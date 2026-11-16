"""Draw the three new weapon sprites in the vanilla 16x16 item style.

- alloy_sword: steel blade with copper/gold alloy bands, gold crossguard.
- iron_rapier: thin steel blade, chain-link guard, dark grip.
- blaze_sword: 8-frame animated fiery blade (16x128 strip + .mcmeta).
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT = ROOT / "src/main/resources/assets/weapon/textures/item"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

SIZE = 16

DARK_OUTLINE = (10, 9, 8, 255)


def render(grid, palette, out_path, preview_path=None, scale=20):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        assert len(row) == SIZE, (y, len(row), row)
        for x, ch in enumerate(row):
            px[x, y] = palette[ch]
    img.save(out_path)
    if preview_path:
        img.resize((SIZE * scale, SIZE * scale), Image.Resampling.NEAREST).save(preview_path)
    return img


def grid_from(rows):
    return [list(r) for r in rows]


def put(grid, x, y, ch):
    if 0 <= x < SIZE and 0 <= y < SIZE:
        grid[y][x] = ch


# --------------------------------------------------------------------------
# Alloy sword
# --------------------------------------------------------------------------
ALLOY_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": DARK_OUTLINE,
    "l": (228, 236, 242, 255),
    "s": (158, 168, 176, 255),
    "p": (198, 118, 72, 255),
    "P": (244, 178, 126, 255),
    "d": (116, 70, 46, 255),
    "y": (222, 176, 64, 255),
    "Y": (252, 224, 132, 255),
    "n": (134, 94, 30, 255),
    "k": (34, 30, 28, 255),
    "K": (64, 58, 52, 255),
    "w": (250, 250, 240, 255),
}

alloy = grid_from([
    "................",
    "...............Y",
    ".............lwY",
    "............lldo",
    "...........lPdo.",
    "..........lPdo..",
    ".........lPdo...",
    "........lPdo....",
    ".......lPdo.....",
    "..y...lYdo......",
    "..Yy.lPdo.......",
    "....yYpdo.......",
    ".....yYy........",
    "...ko.yyn.......",
    "..kK...yY.......",
    ".oky............",
])

render(alloy, ALLOY_PALETTE, OUT / "alloy_sword.png", ART / "alloy_sword_preview.png")

# --------------------------------------------------------------------------
# Iron rapier
# --------------------------------------------------------------------------
RAPIER_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (10, 12, 14, 255),
    "l": (226, 236, 242, 255),
    "s": (152, 164, 174, 255),
    "d": (74, 84, 94, 255),
    "c": (196, 202, 208, 255),
    "C": (98, 106, 114, 255),
    "k": (30, 30, 32, 255),
    "K": (62, 62, 66, 255),
    "p": (146, 154, 162, 255),
    "w": (250, 252, 255, 255),
}

rapier = grid_from([
    "................",
    "...............w",
    ".............lwl",
    "............lldo",
    "...........lsdo.",
    "..........lsdo..",
    ".........lsdo...",
    "........lsdo....",
    ".......lsdo.....",
    "..c...lsdo......",
    "..Cc.lsdo.......",
    "....cCsdo.......",
    ".....cCo........",
    "...ko.cC........",
    "..kK...c........",
    ".okp............",
])

render(rapier, RAPIER_PALETTE, OUT / "iron_rapier.png", ART / "iron_rapier_preview.png")

# --------------------------------------------------------------------------
# Blaze sword: 8 animated frames
# --------------------------------------------------------------------------
BLAZE_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (12, 8, 6, 255),
    "W": (255, 248, 206, 255),   # white-hot
    "F": (255, 214, 64, 255),    # bright flame
    "f": (246, 132, 24, 255),    # orange flame
    "m": (170, 44, 12, 255),     # deep red flame
    "r": (92, 18, 8, 255),       # ember / scar
    "g": (232, 154, 42, 255),    # blaze gold
    "G": (255, 208, 108, 255),   # light blaze gold
    "n": (146, 82, 20, 255),     # dark blaze gold
    "k": (38, 30, 26, 255),      # grip
    "K": (66, 54, 46, 255),      # grip highlight
}

BLAZE_FRAMES = 8

# Static base: blade body is written with flame placeholders F/f/m; the
# animation recolours them along the diagonal each frame.
blaze_base = grid_from([
    "................",
    "...............W",
    ".............WFo",
    "............Ffmo",
    "...........Ffmo.",
    "..........Ffmo..",
    ".........Ffmo...",
    "........Ffmo....",
    ".......Ffmo.....",
    "......Ffmo......",
    ".....Ffmo.......",
    "....Ffmo........",
    "...Ffmo.........",
    "..GgGgo.........",
    ".GkKkgo.........",
    "oGkGo...........",
])

# Diagonal index per pixel, used to phase the flame colours.
diag = {}
for y in range(SIZE):
    for x in range(SIZE):
        diag[(x, y)] = (x - y) % 16

FLAME_CORE = ["F", "f", "m", "r"]

strip = Image.new("RGBA", (SIZE, SIZE * BLAZE_FRAMES), (0, 0, 0, 0))
frame_images = []
for frame in range(BLAZE_FRAMES):
    g = [row[:] for row in blaze_base]
    for y in range(SIZE):
        for x in range(SIZE):
            ch = g[y][x]
            if ch == "F":
                # Outer edge stays hot; a white-hot wave travels up the blade.
                g[y][x] = "W" if (diag[(x, y)] + frame * 2) % 7 == 0 else "F"
            elif ch == "f":
                # Molten core flows along the blade.
                g[y][x] = FLAME_CORE[(diag[(x, y)] + frame * 2) % len(FLAME_CORE)]
            elif ch == "m":
                # Inner edge stays dark red, with occasional embers.
                g[y][x] = "r" if (diag[(x, y)] + frame) % 3 == 0 else "m"

    # Little flames licking off the top edge of the blade.
    flame_spots = [(13, 3), (11, 5), (9, 6), (7, 8), (5, 10), (3, 11)]
    for idx, (fx, fy) in enumerate(flame_spots):
        phase = (frame + idx) % 3
        dx, dy = [(0, 0), (1, -1), (0, -1)][phase]
        tx, ty = fx + dx, fy + dy
        if 0 <= tx < SIZE and 0 <= ty < SIZE and g[ty][tx] == ".":
            g[ty][tx] = "F" if phase == 0 else "f"

    # Flickering tip.
    if frame % 3 == 0:
        put(g, 15, 1, "F")
    else:
        put(g, 15, 1, "W")

    # A couple of drifting embers just off the blade.
    embers = [
        (12, 6), (10, 4), (8, 8), (13, 9), (6, 11), (14, 3),
    ]
    for i in range(2):
        ex, ey = embers[(frame * 2 + i) % len(embers)]
        if 0 <= ex < SIZE and 0 <= ey < SIZE and g[ey][ex] == ".":
            g[ey][ex] = "F" if i == 0 else "f"

    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y in range(SIZE):
        for x in range(SIZE):
            px[x, y] = BLAZE_PALETTE[g[y][x]]
    strip.alpha_composite(img, (0, frame * SIZE))
    frame_images.append(img)

strip.save(OUT / "blaze_sword.png")
frame_images[0].resize((SIZE * 20, SIZE * 20), Image.Resampling.NEAREST).save(ART / "blaze_frame0.png")
# Contact sheet: 4 columns x 2 rows.
sheet = Image.new("RGBA", (SIZE * 4, SIZE * 2), (24, 20, 20, 255))
for i, img in enumerate(frame_images):
    sheet.alpha_composite(img, ((i % 4) * SIZE, (i // 4) * SIZE))
sheet.resize((SIZE * 4 * 10, SIZE * 2 * 10), Image.Resampling.NEAREST).save(ART / "blaze_frames.png")
frame_images[0].save(ART / "blaze_preview.gif", save_all=True,
                     append_images=frame_images[1:], duration=100, loop=0)

(OUT / "blaze_sword.png.mcmeta").write_text(
    json.dumps({"animation": {"frametime": 2}}, indent=2) + "\n", encoding="utf-8"
)

# --------------------------------------------------------------------------
# Greatsword: a broad 5px-wide blade for the 1.5x-scaled held model.
# --------------------------------------------------------------------------
GREATSWORD_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (8, 10, 12, 255),
    "w": (250, 252, 255, 255),
    "l": (226, 235, 242, 255),
    "s": (150, 162, 172, 255),
    "d": (86, 98, 108, 255),
    "D": (48, 56, 64, 255),
    "G": (130, 136, 142, 255),
    "g": (72, 78, 84, 255),
    "k": (30, 30, 32, 255),
    "K": (62, 62, 66, 255),
    "n": (96, 102, 108, 255),
}

greatsword = grid_from([
    "................",
    "...............w",
    ".............lwo",
    "............lsdo",
    "...........lsDso",
    "..........lsDso.",
    ".........lsDso..",
    "........lsDso...",
    ".......lsDso....",
    "......lsDso.....",
    ".....lsDso......",
    "....lsDso.......",
    "...lsDso........",
    ".GGGGGGGo.......",
    "GgkKkKgo........",
    "oGkKo...........",
])

render(greatsword, GREATSWORD_PALETTE, OUT / "greatsword.png", ART / "greatsword_preview.png")

print("wrote", OUT / "alloy_sword.png")
print("wrote", OUT / "iron_rapier.png")
print("wrote", OUT / "greatsword.png")
print("wrote", OUT / "blaze_sword.png", strip.size)
print("wrote", OUT / "blaze_sword.png.mcmeta")
