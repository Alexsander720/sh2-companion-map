"""End-to-end headless Chromium verification of the web UI (skipped cleanly if Playwright is absent)."""
from __future__ import annotations

import threading

import pytest

import server


def test_browser_ui_renders_and_switches_floors():
    pw_mod = pytest.importorskip('playwright.sync_api')
    sync_playwright = pw_mod.sync_playwright

    fake_save = lambda: {
        'ok': True,
        'location_tag': 'WestCity_Woodside',
        'slot_type': 'SavePoint',
        'save_datetime': '2026-11-18 03:00:00',
        'play_time': '2:30:00',
        'combat_difficulty_id': 1,
        'puzzle_difficulty_id': 1,
        'active_map_slug': 'woodside-2f',
        'player_pos': [-21500.0, 35500.0, 520.0],
        'player_yaw': 45.0,
        'health': 92.0,
        'items': {'HealthDrink': 5, 'Syringe': 2, 'HandgunAmmo': 30, 'WsaFW_MapWoodSide1F': 1, 'WsaFW_MapWoodSide2F': 1},
        'ammo_loaded': {'Pistol': 10},
        'memos': ['WsaFW_Gun_Note'],
        'glimpses': [],
        'stats': {'kills': 18},
        'map_objects': {
            'Woodside_2F': {
                'F2_SAFE': {'type': 'Puzzle', 'val': 1},
            }
        },
        'map_dynamic': {},
        'actor_states': {},
        'source': {'slot': 'SaveGameData_0.sav'},
    }
    fake_live = lambda **kw: {'available': False, 'process_running': False, 'reason_code': 'game_closed', 'build_fingerprint': {'matched': True}}

    app = server.App(save_reader=fake_save, telemetry_reader=fake_live)
    httpd = server.make_server('127.0.0.1', 0, app)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    url = f'http://127.0.0.1:{httpd.server_port}/'
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f'Chromium unavailable: {exc}')
            page = browser.new_page(viewport={'width': 1920, 'height': 1080}, locale='ru-RU')
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(url, wait_until='networkidle')
            page.wait_for_selector('.sh2-reg-tab.is-active')
            page.wait_for_selector('.sh2-pin-row')

            # Click a puzzle pin row and verify drawer opens with safe code
            rows = page.locator('.sh2-pin-row')
            assert rows.count() > 0
            rows.first.click()
            page.wait_for_selector('#sh2Drawer:not([hidden])')

            # Switch floor via floor bar
            page.locator('[data-floor="woodside-1f"]').click()
            page.wait_for_function("window.location.hash.includes('woodside-1f')")

            assert errors == []
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_tablet_suite_views_responsive_and_live_sse():
    pw_mod = pytest.importorskip('playwright.sync_api')
    sync_playwright = pw_mod.sync_playwright

    live_state = {
        'px': 500.0,
        'py': 850.0,
        'angle': 45.0,
        'health': 88.0,
    }

    fake_save = lambda: {
        'ok': True,
        'location_tag': 'WestCity_Woodside',
        'slot_type': 'SavePoint',
        'play_time': '2:30:00',
        'combat_difficulty_id': 1,
        'puzzle_difficulty_id': 1,
        'active_map_slug': 'woodside-2f',
        'player_pos': [-21500.0, 35500.0, 520.0],
        'player_yaw': 45.0,
        'health': 88.0,
        'items': {
            'HealthDrink': 5,
            'Syringe': 2,
            'Pistol': 1,
            'IronPipe': 1,
            'HandgunAmmo': 30,
            'Reflections_Photo_1': 1,
            'PhotoOfMary': 1,
            'LetterFromMary': 1,
            'WsaFW_MapWoodSide1F': 1,
            'WsaFW_MapWoodSide2F': 1,
            'Flashlight': 1,
            'Radio': 1,
        },
        'ammo_loaded': {'Pistol': 10},
        'last_used_weapon': 'IronPipe',
        'equipment': {'Flashlight': True, 'Radio': False},
        'memos': ['WsaFW_Gun_Note'],
        'glimpses': [],
        'weapon_kills': {'IronPipe': 12, 'Pistol': 6},
        'stats': {'kills': 18, 'shots_fired': 22, 'dodges': 4, 'distance_m': 1420},
        'map_objects': {},
        'map_dynamic': {},
        'actor_states': {},
        'source': {'slot': 'SaveGameData_0.sav'},
    }

    def fake_live(**kw):
        return {
            'available': True,
            'process_running': True,
            'active_map_slug': 'woodside-2f',
            'world_pos': [-21500.0, 35500.0, 520.0],
            'camera_yaw': live_state['angle'],
            'body_yaw': live_state['angle'],
            'fov': 75.0,
            'health': live_state['health'],
            'health_state': 0,
            'in_game_menu': False,
            'weapon_drawn': True,
            'last_used_weapon': 'IronPipe',
            'active_projection': {
                'px': live_state['px'],
                'py': live_state['py'],
                'angle_deg': live_state['angle'],
                'in_bounds': True,
            },
            'selected_projection': {
                'px': live_state['px'],
                'py': live_state['py'],
                'angle_deg': live_state['angle'],
                'in_bounds': True,
            },
            'build_fingerprint': {'matched': True, 'version': '1.0.0.5'},
        }

    app = server.App(save_reader=fake_save, telemetry_reader=fake_live)
    httpd = server.make_server('127.0.0.1', 0, app)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    url = f'http://127.0.0.1:{httpd.server_port}/'
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                pytest.skip(f'Chromium unavailable: {exc}')

            # 1. Tablet Landscape (Xiaomi Pad 6 Max 14 CSS px: 1280x800, touch enabled)
            ctx = browser.new_context(viewport={'width': 1280, 'height': 800}, has_touch=True, locale='ru-RU')
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(url, wait_until='networkidle')
            page.wait_for_selector('[data-stream="open"]', timeout=4000)

            def assert_no_overflow():
                ov = page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                assert ov, 'Horizontal overflow detected!'

            assert_no_overflow()

            # Live animated ECG pulse HUD must be visible right on the Map view even on 1280px landscape
            page.wait_for_selector('#sh2MapVitals:not([hidden]) .sh2-mv-ecg')
            assert '88%' in page.locator('#sh2MapVitalsHp').inner_text()
            assert 'в норме' in page.locator('#sh2MapVitalsState').inner_text().lower()

            # Cross-floor global search -> jump to bluecreek-2f
            page.fill('#sh2SearchInput', '373')
            page.wait_for_selector('#sh2GlobalResults .sh2-global-hit', timeout=3000)
            page.locator('#sh2GlobalResults .sh2-global-hit').first.click()
            page.wait_for_function("window.location.hash.includes('bluecreek-2f')")
            page.wait_for_selector('#sh2Drawer:not([hidden]) .sh2-code-row.is-active-diff')

            # Switch to Loadout tab -> click pocket item (PhotoOfMary / LetterFromMary) -> Large Inspect Lightbox opens
            page.locator('[data-maintab="loadout"]').click()
            page.wait_for_selector('.sh2-ecg-val')
            assert '88%' in page.locator('#sh2LoadoutHp').inner_text()
            assert page.locator('.sh2-wep-card.is-drawn').count() == 1
            page.locator('[data-pocket-id="LetterFromMary"]').click()
            page.wait_for_selector('#sh2Modal:not([hidden]) .sh2-inspect-modal')
            page.locator('#sh2ModalClose').click()
            page.wait_for_selector('#sh2Modal[hidden]', state='attached')
            assert_no_overflow()

            # Switch to Archive tab (Photos -> open modal -> Memos -> open large modal -> Chapters)
            page.locator('[data-maintab="archive"]').click()
            page.wait_for_selector('.sh2-polaroid-card')
            assert page.locator('.sh2-polaroid-card').count() == 26
            page.locator('.sh2-polaroid-card').first.click()
            page.wait_for_selector('#sh2Modal:not([hidden])')
            page.locator('#sh2ModalClose').click()
            page.wait_for_selector('#sh2Modal[hidden]', state='attached')
            page.locator('[data-asub="memos"]').click()
            page.wait_for_selector('.sh2-memo-reader-body')
            page.locator('[data-inspect-memo]').first.click()
            page.wait_for_selector('#sh2Modal:not([hidden]) .sh2-inspect-modal')
            page.locator('#sh2ModalClose').click()
            page.wait_for_selector('#sh2Modal[hidden]', state='attached')
            page.locator('[data-asub="chapters"]').click()
            assert page.locator('.sh2-chapter-card').count() == 8
            assert_no_overflow()

            # Switch to Safes & Codes tab
            page.locator('[data-maintab="codes"]').click()
            page.wait_for_selector('.sh2-code-card-item .is-active-diff')
            assert_no_overflow()

            # Switch back to Map (woodside-2f where live telemetry is) and verify zero-reload SSE tick movement
            page.locator('[data-maintab="map"]').click()
            page.locator('[data-reg="woodside-2f"]').click()
            page.wait_for_function("window.location.hash.includes('woodside-2f')")
            before_style = page.locator('.sh2-james-wrap').evaluate("el => el.style.left + ',' + el.style.top")
            live_state['px'] = 1200.0
            live_state['py'] = 420.0
            live_state['health'] = 54.0
            page.wait_for_function(
                "prev => { const el = document.querySelector('.sh2-james-wrap'); return el && (el.style.left + ',' + el.style.top) !== prev; }",
                arg=before_style,
                timeout=3000,
            )
            page.wait_for_function("document.querySelector('#sh2SideHp') && document.querySelector('#sh2SideHp').textContent.includes('54%')")
            page.wait_for_function("document.querySelector('#sh2MapVitalsHp') && document.querySelector('#sh2MapVitalsHp').textContent.includes('54%')")
            assert 'ранен' in page.locator('#sh2MapVitalsState').inner_text().lower()
            assert page.locator('#sh2MapVitals.is-caution').count() == 1

            # Ensure James marker keeps sh2-pin-marker positioning & compact 84px cone after SSE ticks
            jbox = page.evaluate("""() => {
                const w = document.querySelector('.sh2-james-wrap');
                const c = document.querySelector('.sh2-james-cone');
                return {
                    hasPinCls: w.classList.contains('sh2-pin-marker'),
                    pos: getComputedStyle(w).position,
                    csW: getComputedStyle(c).width,
                    csH: getComputedStyle(c).height,
                    coneW: c.getBoundingClientRect().width,
                    coneH: c.getBoundingClientRect().height,
                };
            }""")
            assert jbox['hasPinCls'] is True and jbox['pos'] == 'absolute'
            assert jbox['csW'] == '84px' and jbox['csH'] == '84px'
            assert jbox['coneW'] <= 124 and jbox['coneH'] <= 124

            assert errors == []
            ctx.close()

            # 2. Tablet Portrait (800x1280, touch) + Desktop (1920x1080) overflow checks
            for vw, vh, touch in ((800, 1280, True), (1920, 1080, False)):
                c2 = browser.new_context(viewport={'width': vw, 'height': vh}, has_touch=touch, locale='ru-RU')
                p2 = c2.new_page()
                e2 = []
                p2.on('pageerror', lambda err: e2.append(str(err)))
                p2.goto(url, wait_until='networkidle')
                for tab in ('map', 'loadout', 'archive', 'codes'):
                    p2.locator(f'[data-maintab="{tab}"]').click()
                    p2.wait_for_timeout(80)
                    assert p2.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {vw}x{vh} tab={tab}'
                assert e2 == []
                c2.close()

            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
