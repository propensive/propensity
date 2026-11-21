"""Recipes for Greek letters. Lowercase coordinates assume the x-height of 1024."""
from geom import BIG, Shape, stroke

ASCENDER_BAR = 1475   # top of the bar on ζ and ξ
TAIL_DEPTH = -332     # how far ζ ξ ς descend; μ, the font's one Greek letter, reaches -348
THIN = 75             # hairline weight of the round lowercase letters (top and bottom of c)
# Direction of the stroke where the bowl of ζ or ξ hands over to the tail: 14 degrees below
# level, so the bowl runs on into the tail instead of flattening along the baseline first.
TAIL_ENTRY = 346


def _hook(x, y):
    """Nodes that continue a stroke travelling east along the baseline at (x, y) into the
    tail shared by ζ, ξ and ς: down round a small bulge, ending in a tapered point like
    the tails of j and 3."""
    return [(x + 172, y - 142, 122, 270), (x - 110, TAIL_DEPTH, 14, 205)]


def final_sigma(c, c_adv):
    """c with its lower arm replaced by the tail."""
    # the underside of c is level between about x=600 and x=690, so cut there
    x_cut = 640
    lo, hi = c.ys(x_cut - 15)[:2]
    y = (lo + hi) / 2
    body = c.drop(x0=x_cut, y1=500)
    tail = stroke([(x_cut - 22, y, hi - lo, 0)] + _hook(x_cut - 22, y))
    return body | tail, c_adv - 60


def _top_bar(z, left, right, top=ASCENDER_BAR):
    """z's top bar with its left terminal, raised to ascender height, running from about
    `left` to `right`. Returns the bar, the height of its centre line and its thickness."""
    lo, hi = z.ys(520)[-2:]
    piece = z.keep(x1=560, y0=lo - 80)
    piece = piece.shift(left - piece.bounds[0], top - hi)
    return piece | Shape.rect(left + 460, top - (hi - lo), right, top), top - (hi - lo) / 2, hi - lo


def _hung(bar, yc, t, start, heading, nodes):
    """A stroke hung from the right end of a top bar, as on ζ and ξ. The stroke leaves the
    bar at `start` travelling along `heading`, and the bar is trimmed to the stroke's
    outer edge so the two meet in a sharp corner like the one on z."""
    import math
    a = math.radians(heading)
    dx, dy = math.cos(a), math.sin(a)
    x, y = start
    back = 2.5 * t
    body = stroke([(x - dx * back, y - dy * back, t, heading), (x, y, t, heading)] + nodes)
    body = body.keep(y1=yc + t / 2)
    # the edge of the stroke on the side away from the bar: travel direction turned left
    ex, ey = x - dy * t / 2, y + dx * t / 2
    line = lambda yy: ex + (yy - ey) * dx / dy  # noqa: E731
    lo, hi = yc - t / 2 - 2, yc + t / 2 + 5
    bar = bar - Shape.poly([(line(hi), hi), (line(lo), lo), (BIG, lo), (BIG, hi)])
    return bar | body


def zeta(z):
    bar, yc, t = _top_bar(z, 215, 800)
    shape = _hung(bar, yc, t, (690, yc), 214,
                  [(180, 590, 190, 270), (590, 20, THIN, TAIL_ENTRY)] + _hook(590, 20))
    shape = shape.shift(60 - shape.bounds[0], 0)
    return shape, shape.bounds[2] + 30


def xi(c):
    """Two bowls and the tail, with no bar: the upper bowl is the top half of c at a
    smaller size, so the letter begins with c's own terminal."""
    # c reduced, then thickened to put back the weight the reduction took out
    small = c.scale(0.555, 0.615).grow(16)
    belly = min(range(int(small.bounds[1]) + 80, int(small.bounds[3]) - 80, 2), key=lambda y: small.xs(y)[0])
    left, right = small.xs(belly)[:2]
    belly_y = 1165
    dx, dy = 193 - left, belly_y - belly
    x, w = (left + right) / 2 + dx, right - left
    top = small.keep(y0=belly).shift(dx, dy)
    upper = top | stroke([(x, belly_y + 12, w, 270), (x, belly_y, w, 270), (610, 884, 64, 0)])
    lower = stroke([(610, 880, 64, 180), (172, 450, 186, 270), (540, 20, THIN, TAIL_ENTRY)] + _hook(540, 20))
    shape = upper | lower
    shape = shape.shift(60 - shape.bounds[0], 0)
    return shape, shape.bounds[2] + 30


def beta(eszett, mu, adv):
    """ß with the stem carried below the baseline on μ's descender, and the lower bowl
    closed back onto the stem."""
    a, b = eszett.xs(400)[:2]
    # a plain stem from where ß's stem is still straight down to μ's descender, which is
    # taken from below the point where μ's own bowl leaves it
    stem = Shape.rect(a, 0, b, 400) | mu.keep(x1=b + 60, y1=8)
    body = eszett.drop(x1=b + 40, y1=395) | stem
    # the bowl's last stroke ends in the open, tapering; carry it on to the stem
    end = eszett.keep(x0=b + 60, y1=30).contours
    face = min(end, key=lambda c: c.bounds[0]).keep(x1=b + 170)
    x0, y0, _, y1 = face.bounds
    join = Shape.poly([(b - 8, y0 - 4), (b - 8, y1 + 8), (x0 + 12, y1), (x0 + 12, y0)])
    return body | join, adv + 20


# =============================================================================================
# The rest of the alphabet
# =============================================================================================

import math  # noqa: E402

import recipes as r  # noqa: E402
from recipes import CAP_HEIGHT, X_HEIGHT  # noqa: E402

ASCENDER = 1495       # top of l
DESCENDER = -348      # Greek stems descend as far as the font's own μ, not as far as p


def _line(p, q):
    (x0, y0), (x1, y1) = p, q
    return lambda y: x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def _descender(mu, x_left):
    """μ's descending stem below the baseline, moved so its straight left edge is at x_left."""
    a, b = mu.xs(-40)[:2]
    return mu.keep(x1=b + 60, y1=8).shift(x_left - a, 0), b - a


# ---- capitals -------------------------------------------------------------------------------

def delta_cap(m):
    s, adv = r.el(m)
    x0, _, x1, _ = s.bounds
    inset = 0.25 * m.sw
    return s | Shape.rect(x0 + inset, 0, x1 - inset, m.bottom_arm), adv


def theta_cap(m):
    O = m("O")
    lo, hi = m.hbar
    t = hi - lo
    cy = (O.bounds[1] + O.bounds[3]) / 2
    xs = O.xs(cy)
    return O | Shape.rect(xs[1] - 15, cy - t / 2, xs[2] + 15, cy + t / 2), m.adv("O")


def _t_bar(m):
    """T's bar on its own, with both hanging terminals."""
    T = m("T")
    a, b = T.xs(0.35 * m.h)[:2]
    under = T.ys(b + 40)[0]
    return T - Shape.rect(a - 40, -BIG, b + 40, under)


def xi_cap(m, narrow=0.92):
    bar = _t_bar(m)
    x0, _, x1, _ = bar.bounds
    cx, width = (x0 + x1) / 2, x1 - x0
    E = m("E")
    eb = E.xs(0.35 * m.h)[1]
    arm = E.keep(x0=eb, y0=0.4 * m.h, y1=0.66 * m.h)
    reach = 0.29 * width
    tip = arm.bounds[2]
    half = arm.keep(x0=tip - reach)
    mid_y = (half.bounds[1] + half.bounds[3]) / 2
    right = half.shift(cx + reach - tip, m.h / 2 - mid_y)
    shape = (bar | bar.flip_v(m.h / 2) | right | right.flip_h(cx)).scale(narrow, 1, ox=cx)
    lsb = 0.45 * m.lsb("H")
    shape = shape.shift(lsb - shape.bounds[0], 0)
    return shape, shape.bounds[2] + lsb


def sigma_cap(m):
    E = m("E")
    a, b = E.xs(0.35 * m.h)[:2]
    top_under = E.ys(b + 6)[-2]
    bottom_top = E.ys(b + 6)[1]
    xl = a - 0.1 * m.sw
    top = E.keep(x0=b + 1, y0=0.8 * m.h) | Shape.rect(xl, top_under, b + 20, m.h)
    bottom = E.keep(x0=b + 1, y1=0.2 * m.h) | Shape.rect(xl - 0.1 * m.sw, 0, b + 20, bottom_top)
    width = E.bounds[2] - xl
    ym = 0.515 * m.h
    xo = xl + 0.55 * width
    thick, thin = 1.03 * m.sw, 0.66 * m.sw          # horizontal thickness of the two diagonals
    xb = xl - 0.1 * m.sw
    upper_edge = _line((xl, m.h), (xo - thick, ym))
    lower_edge = _line((xb, 0), (xo - thin, ym))
    # the inner vertex is where the two inner edges cross
    k1 = (xo - thick - xl) / (ym - m.h)
    k2 = (xo - thin - xb) / ym
    yi = (xb - xl + k1 * m.h) / (k1 - k2)
    chevron = Shape.poly([(xl, m.h), (xl + thick, m.h), (xo, ym), (xb + thin, 0), (xb, 0), (lower_edge(yi), yi)])
    shape = top | bottom | chevron
    lsb = 0.5 * m.lsb("H")
    shape = shape.shift(lsb - shape.bounds[0], 0)
    return shape, shape.bounds[2] + m.rsb("E")


def psi_cap(m, lift=0.3, squash=0.85, narrow=0.9):
    """U raised off the baseline as a cup, on a full-height stem."""
    U, I = m("U"), m("I")
    a, b, c, d = U.xs(0.6 * m.h)[:4]
    y_cut, y_top = 0.42 * m.h, 0.72 * m.h
    low = U.keep(y1=y_cut)
    bottom = low.bounds[1]
    low = low.scale(1, squash, oy=y_cut)
    dy = lift * m.h - (y_cut - (y_cut - bottom) * squash)
    cup = (low.shift(0, dy) | Shape.rect(a, y_cut + dy - 1, b, y_top + 1)
           | Shape.rect(c, y_cut + dy - 1, d, y_top + 1) | U.keep(y0=y_top))
    cx = (b + c) / 2
    cup = cup.warp(lambda x, y: (cx + (x - cx) * narrow if b < x < c else (x + (1 - narrow) * (c - b) / 2 if x <= b else x - (1 - narrow) * (c - b) / 2), y))
    il, ir = I.xs(0.5 * m.h)[:2]
    shape = cup | I.shift(cx - (il + ir) / 2, 0)
    lsb = 0.75 * m.lsb("H")
    shape = shape.shift(lsb - shape.bounds[0], 0)
    return shape, shape.bounds[2] + 0.75 * m.rsb("H")


def omega_cap(m):
    """O with the foot of the bowl taken out, its two ends landing on level feet."""
    O, L = m("O"), m("L")
    t = m.bottom_arm
    x0, _, x1, _ = O.bounds
    cx = (x0 + x1) / 2
    half_gap = 0.15 * (x1 - x0)
    # take out the foot of the bowl between the two feet, and everything below the feet's line
    top = O.keep(y0=0.6 * t) - Shape.rect(cx - half_gap, -BIG, cx + half_gap, 0.16 * m.h)
    tip = L.keep(x0=L.bounds[2] - 1.3 * m.sw, y1=0.25 * m.h)      # the flared end of L's arm
    out_end = x0 + 0.55 * m.sw
    tip = tip.flip_h().shift(out_end - tip.bounds[0], 0)
    foot = tip | Shape.rect(tip.bounds[2] - 10, 0, cx - half_gap, t)
    return top | foot | foot.flip_h(cx), m.adv("O")


# ---- lowercase ------------------------------------------------------------------------------

def alpha(q, d, adv):
    """q with its descender replaced by the foot of d."""
    qs, ds = q.xs(500)[2], d.xs(500)[2]
    foot = d.shift(qs - ds, 0).keep(x0=qs + 0.5, y1=300)
    return q.keep(y0=300) | q.keep(x1=qs + 1, y0=-60, y1=300) | foot, adv


def gamma(v, mu):
    """v on a short thin descender."""
    foot, w = _descender(mu, 0)
    lo = v.xs(0)
    cx = (lo[0] + lo[1]) / 2
    k = 0.64
    foot = foot.scale(k, 1, ox=w / 2).shift(cx - w / 2, 0)
    return v | foot | Shape.rect(cx - k * w / 2, 0, cx + k * w / 2, 58)


def delta(eth):
    """ð without its crossbar."""
    # the bar is straight and crosses the ascender; these are its two halves, corner to corner
    upper = [(645, 1364), (868, 1509), (899, 1468), (690, 1331)]
    lower = [(618, 1284), (395, 1137), (362, 1180), (580, 1321)]

    def beyond(quad):
        (ax, ay), (bx, by), (cx_, cy_), (dx, dy) = quad
        # push the two far corners outward so nothing of the bar's end is left
        ex, ey = (bx - ax) * 0.2, (by - ay) * 0.2
        return [(ax, ay), (bx + ex, by + ey), (cx_ + ex, cy_ + ey), (dx, dy)]

    return eth - Shape.poly(beyond(upper)) - Shape.poly(beyond(lower))


def epsilon(ze, ze_adv):
    """The Cyrillic з turned to face the other way."""
    x0, _, x1, _ = ze.bounds
    s = ze.flip_h((x0 + x1) / 2)
    return s.shift(ze_adv - x1 - x0 + 10, 0), ze_adv


def eta(n, mu):
    """n with its right stem carried below the baseline."""
    c, d = n.xs(500)[2:4]
    foot, _ = _descender(mu, c)
    return n.drop(x0=c - 60, y1=330) | Shape.rect(c, 0, d, 335) | foot


def theta(o):
    ox0, oy0, ox1, oy1 = o.bounds
    w = 0.8 * (ox1 - ox0)
    top = ASCENDER + (oy1 - X_HEIGHT)
    bowl = r.ring(o, width=w, height=top - oy0, cx=ox0 + w / 2, cy=(top + oy0) / 2)
    cy = (top + oy0) / 2
    xs = bowl.xs(cy)
    return bowl | Shape.rect(xs[1] - 12, cy - THIN / 2, xs[2] + 12, cy + THIN / 2), w + 2 * ox0


def iota(t, dotlessi):
    """The top of ı on the curved foot of t."""
    ts, i_s = t.xs(600)[0], dotlessi.xs(600)[0]
    shape = t.keep(y1=700) | dotlessi.keep(y0=700).shift(ts - i_s, 0)
    lsb = dotlessi.bounds[0]
    shape = shape.shift(lsb - shape.keep(y0=700).bounds[0], 0)
    return shape, shape.bounds[2] + 55


def lamda(small):
    """The pointed л with its heavy right leg carried up to ascender height."""
    s, adv = r.el(small)
    ya, yb = 0.45 * small.h, 0.72 * small.h
    xa, xb = s.xs(ya), s.xs(yb)
    inner = _line((xa[2], ya), (xb[2], yb))
    outer = _line((xa[3], ya), (xb[3], yb))
    lo = 0.7 * small.h
    arm = Shape.poly([(inner(lo), lo), (inner(ASCENDER), ASCENDER), (outer(ASCENDER), ASCENDER), (outer(lo), lo)])
    return s | arm, adv


def rho(o, mu):
    """o with a descender dropped from its left side."""
    x0 = o.bounds[0]
    y_ext = min(range(300, 800, 5), key=lambda y: o.xs(y)[0])
    foot, w = _descender(mu, x0)
    return o | Shape.rect(x0, 0, x0 + w, y_ext) | foot


def sigma(o, small):
    """o with its top carried out to the right as a bar, ended like the bar of τ."""
    T = small("T")
    a, b = T.xs(0.4 * small.h)[:2]
    arm = T.keep(x0=b + 30, y0=0.7 * small.h)
    lo, hi = T.ys(b + 60)[-2:]
    ox0, _, ox1, oy1 = o.bounds
    lift = oy1 - 6 - hi
    right = ox1 + 0.16 * (ox1 - ox0)
    arm = arm.shift(right - arm.bounds[2], lift)
    start = (ox0 + ox1) / 2
    shape = o | arm | Shape.rect(start, lo + lift, arm.bounds[0] + 20, hi + lift)
    return shape, right + 45


def phi(o, l, mu, widen=1.17):
    ox0, oy0, ox1, oy1 = o.bounds
    w = widen * (ox1 - ox0)
    cx = ox0 + w / 2
    bowl = r.ring(o, width=w, cx=cx)
    ll, lr = l.xs(600)[:2]
    foot, _ = _descender(mu, cx - (lr - ll) / 2)
    stem = l.keep(y0=600).shift(cx - (ll + lr) / 2, 0) | Shape.rect(cx - (lr - ll) / 2, 0, cx + (lr - ll) / 2, 610) | foot
    return bowl | stem, w + 2 * ox0


def chi(x):
    """x drawn down to the descender line."""
    return x.scale(1, (X_HEIGHT - DESCENDER) / X_HEIGHT, oy=X_HEIGHT)


def psi(small, l, mu):
    """The small-capital U as a cup on a stem that rises and descends."""
    U = small("U")
    a, b, c, d = U.xs(0.6 * small.h)[:4]
    cx = (b + c) / 2
    ll, lr = l.xs(600)[:2]
    half = (lr - ll) / 2
    foot, _ = _descender(mu, cx - half)
    stem = l.keep(y0=600).shift(cx - (ll + lr) / 2, 0) | Shape.rect(cx - half, 0, cx + half, 610) | foot
    return U | stem, small.adv("U")


def omega(m):
    """m turned upside down, with the middle stem cut short."""
    h = X_HEIGHT
    s = m.rotate180()
    s = s.shift(0, -s.bounds[1] - (m.bounds[3] - h))
    xs = s.xs(0.7 * h)
    mx0, mx1 = xs[2], xs[3]
    top = 0.64 * h
    end = s.keep(x0=mx0 - 40, x1=mx1 + 40, y0=0.8 * h)
    shape = s.drop(x0=mx0 - 40, x1=mx1 + 40, y0=0.5 * h) | Shape.rect(mx0, 0.3 * h, mx1, top - 0.19 * h) | end.shift(0, top - h)
    return shape


# ---- accents --------------------------------------------------------------------------------

def tonos(acute, scale=0.68, turn=38):
    """The acute made shorter and steeper, as the Greek accent is."""
    x0, y0, x1, y1 = acute.bounds
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    s = acute.scale(scale, scale, ox=cx, oy=cy).rotate(turn, cx, cy)
    b = s.bounds
    return s.shift(512 - (b[0] + b[2]) / 2, 1170 - b[1])


# =============================================================================================
# The Greek glyph list
# =============================================================================================

SAME_UPPER = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
              "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X"}
UPPER = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
LOWER = "αβγδεζηθικλμνξοπρσςτυφχψω"
TONOS_UPPER = {"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω"}
TONOS_LOWER = {"ά": "α", "έ": "ε", "ή": "η", "ί": "ι", "ό": "ο", "ύ": "υ", "ώ": "ω"}
DIALYTIKA_LOWER = {"ϊ": "ι", "ϋ": "υ"}
DIALYTIKA_TONOS_LOWER = {"ΐ": "ι", "ΰ": "υ"}
ALL = (UPPER + LOWER + "".join(TONOS_UPPER) + "".join(TONOS_LOWER) + "".join(DIALYTIKA_LOWER)
       + "".join(DIALYTIKA_TONOS_LOWER) + "ΪΫ" + "΄΅·;")


def uni(ch):
    return "uni%04X" % ord(ch)


def build(font, cap, small, specs):
    """Specs for every Greek glyph. `specs` are the glyphs already made (the Cyrillic ones),
    some of which Greek reuses."""
    gs, hmtx = font.getGlyphSet(), font["hmtx"]
    original = set(font.getGlyphOrder())
    lat = lambda n: Shape.glyph(gs, n)  # noqa: E731
    out = []

    def find(name):
        return next(s for s in specs + out if s["name"] == name)

    def outline(name):
        if name in original:
            return lat(name)
        spec = find(name)
        if spec["kind"] == "shape":
            return spec["shape"]
        parts = [outline(base).shift(dx, dy) for base, dx, dy in spec["parts"]]
        return Shape.join(parts)

    def advance(name):
        return hmtx[name][0] if name in original else find(name)["adv"]

    def shape(ch, s, adv, edges=(None, None)):
        out.append({"name": uni(ch), "kind": "shape", "shape": s, "adv": adv, "code": ord(ch),
                    "char": ch, "smooth": True, "edges": edges, "script": "grek"})

    def comp(ch, parts, adv, edges=(None, None), own_metrics=False):
        out.append({"name": uni(ch), "kind": "comp", "parts": parts, "adv": adv, "code": ord(ch),
                    "char": ch, "edges": edges, "own_metrics": own_metrics, "script": "grek"})

    def same(ch, name, edges):
        comp(ch, [(name, 0, 0)], advance(name), edges)

    # ---- capitals ----
    for ch, base in SAME_UPPER.items():
        same(ch, base, (base, base))
    same("Γ", "uni0413", ("H", "T"))
    same("Π", "uni041F", ("H", "H"))
    same("Φ", "uni0424", ("O", "O"))
    same("Λ", "uni041B.ss01", ("A", "A"))
    shape("Δ", *delta_cap(cap), edges=("A", "A"))
    shape("Θ", *theta_cap(cap), edges=("O", "O"))
    shape("Ξ", *xi_cap(cap))
    shape("Σ", *sigma_cap(cap), edges=(None, "E"))
    shape("Ψ", *psi_cap(cap))
    shape("Ω", *omega_cap(cap))

    # ---- lowercase ----
    mu, o, l = lat("mu"), lat("o"), lat("l")
    shape("α", *alpha(lat("q"), lat("d"), hmtx["q"][0]), edges=("o", "d"))
    shape("β", *beta(lat("germandbls"), mu, hmtx["germandbls"][0]), edges=(None, "o"))
    shape("γ", gamma(lat("v"), mu), hmtx["v"][0], edges=("v", "v"))
    shape("δ", delta(lat("eth")), hmtx["eth"][0], edges=("o", "o"))
    ze = find("uni0437")
    shape("ε", *epsilon(ze["shape"], ze["adv"]), edges=(None, "c"))
    shape("ζ", *zeta(lat("z")))
    shape("η", eta(lat("n"), mu), hmtx["n"][0], edges=("n", "n"))
    shape("θ", *theta(o), edges=("o", "o"))
    shape("ι", *iota(lat("t"), lat("dotlessi")))
    same("κ", "uni043A", ("n", "k"))
    shape("λ", *lamda(small))
    same("ν", "v", ("v", "v"))
    shape("ξ", *xi(lat("c")))
    same("ο", "o", ("o", "o"))
    same("π", "uni043F", ("n", "n"))
    shape("ρ", rho(o, mu), hmtx["o"][0], edges=("p", "o"))
    shape("σ", *sigma(o, small), edges=("o", None))
    shape("ς", *final_sigma(lat("c"), hmtx["c"][0]), edges=("c", None))
    same("τ", "uni0442", (None, "r"))
    shape("υ", small("U"), small.adv("U"), edges=("u", "u"))
    shape("φ", *phi(o, l, mu), edges=("o", "o"))
    shape("χ", chi(lat("x")), hmtx["x"][0], edges=("x", "x"))
    shape("ψ", *psi(small, l, mu))
    shape("ω", omega(lat("m")), hmtx["m"][0])

    # ---- accents ----
    accent = tonos(lat("acute"))
    shape("΄", accent, 1024)
    shape("΅", lat("dieresis") | accent.shift(0, 40), 1024)

    def over(base_ch):
        """Centre of the top of a lowercase letter, where an accent should sit."""
        b = outline(uni(base_ch)).keep(y0=0.7 * X_HEIGHT, y1=X_HEIGHT + 40).bounds
        return (b[0] + b[2]) / 2

    for table, mark in ((TONOS_LOWER, "΄"), (DIALYTIKA_LOWER, None), (DIALYTIKA_TONOS_LOWER, "΅")):
        for ch, base_ch in table.items():
            base = uni(base_ch) if base_ch != "μ" else "mu"
            name = uni(mark) if mark else "dieresis"
            comp(ch, [(base, 0, 0), (name, over(base_ch) - 512, 0)], advance(base), find(base)["edges"])

    # a capital carries its tonos at the upper left, and moves right to make room for it
    t0, _, t1, t_top = accent.bounds
    for ch, base_ch in TONOS_UPPER.items():
        base = uni(base_ch)
        ink = outline(base)
        left = min(ink.xs(y)[0] for y in range(1150, 1430, 20))
        gap, lsb = 45, 40
        move = max(0, lsb + (t1 - t0) + gap - left)
        comp(ch, [(base, move, 0), (uni("΄"), move + left - gap - t1, CAP_HEIGHT + 16 - t_top)],
             advance(base) + move, (None, find(base)["edges"][1]), own_metrics=True)
    same("Ϊ", "Idieresis", ("I", "I"))
    same("Ϋ", "Ydieresis", ("Y", "Y"))

    # ---- punctuation ----
    comp("·", [("periodcentered", 0, 190)], hmtx["periodcentered"][0])   # ano teleia, a raised dot
    same(";", "semicolon", (None, None))                                   # Greek question mark
    return out
