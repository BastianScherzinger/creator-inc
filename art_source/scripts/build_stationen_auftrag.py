"""Erzeugt die Stationen der Welt `auftrag` (Welt 2, N11) als GLB plus Symbole.

Aufruf:
    blender --background --python art_source/scripts/build_stationen_auftrag.py
    blender --background --python art_source/scripts/build_stationen_auftrag.py -- --vorschau --nah
    blender --background --python art_source/scripts/build_stationen_auftrag.py -- --nur intake --kein_export --vorschau
    blender --background --python art_source/scripts/build_stationen_auftrag.py -- --symbole

Vertrag (docs/NACHT_PLAN.md Paragraf 5, docs/nacht/ausstattung_welten.md):
    project/assets/stations/auftrag/station_<id>_basis.glb
    project/assets/stations/auftrag/station_<id>_ausstattung_<n>_<m>.glb   (m = 0..3, 0 darf fehlen)
    project/assets/stations/auftrag/station_<id>_<1|2|3>.glb               (Altmodelle: Basis + alle Plaetze auf Stufe m)
    project/assets/world/auftrag/fluss_teil.glb
    project/assets/ui/auftrag/station_<id>.png, station_<id>_ausstattung_<n>_<m>.png

Die Helfer (Koordinaten, Kasten, Zylinder, Pruefung, Vorschau) kommen aus
build_stationen_wg.py; dieses Skript tauscht nur Ausgabeordner, Palette und
Stationsliste aus. Alle Masse sind GODOT-Koordinaten (y oben, Vorderseite +z).
Aus der Kamera (+1, +1, +1) gilt: links im Bild = (-x, +z), oben im Bild =
(-x, -z), rechts im Bild = (+x, -z). Platz 1 steht links, Platz 2 hinten/Mitte,
Platz 3 rechts.
"""

import bpy
import math
import os
import sys

import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stationen_wg as wg  # noqa: E402

from build_stationen_wg import (kasten, zylinder, stab, kugel, ring, keil,  # noqa: E402
                                punkt, verkette, schirm_inhalt, monitor, laptop,
                                handy, pflanze, farbe)

AUSGABE = os.path.join(wg.PROJEKT, "project", "assets", "stations", "auftrag")
AUSGABE_UI = os.path.join(wg.PROJEKT, "project", "assets", "ui", "auftrag")
AUSGABE_FLUSS = os.path.join(wg.PROJEKT, "project", "assets", "world", "auftrag", "fluss_teil.glb")
VORSCHAU = os.path.join(wg.PROJEKT, "art_source", "vorschau", "auftrag_stationen")
BUDGET_GESAMT = 3000

wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU

# --- Palette -----------------------------------------------------------------
# Studio in einer Hinterhof-Garage: warmes Holz, Beton-Grau, Geraete dunkel,
# Welt-Akzent Pink #FF4FA3 sparsam (Leuchtstreifen, Kabel, einzelne Flaechen).
wg.PALETTE.update({
    "pink":          ("#FF4FA3", 0.0),
    "pink_hell":     ("#FFB3D6", 0.0),
    "pink_led":      ("#FF4FA3", 1.4),
    "schirm_pink":   ("#FF7DBB", 0.55),
    "tuerkis":       ("#3FB8AF", 0.0),
    "mint":          ("#9FE0C8", 0.0),
    "metall":        ("#A9B0BA", 0.0),
    "container":     ("#4F8FA8", 0.0),
    "container_d":   ("#3C7189", 0.0),
    "leder":         ("#B5653A", 0.0),
    "stoff_senf":    ("#E3A33B", 0.0),
    "stoff_blau":    ("#5C7FC4", 0.0),
    "weiss":         ("#FAFAF7", 0.0),
    "kuehl_blau":    ("#7FD3F7", 1.0),
    "rot_led":       ("#FF3B3B", 1.4),
})
GLAS = {"glas": ("#CFEFFF", 0.35)}


def material(name):
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if name in GLAS:
        hexwert, alpha = GLAS[name]
        lin = farbe(hexwert)
        bsdf.inputs["Base Color"].default_value = lin
        bsdf.inputs["Alpha"].default_value = alpha
        bsdf.inputs["Roughness"].default_value = 0.1
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
        mat.diffuse_color = lin[:3] + (alpha,)
        return mat
    hexwert, leuchten = wg.PALETTE[name]
    lin = farbe(hexwert)
    bsdf.inputs["Base Color"].default_value = lin
    bsdf.inputs["Roughness"].default_value = 0.45 if name in ("metall", "container", "container_d") else 0.75
    bsdf.inputs["Metallic"].default_value = 0.35 if name == "metall" else 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
    if leuchten > 0.0:
        bsdf.inputs["Emission Color"].default_value = lin
        bsdf.inputs["Emission Strength"].default_value = leuchten
    mat.diffuse_color = lin
    return mat


wg.material = material
wg.BUDGET_AUSSTATTUNG = 1100

_bevel_orig = wg._bevel


def _bevel_sparsam(obj, breite, segmente):
    """Hoechstens ein Bevel-Segment: aus der Spielkamera kaum ein
    Unterschied, spart aber ~60 Dreiecke je Quader."""
    _bevel_orig(obj, breite, min(segmente, 1))


wg._bevel = _bevel_sparsam


def tasse(pos, mat="creme", hoehe=0.10, radius=0.045, voll=True):
    """Guenstiger Becher: 8 Seiten, Kastenhenkel."""
    t = [zylinder("tasse", radius, hoehe, (pos[0], pos[1] + hoehe * 0.5, pos[2]), mat, seiten=8, rund=(0, 0))]
    t.append(kasten("henkel", (0.012, hoehe * 0.55, 0.012), (pos[0] + radius + 0.006, pos[1] + hoehe * 0.5, pos[2]), mat, rund=(0, 0)))
    return t


# --- kleine Helfer -----------------------------------------------------------

def flach(name, b, h, pos, dreh, mat, dicke=0.004):
    return kasten(name, (b, h, dicke), pos, mat, dreh, rund=(0, 0))


def schirm(pos, dreh, b, h, art="video", rahmen="schwarz", d=0.035):
    """Bildschirm ohne Fuss, pos = Mitte, zeigt nach lokal +z."""
    t = [kasten("gehaeuse", (b, h, d), pos, rahmen, dreh, rund=(0, 0))]
    t += schirm_inhalt(pos, dreh, b * 0.9, h * 0.84, art, tiefe=d * 0.5 + 0.001)
    return t


def radar(pos, dreh, r):
    """Leuchtende Radarscheibe (Trends) auf einer Flaeche, zeigt nach +z."""
    d2 = verkette(dreh, (90, 0, 0))
    t = [zylinder("radar", r, 0.004, punkt(pos, dreh, (0, 0, 0.004)), "schirm_blau", seiten=20, dreh=d2, rund=(0, 0))]
    t.append(ring("radar_ring", r * 0.62, 0.006, punkt(pos, dreh, (0, 0, 0.008)), "schirm", verkette(dreh, (90, 0, 0)), segmente=16, quer=3))
    t.append(kasten("radar_zeiger", (r * 0.9, 0.012, 0.004), punkt(pos, dreh, (r * 0.4, r * 0.12, 0.009)), "schirm_pink", verkette(dreh, (0, 0, 18)), rund=(0, 0)))
    for k, (dx, dy) in enumerate(((-0.4, 0.35), (0.3, -0.45), (0.55, 0.3))):
        t.append(kasten("radar_punkt", (r * 0.12, r * 0.12, 0.004), punkt(pos, dreh, (dx * r, dy * r, 0.011)), "schirm_pink" if k == 1 else "schirm_orange", dreh, rund=(0, 0)))
    return t


def hocker_bar(x, z, hoehe, mat="pink"):
    t = [zylinder("sitz", 0.17, 0.05, (x, hoehe - 0.025, z), mat, seiten=10, rund=(0.015, 1))]
    t.append(stab("saeule", (x, 0.03, z), (x, hoehe - 0.05, z), 0.022, "metall", seiten=6))
    t.append(zylinder("fuss", 0.15, 0.025, (x, 0.0125, z), "grau_dunkel", seiten=10, rund=(0, 0)))
    t.append(ring("fussring", 0.12, 0.01, (x, hoehe * 0.4, z), "metall", segmente=8, quer=3))
    return t


def stuhl_buero(x, y, z, gier=0.0, mat="grau_dunkel", akzent="pink"):
    """Buerostuhl, Sitzflaeche bei y, Lehne auf der Seite lokal +z (Blick -z)."""
    d = (0, gier, 0)
    t = [kasten("sitz", (0.48, 0.08, 0.46), (x, y - 0.04, z), mat, d, rund=(0.025, 1))]
    t.append(stab("feder", (x, 0.08, z), (x, y - 0.08, z), 0.026, "metall", seiten=6))
    lehne = punkt((x, y + 0.34, z), d, (0, 0, 0.26))
    dl = verkette(d, (-8, 0, 0))
    t.append(kasten("lehne", (0.46, 0.52, 0.05), lehne, mat, dl, rund=(0.02, 1)))
    t.append(kasten("lehne_streifen", (0.08, 0.44, 0.006), punkt(lehne, dl, (0, 0, -0.027)), akzent, dl, rund=(0, 0)))
    t.append(stab("traeger", punkt((x, y - 0.05, z), d, (0, 0, 0.21)), punkt((x, y + 0.12, z), d, (0, 0, 0.26)), 0.018, "metall", seiten=4))
    for i in range(5):
        w = math.radians(90 + i * 72 + gier)
        ende = (x + math.cos(w) * 0.27, 0.04, z + math.sin(w) * 0.27)
        t.append(stab("fussarm", (x, 0.08, z), ende, 0.018, "grau_dunkel", seiten=4))
    return t


def tower(x, z, b=0.22, h=0.50, d=0.46, gier=0.0, led="pink_led", glas_seite=1, luefter=("pink_led", "rgb_cyan")):
    """PC-Gehaeuse auf dem Boden, Front nach lokal +z, Glasseite lokal +x*glas_seite."""
    dr = (0, gier, 0)
    mitte = (x, h * 0.5 + 0.006, z)
    t = [kasten("tower", (b, h, d), mitte, "schwarz", dr, rund=(0.012, 1))]
    t.append(kasten("fuesse", (b * 0.8, 0.006, d * 0.86), (x, 0.003, z), "grau_dunkel", dr, rund=(0, 0)))
    t.append(kasten("front_led", (0.02, h * 0.8, 0.004), punkt(mitte, dr, (-b * 0.27, 0.0, d * 0.5 + 0.002)), led, dr, rund=(0, 0)))
    t.append(kasten("glas", (0.004, h * 0.72, d * 0.74), punkt(mitte, dr, (glas_seite * (b * 0.5 + 0.002), 0.02, 0)), "grau_dunkel", dr, rund=(0, 0)))
    for k, y in enumerate((0.16, -0.10)):
        t.append(ring("luefter", min(0.065, h * 0.13), 0.012, punkt(mitte, dr, (glas_seite * (b * 0.5 + 0.008), y * h / 0.5 * 0.5, d * 0.12)),
                      luefter[k % len(luefter)], verkette(dr, (0, 0, 90)), segmente=10, quer=3))
    t.append(kasten("knopf", (0.03, 0.01, 0.01), punkt(mitte, dr, (b * 0.2, h * 0.45, d * 0.5 + 0.002)), "led_blau", dr, rund=(0, 0)))
    return t


# =============================================================================
# Station 1: station_intake -- Konzept (Stehtisch vor Pinnwand)
# Stehtisch Mitte (-0,05 | -0,25), Pinnwand hinten (z -0,95).
# Platz 1 links (x ~ -0,9): Storyboard. Platz 2 auf dem Tisch / hinten rechts:
# Recherche. Platz 3 rechts (x 0,4..1,08, z > -0,35): Team.
# =============================================================================

I_TISCH = (-0.05, -0.25)
I_TISCH_B, I_TISCH_T = 0.80, 0.50
I_H = 1.02
I_AUF = I_H + 0.002
I_PINN = {"x": -0.20, "b": 0.70, "unten": 0.90, "h": 0.70, "z": -0.95}


def intake_basis():
    t = []
    tx, tz = I_TISCH
    # runder Teppich
    t.append(zylinder("teppich", 0.34, 0.01, (-0.05, 0.005, -0.20), "pink_hell", seiten=16, rund=(0, 0)))
    # Stehtisch: Platte, Saeule, Fussplatte, Ablage
    t.append(kasten("platte", (I_TISCH_B, 0.04, I_TISCH_T), (tx, I_H - 0.02, tz), "holz_hell", rund=(0.014, 2)))
    t.append(kasten("zarge", (I_TISCH_B - 0.08, 0.05, I_TISCH_T - 0.08), (tx, I_H - 0.065, tz), "holz", rund=(0.01, 1)))
    t.append(zylinder("saeule", 0.05, I_H - 0.09, (tx, (I_H - 0.09) * 0.5 + 0.02, tz), "grau_dunkel", seiten=10, rund=(0, 0)))
    t.append(kasten("fussplatte", (0.52, 0.03, 0.40), (tx, 0.025, tz), "grau_dunkel", rund=(0.01, 1)))
    t.append(kasten("fussstange", (0.50, 0.03, 0.03), (tx, 0.25, tz + 0.12), "metall", rund=(0, 0)))
    t += tasse((tx - 0.28, I_AUF, tz + 0.14), "pink", hoehe=0.09, radius=0.038)
    # Stift und Karteikarten auf der Platte
    t.append(stab("stift", (tx + 0.24, I_AUF + 0.008, tz + 0.20), (tx + 0.34, I_AUF + 0.008, tz + 0.16), 0.007, "pink", seiten=4))
    # Pinnwand auf zwei Beinen
    p = I_PINN
    my = p["unten"] + p["h"] * 0.5
    t.append(kasten("rahmen", (p["b"], p["h"], 0.03), (p["x"], my, p["z"]), "holz_dunkel", rund=(0.012, 2)))
    t.append(kasten("kork", (p["b"] - 0.08, p["h"] - 0.08, 0.012), (p["x"], my, p["z"] + 0.02), "kork", rund=(0, 0)))
    for dx in (-p["b"] * 0.5 + 0.06, p["b"] * 0.5 - 0.06):
        t.append(kasten("bein", (0.04, p["unten"] + p["h"] - 0.05, 0.04), (p["x"] + dx, (p["unten"] + p["h"] - 0.05) * 0.5, p["z"] - 0.04), "holz_dunkel"))
        t.append(kasten("fuss", (0.05, 0.035, 0.28), (p["x"] + dx, 0.0175, p["z"] - 0.01), "holz_dunkel", rund=(0.01, 1)))
    kork_z = p["z"] + 0.028
    for dx, dy, b, h, mat, w in ((-0.20, 0.18, 0.14, 0.11, "gelb", 4), (-0.02, 0.20, 0.16, 0.12, "papier", -3),
                                  (0.17, 0.16, 0.12, 0.12, "pink_hell", 6), (-0.16, -0.05, 0.16, 0.12, "papier", -5),
                                  (0.05, -0.08, 0.14, 0.13, "mint", 3), (0.20, -0.12, 0.10, 0.10, "gelb", -8)):
        t.append(flach("zettel", b, h, (p["x"] + dx, my + dy, kork_z), (0, 0, w), mat))
    t.append(stab("faden", (p["x"] - 0.20, my + 0.18, kork_z + 0.004), (p["x"] + 0.05, my - 0.08, kork_z + 0.004), 0.004, "pink", seiten=3))
    return t


# --- Platz 1: Storyboard -------------------------------------------------------

def intake_a1_0():
    """Obstkiste mit losen Zetteln."""
    x, z = -0.80, 0.30
    t = [kasten("kiste", (0.40, 0.26, 0.30), (x, 0.13, z), "holz", (0, 12, 0), rund=(0.012, 1))]
    for k in range(2):
        t.append(kasten("latte", (0.41, 0.03, 0.005), punkt((x, 0.08 + k * 0.10, z), (0, 12, 0), (0, 0, 0.151)), "holz_dunkel", (0, 12, 0), rund=(0, 0)))
    for dx, dz, w, mat in ((-0.08, -0.03, 10, "papier"), (0.06, 0.04, -14, "gelb"), (0.0, 0.0, 30, "papier")):
        t.append(kasten("zettel", (0.16, 0.004, 0.12), (x + dx, 0.263 + (0.004 if mat == "gelb" else 0.0), z + dz), mat, (0, w, 0), rund=(0, 0)))
    t.append(kasten("zettel", (0.14, 0.004, 0.10), (x + 0.12, 0.002, z + 0.26), "papier", (0, -20, 0), rund=(0, 0)))
    return t


def _storykarte(pos, dreh, b, h, farbe_bild):
    t = [flach("karte", b, h, pos, dreh, "papier", dicke=0.006)]
    t.append(flach("bild", b * 0.8, h * 0.55, punkt(pos, dreh, (0, h * 0.1, 0.004)), dreh, farbe_bild))
    t.append(flach("zeile", b * 0.6, h * 0.08, punkt(pos, dreh, (-b * 0.08, -h * 0.32, 0.004)), dreh, "grau_mittel"))
    return t


def intake_a1_1():
    """Skizzenblock auf einer Staffelei."""
    x, z = -0.82, 0.20
    d = (0, 90, 0)
    t = []
    for s in (-1, 1):
        t.append(stab("bein", (x - 0.02, 1.42, z + s * 0.10), (x + 0.10, 0.0, z + s * 0.30), 0.018, "holz", seiten=4))
    t.append(stab("bein_hinten", (x - 0.03, 1.38, z), (x - 0.24, 0.0, z), 0.016, "holz_dunkel", seiten=4))
    t.append(kasten("leiste", (0.06, 0.04, 0.56), (x + 0.06, 0.62, z), "holz_dunkel", rund=(0.008, 1)))
    blatt = (x + 0.035, 0.99, z)
    dn = verkette(d, (-10, 0, 0))
    t.append(kasten("block", (0.56, 0.72, 0.02), blatt, "grau_dunkel", dn, rund=(0.004, 1)))
    t.append(flach("blatt", 0.52, 0.68, punkt(blatt, dn, (0, -0.01, 0.012)), dn, "papier"))
    for r in range(2):
        for s in range(2):
            t += _storykarte(punkt(blatt, dn, (-0.12 + s * 0.24, 0.15 - r * 0.30, 0.018)), dn, 0.20, 0.24, "schirm_blau" if (r + s) % 2 else "pink_hell")
    t.append(kasten("ringe", (0.44, 0.02, 0.03), punkt(blatt, dn, (0, 0.36, 0.01)), "metall", dn, rund=(0, 0)))
    return t


def intake_a1_2():
    """Freistehende Storyboard-Wand mit acht Karten."""
    x, z = -0.92, 0.05
    d = (0, 90, 0)
    mitte = (x, 1.10, z)
    t = [kasten("wand", (1.30, 0.96, 0.05), mitte, "weiss", d, rund=(0.014, 1))]
    t.append(kasten("kopf", (1.30, 0.10, 0.06), punkt(mitte, d, (0, 0.52, 0.0)), "pink", d, rund=(0.012, 1)))
    for s in (-1, 1):
        t.append(kasten("stuetze", (0.05, 1.60, 0.05), punkt((x, 0.80, z), d, (s * 0.60, 0, -0.04)), "grau_dunkel", d, rund=(0.008, 1)))
        t.append(kasten("fuss", (0.06, 0.04, 0.30), punkt((x, 0.02, z), d, (s * 0.60, 0, 0.0)), "grau_dunkel", d, rund=(0.008, 1)))
    farben = ("pink_hell", "schirm_blau", "mint", "gelb")
    for r in range(2):
        for s in range(4):
            t += _storykarte(punkt(mitte, d, (-0.46 + s * 0.307, 0.17 - r * 0.40, 0.03)), d, 0.25, 0.32, farben[(r + s) % 4])
    t.append(stab("pfeil", punkt(mitte, d, (-0.55, -0.40, 0.04)), punkt(mitte, d, (0.50, -0.40, 0.04)), 0.008, "pink", seiten=3))
    return t


def intake_a1_3():
    """Bildschirm-Wand: sechs Monitore im Rahmen, Leuchtkante, Pult."""
    x, z = -0.93, 0.05
    d = (0, 90, 0)
    mitte = (x, 1.34, z)
    t = [kasten("rahmen", (1.40, 0.92, 0.06), punkt(mitte, d, (0, 0, -0.03)), "grau_dunkel", d, rund=(0.012, 1))]
    t.append(kasten("led_oben", (1.40, 0.025, 0.02), punkt(mitte, d, (0, 0.47, 0.0)), "pink_led", d, rund=(0, 0)))
    t.append(kasten("led_unten", (1.40, 0.025, 0.02), punkt(mitte, d, (0, -0.47, 0.0)), "pink_led", d, rund=(0, 0)))
    arten = ("video", "plan", "video", "kurve", "video", "balken")
    for r in range(2):
        for s in range(3):
            t += schirm(punkt(mitte, d, (-0.455 + s * 0.455, 0.215 - r * 0.43, 0.02)), d, 0.44, 0.41, arten[r * 3 + s], d=0.03)
    for s in (-1, 1):
        t.append(kasten("saeule", (0.08, 0.90, 0.08), punkt((x, 0.45, z), d, (s * 0.52, 0, -0.06)), "grau_dunkel", d, rund=(0.01, 1)))
    t.append(kasten("sockel", (1.30, 0.06, 0.34), punkt((x, 0.03, z), d, (0, 0, 0.02)), "grau_dunkel", d, rund=(0.012, 1)))
    # kleines Steuerpult davor
    t.append(kasten("pult", (0.36, 0.72, 0.26), (x + 0.30, 0.36 + 0.06, z + 0.42), "schwarz", (0, 90, 0), rund=(0.012, 1)))
    t.append(kasten("pult_flaeche", (0.32, 0.006, 0.20), (x + 0.30, 0.785, z + 0.42), "schirm_pink", (0, 90, 0), rund=(0, 0)))
    return t


# --- Platz 2: Recherche --------------------------------------------------------

def intake_a2_1():
    """Tablet im Staender auf dem Tisch."""
    tx, tz = I_TISCH
    pos = (tx + 0.18, I_AUF, tz - 0.05)
    t = [kasten("staender", (0.12, 0.012, 0.10), (pos[0], I_AUF + 0.006, pos[2]), "grau_dunkel", (0, -15, 0), rund=(0, 0))]
    d = (-20, -15, 0)
    m = punkt((pos[0], I_AUF + 0.13, pos[2] - 0.02), (0, 0, 0), (0, 0, 0))
    t.append(kasten("tablet", (0.30, 0.21, 0.014), m, "grau_dunkel", d, rund=(0.006, 1)))
    t += schirm_inhalt(m, d, 0.27, 0.18, "kurve", tiefe=0.008)
    t.append(stab("stuetze", (pos[0], I_AUF + 0.01, pos[2] - 0.08), punkt(m, d, (0, 0, -0.01)), 0.008, "grau_dunkel", seiten=4))
    return t


def _doppelmonitor():
    tx, tz = I_TISCH
    t = []
    for s, art in ((-1, "video"), (1, "kurve")):
        t += monitor((tx + s * 0.20, I_AUF, tz - 0.08), (0, -s * 10, 0), 0.38, 0.26, art, fuss_hoehe=0.08)
    t += wg._tastatur((tx + 0.02, I_AUF, tz + 0.14), (0, 0, 0), 0.34, 0.11, mat="weiss", tasten="grau_hell")
    return t


def intake_a2_2():
    """Zwei Monitore und Tastatur auf dem Stehtisch."""
    return _doppelmonitor()


def intake_a2_3():
    """Grosser Trend-Bildschirm auf Rollstaender (Radar + Kurve), dazu die
    beiden Monitore."""
    t = _doppelmonitor()
    x, z = 0.66, -0.74
    d = (0, -25, 0)
    mitte = (x, 1.52, z)
    t.append(kasten("gehaeuse", (0.90, 0.60, 0.05), mitte, "schwarz", d, rund=(0, 0)))
    t.append(kasten("led", (0.90, 0.02, 0.02), punkt(mitte, d, (0, -0.32, 0.01)), "pink_led", d, rund=(0, 0)))
    t.append(flach("grund", 0.84, 0.52, punkt(mitte, d, (0, 0, 0.027)), d, "schirm"))
    t += radar(punkt(mitte, d, (-0.22, 0.0, 0.028)), d, 0.22)
    for k in range(4):
        hk = 0.10 + k * 0.08
        t.append(flach("balken", 0.06, hk, punkt(mitte, d, (0.12 + k * 0.08, -0.22 + hk * 0.5, 0.032)), d, "schirm_pink" if k == 3 else "schirm_blau"))
    t.append(kasten("saeule", (0.08, 1.20, 0.05), punkt((x, 0.62, z), d, (0, 0, -0.05)), "grau_dunkel", d, rund=(0.01, 1)))
    t.append(kasten("fuss", (0.60, 0.05, 0.10), punkt((x, 0.045, z), d, (0, 0, -0.05)), "grau_dunkel", d, rund=(0, 0)))
    for s in (-1, 1):
        t.append(kasten("fuss_quer", (0.08, 0.05, 0.30), punkt((x, 0.045, z), d, (s * 0.26, 0, -0.03)), "grau_dunkel", d, rund=(0, 0)))
        t.append(zylinder("rolle", 0.02, 0.02, punkt((x, 0.01, z), d, (s * 0.26, 0, 0.09)), "schwarz", seiten=6, rund=(0, 0)))
    return t


# --- Platz 3: Team -------------------------------------------------------------

def intake_a3_0():
    """Ein Barhocker neben dem Tisch."""
    return hocker_bar(0.62, 0.10, 0.76)


def intake_a3_1():
    """Pinker Sitzsack."""
    x, z = 0.72, 0.36
    t = [kugel("sack", 0.34, (x, 0.24, z), "pink", stufen=2, skala=(1.0, 0.72, 1.0))]
    t.append(kugel("mulde", 0.22, (x - 0.04, 0.42, z + 0.02), "pink_hell", stufen=1, skala=(1.0, 0.45, 1.0)))
    t.append(kasten("naht", (0.02, 0.012, 0.30), (x + 0.10, 0.49, z), "pink", (0, 0, 20), rund=(0, 0)))
    return t


def _sofa(x, z, laenge, gier, mat="stoff_blau", kissen="stoff_senf"):
    """Sofa, Mitte (x, z), Sitzflaeche schaut nach lokal +z."""
    d = (0, gier, 0)
    t = [kasten("sockel", (laenge, 0.26, 0.62), punkt((x, 0.17, z), d, (0, 0, 0)), mat, d, rund=(0.03, 2))]
    t.append(kasten("polster", (laenge - 0.24, 0.10, 0.50), punkt((x, 0.35, z), d, (0, 0, 0.04)), mat, d, rund=(0.035, 1)))
    t.append(kasten("lehne", (laenge, 0.38, 0.16), punkt((x, 0.46, z), d, (0, 0, -0.23)), mat, d, rund=(0.04, 2)))
    for s in (-1, 1):
        t.append(kasten("armlehne", (0.12, 0.44, 0.62), punkt((x, 0.28, z), d, (s * (laenge * 0.5 - 0.06), 0, 0)), mat, d, rund=(0.035, 1)))
    t.append(kasten("kissen", (0.30, 0.28, 0.10), punkt((x, 0.53, z), d, (-laenge * 0.22, 0, -0.10)), kissen, verkette(d, (-12, 0, 8)), rund=(0.035, 1)))
    t.append(kasten("kissen", (0.28, 0.26, 0.10), punkt((x, 0.53, z), d, (laenge * 0.22, 0, -0.10)), "pink", verkette(d, (-12, 0, -8)), rund=(0.035, 1)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(kasten("fuss", (0.04, 0.04, 0.04), punkt((x, 0.02, z), d, (sx * (laenge * 0.5 - 0.06), 0, sz * 0.25)), "holz_dunkel", d, rund=(0, 0)))
    return t


def intake_a3_2():
    """Sofa-Ecke: Sofa mit Blick zum Stehtisch, Beistelltisch, Pflanze."""
    t = _sofa(0.70, 0.40, 1.20, -90)
    t.append(zylinder("beistell", 0.16, 0.02, (0.66, 0.46, -0.30), "holz_hell", seiten=10, rund=(0, 0)))
    t.append(stab("beistell_bein", (0.66, 0.0, -0.30), (0.66, 0.45, -0.30), 0.02, "metall", seiten=6))
    t += tasse((0.62, 0.47, -0.32), "weiss", hoehe=0.08, radius=0.032)
    t += pflanze((0.88, 0.0, -0.26), groesse=1.4)
    return t


def intake_a3_3():
    """Konferenztisch mit Baenken, Laptop und Mappen."""
    x, z = 0.72, 0.36
    t = [kasten("platte", (0.50, 0.04, 1.10), (x, 0.74, z), "holz_hell", rund=(0.014, 2))]
    t.append(kasten("laeufer", (0.16, 0.004, 1.00), (x, 0.762, z), "pink", rund=(0, 0)))
    for dz in (-0.45, 0.45):
        t.append(kasten("wange", (0.40, 0.70, 0.04), (x, 0.36, z + dz), "grau_dunkel", rund=(0.01, 1)))
    t.append(kasten("steg", (0.06, 0.06, 0.86), (x, 0.30, z), "grau_dunkel", rund=(0, 0)))
    # Baenke links und rechts
    for bx in (0.33, 1.00):
        t.append(kasten("bank", (0.14, 0.04, 0.96), (bx, 0.46, z), "stoff_blau" if bx < 0.5 else "stoff_senf", rund=(0.012, 1)))
        for dz in (-0.40, 0.40):
            t.append(kasten("bank_bein", (0.10, 0.44, 0.03), (bx, 0.22, z + dz), "grau_dunkel", rund=(0, 0)))
    t += laptop((x, 0.762, z - 0.24), (0, -90, 0), breite=0.30, tiefe=0.21, mat="metall", inhalt="plan", dicke=0.014)
    t.append(kasten("mappe", (0.22, 0.02, 0.30), (x - 0.02, 0.772, z + 0.18), "pink_hell", (0, 8, 0), rund=(0.004, 1)))
    t.append(kasten("mappe", (0.22, 0.02, 0.30), (x + 0.01, 0.792, z + 0.20), "tuerkis", (0, -6, 0), rund=(0.004, 1)))
    t += tasse((x + 0.12, 0.762, z + 0.42), "weiss", hoehe=0.08, radius=0.03)
    # Haengelampe darueber an einem Galgen? -- Pendelleuchte an Stativ
    t.append(stab("lampe_mast", (1.02, 0.48, z - 0.52), (1.02, 1.62, z - 0.52), 0.016, "grau_dunkel", seiten=6))
    t.append(stab("lampe_arm", (1.02, 1.62, z - 0.52), (x, 1.62, z - 0.05), 0.012, "grau_dunkel", seiten=4))
    t.append(zylinder("lampe_schirm", 0.14, 0.12, (x, 1.52, z - 0.05), "pink", seiten=12, radius_oben=0.05))
    t.append(zylinder("lampe_licht", 0.12, 0.004, (x, 1.458, z - 0.05), "licht_warm", seiten=12, rund=(0, 0)))
    return t


INTAKE = {
    "basis": intake_basis,
    "plaetze": {
        1: {0: intake_a1_0, 1: intake_a1_1, 2: intake_a1_2, 3: intake_a1_3},
        2: {1: intake_a2_1, 2: intake_a2_2, 3: intake_a2_3},
        3: {0: intake_a3_0, 1: intake_a3_1, 2: intake_a3_2, 3: intake_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (-0.05, 0.0, 0.25))],
    "frei": [(-0.05, 0.25, 0.22, 1.6)],
}

# =============================================================================
# Station 2: station_buffer -- Dreh (Set-Podest mit Hintergrund)
# Podest x -1,0..0,3, z -0,9..0,2; Darsteller bei (-0,35 | -0,30) auf dem
# Podest. Platz 1 (Kamera) vorn links, Platz 2 (Licht) hinten rechts,
# Platz 3 (Ton) vorn rechts.
# =============================================================================

B_POD = (-0.35, -0.35)
B_POD_H = 0.12
B_DARSTELLER = (-0.35, -0.30)


def gier_zu(von, nach):
    return math.degrees(math.atan2(nach[0] - von[0], nach[1] - von[1]))


def buffer_basis():
    t = []
    px, pz = B_POD
    t.append(kasten("podest", (1.30, B_POD_H, 1.10), (px, B_POD_H * 0.5, pz), "holz", rund=(0.02, 2)))
    t.append(kasten("belag", (1.24, 0.006, 1.04), (px, B_POD_H + 0.002, pz), "grau_mittel", rund=(0, 0)))
    t.append(kasten("kante", (1.30, 0.02, 0.012), (px, B_POD_H - 0.03, pz + 0.556), "pink", rund=(0, 0)))
    dx, dz = B_DARSTELLER
    for w in (45, -45):
        t.append(kasten("kreuz", (0.28, 0.004, 0.045), (dx, B_POD_H + 0.006, dz + 0.02), "gelb", (0, w, 0), rund=(0, 0)))
    # Hintergrund: zwei Staender, Rolle, Papierbahn mit Hohlkehle
    wz = -0.99
    for x in (-0.98, 0.28):
        t.append(stab("staender", (x, 0.02, wz), (x, 2.02, wz), 0.018, "grau_dunkel", seiten=6))
        t.append(kasten("fuss", (0.06, 0.03, 0.18), (x, 0.015, wz + 0.02), "grau_dunkel", rund=(0, 0)))
        t.append(kasten("fuss", (0.26, 0.03, 0.05), (x + (0.10 if x < 0 else -0.10), 0.015, wz + 0.01), "grau_dunkel", rund=(0, 0)))
    t.append(zylinder("rolle", 0.05, 1.20, (-0.35, 1.96, wz + 0.02), "tuerkis", seiten=10, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(kasten("bahn", (1.14, 1.70, 0.01), (-0.35, 1.06, wz + 0.05), "mint", rund=(0, 0)))
    for k, (y, z, w) in enumerate(((0.19, -0.915, 30), (0.145, -0.86, 60))):
        t.append(kasten("kehle", (1.14, 0.10, 0.01), (-0.35, y, z), "mint", (w, 0, 0), rund=(0, 0)))
    t.append(kasten("kehle_boden", (1.14, 0.006, 0.40), (-0.35, B_POD_H + 0.008, -0.62), "mint", rund=(0, 0)))
    # Sandsaecke an den Staendern, Filmklappe am Podestrand
    for x in (-0.86, 0.16):
        t.append(kugel("sandsack", 0.09, (x, 0.05, wz + 0.10), "stoff_senf", stufen=1, skala=(1.4, 0.55, 0.8)))
    t += _klappe((0.14, B_POD_H + 0.012, 0.08), (0, -20, 0), 0.9, liegend=True)
    return t


def _klappe(pos, dreh, g=1.0, liegend=False, farbe_a="pink", farbe_b="weiss"):
    """Filmklappe. pos = Mitte unten (liegend: Mitte der Unterseite)."""
    t = []
    b, h, d = 0.24 * g, 0.18 * g, 0.022 * g
    if liegend:
        dr = verkette(dreh, (-90, 0, 0))
        mitte = (pos[0], pos[1] + d * 0.5, pos[2])
    else:
        dr = dreh
        mitte = (pos[0], pos[1] + h * 0.5, pos[2])
    t.append(kasten("klappe_tafel", (b, h, d), mitte, "schwarz", dr, rund=(0.004 * g, 1)))
    for k in range(2):
        t.append(flach("klappe_zeile", b * 0.8, h * 0.08, punkt(mitte, dr, (0, -h * 0.1 - k * h * 0.22, d * 0.5 + 0.001)), dr, farbe_b, dicke=0.002))
    oben = punkt(mitte, dr, (0, h * 0.5 + h * 0.08, 0))
    t.append(kasten("klappe_leiste", (b, h * 0.15, d), oben, farbe_a, dr, rund=(0, 0)))
    for s in range(3):
        t.append(flach("klappe_streifen", b * 0.12, h * 0.15, punkt(oben, dr, (-b * 0.3 + s * b * 0.3, 0, d * 0.5 + 0.001)), verkette(dr, (0, 0, 25)), farbe_b, dicke=0.002))
    return t


# --- Platz 1: Kamera -----------------------------------------------------------

B_KAM = (-0.45, 0.72)


def _gimbal_handy(pos, gier, g=1.0):
    x, y, z = pos
    d = (0, gier, 0)
    t = [zylinder("griff", 0.028 * g, 0.16 * g, (x, y + 0.08 * g, z), "grau_dunkel", seiten=8, rund=(0, 0))]
    t.append(kasten("motor", (0.05 * g, 0.05 * g, 0.05 * g), (x, y + 0.19 * g, z), "schwarz", d, rund=(0.008, 1)))
    t.append(kasten("arm", (0.03 * g, 0.12 * g, 0.03 * g), punkt((x, y + 0.26 * g, z), d, (0.04 * g, 0, 0)), "schwarz", d, rund=(0, 0)))
    t += handy(punkt((x, y + 0.30 * g, z), d, (0, 0, 0.02 * g)), verkette(d, (0, 180, 90)), "video", gross=1.1 * g)
    t.append(kasten("led", (0.012, 0.012, 0.004), punkt((x, y + 0.12 * g, z), d, (0, 0, 0.03 * g)), "pink_led", d, rund=(0, 0)))
    return t


def buffer_a1_0():
    """Handy im Gimbal, aufgestellt auf einer Apfelkiste."""
    x, z = B_KAM
    gier = gier_zu(B_KAM, B_DARSTELLER) + 180
    t = [kasten("apfelkiste", (0.40, 0.22, 0.30), (x, 0.11, z), "holz_hell", (0, 8, 0), rund=(0.012, 1))]
    t.append(kasten("griffloch", (0.12, 0.04, 0.004), punkt((x, 0.14, z), (0, 8, 0), (0, 0, 0.151)), "holz_dunkel", (0, 8, 0), rund=(0, 0)))
    t.append(kasten("ministativ", (0.10, 0.03, 0.10), (x, 0.235, z), "grau_dunkel", rund=(0, 0)))
    t += _gimbal_handy((x, 0.25, z), gier, 1.3)
    return t


def _kamerastativ(x, z, kopf, spreizung, dicke, mat="schwarz"):
    return wg.stativ(x, z, kopf, spreizung, dicke=dicke, mat=mat, saeule_mat="grau_dunkel", y0=0.0)


def _systemkamera(pos, gier, g=1.0, akzent="pink"):
    """Kamera, pos = Mitte, Objektiv zeigt nach lokal -z (zum Motiv)."""
    d = (0, gier, 0)
    t = [kasten("gehaeuse", (0.15 * g, 0.11 * g, 0.10 * g), pos, "schwarz", d, rund=(0.015 * g, 1))]
    t.append(kasten("griff", (0.045 * g, 0.10 * g, 0.06 * g), punkt(pos, d, (-0.07 * g, -0.005, -0.01)), "grau_dunkel", d, rund=(0.012, 1)))
    ob = punkt(pos, d, (0.015 * g, -0.005, -0.12 * g))
    t.append(zylinder("objektiv", 0.042 * g, 0.14 * g, ob, "grau_dunkel", seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0.006, 1)))
    t.append(zylinder("fokusring", 0.046 * g, 0.025 * g, punkt(ob, d, (0, 0, -0.02 * g)), akzent, seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    t.append(zylinder("linse", 0.032 * g, 0.004, punkt(ob, d, (0, 0, -0.071 * g)), "schirm_blau", seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    t.append(flach("display", 0.10 * g, 0.07 * g, punkt(pos, d, (0, 0, 0.052 * g)), d, "schirm"))
    t.append(kasten("rec", (0.015, 0.008, 0.015), punkt(pos, d, (0.04 * g, 0.058 * g, 0.02)), "rot_led", d, rund=(0, 0)))
    return t


def buffer_a1_1():
    """Systemkamera auf leichtem Stativ."""
    x, z = B_KAM
    gier = gier_zu(B_KAM, B_DARSTELLER) + 180
    kopf = 1.22
    t = _kamerastativ(x, z, kopf, 0.26, 0.013)
    t.append(kasten("neiger", (0.07, 0.04, 0.07), (x, kopf + 0.02, z), "grau_dunkel", rund=(0, 0)))
    t += _systemkamera((x, kopf + 0.10, z), gier, 1.1)
    return t


def _kinokamera(pos, gier, g=1.0):
    d = (0, gier, 0)
    t = [kasten("body", (0.20 * g, 0.20 * g, 0.34 * g), pos, "grau_dunkel", d, rund=(0.02 * g, 1))]
    t.append(kasten("seite", (0.006, 0.12 * g, 0.20 * g), punkt(pos, d, (0.103 * g, 0, 0)), "pink", d, rund=(0, 0)))
    t.append(kasten("akku", (0.14 * g, 0.12 * g, 0.06 * g), punkt(pos, d, (0, -0.01, 0.20 * g)), "schwarz", d, rund=(0.01, 1)))
    t.append(kasten("henkel", (0.03 * g, 0.03 * g, 0.26 * g), punkt(pos, d, (0, 0.15 * g, 0)), "schwarz", d, rund=(0, 0)))
    for dz in (-0.10, 0.10):
        t.append(kasten("henkel_fuss", (0.03 * g, 0.05 * g, 0.03 * g), punkt(pos, d, (0, 0.115 * g, dz * g)), "schwarz", d, rund=(0, 0)))
    ob = punkt(pos, d, (0, 0, -0.26 * g))
    t.append(zylinder("objektiv", 0.065 * g, 0.18 * g, ob, "schwarz", seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0.008, 1)))
    t.append(zylinder("fokusring", 0.07 * g, 0.03 * g, punkt(ob, d, (0, 0, 0.02 * g)), "pink", seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    mb = punkt(pos, d, (0, 0, -0.39 * g))
    t.append(keil("mattebox", (0.26 * g, 0.10 * g, 0.20 * g), mb, "schwarz", verkette(d, (-90, 0, 0))))
    t.append(zylinder("linse", 0.05 * g, 0.004, punkt(ob, d, (0, 0, -0.091 * g)), "schirm_blau", seiten=12, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    mon = punkt(pos, d, (-0.17 * g, 0.12 * g, -0.02))
    dm = verkette(d, (0, -150, 0))
    t.append(kasten("kontrollmonitor", (0.18 * g, 0.12 * g, 0.025), mon, "schwarz", dm, rund=(0.008, 1)))
    t += schirm_inhalt(mon, dm, 0.16 * g, 0.10 * g, "video", tiefe=0.0135)
    t.append(kasten("tally", (0.03, 0.02, 0.02), punkt(pos, d, (0.06 * g, 0.11 * g, -0.12 * g)), "rot_led", d, rund=(0, 0)))
    return t


def buffer_a1_2():
    """Kinokamera mit Mattebox auf schwerem Stativ mit Bodenspinne."""
    x, z = B_KAM
    gier = gier_zu(B_KAM, B_DARSTELLER) + 180
    kopf = 1.18
    t = _kamerastativ(x, z, kopf, 0.34, 0.022)
    for i in range(3):
        w = math.radians(30 + 120 * i)
        t.append(stab("spinne", (x, 0.03, z), (x + math.cos(w) * 0.34, 0.03, z + math.sin(w) * 0.34), 0.012, "pink", seiten=4))
    t.append(kasten("neiger", (0.12, 0.08, 0.12), (x, kopf + 0.04, z), "grau_dunkel", rund=(0.012, 1)))
    t.append(stab("schwenkarm", (x, kopf + 0.05, z), punkt((x, kopf - 0.02, z), (0, gier, 0), (0.05, 0, 0.36)), 0.012, "schwarz", seiten=4))
    t += _kinokamera((x, kopf + 0.20, z), gier)
    return t


def buffer_a1_3():
    """Kamera-Kran: Dolly, Saeule, langer Arm mit Gegengewicht, Kinokamera
    ueber dem Darsteller, Regiemonitor am Fuss."""
    bx, bz = -0.72, 0.70
    t = []
    t.append(kasten("dolly", (0.42, 0.10, 0.42), (bx, 0.10, bz), "grau_dunkel", (0, 45, 0), rund=(0.02, 1)))
    for k in range(4):
        w = math.radians(45 + 90 * k)
        t.append(zylinder("rad", 0.05, 0.04, (bx + math.cos(w) * 0.21, 0.05, bz + math.sin(w) * 0.21), "schwarz", seiten=8, dreh=(0, 45 + 90 * k, 90), rund=(0, 0)))
    t.append(zylinder("saeule", 0.07, 1.10, (bx, 0.70, bz), "pink", seiten=8, rund=(0, 0)))
    dreh_p = (bx, 1.30, bz)
    t.append(kasten("drehkopf", (0.16, 0.10, 0.16), (bx, 1.28, bz), "schwarz", rund=(0.02, 1)))
    spitze = Vector((-0.38, 2.10, 0.08))
    p = Vector(dreh_p)
    r = (spitze - p).normalized()
    hinten = p - r * 0.36
    for off in (-0.035, 0.035):
        quer = Vector((r.z, 0.0, -r.x)).normalized() * off
        t.append(stab("arm", tuple(hinten + quer), tuple(spitze + quer), 0.018, "metall", seiten=6))
    for k in range(1, 6):
        a = hinten + (spitze - hinten) * (k / 6.0)
        t.append(stab("strebe", tuple(a + Vector((0, -0.04, 0))), tuple(a + Vector((0, 0.04, 0))), 0.008, "grau_dunkel", seiten=4))
    t.append(kasten("gewicht", (0.16, 0.18, 0.16), tuple(hinten - r * 0.06), "schwarz", (0, gier_zu((bx, bz), (spitze.x, spitze.z)), 0), rund=(0.02, 1)))
    t.append(stab("haenger", tuple(spitze), tuple(spitze - Vector((0, 0.10, 0))), 0.015, "grau_dunkel", seiten=6))
    gier = gier_zu((spitze.x, spitze.z), B_DARSTELLER) + 180
    t += _kinokamera((spitze.x, spitze.y - 0.20, spitze.z + 0.02), gier, 0.8)
    # Regiemonitor auf kleinem Staender neben dem Dolly
    mx, mz = -0.96, 0.40
    t.append(stab("mon_mast", (mx, 0.02, mz), (mx, 1.00, mz), 0.015, "grau_dunkel", seiten=6))
    t.append(kasten("mon_fuss", (0.18, 0.02, 0.18), (mx, 0.01, mz), "grau_dunkel", rund=(0, 0)))
    t += schirm((mx + 0.01, 1.12, mz), (-10, 60, 0), 0.30, 0.20, "video")
    return t


# --- Platz 2: Licht ------------------------------------------------------------

def _softbox(pos_boden, hoehe, groesse, farbe_rahmen="schwarz"):
    x, z = pos_boden
    gier = gier_zu(pos_boden, B_DARSTELLER)
    t = wg.stativ(x, z, hoehe - 0.10, 0.24, dicke=0.014, y0=0.0)
    kopf = (x, hoehe, z)
    d = (-90 + 10, gier, 0)
    t.append(keil("softbox", (groesse, groesse * 0.55, groesse * 0.72), punkt(kopf, (0, gier, 0), (0, 0, -groesse * 0.1)), farbe_rahmen, d))
    front = punkt(kopf, (10, gier, 0), (0, 0, groesse * 0.19))
    t.append(kasten("diffusor", (groesse * 0.94, groesse * 0.68, 0.012), front, "licht_weiss", (10, gier, 0), rund=(0, 0)))
    t.append(kasten("diffusor_rand", (groesse * 0.98, groesse * 0.72, 0.008), punkt(front, (10, gier, 0), (0, 0, -0.008)), "pink", (10, gier, 0), rund=(0, 0)))
    return t


def buffer_a2_0():
    """Eine Softbox."""
    return _softbox((0.66, -0.58), 1.40, 0.50)


def buffer_a2_1():
    """Zwei Softboxen."""
    return _softbox((0.56, -0.72), 1.46, 0.52) + _softbox((0.82, -0.08), 1.30, 0.46)


def _ledwand(pos_boden, hoehe, b, h):
    x, z = pos_boden
    gier = gier_zu(pos_boden, B_DARSTELLER)
    d = (0, gier, 0)
    mitte = (x, hoehe, z)
    t = [kasten("ledrahmen", (b, h, 0.05), mitte, "grau_dunkel", d, rund=(0.012, 1))]
    for r in range(3):
        for s in range(4):
            mat = "licht_weiss" if (r + s) % 3 else "licht_warm"
            t.append(flach("led_kachel", b * 0.21, h * 0.27, punkt(mitte, d, (-b * 0.36 + s * b * 0.24, h * 0.3 - r * h * 0.3, 0.027)), d, mat))
    t.append(kasten("buegel", (b + 0.08, 0.03, 0.03), punkt(mitte, d, (0, -h * 0.5 - 0.05, 0)), "grau_dunkel", d, rund=(0, 0)))
    for s in (-1, 1):
        t.append(stab("buegel_s", punkt(mitte, d, (s * (b * 0.5 + 0.04), -h * 0.5 - 0.05, 0)), punkt(mitte, d, (s * (b * 0.5 + 0.04), 0, 0)), 0.012, "grau_dunkel", seiten=4))
    t += wg.stativ(x, z, hoehe - h * 0.5 - 0.05, 0.28, dicke=0.016, y0=0.0)
    return t


def _roehre(x, z, hoehe, mat="pink_led"):
    t = [zylinder("roehre", 0.03, hoehe, (x, 0.08 + hoehe * 0.5, z), mat, seiten=8, rund=(0, 0))]
    t.append(zylinder("roehre_fuss", 0.10, 0.03, (x, 0.015, z), "grau_dunkel", seiten=10, rund=(0, 0)))
    t.append(stab("roehre_stiel", (x, 0.03, z), (x, 0.09, z), 0.015, "grau_dunkel", seiten=4))
    return t


def buffer_a2_2():
    """LED-Wand auf Stativ plus pinke Leuchtroehre."""
    return _ledwand((0.68, -0.62), 1.40, 0.80, 0.56) + _roehre(0.86, -0.06, 1.10)


def buffer_a2_3():
    """Lichtrig: Traverse ueber dem Set auf zwei Masten, vier Scheinwerfer,
    LED-Wand und Leuchtroehre."""
    t = _ledwand((0.72, -0.40), 1.30, 0.62, 0.44) + _roehre(0.90, 0.00, 1.10)
    a = Vector((0.90, 2.22, -0.86))
    b = Vector((-1.06, 2.22, -0.62))
    for m in (a, b):
        t.append(stab("mast", (m.x, 0.02, m.z), (m.x, m.y + 0.04, m.z), 0.026, "grau_dunkel", seiten=6))
        t.append(kasten("mastfuss", (0.07, 0.04, 0.20), (m.x, 0.02, m.z), "grau_dunkel", rund=(0.01, 1)))
    for dy in (-0.05, 0.05):
        for dz in (-0.05, 0.05):
            t.append(stab("traverse", (a.x, a.y + dy, a.z + dz), (b.x, b.y + dy, b.z + dz), 0.012, "metall", seiten=4))
    for k in range(9):
        p0 = a + (b - a) * (k / 9.0)
        p1 = a + (b - a) * ((k + 1) / 9.0)
        t.append(stab("diagonale", (p0.x, p0.y - 0.05, p0.z), (p1.x, p1.y + 0.05, p1.z), 0.006, "metall", seiten=3))
    for k, f in enumerate((0.18, 0.40, 0.66, 0.86)):
        p = a + (b - a) * f
        ziel = Vector((B_DARSTELLER[0], 1.2, B_DARSTELLER[1]))
        t.append(stab("buegel", (p.x, p.y - 0.06, p.z), (p.x, p.y - 0.16, p.z), 0.01, "grau_dunkel", seiten=4))
        kopf = Vector((p.x, p.y - 0.24, p.z + 0.02))
        r = (ziel - kopf).normalized()
        t.append(stab("spot", tuple(kopf - r * 0.10), tuple(kopf + r * 0.10), 0.07, "schwarz", seiten=8))
        t.append(stab("spot_licht", tuple(kopf + r * 0.10), tuple(kopf + r * 0.106), 0.06, "pink_led" if k % 2 else "licht_warm", seiten=8))
    return t


# --- Platz 3: Ton --------------------------------------------------------------

B_TON = (0.58, 0.66)


def _koffer_mikro():
    x, z = B_TON
    t = [kasten("koffer", (0.34, 0.07, 0.24), (x, 0.035, z), "schwarz", (0, -15, 0), rund=(0.012, 1))]
    t.append(kasten("schaum", (0.30, 0.004, 0.20), (x, 0.072, z), "grau_dunkel", (0, -15, 0), rund=(0, 0)))
    dk = (-70, -15, 0)
    t.append(kasten("deckel", (0.34, 0.24, 0.03), punkt((x, 0.07, z), (0, -15, 0), (0, 0.11, -0.14)), "schwarz", dk, rund=(0.01, 1)))
    t.append(kasten("sender", (0.07, 0.03, 0.10), punkt((x, 0.09, z), (0, -15, 0), (-0.07, 0, 0)), "grau_mittel", (0, -15, 0), rund=(0.006, 1)))
    t.append(kasten("sender_led", (0.02, 0.006, 0.02), punkt((x, 0.108, z), (0, -15, 0), (-0.07, 0, 0.02)), "pink_led", (0, -15, 0), rund=(0, 0)))
    t.append(kugel("ansteckmikro", 0.022, punkt((x, 0.095, z), (0, -15, 0), (0.07, 0, 0)), "schwarz", stufen=1))
    t.append(stab("kabel", punkt((x, 0.085, z), (0, -15, 0), (0.07, 0, 0)), punkt((x, 0.085, z), (0, -15, 0), (-0.03, 0, 0.04)), 0.005, "pink", seiten=3))
    return t


def buffer_a3_0():
    """Offener Koffer mit Ansteckmikro und Funksender."""
    return _koffer_mikro()


def _tonangel(hoehe, spitze, fuss=B_TON):
    x, z = fuss
    t = wg.stativ(x, z, hoehe, 0.26, dicke=0.015, mat="schwarz", saeule_mat="grau_dunkel", y0=0.0)
    p = Vector((x, hoehe, z))
    s = Vector(spitze)
    r = (s - p).normalized()
    t.append(kugel("gelenk", 0.03, tuple(p), "grau_dunkel", stufen=1))
    t.append(stab("angel", tuple(p - r * 0.40), tuple(s), 0.013, "metall", seiten=6))
    t.append(zylinder("gegengewicht", 0.04, 0.10, tuple(p - r * 0.40), "schwarz", seiten=8, rund=(0, 0)))
    t.append(stab("abhaenger", tuple(s), tuple(s - Vector((0, 0.08, 0))), 0.008, "grau_dunkel", seiten=4))
    t.append(kasten("fell", (0.09, 0.09, 0.30), tuple(s - Vector((0, 0.13, 0))), "grau_mittel", (0, gier_zu((s.x, s.z), (x, z)), 0), rund=(0.03, 1)))
    return t


def buffer_a3_1():
    """Tonangel mit Fell ueber dem Darsteller, Koffer am Boden."""
    return _tonangel(1.60, (-0.05, 2.02, -0.02)) + _koffer_mikro()


def buffer_a3_2():
    """Rollwagen mit Tonpult und Kopfhoerern, dazu die Tonangel."""
    t = _tonangel(1.60, (-0.05, 2.02, -0.02))
    x, z = 0.62, 0.78
    d = (0, -20, 0)
    t.append(kasten("wagen_platte", (0.62, 0.04, 0.38), (x, 0.74, z), "grau_dunkel", d, rund=(0.01, 1)))
    t.append(kasten("wagen_boden", (0.56, 0.03, 0.32), (x, 0.24, z), "grau_dunkel", d, rund=(0, 0)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            ec = punkt((x, 0.40, z), d, (sx * 0.28, 0, sz * 0.16))
            t.append(stab("wagen_bein", (ec[0], 0.05, ec[2]), (ec[0], 0.73, ec[2]), 0.013, "metall", seiten=4))
            t.append(zylinder("wagen_rolle", 0.03, 0.03, (ec[0], 0.03, ec[2]), "schwarz", seiten=6, rund=(0, 0)))
    pult = punkt((x, 0.80, z), d, (0, 0, 0))
    dp = verkette(d, (14, 0, 0))
    t.append(kasten("pult", (0.52, 0.06, 0.30), pult, "schwarz", dp, rund=(0.01, 1)))
    for k in range(6):
        t.append(kasten("fader", (0.03, 0.012, 0.10), punkt(pult, dp, (-0.19 + k * 0.075, 0.034, 0.05)), "pink" if k == 2 else "grau_hell", dp, rund=(0, 0)))
        t.append(kasten("pegel", (0.03, 0.004, 0.06), punkt(pult, dp, (-0.19 + k * 0.075, 0.032, -0.08)), "led_gruen" if k % 2 else "pink_led", dp, rund=(0, 0)))
    t.append(kasten("recorder", (0.20, 0.06, 0.24), punkt((x, 0.285, z), d, (0, 0, 0)), "grau_mittel", d, rund=(0.01, 1)))
    hk = punkt((x, 0.78, z), d, (0.20, 0.07, -0.02))
    t.append(ring("kopfhoerer", 0.08, 0.012, hk, "schwarz", (90, -20, 0), segmente=10, quer=4, anteil=0.5))
    return t


def buffer_a3_3():
    """Tonkabine mit Schaumstoff, Fenster und Aufnahmelicht, davor die
    Tonangel."""
    t = _tonangel(1.66, (-0.08, 2.04, -0.02), fuss=(0.04, 0.66))
    x, z = 0.68, 0.78
    b, h, d = 0.64, 1.46, 0.48
    t.append(kasten("kabine", (b, h, d), (x, h * 0.5 + 0.02, z), "grau_dunkel", rund=(0.03, 2)))
    t.append(kasten("kabine_sockel", (b + 0.04, 0.04, d + 0.04), (x, 0.02, z), "schwarz", rund=(0.01, 1)))
    t.append(kasten("dach", (b + 0.04, 0.05, d + 0.04), (x, h + 0.045, z), "schwarz", rund=(0.012, 1)))
    # Tuer auf +z mit Fenster
    t.append(kasten("tuer", (0.44, 1.30, 0.02), (x - 0.05, 0.70, z + d * 0.5 + 0.01), "grau_mittel", rund=(0, 0)))
    t.append(kasten("fenster", (0.28, 0.32, 0.02), (x - 0.05, 1.04, z + d * 0.5 + 0.022), "glas", rund=(0, 0)))
    t.append(kasten("fenster_innen", (0.24, 0.28, 0.004), (x - 0.05, 1.04, z + d * 0.5 + 0.012), "schirm_pink", rund=(0, 0)))
    t.append(kasten("klinke", (0.08, 0.02, 0.03), (x + 0.10, 0.70, z + d * 0.5 + 0.035), "metall", rund=(0, 0)))
    # Noppen auf der Seite +x
    for r in range(3):
        for s in range(2):
            t.append(kasten("noppe", (0.03, 0.34, 0.18), (x + b * 0.5 + 0.015, 0.32 + r * 0.42, z - 0.10 + s * 0.20),
                            "pink" if (r + s) % 2 else "grau_mittel", rund=(0, 0)))
    # Aufnahmelicht
    t.append(kasten("onair", (0.30, 0.10, 0.04), (x - 0.06, h + 0.13, z + 0.12), "schwarz", rund=(0.01, 1)))
    t.append(kasten("onair_licht", (0.26, 0.06, 0.004), (x - 0.06, h + 0.13, z + 0.142), "rot_led", rund=(0, 0)))
    return t


BUFFER = {
    "basis": buffer_basis,
    "plaetze": {
        1: {0: buffer_a1_0, 1: buffer_a1_1, 2: buffer_a1_2, 3: buffer_a1_3},
        2: {0: buffer_a2_0, 1: buffer_a2_1, 2: buffer_a2_2, 3: buffer_a2_3},
        3: {0: buffer_a3_0, 1: buffer_a3_1, 2: buffer_a3_2, 3: buffer_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (B_DARSTELLER[0], B_POD_H, B_DARSTELLER[1]))],
    "frei": [(B_DARSTELLER[0], B_DARSTELLER[1], 0.26, 1.72)],
}

# =============================================================================
# Station 3: station_processing -- Schnitt (Schreibtisch mit Stuhl)
# Platte 1,4 x 0,7 auf 0,74 m, z -1,05..-0,35. Stuhl vor dem Tisch (Sitz
# y 0,48 bei (0 | 0,05)). Platz 1 Rechner links neben/unter dem Tisch,
# Platz 2 Monitore hinten auf der Platte, Platz 3 Farbe rechts neben dem Tisch.
# =============================================================================

P_H = 0.74
P_AUF = P_H + 0.002
P_Z = -0.70
P_SITZ = (0.0, 0.48, 0.05)


def processing_basis():
    t = []
    t.append(kasten("platte", (1.40, 0.04, 0.70), (0.0, P_H - 0.02, P_Z), "holz_hell", rund=(0.014, 2)))
    t.append(kasten("kante", (1.40, 0.012, 0.012), (0.0, P_H - 0.03, P_Z + 0.352), "pink", rund=(0, 0)))
    for x in (-0.64, 0.64):
        t.append(kasten("wange", (0.04, P_H - 0.04, 0.06), (x, (P_H - 0.04) * 0.5, P_Z - 0.26), "grau_dunkel", rund=(0.01, 1)))
        t.append(kasten("wange", (0.04, P_H - 0.04, 0.06), (x, (P_H - 0.04) * 0.5, P_Z + 0.26), "grau_dunkel", rund=(0.01, 1)))
        t.append(kasten("kufe", (0.05, 0.03, 0.66), (x, 0.015, P_Z), "grau_dunkel", rund=(0.008, 1)))
    t.append(kasten("traverse", (1.24, 0.05, 0.03), (0.0, P_H - 0.08, P_Z - 0.26), "grau_dunkel", rund=(0, 0)))
    # Tastatur, Maus, Kopfhoerer, Tasse
    t += wg._tastatur((0.0, P_AUF, -0.50), (0, 0, 0), 0.46, 0.15, mat="schwarz", tasten="weiss")
    t.append(kasten("mauspad", (0.28, 0.004, 0.22), (0.40, P_AUF + 0.002, -0.52), "pink", rund=(0, 0)))
    t += wg._maus((0.40, P_AUF + 0.004, -0.52), "schwarz", akzent="pink_led")
    t += tasse((-0.44, P_AUF, -0.50), "weiss", hoehe=0.09, radius=0.036)
    t.append(ring("kopfhoerer", 0.09, 0.013, (-0.50, P_AUF + 0.02, -0.82), "schwarz", (0, 30, 0), segmente=10, quer=4, anteil=0.5))
    t += stuhl_buero(P_SITZ[0], P_SITZ[1], P_SITZ[2], 0.0, mat="grau_dunkel", akzent="pink")
    # Kabel zur Steckdosenleiste
    t.append(kasten("leiste", (0.30, 0.045, 0.07), (0.10, 0.023, -0.98), "weiss", rund=(0.01, 1)))
    t.append(kasten("schalter", (0.03, 0.01, 0.03), (0.21, 0.05, -0.98), "rot", rund=(0, 0)))
    return t


# --- Platz 1: Rechner ----------------------------------------------------------

R_X, R_Z = -0.90, -0.72


def processing_a1_0():
    """Der Gaming-PC aus der WG: schwarzer Tower mit Leuchtstreifen und
    zwei bunten Luefterringen hinter der Glasseite."""
    return tower(R_X, R_Z, 0.22, 0.50, 0.46, led="rgb_cyan", luefter=("rgb_magenta", "rgb_cyan"))


def _wasser_pc(x, z):
    t = tower(x, z, 0.26, 0.58, 0.50, led="pink_led", luefter=("pink_led", "pink_led"))
    gx = x + 0.13 + 0.012
    t.append(zylinder("ausgleich", 0.035, 0.22, (gx + 0.01, 0.30, z - 0.12), "pink_led", seiten=8, rund=(0, 0)))
    t.append(stab("schlauch", (gx + 0.012, 0.42, z - 0.12), (gx + 0.012, 0.50, z + 0.10), 0.011, "pink_led", seiten=4))
    t.append(stab("schlauch", (gx + 0.012, 0.18, z - 0.12), (gx + 0.012, 0.12, z + 0.12), 0.011, "pink_led", seiten=4))
    t.append(kasten("radiator", (0.22, 0.05, 0.42), (x, 0.61, z), "grau_dunkel", rund=(0.008, 1)))
    for k in range(3):
        t.append(zylinder("rad_luefter", 0.055, 0.006, (x, 0.638, z - 0.14 + k * 0.14), "pink_led" if k == 1 else "grau_mittel", seiten=10, rund=(0, 0)))
    return t


def processing_a1_1():
    """PC mit Wasserkuehlung: pinke Schlaeuche, Ausgleichsbehaelter, Radiator."""
    return _wasser_pc(R_X, R_Z)


def processing_a1_2():
    """Doppel-PC: der wassergekuehlte daneben, ein zweiter unter dem Tisch."""
    t = _wasser_pc(R_X, R_Z)
    t += tower(-0.40, -0.82, 0.22, 0.52, 0.42, led="rgb_cyan", luefter=("rgb_cyan", "pink_led"))
    t.append(stab("kabel", (-0.29, 0.10, -0.82), (-0.77, 0.10, -0.80), 0.008, "pink", seiten=3))
    return t


def processing_a1_3():
    """Schnitt-Workstation: grosses Gehaeuse mit Gitterfront und Griffen,
    Render-Einheit unter dem Tisch, USV."""
    t = []
    x, z = -0.89, -0.70
    b, h, d = 0.30, 0.78, 0.58
    m = (x, h * 0.5 + 0.03, z)
    t.append(kasten("workstation", (b, h, d), m, "grau_mittel", rund=(0.02, 2)))
    t.append(kasten("front", (b - 0.04, h - 0.10, 0.012), (x, m[1] - 0.02, z + d * 0.5 + 0.004), "schwarz", rund=(0, 0)))
    for k in range(6):
        t.append(kasten("gitter", (b - 0.08, 0.018, 0.006), (x, 0.14 + k * 0.10, z + d * 0.5 + 0.012), "pink_led" if k in (1, 4) else "grau_dunkel", rund=(0, 0)))
    for s in (-1, 1):
        t.append(stab("griff", (x + s * 0.10, h + 0.03, z - 0.18), (x + s * 0.10, h + 0.03, z + 0.18), 0.012, "metall", seiten=4))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(zylinder("rolle", 0.025, 0.03, (x + sx * 0.11, 0.015, z + sz * 0.22), "schwarz", seiten=6, rund=(0, 0)))
    t.append(kasten("seite_led", (0.006, h - 0.2, 0.02), (x + b * 0.5 + 0.004, m[1], z + d * 0.5 - 0.04), "pink_led", rund=(0, 0)))
    t += tower(-0.40, -0.82, 0.24, 0.56, 0.42, led="pink_led", luefter=("pink_led", "rgb_cyan"))
    t.append(kasten("usv", (0.16, 0.24, 0.34), (-0.18, 0.12, -0.84), "schwarz", rund=(0.012, 1)))
    t.append(kasten("usv_anzeige", (0.08, 0.04, 0.004), (-0.18, 0.19, -0.668), "led_gruen", rund=(0, 0)))
    t.append(stab("kabel", (-0.28, 0.08, -0.82), (-0.74, 0.08, -0.80), 0.008, "pink", seiten=3))
    return t


# --- Platz 2: Monitor ----------------------------------------------------------

def processing_a2_0():
    """Ein Monitor."""
    return monitor((0.0, P_AUF, -0.88), (0, 0, 0), 0.58, 0.35, "video", fuss_hoehe=0.10)


def processing_a2_1():
    """Zwei Monitore."""
    t = []
    for s, art in ((-1, "video"), (1, "plan")):
        t += monitor((s * 0.31, P_AUF, -0.86), (0, -s * 10, 0), 0.58, 0.35, art, fuss_hoehe=0.10)
    return t


def processing_a2_2():
    """Curved-Monitor aus fuenf Segmenten, Lichtleiste oben."""
    t = []
    y = P_AUF + 0.42
    t.append(kasten("fuss", (0.40, 0.02, 0.20), (0.0, P_AUF + 0.01, -0.90), "grau_dunkel", rund=(0.008, 1)))
    t.append(kasten("hals", (0.06, 0.26, 0.04), (0.0, P_AUF + 0.14, -0.94), "grau_dunkel", rund=(0.008, 1)))
    arten = ("balken", "video", "video", "video", "kurve")
    for i in range(-2, 3):
        a = math.radians(i * 12)
        pos = (math.sin(a) * 1.0, y, 0.10 - math.cos(a) * 1.0 - 0.02)
        d = (0, -i * 12, 0)
        t.append(kasten("segment", (0.215, 0.40, 0.035), pos, "schwarz", d, rund=(0, 0)))
        t.append(flach("bild", 0.20, 0.34, punkt(pos, d, (0, 0, 0.019)), d, "schirm"))
        t.append(flach("inhalt", 0.17, 0.20 if i else 0.26, punkt(pos, d, (0, 0.03, 0.022)), d, "schirm_blau" if i % 2 else "schirm_pink"))
        t.append(flach("zeitleiste", 0.19, 0.03, punkt(pos, d, (0, -0.12, 0.022)), d, "schirm_orange"))
        t.append(kasten("lichtleiste", (0.20, 0.015, 0.02), punkt(pos, d, (0, 0.215, -0.01)), "pink_led", d, rund=(0, 0)))
    return t


def processing_a2_3():
    """Monitorwand: vier grosse Monitore an einer Saeule, Hintergrundlicht."""
    t = []
    sz = -0.98
    t.append(kasten("klemme", (0.16, 0.04, 0.10), (0.0, P_AUF + 0.02, sz), "grau_dunkel", rund=(0.008, 1)))
    t.append(stab("saeule", (0.0, P_AUF + 0.04, sz), (0.0, 1.78, sz), 0.028, "metall", seiten=8))
    t.append(kasten("traeger", (1.20, 0.05, 0.04), (0.0, 1.22, sz + 0.02), "grau_dunkel", rund=(0, 0)))
    t.append(kasten("backlight", (1.24, 0.80, 0.01), (0.0, 1.22, sz - 0.01), "pink_led", rund=(0, 0)))
    arten = (("video", "kurve"), ("video", "plan"))
    for r, y in enumerate((1.42, 1.02)):
        for s in (-1, 1):
            t += schirm((s * 0.305, y, -0.93), (0, -s * 6, 0), 0.60, 0.38, arten[r][(s + 1) // 2], d=0.03)
    return t


# --- Platz 3: Farbe ------------------------------------------------------------

def _beistelltisch(x, z, b, tiefe, h, mat="grau_dunkel"):
    t = [kasten("tisch", (b, 0.03, tiefe), (x, h - 0.015, z), "holz_hell", rund=(0.01, 1))]
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(stab("tischbein", (x + sx * (b * 0.5 - 0.03), 0.0, z + sz * (tiefe * 0.5 - 0.03)),
                          (x + sx * (b * 0.5 - 0.03), h - 0.03, z + sz * (tiefe * 0.5 - 0.03)), 0.015, mat, seiten=4))
    t.append(kasten("ablage", (b - 0.04, 0.02, tiefe - 0.04), (x, 0.18, z), mat, rund=(0, 0)))
    return t


def _farbpult(pos, gier, g=1.0):
    d = (0, gier, 0)
    dp = verkette(d, (12, 0, 0))
    t = [kasten("farbpult", (0.30 * g, 0.06, 0.20 * g), pos, "schwarz", dp, rund=(0.012, 1))]
    for k, mat in enumerate(("rot", "gruen_hell", "blau")):
        p = punkt(pos, dp, ((-0.09 + k * 0.09) * g, 0.035, -0.02 * g))
        t.append(ring("farbring", 0.030 * g, 0.008, p, "grau_mittel", dp, segmente=10, quer=3))
        t.append(kugel("trackball", 0.022 * g, p, mat, stufen=1))
    t.append(kasten("pult_leiste", (0.26 * g, 0.008, 0.02), punkt(pos, dp, (0, 0.032, 0.07 * g)), "pink_led", dp, rund=(0, 0)))
    return t


def processing_a3_1():
    """Farbpult mit drei Kugeln auf einem Beistelltisch."""
    t = _beistelltisch(0.90, -0.30, 0.32, 0.46, 0.66)
    t += _farbpult((0.90, 0.69, -0.28), -90)
    return t


def _referenzmonitor(pos, gier, b, h):
    d = (0, gier, 0)
    t = schirm(pos, d, b, h, "video", rahmen="schwarz", d=0.05)
    for s in (-1, 1):
        t.append(kasten("blende", (0.02, h, 0.10), punkt(pos, d, (s * (b * 0.5 + 0.01), 0, 0.04)), "schwarz", verkette(d, (0, s * 20, 0)), rund=(0, 0)))
    t.append(kasten("blende_oben", (b, 0.02, 0.10), punkt(pos, d, (0, h * 0.5 + 0.01, 0.04)), "schwarz", verkette(d, (-15, 0, 0)), rund=(0, 0)))
    return t


def processing_a3_2():
    """Farbpult und ein Referenzmonitor mit Blende auf Staender."""
    t = processing_a3_1()
    mx, mz = 0.90, -0.84
    gier = -45
    t.append(kasten("mon_fuss", (0.26, 0.02, 0.26), (mx, 0.01, mz), "grau_dunkel", rund=(0.008, 1)))
    t.append(stab("mon_mast", (mx, 0.02, mz), (mx, 1.02, mz), 0.022, "metall", seiten=6))
    t += _referenzmonitor((mx, 1.18, mz), gier, 0.44, 0.28)
    return t


def processing_a3_3():
    """Grading-Suite: langer Beistelltisch, grosses Farbpult, grosser
    Referenzmonitor mit pinkem Hintergrundlicht, Lautsprecher."""
    t = _beistelltisch(0.90, -0.52, 0.34, 1.00, 0.70)
    t += _farbpult((0.90, 0.73, -0.20), -90, g=1.25)
    mx, mz = 0.86, -0.80
    gier = -50
    t.append(kasten("mon_fuss", (0.20, 0.02, 0.14), (mx, 0.71, mz), "grau_dunkel", (0, gier, 0), rund=(0, 0)))
    t.append(kasten("mon_hals", (0.05, 0.26, 0.03), punkt((mx, 0.84, mz), (0, gier, 0), (0, 0, -0.04)), "grau_dunkel", (0, gier, 0), rund=(0, 0)))
    t += _referenzmonitor((mx, 1.22, mz), gier, 0.46, 0.30)
    t.append(flach("bias", 0.52, 0.38, punkt((mx, 1.22, mz), (0, gier, 0), (0, 0, -0.05)), (0, gier, 0), "pink_led"))
    t.append(kasten("lautsprecher", (0.12, 0.20, 0.14), (0.92, 0.82, -0.52), "schwarz", (0, -70, 0), rund=(0.012, 1)))
    t.append(zylinder("membran", 0.035, 0.004, punkt((0.92, 0.80, -0.52), (0, -70, 0), (0, 0, 0.072)), "pink", seiten=10, dreh=(90, -70, 0), rund=(0, 0)))
    t.append(kasten("graukarte", (0.14, 0.10, 0.004), (0.90, 0.19 + 0.06, -0.55), "grau_mittel", (0, -90, 0), rund=(0, 0)))
    return t


PROCESSING = {
    "basis": processing_basis,
    "plaetze": {
        1: {0: processing_a1_0, 1: processing_a1_1, 2: processing_a1_2, 3: processing_a1_3},
        2: {0: processing_a2_0, 1: processing_a2_1, 2: processing_a2_2, 3: processing_a2_3},
        3: {1: processing_a3_1, 2: processing_a3_2, 3: processing_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("sitz", P_SITZ)],
}

# =============================================================================
# Station 4: station_transport -- Render-Server (Metallregal im Container)
# Containerwand hinten (z -1,10..-1,04), Regal x -0,55..0,55, z -1,0..-0,56,
# Boeden bei y 0,08 / 0,58 / 1,08 / 1,58. Platz 1 Server links, Platz 2
# Speicher im Regal, Platz 3 Kuehlung rechts.
# =============================================================================

T_BOEDEN = (0.08, 0.58, 1.08, 1.58)
T_Z = -0.78
T_TIEFE = 0.44


def t_auf(ebene):
    return T_BOEDEN[ebene] + 0.017


def transport_basis():
    t = []
    # Containerwand mit Sicken
    t.append(kasten("wand", (2.20, 2.30, 0.04), (0.0, 1.15, -1.08), "container", rund=(0, 0)))
    for k in range(9):
        t.append(kasten("sicke", (0.10, 2.24, 0.02), (-0.96 + k * 0.24, 1.15, -1.05), "container_d", rund=(0, 0)))
    t.append(kasten("wand_kante", (2.20, 0.06, 0.06), (0.0, 2.30, -1.068), "container_d", rund=(0, 0)))
    # Regal
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(kasten("pfosten", (0.035, 1.80, 0.035), (sx * 0.535, 0.90, T_Z + sz * 0.205), "metall", rund=(0, 0)))
    for y in T_BOEDEN:
        t.append(kasten("boden", (1.10, 0.03, T_TIEFE), (0.0, y, T_Z), "grau_mittel", rund=(0.006, 1)))
        t.append(kasten("boden_kante", (1.10, 0.012, 0.006), (0.0, y, T_Z + T_TIEFE * 0.5 + 0.004), "pink", rund=(0, 0)))
    # Bodenmarkierung und Lampe
    for k in range(4):
        t.append(kasten("warnstreifen", (0.16, 0.004, 0.08), (-0.36 + k * 0.24, 0.002, -0.40), "gelb" if k % 2 == 0 else "schwarz", (0, 45, 0), rund=(0, 0)))
    t.append(kasten("lampe", (0.50, 0.06, 0.10), (0.0, 2.08, -0.99), "grau_dunkel", rund=(0.01, 1)))
    t.append(kasten("lampe_licht", (0.46, 0.012, 0.08), (0.0, 2.045, -0.99), "licht_weiss", rund=(0, 0)))
    t.append(kasten("kabelkanal", (0.06, 0.06, 0.60), (0.0, 0.03, -0.30), "grau_dunkel", rund=(0, 0)))
    return t


# --- Platz 1: Server -----------------------------------------------------------

S_X = -0.86


def _einschub(pos, b, h, d=0.02, leds=3):
    """Serverfront, pos = Mitte der Frontflaeche, zeigt nach +x."""
    dr = (0, 90, 0)
    t = [kasten("einschub", (b, h, d), pos, "grau_dunkel", dr, rund=(0, 0))]
    for k in range(min(leds, 2)):
        mat = "pink_led" if k == 0 else "led_gruen"
        t.append(kasten("led", (0.004, 0.012, 0.012), (pos[0] + d * 0.5 + 0.002, pos[1], pos[2] - b * 0.4 + k * 0.035), mat, rund=(0, 0)))
    t.append(kasten("schlitz", (0.004, h * 0.3, b * 0.45), (pos[0] + d * 0.5 + 0.002, pos[1], pos[2] + b * 0.18), "schwarz", rund=(0, 0)))
    return t


def _rack(z, h, einschuebe, glut=False):
    b, d = 0.60, 0.44
    x = S_X
    t = [kasten("rack", (d, h, b), (x, h * 0.5 + 0.04, z), "schwarz", rund=(0.02, 1))]
    t.append(kasten("rack_innen", (0.01, h - 0.10, b - 0.08), (x + d * 0.5 + 0.004, h * 0.5 + 0.04, z), "grau_dunkel", rund=(0, 0)))
    for k in range(einschuebe):
        y = 0.12 + k * ((h - 0.16) / einschuebe) + (h - 0.16) / einschuebe * 0.5
        t += _einschub((x + d * 0.5 + 0.012, y, z), b - 0.12, (h - 0.16) / einschuebe * 0.7, leds=3 if k % 2 == 0 else 2)
    for sz in (-1, 1):
        t.append(zylinder("rolle", 0.02, 0.04, (x, 0.02, z + sz * 0.24), "schwarz", seiten=6, rund=(0, 0)))
        if glut:
            t.append(kasten("glutkante", (0.006, h - 0.06, 0.012), (x + d * 0.5 + 0.004, h * 0.5 + 0.04, z + sz * (b * 0.5 - 0.01)), "pink_led", rund=(0, 0)))
    return t


def transport_a1_0():
    """Ein einzelner Rechner-Tower auf dem Boden."""
    return tower(S_X, -0.72, 0.22, 0.50, 0.44, gier=90, led="pink_led", glas_seite=-1)


def transport_a1_1():
    """Halbes Rack mit drei Einschueben."""
    return _rack(-0.70, 0.95, 3)


def transport_a1_2():
    """Volles Rack mit sieben Einschueben."""
    return _rack(-0.70, 1.90, 7)


def transport_a1_3():
    """Zwei volle Racks mit Leuchtkanten, Kabeltrasse obendrauf."""
    t = _rack(-0.70, 1.90, 7, glut=True) + _rack(-0.06, 1.90, 7, glut=True)
    t.append(kasten("trasse", (0.20, 0.05, 1.24), (S_X, 1.99, -0.38), "metall", rund=(0, 0)))
    for k in range(3):
        t.append(stab("kabel", (S_X - 0.05 + k * 0.05, 2.02, -0.98), (S_X - 0.05 + k * 0.05, 2.02, 0.20), 0.012, "pink" if k == 1 else "schwarz", seiten=4))
    return t


# --- Platz 2: Speicher (im Regal) ----------------------------------------------

def _platte(x, y, z, gier=0.0, mat="grau_mittel"):
    t = [kasten("platte", (0.12, 0.028, 0.17), (x, y + 0.014, z), mat, (0, gier, 0), rund=(0.004, 1))]
    t.append(kasten("etikett", (0.06, 0.03, 0.004), punkt((x, y + 0.014, z), (0, gier, 0), (0, 0, 0.086)), "weiss", (0, gier, 0), rund=(0, 0)))
    return t


def _nas(x, y, schaechte, zeilen=1):
    b = 0.05 * schaechte / zeilen + 0.06
    h = 0.20 * zeilen + 0.04
    d = 0.30
    m = (x, y + h * 0.5, T_Z + 0.02)
    t = [kasten("nas", (b, h, d), m, "schwarz", rund=(0.014, 1))]
    for r in range(zeilen):
        for s in range(schaechte // zeilen):
            px = x - b * 0.5 + 0.055 + s * 0.05
            py = y + 0.12 + r * 0.20
            t.append(kasten("schacht", (0.042, 0.17, 0.006), (px, py, m[2] + d * 0.5 + 0.003), "grau_mittel", rund=(0, 0)))
            t.append(kasten("schacht_led", (0.012, 0.012, 0.004), (px, py + 0.06, m[2] + d * 0.5 + 0.007), "pink_led" if s % 2 else "led_gruen", rund=(0, 0)))
    return t


def transport_a2_0():
    """Stapel externer Festplatten im Regal."""
    t = []
    y = t_auf(1)
    for k, g in enumerate((0, 8, -6, 4, -3)):
        t += _platte(-0.20, y + k * 0.03, T_Z + 0.02, g, "grau_mittel" if k % 2 else "grau_dunkel")
    for k, g in enumerate((-10, 6, 0)):
        t += _platte(0.18, y + k * 0.03, T_Z + 0.04, g, "pink" if k == 1 else "grau_hell")
    return t


def transport_a2_1():
    """NAS mit vier Schaechten, daneben zwei Platten."""
    y = t_auf(1)
    t = _nas(-0.14, y, 4)
    t += _platte(0.22, y, T_Z + 0.04, 8) + _platte(0.22, y + 0.03, T_Z + 0.04, -5, "pink")
    return t


def transport_a2_2():
    """NAS mit acht Schaechten, darueber ein zweites mit vier."""
    return _nas(-0.10, t_auf(1), 8, 2) + _nas(0.20, t_auf(2), 4)


def transport_a2_3():
    """Band-Archiv: Bandbibliothek mit Glasfront im unteren Fach,
    Kassetten-Reihen oben, dazu das grosse NAS."""
    t = _nas(-0.10, t_auf(1), 8, 2)
    y = t_auf(0)
    h = 0.44
    m = (0.0, y + h * 0.5, T_Z)
    t.append(kasten("bibliothek", (1.00, h, 0.40), m, "grau_dunkel", rund=(0.014, 1)))
    t.append(kasten("glas", (0.60, h - 0.10, 0.006), (-0.14, m[1], T_Z + 0.203), "glas", rund=(0, 0)))
    for r in range(3):
        t.append(kasten("kassetten", (0.54, 0.08, 0.02), (-0.14, y + 0.09 + r * 0.12, T_Z + 0.18), ("pink", "tuerkis", "gelb")[r], rund=(0, 0)))
    t.append(kasten("greifer", (0.06, 0.06, 0.06), (0.05, y + 0.30, T_Z + 0.16), "metall", rund=(0, 0)))
    t.append(kasten("bedienfeld", (0.24, 0.30, 0.006), (0.34, m[1], T_Z + 0.203), "schirm", rund=(0, 0)))
    t.append(kasten("bedien_balken", (0.18, 0.04, 0.004), (0.34, m[1] + 0.08, T_Z + 0.207), "schirm_pink", rund=(0, 0)))
    for k in range(8):
        t.append(kasten("band", (0.06, 0.16, 0.22), (-0.42 + k * 0.075, t_auf(2) + 0.08, T_Z + 0.06), ("pink", "tuerkis", "gelb", "weiss")[k % 4], rund=(0, 0)))
    return t


# --- Platz 3: Kuehlung ---------------------------------------------------------

K_X, K_Z = 0.86, -0.44


def _ventilator(x, y, z, r, gier, mat="weiss"):
    d = (0, gier, 0)
    t = [ring("korb", r, 0.012, (x, y, z), mat, verkette(d, (90, 0, 0)), segmente=14, quer=4)]
    t.append(zylinder("korb_hinten", r * 0.95, 0.02, punkt((x, y, z), d, (0, 0, -0.06)), "grau_hell", seiten=14, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    t.append(zylinder("nabe", r * 0.2, 0.06, punkt((x, y, z), d, (0, 0, -0.02)), "pink", seiten=8, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    for k in range(3):
        t.append(kasten("fluegel", (r * 0.7, r * 0.35, 0.006), punkt((x, y, z), d, (math.cos(math.radians(k * 120)) * r * 0.45, math.sin(math.radians(k * 120)) * r * 0.45, -0.03)),
                        "mint", verkette(d, (0, 0, k * 120)), rund=(0, 0)))
    t.append(kasten("motor", (r * 0.4, r * 0.4, 0.10), punkt((x, y, z), d, (0, 0, -0.12)), mat, d, rund=(0.01, 1)))
    return t


def transport_a3_0():
    """Tischventilator auf einer Kiste."""
    t = [kasten("kiste", (0.34, 0.30, 0.34), (K_X, 0.15, K_Z), "karton", (0, 10, 0), rund=(0.012, 1))]
    gier = -30
    t += _ventilator(K_X, 0.52, K_Z, 0.13, gier)
    t.append(stab("hals", (K_X, 0.31, K_Z), punkt((K_X, 0.48, K_Z), (0, gier, 0), (0, 0, -0.14)), 0.015, "weiss", seiten=6))
    t.append(zylinder("fuss", 0.09, 0.03, (K_X, 0.315, K_Z), "weiss", seiten=10, rund=(0, 0)))
    return t


def transport_a3_1():
    """Standventilator."""
    gier = -30
    t = _ventilator(K_X, 1.20, K_Z, 0.22, gier)
    t.append(stab("stange", (K_X, 0.04, K_Z), punkt((K_X, 1.20, K_Z), (0, gier, 0), (0, -0.06, -0.14)), 0.02, "weiss", seiten=6))
    t.append(zylinder("fuss", 0.20, 0.04, (K_X, 0.02, K_Z), "weiss", seiten=12, rund=(0.01, 1)))
    return t


def _klimageraet(x, z, b, h, d, gier=0):
    dr = (0, gier, 0)
    m = (x, h * 0.5 + 0.03, z)
    t = [kasten("klima", (b, h, d), m, "weiss", dr, rund=(0.03, 2))]
    t.append(kasten("gitter_rahmen", (b * 0.8, h * 0.4, 0.01), punkt(m, dr, (0, h * 0.15, d * 0.5 + 0.004)), "grau_hell", dr, rund=(0, 0)))
    for k in range(4):
        t.append(kasten("lamelle", (b * 0.74, 0.012, 0.012), punkt(m, dr, (0, h * 0.15 - h * 0.15 + k * h * 0.1, d * 0.5 + 0.01)), "grau_mittel", dr, rund=(0, 0)))
    t.append(kasten("anzeige", (b * 0.3, 0.05, 0.006), punkt(m, dr, (0, h * 0.42, d * 0.5 + 0.004)), "kuehl_blau", dr, rund=(0, 0)))
    t.append(kasten("streifen", (b + 0.004, 0.03, d + 0.004), punkt(m, dr, (0, -h * 0.30, 0)), "pink", dr, rund=(0, 0)))
    return t


def transport_a3_2():
    """Mobiles Klimageraet mit Abluftschlauch zur Wand."""
    t = _klimageraet(K_X, -0.50, 0.38, 0.78, 0.34)
    for sz in (-1, 1):
        for sx in (-1, 1):
            t.append(zylinder("rolle", 0.02, 0.03, (K_X + sx * 0.12, 0.015, -0.50 + sz * 0.12), "schwarz", seiten=6, rund=(0, 0)))
    punkte = [(K_X, 0.84, -0.58), (K_X - 0.02, 1.05, -0.72), (K_X, 1.20, -0.86), (K_X, 1.24, -0.97)]
    for a, b in zip(punkte, punkte[1:]):
        t.append(stab("schlauch", a, b, 0.055, "grau_hell", seiten=8))
    t.append(kasten("fensterplatte", (0.30, 0.30, 0.02), (K_X, 1.24, -1.01), "grau_mittel", rund=(0, 0)))
    return t


def transport_a3_3():
    """Grosse Klimaanlage mit isolierten Rohren unter der Decke und
    Auslass ueber dem Regal."""
    t = _klimageraet(K_X, -0.66, 0.40, 1.66, 0.50)
    t.append(kasten("sockel", (0.46, 0.03, 0.54), (K_X, 0.015, -0.66), "grau_dunkel", rund=(0, 0)))
    for k, dz in enumerate((-0.10, 0.06)):
        mat = "grau_hell" if k == 0 else "pink"
        oben = 2.06 + k * 0.10
        t.append(stab("rohr", (K_X, 1.70, -0.66 + dz), (K_X, oben, -0.66 + dz), 0.04, mat, seiten=8))
        t.append(kugel("rohrbogen", 0.045, (K_X, oben, -0.66 + dz), mat, stufen=1))
        t.append(stab("rohr", (K_X, oben, -0.66 + dz), (K_X, oben, -0.84 + dz * 0.0 - k * 0.0), 0.04, mat, seiten=8))
        t.append(kugel("rohrbogen", 0.045, (K_X, oben, -0.84), mat, stufen=1))
        t.append(stab("rohr", (K_X, oben, -0.84), (-0.42, oben, -0.84), 0.04, mat, seiten=8))
    t.append(kasten("auslass", (0.34, 0.14, 0.24), (-0.42, 2.02, -0.80), "weiss", rund=(0.02, 1)))
    t.append(kasten("auslass_gitter", (0.30, 0.01, 0.20), (-0.42, 1.945, -0.80), "kuehl_blau", rund=(0, 0)))
    for k in range(2):
        t.append(stab("halter", (0.45 - k * 0.75, 2.06, -0.88), (0.45 - k * 0.75, 2.06, -1.025), 0.01, "metall", seiten=4))
    return t


TRANSPORT = {
    "basis": transport_basis,
    "plaetze": {
        1: {0: transport_a1_0, 1: transport_a1_1, 2: transport_a1_2, 3: transport_a1_3},
        2: {0: transport_a2_0, 1: transport_a2_1, 2: transport_a2_2, 3: transport_a2_3},
        3: {0: transport_a3_0, 1: transport_a3_1, 2: transport_a3_2, 3: transport_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [],
}

# =============================================================================
# Station 5: station_special -- Sponsoren (Lounge-Sofa mit Tisch)
# Sofa hinten (z ~ -0,78), Couchtisch davor (-0,25 | -0,05). Platz 1
# Praesentation links, Platz 2 Produkte hinten rechts, Platz 3 Empfang vorn
# rechts.
# =============================================================================

L_TISCH = (-0.25, -0.05)
L_TISCH_H = 0.40
L_SITZ = (-0.20, 0.42, -0.70)


def special_basis():
    t = []
    t.append(zylinder("teppich", 0.44, 0.012, (-0.25, 0.006, -0.05), "pink_hell", seiten=14, rund=(0, 0)))
    t.append(zylinder("teppich_rand", 0.36, 0.004, (-0.25, 0.013, -0.05), "weiss", seiten=14, rund=(0, 0)))
    t += _sofa(-0.20, -0.74, 1.20, 0, mat="leder", kissen="stoff_senf")
    tx, tz = L_TISCH
    t.append(kasten("tischplatte", (0.80, 0.04, 0.42), (tx, L_TISCH_H - 0.02, tz), "holz_hell", rund=(0.016, 2)))
    for s in (-1, 1):
        t.append(kasten("tischkufe", (0.04, L_TISCH_H - 0.04, 0.36), (tx + s * 0.34, (L_TISCH_H - 0.04) * 0.5 + 0.015, tz), "grau_dunkel", rund=(0.01, 1)))
    t.append(kasten("magazin", (0.20, 0.012, 0.26), (tx + 0.18, L_TISCH_H + 0.006, tz + 0.02), "pink", (0, 12, 0), rund=(0, 0)))
    t.append(kasten("magazin", (0.20, 0.012, 0.26), (tx + 0.20, L_TISCH_H + 0.018, tz + 0.01), "tuerkis", (0, -8, 0), rund=(0, 0)))

    return t


# --- Platz 1: Praesentation ----------------------------------------------------

def special_a1_0():
    """Laptop auf dem Couchtisch."""
    tx, tz = L_TISCH
    return laptop((tx - 0.18, L_TISCH_H + 0.003, tz), (0, 60, 0), breite=0.32, tiefe=0.22, mat="metall", inhalt="kurve", dicke=0.016)


def special_a1_1():
    """Tablet auf einem Bodenstaender."""
    x, z = -0.86, 0.22
    d = (-12, 60, 0)
    t = [zylinder("staender_fuss", 0.16, 0.025, (x, 0.0125, z), "grau_dunkel", seiten=12, rund=(0, 0))]
    t.append(stab("staender", (x, 0.02, z), (x, 1.00, z), 0.018, "metall", seiten=6))
    m = (x + 0.02, 1.14, z + 0.01)
    t.append(kasten("tablet", (0.36, 0.26, 0.016), m, "grau_dunkel", d, rund=(0.008, 1)))
    t += schirm_inhalt(m, d, 0.32, 0.22, "kurve", tiefe=0.009)
    t.append(kasten("halter", (0.06, 0.08, 0.03), punkt(m, d, (0, -0.10, -0.02)), "grau_dunkel", d, rund=(0, 0)))
    return t


def special_a1_2():
    """Grosser Fernseher auf Rollstaender."""
    x, z = -0.85, 0.52
    d = (0, 70, 0)
    t = schirm((x, 1.10, z), d, 0.92, 0.54, "kurve", d=0.04)
    t.append(kasten("tv_led", (0.92, 0.015, 0.02), punkt((x, 1.10, z), d, (0, -0.28, -0.01)), "pink_led", d, rund=(0, 0)))
    t.append(kasten("saeule", (0.08, 0.86, 0.05), punkt((x, 0.48, z), d, (0, 0, -0.05)), "grau_dunkel", d, rund=(0.01, 1)))
    t.append(kasten("fuss", (0.60, 0.04, 0.10), punkt((x, 0.05, z), d, (0, 0, -0.05)), "grau_dunkel", d, rund=(0.01, 1)))
    for s in (-1, 1):
        t.append(kasten("fuss_quer", (0.06, 0.04, 0.34), punkt((x, 0.05, z), d, (s * 0.24, 0, 0.0)), "grau_dunkel", d, rund=(0.008, 1)))
        t.append(zylinder("rolle", 0.02, 0.03, punkt((x, 0.015, z), d, (s * 0.24, 0, 0.14)), "schwarz", seiten=6, rund=(0, 0)))
    return t


def special_a1_3():
    """Leinwand auf Stativ, Beamer auf dem Couchtisch."""
    x, z = -0.98, 0.26
    d = (0, 90, 0)
    t = []
    mitte = (x, 1.30, z)
    t.append(kasten("leinwand", (1.36, 0.84, 0.012), mitte, "weiss", d, rund=(0, 0)))
    t.append(kasten("leinwand_rand", (1.40, 0.88, 0.006), punkt(mitte, d, (0, 0, -0.008)), "schwarz", d, rund=(0, 0)))
    t.append(flach("bild", 1.20, 0.70, punkt(mitte, d, (0, 0, 0.008)), d, "schirm"))
    t += radar(punkt(mitte, d, (-0.30, 0.02, 0.009)), d, 0.26)
    for k in range(4):
        hk = 0.12 + k * 0.10
        t.append(flach("balken", 0.10, hk, punkt(mitte, d, (0.10 + k * 0.13, -0.28 + hk * 0.5, 0.012)), d, "schirm_pink" if k == 3 else "schirm_blau"))
    t.append(zylinder("rolle_oben", 0.035, 1.46, punkt(mitte, d, (0, 0.46, -0.01)), "grau_dunkel", seiten=8, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(stab("mast", (x - 0.04, 0.02, z), (x - 0.04, 1.76, z), 0.018, "grau_dunkel", seiten=6))
    for i in range(3):
        w = math.radians(90 + 120 * i)
        t.append(stab("bein", (x - 0.04, 0.50, z), (x - 0.04 + math.cos(w) * 0.05, 0.012, z + math.sin(w) * 0.34), 0.012, "grau_dunkel", seiten=4))
    # Beamer auf dem Couchtisch, zeigt nach -x
    tx, tz = L_TISCH
    bx, by, bz = tx - 0.20, L_TISCH_H + 0.05, tz
    t.append(kasten("beamer", (0.22, 0.09, 0.26), (bx, by, bz), "weiss", (0, 90, 0), rund=(0.02, 1)))
    t.append(zylinder("beamer_linse", 0.035, 0.03, (bx - 0.12, by, bz + 0.05), "schirm_blau", seiten=10, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(kasten("beamer_streifen", (0.004, 0.02, 0.24), (bx + 0.11, by + 0.02, bz), "pink", rund=(0, 0)))
    return t


# --- Platz 2: Produkte ---------------------------------------------------------

def _produkte(x, y, z, breite, anzahl, seed=0):
    t = []
    farben = ("pink", "tuerkis", "gelb", "weiss", "stoff_blau")
    for k in range(anzahl):
        px = x - breite * 0.5 + (k + 0.5) * breite / anzahl
        art = (k + seed) % 3
        mat = farben[(k + seed) % len(farben)]
        if art == 0:
            t.append(kasten("produkt", (0.08, 0.14, 0.08), (px, y + 0.07, z), mat, (0, 10 * k, 0), rund=(0.008, 1)))
        elif art == 1:
            t.append(zylinder("produkt", 0.035, 0.16, (px, y + 0.08, z), mat, seiten=6, rund=(0, 0)))
        else:
            t.append(kasten("produkt", (0.09, 0.10, 0.06), (px, y + 0.05, z), mat, (0, -8 * k, 0), rund=(0.008, 1)))
    return t


def special_a2_0():
    """Ein Sponsorenkarton mit pinkem Klebeband."""
    x, z = 0.80, -0.74
    t = [kasten("karton", (0.40, 0.34, 0.36), (x, 0.17, z), "karton", (0, -12, 0), rund=(0.012, 1))]
    t.append(kasten("band", (0.41, 0.004, 0.08), (x, 0.342, z), "pink", (0, -12, 0), rund=(0, 0)))
    t.append(kasten("band_s", (0.08, 0.30, 0.004), punkt((x, 0.18, z), (0, -12, 0), (0, 0, 0.181)), "pink", (0, -12, 0), rund=(0, 0)))
    t.append(kasten("klappe", (0.30, 0.004, 0.18), punkt((x, 0.40, z), (0, -12, 0), (0, 0, -0.14)), "karton", verkette((0, -12, 0), (40, 0, 0)), rund=(0, 0)))
    return t


def _regal(x, z, b, h, d, boeden, mat="holz_hell"):
    t = []
    for s in (-1, 1):
        t.append(kasten("regal_seite", (0.03, h, d), (x + s * (b * 0.5 - 0.015), h * 0.5, z), mat, rund=(0.008, 1)))
    for k in range(boeden):
        y = 0.08 + k * (h - 0.12) / (boeden - 1)
        t.append(kasten("regal_boden", (b - 0.06, 0.025, d - 0.02), (x, y, z), mat, rund=(0, 0)))
    t.append(kasten("regal_rueck", (b - 0.06, h - 0.04, 0.01), (x, h * 0.5, z - d * 0.5 + 0.01), "pink_hell", rund=(0, 0)))
    return t


def special_a2_1():
    """Produktregal mit drei Boeden."""
    x, z = 0.80, -0.86
    t = _regal(x, z, 0.52, 1.20, 0.30, 4)
    for k in range(3):
        y = 0.08 + k * (1.20 - 0.12) / 3 + 0.013
        t += _produkte(x, y, z + 0.02, 0.44, 4, seed=k)
    return t


def _vitrine(x, z, b, h, d):
    t = [kasten("vitrine_sockel", (b, 0.30, d), (x, 0.15, z), "weiss", rund=(0.02, 1))]
    t.append(kasten("vitrine_dach", (b, 0.08, d), (x, h - 0.04, z), "weiss", rund=(0.02, 1)))
    t.append(kasten("vitrine_licht", (b - 0.06, 0.008, d - 0.06), (x, h - 0.084, z), "licht_warm", rund=(0, 0)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(kasten("vitrine_kante", (0.025, h - 0.38, 0.025), (x + sx * (b * 0.5 - 0.0125), 0.30 + (h - 0.38) * 0.5, z + sz * (d * 0.5 - 0.0125)), "metall", rund=(0, 0)))
    t.append(kasten("vitrine_glas", (b - 0.03, h - 0.38, 0.006), (x, 0.30 + (h - 0.38) * 0.5, z + d * 0.5 - 0.005), "glas", rund=(0, 0)))
    t.append(kasten("vitrine_glas", (0.006, h - 0.38, d - 0.03), (x + b * 0.5 - 0.005, 0.30 + (h - 0.38) * 0.5, z), "glas", rund=(0, 0)))
    t.append(kasten("vitrine_band", (b + 0.004, 0.04, d + 0.004), (x, 0.26, z), "pink", rund=(0, 0)))
    ebenen = 2
    for k in range(ebenen):
        y = 0.30 + k * (h - 0.38) / ebenen
        if k > 0:
            t.append(kasten("glasboden", (b - 0.06, 0.012, d - 0.06), (x, y, z), "glas", rund=(0, 0)))
        t += _produkte(x, y + 0.008, z, b - 0.14, 3, seed=k + 2)
    return t


def special_a2_2():
    """Beleuchtete Glasvitrine."""
    return _vitrine(0.80, -0.80, 0.50, 1.50, 0.42)


def special_a2_3():
    """Messestand: pinke Winkelwand mit Logo-Kreis, Spots, Theke mit
    Produkten, Vitrine."""
    t = []
    t.append(kasten("standwand", (0.64, 2.00, 0.06), (0.76, 1.00, -1.05), "pink", rund=(0.02, 1)))

    t.append(zylinder("logo", 0.20, 0.02, (0.72, 1.46, -1.01), "weiss", seiten=16, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(ring("logo_ring", 0.12, 0.025, (0.72, 1.46, -0.995), "pink", dreh=(90, 0, 0), segmente=12, quer=3))

    for k in range(2):
        px = 0.56 + k * 0.34
        t.append(stab("spotarm", (px, 2.00, -1.02), (px, 2.06, -0.86), 0.01, "grau_dunkel", seiten=4))
        t.append(zylinder("spot", 0.04, 0.10, (px, 2.02, -0.84), "schwarz", seiten=8, dreh=(35, 0, 0), rund=(0, 0)))
    t.append(kasten("theke", (0.34, 0.92, 0.50), (0.78, 0.46, -0.44), "weiss", rund=(0.02, 1)))
    t.append(kasten("theke_platte", (0.40, 0.03, 0.56), (0.78, 0.935, -0.44), "holz_hell", rund=(0.01, 1)))
    t.append(kasten("theke_front", (0.006, 0.50, 0.40), (0.61 - 0.004, 0.52, -0.44), "pink", rund=(0, 0)))
    t += _produkte(0.78, 0.95, -0.44, 0.34, 3, seed=1)
    t += _vitrine(0.82, -0.84, 0.38, 1.10, 0.28)
    return t


# --- Platz 3: Empfang ----------------------------------------------------------

def special_a3_0():
    """Beistelltischchen mit Wasserflasche und zwei Glaesern."""
    x, z = 0.58, 0.50
    t = [zylinder("tischchen", 0.20, 0.03, (x, 0.45, z), "weiss", seiten=14, rund=(0.01, 1))]
    t.append(stab("tischbein", (x, 0.0, z), (x, 0.44, z), 0.025, "metall", seiten=6))
    t.append(zylinder("tischfuss", 0.14, 0.02, (x, 0.01, z), "metall", seiten=12, rund=(0, 0)))
    t.append(zylinder("flasche", 0.04, 0.24, (x - 0.02, 0.585, z - 0.03), "glas", seiten=10, rund=(0, 0)))
    t.append(zylinder("etikett", 0.042, 0.07, (x - 0.02, 0.57, z - 0.03), "pink", seiten=10, rund=(0, 0)))
    t.append(zylinder("verschluss", 0.018, 0.03, (x - 0.02, 0.72, z - 0.03), "weiss", seiten=6, rund=(0, 0)))
    for dx, dz in ((0.09, 0.05), (0.02, 0.11)):
        t.append(zylinder("glas", 0.03, 0.09, (x + dx, 0.51, z + dz), "glas", seiten=8, rund=(0, 0)))
    return t


def _kaffeemaschine(x, y, z, gier=0.0, g=1.0, mit_tasse=True):
    d = (0, gier, 0)
    t = [kasten("maschine", (0.26 * g, 0.32 * g, 0.28 * g), (x, y + 0.16 * g, z), "grau_dunkel", d, rund=(0.02, 1))]
    t.append(kasten("maschine_front", (0.20 * g, 0.10 * g, 0.006), punkt((x, y + 0.16 * g, z), d, (0, -0.04 * g, 0.143 * g)), "metall", d, rund=(0, 0)))
    t.append(kasten("maschine_akzent", (0.26 * g + 0.004, 0.03, 0.28 * g + 0.004), punkt((x, y + 0.29 * g, z), d, (0, 0, 0)), "pink", d, rund=(0, 0)))
    t.append(kasten("maschine_anzeige", (0.08, 0.03, 0.004), punkt((x, y + 0.25 * g, z), d, (0.05 * g, 0, 0.143 * g)), "schirm", d, rund=(0, 0)))
    if mit_tasse:
        t += tasse(punkt((x, y, z), d, (0, 0.03, 0.08 * g)), "weiss", hoehe=0.07, radius=0.03)
    return t


def special_a3_1():
    """Kaffeemaschine auf einem kleinen Sideboard, Tassen."""
    x, z = 0.80, 0.56
    t = [kasten("sideboard", (0.50, 0.72, 0.38), (x, 0.38, z), "holz", rund=(0.02, 1))]
    t.append(kasten("sideboard_front", (0.44, 0.26, 0.006), (x, 0.52, z + 0.192), "holz_hell", rund=(0, 0)))
    t.append(kasten("sideboard_front", (0.44, 0.26, 0.006), (x, 0.22, z + 0.192), "holz_hell", rund=(0, 0)))
    for k in range(4):
        t.append(zylinder("fuss", 0.02, 0.02, (x + (-0.2 if k % 2 else 0.2), 0.01, z + (-0.15 if k < 2 else 0.15)), "grau_dunkel", seiten=6, rund=(0, 0)))
    t += _kaffeemaschine(x - 0.06, 0.742, z - 0.02)
    t += tasse((x + 0.17, 0.742, z + 0.06), "pink", hoehe=0.07, radius=0.03)
    return t


def _theke(x, z, laenge):
    t = [kasten("theke", (0.36, 1.00, laenge), (x, 0.50, z), "holz_hell", rund=(0.02, 1))]
    t.append(kasten("theke_platte", (0.46, 0.04, laenge + 0.06), (x - 0.04, 1.02, z), "weiss", rund=(0.012, 1)))
    t.append(kasten("theke_front", (0.006, 0.60, laenge - 0.10), (x - 0.183, 0.52, z), "pink", rund=(0, 0)))
    t.append(kasten("theke_band", (0.006, 0.10, laenge - 0.10), (x + 0.183, 0.80, z), "pink", rund=(0, 0)))
    t.append(kasten("theke_band", (0.30, 0.10, 0.006), (x, 0.80, z + laenge * 0.5 + 0.003), "pink", rund=(0, 0)))
    t.append(kasten("fussleiste", (0.02, 0.06, laenge - 0.04), (x - 0.19, 0.12, z), "metall", rund=(0, 0)))
    return t


def special_a3_2():
    """Empfangstheke mit Kaffeemaschine und Tassen."""
    x, z = 0.84, 0.58
    t = _theke(x, z, 0.90)
    t += _kaffeemaschine(x, 1.04, z - 0.22, gier=-90)
    for k in range(3):
        t += tasse((x - 0.06, 1.04, z + 0.12 + k * 0.09), ("weiss", "pink", "weiss")[k], hoehe=0.07, radius=0.028)
    return t


def special_a3_3():
    """Bar: Theke mit Leuchtband, zwei Barhocker, Flaschenregal mit
    Neonkreis."""
    x, z = 0.66, 0.58
    t = _theke(x, z, 0.92)
    t.append(kasten("leuchtband", (0.006, 0.03, 0.82), (x - 0.184, 0.86, z), "pink_led", rund=(0, 0)))
    t += _kaffeemaschine(x + 0.02, 1.04, z - 0.28, gier=-90, g=0.9, mit_tasse=False)
    for k in range(2):
        t += hocker_bar(0.26, z - 0.18 + k * 0.42, 0.74, mat="pink" if k == 0 else "weiss")
    # Flaschenregal hinter der Theke
    rx = 0.98
    t.append(kasten("barregal", (0.18, 0.84, 0.90), (rx, 0.42, z), "holz_dunkel", rund=(0.012, 1)))
    for k in range(5):
        mat = ("pink", "gruen_hell", "gelb", "tuerkis", "weiss")[k % 5]
        t.append(zylinder("flasche", 0.028, 0.20, (rx, 0.94, z - 0.34 + k * 0.17), mat, seiten=6, rund=(0, 0)))
    t.append(stab("neon_halter", (rx + 0.02, 0.84, z), (rx + 0.02, 1.16, z), 0.012, "metall", seiten=4))
    t.append(ring("neon", 0.15, 0.014, (rx + 0.02, 1.30, z), "pink_led", dreh=(0, 0, 90), segmente=12, quer=3))
    return t


SPECIAL = {
    "basis": special_basis,
    "plaetze": {
        1: {0: special_a1_0, 1: special_a1_1, 2: special_a1_2, 3: special_a1_3},
        2: {0: special_a2_0, 1: special_a2_1, 2: special_a2_2, 3: special_a2_3},
        3: {0: special_a3_0, 1: special_a3_1, 2: special_a3_2, 3: special_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("sitz", L_SITZ)],
    "frei": [(L_SITZ[0], L_SITZ[2] + 0.1, 0.18, 1.0)],
}

STATIONEN = {"intake": INTAKE, "buffer": BUFFER, "processing": PROCESSING,
             "transport": TRANSPORT, "special": SPECIAL}
wg.STATIONEN = STATIONEN

# =============================================================================
# Altmodelle, Flussteil, Budget
# =============================================================================

def baue_altmodelle(station):
    daten = STATIONEN[station]
    for m in (1, 2, 3):
        wg.alles_loeschen()
        teile = daten["basis"]()
        for platz, stufen in daten["plaetze"].items():
            verfuegbar = [s for s in sorted(stufen) if s <= m]
            if verfuegbar:
                teile += stufen[verfuegbar[-1]]()
        name = "station_%s_%d" % (station, m)
        obj = wg.zusammenfuegen(teile, name)
        wg.exportieren(obj, os.path.join(AUSGABE, name + ".glb"))
        print("  %-42s %5d Dreiecke" % (name, wg.dreiecke(obj)))


def pruefe_budget(station):
    """Schlimmster Fall: Basis plus je Platz die teuerste Stufe."""
    daten = STATIONEN[station]
    wg.alles_loeschen()
    summe = wg.dreiecke(wg.zusammenfuegen(daten["basis"](), "b"))
    for platz, stufen in daten["plaetze"].items():
        groesste = 0
        for bauen in stufen.values():
            wg.alles_loeschen()
            groesste = max(groesste, wg.dreiecke(wg.zusammenfuegen(bauen(), "p")))
        summe += groesste
    ok = summe <= BUDGET_GESAMT
    print("  Budget %s: %d / %d Dreiecke %s" % (station, summe, BUDGET_GESAMT, "ok" if ok else "!! UEBER BUDGET"))
    return summe, (0 if ok else 1)


def fluss_teil():
    """Kleine Filmklappe, kraeftig pink und weiss, Ursprung in der Mitte."""
    t = []
    b, h, d = 0.26, 0.16, 0.05
    y0 = -0.16
    tafel = (0.0, y0 + h * 0.5, 0.0)
    t.append(kasten("tafel", (b, h, d), tafel, "pink", rund=(0.012, 2)))
    for k in range(2):
        t.append(kasten("zeile", (b * 0.78, 0.022, 0.006), (0.0, y0 + h * 0.62 - k * 0.06, d * 0.5 + 0.002), "weiss", rund=(0, 0)))
        t.append(kasten("zeile_h", (b * 0.78, 0.022, 0.006), (0.0, y0 + h * 0.62 - k * 0.06, -d * 0.5 - 0.002), "weiss", rund=(0, 0)))
    leiste_unten = (0.0, y0 + h + 0.022, 0.0)
    t.append(kasten("leiste", (b, 0.044, d), leiste_unten, "weiss", rund=(0.008, 1)))
    # Schlagholz leicht geoeffnet, Scharnier links
    scharnier = (-b * 0.5, y0 + h + 0.044, 0.0)
    dr = (0, 0, 18)
    arm = punkt(scharnier, dr, (b * 0.5, 0.024, 0.0))
    t.append(kasten("schlagholz", (b, 0.044, d), arm, "weiss", dr, rund=(0.008, 1)))
    for s in range(3):
        for mitte, drehung in ((leiste_unten, (0, 0, 0)), (arm, dr)):
            p = punkt(mitte, drehung, (-b * 0.32 + s * b * 0.32, 0.0, 0.0))
            t.append(kasten("streifen", (0.05, 0.046, d + 0.004), p, "pink", verkette(drehung, (0, 0, 30)), rund=(0, 0)))
    t.append(zylinder("scharnier", 0.014, d + 0.01, scharnier, "grau_dunkel", seiten=8, dreh=(90, 0, 0), rund=(0, 0)))
    return t


def baue_fluss():
    wg.alles_loeschen()
    obj = wg.zusammenfuegen(fluss_teil(), "fluss_teil")
    ecken = [v.co for v in obj.data.vertices]
    mitte = Vector([(max(c[i] for c in ecken) + min(c[i] for c in ecken)) * 0.5 for i in range(3)])
    obj.data.transform(Matrix.Translation(-mitte))
    wg.exportieren(obj, AUSGABE_FLUSS)
    g = wg.grenzen(obj)
    print("  fluss_teil: %d Dreiecke, x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % ((wg.dreiecke(obj),) + g))


def vorschau_fluss():
    wg.alles_loeschen()
    wg.licht_und_welt()
    wg.zusammenfuegen(fluss_teil(), "fluss_teil")
    wg._kamera_iso((0, 0, 0), 0.6, (500, 500))
    pfad = os.path.join(VORSCHAU, "fluss_teil.png")
    os.makedirs(VORSCHAU, exist_ok=True)
    bpy.context.scene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)
    print("  Vorschau:", pfad)


# =============================================================================
# Symbole (Render wie build_symbole_wg.py, dazu 6 px Tintenkontur)
# =============================================================================

KONTUR_PX = 6
TINTE = "#1B1726"

SYM_AZIMUT = {
    ("intake", 0): 30, ("intake", 1): 60, ("intake", 2): 5, ("intake", 3): -45,
    ("buffer", 0): 35, ("buffer", 1): 60, ("buffer", 2): -55, ("buffer", 3): 35,
    ("processing", 0): 30, ("processing", 1): 45, ("processing", 2): 15, ("processing", 3): -50,
    ("transport", 0): 30, ("transport", 1): 70, ("transport", 2): 15, ("transport", 3): 20,
    ("special", 0): 25, ("special", 1): 60, ("special", 2): 20, ("special", 3): -30,
}

_ANGEL = ["bein", "saeule", "gelenk", "angel", "gegengewicht", "abhaenger", "fell"]
_ALLE_Y = (-9.0, 9.0)
SYM_MOTIVE = {
    ("buffer", 3, 3): {"weg": [(_ANGEL, _ALLE_Y)]},
    ("buffer", 3, 2): {"weg": [(_ANGEL, _ALLE_Y)]},

    ("transport", 3, 3): {"weg": [(["rohr", "rohrbogen", "auslass", "auslass_gitter", "halter"], _ALLE_Y)]},
    ("special", 1, 3): {"weg": [(["beamer", "beamer_linse", "beamer_streifen"], _ALLE_Y)]},
    ("intake", 2, 3): {"weg": [(["gehaeuse", "fuss", "hals", "schirm", "i", "tastatur", "taste", "tasten", "reihe"], (0.9, 1.4))]},
}


def _kontur(pfad, ausblenden):
    """Weiches Ausblenden (optional), dann 6 px Tintenkontur um die
    Silhouette. Kein weicher Schatten: Sticker-Stil hat harte Kanten."""
    n = 256
    bild = bpy.data.images.load(pfad)
    px = np.array(bild.pixels[:], dtype=np.float32).reshape(n, n, 4)
    bpy.data.images.remove(bild)
    a = px[:, :, 3].copy()
    if ausblenden:
        y = np.arange(n, dtype=np.float32)
        t = np.clip(y / (n * 0.30), 0.0, 1.0)
        a *= (t * t * (3.0 - 2.0 * t))[:, None]
    r = KONTUR_PX
    pad = np.pad(a, r)
    dil = np.zeros_like(a)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            abstand = math.hypot(dx, dy)
            if abstand > r + 0.5:
                continue
            gewicht = min(1.0, r + 0.5 - abstand)
            dil = np.maximum(dil, pad[r + dy:r + dy + n, r + dx:r + dx + n] * gewicht)
    tinte = np.array(farbe(TINTE)[:3], dtype=np.float32)
    a_neu = a + dil * (1.0 - a)
    rgb = (px[:, :, :3] * a[:, :, None] + tinte * (dil * (1.0 - a))[:, :, None]) / np.maximum(a_neu, 1e-6)[:, :, None]
    aus = np.dstack([rgb, a_neu]).astype(np.float32)
    ziel = bpy.data.images.new("symbol", width=n, height=n, alpha=True)
    ziel.pixels[:] = aus.ravel()
    ziel.filepath_raw = pfad
    ziel.file_format = "PNG"
    ziel.save()
    bpy.data.images.remove(ziel)


def symbole(stationen):
    import build_symbole_wg as sym
    sym.AUSGABE = AUSGABE_UI
    sym.AZIMUT = SYM_AZIMUT
    sym.MOTIVE = SYM_MOTIVE
    sym.FUELLUNG = 0.78
    sym.nachbearbeiten = _kontur
    os.makedirs(AUSGABE_UI, exist_ok=True)
    anzahl = 0
    for station in stationen:
        anzahl += len(sym.symbole_station(station))
        print("  Symbole %s fertig" % station)
    sym.kontaktbogen(stationen)
    print("  %d Symbole" % anzahl)


# =============================================================================

def main():
    a = wg.argumente()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    print("")
    print("=== STATIONEN AUFTRAG (N11) ===")
    gesamt = 0
    stationen = [s for s in STATIONEN if not a["nur"] or s in a["nur"]]
    budget = {}
    for station in stationen:
        print("--", station)
        gesamt += wg.baue_station(station, export=not a["kein_export"])
        summe, fehler = pruefe_budget(station)
        budget[station] = summe
        gesamt += fehler
        if not a["kein_export"]:
            baue_altmodelle(station)
        if a["vorschau"]:
            wg.vorschau_station(station)
        if a["klein"]:
            wg.vorschau_station(station, klein=True)
        if a["nah"]:
            wg.vorschau_nah(station, [3, 3, 3], "m3")
            wg.vorschau_nah(station, [0, 0, 0], "m0")
    if (not a["nur"] and not a["kein_export"]) or "--fluss" in args:
        baue_fluss()
        if a["vorschau"]:
            vorschau_fluss()
    if "--symbole" in args:
        symbole(stationen)
    print("")
    for station, summe in budget.items():
        print("  %-12s %5d Dreiecke (Basis + teuerste Stufen)" % (station, summe))
    print("  Probleme gesamt: %d" % gesamt)


if __name__ == "__main__":
    main()
