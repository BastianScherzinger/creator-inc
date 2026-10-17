"""Architektur-Baukasten fuer Welt 5 (alte Fabrikhalle), Nachtplan N40
(docs/NACHT_PLAN.md Abschnitte 2 und 5).

Aufruf:
    blender --background --python art_source/scripts/build_room_produkt_neu.py
    (optional nach "--": --ohne-vorschau)

Erzeugt nach project/assets/room/produkt/:
    boden_<typ>_a/_b   Bodenmodule 1 x 1 m, Oberkante y = 0, 0,06 dick nach unten
                       typ = hallenboden, gitterrost, beton, teppich, deck, fliese
    wand_*             Wandsegmente 1 m entlang lokal X, Ursprung unten Mitte,
                       Innenseite lokal +z (Masse wie wg_wand_* in room/zimmer)
    gelaender          Stahlgelaender 1 m
    pfosten_*          Stahlstuetzen 0,22 x 0,22 (Kappe 0,27)
    raum_*             die sieben Altmodule fuer validate Schritt 7
und Uebersichten nach art_source/vorschau/produkt/.

Stil: roter Backstein mit hellen Fugen, dunkle Stahlkappen mit einem feinen
violetten Lichtband, Industriefenster mit Sprossen. Kuehl-violett, aber hell.

Jede Datei enthaelt GENAU EIN Mesh (MultiMesh-tauglich, siehe build_room_wg.py).
KOORDINATEN: alle Funktionen nehmen GODOT-Koordinaten (siehe build_room_wg.py).
"""

import bpy
import bmesh
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_room_wg as rw  # noqa: E402
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, profil_x, rundprofil, kissen_platte, transformieren,
    alles_loeschen, verbinden, dreiecke, masse, exportieren, importieren,
    palette_erweitern, _objekt, WURZEL,
)

AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "produkt")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "produkt")
HINTERGRUND = "#DCD8EC"

# Toene der Fabrikhalle. Namen nach Stoff und Ton, mit Endung _f (Farm),
# damit nichts mit anderen Paletten zusammenstoesst.
palette_erweitern({
    "ziegel_f":        ("#7A463C", 0.90, 0.0, 1.0),
    "ziegel_d_f":      ("#653A32", 0.90, 0.0, 1.0),
    "fuge_f":          ("#8E7A6E", 0.95, 0.0, 1.0),
    "kappe_f":         ("#3E3A57", 0.50, 0.30, 1.0),
    "sockel_f":        ("#4E5060", 0.80, 0.0, 1.0),
    "rahmen_f":        ("#34364A", 0.45, 0.35, 1.0),
    "glas_f":          ("#3A4C74", 0.12, 0.0, 1.0),
    "stahl_f":         ("#555C7C", 0.45, 0.40, 1.0),
    "stahl_hell_f":    ("#A7AEC0", 0.40, 0.50, 1.0),
    "violett_f":       ("#8B5CF6", 0.45, 0.0, 1.0),
    "led_violett_f":   ("#A78BFA", 0.40, 0.0, 1.0),
    "led_cyan_f":      ("#5EE6F0", 0.40, 0.0, 1.0),
    "warn_gelb_f":     ("#FFC21A", 0.60, 0.0, 1.0),
    "warn_dunkel_f":   ("#2B2A36", 0.60, 0.0, 1.0),
    "halle_f":         ("#4B505D", 0.55, 0.0, 1.0),
    "halle_fuge_f":    ("#343844", 0.80, 0.0, 1.0),
    "halle_fleck_d_f": ("#41454F", 0.60, 0.0, 1.0),
    "halle_fleck_h_f": ("#5A5F6D", 0.50, 0.0, 1.0),
    "rost_wanne_f":    ("#3A3C4E", 0.80, 0.10, 1.0),
    "rost_stab_f":     ("#A3AABB", 0.40, 0.55, 1.0),
    "beton_f":         ("#5A5D68", 0.90, 0.0, 1.0),
    "beton_fleck_f":   ("#2E3038", 0.90, 0.0, 1.0),
    "beton_hell_f":    ("#666A76", 0.90, 0.0, 1.0),
    "beton_fuge_f":    ("#3A3C45", 0.95, 0.0, 1.0),
    "teppich_f":       ("#3E4353", 0.95, 0.0, 1.0),
    "teppich2_f":      ("#4A5063", 0.95, 0.0, 1.0),
    "teppich_fuge_f":  ("#252833", 0.95, 0.0, 1.0),
    "deck_f":          ("#1F3158", 0.22, 0.35, 1.0),
    "deck2_f":         ("#263B68", 0.22, 0.35, 1.0),
    "deck_fuge_f":     ("#9AA3B8", 0.95, 0.0, 1.0),
    "fliese_f":        ("#CDD0D6", 0.45, 0.0, 1.0),
    "fliese2_f":       ("#BAC6D4", 0.45, 0.0, 1.0),
    "fliese_fuge_f":   ("#9EA4B0", 0.90, 0.0, 1.0),
    "tuer_f":          ("#3E4256", 0.55, 0.0, 1.0),
    "led_boden_f":     ("#8B5CF6", 0.45, 0.0, 1.0),
    "led_warm_f":      ("#FFB347", 0.45, 0.0, 1.0),
})

# Leuchtende Toene: Emission wird beim Anlegen des Materials gesetzt.
LEUCHTEN = {"led_violett_f": 2.2, "led_cyan_f": 2.2, "led_boden_f": 1.6, "led_warm_f": 1.8}

_material_roh = rw.material


def _material_mit_licht(name):
    mat = _material_roh(name)
    staerke = LEUCHTEN.get(name)
    if staerke and not mat.get("leuchtet"):
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Emission Color"].default_value = bsdf.inputs["Base Color"].default_value
        bsdf.inputs["Emission Strength"].default_value = staerke
        mat["leuchtet"] = True
    return mat


rw.material = _material_mit_licht


def leuchten_erweitern(eintraege):
    LEUCHTEN.update(eintraege)


def flach_viereck(name, punkte, y, mat_name):
    """Flaches Viereck auf Hoehe y aus vier (x, z)-Punkten, Normale nach oben."""
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for (x, z) in punkte]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat_name)


# ==============================================================================
# BODENMODULE
# ==============================================================================

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def _flecken(seed, anzahl, mats, y=0.0012, groesse=(0.02, 0.07)):
    rng = random.Random(seed)
    teile = []
    for i in range(anzahl):
        x = rng.uniform(-0.44, 0.44)
        z = rng.uniform(-0.44, 0.44)
        s = rng.uniform(*groesse)
        w = math.radians(rng.uniform(0, 90))
        pk = []
        for k in range(4):
            a = w + k * math.pi / 2
            pk.append((x + math.cos(a) * s * 0.5, z + math.sin(a) * s * 0.5 * rng.uniform(0.6, 1.0)))
        teile.append(flach_viereck("fleck", pk, y, mats[i % len(mats)]))
    return teile


def _hallenplatte(seed):
    teile = [_tragplatte("halle_fuge_f", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004, "halle_f"))
    teile += _flecken(seed, 9, ["halle_fleck_d_f", "halle_fleck_h_f", "halle_fleck_d_f"])
    return teile


def boden_hallenboden_a():
    return _hallenplatte(501)


def boden_hallenboden_b():
    teile = _hallenplatte(502)
    # Kabelkanal: dunkle Rille quer ueber die Platte, darin ein duenner LED-Streifen
    teile.append(kasten("kanal", (1.0, 0.004, 0.09), (0.0, 0.002, 0.43), "rost_wanne_f", unten=False))
    teile.append(kasten("kanal_led", (1.0, 0.006, 0.02), (0.0, 0.003, 0.43), "led_boden_f", unten=False))
    return teile


def _gitterrost(variante):
    """Gitterrost ueber einer dunklen Kabelwanne. Unter dem Rost laufen zwei
    Leuchtkabel entlang x (in a und b an derselben Stelle, damit sie ueber
    die Modulgrenzen durchlaufen)."""
    teile = [_tragplatte("rost_wanne_f", -0.05)]
    teile.append(kasten("kabel_c", (1.0, 0.018, 0.035), (0.0, -0.041, -0.22), "led_cyan_f", unten=False))
    teile.append(kasten("kabel_v", (1.0, 0.018, 0.035), (0.0, -0.041, 0.2), "led_violett_f", unten=False))
    teile.append(kasten("kabel_d", (1.0, 0.022, 0.05), (0.0, -0.039, 0.0), "warn_dunkel_f", unten=False))
    # Traeger (tragend, entlang z) und Querstaebe (entlang x)
    for i in range(6):
        x = -0.5 + (i + 0.5) / 6.0
        teile.append(kasten("traeger", (0.022, 0.03, 1.0), (x, -0.015, 0.0), "rost_stab_f", unten=False))
    for k in range(4):
        z = -0.5 + (k + 0.5) / 4.0
        teile.append(kasten("quer", (1.0, 0.012, 0.012), (0.0, -0.006, z), "rost_stab_f", unten=False))
    # Randrahmen nur hinten und links: Nachbarn legen ihren eigenen an
    teile.append(kasten("rand", (1.0, 0.03, 0.03), (0.0, -0.015, -0.485), "stahl_f", unten=False))
    teile.append(kasten("rand", (0.03, 0.03, 0.94), (-0.485, -0.015, 0.015), "stahl_f", unten=False))
    if variante == "b":
        # Schraubplatte
        teile.append(kasten("lasche", (0.12, 0.004, 0.12), (0.3, 0.002, 0.3), "stahl_f", unten=False))
    return teile


def boden_gitterrost_a():
    return _gitterrost("a")


def boden_gitterrost_b():
    return _gitterrost("b")


def _beton(seed):
    teile = [_tragplatte("beton_fuge_f", -0.004)]
    teile.append(kissen_platte("belag", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.006, "beton_f"))
    teile += _flecken(seed, 12, ["beton_fleck_f", "beton_hell_f"], groesse=(0.02, 0.09))
    return teile


def boden_beton_a():
    return _beton(503)


def boden_beton_b():
    return _beton(504)


def _kacheln(anzahl, fuge_mat, mat_fn, fase, tiefe=-0.006):
    teile = [_tragplatte(fuge_mat, tiefe)]
    kante = 1.0 / anzahl
    for i in range(anzahl):
        for k in range(anzahl):
            x0 = -0.5 + i * kante
            z0 = -0.5 + k * kante
            teile.append(kissen_platte("kachel", x0, x0 + kante, z0, z0 + kante,
                                       0.0, tiefe, fase, mat_fn(i, k)))
    return teile


def boden_teppich_a():
    return _kacheln(2, "teppich_fuge_f",
                    lambda i, k: "teppich_f" if (i + k) % 2 == 0 else "teppich2_f", 0.006, -0.004)


def boden_teppich_b():
    return _kacheln(2, "teppich_fuge_f",
                    lambda i, k: "teppich2_f" if (i + k) % 2 == 0 else "teppich_f", 0.006, -0.004)


def _deck(versatz):
    """Dachdeck aus Verbunddielen mit sichtbaren Spalten."""
    teile = [_tragplatte("deck_fuge_f", -0.03)]
    breite = 0.25
    for i in range(4):
        z0 = -0.5 + i * breite + 0.012
        z1 = -0.5 + (i + 1) * breite - 0.012
        mat = "deck2_f" if (i + versatz) % 2 else "deck_f"
        teile.append(kasten("diele", (1.0, 0.03, z1 - z0), (0.0, -0.015, (z0 + z1) / 2.0), mat, unten=False))
        # feine Rillen der Verbunddiele
        teile.append(flach_viereck("rille", [(-0.5, (z0 + z1) / 2 - 0.006), (0.5, (z0 + z1) / 2 - 0.006),
                                             (0.5, (z0 + z1) / 2 + 0.006), (-0.5, (z0 + z1) / 2 + 0.006)],
                                   0.0008, "deck_fuge_f"))
    return teile


def boden_deck_a():
    return _deck(0)


def boden_deck_b():
    return _deck(1)


def boden_fliese_a():
    return _kacheln(3, "fliese_fuge_f", lambda i, k: "fliese_f", 0.010)


def boden_fliese_b():
    lila = {(0, 2), (2, 0)}
    return _kacheln(3, "fliese_fuge_f",
                    lambda i, k: "fliese2_f" if (i, k) in lila else "fliese_f", 0.010)


# ==============================================================================
# WANDMODULE
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
STEIN_H = 0.15          # Schichthoehe Backstein (mit Fuge)


def _kappe(hoehe, x0=-0.5, x1=0.5, licht=True):
    """Dunkle Stahlkappe; obenauf ein schmales violettes Lichtband."""
    d = KAPPE_DICKE / 2.0
    teile = [profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.02), x0, x1, "kappe_f")]
    if licht:
        teile.append(kasten("lichtband", (x1 - x0, 0.006, 0.05), ((x0 + x1) / 2, hoehe + 0.002, 0.0),
                            "led_violett_f", unten=False))
    return teile


def _leiste(hoehe, x0=-0.5, x1=0.5):
    d = LEISTE_DICKE / 2.0
    return profil_x("leiste", rundprofil(-d, d, 0.0, hoehe, 0.012, 1), x0, x1, "sockel_f")


def _koerper(x0, x1, y0, y1, mat="ziegel_f"):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, mat)


def _leistenhoehe(hoehe):
    return min(LEISTE_HOEHE, hoehe * 0.2)


def _ziegel(x0, x1, y0, y1, seiten=(-1, 1), stoss=True):
    """Backsteinbild auf der Wandflaeche: waagerechte Lagerfugen je Schicht,
    versetzte Stossfugen, einzelne dunklere Steine. Nur Flaechen knapp vor
    der Wand -- guenstig und aus der Kameradistanz klar lesbar."""
    teile = []
    rng = random.Random(int((x0 + 3) * 100 + y0 * 1000))
    y = y0 + STEIN_H
    schicht = 0
    while y < y1 - 0.02:
        for s in seiten:
            teile.append(kasten("lagerfuge", (x1 - x0, 0.018, 0.004),
                                ((x0 + x1) / 2, y, s * (WAND_DICKE / 2 + 0.002)), "fuge_f"))
        schicht += 1
        y += STEIN_H
    if stoss:
        yb = y0
        schicht = 0
        while yb < y1 - 0.05:
            yt = min(yb + STEIN_H, y1)
            versatz = 0.0 if schicht % 2 == 0 else 0.25
            for s in seiten:
                for xs in (-0.5 + versatz, 0.0 + versatz):
                    if x0 + 0.01 < xs < x1 - 0.01:
                        teile.append(kasten("stossfuge", (0.016, yt - yb - 0.018, 0.004),
                                            (xs, (yb + yt) / 2 + 0.009, s * (WAND_DICKE / 2 + 0.002)), "fuge_f"))
                # ein dunklerer Stein je zweiter Schicht
                if rng.random() < 0.45:
                    xm = rng.choice((-0.25, 0.25)) + versatz * (1 if rng.random() < 0.5 else -1)
                    if x0 + 0.13 < xm < x1 - 0.13:
                        teile.append(kasten("stein_d", (0.22, yt - yb - 0.03, 0.003),
                                            (xm, (yb + yt) / 2 + 0.009, s * (WAND_DICKE / 2 + 0.0015)), "ziegel_d_f"))
            schicht += 1
            yb += STEIN_H
    return teile


def wand_voll():
    h = HOEHE["voll"]
    teile = [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001), _leiste(_leistenhoehe(h))]
    teile += _kappe(h)
    # Vollwaende stehen nur hinten und links: die Aussenseite sieht niemand.
    teile += _ziegel(-0.5, 0.5, LEISTE_HOEHE, h - KAPPE_HOEHE, seiten=(1,))
    return teile


def wand_voll_fenster():
    """Industriefenster: Stahlrahmen mit 3 x 3 Sprossenfeldern, 1,05 bis 2,20,
    fast modulbreit. Oben ein kleiner Kippfluegel, leicht geoeffnet."""
    h = HOEHE["voll"]
    ox, u, o = 0.44, 1.02, 2.2
    teile = [
        _koerper(-0.5, 0.5, 0.0, u),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _koerper(-0.5, -ox, u, o),
        _koerper(ox, 0.5, u, o),
        _leiste(_leistenhoehe(h)),
    ]
    teile += _kappe(h)
    teile += _ziegel(-0.5, 0.5, LEISTE_HOEHE, u, seiten=(1,))
    # Sturz aus Rollschicht (hochkant gestellte Steine), innen und aussen
    for s in (-1, 1):
        teile.append(kasten("sturz", (2 * ox + 0.08, 0.14, 0.012), (0.0, o + 0.07, s * (WAND_DICKE / 2 + 0.004)),
                            "ziegel_d_f"))
        for i in range(7):
            teile.append(kasten("sturz_fuge", (0.012, 0.14, 0.004),
                                (-ox + 0.06 + i * (2 * ox - 0.12) / 6, o + 0.07, s * (WAND_DICKE / 2 + 0.011)),
                                "fuge_f"))
    r, t = 0.045, 0.1
    teile.append(kasten("rahmen_l", (r, o - u, t), (-ox + r / 2, (u + o) / 2, 0.0), "rahmen_f"))
    teile.append(kasten("rahmen_r", (r, o - u, t), (ox - r / 2, (u + o) / 2, 0.0), "rahmen_f"))
    teile.append(kasten("rahmen_o", (2 * ox - 2 * r, r, t), (0.0, o - r / 2, 0.0), "rahmen_f"))
    teile.append(kasten("rahmen_u", (2 * ox - 2 * r, r, t), (0.0, u + r / 2, 0.0), "rahmen_f"))
    innen_b = 2 * ox - 2 * r
    innen_h = o - u - 2 * r
    for i in (1, 2):
        teile.append(kasten("sprosse_s", (0.022, innen_h, 0.05), (-innen_b / 2 + i * innen_b / 3, (u + o) / 2, 0.0),
                            "rahmen_f"))
        teile.append(kasten("sprosse_w", (innen_b, 0.022, 0.05), (0.0, u + r + i * innen_h / 3, 0.0), "rahmen_f"))
    teile.append(kasten("glas", (innen_b, innen_h, 0.016), (0.0, (u + o) / 2, 0.0), "glas_f"))
    # Fensterbank innen, Stahl
    teile.append(kasten("bank", (0.98, 0.03, 0.22), (0.0, u - 0.015, 0.04), "stahl_f", rund=0.008, segmente=1))
    return teile


def wand_halb():
    """Innenwand: Backstein bis 0,55, darueber Stahlgitter, oben die Kappe."""
    h = HOEHE["halb"]
    u = 0.55
    teile = [_koerper(-0.5, 0.5, 0.0, u), _leiste(_leistenhoehe(h))]
    teile += _kappe(h)
    teile += _ziegel(-0.5, 0.5, LEISTE_HOEHE, u)
    teile.append(profil_x("bruestung", rundprofil(-0.11, 0.11, u - 0.001, u + 0.035, 0.012, 1),
                          -0.5, 0.5, "kappe_f"))
    oben = h - KAPPE_HOEHE
    teile.append(kasten("gitterpfosten", (0.04, oben - u, 0.05), (-0.48, (oben + u) / 2, 0.0), "rahmen_f"))
    for i in range(8):
        x = -0.4375 + i * 0.125
        teile.append(kasten("draht_s", (0.012, oben - u - 0.03, 0.012), (x, (oben + u) / 2 + 0.01, 0.0),
                            "stahl_hell_f"))
    for y in (0.74, 0.92):
        teile.append(kasten("draht_w", (1.0, 0.012, 0.014), (0.0, y, 0.0), "stahl_hell_f"))
    return teile


def wand_sockel():
    """Sockel vorn: Backstein mit Kappe, aussen (lokal -z) ein Lichtband."""
    h = HOEHE["sockel"]
    teile = [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001), _leiste(_leistenhoehe(h))]
    teile += _kappe(h)
    teile += _ziegel(-0.5, 0.5, 0.07, h - KAPPE_HOEHE, stoss=True)
    teile.append(kasten("lichtband_aussen", (1.0, 0.02, 0.006), (0.0, h - KAPPE_HOEHE - 0.03,
                                                                  -(WAND_DICKE / 2 + 0.004)), "led_violett_f"))
    return teile


def _tuerrahmen():
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1, t), (s * TUER_PFOSTEN_X, (h - 0.1) / 2, 0.0),
                            "rahmen_f", rund=0.012, segmente=1, unten=False))
        # Leuchtstreifen innen in der Laibung
        teile.append(kasten("laibung_licht", (0.012, h - 0.3, 0.05),
                            (s * (TUER_PFOSTEN_X - b / 2 - 0.004), (h - 0.1) / 2, 0.0), "led_cyan_f"))
        teile.append(kasten("schutz", (b + 0.01, 0.3, t + 0.01), (s * TUER_PFOSTEN_X, 0.15, 0.0), "warn_gelb_f",
                            unten=False))
        teile.append(kasten("schutz_band", (b + 0.012, 0.07, t + 0.012), (s * TUER_PFOSTEN_X, 0.15, 0.0),
                            "warn_dunkel_f", unten=False))
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.12, t), (0.0, h - 0.06, 0.0),
                        "kappe_f", rund=0.02, segmente=2))
    teile.append(kasten("sturz_licht", (2 * TUER_PFOSTEN_X - 0.1, 0.03, 0.006), (0.0, h - 0.06, t / 2 + 0.003),
                        "led_violett_f"))
    teile.append(kasten("sturz_licht", (2 * TUER_PFOSTEN_X - 0.1, 0.03, 0.006), (0.0, h - 0.06, -t / 2 - 0.003),
                        "led_violett_f"))
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "stahl_hell_f", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Stahltuer mit Bullauge, 105 Grad nach aussen (lokal -z) aufgeschwenkt."""
    teile = _tuerrahmen()
    blatt_b, blatt_h, blatt_d = 0.78, 1.93, 0.045
    blatt = [
        kasten("tuerblatt", (blatt_b, blatt_h, blatt_d), (blatt_b / 2, 0.012 + blatt_h / 2, 0.0),
               "tuer_f", rund=0.012, segmente=1),
    ]
    import mathutils
    mitte = G(blatt_b / 2, 1.34, 0.0)
    kipp = (mathutils.Matrix.Translation(mitte) @ mathutils.Matrix.Rotation(math.radians(90), 4, "X")
            @ mathutils.Matrix.Translation(-mitte))
    for seite in (-1, 1):
        for name, r, h, mat, dz in (("bullauge_r", 0.15, 0.01, "rahmen_f", 0.005),
                                    ("bullauge", 0.12, 0.004, "glas_f", 0.011)):
            o = zylinder(name, r, h, (blatt_b / 2, 1.34 - h / 2, 0.0), mat, seiten=12)
            o.matrix_world = mathutils.Matrix.Translation(G(0, 0, seite * (blatt_d / 2 + dz))) @ kipp @ o.matrix_world
            blatt.append(o)
        blatt.append(kasten("stange", (0.5, 0.035, 0.03), (blatt_b / 2 + 0.05, 0.98, seite * (blatt_d / 2 + 0.03)),
                            "stahl_hell_f"))
        blatt.append(kasten("trittblech", (blatt_b - 0.06, 0.16, 0.006),
                            (blatt_b / 2, 0.11, seite * (blatt_d / 2 + 0.003)), "stahl_hell_f"))
    scharnier_x = -TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2
    transformieren(blatt, x=scharnier_x, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    teile += blatt
    return teile


def gelaender():
    """Stahlgelaender: runder Handlauf mit Lichtleiste, Knieleiste, Fussblech."""
    teile = []
    teile.append(profil_x("handlauf", rundprofil(-0.035, 0.035, 0.94, 1.0, 0.025), -0.5, 0.5, "stahl_hell_f"))
    teile.append(kasten("handlauf_licht", (1.0, 0.012, 0.02), (0.0, 0.935, 0.0), "led_violett_f"))
    teile.append(profil_x("knieleiste", rundprofil(-0.02, 0.02, 0.50, 0.54, 0.015), -0.5, 0.5, "stahl_hell_f"))
    teile.append(kasten("fussblech", (1.0, 0.12, 0.02), (0.0, 0.10, 0.0), "kappe_f"))
    teile.append(kasten("stiel", (0.05, 0.95, 0.05), (0.0, 0.475, 0.0), "stahl_f", rund=0.008, segmente=1))
    return teile


def _pfosten(hoehe):
    """Genieteter Stahltraeger als I-Profil, dunkles Violettgrau."""
    lh = _leistenhoehe(hoehe)
    koerper_h = hoehe - KAPPE_HOEHE + 0.002
    teile = [
        kasten("flansch_v", (0.20, koerper_h, 0.035), (0.0, koerper_h / 2, 0.0925), "stahl_f", unten=False),
        kasten("flansch_h", (0.20, koerper_h, 0.035), (0.0, koerper_h / 2, -0.0925), "stahl_f", unten=False),
        kasten("steg", (0.035, koerper_h, 0.16), (0.0, koerper_h / 2, 0.0), "stahl_f", unten=False),
        kasten("kopfplatte", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "kappe_f", rund=0.02, segmente=2),
        kasten("kopflicht", (0.12, 0.006, 0.12), (0.0, hoehe + 0.002, 0.0), "led_violett_f", unten=False),
        kasten("fussplatte", (0.24, lh, 0.24), (0.0, lh / 2, 0.0), "sockel_f", unten=False),
    ]
    if hoehe > 1.0:
        # Nietreihen auf den Flanschen
        for y in [v for v in (0.6, 1.2, 1.8) if v < hoehe - 0.2]:
            for s in (-1, 1):
                for xn in (-0.06, 0.06):
                    teile.append(kasten("niet", (0.022, 0.022, 0.01), (xn, y, s * 0.114), "stahl_hell_f"))
        lang = hoehe - 0.8
        teile.append(kasten("lichtstreifen", (0.02, lang, 0.006), (0.0, 0.4 + lang / 2, 0.1135), "led_cyan_f"))
    return teile


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


# ==============================================================================
# ALTMODULE (validate Schritt 7, RoomBuilder) -- einfache Varianten
# ==============================================================================

def _altfliese(linie, mat="halle_f"):
    teile = [kasten("fliese", (0.98, 0.03, 0.98), (0.0, 0.0, 0.0), mat)]
    teile += _flecken(507 if not linie else 508, 5, ["halle_fleck_d_f", "halle_fleck_h_f"], y=0.0162)
    if linie:
        teile.append(flach_viereck("linie", [(-0.49, -0.04), (0.49, -0.04), (0.49, 0.04), (-0.49, 0.04)],
                                   0.0166, "violett_f"))
    return teile


def raum_fliese_a():
    return _altfliese(False)


def raum_fliese_b():
    return _altfliese(False, "halle_fleck_h_f")


def raum_fliese_weg():
    return _altfliese(True)


def _altwand(x0, x1, y0=0.0, y1=2.2):
    teile = [
        kasten("altwand", (x1 - x0, y1 - 0.06 - y0, 0.2), ((x0 + x1) / 2, (y0 + y1 - 0.06) / 2, 0.0), "ziegel_f"),
        kasten("altkappe", (x1 - x0, 0.06, 0.2), ((x0 + x1) / 2, y1 - 0.03, 0.0), "kappe_f"),
    ]
    y = y0 + 0.3
    while y < y1 - 0.1:
        teile.append(kasten("altfuge", (x1 - x0, 0.018, 0.206), ((x0 + x1) / 2, y, 0.0), "fuge_f"))
        y += 0.3
    return teile


def raum_wand():
    return _altwand(-0.5, 0.5)


def raum_wand_ecke():
    teile = _altwand(-0.5, 0.53)
    teile.append(kasten("altwand_z", (0.2, 2.14, 0.83), (0.43, 1.07, 0.515), "ziegel_f"))
    teile.append(kasten("altkappe_z", (0.2, 0.06, 0.83), (0.43, 2.17, 0.515), "kappe_f"))
    return teile


def raum_wand_tuer():
    teile = _altwand(-1.0, -0.5) + _altwand(0.5, 1.0)
    teile.append(kasten("altsturz", (1.0, 0.3, 0.2), (0.0, 2.05, 0.0), "ziegel_d_f"))
    for s in (-1, 1):
        teile.append(kasten("altpfosten", (0.08, 1.9, 0.2), (s * 0.46, 0.95, 0.0), "rahmen_f"))
    return teile


def raum_wand_fenster():
    teile = [
        kasten("unten", (1.0, 1.0, 0.2), (0.0, 0.5, 0.0), "ziegel_f"),
        kasten("oben", (1.0, 0.2, 0.2), (0.0, 1.97, 0.0), "ziegel_d_f"),
        kasten("kappe", (1.0, 0.06, 0.2), (0.0, 2.17, 0.0), "kappe_f"),
        kasten("seite_l", (0.1, 0.87, 0.2), (-0.45, 1.435, 0.0), "ziegel_f"),
        kasten("seite_r", (0.1, 0.87, 0.2), (0.45, 1.435, 0.0), "ziegel_f"),
        kasten("rahmen", (0.8, 0.87, 0.26), (0.0, 1.435, 0.0), "rahmen_f", unten=False),
        kasten("sprosse", (0.03, 0.8, 0.265), (0.0, 1.435, 0.0), "rahmen_f"),
    ]
    teile.append(kasten("glas", (0.72, 0.79, 0.262), (0.0, 1.435, 0.0), "glas_f"))
    return teile


# ==============================================================================
# VORSCHAU -- kuehl-violettes Umgebungslicht, warme Sonne (wie worlds.json)
# ==============================================================================

def rendern(pfad, ziel, ortho, aufloesung=1080, breite=None, hintergrund=HINTERGRUND):
    from mathutils import Vector
    from build_room_wg import farbe
    szene = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(o, do_unlink=True)
    zielvek = G(*ziel)
    richtung = Vector((1.0, -1.0, 1.0)).normalized()
    cam_daten = bpy.data.cameras.new("vorschau_kamera")
    cam_daten.type = "ORTHO"
    cam_daten.ortho_scale = ortho
    cam_daten.clip_start = 0.1
    cam_daten.clip_end = 400.0
    cam = bpy.data.objects.new("vorschau_kamera", cam_daten)
    szene.collection.objects.link(cam)
    cam.location = zielvek + richtung * 120.0
    cam.rotation_euler = (-richtung).to_track_quat("-Z", "Y").to_euler()
    szene.camera = cam

    def sonne(name, energie, farbe_hex, richtung_blender, schatten, winkel):
        daten = bpy.data.lights.new(name, "SUN")
        daten.energy = energie
        daten.color = farbe(farbe_hex)[:3]
        daten.use_shadow = schatten
        daten.angle = math.radians(winkel)
        obj = bpy.data.objects.new(name, daten)
        szene.collection.objects.link(obj)
        obj.rotation_euler = (-Vector(richtung_blender).normalized()).to_track_quat("-Z", "Y").to_euler()
        return obj

    sonne("licht_haupt", 2.3, "#FFE6CC", G(0.45, 1.0, 0.65), True, 12.0)
    sonne("licht_auf", 0.7, "#DCD6FF", G(-0.9, 0.55, 0.25), False, 30.0)
    welt = bpy.data.worlds.new("vorschau_welt")
    if welt.node_tree is None:
        welt.use_nodes = True
    baum = welt.node_tree
    for n in list(baum.nodes):
        baum.nodes.remove(n)
    ausgang = baum.nodes.new("ShaderNodeOutputWorld")
    licht = baum.nodes.new("ShaderNodeBackground")
    licht.inputs["Color"].default_value = farbe("#EEEAFF")
    licht.inputs["Strength"].default_value = 0.55
    grund = baum.nodes.new("ShaderNodeBackground")
    grund.inputs["Color"].default_value = farbe(hintergrund)
    grund.inputs["Strength"].default_value = 1.0
    pfad_knoten = baum.nodes.new("ShaderNodeLightPath")
    mischen = baum.nodes.new("ShaderNodeMixShader")
    baum.links.new(pfad_knoten.outputs["Is Camera Ray"], mischen.inputs["Fac"])
    baum.links.new(licht.outputs["Background"], mischen.inputs[1])
    baum.links.new(grund.outputs["Background"], mischen.inputs[2])
    baum.links.new(mischen.outputs["Shader"], ausgang.inputs["Surface"])
    szene.world = welt
    szene.render.engine = "BLENDER_EEVEE"
    szene.eevee.taa_render_samples = 32
    szene.eevee.use_shadows = True
    try:
        szene.eevee.use_fast_gi = True
    except Exception:
        pass
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"
    szene.render.resolution_x = breite or aufloesung
    szene.render.resolution_y = aufloesung
    szene.render.resolution_percentage = 100
    szene.render.film_transparent = False
    szene.render.image_settings.file_format = "PNG"
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    szene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)


MODULE = {
    "boden_hallenboden_a": boden_hallenboden_a,
    "boden_hallenboden_b": boden_hallenboden_b,
    "boden_gitterrost_a": boden_gitterrost_a,
    "boden_gitterrost_b": boden_gitterrost_b,
    "boden_beton_a": boden_beton_a,
    "boden_beton_b": boden_beton_b,
    "boden_teppich_a": boden_teppich_a,
    "boden_teppich_b": boden_teppich_b,
    "boden_deck_a": boden_deck_a,
    "boden_deck_b": boden_deck_b,
    "boden_fliese_a": boden_fliese_a,
    "boden_fliese_b": boden_fliese_b,
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
    "raum_fliese_a": raum_fliese_a,
    "raum_fliese_b": raum_fliese_b,
    "raum_fliese_weg": raum_fliese_weg,
    "raum_wand": raum_wand,
    "raum_wand_ecke": raum_wand_ecke,
    "raum_wand_tuer": raum_wand_tuer,
    "raum_wand_fenster": raum_wand_fenster,
}


def modul_pfad(name):
    return os.path.join(AUSGABE_MODULE, name + ".glb")


def module_bauen():
    print("")
    print("=== MODULE WELT 5 (FABRIKHALLE) ===")
    for name, bauen in MODULE.items():
        alles_loeschen()
        obj = verbinden(bauen(), name)
        pfad = modul_pfad(name)
        exportieren(obj, pfad)
        (x0, x1), (y0, y1), (z0, z1) = masse(obj)
        print("  %-28s %4d Dreiecke  x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f  %2d Mat  %5.1f KB"
              % (name, dreiecke(obj), x0, x1, y0, y1, z0, z1, len(obj.data.materials),
                 os.path.getsize(pfad) / 1024.0))


def module_vorschau():
    alles_loeschen()
    boeden = [n for n in MODULE if n.startswith("boden_")]
    for i, name in enumerate(boeden):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                importieren(modul_pfad(name), x=(i % 4) * 3.4 + dx, z=(i // 4) * 3.4 + dz)
    rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (5.1, 0.0, 3.4), 14.0)

    alles_loeschen()
    zeilen = [
        ("wand_voll", "wand_voll_fenster", "pfosten_voll"),
        ("wand_halb", "wand_halb_tuer", "pfosten_halb"),
        ("wand_sockel", "wand_sockel_tuer", "pfosten_sockel"),
    ]
    for r, (wand, sonder, pfosten) in enumerate(zeilen):
        z = r * 3.0
        for dx, modul in ((0, wand), (1, sonder), (2, sonder if r == 0 else wand), (3, wand)):
            importieren(modul_pfad(modul), x=dx, z=z)
        importieren(modul_pfad(pfosten), x=-0.5, z=z)
        importieren(modul_pfad(pfosten), x=3.5, z=z)
        importieren(modul_pfad(wand), x=-0.5, z=z + 0.5, dreh_grad=90.0)
        importieren(modul_pfad(wand), x=-0.5, z=z + 1.5, dreh_grad=90.0)
        for dx in range(4):
            importieren(modul_pfad("boden_hallenboden_" + ("a" if dx % 2 == 0 else "b")), x=dx, z=z + 1)
    for dx in range(4):
        importieren(modul_pfad("wand_sockel"), x=dx, z=8.5, dreh_grad=180.0)
    for dx in range(3):
        importieren(modul_pfad("gelaender"), x=5.5 + dx, z=0.0)
        importieren(modul_pfad("boden_deck_" + ("a" if dx % 2 == 0 else "b")), x=5.5 + dx, z=0.5)
        importieren(modul_pfad("boden_gitterrost_" + ("a" if dx % 2 == 0 else "b")), x=5.5 + dx, z=2.5)
    rendern(os.path.join(AUSGABE_VORSCHAU, "module_waende.png"), (3.2, 0.8, 4.0), 11.5)

    alles_loeschen()
    for i, name in enumerate(("raum_fliese_a", "raum_fliese_b", "raum_fliese_weg")):
        importieren(modul_pfad(name), x=i, z=2.0)
    importieren(modul_pfad("raum_wand"), x=0, z=0)
    importieren(modul_pfad("raum_wand_fenster"), x=1, z=0)
    importieren(modul_pfad("raum_wand_tuer"), x=2.5, z=0)
    importieren(modul_pfad("raum_wand_ecke"), x=4, z=0)
    rendern(os.path.join(AUSGABE_VORSCHAU, "module_alt.png"), (2.0, 0.8, 1.0), 6.5)


if __name__ == "__main__":
    module_bauen()
    if "--ohne-vorschau" not in sys.argv:
        module_vorschau()
