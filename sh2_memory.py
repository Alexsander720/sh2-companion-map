"""Read-only live telemetry reader for SILENT HILL 2 Remake (UE 5.1, SHProto-Win64-Shipping.exe).

Safety guarantees:
1. READ-ONLY: opens the process strictly with PROCESS_VM_READ | PROCESS_QUERY_INFORMATION (0x0410).
   Never requests write permissions and never calls WriteProcessMemory.
2. BUILD FINGERPRINT LOCKED: pointer offsets are bound to the exact PE fingerprint (file size,
   COFF TimeDateStamp, disk header SHA-256, and in-memory PE header SHA-256).
3. NO STALE MARKER: if the game is closed, in the main menu, or running an unverified patch,
   returns available=False with an explicit reason_code.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import math
import os
import struct
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import paths
import sh2_save

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
SAFE_ACCESS_MASK = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
STILL_ACTIVE = 259
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MODULE_NAME = 'SHProto-Win64-Shipping.exe'

MAP_OBJ_TYPE_NAMES: dict[int, str] = {
    0: 'None',
    1: 'Objective',
    2: 'Puzzle',
    3: 'Door',
    4: 'DoorAttachment',
    5: 'Collectable',
    6: 'Obstacle',
    7: 'Ladder',
    8: 'SavePoint',
    9: 'Pushable',
    10: 'TextHint',
    11: 'HintSign',
}

KNOWN_BUILDS: dict[tuple[int, int], dict[str, Any]] = {
    # Steam Release 1.0.0.5 (UE 5.1, LWC float64)
    (142126592, 1737472969): {
        'version': '1.0.0.5 (Steam Win64)',
        'header_sha256': 'd483b0c88d2e488cf862d056bca1f4735ccd464d11cb0facbf16e27156e5aed8',
        'loaded_header_key': '93edf6e50f5ffdc6b517c87b8158e1993dafa46bf30ed22045f04fae7f2793b6',
        'size_of_headers': 0x600,
        'gworld_rva': 0x082D46F0,
        'gnames_rva': 0x080C65C0,
        'gnames_blocks_rva': 0x080C65D0,
        'offsets': {
            'uobject_class': 0x0010,
            'uobject_name': 0x0018,
            'world_game_instance': 0x01F8,
            'gi_local_players': 0x0038,       # TArray<ULocalPlayer*>
            'lp_player_controller': 0x0030,
            'pc_pawn': 0x02F0,
            'pc_control_rot': 0x0328,         # FRotator3d (3x double)
            'pc_ack_pawn': 0x0358,            # ASHCharacterPlay*
            'pc_camera_mgr': 0x0368,          # APlayerCameraManager*
            'actor_root_comp': 0x01B0,        # USceneComponent*
            'sc_comp_to_world_rot': 0x0240,   # FQuat4d (4x double)
            'sc_comp_to_world_pos': 0x0260,   # FVector3d (3x double)
            'cam_pov_loc': 0x2360,            # FVector3d (3x double)
            'cam_pov_rot': 0x2378,            # FRotator3d (Pitch, Yaw, Roll 3x double)
            'cam_pov_fov': 0x2390,            # float32
            'char_health_comp': 0x06B8,       # USHCharacterPlayHealthComponent*
            'health_value': 0x00F8,           # float32
            'health_state': 0x0114,           # uint8 ESHHealthStateEnum
            'char_items_comp': 0x06C0,        # USHCharacterPlayItemsComponent*
            'items_collected_arr': 0x0110,    # TArray<FSHCollectedItemData> (0x0C)
            'items_equip_map': 0x0130,        # TMap<FName, bool> (0x14)
            'char_combat_comp': 0x06C8,       # USHCharacterPlayCombatComponent*
            'combat_owned_subcomps': 0x0100,  # TSet<UObject*> (0x10)
            'combat_ranged_subcomp': 0x01B8,  # USHRangedCmbSubcomp*
            'combat_weapon_mgr_subcomp': 0x01C8,  # USHWeaponManageCmbSubcomp*
            'wmgr_equipped_weapon': 0x0038,   # AActor*
            'wmgr_last_weapon': 0x0040,       # FName
            'wmgr_last_melee': 0x0048,        # FName
            'wmgr_last_ranged': 0x0050,       # FName
            'ranged_ammo_map': 0x0078,        # TMap<FName, int32> (0x14)
            'char_map_comp': 0x06D0,          # USHCharacterPlayMapComponent*
            'map_volumes_arr': 0x00F8,        # TArray<ASHGameplayMapVolume*>
            'map_objects_map': 0x0118,        # TMap<uint8, FSHMapObjectsStruct> (0x20)
            'map_dynamic_map': 0x0168,        # TMap<uint8, FSHMapDynamicObjectsContainer> (0x20)
            'map_volume_enum': 0x02E8,        # uint8 ESHMapsEnum
            'char_stats_comp': 0x0740,        # USHCharacterPlayStatisticsComponent*
            'stats_processors_arr': 0x00B0,   # TArray<USHStatisticsValueProcessor*>
            'stats_proc_anims': 0x00C8,       # USHAnimsPlayedStatisticsValueProcessor*
            'stats_proc_combat': 0x00D0,      # USHCombatStatisticsValueProcessor*
            'stats_proc_distance': 0x00D8,    # USHDistanceTravelledStatisticsValueProcessor*
            'stats_proc_invest': 0x00E0,      # USHItemsInvestigationStatisticsValueProcessor*
            'stats_proc_picked': 0x00E8,      # USHItemsPickedUpStatisticsValueProcessor*
            'stat_combat_melee': 0x0030,      # int32
            'stat_combat_ranged': 0x0034,     # int32
            'stat_combat_shots': 0x0038,      # int32
            'stat_combat_dodges': 0x003C,     # int32
            'stat_combat_glass': 0x0040,      # int32
            'stat_combat_heals': 0x0044,      # int32
            'stat_combat_dmg': 0x0048,        # float32
            'stat_combat_weapon_kills_map': 0x0050,  # TMap<FName, int32> (0x14)
            'stat_anims_locked_doors': 0x0030,       # int32
            'stat_dist_cm': 0x0030,                  # int32
            'stat_invest_maps': 0x0030,              # int32
            'stat_picked_consumables': 0x0030,       # int32
            'stat_picked_memos_arr': 0x0038,         # TArray<FName> (0x08)
            'char_input_mode': 0x07A9,        # uint8 ESHGameplayInputModeEnum
        },
    },
}


@lru_cache(maxsize=1)
def load_maps_by_slug() -> dict[str, dict[str, Any]]:
    raw = json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))
    return {m['slug']: m for m in raw}


@lru_cache(maxsize=1)
def load_maps_by_id() -> dict[int, dict[str, Any]]:
    raw = json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))
    return {int(m['map_id']): m for m in raw}


def project_world_to_sheet(wx: float, wy: float, yaw_deg: float, map_meta: dict[str, Any]) -> dict[str, Any]:
    """Project UE5 world (X, Y) + yaw_deg onto a 2048x2048 paper map using Bloober's exact formula."""
    rot = float(map_meta['rotation_deg'])
    rad = math.radians(rot)
    s, c = math.sin(rad), math.cos(rad)
    ox, oy = map_meta['origin_xy']
    scale = float(map_meta['scale_px_per_cm'])
    dx = (wx - ox) * scale
    dy = (wy - oy) * scale
    px = 1024.0 + (dx * c - dy * s)
    py = 1024.0 + (dy * c + dx * s)
    angle = (yaw_deg + 90.0 + rot) % 360.0
    in_bounds = -96.0 <= px <= 2144.0 and -96.0 <= py <= 2144.0
    return {
        'px': round(px, 2),
        'py': round(py, 2),
        'angle_deg': round(angle, 2),
        'in_bounds': in_bounds,
    }


def inspect_exe_fingerprint(exe_path: Path | str | None = None) -> dict[str, Any]:
    p = Path(exe_path) if exe_path else paths.shipping_exe()
    if not p or not p.is_file():
        return {'found': False, 'matched': False}
    try:
        size = p.stat().st_size
        with p.open('rb') as f:
            head = f.read(4096)
        if len(head) < 0x200 or head[:2] != b'MZ':
            return {'found': True, 'matched': False}
        e_lfanew, = struct.unpack_from('<I', head, 0x3C)
        if e_lfanew + 24 > len(head) or head[e_lfanew:e_lfanew + 4] != b'PE\x00\x00':
            return {'found': True, 'matched': False}
        pe_ts, = struct.unpack_from('<I', head, e_lfanew + 8)
        hdr_sha = hashlib.sha256(head).hexdigest()
        prof = KNOWN_BUILDS.get((size, pe_ts))
        matched = bool(prof and prof['header_sha256'] == hdr_sha)
        return {
            'found': True,
            'size': size,
            'pe_timestamp': pe_ts,
            'header_sha256': hdr_sha,
            'matched': matched,
            'version': prof['version'] if matched and prof else None,
        }
    except OSError:
        return {'found': False, 'matched': False}


def _normalized_loaded_header_sha256(hdr_bytes: bytes) -> str | None:
    if len(hdr_bytes) < 0x200 or hdr_bytes[:2] != b'MZ':
        return None
    e_lfanew, = struct.unpack_from('<I', hdr_bytes, 0x3C)
    if e_lfanew + 0x58 > len(hdr_bytes) or hdr_bytes[e_lfanew:e_lfanew + 4] != b'PE\x00\x00':
        return None
    buf = bytearray(hdr_bytes)
    # Zero relocated ImageBase in OptionalHeader64 (+24 + 24 = +48 from PE signature)
    img_base_off = e_lfanew + 24 + 24
    buf[img_base_off:img_base_off + 8] = b'\x00' * 8
    return hashlib.sha256(bytes(buf)).hexdigest()


if os.name == 'nt':
    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ProcessID', wt.DWORD),
            ('th32DefaultHeapID', ctypes.c_size_t), ('th32ModuleID', wt.DWORD),
            ('cntThreads', wt.DWORD), ('th32ParentProcessID', wt.DWORD),
            ('pcPriClassBase', wt.LONG), ('dwFlags', wt.DWORD),
            ('szExeFile', wt.WCHAR * 260),
        ]

    class _MODULEENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', wt.DWORD), ('th32ModuleID', wt.DWORD), ('th32ProcessID', wt.DWORD),
            ('GlblcntUsage', wt.DWORD), ('ProccntUsage', wt.DWORD),
            ('modBaseAddr', ctypes.c_void_p), ('modBaseSize', wt.DWORD),
            ('hModule', wt.HMODULE), ('szModule', wt.WCHAR * 256),
            ('szExePath', wt.WCHAR * 260),
        ]

    _k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    _k32.OpenProcess.restype = wt.HANDLE
    _k32.CloseHandle.argtypes = [wt.HANDLE]
    _k32.CloseHandle.restype = wt.BOOL
    _k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
    _k32.GetExitCodeProcess.restype = wt.BOOL
    _k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    _k32.ReadProcessMemory.restype = wt.BOOL
else:
    _k32 = None


@lru_cache(maxsize=1)
def map_enum_tag_by_id() -> dict[int, str]:
    out = {int(mid): str(m['enum_tag']) for mid, m in load_maps_by_id().items() if m.get('enum_tag')}
    out.setdefault(34, 'Hospital_FW_RF')
    out.setdefault(54, 'Hospital_OW_RF')
    out.setdefault(82, 'LakeviewHotel_FW_1F')
    return out


def _is_valid_ptr(addr: int) -> bool:
    return 0x10000 <= addr <= 0x7FFFFFFFFFFF


def decode_fname_entry(entry_bytes: bytes) -> str | None:
    """Decode one UE 5.1 FNameEntry buffer starting at the 2-byte header."""
    if len(entry_bytes) < 2:
        return None
    hdr, = struct.unpack_from('<H', entry_bytes, 0)
    is_wide = bool(hdr & 1)
    length = hdr >> 6
    if length == 0:
        return ''
    if length > 512:
        return None
    nbytes = length * (2 if is_wide else 1)
    if len(entry_bytes) < 2 + nbytes:
        return None
    raw = entry_bytes[2:2 + nbytes]
    try:
        return raw.decode('utf-16le' if is_wide else 'utf-8', errors='replace')
    except UnicodeDecodeError:
        return raw.decode('latin-1', errors='replace')


def format_fname(base_name: str, number: int) -> str:
    return f'{base_name}_{number - 1}' if number > 0 else base_name


def read_fname(
    mr: Any,
    blocks_base: int,
    comp_idx: int,
    number: int,
    cache: dict[int, str],
    block_cache: dict[int, int],
) -> str | None:
    if comp_idx == 0:
        return 'None'
    if number < 0 or number > 100000:
        return None
    base = cache.get(comp_idx)
    if base is None:
        blk_i = comp_idx >> 16
        if blk_i < 0 or blk_i >= 8192:
            return None
        blk_ptr = block_cache.get(blk_i)
        if not blk_ptr:
            blk_ptr = mr.ptr(blocks_base + blk_i * 8)
            if not blk_ptr:
                return None
            block_cache[blk_i] = blk_ptr
        entry_addr = blk_ptr + (comp_idx & 0xFFFF) * 2
        hdr_raw = mr.read(entry_addr, 2)
        if not hdr_raw:
            return None
        hdr, = struct.unpack('<H', hdr_raw)
        is_wide = bool(hdr & 1)
        length = hdr >> 6
        if length > 512:
            return None
        if length == 0:
            base = ''
        else:
            nbytes = length * (2 if is_wide else 1)
            str_raw = mr.read(entry_addr + 2, nbytes)
            if not str_raw:
                return None
            base = decode_fname_entry(hdr_raw + str_raw)
            if base is None:
                return None
        if len(cache) >= 16384:
            cache.clear()
        cache[comp_idx] = base
    return format_fname(base, number)


def read_uobject_class_name(
    mr: Any,
    obj_ptr: int,
    blocks_base: int,
    offs: dict[str, int],
    cache: dict[int, str],
    block_cache: dict[int, int],
) -> str | None:
    if not _is_valid_ptr(obj_ptr):
        return None
    cls_ptr = mr.ptr(obj_ptr + offs['uobject_class'])
    if not cls_ptr:
        return None
    nm_raw = mr.read(cls_ptr + offs['uobject_name'], 8)
    if not nm_raw:
        return None
    comp_idx, num = struct.unpack('<II', nm_raw)
    return read_fname(mr, blocks_base, comp_idx, num, cache, block_cache)


def iter_tsparse_active_indices(
    hdr_bytes: bytes,
    read_secondary_fn: Callable[[int, int], bytes | None] | None = None,
    max_slots: int = 4096,
) -> list[int]:
    """Return active slot indices from a UE 5.1 TSet/TMap/TSparseArray 0x38-byte header."""
    if len(hdr_bytes) < 0x38:
        return []
    data_ptr, array_num, _array_max = struct.unpack_from('<Qii', hdr_bytes, 0x00)
    if not _is_valid_ptr(data_ptr) or array_num <= 0 or array_num > max_slots:
        return []
    secondary_ptr, num_bits, _max_bits, _first_free, num_free = struct.unpack_from('<Qiiii', hdr_bytes, 0x20)
    if array_num <= num_free or num_free < 0:
        return []
    limit = min(array_num, num_bits) if num_bits > 0 else array_num
    if limit <= 0 or limit > max_slots:
        return []
    n_words = (limit + 31) // 32
    if _is_valid_ptr(secondary_ptr):
        if not read_secondary_fn:
            return []
        bits_raw = read_secondary_fn(secondary_ptr, n_words * 4)
        if not bits_raw or len(bits_raw) < n_words * 4:
            return []
        words = struct.unpack_from(f'<{n_words}I', bits_raw, 0)
    else:
        if n_words > 4:
            return []
        words = struct.unpack_from(f'<{n_words}I', hdr_bytes, 0x10)
    active: list[int] = []
    for wi, word in enumerate(words):
        if not word:
            continue
        base_idx = wi * 32
        for b in range(32):
            idx = base_idx + b
            if idx >= limit:
                break
            if (word >> b) & 1:
                active.append(idx)
    return active


def read_tsparse_elements(mr: Any, map_addr: int, stride: int, max_slots: int = 4096) -> list[bytes]:
    if not _is_valid_ptr(map_addr) or stride <= 0:
        return []
    hdr = mr.read(map_addr, 0x38)
    if not hdr:
        return []
    active = iter_tsparse_active_indices(hdr, mr.read, max_slots=max_slots)
    if not active:
        return []
    data_ptr, = struct.unpack_from('<Q', hdr, 0x00)
    span = active[-1] + 1
    raw = mr.read(data_ptr, span * stride)
    if not raw:
        return []
    return [raw[i * stride:(i + 1) * stride] for i in active]


def parse_collected_items(raw: bytes, resolve_fname: Callable[[int, int], str | None]) -> dict[str, int]:
    """Decode TArray<FSHCollectedItemData> (0x0C stride: FName + int32 Quantity)."""
    out: dict[str, int] = {}
    for off in range(0, len(raw) - (len(raw) % 0x0C), 0x0C):
        comp_idx, num, qty = struct.unpack_from('<IIi', raw, off)
        if comp_idx == 0 or qty < 0:
            continue
        name = resolve_fname(comp_idx, num)
        if name and name != 'None':
            out[name] = qty
    return out


def parse_fname_int_map(elements: list[bytes], resolve_fname: Callable[[int, int], str | None]) -> dict[str, int]:
    """Decode TMap<FName, int32> elements (0x14 stride: FName +0x00, int32 +0x08)."""
    out: dict[str, int] = {}
    for elem in elements:
        if len(elem) < 0x0C:
            continue
        comp_idx, num, val = struct.unpack_from('<IIi', elem, 0)
        if comp_idx == 0:
            continue
        name = resolve_fname(comp_idx, num)
        if name and name != 'None':
            out[name] = val
    return out


def parse_fname_bool_map(elements: list[bytes], resolve_fname: Callable[[int, int], str | None]) -> dict[str, bool]:
    """Decode TMap<FName, bool> elements (0x14 stride: FName +0x00, bool +0x08)."""
    out: dict[str, bool] = {}
    for elem in elements:
        if len(elem) < 0x09:
            continue
        comp_idx, num, val = struct.unpack_from('<IIB', elem, 0)
        if comp_idx == 0:
            continue
        name = resolve_fname(comp_idx, num)
        if name and name != 'None':
            out[name] = bool(val)
    return out


def parse_map_objects_entry(inner_raw: bytes, resolve_fname: Callable[[int, int], str | None]) -> dict[str, dict[str, Any]]:
    """Decode inner TArray<SHMapObjectDataStruct> (0x10 stride: FName +0x00, Map u8 +0x08, Type u8 +0x09, Value i32 +0x0C)."""
    out: dict[str, dict[str, Any]] = {}
    for off in range(0, len(inner_raw) - (len(inner_raw) % 0x10), 0x10):
        comp_idx, num, _map_id, otype, _pad, val = struct.unpack_from('<IIBBHi', inner_raw, off)
        if comp_idx == 0:
            continue
        oid = resolve_fname(comp_idx, num)
        if oid and oid != 'None':
            out[oid] = {'type': MAP_OBJ_TYPE_NAMES.get(otype, 'None'), 'val': int(val)}
    return out


def _read_tarray_header(mr: Any, arr_addr: int, max_num: int = 4096) -> tuple[int, int]:
    hdr = mr.read(arr_addr, 12)
    if not hdr:
        return 0, 0
    data_ptr, num = struct.unpack('<Qi', hdr)
    if not _is_valid_ptr(data_ptr) or num <= 0 or num > max_num:
        return 0, 0
    return data_ptr, num


def _find_process() -> tuple[int, int, str] | None:
    if os.name != 'nt' or _k32 is None:
        return None
    snap = _k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == wt.HANDLE(-1).value:
        return None
    try:
        pe = _PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(pe)
        if not _k32.Process32FirstW(snap, ctypes.byref(pe)):
            return None
        target_pid = 0
        while True:
            if pe.szExeFile.lower() == MODULE_NAME.lower():
                target_pid = int(pe.th32ProcessID)
                break
            if not _k32.Process32NextW(snap, ctypes.byref(pe)):
                break
        if not target_pid:
            return None
    finally:
        _k32.CloseHandle(snap)

    msnap = _k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, target_pid)
    if msnap == wt.HANDLE(-1).value:
        return None
    try:
        me = _MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(me)
        if not _k32.Module32FirstW(msnap, ctypes.byref(me)):
            return None
        while True:
            if me.szModule.lower() == MODULE_NAME.lower():
                return target_pid, int(me.modBaseAddr or 0), str(me.szExePath)
            if not _k32.Module32NextW(msnap, ctypes.byref(me)):
                break
    finally:
        _k32.CloseHandle(msnap)
    return None


class _MemReader:
    def __init__(self, handle: int):
        self.h = handle

    def read(self, addr: int, size: int) -> bytes | None:
        if not _is_valid_ptr(addr) or size <= 0 or size > 4 * 1024 * 1024:
            return None
        buf = (ctypes.c_char * size)()
        nread = ctypes.c_size_t(0)
        ok = _k32.ReadProcessMemory(self.h, ctypes.c_void_p(addr), buf, size, ctypes.byref(nread))
        if not ok or nread.value != size:
            return None
        return buf.raw

    def ptr(self, addr: int) -> int:
        raw = self.read(addr, 8)
        if not raw:
            return 0
        v, = struct.unpack('<Q', raw)
        return v if _is_valid_ptr(v) else 0

    def vec3d(self, addr: int) -> tuple[float, float, float] | None:
        raw = self.read(addr, 24)
        if not raw:
            return None
        vals = struct.unpack('<3d', raw)
        if not all(math.isfinite(x) and abs(x) < 1e7 for x in vals):
            return None
        return vals


class LiveSession:
    """Thread-safe persistent read-only handle (0x0410) + FName cache for zero-lag polling."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pid: int = 0
        self._mod_base: int = 0
        self._handle: int = 0
        self._prof: dict[str, Any] | None = None
        self._mr: _MemReader | None = None
        self._fname_cache: dict[int, str] = {}
        self._block_cache: dict[int, int] = {}
        self._last_probe_ts: float = 0.0
        self._cached_closed: dict[str, Any] | None = None

    def close(self) -> None:
        with self._lock:
            self._reset_handle()

    def _reset_handle(self) -> None:
        if self._handle and _k32 is not None:
            try:
                _k32.CloseHandle(self._handle)
            except Exception:
                pass
        self._pid = 0
        self._mod_base = 0
        self._handle = 0
        self._prof = None
        self._mr = None
        self._fname_cache.clear()
        self._block_cache.clear()

    def _handle_alive(self) -> bool:
        if not self._handle or _k32 is None or self._prof is None or self._mr is None:
            return False
        code = wt.DWORD(0)
        if not _k32.GetExitCodeProcess(self._handle, ctypes.byref(code)) or code.value != STILL_ACTIVE:
            return False
        # Fast probe that the base module header is still mapped
        hdr_probe = self._mr.read(self._mod_base, 4)
        return hdr_probe is not None and hdr_probe[:2] == b'MZ'

    def _attach(self) -> tuple[bool, dict[str, Any] | None]:
        if os.name != 'nt' or _k32 is None:
            fp = inspect_exe_fingerprint()
            return False, {
                'available': False, 'process_running': False, 'reason_code': 'game_closed',
                'build_fingerprint': {k: v for k, v in fp.items() if k in ('matched', 'version')},
            }
        if self._handle_alive():
            return True, None

        self._reset_handle()
        now = time.monotonic()
        if self._cached_closed is not None and (now - self._last_probe_ts) < 0.45:
            return False, dict(self._cached_closed)
        self._last_probe_ts = now

        proc = _find_process()
        if not proc:
            fp = inspect_exe_fingerprint()
            res = {
                'available': False, 'process_running': False, 'reason_code': 'game_closed',
                'build_fingerprint': {k: v for k, v in fp.items() if k in ('matched', 'version')},
            }
            self._cached_closed = res
            return False, dict(res)

        self._cached_closed = None
        pid, mod_base, exe_path = proc
        fp = inspect_exe_fingerprint(exe_path)
        if not fp.get('found'):
            return False, {
                'available': False, 'process_running': True, 'reason_code': 'build_unverified',
                'build_fingerprint': {'matched': False},
            }
        if not fp.get('matched'):
            return False, {
                'available': False, 'process_running': True, 'reason_code': 'unsupported_build',
                'build_fingerprint': {'matched': False},
            }

        prof = KNOWN_BUILDS[(fp['size'], fp['pe_timestamp'])]
        handle = _k32.OpenProcess(SAFE_ACCESS_MASK, False, pid)
        if not handle:
            return False, {
                'available': False, 'process_running': True, 'reason_code': 'memory_unavailable',
                'build_fingerprint': {'matched': True, 'version': prof['version']},
            }
        mr = _MemReader(handle)
        hdr_mem = mr.read(mod_base, prof['size_of_headers'])
        if not hdr_mem or _normalized_loaded_header_sha256(hdr_mem) != prof['loaded_header_key']:
            _k32.CloseHandle(handle)
            return False, {
                'available': False, 'process_running': True, 'reason_code': 'unsupported_build',
                'build_fingerprint': {'matched': False},
            }
        self._pid = pid
        self._mod_base = mod_base
        self._handle = handle
        self._prof = prof
        self._mr = mr
        return True, None

    def _read_extended(self, mr: _MemReader, pawn: int, mcomp: int, offs: dict[str, int], prof: dict[str, Any]) -> dict[str, Any]:
        blocks_base = self._mod_base + prof['gnames_blocks_rva']
        resolve_fn = lambda cidx, num: read_fname(mr, blocks_base, cidx, num, self._fname_cache, self._block_cache)
        ext: dict[str, Any] = {}

        # 1. USHCharacterPlayItemsComponent -> CollectedItems + EquipmentStateValues
        icomp = mr.ptr(pawn + offs['char_items_comp'])
        if icomp:
            arr_ptr, num = _read_tarray_header(mr, icomp + offs['items_collected_arr'], max_num=2048)
            if arr_ptr and num > 0:
                raw_items = mr.read(arr_ptr, num * 0x0C)
                if raw_items:
                    ext['items'] = parse_collected_items(raw_items, resolve_fn)
            elif mr.read(icomp + offs['items_collected_arr'], 12):
                ext['items'] = {}
            eq_elems = read_tsparse_elements(mr, icomp + offs['items_equip_map'], stride=0x14, max_slots=256)
            if eq_elems:
                ext['equipment'] = parse_fname_bool_map(eq_elems, resolve_fn)

        # 2. USHCharacterPlayCombatComponent -> RangedSubcomp + WeaponManageSubcomp
        ccomp = mr.ptr(pawn + offs['char_combat_comp'])
        if ccomp:
            ranged_ptr = mr.ptr(ccomp + offs['combat_ranged_subcomp'])
            if ranged_ptr:
                cls = read_uobject_class_name(mr, ranged_ptr, blocks_base, offs, self._fname_cache, self._block_cache)
                if cls != 'SHRangedCmbSubcomp':
                    ranged_ptr = 0
            wmgr_ptr = mr.ptr(ccomp + offs['combat_weapon_mgr_subcomp'])
            if wmgr_ptr:
                cls = read_uobject_class_name(mr, wmgr_ptr, blocks_base, offs, self._fname_cache, self._block_cache)
                if cls != 'SHWeaponManageCmbSubcomp':
                    wmgr_ptr = 0
            if not ranged_ptr or not wmgr_ptr:
                for sub_elem in read_tsparse_elements(mr, ccomp + offs['combat_owned_subcomps'], stride=0x10, max_slots=128):
                    sptr, = struct.unpack_from('<Q', sub_elem, 0)
                    if not _is_valid_ptr(sptr):
                        continue
                    scls = read_uobject_class_name(mr, sptr, blocks_base, offs, self._fname_cache, self._block_cache)
                    if not ranged_ptr and scls == 'SHRangedCmbSubcomp':
                        ranged_ptr = sptr
                    elif not wmgr_ptr and scls == 'SHWeaponManageCmbSubcomp':
                        wmgr_ptr = sptr
            if ranged_ptr:
                ammo_elems = read_tsparse_elements(mr, ranged_ptr + offs['ranged_ammo_map'], stride=0x14, max_slots=64)
                if ammo_elems:
                    ext['ammo_loaded'] = parse_fname_int_map(ammo_elems, resolve_fn)
            if wmgr_ptr:
                eq_wep = mr.ptr(wmgr_ptr + offs['wmgr_equipped_weapon'])
                ext['weapon_drawn'] = bool(eq_wep)
                lw_raw = mr.read(wmgr_ptr + offs['wmgr_last_weapon'], 8)
                if lw_raw:
                    cidx, num = struct.unpack('<II', lw_raw)
                    wname = resolve_fn(cidx, num)
                    if wname and wname != 'None':
                        ext['last_used_weapon'] = wname

        # 3. USHCharacterPlayMapComponent -> MapsObjectsData (live red-pen marks)
        if mcomp:
            tag_by_id = map_enum_tag_by_id()
            mod_elems = read_tsparse_elements(mr, mcomp + offs['map_objects_map'], stride=0x20, max_slots=128)
            if mod_elems:
                live_mo: dict[str, dict[str, dict[str, Any]]] = {}
                for elem in mod_elems:
                    map_id = elem[0]
                    tag = tag_by_id.get(map_id)
                    if not tag:
                        continue
                    inner_ptr, inner_num = struct.unpack_from('<Qi', elem, 0x08)
                    if _is_valid_ptr(inner_ptr) and 0 < inner_num <= 2048:
                        inner_raw = mr.read(inner_ptr, inner_num * 0x10)
                        if inner_raw:
                            parsed_inner = parse_map_objects_entry(inner_raw, resolve_fn)
                            if parsed_inner:
                                live_mo[tag] = parsed_inner
                if live_mo:
                    ext['map_objects'] = live_mo

        # 4. USHCharacterPlayStatisticsComponent -> kills, weapon_kills, memos, stats
        scomp = mr.ptr(pawn + offs['char_stats_comp'])
        if scomp:
            procs: dict[str, int] = {}
            for pname, pkey in (
                ('SHAnimsPlayedStatisticsValueProcessor', 'stats_proc_anims'),
                ('SHCombatStatisticsValueProcessor', 'stats_proc_combat'),
                ('SHDistanceTravelledStatisticsValueProcessor', 'stats_proc_distance'),
                ('SHItemsInvestigationStatisticsValueProcessor', 'stats_proc_invest'),
                ('SHItemsPickedUpStatisticsValueProcessor', 'stats_proc_picked'),
            ):
                pptr = mr.ptr(scomp + offs[pkey])
                if pptr and read_uobject_class_name(mr, pptr, blocks_base, offs, self._fname_cache, self._block_cache) == pname:
                    procs[pname] = pptr
            if len(procs) < 5:
                parr_ptr, pnum = _read_tarray_header(mr, scomp + offs['stats_processors_arr'], max_num=32)
                if parr_ptr and pnum > 0:
                    praw = mr.read(parr_ptr, pnum * 8)
                    if praw:
                        for (pptr,) in struct.iter_unpack('<Q', praw):
                            if _is_valid_ptr(pptr):
                                cls = read_uobject_class_name(mr, pptr, blocks_base, offs, self._fname_cache, self._block_cache)
                                if cls:
                                    procs[cls] = pptr

            live_stats: dict[str, Any] = {}
            cp = procs.get('SHCombatStatisticsValueProcessor')
            if cp:
                cbuf = mr.read(cp + offs['stat_combat_melee'], 0x1C)
                if cbuf:
                    km, kr, shots, dodges, glass, heals, dmg = struct.unpack('<6if', cbuf)
                    live_stats['kills_melee'] = int(km)
                    live_stats['kills_ranged'] = int(kr)
                    live_stats['kills'] = int(km) + int(kr)
                    live_stats['shots_fired'] = int(shots)
                    live_stats['dodges'] = int(dodges)
                    live_stats['broken_glass'] = int(glass)
                    live_stats['heals_used'] = int(heals)
                    if math.isfinite(dmg):
                        live_stats['damage_taken'] = round(float(dmg), 1)
                wk_elems = read_tsparse_elements(mr, cp + offs['stat_combat_weapon_kills_map'], stride=0x14, max_slots=64)
                if wk_elems:
                    ext['weapon_kills'] = parse_fname_int_map(wk_elems, resolve_fn)

            ap = procs.get('SHAnimsPlayedStatisticsValueProcessor')
            if ap:
                araw = mr.read(ap + offs['stat_anims_locked_doors'], 4)
                if araw:
                    live_stats['locked_doors_checked'] = struct.unpack('<i', araw)[0]

            dp = procs.get('SHDistanceTravelledStatisticsValueProcessor')
            if dp:
                draw = mr.read(dp + offs['stat_dist_cm'], 4)
                if draw:
                    dist_cm, = struct.unpack('<i', draw)
                    if dist_cm >= 0:
                        live_stats['distance_m'] = round(float(dist_cm) / 100.0)

            ip = procs.get('SHItemsInvestigationStatisticsValueProcessor')
            if ip:
                iraw = mr.read(ip + offs['stat_invest_maps'], 4)
                if iraw:
                    live_stats['investigated'] = struct.unpack('<i', iraw)[0]

            pp = procs.get('SHItemsPickedUpStatisticsValueProcessor')
            if pp:
                praw = mr.read(pp + offs['stat_picked_consumables'], 4)
                if praw:
                    live_stats['consumables_picked'] = struct.unpack('<i', praw)[0]
                marr_ptr, mnum = _read_tarray_header(mr, pp + offs['stat_picked_memos_arr'], max_num=512)
                if marr_ptr and mnum > 0:
                    mraw = mr.read(marr_ptr, mnum * 8)
                    if mraw:
                        memos = []
                        for cidx, num in struct.iter_unpack('<II', mraw):
                            mname = resolve_fn(cidx, num)
                            if mname and mname != 'None':
                                memos.append(mname)
                        ext['memos'] = memos

            if live_stats:
                ext['stats'] = live_stats

        return ext

    def read(
        self,
        selected_slug: str | None = None,
        active_save_slug: str | None = None,
        include_extended: bool = True,
    ) -> dict[str, Any]:
        with self._lock:
            ok, err = self._attach()
            if not ok or self._mr is None or self._prof is None:
                return err or {'available': False, 'process_running': False, 'reason_code': 'game_closed'}

            mr = self._mr
            prof = self._prof
            offs = prof['offsets']
            uworld = mr.ptr(self._mod_base + prof['gworld_rva'])
            if not uworld:
                return {'available': False, 'process_running': True, 'reason_code': 'memory_unavailable',
                        'build_fingerprint': {'matched': True, 'version': prof['version']}}
            gi = mr.ptr(uworld + offs['world_game_instance'])
            lp_arr = mr.ptr(gi + offs['gi_local_players']) if gi else 0
            lp0 = mr.ptr(lp_arr) if lp_arr else 0
            pc = mr.ptr(lp0 + offs['lp_player_controller']) if lp0 else 0
            if not pc:
                return {'available': False, 'process_running': True, 'reason_code': 'memory_unavailable',
                        'build_fingerprint': {'matched': True, 'version': prof['version']}}

            pawn = mr.ptr(pc + offs['pc_ack_pawn']) or mr.ptr(pc + offs['pc_pawn'])
            root = mr.ptr(pawn + offs['actor_root_comp']) if pawn else 0
            pos = mr.vec3d(root + offs['sc_comp_to_world_pos']) if root else None
            if not pos or (pos[0] == 0.0 and pos[1] == 0.0 and pos[2] == 0.0):
                return {'available': False, 'process_running': True, 'reason_code': 'memory_unavailable',
                        'build_fingerprint': {'matched': True, 'version': prof['version']}}

            body_yaw = 0.0
            qraw = mr.read(root + offs['sc_comp_to_world_rot'], 32)
            if qraw:
                qx, qy, qz, qw = struct.unpack('<4d', qraw)
                if all(math.isfinite(v) for v in (qx, qy, qz, qw)):
                    body_yaw = sh2_save.quat_to_yaw_deg(qx, qy, qz, qw)

            cam_mgr = mr.ptr(pc + offs['pc_camera_mgr'])
            cam_yaw = body_yaw
            cam_fov = 70.0
            if cam_mgr:
                cam_rot = mr.vec3d(cam_mgr + offs['cam_pov_rot'])
                if cam_rot:
                    cam_yaw = round(cam_rot[1], 2)
                fov_raw = mr.read(cam_mgr + offs['cam_pov_fov'], 4)
                if fov_raw:
                    fv, = struct.unpack('<f', fov_raw)
                    if 20.0 <= fv <= 150.0:
                        cam_fov = round(fv, 1)

            health = None
            health_state = None
            hcomp = mr.ptr(pawn + offs['char_health_comp'])
            if hcomp:
                hraw = mr.read(hcomp + offs['health_value'], 4)
                if hraw:
                    hv, = struct.unpack('<f', hraw)
                    if 0.0 <= hv <= 200.0:
                        health = round(hv, 1)
                hsraw = mr.read(hcomp + offs['health_state'], 1)
                if hsraw:
                    health_state = hsraw[0]

            maps_by_id = load_maps_by_id()
            maps_by_slug = load_maps_by_slug()
            live_slug = None
            mcomp = mr.ptr(pawn + offs['char_map_comp'])
            if mcomp:
                arr_hdr = mr.read(mcomp + offs['map_volumes_arr'], 12)
                if arr_hdr:
                    vdata, vnum = struct.unpack('<Qi', arr_hdr)
                    if 1 <= vnum <= 16 and _is_valid_ptr(vdata):
                        ptrs_raw = mr.read(vdata, vnum * 8)
                        if ptrs_raw:
                            vol_hits = []
                            for (vptr,) in struct.iter_unpack('<Q', ptrs_raw):
                                eb = mr.read(vptr + offs['map_volume_enum'], 1) if vptr else None
                                if eb:
                                    mid = eb[0]
                                    if mid == 34:
                                        mid = 32
                                    elif mid == 54:
                                        mid = 52
                                    elif mid == 82:
                                        mid = 81
                                    mmeta = maps_by_id.get(mid)
                                    if mmeta:
                                        prio = mmeta['priority'] if mmeta['priority'] is not None else -1
                                        vol_hits.append((prio, mmeta['slug']))
                            if vol_hits:
                                vol_hits.sort(reverse=True)
                                live_slug = vol_hits[0][1]

            if not live_slug:
                live_slug = sh2_save.resolve_world_to_map(pos) or active_save_slug or 'city-east'

            input_mode = None
            im_raw = mr.read(pawn + offs['char_input_mode'], 1)
            if im_raw:
                input_mode = im_raw[0]

            active_meta = maps_by_slug.get(live_slug)
            active_proj = project_world_to_sheet(pos[0], pos[1], cam_yaw, active_meta) if active_meta else None

            selected_proj = None
            if selected_slug and selected_slug in maps_by_slug and active_meta:
                sel_meta = maps_by_slug[selected_slug]
                same_space = (
                    selected_slug == live_slug
                    or sel_meta['region'] == active_meta['region']
                    or sel_meta.get('twin') == live_slug
                    or active_meta.get('twin') == selected_slug
                )
                if same_space:
                    p_sel = project_world_to_sheet(pos[0], pos[1], cam_yaw, sel_meta)
                    if p_sel['in_bounds']:
                        selected_proj = p_sel

            out: dict[str, Any] = {
                'available': True,
                'process_running': True,
                'active_map_slug': live_slug,
                'world_pos': [round(pos[0], 1), round(pos[1], 1), round(pos[2], 1)],
                'body_yaw': body_yaw,
                'camera_yaw': cam_yaw,
                'fov': cam_fov,
                'health': health,
                'health_state': health_state,
                'in_game_menu': input_mode == 4,
                'active_projection': active_proj,
                'selected_projection': selected_proj,
                'build_fingerprint': {'matched': True, 'version': prof['version']},
            }
            if include_extended:
                try:
                    out.update(self._read_extended(mr, pawn, mcomp, offs, prof))
                except Exception:
                    pass
            return out


_DEFAULT_SESSION = LiveSession()


def read_live_telemetry(
    selected_slug: str | None = None,
    active_save_slug: str | None = None,
    include_extended: bool = True,
) -> dict[str, Any]:
    """Read live James world coordinates, camera yaw/FOV, health, active map, and inventory/combat state."""
    return _DEFAULT_SESSION.read(
        selected_slug=selected_slug,
        active_save_slug=active_save_slug,
        include_extended=include_extended,
    )
