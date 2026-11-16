from PIL import Image, ImageDraw

S = 32
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

# silhouette shapes
head = [(21, 9), (24, 7), (27, 5), (29, 4), (30, 6), (30, 9), (29, 12), (27, 15), (25, 18), (23, 20), (22, 17), (21, 15), (21, 12), (20, 11), (19, 11), (19, 13), (20, 14)]
poll = [(19, 11), (17, 10), (15, 8), (16, 7), (18, 9), (21, 9)]
d.polygon(head, fill=(255, 0, 0, 255))
d.polygon(poll, fill=(255, 0, 0, 255))
# handle 3px diagonal
for t in range(17):
    cx, cy = 5 + t, 29 - t
    for dx, dy in ((0, 0), (1, 0), (0, -1)):
        if 0 <= cx + dx < S and 0 <= cy + dy < S:
            im.putpixel((cx + dx, cy + dy), (0, 0, 255, 255))
# socket
d.rectangle([19, 11, 22, 14], fill=(255, 255, 0, 255))
# pommel
d.rectangle([4, 27, 7, 30], fill=(255, 255, 0, 255))

# ascii
for y in range(S):
    row = ""
    for x in range(S):
        r, g, b, a = im.getpixel((x, y))
        if a == 0: row += "."
        elif r > 200 and g < 50: row += "#"
        elif b > 200 and r < 50: row += "H"
        else: row += "G"
    print(f"{y:02d} {row}")

# preview with grid
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
preview.save("war_axe_silhouette.png")
print("saved war_axe_silhouette.png")
