(function () {
  'use strict';

  var i18n = window.SH2I18n;
  var tr = i18n.t;

  function svg(body, filled) {
    return '<svg class="sh2-svg" viewBox="0 0 24 24" aria-hidden="true" ' +
      (filled ? 'fill="currentColor" stroke="none"' :
        'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"') +
      '>' + body + '</svg>';
  }

  var ICONS = {
    strange_photo: svg('<rect x="3.5" y="4" width="17" height="16" rx="1.5"/><path d="M3.5 15.5h17"/><circle cx="9" cy="9.5" r="1.6"/><path d="M7 15.5l4-4 3 2.5 2.5-2 3 3.5"/>'),
    memo: svg('<path d="M6 3.5h9l4 4V20.5H6z"/><path d="M15 3.5v4h4"/><path d="M9 11h6M9 14.5h6M9 17.5h4"/>'),
    glimpse: svg('<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.8"/><path d="M12 3v2M12 19v2"/>'),
    puzzle: svg('<rect x="5" y="10.5" width="14" height="10" rx="1.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/><circle cx="12" cy="15.5" r="1.5"/>'),
    key_item: svg('<circle cx="8" cy="12" r="4"/><path d="M12 12h9M18 12v3M21 12v2.5"/>'),
    weapon: svg('<path d="M3 10h13l3 3h2v3h-4l-2 4h-3l1.5-4H8l-2 4H3l2-6H3z"/>'),
    map_pickup: svg('<path d="M3.5 6l5.5-2 6 2 5.5-2v14l-5.5 2-6-2-5.5 2z"/><path d="M9 4v14M15 6v14"/>'),
    ng_plus: svg('<path d="M12 2.5l2.8 5.8 6.4.9-4.6 4.5 1.1 6.3L12 17l-5.7 3 1.1-6.3-4.6-4.5 6.4-.9z"/>'),
    save_point: svg('<rect x="5" y="5" width="14" height="14" rx="1"/>', true),
    note_focus: svg('<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.8v.2"/>'),
    health: svg('<path d="M9.5 4h5v3l2 2.5V20h-9V9.5L9.5 7z"/><path d="M12 11.5v5M9.5 14h5"/>'),
    ammo: svg('<path d="M7 19V9l2-4 2 4v10zM13 19V9l2-4 2 4v10z"/><path d="M6 19h12"/>'),
    breakable_wall: svg('<rect x="3.5" y="4.5" width="17" height="15"/><path d="M3.5 9.5h17M3.5 14.5h17M10 4.5l2 5-3 5 3 5"/>'),
    pushable: svg('<rect x="4" y="7" width="13" height="8" rx="1"/><path d="M17 9h3l1 4h-4"/><circle cx="7.5" cy="17.5" r="2"/><circle cx="14.5" cy="17.5" r="2"/>'),
    door: svg('<path d="M6.5 20.5V4.5h11v16"/><path d="M4 20.5h16M14.5 12.5v.2"/>'),
    menu: svg('<path d="M4 7h16M4 12h16M4 17h16"/>'),
    close: svg('<path d="M6 6l12 12M18 6L6 18"/>'),
    plus: svg('<path d="M12 5v14M5 12h14"/>'),
    minus: svg('<path d="M5 12h14"/>'),
    target: svg('<circle cx="12" cy="12" r="6.5"/><path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4"/>'),
    fit: svg('<path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5"/>'),
    chev: svg('<path d="M6 9.5l6 6 6-6"/>'),
    fullscreen: svg('<path d="M3.5 8.5v-5h5M15.5 3.5h5v5M20.5 15.5v5h-5M8.5 20.5h-5v-5"/>'),
    sun: svg('<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2.5 12h2M19.5 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
    trail: svg('<path d="M4 18c3-4 4-9 8-9s4 5 8-3"/><circle cx="20" cy="6" r="1.7" fill="currentColor"/>'),
    radio: svg('<rect x="6" y="8" width="12" height="12" rx="1.5"/><path d="M9 8V3.5M9.5 13h5M9.5 16.5h2.5"/><circle cx="15" cy="16.5" r="1.2"/>'),
    flashlight: svg('<path d="M9 3h6v4l-1.5 2.5V20a1.5 1.5 0 0 1-3 0V9.5L9 7z"/><path d="M9 7h6"/>'),
    loadout: svg('<path d="M4 12h3.5l2-5 3.5 10 2.5-6.5 1.5 1.5H20"/>'),
    archive: svg('<rect x="3.5" y="4.5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17M10 13.5h4"/>'),
    codes: svg('<rect x="5" y="10" width="14" height="10" rx="1.5"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><path d="M9.5 15h5"/>')
  };

  var CAT_COLOR = {
    strange_photo: '#e3a6c8',
    memo: '#e8dfc4',
    glimpse: '#8ec4e8',
    puzzle: '#e5be6d',
    key_item: '#d8a657',
    weapon: '#ea6f5c',
    map_pickup: '#7fd1ae',
    ng_plus: '#c79bf2',
    save_point: '#f04238',
    note_focus: '#a7b4ad',
    health: '#76c78c',
    ammo: '#c7b387',
    breakable_wall: '#cc845e',
    pushable: '#8fb4c9',
    door: '#8c948f'
  };

  var CAT_ORDER = [
    'strange_photo', 'memo', 'glimpse', 'puzzle', 'key_item', 'weapon', 'map_pickup', 'ng_plus',
    'save_point', 'note_focus', 'health', 'ammo', 'breakable_wall', 'pushable', 'door'
  ];

  var S = {
    payload: null,
    activeTab: 'map',        // 'map' | 'loadout' | 'archive' | 'codes'
    archiveSub: 'photos',    // 'photos' | 'memos' | 'chapters'
    archiveFilter: 'all',    // 'all' | 'got' | 'missing'
    selectedMemoId: null,
    archiveMemoQuery: '',
    inspect: null,           // { kind: 'photo'|'pocket'|'memo'|'pin', id: string|number }
    codesQuery: '',
    codesFilter: 'all',
    revealedCodes: {},
    mapSlug: null,
    renderedSlug: null,
    mode: 'scored',
    redPen: null,
    showLabels: true,
    antiSpoiler: false,
    category: null,
    query: '',
    globalHits: [],
    globalQuery: '',
    selectedPinId: null,
    codeRevealedFor: null,
    trLang: null,
    follow: true,
    showTrail: true,
    trailPoints: [],
    sidebarCollapsed: window.innerWidth < 960,
    modeMenuOpen: false,
    fetching: false,
    lastLiveSlug: null,
    streamState: 'idle',
    wakeLock: null,
    wakeActive: false
  };

  try {
    var prefs = JSON.parse(localStorage.getItem('sh2CompanionPrefs') || '{}');
    if (prefs.mode) S.mode = prefs.mode;
    if (prefs.redPen) S.redPen = prefs.redPen;
    if (typeof prefs.showLabels === 'boolean') S.showLabels = prefs.showLabels;
    if (typeof prefs.antiSpoiler === 'boolean') S.antiSpoiler = prefs.antiSpoiler;
    if (typeof prefs.follow === 'boolean') S.follow = prefs.follow;
    if (typeof prefs.showTrail === 'boolean') S.showTrail = prefs.showTrail;
    if (typeof prefs.sidebarCollapsed === 'boolean') S.sidebarCollapsed = prefs.sidebarCollapsed;
  } catch (e) {}

  var hashSlug = (window.location.hash.match(/map=([a-z0-9-]+)/) || [])[1];
  if (hashSlug) S.mapSlug = hashSlug;

  function savePrefs() {
    try {
      localStorage.setItem('sh2CompanionPrefs', JSON.stringify({
        mode: S.mode, redPen: S.redPen, showLabels: S.showLabels,
        antiSpoiler: S.antiSpoiler, follow: S.follow, showTrail: S.showTrail,
        sidebarCollapsed: S.sidebarCollapsed
      }));
    } catch (e) {}
  }

  function getManualSet() {
    try {
      var arr = JSON.parse(localStorage.getItem('sh2ManualPins') || '[]');
      return new Set(Array.isArray(arr) ? arr.map(String) : []);
    } catch (e) {
      return new Set();
    }
  }

  function toggleManualPin(pinId) {
    var set = getManualSet();
    var k = String(pinId);
    if (set.has(k)) set.delete(k); else set.add(k);
    try {
      localStorage.setItem('sh2ManualPins', JSON.stringify(Array.from(set)));
    } catch (e) {}
    fetchState(true);
  }

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function itemImgHtml(iconStem, cls, alt) {
    if (!iconStem) return '';
    return '<img class="' + cls + '" src="/sh2-items/' + encodeURIComponent(iconStem) + '.png" alt="' + esc(alt || '') + '" loading="lazy" onerror="this.hidden=true">';
  }

  function vitalMeta(hp) {
    if (hp == null || !Number.isFinite(Number(hp))) {
      return { cls: 'unknown', label: tr('cond_unknown'), tone: 'muted' };
    }
    var v = Number(hp);
    if (v >= 75) return { cls: 'fine', label: tr('cond_fine'), tone: 'good' };
    if (v >= 45) return { cls: 'caution', label: tr('cond_caution'), tone: 'warn' };
    if (v > 20) return { cls: 'danger', label: tr('cond_danger'), tone: 'danger' };
    return { cls: 'critical', label: tr('cond_critical'), tone: 'crit' };
  }

  function ecgSvgHtml(wide) {
    var w = wide ? 160 : 66;
    var h = wide ? 48 : 26;
    var d = wide
      ? 'M0,26 L28,26 L36,20 L44,31 L52,7 L60,41 L68,26 L98,26 L112,21 L126,26 L160,26'
      : 'M2,16 H14 L19,11 L23,19 L29,4 L35,23 L41,10 L46,16 H64';
    return '<svg class="' + (wide ? 'sh2-ecg-svg' : 'sh2-mv-ecg') + '" viewBox="0 0 ' + w + ' ' + h + '" aria-hidden="true">' +
      '<path class="sh2-ecg-bg" d="' + d + '"/>' +
      '<path class="sh2-ecg-line" d="' + d + '"/>' +
    '</svg>';
  }

  function healthTone(hp) {
    return vitalMeta(hp).tone;
  }

  function diffKeyFromId(id) {
    return id === 0 ? 'easy' : (id === 1 ? 'normal' : (id === 2 ? 'hard' : null));
  }

  // Build static DOM skeleton with safe flex top stack + flexible workspace
  var root = document.getElementById('sh2App');
  root.setAttribute('data-tab', 'map');
  root.setAttribute('data-stream', 'idle');
  root.innerHTML =
    '<div id="sh2MapCanvas"></div>' +
    '<div class="sh2-vignette"></div>' +
    '<div class="sh2-top-stack">' +
      '<header class="sh2-plate sh2-topbar" id="sh2Topbar"></header>' +
      '<nav class="sh2-plate sh2-regbar" id="sh2Regbar" aria-label="Areas"></nav>' +
    '</div>' +
    '<div class="sh2-workspace">' +
      '<div class="sh2-scrim" id="sh2Scrim" hidden></div>' +
      '<nav class="sh2-plate sh2-floorbar" id="sh2Floorbar" aria-label="Floors"></nav>' +
      '<button type="button" class="sh2-plate sh2-btn sh2-sidebar-toggle" id="sh2SidebarOpenBtn" hidden>' +
        '<span class="sh2-ico">' + ICONS.menu + '</span><span id="sh2SidebarOpenLbl">HUD</span>' +
      '</button>' +
      '<button type="button" class="sh2-plate sh2-map-vitals" id="sh2MapVitals" hidden></button>' +
      '<aside class="sh2-plate sh2-sidebar" id="sh2Sidebar">' +
        '<div class="sh2-sec" id="sh2StatusCard"></div>' +
        '<div class="sh2-sec sh2-toggles" id="sh2TogglesSec"></div>' +
        '<div class="sh2-sec"><div class="sh2-cats-wrap" id="sh2CatsWrap"></div></div>' +
        '<div class="sh2-sec"><input type="search" class="sh2-search-input" id="sh2SearchInput"></div>' +
        '<div class="sh2-pin-list" id="sh2PinList"></div>' +
        '<div class="sh2-footer-hint" id="sh2FooterHint"></div>' +
      '</aside>' +
      '<aside class="sh2-plate sh2-drawer" id="sh2Drawer" hidden></aside>' +
      '<div class="sh2-plate sh2-unowned-banner" id="sh2UnownedBanner" hidden></div>' +
      '<div class="sh2-plate sh2-controls" id="sh2Controls"></div>' +
      '<section class="sh2-plate sh2-dossier-stage" id="sh2DossierStage" hidden></section>' +
    '</div>' +
    '<div class="sh2-modal-backdrop" id="sh2Modal" hidden></div>';

  var mapView = new window.SH2MapEngine.PaperMapView('sh2MapCanvas');
  var jamesEntry = null;
  var jamesDom = { wrap: null, cone: null, conePath: null, arrow: null };
  var jamesAnim = { curPx: null, curPy: null, curAng: null, tgtPx: null, tgtPy: null, tgtAng: null, fov: 70, isLive: false, rafId: 0 };

  mapView.on('dragstart', function () {
    if (S.follow) {
      S.follow = false;
      savePrefs();
      renderControls();
    }
  });
  mapView.on('mapclick', function () {
    if (S.modeMenuOpen) {
      S.modeMenuOpen = false;
      renderTopbar();
    }
  });

  var searchTimer = 0;
  document.getElementById('sh2SearchInput').addEventListener('input', function (e) {
    S.query = e.target.value || '';
    renderPinsAndSidebarList();
    clearTimeout(searchTimer);
    var trimmed = S.query.trim();
    if (trimmed.length < 2) {
      S.globalHits = [];
      S.globalQuery = '';
      renderGlobalHits();
      return;
    }
    searchTimer = setTimeout(function () {
      runGlobalSearch(trimmed);
    }, 180);
  });

  function runGlobalSearch(qtext) {
    var manual = Array.from(getManualSet()).join(',');
    var qs = '?q=' + encodeURIComponent(qtext) + '&lang=' + encodeURIComponent(i18n.lang) + '&limit=24';
    if (S.renderedSlug) qs += '&exclude=' + encodeURIComponent(S.renderedSlug);
    if (manual) qs += '&marked=' + encodeURIComponent(manual);
    S.globalQuery = qtext;
    fetch('/api/search' + qs, { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (S.query.trim() !== qtext) return;
        S.globalHits = (res && res.ok && Array.isArray(res.results)) ? res.results : [];
        renderGlobalHits();
      })
      .catch(function () {});
  }

  document.getElementById('sh2SidebarOpenBtn').addEventListener('click', function () {
    S.sidebarCollapsed = false;
    savePrefs();
    syncSidebarVisibility();
  });
  document.getElementById('sh2Scrim').addEventListener('click', function () {
    S.sidebarCollapsed = true;
    savePrefs();
    syncSidebarVisibility();
  });
  document.getElementById('sh2MapVitals').addEventListener('click', function () {
    setActiveTab('loadout');
  });

  function syncSidebarVisibility() {
    var onMap = S.activeTab === 'map';
    var sb = document.getElementById('sh2Sidebar');
    var btn = document.getElementById('sh2SidebarOpenBtn');
    var scrim = document.getElementById('sh2Scrim');
    var vitals = document.getElementById('sh2MapVitals');
    var narrow = window.innerWidth <= 960;
    sb.classList.toggle('is-collapsed', !onMap || S.sidebarCollapsed);
    btn.hidden = !onMap || !S.sidebarCollapsed;
    scrim.hidden = !onMap || !narrow || S.sidebarCollapsed;
    var hasVitals = Boolean(S.payload && ((S.payload.save && S.payload.save.ok) || (S.payload.live_telemetry && S.payload.live_telemetry.available)));
    vitals.hidden = !onMap || !hasVitals;
    var lbl = document.getElementById('sh2SidebarOpenLbl');
    if (lbl) lbl.textContent = tr('filters_btn');
  }

  function setActiveTab(tab) {
    if (S.activeTab === tab) return;
    S.activeTab = tab;
    root.setAttribute('data-tab', tab);
    document.getElementById('sh2Regbar').hidden = tab !== 'map';
    document.getElementById('sh2Floorbar').hidden = tab !== 'map';
    document.getElementById('sh2Controls').hidden = tab !== 'map';
    document.getElementById('sh2DossierStage').hidden = tab === 'map';
    if (tab !== 'map') {
      document.getElementById('sh2Drawer').hidden = true;
      document.getElementById('sh2UnownedBanner').hidden = true;
    } else {
      renderFloorbar();
      renderDrawer();
      setTimeout(function () { mapView.draw(); }, 20);
    }
    syncSidebarVisibility();
    renderTopbar();
    if (tab !== 'map') renderDossierStage();
  }

  function jumpToMapAndPin(slug, pinId, revealCode) {
    if (revealCode && pinId != null) S.codeRevealedFor = pinId;
    S.activeTab = 'map';
    root.setAttribute('data-tab', 'map');
    document.getElementById('sh2Regbar').hidden = false;
    document.getElementById('sh2Floorbar').hidden = false;
    document.getElementById('sh2Controls').hidden = false;
    document.getElementById('sh2DossierStage').hidden = true;
    syncSidebarVisibility();
    if (!slug) {
      if (pinId != null) {
        S.selectedPinId = pinId;
        renderPinsAndSidebarList();
        renderDrawer();
      }
      renderTopbar();
      return;
    }
    if (S.renderedSlug === slug && S.payload) {
      S.selectedPinId = pinId || null;
      var p = (S.payload.world.pins || []).find(function (x) { return x.id === pinId; });
      if (p) mapView.flyTo(p.px, Math.max(mapView.zoom, 0.35), 260);
      renderTopbar();
      renderPinsAndSidebarList();
      renderDrawer();
      return;
    }
    S.follow = false;
    savePrefs();
    S.mapSlug = slug;
    S.selectedPinId = pinId || null;
    window.history.replaceState(null, '', '#map=' + encodeURIComponent(slug));
    fetchState(false, function (data) {
      if (pinId != null && data && data.world) {
        S.selectedPinId = pinId;
        var p2 = (data.world.pins || []).find(function (x) { return x.id === pinId; });
        if (p2) mapView.flyTo(p2.px, Math.max(mapView.zoom, 0.35), 240);
        renderPinsAndSidebarList();
        renderDrawer();
      }
    });
  }

  function effectiveRedPenMode() {
    if (S.redPen) return S.redPen;
    var hasSave = S.payload && S.payload.save && S.payload.save.ok;
    return hasSave ? 'save' : 'all';
  }

  function pinVisibleInMode(p) {
    if (S.category && p.cat !== S.category) return false;
    if (S.query) {
      var q = S.query.toLowerCase();
      var hay = (p.title + ' ' + (p.title_en || '') + ' ' + (p.note || '') + ' ' +
        JSON.stringify(p.codes || '') + ' ' + (p.transcript_ru || '')).toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }
    if (S.category) return true;
    if (S.mode === 'remaining') {
      if (p.cat === 'save_point') return true;
      return p.scored && p.status !== 'collected';
    }
    if (S.mode === 'scored') {
      return p.scored || p.cat === 'save_point';
    }
    if (S.mode === 'loot') {
      return p.scored || p.cat === 'save_point' || p.cat === 'health' || p.cat === 'ammo' || p.cat === 'note_focus';
    }
    return true;
  }

  function selectMap(slug, keepViewport, isManual) {
    if (!slug) return;
    if (isManual !== false && S.payload && S.payload.live_telemetry && S.payload.live_telemetry.available) {
      if (slug !== S.payload.live_telemetry.active_map_slug) {
        S.follow = false;
        savePrefs();
      }
    }
    S.mapSlug = slug;
    S.selectedPinId = null;
    window.history.replaceState(null, '', '#map=' + encodeURIComponent(slug));
    fetchState(keepViewport);
  }

  window.addEventListener('hashchange', function () {
    var hs = (window.location.hash.match(/map=([a-z0-9-]+)/) || [])[1];
    if (hs && hs !== S.mapSlug) {
      selectMap(hs, false, true);
    }
  });

  function toggleFullscreen() {
    if (document.fullscreenElement) {
      if (document.exitFullscreen) document.exitFullscreen().catch(function () {});
    } else if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(function () {});
    }
  }
  document.addEventListener('fullscreenchange', function () { renderTopbar(); });

  function toggleWakeLock() {
    if (S.wakeLock) {
      try { S.wakeLock.release(); } catch (e) {}
      S.wakeLock = null;
      S.wakeActive = false;
      renderTopbar();
      return;
    }
    if (navigator.wakeLock && navigator.wakeLock.request) {
      navigator.wakeLock.request('screen').then(function (sentinel) {
        S.wakeLock = sentinel;
        S.wakeActive = true;
        sentinel.addEventListener('release', function () {
          S.wakeLock = null;
          S.wakeActive = false;
          renderTopbar();
        });
        renderTopbar();
      }).catch(function () {});
    }
  }

  function renderTopbar() {
    if (!S.payload) return;
    var w = S.payload.world;
    var gc = w.global_completion;
    var selMap = w.selected_map;
    var lt = S.payload.live_telemetry;
    var sv = S.payload.save;
    var hp = (lt && lt.available && lt.health != null) ? lt.health : (sv && sv.health);
    var modes = [
      { k: 'remaining', lbl: tr('mode_remaining'), hint: tr('mode_remaining_hint') },
      { k: 'scored', lbl: tr('mode_scored'), hint: tr('mode_scored_hint') },
      { k: 'loot', lbl: tr('mode_loot'), hint: tr('mode_loot_hint') },
      { k: 'all', lbl: tr('mode_all'), hint: tr('mode_all_hint') }
    ];
    var curMode = modes.find(function (m) { return m.k === S.mode; }) || modes[1];

    var mainTabs = [
      { k: 'map', ico: ICONS.map_pickup, lbl: tr('tab_map') },
      { k: 'loadout', ico: ICONS.loadout, lbl: tr('tab_loadout') },
      { k: 'archive', ico: ICONS.archive, lbl: tr('tab_archive') },
      { k: 'codes', ico: ICONS.codes, lbl: tr('tab_codes') }
    ].map(function (tb) {
      return '<button type="button" class="sh2-main-tab' + (S.activeTab === tb.k ? ' is-active' : '') + '" data-maintab="' + tb.k + '">' +
        '<span class="sh2-ico">' + tb.ico + '</span><span>' + esc(tb.lbl) + '</span></button>';
    }).join('');

    var menuHtml = (S.modeMenuOpen && S.activeTab === 'map') ? (
      '<div class="sh2-dropdown-panel">' +
      modes.map(function (m) {
        return '<button type="button" class="sh2-mode-opt' + (m.k === S.mode ? ' is-active' : '') + '" data-mode="' + m.k + '">' +
          '<strong>' + esc(m.lbl) + '</strong><span>' + esc(m.hint) + '</span></button>';
      }).join('') +
      '</div>'
    ) : '';

    var isLive = Boolean(lt && lt.available);
    var streamCls = isLive ? 'is-live' : (S.streamState === 'open' ? 'is-ready' : '');
    var streamTxt = isLive ? tr('stream_live') : (sv && sv.ok ? (hp != null ? Math.round(hp) + '%' : tr('save_active')) : tr('stream_wait'));
    var wakeSupported = Boolean(navigator.wakeLock && navigator.wakeLock.request);
    var isFs = Boolean(document.fullscreenElement);

    var tbEl = document.getElementById('sh2Topbar');
    tbEl.innerHTML =
      '<div class="sh2-global-box">' +
        '<div class="sh2-kicker">' + esc(tr('global_kicker')) + '</div>' +
        '<div class="sh2-global-num">' + gc.collected + ' / ' + gc.total + '<em>' + gc.percent + '%</em></div>' +
        '<span class="sh2-bar"><i style="width:' + gc.percent + '%"></i></span>' +
      '</div>' +
      '<div class="sh2-main-tabs" role="tablist">' + mainTabs + '</div>' +
      '<div class="sh2-top-actions">' +
        '<span class="sh2-stream-badge ' + streamCls + '" id="sh2StreamBadge"><i class="sh2-pulse"></i><span id="sh2StreamTxt">' + esc(streamTxt) + '</span></span>' +
        (S.activeTab === 'map' ? (
          '<div class="sh2-dropdown">' +
            '<button type="button" class="sh2-btn" id="sh2ModeBtn">' +
              '<span>' + esc(curMode.lbl) + '</span><span class="sh2-ico">' + ICONS.chev + '</span>' +
            '</button>' + menuHtml +
          '</div>'
        ) : '') +
        (document.fullscreenEnabled !== false ? (
          '<button type="button" class="sh2-btn sh2-ico-btn' + (isFs ? ' is-active' : '') + '" id="sh2FsBtn" title="' + esc(tr('btn_fullscreen')) + '">' +
            '<span class="sh2-ico">' + ICONS.fullscreen + '</span></button>'
        ) : '') +
        (wakeSupported ? (
          '<button type="button" class="sh2-btn sh2-ico-btn' + (S.wakeActive ? ' is-active' : '') + '" id="sh2WakeBtn" title="' + esc(tr('btn_wakelock')) + '">' +
            '<span class="sh2-ico">' + ICONS.sun + '</span></button>'
        ) : '') +
        '<button type="button" class="sh2-btn" id="sh2LangBtn">' + (i18n.lang === 'ru' ? 'RU' : 'EN') + '</button>' +
      '</div>';

    tbEl.querySelectorAll('[data-maintab]').forEach(function (b) {
      b.addEventListener('click', function () { setActiveTab(b.getAttribute('data-maintab')); });
    });
    var modeBtn = document.getElementById('sh2ModeBtn');
    if (modeBtn) {
      modeBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        S.modeMenuOpen = !S.modeMenuOpen;
        renderTopbar();
      });
    }
    tbEl.querySelectorAll('[data-mode]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.mode = b.getAttribute('data-mode');
        S.modeMenuOpen = false;
        savePrefs();
        renderTopbar();
        renderPinsAndSidebarList();
      });
    });
    var fsBtn = document.getElementById('sh2FsBtn');
    if (fsBtn) fsBtn.addEventListener('click', toggleFullscreen);
    var wkBtn = document.getElementById('sh2WakeBtn');
    if (wkBtn) wkBtn.addEventListener('click', toggleWakeLock);
    document.getElementById('sh2LangBtn').addEventListener('click', function () {
      i18n.setLang(i18n.lang === 'ru' ? 'en' : 'ru');
      fetchState(true);
    });

    // Separate Area/Region strip cleanly below topbar on Map view
    var regBar = document.getElementById('sh2Regbar');
    regBar.hidden = S.activeTab !== 'map';
    regBar.innerHTML = w.regions.map(function (r) {
      var active = r.key === selMap.region;
      var here = r.is_live || r.is_current;
      return '<button type="button" class="sh2-reg-tab' + (active ? ' is-active' : '') + '" data-reg="' + esc(r.default_map) + '">' +
        '<span class="sh2-reg-title">' + (here ? '<i class="sh2-red-sq"></i>' : '') + esc(r.name) + '</span>' +
        '<span class="sh2-reg-meta"><span class="sh2-bar"><i style="width:' + r.completion.percent + '%"></i></span>' +
        '<span class="sh2-reg-pct">' + Math.round(r.completion.percent) + '%</span></span>' +
      '</button>';
    }).join('');
    regBar.querySelectorAll('[data-reg]').forEach(function (b) {
      b.addEventListener('click', function () { selectMap(b.getAttribute('data-reg'), false); });
    });
  }

  function renderMapVitals() {
    if (!S.payload) return;
    var el = document.getElementById('sh2MapVitals');
    var dos = S.payload.dossier || {};
    var sv = S.payload.save || {};
    var lt = S.payload.live_telemetry || {};
    var hp = (lt.available && lt.health != null) ? lt.health : (dos.health != null ? dos.health : sv.health);
    var vm = vitalMeta(hp);
    var isLive = Boolean(lt.available);
    var drinks = sv.supplies ? sv.supplies.drinks : (dos.drinks != null ? dos.drinks : 0);
    var syringes = sv.supplies ? sv.supplies.syringes : (dos.syringes != null ? dos.syringes : 0);

    el.className = 'sh2-plate sh2-map-vitals is-' + vm.cls + (isLive ? ' is-live' : '');
    el.innerHTML =
      '<div class="sh2-mv-top">' +
        (isLive ? '<i class="sh2-pulse sh2-mv-dot"></i>' : '') +
        '<span>' + esc(tr('cond_kicker')) + ' · <b id="sh2MapVitalsState">' + esc(vm.label) + '</b></span>' +
      '</div>' +
      '<div class="sh2-mv-main">' +
        '<div class="sh2-mv-ecg-wrap">' + ecgSvgHtml(false) + '</div>' +
        '<span class="sh2-vitals-hp is-' + vm.tone + '" id="sh2MapVitalsHp">' +
          (hp != null ? Math.round(hp) + '%' : '—') +
        '</span>' +
        '<span class="sh2-vitals-sep"></span>' +
        '<span class="sh2-mv-item' + (!drinks ? ' is-zero' : '') + '">' +
          (dos.drinks_icon ? itemImgHtml(dos.drinks_icon, 'sh2-mv-ico', tr('drinks_lbl')) : '') +
          '×' + drinks + '</span>' +
        '<span class="sh2-mv-item' + (!syringes ? ' is-zero' : '') + '">' +
          (dos.syringes_icon ? itemImgHtml(dos.syringes_icon, 'sh2-mv-ico', tr('syringes_lbl')) : '') +
          '×' + syringes + '</span>' +
      '</div>';
  }

  function renderFloorbar() {
    if (!S.payload) return;
    var w = S.payload.world;
    var sel = w.selected_map;
    var reg = w.regions.find(function (r) { return r.key === sel.region; });
    var fb = document.getElementById('sh2Floorbar');
    if (!reg || S.activeTab !== 'map') { fb.innerHTML = ''; return; }

    var btns = reg.maps.map(function (m) {
      var active = m.slug === sel.slug;
      var here = m.is_live || m.is_current;
      var unowned = S.antiSpoiler && !m.map_owned;
      var rem = m.completion.remaining;
      return '<button type="button" class="sh2-floor-btn' + (active ? ' is-active' : '') + (unowned ? ' is-unowned' : '') +
        '" data-floor="' + esc(m.slug) + '" title="' + esc(m.title) + '">' +
        (here ? '<i class="sh2-red-sq"></i>' : '') +
        '<span>' + esc(m.floor) + '</span>' +
        (rem > 0 ? '<span class="sh2-floor-rem">' + rem + '</span>' : '') +
      '</button>';
    }).join('');

    var twinBtn = '';
    if (sel.twin) {
      var twinLbl = sel.era === 'burnt' ? tr('btn_twin_clean') :
        (sel.region === 'hotel' ? tr('btn_twin_burnt') :
          (sel.era === 'otherworld' ? tr('btn_twin_fog') : tr('btn_twin_ow')));
      twinBtn = '<button type="button" class="sh2-twin-btn" id="sh2TwinBtn">' + esc(twinLbl) + '</button>';
    }

    fb.innerHTML = btns + twinBtn;
    fb.querySelectorAll('[data-floor]').forEach(function (b) {
      b.addEventListener('click', function () {
        var nextSlug = b.getAttribute('data-floor');
        var sameBuilding = sel.region !== 'south-vale' && sel.region !== 'labyrinth';
        selectMap(nextSlug, sameBuilding);
      });
    });
    var tb = document.getElementById('sh2TwinBtn');
    if (tb) {
      tb.addEventListener('click', function () { selectMap(sel.twin, true); });
    }

    var banner = document.getElementById('sh2UnownedBanner');
    if (S.activeTab === 'map' && S.antiSpoiler && !sel.map_owned) {
      banner.textContent = tr('unowned_map_warn');
      banner.hidden = false;
    } else {
      banner.hidden = true;
    }
  }

  function renderSidebarHeaderAndToggles() {
    if (!S.payload) return;
    var sv = S.payload.save;
    var lt = S.payload.live_telemetry;
    var w = S.payload.world;

    var badgeCls = lt && lt.available ? 'is-live' : (sv && sv.ok ? 'is-save' : '');
    var badgeTxt = lt && lt.available ? tr('live_active') : (sv && sv.ok ? tr('save_active') : tr('no_save_badge'));
    var placeTxt = (lt && lt.available && w.live_map_title) ? w.live_map_title :
      ((sv && sv.place) ? sv.place : w.selected_map.title);

    var subParts = [];
    if (sv && sv.ok) {
      if (sv.play_time) subParts.push(tr('playtime_lbl') + ': ' + sv.play_time);
      if (sv.puzzle_difficulty) subParts.push(sv.puzzle_difficulty);
      if (sv.source && sv.source.slot) subParts.push(sv.source.slot);
    } else if (lt && !lt.available && lt.reason) {
      subParts.push(lt.reason);
    }

    var supHtml = '';
    if (sv && sv.ok && sv.supplies) {
      var sp = sv.supplies;
      var hp = (lt && lt.available && lt.health != null) ? lt.health : sv.health;
      var hpTxt = hp != null ? Math.round(hp) + '%' : '—';
      var cells = [
        [hpTxt, tr('health_lbl'), 'sh2SideHp'],
        [sp.drinks + ' / ' + sp.syringes, tr('drinks_lbl')],
        [sp.handgun_ammo, tr('hg_ammo_lbl')],
        [sp.shotgun_ammo + ' / ' + sp.rifle_ammo, tr('sg_ammo_lbl')],
        [sp.memos_count, tr('memos_lbl')],
        [sp.photos_count + '/26', tr('photos_lbl')],
        [sp.glimpses_count + '/26', tr('glimpses_lbl')],
        [(sv.stats && sv.stats.kills != null) ? sv.stats.kills : '—', tr('kills_lbl')]
      ];
      supHtml = '<div class="sh2-supplies-grid">' + cells.map(function (c) {
        return '<div class="sh2-sup-cell"><span class="sh2-sup-val"' + (c[2] ? ' id="' + c[2] + '"' : '') + '>' + esc(c[0]) +
          '</span><span class="sh2-sup-lbl">' + esc(c[1]) + '</span></div>';
      }).join('') + '</div>';
    }

    document.getElementById('sh2StatusCard').innerHTML =
      '<div class="sh2-status-row">' +
        '<span class="sh2-live-pill ' + badgeCls + '"><i class="sh2-pulse"></i>' + esc(badgeTxt) + '</span>' +
        '<button type="button" class="sh2-btn" id="sh2CollapseBtn" style="height:28px;padding:0 8px" title="Tab">' +
          '<span class="sh2-ico" style="width:13px;height:13px">' + ICONS.close + '</span>' +
        '</button>' +
      '</div>' +
      '<div class="sh2-place-line">' + esc(placeTxt) + '</div>' +
      (subParts.length ? '<div class="sh2-submeta">' + esc(subParts.join(' · ')) + '</div>' : '') +
      supHtml;

    document.getElementById('sh2CollapseBtn').addEventListener('click', function () {
      S.sidebarCollapsed = true;
      savePrefs();
      syncSidebarVisibility();
    });

    var rp = effectiveRedPenMode();
    var tg = document.getElementById('sh2TogglesSec');
    tg.innerHTML =
      '<div class="sh2-toggle-row"><span>' + esc(tr('redpen_lbl')) + '</span>' +
        '<div class="sh2-seg">' +
          '<button type="button" data-rp="save" class="' + (rp === 'save' ? 'is-active' : '') + '">' + esc(tr('redpen_save')) + '</button>' +
          '<button type="button" data-rp="all" class="' + (rp === 'all' ? 'is-active' : '') + '">' + esc(tr('redpen_all')) + '</button>' +
          '<button type="button" data-rp="off" class="' + (rp === 'off' ? 'is-active' : '') + '">' + esc(tr('redpen_off')) + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="sh2-toggle-row"><span>' + esc(tr('labels_lbl')) + '</span>' +
        '<div class="sh2-seg">' +
          '<button type="button" data-lbl="1" class="' + (S.showLabels ? 'is-active' : '') + '">' + esc(tr('on')) + '</button>' +
          '<button type="button" data-lbl="0" class="' + (!S.showLabels ? 'is-active' : '') + '">' + esc(tr('off')) + '</button>' +
        '</div>' +
      '</div>' +
      '<div class="sh2-toggle-row"><span>' + esc(tr('spoiler_lbl')) + '</span>' +
        '<div class="sh2-seg">' +
          '<button type="button" data-sp="1" class="' + (S.antiSpoiler ? 'is-active' : '') + '">' + esc(tr('on')) + '</button>' +
          '<button type="button" data-sp="0" class="' + (!S.antiSpoiler ? 'is-active' : '') + '">' + esc(tr('off')) + '</button>' +
        '</div>' +
      '</div>';

    tg.querySelectorAll('[data-rp]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.redPen = b.getAttribute('data-rp');
        savePrefs();
        renderSidebarHeaderAndToggles();
        mapView.setRedPenMarks(S.payload.world.overlays.james_marks, effectiveRedPenMode());
      });
    });
    tg.querySelectorAll('[data-lbl]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.showLabels = b.getAttribute('data-lbl') === '1';
        savePrefs();
        renderSidebarHeaderAndToggles();
        mapView.setLabels(S.payload.world.overlays.labels, S.showLabels);
      });
    });
    tg.querySelectorAll('[data-sp]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.antiSpoiler = b.getAttribute('data-sp') === '1';
        S.codeRevealedFor = null;
        savePrefs();
        renderFloorbar();
        renderSidebarHeaderAndToggles();
        renderDrawer();
        if (S.activeTab !== 'map') renderDossierStage();
      });
    });

    document.getElementById('sh2SearchInput').placeholder = tr('search_ph');
    document.getElementById('sh2FooterHint').textContent = tr('hotkeys_hint');
  }

  function renderGlobalHits() {
    var listEl = document.getElementById('sh2PinList');
    var oldBox = document.getElementById('sh2GlobalResults');
    if (oldBox) oldBox.remove();
    if (!S.globalHits.length || !S.query.trim()) return;

    var box = document.createElement('div');
    box.id = 'sh2GlobalResults';
    box.className = 'sh2-global-results';
    box.innerHTML =
      '<div class="sh2-kicker" style="padding:8px 8px 4px">' + esc(tr('global_search_hdr')) + ' (' + S.globalHits.length + ')</div>' +
      S.globalHits.map(function (h) {
        var col = CAT_COLOR[h.cat] || '#d8b46a';
        return '<button type="button" class="sh2-pin-row sh2-global-hit' + (h.status === 'collected' ? ' is-done' : '') +
          '" data-gmap="' + esc(h.map) + '" data-gpid="' + h.id + '">' +
          '<span class="sh2-pin-row-ico" style="color:' + col + '">' + (ICONS[h.cat] || ICONS.note_focus) + '</span>' +
          '<span class="sh2-pin-row-body">' +
            '<span class="sh2-pin-row-title">' + esc(h.title) + '</span>' +
            '<span class="sh2-pin-row-sub">' + esc(h.region_name + ' · ' + h.floor + (h.has_code ? ' · #' : '')) + '</span>' +
          '</span>' +
        '</button>';
      }).join('');

    listEl.appendChild(box);
    box.querySelectorAll('[data-gmap]').forEach(function (b) {
      b.addEventListener('click', function () {
        var gm = b.getAttribute('data-gmap');
        var gpid = Number(b.getAttribute('data-gpid'));
        jumpToMapAndPin(gm, gpid, false);
      });
    });
  }

  function renderPinsAndSidebarList() {
    if (!S.payload) return;
    var w = S.payload.world;
    var pins = w.pins || [];

    var byCat = {};
    pins.forEach(function (p) {
      if (!byCat[p.cat]) byCat[p.cat] = { total: 0, done: 0, label: p.category_label };
      byCat[p.cat].total += 1;
      if (p.status === 'collected') byCat[p.cat].done += 1;
    });

    var chipsHtml = '<button type="button" class="sh2-cat-chip' + (!S.category ? ' is-active' : '') + '" data-cat="">' +
      esc(tr('all_cats')) + '</button>';
    CAT_ORDER.forEach(function (ck) {
      if (!byCat[ck]) return;
      var c = byCat[ck];
      var col = CAT_COLOR[ck] || '#d8b46a';
      chipsHtml += '<button type="button" class="sh2-cat-chip' + (S.category === ck ? ' is-active' : '') + '" data-cat="' + ck + '">' +
        '<span class="sh2-chip-ico" style="color:' + col + '">' + (ICONS[ck] || ICONS.note_focus) + '</span>' +
        '<span>' + esc(c.label) + '</span><em>' + c.done + '/' + c.total + '</em></button>';
    });
    var cw = document.getElementById('sh2CatsWrap');
    cw.innerHTML = chipsHtml;
    cw.querySelectorAll('[data-cat]').forEach(function (b) {
      b.addEventListener('click', function () {
        var val = b.getAttribute('data-cat') || null;
        S.category = S.category === val ? null : val;
        renderPinsAndSidebarList();
      });
    });

    mapView.clearMarkers();
    jamesEntry = null;
    jamesDom = { wrap: null, cone: null, conePath: null, arrow: null };

    var visiblePins = pins.filter(pinVisibleInMode);
    visiblePins.forEach(function (p) {
      var el = document.createElement('button');
      el.type = 'button';
      var isLoot = p.cat === 'ammo' || p.cat === 'health' || p.cat === 'door';
      el.className = 'sh2-map-pin' +
        (p.status === 'collected' ? ' is-done' : '') +
        (p.cat === 'save_point' ? ' is-savepoint' : '') +
        (isLoot ? ' is-loot' : '') +
        (S.selectedPinId === p.id ? ' is-selected' : '');
      el.style.setProperty('--pin-color', CAT_COLOR[p.cat] || '#d8b46a');
      el.innerHTML = ICONS[p.cat] || ICONS.note_focus;
      el.title = p.title + (p.note ? ' (' + p.note + ')' : '');
      el.addEventListener('click', function (ev) {
        ev.stopPropagation();
        S.selectedPinId = p.id;
        renderPinsAndSidebarList();
        renderDrawer();
      });
      var zOff = p.cat === 'save_point' ? 40 : (p.scored ? 30 : 10);
      if (S.selectedPinId === p.id) zOff = 120;
      mapView.addMarker(p.px, el, zOff);
    });

    renderJamesMarker();

    var listEl = document.getElementById('sh2PinList');
    if (!visiblePins.length) {
      listEl.innerHTML = '<div style="padding:18px 10px;text-align:center;font-size:12px;color:var(--sh2-muted)">' + esc(tr('empty_list')) + '</div>';
    } else {
      listEl.innerHTML = visiblePins.map(function (p) {
        var col = CAT_COLOR[p.cat] || '#d8b46a';
        var sub = p.note || p.category_label;
        return '<button type="button" class="sh2-pin-row' +
          (p.status === 'collected' ? ' is-done' : '') +
          (S.selectedPinId === p.id ? ' is-selected' : '') + '" data-pid="' + p.id + '">' +
          '<span class="sh2-pin-row-ico" style="color:' + col + '">' + (ICONS[p.cat] || ICONS.note_focus) + '</span>' +
          '<span class="sh2-pin-row-body">' +
            '<span class="sh2-pin-row-title">' + esc(p.title) + '</span>' +
            '<span class="sh2-pin-row-sub">' + esc(sub) + '</span>' +
          '</span>' +
        '</button>';
      }).join('');

      listEl.querySelectorAll('[data-pid]').forEach(function (b) {
        b.addEventListener('click', function () {
          var pid = Number(b.getAttribute('data-pid'));
          var target = pins.find(function (x) { return x.id === pid; });
          if (!target) return;
          S.selectedPinId = pid;
          if (window.innerWidth <= 960) {
            S.sidebarCollapsed = true;
            syncSidebarVisibility();
          }
          mapView.flyTo(target.px, Math.max(mapView.zoom, 0.35), 260);
          renderPinsAndSidebarList();
          renderDrawer();
        });
      });
    }
    renderGlobalHits();
  }

  function conePathForFov(fov) {
    var f = Number.isFinite(fov) ? Math.max(30, Math.min(120, fov)) : 70;
    var halfRad = (f * 0.42 * Math.PI) / 180;
    var r = 40;
    var x1 = (42 - Math.sin(halfRad) * r).toFixed(1);
    var y1 = (42 - Math.cos(halfRad) * r).toFixed(1);
    var x2 = (42 + Math.sin(halfRad) * r).toFixed(1);
    return 'M42 42 L' + x1 + ' ' + y1 + ' A' + r + ' ' + r + ' 0 0 1 ' + x2 + ' ' + y1 + ' Z';
  }

  function ensureJamesMarker(px, py, angleDeg, fov, isLive) {
    if (jamesEntry && jamesDom.wrap) {
      jamesDom.wrap.classList.toggle('is-saved-only', !isLive);
      jamesDom.wrap.classList.add('sh2-pin-marker', 'sh2-james-wrap');
      jamesDom.wrap.title = isLive ? tr('james_live_tip') : tr('james_save_tip');
      jamesDom.cone.style.transform = 'rotate(' + angleDeg.toFixed(2) + 'deg)';
      jamesDom.arrow.style.transform = 'rotate(' + angleDeg.toFixed(2) + 'deg)';
      jamesDom.conePath.setAttribute('d', conePathForFov(fov));
      jamesDom.conePath.setAttribute('fill', isLive ? 'rgba(240,66,56,0.28)' : 'rgba(216,180,106,0.22)');
      jamesDom.arrow.querySelector('path').setAttribute('fill', isLive ? '#f54238' : '#e0b96c');
      mapView.updateMarkerPos(jamesEntry, [px, py]);
      return;
    }

    var wrap = document.createElement('div');
    wrap.className = 'sh2-james-wrap' + (isLive ? '' : ' is-saved-only');
    wrap.title = isLive ? tr('james_live_tip') : tr('james_save_tip');

    var coneColor = isLive ? 'rgba(240,66,56,0.28)' : 'rgba(216,180,106,0.22)';
    var arrowFill = isLive ? '#f54238' : '#e0b96c';
    wrap.innerHTML =
      '<svg class="sh2-james-cone" viewBox="0 0 84 84" style="transform:rotate(' + angleDeg + 'deg)">' +
        '<path d="' + conePathForFov(fov) + '" fill="' + coneColor + '"/>' +
      '</svg>' +
      '<svg class="sh2-james-arrow" viewBox="0 0 28 28" style="transform:rotate(' + angleDeg + 'deg)">' +
        '<path d="M14 2 L24 24 L14 19 L4 24 Z" fill="' + arrowFill + '" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/>' +
      '</svg>';

    jamesDom.wrap = wrap;
    jamesDom.cone = wrap.querySelector('.sh2-james-cone');
    jamesDom.conePath = jamesDom.cone.querySelector('path');
    jamesDom.arrow = wrap.querySelector('.sh2-james-arrow');
    jamesEntry = mapView.addMarker([px, py], wrap, 150);
  }

  function stepJamesAnimation() {
    jamesAnim.rafId = 0;
    if (jamesAnim.tgtPx == null || jamesAnim.curPx == null) return;
    var dx = jamesAnim.tgtPx - jamesAnim.curPx;
    var dy = jamesAnim.tgtPy - jamesAnim.curPy;
    var da = ((jamesAnim.tgtAng - jamesAnim.curAng + 540) % 360) - 180;
    if (Math.hypot(dx, dy) < 0.15 && Math.abs(da) < 0.25) {
      jamesAnim.curPx = jamesAnim.tgtPx;
      jamesAnim.curPy = jamesAnim.tgtPy;
      jamesAnim.curAng = jamesAnim.tgtAng;
    } else {
      jamesAnim.curPx += dx * 0.34;
      jamesAnim.curPy += dy * 0.34;
      jamesAnim.curAng = (jamesAnim.curAng + da * 0.34 + 360) % 360;
      jamesAnim.rafId = requestAnimationFrame(stepJamesAnimation);
    }
    ensureJamesMarker(jamesAnim.curPx, jamesAnim.curPy, jamesAnim.curAng, jamesAnim.fov, jamesAnim.isLive);
    if (S.follow && S.activeTab === 'map' && !mapView.drag && !mapView._flyRaf) {
      mapView.setView([jamesAnim.curPx, jamesAnim.curPy]);
    }
  }

  function setJamesTarget(px, py, angleDeg, fov, isLive, snap) {
    jamesAnim.tgtPx = Number(px);
    jamesAnim.tgtPy = Number(py);
    jamesAnim.tgtAng = Number(angleDeg || 0);
    jamesAnim.fov = Number(fov || 70);
    jamesAnim.isLive = Boolean(isLive);

    if (snap || jamesAnim.curPx == null || Math.hypot(jamesAnim.tgtPx - jamesAnim.curPx, jamesAnim.tgtPy - jamesAnim.curPy) > 220) {
      if (jamesAnim.rafId) { cancelAnimationFrame(jamesAnim.rafId); jamesAnim.rafId = 0; }
      jamesAnim.curPx = jamesAnim.tgtPx;
      jamesAnim.curPy = jamesAnim.tgtPy;
      jamesAnim.curAng = jamesAnim.tgtAng;
      ensureJamesMarker(jamesAnim.curPx, jamesAnim.curPy, jamesAnim.curAng, jamesAnim.fov, jamesAnim.isLive);
    } else if (!jamesAnim.rafId) {
      jamesAnim.rafId = requestAnimationFrame(stepJamesAnimation);
    }

    if (isLive) {
      var last = S.trailPoints.length ? S.trailPoints[S.trailPoints.length - 1] : null;
      if (!last || Math.hypot(px - last[0], py - last[1]) > 6) {
        S.trailPoints.push([Number(px), Number(py)]);
        if (S.trailPoints.length > 180) S.trailPoints.shift();
        mapView.setTrail(S.trailPoints, S.showTrail);
      }
    }
  }

  function renderJamesMarker() {
    if (!S.payload) return;
    var lt = S.payload.live_telemetry;
    var w = S.payload.world;
    var proj = null;
    var isLive = false;
    var fov = 70;

    if (lt && lt.available && lt.selected_projection && lt.selected_projection.in_bounds) {
      proj = lt.selected_projection;
      isLive = true;
      fov = lt.fov || 70;
    } else if (w.saved_james && w.saved_james.selected_projection && w.saved_james.selected_projection.in_bounds) {
      proj = w.saved_james.selected_projection;
      isLive = false;
    }
    if (!proj) return;
    setJamesTarget(proj.px, proj.py, proj.angle_deg, fov, isLive, true);
  }

  function renderDrawer() {
    var dr = document.getElementById('sh2Drawer');
    if (S.activeTab !== 'map' || !S.payload || S.selectedPinId == null) {
      dr.hidden = true;
      return;
    }
    var p = (S.payload.world.pins || []).find(function (x) { return x.id === S.selectedPinId; });
    if (!p) {
      dr.hidden = true;
      return;
    }
    dr.hidden = false;

    var stTxt = p.status === 'collected' ? tr('status_collected') :
      (p.status === 'not_collected' ? tr('status_remaining') : tr('status_unknown'));
    var stCls = p.status === 'collected' ? 'is-done' : (p.status === 'not_collected' ? 'is-rem' : '');
    var activeDiffKey = diffKeyFromId(S.payload.save && S.payload.save.puzzle_difficulty_id);

    var doorPill = '';
    if (p.door_state) {
      var dMap = { locked: tr('door_locked'), opened: tr('door_opened'), blocked: tr('door_blocked') };
      if (dMap[p.door_state]) doorPill = '<span class="sh2-pill">' + esc(dMap[p.door_state]) + '</span>';
    }

    var codeHtml = '';
    if (p.codes) {
      var hiddenBySpoiler = S.antiSpoiler && S.codeRevealedFor !== p.id;
      if (hiddenBySpoiler) {
        codeHtml = '<div class="sh2-code-card">' +
          '<div class="sh2-kicker">' + esc(tr('code_header')) + '</div>' +
          '<button type="button" class="sh2-btn" id="sh2RevealCodeBtn" style="margin-top:8px;width:100%">' + esc(tr('reveal_code')) + '</button>' +
        '</div>';
      } else {
        var rows = [];
        if (p.codes.all) rows.push(['all', tr('diff_all'), p.codes.all]);
        if (p.codes.easy) rows.push(['easy', tr('diff_easy'), p.codes.easy]);
        if (p.codes.normal) rows.push(['normal', tr('diff_normal'), p.codes.normal]);
        if (p.codes.hard) rows.push(['hard', tr('diff_hard'), p.codes.hard]);
        codeHtml = '<div class="sh2-code-card">' +
          '<div class="sh2-kicker">' + esc(tr('code_header')) + '</div>' +
          '<div class="sh2-code-grid">' + rows.map(function (r) {
            var match = activeDiffKey && r[0] === activeDiffKey;
            return '<div class="sh2-code-row' + (match ? ' is-active-diff' : '') + '">' +
              '<span>' + esc(r[1]) + (match ? '<em class="sh2-diff-here">' + esc(tr('active_diff_badge')) + '</em>' : '') + '</span>' +
              '<span class="sh2-code-val">' + esc(r[2]) + '</span>' +
            '</div>';
          }).join('') + '</div>' +
        '</div>';
      }
    }

    var rewardsHtml = '';
    if (p.rewards && p.rewards.length) {
      var rIcons = p.rewards_icons || [];
      rewardsHtml = '<div><div class="sh2-kicker" style="margin-bottom:5px">' + esc(tr('rewards_header')) + '</div>' +
        '<div class="sh2-rewards-list">' + p.rewards.map(function (rw, idx) {
          return '<span class="sh2-reward-pill">' +
            (rIcons[idx] ? itemImgHtml(rIcons[idx], 'sh2-reward-thumb', rw) : '') +
            '<span>' + esc(rw) + '</span></span>';
        }).join('') + '</div></div>';
    }

    var trHtml = '';
    if (p.transcript_ru || p.transcript_en) {
      var curTr = S.trLang || i18n.lang;
      var txt = curTr === 'ru' ? (p.transcript_ru || p.transcript_en) : (p.transcript_en || p.transcript_ru);
      trHtml = '<div>' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">' +
          '<span class="sh2-kicker">' + esc(tr('transcript_header')) + '</span>' +
          '<div class="sh2-seg">' +
            '<button type="button" data-trl="ru" class="' + (curTr === 'ru' ? 'is-active' : '') + '">RU</button>' +
            '<button type="button" data-trl="en" class="' + (curTr === 'en' ? 'is-active' : '') + '">EN</button>' +
          '</div>' +
        '</div>' +
        '<div class="sh2-transcript-box">' + esc(txt) + '</div>' +
      '</div>';
    }

    var saveConfirmed = p.status === 'collected' && !p.manual;
    var actionBtn = saveConfirmed ?
      '<div style="font-size:12px;color:var(--sh2-green)">✓ ' + esc(tr('save_confirmed')) + '</div>' :
      '<button type="button" class="sh2-btn" id="sh2ManualBtn" style="width:100%">' +
        esc(p.manual ? tr('unmark_done') : tr('mark_done')) + '</button>';
    var canInspectPin = Boolean(p.icon || p.transcript_ru || p.transcript_en || p.desc);

    dr.innerHTML =
      '<div class="sh2-drawer-head">' +
        (p.icon ? '<button type="button" class="sh2-drawer-art is-clickable" id="sh2DrawerArtBtn" title="' + esc(tr('inspect_btn')) + '">' + itemImgHtml(p.icon, 'sh2-drawer-img', p.title) + '</button>' : '') +
        '<div style="flex:1;min-width:0">' +
          '<div class="sh2-kicker">' + esc(p.category_label) + '</div>' +
          '<h3 class="sh2-drawer-title">' + esc(p.title) + '</h3>' +
          (p.title_en && p.title_en !== p.title ? '<div class="sh2-drawer-sub">' + esc(p.title_en) + '</div>' : '') +
        '</div>' +
        '<button type="button" class="sh2-btn" id="sh2CloseDrawerBtn" style="height:30px;padding:0 9px;flex:none">' +
          '<span class="sh2-ico">' + ICONS.close + '</span>' +
        '</button>' +
      '</div>' +
      '<div class="sh2-drawer-body">' +
        '<div class="sh2-badge-line"><span class="sh2-pill ' + stCls + '">' + esc(stTxt) + '</span>' + doorPill +
          (canInspectPin ? '<button type="button" class="sh2-btn sh2-inspect-pill-btn" id="sh2DrawerInspectBtn">' + esc(tr('inspect_btn')) + '</button>' : '') +
        '</div>' +
        (p.desc ? '<div class="sh2-drawer-desc">' + esc(p.desc) + '</div>' : '') +
        (p.note ? '<div style="font-size:12.5px;color:var(--sh2-muted)">' + esc(p.note) + '</div>' : '') +
        codeHtml + rewardsHtml + trHtml + actionBtn +
      '</div>';

    document.getElementById('sh2CloseDrawerBtn').addEventListener('click', function () {
      S.selectedPinId = null;
      renderPinsAndSidebarList();
      renderDrawer();
    });
    var artBtn = document.getElementById('sh2DrawerArtBtn');
    if (artBtn) {
      artBtn.addEventListener('click', function () {
        S.inspect = { kind: 'pin', id: p.id };
        renderInspectModal();
      });
    }
    var inspBtn = document.getElementById('sh2DrawerInspectBtn');
    if (inspBtn) {
      inspBtn.addEventListener('click', function () {
        S.inspect = { kind: 'pin', id: p.id };
        renderInspectModal();
      });
    }
    var revBtn = document.getElementById('sh2RevealCodeBtn');
    if (revBtn) {
      revBtn.addEventListener('click', function () {
        S.codeRevealedFor = p.id;
        renderDrawer();
      });
    }
    dr.querySelectorAll('[data-trl]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.trLang = b.getAttribute('data-trl');
        renderDrawer();
      });
    });
    var mBtn = document.getElementById('sh2ManualBtn');
    if (mBtn) {
      mBtn.addEventListener('click', function () { toggleManualPin(p.id); });
    }
  }

  function fitCurrentSheet() {
    var leftPad = (S.sidebarCollapsed || window.innerWidth < 960) ? 24 : 348;
    mapView.fitSheet(leftPad, 24, 24, 72);
  }

  function jumpToJames() {
    if (!S.payload) return;
    var lt = S.payload.live_telemetry;
    var w = S.payload.world;
    if (lt && lt.available && lt.active_map_slug) {
      if (w.selected_map_slug !== lt.active_map_slug) {
        S.follow = true;
        savePrefs();
        selectMap(lt.active_map_slug, false);
        return;
      }
      if (lt.selected_projection) {
        mapView.flyTo([lt.selected_projection.px, lt.selected_projection.py], Math.max(mapView.zoom, 0.25), 260);
      }
      return;
    }
    if (w.saved_james) {
      if (w.selected_map_slug !== w.saved_james.map_slug) {
        selectMap(w.saved_james.map_slug, false);
        return;
      }
      if (w.saved_james.selected_projection) {
        mapView.flyTo([w.saved_james.selected_projection.px, w.saved_james.selected_projection.py], Math.max(mapView.zoom, 0.25), 260);
      }
    }
  }

  function renderControls() {
    var c = document.getElementById('sh2Controls');
    c.innerHTML =
      '<button type="button" class="sh2-btn" id="sh2ZoomIn" title="+"><span class="sh2-ico">' + ICONS.plus + '</span></button>' +
      '<button type="button" class="sh2-btn" id="sh2ZoomOut" title="-"><span class="sh2-ico">' + ICONS.minus + '</span></button>' +
      '<button type="button" class="sh2-btn" id="sh2JumpJames"><span class="sh2-ico">' + ICONS.target + '</span><span class="sh2-ctl-lbl">' + esc(tr('btn_to_james')) + '</span></button>' +
      '<button type="button" class="sh2-btn' + (S.follow ? ' is-active' : '') + '" id="sh2FollowBtn"><span>' + esc(tr('btn_follow')) + '</span></button>' +
      '<button type="button" class="sh2-btn' + (S.showTrail ? ' is-active' : '') + '" id="sh2TrailBtn" title="' + esc(tr('btn_trail')) + '"><span class="sh2-ico">' + ICONS.trail + '</span><span class="sh2-ctl-lbl">' + esc(tr('btn_trail')) + '</span></button>' +
      '<button type="button" class="sh2-btn" id="sh2FitBtn"><span class="sh2-ico">' + ICONS.fit + '</span><span class="sh2-ctl-lbl">' + esc(tr('btn_fit')) + '</span></button>';

    document.getElementById('sh2ZoomIn').addEventListener('click', function () { mapView.zoomIn(); });
    document.getElementById('sh2ZoomOut').addEventListener('click', function () { mapView.zoomOut(); });
    document.getElementById('sh2JumpJames').addEventListener('click', jumpToJames);
    document.getElementById('sh2FollowBtn').addEventListener('click', function () {
      S.follow = !S.follow;
      savePrefs();
      renderControls();
      if (S.follow) jumpToJames();
    });
    document.getElementById('sh2TrailBtn').addEventListener('click', function () {
      S.showTrail = !S.showTrail;
      savePrefs();
      mapView.setTrail(S.trailPoints, S.showTrail);
      renderControls();
    });
    document.getElementById('sh2FitBtn').addEventListener('click', fitCurrentSheet);
  }

  // ==================== DOSSIER TABLET VIEWS (Loadout / Archive / Codes) ====================

  function renderLoadoutView(dos, sv) {
    var hp = dos.health != null ? Math.round(dos.health) : (sv.health != null ? Math.round(sv.health) : null);
    var vm = vitalMeta(hp);
    var eq = dos.equipment || {};
    var weapons = dos.weapons || [];
    var looseAmmo = dos.loose_ammo || [];
    var pocket = dos.pocket || [];
    var st = dos.stats || {};

    var vitalsHtml =
      '<div class="sh2-dos-card sh2-card-vitals">' +
        '<div class="sh2-card-head"><span class="sh2-kicker">' + esc(tr('vitals_hdr')) + ' · <b id="sh2LoadoutState">' + esc(vm.label) + '</b></span>' +
          (dos.is_live ? '<span class="sh2-live-pill is-live"><i class="sh2-pulse"></i>LIVE</span>' : '') +
        '</div>' +
        '<div class="sh2-ecg-row is-' + vm.cls + ' is-' + vm.tone + '" id="sh2LoadoutEcgRow">' +
          ecgSvgHtml(true) +
          '<div class="sh2-ecg-val" id="sh2LoadoutHp">' + (hp != null ? hp + '%' : '—') + '</div>' +
        '</div>' +
        '<div class="sh2-meds-row">' +
          '<div class="sh2-med-box">' + itemImgHtml(dos.drinks_icon, 'sh2-med-img', tr('drinks_lbl')) +
            '<div><strong>×' + (dos.drinks != null ? dos.drinks : 0) + '</strong><span>' + esc(tr('drinks_lbl')) + '</span></div></div>' +
          '<div class="sh2-med-box">' + itemImgHtml(dos.syringes_icon, 'sh2-med-img', tr('syringes_lbl')) +
            '<div><strong>×' + (dos.syringes != null ? dos.syringes : 0) + '</strong><span>' + esc(tr('syringes_lbl')) + '</span></div></div>' +
        '</div>' +
      '</div>';

    var eqHtml =
      '<div class="sh2-dos-card">' +
        '<div class="sh2-card-head"><span class="sh2-kicker">' + esc(tr('equipment_hdr')) + '</span></div>' +
        '<div class="sh2-eq-grid">' +
          '<div class="sh2-eq-item' + (eq.flashlight_on ? ' is-on' : '') + '">' +
            (eq.flashlight_icon ? itemImgHtml(eq.flashlight_icon, 'sh2-eq-img', tr('flashlight_lbl')) : '<span class="sh2-ico sh2-eq-ico">' + ICONS.flashlight + '</span>') +
            '<div><div class="sh2-eq-name">' + esc(tr('flashlight_lbl')) + '</div><div class="sh2-eq-state">' + esc(eq.flashlight ? (eq.flashlight_on ? tr('state_on') : tr('state_off')) : '—') + '</div></div>' +
          '</div>' +
          '<div class="sh2-eq-item' + (eq.radio_on ? ' is-on' : '') + '">' +
            (eq.radio_icon ? itemImgHtml(eq.radio_icon, 'sh2-eq-img', tr('radio_lbl')) : '<span class="sh2-ico sh2-eq-ico">' + ICONS.radio + '</span>') +
            '<div><div class="sh2-eq-name">' + esc(tr('radio_lbl')) + '</div><div class="sh2-eq-state">' + esc(eq.radio ? (eq.radio_on ? tr('state_on') : tr('state_off')) : '—') + '</div></div>' +
          '</div>' +
        '</div>' +
        '<div class="sh2-meta-pills">' +
          (sv.place ? '<span class="sh2-pill">' + esc(sv.place) + '</span>' : '') +
          (sv.play_time ? '<span class="sh2-pill">' + esc(tr('playtime_lbl') + ': ' + sv.play_time) + '</span>' : '') +
          (sv.combat_difficulty ? '<span class="sh2-pill">' + esc(tr('combat_diff_lbl') + ': ' + sv.combat_difficulty) + '</span>' : '') +
          (sv.puzzle_difficulty ? '<span class="sh2-pill">' + esc(tr('puzzle_diff_lbl') + ': ' + sv.puzzle_difficulty) + '</span>' : '') +
        '</div>' +
      '</div>';

    var arsenalHtml =
      '<div class="sh2-dos-card sh2-card-wide">' +
        '<div class="sh2-card-head"><span class="sh2-kicker">' + esc(tr('arsenal_hdr')) + '</span></div>' +
        (!weapons.length && !looseAmmo.length ? '<div class="sh2-empty-note">' + esc(tr('no_items_empty')) + '</div>' : '') +
        '<div class="sh2-weapons-grid">' + weapons.map(function (w) {
          var maxBar = w.id === 'Pistol' ? 48 : (w.id === 'Shotgun' ? 24 : 20);
          var pct = w.kind === 'ranged' ? Math.min(100, Math.round(((w.total_ammo || 0) / Math.max(maxBar, w.total_ammo || 1)) * 100)) : 100;
          return '<div class="sh2-wep-card' + (w.equipped ? ' is-equipped' : '') + (w.drawn ? ' is-drawn' : '') + '">' +
            '<div class="sh2-wep-top">' +
              (w.icon ? itemImgHtml(w.icon, 'sh2-wep-img', w.name) : '<span class="sh2-ico sh2-wep-svg">' + ICONS.weapon + '</span>') +
              '<div class="sh2-wep-info">' +
                '<div class="sh2-wep-name">' + esc(w.name) + '</div>' +
                '<div class="sh2-wep-badges">' +
                  (w.drawn ? '<span class="sh2-pill is-live-sm">' + esc(tr('drawn_lbl')) + '</span>' : (w.equipped ? '<span class="sh2-pill">' + esc(tr('holstered_lbl')) + '</span>' : '')) +
                  '<span class="sh2-pill">' + esc(tr('kills_lbl') + ': ' + w.kills) + '</span>' +
                '</div>' +
              '</div>' +
            '</div>' +
            (w.kind === 'ranged' ? (
              '<div class="sh2-wep-ammo">' +
                '<span>' + esc(tr('loaded_lbl') + ': ') + '<b>' + w.loaded + '</b> · ' + esc(tr('reserve_lbl') + ': ') + '<b>' + w.reserve + '</b></span>' +
                '<span class="sh2-bar"><i style="width:' + pct + '%"></i></span>' +
              '</div>'
            ) : '') +
          '</div>';
        }).join('') + '</div>' +
        (looseAmmo.length ? (
          '<div class="sh2-loose-wrap"><div class="sh2-kicker" style="margin-bottom:6px">' + esc(tr('loose_ammo_hdr')) + '</div>' +
          '<div class="sh2-rewards-list">' + looseAmmo.map(function (a) {
            return '<span class="sh2-reward-pill">' + itemImgHtml(a.icon, 'sh2-reward-thumb', a.name) +
              '<span>' + esc(a.name) + ' ×' + a.qty + '</span></span>';
          }).join('') + '</div></div>'
        ) : '') +
      '</div>';

    var pocketHtml =
      '<div class="sh2-dos-card sh2-card-wide">' +
        '<div class="sh2-card-head"><span class="sh2-kicker">' + esc(tr('pocket_hdr')) + ' (' + pocket.length + ')</span></div>' +
        (!pocket.length ? '<div class="sh2-empty-note">' + esc(tr('no_items_empty')) + '</div>' : (
          '<div class="sh2-pocket-grid">' + pocket.map(function (it) {
            var hasText = Boolean(it.transcript_ru || it.transcript_en);
            var tagTxt = hasText ? tr('inspect_text_tag') : (it.memento ? tr('memento_badge') + ' · ' + tr('inspect_tag') : tr('inspect_tag'));
            return '<button type="button" class="sh2-pocket-item' + (it.memento ? ' is-memento' : '') + '" data-pocket-id="' + esc(it.id) + '">' +
              (it.icon ? itemImgHtml(it.icon, 'sh2-pocket-img', it.name) : '<span class="sh2-ico sh2-pocket-svg">' + ICONS.key_item + '</span>') +
              '<span class="sh2-pocket-body">' +
                '<span class="sh2-pocket-name">' + esc(it.name) + (it.qty > 1 ? ' ×' + it.qty : '') + '</span>' +
                '<span class="sh2-pocket-tag">' + esc(tagTxt) + '</span>' +
              '</span></button>';
          }).join('') + '</div>'
        )) +
      '</div>';

    var statPairs = [
      [tr('kills_lbl'), st.kills],
      [tr('kills_melee_lbl'), st.kills_melee],
      [tr('kills_ranged_lbl'), st.kills_ranged],
      [tr('shots_lbl'), st.shots_fired],
      [tr('dodges_lbl'), st.dodges],
      [tr('doors_checked_lbl'), st.locked_doors_checked],
      [tr('glass_lbl'), st.broken_glass],
      [tr('heals_lbl'), st.heals_used],
      [tr('damage_lbl'), st.damage_taken],
      [tr('consumables_lbl'), st.consumables_picked],
      [tr('investigated_lbl'), st.investigated],
      [tr('distance_lbl'), st.distance_m != null ? (st.distance_m >= 1000 ? (st.distance_m / 1000).toFixed(2) + ' km' : st.distance_m + ' m') : null]
    ].filter(function (x) { return x[1] != null; });

    var statsHtml =
      '<div class="sh2-dos-card sh2-card-wide">' +
        '<div class="sh2-card-head"><span class="sh2-kicker">' + esc(tr('stats_hdr')) + '</span></div>' +
        '<div class="sh2-stats-grid">' + statPairs.map(function (sp) {
          return '<div class="sh2-stat-tile"><strong>' + esc(sp[1]) + '</strong><span>' + esc(sp[0]) + '</span></div>';
        }).join('') + '</div>' +
      '</div>';

    return '<div class="sh2-loadout-grid">' + vitalsHtml + eqHtml + arsenalHtml + pocketHtml + statsHtml + '</div>';
  }

  function renderArchiveView(dos) {
    var photos = (dos.photos && dos.photos.list) || [];
    var memos = (dos.memos && dos.memos.list) || [];
    var chapters = dos.chapters || [];

    var subNav =
      '<div class="sh2-stage-bar">' +
        '<div class="sh2-seg">' +
          '<button type="button" data-asub="photos" class="' + (S.archiveSub === 'photos' ? 'is-active' : '') + '">' + esc(tr('photos_tab') + ' (' + ((dos.photos && dos.photos.got) || 0) + '/' + photos.length + ')') + '</button>' +
          '<button type="button" data-asub="memos" class="' + (S.archiveSub === 'memos' ? 'is-active' : '') + '">' + esc(tr('memos_tab') + ' (' + ((dos.memos && dos.memos.got) || 0) + '/' + memos.length + ')') + '</button>' +
          '<button type="button" data-asub="chapters" class="' + (S.archiveSub === 'chapters' ? 'is-active' : '') + '">' + esc(tr('chapters_tab') + ' (' + chapters.length + ')') + '</button>' +
        '</div>' +
        (S.archiveSub !== 'chapters' ? (
          '<div class="sh2-seg">' +
            '<button type="button" data-afilt="all" class="' + (S.archiveFilter === 'all' ? 'is-active' : '') + '">' + esc(tr('filter_all')) + '</button>' +
            '<button type="button" data-afilt="got" class="' + (S.archiveFilter === 'got' ? 'is-active' : '') + '">' + esc(tr('filter_got')) + '</button>' +
            '<button type="button" data-afilt="missing" class="' + (S.archiveFilter === 'missing' ? 'is-active' : '') + '">' + esc(tr('filter_missing')) + '</button>' +
          '</div>'
        ) : '') +
        (S.archiveSub === 'memos' ? (
          '<input type="search" class="sh2-search-input sh2-stage-search" id="sh2ArchiveMemoSearch" placeholder="' + esc(tr('search_ph')) + '" value="' + esc(S.archiveMemoQuery) + '">'
        ) : '') +
      '</div>';

    if (S.archiveSub === 'photos') {
      var visPhotos = photos.filter(function (ph) {
        if (S.archiveFilter === 'got') return ph.collected;
        if (S.archiveFilter === 'missing') return !ph.collected;
        return true;
      });
      return subNav + '<div class="sh2-polaroid-grid">' + visPhotos.map(function (ph) {
        var mask = S.antiSpoiler && !ph.collected;
        return '<button type="button" class="sh2-polaroid-card' + (ph.collected ? ' is-collected' : ' is-missing') + '" data-pnum="' + ph.num + '">' +
          '<div class="sh2-polaroid-frame">' +
            (mask ? '<div class="sh2-polaroid-mystery">?</div>' : (ph.icon ? itemImgHtml(ph.icon, 'sh2-polaroid-img', ph.title) : '<div class="sh2-polaroid-mystery">#' + ph.num + '</div>')) +
            '<span class="sh2-polaroid-num">#' + ph.num + '</span>' +
          '</div>' +
          '<div class="sh2-polaroid-cap">' + esc(mask ? tr('uncollected_lbl') : ph.title) + '</div>' +
          '<div class="sh2-polaroid-loc">' + esc(ph.region_name + ' · ' + ph.map_title) + '</div>' +
        '</button>';
      }).join('') + '</div>';
    }

    if (S.archiveSub === 'memos') {
      var mq = S.archiveMemoQuery.trim().toLowerCase();
      var visMemos = memos.filter(function (mm) {
        if (S.archiveFilter === 'got' && !mm.collected) return false;
        if (S.archiveFilter === 'missing' && mm.collected) return false;
        if (mq) {
          var hay = (mm.title + ' ' + mm.map_title + ' ' + mm.region_name + ' ' + (mm.transcript_ru || '') + ' ' + (mm.transcript_en || '')).toLowerCase();
          if (hay.indexOf(mq) === -1) return false;
        }
        return true;
      });
      var selMemo = visMemos.find(function (m) { return m.id === S.selectedMemoId; }) || visMemos[0] || null;
      var curTr = S.trLang || i18n.lang;
      var memoTxt = selMemo ? (curTr === 'ru' ? (selMemo.transcript_ru || selMemo.transcript_en) : (selMemo.transcript_en || selMemo.transcript_ru)) : '';

      return subNav + '<div class="sh2-memo-split">' +
        '<div class="sh2-memo-list">' +
          (!visMemos.length ? '<div class="sh2-empty-note">' + esc(tr('no_memos_empty')) + '</div>' : visMemos.map(function (mm) {
            return '<button type="button" class="sh2-pin-row' + (mm.collected ? ' is-done' : '') + (selMemo && selMemo.id === mm.id ? ' is-selected' : '') + '" data-mid="' + mm.id + '">' +
              '<span class="sh2-pin-row-ico" style="color:' + (mm.collected ? 'var(--sh2-green)' : 'var(--sh2-ivory)') + '">' + ICONS.memo + '</span>' +
              '<span class="sh2-pin-row-body">' +
                '<span class="sh2-pin-row-title">' + esc(mm.title) + '</span>' +
                '<span class="sh2-pin-row-sub">' + esc(mm.region_name + ' · ' + mm.floor) + '</span>' +
              '</span></button>';
          }).join('')) +
        '</div>' +
        '<div class="sh2-memo-reader">' + (selMemo ? (
          '<div class="sh2-memo-reader-head">' +
            (selMemo.icon ? '<button type="button" class="sh2-drawer-art is-clickable" data-inspect-memo="' + selMemo.id + '" title="' + esc(tr('inspect_btn')) + '">' + itemImgHtml(selMemo.icon, 'sh2-drawer-img', selMemo.title) + '</button>' : '') +
            '<div style="flex:1;min-width:0">' +
              '<div class="sh2-kicker">' + esc(selMemo.region_name + ' · ' + selMemo.map_title) + '</div>' +
              '<h3 class="sh2-drawer-title">' + esc(selMemo.title) + '</h3>' +
              '<div class="sh2-badge-line" style="margin-top:8px">' +
                '<span class="sh2-pill ' + (selMemo.collected ? 'is-done' : 'is-rem') + '">' + esc(selMemo.collected ? tr('status_collected') : tr('status_remaining')) + '</span>' +
                '<button type="button" class="sh2-btn" data-inspect-memo="' + selMemo.id + '" style="height:28px;padding:0 10px">' + esc(tr('inspect_btn')) + '</button>' +
                '<button type="button" class="sh2-btn" data-jmap="' + esc(selMemo.map) + '" data-jpid="' + selMemo.pin_id + '" style="height:28px;padding:0 10px">' + esc(tr('jump_to_map')) + '</button>' +
              '</div>' +
            '</div>' +
            '<div class="sh2-seg">' +
              '<button type="button" data-trl="ru" class="' + (curTr === 'ru' ? 'is-active' : '') + '">RU</button>' +
              '<button type="button" data-trl="en" class="' + (curTr === 'en' ? 'is-active' : '') + '">EN</button>' +
            '</div>' +
          '</div>' +
          (selMemo.desc ? '<div class="sh2-drawer-desc" style="margin:0 16px 10px">' + esc(selMemo.desc) + '</div>' : '') +
          '<div class="sh2-memo-reader-body">' + esc(memoTxt || tr('uncollected_lbl')) + '</div>'
        ) : '<div class="sh2-empty-note">' + esc(tr('no_memos_empty')) + '</div>') + '</div>' +
      '</div>';
    }

    return subNav + '<div class="sh2-chapters-grid">' + chapters.map(function (c) {
      return '<button type="button" class="sh2-dos-card sh2-chapter-card' + (c.is_current || c.is_live ? ' is-current' : '') + '" data-jmap="' + esc(c.default_map) + '">' +
        '<div class="sh2-card-head">' +
          '<span class="sh2-chapter-title">' + (c.is_current || c.is_live ? '<i class="sh2-red-sq" style="margin-right:6px"></i>' : '') + esc(c.name) + '</span>' +
          '<span class="sh2-global-num" style="margin:0">' + Math.round(c.completion.percent) + '%</span>' +
        '</div>' +
        '<span class="sh2-bar"><i style="width:' + c.completion.percent + '%"></i></span>' +
        '<div class="sh2-chapter-metrics">' +
          '<span>' + esc(tr('photos_lbl') + ': ' + c.photos_got + '/' + c.photos_total) + '</span>' +
          '<span>' + esc(tr('memos_lbl') + ': ' + c.memos_got + '/' + c.memos_total) + '</span>' +
          '<span>' + esc(tr('glimpses_lbl') + ': ' + c.glimpses_got + '/' + c.glimpses_total) + '</span>' +
          '<span>100%: ' + c.completion.collected + '/' + c.completion.total + '</span>' +
        '</div>' +
      '</button>';
    }).join('') + '</div>';
  }

  function renderCodesView(dos, sv) {
    var puzzles = (dos.puzzles || []).slice().sort(function (a, b) {
      return (b.codes ? 1 : 0) - (a.codes ? 1 : 0);
    });
    var cq = S.codesQuery.trim().toLowerCase();
    var vis = puzzles.filter(function (pz) {
      if (S.codesFilter === 'got' && pz.status !== 'collected') return false;
      if (S.codesFilter === 'missing' && pz.status === 'collected') return false;
      if (cq) {
        var hay = (pz.title + ' ' + pz.region_name + ' ' + pz.map_title + ' ' +
          JSON.stringify(pz.codes || '') + ' ' + (pz.note || '') + ' ' + (pz.rewards || []).join(' ')).toLowerCase();
        if (hay.indexOf(cq) === -1) return false;
      }
      return true;
    });
    var activeDiffKey = diffKeyFromId(sv && sv.puzzle_difficulty_id);

    var bar =
      '<div class="sh2-stage-bar">' +
        '<input type="search" class="sh2-search-input sh2-stage-search" id="sh2CodesSearch" placeholder="' + esc(tr('codes_search_ph')) + '" value="' + esc(S.codesQuery) + '">' +
        '<div class="sh2-seg">' +
          '<button type="button" data-cfilt="all" class="' + (S.codesFilter === 'all' ? 'is-active' : '') + '">' + esc(tr('filter_all')) + ' (' + puzzles.length + ')</button>' +
          '<button type="button" data-cfilt="got" class="' + (S.codesFilter === 'got' ? 'is-active' : '') + '">' + esc(tr('status_collected')) + '</button>' +
          '<button type="button" data-cfilt="missing" class="' + (S.codesFilter === 'missing' ? 'is-active' : '') + '">' + esc(tr('filter_missing')) + '</button>' +
        '</div>' +
      '</div>';

    if (!vis.length) {
      return bar + '<div class="sh2-empty-note">' + esc(tr('no_puzzles_empty')) + '</div>';
    }

    return bar + '<div class="sh2-codes-grid">' + vis.map(function (pz) {
      var stCls = pz.status === 'collected' ? 'is-done' : (pz.status === 'not_collected' ? 'is-rem' : '');
      var stTxt = pz.status === 'collected' ? tr('status_collected') : (pz.status === 'not_collected' ? tr('status_remaining') : tr('status_unknown'));
      var hiddenCode = S.antiSpoiler && !S.revealedCodes[pz.id];
      var codeRows = '';
      if (pz.codes) {
        if (hiddenCode) {
          codeRows = '<button type="button" class="sh2-btn" data-creveal="' + pz.id + '" style="width:100%;margin-top:8px">' + esc(tr('reveal_code')) + '</button>';
        } else {
          var pairs = [];
          if (pz.codes.all) pairs.push(['all', tr('diff_all'), pz.codes.all]);
          if (pz.codes.easy) pairs.push(['easy', tr('diff_easy'), pz.codes.easy]);
          if (pz.codes.normal) pairs.push(['normal', tr('diff_normal'), pz.codes.normal]);
          if (pz.codes.hard) pairs.push(['hard', tr('diff_hard'), pz.codes.hard]);
          codeRows = '<div class="sh2-code-grid">' + pairs.map(function (r) {
            var m = activeDiffKey && r[0] === activeDiffKey;
            return '<div class="sh2-code-row' + (m ? ' is-active-diff' : '') + '">' +
              '<span>' + esc(r[1]) + (m ? '<em class="sh2-diff-here">' + esc(tr('active_diff_badge')) + '</em>' : '') + '</span>' +
              '<span class="sh2-code-val">' + esc(r[2]) + '</span></div>';
          }).join('') + '</div>';
        }
      }
      var rIcons = pz.rewards_icons || [];
      return '<div class="sh2-dos-card sh2-code-card-item' + (pz.status === 'collected' ? ' is-solved' : '') + '">' +
        '<div class="sh2-card-head">' +
          '<div>' +
            '<div class="sh2-kicker">' + esc(pz.region_name + ' · ' + pz.floor) + '</div>' +
            '<div class="sh2-code-item-title">' + esc(pz.title) + '</div>' +
          '</div>' +
          '<span class="sh2-pill ' + stCls + '">' + esc(stTxt) + '</span>' +
        '</div>' +
        codeRows +
        (pz.rewards && pz.rewards.length ? (
          '<div class="sh2-rewards-list" style="margin-top:8px">' + pz.rewards.map(function (rw, idx) {
            return '<span class="sh2-reward-pill">' + (rIcons[idx] ? itemImgHtml(rIcons[idx], 'sh2-reward-thumb', rw) : '') + '<span>' + esc(rw) + '</span></span>';
          }).join('') + '</div>'
        ) : '') +
        '<div style="margin-top:auto;padding-top:8px;display:flex;justify-content:flex-end">' +
          '<button type="button" class="sh2-btn" data-jmap="' + esc(pz.map) + '" data-jpid="' + pz.pin_id + '" style="height:30px;padding:0 10px">' + esc(tr('jump_to_map')) + '</button>' +
        '</div>' +
      '</div>';
    }).join('') + '</div>';
  }

  function resolveInspectContext() {
    if (!S.inspect || !S.payload) return null;
    var dos = S.payload.dossier || {};
    var kind = S.inspect.kind;
    var curTr = S.trLang || i18n.lang;

    if (kind === 'photo') {
      var photos = (dos.photos && dos.photos.list) || [];
      var idx = photos.findIndex(function (x) { return x.num === S.inspect.id; });
      if (idx === -1) return null;
      var ph = photos[idx];
      var mask = S.antiSpoiler && !ph.collected;
      var cap = curTr === 'ru' ? (ph.transcript_ru || ph.transcript_en) : (ph.transcript_en || ph.transcript_ru);
      return {
        kind: 'photo',
        kicker: '#' + ph.num + ' · ' + ph.region_name + ' · ' + ph.map_title,
        title: mask ? tr('uncollected_lbl') : ph.title,
        icon: mask ? null : ph.icon,
        mystery: mask ? '?' : ('#' + ph.num),
        desc: mask ? null : ph.desc,
        caption: mask ? null : cap,
        transcript: null,
        hasTranscriptLang: false,
        statusTxt: ph.collected ? tr('status_collected') : tr('status_remaining'),
        statusCls: ph.collected ? 'is-done' : 'is-rem',
        map: ph.map,
        pinId: ph.pin_id,
        index: idx,
        total: photos.length,
        step: function (d) {
          if (photos.length < 2) return;
          var n = photos[(idx + d + photos.length) % photos.length];
          S.inspect = { kind: 'photo', id: n.num };
          renderInspectModal();
        }
      };
    }

    if (kind === 'pocket') {
      var pocket = dos.pocket || [];
      var pIdx = pocket.findIndex(function (x) { return x.id === S.inspect.id; });
      if (pIdx === -1) return null;
      var it = pocket[pIdx];
      var pTxt = curTr === 'ru' ? (it.transcript_ru || it.transcript_en) : (it.transcript_en || it.transcript_ru);
      return {
        kind: 'pocket',
        kicker: it.memento ? tr('memento_full_lbl') : tr('clue_full_lbl'),
        title: it.name + (it.qty > 1 ? ' ×' + it.qty : ''),
        icon: it.icon,
        mystery: null,
        desc: it.desc || null,
        caption: null,
        transcript: pTxt || null,
        hasTranscriptLang: Boolean(it.transcript_ru && it.transcript_en && it.transcript_ru !== it.transcript_en),
        statusTxt: tr('status_collected'),
        statusCls: 'is-done',
        map: it.map,
        pinId: it.pin_id,
        index: pIdx,
        total: pocket.length,
        step: function (d) {
          if (pocket.length < 2) return;
          var n = pocket[(pIdx + d + pocket.length) % pocket.length];
          S.inspect = { kind: 'pocket', id: n.id };
          renderInspectModal();
        }
      };
    }

    if (kind === 'memo') {
      var memos = (dos.memos && dos.memos.list) || [];
      var mIdx = memos.findIndex(function (x) { return x.id === S.inspect.id; });
      if (mIdx === -1) return null;
      var mm = memos[mIdx];
      var mMask = S.antiSpoiler && !mm.collected;
      var mTxt = curTr === 'ru' ? (mm.transcript_ru || mm.transcript_en) : (mm.transcript_en || mm.transcript_ru);
      return {
        kind: 'memo',
        kicker: mm.region_name + ' · ' + mm.map_title,
        title: mMask ? tr('uncollected_lbl') : mm.title,
        icon: mMask ? null : mm.icon,
        mystery: mMask ? '?' : null,
        desc: mMask ? null : (mm.desc || null),
        caption: null,
        transcript: mMask ? tr('uncollected_lbl') : (mTxt || null),
        hasTranscriptLang: !mMask && Boolean(mm.transcript_ru && mm.transcript_en && mm.transcript_ru !== mm.transcript_en),
        statusTxt: mm.collected ? tr('status_collected') : tr('status_remaining'),
        statusCls: mm.collected ? 'is-done' : 'is-rem',
        map: mm.map,
        pinId: mm.pin_id,
        index: mIdx,
        total: memos.length,
        step: function (d) {
          if (memos.length < 2) return;
          var n = memos[(mIdx + d + memos.length) % memos.length];
          S.selectedMemoId = n.id;
          S.inspect = { kind: 'memo', id: n.id };
          renderInspectModal();
        }
      };
    }

    if (kind === 'pin') {
      var pins = (S.payload.world && S.payload.world.pins) || [];
      var pin = pins.find(function (x) { return x.id === S.inspect.id; });
      if (!pin) return null;
      var pinTxt = curTr === 'ru' ? (pin.transcript_ru || pin.transcript_en) : (pin.transcript_en || pin.transcript_ru);
      var stCls = pin.status === 'collected' ? 'is-done' : (pin.status === 'not_collected' ? 'is-rem' : '');
      var stTxt = pin.status === 'collected' ? tr('status_collected') : (pin.status === 'not_collected' ? tr('status_remaining') : tr('status_unknown'));
      return {
        kind: 'pin',
        kicker: pin.category_label + (pin.note ? ' · ' + pin.note : ''),
        title: pin.title,
        icon: pin.icon,
        mystery: null,
        desc: pin.desc || null,
        caption: null,
        transcript: pinTxt || null,
        hasTranscriptLang: Boolean(pin.transcript_ru && pin.transcript_en && pin.transcript_ru !== pin.transcript_en),
        statusTxt: stTxt,
        statusCls: stCls,
        map: null,
        pinId: null,
        index: 0,
        total: 1,
        step: null
      };
    }

    return null;
  }

  function renderInspectModal() {
    var mod = document.getElementById('sh2Modal');
    var ctx = resolveInspectContext();
    if (!ctx) {
      mod.hidden = true;
      mod.innerHTML = '';
      return;
    }
    mod.hidden = false;
    var curTr = S.trLang || i18n.lang;
    var hasTextPane = Boolean(ctx.transcript || ctx.desc || ctx.caption);
    var hasVisualPane = Boolean(ctx.icon || ctx.mystery);
    var isSplit = hasVisualPane && Boolean(ctx.transcript);

    var visualHtml = hasVisualPane ? (
      '<div class="sh2-inspect-visual' + (ctx.kind === 'photo' ? ' is-polaroid' : '') + '">' +
        (ctx.icon ? itemImgHtml(ctx.icon, 'sh2-inspect-img', ctx.title) : '<div class="sh2-polaroid-mystery" style="height:240px">' + esc(ctx.mystery || '') + '</div>') +
        (ctx.caption ? '<div class="sh2-inspect-caption"><span>' + esc(tr('photo_caption_lbl')) + '</span><strong>«' + esc(ctx.caption) + '»</strong></div>' : '') +
      '</div>'
    ) : '';

    var textHtml = hasTextPane ? (
      '<div class="sh2-inspect-text">' +
        (ctx.desc ? '<div class="sh2-inspect-desc">' + esc(ctx.desc) + '</div>' : '') +
        (ctx.transcript ? (
          '<div class="sh2-inspect-tr-head">' +
            '<span class="sh2-kicker">' + esc(tr('transcript_header')) + '</span>' +
            (ctx.hasTranscriptLang ? (
              '<div class="sh2-seg">' +
                '<button type="button" data-mtrl="ru" class="' + (curTr === 'ru' ? 'is-active' : '') + '">RU</button>' +
                '<button type="button" data-mtrl="en" class="' + (curTr === 'en' ? 'is-active' : '') + '">EN</button>' +
              '</div>'
            ) : '') +
          '</div>' +
          '<div class="sh2-inspect-transcript">' + esc(ctx.transcript) + '</div>'
        ) : '') +
      '</div>'
    ) : '';

    var navBtns = (ctx.step && ctx.total > 1) ? (
      '<div class="sh2-inspect-nav">' +
        '<button type="button" class="sh2-btn" id="sh2ModalPrev" title="' + esc(tr('prev_item')) + '">‹</button>' +
        '<span class="sh2-inspect-counter">' + (ctx.index + 1) + ' / ' + ctx.total + '</span>' +
        '<button type="button" class="sh2-btn" id="sh2ModalNext" title="' + esc(tr('next_item')) + '">›</button>' +
      '</div>'
    ) : '';

    mod.innerHTML =
      '<div class="sh2-plate sh2-photo-modal sh2-inspect-modal' + (isSplit ? ' is-split' : '') + '">' +
        '<div class="sh2-drawer-head">' +
          '<div style="flex:1;min-width:0">' +
            '<div class="sh2-kicker">' + esc(ctx.kicker) + '</div>' +
            '<h3 class="sh2-drawer-title">' + esc(ctx.title) + '</h3>' +
          '</div>' +
          navBtns +
          '<button type="button" class="sh2-btn" id="sh2ModalClose" style="height:34px;padding:0 11px;flex:none"><span class="sh2-ico">' + ICONS.close + '</span></button>' +
        '</div>' +
        '<div class="sh2-inspect-body' + (isSplit ? ' is-split' : '') + '">' +
          visualHtml + textHtml +
        '</div>' +
        '<div class="sh2-photo-modal-foot">' +
          '<span class="sh2-pill ' + ctx.statusCls + '">' + esc(ctx.statusTxt) + '</span>' +
          (ctx.map && ctx.pinId != null ? '<button type="button" class="sh2-btn" id="sh2ModalJump">' + esc(tr('jump_to_map')) + '</button>' : '') +
        '</div>' +
      '</div>';

    document.getElementById('sh2ModalClose').addEventListener('click', function () {
      S.inspect = null;
      renderInspectModal();
    });
    mod.onclick = function (e) {
      if (e.target === mod) {
        S.inspect = null;
        renderInspectModal();
      }
    };
    var prevBtn = document.getElementById('sh2ModalPrev');
    if (prevBtn && ctx.step) prevBtn.addEventListener('click', function () { ctx.step(-1); });
    var nextBtn = document.getElementById('sh2ModalNext');
    if (nextBtn && ctx.step) nextBtn.addEventListener('click', function () { ctx.step(1); });
    mod.querySelectorAll('[data-mtrl]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.trLang = b.getAttribute('data-mtrl');
        renderInspectModal();
      });
    });
    var jumpBtn = document.getElementById('sh2ModalJump');
    if (jumpBtn) {
      jumpBtn.addEventListener('click', function () {
        var gm = ctx.map;
        var gp = ctx.pinId;
        S.inspect = null;
        renderInspectModal();
        jumpToMapAndPin(gm, gp, false);
      });
    }
  }

  function renderDossierStage() {
    if (S.activeTab === 'map' || !S.payload) return;
    var stage = document.getElementById('sh2DossierStage');
    var dos = S.payload.dossier || {};
    var sv = S.payload.save || {};
    var prevScroll = stage.scrollTop;

    if (S.activeTab === 'loadout') {
      stage.innerHTML = renderLoadoutView(dos, sv);
    } else if (S.activeTab === 'archive') {
      stage.innerHTML = renderArchiveView(dos);
    } else if (S.activeTab === 'codes') {
      stage.innerHTML = renderCodesView(dos, sv);
    }
    stage.scrollTop = prevScroll;

    stage.querySelectorAll('[data-jmap]').forEach(function (b) {
      b.addEventListener('click', function () {
        var gm = b.getAttribute('data-jmap');
        var gp = b.getAttribute('data-jpid');
        jumpToMapAndPin(gm, gp ? Number(gp) : null, S.activeTab === 'codes');
      });
    });
    stage.querySelectorAll('[data-asub]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.archiveSub = b.getAttribute('data-asub');
        renderDossierStage();
      });
    });
    stage.querySelectorAll('[data-afilt]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.archiveFilter = b.getAttribute('data-afilt');
        renderDossierStage();
      });
    });
    stage.querySelectorAll('[data-pnum]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.inspect = { kind: 'photo', id: Number(b.getAttribute('data-pnum')) };
        renderInspectModal();
      });
    });
    stage.querySelectorAll('[data-pocket-id]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.inspect = { kind: 'pocket', id: b.getAttribute('data-pocket-id') };
        renderInspectModal();
      });
    });
    stage.querySelectorAll('[data-inspect-memo]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.inspect = { kind: 'memo', id: Number(b.getAttribute('data-inspect-memo')) };
        renderInspectModal();
      });
    });
    stage.querySelectorAll('[data-mid]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.selectedMemoId = Number(b.getAttribute('data-mid'));
        renderDossierStage();
      });
    });
    stage.querySelectorAll('[data-trl]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.trLang = b.getAttribute('data-trl');
        renderDossierStage();
      });
    });
    stage.querySelectorAll('[data-cfilt]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.codesFilter = b.getAttribute('data-cfilt');
        renderDossierStage();
      });
    });
    stage.querySelectorAll('[data-creveal]').forEach(function (b) {
      b.addEventListener('click', function () {
        S.revealedCodes[b.getAttribute('data-creveal')] = true;
        renderDossierStage();
      });
    });

    var memoSearch = document.getElementById('sh2ArchiveMemoSearch');
    if (memoSearch) {
      memoSearch.addEventListener('input', function (e) {
        S.archiveMemoQuery = e.target.value || '';
        renderDossierStage();
        var el = document.getElementById('sh2ArchiveMemoSearch');
        if (el) { el.focus(); el.setSelectionRange(el.value.length, el.value.length); }
      });
    }
    var codesSearch = document.getElementById('sh2CodesSearch');
    if (codesSearch) {
      codesSearch.addEventListener('input', function (e) {
        S.codesQuery = e.target.value || '';
        renderDossierStage();
        var el = document.getElementById('sh2CodesSearch');
        if (el) { el.focus(); el.setSelectionRange(el.value.length, el.value.length); }
      });
    }
  }

  function applyPayload(data, keepViewport, cb) {
    S.payload = data;
    var w = data.world;
    var sel = w.selected_map;
    document.documentElement.setAttribute('data-era', sel.era || 'fog');
    document.title = i18n.lang === 'ru' ? 'SILENT HILL 2 — Живой планшет-компаньон' : 'SILENT HILL 2 — Companion Tablet';

    var lt = data.live_telemetry;
    if (S.follow && lt && lt.available && lt.active_map_slug && lt.active_map_slug !== w.selected_map_slug && S.lastLiveSlug !== lt.active_map_slug) {
      S.lastLiveSlug = lt.active_map_slug;
      selectMap(lt.active_map_slug, false, false);
      return;
    }
    if (lt && lt.available) S.lastLiveSlug = lt.active_map_slug;

    var slugChanged = S.renderedSlug !== sel.slug;
    if (slugChanged) {
      S.trailPoints = [];
      mapView.setTrail([], S.showTrail);
    }
    S.renderedSlug = sel.slug;
    S.mapSlug = sel.slug;

    mapView.setPaperUrl('/sh2-paper/' + encodeURIComponent(sel.slug) + '.png');
    mapView.setLabels(w.overlays.labels, S.showLabels);
    mapView.setRedPenMarks(w.overlays.james_marks, effectiveRedPenMode());

    syncSidebarVisibility();
    renderTopbar();
    renderMapVitals();
    renderFloorbar();
    renderSidebarHeaderAndToggles();
    renderPinsAndSidebarList();
    renderDrawer();
    renderControls();
    if (S.activeTab !== 'map') renderDossierStage();
    renderInspectModal();

    if (slugChanged && !keepViewport) {
      fitCurrentSheet();
    }
    if (S.follow && lt && lt.available && lt.selected_projection && lt.selected_projection.in_bounds) {
      mapView.setView([lt.selected_projection.px, lt.selected_projection.py]);
    }
    if (cb) cb(data);
  }

  function fetchState(keepViewport, cb) {
    if (S.fetching) return;
    S.fetching = true;
    var manual = Array.from(getManualSet()).join(',');
    var qs = '?lang=' + encodeURIComponent(i18n.lang);
    if (S.mapSlug) qs += '&map=' + encodeURIComponent(S.mapSlug);
    if (manual) qs += '&marked=' + encodeURIComponent(manual);

    fetch('/api/map' + qs, { cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        S.fetching = false;
        if (data && data.ok) applyPayload(data, keepViewport, cb);
      })
      .catch(function () { S.fetching = false; });
  }

  // ==================== REAL-TIME SSE STREAM ====================
  var sse = null;
  var stateTimer = 0;

  function applyLiveTick(tick) {
    if (!tick || !S.payload) return;
    S.payload.live_telemetry = Object.assign({}, S.payload.live_telemetry || {}, tick);
    if (tick.health != null) {
      if (S.payload.save) S.payload.save.health = tick.health;
      if (S.payload.dossier) S.payload.dossier.health = tick.health;
    }

    var badge = document.getElementById('sh2StreamBadge');
    var stxt = document.getElementById('sh2StreamTxt');
    if (badge && stxt) {
      badge.className = 'sh2-stream-badge ' + (tick.available ? 'is-live' : 'is-ready');
      stxt.textContent = tick.available ? tr('stream_live') : (tick.health != null ? Math.round(tick.health) + '%' : tr('stream_wait'));
    }

    var hpVal = tick.health != null ? Math.round(tick.health) + '%' : null;
    if (hpVal) {
      var vm = vitalMeta(tick.health);
      var sideHp = document.getElementById('sh2SideHp');
      if (sideHp) sideHp.textContent = hpVal;
      var loadHp = document.getElementById('sh2LoadoutHp');
      if (loadHp) loadHp.textContent = hpVal;
      var loadState = document.getElementById('sh2LoadoutState');
      if (loadState) loadState.textContent = vm.label;
      var loadEcg = document.getElementById('sh2LoadoutEcgRow');
      if (loadEcg) loadEcg.className = 'sh2-ecg-row is-' + vm.cls + ' is-' + vm.tone;
      var mapVitals = document.getElementById('sh2MapVitals');
      if (mapVitals) {
        mapVitals.className = 'sh2-plate sh2-map-vitals is-' + vm.cls + (tick.available ? ' is-live' : '');
        if (S.activeTab === 'map') mapVitals.hidden = false;
      }
      var mapState = document.getElementById('sh2MapVitalsState');
      if (mapState) mapState.textContent = vm.label;
      var mapHp = document.getElementById('sh2MapVitalsHp');
      if (mapHp) {
        mapHp.className = 'sh2-vitals-hp is-' + vm.tone;
        mapHp.textContent = hpVal;
      }
    }

    if (tick.available && tick.active_map_slug && tick.active_map_slug !== S.renderedSlug) {
      if (S.follow && S.activeTab === 'map' && S.lastLiveSlug !== tick.active_map_slug) {
        S.lastLiveSlug = tick.active_map_slug;
        selectMap(tick.active_map_slug, false, false);
        return;
      }
    }

    if (tick.available && tick.active_projection && tick.active_projection.in_bounds && tick.active_map_slug === S.renderedSlug) {
      var p = tick.active_projection;
      setJamesTarget(p.px, p.py, p.angle_deg, tick.fov || 70, true, false);
    }
  }

  function connectStream() {
    if (typeof window.EventSource !== 'function' || sse) return;
    try {
      sse = new window.EventSource('/api/stream');
      sse.onopen = function () {
        S.streamState = 'open';
        root.setAttribute('data-stream', 'open');
      };
      sse.addEventListener('tick', function (ev) {
        try { applyLiveTick(JSON.parse(ev.data)); } catch (e) {}
      });
      sse.addEventListener('state', function () {
        clearTimeout(stateTimer);
        stateTimer = setTimeout(function () { fetchState(true); }, 110);
      });
      sse.onerror = function () {
        S.streamState = 'idle';
        root.setAttribute('data-stream', 'idle');
      };
    } catch (e) {
      S.streamState = 'idle';
    }
  }

  function stepFloor(delta) {
    if (!S.payload) return;
    var w = S.payload.world;
    var sel = w.selected_map;
    var reg = w.regions.find(function (r) { return r.key === sel.region; });
    if (!reg || reg.maps.length < 2) return;
    var idx = reg.maps.findIndex(function (m) { return m.slug === sel.slug; });
    var next = reg.maps[(idx + delta + reg.maps.length) % reg.maps.length];
    selectMap(next.slug, true);
  }

  window.addEventListener('resize', syncSidebarVisibility);

  // Keyboard shortcuts
  window.addEventListener('keydown', function (e) {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    var k = e.key.toLowerCase();
    if (e.key === 'Tab') {
      if (S.activeTab === 'map') {
        e.preventDefault();
        S.sidebarCollapsed = !S.sidebarCollapsed;
        savePrefs();
        syncSidebarVisibility();
      }
    } else if (e.key === 'Escape') {
      if (S.inspect) {
        S.inspect = null;
        renderInspectModal();
      } else if (S.selectedPinId != null) {
        S.selectedPinId = null;
        renderPinsAndSidebarList();
        renderDrawer();
      }
    } else if (S.inspect && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      var ic = resolveInspectContext();
      if (ic && ic.step) {
        e.preventDefault();
        ic.step(e.key === 'ArrowRight' ? 1 : -1);
      }
    } else if (k === 'c' || k === 'с') {
      jumpToJames();
    } else if (k === 'f' || k === 'а') {
      S.follow = !S.follow;
      savePrefs();
      renderControls();
    } else if (k === 'r' || k === 'к') {
      fitCurrentSheet();
    } else if (k === 'x' || k === 'ч') {
      var sel = S.payload && S.payload.world && S.payload.world.selected_map;
      if (sel && sel.twin) selectMap(sel.twin, true);
    } else if (e.key === '[' || k === 'х' || e.key === 'PageDown') {
      stepFloor(-1);
    } else if (e.key === ']' || k === 'ъ' || e.key === 'PageUp') {
      stepFloor(1);
    } else if (k === 'm' || k === 'ь') {
      var order = ['save', 'all', 'off'];
      S.redPen = order[(order.indexOf(effectiveRedPenMode()) + 1) % order.length];
      savePrefs();
      renderSidebarHeaderAndToggles();
      if (S.payload) mapView.setRedPenMarks(S.payload.world.overlays.james_marks, S.redPen);
    } else if (k === 'u' || k === 'г') {
      var mOrder = ['remaining', 'scored', 'loot', 'all'];
      S.mode = mOrder[(mOrder.indexOf(S.mode) + 1) % mOrder.length];
      savePrefs();
      renderTopbar();
      renderPinsAndSidebarList();
    } else if (e.key >= '1' && e.key <= '8' && S.payload) {
      if (S.activeTab !== 'map') setActiveTab('map');
      var reg = S.payload.world.regions[Number(e.key) - 1];
      if (reg) selectMap(reg.default_map, false);
    }
  });

  // Fallback poll (10s when SSE open, 3.5s if SSE down)
  function schedulePoll() {
    var ms = S.streamState === 'open' ? 10000 : 3500;
    setTimeout(function () {
      fetchState(true);
      schedulePoll();
    }, ms);
  }

  fetchState(false, function () {
    setTimeout(connectStream, 650);
  });
  schedulePoll();
})();
