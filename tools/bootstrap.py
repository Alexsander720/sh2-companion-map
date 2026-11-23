"""Install core requirements once per requirements-file change; honor offline mode."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def prepare(offline: bool = False, runner=subprocess.run) -> int:
    present = all(importlib.util.find_spec(name) is not None for name in ('numpy', 'PIL', 'ooz', 'texture2ddecoder'))
    if offline:
        if not present:
            print('Offline startup needs installed core packages. Run start.bat online once.')
            return 1
        return 0
    requirements = ROOT / 'requirements.txt'
    receipt = Path(sys.prefix) / 'sh2-requirements.sha256'
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    if present and receipt.is_file() and receipt.read_text(encoding='ascii') == digest:
        return 0
    result = runner([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(requirements)])
    if result.returncode:
        return result.returncode
    receipt.write_text(digest, encoding='ascii')
    return 0


if __name__ == '__main__':
    raise SystemExit(prepare('--offline' in sys.argv[1:]))
