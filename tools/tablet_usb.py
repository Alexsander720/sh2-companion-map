"""USB ADB reverse-tunnel launcher for SILENT HILL 2 Companion & Tablet Suite."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def find_adb() -> str | None:
    """Locate adb executable via environment, PATH, local Android SDK, scoop, or scrcpy folders."""
    for env_key in ('ADB', 'SH2_ADB'):
        val = (os.environ.get(env_key) or '').strip()
        if val and Path(val).is_file():
            return str(Path(val))

    on_path = shutil.which('adb')
    if on_path:
        return on_path

    candidates: list[Path] = []
    local_app = os.environ.get('LOCALAPPDATA') or ''
    if local_app:
        candidates.append(Path(local_app) / 'Android' / 'Sdk' / 'platform-tools' / 'adb.exe')
    user_prof = os.environ.get('USERPROFILE') or ''
    if user_prof:
        candidates.append(Path(user_prof) / 'scoop' / 'shims' / 'adb.exe')
        candidates.append(Path(user_prof) / 'Android' / 'Sdk' / 'platform-tools' / 'adb.exe')
    sys_drive = (os.environ.get('SystemDrive') or '').strip()
    if sys_drive:
        root_dir = Path(sys_drive + os.sep)
        try:
            candidates.extend(sorted(root_dir.glob('scrcpy*/adb.exe'), reverse=True))
            candidates.extend(sorted(root_dir.glob('platform-tools*/adb.exe')))
        except OSError:
            pass

    for cand in candidates:
        try:
            if cand.is_file():
                return str(cand)
        except OSError:
            continue
    return None


def _run_adb(adb: str, *args: str, timeout: float = 8.0) -> subprocess.CompletedProcess[str]:
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.run(
        [adb, *args],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=timeout,
        creationflags=flags,
    )


def parse_adb_devices(output: str) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for raw_line in (output or '').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('*') or line.lower().startswith('list of devices'):
            continue
        parts = line.split()
        if len(parts) < 2 or parts[1] != 'device':
            continue
        serial = parts[0]
        meta: dict[str, str] = {}
        for tok in parts[2:]:
            if ':' in tok:
                k, v = tok.split(':', 1)
                meta[k] = v
        devices.append({
            'serial': serial,
            'state': 'device',
            'usb': ':' not in serial,
            'model': meta.get('model', '').replace('_', ' '),
            'device': meta.get('device', ''),
        })
    return devices


def list_devices(adb: str) -> list[dict[str, Any]]:
    try:
        res = _run_adb(adb, 'devices', '-l', timeout=6.0)
        if res.returncode != 0:
            return []
        return parse_adb_devices(res.stdout)
    except (OSError, subprocess.SubprocessError):
        return []


def pick_tablet_serial(devices: list[dict[str, Any]], preferred: str | None = None) -> dict[str, Any] | None:
    if not devices:
        return None
    if preferred:
        for d in devices:
            if d['serial'] == preferred:
                return d
    for d in devices:
        if d.get('usb'):
            return d
    return devices[0]


def connect_tablet(
    port: int = 8791,
    serial: str | None = None,
    open_browser: bool = True,
    lang: str = 'ru',
) -> dict[str, Any]:
    """Set up `adb reverse tcp:<port> tcp:<port>` on the USB tablet and optionally open the map UI."""
    adb = find_adb()
    if not adb:
        return {'ok': False, 'error': 'adb_not_found' if lang != 'ru' else 'adb не найден (установите platform-tools или задайте ADB)'}

    devices = list_devices(adb)
    picked = pick_tablet_serial(devices, serial)
    if not picked:
        return {'ok': False, 'adb': adb, 'error': 'no_usb_device' if lang != 'ru' else 'планшет по USB не обнаружен (включите отладку по USB)'}

    ser = picked['serial']
    rev = _run_adb(adb, '-s', ser, 'reverse', f'tcp:{port}', f'tcp:{port}', timeout=6.0)
    if rev.returncode != 0:
        err_msg = (rev.stderr or rev.stdout or 'adb reverse failed').strip()
        return {'ok': False, 'adb': adb, 'serial': ser, 'error': err_msg}

    url = f'http://127.0.0.1:{port}/'
    if open_browser:
        cmd_chrome = _run_adb(
            adb, '-s', ser, 'shell', 'am', 'start',
            '-a', 'android.intent.action.VIEW',
            '-d', url,
            '-p', 'com.android.chrome',
            timeout=8.0,
        )
        if cmd_chrome.returncode != 0 or 'Error:' in (cmd_chrome.stdout or ''):
            _run_adb(adb, '-s', ser, 'shell', 'am', 'start', '-a', 'android.intent.action.VIEW', '-d', url, timeout=8.0)

    return {
        'ok': True,
        'adb': adb,
        'serial': ser,
        'usb': bool(picked.get('usb')),
        'model': picked.get('model') or ser,
        'port': int(port),
        'url': url,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--port', type=int, default=8791)
    p.add_argument('--serial', default=None)
    p.add_argument('--no-open', action='store_true')
    p.add_argument('--serve', action='store_true', help='Start the local server with tablet USB forwarding')
    p.add_argument('--lang', choices=['ru', 'en'], default='ru')
    args = p.parse_args(argv)

    if args.serve:
        import server
        srv_args = ['--port', str(args.port), '--tablet', '--lang', args.lang]
        if args.no_open:
            srv_args.append('--no-browser')
        server.main(srv_args)
        return 0

    res = connect_tablet(port=args.port, serial=args.serial, open_browser=not args.no_open, lang=args.lang)
    if res.get('ok'):
        print(f"USB Tablet OK [{res['serial']} · {res['model']}]: {res['url']}")
        return 0
    print(f"USB Tablet error: {res.get('error')}")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
