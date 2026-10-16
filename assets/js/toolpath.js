/* ==========================================================================
   Toolpath — the home page hero.
   A vessel is generated from a handful of rules (profile + surface rule),
   turned into ONE continuous spiral toolpath (like vase-mode clay printing)
   and "printed" live, layer by layer. Click or press the button for a new form.
   ========================================================================== */
(() => {
  const canvas = document.querySelector('[data-toolpath]');
  if (!canvas) return;
  const ctx = canvas.getContext('2d', { alpha: true });
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const out = (k) => document.querySelector(`[data-r="${k}"]`);
  const elForm = out('form'), elLayer = out('layer'), elPath = out('path'), elG = out('gcode');

  const INK = '236,231,222';
  const EMBER = '255,90,31';
  const HEIGHT_MM = 320; // printed height the readout pretends to

  let W = 0, H = 0, DPR = 1, small = false;
  let form = null, progress = 0, doneAt = 0, seed = 0;
  let rotY = 0.6, tilt = 0.32, tRotX = 0, tTilt = 0.32, ptrX = 0;
  let running = false, visible = true, raf = 0, last = 0, frame = 0;

  /* ---------- seeded random ---------- */
  const rng = (a) => () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

  /* ---------- surface rules (nods to the collections) ---------- */
  const FAMILIES = [
    { code: 'T', name: 'tornado', mod: (p) => (th, t) => p.A * Math.sin(p.m * th + p.tw * t * Math.PI * 2) },
    { code: 'W', name: 'wave', mod: (p) => (th, t) => p.A * Math.sin(p.k * t * Math.PI * 2 + 2.2 * Math.sin(p.m * th)) * (0.55 + 0.45 * Math.sin(t * Math.PI)) },
    { code: 'D', name: 'dash', mod: (p) => (th, t) => { const band = Math.floor(t * p.k); return p.A * Math.tanh(5 * Math.sin(p.m * th + (band % 2) * Math.PI / p.m)) * (band % 3 === 0 ? 0.25 : 1); } },
    { code: 'L', name: 'lattice', mod: (p) => (th, t) => p.A * 1.3 * Math.sin(p.m * th + p.k * t * Math.PI * 2) * Math.sin(p.m * th - p.k * t * Math.PI * 2) },
  ];

  function makeForm(s) {
    const r = rng(s * 9973 + 17);
    const fam = FAMILIES[s % FAMILIES.length];
    const layers = small ? 96 : 150;
    const seg = small ? 90 : 132;
    const p = {
      A: 0.016 + r() * 0.02,
      m: [7, 9, 11, 12, 14, 16][Math.floor(r() * 6)],
      k: 4 + Math.floor(r() * 6),
      tw: (r() < 0.5 ? -1 : 1) * (0.5 + r() * 1.1),
    };
    const r0 = 0.2 + r() * 0.05;
    const belly = 0.25 + r() * 0.45;
    const pw = 0.6 + r() * 1.1; // where the belly sits
    const neck = 0.18 + r() * 0.3;
    const flare = r() * 0.25;
    const profile = (t) => {
      const b = Math.sin(Math.PI * Math.pow(t, pw));
      return r0 * (1 + belly * b - neck * smooth(0.72, 1, t) + flare * smooth(0.9, 1, t)) * (0.82 + 0.18 * smooth(0, 0.08, t));
    };
    const mod = fam.mod(p);
    const N = layers * seg;
    const pts = new Float32Array(N * 3);
    const cum = new Float32Array(N); // cumulative path length (normalised units)
    let len = 0;
    for (let i = 0; i < N; i++) {
      const t = i / N;
      const th = (i % seg) / seg * Math.PI * 2;
      const rad = Math.max(0.04, profile(t) + mod(th, t));
      const x = rad * Math.cos(th), z = rad * Math.sin(th), y = t - 0.5;
      pts[i * 3] = x; pts[i * 3 + 1] = y; pts[i * 3 + 2] = z;
      if (i) { const dx = x - pts[i * 3 - 3], dy = y - pts[i * 3 - 2], dz = z - pts[i * 3 - 1]; len += Math.hypot(dx, dy, dz); }
      cum[i] = len;
    }
    const bits = (s % 16).toString(2).padStart(4, '0');
    return { pts, cum, N, layers, seg, code: `${fam.code}-${bits}`, name: fam.name };
  }

  /* ---------- layout ---------- */
  function resize() {
    DPR = Math.min(2, devicePixelRatio || 1);
    const r = canvas.getBoundingClientRect();
    W = r.width; H = r.height;
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const wasSmall = small;
    small = W < 900;
    if (!form || wasSmall !== small) { form = makeForm(seed); if (reduce) progress = form.N; }
    if (!running) draw();
  }

  /* ---------- render ---------- */
  const BUCKETS = 6;
  const paths = Array.from({ length: BUCKETS }, () => new Path2D());
  function draw() {
    ctx.clearRect(0, 0, W, H);
    if (!form) return;
    const { pts, N } = form;
    const cx = small ? W * 0.5 : W * 0.735;
    const cy = small ? H * 0.3 : H * 0.5;
    const scale = small ? Math.min(H * 0.42, W * 0.95) : Math.min(H * 0.74, W * 0.42);
    const f = 3.2;
    const cr = Math.cos(rotY), sr = Math.sin(rotY), ct = Math.cos(tilt), st = Math.sin(tilt);
    const count = Math.min(N, Math.floor(progress));
    const proj = (x, y, z) => {
      const x1 = x * cr - z * sr, z1 = x * sr + z * cr;
      const y2 = y * ct - z1 * st, z2 = y * st + z1 * ct;
      const s = f / (f + z2);
      return [cx + x1 * s * scale, cy - y2 * s * scale, z2];
    };

    // build plate
    ctx.lineWidth = 1;
    ctx.strokeStyle = `rgba(${INK},.10)`;
    ctx.setLineDash([2, 6]);
    ctx.beginPath();
    for (let a = 0; a <= 64; a++) {
      const th = a / 64 * Math.PI * 2;
      const [px, py] = proj(Math.cos(th) * 0.48, -0.5, Math.sin(th) * 0.48);
      a ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // toolpath, bucketed by depth so the far side reads fainter
    for (let b = 0; b < BUCKETS; b++) paths[b] = new Path2D();
    let prev = null, prevB = -1;
    for (let i = 0; i < count; i++) {
      const p = proj(pts[i * 3], pts[i * 3 + 1], pts[i * 3 + 2]);
      const b = Math.max(0, Math.min(BUCKETS - 1, Math.floor((p[2] + 0.42) / 0.84 * BUCKETS)));
      if (prev) {
        const path = paths[b];
        if (b !== prevB) path.moveTo(prev[0], prev[1]);
        path.lineTo(p[0], p[1]);
      }
      prev = p; prevB = b;
    }
    const lw = small ? 0.7 : 0.8;
    for (let b = 0; b < BUCKETS; b++) {
      const a = 0.9 - (b / (BUCKETS - 1)) * 0.8; // near = bright
      ctx.strokeStyle = `rgba(${INK},${(a * (small ? 0.5 : 1)).toFixed(3)})`;
      ctx.lineWidth = lw;
      ctx.stroke(paths[b]);
    }

    // nozzle
    if (count > 0 && count < N) {
      const [hx, hy] = prev;
      ctx.strokeStyle = `rgba(${EMBER},.35)`;
      ctx.beginPath(); ctx.moveTo(hx, hy - 8); ctx.lineTo(hx, 0); ctx.stroke();
      ctx.strokeStyle = `rgba(${INK},.12)`;
      ctx.beginPath(); ctx.moveTo(hx - 40, hy); ctx.lineTo(hx + 40, hy); ctx.stroke();
      const g = ctx.createRadialGradient(hx, hy, 0, hx, hy, 18);
      g.addColorStop(0, `rgba(${EMBER},.9)`); g.addColorStop(1, `rgba(${EMBER},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(hx, hy, 18, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = `rgb(${EMBER})`; ctx.beginPath(); ctx.arc(hx, hy, 2.2, 0, Math.PI * 2); ctx.fill();
    }
  }

  function readout() {
    if (!form || !elForm) return;
    const i = Math.max(0, Math.min(form.N - 1, Math.floor(progress) - 1));
    const layer = Math.floor(i / form.seg) + 1;
    elForm.textContent = form.code;
    elLayer.textContent = `${String(layer).padStart(3, '0')} / ${form.layers}`;
    elPath.textContent = `${(form.cum[i] * HEIGHT_MM / 1000).toFixed(2)} m`;
    const x = form.pts[i * 3] * HEIGHT_MM, y = form.pts[i * 3 + 2] * HEIGHT_MM, z = (form.pts[i * 3 + 1] + 0.5) * HEIGHT_MM;
    elG.textContent = progress >= form.N ? `M84 ; ${form.name} complete` : `G1 X${x.toFixed(2)} Y${y.toFixed(2)} Z${z.toFixed(2)} E${(form.cum[i] * 0.42).toFixed(3)}`;
  }

  /* ---------- loop ---------- */
  function step(now) {
    raf = 0;
    if (!running) return;
    const dt = Math.min(0.05, (now - (last || now)) / 1000);
    last = now;
    if (progress < form.N) {
      progress += form.N * dt / (small ? 6.5 : 8.5); // full print in ~8s
      if (progress >= form.N) { progress = form.N; doneAt = now; }
    } else if (now - doneAt > 16000) {
      newForm();
    }
    rotY += dt * 0.22;
    tilt += (tTilt - tilt) * 0.05;
    ptrX += (tRotX - ptrX) * 0.05;
    const keep = rotY;
    rotY = keep + ptrX;
    draw();
    rotY = keep;
    if (++frame % 3 === 0 || progress >= form.N) readout();
    raf = requestAnimationFrame(step);
  }
  function start() { if (running || reduce) return; running = true; last = 0; raf = requestAnimationFrame(step); }
  function stop() { running = false; if (raf) cancelAnimationFrame(raf); raf = 0; }

  function newForm() {
    seed = (seed + 1 + Math.floor(Math.random() * 7)) % 4096;
    form = makeForm(seed);
    progress = reduce ? form.N : 0;
    doneAt = 0;
    if (reduce) { draw(); readout(); }
  }

  /* ---------- input ---------- */
  canvas.addEventListener('pointermove', (e) => {
    const r = canvas.getBoundingClientRect();
    tRotX = ((e.clientX - r.left) / r.width - 0.5) * 0.9;
    tTilt = 0.18 + ((e.clientY - r.top) / r.height) * 0.36;
  }, { passive: true });
  canvas.addEventListener('pointerleave', () => { tRotX = 0; tTilt = 0.32; });
  canvas.addEventListener('click', newForm);
  document.querySelector('[data-new-form]')?.addEventListener('click', newForm);

  new IntersectionObserver(([e]) => { visible = e.isIntersecting; visible && !document.hidden ? start() : stop(); }, { threshold: 0.02 }).observe(canvas);
  document.addEventListener('visibilitychange', () => { document.hidden ? stop() : visible && start(); });
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(resize, 120); });

  seed = Math.floor(Math.random() * 4096);
  resize();
  if (reduce) { progress = form.N; draw(); readout(); } else { start(); }
})();
