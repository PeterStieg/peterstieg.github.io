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

- `date` – `date.today()` supplies the copyright year in `footer()`, the `lastmod` date in the sitemap and the end month of the role that is still running in `months()`.
- `escape as e` – `html.escape` under a one-letter alias, because it is called dozens of times inside f-strings and `{e(text)}` keeps those lines short. It replaces the five characters that have meaning in HTML: `&` → `&amp;` · `<` → `&lt;` · `>` → `&gt;` · `"` → `&quot;` · `'` → `&#x27;`.
- Why escaping matters: unescaped, a `<` in the copy opens a tag, an `&` may start an entity, and a `"` inside an attribute value ends the attribute – the page breaks in ways that are hard to spot. If text ever comes from outside (a form, an API, a spreadsheet export), the same gap lets a `<script>` in that text run in the visitor's browser: cross-site scripting (XSS). All copy here is your own, so the practical risk is broken markup; the habit protects you the day content comes from elsewhere.
- Pitfall: never use `e` as a variable name in this file. Inside a function, even `except Exception as e:` turns `e` into a local variable for the whole function, and every `e(...)` call in it fails with `UnboundLocalError`.
- `Path` – object-oriented file paths: `/` joins parts, `.parent` goes up a level, `.mkdir()`, `.write_text()` and `.rglob()` do the file work.
- `json` – serializes the structured-data block in `jsonld()`.
- `re` – regular expressions for three text markers: `*italics*`, syllable dots and `[[footnotes]]` – and for the `MM/YYYY` dates of the roles.

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
DEMO_DS = "https://feb25-bds-rakuten.streamlit.app/"       # Streamlit Community Cloud: sleeps when idle, wakes on request
DEMO_MLOPS = "https://may25-bds-rakuten.streamlit.app/"
```

- `SITE` – the output folder, computed rather than typed:
  - `__file__` is the path of this script as Python received it, possibly relative (`src/build.py`).
  - `.resolve()` makes it absolute and resolves symbolic links.
  - `.parent` is `src/`, `.parent.parent` the repository root.
  - `/ "site"` appends the folder name. Result: the script writes to the right place no matter which directory you start it from.
- `URL` ends with a slash. Every use concatenates (`URL + slug`, `f"{URL}og-image.png"`), so the trailing slash must stay and the parts appended to it must not start with one.
- `DEMO_*` – the two capstone apps on Streamlit Community Cloud. An app that nobody has opened for a while goes to sleep; the first visitor sees a wake-up button and waits about a minute.
- `EMAIL`, `LINKEDIN`, `GITHUB`, `REPO_*`, `DEMO_*` – each defined once and used in several places (contact section, JSON-LD, legal pages, project links). Change once, rebuild, done.
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
# four chapters, like the parts of a slide deck: the first section of each is numbered and linked in the menu,
# the sections after it belong to it – P⁴ to Profile, Education to Experience, Approach to Projects, Sources to Contact
CHAPTERS = {"profile": ["fields"], "experience": ["education"], "projects": ["approach"], "contact": ["notes"]}
SECTIONS = [k for first, rest in CHAPTERS.items() for k in (first, *rest)]   # page order: profile, fields, experience …
```

- `P4` – the four headings of the P⁴ section. `page()` pairs them by position with `CONTENT[lang]["fields"]`.
- `P4_TAIL` – an extra closing line for selected fields, keyed by index (3 = People). A dict instead of a list because only some fields have a tail; `i in P4_TAIL` checks the keys.
- `SLOGANS` – paired by position with `CONTENT[lang]["approach"]`.
- `PROJECTS_LEAD` – the note behind the superscript i after the Projects heading (a toggletip, section 20).
- `CHAPTERS` – the page's four chapters, like the four parts of a slide deck. Each key opens a chapter and is linked in the menu; the list holds the sections that follow it and belong to it. The order of the keys is the order of the chapters, so `profile` is 01 and `contact` 04. The keys are the English ones, so both languages share the numbers.
- The page order must match: every section in a list comes right after its chapter's first section. That is why Education stands behind Experience in `page()`, not at the end.
- `SECTIONS` – all eight section keys in page order, derived from `CHAPTERS`: `["profile", "fields", "experience", "education", "projects", "approach", "contact", "notes"]`. The jump control lists the sections from it (section 22).
  - A list comprehension with two `for` clauses reads like two nested loops, left to right: for each chapter (`first`, `rest`), for each `k` in that chapter.
  - `(first, *rest)` builds a tuple: the opener, then the items of `rest` unpacked into it. `("experience", *["education"])` is `("experience", "education")`.
  - Derived, not typed: add a section to `CHAPTERS` and it appears in the jump control's list with the right number. The order of the `out.append` calls in `page()` still has to follow by hand.
- Pitfall: pairing by position. Reorder `P4` without reordering both `fields` lists and every text lands under the wrong heading. And `zip()` stops at the shorter list: a missing fourth text silently drops "People" – no error.

---

## 7 · NOTES, companies and stacks

```python
# Footnotes: verification links (QR codes on the Liora diplomas, thekey.career, edX), plus course pages where they exist.
# "title": one string, or one per language; "when": which date label (issued | completed), default issued;
# "by": the organisation behind the credential, for the structured data (hasCredential → recognizedBy).
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
}

# the ledger names a company, the name links to its role under Experience (role "id")
COMPANIES = {"e-service-check": "E+SERVICE+CHECK", "brandible": "Brandible", "posterlounge": "Posterlounge"}

STACK_DS = "Python · Keras · PyTorch · Google Cloud"
STACK_MLOPS = "Docker · Airflow · MLflow · FastAPI · Grafana"
```

- `NOTES` – a dict of dicts. The outer key (`"ds"`, `"mlops"`, `"ihk"`, `"edx"`) is the footnote ID: it appears in the `[[ds]]` markers in the copy and in the HTML ids `fn-ds` and `ref-ds`.
- Inner keys:
  - `title` – the credential's name. One string when it is the same in both languages, a dict with one string per language when not (the IHK certificate). `note_title()` (section 12) picks the right one.
  - `verify` – the verification page: the URL behind the QR code on the Liora diplomas, the certificate pages on thekey.career and edX.
  - `course` – the course page. Optional: the IHK and edX entries have none, and the Sources list then leaves the link out.
  - `date` – one preformatted string per language.
  - `when` – which label goes before the date. Optional, default `"issued"`. The IHK page says the course was *completed* on that date, so its entry says `"completed"`; the label text itself lives in `CONTENT[lang]["notes"]`.
  - `by` – the organisation behind the credential, for the structured data (section 19).
- Why preformatted dates instead of `date` objects: Python's month names (`%B` in `strftime`) follow the system locale, and switching to a German locale depends on what the machine has installed. Two literal strings avoid that entirely.
- `NOTES` feeds both the visible footnotes in `page()` and the credentials in `jsonld()` – one source, two outputs.
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
        "theme": ("Theme", "Light", "Dark"), "arrow": "to", "to_top": "Back to top", "info": "Info",
        "dur": ("year", "years", "month", "months"),
        "jump": {"label": "Sections", "menu": "All sections", "up": "Up: %s", "down": "Down: %s"},
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
            ("€6k → €240k", "monthly media budget at a RoAS of 4.0", "posterlounge"),
            …
        ],
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, SEO and marketplaces. …",
            …
        ],
        "people_note": "Processes fit people, not the other way round.",
        "roles": [
            {"id": "e-service-check", "when": "since 11/2025", "title": "Head of Marketing", "org": "E+SERVICE+CHECK GmbH", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.",
             "tree": [("Team", "…"),
                      ("Scope", "…"),
                      ("Result", "…")]},
            …
            {"id": "posterlounge", "when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge GmbH", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Art prints online in more than 15 European countries.",
             "tree": [("Team", "…"),
                      ("Scope", "…"),
                      ("Result", "…")],
             "path": ("Three promotions", [("10/2017", "SEA Manager"), ("", "Digital Marketing Manager"),
                             ("", "Senior Marketing Manager"), ("06/2021", "Head of Marketing")])},
            …
            {"when": "10/2010 – 08/2014", "title": "Marketing, market research, export", "org": "Five companies", "place": "Rome",
             "tree": [("Scope", "…")],
             "more": ("All five positions", [
                 {"when": "04/2014 – 08/2014", "title": "Marketing Consultant", "org": "SBS systems for business solutions Srl", "place": "Rome",
                  "tree": [("Scope", "…")]},
                 {"when": "06/2013 – 05/2014", "title": "Corporate investigations", "org": "Inner Valor Srl", "place": "Rome", "tree": []},
                 …
             ])},
        ],
        "groups": [
            ("At E+SERVICE+CHECK", [
                ("Call and inquiry pipeline", "…", "Python · BigQuery · Data Studio", []),
                …
            ]),
            ("Certification capstones", [
                ("Rakuten product classification", "…", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                …
            ]),
        ],
        "approach": [
            "Every figure on this page can be backed up on request. …",
            …
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora in partnership with Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Agile project management specialist[[ihk]]", "IHK"),
            …
            ("Languages", ["German (native)", "English C2", "Italian C2", "Spanish B1", "French A2"], ""),
        ],
        "offline": ("Leipzig.", "Before: Rome, Trento, Jinotega (Nicaragua), Orem (Utah)."),
        "notes": {"issued": "issued", "completed": "completed", "verify": "Verify credential", "course": "Course page", "back": "Back to text"},
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
| `arrow` | str | the word behind a drawn → (`"to"` / `"auf"`): what screen readers say and what copied text reads |
| `to_top` | str | label of the jump control's up link while it leads to the top of the page (`"Back to top"` / `"Nach oben"`) |
| `info` | str | spoken name of the superscript i that opens a toggletip |
| `dur` | 4-tuple | the words for the durations under the role dates: year, years, month, months (`duration()`, section 21). Joined by commas, they also go to `site.js`, which recounts the running role |
| `jump` | dict | the jump control: `label` names its `<nav>`, `menu` the button that opens the section list, `up` and `down` are templates in which `%s` stands for a section name (`"Up: %s"` → "Up: Experience") |
| `skip` | str | text of the skip link |
| `nav` | list of (id, label) | header links |
| `sec` | dict | section headings, keyed by internal section name |
| `notes` | dict | labels in the Sources list, incl. the two date labels `issued` and `completed` |
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
| `ledger_label`, `ledger` | str, list of (figure, context, company key) | the results list in the profile; the key looks up the name in `COMPANIES` and links to the role with that `id` |
| `fields` | list of 4 str | the P⁴ section, paired with `P4` |
| `people_note` | str | the toggletip after the People heading in P⁴ |
| `roles` | list of dicts | Experience: `id` (optional: the anchor the ledger links to), `when` (`"MM/YYYY – MM/YYYY"`, or `"since MM/YYYY"` for the role that is still running – `months()` reads the dates), `title`, `org`, `url` (optional: the company's website), `place` (may be `""`), `ctx` (optional), `tree` (list of (label, text), may be empty), `path` (optional: (label, list of (date or `""`, title)) – the titles within one role, behind a disclosure), `more` (optional: (label, list of sub-roles) – the single positions behind a disclosure, each a role dict of its own) |
| `groups` | list of (title, items) | Projects; each item is (name, text, stack, links) – `links` a list of (label, URL) pairs, empty when there is nothing to link |
| `approach` | list of 3 str | paired with `SLOGANS` |
| `facts` | list of (label, value, sub-line or `""`) | Education; the value is a string, or a list of strings shown one per line (the languages) |
| `offline` | 2-tuple | Contact: current city, earlier places |

### How EN and DE mirror each other

- Same keys, same shapes, same number and order of list items. The only key that exists in one language and not the other is `ids` – English uses the internal keys directly as anchors.
- Localized, not translated: German uses KUR, English RoAS (rule 2), job titles follow German usage ("Leiter Marketing"), number formats follow each language ("6.000 → 240.000 €" vs "€6k → €240k"), and trade terms follow each language's habit – "marketing automation" (Brandible, Rapidobject) is "Marketing Automation" in German, the English term German marketing uses, capitalized as a German noun.
- English inside German: the tree labels `"Team"`, `"Scope"` and `"Result"` stay English in the DE dict (rule 5). Every role uses the same three, in that order, wherever there is something to say – a role without a team simply has no `"Team"` row.
- Not localized at all: the company keys at the end of each `ledger` entry and the role `id`s they point to. `#posterlounge` is the anchor on both pages, unlike the section anchors, which `ids` translates.
- Nested lists mirror too: the five sub-roles under `"more"` and the four titles under `"path"` exist in both dicts, in the same order. Only the labels differ ("Three promotions", "Drei Beförderungen"); the titles are the same in both, because they are the titles that were held.
- Nothing checks parity. A key missing in DE raises `KeyError` as soon as `page()` asks for it – loud and easy to find. A missing list item – a role or project only added in EN – is silent: the German page simply shows one entry fewer. Edit both languages in the same sitting.
- Quick parity check from the repository root (importing does not build anything, see section 28):

  ```
  python3 -c "import sys; sys.path.insert(0, 'src'); import build as b; print(set(b.CONTENT['en']) ^ set(b.CONTENT['de']))"
  ```

  It prints `{'ids'}`. Anything else means a key is missing on one side. (`^` on sets is the symmetric difference: elements in exactly one of the two.)

### Markers inside the copy

| Marker | Example | Becomes | Handled by |
|---|---|---|---|
| `→` | `"€6k → €240k"` | a drawn SVG arrow, its word kept as visually hidden text | `t()` |
| `*word*` | `"[*marketer* × *tinkerer*]"` | `<i>word</i>` – words cited as words, like in a dictionary | `t()` |
| `[[key]]` | `"Data Scientist[[ds]]"` | a numbered footnote reference to `NOTES[key]` | regex in `page()`, education section |
| ` · ` | `"Python · BigQuery · Data Studio"` | a middle dot glued to the word before it | `dots()` |

Pitfall: the markers only work where the code runs the text through the matching function. `t()` handles `entry["ety"]`, the first item of each `ledger` entry and the values in each role's `tree`. The `[[…]]` regex runs only on the middle value of each `facts` tuple, and only when that value is a string – the items of a list go through `e()` alone. Everywhere else – `profile`, `fields`, `people_note`, `ctx`, `path`, `groups`, `approach` – the text only goes through `e()`: asterisks stay visible and `→` stays a plain character in a fallback font.

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
- `dots()` deliberately leaves this comment alone (section 27).

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
DOWN_SVG = ('<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
            '<path d="M8 2.5v10.7M3.4 8.8 8 13.4l4.6-4.6"/></svg>')
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
                flags=re.S)
```

- Inline SVG as strings, pasted straight into the HTML: no image requests, and the icons can take the text color.
- Why draw the arrow: the site font, Atkinson Hyperlegible, has no → glyph. The browser would borrow it from a fallback font with a different weight and baseline. Sun, moon, the two jump arrows and the three lines have no font equivalent anyway.
- `UP_SVG` and `DOWN_SVG` – the two ends of the jump control (section 22). `DOWN_SVG` also follows each company name in the results ledger, as a small superscript ↓ (section 24). It is `UP_SVG` mirrored: the shaft runs from y = 2.5 down to 13.2 (`v10.7` – a vertical line, relative), the head points down.
- `LINES_SVG` – three horizontal strokes of different lengths (`h11`, `h9`, `h7`), the second one indented: lines of code, like the bars of the minimap. It sits in the middle of the jump control as long as there is no chapter number to show – at the top of the page and without JavaScript.
- `viewBox="0 0 16 10"` – the internal coordinate system (16 × 10 units). The real size comes from CSS (`.arr` is 0.95em × 0.62em), so the icon scales with the text.
- `<path d="…">` – drawing commands. In the arrow: `M1 5` moves the pen to (1, 5), `h13.5` draws a horizontal line 13.5 units to the right (the shaft), `M10 1.2` jumps to the top of the head, `14 5` draws to the tip (coordinate pairs after an `M` count as line commands), `l-4 3.8` draws relative to the tip down to the bottom of the head. Uppercase = absolute coordinates, lowercase = relative.
- No `fill` or `stroke` in the markup: the CSS sets `fill: none; stroke: currentColor`, so every icon takes the current text color. Dark mode and hover colors work without a second set of icons.
- `aria-hidden="true"` – screen readers skip the drawing. The meaning comes from elsewhere: the arrow's word "to" in a visually hidden span next to it (section 13), the button's `aria-label`, the link text of the ledger's company names.
- `focusable="false"` – Internet Explorer and old Edge put inline SVGs into the keyboard tab order. This switches that off; modern browsers ignore it.

**The logo** is the one SVG that is not typed in here. `LOCKUP` reads the lockup from its own folder, `src/lockup/`, where `lockup_takt50.py` builds it from the font (see `src/lockup/README.md`):

- `Path(__file__).resolve().parent / "lockup" / "out" / "lockup.svg"` – the file next to `build.py`, wherever you start the script from (the same trick as `SITE`, section 3).
- `.read_text(encoding="utf-8").strip()` – the file as a string, without the line break at its end.
- `re.sub(r"<svg ([^>]*)>(.*)</svg>", …, flags=re.S)` – rewrites the file in one step:
  - Group 1, `([^>]*)`, is everything inside the opening tag: its attributes (`viewBox`, `role="img"`, `aria-label="Peter Stieg"`). Group 2, `(.*)`, is everything between the tags: the two paths.
  - The replacement puts `class="lockup"` in front of the attributes and wraps the paths in `<g class="still">`. `\1` and `\2` insert the groups. The `r` in front of the string makes it a raw string: Python leaves the backslashes alone, and `re.sub` reads `\1` as "group 1". Without the `r`, Python would turn `\1` into a control character before `re.sub` ever saw it.
  - `re.S` lets `.` match line breaks too, in case the file ever spans several lines.
- Why the file stays untouched: it is the design's output. Regenerate it, rebuild, and the site has the new logo – no copying of path data.
- The paths fill from `var(--accent)` and `var(--ink)` (inline `style` in the file), so the logo follows light and dark like the text. The `.still` group is what `site.js` hides while it draws the condensing wordmark in the same SVG.

---

## 12 · sid and num

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
- Result: English → `"experience"`, German → `"stationen"`. German visitors get German anchors (`/de/#stationen`).
- Pitfall: `nav` holds its own copy of these IDs. Rename an ID in `ids` without changing `nav` and the header link points to an anchor that no longer exists. No error – the link just stops scrolling.

`note_title` returns a footnote's title in the page language:

```python
def note_title(c, note):
    """A footnote's title in the page language – NOTES titles are a string or one per language."""
    return note["title"][c["lang"]] if isinstance(note["title"], dict) else note["title"]
```

- `isinstance(x, dict)` – true when `x` is a dict. Most titles are one string for both languages; only the IHK certificate has a German and an English name.
- Why not `title`: `head()` and `legal()` have a parameter called `title`. Inside those functions it would hide a function of the same name – the same trap as `t` in `topbar` (section 17).

`num` gives a section its chapter number. Headings and menu both call it, so the two can never disagree.

- `CHAPTERS.items()` – the (key, list) pairs in order: `("profile", ["fields"])`, `("experience", ["education"])` …
- `enumerate(…, 1)` – counts along, starting at 1 instead of 0. Each round gets the number `i` and the pair, unpacked into `first` and `rest`.
- `if key == first or key in rest` – the section opens this chapter or belongs to it. `num("fields")` and `num("profile")` both return `"01"`.
- `:02d` – a format spec: an integer (`d`), at least two digits wide, padded with zeros (`0`). 1 becomes `01`.
- `return ""` – after the loop: a section in no chapter. None exists today; the empty string keeps `chapter_no()` (section 20) working if one is added.

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
  - `sr-only` ("screen reader only") is a CSS class that shrinks an element to one clipped pixel: invisible on screen, but still text. The hero prompt uses the same class for the motto (section 24).
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
<link rel="icon" href="{r}favicon.ico" sizes="48x48">
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
<link rel="manifest" href="{r}site.webmanifest">
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
- Four icon lines, all with `{r}` – relative to where the page lives. All four files are drawn from the "PS" monogram; they are made in `src/monogram/`, not here (section 29).
  - `favicon.ico` with `sizes="48x48"` – the classic format: one file that holds several bitmaps, here 16, 32 and 48 pixels. Why it still exists next to the SVG: not every browser takes an SVG favicon (Safari did not for a long time), and some programs ask for `/favicon.ico` directly without reading the page at all – feed readers, bookmark services, older browsers. On top of that, the 16 and 32 pixel versions are drawn by hand on the pixel grid, which stays sharper in a browser tab than any automatic downscaling of the vector. `sizes` names the largest bitmap in the file: a fixed size marks the ICO as the bitmap fallback, so a browser that understands SVG prefers the vector, which fits any size.
  - `favicon.svg` – the vector mark. It carries its own `prefers-color-scheme` rule and switches to the lighter accent in dark mode. `type="image/svg+xml"` lets a browser that cannot use SVG icons skip the file.
  - `apple-touch-icon` – the icon iOS shows when someone adds the page to the home screen: a 180 × 180 pixel PNG, because iOS takes neither the SVG nor the ICO here.
  - `manifest` – `site.webmanifest`, a small JSON file that describes the site as a web app: its name, a short name, the colors, and two more icons (192 and 512 pixels). Android and Chrome take their home-screen and install icons from it. Its `"display": "browser"` keeps the site an ordinary page in a browser tab even when opened from the home screen – the manifest is here for the icons, not to turn the site into an app.
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
    return f'<span class="langs" role="group" aria-label="{e(c["aria_lang"])}">{" ".join(items)}</span>'
```

- The docstring names the two current languages. The output itself follows `LANGS`, so a third entry there would appear in the switch automatically.
- `items = []` plus `append` – an explicit loop, because each language takes one of two shapes.
- `for code, label, name, path, _ in LANGS` – full unpacking; the slug is not needed here.
- Current language: a `<span>`, not a link – a link to the page you are on is noise. `aria-current="page"` tells screen readers "this is the current one"; the CSS rule `.langs [aria-current]` sets it in bold.
- Other languages: `<a href="{r}{path}">` – from the English page `de/index.html`, from the German page `../index.html`. `hreflang` states the language of the target page; `lang` the language of the link text itself; `title` shows the full name on hover.
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
def topbar(c, sections=True, langs=True):
    r = c["root"]
    keys = {sid(c, k): k for k in CHAPTERS}          # localized id → section key, for the number
    # number as on the heading; data-label: CSS reserves the bold width, so marking the current section does not shift the menu
    links = "\n".join(f'<a class="sect" href="#{i}"><span class="no" aria-hidden="true">{num(keys[i])}</span> '
                     f'<span class="label" data-label="{e(t)}">{e(t)}</span></a>' for i, t in c["nav"]) if sections else ""
    switch = lang_switch(c) if langs else ""
    # the wordmark the hero name docks into – invisible, it only gives site.js the target to measure
    word = f'<span class="word" aria-hidden="true"><span class="caret">&gt;_</span><span class="name">{NAME}</span></span>' if sections else ""
    return f"""<a class="skip" href="#main">{e(c['skip'])}</a>
<header class="top">
<div class="wrap">
<a class="home" href="{'#top' if sections else r + c['path']}">{word}{LOCKUP}</a>
<nav class="nav" aria-label="{e(c['aria_main'])}">{links}
{switch}
{theme_switch(c)}</nav>
</div>
</header>
"""
```

- `sections`, `langs` – switches. The main pages get section links and the language switch; legal and 404 pages pass `False` for both.
- `keys` – a dict comprehension that turns the lookup around. `nav` holds the localized ids (`"stationen"`), `num()` needs the section key (`"experience"`). Looping over `CHAPTERS` loops over its keys – the four sections the menu links to. So `keys` maps each id back to its key: `{"profil": "profile", "stationen": "experience", …}` on the German page; in English, id and key are the same.
- `links = "\n".join(…) if sections else ""` – the conditional expression wraps the whole join, so the generator only runs when `sections` is true.
  - `"\n"` – a line break between the links. Like the space in the language switch (section 15), it is there for the text: the number span has no space before it, so without a separator the menu's text reads "01 Profile02 Experience". With it, copy and paste and search engines get "01 Profile 02 Experience …".
  - Two f-strings in a row, without a `+` between them, are joined into one string by Python itself. That splits a long line without changing the result.
  - `for i, t in c["nav"]` – unpacks each (id, label) pair. Here `t` is a loop variable that shadows the function `t()`. It works because a generator expression has its own scope – outside it, `t()` is untouched – but it is confusing. Do not copy the pattern.
  - `href="#{i}"` – an in-page anchor.
  - `<span class="no" aria-hidden="true">{num(keys[i])}</span>` – the chapter number, the same as on the heading: "01 Profile", "02 Experience". Hidden from screen readers, so the link is still called "Profile".
  - `<span class="label" data-label="{e(t)}">` – the label in its own span, plus a copy as a data attribute. `site.js` marks the section being read in bold; the CSS uses the copy to reserve the bold width in advance (chapter 3, Navigation). The span is needed because the trick works on the label alone – the number stays regular.
- `switch = lang_switch(c) if langs else ""` – same pattern.
- The skip link comes first in the page so it is the first thing the Tab key reaches. CSS keeps it off-screen until it receives keyboard focus; it jumps to `<main id="main">`.
- `<header class="top">` and `<div class="wrap">` – the page header and a width-limiting layout container.
- The home link: `{'#top' if sections else r + c['path']}` – a full conditional expression inside a replacement field. On the main page it jumps to the hero (`#top`). On other pages it links to that language's home page: `"" + "de/index.html"` on the legal pages, `"/" + "index.html"` on the 404 page.
- `{word}{LOCKUP}` – the link holds two things:
  - `word` – the old wordmark `>_ PETER STIEG`, on the main pages only. The CSS keeps it invisible; it is the target the hero name flies into, because `site.js` measures where its letters sit. `aria-hidden` on the whole span, so screen readers do not read "greater than underscore Peter Stieg" twice.
  - `LOCKUP` – the logo `>_ P/S` (section 11), on every page. Its `role="img"` and `aria-label="Peter Stieg"` give the link its name: screen readers say "Peter Stieg, link".
  - `&gt;_` – `>` written as an entity, so the parser cannot mistake it for the end of a tag.
- `<nav aria-label=…>` – a named navigation landmark. The name matters because the page has two navs (header and footer).
- `{links}`, `{switch}` and `{theme_switch(c)}` on lines of their own – the same whitespace for the same reason: "Contact EN DE" instead of "ContactENDE". `.nav` is a flex container, so the line breaks do not move anything; the gaps between the items come from `gap` in the CSS.

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
            {"@type": "EducationalOccupationalCredential", "name": note_title(c, n), "url": n["verify"],
             "recognizedBy": {"@type": "Organization", "name": n["by"]}}
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
- `"hasCredential"` – a list comprehension: `[{…} for n in NOTES.values()]` builds one credential object per footnote. Dicts keep insertion order (guaranteed since Python 3.7), so the order is always that of `NOTES`: Data Scientist, MLOps Engineer, IHK, edX.
  - `note_title(c, n)` – the credential's name in the page language.
  - `n["by"]` – who stands behind it: the Sorbonne for the Liora certificates, the IHK-Projektgesellschaft for the IHK course, Microsoft for the edX course.
- `json.dumps(data, ensure_ascii=False)` turns the dict into JSON text. The default (`ensure_ascii=True`) would write `"Università"`; `False` keeps `"Università"`. Both are valid JSON; the second is shorter and readable, and safe because the file is written as UTF-8.
- Why no `e()` here: the content of a `<script>` element is raw text. The browser does not decode entities inside it, so `&amp;` would land literally in the JSON.
- Pitfall: `json.dumps` does not protect against the sequence `</script>`. A string containing it would close the script element early. All values here are your own constants, so it cannot happen today. If outside data is ever fed in, replace `"</"` with `"<\/"` in the output.

---

## 20 · chapter_no and info

Two small helpers for headings: the chapter number in front, a toggletip behind.

```python
def chapter_no(key):
    """The number before a section title: visible if the section opens a chapter, invisible (.ghost) for the rest,
    so the titles line up."""
    ghost = "" if key in CHAPTERS else " ghost"
    return f'<span class="no{ghost}" aria-hidden="true">{num(key)}</span> ' if num(key) else ""
```

- The number before a section title, as a finished span. Two places show it: the section headings (`section()`, section 21) and the list in the jump control (section 22). Both call this one function, so the two can never disagree.
- `ghost` – a second class for the sections that do not open a chapter (P⁴, Education, Approach, Sources). `key in CHAPTERS` checks the dict's keys only, so it is true just for the four chapter openers.
- The span holds the number from `num(key)` (section 12). P⁴ gets `<span class="no ghost">01</span>`: the number of its chapter, which the CSS makes invisible. It still takes up its width, so "P⁴" starts exactly where "Profile" does – an outline, without any measuring. An empty string counts as false, so `if num(key)` is enough.
  - `aria-hidden="true"` – screen readers skip the number and announce "Profile", not "zero one Profile". The number is a visual signpost; the order of headings already carries the structure.
  - The space after `</span>` sits outside the span, so the plain text of the heading still reads "01 Profile" for search engines and copy-paste.

```python
def info(c, key, text, lang=""):
    """Toggletip: a superscript i after a heading, the note opens next to it as a popover – no JavaScript needed.
    Returns the button (it goes into the heading; its i is drawn by CSS) and the note (it goes after the heading) – so the
    heading's text stays its title for anything that reads the page as text. lang: the note's language where it differs
    from the page's."""
    tip = f"tip-{key}"
    lang_attr = f' lang="{lang}"' if lang else ""
    return (f'<button type="button" class="info" popovertarget="{tip}" aria-label="{e(c["info"])}"></button>',
            f'<span class="tip" id="{tip}" popover{lang_attr}>{e(text)}</span>')
```

- A toggletip: a small button that shows a short note when clicked or tapped and hides it again on the next click. Unlike a tooltip, which appears on hover, it works the same with a mouse, a finger and the keyboard (Enter or Space on the focused button). The page has two: after the People heading in P⁴ and after the Projects heading.
- `tip = f"tip-{key}"` – the note's id: `tip-people`, `tip-projects`. Ids must be unique on a page, so every call needs its own key.
- `lang_attr` – an optional `lang` attribute for the note, for where its language differs from the page's. The Projects note is English on the German page (rule 5).
- The return value is a pair – a tuple of two strings, the button and the note, separated by the comma at the end of the first line. The caller unpacks it and puts the two in different places:
  - the button into the heading, right after the title – the superscript i belongs there;
  - the note after the heading – for People right after the `</h3>`, for Projects as the first thing in the section's body (section 21).
- Why apart: everything inside a heading is part of its text. Programs that read the HTML as text – search engines, tools that extract a profile from a page – take a heading as one string. With the i and the note inside, the People heading would read "PeopleiProcesses fit people, not the other way round." Now it reads "People", and the Projects heading "03 Projects": the title, nothing else. On screen nothing changes – `site.js` places the open note next to the i wherever the note sits in the HTML.
- The button:
  - `type="button"` – the safe habit (section 16).
  - `popovertarget="{tip}"` – the HTML popover API. A button with this attribute opens and closes the element with that id, provided the element carries the `popover` attribute. The browser does it on its own, without JavaScript. The two do not need to be next to each other.
  - It is empty in the HTML. The visible `i` comes from the CSS – `.info::after { content: "i"; }` – and is set as a superscript there. Text that CSS generates with `content` is drawn but is not part of the page's text, so the heading reads "People", not "Peoplei". `aria-label` gives the button its real name: "Info". The browser also tells screen readers whether the note is open or closed.
- The note:
  - `popover` – short for `popover="auto"`: the element stays hidden until its button opens it. Then it is drawn in the top layer – above everything else on the page, regardless of `z-index`, and never cut off by a parent element. "Auto" also brings light dismiss: a click outside the note or the Esc key closes it, and opening another auto popover closes the first.
  - Where it appears: without JavaScript, the browser's default style centers it in the window. `site.js` places it right next to the i, keeps it there while the page scrolls and closes it once the i leaves the screen (chapter 4).
  - `{e(text)}` – the note is copy, so it is escaped.
- A browser without popover support does not know the attribute and shows the `<span>` as ordinary text. The CSS builds on that: `@supports not selector(:popover-open)` hides the i and sets the note as a muted line between the heading and the text (chapter 3). The note is never lost.

---

## 21 · section, tree, months and duration

```python
def section(c, key, title_html, body, cls="body", tip=None):
    i = sid(c, key)
    label = f"h-{i}"
    if tip:                                            # the section is named by its title, not by the i
        button, note = tip
        title_html, label, body = f'<span id="t-{i}">{title_html}</span>{button}', f"t-{i}", note + "\n" + body
    return f"""<section class="sec" id="{i}" aria-labelledby="{label}">
<h2 id="h-{i}">{chapter_no(key)}{title_html}</h2>
<div class="{cls}">
{body}</div>
</section>
"""
```

- The wrapper for every content section of the main page.
- `cls="body"` – a default parameter: used when the caller passes nothing. No caller currently passes another value.
- `tip=None` – an optional toggletip: the (button, note) pair from `info()` (section 20). `None` means "no toggletip"; `if tip:` is false for it. Only Projects passes one; the People toggletip belongs to an `<h3>` inside P⁴ and is placed in `page()`.
- `i = sid(c, key)` – the localized anchor.
- `label` – the id of the element that names the section; normally the heading's, `h-{i}`.
- `aria-labelledby="{label}"` – the text of the element with that id becomes the section's name, and a named `<section>` is exposed as a landmark that screen-reader users can jump between.
- `if tip:` – with the i inside the heading, the heading's accessible name includes the button's name: pointing at the `<h2>` would name the section "Projects Info". So the title gets a span of its own, `<span id="t-{i}">`, and the label points there – the section is called "Projects".
  - `button, note = tip` – unpacks the pair into two names. A `tip` that is not a pair raises `ValueError`.
  - `title_html, label, body = …, …, …` – tuple assignment: three names get new values in one statement. Python evaluates the whole right side first, so the new title is built from the old title and the new body from the old body.
  - The button goes after the title span, inside the heading. The note goes in front of the body, followed by a line break: it becomes the first thing in `<div class="body">`, right under the heading – outside it, so the heading's text stays "03 Projects" (section 20).
  - The `<h2>` keeps `id="h-{i}"` either way. The footnote references point at the Sources heading by that id (section 24).
- `{chapter_no(key)}{title_html}` – number, then title (section 20).
- `title_html` – the name says it: raw HTML, inserted unescaped. Callers pass `e(s["profile"])` and so on, or `title_of()` for P⁴ (section 22), which returns markup. Pitfall: pass plain copy here without `e()` and the first `&` breaks the markup.
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
- `if rows else ""` – a role with nothing to list (one of the five early positions) gets no list at all. An empty `<ul></ul>` would be valid HTML, but a screen reader may still announce "list, 0 items", and the list's margin would leave a gap.
- `{e(k)}:` – the colon after the label is part of the text, inside the bold span. It could come from the CSS (`content: ":"`), but generated content is not part of the page's text: copied or extracted, the line would read "Scope SEA, social media …" with nothing between label and text. The CSS only draws the branch lines, with `::before` and `::after` on each `<li>` – lines are presentation, the colon is punctuation.

```python
def months(when):
    """Length of a role in months, counted like LinkedIn: first and last month included (10/2017 – 06/2023: 69).
    "since 11/2025" runs to the build date; site.js recounts it when the page loads."""
    dates = [(int(y), int(m)) for m, y in re.findall(r"(\d{2})/(\d{4})", when)]
    (y1, m1), (y2, m2) = dates[0], dates[1] if len(dates) > 1 else (date.today().year, date.today().month)
    return (y2 - y1) * 12 + m2 - m1 + 1
```

- The length of a role in months, read from its `when` string. `role()` (section 23) prints it under the dates.
- Counted like LinkedIn: the first and the last month both count. 10/2017 – 06/2023 is (2023 − 2017) × 12 + 6 − 10 + 1 = 69 months. Without the `+ 1`, the result is the number of steps from one month to the other, 68 – and a role from 03/2025 to 03/2025 would last zero months.
- `re.findall(r"(\d{2})/(\d{4})", when)` – every date in the string:
  - `\d` is one digit, `{2}` exactly two of them, `/` a literal slash, `\d{4}` four digits. The parentheses make month and year two groups.
  - With groups in the pattern, `findall` returns one tuple of the groups per match: `"10/2017 – 06/2023"` gives `[("10", "2017"), ("06", "2023")]`, `"since 11/2025"` gives `[("11", "2025")]`. The words around the dates do not matter.
- `[(int(y), int(m)) for m, y in …]` – a list comprehension that unpacks each tuple into month and year, turns both into numbers and puts the year first: `[(2017, 10), (2023, 6)]`.
- The second line unpacks start and end in one statement:
  - The right side is a tuple of two items, separated by the comma: `dates[0]` and `dates[1] if len(dates) > 1 else (…)`. The conditional expression binds more tightly than the comma, so the `if … else` decides the second item only.
  - Two dates: the end is `dates[1]`. One date, as for a role that is still running: the end is the year and month of today – the build date.
  - The left side, `(y1, m1), (y2, m2)`, is nested unpacking: two pairs, each split into year and month.
- `(y2 - y1) * 12 + m2 - m1 + 1` – whole years in months, plus the difference of the months, plus one. The month difference may be negative (6 − 10 = −4); the year term makes up for it.
- The running role: "since 11/2025" built in October 2026 counts 11/2025 – 10/2026, 12 months. That number is right on the day of the build and then ages until the next one. So `role()` hands the start to `site.js`, which counts again in the visitor's browser (chapter 4).
- Pitfalls: a `when` without an `MM/YYYY` date finds nothing, and `dates[0]` raises `IndexError` – loud. That is why the entry for the years before 2014 carries exact months, "10/2010 – 08/2014": a duration needs months. Quieter: a one-digit month. `"03/2025 – 7/2025"` finds only the first date (`\d{2}` wants two digits), and the role counts as still running. Always write months with two digits.

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

---

## 22 · title_of and jump

```python
def title_of(c, key):
    return 'P<sup>4</sup>' if key == "fields" else e(c["sec"][key])
```

- A section's title as HTML: the escaped heading from `sec`, or for P⁴, which has no entry in `sec`, the fixed markup with a superscript 4. `page()` uses it for the P⁴ heading, `jump()` for every item of its list – so the list shows the titles exactly as the headings do.

```python
def jump(c):
    """Up, the sections, down – fixed bottom right once the name has docked (replaces the old back-to-top button).
    site.js points up and down at the section above and below and shows the chapter number in the middle.
    Without JavaScript: up goes to the top, the menu works (details), down is hidden."""
    j = c["jump"]
    items = "".join(f'<li><a href="#{sid(c, k)}" data-t="{"P⁴" if k == "fields" else e(c["sec"][k])}">'
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
  - `<span class="cur" aria-hidden="true"></span>` – empty in the HTML. `site.js` writes the current chapter number into it, "01" to "04". While it is empty, the CSS shows `LINES_SVG` (section 11) instead; once it holds a number, the icon hides.
  - `<ol>` – an ordered list, because the sections have an order.
- The down link: `href` points at the first section, `SECTIONS[0]`, and the label names it. That is correct at the top of the page, where "down" means Profile.
  - `j['down'] % c['sec'][SECTIONS[0]]` – Python's `%` operator on a string fills in `%s`: `"Down: %s" % "Profile"` gives `"Down: Profile"`. The same template serves Python here and `site.js` later (`.replace("%s", …)`).
  - Without JavaScript, the CSS hides the down link: a fixed target would be wrong as soon as the page scrolls. It still gets a real target because `THEME_BOOT` sets the `js` class before `site.js` has even loaded. If `site.js` then fails, the CSS shows the link anyway, and it should lead somewhere sensible.
- Where it goes in the page: after the footer (section 24).

---

## 23 · role

```python
def role(c, ro, h="h3"):
    """One role: dates and duration, title, company and place, context, the tree – and behind a disclosure
    the promotions within it (Posterlounge) or the single positions it sums up (before 2014)."""
    place = f'&nbsp;<span class="place">· {e(ro["place"])}</span>' if ro.get("place") else ""
    ctx = f'<p class="ctx">{e(ro["ctx"])}</p>' if ro.get("ctx") else ""
    org = f'<a href="{ro["url"]}">{e(ro["org"])}</a>' if ro.get("url") else e(ro["org"])
    # the duration under the dates; a role that is still running carries its start, so site.js can recount it
    start = re.search(r"(\d{2})/(\d{4})", ro["when"])
    live = (f' data-from="{start[2]}-{start[1]}" data-units="{",".join(c["dur"])}"'
            if len(re.findall(r"\d{2}/\d{4}", ro["when"])) == 1 else "")
    when = f'{e(ro["when"])}<br><span class="dur"{live}>{duration(c, months(ro["when"]))}</span>'
    more = ""
    if ro.get("path"):                                 # titles in order, dates where known
        label, steps = ro["path"]
        lis = "".join(f'<li>{e(title)}' + (f' <span class="muted">· {e(at)}</span>' if at else "") + '</li>'
                      for at, title in steps)
        more += f'<details class="more">\n<summary>{e(label)}</summary>\n<ol class="tree">{lis}</ol>\n</details>\n'
    if ro.get("more"):
        label, subs = ro["more"]
        lis = "".join(f'<li class="role">\n{role(c, sub, "h4")}</li>\n' for sub in subs)
        more += f'<details class="more">\n<summary>{e(label)}</summary>\n<ol class="roles">\n{lis}</ol>\n</details>\n'
    return f"""<p class="when">{when}</p>
<div>
<{h}>{e(ro['title'])}</{h}>
<p class="org">{org}{place}</p>
{ctx}{tree(c, ro['tree'])}
{more}</div>
"""
```

- One entry of the Experience timeline: dates with duration, title, company with place, context line, tree, disclosures – the inside of an `<li class="role">`. The `<li>` itself is written by the caller, because only `page()` gives a role its `id` (section 24).
- `place` – optional field: `ro.get("place")` returns `None` when the key is missing and `""` when it is empty (Rapidobject). Both are falsy, so no place span appears.
- `&nbsp;` before the span – the same job as `dots()`: "· Laucha" must not start a new line. `dots()` cannot do it here, because it only matches the plain sequence ` · `, and here a `<span>` tag sits between the space and the dot. So the place line brings its own non-breaking space.
- `ctx` – the optional context line, same pattern.
- `org` – the company name, as a link to its website when the role has a `url` (E+SERVICE+CHECK, Brandible, Posterlounge). The name is escaped inside the link; the URL is one of your own constants and goes in as it is.

The dates and the duration:

- `start = re.search(r"(\d{2})/(\d{4})", ro["when"])` – the first date in the string, the start. `re.search` stops at the first match and returns a match object. Indexing it is short for `.group()`: `start[1]` is group 1, the month (`"11"`), `start[2]` group 2, the year (`"2025"`).
- `live` – two extra attributes for the role that is still running, an empty string for all others:
  - `len(re.findall(r"\d{2}/\d{4}", ro["when"])) == 1` – exactly one date in `when` means "since …": the role has no end yet. This pattern has no groups, so `findall` returns the matched strings themselves; only their number counts here.
  - `data-from="{start[2]}-{start[1]}"` – the start, year first: `"2025-11"`. `site.js` splits it at the hyphen.
  - `data-units="{",".join(c["dur"])}"` – the four words of `dur`, joined with commas: `"year,years,month,months"`, on the German page `"Jahr,Jahre,Monat,Monate"`. `site.js` splits them again, so the script contains no words in either language – the same idea as the jump control's `data-up` and `data-down` (section 22).
  - With both, `site.js` counts the running role again when the page loads, by the same rule as `months()` and in the same words as `duration()` (chapter 4). With JavaScript, the page never shows a stale duration, however long ago the last build was; without, it shows the count of the build day.
  - The leading space in `' data-from=…'` belongs to the attribute string, so every other role gets a clean `<span class="dur">` – the pattern of `rid` and `en_attr` (section 24). The outer parentheses let the expression span two lines.
- `when` – the dates, escaped, then `<br>`, then `<span class="dur">` with the duration from `duration(c, months(…))` (section 21). Result for the running role: `since 11/2025<br><span class="dur" data-from="2025-11" data-units="year,years,month,months">1 year</span>`.
  - The `<br>` puts the duration on a line of its own under the dates. It also keeps the two apart in text taken from the page, where a `<br>` becomes a line break: without it, the Posterlounge dates would read "10/2017 – 06/20235 years 9 months".
  - The CSS sets `.dur` a little smaller than the dates (chapter 3).

The disclosures:

- `more` – up to two disclosures, collected into one string. It starts empty, and each `+=` appends one, in a fixed order: first `path`, then `more`. Today each entry has at most one of them.
- `path` – used by Posterlounge: the four titles held within that one role, from SEA Manager (10/2017) to Head of Marketing (06/2021), behind "Three promotions". The titles are the words people search for; in the disclosure they are part of the page's text without lengthening the timeline. The context line, `ctx`, describes the company only.
  - `label, steps = ro["path"]` – the summary text and the list of (date, title) pairs.
  - `for at, title in steps` – the date comes first in each pair, the title first in the output. `at` is a date or `""`: the two promotions in between have no date on the page.
  - Three strings joined with `+`: the opening `<li>` with the title, the date as ` · 10/2017` in a muted span – or nothing –, the closing `</li>`. Pitfall: the parentheses around the middle part are required. Without them, Python reads `A + B if at else "" + C` as `(A + B) if at else ("" + C)`: a title with a date loses its closing `</li>`, and a title without one shrinks to a bare `</li>`.
  - `<ol class="tree">` – an ordered list, because the titles have an order. The class `tree` borrows the #JobAlert branch lines from the CSS, so the promotions read as a path; `.more .tree` gives it its distance from the summary (chapter 3).
  - No headings and no recursion here: the titles are steps within one role, not roles of their own.
  - The wrapper is the same `<details class="more">` as for the five positions below, so it looks and behaves the same, `site.js` included.
- `more` – used by one entry: "10/2010 – 08/2014 · Five companies" keeps the timeline at one line for those years and holds the five single positions behind a disclosure.
  - `label, subs = ro["more"]` – the summary text ("All five positions") and the list of sub-roles.
  - `role(c, sub, "h4")` – the function calls itself, once per sub-role: recursion. A sub-role is a role dict like any other, so the same code renders it. The recursion ends because the sub-roles have no `"more"` of their own: those calls return without calling `role()` again.
  - `h` – the heading level, `"h3"` unless the caller says otherwise. The sub-roles sit below the `<h3>` of their summary entry and pass `"h4"`, so the outline stays correct: Experience (h2) › Marketing, market research, export (h3) › Marketing Consultant (h4).
  - The sub-roles get an `<ol class="roles">` of their own, inside `<details class="more">` – the same native disclosure as in the jump control: closed by default, opened by click or keyboard, announced as collapsed or expanded. `site.js` adds two things: it redraws the minimap when the disclosure opens, because the page just got longer, and it opens the disclosure for printing (chapter 4).
- `<{h}>{e(ro['title'])}</{h}>` – a replacement field can produce part of a tag name: `<h3>` or `<h4>`.
- Required fields (`when`, `title`, `org`, `tree`) use `ro['…']`: a missing key raises `KeyError`. That is intended – a role without a title should fail loudly. `tree` may be an empty list (Inner Valor); `tree()` then returns `""`. `when` must hold at least one `MM/YYYY` date, for `months()` (section 21).
- `{ctx}{tree(c, ro['tree'])}` – context line and tree directly after each other, then the disclosure, if there is one.

---

## 24 · page – one complete language version

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
    out.append('<div class="minimap" aria-hidden="true"></div>\n<main id="main">\n<div class="wrap">\n')
```

- The list starts with four parts: the head (canonical URL = `URL + slug`, for example `https://peterstieg.com/de/`), the JSON-LD block, the closing `</head>` with the opening `<body>`, and the header.
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

- `id="top"` – target of the home link and of the jump control's up link – its first target, and its only one without JavaScript.
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
    # each result names its company; the name leads to the role under Experience
    # ↓: superscript and in accent like the footnote numbers and the i – a link that stays on this page
    led = "".join(f'<div><dt>{t(c, a)}</dt><dd>{e(b)} · <a href="#{k}">{e(COMPANIES[k])}'
                  f'<span class="jmp">{DOWN_SVG}</span></a></dd></div>\n' for a, b, k in c["ledger"])
    out.append(section(c, "profile", e(s["profile"]),
                       f'{entry}<p>{e(c["profile"])}</p>\n<dl class="ledger" aria-label="{e(c["ledger_label"])}">\n{led}</dl>\n'))
```

- `d = c["entry"]` – a short local name.
- `hw = re.sub(r"([·|])", …, e(d["hw"]))` – escape first, then wrap each syllable separator in a span so CSS can mute it.
  - `[·|]` is a character class: one character that is either the middle dot (English dictionary style: mar·ke·tin·ker·er) or the pipe (Duden style: Mar|ke|tin|ke|rer). Inside square brackets `|` is a literal character, not "or".
  - `( )` captures the separator as group 1; `\1` in the raw replacement string puts it back inside the span.
- `entry` – the dictionary entry. `<dfn>` marks the term being defined – the right element for a headword. `pos` and `def` go through `e()`, `ety` through `t()` for its italics.
- `led` – the results list as a description list: `<dt>` holds the figure (through `t()` for the arrows; "> 2×" becomes `&gt; 2×`), `<dd>` the context, a middle dot and the company. A `<div>` around each `dt`/`dd` pair is valid inside `<dl>` and gives CSS one box per row.
  - `for a, b, k in c["ledger"]` – each entry is a 3-tuple: figure, context, company key. The generator spans two lines – two adjacent f-strings, joined into one; inside the parentheses of `join()` Python needs no line-continuation sign.
  - `<a href="#{k}">{e(COMPANIES[k])}…</a>` – the company's name from `COMPANIES` (section 7), as a link to the role with that `id` under Experience. In the CSS, `.role:target` colors the dates and title of the role the visitor arrived at (chapter 3).
  - `<span class="jmp">{DOWN_SVG}</span>` – a small ↓ after the name, inside the link. The CSS sets it superscript and in the accent color, like the footnote numbers and the i: a mark that says "this link stays on this page and leads down". An ↗ would say the opposite – by convention it marks a link that leaves the site. The SVG is `aria-hidden`, so the link's name stays the company's name. The link's underline does not run under the arrow: the span is an inline-block, and text decoration does not reach into inline-blocks (chapter 3).
  - The ` · ` before the link is glued to the context by `dots()` later.
  - Pitfalls: a key missing from `COMPANIES` raises `KeyError` – loud. A key that no role carries as its `id` is silent: the link points at nothing and does not scroll.
- `section(…)` – heading escaped, body = entry + profile paragraph + results list with its own `aria-label`.

### P⁴

```python
    # P⁴ – four fields, each a P; People carries its principle as a note behind the i
    p4 = []
    for i, (p, txt) in enumerate(zip(P4, c["fields"])):
        tail = f' <strong lang="en">{e(P4_TAIL[i])}</strong>' if i in P4_TAIL else ""
        button, note = info(c, "people", c["people_note"]) if p == "People" else ("", "")
        p4.append(f'<div><h3{en_attr}>{e(p)}{button}</h3>{note}<p>{e(txt)}{tail}</p></div>\n')
    out.append(section(c, "fields", title_of(c, "fields"), f'<div class="fields">\n{"".join(p4)}</div>\n'))
```

- `zip(P4, c["fields"])` pairs each heading with its text; `enumerate(…)` adds a counter. `for i, (p, txt) in …` unpacks both levels at once: the counter, then the pair.
- `if i in P4_TAIL` – `in` on a dict checks its keys. Only index 3 (People) gets the tail, marked English.
- `button, note = … if p == "People" else ("", "")` – the toggletip for People (section 20), two empty strings for the other three fields. `p == "People"` compares with the English word from `P4`, which is the same on both pages.
  - The conditional expression yields a pair either way, and the pair is unpacked into two names. Pitfall: `else ""` would not do – unpacking an empty string into two names raises `ValueError: not enough values to unpack`.
  - No language argument: the note sits after the English `<h3>`, not inside it, so it inherits the page's language – German on the German page, English on the English one. Only the Projects note needs one: the slogan stays English on the German page, so it passes `"en"` there.
  - `{e(p)}{button}</h3>{note}` – the i follows the word without a space, like a footnote number, inside the heading. The note follows the closing `</h3>`, between heading and text.
- `<h3{en_attr}>` – the P-words are English on both pages.
- The section key is `"fields"`, but `sec` has no `"fields"` heading: `title_of()` (section 22) returns the fixed markup `P<sup>4</sup>` in every language. The German anchor is `p-wie-peter`.

### Experience

```python
    # experience – each role as a #JobAlert-style tree
    roles = []
    for ro in c["roles"]:
        rid = f' id="{ro["id"]}"' if ro.get("id") else ""     # the ledger links here
        roles.append(f'<li class="role"{rid}>\n{role(c, ro)}</li>\n')
    out.append(section(c, "experience", e(s["experience"]), f'<ol class="roles" reversed>\n{"".join(roles)}</ol>\n'))
```

- `role(c, ro)` renders the inside of each entry (section 23); the loop only adds the `<li>` around it.
- `rid` – the anchor the ledger links to, for the three roles that carry an `id`. The leading space belongs to the attribute string, so a role without an id gets a clean `<li class="role">` – the same pattern as `en_attr`.
- On phones, where the section heading sticks under the header, the CSS gives `.role` a `scroll-margin-top`: a role reached from the ledger stops below the stuck heading instead of under it (chapter 3).
- `<ol class="roles" reversed>` – an ordered list, because sequence matters; `reversed` makes the numbering count down, so the newest role at the top carries the highest number. It is a boolean attribute: present means true.

### Education – where the footnotes are created

```python
    # education – certificates carry footnotes
    fa = []
    for k, v, sub in c["facts"]:
        subtxt = f'<br><span class="muted">{e(sub)}</span>' if sub else ""
        if isinstance(v, list):                             # one per line: the languages
            val = '<ul class="lines">' + "".join(f"<li>{e(x)}</li>" for x in v) + "</ul>"
        else:
            val = re.sub(r"\[\[(\w+)\]\]", fn, e(v))
        fa.append(f"<div><dt>{e(k)}</dt><dd>{val}{subtxt}</dd></div>\n")
    out.append(section(c, "education", e(s["education"]), f'<dl class="facts">\n{"".join(fa)}</dl>\n'))
```

- The block sits right behind Experience: Education belongs to chapter 02 (`CHAPTERS`), so it follows Experience on the page – and here, because the order of the `out.append` calls is the order of the page.
- `for k, v, sub in c["facts"]` – each fact is a 3-tuple; an empty `sub` means "no second line".
- `isinstance(v, list)` – the value is a string or a list. The list – the languages – becomes `<ul class="lines">` with one `<li>` per item; the CSS removes the bullets, so each language stands on its own line.
  - A list rather than `<br>` line breaks, because it is one: screen readers announce "list, 5 items" and can step through it. A `<ul>` is allowed inside `<dd>`.
  - `'<ul class="lines">' + "".join(…) + "</ul>"` – three strings joined with `+`.
  - Each item goes through `e()` only – no footnote markers in a list.
- `re.sub(r"\[\[(\w+)\]\]", fn, e(v))` – for string values:
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
            ln = "".join(f' · <a href="{url}">{e(label)}</a>' for label, url in links)
            lis.append(f'<li><h4>{e(name)}</h4><p>{e(text)}</p><p class="stack">{e(stack)}{ln}</p></li>\n')
        groups.append(f'<div class="group"><h3>{e(gt)}</h3>\n<ul class="projects">\n{"".join(lis)}</ul></div>\n')
    out.append(section(c, "projects", e(s["projects"]), "".join(groups),
                       tip=info(c, "projects", PROJECTS_LEAD, "en" if L != "en" else "")))
```

- Two nested loops: groups (`gt` = group title), then projects within a group.
- `for name, text, stack, links in items` – each project is a 4-tuple. A tuple with three or five values raises `ValueError`.
- `ln` – one ` · <a …>` per (label, URL) pair: "GitHub · Demo" for the capstones. For an empty list the generator yields nothing and `"".join` returns `""`, so projects without links need no special case. The ` · ` separators get glued by `dots()` later.
- The section body is the joined groups alone.
- `tip=info(…)` – a keyword argument: `section()` has two optional parameters, `cls` and `tip`, and naming `tip` skips `cls`. The toggletip holds `PROJECTS_LEAD`, which is English on every page; on the German page, under the heading "Projekte", it gets `lang="en"`. `info()` returns the (button, note) pair as it is; `section()` puts the button into the heading, the note at the start of the body, and names the section by its title alone (section 21).
- `name` is a local variable here; it does not clash with the constant `NAME` (Python is case-sensitive).

### Approach

```python
    # approach – three of a kind: X, not Y
    pr = "".join(f'<li><p><strong lang="en">{e(a)}</strong> {e(b)}</p></li>\n' for a, b in zip(SLOGANS, c["approach"]))
    out.append(section(c, "approach", e(s["approach"]), f'<ul class="principles">\n{pr}</ul>\n'))
```

- `zip(SLOGANS, c["approach"])` – English slogan plus localized sentence, paired by position.
- The slogan is marked `lang="en"` on both pages.

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
        course = f' · <a href="{n["course"]}" hreflang="en">{e(nl["course"])}</a>' if n.get("course") else ""
        notes.append(f'<li id="fn-{key}"><a class="back" href="#ref-{key}" aria-label="{e(nl["back"])}">^</a> '
                     f'{e(note_title(c, n))} · {e(nl[n.get("when", "issued")])} {e(n["date"][L])} · '
                     f'<a href="{n["verify"]}">{e(nl["verify"])}</a>{course}</li>\n')
    out.append(section(c, "notes", e(s["notes"]), f'<ol class="notes">\n{"".join(notes)}</ol>\n'))
```

- This loop runs after the education section, so `order` is already filled. The order of the `out.append` calls is load-bearing: build Sources before Education and the list comes out empty.
- Only footnotes that were actually referenced appear, in the order they were referenced. `<ol>` numbers its items 1, 2, … automatically – matching the numbers `fn()` produced, because both follow `order`.
- `id="fn-{key}"` – the target of the superscript link. `<a class="back" href="#ref-{key}">^</a>` – the way back, with a spoken label.
- `n["date"][L]` – the date string for the current language.
- `nl[n.get("when", "issued")]` – two lookups in one: first which label the note wants (`"issued"` unless it says otherwise), then that label in the page language: "issued", "completed", "ausgestellt am", "abgeschlossen am".
- `course` – the course link, or nothing when the note has no course page. `hreflang="en"` – the course pages are in English.
- Three adjacent f-strings inside the `append(…)` parentheses form one string.

### Closing

```python
    out.append("</div>\n</main>\n")
    out.append(footer(c))
    out.append(jump(c))
    out.append(f'<script src="{c["root"]}assets/site.js" defer></script>\n</body>\n</html>\n')
    return "".join(out)
```

- Closes the `wrap` div and `<main>`, adds the footer.
- `jump(c)` – the jump control (section 22) comes after the footer. The CSS fixes it to the corner of the window, so its place in the HTML does not decide where it appears. It decides two other things:
  - Tab order: keyboard focus reaches the control last, after the content and the footer links, instead of before the content.
  - The CSS fades it in with `.top.docked ~ .jump` – "a `.jump` that comes after the docked header, under the same parent". The `~` combinator only looks forward, so the control has to follow the header; both are direct children of `<body>`.
- `defer` – the script downloads while the HTML is parsed and runs only after parsing is complete. By then every element exists, so `site.js` can query all of them.
- `"".join(out)` – one string for the whole page.

---

## 25 · Legal pages

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
<p>Die Seite verlinkt auf LinkedIn, GitHub, die Kursseiten von Liora, die Nachweisseiten von DataScientest, thekey.career und edX, die Demos der Abschlussprojekte bei Streamlit sowie die Websites früherer und heutiger Arbeitgeber. Erst wenn Sie einem dieser Links folgen, verarbeiten die jeweiligen Anbieter Daten nach ihren eigenen Datenschutzbestimmungen.</p>
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

## 26 · not_found

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

## 27 · nbsp and dots – typography after the fact

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

## 28 · build – writing to disk

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
    (SITE / ".htaccess").write_text("ErrorDocument 404 /404.html\nAddType application/manifest+json .webmanifest\n",
                                    encoding="utf-8")
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
- `.htaccess` – configuration for Apache web servers, two lines. Other servers ignore the file. The leading dot hides it by default in `ls` and in the macOS Finder.
  - `ErrorDocument 404 /404.html` – "for a 404, deliver `/404.html`".
  - `AddType application/manifest+json .webmanifest` – "send files ending in `.webmanifest` with this media type". Every response carries a `Content-Type` header that tells the browser what the bytes are. `application/manifest+json` is the registered type for web app manifests, but Apache's built-in list of extensions does not necessarily contain `.webmanifest`; without this line the manifest from `head()` (section 14) may go out under a generic type.
  - The call no longer fits on one line, so it continues inside the parentheses of `write_text(…)`, aligned under the first argument.
- `robots.txt` – `User-agent: *` addresses all crawlers, `Allow: /` permits everything, `Sitemap:` gives the absolute URL of the sitemap.

The sitemap:

- `today = date.today().isoformat()` – the date as `YYYY-MM-DD` (for example `2026-10-28`), the format sitemaps expect.
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

## 29 · Running it, output, and why site/ is committed

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
| `site/.htaccess` | fixed string, two lines |
| `site/robots.txt` | f-string with `URL` |
| `site/sitemap.xml` | `LANGS` plus build date |

What it never touches: `site/assets/site.css`, `site/assets/site.js`, `site/assets/fonts/`, `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `site.webmanifest`, `og-image.png`. Those are hand-made: the CSS and JavaScript are edited directly in `site/`; the icons, the manifest and the preview image come from `src/monogram/`, the source of the "PS" monogram:

- `src/monogram/README.md` – the mark's construction, colors, sizes and the full file list.
- `src/monogram/source/` – the generator (`ps_monogram.py`) and the hand-drawn pixel grids for the 16 and 32 pixel favicons (`favicons.py`). The generator writes the favicon set to `out/final/favicon/`; from there the files are copied to `site/` by hand.
- `src/monogram/og/og.html` – the source of `og-image.png`: a 1200 × 630 page with the hero text and the monogram on the right. Open it at exactly that size and take a screenshot; the comment at the top of the file shows how.

`head()` only links these files. Changing an icon means regenerating it there, not editing `build.py`.

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
- **Recursion** – a function that calls itself for a part of its input, like `role()` for each sub-role. It ends where the input offers nothing more to recurse into.
- **Canonical and hreflang** – link annotations that tell search engines the preferred URL of a page and which language versions exist.
- **JSON-LD** – structured data in a `<script type="application/ld+json">` block, using the schema.org vocabulary.
- **Web app manifest** – a JSON file linked with `<link rel="manifest">` that describes a site as an installable app: name, colors, icons, display mode. Here it supplies the home-screen icons.
- **Popover and toggletip** – a popover is an element with the `popover` attribute: hidden until a button with `popovertarget` opens it, then drawn above the whole page, closed again by a click outside or Esc. A toggletip is the pattern built from it here: a small button that shows a short note on click instead of on hover.
- **Disclosure** – a control that shows and hides a block of content. HTML has one built in: `<details>` with its `<summary>`, used for the Posterlounge promotions, the five early positions and the jump control's list.
- **Generated content** – text that CSS inserts with `content` in `::before` or `::after`, such as the toggletip's i. It is drawn, but it is not part of the page's text: copy and paste, search engines and parsers do not get it. Words and punctuation that carry meaning belong in the HTML.
- **Visually hidden text** – text that is in the HTML but shrunk out of sight by CSS (here the class `sr-only`), so screen readers and anything that reads the text still get it: the word behind each drawn arrow, the full motto in the hero.
- **Relative vs root-absolute path** – `assets/site.css` or `../assets/site.css` resolve from the current page's folder; `/assets/site.css` resolves from the domain root.
- **Non-breaking space** – U+00A0 or `&nbsp;`: looks like a space, but a line never breaks there.

[Next: The HTML](02-html.md)
