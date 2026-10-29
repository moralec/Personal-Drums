# Builds the app icons (img/icon-*.png) from the drum in img/source/scene.png: the drum on the app's dark background.
# Needs pillow. Run: python3 tools/icon.py
from PIL import Image

DRUM = (120, 250, 1190, 1250)   # crop box of the drum in scene.png (image pixels)
FILL = 0.74                # drum width as a share of the icon: leaves room for the OS icon mask
SIZES = {'icon-512.png': 512, 'icon-192.png': 192, 'apple-touch-icon.png': 180}

scene = Image.open('img/source/scene.png').convert('RGB')
BG = scene.getpixel((10, 10))   # the artwork's own background, so the crop has no visible edge
src = scene.crop(DRUM)
big = Image.new('RGB', (1024, 1024), BG)
w = round(1024 * FILL); h = round(src.height * w / src.width)
big.paste(src.resize((w, h), Image.LANCZOS), ((1024 - w) // 2, (1024 - h) // 2))
for name, px in SIZES.items():
    big.resize((px, px), Image.LANCZOS).save(f'img/{name}', optimize=True)
    print(name, px)
