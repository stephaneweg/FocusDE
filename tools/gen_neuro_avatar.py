#!/usr/bin/env python3
# Generate the "Professeur Neuro" mascot avatar (owl-Einstein) and bake it into a
# SillyTavern V2 character card PNG (card JSON embedded in the "chara" tEXt chunk).
#   python tools/gen_neuro_avatar.py
# -> rootfs/usr/local/lib/focusde/assistant/neuro_avatar.png   (plain avatar)
# -> rootfs/usr/local/lib/focusde/assistant/professeur-neuro.png (importable ST card)
import os, sys, json, base64, math
from PIL import Image, ImageDraw, PngImagePlugin

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
ASSET = os.path.join(ROOT, "rootfs", "usr", "local", "lib", "focusde", "assistant")


def draw_avatar():
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def circle(c, r, **kw):
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], **kw)

    d.rounded_rectangle([0, 0, S, S], radius=140, fill=(233, 228, 246, 255))  # pastel bg
    # wild white "Einstein" hair (frizzy cluster along the top)
    for a in range(-70, 71, 14):
        rad = math.radians(a - 90)
        circle((512 + int(300 * math.cos(rad)), 470 + int(300 * math.sin(rad))), 95, fill=(214, 208, 232, 255))
    for a in range(-66, 67, 12):
        rad = math.radians(a - 90)
        circle((512 + int(285 * math.cos(rad)), 475 + int(285 * math.sin(rad))), 82, fill=(247, 246, 251, 255))
    # a few spiky tufts poking out (more "professor frizz")
    for x, y in ((250, 250), (774, 250), (330, 180), (694, 180), (512, 150)):
        circle((x, y), 34, fill=(247, 246, 251, 255))
    # head (chibi owl)
    circle((512, 510), 300, fill=(176, 164, 148, 255))
    circle((512, 540), 250, fill=(196, 186, 170, 255))
    # facial disc: two big cream eye discs
    circle((406, 520), 140, fill=(240, 232, 214, 255))
    circle((618, 520), 140, fill=(240, 232, 214, 255))
    # round glasses + bridge
    gl = (58, 53, 80, 255)
    d.ellipse([406 - 118, 520 - 118, 406 + 118, 520 + 118], outline=gl, width=18)
    d.ellipse([618 - 118, 520 - 118, 618 + 118, 520 + 118], outline=gl, width=18)
    d.line([406 + 112, 520, 618 - 112, 520], fill=gl, width=16)
    # eyes with catchlight
    for ex in (406, 618):
        circle((ex, 528), 62, fill=(44, 42, 56, 255))
        circle((ex - 20, 510), 18, fill=(255, 255, 255, 235))
    # beak
    d.polygon([(512, 556), (474, 612), (550, 612)], fill=(224, 162, 74, 255))
    # bowtie (accent purple)
    bt = (124, 111, 224, 255)
    d.polygon([(512, 812), (430, 772), (430, 852)], fill=bt)
    d.polygon([(512, 812), (594, 772), (594, 852)], fill=bt)
    circle((512, 812), 24, fill=(90, 80, 180, 255))
    return img.resize((512, 512), Image.LANCZOS)


def main():
    os.makedirs(ASSET, exist_ok=True)
    avatar = draw_avatar()
    avatar.save(os.path.join(ASSET, "neuro_avatar.png"))
    # bake the V2 card JSON into the PNG (SillyTavern reads the "chara" tEXt chunk).
    card = json.load(open(os.path.join(ASSET, "professeur-neuro.json"), encoding="utf-8"))
    b64 = base64.b64encode(json.dumps(card, ensure_ascii=False).encode("utf-8")).decode("ascii")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("chara", b64)
    avatar.save(os.path.join(ASSET, "professeur-neuro.png"), pnginfo=meta)
    print("wrote neuro_avatar.png + professeur-neuro.png (card) to", ASSET)


if __name__ == "__main__":
    main()
