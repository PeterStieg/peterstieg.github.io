"""Lockup ">_ P/S", "Ein Takt": the PS monogram (locked 23.10.2026) next to the site's prompt.

Every number comes from Atkinson Hyperlegible Bold (the woff2 that peterstieg.com serves):
  > to _   50   the font's own distance (> ink ends at 533, _ ink starts at 573 + 10)
  _ to P   50   same beat: the P's stem starts 50 after the _ ends
  P to S   50   the monogram's gap, measured square to the slash (68.66 deg, the font's "/")
The monogram itself is the locked "one-bar step": S one stem (158) under the bowl, gap 50
centred where it takes the same ink from P and S, S one bar (133) down the slash, the P's stem
extended to the line of the S's lower terminal (19.86 deg).

Run:  python3 lockup_takt50.py   ->  out/lockup*.svg, out/lockup-*.png
"""
import math, pathlib
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
import pathops

HERE = pathlib.Path(__file__).parent
FONT = TTFont(HERE / 'fonts' / 'atkinson-hyperlegible-latin-700-normal.woff2')
GS, CMAP = FONT.getGlyphSet(), FONT.getBestCmap()

def glyph(ch, dx=0.0, dy=0.0):
    p = pathops.Path()
    GS[CMAP[ord(ch)]].draw(TransformPen(p.getPen(), (1, 0, 0, 1, dx, dy)))
    return p

def poly(points):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo(points[0])
    for q in points[1:]: pen.lineTo(q)
    pen.closePath(); return p

op = lambda a, b, o: pathops.op(a, b, o)
U, D = pathops.PathOp.UNION, pathops.PathOp.DIFFERENCE

# ---- measured --------------------------------------------------------------------------
SL = math.atan2(668, 276 - 15)                       # Atkinson's "/"
SIN, COS = math.sin(SL), math.cos(SL)
STEM, BAR = 202 - 44, 668 - 535                      # P stem 158, P top bar 133
GAP_C, GAP_H = 350.0, 25.0                           # equal ink from P and S (see ps_monogram.py)
S_SLOT = 626 - STEM                                  # 468
STEP = (-BAR * 261 / 668, -BAR)                      # one bar down the slash
KT = (209 - 157) / (169 - 25)                        # S lower terminal, 19.86 deg
US_R = 573 + 420                                     # right end of "_"
P_X = US_R + 50 - 44                                 # the beat: 999

def halfplane(c, keep_right):
    """n.p > c (keep_right) or n.p < c, n = (sin, -cos): the side of a line at the slash angle"""
    R = 10000
    bx, by = c * SIN, -c * COS
    dx, dy = COS, SIN
    a, b = (bx - dx * R, by - dy * R), (bx + dx * R, by + dy * R)
    s = 1 if keep_right else -1
    return poly([a, b, (b[0] + SIN * R * s, b[1] - COS * R * s), (a[0] + SIN * R * s, a[1] - COS * R * s)])

def monogram():
    """In P's coordinates (P at x = 0)."""
    P = op(glyph('P'), halfplane(GAP_C - GAP_H, False), pathops.PathOp.INTERSECTION)
    fx0, fy0 = 25 + S_SLOT + STEP[0], 157 + STEP[1]
    fy = lambda x: fy0 + (x - fx0) * KT
    P = op(P, poly([(44, 1), (202, 1), (202, fy(202)), (44, fy(44))]), U)
    S = op(glyph('S', S_SLOT, 0), halfplane(GAP_C + GAP_H, True), pathops.PathOp.INTERSECTION)
    S = op(S, poly([(-5000, -5000), (5000, -5000), (5000, 5000), (-5000, 5000)]), pathops.PathOp.INTERSECTION)
    S_moved = pathops.Path(); S.draw(TransformPen(S_moved.getPen(), (1, 0, 0, 1, STEP[0], STEP[1])))
    return P, S_moved, (fy(44), fy(202))

def shifted(path, dx):
    out = pathops.Path(); path.draw(TransformPen(out.getPen(), (1, 0, 0, 1, dx, 0))); return out

def svg_d(path):
    pen = SVGPathPen(None, ntos=lambda v: ('%.2f' % v).rstrip('0').rstrip('.'))
    path.draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))  # font y-up -> SVG y-down
    return pen.getCommands()

def bounds(path):
    bp = BoundsPen(None); path.draw(bp); return bp.bounds

if __name__ == '__main__':
    P, S, (f0, f1) = monogram()
    mark = op(shifted(P, P_X), shifted(S, P_X), U)
    prompt = op(glyph('>'), glyph('_', 573), U)
    mb, pb = bounds(mark), bounds(prompt)
    x0, y0, x1, y1 = min(mb[0], pb[0]), min(mb[1], pb[1]), max(mb[2], pb[2]), max(mb[3], pb[3])
    W, H = x1 - x0, y1 - y0
    print('monogram %.1f x %.1f   foot %.1f .. %.1f' % (mb[2] - mb[0], mb[3] - mb[1], f0, f1))
    print('lockup   %.1f x %.1f   ratio %.3f' % (W, H, W / H))
    print('beats    > to _: %.1f   _ to P: %.1f' % (573 + 10 - 533, (P_X + 44) - US_R))
    vb = '%g %g %g %g' % (x0, -y1, W, H)
    out = HERE / 'out'; out.mkdir(exist_ok=True)
    pd, md = svg_d(prompt), svg_d(mark)
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" aria-label="Peter Stieg">'
    files = {
        # inline on the site: picks up --accent and --ink, so it follows light and dark
        'lockup.svg': f'{head}<path style="fill:var(--accent,#7A1A2C)" d="{pd}"/><path style="fill:var(--ink,#1A1C1E)" d="{md}"/></svg>\n',
        'lockup-light.svg': f'{head}<path fill="#7A1A2C" d="{pd}"/><path fill="#1A1C1E" d="{md}"/></svg>\n',
        'lockup-dark.svg': f'{head}<path fill="#C98593" d="{pd}"/><path fill="#F5F4F2" d="{md}"/></svg>\n',
        'lockup-mono.svg': f'{head}<path fill="currentColor" d="{pd} {md}"/></svg>\n',
    }
    for n, s in files.items(): (out / n).write_text(s)
    try:
        import resvg_py
        for n in ('lockup-light', 'lockup-dark'):
            png = resvg_py.svg_to_bytes(svg_string=files[n + '.svg'], width=2400)
            (out / (n + '.png')).write_bytes(bytes(png))
    except Exception as e:
        print('png skipped:', e)
    print('written', sorted(p.name for p in out.iterdir()))
