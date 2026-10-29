# Decisions

Why the site looks and reads the way it does. Newest first within each topic; change a line here when a decision changes.

## Content

- **Languages:** English is the default, German lives under `/de/`. Italian is out until there is a native localization – a translation is not enough.
- **Brand elements stay English** in every language: claim, tagline, motto, the four Ps, the slogans and the tree labels (Scope, Team, Result – as in the #JobAlert posts).
- **Localized, not translated:** each language follows its own conventions – the dictionary entry in Merriam-Webster style (EN) and Duden style (DE), Trient instead of Trento in German, KUR in German and RoAS in English.
- **Current employer:** no internal cost figures, absolute values rounded ("more than doubled", "more than half a million").
- **No first-person monologue.** Telegram style, facts instead of adjectives.
- **Four coined elements, no more:** the claim, the motto, *marketinkerer* and P⁴. Ten were too many (feedback, 29.10.2026); cut were "Everything human:e.", the footer line "Admiring complexity. Loving simplicity.", "Stop starting. Start finishing." and the Approach slogans "Facts, not fluff." · "Built, not briefed." · "Prompted, not pasted." – their sentences stay. AI is named once as a principle, in Approach, never as a label on single projects.
- **A principle behind an i:** "Processes fit people, not the other way round." sits behind a superscript *i* after People instead of in the text – there when asked for, out of the way otherwise.
- **P⁴:** four fields without an intro line ("P as in Peter" dropped). Pixels names the tools that are used (Inkscape, Canva, Python), not Figma.
- **Order:** newest first everywhere – the timeline, the steps inside an entry, the ledger, Education, Projects. One direction, so nothing reads as reversed.
- **Ledger:** four results, newest first, each naming its company; the name links to the role under Experience, marked with a superscript ↓ in the accent colour – like the footnote numbers and the *i*, it says "more on this page" (↗ would mean "leaves the site"). "17 shops in 12 languages across Europe", not "European Economic Area": the shops included Switzerland and the UK.
- **Roles:** the same tree labels wherever the facts exist – Team, Scope, Result; a role shows only what is known rather than filler. Every role shows its length under the dates, in full words, counted like LinkedIn (first and last month included); the running one is recounted on every visit. Posterlounge keeps "Head of Marketing" as its heading – easier to read than the whole path; its four titles open behind "Three promotions", newest first, each with its dates and length from the contracts – real titles are what people search for. The two Liora courses stay in the timeline, marked as trainings: full-time from 02 to 07/2025, they show what that stretch was without reading as jobs. Marketing automation is named where it was done (Brandible, Rapidobject). 2010–2014 stays one entry in the timeline (with exact months); its five positions open behind "All five positions", listed like the promotions – title, company, dates and length.
- **Wordplay:** only Pete's own or in his patterns. Tried and dropped: "einSTIEG" as a heading, "See also: root access", "The other four Ps".
- **Cloud:** Google Cloud is a tool; Azure appears only as the platform of single projects. IT administration (Intune, GPO) is not on the site.
- **Certificates:** the profile names them without a year (the year is in Education, where it belongs). Two separate bootcamps (Data Scientist 02–05/2025, MLOps Engineer 05–07/2025), each with a footnote linking the verification page from the diploma's QR code and the course page.
- **More proof:** the IHK certificate (2023, the IHK as issuer, like the other certificates) and the edX course "Introduction to Artificial Intelligence" by Microsoft (2018) carry footnotes to their verification pages too. The capstones link their Streamlit demos next to GitHub. E+SERVICE+CHECK, Brandible and Posterlounge link their websites. Every new link target is named in the privacy statement.
- **Languages:** one per line – easier to scan than a row with dots.
- **Offline:** Leipzig, before that Rome, Trento, Jinotega (Nicaragua), Orem (Utah).
- **Not on the site:** recommendations as quotes, photo (pending).

## Design

- **Typeface:** Atkinson Hyperlegible, self-hosted, no font service.
- **Colour:** bordeaux as the only accent (prompt, focus, footnotes, hover). Light and dark themes with the same structure.
- **Hero:** same order as the LinkedIn banner – name, tagline, claim, prompt `>_ sudo dream plan ship`.
- **Logo:** the lockup `>_ P/S` ("Ein Takt", decided 25.10.2026; v2 29.10.2026: `>_` raised 8.63 units, so the `_` ends exactly on the P's foot instead of missing it by a hair) in the header, 28 px tall, inline so it follows light and dark. Source and generator in `src/lockup/`. The monogram alone (final 23.10.2026, `src/monogram/`) is the favicon set, the mark in the link preview (`og-image.png`), the avatar and the footer of printed documents.
- **Docking:** while scrolling, PETER STIEG and `>_` travel into the header as the wordmark `>_ PETER STIEG`, so the name is visible once. Scrolling on (180 px), the wordmark condenses into the lockup – the closing step of `src/lockup/animation/ps-morph.html`, scroll-driven and reversible. Reduced motion: the lockup appears instantly.
- **Minimap:** on wide screens, the page drawn as code lines like the banner; click or drag to jump.
- **Jump control:** once the name has docked, a pill bottom right (under the minimap on wide screens): up, the chapter number, down. Up and down go to the start of the section above and below, the number opens a list of all sections. It replaced the round back-to-top button. Without JavaScript: up to the top and the list.
- **A heading always in view:** on wide screens the section heading sticks in its column; on phones it sticks under the header as one bar with it. The menu (wide screens) and the jump control's number (all screens) name the chapter.
- **Four chapters, like the parts of a slide deck:** 01 Profile (with P⁴), 02 Experience (with Education), 03 Projects (with Approach), 04 Contact (with Sources). The number stands in front of the chapter's heading, in the accent colour and regular weight; the sections inside a chapter carry the same number invisibly, so all titles line up like an outline. Education moved up behind Experience for this.
- **Menu numbers:** the four menu links are the four chapters, numbered like their headings – no gaps. Below 56rem the numbers drop so the header fits.
- **You are here:** while scrolling, the menu link of the chapter being read looks like its heading – number in the accent colour, label in ink and bold – also in the sections that belong to it; at the very bottom, Contact. The bold width is reserved, so the menu never shifts.
- **Links that leave the site** open in a new tab, so the page stays open behind them. A muted ↗ marks them, in accent on hover – quieter than the accent ↓, so fifteen of them do not clutter the page; screen readers hear "opens in a new tab". Mail, menu, language switch and legal pages stay in the same tab.
- **Arrows and tree lines are drawn**, because the typeface has no → glyph and box-drawing characters depend on the font.

## Tech

- **No framework, no build tools:** one Python script, plain CSS, one small script file.
- **Favicons:** `favicon.ico` (16 and 32 px hand-hinted, 48 px) for browsers and tabs that want a bitmap, `favicon.svg` that follows light and dark, `apple-touch-icon.png`, and `site.webmanifest` with 192 and 512 px icons for Android home screens. `.htaccess` gives the manifest its MIME type.
- **Notes as popovers:** the *i* uses the HTML popover API – opens, closes on a click elsewhere or Esc, and stays accessible without JavaScript; the script only places it next to the *i*.
- **Plain text that reads right:** search engines, sourcing tools and parsers read the page as text, so what CSS draws must not carry meaning alone – arrows keep the word "to" as hidden text, the tree labels carry their colon in the HTML, a note sits after its heading instead of inside it. Checked by extracting the text.
- **Findability:** Search Console, Bing Webmaster Tools and links from LinkedIn and GitHub – tracked in issue #19.
- **Privacy:** no cookies, no analytics, no third-party requests. The theme choice is stored in the visitor's browser (localStorage) only after a click.
- **Sitemap:** generated by the build; it lists pages, not content, so it only needs a rebuild when pages are added or removed. `lastmod` is the build date.
- **404:** `{KeyWord:Page} not found.` – Google Ads Dynamic Keyword Insertion, for those who know. `.htaccess` activates it on Apache hosting.
- **Deploy:** manual upload of `site/` to IONOS. Auto-deploy via GitHub Actions is an open option.
- **peterstieg.github.io forwards to peterstieg.com** instead of mirroring the site: one address for search engines, and the privacy statement (host: IONOS) stays true.
- **Forward page:** a two-second terminal scene instead of "Moved to …" – `mv -v peterstieg.github.io peterstieg.com`, the real `mv -v` output, `cd peterstieg.com` (with the path for deep links), then on. Click or Enter skips, Esc or Ctrl+C stops (`^C`). Reduced motion: no typing, forward after 1.2 s; no JavaScript: plain text, refresh after 3 s. Typeface: Atkinson Hyperlegible Mono, self-hosted in `forward/fonts/` – no third-party request.
