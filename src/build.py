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
from datetime import date
from html import escape as e
from pathlib import Path
import json
import re

SITE = Path(__file__).resolve().parent.parent / "site"
URL = "https://peterstieg.com/"
EMAIL = "info@peterstieg.com"
LINKEDIN = "https://www.linkedin.com/in/peterstieg/"
GITHUB = "https://github.com/PeterStieg"
REPO_DS = "https://github.com/PeterStieg/feb25_bds_classification-of-rakuten-e-commerce-products"
REPO_MLOPS = "https://github.com/PeterStieg/may25_bmlops_classification-of-rakuten-e-commerce-products"
DEMO_DS = "https://feb25-bds-rakuten.streamlit.app/"       # Streamlit Community Cloud: sleeps when idle, wakes on request
DEMO_MLOPS = "https://may25-bds-rakuten.streamlit.app/"

NAME = "Peter Stieg"
TAGLINE = "Performance Marketing · Data Science"
CLAIM = "Marketing leadership with root access"
MOTTO = "sudo dream plan ship"
TITLE = f"{NAME} – {TAGLINE}"

LANGS = [("en", "EN", "English", "index.html", ""),
         ("de", "DE", "Deutsch", "de/index.html", "de/")]

# P as in Peter – English in every language, like M³ and F³.
P4 = ["Performance", "Pipelines", "Pixels", "People"]
P4_TAIL = {3: "Everything human:e."}
SLOGANS = ["Facts, not fluff.", "Built, not briefed.", "Prompted, not pasted."]
PROJECTS_LEAD = "Stop starting. Start finishing."
# four chapters, like the parts of a slide deck: the first section of each is numbered and linked in the menu,
# the sections after it belong to it – P⁴ to Profile, Education to Experience, Approach to Projects, Sources to Contact
CHAPTERS = {"profile": ["fields"], "experience": ["education"], "projects": ["approach"], "contact": ["notes"]}

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

STACK_DS = "Python · Keras · PyTorch · Google Cloud"
STACK_MLOPS = "Docker · Airflow · MLflow · FastAPI · Grafana"

CONTENT = {
    # ------------------------------------------------------------------ EN
    "en": {
        "lang": "en", "path": "index.html", "root": "", "locale": "en_GB",
        "aria_main": "Main", "aria_legal": "Legal", "aria_lang": "Language",
        "theme": ("Theme", "Light", "Dark"), "arrow": "to", "to_top": "Back to top",
        "desc": "Marketinkerer from Leipzig: performance marketing, lead generation and data science. Leadership roles at four companies, self-built tools.",
        "skip": "Skip to content",
        "nav": [("profile", "Profile"), ("experience", "Experience"), ("projects", "Projects"), ("contact", "Contact")],
        "sec": {"profile": "Profile", "experience": "Experience", "projects": "Projects", "approach": "Approach",
                "education": "Education", "contact": "Contact", "notes": "Sources"},
        "entry": {"hw": "mar·ke·tin·ker·er", "pos": "noun", "ety": "[*marketer* × *tinkerer*]",
                  "def": "A marketing leader who builds the tools behind the campaigns."},
        "profile": "Leadership roles at four companies, with interdisciplinary teams of up to six people in e-commerce and B2B. Certified Data Scientist and MLOps Engineer since 2025 – Liora, in partnership with Université Paris 1 Panthéon-Sorbonne.",
        "ledger_label": "Selected results",
        "ledger": [
            ("€6k → €240k", "monthly media budget at a RoAS of 4.0 · Posterlounge"),
            ("17 shops", "in 12 languages across the European Economic Area · Posterlounge"),
            ("RoAS 7.6 → 7.8", "on a €1.7m media budget, while spend grew · Brandible"),
            ("> 2×", "inbound inquiries year over year · E+SERVICE+CHECK"),
        ],
        "p4_intro": "P as in Peter.",
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, SEO and marketplaces. Steered by cost per inquiry, quote and order.",
            "Tracking with Google Tag Manager and Consent Mode v2, then Python, SQL, BigQuery and Data Studio on Google Cloud. Internal web apps in Streamlit.",
            "Corporate identity from claim to logo, websites, templates and employer branding. Figma, Inkscape, Canva – and Python wherever pixels can be generated.",
            "Teams of up to six, from SEA to graphic design, trained in performance marketing and data analysis. Processes fit people, not the other way round.",
        ],
        "roles": [
            {"when": "since 11/2025", "title": "Head of Marketing", "org": "E+SERVICE+CHECK GmbH", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.",
             "tree": [("Scope", "marketing, design and automation, built from scratch – SEA, SEO, CRM, events, employer branding"),
                      ("Result", "inbound inquiries more than doubled year over year; new corporate identity incl. groundwork for an EUIPO trademark")]},
            {"when": "05/2025 – 07/2025", "title": "MLOps Engineer (full-time)",
             "org": "Liora · Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Capstone", "the Rakuten model as a production pipeline – training, tracking, serving, monitoring")]},
            {"when": "03/2025 – 07/2025", "title": "Marketing & UX Design (part-time)", "org": "Rapidobject GmbH", "place": "",
             "tree": [("Scope", "UI concepts, usability tests, support for the migration from ActiveCampaign to Salesforce")]},
            {"when": "02/2025 – 05/2025", "title": "Data Scientist (full-time)",
             "org": "Liora · Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Capstone", "multimodal classification of e-commerce products with NLP and computer vision")]},
            {"when": "11/2023 – 12/2024", "title": "Head of Marketing", "org": "Brandible by KSi International GmbH", "url": "https://www.brandible.de/", "place": "Dresden",
             "ctx": "B2B promotional products for Germany, Austria and Switzerland.",
             "tree": [("Team", "five – marketing, graphic design, project management"),
                      ("Budget", "€1.7m across Google Ads, Microsoft Advertising, Meta and LinkedIn"),
                      ("Result", "RoAS 7.6 → 7.8 while spend grew; Microsoft Advertising +45% revenue at a RoAS of 9.9")]},
            {"when": "07/2023 – 10/2023", "title": "Chief Operating Officer", "org": "SportSpar GmbH", "place": "Leipzig",
             "tree": [("Scope", "e-commerce operations for discounted sporting goods, email automation, WhatsApp and Telegram")]},
            {"when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge GmbH", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Art prints online in more than 15 European countries.",
             "tree": [("Path", "SEA Manager in 2017 → Head of Marketing in 2021, three promotions"),
                      ("Team", "six – SEA, SEO, social, influencer, offline marketing, design"),
                      ("Result", "17 shops in 12 languages; media budget €6k → €240k a month at a RoAS of 4.0")]},
            {"when": "10/2014 – 04/2017", "title": "Online Marketing Manager", "org": "YOUniversal Media Srl", "place": "Rome",
             "tree": [("Scope", "client and in-house accounts for DE, FR, IT, SE, UK and US – search, social, native, retargeting")]},
            {"when": "2010 – 2014", "title": "Marketing, market research, export", "org": "Several companies", "place": "Rome",
             "tree": [("Scope", "export promotion, brand protection, competitive intelligence, web marketing")]},
        ],
        "groups": [
            ("At E+SERVICE+CHECK", [
                ("Call and inquiry pipeline", "More than half a million calls, two phone systems, five web forms – joined with Odoo master data and Google Ads attribution.", "Python · BigQuery · Data Studio", []),
                ("PRUEF+CHECK", "Rule-based validation of inspection checklists instead of manual Excel checks. From requirement to go-live: five days.", "Streamlit · Azure", []),
                ("Document extraction", "Around 14,000 unstructured supplier documents turned into structured records for ERP import.", "Python · Claude API", []),
                ("Customer portal", "Moved to a company-owned Azure tenant with separate production and staging. Running cloud costs: a fraction of before.", "Azure", []),
            ]),
            ("Certification capstones", [
                ("Rakuten product classification", "Around 85,000 e-commerce products classified from text and images.", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                ("Rakuten classification · MLOps", "The same model as a production pipeline: training, tracking, serving and monitoring.", STACK_MLOPS, [("GitHub", REPO_MLOPS), ("Demo", DEMO_MLOPS)]),
            ]),
        ],
        "approach": [
            "Every figure on this page can be backed up on request. Growth only counts when efficiency keeps pace.",
            "Knowing the systems underneath makes agencies easier to steer. And less necessary.",
            "AI is part of the toolbox – for code, copy and graphics. Nothing goes out unchecked.",
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora in partnership with Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Agile project management specialist (IHK)[[ihk]]", "with distinction"),
            ("2018", "Introduction to Artificial Intelligence[[edx]]", "Microsoft on edX"),
            ("2010", "Bachelor’s degree in economics", "Università degli Studi di Trento"),
            ("Languages", "German (native) · English C2 · Italian C2 · Spanish B1 · French A2", ""),
        ],
        "offline": ("Leipzig.", "Before: Rome, Trento, Jinotega (Nicaragua), Orem (Utah)."),
        "notes": {"issued": "issued", "completed": "completed", "verify": "Verify credential", "course": "Course page", "back": "Back to text"},
        "imprint": "Legal notice", "privacy": "Privacy",
        "jobtitle": "Head of Marketing",
    },
    # ------------------------------------------------------------------ DE
    "de": {
        "lang": "de", "path": "de/index.html", "root": "../", "locale": "de_DE",
        "aria_main": "Hauptnavigation", "aria_legal": "Rechtliches", "aria_lang": "Sprache",
        "theme": ("Darstellung", "Hell", "Dunkel"), "arrow": "auf", "to_top": "Nach oben",
        "desc": "Marketinkerer aus Leipzig: Performance Marketing, Leadgenerierung und Data Science. Führungsverantwortung in vier Unternehmen, Werkzeuge selbst gebaut.",
        "skip": "Zum Inhalt springen",
        "nav": [("profil", "Profil"), ("stationen", "Stationen"), ("projekte", "Projekte"), ("kontakt", "Kontakt")],
        "sec": {"profile": "Profil", "experience": "Stationen", "projects": "Projekte", "approach": "Arbeitsweise",
                "education": "Ausbildung", "contact": "Kontakt", "notes": "Quellen"},
        "ids": {"profile": "profil", "fields": "p-wie-peter", "experience": "stationen", "projects": "projekte",
                "approach": "arbeitsweise", "education": "ausbildung", "contact": "kontakt", "notes": "quellen"},
        "entry": {"hw": "Mar|ke|tin|ke|rer", "pos": "der; -s, -", "ety": "[engl. *marketer* × *tinkerer* ‚Tüftler‘]",
                  "def": "Marketingleiter, der die Werkzeuge hinter seinen Kampagnen selbst baut."},
        "profile": "Führungsverantwortung in vier Unternehmen, für interdisziplinäre Teams mit bis zu sechs Personen in E-Commerce und B2B. Seit 2025 zertifiziert als Data Scientist und MLOps Engineer – Liora in Partnerschaft mit der Université Paris 1 Panthéon-Sorbonne.",
        "ledger_label": "Ausgewählte Ergebnisse",
        "ledger": [
            ("6.000 → 240.000 €", "Mediabudget im Monat bei einer KUR von 25 % · Posterlounge"),
            ("17 Shops", "in 12 Sprachen im Europäischen Wirtschaftsraum · Posterlounge"),
            ("KUR 13,2 → 12,8 %", "bei ausgebautem Mediabudget von 1,7 Mio. € · Brandible"),
            ("> 2×", "Anfragen im Jahresvergleich · E+SERVICE+CHECK"),
        ],
        "p4_intro": "P wie Peter.",
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, SEO und Marktplätze. Gesteuert über Kosten je Anfrage, Angebot und Auftrag.",
            "Tracking mit Google Tag Manager und Consent Mode v2, danach Python, SQL, BigQuery und Data Studio auf Google Cloud. Interne Web-Apps mit Streamlit.",
            "Corporate Identity vom Claim bis zum Logo, Websites, Vorlagen und Employer Branding. Figma, Inkscape, Canva – und Python, wo sich Pixel generieren lassen.",
            "Teams mit bis zu sechs Personen, von SEA bis Grafik, geschult in Performance Marketing und Datenanalyse. Prozesse passen zu Menschen, nicht umgekehrt.",
        ],
        "roles": [
            {"when": "seit 11/2025", "title": "Leiter Marketing", "org": "E+SERVICE+CHECK GmbH", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-zertifizierte Prüfungen der elektrischen Sicherheit (DGUV V3/V4), bundesweit, 349 Mitarbeitende.",
             "tree": [("Scope", "Marketing, Design und Automatisierung von Grund auf aufgebaut – SEA, SEO, CRM, Events, Employer Branding"),
                      ("Result", "Anfragen im Jahresvergleich mehr als verdoppelt; neue Corporate Identity samt Grundlage der EUIPO-Markenanmeldung")]},
            {"when": "05/2025 – 07/2025", "title": "MLOps Engineer (Vollzeit)",
             "org": "Liora · Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Capstone", "das Rakuten-Modell als produktive Pipeline – Training, Tracking, Bereitstellung, Monitoring")]},
            {"when": "03/2025 – 07/2025", "title": "Marketing & UX-Design (Teilzeit)", "org": "Rapidobject GmbH", "place": "",
             "tree": [("Scope", "UI-Konzeption, Usability-Tests, Begleitung der Migration von ActiveCampaign zu Salesforce")]},
            {"when": "02/2025 – 05/2025", "title": "Data Scientist (Vollzeit)",
             "org": "Liora · Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Capstone", "multimodale Klassifikation von E-Commerce-Produkten mit NLP und Computer Vision")]},
            {"when": "11/2023 – 12/2024", "title": "Marketingleiter", "org": "Brandible by KSi International GmbH", "url": "https://www.brandible.de/", "place": "Dresden",
             "ctx": "B2B-Werbeartikel für Deutschland, Österreich und die Schweiz.",
             "tree": [("Team", "fünf Personen – Marketing, Grafik, Projektmanagement"),
                      ("Budget", "1,7 Mio. € über Google Ads, Microsoft Advertising, Meta und LinkedIn"),
                      ("Result", "KUR 13,2 → 12,8 % bei ausgebautem Budget; Microsoft Advertising +45 % Umsatz bei einer KUR von 10,1 %")]},
            {"when": "07/2023 – 10/2023", "title": "Chief Operating Officer", "org": "SportSpar GmbH", "place": "Leipzig",
             "tree": [("Scope", "E-Commerce-Betrieb für Sportartikel im Rabattsegment, E-Mail-Automatisierung, WhatsApp und Telegram")]},
            {"when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge GmbH", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Kunstdrucke online in über 15 europäischen Ländern.",
             "tree": [("Path", "SEA Manager 2017 → Head of Marketing 2021, drei Beförderungen"),
                      ("Team", "sechs Personen – SEA, SEO, Social Media, Influencer, klassisches Marketing, Grafik"),
                      ("Result", "17 Shops in 12 Sprachen; Mediabudget 6.000 → 240.000 € im Monat bei einer KUR von 25 %")]},
            {"when": "10/2014 – 04/2017", "title": "Online Marketing Manager", "org": "YOUniversal Media Srl", "place": "Rom",
             "tree": [("Scope", "Kunden- und In-House-Accounts für DE, FR, IT, SE, UK und US – Search, Social, Native, Retargeting")]},
            {"when": "2010 – 2014", "title": "Marketing, Marktforschung, Export", "org": "Verschiedene Unternehmen", "place": "Rom",
             "tree": [("Scope", "Exportförderung, Brand Protection, Competitive Intelligence, Web Marketing")]},
        ],
        "groups": [
            ("Bei E+SERVICE+CHECK", [
                ("Anruf- und Anfragen-Pipeline", "Über eine halbe Million Anrufe, zwei Telefonanlagen, fünf Webformulare – verknüpft mit Odoo-Stammdaten und Google-Ads-Attribution.", "Python · BigQuery · Data Studio", []),
                ("PRUEF+CHECK", "Regelbasierte Validierung von Prüflisten statt manueller Excel-Kontrolle. Von der Anforderung bis zum Go-live: fünf Tage.", "Streamlit · Azure", []),
                ("Dokumentenextraktion", "Rund 14.000 unstrukturierte Lieferantendokumente als strukturierte Datensätze für den ERP-Import.", "Python · Claude API", []),
                ("Kundenportal", "Umzug in einen eigenen Azure-Tenant mit getrennter Produktion und Staging. Laufende Cloud-Kosten: ein Bruchteil von vorher.", "Azure", []),
            ]),
            ("Abschlussprojekte der Weiterbildungen", [
                ("Rakuten-Produktklassifikation", "Rund 85.000 E-Commerce-Produkte, klassifiziert aus Text und Bild.", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                ("Rakuten-Klassifikation · MLOps", "Dasselbe Modell als produktive Pipeline: Training, Tracking, Bereitstellung und Monitoring.", STACK_MLOPS, [("GitHub", REPO_MLOPS), ("Demo", DEMO_MLOPS)]),
            ]),
        ],
        "approach": [
            "Jede Zahl auf dieser Seite ist auf Nachfrage belegbar. Wachstum zählt nur, wenn die Effizienz mithält.",
            "Wer die Systeme darunter kennt, steuert Agenturen besser. Und braucht weniger davon.",
            "KI gehört zum Werkzeugkasten – für Code, Text und Grafik. Nichts geht ungeprüft raus.",
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora in Partnerschaft mit der Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Fachkraft für agiles Projektmanagement (IHK)[[ihk]]", "mit Auszeichnung"),
            ("2018", "Introduction to Artificial Intelligence[[edx]]", "Microsoft auf edX"),
            ("2010", "Bachelor in Wirtschaftswissenschaften", "Università degli Studi di Trento"),
            ("Sprachen", "Deutsch (Muttersprache) · Englisch C2 · Italienisch C2 · Spanisch B1 · Französisch A2", ""),
        ],
        "offline": ("Leipzig.", "Davor: Rom, Trient, Jinotega (Nicaragua), Orem (Utah)."),
        "notes": {"issued": "ausgestellt am", "completed": "abgeschlossen am", "verify": "Nachweis prüfen", "course": "Kursseite", "back": "Zurück zum Text"},
        "imprint": "Impressum", "privacy": "Datenschutz",
        "jobtitle": "Leiter Marketing",
    },
}

SOURCE_NOTE = f"""<!--
  Hallo · Hi · Ciao – view-source counts as root access, too.

  peterstieg.com
  ├── no tracking
  ├── no cookies
  └── no framework

  >_ {MOTTO}
-->"""

# Runs before the stylesheet: marks JS as available and applies a stored theme without a flash.
THEME_BOOT = ("<script>(function(){document.documentElement.classList.add('js');"
              "try{var t=localStorage.getItem('theme');"
              "if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}})()</script>")

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


def sid(c, key):
    return c.get("ids", {}).get(key, key)


def note_title(c, note):
    """A footnote's title in the page language – NOTES titles are a string or one per language."""
    return note["title"][c["lang"]] if isinstance(note["title"], dict) else note["title"]


def num(key):
    """Chapter number of a section, '01'–'04': its own if it opens a chapter, else that of the chapter it belongs to."""
    for i, (first, rest) in enumerate(CHAPTERS.items(), 1):
        if key == first or key in rest:
            return f"{i:02d}"
    return ""


def t(c, text):
    """Escape, draw arrows, set *words* in italics (words cited as words, as in a dictionary)."""
    html = e(text).replace("→", f'<span class="arr" role="img" aria-label="{e(c["arrow"])}">{ARROW_SVG}</span>')
    lang = ' lang="en"' if c["lang"] != "en" else ""
    return re.sub(r"\*([^*]+)\*", rf"<i{lang}>\1</i>", html)


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


def theme_switch(c):
    group, light, dark = c["theme"]
    return (f'<span class="themes" role="group" aria-label="{e(group)}">'
            f'<button type="button" data-theme-set="light" aria-pressed="false" aria-label="{e(light)}" title="{e(light)}">{SUN_SVG}</button>'
            f'<button type="button" data-theme-set="dark" aria-pressed="false" aria-label="{e(dark)}" title="{e(dark)}">{MOON_SVG}</button>'
            f'</span>')


def topbar(c, sections=True, langs=True):
    r = c["root"]
    keys = {sid(c, k): k for k in CHAPTERS}          # localized id → section key, for the number
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


def section(c, key, title_html, body, cls="body"):
    i = sid(c, key)
    ghost = "" if key in CHAPTERS else " ghost"      # the rest of a chapter repeats its number invisibly: titles line up
    no = f'<span class="no{ghost}" aria-hidden="true">{num(key)}</span> ' if num(key) else ""
    return f"""<section class="sec" id="{i}" aria-labelledby="h-{i}">
<h2 id="h-{i}">{no}{title_html}</h2>
<div class="{cls}">
{body}</div>
</section>
"""


def tree(c, rows):
    lang = ' lang="en"' if c["lang"] != "en" else ""
    items = "".join(f'<li><span class="k"{lang}>{e(k)}</span> {t(c, v)}</li>' for k, v in rows)
    return f'<ul class="tree">{items}</ul>'


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

    out = [head(c, TITLE, c["desc"], URL + slug), jsonld(c), "</head>\n<body>\n", topbar(c)]
    out.append(f'<a class="to-top" href="#top" aria-label="{e(c["to_top"])}" title="{e(c["to_top"])}">{UP_SVG}</a>\n')
    out.append('<div class="minimap" aria-hidden="true"></div>\n<main id="main">\n<div class="wrap">\n')

    # hero – same order as the LinkedIn banner
    out.append(f"""<section class="hero" id="top">
<h1>{NAME}</h1>
<p class="tagline" lang="en">{TAGLINE.replace("Performance Marketing", "Performance&nbsp;Marketing").replace("Data Science", "Data&nbsp;Science")}</p>
<p class="claim" lang="en">{CLAIM}</p>
<p class="prompt" lang="en"><span class="caret" aria-hidden="true">&gt;_</span><span class="cmd" aria-hidden="true">{MOTTO}</span><span class="sr-only">{MOTTO}</span><span class="cursor" aria-hidden="true"></span></p>
</section>
""")

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

    # P⁴ – P as in Peter
    p4 = []
    for i, (p, txt) in enumerate(zip(P4, c["fields"])):
        tail = f' <strong lang="en">{e(P4_TAIL[i])}</strong>' if i in P4_TAIL else ""
        p4.append(f'<div><h3{en_attr}>{e(p)}</h3><p>{e(txt)}{tail}</p></div>\n')
    out.append(section(c, "fields", 'P<sup>4</sup>',
                       f'<p class="intro">{e(c["p4_intro"])}</p>\n<div class="fields">\n{"".join(p4)}</div>\n'))

    # experience – each role as a #JobAlert-style tree
    roles = []
    for ro in c["roles"]:
        place = f'&nbsp;<span class="place">· {e(ro["place"])}</span>' if ro.get("place") else ""
        ctx = f'<p class="ctx">{e(ro["ctx"])}</p>' if ro.get("ctx") else ""
        org = f'<a href="{ro["url"]}">{e(ro["org"])}</a>' if ro.get("url") else e(ro["org"])
        roles.append(f"""<li class="role">
<p class="when">{e(ro['when'])}</p>
<div>
<h3>{e(ro['title'])}</h3>
<p class="org">{org}{place}</p>
{ctx}{tree(c, ro['tree'])}
</div>
</li>
""")
    out.append(section(c, "experience", e(s["experience"]), f'<ol class="roles" reversed>\n{"".join(roles)}</ol>\n'))

    # education – certificates carry footnotes
    fa = []
    for k, v, sub in c["facts"]:
        subtxt = f'<br><span class="muted">{e(sub)}</span>' if sub else ""
        val = re.sub(r"\[\[(\w+)\]\]", fn, e(v))
        fa.append(f"<div><dt>{e(k)}</dt><dd>{val}{subtxt}</dd></div>\n")
    out.append(section(c, "education", e(s["education"]), f'<dl class="facts">\n{"".join(fa)}</dl>\n'))

    # projects
    groups = []
    for gt, items in c["groups"]:
        lis = []
        for name, text, stack, links in items:
            ln = "".join(f' · <a href="{url}">{e(label)}</a>' for label, url in links)
            lis.append(f'<li><h4>{e(name)}</h4><p>{e(text)}</p><p class="stack">{e(stack)}{ln}</p></li>\n')
        groups.append(f'<div class="group"><h3>{e(gt)}</h3>\n<ul class="projects">\n{"".join(lis)}</ul></div>\n')
    out.append(section(c, "projects", e(s["projects"]),
                       f'<p class="intro"><strong lang="en">{e(PROJECTS_LEAD)}</strong></p>\n' + "".join(groups)))

    # approach – three of a kind: X, not Y
    pr = "".join(f'<li><p><strong lang="en">{e(a)}</strong> {e(b)}</p></li>\n' for a, b in zip(SLOGANS, c["approach"]))
    out.append(section(c, "approach", e(s["approach"]), f'<ul class="principles">\n{pr}</ul>\n'))

    # contact – a nod to the 2016 claim: Work online | Live offline
    here, before = c["offline"]
    contact = f"""<p class="hello">Hallo · Hi · Ciao</p>
<dl class="reach">
<div><dt lang="en">Online</dt><dd><a class="mail" href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{LINKEDIN}" rel="me">LinkedIn</a> · <a href="{GITHUB}" rel="me">GitHub</a></dd></div>
<div><dt lang="en">Offline</dt><dd>{e(here)} <span class="muted">{e(before)}</span></dd></div>
</dl>
"""
    out.append(section(c, "contact", e(s["contact"]), contact))

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

    out.append("</div>\n</main>\n")
    out.append(footer(c))
    out.append(f'<script src="{c["root"]}assets/site.js" defer></script>\n</body>\n</html>\n')
    return "".join(out)


# ---------- legal pages (German) ----------

ADDRESS = """Peter Stieg<br>
Heinrich-Budde-Str. 8<br>
04157 Leipzig<br>
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
<p>Hosting-Anbieter: IONOS SE, Elgendorfer Str. 57, 56410 Montabaur. Mit ihm besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Speicherdauer der Logfiles richtet sich nach seinen Vorgaben.</p>
<h2>Helles und dunkles Design</h2>
<p>Ohne Ihr Zutun folgt die Website der Einstellung Ihres Geräts. Wählen Sie das Design über den Schalter oben selbst, speichert Ihr Browser diese Auswahl lokal (Local Storage), damit sie beim nächsten Besuch erhalten bleibt. Der Eintrag bleibt auf Ihrem Gerät und wird nicht an den Server übertragen. Rechtsgrundlage ist § 25 Abs. 2 Nr. 2 TDDDG. Sie können den Eintrag jederzeit über die Einstellungen Ihres Browsers löschen.</p>
<h2>Kontakt per E-Mail</h2>
<p>Wenn Sie eine E-Mail schreiben, werden Ihre Angaben verarbeitet, um die Anfrage zu beantworten (Art. 6 Abs. 1 lit. b oder f DSGVO). Die Daten werden gelöscht, sobald sie dafür nicht mehr benötigt werden und keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>
<h2>Links zu anderen Plattformen</h2>
<p>Die Seite verlinkt auf LinkedIn, GitHub, die Kursseiten von Liora, die Nachweisseiten von DataScientest, thekey.career und edX, die Demos der Abschlussprojekte bei Streamlit sowie die Websites früherer und heutiger Arbeitgeber. Erst wenn Sie einem dieser Links folgen, verarbeiten die jeweiligen Anbieter Daten nach ihren eigenen Datenschutzbestimmungen.</p>
<h2>Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18) und Datenübertragbarkeit (Art. 20). Einer Verarbeitung auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO können Sie widersprechen (Art. 21). Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, etwa bei der zuständigen Behörde Ihres Bundeslandes.</p>
"""


def legal(title, body, path):
    c = dict(CONTENT["de"], root="")
    out = [head(c, f"{title} – {NAME}", f"{title} von peterstieg.com", URL + path, alternates=False),
           '<meta name="robots" content="noindex, follow">\n</head>\n<body>\n',
           topbar(c, sections=False, langs=False),
           f'<main id="main">\n<div class="wrap legal">\n<div class="body">\n{body}<p>peterstieg.com: <a href="index.html" hreflang="en">English</a> · <a href="de/index.html">Deutsch</a></p>\n</div>\n</div>\n</main>\n',
           footer(c), '<script src="assets/site.js" defer></script>\n</body>\n</html>\n']
    return "".join(out)


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


def nbsp(html):
    """Keep numbers and units together: 25 %, 240.000 €, 1,7 Mio. €."""
    return (html.replace(" %", " %").replace(" €", " €")
                .replace("Mio. ", "Mio. ").replace(" Mio.", " Mio."))


def dots(html):
    """A middle dot never starts a line: it sticks to the word before it (body only, the source comment stays readable)."""
    head_part, sep, body = html.partition("<body>")
    return head_part + sep + body.replace(" · ", "&nbsp;· ")


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


if __name__ == "__main__":
    build()
