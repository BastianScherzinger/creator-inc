"""Einrichtung, Umgebung und Fundament fuer Welt 2 `auftrag` -- "Das Studio"
(docs/NACHT_PLAN.md Abschnitte 2 und 5, docs/nacht/ausstattung_welten.md).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_auftrag.py
    (optional nach "--": Zonennamen -> nur diese; --ohne-vorschau; --nur-gesamt)

Voraussetzung: build_room_auftrag_neu.py ist gelaufen (die Vorschau stellt
die exportierten Module auf).

Erzeugt project/assets/world/auftrag/:
    einrichtung_<zone>.glb   EIN Mesh je Zone, Ursprung = Zonenmitte (Godot)
    umgebung.glb             Hinterhof ringsum, Ursprung 0,0
    fundament.glb            Sockel unter der Grundflaeche + 1 m Rand
und Vorschauen nach art_source/vorschau/auftrag/.

Freiflaechen (Stationen 2,2 x 2,2, Tuergaenge, 1-m-Laufwege) prueft das
Skript selbst. Stationsflaechen sind streng; ueber Tuer- und Laufwegen ist
alles erlaubt, was hoeher als 1,9 m haengt (Lichterketten, Rolltorkasten).

Koordinaten: GODOT (x rechts, y oben, z zum Betrachter). Moebel werden lokal
mit Vorderseite +z gebaut; setzen(..., dreh=90) dreht die Vorderseite nach +x.
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
    G, kasten, zylinder, liegender_zylinder, kugel, profil_x,
    transformieren, alles_loeschen, verbinden, dreiecke, masse, exportieren,
    importieren, vorschau_rendern, palette_erweitern,
)
from build_einrichtung_wg_a import (  # noqa: E402
    stab, pflanze, karton, teppich, tasse, buchstapel, fahrrad, kleiderstange,
    sitzsack, stehlampe, gitarre, _auswerten,
)
import build_room_auftrag_neu as modul  # noqa: E402  (Palette der Module + Pfade)

WURZEL = modul.WURZEL
AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "auftrag")
VORSCHAU = modul.AUSGABE_VORSCHAU

palette_erweitern({
    "s_neon":          ("#FF4FA3", 0.40, 0.0, 1.0),
    "s_wandpink":      ("#D9558F", 0.85, 0.0, 1.0),
    "s_eimer":         ("#7A8591", 0.55, 0.3, 1.0),
    "s_kaktus":        ("#5E9B62", 0.85, 0.0, 1.0),
    "s_kaktus_dunkel": ("#4A8553", 0.85, 0.0, 1.0),
    "s_kaktus_blume":  ("#F4A8C8", 0.80, 0.0, 1.0),
    "s_licht":         ("#FFE3A3", 0.40, 0.0, 1.0),
    "s_bild_an":       ("#8EC5F2", 0.30, 0.0, 1.0),
    "s_bildschirm":    ("#353B48", 0.35, 0.0, 1.0),
    "s_gruen_screen":  ("#4CC66E", 0.85, 0.0, 1.0),
    "s_container":     ("#3FA7B8", 0.60, 0.1, 1.0),
    "s_container_2":   ("#33909F", 0.60, 0.1, 1.0),
    "s_samt":          ("#D9434F", 0.95, 0.0, 1.0),
    "s_samt_dunkel":   ("#B8323F", 0.95, 0.0, 1.0),
    "s_leinwand":      ("#F7F4EE", 0.60, 0.0, 1.0),
    "s_popcorn":       ("#FFE9A8", 0.90, 0.0, 1.0),
    "s_gelb":          ("#FFC83D", 0.60, 0.0, 1.0),
    "s_gold":          ("#F2B84B", 0.35, 0.5, 1.0),
    "s_lochwand":      ("#E6C79A", 0.85, 0.0, 1.0),
    "s_palette":       ("#DDB27A", 0.85, 0.0, 1.0),
    "s_schirm":        ("#FF8FC4", 0.85, 0.0, 1.0),
    "s_blau":          ("#3FB6E0", 0.70, 0.0, 1.0),
    "s_lila":          ("#8B5CF6", 0.70, 0.0, 1.0),
    "s_orange":        ("#FF7A1A", 0.70, 0.0, 1.0),
    "s_mint":          ("#7FD8BE", 0.80, 0.0, 1.0),
    "s_himmel":        ("#9ED8F5", 0.50, 0.0, 1.0),
    "s_asphalt":       ("#4C4A55", 0.95, 0.0, 1.0),
    "s_markierung":    ("#E3DCC9", 0.80, 0.0, 1.0),
    "s_bordstein":     ("#8F877E", 0.90, 0.0, 1.0),
    "s_rasen":         ("#8DC262", 0.95, 0.0, 1.0),
    "s_baum":          ("#5DA84A", 0.85, 0.0, 1.0),
    "s_baum_2":        ("#4B9444", 0.85, 0.0, 1.0),
    "s_baum_3":        ("#7DBE55", 0.85, 0.0, 1.0),
    "s_stamm":         ("#8A6446", 0.90, 0.0, 1.0),
    "s_tonne_grau":    ("#7C8591", 0.70, 0.0, 1.0),
    "s_fundament":     ("#8C867D", 0.90, 0.0, 1.0),
    "s_boden_aussen":  ("#5D5651", 0.95, 0.0, 1.0),
    "s_boden_aussen_2": ("#524C48", 0.95, 0.0, 1.0),
    # Aliase -> weniger Draw Calls
    "s_tonne_blau":    "s_blau",
    "s_tonne_gelb":    "s_gelb",
    "s_werkzeug":      "akzent_rot",
})

# Materialien, die in Godot leuchten sollen (Emission, Staerke)
LEUCHTEND = {"s_neon": 2.5, "s_licht": 3.0, "s_bild_an": 1.2, "lampe_licht": 1.2}


def leuchten_setzen():
    for mat in bpy.data.materials:
        basis = mat.name.split(".")[0]
        if basis in LEUCHTEND and mat.node_tree:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Emission Color"].default_value = bsdf.inputs["Base Color"].default_value
                bsdf.inputs["Emission Strength"].default_value = LEUCHTEND[basis]


# --- Buchfuehrung -------------------------------------------------------------

MOEBEL = []
MOEBEL_BUDGET = 600
ZONEN_BUDGET = 8000
WEG_FREI_HOEHE = 1.9


def setzen(name, teile, x=0.0, z=0.0, dreh=0.0, y=0.0):
    teile = [t for t in teile if t is not None]
    transformieren(teile, x=x, z=z, y=y, dreh_grad=dreh)
    MOEBEL.append((name, teile))
    return teile


def moebel_bericht(budget=MOEBEL_BUDGET):
    gesamt = 0
    zu_viel = 0
    for name, teile in MOEBEL:
        n = sum(_auswerten(t)[0] for t in teile)
        gesamt += n
        if n > budget:
            zu_viel += 1
            print("    %-28s %5d  <-- UEBER BUDGET" % (name, n))
    print("    %d Moebel, groesstes %d Dreiecke" % (len(MOEBEL), max(
        [sum(_auswerten(t)[0] for t in teile) for _, teile in MOEBEL] or [0])))
    return gesamt, zu_viel


def freiflaechen_pruefen(zone):
    toleranz = 0.01
    fehler = 0
    hx, hz = zone["breite"] / 2.0 - 0.1, zone["tiefe"] / 2.0 - 0.1
    for name, teile in MOEBEL:
        for t in teile:
            _, punkte = _auswerten(t)
            if not punkte:
                continue
            x0 = min(p.x for p in punkte); x1 = max(p.x for p in punkte)
            z0 = min(-p.y for p in punkte); z1 = max(-p.y for p in punkte)
            y0 = min(p.z for p in punkte); y1 = max(p.z for p in punkte)
            if y1 > 0.021:
                for (fx, fz, fb, ft, was, art) in zone["frei"]:
                    if art == "W" and y0 >= WEG_FREI_HOEHE:
                        continue
                    if (x1 > fx - fb / 2 + toleranz and x0 < fx + fb / 2 - toleranz and
                            z1 > fz - ft / 2 + toleranz and z0 < fz + ft / 2 - toleranz):
                        print("    FREIFLAECHE VERLETZT: %s/%s schneidet '%s'" % (name, t.name, was))
                        fehler += 1
            if x0 < -hx - toleranz or x1 > hx + toleranz or z0 < -hz - toleranz or z1 > hz + toleranz:
                print("    RAGT IN DIE WAND: %s/%s  x %+.2f..%+.2f  z %+.2f..%+.2f"
                      % (name, t.name, x0, x1, z0, z1))
                fehler += 1
    return fehler


# --- Zonen (NACHT_PLAN 2) -----------------------------------------------------
# welt = Zonenmitte (Godot x, z). frei: (x, z, breite, tiefe, text, S|W) lokal.

def _s(x, z, text):
    return (x, z, 2.2, 2.2, "Station " + text, "S")


def _w(x, z, b, t, text):
    return (x, z, b, t, text, "W")


ZONEN = {
    # Verbindlich: docs/nacht/karten_welten.md bzw. worlds.json (Eintrag auftrag).
    # Tueren nur in den Querwaenden z -3,5 und z -0,5 bei x -7, 0, 6.
    "garage": {
        "breite": 7.0, "tiefe": 7.0, "welt": (0.0, 3.0), "boden": "beton",
        "waende": {"hinten": ("halb", {0.0: "tuer"}), "links": ("halb", {}),
                   "rechts": ("halb", {}), "vorn": ("sockel", {})},
        "frei": [_s(-2.0, -2.35, "intake"), _s(1.8, -2.35, "processing"), _s(0.0, 0.7, "buffer"),
                 _w(0.0, -3.0, 1.2, 1.0, "Tuer hinten"), _w(-0.1, -2.3, 1.0, 2.4, "Laufweg zur Mitte")],
        "ortho": 10.5,
    },
    "hof": {
        "breite": 21.0, "tiefe": 3.0, "welt": (0.0, -2.0), "boden": "pflaster",
        "waende": {"hinten": ("halb", {-7.0: "tuer", 0.0: "tuer", 6.0: "tuer"}),
                   "vorn": ("halb", {-7.0: "tuer", 0.0: "tuer", 6.0: "tuer"}),
                   "links": ("voll", {}), "rechts": ("sockel", {})},
        "frei": [_s(8.4, 0.0, "transport"), _w(-0.55, 0.2, 14.1, 1.0, "Laufweg z -1,8"),
                 _w(-7.0, -1.0, 1.2, 1.0, "Tuer hinten -7"), _w(0.0, -1.0, 1.2, 1.0, "Tuer hinten 0"),
                 _w(6.0, -1.0, 1.2, 1.0, "Tuer hinten 6"), _w(-7.0, 1.0, 1.2, 1.0, "Tuer vorn -7"),
                 _w(0.0, 1.0, 1.2, 1.0, "Tuer vorn 0"), _w(6.0, 1.0, 1.2, 1.0, "Tuer vorn 6")],
        "ortho": 17.0,
    },
    "requisite": {
        "breite": 7.0, "tiefe": 5.0, "welt": (-7.0, -6.0), "boden": "holz",
        "waende": {"hinten": ("voll", {-2.0: "fenster", 1.0: "fenster"}), "links": ("voll", {0.0: "fenster"}),
                   "rechts": ("halb", {}), "vorn": ("halb", {0.0: "tuer"})},
        "frei": [_w(0.0, 1.45, 1.0, 2.1, "Laufweg zum Wartepunkt"), _w(0.0, 2.0, 1.2, 1.0, "Tuer vorn")],
        "ortho": 9.0,
    },
    "greenscreen": {
        "breite": 7.0, "tiefe": 5.0, "welt": (0.0, -6.0), "boden": "studio",
        "waende": {"hinten": ("voll", {0.0: "fenster"}), "links": ("halb", {}),
                   "rechts": ("halb", {}), "vorn": ("halb", {0.0: "tuer"})},
        "frei": [_s(0.6, 0.0, "special"), _w(0.0, 1.8, 1.2, 1.4, "Tuer vorn")],
        "ortho": 9.0,
    },
    "dach": {
        "breite": 7.0, "tiefe": 5.0, "welt": (7.0, -6.0), "boden": "deck",
        "waende": {"hinten": ("gelaender", {}), "rechts": ("gelaender", {}),
                   "links": ("halb", {}), "vorn": ("halb", {-1.0: "tuer"})},
        "frei": [_w(-1.0, 1.25, 1.0, 2.5, "Laufweg vorn"), _w(-1.0, 2.0, 1.2, 1.0, "Tuer vorn")],
        "ortho": 9.0,
    },
    "kino": {
        "breite": 7.0, "tiefe": 7.0, "welt": (-7.0, 3.0), "boden": "teppich",
        "waende": {"hinten": ("halb", {0.0: "tuer"}), "links": ("voll", {0.0: "fenster"}),
                   "rechts": ("halb", {}), "vorn": ("sockel", {})},
        "frei": [_w(0.0, -3.0, 1.2, 1.0, "Tuer hinten"), _w(0.0, -2.0, 1.0, 2.0, "Laufweg")],
        "ortho": 10.5,
    },
    "younes_ecke": {
        "breite": 7.0, "tiefe": 7.0, "welt": (7.0, 3.0), "boden": "holz",
        "waende": {"hinten": ("halb", {-1.0: "tuer"}), "links": ("halb", {}),
                   "rechts": ("sockel", {}), "vorn": ("sockel", {})},
        "frei": [_w(-1.0, -3.0, 1.2, 1.0, "Tuer hinten"), _w(-1.0, -2.25, 1.0, 2.5, "Laufweg"),
                 _w(-0.4, -0.5, 1.8, 1.6, "Laufweg zum Wartepunkt")],
        "ortho": 10.5,
    },
}

RANG = {"voll": 3, "halb": 2, "gelaender": 1.5, "sockel": 1}


def _sonder(sonder, pos):
    for p, art in sonder.items():
        if abs(p - pos) < 0.01:
            return art
    return ""


def huelle_module(zone):
    wx, wz = zone["welt"]
    b, t = zone["breite"], zone["tiefe"]
    liste = []
    for seite, (typ, sonder) in zone["waende"].items():
        quer = seite in ("hinten", "vorn")
        anzahl = int(round(b if quer else t))
        for i in range(anzahl):
            pos = (-b / 2 if quer else -t / 2) + 0.5 + i
            art = _sonder(sonder, pos)
            name = "gelaender" if typ == "gelaender" else "wand_%s%s" % (typ, "_" + art if art else "")
            rang = RANG[typ] + (10 if art else 0)
            if quer:
                z = -t / 2 if seite == "hinten" else t / 2
                liste.append((name, wx + pos, wz + z, 0.0 if seite == "hinten" else 180.0, rang))
            else:
                x = -b / 2 if seite == "links" else b / 2
                liste.append((name, wx + x, wz + pos, 90.0 if seite == "links" else -90.0, rang))
    for sx, sz, s1, s2 in ((-1, -1, "links", "hinten"), (1, -1, "rechts", "hinten"),
                           (-1, 1, "links", "vorn"), (1, 1, "rechts", "vorn")):
        typ = max(zone["waende"][s1][0], zone["waende"][s2][0], key=lambda k: RANG[k])
        pf = "sockel" if typ == "gelaender" else typ
        liste.append(("pfosten_" + pf, wx + sx * b / 2, wz + sz * t / 2, 0.0, RANG[typ]))
    for i in range(int(round(b))):
        for k in range(int(round(t))):
            x = -b / 2 + 0.5 + i
            z = -t / 2 + 0.5 + k
            gx, gz = int(math.floor(wx + x)), int(math.floor(wz + z))
            ab = "a" if (gx + gz) % 2 == 0 else "b"
            liste.append(("boden_%s_%s" % (zone["boden"], ab), wx + x, wz + z, 0.0, 0))
    return liste


_CACHE = {}


def platzieren(pfad, x=0.0, z=0.0, dreh=0.0, y=0.0):
    """Wie importieren(), aber jede Datei wird nur einmal gelesen; weitere
    Exemplare teilen sich das Mesh (schnelle Gesamtvorschau)."""
    m = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh), 4, "Z")
    if pfad not in _CACHE:
        neu = importieren(pfad)
        _CACHE[pfad] = [(o.data, o.matrix_world.copy()) for o in neu if o.type == "MESH"]
        for o in neu:
            o.matrix_world = m @ o.matrix_world
        return
    for daten, basis in _CACHE[pfad]:
        o = bpy.data.objects.new("kopie", daten)
        bpy.context.scene.collection.objects.link(o)
        o.matrix_world = m @ basis


def huellen_aufstellen(namen):
    belegt = {}
    for name in namen:
        for mod, x, z, dreh, rang in huelle_module(ZONEN[name]):
            schl = (round(x, 2), round(z, 2), "b" if mod.startswith("boden") else "w")
            if schl in belegt and belegt[schl][3] >= rang:
                continue
            belegt[schl] = (mod, x, z, rang, dreh)
    for mod, x, z, rang, dreh in belegt.values():
        platzieren(modul.modul_pfad(mod), x=x, z=z, dreh=dreh)


# ==============================================================================
# KLEINTEILE
# ==============================================================================

def kiste_holz(b=0.5, h=0.4, t=0.4, mat="s_palette"):
    teile = [kasten("kiste", (b, h, t), (0, h / 2, 0), mat, rund=0.008, segmente=1)]
    for s in (-1, 1):
        teile.append(kasten("latte", (b + 0.01, 0.05, 0.012), (0, h * 0.72, s * (t / 2 + 0.004)), "holz_moebel"))
        teile.append(kasten("latte", (b + 0.01, 0.05, 0.012), (0, h * 0.28, s * (t / 2 + 0.004)), "holz_moebel"))
    return teile


def flightcase(b=0.7, h=0.45, t=0.45, mat="s_bildschirm"):
    teile = [kasten("case", (b, h, t), (0, h / 2, 0), mat, rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("ecke", (0.06, 0.06, 0.06), (sx * (b / 2 - 0.02), h - 0.02, sz * (t / 2 - 0.02)),
                                "metall_hell"))
    teile.append(kasten("kante", (b + 0.006, 0.03, t + 0.006), (0, h * 0.62, 0), "metall_hell"))
    teile.append(kasten("griff", (0.16, 0.03, 0.03), (0, h * 0.4, t / 2 + 0.02), "metall_hell"))
    return teile


def kabeltrommel(kabel="s_orange", liegend=True):
    r = 0.26
    teile = [
        zylinder("scheibe_u", r, 0.03, (0, 0, 0), "s_gelb", seiten=12),
        zylinder("kern", 0.2, 0.2, (0, 0.03, 0), kabel, seiten=12),
        zylinder("scheibe_o", r, 0.03, (0, 0.23, 0), "s_gelb", seiten=12),
        zylinder("dose", 0.07, 0.08, (0.0, 0.26, 0.0), "kunststoff_dunkel", seiten=8),
        stab("kurbel", (0.12, 0.26, 0.0), (0.2, 0.38, 0.0), 0.025, "kunststoff_dunkel"),
    ]
    if liegend:
        for t in teile:
            t.matrix_world = (Matrix.Translation(G(0, r, 0)) @ Matrix.Rotation(math.radians(90), 4, "Y")
                              @ Matrix.Translation(G(0, -0.13, 0)) @ t.matrix_world)
    return teile


def mast(h=2.6):
    return [zylinder("fuss", 0.14, 0.04, (0, 0, 0), "s_stahl", seiten=8),
            zylinder("mast", 0.03, h, (0, 0.04, 0), "s_stahl", seiten=6)]


def lichterkette(punkte, durchhang=0.18, abstand=0.35):
    """Punkte (x, y, z) Godot; zwischen je zwei Punkten ein durchhaengender
    Draht mit Birnen."""
    teile = []
    for (a, b) in zip(punkte[:-1], punkte[1:]):
        laenge = math.dist(a, b)
        n = max(3, int(laenge / abstand))
        vorher = a
        for i in range(1, n + 1):
            f = i / n
            p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f - durchhang * 4 * f * (1 - f),
                 a[2] + (b[2] - a[2]) * f)
            teile.append(stab("draht", vorher, p, 0.012, "kunststoff_dunkel"))
            if i < n:
                teile.append(kugel("birne", 0.04, (p[0], p[1] - 0.05, p[2]), "s_licht", ringe=3, seiten=5))
            vorher = p
    return teile


def neon_play(breite=0.7):
    """Tafel mit Neon-Rahmen und Play-Dreieck (Akzent Pink)."""
    h = breite * 0.62
    teile = [kasten("tafel", (breite, h, 0.03), (0, h / 2, 0), "s_bildschirm", rund=0.01, segmente=1)]
    k = 0.02
    for (a, b) in (((-breite / 2 + 0.05, 0.05), (breite / 2 - 0.05, 0.05)),
                   ((breite / 2 - 0.05, 0.05), (breite / 2 - 0.05, h - 0.05)),
                   ((breite / 2 - 0.05, h - 0.05), (-breite / 2 + 0.05, h - 0.05)),
                   ((-breite / 2 + 0.05, h - 0.05), (-breite / 2 + 0.05, 0.05))):
        teile.append(stab("neon", (a[0], a[1], 0.03), (b[0], b[1], 0.03), k, "s_neon"))
    d = h * 0.28
    ecken = [(-d * 0.7, h / 2 - d), (-d * 0.7, h / 2 + d), (d, h / 2)]
    for i in range(3):
        a, b = ecken[i], ecken[(i + 1) % 3]
        teile.append(stab("neon", (a[0], a[1], 0.03), (b[0], b[1], 0.03), k, "s_neon"))
    return teile


def softbox_stativ(h=1.7, dreh_kopf=0.0):
    teile = []
    for i in range(3):
        a = math.radians(i * 120 + 30)
        teile.append(stab("bein", (0, 0.55, 0), (math.cos(a) * 0.36, 0.0, math.sin(a) * 0.36), 0.025, "s_stahl"))
    teile.append(zylinder("saeule", 0.02, h - 0.5, (0, 0.5, 0), "s_stahl", seiten=6))
    kopf = [
        kasten("softbox", (0.6, 0.5, 0.26), (0, 0, -0.05), "kunststoff_dunkel", rund=0.02, segmente=1),
        kasten("diffusor", (0.54, 0.44, 0.02), (0, 0, 0.09), "s_licht"),
    ]
    for t in kopf:
        t.matrix_world = (Matrix.Translation(G(0, h, 0)) @ Matrix.Rotation(math.radians(dreh_kopf), 4, "Z")
                          @ Matrix.Rotation(math.radians(-15), 4, "X") @ t.matrix_world)
    return teile + kopf


def kamera_stativ(h=1.35, farbe="kunststoff_dunkel"):
    teile = []
    for i in range(3):
        a = math.radians(i * 120 + 90)
        teile.append(stab("bein", (0, h - 0.1, 0), (math.cos(a) * 0.38, 0.0, math.sin(a) * 0.38), 0.025, "s_stahl"))
    teile += [
        kasten("kopf", (0.1, 0.06, 0.1), (0, h - 0.07, 0), "s_stahl"),
        kasten("kamera", (0.16, 0.14, 0.26), (0, h + 0.07, 0), farbe, rund=0.015, segmente=1),
        liegender_zylinder("objektiv", 0.05, 0.14, (0, h + 0.07, 0.18), "z", "s_stahl", seiten=8),
        liegender_zylinder("glas", 0.035, 0.01, (0, h + 0.07, 0.25), "z", "s_bild_an", seiten=8),
        kasten("monitor", (0.12, 0.08, 0.02), (0.1, h + 0.16, -0.08), "s_bild_an"),
        kugel("rec", 0.015, (0.0, h + 0.15, 0.1), "s_neon", ringe=3, seiten=4),
    ]
    return teile


def sofa(breite=1.7, stoff="stoff_senf", kissen="stoff_weiss", tiefe=0.82):
    t = tiefe
    teile = [
        kasten("basis", (breite, 0.24, t), (0, 0.2, 0), stoff, rund=0.03, segmente=1),
        kasten("lehne", (breite, 0.46, 0.2), (0, 0.49, -t / 2 + 0.1), stoff, rund=0.04, segmente=1),
    ]
    for s in (-1, 1):
        teile.append(kasten("arm", (0.16, 0.34, t), (s * (breite / 2 - 0.08), 0.43, 0), stoff, rund=0.04, segmente=1))
        teile.append(kasten("sitz", ((breite - 0.34) / 2 - 0.01, 0.12, t - 0.24),
                            (s * (breite - 0.34) / 4, 0.38, 0.08), stoff, rund=0.03, segmente=1))
    teile.append(kasten("kissen", (0.36, 0.32, 0.1), (-breite / 2 + 0.36, 0.58, -t / 2 + 0.26), kissen,
                        rund=0.04, segmente=1))
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("fuss", (0.05, 0.08, 0.05), (sx * (breite / 2 - 0.08), 0.04, sz * (t / 2 - 0.08)),
                                "holz_dunkel", unten=False))
    return teile


def poster(b, h, grund, motiv, rahmen="s_stahl"):
    """Gerahmtes Poster mit einfachem Motiv (Kreis + Balken), Rueckseite -z."""
    teile = [kasten("rahmen", (b, h, 0.03), (0, h / 2, 0), rahmen),
             kasten("bild", (b - 0.06, h - 0.06, 0.006), (0, h / 2, 0.016), grund)]
    teile.append(liegender_zylinder("motiv_kreis", b * 0.22, 0.004, (0, h * 0.62, 0.021), "z", motiv, seiten=10))
    teile.append(kasten("motiv_balken", (b * 0.6, h * 0.06, 0.004), (0, h * 0.25, 0.021), "s_leinwand"))
    return teile


def pflanze(groesse=1.0, topf="topf_terra", stil="busch"):
    """Kaktus im Zinkeimer (M1: Kugelbusch-Verbot, D1 B). Gleiche Signatur wie die
    WG-Pflanze, damit alle Aufrufe in diesem Skript sie benutzen."""
    g = groesse
    teile = [zylinder("eimer", 0.17 * g, 0.30 * g, (0, 0, 0), "s_eimer", seiten=10, radius_oben=0.2 * g),
             zylinder("eimerrand", 0.205 * g, 0.03 * g, (0, 0.29 * g, 0), "s_eimer", seiten=10),
             kasten("erde", (0.26 * g, 0.015 * g, 0.26 * g), (0, 0.31 * g, 0), "erde")]
    if stil == "mini":
        teile.append(kugel("kugel", 0.09 * g, (0, 0.40 * g, 0), "s_kaktus", stauchung=1.0, ringe=4, seiten=8))
        teile.append(kugel("bluete", 0.025 * g, (0, 0.50 * g, 0), "s_kaktus_blume", ringe=3, seiten=5))
        return teile
    hoch = 1.0 if stil == "hoch" else 0.62
    teile.append(zylinder("stamm", 0.085 * g, hoch * g, (0, 0.31 * g, 0), "s_kaktus", seiten=8, radius_oben=0.08 * g))
    teile.append(kugel("kuppe", 0.085 * g, (0, (0.31 + hoch) * g, 0), "s_kaktus", stauchung=0.9, ringe=4, seiten=8))
    teile.append(kugel("bluete", 0.03 * g, (0, (0.31 + hoch + 0.09) * g, 0), "s_kaktus_blume", ringe=3, seiten=5))
    arme = ((1, 0.55), (-1, 0.42)) if stil == "hoch" else ((1, 0.35),)
    for seite, ah in arme:
        y = (0.31 + hoch * ah) * g
        teile.append(stab("arm", (0, y, 0), (seite * 0.2 * g, y, 0), 0.05 * g, "s_kaktus_dunkel"))
        teile.append(zylinder("arm_hoch", 0.05 * g, 0.3 * g, (seite * 0.2 * g, y - 0.02 * g, 0), "s_kaktus_dunkel", seiten=7,
                              radius_oben=0.045 * g))
        teile.append(kugel("arm_kuppe", 0.048 * g, (seite * 0.2 * g, y + 0.28 * g, 0), "s_kaktus_dunkel", ringe=3, seiten=7))
    return teile


def pflanze_kuebel(groesse=1.0, topf="s_bildschirm", stil="busch"):
    return pflanze(groesse, topf, stil)


# ==============================================================================
# GARAGE -- Set, Kamera, Schnittplatz (Start)
# ==============================================================================

def rolltor(x0=-0.88, x1=0.68):
    """Angedeutetes Rolltor an der Rueckwand, genau zwischen den beiden
    Stationsflaechen: schmale Fuehrungsschienen mit Warnstreifen, oben der
    Wickelkasten und die Unterkante des hochgerollten Tors."""
    teile = []
    for x in (x0 + 0.03, x1 - 0.03):
        teile.append(kasten("schiene", (0.06, 2.22, 0.14), (x, 1.11, 0), "s_stahl"))
        for y in (0.35, 0.75):
            teile.append(kasten("warn", (0.064, 0.12, 0.146), (x, y, 0), "s_gelb"))
    m = (x0 + x1) / 2
    teile.append(kasten("kasten", (x1 - x0, 0.26, 0.3), (m, 2.35, 0), "s_stahl", rund=0.03, segmente=1))
    teile.append(kasten("lamelle", (x1 - x0 - 0.1, 0.14, 0.04), (m, 2.15, 0.08), "s_stahl_hell"))
    teile.append(kasten("lamelle_2", (x1 - x0 - 0.1, 0.02, 0.05), (m, 2.1, 0.08), "s_stahl"))
    return teile


def werkbank():
    b, h, t = 1.25, 0.9, 0.55
    teile = [kasten("platte", (b, 0.05, t), (0, h - 0.025, 0), "holz_moebel", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.05, h - 0.05, 0.05), (sx * (b / 2 - 0.05), (h - 0.05) / 2, sz * (t / 2 - 0.05)),
                                "s_stahl", unten=False))
    teile.append(kasten("boden", (b - 0.1, 0.03, t - 0.1), (0, 0.18, 0), "holz_moebel_hell"))
    teile.append(kasten("werkzeugkiste", (0.42, 0.2, 0.22), (-0.3, h + 0.1, -0.05), "s_werkzeug", rund=0.015, segmente=1))
    teile.append(kasten("kistengriff", (0.2, 0.03, 0.03), (-0.3, h + 0.22, -0.05), "kunststoff_dunkel"))
    teile.append(kasten("schraubstock", (0.14, 0.12, 0.16), (0.42, h + 0.06, 0.12), "s_blau"))
    teile += transformieren(tasse("s_gelb"), x=0.1, y=h, z=0.12)
    teile += transformieren(kiste_holz(0.4, 0.26, 0.34, "s_palette")[:1], x=-0.25, y=0.195)
    teile.append(kasten("eimer", (0.26, 0.28, 0.26), (0.3, 0.335, 0), "s_orange", rund=0.03, segmente=1))
    return teile


def lochwand():
    """Lochwand auf zwei Pfosten, 1,0 bis 1,9 m, mit Werkzeug."""
    b = 1.25
    teile = [kasten("wand", (b, 0.9, 0.03), (0, 1.45, 0), "s_lochwand", rund=0.008, segmente=1)]
    for s in (-1, 1):
        teile.append(kasten("pfosten", (0.05, 1.92, 0.04), (s * (b / 2 - 0.04), 0.96, -0.035), "s_stahl", unten=False))
    z = 0.025
    teile += [
        kasten("hammer_stiel", (0.03, 0.3, 0.02), (-0.45, 1.5, z), "holz_moebel"),
        kasten("hammer_kopf", (0.12, 0.04, 0.03), (-0.45, 1.66, z), "s_stahl"),
        kasten("schluessel", (0.03, 0.26, 0.012), (-0.3, 1.5, z), "metall_hell"),
        kasten("schluessel_2", (0.03, 0.2, 0.012), (-0.24, 1.53, z), "metall_hell"),
        kasten("saege", (0.36, 0.12, 0.008), (0.05, 1.7, z), "metall_hell"),
        kasten("saege_griff", (0.08, 0.1, 0.02), (-0.15, 1.7, z), "s_werkzeug"),
        kasten("zange", (0.04, 0.2, 0.015), (0.35, 1.52, z), "s_werkzeug"),
        kasten("schraubendreher", (0.025, 0.22, 0.02), (0.45, 1.5, z), "s_gelb"),
        liegender_zylinder("klebeband", 0.06, 0.04, (0.12, 1.3, 0.04), "z", "s_gelb", seiten=8),
        liegender_zylinder("klebeband_2", 0.055, 0.04, (0.27, 1.3, 0.04), "z", "s_blau", seiten=8),
        kasten("ablage", (0.5, 0.03, 0.12), (0.15, 1.2, 0.06), "s_stahl"),
        kasten("dose", (0.08, 0.12, 0.08), (-0.05, 1.28, 0.06), "s_mint"),
    ]
    return teile


def neon_an_wand():
    return transformieren(neon_play(0.62), y=0.72)


def teppich_rund(r, mat, ring):
    return [zylinder("teppich", r, 0.012, (0, 0, 0), mat, seiten=16),
            zylinder("ring", r * 0.7, 0.003, (0, 0.012, 0), ring, seiten=16)]


def einrichtung_garage():
    setzen("rolltor", rolltor(), z=-3.25)
    setzen("neon_wand", neon_an_wand(), x=-3.37, z=-0.15, dreh=90.0)
    setzen("pflanze_links", pflanze(1.3, "topf_terra", "hoch"), x=-2.98, z=-0.85)
    setzen("licht_links", softbox_stativ(1.7, 40.0), x=-2.3, z=1.2, dreh=90.0)
    setzen("kuehlschrank", [kasten("korpus", (0.5, 0.85, 0.5), (0, 0.425, 0), "stoff_weiss", rund=0.03, segmente=1),
                            kasten("fuge", (0.46, 0.012, 0.01), (0, 0.6, 0.252), "s_stahl_hell"),
                            kasten("griff", (0.03, 0.14, 0.03), (0.18, 0.7, 0.26), "s_stahl"),
                            kasten("sticker", (0.12, 0.12, 0.006), (-0.08, 0.35, 0.252), "s_neon")]
           + transformieren(tasse("s_gelb"), x=-0.1, y=0.85) + transformieren(pflanze(0.45, "topf_terra", "mini"),
                                                                           x=0.1, y=0.85),
           x=-3.08, z=1.75, dreh=90.0)
    setzen("pflanze_rechts_hinten", pflanze(0.8, "s_bildschirm"), x=3.15, z=-2.0)
    setzen("cases_rechts", flightcase(0.7, 0.45, 0.45, "s_blau") +
           transformieren(flightcase(0.5, 0.3, 0.4), y=0.45, dreh_grad=-10.0), x=2.6, z=-0.45, dreh=-90.0)
    setzen("kabeltrommel_rechts", kabeltrommel("s_orange"), x=2.7, z=0.8)
    setzen("werkbank", werkbank(), x=-3.05, z=2.68, dreh=90.0)
    setzen("lochwand", lochwand(), x=-3.34, z=2.68, dreh=90.0)
    setzen("sofa_rechts", sofa(1.5, "s_mint", "s_gelb", 0.78), x=3.0, z=2.55, dreh=-90.0)
    setzen("teppich_rechts", teppich(1.3, 1.6, "teppich_creme", "teppich_terra"), x=2.3, z=2.55)
    setzen("kabeltrommel_vorn", kabeltrommel("s_blau", liegend=False), x=1.6, z=3.0)
    setzen("cases_vorn", flightcase(0.8, 0.45, 0.45) + transformieren(flightcase(0.6, 0.3, 0.4, "s_stahl"), y=0.45,
                                                                       dreh_grad=8.0), x=-0.4, z=3.05)
    setzen("pflanze_vorn_links", pflanze(0.9, "topf_terra"), x=-1.9, z=3.05)
    setzen("pflanze_vorn_mitte", pflanze(0.8, "s_bildschirm"), x=0.75, z=3.1)
    setzen("kabel_boden", [kasten("kabel", (0.02, 0.012, 1.8), (1.2, 0.006, -0.3), "kunststoff_dunkel"),
                           kasten("kabel_2", (1.3, 0.012, 0.02), (1.85, 0.006, 0.6), "kunststoff_dunkel")])


# ==============================================================================
# HOF -- Pflaster, Container, Lichterkette
# ==============================================================================

def container(b=0.85, h=2.3, t=2.7):
    """Container-Kante am rechten Hofende: ein schmaler Container-Anschnitt
    (0,85 x 2,3 x 2,8), Tueren zur Station (-x), Rippen auf den sichtbaren
    Seiten, pinker Neonpfeil zur Station."""
    teile = [kasten("koerper", (b, h, t), (0, h / 2, 0), "s_container", rund=0.02, segmente=1),
             kasten("dachrahmen", (b + 0.02, 0.08, t + 0.02), (0, h - 0.04, 0), "s_container_2")]
    for i in range(3):
        x = -b / 2 + 0.17 + i * (b - 0.34) / 2
        teile.append(kasten("rippe", (0.07, h - 0.3, 0.03), (x, h / 2, t / 2 + 0.005), "s_container_2", unten=False))
    for i in range(10):
        z = -t / 2 + 0.2 + i * (t - 0.4) / 9
        teile.append(kasten("rippe_s", (0.03, h - 0.3, 0.07), (b / 2 - 0.005, h / 2, z), "s_container_2", unten=False))
    for s_ in (-1, 1):
        teile.append(kasten("tuer", (0.03, h - 0.2, t / 2 - 0.06), (-b / 2 - 0.005, h / 2, s_ * t / 4), "s_container_2"))
        teile.append(kasten("riegel", (0.03, h - 0.4, 0.03), (-b / 2 - 0.02, h / 2, s_ * 0.25), "s_stahl_hell"))
    y0 = 1.7
    for (a, c) in (((0.3, y0), (-0.28, y0)), ((-0.28, y0), (-0.1, y0 + 0.16)), ((-0.28, y0), (-0.1, y0 - 0.16))):
        teile.append(stab("neon", (a[0], a[1], t / 2 + 0.025), (c[0], c[1], t / 2 + 0.025), 0.03, "s_neon"))
    teile.append(kasten("lueftung", (0.4, 0.22, 0.5), (0.0, h + 0.11, -0.7), "s_stahl_hell", rund=0.02, segmente=1))
    teile += transformieren(pflanze(0.6, "topf_terra"), x=0.0, y=h, z=0.6)
    return teile


def bank():
    b = 1.4
    teile = []
    for i in range(3):
        teile.append(kasten("latte", (b, 0.035, 0.11), (0, 0.44, -0.14 + i * 0.14), "holz_moebel_hell", rund=0.008, segmente=1))
    teile.append(kasten("lehne", (b, 0.1, 0.035), (0, 0.72, -0.24), "holz_moebel_hell", rund=0.008, segmente=1))
    teile.append(kasten("lehne_2", (b, 0.1, 0.035), (0, 0.6, -0.24), "holz_moebel_hell", rund=0.008, segmente=1))
    for s in (-1, 1):
        teile.append(kasten("fuss", (0.05, 0.42, 0.4), (s * (b / 2 - 0.12), 0.21, 0), "s_stahl", unten=False))
        teile.append(kasten("lehnstuetze", (0.04, 0.4, 0.04), (s * (b / 2 - 0.12), 0.62, -0.24), "s_stahl"))
    teile += transformieren(tasse("s_gelb"), x=0.4, y=0.4575, z=0.0)
    return teile


def palette(b=1.2, t=0.8):
    teile = []
    for i in range(5):
        teile.append(kasten("brett", (b, 0.022, 0.12), (0, 0.133, -t / 2 + 0.06 + i * (t - 0.12) / 4), "s_palette"))
    for sx in (-1, 0, 1):
        teile.append(kasten("klotz", (0.1, 0.1, t), (sx * (b / 2 - 0.05), 0.072, 0), "holz_moebel", unten=False))
    teile.append(kasten("unten", (b, 0.022, 0.12), (0, 0.011, 0), "holz_moebel", unten=False))
    return teile


def palettenlounge():
    teile = palette() + transformieren(palette(), y=0.144)
    teile.append(kasten("polster", (1.16, 0.12, 0.76), (0, 0.35, 0), "s_samt_dunkel", rund=0.04, segmente=1))
    teile.append(kasten("rueckenkissen", (1.1, 0.34, 0.14), (0, 0.55, -0.3), "stoff_weiss", rund=0.05, segmente=1))
    teile.append(kasten("kissen", (0.34, 0.3, 0.1), (0.35, 0.53, -0.18), "s_gelb", rund=0.05, segmente=1))
    return teile


def kuebel_baum(h=1.8):
    return [kasten("kuebel", (0.55, 0.5, 0.55), (0, 0.25, 0), "s_palette", rund=0.02, segmente=1),
            kasten("erde", (0.48, 0.02, 0.48), (0, 0.5, 0), "erde"),
            zylinder("stamm", 0.04, h * 0.55, (0, 0.5, 0), "s_stamm", seiten=6),
            kugel("krone", 0.42, (0, h * 0.8, 0), "s_baum", stauchung=0.9, ringe=5, seiten=8),
            kugel("krone_2", 0.28, (0.2, h * 0.9, 0.12), "s_baum_3", ringe=4, seiten=7)]


def wandbild_hof(b=1.7):
    """Bunte Farbflaechen an der Innenseite der linken Hofmauer (lokal +z)."""
    z = 0.006
    return [
        liegender_zylinder("sonne", 0.42, 0.012, (0.0, 1.5, z), "z", "s_gelb", seiten=14),
        kasten("welle_1", (b, 0.16, 0.012), (0.0, 0.85, z), "s_neon"),
        kasten("welle_2", (b, 0.16, 0.012), (0.0, 0.6, z), "s_blau"),
        kasten("welle_3", (b, 0.12, 0.012), (0.0, 0.38, z), "s_lila"),
        kasten("streifen", (0.14, 1.2, 0.012), (-b / 2 + 0.12, 1.5, z + 0.002), "s_mint"),
        kasten("streifen_2", (0.14, 0.9, 0.012), (b / 2 - 0.12, 1.4, z + 0.002), "s_orange"),
    ]


def einrichtung_hof():
    setzen("wandbild", wandbild_hof(), x=-10.39, z=-0.45, dreh=90.0)
    setzen("pflanze_links", pflanze(0.9, "topf_terra"), x=-9.9, z=0.95)
    setzen("fahrrad_1", fahrrad(), x=-9.0, z=-1.2)
    setzen("fahrrad_2", fahrrad(), x=-5.2, z=-1.15, dreh=180.0)
    setzen("bank", bank(), x=-3.3, z=-1.08)
    setzen("pflanze_bank", pflanze(1.0, "topf_terra"), x=-2.3, z=-1.12)
    setzen("kuebel_mitte", kuebel_baum(1.7), x=-1.3, z=-0.92)
    setzen("palettenlounge", palettenlounge(), x=3.0, z=-0.95)
    setzen("kuebel_rechts", kuebel_baum(1.8), x=4.2, z=-0.95)
    setzen("container", container(), x=9.97, z=0.0)
    setzen("kiste_rechts", kiste_holz(0.5, 0.4, 0.4, "s_orange"), x=6.95, z=-1.1, dreh=90.0)
    setzen("mast_1", mast(), x=-10.2, z=-1.25)
    setzen("mast_2", mast(), x=-5.9, z=-1.25)
    setzen("mast_3", mast(), x=-1.75, z=-1.25)
    setzen("mast_4", mast(), x=1.95, z=-1.25)
    setzen("mast_5", mast(), x=4.95, z=-1.25)
    setzen("lichterkette_1", lichterkette([(-10.2, 2.6, -1.25), (-5.9, 2.6, -1.25)]))
    setzen("lichterkette_1b", lichterkette([(-5.9, 2.6, -1.25), (-1.75, 2.6, -1.25)]))
    setzen("lichterkette_2", lichterkette([(1.95, 2.6, -1.25), (4.95, 2.6, -1.25)]))
    setzen("lichterkette_3", lichterkette([(4.95, 2.6, -1.25), (9.55, 2.3, -1.3)], durchhang=0.12))
    setzen("kiste_vorn", kiste_holz(0.5, 0.4, 0.4) + transformieren(kiste_holz(0.4, 0.3, 0.35), y=0.4, dreh_grad=15),
           x=-4.3, z=1.05)
    setzen("pflanze_vorn_1", pflanze(0.7, "s_bildschirm"), x=-2.4, z=1.1)
    setzen("pflanze_vorn_2", pflanze(0.8, "topf_terra"), x=2.8, z=1.1)
    setzen("case_vorn", flightcase(0.6, 0.4, 0.4, "s_stahl"), x=4.2, z=1.1)


# ==============================================================================
# REQUISITE -- Regale, Kleiderstaender, Kisten
# ==============================================================================

def _requisit(art, x, y, z):
    """Kleine Requisiten fuer Regalboeden, Unterkante bei y."""
    if art == "globus":
        return [zylinder("fuss", 0.06, 0.03, (x, y, z), "s_gold", seiten=8),
                zylinder("achse", 0.012, 0.08, (x, y + 0.03, z), "s_gold", seiten=4),
                kugel("globus", 0.1, (x, y + 0.2, z), "s_blau", ringe=5, seiten=8),
                kugel("land", 0.06, (x + 0.05, y + 0.23, z + 0.04), "s_baum", ringe=3, seiten=5)]
    if art == "helm":
        return [kugel("helm", 0.12, (x, y + 0.02, z), "s_gelb", stauchung=0.8, ringe=4, seiten=8),
                kasten("visier", (0.18, 0.05, 0.03), (x, y + 0.06, z + 0.1), "s_bildschirm")]
    if art == "pokal":
        return [kasten("sockel", (0.1, 0.05, 0.1), (x, y + 0.025, z), "holz_dunkel"),
                zylinder("stiel", 0.02, 0.1, (x, y + 0.05, z), "s_gold", seiten=6),
                zylinder("kelch", 0.04, 0.12, (x, y + 0.15, z), "s_gold", seiten=8, radius_oben=0.08)]
    if art == "lampe":
        return [zylinder("fuss", 0.07, 0.25, (x, y, z), "s_mint", seiten=8, radius_oben=0.04),
                zylinder("schirm", 0.13, 0.14, (x, y + 0.25, z), "lampe_licht", seiten=10, radius_oben=0.08)]
    if art == "vase":
        return [zylinder("vase", 0.06, 0.22, (x, y, z), "s_gelb", seiten=8, radius_oben=0.03),
                kugel("blume", 0.05, (x, y + 0.27, z), "s_gelb", ringe=3, seiten=5)]
    if art == "koffer":
        return [kasten("koffer", (0.36, 0.26, 0.14), (x, y + 0.13, z), "s_orange", rund=0.02, segmente=1),
                kasten("gurt", (0.03, 0.262, 0.145), (x - 0.08, y + 0.13, z), "holz_dunkel")]
    if art == "boxen":
        return [kasten("box", (0.26, 0.2, 0.26), (x - 0.05, y + 0.1, z), "s_lila", rund=0.01, segmente=1),
                kasten("box_2", (0.2, 0.14, 0.2), (x + 0.02, y + 0.27, z), "s_mint", rund=0.01, segmente=1)]
    if art == "buecher":
        return transformieren(buchstapel(3), x=x, y=y, z=z)
    if art == "schaedel":
        return [kugel("kopf", 0.08, (x, y + 0.09, z), "stoff_weiss", ringe=4, seiten=7),
                kasten("kiefer", (0.08, 0.04, 0.06), (x, y + 0.025, z + 0.03), "stoff_weiss")]
    if art == "kamera_alt":
        return [kasten("koerper", (0.2, 0.14, 0.12), (x, y + 0.07, z), "holz_moebel", rund=0.01, segmente=1),
                liegender_zylinder("objektiv", 0.045, 0.1, (x, y + 0.07, z + 0.1), "z", "s_gold", seiten=8)]
    return []


def regal_metall(b=1.4, h=2.0, t=0.45, requisiten=()):
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("pfosten", (0.04, h, 0.04), (sx * (b / 2 - 0.02), h / 2, sz * (t / 2 - 0.02)),
                                "s_stahl", unten=False))
    boeden = [0.12, 0.62, 1.12, 1.62, h - 0.02]
    for y in boeden:
        teile.append(kasten("boden", (b, 0.03, t), (0, y, 0), "holz_moebel_hell"))
    for i, reihe in enumerate(requisiten):
        y = boeden[i] + 0.015
        for k, art in enumerate(reihe):
            x = -b / 2 + (k + 0.5) * b / len(reihe)
            teile += _requisit(art, x, y, 0.0)
    return teile


def schneiderpuppe(farbe="s_lochwand"):
    return [
        zylinder("fuss", 0.16, 0.03, (0, 0, 0), "holz_dunkel", seiten=8),
        zylinder("stange", 0.02, 0.9, (0, 0.03, 0), "holz_dunkel", seiten=5),
        kugel("torso", 0.2, (0, 1.15, 0), farbe, stauchung=1.5, ringe=5, seiten=8),
        kasten("schultern", (0.42, 0.1, 0.2), (0, 1.36, 0), farbe, rund=0.04, segmente=1),
        kasten("rock", (0.36, 0.2, 0.3), (0, 0.9, 0), "s_gelb", rund=0.04, segmente=1),
        zylinder("hals", 0.04, 0.1, (0, 1.42, 0), "holz_moebel_hell", seiten=6),
        kasten("kragen", (0.2, 0.04, 0.12), (0, 1.38, 0.02), "stoff_weiss"),
    ]


def standspiegel():
    teile = [kasten("rahmen", (0.55, 1.5, 0.05), (0, 0.85, 0), "s_gold", rund=0.02, segmente=1),
             kasten("glas", (0.45, 1.38, 0.01), (0, 0.85, 0.028), "s_himmel")]
    teile.append(stab("stuetze", (0, 1.2, -0.03), (0, 0.0, -0.4), 0.04, "s_gold"))
    teile.append(kasten("fuss", (0.55, 0.05, 0.08), (0, 0.025, 0), "s_gold"))
    return teile


def leiter():
    teile = []
    for s in (-1, 1):
        teile.append(stab("holm", (s * 0.2, 0.0, 0.35), (s * 0.2, 1.9, 0.0), 0.05, "holz_moebel_hell"))
    for i in range(6):
        f = (i + 1) / 7.0
        teile.append(kasten("sprosse", (0.4, 0.03, 0.04), (0, 1.9 * f, 0.35 * (1 - f)), "holz_moebel_hell"))
    return teile


def sessel_samt():
    return sofa(0.95, "s_lila", "s_gelb", 0.8)


def einrichtung_requisite():
    setzen("regal_hinten", regal_metall(1.5, 2.0, 0.45, (("koffer",), ("globus", "pokal"),
                                                           ("lampe", "buecher"), ("schaedel", "kamera_alt"))),
           x=-0.5, z=-2.15)
    setzen("regal_links_hinten", regal_metall(1.3, 2.0, 0.45, (("boxen",), ("helm", "lampe"),
                                                                 ("buecher", "pokal"), ("globus", "vase"))),
           x=-3.15, z=-1.55, dreh=90.0)
    setzen("regal_links_vorn", regal_metall(1.3, 2.0, 0.45, (("koffer",), ("kamera_alt", "boxen"),
                                                               ("vase", "schaedel"), ("lampe", "buecher"))),
           x=-3.15, z=1.55, dreh=90.0)
    setzen("kisten_fenster_l", kiste_holz(0.6, 0.45, 0.45) + transformieren(kiste_holz(0.45, 0.32, 0.4, "s_mint"),
                                                                             y=0.45, dreh_grad=10), x=-2.0, z=-2.1)
    setzen("kisten_fenster_r", kiste_holz(0.55, 0.4, 0.45, "s_orange") + transformieren(kiste_holz(), x=0.6),
           x=0.85, z=-2.12)
    setzen("truhe_fenster", flightcase(0.8, 0.5, 0.45, "holz_moebel"), x=-3.0, z=0.0, dreh=90.0)
    setzen("kleiderstange_links", kleiderstange(), x=-1.55, z=1.65)
    setzen("kleiderstange_rechts", kleiderstange(), x=2.2, z=1.75, dreh=-8.0)
    setzen("schneiderpuppe", schneiderpuppe(), x=-1.3, z=-0.9)
    setzen("standspiegel", standspiegel(), x=2.72, z=-1.6, dreh=-90.0)
    setzen("sessel", sessel_samt(), x=1.35, z=-1.35, dreh=-20.0)
    setzen("leiter", leiter(), x=2.55, z=-2.05)
    setzen("koffer_boden", _requisit("koffer", 0, 0, 0) + _requisit("koffer", 0.05, 0.26, 0.0), x=-2.2, z=0.9,
           dreh=80.0)
    setzen("teppich", teppich(1.6, 1.1, "s_samt", "s_gelb"), x=1.3, z=-1.3)
    setzen("kisten_rechts", kiste_holz(0.6, 0.45, 0.45, "s_mint") + transformieren(kiste_holz(0.45, 0.3, 0.4),
                                                                                   y=0.45, dreh_grad=-12),
           x=3.0, z=0.3, dreh=-90.0)


# ==============================================================================
# GREENSCREEN -- Hohlkehle, Stative (Sonderstation in der Mitte)
# ==============================================================================

def hohlkehle(breite=4.6, hoehe=2.2, rueck=-2.35, vorn=-1.15, radius=0.4):
    """Gruene Hohlkehle: Boden -> Viertelkreis -> Wand, als duennes Profil
    entlang x extrudiert. Oben ein Traversenrohr auf zwei Stativen."""
    innen = [(vorn, 0.012), (rueck + radius, 0.012)]
    aussen = []
    for k in range(1, 6):
        a = math.radians(90.0 * k / 6.0)
        innen.append((rueck + radius - (radius - 0.012) * math.sin(a), radius - (radius - 0.012) * math.cos(a)))
    innen += [(rueck + 0.012, radius), (rueck + 0.012, hoehe)]
    aussen = [(rueck, hoehe), (rueck, radius)]
    for k in range(5, 0, -1):
        a = math.radians(90.0 * k / 6.0)
        aussen.append((rueck + radius - radius * math.sin(a), radius - radius * math.cos(a)))
    aussen += [(rueck + radius, 0.0), (vorn, 0.0)]
    punkte = innen + aussen
    teile = [profil_x("kehle", punkte, -breite / 2, breite / 2, "s_gruen_screen")]
    for s in (-1, 1):
        teile.append(zylinder("stativ", 0.025, hoehe + 0.1, (s * (breite / 2 + 0.08), 0.05, rueck - 0.0), "s_stahl", seiten=6))
        teile.append(zylinder("stativfuss", 0.2, 0.05, (s * (breite / 2 + 0.08), 0.0, rueck + 0.18), "s_stahl", seiten=6))
    teile.append(liegender_zylinder("traverse", 0.03, breite + 0.3, (0, hoehe + 0.12, rueck), "x", "s_stahl", seiten=6))
    teile.append(liegender_zylinder("rolle", 0.07, breite, (0, hoehe + 0.02, rueck + 0.03), "x", "s_gruen_screen", seiten=8))
    return teile


def regiestuhl(farbe="s_container"):
    teile = []
    for s in (-1, 1):
        teile.append(stab("x1", (s * 0.24, 0.0, -0.2), (s * 0.24, 0.45, 0.2), 0.03, "holz_moebel"))
        teile.append(stab("x2", (s * 0.24, 0.0, 0.2), (s * 0.24, 0.45, -0.2), 0.03, "holz_moebel"))
        teile.append(kasten("hinten", (0.03, 0.95, 0.03), (s * 0.24, 0.475, -0.2), "holz_moebel"))
        teile.append(kasten("armlehne", (0.05, 0.03, 0.42), (s * 0.24, 0.68, 0.0), "holz_moebel"))
    teile.append(kasten("sitz", (0.46, 0.02, 0.38), (0, 0.46, 0), farbe))
    teile.append(kasten("lehne", (0.46, 0.18, 0.02), (0, 0.84, -0.2), farbe))
    return teile


def apfelkisten():
    teile = kiste_holz(0.5, 0.2, 0.3, "holz_moebel_hell")[:1]
    teile += transformieren(kiste_holz(0.5, 0.2, 0.3, "s_palette")[:1], y=0.2, dreh_grad=12)
    teile.append(kugel("sandsack", 0.16, (0.45, 0.07, 0.05), "s_orange", stauchung=0.45, ringe=4, seiten=8))
    return teile


def on_air(h=1.5):
    return [zylinder("fuss", 0.16, 0.03, (0, 0, 0), "s_stahl", seiten=8),
            zylinder("stange", 0.02, h, (0, 0.03, 0), "s_stahl", seiten=5),
            kasten("leuchte", (0.42, 0.18, 0.08), (0, h + 0.09, 0), "s_bildschirm", rund=0.02, segmente=1),
            kasten("schrift", (0.34, 0.1, 0.01), (0, h + 0.09, 0.042), "s_neon")]


def einrichtung_greenscreen():
    setzen("hohlkehle", hohlkehle(rueck=-2.1), x=0.4)
    setzen("licht_hinten_links", softbox_stativ(1.8, -35.0), x=-2.7, z=-1.75)
    setzen("licht_hinten_rechts", softbox_stativ(1.8, 35.0), x=2.3, z=-0.65, dreh=-60.0)
    setzen("kamera", kamera_stativ(), x=-2.2, z=1.75, dreh=-135.0)
    setzen("licht_vorn", softbox_stativ(1.6, 0.0), x=-2.9, z=1.1, dreh=110.0)
    setzen("regiestuhl", regiestuhl(), x=-1.55, z=0.95, dreh=100.0)
    setzen("apfelkisten", apfelkisten(), x=-1.3, z=-0.75, dreh=10.0)
    setzen("on_air", on_air(), x=3.05, z=-0.2, dreh=-90.0)
    setzen("pflanze_vorn_rechts", pflanze(1.1, "topf_terra", "hoch"), x=3.05, z=2.1)
    setzen("case_vorn_links", flightcase(0.6, 0.35, 0.4), x=-1.0, z=2.1)
    setzen("pflanze_links", pflanze(1.1, "topf_terra"), x=-2.95, z=-0.2)
    setzen("kabel", [kasten("kabel", (1.6, 0.012, 0.02), (-2.0, 0.006, 0.6), "kunststoff_dunkel"),
                     kasten("kabel_2", (0.02, 0.012, 1.2), (-1.2, 0.006, 1.2), "kunststoff_dunkel")])


# ==============================================================================
# DACH -- Holzdeck, Sonnenschirm, Lichterketten
# ==============================================================================

def sitzgruppe_schirm():
    teile = [
        zylinder("schirmfuss", 0.22, 0.08, (0, 0, 0), "s_stahl", seiten=8),
        zylinder("schirmstange", 0.025, 2.05, (0, 0.08, 0), "s_stahl_hell", seiten=6),
        zylinder("schirm", 0.9, 0.3, (0, 1.85, 0), "s_schirm", seiten=8, radius_oben=0.05),
        zylinder("schirmrand", 0.91, 0.06, (0, 1.82, 0), "stoff_weiss", seiten=8),
        zylinder("platte", 0.36, 0.035, (0, 0.7, 0), "stoff_weiss", seiten=12),
        zylinder("tischfuss", 0.2, 0.03, (0.0, 0.08, 0.0), "s_stahl", seiten=8),
    ]
    teile += transformieren(tasse("s_gelb"), x=0.15, y=0.735, z=0.1)
    teile.append(zylinder("krug", 0.05, 0.16, (-0.12, 0.735, -0.05), "s_himmel", seiten=8))
    for dreh in (60.0, -120.0):
        stuhl = [kasten("sitz", (0.42, 0.05, 0.42), (0, 0.44, 0), "s_mint", rund=0.015, segmente=1),
                 kasten("lehne", (0.42, 0.34, 0.04), (0, 0.66, -0.2), "s_mint", rund=0.015, segmente=1)]
        for sx in (-1, 1):
            stuhl.append(kasten("bein", (0.03, 0.42, 0.36), (sx * 0.18, 0.21, 0), "s_stahl", unten=False))
        transformieren(stuhl, x=math.sin(math.radians(dreh)) * -0.75, z=math.cos(math.radians(dreh)) * -0.75,
                       dreh_grad=dreh)
        teile += stuhl
    return teile


def liegestuhl(farbe="s_gelb"):
    teile = [kasten("rahmen", (0.62, 0.08, 1.5), (0, 0.22, 0.1), "holz_moebel", rund=0.015, segmente=1),
             kasten("polster", (0.56, 0.06, 1.1), (0, 0.29, 0.3), farbe, rund=0.025, segmente=1)]
    lehne = [kasten("lehne", (0.56, 0.07, 0.6), (0, 0, -0.3), farbe, rund=0.025, segmente=1),
             kasten("lehnenrahmen", (0.62, 0.05, 0.6), (0, -0.05, -0.3), "holz_moebel")]
    for t in lehne:
        t.matrix_world = Matrix.Translation(G(0, 0.3, -0.45)) @ Matrix.Rotation(math.radians(50), 4, "X") @ t.matrix_world
    teile += lehne
    for sx in (-1, 1):
        for sz in (-0.55, 0.75):
            teile.append(kasten("fuss", (0.05, 0.18, 0.05), (sx * 0.26, 0.09, sz), "holz_dunkel", unten=False))
    teile += transformieren([kasten("handtuch", (0.4, 0.03, 0.3), (0, 0, 0), "s_gelb", rund=0.01, segmente=1)],
                            y=0.335, z=0.6, dreh_grad=12)
    return teile


def pflanzkasten(laenge=1.4, blueten=("s_gelb", "stoff_weiss")):
    teile = [kasten("kasten", (laenge, 0.45, 0.4), (0, 0.225, 0), "s_palette", rund=0.02, segmente=1),
             kasten("erde", (laenge - 0.06, 0.02, 0.34), (0, 0.45, 0), "erde")]
    n = int(laenge / 0.35)
    for i in range(n):
        x = -laenge / 2 + (i + 0.5) * laenge / n
        teile.append(kugel("busch", 0.2, (x, 0.58, 0), "s_baum" if i % 2 else "s_baum_3", stauchung=0.8, ringe=4, seiten=7))
        teile.append(kugel("bluete", 0.05, (x + 0.05, 0.74, 0.08), blueten[i % len(blueten)], ringe=3, seiten=5))
    return teile


def grill():
    teile = [kugel("kessel", 0.28, (0, 0.72, 0), "s_bildschirm", stauchung=0.8, ringe=5, seiten=10),
             kasten("rost", (0.42, 0.02, 0.42), (0, 0.74, 0), "s_stahl_hell")]
    for i in range(3):
        a = math.radians(i * 120)
        teile.append(stab("bein", (0, 0.6, 0), (math.cos(a) * 0.3, 0.0, math.sin(a) * 0.3), 0.03, "s_stahl"))
    teile.append(kasten("kuehlbox", (0.5, 0.36, 0.34), (0.55, 0.18, 0.1), "s_blau", rund=0.03, segmente=1))
    teile.append(kasten("deckel", (0.52, 0.06, 0.36), (0.55, 0.39, 0.1), "stoff_weiss", rund=0.02, segmente=1))
    return teile


def einrichtung_dach():
    setzen("sitzgruppe", sitzgruppe_schirm(), x=-2.1, z=-1.46)
    setzen("lounge", palettenlounge(), x=1.8, z=-1.95)
    setzen("pflanzkasten_hinten", pflanzkasten(1.4), x=-0.1, z=-2.15)
    setzen("pflanzkasten_rechts", pflanzkasten(1.4, ("s_orange", "stoff_weiss")), x=3.15, z=-0.2, dreh=-90.0)
    setzen("liegestuhl_1", liegestuhl(), x=0.9, z=0.35, dreh=-15.0)
    setzen("liegestuhl_2", liegestuhl("s_mint"), x=2.05, z=0.25, dreh=-15.0)
    setzen("pflanze_vorn", pflanze(0.9, "topf_terra"), x=2.9, z=1.9)
    setzen("grill", grill(), x=-2.6, z=1.7)
    setzen("kamera_dach", kamera_stativ(1.45, "kunststoff_dunkel"), x=-2.4, z=0.35, dreh=120.0)
    setzen("pflanze_ecke", pflanze(1.3, "topf_terra", "hoch"), x=2.95, z=-1.98)
    setzen("mast_1", mast(2.5), x=-3.2, z=-2.2)
    setzen("mast_2", mast(2.5), x=3.2, z=-1.25)
    setzen("mast_3", mast(2.5), x=3.2, z=2.2)
    setzen("lichterkette", lichterkette([(-3.2, 2.5, -2.2), (3.2, 2.5, -1.25)], durchhang=0.3))
    setzen("lichterkette_2", lichterkette([(3.2, 2.5, -1.25), (3.2, 2.5, 2.2)], durchhang=0.3))


# ==============================================================================
# KINO -- Leinwand, zwei Sitzreihen, Popcorn, roter Teppich
# ==============================================================================

def leinwand(breite=3.6):
    """Leinwand an der hohen linken Wand (Rueckseite lokal -z), mit einem
    laufenden 'Film' aus Farbflaechen und roten Vorhaengen seitlich."""
    u, o = 0.55, 2.3
    teile = [kasten("rahmen", (breite, o - u, 0.06), (0, (u + o) / 2, 0), "s_bildschirm", rund=0.015, segmente=1),
             kasten("tuch", (breite - 0.14, o - u - 0.14, 0.01), (0, (u + o) / 2, 0.034), "s_leinwand")]
    z = 0.042
    teile += [
        kasten("himmel", (breite - 0.3, 0.9, 0.004), (0, 1.62, z), "s_bild_an"),
        liegender_zylinder("sonne", 0.2, 0.004, (0.9, 1.8, z + 0.003), "z", "s_gelb", seiten=12),
        kasten("huegel", (1.6, 0.5, 0.004), (-0.6, 0.95, z), "s_baum_3"),
        kasten("huegel_2", (1.5, 0.35, 0.004), (0.8, 0.88, z + 0.002), "s_baum"),
    ]
    for s in (-1, 1):
        teile.append(kasten("vorhang", (0.34, 2.2, 0.12), (s * (breite / 2 + 0.12), 1.1, 0.05), "s_samt",
                            rund=0.04, segmente=1))
        teile.append(kasten("vorhang_falte", (0.08, 2.2, 0.14), (s * (breite / 2 + 0.05), 1.1, 0.06), "s_samt_dunkel"))
    teile.append(kasten("buehne", (breite + 0.9, 0.25, 0.55), (0, 0.125, 0.3), "holz_dunkel", rund=0.02, segmente=1))
    teile.append(kasten("buehnenkante", (breite + 0.9, 0.03, 0.02), (0, 0.2, 0.58), "s_neon"))
    return teile


def lautsprecher(h=1.3):
    return [kasten("box", (0.42, h, 0.36), (0, h / 2, 0), "kunststoff_dunkel", rund=0.02, segmente=1),
            liegender_zylinder("membran", 0.13, 0.02, (0, h * 0.35, 0.18), "z", "s_stahl", seiten=10),
            liegender_zylinder("hochtoener", 0.06, 0.02, (0, h * 0.75, 0.18), "z", "s_stahl", seiten=8)]


def sitzreihe(n=3, podest=0.0):
    """Kinosessel nebeneinander entlang x, Blick nach +z."""
    teile = []
    b = 0.72
    if podest > 0:
        teile.append(kasten("podest", (n * b + 0.3, podest, 0.95), (0, podest / 2, -0.05), "s_teppich_fuge",
                            rund=0.015, segmente=1))
    y = podest
    for i in range(n):
        x = (i - (n - 1) / 2) * b
        teile.append(kasten("sitz", (b - 0.14, 0.14, 0.55), (x, y + 0.36, 0.05), "s_samt", rund=0.04, segmente=1))
        teile.append(kasten("lehne", (b - 0.14, 0.6, 0.16), (x, y + 0.62, -0.28), "s_samt", rund=0.05, segmente=1))
    for i in range(n + 1):
        x = (i - n / 2) * b
        teile.append(kasten("armlehne", (0.1, 0.6, 0.7), (x, y + 0.3, -0.05), "s_samt_dunkel", rund=0.02, segmente=1))
    teile.append(kasten("becher", (0.06, 0.1, 0.06), (-n / 2 * b, y + 0.65, 0.18), "s_gelb"))
    return teile


def popcornmaschine():
    teile = [kasten("wagen", (0.6, 0.7, 0.45), (0, 0.45, 0), "s_samt", rund=0.02, segmente=1),
             kasten("zierleiste", (0.62, 0.05, 0.47), (0, 0.72, 0), "s_gelb")]
    for sx in (-1, 1):
        teile.append(liegender_zylinder("rad", 0.1, 0.04, (sx * 0.24, 0.1, 0.24), "z", "s_bildschirm", seiten=10))
    teile += [
        kasten("vitrine", (0.5, 0.5, 0.38), (0, 1.05, 0), "s_himmel"),
        kasten("popcorn", (0.46, 0.22, 0.34), (0, 0.92, 0), "s_popcorn"),
        kugel("haufen", 0.18, (0.05, 1.02, 0.0), "s_popcorn", stauchung=0.6, ringe=4, seiten=8),
        kasten("dach", (0.6, 0.1, 0.46), (0, 1.35, 0), "s_samt", rund=0.02, segmente=1),
        kasten("schild", (0.4, 0.14, 0.03), (0, 1.47, 0.0), "s_gelb"),
        kasten("tuete", (0.1, 0.16, 0.06), (0.36, 0.78, 0.1), "s_samt"),
        kugel("tuete_pop", 0.05, (0.36, 0.87, 0.1), "s_popcorn", ringe=3, seiten=5),
    ]
    for sx in (-1, 1):
        teile.append(kasten("saeule", (0.04, 0.5, 0.04), (sx * 0.27, 1.05, 0.17), "s_gold"))
    return teile


def absperrung(anzahl=3, abstand=1.0):
    teile = []
    for i in range(anzahl):
        z = i * abstand
        teile += [zylinder("fuss", 0.12, 0.03, (0, 0, z), "s_gold", seiten=8),
                  zylinder("pfosten", 0.025, 0.85, (0, 0.03, z), "s_gold", seiten=6),
                  kugel("knauf", 0.04, (0, 0.9, z), "s_gold", ringe=3, seiten=6)]
        if i < anzahl - 1:
            for k in range(4):
                a = z + 0.05 + k * (abstand - 0.1) / 4
                b = a + (abstand - 0.1) / 4
                ya = 0.8 - 0.18 * math.sin(math.pi * (a - z) / abstand)
                yb = 0.8 - 0.18 * math.sin(math.pi * (b - z) / abstand)
                teile.append(stab("seil", (0, ya, a), (0, yb, b), 0.03, "s_samt"))
    return teile


def projektor():
    return [zylinder("fuss", 0.16, 0.03, (0, 0, 0), "s_stahl", seiten=8),
            zylinder("saeule", 0.03, 1.05, (0, 0.03, 0), "s_stahl", seiten=6),
            kasten("geraet", (0.34, 0.16, 0.3), (0, 1.16, 0), "stoff_weiss", rund=0.03, segmente=1),
            liegender_zylinder("linse", 0.05, 0.05, (0, 1.16, 0.17), "z", "s_bild_an", seiten=8)]


def getraenketisch():
    return [zylinder("platte", 0.28, 0.03, (0, 0.5, 0), "s_gold", seiten=10),
            zylinder("fuss", 0.04, 0.5, (0, 0, 0), "s_gold", seiten=6),
            zylinder("becher", 0.04, 0.14, (0.08, 0.53, 0.02), "s_samt", seiten=6),
            zylinder("becher_2", 0.04, 0.14, (-0.08, 0.53, -0.04), "s_blau", seiten=6),
            kasten("schale", (0.14, 0.05, 0.1), (0.0, 0.555, 0.12), "s_popcorn")]


def einrichtung_kino():
    setzen("leinwand", leinwand(), x=-3.2, z=0.3, dreh=90.0)
    setzen("lautsprecher_hinten", lautsprecher(), x=-3.05, z=-2.2, dreh=70.0)
    setzen("lautsprecher_vorn", lautsprecher(), x=-3.05, z=2.6, dreh=110.0)
    setzen("reihe_1", sitzreihe(3), x=-1.35, z=0.3, dreh=-90.0)
    setzen("reihe_2", sitzreihe(3, podest=0.22), x=0.25, z=0.3, dreh=-90.0)
    setzen("popcorn", popcornmaschine(), x=3.0, z=-3.05, dreh=-90.0)
    setzen("teppich_rot", teppich(0.8, 2.4, "s_samt", "s_gelb", h=0.015), x=0.0, z=-2.2)
    setzen("absperrung", absperrung(3, 1.0), x=0.76, z=-3.2)
    setzen("projektor", projektor(), x=1.35, z=0.3, dreh=-90.0)
    setzen("poster_1", poster(0.5, 0.72, "s_lila", "s_gelb"), x=-2.3, y=0.3, z=-3.37)
    setzen("poster_2", poster(0.5, 0.72, "s_blau", "s_gelb"), x=-1.5, y=0.3, z=-3.37)
    setzen("sitzsack_1", sitzsack(), x=-1.6, z=2.55)
    setzen("sitzsack_2", [kugel("sack", 0.44, (0, 0.23, 0), "s_container", stauchung=0.55, ringe=6, seiten=12),
                          kugel("mulde", 0.28, (0.02, 0.34, 0.06), "s_container", stauchung=0.45, ringe=4, seiten=10)],
           x=-0.4, z=2.8)
    setzen("getraenketisch", getraenketisch(), x=-2.6, z=2.7)
    setzen("pflanze_vorn_links", pflanze(1.2, "topf_terra", "hoch"), x=-2.2, z=3.05)
    setzen("pflanze_vorn_rechts", pflanze(0.9, "s_bildschirm"), x=3.0, z=3.0)
    setzen("pflanze_hinten", pflanze(0.9, "topf_terra"), x=1.25, z=-3.1)
    setzen("sitzsack_3", sitzsack(), x=2.5, z=1.3)
    setzen("pflanze_rechts", pflanze(1.3, "topf_terra", "hoch"), x=3.0, z=-1.2)


# ==============================================================================
# YOUNES' ECKE -- Schnittplatz, Sofa, Platten
# ==============================================================================

def schreibtisch_doppel():
    b, h, t = 1.5, 0.75, 0.7
    teile = [kasten("platte", (b, 0.04, t), (0, h - 0.02, 0), "holz_moebel_hell", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("wange", (0.05, h - 0.04, t - 0.1), (sx * (b / 2 - 0.05), (h - 0.04) / 2, 0), "s_stahl",
                            unten=False))
    for i, (x, dreh) in enumerate(((-0.32, 12.0), (0.32, -12.0))):
        mon = [kasten("fuss", (0.2, 0.02, 0.14), (0, h + 0.01, 0), "s_stahl"),
               kasten("arm", (0.04, 0.2, 0.03), (0, h + 0.1, -0.03), "s_stahl"),
               kasten("monitor", (0.58, 0.34, 0.04), (0, h + 0.36, 0), "s_bildschirm", rund=0.01, segmente=1),
               kasten("bild", (0.52, 0.28, 0.005), (0, h + 0.36, 0.022), "s_bild_an" if i == 0 else "s_lila")]
        # Schnitt-Spuren auf dem zweiten Monitor
        if i == 1:
            for k, (m, w) in enumerate((("s_blau", 0.3), ("s_gelb", 0.2), ("s_mint", 0.36))):
                mon.append(kasten("spur", (w, 0.04, 0.004), (-0.1 + w / 4, h + 0.28 + k * 0.07, 0.026), m))
        transformieren(mon, x=x, z=-0.12, dreh_grad=dreh)
        teile += mon
    teile += [
        kasten("tastatur", (0.44, 0.02, 0.14), (0, h + 0.01, 0.18), "stoff_weiss"),
        kasten("maus", (0.06, 0.02, 0.09), (0.33, h + 0.01, 0.18), "stoff_weiss"),
        kasten("rechner", (0.22, 0.46, 0.46), (-0.55, 0.23, 0.0), "s_bildschirm", rund=0.01, segmente=1),
        kasten("rechner_licht", (0.005, 0.36, 0.02), (-0.44, 0.24, 0.2), "s_neon"),
    ]
    teile += transformieren(tasse("s_gelb"), x=0.58, y=h, z=0.12)
    return teile


def buerostuhl():
    teile = [kasten("sitz", (0.48, 0.08, 0.46), (0, 0.48, 0), "s_bildschirm", rund=0.03, segmente=1),
             kasten("lehne", (0.44, 0.52, 0.07), (0, 0.84, -0.22), "s_bildschirm", rund=0.03, segmente=1),
             kasten("lehne_akzent", (0.3, 0.3, 0.01), (0, 0.86, -0.18), "s_blau"),
             zylinder("saeule", 0.03, 0.4, (0, 0.05, 0), "s_stahl", seiten=6)]
    for i in range(5):
        a = math.radians(i * 72)
        teile.append(stab("stern", (0, 0.06, 0), (math.cos(a) * 0.3, 0.03, math.sin(a) * 0.3), 0.035, "s_stahl"))
    return teile


def sideboard_platten():
    b, h, t = 1.4, 0.6, 0.42
    teile = [kasten("korpus", (b, h - 0.08, t), (0, 0.08 + (h - 0.08) / 2, 0), "holz_moebel", rund=0.015, segmente=1)]
    for i in range(3):
        teile.append(kasten("front", (b / 3 - 0.03, h - 0.16, 0.01), (-b / 3 + i * b / 3, 0.34, t / 2 + 0.004),
                            ("s_mint", "stoff_weiss", "s_gelb")[i]))
    for sx in (-1, 1):
        teile.append(kasten("fuss", (0.04, 0.08, 0.04), (sx * (b / 2 - 0.08), 0.04, 0), "s_stahl", unten=False))
    # Plattenspieler
    teile += [
        kasten("spieler", (0.44, 0.08, 0.34), (-0.3, h + 0.04, 0.0), "stoff_weiss", rund=0.01, segmente=1),
        zylinder("platte", 0.14, 0.012, (-0.34, h + 0.08, 0.0), "kunststoff_dunkel", seiten=14),
        zylinder("label", 0.05, 0.004, (-0.34, h + 0.092, 0.0), "s_gelb", seiten=8),
        stab("tonarm", (-0.13, h + 0.1, -0.1), (-0.24, h + 0.1, 0.06), 0.015, "s_stahl"),
        kasten("box_l", (0.2, 0.3, 0.2), (0.3, h + 0.15, 0.0), "holz_dunkel", rund=0.01, segmente=1),
        liegender_zylinder("box_m", 0.06, 0.02, (0.3, h + 0.13, 0.1), "z", "s_stahl", seiten=8),
    ]
    teile += transformieren(pflanze(0.5, "topf_terra", "mini"), x=0.58, y=h)
    return teile


def plattenkiste():
    teile = kiste_holz(0.45, 0.32, 0.36, "s_palette")[:1]
    for i, m in enumerate(("s_samt", "s_blau", "s_gelb", "kunststoff_dunkel", "s_lila")):
        teile.append(kasten("platte", (0.012, 0.3, 0.3), (-0.16 + i * 0.07, 0.3, 0), m))
    return teile


def wandposter():
    teile = []
    for x, g, m in ((-0.35, "s_gelb", "s_samt"), (0.3, "s_samt", "s_blau")):
        teile += transformieren(poster(0.46, 0.4, g, m), x=x)
    return teile


def couchtisch():
    teile = [kasten("platte", (0.9, 0.04, 0.55), (0, 0.4, 0), "holz_moebel_hell", rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.04, 0.38, 0.04), (sx * 0.4, 0.19, sz * 0.22), "s_stahl", unten=False))
    teile += transformieren(buchstapel(2), x=-0.2, y=0.42)
    teile += transformieren(tasse("s_gelb"), x=0.25, y=0.42, z=0.1)
    teile.append(kasten("kamera", (0.16, 0.12, 0.1), (0.1, 0.48, -0.1), "s_bildschirm", rund=0.01, segmente=1))
    teile.append(liegender_zylinder("objektiv", 0.04, 0.08, (0.1, 0.48, -0.01), "z", "s_stahl", seiten=8))
    return teile


def regal_niedrig():
    b, h, t = 1.2, 0.8, 0.36
    teile = [kasten("korpus", (b, h, t), (0, h / 2, 0), "stoff_weiss", rund=0.012, segmente=1),
             kasten("fach", (b - 0.06, h / 2 - 0.06, 0.01), (0, h * 0.28, t / 2 + 0.002), "holz_moebel_hell"),
             kasten("fach_2", (b - 0.06, h / 2 - 0.06, 0.01), (0, h * 0.72, t / 2 + 0.002), "holz_moebel_hell")]
    for i, (x, r) in enumerate(((-0.4, 0.05), (-0.22, 0.04), (0.0, 0.06))):
        teile.append(zylinder("objektiv", r, 0.14 + i * 0.03, (x, h, 0), "s_bildschirm", seiten=8))
    teile += transformieren(buchstapel(2), x=0.35, y=h)
    return teile


def einrichtung_younes_ecke():
    setzen("schreibtisch", schreibtisch_doppel(), x=1.9, z=-2.95)
    setzen("buerostuhl", buerostuhl(), x=1.9, z=-2.15, dreh=160.0)
    setzen("sideboard", sideboard_platten(), x=-2.36, z=-3.1)
    setzen("wandposter", wandposter(), x=-2.36, y=0.7, z=-3.37)
    setzen("plattenkiste", plattenkiste(), x=0.3, z=-3.1, dreh=15.0)
    setzen("sofa", sofa(2.0, "s_blau", "s_gelb"), x=-2.95, z=-1.2, dreh=90.0)
    setzen("teppich", teppich(2.0, 2.2, "teppich_creme", "s_gelb"), x=-1.8, z=-1.2)
    setzen("couchtisch", couchtisch(), x=-1.87, z=-1.2, dreh=90.0)
    setzen("stehlampe", stehlampe(), x=-2.85, z=-2.65, dreh=-30.0)
    setzen("pflanze_gross", pflanze(1.45, "topf_terra", "hoch"), x=-3.0, z=2.9)
    setzen("sitzsack", sitzsack(), x=-1.7, z=2.6)
    setzen("koffer", flightcase(0.7, 0.4, 0.45) + transformieren(kamera_stativ(0.4)[4:6], x=0.1),
           x=1.3, z=2.5, dreh=-10.0)
    setzen("koffer_2", flightcase(0.55, 0.3, 0.4, "s_stahl"), x=2.35, z=2.85, dreh=20.0)
    setzen("regal_rechts", regal_niedrig(), x=3.12, z=-0.4, dreh=-90.0)
    setzen("gitarre", gitarre(), x=3.1, z=0.9, dreh=-90.0)
    setzen("pflanze_vorn_rechts", pflanze(0.8, "s_bildschirm"), x=3.05, z=3.05)
    setzen("pflanze_mitte", pflanze(0.9, "topf_terra"), x=0.95, z=-1.3)


# ==============================================================================
# UMGEBUNG (Weltkoordinaten) UND FUNDAMENT
# ==============================================================================

AUSSEN_Y = -0.47                       # Unterkante Fundament = Hofniveau
FUNDAMENT = (-11.5, 11.5, -9.5, 7.5)   # Grundflaeche + 1 m Rand
AUSSEN = (-18.0, 17.5, -15.5, 12.5)
UMGEBUNG_BUDGET = 12000


def baum(rng, h=3.6, r=1.2):
    teile = [kasten("scheibe", (1.2, 0.06, 1.2), (0, 0.03, 0), "s_bordstein"),
             kasten("beet", (1.0, 0.02, 1.0), (0, 0.06, 0), "s_rasen"),
             zylinder("stamm", 0.13, h * 0.55, (0, 0.06, 0), "s_stamm", seiten=7, radius_oben=0.08)]
    ballen = [(0.0, h - r * 0.9, 0.0, r, "s_baum")]
    for i in range(3):
        a = rng.uniform(0, 2 * math.pi) + i * 2.1
        ballen.append((math.cos(a) * r * 0.5, h - r * 1.15 + rng.uniform(-0.1, 0.25), math.sin(a) * r * 0.5,
                       r * rng.uniform(0.6, 0.72), ("s_baum_2", "s_baum_3", "s_baum")[i]))
    for x, y, z, rr, m in ballen:
        teile.append(kugel("krone", rr, (x, y, z), m, stauchung=0.88, ringe=5, seiten=8))
    return teile


def laterne(h=4.0):
    return [zylinder("fuss", 0.16, 0.3, (0, 0, 0), "s_stahl", seiten=8),
            zylinder("mast", 0.06, h, (0, 0.3, 0), "s_stahl", seiten=6, radius_oben=0.045),
            stab("arm", (0, h + 0.2, 0), (0.7, h + 0.3, 0), 0.05, "s_stahl"),
            kasten("kopf", (0.5, 0.12, 0.26), (0.85, h + 0.26, 0), "s_stahl", rund=0.03, segmente=1),
            kasten("licht", (0.4, 0.02, 0.18), (0.85, h + 0.19, 0), "s_licht")]


def tonne(farbe):
    return [kasten("tonne", (0.6, 0.95, 0.7), (0, 0.475, 0), "s_tonne_grau", rund=0.04, segmente=1),
            kasten("deckel", (0.64, 0.06, 0.74), (0, 0.98, 0.0), farbe, rund=0.02, segmente=1),
            liegender_zylinder("rad", 0.08, 0.66, (0, 0.08, -0.33), "x", "kunststoff_dunkel", seiten=6)]


def nachbarwand(laenge, hoehe, motive):
    """Hohe Backsteinwand entlang x (Innenseite +z) mit Wandbild."""
    teile = [kasten("wand", (laenge, hoehe, 0.4), (0, hoehe / 2, 0), "s_ziegel"),
             kasten("kappe", (laenge + 0.06, 0.1, 0.46), (0, hoehe + 0.05, 0), "s_beton_kappe")]
    z = 0.21
    for i in range(int(hoehe / 0.32)):
        teile.append(kasten("fuge", (laenge, 0.02, 0.004), (0, 0.32 * (i + 1), z), "s_moertel"))
    for art, x, y, a, b, m in motive:
        if art == "kreis":
            teile.append(liegender_zylinder("kreis", a, 0.012, (x, y, z + 0.012), "z", m, seiten=16))
        elif art == "band":
            teile.append(kasten("band", (a, b, 0.012), (x, y, z + 0.01), m))
        elif art == "berg":
            teile.append(kasten("berg", (a, a, 0.012), (x, y, z + 0.014), m))
            transformieren([teile[-1]], x=0, dreh_grad=0)
            teile[-1].matrix_world = (Matrix.Translation(G(x, y, z + 0.014)) @ Matrix.Rotation(math.radians(45), 4, "Y")
                                      @ Matrix.Translation(-G(x, y, z + 0.014)) @ teile[-1].matrix_world)
    return teile


def einrichtung_umgebung():
    rng = random.Random(20)
    x0, x1, z0, z1 = AUSSEN
    fx0, fx1, fz0, fz1 = FUNDAMENT
    y = AUSSEN_Y
    # Pflasterflaeche in vier Streifen um das Fundament
    boden = [
        kasten("boden_hinten", (x1 - x0, 0.03, fz0 - z0), ((x0 + x1) / 2, y + 0.015, (z0 + fz0) / 2), "s_boden_aussen", unten=False),
        kasten("boden_vorn", (x1 - x0, 0.03, z1 - fz1), ((x0 + x1) / 2, y + 0.015, (fz1 + z1) / 2), "s_boden_aussen", unten=False),
        kasten("boden_links", (fx0 - x0, 0.03, fz1 - fz0), ((x0 + fx0) / 2, y + 0.015, (fz0 + fz1) / 2), "s_boden_aussen", unten=False),
        kasten("boden_rechts", (x1 - fx1, 0.03, fz1 - fz0), ((fx1 + x1) / 2, y + 0.015, (fz0 + fz1) / 2), "s_boden_aussen", unten=False),
    ]
    # Pflastermuster: versetzte Flecken im zweiten Ton
    for _ in range(46):
        px, pz = rng.uniform(x0 + 0.5, x1 - 0.5), rng.uniform(z0 + 0.5, z1 - 3.0)
        if fx0 - 0.4 < px < fx1 + 0.4 and fz0 - 0.4 < pz < fz1 + 0.4:
            continue
        boden.append(kasten("fleck", (rng.choice((0.5, 1.0)), 0.004, 0.5), (px, y + 0.032, pz), "s_boden_aussen_2", unten=False))
    setzen("boden", boden)
    # Strasse vorn: Bordstein, Asphalt, Mittelmarkierung (flach)
    strasse = [kasten("bordstein", (x1 - x0, 0.12, 0.25), ((x0 + x1) / 2, y + 0.06, 10.0), "s_bordstein", unten=False),
               kasten("asphalt", (x1 - x0, 0.02, 2.3), ((x0 + x1) / 2, y + 0.035, 11.3), "s_asphalt", unten=False)]
    x = x0 + 0.8
    while x < x1 - 1:
        strasse.append(kasten("markierung", (1.0, 0.004, 0.12), (x, y + 0.047, 11.4), "s_markierung", unten=False))
        x += 2.0
    setzen("strasse", strasse)
    # Nachbarwand hinten mit Wandbild, Seitenwand links
    motive = [("kreis", -8.0, 2.6, 1.3, 0, "s_gelb"), ("band", 0.0, 1.4, 34.0, 0.35, "s_wandpink"),
              ("band", 0.0, 0.95, 34.0, 0.3, "s_blau"), ("berg", -3.5, 1.9, 1.6, 0, "s_lila"),
              ("berg", -1.0, 1.7, 1.2, 0, "s_mint"), ("kreis", 5.0, 2.9, 0.9, 0, "s_orange"),
              ("band", 9.0, 2.9, 3.0, 0.25, "s_lila"), ("band", 9.0, 3.4, 2.2, 0.25, "s_gelb"),
              ("kreis", 13.5, 2.5, 0.7, 0, "s_wandpink")]
    setzen("nachbarwand", nachbarwand(x1 - x0, 4.4, motive), x=(x0 + x1) / 2, y=y, z=z0 + 0.25)
    # Nachbarhaus: zwei erleuchtete, zwei dunkle Fenster (Abendlicht, jemand ist zu Hause)
    for i, wx in enumerate((-11.0, -4.5, 2.5, 9.5)):
        an = i in (1, 3)
        setzen("nachbar_fenster_%d" % i,
               [kasten("rahmen", (1.1, 1.3, 0.05), (0, 2.75, 0.0), "s_stahl"),
                kasten("scheibe", (0.92, 1.12, 0.03), (0, 2.75, 0.03), "s_licht" if an else "s_bildschirm"),
                kasten("sprosse", (0.04, 1.12, 0.04), (0, 2.75, 0.05), "s_stahl"),
                kasten("bank", (1.2, 0.06, 0.14), (0, 2.08, 0.07), "s_beton_kappe")],
               x=wx, y=y, z=z0 + 0.25 + 0.22)
    setzen("seitenwand", nachbarwand(z1 - 4.0 - z0, 3.0, [("band", 0.0, 1.2, z1 - 4.0 - z0, 0.3, "s_mint"),
                                                           ("kreis", -3.0, 2.2, 0.6, 0, "s_wandpink")]),
           x=x0 + 0.25, y=y, z=(z0 + z1 - 4.0) / 2, dreh=90.0)
    # Baeume hinten und links
    for i, (bx, bz) in enumerate(((-14.5, -13.2), (-8.5, -13.3), (-2.5, -13.1), (3.5, -13.3), (9.5, -13.2),
                                  (15.0, -13.0), (-16.2, -8.0), (-16.3, -2.5), (-16.1, 3.0))):
        setzen("baum_%d" % i, baum(rng, rng.uniform(3.3, 4.2), rng.uniform(1.0, 1.25)), x=bx, y=y, z=bz,
               dreh=rng.uniform(0, 360))
    for i, bx in enumerate((-12.0, -6.0, 0.5, 6.5)):
        setzen("wandbeet_%d" % i, [kasten("beet", (2.2, 0.12, 0.6), (0, 0.06, 0), "s_rasen", rund=0.03, segmente=1),
                                   kugel("busch", 0.32, (-0.5, 0.25, 0), "s_baum_3", stauchung=0.8, ringe=4, seiten=7),
                                   kugel("busch_2", 0.26, (0.45, 0.22, 0.05), "s_baum", stauchung=0.8, ringe=4, seiten=7),
                                   kugel("bluete", 0.07, (0.0, 0.2, 0.15), "s_gelb", ringe=3, seiten=5)],
               x=bx, y=y, z=-14.7)
    setzen("laterne_1", laterne(), x=-12.8, y=y, z=-11.6, dreh=-45.0)
    setzen("laterne_2", laterne(), x=-13.5, y=y, z=1.0)
    # Muelltonnen, Paletten, Kisten hinten
    for i, (tx, m) in enumerate(((-6.4, "s_tonne_grau"), (-5.6, "s_tonne_blau"), (-4.8, "s_tonne_gelb"),
                                 (-4.0, "s_orange"))):
        setzen("tonne_%d" % i, tonne(m), x=tx, y=y, z=-12.9)
    setzen("paletten", palette() + transformieren(palette(), y=0.144, dreh_grad=6) +
           transformieren(palette(), y=0.288, dreh_grad=-4), x=6.5, y=y, z=-12.6)
    setzen("kisten_hinten", kiste_holz(0.6, 0.5, 0.5) + transformieren(kiste_holz(0.5, 0.4, 0.45, "s_mint"),
                                                                       y=0.5, dreh_grad=20), x=12.3, y=y, z=-12.8)
    setzen("kuebel_hinten", kuebel_baum(2.2), x=0.8, y=y, z=-12.9)
    # Links: Fahrradstaender, Bank
    for i, bz in enumerate((-5.0, -4.2, -3.4)):
        setzen("fahrrad_links_%d" % i, fahrrad(), x=-14.2, y=y, z=bz, dreh=90.0)
    setzen("bank_links", bank(), x=-15.4, y=y, z=5.8, dreh=90.0)
    setzen("tonne_links", tonne("s_tonne_blau"), x=-14.0, y=y, z=-9.8, dreh=90.0)
    # Rechts und vorn: nur Niedriges (<= 1 m)
    for i, (hx, hz, lang, dreh) in enumerate(((14.8, -6.0, 3.0, 90.0), (14.8, 5.5, 2.4, 90.0), (-6.0, 8.8, 3.0, 0.0),
                                              (5.0, 8.8, 3.0, 0.0), (-13.8, 8.8, 2.0, 0.0))):
        setzen("pflanzkasten_%d" % i, pflanzkasten(lang, ("s_gelb", "stoff_weiss", "s_gelb")), x=hx, y=y, z=hz,
               dreh=dreh)
    for i, px in enumerate((-2.0, 0.0, 2.0, 12.6)):
        setzen("poller_%d" % i, [zylinder("poller", 0.08, 0.6, (0, 0, 0), "s_stahl", seiten=8),
                                 zylinder("ring", 0.085, 0.06, (0, 0.45, 0), "s_neon", seiten=8)],
               x=px, y=y, z=9.4)
    setzen("bank_vorn", bank(), x=9.5, y=y, z=8.8, dreh=180.0)
    for i, (bx, bz) in enumerate(((15.6, -1.0), (-9.5, 9.0), (1.5, 9.0), (15.8, 8.5))):
        setzen("busch_%d" % i, [kugel("busch", 0.45, (0, 0.3, 0), "s_baum", stauchung=0.7, ringe=4, seiten=8),
                                kugel("busch_2", 0.3, (0.3, 0.25, 0.1), "s_baum_3", stauchung=0.7, ringe=4, seiten=7)],
               x=bx, y=y, z=bz)


def einrichtung_fundament():
    fx0, fx1, fz0, fz1 = FUNDAMENT
    h = 0.45
    setzen("fundament", [kasten("sockel", (fx1 - fx0, h, fz1 - fz0), ((fx0 + fx1) / 2, -0.02 - h / 2, (fz0 + fz1) / 2),
                                "s_fundament", rund=0.06, segmente=2)])


# ==============================================================================
# ABLAUF
# ==============================================================================

EINRICHTUNGEN = {
    "garage": einrichtung_garage,
    "hof": einrichtung_hof,
    "requisite": einrichtung_requisite,
    "greenscreen": einrichtung_greenscreen,
    "dach": einrichtung_dach,
    "kino": einrichtung_kino,
    "younes_ecke": einrichtung_younes_ecke,
}
AUSSENTEILE = {"umgebung": einrichtung_umgebung, "fundament": einrichtung_fundament}
ERGEBNIS = []


def pfad(name):
    return os.path.join(AUSGABE, name + ".glb")


def _export(name, budget):
    obj = verbinden([t for _, teile in MOEBEL for t in teile], name)
    leuchten_setzen()
    exportieren(obj, pfad(name))
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    print("  -> %s: %d Dreiecke (Budget %d)%s, %d Mat, %.0f KB, BBox x %+.2f..%+.2f y %.2f..%.2f z %+.2f..%+.2f"
          % (name, n, budget, "  <-- UEBER BUDGET" if n > budget else "", len(obj.data.materials),
             os.path.getsize(pfad(name)) / 1024.0, x0, x1, y0, y1, z0, z1))
    ERGEBNIS.append((name, n))
    return n


def zone_bauen(name):
    alles_loeschen()
    del MOEBEL[:]
    zone = ZONEN[name]
    EINRICHTUNGEN[name]()
    print("")
    print("=== EINRICHTUNG %s (%g x %g) ===" % (name.upper(), zone["breite"], zone["tiefe"]))
    _, zu_viel = moebel_bericht()
    fehler = freiflaechen_pruefen(zone)
    _export("einrichtung_" + name, ZONEN_BUDGET)
    print("     Freiflaechen-/Wandpruefung: %s" % ("OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler))
    return fehler + zu_viel


def aussen_bauen(name):
    alles_loeschen()
    del MOEBEL[:]
    AUSSENTEILE[name]()
    print("")
    print("=== %s ===" % name.upper())
    _, zu_viel = moebel_bericht(MOEBEL_BUDGET if name == "umgebung" else 1000)
    _export(name, UMGEBUNG_BUDGET)
    return 0


def freiflaechen_markieren(zone, x=0.0, z=0.0):
    palette_erweitern({"vorschau_frei": ("#3DDC84", 0.9, 0.0, 1.0),
                       "vorschau_weg": ("#FFFFFF", 0.9, 0.0, 1.0)})
    for (fx, fz, fb, ft, _, art) in zone["frei"]:
        d = 0.05
        mat = "vorschau_frei" if art == "S" else "vorschau_weg"
        for (gx, gz, sb, st) in ((fx, fz - ft / 2 + d / 2, fb, d), (fx, fz + ft / 2 - d / 2, fb, d),
                                 (fx - fb / 2 + d / 2, fz, d, ft), (fx + fb / 2 - d / 2, fz, d, ft)):
            kasten("frei", (sb, 0.006, st), (x + gx, 0.004 + (0.002 if art == "S" else 0), z + gz), mat)


def zone_vorschau(name):
    alles_loeschen()
    _CACHE.clear()
    zone = dict(ZONEN[name])
    zone["welt"] = (0.0, 0.0)
    for mod, x, z, dreh, _ in huelle_module(zone):
        platzieren(modul.modul_pfad(mod), x=x, z=z, dreh=dreh)
    importieren(pfad("einrichtung_" + name))
    freiflaechen_markieren(zone)
    leuchten_setzen()
    vorschau_rendern(os.path.join(VORSCHAU, "zone_%s.png" % name), (0.0, 0.6, 0.0), zone["ortho"])


def gesamt_vorschau(mit_markierung=False):
    alles_loeschen()
    _CACHE.clear()
    namen = list(EINRICHTUNGEN)
    huellen_aufstellen(namen)
    for name in namen:
        wx, wz = ZONEN[name]["welt"]
        importieren(pfad("einrichtung_" + name), x=wx, z=wz)
        if mit_markierung:
            freiflaechen_markieren(ZONEN[name], wx, wz)
    importieren(pfad("umgebung"))
    importieren(pfad("fundament"))
    leuchten_setzen()
    datei = "gesamt_markiert.png" if mit_markierung else "gesamt.png"
    vorschau_rendern(os.path.join(VORSCHAU, datei), (-0.3, 0.3, -1.2), 31.0, aufloesung=1800)
    if not mit_markierung:
        vorschau_rendern(os.path.join(VORSCHAU, "gesamt_nah_links.png"), (-6.0, 0.6, -1.5), 15.0, aufloesung=1400)
        vorschau_rendern(os.path.join(VORSCHAU, "gesamt_nah_rechts.png"), (5.0, 0.6, -1.0), 15.0, aufloesung=1400)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    gewaehlt = [a for a in argumente if a in EINRICHTUNGEN or a in AUSSENTEILE]
    alle = not gewaehlt
    ohne_vorschau = "--ohne-vorschau" in argumente
    nur_gesamt = "--nur-gesamt" in argumente
    fehler = 0
    if not nur_gesamt:
        for name in (gewaehlt or list(EINRICHTUNGEN) + list(AUSSENTEILE)):
            if name in EINRICHTUNGEN:
                fehler += zone_bauen(name)
                if not ohne_vorschau:
                    zone_vorschau(name)
            else:
                fehler += aussen_bauen(name)
    if not ohne_vorschau and (alle or nur_gesamt):
        gesamt_vorschau()
        gesamt_vorschau(mit_markierung=True)
    print("")
    for name, n in ERGEBNIS:
        print("  %-28s %6d Dreiecke" % (name, n))
    print("=== FERTIG: %s ===" % ("keine Verletzungen" if fehler == 0 else "%d Probleme -- siehe oben" % fehler))


if __name__ == "__main__":
    main()
