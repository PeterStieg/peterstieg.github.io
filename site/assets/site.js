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

  /* ---------- Duration of the role that is still running: counted when the page loads, so it never goes stale
     between uploads. Same rule as build.py: first and current month included. */
  document.querySelectorAll(".dur[data-from]").forEach((el) => {
    const [y, m] = el.dataset.from.split("-").map(Number), now = new Date();
    const n = (now.getFullYear() - y) * 12 + now.getMonth() + 1 - m + 1;
    const [year, years, month, months] = el.dataset.units.split(",");
    const a = Math.floor(n / 12), b = n % 12;
    el.textContent = [a ? `${a} ${a === 1 ? year : years}` : "", b ? `${b} ${b === 1 ? month : months}` : ""]
      .filter(Boolean).join(" ");
  });

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
    lockMeasure();
  };

  const dockApply = () => {
    if (mode === "off") return;
    const sy = window.scrollY;
    const done = sy >= dist;
    top.classList.toggle("docked", done);
    if (done) condense(mode === "swap" ? 1 : (sy - dist) / CONDENSE);   // reduced motion: straight to the lockup
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

  /* ---------- Lockup: once docked, the wordmark >_ PETER STIEG condenses into the logo >_ P/S while you keep
     scrolling – the other letters drop out, P and S close up, the / becomes the gap, the S steps down one bar.
     Drawn from the font's own outlines (Atkinson Hyperlegible Bold, 1000 units per em, y up), so the first frame
     matches the header text and the last one the lockup in the page. The design is in src/lockup/. */
  const logo = home && home.querySelector(".lockup");
  const still = logo && logo.querySelector(".still");
  const CONDENSE = 180;                                            // px of scroll from wordmark to lockup
  const GLYPH = {
    ">": "M40 -12V130L365 250L40 368V510L533 299V200Z",
    "_": "M10 -128V0H420V-128Z",
    "P": "M44 0V668H301Q388 668 456.5 650Q525 632 564.5 585Q604 538 604 450Q604 363 564.5 315.5Q525 268 456.5 250Q388 232 301 232H202V0ZM202 363H306Q343 363 372.5 370Q402 377 419.5 396Q437 415 437 450Q437 485 419.5 503.5Q402 522 372.5 528.5Q343 535 306 535H202Z",
    "E": "M44 0V668H558V529H202V413H419V274H202V139H558V0Z",
    "T": "M230 0V529H15V668H602V529H387V0Z",
    "R": "M44 0V668H301Q388 668 456.5 651Q525 634 564.5 589Q604 544 604 461Q604 423 590 385.5Q576 348 541.5 317Q507 286 443 269L637 0H454L273 252H202V0ZM202 384H306Q362 384 399.5 398.5Q437 413 437 459Q437 506 399.5 520.5Q362 535 306 535H202Z",
    "S": "M314 -12Q205 -12 130.5 32.5Q56 77 25 157L169 209Q183 161 221.5 138Q260 115 315 115Q344 115 371 121.5Q398 128 416 143.5Q434 159 434 185Q434 220 400 239.5Q366 259 312 269L231 285Q177 296 130.5 318.5Q84 341 56 378.5Q28 416 28 473Q28 527 53 566Q78 605 119.5 630Q161 655 211 667.5Q261 680 311 680Q365 680 415.5 665Q466 650 506 618.5Q546 587 567 535L424 483Q411 517 377.5 535Q344 553 297 553Q251 553 220.5 536.5Q190 520 190 489Q190 464 211 446Q232 428 266 421L356 403Q397 395 439 382.5Q481 370 516.5 349.5Q552 329 574 295Q596 261 596 209Q596 156 571.5 114.5Q547 73 506.5 45Q466 17 416 2.5Q366 -12 314 -12Z",
    "I": "M57 0V124H151V544H57V668H401V544H309V124H401V0Z",
    "G": "M352 -12Q254 -12 183 30.5Q112 73 73.5 151.5Q35 230 35 336Q35 442 78 519Q121 596 197.5 638Q274 680 375 680Q463 680 533.5 645Q604 610 644 542L508 486Q492 512 458.5 531Q425 550 373 550Q326 550 287 526Q248 502 225 454.5Q202 407 202 336Q202 231 250 174.5Q298 118 376 118Q413 118 447 128.5Q481 139 503 164Q525 189 525 231V250H375V378H683V0H579L557 74Q493 -12 352 -12Z"
  };
  const SL = Math.atan2(668, 261), SIN = Math.sin(SL), COS = Math.cos(SL);   // the font's "/": 68.66°
  const HW = 50 / SIN;                                             // a "/" only 50 wide – as wide as the gap
  const LS = 55, P_TXT = 1453, P_END = 999;                        // letter-spacing 0.055em · P in the text · P in the lockup
  const ADV = { " ": 320, P: 626, E: 580, T: 617, R: 654, S: 619, I: 458, G: 719 };
  const WORD = [];                                                 // "PETER STIEG" as the browser sets it
  for (let i = 0, x = P_TXT, prev = ""; i < 11; i++) {
    const ch = "PETER STIEG"[i];
    if (prev === "E" && ch === "G") x -= 19;                       // the font's one kerning pair here
    WORD.push([ch, x]);
    x += ADV[ch] + LS; prev = ch;
  }
  const GAP_C = 350, GAP_H = 25;                                   // the gap: centre and half width, square to the /
  const S_SLOT = 626 - 158;                                        // the S one stem under the bowl
  const STEP = [-133 * 261 / 668, -133];                           // one bar (133) down the slash
  const KT = 52 / 144;                                             // slope of the S's lower end, 19.86°
  const SLASH_REL = 626 + LS, S_REL = SLASH_REL + 15 + 261 + HW + 15 + LS;   // "P/S" as text, relative to P
  const S_WORD = WORD[6][1] - P_TXT;                               // the S of STIEG, relative to P
  const lineX = (c, y) => (c + y * COS) / SIN;                     // x on a line at the slash angle
  const SL_TXT = [[15, 0], [276, 668], [276 + HW, 668], [15 + HW, 0]].map(([x, y]) => [x + SLASH_REL, y]);
  const SL_END = [[lineX(GAP_C - GAP_H, 0), 0], [lineX(GAP_C - GAP_H, 668), 668],
    [lineX(GAP_C + GAP_H, 668), 668], [lineX(GAP_C + GAP_H, 0), 0]];
  const clamp01 = (x) => Math.min(1, Math.max(0, x));
  const sine = (x) => (1 - Math.cos(Math.PI * x)) / 2;
  const lerp = (a, b, t) => a + (b - a) * t;
  const pts = (P) => P.map(([x, y]) => x.toFixed(1) + "," + y.toFixed(1)).join(" ");
  const halfPlane = (p1, p2, side) => {                            // everything on one side of the line p1–p2
    const R = 40000, dx = p2[0] - p1[0], dy = p2[1] - p1[1], L = Math.hypot(dx, dy);
    const ux = dx / L, uy = dy / L, nx = uy * side, ny = -ux * side;
    const a = [p1[0] - ux * R, p1[1] - uy * R], b = [p1[0] + ux * R, p1[1] + uy * R];
    return pts([a, b, [b[0] + nx * R, b[1] + ny * R], [a[0] + nx * R, a[1] + ny * R]]);
  };
  const foot = (w) => {                                            // the P's stem, grown to the S's lower end
    const lift = 5.15 * (1 - w);
    const x0 = 25 + S_SLOT + STEP[0] * w, y0 = 157 + STEP[1] * w + lift, y = (x) => y0 + (x - x0) * KT;
    const yl = y(44), yr = y(202);
    if (yl >= 0) return null;
    if (yr >= 0) { const xz = x0 - y0 / KT; return [[44, 20], [xz, 20], [xz, 0], [44, yl]]; }
    return [[44, 20], [202, 20], [202, yr], [44, yl]];
  };

  let cam0 = null, morph = null, lastV = -1;                       // cam0: the header text, in the lockup's units
  const lockMeasure = () => {
    cam0 = null; lastV = -1;
    const word = home && home.querySelector(".word");
    if (!logo || !word) return;
    const box = logo.getBoundingClientRect(), k = box.height / 813;        // px per unit
    const fs = parseFloat(getComputedStyle(word).fontSize);
    const r = textRects(word.querySelector(".caret"))[0];
    if (!r || !k) return;
    // Range boxes start at the glyph origin and reach 950 units (the ascent) above the baseline
    cam0 = { m: fs / 1000 / k, x: 40 + (r.left - box.left) / k, y: -668 + (r.top - box.top + 0.95 * fs) / k };
  };

  const condense = (v) => {
    if (!logo) return;
    v = clamp01(v);
    if (v === lastV) return;
    lastV = v;
    const done = v >= 1 || !cam0;
    still.style.display = done ? "" : "none";
    if (morph) morph.style.display = done ? "none" : "";
    if (done) return;
    if (!morph) {
      morph = document.createElementNS("http://www.w3.org/2000/svg", "g");
      morph.setAttribute("class", "morph");
      logo.insertAdjacentHTML("afterbegin", "<defs>" + Object.keys(GLYPH)
        .map((ch) => `<path id="lk-${ch === ">" ? "gt" : ch === "_" ? "us" : ch}" d="${GLYPH[ch]}"/>`).join("") + "</defs>");
      logo.appendChild(morph);
    }
    const a = clamp01(v / 0.25);                                   // 0–25 %: the other letters fade out
    const b = ease(clamp01((v - 0.2) / 0.3));                      // 20–50 %: the S closes up, the / appears – P/S
    const u = ease(clamp01((v - 0.45) / 0.4));                     // 45–85 %: Enter – P/S slide together
    const w = sine(clamp01((v - 0.8) / 0.2));                      // 80–100 %: the S steps down, the foot grows
    const z = ease(clamp01((v - 0.4) / 0.6));                      // 40–100 %: from 16 px text to the 28 px lockup
    const px = lerp(P_TXT, P_END, u);
    const sRel = lerp(lerp(S_WORD, S_REL, b), S_SLOT, u);
    const sl = SL_TXT.map((p, i) => [lerp(p[0], SL_END[i][0], u) + px, lerp(p[1], SL_END[i][1], u)]);
    const k = 1 - clamp01((u - 0.55) / 0.35);                      // the / fades into the gap
    const use = (id, x, y, extra = "") => `<use href="#lk-${id}" x="${x.toFixed(1)}" y="${y.toFixed(1)}"${extra}/>`;
    let s = `<g class="acc">${use("gt", 0, 0)}${use("us", 573, 0)}</g><g class="ink">`;
    s += `<clipPath id="lk-cp" clipPathUnits="userSpaceOnUse"><polygon points="${halfPlane(sl[0], sl[1], -1)}"/></clipPath>`;
    s += `<clipPath id="lk-cs" clipPathUnits="userSpaceOnUse"><polygon points="${halfPlane(sl[3], sl[2], 1)}"/></clipPath>`;
    s += `<g clip-path="url(#lk-cp)">${use("P", px, 0)}</g>`;
    const f = foot(w);
    if (f) s += `<polygon points="${pts(f.map(([x, y]) => [x + px, y]))}"/>`;
    s += `<g clip-path="url(#lk-cs)">${use("S", px + sRel + STEP[0] * w, STEP[1] * w)}</g>`;
    if (a < 1) WORD.forEach(([ch, x], i) => {                      // E T E R and T I E G – the S's companions move with it
      if (i === 0 || i === 6 || ch === " ") return;
      s += use(ch, x + (i > 6 ? sRel - S_WORD : 0), 0, ` opacity="${(1 - a).toFixed(3)}"`);
    });
    if (b * k > 0.002) s += `<polygon points="${pts(sl)}" opacity="${(b * k).toFixed(3)}"/>`;
    s += "</g>";
    const m = Math.pow(cam0.m, 1 - z);                             // zoom: geometric, so it feels even
    morph.setAttribute("transform", `translate(${(cam0.x * (1 - z)).toFixed(2)} ${(cam0.y * (1 - z)).toFixed(2)}) scale(${m.toFixed(4)} ${(-m).toFixed(4)})`);
    morph.innerHTML = s;
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

  /* ---------- You are here: the menu marks the chapter being read, like a slide deck's header;
     the jump control shows its number and marks the section in its list. */
  const marks = [...document.querySelectorAll(".nav .sect")]
    .map((a) => ({ a, sec: document.getElementById(a.hash.slice(1)) }))
    .filter((m) => m.sec);
  const secs = [...document.querySelectorAll("main .sec")];
  const pad = document.querySelector(".jump");
  const cur = pad && pad.querySelector(".cur");
  const list = pad ? [...pad.querySelectorAll(".menu a")] : [];
  let current;                                                      // the section being read in the last frame

  const here = () => {
    if (!marks.length) return;
    const line = top.offsetHeight + window.innerHeight * 0.3;      // reading line: a third down the screen
    let sec = null;                                                 // the section: the last one above the line
    for (const x of secs) if (x.getBoundingClientRect().top <= line) sec = x;
    if (window.scrollY + window.innerHeight >= root.scrollHeight - 2) {  // at the very bottom: the last one in view
      sec = secs.filter((x) => x.getBoundingClientRect().top < window.innerHeight).pop() || sec;
    }
    if (sec === current) return;                                    // same section as in the last frame
    current = sec;
    const i = secs.indexOf(sec);                                    // the chapter: the last menu section up to it –
    const mark = sec ? marks.filter((m) => secs.indexOf(m.sec) <= i).pop() : null;   // P⁴ counts as Profile, and so on
    for (const m of marks) {
      if (m === mark) m.a.setAttribute("aria-current", "location");
      else m.a.removeAttribute("aria-current");
    }
    if (cur) cur.textContent = sec ? sec.querySelector("h2 .no").textContent : "";
    for (const a of list) {
      if (sec && a.hash === "#" + sec.id) a.setAttribute("aria-current", "location");
      else a.removeAttribute("aria-current");
    }
  };

  /* ---------- Jump control: up and down lead to the start of the section above and below. A section counts as
     above once its start has passed under the header (scroll-padding-top), so up first returns to the start of
     the section being read. Several clicks in a row count from where the scroll is headed, not from where it is. */
  const upBtn = pad && pad.querySelector(".up"), downBtn = pad && pad.querySelector(".down");
  const menu = pad && pad.querySelector(".menu");
  let upTo, downTo, goal = null, goalTimer = 0;

  const label = (btn, to, text) => {
    btn.href = "#" + (to ? to.id : "");
    btn.setAttribute("aria-label", text);
    btn.title = text;
    if (to) btn.removeAttribute("aria-disabled");
    else btn.setAttribute("aria-disabled", "true");
  };
  const name = (sec) => (list.find((a) => a.hash === "#" + sec.id) || { dataset: {} }).dataset.t;

  const steer = () => {
    if (!pad || !marks.length) return;
    const edge = parseFloat(getComputedStyle(root).scrollPaddingTop) || 0;
    if (goal && Math.abs(goal.getBoundingClientRect().top - edge) < 2) goal = null;      // arrived
    const base = goal ? goal.getBoundingClientRect().top : edge;
    let u = null, d = null;
    for (const x of secs) {
      const y = x.getBoundingClientRect().top;
      if (y < base - 2) u = x;
      else if (y > base + 2 && !d) d = x;
    }
    if (!u && (goal ? goal !== hero : window.scrollY > 0)) u = hero;       // above the first section: the top
    if (!goal && window.scrollY + window.innerHeight >= root.scrollHeight - 2) d = null;   // nothing left below
    if (u !== upTo) { upTo = u; label(upBtn, u, u === hero ? pad.dataset.top : u ? pad.dataset.up.replace("%s", name(u)) : pad.dataset.top); }
    if (d !== downTo) { downTo = d; label(downBtn, d, d ? pad.dataset.down.replace("%s", name(d)) : pad.dataset.down.replace(/:\s*%s/, "")); }
  };

  const go = (ev, to) => {
    if (ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;   // new tab and so on: a plain link
    ev.preventDefault();
    if (!to) return;
    goal = to;
    clearTimeout(goalTimer);
    goalTimer = setTimeout(() => { goal = null; steer(); }, 1200);
    to.scrollIntoView({ block: "start" });                          // smooth unless reduced motion (CSS scroll-behavior)
    steer();
  };
  if (pad) {
    upBtn.addEventListener("click", (ev) => go(ev, upTo));
    downBtn.addEventListener("click", (ev) => go(ev, downTo));
    // the list: closes on a choice, a click elsewhere, or Esc (focus back on its button)
    list.forEach((a) => a.addEventListener("click", () => { menu.open = false; }));
    document.addEventListener("click", (ev) => { if (menu.open && !menu.contains(ev.target)) menu.open = false; });
    menu.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
    });
  }

  /* ---------- Phones: the heading stuck under the header takes over the header's hairline (see site.css). */
  const heads = [...document.querySelectorAll(".sec > h2")];
  const narrow = window.matchMedia("(max-width: 47.99rem)");
  let stuck = null;
  const stick = () => {
    let h = null;
    if (top && narrow.matches) {
      const edge = top.getBoundingClientRect().bottom;
      for (const x of heads) {
        const r = x.getBoundingClientRect();
        if (r.top <= edge + 0.5 && r.bottom > edge) h = x;
      }
    }
    if (h === stuck) return;
    if (stuck) stuck.classList.remove("stuck");
    if (h) h.classList.add("stuck");
    top.classList.toggle("ext", !!h);
    stuck = h;
  };

  /* ---------- Toggletips: the popover opens next to its i, below or – without room – above it.
     Placed before the first frame it shows in; follows the i while scrolling. Without JavaScript it is centred. */
  const tips = "popover" in HTMLElement.prototype ? [...document.querySelectorAll(".tip")] : [];
  const place = (tip) => {
    const i = document.querySelector(`[popovertarget="${tip.id}"]`).getBoundingClientRect();
    if (i.bottom < top.offsetHeight || i.top > window.innerHeight) { tip.hidePopover(); return; }   // the i left the screen
    const m = 8, w = tip.offsetWidth, h = tip.offsetHeight;
    let y = i.bottom + 6;
    if (y + h > window.innerHeight - m) y = i.top - h - 6;
    tip.style.left = Math.max(m, Math.min(i.left - 12, window.innerWidth - w - m)) + "px";
    tip.style.top = Math.max(m, y) + "px";
  };
  tips.forEach((tip) => tip.addEventListener("beforetoggle", (ev) => {
    if (ev.newState === "open") requestAnimationFrame(() => place(tip));
  }));
  const follow = () => tips.forEach((tip) => { if (tip.matches(":popover-open")) place(tip); });

  /* ---------- The positions before 2014: opening them changes the page height – redraw the minimap.
     Printing shows them open. */
  const more = [...document.querySelectorAll("details.more")];
  more.forEach((d) => d.addEventListener("toggle", () => layout()));
  let closed = [];
  window.addEventListener("beforeprint", () => { closed = more.filter((d) => !d.open); closed.forEach((d) => { d.open = true; }); });
  window.addEventListener("afterprint", () => { closed.forEach((d) => { d.open = false; }); });

  /* ---------- Wiring */
  const hide = () => { if (menu && menu.open && !top.classList.contains("docked")) menu.open = false; };  // back in the hero
  const layout = () => { dockMeasure(); build(); dockApply(); here(); steer(); stick(); };

  let raf = 0;
  window.addEventListener("scroll", () => {
    if (raf) return;
    raf = requestAnimationFrame(() => { raf = 0; here(); steer(); paint(); onScrollTop(); dockApply(); stick(); follow(); hide(); });
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
