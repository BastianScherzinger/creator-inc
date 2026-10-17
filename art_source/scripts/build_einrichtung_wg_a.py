"""Raumeinrichtungen fuer die WG-Karte von Welt 1, Team A (TASK 074a):
Dein Zimmer, Flur, Kueche, Bad (docs/WELT1_TIEFE.md, Abschnitte 3 und 10).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_wg_a.py
    (optional nach "--": zimmer flur kueche bad   -> nur diese Zonen
                         --ohne-vorschau           -> keine Renders
                         --nur-gesamt              -> nur die Gesamtvorschau)

Voraussetzung: build_room_wg.py ist gelaufen -- die Vorschau stellt die
exportierten Boden- und Wandmodule um die Einrichtung herum auf.

Erzeugt project/assets/world/zimmer/einrichtung_<zone>.glb:
  - EIN Mesh je Zone (ein Knoten, je Material eine Surface), Ursprung =
    Zonenmitte auf Bodenhoehe. Ein Mesh statt hundert Knoten: auf dem Handy
    zaehlen Draw Calls, nicht Dreiecke.
  - Keine Waende, keine Boeden -- die setzt der Grundriss-Bauer aus Modulen.
  - Freiflaechen (Stationen, Tuergaenge, Laufwege) bleiben leer. Das Skript
    PRUEFT das selbst (freiflaechen_pruefen) und meldet jede Verletzung laut.

Koordinaten in allen Moebel-Funktionen: GODOT lokal, Vorderseite blickt nach
+z, Ursprung Mitte unten. Platziert wird mit setzen(name, teile, x, z, dreh).
Drehung +90 heisst: die Vorderseite blickt danach nach +x.
"""

import bpy
import math
import os
import sys
from mathutils import Matrix

# Kein __pycache__ im Quellordner hinterlassen.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, profil_x, rundprofil,
    transformieren, alles_loeschen, verbinden, dreiecke, masse, exportieren,
    importieren, vorschau_rendern, palette_erweitern, modul_pfad,
    WURZEL, AUSGABE_VORSCHAU,
)

AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "zimmer")

# Toene der Einrichtung. Namen nach Stoff und Ton, nie nach Spielrolle (D3).
palette_erweitern({
    "holz_moebel":      ("#C8925A", 0.75, 0.0, 1.0),
    "holz_moebel_hell": ("#E2B983", 0.75, 0.0, 1.0),
    "holz_dunkel":      ("#8E623E", 0.80, 0.0, 1.0),
    "karton":           ("#C99A62", 0.90, 0.0, 1.0),
    "klebeband":        ("#EBD3A4", 0.60, 0.0, 1.0),
    "stoff_decke":      ("#7D90BE", 0.95, 0.0, 1.0),
    "stoff_weiss":      ("#F4EEE5", 0.90, 0.0, 1.0),
    "stoff_matratze":   ("#E9E1D4", 0.95, 0.0, 1.0),
    "stoff_senf":       ("#E0A33A", 0.90, 0.0, 1.0),
    "stoff_koralle":    ("#EE8F7E", 0.90, 0.0, 1.0),
    "stoff_petrol":     ("#3F8F8C", 0.90, 0.0, 1.0),
    "stoff_blau":       ("#4F7FB5", 0.90, 0.0, 1.0),
    "stoff_oliv":       ("#7A8A4E", 0.90, 0.0, 1.0),
    "stoff_hellblau":   ("#9FCBEA", 0.90, 0.0, 1.0),
    "stoff_gelb":       ("#FFD27A", 0.90, 0.0, 1.0),
    "stoff_grau":       ("#8B8580", 0.90, 0.0, 1.0),
    "teppich_creme":    ("#F3E6CF", 0.90, 0.0, 1.0),
    "teppich_terra":    ("#CF7454", 0.95, 0.0, 1.0),
    "pflanze":          ("#5DA84A", 0.80, 0.0, 1.0),
    "pflanze_dunkel":   ("#3E8A3B", 0.80, 0.0, 1.0),
    "pflanze_muede":    ("#AFB24A", 0.80, 0.0, 1.0),
    "topf_terra":       ("#C9744A", 0.85, 0.0, 1.0),
    "erde":             ("#5C4030", 0.95, 0.0, 1.0),
    "kunststoff_dunkel":("#383432", 0.55, 0.0, 1.0),
    "metall_hell":      ("#CCD1D6", 0.35, 0.40, 1.0),
    "metall_dunkel":    ("#4A4F57", 0.50, 0.30, 1.0),
    "lampe_licht":      ("#FFE2A0", 0.60, 0.0, 1.0),
    "akzent_gelb":      ("#FFB21E", 0.70, 0.0, 1.0),
    "akzent_rot":       ("#E0553D", 0.70, 0.0, 1.0),
    "akzent_gruen":     ("#3DBE4B", 0.70, 0.0, 1.0),
    "akzent_blau":      ("#4F9FD6", 0.70, 0.0, 1.0),
    "obst_orange":      ("#F29135", 0.60, 0.0, 1.0),
    "kueche_front":     ("#A9C9B3", 0.70, 0.0, 1.0),
    "kueche_weiss":     ("#F6F1E8", 0.70, 0.0, 1.0),
    "kuehlschrank":     ("#5E656D", 0.45, 0.30, 1.0),
    "keramik":          ("#FBFAF6", 0.30, 0.0, 1.0),
    "glas_dusche":      ("#CDEAF5", 0.10, 0.0, 0.35),
    "spiegel":          ("#CFE6EF", 0.10, 0.20, 1.0),
    "korb":             ("#C9A26E", 0.90, 0.0, 1.0),
    # Aliase: fast gleiche Toene teilen sich ein Material (weniger Draw Calls).
    # Die Namen bleiben im Code, damit man liest, WAS dort gemeint ist.
    "arbeitsplatte":    "holz_moebel",
    "karton_hell":      "holz_moebel_hell",
    "teppich_matte":    "holz_dunkel",
    "papier":           "stoff_weiss",
    "kunststoff_weiss": "stoff_weiss",
    "reifen":           "kunststoff_dunkel",
    "herd_schwarz":     "kunststoff_dunkel",
    "stoff_rot":        "akzent_rot",
    "topf_rot":         "akzent_rot",
    "obst_rot":         "akzent_rot",
    "chrom":            "metall_hell",
    "edelstahl":        "metall_hell",
    "topf_creme":       "teppich_creme",
    "pflanze_braun":    "korb",
    "obst_gelb":        "stoff_gelb",
    "pizza_teig":       "stoff_gelb",
    "stoff_decke_hell": "stoff_hellblau",
    "stoff_rosa":       "stoff_koralle",
})


# --- Buchfuehrung -----------------------------------------------------------------
# Jedes Moebel wird mit Namen registriert: so zaehlt das Skript die Dreiecke je
# Moebel (Budget 600) und kann Freiflaechen-Verletzungen beim Namen nennen.

MOEBEL = []   # [(name, [objekte])]
MOEBEL_BUDGET = 600
ZONEN_BUDGET = 12000


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


def moebel_bericht():
    gesamt = 0
    print("    %-26s %5s  %s" % ("Moebel", "Dr.", "Godot-BBox x | y | z"))
    for name, teile in MOEBEL:
        n = 0
        punkte = []
        for t in teile:
            k, w = _auswerten(t)
            n += k
            punkte += w
        gesamt += n
        gx = [p.x for p in punkte]
        gy = [p.z for p in punkte]
        gz = [-p.y for p in punkte]
        warnung = "  <-- UEBER BUDGET" if n > MOEBEL_BUDGET else ""
        print("    %-26s %5d  %+.2f..%+.2f | %.2f..%.2f | %+.2f..%+.2f%s"
              % (name, n, min(gx), max(gx), min(gy), max(gy), min(gz), max(gz), warnung))
    return gesamt


def freiflaechen_pruefen(zone):
    """Meldet jedes Teil, das eine Freiflaeche schneidet (ausser flachen
    Teppichen <= 0,02 m) oder durch eine Wand ragt. Ein Teil zaehlt nur, wenn
    es die Flaeche um mehr als 1 cm anschneidet -- Beruehren ist erlaubt."""
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
            y1 = max(p.z for p in punkte)
            if y1 > 0.021:
                for (fx, fz, fb, ft, was) in zone["frei"]:
                    if (x1 > fx - fb / 2 + toleranz and x0 < fx + fb / 2 - toleranz and
                            z1 > fz - ft / 2 + toleranz and z0 < fz + ft / 2 - toleranz):
                        print("    FREIFLAECHE VERLETZT: %s/%s schneidet '%s'" % (name, t.name, was))
                        fehler += 1
            if name in zone.get("aussen_erlaubt", ()):
                continue
            if x0 < -hx - toleranz or x1 > hx + toleranz or z0 < -hz - toleranz or z1 > hz + toleranz:
                print("    RAGT IN DIE WAND: %s/%s  x %+.2f..%+.2f  z %+.2f..%+.2f"
                      % (name, t.name, x0, x1, z0, z1))
                fehler += 1
    return fehler


# --- Zonen --------------------------------------------------------------------------
# waende: seite -> (typ, {position_entlang_der_wand: sondermodul})
# frei:   (x, z, breite, tiefe, beschreibung) in Zonenkoordinaten

def _tuergang_hinten(x, z_wand, tiefe=1.0):
    return (x, z_wand + tiefe / 2.0, 1.2, tiefe, "Tuer hinten x=%g" % x)


def _tuergang_vorn(x, z_wand, tiefe=1.0):
    return (x, z_wand - tiefe / 2.0, 1.2, tiefe, "Tuer vorn x=%g" % x)


ZONEN = {
    "zimmer": {
        "breite": 7.0, "tiefe": 7.0, "welt": (0.0, 4.0), "boden": "holz",
        "waende": {
            "hinten": ("halb", {0.0: "tuer"}),
            "links": ("halb", {}),
            "rechts": ("halb", {}),
            "vorn": ("sockel", {}),
        },
        "frei": [
            (-2.0, -2.3, 2.2, 2.2, "Station hinten links"),
            (1.8, -2.2, 2.2, 2.2, "Station hinten rechts"),
            (0.0, 0.6, 2.2, 2.2, "Station Mitte"),
            (0.0, -2.0, 1.2, 3.0, "Tuergang"),
        ],
        "ortho": 11.0,
    },
    "flur": {
        "breite": 23.0, "tiefe": 4.0, "welt": (0.0, -1.5), "boden": "flur",
        "waende": {
            "hinten": ("halb", {-9.0: "tuer", 0.0: "tuer", 5.0: "tuer", 9.0: "tuer"}),
            "vorn": ("halb", {-8.0: "tuer", 0.0: "tuer", 7.0: "tuer"}),
            "links": ("voll", {}),
            "rechts": ("sockel", {0.5: "tuer"}),
        },
        "frei": [
            (2.6, -1.1, 1.8, 1.4, "Station an der Wand"),
            (0.0, 0.4, 23.0, 1.6, "Laufgang"),
            _tuergang_hinten(-9.0, -2.0), _tuergang_hinten(0.0, -2.0),
            _tuergang_hinten(5.0, -2.0), _tuergang_hinten(9.0, -2.0),
            _tuergang_vorn(-8.0, 2.0), _tuergang_vorn(0.0, 2.0), _tuergang_vorn(7.0, 2.0),
            (11.0, 0.5, 1.0, 1.2, "Wohnungstuer"),
        ],
        "ortho": 20.0,
    },
    "kueche": {
        "breite": 6.0, "tiefe": 6.0, "welt": (0.5, -6.5), "boden": "fliese",
        "waende": {
            "hinten": ("voll", {-0.5: "fenster"}),
            "links": ("halb", {1.5: "tuer"}),
            "rechts": ("halb", {}),
            "vorn": ("halb", {-0.5: "tuer"}),
        },
        "frei": [
            (-0.5, 2.25, 1.2, 1.5, "Tuergang vorn"),
            (-2.25, 1.5, 1.5, 1.2, "Tuergang links"),
            (0.5, -1.9, 0.8, 0.8, "Kochplatz"),
        ],
        "ortho": 9.5,
    },
    "bad": {
        "breite": 4.0, "tiefe": 6.0, "welt": (5.5, -6.5), "boden": "bad",
        "waende": {
            # Fenster laut Auftrag bei x = 0 -- das ist aber eine Feldkante
            # (Zonenbreite 4). Ein 1-m-Modul sitzt auf Feldmitten, also x = +0,5.
            "hinten": ("voll", {0.5: "fenster"}),
            "links": ("halb", {}),
            "rechts": ("halb", {}),
            "vorn": ("halb", {-0.5: "tuer"}),
        },
        "frei": [
            (-0.5, 2.25, 1.2, 1.5, "Tuergang vorn"),
        ],
        "ortho": 8.8,
    },
}


def huelle_module(zone):
    """Liefert die Wand- und Bodenmodule einer Zone als Liste von
    (modul, welt_x, welt_z, drehung, rang) -- nur fuer die Vorschau.
    rang entscheidet, welches Modul gewinnt, wenn zwei Zonen dieselbe
    Kante belegen (Tuer/Fenster schlaegt Wand, hohe Wand schlaegt niedrige)."""
    wx, wz = zone["welt"]
    b, t = zone["breite"], zone["tiefe"]
    rang_typ = {"voll": 3, "halb": 2, "sockel": 1}
    liste = []
    for seite, (typ, sonder) in zone["waende"].items():
        if seite in ("hinten", "vorn"):
            anzahl = int(round(b))
            z = -t / 2 if seite == "hinten" else t / 2
            dreh = 0.0 if seite == "hinten" else 180.0
            for i in range(anzahl):
                x = -b / 2 + 0.5 + i
                art = _sonder(sonder, x)
                modul = "wg_wand_%s%s" % (typ, "_" + art if art else "")
                liste.append((modul, wx + x, wz + z, dreh, rang_typ[typ] + (10 if art else 0)))
        else:
            anzahl = int(round(t))
            x = -b / 2 if seite == "links" else b / 2
            dreh = 90.0 if seite == "links" else -90.0
            for i in range(anzahl):
                z = -t / 2 + 0.5 + i
                art = _sonder(sonder, z)
                modul = "wg_wand_%s%s" % (typ, "_" + art if art else "")
                liste.append((modul, wx + x, wz + z, dreh, rang_typ[typ] + (10 if art else 0)))
    # Eckpfosten: Typ der hoeheren der beiden anstossenden Waende.
    for sx, sz, s1, s2 in ((-1, -1, "links", "hinten"), (1, -1, "rechts", "hinten"),
                           (-1, 1, "links", "vorn"), (1, 1, "rechts", "vorn")):
        typ = max(zone["waende"][s1][0], zone["waende"][s2][0], key=lambda k: rang_typ[k])
        liste.append(("wg_pfosten_" + typ, wx + sx * b / 2, wz + sz * t / 2, 0.0, rang_typ[typ]))
    # Boden im Schachbrett a/b.
    for i in range(int(round(b))):
        for k in range(int(round(t))):
            x = -b / 2 + 0.5 + i
            z = -t / 2 + 0.5 + k
            gx, gz = int(math.floor(wx + x)), int(math.floor(wz + z))
            ab = "a" if (gx + gz) % 2 == 0 else "b"
            liste.append(("wg_boden_%s_%s" % (zone["boden"], ab), wx + x, wz + z, 0.0, 0))
    return liste


def _sonder(sonder, pos):
    for p, art in sonder.items():
        if abs(p - pos) < 0.01:
            return art
    return ""


def huellen_aufstellen(zonen_namen):
    """Stellt Module fuer mehrere Zonen auf; doppelt belegte Kanten nur einmal."""
    belegt = {}
    for name in zonen_namen:
        for modul, x, z, dreh, rang in huelle_module(ZONEN[name]):
            ist_boden = modul.startswith("wg_boden")
            schluessel = (round(x, 2), round(z, 2), "b" if ist_boden else "w")
            if schluessel in belegt and belegt[schluessel][3] >= rang:
                continue
            belegt[schluessel] = (modul, x, z, rang, dreh)
    for modul, x, z, rang, dreh in belegt.values():
        importieren(modul_pfad(modul), x=x, z=z, dreh_grad=dreh)


# ==============================================================================
# KLEINTEILE, DIE IN MEHREREN RAEUMEN VORKOMMEN
# ==============================================================================

def stab(name, a, b, dicke, mat, rund=0.0):
    """Vierkantstab von Godot-Punkt a nach b (Fahrradrahmen, Beine, Griffe)."""
    pa, pb = G(*a), G(*b)
    richtung = pb - pa
    laenge = richtung.length
    obj = kasten(name, (dicke, laenge, dicke), (0, 0, 0), mat, rund=rund, segmente=1)
    dreh = richtung.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    obj.matrix_world = Matrix.Translation((pa + pb) / 2.0) @ dreh
    return obj


def pflanze(groesse=1.0, topf="topf_terra", stil="busch"):
    """Topfpflanze. stil 'busch' = runde Blattballen, 'hoch' = schlanke
    Zimmerpalme mit Blattbueschel. Kraeftiges Gruen #5DA84A laut Vertrag."""
    s = groesse
    teile = [
        zylinder("topf", 0.13 * s, 0.24 * s, (0, 0, 0), topf, seiten=10, radius_oben=0.16 * s),
        zylinder("topfrand", 0.168 * s, 0.04 * s, (0, 0.22 * s, 0), topf, seiten=10),
        zylinder("erde", 0.145 * s, 0.01, (0, 0.245 * s, 0), "erde", seiten=10),
    ]
    if stil == "mini":
        return [
            zylinder("topf", 0.13 * s, 0.26 * s, (0, 0, 0), topf, seiten=8, radius_oben=0.16 * s),
            kugel("blatt", 0.2 * s, (0.0, 0.4 * s, 0.0), "pflanze", stauchung=0.9, ringe=4, seiten=7),
        ]
    if stil == "busch":
        teile += [
            kugel("blatt_a", 0.2 * s, (0.0, 0.42 * s, 0.0), "pflanze", stauchung=0.85, ringe=5, seiten=8),
            kugel("blatt_b", 0.15 * s, (0.12 * s, 0.56 * s, 0.05 * s), "pflanze_dunkel", ringe=4, seiten=7),
            kugel("blatt_c", 0.13 * s, (-0.1 * s, 0.6 * s, -0.06 * s), "pflanze", ringe=4, seiten=7),
        ]
    else:
        teile.append(zylinder("stamm", 0.025 * s, 0.55 * s, (0, 0.24 * s, 0), "pflanze_braun", seiten=6))
        for i, (dx, dz, r, m) in enumerate(((0, 0, 0.2, "pflanze"), (0.14, 0.05, 0.14, "pflanze_dunkel"),
                                             (-0.12, 0.08, 0.13, "pflanze"), (0.02, -0.13, 0.13, "pflanze_dunkel"))):
            teile.append(kugel("wedel_%d" % i, r * s, (dx * s, (0.85 + 0.12 * (i % 2)) * s, dz * s), m,
                               stauchung=0.6, ringe=4, seiten=7))
    return teile


def karton(b=0.5, h=0.38, t=0.4, mat="karton", klebe=True):
    """Umzugskarton mit Klebestreifen quer ueber den Deckel -- der Streifen
    macht aus einer Kiste erst einen Karton."""
    teile = [kasten("karton", (b, h, t), (0, h / 2, 0), mat, rund=0.012, segmente=1)]
    if klebe:
        teile.append(kasten("klebe", (0.07, 0.004, t + 0.004), (0, h + 0.001, 0), "klebeband"))
        teile.append(kasten("klebe_vorn", (0.07, 0.12, 0.004), (0, h - 0.06, t / 2 + 0.002), "klebeband"))
    return teile


def teppich(b, t, mat, rand_mat=None, h=0.015):
    """Flacher Teppich, hoechstens 0,02 hoch -- darf in Freiflaechen liegen."""
    teile = [kasten("teppich", (b, h, t), (0, h / 2, 0), mat, rund=0.006, segmente=1)]
    if rand_mat:
        for s in (-1, 1):
            teile.append(kasten("streifen", (b - 0.12, 0.003, 0.06), (0, h + 0.0005, s * (t / 2 - 0.12)), rand_mat))
    return teile


def tasse(mat="akzent_rot"):
    return [
        zylinder("tasse", 0.038, 0.085, (0, 0, 0), mat, seiten=8),
        kasten("henkel", (0.02, 0.045, 0.012), (0.045, 0.045, 0), mat),
    ]


def buchstapel(n=3):
    farben = ["akzent_blau", "stoff_senf", "stoff_petrol", "akzent_rot"]
    teile = []
    y = 0.0
    for i in range(n):
        d = 0.035 + 0.01 * (i % 2)
        teile.append(kasten("buch_%d" % i, (0.2 - 0.02 * i, d, 0.26 - 0.015 * i),
                            (0.01 * (i % 2), y + d / 2, 0.0), farben[i % 4]))
        transformieren([teile[-1]], dreh_grad=(i * 11.0) - 8.0)
        y += d
    return teile


# ==============================================================================
# DEIN ZIMMER -- bescheiden, gemuetlich, jung
# ==============================================================================

def matratze():
    """Matratze direkt auf dem Boden, Kopfende bei lokal -z. Die Decke ist
    zurueckgeschlagen und leicht schief -- hier wurde gerade aufgestanden."""
    teile = [
        kasten("matratze", (1.3, 0.2, 2.0), (0, 0.1, 0), "stoff_matratze", rund=0.05, segmente=2),
        kasten("decke", (1.36, 0.06, 1.25), (0.0, 0.225, 0.35), "stoff_decke", rund=0.03, segmente=2),
        kasten("decke_umschlag", (1.36, 0.05, 0.28), (0.0, 0.265, -0.2), "stoff_decke_hell", rund=0.022, segmente=1),
        kasten("kissen", (0.62, 0.13, 0.36), (-0.18, 0.26, -0.72), "stoff_weiss", rund=0.055, segmente=2),
        kasten("kissen_2", (0.5, 0.11, 0.32), (0.34, 0.25, -0.76), "stoff_senf", rund=0.05, segmente=1),
    ]
    transformieren([teile[1], teile[2]], dreh_grad=3.0)
    transformieren([teile[4]], x=0.0, dreh_grad=-9.0)
    return teile


def nachttisch_kiste():
    """Umzugskiste als Nachttisch: Lampe, Tasse, Buecher. Noch nicht einmal
    ausgepackt, aber schon Moebel."""
    teile = karton(0.55, 0.42, 0.42, "karton")
    teile += [
        zylinder("lampe_fuss", 0.065, 0.02, (-0.13, 0.42, -0.04), "kunststoff_dunkel", seiten=8),
        zylinder("lampe_stiel", 0.012, 0.26, (-0.13, 0.44, -0.04), "kunststoff_dunkel", seiten=5, deckel=False),
        zylinder("lampe_schirm", 0.13, 0.15, (-0.13, 0.64, -0.04), "lampe_licht", seiten=10, radius_oben=0.085),
    ]
    becher = transformieren(tasse("stoff_petrol"), x=0.16, y=0.42, z=0.1)
    buecher = transformieren(buchstapel(2), x=0.14, y=0.42, z=-0.06, dreh_grad=20)
    return teile + becher + buecher


def waeschestaender():
    """Waeschestaender mit Waesche: zwei A-Boecke, sechs Leinen, darueber
    T-Shirts, Handtuch, Socken. Entlang lokal x, 1,1 lang."""
    teile = []
    for sx in (-0.52, 0.52):
        for sz in (-1, 1):
            m_neigung = kasten("bein", (0.025, 0.98, 0.025), (0, 0.49, 0), "metall_hell")
            # Neigung um die x-Achse: Blender-x ist Godot-x, Winkel mit Vorzeichen.
            m_neigung.matrix_world = (Matrix.Translation(G(sx, 0, sz * 0.24)) @
                                      Matrix.Rotation(math.radians(-sz * 14.0), 4, "X") @
                                      m_neigung.matrix_world)
            teile.append(m_neigung)
    teile.append(kasten("holm_l", (0.03, 0.03, 0.62), (-0.52, 0.93, 0), "metall_hell"))
    teile.append(kasten("holm_r", (0.03, 0.03, 0.62), (0.52, 0.93, 0), "metall_hell"))
    for i in range(6):
        z = -0.27 + i * 0.108
        teile.append(kasten("leine_%d" % i, (1.04, 0.012, 0.012), (0, 0.935, z), "metall_hell"))
    waesche = [
        (-0.3, -0.27, 0.34, 0.36, "stoff_hellblau"),
        (0.08, -0.05, 0.30, 0.30, "stoff_weiss"),
        (0.36, 0.16, 0.22, 0.44, "stoff_koralle"),
        (-0.36, 0.16, 0.08, 0.16, "stoff_gelb"),
        (-0.22, 0.16, 0.08, 0.16, "stoff_gelb"),
    ]
    for x, z, b, h, m in waesche:
        teile.append(kasten("waesche", (b, h, 0.03), (x, 0.935 - h / 2 + 0.01, z), m, rund=0.012, segmente=1))
    return teile


def pflanze_muede():
    """Die Pflanze, die es gerade so schafft: gelbliche, haengende Blaetter,
    eines ist schon auf den Boden gefallen. Traurig, aber nicht tot."""
    teile = [
        zylinder("topf", 0.1, 0.2, (0, 0, 0), "topf_terra", seiten=9, radius_oben=0.125),
        zylinder("erde", 0.115, 0.01, (0, 0.19, 0), "erde", seiten=9),
        zylinder("stiel", 0.012, 0.36, (0, 0.2, 0), "pflanze_braun", seiten=5, deckel=False),
    ]
    blaetter = [
        (0.0, 0.58, 0.0, 0.11, "pflanze_muede", 0.0),
        (0.1, 0.46, 0.04, 0.08, "pflanze", 0.0),
        (-0.11, 0.42, -0.03, 0.08, "pflanze_muede", 0.0),
    ]
    for x, y, z, r, m, _ in blaetter:
        teile.append(kugel("blatt", r, (x, y, z), m, stauchung=0.45, ringe=4, seiten=6))
    teile.append(kugel("blatt_gefallen", 0.06, (0.2, 0.012, 0.12), "pflanze_braun", stauchung=0.2, ringe=3, seiten=6))
    return teile


def pizzakarton():
    """Pizzakarton, Deckel hochgeklappt, ein letztes Stueck liegt noch drin."""
    teile = [kasten("boden", (0.38, 0.035, 0.38), (0, 0.0175, 0), "karton_hell", rund=0.006, segmente=1)]
    deckel = kasten("deckel", (0.38, 0.012, 0.38), (0, 0.006, 0.19), "karton_hell")
    deckel.matrix_world = (Matrix.Translation(G(0, 0.035, -0.19)) @
                           Matrix.Rotation(math.radians(-105.0), 4, "X") @ deckel.matrix_world)
    teile.append(deckel)
    teile.append(zylinder("logo", 0.07, 0.003, (0, 0.036, 0.0), "akzent_rot", seiten=8))
    stueck = zylinder("stueck", 0.13, 0.014, (0, 0.036, 0), "pizza_teig", seiten=3)
    transformieren([stueck], x=0.02, z=0.03, dreh_grad=25.0)
    belag = zylinder("belag", 0.025, 0.006, (0.05, 0.05, 0.06), "akzent_rot", seiten=6)
    teile += [stueck, belag]
    return teile


def poster_angelehnt():
    """Poster ohne Schrift, an die Wand gelehnt (Rueckseite lokal -z):
    Himmel, Sonne, Berg -- ein Motiv, keine Botschaft."""
    b, h = 0.62, 0.86
    platte = [
        kasten("rahmen", (b, h, 0.025), (0, h / 2, 0), "holz_moebel_hell", rund=0.008, segmente=1),
        kasten("bild", (b - 0.08, h - 0.08, 0.004), (0, h / 2, 0.014), "stoff_hellblau"),
        kasten("berg_fuss", (b - 0.08, 0.2, 0.005), (0, 0.14, 0.017), "stoff_petrol"),
        zylinder("sonne", 0.09, 0.006, (0, 0, 0), "akzent_gelb", seiten=10),
    ]
    sonne = platte[3]
    sonne.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    sonne.matrix_world = Matrix.Translation(G(0.12, 0.6, 0.02))
    berg = zylinder("berg", 0.22, 0.006, (0, 0, 0), "pflanze", seiten=3)
    berg.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    berg.data.transform(Matrix.Rotation(math.radians(-90), 4, "Y"))
    berg.matrix_world = Matrix.Translation(G(-0.08, 0.3, 0.021))
    platte.append(berg)
    neig = Matrix.Translation(G(0, 0, 0.19)) @ Matrix.Rotation(math.radians(-12.0), 4, "X")
    for p in platte:
        p.matrix_world = neig @ p.matrix_world
    return platte


def rucksack():
    """Rucksack, Rueckseite an der Wand (lokal -z), Vorderseite blickt +z.
    Gross genug, dass er aus der Kartenansicht als Rucksack lesbar ist:
    runder Korpus, Deckelklappe, Fronttasche, Tragegriff."""
    teile = [
        kasten("korpus", (0.4, 0.5, 0.24), (0, 0.25, 0), "stoff_senf", rund=0.08, segmente=2),
        kasten("tasche", (0.3, 0.2, 0.08), (0, 0.16, 0.13), "stoff_rot", rund=0.035, segmente=1),
        kasten("klappe", (0.36, 0.12, 0.27), (0, 0.46, 0.02), "stoff_rot", rund=0.045, segmente=2),
        kasten("griff", (0.12, 0.05, 0.03), (0, 0.54, -0.03), "kunststoff_dunkel"),
        kasten("gurt_l", (0.05, 0.4, 0.03), (-0.11, 0.26, -0.12), "kunststoff_dunkel"),
        kasten("gurt_r", (0.05, 0.4, 0.03), (0.11, 0.26, -0.12), "kunststoff_dunkel"),
    ]
    neig = Matrix.Translation(G(0, 0, 0.02)) @ Matrix.Rotation(math.radians(-8.0), 4, "X")
    for t in teile:
        t.matrix_world = neig @ t.matrix_world
    return teile


def sneaker_paar():
    """Zwei Sneaker, stilisiert gross, nicht ordentlich nebeneinander."""
    teile = []
    for i, (x, z, dreh) in enumerate(((0.0, 0.0, 10.0), (0.24, 0.1, -32.0))):
        schuh = [
            kasten("sohle", (0.14, 0.04, 0.34), (0, 0.02, 0), "kunststoff_weiss", rund=0.015, segmente=1),
            kasten("schaft", (0.13, 0.1, 0.24), (0, 0.09, -0.04), "stoff_blau", rund=0.04, segmente=1),
            kasten("kappe", (0.12, 0.05, 0.1), (0, 0.06, 0.11), "stoff_weiss", rund=0.02, segmente=1),
            kasten("lasche", (0.07, 0.03, 0.08), (0, 0.15, 0.02), "stoff_weiss"),
        ]
        transformieren(schuh, x=x, z=z, dreh_grad=dreh)
        teile += schuh
    return teile


def sitzsack():
    """Sitzsack -- der Sessel, den man sich mit zwanzig leisten kann."""
    teile = [
        kugel("sack", 0.46, (0, 0.24, 0), "stoff_petrol", stauchung=0.55, ringe=6, seiten=12),
        kugel("mulde", 0.3, (0.02, 0.36, 0.06), "stoff_petrol", stauchung=0.45, ringe=4, seiten=10),
    ]
    teile += transformieren(buchstapel(1), x=0.42, z=0.3, dreh_grad=30.0)
    return teile


def gitarre():
    """Gitarre, an die Wand gelehnt (Rueckseite lokal -z)."""
    teile = [
        liegender_zylinder("korpus_u", 0.17, 0.09, (0, 0.22, 0), "z", "holz_moebel_hell", seiten=12),
        liegender_zylinder("korpus_o", 0.13, 0.09, (0, 0.46, 0), "z", "holz_moebel_hell", seiten=12),
        liegender_zylinder("schallloch", 0.05, 0.094, (0, 0.36, 0), "z", "holz_dunkel", seiten=8),
        kasten("steg", (0.1, 0.02, 0.01), (0, 0.2, 0.048), "holz_dunkel"),
        kasten("hals", (0.05, 0.46, 0.035), (0, 0.8, 0), "holz_dunkel"),
        kasten("kopf", (0.08, 0.13, 0.03), (0, 1.08, -0.005), "holz_dunkel", rund=0.01, segmente=1),
    ]
    neig = Matrix.Translation(G(0, 0, 0.24)) @ Matrix.Rotation(math.radians(-12.0), 4, "X")
    for t in teile:
        t.matrix_world = neig @ t.matrix_world
    return teile


def kleiderstange():
    """Offene Kleiderstange statt Schrank, entlang lokal x: T-Shirts und ein
    Hoodie auf Buegeln, darunter ein Karton mit Pullis. 1,5 hoch -- sie ragt
    ueber die halbhohe Wand, damit man sie von der Kamera aus sieht."""
    laenge = 1.3
    teile = []
    for sx in (-laenge / 2, laenge / 2):
        teile.append(kasten("pfosten", (0.035, 1.5, 0.035), (sx, 0.75, 0), "metall_dunkel"))
        teile.append(kasten("fuss", (0.04, 0.03, 0.45), (sx, 0.015, 0), "metall_dunkel"))
    teile.append(kasten("stange", (laenge + 0.04, 0.03, 0.03), (0, 1.48, 0), "metall_dunkel"))
    kleider = [(-0.48, "stoff_weiss", 0.55), (-0.28, "stoff_senf", 0.6), (-0.06, "kunststoff_dunkel", 0.72),
               (0.16, "stoff_hellblau", 0.55), (0.36, "stoff_koralle", 0.6)]
    for x, m, lang in kleider:
        teile.append(kasten("kleid", (0.12, lang, 0.36), (x, 1.44 - lang / 2, 0), m, rund=0.03, segmente=1))
    teile += transformieren(karton(0.5, 0.3, 0.4, "karton_hell", klebe=False), x=0.2)
    teile.append(kasten("pulli", (0.38, 0.06, 0.3), (0.2, 0.32, 0.0), "stoff_rot", rund=0.02, segmente=1))
    return teile


def steckdosenleiste_kabel():
    """Steckdosenleiste mitten im Zimmer, zu viele Stecker. Die Kabel liegen
    flach (1 cm) und laufen in die Stationsflaechen hinein -- flach ist dort
    erlaubt, und genau so sieht ein Zimmer aus, in dem alles am Strom haengt."""
    teile = [
        kasten("leiste", (0.44, 0.05, 0.11), (0, 0.025, 0), "kunststoff_weiss", rund=0.012, segmente=1),
        kasten("schalter", (0.05, 0.02, 0.04), (0.17, 0.055, 0), "akzent_rot"),
    ]
    for i, x in enumerate((-0.15, -0.06, 0.03, 0.1)):
        m = "kunststoff_dunkel" if i % 2 == 0 else "kunststoff_weiss"
        teile.append(kasten("stecker", (0.06, 0.06, 0.06), (x, 0.075, 0), m))
    k = "kunststoff_dunkel"
    teile += [
        kasten("kabel_a1", (0.02, 0.012, 0.5), (-0.15, 0.006, -0.3), k),
        kasten("kabel_a2", (0.3, 0.012, 0.02), (-0.01, 0.006, -0.55), k),
        kasten("kabel_a3", (0.02, 0.012, 0.6), (0.13, 0.006, -0.85), k),
        kasten("kabel_b1", (0.02, 0.012, 0.3), (-0.06, 0.006, 0.2), "kunststoff_weiss"),
        kasten("kabel_b2", (0.62, 0.012, 0.02), (-0.36, 0.006, 0.35), "kunststoff_weiss"),
        kasten("kabel_b3", (0.02, 0.012, 0.35), (-0.67, 0.006, 0.52), "kunststoff_weiss"),
        kasten("kabel_c1", (0.9, 0.01, 0.018), (0.66, 0.005, 0.04), k),
    ]
    return teile


def stehlampe():
    """Bogenlampe mit warmem Schirm -- das einzige gekaufte Moebel im Zimmer."""
    teile = [
        zylinder("fuss", 0.16, 0.03, (0, 0, 0), "kunststoff_dunkel", seiten=10),
        zylinder("stange", 0.018, 1.35, (0, 0.03, 0), "metall_dunkel", seiten=6, deckel=False),
        stab("arm", (0, 1.36, 0), (-0.32, 1.52, 0), 0.03, "metall_dunkel"),
        zylinder("schirm", 0.17, 0.2, (-0.36, 1.28, 0), "lampe_licht", seiten=12, radius_oben=0.08),
    ]
    return teile


def einrichtung_zimmer():
    """Dein Zimmer, 7 x 7. Freiflaechen: drei Stationen und der Tuergang.

    Sichtregel aus der ersten Vorschau: Die Kamera schaut von +x/+z. Alles, was
    niedrig an der RECHTEN oder VORDEREN Wand steht, verschwindet hinter der
    Wand. Deshalb steht das Erzaehlende an der linken Wand und vorn im Raum;
    rechts nur, was ueber die Wand hinausragt (Kleiderstange)."""
    # Linke Wand, von vorn nach hinten: Matratze, Kiste, Pflanze, Poster, Gitarre, Rucksack
    setzen("matratze", matratze(), x=-2.38, z=2.6, dreh=90.0)
    setzen("nachttisch_kiste", nachttisch_kiste(), x=-3.08, z=1.45, dreh=90.0)
    setzen("pflanze_muede", pflanze_muede(), x=-3.12, z=0.92)
    setzen("poster", poster_angelehnt(), x=-3.38, z=0.28, dreh=90.0)
    setzen("gitarre", gitarre(), x=-3.36, z=-0.38, dreh=90.0)
    setzen("rucksack", rucksack(), x=-3.2, z=-0.92, dreh=90.0)
    setzen("teppich", teppich(1.6, 1.1, "teppich_creme", "teppich_terra"), x=-1.95, z=0.55, dreh=90.0)
    # Vorn: Sitzsack, Pizza, Sneaker, Waeschestaender, Kartons
    setzen("sitzsack", sitzsack(), x=0.3, z=2.62)
    setzen("pizzakarton", pizzakarton(), x=-0.85, z=3.0, dreh=12.0)
    setzen("sneaker", sneaker_paar(), x=-0.72, z=2.08, dreh=-20.0)
    setzen("waeschestaender", waeschestaender(), x=1.98, z=2.5, dreh=0.0)
    setzen("kartons_gestapelt", karton(0.55, 0.4, 0.45) + transformieren(
        karton(0.45, 0.32, 0.38, "karton_hell"), y=0.4, dreh_grad=14.0), x=2.78, z=3.08)
    # Rechts: Kleiderstange ueber die Wand hinaus; Mitte: Steckdosenleiste
    setzen("kleiderstange", kleiderstange(), x=3.1, z=0.25, dreh=-90.0)
    setzen("steckdosenleiste", steckdosenleiste_kabel(), x=1.55, z=-0.6)
    setzen("stehlampe", stehlampe(), x=2.75, z=1.45, dreh=150.0)


# ==============================================================================
# FLUR -- lang, praktisch, bewohnt
# ==============================================================================

def fahrrad():
    """Fahrrad in Seitenansicht entlang lokal x (Vorderrad bei +x), die
    Seite blickt nach +z. Petrol-Rahmen, dunkle Reifen, helle Felgen."""
    teile = []
    r = 0.28
    for x in (-0.45, 0.45):
        teile.append(liegender_zylinder("reifen", r, 0.05, (x, r, 0), "z", "reifen", seiten=14))
        teile.append(liegender_zylinder("felge", r - 0.06, 0.054, (x, r, 0), "z", "metall_hell", seiten=12))
        teile.append(liegender_zylinder("nabe", 0.04, 0.07, (x, r, 0), "z", "kunststoff_dunkel", seiten=6))
    tretlager = (-0.06, 0.28, 0.0)
    sattel_rohr = (-0.18, 0.74, 0.0)
    lenker_rohr = (0.32, 0.76, 0.0)
    teile += [
        stab("unterrohr", tretlager, lenker_rohr, 0.045, "stoff_petrol"),
        stab("oberrohr", sattel_rohr, lenker_rohr, 0.04, "stoff_petrol"),
        stab("sitzrohr", tretlager, sattel_rohr, 0.045, "stoff_petrol"),
        stab("hinterbau", tretlager, (-0.45, r, 0.0), 0.035, "stoff_petrol"),
        stab("sitzstrebe", sattel_rohr, (-0.45, r, 0.0), 0.03, "stoff_petrol"),
        stab("gabel", lenker_rohr, (0.45, r, 0.0), 0.04, "stoff_petrol"),
        stab("sattelstuetze", sattel_rohr, (-0.21, 0.86, 0.0), 0.025, "metall_hell"),
        kasten("sattel", (0.24, 0.05, 0.12), (-0.2, 0.89, 0.0), "kunststoff_dunkel", rund=0.02, segmente=1),
        stab("vorbau", lenker_rohr, (0.29, 0.91, 0.0), 0.03, "metall_hell"),
        kasten("lenker", (0.035, 0.035, 0.4), (0.29, 0.92, 0.0), "metall_hell"),
        kasten("korb", (0.18, 0.14, 0.24), (0.5, 0.76, 0.0), "korb", rund=0.015, segmente=1),
        liegender_zylinder("kurbel", 0.07, 0.06, tretlager, "z", "kunststoff_dunkel", seiten=8),
    ]
    return teile


def spiegel_wand():
    """Spiegel mit Holzrahmen, Unterkante 0,85, Rueckseite lokal -z."""
    return [
        kasten("rahmen", (0.5, 0.95, 0.04), (0, 1.325, 0), "holz_moebel", rund=0.015, segmente=2),
        kasten("glas", (0.4, 0.85, 0.01), (0, 1.325, 0.022), "spiegel"),
        kasten("glanz", (0.06, 0.5, 0.004), (-0.1, 1.42, 0.028), "kunststoff_weiss"),
    ]


def schuhregal():
    """Offenes Schuhregal, 1,0 breit, 0,55 hoch, voller Schuhe, oben eine
    kleine Pflanze."""
    b, h, t = 1.0, 0.55, 0.32
    teile = [
        kasten("seite_l", (0.03, h, t), (-b / 2 + 0.015, h / 2, 0), "holz_moebel_hell"),
        kasten("seite_r", (0.03, h, t), (b / 2 - 0.015, h / 2, 0), "holz_moebel_hell"),
        kasten("deckel", (b, 0.035, t + 0.02), (0, h - 0.0175, 0), "holz_moebel_hell", rund=0.012, segmente=1),
        kasten("brett", (b - 0.06, 0.025, t), (0, 0.27, 0), "holz_moebel_hell"),
        kasten("brett_u", (b - 0.06, 0.025, t), (0, 0.03, 0), "holz_moebel_hell"),
    ]
    farben = ["stoff_rot", "stoff_weiss", "stoff_blau", "stoff_senf", "kunststoff_dunkel", "stoff_oliv"]
    k = 0
    for y in (0.0425, 0.2825):
        for i in range(3):
            x = -0.32 + i * 0.32
            m = farben[k % len(farben)]
            k += 1
            for dx in (-0.055, 0.055):
                teile.append(kasten("schuh", (0.09, 0.075, 0.24), (x + dx, y + 0.0375, 0.02), m))
    teile += transformieren(pflanze(0.55, "topf_creme"), x=0.32, y=h, z=0.0)
    return teile


def fussmatte():
    return teppich(0.75, 0.48, "teppich_matte", "klebeband", h=0.016)


def garderobe():
    """Hakenleiste mit Jacken ueber einer Sitzbank. Oberkante 1,12 -- die
    halbhohe Wand bleibt hoeher als alles, was an ihr haengt.
    Rueckseite an der Wand (lokal -z)."""
    teile = [
        kasten("leiste", (1.3, 0.12, 0.03), (0, 1.06, -0.12), "holz_moebel", rund=0.01, segmente=1),
    ]
    for i in range(5):
        teile.append(kasten("haken", (0.03, 0.03, 0.06), (-0.5 + i * 0.25, 1.03, -0.08), "metall_dunkel"))
    jacken = [(-0.5, "stoff_senf", 0.58), (-0.22, "stoff_blau", 0.66), (0.25, "stoff_oliv", 0.62)]
    for x, m, lang in jacken:
        teile.append(kasten("jacke", (0.34, lang, 0.13), (x, 1.02 - lang / 2, -0.04), m, rund=0.04, segmente=1))
        teile.append(kasten("kragen", (0.2, 0.08, 0.15), (x, 1.0, -0.04), m, rund=0.03, segmente=1))
    teile.append(kasten("schal", (0.09, 0.5, 0.03), (0.5, 0.8, -0.07), "stoff_rot"))
    # Sitzbank
    teile.append(kasten("bank", (1.1, 0.05, 0.38), (0, 0.42, 0.04), "holz_moebel_hell", rund=0.015, segmente=1))
    for sx in (-0.5, 0.5):
        teile.append(kasten("bank_bein", (0.05, 0.4, 0.32), (sx, 0.2, 0.04), "holz_moebel_hell"))
    teile.append(kasten("bank_kissen", (0.42, 0.06, 0.32), (0.25, 0.475, 0.05), "stoff_koralle", rund=0.025, segmente=1))
    return teile


def kommode():
    """Kommode mit drei Schubladen; oben Schluesselschale, Bilderrahmen,
    kleine Pflanze. Rueckseite lokal -z."""
    b, h, t = 1.1, 0.78, 0.42
    teile = [
        kasten("korpus", (b, h - 0.08, t), (0, 0.08 + (h - 0.08) / 2, 0), "holz_moebel_hell", rund=0.02, segmente=2),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("fuss", (0.05, 0.08, 0.05), (sx * (b / 2 - 0.07), 0.04, sz * (t / 2 - 0.07)),
                                "holz_dunkel", unten=False))
    for i in range(3):
        y = 0.2 + i * 0.2
        teile.append(kasten("schublade", (b - 0.1, 0.16, 0.012), (0, y, t / 2 + 0.004), "holz_moebel"))
        teile.append(kasten("knauf", (0.1, 0.022, 0.03), (0, y, t / 2 + 0.02), "metall_dunkel"))
    teile.append(zylinder("schale", 0.12, 0.045, (0.2, h, 0.02), "stoff_petrol", seiten=10, radius_oben=0.15))
    teile.append(kasten("schluessel", (0.08, 0.012, 0.03), (0.2, h + 0.05, 0.03), "akzent_gelb"))
    foto = kasten("foto", (0.2, 0.25, 0.025), (0, 0.125, 0), "holz_dunkel", rund=0.006, segmente=1)
    bild = kasten("foto_bild", (0.15, 0.19, 0.004), (0, 0.125, 0.014), "stoff_hellblau")
    transformieren([foto, bild], x=-0.15, y=h, z=-0.1, dreh_grad=8.0)
    teile += [foto, bild]
    teile += transformieren(pflanze(0.5, "topf_creme"), x=-0.4, y=h, z=0.02)
    return teile


def schirmstaender():
    teile = [
        zylinder("staender", 0.11, 0.46, (0, 0, 0), "metall_dunkel", seiten=10, deckel=False),
        zylinder("staender_boden", 0.11, 0.02, (0, 0, 0), "metall_dunkel", seiten=10),
    ]
    for i, (dx, dz, m, neigung) in enumerate(((-0.03, 0.0, "stoff_rot", 8.0), (0.04, 0.02, "stoff_blau", -10.0))):
        schirm = [
            zylinder("schirm", 0.045, 0.62, (0, 0.05, 0), m, seiten=7, radius_oben=0.02),
            zylinder("stock", 0.01, 0.2, (0, 0.67, 0), "holz_dunkel", seiten=5),
            kasten("griff", (0.08, 0.025, 0.025), (0.03, 0.87, 0), "holz_dunkel"),
        ]
        for s in schirm:
            s.matrix_world = Matrix.Rotation(math.radians(neigung), 4, "Y") @ s.matrix_world
        transformieren(schirm, x=dx, z=dz)
        teile += schirm
    return teile


def paketstapel():
    """Drei Pakete, das oberste etwas verdreht, eines mit weissem Etikett."""
    teile = karton(0.6, 0.35, 0.45, "karton")
    oben = karton(0.45, 0.28, 0.36, "karton_hell")
    transformieren(oben, y=0.35, x=0.03, dreh_grad=-12.0)
    klein = karton(0.3, 0.18, 0.26, "karton", klebe=False)
    klein.append(kasten("etikett", (0.14, 0.004, 0.1), (0.0, 0.182, 0.0), "kunststoff_weiss"))
    transformieren(klein, y=0.63, x=-0.02, dreh_grad=20.0)
    daneben = karton(0.34, 0.22, 0.3, "karton_hell")
    transformieren(daneben, x=0.55, z=0.05, dreh_grad=8.0)
    return teile + oben + klein + daneben


def heizkoerper():
    """Rippenheizkoerper an der Wand, Rueckseite lokal -z, Oberkante 0,72."""
    teile = [kasten("ruecken", (0.9, 0.5, 0.04), (0, 0.45, -0.06), "kunststoff_weiss")]
    for i in range(7):
        x = -0.39 + i * 0.13
        teile.append(kasten("rippe", (0.08, 0.54, 0.07), (x, 0.45, -0.01), "kunststoff_weiss", rund=0.02, segmente=1))
    teile.append(kasten("ventil", (0.04, 0.06, 0.04), (0.47, 0.25, -0.01), "chrom"))
    return teile


def sitzbank():
    """Schmale Holzbank mit Kissen und einer abgelegten Muetze."""
    teile = [
        kasten("sitz", (1.2, 0.05, 0.36), (0, 0.43, 0), "holz_moebel", rund=0.015, segmente=1),
        kasten("kissen", (0.5, 0.07, 0.3), (-0.28, 0.49, 0.0), "stoff_hellblau", rund=0.03, segmente=1),
        kugel("muetze", 0.09, (0.3, 0.46, 0.0), "stoff_senf", stauchung=0.7, ringe=4, seiten=8),
    ]
    for sx in (-0.52, 0.52):
        for sz in (-0.13, 0.13):
            teile.append(kasten("bein", (0.04, 0.41, 0.04), (sx, 0.205, sz), "holz_dunkel", unten=False))
    return teile


def einrichtung_flur():
    """Flur 23 x 4. Der Laufgang (z -0,4..1,2) geht ueber die ganze Laenge,
    vor jeder Tuer bleibt 1,2 x 1,0 frei. Moebel stehen deshalb in einem
    1,5 m tiefen Streifen an der hinteren Wand. Die vordere Wand verdeckt aus
    der Kamera alles unter ~0,9 m -- dort stehen nur hohe Pflanzen."""
    # Linke Stirnwand (volle Wand): Fahrrad hinten, Spiegel vorn -- beide ausserhalb des Laufgangs.
    setzen("fahrrad", fahrrad(), x=-11.19, z=-1.15, dreh=90.0)
    setzen("spiegel", spiegel_wand(), x=-11.38, z=1.55, dreh=90.0)
    setzen("pflanze_hinten_links", pflanze(1.0, "topf_creme", "hoch"), x=-10.25, z=-1.58)
    setzen("pflanze_vorn_links", pflanze(1.15, "topf_terra", "hoch"), x=-10.0, z=1.6)
    # Hinten zwischen Tuer x=-9 und x=0
    setzen("paketstapel", paketstapel(), x=-7.55, z=-1.5, dreh=4.0)
    setzen("sitzbank", sitzbank(), x=-5.4, z=-1.68)
    setzen("heizkoerper", heizkoerper(), x=-3.3, z=-1.8)
    setzen("pflanze_hinten_mitte", pflanze(0.9), x=-1.55, z=-1.62)
    setzen("laeufer_links", teppich(2.6, 0.8, "teppich_terra", "teppich_creme"), x=-4.6, z=0.45)
    # Hinten zwischen Tuer x=0 und x=5: kleine Pflanze, Station, hohe Pflanze
    setzen("pflanze_tuer_mitte", pflanze(0.8, "topf_terra"), x=1.15, z=-1.65)
    setzen("pflanze_station", pflanze(1.0, "topf_creme", "hoch"), x=4.0, z=-1.62)
    setzen("pflanze_vorn_mitte", pflanze(1.15, "topf_terra", "hoch"), x=4.6, z=1.6)
    setzen("laeufer_rechts", teppich(2.2, 0.8, "teppich_creme", "teppich_terra"), x=7.0, z=0.45)
    # Hinten zwischen Tuer x=5 und x=9: Garderobe mit Bank, Kommode mit Schluesselschale
    setzen("garderobe", garderobe(), x=6.35, z=-1.72)
    setzen("kommode", kommode(), x=7.78, z=-1.69)
    # Hinten rechts an der Wohnungstuer: Schuhregal, Schirmstaender, Fussmatte
    setzen("schuhregal", schuhregal(), x=10.55, z=-1.72)
    setzen("schirmstaender", schirmstaender(), x=11.23, z=-1.55)
    setzen("fussmatte", fussmatte(), x=10.95, z=0.5, dreh=90.0)


# ==============================================================================
# KUECHE -- salbeigruene Unterschraenke, Holzplatte, warmes Chaos
# ==============================================================================
# Die Kuechenzeile steht an der vollen Rueckwand. Masse in Zonenkoordinaten:
# Wandflaeche z = -2,9; Korpus bis z = -2,34; Arbeitsplatte bis -2,32 (der
# Kochplatz beginnt bei -2,3); Arbeitsplatte Oberkante 0,86 -- die
# Fensterbank des Fenstermoduls liegt bei 0,86..0,90 direkt darueber.
# Alle Teile der Zeile werden in ZONENkoordinaten gebaut (setzen ohne Versatz).

WAND_Z = -2.9
KORPUS_VORN = -2.34
PLATTE_VORN = -2.32
PLATTE_OBEN = 0.86


def _unterschrank(x0, x1, fronten, griff_mat="metall_dunkel"):
    """Korpus mit Sockel und Fronten; fronten = Liste von (x0, x1, y0, y1)."""
    tz = KORPUS_VORN - WAND_Z
    mz = (WAND_Z + KORPUS_VORN) / 2
    teile = [
        kasten("sockel", (x1 - x0, 0.1, tz - 0.06), ((x0 + x1) / 2, 0.05, mz - 0.03), "herd_schwarz", unten=False),
        kasten("korpus", (x1 - x0, 0.72, tz), ((x0 + x1) / 2, 0.46, mz), "kueche_front", rund=0.008, segmente=1),
    ]
    for fx0, fx1, fy0, fy1 in fronten:
        teile.append(kasten("front", (fx1 - fx0 - 0.02, fy1 - fy0 - 0.02, 0.018),
                            ((fx0 + fx1) / 2, (fy0 + fy1) / 2, KORPUS_VORN + 0.009), "kueche_front",
                            rund=0.006, segmente=1))
        hoch = (fy1 - fy0) > 0.3
        if hoch:
            teile.append(kasten("griff", (0.02, 0.14, 0.02), (fx1 - 0.06, fy1 - 0.12, KORPUS_VORN + 0.028), griff_mat))
        else:
            teile.append(kasten("griff", (0.16, 0.02, 0.02), ((fx0 + fx1) / 2, fy1 - 0.05, KORPUS_VORN + 0.028), griff_mat))
    return teile


def arbeitsplatte():
    return [kasten("platte", (5.1, 0.04, WAND_Z * -1 + PLATTE_VORN), (-0.35, PLATTE_OBEN - 0.02,
                   (WAND_Z + PLATTE_VORN) / 2), "arbeitsplatte", rund=0.012, segmente=2)]


def unterschraenke_links():
    return _unterschrank(-2.9, -0.8, [(-2.9, -2.2, 0.1, 0.82), (-2.2, -1.5, 0.1, 0.82),
                                      (-1.5, -0.8, 0.1, 0.46), (-1.5, -0.8, 0.46, 0.82)])


def spuele():
    """Spuele unter dem Fenster: Unterschrank, Edelstahlbecken als flache
    Einlage, Armatur VOR der Fensterbank, damit sie nicht hindurchsticht."""
    teile = _unterschrank(-0.8, 0.2, [(-0.8, -0.2, 0.1, 0.82), (-0.2, 0.2, 0.1, 0.82)])
    teile += [
        kasten("becken_rand", (0.56, 0.008, 0.44), (-0.5, PLATTE_OBEN + 0.004, -2.57), "edelstahl"),
        kasten("becken", (0.44, 0.004, 0.32), (-0.5, PLATTE_OBEN + 0.009, -2.56), "metall_dunkel"),
        zylinder("hahn", 0.02, 0.26, (-0.5, PLATTE_OBEN, -2.73), "chrom", seiten=6),
        kasten("auslauf", (0.03, 0.03, 0.16), (-0.5, PLATTE_OBEN + 0.25, -2.66), "chrom"),
        kasten("hebel", (0.02, 0.02, 0.08), (-0.46, PLATTE_OBEN + 0.2, -2.74), "chrom"),
        # Geschirrtuch ueber dem Fronten-Griff rechts neben der Spuele
        kasten("tuch", (0.2, 0.34, 0.012), (0.0, 0.62, KORPUS_VORN + 0.04), "stoff_weiss", rund=0.004, segmente=1),
        kasten("tuch_streifen", (0.2, 0.04, 0.004), (0.0, 0.54, KORPUS_VORN + 0.047), "stoff_rot"),
    ]
    return teile


def herd():
    """Herd mit Backofen: schwarzes Kochfeld, vier Platten, Topf mit Deckel
    und Kochloeffel, Backofentuer mit Glasfenster und Stange."""
    x0, x1 = 0.2, 0.8
    mx = (x0 + x1) / 2
    tz = KORPUS_VORN - WAND_Z
    mz = (WAND_Z + KORPUS_VORN) / 2
    teile = [
        kasten("sockel", (x1 - x0, 0.1, tz - 0.06), (mx, 0.05, mz - 0.03), "herd_schwarz", unten=False),
        kasten("gehaeuse", (x1 - x0, 0.72, tz), (mx, 0.46, mz), "edelstahl", rund=0.008, segmente=1),
        kasten("ofen_tuer", (0.54, 0.46, 0.02), (mx, 0.37, KORPUS_VORN + 0.01), "herd_schwarz", rund=0.01, segmente=1),
        kasten("ofen_glas", (0.38, 0.24, 0.006), (mx, 0.36, KORPUS_VORN + 0.022), "kunststoff_dunkel"),
        kasten("ofen_stange", (0.44, 0.022, 0.022), (mx, 0.56, KORPUS_VORN + 0.029), "chrom"),
        kasten("blende", (0.56, 0.1, 0.012), (mx, 0.74, KORPUS_VORN + 0.006), "herd_schwarz"),
        kasten("kochfeld", (0.58, 0.012, 0.5), (mx, PLATTE_OBEN + 0.006, -2.6), "herd_schwarz"),
    ]
    for i, dx in enumerate((-0.18, -0.06, 0.06, 0.18)):
        teile.append(kasten("knopf", (0.04, 0.04, 0.02), (mx + dx, 0.74, KORPUS_VORN + 0.022), "stoff_grau"))
    for (dx, z, r) in ((-0.14, -2.73, 0.085), (0.14, -2.73, 0.065), (-0.14, -2.47, 0.065), (0.14, -2.47, 0.085)):
        teile.append(zylinder("platte", r, 0.004, (mx + dx, PLATTE_OBEN + 0.012, z), "stoff_grau", seiten=10))
    # Topf auf der hinteren linken Platte
    tx, tz_ = mx - 0.14, -2.73
    teile += [
        zylinder("topf", 0.11, 0.13, (tx, PLATTE_OBEN + 0.016, tz_), "topf_rot", seiten=12),
        zylinder("deckel", 0.115, 0.02, (tx, PLATTE_OBEN + 0.146, tz_), "edelstahl", seiten=12, radius_oben=0.06),
        kugel("deckel_knauf", 0.02, (tx, PLATTE_OBEN + 0.175, tz_), "herd_schwarz", ringe=3, seiten=6),
        kasten("topf_griff_l", (0.05, 0.02, 0.03), (tx - 0.13, PLATTE_OBEN + 0.12, tz_), "herd_schwarz"),
        kasten("topf_griff_r", (0.05, 0.02, 0.03), (tx + 0.13, PLATTE_OBEN + 0.12, tz_), "herd_schwarz"),
    ]
    loeffel = stab("loeffel", (mx + 0.08, PLATTE_OBEN + 0.02, -2.42), (mx + 0.26, PLATTE_OBEN + 0.02, -2.6),
                   0.022, "holz_moebel")
    teile.append(loeffel)
    return teile


def unterschraenke_rechts():
    return _unterschrank(0.8, 2.2, [(0.8, 1.5, 0.1, 0.46), (0.8, 1.5, 0.46, 0.82), (1.5, 2.2, 0.1, 0.82)])


def _oberschrank(x0, x1, tueren):
    tz = 0.34
    mz = WAND_Z + tz / 2
    y0, y1 = 1.45, 2.1
    teile = [kasten("korpus", (x1 - x0, y1 - y0, tz), ((x0 + x1) / 2, (y0 + y1) / 2, mz), "kueche_weiss",
                    rund=0.01, segmente=2)]
    breite = (x1 - x0) / tueren
    for i in range(tueren):
        fx = x0 + breite * (i + 0.5)
        teile.append(kasten("tuer", (breite - 0.03, y1 - y0 - 0.04, 0.014), (fx, (y0 + y1) / 2, WAND_Z + tz + 0.007),
                            "kueche_weiss"))
        gx = fx + (breite / 2 - 0.06) * (1 if i % 2 == 0 else -1)
        teile.append(kasten("griff", (0.02, 0.12, 0.02), (gx, y0 + 0.12, WAND_Z + tz + 0.024), "metall_dunkel"))
    return teile


def oberschraenke_links():
    """Links vom Fenster: zwei Tueren und ein offenes Brett mit Glaesern."""
    teile = _oberschrank(-2.9, -1.75, 2)
    teile.append(kasten("brett", (0.6, 0.03, 0.26), (-1.4, 1.62, WAND_Z + 0.13), "holz_moebel"))
    for i, (dx, m) in enumerate(((-0.2, "obst_orange"), (0.0, "stoff_senf"), (0.18, "akzent_rot"))):
        teile.append(zylinder("glas", 0.05, 0.14, (-1.4 + dx, 1.635, WAND_Z + 0.12), "kunststoff_weiss", seiten=8))
        teile.append(zylinder("inhalt", 0.052, 0.08, (-1.4 + dx, 1.635, WAND_Z + 0.12), m, seiten=8))
    teile += transformieren(pflanze(0.35, "topf_creme", "mini"), x=-1.4, y=1.3, z=WAND_Z + 0.13)
    teile.append(kasten("brett_u", (0.6, 0.03, 0.26), (-1.4, 1.285, WAND_Z + 0.13), "holz_moebel"))
    return teile


def oberschraenke_rechts():
    return _oberschrank(0.95, 2.2, 2)


def dunstabzug():
    return [
        kasten("haube", (0.66, 0.12, 0.46), (0.5, 1.62, WAND_Z + 0.23), "edelstahl", rund=0.02, segmente=2),
        kasten("kamin", (0.28, 0.66, 0.24), (0.5, 2.0, WAND_Z + 0.12), "edelstahl", rund=0.01, segmente=1),
        kasten("leuchte", (0.4, 0.006, 0.08), (0.5, 1.557, WAND_Z + 0.36), "lampe_licht"),
    ]


def kuehlschrank():
    """Kuehlschrank anthrazit, Gefrierfach oben, vier bunte Magnete und ein
    Zettel ohne Schrift. Vorderseite +z."""
    b, h, t = 0.64, 1.84, 0.64
    teile = [
        kasten("korpus", (b, h, t), (0, h / 2, 0), "kuehlschrank", rund=0.03, segmente=2),
        kasten("fuge", (b + 0.004, 0.012, 0.03), (0, 1.3, t / 2 - 0.01), "herd_schwarz"),
        kasten("griff_o", (0.03, 0.26, 0.03), (-b / 2 + 0.07, 1.5, t / 2 + 0.02), "chrom"),
        kasten("griff_u", (0.03, 0.4, 0.03), (-b / 2 + 0.07, 1.05, t / 2 + 0.02), "chrom"),
        kasten("zettel", (0.14, 0.18, 0.004), (0.08, 1.02, t / 2 + 0.002), "papier"),
    ]
    for (x, y, m) in ((0.08, 1.12, "akzent_rot"), (0.18, 1.45, "akzent_gelb"), (-0.05, 1.58, "akzent_gruen"),
                      (0.14, 0.72, "akzent_blau")):
        teile.append(kasten("magnet", (0.05, 0.05, 0.016), (x, y, t / 2 + 0.008), m, rund=0.008, segmente=1))
    return teile


def kaffeemaschine():
    teile = [
        kasten("fuss", (0.22, 0.04, 0.24), (0, 0.02, 0.02), "herd_schwarz", rund=0.01, segmente=1),
        kasten("turm", (0.22, 0.34, 0.1), (0, 0.17, -0.07), "herd_schwarz", rund=0.02, segmente=1),
        kasten("kopf", (0.22, 0.06, 0.22), (0, 0.33, 0.0), "herd_schwarz", rund=0.015, segmente=1),
        zylinder("kanne", 0.07, 0.13, (0, 0.04, 0.05), "spiegel", seiten=10, radius_oben=0.05),
        zylinder("kaffee", 0.072, 0.06, (0, 0.04, 0.05), "holz_dunkel", seiten=10),
        kasten("knopf", (0.03, 0.03, 0.01), (0.07, 0.26, -0.015), "akzent_rot"),
    ]
    teile += transformieren(tasse("stoff_weiss"), x=0.2, z=0.08)
    return teile


def kraeuter():
    """Drei Kraeutertoepfe fuer die Fensterbank, nebeneinander entlang x."""
    teile = []
    for i, (dx, m, r) in enumerate(((-0.16, "pflanze", 0.07), (0.0, "pflanze_dunkel", 0.06), (0.16, "pflanze", 0.075))):
        teile.append(zylinder("topf", 0.045, 0.08, (dx, 0, 0), "topf_terra", seiten=8, radius_oben=0.055))
        teile.append(kugel("kraut", r, (dx, 0.13, 0), m, stauchung=0.9, ringe=4, seiten=7))
    return teile


def muelleimer():
    return [
        zylinder("eimer", 0.14, 0.4, (0, 0, 0), "kunststoff_weiss", seiten=12),
        zylinder("deckel", 0.145, 0.04, (0, 0.4, 0), "edelstahl", seiten=12, radius_oben=0.12),
        kasten("pedal", (0.1, 0.02, 0.06), (0, 0.02, 0.16), "herd_schwarz"),
    ]


def esstisch():
    b, h, t = 1.05, 0.75, 0.72
    teile = [kasten("platte", (b, 0.05, t), (0, h - 0.025, 0), "holz_moebel_hell", rund=0.02, segmente=2)]
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(kasten("bein", (0.05, h - 0.05, 0.05), (sx * (b / 2 - 0.07), (h - 0.05) / 2, sz * (t / 2 - 0.07)),
                                "holz_moebel", unten=False))
    teile += transformieren(pflanze(0.5, "topf_creme"), x=-0.18, y=h, z=-0.05)
    teile += transformieren(tasse("akzent_gelb"), x=0.25, y=h, z=0.12)
    return teile


def stuhl(polster="stoff_koralle"):
    """Holzstuhl mit Sitzkissen, Lehne bei lokal -z, Sitzflaeche blickt +z."""
    teile = [
        kasten("sitz", (0.42, 0.04, 0.4), (0, 0.45, 0), "holz_moebel", rund=0.012, segmente=1),
        kasten("kissen", (0.36, 0.04, 0.34), (0, 0.49, 0.01), polster, rund=0.015, segmente=1),
        kasten("lehne", (0.42, 0.14, 0.03), (0, 0.8, -0.19), "holz_moebel", rund=0.012, segmente=1),
    ]
    for sx in (-0.18, 0.18):
        for sz in (-0.17, 0.17):
            hoch = 0.86 if sz < 0 else 0.43
            teile.append(kasten("bein", (0.035, hoch, 0.035), (sx, hoch / 2, sz), "holz_moebel", unten=False))
    return teile


def beistelltisch_obst():
    """Runder Beistelltisch mit Obstschale -- 'Obstschale und Pflanze vorn
    rechts'. Rund und frei stehend statt Sideboard an der Wand: an der
    rechten Wand verschwand das Sideboard in der Vorschau hinter der Wand."""
    h = 0.72
    teile = [
        zylinder("platte", 0.34, 0.04, (0, h - 0.04, 0), "holz_moebel_hell", seiten=14, rund=0.012, segmente=1),
        zylinder("saeule", 0.04, h - 0.06, (0, 0.03, 0), "holz_moebel", seiten=8, deckel=False),
        zylinder("fuss", 0.2, 0.03, (0, 0, 0), "holz_moebel", seiten=10),
        zylinder("schale", 0.13, 0.06, (0.02, h, 0.02), "stoff_petrol", seiten=10, radius_oben=0.18),
        kugel("apfel", 0.06, (-0.03, h + 0.09, 0.05), "obst_rot", ringe=4, seiten=7),
        kugel("orange", 0.062, (0.09, h + 0.09, -0.02), "obst_orange", ringe=4, seiten=7),
        kugel("apfel_2", 0.055, (0.0, h + 0.1, -0.07), "akzent_gruen", ringe=4, seiten=7),
        kasten("banane", (0.22, 0.045, 0.07), (0.03, h + 0.14, 0.02), "obst_gelb", rund=0.02, segmente=1),
    ]
    return teile


def kuechenregal():
    """Offenes Regal an der linken halbhohen Wand, 0,9 hoch (mit Topfpflanze 1,16 -- unter der Wandkappe): Kochbuecher,
    Vorratsglaeser, ein Korb Kartoffeln. Rueckseite lokal -z."""
    b, h, t = 0.8, 0.9, 0.34
    teile = [
        kasten("seite_l", (0.03, h, t), (-b / 2 + 0.015, h / 2, 0), "holz_moebel"),
        kasten("seite_r", (0.03, h, t), (b / 2 - 0.015, h / 2, 0), "holz_moebel"),
    ]
    for y in (0.02, 0.33, 0.62, h - 0.015):
        teile.append(kasten("brett", (b, 0.03, t), (0, y, 0), "holz_moebel", rund=0.008 if y > 0.9 else 0.0,
                            segmente=1))
    teile += transformieren(buchstapel(3), x=-0.18, y=0.345, dreh_grad=90.0)
    for i, (dx, m) in enumerate(((0.06, "stoff_senf"), (0.2, "pizza_teig"))):
        teile.append(zylinder("glas", 0.055, 0.18, (dx, 0.635, 0), "kunststoff_weiss", seiten=8))
        teile.append(zylinder("vorrat", 0.057, 0.11, (dx, 0.635, 0), m, seiten=8))
    teile.append(kasten("korb", (0.36, 0.2, 0.28), (0.1, 0.135, 0), "korb", rund=0.02, segmente=1))
    for dx in (-0.02, 0.1, 0.2):
        teile.append(kugel("kartoffel", 0.05, (dx, 0.25, 0.02), "pflanze_braun", stauchung=0.8, ringe=3, seiten=6))
    teile += transformieren(pflanze(0.45, "topf_terra", "mini"), x=0.2, y=h, z=0.0)
    return teile


def einrichtung_kueche():
    """Kueche 6 x 6. Zeile hinten (Tueren- und Kochplatz-frei), Tisch rechts
    in der Mitte, Sideboard und Pflanze vorn rechts, Regal links."""
    setzen("arbeitsplatte", arbeitsplatte())
    setzen("unterschraenke_links", unterschraenke_links())
    setzen("spuele", spuele())
    setzen("herd", herd())
    setzen("unterschraenke_rechts", unterschraenke_rechts())
    setzen("oberschraenke_links", oberschraenke_links())
    setzen("oberschraenke_rechts", oberschraenke_rechts())
    setzen("dunstabzug", dunstabzug())
    setzen("kuehlschrank", kuehlschrank(), x=2.56, z=-2.56)
    setzen("kaffeemaschine", kaffeemaschine(), x=-2.1, y=PLATTE_OBEN, z=-2.68)
    setzen("kraeuter", kraeuter(), x=-0.5, y=0.9, z=-2.82)
    setzen("muelleimer", muelleimer(), x=-2.7, z=-1.8, dreh=90.0)
    setzen("teppich", teppich(1.9, 1.5, "teppich_creme", "stoff_petrol"), x=1.35, z=0.5)
    setzen("esstisch", esstisch(), x=1.35, z=0.5)
    setzen("stuhl_hinten", stuhl("stoff_koralle"), x=1.35, z=-0.12)
    setzen("stuhl_links", stuhl("stoff_senf"), x=0.62, z=0.5, dreh=90.0)
    setzen("stuhl_rechts", stuhl("stoff_petrol"), x=2.1, z=0.62, dreh=-100.0)
    # Pflanze hinter (nicht vor) den Beistelltisch: aus der Kamera (+x/+z)
    # verdeckte sie ihn in der zweiten Vorschau vollstaendig.
    setzen("beistelltisch_obst", beistelltisch_obst(), x=1.7, z=2.35)
    setzen("pflanze_vorn_rechts", pflanze(1.25, "topf_terra", "hoch"), x=2.55, z=1.75)
    setzen("kuechenregal", kuechenregal(), x=-2.72, z=-0.5, dreh=90.0)


# ==============================================================================
# BAD -- klein, hell, blau-weiss
# ==============================================================================

def dusche():
    """Bodengleiche Duschwanne, blaue Fliesenwand hinten, Glaswand an der
    rechten Seite (lokal +x), Brausestange an der vollen Rueckwand.
    Ursprung = Mitte der Wanne, Rueckwand bei lokal z = -0,5."""
    teile = [
        kasten("wanne", (0.98, 0.06, 0.98), (0, 0.03, 0), "keramik", rund=0.015, segmente=2),
        kasten("ablauf", (0.12, 0.004, 0.12), (0, 0.062, 0.1), "chrom"),
        kasten("fliesen", (0.98, 1.94, 0.012), (0, 0.06 + 0.97, -0.484), "fliese_blau"),
        kasten("glas", (0.012, 1.86, 0.9), (0.475, 0.06 + 0.93, -0.03), "glas_dusche"),
        kasten("profil_o", (0.03, 0.03, 0.92), (0.475, 1.93, -0.03), "chrom"),
        kasten("profil_v", (0.03, 1.87, 0.03), (0.475, 0.995, 0.425), "chrom"),
        kasten("stange", (0.025, 1.0, 0.025), (-0.12, 1.3, -0.455), "chrom"),
        kasten("arm", (0.025, 0.025, 0.16), (-0.12, 1.8, -0.39), "chrom"),
        zylinder("brause", 0.08, 0.025, (-0.12, 1.77, -0.32), "chrom", seiten=10),
        kasten("mischer", (0.14, 0.06, 0.05), (-0.12, 1.0, -0.455), "chrom", rund=0.01, segmente=1),
    ]
    for dx, m, hoehe in ((-0.36, "stoff_petrol", 0.16), (-0.28, "stoff_rosa", 0.13), (-0.21, "kunststoff_weiss", 0.11)):
        teile.append(zylinder("flasche", 0.03, hoehe, (dx, 0.06, -0.4), m, seiten=7))
    return teile


def wc():
    """WC, Spuelkasten an der Wand (lokal -z), Schuessel blickt +z."""
    teile = [
        kasten("kasten", (0.42, 0.42, 0.17), (0, 0.6, -0.2), "keramik", rund=0.03, segmente=2),
        kasten("taste", (0.12, 0.012, 0.07), (0, 0.816, -0.2), "chrom"),
        zylinder("fuss", 0.13, 0.28, (0, 0, 0.06), "keramik", seiten=10, radius_oben=0.17),
        kasten("schuessel", (0.38, 0.12, 0.46), (0, 0.33, 0.04), "keramik", rund=0.08, segmente=2),
        kasten("deckel", (0.36, 0.03, 0.44), (0, 0.405, 0.05), "keramik", rund=0.012, segmente=1),
        kasten("rollenhalter", (0.14, 0.12, 0.12), (0.34, 0.55, -0.24), "stoff_weiss", rund=0.04, segmente=1),
    ]
    return teile


def waschtisch():
    """Waschtisch mit Holz-Unterschrank, Keramikbecken, Armatur, Zahnputz-
    becher; darueber Spiegelschrank mit Leuchte. Rueckseite lokal -z."""
    b, t = 0.64, 0.46
    teile = [
        kasten("unterschrank", (b, 0.55, t - 0.02), (0, 0.1 + 0.275, -0.01), "holz_moebel_hell", rund=0.015, segmente=2),
        kasten("tuer_l", (b / 2 - 0.03, 0.47, 0.012), (-b / 4, 0.38, t / 2 - 0.014), "holz_moebel"),
        kasten("tuer_r", (b / 2 - 0.03, 0.47, 0.012), (b / 4, 0.38, t / 2 - 0.014), "holz_moebel"),
        kasten("becken", (b - 0.02, 0.12, t), (0, 0.71, 0), "keramik", rund=0.04, segmente=2),
        kasten("mulde", (0.4, 0.004, 0.26), (0, 0.772, 0.04), "spiegel"),
        zylinder("hahn", 0.018, 0.16, (0, 0.77, -0.17), "chrom", seiten=6),
        kasten("auslauf", (0.028, 0.028, 0.1), (0, 0.92, -0.13), "chrom"),
        zylinder("becher", 0.035, 0.1, (0.22, 0.77, -0.15), "stoff_petrol", seiten=8),
        kasten("buerste", (0.012, 0.12, 0.012), (0.23, 0.88, -0.15), "akzent_gelb"),
        # Spiegelschrank
        kasten("spiegelschrank", (0.62, 0.6, 0.14), (0, 1.62, -0.16), "kunststoff_weiss", rund=0.015, segmente=2),
        kasten("spiegel_l", (0.28, 0.54, 0.008), (-0.15, 1.62, -0.086), "spiegel"),
        kasten("spiegel_r", (0.28, 0.54, 0.008), (0.15, 1.62, -0.086), "spiegel"),
        kasten("leuchte", (0.5, 0.04, 0.06), (0, 1.95, -0.13), "lampe_licht", rund=0.012, segmente=1),
    ]
    return teile


def waschmaschine():
    """Waschmaschine, Vorderseite +z: Bullauge, Bedienleiste, Knopf."""
    b, h, t = 0.6, 0.85, 0.58
    teile = [
        kasten("korpus", (b, h, t), (0, h / 2, 0), "keramik", rund=0.03, segmente=2),
        kasten("leiste", (b - 0.06, 0.1, 0.01), (0, h - 0.08, t / 2 + 0.004), "stoff_grau"),
        liegender_zylinder("knopf", 0.035, 0.03, (0.18, h - 0.08, t / 2 + 0.015), "z", "chrom", seiten=8),
        kasten("anzeige", (0.12, 0.04, 0.006), (-0.1, h - 0.08, t / 2 + 0.01), "herd_schwarz"),
        liegender_zylinder("ring", 0.19, 0.03, (0, 0.38, t / 2 + 0.012), "z", "stoff_grau", seiten=14),
        liegender_zylinder("bullauge", 0.14, 0.03, (0, 0.38, t / 2 + 0.02), "z", "spiegel", seiten=14),
        liegender_zylinder("waesche", 0.09, 0.02, (-0.02, 0.35, t / 2 + 0.024), "z", "stoff_koralle", seiten=8),
    ]
    return teile


def waeschekorb():
    return [
        zylinder("korb", 0.19, 0.46, (0, 0, 0), "korb", seiten=10, radius_oben=0.22),
        kugel("waesche_a", 0.13, (-0.04, 0.47, 0.02), "stoff_hellblau", stauchung=0.6, ringe=4, seiten=7),
        kugel("waesche_b", 0.1, (0.08, 0.5, -0.05), "stoff_weiss", stauchung=0.6, ringe=4, seiten=7),
        kasten("socke", (0.05, 0.03, 0.18), (0.14, 0.44, 0.1), "stoff_gelb", rund=0.012, segmente=1),
    ]


def handtuchheizkoerper():
    """Handtuchheizkoerper, Oberkante 1,1, mit einem Handtuch ueber den
    oberen Sprossen. Rueckseite lokal -z."""
    b = 0.5
    teile = []
    for sx in (-b / 2, b / 2):
        teile.append(kasten("holm", (0.035, 0.9, 0.035), (sx, 0.65, -0.03), "kunststoff_weiss"))
    for i in range(6):
        teile.append(kasten("sprosse", (b, 0.022, 0.022), (0, 0.26 + i * 0.16, -0.03), "kunststoff_weiss"))
    teile.append(kasten("handtuch", (0.4, 0.46, 0.05), (0.0, 0.82, 0.0), "stoff_petrol", rund=0.02, segmente=1))
    teile.append(kasten("handtuch_kante", (0.4, 0.04, 0.056), (0.0, 0.64, 0.0), "stoff_weiss"))
    return teile


def regal_handtuecher():
    """Schmales Regal mit gerollten Handtuechern und einem Korb, 0,95 hoch."""
    b, h, t = 0.6, 0.95, 0.32
    teile = [
        kasten("seite_l", (0.03, h, t), (-b / 2 + 0.015, h / 2, 0), "holz_moebel_hell"),
        kasten("seite_r", (0.03, h, t), (b / 2 - 0.015, h / 2, 0), "holz_moebel_hell"),
    ]
    for y in (0.03, 0.34, 0.64, h - 0.015):
        teile.append(kasten("brett", (b, 0.03, t), (0, y, 0), "holz_moebel_hell"))
    for i, (dx, m) in enumerate(((-0.14, "stoff_petrol"), (0.0, "stoff_weiss"), (0.14, "stoff_gelb"))):
        teile.append(liegender_zylinder("rolle", 0.06, 0.26, (dx, 0.415, 0.0), "z", m, seiten=8))
    teile.append(kasten("korb", (0.4, 0.16, 0.26), (0, 0.125, 0), "korb", rund=0.02, segmente=1))
    teile.append(zylinder("flasche", 0.035, 0.14, (-0.12, 0.655, 0.0), "stoff_rosa", seiten=7))
    teile.append(zylinder("dose", 0.045, 0.08, (0.08, 0.655, 0.02), "kunststoff_weiss", seiten=8))
    return teile


def teppich_rund(radius, mat, ring_mat):
    """Runder Badteppich, 1,4 cm flach, mit hellem Ring."""
    return [
        zylinder("teppich", radius, 0.012, (0, 0, 0), mat, seiten=16),
        zylinder("ring", radius * 0.72, 0.002, (0, 0.012, 0), ring_mat, seiten=16),
        zylinder("mitte", radius * 0.62, 0.0025, (0, 0.0125, 0), mat, seiten=16),
    ]


def einrichtung_bad():
    """Bad 4 x 6. Dusche hinten links, Handtuchheizkoerper an der vollen
    Rueckwand zwischen Dusche und Fenster, Waschtisch rechts neben dem
    Fenster. Links: WC, Waschmaschine, Waeschekorb. Rechts nur, was ueber die
    halbhohe Wand ragt oder weit genug davor steht (Sichtregel)."""
    setzen("dusche", dusche(), x=-1.4, z=-2.41)
    setzen("handtuchheizkoerper", handtuchheizkoerper(), x=-0.43, z=-2.84)
    setzen("waschtisch", waschtisch(), x=1.4, z=-2.66)
    setzen("pflanze_fensterbank", pflanze(0.42, "topf_creme", "mini"), x=0.78, y=0.9, z=-2.8)
    setzen("badematte", teppich(0.78, 0.5, "stoff_koralle", "stoff_weiss"), x=-1.3, z=-1.5)
    setzen("wc", wc(), x=-1.6, z=-0.7, dreh=90.0)
    setzen("waschmaschine", waschmaschine(), x=-1.59, z=0.4, dreh=90.0)
    setzen("waeschekorb", waeschekorb(), x=-1.64, z=1.12)
    setzen("regal_handtuecher", regal_handtuecher(), x=-1.73, z=1.95, dreh=90.0)
    setzen("pflanze_boden", pflanze(0.7, "topf_creme"), x=-1.62, z=2.66)
    setzen("teppich_rund", teppich_rund(0.55, "stoff_hellblau", "stoff_weiss"), x=0.35, z=0.1)
    setzen("pflanze_rechts_hoch", pflanze(1.3, "topf_terra", "hoch"), x=1.5, z=-0.6)
    setzen("pflanze_vorn_rechts", pflanze(1.0, "topf_creme"), x=1.45, z=2.5)


# ==============================================================================
# ABLAUF
# ==============================================================================

EINRICHTUNGEN = {
    "zimmer": einrichtung_zimmer,
    "flur": einrichtung_flur,
    "kueche": einrichtung_kueche,
    "bad": einrichtung_bad,
}


def einrichtung_pfad(zone):
    return os.path.join(AUSGABE, "einrichtung_%s.glb" % zone)


def zone_bauen(name):
    alles_loeschen()
    del MOEBEL[:]
    zone = ZONEN[name]
    EINRICHTUNGEN[name]()
    print("")
    print("=== EINRICHTUNG %s (%g x %g) ===" % (name.upper(), zone["breite"], zone["tiefe"]))
    summe = moebel_bericht()
    fehler = freiflaechen_pruefen(zone)
    obj = verbinden([t for _, teile in MOEBEL for t in teile], "einrichtung_%s" % name)
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    pfad = einrichtung_pfad(name)
    exportieren(obj, pfad)
    print("  -> %s" % os.path.relpath(pfad, WURZEL))
    print("     %d Dreiecke (Budget %d)%s, %d Materialien, %.0f KB"
          % (n, ZONEN_BUDGET, "  <-- UEBER BUDGET" if n > ZONEN_BUDGET else "",
             len(obj.data.materials), os.path.getsize(pfad) / 1024.0))
    print("     BBox x %+.2f..%+.2f  y %.2f..%.2f  z %+.2f..%+.2f" % (x0, x1, y0, y1, z0, z1))
    print("     Freiflaechen-/Wandpruefung: %s" % ("OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler))
    return summe, fehler


def zone_vorschau(name):
    """Zone allein, lokal um den Nullpunkt: Module der Huelle plus die
    exportierte Einrichtung."""
    alles_loeschen()
    zone = dict(ZONEN[name])
    zone["welt"] = (0.0, 0.0)
    belegt = huelle_module(zone)
    for modul, x, z, dreh, _ in belegt:
        importieren(modul_pfad(modul), x=x, z=z, dreh_grad=dreh)
    importieren(einrichtung_pfad(name))
    freiflaechen_markieren(zone)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "einrichtung_%s.png" % name),
                     (0.0, 0.6, 0.0), zone["ortho"])


def freiflaechen_markieren(zone):
    """Nur in der Vorschau: Freiflaechen als zarte gruene Rahmen am Boden,
    damit man sieht, wo spaeter Stationen stehen und wo gelaufen wird."""
    palette_erweitern({"vorschau_frei": ("#6CC46A", 0.9, 0.0, 1.0)})
    for (fx, fz, fb, ft, _) in zone["frei"]:
        d = 0.04
        for (gx, gz, sb, st) in ((fx, fz - ft / 2 + d / 2, fb, d), (fx, fz + ft / 2 - d / 2, fb, d),
                                 (fx - fb / 2 + d / 2, fz, d, ft), (fx + fb / 2 - d / 2, fz, d, ft)):
            kasten("frei", (sb, 0.004, st), (gx, 0.003, gz), "vorschau_frei")


def gesamt_vorschau():
    """Alle vier Zonen an ihrer echten Weltposition."""
    alles_loeschen()
    namen = list(EINRICHTUNGEN)
    huellen_aufstellen(namen)
    for name in namen:
        wx, wz = ZONEN[name]["welt"]
        importieren(einrichtung_pfad(name), x=wx, z=wz)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "gesamt_team_a.png"), (1.5, 0.5, -1.2), 21.0)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    gewaehlt = [a for a in argumente if a in EINRICHTUNGEN] or list(EINRICHTUNGEN)
    ohne_vorschau = "--ohne-vorschau" in argumente
    nur_gesamt = "--nur-gesamt" in argumente
    fehler_gesamt = 0
    if not nur_gesamt:
        for name in gewaehlt:
            _, fehler = zone_bauen(name)
            fehler_gesamt += fehler
            if not ohne_vorschau:
                zone_vorschau(name)
    if not ohne_vorschau and (nur_gesamt or len(gewaehlt) == len(EINRICHTUNGEN)):
        gesamt_vorschau()
    print("")
    print("=== FERTIG: %s ===" % ("alle Freiflaechen frei" if fehler_gesamt == 0
                                  else "%d Verletzungen -- siehe oben" % fehler_gesamt))


if __name__ == "__main__":
    main()
