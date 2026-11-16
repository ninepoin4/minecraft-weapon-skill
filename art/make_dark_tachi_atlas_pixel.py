"""Paint a 64x64 pixel-art material atlas for the 3D tachi.

The layout is exactly the 256x256 atlas divided by four, so the existing model
UVs (0..16, same proportions) keep working.  Every pixel is placed by hand with
a small fixed palette; there is no anti-aliasing or smooth gradient, so the 3D
model reads as pixel art like the rest of Minecraft.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT = ROOT / "src/main/resources/assets/weapon/textures/item"
OUT.mkdir(parents=True, exist_ok=True)

SIZE = 64

PAL = {
    ".": (0, 0, 0, 0),
    "k": (4, 3, 8, 255),        # obsidian near-black
    "b": (10, 8, 16, 255),      # obsidian base
    "d": (20, 15, 32, 255),     # obsidian facet
    "s": (36, 26, 56, 255),     # obsidian light facet
    "p": (56, 28, 96, 255),     # deep purple
    "P": (104, 52, 172, 255),   # purple
    "v": (158, 92, 236, 255),   # violet
    "V": (206, 166, 255, 255),  # pale violet
    "W": (246, 234, 255, 255),  # white-violet
    "g": (88, 60, 22, 255),     # gold shadow
    "G": (168, 124, 48, 255),   # gold
    "Y": (226, 184, 100, 255),  # gold light
    "y": (255, 236, 170, 255),  # gold pale
    "i": (24, 20, 30, 255),     # iron
    "I": (58, 48, 70, 255),     # iron light
    "r": (92, 8, 28, 255),      # red shadow
    "R": (190, 24, 58, 255),    # red
    "e": (255, 118, 138, 255),  # red light
    "h": (9, 7, 13, 255),       # wrap black
    "H": (32, 24, 42, 255),     # wrap band
    "u": (58, 44, 72, 255),     # wrap highlight
}

atlas = Image.new("RGBA", (SIZE, SIZE), PAL["."])


def px(x, y, c):
    atlas.putpixel((x, y), PAL[c])


def rect(x1, y1, x2, y2, c):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            px(x, y, c)


# ---------------------------------------------------------------- blade body
# x 0..11, y 0..55.  u=0 spine, u=11 cutting edge; v=0 guard, v=55 tip.
for y in range(56):
    # Wavy 1px hamon near the edge, alternating every four rows.
    hamon = 8 + ((y // 4) % 2)
    for x in range(12):
        if x == 11:
            c = "W" if y % 7 == 0 else "v" if y % 3 == 0 else "V"
        elif x == 10:
            c = "v" if y % 4 == 0 else "P"
        elif x == 9:
            c = "W" if x == hamon and y % 6 == 0 else "V" if x == hamon else "P"
        elif x == 8:
            c = "V" if x == hamon else "p"
        else:
            c = "b"
            if (x * 5 + y * 3) % 23 == 0:
                c = "d"
            if (x * 7 + y) % 41 == 0:
                c = "s"
            if (x + y * 2) % 37 == 0:
                c = "k"
            # faint dragon vein down the blade
            if x == 4 and (y % 9) < 4:
                c = "p"
            # rare sparkle in the obsidian
            if (x * 11 + y * 7) % 97 == 0:
                c = "V"
        px(x, y, c)

# ---------------------------------------------------------------- edge strip
# x 12..15, y 0..55.
for y in range(56):
    px(12, y, "p")
    px(13, y, "P" if y % 3 else "v")
    px(14, y, "v" if y % 4 else "V")
    px(15, y, "W" if y % 5 == 0 else "V")
# occasional bright chips
for y in range(3, 56, 11):
    px(15, y, "W")
    px(14, y + 1 if y + 1 < 56 else y, "V")

# ---------------------------------------------------------------- spine strip
# x 16..19, y 0..55.
for y in range(56):
    px(16, y, "k")
    px(17, y, "d" if y % 5 else "s")
    px(18, y, "s" if y % 4 == 0 else "d")
    px(19, y, "p" if y % 7 == 0 else "s")

# ---------------------------------------------------------------- tip
# x 20..27, y 0..7; bright towards the upper right.
for y in range(8):
    for x in range(8):
        d = x - y + 7
        if d < 3:
            c = "d"
        elif d < 6:
            c = "p"
        elif d < 9:
            c = "P"
        elif d < 11:
            c = "v"
        elif d < 13:
            c = "V"
        else:
            c = "W"
        px(20 + x, y, c)
for i in range(8):
    px(20 + i, 7 - i, "W")

# ---------------------------------------------------------------- handle
# x 28..39, y 0..23; diamond ito-maki, gold fuchi/kashira, two menuki.
for y in range(24):
    for x in range(12):
        c = "h"
        if (x + y) % 5 == 0 or (x - y) % 5 == 0:
            c = "H"
        if (x + y) % 10 == 0 and (x - y) % 10 == 0:
            c = "u"
        px(28 + x, y, c)
rect(28, 0, 39, 1, "G")
rect(28, 1, 39, 1, "Y")
rect(28, 22, 39, 23, "G")
rect(28, 22, 39, 22, "Y")
# menuki: two gold diamonds with a red eye
for cy in (9, 15):
    for (dx, dy) in ((0, -2), (-1, -1), (1, -1), (-2, 0), (2, 0),
                     (-1, 1), (1, 1), (0, 2)):
        px(34 + dx, cy + dy, "Y")
    px(34, cy, "R")
    px(34, cy - 1, "e")
# subtle cylindrical highlight
for y in range(2, 22):
    if y % 3 == 0:
        px(30, y, "u")

# ---------------------------------------------------------------- tsuba
# x 40..59, y 0..15; transparent outside an octagon.
cx, cy = 50, 8
r, cut = 9, 3
octagon = []
for x in range(40, 60):
    for y in range(0, 16):
        dx, dy = abs(x - cx), abs(y - cy)
        inside = dx <= r and dy <= r and dx + dy <= r + cut
        if not inside:
            continue
        if dx + dy >= r + cut - 1:
            c = "Y"
        elif dx + dy >= r + cut - 2:
            c = "G"
        elif dx <= 5 and dy <= 4:
            c = "i" if dx + dy >= 3 else "I"
        elif dx + dy <= 4:
            c = "G"
        else:
            c = "G" if (dx + dy) % 2 else "Y"
        px(x, y, c)
# gold rim accent
for x in range(40, 60):
    for y in range(0, 16):
        dx, dy = abs(x - cx), abs(y - cy)
        if dx + dy == r + cut - 1 and dx <= r and dy <= r:
            px(x, y, "y")
# dragon-eye gem at the centre
for (dx, dy, c) in ((0, -2, "r"), (-1, -1, "r"), (1, -1, "r"),
                    (-2, 0, "r"), (2, 0, "r"), (-1, 1, "r"), (1, 1, "r"),
                    (0, 2, "r"), (0, -1, "R"), (-1, 0, "R"), (1, 0, "R"),
                    (0, 1, "R"), (0, 0, "e")):
    px(cx + dx, cy + dy, c)
px(cx - 1, cy - 1, "W")
# vertical slit pupil
px(cx, cy - 2, "k")
px(cx, cy + 2, "k")

# ---------------------------------------------------------------- gold trim
# x 40..47, y 16..23.
for x in range(40, 48):
    for y in range(16, 24):
        if x in (40, 47):
            c = "g"
        elif x in (42, 45):
            c = "Y"
        elif x == 43:
            c = "y"
        else:
            c = "G"
        px(x, y, c)
for y in (17, 20):
    px(44, y, "y")

# ---------------------------------------------------------------- pommel
# x 48..55, y 16..23; transparent corners.
for x in range(48, 56):
    for y in range(16, 24):
        if (x in (48, 55) and y in (16, 23)):
            continue
        if x in (48, 55) or y in (16, 23):
            c = "G"
        elif x in (49, 54) or y in (17, 22):
            c = "Y"
        else:
            c = "i"
        px(x, y, c)
for (dx, dy, c) in ((0, 0, "e"), (-1, 0, "R"), (1, 0, "R"),
                    (0, -1, "R"), (0, 1, "R"), (-1, -1, "r"),
                    (1, 1, "r"), (0, -2, "W")):
    px(52 + dx, 20 + dy, c)

# ---------------------------------------------------------------- gem
# x 56..59, y 16..19.
gem = [["r", "R", "R", "r"],
       ["R", "e", "R", "R"],
       ["R", "R", "R", "r"],
       ["r", "R", "r", "r"]]
for y in range(4):
    for x in range(4):
        px(56 + x, 16 + y, gem[y][x])

# ---------------------------------------------------------------- glow
# x 60..63, y 16..19.
glow = [["V", "W", "W", "V"],
        ["W", "W", "V", "v"],
        ["W", "V", "v", "P"],
        ["V", "v", "P", "p"]]
for y in range(4):
    for x in range(4):
        px(60 + x, 16 + y, glow[y][x])

atlas.save(ART / "dark_tachi_3d_atlas_pixel.png")
atlas.save(OUT / "dark_tachi_3d_pixel.png")

# 8x nearest preview with a faint grid for inspection.
scale = 8
prev = atlas.resize((SIZE * scale, SIZE * scale), Image.Resampling.NEAREST)
d = ImageDraw.Draw(prev, "RGBA")
for i in range(0, SIZE + 1, 8):
    d.line([(i * scale, 0), (i * scale, SIZE * scale)], fill=(255, 255, 255, 28))
    d.line([(0, i * scale), (SIZE * scale, i * scale)], fill=(255, 255, 255, 28))
prev.save(ART / "dark_tachi_3d_atlas_pixel_preview.png")
print("pixel atlas written", atlas.size)
