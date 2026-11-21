"""Render lines of text from a font file to a PNG, with optional metric guides.

usage: render.py FONT OUT.png SIZE [--guides] [--features ss01] LINE [LINE ...]
"""
import sys

from PIL import Image, ImageDraw, ImageFont


def render(font_path, out, size, lines, guides=False, features=None, width=None):
    font = ImageFont.truetype(font_path, size)
    upm = 2048
    scale = size / upm
    line_h = int(size * 1.45)
    pad = int(size * 0.35)
    kw = {"features": features} if features else {}
    widths = [font.getlength(line, **kw) for line in lines]
    w = width or int(max(widths) + 2 * pad)
    h = line_h * len(lines) + pad
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        base = pad + int(size * 1.0) + i * line_h
        if guides:
            for units, colour in ((0, "#e33"), (1024, "#3a3"), (1434, "#33e"), (-512, "#bbb")):
                y = base - units * scale
                draw.line([(0, y), (w, y)], fill=colour, width=1)
        draw.text((pad, base), line, font=font, fill="black", anchor="ls", **kw)
    img.save(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    guides = "--guides" in args
    if guides:
        args.remove("--guides")
    features = None
    if "--features" in args:
        i = args.index("--features")
        features = args[i + 1].split(",")
        del args[i:i + 2]
    render(args[0], args[1], int(args[2]), args[3:], guides=guides, features=features)
