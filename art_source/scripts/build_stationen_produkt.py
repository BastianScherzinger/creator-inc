"""Erzeugt die Stationen der Welt `produkt` ("Die Farm", Nachtplan N41) als GLB,
dazu die Symbole und die Vorschaublaetter.

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_stationen_produkt.py
    blender --background --python art_source/scripts/build_stationen_produkt.py -- --vorschau --symbole
    blender --background --python art_source/scripts/build_stationen_produkt.py -- --nur buffer --vorschau

Vertrag (docs/NACHT_PLAN.md Paragraf 5, docs/nacht/ausstattung_welten.md, Welt 5):
    project/assets/stations/produkt/station_<id>_basis.glb
    project/assets/stations/produkt/station_<id>_ausstattung_<n>_<m>.glb   n = 1..3, m = 0..3
    project/assets/stations/produkt/station_<id>_<1|2|3>.glb               Altmodelle
    project/assets/ui/produkt/station_<id>.png, station_<id>_ausstattung_<n>_<m>.png  256 x 256

Werkzeuge (Quader, Zylinder, Export, Ueberschneidungspruefung, Vorschau,
Symbol-Render) kommen unveraendert aus build_stationen_wg.py und
build_symbole_wg.py. Dieses Skript setzt nur Ausgabeordner, Palette und die
Stationen selbst.

Stationsflaechen (docs/nacht/karten_welten.md): intake und processing stehen mit
dem Ruecken an der Innenwand (lokal z = -1,05), transport an der Gangwand
(lokal z = -1,1). Am buffer steht Selin bei (-0,9 | 0,3), am special Roman
bei (-0,9 | 0,5); beide Plaetze bleiben frei. Die Spielfigur sitzt an
processing bei (0 | 0,05), Sitzhoehe 0,48.

Koordinaten: GODOT (y oben, Vorderseite +z). Farben linear. Dateinamen neutral.
Budget: Station mit voller Ausstattung <= 3.000 Dreiecke.
"""

import bpy
import math
import os
import sys

import numpy as np
from mathutils import Vector

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.dont_write_bytecode = True
import build_stationen_wg as wg  # noqa: E402
import build_symbole_wg as sy  # noqa: E402
from build_stationen_wg import kasten, zylinder, stab, kugel, ring, punkt  # noqa: E402

PROJEKT = wg.PROJEKT
AUSGABE = os.path.join(PROJEKT, "project", "assets", "stations", "produkt")
AUSGABE_UI = os.path.join(PROJEKT, "project", "assets", "ui", "produkt")
VORSCHAU = os.path.join(PROJEKT, "art_source", "vorschau", "produkt")

BUDGET_GESAMT = 3000
wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU
wg.BUDGET_BASIS = 1100
wg.BUDGET_AUSSTATTUNG = 900
sy.AUSGABE = AUSGABE_UI

# --- Palette: Fabrikhalle, kuehl-violett mit warmen Akzenten -----------------
wg.PALETTE.update({
    "rack":           ("#2E2C40", 0.0),
    "rack_front":     ("#3C3A55", 0.0),
    "alu":            ("#C9CED8", 0.0),
    "stahl":          ("#555C7C", 0.0),
    "schrank":        ("#4C5262", 0.0),
    "weiss":          ("#F4F3F7", 0.0),
    "violett":        ("#444866", 0.0),
    "violett_dunkel": ("#2A2B3C", 0.0),
    "violett_hell":   ("#9AA3B8", 0.0),
    "cyan":           ("#2FC6D6", 0.0),
    "warn_gelb":      ("#FFC21A", 0.0),
    "trafo":          ("#6F8A7C", 0.0),
    "isolator":       ("#E9E2D0", 0.0),
    "kupfer":         ("#C77A45", 0.0),
    "gummi":          ("#2A2A30", 0.0),
    "leder":          ("#2F3245", 0.0),
    "leder_hell":     ("#3E4160", 0.0),
    "wasser_dunkel":  ("#1E3A55", 0.0),
    "rot_cee":        ("#D8423A", 0.0),
    "blau_cee":       ("#3C7FD8", 0.0),
    "licht_violett":  ("#A78BFA", 1.6),
    "licht_cyan":     ("#5EE6F0", 1.6),
    "licht_gruen":    ("#6BE38A", 1.4),
    "licht_rot":      ("#FF5A4A", 1.4),
    "wasser":         ("#4FD6F0", 0.7),
    "glas_kalt":      ("#BFD9F2", 0.0),
    "holo":           ("#B69CFF", 1.8),
    "v_boden":        ("#D8D6E2", 0.0),
    "v_wand":         ("#C4654B", 0.0),
    "v_kappe":        ("#3E3A57", 0.0),
})


def q(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0), r=None):
    """Quader mit sparsamer Rundung."""
    if r is None:
        m = min(groesse)
        r = (min(0.012, m * 0.18), 1) if m >= 0.04 else (0.0, 0)
    return kasten(name, groesse, pos, mat, dreh, rund=r)


def f(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0)):
    return kasten(name, groesse, pos, mat, dreh, rund=(0.0, 0))


def walze(name, radius, laenge, pos, mat, achse="x", seiten=8):
    dreh = (0, 0, 90) if achse == "x" else (90, 0, 0)
    return zylinder(name, radius, laenge, pos, mat, seiten=seiten, dreh=dreh, rund=(0, 0))


def zyl(name, radius, hoehe, pos_unten, mat, seiten=10, radius_oben=None):
    x, y, z = pos_unten
    return zylinder(name, radius, hoehe, (x, y + hoehe / 2, z), mat, seiten=seiten, radius_oben=radius_oben,
                    rund=(0, 0))


def schirm(pos, dreh, b, h, art="kurve", tiefe=0.0):
    """Leuchtflaeche mit angedeutetem Inhalt, zeigt nach lokal +z."""
    t = [f("schirm", (b, h, 0.004), punkt(pos, dreh, (0, 0, tiefe)), "schirm", dreh)]
    z = tiefe + 0.0035
    if art == "kurve":
        for k in range(4):
            hk = h * (0.2 + 0.16 * k)
            t.append(f("i", (b * 0.13, hk, 0.003), punkt(pos, dreh, (-b * 0.3 + k * b * 0.2, -h * 0.38 + hk * 0.5, z)),
                       "licht_violett" if k == 3 else "schirm_blau", dreh))
    elif art == "block":
        for r in range(2):
            for s in range(3):
                t.append(f("i", (b * 0.24, h * 0.3, 0.003), punkt(pos, dreh, (-b * 0.29 + s * b * 0.29, h * 0.17 - r * h * 0.38, z)),
                           "licht_violett" if (r + s) % 3 == 0 else "licht_cyan", dreh))
    elif art == "linie":
        t.append(f("i", (b * 0.85, h * 0.08, 0.003), punkt(pos, dreh, (0, 0.0, z)), "licht_cyan", dreh))
        t.append(f("i", (b * 0.3, h * 0.25, 0.003), punkt(pos, dreh, (-b * 0.25, h * 0.25, z)), "licht_violett", dreh))
    elif art == "gruen":
        t.append(f("i", (b * 0.7, h * 0.5, 0.003), punkt(pos, dreh, (0, 0, z)), "licht_gruen", dreh))
    return t


def monitor(pos, dreh, b, h, art="kurve", fuss=True, fuss_hoehe=0.08):
    t = []
    unten = 0.0
    if fuss:
        t.append(f("fuss", (b * 0.34, 0.014, 0.13), punkt(pos, dreh, (0, 0.007, -0.02)), "grau_dunkel", dreh))
        t.append(f("hals", (0.04, fuss_hoehe + 0.04, 0.025), punkt(pos, dreh, (0, 0.014 + (fuss_hoehe + 0.04) * 0.5, -0.045)), "grau_dunkel", dreh))
        unten = 0.014 + fuss_hoehe
    mitte = punkt(pos, dreh, (0, unten + h * 0.5, 0))
    t.append(q("gehaeuse", (b, h, 0.03), mitte, "schwarz", dreh, r=(0.008, 1)))
    t += schirm(mitte, dreh, b * 0.9, h * 0.84, art, tiefe=0.016)
    return t


def warnzeichen(pos, dreh, g=0.12):
    return [f("warn", (g, g, 0.004), pos, "warn_gelb", dreh),
            f("warn_blitz", (g * 0.2, g * 0.6, 0.003), punkt(pos, dreh, (0, 0, 0.003)), "schwarz", dreh)]


def rig(x0, x1, y, z0, z1, karten, licht="licht_violett", rahmen=True):
    """Offener Rechner-Rahmen mit n Karten. Unterkante y."""
    t = [f("platine", (x1 - x0 - 0.02, 0.015, z1 - z0 - 0.02), ((x0 + x1) / 2, y + 0.0075, (z0 + z1) / 2), "violett_dunkel")]
    h = 0.22
    if rahmen:
        for x in (x0 + 0.01, x1 - 0.01):
            for z in (z0 + 0.01, z1 - 0.01):
                t.append(f("holm", (0.02, h, 0.02), (x, y + h / 2, z), "alu"))
        t.append(f("traverse", (x1 - x0, 0.02, 0.02), ((x0 + x1) / 2, y + h - 0.01, z1 - 0.01), "alu"))
        t.append(f("traverse", (x1 - x0, 0.02, 0.02), ((x0 + x1) / 2, y + h - 0.01, z0 + 0.01), "alu"))
    schritt = (x1 - x0 - 0.06) / max(karten, 1)
    for i in range(karten):
        x = x0 + 0.03 + (i + 0.5) * schritt
        t.append(f("karte", (min(0.035, schritt * 0.7), 0.15, z1 - z0 - 0.08), (x, y + 0.1, (z0 + z1) / 2), "schwarz"))
        t.append(f("karte_licht", (min(0.037, schritt * 0.7), 0.012, z1 - z0 - 0.1), (x, y + 0.18, (z0 + z1) / 2), licht))
    return t


def luefter_rund(pos, dreh, r, rahmen_mat="grau_dunkel", tief=0.05):
    """Runder Luefter, Achse lokal z (zeigt nach +z)."""
    from build_stationen_wg import verkette
    d = verkette(dreh, (90, 0, 0))
    t = [zylinder("luefter_ring", r, tief, pos, rahmen_mat, seiten=14, dreh=d, rund=(0, 0))]
    t.append(zylinder("luefter_nabe", r * 0.25, tief + 0.02, pos, "alu", seiten=8, dreh=d, rund=(0, 0)))
    for k in range(3):
        t.append(f("fluegel", (r * 1.7, r * 0.3, 0.008), punkt(pos, dreh, (0, 0, tief * 0.5 + 0.006)), "grau_hell",
                   verkette(dreh, (0, 0, k * 60 + 15))))
    return t


# =============================================================================
# Station 1: station_intake -- Strom. Verteilerkasten an der Wand (Basis),
# Anschluss links (Platz 1), Speicher vorn links (Platz 2), Messung rechts (Platz 3).
# =============================================================================

def intake_basis():
    t = [q("kasten", (0.8, 1.3, 0.34), (-0.1, 0.25 + 0.65, -0.86), "schrank", r=(0.02, 2)),
         f("sockel", (0.78, 0.25, 0.3), (-0.1, 0.125, -0.86), "grau_dunkel"),
         f("fuge", (0.006, 1.2, 0.004), (-0.1, 0.9, -0.689), "grau_mittel"),
         f("streifen", (0.8, 0.05, 0.004), (-0.1, 1.45, -0.689), "licht_violett")]
    for s in (-1, 1):
        t.append(f("griff", (0.03, 0.12, 0.02), (-0.1 + s * 0.06, 0.95, -0.68), "grau_dunkel"))
    t += warnzeichen((-0.3, 1.25, -0.687), (0, 0, 45), 0.12)
    t.append(f("anzeige", (0.16, 0.06, 0.004), (0.12, 1.3, -0.688), "licht_gruen"))
    # Leitungsrohre nach oben in die Wand
    for i, (x, mat) in enumerate(((-0.35, "grau_mittel"), (-0.1, "violett"), (0.15, "grau_mittel"))):
        t.append(zyl("rohr", 0.03, 0.22, (x, 1.55, -0.92), mat, seiten=8))
    # Gummimatte vor dem Kasten
    t.append(f("matte", (0.9, 0.012, 0.5), (-0.1, 0.006, -0.4), "gummi"))
    t.append(f("matte_rand", (0.9, 0.013, 0.03), (-0.1, 0.0065, -0.17), "warn_gelb"))
    return t


def intake_a1_0():
    """Mehrfachstecker auf dem Boden mit Kabel zum Kasten."""
    t = [q("leiste", (0.32, 0.05, 0.08), (-0.8, 0.025, -0.35), "weiss", (0, 25, 0), r=(0.01, 1)),
         f("schalter", (0.03, 0.012, 0.03), punkt((-0.8, 0.05, -0.35), (0, 25, 0), (0.12, 0.004, 0)), "rot", (0, 25, 0))]
    for k in range(3):
        t.append(f("stecker", (0.04, 0.05, 0.05), punkt((-0.8, 0.075, -0.35), (0, 25, 0), (-0.09 + k * 0.07, 0, 0)),
                   "schwarz", (0, 25, 0)))
    t.append(stab("kabel", (-0.66, 0.02, -0.42), (-0.58, 0.02, -0.62), 0.012, "schwarz"))
    return t


def _cee_dose(x, y, z, farbe="rot_cee"):
    return [q("dose", (0.18, 0.2, 0.12), (x, y, z), farbe, r=(0.015, 1)),
            zyl("deckel", 0.05, 0.05, (x, y - 0.02, z + 0.06), "grau_dunkel", seiten=8)]


def intake_a1_1():
    """Starkstromdose auf einem Pfosten, roter Stecker mit Kabel."""
    t = [f("fussplatte", (0.3, 0.02, 0.3), (-0.8, 0.01, -0.6), "grau_mittel"),
         q("pfosten", (0.08, 0.9, 0.08), (-0.8, 0.47, -0.7), "stahl")]
    t += _cee_dose(-0.8, 0.8, -0.59)
    t.append(stab("kabel", (-0.8, 0.72, -0.5), (-0.78, 0.03, -0.35), 0.018, "rot_cee"))
    t.append(stab("kabel2", (-0.78, 0.03, -0.35), (-0.6, 0.02, -0.12), 0.018, "rot_cee"))
    return t


def _schrank_links(h, farbe="schrank"):
    t = [q("schrank", (0.44, h, 0.4), (-0.83, h / 2, -0.83), farbe, r=(0.015, 1)),
         f("fuge", (0.004, h - 0.15, 0.004), (-0.83, h / 2, -0.628), "grau_mittel")]
    t += warnzeichen((-0.9, h - 0.2, -0.627), (0, 0, 45), 0.1)
    return t


def intake_a1_2():
    """Verteilerschrank mit drei Dosen und Leuchtband."""
    t = _schrank_links(1.5)
    for k in range(3):
        t += _cee_dose(-0.83, 0.35 + k * 0.28, -0.56, ("rot_cee", "blau_cee", "rot_cee")[k])[:1]
    t.append(f("licht", (0.44, 0.04, 0.004), (-0.83, 1.4, -0.628), "licht_violett"))
    return t


def intake_a1_3():
    """Trafo-Kasten: gruener Kessel mit Rippen und drei Isolatoren."""
    t = [q("kessel", (0.44, 0.9, 0.36), (-0.83, 0.12 + 0.45, -0.8), "trafo", r=(0.02, 1)),
         f("fuss", (0.46, 0.12, 0.4), (-0.83, 0.06, -0.8), "grau_dunkel")]
    for i in range(4):
        t.append(f("rippe", (0.03, 0.7, 0.08), (-1.065, 0.57, -0.95 + i * 0.1), "trafo"))
    for k in range(3):
        x = -0.95 + k * 0.12
        t.append(zyl("isolator", 0.03, 0.2, (x, 1.02, -0.8), "isolator", seiten=8, radius_oben=0.02))
        t.append(zyl("schirmchen", 0.05, 0.015, (x, 1.1, -0.8), "isolator", seiten=8))
        t.append(kugel("klemme", 0.025, (x, 1.24, -0.8), "kupfer", stufen=1))
    t += warnzeichen((-0.83, 0.75, -0.618), (0, 0, 45), 0.12)
    t.append(f("licht", (0.3, 0.03, 0.004), (-0.83, 0.3, -0.618), "licht_violett"))
    return t


def intake_a2_1():
    """Autobatterie mit Klemmen vorn links."""
    t = [q("batterie", (0.3, 0.2, 0.2), (-0.55, 0.1, 0.45), "grau_dunkel", (0, 15, 0), r=(0.012, 1)),
         f("deckel", (0.3, 0.02, 0.2), (-0.55, 0.21, 0.45), "violett", (0, 15, 0))]
    for s, mat in ((-1, "rot"), (1, "schwarz")):
        t.append(zyl("pol", 0.02, 0.04, punkt((-0.55, 0.22, 0.45), (0, 15, 0), (s * 0.1, 0, -0.05)), mat, seiten=6))
    t.append(stab("kabel", (-0.65, 0.25, 0.4), (-0.75, 0.02, 0.1), 0.012, "rot"))
    return t


def intake_a2_2():
    """Akkuschrank mit Ladeanzeigen."""
    t = [q("schrank", (0.6, 1.0, 0.45), (-0.55, 0.5, 0.55), "weiss", r=(0.02, 1))]
    for i in range(3):
        y = 0.2 + i * 0.3
        t.append(f("modul", (0.5, 0.24, 0.004), (-0.55, y, 0.777), "schrank"))
        for k in range(3 - (i % 2)):
            t.append(f("ladung", (0.09, 0.03, 0.003), (-0.72 + k * 0.11, y + 0.06, 0.781), "licht_gruen"))
    t.append(f("band", (0.604, 0.05, 0.454), (-0.55, 0.9, 0.55), "violett"))
    return t


def intake_a2_3():
    """Batterie-Container: kleiner Stahlcontainer mit Leuchtstreifen."""
    t = [q("container", (0.95, 0.72, 0.62), (-0.55, 0.38, 0.6), "violett_dunkel", r=(0.02, 1)),
         f("sockel", (0.9, 0.04, 0.58), (-0.55, 0.02, 0.6), "grau_dunkel")]
    for i in range(6):
        t.append(f("sicke", (0.05, 0.55, 0.012), (-0.95 + i * 0.16, 0.38, 0.916), "violett"))
    t.append(f("licht", (0.9, 0.04, 0.006), (-0.55, 0.68, 0.918), "licht_cyan"))
    t.append(f("anzeige", (0.2, 0.1, 0.004), (-0.3, 0.45, 0.924), "licht_gruen"))
    t += warnzeichen((-0.75, 0.45, 0.924), (0, 0, 45), 0.1)
    return t


def intake_a3_0():
    """Alter Drehscheibenzaehler an der Wand."""
    t = [f("brett", (0.26, 0.36, 0.02), (0.75, 1.05, -1.03), "holz_hell"),
         q("zaehler", (0.18, 0.26, 0.1), (0.75, 1.05, -0.97), "grau_hell", r=(0.01, 1)),
         f("fenster", (0.12, 0.06, 0.004), (0.75, 1.1, -0.918), "papier"),
         zylinder("scheibe", 0.03, 0.004, (0.75, 0.99, -0.918), "grau_dunkel", seiten=8, dreh=(90, 0, 0), rund=(0, 0)),
         f("pfosten", (0.05, 0.87, 0.05), (0.75, 0.435, -1.0), "stahl")]
    return t


def intake_a3_1():
    """Digitalzaehler mit Leuchtanzeige auf Pfosten."""
    t = [f("pfosten", (0.06, 0.9, 0.06), (0.75, 0.45, -0.95), "stahl"),
         q("zaehler", (0.24, 0.3, 0.12), (0.75, 1.05, -0.9), "weiss", r=(0.012, 1)),
         f("display", (0.18, 0.08, 0.004), (0.75, 1.1, -0.838), "licht_cyan"),
         f("tasten", (0.12, 0.03, 0.004), (0.75, 0.98, -0.838), "grau_dunkel"),
         f("fuss", (0.25, 0.02, 0.25), (0.75, 0.01, -0.9), "grau_mittel")]
    return t


def _pult(x, z, b=0.5, h=0.95):
    """Stehpult mit schraeger Oberseite (Vorderseite +z)."""
    t = [q("pult", (b, h, 0.36), (x, h / 2, z), "schrank", r=(0.015, 1)),
         q("pult_kopf", (b + 0.02, 0.06, 0.42), (x, h + 0.02, z + 0.02), "grau_dunkel", (-15, 0, 0), r=(0.01, 1))]
    t += schirm((x, h + 0.06, z + 0.02), (-105, 0, 0), b - 0.1, 0.3, "linie")
    return t


def intake_a3_2():
    """Messpult mit Anzeigen."""
    t = _pult(0.75, -0.72)
    for k in range(3):
        t.append(zylinder("instrument", 0.045, 0.01, (0.62 + k * 0.13, 0.7, -0.53), "papier", seiten=10, dreh=(90, 0, 0), rund=(0, 0)))
    return t


def intake_a3_3():
    """Leitstand: Pult plus zwei grosse Monitore auf einem Mast."""
    t = _pult(0.75, -0.72)
    t.append(f("mast", (0.05, 0.75, 0.05), (0.75, 1.35, -0.93), "stahl"))
    for s in (-1, 1):
        t += monitor((0.75 + s * 0.17, 1.35, -0.88), (0, -s * 8, 0), 0.32, 0.22, "block" if s < 0 else "kurve", fuss=False)
    t.append(f("licht", (0.52, 0.02, 0.02), (0.75, 1.7, -0.9), "licht_violett"))
    return t


INTAKE = {
    "basis": intake_basis,
    "plaetze": {
        1: {0: intake_a1_0, 1: intake_a1_1, 2: intake_a1_2, 3: intake_a1_3},
        2: {1: intake_a2_1, 2: intake_a2_2, 3: intake_a2_3},
        3: {0: intake_a3_0, 1: intake_a3_1, 2: intake_a3_2, 3: intake_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.09,
    "figur": None,
}


# =============================================================================
# Station 2: station_buffer -- Rigs. Gitterregal (Basis) hinten-mitte,
# Rig 1 unten links (Platz 1), Rig 2 rechts und oben (Platz 2), Kabel vorn
# rechts (Platz 3). Selin steht links bei (-0,9 | 0,3).
# =============================================================================

B_X0, B_X1, B_Z0, B_Z1 = -0.5, 0.9, -0.95, -0.35
B_EBENEN = (0.08, 0.7, 1.3, 1.85)


def buffer_basis():
    t = []
    for x in (B_X0, B_X1):
        for z in (B_Z0, B_Z1):
            t.append(f("stuetze", (0.035, 1.9, 0.035), (x, 0.95, z), "alu"))
    for y in B_EBENEN:
        t.append(f("fachboden", (B_X1 - B_X0 + 0.02, 0.02, B_Z1 - B_Z0 + 0.02), ((B_X0 + B_X1) / 2, y - 0.01, (B_Z0 + B_Z1) / 2), "stahl"))
        t.append(f("kante", (B_X1 - B_X0 + 0.02, 0.03, 0.01), ((B_X0 + B_X1) / 2, y - 0.015, B_Z1 + 0.012), "licht_violett" if y == 0.7 else "alu"))
    # Obenauf: Ersatzteile, Luefter in Kartons
    t.append(q("karton", (0.34, 0.2, 0.3), (-0.2, 1.95, -0.65), "karton", (0, 8, 0)))
    t.append(q("karton2", (0.26, 0.16, 0.26), (0.45, 1.93, -0.62), "karton", (0, -12, 0)))
    # Unten: Netzteile
    for k in range(3):
        t.append(q("netzteil", (0.18, 0.1, 0.22), (-0.25 + k * 0.24, 0.13, -0.62), "grau_dunkel"))
    t.append(f("bodenmarke", (1.8, 0.004, 0.05), (0.2, 0.002, 0.95), "warn_gelb"))
    return t


def buffer_a1_0():
    """Offene Platine mit wenigen Chips."""
    t = [f("platine", (0.5, 0.015, 0.4), (-0.18, 0.7095, -0.65), "violett_dunkel")]
    for i in range(3):
        t.append(f("chip", (0.08, 0.02, 0.08), (-0.35 + i * 0.14, 0.727, -0.65), "schwarz"))
    t.append(f("led", (0.03, 0.01, 0.03), (0.0, 0.722, -0.52), "licht_violett"))
    return t


def buffer_a1_1():
    return rig(-0.45, 0.12, 0.702, -0.9, -0.4, 4)


def buffer_a1_2():
    return rig(-0.45, 0.12, 0.702, -0.9, -0.4, 8)


def buffer_a1_3():
    """Geschlossener Rack-Einschub mit Leuchtfront."""
    t = [q("einschub", (0.56, 0.42, 0.5), (-0.165, 0.702 + 0.21, -0.65), "rack", r=(0.012, 1)),
         f("front", (0.5, 0.36, 0.006), (-0.165, 0.91, -0.397), "rack_front")]
    for k in range(4):
        t.append(f("led", (0.2 + 0.05 * (k % 2), 0.02, 0.004), (-0.3 + 0.025 * (k % 2), 0.78 + k * 0.08, -0.393), "licht_violett" if k % 2 else "licht_cyan"))
    for s in (-1, 1):
        t += luefter_rund((-0.165 + s * 0.13, 0.91, -0.39), (0, 0, 0), 0.06)[:2]
    return t


def buffer_a2_1():
    return rig(0.22, 0.85, 0.702, -0.9, -0.4, 4, "licht_cyan")


def buffer_a2_2():
    return rig(0.22, 0.85, 0.702, -0.9, -0.4, 6, "licht_cyan") + rig(0.22, 0.85, 1.302, -0.9, -0.4, 4, "licht_violett")


def buffer_a2_3():
    """Volles Rack: rechts zwei geschlossene Einschuebe uebereinander."""
    t = []
    for y, mat in ((0.7, "licht_cyan"), (1.3, "licht_violett")):
        t.append(q("einschub", (0.6, 0.48, 0.5), (0.535, y + 0.242, -0.65), "rack", r=(0.012, 1)))
        t.append(f("front", (0.54, 0.42, 0.006), (0.535, y + 0.24, -0.397), "rack_front"))
        for k in range(4):
            t.append(f("led", (0.4 - 0.06 * k, 0.025, 0.004), (0.535 - 0.03 * k, y + 0.08 + k * 0.1, -0.393), mat))
    return t


def buffer_a3_0():
    """Kabelsalat am Boden."""
    t = []
    for i, (x, z, r, mat) in enumerate(((0.55, 0.3, 0.14, "schwarz"), (0.7, 0.4, 0.1, "violett"), (0.45, 0.45, 0.09, "grau_dunkel"))):
        t.append(ring("knaeuel", r, 0.012, (x, 0.02 + i * 0.012, z), mat, dreh=(8 * i, 20 * i, 0), segmente=12, quer=4))
    t.append(stab("kabel", (0.5, 0.02, 0.2), (0.3, 0.02, -0.3), 0.012, "schwarz"))
    return t


def buffer_a3_1():
    """Kabel ordentlich gebuendelt, Kabelbinder."""
    t = []
    for k, mat in enumerate(("schwarz", "violett", "grau_dunkel")):
        t.append(stab("kabel", (0.35 + k * 0.03, 0.02, -0.3), (0.75 + k * 0.03, 0.02, 0.6), 0.013, mat))
    for s in (0.2, 0.5):
        t.append(f("binder", (0.13, 0.035, 0.02), (0.36 + s * 0.44, 0.02, -0.3 + s * 0.9 + 0.0), "weiss", (0, -24, 0)))
    return t


def buffer_a3_2():
    """Kabelkanal: senkrecht am Regal, waagerecht am Boden."""
    return [f("kanal_senk", (0.08, 1.75, 0.08), (0.98, 0.875, -0.65), "weiss"),
            f("kanal_boden", (0.08, 0.05, 1.4), (0.98, 0.025, 0.1), "weiss"),
            f("kanal_deckel", (0.085, 0.01, 1.4), (0.98, 0.055, 0.1), "grau_hell"),
            f("kanal_licht", (0.005, 1.6, 0.02), (1.022, 0.9, -0.65), "licht_violett")]


def buffer_a3_3():
    """Leuchtender Kabelbaum: Buendel laufen im Bogen vom Regal zum Boden."""
    t = [f("kanal_senk", (0.08, 1.75, 0.08), (0.98, 0.875, -0.65), "grau_dunkel"),
         f("kanal_boden", (0.08, 0.05, 1.4), (0.98, 0.025, 0.1), "grau_dunkel")]
    punkte = [(0.98, 1.8, -0.55), (0.99, 1.5, -0.3), (0.99, 0.9, -0.1), (0.99, 0.35, 0.2), (0.98, 0.08, 0.6)]
    for k, mat in enumerate(("licht_violett", "licht_cyan", "licht_violett")):
        dz = (k - 1) * 0.035
        for a, b in zip(punkte, punkte[1:]):
            t.append(stab("baum", (a[0] + dz, a[1], a[2]), (b[0] + dz, b[1], b[2]), 0.012, mat, seiten=5))
    for p in punkte[1:-1]:
        t.append(q("schelle", (0.09, 0.04, 0.05), (p[0] + 0.01, p[1], p[2]), "alu", r=(0, 0)))
    return t


BUFFER = {
    "basis": buffer_basis,
    "plaetze": {
        1: {0: buffer_a1_0, 1: buffer_a1_1, 2: buffer_a1_2, 3: buffer_a1_3},
        2: {1: buffer_a2_1, 2: buffer_a2_2, 3: buffer_a2_3},
        3: {0: buffer_a3_0, 1: buffer_a3_1, 2: buffer_a3_2, 3: buffer_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (-0.9, 0.0, 0.3))],
    "frei": [(-0.9, 0.3, 0.28, 1.55)],
}


# =============================================================================
# Station 3: station_processing -- Bloecke. Kontrollpult (Basis) an der Wand,
# Monitor hinten auf dem Pult (Platz 1), Wallet rechts (Platz 2), Sessel vorn
# (Platz 3). Die Spielfigur sitzt bei (0 | 0,05), Sitzhoehe 0,48, Blick -z.
# =============================================================================

P_H = 0.74
P_AUF = P_H + 0.002
P_Z = -0.7          # Plattenmitte, Tiefe 0,7 -> z -1,05 .. -0,35


def processing_basis():
    t = [q("platte", (1.6, 0.04, 0.68), (0.0, P_H - 0.02, P_Z), "grau_dunkel", r=(0.012, 2)),
         f("kante", (1.6, 0.012, 0.012), (0.0, P_H - 0.03, P_Z + 0.345), "licht_violett")]
    for x in (-0.76, 0.76):
        t.append(q("wange", (0.06, P_H - 0.04, 0.6), (x, (P_H - 0.04) / 2, P_Z), "stahl", r=(0.01, 1)))
    t.append(f("blende", (1.46, 0.35, 0.02), (0.0, 0.52, -0.99), "stahl"))
    t.append(f("blende_licht", (1.2, 0.02, 0.004), (0.0, 0.4, -0.978), "licht_violett"))
    # Tastatur und Konsolenfeld vorn
    t.append(f("tastatur", (0.44, 0.02, 0.15), (-0.05, P_AUF + 0.01, -0.47), "schwarz"))
    t.append(f("tasten", (0.4, 0.004, 0.11), (-0.05, P_AUF + 0.022, -0.47), "licht_violett"))
    t.append(q("konsole", (0.3, 0.05, 0.16), (-0.52, P_AUF + 0.025, -0.47), "stahl", (-8, 0, 0), r=(0.008, 1)))
    for k in range(3):
        t.append(f("knopf", (0.04, 0.012, 0.04), (-0.6 + k * 0.08, P_AUF + 0.056, -0.47),
                   ("licht_gruen", "licht_cyan", "licht_rot")[k]))
    # Kabelbuendel unter dem Pult zur Wand
    t.append(stab("kabel", (-0.3, 0.02, -0.9), (-0.3, 0.35, -1.0), 0.02, "violett"))
    return t


def processing_a1_0():
    """Laptop auf dem Pult."""
    return wg.laptop((0.05, P_AUF, -0.78), (0, 0, 0), breite=0.4, tiefe=0.28, mat="grau_hell", inhalt="balken")


def processing_a1_1():
    t = []
    for s in (-1, 1):
        t += monitor((s * 0.27, P_AUF, -0.85), (0, -s * 10, 0), 0.5, 0.3, "kurve" if s < 0 else "block")
    return t


def processing_a1_2():
    """Monitorbogen: drei Schirme im Halbkreis."""
    t = []
    for i, (x, z, g) in enumerate(((-0.52, -0.78, 32), (0.0, -0.9, 0), (0.52, -0.78, -32))):
        t += monitor((x, P_AUF, z), (0, g, 0), 0.5, 0.32, ("block", "kurve", "linie")[i], fuss_hoehe=0.1)
    return t


def processing_a1_3():
    """Hologramm-Saeule zwischen zwei Monitoren."""
    t = []
    for s in (-1, 1):
        t += monitor((s * 0.5, P_AUF, -0.82), (0, -s * 25, 0), 0.44, 0.3, "block", fuss_hoehe=0.1)
    t.append(zyl("sockel", 0.13, 0.05, (0.0, P_AUF, -0.85), "grau_dunkel", seiten=12))
    t.append(zyl("saeule", 0.07, 0.55, (0.0, P_AUF + 0.05, -0.85), "holo", seiten=10, radius_oben=0.1))
    for k in range(3):
        t.append(ring("holo_ring", 0.13 + 0.02 * k, 0.008, (0.0, P_AUF + 0.18 + k * 0.16, -0.85), "licht_cyan",
                      segmente=14, quer=4))
    t.append(kasten("holo_wuerfel", (0.1, 0.1, 0.1), (0.0, P_AUF + 0.72, -0.85), "licht_violett", (35, 45, 0), rund=(0.01, 1)))
    return t


def processing_a2_0():
    """Notizzettel mit Stift."""
    return [f("zettel", (0.14, 0.004, 0.14), (0.52, P_AUF + 0.002, -0.47), "gelb", (0, 12, 0)),
            f("zettel2", (0.12, 0.004, 0.12), (0.62, P_AUF + 0.006, -0.55), "papier", (0, -18, 0)),
            walze("stift", 0.008, 0.14, (0.5, P_AUF + 0.012, -0.44), "violett")]


def processing_a2_1():
    """Hardware-Stick in einer Ladeschale."""
    return [q("schale", (0.14, 0.03, 0.1), (0.55, P_AUF + 0.015, -0.48), "weiss", r=(0.008, 1)),
            q("stick", (0.1, 0.02, 0.04), (0.55, P_AUF + 0.04, -0.48), "schwarz", (0, 15, 0), r=(0.006, 1)),
            f("stick_led", (0.02, 0.004, 0.02), (0.58, P_AUF + 0.052, -0.47), "licht_violett")]


def _tresorbox(x, y, z, g=0.26):
    return [q("box", (g, g * 0.8, g), (x, y + g * 0.4, z), "stahl", r=(0.012, 1)),
            f("tuer", (g * 0.8, g * 0.6, 0.006), (x, y + g * 0.4, z + g / 2 + 0.003), "grau_hell"),
            zylinder("rad", g * 0.12, 0.02, (x - g * 0.12, y + g * 0.4, z + g / 2 + 0.012), "grau_dunkel", seiten=8, dreh=(90, 0, 0), rund=(0, 0)),
            f("led", (0.02, 0.02, 0.004), (x + g * 0.25, y + g * 0.6, z + g / 2 + 0.008), "licht_gruen")]


def processing_a2_2():
    return _tresorbox(0.56, P_AUF, -0.5)


def processing_a2_3():
    """Tresor mit Tastenfeld unter dem Pult, Stick obenauf in der Schale."""
    x, z = 0.5, -0.72
    t = [q("tresor", (0.4, 0.5, 0.42), (x, 0.26, z), "stahl", r=(0.015, 1)),
         f("tuer", (0.32, 0.42, 0.008), (x, 0.26, z + 0.214), "grau_hell"),
         f("feld", (0.1, 0.12, 0.006), (x + 0.08, 0.34, z + 0.222), "schwarz"),
         f("feld_licht", (0.08, 0.03, 0.004), (x + 0.08, 0.38, z + 0.226), "licht_cyan"),
         zylinder("rad", 0.05, 0.02, (x - 0.06, 0.26, z + 0.228), "grau_dunkel", seiten=10, dreh=(90, 0, 0), rund=(0, 0)),
         f("fuss", (0.38, 0.01, 0.4), (x, 0.005, z), "gummi")]
    t += processing_a2_1()
    return t


def processing_a3_0():
    """Klappstuhl."""
    t = [q("sitz", (0.42, 0.03, 0.4), (0.0, 0.465, 0.05), "grau_mittel", r=(0.008, 1)),
         q("lehne", (0.4, 0.16, 0.025), (0.0, 0.8, 0.26), "grau_mittel", (-8, 0, 0), r=(0.006, 1))]
    for s in (-1, 1):
        t.append(stab("bein_a", (s * 0.19, 0.012, -0.14), (s * 0.19, 0.9, 0.27), 0.013, "grau_dunkel"))
        t.append(stab("bein_b", (s * 0.19, 0.012, 0.26), (s * 0.19, 0.45, -0.02), 0.013, "grau_dunkel"))
    return t


def _sternfuss(r=0.28):
    t = [zyl("saeule", 0.03, 0.34, (0.0, 0.07, 0.05), "grau_dunkel", seiten=8)]
    for i in range(5):
        a = math.radians(90 + i * 72)
        e = (math.cos(a) * r, 0.04, 0.05 + math.sin(a) * r)
        t.append(stab("fuss", (0.0, 0.08, 0.05), e, 0.018, "grau_dunkel", seiten=4))
        t.append(kugel("rolle", 0.03, (e[0], 0.03, e[2]), "schwarz", stufen=1))
    return t


def processing_a3_1():
    """Buerostuhl."""
    t = _sternfuss()
    t.append(q("sitz", (0.46, 0.07, 0.44), (0.0, 0.445, 0.05), "stoff_grau", r=(0.025, 2)))
    t.append(q("lehne", (0.42, 0.45, 0.06), (0.0, 0.8, 0.29), "stoff_grau", (-6, 0, 0), r=(0.025, 2)))
    t.append(f("traeger", (0.05, 0.3, 0.03), (0.0, 0.55, 0.28), "grau_dunkel"))
    return t


def _gaming(farbe="leder_hell", streifen="violett", hoch=0.75):
    t = _sternfuss(0.3)
    t.append(q("sitz", (0.5, 0.09, 0.48), (0.0, 0.435, 0.05), "leder", r=(0.03, 2)))
    t.append(q("lehne", (0.5, hoch, 0.09), (0.0, 0.48 + hoch / 2, 0.31), "leder", (-8, 0, 0), r=(0.03, 2)))
    t.append(f("lehne_streifen", (0.12, hoch - 0.1, 0.006), (0.0, 0.48 + hoch / 2, 0.36), streifen, (-8, 0, 0)))
    t.append(q("kopfkissen", (0.26, 0.1, 0.05), (0.0, 0.48 + hoch - 0.12, 0.26), farbe, (-8, 0, 0), r=(0.02, 1)))
    for s in (-1, 1):
        t.append(q("armlehne", (0.07, 0.04, 0.3), (s * 0.29, 0.66, 0.08), "schwarz", r=(0.012, 1)))
        t.append(f("armstuetze", (0.04, 0.16, 0.04), (s * 0.29, 0.56, 0.12), "grau_dunkel"))
    return t


def processing_a3_2():
    return _gaming()


def processing_a3_3():
    """Kommandosessel: Gaming-Sessel mit Leuchtkonsolen an den Armlehnen."""
    t = _gaming("violett", "licht_violett", 0.85)
    for s in (-1, 1):
        t.append(q("konsole", (0.14, 0.06, 0.22), (s * 0.4, 0.7, 0.06), "grau_dunkel", (0, 0, s * 10), r=(0.01, 1)))
        t.append(f("konsole_licht", (0.1, 0.004, 0.16), (s * 0.4, 0.735, 0.06), "licht_cyan", (0, 0, s * 10)))
        t.append(f("konsole_arm", (0.08, 0.03, 0.04), (s * 0.34, 0.67, 0.08), "grau_dunkel"))
    return t


PROCESSING = {
    "basis": processing_basis,
    "plaetze": {
        1: {0: processing_a1_0, 1: processing_a1_1, 2: processing_a1_2, 3: processing_a1_3},
        2: {0: processing_a2_0, 1: processing_a2_1, 2: processing_a2_2, 3: processing_a2_3},
        3: {0: processing_a3_0, 1: processing_a3_1, 2: processing_a3_2, 3: processing_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.09,
    "figur": [("sitz", (0.0, 0.48, 0.05))],
}


# =============================================================================
# Station 4: station_transport -- Kuehlung. Lueftungskanal (Basis) hinten,
# Luefter links (Platz 1), Klima rechts hinten (Platz 2), Wasser vorn (Platz 3).
# =============================================================================

def transport_basis():
    t = [q("kanal_quer", (2.1, 0.32, 0.34), (0.0, 1.95, -0.88), "alu", r=(0.015, 1)),
         q("kanal_senk", (0.4, 1.8, 0.36), (0.0, 0.9, -0.87), "alu", r=(0.015, 1)),
         f("bogen", (0.44, 0.1, 0.4), (0.0, 1.78, -0.87), "grau_hell")]
    for k in range(6):
        t.append(f("gitter", (0.3, 0.02, 0.004), (0.0, 0.35 + k * 0.08, -0.688), "grau_dunkel"))
    for x in (-0.9, 0.9):
        t.append(f("schelle", (0.04, 0.36, 0.36), (x, 1.95, -0.88), "stahl"))
    t.append(f("licht", (2.1, 0.03, 0.004), (0.0, 1.82, -0.708), "licht_cyan"))
    t.append(f("sockel", (0.5, 0.06, 0.4), (0.0, 0.03, -0.86), "grau_dunkel"))
    t.append(f("pfeil", (0.08, 0.2, 0.004), (0.0, 1.2, -0.688), "licht_cyan"))
    return t


def transport_a1_0():
    """Tischventilator auf einer Kiste."""
    t = [q("kiste", (0.35, 0.35, 0.3), (-0.65, 0.175, -0.6), "karton")]
    t.append(zyl("fuss", 0.08, 0.02, (-0.65, 0.35, -0.6), "weiss", seiten=10))
    t.append(f("hals", (0.03, 0.15, 0.03), (-0.65, 0.44, -0.6), "weiss"))
    t += luefter_rund((-0.65, 0.62, -0.58), (0, 30, 0), 0.12, "weiss", 0.04)
    return t


def transport_a1_1():
    """Wandluefter im Rahmen auf einem Staender."""
    t = [f("staender", (0.05, 1.0, 0.05), (-0.65, 0.5, -0.85), "stahl"),
         f("fussplatte", (0.3, 0.02, 0.3), (-0.65, 0.01, -0.8), "grau_mittel"),
         q("rahmen", (0.5, 0.5, 0.12), (-0.65, 1.2, -0.8), "weiss", r=(0.012, 1))]
    t += luefter_rund((-0.65, 1.2, -0.72), (0, 0, 0), 0.2)
    return t


def transport_a1_2():
    """Luefterwand: vier Luefter in einem Rahmen."""
    t = [q("rahmen", (0.7, 1.4, 0.2), (-0.7, 0.8, -0.8), "grau_hell", r=(0.015, 1)),
         f("fuss", (0.7, 0.1, 0.3), (-0.7, 0.05, -0.8), "grau_dunkel")]
    for i in range(2):
        for k in range(2):
            t += luefter_rund((-0.86 + i * 0.32, 0.46 + k * 0.62, -0.69), (0, 0, 0), 0.13)
    t.append(f("licht", (0.6, 0.02, 0.004), (-0.7, 1.47, -0.698), "licht_cyan"))
    return t


def transport_a1_3():
    """Industrie-Luefter: grosse Trommel auf Rollgestell, schraeg gestellt."""
    x, z = -0.65, -0.4
    t = [f("gestell", (0.6, 0.04, 0.5), (x, 0.12, z), "stahl")]
    for s in (-1, 1):
        t.append(stab("buegel", (x + s * 0.32, 0.12, z), (x + s * 0.34, 0.55, z), 0.02, "stahl"))
        for v in (-1, 1):
            t.append(kugel("rolle", 0.05, (x + s * 0.25, 0.05, z + v * 0.2), "schwarz", stufen=1))
    t += [zylinder("trommel", 0.32, 0.2, (x, 0.55, z), "violett_dunkel", seiten=16, dreh=(90, 30, 0), rund=(0, 0))]
    t += luefter_rund(punkt((x, 0.55, z), (0, 30, 0), (0, 0, 0.09)), (0, 30, 0), 0.28, "violett", 0.03)
    t.append(zylinder("gitter", 0.3, 0.01, punkt((x, 0.55, z), (0, 30, 0), (0, 0, 0.12)), "grau_hell", seiten=12, dreh=(90, 30, 0), rund=(0, 0)))
    return t


def transport_a2_0():
    """Offenes Fenster: Fensterfluegel im Rahmen, gekippt."""
    return [f("rahmen_l", (0.04, 1.0, 0.06), (0.35, 1.0, -1.02), "weiss"),
            f("rahmen_r", (0.04, 1.0, 0.06), (1.0, 1.0, -1.02), "weiss"),
            f("rahmen_o", (0.69, 0.04, 0.06), (0.675, 1.48, -1.02), "weiss"),
            f("rahmen_u", (0.69, 0.04, 0.06), (0.675, 0.52, -1.02), "weiss"),
            f("stuetze", (0.05, 0.5, 0.05), (0.675, 0.25, -1.02), "stahl"),
            f("fluegel", (0.6, 0.9, 0.03), (0.675, 1.0, -0.9), "glas_kalt", (-15, 0, 0))]


def transport_a2_1():
    """Mobiles Klimageraet mit Abluftschlauch zum Kanal."""
    t = [q("geraet", (0.4, 0.75, 0.35), (0.65, 0.375, -0.62), "weiss", r=(0.03, 2)),
         f("gitter", (0.3, 0.12, 0.004), (0.65, 0.6, -0.443), "grau_mittel"),
         f("anzeige", (0.1, 0.04, 0.004), (0.65, 0.68, -0.443), "licht_cyan")]
    t.append(stab("schlauch", (0.65, 0.75, -0.7), (0.5, 1.2, -0.85), 0.06, "grau_hell"))
    t.append(stab("schlauch2", (0.5, 1.2, -0.85), (0.3, 1.7, -0.85), 0.06, "grau_hell"))
    return t


def transport_a2_2():
    """Kuehlaggregat mit grossem Luefter oben."""
    t = [q("korpus", (0.7, 0.8, 0.6), (0.7, 0.4, -0.68), "weiss", r=(0.03, 2)),
         f("band", (0.704, 0.06, 0.604), (0.7, 0.62, -0.68), "violett")]
    t.append(zyl("ring", 0.25, 0.05, (0.7, 0.8, -0.68), "grau_dunkel", seiten=14))
    t.append(zyl("nabe", 0.05, 0.07, (0.7, 0.8, -0.68), "alu", seiten=8))
    for k in range(3):
        t.append(f("fluegel", (0.42, 0.01, 0.07), (0.7, 0.845, -0.68), "grau_hell", (0, k * 60 + 20, 0)))
    t.append(f("gitter", (0.5, 0.35, 0.004), (0.7, 0.3, -0.378), "grau_mittel"))
    t.append(f("anzeige", (0.12, 0.06, 0.004), (0.9, 0.52, -0.378), "licht_cyan"))
    return t


def transport_a2_3():
    """Kleiner Kuehlturm mit Leuchtband und Rohren zum Kanal."""
    t = [zyl("turm", 0.36, 1.2, (0.7, 0.0, -0.66), "weiss", seiten=16, radius_oben=0.28),
         zyl("band", 0.34, 0.12, (0.7, 0.7, -0.66), "violett", seiten=16, radius_oben=0.33),
         zyl("rand", 0.29, 0.08, (0.7, 1.2, -0.66), "grau_dunkel", seiten=16),
         zyl("luefter", 0.2, 0.03, (0.7, 1.28, -0.66), "grau_hell", seiten=10),
         zyl("dampf", 0.14, 0.22, (0.7, 1.33, -0.66), "violett_hell", seiten=8, radius_oben=0.2)]
    t.append(stab("rohr", (0.4, 0.3, -0.85), (0.24, 0.3, -0.85), 0.035, "cyan"))
    t.append(f("licht", (0.02, 0.5, 0.004), (0.7, 0.4, -0.3), "licht_cyan"))
    return t


def transport_a3_0():
    """Wassereimer."""
    return [zyl("eimer", 0.13, 0.28, (-0.1, 0.0, 0.55), "cyan", seiten=12, radius_oben=0.15),
            zyl("wasser", 0.135, 0.005, (-0.1, 0.25, 0.55), "wasser", seiten=12),
            ring("henkel", 0.14, 0.006, (-0.1, 0.3, 0.55), "grau_dunkel", dreh=(90, 0, 0), segmente=10, quer=3, anteil=0.5)]


def transport_a3_1():
    """Eimer mit aufgerolltem Schlauch."""
    t = transport_a3_0()
    for k in range(3):
        t.append(ring("schlauch", 0.2 - k * 0.012, 0.018, (0.35, 0.02 + k * 0.036, 0.5), "gruen_hell", segmente=14, quer=5))
    t.append(stab("schlauch_weg", (0.2, 0.03, 0.4), (0.1, 0.03, -0.3), 0.018, "gruen_hell"))
    return t


def transport_a3_2():
    """Kuehlkreislauf: Tank, Pumpe und Rohrschleife."""
    t = [zyl("tank", 0.18, 0.6, (-0.45, 0.0, 0.5), "alu", seiten=12),
         zyl("tank_deckel", 0.19, 0.03, (-0.45, 0.6, 0.5), "violett", seiten=12),
         f("tank_fenster", (0.04, 0.4, 0.004), (-0.45, 0.3, 0.682), "wasser"),
         q("pumpe", (0.26, 0.2, 0.2), (0.05, 0.1, 0.55), "violett_dunkel", r=(0.02, 1)),
         zylinder("motor", 0.07, 0.16, (0.05, 0.12, 0.72), "grau_dunkel", seiten=10, dreh=(90, 0, 0), rund=(0, 0))]
    for a, b, mat in (((-0.27, 0.15, 0.5), (-0.08, 0.15, 0.5), "cyan"), ((0.18, 0.1, 0.55), (0.55, 0.1, 0.55), "cyan"),
                      ((0.55, 0.1, 0.55), (0.55, 0.1, 0.1), "cyan"), ((0.55, 0.1, 0.1), (-0.45, 0.62, 0.3), "violett")):
        t.append(stab("rohr", a, b, 0.025, mat))
    return t


def transport_a3_3():
    """Tauchkuehlbecken: Wanne mit leuchtender Fluessigkeit, Platinen darin."""
    x0, x1, z0, z1, h = -0.75, 0.75, 0.15, 0.85, 0.55
    t = [f("boden", (x1 - x0, 0.04, z1 - z0), ((x0 + x1) / 2, 0.02, (z0 + z1) / 2), "grau_dunkel")]
    for (bx, bz, sx, sz) in (((x0 + x1) / 2, z0 + 0.02, x1 - x0, 0.04), ((x0 + x1) / 2, z1 - 0.02, x1 - x0, 0.04),
                             (x0 + 0.02, (z0 + z1) / 2, 0.04, z1 - z0 - 0.08), (x1 - 0.02, (z0 + z1) / 2, 0.04, z1 - z0 - 0.08)):
        t.append(f("wand", (sx, h, sz), (bx, h / 2, bz), "wasser_dunkel" if sz > 0.05 or bz < 0.5 else "wasser"))
    t.append(f("vorn_glas", (x1 - x0 - 0.1, h - 0.15, 0.004), ((x0 + x1) / 2, h / 2, z1 + 0.003), "wasser"))
    t.append(f("oberflaeche", (x1 - x0 - 0.08, 0.01, z1 - z0 - 0.08), ((x0 + x1) / 2, h - 0.06, (z0 + z1) / 2), "wasser"))
    for i in range(6):
        x = x0 + 0.2 + i * 0.22
        t.append(f("platine", (0.03, 0.3, 0.4), (x, h - 0.1, (z0 + z1) / 2), "violett_dunkel"))
        t.append(f("platine_licht", (0.032, 0.02, 0.36), (x, h - 0.05, (z0 + z1) / 2), "licht_violett"))
    t.append(f("rand_licht", (x1 - x0, 0.02, 0.01), ((x0 + x1) / 2, h + 0.01, z1 - 0.01), "licht_cyan"))
    return t


TRANSPORT = {
    "basis": transport_basis,
    "plaetze": {
        1: {0: transport_a1_0, 1: transport_a1_1, 2: transport_a1_2, 3: transport_a1_3},
        2: {0: transport_a2_0, 1: transport_a2_1, 2: transport_a2_2, 3: transport_a2_3},
        3: {0: transport_a3_0, 1: transport_a3_1, 2: transport_a3_2, 3: transport_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.13,
    "figur": None,
}


# =============================================================================
# Station 5: station_special -- Staking. Pult mit Bildschirm (Basis), Knoten
# links hinten (Platz 1), Absicherung rechts (Platz 2), Kurve vorn/hinten
# (Platz 3). Roman steht bei (-0,9 | 0,5).
# =============================================================================

def special_basis():
    t = [q("pult", (1.0, 0.9, 0.45), (0.15, 0.45, -0.5), "violett_dunkel", r=(0.02, 2)),
         q("pult_platte", (1.06, 0.05, 0.52), (0.15, 0.925, -0.48), "grau_dunkel", r=(0.012, 1)),
         f("front_licht", (0.9, 0.03, 0.004), (0.15, 0.8, -0.273), "licht_violett"),
         f("front_feld", (0.5, 0.4, 0.004), (0.15, 0.45, -0.273), "violett")]
    t += monitor((0.15, 0.952, -0.6), (0, 0, 0), 0.6, 0.36, "block")
    t.append(f("tastatur", (0.4, 0.02, 0.13), (0.15, 0.96, -0.36), "schwarz"))
    t.append(f("matte", (1.1, 0.01, 1.0), (0.15, 0.005, -0.3), "gummi"))
    return t


def _mini_pc(x, y, z, g=0.0):
    return [q("mini", (0.16, 0.06, 0.16), (x, y + 0.03, z), "grau_hell", (0, g, 0), r=(0.012, 1)),
            f("mini_led", (0.03, 0.01, 0.004), punkt((x, y + 0.03, z), (0, g, 0), (0.04, 0, 0.082)), "licht_violett", (0, g, 0))]


def _hocker(x, z, h=0.45):
    return [zyl("hocker", 0.16, 0.04, (x, h - 0.04, z), "stahl", seiten=10),
            zyl("hocker_bein", 0.03, h - 0.04, (x, 0.0, z), "grau_dunkel", seiten=6),
            zyl("hocker_fuss", 0.16, 0.02, (x, 0.0, z), "grau_dunkel", seiten=10)]


def special_a1_0():
    return _hocker(-0.75, -0.55) + _mini_pc(-0.75, 0.45, -0.55, 15)


def special_a1_1():
    return _hocker(-0.75, -0.55) + _mini_pc(-0.75, 0.45, -0.55, 15) + _mini_pc(-0.75, 0.51, -0.55, -10)


def _regal_klein(x, z, h, b=0.5, t=0.4):
    teile = []
    for sx in (-1, 1):
        teile.append(f("seite", (0.025, h, t), (x + sx * (b / 2 - 0.0125), h / 2, z), "alu"))
    ebenen = [0.05 + i * 0.32 for i in range(int(h / 0.32) + 1) if 0.05 + i * 0.32 < h]
    for y in ebenen:
        teile.append(f("boden", (b - 0.05, 0.02, t), (x, y, z), "alu"))
    return teile, ebenen


def special_a1_2():
    """Knoten-Regal mit vier Mini-PCs."""
    t, ebenen = _regal_klein(-0.75, -0.6, 1.0)
    for y in ebenen[:3]:
        t += _mini_pc(-0.75, y + 0.01, -0.6)
    t.append(f("licht", (0.45, 0.02, 0.004), (-0.75, 0.98, -0.398), "licht_violett"))
    return t


def special_a1_3():
    """Knoten-Schrank: geschlossener Schrank mit Leuchtreihen."""
    t = [q("schrank", (0.55, 1.6, 0.5), (-0.75, 0.8, -0.6), "rack", r=(0.015, 1)),
         f("front", (0.49, 1.5, 0.006), (-0.75, 0.8, -0.347), "rack_front")]
    for k in range(6):
        t.append(f("led", (0.12 + 0.08 * (k % 3), 0.025, 0.004), (-0.9 + 0.04 * (k % 3), 0.3 + k * 0.22, -0.343),
                   "licht_violett" if k % 2 else "licht_cyan"))
    return t


def special_a2_0():
    """Kassette mit Vorhaengeschloss."""
    return [q("kassette", (0.3, 0.16, 0.22), (0.9, 0.08, 0.1), "stahl", r=(0.012, 1)),
            f("lasche", (0.04, 0.05, 0.02), (0.9, 0.12, 0.215), "grau_dunkel"),
            q("schloss", (0.08, 0.08, 0.03), (0.9, 0.07, 0.24), "gelb", r=(0.008, 1)),
            ring("buegel", 0.03, 0.008, (0.9, 0.12, 0.24), "grau_hell", dreh=(90, 0, 0), segmente=8, quer=3, anteil=0.5)]


def _pfosten_r(h=1.1):
    return [f("pfosten", (0.06, h, 0.06), (0.9, h / 2, -0.05), "stahl"),
            f("fussplatte", (0.26, 0.02, 0.26), (0.9, 0.01, -0.05), "grau_mittel")]


def special_a2_1():
    """Schluesselkasten auf einem Pfosten."""
    t = _pfosten_r()
    t += [q("kasten", (0.28, 0.34, 0.08), (0.9, 1.1, 0.02), "gelb", r=(0.012, 1)),
          f("tuer", (0.22, 0.28, 0.004), (0.9, 1.1, 0.062), "papier")]
    for k in range(3):
        t.append(f("schluessel", (0.02, 0.06, 0.004), (0.84 + k * 0.06, 1.1, 0.066), "grau_mittel"))
    return t


def special_a2_2():
    """Fingerabdruckscanner auf Saeule."""
    t = _pfosten_r(1.0)
    t += [q("scanner", (0.16, 0.24, 0.08), (0.9, 1.05, 0.0), "grau_dunkel", (-20, 0, 0), r=(0.012, 1)),
          f("feld", (0.08, 0.08, 0.004), punkt((0.9, 1.05, 0.0), (-20, 0, 0), (0, -0.03, 0.042)), "licht_cyan", (-20, 0, 0)),
          f("status", (0.06, 0.015, 0.004), punkt((0.9, 1.05, 0.0), (-20, 0, 0), (0, 0.07, 0.042)), "licht_gruen", (-20, 0, 0))]
    return t


def special_a2_3():
    """Sicherheitsschleuse: Torrahmen mit Leuchtband und Scanner."""
    t = []
    for z in (-0.2, 0.75):
        t.append(q("saeule", (0.12, 1.9, 0.12), (0.9, 0.95, z), "grau_dunkel", r=(0.012, 1)))
        t.append(f("saeule_licht", (0.004, 1.6, 0.03), (0.838, 0.95, z), "licht_cyan"))
    t.append(q("sturz", (0.14, 0.14, 1.07), (0.9, 1.97, 0.275), "violett_dunkel", r=(0.012, 1)))
    t.append(f("sturz_licht", (0.004, 0.04, 0.9), (0.828, 1.97, 0.275), "licht_violett"))
    t.append(q("scanner", (0.1, 0.18, 0.06), (0.9, 1.1, -0.11), "schwarz", r=(0.008, 1)))
    t.append(f("scanner_feld", (0.004, 0.06, 0.04), (0.848, 1.12, -0.11), "licht_gruen"))
    t.append(f("schwelle", (0.3, 0.012, 0.83), (0.9, 0.006, 0.275), "warn_gelb"))
    return t


def _staffelei(x, z, g=-20):
    return [stab("bein_l", (x - 0.15, 0.0, z + 0.1), (x - 0.05, 1.2, z), 0.012, "holz"),
            stab("bein_r", (x + 0.15, 0.0, z + 0.1), (x + 0.05, 1.2, z), 0.012, "holz"),
            stab("bein_h", (x, 0.0, z - 0.25), (x, 1.15, z - 0.02), 0.012, "holz"),
            f("ablage", (0.4, 0.02, 0.05), (x, 0.7, z + 0.07), "holz")]


def special_a3_0():
    """Papierausdruck mit Kurve an einer kleinen Staffelei."""
    x, z = 0.35, 0.55
    t = _staffelei(x, z)
    t.append(f("papier", (0.34, 0.45, 0.006), (x, 0.95, z + 0.06), "papier", (-6, 0, 0)))
    for k in range(4):
        hk = 0.05 + k * 0.05
        t.append(f("balken", (0.05, hk, 0.004), (x - 0.1 + k * 0.07, 0.8 + hk / 2, z + 0.068), "violett", (-6, 0, 0)))
    return t


def special_a3_1():
    """Tablet auf der Staffelei."""
    x, z = 0.35, 0.55
    t = _staffelei(x, z)
    t.append(q("tablet", (0.36, 0.26, 0.02), (x, 0.85, z + 0.06), "schwarz", (-8, 0, 0), r=(0.006, 1)))
    t += schirm((x, 0.85, z + 0.06), (-8, 0, 0), 0.32, 0.22, "kurve", tiefe=0.012)
    return t


def _wand_schirm(b=0.9, h=0.55, y=1.55):
    t = [f("mast_l", (0.05, y + h / 2, 0.05), (-0.1, (y + h / 2) / 2, -0.95), "stahl"),
         f("mast_r", (0.05, y + h / 2, 0.05), (0.4, (y + h / 2) / 2, -0.95), "stahl"),
         f("fuss", (0.7, 0.03, 0.2), (0.15, 0.015, -0.95), "grau_dunkel")]
    t.append(q("gehaeuse", (b, h, 0.04), (0.15, y, -0.9), "schwarz", r=(0.008, 1)))
    t += schirm((0.15, y, -0.9), (0, 0, 0), b - 0.06, h - 0.06, "kurve", tiefe=0.021)
    return t


def special_a3_2():
    return _wand_schirm()


def special_a3_3():
    """Wandbildschirm plus Laufschrift-Leiste darueber."""
    t = _wand_schirm()
    t.append(q("leiste", (1.2, 0.12, 0.05), (0.15, 1.98, -0.92), "schwarz", r=(0.006, 1)))
    for k in range(7):
        t.append(f("zeichen", (0.1, 0.05, 0.004), (-0.3 + k * 0.15, 1.98, -0.893),
                   "licht_gruen" if k % 3 else "licht_violett"))
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
    "figur": [("steh", (-0.9, 0.0, 0.5))],
    "frei": [(-0.9, 0.5, 0.28, 1.55)],
}


# =============================================================================
# Bauen, Pruefen, Exportieren
# =============================================================================

STATIONEN = {"intake": INTAKE, "buffer": BUFFER, "processing": PROCESSING,
             "transport": TRANSPORT, "special": SPECIAL}
wg.STATIONEN = STATIONEN


def ueberschneidungen_zeigen(station):
    from mathutils.bvhtree import BVHTree
    wg.alles_loeschen()
    objekte = {}
    for name, bauen, platz, stufe in wg.alle_dateien(station):
        objekte[(platz, stufe)] = wg.zusammenfuegen(bauen(), name)
    deps = bpy.context.evaluated_depsgraph_get()
    baeume = {k: BVHTree.FromObject(o, deps) for k, o in objekte.items()}
    for a in sorted(objekte):
        for b in sorted(objekte):
            if a >= b or a[0] == b[0]:
                continue
            paare = baeume[a].overlap(baeume[b])
            if paare:
                c = objekte[a].data.polygons[paare[0][0]].center
                print("   Ort %s/%s: Godot (%.2f, %.2f, %.2f)" % (a, b, c.x, c.z, -c.y))


def budget_pruefen(station):
    zahlen = {}
    for name, bauen, platz, stufe in wg.alle_dateien(station):
        wg.alles_loeschen()
        zahlen[(platz, stufe)] = wg.dreiecke(wg.zusammenfuegen(bauen(), name))
    basis = zahlen[(0, 0)]
    teuerste = {}
    for (platz, stufe), n in zahlen.items():
        if platz:
            teuerste[platz] = max(teuerste.get(platz, 0), n)
    voll = basis + sum(teuerste.values())
    print("  Budget %s: Basis %d + Plaetze %s = %d / %d  %s"
          % (station, basis, [teuerste[p] for p in sorted(teuerste)], voll, BUDGET_GESAMT,
             "ok" if voll <= BUDGET_GESAMT else "UEBER BUDGET"))
    return voll


def altmodelle(station):
    """station_<id>_1/_2/_3.glb: Basis plus jeder Platz auf Modellstufe m."""
    daten = STATIONEN[station]
    for m in (1, 2, 3):
        wg.alles_loeschen()
        teile = daten["basis"]()
        for platz, stufen in daten["plaetze"].items():
            if m in stufen:
                teile += stufen[m]()
        name = "station_%s_%d" % (station, m)
        obj = wg.zusammenfuegen(teile, name)
        wg.exportieren(obj, os.path.join(AUSGABE, name + ".glb"))
        print("  %-42s %5d Dreiecke" % (name, wg.dreiecke(obj)))


# =============================================================================
# Symbole: Render wie build_symbole_wg.py, dazu eine 6-px-Kontur (Sticker)
# =============================================================================

TINTE = tuple(int("1B1726"[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
KONTUR = 6


def sticker(pfad, ausblenden):
    G = sy.GROESSE
    bild = bpy.data.images.load(pfad)
    px = np.array(bild.pixels[:], dtype=np.float32).reshape(G, G, 4)
    bpy.data.images.remove(bild)
    a = px[:, :, 3].copy()
    if ausblenden:
        y = np.arange(G, dtype=np.float32)
        t = np.clip(y / (G * 0.30), 0.0, 1.0)
        a *= (t * t * (3.0 - 2.0 * t))[:, None]
    R = KONTUR
    rand = R + 2
    pad = np.pad(a, rand)
    d = np.zeros_like(a)
    for dy in range(-R - 1, R + 2):
        for dx in range(-R - 1, R + 2):
            w = min(1.0, max(0.0, R + 1.0 - math.hypot(dx, dy)))
            if w <= 0.0:
                continue
            np.maximum(d, pad[rand + dy:rand + dy + G, rand + dx:rand + dx + G] * w, out=d)
    tinte = np.array(TINTE, dtype=np.float32)
    a_neu = a + d * (1.0 - a)
    rgb = (px[:, :, :3] * a[:, :, None] + tinte * (d * (1.0 - a))[:, :, None]) / np.maximum(a_neu, 1e-6)[:, :, None]
    aus = np.dstack([rgb, a_neu]).astype(np.float32)
    ziel = bpy.data.images.new("symbol", width=G, height=G, alpha=True)
    ziel.pixels[:] = aus.ravel()
    ziel.filepath_raw = pfad
    ziel.file_format = "PNG"
    ziel.save()
    bpy.data.images.remove(ziel)


sy.nachbearbeiten = sticker
sy.FUELLUNG = 0.78
sy.AZIMUT = {
    ("intake", 0): 30, ("intake", 1): 35, ("intake", 2): 30, ("intake", 3): 25,
    ("buffer", 0): 30, ("buffer", 1): 20, ("buffer", 2): 20, ("buffer", 3): 35,
    ("processing", 0): 35, ("processing", 1): 20, ("processing", 2): 30, ("processing", 3): 200,
    ("transport", 0): 30, ("transport", 1): 30, ("transport", 2): 25, ("transport", 3): 30,
    ("special", 0): 30, ("special", 1): 30, ("special", 2): -40, ("special", 3): 20,
}
sy.MOTIVE = {
    ("intake", 2, 1): {"behalten": ["batterie", "deckel", "pol"]},
    ("processing", 2, 3): {"behalten": ["tresor", "tuer", "feld", "feld_licht", "rad"]},
    ("buffer", 3, 3): {"fokus_ab": 0.0},
    ("transport", 3, 1): {"behalten": ["schlauch", "eimer", "wasser", "henkel"]},
}


# =============================================================================
# Vorschau
# =============================================================================

def _png_lesen(pfad):
    bild = bpy.data.images.load(pfad)
    w, h = bild.size
    px = np.array(bild.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(bild)
    return px


def _png_schreiben(px, pfad):
    h, w = px.shape[:2]
    ziel = bpy.data.images.new("bogen", width=w, height=h, alpha=True)
    ziel.pixels[:] = px.ravel()
    ziel.filepath_raw = pfad
    ziel.file_format = "PNG"
    ziel.save()
    bpy.data.images.remove(ziel)


def vorschau_stufen(station, groesse=700):
    """2 x 2: alle Plaetze auf m0, m1, m2, m3 -- Spielwinkel aus (+1,+1,+1)."""
    os.makedirs(VORSCHAU, exist_ok=True)
    kacheln = []
    for m in range(4):
        wg.alles_loeschen()
        wg.licht_und_welt(hintergrund="#E6E2F2")
        for name, bauen, platz, stufe in wg.alle_dateien(station):
            if platz == 0 or stufe == m:
                wg.zusammenfuegen(bauen(), name)
        wg._umgebung(station, Vector((0, 0, 0)))
        wg._beschriftung("m%d" % m, Vector((1.25, -1.25, -0.75)), groesse=0.22)
        wg._kamera_iso((0.0, 0.0, 0.85), 3.6, (groesse, groesse))
        pfad = os.path.join(VORSCHAU, "_tmp_%s_%d.png" % (station, m))
        bpy.context.scene.render.filepath = pfad
        bpy.ops.render.render(write_still=True)
        kacheln.append(_png_lesen(pfad))
        os.remove(pfad)
    oben = np.concatenate([kacheln[0], kacheln[1]], axis=1)
    unten = np.concatenate([kacheln[2], kacheln[3]], axis=1)
    bogen = np.concatenate([unten, oben], axis=0)
    ziel = os.path.join(VORSCHAU, "station_%s_stufen.png" % station)
    _png_schreiben(bogen, ziel)
    print("  Vorschau:", ziel)


def argumente():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    nur = None
    if "--nur" in args:
        nur = args[args.index("--nur") + 1].split(",")
    return {"vorschau": "--vorschau" in args, "symbole": "--symbole" in args,
            "kein_export": "--kein_export" in args, "nur": nur}


def main():
    a = argumente()
    print("")
    print("=== STATIONEN PRODUKT (N41) ===")
    probleme = 0
    budgets = {}
    for station in STATIONEN:
        if a["nur"] and station not in a["nur"]:
            continue
        print("--", station)
        n = wg.baue_station(station, export=not a["kein_export"])
        if n:
            ueberschneidungen_zeigen(station)
        probleme += n
        budgets[station] = budget_pruefen(station)
        if not a["kein_export"]:
            altmodelle(station)
        if a["vorschau"]:
            vorschau_stufen(station)
        if a["symbole"]:
            os.makedirs(AUSGABE_UI, exist_ok=True)
            sy.symbole_station(station)
    if a["symbole"]:
        sy.kontaktbogen([s for s in STATIONEN if not a["nur"] or s in a["nur"]])
    print("")
    for s, n in budgets.items():
        print("  %-12s volle Ausstattung %5d Dreiecke%s" % (s, n, "" if n <= BUDGET_GESAMT else "  !! ueber Budget"))
    print("  Probleme gesamt: %d" % probleme)


if __name__ == "__main__":
    main()
