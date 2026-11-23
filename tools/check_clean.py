"""Check every git-tracked file for private data and prohibited bundled assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_WORDS = [bytes.fromhex(s).decode('utf-8') for s in (
    '62616e3133', '61706f67756c6179', '416c657873616e646572', '40676d61696c',
    '416c6578', 'd09ed180d0bad0b5d181d182d180', '6f7263686573747261',
)]
PATTERNS = {
    'absolute Windows path': re.compile(r'(?<![A-Za-z0-9])[A-Za-z]:[\\/]'),
    'private identifier': re.compile('|'.join(re.escape(s) for s in PRIVATE_WORDS), re.I),
    'account identifier': re.compile(r'(?<![\w.])\d{17}(?![\w.])'),
    'credential': re.compile(r'\b(?:gh' + r'o_|s' + r'k-)[A-Za-z0-9_-]{8,}'),
}
PROHIBITED_NAMES = {
    'loc.json', 'overlays.json', 'item_icons.json', 'extract_receipt.json', 'SaveGameData_0.sav', 'PersistentData.sav', 'UcaSave.sav',
}
TEXT_FIELDS = {'name', 'name_en', 'description', 'game_label', 'region_label', 'pin_evidence', 'pin_rule_evidence', 'path'}


def text_content(data: bytes) -> str:
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        return data.decode('utf-8', errors='ignore')
    pieces = []
    offset = 8
    while offset + 12 <= len(data):
        size = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + size]
        if len(body) != size:
            raise ValueError('Truncated PNG chunk')
        if kind in (b'tEXt', b'eXIf'):
            pieces.append(body)
        elif kind == b'zTXt':
            key, content = body.split(b'\0', 1)
            pieces.extend((key, zlib.decompress(content[1:])))
        elif kind == b'iTXt':
            key, content = body.split(b'\0', 1)
            flag = content[0]
            lang_tag, translated_key, content = content[2:].split(b'\0', 2)
            pieces.extend((key, lang_tag, translated_key, zlib.decompress(content) if flag else content))
        offset += size + 12
        if kind == b'IEND':
            break
    if offset != len(data):
        raise ValueError('Trailing or truncated PNG content')
    return b'\n'.join(pieces).decode('utf-8', errors='ignore')


def tracked(root: Path = ROOT) -> list[str]:
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], check=True, capture_output=True)
    return [p.decode('utf-8') for p in result.stdout.split(b'\0') if p]


def inspect_file(name: str, data: bytes) -> list[str]:
    issues = []
    p = PurePosixPath(name)
    if (
        set(p.parts) & {'cache', '.venv', 'venv', 'user-data', 'tests_fixtures'}
        or p.name in PROHIBITED_NAMES
        or p.suffix.lower() in {'.pak', '.utoc', '.ucas', '.uasset', '.umap', '.ubulk', '.sav', '.locres', '.dds', '.npy'}
        or (p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and name != 'docs/screenshot.png')
    ):
        issues.append('prohibited bundled data')
    try:
        text = text_content(data)
    except (ValueError, zlib.error, struct.error):
        issues.append('invalid PNG metadata')
        text = ''
    for label, pattern in PATTERNS.items():
        if pattern.search(text):
            issues.append(label)
    if p.parts and p.parts[0] == 'data' and p.suffix == '.json':
        try:
            obj = json.loads(data)

            def visit(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key in TEXT_FIELDS:
                            issues.append('text or path in code-owned data: ' + key)
                        visit(item)
                elif isinstance(value, list):
                    for item in value:
                        visit(item)

            visit(obj)
        except (ValueError, UnicodeError):
            issues.append('invalid JSON resource')
    return sorted(set(issues))


def check(root: Path = ROOT):
    files = tracked(root)
    problems = []
    for name in files:
        path = Path(root) / name
        if path.is_symlink():
            problems.append((name, ['symlink is not a publishable local resource']))
        elif path.is_file():
            issues = inspect_file(name, path.read_bytes())
            if issues:
                problems.append((name, issues))
    return files, problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        files, problems = check(args.root)
    except subprocess.CalledProcessError:
        print('FAIL: cannot enumerate tracked git files')
        return 1
    if not files:
        print('FAIL: no tracked files; stage release files before checking')
        return 1
    for name, issues in problems:
        print(name + ': ' + ', '.join(issues))
    if problems:
        print(f'FAIL: {len(problems)} files with issues')
        return 1
    print(f'CLEAN: {len(files)} tracked files; no private signatures or prohibited data')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
