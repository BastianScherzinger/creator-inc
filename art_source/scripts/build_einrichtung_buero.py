"""Raumeinrichtungen, Umgebung und Fundament fuer Welt 4 (Lagerhalle),
Nachtplan N30 (docs/NACHT_PLAN.md Abschnitte 2 und 5).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_buero.py
    (optional nach "--": zonennamen      -> nur diese Zonen
                         --ohne-vorschau -> keine Renders
                         --nur-vorschau  -> nichts bauen, nur rendern)

Voraussetzung: build_room_buero_neu.py ist gelaufen (Module fuer die Vorschau).

Erzeugt project/assets/world/buero/:
    einrichtung_<zone>.glb  EIN Mesh je Zone, Ursprung = Zonenmitte (Godot)
    umgebung.glb            Gewerbegebiet um die Halle, Ursprung 0,0
    fundament.glb           Sockel unter der Grundflaeche
Freiflaechen (Stationen, Tuergaenge, Laufwege) prueft das Skript selbst.

Waende der Vorschau (Vorschlag fuer worlds.json, Welt-Koordinaten) stehen in
WAENDE unten -- Tueren und Fenster sind darauf abgestimmt.
"""

import bpy
import bmesh
import math
import os
import random
import sys
from mathutils import Matrix, Vector

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, transformieren, alles_loeschen,
    verbinden, dreiecke, masse, exportieren, palette_erweitern, _objekt, material, WURZEL,
)
from build_room_buero_neu import (  # noqa: E402
    rendern, modul_pfad, flach_viereck, AUSGABE_VORSCHAU,
)

AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "buero")

palette_erweitern({
    "holz_palette":     ("#DDB77F", 0.85, 0.0, 1.0),
    "holz_palette_d":   ("#BF9660", 0.85, 0.0, 1.0),
    "karton":           ("#C99A62", 0.90, 0.0, 1.0),
    "karton_hell":      ("#DDB47C", 0.90, 0.0, 1.0),
    "karton_dunkel":    ("#B8884F", 0.90, 0.0, 1.0),
    "klebeband":        ("#EBD9B0", 0.60, 0.0, 1.0),
    "etikett":          ("#F7F6F1", 0.70, 0.0, 1.0),
    "regal_orange":     ("#F08A24", 0.55, 0.20, 1.0),
    "gitterboden":      ("#A3ADB6", 0.50, 0.40, 1.0),
    "metall_hell_l":    ("#C8CFD5", 0.35, 0.45, 1.0),
    "metall_dunkel_l":  ("#48505A", 0.50, 0.35, 1.0),
    "kunststoff_schwarz": ("#2F3237", 0.55, 0.0, 1.0),
    "rot_signal":       ("#E0463A", 0.55, 0.0, 1.0),
    "orange_kegel":     ("#FF7A2A", 0.60, 0.0, 1.0),
    "weiss_l":          ("#F4F5F2", 0.70, 0.0, 1.0),
    "folie":            ("#DDEEF3", 0.15, 0.0, 0.55),
    "folie_rolle":      ("#D3E6EC", 0.20, 0.0, 1.0),
    "bildschirm":       ("#26323F", 0.35, 0.0, 1.0),
    "bildschirm_t":     ("#3FD6C6", 0.40, 0.0, 1.0),
    "bildschirm_b":     ("#7FB2FF", 0.40, 0.0, 1.0),
    "bildschirm_o":     ("#FF9F4A", 0.40, 0.0, 1.0),
    "bildschirm_p":     ("#FF6FAE", 0.40, 0.0, 1.0),
    "stoff_grau_l":     ("#7F8A95", 0.95, 0.0, 1.0),
    "stoff_dunkel_l":   ("#4D5662", 0.95, 0.0, 1.0),
    "stoff_senf_l":     ("#E3A93B", 0.90, 0.0, 1.0),
    "stoff_koralle_l":  ("#EE8F7E", 0.90, 0.0, 1.0),
    "stoff_tuerkis":    ("#1FA89A", 0.90, 0.0, 1.0),
    "pflanze_l":        ("#5DA84A", 0.80, 0.0, 1.0),
    "pflanze_d_l":      ("#3E8A3B", 0.80, 0.0, 1.0),
    "topf_weiss":       ("#EEF0EE", 0.60, 0.0, 1.0),
    "topf_terra_l":     ("#C9744A", 0.85, 0.0, 1.0),
    "erde_l":           ("#5C4030", 0.95, 0.0, 1.0),
    "holz_tisch":       ("#DDB98C", 0.70, 0.0, 1.0),
    "holz_stamm":       ("#8A6446", 0.90, 0.0, 1.0),
    "notiz_gelb":       ("#FFE066", 0.80, 0.0, 1.0),
    "notiz_rosa":       ("#FF9FB2", 0.80, 0.0, 1.0),
    "notiz_blau":       ("#8EC9FF", 0.80, 0.0, 1.0),
    "kicker_gruen":     ("#3FAE5A", 0.80, 0.0, 1.0),
    "fahrzeug_weiss":   ("#F1F3F4", 0.40, 0.10, 1.0),
    "rasen":            ("#8CC56A", 0.95, 0.0, 1.0),
    "rasen_dunkel":     ("#74B257", 0.95, 0.0, 1.0),
    "beton_hell":       ("#D3D7DA", 0.85, 0.0, 1.0),
    "beton_sockel":     ("#C2C8CD", 0.85, 0.0, 1.0),
    "markierung":       ("#F3F4EF", 0.70, 0.0, 1.0),
    "lampe_licht":      ("#FFF1C4", 0.50, 0.0, 1.0),
    "kaffee":           ("#6B4430", 0.60, 0.0, 1.0),
    "aussen_dunkel":    ("#353C44", 0.90, 0.0, 1.0),
    "gruen_schild":     ("#2BA35A", 0.60, 0.0, 1.0),
    "vorschau_frei":    ("#2FC4B2", 0.90, 0.0, 1.0),
    "whiteboard_weiss": ("#FBFCFB", 0.40, 0.0, 1.0),
    # M2: Hof, LKW, Container
    "pfuetze":          ("#AEB8C2", 0.12, 0.25, 1.0),
    "cont_rot":         ("#A8473B", 0.60, 0.20, 1.0),
    "cont_blau":        ("#46688C", 0.60, 0.20, 1.0),
    "cont_gruen":       ("#5C7F6A", 0.60, 0.20, 1.0),
    "cont_grau":        ("#8A939B", 0.60, 0.20, 1.0),
    "cont_rippe":       ("#2E3944", 0.80, 0.10, 1.0),
    "lkw_kabine":       ("#E8ECEE", 0.45, 0.10, 1.0),
    "lkw_plane":        ("#12B5A5", 0.75, 0.0, 1.0),
    "lkw_plane_dunkel": ("#0E9488", 0.80, 0.0, 1.0),
    "lkw_rahmen":       ("#3A424B", 0.55, 0.30, 1.0),
    # Aliase -- weniger Draw Calls
    "tuerkis":          "kappe_tuerkis",
    "blau_stahl":       "stahl_blau",
    "gelb":             "warn_gelb",
    "schwarz":          "warn_schwarz",
    "reifen":           "kunststoff_schwarz",
    "glas":             "glas_kuehl",
})

# ==============================================================================
# BUCHFUEHRUNG (wie build_einrichtung_wg_a.py)
# ==============================================================================

MOEBEL = []
MOEBEL_BUDGET = 600
ZONEN_BUDGET = 8000


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
    gesamt = 0
    ueber = 0
    for name, teile in MOEBEL:
        n = 0
        for t in teile:
            n += _auswerten(t)[0]
        gesamt += n
        if n > budget:
            ueber += 1
            print("    %-28s %5d  <-- UEBER BUDGET" % (name, n))
    return gesamt, ueber


def freiflaechen_pruefen(zone):
    toleranz = 0.01
    fehler = 0
    hx, hz = zone["breite"] / 2.0 - 0.1, zone["tiefe"] / 2.0 - 0.1
    for name, teile in MOEBEL:
        unterkante = min(min(p.z for p in _auswerten(t)[1]) for t in teile)
        if unterkante > 0.03 and not name.startswith(("wand_", "auf_")):
            # Nichts schwebt -- ausser an der Wand Befestigtem (wand_*) und
            # dem, was auf einem anderen Moebel steht (auf_*)
            print("    SCHWEBT: %s  Unterkante y %.2f" % (name, unterkante))
            fehler += 1
        for t in teile:
            _, punkte = _auswerten(t)
            if not punkte:
                continue
            x0 = min(p.x for p in punkte); x1 = max(p.x for p in punkte)
            z0 = min(-p.y for p in punkte); z1 = max(-p.y for p in punkte)
            y1 = max(p.z for p in punkte)
            if y1 > 0.021:
                for (fx, fz, fb, ft, was) in zone["frei"]:
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
# GRUNDFORMEN
# ==============================================================================

def stab(name, a, b, dicke, mat):
    pa, pb = G(*a), G(*b)
    richtung = pb - pa
    obj = kasten(name, (dicke, richtung.length, dicke), (0, 0, 0), mat)
    dreh = richtung.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    obj.matrix_world = Matrix.Translation((pa + pb) / 2.0) @ dreh
    return obj


def prisma(name, punkte_xy, z0, z1, mat):
    """Polygon (x, y) in der Godot-xy-Ebene, entlang z von z0 bis z1 extrudiert."""
    bm = bmesh.new()
    vorn = [bm.verts.new(G(x, y, z1)) for (x, y) in punkte_xy]
    hinten = [bm.verts.new(G(x, y, z0)) for (x, y) in punkte_xy]
    n = len(punkte_xy)
    bm.faces.new(vorn)
    bm.faces.new(list(reversed(hinten)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vorn[i], vorn[j], hinten[j], hinten[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _objekt(name, bm, mat)


def flach(name, b, t, x, z, mat, y=0.004):
    """Bodenmarkierung: flaches Rechteck, darf in Freiflaechen liegen."""
    return flach_viereck(name, [(x - b / 2, z - t / 2), (x + b / 2, z - t / 2),
                                (x + b / 2, z + t / 2), (x - b / 2, z + t / 2)], y, mat)


def rahmen_markierung(x, z, b, t, mat="gelb", d=0.06, y=0.004):
    return [flach("mark", b, d, x, z - t / 2 + d / 2, mat, y), flach("mark", b, d, x, z + t / 2 - d / 2, mat, y),
            flach("mark", d, t - 2 * d, x - b / 2 + d / 2, z, mat, y),
            flach("mark", d, t - 2 * d, x + b / 2 - d / 2, z, mat, y)]


def karton(b=0.4, h=0.3, t=0.4, mat="karton", klebe=True, rund=0.0, x=0.0, y=0.0, z=0.0):
    teile = [kasten("karton", (b, h, t), (x, y + h / 2, z), mat, rund=rund, segmente=1)]
    if klebe:
        teile.append(kasten("klebe", (0.06, 0.004, t + 0.004), (x, y + h + 0.001, z), "klebeband"))
    return teile


_KARTON_TOENE = ("karton", "karton_hell", "karton_dunkel", "karton")


def palette(b=1.2, t=0.8, einfach=False):
    """Europalette, Oberkante 0,144. einfach=True fuer Regalinhalte."""
    H = 0.144
    teile = []
    if einfach:
        teile.append(kasten("pal_deck", (b, 0.022, t), (0, H - 0.011, 0), "holz_palette"))
        for s in (-1, 0, 1):
            teile.append(kasten("pal_kufe", (b, H - 0.022, 0.1), (0, (H - 0.022) / 2, s * (t / 2 - 0.05)),
                                "holz_palette_d", unten=False))
        return teile
    for i in range(5):
        z = -t / 2 + 0.05 + i * (t - 0.1) / 4
        teile.append(kasten("pal_brett", (b, 0.022, 0.1), (0, H - 0.011, z), "holz_palette"))
    for s in (-1, 0, 1):
        z = s * (t / 2 - 0.05)
        teile.append(kasten("pal_quer", (b, 0.022, 0.1), (0, 0.111, z), "holz_palette"))
        teile.append(kasten("pal_unten", (b, 0.022, 0.1), (0, 0.011, z), "holz_palette"))
        for k in (-1, 0, 1):
            teile.append(kasten("pal_klotz", (0.12, 0.078, 0.1), (k * (b / 2 - 0.06), 0.061, z),
                                "holz_palette_d"))
    return teile


def kartons_auf_palette(rng, lagen=2, b=1.2, t=0.8, folie=False, einfach=True, zufall=0.0):
    teile = palette(b, t, einfach)
    y = 0.144
    kb, kt = b / 3, t / 2
    for lage in range(lagen):
        h = rng.choice((0.28, 0.32, 0.36))
        for i in range(3):
            for k in range(2):
                if lage == lagen - 1 and rng.random() < zufall:
                    continue
                teile += karton(kb - 0.02, h - 0.01, kt - 0.02, rng.choice(_KARTON_TOENE),
                                klebe=(lage == lagen - 1),
                                x=-b / 2 + kb / 2 + i * kb, y=y, z=-t / 2 + kt / 2 + k * kt)
        y += h
    if folie:
        teile.append(kasten("folie", (b + 0.02, y - 0.1, t + 0.02), (0, 0.1 + (y - 0.1) / 2 + 0.005, 0), "folie"))
    return teile


def palettenstapel(n=5, b=1.2, t=0.8):
    teile = []
    for i in range(n):
        for obj in palette(b, t, einfach=True):
            obj.matrix_world = Matrix.Translation(G(0, i * 0.146, 0)) @ Matrix.Rotation(
                math.radians((i % 2) * 2.0 - 1.0), 4, "Z") @ obj.matrix_world
            teile.append(obj)
    return teile


def regal_feld(breite, hoehe, tiefe, ebenen, links=True, rechts=True, deck=True):
    """Ein Feld eines Palettenregals, entlang x, Vorderseite +z. Blaue Stuetzen,
    orange Traversen. links/rechts: ob die Stuetzenrahmen dazugehoeren."""
    teile = []
    for sx, an in ((-1, links), (1, rechts)):
        if not an:
            continue
        x = sx * breite / 2
        for sz in (-1, 1):
            teile.append(kasten("stuetze", (0.07, hoehe, 0.07), (x, hoehe / 2, sz * (tiefe / 2 - 0.035)),
                                "blau_stahl", unten=False))
        d = tiefe / 2 - 0.07
        y = 0.15
        k = 0
        while y + 0.7 < hoehe:
            teile.append(stab("diagonale", (x, y, -d if k % 2 == 0 else d), (x, y + 0.7, d if k % 2 == 0 else -d),
                              0.025, "blau_stahl"))
            y += 0.7
            k += 1
    for y in ebenen:
        for sz in (-1, 1):
            teile.append(kasten("traverse", (breite - 0.07, 0.1, 0.05), (0, y - 0.05, sz * (tiefe / 2 - 0.035)),
                                "regal_orange"))
        if deck:
            teile.append(kasten("fachboden", (breite - 0.07, 0.02, tiefe - 0.12), (0, y - 0.01, 0), "gitterboden"))
    return teile


def pflanze(groesse=1.0, topf="topf_weiss", stil="busch"):
    s = groesse
    teile = [
        zylinder("topf", 0.14 * s, 0.3 * s, (0, 0, 0), topf, seiten=10, radius_oben=0.17 * s),
        zylinder("erde", 0.155 * s, 0.01, (0, 0.29 * s, 0), "erde_l", seiten=10),
    ]
    if stil == "busch":
        teile += [
            kugel("blatt_a", 0.24 * s, (0.0, 0.52 * s, 0.0), "pflanze_l", stauchung=0.85, ringe=5, seiten=8),
            kugel("blatt_b", 0.17 * s, (0.13 * s, 0.7 * s, 0.05 * s), "pflanze_d_l", ringe=4, seiten=7),
            kugel("blatt_c", 0.15 * s, (-0.1 * s, 0.74 * s, -0.07 * s), "pflanze_l", ringe=4, seiten=7),
        ]
    else:
        teile.append(zylinder("stamm", 0.025 * s, 0.75 * s, (0, 0.29 * s, 0), "holz_stamm", seiten=5))
        for i, (dx, dz, r, m) in enumerate(((0, 0, 0.24, "pflanze_l"), (0.17, 0.06, 0.17, "pflanze_d_l"),
                                             (-0.15, 0.09, 0.16, "pflanze_l"), (0.03, -0.16, 0.16, "pflanze_d_l"),
                                             (-0.05, 0.02, 0.15, "pflanze_d_l"))):
            teile.append(kugel("wedel_%d" % i, r * s, (dx * s, (1.05 + 0.13 * (i % 2) + 0.1 * (i // 4)) * s, dz * s),
                               m, stauchung=0.62, ringe=4, seiten=7))
    return teile


def teppich(b, t, mat, rand=None):
    teile = [kasten("teppich", (b, 0.012, t), (0, 0.006, 0), mat, rund=0.005, segmente=1)]
    if rand:
        teile += rahmen_markierung(0, 0, b - 0.16, t - 0.16, rand, d=0.04, y=0.0135)
    return teile


# ==============================================================================
# HALLENGERAET
# ==============================================================================

def rollcontainer(rng, fuellung=3):
    """Rollbehaelter mit Gitter an drei Seiten, vorn offen."""
    b, t, h = 0.72, 0.8, 1.55
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(liegender_zylinder("rolle", 0.05, 0.04, (sx * 0.28, 0.05, sz * 0.32), "x",
                                            "reifen", seiten=6))
    teile.append(kasten("boden", (b, 0.05, t), (0, 0.125, 0), "metall_hell_l"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("pfosten", (0.03, h - 0.15, 0.03),
                                (sx * (b / 2 - 0.015), 0.15 + (h - 0.15) / 2, sz * (t / 2 - 0.015)),
                                "metall_hell_l"))
    for y in (0.5, 0.9, 1.3, h - 0.02):
        for sx in (-1, 1):
            teile.append(kasten("draht", (0.015, 0.015, t - 0.03), (sx * (b / 2 - 0.015), y, 0), "metall_hell_l"))
        teile.append(kasten("draht", (b - 0.03, 0.015, 0.015), (0, y, -(t / 2 - 0.015)), "metall_hell_l"))
    for sx in (-1, 1):
        for zz in (-0.13, 0.13):
            teile.append(kasten("draht_s", (0.012, h - 0.2, 0.012),
                                (sx * (b / 2 - 0.015), 0.15 + (h - 0.2) / 2, zz), "metall_hell_l"))
    y = 0.15
    for i in range(fuellung):
        hh = rng.choice((0.25, 0.3, 0.35))
        teile += karton(0.55 - 0.05 * (i % 2), hh, 0.6 - 0.04 * i, rng.choice(_KARTON_TOENE),
                        x=rng.uniform(-0.03, 0.03), y=y, z=rng.uniform(-0.03, 0.03))
        y += hh
    return teile


def feuerloescher_staender():
    return [
        kasten("fuss", (0.36, 0.03, 0.3), (0, 0.015, 0), "rot_signal", rund=0.008, segmente=1),
        kasten("saeule", (0.06, 1.55, 0.04), (0, 0.8, -0.1), "rot_signal"),
        zylinder("flasche", 0.08, 0.5, (0, 0.03, 0.0), "rot_signal", seiten=10),
        kugel("kopf", 0.08, (0, 0.53, 0.0), "rot_signal", stauchung=0.7, ringe=4, seiten=8),
        kasten("ventil", (0.05, 0.08, 0.05), (0, 0.62, 0.0), "kunststoff_schwarz"),
        kasten("griff", (0.14, 0.025, 0.03), (0.04, 0.66, 0.0), "kunststoff_schwarz"),
        kasten("etikett", (0.1, 0.14, 0.01), (0, 0.3, 0.08), "weiss_l"),
        kasten("schild", (0.3, 0.3, 0.02), (0, 1.35, -0.07), "rot_signal", rund=0.01, segmente=1),
        kasten("symbol", (0.07, 0.16, 0.006), (0, 1.35, -0.058), "weiss_l"),
        kasten("symbol_k", (0.1, 0.03, 0.006), (0, 1.44, -0.058), "weiss_l"),
    ]


def warnschild_staender(symbol="ausruf"):
    s = 0.46
    y0 = 1.0
    h = s * 0.866
    teile = [
        zylinder("fuss", 0.2, 0.05, (0, 0, 0), "kunststoff_schwarz", seiten=10),
        kasten("stiel", (0.04, y0 + 0.05, 0.04), (0, (y0 + 0.05) / 2, -0.03), "metall_hell_l"),
        prisma("rand", [(-s / 2, y0), (s / 2, y0), (0, y0 + h)], -0.01, 0.005, "schwarz"),
        prisma("feld", [(-s / 2 + 0.05, y0 + 0.03), (s / 2 - 0.05, y0 + 0.03), (0, y0 + h - 0.06)],
               0.005, 0.012, "gelb"),
    ]
    if symbol == "ausruf":
        teile.append(kasten("strich", (0.03, 0.12, 0.006), (0, y0 + 0.2, 0.014), "schwarz"))
        teile.append(kasten("punkt", (0.03, 0.03, 0.006), (0, y0 + 0.1, 0.014), "schwarz"))
    else:
        teile.append(kasten("koerper", (0.1, 0.07, 0.006), (-0.01, y0 + 0.12, 0.014), "schwarz"))
        teile.append(kasten("mast", (0.015, 0.14, 0.006), (0.055, y0 + 0.15, 0.014), "schwarz"))
        teile.append(kasten("gabel", (0.05, 0.012, 0.006), (0.08, y0 + 0.09, 0.014), "schwarz"))
    return teile


def poller(h=0.8):
    teile = [zylinder("poller", 0.07, h, (0, 0, 0), "gelb", seiten=8)]
    for y in (h * 0.45, h * 0.75):
        teile.append(zylinder("band", 0.073, 0.07, (0, y, 0), "schwarz", seiten=8, deckel=False))
    teile.append(kugel("kappe", 0.07, (0, h, 0), "gelb", stauchung=0.5, ringe=3, seiten=8))
    return teile


def leitkegel():
    return [
        kasten("fuss", (0.3, 0.03, 0.3), (0, 0.015, 0), "orange_kegel"),
        zylinder("kegel", 0.12, 0.5, (0, 0.03, 0), "orange_kegel", seiten=8, radius_oben=0.02),
        zylinder("band", 0.089, 0.08, (0, 0.21, 0), "weiss_l", seiten=8, radius_oben=0.075, deckel=False),
    ]


def hubwagen():
    """Handhubwagen, Gabeln nach +z."""
    teile = []
    for sx in (-1, 1):
        teile.append(kasten("gabel", (0.16, 0.05, 1.1), (sx * 0.2, 0.06, 0.1), "rot_signal"))
        teile.append(liegender_zylinder("rolle", 0.035, 0.08, (sx * 0.2, 0.035, 0.55), "x", "reifen", seiten=6))
    teile.append(kasten("koerper", (0.6, 0.2, 0.2), (0, 0.18, -0.52), "rot_signal", rund=0.02, segmente=1))
    teile.append(zylinder("pumpe", 0.05, 0.3, (0, 0.2, -0.55), "metall_dunkel_l", seiten=8))
    teile.append(liegender_zylinder("lenkrad", 0.08, 0.14, (0, 0.08, -0.55), "x", "reifen", seiten=8))
    teile.append(stab("deichsel", (0, 0.45, -0.58), (0, 1.15, -0.78), 0.035, "metall_dunkel_l"))
    teile.append(kasten("griff", (0.3, 0.05, 0.05), (0, 1.17, -0.79), "kunststoff_schwarz", rund=0.015, segmente=1))
    return teile


def stretchrolle(liegend=False):
    if liegend:
        return [liegender_zylinder("rolle", 0.09, 0.5, (0, 0.09, 0), "x", "folie_rolle", seiten=10),
                liegender_zylinder("kern", 0.04, 0.54, (0, 0.09, 0), "x", "karton", seiten=6)]
    return [zylinder("rolle", 0.09, 0.5, (0, 0, 0), "folie_rolle", seiten=10),
            zylinder("kern", 0.04, 0.54, (0, 0, 0), "karton", seiten=6)]


def wickelmaschine():
    """Palettenwickler: Drehteller, Mast hinten (lokal -z)."""
    return [
        zylinder("teller", 0.78, 0.1, (0, 0, 0), "metall_hell_l", seiten=16),
        zylinder("ring", 0.8, 0.03, (0, 0.035, 0), "gelb", seiten=16, deckel=False),
        kasten("sockel", (0.55, 0.12, 0.42), (0, 0.06, -1.0), "gelb", rund=0.02, segmente=1),
        kasten("mast", (0.16, 2.0, 0.16), (0, 1.12, -1.0), "metall_dunkel_l"),
        kasten("schlitten", (0.34, 0.3, 0.22), (0, 1.15, -0.85), "gelb", rund=0.02, segmente=1),
        zylinder("filmrolle", 0.07, 0.36, (0.0, 0.98, -0.7), "folie_rolle", seiten=8),
        kasten("pult", (0.22, 0.3, 0.12), (0, 1.55, -0.87), "kunststoff_schwarz"),
        kasten("knopf", (0.05, 0.05, 0.02), (0, 1.58, -0.8), "rot_signal"),
    ]


def stehpult():
    teile = [
        kasten("fuss", (0.6, 0.03, 0.45), (0, 0.015, 0), "metall_dunkel_l"),
        kasten("saeule", (0.08, 1.0, 0.08), (0, 0.52, -0.05), "metall_dunkel_l"),
        kasten("platte", (0.8, 0.04, 0.55), (0, 1.04, 0), "holz_tisch", rund=0.01, segmente=1),
        kasten("laptop", (0.34, 0.02, 0.24), (-0.1, 1.07, 0.05), "metall_hell_l"),
        kasten("scanner", (0.06, 0.05, 0.14), (0.25, 1.085, 0.05), "kunststoff_schwarz"),
        kasten("scanner_kopf", (0.08, 0.06, 0.06), (0.25, 1.1, -0.04), "gelb"),
    ]
    schirm = [kasten("schirm", (0.34, 0.22, 0.015), (0, 0.11, 0), "metall_hell_l"),
              kasten("anzeige", (0.3, 0.18, 0.004), (0, 0.11, 0.009), "bildschirm_t")]
    for o in schirm:
        o.matrix_world = Matrix.Translation(G(-0.1, 1.08, -0.065)) @ Matrix.Rotation(math.radians(-12), 4, "X")
    teile += schirm
    teile += karton(0.3, 0.2, 0.25, "karton_hell", x=0.2, y=1.06, z=-0.12)
    return teile


def sackkarre():
    return [
        stab("holm_l", (-0.18, 0.02, 0.0), (-0.16, 1.25, -0.22), 0.03, "rot_signal"),
        stab("holm_r", (0.18, 0.02, 0.0), (0.16, 1.25, -0.22), 0.03, "rot_signal"),
        kasten("schaufel", (0.42, 0.015, 0.22), (0, 0.008, 0.1), "metall_dunkel_l"),
        kasten("quer", (0.36, 0.03, 0.03), (0, 0.6, -0.1), "rot_signal"),
        kasten("griff", (0.4, 0.035, 0.035), (0, 1.25, -0.22), "kunststoff_schwarz"),
        liegender_zylinder("rad_l", 0.12, 0.06, (-0.25, 0.12, -0.08), "x", "reifen", seiten=8),
        liegender_zylinder("rad_r", 0.12, 0.06, (0.25, 0.12, -0.08), "x", "reifen", seiten=8),
    ]


def gitterbox(rng, voll=True):
    b, t, h = 1.2, 0.8, 0.9
    teile = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("fuss", (0.1, 0.1, 0.1), (sx * (b / 2 - 0.05), 0.05, sz * (t / 2 - 0.05)),
                                "metall_dunkel_l"))
            teile.append(kasten("ecke", (0.04, h - 0.1, 0.04),
                                (sx * (b / 2 - 0.02), 0.1 + (h - 0.1) / 2, sz * (t / 2 - 0.02)), "metall_hell_l"))
    teile.append(kasten("boden", (b, 0.03, t), (0, 0.115, 0), "metall_dunkel_l"))
    for y in (0.4, 0.65, h - 0.02):
        for sz in (-1, 1):
            teile.append(kasten("holm", (b - 0.04, 0.02, 0.02), (0, y, sz * (t / 2 - 0.02)), "metall_hell_l"))
        for sx in (-1, 1):
            teile.append(kasten("holm", (0.02, 0.02, t - 0.04), (sx * (b / 2 - 0.02), y, 0), "metall_hell_l"))
    for i in range(1, 6):
        x = -b / 2 + i * b / 6
        teile.append(kasten("stab", (0.012, h - 0.15, 0.012), (x, 0.13 + (h - 0.15) / 2, t / 2 - 0.02),
                            "metall_hell_l"))
    if voll:
        teile.append(kasten("inhalt", (b - 0.1, 0.62, t - 0.1), (0, 0.13 + 0.31, 0), "karton_hell"))
        for i in range(3):
            teile += karton(0.35, 0.22, 0.3, rng.choice(_KARTON_TOENE), x=-0.35 + i * 0.36, y=0.75,
                            z=rng.uniform(-0.1, 0.1))
    return teile


def muelltonnen():
    teile = []
    for i, mat in enumerate(("tuerkis", "gelb", "stoff_dunkel_l")):
        x = (i - 1) * 0.56
        teile.append(kasten("tonne", (0.5, 0.88, 0.55), (x, 0.44, 0), mat, rund=0.03, segmente=1))
        teile.append(kasten("deckel", (0.53, 0.05, 0.6), (x, 0.905, -0.01), "kunststoff_schwarz",
                            rund=0.015, segmente=1))
        teile.append(kasten("griff", (0.3, 0.04, 0.04), (x, 0.8, 0.29), "kunststoff_schwarz"))
    return teile


def rollleiter():
    teile = []
    for sx in (-1, 1):
        x = sx * 0.3
        teile.append(stab("wange", (x, 0.05, 0.6), (x, 1.62, -0.35), 0.05, "gelb"))
        teile.append(kasten("hinten", (0.04, 1.6, 0.04), (x, 0.84, -0.5), "gelb"))
        teile.append(stab("handlauf", (x, 1.0, 0.45), (x, 2.2, -0.35), 0.03, "gelb"))
        teile.append(kasten("handlauf_o", (0.03, 0.03, 0.3), (x, 2.2, -0.5), "gelb"))
        teile.append(kasten("pfosten_o", (0.03, 0.6, 0.03), (x, 1.9, -0.63), "gelb"))
        for sz in (0.6, -0.5):
            teile.append(zylinder("rolle", 0.04, 0.05, (x, 0.0, sz), "reifen", seiten=6))
    for i in range(4):
        f = (i + 1) / 5.0
        teile.append(kasten("stufe", (0.58, 0.03, 0.2), (0, 0.05 + f * 1.57, 0.6 - f * 0.95), "gitterboden"))
    teile.append(kasten("podest", (0.58, 0.04, 0.4), (0, 1.62, -0.45), "gitterboden"))
    return teile


def wand_erste_hilfe():
    """Erste-Hilfe-Kasten an der Wand (Rueckseite bei lokal z = 0)."""
    return [
        kasten("kasten", (0.42, 0.34, 0.14), (0, 1.35, 0.07), "weiss_l", rund=0.015, segmente=1),
        kasten("feld", (0.2, 0.2, 0.01), (0, 1.35, 0.145), "gruen_schild"),
        kasten("kreuz_h", (0.12, 0.04, 0.006), (0, 1.35, 0.152), "weiss_l"),
        kasten("kreuz_v", (0.04, 0.12, 0.006), (0, 1.35, 0.152), "weiss_l"),
    ]


def wand_fluchtschild():
    return [
        kasten("schild", (0.44, 0.2, 0.02), (0, 1.95, 0.01), "gruen_schild", rund=0.006, segmente=1),
        kasten("pfeil", (0.18, 0.04, 0.006), (0.04, 1.95, 0.023), "weiss_l"),
        prisma("spitze", [(0.13, 1.9), (0.18, 1.95), (0.13, 2.0)], 0.02, 0.026, "weiss_l"),
        kasten("figur", (0.04, 0.1, 0.006), (-0.14, 1.95, 0.023), "weiss_l"),
    ]


def packtisch_klein(rng):
    """Beistell-Packtisch mit Papierrolle, Abroller und Zuschnitten."""
    teile = [kasten("platte", (1.2, 0.04, 0.6), (0, 0.88, 0), "holz_tisch", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.05, 0.86, 0.05), (sx * 0.55, 0.43, sz * 0.25), "metall_dunkel_l"))
    teile.append(kasten("ablage", (1.1, 0.02, 0.5), (0, 0.2, 0), "metall_dunkel_l"))
    teile.append(kasten("zuschnitte", (0.9, 0.12, 0.45), (0, 0.27, 0), "karton"))
    teile.append(stab("halter_l", (-0.55, 0.9, -0.25), (-0.55, 1.35, -0.25), 0.03, "metall_dunkel_l"))
    teile.append(stab("halter_r", (0.55, 0.9, -0.25), (0.55, 1.35, -0.25), 0.03, "metall_dunkel_l"))
    teile.append(liegender_zylinder("papierrolle", 0.1, 1.05, (0, 1.3, -0.25), "x", "karton_hell", seiten=10))
    teile.append(kasten("abroller", (0.1, 0.1, 0.22), (0.35, 0.95, 0.1), "rot_signal"))
    teile.append(zylinder("band", 0.06, 0.05, (0.35, 0.95, 0.05), "klebeband", seiten=8))
    teile += karton(0.3, 0.2, 0.28, rng.choice(_KARTON_TOENE), x=-0.3, y=0.9, z=0.08)
    return teile


def luftpolster_rolle():
    return [zylinder("rolle", 0.3, 1.1, (0, 0, 0), "folie_rolle", seiten=12),
            zylinder("kern", 0.07, 1.12, (0, 0, 0), "karton", seiten=6),
            zylinder("band", 0.305, 0.06, (0, 0.55, 0), "tuerkis", seiten=12, deckel=False)]


# ==============================================================================
# BUERO UND PAUSENRAUM
# ==============================================================================

def monitor(x=0.0, z=0.0, farbe="bildschirm_t", breite=0.55, y=0.75):
    return [
        kasten("mfuss", (0.2, 0.02, 0.14), (x, y + 0.01, z), "metall_dunkel_l"),
        kasten("mhals", (0.04, 0.22, 0.03), (x, y + 0.12, z - 0.04), "metall_dunkel_l"),
        kasten("mschirm", (breite, 0.33, 0.03), (x, y + 0.36, z - 0.02), "bildschirm", rund=0.008, segmente=1),
        kasten("manzeige", (breite - 0.05, 0.28, 0.004), (x, y + 0.36, z - 0.003), farbe),
    ]


def schreibtisch(farben=("bildschirm_t",), pflanze_klein=False):
    """Buerotisch 1,4 x 0,7, Sitzseite +z."""
    teile = [kasten("platte", (1.4, 0.035, 0.7), (0, 0.735, 0), "holz_tisch", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("wange", (0.05, 0.72, 0.62), (sx * 0.64, 0.36, 0), "weiss_l"))
    teile.append(kasten("blende", (1.23, 0.3, 0.02), (0, 0.55, -0.3), "weiss_l"))
    n = len(farben)
    for i, f in enumerate(farben):
        teile += monitor(x=(i - (n - 1) / 2) * 0.58, z=-0.12, farbe=f)
    teile.append(kasten("tastatur", (0.42, 0.02, 0.14), (0, 0.762, 0.14), "weiss_l"))
    teile.append(kasten("maus", (0.05, 0.02, 0.08), (0.3, 0.762, 0.15), "kunststoff_schwarz"))
    teile.append(zylinder("tasse", 0.04, 0.09, (-0.52, 0.752, 0.12), "tuerkis", seiten=8))
    if pflanze_klein:
        teile.append(zylinder("minitopf", 0.06, 0.1, (0.56, 0.752, -0.2), "topf_terra_l", seiten=8))
        teile.append(kugel("minipflanze", 0.09, (0.56, 0.92, -0.2), "pflanze_l", ringe=4, seiten=7))
    return teile


def buerostuhl(stoff="stoff_dunkel_l"):
    """Sitz blickt nach -z (zum Tisch); Lehne bei +z."""
    teile = [
        kasten("sitz", (0.48, 0.08, 0.46), (0, 0.48, 0), stoff, rund=0.03, segmente=1),
        kasten("lehne", (0.44, 0.5, 0.07), (0, 0.85, 0.22), stoff, rund=0.03, segmente=1),
        kasten("traeger", (0.06, 0.3, 0.04), (0, 0.55, 0.22), "metall_dunkel_l"),
        zylinder("saeule", 0.03, 0.36, (0, 0.08, 0), "metall_dunkel_l", seiten=6),
    ]
    for sx in (-1, 1):
        teile.append(kasten("armlehne", (0.05, 0.03, 0.28), (sx * 0.26, 0.66, 0.02), "kunststoff_schwarz"))
        teile.append(kasten("armstuetze", (0.03, 0.14, 0.03), (sx * 0.26, 0.58, 0.08), "kunststoff_schwarz"))
    for i in range(5):
        a = math.radians(90 + i * 72)
        ex, ez = math.cos(a) * 0.3, math.sin(a) * 0.3
        teile.append(stab("fuss", (0, 0.08, 0), (ex, 0.05, ez), 0.035, "metall_dunkel_l"))
        teile.append(kasten("rolle", (0.05, 0.04, 0.05), (ex, 0.02, ez), "kunststoff_schwarz"))
    return teile


def whiteboard():
    teile = [
        kasten("tafel", (1.6, 0.9, 0.03), (0, 1.3, 0), "whiteboard_weiss", rund=0.008, segmente=1),
        kasten("ablage", (1.2, 0.03, 0.08), (0, 0.84, 0.04), "metall_hell_l"),
    ]
    for sx in (-1, 1):
        teile.append(kasten("bein", (0.04, 1.8, 0.04), (sx * 0.82, 0.9, 0), "metall_hell_l"))
        teile.append(kasten("fuss", (0.06, 0.04, 0.5), (sx * 0.82, 0.02, 0), "metall_hell_l"))
    farben = ("notiz_gelb", "notiz_rosa", "notiz_blau", "notiz_gelb", "tuerkis", "notiz_rosa", "notiz_gelb")
    for i, f in enumerate(farben):
        x = -0.62 + (i % 4) * 0.13
        y = 1.58 - (i // 4) * 0.14 - 0.02 * (i % 2)
        teile.append(kasten("zettel", (0.1, 0.1, 0.004), (x, y, 0.017), f))
    # Balkendiagramm und Kurve als Formen
    for i, h in enumerate((0.12, 0.2, 0.17, 0.3)):
        teile.append(kasten("balken", (0.07, h, 0.004), (0.15 + i * 0.1, 1.0 + h / 2, 0.017),
                            "tuerkis" if i == 3 else "bildschirm_b"))
    teile.append(kasten("linie", (0.5, 0.012, 0.004), (0.3, 1.5, 0.017), "rot_signal"))
    teile.append(kasten("linie2", (0.35, 0.012, 0.004), (0.25, 1.62, 0.017), "stoff_dunkel_l"))
    teile.append(kasten("stift", (0.12, 0.02, 0.02), (-0.3, 0.865, 0.04), "rot_signal"))
    return teile


def wasserspender():
    return [
        kasten("korpus", (0.32, 0.95, 0.32), (0, 0.475, 0), "weiss_l", rund=0.02, segmente=1),
        kasten("mulde", (0.2, 0.2, 0.02), (0, 0.72, 0.16), "metall_dunkel_l"),
        zylinder("flasche", 0.13, 0.42, (0, 0.95, 0), "notiz_blau", seiten=10, rund=0.02),
        zylinder("becher", 0.035, 0.08, (0.1, 0.95, 0.12), "weiss_l", seiten=6),
    ]


def sideboard_drucker():
    teile = [kasten("korpus", (1.2, 0.7, 0.45), (0, 0.35, 0), "weiss_l", rund=0.015, segmente=1)]
    for i in range(3):
        teile.append(kasten("front", (0.38, 0.62, 0.01), (-0.4 + i * 0.4, 0.35, 0.228),
                            "tuerkis" if i == 1 else "weiss_l"))
        teile.append(kasten("griff", (0.12, 0.02, 0.02), (-0.4 + i * 0.4, 0.6, 0.24), "metall_dunkel_l"))
    teile.append(kasten("drucker", (0.5, 0.26, 0.38), (-0.25, 0.83, 0), "stoff_grau_l", rund=0.02, segmente=1))
    teile.append(kasten("papier", (0.3, 0.02, 0.2), (-0.25, 0.97, -0.05), "weiss_l"))
    teile.append(kasten("ordner1", (0.07, 0.3, 0.26), (0.25, 0.85, 0), "bildschirm_b"))
    teile.append(kasten("ordner2", (0.07, 0.3, 0.26), (0.33, 0.85, 0), "stoff_senf_l"))
    teile.append(kasten("ordner3", (0.07, 0.3, 0.26), (0.41, 0.85, 0), "tuerkis"))
    return teile


def musterregal(rng):
    """Niedriges Regal mit Musterkartons der vier Shops."""
    b, h, t = 1.8, 1.1, 0.4
    teile = []
    for sx in (-1, 1):
        teile.append(kasten("seite", (0.03, h, t), (sx * (b / 2 - 0.015), h / 2, 0), "holz_tisch"))
    for y in (0.02, 0.55, h - 0.02):
        teile.append(kasten("boden", (b - 0.06, 0.03, t), (0, y, 0), "holz_tisch"))
    toene = ("bildschirm_t", "bildschirm_o", "bildschirm_p", "bildschirm_b")
    for ebene, y in enumerate((0.035, 0.565)):
        x = -b / 2 + 0.1
        i = 0
        while x < b / 2 - 0.35:
            w = rng.choice((0.26, 0.3, 0.34))
            hh = rng.choice((0.28, 0.34, 0.4))
            teile.append(kasten("muster", (w, hh, 0.3), (x + w / 2, y + hh / 2, 0), rng.choice(_KARTON_TOENE)))
            teile.append(kasten("logo", (0.1, 0.1, 0.004), (x + w / 2, y + hh / 2, 0.152),
                                toene[(i + ebene) % 4]))
            x += w + 0.06
            i += 1
    return teile


def glaswand(laenge, hoehe=2.3):
    """Glastrennwand entlang z, Pfosten bei den Enden und in der Mitte."""
    teile = [kasten("glas", (0.02, hoehe - 0.1, laenge), (0, 0.05 + (hoehe - 0.1) / 2, 0), "folie")]
    for z in (-laenge / 2, 0.0, laenge / 2):
        teile.append(kasten("pfosten", (0.05, hoehe, 0.05), (0, hoehe / 2, z), "metall_dunkel_l"))
    teile.append(kasten("oben", (0.05, 0.05, laenge), (0, hoehe - 0.025, 0), "metall_dunkel_l"))
    teile.append(kasten("unten", (0.05, 0.05, laenge), (0, 0.025, 0), "metall_dunkel_l"))
    return teile


def kuechenzeile(b=2.6):
    """Kuechenzeile an der Wand (Rueckseite lokal -z bei z = -0,3)."""
    teile = [kasten("korpus", (b, 0.82, 0.56), (0, 0.45, 0), "weiss_l")]
    teile.append(kasten("sockel", (b - 0.04, 0.08, 0.5), (0, 0.04, -0.02), "metall_dunkel_l"))
    n = int(b / 0.6)
    for i in range(n):
        x = -b / 2 + 0.3 + i * (b / n) + (b / n - 0.6) / 2
        teile.append(kasten("front", (b / n - 0.02, 0.76, 0.02), (x, 0.46, 0.29), "tuerkis" if i % 2 else "weiss_l"))
        teile.append(kasten("griff", (0.16, 0.02, 0.02), (x, 0.78, 0.31), "metall_dunkel_l"))
    teile.append(kasten("platte", (b + 0.02, 0.04, 0.62), (0, 0.88, 0.02), "holz_tisch", rund=0.01, segmente=1))
    teile.append(kasten("spuele", (0.5, 0.012, 0.38), (-0.5, 0.905, 0.02), "metall_hell_l"))
    teile.append(stab("hahn", (-0.5, 0.9, -0.2), (-0.5, 1.15, -0.2), 0.025, "metall_hell_l"))
    teile.append(stab("hahn_b", (-0.5, 1.15, -0.2), (-0.5, 1.13, -0.06), 0.025, "metall_hell_l"))
    # Kaffeemaschine
    kx = 0.55
    teile.append(kasten("kaffee_korpus", (0.3, 0.42, 0.36), (kx, 1.11, -0.05), "kunststoff_schwarz",
                        rund=0.02, segmente=1))
    teile.append(kasten("kaffee_blende", (0.22, 0.1, 0.02), (kx, 1.24, 0.14), "metall_hell_l"))
    teile.append(kasten("kaffee_anzeige", (0.12, 0.05, 0.006), (kx, 1.24, 0.152), "bildschirm_t"))
    teile.append(zylinder("tasse_k", 0.04, 0.08, (kx, 0.9, 0.06), "weiss_l", seiten=8))
    teile.append(zylinder("kessel", 0.08, 0.2, (0.95, 0.9, 0.0), "metall_hell_l", seiten=8, radius_oben=0.06))
    for i, f in enumerate(("tuerkis", "rot_signal", "stoff_senf_l")):
        teile.append(zylinder("tasse", 0.035, 0.08, (0.05 + i * 0.1, 0.9, 0.12), f, seiten=6))
    # Oberschraenke (an der Wand, Unterkante 1,45)
    teile.append(kasten("ober", (b - 0.8, 0.6, 0.34), (-0.4, 1.75, -0.11), "weiss_l", rund=0.01, segmente=1))
    for i in range(3):
        teile.append(kasten("ober_front", (0.58, 0.56, 0.01), (-1.0 + i * 0.6, 1.75, 0.065), "weiss_l"))
        teile.append(kasten("ober_griff", (0.14, 0.02, 0.02), (-1.0 + i * 0.6, 1.5, 0.08), "metall_dunkel_l"))
    return teile


def kuehlschrank():
    return [
        kasten("korpus", (0.62, 1.8, 0.62), (0, 0.9, 0), "metall_hell_l", rund=0.03, segmente=1),
        kasten("fuge", (0.6, 0.012, 0.01), (0, 1.15, 0.312), "metall_dunkel_l"),
        kasten("griff1", (0.03, 0.4, 0.03), (0.24, 1.45, 0.33), "metall_dunkel_l"),
        kasten("griff2", (0.03, 0.3, 0.03), (0.24, 0.95, 0.33), "metall_dunkel_l"),
        kasten("magnet1", (0.08, 0.1, 0.006), (-0.1, 1.5, 0.313), "notiz_gelb"),
        kasten("magnet2", (0.1, 0.07, 0.006), (-0.12, 1.35, 0.313), "notiz_rosa"),
    ]


def getraenkeautomat():
    teile = [
        kasten("korpus", (0.9, 1.85, 0.72), (0, 0.925, 0), "tuerkis", rund=0.03, segmente=1),
        kasten("fenster", (0.56, 1.25, 0.01), (-0.1, 1.1, 0.362), "stoff_dunkel_l"),
        kasten("panel", (0.18, 0.6, 0.01), (0.3, 1.3, 0.362), "kunststoff_schwarz"),
        kasten("schlitz", (0.5, 0.12, 0.02), (-0.1, 0.3, 0.362), "kunststoff_schwarz"),
    ]
    farben = ("rot_signal", "notiz_gelb", "gruen_schild", "notiz_blau")
    for r in range(4):
        teile.append(kasten("reihe", (0.5, 0.14, 0.006), (-0.1, 0.65 + r * 0.29, 0.37), farben[r]))
    for k in range(3):
        teile.append(kasten("taste", (0.1, 0.05, 0.006), (0.3, 1.45 - k * 0.1, 0.37), "weiss_l"))
    return teile


def spinde(anzahl=4):
    b = 0.42 * anzahl
    teile = [kasten("korpus", (b, 1.8, 0.45), (0, 0.9, 0), "metall_hell_l")]
    for i in range(anzahl):
        x = -b / 2 + 0.21 + i * 0.42
        teile.append(kasten("tuer", (0.39, 1.7, 0.01), (x, 0.92, 0.228), "metall_dunkel_l" if i % 2 == 0 else "stahl_blau"))
        teile.append(kasten("schlitze", (0.2, 0.08, 0.006), (x, 1.6, 0.236), "metall_dunkel_l"))
        teile.append(kasten("griff", (0.03, 0.12, 0.02), (x + 0.13, 1.0, 0.24), "metall_hell_l"))
    return teile


def sitzbank(b=1.4):
    teile = [kasten("sitz", (b, 0.05, 0.36), (0, 0.44, 0), "holz_tisch", rund=0.01, segmente=1)]
    for sx in (-1, 1):
        teile.append(kasten("bein", (0.05, 0.42, 0.32), (sx * (b / 2 - 0.1), 0.21, 0), "metall_dunkel_l"))
    return teile


def kicker():
    teile = [
        kasten("kasten", (1.25, 0.24, 0.72), (0, 0.78, 0), "holz_tisch", rund=0.015, segmente=1),
        kasten("feld", (1.13, 0.01, 0.62), (0, 0.905, 0), "kicker_gruen"),
        kasten("mittellinie", (0.02, 0.004, 0.6), (0, 0.912, 0), "weiss_l"),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.07, 0.66, 0.07), (sx * 0.55, 0.33, sz * 0.3), "stoff_dunkel_l"))
        teile.append(kasten("tor", (0.03, 0.08, 0.2), (sx * 0.6, 0.95, 0), "weiss_l"))
    for i in range(8):
        x = -0.525 + i * 0.15
        rot = i in (0, 1, 3, 5)
        teile.append(liegender_zylinder("stange", 0.012, 1.0, (x, 1.0, 0), "z", "metall_hell_l", seiten=5))
        seite = 1 if i % 2 == 0 else -1
        teile.append(kasten("griff", (0.045, 0.045, 0.1), (x, 1.0, seite * 0.55), "kunststoff_schwarz"))
        for k in (-1, 1):
            teile.append(kasten("figur", (0.035, 0.1, 0.05), (x, 0.96, k * 0.13),
                                "rot_signal" if rot else "bildschirm_b"))
    teile.append(kugel("ball", 0.02, (0.1, 0.93, 0.05), "weiss_l", ringe=3, seiten=6))
    return teile


def sofa(stoff="stoff_tuerkis", b=2.0):
    """Sitzseite +z."""
    teile = [
        kasten("basis", (b, 0.24, 0.85), (0, 0.18, 0), stoff, rund=0.04, segmente=1),
        kasten("lehne", (b, 0.45, 0.22), (0, 0.55, -0.32), stoff, rund=0.06, segmente=1),
    ]
    for sx in (-1, 1):
        teile.append(kasten("arm", (0.2, 0.34, 0.85), (sx * (b / 2 - 0.1), 0.5, 0), stoff, rund=0.05, segmente=1))
        teile.append(kasten("kissen", ((b - 0.4) / 2 - 0.02, 0.14, 0.62), (sx * (b - 0.4) / 4, 0.37, 0.08),
                            stoff, rund=0.05, segmente=1))
        teile.append(kasten("fuss", (0.06, 0.06, 0.06), (sx * (b / 2 - 0.1), 0.03, 0.3), "holz_stamm"))
    teile.append(kugel("deko1", 0.16, (-0.55, 0.62, -0.12), "stoff_senf_l", stauchung=0.7, ringe=4, seiten=7))
    teile.append(kugel("deko2", 0.15, (0.6, 0.62, -0.12), "stoff_koralle_l", stauchung=0.7, ringe=4, seiten=7))
    return teile


def couchtisch():
    teile = [kasten("platte", (1.0, 0.04, 0.55), (0, 0.42, 0), "holz_tisch", rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.04, 0.4, 0.04), (sx * 0.44, 0.2, sz * 0.22), "metall_dunkel_l"))
    teile.append(kasten("heft", (0.24, 0.015, 0.3), (-0.2, 0.448, 0.02), "bildschirm_o"))
    teile.append(zylinder("becher", 0.04, 0.09, (0.25, 0.44, -0.05), "weiss_l", seiten=8))
    teile.append(kasten("controller", (0.14, 0.03, 0.08), (0.1, 0.455, 0.12), "kunststoff_schwarz"))
    return teile


def tisch(b=1.2, t=0.8):
    teile = [kasten("platte", (b, 0.04, t), (0, 0.74, 0), "holz_tisch", rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.05, 0.72, 0.05), (sx * (b / 2 - 0.08), 0.36, sz * (t / 2 - 0.08)),
                                "metall_dunkel_l"))
    teile.append(zylinder("vase", 0.05, 0.14, (0, 0.76, 0), "topf_weiss", seiten=8))
    teile.append(kugel("strauss", 0.08, (0, 0.95, 0), "stoff_koralle_l", ringe=4, seiten=6))
    return teile


def stuhl(farbe="stoff_senf_l"):
    """Sitzseite +z, Lehne bei -z."""
    teile = [kasten("sitz", (0.42, 0.04, 0.42), (0, 0.46, 0), farbe, rund=0.012, segmente=1),
             kasten("lehne", (0.42, 0.3, 0.04), (0, 0.72, -0.19), farbe, rund=0.012, segmente=1)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.03, 0.44, 0.03), (sx * 0.18, 0.22, sz * 0.18), "metall_dunkel_l"))
    return teile


# ==============================================================================
# FAHRZEUG UND AUSSENANLAGE
# ==============================================================================

def transporter(teil="ganz"):
    """Kastenwagen, Heck bei lokal z = 0 (blickt nach +z), Aufbau nach -z.
    teil: 'ganz', 'heck' (Heck bis z = -2,4) oder 'front' (z -2,6 .. -4,5)."""
    w = 1.9
    teile = []
    if teil in ("ganz", "heck"):
        z0 = -2.4 if teil == "heck" else -3.2
        L = -z0
        teile.append(kasten("aufbau", (w, 1.62, L), (0, 0.38 + 0.81, z0 / 2), "fahrzeug_weiss", rund=0.07,
                            segmente=1))
        teile.append(kasten("streifen_l", (0.006, 0.14, L - 0.3), (-w / 2 - 0.003, 1.1, z0 / 2 - 0.1), "tuerkis"))
        teile.append(kasten("streifen_r", (0.006, 0.14, L - 0.3), (w / 2 + 0.003, 1.1, z0 / 2 - 0.1), "tuerkis"))
        teile.append(kasten("stossfaenger", (w + 0.04, 0.16, 0.16), (0, 0.36, -0.02), "kunststoff_schwarz"))
        for sx in (-1, 1):
            teile.append(kasten("tuer", (w / 2 - 0.08, 1.45, 0.012), (sx * (w / 4), 1.17, 0.006), "fahrzeug_weiss"))
            teile.append(kasten("heckfenster", (0.55, 0.36, 0.01), (sx * (w / 4), 1.62, 0.016), "bildschirm"))
            teile.append(kasten("leuchte", (0.1, 0.4, 0.06), (sx * (w / 2 - 0.06), 0.72, 0.0), "rot_signal"))
            teile.append(kasten("blinker", (0.1, 0.1, 0.061), (sx * (w / 2 - 0.06), 0.47, 0.0), "gelb"))
            teile.append(liegender_zylinder("rad", 0.33, 0.24, (sx * (w / 2 - 0.1), 0.33, -0.75), "x",
                                            "reifen", seiten=8))
            teile.append(liegender_zylinder("felge", 0.16, 0.25, (sx * (w / 2 - 0.1), 0.33, -0.75), "x",
                                            "metall_hell_l", seiten=6))
        teile.append(kasten("fuge", (0.012, 1.45, 0.014), (0, 1.17, 0.007), "metall_dunkel_l"))
        teile.append(kasten("kennzeichen", (0.5, 0.11, 0.01), (0, 0.5, 0.07), "weiss_l"))
    if teil in ("ganz", "front"):
        zf = -3.2
        if teil == "front":
            # gleicher Anker wie 'heck': Wand-Aussenseite bei z = -2,6
            teile.append(kasten("aufbau_rest", (w, 1.62, 0.6), (0, 0.38 + 0.81, -2.9),
                                "fahrzeug_weiss", rund=0.07, segmente=1))
        teile.append(kasten("kabine", (w - 0.04, 1.1, 0.9), (0, 0.9 + 0.1, zf - 0.45), "fahrzeug_weiss",
                            rund=0.1, segmente=1))
        teile.append(kasten("haube", (w - 0.06, 0.55, 0.55), (0, 0.72, zf - 1.1), "fahrzeug_weiss",
                            rund=0.1, segmente=1))
        teile.append(kasten("scheibe", (w - 0.26, 0.42, 0.012), (0, 1.26, zf - 0.906), "bildschirm"))
        teile.append(kasten("grill", (1.2, 0.2, 0.02), (0, 0.72, zf - 1.38), "kunststoff_schwarz"))
        teile.append(kasten("stoss_v", (w + 0.02, 0.16, 0.14), (0, 0.38, zf - 1.36), "kunststoff_schwarz"))
        for sx in (-1, 1):
            teile.append(kasten("scheinwerfer", (0.26, 0.1, 0.02), (sx * 0.72, 0.84, zf - 1.38), "lampe_licht"))
            teile.append(liegender_zylinder("rad_v", 0.33, 0.24, (sx * (w / 2 - 0.1), 0.33, zf - 0.95), "x",
                                            "reifen", seiten=8))
            teile.append(liegender_zylinder("felge_v", 0.16, 0.25, (sx * (w / 2 - 0.1), 0.33, zf - 0.95), "x",
                                            "metall_hell_l", seiten=6))
            teile.append(kasten("spiegel", (0.08, 0.14, 0.1), (sx * (w / 2 + 0.05), 1.3, zf - 0.7),
                                "kunststoff_schwarz"))
            teile.append(kasten("seitenfenster", (0.006, 0.4, 0.55), (sx * (w / 2 - 0.018), 1.3, zf - 0.45),
                                "bildschirm"))
    return teile


def rolltor(breite=2.3, hoehe=2.3):
    """Rolltor-Andeutung an einer Wand; Wandflaeche bei lokal z = 0, Tor blickt
    nach +z. Dunkle Oeffnung, Torblatt oben aufgerollt, gelb-schwarze Zargen."""
    teile = [kasten("oeffnung", (breite, 2.0, 0.004), (0, 1.0, 0.002), "aussen_dunkel")]
    teile.append(kasten("blatt", (breite, 0.1, 0.04), (0, 2.07, 0.02), "metall_hell_l"))
    teile.append(kasten("kasten", (breite + 0.3, 0.2, 0.3), (0, 2.22, 0.15), "metall_hell_l", rund=0.02,
                        segmente=1))
    teile.append(kasten("kasten_band", (breite + 0.304, 0.04, 0.302), (0, 2.22, 0.15), "tuerkis"))
    for sx in (-1, 1):
        x = sx * (breite / 2 + 0.07)
        teile.append(kasten("zarge", (0.12, hoehe - 0.18, 0.14), (x, (hoehe - 0.18) / 2 + 0.0, 0.07), "gelb"))
        for y in (0.25, 0.65, 1.05, 1.45, 1.85):
            teile.append(kasten("zarge_band", (0.124, 0.18, 0.144), (x, y, 0.07), "schwarz"))
        teile.append(kasten("puffer", (0.12, 0.22, 0.12), (sx * (breite / 2 + 0.24), 0.35, 0.06),
                            "kunststoff_schwarz", rund=0.015, segmente=1))
        teile.append(kasten("ampel", (0.12, 0.26, 0.08), (sx * (breite / 2 + 0.26), 1.55, 0.04),
                            "kunststoff_schwarz"))
        teile.append(kugel("ampel_l", 0.04, (sx * (breite / 2 + 0.26), 1.6, 0.08),
                           "gruen_schild" if sx > 0 else "rot_signal", ringe=3, seiten=6))
    return teile


def baum(rng, h=3.4, rad=1.1):
    teile = [zylinder("stamm", 0.12, h * 0.45, (0, 0, 0), "holz_stamm", seiten=6, radius_oben=0.08)]
    teile.append(kugel("krone", rad, (0, h * 0.62, 0), "pflanze_l", stauchung=0.9, ringe=5, seiten=8))
    teile.append(kugel("krone_b", rad * 0.7, (rad * 0.45, h * 0.78, rad * 0.2), "pflanze_d_l", ringe=4, seiten=7))
    teile.append(kugel("krone_c", rad * 0.6, (-rad * 0.4, h * 0.8, -rad * 0.25), "pflanze_l", ringe=4, seiten=7))
    return teile


def saeulenbaum(h=4.0, rad=0.8):
    return [zylinder("stamm", 0.1, 0.8, (0, 0, 0), "holz_stamm", seiten=6),
            kugel("krone", rad, (0, h * 0.55, 0), "pflanze_d_l", stauchung=2.2, ringe=5, seiten=8)]


def busch(rad=0.5, h=0.6):
    return [kugel("busch", rad, (0, h * 0.5, 0), "pflanze_l", stauchung=h / rad * 0.55, ringe=4, seiten=7),
            kugel("busch_b", rad * 0.65, (rad * 0.35, h * 0.65, rad * 0.1), "pflanze_d_l",
                  stauchung=h / rad * 0.55, ringe=3, seiten=6)]


def laterne(h=4.0):
    return [
        zylinder("mast", 0.06, h, (0, 0, 0), "metall_dunkel_l", seiten=6, radius_oben=0.045),
        zylinder("fuss", 0.12, 0.3, (0, 0, 0), "metall_dunkel_l", seiten=6),
        kasten("arm", (0.05, 0.05, 0.7), (0, h - 0.05, 0.33), "metall_dunkel_l"),
        kasten("kopf", (0.26, 0.1, 0.5), (0, h - 0.1, 0.62), "metall_dunkel_l", rund=0.02, segmente=1),
        kasten("licht", (0.2, 0.01, 0.42), (0, h - 0.155, 0.62), "lampe_licht"),
    ]


def zaunfeld(laenge=2.5, h=1.6):
    """Stabgitterzaun entlang x, Pfosten am linken Ende."""
    teile = [kasten("pfosten", (0.06, h + 0.05, 0.06), (-laenge / 2, (h + 0.05) / 2, 0), "metall_dunkel_l")]
    for y in (0.15, h - 0.08):
        teile.append(kasten("holm", (laenge, 0.04, 0.03), (0, y, 0), "metall_dunkel_l"))
    for i in range(1, 4):
        x = -laenge / 2 + i * laenge / 4
        teile.append(kasten("stab", (0.02, h - 0.1, 0.02), (x, 0.05 + (h - 0.1) / 2, 0), "metall_dunkel_l"))
    return teile


def fahrradstaender():
    teile = [kasten("schiene", (1.6, 0.04, 0.08), (0, 0.02, 0), "metall_dunkel_l")]
    for i in range(4):
        x = -0.6 + i * 0.4
        teile.append(stab("buegel_l", (x - 0.12, 0.0, 0), (x - 0.12, 0.7, 0), 0.04, "metall_hell_l"))
        teile.append(stab("buegel_r", (x + 0.12, 0.0, 0), (x + 0.12, 0.7, 0), 0.04, "metall_hell_l"))
        teile.append(kasten("buegel_o", (0.28, 0.04, 0.04), (x, 0.7, 0), "metall_hell_l"))
    return teile


def firmenschild():
    """Niedriges Standschild (<= 1 m) mit Kartonsymbol, ohne Schrift."""
    return [
        kasten("sockel", (1.8, 0.2, 0.5), (0, 0.1, 0), "beton_hell", rund=0.03, segmente=1),
        kasten("tafel", (1.6, 0.7, 0.16), (0, 0.55, 0), "tuerkis", rund=0.04, segmente=2),
        kasten("symbol", (0.34, 0.34, 0.02), (-0.45, 0.55, 0.085), "karton_hell"),
        kasten("symbol_band", (0.06, 0.34, 0.024), (-0.45, 0.55, 0.086), "klebeband"),
        kasten("balken1", (0.7, 0.08, 0.02), (0.25, 0.63, 0.085), "weiss_l"),
        kasten("balken2", (0.5, 0.06, 0.02), (0.15, 0.47, 0.085), "weiss_l"),
    ]


# ==============================================================================
# ZONEN (Masse und Freiflaechen nach docs/nacht/karten_welten.md)
# frei: (x, z, breite, tiefe, was) in Zonenkoordinaten
# ==============================================================================

def _station(wx, wz, mx, mz, was):
    return (wx - mx, wz - mz, 2.2, 2.2, was)


ZONEN = {
    "packhalle": {
        "breite": 9.0, "tiefe": 7.0, "welt": (0.0, 4.0), "boden": "hallenboden",
        "frei": [
            _station(-2.4, 1.65, 0, 4, "Station intake"),
            _station(2.2, 1.65, 0, 4, "Station processing"),
            _station(0.0, 4.7, 0, 4, "Station buffer"),
            (0.0, -3.0, 1.2, 1.0, "Tuer hinten x=0"),
            (-0.1, -2.35, 1.2, 2.2, "Weg zwischen den Stationen"),
            (0.0, -0.8, 8.8, 0.8, "Laufweg quer"),
        ],
    },
    "ladehof": {
        "breite": 8.0, "tiefe": 4.0, "welt": (-8.5, 9.5), "boden": "asphalt",
        "frei": [
            (0.0, -1.7, 7.8, 0.6, "Laufweg Rampe"),
        ],
    },
    "gang": {
        "breite": 25.0, "tiefe": 4.0, "welt": (0.0, -1.5), "boden": "hallenboden_linie",
        "frei": [
            _station(4.0, -2.3, 0, -1.5, "Station transport"),
            (0.0, -0.2, 24.8, 1.4, "Gangmitte"),
            (0.0, 0.9, 16.4, 0.8, "Laufweg z -0,6"),
            (-8.0, -1.5, 1.2, 1.0, "Tuer hinten x=-8"), (0.0, -1.5, 1.2, 1.0, "Tuer hinten x=0"),
            (8.0, -1.5, 1.2, 1.0, "Tuer hinten x=8"),
            (-8.0, 1.5, 1.2, 1.0, "Tuer vorn x=-8"), (0.0, 1.5, 1.2, 1.0, "Tuer vorn x=0"),
            (8.0, 1.5, 1.2, 1.0, "Tuer vorn x=8"),
            (11.95, -0.5, 1.1, 1.2, "Eingang rechts z=-2"),
        ],
    },
    "wareneingang": {
        "breite": 8.0, "tiefe": 6.0, "welt": (-8.5, -6.5), "boden": "hallenboden",
        "frei": [
            (0.5, 2.5, 1.2, 1.0, "Tuer vorn x=-8"),
            (0.5, 1.0, 1.2, 2.0, "Laufweg"),
            (0.0, -0.4, 7.8, 0.8, "Laufweg quer"),
        ],
    },
    "buero_shops": {
        "breite": 9.0, "tiefe": 6.0, "welt": (0.0, -6.5), "boden": "teppich",
        "frei": [
            _station(0.8, -6.6, 0, -6.5, "Station special"),
            (0.0, 2.5, 1.2, 1.0, "Tuer vorn x=0"),
            (0.0, 1.5, 1.2, 1.0, "Laufweg"),
        ],
    },
    "hochregal": {
        "breite": 8.0, "tiefe": 6.0, "welt": (8.5, -6.5), "boden": "hallenboden",
        "frei": [
            (-0.5, 2.5, 1.2, 1.0, "Tuer vorn x=8"),
            (-0.5, 0.6, 1.2, 2.8, "Laufweg"),
        ],
    },
    "rampe": {
        "breite": 8.0, "tiefe": 7.0, "welt": (-8.5, 4.0), "boden": "asphalt",
        "frei": [
            (0.5, -3.0, 1.2, 1.0, "Tuer hinten x=-8"),
            (0.5, -1.0, 1.2, 3.0, "Laufweg"),
        ],
    },
    "pausenraum": {
        "breite": 8.0, "tiefe": 7.0, "welt": (8.5, 4.0), "boden": "fliese",
        "frei": [
            (-0.5, -3.0, 1.2, 1.0, "Tuer hinten x=8"),
            (-0.5, -1.5, 1.2, 2.0, "Laufweg"),
            (0.0, 0.2, 7.8, 0.8, "Laufweg quer"),
        ],
    },
}

# Waende wie in worlds.json (Welt buero) -- nur fuer die Vorschau.
WAENDE = [
    {"typ": "voll", "achse": "x", "fest": -9.5, "von": -12.5, "bis": 12.5, "tueren": [], "fenster": [-10, -7, 0, 7, 10]},
    {"typ": "voll", "achse": "z", "fest": -12.5, "von": -9.5, "bis": 11.5, "tueren": [], "fenster": [-7, 4]},
    {"typ": "sockel", "achse": "x", "fest": 7.5, "von": -4.5, "bis": 12.5, "tueren": [], "fenster": [], "drehung": 180},
    {"typ": "sockel", "achse": "x", "fest": 11.5, "von": -12.5, "bis": -4.5, "tueren": [], "fenster": [], "drehung": 180},
    {"typ": "sockel", "achse": "z", "fest": -4.5, "von": 7.5, "bis": 11.5, "tueren": [], "fenster": [], "drehung": -90},
    {"typ": "sockel", "achse": "z", "fest": 12.5, "von": -9.5, "bis": 7.5, "tueren": [-2], "fenster": [], "drehung": -90},
    {"typ": "halb", "achse": "x", "fest": -3.5, "von": -12.5, "bis": 12.5, "tueren": [-8, 0, 8], "fenster": []},
    {"typ": "halb", "achse": "x", "fest": 0.5, "von": -12.5, "bis": 12.5, "tueren": [-8, 0, 8], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": -4.5, "von": -9.5, "bis": -3.5, "tueren": [], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": 4.5, "von": -9.5, "bis": -3.5, "tueren": [], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": -4.5, "von": 0.5, "bis": 7.5, "tueren": [], "fenster": []},
    {"typ": "halb", "achse": "z", "fest": 4.5, "von": 0.5, "bis": 7.5, "tueren": [], "fenster": []},
]
STATIONEN = {"intake": (-2.4, 1.65), "buffer": (0.0, 4.7), "processing": (2.2, 1.65),
             "transport": (4.0, -2.3), "special": (0.8, -6.6)}


def regal_mit_ware(rng, name, felder, feld_b, hoehe, tiefe, ebenen, x, z, dreh, lagen=(1, 2), folie=0.3):
    """Mehrfeldregal (Felder entlang lokal x) mit Paletten; jedes Feld und
    jede Palette wird einzeln verbucht (Budget je Moebel)."""
    x0 = -felder * feld_b / 2 + feld_b / 2
    for i in range(felder):
        teile = regal_feld(feld_b, hoehe, tiefe, [e for e in ebenen if e > 0.01], links=True,
                           rechts=(i == felder - 1), deck=False)
        transformieren(teile, x=x0 + i * feld_b)
        setzen("%s_feld%d" % (name, i), teile, x=x, z=z, dreh=dreh)
        for k, y in enumerate(ebenen):
            if (rng.random() < 0.12 and y > 0.01) or y > 2.5:
                # oberste Traverse bleibt leer: Ware hoechstens bis 3 m
                continue
            pal = kartons_auf_palette(rng, lagen=rng.choice(lagen), b=min(1.2, feld_b - 0.2),
                                      t=min(0.8, tiefe - 0.15), folie=rng.random() < folie, zufall=0.25)
            transformieren(pal, x=x0 + i * feld_b, y=y + (0.0 if y < 0.01 else 0.0))
            setzen("auf_%s_ware%d_%d" % (name, i, k), pal, x=x, z=z, dreh=dreh)


def einrichtung_packhalle():
    rng = random.Random(40)
    # links: Fachregal mit Versandmaterial (Front nach +x)
    teile = regal_feld(1.2, 2.0, 0.6, (0.12, 0.7, 1.35, 2.0), deck=True)
    for y in (0.12, 0.72, 1.37):
        x = -0.45
        while x < 0.4:
            w = rng.choice((0.26, 0.3, 0.34))
            teile += karton(w, rng.choice((0.22, 0.3, 0.4)), 0.42, rng.choice(_KARTON_TOENE), x=x + w / 2 - 0.1,
                            y=y, klebe=rng.random() < 0.5)
            x += w + 0.05
    setzen("regal_links_a", teile, x=-4.1, z=-2.765, dreh=90)
    teile = regal_feld(0.95, 2.0, 0.6, (0.12, 0.7, 1.35, 2.0), links=False, deck=True)
    for y in (0.12, 0.72):
        for i in range(3):
            r = stretchrolle(liegend=True)
            transformieren(r, x=0.0, y=y, z=-0.19 + i * 0.19)
            teile += r
    teile += karton(0.8, 0.5, 0.45, "karton_hell", x=0.0, y=1.37, klebe=True)
    setzen("regal_links_b", teile, x=-4.1, z=-1.69, dreh=90)
    setzen("luftpolster", luftpolster_rolle(), x=-4.05, z=0.4)
    # rechts: Rollbehaelter
    setzen("rollcontainer_a", rollcontainer(rng, 3), x=3.9, z=-2.85, dreh=-90)
    setzen("rollcontainer_b", rollcontainer(rng, 2), x=3.9, z=-1.8, dreh=-90)
    # vorn links
    setzen("packtisch", packtisch_klein(rng), x=-2.9, z=0.35)
    setzen("palette_folie", kartons_auf_palette(rng, 3, folie=True), x=-3.6, z=2.6, dreh=90)
    setzen("hubwagen", hubwagen(), x=-2.25, z=2.55)
    # vorn rechts
    setzen("palette_ausgang", kartons_auf_palette(rng, 2, einfach=False), x=2.8, z=0.4)
    setzen("gitterbox", gitterbox(rng), x=3.65, z=2.55, dreh=90)
    setzen("muelltonnen", muelltonnen(), x=2.05, z=3.0)
    setzen("feuerloescher", feuerloescher_staender(), x=-0.95, z=-3.2)
    setzen("wand_fluchtschild", wand_fluchtschild(), x=0.85, z=-3.4)
    # Bodenmarkierungen: Stationsrahmen, Palettenplatz
    mark = []
    for (fx, fz, fb, ft, was) in ZONEN["packhalle"]["frei"][:3]:
        mark += rahmen_markierung(fx, fz, fb - 0.1, ft - 0.1)
    mark += rahmen_markierung(2.8, 0.4, 1.45, 1.05, "markierung", d=0.05)
    mark += rahmen_markierung(-3.6, 2.6, 1.05, 1.45, "markierung", d=0.05)
    for i in range(3):
        mark.append(flach_viereck("pfeil", [(-0.35, -1.7 + i * 0.5), (-0.1, -1.95 + i * 0.5),
                                            (0.15, -1.7 + i * 0.5), (-0.1, -1.8 + i * 0.5)], 0.004, "markierung"))
    setzen("markierungen", mark)


def einrichtung_gang():
    rng = random.Random(41)
    setzen("regal_ecke", regal_feld(1.2, 2.0, 0.6, (0.12, 0.7, 1.35, 2.0)) +
           karton(0.5, 0.4, 0.45, "karton", x=-0.28, y=0.12) + karton(0.45, 0.3, 0.45, "karton_hell", x=0.28, y=0.12) +
           karton(0.9, 0.35, 0.45, "karton_dunkel", y=0.72) + karton(0.4, 0.4, 0.4, "karton", x=0.2, y=1.37),
           x=-11.6, z=-1.6)
    setzen("feuerloescher_l", feuerloescher_staender(), x=-10.3, z=-1.7)
    setzen("rollcontainer_1", rollcontainer(rng, 3), x=-6.55, z=-1.5)
    setzen("rollcontainer_2", rollcontainer(rng, 2), x=-5.7, z=-1.5)
    setzen("palette_mitte", kartons_auf_palette(rng, 2), x=-3.2, z=-1.45)
    setzen("warnschild_a", warnschild_staender(), x=-1.4, z=-1.6)
    setzen("muelltonnen", muelltonnen(), x=1.6, z=-1.58)
    setzen("rollcontainer_3", rollcontainer(rng, 1), x=6.1, z=-1.5)
    setzen("rollcontainer_4", rollcontainer(rng, 3), x=6.95, z=-1.5)
    setzen("palette_rechts", kartons_auf_palette(rng, 2, folie=True), x=9.6, z=-1.45)
    setzen("wand_erste_hilfe", wand_erste_hilfe(), x=10.8, z=-1.9)
    setzen("feuerloescher_r", feuerloescher_staender(), x=11.1, z=-1.7)
    # vorn
    setzen("palettenstapel", palettenstapel(5), x=-11.4, z=1.3)
    setzen("poller_a", poller(), x=-9.9, z=1.4)
    setzen("poller_b", poller(), x=-9.2, z=1.4)
    setzen("leitkegel_a", leitkegel(), x=-4.6, z=1.6)
    setzen("sitzbank", sitzbank(), x=-3.0, z=1.62)
    setzen("warnschild_b", warnschild_staender("stapler"), x=3.5, z=1.6)
    setzen("leitkegel_b", leitkegel(), x=5.6, z=1.6)
    setzen("gitterbox", gitterbox(rng), x=10.1, z=1.2)
    setzen("sackkarre", sackkarre(), x=11.7, z=1.45)
    # Boden: Zebrastreifen an den Tueren, Pfeile, Haltelinie am Eingang
    mark = []
    for tx in (-8.0, 0.0, 8.0):
        for k in range(6):
            mark.append(flach("zebra", 0.9, 0.16, tx, -0.95 + k * 0.4, "markierung"))
    for px in (-10.5, -4.0, 4.0 + 2.5, 10.2):
        if abs(px - 4.0) < 1.2:
            continue
        mark.append(flach_viereck("pfeil", [(px - 0.25, -0.45), (px + 0.1, -0.2), (px - 0.25, 0.05),
                                            (px - 0.1, -0.2)], 0.004, "gelb"))
        mark.append(flach_viereck("pfeil2", [(px + 0.1, -0.45), (px + 0.45, -0.2), (px + 0.1, 0.05),
                                             (px + 0.25, -0.2)], 0.004, "gelb"))
    mark += rahmen_markierung(11.9, -0.5, 0.9, 1.1, "gelb", d=0.05)
    mark += rahmen_markierung(4.0, -0.8, 2.1, 2.1)
    setzen("markierungen", mark)


def einrichtung_wareneingang():
    rng = random.Random(42)
    setzen("palette_folie_a", kartons_auf_palette(rng, 3, folie=True), x=-3.2, z=-2.45)
    setzen("palette_folie_b", kartons_auf_palette(rng, 4, folie=True), x=-1.9, z=-2.45)
    teile = regal_feld(1.6, 1.25, 0.5, (0.12, 0.64, 1.25), deck=True)
    for y in (0.12, 0.64):
        x = -0.7
        while x < 0.55:
            w = rng.choice((0.28, 0.34, 0.4))
            teile += karton(w, rng.choice((0.25, 0.32, 0.4)), 0.38, rng.choice(_KARTON_TOENE),
                            x=x + w / 2, y=y, klebe=rng.random() < 0.6)
            x += w + 0.05
    setzen("regal_niedrig", teile, x=1.9, z=-2.62)
    rollen = []
    for i in range(3):
        r = stretchrolle()
        transformieren(r, x=-0.22 + i * 0.22, z=0.02 * i)
        rollen += r
    setzen("stretchrollen", rollen, x=3.4, z=-2.55)
    setzen("palettenstapel", palettenstapel(6), x=-3.25, z=-1.45)
    setzen("leitkegel", leitkegel(), x=-1.6, z=-1.3)
    setzen("palette_ankunft", kartons_auf_palette(rng, 1, einfach=False), x=2.65, z=-1.4)
    # vorn links: Wickler mit Palette
    setzen("wickler", wickelmaschine(), x=-2.4, z=1.6)
    pal = kartons_auf_palette(rng, 3, folie=True)
    transformieren(pal, y=0.1)
    setzen("auf_wickler_palette", pal, x=-2.4, z=1.6)
    setzen("stretchrolle_liegend", stretchrolle(liegend=True), x=-0.8, z=2.6)
    # vorn rechts
    setzen("stehpult", stehpult(), x=2.1, z=0.75)
    hw = hubwagen()
    setzen("hubwagen", hw, x=3.3, z=1.9, dreh=180)
    pal = palette(1.2, 0.8, einfach=True)
    transformieren(pal, y=0.085)
    setzen("auf_hubwagen_palette", pal + karton(0.5, 0.4, 0.5, "karton_hell", y=0.229, x=-0.2), x=3.3, z=1.95,
           dreh=90)
    setzen("sackkarre", sackkarre(), x=1.6, z=2.45, dreh=20)
    setzen("feuerloescher", feuerloescher_staender(), x=-3.6, z=0.5, dreh=90)
    setzen("markierungen", rahmen_markierung(-2.4, 1.6, 1.9, 1.9) +
           rahmen_markierung(-2.55, -2.45, 2.7, 0.9, "markierung", d=0.05))


def einrichtung_buero_shops():
    rng = random.Random(43)
    toene = (("bildschirm_t", "bildschirm_o"), ("bildschirm_p",), ("bildschirm_b", "bildschirm_t"),
             ("bildschirm_o",))
    for i, x in enumerate((-3.4, -1.95, 1.95, 3.4)):
        setzen("schreibtisch_%d" % i, schreibtisch(toene[i], pflanze_klein=(i % 2 == 1)), x=x, z=-2.45)
        setzen("stuhl_%d" % i, buerostuhl("stoff_dunkel_l" if i % 2 else "stoff_tuerkis"), x=x + 0.05, z=-1.65,
               dreh=rng.uniform(-15, 15))
    setzen("whiteboard", whiteboard(), x=0.0, z=-2.6)
    setzen("glaswand", glaswand(5.4), x=-4.34, z=0.0)
    setzen("musterregal", musterregal(rng), x=-4.08, z=0.3, dreh=90)
    setzen("wasserspender", wasserspender(), x=-3.95, z=-0.95)
    setzen("sideboard", sideboard_drucker(), x=-2.3, z=2.6, dreh=180)
    setzen("teppich_lounge", teppich(2.0, 1.8, "stoff_grau_l", "tuerkis"), x=3.2, z=1.85)
    setzen("sofa", sofa("stoff_senf_l", 1.6), x=3.2, z=2.3, dreh=180)
    setzen("couchtisch", couchtisch(), x=3.2, z=1.3)


def einrichtung_hochregal():
    rng = random.Random(44)
    ebenen3 = (0.0, 1.05, 2.0)
    regal_mit_ware(rng, "reihe_links", 2, 1.9, 3.0, 1.0, ebenen3 + (2.95,), x=-3.4, z=-0.96, dreh=90)
    regal_mit_ware(rng, "reihe_mitte", 2, 1.9, 2.6, 1.0, (0.0, 0.95, 1.85), x=0.75, z=-0.96, dreh=90)
    regal_mit_ware(rng, "reihe_rechts", 2, 1.9, 3.0, 1.0, ebenen3 + (2.95,), x=3.4, z=-0.96, dreh=-90)
    setzen("rollleiter", rollleiter(), x=2.15, z=-0.4)
    setzen("palette_vorn", kartons_auf_palette(rng, 2), x=-2.8, z=2.35)
    setzen("palettenstapel", palettenstapel(4), x=1.65, z=2.4)
    setzen("warnschild", warnschild_staender("stapler"), x=3.45, z=1.4)
    setzen("feuerloescher", feuerloescher_staender(), x=-3.6, z=1.5, dreh=90)
    mark = []
    for x in (-2.75, 0.05, 1.45, 2.8):
        mark.append(flach("gangline", 0.06, 3.7, x, -1.0, "gelb"))
    mark += rahmen_markierung(-2.8, 2.35, 1.4, 1.0, "markierung", d=0.05)
    setzen("markierungen", mark)


def einrichtung_rampe():
    rng = random.Random(45)
    for i, c in enumerate((-1.95, 1.95)):
        setzen("wand_rolltor_%d" % i, rolltor(2.2), x=-3.9, z=c, dreh=90)
        setzen("transporter_%d" % i, transporter("heck"), x=-1.5, z=c, dreh=90)
    mark = []
    for z in (-3.15, -0.75, 0.75, 3.15):
        mark.append(flach("bucht", 2.9, 0.07, -2.45, z, "markierung"))
    for c in (-1.95, 1.95):
        mark.append(flach("halt", 0.1, 2.4, -0.95, c, "gelb"))
        for k in range(4):
            mark.append(flach_viereck("schraffur", [(-0.85, c - 1.1 + k * 0.6), (-0.6, c - 0.95 + k * 0.6),
                                                    (-0.6, c - 0.8 + k * 0.6), (-0.85, c - 0.95 + k * 0.6)],
                                      0.004, "gelb"))
    setzen("markierungen", mark)
    setzen("palette_laden", kartons_auf_palette(rng, 3, folie=True), x=-0.7, z=-1.95, dreh=90)
    setzen("hubwagen", hubwagen(), x=-0.6, z=1.9, dreh=90)
    setzen("poller_mitte", poller(), x=-3.3, z=0.0)
    setzen("poller_a", poller(), x=-0.6, z=0.0)
    setzen("palettenstapel", palettenstapel(7), x=2.8, z=-2.75)
    setzen("gitterbox", gitterbox(rng), x=2.55, z=-1.2)
    setzen("leitkegel_a", leitkegel(), x=1.6, z=-2.95)
    setzen("leitkegel_b", leitkegel(), x=1.6, z=0.35)
    setzen("palette_warten", kartons_auf_palette(rng, 2), x=2.5, z=1.25)
    setzen("muelltonnen", muelltonnen(), x=2.95, z=2.95)
    setzen("sackkarre", sackkarre(), x=0.8, z=2.9, dreh=-25)
    setzen("feuerloescher", feuerloescher_staender(), x=3.6, z=0.3, dreh=-90)


def einrichtung_pausenraum():
    rng = random.Random(46)
    setzen("kuechenzeile", kuechenzeile(2.6), x=1.5, z=-3.11)
    setzen("kuehlschrank", kuehlschrank(), x=3.45, z=-3.09)
    setzen("spinde", spinde(4), x=-2.9, z=-3.175)
    setzen("sitzbank", sitzbank(), x=-2.9, z=-2.45)
    setzen("wand_fluchtschild", wand_fluchtschild(), x=-1.35, z=-3.4)
    setzen("automat", getraenkeautomat(), x=-3.52, z=-1.35, dreh=90)
    setzen("tisch", tisch(), x=1.9, z=-1.3)
    for i, (x, z, d) in enumerate(((1.6, -2.05, 0), (2.2, -2.05, 0), (1.6, -0.55, 180), (2.2, -0.55, 180))):
        setzen("stuhl_%d" % i, stuhl(("stoff_senf_l", "tuerkis", "stoff_koralle_l", "stoff_senf_l")[i]),
               x=x, z=z, dreh=d + rng.uniform(-8, 8))
    setzen("kicker", kicker(), x=-2.0, z=1.4)
    setzen("teppich", teppich(2.6, 2.0, "stoff_grau_l", "stoff_senf_l"), x=2.4, z=2.2)
    setzen("sofa", sofa("stoff_tuerkis", 2.0), x=2.4, z=2.9, dreh=180)
    setzen("couchtisch", couchtisch(), x=2.4, z=1.8)


def stapler():
    """Gabelstapler, Gabeln nach +z, gelb mit Schutzdach. Boden y = 0, 2,1 hoch."""
    t = []
    t.append(kasten("chassis", (1.0, 0.5, 1.7), (0, 0.55, -0.1), "gelb", rund=0.05, segmente=1))
    t.append(kasten("gegengewicht", (1.0, 0.75, 0.5), (0, 0.78, -0.95), "gelb", rund=0.06, segmente=1))
    t.append(kasten("gegen_band", (1.02, 0.1, 0.52), (0, 0.55, -0.95), "schwarz"))
    t.append(kasten("sitz", (0.5, 0.1, 0.5), (0, 0.9, -0.15), "kunststoff_schwarz"))
    t.append(kasten("lehne", (0.5, 0.5, 0.08), (0, 1.15, -0.42), "kunststoff_schwarz"))
    t.append(kasten("lenksaeule", (0.06, 0.5, 0.06), (0, 1.0, 0.25), "metall_dunkel_l"))
    t.append(kasten("lenkrad", (0.3, 0.04, 0.3), (0, 1.25, 0.2), "kunststoff_schwarz"))
    for sx in (-1, 1):
        for z in (-0.55, 0.45):
            t.append(kasten("pfosten", (0.05, 1.2, 0.05), (sx * 0.46, 1.45, z), "metall_dunkel_l"))
        t.append(liegender_zylinder("rad_v", 0.32, 0.22, (sx * 0.5, 0.32, 0.5), "x", "reifen", seiten=10))
        t.append(liegender_zylinder("rad_h", 0.26, 0.2, (sx * 0.5, 0.26, -0.85), "x", "reifen", seiten=10))
    t.append(kasten("dach", (1.1, 0.05, 1.2), (0, 2.07, -0.05), "metall_dunkel_l"))
    for i in range(6):
        t.append(kasten("dachstab", (0.025, 0.03, 1.2), (-0.45 + i * 0.18, 2.1, -0.05), "metall_dunkel_l"))
    t.append(kasten("blitzlicht", (0.12, 0.12, 0.12), (0.3, 2.17, -0.5), "orange_kegel"))
    # Mast und Gabeln
    for sx in (-1, 1):
        t.append(kasten("mast", (0.07, 1.9, 0.08), (sx * 0.22, 1.0, 0.95), "metall_dunkel_l"))
        t.append(kasten("gabel", (0.1, 0.05, 1.0), (sx * 0.3, 0.12, 1.45), "metall_dunkel_l"))
    t.append(kasten("traverse", (0.7, 0.08, 0.06), (0, 1.9, 0.95), "metall_dunkel_l"))
    t.append(kasten("schlitten", (0.7, 0.5, 0.05), (0, 0.4, 1.0), "metall_dunkel_l"))
    return t


def einrichtung_ladehof():
    rng = random.Random(48)
    setzen("stapler", stapler(), x=-2.4, z=0.4, dreh=90)
    setzen("gitterbox", gitterbox(rng), x=1.6, z=0.9, dreh=8)
    setzen("palettenstapel", palettenstapel(4), x=3.15, z=1.1)
    setzen("hubwagen", hubwagen(), x=0.0, z=0.5, dreh=-90)
    setzen("paletten_ware", kartons_auf_palette(rng, 3, folie=True), x=3.0, z=-0.1, dreh=90)
    setzen("kegel_a", leitkegel(), x=-0.9, z=1.4)
    setzen("kegel_b", leitkegel(), x=-0.5, z=-0.5)
    setzen("muelltonnen", muelltonnen(), x=-2.85, z=1.45)
    setzen("sackkarre", sackkarre(), x=1.0, z=-0.7, dreh=-30)
    for i, px in enumerate((-3.7, -1.2, 1.6, 3.7)):
        setzen("poller_%d" % i, poller(), x=px, z=1.8)
    mark = rahmen_markierung(-2.4, 0.4, 3.0, 2.0)
    for k in range(5):
        mark.append(flach_viereck("schraffur", [(-3.7 + k * 0.5, -0.55), (-3.45 + k * 0.5, -0.55),
                                                 (-3.05 + k * 0.5, 0.0), (-3.3 + k * 0.5, 0.0)], 0.004, "gelb"))
    mark.append(flach("laufspur", 7.0, 0.07, 0.0, -1.3, "gelb"))
    mark.append(flach("laufspur2", 7.0, 0.07, 0.0, 1.55, "markierung"))
    for k in range(3):
        px = -2.0 + k * 2.2
        mark.append(flach_viereck("pfeil", [(px - 0.3, -1.0), (px + 0.1, -0.78), (px - 0.3, -0.56), (px - 0.15, -0.78)],
                                  0.004, "gelb"))
    mark.append(pfuetze(2.0, 1.0, 0.45, 0.28, 0.006))
    setzen("markierungen", mark)


EINRICHTUNGEN = {
    "packhalle": einrichtung_packhalle,
    "gang": einrichtung_gang,
    "wareneingang": einrichtung_wareneingang,
    "buero_shops": einrichtung_buero_shops,
    "hochregal": einrichtung_hochregal,
    "rampe": einrichtung_rampe,
    "pausenraum": einrichtung_pausenraum,
    "ladehof": einrichtung_ladehof,
}


# ==============================================================================
# UMGEBUNG UND FUNDAMENT (Welt-Koordinaten, Ursprung 0,0)
# ==============================================================================

BODEN_Y = -0.47


def container(laenge=6.1, farbe="cont_blau", hoehe=2.6, breite=2.4):
    """Seecontainer entlang x, Tueren bei +x. Wellblech als Rippen."""
    teile = [kasten("korpus", (laenge, hoehe, breite), (0, hoehe / 2, 0), farbe, rund=0.02, segmente=1),
             kasten("sockel", (laenge + 0.05, 0.12, breite + 0.05), (0, 0.06, 0), "cont_rippe"),
             kasten("dach", (laenge + 0.05, 0.1, breite + 0.05), (0, hoehe, 0), "cont_rippe")]
    n = int(laenge / 0.3)
    for sz in (-1, 1):
        for i in range(n):
            x = -laenge / 2 + 0.2 + i * (laenge - 0.4) / (n - 1)
            teile.append(kasten("rippe", (0.1, hoehe - 0.3, 0.03), (x, hoehe / 2, sz * (breite / 2 + 0.012)), "cont_rippe"))
    teile.append(kasten("tuerrahmen", (0.06, hoehe - 0.2, breite - 0.1), (laenge / 2 + 0.01, hoehe / 2, 0), "cont_rippe"))
    for sz in (-1, 1):
        teile.append(kasten("riegel", (0.05, hoehe - 0.5, 0.04), (laenge / 2 + 0.05, hoehe / 2, sz * 0.3), "metall_hell_l"))
    return teile


def lkw(trailer=8.0):
    """Sattelzug entlang x: Zugmaschine bei +x (Fahrerhaus zeigt nach +x), Auflieger mit
    tuerkiser Plane bei -x. Boden y = 0, 3,0 hoch, Seite +z zur Kamera."""
    teile = []
    t0, t1 = -trailer / 2 - 1.2, trailer / 2 - 1.2          # Auflieger
    # Rahmen und Plane
    teile.append(kasten("rahmen", (trailer, 0.25, 2.3), ((t0 + t1) / 2, 0.95, 0), "lkw_rahmen"))
    teile.append(kasten("plane", (trailer, 2.2, 2.5), ((t0 + t1) / 2, 0.95 + 1.1, 0), "lkw_plane", rund=0.12, segmente=2))
    for i in range(7):
        x = t0 + 0.5 + i * (trailer - 1.0) / 6
        for sz in (-1, 1):
            teile.append(kasten("gurt", (0.08, 2.0, 0.03), (x, 2.05, sz * 1.27), "lkw_plane_dunkel"))
    teile.append(kasten("dachband", (trailer - 0.1, 0.06, 1.8), ((t0 + t1) / 2, 3.2, 0), "lkw_plane_dunkel", rund=0.02, segmente=1))
    # Heckleuchten
    for sz in (-1, 1):
        teile.append(kasten("leuchte", (0.05, 0.3, 0.12), (t0 - 0.02, 1.0, sz * 1.0), "rot_signal"))
    # Zugmaschine
    zx = t1 + 0.35
    teile.append(kasten("zugrahmen", (3.0, 0.3, 2.1), (zx + 0.4, 0.85, 0), "lkw_rahmen"))
    teile.append(kasten("kabine", (1.9, 2.1, 2.45), (zx + 1.2, 0.95 + 1.1, 0), "lkw_kabine", rund=0.1, segmente=2))
    teile.append(kasten("dachspoiler", (1.2, 0.55, 2.3), (zx + 0.6, 3.5, 0), "lkw_kabine", rund=0.12, segmente=1))
    teile.append(kasten("scheibe", (0.03, 0.7, 2.2), (zx + 2.16, 2.35, 0), "bildschirm"))
    teile.append(kasten("grill", (0.04, 0.6, 1.6), (zx + 2.17, 1.35, 0), "kunststoff_schwarz"))
    teile.append(kasten("stoss", (0.2, 0.3, 2.35), (zx + 2.18, 0.7, 0), "kunststoff_schwarz"))
    for sz in (-1, 1):
        teile.append(kasten("scheinwerfer", (0.04, 0.2, 0.45), (zx + 2.17, 1.0, sz * 0.95), "lampe_licht"))
        teile.append(kasten("seitenfenster", (0.9, 0.7, 0.03), (zx + 1.5, 2.3, sz * 1.24), "bildschirm"))
        teile.append(kasten("tuergriff", (0.2, 0.05, 0.04), (zx + 0.95, 1.6, sz * 1.24), "kunststoff_schwarz"))
        teile.append(kasten("spiegel", (0.1, 0.5, 0.1), (zx + 1.95, 2.2, sz * 1.4), "kunststoff_schwarz"))
        teile.append(kasten("tank", (1.2, 0.5, 0.45), (zx + 0.3, 0.55, sz * 1.05), "metall_hell_l", rund=0.04, segmente=1))
    # Raeder: Zugmaschine 2 Achsen, Auflieger Tandem
    for x in (zx + 1.75, zx + 0.1):
        for sz in (-1, 1):
            teile.append(liegender_zylinder("rad", 0.5, 0.34, (x, 0.5, sz * 1.0), "z", "reifen", seiten=12))
            teile.append(liegender_zylinder("felge", 0.25, 0.36, (x, 0.5, sz * 1.0), "z", "metall_hell_l", seiten=8))
    for x in (t0 + 1.1, t0 + 2.3):
        for sz in (-1, 1):
            teile.append(liegender_zylinder("rad", 0.5, 0.34, (x, 0.5, sz * 1.0), "z", "reifen", seiten=12))
            teile.append(liegender_zylinder("felge", 0.25, 0.36, (x, 0.5, sz * 1.0), "z", "metall_hell_l", seiten=8))
    # Logo-Feld auf der Plane (Seite +z), weiss
    teile.append(kasten("logo", (2.2, 0.8, 0.02), ((t0 + t1) / 2 + 0.2, 2.1, 1.27), "weiss_l"))
    teile.append(kasten("logo_karton", (0.5, 0.5, 0.03), ((t0 + t1) / 2 - 0.5, 2.1, 1.28), "karton_hell"))
    teile.append(kasten("logo_balken", (1.2, 0.12, 0.03), ((t0 + t1) / 2 + 0.5, 2.2, 1.28), "lkw_rahmen"))
    teile.append(kasten("logo_balken2", (0.9, 0.12, 0.03), ((t0 + t1) / 2 + 0.35, 1.95, 1.28), "lkw_rahmen"))
    return teile


def pfuetze(x, z, rx, rz, y):
    import math as _m
    pk = [(x + _m.cos(a * _m.pi / 4) * rx * (1.0 + 0.15 * ((a * 7) % 3 - 1)),
           z + _m.sin(a * _m.pi / 4) * rz * (1.0 + 0.12 * ((a * 5) % 3 - 1))) for a in range(8)]
    return flach_viereck("pfuetze", pk, y, "pfuetze")


def umgebung():
    rng = random.Random(47)
    y = BODEN_Y
    setzen("rasen", [kasten("rasen", (48.0, 0.4, 40.0), (0, y - 0.2, -0.5), "rasen", rund=1.2, segmente=3)])
    setzen("asphalt", [kasten("asphalt", (41.0, 0.03, 31.0), (0, y + 0.012, -0.5), "asphalt_grau",
                              rund=0.8, segmente=2)])
    setzen("umlauf", [kasten("umlauf", (28.0, 0.03, 20.0), (0, y + 0.02, -1.0), "beton_hell")])
    mark = []
    # Parkplaetze vorn
    for i in range(9):
        x = -11.7 + i * 2.9
        mark.append(flach("parklinie", 0.1, 4.2, x, 11.6, "markierung", y=y + 0.03))
    mark.append(flach("parkkante", 23.3, 0.1, 0.0, 9.55, "markierung", y=y + 0.03))
    mark.append(flach("fahrbahnmitte", 34.0, 0.12, 0.0, 14.6, "markierung", y=y + 0.03))
    for i in range(8):
        x = -10.25 + i * 2.9
        mark.append(kasten("radstopp", (0.9, 0.12, 0.18), (x, y + 0.08, 13.3), "beton_hell"))
        if i in (2, 5):
            mark.append(flach("platz_tuerkis", 2.4, 3.6, x, 11.7, "tuerkis", y=y + 0.028))
    # Parkplaetze hinten
    for i in range(6):
        mark.append(flach("parklinie_h", 0.1, 4.0, 3.0 + i * 3.0, -12.8, "markierung", y=y + 0.03))
    for (px_, pz_, rx_, rz_) in ((-6.4, 11.3, 1.1, 0.55), (2.6, 10.6, 0.9, 0.5), (9.9, 12.2, 1.3, 0.6),
                                 (-0.8, 12.6, 0.8, 0.4), (-13.2, 11.0, 0.7, 0.45)):
        mark.append(pfuetze(px_, pz_, rx_, rz_, y + 0.032))
    setzen("markierungen", mark)
    # Laderampe links (Oberkante = Hallenboden) mit Auffahrt
    setzen("laderampe", [kasten("rampe", (3.5, 0.47, 7.2), (-14.25, y + 0.235, 4.0), "beton_sockel", unten=False),
                         prisma("auffahrt", [(-16.0, 0.0), (-19.0, y), (-16.0, y)], 0.4, 7.6, "beton_sockel"),
                         kasten("kante", (0.12, 0.08, 7.2), (-16.0, 0.04, 4.0), "gelb")])
    for i, c in enumerate((2.05, 5.95)):
        setzen("transporter_front_%d" % i, transporter("front"), x=-10.0, z=c, dreh=90)
    # hinten: Transporter, Baeume, Laternen, Zaun
    setzen("transporter_hinten", transporter("ganz"), x=-5.5, z=-12.8, dreh=90, y=y)
    for i, (bx, bz) in enumerate(((-18.5, -14.3), (-12.5, -14.8), (-8.5, -14.2), (1.0, -14.8), (7.5, -15.0),
                                  (13.0, -14.3), (18.5, -14.8))):
        if i % 3 == 1:
            setzen("baum_%d" % i, saeulenbaum(rng.uniform(3.8, 4.6)), x=bx, z=bz, y=y)
        else:
            setzen("baum_%d" % i, baum(rng, rng.uniform(3.2, 3.9), rng.uniform(1.0, 1.25)), x=bx, z=bz,
                   dreh=rng.uniform(0, 360), y=y)
    # M2: Containerlager hinten rechts und links (Hoehenobjekte im Bildhintergrund)
    setzen("container_a", container(6.1, "cont_rot"), x=14.0, z=-12.3, y=y)
    setzen("container_b", container(6.1, "cont_blau"), x=14.0, z=-12.3, y=y + 2.62)
    setzen("container_c", container(6.1, "cont_gruen"), x=20.6, z=-12.5, y=y, dreh=4)
    setzen("container_d", container(6.1, "cont_grau"), x=-17.0, z=-5.5, y=y, dreh=90)
    setzen("container_e", container(6.1, "cont_rot"), x=-17.0, z=-5.5, y=y + 2.62, dreh=90)
    for i, (bx, bz) in enumerate(((-21.0, -8.0), (-21.3, -2.0), (-21.0, 4.5))):
        setzen("baum_l%d" % i, baum(rng, rng.uniform(3.2, 3.8), 1.1), x=bx, z=bz, dreh=rng.uniform(0, 360), y=y)
    for i, (lx, lz, d) in enumerate(((-15.0, -11.0, 0), (-3.0, -11.0, 0), (9.0, -11.0, 0),
                                     (-18.5, -4.0, -90), (-19.8, 1.0, -90))):
        setzen("laterne_%d" % i, laterne(), x=lx, z=lz, dreh=d + 180, y=y)
    for i in range(17):
        teile = zaunfeld()
        transformieren(teile, x=-21.25 + i * 2.5)
        setzen("zaun_h%d" % i, teile, z=-16.8, y=y)
    for i in range(9):
        teile = zaunfeld()
        transformieren(teile, dreh_grad=90)
        setzen("zaun_l%d" % i, teile, x=-22.8, z=-15.55 + i * 2.5, y=y)
    # rechts und vorn: nur Niedriges (<= 1 m)
    setzen("eingangsweg", [kasten("weg", (8.0, 0.03, 1.8), (16.5, y + 0.035, -2.0), "beton_hell")])
    setzen("fahrradstaender", fahrradstaender(), x=15.5, z=0.8, y=y)
    setzen("firmenschild", firmenschild(), x=17.2, z=-5.0, dreh=90, y=y)
    for i in range(9):
        bx = 14.0 + (i % 3) * 2.2 + rng.uniform(-0.3, 0.3)
        bz = -12.0 + i * 2.6 + rng.uniform(-0.3, 0.3)
        if abs(bz + 2.0) < 1.6 or abs(bz - 0.8) < 1.0 or abs(bz + 5.0) < 1.2:
            continue
        setzen("busch_r%d" % i, busch(rng.uniform(0.45, 0.6), rng.uniform(0.5, 0.75)), x=bx, z=bz, y=y)
    for i in range(12):
        bx = -18.5 + i * 3.4
        setzen("hecke_%d" % i, busch(0.7, 0.7), x=bx, z=16.0, y=y)
    for i in range(4):
        setzen("poller_%d" % i, poller(0.7), x=13.2 + i * 1.0, z=-3.3 + (i % 2) * 2.6, y=y)


def fundament():
    setzen("fundament", [kasten("fundament", (26.0, 0.45, 18.0), (0.0, BODEN_Y + 0.225, -1.0), "beton_sockel",
                                rund=0.06, segmente=2),
                         kasten("fundament_ladehof", (9.0, 0.45, 4.6), (-8.5, BODEN_Y + 0.225, 9.8), "beton_sockel",
                                rund=0.06, segmente=2)])


def lkw_kulisse():
    setzen("lkw", lkw(), y=BODEN_Y)


KULISSE = {"umgebung": umgebung, "fundament": fundament, "welt_lkw": lkw_kulisse}


# ==============================================================================
# ABLAUF
# ==============================================================================

def pfad(name):
    return os.path.join(AUSGABE, name + ".glb")


def bauen(name, fn, zone=None):
    alles_loeschen()
    del MOEBEL[:]
    fn()
    summe, ueber = moebel_bericht()
    fehler = freiflaechen_pruefen(zone) if zone else 0
    obj = verbinden([t for _, teile in MOEBEL for t in teile], name)
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    exportieren(obj, pfad(name))
    budget = ZONEN_BUDGET
    zeile = "  %-26s %5d Dreiecke%s  %2d Mat  x %+6.2f..%+6.2f  y %+.2f..%+.2f  z %+6.2f..%+6.2f  %s" % (
        name, n, " <-- UEBER BUDGET" if n > budget else "", len(obj.data.materials), x0, x1, y0, y1, z0, z1,
        "frei OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler)
    print(zeile)
    return zeile, fehler + ueber


# --- Vorschau ------------------------------------------------------------------

_VORLAGEN = {}


def _vorlage(modul_datei):
    """Importiert eine GLB einmal und liefert das verbundene Mesh-Objekt."""
    if modul_datei in _VORLAGEN:
        return _VORLAGEN[modul_datei]
    vorher = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=modul_datei)
    neu = [o for o in bpy.data.objects if o not in vorher]
    mesh = [o for o in neu if o.type == "MESH"][0]
    mesh.matrix_world = mesh.matrix_world.copy()
    for o in neu:
        if o is not mesh:
            bpy.data.objects.remove(o, do_unlink=True)
    mesh.parent = None
    mesh.hide_render = True
    mesh.hide_viewport = True
    _VORLAGEN[modul_datei] = mesh
    return mesh


def aufstellen(modul_datei, x=0.0, z=0.0, dreh=0.0, y=0.0):
    v = _vorlage(modul_datei)
    kopie = v.copy()
    bpy.context.scene.collection.objects.link(kopie)
    kopie.hide_render = False
    kopie.hide_viewport = False
    kopie.matrix_world = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh), 4, "Z")
    return kopie


def karte_aufstellen():
    zonen = [("packhalle", -4, 1, 4, 7), ("gang", -12, -3, 12, 0), ("wareneingang", -12, -9, -5, -4),
             ("buero_shops", -4, -9, 4, -4), ("hochregal", 5, -9, 12, -4), ("rampe", -12, 1, -5, 7),
             ("pausenraum", 5, 1, 12, 7), ("ladehof", -12, 8, -5, 11)]
    for zid, x1, z1, x2, z2 in zonen:
        typ = ZONEN[zid]["boden"]
        for ix in range(x1, x2 + 1):
            for iz in range(z1, z2 + 1):
                ab = "a" if (ix + iz) % 2 == 0 else "b"
                aufstellen(modul_pfad("boden_%s_%s" % (typ, ab)), ix, iz)
    saetze = {"voll": ("wand_voll", "wand_halb_tuer", "wand_voll_fenster", "pfosten_voll"),
              "halb": ("wand_halb", "wand_halb_tuer", "wand_halb", "pfosten_halb"),
              "sockel": ("wand_sockel", "wand_sockel_tuer", "wand_sockel", "pfosten_sockel")}
    rang = {"pfosten_voll": 3, "pfosten_halb": 2, "pfosten_sockel": 1}
    pfosten = {}
    for w in WAENDE:
        satz = saetze[w["typ"]]
        achse_x = w["achse"] == "x"
        grad = w.get("drehung", 0.0 if achse_x else 90.0)
        feld = w["von"] + 0.5
        while feld < w["bis"]:
            modul = satz[0]
            if any(abs(feld - t) < 0.01 for t in w["tueren"]):
                modul = satz[1]
            elif any(abs(feld - t) < 0.01 for t in w["fenster"]):
                modul = satz[2]
            px, pz = (feld, w["fest"]) if achse_x else (w["fest"], feld)
            aufstellen(modul_pfad(modul), px, pz, grad)
            feld += 1.0
        for ende in (w["von"], w["bis"]):
            p = (ende, w["fest"]) if achse_x else (w["fest"], ende)
            if rang[satz[3]] > rang.get(pfosten.get(p, ""), 0):
                pfosten[p] = satz[3]
    for (px, pz), m in pfosten.items():
        aufstellen(modul_pfad(m), px, pz)
    for zid in EINRICHTUNGEN:
        wx, wz = ZONEN[zid]["welt"]
        aufstellen(pfad("einrichtung_" + zid), wx, wz)
    aufstellen(pfad("umgebung"))
    aufstellen(pfad("fundament"))
    aufstellen(pfad("welt_lkw"), 4.5, -12.9)


def stationen_markieren():
    """Nur Vorschau: Stationsflaechen als tuerkise Rahmen (2,2 x 2,2)."""
    teile = []
    for sx, sz in STATIONEN.values():
        for o in rahmen_markierung(sx, sz, 2.2, 2.2, "vorschau_frei", d=0.08, y=0.02):
            teile.append(o)
        teile.append(kasten("stationsklotz", (0.5, 0.5, 0.5), (sx, 0.25, sz), "vorschau_frei"))
    for zid, z in ZONEN.items():
        wx, wz = z["welt"]
        for (fx, fz, fb, ft, was) in z["frei"]:
            if was.startswith("Station"):
                continue
            teile += rahmen_markierung(wx + fx, wz + fz, fb, ft, "notiz_rosa", d=0.03, y=0.015)
    return teile


NAH = {
    "packhalle": ((0.0, 0.8, 4.0), 12.0),
    "gang": ((0.0, 0.6, -1.5), 22.0),
    "wareneingang": ((-8.5, 0.8, -6.5), 11.0),
    "buero_shops": ((0.0, 0.8, -6.5), 11.5),
    "hochregal": ((8.5, 1.0, -6.5), 11.0),
    "rampe": ((-8.5, 0.8, 4.0), 11.5),
    "pausenraum": ((8.5, 0.8, 4.0), 11.5),
    "ladehof": ((-8.5, 0.8, 9.5), 10.0),
}


def vorschau(nur=None):
    alles_loeschen()
    _VORLAGEN.clear()
    karte_aufstellen()
    if not nur:
        rendern(os.path.join(AUSGABE_VORSCHAU, "gesamt_karte.png"), (0.0, 0.0, -1.0), 44.0,
                aufloesung=1500, breite=2000)
        rendern(os.path.join(AUSGABE_VORSCHAU, "gesamt_halle.png"), (0.0, 0.5, -1.0), 31.0,
                aufloesung=1400, breite=2000)
    marken = stationen_markieren()
    for zid, (ziel, ortho) in NAH.items():
        if nur and zid not in nur:
            continue
        rendern(os.path.join(AUSGABE_VORSCHAU, "zone_%s.png" % zid), ziel, ortho, aufloesung=1100)
    for o in marken:
        o.hide_render = True
    if not nur or "umgebung" in nur:
        rendern(os.path.join(AUSGABE_VORSCHAU, "umgebung.png"), (-2.0, 0.0, 0.0), 58.0,
                aufloesung=1400, breite=2000)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    auswahl = [a for a in argumente if not a.startswith("--")]
    zeilen = []
    fehler = 0
    if "--nur-vorschau" not in argumente:
        print("")
        print("=== EINRICHTUNG WELT 4 (LAGER) ===")
        for zid, fn in EINRICHTUNGEN.items():
            if auswahl and zid not in auswahl:
                continue
            print("  -- %s" % zid)
            z, f = bauen("einrichtung_" + zid, fn, ZONEN[zid])
            zeilen.append(z)
            fehler += f
        for name, fn in KULISSE.items():
            if auswahl and name not in auswahl:
                continue
            print("  -- %s" % name)
            z, f = bauen(name, fn)
            zeilen.append(z)
            fehler += f
    if "--ohne-vorschau" not in argumente:
        vorschau(auswahl)
    print("")
    print("=== ERGEBNIS ===")
    for z in zeilen:
        print(z)
    print("=== %s ===" % ("alles sauber" if fehler == 0 else "%d Probleme -- siehe oben" % fehler))


if __name__ == "__main__":
    main()
