# peterstieg.com

Hallo · Hi · Ciao – this is the source of [peterstieg.com](https://peterstieg.com).

One Python script turns the copy into static HTML. No framework, no tracking, no cookies.

```
peterstieg.github.io
├── src/build.py          all copy (EN · DE) and the HTML templates
├── site/                 generated – exactly what goes on the server
│   ├── index.html        English (default)
│   ├── de/index.html     German
│   ├── impressum.html · datenschutz.html
│   ├── 404.html · .htaccess
│   ├── assets/           site.css · site.js · fonts/
│   └── favicon.svg · apple-touch-icon.png · og-image.png · robots.txt · sitemap.xml
└── docs/                 the code explained, line by line
```

## Build

```
python3 src/build.py
```

Python 3, nothing to install. The script overwrites every HTML page in `site/` plus `sitemap.xml`, `robots.txt` and `.htaccess`. Change copy in `src/build.py`, never in `site/*.html` – the next build would overwrite it.

## Deploy

Manual for now: upload the **contents** of `site/` to the web root, keeping the folder structure. Afterwards, refresh the link preview with LinkedIn's Post Inspector.

## Learn the code

[`docs/`](docs/README.md) walks through every file, block by block:

1. [build.py – from content to HTML](docs/01-build.md)
2. [The HTML – what the browser receives](docs/02-html.md)
3. [site.css – look and layout](docs/03-css.md)
4. [site.js – behaviour](docs/04-js.md)

Why things are the way they are: [docs/decisions.md](docs/decisions.md).

## Roadmap

Open features live in [Issues](https://github.com/PeterStieg/peterstieg.github.io/issues).

---

Copy and code © Peter Stieg · Font: Atkinson Hyperlegible, SIL Open Font License (`site/assets/fonts/OFL.txt`)

`>_ sudo dream plan ship`
