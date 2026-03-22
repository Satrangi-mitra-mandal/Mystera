/* ═══════════════════════════════════════════════════════
   DetectiveOS — Evidence Board Engine
   Drag-and-drop pins, SVG wire connections, persistence
═══════════════════════════════════════════════════════ */

export class EvidenceBoard {
  constructor(canvasId, svgId, onSave) {
    this.canvas   = document.getElementById(canvasId);
    this.svg      = document.getElementById(svgId);
    this.onSave   = onSave || (() => {});
    this.pins     = [];     // { id, el, x, y, data }
    this.conns    = [];     // { from, to, color }
    this.tool     = 'select';
    this.connFrom = null;
    this.dragPin  = null;
    this.dragOX   = 0;
    this.dragOY   = 0;
    this.idSeq    = 1;
    this.dirty    = false;
    this._bindCanvas();
  }

  /* ── Tool ─────────────────────────────────────── */
  setTool(t) {
    this.tool = t;
    this.canvas.style.cursor = t === 'connect' ? 'crosshair' : 'default';
    if (this.connFrom) { this.connFrom.el.classList.remove('selected'); this.connFrom = null; }
  }

  /* ── Create pin ───────────────────────────────── */
  addPin(data, x, y) {
    const id   = 'pin-' + (this.idSeq++);
    const isSuspect = data.kind === 'suspect';
    const div  = document.createElement('div');
    div.className = 'board-pin' + (isSuspect ? ' suspect-pin' : '');
    div.id = id;
    div.style.left = x + 'px';
    div.style.top  = y + 'px';
    div.innerHTML  = `
      <div class="pin-tack"></div>
      <span class="pin-icon">${data.icon || '📄'}</span>
      <div class="pin-type">${data.type || ''}</div>
      <div class="pin-label">${data.label || data.title || ''}</div>
    `;
    div.addEventListener('mousedown', e => this._onPinDown(e, pin));
    div.addEventListener('touchstart', e => this._onPinTouch(e, pin), { passive: false });
    this.canvas.appendChild(div);
    const pin = { id, el: div, x, y, data };
    this.pins.push(pin);
    this.dirty = true;
    return pin;
  }

  removePin(pinId) {
    const idx = this.pins.findIndex(p => p.id === pinId);
    if (idx === -1) return;
    const pin = this.pins[idx];
    pin.el.remove();
    this.conns = this.conns.filter(c => c.from.id !== pinId && c.to.id !== pinId);
    this.pins.splice(idx, 1);
    this._redrawConns();
    this.dirty = true;
  }

  /* ── Connections ──────────────────────────────── */
  addConnection(pinA, pinB, color) {
    const exists = this.conns.find(c =>
      (c.from.id === pinA.id && c.to.id === pinB.id) ||
      (c.from.id === pinB.id && c.to.id === pinA.id)
    );
    if (exists) return;
    this.conns.push({ from: pinA, to: pinB, color: color || this._nextColor() });
    this._redrawConns();
    this.dirty = true;
  }

  clearConnections() {
    this.conns = [];
    this._redrawConns();
    this.dirty = true;
  }

  _connColors = ['#c8913a','#7aabff','#ff9a9a','#5ab87a','#f0c040','#c87aff'];
  _colorIdx = 0;
  _nextColor() { return this._connColors[(this._colorIdx++) % this._connColors.length]; }

  _redrawConns() {
    this.svg.innerHTML = '';
    for (const c of this.conns) {
      try {
        const cr = this.canvas.getBoundingClientRect();
        const ar = c.from.el.getBoundingClientRect();
        const br = c.to.el.getBoundingClientRect();
        const ax = ar.left - cr.left + ar.width  / 2;
        const ay = ar.top  - cr.top  + ar.height / 2;
        const bx = br.left - cr.left + br.width  / 2;
        const by = br.top  - cr.top  + br.height / 2;

        // Curved path
        const mx = (ax + bx) / 2;
        const my = (ay + by) / 2 - 20;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M${ax},${ay} Q${mx},${my} ${bx},${by}`);
        path.setAttribute('stroke', c.color);
        path.setAttribute('stroke-width', '1.5');
        path.setAttribute('stroke-dasharray', '6,3');
        path.setAttribute('fill', 'none');
        path.setAttribute('opacity', '0.65');
        this.svg.appendChild(path);
      } catch (_) {}
    }
  }

  /* ── Drag ─────────────────────────────────────── */
  _onPinDown(e, pin) {
    e.stopPropagation();
    if (this.tool === 'connect') {
      if (!this.connFrom) {
        this.connFrom = pin;
        pin.el.classList.add('selected');
      } else if (this.connFrom.id !== pin.id) {
        this.addConnection(this.connFrom, pin);
        this.connFrom.el.classList.remove('selected');
        this.connFrom = null;
      }
      return;
    }
    // select + drag
    this.pins.forEach(p => p.el.classList.remove('selected'));
    pin.el.classList.add('selected');
    const cr  = this.canvas.getBoundingClientRect();
    const pr  = pin.el.getBoundingClientRect();
    this.dragPin = pin;
    this.dragOX  = e.clientX - pr.left;
    this.dragOY  = e.clientY - pr.top;
    const move = ev => this._onDragMove(ev);
    const up   = () => { this.dragPin = null; document.removeEventListener('mousemove', move); document.removeEventListener('mouseup', up); };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  }

  _onPinTouch(e, pin) {
    e.preventDefault();
    const t = e.touches[0];
    const cr = this.canvas.getBoundingClientRect();
    const pr = pin.el.getBoundingClientRect();
    this.dragPin = pin;
    this.dragOX  = t.clientX - pr.left;
    this.dragOY  = t.clientY - pr.top;
    const move = ev => { const t = ev.touches[0]; this._movePin(pin, t.clientX, t.clientY); };
    const end  = () => { this.dragPin = null; document.removeEventListener('touchmove', move); document.removeEventListener('touchend', end); };
    document.addEventListener('touchmove', move, { passive: false });
    document.addEventListener('touchend', end);
  }

  _onDragMove(e) {
    if (!this.dragPin) return;
    this._movePin(this.dragPin, e.clientX, e.clientY);
  }

  _movePin(pin, cx, cy) {
    const cr  = this.canvas.getBoundingClientRect();
    const pw  = pin.el.offsetWidth;
    const ph  = pin.el.offsetHeight;
    const nx  = Math.max(0, Math.min(cx - cr.left - this.dragOX, cr.width  - pw));
    const ny  = Math.max(0, Math.min(cy - cr.top  - this.dragOY, cr.height - ph));
    pin.el.style.left = nx + 'px';
    pin.el.style.top  = ny + 'px';
    pin.x = nx; pin.y = ny;
    this._redrawConns();
    this.dirty = true;
  }

  _bindCanvas() {
    this.canvas.addEventListener('click', () => {
      if (this.tool === 'select') {
        this.pins.forEach(p => p.el.classList.remove('selected'));
      }
    });
    window.addEventListener('resize', () => this._redrawConns());
  }

  /* ── Serialise / restore ─────────────────────── */
  getState() {
    return {
      pins: this.pins.map(p => ({ id: p.id, x: p.x, y: p.y, data: p.data })),
      connections: this.conns.map(c => ({ from: c.from.id, to: c.to.id, color: c.color })),
      idSeq: this.idSeq,
    };
  }

  loadState(state) {
    if (!state || !state.pins) return;
    // Clear current
    this.pins.forEach(p => p.el.remove());
    this.pins = [];
    this.conns = [];
    this.svg.innerHTML = '';
    this.idSeq = state.idSeq || 1;

    for (const p of state.pins) {
      const pin = this.addPin(p.data, p.x, p.y);
      pin.id = p.id;
      pin.el.id = p.id;
    }
    for (const c of (state.connections || [])) {
      const from = this.pins.find(p => p.id === c.from);
      const to   = this.pins.find(p => p.id === c.to);
      if (from && to) this.conns.push({ from, to, color: c.color });
    }
    this._redrawConns();
    this.dirty = false;
  }
}
