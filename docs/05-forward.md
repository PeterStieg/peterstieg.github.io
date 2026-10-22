# The forward page: peterstieg.github.io

The site lives on IONOS at peterstieg.com. This repository is also published by GitHub Pages at peterstieg.github.io, and that address should lead to the same place. Instead of a bare "Moved to …", a visitor sees a two-second terminal scene, then lands on peterstieg.com:

```
>_ mv -v peterstieg.github.io peterstieg.com
renamed 'peterstieg.github.io' -> 'peterstieg.com'
>_ cd peterstieg.com
```

`mv -v` is the real Unix command for moving or renaming, and `renamed '…' -> '…'` is exactly what GNU `mv` prints with `-v` (verbose). `cd` changes into the new place – which is what the browser does next.

Five files, all at the repository root, none of them in `site/`:

| File | Job |
|---|---|
| `index.html` | the page for `peterstieg.github.io/` |
| `404.html` | the same page for every other path |
| `forward/forward.css` | look: colours, terminal lines, cursor |
| `forward/forward.js` | behaviour: typing, forwarding, skip and stop |
| `forward/fonts/` | Atkinson Hyperlegible Mono, the monospaced sibling of the site's typeface (SIL Open Font License) |

Figures marked "measured" come from Chromium on a local server that behaves like GitHub Pages.

## Why a page and not a redirect

- **GitHub Pages serves files, nothing else.** There is no server configuration – no `.htaccess`, no way to answer with a real `301 Moved Permanently`. The only tools left are in the page itself: a `<meta http-equiv="refresh">` or JavaScript that sets `location`.
- **404.html catches the rest.** For any path without a file, Pages answers with the repository's `404.html` (status 404). So one copy of the page under that name forwards every old link, including the `/site/…` addresses from before the forwarding existed.
- **`_config.yml` keeps the source out.** Its `exclude` list stops Pages from publishing `site/`, `src/`, `docs/` and the README, so the forward page is all there is. One address for search engines, and the privacy statement (host: IONOS) stays true.

## index.html and 404.html

Both files are identical below their first comment. Change one, change both.

### Head: telling search engines where the content is

```html
<link rel="canonical" href="https://peterstieg.com/">
<meta name="robots" content="noindex">
```

- `canonical` names the address that counts; `noindex` keeps this copy out of search results. Together they say: index peterstieg.com, not this.

```html
<meta name="theme-color" content="#F7F6F3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#181A1C" media="(prefers-color-scheme: dark)">
```

- The browser chrome on phones takes the page's background colour – the same two values as on peterstieg.com. There is no theme switch here, so the system setting decides.

### The boot script and its failsafe

```html
<script>document.documentElement.classList.add("js");setTimeout(function(){if(!window.fw)document.documentElement.classList.remove("js")},2000)</script>
```

- **The `js` class** goes on `<html>` before anything is painted. With it, the CSS hides the terminal lines so `forward.js` can type them; without it, the full transcript shows at once. Set later, the finished text would flash up and then vanish.
- **The failsafe:** if `forward.js` never arrives (blocked, network error), the lines would stay hidden for good. So after two seconds the script checks `window.fw` – a flag the first line of `forward.js` sets – and, if it is missing, removes the class again. The page then shows the plain version with its link.
- It sits before the stylesheet `<link>` for the same reason as on the main site: an inline script after a stylesheet that is still loading has to wait for it.

### Fonts, icon, styles, script

```html
<link rel="preconnect" href="https://peterstieg.com">
<link rel="icon" href="https://peterstieg.com/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/forward/fonts/atkinson-hyperlegible-mono-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
```

- `preconnect` opens the connection to peterstieg.com while the scene plays, so the jump at the end starts faster. The favicon comes from there anyway.
- `preload` fetches both font files right away instead of waiting until the CSS asks for them. Fonts are always fetched in CORS mode, so a font preload needs `crossorigin` – even on the same server – or the browser downloads the file twice.
- **Absolute paths** (`/forward/…`, starting with a slash) are a must here. `404.html` answers at any depth: for `/site/de/`, a relative `forward/forward.css` would resolve to `/site/de/forward/forward.css`, which does not exist.

```html
<script src="/forward/forward.js" defer></script>
<noscript><meta http-equiv="refresh" content="3; url=https://peterstieg.com/"></noscript>
```

- `defer`: download in parallel, run once the document is parsed.
- **Without JavaScript**, the `<noscript>` content counts: a refresh to peterstieg.com after three seconds (measured: 3.0 s). It goes to the start page, because without a script the path cannot be carried over. A `<meta>` inside `<noscript>` is valid in the head.

### Body

```html
<p class="line" aria-hidden="true"><span class="caret">&gt;_</span><span class="cmd">mv -v peterstieg.github.io peterstieg.com</span></p>
<p class="line out" aria-hidden="true">renamed 'peterstieg.github.io' -&gt; 'peterstieg.com'</p>
<p class="line" aria-hidden="true"><span class="caret">&gt;_</span><span class="cmd">cd peterstieg.com</span></p>
<p class="go">Moved to <a href="https://peterstieg.com/">peterstieg.com</a>.</p>
```

- **The full text is in the HTML.** The script empties the two commands and types them back; without the script, they simply stand there.
- `&gt;` is `>` written so the parser cannot mistake it for the end of a tag.
- **`aria-hidden="true"`** hides the terminal from screen readers – letters arriving one by one, a command and its output would be noise. Screen readers read the last line instead: "Moved to peterstieg.com."
- That last line is visible without JavaScript. With JavaScript it steps back (see the CSS), but stays reachable: Tab focuses the link and makes the line visible.

## forward.css

### The font

```css
@font-face {
  font-family: "Atkinson Hyperlegible Mono";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("fonts/atkinson-hyperlegible-mono-latin-400-normal.woff2") format("woff2");
}
```

- Same typeface family as the site, in its monospaced cut: every character is equally wide, as in a terminal. A second rule loads the bold for the `>_`.
- Paths in a stylesheet are relative to the stylesheet, so `fonts/…` means `/forward/fonts/…` on every page.
- `font-display: swap` shows text in a fallback font until the file is there. `forward.js` waits for the font before typing (see below), so the swap does not happen mid-word.

### Tokens and frame

```css
:root {
  color-scheme: light dark;
  --paper: #F7F6F3;
```

- The four colours of the site, light and dark, without the `data-theme` variants – no switch on this page. `color-scheme: light dark` also gives scrollbars and form controls the matching shade.

```css
  display: grid;
  place-items: center;
```

- One grid cell, the terminal in its centre – horizontally and vertically.

```css
.term { width: min(100%, 52ch); }
```

- `ch` is the width of the "0" glyph; in a monospaced font, that is every character. 52 characters fit the longest line, the output. On a phone, `100%` wins and lines wrap.

### Lines, caret, cursor

```css
.line { display: flex; margin: 0; min-height: 1.6em; }
.caret { flex: none; margin-right: 1ch; color: var(--accent); font-weight: 700; }
.cmd { min-width: 0; }
```

- Flex puts `>_` and the command side by side. When a command wraps on a phone, the second line starts under the command, not under the `>_` – a hanging indent.
- `flex: none` keeps the caret from shrinking; `min-width: 0` lets the command shrink and wrap instead of pushing out of the screen.
- `min-height` keeps an empty prompt one line tall.

```css
.cursor {
  display: inline-block;
  width: 1ch; height: 1.1em;
  vertical-align: -0.2em;
  background: var(--accent);
}
```

- One character cell wide, as in a terminal, in the accent colour – the same block cursor as in the hero of peterstieg.com.
- It blinks only after a stop (`.cursor.blink`), four times, then stays: anything that blinks longer than five seconds needs a way to pause it (WCAG 2.2.2). The rule sits inside `prefers-reduced-motion: no-preference`.

### Hidden, then shown

```css
.js .line { visibility: hidden; }
.js .line.on { visibility: visible; }
```

- `visibility: hidden` keeps the space a line takes; `display: none` would remove it. Because all three lines reserve their space from the start, nothing moves when one appears – the terminal stays put in the middle.

```css
.js .go:not(.on):not(:focus-within) {
```

- The "Moved to" line is visually hidden – the same technique as `.sr-only` on the main site – unless it has the class `on` (after a stop) or contains the focus (Tab). Screen readers read it either way.

## forward.js

About 100 lines, plain JavaScript, wrapped in an IIFE like `site.js` (chapter 4 explains the pattern).

### Start

```js
  window.fw = true;                       // tells the failsafe in the page head that this file arrived
  const root = document.documentElement;
  root.classList.add("js");
```

- `window.fw` is the one deliberate global: the failsafe in the head reads it.
- The `js` class is set again, in case the failsafe removed it because the file came late. The scene then still plays.

### Where to

```js
  const path = location.pathname.replace(/^\/site(?=\/|$)/, "");
  const target = "https://peterstieg.com" + path + location.search + location.hash;
```

- `location.pathname` is the path of the current address, e.g. `/site/de/`.
- **The regular expression** removes a leading `/site`: `^` anchors at the start, `\/site` matches the text, `(?=\/|$)` is a lookahead – it requires a `/` or the end of the string to follow, without consuming it. So `/site/de/` becomes `/de/`, `/site` becomes empty, and `/sitemap.xml` stays untouched.
- `search` (`?…`) and `hash` (`#…`) are carried over, so even a link to a section arrives there.

```js
  const [first, output, second] = term.querySelectorAll(".line");
  go.querySelector("a").href = target;
```

- **Destructuring:** the three lines, in document order, get three names in one statement.
- The visible link now also carries the path, not only the start page.

```js
  if (path.length > 1 && path.length <= 32) second.querySelector(".cmd").textContent = "cd peterstieg.com" + path;
```

- A deep link shows its path in the `cd` line: `/de/` becomes `cd peterstieg.com/de/`. Longer paths keep the plain `cd peterstieg.com`, so the scene stays short.
- **`textContent`, never `innerHTML`:** the path comes from the address bar, so anyone can put anything in it. `textContent` treats it as text; `innerHTML` would run it as HTML (a cross-site scripting hole).

### State, timer, helpers

```js
  let state = "playing";                  // playing → leaving | stopped
  let timer = 0;
  const wait = (ms) => new Promise((done) => { timer = setTimeout(done, ms); });
```

- **A small state machine:** the page is playing, leaving or stopped, and every action checks the state first. That stops a click and the end of the scene from both starting a navigation.
- `wait` turns `setTimeout` into a promise, so the scene reads top to bottom with `await` instead of nested callbacks. It keeps the id of the latest timer, so a stop can cancel it.

```js
  const prompt = (line) => { line.querySelector(".cmd").append(cursor); show(line); };  // the cursor moves here
```

- There is only one cursor element. `append` moves an element that is already in the page – it is never copied.

```js
    location.replace(target);             // replace: the forward page does not stay in the back history
```

- `location.replace` swaps the current history entry. With `location.href = …` the forward page would stay in the history, and Back would land on it – and send the visitor straight forward again.

### Typing

```js
    for (const ch of text) {
      if (state !== "playing") return;
      cursor.before(ch);
      await wait(12 + Math.random() * 18);  // 12–30 ms per key: fast, but not mechanical
    }
```

- `for … of` over a string walks it character by character.
- `cursor.before(ch)` inserts the character as a text node in front of the cursor – the cursor moves right by itself.
- A random delay per key looks like typing; a fixed one looks like a machine.

### The scene

```js
      await Promise.race([document.fonts && document.fonts.ready, wait(600)]);
```

- `document.fonts.ready` resolves once the fonts are loaded. `Promise.race` takes whichever is first: the font, or 600 ms. On a slow connection the scene does not wait forever; it starts in the fallback font.

The timeline (measured, without a click):

| Time | Event |
|---|---|
| 0 | prompt `>_` with cursor |
| 0.2 s | typing starts, once the font is there |
| 1.1 s | `mv` typed |
| 1.3 s | "Enter": output and second prompt appear |
| 1.7 s | typing `cd` |
| 2.4 s | on to peterstieg.com |

- **Reduced motion:** no typing. The finished screen shows at once, then the page forwards after 1.2 s (measured: 1.24 s).
- **Skip:** a click or Enter forwards at once.

### Stop: `^C`

```js
    cursor.before("^C");
    term.querySelectorAll(".line:not(.on)").forEach((l) => l.remove());
    const fresh = first.cloneNode(false); // an empty <p class="line on" aria-hidden="true">
```

- **Ctrl+C** stops a running command in a terminal, and the terminal prints `^C` where the cursor was. Esc does the same here, for everyone who does not think in shortcuts.
- Lines that have not appeared yet are removed; a fresh, empty prompt follows, the cursor blinks, the "Moved to" line becomes visible. Enter still forwards.
- `cloneNode(false)` copies the element with its attributes, but without children – a ready-made empty line. Its content is a fixed string, so `innerHTML` is safe here.

```js
    const ctrlC = e.ctrlKey && !e.altKey && key.toLowerCase() === "c" && !String(getSelection());
```

- `!e.altKey`: on Windows, AltGr reports as Ctrl + Alt; without the check, AltGr + C would count.
- `!String(getSelection())`: when text is selected, Ctrl+C means copy and the scene keeps running.

## Try it

**1. A deep link.** Open `peterstieg.github.io/de/` (or `/site/de/`, an old address). The second line reads `cd peterstieg.com/de/`, and the German page opens.

**2. Stop and go.** Open `peterstieg.github.io`, press Esc while it types. Then press Enter.

**3. The fallbacks.** In DevTools, open the command menu (Ctrl + Shift + P, Cmd + Shift + P on a Mac):
- "Emulate CSS prefers-reduced-motion: reduce", then reload – no typing.
- "Disable JavaScript", then reload – the plain transcript, and after three seconds peterstieg.com. Re-enable JavaScript afterwards.

## Key terms

- **404 fallback** – GitHub Pages answers every path without a file with `404.html`. One page catches all addresses.
- **Meta refresh** – `<meta http-equiv="refresh" content="3; url=…">` loads another address after a delay, without JavaScript.
- **location.replace** – navigates without adding a history entry, so Back skips the page.
- **Promise · async/await** – a promise is a value that arrives later; `await` pauses an `async` function until it does, without blocking the page.
- **Promise.race** – settles with the first of several promises to settle.
- **ch** – a CSS unit: the width of the "0". In a monospaced font, the width of every character.
- **visibility vs. display** – `visibility: hidden` hides an element and keeps its space; `display: none` removes it from the layout.
- **Lookahead** – `(?=…)` in a regular expression checks what follows without making it part of the match.

[Previous: JavaScript](04-js.md) · [Back to the overview](README.md)
