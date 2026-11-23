"""Synthetic unit tests for VASb + GVAS + UcaSave save parsing."""
from __future__ import annotations

import struct
import zlib

import sh2_save


def _pack_fstr(s: str) -> bytes:
    if not s:
        return struct.pack('<i', 0)
    raw = s.encode('utf-8') + b'\x00'
    return struct.pack('<i', len(raw)) + raw


def _pack_transform(tx: float, ty: float, tz: float) -> bytes:
    quat = struct.pack('<4d', 0.0, 0.0, 0.0, 1.0)
    pos = struct.pack('<3d', tx, ty, tz)
    scale = struct.pack('<3d', 1.0, 1.0, 1.0)
    return quat + pos + scale


def _build_synthetic_vasb(location_tag: str = 'WestCity_Woodside', health: float = 87.5) -> bytes:
    # Build minimal inner GVAS stream
    gvas_hdr = (
        b'GVAS'
        + struct.pack('<iii', 2, 522, 1008)
        + b'\x05\x00\x01\x00\x00\x00\x00\x00\x00\x00'
        + _pack_fstr('++UE5+Release-5.1')
        + struct.pack('<ii', 3, 0)
        + _pack_fstr('/Script/SHProto.SHSaveGame')
    )

    # Health component GVAS properties (92B prefix + HealthValue FloatProperty + None\0 + 4B pad)
    health_prop = (
        _pack_fstr('HealthValue')
        + _pack_fstr('FloatProperty')
        + struct.pack('<iiB', 4, 0, 0)
        + struct.pack('<f', health)
        + _pack_fstr('None')
        + struct.pack('<i', 0)
    )
    comp_health_blob = _pack_transform(0, 0, 0) + struct.pack('<iif', 0, 1, 1.0) + health_prop

    player_raw = _pack_transform(-21000.0, 36000.0, 100.0) + struct.pack('<ii', 0, 0) + _pack_fstr('None') + struct.pack('<i', 0)
    player_actor = (
        b'\x00' * 16
        + struct.pack('<i', len(player_raw)) + player_raw
        + struct.pack('<i', 1)
        + _pack_fstr('Health') + struct.pack('<i', len(comp_health_blob)) + comp_health_blob
    )

    # UcaSave GHCA blob with 1 Glimpse GUID
    glimpse_guid = bytes.fromhex('32d003c840c4714f8e240dce2ad6fceb')
    ghca = (
        b'GHCA' + struct.pack('<i', 1)
        + b'LOC_' + struct.pack('<i', 1)
        + _pack_fstr('GlimpsesOfPast') + struct.pack('<i', 1) + glimpse_guid
    )

    empty_actor = b'\x00' * 16 + struct.pack('<i', 0) + struct.pack('<i', 0)
    body_gvas = (
        gvas_hdr
        + player_actor
        + struct.pack('<i', 1) + _pack_transform(-21000.0, 36000.0, 100.0) + (b'\x00' * 16)
        + struct.pack('<i', 0)  # n_actors
        + struct.pack('<i', 0)  # n_runtime
        + struct.pack('<i', 0)  # n_datalayers
        + struct.pack('<i', 0)  # n_target_levels
        + _pack_fstr('main')
        + empty_actor           # gamemode_data
        + struct.pack('<iii', 0, 0, 0)  # global props
        + struct.pack('<i', 1) + _pack_fstr('UcaSave') + struct.pack('<i', len(ghca)) + ghca
        + _pack_fstr('None') + struct.pack('<i', 0)
    )
    comp = zlib.compress(body_gvas)

    hdr_inner = (
        _pack_fstr('/Script/SHProto.SHSaveGame')
        + struct.pack('<i', 1)
        + _pack_fstr('SavePoint')
        + (b'\x11' * 16)
        + struct.pack('<q', 638640000000000000)
        + struct.pack('<ii', 0, 0)
        + struct.pack('<I', 0xDEAD0001)
        + struct.pack('<q', 3661 * 10_000_000)
        + _pack_fstr(location_tag)
    )
    hdr_size = len(hdr_inner) + 2  # +2 before difficulty bytes
    return (
        b'VASb'
        + struct.pack('<iI', hdr_size, 0xDEAD0001)
        + hdr_inner
        + bytes([1, 2]) + b'YDBx'
        + struct.pack('<II', len(comp), len(body_gvas))
        + comp
    )


def test_parse_synthetic_vasb(tmp_path):
    slot = tmp_path / 'SaveGameData_0.sav'
    slot.write_bytes(_build_synthetic_vasb())
    parsed = sh2_save.parse_save_slot(slot)
    assert parsed['ok'] is True
    assert parsed['health'] == 87.5
    assert parsed['play_time'] == '1:01:01'
    assert parsed['combat_difficulty_id'] == 1
    assert parsed['puzzle_difficulty_id'] == 2
    assert parsed['active_map_slug'] == 'woodside-1f'
    assert len(parsed['glimpses']) == 1
    assert parsed['glimpses'][0] == 'C803D032-4F71C440-CE0D248E-EBFCD62A'
