"""
ps_monogram.py – PS monograms built from the real Atkinson Hyperlegible Bold outlines.

Every mark starts from the font's own P and S (read from the TTF, never redrawn) and
gets exactly one move:

    joined   shared stroke   The S slides left until the P's bowl and the S's shoulder
                             share a joint as tall as the P's bars (133 units).
    slash    one cut         The S slides one stem width under the bowl; a 50-unit gap
                             at the angle of Atkinson's own "/" (68.7°) divides the two.
                             The cut takes the same amount of ink from P and S.
    overlap  P in front      The S slides one stem width under the bowl and passes
                             behind the P with 50 units of clearance. The P stays whole.
    foot     one detail      The P's foot is cut at 19.9°, the angle of the S's
                             terminals and of Atkinson's ">". Spacing as the font sets it.

All numbers are font units (1000 per em, cap height 668). 50 units is the space
Atkinson Bold itself leaves between P and S.

Outputs (default ./out):
    svg/<mark>_{ink,paper,accent,currentcolor}.svg   the mark, transparent
    svg/<mark>_avatar_{light,dark,accent}.svg        circle-cropped avatar
    svg/lockup_<mark>_{light,dark}.svg               mark + ">_ PETER STIEG" (outlined)
    svg/lockup_wordmark_{light,dark}.svg             the control: wordmark alone
    svg/slash_foot_parts.svg                         slash and foot as named parts: P, S, slash, foot, line
    svg/slash_step_parts.svg                         the same for the stepped S (Pete's idea 1)
    favicon/<mark>.svg                               hand-hinted 16/32 px, light/dark aware
    favicon/<mark>-{16,32}.png, <mark>.ico           raster fallbacks (accent colour)
    favicon/<mark>-{16,32}-{light,dark}.svg          the same grids in one fixed colour
    favicon/<mark>-auto-{16,32}.png                  automatic downscale, for comparison
    favicon/<mark>-apple-touch-180.png               touch icon, Bordeaux on paper
    construction/<mark>.svg                          the move, measured on the font's own glyphs
    tried/<sketch>.svg                               what did not make it (notes in marks.json)
    marks.json                                       construction values
    final/                                           the locked mark (slash_step_bar), clean names:
      mark/     ps-monogram.svg (currentColor), -ink, -paper, -bordeaux, -bordeaux-dark (.svg, 2048 px .png)
      avatar/   avatar-light, -dark, -bordeaux (.svg, 1024 px .png)
      favicon/  favicon.svg (vector, light/dark), favicon.ico (16/32 hinted, 48), favicon-16/32-hinted.svg,
                apple-touch-icon.png, icon-192/512.png, site.webmanifest, head.html
      lockup/   lockup-light, lockup-dark (.svg, 2400 px .png), transparent
      spec/     construction.svg, clearspace.svg, parts.svg

Usage:
    pip install fonttools skia-pathops resvg-py pillow
    python3 ps_monogram.py [--font fonts/AtkinsonHyperlegible-Bold.ttf] [--out out]
"""
import argparse
import io
import json
import math
import os

import pathops
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- site tokens (site.css)
LIGHT = dict(ground='#F7F6F3', ink='#1A1C1E', accent='#7A1A2C', muted='#565B60', line='#DCDAD4')
DARK = dict(ground='#181A1C', ink='#F5F4F2', accent='#C98593', muted='#A3A8AD', line='#2F3337')

GAP = 50.0          # the space Atkinson Bold leaves between P and S (measured: 50.4)
BAR = 133.0         # the P's top bar (668 - 535); its bowl bar is 131
STEM = 158.0        # the P's stem (44 .. 202)


# ---------------------------------------------------------------- font access
class Font:
    def __init__(self, path):
        self.path = path
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt['head'].unitsPerEm
        self.cap = self.tt['OS/2'].sCapHeight
        self._gpos = self.tt['GPOS'].table if 'GPOS' in self.tt else None

    def name(self, ch):
        return self.cmap[ord(ch)]

    def adv(self, ch):
        return self.tt['hmtx'][self.name(ch)][0]

    def glyph(self, ch, dx=0.0, dy=0.0, s=1.0):
        p = pathops.Path()
        self.gs[self.name(ch)].draw(TransformPen(p.getPen(), (s, 0, 0, s, dx, dy)))
        return p

    def outline(self, ch):
        rec = RecordingPen()
        self.gs[self.name(ch)].draw(rec)
        return rec.value

    def kern(self, a, b):
        """Pair kerning from GPOS (formats 1 and 2), as a browser applies it."""
        if not self._gpos:
            return 0
        a, b = self.name(a), self.name(b)
        out = 0
        for lk in self._gpos.LookupList.Lookup:
            for st in lk.SubTable:
                t = lk.LookupType
                if t == 9:
                    t, st = st.ExtensionLookupType, st.ExtSubTable
                if t != 2:
                    continue
                if st.Format == 1:
                    cov = st.Coverage.glyphs
                    if a in cov:
                        for r in st.PairSet[cov.index(a)].PairValueRecord:
                            if r.SecondGlyph == b and r.Value1:
                                out += getattr(r.Value1, 'XAdvance', 0) or 0
                elif a in st.Coverage.glyphs:
                    c1 = st.ClassDef1.classDefs.get(a, 0)
                    c2 = st.ClassDef2.classDefs.get(b, 0)
                    v = st.Class1Record[c1].Class2Record[c2].Value1
                    if v:
                        out += getattr(v, 'XAdvance', 0) or 0
        return out


# ---------------------------------------------------------------- geometry helpers
def poly(pts):
    p = pathops.Path()
    pen = p.getPen()
    pen.moveTo(pts[0])
    for q in pts[1:]:
        pen.lineTo(q)
    pen.closePath()
    return p


_OPS = {'u': pathops.PathOp.UNION, 'd': pathops.PathOp.DIFFERENCE,
        'i': pathops.PathOp.INTERSECTION, 'x': pathops.PathOp.XOR}


def op(a, b, kind):
    return pathops.op(a, b, _OPS[kind])


def union(*ps):
    out = ps[0]
    for q in ps[1:]:
        out = op(out, q, 'u')
    return out


def empty(p):
    b = p.bounds
    return (b[2] - b[0]) < 1e-6 or (b[3] - b[1]) < 1e-6


def area(p):
    pen = AreaPen()
    p.draw(pen)
    return abs(pen.value)


def band(p0, angle, width, length=5000):
    a = math.radians(angle)
    ux, uy, nx, ny = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    x, y, h, L = p0[0], p0[1], width / 2, length
    return poly([(x - ux * L + nx * h, y - uy * L + ny * h), (x + ux * L + nx * h, y + uy * L + ny * h),
                 (x + ux * L - nx * h, y + uy * L - ny * h), (x - ux * L - nx * h, y - uy * L - ny * h)])


def side(p0, angle, which, size=8000):
    """Half-plane to the left (which=+1) or right (which=-1) of the directed line."""
    a = math.radians(angle)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy * which, ux * which
    x, y, L = p0[0], p0[1], size
    return poly([(x - ux * L, y - uy * L), (x + ux * L, y + uy * L),
                 (x + ux * L + nx * L, y + uy * L + ny * L), (x - ux * L + nx * L, y - uy * L + ny * L)])


def grow(p, w):
    """p plus a clearance ring of width w (round joins)."""
    q = pathops.Path()
    p.draw(q.getPen())
    q.stroke(2 * w, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    q.convertConicsToQuads()
    return union(p, q)


def bisect(f, lo, hi, n=48):
    """f(lo) and f(hi) have different signs; returns the root."""
    flo = f(lo)
    for _ in range(n):
        m = (lo + hi) / 2
        fm = f(m)
        if (fm > 0) == (flo > 0):
            lo, flo = m, fm
        else:
            hi = m
    return (lo + hi) / 2


def angle_of(seg):
    (x0, y0), (x1, y1) = seg
    return math.degrees(math.atan2(y1 - y0, x1 - x0))


# ---------------------------------------------------------------- measurements from the font
def measure(F):
    """Angles and distances read from the outlines, so nothing is typed in by eye."""
    S = F.outline('S')
    pts = {}
    # S terminals: the two straight segments of the S outline
    cur = None
    lines = []
    for verb, args in S:
        if verb == 'moveTo':
            cur = args[0]
        elif verb == 'lineTo':
            lines.append((cur, args[0]))
            cur = args[0]
        elif verb in ('qCurveTo', 'curveTo'):
            cur = args[-1]
    terminals = [l for l in lines if abs(l[1][0] - l[0][0]) > 100]   # the two long cuts
    t_angles = [angle_of(l) % 180 for l in terminals]
    sl = F.outline('/')
    spts = [a[0] for v, a in sl if v in ('moveTo', 'lineTo')]
    slash_angle = (angle_of((spts[0], spts[1])) + angle_of((spts[3], spts[2]))) / 2
    gt = F.outline('>')
    gpts = [a[0] for v, a in gt if v in ('moveTo', 'lineTo')]
    gt_angle = angle_of((gpts[1], gpts[2]))
    P = F.glyph('P')
    touch = bisect(lambda dx: 1 if not empty(op(P, F.glyph('S', dx=dx), 'i')) else -1, 300, 700)
    gap = F.adv('P') - touch
    pts.update(terminal_angle=sum(t_angles) / len(t_angles), terminal_angles=t_angles,
               slash_angle=slash_angle, prompt_angle=gt_angle, touch_dx=touch, font_gap=gap)
    return pts


# ---------------------------------------------------------------- the marks
def mark_set(F, M):
    """Starting point: P and S as the font sets them."""
    return dict(parts=[('P', F.glyph('P')), ('S', F.glyph('S', dx=F.adv('P')))],
                meta=dict(move='none', dx=F.adv('P')))


def mark_joined(F, M):
    P = F.glyph('P')

    def joint(dx):
        i = op(P, F.glyph('S', dx=dx), 'i')
        return 0 if empty(i) else i.bounds[3] - i.bounds[1]
    dx = bisect(lambda dx: joint(dx) - BAR, M['touch_dx'] - 80, M['touch_dx'] - 0.5)
    shape = union(P, F.glyph('S', dx=dx))
    return dict(parts=[('PS', shape)],
                meta=dict(move='shared stroke', dx=round(dx, 1), joint=BAR,
                          rule='S slides left until the joint between bowl and shoulder is as tall as the P\'s bars'))


def mark_slash(F, M, drop=0.0, foot=False, tuck=1):
    P = F.glyph('P')
    dx = F.adv('P') - tuck * STEM
    S = F.glyph('S', dx=dx, dy=-drop)
    ang = M['slash_angle']
    y0 = F.cap / 2

    def pieces(cx):
        b = band((cx, y0), ang, GAP)
        p = op(op(P, b, 'd'), side((cx, y0), ang, -1), 'd')
        s = op(op(S, b, 'd'), side((cx, y0), ang, +1), 'd')
        return p, s
    aP, aS = area(P), area(S)

    def balance(cx):
        p, s = pieces(cx)
        return (aP - area(p)) - (aS - area(s))
    cx = bisect(balance, 250, 750)
    p, s = pieces(cx)
    meta = dict(move='one cut', dx=round(dx, 1), drop=round(drop, 1), angle=round(ang, 2), gap=GAP, cut_x_at_half_cap=round(cx, 1),
                ink_taken_P=round(aP - area(p)), ink_taken_S=round(aS - area(s)),
                rule='S slides one stem width under the bowl; a 50-unit gap at the angle of "/" '
                     'divides them and takes equal ink from both')
    if foot:
        (ax, ay), (bx, by) = terminal_line(F, 'lower')
        a0 = (ax + dx, ay - drop)
        t_ang = math.degrees(math.atan2(by - ay, bx - ax))
        k = math.tan(math.radians(t_ang))
        left, right = a0[1] + (44 - a0[0]) * k, a0[1] + (202 - a0[0]) * k
        stem = poly([(44, -200), (202, -200), (202, 1), (44, 1)])
        below = op(side(a0, t_ang, -1), poly([(-100, -400), (300, -400), (300, 400), (-100, 400)]), 'i')
        p = op(union(p, stem), below, 'd')
        meta.update(foot_angle=round(t_ang, 2), foot_left=round(left, 1), foot_right=round(right, 1),
                    rule=meta['rule'] + '; the P\'s foot is cut along the line of the S\'s lower terminal, extended')
    return dict(parts=[('P', p), ('S', s)], meta=meta)


def terminal_line(F, which):
    """The straight cut of the S's lower or upper terminal, as two points in S's own units."""
    cur, lines = None, []
    for verb, args in F.outline('S'):
        if verb == 'moveTo':
            cur = args[0]
        elif verb == 'lineTo':
            lines.append((cur, args[0]))
            cur = args[0]
        elif verb in ('qCurveTo', 'curveTo'):
            cur = args[-1]
    cuts = sorted([l for l in lines if abs(l[1][0] - l[0][0]) > 100], key=lambda l: min(l[0][1], l[1][1]))
    l = cuts[0] if which == 'lower' else cuts[-1]
    return tuple(sorted(l))


def mark_overlap(F, M):
    P = F.glyph('P')
    dx = F.adv('P') - STEM
    S = F.glyph('S', dx=dx)
    s = op(S, grow(P, GAP), 'd')
    return dict(parts=[('P', P), ('S', s)],
                meta=dict(move='P in front', dx=round(dx, 1), clearance=GAP,
                          rule='S slides one stem width under the bowl and passes behind the whole P with 50 units clearance'))


def mark_foot(F, M):
    P = F.glyph('P')
    ang = M['terminal_angle']
    p = op(P, side((44, 0), ang, -1), 'd')
    rise = STEM * math.tan(math.radians(ang))
    return dict(parts=[('P', p), ('S', F.glyph('S', dx=F.adv('P')))],
                meta=dict(move='one detail', dx=F.adv('P'), angle=round(ang, 2), rise=round(rise, 1),
                          rule='the P\'s foot is cut at the angle of the S\'s terminals (and of ">"); spacing as set by the font'))


def apexes(F):
    """Heights where the curves turn vertical: the P's bowl and counter, the S's shoulder and upper counter."""
    def vertical_points(ch):
        pts = []
        for v, a in F.outline(ch):
            if v == 'qCurveTo' and len(a) >= 2 and abs(a[-1][0] - a[-2][0]) < 1e-6:
                pts.append(a[-1])
        return pts
    P = vertical_points('P')
    S = vertical_points('S')
    bowl = max(P, key=lambda q: q[0])                     # (604, 450)
    counter = [q for q in P if q != bowl and q[0] > 300][0]  # (437, 450)
    shoulder = min(S, key=lambda q: q[0])                  # (28, 473)
    s_counter = [q for q in S if 100 < q[0] < 250 and q[1] > 400][0]   # (190, 489)
    return dict(bowl=bowl, counter=counter, shoulder=shoulder, s_counter=s_counter)


def mark_slash_outer(F, M):
    """Slash, with the S lowered until its shoulder's outer curve turns at the height of the P's bowl."""
    a = apexes(F)
    m = mark_slash(F, M, drop=a['shoulder'][1] - a['bowl'][1])
    m['meta']['rule'] += '; S lowered until the outer curves of bowl and shoulder turn at the same height'
    return m


def mark_slash_inner(F, M):
    """Slash, with the S lowered until its upper counter turns at the height of the P's counter."""
    a = apexes(F)
    m = mark_slash(F, M, drop=a['s_counter'][1] - a['counter'][1])
    m['meta']['rule'] += '; S lowered until the inner curves (the counters) turn at the same height'
    return m


def mark_slash_foot(F, M):
    """Slash, S on the baseline; the P's foot continues the line of the S's lower terminal."""
    return mark_slash(F, M, drop=0.0, foot=True)


def mark_slash_foot_lowered(F, M):
    """Slash, S lowered 23 (outer curves level); the P's foot continues the S's terminal line."""
    a = apexes(F)
    return mark_slash(F, M, drop=a['shoulder'][1] - a['bowl'][1], foot=True)


def moved(p, dx, dy):
    q = pathops.Path()
    p.draw(TransformPen(q.getPen(), (1, 0, 0, 1, dx, dy)))
    return q


def _step(F, M, d, extend=True):
    """Slash; the S steps d down along the slash (gap stays 50, equal ink stays); with extend, the P's
    stem descends to the line of the S's lower terminal."""
    base = mark_slash(F, M)
    meta = dict(base['meta'])
    P1, S1 = base['parts'][0][1], base['parts'][1][1]
    ang = meta['angle']
    sx = -d / math.tan(math.radians(ang))
    S2 = moved(S1, sx, -d)
    (ax, ay), (bx, by) = terminal_line(F, 'lower')
    a0 = (ax + meta['dx'] + sx, ay - d)
    t_ang = math.degrees(math.atan2(by - ay, bx - ax))
    k = math.tan(math.radians(t_ang))
    left, right = a0[1] + (44 - a0[0]) * k, a0[1] + (202 - a0[0]) * k
    P2 = P1
    if extend:
        stem = poly([(44, -900), (202, -900), (202, 1), (44, 1)])
        below = op(side(a0, t_ang, -1), poly([(-100, -1200), (300, -1200), (300, 400), (-100, 400)]), 'i')
        P2 = op(union(P1, stem), below, 'd')
    meta.update(move='one cut, one step', drop=round(d, 1), slide_x=round(sx, 1),
                slide=round(d / math.sin(math.radians(ang)), 1), s_x=round(meta['dx'] + sx, 1),
                foot_angle=round(t_ang, 2), foot_left=round(left, 1), foot_right=round(right, 1))
    return dict(parts=[('P', P2), ('S', S2)], meta=meta)


def mark_slash_step(F, M):
    """Pete's idea 1, built exactly: the S steps down until its cap line sits at 450, where the P's bowl turns."""
    d = F.cap - apexes(F)['bowl'][1]                    # 668 - 450 = 218
    m = _step(F, M, d)
    m['meta']['rule'] = (m['meta']['rule'] + '; the S then steps down along the slash until its cap line sits at 450, '
                         'where the P\'s bowl turns; the P\'s stem descends to the line of the S\'s lower terminal')
    return m


def mark_slash_step_bar(F, M):
    """Idea 1 with a smaller step: one bar (133), so the S's cap line sits on the underside of the P's top bar (535)."""
    m = _step(F, M, BAR)
    m['meta']['rule'] = (m['meta']['rule'] + '; the S then steps down along the slash by one bar (133), so its cap line '
                         'sits on the underside of the P\'s top bar (535); the P\'s stem descends to the line of the S\'s lower terminal')
    return m


MARKS = dict(joined=mark_joined, slash=mark_slash, overlap=mark_overlap, foot=mark_foot,
             slash_outer=mark_slash_outer, slash_inner=mark_slash_inner,
             slash_foot=mark_slash_foot, slash_foot_lowered=mark_slash_foot_lowered,
             slash_step=mark_slash_step, slash_step_bar=mark_slash_step_bar)
TITLES = dict(set='As set', joined='Joined', slash='Slash', overlap='Overlap', foot='Foot', wordmark='Wordmark',
              slash_outer='Slash, S lowered 23', slash_inner='Slash, S lowered 39',
              slash_foot='Slash and foot', slash_foot_lowered='Slash and foot, S lowered 23',
              slash_step='Slash, S steps down', slash_step_bar='Slash, S steps down one bar')


# ---------------------------------------------------------------- svg output
def path_d(p, flip=True):
    pen = SVGPathPen(None, ntos=lambda v: ('%.1f' % v).rstrip('0').rstrip('.'))
    rec = RecordingPen()
    p.draw(rec)
    rec.replay(TransformPen(pen, (1, 0, 0, -1 if flip else 1, 0, 0)))
    return pen.getCommands()


def bbox(paths):
    bs = [p.bounds for p in paths if not empty(p)]
    return min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)


def mark_svg(parts, fill, pad=0.0, title='PS'):
    x0, y0, x1, y1 = bbox([p for _, p in parts])
    vb = (x0 - pad, -y1 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)
    body = '\n'.join(f'  <path id="{n}" d="{path_d(p)}"/>' for n, p in parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="{title}">\n<g fill="{fill}">\n{body}\n</g>\n</svg>\n')


def avatar_svg(parts, ground, fill, title='PS'):
    """Circle crop. The mark's width is 60 % of the circle; optical centre slightly above."""
    x0, y0, x1, y1 = bbox([p for _, p in parts])
    w, h = x1 - x0, y1 - y0
    D = w / 0.60
    cx, cy = (x0 + x1) / 2, -(y0 + y1) / 2
    r = D / 2
    body = '\n'.join(f'  <path d="{path_d(p)}"/>' for _, p in parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{cx - r:.1f} {cy - r:.1f} {D:.1f} {D:.1f}" '
            f'role="img" aria-label="{title}">\n'
            f'<clipPath id="c"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/></clipPath>\n'
            f'<g clip-path="url(#c)"><rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{D:.1f}" height="{D:.1f}" fill="{ground}"/></g>\n'
            f'<g fill="{fill}">\n{body}\n</g>\n</svg>\n')


def set_text(F, text, x=0.0, tracking=0.0):
    """Outlined text with GPOS kerning and CSS-style letter-spacing (em). Returns (path, advance)."""
    out = pathops.Path()
    pen = out.getPen()
    prev = None
    for ch in text:
        if prev is not None:
            x += F.kern(prev, ch)
        if ch != ' ':
            F.gs[F.name(ch)].draw(TransformPen(pen, (1, 0, 0, 1, x, 0)))
        x += F.adv(ch) + tracking * F.upm
        prev = ch
    return out, x


def wordmark(F):
    """'>_ PETER STIEG' as in the site header: caret, 0.45 em margin, name uppercase at 0.055 em."""
    caret, x = set_text(F, '>_')
    name, x2 = set_text(F, 'PETER STIEG', x=x + 0.45 * F.upm, tracking=0.055)
    return caret, name, x2 - 0.055 * F.upm


def lockup_svg(F, parts, T, mark_cap=2.0, gap_em=0.9, centre='cap', ground=True):
    """Mark at mark_cap x the text cap height, then the wordmark. centre='cap' puts the mark's cap on the
    text's cap; centre='box' centres the whole mark on it (for marks that reach below the baseline)."""
    caret, name, w = wordmark(F)
    els = []
    shift = 0.0
    if parts:
        x0, y0, x1, y1 = bbox([p for _, p in parts])
        s = mark_cap  # mark drawn at mark_cap times the text size
        mh = F.cap * s
        ty = (F.cap - mh) / 2 if centre == 'cap' else F.cap / 2 - (y0 + y1) / 2 * s
        mw = (x1 - x0) * s
        tr = f'translate({-x0 * s:.1f} {-ty:.1f}) scale({s})'
        els.append(f'<g fill="{T["ink"]}" transform="{tr}">' + ''.join(f'<path d="{path_d(p)}"/>' for _, p in parts) + '</g>')
        shift = mw + gap_em * F.upm
        top, bottom = ty + y1 * s + 12 * s, ty + y0 * s - 12 * s
    else:
        top, bottom = F.cap + 12, -130
    els.append(f'<g transform="translate({shift:.1f} 0)"><path fill="{T["accent"]}" d="{path_d(caret)}"/>'
               f'<path fill="{T["ink"]}" d="{path_d(name)}"/></g>')
    top = max(top, F.cap + 12)
    bottom = min(bottom, -130)
    W = shift + w
    pad = 120
    rect = (f'<rect x="{-pad}" y="{-top - pad:.1f}" width="{W + 2 * pad:.1f}" height="{top - bottom + 2 * pad:.1f}" '
            f'fill="{T["ground"]}"/>\n') if ground else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-pad} {-top - pad:.1f} {W + 2 * pad:.1f} {top - bottom + 2 * pad:.1f}" '
            f'role="img" aria-label="PS \u2013 Peter Stieg">\n' + rect + '\n'.join(els) + '\n</svg>\n')


# ---------------------------------------------------------------- hand-hinted favicons
# '#' = ink. Drawn by hand on the pixel grid after looking at the outline at that size:
# whole-pixel stems, bars and gaps; the cut and the joint kept where they carry the idea.
FAVICONS = {}   # the pixel grids live in favicons.py next to this script


def grid_rows(s):
    rows = [r.strip() for r in s.strip('\n').split('\n')]
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


def favicon_svg(rows, size, light, dark):
    h = len(rows)
    w = len(rows[0])
    ox = (size - w) // 2
    oy = (size - h) // 2
    rects = []
    for y, r in enumerate(rows):
        x = 0
        while x < w:
            if r[x] == '#':
                x1 = x
                while x1 < w and r[x1] == '#':
                    x1 += 1
                rects.append(f'M{ox + x} {oy + y}h{x1 - x}v1h{-(x1 - x)}z')
                x = x1
            else:
                x += 1
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" shape-rendering="crispEdges">\n'
            f'<style>path{{fill:{light}}}@media (prefers-color-scheme: dark){{path{{fill:{dark}}}}}</style>\n'
            f'<path d="{"".join(rects)}"/>\n</svg>\n')


def favicon_svg_fixed(rows, size, color):
    """Same grid, one fixed colour (for places that strip <style>, e.g. an <img> preview)."""
    return favicon_svg(rows, size, color, color).replace(
        f'<style>path{{fill:{color}}}@media (prefers-color-scheme: dark){{path{{fill:{color}}}}}</style>\n', '').replace(
        '<path d=', f'<path fill="{color}" d=')


def favicon_png(rows, size, color, ground=None):
    from PIL import Image
    im = Image.new('RGBA', (size, size), ground or (0, 0, 0, 0))
    h, w = len(rows), len(rows[0])
    ox, oy = (size - w) // 2, (size - h) // 2
    c = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                im.putpixel((ox + x, oy + y), c)
    return im


def auto_png(parts, size, color, cap_px, y_lo=0, y_hi=None):
    """What a browser does with the vector at that size: plain downscale, no hinting.
    Drawn at the same scale and position as the hinted grid, so the two compare fairly."""
    import resvg_py
    from PIL import Image
    y_hi = 668 if y_hi is None else y_hi
    x0, _, x1, _ = bbox([p for _, p in parts])
    u = (y_hi - y_lo) / cap_px
    wpx = (x1 - x0) / u
    ox = (size - math.ceil(wpx - 0.15)) // 2
    oy = (size - cap_px) // 2
    ss = 8
    vx, vy = x0 - ox * u, -y_hi - oy * u
    body = ''.join(f'<path d="{path_d(p)}"/>' for _, p in parts)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.2f} {vy:.2f} {size * u:.2f} {size * u:.2f}" '
           f'width="{size * ss}" height="{size * ss}"><g fill="{color}">{body}</g></svg>')
    big = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg)))).convert('RGBA')
    return big.resize((size, size), Image.BOX)


# ---------------------------------------------------------------- construction drawings
def label(R, text, x, y, size=30.0, anchor='start'):
    """Annotation text as outlines (Atkinson Regular), baseline at y, so the SVG needs no font."""
    raw, adv = set_text(R, text)
    s = size / R.upm
    w = adv * s
    dx = {'start': 0, 'middle': -w / 2, 'end': -w}[anchor]
    p = pathops.Path()
    raw.draw(TransformPen(p.getPen(), (s, 0, 0, s, x + dx, y)))
    return p


def _line(x0, y0, x1, y1, color, w=3.0, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<line x1="{x0:.1f}" y1="{-y0:.1f}" x2="{x1:.1f}" y2="{-y1:.1f}" stroke="{color}" '
            f'stroke-width="{w}"{da} stroke-linecap="butt"/>')


def _vdim(x, y0, y1, color, tick=14):
    return (_line(x, y0, x, y1, color) + _line(x - tick, y0, x + tick, y0, color) +
            _line(x - tick, y1, x + tick, y1, color))


def _hdim(y, x0, x1, color, tick=14):
    return (_line(x0, y, x1, y, color) + _line(x0, y - tick, x0, y + tick, color) +
            _line(x1, y - tick, x1, y + tick, color))


def _ring(p, w):
    """The band of width 2w along p's outline."""
    q = pathops.Path()
    p.draw(q.getPen())
    q.stroke(2 * w, pathops.LineCap.BUTT_CAP, pathops.LineJoin.ROUND_JOIN, 4)
    q.convertConicsToQuads()
    return op(q, q, 'u')


def outer_contour(F, ch):
    """The glyph's first contour only (the P without its counter)."""
    p = pathops.Path()
    pen = p.getPen()
    for verb, args in F.outline(ch):
        getattr(pen, verb)(*args)
        if verb == 'closePath':
            break
    return p


def construction_svg(F, R, M, k, m, T=LIGHT):
    """The mark, the font's untouched glyphs as dashed ghosts where they differ, and the move measured."""
    ink, acc, ghost, paper = T['ink'], T['accent'], T['muted'], T['ground']
    parts = m['parts']
    meta = m['meta']
    mark = union(*[p for _, p in parts])
    x0, y0, x1, y1 = mark.bounds
    big = poly([(-600, -600), (2400, -600), (2400, 1400), (-600, 1400)])
    outside = op(big, op(mark, _ring(mark, 6), 'u'), 'd')     # clear of the mark's edges
    inside = op(mark, _ring(mark, 6), 'd')
    defs = (f'<clipPath id="out-{k}"><path d="{path_d(outside)}"/></clipPath>'
            f'<clipPath id="in-{k}"><path d="{path_d(inside)}"/></clipPath>')
    under, over, labels = [], [], []
    P0 = F.glyph('P')

    def dashed(p, where='out', color=ghost, w=3):
        return (f'<path d="{path_d(p)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-dasharray="12 9" '
                f'stroke-linejoin="round" clip-path="url(#{where}-{k})"/>')

    if k == 'joined':
        under.append(dashed(F.glyph('S', dx=F.adv('P'))))
        i = op(P0, F.glyph('S', dx=meta['dx']), 'i')
        ix0, iy0, ix1, iy1 = i.bounds
        over.append(f'<path d="{path_d(i)}" fill="{acc}"/>')
        over += [_vdim(x1 + 60, iy0, iy1, acc), _vdim(-14, 535, 668, acc),
                 _hdim(-95, meta['dx'] + 25, F.adv('P') + 25, acc)]
        labels += [label(R, f'{iy1 - iy0:.0f}  the joint (red) is as tall', x1 + 92, (iy0 + iy1) / 2 + 2, size=26),
                   label(R, "as the P\u2019s bar", x1 + 92, (iy0 + iy1) / 2 - 36, size=26),
                   label(R, '133', -40, 590, size=26, anchor='end'),
                   label(R, f'S moves {F.adv("P") - meta["dx"]:.1f} to the left', (meta['dx'] + F.adv('P')) / 2 + 25, -150,
                         size=26, anchor='middle')]
        pad_r = 520
    elif k in ('slash_step', 'slash_step_bar'):
        Bm = mark_slash(F, M)
        PB, SB = Bm['parts'][0][1], Bm['parts'][1][1]
        under.append(dashed(SB))
        xl = max(x1, SB.bounds[2]) + 40
        ang = meta['angle']
        cx = meta['cut_x_at_half_cap']
        b = op(band((cx, F.cap / 2), ang, GAP), poly([(-200, -300), (1600, -300), (1600, 740), (-200, 740)]), 'i')
        under.insert(0, f'<path d="{path_d(b)}" fill="{acc}" fill-opacity="0.14"/>')
        added = op(parts[0][1], PB, 'd')
        over.append(f'<path d="{path_d(added)}" fill="{acc}"/>')
        (ax, ay), (bx, by) = terminal_line(F, 'lower')
        pa = (ax + meta['dx'], ay)
        pb = (ax + meta['s_x'], ay - meta['drop'])
        over.append(_line(pa[0], pa[1], pb[0] + 6, pb[1] + 15, acc, w=3))
        a = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
        hx, hy = math.cos(a), math.sin(a)
        nx, ny = -hy, hx
        tip = (pb[0], pb[1])
        over.append(f'<path d="M{tip[0]:.1f} {-tip[1]:.1f} L{tip[0] - 34 * hx + 13 * nx:.1f} {-(tip[1] - 34 * hy + 13 * ny):.1f} '
                    f'L{tip[0] - 34 * hx - 13 * nx:.1f} {-(tip[1] - 34 * hy - 13 * ny):.1f}Z" fill="{acc}"/>')
        kk2 = math.tan(math.radians(meta['foot_angle']))
        xs, xe = -20, bx + meta['s_x'] + 70
        over.append(_line(xs, pb[1] + (xs - pb[0]) * kk2, xe, pb[1] + (xe - pb[0]) * kk2, acc, w=2.5))
        y_cap = F.cap - meta['drop']
        for y, dash in ((F.cap, None), (y_cap, '14 10'), (0, None)):
            over.append(_line(-120, y, xl - 10, y, acc, w=1.5 if dash is None else 2, dash=dash))
        labels += [label(R, f'S steps {meta["slide"]:.0f} down the slash:', xl, 520, size=26),
                   label(R, f'{meta["drop"]:.0f} lower, {-meta["slide_x"]:.0f} to the left', xl, 482, size=26),
                   label(R, f'its cap line now sits at {y_cap:.0f},', xl, 432, size=26),
                   label(R, 'where the P\u2019s bowl turns' if k == 'slash_step' else 'the underside of the P\u2019s top bar', xl, 394, size=26),
                   label(R, 'gap 50 and equal ink, as before', xl, 344, size=26),
                   label(R, f'{meta["foot_angle"]:.1f}\u00b0  one line: the S\u2019s lower terminal', xl, 120, size=26),
                   label(R, f'is the P\u2019s new foot ({meta["foot_left"]:.0f} to {meta["foot_right"]:.0f})', xl, 82, size=26),
                   label(R, 'red: what the stem gains', xl, 32, size=26)]
        pad_r = xl - x1 + 600
    elif k.startswith('slash'):
        under.append(dashed(P0))
        under.append(dashed(F.glyph('S', dx=meta['dx'], dy=-meta['drop'])))
        ang = meta['angle']
        cx = meta['cut_x_at_half_cap']
        b = op(band((cx, F.cap / 2), ang, GAP), poly([(-200, -60), (1600, -60), (1600, 740), (-200, 740)]), 'i')
        under.insert(0, f'<path d="{path_d(b)}" fill="{acc}" fill-opacity="0.14"/>')
        kk = 1 / math.tan(math.radians(ang))
        h = GAP / 2 / math.sin(math.radians(ang))
        for sgn in (-1, 1):
            over.append(_line(cx + sgn * h + (-60 - F.cap / 2) * kk, -60, cx + sgn * h + (740 - F.cap / 2) * kk, 740, acc, w=2))
        xb0 = cx - F.cap / 2 * kk
        r, a = 120, math.radians(ang)
        over += [_line(xb0, 0, xb0 + 200, 0, acc, w=2),
                 f'<path d="M{xb0 + r:.1f} 0 A{r} {r} 0 0 0 {xb0 + r * math.cos(a):.1f} {-r * math.sin(a):.1f}" '
                 f'fill="none" stroke="{acc}" stroke-width="3"/>']
        labels += [label(R, f'{ang:.1f}\u00b0  the angle of Atkinson\u2019s /', xb0 + 40 if meta.get('foot_angle') is not None else xb0 - 40, -80, size=26),
                   label(R, '50  gap = the font\u2019s own P\u2013S space', x1 + 40, F.cap / 2 + 90, size=26),
                   label(R, 'the cut takes the same ink from P and S', x1 + 40, F.cap / 2 + 40, size=26),
                   label(R, f'({meta["ink_taken_P"]:,} u\u00b2 each)'.replace(',', '\u00a0'), x1 + 40, F.cap / 2 + 2, size=26),
                   label(R, 'S moves 158 = one stem', x1 + 40, F.cap / 2 - 48, size=26)]
        if meta['drop']:
            ap = apexes(F)
            xr = meta['dx'] + 596 + 50
            over.append(_vdim(xr, 680 - meta['drop'], 680, acc, tick=10))
            over.append(_line(meta['dx'] + 311, 680, xr + 10, 680, acc, w=1.5, dash='6 6'))
            outer = abs(meta['drop'] - (ap['shoulder'][1] - ap['bowl'][1])) < 0.5
            pair = ('bowl', 'shoulder') if outer else ('counter', 's_counter')
            y_al = ap[pair[0]][1]
            over.append(_line(-120, y_al, x1 + 30, y_al, acc, w=2, dash='14 10'))
            over.append(_line(-120, 0, x1 + 30, 0, acc, w=1.5))
            what = 'outer curves' if outer else 'counters'
            labels += [label(R, f'S lowered {meta["drop"]:.0f}: the {what} of P and S', x1 + 40, F.cap / 2 - 110, size=26),
                       label(R, f'turn at the same height ({y_al:.0f})', x1 + 40, F.cap / 2 - 148, size=26),
                       label(R, f'{meta["drop"]:.0f}', xr + 26, 680 - meta['drop'] / 2 - 10, size=26),
                       label(R, f'S top {F.cap - (680 - meta["drop"]):.0f} below the cap, foot {12 + meta["drop"]:.0f} below the baseline',
                             x1 + 40, F.cap / 2 - 198, size=26)]
        if meta.get('foot_angle') is not None:
            (ax, ay), (bx, by) = terminal_line(F, 'lower')
            a0 = (ax + meta['dx'], ay - meta['drop'])
            b0 = (bx + meta['dx'], by - meta['drop'])
            kk2 = math.tan(math.radians(meta['foot_angle']))
            xs = -20
            over.append(_line(xs, a0[1] + (xs - a0[0]) * kk2, b0[0] + 60, b0[1] + 60 * kk2, acc, w=2.5))
            mine = parts[0][1]
            changed = op(op(P0, mine, 'd'), poly([(0, -300), (260, -300), (260, 200), (0, 200)]), 'i')
            added = op(mine, P0, 'd')
            under.append(f'<path d="{path_d(changed)}" fill="{acc}"/>')
            over.append(f'<path d="{path_d(added)}" fill="{acc}"/>')
            over.append(_line(-120, 0, 330, 0, acc, w=1.5))
            labels += [label(R, f'{meta["foot_angle"]:.1f}\u00b0  one line: the S\u2019s lower terminal', 0, -150, size=26),
                       label(R, f'carried through the P\u2019s foot ({meta["foot_left"]:+.0f} to {meta["foot_right"]:+.0f})', 0, -188, size=26)]
        pad_r = 760 if meta['drop'] else 560
    elif k == 'overlap':
        S1 = F.glyph('S', dx=meta['dx'])
        Po = outer_contour(F, 'P')
        ring = op(op(grow(Po, GAP), Po, 'd'), poly([(420, -60), (1600, -60), (1600, 740), (420, 740)]), 'i')
        under.insert(0, f'<path d="{path_d(ring)}" fill="{acc}" fill-opacity="0.16"/>')
        under.append(dashed(S1))
        over.append(dashed(S1, where='in', color=paper, w=3))
        over.append(_hdim(-95, meta['dx'] + 25, F.adv('P') + 25, acc))
        labels += [label(R, 'S moves 158 = one stem', (meta['dx'] + F.adv('P')) / 2 + 25, -150, size=26, anchor='middle'),
                   label(R, '50  clearance (red) = the font\u2019s', x1 + 40, F.cap / 2 + 90, size=26),
                   label(R, 'own P\u2013S space', x1 + 40, F.cap / 2 + 52, size=26),
                   label(R, 'the P stays whole, the S runs behind', x1 + 40, F.cap / 2 + 2, size=26)]
        pad_r = 560
    else:  # foot
        ang = meta['angle']
        t = math.tan(math.radians(ang))
        removed = op(P0, parts[0][1], 'd')
        under.append(f'<path d="{path_d(removed)}" fill="{acc}"/>')
        over.append(_line(-40, -84 * t, 330, 286 * t, acc, w=2))
        for (ax, ay), (bx, by) in [((25, 157), (169, 209)), ((424, 483), (567, 535))]:
            dx_ = F.adv('P')
            ux, uy = bx - ax, by - ay
            n = math.hypot(ux, uy)
            ux, uy = ux / n, uy / n
            over.append(_line(dx_ + ax - ux * 90, ay - uy * 90, dx_ + bx + ux * 90, by + uy * 90, acc, w=2))
        gs = 0.62
        gx, gy = x1 + 140, 60
        under.append(f'<path d="{path_d(F.glyph(">", dx=gx, dy=gy, s=gs))}" fill="{ghost}" fill-opacity="0.5"/>')
        pa = math.tan(math.radians(M['prompt_angle']))
        ax_, ay_ = gx + 40 * gs, gy + 130 * gs
        over.append(_line(ax_ - 50, ay_ - 50 * pa, ax_ + 325 * gs + 70, ay_ + (325 * gs + 70) * pa, acc, w=2))
        labels += [label(R, f'{ang:.1f}\u00b0  the P\u2019s foot (red: what it loses)', 0, -110, size=26),
                   label(R, '= the angle of both S terminals', 0, -148, size=26),
                   label(R, f'{M["prompt_angle"]:.1f}\u00b0  the arm of the prompt\u2019s >', gx - 10, -60, size=26)]
        pad_r = 700
    pad_l, pad_t, pad_b = 170, 120, 260
    vb = (x0 - pad_l, -(y1 + pad_t), (x1 - x0) + pad_l + pad_r, (y1 - y0) + pad_t + pad_b)
    body = ''.join(f'<path d="{path_d(p)}" fill="{ink}"/>' for _, p in parts)
    lab = ''.join(f'<path d="{path_d(p)}" fill="{acc}"/>' for p in labels)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="Construction of the {TITLES[k]} monogram">\n<defs>{defs}</defs>\n'
            + '\n'.join(under) + '\n' + body + '\n' + '\n'.join(over) + '\n' + lab + '\n</svg>\n')


def drop_compare_svg(F, R, M, T=LIGHT, variants=None):
    """Slash variants side by side on one baseline, with cap, baseline and 450 drawn."""
    ink, acc = T['ink'], T['accent']
    variants = variants or [('slash', '0 \u00b7 as before'), ('slash_outer', '23 \u00b7 outer curves level'),
                            ('slash_inner', '39 \u00b7 counters level')]
    step = 1300
    els, labs = [], []
    for i, (k, text) in enumerate(variants):
        m = MARKS[k](F, M)
        ox = i * step
        els += [f'<path transform="translate({ox} 0)" d="{path_d(p)}" fill="{ink}"/>' for _, p in m['parts']]
        labs.append(label(R, text, ox + 44, -190, size=40))
    W = step * 3 - 200
    for y, dash in ((0, None), (668, None), (450, '16 12')):
        els.append(_line(-80, y, W, y, acc, w=2.5, dash=dash))
    labs += [label(R, 'cap 668', W + 20, 668 - 12, size=30), label(R, 'baseline', W + 20, -12, size=30),
             label(R, '450  where the P\u2019s bowl turns', W + 20, 450 - 12, size=30)]
    vb = (-120, -800, W + 620, 1100)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" role="img" '
            f'aria-label="Slash with the S at three heights">\n' + '\n'.join(els) + '\n'
            + ''.join(f'<path d="{path_d(p)}" fill="{acc}"/>' for p in labs) + '\n</svg>\n')


def parts_svg(F, M, k='slash_foot', T=LIGHT, line_w=6.0):
    """The slash-and-foot mark as separate, named elements: P, S, slash, terminal line, foot."""
    m = MARKS[k](F, M)
    meta = m['meta']
    P1, S1 = m['parts'][0][1], m['parts'][1][1]
    # the slash: the gap itself, from baseline to cap like the font's own /
    ang, cx = meta['angle'], meta['cut_x_at_half_cap']
    slash = op(band((cx, F.cap / 2), ang, GAP), poly([(-500, 0), (2000, 0), (2000, F.cap), (-500, F.cap)]), 'i')
    # the foot: what the terminal line takes off the P's stem, or adds to it
    foot = op(op(F.glyph('P'), P1, 'x'), poly([(0, -1000), (260, -1000), (260, 200), (0, 200)]), 'i')
    (ax, ay), (bx, by) = terminal_line(F, 'lower')
    sxo = meta.get('s_x', meta['dx'])
    a0 = (ax + sxo, ay - meta['drop'])
    b0 = (bx + sxo, by - meta['drop'])
    kk = math.tan(math.radians(meta['foot_angle']))
    x_start, x_end = 0.0, b0[0] + 60
    y_start, y_end = a0[1] + (x_start - a0[0]) * kk, a0[1] + (x_end - a0[0]) * kk
    allp = union(P1, S1, slash, foot)
    x0, y0, x1, y1 = allp.bounds
    x0, x1 = min(x0, x_start), max(x1, x_end)
    y0, y1 = min(y0, y_start), max(y1, y_end)
    pad = 40
    vb = (x0 - pad, -(y1 + pad), x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)
    ink, red = T['ink'], T['accent']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" '
            f'role="img" aria-label="PS monogram: {TITLES[k]}">\n'
            f'<title>PS \u2013 Atkinson Hyperlegible Bold, slash {ang:.1f}\u00b0, terminal line {meta["foot_angle"]:.1f}\u00b0</title>\n'
            f'<path id="P" fill="{ink}" d="{path_d(P1)}"/>\n'
            f'<path id="S" fill="{ink}" d="{path_d(S1)}"/>\n'
            f'<path id="slash" fill="{red}" d="{path_d(slash)}"/>\n'
            f'<path id="foot" fill="{red}" d="{path_d(foot)}"/>\n'
            f'<line id="terminal-line" x1="{x_start:.1f}" y1="{-y_start:.1f}" x2="{x_end:.1f}" y2="{-y_end:.1f}" '
            f'stroke="{red}" stroke-width="{line_w}" stroke-linecap="butt"/>\n</svg>\n')


# ---------------------------------------------------------------- tried on the way
def tried(F, M):
    """Sketches that did not make it, built the same way, kept for the record."""
    P = F.glyph('P')
    out = {}
    # 1. a 20-degree hairline through both letters, along the S's upper terminal
    S = F.glyph('S', dx=600)
    out['hairline'] = [('PS', op(union(P, S), band((600 + 495.5, 509), M['terminal_angle'], 24), 'd'))]
    # 2. overlap cancelled (xor)
    out['xor'] = [('PS', op(P, F.glyph('S', dx=480), 'x'))]
    # 3. the tail of Atkinson's l on the P
    lt = op(F.glyph('l', dx=-6), poly([(0, -10), (400, -10), (400, 300), (0, 300)]), 'i')
    out['ltail'] = [('P', union(P, lt)), ('S', F.glyph('S', dx=F.adv('P')))]
    # 4. the P's flat top carried over the S
    S4 = F.glyph('S', dx=F.adv('P'))
    out['roof'] = [('PS', union(P, S4, poly([(200, 535), (F.adv('P') + 596, 535), (F.adv('P') + 596, 668), (200, 668)])))]
    # 5. the prompt as the P's bowl
    stem = poly([(44, 0), (202, 0), (202, 668), (44, 668)])
    gt = F.glyph('>', dx=202 - 40 - 30, dy=668 - 510)
    out['prompt_p'] = [('P', union(stem, gt)), ('S', F.glyph('S', dx=640))]
    # 6. capital P with lowercase s
    out['ps_lower'] = [('P', P), ('s', F.glyph('s', dx=F.adv('P')))]
    # 7. overlap the other way round: S in front
    S7 = F.glyph('S', dx=468)
    out['s_front'] = [('P', op(P, grow(S7, GAP), 'd')), ('S', S7)]
    # 8. joined deeper
    out['fused'] = [('PS', union(P, F.glyph('S', dx=M['touch_dx'] - 70)))]
    # 9.-11. alternatives to idea 1
    out['step_no_stem'] = _step(F, M, F.cap - apexes(F)['bowl'][1], extend=False)['parts']
    out['tuck_two'] = mark_slash(F, M, foot=True, tuck=2)['parts']
    out['tuck_half'] = mark_slash(F, M, foot=True, tuck=1.5)['parts']
    # 12. the P alone, as a favicon
    out['p_alone'] = [mark_slash(F, M, foot=True)['parts'][0]]
    return out


TRIED_NOTES = {
    'hairline': '20° hairline through both letters: reads as a break, the P loses its foot',
    'xor': 'Overlap cancelled out: the lens reads as an eye, decoration',
    'ltail': 'Tail of Atkinson’s l on the P: a lowercase foot that never reaches the S',
    'roof': 'The P’s flat top carried over the S: the S turns into a 5',
    'prompt_p': 'The prompt as the P’s bowl: a play on >, reads as a pun, not a letter',
    'ps_lower': 'Capital P, lowercase s: Photoshop',
    's_front': 'S in front of the P: the PlayStation order; the first name should lead',
    'fused': 'Joined deeper: fuses into one blob below 24 px',
    'step_no_stem': 'Idea 1 without the longer stem: equal letters, but the S still sits low and the line joins nothing',
    'tuck_two': 'S two stems under the bowl: nearly square, but the slash eats the bowl and the P reads as F',
    'tuck_half': 'S one and a half stems under the bowl: 1.36 : 1, but no rule behind the half',
    'p_alone': 'The P alone as favicon: no Ps, no PlayStation, but the surname is gone where the mark is smallest',
}


# ---------------------------------------------------------------- the locked mark
FINAL = 'slash_step_bar'          # locked 23.10.2026: idea 1 with a step of one bar
FINAL_NAME = 'ps-monogram'
CLEAR = STEM                      # clear space: one stem on every side


def _png(svg, path, width=None, height=None):
    import resvg_py
    kw = {}
    if width:
        kw['width'] = width
    if height:
        kw['height'] = height
    open(path, 'wb').write(bytes(resvg_py.svg_to_bytes(svg_string=svg, **kw)))


def square_svg(parts, fill, fill_dark=None, margin=0.03, ground=None, scale=1.0):
    """The mark centred in a square; optional ground and a dark-scheme colour via a media query."""
    x0, y0, x1, y1 = bbox([p for _, p in parts])
    w, h = x1 - x0, y1 - y0
    side = max(w, h) * (1 + 2 * margin) / scale
    cx, cy = (x0 + x1) / 2, -(y0 + y1) / 2
    vx, vy = cx - side / 2, cy - side / 2
    style = ''
    if fill_dark:
        style = (f'<style>path{{fill:{fill}}}@media (prefers-color-scheme: dark){{path{{fill:{fill_dark}}}}}</style>\n')
    g = f'<rect x="{vx:.1f}" y="{vy:.1f}" width="{side:.1f}" height="{side:.1f}" fill="{ground}"/>\n' if ground else ''
    attr = '' if fill_dark else f' fill="{fill}"'
    body = '\n'.join(f'<path{attr} d="{path_d(p)}"/>' for _, p in parts)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vx:.1f} {vy:.1f} {side:.1f} {side:.1f}" role="img" '
            f'aria-label="PS">\n' + style + g + body + '\n</svg>\n')


def clearspace_svg(F, R, parts, T=LIGHT):
    """The mark, its clear space (one stem on every side) and the minimum sizes."""
    ink, acc = T['ink'], T['accent']
    x0, y0, x1, y1 = bbox([p for _, p in parts])
    c = CLEAR
    els = [f'<path d="{path_d(p)}" fill="{ink}"/>' for _, p in parts]
    els.append(f'<rect x="{x0 - c:.1f}" y="{-(y1 + c):.1f}" width="{x1 - x0 + 2 * c:.1f}" height="{y1 - y0 + 2 * c:.1f}" '
               f'fill="none" stroke="{acc}" stroke-width="3" stroke-dasharray="14 10"/>')
    els.append(f'<rect x="{x0:.1f}" y="{-y1:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="none" '
               f'stroke="{acc}" stroke-width="1.5"/>')
    els += [_hdim(y1 + c / 2, x1, x1 + c, acc, tick=10), _vdim(x0 - c / 2, y0 - c, y0, acc, tick=10)]
    # a stem, to show where the unit comes from
    els.append(f'<rect x="44" y="{-(y1):.1f}" width="{STEM}" height="24" fill="{acc}"/>')
    labs = [label(R, f'{c:.0f} = one stem', x1 + c + 30, y1 + c / 2 - 10, size=30),
            label(R, 'clear space on every side', x1 + c + 30, y1 + c / 2 - 52, size=30)]
    vb = (x0 - c - 60, -(y1 + c + 60), (x1 - x0) + 2 * c + 520, (y1 - y0) + 2 * c + 120)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" role="img" '
            f'aria-label="Clear space: one stem on every side">\n' + '\n'.join(els) + '\n'
            + ''.join(f'<path d="{path_d(p)}" fill="{acc}"/>' for p in labs) + '\n</svg>\n')


def export_final(F, M, out):
    """The locked mark with clean names: masters, PNGs, avatars, favicon set, lockups, spec drawings."""
    from PIL import Image
    R = Font(os.path.join(os.path.dirname(os.path.abspath(F.path)), 'AtkinsonHyperlegible-Regular.ttf'))
    m = MARKS[FINAL](F, M)
    parts = m['parts']
    n = FINAL_NAME
    d = {k: os.path.join(out, 'final', k) for k in ('mark', 'avatar', 'favicon', 'lockup', 'spec')}
    for v in d.values():
        os.makedirs(v, exist_ok=True)
    colours = {'ink': LIGHT['ink'], 'paper': DARK['ink'], 'bordeaux': LIGHT['accent'], 'bordeaux-dark': DARK['accent']}
    title = 'PS \u2013 Peter Stieg'
    open(os.path.join(d['mark'], f'{n}.svg'), 'w').write(mark_svg(parts, 'currentColor', title=title))
    for k, c in colours.items():
        svg = mark_svg(parts, c, title=title)
        open(os.path.join(d['mark'], f'{n}-{k}.svg'), 'w').write(svg)
        _png(svg, os.path.join(d['mark'], f'{n}-{k}-2048.png'), width=2048)
    for k, g, f in (('light', LIGHT['ground'], LIGHT['ink']), ('dark', DARK['ground'], DARK['ink']),
                    ('bordeaux', LIGHT['accent'], LIGHT['ground'])):
        svg = avatar_svg(parts, g, f, title=title)
        open(os.path.join(d['avatar'], f'avatar-{k}.svg'), 'w').write(svg)
        _png(svg, os.path.join(d['avatar'], f'avatar-{k}-1024.png'), width=1024)
    # favicons: vector for modern browsers, hand-hinted pixels in the .ico, touch and manifest icons
    fav = d['favicon']
    open(os.path.join(fav, 'favicon.svg'), 'w').write(square_svg(parts, LIGHT['accent'], DARK['accent']))
    rows = {s: grid_rows(FAVICONS[FINAL][s]) for s in (16, 32)}
    for s in (16, 32):
        open(os.path.join(fav, f'favicon-{s}-hinted.svg'), 'w').write(favicon_svg(rows[s], s, LIGHT['accent'], DARK['accent']))
        favicon_png(rows[s], s, LIGHT['accent']).save(os.path.join(fav, f'favicon-{s}.png'))
    _png(square_svg(parts, LIGHT['accent']), os.path.join(fav, 'favicon-48.png'), width=48)
    i16 = Image.open(os.path.join(fav, 'favicon-16.png'))
    i32 = Image.open(os.path.join(fav, 'favicon-32.png'))
    i48 = Image.open(os.path.join(fav, 'favicon-48.png'))
    i48.save(os.path.join(fav, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)], append_images=[i16, i32])
    tile = square_svg(parts, LIGHT['accent'], margin=0.0, ground=LIGHT['ground'], scale=0.62)
    _png(tile, os.path.join(fav, 'apple-touch-icon.png'), width=180)
    for s in (192, 512):
        _png(tile, os.path.join(fav, f'icon-{s}.png'), width=s)
    json.dump({'name': 'Peter Stieg', 'short_name': 'PS',
               'icons': [{'src': f'icon-{s}.png', 'sizes': f'{s}x{s}', 'type': 'image/png', 'purpose': 'any maskable'}
                         for s in (192, 512)],
               'theme_color': LIGHT['ground'], 'background_color': LIGHT['ground'], 'display': 'browser'},
              open(os.path.join(fav, 'site.webmanifest'), 'w'), indent=2)
    open(os.path.join(fav, 'head.html'), 'w').write(
        '<link rel="icon" href="favicon.ico" sizes="48x48">\n'
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">\n'
        '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
        '<link rel="manifest" href="site.webmanifest">\n')
    # lockups: transparent, mark centred as a whole on the wordmark's cap
    for k, T in (('light', LIGHT), ('dark', DARK)):
        svg = lockup_svg(F, parts, T, centre='box', ground=False)
        open(os.path.join(d['lockup'], f'lockup-{k}.svg'), 'w').write(svg)
        _png(svg, os.path.join(d['lockup'], f'lockup-{k}-2400.png'), width=2400)
    # spec drawings
    open(os.path.join(d['spec'], 'construction.svg'), 'w').write(construction_svg(F, R, M, FINAL, m))
    open(os.path.join(d['spec'], 'clearspace.svg'), 'w').write(clearspace_svg(F, R, parts))
    open(os.path.join(d['spec'], 'parts.svg'), 'w').write(parts_svg(F, M, FINAL))
    return m


# ---------------------------------------------------------------- main
def build(font_path, out):
    F = Font(font_path)
    M = measure(F)
    marks = {k: f(F, M) for k, f in MARKS.items()}
    marks_all = dict(set=mark_set(F, M), **marks)
    os.makedirs(os.path.join(out, 'svg'), exist_ok=True)
    os.makedirs(os.path.join(out, 'favicon'), exist_ok=True)
    meta = dict(font=os.path.basename(font_path), upm=F.upm, cap=F.cap, measured=M,
                constants=dict(gap=GAP, bar=BAR, stem=STEM), marks={})
    for k, m in marks_all.items():
        parts = m['parts']
        x0, y0, x1, y1 = bbox([p for _, p in parts])
        meta['marks'][k] = dict(m['meta'], width=round(x1 - x0, 1), height=round(y1 - y0, 1),
                                aspect=round((x1 - x0) / (y1 - y0), 3))
        for nm, fill in (('ink', LIGHT['ink']), ('paper', DARK['ink']), ('accent', LIGHT['accent']),
                         ('currentcolor', 'currentColor')):
            open(os.path.join(out, 'svg', f'{k}_{nm}.svg'), 'w').write(mark_svg(parts, fill, title=f'PS – {TITLES[k]}'))
        if k == 'set':
            continue
        for nm, g, f in (('light', LIGHT['ground'], LIGHT['ink']), ('dark', DARK['ground'], DARK['ink']),
                         ('accent', LIGHT['accent'], LIGHT['ground'])):
            open(os.path.join(out, 'svg', f'{k}_avatar_{nm}.svg'), 'w').write(avatar_svg(parts, g, f))
        for nm, T in (('light', LIGHT), ('dark', DARK)):
            open(os.path.join(out, 'svg', f'lockup_{k}_{nm}.svg'), 'w').write(lockup_svg(F, parts, T))
    for nm, T in (('light', LIGHT), ('dark', DARK)):
        open(os.path.join(out, 'svg', f'lockup_wordmark_{nm}.svg'), 'w').write(lockup_svg(F, None, T))
    # construction drawings and the sketches that did not make it
    R = Font(os.path.join(os.path.dirname(font_path), 'AtkinsonHyperlegible-Regular.ttf'))
    os.makedirs(os.path.join(out, 'construction'), exist_ok=True)
    for k, m in marks.items():
        open(os.path.join(out, 'construction', f'{k}.svg'), 'w').write(construction_svg(F, R, M, k, m))
    open(os.path.join(out, 'construction', 'slash_drop_compare.svg'), 'w').write(drop_compare_svg(F, R, M))
    open(os.path.join(out, 'construction', 'slash_foot_compare.svg'), 'w').write(drop_compare_svg(F, R, M, variants=[
        ('slash', 'Slash'), ('slash_foot', 'Slash and foot, S on the baseline'),
        ('slash_foot_lowered', 'Slash and foot, S lowered 23')]))
    open(os.path.join(out, 'svg', 'slash_foot_parts.svg'), 'w').write(parts_svg(F, M))
    open(os.path.join(out, 'svg', 'slash_step_parts.svg'), 'w').write(parts_svg(F, M, 'slash_step'))
    open(os.path.join(out, 'svg', 'slash_step_bar_parts.svg'), 'w').write(parts_svg(F, M, 'slash_step_bar'))
    os.makedirs(os.path.join(out, 'tried'), exist_ok=True)
    for k, parts in tried(F, M).items():
        open(os.path.join(out, 'tried', f'{k}.svg'), 'w').write(mark_svg(parts, LIGHT['ink'], title=TRIED_NOTES[k]))
    meta['tried'] = TRIED_NOTES
    # prompt mark from the font, for the favicon control
    caret, _ = set_text(F, '>_')
    marks_all['prompt'] = dict(parts=[('prompt', caret)], meta=dict(move='control'))
    open(os.path.join(out, 'svg', 'prompt_accent.svg'), 'w').write(mark_svg([('prompt', caret)], LIGHT['accent'], title='>_'))
    # favicons
    for k, sizes in FAVICONS.items():
        rows = {s: grid_rows(sizes[s]) for s in (16, 32)}
        fav = os.path.join(out, 'favicon')
        open(os.path.join(fav, f'{k}.svg'), 'w').write(favicon_svg(rows[32], 32, LIGHT['accent'], DARK['accent']))
        open(os.path.join(fav, f'{k}-16.svg'), 'w').write(favicon_svg(rows[16], 16, LIGHT['accent'], DARK['accent']))
        for s in (16, 32):
            for nm, c in (('light', LIGHT['accent']), ('dark', DARK['accent'])):
                open(os.path.join(fav, f'{k}-{s}-{nm}.svg'), 'w').write(favicon_svg_fixed(rows[s], s, c))
        i16 = favicon_png(rows[16], 16, LIGHT['accent'])
        i32 = favicon_png(rows[32], 32, LIGHT['accent'])
        i16.save(os.path.join(fav, f'{k}-16.png'))
        i32.save(os.path.join(fav, f'{k}-32.png'))
        i32.save(os.path.join(fav, f'{k}.ico'), sizes=[(16, 16), (32, 32)], append_images=[i16])
        if k == 'prompt':
            ylo, yhi, caps = -128, 510, {16: 10, 32: 20}
        elif k == 'slash_step':
            ylo, yhi, caps = -230, 668, {16: 13, 32: 28}
        elif k == 'slash_step_bar':
            ylo, yhi, caps = -145, 668, {16: 12, 32: 25}
        else:
            ylo, yhi, caps = 0, 668, {16: 9, 32: 18}
        for s in (16, 32):
            auto_png(marks_all[k]['parts'], s, LIGHT['accent'], caps[s], ylo, yhi).save(
                os.path.join(fav, f'{k}-auto-{s}.png'))
    # touch icons: iOS puts them on a rounded square itself, so the mark sits on paper, Bordeaux
    import resvg_py
    for k, m in marks.items():
        x0, y0, x1, y1 = bbox([p for _, p in m['parts']])
        w, h = x1 - x0, y1 - y0
        S = w / 0.62
        cx, cy = (x0 + x1) / 2, -(y0 + y1) / 2
        body = ''.join(f'<path d="{path_d(p)}"/>' for _, p in m['parts'])
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{cx - S / 2:.1f} {cy - S / 2:.1f} {S:.1f} {S:.1f}" '
               f'width="180" height="180"><rect x="{cx - S / 2:.1f}" y="{cy - S / 2:.1f}" width="{S:.1f}" height="{S:.1f}" '
               f'fill="{LIGHT["ground"]}"/><g fill="{LIGHT["accent"]}">{body}</g></svg>')
        open(os.path.join(out, 'favicon', f'{k}-apple-touch-180.png'), 'wb').write(bytes(resvg_py.svg_to_bytes(svg_string=svg)))
    meta['final'] = dict(mark=FINAL, locked='2026-10-23', clear_space=CLEAR)
    export_final(F, M, out)
    json.dump(meta, open(os.path.join(out, 'marks.json'), 'w'), indent=2, ensure_ascii=False)
    return F, M, marks_all, meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', default=os.path.join(HERE, 'fonts', 'AtkinsonHyperlegible-Bold.ttf'))
    ap.add_argument('--out', default=os.path.join(HERE, 'out'))
    a = ap.parse_args()
    try:
        from favicons import FAVICONS as _F
        FAVICONS.update(_F)
    except ImportError:
        pass
    _, M, _, meta = build(a.font, a.out)
    print(json.dumps({k: v.get('dx') for k, v in meta['marks'].items()}), 'terminal %.2f slash %.2f prompt %.2f touch %.1f' %
          (M['terminal_angle'], M['slash_angle'], M['prompt_angle'], M['touch_dx']))
