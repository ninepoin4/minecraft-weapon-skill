from PIL import Image, ImageDraw

S = 32
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

# palette
WOOD_D = (43, 26, 16, 255)
WOOD_S = (74, 46, 26, 255)
WOOD_B = (110, 71, 38, 255)
WOOD_L = (150, 102, 58, 255)
EM_D = (11, 61, 36, 255)
EM_S = (18, 107, 60, 255)
EM_B = (30, 155, 86, 255)
EM_L = (63, 208, 122, 255)
EM_H = (180, 245, 200, 255)
GOLD_D = (74, 50, 16, 255)
GOLD_S = (138, 100, 24, 255)
GOLD_B = (199, 154, 46, 255)
GOLD_L = (242, 208, 107, 255)

# handle: 3px-ish diagonal from (4,29) to (21,12)
d.line([(4, 29), (21, 12)], fill=WOOD_B, width=4)
d.line([(5, 29), (21, 13)], fill=WOOD_S, width=1)
d.line([(4, 28), (20, 12)], fill=WOOD_L, width=1)

# axe head: bearded blade polygon
head = [(21, 9), (27, 5), (30, 5), (30, 9), (28, 14), (25, 18), (23, 20), (22, 16), (21, 14), (20, 12), (19, 9)]
d.polygon(head, fill=EM_B)

# back spike / poll
poll = [(19, 9), (15, 6), (14, 7), (17, 11), (20, 12)]
d.polygon(poll, fill=EM_S)

# socket / collar
d.rectangle([19, 11, 22, 14], fill=GOLD_B)
d.line([(19, 11), (22, 11)], fill=GOLD_L)
d.line([(19, 14), (22, 14)], fill=GOLD_D)

# outline roughly: draw polygon outlines
d.line(head + [head[0]], fill=EM_D, width=1)
d.line(poll + [poll[0]], fill=EM_D, width=1)
d.rectangle([19, 11, 22, 14], outline=GOLD_D)

# some shading on head
d.line([(22, 10), (27, 6)], fill=EM_H)
d.line([(23, 11), (28, 7)], fill=EM_L)
d.line([(28, 13), (25, 17)], fill=EM_S)
d.line([(29, 9), (28, 12)], fill=EM_L)

# pommel
d.rectangle([3, 27, 6, 30], fill=GOLD_B)
d.line([(3, 27), (6, 27)], fill=GOLD_L)
d.line([(3, 30), (6, 30)], fill=GOLD_D)

im.resize((S * 12, S * 12), Image.Resampling.NEAREST).convert("RGB").save("war_axe_proto.png")
im.save("war_axe_proto_1x.png")
print("saved")
