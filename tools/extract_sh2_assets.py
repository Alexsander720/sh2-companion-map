"""Extract paper maps, red marker sprites, room labels, and RU/EN localization from local SILENT HILL 2."""
from __future__ import annotations

import argparse
import io
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import paths
from tools.ue_archive import (
    Pak,
    ZenContext,
    decode_texture2d,
    extract_textblock_strings,
    parse_canvas_slot,
    parse_locres,
    parse_uimage_info,
    zen_name_map,
)

EXTRACTOR_VERSION = 3

ITEM_DATATABLES = (
    'Game/Gameplay/Data/Items/Items_DT',
    'Game/Gameplay/Data/Items/WeaponItems_DT',
    'Game/Gameplay/Data/Items/EquipmentItems_DT',
    'Game/Gameplay/Data/Items/Useables_DT',
    'Game/Gameplay/Data/Items/MapItems_DT',
)
# Inventory rows shown in the HUD supplies grid and personal mementos even when no pin references them directly
HUD_ROWS = (
    'HealthDrink', 'Syringe', 'HandgunAmmo', 'ShotgunAmmo', 'RifleAmmo',
    'Pistol', 'Shotgun', 'Rifle', 'Radio', 'Flashlight',
    'PhotoOfMary', 'LetterFromMary', 'LetterFromMary2', 'LetterFromMary3',
    'BcaOW_AngelasKnife', 'WsaFW_MarysScarf',
)
WEAPON_ROWS = ('WoodenPlank', 'IronPipe', 'Chainsaw', 'Pistol', 'Shotgun', 'Rifle')
MEMENTO_PHOTO_STEMS = frozenset({'PhotoMary_Inv_TB', 'LetterFromMary_Inv_TB', 'LetterFromMary3_Inv_TB'})


def _flatten_locres(loc: dict[str, dict[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for ns_dict in loc.values():
        out.update(ns_dict)
    return out


def _prepare_icon(im, max_side: int, lift_dark: bool):
    """Tight alpha crop + gentle midtone lift for dark 3D renders (steel, wood); Polaroids stay untouched."""
    import numpy as np
    from PIL import Image

    im = im.convert('RGBA')
    arr = np.asarray(im)
    ys, xs = np.where(arr[..., 3] > 10)
    if len(xs) and len(ys):
        pad = 10
        im = im.crop((max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad),
                      min(im.width, int(xs.max()) + pad + 1), min(im.height, int(ys.max()) + pad + 1)))
    if lift_dark:
        a = np.asarray(im, dtype=np.float32)
        vis = a[..., 3] > 24
        if np.any(vis):
            rgb = a[..., :3] / 255.0
            lum = float((0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])[vis].mean())
            if lum < 0.42:
                gamma = 0.74 if lum < 0.25 else 0.82
                a[..., :3] = np.clip((rgb ** gamma) * 1.08, 0.0, 1.0) * 255.0
                im = Image.fromarray(a.astype(np.uint8))
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return im


def _decode_transcript_asset(io_store, asset_key: str, ru_flat: dict[str, str], en_flat: dict[str, str]) -> tuple[str, str]:
    blob = io_store.read(asset_key)
    hdr_sz, = struct.unpack_from('<I', blob, 4)
    eb = blob[hdr_sz:]
    keys = [m.group(1).decode('ascii') for m in re.finditer(rb'([0-9A-F]{32})', eb)]
    parts_ru, parts_en = [], []
    seen = set()
    for k in keys:
        if k in seen:
            continue
        seen.add(k)
        vr = (ru_flat.get(k) or '').strip()
        ve = (en_flat.get(k) or '').strip()
        if vr:
            parts_ru.append(vr)
        if ve:
            parts_en.append(ve)
    return '\n\n'.join(parts_ru), '\n\n'.join(parts_en)


def _parse_items_dt_rows(io_store, ru_flat: dict[str, str], en_flat: dict[str, str]):
    """Parse all rows from Items_DT using exact row-boundary headers + SoftObjectPath verification."""
    inv_files = {
        f.rsplit('/', 1)[-1].removesuffix('.uasset'): f
        for f in io_store.files
        if '/InventoryItems/' in f and f.endswith('.uasset')
    }
    tr_files_by_rel = {
        '/Game/' + f.removeprefix('SHProto/Content/').removesuffix('.uasset'): f
        for f in io_store.files
        if '/Data/Items/Transcripts/' in f and f.endswith('.uasset')
    }
    rk = io_store.resolve_key('Game/Gameplay/Data/Items/Items_DT')
    if not rk:
        return {}, {}, {}, {}, {}, {}, {}

    blob = io_store.read(rk)
    nm = zen_name_map(blob)
    start_off, = struct.unpack_from('<I', blob, 4)
    asset_re = re.compile(r'(_Inspect|_MI|_TB|_Transcript\w*|_INV|_BP_C|_HC|FogMap\w*)$|^/|^None$')

    rows: list[tuple[int, str]] = []
    for o in range(start_off, len(blob) - 12):
        if blob[o + 8] == 0x80 and blob[o + 9] == 0x43:
            idx_n, num = struct.unpack_from('<II', blob, o)
            if idx_n < len(nm) and num <= 64 and not asset_re.search(nm[idx_n]) and nm[idx_n] not in ('None', 'RowStruct', 'DataTable'):
                cand = nm[idx_n] + (f'_{num - 1}' if num else '')
                rows.append((o, cand))

    tx = [
        (m.start(), m.group(1).decode('ascii'))
        for m in re.finditer(rb'[\x00-\x7f]\x00\x00\x00([0-9A-F]{32})\x00', blob)
    ]
    icon_path_to_stem = {
        i: s.rsplit('/', 1)[-1].split('.')[0]
        for i, s in enumerate(nm)
        if '/InventoryItems/' in s and s.rsplit('/', 1)[-1].split('.')[0] in inv_files
    }
    tr_path_indices = {
        i: s for i, s in enumerate(nm) if '/Data/Items/Transcripts/' in s
    }

    items_ru: dict[str, str] = {}
    items_en: dict[str, str] = {}
    desc_ru: dict[str, str] = {}
    desc_en: dict[str, str] = {}
    item_tr_ru: dict[str, str] = {}
    item_tr_en: dict[str, str] = {}
    row_to_stem: dict[str, str] = {}
    tr_cache: dict[str, tuple[str, str]] = {}

    for idx_r, (ro, row) in enumerate(rows):
        end_o = rows[idx_r + 1][0] if idx_r + 1 < len(rows) else len(blob)
        r_tx = [k for p, k in tx if ro < p < end_o]
        if r_tx:
            r_name = (ru_flat.get(r_tx[0]) or '').strip()
            e_name = (en_flat.get(r_tx[0]) or '').strip()
            if r_name or e_name:
                items_ru[row] = r_name or e_name
                items_en[row] = e_name or r_name
        if len(r_tx) >= 2:
            r_desc = (ru_flat.get(r_tx[1]) or '').strip()
            e_desc = (en_flat.get(r_tx[1]) or '').strip()
            if r_desc or e_desc:
                desc_ru[row] = r_desc or e_desc
                desc_en[row] = e_desc or r_desc

        found_icon = None
        fallback_icon = None
        found_trs: list[str] = []
        for o2 in range(ro + 8, max(ro + 8, end_o - 16)):
            i2, n2 = struct.unpack_from('<II', blob, o2)
            if n2 == 0 and i2 in icon_path_to_stem and not found_icon:
                stem = icon_path_to_stem[i2]
                i3, n3 = struct.unpack_from('<II', blob, o2 + 8)
                if n3 == 0 and i3 < len(nm) and nm[i3] == stem:
                    found_icon = stem
                elif fallback_icon is None and (o2 - ro) >= 48:
                    fallback_icon = stem
            if i2 in tr_path_indices and n2 <= 64:
                cand_tr = tr_path_indices[i2] + (f'_{n2 - 1}' if n2 else '')
                asset_key = tr_files_by_rel.get(cand_tr)
                if asset_key and asset_key not in found_trs:
                    found_trs.append(asset_key)

        chosen_icon = found_icon or fallback_icon
        if chosen_icon:
            row_to_stem[row] = chosen_icon

        if found_trs:
            parts_ru, parts_en = [], []
            for ak in found_trs:
                if ak not in tr_cache:
                    tr_cache[ak] = _decode_transcript_asset(io_store, ak, ru_flat, en_flat)
                tr_r, tr_e = tr_cache[ak]
                if tr_r and tr_r not in parts_ru:
                    parts_ru.append(tr_r)
                if tr_e and tr_e not in parts_en:
                    parts_en.append(tr_e)
            if parts_ru or parts_en:
                item_tr_ru[row] = '\n\n'.join(parts_ru) or '\n\n'.join(parts_en)
                item_tr_en[row] = '\n\n'.join(parts_en) or '\n\n'.join(parts_ru)

    if 'Syringe' in row_to_stem and 'SyringeConsumable_Inv_TB' in inv_files:
        row_to_stem['Syringe'] = 'SyringeConsumable_Inv_TB'

    return items_ru, items_en, desc_ru, desc_en, item_tr_ru, item_tr_en, row_to_stem


def _extract_item_icons(io_store, wanted_rows: set[str], force: bool,
                        preparsed_map: dict[str, str] | None = None) -> dict[str, str]:
    """Map item DataTable rows -> InventoryItems render stem; decode each needed texture once."""
    inv_files = {
        f.rsplit('/', 1)[-1].removesuffix('.uasset'): f
        for f in io_store.files
        if '/InventoryItems/' in f and f.endswith('.uasset')
    }
    if not inv_files:
        return {}
    row_to_stem: dict[str, str] = dict(preparsed_map or {})
    for dt in ITEM_DATATABLES:
        rk = io_store.resolve_key(dt)
        if not rk:
            continue
        blob = io_store.read(rk)
        nm = zen_name_map(blob)
        icon_names = {}
        for i, s in enumerate(nm):
            stem = s.rsplit('/', 1)[-1].split('.')[0]
            if '/InventoryItems/' in s and stem in inv_files:
                icon_names[i] = stem
        start_off, = struct.unpack_from('<I', blob, 4)
        rows_pos, icons_pos = [], []
        for o in range(start_off, len(blob) - 8):
            idx_n, num = struct.unpack_from('<II', blob, o)
            if idx_n < len(nm) and num <= 32:
                cand = nm[idx_n] + (f'_{num - 1}' if num else '')
                if cand in wanted_rows and cand not in row_to_stem:
                    rows_pos.append((o, cand))
                if num == 0 and idx_n in icon_names:
                    icons_pos.append((o, icon_names[idx_n]))
        for ro, rname in rows_pos:
            if rname in row_to_stem:
                continue
            near = [iname for ioff, iname in icons_pos if ro + 48 <= ioff < ro + 900]
            if near:
                row_to_stem[rname] = near[0]
    if 'Syringe' in row_to_stem and 'SyringeConsumable_Inv_TB' in inv_files:
        row_to_stem['Syringe'] = 'SyringeConsumable_Inv_TB'

    weapon_stems = {row_to_stem[w] for w in WEAPON_ROWS if w in row_to_stem}
    paths.ITEMS_DIR.mkdir(parents=True, exist_ok=True)
    ready: set[str] = set()
    for stem in sorted(set(row_to_stem.values())):
        out_p = paths.ITEMS_DIR / f'{stem}.png'
        if out_p.is_file() and not force:
            ready.add(stem)
            continue
        try:
            is_photo = stem.startswith('Reflections_Photo_') or stem in MEMENTO_PHOTO_STEMS or 'Polaroid' in stem
            # High-res studio renders (768px for photos/letters/clues/memos, 420px for weapons/HUD) for crisp large inspect views
            side = 768 if is_photo else (420 if stem in weapon_stems else 640)
            im = _prepare_icon(decode_texture2d(io_store, inv_files[stem]), side, lift_dark=not is_photo)
            buf = io.BytesIO()
            im.save(buf, 'PNG', optimize=True)
            paths.atomic_bytes(out_p, buf.getvalue())
            ready.add(stem)
        except (ValueError, KeyError, OSError):
            continue
    return {row: stem for row, stem in sorted(row_to_stem.items()) if stem in ready}


def _extract_dt_items(io_store, ru_flat: dict[str, str], en_flat: dict[str, str],
                      pin_rows: set[str]) -> tuple[dict[str, str], dict[str, str]]:
    items_ru: dict[str, str] = {}
    items_en: dict[str, str] = {}
    asset_re = re.compile(r'(_Inspect|_MI|_TB|_Transcript\w*|_INV|_BP_C|_HC|FogMap\w*)$|^/|^None$')
    dt_paths = [
        'Game/Gameplay/Data/Items/Items_DT',
        'Game/Gameplay/Data/Items/WeaponItems_DT',
        'Game/Gameplay/Data/Items/MapItems_DT',
        'Game/Gameplay/Data/Items/EquipmentItems_DT',
        'Game/Gameplay/Data/Items/Useables_DT',
        'Game/Items/DataTables/MapItems_DT',
    ]
    for dt in dt_paths:
        rk = io_store.resolve_key(dt)
        if not rk:
            continue
        blob = io_store.read(rk)
        nm = zen_name_map(blob)
        base_ok = {k for k, s in enumerate(nm) if not asset_re.search(s)}
        start_off, = struct.unpack_from('<I', blob, 4)
        refs = []
        for o in range(start_off, len(blob) - 8):
            idx_n, num = struct.unpack_from('<II', blob, o)
            if idx_n in base_ok and num <= 64:
                cand = nm[idx_n] + (f'_{num - 1}' if num else '')
                if num == 0 or cand in pin_rows or cand.startswith('Reflections_Photo_'):
                    refs.append((o, cand))
        tx = [
            (m.start(), m.group(1).decode('ascii'))
            for m in re.finditer(rb'[\x00-\x7f]\x00\x00\x00([0-9A-F]{32})\x00', blob)
        ]
        for pos, row in refs:
            if row in items_ru and row in items_en:
                continue
            for p_tx, key in tx:
                if pos < p_tx < pos + 850:
                    r_val = (ru_flat.get(key) or '').strip()
                    e_val = (en_flat.get(key) or '').strip()
                    if r_val or e_val:
                        items_ru.setdefault(row, r_val or e_val)
                        items_en.setdefault(row, e_val or r_val)
                        break
    return items_ru, items_en


def _extract_savepoints(io_store, ru_loc: dict, en_loc: dict, ru_flat: dict, en_flat: dict):
    rk = io_store.resolve_key('Game/UI/GameplaySaveMenu/SavePoints_DT')
    places_ru: dict[str, list[str]] = {}
    places_en: dict[str, list[str]] = {}
    if not rk:
        return places_ru, places_en
    blob = io_store.read(rk)
    nm = zen_name_map(blob)
    wanted = {k for k, s in enumerate(nm) if not s.startswith('/') and s not in ('SavePoints_DT', 'None')}
    start_off, = struct.unpack_from('<I', blob, 4)
    refs = []
    for o in range(start_off, len(blob) - 8):
        idx_n, num = struct.unpack_from('<II', blob, o)
        if num == 0 and idx_n in wanted:
            refs.append((o, nm[idx_n]))
    tx = [
        (m.start(), m.group(1).decode('latin1'))
        for m in re.finditer(rb'[\x00-\x7f]\x00\x00\x00([0-9A-F]{32}|\w+DisplayTitle)\x00', blob)
    ]

    def look(loc_ns: dict, flat: dict, k: str) -> str:
        return (loc_ns.get('SavePoints_DT', {}).get(k) or loc_ns.get('', {}).get(k) or flat.get(k) or '').strip()

    tmp_ru: dict[str, list[str]] = {}
    tmp_en: dict[str, list[str]] = {}
    for pos, key in tx:
        prev = [r for r in refs if r[0] < pos]
        if prev:
            tag = prev[-1][1]
            tmp_ru.setdefault(tag, []).append(look(ru_loc, ru_flat, key))
            tmp_en.setdefault(tag, []).append(look(en_loc, en_flat, key))
    for tag, vals in tmp_ru.items():
        if len(vals) >= 2 and any(vals[:2]):
            places_ru[tag] = vals[:2]
    for tag, vals in tmp_en.items():
        if len(vals) >= 2 and any(vals[:2]):
            places_en[tag] = vals[:2]
    return places_ru, places_en


def _extract_transcripts(io_store, pins: list[dict], ru_flat: dict[str, str], en_flat: dict[str, str]):
    tr_ids = sorted({p['tr_id'] for p in pins if p.get('tr_id')})
    tr_ru: dict[str, str] = {}
    tr_en: dict[str, str] = {}
    for tid in tr_ids:
        rk = io_store.resolve_key(tid)
        if not rk:
            continue
        blob = io_store.read(rk)
        hdr_sz, = struct.unpack_from('<I', blob, 4)
        eb = blob[hdr_sz:]
        keys = [m.group(1).decode('ascii') for m in re.finditer(rb'([0-9A-F]{32})', eb)]
        parts_ru, parts_en = [], []
        seen = set()
        for k in keys:
            if k in seen:
                continue
            seen.add(k)
            vr = (ru_flat.get(k) or '').strip()
            ve = (en_flat.get(k) or '').strip()
            if vr:
                parts_ru.append(vr)
            if ve:
                parts_en.append(ve)
        if parts_ru:
            tr_ru[tid] = '\n\n'.join(parts_ru)
        if parts_en:
            tr_en[tid] = '\n\n'.join(parts_en)
    return tr_ru, tr_en


def _extract_widget_overlays(zc: ZenContext, maps_meta: list[dict], marker_sizes: dict[str, list[int]],
                             ru_flat: dict[str, str], en_flat: dict[str, str]) -> dict[str, dict]:
    overlays: dict[str, dict] = {}
    for m in maps_meta:
        slug = m['slug']
        w_asset = m.get('widget_asset')
        if not w_asset:
            overlays[slug] = {'labels': [], 'objects': []}
            continue
        try:
            _nm, _imps, exps, res_fn = zc.parse_package(w_asset)
        except KeyError:
            overlays[slug] = {'labels': [], 'objects': []}
            continue

        obj_panel_idx = next((e['idx'] for e in exps if e['name'] == 'ObjectsContainer'), None)
        fog_panel_idx = next((e['idx'] for e in exps if e['name'] == 'FogRevealObjectsContainer'), None)

        canvas_slots: dict[int, dict] = {}
        overlay_children: dict[int, list[int]] = {}
        for e in exps:
            cls = e['class']
            if cls.endswith('/CanvasPanelSlot'):
                sd = parse_canvas_slot(e['bytes'])
                if sd['content_exp'] is not None:
                    canvas_slots[sd['content_exp']] = sd
            elif cls.endswith('/OverlaySlot') and len(e['bytes']) >= 12:
                par_i, cnt_i = struct.unpack_from('<ii', e['bytes'], len(e['bytes']) - 12)
                if par_i > 0 and cnt_i > 0:
                    overlay_children.setdefault(par_i - 1, []).append(cnt_i - 1)

        labels = []
        objects = []

        for exp_idx, sd in sorted(canvas_slots.items(), key=lambda kv: kv[1]['zorder']):
            if exp_idx >= len(exps):
                continue
            e = exps[exp_idx]
            par = sd['parent']
            if par == fog_panel_idx:
                continue

            anchor_x = 2048.0 * sd['anchors'][0] + sd['left']
            anchor_y = 2048.0 * sd['anchors'][1] + sd['top']

            if par == obj_panel_idx:
                if e['class'].endswith('/Image'):
                    info = parse_uimage_info(e['bytes'], res_fn)
                    res_path = info['resource'] or ''
                    sprite = Path(res_path).stem if res_path else ''
                    if not sprite:
                        continue
                    tw, th = marker_sizes.get(sprite, [int(info['image_size'][0]), int(info['image_size'][1])])
                    w = tw if sd['autosize'] else sd['right']
                    h = th if sd['autosize'] else sd['bottom']
                    tl_x = anchor_x - w * sd['align'][0] + info['tx']
                    tl_y = anchor_y - h * sd['align'][1] + info['ty']
                    cx = tl_x + w * 0.5
                    cy = tl_y + h * 0.5
                    objects.append({
                        'oid': e['name'],
                        'kind': 'image',
                        'sprite': sprite,
                        'px': [round(cx, 1), round(cy, 1)],
                        'size': [round(w * abs(info['sx']), 1), round(h * abs(info['sy']), 1)],
                        'flip': [info['sx'] < 0, info['sy'] < 0],
                        'angle': round(info['angle'], 1),
                        'z': sd['zorder'],
                    })
                elif e['class'].endswith('/Overlay'):
                    ch_indices = overlay_children.get(exp_idx, [])
                    sprite = ''
                    note_ru = note_en = ''
                    img_size = [round(sd['right'], 1), round(sd['bottom'], 1)]
                    img_angle = 0.0
                    for ci in ch_indices:
                        if ci >= len(exps):
                            continue
                        ce = exps[ci]
                        if ce['class'].endswith('/Image'):
                            cinfo = parse_uimage_info(ce['bytes'], res_fn)
                            if cinfo['resource']:
                                sprite = Path(cinfo['resource']).stem
                                tw, th = marker_sizes.get(sprite, [64, 64])
                                img_size = [round(tw * abs(cinfo['sx']), 1), round(th * abs(cinfo['sy']), 1)]
                                img_angle = round(cinfo['angle'], 1)
                        elif ce['class'].endswith('/TextBlock'):
                            nr, ne, _, _ = extract_textblock_strings(ce['bytes'], ru_flat, en_flat)
                            if nr or ne:
                                note_ru, note_en = nr, ne
                    w = sd['right'] if not sd['autosize'] else img_size[0]
                    h = sd['bottom'] if not sd['autosize'] else img_size[1]
                    cx = anchor_x - w * sd['align'][0] + w * 0.5
                    cy = anchor_y - h * sd['align'][1] + h * 0.5
                    objects.append({
                        'oid': e['name'],
                        'kind': 'overlay',
                        'sprite': sprite,
                        'px': [round(cx, 1), round(cy, 1)],
                        'size': img_size,
                        'angle': img_angle,
                        'note_ru': note_ru,
                        'note_en': note_en,
                        'z': sd['zorder'],
                    })
            else:
                # Static map text label (room number, street name, wing title)
                if e['class'].endswith('/TextBlock'):
                    if e['name'].startswith('NoMap') or 'Debug' in e['name']:
                        continue
                    tr_s, te_s, ang, fsz = extract_textblock_strings(e['bytes'], ru_flat, en_flat)
                    if not tr_s and not te_s:
                        continue
                    w = 0.0 if sd['autosize'] else sd['right']
                    h = 0.0 if sd['autosize'] else sd['bottom']
                    cx = anchor_x + (0.5 - sd['align'][0]) * w
                    cy = anchor_y + (0.5 - sd['align'][1]) * h
                    if not (0.0 <= cx <= 2048.0 and 0.0 <= cy <= 2048.0):
                        continue
                    labels.append({
                        'px': [round(cx, 1), round(cy, 1)],
                        'ru': tr_s,
                        'en': te_s,
                        'angle': ang,
                        'size': fsz,
                    })

        overlays[slug] = {'labels': labels, 'objects': objects}
    return overlays


def is_extracted() -> bool:
    if not (paths.RECEIPT_FILE.is_file() and paths.LOC_FILE.is_file() and paths.OVERLAYS_FILE.is_file()
            and paths.ITEM_ICONS_FILE.is_file()):
        return False
    try:
        rec = json.loads(paths.RECEIPT_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    if rec.get('version') != EXTRACTOR_VERSION:
        return False
    maps_meta = json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))
    return all((paths.MAPS_DIR / f"{m['slug']}.png").is_file() for m in maps_meta)


def prepare(game_dir: Path | str | None = None, force: bool = False, notify=print) -> bool:
    if not force and is_extracted():
        return True
    pdir = paths.paks_dir(game_dir)
    if not pdir:
        return False
    utoc = pdir / 'SHProto-Windows.utoc'
    pak_path = pdir / 'SHProto-Windows.pak'
    if not (utoc.is_file() and pak_path.is_file()):
        return False

    maps_meta = json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))
    world_pins = json.loads((paths.DATA / 'world_pins.json').read_text(encoding='utf-8'))

    paths.MAPS_DIR.mkdir(parents=True, exist_ok=True)
    paths.MARKERS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Localization from .pak
    with Pak(pak_path) as pak:
        ru_loc = parse_locres(pak.read('SHProto/Content/Localization/Game/ru/Game.locres'))
        en_loc = parse_locres(pak.read('SHProto/Content/Localization/Game/en/Game.locres'))
        ru_dlg = parse_locres(pak.read('SHProto/Content/Localization/Dialog/ru/Dialog.locres')) if 'SHProto/Content/Localization/Dialog/ru/Dialog.locres' in pak.entries else {}
        en_dlg = parse_locres(pak.read('SHProto/Content/Localization/Dialog/en/Dialog.locres')) if 'SHProto/Content/Localization/Dialog/en/Dialog.locres' in pak.entries else {}

    ru_flat = {**_flatten_locres(ru_dlg), **_flatten_locres(ru_loc)}
    en_flat = {**_flatten_locres(en_dlg), **_flatten_locres(en_loc)}

    zc = ZenContext(pdir)
    io_store = zc.io

    pin_rows = {p['row'] for p in world_pins if p.get('row')}
    for p in world_pins:
        pin_rows.update(p.get('rows') or ())
        pin_rows.update(p.get('rewards') or ())
    dt_ru, dt_en, desc_ru, desc_en, item_tr_ru, item_tr_en, dt_icons = _parse_items_dt_rows(io_store, ru_flat, en_flat)
    fb_ru, fb_en = _extract_dt_items(io_store, ru_flat, en_flat, pin_rows)
    items_ru = {**fb_ru, **dt_ru}
    items_en = {**fb_en, **dt_en}
    places_ru, places_en = _extract_savepoints(io_store, ru_loc, en_loc, ru_flat, en_flat)
    tr_ru, tr_en = _extract_transcripts(io_store, world_pins, ru_flat, en_flat)

    paths.atomic_json(paths.LOC_FILE, {
        'items_ru': items_ru,
        'items_en': items_en,
        'desc_ru': desc_ru,
        'desc_en': desc_en,
        'item_transcripts_ru': item_tr_ru,
        'item_transcripts_en': item_tr_en,
        'places_ru': places_ru,
        'places_en': places_en,
        'transcripts_ru': tr_ru,
        'transcripts_en': tr_en,
    })
    notify(
        f'Localization extracted: {len(items_ru)} items, {len(desc_ru)} descriptions, '
        f'{len(places_ru)} save points, {len(tr_ru)} pin transcripts, {len(item_tr_ru)} item transcripts'
    )

    # 2. Red marker sprites + player pointer
    marker_sizes: dict[str, list[int]] = {}
    marker_files = [
        f for f in sorted(io_store.files)
        if ('/GameplayMenu/MapMarkers/' in f or f.endswith('/MapPlayerPionter_TB.uasset'))
        and f.endswith('.uasset') and not f.endswith(('_MI.uasset', '_M.uasset'))
    ]
    for mf in marker_files:
        stem = Path(mf).stem
        try:
            im = decode_texture2d(io_store, mf)
        except ValueError:
            continue
        marker_sizes[stem] = [im.width, im.height]
        out_p = paths.MARKERS_DIR / f'{stem}.png'
        if force or not out_p.is_file():
            buf = io.BytesIO()
            im.save(buf, 'PNG', compress_level=4)
            paths.atomic_bytes(out_p, buf.getvalue())
    notify(f'Marker sprites extracted: {len(marker_sizes)}')

    # 3. Widget overlays (room/street labels + ObjectsContainer red marks)
    overlays = _extract_widget_overlays(zc, maps_meta, marker_sizes, ru_flat, en_flat)
    paths.atomic_json(paths.OVERLAYS_FILE, overlays)

    # 4. All 41 paper map textures (2048x2048)
    tex_mem: dict[str, bytes] = {}
    for m in maps_meta:
        slug = m['slug']
        out_p = paths.MAPS_DIR / f'{slug}.png'
        if not force and out_p.is_file():
            continue
        paper_asset = m.get('paper_asset') or m.get('nofog_asset')
        if not paper_asset:
            continue
        if paper_asset not in tex_mem:
            im = decode_texture2d(io_store, paper_asset)
            buf = io.BytesIO()
            im.save(buf, 'PNG', compress_level=3)
            tex_mem[paper_asset] = buf.getvalue()
        paths.atomic_bytes(out_p, tex_mem[paper_asset])
    notify(f'Paper maps extracted: {len(maps_meta)} sheets')

    # 5. High-res inventory renders for all Items_DT rows (weapons, keys, puzzle clues, mementos, Polaroids, memos, HUD)
    wanted_rows = set(pin_rows) | set(HUD_ROWS) | set(dt_icons.keys()) | {f'Reflections_Photo_{i}' for i in range(1, 27)}
    try:
        item_icons = _extract_item_icons(io_store, wanted_rows, force, preparsed_map=dt_icons)
    except Exception as exc:  # icons are optional polish; never block map startup
        notify(f'Item renders skipped: {exc.__class__.__name__}')
        item_icons = {}
    paths.atomic_json(paths.ITEM_ICONS_FILE, item_icons)
    notify(f'Item renders extracted: {len(set(item_icons.values()))} images for {len(item_icons)} item rows')

    paths.atomic_json(paths.RECEIPT_FILE, {
        'version': EXTRACTOR_VERSION,
        'maps': len(maps_meta),
        'markers': len(marker_sizes),
        'item_icons': len(item_icons),
    })
    return True


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-dir', type=Path)
    p.add_argument('--force', action='store_true')
    args = p.parse_args(argv)
    ok = prepare(args.game_dir, force=args.force, notify=print)
    if not ok:
        print('SILENT HILL 2 archive not found; starting without extracted textures.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
