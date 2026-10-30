# Changelog

## v2 · 29.10.2026

Closes the near-miss between `_` and the P's foot.

- `>_` is raised as one unit by **8.6265** units (8.63). `lockup_takt50.py` measures it from the outlines: the P's lowest point, the left end of the foot at −119.3735, minus the `_`'s bottom edge at −128.
- New coordinates in `out/lockup.svg` (y down, baseline 0, font units):
  - `>`: x 40 to 533, y −518.63 to 3.37 (v1: −510 to 12)
  - `_`: x 583 to 993, y −8.63 to 119.37 (v1: 0 to 128). Its bottom edge now lies on the foot's lowest point (x 1043, y 119.37).
- Unchanged:
  - the size: viewBox `40 −668 1971.03 813`, 1971 × 813. The top stays at the P (−668), the bottom at the S (145).
  - the horizontal spacing: `>` to `_`, `_` to P and P to S are 50 each.
  - the monogram part: its path is byte for byte the same as in v1.
  - the colours.
- Animation: `>_` travels the 8.63 units in step 6, "Enter", between 6.85 and 7.45 s. It rises with the same easing and timing as the S stepping down and the foot growing, so the `_` and the foot meet at 7.45 s. The last frame matches the new lockup.
- Changed files: `lockup_takt50.py`, `out/*` (only the prompt path), `animation/ps-morph.html`, `README.md`.
