"""HTTP API and privacy/sanitization tests for server.py."""
from __future__ import annotations

import http.client
import json
import threading
import time
import urllib.error
import urllib.request

import paths
import server


def test_server_endpoints_and_unsupported_build_safety():
    fake_save = lambda: {
        'ok': True,
        'location_tag': 'M_BlueCreek_ClockRoom',
        'slot_type': 'SavePoint',
        'save_datetime': '2026-11-18 03:00:00',
        'play_time': '4:12:00',
        'combat_difficulty_id': 1,
        'puzzle_difficulty_id': 1,
        'active_map_slug': 'bluecreek-2f',
        'player_pos': [-27351.0, 38435.0, 110.0],
        'player_yaw': 90.0,
        'health': 76.0,
        'items': {'HealthDrink': 4, 'Syringe': 1, 'HandgunAmmo': 24, 'Reflections_Photo_1': 1},
        'ammo_loaded': {'Pistol': 10},
        'memos': ['WsaFW_Gun_Note'],
        'glimpses': [],
        'stats': {'kills': 42},
        'map_objects': {},
        'map_dynamic': {},
        'actor_states': {},
        'source': {'slot': '/mock/SecretFolder/SaveGameData_0.sav'},
    }
    # Simulate an unverified game patch: live marker must be suppressed
    fake_telemetry = lambda **kw: {
        'available': True,
        'process_running': True,
        'active_map_slug': 'woodside-1f',
        'world_pos': [-20000.0, 35000.0, 100.0],
        'build_fingerprint': {'matched': False},
    }

    app = server.App(save_reader=fake_save, telemetry_reader=fake_telemetry)
    httpd = server.make_server('127.0.0.1', 0, app)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f'http://127.0.0.1:{httpd.server_port}'
    try:
        with urllib.request.urlopen(base + '/api/map?lang=ru') as r:
            body = json.loads(r.read().decode('utf-8'))
        assert body['ok'] is True
        # Secret path must be stripped to bare filename
        assert body['save']['source']['slot'] == 'SaveGameData_0.sav'
        assert 'SecretFolder' not in json.dumps(body)
        # Unmatched fingerprint must force available=False
        assert body['live_telemetry']['available'] is False
        assert body['live_telemetry']['reason_code'] == 'unsupported_build'
        assert body['world']['selected_map_slug'] == 'bluecreek-2f'
        assert body['save']['supplies']['handgun_ammo'] == 34

        # Invalid map slug returns 400
        try:
            urllib.request.urlopen(base + '/api/map?map=../../etc/passwd')
            assert False, 'Expected 400'
        except urllib.error.HTTPError as e:
            assert e.code == 400

        # Paper endpoint returns PNG
        with urllib.request.urlopen(base + '/sh2-paper/woodside-1f.png') as rp:
            png = rp.read(16)
        assert png.startswith(b'\x89PNG\r\n\x1a\n')
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_dossier_search_pwa_items_and_sse_stream(tmp_path, monkeypatch):
    items_dir = tmp_path / 'items'
    items_dir.mkdir()
    sample_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 12
    (items_dir / 'HealthDrink.png').write_bytes(sample_png)
    monkeypatch.setattr(paths, 'ITEMS_DIR', items_dir)

    fake_save = lambda: {
        'ok': True,
        'location_tag': 'M_BlueCreek_ClockRoom',
        'slot_type': 'SavePoint',
        'play_time': '4:12:00',
        'combat_difficulty_id': 1,
        'puzzle_difficulty_id': 1,
        'active_map_slug': 'bluecreek-2f',
        'player_pos': [-27351.0, 38435.0, 110.0],
        'player_yaw': 90.0,
        'health': 75.0,
        'items': {'HealthDrink': 4, 'Pistol': 1, 'HandgunAmmo': 18, 'Reflections_Photo_1': 1},
        'ammo_loaded': {'Pistol': 10},
        'last_used_weapon': 'Pistol',
        'equipment': {'Flashlight': True, 'Radio': True},
        'memos': ['WsaFW_Gun_Note'],
        'glimpses': [],
        'weapon_kills': {'Pistol': 12},
        'stats': {'kills': 12, 'shots_fired': 30},
        'map_objects': {},
        'map_dynamic': {},
        'actor_states': {},
        'source': {'slot': 'SaveGameData_0.sav'},
    }
    fake_live = lambda **kw: {
        'available': True,
        'process_running': True,
        'active_map_slug': 'bluecreek-2f',
        'world_pos': [-27351.0, 38435.0, 110.0],
        'camera_yaw': 90.0,
        'body_yaw': 90.0,
        'fov': 75.0,
        'health': 88.0,
        'health_state': 0,
        'in_game_menu': False,
        'weapon_drawn': True,
        'last_used_weapon': 'Pistol',
        'active_projection': {'px': 930.3, 'py': 972.0, 'angle_deg': 180.0, 'in_bounds': True},
        'build_fingerprint': {'matched': True, 'version': '1.0.0.5'},
    }

    app = server.App(save_reader=fake_save, telemetry_reader=fake_live)
    httpd = server.make_server('127.0.0.1', 0, app)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f'http://127.0.0.1:{httpd.server_port}'
    try:
        # 1. /api/map includes full live-merged dossier
        with urllib.request.urlopen(base + '/api/map?lang=ru') as r:
            body = json.loads(r.read().decode('utf-8'))
        dos = body['dossier']
        assert dos['is_live'] is True
        assert dos['health'] == 88.0
        assert len(dos['weapons']) == 1 and dos['weapons'][0]['drawn'] is True
        assert dos['photos']['total'] == 26 and len(dos['photos']['list']) == 26
        assert len(dos['memos']['list']) == 72
        assert len(dos['puzzles']) == 52
        assert len(dos['chapters']) == 8
        assert dos['stats']['shots_fired'] == 30

        # 2. /api/search across floors
        with urllib.request.urlopen(base + '/api/search?q=373&lang=ru&exclude=woodside-1f') as r:
            sr = json.loads(r.read().decode('utf-8'))
        assert sr['ok'] is True and any(h['cat'] == 'puzzle' and h['map'] == 'bluecreek-2f' for h in sr['results'])

        # 3. /api/info, PWA manifest, icons, /sh2-items/
        with urllib.request.urlopen(base + '/api/info') as r:
            info = json.loads(r.read().decode('utf-8'))
        assert info['ok'] is True and info['sse'] is True and info['port'] == httpd.server_port

        with urllib.request.urlopen(base + '/manifest.webmanifest') as r:
            man = json.loads(r.read().decode('utf-8'))
        assert man['display'] == 'fullscreen' and len(man['icons']) >= 2

        with urllib.request.urlopen(base + '/icon-192.png') as r:
            assert r.read(8) == b'\x89PNG\r\n\x1a\n'
        with urllib.request.urlopen(base + '/icon.svg') as r:
            assert b'<svg' in r.read(256)
        with urllib.request.urlopen(base + '/sh2-items/HealthDrink.png') as r:
            assert r.read() == sample_png
        try:
            urllib.request.urlopen(base + '/sh2-items/../secret.png')
            assert False, 'Expected 404'
        except urllib.error.HTTPError as e:
            assert e.code == 404

        # 4. /api/stream receives event: tick in <1s and closes cleanly on server shutdown
        conn = http.client.HTTPConnection('127.0.0.1', httpd.server_port, timeout=2.0)
        conn.request('GET', '/api/stream')
        resp = conn.getresponse()
        assert resp.status == 200
        assert 'text/event-stream' in (resp.getheader('Content-Type') or '')
        lines = []
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            ln = resp.fp.readline().decode('utf-8', errors='replace')
            lines.append(ln)
            if ln.startswith('data:') and any(x.strip() == 'event: tick' for x in lines):
                break
        assert any(x.strip() == 'event: tick' for x in lines), f'SSE lines: {lines}'
        data_line = next(x for x in lines if x.startswith('data:'))
        tick_obj = json.loads(data_line.removeprefix('data:').strip())
        assert tick_obj['available'] is True and tick_obj['health'] == 88.0

        # Shutdown while SSE connection is still open must complete rapidly (<1.5s)
        t0 = time.monotonic()
        httpd.shutdown()
        httpd.server_close()
        elapsed = time.monotonic() - t0
        conn.close()
        assert elapsed < 1.5, f'SSE shutdown blocked for {elapsed:.2f}s'
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        try:
            httpd.server_close()
        except Exception:
            pass
