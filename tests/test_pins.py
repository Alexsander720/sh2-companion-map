"""Tests for pin catalog completeness, save correlation, and red-marker state machine."""
from __future__ import annotations

from collections import Counter

import sh2_pins


def test_world_pins_completeness():
    pins = sh2_pins.load_world_pins()
    counts = Counter(p['cat'] for p in pins)
    assert counts['strange_photo'] == 26
    assert counts['glimpse'] == 26
    assert counts['save_point'] == 46
    assert counts['memo'] == 72  # + 4 NG+ memos in ng_plus = 76
    assert counts['weapon'] == 5  # + Chainsaw in ng_plus = 6


def test_save_correlation_and_manual_marks():
    pins = sh2_pins.load_world_pins()
    photo_pin = next(p for p in pins if p['cat'] == 'strange_photo')
    glimpse_pin = next(p for p in pins if p['cat'] == 'glimpse')

    fake_save = {
        'ok': True,
        'active_map_slug': photo_pin['map'],
        'player_pos': photo_pin['xyz'],
        'player_yaw': 45.0,
        'items': {photo_pin['row']: 1},
        'memos': [],
        'glimpses': [glimpse_pin['guid']],
        'map_objects': {},
        'map_dynamic': {},
        'actor_states': {},
    }

    st_photo = sh2_pins.build_companion_state(photo_pin['map'], fake_save, 'ru')
    matched_p = next(x for x in st_photo['pins'] if x['id'] == photo_pin['id'])
    assert matched_p['status'] == 'collected'

    st_glimpse = sh2_pins.build_companion_state(glimpse_pin['map'], fake_save, 'en')
    matched_g = next(x for x in st_glimpse['pins'] if x['id'] == glimpse_pin['id'])
    assert matched_g['status'] == 'collected'

    # Manual mark without save
    any_pin = st_photo['pins'][0]
    st_manual = sh2_pins.build_companion_state(photo_pin['map'], {'ok': False}, 'ru', manual_ids={str(any_pin['id'])})
    m_pin = next(x for x in st_manual['pins'] if x['id'] == any_pin['id'])
    assert m_pin['status'] == 'collected'
    assert m_pin['manual'] is True


def test_red_marker_state_machine():
    sp, vis = sh2_pins._resolve_james_marker_sprite('Map_Marker_Locked_01_B_TB', 'Door', 3)
    assert vis is True and sp == 'Map_Marker_Opened_01_B_TB'
    sp2, vis2 = sh2_pins._resolve_james_marker_sprite('Map_Marker_Puzzle_01_A_TB', 'Puzzle', 22)
    assert vis2 is True and sp2 == 'Map_Marker_PuzzleCompleted_01_A_TB'


def test_search_world_pins_codes_and_languages():
    # Search by puzzle safe code (Moth Lock Normal = 373) across all maps excluding woodside-1f
    hits = sh2_pins.search_world_pins('373', None, 'ru', exclude_map='woodside-1f')
    assert any(h['cat'] == 'puzzle' and h.get('has_code') and h['map'] == 'bluecreek-2f' for h in hits)

    # Search English memo title (works with or without extracted localization cache)
    hits_en = sh2_pins.search_world_pins('Neely', None, 'en')
    assert any(h['cat'] == 'memo' and h['map'] == 'city-east' for h in hits_en)


def test_merge_live_into_save_and_build_dossier_state():
    fake_save = {
        'ok': True,
        'puzzle_difficulty_id': 1,
        'active_map_slug': 'woodside-1f',
        'player_pos': [-21000.0, 35000.0, 100.0],
        'player_yaw': 10.0,
        'health': 80.0,
        'items': {'HealthDrink': 2, 'Pistol': 1, 'HandgunAmmo': 12},
        'ammo_loaded': {'Pistol': 5},
        'last_used_weapon': 'Pistol',
        'equipment': {'Flashlight': True, 'Radio': True},
        'memos': [],
        'glimpses': [],
        'weapon_kills': {'Pistol': 4},
        'stats': {'kills': 4, 'shots_fired': 9},
        'map_objects': {'Woodside_1F': {'DOOR_A': {'type': 'Door', 'val': 1}}},
        'map_dynamic': {},
        'actor_states': {},
    }
    fake_live = {
        'available': True,
        'process_running': True,
        'active_map_slug': 'woodside-2f',
        'world_pos': [-21500.0, 35500.0, 520.0],
        'camera_yaw': 45.0,
        'health': 64.5,
        'health_state': 1,
        'weapon_drawn': True,
        'last_used_weapon': 'IronPipe',
        'items': {'HealthDrink': 3, 'Syringe': 1, 'Pistol': 1, 'IronPipe': 1, 'HandgunAmmo': 20, 'Reflections_Photo_1': 1, 'Flashlight': 1, 'Radio': 1},
        'ammo_loaded': {'Pistol': 10},
        'equipment': {'Flashlight': False, 'Radio': True},
        'memos': ['WsaFW_Gun_Note'],
        'weapon_kills': {'Pistol': 6, 'IronPipe': 3},
        'stats': {'kills': 9, 'shots_fired': 15},
        'map_objects': {'Woodside_2F': {'F2_SAFE': {'type': 'Puzzle', 'val': 2}}},
    }
    merged = sh2_pins.merge_live_into_save(fake_save, fake_live)
    # Input dict must not be mutated
    assert fake_save['health'] == 80.0
    assert merged['health'] == 64.5
    assert merged['active_map_slug'] == 'woodside-2f'
    assert merged['items']['Syringe'] == 1
    assert merged['map_objects']['Woodside_1F']['DOOR_A']['val'] == 1
    assert merged['map_objects']['Woodside_2F']['F2_SAFE']['val'] == 2

    dossier = sh2_pins.build_dossier_state(fake_save, fake_live, 'ru')
    assert dossier['is_live'] is True
    assert dossier['drinks'] == 3 and dossier['syringes'] == 1
    assert dossier['equipment']['flashlight_on'] is False
    assert dossier['equipment']['radio_on'] is True
    assert dossier['photos']['total'] == 26 and len(dossier['photos']['list']) == 26
    assert dossier['photos']['got'] == 1
    assert dossier['memos']['total'] == 72 and dossier['memos']['got'] == 1
    assert len(dossier['puzzles']) == 52
    assert len(dossier['chapters']) == 8
    pipe = next(w for w in dossier['weapons'] if w['id'] == 'IronPipe')
    assert pipe['equipped'] is True and pipe['drawn'] is True and pipe['kills'] == 3
    pistol = next(w for w in dossier['weapons'] if w['id'] == 'Pistol')
    assert pistol['loaded'] == 10 and pistol['reserve'] == 20 and pistol['total_ammo'] == 30
