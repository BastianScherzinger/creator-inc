"""Symbole im Stil "Sticker-Pop", ein Rezept (docs/nacht/D1_ART_DIRECTION.md C4, Paket A).

Rezept fuer JEDES Symbol (viewBox 128, Ausgabe 256 x 256):
  * gefuellte Flaeche in hoechstens zwei Farben (+ Tinte); Papier/Creme zaehlt als Farbe
  * Tintenkontur 6 (= 3 px bei 64 px Anzeige), runde Ecken und Enden
  * Lichtkante: weisse Kante (40 %) innen oben links, immer gleich gebaut (`flaeche`)
  * kein Schatten (den setzen die Karten), Motiv fuellt etwa 12..116 der Flaeche

Aufruf:
    python build_symbole_sticker.py            # schreibt symbole/ und je Welt bereich_1..5.svg
    python build_symbole_sticker.py --vorschau # zusaetzlich Kontaktboegen nach art_source/vorschau/

Ziel: project/assets/ui/symbole/<name>.svg (28 UI-Symbole, Dateinamen unveraendert)
      project/assets/ui/<welt>/bereich_<n>.svg (Bereichssymbole Welt 1-5)
"""
import base64
import math
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parents[2]
UI = WURZEL / "project" / "assets" / "ui"
VORSCHAU = WURZEL / "art_source" / "vorschau"

TINTE = "#1B1726"
TINTE_2 = "#8C8499"
PAPIER = "#FFF7EA"
PAPIER_2 = "#F3E9D8"
KAUFEN = "#B6F03C"
WARNUNG = "#FF4D3D"
GOLD = "#FFC21A"
GOLD_TIEF = "#E09A00"
BLAU = "#3D7BFF"
HONIG = "#D9A86C"
HIMMEL = "#7CD4FF"
S = 6  # Kontur

_zaehler = [0]


def svg(inhalt: str) -> str:
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 128 128">\n'
            + inhalt + '\n</svg>\n')


# --- Formen: (tag, attrs) ------------------------------------------------------

def rect(x, y, w, h, rx=8):
    return ("rect", f'x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"')


def kreis(cx, cy, r):
    return ("circle", f'cx="{cx}" cy="{cy}" r="{r}"')


def pfad(d):
    return ("path", f'd="{d}"')


def poly(punkte, schluss=True):
    return pfad("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in punkte) + (" Z" if schluss else ""))


# --- Bausteine ---------------------------------------------------------------

def flaeche(form, fill, kontur=TINTE, sw=S, licht=True):
    """Flaeche + Lichtkante (innen oben links) + Tintenkontur. Das Rezept."""
    tag, attrs = form
    _zaehler[0] += 1
    cid = f"k{_zaehler[0]}"
    teile = [f'<{tag} {attrs} fill="{fill}"/>']
    if licht:
        teile.append(f'<clipPath id="{cid}"><{tag} {attrs}/></clipPath>')
        teile.append(f'<g clip-path="url(#{cid})"><g transform="translate(4 4)">'
                     f'<{tag} {attrs} fill="none" stroke="#FFFFFF" stroke-opacity="0.4" stroke-width="6" '
                     f'stroke-linejoin="round"/></g></g>')
    teile.append(f'<{tag} {attrs} fill="none" stroke="{kontur}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
    return "\n".join(teile)


def linie(d, sw=S, farbe=TINTE):
    return (f'<path d="{d}" fill="none" stroke="{farbe}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def rohr(d, w, farbe):
    """Dicke Linie mit Tintenrand (Buegel, Griffe, Kabel)."""
    return linie(d, w + 2 * S, TINTE) + "\n" + linie(d, w, farbe)


def punkt(cx, cy, r=4, farbe=TINTE):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{farbe}"/>'


def stern_pfad(cx=64, cy=66, r1=52, r2=25, zacken=5):
    pts = []
    for i in range(zacken * 2):
        r = r1 if i % 2 == 0 else r2
        w = -math.pi / 2 + i * math.pi / zacken
        pts.append((cx + r * math.cos(w), cy + r * math.sin(w)))
    return poly(pts)


def zahnrad_pfad(cx=64, cy=64, aussen=50, innen=38, zaehne=8):
    pts = []
    schritt = 2 * math.pi / zaehne
    for i in range(zaehne):
        w = i * schritt
        for dw, r in ((-0.28, innen), (-0.17, aussen), (0.17, aussen), (0.28, innen)):
            a = w + dw * schritt * 1.6
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


# --- Die 28 UI-Symbole ----------------------------------------------------------

SYMBOLE = {}


def sym(name, *teile):
    SYMBOLE[name] = svg("\n".join(teile))


sym("bilderrahmen",
    flaeche(rect(14, 20, 100, 88, 12), GOLD),
    flaeche(rect(30, 36, 68, 56, 4), PAPIER, sw=5),
    flaeche(poly([(30, 92), (52, 62), (66, 78), (78, 66), (98, 92)]), GOLD, sw=5, licht=False),
    punkt(80, 50, 6))

sym("blitz", flaeche(pfad("M76 10 L24 72 H57 L48 118 L104 52 H70 Z"), GOLD))

sym("clip",
    flaeche(rect(20, 10, 88, 108, 14), PAPIER),
    flaeche(rect(32, 22, 64, 48, 6), WARNUNG, sw=5),
    flaeche(poly([(56, 34), (56, 58), (78, 46)]), PAPIER, sw=4, licht=False),
    linie("M34 86 H94 M34 102 H72", 6))

sym("diamant",
    flaeche(pfad("M34 16 H94 L120 48 L64 114 L8 48 Z"), HIMMEL),
    linie("M8 48 H120 M34 16 L48 48 L64 114 M94 16 L80 48 L64 114 M48 48 L64 16 L80 48", 4.5))

sym("geschenk",
    flaeche(rect(18, 56, 92, 58, 8), WARNUNG),
    flaeche(rect(10, 38, 108, 26, 8), WARNUNG),
    flaeche(rect(52, 38, 24, 76, 4), GOLD, licht=False),
    flaeche(pfad("M64 38 C50 10 26 16 34 30 C40 40 56 38 64 38 C72 38 88 40 94 30 C102 16 78 10 64 38 Z"),
            GOLD, licht=False))

sym("haken",
    flaeche(kreis(64, 64, 52), KAUFEN),
    linie("M38 66 L57 84 L92 46", 12))

sym("handy",
    flaeche(rect(30, 6, 68, 116, 16), BLAU),
    flaeche(rect(39, 22, 50, 78, 6), PAPIER, sw=4),
    linie("M48 40 H68 M60 56 H80 M48 72 H66", 7),
    punkt(64, 111, 4.5, PAPIER))

sym("haus",
    flaeche(pfad("M22 60 V112 H106 V60"), PAPIER),
    flaeche(pfad("M10 64 L64 14 L118 64 Z"), WARNUNG),
    flaeche(rect(50, 76, 28, 36, 5), WARNUNG, sw=5, licht=False),
    flaeche(rect(28, 72, 16, 16, 3), PAPIER, sw=4, licht=False),
    flaeche(rect(84, 72, 16, 16, 3), PAPIER, sw=4, licht=False))

sym("herz",
    flaeche(pfad("M64 114 C12 78 8 40 30 24 C46 13 60 20 64 34 C68 20 82 13 98 24 C120 40 116 78 64 114 Z"),
            WARNUNG))

sym("hochhaus",
    flaeche(rect(14, 52, 34, 66, 5), PAPIER),
    flaeche(rect(80, 42, 34, 76, 5), PAPIER),
    flaeche(rect(36, 10, 56, 108, 6), BLAU),
    linie("M50 28 H60 M70 28 H78 M50 48 H60 M70 48 H78 M50 68 H60 M70 68 H78", 7, PAPIER),
    flaeche(rect(54, 92, 20, 26, 4), PAPIER, sw=5, licht=False))

sym("kaufpfeil",
    flaeche(kreis(64, 64, 52), KAUFEN),
    flaeche(pfad("M64 24 L94 58 H76 V92 H52 V58 H34 Z"), PAPIER, sw=5))

sym("muenze",
    flaeche(kreis(64, 64, 52), GOLD),
    f'<circle cx="64" cy="64" r="37" fill="none" stroke="{GOLD_TIEF}" stroke-width="5"/>',
    linie("M80 46 A24 24 0 1 0 80 82", 9),
    linie("M42 58 H68 M42 70 H68", 7))

sym("pfeil_hoch", flaeche(pfad("M64 12 L112 62 H82 V116 H46 V62 H16 Z"), TINTE))

sym("play",
    flaeche(kreis(64, 64, 52), PAPIER),
    flaeche(poly([(50, 36), (94, 64), (50, 92)]), TINTE, licht=False))

sym("saeule",
    flaeche(rect(26, 32, 76, 68, 3), PAPIER),
    linie("M44 40 V94 M64 40 V94 M84 40 V94", 6),
    flaeche(rect(12, 12, 104, 22, 7), GOLD),
    flaeche(rect(12, 98, 104, 22, 7), GOLD))

sym("schliessen",
    flaeche(kreis(64, 64, 52), PAPIER),
    linie("M44 44 L84 84 M84 44 L44 84", 13))

sym("schloss",
    rohr("M42 56 V40 A22 22 0 0 1 86 40 V56", 8, PAPIER),
    flaeche(rect(18, 54, 92, 62, 14), GOLD),
    punkt(64, 78, 8),
    linie("M64 82 V96", 8))

sym("stern", flaeche(stern_pfad(), GOLD))

sym("stern_leer", flaeche(stern_pfad(), PAPIER_2, kontur=TINTE_2))

sym("tasche",
    rohr("M44 48 V36 A20 20 0 0 1 84 36 V48", 6, PAPIER),
    flaeche(pfad("M16 42 H112 L104 116 H24 Z"), BLAU),
    punkt(46, 60, 5, PAPIER), punkt(82, 60, 5, PAPIER))

sym("tisch",
    flaeche(rect(20, 52, 14, 62, 5), HONIG),
    flaeche(rect(94, 52, 14, 62, 5), HONIG),
    flaeche(rect(10, 34, 108, 24, 8), HONIG),
    flaeche(rect(42, 8, 44, 30, 5), PAPIER, sw=5))

_lautsprecher = flaeche(pfad("M12 46 H34 L64 20 V108 L34 82 H12 Z"), BLAU)
sym("ton_an", _lautsprecher,
    linie("M80 46 A26 26 0 0 1 80 82", 9),
    linie("M96 28 A46 46 0 0 1 96 100", 9))
sym("ton_aus", _lautsprecher,
    linie("M82 48 L114 80 M114 48 L82 80", 10))

sym("uhr",
    flaeche(rect(50, 6, 28, 14, 5), GOLD_TIEF, licht=False),
    flaeche(kreis(64, 68, 50), GOLD),
    flaeche(kreis(64, 68, 34), PAPIER, sw=5, licht=False),
    linie("M64 68 V44 M64 68 L80 78", 8),
    punkt(64, 68, 5))

sym("warnung",
    flaeche(pfad("M64 10 L120 108 H8 Z"), WARNUNG),
    linie("M64 46 V74", 12),
    punkt(64, 92, 7.5))

sym("werkzeug",
    flaeche(pfad("M90 10 A28 28 0 0 0 62 48 L18 92 A12 12 0 0 0 36 110 L80 66 A28 28 0 0 0 118 38 "
                 "L98 50 L82 44 L78 26 Z"), GOLD),
    punkt(27, 101, 5))

sym("zahnrad",
    flaeche(zahnrad_pfad(), BLAU),
    flaeche(kreis(64, 64, 16), PAPIER, licht=False))

sym("ziel",
    flaeche(kreis(60, 68, 48), PAPIER),
    flaeche(kreis(60, 68, 32), WARNUNG, sw=5, licht=False),
    flaeche(kreis(60, 68, 17), PAPIER, sw=5, licht=False),
    punkt(60, 68, 6),
    linie("M60 68 L104 24", 8),
    flaeche(pfad("M96 10 L118 8 L112 30 L100 28 Z"), PAPIER, sw=5, licht=False))


# --- Bereichssymbole Welt 1-5 --------------------------------------------------
# Akzent der Welt + Creme + Tinte. Reihenfolge = bereich_1 .. bereich_5 laut theme.json.

WELTEN = {
    "zimmer": "#3D7BFF",
    "auftrag": "#FF4FA3",
    "webseiten": "#FF7A1A",
    "buero": "#12B5A5",
    "produkt": "#8B5CF6",
}

BEREICHE = {}


def bereich(welt, n, *teile):
    BEREICHE[(welt, n)] = svg("\n".join(teile))


def _a(welt):
    return WELTEN[welt]


# W1 Die WG: Flur=Router, Kueche=Topf, Wohnzimmer=Sofa, Balkon=Sonne+Gelaender, freies Zimmer=Bett
w = "zimmer"; A = _a(w)
bereich(w, 1,
        linie("M38 70 L26 26 M90 70 L102 26", 8),
        punkt(26, 24, 7), punkt(102, 24, 7),
        flaeche(rect(10, 68, 108, 44, 14), A),
        punkt(34, 90, 6, PAPIER), punkt(54, 90, 6, PAPIER), linie("M78 90 H100", 7, PAPIER))
bereich(w, 2,
        linie("M42 34 C34 24 50 18 42 8 M64 34 C56 24 72 18 64 8 M86 34 C78 24 94 18 86 8", 6),
        flaeche(rect(10, 50, 108, 14, 7), PAPIER),
        flaeche(pfad("M20 62 H108 V94 A18 18 0 0 1 90 112 H38 A18 18 0 0 1 20 94 Z"), A),
        linie("M8 80 H20 M108 80 H120", 8))
bereich(w, 3,
        flaeche(rect(18, 26, 92, 52, 18), A),
        flaeche(rect(32, 54, 64, 34, 10), PAPIER),
        flaeche(rect(8, 52, 26, 52, 12), A),
        flaeche(rect(94, 52, 26, 52, 12), A),
        linie("M30 112 V118 M98 112 V118", 8))
bereich(w, 4,
        flaeche(kreis(64, 44, 26), PAPIER),
        linie("M64 6 V10 M24 24 L28 28 M104 24 L100 28 M12 52 H16 M112 52 H116", 7),
        flaeche(rect(10, 70, 108, 12, 6), A),
        flaeche(rect(16, 82, 14, 32, 5), A), flaeche(rect(57, 82, 14, 32, 5), A),
        flaeche(rect(98, 82, 14, 32, 5), A))
bereich(w, 5,
        flaeche(rect(10, 22, 16, 92, 6), A),
        flaeche(rect(20, 62, 98, 24, 8), PAPIER),
        flaeche(rect(22, 44, 30, 20, 8), A),
        flaeche(rect(94, 86, 16, 28, 5), A),
        punkt(100, 70, 0.1, A))

# W2 Das Studio: Hof=Container, Requisitenlager=Kisten, Greenscreen=Wand+Figur, Dach=Sonne ueber Dach, Kino=Popcorn
w = "auftrag"; A = _a(w)
bereich(w, 1,
        flaeche(rect(8, 36, 112, 72, 8), A),
        linie("M30 46 V98 M50 46 V98 M70 46 V98 M90 46 V98", 6),
        flaeche(rect(98, 62, 22, 46, 6), PAPIER, sw=5, licht=False),
        linie("M14 114 H114", 6))
bereich(w, 2,
        flaeche(rect(10, 66, 52, 48, 6), A),
        flaeche(rect(66, 66, 52, 48, 6), PAPIER),
        flaeche(rect(34, 16, 56, 48, 6), A),
        linie("M20 82 H52 M76 82 H108 M44 32 H80", 6, PAPIER))
bereich(w, 3,
        flaeche(rect(10, 14, 108, 72, 8), A),
        flaeche(kreis(64, 52, 14), PAPIER),
        flaeche(pfad("M32 86 C32 66 46 66 64 66 C82 66 96 66 96 86 Z"), PAPIER),
        flaeche(rect(10, 98, 108, 16, 7), PAPIER))
bereich(w, 4,
        flaeche(pfad("M24 70 A40 40 0 0 1 104 70 Z"), PAPIER),
        linie("M64 8 V16 M22 28 L28 34 M106 28 L100 34", 7),
        flaeche(rect(8, 70, 112, 44, 6), A),
        linie("M26 88 H44 M58 88 H76 M90 88 H102", 7, PAPIER))
bereich(w, 5,
        flaeche(kreis(40, 30, 18), PAPIER), flaeche(kreis(64, 22, 20), PAPIER),
        flaeche(kreis(88, 30, 18), PAPIER),
        flaeche(pfad("M18 52 H110 L98 116 H30 Z"), A),
        linie("M50 58 L54 112 M64 58 V112 M78 58 L74 112", 6, PAPIER))

# W3 Merch-Laden: Verkaufsraum=Markise, Keller=Regal, Showroom=Puppe, Fotostudio=Kamera, Hinterzimmer=Shirt
w = "webseiten"; A = _a(w)
bereich(w, 1,
        flaeche(rect(16, 58, 96, 56, 4), PAPIER),
        flaeche(pfad("M8 58 L20 16 H108 L120 58 Z"), A),
        linie("M42 16 L38 58 M64 16 V58 M86 16 L90 58", 5),
        flaeche(rect(50, 74, 28, 40, 4), A, sw=5, licht=False),
        flaeche(rect(22, 72, 20, 18, 3), PAPIER_2, sw=4, licht=False))
bereich(w, 2,
        linie("M18 14 V116 M110 14 V116", 8),
        flaeche(rect(14, 36, 100, 10, 3), PAPIER),
        flaeche(rect(14, 76, 100, 10, 3), PAPIER),
        flaeche(rect(26, 12, 32, 24, 4), A), flaeche(rect(66, 14, 28, 22, 4), A),
        flaeche(rect(30, 52, 40, 24, 4), A), flaeche(rect(76, 56, 26, 20, 4), A),
        flaeche(rect(26, 90, 32, 24, 4), A), flaeche(rect(66, 92, 36, 22, 4), A))
bereich(w, 3,
        flaeche(pfad("M46 10 H82 L88 28 C98 46 90 66 82 80 H46 C38 66 30 46 40 28 Z"), A),
        linie("M64 80 V104", 8),
        flaeche(rect(26, 102, 76, 14, 7), PAPIER),
        linie("M46 38 H82", 5))
bereich(w, 4,
        flaeche(rect(10, 34, 108, 74, 14), A),
        flaeche(rect(36, 18, 28, 20, 5), A),
        flaeche(kreis(64, 72, 26), PAPIER),
        flaeche(kreis(64, 72, 12), A, sw=5, licht=False),
        punkt(100, 50, 5, PAPIER))
bereich(w, 5,
        flaeche(pfad("M40 12 L8 34 L22 58 L36 52 V114 H92 V52 L106 58 L120 34 L88 12 C84 24 74 28 64 28 "
                     "C54 28 44 24 40 12 Z"), A),
        flaeche(kreis(64, 76, 15), PAPIER, sw=5, licht=False))

# W4 Das Lager: Gang=Foerderband, Wareneingang=Rolltor, Haendlerbuero=Aktentasche, Hochregal=Regal, Laderampe=Transporter
w = "buero"; A = _a(w)
bereich(w, 1,
        flaeche(rect(34, 28, 44, 34, 5), PAPIER),
        flaeche(rect(8, 68, 112, 24, 12), A),
        flaeche(kreis(26, 106, 10), PAPIER, sw=5, licht=False),
        flaeche(kreis(64, 106, 10), PAPIER, sw=5, licht=False),
        flaeche(kreis(102, 106, 10), PAPIER, sw=5, licht=False))
bereich(w, 2,
        flaeche(rect(14, 14, 100, 102, 6), PAPIER),
        flaeche(rect(26, 26, 76, 90, 3), A),
        linie("M26 46 H102 M26 66 H102 M26 86 H102", 5),
        flaeche(rect(54, 100, 20, 8, 4), PAPIER, sw=4, licht=False))
bereich(w, 3,
        rohr("M44 40 V30 A8 8 0 0 1 52 22 H76 A8 8 0 0 1 84 30 V40", 6, PAPIER),
        flaeche(rect(10, 38, 108, 76, 12), A),
        linie("M10 70 H118", 6),
        flaeche(rect(54, 62, 20, 18, 4), PAPIER, sw=5, licht=False))
bereich(w, 4,
        linie("M20 12 V118 M108 12 V118", 8),
        flaeche(rect(16, 40, 96, 8, 3), PAPIER), flaeche(rect(16, 80, 96, 8, 3), PAPIER),
        flaeche(rect(30, 14, 28, 26, 4), A), flaeche(rect(66, 18, 28, 22, 4), A),
        flaeche(rect(30, 54, 44, 26, 4), A),
        flaeche(rect(32, 92, 28, 24, 4), A), flaeche(rect(68, 92, 28, 24, 4), A))
bereich(w, 5,
        flaeche(rect(6, 34, 76, 64, 6), A),
        flaeche(pfad("M82 52 H104 L120 72 V98 H82 Z"), PAPIER),
        flaeche(rect(92, 58, 14, 14, 3), PAPIER_2, sw=4, licht=False),
        flaeche(kreis(30, 100, 13), PAPIER, sw=6, licht=False),
        flaeche(kreis(98, 100, 13), PAPIER, sw=6, licht=False))

# W5 Die Farm: Kabeltrasse=Stecker, Trafo=Trafokasten, Kontrollraum=Monitor, Solardach=Panel, zweite Halle=Halle
w = "produkt"; A = _a(w)
bereich(w, 1,
        linie("M42 14 V36 M70 14 V36", 9),
        flaeche(rect(26, 34, 58, 38, 12), A),
        rohr("M55 72 V90 C55 108 85 104 96 116", 8, A),
        punkt(40, 52, 4, PAPIER), punkt(70, 52, 4, PAPIER))
bereich(w, 2,
        flaeche(rect(20, 40, 88, 74, 8), A),
        flaeche(pfad("M64 50 L46 80 H62 L56 104 L82 70 H66 L72 50 Z"), PAPIER, sw=5, licht=False),
        linie("M34 40 V26 M64 40 V20 M94 40 V26", 8),
        punkt(34, 24, 6), punkt(64, 18, 6), punkt(94, 24, 6))
bereich(w, 3,
        flaeche(rect(8, 14, 112, 74, 10), A),
        flaeche(rect(20, 26, 88, 50, 4), PAPIER, sw=5),
        linie("M30 66 L50 48 L68 60 L96 36", 6),
        flaeche(rect(50, 88, 28, 12, 3), A, sw=5, licht=False),
        flaeche(rect(32, 100, 64, 14, 7), A))
bereich(w, 4,
        flaeche(kreis(100, 28, 15), PAPIER),
        linie("M100 4 V6 M76 28 H78", 6),
        flaeche(poly([(30, 44), (118, 44), (100, 112), (12, 112)]), A),
        linie("M26 78 H108 M54 44 L46 112 M82 44 L74 112", 5, PAPIER))
bereich(w, 5,
        flaeche(rect(86, 12, 16, 40, 3), PAPIER),
        flaeche(pfad("M10 112 V54 L38 38 V54 L66 38 V54 L94 38 V112 Z"), A),
        flaeche(rect(94, 56, 24, 56, 4), PAPIER),
        flaeche(rect(26, 76, 20, 36, 3), PAPIER, sw=5, licht=False),
        flaeche(rect(56, 76, 20, 36, 3), PAPIER, sw=5, licht=False))


# --- Ausgabe ------------------------------------------------------------------------

def kontaktbogen(dateien, ziel, spalten, zelle=150, bg=PAPIER):
    from playwright.sync_api import sync_playwright
    teile = []
    for f in dateien:
        b64 = base64.b64encode(pathlib.Path(f).read_bytes()).decode()
        quelle = f"data:image/svg+xml;base64,{b64}"
        teile.append(f'<div class="c"><img src="{quelle}" width="{zelle - 56}"><img src="{quelle}" width="32">'
                     f'<img src="{quelle}" width="48"><br>{pathlib.Path(f).stem}</div>')
    zeilen = (len(dateien) + spalten - 1) // spalten
    html = (f'<body style="margin:0;background:{bg};font:11px sans-serif"><style>.c{{display:inline-block;'
            f'width:{zelle}px;height:{zelle}px;text-align:center;vertical-align:top;padding-top:6px;'
            f'box-sizing:border-box}}</style>' + "".join(teile))
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": spalten * zelle, "height": zeilen * zelle})
        pg.set_content(html)
        pg.screenshot(path=str(ziel))
        br.close()


if __name__ == "__main__":
    out = []
    for name, text in SYMBOLE.items():
        p = UI / "symbole" / f"{name}.svg"
        p.write_text(text, encoding="utf-8")
        out.append(p)
    print(len(SYMBOLE), "Symbole geschrieben")
    bpfade = []
    for (welt, n), text in BEREICHE.items():
        p = UI / welt / f"bereich_{n}.svg"
        p.write_text(text, encoding="utf-8")
        bpfade.append(p)
    print(len(BEREICHE), "Bereichssymbole geschrieben")
    if "--vorschau" in sys.argv:
        VORSCHAU.mkdir(exist_ok=True)
        kontaktbogen(out, VORSCHAU / "symbole.png", 7)
        kontaktbogen(bpfade, VORSCHAU / "bereiche.png", 5)
        print("Kontaktboegen: art_source/vorschau/symbole.png, bereiche.png")
