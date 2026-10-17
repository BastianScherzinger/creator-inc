"""Setzt den Titel auf die Feature-Grafik.

WARUM EIN ZWEITER SCHRITT:
Godots SVG-Renderer (ThorVG) zeichnet Formen, aber KEINEN Text -- ein
<text>-Element verschwindet spurlos. Das faellt nicht auf, solange man die
Datei nicht ansieht: Die Grafik entsteht, sie ist nur leer an der Stelle, an
der der Titel stehen sollte.

Deshalb zwei Schritte: Godot rastert die Formen (scharfe Kanten bei jeder
Groesse), Python setzt die Schrift darueber (echte Schrift statt nachgebauter
Pfade). Beides einmal, beides nachvollziehbar.

Aufruf (NACH tools/icon_bauen.gd):
    python art_source/icon/feature_text.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

BILD = "project/assets/icon/feature_1024x500.png"

# Reihenfolge = Vorliebe. Segoe UI ist auf Windows ueberall da und ruhiger als
# Arial; die anderen sind Rueckfallebenen, damit das Skript nicht an einem
# fehlenden Font scheitert.
SCHRIFTEN = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
SCHRIFTEN_MAGER = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

AKZENT = (242, 169, 59, 255)
TEXT = (195, 201, 212, 255)


def lade(kandidaten, groesse):
    for pfad in kandidaten:
        if os.path.exists(pfad):
            return ImageFont.truetype(pfad, groesse)
    raise SystemExit("Keine der erwarteten Schriften gefunden: %s" % kandidaten)


def main():
    if not os.path.exists(BILD):
        raise SystemExit("Erst tools/icon_bauen.gd laufen lassen -- %s fehlt" % BILD)

    bild = Image.open(BILD).convert("RGBA")
    zeichnung = ImageDraw.Draw(bild)

    zeichnung.text((292, 172), "HELLO WORLD", font=lade(SCHRIFTEN, 78), fill=AKZENT)
    zeichnung.text((296, 268), "Vom ersten Clip zum eigenen Konzern.",
                   font=lade(SCHRIFTEN_MAGER, 30), fill=TEXT)

    bild.save(BILD)
    print("Titel gesetzt: %s (%d x %d)" % (BILD, bild.width, bild.height))


if __name__ == "__main__":
    main()
