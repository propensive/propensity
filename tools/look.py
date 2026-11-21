"""Inspect source glyphs: print crossings at chosen heights, or dump points.

usage: look.py FONT GLYPH[,GLYPH...] [--y 0,100,...] [--x ...] [--points]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontTools.ttLib import TTFont  # noqa: E402

from geom import Shape  # noqa: E402


def main():
    args = sys.argv[1:]
    font = TTFont(args[0])
    gs = font.getGlyphSet()
    ys = xs = None
    if "--y" in args:
        ys = [float(v) for v in args[args.index("--y") + 1].split(",")]
    if "--x" in args:
        xs = [float(v) for v in args[args.index("--x") + 1].split(",")]
    for name in args[1].split(","):
        s = Shape.glyph(gs, name)
        b = s.bounds
        print(f"== {name}: adv {font['hmtx'][name][0]} bounds {tuple(round(v) for v in b)} contours {len(s.contours)}")
        for y in ys or []:
            print(f"   y={y:g}: x = {[round(v, 1) for v in s.xs(y)]}")
        for x in xs or []:
            print(f"   x={x:g}: y = {[round(v, 1) for v in s.ys(x)]}")
        if "--points" in args:
            for i, c in enumerate(s.contours):
                print(f"   contour {i}: " + " ".join(f"{x:g},{y:g}{'' if on else '*'}" for x, y, on in c.points()))


if __name__ == "__main__":
    main()
