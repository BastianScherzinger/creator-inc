"""Architektur-Baukasten fuer Welt 4 (Lagerhalle), Nachtplan N30
(docs/NACHT_PLAN.md Abschnitte 2 und 5).

Aufruf:
    blender --background --python art_source/scripts/build_room_buero_neu.py
    (optional nach "--": --ohne-vorschau)

Erzeugt nach project/assets/room/buero/:
    boden_<typ>_a/_b   Bodenmodule 1 x 1 m, Oberkante y = 0, 0,06 dick nach unten
                       typ = hallenboden, hallenboden_linie, teppich, asphalt, fliese
    wand_*             Wandsegmente 1 m entlang lokal X, Ursprung unten Mitte,
                       Innenseite lokal +z (Masse wie wg_wand_* in room/zimmer)
    gelaender          Sicherheitsgelaender 1 m
    pfosten_*          Stahlstuetzen 0,22 x 0,22 (Kappe 0,27)
    raum_*             die sieben Altmodule fuer validate Schritt 7
und Uebersichten nach art_source/vorschau/buero/.

Jede Datei enthaelt GENAU EIN Mesh (MultiMesh-tauglich, siehe build_room_wg.py).

Bodenmodul hallenboden_linie: a und b tragen die gelbe Linie am hinteren Rand
(lokal z -0,46) an derselben Stelle, b zusaetzlich eine kurze Marke mittig.
So bleibt die Linie im Schachbrett (GrundrissBauer) durchgehend.

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
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, kugel, profil_x, rundprofil, kissen_platte, transformieren,
    alles_loeschen, verbinden, dreiecke, masse, exportieren, importieren,
    vorschau_rendern, palette_erweitern, _objekt, WURZEL,
)

AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "buero")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "buero")
HINTERGRUND = "#E4EEF0"

# Toene der Halle: kuehl-hell, Akzent Tuerkis #12B5A5. Namen nach Stoff und Ton.
# Keine Namen aus build_room_wg.PALETTE verwenden -- die haetten Vorrang.
palette_erweitern({
    "paneel_hell":      ("#D5DCE0", 0.70, 0.0, 1.0),
    "paneel_rille":     ("#CBD3D9", 0.80, 0.0, 1.0),
    "kappe_tuerkis":    ("#12B5A5", 0.55, 0.0, 1.0),
    "kappe_stahl":      ("#56626C", 0.55, 0.20, 1.0),
    "sockel_grau":      ("#66727D", 0.70, 0.0, 1.0),
    "rahmen_anthrazit": ("#4A5561", 0.45, 0.30, 1.0),
    "glas_kuehl":       ("#BCE5EE", 0.15, 0.0, 1.0),
    "stahl_blau":       ("#3F72B8", 0.45, 0.30, 1.0),
    "warn_gelb":        ("#FFC21A", 0.60, 0.0, 1.0),
    "warn_schwarz":     ("#2B2C33", 0.60, 0.0, 1.0),
    "gitter_stahl":     ("#7E8A96", 0.45, 0.40, 1.0),
    "halle_grau":       ("#9CA4AB", 0.55, 0.0, 1.0),
    "halle_fuge":       ("#858E95", 0.80, 0.0, 1.0),
    "halle_fleck_d":    ("#8E979E", 0.60, 0.0, 1.0),
    "halle_fleck_h":    ("#B3BAC0", 0.50, 0.0, 1.0),
    "linie_gelb":       ("#F7BD1E", 0.60, 0.0, 1.0),
    "teppich_blau":     ("#6E7E92", 0.95, 0.0, 1.0),
    "teppich_blau2":    ("#66768B", 0.95, 0.0, 1.0),
    "teppich_fuge":     ("#55657A", 0.95, 0.0, 1.0),
    "asphalt_grau":     ("#5E636B", 0.90, 0.0, 1.0),
    "asphalt_fleck":    ("#50555C", 0.90, 0.0, 1.0),
    "asphalt_hell":     ("#6D727A", 0.90, 0.0, 1.0),
    "asphalt_fuge":     ("#474B52", 0.95, 0.0, 1.0),
    "fliese_kalt":      ("#EEEFEC", 0.45, 0.0, 1.0),
    "fliese_kalt2":     ("#E2E6E4", 0.45, 0.0, 1.0),
    "fliese_kalt_fuge": ("#C4CACA", 0.90, 0.0, 1.0),
    "tuer_blech":       ("#4E6270", 0.55, 0.0, 1.0),
    "fliese_gruen":     ("#B9D6C0", 0.45, 0.0, 1.0),
    "fliese_gruen2":    ("#A8C8B1", 0.45, 0.0, 1.0),
    "fliese_gruen_fuge": ("#8FAE9A", 0.90, 0.0, 1.0),
})


def flach_viereck(name, punkte, y, mat_name):
    """Flaches Viereck auf Hoehe y aus vier (x, z)-Punkten -- fuer Streifen,
    Flecken und Warnschraffuren. Normale zeigt nach oben."""
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for (x, z) in punkte]
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat_name)


def wand_viereck(name, punkte, z, mat_name, nach_plus=True):
    """Senkrechtes Viereck in der Ebene lokal z aus vier (x, y)-Punkten --
    fuer Schraffuren auf Wandflaechen."""
    bm = bmesh.new()
    vs = [bm.verts.new(G(x, y, z)) for (x, y) in punkte]
    f = bm.faces.new(vs)
    f.normal_update()
    # Godot +z = Blender -y
    if (f.normal.y < 0) != nach_plus:
        f.normal_flip()
    return _objekt(name, bm, mat_name)


def boden_fliese_gruen_a():
    return _kacheln(3, "fliese_gruen_fuge", lambda i, k: "fliese_gruen", 0.010)


def boden_fliese_gruen_b():
    dunkler = {(1, 1), (0, 2), (2, 0)}
    return _kacheln(3, "fliese_gruen_fuge",
                    lambda i, k: "fliese_gruen2" if (i, k) in dunkler else "fliese_gruen", 0.010)


# ==============================================================================
# BODENMODULE
# ==============================================================================

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def _flecken(seed, anzahl, mats, y=0.0012, groesse=(0.02, 0.07)):
    """Feine Sprenkel wie in Epoxid- und Asphaltboeden. Fester Seed je
    Variante, damit a und b reproduzierbar verschieden sind."""
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
    """Heller Epoxid-Hallenboden: eine grosse Kissenplatte mit kaum sichtbarer
    Fase, darauf Sprenkel. Keine Rasterfuge -- a und b unterscheiden sich nur
    in der Lage der Sprenkel, sonst entstuende ein Schachbrett."""
    teile = [_tragplatte("halle_fuge", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004, "halle_grau"))
    teile += _flecken(seed, 9, ["halle_fleck_d", "halle_fleck_h", "halle_fleck_d"])
    return teile


def boden_hallenboden_a():
    return _hallenplatte(401)


def boden_hallenboden_b():
    return _hallenplatte(402)


LINIE_BREITE = 0.06


def _linie(z_mitte):
    z0, z1 = z_mitte - LINIE_BREITE / 2, z_mitte + LINIE_BREITE / 2
    return flach_viereck("linie", [(-0.5, z0), (0.5, z0), (0.5, z1), (-0.5, z1)], 0.0016, "linie_gelb")


def boden_hallenboden_linie_a():
    """Duenne gelbe Linie am hinteren Rand (lokal z = -0,46)."""
    teile = [_tragplatte("halle_fuge", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004, "halle_grau"))
    teile += _flecken(403, 7, ["halle_fleck_d", "halle_fleck_h"])
    teile.append(_linie(-0.46))
    return teile


def boden_hallenboden_linie_b():
    """Dieselbe Randlinie plus eine kurze Marke mittig. Die Randlinie liegt in
    a und b an derselben Stelle -- nur so bleibt sie im Schachbrett des
    Grundriss-Bauers durchgehend (erster Anlauf: Linie in b mittig -> Zickzack)."""
    teile = [_tragplatte("halle_fuge", -0.004)]
    teile.append(kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004, "halle_grau"))
    teile += _flecken(404, 7, ["halle_fleck_d", "halle_fleck_h"])
    teile.append(_linie(-0.46))
    teile.append(flach_viereck("marke", [(-0.12, -0.025), (0.12, -0.025), (0.12, 0.025), (-0.12, 0.025)],
                               0.0016, "linie_gelb"))
    return teile


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
    # Teppichfliesen 50 x 50 im Wechsel der Toene -- in a und b vertauscht,
    # damit sich das Wechselmuster ueber die Modulgrenze fortsetzt.
    return _kacheln(2, "teppich_fuge",
                    lambda i, k: "teppich_blau" if (i + k) % 2 == 0 else "teppich_blau2", 0.006, -0.004)


def boden_teppich_b():
    return _kacheln(2, "teppich_fuge",
                    lambda i, k: "teppich_blau2" if (i + k) % 2 == 0 else "teppich_blau", 0.006, -0.004)


def _asphalt(seed, flicken):
    teile = [_tragplatte("asphalt_fuge", -0.004)]
    teile.append(kissen_platte("belag", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.003, "asphalt_grau"))
    teile += _flecken(seed, 14, ["asphalt_fleck", "asphalt_hell"], groesse=(0.015, 0.05))
    # (Ein Flicken je b-Modul bildete im Schachbrett ein Raster -- verworfen.)
    return teile


def boden_asphalt_a():
    return _asphalt(405, False)


def boden_asphalt_b():
    return _asphalt(406, True)


def boden_fliese_a():
    return _kacheln(3, "fliese_kalt_fuge", lambda i, k: "fliese_kalt", 0.010)


def boden_fliese_b():
    dunkler = {(0, 2), (2, 0)}
    return _kacheln(3, "fliese_kalt_fuge",
                    lambda i, k: "fliese_kalt2" if (i, k) in dunkler else "fliese_kalt", 0.010)


# ==============================================================================
# WANDMODULE
# ==============================================================================
# Sandwichpaneel hell mit waagerechten Rillen, tuerkise Kappe, graue
# Fussleiste. Querschnitt, Hoehen und Ursprung exakt wie wg_wand_*.

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
    return profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.025),
                    x0, x1, "kappe_stahl")


def _leiste(hoehe, x0=-0.5, x1=0.5):
    d = LEISTE_DICKE / 2.0
    return profil_x("leiste", rundprofil(-d, d, 0.0, hoehe, 0.012, 1), x0, x1, "sockel_grau")


def _koerper(x0, x1, y0, y1, mat="paneel_hell"):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, mat)


def _leistenhoehe(hoehe):
    return min(LEISTE_HOEHE, hoehe * 0.2)


def _rillen(hoehen, x0=-0.5, x1=0.5):
    """Paneelstoesse als feine Rillen auf beiden Wandseiten."""
    teile = []
    for y in hoehen:
        for s in (-1, 1):
            teile.append(kasten("rille", (x1 - x0, 0.016, 0.006),
                                ((x0 + x1) / 2, y, s * (WAND_DICKE / 2 + 0.002)), "paneel_rille"))
    return teile


def wand_voll():
    h = HOEHE["voll"]
    return [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001), _kappe(h),
            _leiste(_leistenhoehe(h))] + _rillen((0.6, 1.2, 1.8))


def wand_voll_fenster():
    """Oberlichtband: Glas 1,40 bis 2,16, fast modulbreit -- nebeneinander
    gesetzt entsteht ein durchgehendes Band mit schmalen Pfosten."""
    h = HOEHE["voll"]
    ox, u, o = 0.47, 1.40, 2.16
    teile = [
        _koerper(-0.5, 0.5, 0.0, u),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _koerper(-0.5, -ox, u, o),
        _koerper(ox, 0.5, u, o),
        _kappe(h), _leiste(_leistenhoehe(h)),
    ] + _rillen((0.6, 1.2))
    r, t = 0.05, 0.12
    teile.append(kasten("rahmen_l", (r, o - u, t), (-ox + r / 2, (u + o) / 2, 0.0), "rahmen_anthrazit"))
    teile.append(kasten("rahmen_r", (r, o - u, t), (ox - r / 2, (u + o) / 2, 0.0), "rahmen_anthrazit"))
    teile.append(kasten("rahmen_o", (2 * ox - 2 * r, r, t), (0.0, o - r / 2, 0.0), "rahmen_anthrazit"))
    teile.append(kasten("rahmen_u", (2 * ox - 2 * r, r, t), (0.0, u + r / 2, 0.0), "rahmen_anthrazit"))
    teile.append(kasten("sprosse", (0.035, o - u - 2 * r, 0.08), (0.0, (u + o) / 2, 0.0), "rahmen_anthrazit"))
    teile.append(kasten("glas", (2 * ox - 2 * r, o - u - 2 * r, 0.02), (0.0, (u + o) / 2, 0.0), "glas_kuehl"))
    # schmale Blechbank innen
    teile.append(kasten("bank", (0.98, 0.03, 0.2), (0.0, u - 0.015, 0.03), "rahmen_anthrazit",
                        rund=0.008, segmente=1))
    return teile


def wand_halb():
    """Trennwand: unten Paneel, oben Stahlgitter, obenauf der tuerkise Handlauf.
    Der Gitterpfosten sitzt nur am linken Modulrand -- zwei Pfosten an
    derselben Stelle wuerden flackern."""
    h = HOEHE["halb"]
    u = 0.55
    teile = [_koerper(-0.5, 0.5, 0.0, u), _kappe(h), _leiste(_leistenhoehe(h))]
    # Abschlussleiste des Paneels
    teile.append(profil_x("paneelkante", rundprofil(-0.11, 0.11, u - 0.001, u + 0.03, 0.012, 1),
                          -0.5, 0.5, "sockel_grau"))
    oben = h - KAPPE_HOEHE
    teile.append(kasten("gitterpfosten", (0.04, oben - u, 0.05), (-0.48, (oben + u) / 2, 0.0), "rahmen_anthrazit"))
    for i in range(8):
        x = -0.4375 + i * 0.125
        teile.append(kasten("draht_s", (0.012, oben - u - 0.03, 0.012), (x, (oben + u) / 2 + 0.01, 0.0),
                            "gitter_stahl"))
    for y in (0.72, 0.88, 1.03):
        teile.append(kasten("draht_w", (1.0, 0.012, 0.014), (0.0, y, 0.0), "gitter_stahl"))
    return teile


def _schraffur_wand(x0, x1, y0, y1, z, nach_plus, streifen=4):
    """Gelb-schwarze Warnschraffur auf einer Wandflaeche."""
    teile = [wand_viereck("warn_grund", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z, "warn_gelb", nach_plus)]
    schritt = (x1 - x0) / streifen
    hoehe = y1 - y0
    zb = z + (0.0006 if nach_plus else -0.0006)
    for i in range(streifen):
        a = x0 + i * schritt
        b = a + schritt * 0.5
        # Parallelogramm, oben um die Hoehe nach rechts versetzt, in den Grund geklemmt
        pk = [(a, y0), (b, y0), (min(b + hoehe, x1), y1), (min(a + hoehe, x1), y1)]
        if a + hoehe >= x1:
            continue
        teile.append(wand_viereck("warn_streifen", pk, zb, "warn_schwarz", nach_plus))
    return teile


def wand_sockel():
    """Sockel: Paneel mit Warnschraffur auf der Aussenseite (lokal -z) --
    von der Kamera aus sieht man sie an der Vorderkante der Halle."""
    h = HOEHE["sockel"]
    teile = [_koerper(-0.5, 0.5, 0.0, h - KAPPE_HOEHE + 0.001), _kappe(h), _leiste(_leistenhoehe(h))]
    z = -(WAND_DICKE / 2 + 0.003)
    teile += _schraffur_wand(-0.5, 0.5, 0.11, 0.25, z, False, streifen=4)
    return teile


def _anfahrschutz(x, y_bis=0.62):
    """Gelb-schwarzer Rammschutz als unterer Teil des Tuerpfostens: fuenf
    uebereinander gestapelte Stuecke, keine deckungsgleichen Flaechen."""
    teile = []
    grenzen = (0.0, 0.14, 0.22, 0.38, 0.46, y_bis)
    for i in range(5):
        y0, y1 = grenzen[i], grenzen[i + 1]
        mat = "warn_schwarz" if i % 2 else "warn_gelb"
        teile.append(kasten("schutz", (TUER_PFOSTEN_B, y1 - y0, TUER_TIEFE), (x, (y0 + y1) / 2, 0.0), mat,
                            unten=False))
    return teile


def _tuerrahmen():
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    schutz = 0.62
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1 - schutz, t),
                            (s * TUER_PFOSTEN_X, schutz + (h - 0.1 - schutz) / 2, 0.0),
                            "rahmen_anthrazit", rund=0.012, segmente=1))
        teile += _anfahrschutz(s * TUER_PFOSTEN_X, schutz)
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.12, t), (0.0, h - 0.06, 0.0),
                        "kappe_stahl", rund=0.02, segmente=2))
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "gitter_stahl", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Stahltuer mit Glasausschnitt, 105 Grad nach aussen (lokal -z)
    aufgeschwenkt -- Lage wie wg_wand_sockel_tuer."""
    teile = _tuerrahmen()
    blatt_b, blatt_h, blatt_d = 0.78, 1.93, 0.045
    blatt = [
        kasten("tuerblatt_u", (blatt_b, 1.05, blatt_d), (blatt_b / 2, 0.012 + 0.525, 0.0),
               "tuer_blech", rund=0.01, segmente=1),
        kasten("tuerblatt_o", (blatt_b, 0.26, blatt_d), (blatt_b / 2, 0.012 + blatt_h - 0.13, 0.0),
               "tuer_blech", rund=0.01, segmente=1),
        kasten("tuerblatt_l", (0.14, blatt_h - 1.31, blatt_d), (0.07, 0.012 + 1.05 + (blatt_h - 1.31) / 2, 0.0),
               "tuer_blech"),
        kasten("tuerblatt_r", (0.14, blatt_h - 1.31, blatt_d),
               (blatt_b - 0.07, 0.012 + 1.05 + (blatt_h - 1.31) / 2, 0.0), "tuer_blech"),
        kasten("tuerglas", (blatt_b - 0.28, blatt_h - 1.31, 0.015),
               (blatt_b / 2, 0.012 + 1.05 + (blatt_h - 1.31) / 2, 0.0), "glas_kuehl"),
    ]
    for seite in (-1, 1):
        blatt.append(kasten("stange", (0.5, 0.035, 0.03), (blatt_b / 2 + 0.05, 1.0, seite * (blatt_d / 2 + 0.03)),
                            "gitter_stahl"))
        blatt.append(kasten("trittblech", (blatt_b - 0.06, 0.16, 0.006),
                            (blatt_b / 2, 0.11, seite * (blatt_d / 2 + 0.003)), "gitter_stahl"))
    scharnier_x = -TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2
    transformieren(blatt, x=scharnier_x, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    teile += blatt
    return teile


def gelaender():
    """Gelbes Sicherheitsgelaender: runder Handlauf 1,0, Knieleiste 0,5,
    Fussleiste gegen rollende Kartons, ein Pfosten je Meter."""
    teile = []
    teile.append(profil_x("handlauf", rundprofil(-0.035, 0.035, 0.94, 1.0, 0.025), -0.5, 0.5, "warn_gelb"))
    teile.append(profil_x("knieleiste", rundprofil(-0.025, 0.025, 0.50, 0.545, 0.018), -0.5, 0.5, "warn_gelb"))
    teile.append(kasten("fussleiste", (1.0, 0.12, 0.025), (0.0, 0.10, 0.0), "warn_gelb"))
    teile.append(kasten("fussband", (1.0, 0.03, 0.03), (0.0, 0.10, 0.0), "warn_schwarz"))
    teile.append(kasten("stiel", (0.05, 0.95, 0.05), (0.0, 0.475, 0.0), "warn_gelb", rund=0.008, segmente=1))
    return teile


def _pfosten(hoehe):
    """Stahlstuetze als I-Profil, blau, unten ein gelb-schwarzer Rammschutz."""
    lh = _leistenhoehe(hoehe)
    koerper_h = hoehe - KAPPE_HOEHE + 0.002
    teile = [
        kasten("flansch_v", (0.20, koerper_h, 0.035), (0.0, koerper_h / 2, 0.0925), "stahl_blau", unten=False),
        kasten("flansch_h", (0.20, koerper_h, 0.035), (0.0, koerper_h / 2, -0.0925), "stahl_blau", unten=False),
        kasten("steg", (0.035, koerper_h, 0.16), (0.0, koerper_h / 2, 0.0), "stahl_blau", unten=False),
        kasten("kopfplatte", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "kappe_stahl", rund=0.02, segmente=2),
        kasten("fussplatte", (0.24, lh, 0.24), (0.0, lh / 2, 0.0), "sockel_grau", unten=False),
    ]
    if hoehe > 1.0:
        sh = 0.55
        teile.append(kasten("rammschutz", (0.25, sh, 0.25), (0.0, sh / 2, 0.0), "warn_gelb",
                            rund=0.015, segmente=1))
        for y in (0.16, 0.40):
            teile.append(kasten("rammschutz_band", (0.256, 0.08, 0.256), (0.0, y, 0.0), "warn_schwarz"))
    return teile


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


# ==============================================================================
# ALTMODULE (validate Schritt 7, RoomBuilder) -- einfache Varianten
# Masse wie room/zimmer/raum_*: Fliese 0,98 x 0,03 x 0,98 um y = 0,
# Wand 1 x 2,2 x 0,2, Tuer 2 m breit.
# ==============================================================================

def _altfliese(linie, mat="halle_grau"):
    teile = [kasten("fliese", (0.98, 0.03, 0.98), (0.0, 0.0, 0.0), mat)]
    teile += _flecken(407 if not linie else 408, 5, ["halle_fleck_d", "halle_fleck_h"], y=0.0162)
    if linie:
        teile.append(flach_viereck("linie", [(-0.49, -0.05), (0.49, -0.05), (0.49, 0.05), (-0.49, 0.05)],
                                   0.0166, "linie_gelb"))
    return teile


def raum_fliese_a():
    return _altfliese(False)


def raum_fliese_b():
    return _altfliese(False, "halle_fleck_h")


def raum_fliese_weg():
    return _altfliese(True)


def _altwand(x0, x1, y0=0.0, y1=2.2):
    return [
        kasten("altwand", (x1 - x0, y1 - 0.06 - y0, 0.2), ((x0 + x1) / 2, (y0 + y1 - 0.06) / 2, 0.0), "paneel_hell"),
        kasten("altkappe", (x1 - x0, 0.06, 0.2), ((x0 + x1) / 2, y1 - 0.03, 0.0), "kappe_tuerkis"),
    ]


def raum_wand():
    return _altwand(-0.5, 0.5)


def raum_wand_ecke():
    teile = _altwand(-0.5, 0.53)
    teile.append(kasten("altwand_z", (0.2, 2.14, 0.83), (0.43, 1.07, 0.515), "paneel_hell"))
    teile.append(kasten("altkappe_z", (0.2, 0.06, 0.83), (0.43, 2.17, 0.515), "kappe_tuerkis"))
    return teile


def raum_wand_tuer():
    teile = _altwand(-1.0, -0.5) + _altwand(0.5, 1.0)
    teile.append(kasten("altsturz", (1.0, 0.3, 0.2), (0.0, 2.05, 0.0), "paneel_hell"))
    for s in (-1, 1):
        teile.append(kasten("altpfosten", (0.08, 1.9, 0.2), (s * 0.46, 0.95, 0.0), "rahmen_anthrazit"))
    return teile


def raum_wand_fenster():
    teile = [
        kasten("unten", (1.0, 1.0, 0.2), (0.0, 0.5, 0.0), "paneel_hell"),
        kasten("oben", (1.0, 0.2, 0.2), (0.0, 1.97, 0.0), "paneel_hell"),
        kasten("kappe", (1.0, 0.06, 0.2), (0.0, 2.17, 0.0), "kappe_tuerkis"),
        kasten("seite_l", (0.1, 0.87, 0.2), (-0.45, 1.435, 0.0), "paneel_hell"),
        kasten("seite_r", (0.1, 0.87, 0.2), (0.45, 1.435, 0.0), "paneel_hell"),
        kasten("rahmen", (0.8, 0.87, 0.26), (0.0, 1.435, 0.0), "rahmen_anthrazit", unten=False),
    ]
    teile.append(kasten("glas", (0.72, 0.79, 0.262), (0.0, 1.435, 0.0), "glas_kuehl"))
    return teile


# ==============================================================================
# VORSCHAU -- neutral-kuehles Licht statt des warmen WG-Lichts
# ==============================================================================

def rendern(pfad, ziel, ortho, aufloesung=1080, breite=None):
    """Wie build_room_wg.vorschau_rendern, aber mit neutralem Tageslicht
    (Lagerhalle, kuehl-hell) und optional anderem Seitenverhaeltnis."""
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

    sonne("licht_haupt", 2.3, "#FFF4E6", G(0.45, 1.0, 0.65), True, 12.0)
    sonne("licht_auf", 0.6, "#E2EEFF", G(-0.9, 0.55, 0.25), False, 30.0)
    welt = bpy.data.worlds.new("vorschau_welt")
    if welt.node_tree is None:
        welt.use_nodes = True
    baum = welt.node_tree
    for n in list(baum.nodes):
        baum.nodes.remove(n)
    ausgang = baum.nodes.new("ShaderNodeOutputWorld")
    licht = baum.nodes.new("ShaderNodeBackground")
    licht.inputs["Color"].default_value = farbe("#F4F8FA")
    licht.inputs["Strength"].default_value = 0.5
    grund = baum.nodes.new("ShaderNodeBackground")
    grund.inputs["Color"].default_value = farbe(HINTERGRUND)
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
    "boden_hallenboden_linie_a": boden_hallenboden_linie_a,
    "boden_hallenboden_linie_b": boden_hallenboden_linie_b,
    "boden_teppich_a": boden_teppich_a,
    "boden_teppich_b": boden_teppich_b,
    "boden_asphalt_a": boden_asphalt_a,
    "boden_asphalt_b": boden_asphalt_b,
    "boden_fliese_gruen_a": boden_fliese_gruen_a,
    "boden_fliese_gruen_b": boden_fliese_gruen_b,
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
    print("=== MODULE WELT 4 (LAGER) ===")
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
                importieren(modul_pfad(name), x=(i % 5) * 3.4 + dx, z=(i // 5) * 3.4 + dz)
    # Schachbrett-Probe der Linienboeden (so verlegt sie der Grundriss-Bauer heute)
    for dx in range(5):
        for dz in range(3):
            ab = "a" if (dx + dz) % 2 == 0 else "b"
            importieren(modul_pfad("boden_hallenboden_linie_" + ab), x=dx - 1, z=7.8 + dz)
    rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (6.8, 0.0, 3.5), 15.0)

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
    # Sockel vorn, wie auf der Karte gedreht (Schraffur nach aussen)
    for dx in range(4):
        importieren(modul_pfad("wand_sockel"), x=dx, z=8.5, dreh_grad=180.0)
    for dx in range(3):
        importieren(modul_pfad("gelaender"), x=5.5 + dx, z=0.0)
        importieren(modul_pfad("boden_asphalt_" + ("a" if dx % 2 == 0 else "b")), x=5.5 + dx, z=0.5)
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
