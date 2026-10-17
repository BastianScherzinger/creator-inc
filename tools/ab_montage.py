#!/usr/bin/env python3
"""A/B-Montage: legt zwei Varianten eines Bildschirms nebeneinander.

Aufruf (aus dem Projektordner cannabisgame):
    python tools/ab_montage.py stations_panel
    python tools/ab_montage.py raum_panel ziele_leiste story_szene
    python tools/ab_montage.py --alle
    python tools/ab_montage.py stations_panel --klein      # zusaetzlich auf 50 % (Kriterium K1)

Erwartet je Bildschirm zwei Vorschaubilder:
    shots/ab/<schirm>_a.png     (PC-Vorschau, Variante A:  --variante a)
    shots/ab/<schirm>_b.png     (PC-Vorschau, Variante B:  --variante b)
Optional die Handy-Aufnahmen daneben:
    shots/ab/<schirm>_a_handy.png, shots/ab/<schirm>_b_handy.png
Ausgabe:
    shots/ab/<schirm>_ab.png    (und mit --klein: <schirm>_ab_klein.png)

Die Bilder werden auf gleiche Hoehe gebracht, mit A/B-Kopfzeile versehen. Bewertet wird
danach in docs/nacht/ab_bewertung.md mit den Kriterien K1-K5 (0-2 Punkte, Gewinner ab 7/10).
Es werden keine Daten erhoben; das Werkzeug liest und schreibt nur lokale Bilder.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SCHIRME = ["stations_panel", "raum_panel", "ziele_leiste", "story_szene"]
ORDNER = Path(__file__).resolve().parent.parent / "shots" / "ab"
KOPF = 64
LUECKE = 24
RAND = 24
HINTERGRUND = (245, 240, 230)
TINTE = (34, 30, 28)
AKZENT = {"a": (255, 194, 26), "b": (120, 190, 40)}


def schrift(groesse: int) -> ImageFont.FreeTypeFont:
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "segoeuib.ttf"):
        try:
            return ImageFont.truetype(name, groesse)
        except OSError:
            continue
    return ImageFont.load_default()


def lade(pfad: Path) -> Image.Image | None:
    if not pfad.exists():
        return None
    return Image.open(pfad).convert("RGB")


def auf_hoehe(bild: Image.Image, hoehe: int) -> Image.Image:
    if bild.height == hoehe:
        return bild
    breite = max(1, round(bild.width * hoehe / bild.height))
    return bild.resize((breite, hoehe), Image.LANCZOS)


def spalte(schirm: str, variante: str) -> list[Image.Image]:
    """PC-Vorschau und, falls vorhanden, die Handy-Aufnahme dieser Variante."""
    bilder = []
    for suffix in ("", "_handy"):
        bild = lade(ORDNER / f"{schirm}_{variante}{suffix}.png")
        if bild is not None:
            bilder.append(bild)
    return bilder


def montiere(schirm: str, klein: bool) -> Path | None:
    spalten = {v: spalte(schirm, v) for v in ("a", "b")}
    fehlend = [v for v, bilder in spalten.items() if not bilder]
    if fehlend:
        print(f"{schirm}: Bild fuer Variante {', '.join(fehlend).upper()} fehlt in {ORDNER}", file=sys.stderr)
        return None
    hoehe = min(b.height for bilder in spalten.values() for b in bilder)
    hoehe = min(hoehe, 1200)
    teile = {v: [auf_hoehe(b, hoehe) for b in bilder] for v, bilder in spalten.items()}
    breiten = {v: sum(b.width for b in bilder) + LUECKE // 2 * (len(bilder) - 1) for v, bilder in teile.items()}
    gesamt_b = RAND * 2 + breiten["a"] + breiten["b"] + LUECKE
    gesamt_h = RAND * 2 + KOPF + hoehe
    montage = Image.new("RGB", (gesamt_b, gesamt_h), HINTERGRUND)
    zeichner = ImageDraw.Draw(montage)
    x = RAND
    for v in ("a", "b"):
        zeichner.rounded_rectangle((x, RAND, x + breiten[v], RAND + KOPF - 12), radius=14,
                                   fill=AKZENT[v], outline=TINTE, width=3)
        zeichner.text((x + 18, RAND + 8), f"VARIANTE {v.upper()}  ·  {schirm}", font=schrift(30), fill=TINTE)
        y = RAND + KOPF
        xx = x
        for bild in teile[v]:
            montage.paste(bild, (xx, y))
            zeichner.rectangle((xx - 1, y - 1, xx + bild.width, y + bild.height), outline=TINTE, width=2)
            xx += bild.width + LUECKE // 2
        x += breiten[v] + LUECKE
    ORDNER.mkdir(parents=True, exist_ok=True)
    ziel = ORDNER / f"{schirm}_ab.png"
    montage.save(ziel)
    print(f"{schirm}: {ziel}")
    if klein:
        halb = montage.resize((montage.width // 2, montage.height // 2), Image.LANCZOS)
        ziel_klein = ORDNER / f"{schirm}_ab_klein.png"
        halb.save(ziel_klein)
        print(f"{schirm}: {ziel_klein}  (50 %, Kriterium K1)")
    return ziel


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B-Montage der Kernbildschirme")
    parser.add_argument("schirme", nargs="*", help="; ".join(SCHIRME))
    parser.add_argument("--alle", action="store_true", help="alle vier Bildschirme")
    parser.add_argument("--klein", action="store_true", help="zusaetzlich eine 50-Prozent-Fassung")
    args = parser.parse_args()
    auswahl = SCHIRME if args.alle or not args.schirme else args.schirme
    erfolg = True
    for schirm in auswahl:
        erfolg = (montiere(schirm, args.klein) is not None) and erfolg
    return 0 if erfolg else 1


if __name__ == "__main__":
    sys.exit(main())
