"""Draw the two reaper-scythe sprites.

32x32 hand-built silhouette based on the reference: a long slender snath with a
dark pommel, a dark angular socket with a short back spike, and a broad eagle-
wing blade. The blade's top edge runs almost straight from the socket to the tip
while the underside is concave, so it reads as a curved scythe blade rather than
a round hook or a flat farming blade.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT = ROOT / "src/main/resources/assets/weapon/textures/item"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

SIZE = 32

SICKLE_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (10, 12, 16, 255),
    "w": (245, 250, 252, 255),
    "l": (196, 218, 226, 255),
    "s": (142, 170, 182, 255),
    "d": (84, 110, 124, 255),
    "h": (126, 82, 44, 255),
    "H": (76, 46, 26, 255),
    "k": (118, 124, 134, 255),
    "K": (58, 62, 70, 255),
}

HELL_PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (8, 6, 10, 255),
    "w": (255, 234, 160, 255),
    "l": (255, 156, 64, 255),
    "s": (172, 50, 34, 255),
    "d": (64, 26, 74, 255),
    "h": (86, 38, 32, 255),
    "H": (44, 18, 16, 255),
    "k": (128, 108, 124, 255),
    "K": (58, 48, 66, 255),
}

# Blade outline: top edge from the tip (left) to the socket (right), then back
# along the concave underside. This is the reference's eagle-wing shape.
BLADE_POLYGON = [
    (3.0, 4.0), (6.0, 2.0), (10.0, 1.0), (14.0, 1.0),
    (18.0, 2.0), (21.0, 4.0), (23.0, 6.0), (24.5, 8.0),
    (25.0, 12.0), (22.0, 11.0), (19.0, 9.0), (16.0, 7.5),
    (12.0, 6.0), (8.0, 5.0), (5.0, 4.5),
]

# Angular metal socket over the blade base, plus a short back spike.
SOCKET_POLYGON = [
    (22.5, 7.0), (26.0, 6.5), (27.5, 9.5), (26.5, 13.0),
    (23.0, 13.5), (21.5, 10.5),
]
SPIKE_START = (25.0, 8.0)
SPIKE_END = (29.0, 3.5)

# Long snath from the socket to the dark pommel at the lower left.
SHAFT_START = (24.0, 12.0)
SHAFT_END = (4.5, 29.5)
POMMEL = (4.5, 29.5)


def raster_polygon(points):
    img = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(img).polygon(points, fill=255)
    px = img.load()
    return {(x, y) for y in range(SIZE) for x in range(SIZE) if px[x, y] > 0}


def raster_capsule(start, end, radius):
    sx, sy = start
    ex, ey = end
    vx, vy = ex - sx, ey - sy
    length_sq = vx * vx + vy * vy
    mask = set()
    for y in range(SIZE):
        for x in range(SIZE):
            px = x + 0.5 - sx
            py = y + 0.5 - sy
            t = max(0.0, min(1.0, (px * vx + py * vy) / length_sq))
            near_x = sx + vx * t
            near_y = sy + vy * t
            if math.hypot(x + 0.5 - near_x, y + 0.5 - near_y) <= radius:
                mask.add((x, y))
    return mask


def shade_blade(mask):
    """Bright on the top edge, dark along the concave underside."""
    tones = {}
    for x in range(SIZE):
        column = sorted(y for y in range(SIZE) if (x, y) in mask)
        if not column:
            continue
        top, bottom = column[0], column[-1]
        span = max(1, bottom - top)
        for y in column:
            f = (y - top) / span
            if f < 0.18:
                tone = "w"
            elif f < 0.5:
                tone = "l"
            elif f < 0.82:
                tone = "s"
            else:
                tone = "d"
            tones[(x, y)] = tone
    return tones


def build_grid(palette):
    blade = raster_polygon(BLADE_POLYGON)
    socket = raster_polygon(SOCKET_POLYGON)
    spike = raster_capsule(SPIKE_START, SPIKE_END, 1.0)
    shaft = raster_capsule(SHAFT_START, SHAFT_END, 1.1)
    pommel = set()
    for y in range(SIZE):
        for x in range(SIZE):
            if math.hypot(x + 0.5 - POMMEL[0], y + 0.5 - POMMEL[1]) <= 2.2:
                pommel.add((x, y))

    grid = [["." for _ in range(SIZE)] for _ in range(SIZE)]

    for (x, y) in shaft:
        grid[y][x] = "H" if (x + y) % 7 < 2 else "h"
    for (x, y) in pommel:
        grid[y][x] = "K"

    # Blade first, then the socket and spike sit over its base.
    for (x, y), tone in shade_blade(blade).items():
        grid[y][x] = tone
    for (x, y) in socket:
        grid[y][x] = "k"
    for (x, y) in spike:
        grid[y][x] = "K"

    solid = blade | socket | spike | shaft | pommel
    for (x, y) in solid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < SIZE and 0 <= ny < SIZE and (nx, ny) not in solid:
                    if grid[ny][nx] == ".":
                        grid[ny][nx] = "o"

    return [list(row) for row in grid]


def render(grid, palette, out_path, preview_path, scale=12):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        assert len(row) == SIZE, (y, len(row))
        for x, ch in enumerate(row):
            px[x, y] = palette[ch]
    img.save(out_path)
    img.resize((SIZE * scale, SIZE * scale), Image.Resampling.NEAREST).save(preview_path)
    return img


render(build_grid(SICKLE_PALETTE), SICKLE_PALETTE,
       OUT / "sickle.png", ART / "sickle_preview.png")
render(build_grid(HELL_PALETTE), HELL_PALETTE,
       OUT / "hell_sickle.png", ART / "hell_sickle_preview.png")

print("reference-style scythe sprites written")
