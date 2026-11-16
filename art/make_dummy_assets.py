"""Generate the training dummy's entity texture and its placement item icon.

The entity texture reuses the vanilla zombie UV layout (the dummy renders with
the zombie humanoid model, arms out) and recolours it into straw, wood and a
jack-o'-lantern head.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
VANILLA = ART / "vanilla/zombie.png"
ENTITY_OUT = ROOT / "src/main/resources/assets/weapon/textures/entity/training_dummy.png"
ITEM_OUT = ROOT / "src/main/resources/assets/weapon/textures/item/training_dummy.png"
ENTITY_OUT.parent.mkdir(parents=True, exist_ok=True)

ZOMBIE = Image.open(VANILLA).convert("RGBA")
SRC = ZOMBIE.load()
OUT = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
DST = OUT.load()

PUMPKIN = (232, 138, 38)
STRAW = (198, 158, 70)
ARM = (186, 146, 62)
WOOD = (108, 74, 40)
DARK_WOOD = (82, 55, 30)


def tint(pixel, base, lo=0.52, hi=1.28):
    r, g, b, a = pixel
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    factor = lo + (hi - lo) * lum
    return (min(255, int(base[0] * factor)),
            min(255, int(base[1] * factor)),
            min(255, int(base[2] * factor)), a)


def in_rect(x, y, x0, y0, x1, y1):
    return x0 <= x < x1 and y0 <= y < y1


for y in range(64):
    for x in range(64):
        src = SRC[x, y]
        if src[3] == 0:
            continue

        if in_rect(x, y, 0, 0, 32, 16):
            # Head: pumpkin, preserving the vanilla skin shading.
            dst = tint(src, PUMPKIN)
        elif in_rect(x, y, 16, 16, 40, 32):
            # Body: straw shirt.
            dst = tint(src, STRAW)
        elif in_rect(x, y, 40, 16, 56, 32):
            # Arm: straw sleeve, dark wooden hand at the bottom 4 pixels.
            dst = tint(src, WOOD if y >= 28 else ARM)
        elif in_rect(x, y, 0, 16, 16, 32):
            # Leg: wooden post.
            dst = tint(src, DARK_WOOD)
        elif in_rect(x, y, 32, 0, 64, 16):
            # Hat layer: leave empty.
            continue
        else:
            continue
        DST[x, y] = dst

# Pineapple... pumpkin ridges on the head sides/back.
for x, y in [(1, 10), (2, 11), (3, 12), (4, 13), (5, 14), (6, 15),
             (19, 9), (18, 10), (17, 11), (16, 12), (0, 9), (7, 15)]:
    if DST[x, y][3] > 0:
        DST[x, y] = (176, 96, 24, DST[x, y][3])

# Jack-o'-lantern face on the head front (UV 8..16, 8..16).
BLACK = (32, 22, 12, 255)
NOSE = (150, 76, 20, 255)
GREEN = (74, 132, 48, 255)
for x, y in [(11, 8), (12, 8), (11, 9), (12, 9)]:
    DST[x, y] = GREEN
for x, y in [(9, 10), (10, 10), (10, 11),
             (13, 10), (14, 10), (13, 11),
             (9, 14), (10, 13), (11, 14), (12, 13), (13, 14)]:
    DST[x, y] = BLACK
for x, y in [(11, 12), (12, 12)]:
    DST[x, y] = NOSE

# Rope belt across the body front (UV 20..28, 20..32).
ROPE = (92, 60, 30, 255)
for x in range(20, 28):
    DST[x, 26] = ROPE
    DST[x, 27] = ROPE
for x, y in [(23, 26), (24, 26), (23, 27), (24, 27), (23, 28), (24, 29)]:
    DST[x, y] = ROPE

# A few straw strokes on the body and arms.
STRAW_DARK = (150, 112, 48, 255)
for x, y in [(21, 22), (21, 24), (26, 23), (26, 25), (22, 30), (25, 29),
             (44, 21), (46, 23), (45, 26), (47, 27)]:
    if DST[x, y][3] > 0:
        DST[x, y] = STRAW_DARK

OUT.save(ENTITY_OUT)
OUT.resize((512, 512), Image.Resampling.NEAREST).save(ART / "training_dummy_entity_preview.png")

# --------------------------------------------------------------------------
# Placement item icon: pumpkin head on a straw cross.
# --------------------------------------------------------------------------
PALETTE = {
    ".": (0, 0, 0, 0),
    "G": (74, 132, 48, 255),    # stem
    "H": (168, 86, 22, 255),    # pumpkin outline
    "O": (238, 146, 38, 255),   # pumpkin
    "E": (34, 22, 12, 255),     # eye
    "#": (52, 32, 14, 255),     # mouth / base
    "|": (116, 78, 40, 255),    # wooden post
    "=": (206, 172, 92, 255),   # straw crossbar
}

ICON = [
    "................",
    ".......G........",
    ".....HHHHH......",
    "....HOOOOOH.....",
    "....HOEOEOH.....",
    "....HOOOOOH.....",
    ".....HO#OH......",
    "......HHH.......",
    ".......|........",
    "..=====|=====...",
    ".......|........",
    ".......|........",
    ".......|........",
    ".......|........",
    ".......|........",
    "......###.......",
]

img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
px = img.load()
for y, row in enumerate(ICON):
    assert len(row) == 16, (y, len(row))
    for x, ch in enumerate(row):
        px[x, y] = PALETTE[ch]
img.save(ITEM_OUT)
img.resize((320, 320), Image.Resampling.NEAREST).save(ART / "training_dummy_item_preview.png")

print("wrote", ENTITY_OUT)
print("wrote", ITEM_OUT)
