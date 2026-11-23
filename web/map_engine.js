/* Direct 2048x2048 Cartesian paper-sheet renderer for SILENT HILL 2 Companion Map.
 * Zero external dependencies or CDN calls. Supports momentum pan, wheel/pinch/double-tap zoom, flyTo, and trail.
 */
(function () {
  'use strict';

  var SHEET_SIZE = 2048;

  function PaperMapView(container, opts) {
    this.el = typeof container === 'string' ? document.getElementById(container) : container;
    this.el.classList.add('sh2-map-viewport');
    this.opts = opts || {};
    this.minZoom = this.opts.minZoom != null ? this.opts.minZoom : -2.2;
    this.maxZoom = this.opts.maxZoom != null ? this.opts.maxZoom : 2.6;
    this.center = [1024, 1024];
    this.zoom = -0.5;
    this.events = {};
    this.markers = [];
    this.pending = false;
    this.pointers = new window.Map();
    this.drag = null;
    this.moved = false;
    this._wasMulti = false;
    this._vel = { vx: 0, vy: 0, lastX: 0, lastY: 0, lastT: 0 };
    this._inertiaRaf = 0;
    this._flyRaf = 0;
    this._lastTap = { t: 0, x: 0, y: 0 };

    this.stage = document.createElement('div');
    this.stage.className = 'sh2-sheet-stage';

    this.paperImg = document.createElement('img');
    this.paperImg.className = 'sh2-paper-img';
    this.paperImg.alt = '';
    this.paperImg.draggable = false;

    this.labelPane = document.createElement('div');
    this.labelPane.className = 'sh2-label-pane';

    this.trailSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    this.trailSvg.setAttribute('class', 'sh2-trail-svg');
    this.trailSvg.setAttribute('viewBox', '0 0 2048 2048');
    this.trailSvg.hidden = true;
    this.trailLine = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    this.trailLine.setAttribute('class', 'sh2-trail-line');
    this.trailSvg.appendChild(this.trailLine);

    this.redPenPane = document.createElement('div');
    this.redPenPane.className = 'sh2-redpen-pane';

    this.markerPane = document.createElement('div');
    this.markerPane.className = 'sh2-marker-pane';

    this.stage.append(this.paperImg, this.labelPane, this.trailSvg, this.redPenPane);
    this.el.append(this.stage, this.markerPane);

    var self = this;
    this.el.addEventListener('wheel', function (e) {
      e.preventDefault();
      self._cancelAnims();
      var delta = e.deltaY < 0 ? 0.28 : -0.28;
      self.zoomAtClient(e.clientX, e.clientY, self.zoom + delta);
    }, { passive: false });

    this.el.addEventListener('dblclick', function (e) {
      if (e.target.closest('.sh2-pin-marker')) return;
      self._cancelAnims();
      self.zoomAtClient(e.clientX, e.clientY, self.zoom + 0.65);
    });

    this.el.addEventListener('pointerdown', function (e) {
      if (e.target.closest('.sh2-pin-marker')) return;
      if (e.button !== 0 && e.pointerType === 'mouse') return;
      e.preventDefault();
      self._cancelAnims();
      try { self.el.setPointerCapture(e.pointerId); } catch (err) {}
      self.pointers.set(e.pointerId, [e.clientX, e.clientY]);
      if (self.pointers.size > 1) self._wasMulti = true;
      else if (self.pointers.size === 1) self._wasMulti = false;
      self._vel = { vx: 0, vy: 0, lastX: e.clientX, lastY: e.clientY, lastT: performance.now() };
      self.el.classList.add('is-dragging');
      self._beginGesture();
    });

    this.el.addEventListener('pointermove', function (e) {
      if (!self.pointers.has(e.pointerId) || !self.drag) return;
      self.pointers.set(e.pointerId, [e.clientX, e.clientY]);
      var pts = Array.from(self.pointers.values());
      var d = self.drag;
      var mid = pts.length > 1 ? [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2] : pts[0];
      var dx = mid[0] - d.mid[0];
      var dy = mid[1] - d.mid[1];
      if (!self.moved && Math.hypot(dx, dy) > 3) {
        self.moved = true;
        self.emit('dragstart');
      }
      if (pts.length === 1) {
        var now = performance.now();
        var dt = now - self._vel.lastT;
        if (dt > 4 && dt < 90) {
          var instVx = (e.clientX - self._vel.lastX) / dt;
          var instVy = (e.clientY - self._vel.lastY) / dt;
          self._vel.vx = self._vel.vx * 0.45 + instVx * 0.55;
          self._vel.vy = self._vel.vy * 0.45 + instVy * 0.55;
        }
        self._vel.lastX = e.clientX;
        self._vel.lastY = e.clientY;
        self._vel.lastT = now;
      } else {
        self._vel.vx = 0;
        self._vel.vy = 0;
      }

      var nextZoom = d.zoom;
      if (pts.length > 1 && d.dist > 8) {
        var curDist = Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]);
        nextZoom = d.zoom + Math.log2(Math.max(curDist, 8) / d.dist);
      }
      self.zoom = Math.max(self.minZoom, Math.min(self.maxZoom, nextZoom));
      var scale = Math.pow(2, self.zoom);
      var rect = self.el.getBoundingClientRect();
      var midLocalX = mid[0] - rect.left - rect.width / 2;
      var midLocalY = mid[1] - rect.top - rect.height / 2;
      self.center = [
        self._clampCoord(d.anchorSheet[0] - midLocalX / scale),
        self._clampCoord(d.anchorSheet[1] - midLocalY / scale)
      ];
      self.draw();
    });

    function onUp(e) {
      if (!self.pointers.has(e.pointerId)) return;
      self.pointers.delete(e.pointerId);
      if (self.pointers.size > 0) {
        self._beginGesture();
      } else {
        self.drag = null;
        self.el.classList.remove('is-dragging');
        var freshVel = (performance.now() - self._vel.lastT) < 85;
        if (self.moved && !self._wasMulti && freshVel) {
          var speed = Math.hypot(self._vel.vx, self._vel.vy);
          if (speed > 0.14) {
            self._startInertia(self._vel.vx, self._vel.vy);
          }
        }
        if (!self.moved && !self._wasMulti) {
          if (e.pointerType !== 'mouse') {
            var now = performance.now();
            var dt = now - self._lastTap.t;
            var dist = Math.hypot(e.clientX - self._lastTap.x, e.clientY - self._lastTap.y);
            if (dt > 0 && dt < 300 && dist < 28) {
              self._lastTap.t = 0;
              var nextZ = self.zoom >= self.maxZoom - 0.35 ? Math.max(self.minZoom, self.zoom - 1.1) : Math.min(self.maxZoom, self.zoom + 0.85);
              self._flyZoomAt(e.clientX, e.clientY, nextZ, 220);
              return;
            }
            self._lastTap = { t: now, x: e.clientX, y: e.clientY };
          }
          self.emit('mapclick', e);
        }
      }
    }
    this.el.addEventListener('pointerup', onUp);
    this.el.addEventListener('pointercancel', onUp);
    window.addEventListener('resize', function () { self.draw(); });
  }

  PaperMapView.prototype._cancelAnims = function () {
    if (this._inertiaRaf) { cancelAnimationFrame(this._inertiaRaf); this._inertiaRaf = 0; }
    if (this._flyRaf) { cancelAnimationFrame(this._flyRaf); this._flyRaf = 0; }
  };

  PaperMapView.prototype._startInertia = function (vx0, vy0) {
    var self = this;
    var cap = 2.4;
    var sp = Math.hypot(vx0, vy0);
    var vx = sp > cap ? (vx0 / sp) * cap : vx0;
    var vy = sp > cap ? (vy0 / sp) * cap : vy0;
    var prevT = performance.now();

    function step(now) {
      var dt = Math.min(34, Math.max(4, now - prevT));
      prevT = now;
      var decay = Math.pow(0.90, dt / 16.0);
      vx *= decay;
      vy *= decay;
      var scale = Math.pow(2, self.zoom);
      self.center = [
        self._clampCoord(self.center[0] - (vx * dt) / scale),
        self._clampCoord(self.center[1] - (vy * dt) / scale)
      ];
      self.draw();
      if (Math.hypot(vx, vy) > 0.04) {
        self._inertiaRaf = requestAnimationFrame(step);
      } else {
        self._inertiaRaf = 0;
      }
    }
    this._inertiaRaf = requestAnimationFrame(step);
  };

  PaperMapView.prototype._flyZoomAt = function (clientX, clientY, targetZoom, durationMs) {
    var rect = this.el.getBoundingClientRect();
    var ox = clientX - rect.left - rect.width / 2;
    var oy = clientY - rect.top - rect.height / 2;
    var oldScale = Math.pow(2, this.zoom);
    var sheetX = this.center[0] + ox / oldScale;
    var sheetY = this.center[1] + oy / oldScale;
    var z = Math.max(this.minZoom, Math.min(this.maxZoom, targetZoom));
    var newScale = Math.pow(2, z);
    var targetCenter = [
      this._clampCoord(sheetX - ox / newScale),
      this._clampCoord(sheetY - oy / newScale)
    ];
    this.flyTo(targetCenter, z, durationMs || 220);
  };

  PaperMapView.prototype.flyTo = function (pxPair, targetZoom, durationMs) {
    this._cancelAnims();
    var dur = Math.max(80, durationMs || 260);
    var startCenter = [this.center[0], this.center[1]];
    var startZoom = this.zoom;
    var endCenter = (pxPair && pxPair.length === 2)
      ? [this._clampCoord(Number(pxPair[0])), this._clampCoord(Number(pxPair[1]))]
      : startCenter;
    var endZoom = (targetZoom != null && Number.isFinite(targetZoom))
      ? Math.max(this.minZoom, Math.min(this.maxZoom, targetZoom))
      : startZoom;
    var t0 = performance.now();
    var self = this;

    function tick(now) {
      var u = Math.min(1, (now - t0) / dur);
      var e = 1 - Math.pow(1 - u, 3);
      self.center = [
        startCenter[0] + (endCenter[0] - startCenter[0]) * e,
        startCenter[1] + (endCenter[1] - startCenter[1]) * e
      ];
      self.zoom = startZoom + (endZoom - startZoom) * e;
      self.draw();
      if (u < 1) {
        self._flyRaf = requestAnimationFrame(tick);
      } else {
        self._flyRaf = 0;
      }
    }
    this._flyRaf = requestAnimationFrame(tick);
    return this;
  };

  PaperMapView.prototype._clampCoord = function (v) {
    return Math.max(-256, Math.min(SHEET_SIZE + 256, v));
  };

  PaperMapView.prototype._beginGesture = function () {
    var pts = Array.from(this.pointers.values());
    var mid = pts.length > 1 ? [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2] : pts[0];
    var rect = this.el.getBoundingClientRect();
    var scale = Math.pow(2, this.zoom);
    var anchorSheet = [
      this.center[0] + (mid[0] - rect.left - rect.width / 2) / scale,
      this.center[1] + (mid[1] - rect.top - rect.height / 2) / scale
    ];
    this.drag = {
      zoom: this.zoom,
      mid: mid,
      anchorSheet: anchorSheet,
      dist: pts.length > 1 ? Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]) : 0
    };
    this.moved = false;
  };

  PaperMapView.prototype.on = function (name, fn) {
    (this.events[name] || (this.events[name] = [])).push(fn);
    return this;
  };

  PaperMapView.prototype.emit = function (name, arg) {
    (this.events[name] || []).forEach(function (fn) { fn(arg); });
  };

  PaperMapView.prototype.setPaperUrl = function (url) {
    if (this.paperImg.getAttribute('data-url') !== url) {
      this.paperImg.setAttribute('data-url', url);
      this.paperImg.src = url;
    }
  };

  PaperMapView.prototype.setView = function (pxPair, zoom) {
    this._cancelAnims();
    if (pxPair && pxPair.length === 2) {
      this.center = [this._clampCoord(Number(pxPair[0])), this._clampCoord(Number(pxPair[1]))];
    }
    if (zoom != null && Number.isFinite(zoom)) {
      this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, zoom));
    }
    this.draw();
    return this;
  };

  PaperMapView.prototype.zoomIn = function () {
    this._cancelAnims();
    return this.setView(this.center, this.zoom + 0.4);
  };

  PaperMapView.prototype.zoomOut = function () {
    this._cancelAnims();
    return this.setView(this.center, this.zoom - 0.4);
  };

  PaperMapView.prototype.zoomAtClient = function (clientX, clientY, targetZoom) {
    var rect = this.el.getBoundingClientRect();
    var ox = clientX - rect.left - rect.width / 2;
    var oy = clientY - rect.top - rect.height / 2;
    var oldScale = Math.pow(2, this.zoom);
    var sheetX = this.center[0] + ox / oldScale;
    var sheetY = this.center[1] + oy / oldScale;
    this.zoom = Math.max(this.minZoom, Math.min(this.maxZoom, targetZoom));
    var newScale = Math.pow(2, this.zoom);
    this.center = [
      this._clampCoord(sheetX - ox / newScale),
      this._clampCoord(sheetY - oy / newScale)
    ];
    this.draw();
  };

  PaperMapView.prototype.fitSheet = function (padLeft, padTop, padRight, padBottom) {
    this._cancelAnims();
    var w = Math.max(160, this.el.clientWidth - (padLeft || 24) - (padRight || 24));
    var h = Math.max(160, this.el.clientHeight - (padTop || 88) - (padBottom || 28));
    var scale = Math.min(w / SHEET_SIZE, h / SHEET_SIZE);
    var z = Math.max(this.minZoom, Math.min(this.maxZoom, Math.log2(scale)));
    var shiftX = ((padLeft || 24) - (padRight || 24)) / (2 * Math.pow(2, z));
    var shiftY = ((padTop || 88) - (padBottom || 28)) / (2 * Math.pow(2, z));
    return this.setView([1024 - shiftX, 1024 - shiftY], z);
  };

  PaperMapView.prototype.setTrail = function (points, visible) {
    if (!visible || !Array.isArray(points) || points.length < 2) {
      this.trailSvg.hidden = true;
      this.trailLine.setAttribute('points', '');
      return;
    }
    var coords = [];
    for (var i = 0; i < points.length; i++) {
      coords.push(Number(points[i][0]).toFixed(1) + ',' + Number(points[i][1]).toFixed(1));
    }
    this.trailLine.setAttribute('points', coords.join(' '));
    this.trailSvg.hidden = false;
  };

  PaperMapView.prototype.setLabels = function (labels, visible) {
    this.labelPane.innerHTML = '';
    this.labelPane.hidden = !visible;
    if (!visible || !Array.isArray(labels)) return;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < labels.length; i++) {
      var lb = labels[i];
      var d = document.createElement('div');
      d.className = 'sh2-room-label';
      d.textContent = lb.text;
      var fsz = Math.max(13, Math.min(30, Math.round((lb.size || 15) * 1.25)));
      var rot = lb.angle ? ' rotate(' + lb.angle + 'deg)' : '';
      d.style.cssText = 'left:' + lb.px[0] + 'px;top:' + lb.px[1] + 'px;font-size:' + fsz + 'px;transform:translate(-50%,-50%)' + rot;
      frag.appendChild(d);
    }
    this.labelPane.appendChild(frag);
  };

  PaperMapView.prototype.setRedPenMarks = function (marks, mode) {
    this.redPenPane.innerHTML = '';
    if (mode === 'off' || !Array.isArray(marks)) {
      this.redPenPane.hidden = true;
      return;
    }
    this.redPenPane.hidden = false;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < marks.length; i++) {
      var m = marks[i];
      if (mode === 'save' && !m.in_save) continue;
      var wrap = document.createElement('div');
      wrap.className = 'sh2-redpen-item';
      var w = Math.max(16, m.size && m.size[0] ? m.size[0] : 44);
      var h = Math.max(16, m.size && m.size[1] ? m.size[1] : 44);
      var sx = m.flip && m.flip[0] ? -1 : 1;
      var sy = m.flip && m.flip[1] ? -1 : 1;
      var tf = 'translate(-50%,-50%)';
      if (m.angle) tf += ' rotate(' + m.angle + 'deg)';
      if (sx !== 1 || sy !== 1) tf += ' scale(' + sx + ',' + sy + ')';
      wrap.style.cssText = 'left:' + m.px[0] + 'px;top:' + m.px[1] + 'px;width:' + w + 'px;height:' + h + 'px;transform:' + tf + ';z-index:' + (10 + (m.z || 0));
      if (m.sprite) {
        var img = document.createElement('img');
        img.className = 'sh2-redpen-img' + (m.sprite.indexOf('Stroke') !== -1 ? ' is-stroke' : '');
        img.src = '/sh2-markers/' + encodeURIComponent(m.sprite) + '.png';
        img.alt = '';
        img.draggable = false;
        img.onerror = function () { this.hidden = true; };
        wrap.appendChild(img);
      }
      if (m.note) {
        var nt = document.createElement('div');
        nt.className = 'sh2-redpen-note' + (m.crossed ? ' is-crossed' : '');
        nt.textContent = m.note;
        wrap.appendChild(nt);
      }
      frag.appendChild(wrap);
    }
    this.redPenPane.appendChild(frag);
  };

  PaperMapView.prototype.clearMarkers = function () {
    this.markers = [];
    this.markerPane.innerHTML = '';
    this.draw();
  };

  PaperMapView.prototype.addMarker = function (pxPair, el, zOffset) {
    el.classList.add('sh2-pin-marker');
    el.style.zIndex = String(200 + (zOffset || 0));
    var entry = { px: [Number(pxPair[0]), Number(pxPair[1])], el: el, z: zOffset || 0 };
    this.markers.push(entry);
    this.markerPane.appendChild(el);
    this.draw();
    return entry;
  };

  PaperMapView.prototype.updateMarkerPos = function (entry, pxPair) {
    if (!entry) return;
    entry.px = [Number(pxPair[0]), Number(pxPair[1])];
    this.draw();
  };

  PaperMapView.prototype.draw = function () {
    if (this.pending) return;
    this.pending = true;
    var self = this;
    requestAnimationFrame(function () {
      self.pending = false;
      self._paint();
    });
  };

  PaperMapView.prototype._paint = function () {
    var w = this.el.clientWidth || window.innerWidth;
    var h = this.el.clientHeight || window.innerHeight;
    var scale = Math.pow(2, this.zoom);
    var left = w / 2 - this.center[0] * scale;
    var top = h / 2 - this.center[1] * scale;
    this.stage.style.transform = 'translate3d(' + left.toFixed(2) + 'px,' + top.toFixed(2) + 'px,0) scale(' + scale.toFixed(5) + ')';

    for (var i = 0; i < this.markers.length; i++) {
      var m = this.markers[i];
      var sx = left + m.px[0] * scale;
      var sy = top + m.px[1] * scale;
      m.el.style.left = sx.toFixed(1) + 'px';
      m.el.style.top = sy.toFixed(1) + 'px';
    }
  };

  window.SH2MapEngine = { PaperMapView: PaperMapView, SHEET_SIZE: SHEET_SIZE };
})();
