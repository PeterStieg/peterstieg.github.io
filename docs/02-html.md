# The HTML: what the browser receives

Every HTML page in `site/` is generated: `src/build.py` writes them, together with `robots.txt`, `sitemap.xml` and `.htaccess`, from the texts and templates it contains. Never edit the HTML by hand – the next build overwrites it; change `src/build.py` and run `python3 src/build.py`. This chapter reads `site/index.html` from top to bottom, compares it with `site/de/index.html` where the two differ, and ends with the small files around it.

---

## Before the `<html>` element

```html
<!doctype html>
<!--
  Hallo · Hi · Ciao – view-source counts as root access, too.

  peterstieg.com
  ├── no tracking
  ├── no cookies
  └── no framework

  >_ sudo dream plan ship
-->
```

- `<!doctype html>` – switches the browser to standards mode. Without it, browsers fall back to quirks mode, which imitates the rendering bugs of late-1990s browsers (for example in how heights and table cells are calculated). This short form is all HTML needs; upper or lower case does not matter.
- `<!-- … -->` – a comment. The parser keeps it in the document (DevTools shows it above `<html>`), but nothing renders. It is an easter egg for anyone who opens view-source: the greeting repeats the contact section, "root access" picks up the claim, the tree imitates the Unix `tree` command, and the last line is the motto from the hero. `build.py` keeps the text in the constant `SOURCE_NOTE` and puts it on every page. `site.js` prints a similar message to the browser console.
- The comment sits before `<meta charset>`. That is fine as long as it stays short: browsers look for the charset declaration within the first 1024 bytes of the file. Here the declaration starts at byte 232.
- The comment keeps ordinary spaces around its middle dot. The function `dots()` in `build.py`, which makes middle dots non-breaking, only touches what comes after `<body>` (see "Non-breaking spaces and middle dots").

## `<html lang>`

```html
<html lang="en">
```

- `<html>` – the root element. Everything else is inside it.
- `lang="en"` – the language of the whole page. Every element inherits it unless it sets its own `lang`. Screen readers use it to choose voice and pronunciation rules; browsers use it for hyphenation, spell-checking and the "translate this page?" prompt. The German page has `lang="de"`.
- Search engines: Google states that it detects a page's language from the visible text and ignores `lang`. For search, the pairing of English and German versions comes from the `hreflang` links in the head.

---

## The head

The `<head>` holds information about the page, not content. Of all its lines, only the title (in the tab) and the icons become visible.

### Encoding and viewport

```html
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
```

- `<meta charset="utf-8">` – tells the browser how to turn bytes into characters. Without it, every character outside plain ASCII – `–`, `·`, `€`, the `à` in "Università" – can turn into garbage if the server does not name an encoding in its HTTP header. If the server does name one, the header wins.
- `<meta name="viewport">` – without it, phone browsers lay the page out for an imaginary desktop screen (typically 980 px wide) and shrink the result. `width=device-width` makes the layout width equal to the screen width in CSS pixels, so the media queries in `site.css` see the real width. `initial-scale=1` starts at 100 % zoom.
- No `maximum-scale=1`, no `user-scalable=no`. Both would stop visitors from pinch-zooming. People with low vision depend on zoom, and WCAG (the accessibility standard behind the EU accessibility rules) requires that text can be enlarged to 200 %. Some sites block zoom to avoid layout glitches; this one is built to survive zoom instead.

### The theme boot script

```html
<script>(function(){document.documentElement.classList.add('js');try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}})()</script>
```

The same code, indented for reading (`build.py` writes it on one line, from the constant `THEME_BOOT`):

```js
(function () {
  document.documentElement.classList.add('js');
  try {
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark')
      document.documentElement.setAttribute('data-theme', t);
  } catch (e) {}
})()
```

- `(function () { … })()` – an IIFE ("immediately invoked function expression"): a function that is defined and called in one go. The outer parentheses make the parser read `function` as an expression instead of a declaration; the final `()` calls it. Its purpose is scope: variables declared inside, such as `t`, exist only within the function. A plain `var t` at the top level of a script would land on the global object as `window.t`, where any other script could overwrite or read it.
- `document.documentElement` – the `<html>` element.
- `.classList.add('js')` – turns it into `<html lang="en" class="js">`. CSS uses the class to tell "JavaScript runs" from "JavaScript is off": `html:not(.js) .themes` hides the theme buttons (without JavaScript they would do nothing), `html:not(.js) .to-top` shows the back-to-top button permanently.
- `localStorage.getItem('theme')` – reads the theme a visitor picked on an earlier visit. `site.js` stores it when someone clicks a theme button.
- `if (t === 'light' || t === 'dark')` – accepts only the two known values. Anything else (empty, outdated, edited by hand) is ignored, and the page follows the system setting.
- `setAttribute('data-theme', t)` – writes `data-theme="dark"` or `data-theme="light"` on `<html>`. The CSS has rules for `:root[data-theme="dark"]` and `:root:not([data-theme="light"])`, so this one attribute switches every color variable at once.
- `try { … } catch (e) {}` – reading `localStorage` throws an error when the browser blocks storage, which some privacy settings do. The empty `catch` swallows the error; the page then simply follows the system theme.
- `var t` – a local variable, thanks to the IIFE. `site.js` uses the same pattern: its whole code sits inside one arrow function that runs immediately.

Why inline, and why exactly here:

- **Before the first paint.** The browser paints nothing until the stylesheet in the head has arrived. A script in the head runs within that window, so the very first frame already has the right `data-theme`. If the same code lived in `site.js` (loaded with `defer`, after parsing), a visitor who chose dark on a light system would see a light page flash before it turns dark.
- **Inline, not a file.** An external script costs a network request, and a plain `<script src>` stops the parser until it has downloaded. Four short statements are cheaper inline.
- **Before the stylesheet `<link>`.** A script that comes after a stylesheet has to wait until that stylesheet has downloaded, because scripts are allowed to ask for computed styles. Placed before the `<link>`, the script runs immediately.

### Title, description, author

```html
<title>Peter Stieg – Performance Marketing · Data Science</title>
<meta name="description" content="Marketinkerer from Leipzig: performance marketing, lead generation and data science. Leadership roles at four companies, self-built tools.">
<meta name="author" content="Peter Stieg">
```

- `<title>` – the text in the browser tab, in bookmarks and history, and usually the headline of the search result (Google may rewrite it). Both languages use the same title, because the tagline is a brand element that stays English.
- `<meta name="description">` – the snippet search engines may show under the headline. It is not a ranking factor; its job is to earn the click. At 138 characters it is short enough to avoid truncation. The German page has its own German text.
- `<meta name="author">` – the author's name. Search engines do not use it for ranking; it is metadata for tools that look for an author.

### Canonical URL and language alternates

```html
<link rel="canonical" href="https://peterstieg.com/">
<link rel="alternate" hreflang="en" href="https://peterstieg.com/">
<link rel="alternate" hreflang="de" href="https://peterstieg.com/de/">
<link rel="alternate" hreflang="x-default" href="https://peterstieg.com/">
<meta property="og:locale:alternate" content="de_DE">
```

- `rel="canonical"` – names the one official URL of this page. The same file is reachable as `https://peterstieg.com/`, `…/index.html`, `…/?utm_source=linkedin` and more; the canonical tells search engines to treat them as one page and to collect all signals on `https://peterstieg.com/`. The German page points to `https://peterstieg.com/de/`.
- `rel="alternate" hreflang="en"` and `"de"` – "the same content exists in this language, at this URL". A German searcher then gets `/de/`, an English one `/`. The rules: absolute URLs, each page lists every version including itself, and the pairing must be confirmed from both sides – the German page carries the identical three lines. If page A names B as its alternate but B does not name A, Google ignores the pair.
- `hreflang="x-default"` – the fallback for everyone else: a visitor searching in Italian or French gets the English page.
- `og:locale:alternate` – the Open Graph counterpart for social networks: "this page also exists as `de_DE`". `build.py` emits one tag per other language, so the German page says `en_GB`. Facebook's crawler is the main reader of this tag.

### Theme color

```html
<meta name="theme-color" content="#F7F6F3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#181A1C" media="(prefers-color-scheme: dark)">
```

- `theme-color` – browsers that tint their own interface (address bar, status bar) with the page's color read this. Chrome on Android does; Safari has done so in several versions.
- Two tags with `media` – the browser uses the tag whose media query matches the system setting: the paper white in light mode, the dark background in dark mode. The values equal `--paper` in `site.css`, so the browser frame and the page blend.
- A media query only knows the system setting, not the theme buttons. That is why `site.js` overwrites the `content` of both tags with the chosen color as soon as a visitor picks a theme.

### Link preview: Open Graph, profile, Twitter

```html
<meta property="og:type" content="profile">
<meta property="og:title" content="Peter Stieg – Performance Marketing · Data Science">
<meta property="og:description" content="Marketinkerer from Leipzig: …">
<meta property="og:url" content="https://peterstieg.com/">
<meta property="og:image" content="https://peterstieg.com/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Peter Stieg – Performance Marketing · Data Science – Marketing leadership with root access">
<meta property="og:locale" content="en_GB">
<meta property="profile:first_name" content="Peter">
<meta property="profile:last_name" content="Stieg">
<meta name="twitter:card" content="summary_large_image">
```

When someone pastes the URL into LinkedIn, Slack, WhatsApp or X, a crawler from that platform downloads the HTML, reads these tags and builds the preview card. It runs no JavaScript; what is not in these tags is guessed from the page, often badly.

- `property` vs `name` – Open Graph (a Facebook protocol, now read by almost every platform) is specified with the attribute `property`; ordinary HTML meta tags and the Twitter tags use `name`. Many crawlers accept either, but the specified form is the safe one.
- `og:type` = `profile` – the page is about a person, not an article or a generic website. This type unlocks the `profile:` properties below.
- `og:title`, `og:description` – headline and text of the card. Identical to `<title>` and the meta description, so the search result and the LinkedIn card say the same thing.
- `og:url` – the URL the card belongs to. Shares of `…/index.html` or `…/?utm_source=x` collapse into one card.
- `og:image` – the card's picture. It must be an absolute URL: the crawler only sees this tag, and a relative path has nothing reliable to resolve against.
- `og:image:width`, `og:image:height` – 1200 × 630 px, the 1.91 : 1 format that LinkedIn and Facebook show at full card width. Declaring the size lets a crawler lay out the card before it has downloaded the image, which helps on the very first share.
- `og:image:alt` – a text description of the image, for screen-reader users on platforms that pass it on. Not all do.
- `og:locale` = `en_GB` – language and region of this page, written with an underscore (`de_DE` on the German page). A different notation from `lang` (`en`, `de`).
- `profile:first_name`, `profile:last_name` – the two fields of the `profile` type. Few platforms show them; they make the page unambiguously one person's profile.
- `twitter:card` = `summary_large_image` – X (Twitter) has its own tags but falls back to the `og:` equivalents for title, description and image. One tag is therefore enough: it asks for the large-image card instead of the small square thumbnail.

LinkedIn's preview is built from `og:title`, `og:description`, `og:image` and `og:url`. If you change any of them, LinkedIn keeps showing the old card for up to about a week unless you refresh it (see "Try it").

### Icons

```html
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
```

- `rel="icon"` with an SVG file – a vector favicon stays sharp at every size and can switch colors in dark mode (see `favicon.svg` at the end of this chapter). `type="image/svg+xml"` lets a browser that cannot use SVG icons skip the file.
- `rel="apple-touch-icon"` – the icon iOS shows when someone adds the page to the home screen. iOS does not take SVG here, so it is a 180 × 180 px PNG.
- Relative paths – `favicon.svg` resolves against the page's own address. The German page, one folder deeper, writes `../favicon.svg`. `build.py` handles this with the value `root` per language (`""` or `"../"`). Relative paths make the site work anywhere: on the domain, in a subfolder, or opened straight from disk. The 404 page is the exception, for reasons explained there.

### Font preload and stylesheet

```html
<link rel="preload" href="assets/fonts/atkinson-hyperlegible-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/site.css">
```

Without a hint, a web font is discovered late: the browser downloads the HTML, then the CSS, reads the `@font-face` rules, lays out the page, notices that text needs "Atkinson Hyperlegible" – and only then requests the font file. Until it arrives, the text appears in a fallback font (`font-display: swap` in the CSS) and visibly jumps when the real font replaces it.

- `rel="preload"` – "download this now, it will be needed". The request starts while the head is still being parsed, in parallel with the CSS.
- `as="font"` – the kind of resource. It sets priority and request headers, and it lets the browser match the preloaded file to the later request from `@font-face`. Without `as`, the browser cannot make that match and downloads the font again.
- `type="font/woff2"` – a browser that cannot read WOFF2 skips the preload instead of wasting bandwidth.
- `crossorigin` – the non-obvious one. Fonts are always requested in CORS mode, even from your own server; the CSS Fonts specification demands it. A preload without `crossorigin` is made in "no-cors" mode. The two requests differ in mode, the browser treats them as different resources, and the font is downloaded twice – Chrome then warns in the console that a preloaded resource was not used. The bare attribute means `crossorigin="anonymous"`: CORS mode without cookies, exactly what `@font-face` does.
- Only two of the three font files are preloaded: bold (name, headings, ledger figures) and regular (body text). The italic appears only in a few words of the dictionary entry and loads on demand. Every preload competes with the stylesheet for bandwidth, so preloads are limited to what the first screen needs.
- `rel="stylesheet"` – the CSS, one file of about 16 KB, no third-party styles. It is render-blocking: the browser paints nothing until it has arrived, which prevents a flash of unstyled content.

### Structured data: JSON-LD

```html
<script type="application/ld+json">{"@context": "https://schema.org", "@type": "Person", "name": "Peter Stieg", … }</script>
</head>
```

The content of the block, indented for reading (in the file it is one line):

```json
{
  "@context": "https://schema.org",
  "@type": "Person",
  "name": "Peter Stieg",
  "url": "https://peterstieg.com/",
  "image": "https://peterstieg.com/og-image.png",
  "jobTitle": "Head of Marketing",
  "description": "Marketinkerer from Leipzig: performance marketing, lead generation and data science. Leadership roles at four companies, self-built tools.",
  "address": {"@type": "PostalAddress", "addressLocality": "Leipzig", "addressCountry": "DE"},
  "email": "mailto:info@peterstieg.com",
  "sameAs": ["https://www.linkedin.com/in/peterstieg/", "https://github.com/PeterStieg"],
  "knowsLanguage": ["de", "en", "it", "es", "fr"],
  "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Università degli Studi di Trento"}],
  "hasCredential": [
    {"@type": "EducationalOccupationalCredential", "name": "Data Scientist",
     "url": "https://document-factory.datascientest.com/verify/3225d69a-a3b6-4bd2-bafe-df9381eff729",
     "recognizedBy": {"@type": "Organization", "name": "Université Paris 1 Panthéon-Sorbonne"}},
    {"@type": "EducationalOccupationalCredential", "name": "MLOps Engineer",
     "url": "https://document-factory.datascientest.com/verify/46b46e0c-cd3b-458a-8e9f-4ee08feb9164",
     "recognizedBy": {"@type": "Organization", "name": "Université Paris 1 Panthéon-Sorbonne"}}
  ]
}
```

- `<script type="application/ld+json">` – a data block, not a program. Browsers do not execute scripts with a type they do not know; they keep the text and move on. Search engines and other crawlers parse it as JSON-LD ("JSON for Linked Data"): ordinary JSON whose keys come from a shared vocabulary. Because nothing executes, its position at the end of the head blocks nothing.
- `"@context": "https://schema.org"` – the vocabulary. Every key that follows is a schema.org term: `name` means schema.org/name.
- `"@type": "Person"` – the thing described is a person, not the website and not a company.
- `name`, `url`, `image` – who, where his home on the web is, which image represents him. The image is the Open Graph banner, not a portrait.
- `jobTitle` – "Head of Marketing"; the German page says "Leiter Marketing".
- `description` – the meta description again.
- `address` – a nested `PostalAddress` with only city and country (`DE`, the ISO country code). The full postal address stays on the legal notice, which is kept out of search results.
- `email` – written as a `mailto:` URL.
- `knowsLanguage` – language codes in the same notation as `lang`.
- `alumniOf` – the university, typed as `CollegeOrUniversity`.
- `sameAs` – URLs of other pages about the same person: LinkedIn and GitHub. This is how a search engine joins "Peter Stieg on peterstieg.com", "Peter Stieg on LinkedIn" and "PeterStieg on GitHub" into one entity instead of guessing from matching names. Together with `rel="me"` on the contact links, it is the clearest identity signal a small site can give.
- `hasCredential` – the two certificates, each an `EducationalOccupationalCredential` with a `name`, a `url` pointing to the issuer's verification page, and `recognizedBy` naming the university. It turns "Certified Data Scientist" from a sentence into a machine-readable claim with a link anyone can check – the same principle as the footnotes in the Education section.
- What it buys: Google offers no special search result for a standalone Person, so nothing visibly changes in the results. The value is disambiguation – which profiles, which job, which credentials belong together – for search engines and any other system that reads schema.org.
- `build.py` produces the block with `json.dumps(…, ensure_ascii=False)`, so "Università" stays readable instead of becoming `Università`. One trap if you ever add text here: the character sequence `</script>` inside a value would end the block early, because the HTML parser knows nothing about JSON.
- `</head>` – end of the metadata.

---

## The body

### Skip link

```html
<body>
<a class="skip" href="#main">Skip to content</a>
```

- `<body>` – everything visible.
- `<a class="skip" href="#main">` – the first focusable element on the page. A keyboard user presses Tab once, sees "Skip to content", presses Enter and lands at `<main id="main">`, past the header with its up to eight links and buttons. Without it, keyboard and screen-reader users would tab through the whole navigation on every visit.
- The CSS parks the link above the visible area (`top: -3rem`) and moves it into view on `:focus`. It is deliberately not hidden with `display: none`, which would also make it unreachable by keyboard.
- Following an in-page link also moves the keyboard's starting point: the next Tab goes to the first link inside `<main>`.

### Header and logo

```html
<header class="top">
<div class="wrap">
<a class="home" href="#top"><span class="caret" aria-hidden="true">&gt;_</span><span class="name">Peter Stieg</span></a>
```

- `<header>` – directly inside `<body>`, it becomes the page's banner landmark. Screen readers keep a list of landmarks (banner, navigation, main, regions, contentinfo) and let the user jump between them, the way a sighted reader scans a layout.
- `class="top"` – the hook for CSS: sticky position, translucent background, a hairline that appears once the page scrolls.
- `<div class="wrap">` – no meaning, only layout: maximum width and side padding. The same wrapper sits in `<main>` and `<footer>`, so all three align.
- `<a class="home" href="#top">` – the logo links to the hero section (`id="top"`), not to `index.html`. On a one-page site, "home" means "back to the beginning" and needs no reload. A side note: `#top` would scroll to the top even without an element of that id, because the HTML specification treats the fragment `top` specially. Here the id exists, so the browser scrolls to the hero.
- `<span class="caret" aria-hidden="true">&gt;_</span>` – the terminal prompt `>_`. `&gt;` is the escaped `>`; `build.py` escapes it with Python's `html.escape`, and the browser shows `>`. `aria-hidden="true"` removes the span from the accessibility tree, so a screen reader does not say "greater than underscore" before the name.
- `<span class="name">Peter Stieg</span>` – the name. The capitals on screen come from CSS (`text-transform: uppercase`); the source keeps normal case. The link's accessible name is "Peter Stieg".
- No whitespace between the two spans: inside an inline element like `<a>`, a space or line break would render as a visible space. The gap comes from a CSS margin on `.caret` instead.
- Docking: `site.js` moves the large hero name into this logo while you scroll. Until the name has arrived, the logo has `visibility: hidden`, which also takes it out of the tab order and the accessibility tree. That is intended: at that point the hero name is visible.

### Navigation

`build.py` assembles the whole `<nav>` from f-string pieces, so it lands on one line without whitespace between the tags. As a flex container, the nav would ignore such whitespace anyway; the spacing comes from CSS `gap`. The three parts, quoted one by one:

```html
<nav class="nav" aria-label="Main"><a class="sect" href="#profile"><span class="no" aria-hidden="true">01</span> <span class="label" data-label="Profile">Profile</span></a><a class="sect" href="#experience"><span class="no" aria-hidden="true">02</span> <span class="label" data-label="Experience">Experience</span></a>…
```

- `<nav>` – a navigation landmark.
- `aria-label="Main"` – its name. Screen readers announce "Main navigation", which distinguishes it from the second `<nav>` in the footer. On the German page the label is "Hauptnavigation".
- `<a class="sect" href="#profile">` – four links to section ids. The fragment `#profile` scrolls to the element with `id="profile"`; `scroll-padding-top` in the CSS stops the target from sliding under the sticky header. The four links are the four chapters; the other sections belong to one of them and are a scroll away.
- `<span class="no" aria-hidden="true">01</span>` – the chapter number, the same as on the heading: 01 Profile, 02 Experience, 03 Projects, 04 Contact. `aria-hidden` keeps the link's name "Profile" for screen readers. Below 56rem the CSS hides the numbers, so the header still fits.
- `<span class="label" data-label="Profile">` – the label in its own span, plus a copy as a data attribute. HTML ignores `data-*` attributes; they exist for CSS and scripts. Here the CSS prints a hidden bold copy of the label to keep the link's width constant when it turns bold.
- **You are here:** while scrolling, `site.js` gives the link of the chapter being read `aria-current="location"` – "the current location within this set of links". The CSS then styles the link like the heading it points to: number in the accent colour, label in ink and bold. In P⁴ the menu marks Profile, in Education Experience, and so on – like a slide deck whose header shows the current part on every slide.
- On narrow screens the CSS hides the `.sect` links with `display: none`, which hides them from screen readers as well.
- The German page uses German ids (`#profil`, `#stationen`, `#projekte`, `#kontakt`), so shared links read naturally in each language. They come from the `ids` map in `build.py`.

```html
<span class="langs" role="group" aria-label="Language"><span aria-current="page" title="English">EN</span><a href="de/index.html" hreflang="de" lang="de" title="Deutsch">DE</a></span>
```

- `<span class="langs" role="group" aria-label="Language">` – a span carries no meaning; `role="group"` turns it into a named group, so a screen reader announces "Language, group" on entering. Visually it is the pill around EN and DE.
- `<span aria-current="page" title="English">EN</span>` – the current language is not a link; a link to the page you are on is a dead end.
  - `aria-current="page"` – screen readers that support it announce "current page". The CSS uses the same attribute (`.langs [aria-current]`) to set the label bold: one attribute drives both meaning and style.
  - `title="English"` – the tooltip on hover.
- `<a href="de/index.html" hreflang="de" lang="de" title="Deutsch">DE</a>`:
  - `href="de/index.html"` – relative, so it also works from disk. On the server, `/de/index.html` and `/de/` are the same file; the canonical tag of the German page settles which URL counts.
  - `hreflang="de"` – "the target is in German". On an `<a>` this is only an advisory hint; search engines use `hreflang` from the `<link>` tags in the head, not from ordinary links.
  - `lang="de"` – the link text itself is German, so a screen reader pronounces it with German rules. The convention for language switches: each language is named in that language.
  - `title="Deutsch"` – tooltip, again in its own language.
- On the German page the roles swap: `EN` is the link (`../index.html`, `hreflang="en" lang="en"`), `DE` is the `aria-current` span.

```html
<span class="themes" role="group" aria-label="Theme"><button type="button" data-theme-set="light" aria-pressed="false" aria-label="Light" title="Light"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="3"/><path d="M8 1v1.6M8 13.4V15M1 8h1.6M13.4 8H15…"/></svg></button><button type="button" data-theme-set="dark" aria-pressed="false" aria-label="Dark" title="Dark"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M13.6 10.2A6 6 0 0 1 5.8 2.4a6 6 0 1 0 7.8 7.8z"/></svg></button></span></nav>
</div>
</header>
```

- `<span class="themes" role="group" aria-label="Theme">` – the same group pattern as the languages. German: "Darstellung".
- `<button type="button">` – a real button, not a clickable `<div>`: focusable, reacts to Enter and Space, announced as a button – all built in. `type="button"` states that it submits nothing; the default type is `submit`, which would matter inside a form.
- `data-theme-set="light"` – a custom data attribute. Any attribute that starts with `data-` is valid HTML and reserved for the page's own scripts. `site.js` reads it as `button.dataset.themeSet` and copies the value to `<html data-theme>`.
- `aria-pressed="false"` – makes the button a toggle button. A screen reader says "Light, toggle button, not pressed". `site.js` sets `"true"` on the button that matches the active theme – chosen or inherited from the system – and updates both on every click. The CSS styles `[aria-pressed="true"]`, so again one attribute drives both the announcement and the look. Both start as `"false"` in the HTML because the build cannot know the visitor's theme.
- `aria-label="Light"` – the accessible name. The button contains only an icon; without a label it would be announced as "button" and nothing else. German: "Hell", "Dunkel".
- `title="Light"` – the tooltip for mouse users. It does not replace `aria-label`: tooltips need a hover, which touch and keyboard users do not have, and screen readers handle `title` inconsistently.
- `<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">` – an icon drawn inline:
  - `viewBox="0 0 16 16"` – the drawing's own coordinate system, 16 × 16 units. CSS sets the real size (`1rem`), and the drawing scales to fit.
  - `aria-hidden="true"` – the icon is decoration; the name comes from the button's `aria-label`.
  - `focusable="false"` – Internet Explorer and the old Edge made inline SVGs tab stops. Modern browsers do not need it; it costs nothing.
  - Sun: `<circle cx="8" cy="8" r="3"/>` is the disc in the center (center at 8/8, radius 3). The `<path>` draws eight short rays, each an `M` (move to) followed by a short line: `v` vertical, `h` horizontal, `l` a relative line in any direction.
  - Moon: one closed path of two arcs with radius 6 (`A` absolute, `a` relative) that meet at two points – one bulges out, the other cuts in, which leaves a crescent. `z` closes the shape.
  - No colors in the SVG: CSS sets `fill: none; stroke: currentColor`, so the icons take the text color and follow the theme automatically.
- Without JavaScript the whole group is hidden (`html:not(.js) .themes`): a button that cannot work should not be offered.
- Strictly, `<nav>` is meant for navigation links; the theme buttons sit inside it because they share the header row. Screen readers cope with this without problems.

### Back to top

```html
<a class="to-top" href="#top" aria-label="Back to top" title="Back to top"><svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 13.5V2.8M3.4 7.2 8 2.6l4.6 4.6"/></svg></a>
```

- A plain link to `#top`, so it works without JavaScript. Smooth scrolling comes from CSS (`scroll-behavior: smooth`, only when the visitor has not asked the operating system to reduce motion).
- `aria-label` – an icon-only link needs a name, same reasoning as the theme buttons. German: "Nach oben".
- The path: `M8 13.5V2.8` draws the shaft from bottom to top; `M3.4 7.2 8 2.6l4.6 4.6` draws the arrowhead. How the coordinates after `M` work is explained with the arrow in the Profile section.
- CSS fixes the button to the bottom-right corner and fades it in only once the name has docked into the header. Without JavaScript it is always visible.
- It sits between `</header>` and `<main>`, outside any landmark. In the tab order it therefore comes right after the header, although it appears at the bottom of the screen. While it is invisible (`visibility: hidden`), Tab skips it.

### Minimap

```html
<div class="minimap" aria-hidden="true"></div>
```

- An empty container. `site.js` fills it with one thin bar per rendered line of text in `<main>` – like the code overview in an editor – and lets you click or drag on it to scroll. CSS shows it only on wide and tall enough screens (at least 74rem × 30rem).
- `aria-hidden="true"` – it is a picture of the page, not content. Without the attribute, a screen reader could run into dozens of empty spans. It contains nothing focusable, which is the condition for using `aria-hidden` safely: a hidden element that can still receive focus leaves keyboard users on an invisible, nameless stop.
- A `<div>`, because HTML has no element for "decorative scroll widget".

### `<main>`

```html
<main id="main">
<div class="wrap">
```

- `<main>` – the main landmark: the content that is unique to this page. One per page.
- `id="main"` – the target of the skip link.

### Hero

```html
<section class="hero" id="top">
<h1>Peter Stieg</h1>
<p class="tagline" lang="en">Performance&nbsp;Marketing&nbsp;· Data&nbsp;Science</p>
<p class="claim" lang="en">Marketing leadership with root access</p>
<p class="prompt" lang="en"><span class="caret" aria-hidden="true">&gt;_</span><span class="cmd" aria-hidden="true">sudo dream plan ship</span><span class="sr-only">sudo dream plan ship</span><span class="cursor" aria-hidden="true"></span></p>
</section>
```

- `<section>` without a name – a section becomes a region landmark only when it has an accessible name (`aria-label` or `aria-labelledby`). The hero has none on purpose: it opens `<main>`, which is already a landmark, and its `<h1>` is the first thing a screen reader meets there. A name would only make the screen reader say "Peter Stieg" twice – once for the region, once for the heading.
- `id="top"` – the target of the logo and the back-to-top link.
- `<h1>` – the one top-level heading. Search engines read it as the page's main topic; screen-reader users reach it with a single key (H or 1 in most screen readers). Once the name has docked into the header, the CSS fades this `<h1>` out with `opacity: 0` (plus `pointer-events: none`, so it cannot be clicked or selected while invisible). Unlike `visibility: hidden` or `display: none`, opacity leaves the element in the accessibility tree: heading navigation still finds the `<h1>` while the page is scrolled down.
- `<p class="tagline" lang="en">` – three `&nbsp;` keep "Performance Marketing" and "Data Science" together and glue the middle dot to "Marketing". On a narrow phone the line can only break after the dot. `build.py` inserts the first two in the hero template; `dots()` adds the one before the dot. `lang="en"` marks the tagline as an English brand element, which matters on the German page.
- `<p class="claim" lang="en">` – the claim. `lang="en"` is redundant on the English page and essential on the German one (see "English inside the German page").
- `<p class="prompt" lang="en">` – the typing line, built from four spans:
  - `.caret` – `>_`, decorative, hidden from screen readers.
  - `.cmd` with `aria-hidden="true"` – the visible text. `site.js` empties it and types it again, letter by letter. It is hidden from screen readers so they never catch a half-typed "sudo dre".
  - `.sr-only` – the same text for screen readers only. The class does not use `display: none` (that would hide it from screen readers too); it shrinks the box to 1 × 1 px and clips it. Invisible on screen, present in the accessibility tree. Side effect: selecting and copying the whole line usually copies the motto twice.
  - `.cursor` – an empty span that CSS draws as a blinking block.
- Without JavaScript nothing is typed: `.cmd` simply shows the full text. When the visitor has turned on "reduce motion" in the operating system, `site.js` skips the typing too.

### The section pattern

```html
<section class="sec" id="profile" aria-labelledby="h-profile">
<h2 id="h-profile"><span class="no" aria-hidden="true">01</span> Profile</h2>
<div class="body">
…
</div>
</section>
```

Every content section comes from this template (function `section()` in `build.py`):

- `<section>` – a thematic group with its own heading.
- `id="profile"` – the target for `#profile` links.
- `aria-labelledby="h-profile"` – names the region after its heading, so the screen reader's landmark list reads "Profile, Experience, Projects …". It points to the heading's id instead of repeating the text in `aria-label`: the name always matches the visible heading, and it is translated along with it (some browser translation tools leave `aria-label` untranslated).
- `<span class="no" aria-hidden="true">01</span>` – the chapter number, like the parts of a slide deck. The page has four chapters: 01 Profile, 02 Experience, 03 Projects, 04 Contact. `aria-hidden` keeps the number out of what screen readers announce, so the region is still named "Profile", not "01 Profile".
- The sections inside a chapter repeat its number with a second class, `<span class="no ghost" aria-hidden="true">01</span>` on P⁴. The CSS makes it invisible; it only keeps the space, so the title lines up with the chapter's title.
- `<h2 id="h-profile">` – the heading, with the id the section points to. Heading levels form an outline: `h1` (name) → `h2` (sections) → `h3` (roles, fields, project groups) → `h4` (single projects). Screen-reader users move through this outline the way sighted users skim bold text.
- `<div class="body">` – the content column next to the sticky heading (CSS grid). No meaning.
- The eight sections make eight region landmarks. That makes the landmark list longer; in exchange, every section is one keystroke away.

### Profile: a dictionary entry

```html
<div class="entry">
<p class="hw"><dfn>mar<span class="syl">·</span>ke<span class="syl">·</span>tin<span class="syl">·</span>ker<span class="syl">·</span>er</dfn> <span class="pos">noun</span> <span class="ety">[<i>marketer</i> × <i>tinkerer</i>]</span></p>
<p class="def">A marketing leader who builds the tools behind the campaigns.</p>
</div>
```

The section opens with the word "marketinkerer", set like an entry in a dictionary.

- `<div class="entry">` – groups the entry for spacing.
- `<p class="hw">` – the headword line (hw = headword, dictionary jargon).
- `<dfn>` – "this is the defining instance of the term". HTML has an element for exactly this; it tells machines that the surrounding text defines "marketinkerer". Browsers set `<dfn>` in italics by default; the CSS resets it to upright bold. Strictly, the HTML specification wants the definition inside the same paragraph as the `<dfn>`; here it follows in the next `<p>`. No browser or validator objects.
- `<span class="syl">·</span>` – syllable separators in a muted color. English dictionaries such as Merriam-Webster separate syllables with middle dots; the German page uses vertical bars as Duden does: `Mar|ke|tin|ke|rer`. Each language follows its own dictionary convention. The trade-off: a screen reader may read the word as five fragments, depending on its punctuation settings.
- `<span class="pos">noun</span>` – part of speech. German: `der; -s, -` (article, genitive, plural – Duden notation).
- `<span class="ety">[<i>marketer</i> × <i>tinkerer</i>]</span>` – the etymology. `<i>` marks text in an "alternate voice" – here words mentioned as words, which dictionaries set in italics. `×` is the multiplication sign, not the letter x. On the German page the two words carry `lang="en"`: `<i lang="en">marketer</i>`.
- `<p class="def">` – the definition.

### Profile: text and results ledger

```html
<p>Leadership roles at four companies, … Université Paris 1 Panthéon-Sorbonne.</p>
<dl class="ledger" aria-label="Selected results">
<div><dt>€6k <span class="arr" role="img" aria-label="to"><svg viewBox="0 0 16 10" aria-hidden="true" focusable="false"><path d="M1 5h13.5M10 1.2 14 5l-4 3.8"/></svg></span> €240k</dt><dd>monthly media budget at a RoAS of 4.0&nbsp;· Posterlounge</dd></div>
<div><dt>17 shops</dt><dd>in 12 languages across the European Economic Area&nbsp;· Posterlounge</dd></div>
<div><dt>RoAS 7.6 <span class="arr" role="img" aria-label="to">…</span> 7.8</dt><dd>on a €1.7m media budget, while spend grew&nbsp;· Brandible</dd></div>
<div><dt>&gt; 2×</dt><dd>inbound inquiries year over year&nbsp;· E+SERVICE+CHECK</dd></div>
</dl>
```

- `<p>` – a plain paragraph.
- `<dl>` – a description list: pairs of a term (`<dt>`) and its description (`<dd>`). The classic use is a glossary, but any name–value pairing qualifies – here figure → context. A table would claim rows and columns that are not there; a `<ul>` would lose the pairing.
- `aria-label="Selected results"` – a name for the list. Screen readers differ in whether they announce a name on a `<dl>`, so it is a bonus; the section heading carries the context anyway.
- `<div>` around each `<dt>`/`<dd>` pair – allowed inside `<dl>`, but only `<div>` and only around complete groups. It gives CSS one box per row for the grid and the dividing lines.
- `<dt>€6k … €240k</dt>` – the figure. `<dd>` – what it means and where.
- `&gt; 2×` – the escaped `>`, then the multiplication sign: "more than twice".
- `&nbsp;·` – the middle dot glued to the word before it (see "Non-breaking spaces and middle dots").

The drawn arrow:

- `<span class="arr" role="img" aria-label="to">` – the arrow → is not part of the Atkinson Hyperlegible font. A text arrow would come from a fallback font and look foreign, so `build.py` (function `t()`) replaces every → in the copy with this drawn version.
- `role="img"` – turns the span into a single image as far as assistive technology is concerned; its inner content is no longer read.
- `aria-label="to"` – the image's text alternative. A screen reader reads "€6k, to, €240k", often adding "image" or "graphic". A text arrow would be read as "right arrow", which makes no sentence. The German page uses `aria-label="auf"`: "6.000 auf 240.000 €".
- `<svg … aria-hidden="true">` inside – hidden so the arrow is not announced twice.
- The path `M1 5h13.5M10 1.2 14 5l-4 3.8`, in a 16 × 10 `viewBox`, command by command:
  - `M1 5` – move the pen to x 1, y 5 (the vertical middle) without drawing.
  - `h13.5` – a horizontal line 13.5 units to the right: the shaft.
  - `M10 1.2` – lift the pen, move to the upper end of the arrowhead.
  - `14 5` – coordinates without a command letter after `M` count as "line to": a line down to the tip at 14/5.
  - `l-4 3.8` – lowercase means relative: 4 units left, 3.8 down – the lower half of the head.
  - The stroke color is `currentColor` (set in CSS), so the arrow always matches the surrounding text.

### P⁴

```html
<section class="sec" id="fields" aria-labelledby="h-fields">
<h2 id="h-fields"><span class="no ghost" aria-hidden="true">01</span> P<sup>4</sup></h2>
<div class="body">
<p class="intro">P as in Peter.</p>
<div class="fields">
<div><h3>Performance</h3><p>Google Ads, Microsoft Advertising, Meta, LinkedIn, SEO and marketplaces. Steered by cost per inquiry, quote and order.</p></div>
…
<div><h3>People</h3><p>Teams of up to six, … Processes fit people, not the other way round. <strong lang="en">Everything human:e.</strong></p></div>
</div>
</div>
</section>
```

- `id="fields"` – not linked from the navigation, but addressable. German: `p-wie-peter`.
- `P<sup>4</sup>` – "P to the power of four" for the four Ps. `<sup>` is meant for typographic conventions that need superscript (exponents, footnote marks), so this is correct use. Screen readers usually ignore the superscript and say "P4"; that is also the section's name in the landmark list.
- `<p class="intro">` – a one-line lead-in.
- `<div class="fields">` – a 2 × 2 grid on wider screens. Four `<div>`s, each with an `<h3>` and a `<p>`. Not a list: each block stands on its own with a heading, and headings are more useful for navigation than list items.
- `<strong lang="en">Everything human:e.</strong>` – `<strong>` means strong importance (`<b>` would be visual only). The colon in "human:e" belongs to the slogan; it is not a typo.
- On the German page the four `<h3>` carry `lang="en"`, because the four Ps stay English.

### Experience: a reversed timeline

```html
<ol class="roles" reversed>
<li class="role">
<p class="when">since 11/2025</p>
<div>
<h3>Head of Marketing</h3>
<p class="org">E+SERVICE+CHECK GmbH&nbsp;<span class="place">· Laucha</span></p>
<p class="ctx">TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.</p><ul class="tree"><li><span class="k">Scope</span> marketing, design and automation, built from scratch – SEA, SEO, CRM, events, employer branding</li><li><span class="k">Result</span> inbound inquiries more than doubled year over year; new corporate identity incl. groundwork for an EUIPO trademark</li></ul>
</div>
</li>
…
</ol>
```

Nine entries; the first stands for all.

- `<ol>` – an ordered list, because the order carries meaning: it is a timeline. A `<ul>` would say "these items could come in any order".
- `reversed` – the numbering counts down: the newest entry is number 9, the oldest number 1. The list runs newest-first like a CV, so this is the honest numbering. The CSS hides the numbers (`list-style: none`); you see them only if the stylesheet fails to load.
- A known quirk: Safari has, in many versions, stopped announcing lists as lists in VoiceOver once CSS sets `list-style: none`. The usual fix is `role="list"` on the list. It applies to all unstyled lists on this page.
- `<li class="role">` – one position.
- `<p class="when">` – the period, in the left column on wide screens.
- `<div>` – groups everything else into the right column, so the CSS grid gets exactly two columns: date | details.
- `<h3>` – the job title. As a heading, every role is reachable through heading navigation.
- `<p class="org">` with `<span class="place">· Laucha</span>` – employer and location; the span mutes the location. The `&nbsp;` before the span glues the dot to "GmbH", so the location can wrap to the next line but the dot never starts it (see "Non-breaking spaces and middle dots").
- `<p class="ctx">` – one line of company context. Optional: `build.py` emits it only for roles that have a `ctx`, and the `place` span only for roles that have a place (Rapidobject has none).
- `<ul class="tree">` – the details as an unordered list, styled like the output of the Unix `tree` command – the format of the #JobAlert posts. The branches `├──` and `└──` are not characters in the HTML but CSS borders on `::before` and `::after`. They align in any font, and screen readers do not read out box-drawing characters.
- `<span class="k">Scope</span>` – the key. CSS sets it bold and adds the colon via `content: ":"`. Screen readers generally read such generated content, so they say "Scope: marketing, design …". On the German page the keys carry `lang="en"` – Scope, Team, Result are brand vocabulary.
- Variants among the nine entries: some have no `ctx`, one has no place, and the Brandible and Posterlounge entries contain the drawn arrow inside their tree items.

### Education and footnote references

```html
<dl class="facts">
<div><dt>2025</dt><dd>Data Scientist<sup class="fnref"><a href="#fn-ds" id="ref-ds" aria-describedby="h-notes">1</a></sup>&nbsp;· MLOps Engineer<sup class="fnref"><a href="#fn-mlops" id="ref-mlops" aria-describedby="h-notes">2</a></sup><br><span class="muted">Liora in partnership with Université Paris 1 Panthéon-Sorbonne</span></dd></div>
<div><dt>2023</dt><dd>Agile project management specialist (IHK)</dd></div>
<div><dt>2010</dt><dd>Bachelor’s degree in economics<br><span class="muted">Università degli Studi di Trento</span></dd></div>
<div><dt>Languages</dt><dd>German (native)&nbsp;· English C2&nbsp;· Italian C2&nbsp;· Spanish B1&nbsp;· French A2</dd></div>
</dl>
```

- `<dl class="facts">` – the description-list pattern from the ledger: year (or "Languages") → what.
- `<br>` – a line break that belongs to the content: the institution goes on its own line.
- `<span class="muted">` – grey text, no meaning.
- `’` in "Bachelor’s" – a typographic apostrophe, not the straight `'`.

The footnote reference, piece by piece:

- `<sup class="fnref">` – superscript, the typographic convention for footnote marks.
- `<a href="#fn-ds">` – jumps to the note with `id="fn-ds"` in the Sources section.
- `id="ref-ds"` – the reference itself has an id, so the note can link back to exactly this spot.
- `aria-describedby="h-notes"` – adds a description to the link: the text of the element with that id, the heading "Sources". A screen reader reads "1, link" and then, typically on focus, "Sources". Without it, a lone "1" would mean nothing.
- `1`, `2` – `build.py` numbers the notes in order of first appearance (the inner function `fn()` collects the keys in a list). Reorder the text and the numbers and the list of notes follow.

### Projects

```html
<section class="sec" id="projects" aria-labelledby="h-projects">
<h2 id="h-projects"><span class="no" aria-hidden="true">03</span> Projects</h2>
<div class="body">
<p class="intro"><strong lang="en">Stop starting. Start finishing.</strong></p>
<div class="group"><h3>At E+SERVICE+CHECK</h3>
<ul class="projects">
<li><h4>Call and inquiry pipeline</h4><p>More than half a million calls, two phone systems, five web forms – joined with Odoo master data and Google Ads attribution.</p><p class="stack">Python&nbsp;· BigQuery&nbsp;· Data Studio</p></li>
…
</ul></div>
<div class="group"><h3>Certification capstones</h3>
<ul class="projects">
<li><h4>Rakuten product classification</h4><p>Around 85,000 e-commerce products classified from text and images.</p><p class="stack">Python&nbsp;· Keras&nbsp;· PyTorch&nbsp;· Google Cloud&nbsp;· <a href="https://github.com/PeterStieg/feb25_bds_classification-of-rakuten-e-commerce-products">GitHub</a></p></li>
…
</ul></div>
</div>
</section>
```

- `<p class="intro"><strong lang="en">` – the lead slogan, important and English on both pages.
- `<div class="group">` – two groups, each with an `<h3>` and a list. The outline reads: Projects (h2) → At E+SERVICE+CHECK (h3) → Call and inquiry pipeline (h4).
- `<ul class="projects">` – unordered: the projects are not ranked.
- `<li><h4>…</h4><p>…</p><p class="stack">…</p></li>` – name, description, tech stack. A list item may hold headings and paragraphs; it does not have to be a single line.
- `<a href="https://github.com/…">GitHub</a>` – only the capstones link to their code. The link text "GitHub" appears three times on the page with three different targets (two repositories, one profile). A screen-reader user who lists all links out of context sees three identical names; the surrounding list item supplies the context, which WCAG accepts.

### Approach

```html
<ul class="principles">
<li><p><strong lang="en">Facts, not fluff.</strong> Every figure on this page can be backed up on request. Growth only counts when efficiency keeps pace.</p></li>
…
</ul>
```

- Three principles as a list. Each opens with a slogan in `<strong lang="en">` – important text, English on both pages.
- `<li><p>…</p></li>` – the paragraph inside the item adds no meaning but gives CSS one consistent block per principle.

### Contact

```html
<p class="hello">Hallo&nbsp;· Hi&nbsp;· Ciao</p>
<dl class="reach">
<div><dt lang="en">Online</dt><dd><a class="mail" href="mailto:info@peterstieg.com">info@peterstieg.com</a>&nbsp;· <a href="https://www.linkedin.com/in/peterstieg/" rel="me">LinkedIn</a>&nbsp;· <a href="https://github.com/PeterStieg" rel="me">GitHub</a></dd></div>
<div><dt lang="en">Offline</dt><dd>Leipzig. <span class="muted">Before: Rome, Trento, Jinotega (Nicaragua), Orem (Utah).</span></dd></div>
</dl>
```

- `<p class="hello">` – a greeting in German, English and Italian. The words carry no `lang`, so a screen reader says all three in the page's voice.
- `<dl class="reach">` – Online and Offline as terms, a nod to an older claim ("Work online | Live offline", according to a comment in `build.py`). `lang="en"` on the `<dt>` keeps them English on the German page.
- `href="mailto:…"` – opens the visitor's mail program with the address filled in. The address is in clear text here and in the JSON-LD: convenient for people, readable for address harvesters. The site accepts that trade-off.
- `rel="me"` – "the linked page represents the same person as this one". Services that verify profile links – Mastodon is the best known – check for `rel="me"` in both directions. Together with `sameAs` in the JSON-LD, it ties the site to the LinkedIn and GitHub profiles.

### Sources

```html
<section class="sec" id="notes" aria-labelledby="h-notes">
<h2 id="h-notes"><span class="no ghost" aria-hidden="true">04</span> Sources</h2>
<div class="body">
<ol class="notes">
<li id="fn-ds"><a class="back" href="#ref-ds" aria-label="Back to text">^</a> Data Scientist&nbsp;· issued 10 June 2025&nbsp;· <a href="https://document-factory.datascientest.com/verify/3225d69a-a3b6-4bd2-bafe-df9381eff729">Verify credential</a>&nbsp;· <a href="https://liora.io/en/courses/data-ai/data-scientist" hreflang="en">Course page</a></li>
<li id="fn-mlops">…</li>
</ol>
</div>
</section>
```

- `<h2 id="h-notes">` – the heading that the footnote references use as their description.
- `<ol class="notes">` – ordered: note 1, note 2. Here the numbers are visible (CSS colors the `::marker`), and they match the superscripts because both come from the same list in `build.py`.
- `<li id="fn-ds">` – the jump target. CSS highlights the targeted note with the `:target` selector, so after the jump you see where you landed.
- `<a class="back" href="#ref-ds" aria-label="Back to text">^</a>` – jumps back to the reference. The visible `^` says nothing when spoken, so `aria-label` replaces it: "Back to text, link".
- `Verify credential` – the issuer's verification page; the same URL as in the JSON-LD `hasCredential`.
- `hreflang="en"` on "Course page" – a hint that the target is in English, which matters on the German page.

### Footer

```html
</div>
</main>
<footer class="foot">
<div class="wrap">
<p lang="en">Admiring complexity. Loving simplicity.</p>
<nav aria-label="Legal">
<a href="impressum.html" hreflang="de">Legal notice</a>
<a href="datenschutz.html" hreflang="de">Privacy</a>
<span>© 2026 Peter Stieg</span>
</nav>
</div>
</footer>
```

- `</div></main>` – end of the content.
- `<footer>` – directly inside `<body>`, it becomes the contentinfo landmark: copyright and legal links.
- `<p lang="en">` – the motto, English on both pages.
- `<nav aria-label="Legal">` – a second navigation landmark, named so screen readers can tell "Main" from "Legal". German: "Rechtliches".
- `hreflang="de"` – the legal pages exist only in German. On the English page the link text says "Legal notice", the attribute says the target is German.
- Here the tags sit on separate lines. The nav is a flex container (CSS), so the line breaks do not create extra spaces.
- `© 2026` – `build.py` inserts the current year at build time (`date.today().year`). The year changes with the next build, not on its own.

### The script

```html
<script src="assets/site.js" defer></script>
</body>
</html>
```

- `src` – an external file, so the browser can cache it between visits.
- `defer` – download without stopping the parser, run after the whole document has been parsed, just before the `DOMContentLoaded` event; several deferred scripts run in source order. `site.js` can therefore rely on every element being present. `defer` only works on external scripts.
- Position: a deferred script could also sit in the head, where its download would start earlier. At the end of the body, the download starts only when the parser gets there. For an 18 KB page the difference is milliseconds, and the time-critical part – the theme – already ran in the head.
- Everything `site.js` adds is an enhancement. Without it the page is complete: the motto stands untyped, the theme follows the system, the back-to-top link is always visible.

---

## Non-breaking spaces and middle dots

`&nbsp;` is the entity for U+00A0, the no-break space. It looks like a space but forbids a line break at that point. The site uses it for two typographic rules.

**Middle dots never start a line.** The copy in `build.py` uses " · " as a separator. Before writing any page – the two home pages, the legal pages and the 404 page – the function `dots()` replaces every " · " after `<body>` with `&nbsp;· `. The dot is now glued to the word before it, and the only break opportunity is after it:

```html
<dd>monthly media budget at a RoAS of 4.0&nbsp;· Posterlounge</dd>
```

On a narrow screen this breaks as "…RoAS of 4.0 ·" / "Posterlounge" – never with a dot at the start of a line, where it would look like a bullet point. The tagline adds two more `&nbsp;` so that "Performance Marketing" and "Data Science" stay in one piece each.

`dots()` is a plain text replacement, so it only finds the pattern space – dot – space. In the employer line, a tag sits between the space and the dot. There the role template in `build.py` writes the `&nbsp;` itself, in front of the tag:

```html
<p class="org">Posterlounge GmbH&nbsp;<span class="place">· Leipzig</span></p>
```

The no-break space works across the tag boundary: "GmbH" and "·" stay on one line, and the break opportunity is the space after the dot, inside the span.

**German numbers stay with their units.** On the German page only, the function `nbsp()` glues "25 %", "240.000 €" and "1,7 Mio. €" together, as German typography (DIN 5008) asks. It inserts the character U+00A0 itself, not the entity `&nbsp;` – the same character for the browser, but invisible in view-source and in an editor. The German page contains twelve of them; a search for ` ` finds them.

```html
<dd>Mediabudget im Monat bei einer KUR von 25 %&nbsp;· Posterlounge</dd>
```

(The space between "25" and "%" in this line is a U+00A0.)

## English inside the German page

`build.py` follows an editorial rule: brand elements stay English in every language – claim, tagline, motto, the four Ps, the slogans and the tree labels. On the German page, these elements carry `lang="en"`:

```html
<p class="tagline" lang="en">Performance&nbsp;Marketing&nbsp;· Data&nbsp;Science</p>
<p class="claim" lang="en">Marketing leadership with root access</p>
<div><h3 lang="en">Performance</h3>…
<li><span class="k" lang="en">Scope</span> Marketing, Design und Automatisierung von Grund auf aufgebaut – …</li>
<li><p><strong lang="en">Facts, not fluff.</strong> Jede Zahl auf dieser Seite ist auf Nachfrage belegbar. …</p></li>
<span class="ety">[engl. <i lang="en">marketer</i> × <i lang="en">tinkerer</i> ‚Tüftler‘]</span>
```

- The mechanism: a screen reader switches voice at every `lang` change. Without the attribute, a German voice would read "Built, not briefed" with German pronunciation rules – recognizable at best. Spell-checkers and hyphenation use the same attribute.
- On the English page some of these attributes are left out: `build.py` adds them to the P⁴ headings, the tree keys and the italic words only when the page language is not English (variables `en_attr` and `lang`). Others are written into the shared template and therefore appear on both pages – tagline, claim, prompt, slogans, footer motto, Online/Offline. On the English page they are redundant and harmless.
- The mirror case is on the 404 page: an English page with one German line, marked `lang="de"`.

---

## The other files

### `404.html`

```html
<title>404 – Peter Stieg</title>
<meta name="description" content="Page not found.">
…
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/atkinson-hyperlegible-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
…
<link rel="stylesheet" href="/assets/site.css">
<meta name="robots" content="noindex">
</head>
```

```html
<a class="home" href="/index.html"><span class="caret" aria-hidden="true">&gt;_</span><span class="name">Peter Stieg</span></a>
<nav class="nav" aria-label="Main"><span class="themes" role="group" aria-label="Theme">…</span></nav>
…
<main id="main">
<div class="wrap">
<section class="lost">
<p class="code">404</p>
<h1><code class="dki">{KeyWord:Page}</code> not found.</h1>
<p class="claim" lang="de">Diese Seite gibt es nicht.</p>
<p class="prompt"><span class="caret" aria-hidden="true">&gt;_</span><a href="/">cd ~</a>&nbsp;· <a href="/de/" lang="de">Deutsch</a></p>
</section>
</div>
</main>
…
<script src="/assets/site.js" defer></script>
```

- Absolute paths (`/…`) – the server answers a missing URL such as `https://peterstieg.com/de/old/page` with the content of `404.html`, but the browser still believes it is at `/de/old/page`. Relative paths resolve against that address: `assets/site.css` would become `/de/old/assets/site.css`, which does not exist, and the error page would appear unstyled. A path starting with `/` always begins at the domain root. The trade-off: opened from disk, `/assets/…` points to the root of your file system, so the 404 page only looks right on a server. `build.py` passes `root="/"` for this page alone.
- `<meta name="robots" content="noindex">` – error pages do not belong in search results.
- No `hreflang` alternates, no section links, no language switch (`alternates=False`, `sections=False`, `langs=False` in `build.py`): there is nothing to switch to.
- The logo links to `/index.html`, because there is no `#top` on this page.
- `{KeyWord:Page}` – Google Ads syntax for Dynamic Keyword Insertion: `{KeyWord:Default}` puts the searched keyword into an ad, or the default text when the keyword does not fit. The capitalization of `KeyWord` even controls the case of the inserted words. Here the "default" won – a joke for anyone who has run search campaigns. `<code>` marks it as code; the CSS keeps the regular font and sets it in the accent color.
- `lang="de"` – the German line inside the English page.
- `cd ~` – the shell command "change to the home directory", linked to `/`.
- The page has no minimap and no back-to-top link. `site.js` checks whether elements exist before using them, so it runs here without errors.
- Like every page, this one passes through `dots()`: the `&nbsp;` glues the dot to `cd ~`.

### `.htaccess`

```apache
ErrorDocument 404 /404.html
```

- A configuration file for the Apache web server, read per directory. This line says: for every "not found" error, deliver `/404.html`.
- With a local path, Apache keeps the status code 404, so browsers and crawlers learn that the page does not exist. With a full `https://` URL, Apache would send a redirect instead, and the error status would be lost.
- Only Apache and compatible servers read `.htaccess`, and only if the host allows overrides. GitHub Pages ignores it and serves a `404.html` from the site root automatically. With both in place, the error page works on either kind of host.
- The leading dot makes it a hidden file on Unix systems; some FTP clients and file managers do not show it. Since `site/` is uploaded by hand (see `decisions.md`), check that it arrived.

### `robots.txt`

```text
User-agent: *
Allow: /

Sitemap: https://peterstieg.com/sitemap.xml
```

- Well-behaved crawlers fetch `/robots.txt` before anything else.
- `User-agent: *` – the rules below apply to every crawler.
- `Allow: /` – everything may be crawled. An empty file would mean the same; the explicit line documents the intent.
- `Sitemap:` – the absolute URL of the sitemap. This line stands outside the user-agent rules and applies to all crawlers.
- `robots.txt` controls crawling, not indexing. To keep a page out of search results, a crawler must be allowed to fetch it and read its `noindex` – that is why the legal pages are not blocked here. A page blocked in `robots.txt` can still appear in results as a bare URL if other sites link to it.

### `sitemap.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
<url><loc>https://peterstieg.com/</loc><lastmod>2026-10-23</lastmod>
<xhtml:link rel="alternate" hreflang="en" href="https://peterstieg.com/"/><xhtml:link rel="alternate" hreflang="de" href="https://peterstieg.com/de/"/></url>
<url><loc>https://peterstieg.com/de/</loc><lastmod>2026-10-23</lastmod>
<xhtml:link rel="alternate" hreflang="en" href="https://peterstieg.com/"/><xhtml:link rel="alternate" hreflang="de" href="https://peterstieg.com/de/"/></url>
</urlset>
```

- `<?xml …?>` – XML declaration: version and encoding.
- `<urlset xmlns="…sitemap/0.9">` – the root element of the sitemap protocol. `xmlns:xhtml="…"` declares the prefix `xhtml:`, so the file may borrow the `<link>` element from XHTML.
- `<url><loc>` – one entry per page that should be found: only the two home pages. The legal pages and the 404 page carry `noindex`, so they are left out.
- `<lastmod>` – the build date (`date.today()` in `build.py`). It changes with every build, even when no text changed. Google uses `lastmod` only from sites where it proves consistently accurate.
- `<xhtml:link rel="alternate" hreflang="…">` – the same language pairing as the `<link>` tags in the head, delivered a second way. Each entry lists every version including itself, as the head does. The `x-default` from the head is not repeated here; the head already declares it.

### `impressum.html` and `datenschutz.html`

```html
<html lang="de">
…
<title>Impressum – Peter Stieg</title>
…
<link rel="canonical" href="https://peterstieg.com/impressum.html">
…
<meta name="robots" content="noindex, follow">
</head>
<body>
<a class="skip" href="#main">Zum Inhalt springen</a>
…
<a class="home" href="de/index.html">…</a>
…
<main id="main">
<div class="wrap legal">
<div class="body">
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
<address>Peter Stieg<br>
…
Deutschland</address>
…
<p>peterstieg.com: <a href="index.html" hreflang="en">English</a>&nbsp;· <a href="de/index.html">Deutsch</a></p>
</div>
</div>
</main>
```

- German pages, built from the German settings with `root=""`, because they sit in the site root next to `index.html`.
- `<meta name="robots" content="noindex, follow">` – "do not show this page in search results, but do follow its links". `follow` is the default; it is written out for clarity. Why `noindex`: legal pages answer no search query, and the legal notice carries a full postal address that should not turn up when someone searches the name.
- No alternates, no language switch, no section links – the header shows only the logo (linking to the German home page) and the theme buttons.
- `<address>` – contact information for the owner of the page: the right element for a legal notice. Browsers set it in italics by default; the CSS resets that.
- `<br>` – line breaks that belong to the content: an address is the textbook case for `<br>`.
- The closing line links back to both language versions.
- The privacy page has the same structure with more `<h2>` sections and a dated line `<p class="muted">Stand: Oktober 2026</p>`, which is fixed text in `build.py` and needs a manual update when the policy changes.

### `favicon.svg`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <style>
    .c { fill: none; stroke: #7A1A2C; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
    .u { fill: #7A1A2C; }
    @media (prefers-color-scheme: dark) { .c { stroke: #C98593; } .u { fill: #C98593; } }
  </style>
  <path class="c" d="M5 8 L13 16 L5 24"/>
  <rect class="u" x="15" y="22" width="13" height="4" rx="2"/>
</svg>
```

A static file, not generated by `build.py`.

- `xmlns="http://www.w3.org/2000/svg"` – required in a standalone SVG file. Inline SVG inside HTML gets the namespace from the HTML parser, which is why the icons in the page do without it.
- `viewBox="0 0 32 32"` – a 32 × 32 drawing area.
- `<style>` – CSS inside the SVG. It applies only to this drawing.
- `.c` – the chevron: no fill, a 4-unit stroke in the accent color, with round ends and corners.
- `.u` – the underscore: a filled shape in the same color.
- `@media (prefers-color-scheme: dark)` – in dark mode, the lighter accent color. Both values equal `--accent` in `site.css`. The query sees the system or browser setting; the favicon is a separate document and knows nothing about the page's `data-theme`, so it does not follow the theme buttons. Support for media queries inside favicons varies between browsers.
- `<path d="M5 8 L13 16 L5 24"/>` – from the upper left to the middle right and back to the lower left: `>`.
- `<rect x="15" y="22" width="13" height="4" rx="2"/>` – a 13 × 4 bar with rounded corners (radius 2) at the bottom: `_`.
- Together: `>_`, the same mark as the caret in the header.

---

## Try it

1. **Source vs DOM.** Open https://peterstieg.com/ and press Ctrl+U (view-source). Find the comment and the theme boot script. Then open DevTools (F12) → Elements and compare: `<html>` now has `class="js"`, one theme button has `aria-pressed="true"`, and on a wide screen `.minimap` is full of `span.mm-bar`. Click the moon and check `<html data-theme="dark">` and, under Application → Local Storage, the key `theme`. Finally press Ctrl+Shift+P, run "Disable JavaScript" and reload: theme buttons gone, motto static, back-to-top button always visible.
2. **Accessibility tree.** In Elements, select a `span.arr` and open the Accessibility pane: role "image", name "to". Select a theme button and click it – watch "pressed" flip. Select the footnote link "1" and find its description "Sources". Then open the Network panel, filter by "Font" and reload: the two preloaded fonts start early, the italic only after `site.css` has been read.
3. **Link preview and structured data.** Paste https://peterstieg.com/ into LinkedIn's Post Inspector (https://www.linkedin.com/post-inspector/) and compare title, description and image with the `og:` tags; repeat with https://peterstieg.com/de/. The Inspector fetches fresh, which also refreshes LinkedIn's cached card. Then paste the URL into https://validator.schema.org/ and find the Person with its `sameAs` and `hasCredential` entries.

## Key terms

- **Accessibility tree** – the browser's version of the page for assistive technology: roles, names and states, derived from the HTML. `aria-hidden="true"` removes an element from it; `.sr-only` keeps text in it while hiding it from the screen.
- **Accessible name** – what a screen reader calls an element: a link's text, a button's `aria-label`, a region's heading via `aria-labelledby`.
- **Landmark** – a major page area a screen reader can jump to: banner (`<header>`), navigation (`<nav>`), main (`<main>`), region (a named `<section>`), contentinfo (`<footer>`).
- **Canonical URL** – the one official address of a page, declared with `<link rel="canonical">`, so search engines merge its variants.
- **hreflang** – an attribute that pairs language versions of a page, so search engines show each searcher the right one; `x-default` is the fallback.
- **Open Graph** – `og:` meta tags that platforms such as LinkedIn read to build link previews.
- **JSON-LD** – structured data as JSON in a `<script type="application/ld+json">` block, using the schema.org vocabulary; read by crawlers, never executed.
- **Preload** – `<link rel="preload">`: fetch a resource early, before the browser would discover it. Fonts need `as="font"` and `crossorigin`.
- **defer** – a script attribute: download in parallel, execute after parsing, in source order.
- **No-break space** – U+00A0, written `&nbsp;`: looks like a space, forbids a line break at that point.

---

[Previous: build.py](01-build.md) · [Next: CSS](03-css.md)
