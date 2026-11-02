# Changelog

## Favicons v2 · 30.10.2026 – legible in dark browser themes

- **New favicon:** paper PS (#F7F6F3) on a bordeaux disc (#7A1A2C), based on `avatar/avatar-bordeaux.svg`. It replaces the bare bordeaux mark on transparent, which nearly disappeared on dark tab strips (1.2 : 1 on #35363A, 1.4 : 1 on #2B2A33).
- **16 and 32 px drawn by hand:** new grids in `source/favicons.py` (`FAVICONS_DISC`).
  - 16 px: the mark is 11 × 10 at columns 3 to 13, rows 3 to 12.
  - 32 px: the mark is 22 × 19 at columns 5 to 26, rows 7 to 25.
  - The disc edge is antialiased by coverage into the alpha channel.
- **favicon.ico:** contains those two images plus a 48 px image. The 48 px is rendered from the vector at 69 % of the disc, with the P's stem and top on whole pixels.
- **favicon.svg:** the disc as a vector, one version. The `prefers-color-scheme` switch is gone.
- **Head:** the pages link only `favicon.ico` (`sizes="16x16 32x32 48x48"`), plus the touch icon and the manifest. The SVG link is dropped, so browsers use the hand-hinted pixels.
- **apple-touch-icon.png (180), icon-192.png and icon-512.png:** full-bleed bordeaux with the paper PS inside the 80 % safe zone. In v1 the PS crossed the safe zone, so a round mask would have cut the P's corner.
- **site.webmanifest:** unchanged. `theme_color` and `background_color` stay #F7F6F3.
- **Removed:** `favicon-16-hinted.svg` and `favicon-32-hinted.svg`, the v1 pixel SVGs.
- **Source:**
  - `ps_monogram.py` gains `disc_png`, `disc_svg`, `disc_auto_png`, `tile_svg`, `export_favicons` and the `--favicons` option. `export_final` now writes this set into `final/favicon/`.
  - Every other file the generator writes (masters, avatars, lockups, spec drawings, exploration) is byte for byte the same as before.
  - `favicon_preview.py` draws `preview/favicon-preview.png`.

## v1 · 23.10.2026

The monogram locked: P and S from Atkinson Hyperlegible Bold, slash, step and foot (see `README.md`).
