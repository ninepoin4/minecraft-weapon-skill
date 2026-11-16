from PIL import Image, ImageDraw
from pathlib import Path

S = 32
OUT = Path(r"D:/zd1/weapon/art/template_previews")

def blank():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))

def spans(im, rows):
    for y, x0, x1 in rows:
        for x in range(x0, x1 + 1):
            if 0 <= x < S and 0 <= y < S:
                im.putpixel((x, y), (255, 0, 255, 255))

def line(im, p1, p2, width=1):
    ImageDraw.Draw(im).line([p1, p2], fill=(255, 0, 255, 255), width=width)

def rect(im, x0, y0, x1, y1):
    ImageDraw.Draw(im).rectangle([x0, y0, x1, y1], fill=(255, 0, 255, 255))

def preview(im, name):
    im.resize((S * 12, S * 12), Image.Resampling.NEAREST).convert("RGB").save(OUT / f"{name}.png")
    rows = []
    for y in range(S):
        rows.append("".join("X" if im.getpixel((x, y))[3] else "." for x in range(S)))
    visible = sum(r.count("X") for r in rows)
    xs = [x for y in range(S) for x in range(S) if im.getpixel((x, y))[3]]
    ys = [y for y in range(S) for x in range(S) if im.getpixel((x, y))[3]]
    bbox = [min(xs), min(ys), max(xs), max(ys)] if xs else None
    print(name, "visible", visible, "bbox", bbox)
    for i, row in enumerate(rows):
        print(f"{i:02d} {row}")

# SPEAR v3
spear = blank()
line(spear, (4, 29), (20, 13), width=2)
spans(spear, [
    (3, 29, 29), (4, 28, 30), (5, 27, 30), (6, 26, 30),
    (7, 25, 30), (8, 24, 29), (9, 23, 29), (10, 22, 28),
    (11, 21, 27), (12, 20, 26), (13, 20, 25),
])
rect(spear, 19, 14, 22, 16)
rect(spear, 2, 28, 4, 30)
print("=== SPEAR v3 ===")
preview(spear, "spear3")

# GREATSWORD v3 (shorter guard wings)
great = blank()
spans(great, [
    (3, 28, 29), (4, 27, 30), (5, 26, 30), (6, 25, 30),
    (7, 24, 30), (8, 23, 30), (9, 22, 30), (10, 21, 30),
    (11, 20, 30), (12, 19, 30), (13, 18, 29), (14, 17, 29),
    (15, 16, 28), (16, 15, 28), (17, 14, 27), (18, 13, 26),
    (19, 13, 25),
])
line(great, (7, 15), (17, 25), width=3)
line(great, (10, 22), (4, 28), width=4)
rect(great, 2, 27, 5, 30)
print("=== GREATSWORD v3 ===")
preview(great, "greatsword3")
