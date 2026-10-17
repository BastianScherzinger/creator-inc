"""Handybild (1080x2400) -> Play-Screenshot 1080x2160 (hoechstens 2:1), ohne etwas abzuschneiden:
das Bild wird auf 2160 Hoehe verkleinert und mittig auf eine weichgezeichnete Fassung seiner selbst gesetzt."""
import sys
from PIL import Image, ImageFilter

quelle, ziel = sys.argv[1], sys.argv[2]
im = Image.open(quelle).convert("RGB")
h = 2160
w = round(im.width * h / im.height)
klein = im.resize((w, h), Image.LANCZOS)
grund = im.resize((1080, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
grund = Image.blend(grund, Image.new("RGB", grund.size, (20, 24, 40)), 0.35)
grund.paste(klein, ((1080 - w) // 2, 0))
grund.save(ziel)
print(ziel, grund.size)
