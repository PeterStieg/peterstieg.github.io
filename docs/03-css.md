# site.css: look and layout

`site/assets/site.css` is the single stylesheet behind every page: the English and German home pages, the 404 page and the two legal pages. It has no preprocessor, no framework and no build step, so the file you read is exactly what the browser receives. This chapter goes through it from top to bottom, rule by rule, and explains for each declaration what it does, which mechanism makes it work and what would break without it.

Figures marked "measured" come from Chromium. Pixel values in brackets assume the browser default of 16px for 1rem.

---

## File header

```css
/* peterstieg.com · Admiring complexity. Loving simplicity. */
```

- Everything between `/*` and `*/` is a comment. The browser skips it, but it is still downloaded, so anyone who opens the file sees the motto.

## Fonts: @font-face

```css
@font-face {
  font-family: "Atkinson Hyperlegible";
  src: url("fonts/atkinson-hyperlegible-latin-400-normal.woff2") format("woff2");
  font-weight: 400; font-style: normal; font-display: swap;
}
@font-face {
  font-family: "Atkinson Hyperlegible";
  src: url("fonts/atkinson-hyperlegible-latin-400-italic.woff2") format("woff2");
  font-weight: 400; font-style: italic; font-display: swap;
}
@font-face {
  font-family: "Atkinson Hyperlegible";
  src: url("fonts/atkinson-hyperlegible-latin-700-normal.woff2") format("woff2");
  font-weight: 700; font-style: normal; font-display: swap;
}
```

`@font-face` styles nothing. It registers a font face – "if text asks for this family at this weight and style, here is the file" – and the `font-family` declaration on `body` later puts the family to use. The lines inside are descriptors that describe the file, not properties applied to elements.

- `font-family: "Atkinson Hyperlegible";` – the family name the rest of the CSS refers to. All three blocks register the same name, so the browser sees one family with three faces.
- `src: url(...) format("woff2");` – where the file lives. A relative URL inside a stylesheet resolves against the stylesheet's own location, so `fonts/…` means `site/assets/fonts/…` on every page, including `de/index.html`. `format("woff2")` names the format up front; a browser that cannot decode it skips the source without downloading it. WOFF2 is a compressed font container; each file here is about 17–18 KB.
- `latin` in the file names marks a subset: each file holds only 220 characters – Latin letters, digits, punctuation, € · × – and a few more. That keeps the files small. It also means that characters outside the subset – arrows, box-drawing lines, superscript digits – are missing. Three later sections (P⁴, the #JobAlert tree, the drawn arrows) exist because of this.
- `font-weight: 400; font-style: normal;` – this file is the regular upright face. When an element asks for `font-weight: 700`, the browser's font matching picks the block that declares 700; for `font-style: italic`, the italic block.
- `font-display: swap;` – what happens while the file is still downloading. `swap` renders text straight away in the next font of the stack (see `body`) and replaces it when the web font arrives. Trade-off: text is readable from the first frame instead of invisible, but the swap can re-wrap lines, because the fallback font has different widths. The project softens this on both ends: `index.html` preloads the 400 and 700 upright files with `<link rel="preload">`, so they are requested before the stylesheet is even parsed, and `site.js` measures the docking positions only after `document.fonts.ready`, because positions measured in the fallback font would be wrong after the swap.

**Why italic and bold need their own files.** A font file contains one design. Bold is not the regular drawn thicker, and a true italic has its own letterforms. If no matching face is registered, the browser synthesizes one: fake bold smears the regular outlines, fake italic slants the upright letters. With real faces registered, nothing is faked. Browsers download a face only when text on the page actually uses it – the italic file is fetched because `.pos` and `.ety i` set italic. There is no bold-italic file; the site never combines the two.

**The license file.** Atkinson Hyperlegible is published by the Braille Institute of America under the SIL Open Font License 1.1. Self-hosting means redistributing the font files, which the OFL allows as long as the copyright notice and the license travel with them; `assets/fonts/OFL.txt` takes care of that. The OFL also permits embedding in web pages and forbids selling the fonts on their own. Self-hosting has a second effect: no request goes to a third-party font service, which keeps the site's no-tracking promise.

## Design tokens and the theme system

### Cascade and specificity, briefly

The theme system depends on how the browser decides between competing rules, so this comes first. When several rules set the same property on the same element, the browser picks one winner. It compares, in this order: origin and importance (browser defaults versus site styles, `!important`), then **specificity**, then **source order** – the later rule wins only when specificity ties.

Specificity counts the parts of a selector in three columns, written (a,b,c): a = ID selectors, b = classes, attribute selectors and pseudo-classes, c = element names and pseudo-elements. The columns are compared from the left; the first one that differs decides.

| Selector | (a,b,c) |
|---|---|
| `html` | (0,0,1) |
| `:root` | (0,1,0) |
| `:root[data-theme="dark"]` | (0,2,0) |
| `:root:not([data-theme="light"])` | (0,2,0) – `:not()` counts as its argument |
| `.intro` | (0,1,0) |
| `:where(.body) p` | (0,0,1) – `:where()` counts as nothing |
| `.js .top.dock .home` | (0,4,0) |

Media queries and `@supports` add nothing to specificity; they only decide whether the rules inside take part at all. Inline styles (`style="…"`, which `site.js` writes) beat every stylesheet selector – unless the stylesheet declaration is marked `!important`, which the print rules use.

### Light values on :root

```css
:root {
  --paper: #F7F6F3;
  --ink: #1A1C1E;
  --muted: #565B60;
  --line: #DCDAD4;
  --accent: #7A1A2C;
  --accent-soft: #E8C3CA;
  --bar: #C4C6C9;
  --bar-lit: #6E7378;
  color-scheme: light;
}
```

- `:root` – matches the root element of the document, `<html>`. Same element as the selector `html`, but as a pseudo-class it weighs (0,1,0) instead of (0,0,1).
- `--paper`, `--ink`, … – **custom properties**. Any name that starts with two hyphens is one. They do nothing on their own; other declarations read them with `var(--name)`. Two mechanisms make them the right tool for themes:
  - They **inherit**. A value set on `<html>` is visible on every element below it, unless an element sets its own.
  - `var()` is resolved **per element, at computed-value time**. When `--paper` changes on `<html>`, every `var(--paper)` in the page picks up the new value in the same frame. No other rule needs to know that themes exist.
- The roles:
  - `--paper` – page background, a warm off-white.
  - `--ink` – body text, near-black with a cool tint. Not pure #000, which glares on a bright screen.
  - `--muted` – secondary text: dates, labels, descriptions.
  - `--line` – hairlines: borders, link underlines, pill outlines.
  - `--accent` – the bordeaux: prompt caret, cursor block, focus ring, hover underline, footnote numbers.
  - `--accent-soft` – the text-selection highlight.
  - `--bar`, `--bar-lit` – minimap bars, normal and highlighted.
- `color-scheme: light;` – a real property, not a variable. It tells the browser which scheme the page is drawn in, so the parts the browser draws itself match: the default canvas color, scrollbars, form controls and system colors.

Below this point the stylesheet contains no hex color at all – every color is a `var()` or `transparent`. That is why three small blocks are enough to re-theme the whole site.

### Dark by system preference

```css
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #181A1C;
    --ink: #F5F4F2;
    --muted: #A3A8AD;
    --line: #2F3337;
    --accent: #C98593;
    --accent-soft: #4E0E1B;
    --bar: #3A3F44;
    --bar-lit: #8E949A;
    color-scheme: dark;
  }
}
```

- `@media (prefers-color-scheme: dark)` – a media feature for a user preference: true when the operating system or browser is set to a dark appearance. While it is false, the rules inside are ignored. When the visitor flips the OS setting, the page follows live.
- `:root:not([data-theme="light"])` – the root element, unless it carries `data-theme="light"`. The `:not()` is what lets an explicit light choice beat a dark OS.
- The eight values: dark paper, light ink, a lighter accent. `color-scheme: dark` switches scrollbars and other browser-drawn parts to dark.

### Dark by explicit choice

```css
:root[data-theme="dark"] {
  --paper: #181A1C;
  --ink: #F5F4F2;
  --muted: #A3A8AD;
  --line: #2F3337;
  --accent: #C98593;
  --accent-soft: #4E0E1B;
  --bar: #3A3F44;
  --bar-lit: #8E949A;
  color-scheme: dark;
}
```

- `:root[data-theme="dark"]` – the root element with the attribute `data-theme="dark"`, whatever the OS says. Its (0,2,0) beats the bare `:root` (0,1,0), so these values replace the light defaults. Specificity decides on its own here; the rule would win even if it stood at the top of the file.

Where the attribute comes from: every page has a one-line script in `<head>` that reads `localStorage.theme` and sets `data-theme` on `<html>` before the first paint, so a returning visitor never sees a flash of the wrong theme. The two theme buttons set it on click ([chapter 4](04-js.md)). No attribute means "follow the system".

### The three states

| `data-theme` on `<html>` | OS set to light | OS set to dark |
|---|---|---|
| none – system | `:root` → light | media block → dark |
| `light` | `:root` → light | `:root` → light; the media block is excluded by `:not()` |
| `dark` | `:root[data-theme="dark"]` → dark | both dark rules match, with identical values |

### Why the dark values appear twice

The two reasons for dark – "the OS prefers dark" and "the visitor chose dark" – are different kinds of condition. The first is a media condition about the environment; the second is a selector about the document. CSS cannot join a media condition and a selector with OR in one rule, so the same values are written once under each condition. The price: both copies must be edited together.

The `:not([data-theme="light"])` saves a third copy. With a plain `:root` inside the media query, a dark OS would always beat the light defaults (same specificity, later in the file), and an explicit light choice would need yet another block repeating all light values under `:root[data-theme="light"]`.

### The contrast behind the values

WCAG contrast ratios computed from the token values. For reference, level AA asks for 4.5:1 for body text and 3:1 for large text, focus indicators and UI parts.

| Token | Light | vs `--paper` | Dark | vs `--paper` |
|---|---|---|---|---|
| `--ink` | #1A1C1E | 15.8:1 | #F5F4F2 | 15.9:1 |
| `--muted` | #565B60 | 6.4:1 | #A3A8AD | 7.3:1 |
| `--accent` | #7A1A2C | 9.7:1 | #C98593 | 6.0:1 |
| `--bar-lit` | #6E7378 | 4.4:1 | #8E949A | 5.7:1 |
| `--bar` | #C4C6C9 | 1.6:1 | #3A3F44 | 1.6:1 |
| `--line` | #DCDAD4 | 1.3:1 | #2F3337 | 1.4:1 |
| `--ink` on `--accent-soft` | #E8C3CA | 10.7:1 | #4E0E1B | 13.6:1 |

- Each role keeps about the same contrast in both themes: ink near 16:1, muted text well above 4.5:1. The dark theme is a re-tuning, not an inversion.
- All four accent values share one hue, about 348° – bordeaux – and differ only in lightness and saturation. The dark bordeaux #7A1A2C on near-black paper would almost disappear, so dark mode lightens it to a dusty rose. `--accent-soft` swaps roles: pale pink behind dark ink in light mode, deep wine behind light ink in dark mode.
- `--line` and `--bar` are faint on purpose. Hairlines and inactive minimap bars carry no information of their own.
- The neutrals are not pure grey. Light paper and light ink lean warm; the dark paper, the dark ink and both muted greys lean cool blue-grey, all with very low saturation.

## Base: box model, html, body

```css
*, *::before, *::after { box-sizing: border-box; }
```

- `*` – the universal selector: every element. Pseudo-elements are not elements, so `*::before, *::after` adds the generated boxes (the tree lines use them).
- `box-sizing: border-box` – `width` and `height` include padding and border. With the default `content-box`, padding and border are added on top: `.to-top` would be 2.75rem plus 2px of border wide, and `.wrap`'s 70rem maximum would grow by its side padding. With `border-box`, the size you write is the size you get.
- `*` has specificity (0,0,0), so any other rule can override this.

```css
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; scroll-padding-top: 4.5rem; }
@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
```

- `-webkit-text-size-adjust: 100%; text-size-adjust: 100%;` – some mobile browsers, Safari on iOS in particular, enlarge text on their own, for example after rotating to landscape. `100%` switches that off, because the site's sizes are already designed for small screens. Pinch-zoom is unaffected. The prefixed name is the one iOS Safari has relied on for years; the standard name covers the others.
- `scroll-padding-top: 4.5rem;` – when the browser scrolls to an anchor target (`#profile`, a footnote, the skip-link target `#main`), it aligns the target with the top edge of the viewport – exactly where the sticky header sits, so the heading would end up underneath it. Scroll padding on the scroll container (for the page, that is `html`) moves this alignment line down: targets land 4.5rem (72px) below the top. The header is 3.5rem plus a 1px border (57px, measured), which leaves about 15px of air. Remove the declaration and every in-page link hides its heading behind the header.
- `@media (prefers-reduced-motion: no-preference)` – true when the visitor has not asked the OS to reduce motion. Large animated movements can cause dizziness or nausea for people with vestibular disorders; the OS setting exists for them.
- `scroll-behavior: smooth;` – anchor jumps glide instead of jumping. Because the rule sits behind `no-preference`, the instant jump is the default: visitors who asked for less motion, and browsers that don't know the media feature, get no animation.

```css
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 1.125rem;
  line-height: 1.55;
  font-kerning: normal;
}
```

- `margin: 0;` – removes the browser's default 8px around the page.
- `background: var(--paper);` – the page color. A background on `body` (with none on `html`) is propagated to the canvas, so it fills the whole viewport, including the overscroll area.
- `color: var(--ink);` – the text color. `color` inherits, so every element that doesn't set its own gets ink.
- `font-family: …` – a fallback stack. For each character, the browser uses the first font in the list that is available and contains it: Atkinson; `system-ui`, the operating system's interface font; `-apple-system`, older Safari's name for the same; `"Segoe UI"`, the Windows interface font, for browsers that predate `system-ui`; `sans-serif`, the generic last resort. The fallbacks show during the font swap and for characters missing from the Latin subset.
- `font-size: 1.125rem;` – 18px at default settings. **rem** is relative to the root element's font size. This site never sets one, so 1rem is the browser default – 16px unless the visitor changed it. Someone who raises the default to 20px gets 22.5px body text. **em**, used further down, is relative to the element's own font size (inside `font-size` itself: the parent's). The rule of thumb in this file: rem for sizes that should follow the visitor's setting, em for details that should scale with the text they belong to.
- `line-height: 1.55;` – unitless on purpose. A unitless line height is inherited as the factor, and each element multiplies it by its own font size: 1.55 × 18px for body text, 1.55 × 20px for a 1.25rem paragraph. With `1.55em` or `27.9px`, the computed length would be inherited instead, and every larger text below would get 27.9px lines – cramped or overlapping.
- `font-kerning: normal;` – kerning adjusts the space between specific letter pairs (AV, To, Te). Atkinson ships kerning data; the default `auto` lets the browser skip it, for example at small sizes; `normal` always applies it.

## Selection, links, focus

```css
::selection { background: var(--accent-soft); color: var(--ink); }
```

- `::selection` – a pseudo-element for the text the visitor highlights. Only a few properties work inside it (color, background color, text decoration and a few more).
- Pale bordeaux in light mode, deep wine in dark mode, with ink on top at 10.7:1 and 13.6:1.

```css
a {
  color: inherit;
  text-decoration-line: underline;
  text-decoration-color: var(--line);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.22em;
}
a:hover { text-decoration-color: var(--accent); }
a:focus-visible, button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
  border-radius: 2px;
}
```

- `color: inherit;` – links take the color of the text around them instead of the browser's blue and purple. From here on, a link is recognized by its underline alone.
- `text-decoration-line`, `text-decoration-color`, `text-decoration-thickness` – the underline set through its longhands. Longhands let `a:hover` change only the color; the shorthand `text-decoration` would reset every part at once.
- The underline color is `--line`, about 1.3:1 against paper: deliberately quiet. Trade-off: links in running text are easy to overlook until hovered.
- `text-underline-offset: 0.22em;` – moves the underline down, clear of descenders (g, p, y). In em, so the gap scales: the 1.25rem e-mail link and a 0.95rem footer link get proportionally the same distance.
- `a:hover { text-decoration-color: var(--accent); }` – on hover only the underline color changes. (0,1,1) beats `a` (0,0,1).
- `:focus-visible` – matches an element that has focus *and* for which the browser decides a focus indicator should show: yes after keyboard navigation, usually not after a mouse click on a link or button. Plain `:focus` would also draw the ring on every click.
- `outline: 2px solid var(--accent);` – the focus ring. An outline is drawn outside the border and takes no space, so focusing never shifts the layout, which a border would. The accent reaches 9.7:1 and 6.0:1, far above the 3:1 needed for focus indicators.
- `outline-offset: 3px;` – a gap between element and ring.
- `border-radius: 2px;` – current browsers draw outlines along the border radius, so the ring gets soft corners. Side effect: it rounds the element itself too, and at (0,1,1) it beats any single-class rule. A round element therefore needs a stronger rule to stay round while focused. The back-to-top button has one: `.to-top { border-radius: 50% }` is only (0,1,0), so `.to-top:focus-visible` at (0,2,0) sets 50% again (see the back-to-top section). The theme buttons need nothing extra: `.themes button` is also (0,1,1), ties, and wins because it comes later.

## Skip link and visually hidden text

```css
.skip {
  position: absolute; left: 1rem; top: -3rem;
  background: var(--ink); color: var(--paper);
  padding: 0.5rem 0.75rem; z-index: 10; text-decoration: none;
}
.skip:focus { top: 1rem; }
```

The skip link is the first focusable element on every page. Keyboard users press Tab once, then Enter, and land in `<main id="main">`, past the header.

- `position: absolute; left: 1rem; top: -3rem;` – out of the flow and above the visible area. No ancestor is positioned, so the coordinates refer to the top of the page.
- `background: var(--ink); color: var(--paper);` – inverted colors, so it stands out in both themes.
- `padding: 0.5rem 0.75rem;` – a comfortable target.
- `z-index: 10;` – above everything else (the header uses 5, the flying hero name 6).
- `text-decoration: none;` – no underline on a button-like label.
- `.skip:focus { top: 1rem; }` – when focused, the link moves into view. `:focus` rather than `:focus-visible`, because it must appear on any focus.
- Why not `display: none` until focused: an element that isn't rendered cannot receive focus at all.

```css
.sr-only {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}
```

Visually hidden, still read by screen readers. In the hero, the visible typed text `.cmd` is `aria-hidden`, because `site.js` rewrites it letter by letter; a `.sr-only` copy holds the full sentence for assistive technology.

- `position: absolute;` – out of the flow, so it takes no space.
- `width: 1px; height: 1px;` – tiny but not zero: some screen readers skip elements without size.
- `overflow: hidden;` – content beyond the 1 × 1 box is not painted.
- `clip: rect(0 0 0 0);` – the old way to cut an absolutely positioned box down to nothing. Deprecated but still working; it stays for older browsers.
- `clip-path: inset(50%);` – the modern equivalent: every edge moves inward by half the box, which leaves a visible area of zero.
- `white-space: nowrap;` – in a 1px-wide box, text would wrap after every word, and some screen readers then read the words run together.
- The obvious alternatives fail: `display: none` and `visibility: hidden` remove the text from the accessibility tree as well; `opacity: 0` keeps its space in the layout.

## Layout frame

```css
/* ---------- frame ---------- */

.wrap {
  max-width: 70rem;
  margin-inline: auto;
  padding-inline: 1rem;
}
@media (min-width: 48rem) { .wrap { padding-inline: 2.5rem; } }
@media (min-width: 74rem) { .wrap { padding-right: 8rem; } }
```

`.wrap` is the content frame inside header, main and footer, so all three share the same edges.

- `max-width: 70rem;` – 1120px at most; with `border-box` this includes the padding.
- `margin-inline: auto;` – a logical property: left and right margin in a left-to-right language. `auto` margins on both sides split the remaining space equally, which centers the block.
- `padding-inline: 1rem;` – a 16px gutter on phones, so text never touches the screen edge.
- `@media (min-width: 48rem)` – from 768px viewport width (at default font size), the gutter grows to 2.5rem.
- **rem in media queries** refers to the browser's *initial* font size – the visitor's default setting – never to a font size set in CSS. With a 20px default, 48rem means 960px: the layout switches to the narrow version earlier, which is what larger text needs. Pixel breakpoints would ignore the setting.
- `@media (min-width: 74rem) { .wrap { padding-right: 8rem; } }` – from 1184px, the right padding grows to 8rem: a lane for the minimap, which appears from the same width. `padding-right` is the physical twin of the logical `padding-inline-end`; when both target the same side, the later declaration wins. The minimap also needs a height of at least 30rem, so on a wide but very short window the lane stays reserved while the minimap is hidden.

## Sticky header

```css
.top {
  position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5;
  background: color-mix(in srgb, var(--paper) 92%, transparent);
  -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
  border-bottom: 1px solid transparent;
}
.top.scrolled { border-bottom-color: var(--line); }
.top .wrap {
  display: flex; align-items: center; justify-content: space-between;
  gap: 1.5rem; min-height: 3.5rem;
}
```

- `position: sticky;` – the header stays in the normal flow (it takes its space at the top, so nothing starts underneath it), and as soon as scrolling would carry it above its `top` offset, it sticks there. It sticks only within its containing block; the header is a direct child of `body`, which spans the whole page, so it sticks all the way down. **sticky versus fixed:** a `fixed` element leaves the flow entirely and is placed relative to the viewport; the content would start underneath it and need a compensating padding.
- `top: env(safe-area-inset-top, 0px);` – the sticking offset. `env()` reads values the browser provides; `safe-area-inset-top` is the height of the notch or status-bar zone on phones; the second argument is the fallback for browsers that don't know the variable. Caveat: browsers report non-zero insets only to pages that opt into edge-to-edge drawing with `viewport-fit=cover` in the viewport meta tag. These pages don't, so the browser keeps the page inside the safe area and the value is 0. The declaration is future-proofing.
- `z-index: 5;` – sticky elements are positioned, so `z-index` applies. 5 keeps the header above the content scrolling beneath it. A positioned element with a z-index other than `auto` forms its own **stacking context** (see the docking rules).
- `background: color-mix(in srgb, var(--paper) 92%, transparent);` – mixes 92% paper with 8% nothing: the paper color at 92% opacity, in whichever theme is active. `color-mix()` works in all major browsers since 2023. There is no fallback declaration, so an older browser would show a fully transparent header.
- `-webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);` – `filter` would blur the element itself; `backdrop-filter` blurs whatever lies *behind* it. Content scrolling under the header is blurred and shows faintly through the 8% transparency. Older Safari versions only understand the prefixed name. A backdrop filter also forms a stacking context.
- `border-bottom: 1px solid transparent;` – reserves the pixel from the start, so the line that appears later doesn't push the page down.
- `.top.scrolled { border-bottom-color: var(--line); }` – `site.js` adds `.scrolled` once the page has moved more than 8px; the hairline separates header and content. No space between two classes means both on the same element: (0,2,0).
- `.top .wrap` – with a space: a `.wrap` *inside* `.top`.
  - `display: flex;` – logo and navigation become flex items in a row.
  - `align-items: center;` – vertical centering within the row.
  - `justify-content: space-between;` – logo at the left edge, navigation at the right, the free space between them.
  - `gap: 1.5rem;` – the minimum distance when space runs short.
  - `min-height: 3.5rem;` – the header height (56px). `min-height` instead of `height`, so the header can grow rather than clip if its content ever wraps.

```css
.home {
  font-weight: 700; text-decoration: none; white-space: nowrap;
  font-size: 1rem;
}
.home .caret { display: inline-block; color: var(--accent); margin-right: 0.45em; }
.home .name { display: inline-block; text-transform: uppercase; letter-spacing: 0.055em; }
```

`.home` is the header logo – `>_ PETER STIEG`, a link to the top.

- `font-weight: 700; text-decoration: none;` – bold, no underline.
- `white-space: nowrap;` – caret and name always on one line. `site.js` needs the docking target to be a single line box; if it wrapped, the script would fall back to a plain swap without the flight.
- `font-size: 1rem;` – a fixed 16px base for the logo, independent of the body's 18px.
- `.home .caret` – `display: inline-block` gives the span a box of its own that the script can measure (its hero counterpart must be inline-block to be transformable at all). `color: var(--accent)` makes the `>_` bordeaux; `margin-right: 0.45em` is the gap before the name.
- `.home .name` – `text-transform: uppercase` renders capitals while the HTML says "Peter Stieg". The source keeps normal case for screen readers and search engines. `letter-spacing: 0.055em` adds 5.5% of the font size after each letter: capitals are designed to stand next to lowercase letters and look cramped in a row of their own.

**Why the letter spacing is in em.** During docking, `site.js` shrinks the big hero name onto the header name with `transform: scale(k)`, where k is the ratio of the two text heights – about 0.175 on a wide screen (measured). A transform scales everything, the gaps between letters included. Both names use `0.055em`, so the hero's spacing is 0.055 × 92px and the header's 0.055 × 16px – the same proportion. After scaling, the two words are exactly the same width and the hand-over at the end is invisible. With `letter-spacing: 1px` on both, the hero's spacing would shrink to about 0.17px in flight while the header keeps a full 1px, and the name would jump in width at the moment of the swap.

```css
.nav { display: flex; align-items: center; gap: 1.25rem; font-size: 0.95rem; }
@media (max-width: 47.99rem) { .nav { gap: 0.5rem; } .top .wrap { gap: 0.75rem; } }
```

- `.nav` – a flex row of section links, language pill and theme pill, centered vertically, 1.25rem apart, at 0.95rem.
- `@media (max-width: 47.99rem)` – the counterpart of the `min-width: 48rem` queries: tighter gaps on phones. The .01 keeps the two ranges from overlapping at exactly 48rem. Small caveat: at fractional widths between 47.99rem and 48rem, which zoom can produce, neither applies; the newer range syntax `(width < 48rem)` has no such gap.

## Docking rules

```css
/* docking: the hero name and its prompt become the header logo (see site.js) */
.js .top.dock .home { visibility: hidden; }
.js .top.dock.docked .home { visibility: visible; }
.hero h1, .hero .prompt .caret { transform-origin: 0 0; }
.hero.flying h1, .hero.flying .prompt .caret { position: relative; z-index: 6; will-change: transform; }
.hero.docked h1, .hero.docked .prompt .caret { opacity: 0; pointer-events: none; }
```

While you scroll, the hero's `PETER STIEG` and its `>_` travel into the header logo. `site.js` moves them with inline `transform` values tied to the scroll position; CSS provides the states. The classes involved:

- `.js` on `<html>` – set by the inline script in `<head>` whenever JavaScript runs.
- `.dock` on the header – set by `site.js` on pages where docking is possible (a hero name and a header logo exist).
- `.docked` on header and hero – set once the flight is complete.
- `.flying` on the hero – present while the elements are in motion.

Declaration by declaration:

- `.js .top.dock .home { visibility: hidden; }` – while the hero name is on screen, the header logo is hidden: the name is visible exactly once. `visibility: hidden` keeps the logo's space, so the header layout doesn't shift, and takes it out of the tab order and the accessibility tree – measured: the first Tab presses go skip link, then the section links. Without JavaScript, `.js` is missing, nothing is hidden, and the header logo simply stays visible.
- `.js .top.dock.docked .home { visibility: visible; }` – once docked, the real logo appears. (0,5,0) beats (0,4,0).
- `.hero h1, .hero .prompt .caret { transform-origin: 0 0; }` – a selector list: the comma gives both selectors the same declaration. `transform-origin: 0 0` makes scaling start from the top-left corner instead of the default center, matching the coordinates the script calculates with. While flying, `site.js` sets a more precise origin inline (the offset of the text inside its box), and inline styles beat stylesheet rules; the CSS value is the baseline when no inline value is set.
- `.hero.flying …` – three declarations that apply only while the elements are in motion:
  - `position: relative;` – without offsets, the element stays exactly where it is. It is there because `z-index` only works on positioned elements (and flex or grid items).
  - `z-index: 6;` – one more than the header's 5, so the travelling name is painted *over* the header it flies into, not under its blurred background.
  - `will-change: transform;` – tells the browser that `transform` is about to change, so it can prepare, typically by giving the element its own compositing layer and moving it without repainting. A permanent `will-change` would keep such layers in memory for nothing.
- **Why only while flying.** Outside the flight, the name must behave like any other content and scroll *under* the sticky header. With a permanent z-index of 6, it would be painted over the header whenever it is not being moved – before the flight starts and, above all, in the reduced-motion "swap" mode, where the name never flies and simply scrolls away beneath the header.
- **Stacking contexts.** `z-index` values are compared only among elements in the same stacking context. The header (sticky with a z-index) is one such context inside the page's root context. The flying name's 6 can only beat the header's 5 because none of its ancestors – `.hero`, `.wrap`, `main` – forms a context of its own. Give any of them a `transform`, a `filter`, an `opacity` below 1, `isolation: isolate` or a position with a z-index, and the h1's 6 would count only inside that ancestor. The whole hero would then be compared with the header as a single layer at the ancestor's own level – 0 for a transform, filter or opacity – and the name would slide *under* the header.
- `.hero.docked …` – after landing, the hero copies disappear and the real header logo takes over.
  - `opacity: 0;` – invisible, but still in the layout and in the accessibility tree. The hero `<h1>` is the page's main heading; screen-reader users who jump between headings still find it after the name has docked. `visibility: hidden` would remove it from that tree, `display: none` would also collapse its box and make the page height and scroll position jump.
  - `pointer-events: none;` – an element at opacity 0 still catches clicks and text selection. The docked copy has been moved onto the header logo's position; this lets every click pass through to what lies beneath.
- With reduced motion, `site.js` uses the swap mode: no flight, the hero gets neither `.flying` nor `.docked`, the name keeps its normal stacking, and the header logo appears once the hero name has scrolled under the header.

## Navigation and language pill

```css
.nav a { text-decoration: none; color: var(--muted); }
.nav a:hover { color: var(--ink); }
/* menu numbers match the headings ("01 Profile"). You are here (site.js): the section being read looks like
   its heading – number in accent, label in ink and bold. A hidden bold copy of the label (data-label)
   reserves the width, so the menu never shifts. */
.nav .sect { white-space: nowrap; }
.nav .sect .no { font-variant-numeric: tabular-nums; }
.nav .sect .label { display: inline-grid; }
.nav .sect .label::after { content: attr(data-label); font-weight: 700; height: 0; overflow: hidden; visibility: hidden; }
.nav .sect[aria-current] { color: var(--ink); }
.nav .sect[aria-current] .no { color: var(--accent); }
.nav .sect[aria-current] .label { font-weight: 700; }
.langs {
  display: inline-flex; align-items: center;
  border: 1px solid var(--line); border-radius: 999px;
  padding: 0.1rem 0.3rem;
}
.langs > * { padding: 0 0.35rem; line-height: 1.6; }
.nav .langs a { color: var(--muted); }
.nav .langs a:hover { color: var(--ink); }
.langs [aria-current] { color: var(--ink); font-weight: 700; }
```

These rules continue the header after the docking block.

- `.nav a { text-decoration: none; color: var(--muted); }` – navigation links without underline, in muted grey. The shorthand `text-decoration: none` resets all three longhands set on `a`. (0,1,1) beats `a`.
- `.nav a:hover` – ink on hover. (0,2,1) beats `.nav a` (0,1,1), because `:hover` is a pseudo-class and counts like a class.
- **Menu numbers.** Each link reads like its chapter heading – "01 Profile", "02 Experience" – in the muted grey of the menu.
  - `white-space: nowrap` – number and label stay on one line. Without it, a squeezed header breaks "01" and "Profile" onto two lines (measured at 768 px).
  - `font-variant-numeric: tabular-nums` – equal-width digits, as on the headings (see Sections).
- **You are here.** `site.js` gives the link of the section being read `aria-current="location"`. The three `[aria-current]` rules then style it like the heading it points to: the link in ink, the number in the accent colour, the label in bold.
  - **The problem:** bold letters are wider. "Experience" is 73.9 px in regular weight and 78.9 px in bold (measured), so every change of section would push the pills to its right sideways.
  - **The fix:** `.label::after` adds a second copy of the label – `content: attr(data-label)` reads the `data-label` attribute that `build.py` writes – in bold, but with `height: 0`, `overflow: hidden` and `visibility: hidden`. It takes no height and shows nothing, yet it still has its full bold width.
  - `display: inline-grid` makes the label a one-column grid: the text and the hidden copy are stacked in that column, and a column is as wide as its widest item. So the label is always as wide as its bold version, whether it is bold or not. Measured: the menu stays on the same pixels in every state.
  - The trick sits on `.label`, not on the whole link, because a grid would put the number, the space and the label into separate rows. The number never turns bold, so it needs no reserve.
  - Two rules further down hide things on smaller screens; they come later in the file with the same or higher specificity, so they win (see Theme switch).
- `.langs` – the language pill.
  - `display: inline-flex; align-items: center;` – a flex row, centered vertically. As a child of the `.nav` flex container it is a flex item, and flex items are block-level anyway, so `inline-flex` acts like `flex` here.
  - `border: 1px solid var(--line);` – the hairline outline.
  - `border-radius: 999px;` – the pill trick. When the radii are larger than the box can hold, browsers scale them down until they fit, which gives perfect half-circle ends at any height.
  - `padding: 0.1rem 0.3rem;` – space inside the outline.
- `.langs > *` – the child combinator `>` with the universal selector: every direct child of the pill (the EN span, the DE link). Equal side padding, line height 1.6.
- `.nav .langs a` and `.nav .langs a:hover` – repeat what `.nav a` and `.nav a:hover` already set; currently redundant.
- `.langs [aria-current]` – an attribute presence selector: any element inside the pill that has `aria-current`, whatever the value. The current language is a `<span aria-current="page">`, not a link, because a page shouldn't link to itself. Ink and bold mark it.

## Theme switch

```css
/* theme switch: same pill as the languages */
.themes {
  display: inline-flex; align-items: center;
  border: 1px solid var(--line); border-radius: 999px;
  padding: 0.1rem 0.2rem;
}
.themes button {
  display: inline-grid; place-items: center;
  width: 1.7rem; height: 1.5rem; padding: 0; margin: 0;
  border: 0; border-radius: 999px; background: none;
  color: var(--muted); cursor: pointer;
}
.themes button:hover { color: var(--ink); }
.themes button[aria-pressed="true"] { color: var(--ink); }
.themes svg { width: 1rem; height: 1rem; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
.themes button[aria-pressed="true"] svg { stroke-width: 2; }
html:not(.js) .themes { display: none; }
@media (max-width: 47.99rem) { .nav .sect { display: none; } }
@media (max-width: 55.99rem) { .nav .sect .no { display: none; } }  /* narrow desktops: labels only, so the header fits */
```

- `.themes` – the same pill as `.langs`, with less side padding because the buttons bring their own width.
- `.themes button` – removes the browser's button look and builds a small target:
  - `display: inline-grid; place-items: center;` – a one-cell grid. `place-items` is shorthand for `align-items` plus `justify-items`, so the icon sits in the middle on both axes.
  - `width: 1.7rem; height: 1.5rem;` – the button size.
  - `padding: 0; margin: 0; border: 0; background: none;` – removes whatever padding, margin, border and background the browser gives buttons by default.
  - `border-radius: 999px;` – rounds the focus ring, which follows the radius.
  - `color: var(--muted);` – the icon color, passed on through `currentColor` below.
  - `cursor: pointer;` – buttons get the arrow cursor by default; the hand matches the links.
- `:hover` and `[aria-pressed="true"]` – ink. `site.js` sets `aria-pressed` on both buttons to reflect the active theme, and screen readers announce it as "pressed". Styling the ARIA attribute instead of a separate class means the visible state and the announced state come from one attribute and cannot drift apart.
- `.themes svg` – CSS can set SVG presentation properties directly:
  - `width: 1rem; height: 1rem;` – icon size.
  - `fill: none;` – outline icons, no filled shapes.
  - `stroke: currentColor;` – `currentColor` is the element's computed `color`. The SVG inherits it from the button, so hover and pressed states recolor the icon without rules of their own.
  - `stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;` – line weight in viewBox units (the icons use a 16 × 16 viewBox), with rounded ends and corners to match the rounded letterforms.
- `.themes button[aria-pressed="true"] svg { stroke-width: 2; }` – the active theme's icon is drawn heavier. Muted versus ink alone is a subtle difference; a change in shape keeps the state recognizable without relying on color.
- `html:not(.js) .themes { display: none; }` – without JavaScript the buttons cannot work, so they are removed. The system preference still applies through the media query.
- `@media (max-width: 47.99rem) { .nav .sect { display: none; } }` – on narrow screens the four section links disappear; logo, language pill and theme pill stay. The rule belongs to the navigation and only sits here by placement.
- `@media (max-width: 55.99rem) { .nav .sect .no { display: none; } }` – between 48 and 56rem the links stay, but without numbers. With numbers, the English header needs a window about 800 px wide and overflows at 768 px (measured); without them, it fits with room to spare. The space between number and label disappears with the number: at the start of a line, white space is dropped.

## Hero

```css
/* ---------- hero ---------- */

.hero { padding-block: clamp(3.5rem, 13vh, 8.5rem) clamp(3rem, 9vh, 6rem); }
```

- `padding-block` – padding on the block axis, which in horizontal text means top and bottom. Two values: start (top), then end (bottom).
- `clamp(MIN, PREFERRED, MAX)` – returns PREFERRED, but never less than MIN and never more than MAX; the same as `max(MIN, min(PREFERRED, MAX))`.
- `13vh` – 13% of the viewport height. The space above the name grows on tall screens and stays between 3.5rem and 8.5rem; below it, 9% between 3rem and 6rem.

```css
.hero h1 {
  margin: 0 0 1.1rem;
  font-size: clamp(2.6rem, 9.2vw, 5.75rem);
  line-height: 0.98;
  font-weight: 700;
  letter-spacing: 0.055em;
  text-transform: uppercase;
}
```

- `margin: 0 0 1.1rem;` – no default heading margin above, 1.1rem below.
- `font-size: clamp(2.6rem, 9.2vw, 5.75rem);` – fluid type. `vw` is 1% of the viewport width: the name is 9.2% of the screen width, never smaller than 2.6rem (41.6px), never larger than 5.75rem (92px). The maximum is reached at a 1000px-wide viewport, the minimum below about 452px. Without `clamp()` this would take a staircase of media queries. Trade-off: between the bounds, the size depends on the viewport width alone, so a visitor's larger default font size only moves the bounds. A preferred value that mixes units, such as `2rem + 6vw`, would follow that setting throughout. Browser zoom works either way, because zooming changes the viewport width in CSS pixels.
- `line-height: 0.98;` – very tight leading for display capitals. It only shows when the name wraps on a very narrow screen; capitals have no descenders, so the lines don't collide.
- `font-weight: 700;` – bold, from the 700 face.
- `letter-spacing: 0.055em; text-transform: uppercase;` – identical to `.home .name`. This is what makes the scaled hero name match the header name exactly (see the header section).

```css
.tagline {
  margin: 0 0 0.35rem;
  font-size: clamp(1.3rem, 3.3vw, 2rem);
  line-height: 1.25;
}
.claim {
  margin: 0 0 1.6rem;
  font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  line-height: 1.3;
  color: var(--muted);
}
.prompt {
  margin: 0;
  font-size: clamp(1rem, 2.1vw, 1.25rem);
  min-height: 1.6em;
}
```

- `.tagline` – "Performance Marketing · Data Science": fluid between 1.3rem and 2rem, line height 1.25 because larger text needs less relative leading, a small gap of 0.35rem below.
- `.claim` – the one-line claim, a step smaller, muted, 1.6rem of space before the prompt.
- `.prompt` – the terminal line `>_ sudo dream plan ship`.
  - `margin: 0;` and a fluid size between 1rem and 1.25rem.
  - `min-height: 1.6em;` – reserves one line of height (em here is the prompt's own font size). `site.js` empties the text and types it letter by letter; the reserved height keeps the line from changing size meanwhile, so nothing below it moves.
- The four hero sizes all reach their maximum at roughly 950–1000px viewport width, so the hierarchy keeps its proportions as the screen grows.

```css
.prompt .caret { display: inline-block; color: var(--accent); font-weight: 700; margin-right: 0.45em; }
.cursor {
  display: inline-block; width: 0.55em; height: 1.05em;
  margin-left: 0.12em; vertical-align: -0.16em;
  background: var(--accent);
}
```

- `.prompt .caret` – `display: inline-block` is required here: CSS transforms don't apply to ordinary inline boxes, and this caret gets transformed when it flies into the header. Bordeaux, bold, and the same 0.45em gap as the header caret.
- `.cursor` – the block cursor at the end of the prompt, an empty `<span>`.
  - `display: inline-block;` – an empty inline span has no width or height; as inline-block, `width` and `height` apply.
  - `width: 0.55em; height: 1.05em;` – about one character cell, scaling with the prompt's font size.
  - `margin-left: 0.12em;` – a small gap after the last letter.
  - `vertical-align: -0.16em;` – an inline-block sits on the text baseline by default. Lowering it by 0.16em lets it reach into the descender zone, like a terminal cursor that fills a whole character cell.
  - `background: var(--accent);` – a solid bordeaux block.

```css
@media (prefers-reduced-motion: no-preference) {
  .typed .cursor { animation: blink 1.1s steps(2, start) 4; }
}
@keyframes blink { to { visibility: hidden; } }
```

- `@keyframes blink { to { visibility: hidden; } }` – defines an animation named `blink`. Only the end state is written; the start is the element's normal value, `visible`.
- `.typed .cursor` – `site.js` adds `.typed` to `<html>` when the text is fully typed. An animation starts the moment its `animation` declaration begins to apply, so the blinking starts exactly then.
- `animation: blink 1.1s steps(2, start) 4;` – shorthand for name, length of one cycle, timing function and number of cycles.
  - `visibility` cannot fade. Between `visible` and `hidden` it stays `visible` at any progress strictly between 0 and 1 and becomes `hidden` only at the end. With a smooth timing function, the cursor would be visible almost all the time.
  - `steps(2, start)` cuts each cycle into two jumps and takes the first jump immediately: progress is 0.5 in the first half (visible) and 1 in the second (hidden) – 0.55s on, 0.55s off (measured). With `steps(2, end)` the values would be 0 and 0.5, both visible, and the cursor would never blink.
  - `4` – four cycles; then the animation ends, the cursor returns to its normal style and stays solid. Endless blinking distracts from reading. The number is chosen for a limit: WCAG 2.2.2 (Pause, Stop, Hide) asks for a pause control when blinking content runs longer than 5 seconds. Four cycles last 4.4 seconds and need none; six would already take 6.6.
- The rule sits inside `prefers-reduced-motion: no-preference`, so visitors who asked for less motion see a steady cursor. (`site.js` skips the typing for them as well.)

**Transitions versus animations.** A transition reacts to a change: when a property gets a new value (a class is added, `:hover` begins), the browser interpolates from the old value to the new one over the given time. It needs a trigger and runs once per change. An animation runs keyframes on its own timeline as soon as it applies; it can loop or run a fixed number of times, with no change of state needed. The cursor uses an animation; the back-to-top button uses transitions.

## Sections

```css
/* ---------- sections ---------- */

.sec {
  display: grid;
  gap: 0.75rem 2.5rem;
  padding-block: 3rem;
  border-top: 1px solid var(--line);
}
@media (min-width: 48rem) {
  .sec { grid-template-columns: 11rem minmax(0, 1fr); padding-block: 3.75rem; }
  .sec > h2 { position: sticky; top: 5rem; align-self: start; }
}
.sec > h2 {
  margin: 0;
  font-size: 1.25rem;
  line-height: 1.3;
  font-weight: 700;
}
/* chapter number, like a slide deck's parts: "01 Profile" – equal-width digits keep the titles aligned.
   The other sections of a chapter carry the same number invisibly (.ghost), so their titles line up with it. */
.sec > h2 .no { color: var(--accent); font-weight: 400; font-variant-numeric: tabular-nums; }
.sec > h2 .ghost { visibility: hidden; }
```

Each content section is a `.sec`: heading left and body right on wide screens, stacked on phones.

- `display: grid;` – a grid container. Without `grid-template-columns` there is a single column, so heading and body stack.
- `gap: 0.75rem 2.5rem;` – row gap 0.75rem, column gap 2.5rem (used once there are two columns).
- `padding-block: 3rem;` – vertical breathing room.
- `border-top: 1px solid var(--line);` – a hairline between sections.
- From 48rem:
  - `grid-template-columns: 11rem minmax(0, 1fr);` – two tracks: a fixed 11rem heading column and a flexible content column. `fr` is a share of the free space.
  - **Why `minmax(0, 1fr)`:** a plain `1fr` means `minmax(auto, 1fr)`, and `auto` as a minimum is the content's min-content width – the widest piece that cannot wrap, such as a long URL or a `nowrap` figure. If that piece is wider than the free space, a `1fr` column grows anyway and pushes the page wider than the screen. `minmax(0, 1fr)` lets the column shrink to the space actually available; wide content then has to wrap or overflow inside its own box instead of breaking the layout.
  - `padding-block: 3.75rem;` – a little more space on large screens.
  - `.sec > h2 { position: sticky; top: 5rem; align-self: start; }` – the heading stays visible while you scroll through a long section; `top: 5rem` keeps it clear of the header. The child combinator `>` limits this to the section's own `h2`.
  - **Why `align-self: start` is essential:** grid items stretch to the full height of their row by default. The row is as tall as the section body, so a stretched heading would already fill its whole area and have no room to move – sticky would do nothing. With `start`, the heading is only as tall as its text and can slide down inside the tall grid area. It stops at the end of the section, because a sticky element never leaves its containing block.
- `.sec > h2` – no margin, 1.25rem, line height 1.3, bold. This unconditional rule comes after the media query; the two set different properties, so the order doesn't matter.
- `.sec > h2 .no` – the chapter number in front of the heading: accent colour, regular weight, so the title stays the strong part.
  - `font-variant-numeric: tabular-nums` – switches the font to its equal-width digits (the OpenType feature `tnum`). By default Atkinson Hyperlegible uses proportional digits: in the regular weight used here, a "1" is about 60 % as wide as a "0". With tabular digits every number from 01 to 04 has the same width, so all titles start on the same pixel (measured).
- `.sec > h2 .ghost { visibility: hidden; }` – the sections inside a chapter (P⁴, Education, Approach, Sources) carry their chapter's number with this extra class. `visibility: hidden` hides it but keeps its box, so the title after it starts on the same pixel as the chapter's title (measured: all eight titles at the same x). The page reads like an outline.
  - Why not `padding-left` instead: the padding would have to equal the width of "01" plus a space in this font at this size – a number to measure and to update with every font change. The invisible number is always exactly as wide as the visible one.
  - Hidden text is not selected when you copy the heading, and the minimap skips it (`site.js` filters `.ghost`).

```css
.body { max-width: 42rem; }
.body > :first-child { margin-top: 0; }
.body > :last-child { margin-bottom: 0; }
:where(.body) p { margin: 0 0 1em; }
```

- `.body { max-width: 42rem; }` – caps the content column for a comfortable line length; on wide screens it doesn't use the whole grid track.
- `.body > :first-child { margin-top: 0; }` – `:first-child` without an element name means `*:first-child`: whatever comes first. Its top margin goes, so the first line of the body aligns with the heading. (0,2,0).
- `.body > :last-child { margin-bottom: 0; }` – the same at the end; the section padding alone sets the spacing.
- `:where(.body) p { margin: 0 0 1em; }` – paragraphs inside `.body` get space only below: 1em of their own font size. It matches exactly the same elements as `.body p` would; only its weight differs.

**`:where()` and why the default must be weak.** `:where()` is a pseudo-class that takes a list of selectors and matches whatever any of them matches – but it always adds zero specificity, whatever is inside. So `:where(.body) p` weighs (0,0,1), the same as a bare `p`.

This rule is a default: "paragraphs in the content column get a bottom margin unless something more specific says otherwise". A default must lose against every class rule written for a particular paragraph. Written as `.body p`, it would weigh (0,1,1) – one class plus one element – and beat any single-class rule such as `.intro` (0,1,0), wherever that rule stands in the file. The margins of seven paragraph classes would then be silently ignored: `.intro`, `.hello`, `.hw`, `.def`, `.when`, `.org` and `.ctx` (`.hello` would get 48px below instead of 16px). With `:where()`, every one of them wins by specificity, and the margins they declare are the ones you see (measured). Rules such as `.fields p` (0,1,1) win by specificity as well, wherever they stand in the file, and `.body > :first-child` and `.body > :last-child` (0,2,0) still trim the ends.

`:where()` works in all major browsers since early 2021. A browser that doesn't know it drops the whole rule, as with any selector it cannot parse, and paragraphs fall back to the browser's default margins.

```css
h3 { margin: 0 0 0.3rem; font-size: 1.125rem; line-height: 1.35; font-weight: 700; }

.muted { color: var(--muted); }
```

- `h3` – a type selector at (0,0,1): the base for every h3, easy to override (`.fields h3`, `.role h3` and `.group > h3` do). No top margin, a small one below, size, leading and weight.
- `.muted` – a utility class for secondary text, used for the university names in Education and the earlier cities in Contact.

## Ledger of results

```css
/* ledger of results */
.ledger { margin: 2rem 0 0; padding: 0; }
.ledger div {
  display: grid; gap: 0.15rem 1.5rem;
  padding-block: 0.9rem;
  border-top: 1px solid var(--line);
}
.ledger div:last-child { border-bottom: 1px solid var(--line); }
```

The ledger in the Profile section is a `<dl>`: a big figure (`<dt>`) with its explanation (`<dd>`), each pair wrapped in a `<div>` – which HTML allows inside `<dl>`.

- `.ledger { margin: 2rem 0 0; padding: 0; }` – space above, browser defaults removed.
- `.ledger div` – each row: a grid (on phones a single column, figure above text), vertical padding and a line above, like a ruled table.
- `.ledger div:last-child` – a closing line under the last row.

```css
@media (min-width: 36rem) {
  .ledger { display: grid; grid-template-columns: max-content 1fr; column-gap: 1.5rem; }
  .ledger div { grid-column: 1 / -1; grid-template-columns: subgrid; align-items: baseline; }
  @supports not (grid-template-columns: subgrid) { .ledger div { grid-template-columns: 15.5rem 1fr; } }
}
```

From 36rem, figures and explanations form two aligned columns.

- `.ledger { display: grid; grid-template-columns: max-content 1fr; column-gap: 1.5rem; }` – the list itself becomes the grid that owns the columns. `max-content` makes the first column exactly as wide as the widest figure, without wrapping.
- `grid-column: 1 / -1;` – each row div spans from the first grid line to the last. Negative line numbers count from the end, so `-1` is always the last line.
- `grid-template-columns: subgrid;` – the row div is a grid as well, but instead of defining its own columns it *uses its parent's*. All four `<dt>`s sit in the same parent column, so the `max-content` width is computed from all figures together, and every explanation starts at the same x position (measured: all four at 545px). Without subgrid, each div would be an independent grid with its own column widths, and each explanation would start wherever its own figure ends.
- `align-items: baseline;` – the 1.5rem bold figure and the body-size explanation share their first baseline and read as one line.
- `@supports not (grid-template-columns: subgrid) { … }` – a feature query: the rule inside applies only where the browser does *not* understand `subgrid`. Such a browser drops the `subgrid` declaration as invalid, and the row would fall back to a single column. The fallback gives every row the same fixed first column of 15.5rem – aligned too, just not sized to the content. Subgrid reached all major engines only in 2023 (Chrome 117 came last), which is why the fallback exists. `@supports` may be nested inside `@media`.

```css
.ledger dt {
  font-size: 1.5rem; font-weight: 700; line-height: 1.2;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.ledger dd { margin: 0; color: var(--muted); }
```

- `font-size: 1.5rem; font-weight: 700; line-height: 1.2;` – the figure as the visual anchor.
- `font-variant-numeric: tabular-nums;` – Atkinson's digits are proportional by default (the 1 is much narrower than the 0). `tabular-nums` switches on the font's tabular figures (the OpenType feature `tnum`, which these files contain): every digit gets the same width, so numbers line up.
- `white-space: nowrap;` – "€6k → €240k" stays on one line; with `max-content`, this line sets the width of the first column.
- `.ledger dd { margin: 0; color: var(--muted); }` – `<dd>` has a 40px left margin by default; removed. Explanations in muted grey.

## Fields of work

```css
/* fields of work */
.fields { display: grid; gap: 1.75rem 2.5rem; }
@media (min-width: 40rem) { .fields { grid-template-columns: 1fr 1fr; } }
.fields p { margin: 0; color: var(--muted); }
```

- `.fields` – the four P⁴ fields as a grid: one column on phones, two equal columns from 40rem. `1fr 1fr` splits the free space in half.
- `.fields p` – (0,1,1) beats the default `:where(.body) p` (0,0,1). Spacing comes from the grid gap instead of margins.

## Experience timeline

```css
/* experience timeline */
.roles { list-style: none; margin: 0; padding: 0; }
.role { display: grid; gap: 0.2rem 1.5rem; padding-bottom: 2rem; }
.role + .role { padding-top: 2rem; border-top: 1px solid var(--line); }
.role:last-child { padding-bottom: 0; }
@media (min-width: 36rem) { .role { grid-template-columns: 9.5rem 1fr; } }
```

- `.roles` – the `<ol reversed>` loses its numbers, margin and indent.
- `.role` – each job is a grid: date and content stacked on phones, side by side from 36rem (`9.5rem 1fr`). 2rem of space below.
- `.role + .role` – the adjacent sibling combinator: a `.role` directly after another `.role`. Every role except the first gets a line and space above, so lines appear only *between* roles.
- `.role:last-child { padding-bottom: 0; }` – no trailing space after the last role.

```css
.when {
  margin: 0; color: var(--muted); font-size: 0.95rem;
  font-variant-numeric: tabular-nums; padding-top: 0.15rem; white-space: nowrap;
}
.role h3 { margin-bottom: 0.1rem; }
.org { margin: 0 0 0.5rem; }
.org .place { color: var(--muted); }
.ctx { margin: 0 0 0.6rem; color: var(--muted); font-size: 1rem; }
```

- `.when` – the date column:
  - `margin: 0;` – no paragraph margin; the grid gap alone separates date and title when they stack on phones.
  - `color: var(--muted); font-size: 0.95rem;` – quieter than the job title.
  - `font-variant-numeric: tabular-nums;` – 05/2025 and 11/2023 take the same width.
  - `padding-top: 0.15rem;` – lowers the smaller date text so it lines up with the larger h3 next to it.
  - `white-space: nowrap;` – a date range never wraps.
- `.role h3 { margin-bottom: 0.1rem; }` – job title close to the company line.
- `.org` – the company line, 0.5rem above the next line. `.org .place` – the city, muted.
- `.ctx` – a context line (industry, size), muted at 1rem, 0.6rem above the tree. Both margins apply because `:where(.body) p` is weaker than any class.

## Projects

```css
/* projects */
.group + .group { margin-top: 2.5rem; }
.group > h3 { color: var(--muted); font-weight: 400; font-size: 1rem; margin-bottom: 1rem; }
.projects { list-style: none; margin: 0; padding: 0; display: grid; gap: 1.4rem; }
.projects h4 { margin: 0 0 0.15rem; font-size: 1.125rem; font-weight: 700; }
.projects p { margin: 0; }
.projects .stack { color: var(--muted); font-size: 0.95rem; margin-top: 0.2rem; }
```

- `.group + .group` – space between the two project groups, again only between.
- `.group > h3` – group headings as quiet labels: muted, regular weight, 1rem. They label; the project titles carry the weight.
- `.projects` – list reset, then `display: grid; gap: 1.4rem`. A grid gap instead of margins on list items: the space exists only between items, never before the first or after the last.
- `.projects h4` – the project title.
- `.projects p { margin: 0; }` – removes the paragraph default; (0,1,1) beats `:where(.body) p`.
- `.projects .stack` – the technology line, muted and smaller. At (0,2,0) it beats `.projects p` (0,1,1), so its `margin-top: 0.2rem` applies.

## Approach

```css
/* approach */
.principles { margin: 0; padding: 0; list-style: none; display: grid; gap: 1.4rem; }
.principles p { margin: 0; }
.principles strong { font-weight: 700; }
```

- `.principles` – the same list-as-grid pattern as `.projects`.
- `.principles p { margin: 0; }` – removes the paragraph default, as in `.projects`.
- `.principles strong { font-weight: 700; }` – the browser default for `<strong>` is `bolder`, which from regular text already resolves to 700. The rule makes it explicit but changes nothing.

## Education

```css
/* education */
.facts { margin: 0; }
.facts div { display: grid; gap: 0.1rem 1.5rem; padding-block: 0.75rem; border-top: 1px solid var(--line); }
.facts div:first-child { border-top: 0; padding-top: 0; }
@media (min-width: 36rem) { .facts div { grid-template-columns: 9.5rem 1fr; } }
.facts dt { color: var(--muted); font-size: 0.95rem; font-variant-numeric: tabular-nums; padding-top: 0.15rem; }
.facts dd { margin: 0; }
```

- `.facts` – another `<dl>` with div-wrapped pairs.
- `.facts div` – each row a grid, ruled with a line above.
- `.facts div:first-child` – no line and no top padding on the first row, so the list starts flush with the section heading.
- From 36rem, `9.5rem 1fr` – the same column width as the experience dates, so the years in Education line up with the dates in Experience.
- `.facts dt` – the year: muted, smaller, tabular digits, lowered 0.15rem like `.when`.
- `.facts dd { margin: 0; }` – removes the default indent.

## Contact: greeting and e-mail

```css
/* contact */
.hello {
  margin: 0 0 1rem;
  font-size: clamp(1.9rem, 5vw, 3rem);
  line-height: 1.1;
  font-weight: 700;
}
.mail { font-size: 1.25rem; font-weight: 700; }
```

- `.hello` – "Hallo · Hi · Ciao" as a display line: fluid between 1.9rem and 3rem, tight line height 1.1, bold. `margin: 0 0 1rem` – a fixed 16px below. In rem on purpose: the paragraph default of 1em would scale with the greeting's large size and reach 48px.
- `.mail` – the e-mail link, larger and bold: the main call to action.

## Dictionary entry

```css
/* dictionary entry: the word on GitHub, defined like Merriam-Webster, Duden or Treccani would */
.entry { margin: 0 0 1.75rem; }
.hw { margin: 0 0 0.4rem; display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.1rem 0.8rem; }
.hw dfn { font-style: normal; font-weight: 700; font-size: clamp(1.7rem, 4.4vw, 2.3rem); line-height: 1.15; }
.hw .syl { color: var(--muted); font-weight: 400; margin: 0 0.03em; }
.pos { font-style: italic; color: var(--muted); }
.ety { color: var(--muted); font-size: 1rem; }
.def { margin: 0; font-size: 1.25rem; line-height: 1.5; }
.ety i { font-style: italic; }
```

The Profile section opens like a dictionary entry: headword with syllable dots, part of speech, etymology, definition.

- `.entry` – the wrapper, 1.75rem of space below.
- `.hw` – the headword line:
  - `margin: 0 0 0.4rem;` – keeps the definition close to its headword.
  - `display: flex;` – headword, part of speech and etymology become flex items. Whitespace between flex items is not rendered, so the spaces in the HTML vanish and `gap` controls the spacing instead.
  - `flex-wrap: wrap;` – on narrow screens, "noun" and the etymology move to the next line instead of squeezing the headword.
  - `align-items: baseline;` – the large headword and the small labels share a baseline, as in a printed dictionary.
  - `gap: 0.1rem 0.8rem;` – a small row gap when wrapped, 0.8rem between items.
- `.hw dfn` – `<dfn>` marks the term being defined. Browsers italicize it by default, so `font-style: normal` undoes that. Bold, fluid between 1.7rem and 2.3rem, line height 1.15.
- `.hw .syl` – the middle dots between syllables (mar·ke·tin·ker·er): muted, regular weight inside the bold word, with a hair of space (0.03em) on each side.
- `.pos` – the part of speech ("noun"), italic and muted, as dictionaries set it. One of the two reasons the italic font file loads.
- `.ety` – the etymology "[marketer × tinkerer]", muted, at 1rem.
- `.def` – the definition at 1.25rem, `margin: 0`. The space below the entry comes from `.entry` alone.
- `.ety i { font-style: italic; }` – `<i>` is italic by default, so this repeats the default. It also sits after `.def`, apart from the other `.ety` rule.

## P⁴ and intro lines

```css
/* P⁴ */
.sec > h2 sup { font-size: 0.62em; line-height: 0; vertical-align: 0.55em; margin-left: 0.04em; }
.intro { margin: 0 0 1.5rem; color: var(--muted); }
.intro strong { color: var(--ink); }
.fields h3 { font-size: 1.375rem; margin-bottom: 0.25rem; }
```

- `.sec > h2 sup` – the 4 in the heading "P⁴". The HTML uses `P<sup>4</sup>` rather than the character ⁴, which the font subset doesn't contain.
  - `font-size: 0.62em;` – 62% of the heading size.
  - `line-height: 0;` – the browser's default `vertical-align: super` raises the box and can make its line taller, so lines with a superscript get uneven spacing. With a line height of zero, the raised box adds nothing to the line's height.
  - `vertical-align: 0.55em;` – raises it by 0.55em of the superscript's own, already reduced, size.
  - `margin-left: 0.04em;` – a hair of space after the P.
- `.intro` – the short muted line that opens a section ("P as in Peter.", "Stop starting. Start finishing."), with 1.5rem of space below – more than a normal paragraph, to set it apart from what it introduces.
- `.intro strong { color: var(--ink); }` – bold parts in full ink.
- `.fields h3` – the four field names, larger than other h3s.

## #JobAlert tree

```css
/* #JobAlert tree: ├── and └── drawn with borders, so they align in any font */
.tree { list-style: none; margin: 0.35rem 0 0; padding: 0; }
.tree li { position: relative; padding-left: 1.7em; margin: 0; padding-bottom: 0.2rem; }
.tree li::before {
  content: ""; position: absolute; left: 0.3em; top: 0; bottom: 0;
  border-left: 1px solid var(--muted);
}
.tree li:last-child::before { bottom: auto; height: 0.8em; }
.tree li::after {
  content: ""; position: absolute; left: 0.3em; top: 0.8em; width: 0.95em;
  border-top: 1px solid var(--muted);
}
.tree .k { font-weight: 700; }
.tree .k::after { content: ":"; }
```

Each role lists its key facts as a file tree, the way the Unix `tree` command prints folders. The lines are drawn with CSS instead of the characters ├── and └──. Those characters are not in the Latin subset, so the browser would borrow them from a fallback font with different proportions. And their vertical strokes only join up from row to row when the glyphs fill the whole line height – with a line height of 1.55 they would leave gaps. Borders are drawn by the browser itself and line up in any font at any line height.

- `.tree` – list reset, a little space above.
- `.tree li`:
  - `position: relative;` – makes the item the containing block for its absolutely positioned pseudo-elements.
  - `padding-left: 1.7em;` – room for the lines; in em, so it scales with the text.
  - `margin: 0; padding-bottom: 0.2rem;` – the space between items is padding, inside the item, so the vertical line runs through it and meets the next item's line.
- **Pseudo-elements.** `::before` and `::after` create two extra boxes inside an element, before and after its content, without any markup. They exist only when `content` is set – here to an empty string.
- `.tree li::before` – the vertical line:
  - `content: ""; position: absolute;` – an empty box taken out of the flow.
  - `left: 0.3em; top: 0; bottom: 0;` – setting both `top` and `bottom` stretches the box over the full height of the item, padding included.
  - `border-left: 1px solid var(--muted);` – the box has no width; its left border is the line.
- `.tree li:last-child::before { bottom: auto; height: 0.8em; }` – on the last item, the vertical line stops at 0.8em, where the horizontal branch starts. That turns ├ into └.
- `.tree li::after` – the horizontal branch: from `left: 0.3em`, `width: 0.95em`, drawn as a top border at `top: 0.8em` – about the middle of the first text line (1.55 × 18px = 27.9px line height, half of that is 0.78em). It ends 0.45em before the text.
- `.tree .k { font-weight: 700; }` – the key ("Scope", "Result").
- `.tree .k::after { content: ":"; }` – the colon after the key is generated. The HTML stays plain (`<span class="k">Scope</span>`), the punctuation lives in the CSS.

## Drawn arrows

```css
/* drawn arrow: → is not part of Atkinson Hyperlegible */
.arr { display: inline-block; width: 0.95em; height: 0.62em; margin: 0 0.12em; vertical-align: 0.06em; }
.arr svg { display: block; width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; overflow: visible; }
.ledger dt .arr svg { stroke-width: 2.1; }
```

The arrow in "€6k → €240k" is a small inline SVG in `<span class="arr" role="img" aria-label="to">`; screen readers read "to". The → character is missing from the font files, so a fallback font would draw it, with its own weight and size.

- `.arr`:
  - `display: inline-block;` – sits in the line of text and accepts width and height.
  - `width: 0.95em; height: 0.62em;` – in em, so the arrow scales with its text: small in the timeline, large in the ledger figures.
  - `margin: 0 0.12em;` – a little space on both sides.
  - `vertical-align: 0.06em;` – lifts the box slightly off the baseline, so the arrow's center sits at about half the height of capitals and digits.
- `.arr svg`:
  - `display: block;` – an `<svg>` is inline by default and sits on the baseline with room for descenders below it. As a block it fills the span exactly.
  - `width: 100%; height: 100%;` – fills the span.
  - `fill: none; stroke: currentColor;` – a line drawing in the current text color: ink in a figure, muted in a muted line.
  - `stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round;` – line weight in viewBox units, rounded ends.
  - `overflow: visible;` – an SVG clips at its viewBox by default; this keeps round line caps near the edge from being cut off.
- `.ledger dt .arr svg { stroke-width: 2.1; }` – inside the big bold ledger figures, a heavier stroke matches the bold digits. (0,2,2) beats `.arr svg` (0,1,1).

## Footnotes

```css
/* footnotes */
.fnref { font-size: 0.68em; line-height: 0; vertical-align: 0.6em; margin-left: 0.08em; }
.fnref a { text-decoration: none; color: var(--accent); font-weight: 700; padding: 0 0.1em; }
.fnref a:hover { text-decoration: underline; }
.notes { margin: 0; padding-left: 1.4em; color: var(--muted); font-size: 0.95rem; display: grid; gap: 0.5rem; }
.notes li::marker { color: var(--ink); font-weight: 700; }
.notes .back { text-decoration: none; color: var(--accent); font-weight: 700; margin-right: 0.15em; }
.notes li:target { color: var(--ink); }
```

The Education section has footnote numbers (`<sup class="fnref">`) that link to the Sources section, and back links (`^`) that return to the text.

- `.fnref` – the same superscript technique as P⁴: smaller (0.68em), `line-height: 0` so the line spacing stays even, raised by 0.6em, a hair of space before.
- `.fnref a` – no underline (a raised number is clearly a reference), bordeaux, bold, and `padding: 0 0.1em` to widen the tiny target a little.
- `.fnref a:hover { text-decoration: underline; }` – the shorthand switches the underline on and resets its color to `currentColor`, here the accent.
- `.notes` – the ordered list of sources:
  - `margin: 0; padding-left: 1.4em;` – list numbers (markers) are drawn outside the item's box, in the list's left padding; 1.4em leaves room for them.
  - `color: var(--muted); font-size: 0.95rem;` – quieter than body text.
  - `display: grid; gap: 0.5rem;` – even spacing between sources. List items inside a grid keep `display: list-item` (measured), so their numbers still render.
- `.notes li::marker` – `::marker` is the pseudo-element for a list item's number or bullet. Only a few properties work on it (color, font properties, `content` and a few more). Ink and bold numbers against the muted text.
- `.notes .back` – the `^` back link: no underline, bordeaux, bold, a little space after it.
- `.notes li:target` – `:target` matches the element whose `id` equals the URL fragment. Click footnote 1, the URL ends in `#fn-ds`, and that list item switches from muted to ink: a highlight for the note you came to read, with no JavaScript.

## Contact: online and offline

```css
/* contact: Work online | Live offline */
.reach { margin: 0; display: grid; gap: 0.5rem; }
.reach div { display: grid; grid-template-columns: 5.5rem 1fr; gap: 0 1rem; align-items: baseline; }
.reach dt { color: var(--muted); font-size: 0.95rem; }
.reach dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
```

- `.reach` – the contact list; its rows are spaced by a grid gap.
- `.reach div` – each row a two-column grid at every width: a 5.5rem label column ("Online", "Offline") and the rest. `align-items: baseline` aligns the small label with the 1.25rem e-mail link.
- `.reach dt` – muted, smaller label.
- `.reach dd`:
  - `margin: 0;` – no default indent.
  - `min-width: 0;` – grid items default to `min-width: auto`, which keeps them at least as wide as their longest unbreakable word. On a narrow phone, the e-mail address could then push the row wider than the screen.
  - `overflow-wrap: anywhere;` – allows a line break at any character when a word doesn't fit. Together, the two let the address break instead of overflowing.

## 404 page

```css
/* 404 */
.lost { padding-block: clamp(3.5rem, 13vh, 8.5rem) clamp(3rem, 9vh, 6rem); }
.lost .code { margin: 0; font-size: clamp(3rem, 10vw, 6rem); line-height: 1; font-weight: 700; letter-spacing: 0.04em; }
.lost h1 { margin: 0.6rem 0 0.35rem; font-size: clamp(1.3rem, 3.3vw, 2rem); line-height: 1.25; font-weight: 400; }
.dki { font-family: inherit; font-size: inherit; color: var(--accent); }
```

`404.html` reuses the hero's rhythm, without docking.

- `.lost` – the same vertical padding as `.hero` (the values are repeated, not shared), so the error page has the home page's proportions.
- `.lost .code` – the large "404", fluid and bold, with slight letter spacing.
- `.lost h1` – the message, sized like the tagline, in regular weight so it reads as a sentence. The page also reuses `.claim` and `.prompt` from the hero.
- `.dki` – the `{KeyWord:Page}` placeholder, a nod to Google Ads keyword insertion, marked up as `<code>`. Browsers render `<code>` in a monospace font at a smaller size; `font-family: inherit` and `font-size: inherit` make it match the heading, and the accent color marks it.

## Back-to-top button

```css
/* back to top: appears once the name has docked; on wide screens it sits under the minimap */
.to-top {
  position: fixed; z-index: 5;
  right: max(1rem, calc(env(safe-area-inset-right, 0px) + 1rem));
  bottom: max(1rem, calc(env(safe-area-inset-bottom, 0px) + 1rem));
  width: 2.75rem; height: 2.75rem; border-radius: 50%;
  display: grid; place-items: center;
  text-decoration: none; color: var(--ink);
  background: color-mix(in srgb, var(--paper) 92%, transparent);
  -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px);
  border: 1px solid var(--line);
  opacity: 0; visibility: hidden; transform: translateY(0.5rem);
  transition: opacity 0.2s, transform 0.2s, visibility 0s linear 0.2s;
}
```

- `position: fixed; z-index: 5;` – fixed to the viewport: out of the flow, unaffected by scrolling. Unlike a sticky element, it has no place in the document at all.
- `right: max(1rem, calc(env(safe-area-inset-right, 0px) + 1rem));` and the same for `bottom` – 1rem from the edges, plus the safe-area inset on phones with rounded corners or a home indicator. `max()` returns the larger argument. As written, the `calc()` can never be smaller than 1rem (insets are never negative), so the `max()` changes nothing; and as with the header, the insets are 0 without `viewport-fit=cover`.
- `width: 2.75rem; height: 2.75rem; border-radius: 50%;` – a 44px circle, the common minimum size for touch targets. 50% radius on a square gives a circle.
- `display: grid; place-items: center;` – centers the arrow icon.
- `text-decoration: none; color: var(--ink);` – it's a link: no underline, ink icon.
- `background: …; backdrop-filter: blur(6px); border: 1px solid var(--line);` – the same frosted look as the header.
- `opacity: 0; visibility: hidden; transform: translateY(0.5rem);` – the hidden state: transparent, not interactive, 0.5rem lower.
- `transition: opacity 0.2s, transform 0.2s, visibility 0s linear 0.2s;` – the transitions used when *entering* this hidden state.

**The visibility trick.** `opacity: 0` alone hides the button only for the eye: it stays clickable and keyboard-focusable, so a Tab press could land on an invisible control. `visibility: hidden` takes it out of the tab order, the accessibility tree and mouse hit-testing. But `visibility` cannot fade, and if it switched to `hidden` at once, the fade-out would be cut short. Hence the entry `visibility 0s linear 0.2s`: duration 0, delay 0.2s – it flips to `hidden` only after the 0.2s fade has finished. On the way in, the visible state's `transition` (next rule) has no `visibility` entry, so visibility switches on immediately and the fade-in can be seen. The mechanism behind it: a transition always uses the `transition` value of the state being entered.

```css
.top.docked ~ .to-top { opacity: 1; visibility: visible; transform: none; transition: opacity 0.2s, transform 0.2s; }
html:not(.js) .to-top { opacity: 1; visibility: visible; transform: none; }
.to-top:hover { border-color: var(--accent); color: var(--accent); }
.to-top:focus-visible { border-radius: 50%; }
.to-top svg { width: 1.1rem; height: 1.1rem; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
@media (prefers-reduced-motion: reduce) { .to-top, .top.docked ~ .to-top { transition: none; } }
@media (min-width: 74rem) and (min-height: 30rem) {
  .to-top { right: calc(1.75rem + (4.25rem - 2.75rem) / 2); bottom: 1.75rem; }
}
```

- `.top.docked ~ .to-top` – the general sibling combinator `~`: a `.to-top` that comes *after* a `.top.docked` element with the same parent. In the HTML, `<a class="to-top">` follows `<header class="top">` inside `<body>`. When `site.js` adds `.docked` to the header, the button's state follows from CSS alone; no script touches the button. Apart from the newer `:has()`, selectors can only look at later siblings and at descendants, which is why the button comes after the header in the markup. The declarations: fully opaque, visible, back in place, and transitions without the visibility delay. (0,3,0) beats `.to-top` (0,1,0).
- `html:not(.js) .to-top` – without JavaScript there is no docking, so the button is simply always visible. It is a plain link to `#top` and needs no script.
- `.to-top:hover` – bordeaux border and icon.
- `.to-top:focus-visible { border-radius: 50%; }` – keeps the circle round under keyboard focus. The global `a:focus-visible` sets `border-radius: 2px` at (0,1,1), which beats the base `.to-top` (0,1,0) and would turn the button into a rounded square. This rule, (0,2,0), wins it back, and the focus ring follows the circle (measured: 50% while focused).
- `.to-top svg` – an outline arrow in `currentColor`, slightly heavier (1.8) than the theme icons.
- `@media (prefers-reduced-motion: reduce)` – no fade and no slide for visitors who asked for less motion. Both selectors are needed: `.top.docked ~ .to-top` sets its own `transition` at (0,3,0), which `.to-top` alone could not override.
- `@media (min-width: 74rem) and (min-height: 30rem)` – the same condition as the minimap. `right: calc(1.75rem + (4.25rem - 2.75rem) / 2)` comes to 2.5rem: the minimap starts 1.75rem from the edge and is 4.25rem wide, so adding half the difference between minimap and button width centers the button under it. `bottom: 1.75rem` puts the button's top edge at 4.5rem, 0.75rem below the minimap's lower end at 5.25rem. Same specificity as the base rule, later in the file, so it wins.

## Footer

```css
/* footer */
.foot { border-top: 1px solid var(--line); padding-block: 2rem 2.5rem; color: var(--muted); font-size: 0.95rem; }
.foot .wrap { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.75rem 2rem; }
.foot p { margin: 0; }
.foot nav { display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; }
.foot a { color: inherit; }
```

- `.foot` – a line above, 2rem of padding above and 2.5rem below, muted and smaller text.
- `.foot .wrap` – a wrapping flex row: motto left, legal links right (`space-between`), two lines on narrow screens. `gap: 0.75rem 2rem` sets row and column gaps.
- `.foot p { margin: 0; }` – the motto without the browser's default paragraph margins. The footer is outside `.body`, so `:where(.body) p` doesn't reach it.
- `.foot nav` – legal links and copyright as another wrapping flex row.
- `.foot a { color: inherit; }` – repeats the global `a { color: inherit; }`; redundant.

## Legal pages

```css
/* legal pages */
.legal { padding-block: 3rem 4rem; }
.legal h1 { font-size: clamp(2rem, 5vw, 2.75rem); line-height: 1.15; margin: 0 0 2rem; }
.legal h2 { font-size: 1.25rem; margin: 2.25rem 0 0.5rem; }
.legal .body { max-width: 40rem; }
.legal address { font-style: normal; }
.legal ul { padding-left: 1.2em; }
```

On `impressum.html` and `datenschutz.html`, the frame carries both classes (`class="wrap legal"`) and contains a `.body`.

- `.legal` – vertical padding in place of a hero.
- `.legal h1` – a fluid page title, tight leading, 2rem below.
- `.legal h2` – section headings at 1.25rem, with more space above than below, so each heading visibly belongs to the text that follows.
- `.legal .body { max-width: 40rem; }` – a slightly narrower column for long legal text. (0,2,0) beats `.body`.
- `.legal address { font-style: normal; }` – browsers italicize `<address>` by default.
- `.legal ul { padding-left: 1.2em; }` – a smaller list indent than the default 40px.

## Minimap

```css
/* ---------- minimap ---------- */

.minimap { display: none; }
@media (min-width: 74rem) and (min-height: 30rem) {
  .minimap {
    display: block;
    position: fixed;
    right: 1.75rem;
    top: 5rem;
    bottom: 5.25rem;
    width: 4.25rem;
    cursor: pointer;
    touch-action: none;
    z-index: 4;
  }
}
```

On wide screens, a rail at the right edge shows the page as lines of code, like a code editor's minimap. `site.js` draws one bar per rendered line of text; click or drag to navigate.

- `.minimap { display: none; }` – hidden by default. `site.js` reads the computed `display` and builds nothing while it is `none`, so this media query is the single switch for the whole feature.
- `(min-width: 74rem) and (min-height: 30rem)` – both conditions must hold: wide enough for the lane that `.wrap` reserves, tall enough for a usable rail.
  - `display: block; position: fixed;` – shown, and fixed to the viewport.
  - `right: 1.75rem; top: 5rem; bottom: 5.25rem;` – with both `top` and `bottom` set and no height, a positioned box stretches between them: the rail fills the viewport height below the header and above the back-to-top button.
  - `width: 4.25rem;` – the rail width.
  - `cursor: pointer;` – signals that the rail is clickable.
  - `touch-action: none;` – on a touch screen the browser would normally claim a drag for scrolling and cancel the pointer events. `none` leaves all touch gestures on the rail to the pointer handlers in `site.js`, so dragging works.
  - `z-index: 4;` – below header and button (5).

```css
.mm-measure .sec > h2 { position: static; }
```

- `.mm-measure .sec > h2 { position: static; }` – a rule for the script, not for the visitor. To place a heading's bar, `site.js` asks the browser for the heading's rectangles on screen. A sticky heading reports where it is *stuck* at that moment, which depends on the current scroll position, so its bar would land in the wrong place on the map. While measuring, `site.js` adds `.mm-measure` to `<html>`; this rule turns the sticky headings back into ordinary ones, and they report their place in the flow. (0,2,1) beats the sticky `.sec > h2` (0,1,1). The script removes the class again in the same run of code. The browser recalculates the layout for each measurement, but it paints no frame in between, so the headings never visibly unstick.

```css
.mm-bar {
  position: absolute; left: 0; height: 2px; border-radius: 1px;
  background: var(--bar);
}
.mm-bar.h { background: var(--bar-lit); }
.mm-bar.lit { background: var(--bar-lit); }
.mm-bar.h.lit { background: var(--ink); }
```

- `.mm-bar` – one bar:
  - `position: absolute;` – placed inside the rail. A fixed element counts as positioned, so the rail is the bars' containing block. Absolute positioning also turns the `<span>` into a block box, so width and height apply.
  - `left: 0; height: 2px;` – defaults only: `site.js` writes `top`, `left`, `width` and `height` inline on every bar, and inline styles win.
  - `border-radius: 1px; background: var(--bar);` – a faint, slightly rounded line.
- `.mm-bar.h` – bars for h1 and h2 headings are darker.
- `.mm-bar.lit` – bars inside the current viewport; `site.js` toggles the class on scroll.
- `.mm-bar.h.lit` – a heading inside the viewport gets full ink. (0,3,0) beats both two-class rules, whatever their order.

```css
.mm-view {
  position: absolute; left: -0.5rem; right: -0.5rem;
  border-radius: 3px;
  background: color-mix(in srgb, var(--ink) 6%, transparent);
  border: 1px solid var(--line);
  pointer-events: none;
}
```

- `.mm-view` – the box that marks the visible part of the page.
  - `position: absolute; left: -0.5rem; right: -0.5rem;` – negative offsets let it stick out 0.5rem on both sides of the rail. `site.js` sets `top` and `height`.
  - `border-radius: 3px;` – soft corners.
  - `background: color-mix(in srgb, var(--ink) 6%, transparent);` – a 6% tint of the text color: it darkens light paper and lightens dark paper, so one rule serves both themes.
  - `border: 1px solid var(--line);` – a hairline frame.
  - `pointer-events: none;` – the box ignores the mouse; clicks reach the rail beneath it.

## Print

```css
@media print {
  .top, .minimap, .skip, .to-top { display: none; }
  .hero h1, .hero .prompt .caret { transform: none !important; opacity: 1 !important; }
  .hero .prompt .cmd, .hero .prompt .cursor { opacity: 1 !important; }
  .sec > h2 { position: static; }
  body { font-size: 11pt; }
}
```

- `@media print` – applies when the page is printed or saved as PDF.
- `.top, .minimap, .skip, .to-top { display: none; }` – navigation and screen-only aids don't belong on paper. The back-to-top button matters most here: browsers typically repeat fixed elements on every printed page.
- `.hero h1, .hero .prompt .caret { transform: none !important; opacity: 1 !important; }` – puts the name and its caret back in the hero. Once you have scrolled down, the name has docked: `site.js` has moved and shrunk it with an inline `transform`, and `.hero.docked` has set its opacity to 0. With the header hidden on paper, the printout would otherwise carry no name at all.
  - **Why `!important`.** An inline style beats every normal stylesheet declaration, whatever its specificity. The one way for a stylesheet to override it is `!important`: important declarations from the site outrank normal ones, inline styles included. The same flag also beats `.hero.docked`'s `opacity: 0` (0,2,1), which (0,1,1) alone could not.
  - Measured with Chromium's print emulation after scrolling: name visible, no transform.
- `.hero .prompt .cmd, .hero .prompt .cursor { opacity: 1 !important; }` – the rest of the prompt line. During the flight, `site.js` fades the typed motto and the cursor block with inline `opacity`, down to 0 once the name has docked. They don't move, so only the opacity needs resetting, and again only `!important` can beat the inline value. A page printed after scrolling shows the full `>_ sudo dream plan ship` with its cursor.
- `.sec > h2 { position: static; }` – sticky makes no sense on a printed page. Same specificity as the sticky rule, later in the file, so it wins.
- `body { font-size: 11pt; }` – `pt` (1/72 inch) is a natural unit on paper. Only text that inherits its size from `body` changes; everything sized in rem (headings, ledger figures, the hero name) stays relative to the root.

---

## Try it

Open peterstieg.com (or `site/index.html` locally) and the DevTools (F12).

1. **Change the accent.** In the Elements panel, select `<html>`. In the Styles pane, find the `:root` rule and change `--accent` to `#1A5A7A`. Prompt caret, cursor, hover underlines, footnote numbers and focus ring change at once – one variable, inherited everywhere. Then click the moon button: your color is gone, because `:root[data-theme="dark"]` (0,2,0) defines its own `--accent` and beats `:root` (0,1,0). Change it there to see it come back.
2. **Walk through the three theme states.** Remove the `data-theme` attribute from `<html>` (double-click it in the Elements panel). Open the Rendering tool (Ctrl+Shift+P, type "Rendering") and switch "Emulate CSS media feature prefers-color-scheme" between light and dark – the page follows. Now add `data-theme="light"` to `<html>` and emulate dark again: the page stays light, because `:not()` excludes it from the media block. Finally set `data-theme="dark"` and emulate light: dark wins without any media query.
3. **Remove subgrid.** Make the window wider than 36rem and select one of the `<div>`s inside `<dl class="ledger">`. In the `.ledger div` rule, untick `grid-template-columns: subgrid`: every row collapses to one column, figure above text. Then add `grid-template-columns: max-content 1fr` to the same rule: each row is now its own grid with its own first column, and the four explanations start at four different positions (measured: 410px to 545px). Click the "grid" badge next to `<dl class="ledger">` to see the tracks.

## Key terms

- **Cascade** – the algorithm that picks one value when several rules set the same property on an element: origin and importance first, then specificity, then source order.
- **Specificity** – the weight of a selector, counted as (IDs, classes/attributes/pseudo-classes, elements/pseudo-elements) and compared from the left. Media queries and `:where()` add none; inline styles beat all selectors unless a stylesheet declaration is `!important`.
- **Custom property** – a variable such as `--accent`, read with `var()`. It inherits and is resolved per element, so changing it on `<html>` re-colors the whole page.
- **rem and em** – rem is relative to the root font size (the visitor's default, 16px unless changed); em to the element's own font size. In media queries, both refer to the browser's initial font size.
- **clamp()** – `clamp(MIN, PREFERRED, MAX)`: a fluid value with a floor and a ceiling, used for type that grows with the viewport.
- **fr and minmax()** – `fr` is a share of a grid's free space; `minmax(0, 1fr)` lets a track shrink below its content's minimum width, which a plain `1fr` does not.
- **Subgrid** – `grid-template-columns: subgrid` makes a nested grid reuse its parent's column tracks, so content in different rows aligns.
- **Sticky and fixed** – sticky stays in the flow and sticks at an offset while its containing block is on screen; fixed leaves the flow and is placed relative to the viewport.
- **Stacking context** – a group of elements whose z-index values are compared only with each other. Created, for example, by a position with a z-index, `transform`, `opacity` below 1 or `backdrop-filter`.
- **Pseudo-element** – a box CSS generates without markup: `::before`, `::after`, `::marker`, `::selection`. `::before` and `::after` need `content` to exist.
- **Transition and animation** – a transition interpolates between two values when a value changes; an animation runs keyframes on its own timeline, can repeat and needs no trigger.
- **User-preference media query** – `prefers-color-scheme` and `prefers-reduced-motion` read OS or browser settings, so the page can follow the visitor's choices live.

---

[Previous: The HTML](02-html.md) · [Next: JavaScript](04-js.md)
