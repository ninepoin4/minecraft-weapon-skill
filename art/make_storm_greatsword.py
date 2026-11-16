"""Generate the animated 64x64 divine storm greatsword texture.

A holy greatsword: long tapered blade with a brilliant white edge, pale-blue
steel, a thin gold rune core, swept gold wing-guards and a glowing gem pommel.
Eight frames (64x512 + .mcmeta, 10 fps): a white-gold radiance travels up the
blade, small light motes sparkle along it, and the guard gem pulses.
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
    "o": (8, 10, 18, 255),
    "w": (255, 255, 250, 255),
    "c": (205, 246, 255, 255),
    "l": (168, 205, 232, 255),
    "s": (122, 152, 184, 255),
    "d": (62, 84, 112, 255),
    "g": (242, 204, 116, 255),
    "G": (255, 240, 184, 255),
    "h": (40, 54, 82, 255),
    "H": (24, 32, 52, 255),
    "k": (170, 180, 200, 255),
    "K": (86, 96, 118, 255),
}

BLADE_A = (25.0, 39.0)
BLADE_B = (60.0, 4.0)

LEFT_WING = [
    (24.0, 37.0), (20.0, 34.0), (15.0, 31.0), (11.0, 30.0),
    (12.0, 32.0), (16.0, 34.0), (20.0, 37.0), (24.0, 39.0),
]
RIGHT_WING = [
    (27.0, 42.0), (31.0, 45.0), (36.0, 48.0), (40.0, 49.0),
    (39.0, 47.0), (35.0, 45.0), (31.0, 42.0), (27.0, 40.0),
]
GUARD_GEM = (25.0, 39.0)

HANDLE_A = (24.0, 41.0)
HANDLE_B = (9.0, 58.0)
POMMEL = (9.0, 58.0)


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


def circle(cx, cy, radius):
    return {(x, y) for y in range(SIZE) for x in range(SIZE)
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= radius}


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def blade_pixels():
    """{(x, y): (t, q, upper_side)} for the tapered blade."""
    ax, ay = BLADE_A
    bx, by = BLADE_B
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    pixels = {}
    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x + 0.5 - ax, y + 0.5 - ay
            t = max(0.0, min(1.0, (px * dx + py * dy) / length_sq))
            near_x = dx * t
            near_y = dy * t
            dist = math.hypot(px - near_x, py - near_y)
            half = 4.2 * ((1.0 - t) ** 0.6) + 0.4
            if dist > half:
                continue
            cross = dx * (py - near_y) - dy * (px - near_x)
            pixels[(x, y)] = (t, dist / half, cross < 0.0)
    return pixels


def base_grid():
    grid = [["." for _ in range(SIZE)] for _ in range(SIZE)]

    # Long two-handed grip: dark navy leather with gold collars.
    for (x, y) in raster_capsule(HANDLE_A, HANDLE_B, 2.0):
        grid[y][x] = "H" if (x + y) % 6 < 2 else "h"
    for t in (0.2, 0.5, 0.8):
        cx, cy = lerp(HANDLE_A, HANDLE_B, t)
        for (x, y) in circle(cx, cy, 2.6):
            grid[y][x] = "g"

    # Gem pommel.
    for (x, y) in circle(*POMMEL, 3.2):
        grid[y][x] = "g"
    for (x, y) in circle(*POMMEL, 2.0):
        grid[y][x] = "G"
    grid[58][9] = "w"

    # Blade: white edge, pale-blue body, silver belly, gold rune core.
    blade = blade_pixels()
    for (x, y), (t, q, upper) in blade.items():
        if q < 0.10:
            grid[y][x] = "G"
        elif upper:
            grid[y][x] = "w" if q > 0.8 else "c" if q > 0.55 else "l"
        else:
            grid[y][x] = "d" if q > 0.84 else "s" if q > 0.55 else "l"

    # Swept gold wing-guards over the blade base.
    for wing in (LEFT_WING, RIGHT_WING):
        for (x, y) in raster_polygon(wing):
            grid[y][x] = "g"
    for (x, y) in circle(11.5, 30.5, 1.6) | circle(39.5, 48.5, 1.6):
        grid[y][x] = "w"

    # Central gem.
    for (x, y) in circle(*GUARD_GEM, 1.8):
        grid[y][x] = "c"
    grid[39][25] = "w"

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

    # White-gold radiance travelling from the guard to the tip.
    pulse = frame / FRAMES
    for (x, y), (t, q, upper) in blade.items():
        phase = (t - pulse) % 1.0
        if phase < 0.12:
            grid[y][x] = "w" if upper and q > 0.45 else "G"
        # Small divine motes at fixed points along the blade.
        for k in range(3):
            center_t = 0.22 + 0.2 * k
            if abs(t - center_t) < 0.012 and (frame + k) % 4 < 2 and q < 0.5:
                grid[y][x] = "w"

    # Guard gem and pommel pulse between white and gold.
    gem_tone = "w" if frame % 2 == 0 else "G"
    grid[39][25] = gem_tone
    grid[58][9] = gem_tone

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
strip.save(OUT / "storm_greatsword.png")

frames[0].resize((SIZE * 6, SIZE * 6), Image.Resampling.NEAREST).save(
    ART / "storm_greatsword_preview.png")
big_frames = [f.resize((SIZE * 6, SIZE * 6), Image.Resampling.NEAREST) for f in frames]
big_frames[0].save(ART / "storm_greatsword_preview.gif", save_all=True,
                   append_images=big_frames[1:], duration=100, loop=0, disposal=2)

meta = '{"animation": {"frametime": 2}}\n'
(OUT / "storm_greatsword.png.mcmeta").write_text(meta, encoding="utf-8")

print("divine storm greatsword frames written")
