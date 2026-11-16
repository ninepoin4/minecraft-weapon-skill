from PIL import Image, ImageDraw

S = 32
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))

def fill_span(y, x0, x1, color):
    for x in range(x0, x1 + 1):
        if 0 <= x < S and 0 <= y < S:
            im.putpixel((x, y), color)

# blade spans by row (x0,x1)
blade = {
    5: (28, 29),
    6: (27, 30),
    7: (26, 30),
    8: (25, 30),
    9: (24, 30),
    10: (23, 30),
    11: (22, 30),
    12: (21, 30),
    13: (20, 29),
    14: (20, 29),
    15: (20, 28),
    16: (24, 27),
    17: (24, 27),
    18: (24, 26),
    19: (24, 25),
    20: (23, 24),
    21: (22, 23),
}
for y, (x0, x1) in blade.items():
    fill_span(y, x0, x1, (255, 0, 0, 255))

# back spike
spike = {
    9: (15, 16),
    10: (15, 17),
    11: (16, 18),
    12: (18, 19),
}
for y, (x0, x1) in spike.items():
    fill_span(y, x0, x1, (255, 0, 0, 255))

# handle 3px diagonal from (5,29) to (19,15)
for t in range(15):
    cx, cy = 5 + t, 29 - t
    for dx, dy in ((0, 0), (1, 0), (0, -1)):
        x, y = cx + dx, cy + dy
        if 0 <= x < S and 0 <= y < S and im.getpixel((x, y))[3] == 0:
            im.putpixel((x, y), (0, 0, 255, 255))

# socket
d = ImageDraw.Draw(im)
d.rectangle([19, 12, 22, 15], fill=(255, 255, 0, 255))
d.rectangle([4, 27, 6, 29], fill=(255, 255, 0, 255))

for y in range(S):
    row = ""
    for x in range(S):
        r, g, b, a = im.getpixel((x, y))
        if a == 0: row += "."
        elif r > 200 and g < 50: row += "#"
        elif b > 200 and r < 50: row += "H"
        else: row += "G"
    print(f"{y:02d} {row}")

P = 16
preview = Image.new("RGB", (S * P, S * P), (40, 40, 40))
for y in range(S):
    for x in range(S):
        px = im.getpixel((x, y))
        if px[3]:
            preview.paste(px[:3], (x * P, y * P, (x + 1) * P, (y + 1) * P))
gd = ImageDraw.Draw(preview)
for i in range(S + 1):
    gd.line([(i * P, 0), (i * P, S * P)], fill=(80, 80, 80), width=1)
    gd.line([(0, i * P), (S * P, i * P)], fill=(80, 80, 80), width=1)
preview.save("war_axe_silhouette3.png")
print("saved")
