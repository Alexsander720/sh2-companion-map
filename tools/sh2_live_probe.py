"""Static read-only PE analyzer to locate GWorld RVA and PE fingerprint for SHProto-Win64-Shipping.exe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import paths


def scan_pe_for_gworld(exe_path: Path) -> dict:
    raw = exe_path.read_bytes()
    if raw[:2] != b'MZ':
        raise ValueError('Not a valid PE executable')
    e_lfanew, = struct.unpack_from('<I', raw, 0x3C)
    if raw[e_lfanew:e_lfanew + 4] != b'PE\x00\x00':
        raise ValueError('Invalid PE signature')
    nsec, pe_ts = struct.unpack_from('<HI', raw, e_lfanew + 6)
    opt_sz, = struct.unpack_from('<H', raw, e_lfanew + 20)
    opt_off = e_lfanew + 24
    img_base, = struct.unpack_from('<Q', raw, opt_off + 24)
    size_of_headers, = struct.unpack_from('<I', raw, opt_off + 60)

    hdr_4k_sha = hashlib.sha256(raw[:4096]).hexdigest()
    norm_hdr = bytearray(raw[:size_of_headers])
    norm_hdr[opt_off + 24:opt_off + 32] = b'\x00' * 8
    loaded_hdr_key = hashlib.sha256(bytes(norm_hdr)).hexdigest()

    secs = {}
    sec_off = opt_off + opt_sz
    for i in range(nsec):
        s_raw = raw[sec_off + i * 40:sec_off + (i + 1) * 40]
        sname = s_raw[:8].rstrip(b'\x00').decode('ascii', 'ignore')
        vsz, va, rsz, rptr = struct.unpack_from('<4I', s_raw, 8)
        secs[sname] = (va, vsz, rptr, rsz)

    text_va, _tvsz, text_ptr, text_sz = secs['.text']
    data_va, data_vsz, _, _ = secs['.data']
    text_buf = raw[text_ptr:text_ptr + text_sz]

    # Signature 1: UWorld::DestroyWorld — `if (GWorld == this) GWorld = nullptr;`
    destroy_world_set = set()
    for m in re.finditer(
        rb'[\x48\x4c]\x39[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....\x75\x07'
        rb'[\x48\x4c]\x89[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',
        text_buf,
        re.DOTALL,
    ):
        pos = m.start()
        r1 = text_va + pos + 7 + struct.unpack_from('<i', text_buf, pos + 3)[0]
        r2 = text_va + pos + 16 + struct.unpack_from('<i', text_buf, pos + 12)[0]
        if r1 == r2 and data_va <= r1 < data_va + data_vsz:
            destroy_world_set.add(r1)

    # Signature 2: FSeamlessTravelHandler::Tick — `GWorld = nullptr; ... GWorld = CurrentWorld (+0x78);`
    seamless_set = set()
    for m in re.finditer(rb'\x48\xc7\x05....\x00\x00\x00\x00', text_buf, re.DOTALL):
        pos = m.start()
        r1 = text_va + pos + 11 + struct.unpack_from('<i', text_buf, pos + 3)[0]
        if not (data_va <= r1 < data_va + data_vsz):
            continue
        win = text_buf[pos:pos + 320]
        for rm in re.finditer(
            rb'[\x48\x49]\x8b[\x43\x45\x46\x47]\x78[\x48\x4c]\x89[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',
            win,
            re.DOTALL,
        ):
            r2_off = pos + rm.start() + 4
            r2 = text_va + r2_off + 7 + struct.unpack_from('<i', text_buf, r2_off + 3)[0]
            if r2 == r1:
                seamless_set.add(r1)

    gworld_candidates = sorted(destroy_world_set & seamless_set) or sorted(seamless_set) or sorted(destroy_world_set)

    return {
        'file_size': len(raw),
        'pe_timestamp': pe_ts,
        'image_base': hex(img_base),
        'size_of_headers': hex(size_of_headers),
        'header_sha256': hdr_4k_sha,
        'loaded_header_key': loaded_hdr_key,
        'gworld_rva_candidates': [hex(x) for x in gworld_candidates],
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, help='Path to SHProto-Win64-Shipping.exe')
    args = p.parse_args(argv)
    exe = args.exe or paths.shipping_exe()
    if not exe or not exe.is_file():
        print('SHProto-Win64-Shipping.exe not found. Pass --exe "<path>".')
        return 1
    info = scan_pe_for_gworld(exe)
    print(json.dumps(info, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
