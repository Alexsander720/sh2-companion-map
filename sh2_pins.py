"""Correlate SILENT HILL 2 world pins and red-marker overlays with read-only save data."""
from __future__ import annotations

from functools import lru_cache
import json
import re
from typing import Any

import paths
from i18n import category, language, puzzle_title, t
import sh2_memory

REGION_ORDER = (
    'south-vale',
    'woodside',
    'blue-creek',
    'hospital-fw',
    'hospital-ow',
    'prison',
    'labyrinth',
    'hotel',
)
_REGION_RANK = {rk: i for i, rk in enumerate(REGION_ORDER)}

WEAPON_ORDER = ('WoodenPlank', 'IronPipe', 'Chainsaw', 'Pistol', 'Shotgun', 'Rifle')
WEAPON_AMMO_ROW = {'Pistol': 'HandgunAmmo', 'Shotgun': 'ShotgunAmmo', 'Rifle': 'RifleAmmo'}
MEMENTO_ROWS = (
    'LetterFromMary',
    'LetterFromMary2',
    'LetterFromMary3',
    'PhotoOfMary',
    'BcaOW_AngelasKnife',
    'WsaFW_MarysScarf',
)
_NOTE_ROW_RE = re.compile(r'(Note\d*|_Memo|Brochure|Flyer|Postcard|LetterTrailer|LetterWrench|Rifle_Hint)$', re.I)


@lru_cache(maxsize=1)
def load_maps_meta() -> list[dict[str, Any]]:
    return json.loads((paths.DATA / 'maps_meta.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def load_world_pins() -> list[dict[str, Any]]:
    return json.loads((paths.DATA / 'world_pins.json').read_text(encoding='utf-8'))


_EMPTY_LOC: dict[str, Any] = {
    'items_ru': {}, 'items_en': {},
    'desc_ru': {}, 'desc_en': {},
    'item_transcripts_ru': {}, 'item_transcripts_en': {},
    'places_ru': {}, 'places_en': {},
    'transcripts_ru': {}, 'transcripts_en': {},
}
_LOC_CACHE: tuple[str, float, dict[str, Any]] = ('', -1.0, _EMPTY_LOC)
_OVERLAYS_CACHE: tuple[str, float, dict[str, Any]] = ('', -1.0, {})
_ICONS_CACHE: tuple[str, float, dict[str, str]] = ('', -1.0, {})


def _load_loc() -> dict[str, Any]:
    global _LOC_CACHE
    p = paths.LOC_FILE
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return dict(_EMPTY_LOC)
    key = str(p)
    if _LOC_CACHE[0] != key or _LOC_CACHE[1] != mtime:
        try:
            doc = json.loads(p.read_text(encoding='utf-8'))
            _LOC_CACHE = (key, mtime, doc if isinstance(doc, dict) else dict(_EMPTY_LOC))
        except (OSError, ValueError):
            _LOC_CACHE = (key, mtime, dict(_EMPTY_LOC))
    return _LOC_CACHE[2]


def _load_overlays() -> dict[str, Any]:
    global _OVERLAYS_CACHE
    p = paths.OVERLAYS_FILE
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return {}
    key = str(p)
    if _OVERLAYS_CACHE[0] != key or _OVERLAYS_CACHE[1] != mtime:
        try:
            doc = json.loads(p.read_text(encoding='utf-8'))
            _OVERLAYS_CACHE = (key, mtime, doc if isinstance(doc, dict) else {})
        except (OSError, ValueError):
            _OVERLAYS_CACHE = (key, mtime, {})
    return _OVERLAYS_CACHE[2]


def load_item_icons() -> dict[str, str]:
    """Item DataTable row -> extracted inventory render stem (empty until the first local extraction)."""
    global _ICONS_CACHE
    p = paths.ITEM_ICONS_FILE
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return {}
    key = str(p)
    if _ICONS_CACHE[0] != key or _ICONS_CACHE[1] != mtime:
        try:
            doc = json.loads(p.read_text(encoding='utf-8'))
            _ICONS_CACHE = (key, mtime, {str(k): str(v) for k, v in doc.items()} if isinstance(doc, dict) else {})
        except (OSError, ValueError):
            _ICONS_CACHE = (key, mtime, {})
    return _ICONS_CACHE[2]


def item_icon(row: str | None) -> str | None:
    return load_item_icons().get(row) if row else None


def resolve_place_label(location_tag: str | None, lang: str = 'en') -> str | None:
    if not location_tag:
        return None
    loc = _load_loc()
    table = loc['places_ru'] if language(lang) == 'ru' else loc['places_en']
    pair = table.get(location_tag)
    if pair and any(pair):
        return ' — '.join(p for p in pair if p)
    return location_tag.replace('_', ' ')


def _human_row(row: str, items_lang: dict[str, str]) -> str:
    if row in items_lang and items_lang[row]:
        return items_lang[row]
    # Clean readable fallback if game archive wasn't extracted
    s = row
    for pref in ('Reflections_Photo_', 'WsaFW_', 'BcaOW_', 'HosFW_', 'HosOW_', 'PriOW_', 'LabOW_', 'LhOW_', 'LhFW_', 'EcFW_', 'EcOW_', 'WcFW_', 'RtSH_', 'HisOW_', 'End_'):
        if s.startswith(pref):
            if pref == 'Reflections_Photo_':
                return f'Strange Photo #{s.removeprefix(pref)}'
            s = s.removeprefix(pref)
            break
    return s.replace('_', ' ')


def _prepare_save_index(save_data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not save_data or not save_data.get('ok'):
        return None
    maps_by_slug = sh2_memory.load_maps_by_slug()
    active_slug = save_data.get('active_map_slug')
    active_region = maps_by_slug[active_slug]['region'] if active_slug in maps_by_slug else None
    return {
        'items': save_data.get('items') or {},
        'memos': set(save_data.get('memos') or ()),
        'glimpses': set(save_data.get('glimpses') or ()),
        'map_objects': save_data.get('map_objects') or {},
        'map_dynamic': save_data.get('map_dynamic') or {},
        'actor_states': save_data.get('actor_states') or {},
        'active_slug': active_slug,
        'active_region': active_region,
    }


def _evaluate_pin(pin: dict[str, Any], map_meta: dict[str, Any], sidx: dict[str, Any] | None,
                  manual_ids: set[str] | None) -> tuple[str, str | None]:
    """Return (status, door_state) where status in ('collected', 'not_collected', 'unknown')."""
    pid_s = str(pin['id'])
    manual_hit = bool(manual_ids and pid_s in manual_ids)
    cat = pin['cat']
    guid = pin.get('guid') or ''
    oids = pin.get('oids') or ()

    if sidx is None:
        return ('collected' if manual_hit else 'unknown'), ('locked' if pin.get('locked_init') else None)

    enum_tag = map_meta['enum_tag']
    m_objs = sidx['map_objects'].get(enum_tag) or {}
    act = sidx['actor_states'].get(guid) or {}
    items = sidx['items']

    if cat == 'door':
        dstate = 'locked' if pin.get('locked_init') else 'closed'
        for oid in oids:
            if oid in m_objs:
                val = m_objs[oid]['val']
                if val == 3:
                    dstate = 'opened'
                elif val == 4:
                    dstate = 'blocked'
                elif val in (1, 2):
                    dstate = 'locked'
                break
        if act.get('opened'):
            dstate = 'opened'
        if manual_hit:
            return 'collected', 'opened'
        return ('collected' if dstate == 'opened' else 'not_collected'), dstate

    if manual_hit:
        return 'collected', None

    if cat == 'memo':
        row = pin.get('row', '')
        done = (row in sidx['memos']) or (row in items) or bool(act.get('collected'))
        return ('collected' if done else 'not_collected'), None

    if cat == 'strange_photo':
        row = pin.get('row', '')
        done = (row in items) or bool(act.get('collected'))
        return ('collected' if done else 'not_collected'), None

    if cat == 'glimpse':
        done = (guid in sidx['glimpses']) or bool(act.get('completed'))
        return ('collected' if done else 'not_collected'), None

    if cat == 'map_pickup':
        rows = pin.get('rows') or ([pin['row']] if pin.get('row') else [])
        done = (bool(rows) and all(r in items for r in rows)) or bool(act.get('collected'))
        return ('collected' if done else 'not_collected'), None

    if cat == 'weapon':
        row = pin.get('row', '')
        done = (row in items) or bool(act.get('collected') or act.get('completed'))
        return ('collected' if done else 'not_collected'), None

    if cat in ('key_item', 'ng_plus', 'puzzle'):
        row = pin.get('row')
        rewards = pin.get('rewards') or ()
        done = False
        if row and row in items:
            done = True
        if rewards and all(r in items for r in rewards):
            done = True
        if act.get('collected') or act.get('completed') or act.get('opened'):
            done = True
        for oid in oids:
            mo = m_objs.get(oid)
            if mo:
                if mo['type'] == 'Puzzle' and (mo['val'] % 10) == 2:
                    done = True
                elif mo['type'] in ('Collectable', 'DoorAttachment', 'Objective', 'HintSign') and mo['val'] >= 2:
                    done = True
        return ('collected' if done else 'not_collected'), None

    if cat in ('health', 'ammo'):
        if act.get('collected') or act.get('hidden'):
            return 'collected', None
        for oid in oids:
            mo = m_objs.get(oid)
            if mo and mo['type'] == 'Collectable' and mo['val'] >= 2:
                return 'collected', None
        if sidx['active_region'] and sidx['active_region'] == map_meta['region']:
            return 'not_collected', None
        return 'unknown', None

    if cat == 'note_focus':
        done = bool(act.get('completed')) or any(
            m_objs.get(oid, {}).get('val', 0) >= 2 for oid in oids
        )
        return ('collected' if done else 'unknown'), None

    if cat in ('breakable_wall', 'pushable'):
        done = bool(act.get('completed') or act.get('opened') or act.get('hidden')) or any(
            m_objs.get(oid, {}).get('val', 0) >= 3 for oid in oids
        )
        return ('collected' if done else 'unknown'), None

    return 'unknown', None


def format_pin(pin: dict[str, Any], map_meta: dict[str, Any], loc: dict[str, Any], lang: str,
               sidx: dict[str, Any] | None, manual_ids: set[str] | None) -> dict[str, Any]:
    lg = language(lang)
    items_l = loc['items_ru'] if lg == 'ru' else loc['items_en']
    items_en = loc['items_en']
    places_l = loc['places_ru'] if lg == 'ru' else loc['places_en']
    trs_l = loc['transcripts_ru'] if lg == 'ru' else loc['transcripts_en']
    trs_en = loc['transcripts_en']

    status, door_state = _evaluate_pin(pin, map_meta, sidx, manual_ids)
    cat = pin['cat']
    title = category(cat, lg)
    title_en = category(cat, 'en')
    subtitle = ''

    if pin.get('row'):
        row = pin['row']
        if pin.get('rows') and len(pin['rows']) > 1:
            names = [_human_row(r, items_l) for r in pin['rows']]
            title = names[0] + (f' (+{len(names) - 1})' if len(names) > 1 else '')
            subtitle = ', '.join(names)
        else:
            title = _human_row(row, items_l)
            title_en = _human_row(row, items_en)
            if pin.get('qty', 1) > 1 and cat in ('ammo', 'health'):
                title = f"{title} ×{pin['qty']}"
    elif cat in ('puzzle', 'ng_plus') and pin.get('cls_id'):
        title = puzzle_title(pin['cls_id'], lg)
        title_en = puzzle_title(pin['cls_id'], 'en')
    elif cat == 'glimpse':
        idx_num = pin['id']
        title = f"{category('glimpse', lg)}"
        title_en = 'Glimpse of the Past'
    elif cat == 'save_point':
        sp_row = pin.get('sp_row') or ''
        pair = places_l.get(sp_row)
        if pair and any(pair):
            title = pair[-1] or pair[0]
            subtitle = pair[0] if len(pair) > 1 and pair[0] != title else ''
        else:
            title = category('save_point', lg)
    elif cat == 'note_focus':
        tr_id = pin.get('tr_id') or ''
        raw_t = trs_l.get(tr_id) or ''
        first_line = raw_t.splitlines()[0].strip()[:64] if raw_t else ''
        title = first_line or category('note_focus', lg)

    # Dynamic position update for pushable carts if present in save
    px_xy = list(pin['px'])
    if cat == 'pushable' and sidx is not None:
        dyn_map = sidx['map_dynamic'].get(map_meta['enum_tag']) or {}
        for oid in (pin.get('oids') or ()):
            if oid in dyn_map:
                proj = sh2_memory.project_world_to_sheet(dyn_map[oid]['wx'], dyn_map[oid]['wy'], 0.0, map_meta)
                if proj['in_bounds']:
                    px_xy = [round(proj['px'], 1), round(proj['py'], 1)]
                break

    meta_notes = []
    if pin.get('box'):
        meta_notes.append(t('box_' + pin['box'], lg))
    if pin.get('subzone'):
        meta_notes.append(t('sub_' + pin['subzone'], lg))
    if subtitle:
        meta_notes.insert(0, subtitle)

    rewards_labels = [_human_row(r, items_l) for r in (pin.get('rewards') or ())]
    icon_row = (pin.get('rows') or [pin.get('row')])[0]
    tr_id = pin.get('tr_id')
    item_trs_ru = loc.get('item_transcripts_ru') or {}
    item_trs_en = loc.get('item_transcripts_en') or {}
    desc_l = (loc.get('desc_ru') if lg == 'ru' else loc.get('desc_en')) or {}
    transcript_ru = (loc.get('transcripts_ru') or {}).get(tr_id) if tr_id else None
    transcript_en = trs_en.get(tr_id) if tr_id else None
    if not transcript_ru and icon_row:
        transcript_ru = item_trs_ru.get(icon_row)
    if not transcript_en and icon_row:
        transcript_en = item_trs_en.get(icon_row)
    item_desc = desc_l.get(icon_row) if icon_row else None

    out: dict[str, Any] = {
        'id': pin['id'],
        'cat': cat,
        'category_label': category(cat, lg),
        'scored': bool(pin.get('scored')),
        'map': pin['map'],
        'px': px_xy,
        'title': title,
        'title_en': title_en,
        'status': status,
        'manual': bool(manual_ids and str(pin['id']) in manual_ids),
    }
    if meta_notes:
        out['note'] = ' · '.join(meta_notes)
    if item_desc:
        out['desc'] = item_desc
    icon = item_icon(icon_row)
    if icon:
        out['icon'] = icon
    if door_state:
        out['door_state'] = door_state
    if pin.get('codes'):
        out['codes'] = pin['codes']
    if rewards_labels:
        out['rewards'] = rewards_labels
        r_icons = [item_icon(r) for r in (pin.get('rewards') or ())]
        if any(r_icons):
            out['rewards_icons'] = r_icons
    if transcript_ru or transcript_en:
        out['transcript_ru'] = transcript_ru or transcript_en
        out['transcript_en'] = transcript_en or transcript_ru
    return out


def summarize_completion(formatted_pins: list[dict[str, Any]]) -> dict[str, Any]:
    total = collected = remaining = unknown = 0
    by_cat: dict[str, dict[str, Any]] = {}
    for p in formatted_pins:
        if not p.get('scored'):
            continue
        total += 1
        st = p['status']
        ck = p['cat']
        ce = by_cat.get(ck)
        if ce is None:
            ce = {'key': ck, 'label': p['category_label'], 'total': 0, 'collected': 0, 'remaining': 0, 'unknown': 0}
            by_cat[ck] = ce
        ce['total'] += 1
        if st == 'collected':
            collected += 1
            ce['collected'] += 1
        elif st == 'not_collected':
            remaining += 1
            ce['remaining'] += 1
        else:
            unknown += 1
            ce['unknown'] += 1
    pct = round((collected / total) * 100.0, 1) if total > 0 else 0.0
    return {
        'total': total,
        'collected': collected,
        'remaining': remaining,
        'unknown': unknown,
        'percent': pct,
        'by_category': list(by_cat.values()),
    }


def _resolve_james_marker_sprite(default_sprite: str, obj_type: str, val: int) -> tuple[str, bool]:
    """Replicate Base_MapWidget::ApplyObjectData sprite state machine."""
    if val <= 0:
        return default_sprite, False
    if obj_type == 'Door':
        if val in (1, 2):
            return 'Map_Marker_Locked_01_B_TB', True
        if val == 3:
            # Keep one-way / arrow / path sprite if the designer assigned a specific path arrow
            if 'OneWay' in default_sprite or 'Arrow' in default_sprite or 'Path' in default_sprite:
                return default_sprite, True
            return 'Map_Marker_Opened_01_B_TB', True
        if val == 4:
            return 'Map_Marker_Blocked_02_A', True
    elif obj_type == 'DoorAttachment':
        return ('Map_Marker_OpenedKey_01_A_TB' if val >= 2 else 'Map_Marker_LockedKey_01_A'), True
    elif obj_type == 'Collectable':
        return ('Map_Marker_HintAlarming_02_A_TB' if val >= 2 else 'Map_Marker_HintAlarming_01_A_TB'), True
    elif obj_type == 'HintSign':
        return ('Map_Marker_HintPuzzling_02_A_TB' if val >= 2 else 'Map_Marker_HintPuzzling_01_A_TB'), True
    elif obj_type == 'Puzzle':
        solved = (val % 10) == 2
        if solved and 'Map_Marker_Puzzle_' in default_sprite:
            return default_sprite.replace('Map_Marker_Puzzle_', 'Map_Marker_PuzzleCompleted_'), True
        return default_sprite, True
    elif obj_type == 'TextHint':
        return default_sprite, True
    return default_sprite, True


def get_map_overlays(slug: str, save_data: dict[str, Any] | None, lang: str = 'en') -> dict[str, Any]:
    """Return localized room/street labels + James's red-pen ObjectsContainer markers for slug."""
    lg = language(lang)
    ov_all = _load_overlays()
    ov = ov_all.get(slug) or {'labels': [], 'objects': []}
    maps_by_slug = sh2_memory.load_maps_by_slug()
    mmeta = maps_by_slug.get(slug)
    if not mmeta:
        return {'labels': [], 'james_marks': [], 'has_save_marks': False}

    labels_out = [
        {
            'px': lb['px'],
            'text': lb['ru'] if lg == 'ru' else lb['en'],
            'angle': lb.get('angle', 0.0),
            'size': lb.get('size', 15),
        }
        for lb in ov.get('labels', [])
        if (lb.get('ru') if lg == 'ru' else lb.get('en'))
    ]

    has_save = bool(save_data and save_data.get('ok'))
    save_map_objs = ((save_data or {}).get('map_objects') or {}).get(mmeta['enum_tag']) or {}
    dyn_objs = ((save_data or {}).get('map_dynamic') or {}).get(mmeta['enum_tag']) or {}

    marks_out = []
    for obj in ov.get('objects', []):
        oid = obj['oid']
        sprite = obj.get('sprite') or ''
        px = list(obj['px'])
        in_save = False
        crossed = False
        mo = save_map_objs.get(oid)
        if mo:
            sprite, vis = _resolve_james_marker_sprite(sprite, mo['type'], mo['val'])
            in_save = vis
            if mo['type'] == 'TextHint' and mo['val'] >= 2:
                crossed = True
        if oid in dyn_objs:
            proj = sh2_memory.project_world_to_sheet(dyn_objs[oid]['wx'], dyn_objs[oid]['wy'], 0.0, mmeta)
            if proj['in_bounds']:
                px = [round(proj['px'], 1), round(proj['py'], 1)]
                in_save = True

        note = (obj.get('note_ru') if lg == 'ru' else obj.get('note_en')) or ''
        marks_out.append({
            'oid': oid,
            'kind': obj['kind'],
            'sprite': sprite,
            'px': px,
            'size': obj['size'],
            'angle': obj.get('angle', 0.0),
            'flip': obj.get('flip', [False, False]),
            'note': note,
            'crossed': crossed,
            'in_save': in_save,
            'z': obj.get('z', 0),
        })

    return {
        'labels': labels_out,
        'james_marks': marks_out,
        'has_save_marks': has_save,
    }


def build_companion_state(selected_slug: str | None, save_data: dict[str, Any] | None,
                          lang: str = 'en', manual_ids: set[str] | None = None) -> dict[str, Any]:
    lg = language(lang)
    maps_meta = load_maps_meta()
    maps_by_slug = {m['slug']: m for m in maps_meta}
    all_pins = load_world_pins()
    loc = _load_loc()
    sidx = _prepare_save_index(save_data)

    current_slug = (sidx['active_slug'] if sidx and sidx.get('active_slug') in maps_by_slug else None) or 'city-east'
    sel_slug = selected_slug if selected_slug in maps_by_slug else current_slug
    sel_meta = maps_by_slug[sel_slug]

    pins_by_map: dict[str, list[dict[str, Any]]] = {m['slug']: [] for m in maps_meta}
    all_formatted: list[dict[str, Any]] = []

    for pin in all_pins:
        mmeta = maps_by_slug.get(pin['map'])
        if not mmeta:
            continue
        fp = format_pin(pin, mmeta, loc, lg, sidx, manual_ids)
        pins_by_map[pin['map']].append(fp)
        all_formatted.append(fp)

    global_comp = summarize_completion(all_formatted)
    items_owned = (sidx['items'] if sidx else {})

    # Per-map and per-region summaries
    maps_nav = []
    region_Buckets: dict[str, list[dict[str, Any]]] = {rk: [] for rk in REGION_ORDER}
    for m in maps_meta:
        mslug = m['slug']
        mpins = pins_by_map[mslug]
        mcomp = summarize_completion(mpins)
        has_paper_item = (m['dt_row'] in items_owned) if sidx else True
        m_entry = {
            'slug': mslug,
            'title': t(mslug, lg),
            'region': m['region'],
            'floor': m['floor'],
            'era': m['era'],
            'era_label': t('era_' + m['era'], lg),
            'twin': m['twin'],
            'rotation_deg': m['rotation_deg'],
            'cm_per_px': m['cm_per_px'],
            'is_current': bool(sidx and mslug == current_slug),
            'map_owned': has_paper_item,
            'texture_ready': (paths.MAPS_DIR / f'{mslug}.png').is_file(),
            'completion': mcomp,
        }
        maps_nav.append(m_entry)
        region_Buckets[m['region']].append(m_entry)

    regions_nav = []
    for rk in REGION_ORDER:
        rmaps = region_Buckets[rk]
        r_pins = [p for m in rmaps for p in pins_by_map[m['slug']]]
        rcomp = summarize_completion(r_pins)
        default_map = next((m['slug'] for m in rmaps if m['is_current']), rmaps[0]['slug'] if rmaps else 'city-east')
        regions_nav.append({
            'key': rk,
            'name': t(rk, lg),
            'is_current': any(m['is_current'] for m in rmaps),
            'default_map': default_map,
            'completion': {k: rcomp[k] for k in ('total', 'collected', 'remaining', 'unknown', 'percent')},
            'maps': rmaps,
        })

    # Saved James fallback projection on the selected map (or his saved map)
    saved_marker = None
    if sidx and save_data and save_data.get('player_pos'):
        sx, sy, sz = save_data['player_pos']
        syaw = float(save_data.get('player_yaw') or 0.0)
        save_map_meta = maps_by_slug.get(current_slug)
        if save_map_meta:
            sproj_home = sh2_memory.project_world_to_sheet(sx, sy, syaw, save_map_meta)
            sproj_sel = None
            if sel_slug == current_slug or sel_meta['region'] == save_map_meta['region'] or sel_meta.get('twin') == current_slug:
                cand_sel = sh2_memory.project_world_to_sheet(sx, sy, syaw, sel_meta)
                if cand_sel['in_bounds']:
                    sproj_sel = cand_sel
            saved_marker = {
                'map_slug': current_slug,
                'map_title': t(current_slug, lg),
                'home_projection': sproj_home,
                'selected_projection': sproj_sel,
            }

    return {
        'selected_map_slug': sel_slug,
        'selected_map': next(m for m in maps_nav if m['slug'] == sel_slug),
        'active_map_slug': current_slug,
        'active_map_title': t(current_slug, lg),
        'regions': regions_nav,
        'maps': maps_nav,
        'pins': pins_by_map[sel_slug],
        'overlays': get_map_overlays(sel_slug, save_data, lg),
        'map_completion': summarize_completion(pins_by_map[sel_slug]),
        'global_completion': global_comp,
        'saved_james': saved_marker,
    }


def search_world_pins(query: str, save_data: dict[str, Any] | None, lang: str = 'en',
                      manual_ids: set[str] | None = None, exclude_map: str | None = None,
                      limit: int = 48) -> list[dict[str, Any]]:
    """Search across all 1,518 pins on all 41 paper maps (titles, codes, rewards, notes, transcripts)."""
    q = ' '.join((query or '').strip().lower().split())
    if not q:
        return []
    lg = language(lang)
    maps_meta = load_maps_meta()
    maps_by_slug = {m['slug']: m for m in maps_meta}
    loc = _load_loc()
    sidx = _prepare_save_index(save_data)
    tokens = q.split()

    scored_hits: list[tuple[tuple[int, int, int, int], dict[str, Any]]] = []
    for pin in load_world_pins():
        mslug = pin['map']
        if exclude_map and mslug == exclude_map:
            continue
        mmeta = maps_by_slug.get(mslug)
        if not mmeta:
            continue
        fp = format_pin(pin, mmeta, loc, lg, sidx, manual_ids)
        map_title = t(mslug, lg)
        reg_name = t(mmeta['region'], lg)
        title_hay = f"{fp['title']} {fp.get('title_en', '')} {fp['category_label']}".lower()
        code_hay = json.dumps(fp.get('codes') or '', ensure_ascii=False).lower()
        extra_hay = ' '.join((
            fp.get('note') or '',
            ' '.join(fp.get('rewards') or ()),
            map_title,
            reg_name,
            fp.get('transcript_ru') or '',
            fp.get('transcript_en') or '',
        )).lower()
        full_hay = f'{title_hay} {code_hay} {extra_hay}'
        if not all(tok in full_hay for tok in tokens):
            continue
        in_title = 0 if q in title_hay else (1 if q in code_hay else 2)
        is_scored = 0 if (fp.get('scored') or fp['cat'] == 'save_point') else 1
        uncollected_first = 0 if fp['status'] != 'collected' else 1
        entry = {
            'id': fp['id'],
            'cat': fp['cat'],
            'category_label': fp['category_label'],
            'scored': fp['scored'],
            'map': mslug,
            'map_title': map_title,
            'region': mmeta['region'],
            'region_name': reg_name,
            'floor': mmeta['floor'],
            'era': mmeta['era'],
            'px': fp['px'],
            'title': fp['title'],
            'status': fp['status'],
        }
        if fp.get('note'):
            entry['note'] = fp['note']
        if fp.get('icon'):
            entry['icon'] = fp['icon']
        if fp.get('codes'):
            entry['has_code'] = True
        scored_hits.append(((in_title, is_scored, uncollected_first, fp['id']), entry))

    scored_hits.sort(key=lambda pair: pair[0])
    return [item for _, item in scored_hits[:max(1, min(limit, 100))]]


def merge_live_into_save(save_data: dict[str, Any] | None, live_data: dict[str, Any] | None) -> dict[str, Any]:
    """Overlay verified real-time process telemetry onto the latest save snapshot without mutating inputs."""
    base: dict[str, Any] = dict(save_data) if (save_data and save_data.get('ok')) else {'ok': False}
    if not live_data or not live_data.get('available'):
        return base

    if not base.get('ok'):
        base = {
            'ok': True,
            'slot_type': 'LiveSession',
            'items': {},
            'ammo_loaded': {},
            'equipment': {},
            'memos': [],
            'glimpses': [],
            'weapon_kills': {},
            'stats': {},
            'map_objects': {},
            'map_dynamic': {},
            'actor_states': {},
            'source': {'slot': ''},
        }

    if live_data.get('health') is not None:
        base['health'] = live_data['health']
    if live_data.get('active_map_slug'):
        base['active_map_slug'] = live_data['active_map_slug']
    if live_data.get('world_pos'):
        base['player_pos'] = list(live_data['world_pos'])
    if live_data.get('camera_yaw') is not None:
        base['player_yaw'] = live_data['camera_yaw']

    if isinstance(live_data.get('items'), dict):
        base['items'] = dict(live_data['items'])
    if isinstance(live_data.get('equipment'), dict):
        base['equipment'] = {**(base.get('equipment') or {}), **live_data['equipment']}
    if isinstance(live_data.get('ammo_loaded'), dict):
        base['ammo_loaded'] = {**(base.get('ammo_loaded') or {}), **live_data['ammo_loaded']}
    if live_data.get('last_used_weapon'):
        base['last_used_weapon'] = live_data['last_used_weapon']
    if isinstance(live_data.get('memos'), list) and live_data['memos']:
        base['memos'] = list(dict.fromkeys([*live_data['memos'], *(base.get('memos') or ())]))
    if isinstance(live_data.get('weapon_kills'), dict):
        base['weapon_kills'] = {**(base.get('weapon_kills') or {}), **live_data['weapon_kills']}
    if isinstance(live_data.get('stats'), dict):
        merged_stats = dict(base.get('stats') or {})
        for sk, sv in live_data['stats'].items():
            if sv is not None:
                merged_stats[sk] = sv
        base['stats'] = merged_stats
    if isinstance(live_data.get('map_objects'), dict):
        merged_mo = {k: dict(v) for k, v in (base.get('map_objects') or {}).items()}
        for mtag, dmap in live_data['map_objects'].items():
            if isinstance(dmap, dict):
                merged_mo[mtag] = {**(merged_mo.get(mtag) or {}), **dmap}
        base['map_objects'] = merged_mo
    return base


def build_dossier_state(
    save_data: dict[str, Any] | None,
    live_data: dict[str, Any] | None = None,
    lang: str = 'en',
    manual_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Assemble full Tablet & Companion Dossier (loadout, pocket, 26 photos, memos, puzzles, chapters, stats)."""
    lg = language(lang)
    is_live = bool(live_data and live_data.get('available'))
    merged = merge_live_into_save(save_data, live_data)
    has_data = bool(merged.get('ok')) or is_live

    loc = _load_loc()
    items_l = loc['items_ru'] if lg == 'ru' else loc['items_en']
    maps_meta = load_maps_meta()
    maps_by_slug = {m['slug']: m for m in maps_meta}
    map_rows_set = {str(m['dt_row']) for m in maps_meta if m.get('dt_row')}
    all_pins = load_world_pins()
    sidx = _prepare_save_index(merged)

    items = merged.get('items') or {}
    ammo_loaded = merged.get('ammo_loaded') or {}
    eq_map = merged.get('equipment') or {}
    weapon_kills = merged.get('weapon_kills') or {}
    last_weapon = merged.get('last_used_weapon')
    weapon_drawn = bool(live_data.get('weapon_drawn')) if is_live else False

    # Build row -> first world pin lookup so pocket items jump to their map location
    row_to_pin: dict[str, tuple[int, str]] = {}
    for pin in all_pins:
        pref_weight = 0 if pin['cat'] in ('key_item', 'puzzle', 'weapon', 'ng_plus') else 1
        for r in (([pin['row']] if pin.get('row') else []) + list(pin.get('rewards') or ())):
            if r and (r not in row_to_pin or pref_weight == 0):
                row_to_pin[r] = (pin['id'], pin['map'])

    # Equipment (Flashlight & Radio)
    has_flash = items.get('Flashlight', 0) > 0 or ('Flashlight' in eq_map)
    has_radio = items.get('Radio', 0) > 0 or ('Radio' in eq_map)
    equipment = {
        'radio': has_radio,
        'radio_on': bool(eq_map.get('Radio', True)) if has_radio else False,
        'radio_icon': item_icon('Radio'),
        'flashlight': has_flash,
        'flashlight_on': bool(eq_map.get('Flashlight', True)) if has_flash else False,
        'flashlight_icon': item_icon('Flashlight'),
    }

    # Weapons & Ammo
    weapons_detail = []
    owned_weapons = [wid for wid in WEAPON_ORDER if items.get(wid, 0) > 0]
    for wid in owned_weapons:
        ammo_row = WEAPON_AMMO_ROW.get(wid)
        is_ranged = ammo_row is not None
        loaded_n = int(ammo_loaded.get(wid, 0)) if is_ranged else None
        reserve_n = int(items.get(ammo_row, 0)) if is_ranged else None
        weapons_detail.append({
            'id': wid,
            'name': _human_row(wid, items_l),
            'kind': 'ranged' if is_ranged else 'melee',
            'equipped': wid == last_weapon,
            'drawn': bool(weapon_drawn and wid == last_weapon),
            'loaded': loaded_n,
            'reserve': reserve_n,
            'total_ammo': (loaded_n + reserve_n) if is_ranged else None,
            'kills': int(weapon_kills.get(wid, 0)),
            'icon': item_icon(wid),
        })

    weapon_kills_list = []
    for wid in WEAPON_ORDER:
        wk = int(weapon_kills.get(wid, 0))
        if wk > 0 or wid in owned_weapons:
            weapon_kills_list.append({
                'id': wid,
                'name': _human_row(wid, items_l),
                'kills': wk,
                'owned': wid in owned_weapons,
                'equipped': wid == last_weapon,
                'icon': item_icon(wid),
            })

    loose_ammo = []
    for wid, arow in WEAPON_AMMO_ROW.items():
        if wid not in owned_weapons and items.get(arow, 0) > 0:
            loose_ammo.append({
                'id': arow,
                'name': _human_row(arow, items_l),
                'qty': int(items[arow]),
                'icon': item_icon(arow),
            })

    # Pocket keys/puzzle items & Mementos
    memo_set = set(merged.get('memos') or ())
    skip_rows = (
        set(WEAPON_ORDER)
        | set(WEAPON_AMMO_ROW.values())
        | {'HealthDrink', 'Syringe', 'Radio', 'Flashlight'}
        | map_rows_set
        | memo_set
    )
    desc_l = (loc.get('desc_ru') if lg == 'ru' else loc.get('desc_en')) or {}
    item_trs_ru = loc.get('item_transcripts_ru') or {}
    item_trs_en = loc.get('item_transcripts_en') or {}
    active_clues = []
    mementos = []
    for row, qty in items.items():
        if qty <= 0 or row in skip_rows or row.startswith('Reflections_Photo_') or _NOTE_ROW_RE.search(row):
            continue
        nm = _human_row(row, items_l)
        pmatch = row_to_pin.get(row)
        tr_r = item_trs_ru.get(row)
        tr_e = item_trs_en.get(row)
        entry = {
            'id': row,
            'name': nm,
            'qty': int(qty),
            'memento': row in MEMENTO_ROWS,
            'icon': item_icon(row),
            'desc': desc_l.get(row) or None,
            'transcript_ru': tr_r or tr_e,
            'transcript_en': tr_e or tr_r,
            'pin_id': pmatch[0] if pmatch else None,
            'map': pmatch[1] if pmatch else None,
        }
        if row in MEMENTO_ROWS:
            mementos.append(entry)
        else:
            active_clues.append(entry)
    pocket = active_clues + mementos

    # Archive: 26 Photos, 72 Memos, 52 Puzzles, 8 Chapters
    photos_by_num: dict[int, dict[str, Any]] = {}
    memos_list: list[dict[str, Any]] = []
    puzzles_list: list[dict[str, Any]] = []
    chapter_acc: dict[str, dict[str, int]] = {
        rk: {'photos_got': 0, 'photos_total': 0, 'memos_got': 0, 'memos_total': 0,
             'glimpses_got': 0, 'glimpses_total': 0, 'puzzles_got': 0, 'puzzles_total': 0}
        for rk in REGION_ORDER
    }
    pins_by_region: dict[str, list[dict[str, Any]]] = {rk: [] for rk in REGION_ORDER}

    for pin in all_pins:
        mmeta = maps_by_slug.get(pin['map'])
        if not mmeta:
            continue
        rk = mmeta['region']
        fp = format_pin(pin, mmeta, loc, lg, sidx, manual_ids)
        pins_by_region[rk].append(fp)
        is_got = fp['status'] == 'collected'
        map_title = t(pin['map'], lg)
        reg_name = t(rk, lg)
        ca = chapter_acc[rk]

        if pin['cat'] == 'strange_photo':
            ca['photos_total'] += 1
            if is_got:
                ca['photos_got'] += 1
            row = pin.get('row') or ''
            try:
                num = int(row.removeprefix('Reflections_Photo_'))
            except ValueError:
                num = len(photos_by_num) + 1
            photos_by_num[num] = {
                'num': num,
                'id': row or f'Reflections_Photo_{num}',
                'title': fp['title'],
                'collected': is_got,
                'map': pin['map'],
                'map_title': map_title,
                'region': rk,
                'region_name': reg_name,
                'pin_id': pin['id'],
                'px': fp['px'],
                'icon': fp.get('icon') or item_icon(row),
                'desc': fp.get('desc') or desc_l.get(row) or None,
                'transcript_ru': fp.get('transcript_ru') or item_trs_ru.get(row),
                'transcript_en': fp.get('transcript_en') or item_trs_en.get(row),
            }
        elif pin['cat'] == 'memo':
            ca['memos_total'] += 1
            if is_got:
                ca['memos_got'] += 1
            memos_list.append({
                'id': pin['id'],
                'pin_id': pin['id'],
                'row': pin.get('row') or '',
                'title': fp['title'],
                'collected': is_got,
                'map': pin['map'],
                'map_title': map_title,
                'region': rk,
                'region_name': reg_name,
                'floor': mmeta['floor'],
                'px': fp['px'],
                'icon': fp.get('icon'),
                'desc': fp.get('desc'),
                'transcript_ru': fp.get('transcript_ru'),
                'transcript_en': fp.get('transcript_en'),
            })
        elif pin['cat'] == 'glimpse':
            ca['glimpses_total'] += 1
            if is_got:
                ca['glimpses_got'] += 1
        elif pin['cat'] == 'puzzle':
            ca['puzzles_total'] += 1
            if is_got:
                ca['puzzles_got'] += 1
            p_entry = {
                'id': pin['id'],
                'pin_id': pin['id'],
                'title': fp['title'],
                'status': fp['status'],
                'map': pin['map'],
                'map_title': map_title,
                'region': rk,
                'region_name': reg_name,
                'floor': mmeta['floor'],
                'px': fp['px'],
                'codes': fp.get('codes'),
                'note': fp.get('note'),
                'rewards': fp.get('rewards'),
                'rewards_icons': fp.get('rewards_icons'),
                'icon': fp.get('icon'),
            }
            puzzles_list.append(p_entry)

    photos_ordered = [photos_by_num[n] for n in sorted(photos_by_num)]
    memos_list.sort(key=lambda m: (_REGION_RANK.get(m['region'], 99), m['id']))
    puzzles_list.sort(key=lambda p: (_REGION_RANK.get(p['region'], 99), p['id']))

    active_slug = merged.get('active_map_slug')
    live_slug = live_data.get('active_map_slug') if is_live else None
    chapters = []
    for rk in REGION_ORDER:
        rmaps = [m for m in maps_meta if m['region'] == rk]
        rcomp = summarize_completion(pins_by_region[rk])
        ca = chapter_acc[rk]
        def_map = next((m['slug'] for m in rmaps if m['slug'] == (live_slug or active_slug)), rmaps[0]['slug'])
        chapters.append({
            'key': rk,
            'name': t(rk, lg),
            'is_current': any(m['slug'] == active_slug for m in rmaps) if active_slug else False,
            'is_live': any(m['slug'] == live_slug for m in rmaps) if live_slug else False,
            'default_map': def_map,
            'completion': {k: rcomp[k] for k in ('total', 'collected', 'remaining', 'percent')},
            **ca,
        })

    return {
        'is_live': is_live,
        'has_data': has_data,
        'health': merged.get('health'),
        'health_state': live_data.get('health_state') if is_live else None,
        'drinks': int(items.get('HealthDrink', 0)) if has_data else 0,
        'drinks_icon': item_icon('HealthDrink'),
        'syringes': int(items.get('Syringe', 0)) if has_data else 0,
        'syringes_icon': item_icon('Syringe'),
        'equipment': equipment,
        'weapons': weapons_detail,
        'weapon_kills': weapon_kills_list,
        'loose_ammo': loose_ammo,
        'pocket': pocket,
        'puzzle_difficulty_id': merged.get('puzzle_difficulty_id'),
        'photos': {
            'got': sum(1 for ph in photos_ordered if ph['collected']),
            'total': len(photos_ordered) or 26,
            'list': photos_ordered,
        },
        'memos': {
            'got': sum(1 for mm in memos_list if mm['collected']),
            'total': len(memos_list),
            'list': memos_list,
        },
        'glimpses': {
            'got': sum(c['glimpses_got'] for c in chapters),
            'total': sum(c['glimpses_total'] for c in chapters) or 26,
        },
        'puzzles': puzzles_list,
        'stats': dict(merged.get('stats') or {}),
        'chapters': chapters,
    }
