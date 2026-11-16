from PIL import Image, ImageDraw

S = 32
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

# axe head: crescent blade with beard
head = [
    (21, 11), (24, 9), (27, 7), (29, 6),
    (30, 8), (30, 11), (29, 14), (27, 17),
    (24, 20), (22, 21), (21, 18), (20, 16),
    (19, 14), (19, 11),
]
d.polygon(head, fill=(255, 0, 0, 255))

# back spike / poll
poll = [(20, 14), (18, 13), (16, 11), (14, 10), (15, 9), (18, 11), (19, 11)]
d.polygon(poll, fill=(255, 0, 0, 255))

# handle 3px diagonal, stops at socket
for t in range(16):
    cx, cy = 5 + t, 30 - t
    for dx, dy in ((0, 0), (1, 0), (0, -1)):
        x, y = cx + dx, cy + dy
        if 0 <= x < S and 0 <= y < S and im.getpixel((x, y))[3] == 0:
            im.putpixel((x, y), (0, 0, 255, 255))

# socket / collar
d.rectangle([19, 12, 22, 15], fill=(255, 255, 0, 255))
# pommel
d.rectangle([4, 28, 6, 30], fill=(255, 255, 0, 255))

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
preview.save("war_axe_silhouette2.png")
print("saved")
