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
from datetime import date
from html import escape as e
from pathlib import Path
import base64
import hashlib
import json
import posixpath
import re

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

NAME = "Peter Stieg"
TAGLINE = "Performance Marketing · Data Science"
CLAIM = "Marketing leadership with root access"
MOTTO = "sudo dream plan ship"
# separators, one meaning each: · lists equals, – pauses a sentence, // joins a name to what it stands for (as on
# LinkedIn), › walks a path through the site. No |: it breaks the reading flow and looks like l and I in many fonts.
TITLE = f"{NAME} // {TAGLINE}"
SUBPAGE = f"{NAME} › %s"                                # the title of every other page: the path to it

# code, label, name, the start page's address from the site root – its folder: the server answers with index.html
LANGS = [("en", "EN", "English", ""),
         ("de", "DE", "Deutsch", "de/")]
HOME = {code: home for code, _, _, home in LANGS}

# P as in Peter – English in every language, like M³ and F³.
P4 = ["Performance", "Pipelines", "Pixels", "People"]
# four chapters, like the parts of a slide deck: the first section of each is numbered and linked in the menu,
# the sections after it belong to it – P⁴ and Languages to Profile, Education to Experience
CHAPTERS = {"profile": ["skills", "languages"], "experience": ["education"], "projects": [], "contact": []}
# page order: profile, skills, languages, experience … – Sources close the page in no chapter: footnotes from all four lead there
SECTIONS = [k for first, rest in CHAPTERS.items() for k in (first, *rest)] + ["sources"]

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
        "desc": "Head of Marketing, based in Leipzig. Four leadership roles in e-commerce and B2B, teams of up to nine, up to €240k media budget a month.",
        "skip": "Skip to content",
        "nav": [("profile", "Profile"), ("experience", "Experience"), ("projects", "Projects"), ("contact", "Contact")],
        "sec": {"profile": "Profile", "languages": "Languages", "experience": "Experience", "projects": "Projects",
                "education": "Education", "contact": "Contact", "sources": "Sources"},
        "entry": {"hw": "mar·ke·tin·ker·er", "pos": "noun", "ety": "[*marketer* × *tinkerer*]",
                  "def": "A marketing leader who builds the tools behind the campaigns – and the teams that run them."},
        "profile": "Online marketing since 2010 – leadership roles at four companies, with marketing and design teams of up to nine people in e-commerce and B2B. Certified Data Scientist and MLOps Engineer.",
        "ledger_label": "Selected results",
        "ledger": [
            ("Leads > 2×", "inbound inquiries year over year", "e-service-check"),
            ("RoAS 7.6 → 7.8", "on an expanded €1.7m budget", "brandible"),
            ("Media budget €6k → €240k", "per month, at a RoAS of 4.0", "posterlounge"),
        ],
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, Pinterest, Outbrain, Taboola; Amazon, Otto, Cdiscount – "
            "product feeds in PHP and Python. Optimised for RoAS, ACoS and CPL.",
            "Data from phone systems, web forms and Odoo into BigQuery with Python and SQL; reports in Data Studio, "
            "Google Ads Scripts and Apps Script; internal web apps in Streamlit.",
            "Corporate identity from claim and logo to signage, workwear and vehicle decals; websites, employer branding, "
            "mockups and videos; print from business cards to catalogues.",
            "International marketing and design teams of up to nine, including career changers from retail and fine arts. "
            "Recruiting and in-house training in SEA, social media and data analysis.",
        ],
        "roles": [
            {"id": "e-service-check", "when": "since 11/2025", "title": "Head of Marketing", "org": "E+SERVICE+CHECK", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-certified electrical safety inspections (DGUV V3/V4), nationwide, 349 employees.",
             "tree": [("Team", "two – marketing and marketing assistance"),
                      ("Scope", "marketing, lead generation, design and automation, built from scratch – SEA, SEO, email marketing, events, employer branding"),
                      ("Result", "inbound inquiries more than doubled year over year; new corporate identity incl. groundwork for an EUIPO trademark application")]},
            {"id": "liora-mlops", "when": "05/2025 – 07/2025", "title": "MLOps Engineer training",
             "org": "Liora", "url": NOTES["mlops"]["course"], "with": "Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Scope", "containers, orchestration, tracking, APIs and monitoring – Docker, Airflow, MLflow, FastAPI, Grafana"),
                      ("Result", "certified MLOps Engineer")]},
            {"id": "rapidobject", "when": "03/2025 – 07/2025", "title": "Marketing & UX Design (part-time)", "org": "Rapidobject", "url": "https://www.rapidobject.com/en/", "place": "Leipzig",
             "tree": [("Scope", "UI concepts, usability tests and pricing logic in Python; support for the marketing automation migration from "
                                "ActiveCampaign to Salesforce; liaison and translation between management and London partner AMFG"),
                      ("Result", "Salesforce dashboards, built into the sales process")]},
            {"id": "liora-ds", "when": "02/2025 – 05/2025", "title": "Data Scientist training",
             "org": "Liora", "url": NOTES["ds"]["course"], "with": "Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Scope", "machine learning and deep learning with Python – scikit-learn, Keras, PyTorch, Google Cloud"),
                      ("Result", "certified Data Scientist")]},
            {"id": "brandible", "when": "11/2023 – 12/2024", "title": "Head of Marketing", "org": "Brandible by KSi International", "url": "https://www.brandible.de/", "place": "Dresden",
             "ctx": "B2B promotional products for Germany, Austria and Switzerland.",
             "tree": [("Team", "seven – three in marketing, four in graphic design"),
                      ("Scope", "SEO, performance marketing and lead generation for three online shops, one of them seasonal for Dresden Christstollen – €1.7m across Google Ads, Microsoft Advertising, Meta and LinkedIn; CRM, newsletters and marketing automation; "
                                "photo and video production – a customer testimonial with Hellinger 42[[h42]] and the organisation of a TV shoot for ProSieben’s Galileo[[galileo]]"),
                      ("Result", "RoAS 7.6 → 7.8 on an expanded budget; Microsoft Advertising +45% revenue at a RoAS of 9.9")]},
            {"id": "sportspar", "when": "07/2023 – 10/2023", "title": "Chief Operating Officer", "org": "SportSpar", "url": "https://www.sportspar.com/", "place": "Eilenburg",
             "ctx": "Off-price online outlet for branded sportswear from previous seasons.",
             "tree": [("Team", "nine – five in marketing, four in design"),
                      ("Scope", "e-commerce operations for seven shops (DE, FR, IT, NL, ES, PL and .com) – email automation, Facebook, Instagram, WhatsApp, Telegram and affiliate marketing")]},
            {"id": "posterlounge", "when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Online shops for wall art, art prints and frames in more than 15 European countries.",
             "tree": [("Team", "six – SEA, SEO, social, influencer, offline marketing, design"),
                      ("Scope", "SEA, SEO, marketplaces, social media, creator relations and print partnerships; "
                                "cross-channel reporting with Google Ads Scripts and Apps Script"),
                      ("Result", "17 shops in 12 languages; media budget €6k → €240k a month at a RoAS of 4.0")],
             "path": ("Three promotions", [("09/2021", "Head of Marketing"), ("10/2020", "Senior Marketing Manager"),
                                             ("11/2018", "Online Marketing Manager"), ("10/2017", "SEO Manager Italy")],
                      "Started early: freelance SEO until the move to Germany · 07/2017 – 09/2017")},
            {"id": "immobiliare", "when": "05/2017 – 06/2017", "title": "Online Marketing Manager", "org": "Immobiliare.it", "url": "https://www.immobiliare.it/en/", "place": "Rome",
             "tree": [("Scope", "Google Ads and Microsoft Advertising; international marketing for portals such as LuxuryEstate")]},
            {"id": "youniversal", "when": "10/2014 – 04/2017", "title": "Online Marketing Manager", "org": "YOUniversal Media", "url": "https://www.youniversal.com/", "place": "Rome",
             "tree": [("Scope", "client and in-house accounts for DE, FR, IT, SE, UK and US – search, social and native; lead generation, app install and retargeting campaigns")]},
            {"id": "freelance", "when": "2013 – 2020", "nodur": True, "title": "Freelance: websites, design, translation", "org": "Alongside employment",
             "tree": [("Scope", "WordPress websites incl. photography and copy in three languages; logos, catalogues and posters "
                                "in Adobe Creative Cloud; translations via TextMaster"),
                      ("Result", "websites for a music school and a kiteboarding school in Rome")]},
            {"id": "rome-2010-2014", "when": "10/2010 – 09/2014", "title": "Marketing, market research, export", "org": "Six companies", "place": "Rome",
             "tree": [("Scope", "web design, online marketing, lead generation; export promotion and brand protection; "
                                "competitive intelligence, OSINT, primary and secondary research")],
             "positions": ("Six positions", [
                 ("09/2014", "Business Development Specialist", "3D2B", "http://www.3d2b.com/"),
                 ("04/2014 – 08/2014", "Marketing Consultant", "SBS systems for business solutions", "https://it.sbsbusiness.eu/"),
                 ("06/2013 – 05/2014", "Competitive intelligence", "Inner Valor", "https://innervalor.com/"),
                 ("06/2013 – 12/2013", "Marketing & export DACH", "Fontebona", "http://www.fontebona.com/"),
                 ("04/2012 – 05/2013", "Market research", "Proactive Worldwide, European subsidiary", "https://www.proactiveworldwide.com/"),
                 ("10/2010 – 09/2011", "Web Marketing Manager", "PaesiOnLine", "https://www.paesionline.it/"),
             ])},
        ],
        "groups": [
            ("At E+SERVICE+CHECK", [
                ("Customer portal", "Moved to a company-owned Azure tenant with separate production and staging. Running cloud costs: a fraction of before.", "Azure", []),
                ("Call and inquiry pipeline", "More than half a million calls, two phone systems, 15 web forms on 13 websites – joined with Odoo master data.", "Python · BigQuery · Data Studio", []),
                ("PRUEF+CHECK", "Rule-based validation of inspection checklists instead of manual Excel checks. From requirement to go-live: five days.", "Streamlit · Azure", []),
                ("Document extraction", "Around 14,000 unstructured supplier documents turned into structured records for ERP import.", "Python · Claude API", []),
            ]),
            ("Certification capstones", [
                ("Rakuten product classification", "Around 85,000 e-commerce products classified from text and images.", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                ("Rakuten classification · MLOps", "A text classifier for the same products as a production pipeline: training, tracking, serving and monitoring.", STACK_MLOPS, [("GitHub", REPO_MLOPS), ("Demo", DEMO_MLOPS)]),
            ]),
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora (formerly DataScientest) in partnership with Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Agile project management specialist[[ihk]]", "IHK"),
            ("2018", "Introduction to Artificial Intelligence[[edx]]", "Microsoft on edX"),
            ("2010", "Bachelor’s degree in economics", "Università degli Studi di Trento"),
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
        "aria_main": "Hauptnavigation", "aria_legal": "Rechtliches", "aria_lang": "Sprache",
        "theme": ("Darstellung", "Hell", "Dunkel"), "arrow": "auf", "to_top": "Nach oben", "new_tab": "öffnet in neuem Tab", "map": "Karte",
        "torch": {"tags": ["", "HTML · noch mal: build.py", "build.py · noch mal: aus"],
                  "keys": "Tastenkürzel", "close": "Schließen",
                  "rows": [["sudo", "Code-Ansicht: HTML · build.py · aus"], ["Esc", "Schließen"], [["?", "F1"], "Diese Liste zeigen"]]},
        "dur": ("Jahr", "Jahre", "Monat", "Monate"),
        "jump": {"label": "Abschnitte", "menu": "Alle Abschnitte", "up": "Nach oben: %s", "down": "Nach unten: %s"},
        "desc": "Marketingleiter aus Leipzig. Vier Führungsrollen in E-Commerce und B2B, Teams bis neun Personen, bis 240.000 € Mediabudget im Monat.",
        "skip": "Zum Inhalt springen",
        "nav": [("profil", "Profil"), ("werdegang", "Werdegang"), ("projekte", "Projekte"), ("kontakt", "Kontakt")],
        "sec": {"profile": "Profil", "languages": "Sprachen", "experience": "Werdegang", "projects": "Projekte",
                "education": "Ausbildung", "contact": "Kontakt", "sources": "Quellen"},
        "ids": {"profile": "profil", "skills": "kompetenzen", "languages": "sprachen", "experience": "werdegang",
                "projects": "projekte", "education": "ausbildung", "contact": "kontakt", "sources": "quellen"},
        "entry": {"hw": "Mar|ke|tin|ke|rer", "pos": "der; -s, -", "ety": "[engl. *marketer* × *tinkerer* ‚Tüftler‘]",
                  "def": "Marketingleiter, der die Werkzeuge hinter seinen Kampagnen baut – und die Teams dahinter."},
        "profile": "Online-Marketing seit 2010 – Führungsverantwortung in vier mittelständischen Unternehmen, für Teams aus Marketing und Design mit bis zu neun Personen in E-Commerce und B2B. Zertifiziert als Data Scientist und MLOps Engineer.",
        "ledger_label": "Ausgewählte Ergebnisse",
        "ledger": [
            ("Leads > 2×", "Anfragen im Jahresvergleich", "e-service-check"),
            ("KUR 13,2 → 12,8 %", "bei ausgebautem Budget von 1,7 Mio. €", "brandible"),
            ("Budget 6.000 → 240.000 €", "im Monat, bei einer KUR von 25 %", "posterlounge"),
        ],
        "fields": [
            "Google Ads, Microsoft Advertising, Meta, LinkedIn, Pinterest, Outbrain, Taboola; Amazon, Otto, Cdiscount – "
            "Produktfeeds in PHP und Python. Gesteuert über KUR, ACoS und CPL.",
            "Daten aus Telefonanlagen, Webformularen und Odoo in BigQuery, mit Python und SQL; Reports mit Data Studio, "
            "Google Ads Scripts und Apps Script; interne Web-Apps mit Streamlit.",
            "Corporate Identity von Claim und Logo bis Beschilderung, Fahrzeugbeklebung und Arbeitskleidung; "
            "Websites, Employer Branding und Videos; Print von Visitenkarte bis Katalog.",
            "Internationale Marketing- und Designteams bis neun Personen, mit Quereinsteigern aus Einzelhandel und bildender Kunst; "
            "Recruiting, Schulung in SEA, Social Media, Datenanalyse.",
        ],
        "roles": [
            {"id": "e-service-check", "when": "seit 11/2025", "title": "Leiter Marketing", "org": "E+SERVICE+CHECK", "url": "https://www.e-service-check.de/", "place": "Laucha",
             "ctx": "TÜV-zertifizierte Prüfungen der elektrischen Sicherheit (DGUV V3/V4), bundesweit, 349 Mitarbeitende.",
             "tree": [("Team", "zwei Personen – Marketing und Marketingassistenz"),
                      ("Scope", "Marketing, Leadgenerierung, Design und Automatisierung von Grund auf aufgebaut – SEA, SEO, E-Mail-Marketing, Events, Employer Branding"),
                      ("Result", "Anfragen im Jahresvergleich mehr als verdoppelt; neue Corporate Identity samt Grundlage der EUIPO-Markenanmeldung")]},
            {"id": "liora-mlops", "when": "05/2025 – 07/2025", "title": "Weiterbildung MLOps Engineer",
             "org": "Liora", "url": NOTES["mlops"]["course"], "with": "Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Scope", "Container, Orchestrierung, Tracking, APIs und Monitoring – Docker, Airflow, MLflow, FastAPI, Grafana"),
                      ("Result", "zertifizierter MLOps Engineer")]},
            {"id": "rapidobject", "when": "03/2025 – 07/2025", "title": "Marketing & UX-Design (Teilzeit)", "org": "Rapidobject", "url": "https://www.rapidobject.com/", "place": "Leipzig",
             "tree": [("Scope", "UI-Konzeption, Usability-Tests und Preislogik in Python; Begleitung der Migration der Marketing Automation von "
                                "ActiveCampaign zu Salesforce; Kommunikation und Übersetzung zwischen der Führung "
                                "von Rapidobject und dem Londoner Partner AMFG"),
                      ("Result", "Salesforce-Dashboards, eingebunden in den Vertriebsprozess")]},
            {"id": "liora-ds", "when": "02/2025 – 05/2025", "title": "Weiterbildung Data Scientist",
             "org": "Liora", "url": NOTES["ds"]["course"], "with": "Université Paris 1 Panthéon-Sorbonne", "place": "Remote",
             "tree": [("Scope", "Machine Learning und Deep Learning mit Python – scikit-learn, Keras, PyTorch, Google Cloud"),
                      ("Result", "zertifizierter Data Scientist")]},
            {"id": "brandible", "when": "11/2023 – 12/2024", "title": "Marketingleiter", "org": "Brandible by KSi International", "url": "https://www.brandible.de/", "place": "Dresden",
             "ctx": "B2B-Werbeartikel für Deutschland, Österreich und die Schweiz.",
             "tree": [("Team", "sieben Personen – drei im Marketing, vier in der Grafik"),
                      ("Scope", "SEO, Performance Marketing und Leadgenerierung für drei Online-Shops, darunter ein saisonaler für Dresdner Christstollen – 1,7 Mio. € über Google Ads, Microsoft Advertising, Meta und LinkedIn; CRM, Newsletter und Marketing Automation; "
                                "Foto- und Videoproduktion – ein Kundentestimonial mit Hellinger 42[[h42]] und die Organisation eines TV-Drehs für Galileo auf ProSieben[[galileo]]"),
                      ("Result", "KUR 13,2 → 12,8 % bei ausgebautem Budget; Microsoft Advertising +45 % Umsatz bei einer KUR von 10,1 %")]},
            {"id": "sportspar", "when": "07/2023 – 10/2023", "title": "Chief Operating Officer", "org": "SportSpar", "url": "https://www.sportspar.de/", "place": "Eilenburg",
             "ctx": "Online-Outlet für Markensportartikel der Vorsaison.",
             "tree": [("Team", "neun Personen – fünf im Marketing, vier im Design"),
                      ("Scope", "E-Commerce-Betrieb für sieben Shops (DE, FR, IT, NL, ES, PL und .com) – E-Mail-Automatisierung, Facebook, Instagram, WhatsApp, Telegram und Affiliate Marketing")]},
            {"id": "posterlounge", "when": "10/2017 – 06/2023", "title": "Head of Marketing", "org": "Posterlounge", "url": "https://posterlounge.com/shop", "place": "Leipzig",
             "ctx": "Online-Shops für Wandbilder, Kunstdrucke und Rahmen in über 15 europäischen Ländern.",
             "tree": [("Team", "sechs Personen – SEA, SEO, Social Media, Influencer, klassisches Marketing, Grafik"),
                      ("Scope", "SEA, SEO, Marktplätze, Social Media, Creator Relations und Print-Kooperationen; "
                                "kanalübergreifendes Reporting mit Google Ads Scripts und Apps Script"),
                      ("Result", "17 Shops in 12 Sprachen; Mediabudget 6.000 → 240.000 € im Monat bei einer KUR von 25 %")],
             "path": ("Drei Beförderungen", [("09/2021", "Head of Marketing"), ("10/2020", "Senior Marketing Manager"),
                                                 ("11/2018", "Online Marketing Manager"), ("10/2017", "SEO Manager Italien")],
                      "Vorzeitig gestartet: SEO, freiberuflich bis zum Umzug nach Deutschland · 07/2017 – 09/2017")},
            {"id": "immobiliare", "when": "05/2017 – 06/2017", "title": "Online Marketing Manager", "org": "Immobiliare.it", "url": "https://www.immobiliare.it/", "place": "Rom",
             "tree": [("Scope", "Google Ads und Microsoft Advertising; internationales Marketing für Portale wie LuxuryEstate")]},
            {"id": "youniversal", "when": "10/2014 – 04/2017", "title": "Online Marketing Manager", "org": "YOUniversal Media", "url": "https://www.youniversal.com/", "place": "Rom",
             "tree": [("Scope", "Kunden- und In-House-Accounts für DE, FR, IT, SE, UK und US – Search, Social und Native; Leadgenerierung, App-Install- und Retargeting-Kampagnen")]},
            {"id": "freiberuflich", "when": "2013 – 2020", "nodur": True, "title": "Freiberuflich: Websites, Design, Übersetzung", "org": "Neben der Anstellung",
             "tree": [("Scope", "WordPress-Websites inkl. Fotografie und Texten in drei Sprachen; Logos, Kataloge und Plakate "
                                "mit Adobe Creative Cloud; Übersetzungen über TextMaster"),
                      ("Result", "Websites für eine Musikschule und eine Kiteboarding-Schule in Rom")]},
            {"id": "rom-2010-2014", "when": "10/2010 – 09/2014", "title": "Marketing, Marktforschung, Export", "org": "Sechs Unternehmen", "place": "Rom",
             "tree": [("Scope", "Webdesign, Online-Marketing, Leadgenerierung; Exportförderung und Brand Protection; "
                                "Competitive Intelligence, OSINT, Primär- und Sekundärforschung")],
             "positions": ("Sechs Stationen", [
                 ("09/2014", "Business Development Specialist", "3D2B", "http://www.3d2b.com/"),
                 ("04/2014 – 08/2014", "Marketing Consultant", "SBS systems for business solutions", "https://it.sbsbusiness.eu/"),
                 ("06/2013 – 05/2014", "Competitive Intelligence", "Inner Valor", "https://innervalor.com/"),
                 ("06/2013 – 12/2013", "Marketing & Export DACH", "Fontebona", "http://www.fontebona.com/"),
                 ("04/2012 – 05/2013", "Marktforschung", "Proactive Worldwide, europäische Tochtergesellschaft", "https://www.proactiveworldwide.com/"),
                 ("10/2010 – 09/2011", "Web Marketing Manager", "PaesiOnLine", "https://www.paesionline.it/"),
             ])},
        ],
        "groups": [
            ("Bei E+SERVICE+CHECK", [
                ("Kundenportal", "Umzug in einen eigenen Azure-Tenant mit getrennter Produktion und Staging. Laufende Cloud-Kosten: ein Bruchteil von vorher.", "Azure", []),
                ("Anruf- und Anfragen-Pipeline", "Über eine halbe Million Anrufe, zwei Telefonanlagen, 15 Webformulare auf 13 Websites – verknüpft mit Odoo-Stammdaten.", "Python · BigQuery · Data Studio", []),
                ("PRUEF+CHECK", "Regelbasierte Validierung von Prüflisten statt manueller Excel-Kontrolle. Von der Anforderung bis zum Go-live: fünf Tage.", "Streamlit · Azure", []),
                ("Dokumentenextraktion", "Rund 14.000 unstrukturierte Lieferantendokumente als strukturierte Datensätze für den ERP-Import.", "Python · Claude API", []),
            ]),
            ("Abschlussprojekte der Weiterbildungen", [
                ("Rakuten-Produktklassifikation", "Rund 85.000 E-Commerce-Produkte, klassifiziert aus Text und Bild.", STACK_DS, [("GitHub", REPO_DS), ("Demo", DEMO_DS)]),
                ("Rakuten-Klassifikation · MLOps", "Ein Textklassifikator für dieselben Produkte als produktive Pipeline: Training, Tracking, Bereitstellung und Monitoring.", STACK_MLOPS, [("GitHub", REPO_MLOPS), ("Demo", DEMO_MLOPS)]),
            ]),
        ],
        "facts": [
            ("2025", "Data Scientist[[ds]] · MLOps Engineer[[mlops]]", "Liora (ehemals DataScientest) in Partnerschaft mit der Université Paris 1 Panthéon-Sorbonne"),
            ("2023", "Fachkraft für agiles Projektmanagement[[ihk]]", "IHK"),
            ("2018", "Introduction to Artificial Intelligence[[edx]]", "Microsoft auf edX"),
            ("2010", "Bachelor in Wirtschaftswissenschaften", "Università degli Studi di Trento"),
        ],
        "languages": ["Deutsch (Muttersprache)", "Englisch C2", "Italienisch C2", "Spanisch B1", "Französisch A2"],
        "reach": ("E-Mail", "Wohnort", "Leipzig"),
        "ask": "Fragen zu Performance, Pipelines, Pixels oder People:",
        "notes": {"issued": "ausgestellt am", "completed": "abgeschlossen am", "verify": "Nachweis prüfen", "course": "Kursseite", "back": "Zurück zum Text",
                  "published": "veröffentlicht am", "aired": "ausgestrahlt am", "watch": "Bei %s ansehen"},
        "imprint": "Impressum", "privacy": "Datenschutz", "legal_desc": "%s von peterstieg.com",
        "lost": ("Seite", "nicht gefunden.", "This page does not exist.", "Startseite"),
        "jobtitle": "Leiter Marketing",
    },
}

SOURCE_NOTE = f"""<!--
  Hallo · Hi · Ciao – view-source counts as root access, too.
  On the page: type or tap sudo · ? or F1 lists the keys.

  peterstieg.com
  └── no framework – build.py writes the HTML

  >_ {MOTTO}
-->"""

# Runs before the stylesheet: marks JS as available and applies a stored theme without a flash.
THEME_BOOT = ("<script>(function(){var r=document.documentElement;r.classList.add('js');"
              "try{var t=localStorage.getItem('theme');"
              "if(t==='light'||t==='dark'){r.setAttribute('data-theme',t);"
              "document.querySelector('meta[name=color-scheme]').content=t}}catch(e){}})()</script>")

# Chrome and Edge fetch a page of this site while the pointer rests on a link to it (prefetch, not prerender:
# the start page's typing and docking should run in view). Other browsers ignore the script.
SPECULATION = ('<script type="speculationrules">'
               '{"prefetch":[{"where":{"href_matches":"/*"},"eagerness":"moderate"}]}</script>')


def csp_hash(tag):
    """'sha256-…' of an inline script's content – the content security policy allows exactly these two."""
    body = re.search(r"<script[^>]*>(.*)</script>", tag, re.S)[1]
    return f"'sha256-{base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()}'"

# ?v= after the stylesheet and the script: the first 8 hex digits of the file's SHA-256. A changed file gets a new
# address – browsers may keep each version for a year (.htaccess) and never pair a new page with an old stylesheet.
VERSION = {name: hashlib.sha256((SITE / "assets" / name).read_bytes()).hexdigest()[:8] for name in ("site.css", "site.js")}

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


def sid(c, key):
    return c.get("ids", {}).get(key, key)


def slugify(text):
    """An id from a name: lower case, umlauts spelt out, everything else one hyphen ("PRUEF+CHECK" → "pruef-check")."""
    text = text.lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


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


def twins(c, o):
    """Block ids on start page c → the same block's id on start page o, where they differ: the sections, every role,
    every project. The language switch carries the map; site.js opens the other page at the block being read."""
    projects = lambda x: [slugify(name) for _, items in x["groups"] for name, *_ in items]
    assert len(c["roles"]) == len(o["roles"]) and len(projects(c)) == len(projects(o)), "EN and DE must list the same blocks"
    pairs = [(sid(c, k), sid(o, k)) for k in SECTIONS] + [(a["id"], b["id"]) for a, b in zip(c["roles"], o["roles"])]
    pairs += list(zip(projects(c), projects(o)))
    assert all(re.fullmatch(r"[a-z0-9-]+", x) for pair in pairs for x in pair)   # safe inside a quoted attribute as they are
    return {a: b for a, b in pairs if a != b}


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
    html = e(text).replace("→", f'<span class="arr">{ARROW_SVG}<span class="sr-only">{e(c["arrow"])}</span></span>')
    lang = ' lang="en"' if c["lang"] != "en" else ""
    return re.sub(r"\*([^*]+)\*", rf"<i{lang}>\1</i>", html)


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


def script(r):
    return f'<script src="{r}assets/site.js?v={VERSION["site.js"]}" defer></script>\n'


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


def theme_switch(c):
    group, light, dark = c["theme"]
    return (f'<span class="themes" role="group" aria-label="{e(group)}">'
            f'<button type="button" data-theme-set="light" aria-pressed="false" aria-label="{e(light)}" title="{e(light)}">{SUN_SVG}</button>'
            f'<button type="button" data-theme-set="dark" aria-pressed="false" aria-label="{e(dark)}" title="{e(dark)}">{MOON_SVG}</button>'
            f'</span>')


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


def jsonld(c):
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": NAME,
        "url": URL,
        "image": URL + "og-image.png",
        "jobTitle": c["jobtitle"],
        "worksFor": {"@type": "Organization", "name": c["roles"][0]["org"], "url": c["roles"][0]["url"]},   # the newest role
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


def torch_data(c):
    """data-torch on <main>: the torch's strings for site.js (sudo, ?), as JSON in an attribute – out of the page's text."""
    return f' data-torch="{e(json.dumps(c["torch"], ensure_ascii=False))}"'


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


def chapter_no(key):
    """The number before a section title: visible if the section opens a chapter, invisible (.ghost) for the rest,
    so the titles line up. Sources, in no chapter, hold the place with 00 – site.js marks no chapter there."""
    ghost = "" if key in CHAPTERS else " ghost"
    return f'<span class="no{ghost}" aria-hidden="true">{num(key) or "00"}</span> '


def section(c, key, title_html, body, cls="body"):
    i = sid(c, key)
    return f"""<section class="sec" id="{i}" aria-labelledby="h-{i}">
<h2 id="h-{i}">{chapter_no(key)}{title_html}</h2>
<div class="{cls}">
{body}</div>
</section>
"""


def tree(c, rows):
    lang = ' lang="en"' if c["lang"] != "en" else ""
    items = "".join(f'<li><span class="k"{lang}>{e(k)}:</span> {t(c, v)}</li>' for k, v in rows)
    return f'<ul class="tree">{items}</ul>' if rows else ""


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


def before(mmyyyy):
    """The month before: "11/2018" → "10/2018", "01/2019" → "12/2018"."""
    m, y = int(mmyyyy[:2]), int(mmyyyy[3:])
    return f"{m - 1:02d}/{y}" if m > 1 else f"12/{y - 1}"


def duration(c, n):
    """69 → "5 years 9 months", in full words: no yrs/mos to decode."""
    year, years, month, months_ = c["dur"]
    y, m = divmod(n, 12)
    return " ".join(([f"{y} {year if y == 1 else years}"] if y else []) + ([f"{m} {month if m == 1 else months_}"] if m else []))


def title_of(c, key):
    return 'P<sup>4</sup>' if key == "skills" else e(c["sec"][key])


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


def steps(c, label, rows, note=""):
    """A disclosure with the steps inside one timeline entry, newest first like the timeline itself: title (and company,
    where it changes – linked to its website where there is one), then dates and length. reversed: the list counts down,
    as the timeline does. rows: (title, company, dates, url) – company and url may be empty. note: one muted line
    under the list, for what happened before the first step without being one (Posterlounge: the freelance start)."""
    lis = "".join(f'<li>{e(title)}' + (f'&nbsp;<span class="muted">· {offsite(c, url, e(org)) if url else e(org)}</span>' if org else "")
                  + f'<br><span class="at">{span} · {duration(c, months(span))}</span></li>' for title, org, span, url in rows)
    note = f'<p class="note"><span>{e(note)}</span></p>\n' if note else ""
    return f'<details class="more">\n<summary>{e(label)}</summary>\n<ol class="tree" reversed>{lis}</ol>\n{note}</details>\n'


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
    when = e(ro["when"])
    if not ro.get("nodur"):                            # nodur: work alongside employment – a length would read as full-time years
        when += f'<br><span class="dur"{live}>{duration(c, months(ro["when"]))}</span>'
    more = ""
    if ro.get("path"):                                 # promotions, one per contract: its start; it ends the month before the next
        label, path, *note = ro["path"]
        ends = [re.findall(r"\d{2}/\d{4}", ro["when"])[-1]] + [before(start) for start, _ in path[:-1]]
        more += steps(c, label, [(title, "", f"{start} – {end}", "") for (start, title), end in zip(path, ends)], *note)
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

    out = [head(c, TITLE, c["desc"], URL + HOME[L]), jsonld(c), "</head>\n<body>\n", topbar(c)]
    out.append(f'<div class="minimap" aria-hidden="true"></div>\n<main id="main"{torch_data(c)}>\n<div class="wrap">\n')

    # hero – same order as the LinkedIn banner
    out.append(f"""<section class="hero" id="top">
<h1>{NAME}</h1>
<p class="tagline" lang="en">{TAGLINE.replace("Performance Marketing", "Performance&nbsp;Marketing").replace("Data Science", "Data&nbsp;Science")}</p>
<p class="claim" lang="en">{CLAIM}</p>
<p class="prompt" lang="en"><span class="caret" aria-hidden="true">&gt;_</span><span class="cmd" aria-hidden="true">{MOTTO.replace("sudo", '<span class="sudo">sudo</span>', 1)}</span><span class="sr-only">{MOTTO}</span><span class="cursor" aria-hidden="true"></span></p>
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
    # each result names its company; the name leads to the role under Experience
    # ↓: superscript and in accent like the footnote numbers – a link that stays on this page
    led = "".join(f'<div><dt>{t(c, a)}</dt><dd>{e(b)}<br><a href="#{k}">{e(COMPANIES[k])}'
                  f'<span class="jmp">{DOWN_SVG}</span></a></dd></div>\n' for a, b, k in c["ledger"])
    out.append(section(c, "profile", e(s["profile"]),
                       f'{entry}<p>{e(c["profile"])}</p>\n<dl class="ledger" aria-label="{e(c["ledger_label"])}">\n{led}</dl>\n'))

    # P⁴ – four fields, each a P
    p4 = "".join(f'<div><h3{en_attr}>{e(p)}</h3><p>{e(txt)}</p></div>\n' for p, txt in zip(P4, c["fields"]))
    out.append(section(c, "skills", title_of(c, "skills"), f'<div class="fields">\n{p4}</div>\n'))

    # languages – one per line, the level after the name
    langs = "".join(f"<li>{e(x)}</li>" for x in c["languages"])
    out.append(section(c, "languages", e(s["languages"]), f'<ul class="lines">{langs}</ul>\n'))

    # experience – each role as a #JobAlert-style tree
    roles = []
    for ro in c["roles"]:
        roles.append(f'<li class="role" id="{ro["id"]}">\n{role(c, ro)}</li>\n')   # the ledger and the language switch land here
    roles = re.sub(r"\[\[(\w+)\]\]", fn, "".join(roles))       # a role's tree may cite a source, as Education does
    out.append(section(c, "experience", e(s["experience"]), f'<ol class="roles" reversed>\n{roles}</ol>\n'))

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
            ln = "".join(f' · {offsite(c, url, e(label))}' for label, url in links)
            lis.append(f'<li id="{slugify(name)}"><h4>{e(name)}</h4><p>{e(text)}</p><p class="stack">{e(stack)}{ln}</p></li>\n')
        groups.append(f'<div class="group"><h3>{e(gt)}</h3>\n<ul class="projects">\n{"".join(lis)}</ul></div>\n')
    out.append(section(c, "projects", e(s["projects"]), "".join(groups)))

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

    out.append("</div>\n</main>\n")
    out.append(footer(c))
    out.append(jump(c))
    out.append(script(c["root"]) + "</body>\n</html>\n")
    return "".join(out)


# ---------- legal pages: German and English ----------
# One body line per element: the torch's second level finds each element's line by its place (torch_map).

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
<p class="muted">Stand: November 2026</p>
<h2>Verantwortlicher</h2>
<address>{ADDRESS}<br>E-Mail: <a href="mailto:{EMAIL}">{EMAIL}</a></address>
<h2>Kurz gesagt</h2>
<p>Diese Website setzt keine Cookies und lädt keine Inhalte von Drittanbietern: Schriften, Skripte und Grafiken liegen auf demselben Server wie die Seite selbst. Besuche werden statistisch ausgewertet – aus den Server-Logfiles, mit anonymisierter IP-Adresse. Ihr Browser speichert nur, was Sie selbst wählen: das helle oder dunkle Design und, im Haushaltsbuch, Sprache und Regeln (siehe unten).</p>
<h2>Hosting und Server-Logfiles</h2>
<p>Beim Aufruf der Website verarbeitet der Hosting-Anbieter automatisch Daten, die Ihr Browser übermittelt: IP-Adresse, Datum und Uhrzeit des Zugriffs, aufgerufene Seite, Referrer-URL sowie Browser und Betriebssystem. Das ist technisch erforderlich, um die Seite auszuliefern und ihre Sicherheit zu gewährleisten. Rechtsgrundlage ist das berechtigte Interesse nach Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Hosting-Anbieter: IONOS SE, Elgendorfer Str. 57, 56410 Montabaur. Mit ihm besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Speicherdauer der Logfiles richtet sich nach seinen Vorgaben.</p>
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
<p>This website sets no cookies and loads no content from third parties: fonts, scripts and graphics are stored on the same server as the page itself. Visits are evaluated statistically – from the server log files, with the IP address anonymised. Your browser stores only what you choose yourself: the light or dark design and, in the Haushaltsbuch, language and rules (see below).</p>
<h2>Hosting and server log files</h2>
<p>When you visit the website, the hosting provider automatically processes data your browser transmits: IP address, date and time of access, the page requested, referrer URL, browser and operating system. This is technically necessary to deliver the page and keep it secure. The legal basis is legitimate interest under Art. 6(1)(f) GDPR.</p>
<p>Hosting provider: IONOS SE, Elgendorfer Str. 57, 56410 Montabaur, Germany. A data processing agreement under Art. 28 GDPR is in place with it. How long the log files are kept is set by the provider.</p>
<h2>Audience measurement with IONOS WebAnalytics</h2>
<p>To evaluate the website statistically and improve it technically, IONOS WebAnalytics analyses the server log files: referrer URL, the page or file requested, browser and version, operating system, device type and time of access. The IP address is anonymised directly after transmission and used only to determine where the access came from. No cookies are set, no tracking pixels or additional scripts are loaded, and no data is passed on to third parties. The analysis is covered by the data processing agreement with IONOS. The legal basis is legitimate interest under Art. 6(1)(f) GDPR; you can object to the processing (Art. 21 GDPR).</p>
<h2>Light and dark design</h2>
<p>Unless you choose otherwise, the website follows your device's setting. If you choose the design yourself with the switch at the top, your browser stores this choice locally (Local Storage) so it is kept for your next visit. The entry stays on your device and is not sent to the server. The legal basis is § 25(2) no. 2 TDDDG. You can delete the entry at any time: with a second click on the chosen design, or in your browser's settings.</p>
<h2>Haushaltsbuch</h2>
<p>The Haushaltsbuch, a household ledger at peterstieg.com/haushaltsbuch/, reads the bank statements you select in your browser only: the files are neither uploaded nor passed on to third parties. Your browser stores locally (Local Storage) the language, if you switch it, and your rules and names, if you choose “Remember in this browser” – never transactions. The entries stay on your device. The legal basis is § 25(2) no. 2 TDDDG. You delete the rules by unticking “Remember in this browser”, all entries in your browser's settings.</p>
<h2>Contact by email</h2>
<p>If you write an email, the details you provide are processed to answer your inquiry (Art. 6(1)(b) or (f) GDPR). The data is deleted as soon as it is no longer needed for this purpose, unless statutory retention obligations apply.</p>
<h2>Links to other platforms</h2>
<p>The site links to LinkedIn, GitHub, a map on OpenStreetMap, the course pages of Liora, the verification pages of DataScientest, thekey.career and edX, the demos of the capstone projects on Streamlit, a customer video on YouTube, a TV episode on Joyn, and the websites of former and current employers. Only when you follow one of these links do the respective providers process data, under their own privacy policies.</p>
<h2>Your rights</h2>
<p>You have the right of access (Art. 15 GDPR), rectification (Art. 16), erasure (Art. 17), restriction of processing (Art. 18) and data portability (Art. 20). You can object to processing based on Art. 6(1)(f) GDPR (Art. 21). You can also lodge a complaint with a data protection supervisory authority, for example the one responsible where you live.</p>
"""

# German law asks for both pages; the German text is binding, the English one is a translation and says so.
# Per page and language: path, title, body – English in the root, German in de/, like the start pages.
# The footer links the pair in the page's language.
LEGAL = {
    "imprint": {"en": ("legal-notice.html", "Legal notice", IMPRINT_EN), "de": ("de/impressum.html", "Impressum", IMPRESSUM)},
    "privacy": {"en": ("privacy.html", "Privacy policy", PRIVACY_EN), "de": ("de/datenschutz.html", "Datenschutzerklärung", DATENSCHUTZ)},
}


def legal(key, L):
    """A legal page in one language. The language switch leads to the same page in the other language; the body's id
    (the file name) tells the torch which page it is on."""
    path, title, body = LEGAL[key][L]
    c = dict(CONTENT[L], path=path, root="../" * path.count("/"))   # the German pages sit in de/, like the German start page
    pair = {code: p[0] for code, p in LEGAL[key].items()}
    return "".join([
        head(c, SUBPAGE % title, c["legal_desc"] % title, URL + path, alternates=pair),
        '<meta name="robots" content="noindex, follow">\n</head>\n<body>\n',
        topbar(c, start=False, langs=pair),
        f'<main id="main"{torch_data(c)}>\n<div class="wrap legal">\n<div class="body" id="{page_id(path)}">\n{body}</div>\n</div>\n</main>\n',
        footer(c), script(c["root"]) + "</body>\n</html>\n"])


def not_found(c):
    """404 with a Google Ads insider joke: Dynamic Keyword Insertion, {KeyWord:Default}. One per language – a missing
    address under /de/ gets the German one (de/.htaccess) – each with a line in the other language and its start page."""
    word, rest, line, home_name = c["lost"]
    home = HOME[c["lang"]]
    other = next(x for x in LANGS if x[0] != c["lang"])           # code, label, name, home
    c = dict(c, root="/")
    return "".join([
        head(c, SUBPAGE % "404", f"{word} {rest}", f"{URL}{home}404.html", alternates=False, root="/"),
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


def nbsp(html):
    """Keep numbers and units together: 25 %, 240.000 €, 1,7 Mio. €."""
    return (html.replace(" %", " %").replace(" €", " €")
                .replace("Mio. ", "Mio. ").replace(" Mio.", " Mio."))


def dots(html):
    """A middle dot never starts a line: it sticks to the word before it (body only, the source comment stays readable)."""
    head_part, sep, body = html.partition("<body>")
    return head_part + sep + body.replace(" · ", "&nbsp;· ")


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


if __name__ == "__main__":
    build()
