"""Outline toolkit: glyph outlines as immutable shapes with boolean and affine operations.

Coordinates are font units, y up. Outer contours are kept clockwise, as TrueType expects.
"""
import math

import pathops
from fontTools.misc.roundTools import otRound
from fontTools.cu2qu import curve_to_quadratic
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

BIG = 20000


def _segs(path):
    """Segments with every quadratic split to a single control point."""
    for verb, pts in path.segments:
        if verb == "qCurveTo" and pts[-1] is None:
            # a contour made only of control points: every on-curve point is implied
            offs = list(pts[:-1])
            mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)  # noqa: E731
            yield "moveTo", (mid(offs[-1], offs[0]),)
            for i, ctrl in enumerate(offs):
                yield "qCurveTo", (ctrl, mid(ctrl, offs[(i + 1) % len(offs)]))
        elif verb == "qCurveTo" and len(pts) != 2:
            for ctrl, on in pathops.decompose_quadratic_segment(tuple(pts)):
                yield "qCurveTo", (ctrl, on)
        else:
            yield verb, tuple(pts)


def _normalise(path):
    try:
        return pathops.simplify(path, fix_winding=True, keep_starting_points=False, clockwise=True)
    except pathops.PathOpsError:
        return pathops.simplify(_rounded(path), fix_winding=True, keep_starting_points=False, clockwise=True)


def _rounded(path, digits=None):
    out = pathops.Path()
    for verb, pts in _segs(path):
        if digits is None:
            pts = [(otRound(x), otRound(y)) for x, y in pts]
        else:
            pts = [(round(x, digits), round(y, digits)) for x, y in pts]
        if verb == "moveTo":
            out.moveTo(*pts[0])
        elif verb == "lineTo":
            out.lineTo(*pts[0])
        elif verb == "qCurveTo":
            out.quadTo(*pts[0], *pts[1])
        elif verb == "curveTo":
            out.cubicTo(*pts[0], *pts[1], *pts[2])
        elif verb == "closePath":
            out.close()
    return out


class Shape:
    def __init__(self, path=None):
        self.path = path if path is not None else pathops.Path()

    # ---- constructors -------------------------------------------------------------------

    @classmethod
    def glyph(cls, glyphset, name):
        path = pathops.Path()
        glyphset[name].draw(path.getPen(glyphSet=glyphset))
        return cls(_normalise(path))

    @classmethod
    def raw_glyph(cls, glyphset, name):
        """The glyph's contours exactly as stored (no overlap removal)."""
        path = pathops.Path()
        glyphset[name].draw(path.getPen(glyphSet=glyphset))
        return cls(path)

    @classmethod
    def poly(cls, points):
        path = pathops.Path()
        path.moveTo(*points[0])
        for p in points[1:]:
            path.lineTo(*p)
        path.close()
        return cls(_normalise(path))

    @classmethod
    def rect(cls, x0, y0, x1, y1):
        return cls.poly([(x0, y0), (x0, y1), (x1, y1), (x1, y0)])

    @classmethod
    def outline(cls, segments):
        """Build from a list: first item a point, later items a point (line) or a
        (control, point) pair (quadratic)."""
        path = pathops.Path()
        path.moveTo(*segments[0])
        for seg in segments[1:]:
            if isinstance(seg[0], (int, float)):
                path.lineTo(*seg)
            else:
                path.quadTo(*seg[0], *seg[1])
        path.close()
        return cls(_normalise(path))

    # ---- affine -------------------------------------------------------------------------

    def transform(self, xx, xy, yx, yy, dx, dy):
        path = self.path.transform(xx, xy, yx, yy, dx, dy)
        return Shape(_normalise(path))

    def shift(self, dx=0, dy=0):
        return Shape(self.path.transform(1, 0, 0, 1, dx, dy))

    def scale(self, sx, sy=None, ox=0, oy=0):
        sy = sx if sy is None else sy
        return self.transform(sx, 0, 0, sy, ox - sx * ox, oy - sy * oy)

    def flip_h(self, axis=None):
        if axis is None:
            x0, _, x1, _ = self.bounds
            axis = (x0 + x1) / 2
        return self.transform(-1, 0, 0, 1, 2 * axis, 0)

    def flip_v(self, axis=None):
        if axis is None:
            _, y0, _, y1 = self.bounds
            axis = (y0 + y1) / 2
        return self.transform(1, 0, 0, -1, 0, 2 * axis)

    def rotate180(self, cx=None, cy=None):
        x0, y0, x1, y1 = self.bounds
        cx = (x0 + x1) / 2 if cx is None else cx
        cy = (y0 + y1) / 2 if cy is None else cy
        return self.transform(-1, 0, 0, -1, 2 * cx, 2 * cy)

    def skew(self, tan, oy=0):
        """Horizontal shear: x += tan * (y - oy)."""
        return self.transform(1, 0, tan, 1, -tan * oy, 0)

    def rotate(self, degrees, cx=0, cy=0):
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        return self.transform(c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)

    def warp(self, fn):
        """Map every point (on- and off-curve) through fn(x, y) -> (x, y)."""
        out = pathops.Path()
        for verb, pts in _segs(self.path):
            pts = [fn(x, y) for x, y in pts]
            if verb == "moveTo":
                out.moveTo(*pts[0])
            elif verb == "lineTo":
                out.lineTo(*pts[0])
            elif verb == "qCurveTo":
                out.quadTo(*pts[0], *pts[1])
            elif verb == "curveTo":
                out.cubicTo(*pts[0], *pts[1], *pts[2])
            elif verb == "closePath":
                out.close()
        return Shape(_normalise(out))

    # ---- boolean ------------------------------------------------------------------------

    def _op(self, other, operator):
        try:
            path = pathops.op(self.path, other.path, operator, fix_winding=True,
                              keep_starting_points=False, clockwise=True)
        except pathops.PathOpsError:
            path = pathops.op(_rounded(self.path, 2), _rounded(other.path, 2), operator,
                              fix_winding=True, keep_starting_points=False, clockwise=True)
        return Shape(path)

    def __or__(self, other):
        return self._op(other, pathops.PathOp.UNION)

    def __and__(self, other):
        return self._op(other, pathops.PathOp.INTERSECTION)

    def __sub__(self, other):
        return self._op(other, pathops.PathOp.DIFFERENCE)

    def keep(self, x0=-BIG, y0=-BIG, x1=BIG, y1=BIG):
        return self & Shape.rect(x0, y0, x1, y1)

    def drop(self, x0=-BIG, y0=-BIG, x1=BIG, y1=BIG):
        return self - Shape.rect(x0, y0, x1, y1)

    def grow(self, amount):
        """Offset the outline outwards by `amount` units (negative shrinks)."""
        if amount == 0:
            return self
        edge = pathops.Path()
        edge.addPath(self.path)
        edge.stroke(abs(amount) * 2, pathops.LineCap.BUTT_CAP, pathops.LineJoin.MITER_JOIN, 4.0)
        edge.convertConicsToQuads()
        edge = Shape(_normalise(edge))
        return (self | edge) if amount > 0 else (self - edge)

    # ---- queries ------------------------------------------------------------------------

    @property
    def bounds(self):
        return self.path.bounds

    @property
    def empty(self):
        return len(list(self.path.segments)) == 0

    @property
    def contours(self):
        return [Shape(c) for c in self.path.contours]

    @staticmethod
    def join(shapes):
        """Combine contours without boolean processing (keeps counters as drawn)."""
        path = pathops.Path()
        for s in shapes:
            path.addPath(s.path)
        return Shape(path)

    def _edges(self):
        start = cur = None
        for verb, pts in _segs(self.path):
            if verb == "moveTo":
                start = cur = pts[0]
            elif verb == "lineTo":
                yield (cur, pts[0])
                cur = pts[0]
            elif verb == "qCurveTo":
                yield (cur, pts[0], pts[1])
                cur = pts[1]
            elif verb == "curveTo":
                # flatten cubics coarsely; the fonts here are quadratic so this is rare
                p0, p1, p2, p3 = cur, *pts
                prev = p0
                for i in range(1, 17):
                    t = i / 16
                    m = 1 - t
                    q = (m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                         m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1])
                    yield (prev, q)
                    prev = q
                cur = p3
            elif verb == "closePath":
                if cur != start:
                    yield (cur, start)
                cur = start

    def _crossings(self, value, axis):
        """Coordinates along the other axis where the outline crosses axis == value."""
        other = 1 - axis
        out = []
        for e in self._edges():
            if len(e) == 2:
                a, b = e
                if (a[axis] - value) * (b[axis] - value) < 0 or (a[axis] == value) != (b[axis] == value):
                    if a[axis] == b[axis]:
                        continue
                    t = (value - a[axis]) / (b[axis] - a[axis])
                    if 0 <= t < 1:
                        out.append(a[other] + t * (b[other] - a[other]))
            else:
                p0, p1, p2 = e
                a = p0[axis] - 2 * p1[axis] + p2[axis]
                b = 2 * (p1[axis] - p0[axis])
                c = p0[axis] - value
                ts = []
                if abs(a) < 1e-9:
                    if abs(b) > 1e-9:
                        ts = [-c / b]
                else:
                    disc = b * b - 4 * a * c
                    if disc > 0:
                        r = math.sqrt(disc)
                        ts = [(-b - r) / (2 * a), (-b + r) / (2 * a)]
                for t in ts:
                    if 0 <= t < 1:
                        m = 1 - t
                        out.append(m * m * p0[other] + 2 * m * t * p1[other] + t * t * p2[other])
        return sorted(out)

    def xs(self, y):
        return self._crossings(y + 0.01, 1)

    def ys(self, x):
        return self._crossings(x + 0.01, 0)

    def flatten(self, steps=8):
        """Polylines (one per contour) for drawing."""
        lines = []
        cur = None
        for verb, pts in _segs(self.path):
            if verb == "moveTo":
                cur = [pts[0]]
                lines.append(cur)
            elif verb == "lineTo":
                cur.append(pts[0])
            elif verb == "qCurveTo":
                p0, p1, p2 = cur[-1], pts[0], pts[1]
                for i in range(1, steps + 1):
                    t = i / steps
                    m = 1 - t
                    cur.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                                m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1]))
            elif verb == "curveTo":
                p0, p1, p2, p3 = cur[-1], *pts
                for i in range(1, steps + 1):
                    t = i / steps
                    m = 1 - t
                    cur.append((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                                m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]))
        return lines

    def points(self):
        """(x, y, on_curve) for every stored point."""
        out = []
        for verb, pts in _segs(self.path):
            if verb in ("moveTo", "lineTo"):
                out.append((*pts[0], True))
            elif verb == "qCurveTo":
                out.append((*pts[0], False))
                out.append((*pts[1], True))
        return out

    # ---- output -------------------------------------------------------------------------

    def to_glyph(self, smooth=False):
        """A TrueType glyph. With smooth=True, on-curve points that sit (to within a unit)
        midway between their two control points are left implied, which makes the curve
        exactly smooth there; used for drawn strokes."""
        path = _normalise(_rounded(_normalise(self.path)))
        path = _drop_slivers(path)
        pen = TTGlyphPen(glyphSet=None)
        path.draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=False))
        glyph = pen.glyph()
        _merge_close_points(glyph)
        if smooth:
            _imply_midpoints(glyph)
        glyph.recalcBounds(glyfTable=None)
        return glyph


def _drop_slivers(path, min_area=40):
    out = pathops.Path()
    for contour in path.contours:
        if abs(contour.area) >= min_area:
            out.addPath(contour)
    return out


def _merge_close_points(glyph, limit=3.0):
    """Boolean operations on rounded outlines can leave on-curve points a unit or two
    apart. Merge each such pair, dropping whichever point lies closer to the line through
    its neighbours, so the outline has no stray stubs."""
    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

    coords = list(glyph.coordinates)
    flags = list(glyph.flags)
    new_coords, new_flags, new_ends = [], [], []
    start = 0
    for end in glyph.endPtsOfContours:
        pts = coords[start:end + 1]
        on = [f & 1 for f in flags[start:end + 1]]
        start = end + 1
        changed = True
        while changed and len(pts) > 3:
            changed = False
            n = len(pts)
            for i in range(n):
                j = (i + 1) % n
                if not (on[i] and on[j]):
                    continue
                if math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) >= limit:
                    continue

                def cost(k, a, b):
                    (ax, ay), (bx, by), (px, py) = pts[a], pts[b], pts[k]
                    length = math.hypot(bx - ax, by - ay) or 1
                    return abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / length

                drop_i = cost(i, (i - 1) % n, j)
                drop_j = cost(j, i, (j + 1) % n)
                k = i if drop_i <= drop_j else j
                del pts[k]
                del on[k]
                changed = True
                break
        new_coords += pts
        new_flags += on
        new_ends.append(len(new_coords) - 1)
    glyph.coordinates = GlyphCoordinates(new_coords)
    glyph.flags = bytearray(new_flags)
    glyph.endPtsOfContours = new_ends


# ---- drawn strokes --------------------------------------------------------------------------

def stroke(nodes, tension=0.36, samples=2):
    """A stroke of varying width drawn along a smooth centreline, for shapes with no
    source outline to borrow.

    nodes: (x, y, width, heading[, ease]) tuples the centreline passes through; heading is
    the direction of travel in degrees (0 east, 90 north) or None to follow the neighbours.
    The width changes smoothly from node to node; an ease below 1 makes the change to the
    next node happen early in the span, above 1 late.
    Ends are cut square to the direction of travel; a width near zero gives a point."""
    n = len(nodes)
    pts = [(nd[0], nd[1]) for nd in nodes]
    widths = [nd[2] for nd in nodes]
    eases = [nd[4] if len(nd) > 4 else 1.0 for nd in nodes]
    dirs = []
    for i, heading in enumerate(nd[3] for nd in nodes):
        if heading is not None:
            a = math.radians(heading)
            dirs.append((math.cos(a), math.sin(a)))
        else:
            ax, ay = pts[max(i - 1, 0)]
            bx, by = pts[min(i + 1, n - 1)]
            length = math.hypot(bx - ax, by - ay) or 1
            dirs.append(((bx - ax) / length, (by - ay) / length))

    def segment(i):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        chord = math.hypot(x1 - x0, y1 - y0)
        c1 = (x0 + dirs[i][0] * chord * tension, y0 + dirs[i][1] * chord * tension)
        c2 = (x1 - dirs[i + 1][0] * chord * tension, y1 - dirs[i + 1][1] * chord * tension)
        return (x0, y0), c1, c2, (x1, y1)

    def side(i, t, sign):
        p0, p1, p2, p3 = segment(i)
        m = 1 - t
        cx = m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0]
        cy = m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]
        dx = 3 * m * m * (p1[0] - p0[0]) + 6 * m * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0])
        dy = 3 * m * m * (p1[1] - p0[1]) + 6 * m * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1])
        length = math.hypot(dx, dy) or 1
        e = t ** eases[i]
        w = widths[i] + (widths[i + 1] - widths[i]) * (3 * e * e - 2 * e ** 3)
        return cx - sign * dy / length * w / 2, cy + sign * dx / length * w / 2

    def edge(sign):
        """Points along one side with the edge's own direction at each."""
        out = []
        eps = 1e-3
        for i in range(n - 1):
            for k in range(samples + 1):
                if k == 0 and i > 0:
                    continue
                t = k / samples
                p = side(i, t, sign)
                a = side(i, max(t - eps, 0), sign)
                b = side(i, min(t + eps, 1), sign)
                length = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
                out.append((p, ((b[0] - a[0]) / length, (b[1] - a[1]) / length)))
        return out

    def run(path, points):
        # each span is a cubic that leaves and arrives along the edge's own direction,
        # converted at once to the quadratics TrueType uses
        for (a, ta), (b, tb) in zip(points, points[1:]):
            third = math.hypot(b[0] - a[0], b[1] - a[1]) / 3
            if third < 0.05:
                continue
            cubic = (a, (a[0] + ta[0] * third, a[1] + ta[1] * third),
                     (b[0] - tb[0] * third, b[1] - tb[1] * third), b)
            spline = curve_to_quadratic(cubic, 0.4)
            offs = spline[1:-1]
            for k, ctrl in enumerate(offs):
                if k + 1 < len(offs):
                    nxt = offs[k + 1]
                    path.quadTo(*ctrl, (ctrl[0] + nxt[0]) / 2, (ctrl[1] + nxt[1]) / 2)
                else:
                    path.quadTo(*ctrl, *b)

    left, right = edge(+1), edge(-1)
    back = [(p, (-t[0], -t[1])) for p, t in reversed(right)]
    path = pathops.Path()
    path.moveTo(*left[0][0])
    run(path, left)
    path.lineTo(*back[0][0])
    run(path, back)
    path.close()
    return Shape(_normalise(path))


def _imply_midpoints(glyph, tolerance=1.01):
    """Drop on-curve points lying within `tolerance` of the midpoint of their neighbouring
    control points. TrueType then implies the point exactly at the midpoint, so the two
    curves meet without the small kink that rounding to whole units can leave."""
    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

    coords, flags = list(glyph.coordinates), list(glyph.flags)
    new_coords, new_flags, new_ends = [], [], []
    start = 0
    for end in glyph.endPtsOfContours:
        pts = coords[start:end + 1]
        on = [f & 1 for f in flags[start:end + 1]]
        start = end + 1
        n = len(pts)
        keep = []
        for i in range(n):
            a, b = (i - 1) % n, (i + 1) % n
            implied = (on[i] and not on[a] and not on[b]
                       and abs((pts[a][0] + pts[b][0]) / 2 - pts[i][0]) <= tolerance
                       and abs((pts[a][1] + pts[b][1]) / 2 - pts[i][1]) <= tolerance)
            keep.append(not implied)
        if sum(keep) < 3 or not any(o and k for o, k in zip(on, keep)):
            keep = [True] * n
        new_coords += [p for p, k in zip(pts, keep) if k]
        new_flags += [o for o, k in zip(on, keep) if k]
        new_ends.append(len(new_coords) - 1)
    glyph.coordinates = GlyphCoordinates(new_coords)
    glyph.flags = bytearray(new_flags)
    glyph.endPtsOfContours = new_ends
