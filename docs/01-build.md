# 01 · build.py: from content to HTML

`src/build.py` is the whole site generator: one Python file that holds every line of copy in both languages, turns it into HTML strings and writes finished pages to `site/`. It runs on the Python standard library alone – no framework, no template engine, no `pip install`. Everything else in `site/` (CSS, JavaScript, fonts, images) is maintained by hand and covered in later chapters.

The file reads top to bottom in this order: docstring · imports · constants · `CONTENT` · HTML fragments · small builder functions · `page()` · legal pages and 404 · torch · typography fixes · `.htaccess` · `build()`. Every function returns a string of HTML; bigger functions call smaller ones and glue their strings together. Nothing touches the disk until `build()` at the very end.

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
 5. Brand elements stay English in every language: claim, tagline, motto, the four Ps
    and the tree labels (as in #JobAlert: Scope, Team, Result).
    Everything else is localized, not translated.
 6. Google Cloud is a tool, Azure only the platform of single projects. AI is named once
    as a tool in a project's stack (Claude API), never as a label on single projects.
 7. No wordplay that isn't Pete's own or doesn't follow his patterns.
 8. Four coined elements and no more: claim, motto, marketinkerer, P⁴.
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
| 5 · Brand elements stay English | They live outside `CONTENT` (`TAGLINE`, `CLAIM`, `MOTTO`, `P4`) or appear unchanged in both dictionaries (tree labels such as `"Scope"`). On the German page the code marks them with `lang="en"`. |
| 6 · Google Cloud, Azure, AI | Copy only: Google Cloud in `STACK_DS` and the Scope of the Data Scientist training, Azure only in project entries, AI only as a tool in a project's stack ("Python · Claude API" under Document extraction). The Approach section that once carried an AI principle was removed on 18.11.2026. |
| 7 · No foreign wordplay | Copy only. |
| 8 · Four coined elements | Claim, motto, *marketinkerer*, P⁴ – nothing else on the page is a slogan. Ten were too many; the rest were cut, among them the three Approach slogans and the footer line. Copy only: a new slogan would break the rule, not the build. |

---

## 2 · Imports

```python
from datetime import date
from html import escape as e
from pathlib import Path
import base64
import hashlib
import json
import posixpath
import re
```

- `date` – `date.today()` supplies the copyright year in `footer()`, the `lastmod` date in the sitemap and the end month of the role that is still running in `months()`.
- `escape as e` – `html.escape` under a one-letter alias, because it is called dozens of times inside f-strings and `{e(text)}` keeps those lines short. It replaces the five characters that have meaning in HTML: `&` → `&amp;` · `<` → `&lt;` · `>` → `&gt;` · `"` → `&quot;` · `'` → `&#x27;`.
- Why escaping matters: unescaped, a `<` in the copy opens a tag, an `&` may start an entity, and a `"` inside an attribute value ends the attribute – the page breaks in ways that are hard to spot. If text ever comes from outside (a form, an API, a spreadsheet export), the same gap lets a `<script>` in that text run in the visitor's browser: cross-site scripting (XSS). All copy here is your own, so the practical risk is broken markup; the habit protects you the day content comes from elsewhere.
- Pitfall: never use `e` as a variable name in this file. Inside a function, even `except Exception as e:` turns `e` into a local variable for the whole function, and every `e(...)` call in it fails with `UnboundLocalError`.
- `Path` – object-oriented file paths: `/` joins parts, `.parent` goes up a level, `.mkdir()`, `.write_text()` and `.rglob()` do the file work.
- `base64` – turns the SHA-256 of the two inline scripts into the text form the content security policy expects (`csp_hash()`, section 10).
- `hashlib` – SHA-256, for the fingerprints of `site.css` and `site.js` in their URLs (`VERSION`, section 10) and for the two script hashes.
- `json` – serializes the structured-data block in `jsonld()`, the torch's strings in `torch_data()` and `assets/torch.json`.
- `posixpath` – path arithmetic with `/`, the way URLs write it, on every operating system: the links between the pages (`href()`, `page_id()`, section 12). `Path` would use `\` on Windows.
- `re` – regular expressions for three text markers: `*italics*`, syllable dots and `[[footnotes]]` – for the dates of the roles, and for the content of an inline script in `csp_hash()`.

All eight are standard library – that is what "no dependencies beyond Python 3" means.

---

## 3 · Paths and links

```python
SITE = Path(__file__).resolve().parent.parent / "site"
URL = "https://peterstieg.com/"
EMAIL = "info@peterstieg.com"
LINKEDIN = "https://www.linkedin.com/in/peterstieg/"
GITHUB = "https://github.com/PeterStieg"
MAP = "https://www.openstreetmap.org/?mlat=51.3673&mlon=12.3668#map=15/51.3673/12.3668"   # a pin on Coppiplatz, Gohlis
REPO_DS = "https://github.com/PeterStieg/feb25_bds_classification-of-rakuten-e-commerce-products"
REPO_MLOPS = "https://github.com/PeterStieg/may25_bmlops_classification-of-rakuten-e-commerce-products"
DEMO_DS = "https://feb25-bds-rakuten.streamlit.app/"       # Streamlit Community Cloud: sleeps when idle, wakes on request
DEMO_MLOPS = "https://may25-bds-rakuten.streamlit.app/"
```

- `SITE` – the output folder, computed rather than typed:
  - `__file__` is the path of this script as Python received it, possibly relative (`src/build.py`).
  - `.resolve()` makes it absolute and resolves symbolic links.
  - `.parent` is `src/`, `.parent.parent` the repository root.
  - `/ "site"` appends the folder name. Result: the script writes to the right place no matter which directory you start it from.
- `URL` ends with a slash. Every use concatenates (`URL + HOME[L]`, `f"{URL}og-image.png"`), so the trailing slash must stay and the parts appended to it must not start with one.
- `DEMO_*` – the two capstone apps on Streamlit Community Cloud. An app that nobody has opened for a while goes to sleep; the first visitor sees a wake-up button and waits about a minute.
- `MAP` – the place under Contact as a map: OpenStreetMap with a pin on Coppiplatz in Gohlis. `mlat` and `mlon` in the query set the pin; the part after `#` positions the map – zoom 15, latitude, longitude –, close enough to read the square's name, wide enough to see the district. Four decimals are about 10 metres. OpenStreetMap rather than Google Maps: it opens without a consent page first.
- `EMAIL`, `LINKEDIN`, `GITHUB`, `MAP`, `REPO_*`, `DEMO_*` – each defined once and used in several places (contact section, JSON-LD, legal pages, project links). Change once, rebuild, done.
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
# code, label, name, the start page's address from the site root – its folder: the server answers with index.html
LANGS = [("en", "EN", "English", ""),
         ("de", "DE", "Deutsch", "de/")]
HOME = {code: home for code, _, _, home in LANGS}
```

A list of 4-tuples, one per language. The position of each value is its meaning:

| Index | Example | Used for |
|---|---|---|
| 0 · code | `"de"` | `hreflang`, `lang`, key into `CONTENT` |
| 1 · label | `"DE"` | visible text in the language switch |
| 2 · name | `"Deutsch"` | tooltip in the switch, in its own language |
| 3 · home | `"de/"` | the start page's address: canonical, hreflang, sitemap and every link to it |

- A list, not a dict, because order matters: English comes first in the switch and the sitemap.
- The file is `de/index.html`, the address is `/de/`. Web servers answer a folder with its `index.html`, so every link names the folder: the address search engines know, and one entry per page in the statistics instead of two (`/de/` and `/de/index.html`). `.htaccess` forwards the file names to the folders (section 30). Opened straight from disk, a folder link shows the folder's file list – to click through the pages locally, serve `site/` (`python3 -m http.server -d site`).
- `HOME` – the fourth field as a dict, code → address: `{"en": "", "de": "de/"}`. A dict comprehension; `_` marks the fields it skips. Most places want one language's start page (`HOME[c["lang"]]`), which a dict gives by key.
- The tuples are unpacked by position: `for code, label, name, _ in LANGS`, `for code, *_ in LANGS`. Pitfall: add a fifth field and every fixed-length unpacking raises `ValueError: too many values to unpack`; only the starred forms keep working.
- Adding a language takes three things: a `LANGS` entry, a complete `CONTENT` entry, and a date in that language in every `NOTES` entry (otherwise `n["date"][L]` raises `KeyError`).

---

## 6 · P⁴ and the chapters

```python
# P as in Peter – English in every language, like M³ and F³.
P4 = ["Performance", "Pipelines", "Pixels", "People"]
# four chapters, like the parts of a slide deck: the first section of each is numbered and linked in the menu,
# the sections after it belong to it – P⁴ and Languages to Profile, Education to Experience
CHAPTERS = {"profile": ["skills", "languages"], "experience": ["education"], "projects": [], "contact": []}
# page order: profile, skills, languages, experience … – Sources close the page in no chapter: footnotes from all four lead there
SECTIONS = [k for first, rest in CHAPTERS.items() for k in (first, *rest)] + ["sources"]
```

- `P4` – the four headings of the P⁴ section. `page()` pairs them by position with `CONTENT[lang]["fields"]`.
- `CHAPTERS` – the page's four chapters, like the four parts of a slide deck. Each key opens a chapter and is linked in the menu; the list holds the sections that follow it and belong to it. The order of the keys is the order of the chapters, so `profile` is 01 and `contact` 04. The keys are the English ones, so both languages share the numbers.
- The page order must match: every section in a list comes right after its chapter's first section. That is why Education stands behind Experience in `page()`, not at the end.
- `SECTIONS` – all eight section keys in page order: `["profile", "skills", "languages", "experience", "education", "projects", "contact", "sources"]`. Projects and Contact are chapters of one section: their lists are empty, and `(first, *rest)` then holds the opener alone. The jump control lists the sections from it (section 23).
  - A list comprehension with two `for` clauses reads like two nested loops, left to right: for each chapter (`first`, `rest`), for each `k` in that chapter.
  - `(first, *rest)` builds a tuple: the opener, then the items of `rest` unpacked into it. `("experience", *["education"])` is `("experience", "education")`.
  - `+ ["sources"]` – Sources come last and belong to no chapter: the footnote numbers lead there from Experience and Education alike, an appendix, as at the end of a deck. They carry no number, and the menu marks no chapter while they are read (section 21, and site.js).
  - Derived, not typed: add a section to `CHAPTERS` and it appears in the jump control's list with the right number. The order of the `out.append` calls in `page()` still has to follow by hand.
- Pitfall: pairing by position. Reorder `P4` without reordering both `fields` lists and every text lands under the wrong heading. And `zip()` stops at the shorter list: a missing fourth text silently drops "People" – no error.

---

## 7 · NOTES, companies and stacks

```python
# Footnotes: verification links (QR codes on the Liora diplomas, thekey.career, edX), plus course pages where they exist.
# "title": one string, or one per language; "when": which date label (issued | completed), default issued;
# "by": the organisation behind the credential, for the structured data (hasCredential → recognizedBy).
# Videos carry "watch" instead of "verify": a German title, who published or aired it ("src"), when, where to watch ("on").
NOTES = {
    "ds": {"title": "Data Scientist",
           "verify": "https://document-factory.datascientest.com/verify/3225d69a-a3b6-4bd2-bafe-df9381eff729",
           "course": "https://liora.io/en/courses/data-ai/data-scientist",
           "date": {"en": "10 June 2025", "de": "10. Juni 2025"}, "by": "Université Paris 1 Panthéon-Sorbonne"},
    "mlops": {"title": "MLOps Engineer",
              "verify": "https://document-factory.datascientest.com/verify/46b46e0c-cd3b-458a-8e9f-4ee08feb9164",
              "course": "https://liora.io/en/courses/data-ai/mlops",
              "date": {"en": "1 September 2025", "de": "1. September 2025"}, "by": "Université Paris 1 Panthéon-Sorbonne"},
    "ihk": {"title": {"en": "Agile project management specialist (IHK)", "de": "Fachkraft für agiles Projektmanagement (IHK)"},
            "verify": "https://www.thekey.career/zertifikat/ac-2023-bfbe9c/",
            "date": {"en": "16 February 2023", "de": "16. Februar 2023"}, "when": "completed", "by": "IHK-Projektgesellschaft"},
    "edx": {"title": "Introduction to Artificial Intelligence (Microsoft)",
            "verify": "https://courses.edx.org/certificates/e801d0f98e64454e8b81e052d1947108",
            "date": {"en": "12 June 2018", "de": "12. Juni 2018"}, "by": "Microsoft"},
    "h42": {"title": "Hellinger 42 + Brandible: erfolgreiches Merchandise-Konzept", "src": "Brandible", "when": "published",
            "date": {"en": "22 May 2024", "de": "22. Mai 2024"}, "on": "YouTube",
            "watch": "https://www.youtube.com/watch?v=swBJnkVCTNM"},
    "galileo": {"title": "Galileo X-Plorer: Inside EM – Die Sommermärchen-Macher", "src": "ProSieben", "when": "aired",
                "date": {"en": "9 June 2024", "de": "9. Juni 2024"}, "on": "Joyn",
                "watch": "https://www.joyn.de/play/serien/galileo-x-plorer/2024-15-inside-em-die-sommermaerchen-macher"},
}

# the ledger names a company, the name links to its role under Experience (role "id")
COMPANIES = {"e-service-check": "E+SERVICE+CHECK", "brandible": "Brandible", "posterlounge": "Posterlounge"}

STACK_DS = "Python · Keras · PyTorch · Google Cloud"
STACK_MLOPS = "Docker · Airflow · MLflow · FastAPI · Grafana"
```

- `NOTES` – a dict of dicts. The outer key (`"ds"`, `"mlops"`, `"ihk"`, `"edx"`, `"h42"`, `"galileo"`) is the footnote ID: it appears in the `[[ds]]` markers in the copy and in the HTML ids `fn-ds` and `ref-ds`.
- Two kinds of note. Four are credentials, with `verify`. Two are videos, with `watch`, cited from Brandible's Scope (since 19.11.2026): the customer testimonial with Hellinger 42 on Brandible's YouTube channel, and the Galileo episode on ProSieben, on demand at Joyn. The Sources loop in `page()` tells them apart by `watch` (section 25).
- Inner keys:
  - `title` – the credential's name. One string when it is the same in both languages, a dict with one string per language when not (the IHK certificate). `note_title()` (section 12) picks the right one.
  - `verify` – the verification page: the URL behind the QR code on the Liora diplomas, the certificate pages on thekey.career and edX.
  - `course` – the course page. Optional: the IHK and edX entries have none, and the Sources list then leaves the link out.
  - `date` – one preformatted string per language.
  - `when` – which label goes before the date. Optional, default `"issued"`. The IHK page says the course was *completed* on that date, so its entry says `"completed"`; the label text itself lives in `CONTENT[lang]["notes"]`.
  - `by` – the organisation behind the credential, for the structured data (section 19).
  - Video notes instead: `title` – the video's own title, German on both pages; `src` – who published or aired it; `when` – `"published"` or `"aired"`; `on` – the platform the link leads to; `watch` – the link.
- Why preformatted dates instead of `date` objects: Python's month names (`%B` in `strftime`) follow the system locale, and switching to a German locale depends on what the machine has installed. Two literal strings avoid that entirely.
- `NOTES` feeds both the visible footnotes in `page()` and the credentials in `jsonld()` – one source, two outputs. The videos are no credentials: `jsonld()` takes only the notes with `verify`.
- `COMPANIES` – the companies the results ledger names. Each key does two jobs: it looks up the display name, and it is the HTML id of that company's role under Experience (`#posterlounge`), so the name in the ledger becomes a link to the role. The names are the same in both languages, so they live outside `CONTENT`, and each is spelled once instead of once per ledger row.
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
        "theme": ("Theme", "Light", "Dark"), "arrow": "to", "to_top": "Back to top", "new_tab": "opens in a new tab", "map": "map",
        "torch": {"tags": ["", "HTML · again: build.py", "build.py · again: off"],
                  "keys": "Keyboard shortcuts", "close": "Close",
                  "rows": [["sudo", "Code view: HTML · build.py · off"], ["Esc", "Close"], [["?", "F1"], "Show this list"]]},
        "dur": ("year", "years", "month", "months"),
        "jump": {"label": "Sections", "menu": "All sections", "up": "Up: %s", "down": "Down: %s"},
        "desc": "Head of Marketing in Leipzig. …",
        "skip": "Skip to content",
        "nav": [("profile", "Profile"), ("experience", "Experience"), ("projects", "Projects"), ("contact", "Contact")],
        "sec": {"profile": "Profile", "languages": "Languages", "experience": "Experience", "projects": "Projects",
                "education": "Education", "contact": "Contact", "sources": "Sources"},
        "entry": {"hw": "mar·ke·tin·ker·er", "pos": "noun", "ety": "[*marketer* × *tinkerer*]",
                  "def": "A marketing leader who builds the tools behind the campaigns – and the teams that run them."},
        "profile": "Leadership roles at four companies, …",
        "ledger_label": "Selected results",
        "ledger": [
            ("Leads > 2×", "inbound inquiries year over year", "e-service-check"),
            …
        ],
        "fields": [
            "Google Ads, Microsoft Advertising, Google Shopping; Meta, LinkedIn, Pinterest; Outbrain, Taboola; Amazon, Otto, Cdiscount – "
            "…",
            …
        ],
        "roles": [
            {"id": "e-service-check", "when": "since 11/2025", "title": "Head of Marketing", "org": "E+SERVICE+CHECK", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.",
             "tree": [("Team", "…"),
                      ("Scope", "…"),
                      ("Result", "…")]},
            {"id": "liora-mlops", "when": "05/2025 – 07/2025", "title": "MLOps Engineer training (full-time)",
             "org": "Liora", "url": NOTES["mlops"]["course"], "with": "Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Scope", "…"),
                      ("Result", "…")]},
            …
            {"id": "posterlounge", "when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Online shops for wall art, art prints and frames in more than 15 European countries.",
             "tree": [("Team", "…"),
                      ("Scope", "…"),
                      ("Result", "…")],
             "path": ("Five positions", [("09/2021", "Head of Marketing"), ("10/2020", "Senior Marketing Manager"),
                                           ("11/2018", "Online Marketing Manager"), ("10/2017", "SEO Manager Italy"),
                                           ("07/2017", "SEO, freelance")])},
            {"id": "immobiliare", "when": "05/2017 – 06/2017", "title": "Online Marketing Manager", "org": "Immobiliare.it", "url": "https://www.immobiliare.it/en/", "place": "Rome",
             "tree": [("Scope", "…")]},
            …
            {"id": "freelance", "when": "2013 – 2020", "title": "Freelance: websites, design, translation", "org": "Alongside employment",
             "tree": [("Scope", "…"),
                      ("Result", "…")]},
            {"id": "rome-2010-2014", "when": "10/2010 – 09/2014", "title": "Marketing, market research, export", "org": "Six companies", "place": "Rome",
             "tree": [("Scope", "…")],
             "positions": ("Six positions", [
                 ("09/2014", "Business Development Specialist", "3D2B", "http://www.3d2b.com/"),
                 ("04/2014 – 08/2014", "Marketing Consultant", "SBS systems for business solutions", "https://it.sbsbusiness.eu/"),
                 ("06/2013 – 05/2014", "Corporate investigations", "Inner Valor", "https://innervalor.com/"),
                 …
             ])},
        ],
        "groups": [
            ("At E+SERVICE+CHECK", [
                ("Customer portal", "…", "Azure", []),
                …
            ]),
            ("Certification capstones", [
                ("Rakuten product classification", "…", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                …
            ]),
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora (formerly DataScientest) in partnership with Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Agile project management specialist[[ihk]]", "IHK"),
            …
        ],
        "languages": ["German (native)", "English C2", "Italian C2", "Spanish B1", "French A2"],
        "reach": ("Email", "Based in", "Leipzig"),
        "ask": "Questions about performance, pipelines, pixels or people:",
        "notes": {"issued": "issued", "completed": "completed", "verify": "Verify credential", "course": "Course page", "back": "Back to text",
                  "published": "published", "aired": "aired", "watch": "Watch on %s"},
        "imprint": "Legal notice", "privacy": "Privacy", "legal_desc": "%s for peterstieg.com",
        "lost": ("Page", "not found.", "Diese Seite gibt es nicht.", "start page"),
        "jobtitle": "Head of Marketing",
    },
    # ------------------------------------------------------------------ DE
    "de": {
        "lang": "de", "path": "de/index.html", "root": "../", "locale": "de_DE",
        …
        "ids": {"profile": "profil", "skills": "kompetenzen", "languages": "sprachen", "experience": "werdegang",
                "projects": "projekte", "education": "ausbildung", "contact": "kontakt", "sources": "quellen"},
        …
    },
}
```

`CONTENT` is a dict with one entry per language. Each entry is itself a dict that `page()` receives as its parameter `c` – that is why nearly every function in the file takes `c` as its first argument.

- Every list with a time order runs newest first: the ledger (E+SERVICE+CHECK, Brandible, Posterlounge), the roles, the steps inside a role (`path`, `positions`), the dated facts in Education and the project groups. One direction throughout, so nothing reads as reversed. The trade-off, accepted for that consistency: the largest figure, the media budget from €6k to €240k, stands last in the ledger.
- No code sorts anything. The order in the dict is the order on the page, and `role()` even relies on it to compute the ends of the promotions (section 24). A new entry goes where it belongs in time.
- The two Liora courses stand in `roles` as well: full-time from 02 to 07/2025, between Brandible (until 12/2024) and E+SERVICE+CHECK (from 11/2025), they show what that stretch was. Their titles say what they were, "MLOps Engineer training (full-time)" and "Data Scientist training (full-time)", so they do not read as jobs.
  - `"org": "Liora", "url": NOTES["mlops"]["course"]` – the school links the course page of that training, the same URL as the footnote's "Course page" (section 7): defined once, in `NOTES`. `CONTENT` comes after `NOTES` in the file, so the name is already bound when the dict is built.
  - `"with"` – the partner, written after the link and outside it: "Liora ↗ · Université Paris 1 Panthéon-Sorbonne". The ↗ promises Liora's page; inside the link the Sorbonne would seem to be the target too.
  - "(formerly DataScientest)" stands in Education, not here: there it also explains why the verification links in Sources lead to datascientest.com.
- Company names carry no legal form – "Posterlounge", not "Posterlounge GmbH"; "SBS systems for business solutions", not "… Srl": the names people know, the ones references and LinkedIn use. The ↗ already leads to the website, so no domain stands in as a label either. "Brandible by KSi International" keeps its "by": the commercial register still lists KSI International GmbH, so "formerly" would claim a rename.
- The timeline as of 17.11.2026 – eleven entries, three of them new:
  - Immobiliare.it, 05/2017 – 06/2017, Online Marketing Manager in Rome: an employment, so an entry of its own, between Posterlounge and YOUniversal Media. Each language links its own page of the portal – `immobiliare.it/en/` in English, `immobiliare.it/` in German –, so each dict carries its own `url`.
  - The freelance block, "2013 – 2020", "Alongside employment": websites, design and translations next to the jobs of those years, placed by its start between YOUniversal Media and the early group. Years only, no `place`, no `url`: the client sites are offline. Scope names the work (sites, design, translations; TextMaster without a link – it now belongs to Acolad), Result the two client sites in Rome.
  - 3D2B, 09/2014, as the first row of the early group, not as an entry: one month in Rome, right after SBS – an entry of its own would weigh like a role of several years. The group now runs to 09/2014, reads "Six companies" and "Six positions", and its Scope names lead generation, OSINT and primary and secondary research.
- Posterlounge's `path` ends with `("07/2017", "SEO, freelance")`: freelance SEO before the contract, shown as "07/2017 – 09/2017 · 3 months" (section 24). The label counts what the list holds, "Five positions" (German "Fünf Stationen"): the freelance row is a position too, but being hired is not a promotion, so "promotions" would have miscounted.

### Every key and what it feeds

Page mechanics:

| Key | Type | Feeds |
|---|---|---|
| `lang` | str | `<html lang>`, the `!= "en"` checks that mark English words with `lang="en"`, the date lookup in the footnotes |
| `path` | str | the page's file relative to `site/`: where `build()` writes it, and where `href()` counts links from (section 12). `legal()` replaces it with the legal page's own |
| `root` | str | prefix from the page back to the site root: `""` for `/index.html`, `"../"` for `/de/index.html` and the German legal pages, `"/"` on the 404s. Prepended to the stylesheet, the script, the fonts and the icons |
| `locale` | str | `og:locale`; the other languages' values become `og:locale:alternate` |
| `ids` | dict, DE only | German section anchors (`#werdegang` instead of `#experience`), read through `sid()` |

Interface labels:

| Key | Type | Feeds |
|---|---|---|
| `aria_main`, `aria_legal`, `aria_lang` | str | accessible names of the header nav, footer nav and language group |
| `theme` | 3-tuple | group label, "light" label, "dark" label for `theme_switch()` |
| `arrow` | str | the word behind a drawn → (`"to"` / `"auf"`): what screen readers say and what copied text reads |
| `to_top` | str | label of the jump control's up link while it leads to the top of the page (`"Back to top"` / `"Nach oben"`) |
| `new_tab` | str | what screen readers hear after every link that leaves the site: `"opens in a new tab"` / `"öffnet in neuem Tab"`, in parentheses, as visually hidden text (`offsite()`, section 20) |
| `torch` | dict | the strings of the torch (`sudo`, chapter 4), which `site.js` cannot generate in two languages: `tags` – the line under the light at levels 1 and 2 (level 0 shows none, hence the empty string); `keys`, `close` and `rows` – the card that `?` or F1 opens: its title, the name of its close button, and per shortcut the key – or a list of keys, `["?", "F1"]` – and what it does. Written into `<main>` as JSON in one attribute (section 25) |
| `map` | str | read out before `new_tab` on the place under Contact, which opens a map: "map, opens in a new tab" / "Karte, öffnet in neuem Tab" |
| `dur` | 4-tuple | the words for the durations under the role dates: year, years, month, months (`duration()`, section 22). Joined by commas, they also go to `site.js`, which recounts the running role |
| `jump` | dict | the jump control: `label` names its `<nav>`, `menu` the button that opens the section list, `up` and `down` are templates in which `%s` stands for a section name (`"Up: %s"` → "Up: Experience") |
| `skip` | str | text of the skip link |
| `nav` | list of (id, label) | header links |
| `sec` | dict | section headings, keyed by internal section name |
| `notes` | dict | labels in the Sources list, incl. the date labels `issued`, `completed`, `published` and `aired`, and `watch` – the link text of a video note, `%s` the platform ("Watch on YouTube", "Bei Joyn ansehen") |
| `imprint`, `privacy` | str | footer links |
| `lost` | 4-tuple | the 404 page in this language: the word inside `{KeyWord:…}`, the rest of the heading, the line in the other language, the name of the start page that screen readers hear after `cd ~` (`not_found()`, section 27) |

Metadata:

| Key | Type | Feeds |
|---|---|---|
| `desc` | str | `meta description`, `og:description`, JSON-LD `description` |
| `legal_desc` | str | the description of the legal pages; `%s` stands for the page title: "Legal notice for peterstieg.com", "Impressum von peterstieg.com" (`legal()`, section 26) |
| `jobtitle` | str | JSON-LD `jobTitle` |

Copy:

| Key | Type | Feeds |
|---|---|---|
| `entry` | dict | the dictionary entry: `hw` headword with syllable marks, `pos` part of speech, `ety` etymology, `def` definition |
| `profile` | str | the profile paragraph |
| `ledger_label`, `ledger` | str, list of (figure, context, company key) | the results list in the profile; the key looks up the name in `COMPANIES` and links to the role with that `id` |
| `fields` | list of 4 str | the P⁴ section (key `skills`), paired with `P4` |
| `languages` | list of str | Languages: one per line, the level after the name |
| `roles` | list of dicts | Experience: `id` (the anchor of the role: the ledger links to it, the language switch lands on it – every role has one since 19.11.2026), `when` (`"MM/YYYY – MM/YYYY"`; `"since MM/YYYY"` for the role that is still running; `"YYYY – YYYY"` with years only – `months()` reads the dates), `title`, `org` (the name without legal form), `url` (optional: the company's website – for the two trainings the course page –, behind the name, in a new tab), `with` (optional: a partner named after the link, outside it – the Sorbonne for the two trainings), `place` (optional, may be `""`), `ctx` (optional), `tree` (list of (label, text), may be empty), `path` (optional: (label, list of (start `"MM/YYYY"`, title)), newest first – the steps within one role, one per contract, behind a disclosure; the newest ends with the role, each other one the month before the one that followed it starts), `positions` (optional: (label, list of (dates, title, company, url – `""` without one)), newest first – the positions one entry sums up, behind a disclosure, each with its own dates: a range `"MM/YYYY – MM/YYYY"` or a single month `"MM/YYYY"`) |
| `groups` | list of (title, items) | Projects; each item is (name, text, stack, links) – `links` a list of (label, URL) pairs, empty when there is nothing to link; each link opens in a new tab |
| `facts` | list of (label, value, sub-line or `""`) | Education: year, certificate or degree, school |
| `reach` | 3-tuple | Contact: the label for the mail row, the label for the place row, the place – in German "E-Mail", "Wohnort" |
| `ask` | str | Contact: the line before the rows – what to write about (section 25) |

### How EN and DE mirror each other

- Same keys, same shapes, same number and order of list items. The only key that exists in one language and not the other is `ids` – English uses the internal keys directly as anchors.
- Localized, not translated: German uses KUR, English RoAS (rule 2), job titles follow German usage ("Leiter Marketing"), number formats follow each language ("6.000 → 240.000 €" vs "€6k → €240k"), and trade terms follow each language's habit – "marketing automation" (Brandible, Rapidobject) is "Marketing Automation" in German, the English term German marketing uses, capitalized as a German noun. The two trainings follow each language's word order: "MLOps Engineer training (full-time)", "Weiterbildung MLOps Engineer (Vollzeit)".
- English inside German: the tree labels `"Team"`, `"Scope"` and `"Result"` stay English in the DE dict (rule 5). Every role uses the same three, in that order, wherever there is something to say – a role without a team simply has no `"Team"` row.
- Not localized: the company keys at the end of each `ledger` entry and the role `id`s that name a company or a course. `#posterlounge` is the anchor on both pages, unlike the section anchors, which `ids` translates. The two roles named after what they were get a German id on the German page: `#freelance` / `#freiberuflich`, `#rome-2010-2014` / `#rom-2010-2014`. The project ids come from the project names (`slugify()`, section 12), so they follow the language: `#customer-portal` / `#kundenportal`.
- Nested lists mirror too: the five rows under `"path"` and the six positions under `"positions"` exist in both dicts, in the same order, newest first. The labels differ ("Five positions", "Fünf Stationen"; "Six positions", "Sechs Stationen") and follow one pattern, number and noun. The promotions keep their titles in both, because they are the titles that were held – only the market in "SEO Manager Italy", "SEO Manager Italien", and the freelance row, "SEO, freelance", "SEO, freiberuflich", are localized. The positions localize the titles that describe work ("Market research", "Marktforschung") and keep the rest; dates and company names are identical.
- One value differs on purpose: Immobiliare.it's `url`, the portal's English page on the English page, its Italian home page on the German one.
- Parity is checked in part. A key missing in DE raises `KeyError` as soon as `page()` asks for it – loud and easy to find. A role or project only added in EN stops the build: `twins()` (section 12) pairs them by position and asserts that both pages list as many. Other lists – a fact, a P⁴ text – are not checked: the German page simply shows one entry fewer. Edit both languages in the same sitting.
- Quick parity check from the repository root (importing does not build anything, see section 30):

  ```
  python3 -c "import sys; sys.path.insert(0, 'src'); import build as b; print(set(b.CONTENT['en']) ^ set(b.CONTENT['de']))"
  ```

  It prints `{'ids'}`. Anything else means a key is missing on one side. (`^` on sets is the symmetric difference: elements in exactly one of the two.)

### Markers inside the copy

| Marker | Example | Becomes | Handled by |
|---|---|---|---|
| `→` | `"€6k → €240k"` | a drawn SVG arrow, its word kept as visually hidden text | `t()` |
| `*word*` | `"[*marketer* × *tinkerer*]"` | `<i>word</i>` – words cited as words, like in a dictionary | `t()` |
| `[[key]]` | `"Data Scientist[[ds]]"` | a numbered footnote reference to `NOTES[key]` | regex in `page()`, experience and education sections |
| ` · ` | `"Python · BigQuery · Data Studio"` | a middle dot glued to the word before it | `dots()` |

Pitfall: the markers only work where the code runs the text through the matching function. `t()` handles `entry["ety"]`, the first item of each `ledger` entry and the values in each role's `tree`. The `[[…]]` regex runs on the finished roles – so on every role's `tree` text, where Brandible's Scope cites the two videos – and on the middle value of each `facts` tuple. Everywhere else – `profile`, `fields`, `languages`, `people_note`, `ctx`, `path`, `positions`, `groups`, `approach` – the text only goes through `e()`: asterisks stay visible and `→` stays a plain character in a fallback font.

---

## 9 · SOURCE_NOTE

```python
SOURCE_NOTE = f"""<!--
  Hallo · Hi · Ciao – view-source counts as root access, too.
  On the page: type or tap sudo · ? or F1 lists the keys.

  peterstieg.com
  ├── analytics from the server logs – no cookies, no banner
  ├── fonts, scripts, images from this server
  └── no framework – build.py writes the HTML

  >_ {MOTTO}
-->"""
```

- A triple-quoted f-string: it may span lines, and `{MOTTO}` is the only replacement field.
- The content is an HTML comment (`<!-- … -->`): invisible on the page, visible to anyone who opens the page source. `head()` places it between `<!doctype html>` and `<html>`.
- The tree says how the site is built, for the people who read sources: statistics from the server logs (IONOS WebAnalytics), so no cookie and no consent banner; everything from one server; static HTML from one script. It used to read "no tracking" – odd on the site of a performance marketer, and no longer true once the statistics were switched on (decisions, 22.11.2026).
- The second line points developers to the torch (`site.js`): the same view of the source, on the page. `sudo`, typed or tapped in the prompt, switches it on; `?` or F1 opens the card with the keys. The console greeting in `site.js` says the same words, so whoever finds one finds the other.
- The comment text must never contain `-->` – that would end the comment early and print the rest on the page.
- Pitfall: the comment comes before `<meta charset="utf-8">`. Browsers look for the charset declaration only in the first 1024 bytes of the file; it currently sits at byte 394. Let the comment grow by several hundred bytes and the browser may have to guess the encoding – umlauts and the tree characters break.
- `dots()` deliberately leaves this comment alone (section 29).

---

## 10 · THEME_BOOT, SPECULATION, csp_hash and VERSION

```python
# Runs before the stylesheet: marks JS as available and applies a stored theme without a flash.
THEME_BOOT = ("<script>(function(){var r=document.documentElement;r.classList.add('js');"
              "try{var t=localStorage.getItem('theme');"
              "if(t==='light'||t==='dark'){r.setAttribute('data-theme',t);"
              "document.querySelector('meta[name=color-scheme]').content=t}}catch(e){}})()</script>")
```

The Python side:

- Four string literals side by side inside parentheses. Python joins adjacent literals into one string at compile time – a way to wrap a long one-liner without `+` and without adding line breaks to the output. The same trick builds the SVG constants and the return value of `theme_switch()`.
- The JavaScript uses single quotes, the Python literals double quotes, so neither needs escaping. If you add JavaScript containing double quotes, escape them (`\"`) or switch the Python delimiters. That is also why the selector reads `meta[name=color-scheme]` without quotes around the value: `color-scheme` is a valid CSS identifier, so it needs none.

The JavaScript, statement by statement:

- `(function(){ … })()` – an IIFE ("immediately invoked function expression"): the code is wrapped in an anonymous function that is called right away. The point is scope. A `var` at the top level of a script becomes a global (`window.t`) that any other script on the page could read or overwrite; inside the function, `r` and `t` are local and disappear when the function returns. The outer parentheses make the parser read `function(){…}` as an expression, so the trailing `()` can call it.
- `var r=document.documentElement` – `<html>`, used twice below; the short name keeps the one-liner short.
- `r.classList.add('js')` – adds the class `js` to `<html>`. The CSS uses it to show JavaScript-only controls only when JavaScript actually runs: `html:not(.js) .themes { display: none; }` hides the theme buttons otherwise.
- `try{ … }catch(e){}` – reading `localStorage` throws in some privacy modes or when site data is blocked. The empty `catch` makes the page fall back to the system theme instead of stopping the script. (This `e` is JavaScript and has nothing to do with Python's `e`.)
- `var t=localStorage.getItem('theme')` – the visitor's earlier choice, saved by `site.js` when a theme button is clicked. Local to the IIFE.
- `if(t==='light'||t==='dark'){…}` – a whitelist: only the two known values get through. Two statements in braces:
  - `r.setAttribute('data-theme',t)` – the CSS switches its color variables on `:root[data-theme="dark"]` and `:root:not([data-theme="light"])`.
  - `document.querySelector('meta[name=color-scheme]').content=t` – the `<meta name="color-scheme">` that `head()` writes just above this script (section 14) says `light dark`: the browser draws its own parts – scrollbars, the canvas behind the page, form controls – in the system's scheme. A pick narrows it to the picked one before the first paint, so a dark page on a light system does not get light scrollbars. The parser has already created the meta element when the script runs, because it comes first in the source.

Why it must run inline, in the head, before the stylesheet:

- Inline: no extra file to download; it runs the moment the parser reaches it.
- In the head: the attribute is set before anything is painted. If this logic lived only in `site.js` – loaded with `defer`, so it runs after the whole document is parsed – the page would first render in the system theme and then switch: a visible flash.
- Before the `<link rel="stylesheet">`: a regular script that comes after a stylesheet still downloading has to wait until that stylesheet has loaded, because the script might read computed styles. Placed first, it runs immediately and does not wait for the CSS.
- `site.js` repeats the steps (adds `js`, applies a stored theme if none is set yet, sets the meta tag in `paintTheme()`). Redundant but harmless – a safety net.

Next, a second inline script, for speed:

```python
# Chrome and Edge fetch a page of this site while the pointer rests on a link to it (prefetch, not prerender:
# the start page's typing and docking should run in view). Other browsers ignore the script.
SPECULATION = ('<script type="speculationrules">'
               '{"prefetch":[{"where":{"href_matches":"/*"},"eagerness":"moderate"}]}</script>')
```

- Speculation rules: a `<script type="speculationrules">` holds JSON, not a program. It tells the browser which pages it may load before the visitor clicks. `head()` writes it on every page, right after `THEME_BOOT` (section 14).
- `"prefetch"` – fetch the HTML of the next page and keep it ready; the click then shows it without waiting for the network. Not `"prerender"`, which would also run the page in a hidden tab: the start page's typing and docking would play out where nobody sees them.
- `"where":{"href_matches":"/*"}` – which links: every path on this site. In practice the links between pages – language switch, legal pages, the menu on the legal pages and the 404s. Links to other sites do not match, anchors within the page lead to no other document.
- `"eagerness":"moderate"` – when: once the pointer rests on a link for a moment (about 200 ms in Chrome) or presses it. `"eager"` would fetch every matching link at once, most of them for nothing.
- Chrome and Edge support it; other browsers do not know the script type and skip the element, as they skip the JSON-LD block.
- The JSON uses double quotes, so the Python literals use single quotes – the mirror image of `THEME_BOOT`.

The content security policy (section 30) allows inline scripts only by their hash. `csp_hash()` computes it:

```python
def csp_hash(tag):
    """'sha256-…' of an inline script's content – the content security policy allows exactly these two."""
    body = re.search(r"<script[^>]*>(.*)</script>", tag, re.S)[1]
    return f"'sha256-{base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()}'"
```

- `re.search(r"<script[^>]*>(.*)</script>", tag, re.S)[1]` – the text between the opening and the closing tag: `[^>]*` skips the opening tag's attributes (`type="speculationrules"`), `(.*)` captures the rest up to `</script>`, `re.S` lets `.` cross line breaks. `[1]` – group 1, as with the match object in `role()` (section 24). A tag without `<script>` gives `None`, and `None[1]` raises `TypeError` – loud.
- The hash covers exactly these characters, every space included. The browser hashes the script it received and compares; one changed character and the script counts as a violation.
- `hashlib.sha256(body.encode()).digest()` – the 32 raw bytes of the hash (not `hexdigest()`, the 64 hex characters of `VERSION`). `body.encode()` – the text as UTF-8 bytes, the encoding of the page.
- `base64.b64encode(…).decode()` – the bytes as 44 characters of Base64, the form the policy expects; `.decode()` turns the result from bytes back into a string.
- `f"'sha256-…'"` – the single quotes belong to the value: in a policy, `'sha256-…'` is a source keyword, like `'self'`.
- Computed from the constants `head()` writes, so the hashes follow every edit on the next build. Neither script contains ` · `, ` %` or ` €`, so `dots()` and `nbsp()` (section 29) leave them as they are.
- The JSON-LD block needs no hash: a script of type `application/ld+json` never runs, and the policy governs only scripts that run.

Right below it, the fingerprints of the two hand-written files:

```python
# ?v= after the stylesheet and the script: the first 8 hex digits of the file's SHA-256. A changed file gets a new
# address – browsers may keep each version for a year (.htaccess) and never pair a new page with an old stylesheet.
VERSION = {name: hashlib.sha256((SITE / "assets" / name).read_bytes()).hexdigest()[:8] for name in ("site.css", "site.js")}
```

- A dict comprehension: one entry per file name, for example `{"site.css": "5c417903", "site.js": "c18f8230"}`.
- `.read_bytes()` – the file as bytes, not text: the hash covers exactly what the server sends.
- `hashlib.sha256(…).hexdigest()` – 64 hex digits; `[:8]` keeps eight. 16⁸ is about 4.3 billion values – enough to tell two versions of one file apart.
- `head()` (section 14) and `script()` (section 15) append the value to the URL: `assets/site.css?v=5c417903`. The server ignores the query and sends the same file; for the browser's cache, another query is another address.
- Why a hash and not the build date: it changes only when the file changes. A rebuild for a copy edit keeps both addresses, so the copies browsers already hold stay valid.
- Why it matters: `.htaccess` lets browsers keep CSS and JS for a year without asking again (section 30). Without a new address, a visitor would get new HTML with last month's stylesheet.
- Pitfall: `VERSION` is computed when the module loads, from the files as they are on disk at that moment. Edit `site.css` or `site.js` first, build after. Build without an edit and the pages keep the old fingerprint – browsers that hold the old file keep using it.
- `SITE / "assets" / name` – the same `SITE` as in section 3, so this line has to come after it.

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
DOWN_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            '<path d="M8 2.5v10.7M3.4 8.8 8 13.4l4.6-4.6"/></svg>')
# ↗ after a link that leaves the site – the counterpart of the ledger's ↓
OUT_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
           '<path d="M4 12 12.5 3.5M6 3.5h6.5V10"/></svg>')
# the marks of the two Contact links that are not web pages: the address opens the mail program, the city a map
MAIL_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            '<path d="M1.8 3.6h12.4v8.8H1.8zM2.2 4 8 8.8 13.8 4"/></svg>')
PIN_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
           '<path d="M8 14.8C5.2 11.9 3.3 9.3 3.3 6.5a4.7 4.7 0 0 1 9.4 0c0 2.8-1.9 5.4-4.7 8.3z"/><circle cx="8" cy="6.5" r="1.6"/></svg>')
# three code lines, as in the minimap: the section menu before a chapter is reached, and without JavaScript
LINES_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
             '<path d="M2.5 4.5h11M4.5 8h9M2.5 11.5h7"/></svg>')
MOON_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            '<path d="M13.6 10.2A6 6 0 0 1 5.8 2.4a6 6 0 1 0 7.8 7.8z"/></svg>')

# The header logo: lockup ">_ P/S" ("Ein Takt", 25.10.2026), generated by src/lockup/lockup_takt50.py.
# Inline, so its two paths fill from --accent and --ink and follow light and dark. The paths sit in
# <g class="still">; site.js draws the condensing wordmark next to it while the name docks.
LOCKUP = re.sub(r"<svg ([^>]*)>(.*)</svg>",
                r'<svg class="lockup" \1><g class="still">\2</g></svg>',
                (Path(__file__).resolve().parent / "lockup" / "out" / "lockup.svg").read_text(encoding="utf-8").strip(),
                flags=re.S).replace('style="fill:var(--accent,#7A1A2C)"', 'class="acc"').replace('style="fill:var(--ink,#1A1C1E)"', 'class="ink"')
# (the inline fills become classes: site.css colours them, high-contrast mode can recolour them, no inline styles left)
```

- Inline SVG as strings, pasted straight into the HTML: no image requests, and the icons can take the text color.
- Why draw the arrow: the site font, Atkinson Hyperlegible, has no → glyph. The browser would borrow it from a fallback font with a different weight and baseline. Sun, moon, the two jump arrows and the three lines have no font equivalent anyway.
- `UP_SVG` and `DOWN_SVG` – the two ends of the jump control (section 23). `DOWN_SVG` also follows each company name in the results ledger, as a small superscript ↓ (section 25). It is `UP_SVG` mirrored: the shaft runs from y = 2.5 down to 13.2 (`v10.7` – a vertical line, relative), the head points down.
- `OUT_SVG` – the ↗ after every link that leaves the site (`offsite()`, section 20). `M4 12 12.5 3.5` draws the diagonal shaft from bottom left to top right; `M6 3.5h6.5V10` draws the head as a corner: along the top to the tip, then straight down. `V` is a vertical line to an absolute y, here 10. The comment calls it the counterpart of the ledger's ↓: the ↓ leads down the same page, the ↗ off it.
- `MAIL_SVG`, `PIN_SVG` – the marks of the other two Contact links, in the ↗'s place (section 25): an envelope after the address (it opens the mail program) and a pin after the city (it opens a map). The envelope is one path: `M1.8 3.6h12.4v8.8H1.8z` the outline – right, down, back left, `z` closes it – then `M2.2 4 8 8.8 13.8 4` the flap, a V from corner to corner. The pin is a drop – two cubic curves (`C`, `c`) down to the point at the bottom and an arc (`a4.7 4.7 0 0 1 9.4 0`) over the top – with a circle inside.
- `LINES_SVG` – three horizontal strokes of different lengths (`h11`, `h9`, `h7`), the second one indented: lines of code, like the bars of the minimap. It sits in the middle of the jump control as long as there is no chapter number to show – at the top of the page and without JavaScript.
- `viewBox="0 0 16 10"` – the internal coordinate system (16 × 10 units). The real size comes from CSS (`.arr` is 0.95em × 0.62em), so the icon scales with the text.
- `<path d="…">` – drawing commands. In the arrow: `M1 5` moves the pen to (1, 5), `h13.5` draws a horizontal line 13.5 units to the right (the shaft), `M10 1.2` jumps to the top of the head, `14 5` draws to the tip (coordinate pairs after an `M` count as line commands), `l-4 3.8` draws relative to the tip down to the bottom of the head. Uppercase = absolute coordinates, lowercase = relative.
- No `fill` or `stroke` in the markup: the CSS sets `fill: none; stroke: currentColor`, so every icon takes the current text color. Dark mode and hover colors work without a second set of icons.
- `aria-hidden="true"` – screen readers skip the drawing. The meaning comes from elsewhere: the arrow's word "to" in a visually hidden span next to it (section 13), the button's `aria-label`, the link text of the ledger's company names, the visually hidden "(opens in a new tab)" next to the ↗ (section 20).
- `focusable="false"` – Internet Explorer and old Edge put inline SVGs into the keyboard tab order. This switches that off; modern browsers ignore it.

**The logo** is the one SVG that is not typed in here. `LOCKUP` reads the lockup from its own folder, `src/lockup/`, where `lockup_takt50.py` builds it from the font (see `src/lockup/README.md`):

- `Path(__file__).resolve().parent / "lockup" / "out" / "lockup.svg"` – the file next to `build.py`, wherever you start the script from (the same trick as `SITE`, section 3).
- `.read_text(encoding="utf-8").strip()` – the file as a string, without the line break at its end.
- `re.sub(r"<svg ([^>]*)>(.*)</svg>", …, flags=re.S)` – rewrites the file in one step:
  - Group 1, `([^>]*)`, is everything inside the opening tag: its attributes (`viewBox`, `role="img"`, `aria-label="Peter Stieg"`). Group 2, `(.*)`, is everything between the tags: the two paths.
  - The replacement puts `class="lockup"` in front of the attributes and wraps the paths in `<g class="still">`. `\1` and `\2` insert the groups. The `r` in front of the string makes it a raw string: Python leaves the backslashes alone, and `re.sub` reads `\1` as "group 1". Without the `r`, Python would turn `\1` into a control character before `re.sub` ever saw it.
  - `re.S` lets `.` match line breaks too, in case the file ever spans several lines.
- Why the file stays untouched: it is the design's output. Regenerate it, rebuild, and the site has the new logo – no copying of path data.
- `.replace('style="fill:var(--accent,#7A1A2C)"', 'class="acc"')` and the same for `--ink` – the file fills its two paths with inline `style` attributes; the two calls swap them for the classes `acc` and `ink`. `site.css` already colours `.lockup .acc` and `.lockup .ink` for the condensing wordmark, so the same two rules now colour the logo: it follows light and dark like the text. Three gains, as the comment says:
  - one place for the colours, the stylesheet;
  - Windows high-contrast mode can repaint the logo in a system colour (chapter 3, High contrast) – an inline style would have to be outdone with `!important`;
  - no page carries an inline `style` attribute any more, so the content security policy can keep `style-src 'self'` without `'unsafe-inline'` (section 30).
- Pitfall: `replace` matches the exact text. A regenerated `lockup.svg` with another fallback colour or other spacing in the `style` keeps its inline fills – no error, and the policy reports two violations per page.
- The `.still` group is what `site.js` hides while it draws the condensing wordmark in the same SVG.

---

## 12 · sid, num, slugify, twins, href and page_id

```python
def sid(c, key):
    return c.get("ids", {}).get(key, key)


def num(key):
    """Chapter number of a section, '01'–'04': its own if it opens a chapter, else that of the chapter it belongs to."""
    for i, (first, rest) in enumerate(CHAPTERS.items(), 1):
        if key == first or key in rest:
            return f"{i:02d}"
    return ""
```

- "Section id": turns an internal section key into the anchor used in the HTML.
- `dict.get(k, default)` never raises; it returns `default` when `k` is missing.
- First `.get`: the `ids` dict, or an empty dict when the language has none (English).
- Second `.get`: the localized ID, or the key itself as fallback.
- Result: English → `"experience"`, German → `"werdegang"`. German visitors get German anchors (`/de/#werdegang`).
- The ids name what the section holds, in the page's language – the words a reader would type or a search engine reads in an address: `skills` / `kompetenzen` for P⁴, `languages` / `sprachen`, `sources` / `quellen`. Until 22.11.2026 P⁴ was `fields` / `p-wie-peter` and Sources `notes`: names from the code, not from the page.
- Pitfall: `nav` holds its own copy of these IDs. Rename an ID in `ids` without changing `nav` and the header link points to an anchor that no longer exists. No error – the link just stops scrolling.

`note_title` returns a footnote's title in the page language:

```python
def note_title(c, note):
    """A footnote's title in the page language – NOTES titles are a string or one per language."""
    return note["title"][c["lang"]] if isinstance(note["title"], dict) else note["title"]
```

- `isinstance(x, dict)` – true when `x` is a dict. Most titles are one string for both languages; only the IHK certificate has a German and an English name.
- Why not `title`: `head()` has a parameter called `title`, `legal()` a local variable of that name. Inside those functions it would hide a function of the same name – the same trap as `t` in `topbar` (section 17).

`num` gives a section its chapter number. Headings and menu both call it, so the two can never disagree.

- `CHAPTERS.items()` – the (key, list) pairs in order: `("profile", ["skills", "languages"])`, `("experience", ["education"])` …
- `enumerate(…, 1)` – counts along, starting at 1 instead of 0. Each round gets the number `i` and the pair, unpacked into `first` and `rest`.
- `if key == first or key in rest` – the section opens this chapter or belongs to it. `num("skills")`, `num("languages")` and `num("profile")` all return `"01"`.
- `:02d` – a format spec: an integer (`d`), at least two digits wide, padded with zeros (`0`). 1 becomes `01`.
- `return ""` – after the loop: a section in no chapter – Sources. `chapter_no()` (section 21) puts an invisible 00 in its place.

`slugify` and `twins` give the language switch something to land on (since 19.11.2026):

```python
def slugify(text):
    """An id from a name: lower case, umlauts spelt out, everything else one hyphen ("PRUEF+CHECK" → "pruef-check")."""
    text = text.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def twins(c, o):
    """Block ids on start page c → the same block's id on start page o, where they differ: the sections, every role,
    every project. The language switch carries the map; site.js opens the other page at the block being read."""
    projects = lambda x: [slugify(name) for _, items in x["groups"] for name, *_ in items]
    assert len(c["roles"]) == len(o["roles"]) and len(projects(c)) == len(projects(o)), "EN and DE must list the same blocks"
    pairs = [(sid(c, k), sid(o, k)) for k in SECTIONS] + [(a["id"], b["id"]) for a, b in zip(c["roles"], o["roles"])]
    pairs += list(zip(projects(c), projects(o)))
    assert all(re.fullmatch(r"[a-z0-9-]+", x) for pair in pairs for x in pair)   # safe inside a quoted attribute as they are
    return {a: b for a, b in pairs if a != b}
```

- `slugify(text)` – an id from a name, for the projects: "Customer portal" → `customer-portal`, "Kundenportal" → `kundenportal`, "PRUEF+CHECK" → `pruef-check`.
  - `str.maketrans({…})` plus `translate()` – replaces single characters by strings in one pass: ä → ae, ö → oe, ü → ue, ß → ss, as German spells them without umlauts. Lower case first, so capital umlauts need no entries.
  - `re.sub(r"[^a-z0-9]+", "-", text)` – every run of anything else – spaces, `+`, `·` – becomes one hyphen. `.strip("-")` drops hyphens at either end.
  - Not called `slug`: a slug is what it returns, and any local variable of that name would hide the function – `'str' object is not callable`.
- `twins(c, o)` – which block on page `o` is the same as each block on page `c`. Three kinds of block:
  - the sections: `sid()` gives each one's id in both languages – `experience` and `werdegang`;
  - the roles: paired by position, since both dicts list them in the same order (section 8);
  - the projects: their names slugified, the list flattened across the groups and paired by position. `for name, *_ in items` – the name, and the rest of the tuple into `_`, a throwaway.
- `projects = lambda x: …` – a function in one expression, named for the two calls on the next lines.
- `assert` – both pages must list as many roles and as many projects, or the pairs would shift. A failed assert stops the build with the message.
- The second `assert` – every id only lower-case letters, digits and hyphens: the map goes into a single-quoted HTML attribute without escaping (section 15), so nothing in it may end the attribute or start an entity. `re.fullmatch` – the whole string must match, not just a part of it.
- `{a: b for a, b in pairs if a != b}` – a dict comprehension that keeps only the ids that differ. Most role ids are company names, the same on both pages; `site.js` falls back to the id itself when the map has no entry. The map stays short: 15 entries instead of 25.

`href` and `page_id` – how one page names another (since 22.11.2026):

```python
def href(c, target):
    """target – an address from the site root: "", "de/", "de/impressum.html" – as a link on page c (c["path"]: its file),
    relative to the page's folder. A folder keeps its "/" ("./", "../", "de/"): the address the search engines know,
    and one entry per page in the statistics. The 404 pages answer at any address, so theirs start at the root."""
    if c["root"] == "/":
        return "/" + target
    rel = posixpath.relpath(target or ".", posixpath.dirname(c["path"]) or ".")
    return rel + "/" if not target or target.endswith("/") else rel


def page_id(path):
    """A page's id, its file name without .html: "de/impressum.html" → "impressum" – on the legal pages, the body's id."""
    return posixpath.basename(path)[:-5]
```

- Every internal link goes through `href()`: the header, the language switch, the footer. One rule instead of a prefix pasted in front of each – which had written `../de/impressum.html` where `impressum.html` says the same.
- `target` – where the link leads, written from the site root: `HOME[...]` for a start page (section 5), a path from `LEGAL` (section 26) for a legal page.
- `if c["root"] == "/"` – a 404 page: the server sends it for any missing address, `/de/a/b/c` included, so a link relative to its file would miss. From the root it always lands: `/de/`, `/de/impressum.html`.
- `posixpath.relpath(target, start)` – the path from the folder `start` to `target`, the way `cd` would walk it: from `de` to `privacy.html` is `../privacy.html`, from `de` to `de/` is `.`. `posixpath` – the module behind `os.path` on Linux and macOS, imported directly so the separator is always `/`, as in URLs, even when the build runs on Windows.
  - `posixpath.dirname(c["path"])` – the page's folder: `de` for `de/index.html`, `""` for `index.html`; `or "."` makes the empty one the current folder.
  - `target or "."` – the English start page's address is `""`, and `relpath` needs a path.
- `rel + "/"` – `relpath` drops the trailing slash of a folder; the link puts it back: `.` becomes `./`, `..` becomes `../`, `de` becomes `de/`. Without it, `/de` would cost a redirect to `/de/` (`mod_dir` does that) on every click.
- The results, from the English start page: `de/`, `privacy.html`; from the German one: `../`, `impressum.html`; from `de/impressum.html`: `./` (its start page), `../legal-notice.html` (its English twin).
- `page_id(path)` – `posixpath.basename` keeps the part after the last `/`, `[:-5]` drops `.html`. `legal()` gives the body `<div>` this id and `torch_map()` builds its selectors from it (sections 26, 28) – one function, so the two can't drift apart.

---

## 13 · t – escape, arrows, italics

```python
def t(c, text):
    """Escape, draw arrows, set *words* in italics (words cited as words, as in a dictionary)."""
    html = e(text).replace("→", f'<span class="arr">{ARROW_SVG}<span class="sr-only">{e(c["arrow"])}</span></span>')
    lang = ' lang="en"' if c["lang"] != "en" else ""
    return re.sub(r"\*([^*]+)\*", rf"<i{lang}>\1</i>", html)
```

- `t` for "text": the function for strings that may contain markers.
- First line, part one: `e(text)` escapes the copy. Escaping first and inserting markup second is the central pattern of the whole file. The reverse order would escape your own `<span>` into visible `&lt;span&gt;`. `e()` leaves `→` and `*` untouched, so the markers survive.
- First line, part two: `.replace("→", …)` swaps every arrow for a `<span class="arr">` holding two things: the SVG, which only draws, and the arrow's word in a `<span class="sr-only">` – "to", "auf" on the German page.
  - `sr-only` ("screen reader only") is a CSS class that shrinks an element to one clipped pixel: invisible on screen, but still text. The hero prompt uses the same class for the motto (section 25), `offsite()` for "(opens in a new tab)" (section 20).
  - Why text and not an `aria-label`: a label exists only for assistive technology. Screen readers would still say "€6k to €240k", but everything that reads the page as text – copy and paste, search engines, tools that extract a profile from a page – would get "€6k €240k". As text, the word is there for all of them.
  - Nested quotes: the f-string is delimited by single quotes, so `c["arrow"]` inside it uses double quotes. Before Python 3.12, an expression inside an f-string could not reuse the outer quote character. The file alternates quote types throughout and runs unchanged on Python 3.11.
  - Even the short word goes through `e()`: it is copy like any other.
- Second line: a conditional expression – `A if condition else B`. On non-English pages the italic words get `lang="en"`, because they are English words ("marketer", "tinkerer") and screen readers should pronounce them as such.
- Third line: `re.sub(pattern, replacement, string)` replaces every match.
  - Pattern `r"\*([^*]+)\*"`: `\*` is a literal asterisk (escaped, because `*` alone means "repeat"); `([^*]+)` captures one or more characters that are not asterisks as group 1; `\*` closes. Because `[^*]` cannot cross an asterisk, `*a* and *b*` yields two matches, not one long one.
  - Replacement `rf"<i{lang}>\1</i>"`: the `f` inserts `lang` now; the `r` (raw) keeps `\1` as backslash plus one, which `re` reads as "group 1". Without `r`, Python would turn `\1` into the invisible control character `chr(1)`.
- Pitfall: any two asterisks in a string passed to `t()` become italics. A single asterisk is fine.

---

## 14 · head

```python
def head(c, title, desc, canonical, alternates=True, root=None):
    """alternates: the same page in every language – True for the start pages, a dict (code → path) for another
    pair, False for none (404)."""
    r = c["root"] if root is None else root
    alt = ""
    if alternates:
        paths = alternates if isinstance(alternates, dict) else HOME
        alt = "".join(f'<link rel="alternate" hreflang="{code}" href="{URL}{paths[code]}">\n' for code, *_ in LANGS)
        alt += f'<link rel="alternate" hreflang="x-default" href="{URL}{paths["en"]}">\n'
        alt += "".join(f'<meta property="og:locale:alternate" content="{CONTENT[code]["locale"]}">\n'
                       for code, *_ in LANGS if code != c["lang"])
    return f"""<!doctype html>
{SOURCE_NOTE}
<html lang="{c['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
{THEME_BOOT}
{SPECULATION}
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
<meta property="og:image:alt" content="{NAME} · {TAGLINE} · {CLAIM}">
<meta property="og:locale" content="{c['locale']}">
<meta property="profile:first_name" content="Peter">
<meta property="profile:last_name" content="Stieg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}favicon.ico" sizes="16x16 32x32 48x48">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
<link rel="manifest" href="{r}site.webmanifest">
<link rel="preload" href="{r}assets/fonts/atkinson-hyperlegible-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{r}assets/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{r}assets/site.css?v={VERSION['site.css']}">
"""
```

Signature and setup:

- `alternates` – three kinds of value, as the docstring says: `True` – the start pages, which list their language versions from `LANGS`; a dict code → path – another pair, the legal pages (section 26); `False` – none, the two 404s.
- `root=None` – `None` means "not given". The default could not be `""`, because `""` is a real root value (the English page). `r = c["root"] if root is None else root` takes the caller's value only when one was passed.
- `alt = ""` – stays empty when `alternates` is false.

The alternates block:

- `paths = alternates if isinstance(alternates, dict) else HOME` – one dict code → path either way: the one passed in, or the start pages (`{"en": "", "de": "de/"}`, section 5). The lines after it no longer need to know which kind of page they serve.
- `"".join(f'…' for code, *_ in LANGS)` – a generator expression inside `join()`. It produces one `<link>` per language, one at a time; `"".join` glues them with no separator. The order comes from `LANGS`, the path from `paths[code]`.
- `hreflang` links tell search engines "this page exists in English at …, in German at …". Every language version lists all versions, itself included.
- `x-default` – the version for visitors whose language matches none of the listed ones: always the English one – `paths["en"]`, the root for the start pages, `legal-notice.html` and `privacy.html` for the legal pages.
- Pitfall: a dict must name every language in `LANGS`. A missing code raises `KeyError` – loud, at build time.
- `og:locale:alternate` – the other languages' locales for social platforms. `for code, *_ in LANGS` is star unpacking: the first value goes into `code`, the rest into a throwaway list. `if code != c["lang"]` filters out the current language. `CONTENT[code]["locale"]` reads from the *other* language's dict.
- `+=` on strings creates a new string each time. Fine for three operations; for many pieces, collect in a list and join once (as `page()` does).

The returned document head, top to bottom:

- `<!doctype html>` – switches browsers into standards mode. It must come first.
- `{SOURCE_NOTE}` – the greeting comment.
- `<html lang="{c['lang']}">` – the page language: screen-reader pronunciation, hyphenation, translation offers, spell-check. Single quotes inside a triple-double-quoted f-string – no conflict.
- `<meta charset="utf-8">` – how to decode the bytes; must sit within the first 1024 bytes (section 9).
- `viewport` – on phones, lay the page out at device width instead of a zoomed-out desktop width.
- `color-scheme` with `light dark` – the page supports both schemes, so the browser draws its own parts (scrollbars, the canvas, form controls) in the system's scheme from the first byte on, before the stylesheet has arrived. It must come before `THEME_BOOT`, which narrows it to a stored pick (section 10); `site.js` keeps it in line afterwards.
- `{THEME_BOOT}` – the theme script, before the stylesheet (section 10).
- `{SPECULATION}` – the prefetch rules (section 10). Data, not a program: its place in the head costs nothing.
- `<title>{e(title)}</title>` – tab title and search-result headline, escaped.
- `description` – often shown as the snippet in search results. Escaped, because it sits inside an attribute.
- `author` – the author's name.
- `canonical` – the preferred URL of this page. It merges duplicates such as `/de/` and `/de/?utm_source=linkedin` into one address for search engines; `/de/index.html` no longer reaches the page – `.htaccess` forwards it (section 30).
- `{alt}<meta name="theme-color"…` – `alt` either ends with `\n` or is empty, so the output never gets a blank line.
- `theme-color` twice, with `media` – the browser UI color (for example the address bar on phones) for a light and a dark system setting. `site.js` writes the picked color into both while a pick stands, and each tag's own color back when it is released. The two hex values also exist in `site.css` and `site.js` – change all three together.
- `og:*` – Open Graph: what LinkedIn, Slack, WhatsApp and others show when the link is shared. `og:image` must be an absolute URL, because crawlers do not resolve relative paths. `width` and `height` let the platform lay out the preview before the image arrives.
- `profile:first_name`, `profile:last_name` – Open Graph fields for the `profile` type.
- `twitter:card` – asks X for a large image preview; title, description and image fall back to the `og:*` values.
- Three icon lines, all with `{r}` – relative to where the page lives. All three files are drawn from the "PS" monogram – paper letters on a bordeaux disc – and made in `src/monogram/`, not here (section 30).
  - `favicon.ico` with `sizes="16x16 32x32 48x48"` – the classic format: one file that holds several bitmaps, here 16, 32 and 48 pixels; `sizes` names all three. The 16 and 32 pixel versions are drawn by hand on the pixel grid, which stays sharper in a browser tab than any automatic downscaling of the vector. Every browser takes an ICO, and some programs ask for `/favicon.ico` directly without reading the page at all – feed readers, bookmark services.
  - No link to `favicon.svg`: a browser that supports SVG favicons prefers the SVG whenever both are linked, and at 16 pixels the vector comes out soft. Without the link, Chrome and Firefox use the hand-drawn pixels – 16 in a tab on an ordinary screen, 32 on a high-density one. The SVG stays in `site/` as the vector version of the icon.
  - `apple-touch-icon` – the icon iOS shows when someone adds the page to the home screen: a 180 × 180 pixel PNG, because iOS takes neither the SVG nor the ICO here. The paper PS on a full-bleed bordeaux square; iOS rounds the corners itself.
  - `manifest` – `site.webmanifest`, a small JSON file that describes the site as a web app: its name, a short name, the colors, and two more icons (192 and 512 pixels). Android and Chrome take their home-screen and install icons from it. Its `"display": "browser"` keeps the site an ordinary page in a browser tab even when opened from the home screen – the manifest is here for the icons, not to turn the site into an app.
- `rel="preload"` for two font files – starts the download immediately instead of after the CSS has been parsed and the fonts discovered there. `crossorigin` is required: fonts are always fetched in CORS mode, and a preload without it does not match the real request, so the font would download twice. The italic file is not preloaded; it is only needed for a few words.
- `<link rel="stylesheet">` – the CSS, deliberately after `THEME_BOOT`. `?v={VERSION['site.css']}` – its fingerprint (section 10); single quotes inside the triple-double-quoted f-string.
- No `</head>` at the end. Callers add more first (JSON-LD, `robots` meta) and close the head themselves. If you write a new page function, you must close it.

---

## 15 · script and lang_switch

```python
def script(r):
    return f'<script src="{r}assets/site.js?v={VERSION["site.js"]}" defer></script>\n'
```

- The script tag of every page, with the fingerprint of `site.js` (section 10). One function instead of three copies of the line in `page()`, `legal()` and `not_found()`.
- `r` – the root prefix, `c["root"]` on every page: `""` and `"../"` on the start pages and the legal pages – the German ones sit in `de/` –, `"/"` on the 404s.
- `VERSION["site.js"]` – double quotes inside, because the f-string is delimited by single quotes (section 13).

```python
def lang_switch(c, paths=None, start=False):
    """EN · DE – the current language is marked, the other links to the same page in that language.
    paths: code → address from the site root; without it, the start pages. start: on a start page the link carries the
    map of block ids (twins), so site.js can open the other page where the reader is."""
    paths = paths or HOME
    items = []
    for code, label, name, _ in LANGS:
        if code == c["lang"]:
            items.append(f'<span aria-current="page" title="{name}">{label}</span>')
        else:
            tw = f" data-twins='{json.dumps(twins(c, CONTENT[code]), separators=(',', ':'))}'" if start else ""
            items.append(f'<a href="{href(c, paths[code])}" hreflang="{code}" lang="{code}" title="{name}"{tw}>{label}</a>')
    return f'<span class="langs" role="group" aria-label="{e(c["aria_lang"])}">{" ".join(items)}</span>'
```

- The docstring names the two current languages. The output itself follows `LANGS`, so a third entry there would appear in the switch automatically.
- `paths` – where each language's version of this page lives, from the site root. The legal pages pass their pair (`{"en": "legal-notice.html", "de": "de/impressum.html"}`, section 26); the start pages and the 404s pass nothing.
- `paths = paths or HOME` – `or` returns its left side if that is truthy, else its right side. `None` (and an empty dict) are falsy, so a call without `paths` gets the start pages (section 5).
- `items = []` plus `append` – an explicit loop, because each language takes one of two shapes.
- `for code, label, name, _ in LANGS` – full unpacking; the start page's address is not needed here – the address comes from `paths`.
- Current language: a `<span>`, not a link – a link to the page you are on is noise. `aria-current="page"` tells screen readers "this is the current one"; the CSS rule `.langs [aria-current]` sets it in bold.
- Other languages: `<a href="{href(c, paths[code])}">` – the address as seen from this page (section 12): from the English start page `de/`, from the German one `../`, from `legal-notice.html` `de/impressum.html`, from `de/impressum.html` `../legal-notice.html`, from the English 404 `/de/` (root `"/"`, section 27). `hreflang` states the language of the target page; `lang` the language of the link text itself; `title` shows the full name on hover.
- `start` – on a start page the link carries `data-twins`: the map of block ids from this page to the other (`twins()`, section 12). `site.js` adds the id of the block being read to the link's address, so the other page opens there (chapter 4). The legal pages and the 404s pass no `start`: they have no blocks to keep.
  - `json.dumps(…, separators=(',', ':'))` – compact JSON, without the spaces after `,` and `:`.
  - Single quotes around the attribute value: the JSON is full of double quotes, which would otherwise need escaping as `&quot;` – three times longer. Safe, because `twins()` asserts that every id is lower-case letters, digits and hyphens: no `'`, no `&`, no `<`.
  - Outside an f-string with single quotes the attribute would read more simply; here the f-string itself uses double quotes, so the `','` and `':'` inside are fine on every Python version.
- The wrapper: `role="group"` with `aria-label` lets a screen reader announce "Language, group" before the links.
- `{" ".join(items)}` – an expression inside the f-string. Double quotes inside, single quotes outside.
- The space between the items is there for the text, not for the eye. Without it, copied or extracted text reads "ENDE"; with it, "EN DE". On screen it changes nothing: `.langs` is an inline flex container, and a flex container ignores text that is only whitespace. The visible spacing comes from CSS padding. No separator characters such as `|` – the CSS draws the pill around both.

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
def topbar(c, start=True, langs=True):
    """The header, the same on every page. start: a start page – the menu jumps within it, the hero's name docks into
    the logo; on the other pages the menu leads to the start page's sections.
    langs: True – the switch to the other start page; a dict (code → path) – to that page; False – no switch."""
    to = "" if start else href(c, HOME[c["lang"]])    # the start page the menu's sections are on
    keys = {sid(c, k): k for k in CHAPTERS}          # localized id → section key, for the number
    # number as on the heading; data-label: CSS reserves the bold width, so marking the current section does not shift the menu
    links = "\n".join(f'<a class="sect" href="{to}#{i}"><span class="no" aria-hidden="true">{num(keys[i])}</span> '
                     f'<span class="label" data-label="{e(t)}">{e(t)}</span></a>' for i, t in c["nav"])
    switch = lang_switch(c, langs if isinstance(langs, dict) else None, start) if langs else ""
    # the wordmark the hero name docks into – invisible, it only gives site.js the target to measure
    word = f'<span class="word" aria-hidden="true"><span class="caret">&gt;_</span><span class="name">{NAME}</span></span>' if start else ""
    return f"""<a class="skip" href="#main">{e(c['skip'])}</a>
<header class="top">
<div class="wrap">
<a class="home" href="{'#top' if start else to}">{word}{LOCKUP}</a>
<nav class="nav" aria-label="{e(c['aria_main'])}">{links}
{switch}
{theme_switch(c)}</nav>
</div>
</header>
"""
```

- One header for every page: logo, the four chapters, language switch, theme switch. Two switches set what differs:
  - `start` – a start page (`True`, the default) or not. On a start page the menu jumps within the page and the logo to the hero; on the legal pages and the 404s both lead to the start page of the page's language. Before 13.11.2026 the parameter was called `sections`, and `False` dropped the menu: on the legal pages and the 404s, the logo was the only way to a chapter.
  - `langs` – which language switch: `True` (the default) the other start page, a dict the given pages, `False` none. The start pages and the 404s take the default; the legal pages pass their pair. `False` is no longer passed anywhere.
- `to = "" if start else href(c, HOME[c["lang"]])` – the page the menu's sections are on: nothing on a start page, so the links stay in-page anchors; elsewhere the start page of the page's language, as `href()` writes it (section 12) – `./` on every legal page (the English ones sit next to `index.html`, the German ones next to `de/index.html`), `/` and `/de/` on the 404s.
- `keys` – a dict comprehension that turns the lookup around. `nav` holds the localized ids (`"werdegang"`), `num()` needs the section key (`"experience"`). Looping over `CHAPTERS` loops over its keys – the four sections the menu links to. So `keys` maps each id back to its key: `{"profil": "profile", "werdegang": "experience", …}` on the German page; in English, id and key are the same.
- `links = "\n".join(…)` – the four menu links, on every page.
  - `"\n"` – a line break between the links. Like the space in the language switch (section 15), it is there for the text: the number span has no space before it, so without a separator the menu's text reads "01 Profile02 Experience". With it, copy and paste and search engines get "01 Profile 02 Experience …".
  - Two f-strings in a row, without a `+` between them, are joined into one string by Python itself. That splits a long line without changing the result.
  - `for i, t in c["nav"]` – unpacks each (id, label) pair. Here `t` is a loop variable that shadows the function `t()`. It works because a generator expression has its own scope – outside it, `t()` is untouched – but it is confusing. Do not copy the pattern.
  - `href="{to}#{i}"` – an in-page anchor on a start page (`#profile`), the start page plus the anchor elsewhere (`./#profile`, `/de/#werdegang`). `site.js` marks the chapter being read only where its section is on the page: on the other pages the links find no target, and nothing is marked (chapter 4, You are here).
  - `<span class="no" aria-hidden="true">{num(keys[i])}</span>` – the chapter number, the same as on the heading: "01 Profile", "02 Experience". Hidden from screen readers, so the link is still called "Profile".
  - `<span class="label" data-label="{e(t)}">` – the label in its own span, plus a copy as a data attribute. `site.js` marks the section being read in bold; the CSS uses the copy to reserve the bold width in advance (chapter 3, Navigation). The span is needed because the trick works on the label alone – the number stays regular.
- `switch = lang_switch(c, langs if isinstance(langs, dict) else None) if langs else ""` – the same pattern, one level deeper: no switch for `False`; for a dict, the dict goes on as `paths`; for `True`, `None` – links to the start pages, the switch on the start pages and the 404s.
- The skip link comes first in the page so it is the first thing the Tab key reaches. CSS keeps it off-screen until it receives keyboard focus; it jumps to `<main id="main">`.
- `<header class="top">` and `<div class="wrap">` – the page header and a width-limiting layout container.
- The home link: `{'#top' if start else to}` – a full conditional expression inside a replacement field. On a start page it jumps to the hero (`#top`). On other pages it links to the start page of the page's language, the address of the menu links without their anchor: `./` on the legal pages, `/` or `/de/` on the 404s.
- `{word}{LOCKUP}` – the link holds two things:
  - `word` – the old wordmark `>_ PETER STIEG`, on the start pages only. The CSS keeps it invisible; it is the target the hero name flies into, because `site.js` measures where its letters sit. `aria-hidden` on the whole span, so screen readers do not read "greater than underscore Peter Stieg" twice.
  - `LOCKUP` – the logo `>_ P/S` (section 11), on every page. Its `role="img"` and `aria-label="Peter Stieg"` give the link its name: screen readers say "Peter Stieg, link".
  - `&gt;_` – `>` written as an entity, so the parser cannot mistake it for the end of a tag.
- `<nav aria-label=…>` – a named navigation landmark. The name matters because the page has two navs (header and footer).
- `{links}`, `{switch}` and `{theme_switch(c)}` on lines of their own – the same whitespace for the same reason: "Contact EN DE" instead of "ContactENDE". `.nav` is a flex container, so the line breaks do not move anything; the gaps between the items come from `gap` in the CSS.

---

## 18 · footer

```python
def footer(c):
    """The legal pages in the page's language."""
    L = c["lang"]
    return f"""<footer class="foot">
<div class="wrap">
<nav aria-label="{e(c['aria_legal'])}">
<a href="{href(c, LEGAL['imprint'][L][0])}">{e(c['imprint'])}</a>
<a href="{href(c, LEGAL['privacy'][L][0])}">{e(c['privacy'])}</a>
<span>© {date.today().year} {NAME}</span>
</nav>
</div>
</footer>
"""
```

- The footer holds the legal links and the copyright line, nothing else, all inside one `<nav>`.
- `LEGAL['imprint'][L][0]` – the legal notice in the page's language: `LEGAL` maps page and language to (path, title, body) (section 26), `[0]` is the path. English pages link `legal-notice.html` and `privacy.html`, German pages `de/impressum.html` and `de/datenschutz.html`.
- `href()` (section 12) writes the address as seen from this page: `impressum.html` on the German start page and on the German legal pages, which share its folder, `/de/impressum.html` on the German 404. No `hreflang`: link and target share the page's language.
- `LEGAL` is defined much further down the file. That works: Python looks a global name up when the function runs, not when it is defined, and `footer()` first runs from `build()`, after the whole module has loaded.
- `© {date.today().year}` – evaluated when you build, not when someone visits. The year changes only when you rebuild; a page built in December still shows the old year in January until the next build.

---

## 19 · jsonld and torch_data

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
            {"@type": "EducationalOccupationalCredential", "name": note_title(c, n), "url": n["verify"],
             "recognizedBy": {"@type": "Organization", "name": n["by"]}}
            for n in NOTES.values() if n.get("verify")
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>\n"
```

- JSON-LD ("JSON for Linked Data") – machine-readable facts about the page's subject, using the schema.org vocabulary. Search engines read it; visitors never see it.
- The Python dict mirrors the JSON structure one to one. `"@context"` names the vocabulary, `"@type"` the kind of thing described – a `Person`.
- `jobTitle` and `description` come from `c`, so each language version describes the person in its own language.
- `"address"` – a nested object with its own `@type`. City and country only.
- `"sameAs"` – other profiles of the same person; this ties the site to LinkedIn and GitHub.
- `"hasCredential"` – a list comprehension: `[{…} for n in NOTES.values() if n.get("verify")]` builds one credential object per footnote that has a verification page – the videos have none and are left out. Dicts keep insertion order (guaranteed since Python 3.7), so the order is always that of `NOTES`: Data Scientist, MLOps Engineer, IHK, edX.
  - `note_title(c, n)` – the credential's name in the page language.
  - `n["by"]` – who stands behind it: the Sorbonne for the Liora certificates, the IHK-Projektgesellschaft for the IHK course, Microsoft for the edX course.
- `json.dumps(data, ensure_ascii=False)` turns the dict into JSON text. The default (`ensure_ascii=True`) would write `"Università"`; `False` keeps `"Università"`. Both are valid JSON; the second is shorter and readable, and safe because the file is written as UTF-8.
- Why no `e()` here: the content of a `<script>` element is raw text. The browser does not decode entities inside it, so `&amp;` would land literally in the JSON.
- Pitfall: `json.dumps` does not protect against the sequence `</script>`. A string containing it would close the script element early. All values here are your own constants, so it cannot happen today. If outside data is ever fed in, replace `"</"` with `"<\/"` in the output.

The torch's strings go into the page as JSON too, in an attribute:

```python
def torch_data(c):
    """data-torch on <main>: the torch's strings for site.js (sudo, ?), as JSON in an attribute – out of the page's text."""
    return f' data-torch="{e(json.dumps(c["torch"], ensure_ascii=False))}"'
```

- The strings of the torch (chapter 4) in the page's language: the line under the light and the card that `?` or F1 opens, from `CONTENT["torch"]` (section 8).
- `page()`, `legal()` and `not_found()` write it into `<main id="main"{torch_data(c)}>` – all eight pages carry it, and `site.js` starts the torch wherever it finds the attribute.
- The leading space belongs to the attribute string, the convention of `rid` and `en_attr` (section 25).
- `json.dumps(…, ensure_ascii=False)` – the dict as JSON text, umlauts as they are rather than `\u00fc`. `e()` then escapes it for the attribute: every `"` becomes `&quot;`, and the browser turns them back before `site.js` reads `dataset.torch` and parses it with `JSON.parse`. Unlike the JSON-LD above, this JSON sits in an attribute, where entities are decoded – so here `e()` is required.
- Why an attribute and not hidden elements: the page's text stays what it says. A card with "sudo – HTML · build.py · off" in the HTML would end up in what search engines and parsers read; an attribute does not ("Plain text that reads right", decisions.md).
- The attribute is in the body, so `dots()` (section 29) reaches it like everything else there: the `·` in the strings arrive with a no-break space before them – in the card, too, a dot never starts a line.

---

## 20 · offsite – links that leave the site

```python
def offsite(c, url, text, attrs="", mark=OUT_SVG, kind=""):
    """A link that leaves the site: opens in a new tab, so the page stays open behind it. Marked with ↗ for the eye and
    "(opens in a new tab)" for screen readers. The last word and the ↗ share a no-wrap span: the arrow never starts a
    line on its own. attrs: extra attributes, written as they are (' hreflang="en"', ' rel="me noopener"').
    mark, kind: another mark in place of the ↗ and what it stands for, read out first ("map, opens in a new tab")."""
    rel = "" if "rel=" in attrs else ' rel="noopener"'
    lead, space, last = text.rpartition(" ")
    said = f"{e(kind)}, {e(c['new_tab'])}" if kind else e(c["new_tab"])
    sym = " sym" if kind else ""                      # a drawn symbol, larger than the ↗ to stay legible
    return (f'<a href="{url}" target="_blank"{rel}{attrs}>{lead}{space}<span class="nw">{last}<span class="newtab{sym}">{mark}'
            f'<span class="sr-only"> ({said})</span></span></span></a>')
```

- Every link that leaves the site goes through this function – 27 per page: fourteen in Experience – seven company websites and the two Liora course pages in the roles, five of the six early positions (section 24) –, GitHub and Demo for the two capstones in Projects, LinkedIn, GitHub and the map in Contact, "Verify credential" and "Course page" in Sources (section 25). Links within the site stay in the same tab: the menu, the language switch, the ledger's company names, the footnotes, the legal pages. So does the mail link, which opens a mail program, not a page.
- Why a new tab: whoever checks a certificate or a company website keeps the page open behind it and returns to the same spot. The marker announces the new tab before the click, for the eye (↗) and for screen readers (the hidden words).
- The parameters:
  - `url` – inserted as it is. Every URL is one of your own constants.
  - `text` – HTML, not plain copy, like `title_html` in `section()` (section 22): callers pass `e(…)`, or a constant without special characters such as `"LinkedIn"`.
  - `attrs` – further attributes as one string with a leading space, written into the tag as they are – the convention of `rid` and `en_attr` (section 25). Empty by default.
  - `mark`, `kind` – a different mark in place of the ↗, and the word for what it stands for. Only the map under Contact passes them: `mark=PIN_SVG, kind=c["map"]`. Keyword arguments with defaults, so every other call stays as it is.

The `rel` attribute:

- `rel = "" if "rel=" in attrs else ' rel="noopener"'` – the default, unless the caller brings its own. `in` on two strings is a substring test. An attribute may appear only once per tag – with two, the browser keeps the first and ignores the second – so a caller's `rel` replaces the default instead of joining it. That is why Contact passes `' rel="me noopener"'`: `rel` takes a list of words separated by spaces, so the one attribute keeps `me` (section 25) and names `noopener` itself.
- `noopener` – `target="_blank"` opens the URL in a new tab. Without `noopener`, the new page used to get `window.opener`, a reference back to the tab that opened it, and could send that tab to another address – "reverse tabnabbing": the visitor returns to the old tab and finds a lookalike page in place of peterstieg.com. `noopener` cuts the reference: `window.opener` is `null`. Current browsers apply it to every `target="_blank"` by default; the attribute covers older ones and states the intent in the markup.
  - Not `noreferrer`: the target site still learns where the visitor came from, as far as the referrer policy allows – `.htaccess` sets `strict-origin-when-cross-origin`, so another site learns `https://peterstieg.com/`, not the page or the anchor (section 30).
- Pitfall: a substring test is blunt. `' hreflang="en"'` passes safely ("ref" is not "rel"), but any attribute that contains `rel=` – `data-rel="…"`, a `title` that mentions it – drops the default without a word, and the link loses its `noopener`.

The text and its marker:

- `lead, space, last = text.rpartition(" ")` – `rpartition` is `partition` (section 29) from the right: it splits at the last space into before, the space itself, after. `"YOUniversal Media"` gives `("YOUniversal", " ", "Media")`. Without a space, the whole text lands in the last part: `"Posterlounge"` gives `("", "", "Posterlounge")` – the mirror image of `partition`, which puts it in the first. For a single word `{lead}{space}` is empty and the whole word goes into the span; no special case needed.
  - `lead`, not `head`: a local `head` would hide the function `head()` inside `offsite()` – the trap `dots()` avoids with `head_part` (section 29).
- `<span class="nw">{last}…</span>` – the last word and the marker share one span, which the CSS sets to `white-space: nowrap` (chapter 3). The line may still break before the last word, never between it and the ↗. Without the span, the ↗ wrapped onto a line of its own at widths of 320 to 390 pixels: the marker is an inline-block, and an inline-block is a break opportunity on both sides. A word joiner (U+2060) between word and arrow did not stop the break in Chromium – measured.
- `<span class="newtab{sym}">{mark}…</span>` – the ↗ (section 11), or the symbol passed in `mark`. The CSS keeps it deliberately quiet: smaller than the ledger's ↓ (0.55em against 0.6em), raised like it (`position: relative; top: -0.5em` – the box stays on the baseline, so the line height does not change) and muted, in the accent color only on hover and keyboard focus (chapter 3). With twenty-six per page – the map's pin is the twenty-seventh mark –, a louder marker would clutter the page. The vocabulary: accent superscripts – the footnote numbers and the ↓ – stay on the page; the muted ↗ leaves it.
- `said` – what screen readers hear: `new_tab` alone, or `kind` in front of it – "Leipzig (map, opens in a new tab)". Both escaped, because both are copy.
- `sym` – the class `sym` next to `newtab` when a symbol stands in for the ↗. The CSS draws a symbol larger, with a thinner line, so its detail stays legible at the size of a superscript and its strokes look as heavy as the arrow's (chapter 3). In `{mark}` the f-string inserts the SVG unescaped – it is markup, a constant.
- `<span class="sr-only"> ({said})</span>` – the words from `new_tab` (section 8), visually hidden (section 13), so the link's name for screen readers becomes "Posterlounge (opens in a new tab)". The space at the start of the span keeps the name from running into the parenthesis. Text, not an `aria-label`, for the same reason as the arrow's word in `t()`; escaped, because it is copy.
- Pitfall: `rpartition` sees characters, not markup. A `text` with a tag that has a space in it (`<i lang="en">`) would be split inside the tag, and the span would cut it in two. All link texts today are plain escaped copy.

The name:

- Why not `out()`: `page()` collects its HTML in a local list called `out` (section 25). Inside `page()`, that name means the list, so a call `out(c, url, text)` there would raise `TypeError: 'list' object is not callable`. Projects, Contact and Sources call the helper from inside `page()`. Hence `offsite` – the trap of `t` in `topbar()` (section 17), avoided before it happens.

---

## 21 · chapter_no

A small helper for headings: the chapter number in front.

```python
def chapter_no(key):
    """The number before a section title: visible if the section opens a chapter, invisible (.ghost) for the rest,
    so the titles line up. Sources, in no chapter, hold the place with 00 – site.js marks no chapter there."""
    ghost = "" if key in CHAPTERS else " ghost"
    return f'<span class="no{ghost}" aria-hidden="true">{num(key) or "00"}</span> '
```

- The number before a section title, as a finished span. Two places show it: the section headings (`section()`, section 22) and the list in the jump control (section 23). Both call this one function, so the two can never disagree.
- `ghost` – a second class for the sections that do not open a chapter (P⁴, Languages, Education, Sources). `key in CHAPTERS` checks the dict's keys only, so it is true just for the four chapter openers.
- The span holds the number from `num(key)` (section 12). P⁴ gets `<span class="no ghost">01</span>`: the number of its chapter, which the CSS makes invisible. It still takes up its width, so "P⁴" starts exactly where "Profile" does – an outline, without any measuring.
  - `num(key) or "00"` – Sources belong to no chapter, and `num()` returns `""`. `or` takes the right side when the left is empty: an invisible `00` keeps "Sources" in line with every other title, in the headings and in the jump control's list. Visible, it would read as a chapter before 01; hidden, it only holds the place. `site.js` reads the 00 as "no chapter": the menu marks none while Sources are read, and the jump control shows its section icon instead of a number (chapter 4, You are here).
  - `aria-hidden="true"` – screen readers skip the number and announce "Profile", not "zero one Profile". The number is a visual signpost; the order of headings already carries the structure.
  - The space after `</span>` sits outside the span, so the plain text of the heading still reads "01 Profile" for search engines and copy-paste.

---

## 22 · section, tree, months and duration

```python
def section(c, key, title_html, body, cls="body"):
    i = sid(c, key)
    return f"""<section class="sec" id="{i}" aria-labelledby="h-{i}">
<h2 id="h-{i}">{chapter_no(key)}{title_html}</h2>
<div class="{cls}">
{body}</div>
</section>
"""
```

- The wrapper for every content section of a start page.
- `cls="body"` – a default parameter: used when the caller passes nothing. No caller currently passes another value.
- `i = sid(c, key)` – the localized anchor.
- `aria-labelledby="h-{i}"` – points at the heading's id: the text of the `<h2>` becomes the section's name, and a named `<section>` is exposed as a landmark that screen-reader users can jump between. The heading holds the number, hidden from screen readers (section 21), and the title, nothing else – so each section is called by its title: "Projects".
- The footnote references use the same id: their `aria-describedby` points at the Sources heading, `h-quellen` on the German page (section 25).
- `{chapter_no(key)}{title_html}` – number, then title (section 21).
- `title_html` – the name says it: raw HTML, inserted unescaped. Callers pass `e(s["profile"])` and so on, or `title_of()` for P⁴ (section 23), which returns markup. Pitfall: pass plain copy here without `e()` and the first `&` breaks the markup.
- `{body}</div>` – every caller's body ends with `\n`, so `</div>` lands on its own line.

```python
def tree(c, rows):
    lang = ' lang="en"' if c["lang"] != "en" else ""
    items = "".join(f'<li><span class="k"{lang}>{e(k)}:</span> {t(c, v)}</li>' for k, v in rows)
    return f'<ul class="tree">{items}</ul>' if rows else ""
```

- Renders a role's `tree` list (the #JobAlert format) as `<ul class="tree">`.
- `lang` – labels such as "Scope" stay English and are marked as such on the German page.
- `for k, v in rows` – each row is a (label, text) pair, unpacked in the generator.
- The label goes through `e()`, the text through `t()` – so arrows and italics work in the text.
- `if rows else ""` – a role with nothing to list gets no list at all. Every role has at least one row today; the check keeps a `"tree": []` harmless. An empty `<ul></ul>` would be valid HTML, but a screen reader may still announce "list, 0 items", and the list's margin would leave a gap.
- `{e(k)}:` – the colon after the label is part of the text, inside the bold span. It could come from the CSS (`content: ":"`), but generated content is not part of the page's text: copied or extracted, the line would read "Scope SEA, social media …" with nothing between label and text. The CSS only draws the branch lines, with `::before` and `::after` on each `<li>` – lines are presentation, the colon is punctuation.

```python
def months(when):
    """Length of a role in months, counted like LinkedIn: first and last month included (10/2017 – 06/2023: 69).
    "since 11/2025" runs to the build date; site.js recounts it when the page loads."""
    dates = [(int(y), int(m)) for m, y in re.findall(r"(\d{2})/(\d{4})", when)]
    if not dates:                                      # years only, "2013 – 2020": January to December
        dates = [(int(y), m) for y, m in zip(re.findall(r"\d{4}", when), (1, 12))]
    if len(dates) == 1:                                # "since 11/2025" runs to today; "09/2014" is one month
        dates.append((date.today().year, date.today().month) if not when[:1].isdigit() else dates[0])
    (y1, m1), (y2, m2) = dates
    return (y2 - y1) * 12 + m2 - m1 + 1
```

- The length of a role in months, read from its `when` string. `role()` and `steps()` (section 24) print it under the dates.
- Counted like LinkedIn: the first and the last month both count. 10/2017 – 06/2023 is (2023 − 2017) × 12 + 6 − 10 + 1 = 69 months. Without the `+ 1`, the result is the number of steps from one month to the other, 68 – and a role from 03/2025 to 03/2025 would last zero months.
- `re.findall(r"(\d{2})/(\d{4})", when)` – every date in the string:
  - `\d` is one digit, `{2}` exactly two of them, `/` a literal slash, `\d{4}` four digits. The parentheses make month and year two groups.
  - With groups in the pattern, `findall` returns one tuple of the groups per match: `"10/2017 – 06/2023"` gives `[("10", "2017"), ("06", "2023")]`, `"since 11/2025"` gives `[("11", "2025")]`. The words around the dates do not matter.
- `[(int(y), int(m)) for m, y in …]` – a list comprehension that unpacks each tuple into month and year, turns both into numbers and puts the year first: `[(2017, 10), (2023, 6)]`.
- Three forms, three branches:
  - **Years only** – `if not dates:` the pattern found no month. `re.findall(r"\d{4}", when)` takes the years, `["2013", "2020"]`, and `zip(…, (1, 12))` pairs the first with January and the second with December: `[(2013, 1), (2020, 12)]`. Whole years, first and last included – "2013 – 2020" is 96 months, "8 years". `zip` stops at the shorter list, so a third year would be dropped.
  - **One date** – `if len(dates) == 1:` the end is missing, and the first character of `when` decides which one it is. `when[:1]` – a slice, the first character or `""` for an empty string, where `when[0]` would raise `IndexError`. A word in front – "since 11/2025" – means still running: the end is the year and month of today, the build date. A digit in front – "09/2014", a position of one month – means the end is the start: `dates[0]` again, one month.
  - **Two dates** – nothing to add.
- `(y1, m1), (y2, m2) = dates` – nested unpacking: the list holds exactly two pairs, each split into year and month.
- `(y2 - y1) * 12 + m2 - m1 + 1` – whole years in months, plus the difference of the months, plus one. The month difference may be negative (6 − 10 = −4); the year term makes up for it.
- The running role: "since 11/2025" built in November 2026 counts 11/2025 – 11/2026, 13 months. That number is right on the day of the build and then ages until the next one. So `role()` hands the start to `site.js`, which counts again in the visitor's browser (chapter 4).
- Pitfalls: a `when` with neither a month nor a year leaves `dates` empty, and the unpacking raises `ValueError` – loud. A lone year, "2013", counts as January alone: one date with a digit in front, one month. Quieter: a one-digit month. `"03/2025 – 7/2025"` finds only the first date (`\d{2}` wants two digits): `months()` counts one month, and `role()` takes the entry for the running one (section 24). Always write months with two digits.

```python
def duration(c, n):
    """69 → "5 years 9 months", in full words: no yrs/mos to decode."""
    year, years, month, months_ = c["dur"]
    y, m = divmod(n, 12)
    return " ".join(([f"{y} {year if y == 1 else years}"] if y else []) + ([f"{m} {month if m == 1 else months_}"] if m else []))
```

- Turns a number of months into words in the page language: 69 → "5 years 9 months", "5 Jahre 9 Monate".
- `year, years, month, months_ = c["dur"]` – the four words from `CONTENT` (section 8), singular and plural of each.
  - The trailing underscore in `months_`: `months` is already the name of the function above. A local variable of the same name would hide that function inside `duration()` – the same trap as `t` in `topbar()` (section 17). The underscore is the usual Python way around a name that is taken (`class_`, `type_`).
- `y, m = divmod(n, 12)` – division and remainder in one call: `divmod(69, 12)` is `(5, 9)`, five whole years and nine months left over. The same as `(n // 12, n % 12)`.
- `year if y == 1 else years` – the word is chosen, not built. Adding an "s" works in English but not in German ("Jahr", "Jahre"), so each language lists both forms.
- `[…] if y else []` – each part is a list with one string, or an empty list when its number is 0. `+` joins the two lists, `" ".join` puts a space between whatever is left:
  - 69 → `["5 years", "9 months"]` → "5 years 9 months"
  - 12 → `["1 year"]` → "1 year", not "1 year 0 months"
  - 3 → `["3 months"]` → "3 months"
- Full words instead of "5 yrs 9 mos", as the docstring says: nothing to decode, for readers and for programs that read the text.

```python
def before(mmyyyy):
    """The month before: "11/2018" → "10/2018", "01/2019" → "12/2018"."""
    m, y = int(mmyyyy[:2]), int(mmyyyy[3:])
    return f"{m - 1:02d}/{y}" if m > 1 else f"12/{y - 1}"
```

- The month before a date in `MM/YYYY` form. `role()` (section 24) uses it for the promotions within a role: each ends in the month before the one that followed it begins.
- `mmyyyy[:2]` and `mmyyyy[3:]` – slices: the first two characters, the month, and everything after the slash, the year. Fixed positions are enough here, because the format is fixed – two digits, a slash, four digits; `months()` needs a pattern because its dates sit inside longer text.
- `{m - 1:02d}` – a format spec inside the f-string: `d` an integer, `02` at least two digits, padded with zeros. 11 − 1 gives "10", 10 − 1 gives "09", not "9" – and `months()` only recognizes two-digit months.
- January has no month 0 before it: the conditional expression turns "01/2019" into "12/2018", the last month of the year before.

---

## 23 · title_of and jump

```python
def title_of(c, key):
    return 'P<sup>4</sup>' if key == "skills" else e(c["sec"][key])
```

- A section's title as HTML: the escaped heading from `sec`, or for P⁴, which has no entry in `sec`, the fixed markup with a superscript 4. `page()` uses it for the P⁴ heading, `jump()` for every item of its list – so the list shows the titles exactly as the headings do.

```python
def jump(c):
    """Up, the sections, down – fixed bottom right once the name has docked (replaces the old back-to-top button).
    site.js points up and down at the section above and below and shows the chapter number in the middle.
    Without JavaScript: up goes to the top, the menu works (details), down is hidden."""
    j = c["jump"]
    items = "".join(f'<li><a href="#{sid(c, k)}" data-t="{"P⁴" if k == "skills" else e(c["sec"][k])}">'
                    f'{chapter_no(k)}{title_of(c, k)}</a></li>\n' for k in SECTIONS)
    return f"""<nav class="jump" aria-label="{e(j['label'])}" data-up="{e(j['up'])}" data-down="{e(j['down'])}" data-top="{e(c['to_top'])}">
<a class="up" href="#top" aria-label="{e(c['to_top'])}" title="{e(c['to_top'])}">{UP_SVG}</a>
<details class="menu">
<summary aria-label="{e(j['menu'])}" title="{e(j['menu'])}"><span class="cur" aria-hidden="true"></span>{LINES_SVG}</summary>
<ol>
{items}</ol>
</details>
<a class="down" href="#{sid(c, SECTIONS[0])}" aria-label="{e(j['down'] % c['sec'][SECTIONS[0]])}" title="{e(j['down'] % c['sec'][SECTIONS[0]])}">{DOWN_SVG}</a>
</nav>
"""
```

The jump control: a narrow vertical pill in the bottom-right corner of the window with three parts – up, the sections, down. As the docstring says, `site.js` does the steering (chapter 4); `build.py` writes a version that already works without it.

- `j = c["jump"]` – the four labels of this language (section 8).
- `items` – one `<li>` per section in `SECTIONS`, in page order:
  - `href="#{sid(c, k)}"` – the localized anchor, as in the header menu.
  - `{chapter_no(k)}{title_of(c, k)}` – number and title as on the heading: chapter openers numbered, the others with the invisible number, so the titles line up here too.
  - `data-t` – the section's name as plain text. `site.js` builds the labels of the two arrows from it ("Up: Experience"). The link text cannot serve: it contains the number and, for P⁴, markup. An attribute holds text, not tags, so P⁴ is written with the superscript character `⁴` here.
  - Nested quotes once more: the f-string is single-quoted, so `"P⁴"` and `c["sec"][k]` inside the replacement field use double quotes (section 13).
- The `<nav>`:
  - `aria-label` – "Sections": the page's third navigation landmark, after the header menu and the footer's legal links, told apart from them by its name.
  - `data-up`, `data-down`, `data-top` – the label templates for `site.js`, so the script itself contains no words in either language. It replaces `%s` with a section name.
- The up link: `href="#top"` with the label from `to_top`. That is its state at the top of the page and its whole behavior without JavaScript: back to the hero. With JavaScript, `site.js` points it at the start of the section above.
- `<details class="menu">` with `<summary>` – the native disclosure element: a click on the summary opens and closes the rest, with keyboard and screen-reader support built in and no JavaScript needed. Here the rest is the list of sections.
  - `aria-label` on the summary – its visible content is an icon or a number, so it needs a name: "All sections".
  - `<span class="cur" aria-hidden="true"></span>` – empty in the HTML. `site.js` writes the current chapter number into it, "01" to "04". While it is empty – above the first section, and on a phone in Sources, which belong to no chapter –, the CSS shows `LINES_SVG` (section 11) instead; once it holds a number, the icon hides.
  - `<ol>` – an ordered list, because the sections have an order.
- The down link: `href` points at the first section, `SECTIONS[0]`, and the label names it. That is correct at the top of the page, where "down" means Profile.
  - `j['down'] % c['sec'][SECTIONS[0]]` – Python's `%` operator on a string fills in `%s`: `"Down: %s" % "Profile"` gives `"Down: Profile"`. The same template serves Python here and `site.js` later (`.replace("%s", …)`).
  - Without JavaScript, the CSS hides the down link: a fixed target would be wrong as soon as the page scrolls. It still gets a real target because `THEME_BOOT` sets the `js` class before `site.js` has even loaded. If `site.js` then fails, the CSS shows the link anyway, and it should lead somewhere sensible.
- Where it goes in the page: after the footer (section 25).

---

## 24 · steps and role

`steps()` writes the disclosures inside a timeline entry; `role()`, right below it in the file, writes the entry itself and calls `steps()` for them.

```python
def steps(c, label, rows):
    """A disclosure with the steps inside one timeline entry, newest first like the timeline itself: title (and company,
    where it changes – linked to its website where there is one), then dates and length. reversed: the list counts down,
    as the timeline does. rows: (title, company, dates, url) – company and url may be empty."""
    lis = "".join(f'<li>{e(title)}' + (f'&nbsp;<span class="muted">· {offsite(c, url, e(org)) if url else e(org)}</span>' if org else "")
                  + f'<br><span class="at">{span} · {duration(c, months(span))}</span></li>' for title, org, span, url in rows)
    return f'<details class="more">\n<summary>{e(label)}</summary>\n<ol class="tree" reversed>{lis}</ol>\n</details>\n'
```

- One disclosure: a summary line and, behind it, the steps inside one timeline entry. Two entries have one – Posterlounge's five positions and the six positions up to 2014. Both come from this function, so they look and behave the same.
- `label` – the summary text: "Five positions", "Six positions" – number and noun, the same pattern for both (German "Fünf Stationen", "Sechs Stationen").
- `rows` – a list of (title, company, range, url) tuples, already in page order, newest first. `steps()` writes them as it gets them. The company is `""` where there is none: the promotions all happened at the company the entry already names. The url is `""` where there is none to link: the promotions, and the one early position whose company has no website that could be verified (Proactive Europe).
- `lis` – one `<li>` per row, three f-strings joined with `+`:
  - `<li>{e(title)}` – the title, escaped.
  - `(… if org else "")` – the company, only where there is one. The parentheses are needed: `+` binds more tightly than a conditional expression, so without them the `if … else` would take the whole sum as its two branches – a row with a company would lose its dates, a row without one its title.
  - `{offsite(c, url, e(org)) if url else e(org)}` – the company as a link to its website, in a new tab with its ↗ (section 20), or as plain text where there is no url. A conditional expression inside the replacement field; it holds no quotes, so it can sit inside the single-quoted f-string.
  - `&nbsp;<span class="muted">· …</span>` – the company after a middle dot, set lighter by the class `muted` (chapter 3). The `&nbsp;` does what `dots()` cannot, as in the place line of `role()` below: a `<span>` tag sits between the space and the dot, so the plain sequence ` · ` never occurs, and the line brings its own non-breaking space.
  - `<br><span class="at">{span} · {duration(c, months(span))}</span>` – a line break, then the dates and their length: "04/2014 – 08/2014 · 5 months", or for a single month "09/2014 · 1 month". `months()` counts them, `duration()` puts the count into words (section 22) – the same two functions as for the role's own dates. This ` · ` is plain, so `dots()` glues it later.
  - `span` is the one value inserted without `e()`: digits, slashes and an en dash, nothing HTML reads as markup. Dates with `&` or `<` in them would need `e(span)`.
  - `for title, org, span, url in rows` – unpacks each tuple. The generator spans two lines inside the parentheses of `join()`.
- `<details class="more">` with `<summary>` – the native disclosure, as in the jump control (section 23): closed by default, opened by click or keyboard, announced as collapsed or expanded. `site.js` adds two things: it redraws the minimap when a disclosure opens, because the page just got longer, and it opens the disclosures for printing (chapter 4).
- `<ol class="tree" reversed>` – an ordered list, because the steps have an order.
  - `reversed` – the list counts down, like the timeline's `<ol class="roles" reversed>` (section 25): the newest step at the top carries the highest number. The numbers are not shown; `reversed` only keeps the list's semantics in line with its order, for assistive technology and anything else that reads the list's numbering. Nothing changes on screen.
  - The class `tree` borrows the #JobAlert branch lines from the CSS, so the steps read as a path. `.more .tree` gives the list its distance from the summary; `.more .tree li` and `.more .tree .at` serve both lists (chapter 3).
- No headings: a step is a line in a list, not a role of its own.

```python
def role(c, ro):
    """One role: dates and duration, title, company and place, context, the tree – and behind a disclosure
    the promotions within it (Posterlounge) or the single positions it sums up (before 2014)."""
    place = f'&nbsp;<span class="place">· {e(ro["place"])}</span>' if ro.get("place") else ""
    ctx = f'<p class="ctx">{e(ro["ctx"])}</p>' if ro.get("ctx") else ""
    org = offsite(c, ro["url"], e(ro["org"])) if ro.get("url") else e(ro["org"])
    if ro.get("with"):                                 # a partner named after the company, outside its link
        org += f' · {e(ro["with"])}'
    # the duration under the dates; a role that is still running carries its start, so site.js can recount it
    start = re.search(r"(\d{2})/(\d{4})", ro["when"])
    live = (f' data-from="{start[2]}-{start[1]}" data-units="{",".join(c["dur"])}"'
            if len(re.findall(r"\d{2}/\d{4}", ro["when"])) == 1 else "")
    when = f'{e(ro["when"])}<br><span class="dur"{live}>{duration(c, months(ro["when"]))}</span>'
    more = ""
    if ro.get("path"):                                 # promotions, one per contract: its start; it ends the month before the next
        label, path = ro["path"]
        ends = [re.findall(r"\d{2}/\d{4}", ro["when"])[-1]] + [before(start) for start, _ in path[:-1]]
        more += steps(c, label, [(title, "", f"{start} – {end}", "") for (start, title), end in zip(path, ends)])
    if ro.get("positions"):                            # the positions it sums up, each at its own company
        label, positions = ro["positions"]
        more += steps(c, label, [(title, org_, when_, url) for when_, title, org_, url in positions])
    return f"""<p class="when">{when}</p>
<div>
<h3>{e(ro['title'])}</h3>
<p class="org">{org}{place}</p>
{ctx}{tree(c, ro['tree'])}
{more}</div>
"""
```

- One entry of the Experience timeline: dates with duration, title, company with place, context line, tree, disclosures – the inside of an `<li class="role">`. The `<li>` itself is written by the caller, because only `page()` gives a role its `id` (section 25).
- `place` – optional field: `ro.get("place")` returns `None` when the key is missing (the freelance block) and `""` when it is empty (Rapidobject). Both are falsy, so no place span appears.
- `&nbsp;` before the span – the same job as `dots()`: "· Laucha" must not start a new line. `dots()` cannot do it here, because it only matches the plain sequence ` · `, and here a `<span>` tag sits between the space and the dot. So the place line brings its own non-breaking space.
- `ctx` – the optional context line, same pattern.
- `org` – the company name, as a link when the role has a `url`: nine of the eleven roles – seven company websites from E+SERVICE+CHECK to YOUniversal Media, and for the two trainings Liora's course page. The freelance block and the early group have none; their `org` is plain text, "Alongside employment" and "Six companies". The link leaves the site, so `offsite()` writes it (section 20): new tab, `noopener`, the ↗ after the last word – "YOUniversal Media" keeps "Media" and the ↗ together. `offsite()` takes HTML, so the name is escaped before it goes in; the URL is one of your own constants and goes in as it is.
  - The Liora link reaches the same English course page as the footnote's "Course page" (section 25), but without its `hreflang="en"`: `role()` passes no `attrs`.
- `if ro.get("with"): org += …` – the partner, appended after the finished link, so it stays outside it: `<a …>Liora…</a> · Université Paris 1 Panthéon-Sorbonne`. The ` · ` is plain, so `dots()` glues the dot to the ↗ before it (section 29). Only the two trainings have a `with`.

The dates and the duration:

- `start = re.search(r"(\d{2})/(\d{4})", ro["when"])` – the first date in the string, the start. `re.search` stops at the first match and returns a match object. Indexing it is short for `.group()`: `start[1]` is group 1, the month (`"11"`), `start[2]` group 2, the year (`"2025"`).
- `live` – two extra attributes for the role that is still running, an empty string for all others:
  - `len(re.findall(r"\d{2}/\d{4}", ro["when"])) == 1` – exactly one date in `when` means "since …": the role has no end yet. This pattern has no groups, so `findall` returns the matched strings themselves; only their number counts here. Years only, "2013 – 2020", gives none: no attributes, and `start` is `None` but never read.
  - Pitfall: the test counts dates and ignores the word. A role of a single month, `"09/2014"`, would be taken for a running one and recounted to today by `site.js`. Single months belong in `positions`, which `steps()` writes without these attributes – as 3D2B does.
  - `data-from="{start[2]}-{start[1]}"` – the start, year first: `"2025-11"`. `site.js` splits it at the hyphen.
  - `data-units="{",".join(c["dur"])}"` – the four words of `dur`, joined with commas: `"year,years,month,months"`, on the German page `"Jahr,Jahre,Monat,Monate"`. `site.js` splits them again, so the script contains no words in either language – the same idea as the jump control's `data-up` and `data-down` (section 23).
  - With both, `site.js` counts the running role again when the page loads, by the same rule as `months()` and in the same words as `duration()` (chapter 4). With JavaScript, the page never shows a stale duration, however long ago the last build was; without, it shows the count of the build day.
  - The leading space in `' data-from=…'` belongs to the attribute string, so every other role gets a clean `<span class="dur">` – the pattern of `rid` and `en_attr` (section 25). The outer parentheses let the expression span two lines.
- `when` – the dates, escaped, then `<br>`, then `<span class="dur">` with the duration from `duration(c, months(…))` (section 22). Result for the running role: `since 11/2025<br><span class="dur" data-from="2025-11" data-units="year,years,month,months">1 year</span>`.
  - The `<br>` puts the duration on a line of its own under the dates. It also keeps the two apart in text taken from the page, where a `<br>` becomes a line break: without it, the Posterlounge dates would read "10/2017 – 06/20235 years 9 months".
  - The CSS sets `.dur` a little smaller than the dates (chapter 3).

The disclosures:

- `more` – up to two disclosures, collected into one string. It starts empty, and each `+=` appends one, in a fixed order: first `path`, then `positions`. Today each entry has at most one of them. Both branches only build the (title, company, range) rows; `steps()` writes the HTML.
- `path` – used by Posterlounge: the four titles held within that one role, behind "Five positions", each with its dates and its length, and below them the freelance SEO work that came before the contract. The titles are the words people search for; in the disclosure they are part of the page's text without lengthening the timeline. The context line, `ctx`, describes the company only.
  - `label, path = ro["path"]` – the summary text and the list of (start, title) pairs, newest first. Only the starts are stored, as the contracts give them (section 8): 09/2021, 10/2020, 11/2018, 10/2017 – and 07/2017 for "SEO, freelance".
  - `ends` – one end per step, in the same order as the steps. The newest step ends with the role: `re.findall(…)[-1]` is the last date of its `when`, 06/2023, in a list of its own. Every other step ends the month before the step above it in the list starts – the one that followed it in time: `before(start) for start, _ in path[:-1]` takes the starts of all steps but the oldest and steps each back by a month (section 22). `[:-1]` is a slice without the last item: the oldest start, 07/2017, is where the path begins, and no step ends before it. The underscore is the usual name for a value that is unpacked but not used, here the title. `+` joins the two lists: `["06/2023", "08/2021", "09/2020", "10/2018", "09/2017"]`.
  - `zip(path, ends)` – pairs the n-th step with the n-th end. `(start, title), end` unpacks each pair: the step's tuple on the left, its end on the right. Head of Marketing gets 06/2023; Senior Marketing Manager gets 08/2021, the month before Head of Marketing began; the freelance row gets 09/2017, the month before the contract.
  - `(title, "", f"{start} – {end}", "")` – one row for `steps()`: the title, no company, the range as text and no url, "10/2017 – 10/2018". `steps()` adds the length. The four contract steps add up to the role's 69 months; the freelance row, "07/2017 – 09/2017 · 3 months", lies before the role's own dates, which count the employment.
  - Storing starts instead of ranges means one date per step, each written once: a corrected start moves the end of the step below it, the older one, as well.
  - The computation depends on the order. Stored oldest first, every step but the first would end before it starts – no error, only wrong ranges and lengths on the page.
  - The role itself must have ended: for a role still running, `[-1]` would be its start, and the newest step would end where the role begins.
- `positions` – used by one entry: "10/2010 – 09/2014 · Six companies" keeps the timeline at one line for those years and holds the six single positions behind "Six positions".
  - `label, positions = ro["positions"]` – the summary text and the list of (dates, title, company, url) tuples, newest first. Here every position carries its own dates: the positions overlap (06/2013 – 05/2014 and 06/2013 – 12/2013) and leave gaps, so no end follows from the next start. The newest, 3D2B, lasted one month and carries a single date, "09/2014"; `months()` counts it as one month (section 22).
  - Why 3D2B is a row here and not an entry: one month in Rome, right after SBS. An entry of its own would stand in the timeline with the weight of a role of several years.
  - `[(title, org_, when_, url) for when_, title, org_, url in positions]` – a list comprehension that reorders each tuple from the stored order (dates, title, company, url) into the order `steps()` takes (title, company, dates, url).
  - The trailing underscores: `org` and `when` are already local variables of `role()` – the company line and the dates line built above, both used again in the `return`. Python 3 gives a comprehension its own scope, so plain names would not overwrite them, but one function would then mean two things by each name, a few lines apart. The underscore is the usual way around a name that is taken, as with `months_` in `duration()` (section 22).
  - The `path` branch does reuse a name: in its comprehensions, `start` is a step's start, while the `start` above is the match object of the role's dates. The comprehension scope keeps the two apart, and the match is no longer needed by then.
  - Each position: title, company, range and length – "Marketing Consultant · SBS systems for business solutions", "04/2014 – 08/2014 · 5 months". No place and no tree per position: the entry's own Scope line sums them up, and its company line says "Six companies · Rome".
- `<h3>{e(ro['title'])}</h3>` – every role gets a heading of the same level under the `<h2>` of Experience. The steps behind a disclosure are list items, not headings, so the outline stays flat: Experience (h2) › each role (h3).
- Required fields (`when`, `title`, `org`, `tree`) use `ro['…']`: a missing key raises `KeyError`. That is intended – a role without a title should fail loudly. `tree` may be an empty list; `tree()` then returns `""`. `when` must hold at least one `MM/YYYY` date or a year, for `months()` (section 22).
- `{ctx}{tree(c, ro['tree'])}` – context line and tree directly after each other, then the disclosures, if there are any.

---

## 25 · page – one complete language version

The largest function. It collects HTML fragments in the list `out` and joins them once at the end. Appending to a list and joining once is the standard Python idiom for building long strings: strings are immutable, and repeated `+=` may copy the growing string over and over. The list's name is also why the link helper is called `offsite()`, not `out()` (section 20).

### Setup and footnote numbering

```python
def page(c):
    s, L = c["sec"], c["lang"]
    en_attr = ' lang="en"' if L != "en" else ""
    order = []  # footnotes, numbered in order of first appearance

    def fn(m):
        key = m.group(1)
        if key not in order:
            order.append(key)
        n = order.index(key) + 1
        return f'<sup class="fnref"><a href="#fn-{key}" id="ref-{key}" aria-describedby="h-{sid(c, "sources")}">{n}</a></sup>'
```

- `s, L = c["sec"], c["lang"]` – two assignments in one line (the right side is a tuple, unpacked into two names). `s` holds the section headings, `L` the language code.
- `en_attr` – the same `lang="en"` pattern as in `t()` and `tree()`.
- `order = []` – footnote keys in the order they first appear.
- `def fn(m):` – a function defined inside a function: a closure. It can use `order` and `c` from `page()`'s scope. It changes `order` only with `append`, which mutates the list – that needs no `nonlocal`. Only rebinding the name (`order = …`) would.
  - `m` is a match object from `re.sub`; `m.group(1)` is the text between `[[` and `]]`.
  - The first time a key is seen it is appended; its number is its position plus one (lists count from 0, footnotes from 1).
  - The returned `<sup>` links to `#fn-{key}` in the Sources list, carries `id="ref-{key}"` as the target of the way back, and `aria-describedby` points at the Sources heading.
  - Pitfall: using the same marker twice on one page produces two elements with `id="ref-ds"`. Duplicate IDs are invalid, and the back link only finds the first. One reference per key.

### Head, header and page frame

```python
    out = [head(c, TITLE, c["desc"], URL + HOME[L]), jsonld(c), "</head>\n<body>\n", topbar(c)]
    out.append(f'<div class="minimap" aria-hidden="true"></div>\n<main id="main"{torch_data(c)}>\n<div class="wrap">\n')
```

- The list starts with four parts: the head (canonical URL = `URL + HOME[L]`, for example `https://peterstieg.com/de/`), the JSON-LD block, the closing `</head>` with the opening `<body>`, and the header.
- `<div class="minimap">` – empty; `site.js` fills it with bars drawn from the page on wide screens. `aria-hidden` because it is a purely visual navigation aid.
- `<main id="main">` – the main landmark and the target of the skip link.
- `{torch_data(c)}` – the attribute `data-torch` with the torch's strings, leading space included (section 19). The legal pages and the 404s write the same attribute into their own `<main>`.
- `f'…'` – an f-string for the one field; the `\n` inside stay line breaks.

### Hero

```python
    # hero – same order as the LinkedIn banner
    out.append(f"""<section class="hero" id="top">
<h1>{NAME}</h1>
<p class="tagline" lang="en">{TAGLINE.replace("Performance Marketing", "Performance&nbsp;Marketing").replace("Data Science", "Data&nbsp;Science")}</p>
<p class="claim" lang="en">{CLAIM}</p>
<p class="prompt" lang="en"><span class="caret" aria-hidden="true">&gt;_</span><span class="cmd" aria-hidden="true">{MOTTO.replace("sudo", '<span class="sudo">sudo</span>', 1)}</span><span class="sr-only">{MOTTO}</span><span class="cursor" aria-hidden="true"></span></p>
</section>
""")
```

- `id="top"` – target of the home link and of the jump control's up link – its first target, and its only one without JavaScript.
- No `aria-label` on the section: the `<h1>` inside already names the block, and a label on top would make screen readers announce the name twice.
- `<h1>{NAME}</h1>` – the only `<h1>` on the page.
- The tagline: two chained `.replace()` calls inside the replacement field put `&nbsp;` inside each phrase, so "Performance Marketing" and "Data Science" never break in the middle; the line can only break at the middle dot. Pitfall: the replace matches the exact wording. Reword `TAGLINE` and the replace silently stops matching.
- Double quotes inside a triple-double-quoted f-string are fine on older Pythons too: a single `"` does not end a `"""` string.
- Tagline, claim and prompt are marked `lang="en"`, because they stay English on every page (rule 5).
- The prompt has four parts: the caret (hidden from screen readers), `.cmd` (hidden from screen readers; `site.js` empties it and types the motto letter by letter, unless the visitor's system asks for reduced motion), `.sr-only` (a visually hidden copy that screen readers read in full, instead of a half-typed string), `.cursor` (blinks via CSS). Without JavaScript the full motto simply stays in `.cmd`.
- `MOTTO.replace("sudo", '<span class="sudo">sudo</span>', 1)` – the motto's first word in a span of its own: a tap or a click on it switches on the torch (chapter 4). `1` – replace the first occurrence only. The `.sr-only` copy stays plain text: the span is for the pointer, and `.cmd` is hidden from screen readers anyway – keyboard users type `sudo`.

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
    # each result names its company; the name leads to the role under Experience
    # ↓: superscript and in accent like the footnote numbers – a link that stays on this page
    led = "".join(f'<div><dt>{t(c, a)}</dt><dd>{e(b)}<br><a href="#{k}">{e(COMPANIES[k])}'
                  f'<span class="jmp">{DOWN_SVG}</span></a></dd></div>\n' for a, b, k in c["ledger"])
    out.append(section(c, "profile", e(s["profile"]),
                       f'{entry}<p>{e(c["profile"])}</p>\n<dl class="ledger" aria-label="{e(c["ledger_label"])}">\n{led}</dl>\n'))
```

- `d = c["entry"]` – a short local name.
- `hw = re.sub(r"([·|])", …, e(d["hw"]))` – escape first, then wrap each syllable separator in a span so CSS can mute it.
  - `[·|]` is a character class: one character that is either the middle dot (English dictionary style: mar·ke·tin·ker·er) or the pipe (Duden style: Mar|ke|tin|ke|rer). Inside square brackets `|` is a literal character, not "or".
  - `( )` captures the separator as group 1; `\1` in the raw replacement string puts it back inside the span.
- `entry` – the dictionary entry. `<dfn>` marks the term being defined – the right element for a headword. `pos` and `def` go through `e()`, `ety` through `t()` for its italics.
- `led` – the results list as a description list: `<dt>` holds the label and the figure (through `t()` for the arrows; "Leads > 2×" becomes `Leads &gt; 2×`), `<dd>` the context and, after a `<br>`, the company. Every result reads the same way: label and figure on the first line – Leads, RoAS, Media budget –, one line of context, the company on a line of its own. A `<div>` around each `dt`/`dd` pair is valid inside `<dl>` and gives CSS one box per row.
  - `for a, b, k in c["ledger"]` – each entry is a 3-tuple: figure, context, company key. The generator spans two lines – two adjacent f-strings, joined into one; inside the parentheses of `join()` Python needs no line-continuation sign.
  - `<a href="#{k}">{e(COMPANIES[k])}…</a>` – the company's name from `COMPANIES` (section 7), as a link to the role with that `id` under Experience. In the CSS, `.role:target` colors the dates and title of the role the visitor arrived at (chapter 3).
  - `<span class="jmp">{DOWN_SVG}</span>` – a small ↓ after the name, inside the link. The CSS sets it superscript and in the accent color, like the footnote numbers: a mark that says "this link stays on this page and leads down". The ↗ says the opposite – by convention it marks a link that leaves the site, and the page uses it that way, muted, after every such link (section 20). The SVG is `aria-hidden`, so the link's name stays the company's name. The link's underline does not run under the arrow: the span is an inline-block, and text decoration does not reach into inline-blocks (chapter 3).
  - `<br>` instead of a separator: the company always starts its own line, so all three results are equally long – two lines under the figure on every screen from 360px up. In plain text the `<br>` becomes a line break, so a parser still gets context and company apart.
  - Pitfalls: a key missing from `COMPANIES` raises `KeyError` – loud. A key that no role carries as its `id` is silent: the link points at nothing and does not scroll.
- `section(…)` – heading escaped, body = entry + profile paragraph + results list with its own `aria-label`.

### P⁴

```python
    # P⁴ – four fields, each a P
    p4 = "".join(f'<div><h3{en_attr}>{e(p)}</h3><p>{e(txt)}</p></div>\n' for p, txt in zip(P4, c["fields"]))
    out.append(section(c, "skills", title_of(c, "skills"), f'<div class="fields">\n{p4}</div>\n'))
```

- `zip(P4, c["fields"])` pairs each heading with its text; `for p, txt in …` unpacks each pair into the P-word and its text.
- `"".join(…)` – a generator expression straight into the join: one `<div>` per field, heading and text, no list in between.
- No note behind People any more: the *i* with "Processes fit people, not the other way round." was dropped (decisions.md), and with it the helper `info()` and the toggletip's CSS and script.
- `<h3{en_attr}>` – the P-words are English on both pages.
- The section key is `"skills"` – its anchor, `#skills`, German `#kompetenzen` –, but `sec` has no `"skills"` heading: `title_of()` (section 23) returns the fixed markup `P<sup>4</sup>` in every language. The texts keep their key `fields` and the grid its class `.fields`: four fields, each a P.

### Languages

```python
    # languages – one per line, the level after the name
    langs = "".join(f"<li>{e(x)}</li>" for x in c["languages"])
    out.append(section(c, "languages", e(s["languages"]), f'<ul class="lines">{langs}</ul>\n'))
```

- A section of its own since 22.11.2026, the last one of chapter 01, after the profile and P⁴. Until then the languages were the last row of Education, between the degrees.
- `<ul class="lines">` with one `<li>` per language; the CSS removes the bullets, so each language stands on its own line.
  - A list rather than `<br>` line breaks, because it is one: screen readers announce "list, 5 items" and can step through it.
  - Each item goes through `e()` only – no footnote markers, no arrows.
- `langs`, not `languages`: the name of the content key would read as the same thing, and is not – this is the finished HTML.

### Experience

```python
    # experience – each role as a #JobAlert-style tree
    roles = []
    for ro in c["roles"]:
        roles.append(f'<li class="role" id="{ro["id"]}">\n{role(c, ro)}</li>\n')   # the ledger and the language switch land here
    roles = re.sub(r"\[\[(\w+)\]\]", fn, "".join(roles))       # a role's tree may cite a source, as Education does
    out.append(section(c, "experience", e(s["experience"]), f'<ol class="roles" reversed>\n{roles}</ol>\n'))
```

- `role(c, ro)` renders the inside of each entry (section 24); the loop only adds the `<li>` around it.
- `id` – every role has one: the ledger links to three of them, the language switch lands on all of them (`twins()`, section 12). Until 19.11.2026 only the three ledger roles had one, written through a conditional attribute string.
- `re.sub(r"\[\[(\w+)\]\]", fn, …)` – the footnote markers inside the roles, the same regex as in Education below: Brandible's Scope cites two videos (`[[h42]]`, `[[galileo]]`). Run over the finished HTML of all roles at once – `role()` and `tree()` know nothing of `fn`, and `e()` has left the brackets as they were. Experience comes before Education, so the videos get the numbers 1 and 2 and the certificates follow.
- `roles` is first the list, then the joined string – one name for the same content in two shapes, each used once.
- On phones held upright, where the section heading sticks under the header, the CSS gives `.role` a `scroll-margin-top`: a role reached from the ledger stops below the stuck heading instead of under it (chapter 3).
- `<ol class="roles" reversed>` – an ordered list, because sequence matters; `reversed` makes the numbering count down, so the newest role at the top carries the highest number. It is a boolean attribute: present means true. The step lists inside the entries count down the same way (`steps()`, section 24).

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

- The block sits right behind Experience: Education belongs to chapter 02 (`CHAPTERS`), so it follows Experience on the page – and here, because the order of the `out.append` calls is the order of the page.
- `for k, v, sub in c["facts"]` – each fact is a 3-tuple; an empty `sub` means "no second line".
- `re.sub(r"\[\[(\w+)\]\]", fn, e(v))` – the footnote markers:
  - Pattern: `\[\[` two literal brackets (escaped, because `[` normally opens a character class), `(\w+)` the key – letters, digits, underscore – as group 1, `\]\]` closing brackets.
  - The replacement is a function, not a string. `re.sub` calls `fn(match)` for every match, left to right, and inserts whatever it returns. That is what makes the numbering follow the order of appearance: the first marker processed gets 1.
  - Escape first again: `e()` does not touch `[` or `]`, so the markers survive, and `fn`'s HTML is inserted after escaping.
- Pitfalls: a key with a hyphen (`[[ml-ops]]`) does not match `\w+` and stays visible as text. A key that matches but is missing from `NOTES` gets a number here and then crashes the Sources loop with `KeyError`.

### Projects

```python
    # projects
    groups = []
    for gt, items in c["groups"]:
        lis = []
        for name, text, stack, links in items:
            ln = "".join(f' · {offsite(c, url, e(label))}' for label, url in links)
            lis.append(f'<li id="{slugify(name)}"><h4>{e(name)}</h4><p>{e(text)}</p><p class="stack">{e(stack)}{ln}</p></li>\n')
        groups.append(f'<div class="group"><h3>{e(gt)}</h3>\n<ul class="projects">\n{"".join(lis)}</ul></div>\n')
    out.append(section(c, "projects", e(s["projects"]), "".join(groups)))
```

- Two nested loops: groups (`gt` = group title), then projects within a group.
- `for name, text, stack, links in items` – each project is a 4-tuple. A tuple with three or five values raises `ValueError`.
- `ln` – a ` · ` and a link per (label, URL) pair: "GitHub · Demo" for the capstones. Both lead off the site, to GitHub and Streamlit, so `offsite()` writes them (section 20), with the label escaped first. "GitHub" and "Demo" are single words: the whole label and its ↗ share the no-wrap span. For an empty list the generator yields nothing and `"".join` returns `""`, so projects without links need no special case. The ` · ` separators get glued by `dots()` later.
- The section body is the joined groups alone, under a plain heading like every other section's.
- `name` is a local variable here; it does not clash with the constant `NAME` (Python is case-sensitive).
- `id="{slugify(name)}"` – each project an anchor made from its name (section 12): `#customer-portal`, `#pruef-check`. The language switch lands on it.

### Contact

```python
    # contact – one row per way to get in touch, laid out like Education; every link carries a mark like the ↗:
    # an envelope for the mail program, ↗ for the two profiles, a pin for the map
    mail, based, city = c["reach"]
    rows = [(e(mail), f'<a href="mailto:{EMAIL}"><span class="nw">{EMAIL}<span class="newtab sym">{MAIL_SVG}</span></span></a>')]
    for name, url in (("LinkedIn", LINKEDIN), ("GitHub", GITHUB)):
        address = re.sub(r"^https://(www\.)?|/$", "", url)               # the address is the link text
        rows.append((name, offsite(c, url, address, ' rel="me noopener"')))  # both profiles are Pete's own
    rows.append((e(based), offsite(c, MAP, e(city), mark=PIN_SVG, kind=c["map"])))
    contact = f'<p class="ask">{e(c["ask"])}</p>\n'                  # what to write about, leading into the rows
    contact += '<dl class="facts">\n' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>\n" for k, v in rows) + "</dl>\n"
    out.append(section(c, "contact", e(s["contact"]), contact))
```

- First a line of copy: `<p class="ask">` with `c["ask"]` (section 8) – "Questions about performance, pipelines, pixels or people:", German "Fragen zu Performance, Pipelines, Pixels oder People:" – what to write about, in the four words of P⁴. The colon leads into the rows. Escaped like all copy. The class names it for the torch (section 28); the CSS has no rule for it – a paragraph in `.body` gets its margin from `:where(.body) p` (chapter 3).
- `contact +=` – the list appended to the line. Two statements instead of one long expression; each half reads on its own.
- Four rows – Email, LinkedIn, GitHub, Based in – in the same `<dl class="facts">` as Education: label on the left, value on the right, a line between the rows. The CSS already exists, so Contact needs none of its own.
- `mail, based, city = c["reach"]` – unpacks the 3-tuple: the two labels that change with the language, and the place.
- `rows` – a list of (label, value) pairs, both already HTML. The loop at the end turns each pair into `<div><dt>…</dt><dd>…</dd></div>`.
- Every value is a link, and every link carries a superscript mark in the ↗'s place, so the four rows read alike: an envelope after the address, ↗ after the two profiles, a pin after the city (section 11). Each says what the click does – mail program, another site, a map.
- `mailto:` – opens the visitor's mail program. A plain `<a>`: no page opens, so there is no tab to choose. The address is a constant without special characters, so it goes in without `e()`. The envelope shares a no-wrap span with the address, built like the one in `offsite()` (section 20). It needs no hidden words: the row's label already says "Email".
- `for name, url in (("LinkedIn", LINKEDIN), ("GitHub", GITHUB))` – the two profiles, built the same way. "LinkedIn" and "GitHub" are names, the same in both languages.
- `re.sub(r"^https://(www\.)?|/$", "", url)` – the link text is the address itself, without the parts nobody types: `https://`, a leading `www.` and a closing `/`. `|` joins two patterns, `^` anchors the first at the start, `$` the second at the end; each match is replaced by nothing. Result: `linkedin.com/in/peterstieg`, `github.com/PeterStieg`. A visible address can be read off a printout or typed from a screen, and a parser finds the profile even without the link.
- `offsite()` (section 20) writes the new-tab link. The address has no space, so the whole of it shares the no-wrap span with the ↗.
- `' rel="me noopener"'` – the `attrs` argument. `rel="me"` declares "this profile is also me"; some platforms (Mastodon, for example) use it to verify identity in both directions. Because `attrs` brings a `rel`, `offsite()` leaves out its default, so `noopener` has to be in the list as well.
- The place is the city alone, linked to a map (`MAP`, section 3) through `offsite()` with the pin as its mark and "map" as its spoken kind. The places before Leipzig and the greeting "Hallo · Hi · Ciao" in large type were dropped (decisions.md).

### Sources

```python
    # sources – footnotes in order of appearance, each with a way back
    nl = c["notes"]
    notes = []
    for key in order:
        n = NOTES[key]
        back = f'<li id="fn-{key}"><a class="back" href="#ref-{key}" aria-label="{e(nl["back"])}">^</a> '
        if n.get("watch"):                             # a video: its German title, who and when, where to watch it
            de, hl = (' lang="de"' if L != "de" else ""), ' hreflang="de"'
            notes.append(f'{back}<cite{de}>{e(n["title"])}</cite> · {e(n["src"])} · {e(nl[n["when"]])} {e(n["date"][L])} · '
                         f'{offsite(c, n["watch"], e(nl["watch"] % n["on"]), hl)}</li>\n')
            continue
        en = ' hreflang="en"'                          # the course pages are English
        course = f' · {offsite(c, n["course"], e(nl["course"]), en)}' if n.get("course") else ""
        notes.append(f'{back}{e(note_title(c, n))} · {e(nl[n.get("when", "issued")])} {e(n["date"][L])} · '
                     f'{offsite(c, n["verify"], e(nl["verify"]))}{course}</li>\n')
    out.append(section(c, "sources", e(s["sources"]), f'<ol class="notes">\n{"".join(notes)}</ol>\n'))
```

- The last section, in no chapter (`SECTIONS`, section 6): the footnote numbers lead here from Experience and Education alike. The numbers stay – they tell the reader which source belongs to which claim, and the way back (`^`) returns to the spot in the text. The section key and its anchor are `sources` (German `quellen`); the list keeps its class `.notes`, as each item is a note.
- This loop runs after the education section, so `order` is already filled. The order of the `out.append` calls is load-bearing: build Sources before Education and the list comes out empty.
- Only footnotes that were actually referenced appear, in the order they were referenced. `<ol>` numbers its items 1, 2, … automatically – matching the numbers `fn()` produced, because both follow `order`.
- `back` – the start every note shares: `id="fn-{key}"`, the target of the superscript link, and `<a class="back" href="#ref-{key}">^</a>`, the way back, with a spoken label.
- `if n.get("watch")` – a video (section 7):
  - `<cite>` – the element for the title of a work; browsers set it in italics. `lang="de"` on the English page: the titles are German, and a screen reader should read them as German. On the German page the attribute would only repeat the page's language.
  - `nl[n["when"]]` – "published" or "aired", in the page language.
  - The link: `nl["watch"] % n["on"]` – the `%` operator fills the `%s` in "Watch on %s" with the platform: "Watch on YouTube", "Bei Joyn ansehen". `hreflang="de"` – both videos are German. `de, hl = …` – two variables in one line, as a tuple; a variable for the attribute for the same reason as `en` below.
  - `continue` – the rest of the loop is for credentials: on to the next note.
- `n["date"][L]` – the date string for the current language, for both kinds.
- `nl[n.get("when", "issued")]` – two lookups in one: first which label the note wants (`"issued"` unless it says otherwise), then that label in the page language: "issued", "completed", "ausgestellt am", "abgeschlossen am".
- Both links of a note leave the site – the verification pages at DataScientest, thekey.career and edX, the course pages at Liora – so `offsite()` writes them (section 20). "Verify credential" splits at its last space: "credential" and the ↗ share the no-wrap span. The way back, `^`, stays on the page.
- `course` – the course link, or nothing when the note has no course page.
- `en = ' hreflang="en"'` – the course pages are in English, and `hreflang` says so before the click. It goes in as `attrs`, with the leading space of the convention; it contains no `rel=`, so the tag gets the default as well: `target="_blank" rel="noopener" hreflang="en"`.
  - Why a variable: the f-string around the call is single-quoted, and before Python 3.12 an expression inside an f-string cannot contain the outer quote character (section 13). Written inline, `' hreflang="en"'` would end the f-string on Python 3.11. Contact can write its attribute string inline because the call there is not inside an f-string.
  - The assignment sits in the loop, next to its one use; its value is the same in every round.
- Three adjacent f-strings inside the `append(…)` parentheses form one string.

### Closing

```python
    out.append("</div>\n</main>\n")
    out.append(footer(c))
    out.append(jump(c))
    out.append(script(c["root"]) + "</body>\n</html>\n")
    return "".join(out)
```

- Closes the `wrap` div and `<main>`, adds the footer.
- `script(c["root"])` – the script tag with its fingerprint (section 15), then the end of the document.
- `jump(c)` – the jump control (section 23) comes after the footer. The CSS fixes it to the corner of the window, so its place in the HTML does not decide where it appears. It decides two other things:
  - Tab order: keyboard focus reaches the control last, after the content and the footer links, instead of before the content.
  - The CSS fades it in with `.top.docked ~ .jump` – "a `.jump` that comes after the docked header, under the same parent". The `~` combinator only looks forward, so the control has to follow the header; both are direct children of `<body>`.
- `defer` – the script downloads while the HTML is parsed and runs only after parsing is complete. By then every element exists, so `site.js` can query all of them.
- `"".join(out)` – one string for the whole page.

---

## 26 · Legal pages

```python
# ---------- legal pages: German and English ----------
# One body line per element: the torch's second level finds each element's line by its place (torch_map).

ADDRESS = """…"""

IMPRESSUM = f"""<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
<address>{ADDRESS}</address>
<h2>Kontakt</h2>
<p>E-Mail: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>Peter Stieg, Anschrift wie oben.</p>
"""

DATENSCHUTZ = f"""<h1>Datenschutzerklärung</h1>
<p class="muted">Stand: November 2026</p>
<h2>Verantwortlicher</h2>
<address>{ADDRESS}<br>E-Mail: <a href="mailto:{EMAIL}">{EMAIL}</a></address>
<h2>Kurz gesagt</h2>
<p>Diese Website setzt keine Cookies und lädt keine Inhalte von Drittanbietern: Schriften, Skripte und Grafiken liegen auf demselben Server wie die Seite selbst. Besuche werden statistisch ausgewertet – aus den Server-Logfiles, mit anonymisierter IP-Adresse. Ihr Browser speichert nur, was Sie selbst wählen: das helle oder dunkle Design und, im Haushaltsbuch, Sprache und Regeln (siehe unten).</p>
<h2>Hosting und Server-Logfiles</h2>
<p>Beim Aufruf der Website verarbeitet der Hosting-Anbieter automatisch Daten, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit des Zugriffs, aufgerufene Seite, Referrer-URL sowie Browser und Betriebssystem. Das ist technisch erforderlich, um die Seite auszuliefern und ihre Sicherheit zu gewährleisten. Rechtsgrundlage ist das berechtigte Interesse nach Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Hosting-Anbieter: … Mit ihm besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Speicherdauer der Logfiles richtet sich nach seinen Vorgaben.</p>
<h2>Reichweitenmessung mit IONOS WebAnalytics</h2>
<p>Um die Website statistisch auszuwerten und technisch zu verbessern, wertet IONOS WebAnalytics die Server-Logfiles aus: Referrer-URL, aufgerufene Seite oder Datei, Browser und Version, Betriebssystem, Gerätetyp und Zeitpunkt des Zugriffs. Die IP-Adresse wird direkt nach der Übermittlung anonymisiert und nur noch genutzt, um den Ort des Zugriffs zu bestimmen. Es werden keine Cookies gesetzt, keine Zählpixel oder zusätzlichen Skripte geladen und keine Daten an Dritte weitergegeben. Die Auswertung fällt unter den Vertrag zur Auftragsverarbeitung mit IONOS. Rechtsgrundlage ist das berechtigte Interesse nach Art. 6 Abs. 1 lit. f DSGVO; Sie können der Verarbeitung widersprechen (Art. 21 DSGVO).</p>
<h2>Helles und dunkles Design</h2>
<p>Ohne Ihr Zutun folgt die Website der Einstellung Ihres Geräts. Wählen Sie das Design über den Schalter oben selbst, speichert Ihr Browser diese Auswahl lokal (Local Storage), damit sie beim nächsten Besuch erhalten bleibt. Der Eintrag bleibt auf Ihrem Gerät und wird nicht an den Server übertragen. Rechtsgrundlage ist § 25 Abs. 2 Nr. 2 TDDDG. Sie können den Eintrag jederzeit löschen: mit einem zweiten Klick auf das gewählte Design oder über die Einstellungen Ihres Browsers.</p>
<h2>Haushaltsbuch</h2>
<p>Das Haushaltsbuch unter peterstieg.com/haushaltsbuch/ liest die Kontoauszüge, die Sie auswählen, ausschließlich in Ihrem Browser: Die Dateien werden weder hochgeladen noch an Dritte übertragen. Lokal (Local Storage) speichert Ihr Browser die Sprache, wenn Sie sie wechseln, und Ihre Regeln und Namen, wenn Sie „In diesem Browser merken“ wählen – nie Umsätze. Die Einträge bleiben auf Ihrem Gerät. Rechtsgrundlage ist § 25 Abs. 2 Nr. 2 TDDDG. Die Regeln löschen Sie, indem Sie „In diesem Browser merken“ wieder abwählen, alle Einträge über die Einstellungen Ihres Browsers.</p>
<h2>Kontakt per E-Mail</h2>
<p>Wenn Sie eine E-Mail schreiben, werden Ihre Angaben verarbeitet, um die Anfrage zu beantworten (Art. 6 Abs. 1 lit. b oder f DSGVO). Die Daten werden gelöscht, sobald sie dafür nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>
<h2>Links zu anderen Plattformen</h2>
<p>Die Seite verlinkt auf LinkedIn, GitHub, eine Karte bei OpenStreetMap, die Kursseiten von Liora, die Nachweisseiten von DataScientest, thekey.career und edX, die Demos der Abschlussprojekte bei Streamlit, ein Kundenvideo bei YouTube, eine TV-Folge bei Joyn sowie die Websites früherer und heutiger Arbeitgeber. Erst wenn Sie einem dieser Links folgen, verarbeiten die jeweiligen Anbieter Daten nach ihren eigenen Datenschutzbestimmungen.</p>
<h2>Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18) und Datenübertragbarkeit (Art. 20). Einer Verarbeitung auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO können Sie widersprechen (Art. 21). Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, etwa bei der zuständigen Behörde Ihres Bundeslandes.</p>
"""
```

- `ADDRESS` and the hosting provider's address are cut to `…` here; the real values are in `src/build.py`.
- `ADDRESS` – a plain triple-quoted string (no `f`): four lines – name, street, postcode and city, country – joined by `<br>`. The legal notice requires a full postal address (§ 5 DDG), and the privacy notice names the same person as the one responsible, so the address is defined once and used by all four pages. `<address>` marks it as contact information.
- The privacy notice also names the hosting provider with its address, because the server logs are processed on its behalf (Art. 28 DSGVO). Change hosts and this line has to change too – in both languages.
- Trade-off: the address in `ADDRESS` stays in the git history for good, even if you change it later. If the repository is public, so is the address – which the Impressum publishes anyway.
- `IMPRESSUM`, `DATENSCHUTZ` and the English pair below – f-strings that insert `ADDRESS` and `EMAIL`. They are HTML, inserted unescaped by `legal()`; a literal `&` in a new sentence must be written `&amp;`.
- The comment at the top is a rule for these four strings: one element per line. `torch_map()` (section 28) finds the line of each element by its place – the third element of the body is the third line of its string. `ADDRESS` spans four lines of its own, but it enters every body through one line, `<address>{ADDRESS}</address>`: what counts is the line in this file, not in the output.
- `Stand: November 2026` is typed by hand – update it when the text changes, and its English twin with it.
- The privacy text describes what the code and the server do: no cookies, fonts and scripts on the same server, `localStorage` only for the theme choice – and a second click on the chosen design deletes the entry, which is exactly what `site.js` does (chapter 4). Code and text are coupled: anything that loads third-party content (a web font service, a tracking script, an embedded video) requires a change to this text as well.
- "Reichweitenmessung mit IONOS WebAnalytics" (since 22.11.2026) – the statistics IONOS draws from the server logs. Nothing in the pages measures; the server does, so the code shows no trace of it, and only this section tells the visitor. IONOS requires the mention and describes the processing on its help page "Datenverarbeitung durch WebAnalytics": the data it lists, the IP address anonymised directly after transmission and used only for the place of access, no cookies, no data passed on – and the purpose, statistical evaluation and technical optimisation. The legal basis and the right to object are this site's own: IONOS names neither. Until then the page said "no analytics"; with the statistics on, that sentence was wrong (decisions, 22.11.2026).
- "Haushaltsbuch" – the household ledger at `/haushaltsbuch/`, on the same server, built outside this repository. It reads bank statements in the browser only – its content security policy allows no connection at all (`connect-src 'none'`) – and stores two `localStorage` entries: `hb.lang` once the language is switched, `hb.cfg` (rules and names, never transactions) while "In diesem Browser merken" is ticked; unticking deletes it. A privacy policy covers the whole domain, so the tool is described here, without a link: it is not part of the site's navigation.

The English translations and the table that ties the four pages together:

```python
IMPRINT_EN = f"""<h1>Legal notice</h1>
<p class="muted">Translation – the German <a href="de/impressum.html" hreflang="de" lang="de">Impressum</a> is legally binding.</p>
<h2>Information pursuant to § 5 DDG</h2>
<address>{ADDRESS.replace("Deutschland", "Germany")}</address>
<h2>Contact</h2>
<p>Email: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<h2>Responsible for the content under § 18(2) MStV</h2>
<p>Peter Stieg, address as above.</p>
"""

PRIVACY_EN = f"""<h1>Privacy policy</h1>
<p class="muted">As of November 2026 · Translation – the German <a href="de/datenschutz.html" hreflang="de" lang="de">Datenschutzerklärung</a> is legally binding.</p>
<h2>Controller</h2>
<address>{ADDRESS.replace("Deutschland", "Germany")}<br>Email: <a href="mailto:{EMAIL}">{EMAIL}</a></address>
<h2>In short</h2>
…
<h2>Light and dark design</h2>
<p>Unless you choose otherwise, the website follows your device's setting. … You can delete the entry at any time: with a second click on the chosen design, or in your browser's settings.</p>
…
"""

# German law asks for both pages; the German text is binding, the English one is a translation and says so.
# Per page and language: path, title, body – English in the root, German in de/, like the start pages.
# The footer links the pair in the page's language.
LEGAL = {
    "imprint": {"en": ("legal-notice.html", "Legal notice", IMPRINT_EN), "de": ("de/impressum.html", "Impressum", IMPRESSUM)},
    "privacy": {"en": ("privacy.html", "Privacy policy", PRIVACY_EN), "de": ("de/datenschutz.html", "Datenschutzerklärung", DATENSCHUTZ)},
}
```

- `IMPRINT_EN`, `PRIVACY_EN` – the same structure, element for element, in English. Their second line says what they are: a translation, with the German original binding and linked – `de/impressum.html`, written relative to the English page, which sits in the root. On that link, `hreflang="de"` names the target's language and `lang="de"` the language of the link text, a German word.
- `ADDRESS.replace("Deutschland", "Germany")` – the country in English, the rest as it is. `replace` returns a new string; `ADDRESS` itself stays German for the German pages.
- `As of November 2026` – typed by hand, like `Stand:`. The two dates move together.
- Code and text are coupled across languages too: a sentence changed in `DATENSCHUTZ` is a sentence to change in `PRIVACY_EN`.
- `LEGAL` – a dict of dicts: page → language → (path, title, body). The footer (section 18), `legal()` below and `build()` (section 30) read it; a third language would be one more entry per page.
- Each page under a file name in its own language, in its language's folder: English in the root next to `index.html`, German in `de/` next to `de/index.html` – the same structure as the start pages and the 404s. Until 22.11.2026 the German pair sat in the root as well; `.htaccess` forwards the old addresses (section 30).

```python
def legal(key, L):
    """A legal page in one language. The language switch leads to the same page in the other language; the body's id
    (the file name) tells the torch which page it is on."""
    path, title, body = LEGAL[key][L]
    c = dict(CONTENT[L], path=path, root="../" * path.count("/"))   # the German pages sit in de/, like the German start page
    pair = {code: p[0] for code, p in LEGAL[key].items()}
    return "".join([
        head(c, f"{title} – {NAME}", c["legal_desc"] % title, URL + path, alternates=pair),
        '<meta name="robots" content="noindex, follow">\n</head>\n<body>\n',
        topbar(c, start=False, langs=pair),
        f'<main id="main"{torch_data(c)}>\n<div class="wrap legal">\n<div class="body" id="{page_id(path)}">\n{body}</div>\n</div>\n</main>\n',
        footer(c), script(c["root"]) + "</body>\n</html>\n"])
```

- `legal(key, L)` – one page: which one (`"imprint"`, `"privacy"`) in which language (`"en"`, `"de"`). `build()` calls it four times.
- `path, title, body = LEGAL[key][L]` – the three values of this page, unpacked.
- `c = dict(CONTENT[L], path=path, root=…)` – `dict(mapping, key=value)` creates a new dict with every entry of the language's dict, then overrides `path` and `root`: the page's own file, so `href()` counts its links from there (section 12), and the way back to the site root for the stylesheet, the script and the icons.
  - `"../" * path.count("/")` – a string times a number repeats it: one `../` per folder in the path. `de/impressum.html` has one slash and gets `"../"`, `privacy.html` none and gets `""`.
  - Why a copy instead of `CONTENT["de"]["path"] = …`: changing the original would leave the German start page writing to the wrong file.
  - It is a shallow copy: nested lists and dicts are shared with the original. `c["root"]` is safe to replace; `c["nav"].append(…)` would change `CONTENT` itself.
- `pair = {…}` – a dict comprehension over both languages of this page: code → path, `{"en": "legal-notice.html", "de": "de/impressum.html"}`. `p[0]` is the path in each tuple. Both pages of a pair build the same dict, so each names the other.
- The parts:
  - `head(…)` – title "Legal notice – Peter Stieg"; description `c["legal_desc"] % title` – the `%` operator fills `%s`: "Legal notice for peterstieg.com", "Impressum von peterstieg.com"; canonical `URL + path`; `alternates=pair` – the hreflang links to both versions, x-default the English one (section 14).
  - `robots` meta `noindex, follow` – keep the page out of search results, but follow its links. Then the head closes and the body opens.
  - `topbar(c, start=False, langs=pair)` – the menu leads to the sections of the start page in the page's language (`./#werdegang` from `de/impressum.html`), and so does the home link, without an anchor (`./`); the language switch leads to the same page in the other language (section 15). The theme switch stays.
  - `<main id="main"{torch_data(c)}>` – the torch works here too (section 19).
  - `<div class="body" id="{page_id(path)}">` – the file name without folder and `.html` (section 12): `legal-notice`, `privacy`, `impressum`, `datenschutz` – four different ids, so one `torch.json` can hold the rules of all four pages (`#impressum > :nth-child(3)`, section 28).
  - `{body}` – inserted raw, followed directly by the closing tags. The line that once linked both start pages at the end of the body is gone: the logo leads to the start page, the switch to the other language.
  - `footer(c)` – the legal links in the page's language. `script(c["root"])` – the root prefix of this page: `""` for the English pair, `"../"` for the German.

---

## 27 · not_found

```python
def not_found(c):
    """404 with a Google Ads insider joke: Dynamic Keyword Insertion, {KeyWord:Default}. One per language – a missing
    address under /de/ gets the German one (de/.htaccess) – each with a line in the other language and its start page."""
    word, rest, line, home_name = c["lost"]
    home = HOME[c["lang"]]
    other = next(x for x in LANGS if x[0] != c["lang"])           # code, label, name, home
    c = dict(c, root="/")
    return "".join([
        head(c, f"404 – {NAME}", f"{word} {rest}", f"{URL}{home}404.html", alternates=False, root="/"),
        '<meta name="robots" content="noindex">\n</head>\n<body>\n',
        topbar(c, start=False),
        f"""<main id="main"{torch_data(c)}>
<div class="wrap">
<section class="lost">
<p class="code">404</p>
<h1><code class="dki">{{KeyWord:{e(word)}}}</code> {e(rest)}</h1>
<p class="claim" lang="{other[0]}">{e(line)}</p>
<p class="prompt"><span class="caret" aria-hidden="true">&gt;_</span><a href="/{home}">cd ~<span class="sr-only"> – {e(home_name)}</span></a></p>
</section>
</div>
</main>
""",
        footer(c), script("/") + "</body>\n</html>\n"])
```

- One 404 per language: `build()` calls `not_found(c)` with each language's dict and writes `404.html` and `de/404.html` (section 30). Which one a visitor sees is up to the server: `.htaccess` names `/404.html`, and `de/.htaccess` names `/de/404.html` for every missing address under `/de/`.
- `word, rest, line, home_name = c["lost"]` – the four strings of the page (section 8): `("Page", "not found.", "Diese Seite gibt es nicht.", "start page")` in English, `("Seite", "nicht gefunden.", "This page does not exist.", "Startseite")` in German.
- `home = HOME[c["lang"]]` – the start page of the page's own language: `""` or `"de/"` (section 5).
- `other = next(x for x in LANGS if x[0] != c["lang"])` – the whole tuple of the other language. `next()` takes the first value the generator yields and stops. The comment names its fields; only `other[0]`, the code, is still used – for the `lang` of the line in the other language. With two languages there is exactly one other; a third would need a list here.
- `c = dict(c, root="/")` – the parameter rebound to a copy with a root-absolute prefix. The caller's dict stays as it was.
- Why `"/"`: the server delivers this page for every missing URL, at any depth – `/de/old/page` included. A relative `assets/site.css` would then resolve to `/de/old/assets/site.css` and fail. A leading slash always resolves from the domain root.
- Trade-off: opened straight from disk (`file://`), `/` means the root of your file system, so the 404 pages look unstyled locally. That is expected.
- `head(…)` – description `f"{word} {rest}"`: "Page not found.", "Seite nicht gefunden."; canonical `f"{URL}{home}404.html"`: the page's own address. `root="/"` is passed as well – redundant, since `c["root"]` is already `"/"`.
- `robots` `noindex` – error pages do not belong in search results.
- `topbar(c, start=False)` – the header as on the legal pages: the menu leads to the start page's sections (`/#profile`), the logo to the start page. With the root `"/"`, `href()` writes every address from the root (section 12). `langs` keeps its default, `True`: the switch leads to the other start page – `/de/` from the English 404, `/` from the German one –, because a missing page has no counterpart in the other language.
- `<main id="main"{torch_data(c)}>` – the torch here too; `TORCH` has four rules for the lines below (section 28).
- `{{KeyWord:{e(word)}}}` – in an f-string, `{{` and `}}` produce literal braces, and `{e(word)}` between them is a replacement field. The output is `{KeyWord:Page}` or `{KeyWord:Seite}`: Google Ads Dynamic Keyword Insertion syntax, where the ad shows the searched keyword or, if that does not fit, the default text after the colon. Without the doubling, Python would try to evaluate `KeyWord:…` as an expression and fail.
- `lang="{other[0]}"` – the line in the other language is marked as such: `lang="de"` on the English page, `lang="en"` on the German one.
- `cd ~` links to the start page of the page's language (`/` or `/de/`). `<span class="sr-only"> – {e(home_name)}</span>` – visually hidden (section 13), inside the link: on screen the shell command, for screen readers "cd ~ – start page", "cd ~ – Startseite" – a name that says where the link goes. The link to the other start page that stood after it until 13.11.2026 is now the header's language switch.
- `script("/")` – the script tag with a root-absolute path.

---

## 28 · TORCH and torch_map – what the torch shows second

```python
# ---------- torch ----------

# What the torch's second level shows (site.js): for each CSS selector, a snippet that occurs on exactly one line of this
# file – the line that writes the element – and how many lines to show from there. First match wins, so the narrower
# selector comes first (Contact before Education). Selectors without ids: the ids differ between the languages.
TORCH = [
    (".hero h1", "<h1>{NAME}</h1>", 1),
    (".hero .tagline", '<p class="tagline" lang="en">', 1),
    (".hero .claim", '<p class="claim" lang="en">', 1),
    (".hero .prompt", '<p class="prompt" lang="en">', 1),
    (".sec > h2", '<h2 id="h-{i}">', 1),
    (".hw", '<p class="hw">', 1),
    (".def", '<p class="def">', 1),
    (".entry + p", '{entry}<p>{e(c["profile"])}</p>', 1),
    (".ledger dt, .ledger dd", "led = \"\".join(f'<div><dt>", 2),
    (".fields h3, .fields p", "p4 = \"\".join(f'<div><h3", 1),
    (".more summary", '<details class="more">', 1),
    (".more .tree li", "lis = \"\".join(f'<li>{e(title)}'", 3),
    (".role .when", '<p class="when">{when}</p>', 1),
    (".role h3", "<h3>{e(ro['title'])}</h3>", 1),
    (".role .org", '<p class="org">{org}{place}</p>', 1),
    (".role .ctx", 'ctx = f\'<p class="ctx">', 1),
    (".role .tree li", "items = \"\".join(f'<li><span class=\"k\"", 1),
    (".lines li", 'langs = "".join(f"<li>{e(x)}</li>"', 1),
    (".ask", "contact = f'<p class=\"ask\">", 1),
    (".facts:has(a[href^='mailto:']) dt, .facts:has(a[href^='mailto:']) dd", "contact += '<dl class=\"facts\">", 1),
    (".facts dt, .facts dd", 'fa.append(f"<div><dt>', 1),
    (".group > h3", "groups.append(f'<div class=\"group\"><h3>", 1),
    (".projects h4, .projects p", "lis.append(f'<li id=", 1),
    (".notes li:has(cite)", "if n.get(\"watch\"):", 5),
    (".notes li", "back = f'<li id=\"fn-{key}\">", 1),
    (".lost .code", '<p class="code">404</p>', 1),
    (".lost h1", '<h1><code class="dki">', 1),
    (".lost .claim", '<p class="claim" lang="{other[0]}">', 1),
    (".lost .prompt", '<p class="prompt"><span class="caret"', 1),
]


def torch_map():
    """[selector, line number, code] for every TORCH rule, read from this file as it is now – so the numbers stay right
    whatever changes above them. Stops the build if a snippet matches no line or several."""
    src = Path(__file__).read_text(encoding="utf-8").split("\n")
    start = src.index("TORCH = [")
    end = src.index("]", start)                       # the list names every snippet once more: skip it
    rows = []
    for sel, snip, n in TORCH:
        hits = [i for i, line in enumerate(src) if snip in line and not start <= i <= end]
        if len(hits) != 1:
            raise SystemExit(f"TORCH {sel}: {len(hits)} lines match {snip!r}")
        lines = src[hits[0]:hits[0] + n]
        pad = min(len(x) - len(x.lstrip()) for x in lines if x.strip())
        rows.append([sel, hits[0] + 1, "\n".join(x[pad:] for x in lines)])
    # legal pages: one line per element, so the n-th element in a page's body is the n-th line of its string
    for pages in LEGAL.values():
        for path, _, body in pages.values():
            first = next(i for i, line in enumerate(src) if line.endswith('f"""' + body.split("\n")[0]))
            rows += [[f"#{page_id(path)} > :nth-child({k + 1})", i + 1, src[i]]
                     for k, i in enumerate(range(first, src.index('"""', first)))]
    return rows
```

The torch (chapter 4) has two levels. The first shows each block of text as HTML – the browser has that at hand. The second shows the line of this file that wrote the block; that the browser cannot know, so the build tells it, in `site/assets/torch.json`. The torch runs on every page, so the file covers the start pages, the 404s and the legal pages.

- `TORCH` – one rule per kind of element: a CSS selector, a snippet of this file, a number of lines.
  - The selector names the elements on the page, as `site.js` will test them with `el.matches()`. `".ledger dt, .ledger dd"` – a selector list, either one.
  - The snippet is a piece of the template line that writes those elements, long enough to occur on exactly one line: `'<p class="hw">'` finds the line in `page()` that writes the dictionary entry's headword.
  - The number says how many lines to show from there: 2 for the ledger, whose f-string spans two lines; 3 for the steps behind a disclosure; 5 for a video note, from the `if` to its `append`.
  - Order matters, because `site.js` takes the first rule that matches: `.facts:has(a[href^='mailto:'])` – the list that holds the mail link, Contact – comes before `.facts`, which would also match Contact but means Education.
  - No ids in the selectors: the ids are localized (`#contact` is `#kontakt` in German, section 8), the classes are not. `:has()` picks the list by what it contains instead.
  - The Sources have two rules: `.notes li:has(cite)` – a video note, the only kind with a `<cite>` – before `.notes li`, which would match it too and means the credentials. Both point into the same loop; the credentials' rule shows the line both kinds start with, `back = …`.
  - Contact has two rules: `.ask` finds the line `contact = f'<p class="ask">…`, the list's rule the line after it. Its snippet begins `contact +=`, not `contact =` – `contact = '<dl class="facts">` occurs nowhere since the line was added, and a snippet that matches no line stops the build.
  - The four `.lost` rules are the 404 (section 27). Its claim and prompt need snippets of their own: `'<p class="claim" lang="{other[0]}">'` and the hero's `'<p class="claim" lang="en">'` each occur on one line only. The selectors keep them apart on the page – the hero's elements sit in `.hero`, the 404's in `.lost`.
- Why a snippet and not a line number: line numbers move with every edit above them. A snippet stays with its line; `torch_map()` looks the number up on every build.

`torch_map()`:

- `Path(__file__).read_text(…)` – the script reads itself: `__file__` is its own path (section 3). `.split("\n")` gives the lines; index 0 is line 1.
- `start = src.index("TORCH = [")` – the list's first line. `list.index` returns the position of the first element equal to the argument – a whole line, not a substring – and raises `ValueError` if there is none. So the line must read exactly `TORCH = [`, without a comment.
- `end = src.index("]", start)` – the first line after it that is exactly `]`: the list's closing bracket, unindented. The second argument of `index` is where the search starts.
- Why skip the list: every snippet occurs there too, as a string inside the rule. Without `not start <= i <= end` each snippet would match twice. `start <= i <= end` is a chained comparison: `start <= i and i <= end`.
- `hits` – the line indexes that contain the snippet, outside the list. `snip in line` is a substring test.
- `if len(hits) != 1: raise SystemExit(…)` – no line or several: the template has changed and the rule no longer finds its line. `SystemExit` ends the build with that message and exit status 1, before anything is written, instead of shipping a torch that shows the wrong line.
- `lines = src[hits[0]:hits[0] + n]` – a slice: `n` lines from the hit.
- `pad` – the smallest indentation among them (`len(x) - len(x.lstrip())`: the length of the leading spaces), skipping empty lines. `x[pad:]` cuts exactly that much from each, so the snippet keeps its inner indentation but starts at the left edge.
- `rows.append([sel, hits[0] + 1, …])` – the line number counts from 1, as editors do; the list index counts from 0.
- The result is a list of lists, not tuples: `json.dumps` writes both as JSON arrays, and the lists say what the file will hold.

The legal pages need no rules in `TORCH`: their bodies are written one element per line (section 26), so position does the work.

- `for pages in LEGAL.values()` and `for path, _, body in pages.values()` – the four pages; the title is not needed.
- `first` – the line where the body string starts. `body.split("\n")[0]` is the body's first line (`<h1>Legal notice</h1>`); the line in this file that ends with `f"""` plus that line is the one that opens the string: `IMPRINT_EN = f"""<h1>Legal notice</h1>`. `next()` takes the first such line.
- `src.index('"""', first)` – the first line from there that is exactly `"""`: the end of the string. `range(first, …)` – every line of the body, the closing one excluded.
- `enumerate(…)` – counts the lines: `k` from 0, `i` the line's index in the file.
- `f"#{page_id(path)} > :nth-child({k + 1})"` – the selector of the element that line writes: the `(k + 1)`-th child of the body `<div>` whose id is the file name (`page_id()`, section 12). `#impressum > :nth-child(3)` is the `<address>`. `:nth-child()` counts from 1 and counts every element, whatever its tag.
- `i + 1`, `src[i]` – line number and line, one line per rule.
- `rows += […]` – appends every item of the list, like `extend`.
- Pitfall: the rule is one element per line. Two elements on one line, or one over two lines, shifts every rule after it – the torch shows the neighbour's line, without an error. The comment above `ADDRESS` states the rule where the text is edited.
- Pitfall: the numbers are right for the build that wrote them. Change `build.py` without rebuilding, and the torch shows the old numbers – the same as every other file in `site/`.

---

## 29 · nbsp and dots – typography after the fact

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
- `dots()` runs on every generated HTML page: the two start pages, the four legal pages and the two 404s. `nbsp()` stays on the German start page.

---

## 30 · HTACCESS and build – writing to disk

```python
# Apache (IONOS): the error pages, one address for the site, the manifest's type, how long browsers keep what.
HTACCESS = r"""ErrorDocument 404 /404.html
ErrorDocument 403 /404.html
AddType application/manifest+json .webmanifest

# one address: https://peterstieg.com/ – www. and http:// forward there (the port check IONOS recommends)
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTP_HOST} ^www\. [NC,OR]
RewriteCond %{SERVER_PORT} !=443
RewriteRule ^ https://peterstieg.com%{REQUEST_URI} [R=301,L]
# a start page has one address, its folder: /index.html → /, /de/index.html → /de/. THE_REQUEST is the line the
# browser sent – the server's own step from / to index.html does not match it, so nothing loops.
RewriteCond %{THE_REQUEST} \s/((de/)?)index\.html[?\s]
RewriteRule ^ https://peterstieg.com/%1 [R=301,L]
# the German legal pages moved to de/ (November 2026): old links and bookmarks follow
RewriteRule ^(impressum|datenschutz)\.html$ https://peterstieg.com/de/$1.html [R=301,L]
</IfModule>

# security: HTTPS only for a year, no content sniffing, no framing, no camera, microphone or location; the referrer
# leaves the site as the origin only. The content security policy allows this server and the two inline scripts
# (by hash) – report-only for now: violations show in the browser console, nothing is blocked.
<IfModule mod_headers.c>
Header always set Strict-Transport-Security "max-age=31536000"
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
Header always set Content-Security-Policy-Report-Only "default-src 'self'; script-src 'self' __HASHES__; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
</IfModule>

# stylesheet and script change their address with their content (?v=), fonts never change: kept for a year.
# Pages and torch.json are asked for on every visit – unchanged, the answer is a short 304.
<IfModule mod_headers.c>
<FilesMatch "\.(css|js|woff2)$">
Header set Cache-Control "public, max-age=31536000, immutable"
</FilesMatch>
<FilesMatch "\.(html|json)$">
Header set Cache-Control "no-cache"
</FilesMatch>
</IfModule>

# text goes out compressed – pages, stylesheet and script shrink to a quarter to a third
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/css text/javascript application/javascript application/json image/svg+xml application/manifest+json
</IfModule>
"""
```

- The server configuration for Apache, as one string that `build()` writes to `site/.htaccess`. What each directive does is in chapter 2 (`.htaccess`); here only the Python.
- `r"""…"""` – a raw string: backslashes stay as typed. `^www\.` and `"\.(css|js|woff2)$"` reach Apache with their `\.` – a literal dot in a regular expression. Without the `r`, Python would read `\.` as an unknown escape sequence: it keeps the backslash but warns (`SyntaxWarning` since Python 3.12).
- Not an f-string: `%{HTTP_HOST}`, `%{SERVER_PORT}`, `%{REQUEST_URI}` and `%{THE_REQUEST}` are Apache's variables. In an f-string, their braces would be replacement fields.
- `__HASHES__` – a placeholder in the policy. The string cannot compute the two script hashes itself, since it is no f-string; `build()` puts them in with `replace` (below).
- Five blocks: the error pages and the manifest's type; one address per page (`mod_rewrite`: the domain, the start pages' folders, the German legal pages in `de/`); security headers and caching (both `mod_headers`, one block each); compression (`mod_deflate`). Each `<IfModule>` block applies only where its module is loaded.
- The caching block depends on `VERSION` (section 10): a year without asking again is safe only because the stylesheet and the script change their address when they change.
- The policy depends on `csp_hash()` and on `LOCKUP` (sections 10 and 11): it allows exactly the two inline scripts and no inline style. Report-only until the live site shows no violations; then the header's name changes to `Content-Security-Policy`, and the policy blocks instead of reporting.

```python
def build():
    for key, *_ in LANGS:
        c = CONTENT[key]
        target = SITE / c["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(dots(page(c) if key == "en" else nbsp(page(c))), encoding="utf-8")
        target.with_name("404.html").write_text(dots(not_found(c)), encoding="utf-8")   # 404.html, de/404.html
    for key, pages in LEGAL.items():
        for L, (path, _, _) in pages.items():
            (SITE / path).write_text(dots(legal(key, L)), encoding="utf-8")
    (SITE / ".htaccess").write_text(HTACCESS.replace("__HASHES__", f"{csp_hash(THEME_BOOT)} {csp_hash(SPECULATION)}"),
                                    encoding="utf-8")
    (SITE / "de" / ".htaccess").write_text("# a missing address under /de/: the German 404\nErrorDocument 404 /de/404.html\n",
                                           encoding="utf-8")
    (SITE / "assets" / "torch.json").write_text(json.dumps(torch_map(), ensure_ascii=False), encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {URL}sitemap.xml\n", encoding="utf-8")
    # The sitemap lists pages, not content: it changes when pages are added or removed. lastmod = build date.
    today = date.today().isoformat()
    alts = "".join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{URL}{home}"/>' for code, home in HOME.items())
    urls = "".join(f"<url><loc>{URL}{home}</loc><lastmod>{today}</lastmod>\n{alts}</url>\n" for home in HOME.values())
    (SITE / "sitemap.xml").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
{urls}</urlset>
""", encoding="utf-8")
    print("ok:", ", ".join(str(p.relative_to(SITE)) for p in sorted(SITE.rglob("*.html"))))
```

The start pages and the 404s:

- `for key, *_ in LANGS` – only the language code is needed.
- `target = SITE / c["path"]` – the `/` operator on a `Path` joins path parts (Python calls `Path.__truediv__`). It uses the right separator for the operating system; `"de/index.html"` with a forward slash works on Windows too, because `pathlib` normalizes it.
- `target.parent.mkdir(parents=True, exist_ok=True)` – creates `site/de/` if missing. `parents=True` also creates any missing folders above it; `exist_ok=True` means "no error if it already exists". Safe to run on every build.
- `dots(page(c) if key == "en" else nbsp(page(c)))` – a conditional expression picks the pipeline: English gets `page(c)`, German `nbsp(page(c))`; both then go through `dots()`.
- `target.with_name("404.html")` – the same folder, another file name: `site/index.html` gives `site/404.html`, `site/de/index.html` gives `site/de/404.html`. Each language's 404 lands next to its start page.
- `.write_text(…, encoding="utf-8")` – opens, writes, closes. It overwrites without asking.
- `encoding="utf-8"` matters most on Windows. Without it, Python uses the platform's default encoding, which on Windows has traditionally been a legacy code page such as cp1252. That code page has no →, no ├ and no └ – the build would crash with `UnicodeEncodeError`. The pages declare `<meta charset="utf-8">`, so the bytes must be UTF-8.

The other files:

- The legal pages – two loops over `LEGAL` (section 26): every page, every language. `site/de/` exists by then: the first loop created it. `for L, (path, _, _) in pages.items()` unpacks a nested tuple in one step: the key into `L`, the (path, title, body) tuple into its parts. Then the same pattern as above: build the path with `/`, generate the HTML, pass it through `dots()`, write it. `(SITE / path)` needs the parentheses so `.write_text` applies to the joined path, not to the string.
- `.htaccess` – `HTACCESS`, above, with `__HASHES__` replaced by the two hashes, separated by a space: `'sha256-…' 'sha256-…'`. The leading dot hides the file by default in `ls` and in the macOS Finder.
- `de/.htaccess` – two lines, a comment and `ErrorDocument 404 /de/404.html`: Apache reads an `.htaccess` per folder, and this one overrides the root's 404 page for everything under `/de/`. It is written after the loop, which has created `site/de/` by then. The call no longer fits on one line, so it continues inside the parentheses of `write_text(…)`, aligned under the first argument.
- `assets/torch.json` – the torch's second level (section 28): for every rule, its selector, its line number in this file and the lines. About 12 KB, fetched by `site.js` only when the torch is first switched on. `ensure_ascii=False` keeps the `·` in the code as it is instead of `\u00b7`.
- `robots.txt` – `User-agent: *` addresses all crawlers, `Allow: /` permits everything, `Sitemap:` gives the absolute URL of the sitemap.

The sitemap:

- `today = date.today().isoformat()` – the date as `YYYY-MM-DD` (for example `2026-10-29`), the format sitemaps expect.
- `alts` – one `<xhtml:link>` per language, from `HOME` (section 5): `.items()` gives the pairs code, address. The block is the same for every URL, since every language version lists all versions.
- `urls` – one `<url>` per language; `.values()` gives the addresses alone.
- The `<urlset>` declares two namespaces: the sitemap format itself and `xhtml`, which provides the `<xhtml:link>` elements for language versions.
- Trade-off, as the comment says: `lastmod` is the build date. Every build on a new day changes `sitemap.xml`, even when no page changed – expect a diff in that file. Google states that it only uses `lastmod` when the value is consistently accurate, so the field carries little weight either way.
- The legal pages and the 404s are not in the sitemap – consistent with their `noindex`.

The report line:

- `SITE.rglob("*.html")` – all `.html` files under `site/`, recursively. `sorted()` orders them; `p.relative_to(SITE)` shortens each to `de/index.html` and so on; `str()` turns the `Path` back into text for `join`.
- Pitfall: the line lists what is on disk, not what was just written. The build never deletes anything – if you remove or move a page in `build()`, its old HTML file stays in `site/`, keeps being published and keeps appearing in this line. Delete it by hand – `git rm` – as with `impressum.html` and `datenschutz.html` when they moved to `de/`. On the server the same: the upload adds and replaces, it does not delete.

```python
if __name__ == "__main__":
    build()
```

- `__name__` is `"__main__"` when the file runs as a script and `"build"` when another program imports it. The guard means: import for inspection (as in the parity check in section 8) without writing any files.

---

## 31 · Running it, output, and why site/ is committed

Run from the repository root:

```
python3 src/build.py
```

On Windows: `py src\build.py`. Thanks to `SITE`, the working directory does not matter. The run takes a fraction of a second and prints:

```
ok: 404.html, de/404.html, de/datenschutz.html, de/impressum.html, de/index.html, index.html, legal-notice.html, privacy.html
```

What it writes (and overwrites):

| File | Made by |
|---|---|
| `site/index.html` | `page(CONTENT["en"])` → `dots()` |
| `site/de/index.html` | `page(CONTENT["de"])` → `nbsp()` → `dots()` |
| `site/404.html` | `not_found(CONTENT["en"])` → `dots()` |
| `site/de/404.html` | `not_found(CONTENT["de"])` → `dots()` |
| `site/legal-notice.html` · `site/privacy.html` | `legal("imprint", "en")` · `legal("privacy", "en")` → `dots()` |
| `site/de/impressum.html` · `site/de/datenschutz.html` | `legal("imprint", "de")` · `legal("privacy", "de")` → `dots()` |
| `site/.htaccess` | `HTACCESS` with the hashes of `THEME_BOOT` and `SPECULATION` |
| `site/de/.htaccess` | fixed string, two lines |
| `site/assets/torch.json` | `torch_map()` |
| `site/robots.txt` | f-string with `URL` |
| `site/sitemap.xml` | `LANGS` plus build date |

What it never touches: `site/assets/site.css`, `site/assets/site.js`, `site/assets/fonts/`, `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `site.webmanifest`, `og-image.png`. Those are hand-made: the CSS and JavaScript are edited directly in `site/`; the icons, the manifest and the preview image come from `src/monogram/`, the source of the "PS" monogram:

- `src/monogram/README.md` – the mark's construction, colors, sizes and the full file list.
- `src/monogram/source/` – the generator (`ps_monogram.py`) and the hand-drawn pixel grids for the 16 and 32 pixel favicons (`favicons.py`). The generator writes the favicon set to `out/final/favicon/` (`python3 ps_monogram.py --favicons` writes only that set, to `out/`, and draws a preview sheet with `favicon_preview.py`); from there the files are copied to `site/` by hand.
- `src/monogram/og/og.html` – the source of `og-image.png`: a 1200 × 630 page with the hero text and the monogram on the right, as tall as the text block (274 px, cap height of the name to the prompt), the two centred on the card with 72 px margins (13.11.2026; `src/monogram/CHANGELOG.md`). Open it at exactly that size and take a screenshot; the comment at the top of the file shows how.

`head()` only links these files. Changing an icon means regenerating it there, not editing `build.py`.

Two of them the build reads: `VERSION` hashes `site.css` and `site.js` for the `?v=` in every page (section 10).

Working rules:

- Copy or markup change → edit `src/build.py` → run the build → check the result in `site/`.
- `site.css` or `site.js` changed → run the build as well: every page carries their fingerprints, and without a new one, browsers keep the old file for up to a year.
- `THEME_BOOT` or `SPECULATION` changed → upload `.htaccess` with the pages: it carries their hashes, and a page with a new script under an old policy reports a violation (once the policy enforces: a script that does not run).
- Checks after a build: the Nu Html Checker (validator.w3.org/nu, version 26.9.30) finds no error in the HTML of the eight pages. Its CSS checker does not know `container` and `@container` yet and reports them as errors (chapter 3) – the browsers know them. The policy: on a local Apache, all eight pages, with torch, keys card, theme switch and minimap used – no violation in the console.
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

1. **Change the motto.** Set `MOTTO = "sudo dream plan ship it"`. In `site/index.html` the new motto appears three times: in the source comment at the top and twice in the hero prompt (`.cmd` and `.sr-only`); `site/de/index.html`, the two 404s and the four legal pages change too. Then search `site/assets/site.js` for "plan ship": the console greeting still shows the old motto, because `site.js` is not generated and its copy does not follow.
2. **Swap the footnotes.** In `CONTENT["en"]["facts"]`, change `"Data Scientist[[ds]] · MLOps Engineer[[mlops]]"` to `"MLOps Engineer[[mlops]] · Data Scientist[[ds]]"`. In `site/index.html` the MLOps reference now carries 3 and Data Scientist 4 – the two videos in Experience keep 1 and 2 –, and the Sources list has swapped the two. `site/de/index.html` is unchanged – each language numbers its own footnotes.
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
- **Web app manifest** – a JSON file linked with `<link rel="manifest">` that describes a site as an installable app: name, colors, icons, display mode. Here it supplies the home-screen icons.
- **Popover** – an element with the `popover` attribute: hidden until a button with `popovertarget` or a script opens it, then drawn above the whole page, closed again by a click outside or Esc. Here: the torch's keys card (chapter 4).
- **Disclosure** – a control that shows and hides a block of content. HTML has one built in: `<details>` with its `<summary>`, used for the Posterlounge promotions and the six early positions (both written by `steps()`) and for the jump control's list.
- **Generated content** – text that CSS inserts with `content` in `::before` or `::after`, such as the bold copy of each menu label that reserves its width (`content: attr(data-label)`). It is drawn, but it is not part of the page's text: copy and paste, search engines and parsers do not get it. Words and punctuation that carry meaning belong in the HTML.
- **Visually hidden text** – text that is in the HTML but shrunk out of sight by CSS (here the class `sr-only`), so screen readers and anything that reads the text still get it: the word behind each drawn arrow, the full motto in the hero, the "(opens in a new tab)" after each link that leaves the site.
- **`target="_blank"` and `noopener`** – `target="_blank"` opens a link in a new tab; `rel="noopener"` keeps the new page from reaching back to the one that opened it through `window.opener`. Here both come from `offsite()`, for every link that leaves the site.
- **Content security policy** – an HTTP header that names where a page may load scripts, styles, images and other resources from; inline scripts it allows by the hash of their content. In report-only mode it reports violations in the console and blocks nothing.
- **Speculation rules** – a `<script type="speculationrules">` with JSON that lets the browser prefetch or prerender pages before a click. Chrome and Edge read it; other browsers skip it.
- **Fingerprint** – a short hash of a file's content in its URL (`site.css?v=5c417903`): a new version gets a new address, so browsers may keep each version as long as they like.
- **Relative vs root-absolute path** – `assets/site.css` or `../assets/site.css` resolve from the current page's folder; `/assets/site.css` resolves from the domain root.
- **Non-breaking space** – U+00A0 or `&nbsp;`: looks like a space, but a line never breaks there.

[Next: The HTML](02-html.md)
