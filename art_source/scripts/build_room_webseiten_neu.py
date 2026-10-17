"""Architektur-Baukasten fuer Welt 3 `webseiten` -- der Eckladen mit Werkstatt
(docs/NACHT_PLAN.md 2 und 5, Aufgabe N20).

Aufruf:
    blender --background --python art_source/scripts/build_room_webseiten_neu.py
    (optional nach "--": --ohne-vorschau)

Erzeugt nach project/assets/room/webseiten/:
    boden_<typ>_a/_b  fuer beton, fliese, holz, studio -- 1 x 1 m, Oberkante y = 0,
                      0,06 dick nach unten, EIN Mesh
    wand_voll, wand_voll_fenster (Schaufenster), wand_halb, wand_halb_tuer,
    wand_sockel, wand_sockel_tuer (Glastuer), gelaender, pfosten_voll/halb/sockel
    raum_fliese_a/_b/_weg, raum_wand, raum_wand_ecke, raum_wand_tuer,
    raum_wand_fenster  (Altmodule fuer validate Schritt 7)
und Uebersichten nach art_source/vorschau/webseiten/.

Masse, Ursprung und Ausrichtung sind EXAKT die der wg_*-Module aus Welt 1
(build_room_wg.py): Waende 1 m entlang lokal X, 0,2 dick, Ursprung unten Mitte,
Innenseite bei lokal +z, Hoehen 2,4 / 1,2 / 0,35, Pfosten 0,22 im Quadrat.
Nur Stoffe und Formen sind neu: heller Putz, Kappe aus hellem Holz,
schwarze Stahlrahmen, Terrazzo, Beton, Studioboden.

Die Werkzeuge (Koordinaten, Grundkoerper, Export, Vorschau) kommen aus
build_room_wg.py. Alle Masse in GODOT-Koordinaten.
"""

import bpy
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, kugel, profil_x, rundprofil, kissen_platte,
    transformieren, alles_loeschen, verbinden, dreiecke, masse, exportieren,
    importieren, vorschau_rendern, palette_erweitern, _dielen_ab,
    WURZEL,
)

AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "webseiten")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "webseiten")
HINTERGRUND = "#FBE3CF"

# Toene (sRGB-Hex, material() rechnet linear um). Namen nach Stoff und Ton.
palette_erweitern({
    # Architektur
    "l3_putz":          ("#F5F0E8", 0.88, 0.0, 1.0),
    "l3_putz_leiste":   ("#DCD5CA", 0.80, 0.0, 1.0),
    "l3_kappe":         ("#DDB17C", 0.72, 0.0, 1.0),
    "l3_stahl_schwarz": ("#2E2D33", 0.45, 0.35, 1.0),
    "l3_glas":          ("#BFE3F2", 0.15, 0.0, 1.0),
    "l3_glas_tuer":     ("#CDEBF6", 0.10, 0.0, 0.45),
    "l3_orange":        ("#FF7A1A", 0.60, 0.0, 1.0),
    # Beton
    "l3_beton_a":       ("#BEBAB3", 0.92, 0.0, 1.0),
    "l3_beton_b":       ("#B9B5AE", 0.92, 0.0, 1.0),
    "l3_beton_fleck":   ("#ACA8A1", 0.95, 0.0, 1.0),
    "l3_beton_fuge":    ("#98948D", 0.95, 0.0, 1.0),
    # Terrazzo
    "l3_terrazzo":      ("#F3F0EB", 0.45, 0.0, 1.0),
    "l3_terrazzo2":     ("#EEEAE3", 0.45, 0.0, 1.0),
    "l3_terrazzo_fuge": ("#D6D0C6", 0.90, 0.0, 1.0),
    "l3_korn_orange":   ("#FFA468", 0.50, 0.0, 1.0),
    "l3_korn_grau":     ("#A6A29C", 0.50, 0.0, 1.0),
    "l3_korn_dunkel":   ("#6F6B67", 0.50, 0.0, 1.0),
    # Holz hell (Eiche geoelt)
    "l3_eiche_a":       ("#E9C89B", 0.78, 0.0, 1.0),
    "l3_eiche_a2":      ("#E3BF8F", 0.78, 0.0, 1.0),
    "l3_eiche_b":       ("#DDB787", 0.78, 0.0, 1.0),
    "l3_eiche_b2":      ("#ECCFA6", 0.78, 0.0, 1.0),
    "l3_eiche_fuge":    ("#BB9163", 0.90, 0.0, 1.0),
    # Studio (Epoxid, fast weiss)
    "l3_studio":        ("#F1F1EE", 0.35, 0.0, 1.0),
    "l3_studio2":       ("#ECECE8", 0.35, 0.0, 1.0),
    "l3_studio_fuge":   ("#D5D4CF", 0.90, 0.0, 1.0),
    # M2: Terrazzo warm-sandig (D1 Welt 3), Schachbrett, Farbbeton
    "l3_terra_a":       ("#D9CDB8", 0.50, 0.0, 1.0),
    "l3_terra_b":       ("#D2C5AE", 0.50, 0.0, 1.0),
    "l3_terra_fuge":    ("#A99A82", 0.90, 0.0, 1.0),
    "l3_terra_korn1":   ("#B7A58E", 0.55, 0.0, 1.0),
    "l3_terra_korn2":   ("#F1E9DA", 0.55, 0.0, 1.0),
    "l3_terra_korn3":   ("#8C7E6B", 0.55, 0.0, 1.0),
    "l3_terra_korn4":   ("#E39A57", 0.55, 0.0, 1.0),
    "l3_schach_dunkel": ("#2C2A2E", 0.40, 0.0, 1.0),
    "l3_schach_hell":   ("#F3EEE6", 0.40, 0.0, 1.0),
    "l3_schach_fuge":   ("#9A958D", 0.85, 0.0, 1.0),
    "l3_farbbeton_a":   ("#8E8B86", 0.92, 0.0, 1.0),
    "l3_farbbeton_b":   ("#868380", 0.92, 0.0, 1.0),
    "l3_klecks_orange": ("#F07A22", 0.70, 0.0, 1.0),
    "l3_klecks_blau":   ("#3D6FD1", 0.70, 0.0, 1.0),
    "l3_klecks_gelb":   ("#F2C94C", 0.70, 0.0, 1.0),
    "l3_klecks_pink":   ("#E0558F", 0.70, 0.0, 1.0),
})

MATERIAL_WAND = "l3_putz"


# ==============================================================================
# BOEDEN
# ==============================================================================
# Wie in Welt 1: Tragplatte in Fugenfarbe, darauf "Kissen"-Platten mit
# Oberkante genau y = 0. Beton und Studio bestehen aus EINER Platte je Meter
# mit sehr feiner Fase -- die Meterfuge ahnt man wie einen Fugenschnitt.
# Streu-Details (Koerner, Flecken) liegen exakt auf y = 0, die Platte darunter
# bei -0,0008: kein Z-Fighting, und die Oberkante bleibt 0.

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def _flach_polygon(name, punkte, y, mat_name):
    """Flaches n-Eck auf Hoehe y (Godot, Punkte (x, z)), Normale nach oben."""
    import bmesh
    from build_room_wg import _objekt
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for (x, z) in punkte]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat_name)


def _streuung(seed, anzahl, groesse, mats, rand=0.06, bereich=0.5):
    """Kleine unregelmaessige Dreiecke (Terrazzo-Koerner, Betonporen)."""
    rng = random.Random(seed)
    teile = []
    for i in range(anzahl):
        cx = rng.uniform(-bereich + rand, bereich - rand)
        cz = rng.uniform(-bereich + rand, bereich - rand)
        s = groesse * rng.uniform(0.6, 1.3)
        a = rng.uniform(0, 2 * math.pi)
        pkt = [(cx + math.cos(a + k * 2.1 + rng.uniform(-0.3, 0.3)) * s,
                cz + math.sin(a + k * 2.1 + rng.uniform(-0.3, 0.3)) * s) for k in range(3)]
        teile.append(_flach_polygon("korn", pkt, 0.0, mats[i % len(mats)]))
    return teile


def boden_beton(variante):
    teile = [_tragplatte("l3_beton_fuge", -0.006)]
    ton = "l3_beton_a" if variante == "a" else "l3_beton_b"
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, -0.0008, -0.006, 0.005, ton))
    # Poren und eine flache Schattierung -- a und b verschieden, damit das
    # Schachbrett nicht als Muster auffaellt.
    if variante == "a":
        teile += _streuung(31, 7, 0.018, ["l3_beton_fleck"])
    else:
        teile += _streuung(57, 6, 0.018, ["l3_beton_fleck"])
    return teile


def boden_fliese(variante):
    """Terrazzo-Platten 50 x 50 mit bunten Koernern (Orange als Weltakzent)."""
    teile = [_tragplatte("l3_terrazzo_fuge", -0.006)]
    for i in range(2):
        for k in range(2):
            x0, z0 = -0.5 + i * 0.5, -0.5 + k * 0.5
            ton = "l3_terrazzo2" if (variante == "b" and (i, k) == (1, 0)) else "l3_terrazzo"
            teile.append(kissen_platte("fliese", x0, x0 + 0.5, z0, z0 + 0.5, -0.0008, -0.006, 0.012, ton))
    mats = ["l3_korn_orange", "l3_korn_grau", "l3_korn_dunkel", "l3_korn_grau"]
    teile += _streuung(11 if variante == "a" else 23, 18, 0.02, mats, rand=0.05)
    return teile


def boden_terrazzo(variante):
    """Terrazzo 50 x 50 warm-sandig mit Koernern in Sand, Creme, Braun (D1 Welt 3)."""
    teile = [_tragplatte("l3_terra_fuge", -0.006)]
    for i in range(2):
        for k in range(2):
            x0, z0 = -0.5 + i * 0.5, -0.5 + k * 0.5
            ton = "l3_terra_b" if (variante == "b" and (i, k) == (1, 0)) or (variante == "a" and (i, k) == (0, 1)) else "l3_terra_a"
            teile.append(kissen_platte("fliese", x0, x0 + 0.5, z0, z0 + 0.5, -0.0008, -0.006, 0.012, ton))
    mats = ["l3_terra_korn1", "l3_terra_korn2", "l3_terra_korn3", "l3_terra_korn1", "l3_terra_korn2", "l3_terra_korn4"]
    teile += _streuung(111 if variante == "a" else 123, 22, 0.02, mats, rand=0.05)
    return teile


def boden_schachbrett(variante):
    """Schwarz-weisse Schachbrettfliese 50 x 50 -- a und b gleich, das Muster
    setzt sich ueber die Modulgrenzen fort."""
    teile = [_tragplatte("l3_schach_fuge", -0.006)]
    for i in range(2):
        for k in range(2):
            x0, z0 = -0.5 + i * 0.5, -0.5 + k * 0.5
            ton = "l3_schach_dunkel" if (i + k) % 2 == 0 else "l3_schach_hell"
            teile.append(kissen_platte("fliese", x0, x0 + 0.5, z0, z0 + 0.5, -0.0008, -0.006, 0.008, ton))
    return teile


def boden_farbbeton(variante):
    """Werkstattbeton mit Farbklecksen (Sieb-Abstreifer) in Orange, Blau, Gelb, Pink."""
    teile = [_tragplatte("l3_beton_fuge", -0.006)]
    ton = "l3_farbbeton_a" if variante == "a" else "l3_farbbeton_b"
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, -0.0008, -0.006, 0.005, ton))
    teile += _streuung(31 if variante == "a" else 57, 6, 0.018, ["l3_beton_fleck"])
    if variante == "a":
        teile += _streuung(71, 2, 0.07, ["l3_klecks_orange"], rand=0.12)
        teile += _streuung(72, 1, 0.05, ["l3_klecks_blau"], rand=0.12)
    else:
        teile += _streuung(81, 1, 0.08, ["l3_klecks_gelb"], rand=0.12)
        teile += _streuung(82, 2, 0.05, ["l3_klecks_pink"], rand=0.12)
        teile += _streuung(83, 1, 0.06, ["l3_klecks_blau"], rand=0.12)
    return teile


_EICHE_TOENE = [("l3_eiche_a", "l3_eiche_b"), ("l3_eiche_b2", "l3_eiche_a"),
                ("l3_eiche_a2", "l3_eiche_b2"), ("l3_eiche_b", "l3_eiche_a2"),
                ("l3_eiche_a", "l3_eiche_b2")]
_EICHE_FUGEN_A = (0.1, -0.3, 0.25, -0.05, 0.35)
_EICHE_FUGEN_B = (-0.25, 0.15, -0.35, 0.3, -0.12)


def boden_holz(variante):
    return _dielen_ab(_EICHE_TOENE, _EICHE_FUGEN_A, _EICHE_FUGEN_B, 0.2, variante, "l3_eiche_fuge")


def boden_studio(variante):
    teile = [_tragplatte("l3_studio_fuge", -0.004)]
    ton = "l3_studio" if variante == "a" else "l3_studio2"
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004, ton))
    return teile


# ==============================================================================
# WAENDE
# ==============================================================================

WAND_DICKE = 0.20
KAPPE_DICKE = 0.24
KAPPE_HOEHE = 0.06
LEISTE_HOEHE = 0.08
LEISTE_DICKE = 0.22
HOEHE = {"voll": 2.4, "halb": 1.2, "sockel": 0.35}
TUER_HOEHE = 2.05
TUER_PFOSTEN_X = 0.45
TUER_PFOSTEN_B = 0.10
TUER_TIEFE = 0.26


def _kappe(hoehe, x0=-0.5, x1=0.5):
    d = KAPPE_DICKE / 2.0
    return profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.025), x0, x1, "l3_kappe")


def _leiste(hoehe, x0=-0.5, x1=0.5):
    d = LEISTE_DICKE / 2.0
    return profil_x("leiste", rundprofil(-d, d, 0.0, hoehe, 0.012, 1), x0, x1, "l3_putz_leiste")


def _koerper(x0, x1, y0, y1):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, MATERIAL_WAND)


def _leistenhoehe(hoehe):
    return min(LEISTE_HOEHE, hoehe * 0.2)


def _wand(hoehe):
    return [_koerper(-0.5, 0.5, 0.0, hoehe - KAPPE_HOEHE + 0.001),
            _kappe(hoehe), _leiste(_leistenhoehe(hoehe))]


def wand_voll():
    return _wand(HOEHE["voll"])


def wand_halb():
    return _wand(HOEHE["halb"])


def wand_sockel():
    return _wand(HOEHE["sockel"])


def wand_voll_fenster():
    """Grosses Schaufenster: Oeffnung 0,9 breit von 0,55 bis 2,15 m. Schwarzer
    Stahlrahmen, ein Kaempfer bei 1,85 (Oberlicht), keine Sprossen -- stehen
    zwei Module nebeneinander, liest es sich als ein Glasband. Innen eine
    schmale Bank aus hellem Holz."""
    h = HOEHE["voll"]
    ox, u, o = 0.45, 0.55, 2.15
    teile = [
        _koerper(-0.5, 0.5, 0.0, u),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _koerper(-0.5, -ox, u, o),
        _koerper(ox, 0.5, u, o),
        _kappe(h), _leiste(_leistenhoehe(h)),
    ]
    r = 0.045
    t = 0.10
    m = "l3_stahl_schwarz"
    teile.append(kasten("rahmen_l", (r, o - u, t), (-ox + r / 2, (u + o) / 2, 0.0), m))
    teile.append(kasten("rahmen_r", (r, o - u, t), (ox - r / 2, (u + o) / 2, 0.0), m))
    teile.append(kasten("rahmen_o", (2 * ox - 2 * r, r, t), (0.0, o - r / 2, 0.0), m))
    teile.append(kasten("rahmen_u", (2 * ox - 2 * r, r, t), (0.0, u + r / 2, 0.0), m))
    teile.append(kasten("kaempfer", (2 * ox - 2 * r, 0.035, 0.07), (0.0, 1.85, 0.0), m))
    teile.append(kasten("glas", (2 * ox - 2 * r, o - u - 2 * r, 0.02), (0.0, (u + o) / 2, 0.0), "l3_glas"))
    teile.append(kasten("bank", (0.96, 0.04, 0.36), (0.0, u - 0.02, 0.05), "l3_kappe", rund=0.012, segmente=2))
    return teile


def _tuerrahmen():
    """Holzrahmen wie in Welt 1 (Pfosten bei +-0,45, Sturz bei 2,05), aber in
    hellem Holz mit einer schwarzen Innenkante -- Werkstatt-Loft."""
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1, t), (s * TUER_PFOSTEN_X, (h - 0.1) / 2, 0.0),
                            "l3_kappe", rund=0.015, segmente=2))
        teile.append(kasten("kante", (0.012, h - 0.12, t - 0.06),
                            (s * (TUER_PFOSTEN_X - b / 2 - 0.004), (h - 0.1) / 2, 0.0), "l3_stahl_schwarz"))
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.1, t), (0.0, h - 0.05, 0.0),
                        "l3_kappe", rund=0.02, segmente=2))
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "l3_stahl_schwarz", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Ladentuer: Glastuer im schwarzen Stahlrahmen mit orangefarbener
    Stossstange. Steht wie in Welt 1 um 105 Grad nach AUSSEN (lokal -z) offen."""
    teile = _tuerrahmen()
    blatt_b, blatt_h, blatt_d = 0.78, 1.93, 0.045
    m = "l3_stahl_schwarz"
    blatt = [
        kasten("fries_l", (0.07, blatt_h, blatt_d), (0.035, blatt_h / 2 + 0.012, 0.0), m),
        kasten("fries_r", (0.07, blatt_h, blatt_d), (blatt_b - 0.035, blatt_h / 2 + 0.012, 0.0), m),
        kasten("fries_o", (blatt_b - 0.14, 0.07, blatt_d), (blatt_b / 2, blatt_h - 0.023, 0.0), m),
        kasten("fries_u", (blatt_b - 0.14, 0.16, blatt_d), (blatt_b / 2, 0.092, 0.0), m),
        kasten("glas", (blatt_b - 0.14, blatt_h - 0.23, 0.016), (blatt_b / 2, 0.172 + (blatt_h - 0.23) / 2, 0.0),
               "l3_glas_tuer"),
    ]
    for seite in (-1, 1):
        blatt.append(kasten("stange", (0.035, 0.7, 0.035), (blatt_b - 0.14, 1.0, seite * 0.07), "l3_orange",
                            rund=0.012, segmente=1))
        for y in (0.7, 1.3):
            blatt.append(kasten("halter", (0.02, 0.02, 0.05), (blatt_b - 0.14, y, seite * 0.04), m))
    scharnier_x = -TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2
    transformieren(blatt, x=scharnier_x, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    teile += blatt
    return teile


def gelaender():
    """Stahlgelaender 1 m: Handlauf aus hellem Holz bei 1,0 m, schwarzer
    Unterholm, sechs Flachstaebe. Masse wie wg_gelaender."""
    teile = [
        profil_x("handlauf", rundprofil(-0.035, 0.035, 0.95, 1.0, 0.02), -0.5, 0.5, "l3_kappe"),
        kasten("oberholm", (1.0, 0.03, 0.03), (0.0, 0.935, 0.0), "l3_stahl_schwarz"),
        kasten("unterholm", (1.0, 0.035, 0.04), (0.0, 0.10, 0.0), "l3_stahl_schwarz"),
    ]
    for i in range(6):
        x = -0.5 + (i + 0.5) / 6.0
        teile.append(kasten("stab", (0.04, 0.82, 0.012), (x, 0.51, 0.0), "l3_stahl_schwarz"))
    return teile


def _pfosten(hoehe):
    lh = _leistenhoehe(hoehe)
    return [
        kasten("saeule", (0.22, hoehe - KAPPE_HOEHE + 0.002, 0.22),
               (0.0, (hoehe - KAPPE_HOEHE) / 2 + 0.001, 0.0), MATERIAL_WAND, unten=False),
        kasten("saeule_kappe", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "l3_kappe", rund=0.022, segmente=2),
        kasten("saeule_leiste", (0.24, lh, 0.24), (0.0, lh / 2, 0.0), "l3_putz_leiste", unten=False),
    ]


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


# ==============================================================================
# ALTMODULE (validate Schritt 7) -- Masse wie room/zimmer/raum_*
# ==============================================================================

def raum_fliese(variante):
    """Duenne Platte 0,98 x 0,996, 2,6 cm dick um y = 0."""
    ton = {"a": "l3_terrazzo", "b": "l3_terrazzo2", "weg": "l3_eiche_a"}[variante]
    return [kasten("platte", (0.98, 0.026, 0.996), (0.0, 0.0, 0.0), ton, rund=0.006, segmente=1)]


def _raum_wandstueck(x0, x1, h=2.2):
    return [
        kasten("wand", (x1 - x0, h - 0.05, 0.2), ((x0 + x1) / 2, (h - 0.05) / 2, 0.0), MATERIAL_WAND),
        kasten("kappe", (x1 - x0, 0.05, 0.2), ((x0 + x1) / 2, h - 0.025, 0.0), "l3_kappe"),
    ]


def raum_wand():
    return _raum_wandstueck(-0.5, 0.5)


def raum_wand_ecke():
    """L-Ecke: Stueck entlang x (-0,5..0,53) und Stueck entlang +z bei x 0,43."""
    teile = _raum_wandstueck(-0.5, 0.53)
    teile += [
        kasten("wand_s", (0.2, 2.15, 0.83), (0.43, 1.075, 0.515), MATERIAL_WAND),
        kasten("kappe_s", (0.2, 0.05, 0.83), (0.43, 2.175, 0.515), "l3_kappe"),
    ]
    return teile


def raum_wand_tuer():
    teile = _raum_wandstueck(-1.0, -0.5) + _raum_wandstueck(0.5, 1.0)
    teile.append(kasten("sturz", (1.0, 0.2, 0.2), (0.0, 2.1, 0.0), MATERIAL_WAND))
    teile.append(kasten("rahmen_l", (0.06, 2.0, 0.2), (-0.47, 1.0, 0.0), "l3_kappe"))
    teile.append(kasten("rahmen_r", (0.06, 2.0, 0.2), (0.47, 1.0, 0.0), "l3_kappe"))
    teile.append(kasten("rahmen_o", (1.0, 0.06, 0.2), (0.0, 1.97, 0.0), "l3_kappe"))
    return teile


def raum_wand_fenster():
    h = 2.2
    teile = [
        kasten("unten", (1.0, 0.8, 0.2), (0.0, 0.4, 0.0), MATERIAL_WAND),
        kasten("oben", (1.0, h - 1.95, 0.2), (0.0, (1.95 + h) / 2, 0.0), MATERIAL_WAND),
        kasten("l", (0.08, 1.15, 0.2), (-0.46, 1.375, 0.0), MATERIAL_WAND),
        kasten("r", (0.08, 1.15, 0.2), (0.46, 1.375, 0.0), MATERIAL_WAND),
        kasten("rahmen", (0.84, 1.15, 0.1), (0.0, 1.375, 0.0), "l3_stahl_schwarz"),
        kasten("glas", (0.76, 1.07, 0.12), (0.0, 1.375, 0.0), "l3_glas"),
        kasten("bank", (1.0, 0.04, 0.26), (0.0, 0.8, 0.0), "l3_kappe"),
    ]
    return teile


MODULE = {
    "boden_beton_a": lambda: boden_beton("a"),
    "boden_beton_b": lambda: boden_beton("b"),
    "boden_fliese_a": lambda: boden_fliese("a"),
    "boden_fliese_b": lambda: boden_fliese("b"),
    "boden_holz_a": lambda: boden_holz("a"),
    "boden_holz_b": lambda: boden_holz("b"),
    "boden_terrazzo_a": lambda: boden_terrazzo("a"),
    "boden_terrazzo_b": lambda: boden_terrazzo("b"),
    "boden_schachbrett_a": lambda: boden_schachbrett("a"),
    "boden_schachbrett_b": lambda: boden_schachbrett("b"),
    "boden_farbbeton_a": lambda: boden_farbbeton("a"),
    "boden_farbbeton_b": lambda: boden_farbbeton("b"),
    "boden_studio_a": lambda: boden_studio("a"),
    "boden_studio_b": lambda: boden_studio("b"),
    "wand_voll": wand_voll,
    "wand_voll_fenster": wand_voll_fenster,
    "wand_halb": wand_halb,
    "wand_halb_tuer": wand_halb_tuer,
    "wand_sockel": wand_sockel,
    "wand_sockel_tuer": wand_sockel_tuer,
    "gelaender": gelaender,
    "pfosten_voll": pfosten_voll,
    "pfosten_halb": pfosten_halb,
    "pfosten_sockel": pfosten_sockel,
    "raum_fliese_a": lambda: raum_fliese("a"),
    "raum_fliese_b": lambda: raum_fliese("b"),
    "raum_fliese_weg": lambda: raum_fliese("weg"),
    "raum_wand": raum_wand,
    "raum_wand_ecke": raum_wand_ecke,
    "raum_wand_tuer": raum_wand_tuer,
    "raum_wand_fenster": raum_wand_fenster,
}

# Soll-Masse (Godot-BBox) aus room/zimmer/wg_* -- das Skript prueft sich selbst.
SOLL = {
    "boden": ((-0.5, 0.5), (-0.06, 0.0), (-0.5, 0.5)),
    "wand_voll": ((-0.5, 0.5), (0.0, 2.4), (-0.12, 0.12)),
    "wand_halb": ((-0.5, 0.5), (0.0, 1.2), (-0.12, 0.12)),
    "wand_sockel": ((-0.5, 0.5), (0.0, 0.35), (-0.12, 0.12)),
    "wand_voll_fenster": ((-0.5, 0.5), (0.0, 2.4), (-0.13, 0.23)),
    "wand_halb_tuer": ((-0.5, 0.5), (0.0, 2.05), (-0.13, 0.13)),
    "wand_sockel_tuer": ((-0.663, 0.5), (0.0, 2.05), (-0.876, 0.13)),
    "gelaender": ((-0.5, 0.5), (0.083, 1.0), (-0.035, 0.035)),
    "pfosten_voll": ((-0.135, 0.135), (0.0, 2.4), (-0.135, 0.135)),
    "pfosten_halb": ((-0.135, 0.135), (0.0, 1.2), (-0.135, 0.135)),
    "pfosten_sockel": ((-0.135, 0.135), (0.0, 0.35), (-0.135, 0.135)),
}


def modul_pfad(name):
    return os.path.join(AUSGABE_MODULE, name + ".glb")


def _soll_fuer(name):
    if name.startswith("boden_"):
        return SOLL["boden"]
    return SOLL.get(name)


def module_bauen():
    print("")
    print("=== MODULE WELT 3 (webseiten) ===")
    abweichungen = 0
    for name, bauen in MODULE.items():
        alles_loeschen()
        obj = verbinden(bauen(), name)
        pfad = modul_pfad(name)
        exportieren(obj, pfad)
        ist = masse(obj)
        (x0, x1), (y0, y1), (z0, z1) = ist
        hinweis = ""
        soll = _soll_fuer(name)
        if soll:
            # Rueckleseprobe: Abweichung ueber 1,5 cm von den wg_*-Massen ist ein Fehler.
            # (Das Tuerblatt darf 1,5 cm anders liegen -- es ist kein Stossmass.)
            grenze = 0.015
            for (a, b), (sa, sb) in zip(ist, soll):
                if abs(a - sa) > grenze or abs(b - sb) > grenze:
                    hinweis = "  <-- MASS WEICHT AB (soll %s)" % (soll,)
                    abweichungen += 1
                    break
        print("  %-20s %4d Dreiecke  x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f  %2d Mat  %5.1f KB%s"
              % (name, dreiecke(obj), x0, x1, y0, y1, z0, z1, len(obj.data.materials),
                 os.path.getsize(pfad) / 1024.0, hinweis))
    print("  Massabweichungen: %d" % abweichungen)
    return abweichungen


def module_vorschau():
    alles_loeschen()
    boeden = [n for n in MODULE if n.startswith("boden_")]
    for i, name in enumerate(boeden):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                importieren(modul_pfad(name), x=(i % 4) * 3.4 + dx, z=(i // 4) * 3.4 + dz)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (5.1, 0.0, 1.7), 12.0,
                     hintergrund=HINTERGRUND)

    alles_loeschen()
    zeilen = [
        ("wand_voll", "wand_voll_fenster", "pfosten_voll"),
        ("wand_halb", "wand_halb_tuer", "pfosten_halb"),
        ("wand_sockel", "wand_sockel_tuer", "pfosten_sockel"),
    ]
    for r, (wand, sonder, pfosten) in enumerate(zeilen):
        z = r * 3.0
        for dx, modul in ((0, wand), (1, sonder), (2, sonder), (3, wand)):
            importieren(modul_pfad(modul), x=dx, z=z)
        importieren(modul_pfad(pfosten), x=-0.5, z=z)
        importieren(modul_pfad(wand), x=-0.5, z=z + 0.5, dreh_grad=90.0)
        importieren(modul_pfad(wand), x=-0.5, z=z + 1.5, dreh_grad=90.0)
        for dx in range(4):
            importieren(modul_pfad("boden_fliese_%s" % ("a" if dx % 2 == 0 else "b")), x=dx, z=z + 1)
    for dx in range(3):
        importieren(modul_pfad("gelaender"), x=5.5 + dx, z=0.0)
        importieren(modul_pfad("boden_holz_%s" % ("a" if dx % 2 == 0 else "b")), x=5.5 + dx, z=0.5)
    for i, n in enumerate(["raum_fliese_a", "raum_wand", "raum_wand_fenster", "raum_wand_tuer", "raum_wand_ecke"]):
        importieren(modul_pfad(n), x=5.0 + i * 1.3 - (0.3 if n == "raum_wand_tuer" else 0), z=4.5 + i * 0.6)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_waende.png"), (3.5, 0.8, 3.2), 11.0,
                     hintergrund=HINTERGRUND)


if __name__ == "__main__":
    module_bauen()
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--ohne-vorschau" not in argumente:
        module_vorschau()
