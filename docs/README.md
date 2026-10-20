# The code, line by line

Four chapters, one per file type, in the order the site comes to life: Python writes the HTML, the browser reads it, CSS styles it, JavaScript moves it.

| Chapter | File | What you learn |
|---|---|---|
| [1 · build.py](01-build.md) | `src/build.py` | how copy, templates and footnotes become static pages |
| [2 · HTML](02-html.md) | `site/index.html` and friends | what the browser, screen readers, search engines and LinkedIn read |
| [3 · CSS](03-css.md) | `site/assets/site.css` | tokens, light/dark, grid, sticky header, drawn tree lines |
| [4 · JavaScript](04-js.md) | `site/assets/site.js` | theme switch, typing prompt, docking animation, minimap |

## How to read

- **One chapter per session.** Each ends with three small exercises – do them, they take minutes.
- **Keep the file open next to the chapter.** Code is quoted in file order; references use function and selector names, not line numbers, so they stay valid when the code changes.
- **Use the browser's DevTools** (F12): Elements for HTML and CSS, Console for JavaScript. Changes there are temporary – reload and they are gone, so experiment freely.
- **Change copy only in `src/build.py`**, then run `python3 src/build.py`. Edits in `site/*.html` are overwritten by the next build.

Why things are built this way: [decisions.md](decisions.md).
