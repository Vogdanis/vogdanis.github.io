/* vogdanis.com — site behaviour. No dependencies. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---- nav: solid on scroll, hide on scroll down ---- */
  const nav = $('[data-nav]');
  let lastY = scrollY;
  const onScroll = () => {
    const y = scrollY;
    nav.classList.toggle('is-scrolled', y > 24);
    const menuOpen = !$('[data-menu]').hidden;
    nav.classList.toggle('is-hidden', !menuOpen && y > 400 && y > lastY + 4);
    if (y < lastY - 4 || y < 400) nav.classList.remove('is-hidden');
    lastY = y;
  };
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- mobile menu ---- */
  const toggle = $('[data-menu-toggle]');
  const menu = $('[data-menu]');
  const setMenu = (open) => {
    menu.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Close' : 'Menu';
    document.body.style.overflow = open ? 'hidden' : '';
  };
  toggle.addEventListener('click', () => setMenu(menu.hidden));
  menu.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) setMenu(false); });

  /* ---- reveal on scroll ---- */
  const revealIO = new IntersectionObserver((entries) => {
    entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add('is-in'); revealIO.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
  $$('.reveal').forEach((el) => revealIO.observe(el));

  /* ---- videos: load + play only while visible ---- */
  const vids = $$('video[data-autoplay]');
  const onScreen = new Set();
  const play = (v) => {
    if (reduce) return;
    if (v.preload === 'none') v.preload = 'auto';
    const p = v.play(); if (p && p.catch) p.catch(() => {});
  };
  const vidIO = new IntersectionObserver((entries) => {
    entries.forEach(({ target: v, isIntersecting }) => {
      if (isIntersecting) { onScreen.add(v); play(v); } else { onScreen.delete(v); v.pause(); }
    });
  }, { threshold: 0.15 });
  vids.forEach((v) => { v.muted = true; vidIO.observe(v); });
  // pause in background tabs; resume what's on screen when the tab comes back
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) vids.forEach((v) => v.pause()); else onScreen.forEach(play);
  });
  // coming "back" restores the page from the browser's cache with every video paused
  addEventListener('pageshow', (e) => { if (e.persisted) onScreen.forEach(play); });

  /* ---- email: assembled client-side to keep scrapers out ---- */
  $$('.mail[data-u]').forEach((a) => {
    const addr = `${a.dataset.u}@${a.dataset.d}`;
    a.href = `mailto:${addr}${a.dataset.subject ? `?subject=${encodeURIComponent(a.dataset.subject)}` : ''}`;
    if (!a.classList.contains('btn')) a.textContent = addr;
  });

  /* ---- Athens clock ---- */
  const clock = $('[data-clock]');
  if (clock) {
    const fmt = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Athens', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const tick = () => { clock.textContent = fmt.format(new Date()); };
    tick(); setInterval(tick, 1000);
  }

  /* ---- cursor label ---- */
  const cur = $('[data-cursor]');
  if (cur && finePointer && !reduce) {
    const label = cur.firstElementChild;
    let x = 0, y = 0, cx = 0, cy = 0, raf = 0;
    const loop = () => { cx += (x - cx) * 0.22; cy += (y - cy) * 0.22; cur.style.transform = `translate3d(${cx}px, ${cy}px, 0)`; raf = requestAnimationFrame(loop); };
    addEventListener('pointermove', (e) => { x = e.clientX; y = e.clientY; if (!raf) { cx = x; cy = y; loop(); } }, { passive: true });
    document.addEventListener('pointerover', (e) => {
      const t = e.target.closest('[data-cursor-label]');
      if (t) { label.textContent = t.dataset.cursorLabel; cur.classList.add('is-on'); } else { cur.classList.remove('is-on'); }
    });
  }

  /* ---- archive: filter + floating preview ---- */
  const filters = $('[data-filters]');
  if (filters) {
    const rows = $$(filters.dataset.target || '[data-archive] .arch__row');
    filters.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      $$('button', filters).forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      const f = b.dataset.filter;
      rows.forEach((r) => { r.hidden = f !== '*' && !r.dataset.tags.split(',').includes(f); });
    });
  }
  const peek = $('[data-peek-el]');
  if (peek && finePointer) {
    const img = $('img', peek);
    let px = 0, py = 0, tx = 0, ty = 0, on = false, raf = 0;
    const loop = () => { px += (tx - px) * 0.16; py += (ty - py) * 0.16; peek.style.transform = `translate3d(${px + 40}px, ${py - 120}px, 0)`; raf = on ? requestAnimationFrame(loop) : 0; };
    $$('[data-peek]').forEach((a) => {
      a.addEventListener('pointerenter', (e) => {
        img.src = a.dataset.peek; img.style.aspectRatio = a.dataset.peekRatio;
        tx = e.clientX; ty = e.clientY; if (!on) { px = tx; py = ty; }
        on = true; peek.classList.add('is-on'); if (!raf) loop();
      });
      a.addEventListener('pointermove', (e) => { tx = e.clientX; ty = e.clientY; });
      a.addEventListener('pointerleave', () => { on = false; peek.classList.remove('is-on'); });
    });
  }

  /* ---- YouTube: load on click ---- */
  $$('[data-yt]').forEach((box) => {
    $('button', box).addEventListener('click', () => {
      const f = document.createElement('iframe');
      f.src = `https://www.youtube-nocookie.com/embed/${box.dataset.yt}?autoplay=1&rel=0&modestbranding=1`;
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true; f.title = 'Video';
      box.replaceChildren(f);
    });
  });

  /* ---- lightbox ---- */
  const dlg = $('[data-lightbox-dialog]');
  const triggers = $$('[data-lightbox], .machines img');
  if (dlg && triggers.length) {
    const im = $('img', dlg), cap = $('.lightbox__cap', dlg);
    let i = 0;
    const show = (n) => {
      i = (n + triggers.length) % triggers.length;
      const src = triggers[i].querySelector('img') || triggers[i];
      im.src = src.dataset.full || src.currentSrc || src.src;
      im.alt = src.alt || '';
      const fc = triggers[i].closest('figure')?.querySelector('figcaption');
      cap.textContent = `${String(i + 1).padStart(2, '0')} / ${String(triggers.length).padStart(2, '0')}${fc ? '  ·  ' + fc.textContent : ''}`;
    };
    triggers.forEach((t, n) => t.addEventListener('click', () => { show(n); dlg.showModal(); }));
    $('[data-close]', dlg).addEventListener('click', () => dlg.close());
    $('[data-prev]', dlg).addEventListener('click', () => show(i - 1));
    $('[data-next]', dlg).addEventListener('click', () => show(i + 1));
    dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') show(i - 1); if (e.key === 'ArrowRight') show(i + 1); });
    let sx = 0;
    dlg.addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; }, { passive: true });
    dlg.addEventListener('touchend', (e) => { const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1)); });
  }
})();
