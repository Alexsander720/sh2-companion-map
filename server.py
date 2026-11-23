"""Local stdlib HTTP server for SILENT HILL 2 Companion Map."""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import inspect
import io
import json
from pathlib import Path
import queue
import re
import socket
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

from PIL import Image, ImageDraw

import paths
from i18n import language, t
from saves import SaveReader
import sh2_memory
import sh2_pins

VERSION = '0.1.0'
VALID_SLUGS = frozenset(m['slug'] for m in sh2_pins.load_maps_meta())
MARKER_NAME_RE = re.compile(r'^[A-Za-z0-9_]{1,80}$')
_FALLBACK_PNG: bytes | None = None


def _fallback_paper_png() -> bytes:
    global _FALLBACK_PNG
    if _FALLBACK_PNG is None:
        im = Image.new('RGBA', (2048, 2048), (222, 214, 198, 255))
        dr = ImageDraw.Draw(im)
        for g in range(0, 2049, 128):
            col = (196, 188, 172, 255) if g % 512 else (174, 165, 148, 255)
            dr.line([(g, 0), (g, 2048)], fill=col, width=2 if g % 512 == 0 else 1)
            dr.line([(0, g), (2048, g)], fill=col, width=2 if g % 512 == 0 else 1)
        dr.rectangle([24, 24, 2024, 2024], outline=(140, 128, 110, 255), width=4)
        buf = io.BytesIO()
        im.save(buf, 'PNG', compress_level=3)
        _FALLBACK_PNG = buf.getvalue()
    return _FALLBACK_PNG


class LiveBroadcaster:
    """Thread-safe SSE broadcaster pushing 15 Hz live ticks and instant state invalidation."""

    def __init__(self, app: App):
        self.app = app
        self._lock = threading.Lock()
        self._subs: set[queue.Queue] = set()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_tick: dict | None = None
        self._last_tick_sig: Any = None
        self._last_state_sig: Any = None

    def _ensure_started(self) -> None:
        if self._stop.is_set():
            return
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run, name='sh2-sse-broadcaster', daemon=True)
            self._thread.start()

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=32)
        with self._lock:
            self._subs.add(q)
            self._ensure_started()
            snap = self._last_tick
        if snap is not None:
            try:
                q.put_nowait(('tick', json.dumps(snap, ensure_ascii=False)))
            except queue.Full:
                pass
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            self._subs.discard(q)

    def _broadcast(self, event_name: str, payload: dict) -> None:
        data_str = json.dumps(payload, ensure_ascii=False)
        with self._lock:
            subs = list(self._subs)
        for q in subs:
            try:
                q.put_nowait((event_name, data_str))
            except queue.Full:
                try:
                    q.get_nowait()
                except queue.Empty:
                    pass
                try:
                    q.put_nowait((event_name, data_str))
                except queue.Full:
                    pass

    def _tick_from_telemetry(self, lt: dict) -> dict:
        return {
            'available': bool(lt.get('available')),
            'process_running': bool(lt.get('process_running')),
            'reason_code': lt.get('reason_code'),
            'active_map_slug': lt.get('active_map_slug'),
            'world_pos': lt.get('world_pos'),
            'camera_yaw': lt.get('camera_yaw'),
            'body_yaw': lt.get('body_yaw'),
            'fov': lt.get('fov'),
            'health': lt.get('health'),
            'health_state': lt.get('health_state'),
            'in_game_menu': bool(lt.get('in_game_menu')),
            'weapon_drawn': bool(lt.get('weapon_drawn')) if 'weapon_drawn' in lt else None,
            'last_used_weapon': lt.get('last_used_weapon'),
            'active_projection': lt.get('active_projection'),
            'ts': round(time.time(), 3),
        }

    def _run(self) -> None:
        last_ext_check = 0.0
        while not self._stop.is_set():
            with self._lock:
                has_subs = bool(self._subs)
            if not has_subs:
                self._stop.wait(0.25)
                continue

            now = time.monotonic()
            live_now = bool(self._last_tick and self._last_tick.get('available'))
            ext_period = 0.4 if live_now else 1.0
            check_ext = (now - last_ext_check) >= ext_period

            save = None
            if check_ext:
                last_ext_check = now
                try:
                    save = self.app.save_reader() or {'ok': False}
                except Exception:
                    save = {'ok': False}

            lt = self.app._read_telemetry(
                selected_slug=None,
                active_save_slug=save.get('active_map_slug') if save else None,
                include_extended=check_ext,
                lang='en',
            )
            tick = self._tick_from_telemetry(lt)
            tick_sig = (
                tick['available'],
                tick['reason_code'],
                tick['active_map_slug'],
                tuple(tick['world_pos'] or ()),
                tick['camera_yaw'],
                tick['fov'],
                tick['health'],
                tick['health_state'],
                tick['in_game_menu'],
            )
            if tick_sig != self._last_tick_sig:
                self._last_tick_sig = tick_sig
                self._last_tick = tick
                self._broadcast('tick', tick)

            if check_ext and save is not None:
                ext_sig = (
                    bool(save.get('ok')),
                    save.get('ticks'),
                    (save.get('source') or {}).get('slot'),
                    save.get('active_map_slug'),
                    tuple(sorted((lt.get('items') or {}).items())) if lt.get('available') else (),
                    tuple(sorted((lt.get('ammo_loaded') or {}).items())) if lt.get('available') else (),
                    tuple(sorted((lt.get('equipment') or {}).items())) if lt.get('available') else (),
                    lt.get('last_used_weapon') if lt.get('available') else None,
                    len(lt.get('memos') or ()) if lt.get('available') else 0,
                    sum(len(v) for v in (lt.get('map_objects') or {}).values()) if lt.get('available') else 0,
                    lt.get('active_map_slug') if lt.get('available') else None,
                )
                if self._last_state_sig is not None and ext_sig != self._last_state_sig:
                    self._last_state_sig = ext_sig
                    self._broadcast('state', {
                        'reason': 'live_state' if lt.get('available') else 'save',
                        'active_map_slug': lt.get('active_map_slug') or save.get('active_map_slug'),
                    })
                elif self._last_state_sig is None:
                    self._last_state_sig = ext_sig

            wait_s = 0.065 if tick['available'] else 0.75
            self._stop.wait(wait_s)

    def close(self) -> None:
        self._stop.set()
        with self._lock:
            subs = list(self._subs)
            self._subs.clear()
        for q in subs:
            try:
                q.put_nowait(None)
            except queue.Full:
                try:
                    q.get_nowait()
                    q.put_nowait(None)
                except Exception:
                    pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)


class App:
    def __init__(self, save_reader=None, telemetry_reader=None):
        self.save_reader = save_reader or SaveReader().read
        if telemetry_reader is None:
            self._live_session = sh2_memory.LiveSession()
            self.telemetry_reader = self._live_session.read
        else:
            self._live_session = None
            self.telemetry_reader = telemetry_reader
        self._tel_has_ext = self._detect_ext_kw(self.telemetry_reader)
        self.lock = threading.Lock()
        self.broadcaster = LiveBroadcaster(self)

    @staticmethod
    def _detect_ext_kw(fn) -> bool:
        try:
            sig = inspect.signature(fn)
            return 'include_extended' in sig.parameters
        except (TypeError, ValueError):
            return False

    def close(self) -> None:
        self.broadcaster.close()
        if self._live_session is not None:
            self._live_session.close()

    def _sanitize_telemetry(self, lt: dict | None, lg: str) -> dict:
        lt = lt or {'available': False}
        if (lt.get('build_fingerprint') or {}).get('matched') is False:
            lt = {
                'available': False,
                'process_running': bool(lt.get('process_running')),
                'reason_code': 'unsupported_build',
                'build_fingerprint': {'matched': False},
            }
        if not lt.get('available'):
            code = lt.get('reason_code') or ('memory_unavailable' if lt.get('process_running') else 'game_closed')
            if code not in ('unsupported_build', 'build_unverified', 'memory_unavailable', 'game_closed'):
                code = 'memory_unavailable' if lt.get('process_running') else 'game_closed'
            lt = dict(lt, reason_code=code, reason=t(code, lg))
        return lt

    def _read_telemetry(
        self,
        selected_slug: str | None = None,
        active_save_slug: str | None = None,
        include_extended: bool = True,
        lang: str = 'en',
    ) -> dict:
        try:
            if self._tel_has_ext:
                raw = self.telemetry_reader(
                    selected_slug=selected_slug,
                    active_save_slug=active_save_slug,
                    include_extended=include_extended,
                )
            else:
                raw = self.telemetry_reader(
                    selected_slug=selected_slug,
                    active_save_slug=active_save_slug,
                )
        except (OSError, ValueError, RuntimeError, AttributeError):
            raw = {'available': False, 'reason_code': 'memory_unavailable'}
        return self._sanitize_telemetry(raw, lang)

    def _merged_context(self, map_slug: str | None, lg: str) -> tuple[dict, dict, dict]:
        save = self.save_reader() or {'ok': False}
        save_active_slug = save.get('active_map_slug') if save.get('ok') else None
        lt = self._read_telemetry(selected_slug=map_slug, active_save_slug=save_active_slug, include_extended=True, lang=lg)
        merged = sh2_pins.merge_live_into_save(save, lt)
        return save, lt, merged

    def search(
        self,
        query: str,
        lang: str = 'en',
        manual_ids: set[str] | None = None,
        exclude_map: str | None = None,
        limit: int = 48,
    ) -> list[dict]:
        lg = language(lang)
        with self.lock:
            _save, _lt, merged = self._merged_context(None, lg)
            return sh2_pins.search_world_pins(query, merged, lg, manual_ids, exclude_map=exclude_map, limit=limit)

    def payload(self, map_slug: str | None = None, lang: str = 'en', manual_ids: set[str] | None = None) -> dict:
        lg = language(lang)
        with self.lock:
            save, lt, merged = self._merged_context(map_slug, lg)
            save_active_slug = merged.get('active_map_slug') if merged.get('ok') else None

            effective_slug = map_slug
            if not effective_slug:
                effective_slug = (lt.get('active_map_slug') if lt.get('available') else None) or save_active_slug or 'city-east'

            # If live telemetry was read before knowing effective_slug, ensure selected_projection matches effective_slug
            if lt.get('available') and lt.get('world_pos') and not lt.get('selected_projection'):
                maps_by_slug = sh2_memory.load_maps_by_slug()
                live_meta = maps_by_slug.get(lt.get('active_map_slug') or '')
                sel_meta = maps_by_slug.get(effective_slug)
                if live_meta and sel_meta and (
                    effective_slug == lt.get('active_map_slug')
                    or sel_meta['region'] == live_meta['region']
                    or sel_meta.get('twin') == lt.get('active_map_slug')
                ):
                    p_sel = sh2_memory.project_world_to_sheet(
                        lt['world_pos'][0], lt['world_pos'][1], float(lt.get('camera_yaw') or 0.0), sel_meta
                    )
                    if p_sel['in_bounds']:
                        lt = dict(lt, selected_projection=p_sel)

            state = sh2_pins.build_companion_state(effective_slug, merged, lg, manual_ids)
            dossier = sh2_pins.build_dossier_state(merged, lt, lg, manual_ids)
            if lt.get('available') and lt.get('active_map_slug'):
                live_active = lt['active_map_slug']
                state['live_map_slug'] = live_active
                state['live_map_title'] = t(live_active, lg)
                for reg in state['regions']:
                    reg['is_live'] = any(m['slug'] == live_active for m in reg['maps'])
                for m in state['maps']:
                    m['is_live'] = m['slug'] == live_active

            items = merged.get('items') or {}
            ammo_loaded = merged.get('ammo_loaded') or {}
            public_save = {
                'ok': bool(merged.get('ok')),
                'place': sh2_pins.resolve_place_label(merged.get('location_tag'), lg) if merged.get('ok') else None,
                'slot_type': merged.get('slot_type'),
                'save_datetime': merged.get('save_datetime'),
                'play_time': merged.get('play_time'),
                'combat_difficulty': t(f"diff_{merged['combat_difficulty_id']}", lg) if merged.get('combat_difficulty_id') in (0, 1, 2) else None,
                'puzzle_difficulty': t(f"diff_{merged['puzzle_difficulty_id']}", lg) if merged.get('puzzle_difficulty_id') in (0, 1, 2) else None,
                'puzzle_difficulty_id': merged.get('puzzle_difficulty_id'),
                'health': lt.get('health') if (lt.get('available') and lt.get('health') is not None) else merged.get('health'),
                'supplies': {
                    'drinks': items.get('HealthDrink', 0),
                    'syringes': items.get('Syringe', 0),
                    'handgun_ammo': items.get('HandgunAmmo', 0) + ammo_loaded.get('Pistol', 0),
                    'shotgun_ammo': items.get('ShotgunAmmo', 0) + ammo_loaded.get('Shotgun', 0),
                    'rifle_ammo': items.get('RifleAmmo', 0) + ammo_loaded.get('Rifle', 0),
                    'memos_count': len(merged.get('memos') or ()),
                    'photos_count': sum(1 for k, q in items.items() if k.startswith('Reflections_Photo_') and q > 0),
                    'glimpses_count': len(merged.get('glimpses') or ()),
                } if merged.get('ok') else None,
                'icons': {row: sh2_pins.item_icon(row) for row in (
                    'HealthDrink', 'Syringe', 'HandgunAmmo', 'ShotgunAmmo', 'RifleAmmo') if sh2_pins.item_icon(row)},
                'stats': merged.get('stats') if merged.get('ok') else None,
                'source': {'slot': Path(str((merged.get('source') or {}).get('slot') or '')).name},
            }

            notices = []
            if not merged.get('ok'):
                notices.append(t('save_missing', lg))
            if not all(m['texture_ready'] for m in state['maps']):
                notices.append(t('assets_missing', lg))

            return {
                'ok': True,
                'version': VERSION,
                'lang': lg,
                'world': state,
                'dossier': dossier,
                'save': public_save,
                'live_telemetry': lt,
                'update_policy': t('save_updates', lg),
                'notices': notices,
            }


def lan_urls(port: int) -> list[str]:
    """Private IPv4 addresses a tablet on the same Wi-Fi can reach (primary route first)."""
    import ipaddress
    found: list[str] = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(('192.0.2.1', 9))  # route lookup only, nothing is sent
            found.append(s.getsockname()[0])
        except OSError:
            pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.append(info[4][0])
    except OSError:
        pass
    out = []
    for ip in dict.fromkeys(found):
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            continue
        if addr.is_private and not addr.is_loopback and not addr.is_link_local:
            out.append(f'http://{ip}:{port}/')
    return out


_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
    '<rect width="512" height="512" rx="96" fill="#0b0e0d"/>'
    '<rect x="40" y="40" width="432" height="432" rx="64" fill="none" stroke="#3a3f3b" stroke-width="10"/>'
    '<rect x="176" y="176" width="160" height="160" fill="#cf2a22"/>'
    '<rect x="176" y="176" width="160" height="160" fill="none" stroke="#f04238" stroke-width="6" opacity=".7"/>'
    '</svg>'
).encode('utf-8')
_ICON_PNG: dict[int, bytes] = {}


def _icon_png(size: int) -> bytes:
    if size not in _ICON_PNG:
        im = Image.new('RGBA', (size, size), (11, 14, 13, 255))
        dr = ImageDraw.Draw(im)
        k = size / 512
        dr.rounded_rectangle([40 * k, 40 * k, 472 * k, 472 * k], radius=64 * k, outline=(58, 63, 59, 255), width=max(2, int(10 * k)))
        dr.rectangle([176 * k, 176 * k, 336 * k, 336 * k], fill=(207, 42, 34, 255))
        buf = io.BytesIO()
        im.save(buf, 'PNG')
        _ICON_PNG[size] = buf.getvalue()
    return _ICON_PNG[size]


def _manifest(lang: str) -> dict:
    ru = lang == 'ru'
    return {
        'name': 'SILENT HILL 2 — ' + ('Живая карта' if ru else 'Companion Map'),
        'short_name': 'SH2 ' + ('Карта' if ru else 'Map'),
        'start_url': '/',
        'scope': '/',
        'display': 'fullscreen',
        'orientation': 'any',
        'background_color': '#0b0e0d',
        'theme_color': '#0b0e0d',
        'icons': [
            {'src': '/icon.svg', 'sizes': 'any', 'type': 'image/svg+xml'},
            {'src': '/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
        ],
    }


def make_server(host: str = '127.0.0.1', port: int = 8791, app: App | None = None) -> ThreadingHTTPServer:
    app = app or App()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def reply(self, status: int, data, content_type: str = 'application/json; charset=utf-8', cache: bool = False):
            if not isinstance(data, bytes):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'public, max-age=86400' if cache else 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def _parse_marked(self, query: dict, lang: str) -> set[str] | None:
            marked = query.get('marked', [''])[0]
            ids = marked.split(',') if marked else []
            if len(marked) > 25000 or any(not (p.isascii() and p.isdigit() and len(p) <= 10) for p in ids):
                self.reply(400, {'ok': False, 'error': t('bad_request', lang)})
                return None
            return set(ids)

        def _serve_sse(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store')
            self.send_header('Connection', 'keep-alive')
            self.send_header('X-Accel-Buffering', 'no')
            self.end_headers()
            self.close_connection = True
            q = app.broadcaster.subscribe()
            try:
                self.wfile.write(b': connected\n\n')
                self.wfile.flush()
                while not app.broadcaster._stop.is_set():
                    try:
                        msg = q.get(timeout=15.0)
                    except queue.Empty:
                        self.wfile.write(b': keepalive\n\n')
                        self.wfile.flush()
                        continue
                    if msg is None:
                        break
                    ev_name, data_str = msg
                    frame = f'event: {ev_name}\ndata: {data_str}\n\n'.encode('utf-8')
                    self.wfile.write(frame)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                pass
            finally:
                app.broadcaster.unsubscribe(q)

        def do_GET(self):
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            lang = language(query.get('lang', [self.headers.get('Accept-Language', 'en')])[0])
            try:
                if url.path in ('/', '/sh2-map'):
                    self.reply(200, (paths.ROOT / 'web' / 'index.html').read_bytes(), 'text/html; charset=utf-8')
                elif url.path in ('/api/map', '/api/companion'):
                    slug = query.get('map', [None])[0]
                    if slug and slug not in VALID_SLUGS:
                        self.reply(400, {'ok': False, 'error': t('bad_request', lang)})
                        return
                    ids = self._parse_marked(query, lang)
                    if ids is None:
                        return
                    self.reply(200, app.payload(slug, lang, ids))
                elif url.path == '/api/search':
                    ids = self._parse_marked(query, lang)
                    if ids is None:
                        return
                    qtext = query.get('q', [''])[0]
                    exclude = query.get('exclude', [None])[0]
                    if exclude and exclude not in VALID_SLUGS:
                        exclude = None
                    try:
                        limit = max(1, min(int(query.get('limit', ['48'])[0]), 100))
                    except ValueError:
                        limit = 48
                    hits = app.search(qtext, lang=lang, manual_ids=ids, exclude_map=exclude, limit=limit)
                    self.reply(200, {'ok': True, 'query': qtext, 'results': hits})
                elif url.path == '/api/stream':
                    self._serve_sse()
                elif url.path.startswith('/sh2-paper/') and url.path.endswith('.png'):
                    slug = url.path.removeprefix('/sh2-paper/').removesuffix('.png')
                    if slug not in VALID_SLUGS:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    target = paths.MAPS_DIR / f'{slug}.png'
                    if target.is_file():
                        self.reply(200, target.read_bytes(), 'image/png', cache=True)
                    else:
                        self.reply(200, _fallback_paper_png(), 'image/png', cache=False)
                elif url.path.startswith('/sh2-markers/') and url.path.endswith('.png'):
                    mname = url.path.removeprefix('/sh2-markers/').removesuffix('.png')
                    if not MARKER_NAME_RE.match(mname):
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    target = paths.MARKERS_DIR / f'{mname}.png'
                    if target.is_file():
                        self.reply(200, target.read_bytes(), 'image/png', cache=True)
                    else:
                        self.reply(204, b'', 'image/png', cache=False)
                elif url.path.startswith('/sh2-items/') and url.path.endswith('.png'):
                    iname = url.path.removeprefix('/sh2-items/').removesuffix('.png')
                    target = paths.ITEMS_DIR / f'{iname}.png'
                    if MARKER_NAME_RE.match(iname) and target.is_file():
                        self.reply(200, target.read_bytes(), 'image/png', cache=True)
                    else:
                        self.reply(404, {'error': t('not_found', lang)})
                elif url.path == '/api/info':
                    bound = self.server.server_address[0]
                    port_now = self.server.server_address[1]
                    self.reply(200, {
                        'ok': True,
                        'version': VERSION,
                        'port': port_now,
                        'usb_url': f'http://127.0.0.1:{port_now}/',
                        'sse': True,
                        'lan': bound in ('0.0.0.0', ''),
                        'lan_urls': lan_urls(port_now) if bound in ('0.0.0.0', '') else [],
                    })
                elif url.path == '/manifest.webmanifest':
                    self.reply(200, json.dumps(_manifest(lang), ensure_ascii=False).encode('utf-8'),
                               'application/manifest+json; charset=utf-8')
                elif url.path == '/icon.svg':
                    self.reply(200, _ICON_SVG, 'image/svg+xml', cache=True)
                elif url.path in ('/icon-192.png', '/icon-512.png', '/apple-touch-icon.png', '/favicon.ico'):
                    size = {'/icon-192.png': 192, '/icon-512.png': 512, '/apple-touch-icon.png': 180}.get(url.path, 64)
                    self.reply(200, _icon_png(size), 'image/png', cache=True)
                elif url.path.startswith('/web/'):
                    name = url.path.removeprefix('/web/')
                    allowed = {
                        'map_engine.js': 'text/javascript',
                        'map_engine.css': 'text/css',
                        'i18n.js': 'text/javascript',
                        'companion_sh2_map.js': 'text/javascript',
                        'companion_sh2_map.css': 'text/css',
                    }
                    if name not in allowed:
                        self.reply(404, {'error': t('not_found', lang)})
                        return
                    self.reply(200, (paths.ROOT / 'web' / name).read_bytes(), allowed[name] + '; charset=utf-8')
                else:
                    self.reply(404, {'error': t('not_found', lang)})
            except (OSError, ValueError, KeyError, RuntimeError):
                self.reply(500, {'ok': False, 'error': t('internal_error', lang)})

    class _ExclusiveHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = False
        daemon_threads = True
        block_on_close = False

        def server_bind(self):
            if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

        def server_close(self):
            try:
                app.close()
            finally:
                super().server_close()

    return _ExclusiveHTTPServer((host, port), Handler)


DEFAULT_PORT = 8791


def _is_sh2_companion_running(port: int) -> bool:
    import urllib.request
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/web/companion_sh2_map.css', timeout=0.25) as r:
            return r.status == 200 and b'sh2' in r.read(512).lower()
    except OSError:
        return False


def _connect_tablet_safe(port: int, open_browser: bool, lang: str) -> None:
    try:
        from tools.tablet_usb import connect_tablet
        res = connect_tablet(port=port, open_browser=open_browser, lang=lang)
        if res.get('ok'):
            print(f"USB Tablet ({res.get('serial')}): {res.get('url')}")
        else:
            print(f"USB Tablet skipped: {res.get('error', 'not connected')}")
    except Exception as exc:
        print(f"USB Tablet error: {exc}")


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    explicit_port = any(a == '--port' or a.startswith('--port=') for a in raw_argv)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=DEFAULT_PORT)
    p.add_argument('--lan', action='store_true', help='Listen on all local network interfaces')
    p.add_argument('--tablet', action='store_true', help='Forward port over USB ADB and open on attached tablet')
    p.add_argument('--game-dir', type=Path)
    p.add_argument('--save-dir', type=Path)
    p.add_argument('--offline', action='store_true', help='Local mode (no external network requests are ever made)')
    p.add_argument('--no-browser', action='store_true')
    p.add_argument('--lang', choices=['ru', 'en'], default='ru', help='Terminal message language')
    args = p.parse_args(raw_argv)

    if _is_sh2_companion_running(args.port):
        url = f'http://127.0.0.1:{args.port}/'
        print(t('ready', args.lang) + ': ' + url)
        if args.tablet:
            _connect_tablet_safe(args.port, not args.no_browser, args.lang)
        elif not args.no_browser:
            webbrowser.open(url)
        return

    if args.game_dir:
        paths.GAME_DIR = paths.find_game_dir(args.game_dir)

    if paths.find_game_dir():
        from tools.extract_sh2_assets import is_extracted, prepare
        if not is_extracted():
            print(t('extracting', args.lang))
        try:
            prepare(paths.GAME_DIR, notify=print)
        except Exception:
            print(t('assets_missing', args.lang))

    app = App(save_reader=SaveReader(args.save_dir).read)
    bind_host = '0.0.0.0' if args.lan else '127.0.0.1'
    httpd = None
    candidates = [args.port] if explicit_port else [args.port, *range(8821, 8840)]
    last_err = None
    for cand in candidates:
        try:
            httpd = make_server(bind_host, cand, app)
            break
        except OSError as e:
            last_err = e
    if httpd is None:
        raise last_err  # type: ignore[misc]

    with httpd:
        url = f'http://127.0.0.1:{httpd.server_port}/'
        print(t('ready', args.lang) + ': ' + url)
        if args.lan:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                try:
                    s.connect(('192.0.2.1', 9))
                    print(f'LAN: http://{s.getsockname()[0]}:{httpd.server_port}/')
                except OSError:
                    print(f'LAN: http://<LAN-IP>:{httpd.server_port}/')
        if args.tablet:
            _connect_tablet_safe(httpd.server_port, not args.no_browser, args.lang)
        elif not args.no_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
