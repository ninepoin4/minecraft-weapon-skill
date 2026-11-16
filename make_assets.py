"""Build the Weapon mod's runtime assets from the hand-drawn rapier sprite.

Copies the approved 16x16 sprite into the mod resources and renders a 128x128
mod icon: dark plate, green venom glow, crisp 7x pixel sword.
"""
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(r"D:/zd1/weapon")
SRC_SPRITE = Path(r"D:/zd1/lightning_greatsword/venom_rapier_sprite.png")
ART = ROOT / "art"
TEX = ROOT / "src/main/resources/assets/weapon/textures/item/venom_rapier.png"
ICON = ROOT / "src/main/resources/assets/weapon/icon.png"
ICON_PREVIEW = ROOT / "art/icon_preview.png"

ART.mkdir(parents=True, exist_ok=True)
TEX.parent.mkdir(parents=True, exist_ok=True)
ICON.parent.mkdir(parents=True, exist_ok=True)

shutil.copy2(SRC_SPRITE, ART / "venom_rapier_sprite.png")
shutil.copy2(SRC_SPRITE, TEX)

sprite = Image.open(SRC_SPRITE).convert("RGBA")
assert sprite.size == (16, 16), sprite.size

SIZE = 128
bg_top = (18, 26, 24)
bg_bottom = (7, 11, 10)
icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
px = icon.load()
for y in range(SIZE):
    t = y / (SIZE - 1)
    c = tuple(round(bg_top[i] * (1 - t) + bg_bottom[i] * t) for i in range(3))
    for x in range(SIZE):
        px[x, y] = (*c, 255)

# Venom glow behind the sword.
glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
gdraw = ImageDraw.Draw(glow)
gdraw.ellipse((22, 22, 106, 106), fill=(36, 196, 88, 120))
glow = glow.filter(ImageFilter.GaussianBlur(18))
icon = Image.alpha_composite(icon, glow)

# Crisp 7x pixel sword, centred.
big = sprite.resize((112, 112), Image.Resampling.NEAREST)
# Drop shadow.
shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
shadow.paste((0, 0, 0, 120), (12, 14), big)
shadow = shadow.filter(ImageFilter.GaussianBlur(4))
icon = Image.alpha_composite(icon, shadow)
icon.alpha_composite(big, (8, 8))

# Thin frame.
draw = ImageDraw.Draw(icon)
draw.rectangle((0, 0, SIZE - 1, SIZE - 1), outline=(52, 74, 62, 255), width=2)
draw.rectangle((3, 3, SIZE - 4, SIZE - 4), outline=(14, 20, 17, 255), width=1)

icon.save(ICON)
icon.save(ICON_PREVIEW)
print("wrote", TEX)
print("wrote", ICON)
