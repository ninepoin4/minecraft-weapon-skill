from PIL import Image

S = 32
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))

EM_D = (11, 61, 36, 255)
EM_S = (18, 107, 60, 255)
EM_B = (30, 155, 86, 255)
EM_L = (63, 208, 122, 255)
EM_H = (180, 245, 200, 255)
WOOD_D = (43, 26, 16, 255)
WOOD_S = (74, 46, 26, 255)
WOOD_B = (110, 71, 38, 255)
WOOD_L = (150, 102, 58, 255)
GOLD_D = (74, 50, 16, 255)
GOLD_S = (138, 100, 24, 255)
GOLD_B = (199, 154, 46, 255)
GOLD_L = (242, 208, 107, 255)

head = set()
blade = {
    5: (28, 29), 6: (27, 30), 7: (26, 30), 8: (25, 30),
    9: (24, 30), 10: (23, 30), 11: (22, 30), 12: (21, 30),
    13: (20, 29), 14: (20, 29), 15: (20, 28), 16: (24, 27),
    17: (24, 27), 18: (24, 26), 19: (24, 25), 20: (23, 24), 21: (22, 23),
}
for y, (x0, x1) in blade.items():
    for x in range(x0, x1 + 1):
        head.add((x, y))
spike = {9: (15, 16), 10: (15, 17), 11: (16, 18), 12: (18, 19)}
for y, (x0, x1) in spike.items():
    for x in range(x0, x1 + 1):
        head.add((x, y))

handle = set()
for t in range(15):
    cx, cy = 5 + t, 29 - t
    for dx, dy in ((0, 0), (1, 0), (0, -1)):
        x, y = cx + dx, cy + dy
        if (x, y) not in head:
            handle.add((x, y))

socket = {(x, y) for y in range(12, 16) for x in range(19, 23)}
pommel = {(x, y) for y in range(27, 30) for x in range(4, 7)}

def neighbors(p):
    x, y = p
    return [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]

def paint_head():
    for p in head:
        x, y = p
        n = neighbors(p)
        edge = any(q not in head and q not in socket for q in n)
        if edge:
            im.putpixel(p, EM_D)
        else:
            top_left = (x-1,y) not in head or (x,y-1) not in head
            bottom_right = (x+1,y) not in head or (x,y+1) not in head
            if top_left and not bottom_right:
                im.putpixel(p, EM_L)
            elif bottom_right and not top_left:
                im.putpixel(p, EM_S)
            else:
                im.putpixel(p, EM_B)
    # bevel along the cutting edge (right edge, just inside outline)
    for y in range(6, 21):
        xs = [x for x in range(S) if (x, y) in head]
        if xs:
            x = max(xs)
            if (x-1, y) in head:
                im.putpixel((x-1, y), EM_L)
    # tip highlight
    for p in [(29,5),(30,6),(29,6),(30,7)]:
        if p in head: im.putpixel(p, EM_H)

def paint_handle():
    for p in handle:
        x, y = p
        if any(q not in handle and q not in socket and q not in pommel for q in neighbors(p)):
            im.putpixel(p, WOOD_D)
        else:
            # diagonal band: top (x,y-1) light, middle (x,y) base, lower-right (x+1,y) shadow
            if (x, y-1) in handle and (x+1, y) in handle and (x-1, y) in handle:
                im.putpixel(p, WOOD_B)
            elif (x, y-1) in handle:
                im.putpixel(p, WOOD_L)
            elif (x+1, y) in handle:
                im.putpixel(p, WOOD_S)
            else:
                im.putpixel(p, WOOD_B)

def paint_gold(mask):
    for p in mask:
        x, y = p
        im.putpixel(p, GOLD_B)
    # simple bevel
    for p in mask:
        x, y = p
        if (x, y-1) not in mask:
            im.putpixel(p, GOLD_L)
        elif (x, y+1) not in mask:
            im.putpixel(p, GOLD_D)
        elif (x-1, y) not in mask:
            im.putpixel(p, GOLD_S)
        elif (x+1, y) not in mask:
            im.putpixel(p, GOLD_S)

paint_head()
paint_handle()
paint_gold(socket)
paint_gold(pommel)

# leather wraps: two dark bands on the handle
for t in (4, 9):
    cx, cy = 5 + t, 29 - t
    for dx, dy in ((0, 0), (1, 0), (0, -1)):
        p = (cx+dx, cy+dy)
        if p in handle:
            im.putpixel(p, WOOD_D if (dx,dy) != (1,0) else WOOD_S)

im.save("war_axe_paint1.png")
im.resize((S*12, S*12), Image.Resampling.NEAREST).convert("RGB").save("war_axe_paint1_12x.png")

# ascii palette map
key = {}
for col, ch in [(EM_D,'D'),(EM_S,'S'),(EM_B,'B'),(EM_L,'L'),(EM_H,'H'),
                (WOOD_D,'w'),(WOOD_S,'u'),(WOOD_B,'o'),(WOOD_L,'k'),
                (GOLD_D,'G'),(GOLD_S,'g'),(GOLD_B,'y'),(GOLD_L,'Y')]:
    key[col] = ch
for y in range(S):
    row = ""
    for x in range(S):
        px = im.getpixel((x, y))
        row += "." if px[3] == 0 else key.get(px, '?')
    print(f"{y:02d} {row}")
print("saved")
