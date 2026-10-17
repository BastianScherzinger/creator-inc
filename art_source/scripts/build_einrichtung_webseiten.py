"""Raumeinrichtungen fuer Welt 3 `webseiten` -- der Eckladen mit Werkstatt
(docs/NACHT_PLAN.md 2 und 5, Aufgabe N20).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_webseiten.py
    (optional nach "--": <zone> ...      -> nur diese Zonen
                         --ohne-vorschau -> keine Renders
                         --nur-vorschau  -> nichts bauen, nur rendern)

Voraussetzung: build_room_webseiten_neu.py ist gelaufen (die Vorschau stellt
die exportierten Boden- und Wandmodule auf).

Erzeugt project/assets/world/webseiten/:
    einrichtung_<zone>.glb  EIN Mesh je Zone, Ursprung = Zonenmitte (Godot)
    umgebung.glb            Strassenecke, Nachbarhaeuser, Ursprung 0,0
    fundament.glb           Sockel unter der Grundflaeche (+0,5 m je Seite)
und Vorschaubilder nach art_source/vorschau/webseiten/.

Grundriss wie worlds.json / docs/nacht/karten_welten.md (Stationen, Tueren, Wege):
    werkstatt   x -3..3,  z 0..6    beton   (Start)
    laden       x -10..10, z -3..-1 fliese  bereich_1
    lager       x -10..-4, z -8..-4 beton   bereich_2
    showroom    x -3..3,  z -8..-4  holz    bereich_3
    fotostudio  x 4..10,  z -8..-4  studio  bereich_4
    siebdruck   x -10..-4, z 0..6   beton   bereich_5
    romans_buero x 4..10, z 0..6    holz    offen

Koordinaten in allen Moebel-Funktionen: GODOT lokal, Vorderseite +z,
Ursprung Mitte unten. Platziert wird mit setzen(name, teile, x, z, dreh).
"""

import bpy
import math
import os
import random
import sys
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, profil_x, rundprofil,
    transformieren, alles_loeschen, verbinden, dreiecke, masse, exportieren,
    vorschau_rendern, palette_erweitern, material, WURZEL,
)
import build_einrichtung_wg_a as wa  # noqa: E402
from build_einrichtung_wg_a import (  # noqa: E402
    stab, pflanze, karton, teppich, setzen, moebel_bericht, freiflaechen_pruefen,
)
import build_room_webseiten_neu as raum  # noqa: E402

AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "webseiten")
VORSCHAU = raum.AUSGABE_VORSCHAU
ZONEN_BUDGET = 8000
UMGEBUNG_BUDGET = 14000

palette_erweitern({
    "m3_holz_hell":   ("#E8C99E", 0.75, 0.0, 1.0),
    "m3_holz":        ("#D09F6A", 0.75, 0.0, 1.0),
    "m3_holz_dunkel": ("#8F6240", 0.80, 0.0, 1.0),
    "m3_sperrholz":   ("#EBD2A8", 0.80, 0.0, 1.0),
    "m3_orange":      ("#FF7A1A", 0.60, 0.0, 1.0),
    "m3_orange_hell": ("#FFB27A", 0.80, 0.0, 1.0),
    "m3_schwarz":     ("#2C2B30", 0.50, 0.20, 1.0),
    "m3_anthrazit":   ("#4B4A52", 0.60, 0.0, 1.0),
    "m3_grau":        ("#9B9994", 0.80, 0.0, 1.0),
    "m3_grau_hell":   ("#D9D6D0", 0.80, 0.0, 1.0),
    "m3_weiss":       ("#F8F6F2", 0.70, 0.0, 1.0),
    "m3_stahl":       ("#BAC0C6", 0.35, 0.50, 1.0),
    "m3_blau":        ("#3F6FD1", 0.70, 0.0, 1.0),
    "m3_blau_regal":  ("#3056A8", 0.55, 0.20, 1.0),
    "m3_mint":        ("#7FD4B8", 0.85, 0.0, 1.0),
    "m3_gelb":        ("#FFD04A", 0.80, 0.0, 1.0),
    "m3_pink":        ("#FF8FB6", 0.85, 0.0, 1.0),
    "m3_lila":        ("#9C82E0", 0.85, 0.0, 1.0),
    "m3_rot":         ("#E24E3A", 0.75, 0.0, 1.0),
    "m3_oliv":        ("#7F8C52", 0.85, 0.0, 1.0),
    "m3_creme":       ("#F2E6D2", 0.90, 0.0, 1.0),
    "m3_senf":        ("#E0A63A", 0.90, 0.0, 1.0),
    "m3_puppe":       ("#EDE4D8", 0.50, 0.0, 1.0),
    "m3_gummi":       ("#3A3A3E", 0.95, 0.0, 1.0),
    "m3_acryl":       ("#3B3642", 0.30, 0.0, 1.0),
    "m3_glas":        ("#BFE3F2", 0.15, 0.0, 1.0),
    "m3_spiegel":     ("#D4EAF2", 0.08, 0.30, 1.0),
    "m3_bildschirm":  ("#262B36", 0.35, 0.0, 1.0),
    "m3_sieb":        ("#F4D35E", 0.85, 0.0, 1.0),
    "m3_neon_orange": ("#FFAA55", 0.40, 0.0, 1.0),
    "m3_neon_pink":   ("#FF6FB5", 0.40, 0.0, 1.0),
    "m3_licht":       ("#FFF4DE", 0.50, 0.0, 1.0),
    "m3_bildschirm_an": ("#9CC8F2", 0.40, 0.0, 1.0),
    # Aussen
    "m3_gehweg":      ("#D3CCC2", 0.90, 0.0, 1.0),
    "m3_gehweg_fuge": ("#B9B1A6", 0.95, 0.0, 1.0),
    "m3_bordstein":   ("#C4C1BC", 0.85, 0.0, 1.0),
    "m3_asphalt":     ("#61646B", 0.95, 0.0, 1.0),
    "m3_markierung":  ("#F4F1EA", 0.80, 0.0, 1.0),
    "m3_sockel":      ("#CFC8BE", 0.90, 0.0, 1.0),
    "m3_hof":         ("#C9C2B5", 0.95, 0.0, 1.0),
    "m3_haus_sand":   ("#EBD7B8", 0.90, 0.0, 1.0),
    "m3_haus_salbei": ("#BCCFB2", 0.90, 0.0, 1.0),
    "m3_haus_terra":  ("#E7A98C", 0.90, 0.0, 1.0),
    "m3_haus_blau":   ("#B7CDE3", 0.90, 0.0, 1.0),
    "m3_haus_gelb":   ("#F1DC9C", 0.90, 0.0, 1.0),
    "m3_haus_grau":   ("#C9CCD3", 0.90, 0.0, 1.0),
    "m3_dach":        ("#8C8580", 0.90, 0.0, 1.0),
    "m3_fenster":     ("#5E7A94", 0.30, 0.0, 1.0),
    "m3_rahmen":      ("#F7F3EC", 0.70, 0.0, 1.0),
    "m3_rasen":       ("#8DC262", 0.90, 0.0, 1.0),
    "m3_busch":       ("#5DA84A", 0.85, 0.0, 1.0),
    "m3_busch_dunkel": ("#468F3E", 0.85, 0.0, 1.0),
    "m3_busch_hell":  ("#7DBE55", 0.85, 0.0, 1.0),
    "m3_stamm":       ("#8A6446", 0.90, 0.0, 1.0),
    "m3_erde":        ("#6B4A33", 0.95, 0.0, 1.0),
    # M2: Lieferwagen, Hof
    "m3_lack_van":    ("#F2F2F0", 0.45, 0.0, 1.0),
    "m3_lack_van_2":  ("#DADCDD", 0.55, 0.0, 1.0),
    "m3_hof_asphalt": ("#7B7F86", 0.95, 0.0, 1.0),
    "m3_hof_flick":   ("#6D7178", 0.95, 0.0, 1.0),
    "m3_hof_gelb":    ("#F2C230", 0.80, 0.0, 1.0),
    "m3_ladung_dunkel": ("#2E2C33", 0.95, 0.0, 1.0),
})

# Leuchtende Stoffe: Emission wird nach dem Anlegen gesetzt (glTF emissive).
LEUCHTEND = {"m3_neon_orange": 2.5, "m3_neon_pink": 2.5, "m3_licht": 1.2, "m3_bildschirm_an": 0.8}


def leucht_materialien():
    for name, staerke in LEUCHTEND.items():
        mat = material(name)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Emission Color"].default_value = mat.diffuse_color
        bsdf.inputs["Emission Strength"].default_value = staerke


def bei(teile, x=0.0, y=0.0, z=0.0, dreh=0.0):
    """Verschiebt/dreht eine lokal gebaute Gruppe (Godot) und gibt sie zurueck."""
    teile = [t for t in teile if t is not None]
    transformieren(teile, x=x, z=z, y=y, dreh_grad=dreh)
    return teile


def box(name, s, m, mat, r=0.0, seg=1):
    return kasten(name, s, m, mat, rund=r, segmente=seg)


# ==============================================================================
# MOEBEL
# ==============================================================================
SHIRT_FARBEN = ["m3_weiss", "m3_orange", "m3_schwarz", "m3_mint", "m3_blau", "m3_gelb", "m3_grau_hell",
                "m3_pink", "m3_oliv", "m3_lila"]


def kleiderstange(breite=1.2, n=7, hoehe=1.45, seed=1, lang=False):
    """Rollstaender aus schwarzem Rohr, Bügel aus Holz, Shirts/Hoodies quer
    zur Stange (so sieht man ihre Farbe von vorn und von der Seite)."""
    rng = random.Random(seed)
    m = "m3_schwarz"
    teile = []
    for s in (-1, 1):
        x = s * breite / 2
        teile.append(zylinder("pfosten", 0.02, hoehe, (x, 0.04, 0), m, seiten=6))
        teile.append(box("fuss", (0.05, 0.03, 0.5), (x, 0.055, 0), m))
        for dz in (-0.22, 0.22):
            teile.append(box("rolle", (0.03, 0.04, 0.04), (x, 0.02, dz), "m3_gummi"))
    teile.append(liegender_zylinder("stange", 0.017, breite + 0.05, (0, hoehe + 0.04, 0), "x", "m3_stahl", seiten=6))
    teile.append(box("quer", (breite, 0.03, 0.03), (0, 0.2, 0), m))
    farben = SHIRT_FARBEN[:]
    rng.shuffle(farben)
    y0 = hoehe + 0.02
    for i in range(n):
        x = -breite / 2 + 0.12 + i * (breite - 0.24) / max(1, n - 1)
        f = farben[i % len(farben)]
        laenge = 0.62 if (lang or i % 3 == 0) else 0.5
        teile.append(box("buegel", (0.012, 0.03, 0.38), (x, y0 - 0.04, 0), "m3_holz"))
        teile.append(box("schulter", (0.05, 0.16, 0.5), (x, y0 - 0.14, 0), f))
        teile.append(box("koerper", (0.045, laenge, 0.4), (x, y0 - 0.2 - laenge / 2, 0), f))
    return teile


def regal_shirts(b=1.6, h=1.8, t=0.42, seed=2, oben="kartons"):
    """Wandregal aus hellem Holz mit gefalteten Shirts in Stapeln."""
    rng = random.Random(seed)
    teile = [
        box("seite_l", (0.035, h, t), (-b / 2 + 0.0175, h / 2, 0), "m3_holz_hell"),
        box("seite_r", (0.035, h, t), (b / 2 - 0.0175, h / 2, 0), "m3_holz_hell"),
        box("rueck", (b - 0.07, h - 0.1, 0.015), (0, h / 2 + 0.05, -t / 2 + 0.01), "m3_weiss"),
        box("sockel", (b - 0.07, 0.08, t - 0.04), (0, 0.04, 0), "m3_holz"),
    ]
    boeden = [0.08, 0.5, 0.92, 1.34, h - 0.02]
    for y in boeden:
        teile.append(box("brett", (b - 0.07, 0.03, t), (0, y + 0.015, 0), "m3_holz_hell"))
    for k, y in enumerate(boeden[:-1]):
        spalten = 3 if b > 1.2 else 2
        breite = (b - 0.15) / spalten
        for s in range(spalten):
            x = -b / 2 + 0.075 + breite * (s + 0.5)
            f = rng.choice(SHIRT_FARBEN)
            n = rng.randint(2, 4)
            teile.append(box("stapel", (breite - 0.08, 0.05 * n, 0.3), (x, y + 0.03 + 0.025 * n, 0.02), f))
            teile.append(box("oben", (breite - 0.1, 0.045, 0.28), (x + 0.01, y + 0.03 + 0.05 * n + 0.0225, 0.02),
                             rng.choice(SHIRT_FARBEN)))
    if oben == "kartons":
        teile += bei(karton(0.4, 0.22, 0.3), x=-b / 4, y=h)
        teile += bei(karton(0.3, 0.16, 0.26, "m3_orange", klebe=False), x=b / 4 - 0.05, y=h)
    else:
        teile += bei(pflanze(0.55, "topf_creme", "hoch"), x=b / 4, y=h)
    return teile


def spiegel_stand(b=0.6, h=1.75):
    teile = [
        box("rahmen", (b, h, 0.04), (0, h / 2 + 0.04, 0), "m3_holz", r=0.015),
        box("glas", (b - 0.1, h - 0.1, 0.012), (0, h / 2 + 0.04, 0.022), "m3_spiegel"),
    ]
    for s in (-1, 1):
        teile.append(box("fuss", (0.05, 0.04, 0.42), (s * (b / 2 - 0.06), 0.02, -0.06), "m3_holz_dunkel"))
    return teile


def puppe(oben="m3_orange", unten="m3_schwarz", kapuze=True):
    """Schaufensterpuppe ohne Gesicht auf Stange und Scheibe."""
    teile = [
        zylinder("scheibe", 0.2, 0.03, (0, 0, 0), "m3_schwarz", seiten=12),
        zylinder("stange", 0.015, 0.78, (0, 0.03, 0), "m3_stahl", seiten=6),
        box("huefte", (0.34, 0.22, 0.2), (0, 0.9, 0), unten, r=0.05),
        box("rumpf", (0.38, 0.46, 0.23), (0, 1.22, 0), oben, r=0.07),
        box("schultern", (0.5, 0.14, 0.24), (0, 1.42, 0), oben, r=0.06),
        zylinder("hals", 0.045, 0.1, (0, 1.47, 0), "m3_puppe", seiten=8),
        kugel("kopf", 0.11, (0, 1.67, 0), "m3_puppe", stauchung=1.18, ringe=6, seiten=10),
    ]
    for s in (-1, 1):
        teile.append(box("arm", (0.09, 0.46, 0.11), (s * 0.28, 1.17, 0), oben, r=0.035))
        teile.append(box("hand", (0.06, 0.08, 0.08), (s * 0.28, 0.9, 0), "m3_puppe", r=0.02))
    if kapuze:
        teile.append(box("kapuze", (0.3, 0.14, 0.13), (0, 1.5, -0.13), oben, r=0.05))
        teile.append(box("tasche", (0.24, 0.1, 0.02), (0, 1.1, 0.12), oben))
    else:
        teile.append(box("druck", (0.18, 0.16, 0.01), (0, 1.26, 0.12), "m3_orange_hell"))
    return teile


def neon_form(breite=1.5, hoehe=0.55, mat="m3_neon_orange", seed=3):
    """Neon-Schwung auf dunkler Acrylplatte: geschwungene Linie mit zwei
    Schlaufen und Unterstrich -- liest sich wie ein Schriftzug, ist aber keiner.
    Rueckseite bei lokal z = 0 (Wandflaeche)."""
    teile = [box("platte", (breite + 0.16, hoehe + 0.16, 0.025), (0, 0, 0.0125), "m3_acryl", r=0.01)]
    d = 0.032
    z = 0.05
    punkte = []
    n = 22
    for i in range(n + 1):
        t = i / n
        x = -breite / 2 + 0.08 + t * (breite - 0.16)
        y = 0.05 + math.sin(t * math.pi * 3.0) * hoehe * 0.22 + (0.08 if 0.3 < t < 0.45 else 0.0)
        punkte.append((x, y))
    for (x0, y0), (x1, y1) in zip(punkte, punkte[1:]):
        teile.append(stab("neon", (x0, y0, z), (x1, y1, z), d, mat))
    for cx, cy, r in ((-breite * 0.28, 0.08, 0.1), (breite * 0.12, 0.02, 0.08)):
        k = 8
        for i in range(k):
            a0 = 2 * math.pi * i / k
            a1 = 2 * math.pi * (i + 1) / k
            teile.append(stab("schlaufe", (cx + math.cos(a0) * r, cy + math.sin(a0) * r, z),
                              (cx + math.cos(a1) * r, cy + math.sin(a1) * r, z), d, mat))
    teile.append(stab("strich", (-breite * 0.3, -hoehe * 0.33, z), (breite * 0.36, -hoehe * 0.3, z), d, mat))
    teile.append(kugel("punkt", 0.04, (breite * 0.42, -hoehe * 0.3, z), mat, ringe=4, seiten=6))
    return teile


def spot_stativ(h=1.8):
    """Scheinwerfer auf Dreibein, Linse blickt nach +z."""
    teile = []
    for i in range(3):
        a = math.radians(90 + i * 120)
        teile.append(stab("bein", (0, 0.75, 0), (math.cos(a) * 0.32, 0.0, math.sin(a) * 0.32), 0.022, "m3_schwarz"))
    teile.append(zylinder("saeule", 0.016, h - 0.75, (0, 0.75, 0), "m3_schwarz", seiten=6))
    teile.append(box("buegel", (0.26, 0.03, 0.03), (0, h - 0.02, 0), "m3_schwarz"))
    teile.append(liegender_zylinder("kopf", 0.095, 0.26, (0, h + 0.08, 0.02), "z", "m3_schwarz", seiten=10))
    teile.append(liegender_zylinder("linse", 0.075, 0.02, (0, h + 0.08, 0.155), "z", "m3_licht", seiten=10))
    for s in (-1, 1):
        teile.append(box("klappe", (0.012, 0.16, 0.08), (s * 0.1, h + 0.08, 0.19), "m3_schwarz"))
    return teile


def buehne(b=6.8, t=1.2, h=0.18):
    """Holzbuehne: Podest mit Dielenfugen und schwarzer Stirnkante, vorn
    eine orangefarbene Lichtleiste."""
    teile = [box("podest", (b, h - 0.03, t), (0, (h - 0.03) / 2, 0), "m3_schwarz", r=0.01)]
    n = int(t / 0.2)
    for i in range(n):
        z = -t / 2 + 0.1 + i * 0.2
        teile.append(box("diele", (b - 0.02, 0.03, 0.19), (0, h - 0.015, z), "m3_holz_hell" if i % 2 else "m3_holz"))
    teile.append(box("leiste", (b - 0.1, 0.02, 0.02), (0, h - 0.06, t / 2 + 0.005), "m3_neon_orange"))
    return teile


def theke_ende(b=2.2, t=0.6, h=1.0):
    """Ladentheke: weisse Front mit orangem Band, Eichenplatte, darauf
    Versandtaschen, Klebebandabroller und ein kleiner Kaktus."""
    teile = [
        box("korpus", (b, h - 0.05, t - 0.04), (0, (h - 0.05) / 2, 0), "m3_weiss", r=0.02),
        box("band", (b + 0.004, 0.12, t - 0.03), (0, 0.55, 0), "m3_holz_dunkel"),
        box("sockel", (b - 0.06, 0.08, t - 0.1), (0, 0.04, 0), "m3_anthrazit"),
        box("platte", (b + 0.06, 0.05, t + 0.04), (0, h - 0.025, 0), "m3_holz_hell", r=0.012),
    ]
    teile += bei([box("taschen", (0.34, 0.06, 0.26), (0, 0.03, 0), "m3_grau_hell"),
                  box("taschen2", (0.32, 0.03, 0.24), (0.01, 0.075, 0), "m3_orange_hell")], x=-0.7, y=h, dreh=8)
    teile += [
        box("abroller", (0.22, 0.1, 0.1), (0.1, h + 0.05, 0.05), "m3_rot", r=0.02),
        liegender_zylinder("rolle", 0.05, 0.05, (0.1, h + 0.12, 0.05), "x", "m3_senf", seiten=8),
        box("terminal", (0.1, 0.03, 0.16), (0.45, h + 0.015, 0.1), "m3_schwarz", r=0.01),
    ]
    teile += bei(karton(0.3, 0.2, 0.24), x=0.85, y=h, dreh=-6)
    teile += bei(pflanze(0.35, "topf_creme", "mini"), x=-0.2, y=h, z=-0.12)
    return teile


def muetzen_staender(h=1.3):
    """Drehstaender mit Caps: Saeule, drei Ebenen, je vier Caps."""
    teile = [zylinder("fuss", 0.22, 0.03, (0, 0, 0), "m3_schwarz", seiten=10),
             zylinder("saeule", 0.02, h, (0, 0.03, 0), "m3_stahl", seiten=6)]
    farben = ["m3_orange", "m3_schwarz", "m3_mint", "m3_weiss", "m3_blau", "m3_gelb"]
    k = 0
    for y in (0.55, 0.85, 1.15):
        for i in range(4):
            a = math.radians(i * 90 + y * 60)
            x, z = math.cos(a) * 0.14, math.sin(a) * 0.14
            teile.append(kugel("cap", 0.08, (x, y, z), farben[k % 6], stauchung=0.7, ringe=4, seiten=7))
            k += 1
    return teile


def bank(b=1.2, t=0.4, h=0.45, polster="m3_orange"):
    teile = [box("sitz", (b, 0.05, t), (0, h - 0.025, 0), "m3_holz_hell", r=0.012),
             box("polster", (b - 0.1, 0.06, t - 0.06), (0, h + 0.03, 0), polster, r=0.02)]
    for s in (-1, 1):
        teile.append(box("bein", (0.05, h - 0.05, t - 0.06), (s * (b / 2 - 0.08), (h - 0.05) / 2, 0), "m3_schwarz"))
    return teile


def sneaker(farbe="m3_weiss", sohle="m3_weiss", akzent="m3_orange"):
    """Ein Schuh, Spitze nach +z."""
    return [
        box("sohle", (0.1, 0.03, 0.28), (0, 0.015, 0), sohle, r=0.01),
        box("schaft", (0.09, 0.07, 0.2), (0, 0.065, -0.03), farbe, r=0.02),
        box("spitze", (0.09, 0.04, 0.1), (0, 0.05, 0.08), farbe, r=0.015),
        box("streifen", (0.092, 0.02, 0.1), (0, 0.06, -0.03), akzent),
    ]


def sneaker_einfach(farbe, akzent):
    return [box("sohle", (0.1, 0.035, 0.28), (0, 0.0175, 0), akzent),
            box("schaft", (0.09, 0.08, 0.22), (0, 0.075, -0.02), farbe)]


def sneaker_paar(farbe="m3_weiss", akzent="m3_orange", sohle="m3_weiss", einfach=False):
    if einfach:
        return bei(sneaker_einfach(farbe, akzent), x=-0.06) + bei(sneaker_einfach(farbe, akzent), x=0.06, z=0.02)
    return (bei(sneaker(farbe, sohle, akzent), x=-0.06) + bei(sneaker(farbe, sohle, akzent), x=0.06, z=0.02))


def wuerfel_podest(s=0.5, h=0.6, mat="m3_weiss"):
    teile = [box("wuerfel", (s, h, s), (0, h / 2, 0), mat, r=0.015)]
    teile += bei(sneaker_paar("m3_schwarz", "m3_orange"), y=h, dreh=-20)
    return teile


def schwerlastregal(b=1.7, h=2.0, t=0.6, seed=4, ebenen=(0.12, 0.8, 1.45)):
    """Palettenregal: blaue Stuetzen, orange Traversen, Holzboeden, Kartons."""
    rng = random.Random(seed)
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("stuetze", (0.06, h, 0.05), (sx * (b / 2 - 0.03), h / 2, sz * (t / 2 - 0.025)),
                             "m3_blau_regal"))
    for y in ebenen:
        for sz in (-1, 1):
            teile.append(box("traverse", (b - 0.06, 0.08, 0.04), (0, y + 0.04, sz * (t / 2 - 0.02)), "m3_stahl"))
        teile.append(box("boden", (b - 0.08, 0.025, t - 0.02), (0, y + 0.09, 0), "m3_sperrholz"))
        x = -b / 2 + 0.08
        stueck = 0
        while x < b / 2 - 0.3 and stueck < 3:
            stueck += 1
            w = rng.uniform(0.35, 0.55)
            if x + w > b / 2 - 0.06:
                break
            hh = rng.uniform(0.25, min(0.5, (0.55 if y < 1.4 else 0.45)))
            teile += bei(karton(w - 0.04, hh, t - 0.14, rng.choice(["karton", "karton", "karton_hell"]),
                                klebe=False), x=x + w / 2, y=y + 0.1, dreh=rng.uniform(-4, 4))
            x += w
    return teile


def palette_kartons(seed=5, lagen=2):
    rng = random.Random(seed)
    teile = []
    for i in range(3):
        teile.append(box("kufe", (1.2, 0.1, 0.1), (0, 0.05, -0.35 + i * 0.35), "m3_holz"))
    for i in range(5):
        teile.append(box("brett", (0.14, 0.025, 0.8), (-0.5 + i * 0.25, 0.1125, 0), "m3_sperrholz"))
    y = 0.125
    for lage in range(lagen):
        for ix in (-0.3, 0.3):
            for iz in (-0.2, 0.2):
                if lage == lagen - 1 and rng.random() < 0.3:
                    continue
                teile += bei(karton(0.56, 0.36, 0.38, klebe=True), x=ix, y=y, z=iz, dreh=rng.uniform(-3, 3))
        y += 0.36
    return teile


def rollwagen(b=0.9, t=0.55, seed=6, ladung="kartons"):
    rng = random.Random(seed)
    teile = [box("plattform", (b, 0.04, t), (0, 0.14, 0), "m3_anthrazit", r=0.01)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(zylinder("rad", 0.05, 0.03, (sx * (b / 2 - 0.08), 0.02, sz * (t / 2 - 0.08)), "m3_gummi", seiten=8))
            teile.append(box("gabel", (0.03, 0.08, 0.03), (sx * (b / 2 - 0.08), 0.09, sz * (t / 2 - 0.08)), "m3_stahl"))
    for sz in (-1, 1):
        teile.append(box("buegel_holm", (0.03, 0.8, 0.03), (-b / 2 + 0.02, 0.56, sz * (t / 2 - 0.04)), "m3_stahl"))
    teile.append(box("buegel_oben", (0.03, 0.03, t - 0.05), (-b / 2 + 0.02, 0.96, 0), "m3_stahl"))
    if ladung == "kartons":
        teile += bei(karton(0.42, 0.3, 0.36), x=-0.15, y=0.16, dreh=4)
        teile += bei(karton(0.36, 0.24, 0.3, "karton_hell"), x=0.22, y=0.16, dreh=-5)
        teile += bei(karton(0.3, 0.2, 0.26), x=-0.1, y=0.46, dreh=12)
    else:
        for i in range(4):
            teile.append(box("shirts", (0.34, 0.06, 0.28), (-0.2 + (i % 2) * 0.4, 0.19 + (i // 2) * 0.06, 0),
                             rng.choice(SHIRT_FARBEN)))
        teile.append(box("shirts", (0.36, 0.1, 0.3), (0.2, 0.3, 0), "m3_orange"))
    return teile


def sackkarre():
    teile = [box("schaufel", (0.36, 0.02, 0.2), (0, 0.01, 0.1), "m3_stahl")]
    for s in (-1, 1):
        teile.append(stab("holm", (s * 0.15, 0.02, 0.0), (s * 0.15, 1.15, -0.25), 0.03, "m3_stahl"))
        teile.append(liegender_zylinder("rad", 0.1, 0.05, (s * 0.21, 0.1, -0.06), "x", "m3_gummi", seiten=10))
    teile.append(stab("griff", (-0.15, 1.15, -0.25), (0.15, 1.15, -0.25), 0.03, "m3_schwarz"))
    teile += bei(karton(0.32, 0.3, 0.26), y=0.02, z=0.06)
    return teile


def gitterbox(b=0.9, h=0.8, t=0.7):
    teile = [box("boden", (b, 0.1, t), (0, 0.05, 0), "m3_anthrazit")]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("ecke", (0.04, h, 0.04), (sx * (b / 2 - 0.02), h / 2, sz * (t / 2 - 0.02)), "m3_stahl"))
    for y in (0.35, 0.6, h - 0.02):
        for sz in (-1, 1):
            teile.append(box("stab_x", (b, 0.015, 0.015), (0, y, sz * (t / 2 - 0.02)), "m3_stahl"))
        for sx in (-1, 1):
            teile.append(box("stab_z", (0.015, 0.015, t), (sx * (b / 2 - 0.02), y, 0), "m3_stahl"))
    for i in range(3):
        for sz in (-1, 1):
            teile.append(box("senkrecht", (0.012, h - 0.1, 0.012), (-b / 4 + i * b / 4, h / 2 + 0.05, sz * (t / 2 - 0.02)),
                             "m3_stahl"))
    for i, (x, z) in enumerate(((-0.2, -0.1), (0.2, 0.12), (0.1, -0.15))):
        teile.append(box("paket", (0.3, 0.2 + 0.05 * i, 0.26), (x, 0.2 + 0.05 * i, z),
                         ["m3_grau_hell", "karton", "m3_orange_hell"][i], r=0.02))
    return teile


def stehleiter(h=1.3):
    teile = []
    for s in (-1, 1):
        teile.append(stab("holm_v", (s * 0.22, 0.0, 0.3), (s * 0.18, h, 0.0), 0.04, "m3_stahl"))
        teile.append(stab("holm_h", (s * 0.22, 0.0, -0.3), (s * 0.18, h, 0.0), 0.04, "m3_stahl"))
    for i in range(4):
        y = 0.28 + i * 0.28
        z = 0.3 - 0.3 * y / h
        teile.append(box("stufe", (0.38 - 0.02 * i, 0.03, 0.11), (0, y, z), "m3_stahl"))
    teile.append(box("kopf", (0.42, 0.05, 0.16), (0, h, 0), "m3_stahl"))
    return teile


def stretchfolie():
    return [zylinder("fuss", 0.16, 0.03, (0, 0, 0), "m3_schwarz", seiten=8),
            zylinder("stiel", 0.02, 0.7, (0, 0.03, 0), "m3_stahl", seiten=6),
            zylinder("rolle", 0.07, 0.4, (0, 0.73, 0), "m3_glas", seiten=10),
            zylinder("kern", 0.03, 0.44, (0, 0.71, 0), "karton", seiten=6)]


# --- Fotostudio -------------------------------------------------------------------

def hintergrund_rolle(b=3.0, h=2.35, vor=1.5):
    """Weisse Papierbahn von der Rolle: haengt an der Wand herab und laeuft in
    einer Hohlkehle auf den Boden aus. Rueckseite bei lokal z = 0."""
    teile = []
    for s in (-1, 1):
        x = s * (b / 2 + 0.1)
        teile.append(zylinder("stativ", 0.02, h, (x, 0, 0.16), "m3_schwarz", seiten=6))
        teile.append(box("fuss", (0.05, 0.03, 0.3), (x, 0.015, 0.16), "m3_schwarz"))
    teile.append(liegender_zylinder("stange", 0.018, b + 0.3, (0, h, 0.16), "x", "m3_schwarz", seiten=6))
    teile.append(liegender_zylinder("rolle", 0.07, b, (0, h, 0.16), "x", "m3_weiss", seiten=10))
    r = 0.45
    z_bahn = 0.24
    pkt = []
    pkt.append((z_bahn, h - 0.05))
    for k in range(7):
        a = math.radians(180 + 90 * k / 6)
        pkt.append((z_bahn + r + r * math.cos(a), r + r * math.sin(a)))
    pkt.append((z_bahn + r + vor, 0.0))
    dicke = 0.012
    profil = [(z, y + dicke) for (z, y) in pkt] + [(z + dicke, y) for (z, y) in reversed(pkt)]
    profil = [(z, max(0.002, y)) for (z, y) in profil]
    teile.append(profil_x("bahn", profil, -b / 2, b / 2, "m3_weiss"))
    return teile


def softbox(h=1.6):
    teile = []
    for i in range(3):
        a = math.radians(90 + i * 120)
        teile.append(stab("bein", (0, 0.7, 0), (math.cos(a) * 0.35, 0.0, math.sin(a) * 0.35), 0.022, "m3_schwarz"))
    teile.append(zylinder("saeule", 0.016, h - 0.7, (0, 0.7, 0), "m3_schwarz", seiten=6))
    kopf = [
        box("kasten", (0.62, 0.62, 0.26), (0, 0, -0.05), "m3_schwarz", r=0.02),
        box("front", (0.56, 0.56, 0.02), (0, 0, 0.09), "m3_licht"),
        box("rand", (0.66, 0.66, 0.03), (0, 0, 0.07), "m3_schwarz"),
    ]
    return teile + bei(kopf, y=h + 0.2)


def reflektor(h=1.1):
    teile = [zylinder("fuss", 0.2, 0.03, (0, 0, 0), "m3_schwarz", seiten=8),
             zylinder("stiel", 0.015, h, (0, 0.03, 0), "m3_schwarz", seiten=6),
             liegender_zylinder("scheibe", 0.4, 0.015, (0, h + 0.4, 0), "z", "m3_senf", seiten=14),
             liegender_zylinder("ring", 0.42, 0.01, (0, h + 0.4, -0.012), "z", "m3_schwarz", seiten=14)]
    return teile


def produkttisch():
    teile = [box("platte", (1.1, 0.04, 0.65), (0, 0.73, 0), "m3_weiss", r=0.012)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("bein", (0.04, 0.71, 0.04), (sx * 0.5, 0.355, sz * 0.27), "m3_weiss"))
    teile += [
        box("hoodie", (0.42, 0.08, 0.36), (-0.22, 0.79, 0.02), "m3_orange", r=0.03),
        box("kordel", (0.12, 0.01, 0.08), (-0.22, 0.835, 0.12), "m3_weiss"),
        box("stapel", (0.3, 0.06, 0.26), (0.28, 0.78, -0.12), "m3_mint", r=0.015),
    ]
    teile += bei(sneaker_paar("m3_weiss", "m3_orange"), x=0.25, y=0.75, z=0.12, dreh=-30)
    return teile


def kamera_stativ(h=1.35):
    teile = []
    for i in range(3):
        a = math.radians(90 + i * 120)
        teile.append(stab("bein", (0, h - 0.1, 0), (math.cos(a) * 0.38, 0.0, math.sin(a) * 0.38), 0.025, "m3_schwarz"))
    teile += [
        box("kopf", (0.08, 0.06, 0.08), (0, h - 0.05, 0), "m3_schwarz"),
        box("gehaeuse", (0.16, 0.11, 0.08), (0, h + 0.05, 0), "m3_schwarz", r=0.015),
        liegender_zylinder("objektiv", 0.04, 0.12, (0, h + 0.05, 0.1), "z", "m3_anthrazit", seiten=8),
        box("blitz", (0.06, 0.04, 0.06), (0, h + 0.12, -0.01), "m3_orange"),
    ]
    return teile


def stehtisch_laptop():
    teile = [box("platte", (0.8, 0.04, 0.5), (0, 1.0, 0), "m3_holz_hell", r=0.012),
             zylinder("saeule", 0.035, 0.98, (0, 0.0, 0), "m3_schwarz", seiten=8),
             box("fuss", (0.5, 0.03, 0.4), (0, 0.015, 0), "m3_schwarz"),
             box("laptop", (0.34, 0.02, 0.24), (-0.12, 1.03, 0.06), "m3_stahl"),
             box("deckel", (0.34, 0.22, 0.015), (-0.12, 1.14, -0.06), "m3_stahl"),
             box("anzeige", (0.3, 0.18, 0.004), (-0.12, 1.14, -0.05), "m3_bildschirm_an"),
             box("kabel", (0.02, 0.02, 0.3), (0.2, 1.03, 0.0), "m3_orange")]
    return teile


def rollen_regal():
    """Wandhalter mit farbigen Hintergrundrollen (Karton-Kerne)."""
    teile = [box("wange_l", (0.04, 1.6, 0.35), (-0.55, 0.8, 0), "m3_schwarz"),
             box("wange_r", (0.04, 1.6, 0.35), (0.55, 0.8, 0), "m3_schwarz")]
    for i, (y, m) in enumerate(((0.35, "m3_orange"), (0.75, "m3_mint"), (1.15, "m3_grau"), (1.52, "m3_pink"))):
        teile.append(liegender_zylinder("rolle", 0.08, 1.06, (0, y, 0.02 * (i % 2)), "x", m, seiten=10))
    return teile


# --- Siebdruck ----------------------------------------------------------------------

def karussell(arme=6):
    """Siebdruckkarussell: Mittelsaeule, Druckpaletten unten, Siebarme oben."""
    teile = [
        zylinder("fuss", 0.3, 0.06, (0, 0, 0), "m3_anthrazit", seiten=8),
        zylinder("saeule", 0.08, 1.15, (0, 0.06, 0), "m3_anthrazit", seiten=8),
        zylinder("kopf", 0.2, 0.12, (0, 1.12, 0), "m3_orange", seiten=8),
    ]
    for i in range(3):
        a = i * 120 + 30
        teile += bei([box("fussarm", (0.08, 0.05, 0.8), (0, 0.025, 0.4), "m3_anthrazit")], dreh=a)
    farben = ["m3_weiss", "m3_orange", "m3_schwarz", "m3_mint", "m3_weiss", "m3_blau"]
    for i in range(arme):
        a = i * 360.0 / arme
        arm = [
            box("arm_u", (0.06, 0.05, 0.62), (0, 0.8, 0.38), "m3_stahl"),
            box("palette", (0.36, 0.03, 0.5), (0, 0.84, 0.82), "m3_holz_dunkel"),
            box("shirt", (0.34, 0.012, 0.46), (0, 0.861, 0.82), farben[i]),
            box("arm_o", (0.05, 0.05, 0.6), (0, 1.16, 0.4), "m3_anthrazit"),
            box("sieb", (0.42, 0.03, 0.56), (0, 1.06, 0.84), "m3_holz"),
            box("gewebe", (0.34, 0.012, 0.46), (0, 1.08, 0.84), "m3_sieb"),
        ]
        if i % 2 == 0:
            arm.append(box("rakel", (0.3, 0.06, 0.02), (0, 1.12, 0.84), "m3_schwarz"))
        teile += bei(arm, dreh=a)
    return teile


def farbeimer(mat="m3_orange", h=0.28, r=0.13):
    return [zylinder("eimer", r * 0.9, h, (0, 0, 0), "m3_weiss", seiten=10, radius_oben=r),
            zylinder("deckel", r + 0.01, 0.02, (0, h, 0), mat, seiten=10),
            box("etikett", (r * 1.2, h * 0.4, 0.01), (0, h * 0.45, r * 0.93), mat)]


def eimergruppe(seed=7):
    rng = random.Random(seed)
    teile = []
    farben = ["m3_orange", "m3_blau", "m3_pink", "m3_gelb", "m3_mint", "m3_schwarz"]
    pos = [(-0.2, -0.15), (0.12, -0.18), (-0.05, 0.14), (0.28, 0.12), (-0.33, 0.2)]
    for i, (x, z) in enumerate(pos):
        teile += bei(farbeimer(farben[i], rng.uniform(0.22, 0.32), rng.uniform(0.11, 0.14)), x=x, z=z)
    teile += bei(farbeimer("m3_lila", 0.18, 0.09), x=0.12, y=0.3, z=-0.18)
    return teile


def trockenregal(b=1.3, h=1.7, t=0.7, seed=8):
    rng = random.Random(seed)
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("stange", (0.035, h, 0.035), (sx * (b / 2 - 0.02), h / 2, sz * (t / 2 - 0.02)), "m3_schwarz"))
        teile.append(zylinder("rad", 0.04, 0.03, (sx * (b / 2 - 0.02), 0.0, 0.0), "m3_gummi", seiten=6))
    teile.append(box("deckel", (b, 0.03, t), (0, h, 0), "m3_schwarz"))
    for i in range(9):
        y = 0.25 + i * 0.16
        teile.append(box("fach", (b - 0.06, 0.012, t - 0.06), (0, y, 0), "m3_grau"))
        if rng.random() < 0.7:
            teile.append(box("shirt", (0.42, 0.01, 0.46), (rng.uniform(-0.3, 0.3), y + 0.011, 0.0),
                             rng.choice(SHIRT_FARBEN)))
    return teile


def auswaschkabine(b=1.0, t=0.7):
    teile = [
        box("wanne", (b, 0.35, t), (0, 0.72, 0), "m3_grau", r=0.02),
        box("rueck", (b, 0.9, 0.05), (0, 1.35, -t / 2 + 0.025), "m3_grau_hell"),
        box("dach", (b, 0.05, 0.3), (0, 1.8, -t / 2 + 0.15), "m3_grau"),
        box("licht", (b - 0.1, 0.02, 0.2), (0, 1.77, -t / 2 + 0.15), "m3_licht"),
        box("sieb", (0.6, 0.5, 0.03), (0, 1.15, -t / 2 + 0.1), "m3_holz"),
        box("gewebe", (0.52, 0.42, 0.01), (0, 1.15, -t / 2 + 0.12), "m3_sieb"),
        liegender_zylinder("schlauch", 0.02, 0.4, (0.35, 1.0, -0.1), "z", "m3_blau", seiten=6),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("bein", (0.05, 0.55, 0.05), (sx * (b / 2 - 0.05), 0.275, sz * (t / 2 - 0.05)), "m3_stahl"))
    return teile


def blitztrockner():
    teile = [zylinder("fuss", 0.22, 0.04, (0, 0, 0), "m3_schwarz", seiten=8),
             zylinder("stiel", 0.025, 0.95, (0, 0.04, 0), "m3_stahl", seiten=6),
             box("arm", (0.05, 0.05, 0.4), (0, 1.0, 0.15), "m3_stahl"),
             box("heizung", (0.45, 0.1, 0.45), (0, 1.02, 0.45), "m3_anthrazit", r=0.015),
             box("gluehen", (0.38, 0.01, 0.38), (0, 0.965, 0.45), "m3_neon_orange")]
    return teile


def siebe_angelehnt(n=4, seed=9):
    rng = random.Random(seed)
    teile = []
    for i in range(n):
        w, hh = rng.uniform(0.45, 0.6), rng.uniform(0.55, 0.75)
        z = 0.03 * i
        teile.append(box("rahmen", (w, hh, 0.03), (0.04 * i, hh / 2, z), "m3_holz", r=0.006))
        teile.append(box("gewebe", (w - 0.08, hh - 0.08, 0.01), (0.04 * i, hh / 2, z + 0.016),
                         "m3_sieb" if i % 2 == 0 else "m3_orange_hell"))
    return teile


def arbeitstisch(b=1.6, t=0.7, seed=10, deko="shirts"):
    rng = random.Random(seed)
    teile = [box("platte", (b, 0.05, t), (0, 0.88, 0), "m3_sperrholz", r=0.01),
             box("boden", (b - 0.1, 0.03, t - 0.1), (0, 0.18, 0), "m3_sperrholz")]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("bein", (0.05, 0.86, 0.05), (sx * (b / 2 - 0.05), 0.43, sz * (t / 2 - 0.05)), "m3_schwarz"))
    if deko == "shirts":
        for i in range(4):
            n = rng.randint(2, 5)
            teile.append(box("stapel", (0.32, 0.04 * n, 0.26), (-b / 2 + 0.25 + i * 0.37, 0.905 + 0.02 * n, 0.05),
                             rng.choice(SHIRT_FARBEN)))
        teile.append(box("rakel", (0.35, 0.03, 0.06), (0.2, 0.92, -0.22), "m3_holz_dunkel"))
        teile.append(box("rakel_gummi", (0.35, 0.02, 0.02), (0.2, 0.9, -0.2), "m3_orange"))
    for i in range(3):
        teile.append(box("unten", (0.3, 0.05 * (i + 2), 0.25), (-b / 2 + 0.3 + i * 0.45, 0.195 + 0.025 * (i + 2), 0),
                         rng.choice(["karton", "m3_grau_hell", "m3_weiss"])))
    return teile


def belichter():
    """Belichtungsgeraet: flacher Kasten mit Glasdeckel auf Unterschrank."""
    teile = [box("schrank", (1.0, 0.7, 0.6), (0, 0.35, 0), "m3_grau_hell", r=0.02),
             box("geraet", (1.0, 0.18, 0.66), (0, 0.79, 0), "m3_anthrazit", r=0.015),
             box("glas", (0.86, 0.01, 0.52), (0, 0.885, 0), "m3_glas"),
             box("deckel", (1.0, 0.04, 0.2), (0, 0.9, -0.24), "m3_schwarz"),
             box("knopf", (0.1, 0.03, 0.02), (0.35, 0.79, 0.335), "m3_neon_orange"),
             box("sieb", (0.5, 0.02, 0.4), (-0.1, 0.9, 0.02), "m3_sieb")]
    return teile


def spritzer(seed=11, n=6):
    """Farbflecken am Boden (flach)."""
    rng = random.Random(seed)
    teile = []
    for i in range(n):
        teile.append(zylinder("fleck", rng.uniform(0.05, 0.14), 0.003, (rng.uniform(-0.6, 0.6), 0, rng.uniform(-0.6, 0.6)),
                              rng.choice(["m3_orange", "m3_blau", "m3_pink", "m3_gelb"]), seiten=7))
    return teile


# --- Romans Buero -------------------------------------------------------------------

def zeichentisch():
    """Zeichentisch mit schraeger Platte (Vorderseite +z), Papier, Lineal,
    Klemmleuchte."""
    teile = []
    for s in (-1, 1):
        teile.append(stab("bein_v", (s * 0.55, 0.0, 0.3), (s * 0.55, 0.85, 0.0), 0.04, "m3_schwarz"))
        teile.append(stab("bein_h", (s * 0.55, 0.0, -0.3), (s * 0.55, 0.95, -0.1), 0.04, "m3_schwarz"))
    teile.append(box("quer", (1.1, 0.03, 0.03), (0, 0.3, 0), "m3_schwarz"))
    platte = [
        box("platte", (1.3, 0.035, 0.85), (0, 0, 0), "m3_holz_hell", r=0.01),
        box("papier", (0.6, 0.004, 0.45), (-0.1, 0.02, 0.05), "m3_weiss"),
        box("skizze", (0.25, 0.002, 0.2), (-0.15, 0.024, 0.02), "m3_orange_hell"),
        box("skizze2", (0.12, 0.002, 0.12), (0.08, 0.024, 0.14), "m3_blau"),
        box("lineal", (0.9, 0.01, 0.05), (0, 0.025, 0.37), "m3_holz_dunkel"),
        box("leiste", (1.3, 0.04, 0.03), (0, 0.03, 0.43), "m3_holz"),
    ]
    platte = bei(platte)
    for t in platte:
        t.matrix_world = Matrix.Rotation(math.radians(18), 4, "X") @ t.matrix_world
    teile += bei(platte, y=0.98, z=0.02)
    lampe = [zylinder("klemme", 0.03, 0.08, (0, 0, 0), "m3_schwarz", seiten=6)]
    lampe.append(stab("arm1", (0, 0.08, 0), (0.1, 0.45, 0.1), 0.02, "m3_anthrazit"))
    lampe.append(stab("arm2", (0.1, 0.45, 0.1), (0.05, 0.6, 0.35), 0.02, "m3_anthrazit"))
    lampe.append(zylinder("schirm", 0.09, 0.1, (0.05, 0.52, 0.38), "m3_anthrazit", seiten=8, radius_oben=0.04))
    lampe.append(zylinder("birne", 0.07, 0.01, (0.05, 0.515, 0.38), "m3_licht", seiten=8))
    teile += bei(lampe, x=0.55, y=1.12, z=-0.35)
    return teile


def hocker(h=0.7, sitz="m3_orange"):
    teile = [zylinder("sitz", 0.18, 0.05, (0, h, 0), sitz, seiten=12, rund=0.01)]
    for i in range(4):
        a = math.radians(45 + i * 90)
        teile.append(stab("bein", (math.cos(a) * 0.11, h, math.sin(a) * 0.11),
                          (math.cos(a) * 0.19, 0.0, math.sin(a) * 0.19), 0.025, "m3_holz"))
    teile.append(zylinder("ring", 0.15, 0.02, (0, 0.25, 0), "m3_schwarz", seiten=8, deckel=False))
    return teile


def moodboard(b=1.4, h=1.5):
    rng = random.Random(12)
    teile = [box("platte", (b, 0.9, 0.03), (0, h - 0.45, 0), "m3_sperrholz", r=0.01)]
    for s in (-1, 1):
        teile.append(box("bein", (0.04, h - 0.1, 0.04), (s * (b / 2 - 0.1), (h - 0.1) / 2, -0.03), "m3_schwarz"))
        teile.append(box("fuss", (0.05, 0.03, 0.4), (s * (b / 2 - 0.1), 0.015, -0.03), "m3_schwarz"))
    farben = ["m3_orange", "m3_mint", "m3_pink", "m3_gelb", "m3_blau", "m3_weiss", "m3_schwarz", "m3_lila"]
    for i in range(10):
        w = rng.uniform(0.14, 0.3)
        hh = rng.uniform(0.12, 0.3)
        x = -b / 2 + 0.15 + (i % 5) * (b - 0.3) / 4 + rng.uniform(-0.04, 0.04)
        y = h - 0.22 - (i // 5) * 0.42 + rng.uniform(-0.04, 0.04)
        teile.append(box("zettel", (w, hh, 0.006), (x, y, 0.02), farben[i % len(farben)]))
    return teile


def sneakerregal(b=1.8, h=1.6, t=0.36):
    rng = random.Random(13)
    teile = [box("wange_l", (0.03, h, t), (-b / 2 + 0.015, h / 2, 0), "m3_weiss"),
             box("wange_r", (0.03, h, t), (b / 2 - 0.015, h / 2, 0), "m3_weiss"),
             box("rueck", (b, h, 0.015), (0, h / 2, -t / 2 + 0.008), "m3_orange_hell")]
    ebenen = [0.05, 0.42, 0.79, 1.16, h - 0.02]
    for y in ebenen:
        teile.append(box("brett", (b - 0.06, 0.025, t), (0, y, 0), "m3_weiss"))
    kombis = [("m3_weiss", "m3_orange"), ("m3_schwarz", "m3_weiss"), ("m3_mint", "m3_weiss"),
              ("m3_rot", "m3_schwarz"), ("m3_blau", "m3_gelb"), ("m3_grau_hell", "m3_pink")]
    for k, y in enumerate(ebenen[:-1]):
        for i in range(3):
            f, a = kombis[(k * 3 + i) % len(kombis)]
            if k == 0 and i != 1:
                teile.append(box("schuhkarton", (0.4, 0.2, 0.26), (-b / 2 + 0.3 + i * 0.6, y + 0.1125, 0),
                                 "m3_orange" if i else "karton"))
                continue
            teile += bei(sneaker_paar(f, a, einfach=True), x=-b / 2 + 0.3 + i * 0.6, y=y + 0.0125,
                         dreh=rng.uniform(-15, 15))
    return teile


def sofa(b=1.9, t=0.85, stoff="m3_senf"):
    teile = [
        box("sockel", (b, 0.12, t), (0, 0.1, 0), "m3_holz_dunkel", r=0.02),
        box("sitz", (b - 0.3, 0.16, t - 0.2), (0, 0.24, 0.08), stoff, r=0.05),
        box("lehne", (b, 0.48, 0.2), (0, 0.4, -t / 2 + 0.1), stoff, r=0.06),
        box("arm_l", (0.16, 0.36, t), (-b / 2 + 0.08, 0.34, 0), stoff, r=0.06),
        box("arm_r", (0.16, 0.36, t), (b / 2 - 0.08, 0.34, 0), stoff, r=0.06),
        box("kissen_a", (0.4, 0.34, 0.12), (-0.45, 0.48, -t / 2 + 0.27), "m3_orange", r=0.05),
        box("kissen_b", (0.38, 0.32, 0.12), (0.5, 0.47, -t / 2 + 0.26), "m3_mint", r=0.05),
        box("decke", (0.4, 0.03, t - 0.1), (0.62, 0.33, 0.05), "m3_creme", r=0.012),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(zylinder("fuss", 0.025, 0.05, (sx * (b / 2 - 0.1), 0.0, sz * (t / 2 - 0.1)), "m3_schwarz", seiten=6))
    return teile


def couchtisch():
    teile = [zylinder("platte", 0.42, 0.04, (0, 0.38, 0), "m3_holz_hell", seiten=16, rund=0.01)]
    for i in range(3):
        a = math.radians(90 + i * 120)
        teile.append(stab("bein", (math.cos(a) * 0.25, 0.38, math.sin(a) * 0.25),
                          (math.cos(a) * 0.3, 0.0, math.sin(a) * 0.3), 0.03, "m3_schwarz"))
    teile += [
        box("magazin", (0.24, 0.02, 0.3), (-0.12, 0.43, 0.05), "m3_orange", r=0.004),
        box("magazin2", (0.22, 0.015, 0.28), (-0.1, 0.447, 0.04), "m3_weiss"),
        zylinder("becher", 0.04, 0.09, (0.18, 0.42, -0.1), "m3_mint", seiten=8),
    ]
    teile += bei(sneaker(), x=0.1, y=0.42, z=0.15, dreh=60)
    return teile


def schreibtisch(b=1.4, t=0.7):
    teile = [box("platte", (b, 0.04, t), (0, 0.74, 0), "m3_holz_hell", r=0.012)]
    for s in (-1, 1):
        teile.append(box("wange", (0.05, 0.72, t - 0.1), (s * (b / 2 - 0.08), 0.36, 0), "m3_schwarz"))
    teile += [
        box("monitor", (0.62, 0.38, 0.03), (0, 1.02, -0.2), "m3_stahl", r=0.01),
        box("anzeige", (0.56, 0.32, 0.005), (0, 1.02, -0.183), "m3_bildschirm_an"),
        box("motiv", (0.2, 0.14, 0.004), (-0.08, 1.04, -0.179), "m3_orange"),
        box("fuss", (0.05, 0.14, 0.05), (0, 0.83, -0.23), "m3_stahl"),
        box("fussplatte", (0.2, 0.01, 0.16), (0, 0.765, -0.22), "m3_stahl"),
        box("tablett", (0.34, 0.012, 0.24), (0.1, 0.766, 0.12), "m3_schwarz", r=0.004),
        zylinder("stifte", 0.04, 0.1, (0.55, 0.76, -0.2), "m3_orange", seiten=8),
        zylinder("becher", 0.04, 0.09, (-0.5, 0.76, 0.05), "m3_weiss", seiten=8),
    ]
    teile += bei(pflanze(0.35, "topf_creme", "mini"), x=-0.55, y=0.76, z=-0.2)
    return teile


def buerostuhl(bezug="m3_anthrazit"):
    teile = [box("sitz", (0.48, 0.08, 0.46), (0, 0.48, 0), bezug, r=0.03),
             box("lehne", (0.44, 0.52, 0.07), (0, 0.8, -0.24), bezug, r=0.03),
             zylinder("saeule", 0.03, 0.36, (0, 0.08, 0), "m3_stahl", seiten=6)]
    for i in range(5):
        a = math.radians(i * 72)
        teile.append(stab("stern", (0, 0.08, 0), (math.cos(a) * 0.3, 0.05, math.sin(a) * 0.3), 0.035, "m3_schwarz"))
    return teile


def planschrank():
    teile = [box("korpus", (1.0, 0.72, 0.62), (0, 0.4, 0), "m3_weiss", r=0.015),
             box("sockel", (0.94, 0.04, 0.56), (0, 0.02, 0), "m3_schwarz")]
    for i in range(4):
        teile.append(box("lade", (0.94, 0.14, 0.012), (0, 0.15 + i * 0.165, 0.315), "m3_weiss"))
        teile.append(box("griff", (0.3, 0.02, 0.02), (0, 0.2 + i * 0.165, 0.33), "m3_grau"))
    for i, m in enumerate(("m3_weiss", "m3_orange_hell", "m3_grau_hell")):
        teile.append(liegender_zylinder("rolle", 0.04, 0.8, (0, 0.8, -0.18 + i * 0.1), "x", m, seiten=8))
    return teile


def poster_angelehnt(w=0.6, h=0.85, motiv="m3_orange", rahmen="m3_schwarz", motiv2="m3_mint"):
    teile = [box("rahmen", (w, h, 0.03), (0, 0, 0), rahmen),
             box("bild", (w - 0.08, h - 0.08, 0.008), (0, 0, 0.017), "m3_creme"),
             zylinder("kreis", w * 0.25, 0.01, (0, 0, 0), motiv, seiten=12),
             box("balken", (w * 0.5, h * 0.1, 0.008), (0, -h * 0.28, 0.022), motiv2)]
    kreis = teile[2]
    kreis.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    kreis.data.transform(Matrix.Translation(G(0, h * 0.08, 0.025)))
    for t in teile:
        t.matrix_world = Matrix.Rotation(math.radians(-10), 4, "X") @ t.matrix_world
    return bei(teile, y=h / 2 + 0.01)


def staffelei(h=1.6):
    teile = [stab("bein_l", (-0.3, 0.0, 0.15), (0.0, h, -0.05), 0.035, "m3_holz"),
             stab("bein_r", (0.3, 0.0, 0.15), (0.0, h, -0.05), 0.035, "m3_holz"),
             stab("bein_h", (0.0, 0.0, -0.45), (0.0, h - 0.05, -0.06), 0.03, "m3_holz"),
             box("ablage", (0.6, 0.03, 0.08), (0, 0.6, 0.1), "m3_holz")]
    tafel = [box("leinwand", (0.62, 0.8, 0.03), (0, 0, 0), "m3_weiss"),
             box("form", (0.3, 0.3, 0.006), (-0.05, 0.1, 0.018), "m3_orange"),
             box("form2", (0.36, 0.08, 0.006), (0.04, -0.22, 0.018), "m3_schwarz")]
    for t in tafel:
        t.matrix_world = Matrix.Rotation(math.radians(-12), 4, "X") @ t.matrix_world
    teile += bei(tafel, y=1.02, z=0.06)
    return teile


def skateboard():
    teile = [box("brett", (0.2, 0.78, 0.015), (0, 0, 0), "m3_orange", r=0.006),
             box("grip", (0.18, 0.7, 0.004), (0, 0, -0.01), "m3_schwarz")]
    for y in (-0.26, 0.26):
        teile.append(box("achse", (0.16, 0.03, 0.04), (0, y, 0.03), "m3_stahl"))
        for s in (-1, 1):
            teile.append(liegender_zylinder("rolle", 0.028, 0.03, (s * 0.09, y, 0.05), "x", "m3_mint", seiten=6))
    for t in teile:
        t.matrix_world = Matrix.Rotation(math.radians(-14), 4, "X") @ t.matrix_world
    return bei(teile, y=0.4)


def stehlampe(h=1.55):
    return [zylinder("fuss", 0.16, 0.03, (0, 0, 0), "m3_schwarz", seiten=10),
            zylinder("stiel", 0.015, h, (0, 0.03, 0), "m3_schwarz", seiten=6),
            zylinder("schirm", 0.2, 0.26, (0, h - 0.05, 0), "m3_creme", seiten=12, radius_oben=0.14),
            zylinder("licht", 0.17, 0.01, (0, h - 0.06, 0), "m3_licht", seiten=12)]


def sitzsack(farbe="m3_mint"):
    return [kugel("sack", 0.42, (0, 0.24, 0), farbe, stauchung=0.6, ringe=6, seiten=10),
            kugel("mulde", 0.26, (0, 0.44, 0.05), farbe, stauchung=0.35, ringe=4, seiten=8)]


# --- Werkstatt ----------------------------------------------------------------------

def niedriges_regal(b=1.8, t=0.45, h=0.9, seed=14, inhalt="stoff"):
    rng = random.Random(seed)
    teile = [box("korpus_l", (0.03, h, t), (-b / 2 + 0.015, h / 2, 0), "m3_sperrholz"),
             box("korpus_r", (0.03, h, t), (b / 2 - 0.015, h / 2, 0), "m3_sperrholz"),
             box("mitte", (0.03, h, t), (0, h / 2, 0), "m3_sperrholz"),
             box("rueck", (b, h, 0.012), (0, h / 2, -t / 2 + 0.006), "m3_holz")]
    for y in (0.04, h / 2, h - 0.015):
        teile.append(box("brett", (b, 0.03, t), (0, y, 0), "m3_sperrholz"))
    # Faecher
    for fx in (-b / 4, b / 4):
        for y in (0.055, h / 2 + 0.015):
            if inhalt == "stoff":
                for i in range(3):
                    teile.append(liegender_zylinder("stoffrolle", 0.06, 0.28, (fx - 0.26 + i * 0.26, y + 0.06, 0.02),
                                                    "z", rng.choice(SHIRT_FARBEN), seiten=8))
            else:
                teile.append(box("kiste", (b / 2 - 0.12, 0.26, t - 0.1), (fx, y + 0.13, 0.02),
                                 rng.choice(["m3_orange", "m3_grau_hell", "m3_mint"]), r=0.015))
                teile.append(box("etikett", (0.12, 0.05, 0.005), (fx, y + 0.16, t / 2 - 0.028), "m3_weiss"))
    # oben
    if inhalt == "stoff":
        teile += bei(karton(0.42, 0.18, 0.32), x=-0.5, y=h)
        teile.append(box("shirtstapel", (0.34, 0.12, 0.28), (0.1, h + 0.06, 0.0), "m3_weiss"))
        teile.append(box("shirtstapel2", (0.34, 0.08, 0.28), (0.1, h + 0.16, 0.0), "m3_orange"))
        teile += bei(pflanze(0.45, "topf_terra", "mini"), x=0.65, y=h)
    else:
        for i in range(3):
            teile.append(liegender_zylinder("klebeband", 0.05, 0.05, (-0.6 + i * 0.13, h + 0.05, 0.05), "x",
                                            "m3_senf" if i != 1 else "m3_orange", seiten=8))
        teile.append(box("versandtaschen", (0.4, 0.1, 0.3), (-0.05, h + 0.05, 0), "m3_grau_hell", r=0.01))
        teile += bei(karton(0.36, 0.26, 0.3), x=0.55, y=h, dreh=6)
        teile += bei(karton(0.26, 0.16, 0.22, "karton_hell"), x=0.55, y=h + 0.26, dreh=-10)
    return teile


def packpapier_rolle():
    teile = [box("fuss", (0.7, 0.04, 0.35), (0, 0.02, 0), "m3_schwarz")]
    for s in (-1, 1):
        teile.append(box("wange", (0.03, 0.75, 0.05), (s * 0.33, 0.4, 0), "m3_schwarz"))
    teile.append(liegender_zylinder("rolle", 0.12, 0.62, (0, 0.62, 0), "x", "karton", seiten=10))
    teile.append(box("bahn", (0.6, 0.004, 0.4), (0, 0.5, 0.2), "karton"))
    return teile


def muelltonne(mat="m3_grau"):
    return [zylinder("tonne", 0.2, 0.55, (0, 0, 0), mat, seiten=10, radius_oben=0.22),
            zylinder("deckel", 0.23, 0.04, (0, 0.55, 0), "m3_anthrazit", seiten=10)]


def kartonstapel(seed=15, n=3):
    rng = random.Random(seed)
    teile = []
    y = 0.0
    for i in range(n):
        b, h, t = rng.uniform(0.4, 0.55), rng.uniform(0.25, 0.38), rng.uniform(0.32, 0.42)
        teile += bei(karton(b - 0.05 * i, h, t - 0.03 * i, rng.choice(["karton", "karton_hell"])),
                     y=y, dreh=rng.uniform(-10, 10))
        y += h
    return teile


# ==============================================================================
# ZONEN
# ==============================================================================

def einrichtung_werkstatt():
    """Werkstatt 7 x 7 (Start). intake und processing stehen hinten an der
    Wand, buffer in der Mitte. Moebel an den Seitenwaenden und vorn."""
    setzen("pflanze_ecke_links", pflanze(0.5, "topf_terra", "mini"), x=-3.27, z=-3.27)
    setzen("tonne_ecke_rechts", muelltonne("m3_grau"), x=3.15, z=-3.15)
    setzen("regal_links", niedriges_regal(1.8, inhalt="stoff"), x=-3.15, z=-0.1, dreh=90)
    setzen("regal_rechts", niedriges_regal(1.8, seed=16, inhalt="kisten"), x=3.15, z=-0.1, dreh=-90)
    setzen("stange_vorn_links", kleiderstange(1.2, 6, seed=3), x=-3.0, z=2.2, dreh=90)
    setzen("kartons_vorn_links", kartonstapel(15, 3), x=-1.8, z=3.0)
    setzen("karton_vorn_links_b", karton(0.5, 0.34, 0.4), x=-1.8, z=2.3)
    setzen("pflanze_vorn_links", pflanze(1.1, "topf_creme", "hoch"), x=-3.12, z=3.15)
    setzen("hocker_links", hocker(0.62, "m3_mint"), x=-1.8, z=1.2)
    setzen("matte_links", teppich(1.1, 0.8, "m3_orange_hell", "m3_weiss"), x=-2.1, z=1.0)
    setzen("rollwagen_vorn", rollwagen(seed=6), x=2.0, z=2.8, dreh=-90)
    setzen("packpapier", packpapier_rolle(), x=2.95, z=1.75, dreh=-90)
    setzen("pflanze_vorn_rechts", pflanze(1.2, "topf_terra", "hoch"), x=2.98, z=3.02)
    setzen("tonne_vorn", muelltonne(), x=1.75, z=1.1)
    setzen("kiste_vorn_mitte", [box("kiste", (1.2, 0.3, 0.4), (0, 0.15, 0), "m3_sperrholz", r=0.015),
                                box("kiste_rand", (1.1, 0.02, 0.3), (0, 0.3, 0), "m3_erde")]
           + bei(pflanze(0.5, "topf_terra", "mini"), x=-0.3, y=0.3)
           + bei(pflanze(0.45, "topf_creme", "mini"), x=0.25, y=0.3), x=0.0, z=3.15)
    band = []
    for (sx, sz, px, pz) in ((1.3, 0.06, -2.0, -1.2), (0.06, 1.0, -0.72, -1.72), (1.3, 0.06, 1.8, -1.2),
                             (0.06, 1.0, 0.52, -1.72), (2.4, 0.06, 0.0, 1.85)):
        band.append(box("band", (sx, 0.004, sz), (px, 0.002, pz), "m3_gelb"))
    setzen("bodenband", band)
    setzen("kartons_rechts", kartonstapel(41, 2), x=2.1, z=1.9)


def einrichtung_laden():
    """Laden 21 x 3: hinten Regale, Kleiderstangen, Spiegel, Theke; vorn nur
    Hohes. Laufgang in der Mitte (z lokal 0,2), Station rechts bei x 8,4."""
    setzen("pflanze_links", pflanze(1.2, "topf_creme", "hoch"), x=-10.05, z=-1.05)
    setzen("regal_links", regal_shirts(1.6, seed=2), x=-9.0, z=-1.17)
    setzen("stange_hinten_a", kleiderstange(1.4, 8, seed=4), x=-5.25, z=-0.95)
    setzen("spiegel", spiegel_stand(), x=-3.7, z=-1.08)
    setzen("stange_hinten_b", kleiderstange(1.4, 8, seed=5, lang=True), x=-2.15, z=-0.95)
    setzen("pflanze_tuer", pflanze(0.8, "topf_terra", "hoch"), x=-1.05, z=-1.12)
    setzen("pflanze_tuer_r", pflanze(1.1, "topf_creme", "hoch"), x=1.02, z=-1.02)
    setzen("theke", theke_ende(2.2), x=2.95, z=-0.98)
    setzen("regal_rechts", regal_shirts(0.9, seed=7, oben="pflanze"), x=4.75, z=-1.17)
    setzen("pflanze_station", pflanze(0.8, "topf_terra", "hoch"), x=6.95, z=-1.15)
    setzen("sneaker_wuerfel", wuerfel_podest(0.4, 0.55), x=10.0, z=-1.1)
    setzen("caps", muetzen_staender(), x=-9.3, z=1.1)
    setzen("pflanze_vorn_links", pflanze(0.9, "topf_terra", "hoch"), x=-8.2, z=1.15)
    setzen("stange_vorn", kleiderstange(1.3, 7, seed=8), x=-4.1, z=1.08)
    setzen("pflanze_vorn_mitte", pflanze(1.0, "topf_creme", "hoch"), x=-1.1, z=1.15)
    setzen("puppe_vorn", puppe("m3_mint", "m3_schwarz"), x=2.6, z=1.1)
    setzen("bank_vorn", bank(1.0, 0.36, 0.45, "m3_holz"), x=4.3, z=1.15)
    setzen("pflanze_vorn_rechts", pflanze(1.0, "topf_creme", "hoch"), x=10.0, z=1.1)
    setzen("teppich_laufgang", teppich(3.0, 0.8, "m3_creme", "m3_grau_hell"), x=-5.5, z=0.2)


def einrichtung_lager():
    setzen("regal_a", schwerlastregal(1.2, seed=4), x=-0.3, z=-2.05)
    setzen("regal_b", schwerlastregal(1.5, seed=21), x=2.55, z=-2.05)
    setzen("palette_fenster", palette_kartons(22, 1), x=-2.3, z=-1.95)
    setzen("leiter", stehleiter(), x=1.0, z=-2.0, dreh=90)
    setzen("kartons_links", kartonstapel(23, 2), x=-3.05, z=-0.9)
    setzen("sackkarre", sackkarre(), x=-3.05, z=2.0, dreh=90)
    setzen("palette_mitte", palette_kartons(24, 2), x=-1.35, z=-0.3)
    setzen("rollwagen", rollwagen(seed=25), x=1.1, z=-0.4)
    setzen("folie", stretchfolie(), x=2.4, z=-0.55)
    setzen("kartons_vorn_links", kartonstapel(26, 3), x=-2.2, z=2.0)
    setzen("karton_vorn", karton(0.5, 0.3, 0.4, "karton_hell"), x=-1.5, z=2.05)
    setzen("gitterbox", gitterbox(), x=1.85, z=2.0)
    setzen("pflanze_vorn", pflanze(0.7, "topf_terra", "hoch"), x=3.1, z=2.1)
    setzen("markierung", [box("streifen", (6.6, 0.004, 0.08), (0, 0.002, 0), "m3_gelb")], z=0.45)
    setzen("markierung_b", [box("streifen", (6.6, 0.004, 0.08), (0, 0.002, 0), "m3_gelb")], z=1.55)


def einrichtung_showroom():
    """Showroom: Holzbuehne an der Rueckwand, Neon-Schwung darueber, Puppen im
    Schaufenster, zwei Spots. Mitte (Sonderstation) frei, Laufsteg-Teppich."""
    setzen("buehne", buehne(6.8, 1.2, 0.18), z=-1.78)
    setzen("neon", neon_form(1.4, 0.5), x=-1.85, y=1.55, z=-2.4)
    setzen("puppe_links", puppe("m3_orange", "m3_schwarz"), x=-2.55, y=0.18, z=-1.8, dreh=15)
    setzen("puppe_links_b", puppe("m3_weiss", "m3_blau", kapuze=False), x=-1.6, y=0.18, z=-1.85, dreh=5)
    setzen("puppe_rechts", puppe("m3_schwarz", "m3_grau", kapuze=True), x=2.55, y=0.18, z=-1.8, dreh=-15)
    setzen("puppe_rechts_b", puppe("m3_mint", "m3_schwarz", kapuze=False), x=1.6, y=0.18, z=-1.85, dreh=-5)
    setzen("pflanze_buehne_l", pflanze(0.9, "topf_creme", "hoch"), x=-3.12, y=0.18, z=-2.1)
    setzen("pflanze_buehne_r", pflanze(0.9, "topf_creme", "hoch"), x=3.12, y=0.18, z=-2.1)
    setzen("spot_links", spot_stativ(), x=-2.95, z=-0.55, dreh=140)
    setzen("spot_rechts", spot_stativ(), x=2.95, z=-0.55, dreh=-140)
    setzen("pouf_links", sitzsack("m3_orange"), x=-1.75, z=0.05)
    setzen("pouf_rechts", sitzsack("m3_lila"), x=2.3, z=0.45)
    setzen("laufsteg", teppich(1.0, 3.5, "m3_orange", "m3_weiss"), x=0.6, z=0.6)
    setzen("pflanze_vorn_l", pflanze(0.6, "topf_terra", "hoch"), x=-3.15, z=2.27)
    setzen("pflanze_vorn_r", pflanze(0.6, "topf_terra", "hoch"), x=3.15, z=2.27)


def einrichtung_fotostudio():
    setzen("hohlkehle", hintergrund_rolle(3.0, 2.3, 1.2), z=-2.4)
    setzen("produkttisch", produkttisch(), x=0.0, z=-1.05)
    setzen("softbox_links", softbox(), x=-2.1, z=-0.6, dreh=110)
    setzen("softbox_rechts", softbox(), x=1.95, z=-0.5, dreh=-75)
    setzen("kamera", kamera_stativ(), x=0.8, z=0.2, dreh=180)
    setzen("reflektor", reflektor(), x=-2.25, z=0.65, dreh=150)
    setzen("stange_shooting", kleiderstange(1.2, 6, seed=31, lang=True), x=-2.95, z=-1.0, dreh=90)
    setzen("rollen", rollen_regal(), x=3.0, z=-1.7, dreh=-90)
    setzen("laptop", stehtisch_laptop(), x=2.5, z=0.1, dreh=-90)
    setzen("kartons_vorn", bei(karton(0.42, 0.3, 0.28), dreh=5) + bei(karton(0.3, 0.22, 0.24, "karton_hell"), y=0.3, dreh=-8), x=2.6, z=2.23)
    setzen("pflanze_vorn_l", pflanze(0.7, "topf_creme", "hoch"), x=-3.12, z=2.22)
    setzen("hocker", hocker(0.65, "m3_orange"), x=-2.2, z=2.2)
    setzen("markierung", [box("tape_%d" % i, s, m, "m3_orange") for i, (s, m) in enumerate((
        ((0.2, 0.003, 0.04), (-0.1, 0.0015, 0)), ((0.04, 0.003, 0.2), (0, 0.0015, 0.08))))], x=0.6, z=0.55)


def einrichtung_siebdruck():
    setzen("gummimatte", teppich(2.4, 2.4, "m3_gummi", "m3_anthrazit"), x=-1.9, z=-1.6)
    setzen("karussell", karussell(), x=-1.9, z=-1.6)
    setzen("flecken", spritzer(), x=-1.2, z=0.0)
    setzen("blitztrockner", blitztrockner(), x=-1.0, z=-2.95, dreh=-60)
    setzen("siebe", siebe_angelehnt(), x=1.0, z=-3.25)
    setzen("trockenregal", trockenregal(), x=2.35, z=-2.9)
    setzen("auswaschen", auswaschkabine(), x=3.0, z=-1.1, dreh=-90)
    setzen("eimer", eimergruppe(), x=-2.9, z=0.95)
    setzen("pflanze_links", pflanze(0.8, "topf_terra", "hoch"), x=-3.12, z=-3.12)
    setzen("arbeitstisch", arbeitstisch(1.6, 0.7), x=-2.3, z=2.65)
    setzen("belichter", belichter(), x=-0.25, z=2.8)
    setzen("rollwagen", rollwagen(seed=33, ladung="shirts"), x=2.0, z=2.7, dreh=-90)
    setzen("pflanze_vorn", pflanze(1.1, "topf_creme", "hoch"), x=3.02, z=3.05)
    setzen("siebe_vorn", siebe_angelehnt(3, seed=34), x=0.9, z=3.2)


def einrichtung_romans_buero():
    setzen("moodboard", moodboard(), x=-2.35, z=-3.12)
    setzen("zeichentisch", zeichentisch(), x=-2.35, z=-2.15)
    setzen("hocker", hocker(0.72, "m3_orange"), x=-2.3, z=-1.2)
    setzen("planschrank", planschrank(), x=-3.05, z=-0.25, dreh=90)
    setzen("pflanze_tuer", pflanze(0.8, "topf_terra", "hoch"), x=0.1, z=-3.15)
    setzen("skateboard", skateboard(), x=0.75, z=-3.3)
    setzen("sneakerregal", sneakerregal(), x=2.15, z=-3.2)
    setzen("schreibtisch", schreibtisch(), x=2.35, z=-1.55)
    setzen("stuhl", buerostuhl("m3_anthrazit"), x=2.3, z=-0.85, dreh=180)
    setzen("teppich", teppich(2.0, 1.7, "m3_creme", "m3_grau_hell"), x=1.85, z=2.35)
    setzen("sofa", sofa(1.9, 0.85, "m3_senf"), x=2.95, z=2.3, dreh=-90)
    setzen("couchtisch", couchtisch(), x=1.55, z=2.3)
    setzen("stehlampe", stehlampe(), x=3.1, z=0.95)
    setzen("poster_a", poster_angelehnt(0.6, 0.85, "m3_orange", "m3_schwarz", "m3_mint"), x=0.95, z=3.2)
    setzen("staffelei", staffelei(), x=-0.95, z=2.75)
    setzen("sitzsack", sitzsack("m3_mint"), x=-2.3, z=2.55)
    setzen("pflanze_vorn_l", pflanze(1.2, "topf_creme", "hoch"), x=-3.1, z=3.1)
    setzen("poster_b", poster_angelehnt(0.5, 0.7, "m3_blau", "m3_holz", "m3_orange"), x=-1.8, z=3.25)


# ==============================================================================
# AUSSEN (Weltkoordinaten, Ursprung 0,0)
# ==============================================================================
# Gebaeude: Waende x -10,5..10,5, z -8,5..6,5. Fundament +0,5 je Seite.
# Strasse laeuft VORN (+z) und RECHTS (+x) -- das ist die Ecke. Dort steht
# nichts hoeher als 1 m. Hohes (Laternen, Baeume, Nachbarhaeuser) nur hinten
# und links: das liegt im Bild oben und verdeckt nichts.

FUND = (-11.0, 11.0, -9.0, 7.0)
GEH_Y = -0.14
STRASSE_Y = -0.30


def platte(name, x0, x1, z0, z1, y_oben, y_unten, mat, r=0.0):
    return box(name, (x1 - x0, y_oben - y_unten, z1 - z0), ((x0 + x1) / 2, (y_oben + y_unten) / 2, (z0 + z1) / 2), mat, r=r)


def fundament():
    """L-Form: volle Breite bis z = 0, darunter nur links (x < 4). Rechts vorn liegt der Hof."""
    return [platte("fundament", FUND[0], FUND[1], FUND[2], 0.0, -0.02, -0.34, "m3_sockel", r=0.03),
            platte("fundament_l", FUND[0], 4.0, 0.0, FUND[3], -0.02, -0.34, "m3_sockel", r=0.03)]


def fugen_x(x0, x1, z0, z1, schritt, y):
    teile = []
    x = math.ceil(x0 / schritt) * schritt
    while x < x1 - 0.01:
        if x > x0 + 0.01:
            teile.append(box("fuge", (0.03, 0.002, z1 - z0), (x, y, (z0 + z1) / 2), "m3_gehweg_fuge"))
        x += schritt
    return teile


def fugen_z(x0, x1, z0, z1, schritt, y):
    teile = []
    z = math.ceil(z0 / schritt) * schritt
    while z < z1 - 0.01:
        if z > z0 + 0.01:
            teile.append(box("fuge", (x1 - x0, 0.002, 0.03), ((x0 + x1) / 2, y, z), "m3_gehweg_fuge"))
        z += schritt
    return teile


def laterne(h=3.6):
    return [zylinder("fuss", 0.12, 0.3, (0, 0, 0), "m3_anthrazit", seiten=8),
            zylinder("mast", 0.05, h, (0, 0.3, 0), "m3_anthrazit", seiten=8, radius_oben=0.035),
            box("ausleger", (0.05, 0.05, 0.6), (0, h + 0.25, 0.25), "m3_anthrazit"),
            box("kopf", (0.22, 0.1, 0.42), (0, h + 0.2, 0.5), "m3_anthrazit", r=0.03),
            box("licht", (0.16, 0.01, 0.34), (0, h + 0.145, 0.5), "m3_licht")]


def baum(rng, h=3.4, r=1.1):
    teile = [zylinder("stamm", 0.13, h * 0.55, (0, 0, 0), "m3_stamm", seiten=7, radius_oben=0.08)]
    teile.append(kugel("krone", r, (0, h - r * 0.8, 0), "m3_busch", stauchung=0.9, ringe=6, seiten=10))
    for i in range(3):
        a = rng.uniform(0, 6.28) + i * 2.1
        teile.append(kugel("krone_%d" % i, r * rng.uniform(0.55, 0.7),
                           (math.cos(a) * r * 0.55, h - r * rng.uniform(0.9, 1.3), math.sin(a) * r * 0.55),
                           ["m3_busch_dunkel", "m3_busch_hell", "m3_busch"][i], stauchung=0.9, ringe=5, seiten=8))
    teile.append(box("scheibe", (1.0, 0.02, 1.0), (0, 0.01, 0), "m3_erde"))
    return teile


def busch(rng, r=0.4, h=0.6):
    return [kugel("busch", r, (0, h * 0.5, 0), rng.choice(["m3_busch", "m3_busch_dunkel", "m3_busch_hell"]),
                  stauchung=(h * 0.5) / r, ringe=5, seiten=8),
            kugel("busch2", r * 0.7, (r * 0.5, h * 0.4, r * 0.2), "m3_busch_hell", stauchung=(h * 0.4) / (r * 0.7),
                  ringe=4, seiten=7)]


def haus(x0, x1, z0, z1, h, farbe, rng, fenster_z=True, fenster_x=True, tuer=None):
    """Nachbarhaus als Block: Attika, Dachflaeche, Fensterreihen an der
    Seite zum Laden (+z bzw. +x)."""
    y = GEH_Y
    teile = [platte("haus", x0, x1, z0, z1, y + h, y, farbe),
             platte("attika", x0 - 0.05, x1 + 0.05, z0 - 0.05, z1 + 0.05, y + h + 0.18, y + h - 0.02, "m3_rahmen"),
             platte("dach", x0 + 0.15, x1 - 0.15, z0 + 0.15, z1 - 0.15, y + h + 0.19, y + h + 0.1, "m3_dach")]
    geschosse = max(1, int((h - 0.3) / 1.4))
    if fenster_z:
        n = max(1, int((x1 - x0) / 1.6))
        for g in range(geschosse):
            for i in range(n):
                fx = x0 + (i + 0.5) * (x1 - x0) / n
                fy = y + 0.9 + g * 1.4
                if tuer is not None and g == 0 and i == tuer:
                    teile.append(box("tuer", (0.8, 1.5, 0.04), (fx, y + 0.75, z1 + 0.01), "m3_holz_dunkel"))
                    continue
                teile.append(box("rahmen", (0.78, 0.92, 0.04), (fx, fy, z1 + 0.01), "m3_rahmen"))
                teile.append(box("glas", (0.64, 0.78, 0.04), (fx, fy, z1 + 0.02), "m3_fenster"))
    if fenster_x:
        n = max(1, int((z1 - z0) / 1.6))
        for g in range(geschosse):
            for i in range(n):
                fz = z0 + (i + 0.5) * (z1 - z0) / n
                fy = y + 0.9 + g * 1.4
                teile.append(box("rahmen", (0.04, 0.92, 0.78), (x1 + 0.01, fy, fz), "m3_rahmen"))
                teile.append(box("glas", (0.04, 0.78, 0.64), (x1 + 0.02, fy, fz), "m3_fenster"))
    if rng.random() < 0.7:
        teile.append(box("klima", (0.6, 0.35, 0.5), (x0 + (x1 - x0) * 0.3, y + h + 0.36, (z0 + z1) / 2), "m3_grau_hell"))
    return teile


def markise(laenge, stoff=("m3_orange", "m3_weiss"), y_oben=2.3, y_unten=1.95, tiefe=0.95):
    """Markise entlang lokal x, Wand bei lokal z = 0, ragt nach -z hinaus."""
    teile = []
    n = int(laenge / 0.25)
    for i in range(n):
        x0 = -laenge / 2 + i * laenge / n
        x1 = x0 + laenge / n
        prof = [(-0.02, y_oben), (-tiefe, y_unten), (-tiefe, y_unten - 0.2), (-tiefe - 0.02, y_unten - 0.2),
                (-tiefe - 0.02, y_unten + 0.02), (-0.02, y_oben + 0.03)]
        teile.append(profil_x("bahn", list(reversed(prof)), x0, x1, stoff[i % 2]))
    for s in (-1, 1):
        teile.append(stab("arm", (s * (laenge / 2 - 0.1), y_oben - 0.25, -0.02),
                          (s * (laenge / 2 - 0.1), y_unten + 0.02, -tiefe + 0.05), 0.03, "m3_anthrazit"))
    teile.append(box("kasten", (laenge + 0.1, 0.12, 0.14), (0, y_oben + 0.05, -0.07), "m3_anthrazit"))
    return teile


def fahrradbuegel():
    teile = []
    for s in (-1, 1):
        teile.append(box("stuetze", (0.05, 0.75, 0.05), (s * 0.3, 0.375, 0), "m3_stahl"))
    teile.append(box("oben", (0.65, 0.05, 0.05), (0, 0.75, 0), "m3_stahl"))
    return teile


def fahrrad(rahmen="m3_orange"):
    """Fahrrad entlang lokal x, 0,95 hoch."""
    teile = []
    for x in (-0.5, 0.5):
        teile.append(liegender_zylinder("reifen", 0.33, 0.04, (x, 0.33, 0), "z", "m3_gummi", seiten=12))
        teile.append(liegender_zylinder("nabe", 0.05, 0.06, (x, 0.33, 0), "z", "m3_stahl", seiten=6))
    teile.append(stab("unterrohr", (-0.5, 0.33, 0), (0.05, 0.33, 0), 0.04, rahmen))
    teile.append(stab("sitzrohr", (-0.05, 0.33, 0), (-0.15, 0.78, 0), 0.04, rahmen))
    teile.append(stab("oberrohr", (-0.15, 0.72, 0), (0.35, 0.75, 0), 0.04, rahmen))
    teile.append(stab("gabel", (0.35, 0.8, 0), (0.5, 0.33, 0), 0.035, "m3_stahl"))
    teile.append(stab("kette", (-0.5, 0.33, 0), (-0.05, 0.33, 0), 0.03, rahmen))
    teile.append(stab("strebe", (-0.5, 0.33, 0), (-0.15, 0.72, 0), 0.03, rahmen))
    teile.append(box("sattel", (0.22, 0.05, 0.1), (-0.17, 0.82, 0), "m3_schwarz", r=0.015))
    teile.append(box("lenker", (0.05, 0.04, 0.5), (0.33, 0.9, 0), "m3_schwarz"))
    return teile


def roller():
    """Lieferroller mit oranger Box, 1,0 hoch, entlang lokal x."""
    teile = [liegender_zylinder("rad_h", 0.2, 0.1, (-0.5, 0.2, 0), "z", "m3_gummi", seiten=10),
             liegender_zylinder("rad_v", 0.2, 0.1, (0.55, 0.2, 0), "z", "m3_gummi", seiten=10),
             box("koerper", (0.8, 0.3, 0.34), (-0.25, 0.45, 0), "m3_mint", r=0.08),
             box("boden", (0.5, 0.06, 0.3), (0.2, 0.28, 0), "m3_anthrazit"),
             stab("lenksaeule", (0.45, 0.3, 0), (0.55, 0.85, 0), 0.08, "m3_mint"),
             box("lenker", (0.05, 0.04, 0.55), (0.56, 0.88, 0), "m3_schwarz"),
             box("sitz", (0.45, 0.08, 0.28), (-0.3, 0.64, 0), "m3_schwarz", r=0.03),
             box("box", (0.38, 0.34, 0.36), (-0.62, 0.8, 0), "m3_orange", r=0.03)]
    return teile


def aufsteller():
    teile = []
    for s in (-1, 1):
        tafel = [box("tafel", (0.5, 0.8, 0.03), (0, 0, 0), "m3_orange"),
                 box("feld", (0.4, 0.5, 0.006), (0, 0.05, 0.018), "m3_schwarz"),
                 box("strich", (0.3, 0.04, 0.004), (0, 0.15, 0.022), "m3_weiss"),
                 box("strich2", (0.22, 0.04, 0.004), (0, 0.02, 0.022), "m3_weiss")]
        for t in tafel:
            t.matrix_world = Matrix.Rotation(math.radians(12 * s), 4, "X") @ t.matrix_world
        teile += bei(tafel, y=0.4, z=0.09 * s, dreh=0 if s > 0 else 180)
    return teile


def hydrant():
    return [zylinder("koerper", 0.1, 0.55, (0, 0, 0), "m3_rot", seiten=8),
            kugel("kappe", 0.1, (0, 0.58, 0), "m3_rot", stauchung=0.7, ringe=4, seiten=8),
            liegender_zylinder("stutzen", 0.04, 0.3, (0, 0.38, 0), "x", "m3_rot", seiten=6)]


def poller():
    return [zylinder("poller", 0.06, 0.75, (0, 0, 0), "m3_anthrazit", seiten=8),
            zylinder("ring", 0.065, 0.06, (0, 0.6, 0), "m3_orange", seiten=8)]


def pflanzkasten(b=1.6, t=0.6, rng=None):
    rng = rng or random.Random(40)
    teile = [box("kasten", (b, 0.45, t), (0, 0.225, 0), "m3_holz", r=0.02),
             box("erde", (b - 0.1, 0.02, t - 0.1), (0, 0.44, 0), "m3_erde")]
    for i in range(3):
        teile.append(kugel("busch", 0.26, (-b / 3 + i * b / 3, 0.58, 0),
                           rng.choice(["m3_busch", "m3_busch_dunkel", "m3_busch_hell"]),
                           stauchung=0.75, ringe=4, seiten=7))
    return teile


def lieferwagen():
    """Weisser Transporter, Laengsachse z, Fahrerhaus bei -z, Hecktueren (offen) bei +z.
    Boden bei y = 0. 2,2 hoch, 5,2 lang, 1,9 breit. Seite +x zeigt zur Kamera."""
    L = "m3_lack_van"
    teile = []
    # Ladekasten
    teile.append(box("kasten", (1.9, 1.95, 3.5), (0, 0.4 + 1.95 / 2, 1.1), L, r=0.07, seg=2))
    teile.append(box("dach_rippe", (1.4, 0.04, 3.2), (0, 2.37, 1.1), "m3_lack_van_2", r=0.01))
    # Fahrerhaus: Haube + Kabine
    teile.append(box("haube", (1.86, 0.62, 1.0), (0, 0.4 + 0.31 + 0.2, -2.1), L, r=0.1, seg=2))
    teile.append(box("kabine", (1.88, 1.05, 1.15), (0, 0.4 + 0.52 + 0.55, -0.95), L, r=0.1, seg=2))
    # Scheiben
    teile.append(box("scheibe_vorn", (1.6, 0.62, 0.05), (0, 1.62, -1.52), "m3_glas", r=0.02))
    for sx in (-1, 1):
        teile.append(box("scheibe_seite", (0.04, 0.55, 0.85), (sx * 0.95, 1.65, -0.85), "m3_glas", r=0.01))
    # Chassis, Stossstangen
    teile.append(box("chassis", (1.7, 0.28, 5.0), (0, 0.42, 0.0), "m3_anthrazit"))
    teile.append(box("stoss_vorn", (1.9, 0.2, 0.18), (0, 0.38, -2.65), "m3_stahl", r=0.04))
    teile.append(box("stoss_hinten", (1.92, 0.2, 0.2), (0, 0.38, 2.88), "m3_stahl", r=0.04))
    teile.append(box("scheinwerfer", (1.5, 0.12, 0.04), (0, 0.78, -2.62), "m3_licht"))
    # Raeder
    for sx in (-1, 1):
        for z in (-1.7, 1.9):
            teile.append(liegender_zylinder("rad", 0.4, 0.26, (sx * 0.84, 0.4, z), "x", "m3_gummi", seiten=12))
            teile.append(liegender_zylinder("felge", 0.2, 0.28, (sx * 0.84, 0.4, z), "x", "m3_stahl", seiten=8))
    # Firmenband und Logofeld auf beiden Seiten (Akzent als Folie, nicht als Lack)
    for sx in (-1, 1):
        teile.append(box("band", (0.02, 0.22, 3.5), (sx * 0.955, 0.95, 1.1), "m3_orange"))
        teile.append(box("logo", (0.02, 0.62, 1.2), (sx * 0.955, 1.65, 1.1), "m3_orange", r=0.01))
        teile.append(box("logo_innen", (0.022, 0.4, 0.8), (sx * 0.956, 1.65, 1.1), "m3_weiss", r=0.01))
        teile.append(box("logo_punkt", (0.024, 0.2, 0.2), (sx * 0.957, 1.65, 1.1), "m3_orange", r=0.01))
    # Heck offen: dunkler Laderaum, Ladung, zwei Tueren nach hinten aufgeschwungen
    teile.append(box("laderaum", (1.7, 1.75, 0.04), (0, 0.4 + 1.0, 2.86), "m3_ladung_dunkel"))
    ladung = bei(karton(0.62, 0.5, 0.5), x=-0.5, y=0.82, z=2.6) + bei(karton(0.55, 0.45, 0.5, "karton_hell"), x=0.4, y=0.82, z=2.62, dreh=6)
    ladung += bei(karton(0.5, 0.4, 0.45), x=-0.4, y=1.32, z=2.6, dreh=-5) + bei(karton(0.6, 0.5, 0.5), x=0.4, y=1.27, z=2.6)
    teile += ladung
    for sx in (-1, 1):
        tuer = [box("tuer", (0.9, 1.8, 0.05), (-sx * 0.45, 0.9, 0.0), L, r=0.01),
                box("tuer_fenster", (0.5, 0.5, 0.06), (-sx * 0.45, 1.35, 0.0), "m3_glas")]
        transformieren(tuer, x=sx * 0.93, z=2.9, dreh_grad=sx * 100.0)
        teile += tuer
    return teile


def vordach(laenge=2.4, tiefe=1.0):
    """Orange-weisses Vordach ueber der Ladentuer. Wand bei lokal z = 0, ragt nach -z.
    Zwei schlanke Stuetzen vorn, zwei hinten (die Ladenwand ist nur ein Sockel)."""
    teile = markise(laenge, y_oben=2.35, y_unten=2.0, tiefe=tiefe)
    for s in (-1, 1):
        teile.append(stab("stuetze_v", (s * (laenge / 2 - 0.08), 0.0, -tiefe + 0.08),
                          (s * (laenge / 2 - 0.08), 1.8, -tiefe + 0.08), 0.045, "m3_anthrazit"))
        teile.append(stab("stuetze_h", (s * (laenge / 2 - 0.08), 0.0, 0.0),
                          (s * (laenge / 2 - 0.08), 2.25, 0.0), 0.05, "m3_anthrazit"))
    # Schild unter der Dachkante: beleuchtete Fahne
    teile.append(box("schild", (laenge * 0.6, 0.26, 0.04), (0, 1.84, -tiefe + 0.02), "m3_neon_orange", r=0.01))
    return teile


def hof_flaeche():
    """Hof in der Ausbuchtung (x 3,5..11, z -0,5..7): Asphalt, Parkfeld-Linien,
    gelbe Schraffur vor der Ladentuer, Oelfleck, Gullydeckel."""
    t = []
    y = GEH_Y
    t.append(platte("hof_asphalt", 3.5, 11.0, -0.45, 7.05, y, -0.36, "m3_hof_asphalt"))
    rng = random.Random(5)
    for i in range(7):
        fx, fz = rng.uniform(4.0, 10.6), rng.uniform(0.6, 6.6)
        t.append(box("flick", (rng.uniform(0.6, 1.4), 0.004, rng.uniform(0.5, 1.0)), (fx, y + 0.002, fz), "m3_hof_flick"))
    # Stellplatz fuer den Lieferwagen: weisse Randlinien
    for lx in (8.25, 10.55):
        t.append(box("linie", (0.1, 0.004, 5.6), (lx, y + 0.003, 3.9), "m3_markierung"))
    t.append(box("linie", (2.4, 0.004, 0.1), (9.4, y + 0.003, 1.1), "m3_markierung"))
    # Schraffur vor der Tuer (Ladezone)
    for i in range(6):
        t.append(box("schraffur", (0.14, 0.004, 1.4), (4.9 + i * 0.4, y + 0.003, 0.7), "m3_hof_gelb"))
    t.append(box("rand_gelb", (2.6, 0.004, 0.1), (5.9, y + 0.003, 1.45), "m3_hof_gelb"))
    t.append(box("rand_gelb", (2.6, 0.004, 0.1), (5.9, y + 0.003, -0.3), "m3_hof_gelb"))
    # Stufe zur Ladentuer
    t.append(platte("stufe", 5.35, 6.65, -0.45, 0.45, y + 0.075, y - 0.02, "m3_sockel", r=0.01))
    t.append(zylinder("gully", 0.22, 0.01, (4.4, y, 4.9), "m3_anthrazit", seiten=10))
    return t


def umgebung():
    rng = random.Random(77)
    t = []
    # Gehweg rund ums Fundament
    geh = [(-13.5, 14.5, 7.0, 10.0), (11.0, 14.5, -11.5, 7.0), (-13.5, 11.0, -11.5, -9.0), (-13.5, -11.0, -9.0, 7.0)]
    for (x0, x1, z0, z1) in geh:
        t.append(platte("gehweg", x0, x1, z0, z1, GEH_Y, -0.36, "m3_gehweg"))
        t += fugen_x(x0, x1, z0, z1, 1.0, GEH_Y + 0.001)
        t += fugen_z(x0, x1, z0, z1, 1.0, GEH_Y + 0.001)
    # Bordsteine
    t.append(platte("bord", -24.0, 14.75, 10.0, 10.25, GEH_Y + 0.01, -0.36, "m3_bordstein"))
    t.append(platte("bord", 14.5, 14.75, -19.0, 10.25, GEH_Y + 0.01, -0.36, "m3_bordstein"))
    t.append(platte("gehweg", -24.0, -13.5, 7.0, 10.0, GEH_Y, -0.36, "m3_gehweg"))
    # Strassen
    t.append(platte("strasse", -24.0, 26.0, 10.25, 16.5, STRASSE_Y, -0.38, "m3_asphalt"))
    t.append(platte("strasse", 14.75, 21.0, -19.0, 10.25, STRASSE_Y, -0.38, "m3_asphalt"))
    # gegenueber
    t.append(platte("bord", -24.0, 26.0, 16.5, 16.75, GEH_Y + 0.01, -0.38, "m3_bordstein"))
    t.append(platte("gehweg", -24.0, 26.0, 16.75, 19.0, GEH_Y, -0.38, "m3_gehweg"))
    t.append(platte("bord", 21.0, 21.25, -19.0, 16.5, GEH_Y + 0.01, -0.38, "m3_bordstein"))
    t.append(platte("gehweg", 21.25, 26.0, -19.0, 16.5, GEH_Y, -0.38, "m3_gehweg"))
    my = STRASSE_Y + 0.002
    x = -23.0
    while x < 25.0:
        if not (13.0 < x < 22.5):
            t.append(box("strich", (1.4, 0.004, 0.12), (x, my, 13.37), "m3_markierung"))
        x += 3.0
    z = -18.0
    while z < 9.0:
        if z < 5.5:
            t.append(box("strich", (0.12, 0.004, 1.4), (17.87, my, z), "m3_markierung"))
        z += 3.0
    for i in range(7):
        t.append(box("zebra", (0.42, 0.004, 2.2), (15.35 + i * 0.8, my, 8.2), "m3_markierung"))
        t.append(box("zebra", (2.2, 0.004, 0.42), (12.4, my, 10.75 + i * 0.8), "m3_markierung"))
    # Hof hinten und links (Grund unter den Nachbarhaeusern)
    t.append(platte("hof", -24.0, 14.5, -19.0, -11.5, GEH_Y - 0.005, -0.38, "m3_hof"))
    t.append(platte("hof", -24.0, -13.5, -11.5, 7.0, GEH_Y - 0.005, -0.38, "m3_hof"))
    # Nachbarhaeuser
    t += haus(-23.0, -14.6, -18.5, -12.3, 4.4, "m3_haus_sand", rng, tuer=2)
    t += haus(-11.8, -3.2, -18.0, -12.4, 3.4, "m3_haus_salbei", rng, tuer=1)
    t += haus(0.2, 7.4, -18.5, -12.4, 4.8, "m3_haus_terra", rng, tuer=2)
    t += haus(9.2, 14.2, -18.0, -12.4, 3.0, "m3_haus_blau", rng, tuer=0)
    t += haus(-22.0, -14.4, -10.4, -2.4, 3.8, "m3_haus_gelb", rng, fenster_z=False)
    t += haus(-22.0, -14.4, 0.8, 9.2, 3.2, "m3_haus_grau", rng, fenster_z=True)
    # Baeume und Laternen hinten/links
    for (bx, bz) in ((-1.5, -13.4), (8.3, -13.2), (-13.0, -12.4), (-15.4, -1.0), (15.8, -13.5), (-12.6, 8.4 - 9.0)):
        t += bei(baum(rng, rng.uniform(3.0, 3.8), rng.uniform(0.9, 1.15)), x=bx, y=GEH_Y, z=bz)
    for (lx, lz, d) in ((-12.4, -10.4, 45), (3.5, -10.4, 0), (-12.4, 4.0, 90)):
        t += bei(laterne(), x=lx, y=GEH_Y, z=lz, dreh=d)
    for (bx, bz, r, h) in ((-5.0, -12.9, 0.5, 0.9), (-7.5, -12.9, 0.45, 0.8), (12.0, -12.8, 0.45, 0.8),
                           (-14.0, -6.5, 0.45, 0.9), (-13.9, 10.8, 0.5, 0.9)):
        t += bei(busch(rng, r, h), x=bx, y=GEH_Y, z=bz)
    # M2: Hof in der Ausbuchtung (vorn rechts), Vordach ueber der Ladentuer
    t += hof_flaeche()
    t += bei(vordach(2.4, 1.0), x=6.0, z=-0.4, dreh=180)
    t += bei(aufsteller(), x=4.35, y=GEH_Y, z=1.9, dreh=-20)
    t += bei(kleiderstange(1.3, 7, seed=61), x=4.4, y=GEH_Y, z=3.4, dreh=90)
    t += bei(palette_kartons(62, 2), x=5.3, y=GEH_Y, z=5.6, dreh=8)
    t += bei(palette_kartons(63, 1), x=6.6, y=GEH_Y, z=6.1, dreh=-5)
    t += bei(rollwagen(seed=64), x=6.5, y=GEH_Y, z=4.2, dreh=70)
    # Markisen: links ueber dem Seitenfenster, hinten ueber den Showroom-Fenstern
    t += bei(markise(2.2), x=-10.62, z=3.0, dreh=90)
    t += bei(markise(2.0), x=0.0, z=-8.62, dreh=0)
    t += bei(markise(2.0), x=6.0, z=-8.62, dreh=0)
    # Vorn und rechts: nur Niedriges (<= 1 m)
    for i in range(3):
        t += bei(fahrradbuegel(), x=-6.8 + i * 1.0, y=GEH_Y, z=8.9, dreh=90)
    t += bei(fahrrad("m3_orange"), x=-6.3, y=GEH_Y, z=8.9)
    t += bei(fahrrad("m3_mint"), x=-4.9, y=GEH_Y, z=9.0, dreh=180)
    t += bei(pflanzkasten(1.8, 0.6, rng), x=-10.0, y=GEH_Y, z=7.9)
    t += bei(pflanzkasten(1.8, 0.6, rng), x=5.5, y=GEH_Y, z=7.9)
    t += bei(bank(1.4, 0.45, 0.45, "m3_holz"), x=1.0, y=GEH_Y, z=9.3, dreh=180)
    t += bei(muelltonne("m3_grau"), x=-2.2, y=GEH_Y, z=9.5)
    for px in (-0.2, 2.3, 8.0, 10.0):
        t += bei(poller(), x=px, y=GEH_Y, z=9.75)
    t += bei(hydrant(), x=13.9, y=GEH_Y, z=9.4)
    t += bei(aufsteller(), x=12.3, y=GEH_Y, z=-0.3, dreh=90)
    t += bei(roller(), x=13.7, y=GEH_Y, z=-5.0, dreh=90)
    t += bei(pflanzkasten(1.6, 0.6, rng), x=11.8, y=GEH_Y, z=-7.2, dreh=90)
    t += bei(pflanzkasten(1.6, 0.6, rng), x=11.8, y=GEH_Y, z=3.5, dreh=90)
    for i, hx in enumerate((-18.0, -9.0, 0.0, 9.0, 24.0)):
        t += bei(pflanzkasten(1.6, 0.6, rng), x=hx, y=GEH_Y, z=17.9)
    for hz in (-12.0, -3.0, 6.0):
        t += bei(pflanzkasten(1.6, 0.6, rng), x=23.4, y=GEH_Y, z=hz, dreh=90)
    for i in range(2):
        t += bei(fahrradbuegel(), x=13.6, y=GEH_Y, z=0.9 + i * 1.0)
    t += bei(fahrrad("m3_blau"), x=13.6, y=GEH_Y, z=1.4, dreh=90)
    return t


# ==============================================================================
# ZONENTABELLE, WAENDE, ABLAUF
# ==============================================================================

def _tuer_hinten(x, z_wand):
    return (x, z_wand + 0.5, 1.2, 1.0, "Tuer hinten x=%g" % x)


def _tuer_vorn(x, z_wand):
    return (x, z_wand - 0.5, 1.2, 1.0, "Tuer vorn x=%g" % x)


def _tuer_links(z, x_wand):
    return (x_wand + 0.5, z, 1.0, 1.2, "Tuer links z=%g" % z)


def _tuer_rechts(z, x_wand):
    return (x_wand - 0.5, z, 1.0, 1.2, "Tuer rechts z=%g" % z)


ZONEN = {
    # Stationen, Tueren und Figurenwege nach docs/nacht/karten_welten.md (worlds.json).
    "werkstatt": {
        "breite": 7.0, "tiefe": 7.0, "welt": (0.0, 3.0), "boden": "beton", "bau": einrichtung_werkstatt,
        "frei": [
            (-2.0, -2.35, 2.2, 2.2, "Station intake"),
            (1.8, -2.35, 2.2, 2.2, "Station processing"),
            (0.0, 0.7, 2.2, 2.2, "Station buffer"),
            _tuer_hinten(0.0, -3.5),
            (-0.1, -2.25, 1.6, 2.3, "Laufweg zur Figur"),
        ],
        "ortho": 10.0,
    },
    "laden": {
        "breite": 21.0, "tiefe": 3.0, "welt": (0.0, -2.0), "boden": "terrazzo", "bau": einrichtung_laden,
        "frei": [
            (8.4, 0.0, 2.2, 2.2, "Station transport"),
            (-1.55, 0.2, 17.7, 1.0, "Laufgang"),
            _tuer_hinten(-7.0, -1.5), _tuer_hinten(0.0, -1.5), _tuer_hinten(6.0, -1.5),
            _tuer_vorn(-7.0, 1.5), _tuer_vorn(0.0, 1.5), _tuer_vorn(6.0, 1.5),
        ],
        "ortho": 16.0,
    },
    "lager": {
        "breite": 7.0, "tiefe": 5.0, "welt": (-7.0, -6.0), "boden": "beton", "bau": einrichtung_lager,
        "frei": [_tuer_vorn(0.0, 2.5), (0.0, 1.2, 1.2, 2.6, "Laufweg zur Figur"),
                 (0.0, 1.0, 6.8, 1.0, "Laufweg quer")],
        "ortho": 9.0,
    },
    "showroom": {
        "breite": 7.0, "tiefe": 5.0, "welt": (0.0, -6.0), "boden": "schachbrett", "bau": einrichtung_showroom,
        "frei": [(0.6, 0.0, 2.2, 2.2, "Station special"), _tuer_vorn(0.0, 2.5),
                 (0.0, 1.5, 6.8, 1.0, "Laufweg")],
        "ortho": 9.0,
    },
    "fotostudio": {
        "breite": 7.0, "tiefe": 5.0, "welt": (7.0, -6.0), "boden": "studio", "bau": einrichtung_fotostudio,
        "frei": [_tuer_vorn(-1.0, 2.5), (-0.6, 1.3, 1.4, 2.4, "Laufweg zur Figur"),
                 (0.0, 1.5, 6.8, 1.0, "Laufweg quer")],
        "ortho": 9.0,
    },
    "siebdruck": {
        "breite": 7.0, "tiefe": 7.0, "welt": (-7.0, 3.0), "boden": "farbbeton", "bau": einrichtung_siebdruck,
        "frei": [_tuer_hinten(0.0, -3.5), (-0.1, -1.9, 1.2, 3.0, "Laufweg zur Figur")],
        "ortho": 10.0,
    },
}

# Waende wie in worlds.json (Stand karten_welten.md) -- nur fuer die Vorschau.
WAENDE = [
    {"typ": "voll", "achse": "x", "fest": -8.5, "von": -10.5, "bis": 10.5, "tueren": [], "fenster": [-9, -6, 0, 6, 9]},
    {"typ": "voll", "achse": "z", "fest": -10.5, "von": -8.5, "bis": 6.5, "tueren": [], "fenster": [-6, 3]},
    {"typ": "sockel", "achse": "x", "fest": 6.5, "von": -10.5, "bis": 3.5, "tueren": [], "fenster": [], "drehung": 180},
    {"typ": "sockel", "achse": "z", "fest": 10.5, "von": -8.5, "bis": -0.5, "tueren": [], "fenster": [], "drehung": -90},
    {"typ": "halb", "achse": "x", "fest": -3.5, "von": -10.5, "bis": 10.5, "tueren": [-7, 0, 6], "fenster": []},
    {"typ": "halb", "achse": "x", "fest": -0.5, "von": -10.5, "bis": 3.5, "tueren": [-7, 0], "fenster": []},
    {"typ": "sockel", "achse": "x", "fest": -0.5, "von": 3.5, "bis": 10.5, "tueren": [6], "fenster": [], "drehung": 180},
    {"typ": "halb", "achse": "z", "fest": -3.5, "von": -8.5, "bis": -3.5, "tueren": [], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": 3.5, "von": -8.5, "bis": -3.5, "tueren": [], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": -3.5, "von": -0.5, "bis": 6.5, "tueren": [], "fenster": []},
    {"typ": "sockel", "achse": "z", "fest": 3.5, "von": -0.5, "bis": 6.5, "tueren": [], "fenster": [], "drehung": -90},
]

SATZ = {
    "voll": ["wand_voll", "wand_halb_tuer", "wand_voll_fenster", "pfosten_voll"],
    "halb": ["wand_halb", "wand_halb_tuer", "wand_halb", "pfosten_halb"],
    "sockel": ["wand_sockel", "wand_sockel_tuer", "wand_sockel", "pfosten_sockel"],
}
RANG = {"pfosten_voll": 3, "pfosten_halb": 2, "pfosten_sockel": 1}


def huelle():
    """Wie GrundrissBauer: (modul, x, z, drehung) fuer Waende, Pfosten, Boeden."""
    liste = []
    pfosten = {}
    for w in WAENDE:
        satz = SATZ[w["typ"]]
        achse_x = w["achse"] == "x"
        grad = w.get("drehung", 0.0 if achse_x else 90.0)
        feld = w["von"] + 0.5
        while feld < w["bis"]:
            modul = satz[0]
            if any(abs(t - feld) < 0.01 for t in w["tueren"]):
                modul = satz[1]
            elif any(abs(f - feld) < 0.01 for f in w["fenster"]):
                modul = satz[2]
            x, z = (feld, w["fest"]) if achse_x else (w["fest"], feld)
            liste.append((modul, x, z, grad))
            feld += 1.0
        for ende in (w["von"], w["bis"]):
            p = (ende, w["fest"]) if achse_x else (w["fest"], ende)
            if RANG[satz[3]] > RANG.get(pfosten.get(p, ""), 0):
                pfosten[p] = satz[3]
    for (x, z), modul in pfosten.items():
        liste.append((modul, x, z, 0.0))
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        for i in range(int(zone["breite"])):
            for k in range(int(zone["tiefe"])):
                ix = int(round(wx - zone["breite"] / 2 + 0.5 + i))
                iz = int(round(wz - zone["tiefe"] / 2 + 0.5 + k))
                ab = "a" if (ix + iz) % 2 == 0 else "b"
                liste.append(("boden_%s_%s" % (zone["boden"], ab), ix, iz, 0.0))
    return liste


def pfad(name):
    return os.path.join(AUSGABE, name + ".glb")


def _neu():
    alles_loeschen()
    del wa.MOEBEL[:]
    leucht_materialien()


def zone_bauen(name):
    _neu()
    zone = ZONEN[name]
    zone["bau"]()
    print("")
    print("=== EINRICHTUNG %s (%g x %g) ===" % (name.upper(), zone["breite"], zone["tiefe"]))
    moebel_bericht()
    fehler = freiflaechen_pruefen(zone)
    obj = verbinden([t for _, teile in wa.MOEBEL for t in teile], "einrichtung_%s" % name)
    return _abschluss(obj, "einrichtung_" + name, ZONEN_BUDGET, fehler)


def _abschluss(obj, name, budget, fehler=0):
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    ziel = pfad(name)
    exportieren(obj, ziel)
    print("  -> %s: %d Dreiecke (Budget %d)%s, %d Materialien, %.0f KB"
          % (name, n, budget, "  <-- UEBER BUDGET" if n > budget else "", len(obj.data.materials),
             os.path.getsize(ziel) / 1024.0))
    print("     BBox x %+.2f..%+.2f  y %.2f..%.2f  z %+.2f..%+.2f" % (x0, x1, y0, y1, z0, z1))
    print("     Freiflaechen-/Wandpruefung: %s" % ("OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler))
    ERGEBNIS[name] = n
    return fehler


ERGEBNIS = {}


def aussen_bauen():
    _neu()
    obj = verbinden(umgebung(), "umgebung")
    print("")
    print("=== UMGEBUNG ===")
    _abschluss(obj, "umgebung", UMGEBUNG_BUDGET)
    # Hoehenregel vorn/rechts pruefen: nichts ueber 1 m (ab Gehweg) vor dem Gebaeude.
    hoch = [v.co for v in obj.data.vertices
            if ((-v.co.y > FUND[3] + 0.05 and v.co.x > FUND[0] - 0.05) or
                (v.co.x > FUND[1] + 0.05 and -v.co.y > FUND[2] - 0.05)) and v.co.z > GEH_Y + 1.0 + 0.001]
    print("     Hoehenregel vorn/rechts: %s" % ("OK" if not hoch else "%d Punkte zu hoch" % len(hoch)))
    _neu()
    obj = verbinden(bei(lieferwagen(), y=GEH_Y), "welt_lieferwagen")
    print("=== LIEFERWAGEN ===")
    _abschluss(obj, "welt_lieferwagen", 2500)
    _neu()
    obj = verbinden(fundament(), "fundament")
    print("=== FUNDAMENT ===")
    _abschluss(obj, "fundament", 500)


# --- Vorschau --------------------------------------------------------------------

_VORLAGEN = {}


def instanz(datei, x=0.0, z=0.0, dreh=0.0, y=0.0):
    """Importiert jede Datei nur einmal, danach verknuepfte Kopien (schnell)."""
    vorlage = _VORLAGEN.get(datei)
    m = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh), 4, "Z")
    if vorlage is None:
        vorher = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=datei)
        neu = [o for o in bpy.data.objects if o not in vorher and o.type == "MESH"]
        vorlage = [(o, o.matrix_world.copy()) for o in neu]
        _VORLAGEN[datei] = vorlage
        for o, basis in vorlage:
            o.matrix_world = m @ basis
        return
    for o, basis in vorlage:
        k = o.copy()
        bpy.context.scene.collection.objects.link(k)
        k.matrix_world = m @ basis


def karte_aufstellen(mit_umgebung=True):
    alles_loeschen()
    _VORLAGEN.clear()
    for modul, x, z, dreh in huelle():
        instanz(raum.modul_pfad(modul), x=x, z=z, dreh=dreh)
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        instanz(pfad("einrichtung_" + name), x=wx, z=wz)
    instanz(pfad("fundament"))
    if mit_umgebung:
        instanz(pfad("umgebung"))
        instanz(pfad("welt_lieferwagen"), x=9.4, z=3.9)


def frei_markieren():
    palette_erweitern({"vorschau_frei": ("#46C35A", 0.9, 0.0, 1.0)})
    for zone in ZONEN.values():
        wx, wz = zone["welt"]
        for (fx, fz, fb, ft, was) in zone["frei"]:
            if not was.startswith("Station"):
                continue
            d = 0.05
            for (gx, gz, sb, st) in ((fx, fz - ft / 2 + d / 2, fb, d), (fx, fz + ft / 2 - d / 2, fb, d),
                                     (fx - fb / 2 + d / 2, fz, d, ft), (fx + fb / 2 - d / 2, fz, d, ft)):
                kasten("frei", (sb, 0.006, st), (wx + gx, 0.004, wz + gz), "vorschau_frei")


def vorschau(nur_karte=False):
    karte_aufstellen()
    frei_markieren()
    vorschau_rendern(os.path.join(VORSCHAU, "gesamt_webseiten.png"), (1.5, 0.0, 0.5), 38.0,
                     aufloesung=1600, hintergrund=raum.HINTERGRUND)
    vorschau_rendern(os.path.join(VORSCHAU, "karte_webseiten.png"), (0.0, 0.5, -1.0), 25.0,
                     aufloesung=1600, hintergrund=raum.HINTERGRUND)
    if nur_karte:
        return
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        vorschau_rendern(os.path.join(VORSCHAU, "zone_%s.png" % name), (wx, 0.6, wz), zone["ortho"],
                         aufloesung=1000, hintergrund=raum.HINTERGRUND)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    gewaehlt = [a for a in argumente if a in ZONEN]
    alle = not gewaehlt and "--nur-vorschau" not in argumente
    fehler = 0
    if "--nur-vorschau" not in argumente:
        for name in (gewaehlt or list(ZONEN)):
            fehler += zone_bauen(name)
        if alle or "aussen" in argumente:
            aussen_bauen()
    if "--ohne-vorschau" not in argumente:
        vorschau(nur_karte="--nur-karte" in argumente)
    print("")
    for k, v in ERGEBNIS.items():
        print("  %-30s %6d Dreiecke" % (k, v))
    print("=== FERTIG: %s ===" % ("alle Freiflaechen frei" if fehler == 0 else "%d Verletzungen" % fehler))


if __name__ == "__main__":
    main()
