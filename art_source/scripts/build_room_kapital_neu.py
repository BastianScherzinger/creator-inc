"""Architektur-Baukasten fuer Welt 6 `kapital` -- das Penthouse, Nachtplan N50
(docs/NACHT_PLAN.md Abschnitte 2 und 5).

Aufruf:
    blender --background --python art_source/scripts/build_room_kapital_neu.py
    (optional nach "--": --ohne-vorschau)

Erzeugt nach project/assets/room/kapital/:
    boden_<typ>_a/_b   typ = parkett, marmor, deck  (1 x 1 m, Oberkante y = 0)
    wand_*             Masse, Hoehen und Ursprung wie wg_wand_* (room/zimmer):
                       1 m entlang lokal X, Ursprung unten Mitte, Innenseite +z
    gelaender          Glasbruestung mit Messing-Handlauf, 1 m
    pfosten_*          Saeulen 0,22 x 0,22 (Kappe 0,27)
    raum_*             die sieben Altmodule fuer validate Schritt 7
und Uebersichten nach art_source/vorschau/kapital/.

Palette: heller Putz, weisser Marmor mit Goldadern, dunkles Holz, Messing
(#F2B200), Glas leicht durchscheinend (goldene Stunde, Stadt dahinter).
Jede Datei enthaelt GENAU EIN Mesh. Koordinaten: GODOT.
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
    G, kasten, zylinder, kugel, profil_x, rundprofil, kissen_platte, transformieren,
    alles_loeschen, verbinden, dreiecke, masse, exportieren, importieren,
    palette_erweitern, material, _objekt, WURZEL,
)

AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "kapital")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "kapital")
HINTERGRUND = "#F3D9B4"

palette_erweitern({
    "k6_putz":          ("#F6F0E6", 0.85, 0.0, 1.0),
    "k6_putz_schatten": ("#E6DCCB", 0.85, 0.0, 1.0),
    "k6_messing":       ("#F2B200", 0.35, 0.45, 1.0),
    "k6_messing_dunkel": ("#C98F12", 0.40, 0.45, 1.0),
    "k6_holz_dunkel":   ("#5B3A26", 0.60, 0.0, 1.0),
    "k6_rahmen":        ("#3A3430", 0.45, 0.30, 1.0),
    "k6_glas":          ("#CFE9F2", 0.08, 0.0, 0.38),
    "k6_glas_dicht":    ("#BFE0EC", 0.10, 0.0, 1.0),
    "k6_parkett_a":     ("#4E3222", 0.70, 0.0, 1.0),
    "k6_parkett_b":     ("#432A1C", 0.70, 0.0, 1.0),
    "k6_parkett_c":     ("#5A3B28", 0.70, 0.0, 1.0),
    "k6_parkett_fuge":  ("#24150C", 0.90, 0.0, 1.0),
    "k6_marmor":        ("#F4F1EC", 0.30, 0.0, 1.0),
    "k6_marmor2":       ("#EEEAE3", 0.30, 0.0, 1.0),
    "k6_marmor_fuge":   ("#D8D1C6", 0.60, 0.0, 1.0),
    "k6_ader_gold":     ("#EDC878", 0.35, 0.3, 1.0),
    "k6_ader_grau":     ("#E1DBD2", 0.40, 0.0, 1.0),
    "k6_deck":          ("#CDA97A", 0.80, 0.0, 1.0),
    "k6_deck2":         ("#C09B6C", 0.80, 0.0, 1.0),
    "k6_stahl":         ("#6E7378", 0.35, 0.55, 1.0),
    "k6_stahl2":        ("#7C8186", 0.35, 0.55, 1.0),
    "k6_stahl_fuge":    ("#33363B", 0.60, 0.2, 1.0),
    "k6_stahl_hell":    ("#A9AEB4", 0.30, 0.6, 1.0),
    "k6_deck_fuge":     ("#6E5238", 0.95, 0.0, 1.0),
})


def flach_viereck(name, punkte, y, mat_name):
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for (x, z) in punkte]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat_name)


# ==============================================================================
# BODEN
# ==============================================================================

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def _parkett(tausch):
    """Tafelparkett: 2 x 2 Felder zu je drei Staeben, die Richtung wechselt
    von Feld zu Feld (Flechtmuster). In b sind die Richtungen vertauscht,
    damit das Muster ueber die Modulgrenze weiterlaeuft."""
    teile = [_tragplatte("k6_parkett_fuge", -0.005)]
    toene = ["k6_parkett_a", "k6_parkett_b", "k6_parkett_c"]
    for i in range(2):
        for k in range(2):
            x0, z0 = -0.5 + i * 0.5, -0.5 + k * 0.5
            quer = ((i + k) % 2 == 0) != tausch
            for s in range(3):
                a, b = s / 3.0 * 0.5, (s + 1) / 3.0 * 0.5
                mat = toene[(s + i * 2 + k) % 3]
                if quer:
                    teile.append(kissen_platte("stab", x0, x0 + 0.5, z0 + a, z0 + b, 0.0, -0.005, 0.005, mat))
                else:
                    teile.append(kissen_platte("stab", x0 + a, x0 + b, z0, z0 + 0.5, 0.0, -0.005, 0.005, mat))
    return teile


def boden_parkett_a():
    return _parkett(False)


def boden_parkett_b():
    return _parkett(True)


def _ader(punkte, breite, y, mat):
    """Schmale Marmorader als Polylinie flacher Vierecke."""
    teile = []
    for (ax, az), (bx, bz) in zip(punkte, punkte[1:]):
        dx, dz = bx - ax, bz - az
        l = math.hypot(dx, dz) or 1.0
        nx, nz = -dz / l * breite / 2, dx / l * breite / 2
        teile.append(flach_viereck("ader", [(ax - nx, az - nz), (bx - nx, bz - nz), (bx + nx, bz + nz), (ax + nx, az + nz)], y, mat))
    return teile


def _marmor(seed, grund):
    teile = [_tragplatte("k6_marmor_fuge", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.006, grund))
    rng = random.Random(seed)
    # eine goldene Hauptader, zwei feine graue
    for n, (mat, br, y) in enumerate((("k6_ader_gold", 0.014, 0.0012), ("k6_ader_grau", 0.008, 0.0010),
                                     ("k6_ader_grau", 0.006, 0.0011))):
        x = rng.uniform(-0.42, 0.42)
        z = -0.46
        pk = [(x, z)]
        while z < 0.44:
            z = min(0.46, z + rng.uniform(0.14, 0.24))
            x = max(-0.46, min(0.46, x + rng.uniform(-0.16, 0.16)))
            pk.append((x, z))
        if (seed + n) % 2:
            pk = [(p[1], p[0]) for p in pk]
        teile += _ader(pk, br, y, mat)
    return teile


def boden_marmor_a():
    return _marmor(601, "k6_marmor")


def boden_marmor_b():
    return _marmor(602, "k6_marmor2")


def _stahl(variante):
    """Tresorboden: Stahlplatte mit Nietreihe, in b mit Riffelstreifen."""
    teile = [_tragplatte("k6_stahl_fuge", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.006,
                               "k6_stahl" if variante == "a" else "k6_stahl2"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("niet", (0.05, 0.012, 0.05), (sx * 0.42, 0.006, sz * 0.42), "k6_messing", unten=False))
    if variante == "b":
        for k in range(5):
            teile.append(kasten("riffel", (0.8, 0.006, 0.03), (0.0, 0.003, -0.32 + k * 0.16), "k6_stahl_hell", unten=False))
    return teile


def boden_stahl_a():
    return _stahl("a")


def boden_stahl_b():
    return _stahl("b")


def _deck(versatz):
    """Teakdeck: fuenf Bretter mit dunklen Spalten und je einem Stoss."""
    teile = [_tragplatte("k6_deck_fuge", -0.03)]
    breite = 0.2
    stoesse = (0.15, -0.25, 0.35, -0.05, 0.2) if not versatz else (-0.3, 0.1, -0.15, 0.3, -0.4)
    for i in range(5):
        z0 = -0.5 + i * breite + 0.012
        z1 = -0.5 + (i + 1) * breite - 0.012
        mat = "k6_deck2" if i % 2 else "k6_deck"
        s = stoesse[i]
        for xa, xb in ((-0.5, s - 0.006), (s + 0.006, 0.5)):
            teile.append(kasten("brett", (xb - xa, 0.03, z1 - z0), ((xa + xb) / 2, -0.015, (z0 + z1) / 2.0),
                                mat if xa < 0 else ("k6_deck" if i % 2 else "k6_deck2"), unten=False))
    return teile


def boden_deck_a():
    return _deck(False)


def boden_deck_b():
    return _deck(True)


# ==============================================================================
# WAENDE -- Querschnitt wie wg_wand_*
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
    return profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.025), x0, x1, "k6_messing")


def _leiste(hoehe, x0=-0.5, x1=0.5):
    d = LEISTE_DICKE / 2.0
    return profil_x("leiste", rundprofil(-d, d, 0.0, hoehe, 0.012, 1), x0, x1, "k6_holz_dunkel")


def _koerper(x0, x1, y0, y1, mat="k6_putz"):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, mat)


def _leistenhoehe(hoehe):
    return min(LEISTE_HOEHE, hoehe * 0.2)


def wand_voll():
    h = HOEHE["voll"]
    teile = [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001), _kappe(h), _leiste(_leistenhoehe(h))]
    # feine Schattenfuge unter der Kappe (innen)
    teile.append(kasten("fuge", (1.0, 0.025, 0.006), (0.0, h - 0.16, WAND_DICKE / 2 + 0.002), "k6_putz_schatten"))
    return teile


def _glasfeld(u, o, pfosten_b=0.045, tiefe=0.10, glas_tiefe=0.02):
    """Glas von u bis o ueber die ganze Modulbreite, Pfosten nur am linken
    Rand (die Reihe wirkt wie eine durchgehende Glasfront)."""
    teile = []
    teile.append(kasten("pfosten", (pfosten_b, o - u, tiefe), (-0.5 + pfosten_b / 2, (u + o) / 2, 0.0), "k6_rahmen"))
    teile.append(kasten("glas", (1.0 - pfosten_b, o - u, glas_tiefe), (pfosten_b / 2, (u + o) / 2, 0.0), "k6_glas"))
    return teile


def wand_voll_fenster():
    """Bodentiefes Glas: schmale Holzschwelle unten, Putzsturz oben mit
    Messingkappe, dunkler Riegel an Ober- und Unterkante."""
    h = HOEHE["voll"]
    u, o = 0.08, 2.14
    teile = [
        profil_x("schwelle", rundprofil(-0.11, 0.11, 0.0, u, 0.012, 1), -0.5, 0.5, "k6_holz_dunkel"),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _kappe(h),
        kasten("riegel_u", (1.0, 0.04, 0.10), (0.0, u + 0.02, 0.0), "k6_rahmen"),
        kasten("riegel_o", (1.0, 0.04, 0.10), (0.0, o - 0.02, 0.0), "k6_rahmen"),
    ]
    teile += _glasfeld(u + 0.04, o - 0.04)
    # Messing-Querstab in Handhoehe (nur innen) -- liest sich als edle Glasfront
    teile.append(kasten("stange", (1.0, 0.022, 0.022), (0.0, 0.95, 0.075), "k6_messing"))
    return teile


def wand_halb():
    """Glastrennwand: dunkler Holzsockel, Glas, Messing-Handlauf obenauf."""
    h = HOEHE["halb"]
    u = 0.16
    teile = [
        _koerper(-0.5, 0.5, 0.0, u, "k6_holz_dunkel"),
        _kappe(h),
        kasten("riegel_u", (1.0, 0.03, 0.12), (0.0, u + 0.015, 0.0), "k6_messing_dunkel"),
    ]
    teile += _glasfeld(u + 0.03, h - KAPPE_HOEHE, pfosten_b=0.04, tiefe=0.08)
    return teile


def wand_sockel():
    """Sockel: Marmorband mit Messingkappe."""
    h = HOEHE["sockel"]
    return [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001, "k6_marmor"), _kappe(h),
            _leiste(_leistenhoehe(h))]


def _tuerrahmen():
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1, t), (s * TUER_PFOSTEN_X, (h - 0.1) / 2, 0.0),
                            "k6_holz_dunkel", rund=0.015, segmente=2))
        teile.append(kasten("zierband", (b, 0.03, t + 0.012), (s * TUER_PFOSTEN_X, 0.10, 0.0), "k6_messing"))
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.1, t), (0.0, h - 0.05, 0.0),
                        "k6_messing", rund=0.02, segmente=2))
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "k6_messing_dunkel", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Glastuer mit Messingrahmen, 105 Grad nach aussen (lokal -z) offen."""
    teile = _tuerrahmen()
    bb, bh, bd = 0.78, 1.93, 0.045
    r = 0.06
    blatt = [
        kasten("blatt_l", (r, bh, bd), (r / 2, bh / 2 + 0.012, 0.0), "k6_messing"),
        kasten("blatt_r", (r, bh, bd), (bb - r / 2, bh / 2 + 0.012, 0.0), "k6_messing"),
        kasten("blatt_o", (bb - 2 * r, r, bd), (bb / 2, bh - r / 2 + 0.012, 0.0), "k6_messing"),
        kasten("blatt_u", (bb - 2 * r, 0.14, bd), (bb / 2, 0.07 + 0.012, 0.0), "k6_messing"),
        kasten("blatt_glas", (bb - 2 * r, bh - r - 0.14, 0.014), (bb / 2, 0.012 + 0.14 + (bh - r - 0.14) / 2, 0.0), "k6_glas"),
    ]
    for seite in (-1, 1):
        blatt.append(kasten("griff", (0.03, 0.55, 0.03), (bb - 0.12, 1.0, seite * (bd / 2 + 0.035)), "k6_holz_dunkel"))
    transformieren(blatt, x=-TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    return teile + blatt


def gelaender():
    """Glasbruestung: Glasscheibe in Bodenprofil, Messing-Handlauf bei 1,0."""
    teile = [
        profil_x("handlauf", rundprofil(-0.035, 0.035, 0.95, 1.0, 0.02), -0.5, 0.5, "k6_messing"),
        kasten("bodenprofil", (1.0, 0.09, 0.08), (0.0, 0.045, 0.0), "k6_rahmen"),
        kasten("glas", (0.99, 0.86, 0.02), (0.0, 0.09 + 0.43, 0.0), "k6_glas"),
    ]
    for x in (-0.3, 0.3):
        teile.append(kasten("klemme", (0.05, 0.05, 0.05), (x, 0.92, 0.0), "k6_messing_dunkel"))
    return teile


def _pfosten(hoehe):
    lh = _leistenhoehe(hoehe)
    teile = [
        kasten("saeule", (0.22, hoehe - KAPPE_HOEHE + 0.002, 0.22),
               (0.0, (hoehe - KAPPE_HOEHE) / 2 + 0.001, 0.0), "k6_putz", unten=False),
        kasten("saeule_kappe", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "k6_messing", rund=0.022, segmente=2),
        kasten("saeule_leiste", (0.24, lh, 0.24), (0.0, lh / 2, 0.0), "k6_holz_dunkel", unten=False),
    ]
    if hoehe > 1.0:
        teile.append(kasten("saeule_band", (0.232, 0.04, 0.232), (0.0, hoehe * 0.55, 0.0), "k6_messing"))
    return teile


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


# ==============================================================================
# ALTMODULE (validate Schritt 7, RoomBuilder)
# ==============================================================================

def _altfliese(mat, ader):
    teile = [kasten("fliese", (0.98, 0.03, 0.98), (0.0, 0.0, 0.0), mat)]
    if ader:
        teile += _ader([(-0.4, -0.45), (-0.1, -0.1), (0.05, 0.2), (0.35, 0.45)], 0.014, 0.0162, "k6_ader_gold")
    return teile


def raum_fliese_a():
    return _altfliese("k6_marmor", True)


def raum_fliese_b():
    return _altfliese("k6_marmor2", False)


def raum_fliese_weg():
    return _altfliese("k6_parkett_a", False)


def _altwand(x0, x1, y0=0.0, y1=2.2):
    return [
        kasten("altwand", (x1 - x0, y1 - 0.06 - y0, 0.2), ((x0 + x1) / 2, (y0 + y1 - 0.06) / 2, 0.0), "k6_putz"),
        kasten("altkappe", (x1 - x0, 0.06, 0.2), ((x0 + x1) / 2, y1 - 0.03, 0.0), "k6_messing"),
    ]


def raum_wand():
    return _altwand(-0.5, 0.5)


def raum_wand_ecke():
    teile = _altwand(-0.5, 0.53)
    teile.append(kasten("altwand_z", (0.2, 2.14, 0.83), (0.43, 1.07, 0.515), "k6_putz"))
    teile.append(kasten("altkappe_z", (0.2, 0.06, 0.83), (0.43, 2.17, 0.515), "k6_messing"))
    return teile


def raum_wand_tuer():
    teile = _altwand(-1.0, -0.5) + _altwand(0.5, 1.0)
    teile.append(kasten("altsturz", (1.0, 0.3, 0.2), (0.0, 2.05, 0.0), "k6_putz"))
    for s in (-1, 1):
        teile.append(kasten("altpfosten", (0.08, 1.9, 0.2), (s * 0.46, 0.95, 0.0), "k6_holz_dunkel"))
    return teile


def raum_wand_fenster():
    return [
        kasten("unten", (1.0, 0.1, 0.2), (0.0, 0.05, 0.0), "k6_holz_dunkel"),
        kasten("oben", (1.0, 0.2, 0.2), (0.0, 2.04, 0.0), "k6_putz"),
        kasten("kappe", (1.0, 0.06, 0.2), (0.0, 2.17, 0.0), "k6_messing"),
        kasten("seite_l", (0.06, 1.84, 0.12), (-0.47, 1.02, 0.0), "k6_rahmen"),
        kasten("seite_r", (0.06, 1.84, 0.12), (0.47, 1.02, 0.0), "k6_rahmen"),
        kasten("glas", (0.88, 1.84, 0.03), (0.0, 1.02, 0.0), "k6_glas_dicht"),
    ]


# ==============================================================================
# VORSCHAU -- goldene Stunde
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
    cam_daten.clip_end = 600.0
    cam = bpy.data.objects.new("vorschau_kamera", cam_daten)
    szene.collection.objects.link(cam)
    cam.location = zielvek + richtung * 200.0
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

    sonne("licht_haupt", 2.6, "#FFE2B8", G(0.55, 0.85, 0.6), True, 10.0)
    sonne("licht_auf", 0.55, "#FFE9D2", G(-0.9, 0.55, 0.25), False, 30.0)
    welt = bpy.data.worlds.new("vorschau_welt")
    if welt.node_tree is None:
        welt.use_nodes = True
    baum = welt.node_tree
    for n in list(baum.nodes):
        baum.nodes.remove(n)
    ausgang = baum.nodes.new("ShaderNodeOutputWorld")
    licht = baum.nodes.new("ShaderNodeBackground")
    licht.inputs["Color"].default_value = farbe("#FFE8CC")
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
    "boden_parkett_a": boden_parkett_a,
    "boden_parkett_b": boden_parkett_b,
    "boden_marmor_a": boden_marmor_a,
    "boden_marmor_b": boden_marmor_b,
    "boden_stahl_a": boden_stahl_a,
    "boden_stahl_b": boden_stahl_b,
    "boden_deck_a": boden_deck_a,
    "boden_deck_b": boden_deck_b,
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


def vergleich_wg():
    """Masse der WG-Module auslesen und neben die eigenen stellen."""
    print("  -- Vergleich mit room/zimmer/wg_* --")
    zimmer = os.path.join(WURZEL, "project", "assets", "room", "zimmer")
    for name in MODULE:
        if name.startswith("boden_") or name.startswith("raum_"):
            continue
        wg = os.path.join(zimmer, "wg_" + name + ".glb")
        if not os.path.exists(wg):
            continue
        alles_loeschen()
        vorher = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=wg)
        neu = [o for o in bpy.data.objects if o not in vorher and o.type == "MESH"]
        pk = [o.matrix_world @ v.co for o in neu for v in o.data.vertices]
        xs = [p.x for p in pk]; ys = [p.z for p in pk]; zs = [-p.y for p in pk]
        print("  wg_%-22s x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f"
              % (name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))


def module_bauen():
    print("")
    print("=== MODULE WELT 6 (PENTHOUSE) ===")
    for name, bauen in MODULE.items():
        alles_loeschen()
        obj = verbinden(bauen(), name)
        pfad = modul_pfad(name)
        exportieren(obj, pfad)
        (x0, x1), (y0, y1), (z0, z1) = masse(obj)
        print("  %-28s %4d Dreiecke  x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f  %2d Mat"
              % (name, dreiecke(obj), x0, x1, y0, y1, z0, z1, len(obj.data.materials)))
    vergleich_wg()


def module_vorschau():
    alles_loeschen()
    boeden = [n for n in MODULE if n.startswith("boden_")]
    for i, name in enumerate(boeden):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                importieren(modul_pfad(name), x=(i % 3) * 3.4 + dx, z=(i // 3) * 3.4 + dz)
    # Schachbrett-Probe
    for j, typ in enumerate(("parkett", "marmor", "deck")):
        for dx in range(4):
            for dz in range(3):
                ab = "a" if (dx + dz) % 2 == 0 else "b"
                importieren(modul_pfad("boden_%s_%s" % (typ, ab)), x=10.5 + dx, z=-1 + j * 3.4 + dz)
    rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (7.0, 0.0, 2.0), 17.0)

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
        importieren(modul_pfad(pfosten), x=3.5, z=z)
        importieren(modul_pfad(wand), x=-0.5, z=z + 0.5, dreh_grad=90.0)
        importieren(modul_pfad("wand_voll_fenster" if r == 0 else wand), x=-0.5, z=z + 1.5, dreh_grad=90.0)
        for dx in range(4):
            importieren(modul_pfad("boden_parkett_" + ("a" if dx % 2 == 0 else "b")), x=dx, z=z + 1)
    for dx in range(3):
        importieren(modul_pfad("gelaender"), x=5.5 + dx, z=0.0)
        importieren(modul_pfad("boden_deck_" + ("a" if dx % 2 == 0 else "b")), x=5.5 + dx, z=0.5)
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
