"""Q1: Store-Bilder im Sticker-Pop-Stil zusammensetzen (Rohaufnahmen 720x1590 -> 1080x2160 + Schlagzeile)
und Feature-Grafik 1024x500 aus keyart_start.png.
Aufruf: python art_source/icon/q1_store_compose.py <ordner_mit_roh_f1..f8.png>
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TINTE = (27, 23, 38)
PAPIER = (255, 247, 234)
GOLD = (255, 194, 26)
LIME = (182, 240, 60)
FONT = "project/assets/fonts/BricolageGrotesque.ttf"
AUS = "docs/release/store"

# (Rohname, Ausgabe, Zeilen der Schlagzeile, Hintergrundfarbe)
BILDER = [
    ("f1", "01_welt1_wg", ["Vom Clip", "zum Imperium"], (61, 123, 255)),
    ("f7", "02_story_dritter_aufruf", ["Drei Aufrufe.", "Ein Geheimnis."], (255, 111, 168)),
    ("f2", "03_welt2_studio", ["Das Studio", "wächst"], (255, 79, 163)),
    ("f3", "04_welt3_merch_station", ["Jede Station", "ausbauen"], (255, 122, 26)),
    ("f4", "05_welt4_ziele", ["Immer ein", "nächstes Ziel"], (18, 181, 165)),
    ("f5", "06_welt5_farm", ["6 Welten.", "1 Geheimnis."], (139, 92, 246)),
    ("f6", "07_welt6_portfolio", ["Ganz oben", "ankommen"], (242, 178, 0)),
    ("f8", "08_belohnung", ["Jedes Ziel", "wird belohnt"], (61, 123, 255)),
]


def schrift(groesse, gewicht=800):
    f = ImageFont.truetype(FONT, groesse)
    try:
        f.set_variation_by_axes([96, min(gewicht, 800), 100])
    except Exception:
        pass
    return f


def text_kontur(d, xy, text, f, fuell=PAPIER, kontur=TINTE, k=9, anker="mm"):
    d.text(xy, text, font=f, fill=fuell, stroke_width=k, stroke_fill=kontur, anchor=anker)


def abgerundet(bild, r):
    m = Image.new("L", bild.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, bild.width - 1, bild.height - 1), r, fill=255)
    out = bild.convert("RGBA")
    out.putalpha(m)
    return out


def tafel(roh, zeilen, farbe):
    b = Image.new("RGB", (1080, 2160), farbe)
    d = ImageDraw.Draw(b)
    # dezente Punkte als Muster
    helle = tuple(min(255, c + 28) for c in farbe)
    for y in range(20, 2160, 90):
        for x in range(20 + (y // 90 % 2) * 45, 1080, 90):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=helle)
    shot = Image.open(roh).convert("RGB")
    h = 1790
    w = round(shot.width * h / shot.height)
    shot = shot.resize((w, h), Image.LANCZOS)
    x0, y0 = (1080 - w) // 2, 2160 - h - 40
    rahmen = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    ImageDraw.Draw(rahmen).rounded_rectangle((0, 0, w + 23, h + 23), 52, fill=TINTE)
    schatten = Image.new("RGBA", b.size, (0, 0, 0, 0))
    ImageDraw.Draw(schatten).rounded_rectangle((x0 - 12 + 14, y0 - 12 + 18, x0 + w + 12 + 14, y0 + h + 12 + 18), 52, fill=(27, 23, 38, 150))
    b = Image.alpha_composite(b.convert("RGBA"), schatten.filter(ImageFilter.GaussianBlur(6)))
    b.alpha_composite(rahmen, (x0 - 12, y0 - 12))
    b.alpha_composite(abgerundet(shot, 40), (x0, y0))
    d = ImageDraw.Draw(b)
    f = schrift(104, 800)
    y = 130 if len(zeilen) == 2 else 150
    for i, z in enumerate(zeilen):
        text_kontur(d, (540, y + i * 118), z, f, fuell=GOLD if i == 1 else PAPIER)
    return b.convert("RGB")


def feature(keyart):
    k = Image.open(keyart).convert("RGB")
    h = round(k.width * 500 / 1024)
    y0 = 1000
    b = k.crop((0, y0, k.width, y0 + h)).resize((1024, 500), Image.LANCZOS)
    b = b.convert("RGBA")
    # Logo-Sticker wie in der Eroeffnung: CREATOR / INC, Limette auf Gold, leicht schraeg
    lw, lh = 440, 300
    logo = Image.new("RGBA", (lw + 80, lh + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(logo)
    gold = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    ImageDraw.Draw(gold).rounded_rectangle((44, 44, 44 + lw, 44 + lh), 60, fill=GOLD, outline=TINTE, width=7)
    gold = gold.rotate(5, resample=Image.BICUBIC)
    logo.alpha_composite(gold)
    lim = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    ImageDraw.Draw(lim).rounded_rectangle((40, 40, 40 + lw, 40 + lh), 60, fill=LIME, outline=TINTE, width=7)
    logo.alpha_composite(lim)
    ld = ImageDraw.Draw(logo)
    # 17.10.: Name "Creator Inc" -- die laengere Zeile bekommt die kleinere Schrift.
    text_kontur(ld, (logo.width // 2, 40 + lh // 2 - 58), "CREATOR", schrift(96, 900), k=10)
    text_kontur(ld, (logo.width // 2, 40 + lh // 2 + 64), "INC", schrift(128, 900), k=11)
    logo = logo.rotate(4, resample=Image.BICUBIC, expand=True)
    b.alpha_composite(logo, (1024 - logo.width - 10, (500 - logo.height) // 2 - 4))
    return b.convert("RGB")


def main():
    if sys.argv[1:] == ["--nur-feature"]:
        feature("project/assets/ui/keyart_start.png").save(os.path.join(AUS, "q1_feature_1024x500.png"))
        return
    roh = sys.argv[1]
    os.makedirs(AUS, exist_ok=True)
    for r, name, zeilen, farbe in BILDER:
        tafel(os.path.join(roh, r + ".png"), zeilen, farbe).save(os.path.join(AUS, "q1_%s.png" % name))
        print(name)
    feature("project/assets/ui/keyart_start.png").save(os.path.join(AUS, "q1_feature_1024x500.png"))


if __name__ == "__main__":
    main()
