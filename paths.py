"""Repository resources are immutable; generated and personal data live in %LOCALAPPDATA%."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

APPID = 2124490
ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
USER = Path(os.environ.get('SH2_DATA_DIR') or
            (Path(os.environ.get('LOCALAPPDATA', Path.home() / '.cache')) / 'sh2-companion-map'))
CACHE = USER / 'cache'
MAPS_DIR = CACHE / 'maps'
MARKERS_DIR = CACHE / 'markers'
ITEMS_DIR = CACHE / 'items'
LOC_FILE = CACHE / 'loc.json'
ITEM_ICONS_FILE = CACHE / 'item_icons.json'
OVERLAYS_FILE = CACHE / 'overlays.json'
RECEIPT_FILE = CACHE / 'extract_receipt.json'
GAME_DIR: Path | None = None


def atomic_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                     prefix=path.name + '.', suffix='.tmp', delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        tmp = Path(f.name)
    tmp.replace(path)


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent,
                                     prefix=path.name + '.', suffix='.tmp', delete=False) as f:
        f.write(data)
        tmp = Path(f.name)
    tmp.replace(path)


def steam_roots() -> list[Path]:
    roots: list[Path] = []
    if os.name == 'nt':
        import winreg
        for hive, key, value in [
            (winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath'),
        ]:
            try:
                with winreg.OpenKey(hive, key) as k:
                    roots.append(Path(winreg.QueryValueEx(k, value)[0]))
            except OSError:
                pass
    for variable in ('ProgramFiles(x86)', 'ProgramFiles'):
        if os.environ.get(variable):
            roots.append(Path(os.environ[variable]) / 'Steam')
    return list(dict.fromkeys(roots))


def _is_sh2_root(candidate: Path) -> bool:
    return (
        (candidate / 'SHProto/Content/Paks/SHProto-Windows.utoc').is_file()
        or (candidate / 'SHProto/Binaries/Win64/SHProto-Win64-Shipping.exe').is_file()
    )


def find_game_dir(game_dir: Path | str | None = None) -> Path | None:
    """Discover Steam libraries without assuming a drive or account identifier."""
    if game_dir:
        cand = Path(game_dir).expanduser().resolve()
        return cand if cand.exists() else None
    if GAME_DIR and GAME_DIR.exists():
        return GAME_DIR
    libraries = steam_roots()
    for root in libraries[:]:
        vdf = root / 'steamapps' / 'libraryfolders.vdf'
        try:
            text = vdf.read_text(encoding='utf-8', errors='ignore')
        except OSError:
            continue
        libraries.extend(
            Path(p.replace('\\\\', '\\'))
            for p in re.findall(r'"path"\s*"([^"\r\n]+)"', text, re.I)
        )
    for root in dict.fromkeys(libraries):
        manifest = root / 'steamapps' / f'appmanifest_{APPID}.acf'
        try:
            match = re.search(r'"installdir"\s*"([^"\r\n]+)"', manifest.read_text(encoding='utf-8', errors='ignore'))
        except OSError:
            continue
        if match:
            candidate = root / 'steamapps' / 'common' / match[1]
            if _is_sh2_root(candidate):
                return candidate
        fallback = root / 'steamapps' / 'common' / 'SILENT HILL 2'
        if _is_sh2_root(fallback):
            return fallback
    return None


def paks_dir(game_dir: Path | str | None = None) -> Path | None:
    game = find_game_dir(game_dir)
    if not game:
        return None
    p = game / 'SHProto' / 'Content' / 'Paks'
    return p if p.is_dir() else None


def shipping_exe(game_dir: Path | str | None = None) -> Path | None:
    game = find_game_dir(game_dir)
    if not game:
        return None
    exe = game / 'SHProto' / 'Binaries' / 'Win64' / 'SHProto-Win64-Shipping.exe'
    return exe if exe.is_file() else None


def find_save_roots(save_dir: Path | str | None = None) -> list[Path]:
    """Locate SILENT HILL 2 save directories (%LOCALAPPDATA%/SilentHill2/Saved/SaveGames)."""
    if save_dir:
        p = Path(save_dir).expanduser().resolve()
        return [p] if p.exists() else []
    roots: list[Path] = []
    local = os.environ.get('LOCALAPPDATA')
    if local:
        base = Path(local) / 'SilentHill2' / 'Saved' / 'SaveGames'
        if base.exists():
            roots.append(base)
    # Proton / Wine compatibility roots inside Steam libraries
    for sr in steam_roots():
        compat = sr / 'steamapps' / 'compatdata' / str(APPID) / 'pfx' / 'drive_c' / 'users' / 'steamuser' / 'AppData' / 'Local' / 'SilentHill2' / 'Saved' / 'SaveGames'
        if compat.exists():
            roots.append(compat)
    return list(dict.fromkeys(roots))
