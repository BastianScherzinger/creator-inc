"""Architektur-Baukasten fuer Welt 2 `auftrag` -- "Das Studio" (Hinterhof mit
umgebauter Garage). docs/NACHT_PLAN.md, Abschnitte 2 und 5 (Asset-Vertrag).

Aufruf:
    blender --background --python art_source/scripts/build_room_auftrag_neu.py
    (optional nach "--": --ohne-vorschau)

Erzeugt nach project/assets/room/auftrag/:
    boden_<typ>_a/_b   typ = beton, pflaster, holz, studio, deck, teppich
                       1 x 1 m, Oberkante y = 0, Unterkante -0,06, EIN Mesh
    wand_voll, wand_voll_fenster, wand_halb, wand_halb_tuer,
    wand_sockel, wand_sockel_tuer, gelaender,
    pfosten_voll, pfosten_halb, pfosten_sockel
                       Masse, Ursprung, Ausrichtung exakt wie wg_* in room/zimmer
                       (Innenseite lokal +z; Hoehen 2,4 / 1,2 / 0,35 / 1,0 m)
    raum_fliese_a, raum_fliese_b, raum_fliese_weg, raum_wand, raum_wand_ecke,
    raum_wand_tuer, raum_wand_fenster
                       einfache Altmodule mit den Massen der Altmodule in room/zimmer
und Uebersichten nach art_source/vorschau/auftrag/.

Stil: Backstein (hell-warm, nicht duester), Betonkappe und Betonsockel,
Stahl in freundlichem Graublau, Akzent Pink #FF4FA3. Alle Farben als sRGB-Hex,
farbe() in build_room_wg.py rechnet linear = s^2,2 zurueck.

KOORDINATEN: wie build_room_wg.py -- alle Funktionen denken in GODOT.
"""

import bpy
import bmesh
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, kugel, profil_x, rundprofil, kissen_platte,
    transformieren, alles_loeschen, verbinden, dreiecke, masse, exportieren,
    importieren, vorschau_rendern, palette_erweitern, _objekt,
    WURZEL,
)

AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "auftrag")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "auftrag")

# Namen mit Vorsilbe "s_", damit sie sich nicht mit der WG-Palette mischen.
palette_erweitern({
    # Mauerwerk
    "s_ziegel":        ("#B05A42", 0.90, 0.0, 1.0),
    "s_ziegel_2":      ("#9E4C38", 0.90, 0.0, 1.0),
    "s_ziegel_3":      ("#C26D4E", 0.90, 0.0, 1.0),
    "s_moertel":       ("#CDBBA6", 0.95, 0.0, 1.0),
    "s_beton_kappe":   ("#B9B2A8", 0.85, 0.0, 1.0),
    "s_beton_sockel":  ("#8E877D", 0.90, 0.0, 1.0),
    # Stahl, Glas, Akzent
    "s_stahl":         ("#4A5468", 0.45, 0.35, 1.0),
    "s_stahl_hell":    ("#AEB6C2", 0.40, 0.40, 1.0),
    "s_glas":          ("#BFE6F5", 0.20, 0.0, 1.0),
    "s_pink":          ("#FF4FA3", 0.55, 0.0, 1.0),
    "s_pink_dunkel":   ("#D93A87", 0.60, 0.0, 1.0),
    # Boeden
    "s_beton_a":       ("#D4CDC2", 0.80, 0.0, 1.0),
    "s_beton_b":       ("#CCC4B8", 0.80, 0.0, 1.0),
    "s_beton_fleck":   ("#CBC3B7", 0.85, 0.0, 1.0),
    "s_beton_fuge":    ("#A69E93", 0.95, 0.0, 1.0),
    "s_pflaster_a":    ("#C9BFB2", 0.90, 0.0, 1.0),
    "s_pflaster_b":    ("#BBB0A2", 0.90, 0.0, 1.0),
    "s_pflaster_c":    ("#D6CCBE", 0.90, 0.0, 1.0),
    "s_pflaster_d":    ("#C2A99A", 0.90, 0.0, 1.0),
    "s_pflaster_fuge": ("#8F877D", 0.95, 0.0, 1.0),
    "s_holz_a":        ("#DDA874", 0.80, 0.0, 1.0),
    "s_holz_b":        ("#D29C66", 0.80, 0.0, 1.0),
    "s_holz_c":        ("#DCA875", 0.80, 0.0, 1.0),
    "s_holz_d":        ("#D09A63", 0.80, 0.0, 1.0),
    "s_holz_fuge":     ("#A06F45", 0.90, 0.0, 1.0),
    "s_studio_a":      ("#E3E0DA", 0.60, 0.0, 1.0),
    "s_studio_b":      ("#D9D5CE", 0.60, 0.0, 1.0),
    "s_studio_fuge":   ("#BDB8B0", 0.90, 0.0, 1.0),
    "s_deck_a":        ("#B98459", 0.85, 0.0, 1.0),
    "s_deck_b":        ("#AD7A51", 0.85, 0.0, 1.0),
    "s_deck_fuge":     ("#6E5039", 0.95, 0.0, 1.0),
    "s_teppich":       ("#C0587E", 0.95, 0.0, 1.0),
    "s_teppich_2":     ("#D4739A", 0.95, 0.0, 1.0),
    "s_teppich_fuge":  ("#9E4467", 0.95, 0.0, 1.0),
    "s_tuer_pink":     "s_pink",
    "s_tuer_stahl":    ("#5E6A7C", 0.50, 0.30, 1.0),
    "s_tuer_stahl_dunkel": ("#4B5666", 0.55, 0.30, 1.0),
})


# --- Kleine Geometrie-Helfer ---------------------------------------------------

def flaeche(name, x0, x1, y0, y1, z, mat, nach_vorn=True):
    """Ein einzelnes Rechteck in der Ebene z = const (Godot), Normale +z oder -z.
    Fuer Moertelfugen und Ziegelflecken: 2 Dreiecke statt 12."""
    bm = bmesh.new()
    pk = [bm.verts.new(G(x, y, z)) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    f = bm.faces.new(pk)
    bm.normal_update()
    # Godot +z = Blender -y
    soll = -1.0 if nach_vorn else 1.0
    if f.normal.y * soll < 0:
        f.normal_flip()
    return _objekt(name, bm, mat)


def deckflaeche(name, x0, x1, z0, z1, y, mat):
    """Waagrechtes Rechteck bei Hoehe y, Normale nach oben."""
    bm = bmesh.new()
    pk = [bm.verts.new(G(x, y, z)) for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
    f = bm.faces.new(pk)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat)


# ==============================================================================
# BODENMODULE
# ==============================================================================

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def boden_beton(variante):
    """Geschliffener Estrich: eine grosse Platte mit feiner Fase (die
    Scheinfuge im Meterraster ist bei Beton echt und darf man sehen), dazu
    zwei, drei flache Flecken als Gebrauchsspuren."""
    haupt = "s_beton_a" if variante == "a" else "s_beton_b"
    teile = [_tragplatte("s_beton_fuge", -0.004),
             kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.008, haupt)]
    rng = random.Random(11 if variante == "a" else 12)
    for _ in range(2 if variante == "a" else 3):
        cx, cz = rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3)
        b, t = rng.uniform(0.12, 0.26), rng.uniform(0.08, 0.2)
        bm = bmesh.new()
        pk = [bm.verts.new(G(cx + b / 2 * math.cos(w) * rng.uniform(0.7, 1.1), 0.0006,
                             cz + t / 2 * math.sin(w) * rng.uniform(0.7, 1.1)))
              for w in [k * math.pi / 3 for k in range(6)]]
        f = bm.faces.new(pk)
        bm.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        teile.append(_objekt("fleck", bm, "s_beton_fleck"))
    return teile


def boden_pflaster(variante):
    """Rechteckpflaster im Laeuferverband: 4 Reihen, Steine 0,25 x 0,5 bzw.
    halbe Steine an den Modulraendern, damit der Verband ueber die Fuge
    weiterlaeuft. Toene gestreut, b spiegelt die Tonfolge."""
    teile = [_tragplatte("s_pflaster_fuge", -0.012)]
    toene = ["s_pflaster_a", "s_pflaster_b", "s_pflaster_c", "s_pflaster_a", "s_pflaster_d",
             "s_pflaster_c", "s_pflaster_b", "s_pflaster_a", "s_pflaster_c", "s_pflaster_b",
             "s_pflaster_a", "s_pflaster_d"]
    if variante == "b":
        toene = toene[5:] + toene[:5]
    k = 0
    for r in range(4):
        z0 = -0.5 + r * 0.25
        stoesse = [-0.5, 0.0, 0.5] if r % 2 == 0 else [-0.5, -0.25, 0.25, 0.5]
        for i in range(len(stoesse) - 1):
            teile.append(kissen_platte("stein", stoesse[i], stoesse[i + 1], z0, z0 + 0.25,
                                       0.0, -0.012, 0.022, toene[k % len(toene)]))
            k += 1
    return teile


def _dielen(reihen, fuge_mat, fase=0.006):
    teile = [_tragplatte(fuge_mat, -0.008)]
    z = -0.5
    for breite, stuecke in reihen:
        for x0, x1, mat in stuecke:
            teile.append(kissen_platte("diele", x0, x1, z, z + breite, 0.0, -0.008, fase, mat))
        z += breite
    return teile


def boden_holz(variante):
    """Breite Eichendielen (4 Reihen), Regel wie WG: a hat (t1|t2), b (t2|t1),
    im Schachbrett laufen die Dielen ueber die Modulgrenze durch."""
    toene = [("s_holz_a", "s_holz_b"), ("s_holz_c", "s_holz_a"),
             ("s_holz_d", "s_holz_c"), ("s_holz_b", "s_holz_d")]
    fa = (-0.18, 0.22, -0.32, 0.08)
    fb = (0.3, -0.12, 0.18, -0.28)
    reihen = []
    for (t1, t2), a, b in zip(toene, fa, fb):
        if variante == "a":
            reihen.append((0.25, [(-0.5, a, t1), (a, 0.5, t2)]))
        else:
            reihen.append((0.25, [(-0.5, b, t2), (b, 0.5, t1)]))
    return _dielen(reihen, "s_holz_fuge")


def boden_studio(variante):
    """Studioboden: helle, matte Kunststoffplatten 0,5 x 0,5."""
    teile = [_tragplatte("s_studio_fuge", -0.005)]
    dunkler = {(1, 0)} if variante == "a" else {(0, 1)}
    for i in range(2):
        for k in range(2):
            x0, z0 = -0.5 + i * 0.5, -0.5 + k * 0.5
            teile.append(kissen_platte("platte", x0, x0 + 0.5, z0, z0 + 0.5, 0.0, -0.005, 0.01,
                                       "s_studio_b" if (i, k) in dunkler else "s_studio_a"))
    return teile


def boden_deck(variante):
    """Dachterrasse: fuenf helle Bretter mit sichtbaren Spalten (anders als
    innen) -- die Spalte sind das Erkennungszeichen eines Decks."""
    teile = [_tragplatte("s_deck_fuge", -0.03)]
    breite = 0.2
    for i in range(5):
        z0 = -0.5 + i * breite + 0.012
        z1 = -0.5 + (i + 1) * breite - 0.012
        gerade = (i % 2 == 0) if variante == "a" else (i % 2 == 1)
        teile.append(kasten("brett", (1.0, 0.03, z1 - z0), (0.0, -0.015, (z0 + z1) / 2.0),
                            "s_deck_a" if gerade else "s_deck_b", unten=False))
    return teile


def boden_teppich(variante):
    """Kinoteppich: Himbeer-Grund mit kleinem Rautenmuster in hellem Rosa.
    Die Rauten sitzen im Halbmeter-Raster, a und b versetzt -- im
    Schachbrett entsteht ein ruhiges Streumuster statt eines Gitters."""
    teile = [_tragplatte("s_teppich_fuge", -0.002),
             kissen_platte("flor", -0.5, 0.5, -0.5, 0.5, 0.0, -0.002, 0.002, "s_teppich")]
    punkte = ((-0.25, -0.25), (0.25, 0.25)) if variante == "a" else ((0.25, -0.25), (-0.25, 0.25))
    for (cx, cz) in punkte:
        bm = bmesh.new()
        r = 0.1
        pk = [bm.verts.new(G(cx + dx, 0.0008, cz + dz)) for (dx, dz) in ((0, -r), (r, 0), (0, r), (-r, 0))]
        f = bm.faces.new(pk)
        bm.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        teile.append(_objekt("raute", bm, "s_teppich_2"))
    return teile


# ==============================================================================
# WANDMODULE -- Backstein
# ==============================================================================

WAND_DICKE = 0.20
KAPPE_DICKE = 0.24
KAPPE_HOEHE = 0.06
SOCKEL_DICKE = 0.22
HOEHE = {"voll": 2.4, "halb": 1.2, "sockel": 0.35}
TUER_HOEHE = 2.05
TUER_PFOSTEN_X = 0.45
TUER_PFOSTEN_B = 0.10
TUER_TIEFE = 0.26
REIHE = 0.16          # Ziegelschicht inklusive Fuge
FUGE = 0.016


def _sockelhoehe(hoehe):
    return min(0.10, hoehe * 0.22)


def _koerper(x0, x1, y0, y1):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, "s_ziegel")


def _kappe(hoehe, x0=-0.5, x1=0.5):
    d = KAPPE_DICKE / 2.0
    return profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.02),
                    x0, x1, "s_beton_kappe")


def _betonsockel(hoehe, x0=-0.5, x1=0.5):
    d = SOCKEL_DICKE / 2.0
    return profil_x("sockel", rundprofil(-d, d, 0.0, _sockelhoehe(hoehe), 0.01, 1), x0, x1, "s_beton_sockel")


def _ziegelbild(felder, hoehe, seiten=(1, -1), saat=1):
    """Moertelfugen und einzelne Farbziegel auf den Wandflaechen.
    felder: Liste massiver Rechtecke (x0, x1, y0, y1) -- Fugen nur dort.
    Laeuferverband: Ziegel 0,5 lang, Stossfugen je Schicht um 0,25 versetzt."""
    teile = []
    rng = random.Random(saat)
    d = WAND_DICKE / 2.0 + 0.0015
    y_start = _sockelhoehe(hoehe)
    y_ende = hoehe - KAPPE_HOEHE
    for s in seiten:
        vorn = s > 0
        for (fx0, fx1, fy0, fy1) in felder:
            y0 = max(fy0, y_start)
            y1 = min(fy1, y_ende)
            if y1 - y0 < 0.05:
                continue
            reihe = 0
            y = y_start
            while y < y_ende - 0.02:
                oben = y + REIHE
                # Lagerfuge an der Oberkante der Schicht
                if y0 < oben - FUGE / 2 < y1 and oben < y_ende - 0.03:
                    teile.append(flaeche("lagerfuge", fx0, fx1, oben - FUGE, oben, s * d, "s_moertel", vorn))
                # Stossfugen
                ys0, ys1 = max(y, y0), min(oben - FUGE, y1)
                if ys1 - ys0 > 0.03:
                    stoesse = (0.0,) if reihe % 2 == 0 else (-0.25, 0.25)
                    for sx in stoesse:
                        if fx0 + 0.02 < sx < fx1 - 0.02:
                            teile.append(flaeche("stossfuge", sx - FUGE / 2, sx + FUGE / 2, ys0, ys1,
                                                 s * d, "s_moertel", vorn))
                    # Farbziegel: gelegentlich ein hellerer oder dunklerer Stein
                    if rng.random() < 0.34:
                        kante = (-0.5, 0.0, 0.5) if reihe % 2 == 0 else (-0.25, 0.25)
                        i = rng.randrange(len(kante) - 1) if len(kante) > 2 else 0
                        bx0 = kante[i] + FUGE / 2
                        bx1 = (kante[i + 1] if len(kante) > 2 else 0.25) - FUGE / 2
                        bx0, bx1 = max(bx0, fx0), min(bx1, fx1)
                        if bx1 - bx0 > 0.1:
                            teile.append(flaeche("farbziegel", bx0, bx1, ys0, ys1, s * (d + 0.0005),
                                                 rng.choice(("s_ziegel_2", "s_ziegel_3")), vorn))
                y = oben
                reihe += 1
    return teile


def _wand(hoehe, saat):
    teile = [_koerper(-0.5, 0.5, 0.0, hoehe - KAPPE_HOEHE + 0.001),
             _kappe(hoehe), _betonsockel(hoehe)]
    teile += _ziegelbild([(-0.5, 0.5, 0.0, hoehe)], hoehe, saat=saat)
    return teile


def wand_voll():
    return _wand(HOEHE["voll"], 3)


def wand_halb():
    return _wand(HOEHE["halb"], 5)


def wand_sockel():
    # Der Sockel ist so niedrig, dass eine Ziegelzeichnung nur flimmert:
    # zwei Schichten reichen.
    return _wand(HOEHE["sockel"], 7)


def wand_voll_fenster():
    """Industriefenster: Stahlrahmen mit 3 x 3 Sprossenfeldern, Oeffnung
    0,84 breit von 0,8 bis 2,1 m, Betonsturz aussen angedeutet, Betonbank innen
    (lokal +z), wie bei der WG tief genug fuer einen Topf."""
    h = HOEHE["voll"]
    ox, u, o = 0.42, 0.80, 2.10
    teile = [
        _koerper(-0.5, 0.5, 0.0, u),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _koerper(-0.5, -ox, u, o),
        _koerper(ox, 0.5, u, o),
        _kappe(h), _betonsockel(h),
    ]
    teile += _ziegelbild([(-0.5, 0.5, 0.0, u), (-0.5, 0.5, o + 0.08, h), (-0.5, -ox, u, o), (ox, 0.5, u, o)],
                         h, saat=9)
    # Sturz: Rollschicht als Betonband ueber dem Fenster, beidseitig
    for s in (1, -1):
        teile.append(kasten("sturz", (2 * ox + 0.12, 0.08, 0.012), (0.0, o + 0.04, s * (WAND_DICKE / 2 + 0.006)),
                            "s_beton_kappe"))
    r = 0.05
    t = 0.10
    innen_b = 2 * ox - 2 * r
    innen_h = o - u - 2 * r
    teile.append(kasten("rahmen_l", (r, o - u, t), (-ox + r / 2, (u + o) / 2, 0.0), "s_stahl"))
    teile.append(kasten("rahmen_r", (r, o - u, t), (ox - r / 2, (u + o) / 2, 0.0), "s_stahl"))
    teile.append(kasten("rahmen_o", (innen_b, r, t), (0.0, o - r / 2, 0.0), "s_stahl"))
    teile.append(kasten("rahmen_u", (innen_b, r, t), (0.0, u + r / 2, 0.0), "s_stahl"))
    for i in (1, 2):
        teile.append(kasten("sprosse_v", (0.025, innen_h, 0.05),
                            (-innen_b / 2 + i * innen_b / 3, (u + o) / 2, 0.0), "s_stahl"))
        teile.append(kasten("sprosse_h", (innen_b, 0.025, 0.05),
                            (0.0, u + r + i * innen_h / 3, 0.0), "s_stahl"))
    teile.append(kasten("glas", (innen_b, innen_h, 0.016), (0.0, (u + o) / 2, 0.0), "s_glas"))
    # ein Kippfluegel in Pink -- der Akzent der Welt, sparsam
    teile.append(kasten("fluegel", (innen_b / 3 - 0.02, 0.02, 0.03),
                        (0.0, u + r + innen_h * 2 / 3 + 0.012, 0.035), "s_stahl_hell"))
    teile.append(kasten("fensterbank", (0.96, 0.05, 0.36), (0.0, u - 0.025, 0.05),
                        "s_beton_kappe", rund=0.012, segmente=1))
    return teile


def _tuerrahmen():
    """Stahlzarge wie die WG-Zarge (Pfosten +-0,45, 2,05 hoch), dazu ein
    schmaler pinker Leuchtstreifen an der Innenseite des Sturzes."""
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1, t), (s * TUER_PFOSTEN_X, (h - 0.1) / 2, 0.0),
                            "s_stahl", rund=0.012, segmente=1))
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.1, t - 0.012), (0.0, h - 0.05, 0.0),
                        "s_stahl", rund=0.015, segmente=1))
    teile.append(kasten("leuchtstreifen", (0.6, 0.03, 0.012), (0.0, h - 0.05, t / 2 - 0.006), "s_pink"))
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "s_stahl_hell", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Hoftuer: pinkes Stahlblatt mit Sichtfenster und Quersicken, halb
    offen nach AUSSEN (lokal -z), Scharnier links, 105 Grad -- gleiche
    Geometrie wie die WG-Wohnungstuer."""
    teile = _tuerrahmen()
    bb, bh, bd = 0.78, 1.93, 0.045
    blatt = [
        kasten("tuerblatt", (bb, bh, bd), (bb / 2, bh / 2 + 0.012, 0.0), "s_tuer_stahl", rund=0.01, segmente=1),
    ]
    for seite in (-1, 1):
        blatt.append(kasten("fenster", (0.34, 0.42, 0.01), (bb / 2, 1.45, seite * (bd / 2 + 0.003)), "s_glas"))
        for y in (0.35, 0.6, 0.85):
            blatt.append(kasten("sicke", (0.6, 0.035, 0.01), (bb / 2, y, seite * (bd / 2 + 0.003)), "s_tuer_stahl_dunkel"))
        blatt.append(kasten("griff", (0.14, 0.03, 0.03), (bb - 0.14, 1.0, seite * (bd / 2 + 0.05)), "s_stahl_hell"))
        blatt.append(kasten("griffhals", (0.025, 0.025, 0.04), (bb - 0.08, 1.0, seite * (bd / 2 + 0.02)), "s_stahl_hell"))
    transformieren(blatt, x=-TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    return teile + blatt


def gelaender():
    """Dachgelaender: Stahlhandlauf auf 1,0 m, drei Querstaebe, je Modul
    ein Flachstahl-Pfosten -- so laeuft der Rhythmus nahtlos weiter."""
    teile = [
        profil_x("handlauf", rundprofil(-0.035, 0.035, 0.95, 1.0, 0.02), -0.5, 0.5, "s_stahl"),
        kasten("unterholm", (1.0, 0.035, 0.04), (0.0, 0.10, 0.0), "s_stahl"),
    ]
    for y in (0.37, 0.62):
        teile.append(kasten("querstab", (1.0, 0.018, 0.018), (0.0, y, 0.0), "s_stahl_hell"))
    teile.append(kasten("pfosten", (0.05, 0.85, 0.05), (-0.25, 0.525, 0.0), "s_stahl"))
    return teile


def _pfosten(hoehe):
    sh = _sockelhoehe(hoehe)
    teile = [
        kasten("saeule", (0.22, hoehe - KAPPE_HOEHE + 0.002, 0.22),
               (0.0, (hoehe - KAPPE_HOEHE) / 2 + 0.001, 0.0), "s_ziegel", unten=False),
        kasten("saeule_kappe", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "s_beton_kappe", rund=0.018, segmente=1),
        kasten("saeule_sockel", (0.24, sh, 0.24), (0.0, sh / 2, 0.0), "s_beton_sockel", unten=False),
    ]
    # Lagerfugen rundum
    y = sh + REIHE
    while y < hoehe - KAPPE_HOEHE - 0.03:
        teile.append(kasten("fuge", (0.224, FUGE, 0.224), (0.0, y - FUGE / 2, 0.0), "s_moertel", unten=False))
        y += REIHE
    return teile


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


# ==============================================================================
# ALTMODULE (validate Schritt 7) -- einfache Varianten, Masse wie room/zimmer
# ==============================================================================

def raum_fliese(mat):
    return [kasten("fliese", (0.98, 0.026, 0.996), (0.0, 0.0, 0.0), mat)]


def raum_wand():
    return [kasten("wand", (1.0, 2.14, 0.2), (0.0, 1.07, 0.0), "s_ziegel"),
            kasten("kappe", (1.0, 0.06, 0.2), (0.0, 2.17, 0.0), "s_beton_kappe")]


def raum_wand_ecke():
    return raum_wand() + [
        kasten("wand_quer", (0.2, 2.14, 1.03), (0.43, 1.07, 0.415), "s_ziegel"),
        kasten("kappe_quer", (0.2, 0.06, 1.03), (0.43, 2.17, 0.415), "s_beton_kappe"),
    ]


def raum_wand_tuer():
    return [
        kasten("wand_l", (0.5, 2.14, 0.2), (-0.75, 1.07, 0.0), "s_ziegel"),
        kasten("wand_r", (0.5, 2.14, 0.2), (0.75, 1.07, 0.0), "s_ziegel"),
        kasten("sturz", (1.0, 0.14, 0.2), (0.0, 2.07, 0.0), "s_ziegel"),
        kasten("kappe", (2.0, 0.06, 0.2), (0.0, 2.17, 0.0), "s_beton_kappe"),
        kasten("zarge_l", (0.06, 2.0, 0.2), (-0.47, 1.0, 0.0), "s_stahl"),
        kasten("zarge_r", (0.06, 2.0, 0.2), (0.47, 1.0, 0.0), "s_stahl"),
    ]


def raum_wand_fenster():
    return [
        kasten("unten", (1.0, 0.9, 0.2), (0.0, 0.45, 0.0), "s_ziegel"),
        kasten("oben", (1.0, 0.3, 0.2), (0.0, 2.05, 0.0), "s_ziegel"),
        kasten("rahmen_l", (0.1, 1.0, 0.26), (-0.45, 1.4, 0.0), "s_stahl"),
        kasten("rahmen_r", (0.1, 1.0, 0.26), (0.45, 1.4, 0.0), "s_stahl"),
        kasten("glas", (0.8, 1.0, 0.02), (0.0, 1.4, 0.0), "s_glas"),
    ]


MODULE = {
    "boden_beton_a": lambda: boden_beton("a"),
    "boden_beton_b": lambda: boden_beton("b"),
    "boden_pflaster_a": lambda: boden_pflaster("a"),
    "boden_pflaster_b": lambda: boden_pflaster("b"),
    "boden_holz_a": lambda: boden_holz("a"),
    "boden_holz_b": lambda: boden_holz("b"),
    "boden_studio_a": lambda: boden_studio("a"),
    "boden_studio_b": lambda: boden_studio("b"),
    "boden_deck_a": lambda: boden_deck("a"),
    "boden_deck_b": lambda: boden_deck("b"),
    "boden_teppich_a": lambda: boden_teppich("a"),
    "boden_teppich_b": lambda: boden_teppich("b"),
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
    "raum_fliese_a": lambda: raum_fliese("s_beton_a"),
    "raum_fliese_b": lambda: raum_fliese("s_beton_b"),
    "raum_fliese_weg": lambda: raum_fliese("s_pflaster_a"),
    "raum_wand": raum_wand,
    "raum_wand_ecke": raum_wand_ecke,
    "raum_wand_tuer": raum_wand_tuer,
    "raum_wand_fenster": raum_wand_fenster,
}

# Soll-Bounding-Boxen (Godot) aus den wg_*-Modulen in room/zimmer,
# per Skript ausgelesen. Die Pruefung unten vergleicht darauf (Toleranz 1 cm).
SOLL = {
    "boden":             ((-0.5, 0.5), (-0.06, 0.0), (-0.5, 0.5)),
    "wand_voll":         ((-0.5, 0.5), (0.0, 2.4), (-0.12, 0.12)),
    "wand_voll_fenster": ((-0.5, 0.5), (0.0, 2.4), (-0.13, 0.23)),
    "wand_halb":         ((-0.5, 0.5), (0.0, 1.2), (-0.12, 0.12)),
    "wand_halb_tuer":    ((-0.5, 0.5), (0.0, 2.05), (-0.13, 0.13)),
    "wand_sockel":       ((-0.5, 0.5), (0.0, 0.35), (-0.12, 0.12)),
    "wand_sockel_tuer":  ((-0.663, 0.5), (0.0, 2.05), (-0.876, 0.13)),
    "gelaender":         ((-0.5, 0.5), (0.083, 1.0), (-0.035, 0.035)),
    "pfosten_voll":      ((-0.135, 0.135), (0.0, 2.4), (-0.135, 0.135)),
    "pfosten_halb":      ((-0.135, 0.135), (0.0, 1.2), (-0.135, 0.135)),
    "pfosten_sockel":    ((-0.135, 0.135), (0.0, 0.35), (-0.135, 0.135)),
    "raum_fliese_a":     ((-0.49, 0.49), (-0.013, 0.013), (-0.498, 0.498)),
    "raum_fliese_b":     ((-0.49, 0.49), (-0.013, 0.013), (-0.498, 0.498)),
    "raum_fliese_weg":   ((-0.49, 0.49), (-0.013, 0.013), (-0.498, 0.498)),
    "raum_wand":         ((-0.5, 0.5), (0.0, 2.2), (-0.1, 0.1)),
    "raum_wand_ecke":    ((-0.5, 0.53), (0.0, 2.2), (-0.1, 0.93)),
    "raum_wand_tuer":    ((-1.0, 1.0), (0.0, 2.2), (-0.1, 0.1)),
    "raum_wand_fenster": ((-0.5, 0.5), (0.0, 2.2), (-0.13, 0.13)),
}


def modul_pfad(name):
    return os.path.join(AUSGABE_MODULE, name + ".glb")


def _soll(name):
    return SOLL["boden"] if name.startswith("boden_") else SOLL[name]


def module_bauen():
    print("")
    print("=== MODULE WELT 2 (auftrag) ===")
    abweichungen = 0
    for name, bauen in MODULE.items():
        alles_loeschen()
        obj = verbinden(bauen(), name)
        pfad = modul_pfad(name)
        exportieren(obj, pfad)
        ist = masse(obj)
        soll = _soll(name)
        fehl = [a for a in range(3) for k in range(2) if abs(ist[a][k] - soll[a][k]) > 0.012]
        abweichungen += 1 if fehl else 0
        (x0, x1), (y0, y1), (z0, z1) = ist
        print("  %-20s %4d Dreiecke  x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f  %2d Mat  %5.1f KB  %s"
              % (name, dreiecke(obj), x0, x1, y0, y1, z0, z1, len(obj.data.materials),
                 os.path.getsize(pfad) / 1024.0,
                 "OK" if not fehl else "MASSE WEICHEN AB (Achsen %s)" % sorted(set(fehl))))
    print("  Massabgleich mit room/zimmer: %s" % ("alle OK" if not abweichungen else "%d ABWEICHUNGEN" % abweichungen))


def module_vorschau():
    alles_loeschen()
    typen = [n[:-2] for n in MODULE if n.startswith("boden_") and n.endswith("_a")]
    for i, typ in enumerate(typen):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                # Schachbrett a/b wie im Spiel
                ab = "a" if (dx + dz) % 2 == 0 else "b"
                importieren(modul_pfad(typ + "_" + ab), x=(i % 3) * 3.4 + dx, z=(i // 3) * 3.4 + dz)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (3.4, 0.0, 1.7), 10.0)

    alles_loeschen()
    zeilen = [
        ("wand_voll", "wand_voll_fenster", "pfosten_voll"),
        ("wand_halb", "wand_halb_tuer", "pfosten_halb"),
        ("wand_sockel", "wand_sockel_tuer", "pfosten_sockel"),
    ]
    for r, (wand, sonder, pfosten) in enumerate(zeilen):
        z = r * 3.0
        for dx, modul in ((0, wand), (1, sonder), (2, wand)):
            importieren(modul_pfad(modul), x=dx, z=z)
        importieren(modul_pfad(pfosten), x=-0.5, z=z)
        importieren(modul_pfad(wand), x=-0.5, z=z + 0.5, dreh_grad=90.0)
        importieren(modul_pfad(wand), x=-0.5, z=z + 1.5, dreh_grad=90.0)
        importieren(modul_pfad("boden_beton_a"), x=0, z=z + 1)
        importieren(modul_pfad("boden_beton_b"), x=1, z=z + 1)
        importieren(modul_pfad("boden_beton_a"), x=2, z=z + 1)
    for dx in range(3):
        importieren(modul_pfad("gelaender"), x=4.5 + dx, z=0.0)
        importieren(modul_pfad("boden_deck_" + ("a" if dx % 2 == 0 else "b")), x=4.5 + dx, z=0.5)
    for i, name in enumerate(("raum_wand", "raum_wand_ecke", "raum_wand_tuer", "raum_wand_fenster")):
        importieren(modul_pfad(name), x=5.0 + (i % 2) * 2.5, z=3.0 + (i // 2) * 2.5)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_waende.png"), (3.5, 0.8, 3.4), 11.0)


if __name__ == "__main__":
    module_bauen()
    if "--ohne-vorschau" not in sys.argv:
        module_vorschau()
