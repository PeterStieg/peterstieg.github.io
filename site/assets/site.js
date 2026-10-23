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
  if (mqDark.addEventListener) mqDark.addEventListener("change", paintTheme);
  else mqDark.addListener(paintTheme);              // Safari before 14
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
        else { root.classList.add("typed"); layout(); }  // redraw the minimap with the full motto
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
    hero.classList.remove("docked", "flying");       // a resize may switch modes while docked
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

    root.classList.add("mm-measure");               // sticky headings report where they are stuck
    const SEL = "h1, h2, h3, h4, p, li, dt, dd";
    main.querySelectorAll(SEL).forEach((el) => {
      if (el.querySelector(SEL)) return;              // leaf text blocks only
      if (!el.textContent.trim()) return;
      const range = document.createRange();
      const rects = [];                               // text visible on screen only, no .sr-only copies
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.textContent.trim() || n.parentElement.closest(".sr-only, .ghost")) continue;
        range.selectNodeContents(n);
        rects.push(...range.getClientRects());
      }
      const lines = [];                               // one bar per rendered line
      for (const r of rects) {
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

    root.classList.remove("mm-measure");
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
    window.scrollTo({ top: Math.max(0, y), behavior: smooth && !reduce ? "smooth" : "instant" });
  };

  if (rail) {
    let dragging = false;
    rail.addEventListener("pointerdown", (e) => { dragging = true; rail.setPointerCapture(e.pointerId); jump(e.clientY, true); });
    rail.addEventListener("pointermove", (e) => { if (dragging) jump(e.clientY, false); });
    rail.addEventListener("pointerup", () => { dragging = false; });
    rail.addEventListener("pointercancel", () => { dragging = false; });
  }

  /* ---------- You are here: the menu marks the chapter being read, like a slide deck's header. */
  const marks = [...document.querySelectorAll(".nav .sect")]
    .map((a) => ({ a, sec: document.getElementById(a.hash.slice(1)) }))
    .filter((m) => m.sec);
  let marked;                                                       // what the menu shows right now

  const here = () => {
    if (!marks.length) return;
    const line = top.offsetHeight + window.innerHeight * 0.3;      // reading line: a third down the screen
    let mark = null;                                                // the chapter: the last menu section above the line –
    for (const m of marks) if (m.sec.getBoundingClientRect().top <= line) mark = m;  // P⁴ counts as Profile, and so on
    if (window.scrollY + window.innerHeight >= root.scrollHeight - 2) {  // at the very bottom: the last one in view
      mark = marks.filter((m) => m.sec.getBoundingClientRect().top < window.innerHeight).pop() || mark;
    }
    if (mark === marked) return;                                    // same chapter as in the last frame
    marked = mark;
    for (const m of marks) {
      if (m === mark) m.a.setAttribute("aria-current", "location");
      else m.a.removeAttribute("aria-current");
    }
  };

  /* ---------- Wiring */
  const layout = () => { dockMeasure(); build(); dockApply(); here(); };

  let raf = 0;
  window.addEventListener("scroll", () => {
    if (raf) return;
    raf = requestAnimationFrame(() => { raf = 0; here(); paint(); onScrollTop(); dockApply(); });
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
