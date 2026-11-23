"""Read-only parser for SILENT HILL 2 Remake saves (SaveGameData_*.sav, PersistentData.sav, UcaSave.sav)."""
from __future__ import annotations

import datetime
import json
import math
import struct
import zlib
from pathlib import Path
from typing import Any

import paths

MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024

NATIVE_STRUCT_FMTS = {
    'Guid': '<16s',
    'Vector': '<3d',
    'Vector2D': '<2d',
    'Rotator': '<3d',
    'Quat': '<4d',
    'LinearColor': '<4f',
    'Color': '<4B',
    'IntPoint': '<2i',
    'DateTime': '<q',
    'Timespan': '<q',
}


def fmt_guid(raw16: bytes) -> str:
    a, b, c, d = struct.unpack('<4I', raw16)
    return f'{a:08X}-{b:08X}-{c:08X}-{d:08X}'


def quat_to_yaw_deg(qx: float, qy: float, qz: float, qw: float) -> float:
    yaw_y = 2.0 * (qw * qz + qx * qy)
    yaw_x = 1.0 - 2.0 * (qy * qy + qz * qz)
    return round(math.degrees(math.atan2(yaw_y, yaw_x)), 2)


def ticks_to_iso(ticks: int) -> str | None:
    if ticks <= 0:
        return None
    try:
        dt = datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=ticks // 10)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (OverflowError, ValueError):
        return None


def ticks_to_playtime(ticks: int) -> str | None:
    if ticks <= 0:
        return None
    total_sec = int(ticks // 10_000_000)
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f'{h}:{m:02d}:{s:02d}'


class _BinReader:
    def __init__(self, buf: bytes, pos: int = 0):
        self.b = buf
        self.p = pos

    def u8(self) -> int:
        v = self.b[self.p]
        self.p += 1
        return v

    def i32(self) -> int:
        v, = struct.unpack_from('<i', self.b, self.p)
        self.p += 4
        return v

    def u32(self) -> int:
        v, = struct.unpack_from('<I', self.b, self.p)
        self.p += 4
        return v

    def i64(self) -> int:
        v, = struct.unpack_from('<q', self.b, self.p)
        self.p += 8
        return v

    def f32(self) -> float:
        v, = struct.unpack_from('<f', self.b, self.p)
        self.p += 4
        return v

    def raw(self, n: int) -> bytes:
        if n < 0 or self.p + n > len(self.b):
            raise ValueError('Truncated binary save stream')
        out = self.b[self.p:self.p + n]
        self.p += n
        return out

    def fstr(self) -> str:
        n = self.i32()
        if n == 0:
            return ''
        if n < 0:
            raw_s = self.raw(-n * 2)
            return raw_s[:-2].decode('utf-16-le', 'replace')
        raw_s = self.raw(n)
        return raw_s[:-1].decode('utf-8', 'replace')

    def guid(self) -> str:
        return fmt_guid(self.raw(16))

    def transform3d(self) -> dict[str, Any]:
        raw80 = self.raw(80)
        qx, qy, qz, qw = struct.unpack_from('<4d', raw80, 0)
        tx, ty, tz = struct.unpack_from('<3d', raw80, 32)
        return {
            'xyz': [round(tx, 2), round(ty, 2), round(tz, 2)],
            'yaw': quat_to_yaw_deg(qx, qy, qz, qw),
        }

    def soft_object_path(self) -> tuple[str, str, str]:
        return self.fstr(), self.fstr(), self.fstr()

    def actor_data(self) -> dict[str, Any]:
        g = self.guid()
        plen = self.i32()
        pbytes = self.raw(plen)
        ncmp = self.i32()
        cmps = []
        for _ in range(ncmp):
            cname = self.fstr()
            clen = self.i32()
            cmps.append((cname, self.raw(clen)))
        return {'guid': g, 'raw': pbytes, 'components': cmps}


class _GvasPropReader(_BinReader):
    """Self-contained UE 5.1 (PackageFileUE5Version=1008) tagged property reader."""

    def __init__(self, buf: bytes, pos: int = 0, ue5: int = 1008):
        super().__init__(buf, pos)
        self.ue5 = ue5

    def read_type_tree(self) -> list[Any]:
        ty = self.fstr()
        if self.ue5 >= 1012:
            n = self.i32()
            return [ty, *[self.read_type_tree() for _ in range(n)]]
        return [ty]

    def read_tag(self) -> dict[str, Any] | None:
        name = self.fstr()
        if not name or name == 'None':
            return None
        ty = self.fstr()
        size = self.i32()
        idx = self.i32()
        tree: list[Any] = [ty]
        bool_val = 0
        if ty == 'StructProperty':
            sname = self.fstr()
            _sguid = self.raw(16)
            tree.append([sname])
        elif ty == 'BoolProperty':
            bool_val = self.u8()
        elif ty in ('ByteProperty', 'EnumProperty'):
            ename = self.fstr()
            tree.append([ename])
        elif ty in ('ArrayProperty', 'SetProperty'):
            inner = self.fstr()
            tree.append([inner])
        elif ty == 'MapProperty':
            kt = self.fstr()
            vt = self.fstr()
            tree.extend([[kt], [vt]])
        has_guid = self.u8()
        if has_guid:
            self.raw(16)
        return {'name': name, 'tree': tree, 'size': size, 'index': idx, 'bool_val': bool_val}

    def read_value(self, tree: list[Any], size: int, tag: dict[str, Any] | None = None, in_container: bool = False) -> Any:
        ty = tree[0]
        if ty == 'BoolProperty':
            return bool(self.u8()) if in_container else bool(tag['bool_val'] if tag else 0)
        if ty == 'IntProperty':
            return self.i32()
        if ty == 'UInt32Property':
            return self.u32()
        if ty == 'Int64Property':
            return self.i64()
        if ty == 'UInt64Property':
            v, = struct.unpack_from('<Q', self.b, self.p)
            self.p += 8
            return v
        if ty == 'Int16Property':
            v, = struct.unpack_from('<h', self.b, self.p)
            self.p += 2
            return v
        if ty == 'UInt16Property':
            v, = struct.unpack_from('<H', self.b, self.p)
            self.p += 2
            return v
        if ty == 'Int8Property':
            v, = struct.unpack_from('<b', self.b, self.p)
            self.p += 1
            return v
        if ty == 'FloatProperty':
            return round(self.f32(), 4)
        if ty == 'DoubleProperty':
            v, = struct.unpack_from('<d', self.b, self.p)
            self.p += 8
            return round(v, 4)
        if ty in ('StrProperty', 'NameProperty'):
            return self.fstr()
        if ty == 'EnumProperty':
            return self.fstr()
        if ty == 'ByteProperty':
            ename = tree[1][0] if len(tree) > 1 else 'None'
            if not in_container and ename != 'None':
                return self.fstr()
            return self.u8()
        if ty in ('ObjectProperty', 'SoftObjectProperty', 'ClassProperty', 'SoftClassProperty'):
            if ty.startswith('Soft'):
                return '.'.join(x for x in self.soft_object_path() if x)
            return self.fstr()
        if ty == 'ArrayProperty':
            cnt = self.i32()
            inner = tree[1]
            if not in_container and inner[0] == 'StructProperty' and self.ue5 < 1012:
                arr_tag = self.read_tag()
                if arr_tag is None:
                    return []
                inner = arr_tag['tree']
            if inner[0] == 'ByteProperty' and (len(inner) == 1 or inner[1][0] == 'None'):
                return self.raw(cnt)
            return [self.read_value(inner, 0, None, True) for _ in range(cnt)]
        if ty == 'SetProperty':
            nrem = self.i32()
            inner = tree[1]
            for _ in range(nrem):
                self.read_value(inner, 0, None, True)
            cnt = self.i32()
            return [self.read_value(inner, 0, None, True) for _ in range(cnt)]
        if ty == 'MapProperty':
            nrem = self.i32()
            kt, vt = tree[1], tree[2]
            for _ in range(nrem):
                self.read_value(kt, 0, None, True)
            cnt = self.i32()
            pairs = []
            for _ in range(cnt):
                k = self.read_value(kt, 0, None, True)
                v = self.read_value(vt, 0, None, True)
                pairs.append((k, v))
            return pairs
        if ty == 'StructProperty':
            sname = tree[1][0] if len(tree) > 1 else ''
            if sname in NATIVE_STRUCT_FMTS:
                fmt = NATIVE_STRUCT_FMTS[sname]
                sz = struct.calcsize(fmt)
                vals = struct.unpack_from(fmt, self.b, self.p)
                self.p += sz
                if sname == 'Guid':
                    return fmt_guid(vals[0])
                return vals[0] if len(vals) == 1 else [round(x, 4) if isinstance(x, float) else x for x in vals]
            if in_container and not sname:
                if self.p + 4 <= len(self.b):
                    slen, = struct.unpack_from('<i', self.b, self.p)
                    if 2 <= slen <= 96 and self.p + 4 + slen <= len(self.b) and self.b[self.p + 4 + slen - 1] == 0:
                        cand = self.b[self.p + 4:self.p + 4 + slen - 1]
                        if all(32 <= b < 127 for b in cand):
                            return self.read_props()
                raise ValueError('Opaque struct in MapProperty')
            if size > 0 and not in_container:
                end = self.p + size
                try:
                    props = self.read_props()
                    if self.p == end:
                        return props
                except Exception:
                    pass
                self.p = end
                return None
            return self.read_props()
        if not in_container and size >= 0:
            self.raw(size)
            return None
        raise ValueError(f'Unsupported GVAS property {ty}')

    def read_props(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while True:
            tag = self.read_tag()
            if tag is None:
                break
            start = self.p
            try:
                val = self.read_value(tag['tree'], tag['size'], tag, False)
            except Exception:
                self.p = start + tag['size']
                val = None
            out[tag['name']] = val
        return out


def _decompress_zlib(comp: bytes) -> bytes:
    inflater = zlib.decompressobj()
    out = inflater.decompress(comp, MAX_DECOMPRESSED_BYTES + 1)
    if len(out) > MAX_DECOMPRESSED_BYTES or inflater.unconsumed_tail or not inflater.eof:
        raise ValueError('Invalid zlib payload in save slot')
    return out


def _parse_actor_blob(blob: bytes) -> dict[str, Any]:
    if len(blob) < 84:
        return {}
    r = _BinReader(blob, 0)
    tr = r.transform3d()
    b_hidden = bool(r.i32())
    if r.p + 4 <= len(blob):
        peek, = struct.unpack_from('<i', blob, r.p)
        if peek == 0:
            r.p += 4
        elif peek == 1 and (r.p + 5 > len(blob) or blob[r.p + 4] != 0):
            r.p += 4
            r.guid()
            r.fstr()
            r.fstr()
            r.transform3d()
    gr = _GvasPropReader(blob, r.p)
    try:
        props = gr.read_props()
    except Exception:
        props = {}
    return {'transform': tr, 'hidden': b_hidden, 'props': props}


def _parse_comp_blob(blob: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if len(blob) < 92:
        # Non-SceneComponent ActorComponent
        for off in (0, 4, 8, 12):
            if off < len(blob):
                gr = _GvasPropReader(blob, off)
                try:
                    p = gr.read_props()
                    if p:
                        return p, []
                except Exception:
                    pass
        return {}, []
    gr = _GvasPropReader(blob, 92)
    try:
        props = gr.read_props()
    except Exception:
        return {}, []
    subs: list[dict[str, Any]] = []
    while gr.p + 8 <= len(blob):
        while gr.p + 4 <= len(blob) and blob[gr.p:gr.p + 4] == b'\x00\x00\x00\x00':
            gr.p += 4
        if gr.p >= len(blob):
            break
        try:
            sp = gr.read_props()
            if sp:
                subs.append(sp)
        except Exception:
            break
    return props, subs


def _decode_ghca_blob(b: bytes) -> dict[str, Any]:
    r = _BinReader(b, 0)
    magic = r.raw(4).decode('ascii', 'ignore')
    _ver = r.i32()
    if magic != 'GHCA':
        return {}
    out: dict[str, Any] = {}
    while r.p + 8 <= len(b):
        sec = r.raw(4).decode('ascii', 'ignore')
        cnt = r.i32()
        if sec == 'TNI_':
            out['ints'] = {r.fstr(): r.u32() for _ in range(cnt)}
        elif sec == 'TLF_':
            out['floats'] = {r.fstr(): round(r.f32(), 3) for _ in range(cnt)}
        elif sec == 'LOC_':
            cols = {}
            for _ in range(cnt):
                nm = r.fstr()
                gcnt = r.i32()
                cols[nm] = [r.guid() for _ in range(gcnt)]
            out['collections'] = cols
        else:
            break
    return out


def parse_ucasave_file(uca_file: Path) -> set[str]:
    """Extract global GlimpsesOfPast GUIDs from standalone UcaSave.sav ('VHCA')."""
    try:
        raw = uca_file.read_bytes()
        if raw[:4] != b'GVAS':
            return set()
        r = _BinReader(raw, 4)
        r.p += 12 + 10
        r.fstr()
        r.i32()
        cf_cnt = r.i32()
        r.p += cf_cnt * 20
        r.fstr()
        if r.raw(4) != b'VHCA':
            return set()
        r.i32()
        for _ in range(r.i32()):
            r.fstr()
            r.fstr()
            r.i32()
        for _ in range(r.i32()):
            r.fstr()
            r.u32()
            for _ in range(r.i32()):
                r.fstr()
                r.i32()
        for _ in range(r.i32()):
            r.fstr()
            r.f32()
            for _ in range(r.i32()):
                r.fstr()
                r.i32()
        glimpses: set[str] = set()
        for _ in range(r.i32()):
            nm = r.fstr()
            guids = [r.guid() for _ in range(r.i32())]
            for _ in range(r.i32()):
                r.fstr()
                r.i32()
            if nm == 'GlimpsesOfPast':
                glimpses.update(guids)
        return glimpses
    except Exception:
        return set()


def resolve_world_to_map(xyz: list[float] | tuple[float, float, float], location_tag: str = '') -> str | None:
    """Resolve 3D world coordinates (X, Y, Z) + optional savepoint tag to one of the 41 map slugs."""
    maps_meta = json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))
    volumes = json.loads((paths.DATA / 'map_volumes.json').read_text(encoding='utf-8'))
    id_to_slug = {m['map_id']: m['slug'] for m in maps_meta}

    # Hint era group from location_tag if available
    tag = location_tag or ''
    preferred_era = None
    if 'HospitalFW' in tag or 'Hospital_FW' in tag:
        preferred_era = 'hosp_fw'
    elif 'HospitalOW' in tag or 'Hospital_OW' in tag:
        preferred_era = 'hosp_ow'
    elif 'HotelFW' in tag or 'LhFW' in tag:
        preferred_era = 'hotel_fw'
    elif 'HotelOW' in tag or 'LhOW' in tag:
        preferred_era = 'hotel_ow'
    elif 'CityOW' in tag or 'EcOW' in tag or 'WcOW' in tag or 'Historical' in tag:
        preferred_era = 'city_ow'
    elif ('EastCity' in tag or 'WestCity' in tag) and 'Woodside' not in tag and 'BlueCreek' not in tag:
        preferred_era = 'city_fw'

    x, y, z = xyz
    hits = []
    for v in volumes:
        bmin, bmax = v['bbox_min'], v['bbox_max']
        if bmin[0] - 50 <= x <= bmax[0] + 50 and bmin[1] - 50 <= y <= bmax[1] + 50 and bmin[2] - 80 <= z <= bmax[2] + 80:
            era_match = 1 if (preferred_era and v['era_group'] == preferred_era) else (0 if v['era_group'] == 'any' else -1)
            prio = v['priority'] if v['priority'] is not None else -1
            hits.append((era_match, prio, v['map_id']))
    if hits:
        hits.sort(reverse=True)
        best_id = hits[0][2]
        if best_id == 34:
            best_id = 32
        elif best_id == 54:
            best_id = 52
        elif best_id == 82:
            best_id = 81
        if best_id in id_to_slug:
            return id_to_slug[best_id]

    if 'Prison' in tag:
        return 'prison-1f-main'
    if 'Labyrinth' in tag:
        return 'labyrinth-hub'
    if 'BlueCreek' in tag:
        return 'bluecreek-1f'
    if 'Woodside' in tag:
        return 'woodside-1f'
    if 'Historical' in tag or 'TolucaLakeShore' in tag:
        return 'city-west-ow'
    return None


def parse_save_slot(slot_path: Path) -> dict[str, Any]:
    """Parse a single SaveGameData_*.sav slot into a clean, rich progress dictionary."""
    raw = slot_path.read_bytes()
    if raw[:4] != b'VASb':
        raise ValueError('Not a VASb gameplay save slot')
    wr = _BinReader(raw, 4)
    hdr_size = wr.i32()
    if wr.u32() != 0xDEAD0001:
        raise ValueError('Invalid VASb header magic')
    save_class = wr.fstr()
    if save_class != '/Script/SHProto.SHSaveGame':
        raise ValueError('Unsupported save class')
    _base_ver = wr.i32()
    slot_type = wr.fstr()
    playthrough_id = wr.guid()
    save_ticks = wr.i64()
    _body_crc = wr.i32()
    _thumb_len = wr.i32()
    if wr.u32() != 0xDEAD0001:
        raise ValueError('Invalid SHSaveGame header magic')
    playtime_ticks = wr.i64()
    location_tag = wr.fstr()
    ybdx_off = 10 + hdr_size
    if ybdx_off + 12 > len(raw) or raw[ybdx_off + 2:ybdx_off + 6] != b'YDBx':
        # Fallback locate YDBx
        idx_y = raw.find(b'YDBx', wr.p, wr.p + 16)
        if idx_y < 2:
            raise ValueError('Missing YDBx framing')
        combat_diff = raw[idx_y - 2]
        puzzle_diff = raw[idx_y - 1]
        wr.p = idx_y + 4
    else:
        combat_diff = raw[ybdx_off]
        puzzle_diff = raw[ybdx_off + 1]
        wr.p = ybdx_off + 6

    comp_sz = wr.u32()
    exp_sz = wr.u32()
    comp_body = wr.raw(comp_sz)
    decomp = _decompress_zlib(comp_body)
    if len(decomp) != exp_sz or decomp[:4] != b'GVAS':
        raise ValueError('Decompressed GVAS size mismatch')

    gr = _BinReader(decomp, 4)
    _gvas_ver, _ue4_ver, ue5_ver = gr.i32(), gr.i32(), gr.i32()
    gr.p += 10
    _branch = gr.fstr()
    _cf_ver = gr.i32()
    cf_cnt = gr.i32()
    gr.p += cf_cnt * 20
    _inner_cls = gr.fstr()

    player_data = gr.actor_data()
    has_player_loc = bool(gr.i32())
    streaming_loc = gr.transform3d()
    _spawn_guid = gr.guid()

    n_actors = gr.i32()
    world_actors = [gr.actor_data() for _ in range(n_actors)]

    n_runtime = gr.i32()
    for _ in range(n_runtime):
        gr.soft_object_path()
        gr.fstr()
        gr.fstr()
        gr.guid()
        gr.raw(gr.i32())
        for _ in range(gr.i32()):
            gr.fstr()
            gr.raw(gr.i32())

    for _ in range(gr.i32()):
        gr.soft_object_path()
        gr.u8()

    for _ in range(gr.i32()):
        gr.fstr()
        gr.u8()
        gr.transform3d()

    _persistent_lvl = gr.fstr()
    _gamemode_data = gr.actor_data()
    for _ in range(gr.i32()):
        gr.fstr()
        gr.i32()
    for _ in range(gr.i32()):
        gr.fstr()
        gr.i32()
    for _ in range(gr.i32()):
        gr.fstr()
        gr.f32()

    glimpses: set[str] = set()
    woodside_balloons: set[str] = set()
    for _ in range(gr.i32()):
        bkey = gr.fstr()
        bdata = gr.raw(gr.i32())
        if bkey == 'UcaSave':
            uca_in = _decode_ghca_blob(bdata)
            cols = uca_in.get('collections') or {}
            glimpses.update(cols.get('GlimpsesOfPast') or ())
            woodside_balloons.update(cols.get('WoodsideBalloons') or ())

    # Also merge sibling UcaSave.sav if present in same folder
    sib_uca = slot_path.parent / 'UcaSave.sav'
    if sib_uca.is_file():
        glimpses.update(parse_ucasave_file(sib_uca))

    # Decode PlayerData components
    p_blob = _parse_actor_blob(player_data['raw'])
    player_tr = streaming_loc if has_player_loc else (p_blob.get('transform') or {'xyz': [0.0, 0.0, 0.0], 'yaw': 0.0})

    health = None
    collected_items: dict[str, int] = {}
    ammo_loaded: dict[str, int] = {}
    last_used_weapon: str | None = None
    equipment_states: dict[str, bool] = {}
    memos_picked: list[str] = []
    weapon_kills: dict[str, int] = {}
    stats: dict[str, Any] = {}
    map_objects: dict[str, dict[str, dict[str, int]]] = {}
    map_dynamic: dict[str, dict[str, dict[str, float]]] = {}
    fog_revealed: dict[str, list[str]] = {}

    for cname, craw in player_data['components']:
        cprops, csubs = _parse_comp_blob(craw)
        for sp in ([cprops] + list(csubs)):
            wac = sp.get('WeaponsAmmoCounts')
            if isinstance(wac, list):
                for k, v in wac:
                    if isinstance(v, int):
                        ammo_loaded[str(k)] = v
            luw = sp.get('LastUsedWeapon')
            if isinstance(luw, str) and luw and luw != 'None':
                last_used_weapon = luw
        if cname == 'Health':
            hv = cprops.get('HealthValue')
            if isinstance(hv, (int, float)):
                health = round(float(hv), 1)
        elif cname == 'Items':
            ci = cprops.get('CollectedItems')
            if isinstance(ci, list):
                for item in ci:
                    if isinstance(item, dict) and item.get('ItemRowName'):
                        collected_items[str(item['ItemRowName'])] = int(item.get('Quantity', 0))
            es = cprops.get('EquipmentStateValues')
            if isinstance(es, list):
                for k, v in es:
                    equipment_states[str(k)] = bool(v)
        elif cname == 'Combat':
            wac = cprops.get('WeaponsAmmoCounts')
            if isinstance(wac, list):
                for k, v in wac:
                    if isinstance(v, int):
                        ammo_loaded[str(k)] = v
        elif cname == 'StatisticsComponent':
            for sp in csubs:
                for k, v in sp.items():
                    if k == 'MemosItemsPickedUp' and isinstance(v, list):
                        memos_picked = [str(x) for x in v if x]
                    elif k == 'WeaponToKillsMap' and isinstance(v, list):
                        for wk, wv in v:
                            if isinstance(wv, int):
                                weapon_kills[str(wk)] = int(wv)
                    elif isinstance(v, (int, float)):
                        stats[k] = v
        elif cname == 'MapData':
            mod = cprops.get('MapsObjectsData')
            if isinstance(mod, list):
                for m_enum, m_struct in mod:
                    enum_short = str(m_enum).split('::')[-1]
                    objs = m_struct.get('Objects', []) if isinstance(m_struct, dict) else []
                    d_map: dict[str, dict[str, int]] = {}
                    for o in objs:
                        if isinstance(o, dict) and o.get('ObjectID'):
                            oid = str(o['ObjectID'])
                            otype_raw = str(o.get('Type', ''))
                            d_map[oid] = {
                                'type': otype_raw.split('::')[-1],
                                'val': int(o.get('Value', 0)),
                            }
                    if d_map:
                        map_objects[enum_short] = d_map
            mdc = cprops.get('MapsDynamicObjectsContainers')
            if isinstance(mdc, list):
                for m_enum, m_struct in mdc:
                    enum_short = str(m_enum).split('::')[-1]
                    objs = m_struct.get('Objects', []) if isinstance(m_struct, dict) else []
                    dyn_map = {}
                    for o in objs:
                        if isinstance(o, dict) and o.get('ObjectID'):
                            w2d = o.get('WorldLocation2D')
                            if isinstance(w2d, list) and len(w2d) == 2:
                                dyn_map[str(o['ObjectID'])] = {
                                    'type': str(o.get('Type', '')).split('::')[-1],
                                    'wx': float(w2d[0]),
                                    'wy': float(w2d[1]),
                                }
                    if dyn_map:
                        map_dynamic[enum_short] = dyn_map
            fmr = cprops.get('FogMapsMapRevealedObjectsContainers')
            if isinstance(fmr, list):
                for m_enum, m_struct in fmr:
                    enum_short = str(m_enum).split('::')[-1]
                    rev = m_struct.get('RevealedTo', []) if isinstance(m_struct, dict) else []
                    if isinstance(rev, list):
                        fog_revealed[enum_short] = [str(x) for x in rev]

    # Decode active chapter placed actors (for individual ammo/healing/drawer/puzzle tracking)
    actor_states: dict[str, dict[str, bool]] = {}
    for act in world_actors:
        ab = _parse_actor_blob(act['raw'])
        ap = ab.get('props') or {}
        hidden = bool(ab.get('hidden'))
        collected = bool(ap.get('bWasCollected')) or hidden
        opened = bool(ap.get('WasOpened') or ap.get('bIsOpen'))
        done = bool(ap.get('bHasFXesFinished') or ap.get('bIsCompleted') or ap.get('bSolved'))
        for _cn, cr in act['components']:
            cp, _ = _parse_comp_blob(cr)
            if cp.get('bIsCompleted') or cp.get('bSolved'):
                done = True
            if cp.get('bIsOpen') or cp.get('WasOpened'):
                opened = True
        if hidden or collected or opened or done:
            actor_states[act['guid']] = {
                'hidden': hidden,
                'collected': collected,
                'opened': opened,
                'completed': done,
            }

    active_slug = resolve_world_to_map(player_tr['xyz'], location_tag)
    kills_m = stats.get('MeleeWeaponKillcount')
    kills_r = stats.get('RangedWeaponKillcount')
    kills = (int(kills_m or 0) + int(kills_r or 0)) if (isinstance(kills_m, (int, float)) or isinstance(kills_r, (int, float))) else None

    return {
        'ok': True,
        'slot_type': slot_type,
        'playthrough_id': playthrough_id,
        'ticks': save_ticks,
        'save_datetime': ticks_to_iso(save_ticks),
        'play_time': ticks_to_playtime(playtime_ticks),
        'playtime_seconds': int(playtime_ticks // 10_000_000) if playtime_ticks > 0 else 0,
        'location_tag': location_tag,
        'combat_difficulty_id': int(combat_diff) if combat_diff in (0, 1, 2) else None,
        'puzzle_difficulty_id': int(puzzle_diff) if puzzle_diff in (0, 1, 2) else None,
        'active_map_slug': active_slug,
        'player_pos': player_tr['xyz'],
        'player_yaw': player_tr['yaw'],
        'health': health,
        'items': collected_items,
        'ammo_loaded': ammo_loaded,
        'last_used_weapon': last_used_weapon,
        'equipment': equipment_states,
        'memos': memos_picked,
        'glimpses': sorted(glimpses),
        'balloons': sorted(woodside_balloons),
        'weapon_kills': weapon_kills,
        'stats': {
            'kills': kills,
            'kills_melee': int(kills_m) if isinstance(kills_m, int) else None,
            'kills_ranged': int(kills_r) if isinstance(kills_r, int) else None,
            'shots_fired': stats.get('RangedShootsFired'),
            'dodges': stats.get('PerformedDodges'),
            'investigated': stats.get('MapItemsInvestigated'),
            'consumables_picked': stats.get('ConsumableItemsPickedUp'),
            'heals_used': stats.get('HealsApplied'),
            'damage_taken': round(float(stats['ReceivedDamage']), 1) if 'ReceivedDamage' in stats else None,
            'broken_glass': stats.get('BrokenGlass'),
            'locked_doors_checked': stats.get('AutoLockedDoorCheckAnimActionPlayedCount'),
            'distance_m': round(float(stats['DistanceTravelled']) / 100.0) if 'DistanceTravelled' in stats else None,
        },
        'map_objects': map_objects,
        'map_dynamic': map_dynamic,
        'fog_revealed': fog_revealed,
        'actor_states': actor_states,
        'source': {'slot': slot_path.name},
    }


def find_latest_slot(save_dir: Path | str | None = None) -> Path | None:
    if save_dir:
        p = Path(save_dir)
        if p.is_file():
            return p
    roots = paths.find_save_roots(save_dir)
    cands: list[Path] = []
    for r in roots:
        if r.is_file():
            cands.append(r)
        elif r.is_dir():
            cands.extend(r.rglob('SaveGameData_*.sav'))
    scored = []
    for c in cands:
        try:
            raw_hdr = c.open('rb').read(256)
            if raw_hdr[:4] != b'VASb':
                continue
            wr = _BinReader(raw_hdr, 12)
            wr.fstr()
            wr.i32()
            wr.fstr()
            wr.raw(16)
            ticks = wr.i64()
            scored.append((ticks, c.stat().st_mtime_ns, str(c), c))
        except Exception:
            continue
    return max(scored)[3] if scored else None


def read(save_dir: Path | str | None = None) -> dict[str, Any]:
    slot = find_latest_slot(save_dir)
    if slot is None:
        return {'ok': False}
    try:
        return parse_save_slot(slot)
    except Exception:
        return {'ok': False, 'source': {'slot': slot.name}}
