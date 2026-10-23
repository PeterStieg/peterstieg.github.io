# 01 · build.py: from content to HTML

`src/build.py` is the whole site generator: one Python file that holds every line of copy in both languages, turns it into HTML strings and writes finished pages to `site/`. It runs on the Python standard library alone – no framework, no template engine, no `pip install`. Everything else in `site/` (CSS, JavaScript, fonts, images) is maintained by hand and covered in later chapters.

The file reads top to bottom in this order: docstring · imports · constants · `CONTENT` · HTML fragments · small builder functions · `page()` · legal pages · typography fixes · `build()`. Every function returns a string of HTML; bigger functions call smaller ones and glue their strings together. Nothing touches the disk until `build()` at the very end.

```
CONTENT["en"]  →  page(c)  →            dots()  →  site/index.html
CONTENT["de"]  →  page(c)  →  nbsp()  →  dots()  →  site/de/index.html
```

---

## 1 · Shebang and docstring

```python
#!/usr/bin/env python3
"""peterstieg.com – site generator.

All copy lives in CONTENT (EN, DE). `python3 src/build.py` writes the static
pages to site/. No framework, no dependencies beyond Python 3.

Editorial rules this file follows:
 1. Current employer (E+SERVICE+CHECK): no internal cost figures (no KUR/RoAS),
    absolute values rounded ("more than doubled", "more than half a million").
 2. Metrics: German uses KUR, English uses RoAS (KUR 25 % = RoAS 4.0;
    13.2 → 12.8 % = 7.6 → 7.8; 10.1 % = 9.9). The direction flips: KUR falls, RoAS rises.
 3. No first-person monologue. Telegram style, facts instead of adjectives.
 4. En dash with spaces ( – ), middle dot ( · ) as separator.
 5. Brand elements stay English in every language: claim, tagline, motto, the four Ps,
    the slogans and the tree labels (as in #JobAlert: Scope, Team, Result).
    Everything else is localized, not translated.
 6. Google Cloud is a tool, Azure only the platform of single projects. AI is named once
    as a principle ("Prompted, not pasted."), never as a label on single projects.
 7. No wordplay that isn't Pete's own or doesn't follow his patterns.
"""
```

- `#!/usr/bin/env python3` – the shebang. On Linux and macOS it lets the file run as a program (`./src/build.py` after `chmod +x`); `env` looks up `python3` on your `PATH`. It has no effect when you start the script explicitly with `python3 src/build.py`.
- The triple-quoted string is the first statement of the module, so Python stores it as the module's docstring (`build.__doc__`). It is documentation, not executed code.
- The editorial rules sit in the code file on purpose: whoever edits the copy – you, someone else, an AI assistant – sees them right next to the text they govern. Only two of them have code support; the rest are discipline:

| Rule | What it means in the code |
|---|---|
| 1 · No cost figures for the current employer | Copy only. The E+SERVICE+CHECK entries in `CONTENT` say "> 2×", "more than doubled", "More than half a million" – no exact counts, no KUR or RoAS. |
| 2 · KUR in German, RoAS in English | The two dictionaries carry different numbers on purpose. RoAS = 1 ÷ KUR: 25 % ↔ 4.0 · 13.2 % ↔ 7.6 · 12.8 % ↔ 7.8 · 10.1 % ↔ 9.9. A better result is a falling KUR and a rising RoAS. Changing a figure means converting it, not translating it. |
| 3 · Telegram style | Copy only. |
| 4 · En dash, middle dot | Written into the strings. `dots()` keeps a ` · ` from starting a line, `nbsp()` keeps German numbers and units together. |
| 5 · Brand elements stay English | They live outside `CONTENT` (`TAGLINE`, `CLAIM`, `MOTTO`, `P4`, `SLOGANS`, `PROJECTS_LEAD`) or appear unchanged in both dictionaries (tree labels such as `"Scope"`). On the German page the code marks them with `lang="en"`. |
| 6 · Google Cloud, Azure, AI | Copy only: Google Cloud in `STACK_DS` and the Pipelines text, Azure only in project entries, AI only in the third approach sentence and its slogan. |
| 7 · No foreign wordplay | Copy only. |

---

## 2 · Imports

```python
from datetime import date
from html import escape as e
from pathlib import Path
import json
import re
```

- `date` – `date.today()` supplies the copyright year in `footer()` and the `lastmod` date in the sitemap.
- `escape as e` – `html.escape` under a one-letter alias, because it is called dozens of times inside f-strings and `{e(text)}` keeps those lines short. It replaces the five characters that have meaning in HTML: `&` → `&amp;` · `<` → `&lt;` · `>` → `&gt;` · `"` → `&quot;` · `'` → `&#x27;`.
- Why escaping matters: unescaped, a `<` in the copy opens a tag, an `&` may start an entity, and a `"` inside an attribute value ends the attribute – the page breaks in ways that are hard to spot. If text ever comes from outside (a form, an API, a spreadsheet export), the same gap lets a `<script>` in that text run in the visitor's browser: cross-site scripting (XSS). All copy here is your own, so the practical risk is broken markup; the habit protects you the day content comes from elsewhere.
- Pitfall: never use `e` as a variable name in this file. Inside a function, even `except Exception as e:` turns `e` into a local variable for the whole function, and every `e(...)` call in it fails with `UnboundLocalError`.
- `Path` – object-oriented file paths: `/` joins parts, `.parent` goes up a level, `.mkdir()`, `.write_text()` and `.rglob()` do the file work.
- `json` – serializes the structured-data block in `jsonld()`.
- `re` – regular expressions for three text markers: `*italics*`, syllable dots and `[[footnotes]]`.

All five are standard library – that is what "no dependencies beyond Python 3" means.

---

## 3 · Paths and links

```python
SITE = Path(__file__).resolve().parent.parent / "site"
URL = "https://peterstieg.com/"
EMAIL = "info@peterstieg.com"
LINKEDIN = "https://www.linkedin.com/in/peterstieg/"
GITHUB = "https://github.com/PeterStieg"
REPO_DS = "https://github.com/PeterStieg/feb25_bds_classification-of-rakuten-e-commerce-products"
REPO_MLOPS = "https://github.com/PeterStieg/may25_bmlops_classification-of-rakuten-e-commerce-products"
```

- `SITE` – the output folder, computed rather than typed:
  - `__file__` is the path of this script as Python received it, possibly relative (`src/build.py`).
  - `.resolve()` makes it absolute and resolves symbolic links.
  - `.parent` is `src/`, `.parent.parent` the repository root.
  - `/ "site"` appends the folder name. Result: the script writes to the right place no matter which directory you start it from.
- `URL` ends with a slash. Every use concatenates (`URL + slug`, `f"{URL}og-image.png"`), so the trailing slash must stay and the parts appended to it must not start with one.
- `EMAIL`, `LINKEDIN`, `GITHUB`, `REPO_*` – each defined once and used in several places (contact section, JSON-LD, legal pages, project links). Change once, rebuild, done.
- UPPER_CASE names mark constants. Python does not enforce this – it is a convention that says "set once, never reassigned".

---

## 4 · Brand constants

```python
NAME = "Peter Stieg"
TAGLINE = "Performance Marketing · Data Science"
CLAIM = "Marketing leadership with root access"
MOTTO = "sudo dream plan ship"
TITLE = f"{NAME} – {TAGLINE}"
```

- These live outside `CONTENT` because they are identical in every language (rule 5).
- `NAME` appears in the page title, the hero `<h1>`, the header logo, the footer, `meta author` and JSON-LD. `TAGLINE` and `CLAIM` appear in the hero and the social-preview image description. `MOTTO` appears in the source comment and the hero prompt.
- `TITLE` is an f-string: `{NAME}` and `{TAGLINE}` are evaluated once, when the module loads. The result is a plain string; it does not "remember" where it came from.
- Several places insert these constants without `e()` (`{NAME}`, `{CLAIM}`, `{MOTTO}`). That is safe only because they contain none of `& < > "`. If you ever add such a character, wrap the uses in `e()`.

---

## 5 · LANGS

```python
LANGS = [("en", "EN", "English", "index.html", ""),
         ("de", "DE", "Deutsch", "de/index.html", "de/")]
```

A list of 5-tuples, one per language. The position of each value is its meaning:

| Index | Example | Used for |
|---|---|---|
| 0 · code | `"de"` | `hreflang`, `lang`, key into `CONTENT` |
| 1 · label | `"DE"` | visible text in the language switch |
| 2 · name | `"Deutsch"` | tooltip in the switch, in its own language |
| 3 · path | `"de/index.html"` | link target in the language switch, relative to the site root |
| 4 · slug | `"de/"` | public URL part for canonical, hreflang and sitemap |

- A list, not a dict, because order matters: English comes first in the switch and the sitemap.
- path vs slug: the file is `de/index.html`, the public URL is `/de/`. Web servers answer a folder URL with its `index.html`, so search engines get the clean URL, while the explicit file name keeps the language links working when you open the files straight from disk.
- The tuples are unpacked by position all over the file: `for code, _, _, _, slug in LANGS`, `for code, *_ in LANGS`, `for *_, slug in LANGS`. Pitfall: add a sixth field and every fixed-length unpacking raises `ValueError: too many values to unpack`; only the starred forms keep working.
- `CONTENT[...]["path"]` repeats index 3. Two copies of the same fact – keep them in sync.
- Adding a language takes three things: a `LANGS` entry, a complete `CONTENT` entry, and a date in that language in every `NOTES` entry (otherwise `n["date"][L]` raises `KeyError`).

---

## 6 · P⁴, slogans, project lead

```python
# P as in Peter – English in every language, like M³ and F³.
P4 = ["Performance", "Pipelines", "Pixels", "People"]
P4_TAIL = {3: "Everything human:e."}
SLOGANS = ["Facts, not fluff.", "Built, not briefed.", "Prompted, not pasted."]
PROJECTS_LEAD = "Stop starting. Start finishing."
# section numbers, like the chapters of a slide deck; Sources stays unnumbered, like a deck's appendix
NUMBERED = ["profile", "fields", "experience", "projects", "approach", "education", "contact"]
```

- `P4` – the four headings of the P⁴ section. `page()` pairs them by position with `CONTENT[lang]["fields"]`.
- `P4_TAIL` – an extra closing line for selected fields, keyed by index (3 = People). A dict instead of a list because only some fields have a tail; `i in P4_TAIL` checks the keys.
- `SLOGANS` – paired by position with `CONTENT[lang]["approach"]`.
- `PROJECTS_LEAD` – the intro line of the Projects section.
- `NUMBERED` – the sections that get a number in front of their heading, in page order. `section()` takes the number from the position in this list: `profile` is 01, `contact` 07. Sources (`notes`) is not in the list and stays unnumbered. The keys are the English ones, so both languages share the numbers.
- Pitfall: pairing by position. Reorder `P4` without reordering both `fields` lists and every text lands under the wrong heading. And `zip()` stops at the shorter list: a missing fourth text silently drops "People" – no error.

---

## 7 · NOTES and stacks

```python
# Footnotes: verification links from the QR codes on both diplomas, plus the course pages.
NOTES = {
    "ds": {"title": "Data Scientist",
           "verify": "https://document-factory.datascientest.com/verify/3225d69a-a3b6-4bd2-bafe-df9381eff729",
           "course": "https://liora.io/en/courses/data-ai/data-scientist",
           "date": {"en": "10 June 2025", "de": "10. Juni 2025"}},
    "mlops": {"title": "MLOps Engineer",
              "verify": "https://document-factory.datascientest.com/verify/46b46e0c-cd3b-458a-8e9f-4ee08feb9164",
              "course": "https://liora.io/en/courses/data-ai/mlops",
              "date": {"en": "1 September 2025", "de": "1. September 2025"}},
}

STACK_DS = "Python · Keras · PyTorch · Google Cloud"
STACK_MLOPS = "Docker · Airflow · MLflow · FastAPI · Grafana"
```

- `NOTES` – a dict of dicts. The outer key (`"ds"`, `"mlops"`) is the footnote ID: it appears in the `[[ds]]` markers in the copy and in the HTML ids `fn-ds` and `ref-ds`.
- Inner keys: `title` (credential name), `verify` (the URL behind the QR code on the diploma), `course` (course page), `date` (one preformatted string per language).
- Why preformatted dates instead of `date` objects: Python's month names (`%B` in `strftime`) follow the system locale, and switching to a German locale depends on what the machine has installed. Two literal strings avoid that entirely.
- `NOTES` feeds both the visible footnotes in `page()` and the credentials in `jsonld()` – one source, two outputs.
- `STACK_DS`, `STACK_MLOPS` – the tool lines of the two capstone projects. They are the same in both languages, so they are defined once and referenced from both dictionaries.

---

## 8 · CONTENT – all copy, two languages

The code below is shortened: `…` stands for copy that follows the same pattern.

```python
CONTENT = {
    # ------------------------------------------------------------------ EN
    "en": {
        "lang": "en", "path": "index.html", "root": "", "locale": "en_GB",
        "aria_main": "Main", "aria_legal": "Legal", "aria_lang": "Language",
        "theme": ("Theme", "Light", "Dark"), "arrow": "to", "to_top": "Back to top",
        "desc": "Marketinkerer from Leipzig: …",
        "skip": "Skip to content",
        "nav": [("profile", "Profile"), ("experience", "Experience"), ("projects", "Projects"), ("contact", "Contact")],
        "sec": {"profile": "Profile", "experience": "Experience", "projects": "Projects", "approach": "Approach",
                "education": "Education", "contact": "Contact", "notes": "Sources"},
        "entry": {"hw": "mar·ke·tin·ker·er", "pos": "noun", "ety": "[*marketer* × *tinkerer*]",
                  "def": "A marketing leader who builds the tools behind the campaigns."},
        "profile": "Leadership roles at four companies, …",
        "ledger_label": "Selected results",
        "ledger": [
            ("€6k → €240k", "monthly media budget at a RoAS of 4.0 · Posterlounge"),
            …
        ],
        "p4_intro": "P as in Peter.",
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, SEO and marketplaces. …",
            …
        ],
        "roles": [
            {"when": "since 11/2025", "title": "Head of Marketing", "org": "E+SERVICE+CHECK GmbH", "place": "Laucha",
             "ctx": "TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.",
             "tree": [("Scope", "…"),
                      ("Result", "…")]},
            …
        ],
        "groups": [
            ("At E+SERVICE+CHECK", [
                ("Call and inquiry pipeline", "…", "Python · BigQuery · Data Studio", None),
                …
            ]),
            ("Certification capstones", [
                ("Rakuten product classification", "…", STACK_DS, REPO_DS),
                …
            ]),
        ],
        "approach": [
            "Every figure on this page can be backed up on request. …",
            …
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora in partnership with Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Agile project management specialist (IHK)", ""),
            …
        ],
        "offline": ("Leipzig.", "Before: Rome, Trento, Jinotega (Nicaragua), Orem (Utah)."),
        "notes": {"issued": "issued", "verify": "Verify credential", "course": "Course page", "back": "Back to text"},
        "imprint": "Legal notice", "privacy": "Privacy",
        "jobtitle": "Head of Marketing",
    },
    # ------------------------------------------------------------------ DE
    "de": {
        "lang": "de", "path": "de/index.html", "root": "../", "locale": "de_DE",
        …
        "ids": {"profile": "profil", "fields": "p-wie-peter", "experience": "stationen", "projects": "projekte",
                "approach": "arbeitsweise", "education": "ausbildung", "contact": "kontakt", "notes": "quellen"},
        …
    },
}
```

`CONTENT` is a dict with one entry per language. Each entry is itself a dict that `page()` receives as its parameter `c` – that is why nearly every function in the file takes `c` as its first argument.

### Every key and what it feeds

Page mechanics:

| Key | Type | Feeds |
|---|---|---|
| `lang` | str | `<html lang>`, the `!= "en"` checks that mark English words with `lang="en"`, the date lookup in the footnotes |
| `path` | str | output file relative to `site/` (in `build()`); header home link on legal and 404 pages |
| `root` | str | prefix from the page back to the site root: `""` for `/index.html`, `"../"` for `/de/index.html`. Prepended to every asset and internal link |
| `locale` | str | `og:locale`; the other languages' values become `og:locale:alternate` |
| `ids` | dict, DE only | German section anchors (`#stationen` instead of `#experience`), read through `sid()` |

Interface labels:

| Key | Type | Feeds |
|---|---|---|
| `aria_main`, `aria_legal`, `aria_lang` | str | accessible names of the header nav, footer nav and language group |
| `theme` | 3-tuple | group label, "light" label, "dark" label for `theme_switch()` |
| `arrow` | str | what a screen reader says for a drawn → (`"to"` / `"auf"`) |
| `to_top` | str | label of the back-to-top button |
| `skip` | str | text of the skip link |
| `nav` | list of (id, label) | header links |
| `sec` | dict | section headings, keyed by internal section name |
| `notes` | dict | labels in the Sources list |
| `imprint`, `privacy` | str | footer links |

Metadata:

| Key | Type | Feeds |
|---|---|---|
| `desc` | str | `meta description`, `og:description`, JSON-LD `description` |
| `jobtitle` | str | JSON-LD `jobTitle` |

Copy:

| Key | Type | Feeds |
|---|---|---|
| `entry` | dict | the dictionary entry: `hw` headword with syllable marks, `pos` part of speech, `ety` etymology, `def` definition |
| `profile` | str | the profile paragraph |
| `ledger_label`, `ledger` | str, list of (figure, context) | the results list in the profile |
| `p4_intro`, `fields` | str, list of 4 str | the P⁴ section, paired with `P4` |
| `roles` | list of dicts | Experience: `when`, `title`, `org`, `place` (may be `""`), `ctx` (optional), `tree` (list of (label, text)) |
| `groups` | list of (title, items) | Projects; each item is (name, text, stack, link or `None`) |
| `approach` | list of 3 str | paired with `SLOGANS` |
| `facts` | list of (label, value, sub-line or `""`) | Education |
| `offline` | 2-tuple | Contact: current city, earlier places |

### How EN and DE mirror each other

- Same keys, same shapes, same number and order of list items. The only key that exists in one language and not the other is `ids` – English uses the internal keys directly as anchors.
- Localized, not translated: German uses KUR, English RoAS (rule 2), job titles follow German usage ("Leiter Marketing"), number formats follow each language ("6.000 → 240.000 €" vs "€6k → €240k").
- English inside German: tree labels such as `"Scope"`, `"Team"`, `"Result"`, `"Capstone"` stay English in the DE dict (rule 5).
- Nothing checks parity. A key missing in DE raises `KeyError` as soon as `page()` asks for it – loud and easy to find. A missing list item – a role or project only added in EN – is silent: the German page simply shows one entry fewer. Edit both languages in the same sitting.
- Quick parity check from the repository root (importing does not build anything, see section 25):

  ```
  python3 -c "import sys; sys.path.insert(0, 'src'); import build as b; print(set(b.CONTENT['en']) ^ set(b.CONTENT['de']))"
  ```

  It prints `{'ids'}`. Anything else means a key is missing on one side. (`^` on sets is the symmetric difference: elements in exactly one of the two.)

### Markers inside the copy

| Marker | Example | Becomes | Handled by |
|---|---|---|---|
| `→` | `"€6k → €240k"` | a drawn SVG arrow with a spoken label | `t()` |
| `*word*` | `"[*marketer* × *tinkerer*]"` | `<i>word</i>` – words cited as words, like in a dictionary | `t()` |
| `[[key]]` | `"Data Scientist[[ds]]"` | a numbered footnote reference to `NOTES[key]` | regex in `page()`, education section |
| ` · ` | `"… · Posterlounge"` | a middle dot glued to the word before it | `dots()` |

Pitfall: the markers only work where the code runs the text through the matching function. `t()` handles `entry["ety"]`, the first item of each `ledger` pair and the values in each role's `tree`. The `[[…]]` regex runs only on the middle value of each `facts` tuple. Everywhere else – `profile`, `fields`, `ctx`, `groups`, `approach` – the text only goes through `e()`: asterisks stay visible and `→` stays a plain character in a fallback font.

---

## 9 · SOURCE_NOTE

```python
SOURCE_NOTE = f"""<!--
  Hallo · Hi · Ciao – view-source counts as root access, too.

  peterstieg.com
  ├── no tracking
  ├── no cookies
  └── no framework

  >_ {MOTTO}
-->"""
```

- A triple-quoted f-string: it may span lines, and `{MOTTO}` is the only replacement field.
- The content is an HTML comment (`<!-- … -->`): invisible on the page, visible to anyone who opens the page source. `head()` places it between `<!doctype html>` and `<html>`.
- The comment text must never contain `-->` – that would end the comment early and print the rest on the page.
- Pitfall: the comment comes before `<meta charset="utf-8">`. Browsers look for the charset declaration only in the first 1024 bytes of the file; it currently sits at byte 232. Let the comment grow by several hundred bytes and the browser may have to guess the encoding – umlauts and the tree characters break.
- `dots()` deliberately leaves this comment alone (section 24).

---

## 10 · THEME_BOOT

```python
# Runs before the stylesheet: marks JS as available and applies a stored theme without a flash.
THEME_BOOT = ("<script>(function(){document.documentElement.classList.add('js');"
              "try{var t=localStorage.getItem('theme');"
              "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}})()</script>")
```

The Python side:

- Three string literals side by side inside parentheses. Python joins adjacent literals into one string at compile time – a way to wrap a long one-liner without `+` and without adding line breaks to the output. The same trick builds the SVG constants and the return value of `theme_switch()`.
- The JavaScript uses single quotes, the Python literals double quotes, so neither needs escaping. If you add JavaScript containing double quotes, escape them (`\"`) or switch the Python delimiters.

The JavaScript, statement by statement:

- `(function(){ … })()` – an IIFE ("immediately invoked function expression"): the code is wrapped in an anonymous function that is called right away. The point is scope. A `var` at the top level of a script becomes a global (`window.t`) that any other script on the page could read or overwrite; inside the function, `t` is local and disappears when the function returns. The outer parentheses make the parser read `function(){…}` as an expression, so the trailing `()` can call it.
- `document.documentElement.classList.add('js')` – adds the class `js` to `<html>`. The CSS uses it to show JavaScript-only controls only when JavaScript actually runs: `html:not(.js) .themes { display: none; }` hides the theme buttons otherwise.
- `try{ … }catch(e){}` – reading `localStorage` throws in some privacy modes or when site data is blocked. The empty `catch` makes the page fall back to the system theme instead of stopping the script. (This `e` is JavaScript and has nothing to do with Python's `e`.)
- `var t=localStorage.getItem('theme')` – the visitor's earlier choice, saved by `site.js` when a theme button is clicked. Local to the IIFE.
- `if(t==='light'||t==='dark')…setAttribute('data-theme',t)` – a whitelist: only the two known values reach the attribute. The CSS switches its color variables on `:root[data-theme="dark"]` and `:root:not([data-theme="light"])`.

Why it must run inline, in the head, before the stylesheet:

- Inline: no extra file to download; it runs the moment the parser reaches it.
- In the head: the attribute is set before anything is painted. If this logic lived only in `site.js` – loaded with `defer`, so it runs after the whole document is parsed – the page would first render in the system theme and then switch: a visible flash.
- Before the `<link rel="stylesheet">`: a regular script that comes after a stylesheet still downloading has to wait until that stylesheet has loaded, because the script might read computed styles. Placed first, it runs immediately and does not wait for the CSS.
- `site.js` repeats both steps (adds `js`, applies a stored theme if none is set yet). Redundant but harmless – a safety net.

---

## 11 · SVG icons

```python
# The arrow is not part of Atkinson Hyperlegible, so it is drawn.
ARROW_SVG = ('<svg viewBox="0 0 16 10" aria-hidden="true" focusable="false">'
             '<path d="M1 5h13.5M10 1.2 14 5l-4 3.8"/></svg>')
SUN_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="3"/>'
           '<path d="M8 1v1.6M8 13.4V15M1 8h1.6M13.4 8H15M3.05 3.05l1.13 1.13M11.82 11.82l1.13 1.13'
           'M3.05 12.95l1.13-1.13M11.82 4.18l1.13-1.13"/></svg>')
UP_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
          '<path d="M8 13.5V2.8M3.4 7.2 8 2.6l4.6 4.6"/></svg>')
MOON_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            '<path d="M13.6 10.2A6 6 0 0 1 5.8 2.4a6 6 0 1 0 7.8 7.8z"/></svg>')
```

- Inline SVG as strings, pasted straight into the HTML: no image requests, and the icons can take the text color.
- Why draw the arrow: the site font, Atkinson Hyperlegible, has no → glyph. The browser would borrow it from a fallback font with a different weight and baseline. Sun, moon and up-arrow have no font equivalent anyway.
- `viewBox="0 0 16 10"` – the internal coordinate system (16 × 10 units). The real size comes from CSS (`.arr` is 0.95em × 0.62em), so the icon scales with the text.
- `<path d="…">` – drawing commands. In the arrow: `M1 5` moves the pen to (1, 5), `h13.5` draws a horizontal line 13.5 units to the right (the shaft), `M10 1.2` jumps to the top of the head, `14 5` draws to the tip (coordinate pairs after an `M` count as line commands), `l-4 3.8` draws relative to the tip down to the bottom of the head. Uppercase = absolute coordinates, lowercase = relative.
- No `fill` or `stroke` in the markup: the CSS sets `fill: none; stroke: currentColor`, so every icon takes the current text color. Dark mode and hover colors work without a second set of icons.
- `aria-hidden="true"` – screen readers skip the drawing. The meaning comes from the parent: the arrow's `<span role="img" aria-label="to">`, the button's `aria-label`.
- `focusable="false"` – Internet Explorer and old Edge put inline SVGs into the keyboard tab order. This switches that off; modern browsers ignore it.

---

## 12 · sid and num

```python
def sid(c, key):
    return c.get("ids", {}).get(key, key)


def num(key):
    """Section number for headings and menu: '01'–'07', '' for sections outside NUMBERED."""
    return f"{NUMBERED.index(key) + 1:02d}" if key in NUMBERED else ""
```

- "Section id": turns an internal section key into the anchor used in the HTML.
- `dict.get(k, default)` never raises; it returns `default` when `k` is missing.
- First `.get`: the `ids` dict, or an empty dict when the language has none (English).
- Second `.get`: the localized ID, or the key itself as fallback.
- Result: English → `"experience"`, German → `"stationen"`. German visitors get German anchors (`/de/#stationen`).
- Pitfall: `nav` holds its own copy of these IDs. Rename an ID in `ids` without changing `nav` and the header link points to an anchor that no longer exists. No error – the link just stops scrolling.

`num` gives a section its number. Headings and menu both call it, so the two can never disagree.

- `NUMBERED.index(key) + 1` – the position in the list, counted from 1.
- `:02d` – a format spec: an integer (`d`), at least two digits wide, padded with zeros (`0`). 1 becomes `01`.
- `if key in NUMBERED else ""` – Sources (`notes`) is not in the list and gets an empty string. Without the check, `index` would raise a `ValueError`.

---

## 13 · t – escape, arrows, italics

```python
def t(c, text):
    """Escape, draw arrows, set *words* in italics (words cited as words, as in a dictionary)."""
    html = e(text).replace("→", f'<span class="arr" role="img" aria-label="{e(c["arrow"])}">{ARROW_SVG}</span>')
    lang = ' lang="en"' if c["lang"] != "en" else ""
    return re.sub(r"\*([^*]+)\*", rf"<i{lang}>\1</i>", html)
```

- `t` for "text": the function for strings that may contain markers.
- First line, part one: `e(text)` escapes the copy. Escaping first and inserting markup second is the central pattern of the whole file. The reverse order would escape your own `<span>` into visible `&lt;span&gt;`. `e()` leaves `→` and `*` untouched, so the markers survive.
- First line, part two: `.replace("→", …)` swaps every arrow for a `<span>` holding the SVG. `role="img"` plus `aria-label` makes a screen reader say "€6k to €240k".
  - Nested quotes: the f-string is delimited by single quotes, so `c["arrow"]` inside it uses double quotes. Before Python 3.12, an expression inside an f-string could not reuse the outer quote character. The file alternates quote types throughout and runs unchanged on Python 3.11.
  - Even the short label goes through `e()`: it ends up inside an attribute, where a stray `"` would end the attribute early.
- Second line: a conditional expression – `A if condition else B`. On non-English pages the italic words get `lang="en"`, because they are English words ("marketer", "tinkerer") and screen readers should pronounce them as such.
- Third line: `re.sub(pattern, replacement, string)` replaces every match.
  - Pattern `r"\*([^*]+)\*"`: `\*` is a literal asterisk (escaped, because `*` alone means "repeat"); `([^*]+)` captures one or more characters that are not asterisks as group 1; `\*` closes. Because `[^*]` cannot cross an asterisk, `*a* and *b*` yields two matches, not one long one.
  - Replacement `rf"<i{lang}>\1</i>"`: the `f` inserts `lang` now; the `r` (raw) keeps `\1` as backslash plus one, which `re` reads as "group 1". Without `r`, Python would turn `\1` into the invisible control character `chr(1)`.
- Pitfall: any two asterisks in a string passed to `t()` become italics. A single asterisk is fine.

---

## 14 · head

```python
def head(c, title, desc, canonical, alternates=True, root=None):
    r = c["root"] if root is None else root
    alt = ""
    if alternates:
        alt = "".join(f'<link rel="alternate" hreflang="{code}" href="{URL}{slug}">\n' for code, _, _, _, slug in LANGS)
        alt += f'<link rel="alternate" hreflang="x-default" href="{URL}">\n'
        alt += "".join(f'<meta property="og:locale:alternate" content="{CONTENT[code]["locale"]}">\n'
                       for code, *_ in LANGS if code != c["lang"])
    return f"""<!doctype html>
{SOURCE_NOTE}
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{THEME_BOOT}
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="{NAME}">
<link rel="canonical" href="{canonical}">
{alt}<meta name="theme-color" content="#F7F6F3" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#181A1C" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="profile">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{URL}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{NAME} – {TAGLINE} – {CLAIM}">
<meta property="og:locale" content="{c['locale']}">
<meta property="profile:first_name" content="Peter">
<meta property="profile:last_name" content="Stieg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
<link rel="preload" href="{r}assets/fonts/atkinson-hyperlegible-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/site.css">
"""
```

Signature and setup:

- `alternates=True` – the two main pages list their language versions; legal and 404 pages pass `False`.
- `root=None` – `None` means "not given". The default could not be `""`, because `""` is a real root value (the English page). `r = c["root"] if root is None else root` takes the caller's value only when one was passed.
- `alt = ""` – stays empty when `alternates` is false.

The alternates block:

- `"".join(f'…' for code, _, _, _, slug in LANGS)` – a generator expression inside `join()`. It produces one `<link>` per language, one at a time; `"".join` glues them with no separator. `_` is the conventional name for values you do not need.
- `hreflang` links tell search engines "this page exists in English at …, in German at …". Every language version lists all versions, itself included.
- `x-default` – the version for visitors whose language matches none of the listed ones: the English root.
- `og:locale:alternate` – the other languages' locales for social platforms. `for code, *_ in LANGS` is star unpacking: the first value goes into `code`, the rest into a throwaway list. `if code != c["lang"]` filters out the current language. `CONTENT[code]["locale"]` reads from the *other* language's dict.
- `+=` on strings creates a new string each time. Fine for three operations; for many pieces, collect in a list and join once (as `page()` does).

The returned document head, top to bottom:

- `<!doctype html>` – switches browsers into standards mode. It must come first.
- `{SOURCE_NOTE}` – the greeting comment.
- `<html lang="{c['lang']}">` – the page language: screen-reader pronunciation, hyphenation, translation offers, spell-check. Single quotes inside a triple-double-quoted f-string – no conflict.
- `<meta charset="utf-8">` – how to decode the bytes; must sit within the first 1024 bytes (section 9).
- `viewport` – on phones, lay the page out at device width instead of a zoomed-out desktop width.
- `{THEME_BOOT}` – the theme script, before the stylesheet (section 10).
- `<title>{e(title)}</title>` – tab title and search-result headline, escaped.
- `description` – often shown as the snippet in search results. Escaped, because it sits inside an attribute.
- `author` – the author's name.
- `canonical` – the preferred URL of this page. It merges duplicates such as `/de/` and `/de/index.html` into one address for search engines.
- `{alt}<meta name="theme-color"…` – `alt` either ends with `\n` or is empty, so the output never gets a blank line.
- `theme-color` twice, with `media` – the browser UI color (for example the address bar on phones) for a light and a dark system setting. `site.js` overwrites both when the visitor picks a theme by hand. The two hex values also exist in `site.css` and `site.js` – change all three together.
- `og:*` – Open Graph: what LinkedIn, Slack, WhatsApp and others show when the link is shared. `og:image` must be an absolute URL, because crawlers do not resolve relative paths. `width` and `height` let the platform lay out the preview before the image arrives.
- `profile:first_name`, `profile:last_name` – Open Graph fields for the `profile` type.
- `twitter:card` – asks X for a large image preview; title, description and image fall back to the `og:*` values.
- Icons with `{r}` – relative to where the page lives.
- `rel="preload"` for two font files – starts the download immediately instead of after the CSS has been parsed and the fonts discovered there. `crossorigin` is required: fonts are always fetched in CORS mode, and a preload without it does not match the real request, so the font would download twice. The italic file is not preloaded; it is only needed for a few words.
- `<link rel="stylesheet">` – the CSS, deliberately after `THEME_BOOT`.
- No `</head>` at the end. Callers add more first (JSON-LD, `robots` meta) and close the head themselves. If you write a new page function, you must close it.

---

## 15 · lang_switch

```python
def lang_switch(c):
    """EN · DE – the current language is marked, the other links to the same page in that language."""
    r = c["root"]
    items = []
    for code, label, name, path, _ in LANGS:
        if code == c["lang"]:
            items.append(f'<span aria-current="page" title="{name}">{label}</span>')
        else:
            items.append(f'<a href="{r}{path}" hreflang="{code}" lang="{code}" title="{name}">{label}</a>')
    return f'<span class="langs" role="group" aria-label="{e(c["aria_lang"])}">{"".join(items)}</span>'
```

- The docstring names the two current languages. The output itself follows `LANGS`, so a third entry there would appear in the switch automatically.
- `items = []` plus `append` – an explicit loop, because each language takes one of two shapes.
- `for code, label, name, path, _ in LANGS` – full unpacking; the slug is not needed here.
- Current language: a `<span>`, not a link – a link to the page you are on is noise. `aria-current="page"` tells screen readers "this is the current one"; the CSS rule `.langs [aria-current]` sets it in bold.
- Other languages: `<a href="{r}{path}">` – from the English page `de/index.html`, from the German page `../index.html`. `hreflang` states the language of the target page; `lang` the language of the link text itself; `title` shows the full name on hover.
- The wrapper: `role="group"` with `aria-label` lets a screen reader announce "Language, group" before the links.
- `{"".join(items)}` – an expression inside the f-string. Double quotes inside, single quotes outside.
- No separator characters in the HTML: the spacing comes from CSS padding.

---

## 16 · theme_switch

```python
def theme_switch(c):
    group, light, dark = c["theme"]
    return (f'<span class="themes" role="group" aria-label="{e(group)}">'
            f'<button type="button" data-theme-set="light" aria-pressed="false" aria-label="{e(light)}" title="{e(light)}">{SUN_SVG}</button>'
            f'<button type="button" data-theme-set="dark" aria-pressed="false" aria-label="{e(dark)}" title="{e(dark)}">{MOON_SVG}</button>'
            f'</span>')
```

- `group, light, dark = c["theme"]` – tuple unpacking: three names from a 3-tuple in one line. A tuple of the wrong length raises `ValueError`.
- Four adjacent f-strings in parentheses become one string (section 10).
- `type="button"` – a `<button>` without a type acts as "submit" inside a form. Setting the type is the safe habit.
- `data-theme-set="light"` – a custom data attribute. `site.js` finds the buttons with `[data-theme-set]` and reads `b.dataset.themeSet`: in `dataset`, dashed attribute names become camelCase.
- `aria-pressed="false"` – marks the button as a toggle. `site.js` sets `"true"` on the active theme; CSS draws that icon with a thicker stroke.
- `aria-label` and `title` – the button contains only an icon, so it needs a spoken name and a tooltip.
- Without JavaScript the buttons cannot work, so CSS hides them (`html:not(.js) .themes`).

---

## 17 · topbar

```python
def topbar(c, sections=True, langs=True):
    r = c["root"]
    keys = {sid(c, k): k for k in NUMBERED}          # localized id → section key, for the number
    # number as on the heading; data-label: CSS reserves the bold width, so marking the current section does not shift the menu
    links = "".join(f'<a class="sect" href="#{i}"><span class="no" aria-hidden="true">{num(keys[i])}</span> '
                    f'<span class="label" data-label="{e(t)}">{e(t)}</span></a>' for i, t in c["nav"]) if sections else ""
    switch = lang_switch(c) if langs else ""
    return f"""<a class="skip" href="#main">{e(c['skip'])}</a>
<header class="top">
<div class="wrap">
<a class="home" href="{'#top' if sections else r + c['path']}"><span class="caret" aria-hidden="true">&gt;_</span><span class="name">{NAME}</span></a>
<nav class="nav" aria-label="{e(c['aria_main'])}">{links}{switch}{theme_switch(c)}</nav>
</div>
</header>
"""
```

- `sections`, `langs` – switches. The main pages get section links and the language switch; legal and 404 pages pass `False` for both.
- `keys` – a dict comprehension that turns the lookup around. `nav` holds the localized ids (`"stationen"`), `num()` needs the section key (`"experience"`). So `keys` maps each id back to its key: `{"profil": "profile", "stationen": "experience", …}` on the German page; in English, id and key are the same.
- `links = "".join(…) if sections else ""` – the conditional expression wraps the whole join, so the generator only runs when `sections` is true.
  - Two f-strings in a row, without a `+` between them, are joined into one string by Python itself. That splits a long line without changing the result.
  - `for i, t in c["nav"]` – unpacks each (id, label) pair. Here `t` is a loop variable that shadows the function `t()`. It works because a generator expression has its own scope – outside it, `t()` is untouched – but it is confusing. Do not copy the pattern.
  - `href="#{i}"` – an in-page anchor.
  - `<span class="no" aria-hidden="true">{num(keys[i])}</span>` – the same number as on the section heading: "01 Profile", "03 Experience". Hidden from screen readers, so the link is still called "Profile".
  - `<span class="label" data-label="{e(t)}">` – the label in its own span, plus a copy as a data attribute. `site.js` marks the section being read in bold; the CSS uses the copy to reserve the bold width in advance (chapter 3, Navigation). The span is needed because the trick works on the label alone – the number stays regular.
- `switch = lang_switch(c) if langs else ""` – same pattern.
- The skip link comes first in the page so it is the first thing the Tab key reaches. CSS keeps it off-screen until it receives keyboard focus; it jumps to `<main id="main">`.
- `<header class="top">` and `<div class="wrap">` – the page header and a width-limiting layout container.
- The home link: `{'#top' if sections else r + c['path']}` – a full conditional expression inside a replacement field. On the main page it jumps to the hero (`#top`). On other pages it links to that language's home page: `"" + "de/index.html"` on the legal pages, `"/" + "index.html"` on the 404 page.
- `&gt;_` – the shell prompt. `>` written as an entity, and `aria-hidden` so screen readers do not read "greater than underscore". While you scroll, `site.js` moves the hero name into this logo position.
- `<nav aria-label=…>` – a named navigation landmark. The name matters because the page has two navs (header and footer).

---

## 18 · footer

```python
def footer(c):
    r = c["root"]
    return f"""<footer class="foot">
<div class="wrap">
<p lang="en">Admiring complexity. Loving simplicity.</p>
<nav aria-label="{e(c['aria_legal'])}">
<a href="{r}impressum.html" hreflang="de">{e(c['imprint'])}</a>
<a href="{r}datenschutz.html" hreflang="de">{e(c['privacy'])}</a>
<span>© {date.today().year} {NAME}</span>
</nav>
</div>
</footer>
"""
```

- `<p lang="en">` – the line stays English on the German page; the attribute tells screen readers.
- The legal links get `{r}` (they live at the site root) and `hreflang="de"` – the legal pages exist only in German, and the link says so in advance.
- `© {date.today().year}` – evaluated when you build, not when someone visits. The year changes only when you rebuild; a page built in December still shows the old year in January until the next build.

---

## 19 · jsonld

```python
def jsonld(c):
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": NAME,
        "url": URL,
        "image": URL + "og-image.png",
        "jobTitle": c["jobtitle"],
        "description": c["desc"],
        "address": {"@type": "PostalAddress", "addressLocality": "Leipzig", "addressCountry": "DE"},
        "email": "mailto:" + EMAIL,
        "sameAs": [LINKEDIN, GITHUB],
        "knowsLanguage": ["de", "en", "it", "es", "fr"],
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Università degli Studi di Trento"}],
        "hasCredential": [
            {"@type": "EducationalOccupationalCredential", "name": n["title"], "url": n["verify"],
             "recognizedBy": {"@type": "Organization", "name": "Université Paris 1 Panthéon-Sorbonne"}}
            for n in NOTES.values()
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"
```

- JSON-LD ("JSON for Linked Data") – machine-readable facts about the page's subject, using the schema.org vocabulary. Search engines read it; visitors never see it.
- The Python dict mirrors the JSON structure one to one. `"@context"` names the vocabulary, `"@type"` the kind of thing described – a `Person`.
- `jobTitle` and `description` come from `c`, so each language version describes the person in its own language.
- `"address"` – a nested object with its own `@type`. City and country only.
- `"sameAs"` – other profiles of the same person; this ties the site to LinkedIn and GitHub.
- `"hasCredential"` – a list comprehension: `[{…} for n in NOTES.values()]` builds one credential object per footnote. Dicts keep insertion order (guaranteed since Python 3.7), so the order is always Data Scientist, then MLOps Engineer.
- `json.dumps(data, ensure_ascii=False)` turns the dict into JSON text. The default (`ensure_ascii=True`) would write `"Università"`; `False` keeps `"Università"`. Both are valid JSON; the second is shorter and readable, and safe because the file is written as UTF-8.
- Why no `e()` here: the content of a `<script>` element is raw text. The browser does not decode entities inside it, so `&amp;` would land literally in the JSON.
- Pitfall: `json.dumps` does not protect against the sequence `</script>`. A string containing it would close the script element early. All values here are your own constants, so it cannot happen today. If outside data is ever fed in, replace `"</"` with `"<\/"` in the output.

---

## 20 · section and tree

```python
def section(c, key, title_html, body, cls="body"):
    i = sid(c, key)
    no = f'<span class="no" aria-hidden="true">{num(key)}</span> ' if num(key) else ""
    return f"""<section class="sec" id="{i}" aria-labelledby="h-{i}">
<h2 id="h-{i}">{no}{title_html}</h2>
<div class="{cls}">
{body}</div>
</section>
"""
```

- The wrapper for every content section of the main page.
- `cls="body"` – a default parameter: used when the caller passes nothing. No caller currently passes another value.
- `i = sid(c, key)` – the localized anchor.
- `no` – the number span from `num(key)` (section 12), or an empty string for Sources. An empty string counts as false, so `if num(key)` is enough.
  - `aria-hidden="true"` – screen readers skip the number and announce "Profile", not "zero one Profile". The number is a visual signpost; the order of headings already carries the structure.
  - The space after `</span>` sits outside the span, so the plain text of the heading still reads "01 Profile" for search engines and copy-paste.
- `aria-labelledby="h-{i}"` points at the `<h2 id="h-{i}">`: the heading becomes the section's name, and a named `<section>` is exposed as a landmark that screen-reader users can jump between.
- `title_html` – the name says it: raw HTML, inserted unescaped. Callers pass `e(s["profile"])` and so on; only P⁴ passes markup (`'P<sup>4</sup>'`). Pitfall: pass plain copy here without `e()` and the first `&` breaks the markup.
- `{body}</div>` – every caller's body ends with `\n`, so `</div>` lands on its own line.

```python
def tree(c, rows):
    lang = ' lang="en"' if c["lang"] != "en" else ""
    items = "".join(f'<li><span class="k"{lang}>{e(k)}</span> {t(c, v)}</li>' for k, v in rows)
    return f'<ul class="tree">{items}</ul>'
```

- Renders a role's `tree` list (the #JobAlert format) as `<ul class="tree">`.
- `lang` – labels such as "Scope" stay English and are marked as such on the German page.
- `for k, v in rows` – each row is a (label, text) pair, unpacked in the generator.
- The label goes through `e()`, the text through `t()` – so arrows and italics work in the text.
- No colon after the label in the HTML: the CSS adds it (`.tree .k::after { content: ":"; }`) and draws the branch lines with `::before` and `::after`. The content stays clean data; the presentation lives in CSS.

---

## 21 · page – one complete language version

The largest function. It collects HTML fragments in the list `out` and joins them once at the end. Appending to a list and joining once is the standard Python idiom for building long strings: strings are immutable, and repeated `+=` may copy the growing string over and over.

### Setup and footnote numbering

```python
def page(c):
    s, L = c["sec"], c["lang"]
    slug = next(sl for code, _, _, _, sl in LANGS if code == L)
    en_attr = ' lang="en"' if L != "en" else ""
    order = []  # footnotes, numbered in order of first appearance

    def fn(m):
        key = m.group(1)
        if key not in order:
            order.append(key)
        n = order.index(key) + 1
        return f'<sup class="fnref"><a href="#fn-{key}" id="ref-{key}" aria-describedby="h-{sid(c, "notes")}">{n}</a></sup>'
```

- `s, L = c["sec"], c["lang"]` – two assignments in one line (the right side is a tuple, unpacked into two names). `s` holds the section headings, `L` the language code.
- `slug = next(…)` – the generator yields the slug of every `LANGS` entry whose code matches; `next()` takes the first value and stops. Shorter than a loop with `break`. If nothing matches, `next()` raises `StopIteration` – a confusing error; `next(gen, "")` would return a default instead.
- `en_attr` – the same `lang="en"` pattern as in `t()` and `tree()`.
- `order = []` – footnote keys in the order they first appear.
- `def fn(m):` – a function defined inside a function: a closure. It can use `order` and `c` from `page()`'s scope. It changes `order` only with `append`, which mutates the list – that needs no `nonlocal`. Only rebinding the name (`order = …`) would.
  - `m` is a match object from `re.sub`; `m.group(1)` is the text between `[[` and `]]`.
  - The first time a key is seen it is appended; its number is its position plus one (lists count from 0, footnotes from 1).
  - The returned `<sup>` links to `#fn-{key}` in the Sources list, carries `id="ref-{key}"` as the target of the way back, and `aria-describedby` points at the Sources heading.
  - Pitfall: using the same marker twice on one page produces two elements with `id="ref-ds"`. Duplicate IDs are invalid, and the back link only finds the first. One reference per key.

### Head, header and page frame

```python
    out = [head(c, TITLE, c["desc"], URL + slug), jsonld(c), "</head>\n<body>\n", topbar(c)]
    out.append(f'<a class="to-top" href="#top" aria-label="{e(c["to_top"])}" title="{e(c["to_top"])}">{UP_SVG}</a>\n')
    out.append('<div class="minimap" aria-hidden="true"></div>\n<main id="main">\n<div class="wrap">\n')
```

- The list starts with four parts: the head (canonical URL = `URL + slug`, for example `https://peterstieg.com/de/`), the JSON-LD block, the closing `</head>` with the opening `<body>`, and the header.
- The back-to-top link: an icon with label and tooltip. CSS shows it only once the name has docked into the header – or always, without JavaScript.
- `<div class="minimap">` – empty; `site.js` fills it with bars drawn from the page on wide screens. `aria-hidden` because it is a purely visual navigation aid.
- `<main id="main">` – the main landmark and the target of the skip link.

### Hero

```python
    # hero – same order as the LinkedIn banner
    out.append(f"""<section class="hero" id="top">
<h1>{NAME}</h1>
<p class="tagline" lang="en">{TAGLINE.replace("Performance Marketing", "Performance&nbsp;Marketing").replace("Data Science", "Data&nbsp;Science")}</p>
<p class="claim" lang="en">{CLAIM}</p>
<p class="prompt" lang="en"><span class="caret" aria-hidden="true">&gt;_</span><span class="cmd" aria-hidden="true">{MOTTO}</span><span class="sr-only">{MOTTO}</span><span class="cursor" aria-hidden="true"></span></p>
</section>
""")
```

- `id="top"` – target of the home link and the back-to-top link.
- No `aria-label` on the section: the `<h1>` inside already names the block, and a label on top would make screen readers announce the name twice.
- `<h1>{NAME}</h1>` – the only `<h1>` on the page.
- The tagline: two chained `.replace()` calls inside the replacement field put `&nbsp;` inside each phrase, so "Performance Marketing" and "Data Science" never break in the middle; the line can only break at the middle dot. Pitfall: the replace matches the exact wording. Reword `TAGLINE` and the replace silently stops matching.
- Double quotes inside a triple-double-quoted f-string are fine on older Pythons too: a single `"` does not end a `"""` string.
- Tagline, claim and prompt are marked `lang="en"`, because they stay English on every page (rule 5).
- The prompt has four parts: the caret (hidden from screen readers), `.cmd` (hidden from screen readers; `site.js` empties it and types the motto letter by letter, unless the visitor's system asks for reduced motion), `.sr-only` (a visually hidden copy that screen readers read in full, instead of a half-typed string), `.cursor` (blinks via CSS). Without JavaScript the full motto simply stays in `.cmd`.

### Profile

```python
    # profile – a dictionary entry for his own word, in each language's dictionary style
    d = c["entry"]
    hw = re.sub(r"([·|])", r'<span class="syl">\1</span>', e(d["hw"]))
    entry = f"""<div class="entry">
<p class="hw"><dfn>{hw}</dfn> <span class="pos">{e(d['pos'])}</span> <span class="ety">{t(c, d['ety'])}</span></p>
<p class="def">{e(d['def'])}</p>
</div>
"""
    led = "".join(f"<div><dt>{t(c, a)}</dt><dd>{e(b)}</dd></div>\n" for a, b in c["ledger"])
    out.append(section(c, "profile", e(s["profile"]),
                       f'{entry}<p>{e(c["profile"])}</p>\n<dl class="ledger" aria-label="{e(c["ledger_label"])}">\n{led}</dl>\n'))
```

- `d = c["entry"]` – a short local name.
- `hw = re.sub(r"([·|])", …, e(d["hw"]))` – escape first, then wrap each syllable separator in a span so CSS can mute it.
  - `[·|]` is a character class: one character that is either the middle dot (English dictionary style: mar·ke·tin·ker·er) or the pipe (Duden style: Mar|ke|tin|ke|rer). Inside square brackets `|` is a literal character, not "or".
  - `( )` captures the separator as group 1; `\1` in the raw replacement string puts it back inside the span.
- `entry` – the dictionary entry. `<dfn>` marks the term being defined – the right element for a headword. `pos` and `def` go through `e()`, `ety` through `t()` for its italics.
- `led` – the results list as a description list: `<dt>` holds the figure (through `t()` for the arrows; "> 2×" becomes `&gt; 2×`), `<dd>` the context. A `<div>` around each `dt`/`dd` pair is valid inside `<dl>` and gives CSS one box per row.
- `section(…)` – heading escaped, body = entry + profile paragraph + results list with its own `aria-label`.

### P⁴

```python
    # P⁴ – P as in Peter
    p4 = []
    for i, (p, txt) in enumerate(zip(P4, c["fields"])):
        tail = f' <strong lang="en">{e(P4_TAIL[i])}</strong>' if i in P4_TAIL else ""
        p4.append(f'<div><h3{en_attr}>{e(p)}</h3><p>{e(txt)}{tail}</p></div>\n')
    out.append(section(c, "fields", 'P<sup>4</sup>',
                       f'<p class="intro">{e(c["p4_intro"])}</p>\n<div class="fields">\n{"".join(p4)}</div>\n'))
```

- `zip(P4, c["fields"])` pairs each heading with its text; `enumerate(…)` adds a counter. `for i, (p, txt) in …` unpacks both levels at once: the counter, then the pair.
- `if i in P4_TAIL` – `in` on a dict checks its keys. Only index 3 (People) gets the tail, marked English.
- `<h3{en_attr}>` – the P-words are English on both pages.
- The section key is `"fields"`, but `sec` has no `"fields"` heading: the title is the fixed markup `P<sup>4</sup>` in every language. The German anchor is `p-wie-peter`.

### Experience

```python
    # experience – each role as a #JobAlert-style tree
    roles = []
    for ro in c["roles"]:
        place = f'&nbsp;<span class="place">· {e(ro["place"])}</span>' if ro.get("place") else ""
        ctx = f'<p class="ctx">{e(ro["ctx"])}</p>' if ro.get("ctx") else ""
        roles.append(f"""<li class="role">
<p class="when">{e(ro['when'])}</p>
<div>
<h3>{e(ro['title'])}</h3>
<p class="org">{e(ro['org'])}{place}</p>
{ctx}{tree(c, ro['tree'])}
</div>
</li>
""")
    out.append(section(c, "experience", e(s["experience"]), f'<ol class="roles" reversed>\n{"".join(roles)}</ol>\n'))
```

- `ro.get("place")` – optional field: returns `None` when the key is missing and `""` when it is empty (Rapidobject). Both are falsy, so no place span appears.
- `&nbsp;` before the span – the same job as `dots()`: "· Laucha" must not start a new line. `dots()` cannot do it here, because it only matches the plain sequence ` · `, and here a `<span>` tag sits between the space and the dot. So the place line brings its own non-breaking space.
- `ctx` – the optional context line, same pattern.
- Required fields (`when`, `title`, `org`, `tree`) use `ro['…']`: a missing key raises `KeyError`. That is intended – a role without a title should fail loudly.
- `{ctx}{tree(c, ro['tree'])}` – context line and tree directly after each other.
- `<ol class="roles" reversed>` – an ordered list, because sequence matters; `reversed` makes the numbering count down, so the newest role at the top carries the highest number. It is a boolean attribute: present means true.

### Projects

```python
    # projects
    groups = []
    for gt, items in c["groups"]:
        lis = []
        for name, text, stack, link in items:
            ln = f' · <a href="{link}">GitHub</a>' if link else ""
            lis.append(f'<li><h4>{e(name)}</h4><p>{e(text)}</p><p class="stack">{e(stack)}{ln}</p></li>\n')
        groups.append(f'<div class="group"><h3>{e(gt)}</h3>\n<ul class="projects">\n{"".join(lis)}</ul></div>\n')
    out.append(section(c, "projects", e(s["projects"]),
                       f'<p class="intro"><strong lang="en">{e(PROJECTS_LEAD)}</strong></p>\n' + "".join(groups)))
```

- Two nested loops: groups (`gt` = group title), then projects within a group.
- `for name, text, stack, link in items` – each project is a 4-tuple. A tuple with three or five values raises `ValueError`.
- `ln` – the GitHub link only when `link` is not `None`; its ` · ` separator gets glued by `dots()` later.
- The section body is an f-string concatenated with a join result via `+` – both are plain strings.
- `name` is a local variable here; it does not clash with the constant `NAME` (Python is case-sensitive).

### Approach

```python
    # approach – three of a kind: X, not Y
    pr = "".join(f'<li><p><strong lang="en">{e(a)}</strong> {e(b)}</p></li>\n' for a, b in zip(SLOGANS, c["approach"]))
    out.append(section(c, "approach", e(s["approach"]), f'<ul class="principles">\n{pr}</ul>\n'))
```

- `zip(SLOGANS, c["approach"])` – English slogan plus localized sentence, paired by position.
- The slogan is marked `lang="en"` on both pages.

### Education – where the footnotes are created

```python
    # education – certificates carry footnotes
    fa = []
    for k, v, sub in c["facts"]:
        subtxt = f'<br><span class="muted">{e(sub)}</span>' if sub else ""
        val = re.sub(r"\[\[(\w+)\]\]", fn, e(v))
        fa.append(f"<div><dt>{e(k)}</dt><dd>{val}{subtxt}</dd></div>\n")
    out.append(section(c, "education", e(s["education"]), f'<dl class="facts">\n{"".join(fa)}</dl>\n'))
```

- `for k, v, sub in c["facts"]` – each fact is a 3-tuple; an empty `sub` means "no second line".
- `re.sub(r"\[\[(\w+)\]\]", fn, e(v))`:
  - Pattern: `\[\[` two literal brackets (escaped, because `[` normally opens a character class), `(\w+)` the key – letters, digits, underscore – as group 1, `\]\]` closing brackets.
  - The replacement is a function, not a string. `re.sub` calls `fn(match)` for every match, left to right, and inserts whatever it returns. That is what makes the numbering follow the order of appearance: the first marker processed gets 1.
  - Escape first again: `e()` does not touch `[` or `]`, so the markers survive, and `fn`'s HTML is inserted after escaping.
- Pitfalls: a key with a hyphen (`[[ml-ops]]`) does not match `\w+` and stays visible as text. A key that matches but is missing from `NOTES` gets a number here and then crashes the Sources loop with `KeyError`.

### Contact

```python
    # contact – a nod to the 2016 claim: Work online | Live offline
    here, before = c["offline"]
    contact = f"""<p class="hello">Hallo · Hi · Ciao</p>
<dl class="reach">
<div><dt lang="en">Online</dt><dd><a class="mail" href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{LINKEDIN}" rel="me">LinkedIn</a> · <a href="{GITHUB}" rel="me">GitHub</a></dd></div>
<div><dt lang="en">Offline</dt><dd>{e(here)} <span class="muted">{e(before)}</span></dd></div>
</dl>
"""
    out.append(section(c, "contact", e(s["contact"]), contact))
```

- `here, before = c["offline"]` – unpacks the 2-tuple.
- "Hallo · Hi · Ciao", "Online" and "Offline" are the same in both languages; the labels are marked `lang="en"`.
- `mailto:` – opens the visitor's mail program.
- `rel="me"` – declares "this profile is also me". Some platforms (Mastodon, for example) use it to verify identity in both directions.

### Sources

```python
    # sources – footnotes in order of appearance, each with a way back
    nl = c["notes"]
    notes = []
    for key in order:
        n = NOTES[key]
        notes.append(f'<li id="fn-{key}"><a class="back" href="#ref-{key}" aria-label="{e(nl["back"])}">^</a> '
                     f'{e(n["title"])} · {e(nl["issued"])} {e(n["date"][L])} · '
                     f'<a href="{n["verify"]}">{e(nl["verify"])}</a> · <a href="{n["course"]}" hreflang="en">{e(nl["course"])}</a></li>\n')
    out.append(section(c, "notes", e(s["notes"]), f'<ol class="notes">\n{"".join(notes)}</ol>\n'))
```

- This loop runs after the education section, so `order` is already filled. The order of the `out.append` calls is load-bearing: build Sources before Education and the list comes out empty.
- Only footnotes that were actually referenced appear, in the order they were referenced. `<ol>` numbers its items 1, 2, … automatically – matching the numbers `fn()` produced, because both follow `order`.
- `id="fn-{key}"` – the target of the superscript link. `<a class="back" href="#ref-{key}">^</a>` – the way back, with a spoken label.
- `n["date"][L]` – the date string for the current language.
- `hreflang="en"` on the course link – the course page is in English.
- Three adjacent f-strings inside the `append(…)` parentheses form one string.

### Closing

```python
    out.append("</div>\n</main>\n")
    out.append(footer(c))
    out.append(f'<script src="{c["root"]}assets/site.js" defer></script>\n</body>\n</html>\n')
    return "".join(out)
```

- Closes the `wrap` div and `<main>`, adds the footer.
- `defer` – the script downloads while the HTML is parsed and runs only after parsing is complete. By then every element exists, so `site.js` can query all of them.
- `"".join(out)` – one string for the whole page.

---

## 22 · Legal pages

```python
# ---------- legal pages (German) ----------

ADDRESS = """Peter Stieg<br>
…<br>
… Leipzig<br>
Deutschland"""

IMPRESSUM = f"""<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
<address>{ADDRESS}</address>
<h2>Kontakt</h2>
<p>E-Mail: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>Peter Stieg, Anschrift wie oben.</p>
"""

DATENSCHUTZ = f"""<h1>Datenschutzerklärung</h1>
<p class="muted">Stand: Oktober 2026</p>
<h2>Verantwortlicher</h2>
<address>{ADDRESS}<br>E-Mail: <a href="mailto:{EMAIL}">{EMAIL}</a></address>
<h2>Kurz gesagt</h2>
<p>Diese Website setzt keine Cookies, nutzt keine Analyse- oder Tracking-Werkzeuge und lädt keine Inhalte von Drittanbietern. Schriften, Skripte und Grafiken liegen auf demselben Server wie die Seite selbst. Nur wenn Sie selbst zwischen hellem und dunklem Design wechseln, merkt sich Ihr Browser diese Auswahl (siehe unten).</p>
<h2>Hosting und Server-Logfiles</h2>
<p>Beim Aufruf der Website verarbeitet der Hosting-Anbieter automatisch Daten, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit des Zugriffs, aufgerufene Seite, Referrer-URL sowie Browser und Betriebssystem. Das ist technisch erforderlich, um die Seite auszuliefern und ihre Sicherheit zu gewährleisten. Rechtsgrundlage ist das berechtigte Interesse nach Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Hosting-Anbieter: … Mit ihm besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Speicherdauer der Logfiles richtet sich nach seinen Vorgaben.</p>
<h2>Helles und dunkles Design</h2>
<p>Ohne Ihr Zutun folgt die Website der Einstellung Ihres Geräts. Wählen Sie das Design über den Schalter oben selbst, speichert Ihr Browser diese Auswahl lokal (Local Storage), damit sie beim nächsten Besuch erhalten bleibt. Der Eintrag bleibt auf Ihrem Gerät und wird nicht an den Server übertragen. Rechtsgrundlage ist § 25 Abs. 2 Nr. 2 TDDDG. Sie können den Eintrag jederzeit über die Einstellungen Ihres Browsers löschen.</p>
<h2>Kontakt per E-Mail</h2>
<p>Wenn Sie eine E-Mail schreiben, werden Ihre Angaben verarbeitet, um die Anfrage zu beantworten (Art. 6 Abs. 1 lit. b oder f DSGVO). Die Daten werden gelöscht, sobald sie dafür nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>
<h2>Links zu anderen Plattformen</h2>
<p>Die Seite verlinkt auf LinkedIn, GitHub, die Kursseiten von Liora und die Nachweisseiten von DataScientest. Erst wenn Sie einem dieser Links folgen, verarbeiten die jeweiligen Anbieter Daten nach ihren eigenen Datenschutzbestimmungen.</p>
<h2>Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18) und Datenübertragbarkeit (Art. 20). Einer Verarbeitung auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO können Sie widersprechen (Art. 21). Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, etwa bei der zuständigen Behörde Ihres Bundeslandes.</p>
"""
```

- The street address and the hosting provider's address are cut to `…` here; the real values are in `src/build.py`.
- `ADDRESS` – a plain triple-quoted string (no `f`), with `<br>` line breaks. The legal notice requires a full postal address (§ 5 DDG), and the privacy notice names the same person as the one responsible, so the address is defined once and used by both pages. `<address>` marks it as contact information.
- The privacy notice also names the hosting provider with its address, because the server logs are processed on its behalf (Art. 28 DSGVO). Change hosts and this line has to change too.
- Trade-off: the address in `ADDRESS` stays in the git history for good, even if you change it later. If the repository is public, so is the address – which the Impressum publishes anyway.
- `IMPRESSUM`, `DATENSCHUTZ` – f-strings that insert `ADDRESS` and `EMAIL`. They are HTML, inserted unescaped by `legal()`; a literal `&` in a new sentence must be written `&amp;`.
- `Stand: Oktober 2026` is typed by hand – update it when the text changes.
- The privacy text describes what the code does: no cookies, no tracking, fonts and scripts on the same server, `localStorage` only for the theme choice. Code and text are coupled: anything that loads third-party content (a web font service, analytics, an embedded video) requires a change to this text as well.

```python
def legal(title, body, path):
    c = dict(CONTENT["de"], root="")
    out = [head(c, f"{title} – {NAME}", f"{title} von peterstieg.com", URL + path, alternates=False),
           '<meta name="robots" content="noindex, follow">\n</head>\n<body>\n',
           topbar(c, sections=False, langs=False),
           f'<main id="main">\n<div class="wrap legal">\n<div class="body">\n{body}<p>peterstieg.com: <a href="index.html" hreflang="en">English</a> · <a href="de/index.html">Deutsch</a></p>\n</div>\n</div>\n</main>\n',
           footer(c), '<script src="assets/site.js" defer></script>\n</body>\n</html>\n']
    return "".join(out)
```

- `c = dict(CONTENT["de"], root="")` – `dict(mapping, key=value)` creates a new dict with every entry of the German dict, then overrides `root`. The legal pages sit at the site root (`/impressum.html`), while the German dict's root is `"../"` (made for `/de/`).
  - Why a copy instead of `CONTENT["de"]["root"] = ""`: changing the original would leave the German dict broken for anything that uses it afterwards.
  - It is a shallow copy: nested lists and dicts are shared with the original. `c["root"]` is safe to replace; `c["nav"].append(…)` would change `CONTENT` itself.
- The `out` list:
  - `head(…)` – title "Impressum – Peter Stieg", a short description, canonical `URL + path`, and `alternates=False`, because these pages exist only in German.
  - `robots` meta `noindex, follow` – keep the page out of search results, but follow its links. Then the head closes and the body opens.
  - `topbar(c, sections=False, langs=False)` – no section links, no language switch; the home link goes to `"" + "de/index.html"`. The theme switch stays.
  - The main block inserts `body` raw and adds a line with links to both language versions. The paths `index.html` and `de/index.html` are hard-coded relative paths – correct because the page sits at the root.
  - `footer(c)` – German labels. The script path `assets/site.js` is hard-coded too, instead of `{c["root"]}assets/site.js`; it works only because `root` is `""` here.

---

## 23 · not_found

```python
def not_found():
    """404 with a Google Ads insider joke: Dynamic Keyword Insertion, {KeyWord:Default}."""
    c = dict(CONTENT["en"], root="/")
    return "".join([
        head(c, f"404 – {NAME}", "Page not found.", URL + "404.html", alternates=False, root="/"),
        '<meta name="robots" content="noindex">\n</head>\n<body>\n',
        topbar(c, sections=False, langs=False),
        f"""<main id="main">
<div class="wrap">
<section class="lost">
<p class="code">404</p>
<h1><code class="dki">{{KeyWord:Page}}</code> not found.</h1>
<p class="claim" lang="de">Diese Seite gibt es nicht.</p>
<p class="prompt"><span class="caret" aria-hidden="true">&gt;_</span><a href="/">cd ~</a> · <a href="/de/" lang="de">Deutsch</a></p>
</section>
</div>
</main>
""",
        footer(c), '<script src="/assets/site.js" defer></script>\n</body>\n</html>\n'])
```

- `c = dict(CONTENT["en"], root="/")` – the English dict with a root-absolute prefix.
- Why `"/"`: the server delivers this page for every missing URL, at any depth – `/de/old/page` included. A relative `assets/site.css` would then resolve to `/de/old/assets/site.css` and fail. A leading slash always resolves from the domain root.
- Trade-off: opened straight from disk (`file://`), `/` means the root of your file system, so the 404 page looks unstyled locally. That is expected.
- `root="/"` is passed to `head()` as well – redundant, since `c["root"]` is already `"/"`.
- `"".join([...])` – the parts as a list literal, joined once.
- `robots` `noindex` – error pages do not belong in search results.
- `{{KeyWord:Page}}` – in an f-string, `{{` and `}}` produce literal braces. The output is `{KeyWord:Page}`: Google Ads Dynamic Keyword Insertion syntax, where the ad shows the searched keyword or, if that does not fit, the default text after the colon. Without the doubling, Python would try to evaluate `KeyWord` as a variable with the format spec `Page` and fail with `NameError`.
- `lang="de"` on the German sentence of an English page.
- `cd ~` links home (`/`), plus a link to the German version.

---

## 24 · nbsp and dots – typography after the fact

```python
def nbsp(html):
    """Keep numbers and units together: 25 %, 240.000 €, 1,7 Mio. €."""
    return (html.replace(" %", " %").replace(" €", " €")
                .replace("Mio. ", "Mio. ").replace(" Mio.", " Mio."))
```

- The second argument of each `replace` contains U+00A0 NO-BREAK SPACE, not a normal space. In most editors the two look identical, so `replace(" %", " %")` looks like a no-op. It is not – do not "tidy it up". To see the difference: `python3 -c "print(repr(open('src/build.py', encoding='utf-8').read().split('def nbsp')[1][:160]))"` shows `\xa0` where the special spaces are.
- Each `.replace()` returns a new string (strings are immutable), so the calls chain left to right. The outer parentheses allow the line break in the middle of the chain.
- Effect: "25 %" → "25 %" with a fixed space, same for "240.000 €" and "1,7 Mio. €" – the number and its unit always stay on one line.
- Order: `" €"` runs before `"Mio. "`, so in "Mio. €" the space is already replaced. `"Mio. "` covers other cases such as "Mio. Euro".
- Applied only to the German page: German style puts a space before % and €; the English copy writes "+45%" and "€1.7m" without one.
- It runs on the whole page, head included – harmless, because U+00A0 is an ordinary character inside attributes.

```python
def dots(html):
    """A middle dot never starts a line: it sticks to the word before it (body only, the source comment stays readable)."""
    head_part, sep, body = html.partition("<body>")
    return head_part + sep + body.replace(" · ", "&nbsp;· ")
```

- `str.partition(sep)` splits at the first occurrence of `sep` into exactly three parts: before, the separator itself, after. If `sep` is missing, the result is `(whole, "", "")` and the function returns its input unchanged. Unlike `split()`, the result always has three items, so unpacking into three names is safe.
- `head_part`, not `head` – a local `head` would shadow the `head()` function inside `dots()`.
- In the body, the space before each ` · ` becomes `&nbsp;`: the line may break after the dot, never before it, so no line starts with a dot.
- The head stays untouched: an entity in an HTML comment is not decoded, so `SOURCE_NOTE` would show a literal `&nbsp;` in view-source.
- `nbsp()` inserts the character, `dots()` the entity. Both render the same; the entity is visible in the source, the character is not.
- `dots()` runs on every generated HTML page: both main pages, the two legal pages and the 404 page. `nbsp()` stays German-only.

---

## 25 · build – writing to disk

```python
def build():
    for key, *_ in LANGS:
        c = CONTENT[key]
        target = SITE / c["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dots(page(c) if key == "en" else nbsp(page(c))), encoding="utf-8")
    (SITE / "impressum.html").write_text(dots(legal("Impressum", IMPRESSUM, "impressum.html")), encoding="utf-8")
    (SITE / "datenschutz.html").write_text(dots(legal("Datenschutzerklärung", DATENSCHUTZ, "datenschutz.html")), encoding="utf-8")
    (SITE / "404.html").write_text(dots(not_found()), encoding="utf-8")
    (SITE / ".htaccess").write_text("ErrorDocument 404 /404.html\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}sitemap.xml\n", encoding="utf-8")
    # The sitemap lists pages, not content: it changes when pages are added or removed. lastmod = build date.
    today = date.today().isoformat()
    alts = "".join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{URL}{slug}"/>' for code, _, _, _, slug in LANGS)
    urls = "".join(f"<url><loc>{URL}{slug}</loc><lastmod>{today}</lastmod>\n{alts}</url>\n" for *_, slug in LANGS)
    (SITE / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
{urls}</urlset>
""", encoding="utf-8")
    print("ok:", ", ".join(str(p.relative_to(SITE)) for p in sorted(SITE.rglob("*.html"))))
```

The two main pages:

- `for key, *_ in LANGS` – only the language code is needed.
- `target = SITE / c["path"]` – the `/` operator on a `Path` joins path parts (Python calls `Path.__truediv__`). It uses the right separator for the operating system; `"de/index.html"` with a forward slash works on Windows too, because `pathlib` normalizes it.
- `target.parent.mkdir(parents=True, exist_ok=True)` – creates `site/de/` if missing. `parents=True` also creates any missing folders above it; `exist_ok=True` means "no error if it already exists". Safe to run on every build.
- `dots(page(c) if key == "en" else nbsp(page(c)))` – a conditional expression picks the pipeline: English gets `page(c)`, German `nbsp(page(c))`; both then go through `dots()`.
- `.write_text(…, encoding="utf-8")` – opens, writes, closes. It overwrites without asking.
- `encoding="utf-8"` matters most on Windows. Without it, Python uses the platform's default encoding, which on Windows has traditionally been a legacy code page such as cp1252. That code page has no →, no ├ and no └ – the build would crash with `UnicodeEncodeError`. The pages declare `<meta charset="utf-8">`, so the bytes must be UTF-8.

The other files:

- `impressum.html`, `datenschutz.html`, `404.html` – one line each: build the path with `/`, generate the HTML, pass it through `dots()`, write it. The calls nest from the inside out: `legal(…)` runs first, `dots()` gets its result, `write_text()` gets that. `(SITE / "…")` needs the parentheses so `.write_text` applies to the joined path, not to the string.
- `.htaccess` – configuration for Apache web servers: "for a 404, deliver `/404.html`". Other servers ignore the file. The leading dot hides it by default in `ls` and in the macOS Finder.
- `robots.txt` – `User-agent: *` addresses all crawlers, `Allow: /` permits everything, `Sitemap:` gives the absolute URL of the sitemap.

The sitemap:

- `today = date.today().isoformat()` – the date as `YYYY-MM-DD` (for example `2026-10-20`), the format sitemaps expect.
- `alts` – one `<xhtml:link>` per language. The block is the same for every URL, since every language version lists all versions.
- `urls` – one `<url>` per language. `for *_, slug in LANGS` puts the star first: everything except the last value goes into `_`, `slug` gets the last one.
- The `<urlset>` declares two namespaces: the sitemap format itself and `xhtml`, which provides the `<xhtml:link>` elements for language versions.
- Trade-off, as the comment says: `lastmod` is the build date. Every build on a new day changes `sitemap.xml`, even when no page changed – expect a diff in that file. Google states that it only uses `lastmod` when the value is consistently accurate, so the field carries little weight either way.
- Legal pages and 404 are not in the sitemap – consistent with their `noindex`.

The report line:

- `SITE.rglob("*.html")` – all `.html` files under `site/`, recursively. `sorted()` orders them; `p.relative_to(SITE)` shortens each to `de/index.html` and so on; `str()` turns the `Path` back into text for `join`.
- Pitfall: the line lists what is on disk, not what was just written. The build never deletes anything – if you remove a page from `build()`, its old HTML file stays in `site/`, keeps being published and keeps appearing in this line. Delete it by hand.

```python
if __name__ == "__main__":
    build()
```

- `__name__` is `"__main__"` when the file runs as a script and `"build"` when another program imports it. The guard means: import for inspection (as in the parity check in section 8) without writing any files.

---

## 26 · Running it, output, and why site/ is committed

Run from the repository root:

```
python3 src/build.py
```

On Windows: `py src\build.py`. Thanks to `SITE`, the working directory does not matter. The run takes a fraction of a second and prints:

```
ok: 404.html, datenschutz.html, de/index.html, impressum.html, index.html
```

What it writes (and overwrites):

| File | Made by |
|---|---|
| `site/index.html` | `page(CONTENT["en"])` → `dots()` |
| `site/de/index.html` | `page(CONTENT["de"])` → `nbsp()` → `dots()` |
| `site/impressum.html` | `legal("Impressum", IMPRESSUM, …)` → `dots()` |
| `site/datenschutz.html` | `legal("Datenschutzerklärung", DATENSCHUTZ, …)` → `dots()` |
| `site/404.html` | `not_found()` → `dots()` |
| `site/.htaccess` | fixed string |
| `site/robots.txt` | f-string with `URL` |
| `site/sitemap.xml` | `LANGS` plus build date |

What it never touches: `site/assets/site.css`, `site/assets/site.js`, `site/assets/fonts/`, `favicon.svg`, `apple-touch-icon.png`, `og-image.png`. Those are hand-made and edited directly in `site/`.

Working rules:

- Copy or markup change → edit `src/build.py` → run the build → check the result in `site/`.
- Never edit the generated HTML files in `site/`. The next build overwrites them without warning.
- Forgetting to rebuild leaves `src/` and `site/` out of sync – the live site keeps the old state. Commit `src/build.py` and the regenerated files together.
- A build on a new day changes `sitemap.xml` (and in January the footer year) even when the content did not change.

Why the generated `site/` folder is committed:

- The web server only serves files; nothing on it runs Python. Whatever is in `site/` is the website.
- With the output in the repository, every commit contains exactly what goes live, and deploying means uploading the contents of one folder to the web root – no build step on the server or in a pipeline. That is the current deploy: a manual upload of `site/` to Apache hosting (see [decisions.md](decisions.md)); an automatic deploy via GitHub Actions would publish the same folder.
- `git diff site/` shows the real effect of a change in `build.py`: the HTML that changed, not only the Python. A change meant for one sentence that accidentally altered every page shows up immediately.
- The cost: two copies of the truth that drift apart when you forget to rebuild. Many projects keep build output out of git for that reason; here the output is small and the build is instant, so the review benefit wins.

---

## Try it

Make each change in `src/build.py`, run `python3 src/build.py`, look at the result, then undo the change and rebuild.

1. **Change the motto.** Set `MOTTO = "sudo dream plan ship it"`. In `site/index.html` the new motto appears three times: in the source comment at the top and twice in the hero prompt (`.cmd` and `.sr-only`); `site/de/index.html` and `site/404.html` change too. Then search `site/assets/site.js` for "plan ship": the console greeting still shows the old motto, because `site.js` is not generated and its copy does not follow.
2. **Swap the footnotes.** In `CONTENT["en"]["facts"]`, change `"Data Scientist[[ds]] · MLOps Engineer[[mlops]]"` to `"MLOps Engineer[[mlops]] · Data Scientist[[ds]]"`. In `site/index.html` the MLOps reference is now 1 and Data Scientist 2, and the Sources list has swapped its order. `site/de/index.html` is unchanged – each language numbers its own footnotes.
3. **Watch escaping and marker scope.** Add `R&D <beta> *test*` to the end of `CONTENT["en"]["profile"]` and to the end of a tree text, for example the SportSpar `"Scope"`. In `site/index.html` the profile paragraph shows `R&amp;D &lt;beta&gt; *test*` – escaped, asterisks untouched. The tree line shows `R&amp;D &lt;beta&gt; <i>test</i>` – the same escaping, but `t()` turned the asterisks into italics.

---

## Key terms

- **Static site generator** – a program that produces finished HTML files ahead of time; the server delivers them unchanged.
- **Escaping** – replacing characters that have meaning in HTML (`& < > " '`) with entities, so text displays as text instead of being read as markup. Prevents broken pages and injected code.
- **Entity** – a character reference such as `&amp;`, `&gt;` or `&nbsp;` that the browser turns back into a character.
- **f-string** – a string literal with an `f` prefix whose `{expressions}` are evaluated at runtime; `{{` and `}}` produce literal braces.
- **Generator expression** – `(expr for x in items if condition)`: produces values one at a time; used here inside `"".join()` and `next()`.
- **Closure** – a function defined inside another function that uses the outer function's variables, like `fn()` with `order`.
- **Canonical and hreflang** – link annotations that tell search engines the preferred URL of a page and which language versions exist.
- **JSON-LD** – structured data in a `<script type="application/ld+json">` block, using the schema.org vocabulary.
- **Relative vs root-absolute path** – `assets/site.css` or `../assets/site.css` resolve from the current page's folder; `/assets/site.css` resolves from the domain root.
- **Non-breaking space** – U+00A0 or `&nbsp;`: looks like a space, but a line never breaks there.

[Next: The HTML](02-html.md)
