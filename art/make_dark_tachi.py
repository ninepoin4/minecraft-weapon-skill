"""Draw the animated 64x64 dark tachi "Ryugiri" sprite.

A long, strongly curved obsidian tachi: black blade with a purple-white cutting
edge and a wavy violet hamon, a gold tsuba with a red dragon-eye gem, and a long
black wrapped grip with gold fittings. Eight frames (64x512 + .mcmeta): the
violet edge glow travels up the blade and the gem pulses.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(r"D:/zd1/weapon")
ART = ROOT / "art"
OUT = ROOT / "src/main/resources/assets/weapon/textures/item"
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)

SIZE = 64
FRAMES = 8

PALETTE = {
    ".": (0, 0, 0, 0),
    "o": (6, 4, 10, 255),
    "w": (240, 220, 255, 255),
    "v": (170, 90, 255, 255),
    "p": (110, 50, 180, 255),
    "d": (55, 25, 95, 255),
    "b": (16, 14, 24, 255),
    "s": (42, 36, 58, 255),
    "g": (190, 150, 70, 255),
    "G": (255, 225, 150, 255),
    "h": (38, 28, 44, 255),
    "H": (18, 14, 22, 255),
    "r": (220, 40, 90, 255),
}

# Blade curve: base at the tsuba, tip high on the right. The control point
# pulls the middle up, giving the deep tachi curve.
BLADE_A = (24.0, 42.0)
BLADE_CTRL = (44.0, 10.0)
BLADE_B = (60.0, 7.0)

TSUBA = (24.0, 42.0)
HANDLE_A = (23.0, 44.0)
HANDLE_B = (8.0, 60.0)
POMMEL = (8.0, 60.0)

SAMPLES = 400


def bezier(t):
    u = 1.0 - t
    return (u * u * BLADE_A[0] + 2 * u * t * BLADE_CTRL[0] + t * t * BLADE_B[0],
            u * u * BLADE_A[1] + 2 * u * t * BLADE_CTRL[1] + t * t * BLADE_B[1])


def bezier_tangent(t):
    u = 1.0 - t
    return (2 * u * (BLADE_CTRL[0] - BLADE_A[0]) + 2 * t * (BLADE_B[0] - BLADE_CTRL[0]),
            2 * u * (BLADE_CTRL[1] - BLADE_A[1]) + 2 * t * (BLADE_B[1] - BLADE_CTRL[1]))


def blade_thickness(t):
    return 4.0 * ((1.0 - t) ** 0.55) + 0.4


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


def circle(cx, cy, radius):
    return {(x, y) for y in range(SIZE) for x in range(SIZE)
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= radius}


def blade_pixels():
    points = [bezier(i / SAMPLES) for i in range(SAMPLES + 1)]
    tangents = [bezier_tangent(i / SAMPLES) for i in range(SAMPLES + 1)]
    pixels = {}
    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x + 0.5, y + 0.5
            best_dist = 1.0e9
            best_i = 0
            for i, (bx, by) in enumerate(points):
                d2 = (px - bx) ** 2 + (py - by) ** 2
                if d2 < best_dist:
                    best_dist = d2
                    best_i = i
            half = blade_thickness(best_i / SAMPLES) * 0.5
            dist = math.sqrt(best_dist)
            if dist > half:
                continue
            bx, by = points[best_i]
            tx, ty = tangents[best_i]
            cross = tx * (py - by) - ty * (px - bx)
            pixels[(x, y)] = (best_i / SAMPLES, dist / half, cross < 0.0)
    return pixels


def base_grid():
    grid = [["." for _ in range(SIZE)] for _ in range(SIZE)]

    # Long wrapped grip with a gold kashira.
    for (x, y) in raster_capsule(HANDLE_A, HANDLE_B, 2.2):
        grid[y][x] = "H" if (x + y) % 6 < 3 else "h"
    for (x, y) in circle(*POMMEL, 2.6):
        grid[y][x] = "g"
    for (x, y) in circle(*POMMEL, 1.6):
        grid[y][x] = "G"

    # Blade: obsidian body, purple-white cutting edge, violet hamon.
    blade = blade_pixels()
    for (x, y), (t, q, upper) in blade.items():
        if upper:
            grid[y][x] = "s" if q > 0.82 or q < 0.12 else "d" if q > 0.55 else "b"
        else:
            grid[y][x] = ("w" if q > 0.9 else "v" if q > 0.68 else
                          "p" if q > 0.42 else "d" if q > 0.2 else "b")

    # Gold tsuba with a dragon-eye gem over the blade base.
    for (x, y) in circle(*TSUBA, 4.0):
        grid[y][x] = "g"
    for (x, y) in circle(*TSUBA, 3.0):
        grid[y][x] = "H"
    grid[42][24] = "r"
    grid[42][25] = "p"
    grid[41][24] = "p"

    return grid, blade


def with_outline(grid, solid):
    out = [row[:] for row in grid]
    for (x, y) in solid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < SIZE and 0 <= ny < SIZE and (nx, ny) not in solid:
                    if out[ny][nx] == ".":
                        out[ny][nx] = "o"
    return out


def animated_frame(base, blade, frame):
    grid = [row[:] for row in base]

    # A violet glow pulse runs along the cutting edge from guard to tip.
    pulse = frame / FRAMES
    for (x, y), (t, q, upper) in blade.items():
        phase = (t - pulse) % 1.0
        if phase < 0.11 and not upper and q > 0.55:
            grid[y][x] = "w" if q > 0.8 else "v"
        # Drifting soul sparks.
        for k in range(3):
            center_t = 0.28 + 0.2 * k
            if abs(t - center_t) < 0.01 and (frame + k) % 4 < 2 and q < 0.45:
                grid[y][x] = "w"

    # Dragon-eye gem pulses red-violet.
    grid[42][24] = "w" if frame % 2 == 0 else "r"
    grid[42][25] = "r" if frame % 2 == 0 else "p"

    return grid


def to_image(grid):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            px[x, y] = PALETTE[ch]
    return img


base, blade = base_grid()
solid = {(x, y) for y in range(SIZE) for x in range(SIZE) if base[y][x] != "."}
base = with_outline(base, solid)

frames = [to_image(animated_frame(base, blade, frame)) for frame in range(FRAMES)]

strip = Image.new("RGBA", (SIZE, SIZE * FRAMES), (0, 0, 0, 0))
for i, img in enumerate(frames):
    strip.paste(img, (0, i * SIZE))
strip.save(OUT / "dark_tachi.png")

frames[0].resize((SIZE * 6, SIZE * 6), Image.Resampling.NEAREST).save(
    ART / "dark_tachi_preview.png")
big_frames = [f.resize((SIZE * 6, SIZE * 6), Image.Resampling.NEAREST) for f in frames]
big_frames[0].save(ART / "dark_tachi_preview.gif", save_all=True,
                   append_images=big_frames[1:], duration=100, loop=0, disposal=2)

meta = '{"animation": {"frametime": 2}}\n'
(OUT / "dark_tachi.png.mcmeta").write_text(meta, encoding="utf-8")

print("dark tachi frames written")
