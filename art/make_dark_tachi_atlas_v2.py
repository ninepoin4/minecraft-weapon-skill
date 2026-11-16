"""Paint a 256x256 material atlas built specifically for the 3D tachi.

This atlas is not derived from the 2D sprite.  It is laid out as a set of
material strips so many thin blade segments can sample a continuous hamon:

    x 0..48    blade wide face, u=0 spine -> u=47 cutting edge,
               v=0 base (tsuba) -> v=223 tip
    x 48..64   cutting-edge strip (bright violet -> white)
    x 64..80   spine strip
    x 80..112  tip cap / bright end
    x 112..160 handle wrap (diamond ito-maki, menuki)
    x 160..240 tsuba (transparent outside an octagon)
    x 160..192 gold trim (habaki / fuchi / kashira)
    x 192..224 pommel cap
    x 224..240 red dragon-eye gem
    x 240..256 violet glow

Pixel rects are written to art/dark_tachi_3d_layout_v2.json.  Java item models
use a 0..16 UV space, so divide pixel coordinates by 16 for Blockbench.
"""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT = ROOT / "src/main/resources/assets/weapon/textures/item"
ART.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

SS = 4                      # supersampling factor
SIZE = 256

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
OBSIDIAN_DARK = (5, 4, 10)
OBSIDIAN = (13, 10, 22)
OBSIDIAN_LIGHT = (34, 24, 56)
PURPLE_DEEP = (58, 30, 104)
PURPLE = (112, 56, 190)
VIOLET = (176, 108, 255)
WHITE_VIOLET = (246, 232, 255)
GOLD_DARK = (92, 64, 22)
GOLD = (176, 132, 54)
GOLD_LIGHT = (236, 196, 112)
GOLD_PALE = (255, 238, 176)
IRON = (22, 18, 28)
IRON_LIGHT = (58, 48, 70)
RED_DARK = (92, 8, 30)
RED = (206, 24, 62)
RED_LIGHT = (255, 118, 138)
WRAP = (11, 9, 15)
WRAP_BAND = (32, 25, 42)
WRAP_LIGHT = (56, 44, 70)


def region(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def finish(img, w, h):
    return img.resize((w, h), Image.Resampling.LANCZOS)


def add_grain(img, strength=18, light=True):
    """Overlay fine Gaussian grain (PIL only, no numpy)."""
    w, h = img.size
    noise = Image.effect_noise((w, h), strength).convert("L")
    if not light:
        noise = ImageChops.invert(noise)
    alpha = noise.point(lambda p: max(0, min(38, (p - 118) // 4)))
    layer = Image.new("RGBA", (w, h), (208, 190, 238, 0))
    layer.putalpha(alpha)
    return Image.alpha_composite(img, layer)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def blade_body(w=48, h=224):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 255))
    px = img.load()
    rng = random.Random(7613)

    # A slow S-curve for the hamon, sampled per row.
    for y in range(h4):
        v = y / (h4 - 1)
        hamon = 0.74 + 0.035 * math.sin(v * 9.2) + 0.018 * math.sin(v * 27.0 + 1.1)
        for x in range(w4):
            u = x / (w4 - 1)
            # Base is mostly black obsidian; only the last fifth turns violet.
            if u < 0.60:
                c = lerp(OBSIDIAN_DARK, OBSIDIAN_LIGHT, u / 0.60)
            elif u < 0.86:
                c = lerp(OBSIDIAN_LIGHT, (26, 16, 44), (u - 0.60) / 0.26)
            elif u < 0.94:
                c = lerp((26, 16, 44), PURPLE_DEEP, (u - 0.86) / 0.08)
            else:
                c = lerp(PURPLE_DEEP, VIOLET, (u - 0.94) / 0.06)

            # broad diagonal facets, like obsidian cleavage planes
            facet = math.sin((u * 6.3 + v * 2.1) * math.pi)
            facet2 = math.sin((u * 2.2 - v * 5.4) * math.pi + 0.7)
            f = max(0.0, facet * 0.55 + facet2 * 0.45)
            c = lerp(c, OBSIDIAN_LIGHT, f * 0.12)
            c = lerp(c, (2, 2, 4), max(0.0, -facet) * 0.38)

            # faint dragon vein
            vein = 0.42 + 0.035 * math.sin(v * 6.0 + 2.0)
            if abs(u - vein) < 0.008:
                c = lerp(c, (92, 46, 150), 0.45)

            # hamon glow: a soft violet band, then a pale lavender line
            d = abs(u - hamon)
            if d < 0.060:
                c = lerp(c, (70, 34, 120), (0.060 - d) / 0.060 * 0.50)
            if d < 0.012:
                c = lerp(c, (196, 154, 255), (0.012 - d) / 0.012)
            if d < 0.003:
                c = lerp(c, (240, 224, 255), 0.65)

            # bright cutting edge
            if u > 0.95:
                c = lerp(c, (226, 196, 255), (u - 0.95) / 0.05)

            # tiny per-pixel jitter
            j = rng.randint(-3, 3)
            px[x, y] = (max(0, c[0] + j), max(0, c[1] + j), max(0, c[2] + j), 255)

    # hairline cracks
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(9):
        x = rng.uniform(0.08, 0.78) * w4
        y = rng.uniform(0.0, 0.8) * h4
        pts = [(x, y)]
        for _ in range(rng.randint(3, 6)):
            x += rng.uniform(-0.04, 0.05) * w4
            y += rng.uniform(0.03, 0.09) * h4
            pts.append((x, y))
        d.line(pts, fill=(2, 2, 5, 110), width=max(1, SS // 2))

    # starry glints near the edge
    for _ in range(90):
        x = rng.uniform(0.58, 1.0) * w4
        y = rng.uniform(0, 1) * h4
        r = rng.choice([1, 1, 1, 2]) * SS // 2
        col = rng.choice([(220, 200, 255), (180, 140, 255), (255, 255, 255)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (rng.randint(90, 200),))

    # very soft vertical sheen down the middle of the blade
    sheen = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.rectangle([int(w4 * 0.30), 0, int(w4 * 0.40), h4], fill=(90, 70, 130, 20))
    sd.rectangle([int(w4 * 0.56), 0, int(w4 * 0.61), h4], fill=(120, 90, 180, 16))
    img = Image.alpha_composite(img, sheen.filter(ImageFilter.GaussianBlur(SS * 2)))
    return add_grain(img, 12)


def blade_edge(w=16, h=224):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 255))
    px = img.load()
    rng = random.Random(45)
    for y in range(h4):
        v = y / (h4 - 1)
        for x in range(w4):
            u = x / (w4 - 1)
            if u < 0.45:
                c = lerp((44, 22, 78), (108, 52, 180), u / 0.45)
            elif u < 0.72:
                c = lerp((108, 52, 180), (184, 112, 255), (u - 0.45) / 0.27)
            elif u < 0.9:
                c = lerp((184, 112, 255), (238, 214, 255), (u - 0.72) / 0.18)
            else:
                c = lerp((238, 214, 255), (255, 255, 255), (u - 0.9) / 0.1)
            # slow shimmer along the length
            shimmer = 0.5 + 0.5 * math.sin(v * 41.0 + u * 3.0)
            c = lerp(c, (255, 255, 255), shimmer * 0.08)
            j = rng.randint(-4, 4)
            px[x, y] = (max(0, c[0] + j), max(0, c[1] + j), max(0, c[2] + j), 255)

    # tiny nicks and bright chips on the very edge
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(rng.randint(6, 20), h4, rng.randint(28, 46)):
        d.line([(w4 - SS, y), (w4 - 3 * SS, y + rng.randint(-2, 2))],
               fill=(70, 40, 110, 170), width=max(1, SS // 2))
    for _ in range(50):
        x = rng.uniform(0.55, 1.0) * w4
        y = rng.uniform(0, 1) * h4
        r = rng.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(120, 230)))
    return add_grain(img, 8)


def blade_spine(w=16, h=224):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (9, 8, 14, 255))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, int(w4 * 0.10), h4], fill=(44, 38, 54, 255))
    d.rectangle([int(w4 * 0.10), 0, int(w4 * 0.16), h4], fill=(72, 62, 88, 255))
    d.rectangle([int(w4 * 0.16), 0, int(w4 * 0.22), h4], fill=(30, 26, 38, 255))
    d.rectangle([int(w4 * 0.78), 0, w4, h4], fill=(24, 16, 40, 255))
    d.rectangle([w4 - int(w4 * 0.10), 0, w4, h4], fill=(52, 30, 84, 255))
    rng = random.Random(9)
    for _ in range(60):
        y = rng.uniform(0, h4)
        x1 = rng.uniform(0, w4 * 0.5)
        x2 = x1 + rng.uniform(2, 10) * SS
        d.line([(x1, y), (x2, y + rng.uniform(-2, 2))], fill=(90, 76, 110, 70), width=1)
    return add_grain(img, 10)


def blade_tip(w=32, h=32):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 255))
    px = img.load()
    rng = random.Random(33)
    for y in range(h4):
        v = y / (h4 - 1)
        for x in range(w4):
            u = x / (w4 - 1)
            base = lerp((8, 6, 14), (70, 36, 120), (u * 0.55 + (1 - v) * 0.45))
            base = lerp(base, (214, 184, 255), max(0.0, (1 - v) - 0.35) * 0.9)
            facet = math.sin((u * 5 + v * 7) * math.pi)
            base = lerp(base, (255, 250, 255), max(0.0, facet) * 0.25)
            j = rng.randint(-3, 3)
            px[x, y] = (max(0, base[0] + j), max(0, base[1] + j), max(0, base[2] + j), 255)
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(w4 * 0.15, h4 * 0.85), (w4 * 0.85, h4 * 0.15)],
           fill=(255, 255, 255, 200), width=SS)
    d.line([(w4 * 0.2, h4 * 0.95), (w4 * 0.95, h4 * 0.2)],
           fill=(180, 120, 255, 140), width=SS * 2)
    return add_grain(img, 8)


def handle(w=48, h=96):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), WRAP + (255,))
    d = ImageDraw.Draw(img, "RGBA")

    # soft cylindrical shading
    for x in range(w4):
        u = x / (w4 - 1)
        shade = 0.55 + 0.45 * math.cos((u - 0.5) * math.pi)
        c = lerp((5, 4, 8), (26, 20, 34), shade)
        d.line([(x, 0), (x, h4)], fill=c + (255,))

    # diamond ito-maki: two crossing families of bands
    for direction in (1, -1):
        step = 7 * SS
        for offset in range(-h4, w4 + h4, step):
            pts = []
            if direction == 1:
                for t in range(0, h4 + 1, SS * 4):
                    pts.append((offset + t, t))
            else:
                for t in range(0, h4 + 1, SS * 4):
                    pts.append((offset + t, h4 - t))
            if len(pts) > 1:
                d.line(pts, fill=WRAP_BAND + (255,), width=3 * SS)
                shifted = [(x + SS, y) for x, y in pts]
                d.line(shifted, fill=WRAP_LIGHT + (160,), width=SS)

    # gold fuchi and kashira bands (the model also has separate 3D fittings)
    d.rectangle([0, 0, w4, 5 * SS], fill=GOLD + (255,))
    d.rectangle([0, SS, w4, 3 * SS], fill=GOLD_LIGHT + (255,))
    d.rectangle([0, h4 - 5 * SS, w4, h4], fill=GOLD + (255,))
    d.rectangle([0, h4 - 4 * SS, w4, h4 - 2 * SS], fill=GOLD_PALE + (255,))

    # two gold menuki with a red eye
    for cy in (h4 * 0.42, h4 * 0.60):
        cx = w4 * 0.50
        pts = [(cx, cy - 7 * SS), (cx + 5 * SS, cy), (cx, cy + 7 * SS), (cx - 5 * SS, cy)]
        d.polygon(pts, fill=GOLD + (255,))
        d.polygon([(cx, cy - 4 * SS), (cx + 3 * SS, cy), (cx, cy + 4 * SS), (cx - 3 * SS, cy)],
                  fill=RED + (255,))
        d.ellipse([cx - SS, cy - 2 * SS, cx + SS, cy], fill=(255, 220, 230, 255))

    # subtle vertical highlight
    d.rectangle([int(w4 * 0.12), 0, int(w4 * 0.20), h4], fill=(120, 96, 160, 22))
    return add_grain(img, 10)


def octagon(cx, cy, r, cut):
    return [
        (cx - r + cut, cy - r), (cx + r - cut, cy - r),
        (cx + r, cy - r + cut), (cx + r, cy + r - cut),
        (cx + r - cut, cy + r), (cx - r + cut, cy + r),
        (cx - r, cy + r - cut), (cx - r, cy - r + cut),
    ]


def tsuba(w=80, h=64):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = w4 / 2, h4 / 2
    outer = octagon(cx, cy, 30 * SS, 9 * SS)

    # gold outer plate with a bevel
    d.polygon(outer, fill=GOLD + (255,))
    d.polygon(octagon(cx, cy, 29 * SS, 8.5 * SS), fill=GOLD_LIGHT + (255,))
    d.polygon(octagon(cx, cy, 27 * SS, 8 * SS), fill=GOLD + (255,))
    # engraved dragon scales around the rim
    for ring in (23.5, 20.0):
        pts = octagon(cx, cy, ring * SS, 7 * SS)
        d.line(pts + [pts[0]], fill=(255, 232, 160, 150), width=SS)
    for i in range(14):
        a = math.pi * 2 * i / 14
        x1 = cx + math.cos(a) * 20.5 * SS
        y1 = cy + math.sin(a) * 20.5 * SS
        x2 = cx + math.cos(a) * 23.0 * SS
        y2 = cy + math.sin(a) * 23.0 * SS
        d.line([(x1, y1), (x2, y2)], fill=(90, 62, 20, 160), width=SS)

    # dark iron inner field
    d.polygon(octagon(cx, cy, 19 * SS, 6 * SS), fill=IRON + (255,))
    d.polygon(octagon(cx, cy, 18 * SS, 5.5 * SS), fill=(34, 26, 44, 255))
    # faint concentric engraving
    d.polygon(octagon(cx, cy, 14.5 * SS, 4 * SS), outline=(110, 78, 30, 170), width=SS)

    # dragon-eye gem: red faceted oval with a vertical slit
    gr = 9 * SS
    d.ellipse([cx - gr - SS, cy - gr - SS, cx + gr + SS, cy + gr + SS], fill=GOLD_DARK + (255,))
    d.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=RED_DARK + (255,))
    d.ellipse([cx - gr * 0.82, cy - gr * 0.82, cx + gr * 0.82, cy + gr * 0.82], fill=RED + (255,))
    d.ellipse([cx - gr * 0.5, cy - gr * 0.5, cx + gr * 0.5, cy + gr * 0.5], fill=RED_LIGHT + (255,))
    # slit pupil
    d.polygon([(cx - SS * 0.8, cy - gr * 0.62), (cx + SS * 0.8, cy - gr * 0.62),
               (cx + SS * 0.3, cy + gr * 0.58), (cx - SS * 0.3, cy + gr * 0.58)],
              fill=(30, 2, 8, 255))
    d.ellipse([cx - gr * 0.62, cy - gr * 0.66, cx - gr * 0.22, cy - gr * 0.34],
              fill=(255, 240, 245, 235))
    # tiny gold prongs
    for a in (-0.6, 0.6, math.pi - 0.6, math.pi + 0.6):
        d.line([(cx - math.cos(a) * gr, cy - math.sin(a) * gr),
                (cx - math.cos(a) * (gr + 2.2 * SS), cy - math.sin(a) * (gr + 2.2 * SS))],
               fill=GOLD_PALE + (255,), width=SS)
    return add_grain(img, 8)


def gold_trim(w=32, h=32):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), GOLD + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(w4):
        u = x / (w4 - 1)
        shade = 0.35 + 0.65 * (1.0 - abs(u - 0.42) * 1.7)
        c = lerp(GOLD_DARK, GOLD_PALE, max(0.0, min(1.0, shade)))
        d.line([(x, 0), (x, h4)], fill=c + (255,))
    d.rectangle([0, 0, w4, SS], fill=GOLD_PALE + (255,))
    d.rectangle([0, h4 - SS, w4, h4], fill=GOLD_DARK + (255,))
    d.line([(w4 * 0.42, 0), (w4 * 0.42, h4)], fill=(255, 246, 200, 220), width=SS)
    d.line([(w4 * 0.30, 0), (w4 * 0.30, h4)], fill=(120, 86, 28, 170), width=SS)
    # a row of tiny rivets
    for i in range(3):
        y = h4 * (0.25 + i * 0.25)
        d.ellipse([w4 * 0.66 - SS, y - SS, w4 * 0.66 + SS, y + SS], fill=GOLD_PALE + (255,))
    return add_grain(img, 6)


def pommel(w=32, h=32):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([SS, SS, w4 - SS, h4 - SS], radius=5 * SS, fill=GOLD_DARK + (255,))
    d.rounded_rectangle([2 * SS, 2 * SS, w4 - 2 * SS, h4 - 2 * SS], radius=4 * SS, fill=GOLD + (255,))
    d.rounded_rectangle([3 * SS, 3 * SS, w4 - 3 * SS, h4 - 3 * SS], radius=3 * SS, fill=GOLD_LIGHT + (255,))
    d.rounded_rectangle([6 * SS, 6 * SS, w4 - 6 * SS, h4 - 6 * SS], radius=2 * SS, fill=IRON + (255,))
    cx, cy = w4 / 2, h4 / 2
    gr = 5 * SS
    d.ellipse([cx - gr, cy - gr, cx + gr, cy + gr], fill=RED_DARK + (255,))
    d.ellipse([cx - gr * 0.8, cy - gr * 0.8, cx + gr * 0.8, cy + gr * 0.8], fill=RED + (255,))
    d.ellipse([cx - gr * 0.42, cy - gr * 0.5, cx - gr * 0.05, cy - gr * 0.2],
              fill=(255, 230, 238, 240))
    d.rectangle([cx - SS, cy - gr, cx + SS, cy + gr], fill=(40, 2, 10, 220))
    return add_grain(img, 6)


def gem(w=16, h=16):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = w4 / 2, h4 / 2
    for r in range(7 * SS, 0, -SS):
        t = 1.0 - (r / (7 * SS))
        c = lerp(RED_DARK, RED_LIGHT, t)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c + (255,))
    # facets
    for a in range(0, 360, 45):
        x = cx + math.cos(math.radians(a)) * 6.4 * SS
        y = cy + math.sin(math.radians(a)) * 6.4 * SS
        d.line([(cx, cy), (x, y)], fill=(255, 190, 205, 70), width=SS)
    d.ellipse([cx - 4 * SS, cy - 4 * SS, cx - 1.2 * SS, cy - 1.2 * SS],
              fill=(255, 240, 245, 240))
    return add_grain(img, 6)


def glow(w=16, h=16):
    w4, h4 = w * SS, h * SS
    img = Image.new("RGBA", (w4, h4), (0, 0, 0, 0))
    px = img.load()
    cx, cy = (w4 - 1) / 2, (h4 - 1) / 2
    for y in range(h4):
        for x in range(w4):
            dist = math.hypot(x - cx, y - cy) / (w4 * 0.5)
            a = max(0.0, 1.0 - dist)
            a = a * a
            px[x, y] = (230, 200, 255, int(255 * a))
    return img.filter(ImageFilter.GaussianBlur(SS))


def main():
    atlas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    pieces = {
        "blade_body": (blade_body(), 48, 224, (0, 0)),
        "blade_edge": (blade_edge(), 16, 224, (48, 0)),
        "blade_spine": (blade_spine(), 16, 224, (64, 0)),
        "blade_tip": (blade_tip(), 32, 32, (80, 0)),
        "handle": (handle(), 48, 96, (112, 0)),
        "tsuba": (tsuba(), 80, 64, (160, 0)),
        "gold_trim": (gold_trim(), 32, 32, (160, 64)),
        "pommel": (pommel(), 32, 32, (192, 64)),
        "gem": (gem(), 16, 16, (224, 64)),
        "glow": (glow(), 16, 16, (240, 64)),
    }

    layout = {"size": [SIZE, SIZE], "regions": {}, "orientation": {}}
    for name, (img, w, h, pos) in pieces.items():
        if img.size != (w * SS, h * SS):
            img = img.resize((w * SS, h * SS), Image.Resampling.LANCZOS)
        atlas.alpha_composite(finish(img, w, h), pos)
        layout["regions"][name] = [pos[0], pos[1], pos[0] + w, pos[1] + h]

    layout["orientation"] = {
        "blade_body": "u 0 = spine, u 47 = cutting edge; v 0 = base/tsuba, v 223 = tip",
        "blade_edge": "u 0 = inner side, u 15 = bright cutting edge; v runs base -> tip",
        "blade_spine": "u 0 = outer bevel, u 15 = blade body side",
        "blade_tip": "top of the region = brightest tip end",
        "uv_note": "Java item UV space is 0..16; divide pixel coords by 16 (256 / 16).",
    }

    atlas.save(ART / "dark_tachi_3d_atlas_v2.png")
    atlas.save(OUT / "dark_tachi_3d_v2.png")
    (ART / "dark_tachi_3d_layout_v2.json").write_text(
        json.dumps(layout, indent=2, ensure_ascii=False), encoding="utf-8")

    # Labeled layout preview at 2x.
    prev = atlas.resize((SIZE * 2, SIZE * 2), Image.Resampling.NEAREST)
    d = ImageDraw.Draw(prev, "RGBA")
    for name, rect in layout["regions"].items():
        x1, y1, x2, y2 = [v * 2 for v in rect]
        d.rectangle([x1, y1, x2 - 1, y2 - 1], outline=(255, 80, 80, 220), width=1)
        d.text((x1 + 2, y1 + 2), name, fill=(255, 255, 0, 255))
    prev.save(ART / "dark_tachi_3d_atlas_v2_labeled.png")

    print("atlas written", atlas.size)
    print(json.dumps(layout["regions"], indent=1))


if __name__ == "__main__":
    main()
