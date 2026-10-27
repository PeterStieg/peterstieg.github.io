# >_ P/S lockup · "Ein Takt"

Decided 25.10.2026. The locked PS monogram (23.10.2026, one-bar step) next to the site's prompt `>_`.

## Files

| File | Use |
|---|---|
| `out/lockup.svg` | inline on peterstieg.com – fills from `--accent` and `--ink`, so it follows light and dark |
| `out/lockup-light.svg`, `out/lockup-dark.svg` | fixed colours: #7A1A2C + #1A1C1E, #C98593 + #F5F4F2 |
| `out/lockup-mono.svg` | one colour, `currentColor` |
| `out/lockup-light.png`, `out/lockup-dark.png` | 2400 px wide, transparent |
| `lockup_takt50.py` | regenerates every file from the font (`pip install fonttools brotli skia-pathops resvg-py`) |
| `animation/ps-morph.html` | the animation from `>_ PETER STIEG` to this lockup, open in a browser |

## Construction

Font units, Atkinson Hyperlegible Bold, UPM 1000.

| Distance | Units | Source |
|---|---|---|
| `>` to `_` | 50 | the font's own spacing |
| `_` to P | 50 | the same beat |
| P to S | 50 | the monogram's gap, square to the slash (68.66°) |

- Size: 1971 × 813 (2.42 : 1). The monogram part is identical to `PS-Monogram_final` (968 × 813).
- Prompt in accent, letters in ink. No other spacing, no other colours.

## Where

- **Lockup:** header and other wide surfaces.
- **Monogram alone:** favicon, avatar, CV.
- **Minimum:** 24 px tall. Below that the three gaps close up.
- **Clear space:** one stem (158 units) on every side, as for the monogram.
