"""Automated checks on the built font.

usage: check.py ORIGINAL.ttf BUILT.ttf [BUILT.woff2]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ots  # noqa: E402
import uharfbuzz as hb  # noqa: E402

import greek  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

from geom import Shape  # noqa: E402

LETTERS = ("АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ" "абвгдежзийклмнопрстуфхцчшщъыьэюя" "ЁёЄєІіЇїЎўҐґ")
SYMBOLS = "№₽₴"
GREEK = greek.ALL
failures = []


def check(label, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + label + (f"  [{detail}]" if detail else ""))
    if not ok:
        failures.append(label)


def shaper(path):
    blob = hb.Blob.from_file_path(path)
    font = hb.Font(hb.Face(blob))

    def shape(text, features=None, script=None):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, features or {})
        return [(i.codepoint, p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    return shape


def main():
    orig_path, built_path = sys.argv[1:3]
    orig, built = TTFont(orig_path), TTFont(built_path)
    cmap = built.getBestCmap()
    glyf = built["glyf"]
    gs = built.getGlyphSet()
    order = built.getGlyphOrder()
    new = order[len(orig.getGlyphOrder()):]

    # ---- coverage ----
    missing = [c for c in LETTERS + SYMBOLS if ord(c) not in cmap]
    check("all 79 Cyrillic code points are mapped", not missing and len(set(LETTERS + SYMBOLS)) == 79,
          f"missing {missing}" if missing else f"{len(set(LETTERS + SYMBOLS))} code points")
    has_greek = ord("α") in cmap
    if has_greek:
        missing = [c for c in GREEK if ord(c) not in cmap]
        check("all 72 new Greek code points are mapped, and μ is still the original glyph",
              not missing and len(set(GREEK) - {"μ"}) == 72 and cmap[0x3BC] == orig.getBestCmap()[0x3BC],
              f"missing {missing}" if missing else f"{len(set(GREEK) - {'μ'})} code points")
    else:
        greek_block = lambda m: {c: g for c, g in m.items() if 0x370 <= c <= 0x3FF}  # noqa: E731
        check("the unfinished Greek letters are left out: only the original μ is present",
              greek_block(cmap) == greek_block(orig.getBestCmap()), str(sorted(chr(c) for c in greek_block(cmap))))
    empty = [n for n in new if glyf[n].numberOfContours == 0]
    check("no new glyph is empty", not empty, f"{len(new)} new glyphs" if not empty else str(empty))
    check("original glyph order is a prefix of the new one", order[:len(orig.getGlyphOrder())] == orig.getGlyphOrder())

    # ---- originals untouched ----
    og, ogs = orig["glyf"], orig.getGlyphOrder()
    changed = [n for n in ogs if og[n].compile(og) != glyf[n].compile(glyf) or orig["hmtx"][n] != built["hmtx"][n]]
    check("every original outline and advance is byte-identical", not changed, f"{len(ogs)} glyphs compared" if not changed else str(changed[:8]))
    ocmap = orig.getBestCmap()
    check("every original character still maps to the same glyph", all(cmap.get(c) == g for c, g in ocmap.items()), f"{len(ocmap)} characters")
    for tag in ("fpgm", "prep", "cvt ", "gasp", "hhea"):
        same = orig.getTableData(tag) == built.getTableData(tag) if tag != "hhea" else (
            (orig["hhea"].ascent, orig["hhea"].descent, orig["hhea"].lineGap) == (built["hhea"].ascent, built["hhea"].descent, built["hhea"].lineGap))
        check(f"'{tag}' {'vertical metrics' if tag == 'hhea' else 'table'} unchanged", same)
    o2a, o2b = orig["OS/2"], built["OS/2"]
    check("OS/2 vertical metrics unchanged", all(getattr(o2a, k) == getattr(o2b, k) for k in
          ("sTypoAscender", "sTypoDescender", "sTypoLineGap", "usWinAscent", "usWinDescent", "sxHeight", "sCapHeight")))

    # ---- Latin shaping regression ----
    s0, s1 = shaper(orig_path), shaper(built_path)
    letters = [chr(c) for c in sorted(ocmap) if c > 0x20]
    diffs = 0
    count = 0
    for a in letters:
        line = "".join(a + b for b in letters)
        r0, r1 = s0(line), s1(line)
        count += len(letters)
        if r0 != r1:
            diffs += 1
    check("Latin text shapes identically before and after (all pairs, default features)", diffs == 0, f"{count} pairs")
    for feats in ({"liga": True}, {"frac": True}, {"sups": True}, {"ordn": True}):
        text = "office fl 1/2 3/4 12345 1o 2a No. H2O x2 100/00"
        check(f"feature {next(iter(feats))} shapes identically", s0(text, feats) == s1(text, feats))

    # ---- Cyrillic layout ----
    gid = built.getGlyphID
    plain = s1("ЛДлд")
    alt = s1("ЛДлд", {"ss01": True})
    check("ss01 swaps Л Д л д to the .ss01 glyphs", [g for g, _ in alt] == [gid("uni%04X.ss01" % ord(c)) for c in "ЛДлд"]
          and [g for g, _ in plain] == [gid("uni%04X" % ord(c)) for c in "ЛДлд"])
    rest = "".join(c for c in LETTERS + SYMBOLS + (GREEK if has_greek else "") if c not in "ЛДлд")
    check("ss01 changes nothing else", s1(rest) == s1(rest, {"ss01": True}) and s1("ABCabc") == s1("ABCabc", {"ss01": True}))

    def adv(text, **kw):
        return sum(a for _, a in s1(text, **kw))

    def kern(pair):
        return adv(pair) - adv(pair[0]) - adv(pair[1])

    lat = lambda p: sum(a for _, a in s0(p)) - sum(a for _, a in s0(p[0])) - sum(a for _, a in s0(p[1]))  # noqa: E731
    expect = {"АТ": "AT", "ТА": "TA", "ГА": "TA", "То": "To", "Го": "To", "УА": "YA", "АУ": "AY", "КО": "KO",
              "Т.": "T.", "Г,": "T,", "Р,": "P,", "Гл": "Ta", "га": "ra", "та": "ra", "Ут": None}
    bad = [(c, kern(c), lat(l)) for c, l in expect.items() if l and kern(c) != lat(l)]
    check("Cyrillic kerning follows the Latin analogues", not bad, str(bad) if bad else ", ".join(f"{c} {kern(c)}" for c in list(expect)[:8]))
    check("unrelated Cyrillic pairs are not kerned", kern("НН") == 0 and kern("нн") == 0 and kern("ШП") == 0)
    if has_greek:
        expect = {"ΑΤ": "AT", "ΤΑ": "TA", "ΓΑ": "TA", "Το": "To", "Γο": "To", "ΥΑ": "YA", "ΛΤ": "AT", "ΔΥ": "AY",
                  "Ρ,": "P,", "Τ.": "T.", "ΚΟ": "KO", "Τά": "To"}
        bad = [(c, kern(c), lat(l)) for c, l in expect.items() if kern(c) != lat(l)]
        check("Greek kerning follows the Latin analogues", not bad, str(bad) if bad else ", ".join(f"{c} {kern(c)}" for c in list(expect)[:8]))
        check("unrelated Greek pairs, and Greek next to Cyrillic, are not kerned",
              kern("ΗΗ") == 0 and kern("ηη") == 0 and kern("ΠΗ") == 0 and kern("ГΑ") == 0 and kern("ΓА") == 0)
        # an accent sits over the middle of the top of its letter
        order_ = built.getGlyphOrder()
        off = []
        for ch, base in {**greek.TONOS_LOWER, **greek.DIALYTIKA_LOWER, **greek.DIALYTIKA_TONOS_LOWER}.items():
            g = glyf["uni%04X" % ord(ch)]
            mark = g.components[-1]
            mg = glyf[mark.glyphName]
            mark_cx = mark.x + (mg.xMin + mg.xMax) / 2
            top = Shape.glyph(gs, g.components[0].glyphName).keep(y0=717, y1=1064).bounds
            if abs(mark_cx - (top[0] + top[2]) / 2) > 12 or mark.y + mg.yMin < 1100:
                off.append(ch)
        check("lowercase accents are centred over their letters and clear of them", not off, str(off) if off else "11 accented letters")
        caps_bad = []
        for ch in greek.TONOS_UPPER:
            g = glyf["uni%04X" % ord(ch)]
            mark = g.components[-1]
            mg = glyf[mark.glyphName]
            if mark.x + mg.xMin < 20 or mark.y + mg.yMax > 1480 or built["hmtx"]["uni%04X" % ord(ch)][0] < built["hmtx"][g.components[0].glyphName][0]:
                caps_bad.append(ch)
        check("capital tonos sits at the upper left inside the glyph's own width", not caps_bad, str(caps_bad) if caps_bad else "7 capitals")
    for tbl in ("GSUB", "GPOS"):
        expected = ["DFLT", "cyrl", "grek", "latn"] if has_greek else ["DFLT", "cyrl", "latn"]
        tags = [sr.ScriptTag for sr in built[tbl].table.ScriptList.ScriptRecord]
        check(f"{tbl} registers {', '.join(expected)}", tags == expected, str(tags))

    # ---- outline hygiene ----
    win_top, win_bottom = o2b.usWinAscent, -o2b.usWinDescent
    out_of_bounds, short, overlapping, direction, offcurve_only = [], [], [], [], []
    for n in new:
        g = glyf[n]
        if g.isComposite():
            if g.yMax > win_top or g.yMin < win_bottom:
                out_of_bounds.append(n)
            continue
        if g.yMax > win_top or g.yMin < win_bottom:
            out_of_bounds.append(n)
        raw = Shape.raw_glyph(gs, n)
        clean = Shape.glyph(gs, n)
        a_raw = sum(abs(c.area) for c in raw.path.contours)
        # after overlap removal the filled area equals outer minus counters; compare signed sums
        signed = abs(sum(c.area for c in raw.path.contours))
        cleaned = abs(sum(c.area for c in clean.path.contours))
        if abs(signed - cleaned) > 0.002 * a_raw:
            overlapping.append(n)
        outer = max(raw.path.contours, key=lambda c: abs(c.area))
        ref_outer = max(Shape.raw_glyph(gs, "O").path.contours, key=lambda c: abs(c.area))
        if (outer.area > 0) != (ref_outer.area > 0):
            direction.append(n)
        coords, ends, flags = g.getCoordinates(glyf)
        start = 0
        for e in ends:
            pts = [coords[i] for i in range(start, e + 1)]
            on = [flags[i] & 1 for i in range(start, e + 1)]
            for i in range(len(pts)):
                j = (i + 1) % len(pts)
                if on[i] and on[j]:
                    d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                    if d < 3:
                        short.append((n, pts[i], pts[j]))
            start = e + 1
    check("new glyphs fit inside the existing win ascent/descent", not out_of_bounds, str(out_of_bounds))
    check("new glyphs have no overlapping contours", not overlapping, str(overlapping))
    check("new glyphs have the same contour direction as the originals", not direction, str(direction))
    check("new glyphs have no stray segments shorter than 3 units", not short, str(short[:10]) + (f" (+{len(short) - 10} more)" if len(short) > 10 else ""))
    check("no new glyph carries hinting instructions", all(not getattr(glyf[n], "program", None) or not glyf[n].program.getAssembly() for n in new))
    check("composites are one level deep", built["maxp"].maxComponentDepth <= 1, f"depth {built['maxp'].maxComponentDepth}")

    # ---- stroke weight ----
    def stem(name, y):
        xs = Shape.glyph(gs, name).xs(y)
        return [round(xs[i + 1] - xs[i]) for i in range(0, len(xs) - 1, 2)]

    cap_ref = stem("H", 500)[0]
    lc_ref = stem("n", 500)[0]
    caps = {c: stem("uni%04X" % ord(c), 500)[0] for c in "БГПЦШЩИЫЬЮ"}
    lcs = {c: stem("uni%04X" % ord(c), 400)[0] for c in "гпцшщиыьюнк"}
    check(f"capital stems match H ({cap_ref})", all(abs(v - cap_ref) <= 3 for v in caps.values()), str(caps))
    check(f"lowercase stems match n ({lc_ref}) within 4 units", all(abs(v - lc_ref) <= 4 for v in lcs.values()), str(lcs))
    if has_greek:
        gcaps = {c: stem("uni%04X" % ord(c), 900)[0] for c in "ΗΠΓΨ"}
        gcaps["Ψ"] = stem("uni03A8", 400)[0]          # below the cup, above the flare of the foot
        glcs = {"η": stem("uni03B7", 400)[0], "ρ": stem("uni03C1", -60)[0], "φ": stem("uni03C6", -60)[0],
                "ψ": stem("uni03C8", -60)[0], "β": stem("uni03B2", -60)[0], "ι": stem("uni03B9", 600)[0]}
        check(f"Greek capital stems match H ({cap_ref})", all(abs(v - cap_ref) <= 3 for v in gcaps.values()), str(gcaps))
        check(f"Greek lowercase stems match n ({lc_ref}) within 4 units", all(abs(v - lc_ref) <= 4 for v in glcs.values()), str(glcs))
        depths = {c: glyf["uni%04X" % ord(c)].yMin for c in "βγζηξρςφχψ"}
        check("Greek descenders reach the depth of the original μ (-348) to within 20 units",
              all(abs(v - glyf["mu"].yMin) <= 20 for v in depths.values()), str(depths))

    # ---- naming and metadata ----
    name = built["name"]
    fam = {name.getDebugName(i) for i in (1, 4, 6, 16) if name.getDebugName(i)}
    check("font names do not contain the reserved name", all("Marcellus" not in v for v in fam), str(sorted(fam)))
    check("original copyright notice is retained", "Brian J. Bonislawsky" in name.getDebugName(0) and "Marcellus" in name.getDebugName(0))
    check("licence strings retained", "SIL Open Font License" in name.getDebugName(13) and bool(name.getDebugName(14)))
    check("additions are credited to Propensive OÜ", "Propensive OÜ" in name.getDebugName(0) and "Propensive OÜ" in name.getDebugName(9))
    check("OS/2 declares Cyrillic", bool(o2b.ulUnicodeRange1 & (1 << 9)) and bool(o2b.ulCodePageRange1 & (1 << 2)))
    if has_greek:
        check("OS/2 declares Greek", bool(o2b.ulUnicodeRange1 & (1 << 7)) and bool(o2b.ulCodePageRange1 & (1 << 3)))
        check("the work-in-progress build is named apart from the font", "WIP" in name.getDebugName(1), name.getDebugName(1))
    else:
        check("OS/2 claims no more Greek than Marcellus did",
              o2b.ulUnicodeRange1 & (1 << 7) == o2a.ulUnicodeRange1 & (1 << 7) and not o2b.ulCodePageRange1 & (1 << 3))
        check("the font is named Propensity", name.getDebugName(1) == "Propensity" and name.getDebugName(6) == "Propensity-Regular",
              f"{name.getDebugName(1)} / {name.getDebugName(6)}")
    check("the description acknowledges Marcellus", "based on Marcellus" in name.getDebugName(10), name.getDebugName(10)[:60])
    check("embedding permissions unchanged", o2a.fsType == o2b.fsType, f"fsType {o2b.fsType}")

    # ---- sanitizer (what browsers run before accepting a web font) ----
    for path in [built_path] + sys.argv[3:]:
        result = ots.sanitize(path, "/dev/null", capture_output=True)
        check(f"OpenType Sanitizer accepts {Path(path).name}", result.returncode == 0, result.stderr.decode().strip()[:200])
    if len(sys.argv) > 3:
        web = TTFont(sys.argv[3])
        check("WOFF2 holds the same glyphs and character map", web.getGlyphOrder() == order and web.getBestCmap() == cmap)

    print()
    print(f"{len(failures)} failure(s)" if failures else "all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
