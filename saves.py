"""Discover and cache only the current user's SILENT HILL 2 saves. Read-only."""
from __future__ import annotations

from pathlib import Path
import threading

import paths
import sh2_save


class SaveReader:
    def __init__(self, save_dir: Path | str | None = None):
        self.save_dir = Path(save_dir) if save_dir else None
        self.lock = threading.Lock()
        self.stamp = None
        self.value: dict = {'ok': False}

    def read(self) -> dict:
        with self.lock:
            if self.save_dir and self.save_dir.is_file():
                files = [self.save_dir]
            else:
                roots = paths.find_save_roots(self.save_dir)
                files = []
                for r in roots:
                    if r.is_file():
                        files.append(r)
                    elif r.is_dir():
                        files.extend(r.rglob('SaveGameData_*.sav'))
                        files.extend(r.rglob('UcaSave.sav'))
            stamp = []
            for p in files:
                try:
                    st = p.stat()
                    stamp.append((str(p), st.st_size, st.st_mtime_ns))
                except OSError:
                    continue
            stamp.sort()
            if self.stamp != stamp:
                self.value = sh2_save.read(self.save_dir) if stamp else {'ok': False}
                self.stamp = stamp
            return self.value
