/* peterstieg.com – no tracking, no cookies, no framework. */
(() => {
  const root = document.documentElement;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("js");

  /* ---------- Theme: follows the system until the visitor picks one; the pick is remembered locally. */
  const mqDark = window.matchMedia("(prefers-color-scheme: dark)");
  const COLORS = { light: "#F7F6F3", dark: "#181A1C" };
  const stored = () => { try { return localStorage.getItem("theme"); } catch (_) { return null; } };
  const effective = () => root.getAttribute("data-theme") || (mqDark.matches ? "dark" : "light");
  const paintTheme = () => {
    const now = effective();
    document.querySelectorAll("[data-theme-set]").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.themeSet === now)));
    if (root.hasAttribute("data-theme")) {
      document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute("content", COLORS[now]));
    }
  };
  document.querySelectorAll("[data-theme-set]").forEach((b) => b.addEventListener("click", () => {
    const val = b.dataset.themeSet;
    root.setAttribute("data-theme", val);
    try { localStorage.setItem("theme", val); } catch (_) { /* private mode: the choice lasts for this page */ }
    paintTheme();
  }));
  const s0 = stored();
  if ((s0 === "light" || s0 === "dark") && !root.hasAttribute("data-theme")) root.setAttribute("data-theme", s0);
  mqDark.addEventListener("change", paintTheme);
  paintTheme();

  /* ---------- Prompt: types the motto once. Full text stays in the HTML for no-JS and screen readers. */
  const cmd = document.querySelector(".hero .prompt .cmd");
  if (cmd) {
    const full = cmd.textContent;
    if (reduce) {
      root.classList.add("typed");
    } else {
      cmd.textContent = "";
      let i = 0;
      const step = () => {
        cmd.textContent = full.slice(0, ++i);
        if (i < full.length) setTimeout(step, 45 + Math.random() * 70);
        else root.classList.add("typed");
      };
      setTimeout(step, 600);
    }
  }

  /* ---------- Header hairline once the page scrolls. */
  const top = document.querySelector(".top");
  const onScrollTop = () => top && top.classList.toggle("scrolled", window.scrollY > 8);

  /* ---------- Docking: PETER STIEG and >_ travel from the hero into the header logo while scrolling.
     The name is visible exactly once. Scrubbed by scroll position, so scrolling up reverses it. */
  const hero = document.querySelector(".hero");
  const home = top && top.querySelector(".home");
  const pairs = hero && home ? [
    { src: hero.querySelector("h1"), dst: home.querySelector(".name") },
    { src: hero.querySelector(".prompt .caret"), dst: home.querySelector(".caret") },
  ].filter((p) => p.src && p.dst) : [];
  const fades = hero ? [...hero.querySelectorAll(".prompt .cmd, .prompt .cursor")] : [];
  let dist = 0, mode = "off";

  const textRects = (el) => {
    const r = document.createRange();
    r.selectNodeContents(el);
    return [...r.getClientRects()].filter((x) => x.width && x.height);
  };
  const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

  const dockClear = () => {
    pairs.forEach((p) => { p.src.style.transform = ""; p.src.style.transformOrigin = ""; });
    fades.forEach((f) => { f.style.opacity = ""; });
  };

  const dockMeasure = () => {
    if (pairs.length !== 2) return;
    top.classList.add("dock");
    dockClear();
    const sy = window.scrollY;
    const headerBottom = top.getBoundingClientRect().bottom;
    mode = reduce ? "swap" : "fly";
    for (const p of pairs) {
      const sr = textRects(p.src), dr = textRects(p.dst);
      if (sr.length !== 1 || dr.length !== 1) { mode = "swap"; }
      const a = sr[0] || p.src.getBoundingClientRect(), b = dr[0] || p.dst.getBoundingClientRect();
      const box = p.src.getBoundingClientRect();
      p.ox = a.left - box.left; p.oy = a.top - box.top;      // text origin inside the element box
      p.x0 = a.left; p.y0 = a.top + sy;                       // document coordinates
      p.x1 = b.left; p.y1 = b.top;                            // screen coordinates (sticky header)
      p.k = b.height / a.height;
      p.bottom = a.bottom + sy;
    }
    const name = pairs[0];
    dist = Math.min(400, Math.max(120, name.y0 - headerBottom + 40));
    if (mode === "swap") dist = Math.max(0, name.bottom - headerBottom);
  };

  const dockApply = () => {
    if (mode === "off") return;
    const sy = window.scrollY;
    const done = sy >= dist;
    top.classList.toggle("docked", done);
    if (mode === "swap") return;
    hero.classList.toggle("docked", done);
    const q = ease(Math.min(1, Math.max(0, sy / dist)));
    hero.classList.toggle("flying", q > 0 && !done);
    for (const p of pairs) {
      const dx = (p.x1 - p.x0) * q;
      const dy = (p.y1 - p.y0) * q + sy;
      const sc = 1 + (p.k - 1) * q;
      p.src.style.transformOrigin = `${p.ox}px ${p.oy}px`;
      p.src.style.transform = q ? `translate(${dx}px, ${dy}px) scale(${sc})` : "";
    }
    const o = Math.max(0, 1 - q * 1.8);
    fades.forEach((f) => { f.style.opacity = q ? String(o) : ""; });
  };

  /* ---------- Minimap: the page drawn as code lines, like the LinkedIn banner – click or drag to navigate. */
  const rail = document.querySelector(".minimap");
  const main = document.querySelector("main");
  let bars = [], view = null, scale = 1;

  const build = () => {
    if (!rail || !main) return;
    rail.replaceChildren();
    bars = [];
    if (getComputedStyle(rail).display === "none") return;

    const docH = root.scrollHeight;
    const H = rail.clientHeight, W = rail.clientWidth;
    scale = H / docH;
    const box = main.getBoundingClientRect();
    const frag = document.createDocumentFragment();

    const SEL = "h1, h2, h3, h4, p, li, dt, dd";
    main.querySelectorAll(SEL).forEach((el) => {
      if (el.querySelector(SEL)) return;              // leaf text blocks only
      if (!el.textContent.trim()) return;
      const range = document.createRange();
      range.selectNodeContents(el);
      const lines = [];                               // one bar per rendered line
      for (const r of range.getClientRects()) {
        if (!r.width || !r.height) continue;
        const l = lines.find((x) => Math.abs(x.top - r.top) < r.height / 2);
        if (l) { l.left = Math.min(l.left, r.left); l.right = Math.max(l.right, r.right); l.h = Math.max(l.h, r.height); }
        else lines.push({ top: r.top, left: r.left, right: r.right, h: r.height });
      }
      const isHead = /^H[12]$/.test(el.tagName);
      for (const l of lines) {
        const x = Math.max(0, ((l.left - box.left) / box.width) * W);
        const w = Math.max(3, ((l.right - l.left) / box.width) * W);
        const y = (l.top + window.scrollY + l.h / 2) * scale;
        const thick = Math.max(2, Math.min(isHead ? 7 : 3, l.h * scale * 0.55));
        const b = document.createElement("span");
        b.className = "mm-bar" + (isHead ? " h" : "");
        b.style.cssText = `top:${(y - thick / 2).toFixed(1)}px;left:${x.toFixed(1)}px;width:${Math.min(W - x, w).toFixed(1)}px;height:${thick.toFixed(1)}px`;
        frag.appendChild(b);
        bars.push({ el: b, y });
      }
    });

    view = document.createElement("span");
    view.className = "mm-view";
    frag.appendChild(view);
    rail.appendChild(frag);
    paint();
  };

  const paint = () => {
    if (!view) return;
    const t = window.scrollY * scale, h = window.innerHeight * scale;
    view.style.top = t + "px";
    view.style.height = h + "px";
    for (const b of bars) b.el.classList.toggle("lit", b.y >= t && b.y <= t + h);
  };

  const jump = (clientY, smooth) => {
    const r = rail.getBoundingClientRect();
    const y = (clientY - r.top) / scale - window.innerHeight / 2;
    window.scrollTo({ top: Math.max(0, y), behavior: smooth && !reduce ? "smooth" : "auto" });
  };

  if (rail) {
    let dragging = false;
    rail.addEventListener("pointerdown", (e) => { dragging = true; rail.setPointerCapture(e.pointerId); jump(e.clientY, true); });
    rail.addEventListener("pointermove", (e) => { if (dragging) jump(e.clientY, false); });
    rail.addEventListener("pointerup", () => { dragging = false; });
    rail.addEventListener("pointercancel", () => { dragging = false; });
  }

  /* ---------- Wiring */
  const layout = () => { dockMeasure(); build(); dockApply(); };

  let raf = 0;
  window.addEventListener("scroll", () => {
    if (raf) return;
    raf = requestAnimationFrame(() => { raf = 0; paint(); onScrollTop(); dockApply(); });
  }, { passive: true });

  let rt = 0;
  window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(layout, 150); });

  onScrollTop();
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(layout);
  window.addEventListener("load", layout);

  /* {KeyWord:Developer}: Google Ads Dynamic Keyword Insertion – the default shows when nothing better matches. */
  console.log("%c>_ sudo dream plan ship", "color:#7A1A2C;font-weight:700;font-size:14px",
    "\nHi {KeyWord:Developer} – view-source counts as root access, too." +
    "\n\npeterstieg.com\n├── no tracking\n├── no cookies\n└── no framework");
})();
