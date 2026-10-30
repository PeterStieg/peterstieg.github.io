"""Preview sheet: favicon v2 (paper PS on a bordeaux disc) next to v1 (bare bordeaux mark), on four tab colours."""
import io, os
from PIL import Image, ImageDraw, ImageFont
import resvg_py
import ps_monogram as pm

HERE = os.path.dirname(os.path.abspath(__file__))
TABS = [('white tab', '#FFFFFF', '#1F1F1F'), ('light grey #DFE1E5', '#DFE1E5', '#1F1F1F'),
        ('Chrome dark #35363A', '#35363A', '#E8EAED'), ('Firefox dark #2B2A33', '#2B2A33', '#FBFBFE')]
SHEET, INK, MUTED, LINE = '#F7F6F3', '#1A1C1E', '#565B60', '#DCDAD4'


def svg_png(svg, size, ss=8):
    big = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=size * ss)))).convert('RGBA')
    return big.resize((size, size), Image.BOX)


def font(bold, px):
    return ImageFont.truetype(os.path.join(HERE, 'fonts', 'AtkinsonHyperlegible-%s.ttf' % ('Bold' if bold else 'Regular')), px)


def icons(F, M):
    import favicons                                        # the grids, as ps_monogram.py loads them when run
    pm.FAVICONS.update(favicons.FAVICONS)
    pm.FAVICONS_DISC.update({s: pm.grid_rows(g) for s, g in favicons.FAVICONS_DISC.items()})
    parts = pm.MARKS[pm.FINAL](F, M)['parts']
    v1_rows = {s: pm.grid_rows(pm.FAVICONS[pm.FINAL][s]) for s in (16, 32)}
    v1_svg = pm.square_svg(parts, pm.LIGHT['accent'])               # what favicon.svg showed in a light OS scheme
    v1 = {'ico16': pm.favicon_png(v1_rows[16], 16, pm.LIGHT['accent']),
          'ico32': pm.favicon_png(v1_rows[32], 32, pm.LIGHT['accent']),
          'ico48': svg_png(v1_svg, 48), 'svg16': svg_png(v1_svg, 16), 'svg32': svg_png(v1_svg, 32),
          'tile': pm.square_svg(parts, pm.LIGHT['accent'], margin=0.0, ground=pm.LIGHT['ground'], scale=0.62)}
    v2_svg = pm.disc_svg(parts)
    v2 = {'ico16': pm.disc_png(pm.FAVICONS_DISC[16], 16), 'ico32': pm.disc_png(pm.FAVICONS_DISC[32], 32),
          'ico48': pm.disc_auto_png(parts, 48), 'svg16': svg_png(v2_svg, 16), 'svg32': svg_png(v2_svg, 32),
          'tile': pm.tile_svg(parts)}
    return v1, v2


def on(im, colour, pad=0):
    t = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), colour)
    t.alpha_composite(im, (pad, pad))
    return t


def tab(icon, colour, text_colour, scale):
    """A browser tab at 1x or 2x: icon, title, close cross."""
    w, h = 190 * scale, 30 * scale
    t = Image.new('RGBA', (w, h), colour)
    t.alpha_composite(icon, (10 * scale, (h - icon.height) // 2))
    d = ImageDraw.Draw(t)
    d.text((34 * scale, h // 2), 'Peter Stieg', fill=text_colour, font=font(False, 12 * scale), anchor='lm')
    x, y, r = w - 16 * scale, h // 2, 4 * scale
    d.line([(x - r, y - r), (x + r, y + r)], fill=text_colour, width=scale)
    d.line([(x - r, y + r), (x + r, y - r)], fill=text_colour, width=scale)
    return t


def nn(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def squircle_mask(size, radius_frac=0.2237):
    m = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=int(size * 4 * radius_frac), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def circle_mask(size):
    m = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    return m.resize((size, size), Image.LANCZOS)


def masked(im, mask):
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def sheet(F, M, path):
    v1, v2 = icons(F, M)
    W = 1520
    S = Image.new('RGBA', (W, 2800), SHEET)
    d = ImageDraw.Draw(S)
    x0 = 40
    d.text((x0, 32), 'Favicon v2 · paper PS on a bordeaux disc', fill=INK, font=font(True, 28))
    d.text((x0, 72), 'v1: the bare mark in bordeaux on transparent. v2: one version for light and dark, hinted by hand at 16 and 32 px.',
           fill=MUTED, font=font(False, 16))

    # ---- A: in the tab
    y = 120
    d.text((x0, y), 'In the tab', fill=INK, font=font(True, 20))
    y += 34
    cols = [('v1 · 1×', v1['svg16'], 1), ('v2 · 1×', v2['ico16'], 1), ('v1 · 2×', v1['svg32'], 2), ('v2 · 2×', v2['ico32'], 2)]
    xs = [x0 + 210, x0 + 420, x0 + 640, x0 + 1040]
    for (lab, _, _), x in zip(cols, xs):
        d.text((x, y), lab, fill=MUTED, font=font(True, 14))
    y += 24
    for name, bg, fg in TABS:
        d.text((x0, y + 20), name, fill=INK, font=font(False, 15), anchor='lm')
        for (lab, ic, k), x in zip(cols, xs):
            S.alpha_composite(tab(ic, bg, fg, k), (x, y))
        y += 70
    d.text((x0, y), 'v1 as Chrome and Firefox show it today (favicon.svg in a light OS scheme). v2 as head.html links it: the hand-hinted ICO, '
                    '16 px at 1×, 32 px at 2×.', fill=MUTED, font=font(False, 14))

    # ---- B: every size, 1x and 2x
    y += 46
    d.text((x0, y), 'Each size at 1× and 2× (2× = pixels doubled)', fill=INK, font=font(True, 20))
    y += 34
    sizes = [('ICO 16', 'ico16'), ('ICO 32', 'ico32'), ('ICO 48', 'ico48'), ('SVG at 16', 'svg16'), ('SVG at 32', 'svg32')]
    cx = [x0 + 210]
    for _, k in sizes[:-1]:
        s = v2[k].width
        cx.append(cx[-1] + s + 2 * s + 60)
    for (lab, _), x in zip(sizes, cx):
        d.text((x, y), lab, fill=MUTED, font=font(True, 14))
    y += 24
    for name, bg, fg in TABS:
        for ver, icset in (('v1', v1), ('v2', v2)):
            rowh = 0
            d.text((x0, y + 30), f'{ver} · {name}', fill=INK, font=font(False, 14), anchor='lm')
            for (lab, k), x in zip(sizes, cx):
                im = icset[k]
                a = on(im, bg, 6)
                b = on(nn(im, 2), bg, 6)
                S.alpha_composite(a, (x, y + (108 - a.height) // 2))
                S.alpha_composite(b, (x + a.width + 8, y + (108 - b.height) // 2))
            y += 112
        y += 6

    # ---- C: touch and app icons
    y += 20
    d.text((x0, y), 'Touch and app icons', fill=INK, font=font(True, 20))
    y += 34
    items = []
    for ver, icset in (('v1', v1), ('v2', v2)):
        t180 = svg_png(icset['tile'], 180, ss=4)
        t192 = svg_png(icset['tile'], 192, ss=4)
        t512 = svg_png(icset['tile'], 512, ss=2).resize((256, 256), Image.LANCZOS)
        guide = t512.copy()
        g = ImageDraw.Draw(guide)
        r = 256 * pm.SAFE
        g.ellipse([128 - r, 128 - r, 128 + r, 128 + r], outline=(90, 162, 255, 255), width=2)
        items.append((ver, [('apple-touch-icon 180, iOS mask', masked(t180, squircle_mask(180))),
                            ('icon-192, circle mask (Android)', masked(t192, circle_mask(192))),
                            ('icon-512 at ½, safe zone 80 %', guide)]))
    for ver, row in items:
        x = x0 + 210
        d.text((x0, y + 90), ver, fill=INK, font=font(True, 16), anchor='lm')
        for lab, im in row:
            S.alpha_composite(on(im, '#FFFFFF', 8), (x, y))
            d.text((x, y + im.height + 22), lab, fill=MUTED, font=font(False, 13))
            x += im.width + 60
        y += 300
    S = S.crop((0, 0, W, y + 10))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    S.convert('RGB').save(path)
    return path
