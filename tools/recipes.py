"""Recipes that construct Cyrillic glyphs from Marcellus and Marcellus SC outlines.

Each recipe takes a Master (a set of source letters at one height) and returns
(Shape, advance). Running a recipe on CAP gives the capital; on SMALL, the lowercase.
"""
import math

from geom import Shape

X_HEIGHT = 1024
CAP_HEIGHT = 1434
SC_HEIGHT = 1075
# Weight of the curved left stroke of Л and Д, as a fraction of the stem weight.
LEG_WEIGHT = 0.85


class Master:
    def __init__(self, font, lower, yscale, height):
        self.font = font
        self.gs = font.getGlyphSet()
        self.lower = lower
        self.yscale = yscale
        self.h = height
        self._cache = {}

    def name(self, ch):
        return ch.lower() if self.lower and len(ch) == 1 else ch

    def __call__(self, ch):
        if ch not in self._cache:
            s = Shape.glyph(self.gs, self.name(ch))
            if self.yscale != 1:
                s = s.scale(1, self.yscale)
            self._cache[ch] = s
        return self._cache[ch]

    def adv(self, ch):
        return self.font["hmtx"][self.name(ch)][0]

    def rsb(self, ch):
        return self.adv(ch) - self(ch).bounds[2]

    def lsb(self, ch):
        return self(ch).bounds[0]

    # ---- measurements -------------------------------------------------------------------

    @property
    def stems(self):
        """Straight edges of H's two stems: (a, b, c, d)."""
        return tuple(self("H").xs(0.35 * self.h)[:4])

    @property
    def sw(self):
        a, b, _, _ = self.stems
        return b - a

    @property
    def hbar(self):
        a, b, c, d = self.stems
        lo, hi = self("H").ys((b + c) / 2)[:2]
        return lo, hi

    @property
    def top_arm(self):
        """Underside of F's top arm where it leaves the stem."""
        F = self("F")
        b = F.xs(0.35 * self.h)[1]
        return F.ys(b + 2)[-2]

    @property
    def bottom_arm(self):
        """Top of L's arm where it leaves the stem."""
        L = self("L")
        b = L.xs(0.35 * self.h)[1]
        return L.ys(b + 6)[1]

    @property
    def depth(self):
        """How far tails on Ц, Щ, Д descend."""
        return round(0.15 * self.h + 60)


# ---- shared parts -----------------------------------------------------------------------

def tick(m, length, factor=0.6):
    """A short thin stroke, centred on x=0, flared free end at y=0, cut end at y=length."""
    I = m("I")
    x0, _, x1, _ = I.bounds
    cx = (x0 + x1) / 2
    return I.keep(y1=length).scale(factor, 1, ox=cx).shift(-cx, 0)


def tail(m, d):
    """Baseline bar extension and descender for Ц, Щ: attaches right of a stem whose
    straight outer edge is x=d. Returns (shape, right extent)."""
    t = m.bottom_arm
    xe = d + 0.82 * m.sw
    tk = tick(m, m.depth + t)
    w = tk.keep(y0=m.depth + t - 2).bounds
    half = (w[2] - w[0]) / 2
    tk = tk.shift(xe - half, -m.depth)
    bar = Shape.rect(d - 30, 0, xe - half, t)
    return bar | tk, xe


def ring(O, width=None, height=None, cx=None, cy=None):
    """Resize a round letter (outer contour plus one counter) keeping its stroke weights."""
    cs = sorted(O.contours, key=lambda c: -(c.bounds[2] - c.bounds[0]))
    outer, inner = cs[0], cs[1]
    ox0, oy0, ox1, oy1 = outer.bounds
    ix0, iy0, ix1, iy1 = inner.bounds
    width = (ox1 - ox0) if width is None else width
    height = (oy1 - oy0) if height is None else height
    cx = (ox0 + ox1) / 2 if cx is None else cx
    cy = (oy0 + oy1) / 2 if cy is None else cy
    nx0, nx1 = cx - width / 2, cx + width / 2
    ny0, ny1 = cy - height / 2, cy + height / 2

    def fit(shape, src, dst):
        sx = (dst[2] - dst[0]) / (src[2] - src[0])
        sy = (dst[3] - dst[1]) / (src[3] - src[1])
        return shape.transform(sx, 0, 0, sy, dst[0] - sx * src[0], dst[1] - sy * src[1])

    new_outer = fit(outer, outer.bounds, (nx0, ny0, nx1, ny1))
    new_inner = fit(inner, inner.bounds,
                    (nx0 + (ix0 - ox0), ny0 + (iy0 - oy0), nx1 - (ox1 - ix1), ny1 - (oy1 - iy1)))
    return new_outer - new_inner


def copy(letter):
    def recipe(m):
        return m(letter), m.adv(letter)
    return recipe


# ---- Г Ґ П Ц Ш Щ ------------------------------------------------------------------------

def ge(m):
    F = m("F")
    b = F.xs(0.35 * m.h)[1]
    return F.drop(x0=b, y0=0.38 * m.h, y1=0.8 * m.h), m.adv("F")


def ghe_upturn(m):
    s, adv = ge(m)
    tip = s.bounds[2]
    end = s.keep(x0=tip - 0.3 * m.sw, y0=0.8 * m.h)
    y0 = end.bounds[1]
    x_s = end.xs(y0 + 1)[0]
    I = m("I")
    x0, _, x1, _ = I.bounds
    cx = (x0 + x1) / 2
    top = m.h + 0.15 * m.h
    width = 0.62 * (I.xs(0.3 * m.h)[1] - I.xs(0.3 * m.h)[0])
    yl = s.ys(tip - width)[-2]
    length = top - yl
    half = I.keep(x1=cx, y1=length).scale(1.24, 1, ox=cx)
    tk = half.flip_v(length / 2).shift(tip - cx, yl)
    fill = Shape.rect(x_s, y0, tip, yl + 1)
    return s | tk | fill, adv + 10


def _corner_stem(m, top):
    """Left stem with a square outer corner at the top (from F) or the bottom (from L);
    the other end keeps its flare. Returns (shape, x of the straight inner edge)."""
    if top:
        s, _ = ge(m)
        b = m("F").xs(0.35 * m.h)[1]
        return s.drop(x0=b + 1, y0=0.7 * m.h).keep(y1=m.h), b
    L = m("L")
    b = L.xs(m.bottom_arm + 20)[1]
    return L.drop(x0=b + 1, y1=0.3 * m.h).keep(y0=0), b


def pe(m, k=1.0):
    a, b, c, d = m.stems
    left, bl = _corner_stem(m, top=True)
    cx = (a + d) / 2 - (1 - k) * (c - b) / 2
    right = left.flip_h(cx)
    bar = Shape.rect(bl - 20, m.top_arm, 2 * cx - bl + 20, m.h)
    return left | right | bar, m.adv("H") - (1 - k) * (c - b)


def tse(m):
    a, b, c, d = m.stems
    left, bl = _corner_stem(m, top=False)
    cx = (a + d) / 2
    right = left.flip_h(cx)
    bar = Shape.rect(bl - 20, 0, 2 * cx - bl + 20, m.bottom_arm)
    tl, xe = tail(m, 2 * cx - a)
    return left | right | bar | tl, xe + 0.28 * m.rsb("H")


def _sha(m):
    a, b, c, d = m.stems
    left, bl = _corner_stem(m, top=False)
    counter = 0.70 * (c - b)
    mid_l = bl + counter
    mid_r = mid_l + m.sw
    cx = (mid_l + mid_r) / 2
    I = m("I")
    ix0, _, ix1, _ = I.bounds
    il, ir = I.xs(0.5 * m.h)[:2]
    mid = I.keep(y0=0.5 * m.h).shift(mid_l - il, 0) | Shape.rect(mid_l, 0, mid_r, 0.5 * m.h + 1)
    right = left.flip_h(cx)
    bar = Shape.rect(bl - 20, 0, 2 * cx - bl + 20, m.bottom_arm)
    return left | mid | right | bar, 2 * cx - a


def sha(m):
    s, d = _sha(m)
    return s, s.bounds[2] + m.rsb("H")


def shcha(m):
    s, d = _sha(m)
    tl, xe = tail(m, d)
    return s | tl, xe + 0.28 * m.rsb("H")


# ---- И ----------------------------------------------------------------------------------

def _diagonal(x0, y0, x1, y1, perp, steps=30):
    """Parallelogram from the left edge x0 (bottom at y0) to the right edge x1 (top at y1)
    whose stroke has perpendicular thickness `perp`; returns the vertical thickness."""
    tv = perp
    for _ in range(steps):
        theta = math.atan2((y1 - tv) - y0, x1 - x0)
        tv = perp / math.cos(theta)
    return tv


def i_cy(m):
    a, b, c, d = m.stems
    H = m("H")
    body = H.drop(x0=b, x1=c, y0=0.38 * m.h, y1=0.65 * m.h)
    perp = 0.62 * m.sw
    tv = _diagonal(b, 0, c, m.h, perp)
    slope = (m.h - tv) / (c - b)
    e = 0.3 * m.sw
    diag = Shape.poly([(b - e, -slope * e), (b - e, -slope * e + tv),
                       (c + e, m.h - tv + slope * e + tv), (c + e, m.h - tv + slope * e)])
    diag = diag.keep(y0=0, y1=m.h)
    return body | diag, m.adv("H")


# ---- Л Д (pointed, ss01) ----------------------------------------------------------------

def _line(p, q):
    (x0, y0), (x1, y1) = p, q
    return lambda y: x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def el(m):
    A = m("A")
    cx = sum(A.bounds[::2]) / 2
    ys = A.ys(cx)
    bar_lo, bar_hi = ys[0], ys[1]
    y_a, y_b = bar_lo - 0.04 * m.h, bar_hi + 0.04 * m.h
    xa, xb = A.xs(y_a), A.xs(y_b)
    left = _line((xa[1], y_a), (xb[1], y_b))
    right = _line((xa[2], y_a), (xb[2], y_b))
    lo, hi = bar_lo - 6, bar_hi + 6
    cut = Shape.poly([(left(lo), lo), (left(hi), hi), (right(hi), hi), (right(lo), lo)])
    return A - cut, m.adv("A")


def de(m):
    s, adv = el(m)
    t = m.bottom_arm
    x0, _, x1, _ = s.bounds
    out = 0.16 * m.sw
    left_edge, right_edge = x0 - out, x1 + out
    bar = Shape.rect(left_edge, 0, right_edge, t)
    tk = tick(m, m.depth + t)
    w = tk.keep(y0=m.depth + t - 2).bounds
    half = (w[2] - w[0]) / 2
    feet = tk.shift(left_edge + half, -m.depth) | tk.shift(right_edge - half, -m.depth)
    shape = s | bar | feet
    lsb = 0.3 * m.lsb("H")
    dx = lsb - shape.bounds[0]
    shape = shape.shift(dx, 0)
    return shape, shape.bounds[2] + lsb


# ---- Ж ----------------------------------------------------------------------------------

def zhe(m, narrow=0.8):
    K = m("K")
    b = K.xs(0.3 * m.h)[1]
    arms = K.keep(x0=b)
    span = arms.ys(b + 2)
    y_v = sum(span) / len(span) + 0.013 * m.h
    # x-scaling thins a diagonal and shearing thickens it; mixing the two narrows the
    # arms to `narrow` of their reach while holding the stroke weight
    sx = 0.90
    slope = (arms.bounds[2] - b) / (m.h - y_v)
    shear = (sx - narrow) * slope * 0.92

    def fold(x, y):
        return b + sx * (x - b) - shear * abs(y - y_v), y

    arms = arms.warp(fold).keep(y0=0, y1=m.h)
    I = m("I")
    il, ir = I.xs(0.5 * m.h)[:2]
    overlap = 0.11 * m.sw
    reach = arms.bounds[2] - b - overlap
    lsb = 12
    stem_l = lsb + reach
    stem = I.shift(stem_l - il, 0)
    stem_r = stem_l + (ir - il)
    right = arms.shift(stem_r - b - overlap, 0)
    left = right.flip_h((stem_l + stem_r) / 2)
    shape = left | stem | right
    return shape, shape.bounds[2] + lsb


# ---- Э Є --------------------------------------------------------------------------------

def ye(m):
    C, E = m("C"), m("E")
    b = E.xs(0.35 * m.h)[1]
    arm = E.keep(x0=b, y0=0.4 * m.h, y1=0.66 * m.h)
    inner = C.xs(0.5 * m.h)[1]
    arm = arm.shift(inner - 0.2 * m.sw - b, 0)
    return C | arm, m.adv("C")


def e_rev(m):
    s, adv = ye(m)
    return s.flip_h(adv / 2), adv


# ---- Ю ----------------------------------------------------------------------------------

def yu(m, k=0.8):
    a, b, c, d = m.stems
    I, O = m("I"), m("O")
    il, ir = I.xs(0.5 * m.h)[:2]
    stem = I.shift(a - il, 0)
    ox0, _, ox1, _ = O.bounds
    w = k * (ox1 - ox0)
    gap = 1.25 * m.sw
    left = b + gap
    bowl = ring(O, width=w, cx=left + w / 2)
    lo, hi = m.hbar
    thick = bowl.xs(0.5 * m.h)[1] - bowl.xs(0.5 * m.h)[0]
    bar = Shape.rect(b - 20, lo, left + 0.6 * thick, hi)
    return stem | bar | bowl, left + w + m.lsb("O")


# ---- Я ----------------------------------------------------------------------------------

def ya(m):
    R = m("R")
    adv = m.adv("R")
    s = R.flip_h(adv / 2)
    shift = 0.25 * m.lsb("H")
    return s.shift(shift, 0), adv + shift


# ---- Ь Ъ Ы Б ----------------------------------------------------------------------------

def soft(m):
    P = m("P")
    s = P.flip_v(m.h / 2)
    return s, m.adv("P") + 0.15 * m.lsb("H")


def hard(m):
    s, adv = soft(m)
    T = m("T")
    a, b = s.xs(0.75 * m.h)[:2]
    reach = 1.55 * m.sw
    flag = T.keep(x1=reach + 0.5 * m.sw, y0=0.75 * m.h, y1=m.h + 0.01 * m.h)
    flag = flag.shift(a - reach, 0)
    shape = s | flag
    dx = 0.3 * m.lsb("H") - shape.bounds[0]
    return shape.shift(dx, 0), adv + dx


def yery(m):
    s, adv = soft(m)
    I = m("I")
    gap = 1.0 * m.sw
    x = s.bounds[2] + gap
    stem = I.shift(x - I.bounds[0], 0)
    return s | stem, x + (I.bounds[2] - I.bounds[0]) + m.rsb("I")


def be(m):
    s, adv = soft(m)
    g, _ = ge(m)
    y = 0.68 * m.h
    return s.keep(y1=y) | g.keep(y0=y - 1), adv


# ---- Ч ----------------------------------------------------------------------------------

def che(m, lift=0.345, squash=0.8, counter=0.86):
    U, I = m("U"), m("I")
    a, b = U.xs(0.6 * m.h)[:2]
    _, hb, hc, _ = m.stems
    y_cut = 0.42 * m.h
    y_top = 0.72 * m.h
    low = U.keep(y1=y_cut)
    bottom = low.bounds[1]
    low = low.scale(1, squash, oy=y_cut)
    new_bottom = y_cut - (y_cut - bottom) * squash
    dy = lift * m.h - new_bottom
    low = low.shift(0, dy)
    hook = low | Shape.rect(a, y_cut + dy - 1, b, y_top + 1) | U.keep(y0=y_top)
    il, ir = I.xs(0.5 * m.h)[:2]
    stem_l = b + counter * (hc - hb)
    stem = I.shift(stem_l - il, 0)
    hook = hook.keep(x1=stem_l + (ir - il) / 2)
    shape = hook | stem
    return shape, shape.bounds[2] + m.rsb("H")


# ---- У (capital) ------------------------------------------------------------------------

def u_cap(m, narrow=0.93):
    X = m("X")
    y_a, y_b = 0.15 * m.h, 0.33 * m.h
    edge = _line((X.xs(y_a)[1], y_a), (X.xs(y_b)[1], y_b))
    top = 0.60 * m.h
    cut = Shape.poly([(edge(-50), -50), (edge(top), top), (20000, top), (20000, -50)])
    s = (X - cut).scale(narrow, 1)
    lsb = 0.2 * m.lsb("H")
    s = s.shift(lsb - s.bounds[0], 0)
    return s, s.bounds[2] + lsb


# ---- Ф (capital) ------------------------------------------------------------------------

def ef_cap(m):
    O, I = m("O"), m("I")
    ox0, oy0, ox1, oy1 = O.bounds
    w = 0.9 * (ox1 - ox0)
    hgt = 0.6 * (oy1 - oy0)
    lsb = m.lsb("O")
    cx = lsb + w / 2
    bowl = ring(O, width=w, height=hgt, cx=cx, cy=0.5 * m.h)
    il, ir = I.xs(0.5 * m.h)[:2]
    stem = I.shift(cx - (il + ir) / 2, 0)
    return bowl | stem, w + 2 * lsb


# ---- З ----------------------------------------------------------------------------------

def ze(m, three, weight=0.0):
    """From the figure three, squashed to sit between baseline and letter height."""
    x0, y0, x1, y1 = three.bounds
    over = 0.012 * m.h
    target = m.h + 2 * over - 2 * weight
    sy = target / (y1 - y0)
    sx = 1.0 if not m.lower else 0.80
    s = three.scale(sx, sy, ox=x0, oy=y0).shift(0, -over + weight - y0)
    if weight:
        s = s.grow(weight)
    lsb = 0.45 * m.lsb("O") if not m.lower else 0.5 * m.lsb("O")
    s = s.shift(lsb - s.bounds[0], 0)
    return s, s.bounds[2] + 0.75 * m.lsb("O")


# ---- Л Д (flat-topped, the default forms) -------------------------------------------------

def _curved_leg(m, J, lean, into_bar, weight):
    """The left stroke of Л and Д: J narrowed to `weight` of the stem weight, so its tail
    gives a gentle curve out to the left ending in the font's own tapered terminal.

    For Л the tapered tip rests on the baseline. For Д the tail runs into the baseline bar
    while it still has some weight, and is cut there. Returned with the top outer corner
    at x=0, together with the stroke's width at the top."""
    k = m.h / CAP_HEIGHT
    jl, jr = J.xs(0.6 * CAP_HEIGHT)[:2]
    leg = J.scale(weight * m.sw / (jr - jl), k, ox=jl, oy=0)
    if into_bar:
        dy = m.bottom_arm + 200 * k
    else:
        dy = -leg.bounds[1] - 0.008 * m.h
    leg = leg.shift(0, dy).skew(lean, oy=0)
    leg = leg.keep(y0=0, y1=m.h) if into_bar else leg.keep(y1=m.h)
    top = leg.xs(m.h - 1)
    return leg.shift(-top[0], 0), top[1] - top[0]


def _flat(m, J, lean, counter, footed, weight):
    a, b, c, d = m.stems
    leg, leg_w = _curved_leg(m, J, lean, into_bar=footed, weight=weight)
    stem0, bl = _corner_stem(m, top=True)
    c2 = leg_w + counter * (c - b)
    right = stem0.flip_h((c2 + bl) / 2)
    bar = Shape.rect(leg_w * 0.5, m.top_arm, c2 + 20, m.h)
    shape = leg | bar | right
    if footed:
        t = m.bottom_arm
        out = 0.5 * m.sw
        x0 = shape.keep(y1=t).bounds[0]
        left_edge, right_edge = x0 - out * 0.9, c2 + m.sw + out
        tk = tick(m, m.depth + t)
        w = tk.keep(y0=m.depth + t - 2).bounds
        half = (w[2] - w[0]) / 2
        shape = (shape | Shape.rect(left_edge, 0, right_edge, t)
                 | tk.shift(left_edge + half, -m.depth) | tk.shift(right_edge - half, -m.depth))
        lsb = 0.3 * m.lsb("H")
        shape = shape.shift(lsb - shape.bounds[0], 0)
        return shape, shape.bounds[2] + lsb
    lsb = 0.1 * m.lsb("H")
    shape = shape.shift(lsb - shape.bounds[0], 0)
    return shape, shape.bounds[2] + m.rsb("H")


def el_flat(m, J, weight=LEG_WEIGHT):
    return _flat(m, J, lean=0.12, counter=0.72, footed=False, weight=weight)


def de_flat(m, J, weight=LEG_WEIGHT):
    return _flat(m, J, lean=0.07, counter=0.66, footed=True, weight=weight)


# ---- lowercase б ф ----------------------------------------------------------------------

def be_lower(o, f, stretch=2.3):
    """Bowl of o with a stem rising from its left extreme into f's hook, lengthened."""
    fl, fr = f.xs(600)[:2]
    bar_top = f.ys(fr + 60)[1]
    x0 = o.bounds[0]
    y_ext = min(range(300, 800, 5), key=lambda y: o.xs(y)[0])
    flag = f.keep(y0=bar_top + 6) | Shape.rect(fl, y_ext, fr, bar_top + 8)
    flag = flag.warp(lambda x, y: (x if x <= fr else fr + (x - fr) * stretch, y))
    return o | flag.shift(x0 - fl, 0)


def ef_lower(o, l, widen=1.17):
    ox0, oy0, ox1, oy1 = o.bounds
    w = widen * (ox1 - ox0)
    cx = ox0 + w / 2
    bowl = ring(o, width=w, cx=cx)
    ll, lr = l.xs(600)[:2]
    stem = l.keep(y0=600) | l.keep(y1=600).shift(0, -512) | Shape.rect(ll, 80, lr, 610)
    return bowl | stem.shift(cx - (ll + lr) / 2, 0), w + 2 * ox0


# ---- № ₽ ₴ ------------------------------------------------------------------------------

def numero(N, n_adv, ordm, ord_adv):
    ox0, oy0, ox1, _ = ordm.bounds
    dx = n_adv - 110
    thick = 80
    gap = 70
    line = Shape.rect(dx + ox0 + 20, oy0 - gap - thick, dx + ox1 - 20, oy0 - gap)
    return N | ordm.shift(dx, 0) | line, dx + ord_adv - 20


def ruble(P, p_adv, h):
    a, b = P.xs(0.3 * h)[:2]
    x_mid = (b + P.bounds[2]) / 2
    lo, hi = P.ys(x_mid)[:2]
    left = a - 0.75 * (b - a)
    upper = Shape.rect(left, lo, b + 1, hi)
    lo2 = lo - 2.3 * (hi - lo)
    lower = Shape.rect(left, lo2, a + 0.8 * (P.bounds[2] - a), lo2 + (hi - lo))
    s = P | upper | lower
    dx = 40 - s.bounds[0]
    return s.shift(dx, 0), p_adv + dx


def hryvnia(S, s_adv, h):
    s = S.flip_h(s_adv / 2)
    x0, _, x1, _ = s.bounds
    t = 0.058 * h
    gap = 0.045 * h
    mid = 0.5 * h
    bars = (Shape.rect(x0 - 55, mid + gap, x1 + 55, mid + gap + t)
            | Shape.rect(x0 - 55, mid - gap - t, x1 + 55, mid - gap))
    s = s | bars
    dx = 45 - s.bounds[0]
    return s.shift(dx, 0), s.bounds[2] + dx + 45
