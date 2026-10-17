"""Bringt Geraeteaufnahmen in ein Format, das Google Play annimmt.

Play lehnt Telefon-Screenshots ab, deren lange Seite mehr als doppelt so lang
ist wie die kurze. Das Referenzgeraet hat 1080 x 2400 -- also 2,22 : 1, und
damit ist JEDE unbearbeitete Aufnahme vom eigenen Handy unbrauchbar.

Beschneiden kommt nicht in Frage: Oben sitzt die Kopfzeile, unten der
Ausbau-Knopf, und beides gehoert ins Bild. Deshalb wird skaliert und seitlich
mit der Grundfarbe des Spiels aufgefuellt -- das Bild bleibt vollstaendig,
und die Raender verschwinden im dunklen Grund.

Aufruf:
    python art_source/icon/store_bilder.py            # Rohaufnahmen -> 1080 x 2160
    python art_source/icon/store_bilder.py --pruefen  # alle Store-Bilder gegen die Play-Regeln pruefen
                                                      # und Kontaktbogen docs/store_bilder/_kontaktbogen.png bauen

Rohaufnahmen heissen shots/store_roh_<nr>_<name>.png (Nummer = Reihenfolge im Store,
siehe docs/release/STORE_BILDER.md).
"""

import glob
import os
import sys
from PIL import Image

ZIEL_B, ZIEL_H = 1080, 2160          # genau 2 : 1
GRUND = (43, 48, 59)                 # 2a2f3a, der Hintergrund der Welten
QUELLE = "shots/store_roh_*.png"
AUSGABE = "docs/store_bilder"


PLAY_REGELN = {
    "telefon": dict(min_kurz=320, max_lang=3840, max_verhaeltnis=2.0, max_mb=8),
    "feature": dict(groesse=(1024, 500), max_mb=15),
    "icon": dict(groesse=(512, 512), max_mb=1),
}


def pruefen():
    """Prueft Telefon-Screenshots (2-8 Stueck, <= 2:1, <= 8 MB, ohne Alpha),
    Feature-Grafik (1024x500) und Icon (512x512) und baut einen Kontaktbogen."""
    fehler = 0
    tel = sorted(g for g in glob.glob(AUSGABE + "/*.png")
                 if not os.path.basename(g).startswith(("feature", "icon", "_")))
    r = PLAY_REGELN["telefon"]
    if not 2 <= len(tel) <= 8:
        print("FEHLER: %d Telefon-Screenshots (erlaubt 2-8)" % len(tel)); fehler += 1
    for pfad in tel:
        bild = Image.open(pfad)
        mb = os.path.getsize(pfad) / 1048576
        ok = (min(bild.size) >= r["min_kurz"] and max(bild.size) <= r["max_lang"]
              and max(bild.size) / min(bild.size) <= r["max_verhaeltnis"] and mb <= r["max_mb"])
        print("%-24s %dx%d %.1f MB %s" % (os.path.basename(pfad), bild.width, bild.height, mb, "ok" if ok else "FEHLER"))
        fehler += 0 if ok else 1
    for name, regel in (("feature_1024x500.png", PLAY_REGELN["feature"]), ("icon_512.png", PLAY_REGELN["icon"])):
        pfad = os.path.join(AUSGABE, name)
        if not os.path.exists(pfad):
            print("%-24s fehlt" % name); fehler += 1; continue
        bild = Image.open(pfad)
        ok = bild.size == regel["groesse"]
        print("%-24s %dx%d %s" % (name, bild.width, bild.height, "ok" if ok else "FEHLER"))
        fehler += 0 if ok else 1
    if tel:
        h = 640
        kacheln = []
        for pfad in tel:
            b = Image.open(pfad).convert("RGB")
            kacheln.append(b.resize((round(b.width * h / b.height), h), Image.LANCZOS))
        bogen = Image.new("RGB", (sum(k.width for k in kacheln) + 12 * (len(kacheln) + 1), h + 24), GRUND)
        x = 12
        for k in kacheln:
            bogen.paste(k, (x, 12)); x += k.width + 12
        bogen.save(os.path.join(AUSGABE, "_kontaktbogen.png"))
        print("Kontaktbogen: %s/_kontaktbogen.png" % AUSGABE)
    raise SystemExit(1 if fehler else 0)


def main():
    if "--pruefen" in sys.argv:
        pruefen()
    dateien = sorted(glob.glob(QUELLE))
    if not dateien:
        raise SystemExit("Keine Rohaufnahmen gefunden: %s" % QUELLE)
    os.makedirs(AUSGABE, exist_ok=True)
    for pfad in dateien:
        roh = Image.open(pfad).convert("RGB")
        faktor = min(ZIEL_B / roh.width, ZIEL_H / roh.height)
        klein = roh.resize((round(roh.width * faktor), round(roh.height * faktor)), Image.LANCZOS)
        bild = Image.new("RGB", (ZIEL_B, ZIEL_H), GRUND)
        bild.paste(klein, ((ZIEL_B - klein.width) // 2, (ZIEL_H - klein.height) // 2))
        name = os.path.basename(pfad).replace("store_roh_", "")
        bild.save(os.path.join(AUSGABE, name))
        print("%-18s %d x %d  (Seitenverhaeltnis %.2f)" % (name, bild.width, bild.height, bild.height / bild.width))


if __name__ == "__main__":
    main()
