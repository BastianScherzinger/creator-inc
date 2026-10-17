"""Einrichtung, Umgebung, Fundament und Fluss-Teil fuer Welt 5 `produkt`
(alte Fabrikhalle), Nachtplan N40 (docs/NACHT_PLAN.md 2 und 5,
docs/nacht/karten_welten.md).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_produkt.py
    (optional nach "--": Zonennamen -> nur diese; --ohne-vorschau; --nur-gesamt)

Voraussetzung: build_room_produkt_neu.py ist gelaufen (Module fuer die Vorschau).

Erzeugt project/assets/world/produkt/:
    einrichtung_<zone>.glb   EIN Mesh je Zone, Ursprung = Zonenmitte (Godot)
    umgebung.glb             Industriegelaende ringsum, Ursprung 0,0
    fundament.glb            Sockel unter der Grundflaeche + 1 m Rand
    fluss_teil.glb           leuchtender Datenwuerfel, <= 0,35 m
und Vorschauen nach art_source/vorschau/produkt/.

Freiflaechen (Stationen 2,2 x 2,2, Tuergaenge, Laufwege) prueft das Skript
selbst; ueber Laufwegen darf nur haengen, was hoeher als 1,9 m ist.
Koordinaten: GODOT. Moebel lokal mit Vorderseite +z; dreh=90 -> Vorderseite +x.
Das Skript ist eigenstaendig (nur build_room_wg und build_room_produkt_neu).
"""

import bpy
import math
import os
import random
import sys
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_room_produkt_neu as modul  # noqa: E402  (Palette, Leuchten, Pfade)
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, transformieren, alles_loeschen,
    verbinden, dreiecke, masse, exportieren, importieren, palette_erweitern, WURZEL,
)

AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "produkt")
VORSCHAU = modul.AUSGABE_VORSCHAU

palette_erweitern({
    "rack_p":         ("#2E2C40", 0.50, 0.20, 1.0),
    "rack_front_p":   ("#4A3F9E", 0.45, 0.30, 1.0),
    "alu_p":          ("#C9CED8", 0.35, 0.55, 1.0),
    "grau_p":         ("#6A6F7E", 0.60, 0.20, 1.0),
    "hellgrau_p":     ("#8A8F9C", 0.60, 0.0, 1.0),
    "weiss_p":        ("#D8DAE2", 0.60, 0.0, 1.0),
    "dunkel_p":       ("#26252F", 0.55, 0.0, 1.0),
    "gummi_p":        ("#2A2A30", 0.80, 0.0, 1.0),
    "schrank_p":      ("#4C5262", 0.55, 0.20, 1.0),
    "trafo_p":        ("#5C7868", 0.55, 0.20, 1.0),
    "isolator_p":     ("#E9E2D0", 0.40, 0.0, 1.0),
    "kupfer_p":       ("#C77A45", 0.40, 0.60, 1.0),
    "rot_p":          ("#E0463A", 0.55, 0.0, 1.0),
    "orange_p":       ("#FF8A3D", 0.60, 0.0, 1.0),
    "gelb_p":         ("#FFC21A", 0.60, 0.0, 1.0),
    "violett_p":      ("#8B5CF6", 0.45, 0.0, 1.0),
    "violett_d_p":    ("#2B2740", 0.50, 0.0, 1.0),
    "lila_hell_p":    ("#9EA6B8", 0.70, 0.0, 1.0),
    "cyan_p":         ("#2FC6D6", 0.50, 0.0, 1.0),
    "holz_p":         ("#D7AE7C", 0.75, 0.0, 1.0),
    "holz_d_p":       ("#9C6D45", 0.85, 0.0, 1.0),
    "palette_p":      ("#DDB77F", 0.85, 0.0, 1.0),
    "karton_p":       ("#C99A62", 0.90, 0.0, 1.0),
    "karton_h_p":     ("#DDB47C", 0.90, 0.0, 1.0),
    "stoff_p":        ("#3E4160", 0.95, 0.0, 1.0),
    "stoff_senf_p":   ("#E3A93B", 0.90, 0.0, 1.0),
    "stoff_koralle_p": ("#EE8F7E", 0.90, 0.0, 1.0),
    "pflanze_p":      ("#5DA84A", 0.80, 0.0, 1.0),
    "pflanze_d_p":    ("#3E8A3B", 0.80, 0.0, 1.0),
    "topf_p":         ("#C9744A", 0.85, 0.0, 1.0),
    "erde_p":         ("#5C4030", 0.95, 0.0, 1.0),
    "stamm_p":        ("#8A6446", 0.90, 0.0, 1.0),
    "solar_p":        ("#2C3E7A", 0.25, 0.30, 1.0),
    "solar_linie_p":  ("#8FA6E0", 0.40, 0.0, 1.0),
    "bildschirm_p":   ("#1F2233", 0.35, 0.0, 1.0),
    "notiz_gelb_p":   ("#FFE066", 0.80, 0.0, 1.0),
    "notiz_rosa_p":   ("#FF9FB2", 0.80, 0.0, 1.0),
    "rasen_p":        ("#343B44", 0.95, 0.0, 1.0),
    "rasen_d_p":      ("#2E343C", 0.95, 0.0, 1.0),
    "asphalt_p":      ("#2B2D37", 0.90, 0.0, 1.0),
    "pflaster_p":     ("#3A3D49", 0.90, 0.0, 1.0),
    "pflaster_d_p":   ("#30333E", 0.90, 0.0, 1.0),
    "fundament_p":    ("#5A5D6A", 0.90, 0.0, 1.0),
    "container_a_p":  ("#2F6B78", 0.60, 0.20, 1.0),
    "container_b_p":  ("#8A4A2E", 0.60, 0.20, 1.0),
    "container_c_p":  ("#4F565E", 0.60, 0.20, 1.0),
    "dach_p":         ("#2E2F3A", 0.70, 0.10, 1.0),
    # leuchtend
    "natrium_p":      ("#FFB347", 0.40, 0.0, 1.0),
    "lichtfleck_p":   ("#8A6A44", 0.90, 0.0, 1.0),
    "pfuetze_p":      ("#4B5C86", 0.10, 0.45, 1.0),
    "fenster_n_p":    ("#FFB86B", 0.50, 0.0, 1.0),
    "dampf_p":        ("#8F94AC", 0.95, 0.0, 1.0),
    "auto_p":         ("#2D6A6E", 0.35, 0.30, 1.0),
    "van_p":          ("#B8BDC9", 0.45, 0.20, 1.0),
    "ruecklicht_p":   ("#FF3B30", 0.40, 0.0, 1.0),
    "funke_p":        ("#FFF1A8", 0.40, 0.0, 1.0),
    "mast_p":         ("#6E5A44", 0.85, 0.0, 1.0),
    "draht_p":        ("#15161C", 0.60, 0.0, 1.0),
    "led_v_p":        ("#A78BFA", 0.40, 0.0, 1.0),
    "led_c_p":        ("#5EE6F0", 0.40, 0.0, 1.0),
    "led_g_p":        ("#6BE38A", 0.40, 0.0, 1.0),
    "led_w_p":        ("#FFE7B8", 0.40, 0.0, 1.0),
    "schirm_v_p":     ("#8F7BFF", 0.40, 0.0, 1.0),
    "schirm_c_p":     ("#56D8F0", 0.40, 0.0, 1.0),
    "schirm_g_p":     ("#72E39A", 0.40, 0.0, 1.0),
    "vorschau_frei":  ("#3DDC84", 0.9, 0.0, 1.0),
    "vorschau_weg":   ("#FFFFFF", 0.9, 0.0, 1.0),
    # Aliase der Module -> dieselben Materialien
    "ziegel":         "ziegel_f",
    "stahl":          "stahl_f",
    "kappe":          "kappe_f",
    "glas":           "glas_f",
})
modul.leuchten_erweitern({"rack_front_p": 0.45, "violett_p": 1.2, "natrium_p": 2.4, "lichtfleck_p": 0.5, "fenster_n_p": 1.0,
                          "ruecklicht_p": 1.6, "dampf_p": 0.16, "funke_p": 3.2, "led_v_p": 2.4, "led_c_p": 2.4, "led_g_p": 2.0, "led_w_p": 2.0,
                          "schirm_v_p": 1.3, "schirm_c_p": 1.3, "schirm_g_p": 1.3})

# ==============================================================================
# BUCHFUEHRUNG
# ==============================================================================

MOEBEL = []
MOEBEL_BUDGET = 600
ZONEN_BUDGET = 8000
UMGEBUNG_BUDGET = 12000
WEG_FREI_HOEHE = 1.9
ERGEBNIS = []


def setzen(name, teile, x=0.0, z=0.0, dreh=0.0, y=0.0):
    teile = [t for t in teile if t is not None]
    transformieren(teile, x=x, z=z, y=y, dreh_grad=dreh)
    MOEBEL.append((name, teile))
    return teile


def _auswerten(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    welt = [obj.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return n, welt


def moebel_bericht(budget=MOEBEL_BUDGET):
    zu_viel = 0
    groesstes = 0
    for name, teile in MOEBEL:
        n = sum(_auswerten(t)[0] for t in teile)
        groesstes = max(groesstes, n)
        if n > budget:
            zu_viel += 1
            print("    %-28s %5d  <-- UEBER BUDGET" % (name, n))
    print("    %d Moebel, groesstes %d Dreiecke" % (len(MOEBEL), groesstes))
    return zu_viel


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


# ==============================================================================
# ZONEN (worlds.json, Eintrag produkt). frei: (x, z, breite, tiefe, text, S|W) lokal
# ==============================================================================

def _s(x, z, text):
    return (x, z, 2.2, 2.2, "Station " + text, "S")


def _w(x, z, b, t, text):
    return (x, z, b, t, text, "W")


ZONEN = {
    "halle": {
        "breite": 9.0, "tiefe": 7.0, "welt": (0.0, 4.0), "boden": "hallenboden",
        "waende": {"hinten": ("halb", {0.0: "tuer"}), "links": ("halb", {}),
                   "rechts": ("halb", {}), "vorn": ("sockel", {})},
        "frei": [_s(-2.4, -2.35, "intake"), _s(2.2, -2.35, "processing"), _s(0.0, 0.7, "buffer"),
                 _w(0.0, -3.0, 1.2, 1.0, "Tuer hinten"), _w(-0.05, -2.3, 1.1, 2.4, "Laufweg zur Mitte")],
        "ortho": 12.0,
    },
    "kabeltrasse": {
        "breite": 25.0, "tiefe": 4.0, "welt": (0.0, -1.5), "boden": "gitterrost",
        "waende": {"hinten": ("halb", {-8.0: "tuer", 0.0: "tuer", 8.0: "tuer"}),
                   "vorn": ("halb", {-8.0: "tuer", 0.0: "tuer", 8.0: "tuer"}),
                   "links": ("voll", {}), "rechts": ("sockel", {-0.5: "tuer"})},
        "frei": [_s(4.0, -0.8, "transport"), _w(0.0, 0.9, 16.8, 0.8, "Laufweg z -0,6"),
                 _w(-8.0, 0.0, 1.2, 4.0, "Quergang -8"), _w(0.0, 0.0, 1.2, 4.0, "Quergang 0"),
                 _w(8.0, 0.0, 1.2, 4.0, "Quergang 8"), _w(11.0, -0.5, 3.0, 1.2, "Tuer rechts"),
                 _w(-6.75, 0.4, 3.0, 1.3, "Weg zum Wartepunkt"), _w(-5.5, -0.1, 1.0, 1.0, "Wartepunkt")],
        "ortho": 18.0,
    },
    "trafo": {
        "breite": 8.0, "tiefe": 6.0, "welt": (-8.5, -6.5), "boden": "beton",
        "waende": {"hinten": ("voll", {-1.5: "fenster", 1.5: "fenster"}), "links": ("voll", {-0.5: "fenster"}),
                   "rechts": ("halb", {}), "vorn": ("halb", {0.5: "tuer"})},
        "frei": [_w(0.5, 2.4, 1.2, 1.2, "Tuer vorn"), _w(0.25, 1.4, 1.4, 2.4, "Laufweg"),
                 _w(0.0, 0.5, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
    "kontrollraum": {
        "breite": 9.0, "tiefe": 6.0, "welt": (0.0, -6.5), "boden": "teppich",
        "waende": {"hinten": ("voll", {0.0: "fenster"}), "links": ("halb", {}),
                   "rechts": ("halb", {}), "vorn": ("halb", {0.0: "tuer"})},
        "frei": [_s(0.8, -0.1, "special"), _w(0.0, 2.4, 1.2, 1.2, "Tuer vorn"),
                 _w(0.0, 1.5, 1.0, 1.6, "Laufweg")],
        "ortho": 10.5,
    },
    "solardach": {
        "breite": 8.0, "tiefe": 6.0, "welt": (8.5, -6.5), "boden": "deck",
        "waende": {"hinten": ("gelaender", {}), "rechts": ("gelaender", {}),
                   "links": ("halb", {}), "vorn": ("halb", {-0.5: "tuer"})},
        "frei": [_w(-0.5, 2.4, 1.2, 1.2, "Tuer vorn"), _w(-0.25, 1.4, 1.4, 2.4, "Laufweg"),
                 _w(0.0, 0.3, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
    "rackhalle_2": {
        "breite": 8.0, "tiefe": 7.0, "welt": (-8.5, 4.0), "boden": "hallenboden",
        "waende": {"hinten": ("halb", {0.5: "tuer"}), "links": ("voll", {0.0: "fenster"}),
                   "rechts": ("halb", {}), "vorn": ("sockel", {})},
        "frei": [_w(0.5, -2.9, 1.2, 1.2, "Tuer hinten"), _w(0.25, -1.9, 1.4, 2.8, "Laufweg"),
                 _w(0.0, -0.5, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.5,
    },
    "selins_labor": {
        "breite": 8.0, "tiefe": 7.0, "welt": (8.5, 4.0), "boden": "fliese",
        "waende": {"hinten": ("halb", {-0.5: "tuer"}), "links": ("halb", {}),
                   "rechts": ("sockel", {}), "vorn": ("sockel", {})},
        "frei": [_w(-0.5, -2.9, 1.2, 1.2, "Tuer hinten"), _w(-0.5, -1.6, 1.0, 2.4, "Laufweg"),
                 _w(-0.2, 0.0, 1.3, 1.4, "Wartepunkt")],
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
            if typ == "gelaender":
                name = "gelaender"
            elif art == "tuer":
                name = "wand_sockel_tuer" if typ == "sockel" else "wand_halb_tuer"
            elif art == "fenster":
                name = "wand_voll_fenster"
            else:
                name = "wand_" + typ
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
# GRUNDFORMEN UND MOEBEL
# ==============================================================================

def _um_punkt_kippen(o, mitte_godot, achse, grad):
    c = G(*mitte_godot)
    o.matrix_world = (Matrix.Translation(c) @ Matrix.Rotation(math.radians(grad), 4, achse)
                      @ Matrix.Translation(-c) @ o.matrix_world)


def stab(name, a, b, dicke, mat):
    pa, pb = G(*a), G(*b)
    richtung = pb - pa
    obj = kasten(name, (dicke, richtung.length, dicke), (0, 0, 0), mat)
    dreh = richtung.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    obj.matrix_world = Matrix.Translation((pa + pb) / 2.0) @ dreh
    return obj


def flach(name, b, t, x, z, mat, y=0.004):
    return kasten(name, (b, 0.004, t), (x, y, z), mat, unten=False)


def karton(b=0.4, h=0.3, t=0.4, mat="karton_p", x=0.0, y=0.0, z=0.0):
    return [kasten("karton", (b, h, t), (x, y + h / 2, z), mat, rund=0.006, segmente=1),
            kasten("klebe", (0.06, 0.004, t + 0.004), (x, y + h + 0.001, z), "hellgrau_p")]


def palette(b=1.2, t=0.8):
    H = 0.144
    teile = [kasten("pal_deck", (b, 0.022, t), (0, H - 0.011, 0), "palette_p")]
    for s in (-1, 0, 1):
        teile.append(kasten("pal_kufe", (b, H - 0.022, 0.1), (0, (H - 0.022) / 2, s * (t / 2 - 0.05)),
                            "holz_d_p", unten=False))
    return teile


def pflanze(groesse=1.0, topf="topf_p", stil="busch"):
    """Farm kennt kein Gruen: an der Stelle der Pflanze steht ein Fass
    (stil "palme": Gasflaschen-Paar). Name bleibt, damit die Zonen unveraendert sind."""
    s = groesse
    if stil == "busch":
        return [zylinder("fass", 0.2 * s, 0.62 * s, (0, 0, 0), "dunkel_p", seiten=10),
                zylinder("band", 0.205 * s, 0.07 * s, (0, 0.3 * s, 0), "gelb_p", seiten=10),
                zylinder("deckel", 0.17 * s, 0.02 * s, (0, 0.62 * s, 0), "grau_p", seiten=10)]
    teile = []
    for i, dx in enumerate((-0.11, 0.11)):
        teile.append(zylinder("flasche", 0.1 * s, 1.0 * s, (dx * s, 0, 0), "rot_p" if i == 0 else "alu_p", seiten=8,
                              radius_oben=0.095 * s))
        teile.append(kugel("kuppe", 0.1 * s, (dx * s, 1.0 * s, 0), "rot_p" if i == 0 else "alu_p", stauchung=0.6,
                           ringe=3, seiten=8))
    return teile


def rack(h=2.0, b=0.6, t=0.9, led="led_v_p", led2="led_c_p", seed=0):
    """Serverschrank, Front +z: dunkler Korpus, Tuer mit LED-Reihen."""
    rng = random.Random(seed)
    teile = [kasten("rack", (b, h, t), (0, h / 2, 0), "rack_p", rund=0.012, segmente=1)]
    teile.append(kasten("front", (b - 0.06, h - 0.12, 0.012), (0, h / 2, t / 2 + 0.004), "rack_front_p"))
    y = 0.3
    while y < h - 0.2:
        lang = rng.choice((0.12, 0.2, 0.28, 0.36))
        wahl = rng.random()
        teile.append(kasten("led", (lang, 0.045, 0.012), (-b / 2 + 0.06 + lang / 2, y, t / 2 + 0.014),
                            led if wahl < 0.5 else (led2 if wahl < 0.75 else "led_g_p")))
        y += 0.26
    teile.append(kasten("licht_oben", (b - 0.04, 0.03, 0.01), (0, h - 0.04, t / 2 + 0.006), led))
    teile.append(kasten("griff", (0.02, 0.3, 0.03), (b / 2 - 0.06, h * 0.55, t / 2 + 0.02), "alu_p"))
    return teile


def rig_offen(led="led_v_p"):
    """Offener Aluminiumrahmen mit sechs Rechenkarten, 0,7 x 0,6 x 0,4."""
    b, h, t = 0.7, 0.6, 0.4
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("holm", (0.03, h, 0.03), (sx * b / 2, h / 2, sz * t / 2), "alu_p"))
    teile.append(kasten("rahmen", (b + 0.03, 0.025, t + 0.03), (0, h - 0.0125, 0), "alu_p"))
    for i in range(6):
        x = -b / 2 + 0.08 + i * 0.108
        teile.append(kasten("karte", (0.04, 0.2, 0.3), (x, h - 0.14, 0), "dunkel_p"))
        teile.append(kasten("karte_licht", (0.042, 0.02, 0.28), (x, h - 0.03, 0), led))
    teile.append(kasten("board", (b - 0.06, 0.03, t - 0.06), (0, 0.06, 0), "violett_d_p"))
    teile.append(kasten("netzteil", (0.2, 0.12, 0.2), (b / 2 - 0.15, 0.14, 0), "dunkel_p"))
    return teile


def kabeltrommel(kabel="violett_p"):
    r = 0.3
    teile = []
    for s in (-1, 1):
        teile.append(liegender_zylinder("scheibe", r, 0.03, (0, r, s * 0.18), "z", "holz_p", seiten=12))
    teile.append(liegender_zylinder("wicklung", r * 0.72, 0.33, (0, r, 0), "z", kabel, seiten=12))
    return teile


def schaltschrank(b=0.8, h=1.9, t=0.45, farbe="schrank_p"):
    teile = [kasten("korpus", (b, h, t), (0, h / 2, 0), farbe, rund=0.015, segmente=1),
             kasten("sockel", (b - 0.02, 0.1, t - 0.02), (0, 0.05, 0), "dunkel_p"),
             kasten("fuge", (0.008, h - 0.2, 0.004), (0, h / 2 + 0.05, t / 2 + 0.002), "grau_p")]
    for s in (-1, 1):
        teile.append(kasten("griff", (0.03, 0.14, 0.03), (s * 0.06, h * 0.55, t / 2 + 0.015), "dunkel_p"))
    teile.append(kasten("warnschild", (0.16, 0.16, 0.004), (-b / 4, h - 0.35, t / 2 + 0.003), "gelb_p"))
    teile.append(kasten("blitz", (0.03, 0.1, 0.004), (-b / 4, h - 0.35, t / 2 + 0.006), "dunkel_p"))
    teile.append(kasten("anzeige", (0.14, 0.06, 0.004), (b / 4, h - 0.32, t / 2 + 0.003), "led_g_p"))
    teile.append(zylinder("beacon", 0.07, 0.1, (0, h, 0), "natrium_p", seiten=8))
    teile.append(kasten("lueftung", (b - 0.2, 0.12, 0.004), (0, 0.3, t / 2 + 0.003), "grau_p"))
    return teile


def trafo_gross():
    """Transformator: Kessel mit Kuehlrippen, drei Durchfuehrungen oben."""
    b, h, t = 1.5, 1.4, 1.0
    teile = [kasten("kessel", (b, h, t), (0, 0.15 + h / 2, 0), "trafo_p", rund=0.03, segmente=1),
             kasten("fuss", (b + 0.1, 0.15, t + 0.1), (0, 0.075, 0), "dunkel_p", unten=False),
             kasten("deckel", (b + 0.06, 0.06, t + 0.06), (0, 0.15 + h + 0.03, 0), "trafo_p")]
    for i in range(7):
        x = -b / 2 + 0.12 + i * (b - 0.24) / 6
        for s in (-1, 1):
            teile.append(kasten("rippe", (0.04, h - 0.25, 0.16), (x, 0.15 + h / 2, s * (t / 2 + 0.08)), "trafo_p"))
    for i in (-1, 0, 1):
        x = i * 0.42
        teile.append(zylinder("isolator", 0.06, 0.38, (x, 0.15 + h + 0.06, 0.1), "isolator_p", seiten=8,
                              radius_oben=0.035))
        for k in range(2):
            teile.append(zylinder("schirm", 0.09, 0.02, (x, 0.15 + h + 0.14 + k * 0.12, 0.1), "isolator_p",
                                  seiten=8))
        teile.append(kugel("klemme", 0.04, (x, 0.15 + h + 0.47, 0.1), "kupfer_p", ringe=3, seiten=6))
    teile.append(kasten("warn", (0.3, 0.26, 0.006), (0.35, 0.8, t / 2 + 0.163), "gelb_p"))
    teile.append(kasten("warn_blitz", (0.05, 0.16, 0.006), (0.35, 0.8, t / 2 + 0.167), "dunkel_p"))
    return teile


def zaunfeld(laenge=2.0, h=1.8, mat="alu_p"):
    """Stabgitterzaun entlang x, Pfosten am linken Ende."""
    teile = [kasten("zpfosten", (0.06, h, 0.06), (-laenge / 2, h / 2, 0), "stahl")]
    for y in (0.12, h - 0.06):
        teile.append(kasten("zholm", (laenge, 0.04, 0.03), (0, y, 0), mat))
    n = max(3, int(laenge / 0.2))
    for i in range(1, n):
        x = -laenge / 2 + i * laenge / n
        teile.append(kasten("zstab", (0.018, h - 0.14, 0.018), (x, 0.07 + (h - 0.14) / 2, 0), mat))
    return teile


def warnschild_steh():
    y0 = 1.15
    return [zylinder("fuss", 0.18, 0.04, (0, 0, 0), "gummi_p", seiten=8),
            kasten("stiel", (0.04, y0, 0.04), (0, y0 / 2, -0.03), "alu_p"),
            kasten("schild", (0.4, 0.4, 0.02), (0, y0, 0.0), "gelb_p", rund=0.01, segmente=1),
            kasten("blitz", (0.06, 0.24, 0.006), (0, y0, 0.012), "dunkel_p")]


def chiller(b=1.4, h=1.2, t=0.8):
    """Kuehlaggregat: Kasten mit zwei grossen Luefterkreisen oben."""
    teile = [kasten("korpus", (b, h, t), (0, h / 2, 0), "hellgrau_p", rund=0.03, segmente=1),
             kasten("band", (b + 0.004, 0.08, t + 0.004), (0, h - 0.2, 0), "violett_p")]
    for s in (-1, 1):
        x = s * b / 4
        teile.append(zylinder("luefterring", 0.3, 0.05, (x, h, 0), "dunkel_p", seiten=14))
        teile.append(zylinder("nabe", 0.06, 0.07, (x, h, 0), "alu_p", seiten=8))
        for k in range(3):
            fl = kasten("fluegel", (0.5, 0.012, 0.08), (0, h + 0.055, 0), "grau_p")
            fl.matrix_world = Matrix.Translation(G(x, 0, 0)) @ Matrix.Rotation(math.radians(k * 60 + s * 15), 4, "Z") @ fl.matrix_world
            teile.append(fl)
        teile.append(kasten("gitter", (b / 2 - 0.1, 0.5, 0.004), (x, h * 0.45, t / 2 + 0.002), "grau_p"))
    teile.append(kasten("anzeige", (0.18, 0.1, 0.006), (b / 2 - 0.2, h - 0.35, t / 2 + 0.003), "schirm_c_p"))
    return teile


def kabelpritsche(laenge, hoehe=2.05, t=0.45, pfosten=True):
    """Kabelleiter auf Stuetzen entlang x, Kabelbuendel Violett/Dunkel/Cyan."""
    teile = []
    if pfosten:
        for s in (-1, 1):
            x = s * (laenge / 2 - 0.1)
            teile.append(kasten("stuetze", (0.08, hoehe, 0.08), (x, hoehe / 2, -t / 2 + 0.04), "stahl"))
            teile.append(kasten("ausleger", (0.06, 0.06, t), (x, hoehe - 0.06, 0), "stahl"))
            teile.append(kasten("fussplatte", (0.2, 0.02, 0.2), (x, 0.01, -t / 2 + 0.04), "grau_p"))
    for s in (-1, 1):
        teile.append(kasten("wange", (laenge, 0.07, 0.025), (0, hoehe + 0.005, s * (t / 2 - 0.015)), "alu_p"))
    n = int(laenge / 0.5)
    for i in range(n):
        x = -laenge / 2 + (i + 0.5) * laenge / n
        teile.append(kasten("sprosse", (0.03, 0.02, t - 0.04), (x, hoehe - 0.02, 0), "alu_p"))
    for dz, mat, r in ((-0.12, "violett_p", 0.045), (0.0, "dunkel_p", 0.05), (0.12, "cyan_p", 0.04)):
        teile.append(liegender_zylinder("buendel", r, laenge, (0, hoehe + r - 0.01, dz), "x", mat, seiten=6))
    teile.append(kasten("licht", (laenge, 0.015, 0.02), (0, hoehe - 0.035, t / 2 - 0.015), "led_v_p"))
    return teile


def solarpaneel(b=1.0, t=1.5, neigung=22.0):
    """Paneel auf Aufstaenderung, neigt sich nach +z (zur Kamera)."""
    teile = []
    tp = t * math.cos(math.radians(neigung))
    dy = t * math.sin(math.radians(neigung))
    vorn = 0.22
    hinten = vorn + dy
    for s in (-1, 1):
        x = s * (b / 2 - 0.08)
        teile.append(kasten("stuetze_h", (0.04, hinten, 0.04), (x, hinten / 2, -tp / 2 + 0.05), "alu_p"))
        teile.append(kasten("stuetze_v", (0.04, vorn, 0.04), (x, vorn / 2, tp / 2 - 0.05), "alu_p"))
        teile.append(kasten("ballast", (0.12, 0.06, tp), (x, 0.03, 0), "grau_p"))
    mitte_y = (hinten + vorn) / 2 + 0.03
    platte = [kasten("paneel", (b - 0.02, 0.03, t), (0, mitte_y, 0), "solar_p"),
              kasten("rahmen", (b, 0.02, t + 0.02), (0, mitte_y - 0.02, 0), "alu_p")]
    for k in range(1, 4):
        platte.append(kasten("zelllinie", (b - 0.04, 0.004, 0.012), (0, mitte_y + 0.017, -t / 2 + k * t / 4),
                             "solar_linie_p"))
    platte.append(kasten("zelllinie_l", (0.012, 0.004, t - 0.04), (0, mitte_y + 0.017, 0), "solar_linie_p"))
    for o in platte:
        _um_punkt_kippen(o, (0, mitte_y, 0), "X", neigung)
    return teile + platte


def monitor(x=0.0, z=0.0, farbe="schirm_v_p", breite=0.55, y=0.75):
    return [kasten("mfuss", (0.2, 0.02, 0.14), (x, y + 0.01, z), "dunkel_p"),
            kasten("mhals", (0.04, 0.22, 0.03), (x, y + 0.12, z - 0.04), "dunkel_p"),
            kasten("mschirm", (breite, 0.33, 0.03), (x, y + 0.36, z - 0.02), "bildschirm_p", rund=0.008, segmente=1),
            kasten("manzeige", (breite - 0.05, 0.28, 0.004), (x, y + 0.36, z - 0.003), farbe)]


def schreibtisch(farben=("schirm_v_p",), b=1.4):
    teile = [kasten("platte", (b, 0.035, 0.7), (0, 0.735, 0), "weiss_p", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("wange", (0.05, 0.72, 0.62), (sx * (b / 2 - 0.06), 0.36, 0), "dunkel_p"))
    n = len(farben)
    for i, f in enumerate(farben):
        teile += monitor(x=(i - (n - 1) / 2) * 0.58, z=-0.12, farbe=f)
    teile.append(kasten("tastatur", (0.42, 0.02, 0.14), (0, 0.762, 0.14), "dunkel_p"))
    teile.append(kasten("tastatur_licht", (0.4, 0.004, 0.12), (0, 0.773, 0.14), "led_v_p"))
    teile.append(zylinder("tasse", 0.04, 0.09, (-b / 2 + 0.15, 0.752, 0.12), "violett_p", seiten=8))
    return teile


def buerostuhl(stoff="stoff_p"):
    """Sitz blickt nach -z (zum Tisch); Lehne bei +z."""
    teile = [kasten("sitz", (0.48, 0.08, 0.46), (0, 0.48, 0), stoff, rund=0.03, segmente=1),
             kasten("lehne", (0.44, 0.55, 0.07), (0, 0.87, 0.22), stoff, rund=0.03, segmente=1),
             kasten("traeger", (0.06, 0.3, 0.04), (0, 0.55, 0.22), "dunkel_p"),
             zylinder("saeule", 0.03, 0.36, (0, 0.08, 0), "dunkel_p", seiten=6)]
    for i in range(5):
        a = math.radians(90 + i * 72)
        teile.append(stab("fuss", (0, 0.08, 0), (math.cos(a) * 0.3, 0.04, math.sin(a) * 0.3), 0.035, "dunkel_p"))
    return teile


def sofa(stoff="stoff_p", b=2.0):
    teile = [kasten("basis", (b, 0.24, 0.85), (0, 0.18, 0), stoff, rund=0.04, segmente=1),
             kasten("lehne", (b, 0.45, 0.22), (0, 0.55, -0.32), stoff, rund=0.06, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("arm", (0.2, 0.34, 0.85), (sx * (b / 2 - 0.1), 0.5, 0), stoff, rund=0.05, segmente=1))
        teile.append(kasten("kissen", ((b - 0.4) / 2 - 0.02, 0.14, 0.62), (sx * (b - 0.4) / 4, 0.37, 0.08),
                            stoff, rund=0.05, segmente=1))
    teile.append(kugel("deko1", 0.16, (-0.55, 0.62, -0.12), "stoff_senf_p", stauchung=0.7, ringe=4, seiten=7))
    teile.append(kugel("deko2", 0.15, (0.6, 0.62, -0.12), "stoff_koralle_p", stauchung=0.7, ringe=4, seiten=7))
    return teile


def couchtisch():
    teile = [kasten("platte", (1.0, 0.04, 0.55), (0, 0.42, 0), "holz_p", rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.04, 0.4, 0.04), (sx * 0.44, 0.2, sz * 0.22), "dunkel_p"))
    teile.append(kasten("tablet", (0.24, 0.015, 0.17), (-0.2, 0.448, 0.02), "bildschirm_p"))
    teile.append(zylinder("becher", 0.04, 0.09, (0.25, 0.44, -0.05), "weiss_p", seiten=8))
    return teile


def whiteboard():
    teile = [kasten("tafel", (1.5, 0.9, 0.03), (0, 1.3, 0), "weiss_p", rund=0.008, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("bein", (0.04, 1.8, 0.04), (sx * 0.77, 0.9, 0), "alu_p"))
        teile.append(kasten("wbfuss", (0.06, 0.04, 0.5), (sx * 0.77, 0.02, 0), "alu_p"))
    for i, (x, y) in enumerate(((-0.5, 1.5), (-0.1, 1.5), (0.3, 1.55), (-0.3, 1.15), (0.25, 1.15))):
        teile.append(kasten("kaestchen", (0.16, 0.1, 0.004), (x, y, 0.017), "violett_p" if i % 2 else "cyan_p"))
    teile.append(kasten("linie", (0.9, 0.012, 0.004), (-0.1, 1.33, 0.017), "dunkel_p"))
    teile.append(kasten("zettel", (0.1, 0.1, 0.004), (0.6, 1.6, 0.017), "notiz_gelb_p"))
    teile.append(kasten("zettel2", (0.1, 0.1, 0.004), (0.6, 1.45, 0.017), "notiz_rosa_p"))
    return teile


def werkbank(b=2.0, t=0.75):
    teile = [kasten("platte", (b, 0.05, t), (0, 0.9, 0), "holz_p", rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.06, 0.88, 0.06), (sx * (b / 2 - 0.06), 0.44, sz * (t / 2 - 0.06)),
                                "violett_d_p"))
    teile.append(kasten("ablage", (b - 0.1, 0.03, t - 0.1), (0, 0.2, 0), "violett_d_p"))
    teile.append(kasten("schublade", (0.5, 0.18, t - 0.05), (b / 2 - 0.35, 0.78, 0), "schrank_p"))
    teile.append(kasten("sgriff", (0.2, 0.02, 0.02), (b / 2 - 0.35, 0.78, t / 2), "dunkel_p"))
    teile += karton(0.4, 0.25, 0.35, "karton_p", x=-0.5, y=0.215, z=0)
    return teile


def oszilloskop(x=0.0, y=0.925, z=0.0):
    return [kasten("oszi", (0.4, 0.24, 0.3), (x, y + 0.12, z), "hellgrau_p", rund=0.015, segmente=1),
            kasten("oszi_schirm", (0.2, 0.14, 0.004), (x - 0.06, y + 0.13, z + 0.152), "bildschirm_p"),
            kasten("oszi_kurve", (0.16, 0.012, 0.004), (x - 0.06, y + 0.14, z + 0.155), "led_g_p"),
            kasten("oszi_kurve2", (0.03, 0.05, 0.004), (x - 0.02, y + 0.12, z + 0.155), "led_g_p"),
            kasten("oszi_knopf", (0.1, 0.12, 0.004), (x + 0.12, y + 0.13, z + 0.152), "grau_p")]


def loetstation(x=0.0, y=0.925, z=0.0):
    return [kasten("loet", (0.2, 0.1, 0.16), (x, y + 0.05, z), "dunkel_p", rund=0.01, segmente=1),
            kasten("loet_anz", (0.08, 0.04, 0.004), (x, y + 0.06, z + 0.082), "led_c_p"),
            zylinder("halter", 0.04, 0.12, (x + 0.18, y, z), "grau_p", seiten=6),
            stab("kolben", (x + 0.18, y + 0.12, z), (x + 0.3, y + 0.2, z + 0.05), 0.02, "violett_p")]


def gpu_pruefstand(x=0.0, y=0.925, z=0.0):
    return [kasten("platine", (0.34, 0.02, 0.22), (x, y + 0.01, z), "violett_d_p"),
            kasten("karte", (0.28, 0.05, 0.12), (x, y + 0.045, z), "dunkel_p", rund=0.008, segmente=1),
            kasten("karte_licht", (0.26, 0.006, 0.02), (x, y + 0.073, z + 0.04), "led_v_p")]


def lochwand(b=1.6, h=0.9):
    """Werkzeugwand auf zwei Stuetzen (Vorderseite +z)."""
    teile = [kasten("wand", (b, h, 0.03), (0, 1.0 + h / 2, 0), "hellgrau_p", rund=0.006, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("stuetze", (0.05, 1.0 + h, 0.05), (sx * (b / 2 - 0.03), (1.0 + h) / 2, -0.04), "dunkel_p"))
    for x, y, w, hh, m in ((-0.6, 1.6, 0.04, 0.3, "rot_p"), (-0.45, 1.55, 0.03, 0.35, "violett_p"),
                           (-0.2, 1.7, 0.2, 0.05, "dunkel_p"), (0.0, 1.45, 0.12, 0.12, "gelb_p"),
                           (0.25, 1.6, 0.05, 0.3, "cyan_p"), (0.5, 1.3, 0.3, 0.2, "grau_p"),
                           (-0.4, 1.2, 0.35, 0.15, "orange_p")):
        teile.append(kasten("werkzeug", (w, hh, 0.03), (x, y, 0.03), m))
    return teile


def teileregal(b=1.0, h=1.6, t=0.4):
    teile = []
    for sx in (-1, 1):
        teile.append(kasten("seite", (0.03, h, t), (sx * (b / 2 - 0.015), h / 2, 0), "alu_p"))
    farben = ("violett_p", "cyan_p", "gelb_p", "orange_p")
    for k, y in enumerate((0.05, 0.45, 0.85, 1.25, h - 0.02)):
        teile.append(kasten("boden", (b - 0.06, 0.025, t), (0, y, 0), "alu_p"))
        if y < h - 0.1:
            for i in range(3):
                teile.append(kasten("kiste", (0.26, 0.18, t - 0.06), (-b / 2 + 0.2 + i * 0.3, y + 0.1, 0.01),
                                    farben[(i + k) % 4]))
    return teile


def drucker3d():
    return [kasten("gehaeuse", (0.5, 0.55, 0.5), (0, 0.275, 0), "dunkel_p", rund=0.015, segmente=1),
            kasten("fenster", (0.4, 0.38, 0.004), (0, 0.32, 0.252), "glas"),
            kasten("objekt", (0.1, 0.12, 0.1), (0, 0.18, 0.1), "violett_p"),
            kasten("anzeige", (0.12, 0.05, 0.004), (0.14, 0.07, 0.252), "schirm_c_p")]


def hocker():
    return [zylinder("sitz", 0.18, 0.05, (0, 0.62, 0), "stoff_p", seiten=10),
            zylinder("saeule", 0.03, 0.6, (0, 0.02, 0), "dunkel_p", seiten=6),
            zylinder("fuss", 0.2, 0.03, (0, 0, 0), "dunkel_p", seiten=10)]


def kaffeezeile(b=1.4):
    teile = [kasten("korpus", (b, 0.85, 0.55), (0, 0.425, 0), "weiss_p", rund=0.015, segmente=1),
             kasten("platte", (b + 0.02, 0.04, 0.6), (0, 0.87, 0.01), "holz_p")]
    for i in range(2):
        teile.append(kasten("front", (b / 2 - 0.04, 0.75, 0.01), (-b / 4 + i * b / 2, 0.42, 0.28),
                            "violett_p" if i else "weiss_p"))
    teile.append(kasten("maschine", (0.3, 0.4, 0.34), (0.35, 1.09, -0.05), "dunkel_p", rund=0.02, segmente=1))
    teile.append(kasten("m_licht", (0.12, 0.04, 0.004), (0.35, 1.2, 0.123), "led_c_p"))
    teile.append(zylinder("tasse", 0.04, 0.08, (0.35, 0.89, 0.06), "weiss_p", seiten=8))
    teile.append(zylinder("dose", 0.08, 0.2, (-0.3, 0.89, -0.05), "cyan_p", seiten=8))
    return teile


def leitkegel():
    return [kasten("kfuss", (0.3, 0.03, 0.3), (0, 0.015, 0), "orange_p"),
            zylinder("kegel", 0.12, 0.5, (0, 0.03, 0), "orange_p", seiten=8, radius_oben=0.02),
            zylinder("kband", 0.089, 0.08, (0, 0.21, 0), "weiss_p", seiten=8, radius_oben=0.075)]


def feuerloescher():
    return [kasten("platte", (0.3, 0.03, 0.26), (0, 0.015, 0), "rot_p"),
            zylinder("flasche", 0.08, 0.5, (0, 0.03, 0), "rot_p", seiten=10),
            kugel("kopf", 0.08, (0, 0.53, 0), "rot_p", stauchung=0.7, ringe=4, seiten=8),
            kasten("ventil", (0.05, 0.08, 0.05), (0, 0.62, 0), "dunkel_p")]


def batterieschrank(b=1.2, h=1.8, t=0.6):
    teile = [kasten("korpus", (b, h, t), (0, h / 2, 0), "weiss_p", rund=0.02, segmente=1)]
    for i in range(4):
        y = 0.3 + i * 0.38
        teile.append(kasten("modul", (b - 0.12, 0.3, 0.01), (0, y, t / 2 + 0.004), "hellgrau_p"))
        for k in range(3 - (i % 2)):
            teile.append(kasten("ladung", (0.12, 0.03, 0.006), (-b / 2 + 0.2 + k * 0.15, y + 0.08, t / 2 + 0.01),
                                "led_g_p"))
    teile.append(kasten("band", (b + 0.004, 0.05, t + 0.004), (0, h - 0.12, 0), "violett_p"))
    return teile


def luefterwand(b=1.2, h=1.2):
    """Wandluefter-Gruppe auf Gestell, Vorderseite +z."""
    teile = [kasten("rahmen", (b, h, 0.25), (0, 0.2 + h / 2, 0), "hellgrau_p", rund=0.02, segmente=1)]
    for i in range(2):
        for k in range(2):
            x, y = -b / 4 + i * b / 2, 0.2 + h / 4 + k * h / 2
            ring = zylinder("ring", 0.24, 0.02, (x, y - 0.01, 0.0), "dunkel_p", seiten=12)
            _um_punkt_kippen(ring, (x, y, 0.0), "X", 90)
            ring.matrix_world = Matrix.Translation(G(0, 0, 0.13)) @ ring.matrix_world
            teile.append(ring)
            nabe = zylinder("nabe", 0.05, 0.03, (x, y - 0.015, 0.0), "alu_p", seiten=8)
            _um_punkt_kippen(nabe, (x, y, 0.0), "X", 90)
            nabe.matrix_world = Matrix.Translation(G(0, 0, 0.14)) @ nabe.matrix_world
            teile.append(nabe)
    for s in (-1, 1):
        teile.append(kasten("fuss", (0.06, 0.2, 0.3), (s * (b / 2 - 0.05), 0.1, 0), "dunkel_p"))
    teile.append(kasten("licht", (b - 0.1, 0.02, 0.01), (0, 0.2 + h - 0.05, 0.13), "led_c_p"))
    return teile


def kabelbruecke(laenge, mat="dunkel_p"):
    """Flache Kabelbruecke am Boden entlang x (<= 2 cm hoch)."""
    return [kasten("bruecke", (laenge, 0.018, 0.22), (0, 0.009, 0), mat, unten=False),
            kasten("bruecke_licht", (laenge, 0.002, 0.03), (0, 0.019, 0), "led_v_p", unten=False)]


def bodenrahmen(x, z, b, t, mat="violett_p", d=0.05):
    return [flach("mark", b, d, x, z - t / 2 + d / 2, mat), flach("mark", b, d, x, z + t / 2 - d / 2, mat),
            flach("mark", d, t - 2 * d, x - b / 2 + d / 2, z, mat),
            flach("mark", d, t - 2 * d, x + b / 2 - d / 2, z, mat)]


# ==============================================================================
# ZONEN
# ==============================================================================

def einrichtung_halle():
    """Startzone: die leere Halle, in der Selin die ersten Rechner aufstellt.
    Hohe Dinge an den Seitenwaenden, vorn nur Niedriges."""
    for i, z in enumerate((-0.7, -0.08, 0.54)):
        setzen("rack_%d" % i, rack(seed=10 + i, led="led_v_p" if i != 1 else "led_c_p"), x=-3.95, z=z, dreh=90.0)
    setzen("schaltschrank", schaltschrank(), x=-4.17, z=-2.4, dreh=90.0)
    setzen("batterie", batterieschrank(), x=4.1, z=-2.4, dreh=-90.0)
    setzen("kabeltrommel", kabeltrommel(), x=-3.7, z=1.6)
    setzen("palette_kartons", palette() + karton(0.5, 0.35, 0.35, "karton_h_p", x=-0.28, y=0.144, z=-0.18)
           + karton(0.5, 0.35, 0.35, "karton_p", x=0.28, y=0.144, z=-0.18)
           + karton(0.5, 0.3, 0.35, "karton_p", x=-0.28, y=0.144, z=0.2)
           + karton(0.45, 0.3, 0.3, "karton_h_p", x=-0.2, y=0.494, z=-0.15), x=-3.6, z=2.8, dreh=90.0)
    setzen("kabel_zur_mitte", kabelbruecke(2.3), x=-2.35, z=0.3)
    setzen("kabel_quer", kabelbruecke(1.4), x=2.6, z=0.3)
    setzen("teileregal", teileregal(), x=4.15, z=-0.3, dreh=-90.0)
    tisch = [kasten("regal_platte", (0.8, 0.04, 0.5), (0, 0.5, 0), "alu_p")]
    for sx in (-1, 1):
        for sz in (-1, 1):
            tisch.append(kasten("regal_bein", (0.04, 0.48, 0.04), (sx * 0.36, 0.24, sz * 0.21), "dunkel_p"))
    tisch += transformieren(rig_offen(), y=0.52)
    setzen("rig_ablage", tisch, x=4.05, z=1.05, dreh=-90.0)
    setzen("werkbank", werkbank(1.6, 0.7), x=2.55, z=2.95)
    setzen("pflanze_palme", pflanze(1.1, stil="palme"), x=4.0, z=3.0)
    setzen("pflanze_busch", pflanze(0.8), x=-2.6, z=3.05)
    setzen("feuerloescher", feuerloescher(), x=-1.0, z=-3.2)
    setzen("warnschild", warnschild_steh(), x=0.85, z=-3.1, dreh=-20.0)
    setzen("kegel_1", leitkegel(), x=-1.7, z=2.9)
    setzen("kegel_2", leitkegel(), x=-1.25, z=3.15)


def einrichtung_kabeltrasse():
    """Langer Gang ueber Gitterrost: Kabelleiter hinten (ueber Kopfhoehe),
    Kuehlaggregate vorn, dazwischen der Laufweg."""
    for name, x0, x1 in (("links", -12.3, 2.8), ("rechts", 5.2, 12.3)):
        setzen("haengt_pritsche_" + name, kabelpritsche(x1 - x0, hoehe=2.05, pfosten=False),
               x=(x0 + x1) / 2, z=-1.55)
        setzen("haengt_rohr_" + name, [liegender_zylinder("rohr_c", 0.07, x1 - x0, (0, 2.32, 0), "x", "cyan_p", seiten=8),
                                        liegender_zylinder("rohr_v", 0.07, x1 - x0, (0, 2.32, 0.18), "x", "violett_p",
                                                           seiten=8)],
               x=(x0 + x1) / 2, z=-1.6)
    for i, x in enumerate((-11.9, -5.0, -2.2, 2.2, 6.2, 11.9)):
        setzen("stuetze_%d" % i, [kasten("stuetze", (0.08, 2.4, 0.08), (0, 1.2, 0), "stahl"),
                                  kasten("fussplatte", (0.2, 0.02, 0.2), (0, 0.01, 0), "grau_p")],
               x=x, z=-1.78)
    for i, x in enumerate((-10.9, -4.6, 4.2, 10.8)):
        setzen("chiller_%d" % i, chiller(1.4, 1.3, 0.55), x=x, z=1.6)
    setzen("kabeltrommel", kabeltrommel("cyan_p"), x=-10.0, z=-1.5)
    setzen("schaltschrank_l", schaltschrank(0.8, 1.7, 0.4), x=-6.5, z=-1.68)
    setzen("schaltschrank_r", schaltschrank(0.8, 1.7, 0.4), x=6.3, z=-1.68)
    setzen("luefterwand", luefterwand(), x=10.3, z=-1.75)
    setzen("kegel", leitkegel(), x=-3.4, z=-1.5)
    setzen("feuerloescher", feuerloescher(), x=1.6, z=-1.7)
    setzen("warnschild", warnschild_steh(), x=-1.2, z=-1.65)
    setzen("pflanze", pflanze(0.9), x=-12.1, z=1.6)


def einrichtung_trafo():
    """Trafostation: grosser Transformator hinter Gitter, Schaltschraenke
    hinten, Akkuschraenke rechts."""
    setzen("trafo", trafo_gross(), x=-1.9, z=-1.25)
    setzen("zaun_vorn", zaunfeld(2.5, 1.8), x=-1.95, z=0.05)
    setzen("zaun_seite", zaunfeld(2.6, 1.8), x=-0.7, z=-1.25, dreh=90.0)
    setzen("warnschild", warnschild_steh(), x=-2.6, z=0.45)
    for i, x in enumerate((0.65, 1.5, 2.35)):
        setzen("schaltschrank_%d" % i, schaltschrank(0.8, 1.6, 0.45), x=x, z=-2.65)
    setzen("kabel_trafo", kabelbruecke(2.4), x=0.6, z=-1.9)
    setzen("batterie_1", batterieschrank(), x=3.6, z=-0.55, dreh=-90.0)
    setzen("batterie_2", batterieschrank(), x=3.6, z=0.75, dreh=-90.0)
    setzen("kabeltrommel", kabeltrommel(), x=2.6, z=2.3)
    setzen("palette", palette() + karton(0.5, 0.4, 0.5, "karton_p", x=-0.28, y=0.144)
           + karton(0.45, 0.3, 0.45, "karton_h_p", x=0.3, y=0.144), x=-2.5, z=2.3)
    setzen("kegel_1", leitkegel(), x=-3.5, z=1.4)
    setzen("kegel_2", leitkegel(), x=-3.2, z=1.75)
    setzen("feuerloescher", feuerloescher(), x=-3.6, z=-2.6)


def videowand(b=3.0, h=1.0, farben=("schirm_v_p", "schirm_c_p", "schirm_g_p")):
    teile = [kasten("rahmen", (b, h, 0.05), (0, 1.0 + h / 2, 0.025), "bildschirm_p")]
    n = 3
    for i in range(n):
        for k in range(2):
            x = -b / 2 + (i + 0.5) * b / n
            y = 1.0 + (k + 0.5) * h / 2
            teile.append(kasten("kachel", (b / n - 0.06, h / 2 - 0.06, 0.004), (x, y, 0.052), farben[(i + k) % 3]))
            for j in range(3):
                hh = 0.06 + 0.05 * ((i + j + k) % 3)
                teile.append(kasten("balken", (0.08, hh, 0.004), (x - 0.2 + j * 0.2, y - 0.14 + hh / 2, 0.056),
                                    "weiss_p"))
    return teile


def einrichtung_kontrollraum():
    """Leitstand: Videowand hinten, zwei Pulte, Sofaecke rechts vorn."""
    setzen("wand_videowand", videowand(), x=-2.3, z=-2.9)
    setzen("wand_schirm_rechts", videowand(1.8, 0.8, ("schirm_c_p", "schirm_v_p", "schirm_c_p")), x=2.3, z=-2.9)
    setzen("pult_1", schreibtisch(("schirm_v_p", "schirm_c_p")), x=-3.0, z=-1.6)
    setzen("pult_2", schreibtisch(("schirm_g_p",)), x=-1.45, z=-1.6)
    setzen("stuhl_1", buerostuhl(), x=-3.0, z=-0.95)
    setzen("stuhl_2", buerostuhl("stoff_senf_p"), x=-1.45, z=-0.95)
    setzen("sofa", sofa(), x=3.2, z=1.85, dreh=180.0)
    setzen("couchtisch", couchtisch(), x=3.2, z=0.75)
    setzen("kaffee", kaffeezeile(), x=4.1, z=-1.2, dreh=-90.0)
    setzen("rack", rack(seed=3), x=3.95, z=-2.45, dreh=-90.0)
    setzen("whiteboard", whiteboard(), x=-3.0, z=1.3, dreh=35.0)
    setzen("pflanze_1", pflanze(1.0, stil="palme"), x=-4.0, z=2.5)
    setzen("pflanze_2", pflanze(0.8), x=2.1, z=2.5)
    setzen("teppich", [kasten("teppich", (2.4, 0.012, 1.8), (0, 0.006, 0), "violett_d_p", rund=0.005, segmente=1)],
           x=3.1, z=1.2)


def einrichtung_solardach():
    """Dach mit Solarpaneelen, Wechselrichter und Speicher, freundlich
    mit Pflanzen. Paneele neigen sich zur Kamera."""
    for i, x in enumerate((-3.3, -2.2, -1.1, 0.0, 1.1, 2.2, 3.3)):
        setzen("paneel_hinten_%d" % i, solarpaneel(), x=x, z=-1.9)
    for i, x in enumerate((-3.3, -2.2, 1.2, 2.3, 3.3)):
        setzen("paneel_vorn_%d" % i, solarpaneel(), x=x, z=0.25)
    setzen("wechselrichter", schaltschrank(0.6, 1.0, 0.35), x=-2.9, z=2.5)
    setzen("speicher", batterieschrank(1.2, 1.2, 0.6), x=1.8, z=2.45)
    kabel = kabelbruecke(4.0)
    setzen("kabel_dach", kabel, x=-1.6, z=1.4)
    setzen("pflanze_1", pflanze(1.0), x=3.4, z=2.4)
    setzen("pflanze_2", pflanze(0.8, stil="palme"), x=-3.6, z=1.6)
    setzen("hocker", hocker(), x=2.9, z=1.6)


def einrichtung_rackhalle_2():
    """Zweite Rechnerhalle: zwei Reihen Serverschraenke, Kabelleiter darueber,
    kalter Gang dazwischen."""
    zs = [-2.8 + i * 0.62 for i in range(10)]
    for i, z in enumerate(zs):
        setzen("reihe_a_%d" % i, rack(seed=40 + i, led="led_v_p" if i % 3 else "led_c_p"), x=-2.6, z=z, dreh=90.0)
        setzen("reihe_b_%d" % i, rack(seed=60 + i, led="led_c_p" if i % 3 else "led_v_p"), x=2.4, z=z, dreh=90.0)
    lang = zs[-1] - zs[0] + 0.6
    for name, x in (("a", -2.6), ("b", 2.4)):
        setzen("haengt_leiter_" + name, kabelpritsche(lang, hoehe=2.12, t=0.4, pfosten=False),
               x=x, z=(zs[0] + zs[-1]) / 2, dreh=90.0)
    setzen("gang_markierung", bodenrahmen(-0.1, 0.0, 3.8, 6.2, "violett_p", 0.06))
    setzen("rigs", palette(0.8, 0.6) + transformieren(rig_offen("led_c_p"), y=0.144), x=0.35, z=2.75)
    setzen("kegel", leitkegel(), x=-1.2, z=3.0)
    setzen("pflanze", pflanze(0.9), x=-3.6, z=3.0)
    setzen("feuerloescher", feuerloescher(), x=-1.7, z=-3.15)


def einrichtung_selins_labor():
    """Selins Werkbank: Oszilloskop, Loetstation, Pruefstand, viele Pflanzen."""
    bank = werkbank(2.0, 0.7)
    bank += oszilloskop(x=-0.6, z=-0.05) + loetstation(x=-0.05, z=0.05) + gpu_pruefstand(x=0.62, z=0.05)
    setzen("werkbank", bank, x=2.0, z=-3.0)
    setzen("lochwand", lochwand(), x=2.0, z=-3.33)
    setzen("hocker", hocker(), x=1.8, z=-2.25)
    setzen("teileregal", teileregal(), x=-3.7, z=-2.0, dreh=90.0)
    setzen("drucker_tisch", [kasten("tischchen", (0.7, 0.6, 0.6), (0, 0.3, 0), "weiss_p", rund=0.015, segmente=1)]
           + transformieren(drucker3d(), y=0.6), x=-3.5, z=0.1, dreh=90.0)
    setzen("schreibtisch", schreibtisch(("schirm_v_p", "schirm_g_p")), x=2.2, z=0.9)
    setzen("stuhl", buerostuhl(), x=2.2, z=1.6)
    setzen("whiteboard", whiteboard(), x=-2.5, z=1.9, dreh=40.0)
    setzen("rig_test", rig_offen("led_c_p"), x=3.55, z=-1.2, dreh=-90.0)
    setzen("kabeltrommel", kabeltrommel("cyan_p"), x=-2.6, z=-3.0, dreh=90.0)
    setzen("pflanze_1", pflanze(1.2, stil="palme"), x=-3.5, z=3.0)
    setzen("pflanze_2", pflanze(0.9), x=3.5, z=3.0)
    setzen("pflanze_3", pflanze(1.0, stil="palme"), x=3.55, z=-2.2)
    setzen("pflanze_4", pflanze(0.6), x=-2.6, z=3.1)
    setzen("pflanze_5", pflanze(0.7), x=-3.6, z=-0.9)
    setzen("teppich", [kasten("teppich", (1.8, 0.012, 1.4), (0, 0.006, 0), "lila_hell_p", rund=0.005, segmente=1)],
           x=2.2, z=1.25)
    setzen("sofa", sofa("stoff_senf_p", 1.6), x=-1.4, z=2.9, dreh=180.0)
    setzen("couchtisch", couchtisch(), x=-1.4, z=1.9)
    setzen("kartons", karton(0.45, 0.35, 0.4, "karton_p") + karton(0.35, 0.28, 0.3, "karton_h_p", y=0.35),
           x=0.6, z=-2.9)


# ==============================================================================
# AUSSENANLAGE
# ==============================================================================

AUSSEN_Y = -0.47
FUNDAMENT = (-13.5, 13.5, -10.5, 8.5)
AUSSEN = (-24.0, 21.0, -21.0, 15.0)


def prisma_xy(name, punkte, z0, z1, mat):
    import bmesh
    from build_room_wg import _objekt
    bm = bmesh.new()
    vorn = [bm.verts.new(G(x, y, z1)) for (x, y) in punkte]
    hinten = [bm.verts.new(G(x, y, z0)) for (x, y) in punkte]
    n = len(punkte)
    bm.faces.new(vorn)
    bm.faces.new(list(reversed(hinten)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vorn[i], vorn[j], hinten[j], hinten[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _objekt(name, bm, mat)


def baum(rng, h=3.6, rad=1.1):
    return [zylinder("stamm", 0.12, h * 0.45, (0, 0, 0), "stamm_p", seiten=6, radius_oben=0.08),
            kugel("krone", rad, (0, h * 0.62, 0), "pflanze_p", stauchung=0.9, ringe=5, seiten=8),
            kugel("krone_b", rad * 0.7, (rad * 0.45, h * 0.78, rad * 0.2), "pflanze_d_p", ringe=4, seiten=7),
            kugel("krone_c", rad * 0.6, (-rad * 0.4, h * 0.8, -rad * 0.25), "pflanze_p", ringe=4, seiten=7)]


def busch(rad=0.45):
    return [kugel("busch", rad, (0, rad * 0.6, 0), "pflanze_p", stauchung=0.7, ringe=4, seiten=8),
            kugel("busch_b", rad * 0.65, (rad * 0.6, rad * 0.5, rad * 0.2), "pflanze_d_p", stauchung=0.7, ringe=3,
                  seiten=6)]


def laterne(h=4.2):
    return [zylinder("mast", 0.06, h, (0, 0, 0), "dunkel_p", seiten=6, radius_oben=0.045),
            kasten("arm", (0.05, 0.05, 0.7), (0, h - 0.05, 0.33), "dunkel_p"),
            kasten("kopf", (0.26, 0.1, 0.5), (0, h - 0.1, 0.62), "dunkel_p", rund=0.02, segmente=1),
            kasten("licht", (0.2, 0.01, 0.42), (0, h - 0.155, 0.62), "natrium_p"),
            zylinder("lichtpfuetze", 1.8, 0.012, (0, 0.06, 0.62), "lichtfleck_p", seiten=14)]


def container(farbe, b=6.0, h=2.6, t=2.4):
    teile = [kasten("container", (b, h, t), (0, h / 2, 0), farbe, rund=0.03, segmente=1)]
    n = int(b / 0.3)
    for i in range(n):
        x = -b / 2 + (i + 0.5) * b / n
        for s in (-1, 1):
            teile.append(kasten("sicke", (0.1, h - 0.3, 0.03), (x, h / 2, s * (t / 2 + 0.01)), farbe))
    for s in (-1, 1):
        teile.append(kasten("tuer_rahmen", (0.06, h - 0.1, t), (s * (b / 2 - 0.03) + s * 0.02, h / 2, 0), "dunkel_p"))
    return teile


def schornstein(h=13.0):
    teile = [kasten("schaft", (1.6, h, 1.6), (0, h / 2, 0), "ziegel", rund=0.04, segmente=1),
             kasten("sockel", (2.2, 1.2, 2.2), (0, 0.6, 0), "ziegel_d_f"),
             kasten("kopf", (1.9, 0.5, 1.9), (0, h - 0.1, 0), "ziegel_d_f")]
    for y in (h * 0.35, h * 0.6, h * 0.85):
        teile.append(kasten("band", (1.64, 0.25, 1.64), (0, y, 0), "fuge_f"))
    teile.append(kasten("lichtring", (1.95, 0.12, 1.95), (0, h - 0.5, 0), "led_v_p"))
    return teile


def sheddach_halle(x0, x1, z0, z1, h=3.2, zahn=2.2, zahn_h=1.2):
    """Nachbarhalle mit Saegezahndach: senkrechte Glasflaechen zeigen nach +x."""
    teile = [kasten("halle", (x1 - x0, h, z1 - z0), ((x0 + x1) / 2, h / 2, (z0 + z1) / 2), "ziegel", rund=0.03,
                    segmente=1),
             kasten("traufe", (x1 - x0 + 0.1, 0.12, z1 - z0 + 0.1), ((x0 + x1) / 2, h, (z0 + z1) / 2), "kappe_f")]
    x = x0
    while x + zahn <= x1 + 0.01:
        teile.append(prisma_xy("zahn", [(x, h + 0.06), (x + zahn, h + 0.06), (x + zahn, h + 0.06 + zahn_h)],
                               z0, z1, "dach_p"))
        teile.append(kasten("oberlicht", (0.03, zahn_h * 0.8, z1 - z0 - 0.3),
                            (x + zahn + 0.02, h + 0.06 + zahn_h * 0.45, (z0 + z1) / 2), "glas"))
        teile.append(kasten("oberlicht_rahmen", (0.05, 0.06, z1 - z0), (x + zahn + 0.01, h + 0.06 + zahn_h - 0.03,
                                                                         (z0 + z1) / 2), "kappe_f"))
        x += zahn
    # Fensterreihe an der Stirnseite (+z), halb verdeckt von der Hallenrueckwand
    n = int((x1 - x0) / 2.0)
    for i in range(n):
        fx = x0 + 1.0 + i * 2.0
        teile.append(kasten("fenster", (1.1, 1.1, 0.03), (fx, 2.0, z1 + 0.01), "fenster_n_p" if i % 3 != 1 else "glas"))
    return teile


def kuehlturm(r=1.1, h=3.2):
    return [zylinder("turm", r, h, (0, 0, 0), "hellgrau_p", seiten=14, radius_oben=r * 0.8),
            zylinder("band", r * 0.93, 0.25, (0, h * 0.62, 0), "violett_p", seiten=14),
            zylinder("rand", r * 0.85, 0.15, (0, h - 0.05, 0), "dunkel_p", seiten=14),
            zylinder("luefter", r * 0.6, 0.05, (0, h + 0.05, 0), "grau_p", seiten=10)]


def bank():
    teile = [kasten("sitz", (1.6, 0.05, 0.42), (0, 0.44, 0), "holz_p", rund=0.01, segmente=1),
             kasten("lehne", (1.6, 0.3, 0.04), (0, 0.72, -0.2), "holz_p", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("fuss", (0.06, 0.44, 0.4), (sx * 0.65, 0.22, 0), "dunkel_p"))
    return teile


def pflanzkasten(lang=2.4):
    teile = [kasten("kasten", (lang, 0.4, 0.6), (0, 0.2, 0), "holz_p", rund=0.02, segmente=1)]
    for i in range(int(lang / 0.45)):
        x = -lang / 2 + 0.25 + i * 0.45
        teile.append(kugel("gruen", 0.2, (x, 0.48, 0), "pflanze_p" if i % 2 else "pflanze_d_p", ringe=3, seiten=6))
        if i % 2 == 0:
            teile.append(kugel("bluete", 0.06, (x + 0.08, 0.64, 0.1), "lila_hell_p", ringe=2, seiten=5))
    return teile


def poller():
    return [zylinder("poller", 0.08, 0.7, (0, 0, 0), "dunkel_p", seiten=8),
            zylinder("ring", 0.085, 0.06, (0, 0.55, 0), "led_v_p", seiten=8)]


def sperre(lang=2.4):
    """Betonleitwand mit Warnstreifen -- ersetzt den Pflanzkasten."""
    teile = [kasten("sperre", (lang, 0.8, 0.45), (0, 0.4, 0), "fundament_p", rund=0.04, segmente=1)]
    n = max(2, int(lang / 0.6))
    for i in range(n):
        x = -lang / 2 + (i + 0.5) * lang / n
        if i % 2 == 0:
            teile.append(kasten("streifen", (lang / n * 0.55, 0.16, 0.47), (x, 0.62, 0), "gelb_p"))
    return teile


def auto(farbe="auto_p", laenge=4.0, hoehe=0.62, kabine=2.0):
    """Kleinwagen, Front +x, Ursprung Mitte unten."""
    teile = [kasten("karosse", (laenge, hoehe, 1.7), (0, 0.32 + hoehe / 2, 0), farbe, rund=0.08, segmente=1),
             kasten("kabine", (kabine, 0.5, 1.5), (-0.25, 0.32 + hoehe + 0.22, 0), farbe, rund=0.08, segmente=1),
             kasten("scheibe_s", (kabine + 0.02, 0.36, 1.52), (-0.25, 0.32 + hoehe + 0.25, 0), "dunkel_p")]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(liegender_zylinder("rad", 0.34, 0.22, (sx * laenge * 0.32, 0.34, sz * 0.8), "z", "gummi_p",
                                            seiten=10))
    for sz in (-1, 1):
        teile.append(kasten("licht_v", (0.04, 0.12, 0.3), (laenge / 2, 0.62, sz * 0.58), "led_w_p"))
        teile.append(kasten("licht_h", (0.04, 0.12, 0.3), (-laenge / 2, 0.62, sz * 0.58), "ruecklicht_p"))
    return teile


def strommast(h=9.5):
    teile = [zylinder("pfahl", 0.17, h, (0, 0, 0), "mast_p", seiten=7, radius_oben=0.12),
             kasten("traverse_o", (0.14, 0.14, 2.6), (0, h - 0.4, 0), "mast_p"),
             kasten("traverse_u", (0.14, 0.14, 1.9), (0, h - 1.5, 0), "mast_p")]
    for zz in (-1.2, 0.0, 1.2):
        teile.append(zylinder("isolator", 0.07, 0.3, (0, h - 0.33, zz), "isolator_p", seiten=6))
    for zz in (-0.85, 0.85):
        teile.append(zylinder("isolator_u", 0.07, 0.3, (0, h - 1.43, zz), "isolator_p", seiten=6))
    return teile


def luefterwand_gross(spalten=3, zeilen=3, zelle=1.7):
    """Grosse Luefterwand (Landmark): Rahmen, 3 x 3 Luefter mit Blaettern, LED-Rand."""
    b, h = spalten * zelle + 0.3, zeilen * zelle + 0.3
    y0 = 0.5
    teile = [kasten("rahmen", (b, h, 0.45), (0, y0 + h / 2, 0), "stahl", rund=0.03, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("fuss", (0.3, y0, 0.7), (sx * (b / 2 - 0.4), y0 / 2, 0), "dunkel_p"))
    for i in range(spalten):
        for k in range(zeilen):
            cx = (i - (spalten - 1) / 2) * zelle
            cy = y0 + 0.15 + zelle / 2 + k * zelle
            teile.append(liegender_zylinder("tiefe", zelle * 0.46, 0.06, (cx, cy, 0.24), "z", "dunkel_p", seiten=14))
            teile.append(liegender_zylinder("ring", zelle * 0.48, 0.05, (cx, cy, 0.27), "z", "grau_p", seiten=14,
                                            deckel=False))
            for j in range(3):
                bl = kasten("blatt", (zelle * 0.40, 0.2, 0.015), (zelle * 0.21, 0, 0), "alu_p")
                bl.matrix_world = (Matrix.Translation(G(cx, cy, 0.285))
                                   @ Matrix.Rotation(math.radians(j * 120 + 17 * ((i + k) % 3)), 4, "Y")
                                   @ bl.matrix_world)
                teile.append(bl)
            teile.append(zylinder("nabe", 0.11, 0.05, (cx, cy - 0.05, 0.27), "dunkel_p", seiten=8))
    teile.append(kasten("led_oben", (b - 0.1, 0.07, 0.03), (0, y0 + h - 0.06, 0.24), "led_v_p"))
    teile.append(kasten("led_unten", (b - 0.1, 0.07, 0.03), (0, y0 + 0.07, 0.24), "led_c_p"))
    for sx in (-1, 1):
        teile.append(kasten("led_seite", (0.07, h - 0.3, 0.03), (sx * (b / 2 - 0.06), y0 + h / 2, 0.24), "led_v_p"))
    teile.append(zylinder("bake_fuss", 0.12, 0.1, (b / 2 - 0.4, y0 + h, 0), "dunkel_p", seiten=8))
    teile.append(zylinder("bake", 0.14, 0.2, (b / 2 - 0.4, y0 + h + 0.1, 0), "natrium_p", seiten=8))
    return teile


def einrichtung_welt_luefterwand():
    setzen("luefterwand_gross", luefterwand_gross(), y=AUSSEN_Y)


def einrichtung_welt_strommast_trasse():
    """Freileitung entlang x hinter der Halle: vier Masten, drei Spannfelder."""
    xs = (-21.0, -8.0, 5.0, 18.0)
    zl = -17.3
    for i, x in enumerate(xs):
        setzen("mast_%d" % i, strommast(), x=x, z=zl, y=AUSSEN_Y, dreh=0.0)
    for a, bx in zip(xs[:-1], xs[1:]):
        for zz in (-1.2, 0.0, 1.2):
            hh = 9.1
            mitte = (a + bx) / 2
            setzen("draht", [stab("d1", (a, hh, zl + zz), (mitte, hh - 0.55, zl + zz), 0.035, "draht_p"),
                             stab("d2", (mitte, hh - 0.55, zl + zz), (bx, hh, zl + zz), 0.035, "draht_p")],
                   y=AUSSEN_Y)


def _nacht_zusatz(y):
    """Landmarken und Bodenwahrheit der Nacht: Fahrzeuge, Pfuetzen, Funken, Dampf."""
    setzen("auto_roman", auto("auto_p"), x=-7.5, y=y, z=12.5, dreh=180.0)
    setzen("transporter", auto("van_p", 5.2, 1.15, 3.0), x=7.5, y=y, z=12.9)
    for i, (px, pz, pb, pt) in enumerate(((-11.0, 13.4, 2.2, 0.9), (1.5, 14.0, 1.6, 0.8), (13.5, 12.2, 1.8, 0.9),
                                          (-2.0, 9.0, 1.2, 0.7), (-16.0, 0.0, 1.4, 0.8), (17.0, -9.0, 1.5, 0.8),
                                          (11.0, 9.2, 1.0, 0.6))):
        setzen("pfuetze_%d" % i, [kasten("pfuetze", (pb, 0.004, pt), (px, 0.05, pz), "pfuetze_p", unten=False)], y=y)
    # Funken am Aussentrafo (Position wie trafo_aussen: x 3,0 z -12,6)
    zig = [(2.55, 2.05), (2.66, 2.35), (2.78, 2.08), (2.9, 2.38), (3.02, 2.08), (3.14, 2.34), (3.26, 2.06)]
    funken = [stab("funke", (zig[i][0], zig[i][1], -12.45), (zig[i + 1][0], zig[i + 1][1], -12.45), 0.03, "funke_p")
              for i in range(len(zig) - 1)]
    setzen("funken", funken, y=y)
    # Dampf aus dem Schornstein und den Kuehltuermen
    dampf = []
    for dx, dy, r in ((0.0, 13.7, 0.8), (0.9, 14.9, 1.1), (2.0, 16.3, 1.4), (3.4, 17.9, 1.7)):
        dampf.append(kugel("dampf", r, (-17.5 + dx, dy, -15.5 + dx * 0.4), "dampf_p", stauchung=0.8, ringe=4, seiten=8))
    for dx, dy, r in ((0.0, 3.6, 0.55), (0.6, 4.4, 0.7)):
        dampf.append(kugel("dampf_k", r, (11.5 + dx, dy, -13.5 + dx * 0.3), "dampf_p", stauchung=0.8, ringe=4, seiten=8))
        dampf.append(kugel("dampf_k2", r * 0.8, (14.2 + dx, dy - 0.5, -13.0 + dx * 0.3), "dampf_p", stauchung=0.8,
                           ringe=4, seiten=8))
    setzen("dampf", dampf, y=y)


def einrichtung_umgebung():
    rng = random.Random(55)
    x0, x1, z0, z1 = AUSSEN
    fx0, fx1, fz0, fz1 = FUNDAMENT
    y = AUSSEN_Y
    boden = [
        kasten("boden_hinten", (x1 - x0, 0.03, fz0 - z0), ((x0 + x1) / 2, y + 0.015, (z0 + fz0) / 2), "pflaster_p", unten=False),
        kasten("boden_vorn", (x1 - x0, 0.03, z1 - fz1), ((x0 + x1) / 2, y + 0.015, (fz1 + z1) / 2), "pflaster_p", unten=False),
        kasten("boden_links", (fx0 - x0, 0.03, fz1 - fz0), ((x0 + fx0) / 2, y + 0.015, (fz0 + fz1) / 2), "pflaster_p", unten=False),
        kasten("boden_rechts", (x1 - fx1, 0.03, fz1 - fz0), ((fx1 + x1) / 2, y + 0.015, (fz0 + fz1) / 2), "pflaster_p", unten=False),
    ]
    for _ in range(40):
        px, pz = rng.uniform(x0 + 0.5, x1 - 0.5), rng.uniform(z0 + 0.5, 10.0)
        if fx0 - 0.4 < px < fx1 + 0.4 and fz0 - 0.4 < pz < fz1 + 0.4:
            continue
        boden.append(kasten("fleck", (rng.choice((0.5, 1.0)), 0.004, 0.5), (px, y + 0.032, pz), "pflaster_d_p",
                            unten=False))
    setzen("boden", boden)
    # Rasenstreifen rechts und vorn, Strasse vorn
    setzen("rasen", [kasten("rasen_r", (4.0, 0.05, 12.0), (17.5, y + 0.025, -4.0), "rasen_p", unten=False),
                     kasten("rasen_v", (20.0, 0.05, 1.6), (-4.0, y + 0.025, 10.2), "rasen_p", unten=False),
                     kasten("rasen_l", (6.0, 0.05, 10.0), (-20.0, y + 0.025, 6.0), "rasen_d_p", unten=False)])
    strasse = [kasten("bordstein", (x1 - x0, 0.12, 0.25), ((x0 + x1) / 2, y + 0.06, 11.4), "fundament_p", unten=False),
               kasten("asphalt", (x1 - x0, 0.02, 3.2), ((x0 + x1) / 2, y + 0.035, 13.2), "asphalt_p", unten=False)]
    x = x0 + 0.8
    while x < x1 - 1:
        strasse.append(kasten("markierung", (1.2, 0.004, 0.12), (x, y + 0.047, 13.2), "weiss_p", unten=False))
        x += 2.4
    setzen("strasse", strasse)
    # Hinten: Nachbarhalle mit Saegezahndach, Schornstein, Kuehltuerme
    setzen("sheddach", sheddach_halle(-14.0, 8.0, -15.0, -11.4), y=y)
    setzen("schornstein", schornstein(), x=-17.5, z=-15.5, y=y)
    setzen("kuehlturm_1", kuehlturm(), x=11.5, z=-13.5, y=y)
    setzen("kuehlturm_2", kuehlturm(0.9, 2.6), x=14.2, z=-13.0, y=y)
    # Links: Container gestapelt, Zaun
    setzen("container_1", container("container_a_p"), x=-18.0, z=-7.0, y=y, dreh=90.0)
    setzen("container_2", container("container_b_p"), x=-18.0, z=-4.4, y=y, dreh=90.0)
    setzen("container_3", container("container_c_p", 6.0, 2.6, 2.4), x=-18.0, z=-5.7, y=y + 2.6, dreh=90.0)
    setzen("container_4", container("container_a_p"), x=-21.5, z=-1.0, y=y, dreh=90.0)
    for i in range(8):
        setzen("zaun_hinten_%d" % i, zaunfeld(2.5, 2.0), x=-20.0 + i * 2.5, z=-19.5, y=y)
    for i in range(6):
        setzen("zaun_links_%d" % i, zaunfeld(2.5, 2.0), x=-23.5, z=-18.0 + i * 2.5, y=y, dreh=90.0)
    setzen("laterne_1", laterne(), x=-15.0, y=y, z=-12.0, dreh=-45.0)
    setzen("laterne_2", laterne(), x=-15.5, y=y, z=3.0, dreh=90.0)
    for i, (lx, lz, ld) in enumerate(((-11.0, 10.9, 0.0), (0.5, 10.9, 0.0), (11.0, 10.9, 0.0),
                                      (18.0, -5.0, -90.0), (18.0, 6.0, -90.0), (-17.5, 9.0, 90.0))):
        setzen("laterne_hof_%d" % i, laterne(), x=lx, y=y, z=lz, dreh=ld)
    setzen("trafo_aussen", trafo_gross(), x=3.0, z=-12.6, y=y)
    setzen("kabeltrommeln", kabeltrommel() + transformieren(kabeltrommel("cyan_p"), x=0.7), x=-15.5, z=-9.0, y=y)
    setzen("paletten", palette() + transformieren(palette(), y=0.144, dreh_grad=5), x=-15.2, z=6.0, y=y, dreh=90.0)
    # Rechts und vorn: nur Niedriges (<= 1 m)
    for i, pz in enumerate((-3.2, -0.8)):
        setzen("poller_tuer_%d" % i, poller(), x=14.3, z=pz, y=y)
    setzen("weg_rechts", [kasten("weg", (3.0, 0.02, 1.4), (0, 0.04, 0), "fundament_p", unten=False)],
           x=15.0, z=-2.0, y=y)
    for i, (hx, hz, dreh) in enumerate(((16.5, -8.0, 90.0), (16.5, 4.0, 90.0), (-8.0, 9.6, 0.0), (3.0, 9.6, 0.0))):
        setzen("pflanzkasten_%d" % i, sperre(), x=hx, y=y, z=hz, dreh=dreh)
    setzen("bank_vorn", bank(), x=9.0, y=y, z=9.8, dreh=180.0)
    setzen("bank_rechts", bank(), x=17.2, y=y, z=0.5, dreh=-90.0)
    for i, px in enumerate((-2.0, 0.0, 2.0, 12.0)):
        setzen("poller_%d" % i, poller(), x=px, y=y, z=10.6)
    for i, (bx, bz) in enumerate(((18.8, -12.0), (-13.0, 10.2), (15.0, 9.5), (19.0, 7.0), (-18.0, 11.0))):
        setzen("fass_%d" % i, pflanze(rng.uniform(0.9, 1.2)), x=bx, y=y, z=bz)
    _nacht_zusatz(y)


def einrichtung_fundament():
    fx0, fx1, fz0, fz1 = FUNDAMENT
    h = 0.45
    setzen("fundament", [kasten("sockel", (fx1 - fx0, h, fz1 - fz0), ((fx0 + fx1) / 2, -0.02 - h / 2, (fz0 + fz1) / 2),
                                "fundament_p", rund=0.06, segmente=2),
                         kasten("lichtband", (fx1 - fx0 + 0.01, 0.04, fz1 - fz0 + 0.01),
                                ((fx0 + fx1) / 2, -0.12, (fz0 + fz1) / 2), "led_v_p")])


def einrichtung_fluss_teil():
    """Leuchtender Datenwuerfel: violetter Kern in einem hellen Rahmen,
    davor ein kleiner Ring. Kein Logo, keine Schrift. Ursprung Mitte."""
    k = 0.2
    teile = [kasten("kern", (k, k, k), (0, 0, 0), "led_v_p", rund=0.03, segmente=2)]
    a = k / 2 + 0.012
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            teile.append(kasten("kante_x", (k + 0.05, 0.03, 0.03), (0, s1 * a, s2 * a), "alu_p"))
            teile.append(kasten("kante_y", (0.03, k + 0.05, 0.03), (s1 * a, 0, s2 * a), "alu_p"))
            teile.append(kasten("kante_z", (0.03, 0.03, k + 0.05), (s1 * a, s2 * a, 0), "alu_p"))
    for s in (-1, 1):
        teile.append(kasten("punkt", (0.05, 0.05, 0.006), (0, 0, s * (k / 2 + 0.004)), "led_c_p"))
        teile.append(kasten("punkt_x", (0.006, 0.05, 0.05), (s * (k / 2 + 0.004), 0, 0), "led_c_p"))
        teile.append(kasten("punkt_y", (0.05, 0.006, 0.05), (0, s * (k / 2 + 0.004), 0), "led_c_p"))
    setzen("fluss_teil", teile)


# ==============================================================================
# ABLAUF
# ==============================================================================

EINRICHTUNGEN = {
    "halle": einrichtung_halle,
    "kabeltrasse": einrichtung_kabeltrasse,
    "trafo": einrichtung_trafo,
    "kontrollraum": einrichtung_kontrollraum,
    "solardach": einrichtung_solardach,
    "rackhalle_2": einrichtung_rackhalle_2,
    "selins_labor": einrichtung_selins_labor,
}
AUSSENTEILE = {"umgebung": (einrichtung_umgebung, UMGEBUNG_BUDGET),
               "welt_luefterwand": (einrichtung_welt_luefterwand, 3000),
               "welt_strommast_trasse": (einrichtung_welt_strommast_trasse, 3000),
               "fundament": (einrichtung_fundament, 2000),
               "fluss_teil": (einrichtung_fluss_teil, 600)}


def pfad(name):
    return os.path.join(AUSGABE, name + ".glb")


def _export(name, budget):
    obj = verbinden([t for _, teile in MOEBEL for t in teile], name)
    exportieren(obj, pfad(name))
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    print("  -> %s: %d Dreiecke (Budget %d)%s, %d Mat, %.0f KB, BBox x %+.2f..%+.2f y %.2f..%.2f z %+.2f..%+.2f"
          % (name, n, budget, "  <-- UEBER BUDGET" if n > budget else "", len(obj.data.materials),
             os.path.getsize(pfad(name)) / 1024.0, x0, x1, y0, y1, z0, z1))
    ERGEBNIS.append((name, n, budget))
    return n


def zone_bauen(name):
    alles_loeschen()
    del MOEBEL[:]
    zone = ZONEN[name]
    EINRICHTUNGEN[name]()
    print("")
    print("=== EINRICHTUNG %s (%g x %g) ===" % (name.upper(), zone["breite"], zone["tiefe"]))
    zu_viel = moebel_bericht()
    fehler = freiflaechen_pruefen(zone)
    n = _export("einrichtung_" + name, ZONEN_BUDGET)
    print("     Freiflaechen-/Wandpruefung: %s" % ("OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler))
    return fehler + zu_viel + (1 if n > ZONEN_BUDGET else 0)


def aussen_bauen(name):
    alles_loeschen()
    del MOEBEL[:]
    bauen, budget = AUSSENTEILE[name]
    bauen()
    print("")
    print("=== %s ===" % name.upper())
    moebel_bericht(1000)
    n = _export(name, budget)
    return 1 if n > budget else 0


def freiflaechen_markieren(zone, x=0.0, z=0.0):
    for (fx, fz, fb, ft, _, art) in zone["frei"]:
        d = 0.05
        mat = "vorschau_frei" if art == "S" else "vorschau_weg"
        for (gx, gz, sb, st) in ((fx, fz - ft / 2 + d / 2, fb, d), (fx, fz + ft / 2 - d / 2, fb, d),
                                 (fx - fb / 2 + d / 2, fz, d, ft), (fx + fb / 2 - d / 2, fz, d, ft)):
            kasten("frei", (sb, 0.006, st), (x + gx, 0.006 + (0.002 if art == "S" else 0), z + gz), mat)


def zone_vorschau(name):
    alles_loeschen()
    _CACHE.clear()
    zone = dict(ZONEN[name])
    zone["welt"] = (0.0, 0.0)
    for mod, x, z, dreh, _ in huelle_module(zone):
        platzieren(modul.modul_pfad(mod), x=x, z=z, dreh=dreh)
    importieren(pfad("einrichtung_" + name))
    freiflaechen_markieren(zone)
    breite = None
    aufl = 1000
    if name == "kabeltrasse":
        breite = 1800
    modul.rendern(os.path.join(VORSCHAU, "zone_%s.png" % name), (0.0, 0.6, 0.0), zone["ortho"],
                  aufloesung=aufl, breite=breite)


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
    stationen = WURZEL + "/project/assets/stations/produkt/station_%s_3.glb"
    for sid, sx, sz in (("intake", -2.4, 1.65), ("buffer", 0.0, 4.7), ("processing", 2.2, 1.65),
                        ("transport", 4.0, -2.3), ("special", 0.8, -6.6)):
        if os.path.exists(stationen % sid):
            importieren(stationen % sid, x=sx, z=sz)
    if not mit_markierung:
        for i, (fx, fz) in enumerate(((-1.0, -0.6), (2.0, 3.0))):
            importieren(pfad("fluss_teil"), x=fx, z=fz, y=1.2)
    datei = "gesamt_markiert.png" if mit_markierung else "gesamt.png"
    modul.rendern(os.path.join(VORSCHAU, datei), (-0.5, 0.3, -1.5), 38.0, aufloesung=1800)
    if not mit_markierung:
        modul.rendern(os.path.join(VORSCHAU, "gesamt_nah_links.png"), (-6.5, 0.6, -2.0), 16.0, aufloesung=1400)
        modul.rendern(os.path.join(VORSCHAU, "gesamt_nah_rechts.png"), (5.5, 0.6, -1.5), 16.0, aufloesung=1400)


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
    for name, n, budget in ERGEBNIS:
        print("  %-28s %6d Dreiecke (Budget %d)" % (name, n, budget))
    print("=== FERTIG: %s ===" % ("keine Verletzungen" if fehler == 0 else "%d Probleme -- siehe oben" % fehler))


if __name__ == "__main__":
    main()
