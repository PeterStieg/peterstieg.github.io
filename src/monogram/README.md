# PS monogram – final

Locked 23.10.2026 · Atkinson Hyperlegible Bold · peterstieg.com

## The mark

P and S from Atkinson Hyperlegible Bold, outlines read from the font file, never redrawn. All values in font units (1000 per em, cap height 668), measured by the script.

1. **Slash** – the S slides one stem (158) under the P's bowl. A 50-unit gap at 68.7°, the angle of Atkinson's `/`, divides them and takes the same ink from both (22 562 u² each). 50 is the space the font itself leaves between P and S.
2. **Step** – the S slides 143 down the slash: one bar (133) lower, so its cap line sits on the underside of the P's top bar (535). The gap stays 50.
3. **Line** – the P's stem descends to the line of the S's lower terminal: one straight cut at 19.9°, from −119 to −62. The prompt's `>` runs at 20.3°.
4. **Nothing else** – both letters keep their shape. 968 × 813 units, 1.19 : 1.

## Colours

| | Light | Dark |
|---|---|---|
| Mark | Ink `#1A1C1E` on `#F7F6F3` – 15.8 : 1 | Paper `#F5F4F2` on `#181A1C` – 15.9 : 1 |
| Accent | Bordeaux `#7A1A2C` – 9.7 : 1 | Rose `#C98593` – 6.0 : 1 |

One colour per use. No gradients, outlines or shadows.

## Clear space · size

- Clear space: one stem (158 units, 16 % of the mark's width) on every side.
- Minimum: 24 px tall on screen, 7 mm in print. Below that, the hand-hinted favicon.

## Where it goes

- Mark alone: favicon, avatar, document footers, profile images.
- With the wordmark: `lockup-light`, `lockup-dark`. The P stands at twice the cap height of `>_ PETER STIEG`, the mark is centred as a whole on the text's cap height, gap 0.9 em.
- The site header works as the wordmark alone.

## Don't

- Redraw, stretch, rotate or re-space the letters.
- Change the slash, the step or the foot.
- Put it on a filled square tile – a P and a lowered S on a square reads as an app icon (Photoshop).
- Lay the S flat or add depth – PlayStation.
- Put the `>_` inside the mark; it belongs to the wordmark.

## Files

| Folder | Content |
|---|---|
| `mark/` | `ps-monogram.svg` (`currentColor`), `-ink`, `-paper`, `-bordeaux`, `-bordeaux-dark`, transparent |
| `avatar/` | circle crops `light`, `dark`, `bordeaux` |
| `site/` (repository root) | `favicon.svg` (vector, follows light/dark), `favicon.ico` (16 and 32 px hand-hinted, 48 px), `apple-touch-icon.png`, `icon-192/512.png`, `site.webmanifest` |
| `lockup/` | mark and wordmark, `light` and `dark`, transparent |
| `spec/` | `construction.svg`, `clearspace.svg`, `parts.svg` (P, S, slash, foot and line as named elements) |
| `source/` | `ps_monogram.py`, `favicons.py` (the hinted pixels), Atkinson Hyperlegible TTF and OFL |

## On peterstieg.com

The favicon set lives in `site/`: `favicon.ico`, `favicon.svg`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `site.webmanifest`. `build.py` writes the four `<link>` lines into every page's `<head>` (with `../` on the German pages, `/` on the 404 page). The header logo `>_ P/S` in `src/lockup/` uses the same P and S.

In this repository: the SVGs and the generator. The PNG exports (mark, avatar, lockup) and the hinted favicon sources are not checked in – `ps_monogram.py` writes them.

## Regenerate

```
cd source
pip install fonttools skia-pathops resvg-py pillow
python3 ps_monogram.py          # writes out/final/ (and the exploration files in out/)
```

Fonts: Atkinson Hyperlegible, SIL Open Font License (`source/fonts/OFL.txt`).
