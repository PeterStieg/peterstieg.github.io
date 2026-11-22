# peterstieg.com

Hallo · Hi · Ciao – this is the source of [peterstieg.com](https://peterstieg.com).

One Python script turns the copy into static HTML. No framework, no cookies – analytics from the server logs.

```
peterstieg.github.io
├── src/build.py          all copy (EN · DE) and the HTML templates
├── src/lockup/           the logo >_ P/S: generator, SVG files, the design's animation
├── src/monogram/         the PS monogram: generator, SVG files, the link preview's source
├── site/                 generated – exactly what goes on the server
│   ├── index.html        English (default)
│   ├── legal-notice.html · privacy.html      legal pages, English
│   ├── de/               German: index.html · impressum.html · datenschutz.html (binding) · 404.html · .htaccess
│   ├── 404.html · .htaccess
│   ├── assets/           site.css · site.js · torch.json · fonts/
│   ├── favicon.ico · favicon.svg · apple-touch-icon.png · icon-192/512.png · site.webmanifest
│   └── og-image.png · robots.txt · sitemap.xml
├── docs/                 the code explained, line by line
├── forward/              forward.css · forward.js · fonts/ – the terminal scene on peterstieg.github.io
└── index.html · 404.html · _config.yml   forward peterstieg.github.io to peterstieg.com
```

## Build

```
python3 src/build.py
```

Python 3, nothing to install. The script overwrites every HTML page in `site/` plus `sitemap.xml`, `robots.txt`, the two `.htaccess` files and `assets/torch.json`. Change copy in `src/build.py`, never in `site/*.html` – the next build would overwrite it. `site.css` and `site.js` are edited by hand; build after editing them too – the pages link them with a fingerprint of their content (`?v=`). `.htaccess` carries the hashes of the two inline scripts for the content security policy, so it changes with them.

## Deploy

Manual for now: upload the **contents** of `site/` to the web root at IONOS, keeping the folder structure – including the two hidden `.htaccess` files. `/haushaltsbuch/` on the server is not built from this repo: replacing files leaves it in place. `/impressum.html` and `/datenschutz.html` in the web root are left over from before November 2026 – `.htaccess` forwards both addresses to `de/`, the files can go. Afterwards, refresh the link preview with LinkedIn's Post Inspector. The content security policy is report-only: while the browser console on the live site shows violations, it stays so; once it shows none, the header in `HTACCESS` (`src/build.py`) becomes `Content-Security-Policy` and the policy blocks.

`peterstieg.github.io` is not a second copy: GitHub Pages serves only the forward page from the repo root – `index.html`, `404.html` and `forward/`. A two-second terminal scene (`mv -v peterstieg.github.io peterstieg.com`), then every path lands on peterstieg.com. `_config.yml` keeps `site/`, `src/` and `docs/` out of Pages. Changes go live on merge to `master`, no upload needed.

## Learn the code

[`docs/`](docs/README.md) walks through every file, block by block:

1. [build.py – from content to HTML](docs/01-build.md)
2. [The HTML – what the browser receives](docs/02-html.md)
3. [site.css – look and layout](docs/03-css.md)
4. [site.js – behaviour](docs/04-js.md)
5. [The forward page – peterstieg.github.io](docs/05-forward.md)

Why things are the way they are: [docs/decisions.md](docs/decisions.md).

## Roadmap

Open features live in [Issues](https://github.com/PeterStieg/peterstieg.github.io/issues).

---

Copy and code © Peter Stieg · Font: Atkinson Hyperlegible, SIL Open Font License (`site/assets/fonts/OFL.txt`)

`>_ sudo dream plan ship`
