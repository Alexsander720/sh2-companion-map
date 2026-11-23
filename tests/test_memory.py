"""Tests for factory world->sheet coordinate projection and PE fingerprint safety."""
from __future__ import annotations

import math
import struct

import sh2_memory


def test_all_41_maps_reproject_anchors_within_1px():
    maps = sh2_memory.load_maps_by_slug()
    assert len(maps) == 41
    for slug, m in maps.items():
        a1w, a2w = m['anchor1_world'], m['anchor2_world']
        a1u, a2u = m['anchor1_ui'], m['anchor2_ui']
        p1 = sh2_memory.project_world_to_sheet(a1w[0], a1w[1], 0.0, m)
        p2 = sh2_memory.project_world_to_sheet(a2w[0], a2w[1], 0.0, m)
        err1 = math.hypot(p1['px'] - (1024.0 + a1u[0]), p1['py'] - (1024.0 + a1u[1]))
        err2 = math.hypot(p2['px'] - (1024.0 + a2u[0]), p2['py'] - (1024.0 + a2u[1]))
        dist_proj = math.hypot(p2['px'] - p1['px'], p2['py'] - p1['py'])
        dist_ui = math.hypot(a2u[0] - a1u[0], a2u[1] - a1u[1])
        assert err1 < 0.05, f'{slug} anchor1 error {err1}'
        assert abs(dist_proj - dist_ui) < 0.05, f'{slug} isotropic scale error'
        assert err2 < 60.0, f'{slug} anchor2 directional drift {err2}'


def test_pointer_rotation_formula():
    maps = sh2_memory.load_maps_by_slug()
    # Hospital FW 1F has +90 deg map rotation
    hosp = maps['hospital-fw-1f']
    p = sh2_memory.project_world_to_sheet(hosp['origin_xy'][0], hosp['origin_xy'][1], 0.0, hosp)
    assert p['px'] == 1024.0 and p['py'] == 1024.0
    assert p['angle_deg'] == 180.0

    # Prison 1F Main has -90 deg map rotation
    prison = maps['prison-1f-main']
    p_pr = sh2_memory.project_world_to_sheet(prison['origin_xy'][0], prison['origin_xy'][1], 0.0, prison)
    assert p_pr['angle_deg'] == 0.0


def test_unmatched_exe_rejected(tmp_path):
    fake_exe = tmp_path / 'SHProto-Win64-Shipping.exe'
    fake_exe.write_bytes(b'MZ' + b'\x00' * 4096)
    fp = sh2_memory.inspect_exe_fingerprint(fake_exe)
    assert fp['matched'] is False


def test_fname_decode_narrow_wide_and_numbered():
    # Narrow: length 6 << 6 = 0x180
    buf_narrow = struct.pack('<H', 6 << 6) + b'Pistol'
    assert sh2_memory.decode_fname_entry(buf_narrow) == 'Pistol'
    assert sh2_memory.format_fname('Pistol', 0) == 'Pistol'
    assert sh2_memory.format_fname('WsaFW_Note', 3) == 'WsaFW_Note_2'

    # Wide UTF-16LE: length 4 << 6 | 1
    buf_wide = struct.pack('<H', (4 << 6) | 1) + 'Тест'.encode('utf-16le')
    assert sh2_memory.decode_fname_entry(buf_wide) == 'Тест'

    # Out-of-range length rejected cleanly
    assert sh2_memory.decode_fname_entry(struct.pack('<H', 600 << 6) + b'x' * 8) is None


def test_tsparse_inline_and_secondary_bitmasks():
    # 5 slots allocated (num_bits=5, array_num=5), free slot at bit 2 -> bits 0,1,3,4 active (0b11011 = 27)
    inline_hdr = struct.pack('<Qii4IQiiii', 0x200000, 5, 8, 0b11011, 0, 0, 0, 0, 5, 128, 2, 1)
    assert sh2_memory.iter_tsparse_active_indices(inline_hdr) == [0, 1, 3, 4]

    # Secondary bitmask (>128 slots): word0=0x1, word4 (bit 130 -> word4 bit 2) = 0x4
    sec_hdr = struct.pack('<Qii4IQiiii', 0x200000, 132, 160, 0, 0, 0, 0, 0x300000, 132, 160, -1, 130)
    sec_words = struct.pack('<5I', 0b101, 0, 0, 0, 0b100)
    assert sh2_memory.iter_tsparse_active_indices(sec_hdr, lambda addr, sz: sec_words[:sz]) == [0, 2, 130]


def test_parse_inventory_ammo_equipment_and_map_objects():
    names = {1: 'HealthDrink', 2: 'Pistol', 3: 'Flashlight', 4: 'Radio', 5: 'F2_SAFE'}
    resolve = lambda cidx, num: sh2_memory.format_fname(names[cidx], num) if cidx in names else None

    raw_items = struct.pack('<IIiIIi', 1, 0, 4, 2, 0, 1)
    assert sh2_memory.parse_collected_items(raw_items, resolve) == {'HealthDrink': 4, 'Pistol': 1}

    elem_ammo = struct.pack('<IIiII', 2, 0, 9, 0xFFFFFFFF, 0)
    assert sh2_memory.parse_fname_int_map([elem_ammo], resolve) == {'Pistol': 9}

    elem_eq = [
        struct.pack('<IIB3xII', 3, 0, 1, 0xFFFFFFFF, 0),
        struct.pack('<IIB3xII', 4, 0, 0, 0xFFFFFFFF, 1),
    ]
    assert sh2_memory.parse_fname_bool_map(elem_eq, resolve) == {'Flashlight': True, 'Radio': False}

    raw_mo = struct.pack('<IIBBHi', 5, 0, 21, 2, 0, 1)  # type 2 = Puzzle, val = 1
    assert sh2_memory.parse_map_objects_entry(raw_mo, resolve) == {'F2_SAFE': {'type': 'Puzzle', 'val': 1}}
