"""Build Propensity: Marcellus plus Cyrillic.

usage: build.py MARCELLUS.ttf MARCELLUS_SC.ttf OUT.ttf [--greek] [--draft]

--greek adds the unfinished Greek letters and names the result as work in progress.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontTools.ttLib.tables._g_l_y_f import (  # noqa: E402
    ROUND_XY_TO_GRID, USE_MY_METRICS, Glyph, GlyphComponent)
from fontTools.ttLib import TTFont  # noqa: E402

import glyphs  # noqa: E402


def add_glyphs(font, specs):
    glyf, hmtx = font["glyf"], font["hmtx"]
    order = font.getGlyphOrder()
    cmap_tables = [t for t in font["cmap"].tables if t.isUnicode()]
    for spec in specs:
        name = spec["name"]
        if spec["kind"] == "shape":
            glyph = spec["shape"].to_glyph(smooth=spec.get("smooth", False))
        else:
            glyph = Glyph()
            glyph.numberOfContours = -1
            glyph.components = []
            parts = []
            for base, dx, dy in spec["parts"]:
                g = glyf[base] if base in glyf.glyphs else None
                if g is not None and g.isComposite():
                    parts += [(c.glyphName, dx + c.x, dy + c.y) for c in g.components]
                else:
                    parts.append((base, dx, dy))
            for i, (base, dx, dy) in enumerate(parts):
                c = GlyphComponent()
                c.glyphName = base
                c.x, c.y = round(dx), round(dy)
                # same flags as the font's existing accented letters
                lead = i == 0 and not spec.get("own_metrics")
                c.flags = (USE_MY_METRICS | ROUND_XY_TO_GRID) if lead else ROUND_XY_TO_GRID
                glyph.components.append(c)
        order.append(name)
        glyf.glyphs[name] = glyph
        hmtx.metrics[name] = (round(spec["adv"]), getattr(glyph, "xMin", 0))
        if spec.get("code") is not None:
            for t in cmap_tables:
                t.cmap[spec["code"]] = name
    font.setGlyphOrder(order)
    glyf.glyphOrder = order
    # composites whose first part carries the metrics
    for spec in specs:
        if spec["kind"] == "comp":
            g = glyf[spec["name"]]
            g.recalcBounds(glyf)
            hmtx.metrics[spec["name"]] = (round(spec["adv"]), g.xMin)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    src, sc, out = args[:3]
    greek = "--greek" in flags
    font = TTFont(src)
    sc_font = TTFont(sc)
    specs = glyphs.build_specs(font, sc_font, with_greek=greek)
    add_glyphs(font, specs)
    if "--draft" in flags:
        font.save(out)
        return
    import finish
    finish.finish(font, specs, greek=greek)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    finish.write_extras(font, out, greek=greek)


if __name__ == "__main__":
    main()
