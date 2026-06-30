#!/usr/bin/env python3
# Generate one palette-swatch strip PNG per Focus DE theme, for the documentation.
# Single source of truth: the palettes are read from the shell's focus_theme.py.
#   python tools/gen_palettes.py   ->  docs/images/palettes/<slug>.png
import os, sys, unicodedata
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "rootfs", "usr", "local", "lib", "focusde"))
import focus_theme  # noqa: E402

OUT = os.path.join(ROOT, "docs", "images", "palettes")
os.makedirs(OUT, exist_ok=True)

# Colours shown, left to right (keys of a Focus DE palette).
COLS = ["bg", "surface", "border", "accent", "accent_strong", "accent_ink", "ink", "avatar"]
SW, GAP, PAD = 44, 5, 8
W = PAD * 2 + len(COLS) * SW + (len(COLS) - 1) * GAP
H = PAD * 2 + SW


def slug(name):
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "-" for c in n.lower()).strip("-")


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def main():
    for name in focus_theme.ORDER:
        pal = focus_theme.PALETTES[name]
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = PAD
        for k in COLS:
            d.rounded_rectangle([x, PAD, x + SW, PAD + SW], radius=8,
                                fill=hex2rgb(pal[k]), outline=(150, 150, 150, 160), width=1)
            x += SW + GAP
        img.save(os.path.join(OUT, slug(name) + ".png"))
    print("wrote %d palette strips to %s" % (len(focus_theme.ORDER), OUT))
    print("columns:", " ".join(COLS))


if __name__ == "__main__":
    main()
