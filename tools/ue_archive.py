"""Read-only UE5 IoStore (.utoc/.ucas), Pak (.pak), Locres, Zen widget, and Texture2D readers."""
from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

PAK_MAGIC = 0x5A6F12E1
LOCRES_MAGIC = bytes.fromhex('0E147475674A03FC4A15909DC3377F1B')


def _fstr(b: bytes, p: int) -> tuple[str, int]:
    n = struct.unpack_from('<i', b, p)[0]
    p += 4
    if n == 0:
        return '', p
    if n < 0:
        return b[p:p - n * 2 - 2].decode('utf-16-le', 'replace'), p - n * 2
    return b[p:p + n - 1].decode('utf-8', 'replace'), p + n


def parse_locres(b: bytes) -> dict[str, dict[str, str]]:
    p, ver = 0, 0
    if b[:16] == LOCRES_MAGIC:
        ver = b[16]
        p = 17
    strings = None
    if ver >= 1:
        so, = struct.unpack_from('<q', b, p)
        p += 8
        q = so
        cnt, = struct.unpack_from('<i', b, q)
        q += 4
        strings = []
        for _ in range(cnt):
            s, q = _fstr(b, q)
            if ver >= 3:
                q += 4
            strings.append(s)
        if ver >= 2:
            p += 4
    out: dict[str, dict[str, str]] = {}
    nns, = struct.unpack_from('<i', b, p)
    p += 4
    for _ in range(nns):
        if ver >= 2:
            p += 4
        ns, p = _fstr(b, p)
        nk, = struct.unpack_from('<i', b, p)
        p += 4
        d = out.setdefault(ns, {})
        for _ in range(nk):
            if ver >= 2:
                p += 4
            key, p = _fstr(b, p)
            p += 4
            if ver >= 1 and strings is not None:
                i, = struct.unpack_from('<i', b, p)
                p += 4
                d[key] = strings[i] if 0 <= i < len(strings) else ''
            else:
                d[key], p = _fstr(b, p)
    return out


class Pak:
    """Minimal read-only UE5 .pak v8-v11 reader."""

    def __init__(self, pak_file: Path | str):
        self.pak_file = Path(pak_file)
        self.f = self.pak_file.open('rb')
        self.f.seek(0, 2)
        size = self.f.tell()
        tail = min(size, 0x100 + 5 * 32)
        self.f.seek(size - tail)
        t = self.f.read(tail)
        i = t.rfind(struct.pack('<I', PAK_MAGIC))
        if i < 0:
            self.f.close()
            raise ValueError('Invalid .pak archive')
        self.version = struct.unpack_from('<I', t, i + 4)[0]
        self.index_off, self.index_size = struct.unpack_from('<qq', t, i + 8)
        names = t[i + 8 + 16 + 20:]
        self.methods = [names[k * 32:(k + 1) * 32].split(b'\0')[0].decode('ascii', 'ignore') for k in range(5)]
        self.f.seek(self.index_off)
        idx = self.f.read(self.index_size)
        self.mount, p = _fstr(idx, 0)
        p += 4 + 8  # NumEntries + PathHashSeed
        has_ph, = struct.unpack_from('<i', idx, p)
        p += 4
        if has_ph:
            p += 8 + 8 + 20
        has_fd, = struct.unpack_from('<i', idx, p)
        p += 4
        fd_off = fd_size = None
        if has_fd:
            fd_off, fd_size = struct.unpack_from('<qq', idx, p)
            p += 16 + 20
        enc_size, = struct.unpack_from('<i', idx, p)
        p += 4
        self.encoded = idx[p:p + enc_size]
        self.entries: dict[str, int] = {}
        if fd_off is not None and fd_size is not None:
            self.f.seek(fd_off)
            fd = self.f.read(fd_size)
            q = 0
            ndir, = struct.unpack_from('<i', fd, q)
            q += 4
            for _ in range(ndir):
                d, q = _fstr(fd, q)
                nf, = struct.unpack_from('<i', fd, q)
                q += 4
                for _ in range(nf):
                    fn, q = _fstr(fd, q)
                    eo, = struct.unpack_from('<i', fd, q)
                    q += 4
                    self.entries[(d + fn).lstrip('/')] = eo

    def close(self) -> None:
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _decode_entry(self, eo: int):
        b, p = self.encoded, eo
        v, = struct.unpack_from('<I', b, p)
        p += 4
        if v & 0x3F == 0x3F:
            bsize, = struct.unpack_from('<I', b, p)
            p += 4
        else:
            bsize = (v & 0x3F) << 11
        method = (v >> 23) & 0x3F

        def rd(safe):
            nonlocal p
            if safe:
                x, = struct.unpack_from('<I', b, p)
                p += 4
            else:
                x, = struct.unpack_from('<Q', b, p)
                p += 8
            return x

        off = rd(v & (1 << 31))
        usize = rd(v & (1 << 30))
        size = rd(v & (1 << 29)) if method else usize
        nblocks = (v >> 6) & 0xFFFF
        hdr = 8 + 8 + 8 + 4 + 20 + (4 + nblocks * 16 if method else 0) + 1 + 4
        blocks = []
        if nblocks == 1:
            blocks = [(hdr, hdr + size)]
        else:
            start = hdr
            for _ in range(nblocks):
                bl, = struct.unpack_from('<I', b, p)
                p += 4
                blocks.append((start, start + bl))
                start += bl
        return off, usize, size, method, blocks, bsize

    def read(self, entry_key: str) -> bytes:
        off, usize, size, method, blocks, bsize = self._decode_entry(self.entries[entry_key])
        if not method:
            self.f.seek(off + (blocks[0][0] if blocks else 53))
            return self.f.read(size)[:usize]
        mname = self.methods[method - 1].lower()
        out = bytearray()
        for a, z in blocks:
            self.f.seek(off + a)
            chunk = self.f.read(z - a)
            want = min(bsize or usize, usize - len(out))
            if mname == 'zlib':
                out += zlib.decompress(chunk)
            elif mname == 'oodle':
                import ooz
                out += ooz.decompress(chunk, want)
            else:
                raise ValueError(f'Unsupported compression {mname}')
        return bytes(out)


class IoStore:
    """Minimal read-only UE5 IoStore (.utoc/.ucas) v4-v5 reader."""

    def __init__(self, utoc_file: Path | str):
        utoc_p = Path(utoc_file)
        self.ucas_p = utoc_p.with_suffix('.ucas')
        b = utoc_p.read_bytes()
        if b[:16] != b'-==--==--==--==-':
            raise ValueError('Invalid .utoc header')
        self.version = b[16]
        hdr_size, n, nblk, blk_entry, nmeth, meth_len, self.block_size, dir_size, _ = struct.unpack_from('<9I', b, 20)
        p = 20 + 36 + 8 + 16
        self.flags = b[p]
        p += 4
        seeds_count, = struct.unpack_from('<I', b, p)
        p += 4 + 8
        no_hash_count, = struct.unpack_from('<I', b, p)
        p = hdr_size
        self.chunk_ids = [b[p + i * 12:p + i * 12 + 12] for i in range(n)]
        p += n * 12
        self.offlen = [
            (int.from_bytes(b[p + i * 10:p + i * 10 + 5], 'big'),
             int.from_bytes(b[p + i * 10 + 5:p + i * 10 + 10], 'big'))
            for i in range(n)
        ]
        p += n * 10
        if self.version >= 4:
            p += seeds_count * 4
        if self.version >= 5:
            p += no_hash_count * 4
        self.blocks = []
        for i in range(nblk):
            e = b[p + i * 12:p + i * 12 + 12]
            self.blocks.append((
                int.from_bytes(e[0:5], 'little'),
                int.from_bytes(e[5:8], 'little'),
                int.from_bytes(e[8:11], 'little'),
                e[11],
            ))
        p += nblk * blk_entry
        self.methods = ['None'] + [
            b[p + i * meth_len:p + (i + 1) * meth_len].split(b'\0')[0].decode('ascii', 'ignore')
            for i in range(nmeth)
        ]
        p += nmeth * meth_len
        if self.flags & 0x04:
            hs, = struct.unpack_from('<i', b, p)
            p += 4 + hs * 2 + nblk * 20
        self.files: dict[str, int] = {}
        self.files_ci: dict[str, str] = {}
        if self.flags & 0x08 and dir_size:
            self._parse_dir(b[p:p + dir_size])
        self.ubulk_by_pkg = {
            struct.unpack_from('<Q', cid, 0)[0]: idx
            for idx, cid in enumerate(self.chunk_ids)
            if cid[11] == 2
        }

    def _parse_dir(self, d: bytes) -> None:
        mount, q = _fstr(d, 0)
        nd, = struct.unpack_from('<i', d, q)
        q += 4
        dirs = [struct.unpack_from('<4I', d, q + i * 16) for i in range(nd)]
        q += nd * 16
        nf, = struct.unpack_from('<i', d, q)
        q += 4
        files = [struct.unpack_from('<3I', d, q + i * 12) for i in range(nf)]
        q += nf * 12
        ns, = struct.unpack_from('<i', d, q)
        q += 4
        strs = []
        for _ in range(ns):
            s, q = _fstr(d, q)
            strs.append(s)
        none_idx = 0xFFFFFFFF

        def walk(di: int, prefix: str) -> None:
            nm, child, _sib, ffile = dirs[di]
            here = prefix + (strs[nm] + '/' if nm != none_idx else '')
            f = ffile
            while f != none_idx:
                fn, nxt, user = files[f]
                full = (mount + here + strs[fn]).replace('../../../', '')
                self.files[full] = user
                self.files_ci[full.lower()] = full
                f = nxt
            c = child
            while c != none_idx:
                walk(c, here)
                c = dirs[c][2]

        if dirs:
            walk(0, '')

    def resolve_key(self, rel_or_full: str) -> str | None:
        cands = [rel_or_full]
        if not rel_or_full.startswith('SHProto/Content/'):
            cands.append('SHProto/Content/' + rel_or_full.lstrip('/'))
        for c in cands:
            if not c.endswith('.uasset') and not c.endswith('.umap'):
                c_u = c + '.uasset'
                if c_u.lower() in self.files_ci:
                    return self.files_ci[c_u.lower()]
            if c.lower() in self.files_ci:
                return self.files_ci[c.lower()]
        return None

    def read_index(self, idx: int) -> bytes:
        off, ln = self.offlen[idx]
        out = bytearray()
        first = off // self.block_size
        last = (off + ln - 1) // self.block_size
        with self.ucas_p.open('rb') as f:
            for bi in range(first, last + 1):
                boff, csz, usz, m = self.blocks[bi]
                f.seek(boff)
                raw = f.read(csz)
                meth = self.methods[m].lower()
                if meth == 'none':
                    data = raw[:usz]
                elif meth == 'oodle':
                    import ooz
                    data = ooz.decompress(raw, usz)
                elif meth == 'zlib':
                    data = zlib.decompress(raw)
                else:
                    raise ValueError(f'Unsupported IoStore compression {meth}')
                out += data
        start = off - first * self.block_size
        return bytes(out[start:start + ln])

    def read(self, key: str) -> bytes:
        rk = self.resolve_key(key)
        if rk is None:
            raise KeyError(key)
        return self.read_index(self.files[rk])


def zen_name_map(b: bytes) -> list[str]:
    i = b.find(struct.pack('<Q', 0xC1640000))
    if i < 8:
        return []
    n, _ = struct.unpack_from('<II', b, i - 8)
    p = i + 8 + n * 8
    hdr = [struct.unpack_from('>H', b, p + k * 2)[0] for k in range(n)]
    p += n * 2
    out = []
    for h in hdr:
        ln = h & 0x7FFF
        if h & 0x8000:
            if p & 1:
                p += 1
            out.append(b[p:p + ln * 2].decode('utf-16-le', 'replace'))
            p += ln * 2
        else:
            out.append(b[p:p + ln].decode('latin1'))
            p += ln
    return out


def parse_global_script_objects(global_utoc: Path | str) -> dict[int, str]:
    gio = IoStore(global_utoc)
    b = gio.read_index(0)
    i = b.find(struct.pack('<Q', 0xC1640000))
    n, _ = struct.unpack_from('<II', b, i - 8)
    p = i + 8 + n * 8
    hdr = [struct.unpack_from('>H', b, p + k * 2)[0] for k in range(n)]
    p += n * 2
    names = []
    for h in hdr:
        ln = h & 0x7FFF
        if h & 0x8000:
            if p & 1:
                p += 1
            names.append(b[p:p + ln * 2].decode('utf-16-le', 'replace'))
            p += ln * 2
        else:
            names.append(b[p:p + ln].decode('latin1'))
            p += ln
    num_objs, = struct.unpack_from('<i', b, p)
    p += 4
    entries = {}
    for k in range(num_objs):
        nm_idx_raw, nm_num, global_idx, outer_idx, _ = struct.unpack_from('<IIQQQ', b, p + k * 32)
        nm = names[nm_idx_raw & 0x3FFFFFFF] + (f'_{nm_num - 1}' if nm_num else '')
        entries[global_idx] = (nm, outer_idx)
    out = {}
    for gidx in entries:
        parts = []
        cur = gidx
        seen = set()
        while cur and cur != 0xFFFFFFFFFFFFFFFF and cur in entries and cur not in seen:
            seen.add(cur)
            nm, outer = entries[cur]
            parts.append(nm)
            cur = outer
        out[gidx] = '/'.join(reversed(parts))
    return out


class ZenContext:
    """Resolves Zen imports/exports across SHProto-Windows.utoc + global.utoc."""

    def __init__(self, paks_folder: Path | str):
        pdir = Path(paks_folder)
        self.io = IoStore(pdir / 'SHProto-Windows.utoc')
        self.script_objs = parse_global_script_objects(pdir / 'global.utoc')
        self.pkg_to_file: dict[int, str] = {}
        ch_idx = None
        for idx, cid in enumerate(self.io.chunk_ids):
            if cid[11] == 6:
                ch_idx = idx
        for fkey, cidx in self.io.files.items():
            cid = self.io.chunk_ids[cidx]
            if cid[11] == 1:
                pid, = struct.unpack_from('<Q', cid, 0)
                self.pkg_to_file[pid] = fkey
        self.pkg_imports_map: dict[int, tuple[int, ...]] = {}
        if ch_idx is not None:
            ch_bytes = self.io.read_index(ch_idx)
            _, _, _, pkg_cnt = struct.unpack_from('<IIQI', ch_bytes, 0)
            ch_pkg_ids = struct.unpack_from(f'<{pkg_cnt}Q', ch_bytes, 20)
            p_ch = 20 + pkg_cnt * 8
            store_len, = struct.unpack_from('<I', ch_bytes, p_ch)
            store_buf = ch_bytes[p_ch + 4:p_ch + 4 + store_len]
            for k in range(pkg_cnt):
                base_e = k * 24
                _, _, imp_num, imp_rel_off, _, _ = struct.unpack_from('<iiIIII', store_buf, base_e)
                imps = struct.unpack_from(f'<{imp_num}Q', store_buf, base_e + 8 + imp_rel_off) if imp_num > 0 else ()
                self.pkg_imports_map[ch_pkg_ids[k]] = imps

    def parse_package(self, key: str):
        rk = self.io.resolve_key(key)
        if rk is None:
            raise KeyError(key)
        cidx = self.io.files[rk]
        pid, = struct.unpack_from('<Q', self.io.chunk_ids[cidx], 0)
        b = self.io.read_index(cidx)
        nm = zen_name_map(b)
        u32s = struct.unpack_from('<12I', b, 0)
        hdr_size, imp_off, exp_off, exp_bundle_off, dep_hdr_off = u32s[1], u32s[7], u32s[8], u32s[9], u32s[10]
        imp_pkgs = self.pkg_imports_map.get(pid, ())
        n_imp = (exp_off - imp_off) // 8
        imports = []
        for i in range(n_imp):
            val, = struct.unpack_from('<Q', b, imp_off + i * 8)
            if val == 0xFFFFFFFFFFFFFFFF:
                imports.append(None)
            elif val in self.script_objs:
                imports.append(self.script_objs[val])
            elif (val >> 62) == 2:
                pkg_i = (val >> 32) & 0x3FFFFFFF
                imports.append(self.pkg_to_file.get(imp_pkgs[pkg_i]) if pkg_i < len(imp_pkgs) else None)
            else:
                imports.append(None)

        n_exp = (exp_bundle_off - exp_off) // 72
        exports = []
        for i in range(n_exp):
            ep = exp_off + i * 72
            c_off, c_sz = struct.unpack_from('<QQ', b, ep)
            ename_idx, ename_num = struct.unpack_from('<II', b, ep + 16)
            outer_i, class_i, _, _ = struct.unpack_from('<4Q', b, ep + 24)
            ename = nm[ename_idx & 0x3FFFFFFF] + (f'_{ename_num - 1}' if ename_num else '')
            cls_name = self.script_objs.get(class_i, '')
            outer_exp = outer_i if (outer_i >> 62) == 0 and outer_i < n_exp else None
            exports.append({
                'idx': i, 'name': ename, 'sz': c_sz,
                'outer_exp': outer_exp, 'class': cls_name, 'bytes': b'',
            })

        n_bnd = (dep_hdr_off - exp_bundle_off) // 8
        cur_p = hdr_size
        for k in range(n_bnd):
            loc_idx, cmd_type = struct.unpack_from('<II', b, exp_bundle_off + k * 8)
            if cmd_type == 1:
                sz = exports[loc_idx]['sz']
                exports[loc_idx]['bytes'] = b[cur_p:cur_p + sz]
                cur_p += sz

        def resolve_pkg_index(v: int):
            if v == 0:
                return None
            if v > 0:
                return f"Exp:{exports[v - 1]['name']}" if v - 1 < len(exports) else None
            return imports[-v - 1] if -v - 1 < len(imports) else None

        return nm, imports, exports, resolve_pkg_index


def unversioned_header(b: bytes, p: int) -> tuple[list[int], int]:
    fragments, bits = [], 0
    for _ in range(64):
        packed, = struct.unpack_from('<H', b, p)
        p += 2
        skip, count, masked = packed & 127, packed >> 9, bool(packed & 128)
        fragments.append((skip, count, masked))
        bits += count if masked else 0
        if packed & 256:
            break
    width = 0 if not bits else 1 if bits <= 8 else 2 if bits <= 16 else ((bits + 31) // 32) * 4
    mask = int.from_bytes(b[p:p + width], 'little')
    p += width
    fields, index, bit = [], 0, 0
    for skip, count, masked in fragments:
        index += skip
        for _ in range(count):
            if not (masked and ((mask >> bit) & 1)):
                fields.append(index)
            bit += bool(masked)
            index += 1
    return fields, p


def decode_bc1_numpy(raw: bytes, width: int, height: int) -> np.ndarray:
    """Pure numpy fallback for BC1 (DXT1) -> RGBA uint8 (height, width, 4)."""
    bw, bh = (width + 3) // 4, (height + 3) // 4
    blocks = np.frombuffer(raw[:bw * bh * 8], dtype=np.dtype('<u2, <u2, <u4')).reshape(bh, bw)
    c0 = blocks['f0'].astype(np.uint32)
    c1 = blocks['f1'].astype(np.uint32)
    idx = blocks['f2']

    def rgb565(c):
        r = ((c >> 11) & 31) * 255 // 31
        g = ((c >> 5) & 63) * 255 // 63
        b = (c & 31) * 255 // 31
        return np.stack([r, g, b, np.full_like(r, 255)], axis=-1).astype(np.float32)

    p0, p1 = rgb565(c0), rgb565(c1)
    gt = (c0 > c1)[..., None]
    p2 = np.where(gt, (2 * p0 + p1) / 3.0, (p0 + p1) / 2.0)
    p3_opaque = (p0 + 2 * p1) / 3.0
    p3_trans = np.zeros_like(p0)
    p3 = np.where(gt, p3_opaque, p3_trans)
    pal = np.stack([p0, p1, p2, p3], axis=-2).round().astype(np.uint8)  # (bh, bw, 4, 4)

    shifts = np.arange(0, 32, 2, dtype=np.uint32)
    codes = ((idx[..., None] >> shifts) & 3).reshape(bh, bw, 4, 4)
    pixels = np.take_along_axis(pal[:, :, None, :, :], codes[..., None], axis=3)[..., 0, :]
    return pixels.transpose(0, 2, 1, 3, 4).reshape(bh * 4, bw * 4, 4)[:height, :width]


def decode_bc3_numpy(raw: bytes, width: int, height: int) -> np.ndarray:
    """Pure numpy fallback for BC3 (DXT5) -> RGBA uint8 (height, width, 4)."""
    bw, bh = (width + 3) // 4, (height + 3) // 4
    raw_arr = np.frombuffer(raw[:bw * bh * 16], dtype=np.uint8).reshape(bh, bw, 16)
    color_bytes = np.ascontiguousarray(raw_arr[:, :, 8:16]).tobytes()
    rgba = decode_bc1_numpy(color_bytes, width, height).copy()

    a0 = raw_arr[:, :, 0].astype(np.float32)
    a1 = raw_arr[:, :, 1].astype(np.float32)
    gt = (a0 > a1)[..., None]
    pal_gt = np.stack([
        a0, a1,
        (6 * a0 + 1 * a1) / 7.0, (5 * a0 + 2 * a1) / 7.0,
        (4 * a0 + 3 * a1) / 7.0, (3 * a0 + 4 * a1) / 7.0,
        (2 * a0 + 5 * a1) / 7.0, (1 * a0 + 6 * a1) / 7.0,
    ], axis=-1)
    pal_le = np.stack([
        a0, a1,
        (4 * a0 + 1 * a1) / 5.0, (3 * a0 + 2 * a1) / 5.0,
        (2 * a0 + 3 * a1) / 5.0, (1 * a0 + 4 * a1) / 5.0,
        np.zeros_like(a0), np.full_like(a0, 255.0),
    ], axis=-1)
    apal = np.where(gt, pal_gt, pal_le).round().astype(np.uint8)  # (bh, bw, 8)

    abits = np.zeros((bh, bw), dtype=np.uint64)
    for k in range(6):
        abits |= raw_arr[:, :, 2 + k].astype(np.uint64) << np.uint64(8 * k)
    shifts = np.arange(0, 48, 3, dtype=np.uint64)
    acodes = ((abits[..., None] >> shifts) & np.uint64(7)).reshape(bh, bw, 4, 4)
    alpha = np.take_along_axis(apal[:, :, None, :], acodes, axis=3).transpose(0, 2, 1, 3).reshape(bh * 4, bw * 4)
    rgba[:, :, 3] = alpha[:height, :width]
    return rgba


def decode_texture2d(io: IoStore, asset_key: str) -> Image.Image:
    rk = io.resolve_key(asset_key)
    if rk is None:
        raise KeyError(asset_key)
    cidx = io.files[rk]
    pkg_id, = struct.unpack_from('<Q', io.chunk_ids[cidx], 0)
    b = io.read_index(cidx)
    hdr_size, = struct.unpack_from('<I', b, 4)
    eb = b[hdr_size:]

    pf_marker = eb.find(b'PF_')
    if pf_marker < 16:
        raise ValueError(f'No PF_ string in {rk}')
    fmt_len, = struct.unpack_from('<i', eb, pf_marker - 4)
    if not (3 <= fmt_len <= 32):
        raise ValueError(f'Invalid PF_ len in {rk}')
    pf_name = eb[pf_marker:pf_marker + fmt_len - 1].decode('ascii')
    sx, sy, _packed = struct.unpack_from('<iiI', eb, pf_marker - 16)
    p = pf_marker + fmt_len
    _first_mip, _num_mips = struct.unpack_from('<ii', eb, p)
    p += 8
    bulk_flags, elem_cnt, _sz_disk, off_in_file = struct.unpack_from('<Iiiq', eb, p)
    p += 20

    if bulk_flags & 0x0100:
        ub = io.read_index(io.ubulk_by_pkg[pkg_id])
        raw = ub[off_in_file:off_in_file + elem_cnt]
    else:
        raw = eb[p:p + elem_cnt]

    if pf_name == 'PF_B8G8R8A8':
        return Image.frombytes('RGBA', (sx, sy), raw, 'raw', 'BGRA')

    try:
        import texture2ddecoder
        if pf_name == 'PF_DXT1':
            bgra = texture2ddecoder.decode_bc1(raw, sx, sy)
        elif pf_name == 'PF_DXT5':
            bgra = texture2ddecoder.decode_bc3(raw, sx, sy)
        elif pf_name == 'PF_BC7':
            bgra = texture2ddecoder.decode_bc7(raw, sx, sy)
        else:
            raise ValueError(pf_name)
        return Image.frombytes('RGBA', (sx, sy), bgra, 'raw', 'BGRA')
    except ImportError:
        if pf_name == 'PF_DXT1':
            return Image.fromarray(decode_bc1_numpy(raw, sx, sy), 'RGBA')
        if pf_name == 'PF_DXT5':
            return Image.fromarray(decode_bc3_numpy(raw, sx, sy), 'RGBA')
        raise


def parse_canvas_slot(eb: bytes) -> dict[str, Any]:
    props, p = unversioned_header(eb, 0)
    res: dict[str, Any] = {
        'left': 0.0, 'top': 0.0, 'right': 100.0, 'bottom': 30.0,
        'anchors': [0.0, 0.0, 0.0, 0.0], 'align': [0.0, 0.0],
        'autosize': False, 'zorder': 0, 'parent': None, 'content_exp': None,
    }
    if 0 in props:
        ad_props, p = unversioned_header(eb, p)
        if 0 in ad_props:
            m_props, p = unversioned_header(eb, p)
            for mi, mkey in [(0, 'left'), (1, 'top'), (2, 'right'), (3, 'bottom')]:
                if mi in m_props:
                    res[mkey], = struct.unpack_from('<f', eb, p)
                    p += 4
        if 1 in ad_props:
            a_props, p = unversioned_header(eb, p)
            if 0 in a_props:
                res['anchors'][0], res['anchors'][1] = struct.unpack_from('<dd', eb, p)
                p += 16
            if 1 in a_props:
                res['anchors'][2], res['anchors'][3] = struct.unpack_from('<dd', eb, p)
                p += 16
        if 2 in ad_props:
            res['align'] = list(struct.unpack_from('<dd', eb, p))
            p += 16
    if 1 in props:
        res['autosize'] = bool(eb[p])
        p += 1
    if 2 in props:
        res['zorder'], = struct.unpack_from('<i', eb, p)
        p += 4
    if 3 in props:
        par_i, = struct.unpack_from('<i', eb, p)
        p += 4
        res['parent'] = par_i - 1 if par_i > 0 else None
    if 4 in props:
        cnt_i, = struct.unpack_from('<i', eb, p)
        p += 4
        res['content_exp'] = cnt_i - 1 if cnt_i > 0 else None
    return res


def parse_uimage_info(eb: bytes, resolve_pkg_index) -> dict[str, Any]:
    props, p = unversioned_header(eb, 0)
    res: dict[str, Any] = {
        'image_size': [32.0, 32.0], 'resource': None,
        'tx': 0.0, 'ty': 0.0, 'sx': 1.0, 'sy': 1.0, 'angle': 0.0, 'px': 0.5, 'py': 0.5,
    }
    for pi in props:
        if pi == 0:  # Brush (FSlateBrush)
            b_props, p = unversioned_header(eb, p)
            for bp in b_props:
                if bp in (0, 1, 2, 3, 4, 5):
                    p += 1
                elif bp == 6:
                    res['image_size'] = list(struct.unpack_from('<dd', eb, p))
                    p += 16
                elif bp == 7:
                    mp, p = unversioned_header(eb, p)
                    p += 4 * len(mp)
                elif bp == 8:
                    sp, p = unversioned_header(eb, p)
                    for s_i in sp:
                        p += 16 if s_i == 0 else 1
                elif bp == 10:
                    ri, = struct.unpack_from('<i', eb, p)
                    p += 4
                    res['resource'] = resolve_pkg_index(ri)
                else:
                    return res
        elif pi == 6:  # Slot
            p += 4
        elif pi in (7, 8, 9, 10, 11, 12):
            return res
        elif pi == 13:  # RenderTransform (FWidgetTransform)
            rt_props, p = unversioned_header(eb, p)
            for rtp in rt_props:
                if rtp == 0:
                    res['tx'], res['ty'] = struct.unpack_from('<dd', eb, p)
                    p += 16
                elif rtp == 1:
                    res['sx'], res['sy'] = struct.unpack_from('<dd', eb, p)
                    p += 16
                elif rtp == 2:
                    p += 16
                elif rtp == 3:
                    res['angle'], = struct.unpack_from('<f', eb, p)
                    p += 4
        elif pi == 14:  # RenderTransformPivot
            res['px'], res['py'] = struct.unpack_from('<dd', eb, p)
            p += 16
        else:
            break
    return res


def extract_textblock_strings(eb: bytes, ru_any: dict[str, str], en_any: dict[str, str]) -> tuple[str, str, float, int]:
    """Extract (text_ru, text_en, angle_deg, font_size) from a serialized UTextBlock export."""
    angle = 0.0
    font_size = 16
    props, _ = unversioned_header(eb, 0)
    if 28 in props and 31 not in props and 29 not in props and len(eb) >= 10:
        # Trailing FWidgetTransform(Angle only = 0x0303 + f32) + 4B ObjectGuid(0)
        if eb[-10:-8] == b'\x03\x03':
            ang, = struct.unpack_from('<f', eb, len(eb) - 8)
            if -360.0 <= ang <= 360.0:
                angle = round(float(ang), 2)
    else:
        idx_rt = eb.rfind(b'\x03\x03')
        if idx_rt != -1 and len(eb) - 24 <= idx_rt <= len(eb) - 10:
            ang, = struct.unpack_from('<f', eb, idx_rt + 2)
            if -360.0 <= ang <= 360.0 and abs(ang) >= 1.0:
                angle = round(float(ang), 2)

    m = re.search(rb'([0-9A-F]{32})', eb)
    txt_ru = txt_en = ''
    if m:
        key = m.group(1).decode('ascii')
        txt_ru = (ru_any.get(key) or '').strip()
        txt_en = (en_any.get(key) or '').strip()
    if not txt_ru and not txt_en:
        cands = re.findall(rb'\x00([\x20-\x7e]{1,16})\x00', eb)
        for cand in reversed(cands):
            s = cand.decode('ascii', 'ignore').strip()
            if s and s not in ('None', 'Default', 'Bold', 'Regular', 'Italic') and not re.fullmatch(r'[0-9A-F]{32}', s):
                txt_ru = txt_en = s
                break
    # Estimate font size from serialized FSlateFontInfo.Size (usually 10..28)
    for m_sz in re.finditer(rb'\x00\x00\x00\x00([\x09-\x24])\x00\x00\x00', eb):
        font_size = m_sz.group(1)[0]
    return txt_ru or txt_en, txt_en or txt_ru, angle, font_size
