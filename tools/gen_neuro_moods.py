#!/usr/bin/env python3
# Génère les avatars d'HUMEUR du Professeur Neuro (hibou-Einstein expressif).
#   python tools/gen_neuro_moods.py
# -> rootfs/usr/local/lib/focusde/assistant/moods/<humeur>.png  (512x512, largeur pleine)
# + une planche de prévisualisation dans le scratchpad.
import os, sys, math
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "rootfs", "usr", "local", "lib", "focusde", "assistant", "moods")

MOODS = ["neutre", "content", "pensif", "surpris", "triste", "fier"]

def draw(mood):
    S = 1024
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    def circle(c, r, **kw):
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], **kw)

    # fond TRANSPARENT : l'avatar colle au thème (le fond du header transparaît).
    # tignasse blanche
    for a in range(-70, 71, 14):
        rad = math.radians(a - 90)
        circle((512 + int(300 * math.cos(rad)), 470 + int(300 * math.sin(rad))), 95, fill=(214, 208, 232, 255))
    for a in range(-66, 67, 12):
        rad = math.radians(a - 90)
        circle((512 + int(285 * math.cos(rad)), 475 + int(285 * math.sin(rad))), 82, fill=(247, 246, 251, 255))
    for x, y in ((250, 250), (774, 250), (330, 180), (694, 180), (512, 150)):
        circle((x, y), 34, fill=(247, 246, 251, 255))

    # tête
    circle((512, 510), 300, fill=(176, 164, 148, 255))
    circle((512, 540), 250, fill=(196, 186, 170, 255))
    # disques des yeux
    circle((406, 520), 140, fill=(240, 232, 214, 255))
    circle((618, 520), 140, fill=(240, 232, 214, 255))

    gl = (58, 53, 80, 255)
    # --- pupilles + forme des yeux selon l'humeur ---
    px, py, pr = 0, 8, 62          # décalage pupille + rayon
    if mood == "pensif":
        px, py = -34, -22          # regard en haut à gauche
    elif mood == "triste":
        py = 40                    # regard baissé
    elif mood == "surpris":
        pr = 40                    # petites pupilles, yeux écarquillés
    happy_eyes = mood in ("content", "fier")
    for ex in (406, 618):
        if happy_eyes:             # yeux rieurs : arcs ^ ^
            d.arc([ex - 70, 500, ex + 70, 620], start=200, end=340, fill=(44, 42, 56, 255), width=20)
        else:
            circle((ex + px, 528 + py), pr, fill=(44, 42, 56, 255))
            circle((ex + px - 20, 508 + py), max(10, pr // 4), fill=(255, 255, 255, 235))
    # lunettes rondes + pont
    d.ellipse([406 - 118, 520 - 118, 406 + 118, 520 + 118], outline=gl, width=18)
    d.ellipse([618 - 118, 520 - 118, 618 + 118, 520 + 118], outline=gl, width=18)
    d.line([406 + 112, 520, 618 - 112, 520], fill=gl, width=16)

    # --- sourcils (au-dessus des lunettes) ---
    brow = (70, 62, 92, 255)
    if mood == "surpris":
        d.arc([406 - 70, 320, 406 + 70, 420], 200, 340, fill=brow, width=16)
        d.arc([618 - 70, 320, 618 + 70, 420], 200, 340, fill=brow, width=16)
    elif mood == "triste":
        d.line([406 - 60, 380, 406 + 50, 350], fill=brow, width=16)   # intérieurs relevés
        d.line([618 + 60, 380, 618 - 50, 350], fill=brow, width=16)
    elif mood in ("fier", "content"):
        d.line([406 - 55, 372, 406 + 55, 360], fill=brow, width=14)
        d.line([618 - 55, 360, 618 + 55, 372], fill=brow, width=14)
    elif mood == "pensif":
        d.line([618 - 55, 372, 618 + 55, 340], fill=brow, width=16)   # un sourcil relevé

    # --- bec ---
    if mood == "surpris":
        circle((512, 590), 26, fill=(224, 162, 74, 255))              # bec ouvert (o)
    else:
        d.polygon([(512, 556), (474, 606), (550, 606)], fill=(224, 162, 74, 255))

    # --- petite bouche (sourire / moue) ---
    if mood in ("content", "fier"):
        d.arc([452, 600, 572, 680], 20, 160, fill=(150, 90, 70, 255), width=12)   # sourire
    elif mood == "triste":
        d.arc([452, 640, 572, 700], 200, 340, fill=(150, 90, 70, 255), width=12)  # moue

    # --- extras selon humeur ---
    if mood == "triste":
        circle((470, 610), 16, fill=(120, 190, 235, 235))             # larme
    elif mood == "surpris":
        d.polygon([(720, 470), (700, 520), (740, 520)], fill=(120, 190, 235, 220))  # goutte de sueur
    elif mood in ("content", "fier"):
        for cx, cy in ((300, 360), (740, 380)):                       # étincelles
            d.line([cx - 16, cy, cx + 16, cy], fill=(255, 214, 100, 255), width=8)
            d.line([cx, cy - 16, cx, cy + 16], fill=(255, 214, 100, 255), width=8)
    elif mood == "pensif":
        for i, r in enumerate((10, 15, 20)):                          # bulles de pensée
            circle((720 + i * 46, 300 - i * 26), r, fill=(150, 145, 170, 220))

    # nœud pap
    bt = (124, 111, 224, 255)
    d.polygon([(512, 812), (430, 772), (430, 852)], fill=bt)
    d.polygon([(512, 812), (594, 772), (594, 852)], fill=bt)
    circle((512, 812), 24, fill=(90, 80, 180, 255))
    return img.resize((512, 512), Image.LANCZOS)

def main():
    os.makedirs(OUT, exist_ok=True)
    imgs = {}
    for m in MOODS:
        im = draw(m); im.save(os.path.join(OUT, m + ".png")); imgs[m] = im
    print("wrote", len(MOODS), "moods to", OUT)
    # planche de preview
    cols = len(MOODS); cell = 256
    board = Image.new("RGBA", (cols * cell, cell + 30), (250, 250, 252, 255))
    dd = ImageDraw.Draw(board)
    for i, m in enumerate(MOODS):
        board.alpha_composite(imgs[m].resize((cell, cell)), (i * cell, 0))
        dd.text((i * cell + 8, cell + 8), m, fill=(60, 60, 80, 255))
    prev = os.environ.get("MOOD_PREVIEW")
    if prev:
        board.convert("RGB").save(prev); print("preview ->", prev)

if __name__ == "__main__":
    main()
