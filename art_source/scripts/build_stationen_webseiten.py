"""Stationen, Ausstattung und Symbole der Welt 3 (`webseiten`, Nachtplan N21).

Aufruf:
    blender --background --python art_source/scripts/build_stationen_webseiten.py
    ... -- --vorschau --nah            Vorschaubilder je Station
    ... -- --symbole                   Symbole (256 x 256, Sticker-Kontur)
    ... -- --nur intake,buffer         nur diese Stationen
    ... -- --kein_export               nur pruefen

Vertrag (docs/NACHT_PLAN.md Paragraf 5, docs/nacht/ausstattung_welten.md):
    project/assets/stations/webseiten/station_<id>_basis.glb
    project/assets/stations/webseiten/station_<id>_ausstattung_<n>_<m>.glb
    project/assets/stations/webseiten/station_<id>_<1|2|3>.glb   (Altmodelle)
    project/assets/world/webseiten/fluss_teil.glb
    project/assets/ui/webseiten/station_<id>.png, station_<id>_ausstattung_<n>_<m>.png

Werkzeuge, Pruefung und Export kommen aus build_stationen_wg.py (dieselben
Helfer, dieselben Regeln). Alle Masse hier in GODOT-Koordinaten, Vorderseite
jeder Station +z, Flaeche 2,2 x 2,2 m um den Ursprung. Platz 1 links,
Platz 2 Mitte/hinten, Platz 3 rechts -- wo die Geometrie es verlangt, steht
die genaue Lage im Kommentar ueber der Station.

Stil: wie die WG (warm, hell, abgerundet), eigene Materialpalette fuer die
Werkstatt (Beton, Birke, Stahlblau), Akzent Orange #FF7A1A sparsam.
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
                                tasse, pflanze, zettel)

WELT = "webseiten"
AUSGABE = os.path.join(wg.PROJEKT, "project", "assets", "stations", WELT)
AUSGABE_UI = os.path.join(wg.PROJEKT, "project", "assets", "ui", WELT)
AUSGABE_FLUSS = os.path.join(wg.PROJEKT, "project", "assets", "world", WELT, "fluss_teil.glb")
VORSCHAU = os.path.join(wg.PROJEKT, "art_source", "vorschau", "webseiten_stationen")
BUDGET_GESAMT = 3000
wg.BUDGET_AUSSTATTUNG = 1100     # Richtwert je Stufe; verbindlich ist das Gesamtbudget

wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU

_exportieren_roh = wg.exportieren


def _exportieren_mit_wiederholung(obj, pfad):
    """Parallel laufende Importe sperren Dateien manchmal kurz (Errno 22).
    Dann warten und erneut schreiben, statt den ganzen Lauf abzubrechen."""
    import time
    for versuch in range(8):
        try:
            _exportieren_roh(obj, pfad)
            return
        except (RuntimeError, OSError) as fehler:
            print("  (Datei gesperrt, Versuch %d) %s" % (versuch + 1, os.path.basename(pfad)))
            time.sleep(1.5)
            letzter = fehler
    raise letzter


wg.exportieren = _exportieren_mit_wiederholung

# Werkstatt-Palette. Holz heller und kuehler als in der WG (Birke), Metall
# stahlblau, Textilien in Merch-Farben. Orange nur als Akzent.
wg.PALETTE.update({
    "birke":         ("#E3C08E", 0.0),
    "birke_dunkel":  ("#B98A55", 0.0),
    "stahl":         ("#5E7185", 0.0),
    "stahl_hell":    ("#A9B6C3", 0.0),
    "tinte":         ("#1B1726", 0.0),
    "akzent":        ("#FF7A1A", 0.0),
    "akzent_dunkel": ("#D9600B", 0.0),
    "shirt_weiss":   ("#F4F1EA", 0.0),
    "shirt_schwarz": ("#34303F", 0.0),
    "shirt_mint":    ("#7FD1B9", 0.0),
    "shirt_senf":    ("#F2B53A", 0.0),
    "shirt_rosa":    ("#F59AB0", 0.0),
    "shirt_blau":    ("#5B8FD9", 0.0),
    "puppe":         ("#EDE6DA", 0.0),
    "gummi":         ("#2B2D33", 0.0),
    "papier_grau":   ("#D9D4CB", 0.0),
    "seide":         ("#FBD9C4", 0.0),
    "kork_hell":     ("#D6A874", 0.0),
    "glas":          ("#BFE3F2", 0.0),
    "leucht_orange": ("#FF7A1A", 1.6),
    "leucht_flaeche":("#FFF4E0", 1.1),
    "ofen_glut":     ("#FF9A3D", 1.4),
    # Vorschau
    "v_boden":       ("#CFC8BD", 0.0),
})

# Stoff-Reihenfolge fuer Stapel und Stangen
MERCH = ("shirt_weiss", "shirt_schwarz", "akzent", "shirt_mint", "shirt_senf", "shirt_blau", "shirt_rosa")


def glatt(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0)):
    """Kasten ohne Rundung (12 Dreiecke) -- fuer kleine Teile."""
    return kasten(name, groesse, pos, mat, dreh, rund=(0.0, 0))


def rund1(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0), r=0.012):
    """Kasten mit einem Rundungssegment (44 Dreiecke)."""
    return kasten(name, groesse, pos, mat, dreh, rund=(min(r, min(groesse) * 0.3), 1))


# --- Wiederkehrende Gegenstaende der Welt ------------------------------------

def shirt_stapel(pos, anzahl, farben=MERCH, gier=0.0, b=0.30, t=0.24, d=0.045, start=0):
    """Gefaltete Shirts, pos = Mitte unten. Gibt Teile zurueck."""
    teile = []
    y = pos[1]
    versatz = (0.0, 5.0, -4.0, 3.0, -6.0, 2.0)
    for i in range(anzahl):
        g = gier + versatz[(i + start) % len(versatz)]
        mat = farben[(i + start) % len(farben)]
        if i == anzahl - 1:
            # nur das oberste Shirt gerundet -- darunter sieht man die Kante nicht
            teile.append(rund1("shirt", (b, d, t), (pos[0], y + d * 0.5, pos[2]), mat, (0, g, 0), r=0.014))
        else:
            teile.append(glatt("shirt", (b, d * 0.98, t), (pos[0], y + d * 0.5, pos[2]), mat, (0, g, 0)))
        y += d
    return teile


def stapel_hoehe(anzahl, d=0.045):
    return anzahl * d


def shirt_haengend(oben, gier, mat, lang=False, buegel=True):
    """Shirt am Buegel. oben = Haken an der Stange. Flaeche in der lokalen
    x/y-Ebene, gier dreht sie (90 = quer zu einer Stange entlang x)."""
    d = (0, gier, 0)
    teile = []
    if buegel:
        teile.append(stab("buegel", oben, punkt(oben, d, (0, -0.06, 0)), 0.006, "stahl_hell", seiten=4))
        teile.append(glatt("buegel_arm", (0.30, 0.012, 0.012), punkt(oben, d, (0, -0.065, 0)), "stahl_hell", d))
    hoehe = 0.46 if lang else 0.40
    koerper = punkt(oben, d, (0, -0.07 - hoehe * 0.5, 0))
    teile.append(rund1("stoff", (0.30, hoehe, 0.035), koerper, mat, d, r=0.012))
    for s in (-1, 1):
        if lang:
            arm = punkt(oben, d, (s * 0.18, -0.07 - hoehe * 0.42, 0))
            teile.append(glatt("aermel", (0.07, hoehe * 0.8, 0.03), arm, mat, verkette(d, (0, 0, s * 8))))
        else:
            arm = punkt(oben, d, (s * 0.18, -0.13, 0))
            teile.append(glatt("aermel", (0.11, 0.13, 0.03), arm, mat, verkette(d, (0, 0, s * 35))))
    if lang:
        teile.append(kugel("kapuze", 0.075, punkt(oben, d, (0, -0.10, -0.03)), mat, stufen=1, skala=(1.2, 0.9, 0.7), dreh=d))
        teile.append(glatt("tasche", (0.16, 0.06, 0.004), punkt(oben, d, (0, -0.07 - hoehe * 0.72, 0.019)), "tinte" if mat != "shirt_schwarz" else "stahl", d))
    return teile


def kleiderstange(pos, laenge, hoehe, gier=0.0, mat="stahl", rollen=False):
    """Stange entlang lokaler x-Achse, pos = Mitte unten."""
    d = (0, gier, 0)
    teile = []
    for s in (-1, 1):
        fuss = punkt(pos, d, (s * laenge * 0.5, 0, 0))
        teile.append(stab("staender", punkt(fuss, d, (0, 0.03, 0)), punkt(fuss, d, (0, hoehe, 0)), 0.014, mat))
        teile.append(glatt("kufe", (0.05, 0.03, 0.40), punkt(fuss, d, (0, 0.015 + (0.04 if rollen else 0), 0)), mat, d))
        if rollen:
            for u in (-1, 1):
                teile.append(zylinder("rolle", 0.028, 0.02, punkt(fuss, d, (0, 0.028, u * 0.17)), "gummi", seiten=8, dreh=verkette(d, (0, 0, 90)), rund=(0, 0)))
    teile.append(stab("stange", punkt(pos, d, (-laenge * 0.5 - 0.02, hoehe, 0)), punkt(pos, d, (laenge * 0.5 + 0.02, hoehe, 0)), 0.013, mat))
    return teile


def puppe(pos, gier, mat, hoodie=False, kappe=None):
    """Schaufensterpuppe (Torso) auf Stange. pos = Mitte unten."""
    d = (0, gier, 0)
    x, y, z = pos
    teile = [zylinder("puppe_fuss", 0.15, 0.03, (x, y + 0.015, z), "tinte", seiten=10, rund=(0, 0)),
             stab("puppe_stange", (x, y + 0.03, z), (x, y + 0.72, z), 0.016, "stahl_hell")]
    teile.append(kugel("torso", 0.19, (x, y + 1.00, z), mat, stufen=2, skala=(1.0, 1.65, 0.62), dreh=d))
    teile.append(kugel("schulter", 0.10, punkt((x, y + 1.22, z), d, (0, 0, 0)), mat, stufen=1, skala=(2.4, 0.75, 0.95), dreh=d))
    teile.append(zylinder("hals", 0.04, 0.08, (x, y + 1.34, z), "puppe", seiten=8, rund=(0, 0)))
    teile.append(kugel("kopf", 0.09, (x, y + 1.44, z), "puppe", stufen=2, skala=(0.9, 1.15, 0.95)))
    if hoodie:
        teile.append(kugel("kapuze", 0.10, punkt((x, y + 1.29, z), d, (0, 0, -0.07)), mat, stufen=1, skala=(1.3, 0.8, 0.8), dreh=d))
        teile.append(glatt("logo", (0.14, 0.09, 0.004), punkt((x, y + 1.06, z), d, (0, 0, 0.118)), "akzent" if mat != "akzent" else "tinte", d))
    else:
        teile.append(glatt("logo", (0.12, 0.12, 0.004), punkt((x, y + 1.08, z), d, (0, 0, 0.118)), "akzent" if mat != "akzent" else "shirt_weiss", d))
    if kappe:
        teile.append(kugel("kappe", 0.094, (x, y + 1.50, z), kappe, stufen=1, skala=(1.0, 0.55, 1.0)))
        teile.append(glatt("schirm", (0.12, 0.008, 0.09), punkt((x, y + 1.485, z), d, (0, 0, 0.09)), kappe, d))
    return teile


def paket(pos, groesse, gier=0.0, mat="karton", band="klebeband", logo=False, neig=0.0, billig=False):
    """Paket, pos = Mitte unten. band: Material des Klebestreifens oder None.
    billig: ohne Rundung (fuer Pakete in Gittern und Regalen)."""
    b, h, t = groesse
    d = (0, gier, neig)
    mitte = punkt(pos, d, (0, h * 0.5, 0))
    teile = [glatt("paket", groesse, mitte, mat, d) if billig else rund1("paket", groesse, mitte, mat, d, r=0.01)]
    if band:
        teile.append(glatt("band", (0.05, 0.004, t + 0.004), punkt(pos, d, (0, h + 0.001, 0)), band, d))
    if logo:
        teile.append(glatt("logo", (b * 0.35, h * 0.35, 0.004), punkt(pos, d, (0, h * 0.5, t * 0.5 + 0.002)), "akzent", d))
    return teile


wg.PALETTE["klebeband"] = ("#E8D2A6", 0.0)


def pfosten(pos, mat="stahl_hell", kopf="akzent"):
    """Absperrpfosten, pos = Mitte unten. Gibt (teile, kopfpunkt) zurueck."""
    x, y, z = pos
    teile = [zylinder("pfosten_fuss", 0.11, 0.03, (x, y + 0.015, z), "tinte", seiten=8, rund=(0, 0)),
             stab("pfosten", (x, y + 0.03, z), (x, y + 0.86, z), 0.02, mat, seiten=8),
             kugel("pfosten_kopf", 0.035, (x, y + 0.88, z), kopf, stufen=1)]
    return teile, (x, y + 0.82, z)


def rad(pos, radius, gier, breite=0.05, mat="gummi", felge="stahl_hell"):
    """Stehendes Rad, Achse quer zur Fahrtrichtung (lokal z)."""
    d = verkette((0, gier, 0), (90, 0, 0))
    teile = [zylinder("rad", radius, breite, pos, mat, seiten=8, dreh=d, rund=(0, 0))]
    if felge:
        teile.append(zylinder("felge", radius * 0.5, breite + 0.008, pos, felge, seiten=6, dreh=d, rund=(0, 0)))
    return teile


def speichenrad(pos, radius, gier):
    d = verkette((0, gier, 0), (90, 0, 0))
    teile = [ring("reifen", radius, 0.018, pos, "gummi", dreh=d, segmente=12, quer=4)]
    teile.append(zylinder("nabe", 0.025, 0.05, pos, "stahl_hell", seiten=6, dreh=d, rund=(0, 0)))
    return teile


def transporter(pos, gier, laenge=1.05, breite=0.50, hoehe=0.62, mat="shirt_weiss", streifen="akzent", dach_licht=False):
    """Kleiner, freundlicher Lieferwagen (bewusst gestaucht), Front = lokal +x.
    pos = Mitte unten."""
    d = (0, gier, 0)
    teile = []
    boden = 0.07
    r = 0.11
    # Kasten hinten, Fahrerhaus vorn etwas niedriger
    kl = laenge * 0.70
    teile.append(kasten("aufbau", (kl, hoehe - boden, breite), punkt(pos, d, (-laenge * 0.5 + kl * 0.5, boden + (hoehe - boden) * 0.5, 0)), mat, d, rund=(0.045, 1)))
    fl = laenge - kl
    fh = (hoehe - boden) * 0.78
    teile.append(kasten("kabine", (fl + 0.04, fh, breite * 0.98), punkt(pos, d, (laenge * 0.5 - fl * 0.5 - 0.02, boden + fh * 0.5, 0)), mat, d, rund=(0.045, 1)))
    # Scheiben
    teile.append(glatt("scheibe", (0.006, fh * 0.34, breite * 0.80), punkt(pos, d, (laenge * 0.5 + 0.003, boden + fh * 0.72, 0)), "glas", d))
    for s in (-1, 1):
        teile.append(glatt("fenster", (fl * 0.62, fh * 0.30, 0.006), punkt(pos, d, (laenge * 0.5 - fl * 0.5, boden + fh * 0.72, s * breite * 0.492)), "glas", d))
        teile.append(glatt("streifen", (kl * 0.92, 0.07, 0.006), punkt(pos, d, (-laenge * 0.5 + kl * 0.5, boden + (hoehe - boden) * 0.45, s * (breite * 0.5 + 0.002))), streifen, d))
        for u in (-1, 1):
            teile += rad(punkt(pos, d, (u * laenge * 0.32, r, s * breite * 0.42)), r, gier, breite=0.07, felge=None)
    teile.append(glatt("stossstange", (0.04, 0.05, breite * 0.9), punkt(pos, d, (laenge * 0.5 + 0.005, boden + 0.03, 0)), "tinte", d))
    for s in (-1, 1):
        teile.append(glatt("scheinwerfer", (0.008, 0.035, 0.07), punkt(pos, d, (laenge * 0.5 + 0.004, boden + 0.10, s * breite * 0.33)), "licht_warm", d))
    if dach_licht:
        teile.append(rund1("dachbox", (0.10, 0.04, breite * 0.5), punkt(pos, d, (laenge * 0.5 - fl * 0.5, boden + fh + 0.02, 0)), "leucht_orange", d, r=0.01))
    return teile


def shirt_zeichen(pos, dreh, s, mat, z):
    """T-Shirt-Umriss als flaches Zeichen auf einer Flaeche (lokal x/y)."""
    return [kasten("zeichen", (0.50 * s, 0.62 * s, 0.003), punkt(pos, dreh, (0, -0.10 * s, z)), mat, dreh, rund=(0, 0)),
            kasten("zeichen", (0.92 * s, 0.20 * s, 0.003), punkt(pos, dreh, (0, 0.16 * s, z)), mat, dreh, rund=(0, 0))]


def geneigte_tafel(pos_fuss, breite, hoehe, neig, mat_rahmen, dicke=0.02):
    """Tafel/Display, Unterkante bei pos_fuss, um `neig` Grad nach hinten
    gekippt. Gibt (teile, mitte, dreh) zurueck."""
    d = (-neig, 0, 0)
    x, y, z = pos_fuss
    mitte = (x, y + 0.03 + hoehe * 0.5 * math.cos(math.radians(neig)),
             z - hoehe * 0.5 * math.sin(math.radians(neig)))
    teile = [rund1("tafel", (breite, hoehe, dicke), mitte, mat_rahmen, d, r=0.008)]
    return teile, mitte, d


# =============================================================================
# Station 1: station_intake -- Design (Zeichentisch)
# Tisch x -0,35..0,95, z -0,72..-0,12, Hoehe 0,76; links Bock, rechts
# Planschrank. Hocker vorn bei (0,30 | 0,35).
# Platz 1: Tischplatte links/Mitte (x -0,30..0,42).
# Platz 2: Tischplatte rechts (x 0,50..0,92) und hinterer Streifen rechts
#          (x 0,10..1,06, z -1,06..-0,78).
# Platz 3: hinterer Streifen links (x -1,06..-0,05) und Boden vorn links.
# =============================================================================

D_TISCH_X = (-0.35, 0.95)
D_TISCH_Z = (-0.72, -0.12)
D_H = 0.76
D_AUF = D_H + 0.002
D_HOCKER = (0.30, 0.35)
D_HOCKER_H = 0.64


def intake_basis():
    t = []
    x0, x1 = D_TISCH_X
    z0, z1 = D_TISCH_Z
    tx, tz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    t.append(kasten("platte", (x1 - x0, 0.04, z1 - z0), (tx, D_H - 0.02, tz), "birke"))
    t.append(glatt("kante", (x1 - x0 - 0.04, 0.012, 0.012), (tx, D_H - 0.02, z1 + 0.004), "akzent"))
    # Bock links
    bx = x0 + 0.12
    for s in (-1, 1):
        t.append(stab("bock", (bx, D_H - 0.04, tz), (bx, 0.012, tz + s * 0.24), 0.02, "birke_dunkel"))
    t.append(stab("bock_quer", (bx, 0.30, tz - 0.14), (bx, 0.30, tz + 0.14), 0.014, "birke_dunkel"))
    # Planschrank rechts mit drei flachen Schubladen
    sx = x1 - 0.27
    t.append(kasten("schrank", (0.48, D_H - 0.04, 0.52), (sx, (D_H - 0.04) * 0.5, tz), "birke_dunkel"))
    for k in range(3):
        y = 0.14 + k * 0.20
        t.append(glatt("lade", (0.42, 0.16, 0.006), (sx, y, tz + 0.263), "birke"))
        t.append(glatt("griff", (0.12, 0.018, 0.018), (sx, y + 0.03, tz + 0.272), "tinte"))
    # Zeichenhocker
    hx, hz = D_HOCKER
    t.append(zylinder("sitz", 0.16, 0.05, (hx, D_HOCKER_H - 0.025, hz), "tinte", seiten=12, rund=(0.012, 1)))
    for i in range(4):
        w = math.radians(45 + 90 * i)
        t.append(stab("bein", (hx + math.cos(w) * 0.09, D_HOCKER_H - 0.05, hz + math.sin(w) * 0.09),
                      (hx + math.cos(w) * 0.17, 0.008, hz + math.sin(w) * 0.17), 0.015, "stahl"))
    t.append(ring("fussring", 0.13, 0.011, (hx, 0.22, hz), "stahl", segmente=10, quer=3))
    return t


def intake_a1_0():
    """Offenes Skizzenbuch mit Bleistift und Radiergummi."""
    x, y, z = 0.05, D_AUF, -0.40
    d = (0, -10, 0)
    t = []
    for s in (-1, 1):
        t.append(glatt("seite", (0.20, 0.012, 0.27), punkt((x, y + 0.010, z), d, (s * 0.102, 0, 0)), "papier", verkette(d, (0, 0, -s * 3))))
    t.append(glatt("umschlag", (0.43, 0.006, 0.29), (x, y + 0.003, z), "tinte", d))
    for k in range(3):
        t.append(glatt("strich", (0.12, 0.002, 0.012), punkt((x, y + 0.019, z), d, (-0.10, 0, -0.07 + k * 0.05)), "grau_mittel", d))
    t += shirt_zeichen(punkt((x, y + 0.019, z), d, (0.10, 0, 0)), verkette(d, (-90, 0, 0)), 0.14, "akzent", 0.0)
    t.append(stab("bleistift", (x + 0.27, y + 0.01, z - 0.05), (x + 0.29, y + 0.01, z + 0.12), 0.008, "shirt_senf", seiten=6))
    t.append(glatt("radierer", (0.05, 0.02, 0.03), (x - 0.26, y + 0.01, z + 0.08), "shirt_rosa", (0, 20, 0)))
    return t


def _grafiktablett(x, y, z, gier=-6):
    d = (0, gier, 0)
    t = [rund1("tablett", (0.38, 0.014, 0.25), (x, y + 0.007, z), "tinte", d, r=0.006)]
    t.append(glatt("feld", (0.28, 0.002, 0.18), punkt((x, y + 0.015, z), d, (0.03, 0, 0)), "stahl", d))
    for k in range(3):
        t.append(glatt("taste", (0.03, 0.004, 0.03), punkt((x, y + 0.015, z), d, (-0.155, 0, -0.07 + k * 0.07)), "akzent" if k == 0 else "grau_mittel", d))
    t.append(stab("stift", punkt((x, y + 0.02, z), d, (0.05, 0, 0.02)), punkt((x, y + 0.03, z), d, (0.14, 0, -0.08)), 0.008, "grau_dunkel", seiten=6))
    return t


def intake_a1_1():
    """Grafiktablett mit Stift, dahinter ein Laptop mit Entwurf."""
    t = _grafiktablett(0.05, D_AUF, -0.25)
    t += laptop((0.02, D_AUF, -0.56), (0, 4, 0), breite=0.34, tiefe=0.22, inhalt="balken")
    return t


def _stiftdisplay(x, y, z, breite, hoehe, neig, gross):
    t = []
    teile, mitte, d = geneigte_tafel((x, y, z), breite, hoehe, neig, "tinte", dicke=0.024)
    t += teile
    t.append(glatt("stuetze", (breite * 0.5, 0.012, 0.18), (x, y + 0.006, z - 0.03), "stahl"))
    t.append(stab("stuetze_arm", (x, y + 0.012, z - 0.11), punkt(mitte, d, (0, -hoehe * 0.1, -0.013)), 0.012 if gross else 0.009, "stahl"))
    rand = 0.022
    t += schirm_inhalt(mitte, d, breite - rand * 2, hoehe - rand * 2, "video" if gross else "balken", tiefe=0.0125)
    t.append(kasten("motivflaeche", (hoehe * 0.55, hoehe * 0.55, 0.003), punkt(mitte, d, (-breite * 0.12, 0.0, 0.0175)), "shirt_weiss", d, rund=(0, 0)))
    t += shirt_zeichen(punkt(mitte, d, (-breite * 0.12, 0.0, 0)), d, hoehe * 0.40, "akzent", 0.0205)
    t.append(stab("stift", (x + breite * 0.5 + 0.05, y + 0.012, z + 0.05), (x + breite * 0.5 + 0.09, y + 0.012, z - 0.10), 0.009, "grau_dunkel", seiten=6))
    return t


def intake_a1_2():
    """Stift-Display auf Klappstuetze, Entwurf auf dem Schirm."""
    return _stiftdisplay(0.02, D_AUF, -0.30, 0.44, 0.28, 30, False)


def intake_a1_3():
    """Grosses Stift-Display auf Stuetze, Tastenfeld, Gelenkleuchte."""
    x, y, z = 0.04, D_AUF, -0.24
    t = _stiftdisplay(x, y, z, 0.62, 0.40, 28, True)
    t.append(rund1("tastenfeld", (0.10, 0.018, 0.16), (x - 0.27, y + 0.009, z + 0.02), "tinte", (0, 8, 0), r=0.006))
    for k in range(2):
        t.append(glatt("knopf", (0.035, 0.006, 0.035), punkt((x - 0.27, y + 0.02, z + 0.02), (0, 8, 0), (0, 0, -0.035 + k * 0.07)), "akzent", (0, 8, 0)))
    lx, lz = -0.24, -0.64
    t.append(zylinder("leuchte_fuss", 0.06, 0.02, (lx, y + 0.01, lz), "tinte", seiten=10, rund=(0.006, 1)))
    k1 = (lx, y + 0.02, lz)
    k2 = (lx + 0.03, y + 0.36, lz - 0.02)
    k3 = (lx + 0.18, y + 0.48, lz + 0.05)
    t.append(stab("leuchte_arm", k1, k2, 0.009, "akzent"))
    t.append(stab("leuchte_arm", k2, k3, 0.009, "akzent"))
    t.append(zylinder("leuchte_kopf", 0.045, 0.09, (k3[0] + 0.03, k3[1] - 0.03, k3[2]), "tinte", seiten=10, dreh=(0, 0, 40), radius_oben=0.018))
    t.append(kugel("leuchte_licht", 0.028, (k3[0] + 0.06, k3[1] - 0.07, k3[2]), "licht_warm", stufen=1))
    return t


# Platz 2: Muster
def _stoffproben(x, y, z):
    t = []
    for k, mat in enumerate(("shirt_mint", "akzent", "shirt_senf", "shirt_blau", "shirt_weiss")):
        t.append(glatt("probe", (0.13, 0.008, 0.13), (x + k * 0.012, y + 0.004 + k * 0.008, z - k * 0.01), mat, (0, -20 + k * 11, 0)))
    return t


def intake_a2_1():
    """Stoffproben gefaechert und eine liegende Stoffrolle."""
    t = _stoffproben(0.64, D_AUF, -0.36)
    t.append(zylinder("stoffrolle", 0.035, 0.34, (0.74, D_AUF + 0.035, -0.60), "shirt_mint", seiten=10, dreh=(0, 0, 90)))
    t.append(zylinder("rollenkern", 0.012, 0.36, (0.74, D_AUF + 0.035, -0.60), "karton", seiten=6, dreh=(0, 0, 90), rund=(0, 0)))
    return t


def intake_a2_2():
    """Musterwand mit Stoffquadraten, Proben bleiben auf dem Tisch."""
    t = _stoffproben(0.64, D_AUF, -0.36)
    cx, z, breite, unten, hoehe = 0.58, -0.92, 0.86, 0.80, 0.80
    t.append(rund1("musterwand", (breite, hoehe, 0.03), (cx, unten + hoehe * 0.5, z), "birke_dunkel", r=0.01))
    t.append(glatt("lochblech", (breite - 0.06, hoehe - 0.06, 0.004), (cx, unten + hoehe * 0.5, z + 0.017), "stahl_hell"))
    for s in (-1, 1):
        bx = cx + s * (breite * 0.5 - 0.05)
        t.append(stab("wandbein", (bx, 0.03, z - 0.035), (bx, unten + 0.05, z - 0.035), 0.016, "stahl"))
        t.append(glatt("wandfuss", (0.05, 0.03, 0.24), (bx, 0.015, z - 0.02), "stahl"))
    zf = z + 0.02
    farben = ("shirt_mint", "akzent", "shirt_senf", "shirt_blau", "shirt_rosa", "shirt_schwarz", "shirt_weiss", "shirt_senf")
    for r in range(3):
        for s in range(4):
            mat = farben[(r * 4 + s * 3) % len(farben)]
            t.append(glatt("stoff", (0.15, 0.17, 0.006), (cx - 0.27 + s * 0.18, 1.43 - r * 0.22, zf + 0.004), mat, (0, 0, ((r + s) % 3 - 1) * 4)))
    return t


def intake_a2_3():
    """Farbfaecher-Regal: offenes Regal mit Stoffrollen, Faechern und Kisten."""
    t = _stoffproben(0.64, D_AUF, -0.36)
    cx, z = 0.60, -0.93
    b, tf, h = 0.90, 0.24, 1.72
    for s in (-1, 1):
        t.append(rund1("regalwange", (0.04, h, tf), (cx + s * (b * 0.5 - 0.02), h * 0.5, z), "birke_dunkel"))
    for y in (0.06, 0.52, 0.98, 1.40, h - 0.02):
        t.append(glatt("regalboden", (b - 0.08, 0.03, tf - 0.01), (cx, y, z), "birke"))
    for k, mat in enumerate(("shirt_mint", "akzent", "shirt_blau", "shirt_senf", "shirt_rosa", "shirt_schwarz")):
        hk = 0.40 - (k % 2) * 0.06
        t.append(zylinder("rolle", 0.045, hk, (cx - 0.33 + k * 0.132, 0.076 + hk * 0.5, z), mat, seiten=8, rund=(0, 0)))
    for f in range(3):
        fx = cx - 0.25 + f * 0.25
        for k, mat in enumerate(("shirt_rosa", "akzent", "shirt_senf", "shirt_mint", "shirt_blau")):
            w = -40 + k * 20
            off = (-math.sin(math.radians(w)) * 0.12, 0.12 * math.cos(math.radians(w)), 0.0)
            t.append(glatt("faecher", (0.045, 0.26, 0.004), (fx + off[0], 0.545 + off[1], z + 0.02 + 0.005 * k), mat, (0, 0, w)))
    t.append(rund1("kiste", (0.34, 0.20, 0.20), (cx - 0.20, 1.096, z), "akzent", r=0.012))
    t.append(glatt("kistengriff", (0.12, 0.03, 0.004), (cx - 0.20, 1.14, z + 0.102), "tinte"))
    t += shirt_stapel((cx + 0.20, 0.996, z), 3, ("shirt_weiss", "shirt_blau", "shirt_senf"), b=0.28, t=0.20)
    t += pflanze((cx + 0.22, 1.416, z), 0.8, topf_mat="shirt_weiss", blaetter=4)
    t += shirt_stapel((cx - 0.20, 1.416, z), 2, ("shirt_schwarz", "akzent"), b=0.28, t=0.20)
    return t


# Platz 3: Moodboard (hinten links)
M_X = -0.58
M_Z = -0.92


def intake_a3_0():
    """Ein Poster, an einen Holzklotz gelehnt, daneben die Versandrolle."""
    t = []
    d = (-12, 0, 0)
    mitte = (M_X, 0.02 + 0.32 * math.cos(math.radians(12)), M_Z + 0.12 - 0.32 * math.sin(math.radians(12)))
    t.append(kasten("poster", (0.46, 0.64, 0.012), mitte, "shirt_weiss", d, rund=(0, 0)))
    t.append(kasten("posterbild", (0.38, 0.44, 0.003), punkt(mitte, d, (0, 0.05, 0.0075)), "shirt_blau", d, rund=(0, 0)))
    t += shirt_zeichen(punkt(mitte, d, (0, 0.05, 0)), d, 0.26, "akzent", 0.0105)
    t.append(glatt("klotz", (0.44, 0.06, 0.08), (M_X, 0.03, M_Z - 0.02), "birke_dunkel"))
    t.append(zylinder("rolle", 0.04, 0.45, (M_X - 0.22, 0.04, M_Z + 0.36), "karton", seiten=8, dreh=(90, 60, 0)))
    return t


def _tafel(breite, hoehe, unten, rahmen="birke_dunkel", flaeche="kork_hell"):
    my = unten + hoehe * 0.5
    t = [rund1("rahmen", (breite, hoehe, 0.03), (M_X, my, M_Z), rahmen, r=0.01)]
    t.append(glatt("flaeche", (breite - 0.06, hoehe - 0.06, 0.004), (M_X, my, M_Z + 0.017), flaeche))
    for s in (-1, 1):
        bx = M_X + s * (breite * 0.5 - 0.06)
        t.append(stab("tafelbein", (bx, 0.03, M_Z - 0.035), (bx, unten + hoehe - 0.03, M_Z - 0.035), 0.016, "birke_dunkel"))
        t.append(glatt("tafelfuss", (0.05, 0.03, 0.24), (bx, 0.015, M_Z - 0.02), "birke_dunkel"))
    return t, M_Z + 0.022


def intake_a3_1():
    """Pinnwand mit vier Zetteln und einem Foto."""
    t, zf = _tafel(0.70, 0.55, 0.80)
    for dx, dy, mat, rz in ((-0.20, 0.12, "papier", 4), (0.02, 0.14, "shirt_senf", -5), (0.20, 0.08, "papier", 3), (-0.12, -0.12, "shirt_mint", -3)):
        t.append(zettel((M_X + dx, 1.075 + dy, zf), (0, 0, rz), (0.14, 0.14), mat))
    t.append(zettel((M_X + 0.14, 0.96, zf), (0, 0, -6), (0.16, 0.12), "shirt_blau"))
    t.append(kugel("nadel", 0.014, (M_X + 0.02, 1.26, zf + 0.008), "akzent", stufen=1))
    return t


def intake_a3_2():
    """Grosse Moodboard-Wand: Fotos, Stoffe, Faeden."""
    t, zf = _tafel(0.90, 0.90, 0.55, flaeche="papier_grau")
    fotos = ((-0.28, 0.25, 0.22, 0.16, "shirt_blau"), (-0.02, 0.28, 0.18, 0.22, "shirt_rosa"), (0.26, 0.24, 0.20, 0.16, "shirt_senf"),
             (-0.26, -0.02, 0.18, 0.18, "shirt_mint"), (0.04, -0.04, 0.24, 0.18, "shirt_schwarz"), (0.28, -0.06, 0.16, 0.22, "akzent"),
             (-0.20, -0.28, 0.24, 0.14, "shirt_weiss"), (0.14, -0.28, 0.20, 0.14, "shirt_blau"))
    for i, (dx, dy, b, h, mat) in enumerate(fotos):
        t.append(zettel((M_X + dx, 1.0 + dy, zf), (0, 0, ((i * 7) % 9) - 4), (b, h), mat))
    t += shirt_zeichen((M_X + 0.04, 0.96, zf), (0, 0, 0), 0.14, "akzent", 0.004)
    t.append(stab("faden", (M_X - 0.28, 1.25, zf + 0.008), (M_X + 0.04, 0.99, zf + 0.008), 0.004, "akzent", seiten=4))
    t.append(stab("faden", (M_X + 0.04, 0.99, zf + 0.008), (M_X + 0.26, 1.24, zf + 0.008), 0.004, "akzent", seiten=4))
    return t


def intake_a3_3():
    """Leuchtkasten mit Motiven, orange eingefasst, und eine grosse Pflanze."""
    breite, hoehe, unten = 0.92, 0.96, 0.52
    my = unten + hoehe * 0.5
    t = [kasten("kasten", (breite, hoehe, 0.08), (M_X, my, M_Z + 0.02), "tinte", rund=(0.02, 2))]
    zf = M_Z + 0.062
    t.append(glatt("leuchtflaeche", (breite - 0.08, hoehe - 0.08, 0.004), (M_X, my, zf), "leucht_flaeche"))
    for s in (-1, 1):
        t.append(glatt("rand", (0.014, hoehe - 0.06, 0.006), (M_X + s * (breite * 0.5 - 0.025), my, zf + 0.002), "leucht_orange"))
        t.append(glatt("rand", (breite - 0.06, 0.014, 0.006), (M_X, my + s * (hoehe * 0.5 - 0.025), zf + 0.002), "leucht_orange"))
        bx = M_X + s * (breite * 0.5 - 0.10)
        t.append(stab("standbein", (bx, 0.03, M_Z - 0.035), (bx, unten + 0.05, M_Z - 0.035), 0.018, "tinte"))
        t.append(glatt("standfuss", (0.06, 0.03, 0.24), (bx, 0.015, M_Z - 0.02), "tinte"))
    zf += 0.004
    for i, (dx, dy, b, h, mat) in enumerate(((-0.25, 0.22, 0.26, 0.30, "shirt_blau"), (0.05, 0.25, 0.22, 0.24, "shirt_rosa"),
                                               (0.28, 0.20, 0.18, 0.30, "shirt_mint"), (-0.22, -0.18, 0.28, 0.24, "shirt_senf"),
                                               (0.20, -0.20, 0.30, 0.26, "shirt_schwarz"))):
        t.append(zettel((M_X + dx, my + dy, zf), (0, 0, ((i * 5) % 7) - 3), (b, h), mat))
    t += shirt_zeichen((M_X + 0.20, my - 0.20, zf), (0, 0, ((4 * 5) % 7) - 3), 0.16, "akzent", 0.004)
    t.append(zettel((M_X - 0.02, my - 0.02, zf + 0.005), (0, 0, 8), (0.20, 0.20), "akzent"))
    t += shirt_zeichen((M_X - 0.02, my - 0.02, zf + 0.005), (0, 0, 8), 0.12, "shirt_weiss", 0.004)
    px, pz = -0.82, 0.30
    t.append(zylinder("kuebel", 0.14, 0.30, (px, 0.15, pz), "shirt_weiss", seiten=10, radius_oben=0.16))
    for i in range(6):
        w = 2 * math.pi * i / 6
        t.append(kugel("blatt", 0.13, (px + math.cos(w) * 0.10, 0.50 + 0.08 * (i % 2), pz + math.sin(w) * 0.10), "pflanze" if i % 2 else "pflanze_dunkel", stufen=1, skala=(1.0, 0.8, 1.0)))
    t.append(kugel("blatt", 0.14, (px, 0.70, pz), "pflanze", stufen=1))
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
    "figur": None,
}


# =============================================================================
# Station 2: station_buffer -- Druck (Werkbank)
# Werkbank x -0,55..0,95, z -0,80..-0,15, Hoehe 0,86, Lochwand hinten.
# Platz 1: Bank rechts (x 0,12..0,93) und ab m3 Karussellpresse vorn rechts
#          (Mitte 0,62 | 0,55).
# Platz 2: Bank links (x -0,52..0,05) und Boden links (x -1,08..-0,60,
#          z -1,05..-0,05).
# Platz 3: Boden vorn links (x -1,08..0,12, z 0,05..1,08).
# =============================================================================

W_X = (-0.55, 0.95)
W_Z = (-0.80, -0.15)
W_H = 0.86
W_AUF = W_H + 0.002


def buffer_basis():
    t = []
    x0, x1 = W_X
    z0, z1 = W_Z
    tx, tz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    t.append(kasten("platte", (x1 - x0, 0.05, z1 - z0), (tx, W_H - 0.025, tz), "birke"))
    for sx in (x0 + 0.05, x1 - 0.05):
        for sz in (z0 + 0.05, z1 - 0.05):
            t.append(rund1("bein", (0.05, W_H - 0.05, 0.05), (sx, (W_H - 0.05) * 0.5, sz), "stahl"))
    t.append(kasten("ablage", (x1 - x0 - 0.06, 0.03, z1 - z0 - 0.06), (tx, 0.18, tz), "birke_dunkel", rund=(0.01, 1)))
    t.append(glatt("zarge", (x1 - x0 - 0.1, 0.07, 0.02), (tx, W_H - 0.085, z1 - 0.04), "stahl"))
    # Lochwand hinten auf der Bank
    lw_z = z0 + 0.02
    t.append(rund1("lochwand", (x1 - x0, 0.52, 0.03), (tx, W_H + 0.26, lw_z), "stahl_hell", r=0.01))
    for sx in (x0 + 0.04, x1 - 0.04):
        t.append(glatt("pfosten", (0.03, 0.54, 0.035), (sx, W_H + 0.27, lw_z - 0.001), "stahl"))
    # Werkzeug an der Lochwand: Rakel, Schere, Klebeband
    zf = lw_z + 0.02
    t.append(glatt("rakel", (0.30, 0.05, 0.02), (x0 + 0.30, W_H + 0.40, zf), "akzent"))
    t.append(glatt("rakel_gummi", (0.30, 0.015, 0.02), (x0 + 0.30, W_H + 0.37, zf), "tinte"))
    for s in (-1, 1):
        t.append(glatt("schere", (0.02, 0.14, 0.01), (x0 + 0.62 + s * 0.02, W_H + 0.38, zf), "grau_dunkel", (0, 0, s * 12)))
    t.append(ring("klebeband", 0.045, 0.016, (x0 + 0.80, W_H + 0.40, zf + 0.012), "klebeband", dreh=(90, 0, 0), segmente=8, quer=4))
    t.append(glatt("haken", (0.14, 0.012, 0.03), (x1 - 0.30, W_H + 0.44, zf), "grau_dunkel"))
    t.append(ring("kabelrolle", 0.06, 0.012, (x1 - 0.30, W_H + 0.36, zf + 0.01), "akzent_dunkel", dreh=(90, 0, 0), segmente=8, quer=3))
    return t


def _bedrucktes_shirt(x, y, z, gier, mat="shirt_weiss", druck="akzent"):
    d = (0, gier, 0)
    t = [glatt("shirt_flach", (0.26, 0.008, 0.30), (x, y + 0.004, z), mat, d)]
    t.append(glatt("aermel_flach", (0.40, 0.008, 0.09), punkt((x, y + 0.004, z), d, (0, 0, -0.11)), mat, d))
    t.append(glatt("druck", (0.12, 0.004, 0.12), punkt((x, y + 0.009, z), d, (0, 0, 0.01)), druck, d))
    return t


def buffer_a1_0():
    """Buegeleisen auf Hitzematte, daneben ein frisch bedrucktes Shirt."""
    x, y, z = 0.50, W_AUF, -0.48
    t = [glatt("matte", (0.62, 0.006, 0.44), (x, y + 0.003, z), "akzent_dunkel")]
    t += _bedrucktes_shirt(x - 0.10, y + 0.006, z + 0.02, 0)
    ex, ez = x + 0.20, z - 0.04
    t.append(kasten("eisen_sohle", (0.13, 0.02, 0.24), (ex, y + 0.017, ez), "stahl_hell", (0, 25, 0), rund=(0.006, 1)))
    t.append(kugel("eisen", 0.09, (ex, y + 0.055, ez), "shirt_blau", stufen=2, skala=(0.75, 0.45, 1.3), dreh=(0, 25, 0)))
    t.append(stab("eisen_griff", punkt((ex, y + 0.12, ez), (0, 25, 0), (0, 0, -0.07)), punkt((ex, y + 0.12, ez), (0, 25, 0), (0, 0, 0.06)), 0.014, "tinte"))
    t.append(stab("eisen_kabel", punkt((ex, y + 0.08, ez), (0, 25, 0), (0, 0, -0.12)), (ex + 0.05, y + 0.008, ez - 0.17), 0.006, "tinte", seiten=4))
    return t


def _presse(x, y, z, gross=False):
    t = []
    t.append(rund1("presse_fuss", (0.36, 0.06, 0.44), (x, y + 0.03, z), "grau_dunkel"))
    t.append(glatt("presse_platte", (0.30, 0.03, 0.34), (x, y + 0.075, z + 0.02), "stahl_hell"))
    t += _bedrucktes_shirt(x, y + 0.09, z + 0.03, 0)
    t.append(rund1("presse_saeule", (0.09, 0.34, 0.09), (x, y + 0.23, z - 0.19), "tinte" if gross else "grau_dunkel"))
    angel = (x, y + 0.40, z - 0.16)
    d = (-32, 0, 0)
    oben = punkt(angel, d, (0, 0, 0.20))
    t.append(kasten("presse_heizplatte", (0.32, 0.06, 0.38), oben, "akzent" if gross else "stahl", d, rund=(0.012, 1)))
    t.append(glatt("presse_heizflaeche", (0.28, 0.006, 0.34), punkt(angel, d, (0, -0.032, 0.20)), "ofen_glut" if gross else "stahl_hell", d))
    griff0 = punkt(angel, d, (0, 0.03, 0.38))
    griff1 = punkt(angel, d, (0, 0.03, 0.52))
    t.append(stab("presse_griff", griff0, griff1, 0.012, "grau_dunkel"))
    t.append(zylinder("presse_knauf", 0.024, 0.18, griff1, "tinte", seiten=8, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(glatt("presse_anzeige", (0.06, 0.04, 0.004), (x, y + 0.30, z - 0.143), "schirm_orange"))
    return t


def buffer_a1_1():
    """Transferpresse, geoeffnet, ein Shirt auf der Platte."""
    return _presse(0.50, W_AUF, -0.46)


def _dtf(x, y, z, gross):
    t = []
    b, h, d = (0.74, 0.28, 0.42)
    t.append(kasten("drucker", (b, h, d), (x, y + 0.03 + h * 0.5, z), "shirt_weiss" if not gross else "tinte", rund=(0.02, 2)))
    for sx in (-1, 1):
        t.append(glatt("drucker_fuss", (0.06, 0.03, 0.30), (x + sx * (b * 0.5 - 0.06), y + 0.015, z), "grau_dunkel"))
    t.append(glatt("deckel", (b - 0.16, 0.012, d - 0.12), (x - 0.04, y + 0.03 + h + 0.006, z - 0.02), "stahl_hell" if not gross else "stahl"))
    t.append(glatt("deckel_fenster", (b - 0.30, 0.004, 0.10), (x - 0.04, y + 0.03 + h + 0.014, z + 0.04), "glas"))
    zf = z + d * 0.5
    t.append(glatt("schlitz", (b - 0.20, 0.03, 0.006), (x - 0.04, y + 0.03 + h * 0.62, zf + 0.002), "tinte" if not gross else "grau_mittel"))
    # Folie laeuft vorn heraus und haengt ueber die Kante
    t.append(glatt("folie", (b - 0.26, 0.004, 0.20), (x - 0.04, y + 0.03 + h * 0.58 - 0.04, zf + 0.08), "papier", (35, 0, 0)))
    t.append(glatt("folie_druck", (0.12, 0.004, 0.10), (x - 0.04, y + 0.03 + h * 0.58 - 0.035, zf + 0.085), "akzent", (35, 0, 0)))
    # Tinte und Bedienfeld rechts
    for k, mat in enumerate(("hellblau", "rosa", "gelb", "schwarz", "papier")):
        t.append(glatt("tinte_patrone", (0.022, 0.05, 0.006), (x + b * 0.5 - 0.17 + k * 0.03, y + 0.03 + h * 0.30, zf + 0.002), mat))
    t.append(glatt("bedienfeld", (0.09, 0.06, 0.006), (x + b * 0.5 - 0.08, y + 0.03 + h * 0.70, zf + 0.002), "schirm_blau"))
    t.append(glatt("streifen", (b - 0.04, 0.02, 0.006), (x, y + 0.03 + h * 0.12, zf + 0.002), "akzent"))
    if gross:
        t.append(zylinder("folienrolle", 0.05, b - 0.10, (x - 0.02, y + 0.03 + h + 0.07, z - d * 0.5 + 0.04), "papier", seiten=10, dreh=(0, 0, 90)))
        for sx in (-1, 1):
            t.append(glatt("rollenhalter", (0.02, 0.09, 0.05), (x - 0.02 + sx * (b * 0.5 - 0.03), y + 0.03 + h + 0.04, z - d * 0.5 + 0.04), "stahl"))
        t.append(kugel("status", 0.018, (x + b * 0.5 - 0.05, y + 0.03 + h + 0.012, z + 0.12), "leucht_orange", stufen=1))
    return t


def buffer_a1_2():
    """DTF-Drucker mit auslaufender Folie."""
    return _dtf(0.52, W_AUF, -0.47, False)


def buffer_a1_3():
    """Druckstrasse: grosser Drucker auf der Bank und eine Karussellpresse."""
    t = _dtf(0.52, W_AUF, -0.47, True)
    cx, cz = 0.62, 0.55
    # Fuss als Kreuz, Saeule, vier Arme mit Paletten, zwei Druckkoepfe
    for w in (45, 135):
        t.append(rund1("karussell_fuss", (0.62, 0.05, 0.08), (cx, 0.025, cz), "tinte", (0, w, 0)))
    t.append(zylinder("karussell_saeule", 0.045, 0.90, (cx, 0.47, cz), "stahl", seiten=8, rund=(0, 0)))
    t.append(zylinder("karussell_nabe", 0.09, 0.08, (cx, 0.78, cz), "akzent", seiten=10, rund=(0, 0)))
    for k in range(4):
        w = math.radians(45 + 90 * k)
        ax, az = cx + math.cos(w) * 0.25, cz + math.sin(w) * 0.25
        t.append(stab("arm", (cx, 0.78, cz), (ax, 0.78, az), 0.014, "stahl", seiten=4))
        gier = -math.degrees(w) + 90
        t.append(glatt("palette", (0.20, 0.025, 0.24), (ax, 0.80, az), "grau_dunkel", (0, gier, 0)))
        mat = ("shirt_weiss", "shirt_schwarz", "shirt_mint", "akzent")[k]
        t.append(glatt("palette_shirt", (0.17, 0.008, 0.20), (ax, 0.817, az), mat, (0, gier, 0)))
    for k, w_grad in enumerate((45, 135)):
        w = math.radians(w_grad)
        ax, az = cx + math.cos(w) * 0.25, cz + math.sin(w) * 0.25
        gier = -w_grad + 90
        t.append(stab("kopfarm", (cx, 0.96, cz), (ax, 0.96, az), 0.014, "stahl", seiten=4))
        t.append(glatt("sieb", (0.22, 0.02, 0.26), (ax, 0.90, az), "akzent" if k == 0 else "shirt_blau", (0, gier, 0)))
        t.append(glatt("sieb_gaze", (0.16, 0.004, 0.18), (ax, 0.912, az), "papier", (0, gier, 0)))
    t.append(kugel("karussell_kappe", 0.05, (cx, 0.98, cz), "akzent", stufen=1))
    return t


# Platz 2: Rohware
def buffer_a2_0():
    """Ein kleiner Stapel Rohlinge auf der Bank."""
    return shirt_stapel((-0.28, W_AUF, -0.45), 3, ("shirt_weiss", "shirt_weiss", "shirt_schwarz"), gier=8)


def _regal_klein(x, z, b, tf, h, boeden, mat="birke"):
    t = []
    for s in (-1, 1):
        t.append(rund1("wange", (0.03, h, tf), (x + s * (b * 0.5 - 0.015), h * 0.5, z), "birke_dunkel"))
    for y in boeden:
        t.append(glatt("boden", (b - 0.04, 0.025, tf - 0.01), (x, y, z), mat))
    return t


def buffer_a2_1():
    """Kleines Regal voller Rohlinge, dazu der Stapel auf der Bank."""
    t = buffer_a2_0()
    x, z = -0.84, -0.72
    boeden = (0.05, 0.42, 0.79, 1.12)
    t += _regal_klein(x, z, 0.44, 0.38, 1.14, boeden)
    for k, y in enumerate(boeden[:3]):
        farben = (("shirt_weiss",) * 3, ("shirt_schwarz",) * 3, ("shirt_weiss", "shirt_mint", "shirt_weiss"))[k]
        t += shirt_stapel((x, y + 0.013, z), 3 if k != 1 else 4, farben, gier=90, b=0.28, t=0.22)
    return t


def _rollwagen(x, z, gier):
    d = (0, gier, 0)
    t = []
    b, tf = 0.44, 0.78
    for y in (0.10, 0.48, 0.86):
        t.append(rund1("wagenboden", (b, 0.03, tf), punkt((x, 0, z), d, (0, y, 0)), "stahl", d, r=0.01))
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = punkt((x, 0, z), d, (sx * (b * 0.5 - 0.03), 0, sz * (tf * 0.5 - 0.03)))
            t.append(stab("wagenstange", (p[0], 0.06, p[2]), (p[0], 0.88, p[2]), 0.012, "stahl_hell", seiten=6))
            t.append(zylinder("wagenrolle", 0.03, 0.025, (p[0], 0.03, p[2]), "gummi", seiten=8, dreh=verkette(d, (90, 0, 0)), rund=(0, 0)))
    griff_a = punkt((x, 0, z), d, (-b * 0.5 + 0.03, 1.02, tf * 0.5 - 0.03))
    griff_b = punkt((x, 0, z), d, (b * 0.5 - 0.03, 1.02, tf * 0.5 - 0.03))
    t.append(stab("wagengriff", griff_a, griff_b, 0.016, "akzent"))
    for sx in (-1, 1):
        p = punkt((x, 0, z), d, (sx * (b * 0.5 - 0.03), 0, tf * 0.5 - 0.03))
        t.append(stab("griffstange", (p[0], 0.88, p[2]), (p[0], 1.02, p[2]), 0.012, "stahl_hell", seiten=6))
    return t


def buffer_a2_2():
    """Rollwagen mit zwei vollen Etagen, dazu ein Karton Rohlinge auf der Bank."""
    t = []
    x, z = -0.84, -0.52
    t += _rollwagen(x, z, 0)
    for k, y in enumerate((0.115, 0.495, 0.875)):
        for u in (-1, 1):
            farben = (("shirt_weiss",) * 4, ("shirt_schwarz",) * 3 + ("shirt_weiss",), ("shirt_mint", "shirt_senf", "shirt_blau"))[k]
            t += shirt_stapel((x, y, z + u * 0.19), 4 if k < 2 else 3, farben, gier=90 + u * 3, b=0.28, t=0.24)
    t += paket((-0.30, W_AUF, -0.46), (0.36, 0.20, 0.30), gier=6, band=None)
    t += shirt_stapel((-0.30, W_AUF + 0.20, -0.46), 2, ("shirt_weiss", "shirt_weiss"), gier=0, b=0.28, t=0.22)
    return t


def buffer_a2_3():
    """Hoodie-Regal: Kleiderstange mit Hoodies, Ablage oben, Rohlinge auf der Bank."""
    t = []
    x = -0.84
    t += kleiderstange((x, 0, -0.55), 0.86, 1.52, gier=90, mat="tinte")
    farben = ("akzent", "shirt_schwarz", "shirt_mint", "shirt_senf", "shirt_blau", "shirt_rosa")
    for k in range(6):
        zk = -0.86 + k * 0.13
        t += shirt_haengend((x, 1.52, zk), 0, farben[k], lang=True, buegel=False)
    t.append(glatt("regal_oben", (0.40, 0.025, 0.90), (x, 1.68, -0.55), "birke"))
    for u in (-1, 1):
        t.append(stab("regal_traeger", (x, 1.52, -0.55 + u * 0.43), (x, 1.667, -0.55 + u * 0.43), 0.012, "tinte", seiten=4))
    t += shirt_stapel((x, 1.693, -0.80), 3, ("shirt_weiss", "shirt_schwarz", "akzent"), gier=90, b=0.26, t=0.22)
    t += shirt_stapel((x, 1.693, -0.32), 3, ("shirt_mint", "shirt_blau", "shirt_senf"), gier=90, b=0.26, t=0.22)
    t += shirt_stapel((-0.36, W_AUF, -0.46), 4, ("shirt_weiss", "shirt_weiss", "shirt_schwarz", "shirt_weiss"), gier=8)
    t += shirt_stapel((-0.10, W_AUF, -0.50), 3, ("shirt_schwarz", "shirt_schwarz", "akzent"), gier=-6)
    return t


# Platz 3: Trockner (vorn links)
def buffer_a3_0():
    """Waescheleine zwischen zwei Staendern, drei Shirts mit Klammern."""
    t = []
    z = 0.55
    for x in (-0.90, 0.02):
        t.append(stab("leinen_pfosten", (x, 0.03, z), (x, 1.22, z), 0.016, "birke_dunkel"))
        t.append(glatt("leinen_fuss", (0.20, 0.03, 0.20), (x, 0.015, z), "birke_dunkel", (0, 45, 0)))
    t.append(stab("leine", (-0.90, 1.18, z), (0.02, 1.18, z), 0.005, "papier", seiten=4))
    for k, (x, mat) in enumerate(((-0.62, "shirt_weiss"), (-0.34, "akzent"), (-0.06, "shirt_mint"))):
        t += shirt_haengend((x, 1.24, z), 0, mat, buegel=False)
        for s in (-1, 1):
            t.append(glatt("klammer", (0.015, 0.05, 0.02), (x + s * 0.10, 1.18, z + 0.01), "birke"))
    return t


def buffer_a3_1():
    """Beistelltisch mit Heissluftfoehn, Waescheleine bleibt kurz."""
    t = []
    x, z = -0.62, 0.55
    th = 0.62
    t.append(rund1("beistell_platte", (0.62, 0.03, 0.40), (x, th - 0.015, z), "birke"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(stab("beistell_bein", (x + sx * 0.27, th - 0.03, z + sz * 0.16), (x + sx * 0.28, 0.0, z + sz * 0.17), 0.014, "stahl", seiten=6))
    t += _bedrucktes_shirt(x - 0.10, th, z, 5, mat="shirt_schwarz")
    fx, fy, fz = x + 0.18, th + 0.002, z - 0.02
    t.append(rund1("foehn_fuss", (0.10, 0.02, 0.12), (fx, fy + 0.01, fz), "tinte"))
    t.append(stab("foehn_griff", (fx, fy + 0.02, fz), (fx, fy + 0.16, fz - 0.02), 0.022, "akzent"))
    t.append(zylinder("foehn_rohr", 0.04, 0.22, (fx - 0.06, fy + 0.19, fz), "akzent", seiten=10, dreh=(0, 0, 90)))
    t.append(zylinder("foehn_duese", 0.022, 0.06, (fx - 0.19, fy + 0.19, fz), "stahl_hell", seiten=8, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(stab("foehn_kabel", (fx, fy + 0.02, fz), (fx + 0.12, fy + 0.002, fz + 0.12), 0.006, "tinte", seiten=4))
    # Klappstaender mit zwei Shirts
    sx = -0.08
    for s in (-1, 1):
        t.append(stab("staender", (sx + s * 0.06, 0.01, 0.32), (sx, 1.05, 0.32), 0.012, "stahl_hell", seiten=6))
        t.append(stab("staender", (sx + s * 0.06, 0.01, 0.90), (sx, 1.05, 0.90), 0.012, "stahl_hell", seiten=6))
    t.append(stab("staender_quer", (sx, 1.05, 0.30), (sx, 1.05, 0.92), 0.01, "stahl_hell", seiten=4))
    for k, (zk, mat) in enumerate(((0.46, "shirt_weiss"), (0.76, "shirt_senf"))):
        t += shirt_haengend((sx, 1.11, zk), 0, mat)
    return t


def buffer_a3_2():
    """Trockenofen mit leuchtendem Fenster und Blechen."""
    t = []
    x, z = -0.60, 0.52
    b, h, d = 0.62, 1.00, 0.52
    t.append(kasten("ofen", (b, h, d), (x, 0.06 + h * 0.5, z), "stahl_hell", rund=(0.03, 2)))
    for sx in (-1, 1):
        t.append(glatt("ofen_fuss", (0.06, 0.06, d - 0.08), (x + sx * (b * 0.5 - 0.08), 0.03, z), "tinte"))
    zf = z + d * 0.5
    t.append(rund1("ofen_tuer", (b - 0.08, h - 0.20, 0.03), (x, 0.06 + h * 0.44, zf + 0.012), "stahl", r=0.01))
    t.append(glatt("ofen_fenster", (b - 0.20, h - 0.44, 0.006), (x, 0.06 + h * 0.46, zf + 0.030), "ofen_glut"))
    for k in range(3):
        t.append(glatt("blech", (b - 0.24, 0.012, 0.006), (x, 0.06 + h * 0.30 + k * 0.14, zf + 0.034), "stahl"))
    t.append(stab("ofen_griff", (x + b * 0.5 - 0.10, 0.06 + h * 0.25, zf + 0.06), (x + b * 0.5 - 0.10, 0.06 + h * 0.65, zf + 0.06), 0.012, "tinte", seiten=6))
    t.append(glatt("ofen_leiste", (b - 0.08, 0.10, 0.006), (x, 0.06 + h * 0.92, zf + 0.002), "tinte"))
    for k in range(2):
        t.append(zylinder("regler", 0.025, 0.02, (x - 0.16 + k * 0.10, 0.06 + h * 0.92, zf + 0.012), "akzent", seiten=8, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(glatt("anzeige", (0.12, 0.05, 0.004), (x + 0.14, 0.06 + h * 0.92, zf + 0.006), "schirm_orange"))
    t.append(kugel("lampe", 0.03, (x, 0.06 + h + 0.02, z), "leucht_orange", stufen=1))
    # fertige Shirts daneben auf einem Wagen-Tablett
    t += shirt_stapel((-0.06, 0.0, 0.55), 5, ("shirt_weiss", "akzent", "shirt_mint", "shirt_schwarz", "shirt_senf"), gier=-10)
    return t


def buffer_a3_3():
    """Tunneltrockner: Laufband mit Tunnel, gluehende Oeffnung, Shirts."""
    t = []
    z = 0.58
    x0, x1 = -1.04, 0.10
    bh = 0.70
    bb = 0.46
    t.append(kasten("band_rahmen", (x1 - x0, 0.06, bb + 0.04), ((x0 + x1) * 0.5, bh - 0.03, z), "stahl", rund=(0.012, 1)))
    t.append(glatt("band", (x1 - x0 - 0.04, 0.006, bb - 0.02), ((x0 + x1) * 0.5, bh + 0.003, z), "gummi"))
    for x in (x0 + 0.06, x1 - 0.06):
        for s in (-1, 1):
            t.append(rund1("band_bein", (0.04, bh - 0.06, 0.04), (x, (bh - 0.06) * 0.5, z + s * (bb * 0.5 - 0.02)), "stahl"))
    tx0, tx1 = -0.72, -0.18
    tm = (tx0 + tx1) * 0.5
    th = 0.44
    t.append(kasten("tunnel", (tx1 - tx0, th, bb + 0.10), (tm, bh + th * 0.5, z), "tinte", rund=(0.04, 2)))
    for x in (tx0 - 0.002, tx1 + 0.002):
        t.append(glatt("tunnel_glut", (0.006, th * 0.45, bb - 0.08), (x, bh + th * 0.26, z), "ofen_glut"))
    t.append(glatt("tunnel_streifen", (tx1 - tx0 - 0.06, 0.05, 0.006), (tm, bh + th * 0.78, z + (bb + 0.10) * 0.5 + 0.002), "akzent"))
    t.append(glatt("tunnel_fenster", (tx1 - tx0 - 0.16, 0.12, 0.006), (tm, bh + th * 0.42, z + (bb + 0.10) * 0.5 + 0.002), "ofen_glut"))
    for k in range(3):
        t.append(zylinder("abluft", 0.04, 0.10, (tm - 0.16 + k * 0.16, bh + th + 0.05, z), "stahl_hell", seiten=8, rund=(0, 0)))
    t.append(kugel("warnlicht", 0.035, (tx1 - 0.04, bh + th + 0.04, z + 0.18), "leucht_orange", stufen=1))
    # Shirts auf dem Band, vor und nach dem Tunnel
    t += _bedrucktes_shirt(-0.92, bh + 0.006, z, 90, mat="shirt_weiss", druck="shirt_blau")
    t += _bedrucktes_shirt(-0.02, bh + 0.006, z, 90, mat="shirt_schwarz")
    # Schaltkasten
    t.append(rund1("schaltkasten", (0.14, 0.22, 0.08), (x1 - 0.10, bh - 0.20, z + bb * 0.5 + 0.06), "stahl_hell"))
    t.append(glatt("schaltknopf", (0.04, 0.04, 0.006), (x1 - 0.10, bh - 0.16, z + bb * 0.5 + 0.103), "akzent"))
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
    "figur": None,
}


# =============================================================================
# Station 3: station_processing -- Verpacken (Packtisch)
# Tisch x -0,80..0,80, z -0,72..-0,08, Hoehe 0,84. Vorn Mitte bleibt frei
# (Platz fuer eine packende Figur, x -0,3..0,3, z 0,1..0,6).
# Platz 1: Tischmitte (x -0,24..0,36).
# Platz 2: Tisch rechts (x 0,40..0,78) und ab m3 der Automat hinter dem Tisch
#          (z -1,06..-0,76).
# Platz 3: Tisch links (x -0,78..-0,28) und ab m3 ein Wagen vorn links.
# =============================================================================

P_X = (-0.80, 0.80)
P_Z = (-0.72, -0.08)
P_H = 0.84
P_AUF = P_H + 0.005
P_MX, P_MZ = 0.06, -0.40


def processing_basis():
    t = []
    x0, x1 = P_X
    z0, z1 = P_Z
    tx, tz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    t.append(kasten("platte", (x1 - x0, 0.05, z1 - z0), (tx, P_H - 0.025, tz), "birke"))
    t.append(glatt("messleiste", (x1 - x0 - 0.10, 0.004, 0.04), (tx, P_H + 0.001, z1 - 0.03), "stahl_hell"))
    for sx in (x0 + 0.05, x1 - 0.05):
        for sz in (z0 + 0.05, z1 - 0.05):
            t.append(rund1("bein", (0.05, P_H - 0.05, 0.05), (sx, (P_H - 0.05) * 0.5, sz), "stahl"))
    t.append(kasten("ablage", (x1 - x0 - 0.06, 0.03, z1 - z0 - 0.06), (tx, 0.16, tz), "birke_dunkel", rund=(0.01, 1)))
    # flache Kartonzuschnitte und Klebepistole auf der Ablage
    for k in range(3):
        t.append(glatt("zuschnitt", (0.60, 0.02, 0.46), (tx - 0.30 + k * 0.01, 0.185 + k * 0.021, tz + k * 0.008), "karton", (0, (k - 1) * 4, 0)))
    gx, gz = 0.40, tz
    t.append(rund1("pistole", (0.20, 0.06, 0.08), (gx, 0.205, gz), "akzent", r=0.01))
    t.append(ring("pistole_rolle", 0.05, 0.018, (gx - 0.02, 0.21, gz), "klebeband", dreh=(90, 0, 0), segmente=8, quer=4))
    t.append(glatt("pistole_griff", (0.04, 0.03, 0.06), (gx + 0.07, 0.19, gz), "tinte"))
    # Papierrollenhalter an der Tischkante links
    t.append(zylinder("papierrolle", 0.06, 0.52, (tx - 0.30, P_H - 0.13, z0 - 0.02), "karton", seiten=10, dreh=(0, 0, 90)))
    for s in (-1, 1):
        t.append(glatt("rollenhalter", (0.02, 0.14, 0.04), (tx - 0.30 + s * 0.28, P_H - 0.10, z0 - 0.02), "stahl"))
    return t


def _offener_karton(x, y, z, b, h, tf, gier, mat="karton", klappen=True, inhalt=None):
    d = (0, gier, 0)
    w = 0.012
    t = [glatt("karton_boden", (b, w, tf), punkt((x, y, z), d, (0, w * 0.5, 0)), mat, d)]
    for s in (-1, 1):
        t.append(glatt("karton_wand", (w, h, tf), punkt((x, y, z), d, (s * (b - w) * 0.5, h * 0.5, 0)), mat, d))
        t.append(glatt("karton_wand", (b, h, w), punkt((x, y, z), d, (0, h * 0.5, s * (tf - w) * 0.5)), mat, d))
    if klappen:
        for s in (-1, 1):
            t.append(glatt("karton_klappe", (b, 0.008, tf * 0.45), punkt((x, y, z), d, (0, h + 0.02, s * (tf * 0.5 + tf * 0.19))), mat, verkette(d, (s * 30, 0, 0))))
    if inhalt:
        t += shirt_stapel(punkt((x, y + w, z), d, (0, 0, 0)), 2, inhalt, gier=gier, b=b - 0.06, t=tf - 0.06, d=0.04)
    return t


def processing_a1_0():
    """Versandtuete, halb gefuellt, daneben ein Shirt."""
    x, y, z = P_MX, P_AUF, P_MZ
    t = [kasten("tuete", (0.34, 0.03, 0.42), (x - 0.04, y + 0.015, z), "papier_grau", (0, 8, 0), rund=(0.012, 1))]
    t.append(glatt("tuete_lasche", (0.32, 0.006, 0.08), punkt((x - 0.04, y + 0.03, z), (0, 8, 0), (0, 0, -0.23)), "papier_grau", (0, 8, 0)))
    t.append(glatt("tuete_etikett", (0.12, 0.004, 0.08), punkt((x - 0.04, y + 0.032, z), (0, 8, 0), (0.06, 0, 0.08)), "papier", (0, 8, 0)))
    t += shirt_stapel((x + 0.20, y, z + 0.12), 1, ("shirt_schwarz",), gier=-12, b=0.24, t=0.22)
    return t


def processing_a1_1():
    """Offener Karton mit zwei Shirts, Klappen stehen auf."""
    x, y, z = P_MX, P_AUF, P_MZ
    t = _offener_karton(x, y, z + 0.02, 0.46, 0.22, 0.36, 6, inhalt=("akzent", "shirt_weiss"))
    t.append(ring("klebeband", 0.05, 0.018, (x + 0.30, y + 0.018, z + 0.16), "klebeband", segmente=8, quer=4))
    return t


def processing_a1_2():
    """Karton mit Logo, zugeklebt, dahinter der naechste offene."""
    x, y, z = P_MX, P_AUF, P_MZ
    t = _offener_karton(x - 0.10, y, z - 0.08, 0.40, 0.20, 0.30, -4, inhalt=("shirt_mint", "shirt_weiss"))
    t += paket((x + 0.18, y, z + 0.16), (0.30, 0.18, 0.22), gier=10, band="akzent", logo=True)
    t += paket((x + 0.18, y + 0.18, z + 0.16), (0.24, 0.14, 0.18), gier=-6, band="akzent", logo=True)
    return t


def _geschenkbox(x, y, z, b, h, gier, mat="tinte", band="akzent", schleife=True):
    d = (0, gier, 0)
    t = [kasten("box", (b, h, b), punkt((x, y, z), d, (0, h * 0.5, 0)), mat, d, rund=(0.01, 1))]
    t.append(glatt("box_band", (0.035, h + 0.004, b + 0.004), punkt((x, y, z), d, (0, h * 0.5, 0)), band, d))
    t.append(glatt("box_band", (b + 0.004, h + 0.004, 0.035), punkt((x, y, z), d, (0, h * 0.5, 0)), band, d))
    if schleife:
        for s in (-1, 1):
            t.append(kugel("schleife", 0.035, punkt((x, y, z), d, (s * 0.035, h + 0.02, 0)), band, stufen=1, skala=(1.2, 0.6, 0.8), dreh=d))
    return t


def processing_a1_3():
    """Geschenkbox: offene schwarze Box mit Seidenpapier, Deckel, zwei fertige Boxen."""
    x, y, z = P_MX, P_AUF, P_MZ
    t = _offener_karton(x - 0.06, y, z + 0.06, 0.34, 0.12, 0.34, 0, mat="tinte", klappen=False)
    t.append(kasten("seide", (0.30, 0.03, 0.30), (x - 0.06, y + 0.10, z + 0.06), "seide", (0, 0, 6), rund=(0, 0)))
    t.append(glatt("sticker", (0.07, 0.004, 0.07), (x - 0.06, y + 0.124, z + 0.06), "akzent", (0, 45, 6)))
    t.append(glatt("dankeskarte", (0.12, 0.004, 0.08), (x - 0.10, y + 0.127, z + 0.10), "shirt_weiss", (0, 20, 6)))
    for s_ in (-1, 1):
        t.append(kugel("schleife", 0.04, (x - 0.06 + s_ * 0.04, y + 0.13, z - 0.02), "akzent", stufen=1, skala=(1.2, 0.6, 0.8)))
    t += _geschenkbox(x + 0.24, y, z + 0.14, 0.18, 0.12, 12)
    t += _geschenkbox(x + 0.24, y + 0.12, z + 0.14, 0.13, 0.09, -8, mat="akzent", band="shirt_weiss")
    return t


# Platz 2: Etiketten (Tisch rechts)
E_X, E_Z = 0.60, -0.40


def processing_a2_0():
    """Filzstift und ein Bogen Adressetiketten."""
    t = [glatt("bogen", (0.21, 0.004, 0.29), (E_X, P_AUF + 0.002, E_Z), "papier", (0, -8, 0))]
    for r in range(4):
        for s in range(2):
            t.append(glatt("etikett", (0.08, 0.002, 0.05), punkt((E_X, P_AUF + 0.005, E_Z), (0, -8, 0), (-0.05 + s * 0.10, 0, -0.10 + r * 0.065)), "shirt_weiss" if (r + s) % 3 else "akzent", (0, -8, 0)))
    t.append(stab("filzstift", (E_X + 0.12, P_AUF + 0.012, E_Z + 0.10), (E_X + 0.14, P_AUF + 0.012, E_Z - 0.05), 0.011, "tinte", seiten=6))
    return t


def _etikettendrucker(x, y, z, gier, mat="shirt_weiss"):
    d = (0, gier, 0)
    t = [kasten("etidrucker", (0.16, 0.14, 0.22), punkt((x, y, z), d, (0, 0.07, 0)), mat, d, rund=(0.03, 2))]
    t.append(glatt("eti_deckel", (0.12, 0.006, 0.12), punkt((x, y, z), d, (0, 0.141, -0.03)), "glas", d))
    t.append(glatt("eti_band", (0.07, 0.004, 0.10), punkt((x, y, z), d, (0, 0.05, 0.15)), "papier", verkette(d, (40, 0, 0))))
    t.append(glatt("eti_knopf", (0.03, 0.02, 0.006), punkt((x, y, z), d, (0.04, 0.10, 0.111)), "akzent", d))
    return t


def processing_a2_1():
    """Kleiner Etikettendrucker."""
    return _etikettendrucker(E_X, P_AUF, E_Z - 0.05, -10)


def processing_a2_2():
    """Zwei Etikettendrucker und eine Ersatzrolle."""
    t = _etikettendrucker(E_X - 0.08, P_AUF, E_Z - 0.14, -6)
    t += _etikettendrucker(E_X + 0.10, P_AUF, E_Z + 0.06, -14, mat="akzent")
    t.append(ring("ersatzrolle", 0.04, 0.02, (E_X - 0.10, P_AUF + 0.02, E_Z + 0.18), "papier", segmente=8, quer=4))
    return t


def processing_a2_3():
    """Etikettenautomat hinter dem Tisch: Saeule, Schirm, Arm ueber dem Band."""
    t = []
    ax, az = 0.56, -0.91
    t.append(kasten("automat", (0.46, 1.34, 0.26), (ax, 0.67, az), "stahl_hell", rund=(0.03, 2)))
    zf = az + 0.13
    t.append(glatt("automat_front", (0.40, 0.36, 0.006), (ax, 1.06, zf + 0.002), "tinte"))
    t += schirm_inhalt((ax, 1.08, zf + 0.004), (0, 0, 0), 0.30, 0.22, "schlange")
    t.append(glatt("automat_streifen", (0.44, 0.05, 0.006), (ax, 0.30, zf + 0.002), "akzent"))
    t.append(zylinder("automat_rolle", 0.10, 0.08, (ax - 0.26, 1.10, az), "papier", seiten=12, dreh=(0, 0, 90)))
    t.append(zylinder("automat_kern", 0.03, 0.09, (ax - 0.26, 1.10, az), "akzent", seiten=6, dreh=(0, 0, 90), rund=(0, 0)))
    # Arm ueber den Tisch, Stempelkopf ueber einem Paket
    t.append(rund1("automat_arm", (0.10, 0.08, 0.64), (ax, 1.24, az + 0.40), "tinte"))
    t.append(rund1("automat_kopf", (0.12, 0.14, 0.12), (ax, 1.12, -0.36), "akzent"))
    t.append(stab("automat_stempel", (ax, 1.05, -0.36), (ax, 1.00, -0.36), 0.03, "stahl", seiten=8))
    t += paket((ax, P_AUF, -0.36), (0.26, 0.14, 0.20), gier=0, band="klebeband")
    t.append(glatt("paket_etikett", (0.10, 0.004, 0.07), (ax, P_AUF + 0.145, -0.33), "papier"))
    t.append(kugel("automat_licht", 0.03, (ax + 0.17, 1.36, az), "leucht_orange", stufen=1))
    return t


# Platz 3: Fuellung (Tisch links)
F_X, F_Z = -0.54, -0.40


def processing_a3_0():
    """Ein Stapel Zeitungspapier, ein Bogen zerknuellt."""
    t = []
    for k in range(4):
        t.append(glatt("zeitung", (0.30, 0.012, 0.40), (F_X, P_AUF + 0.006 + k * 0.012, F_Z), "papier_grau", (0, (k * 7) % 11 - 5, 0)))
    t.append(glatt("zeitung_spalte", (0.10, 0.003, 0.30), (F_X - 0.06, P_AUF + 0.050, F_Z), "grau_mittel", (0, 1, 0)))
    t.append(kugel("knaeuel", 0.05, (F_X + 0.10, P_AUF + 0.10, F_Z + 0.10), "papier_grau", stufen=1))
    return t


def processing_a3_1():
    """Seidenpapier in zwei Farben, ein Bogen aufgefaltet."""
    t = []
    for k, mat in enumerate(("seide", "seide", "shirt_rosa", "seide", "shirt_weiss")):
        t.append(glatt("seide", (0.30, 0.010, 0.40), (F_X, P_AUF + 0.005 + k * 0.010, F_Z), mat, (0, (k * 5) % 9 - 4, 0)))
    t.append(kasten("seide_bausch", (0.22, 0.05, 0.16), (F_X + 0.04, P_AUF + 0.075, F_Z + 0.06), "seide", (0, 20, 8), rund=(0.02, 1)))
    return t


def _stickerrolle(x, y, z, gier=0):
    t = [rund1("abroller", (0.10, 0.03, 0.14), (x, y + 0.015, z), "tinte", (0, gier, 0))]
    t.append(zylinder("stickerrolle", 0.06, 0.06, (x, y + 0.09, z), "akzent", seiten=12, dreh=(0, gier, 90)))
    t.append(zylinder("stickerkern", 0.02, 0.065, (x, y + 0.09, z), "papier", seiten=6, dreh=(0, gier, 90), rund=(0, 0)))
    return t


def processing_a3_2():
    """Seidenpapier plus Sticker-Rolle im Abroller."""
    t = processing_a3_1()
    t += _stickerrolle(F_X - 0.06, P_AUF, F_Z - 0.26 + 0.02)
    return t


def processing_a3_3():
    """Dankeskarten-Station: Wagen vorn links mit Karten, Umschlaegen, Stickern."""
    t = processing_a3_1()
    wx, wz = -0.76, 0.34
    wh = 0.74
    t.append(rund1("wagen_platte", (0.48, 0.03, 0.56), (wx, wh - 0.015, wz), "birke"))
    t.append(glatt("wagen_boden", (0.44, 0.02, 0.52), (wx, 0.22, wz), "birke_dunkel"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(stab("wagen_bein", (wx + sx * 0.20, 0.05, wz + sz * 0.24), (wx + sx * 0.20, wh - 0.03, wz + sz * 0.24), 0.013, "stahl", seiten=6))
            t.append(kugel("wagen_rolle", 0.03, (wx + sx * 0.20, 0.03, wz + sz * 0.24), "gummi", stufen=1))
    # Kartenstapel in Faechern
    for k, mat in enumerate(("shirt_weiss", "akzent", "shirt_mint")):
        t.append(glatt("karten", (0.12, 0.03, 0.09), (wx - 0.13 + k * 0.13, wh + 0.015, wz - 0.16), mat, (0, (k - 1) * 6, 0)))
    t.append(glatt("karte_offen", (0.14, 0.004, 0.10), (wx - 0.04, wh + 0.002, wz + 0.02), "papier", (0, 15, 0)))
    t.append(glatt("karte_herz", (0.04, 0.003, 0.04), (wx - 0.04, wh + 0.006, wz + 0.02), "akzent", (0, 60, 0)))
    t.append(rund1("umschlagkiste", (0.18, 0.12, 0.14), (wx + 0.10, wh + 0.06, wz + 0.14), "papier_grau", r=0.006))
    for k in range(3):
        t.append(glatt("umschlag", (0.16, 0.10, 0.006), (wx + 0.10, wh + 0.10, wz + 0.10 + k * 0.03), "papier" if k != 1 else "seide"))
    t += _stickerrolle(wx - 0.15, wh, wz + 0.14)
    t.append(stab("stift", (wx + 0.02, wh + 0.008, wz + 0.22), (wx - 0.06, wh + 0.008, wz + 0.10), 0.008, "tinte", seiten=6))
    # unten: Nachschub
    t += _geschenkbox(wx - 0.10, 0.23, wz, 0.18, 0.12, 5, band="shirt_weiss")
    t += paket((wx + 0.12, 0.23, wz), (0.18, 0.14, 0.30), band=None)
    return t


PROCESSING = {
    "basis": processing_basis,
    "plaetze": {
        1: {0: processing_a1_0, 1: processing_a1_1, 2: processing_a1_2, 3: processing_a1_3},
        2: {0: processing_a2_0, 1: processing_a2_1, 2: processing_a2_2, 3: processing_a2_3},
        3: {0: processing_a3_0, 1: processing_a3_1, 2: processing_a3_2, 3: processing_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (0.0, 0.0, 0.30))],
    "frei": [(0.0, 0.30, 0.25, 1.5)],
}


# =============================================================================
# Station 4: station_transport -- Versand (Paketregal)
# Regal x -0,30..1,00, z -1,02..-0,58, Hoehe 1,60.
# Platz 1: vorn rechts (x 0,18..1,06, z -0,50..0,60) -- Pakete.
# Platz 2: hinten links (x -1,06..-0,38, z -1,06..-0,45) -- Waage.
# Platz 3: vorn links (x -1,06..0,12, z -0,35..1,06) -- Abholung.
# =============================================================================

R_X = (-0.30, 1.00)
R_Z = (-1.02, -0.58)
R_H = 1.60


def transport_basis():
    t = []
    x0, x1 = R_X
    z0, z1 = R_Z
    rx, rz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    for sx in (x0 + 0.02, x1 - 0.02):
        for sz in (z0 + 0.02, z1 - 0.02):
            t.append(rund1("regalpfosten", (0.04, R_H, 0.04), (sx, R_H * 0.5, sz), "stahl"))
    boeden = (0.08, 0.52, 0.96, 1.40)
    for y in boeden:
        t.append(glatt("regalboden", (x1 - x0 - 0.02, 0.03, z1 - z0 - 0.02), (rx, y, rz), "birke"))
        t.append(glatt("regalkante", (x1 - x0, 0.04, 0.02), (rx, y, z1), "akzent" if y == boeden[0] else "stahl"))
    t.append(stab("diagonale", (x0 + 0.02, 0.10, z0 + 0.03), (x0 + 0.02, 1.38, z1 - 0.03), 0.009, "stahl", seiten=4))
    t.append(stab("diagonale", (x1 - 0.02, 0.10, z1 - 0.03), (x1 - 0.02, 1.38, z0 + 0.03), 0.009, "stahl", seiten=4))
    pakete = ((0.00, 0, (0.34, 0.26, 0.34), 4), (0.42, 0, (0.40, 0.30, 0.36), -3), (0.80, 0, (0.26, 0.20, 0.30), 6),
              (0.05, 1, (0.30, 0.22, 0.30), -5), (0.44, 1, (0.26, 0.30, 0.34), 2),
              (0.15, 2, (0.40, 0.18, 0.34), 3), (0.62, 2, (0.24, 0.24, 0.28), -6),
              (0.30, 3, (0.34, 0.14, 0.30), 0))
    for px, ebene, gr, g in pakete:
        t += paket((px, boeden[ebene] + 0.016, rz), gr, gier=g, logo=(ebene == 1 and px > 0.3), billig=True)
    t.append(glatt("regalschild", (0.24, 0.06, 0.006), (rx, 1.50, z1 + 0.012), "shirt_weiss"))
    return t


def _paketstapel(x, y, z, anzahl, gier=0.0, billig=False):
    t = []
    groessen = ((0.40, 0.24, 0.32), (0.32, 0.20, 0.28), (0.26, 0.16, 0.22), (0.22, 0.14, 0.18))
    for k in range(anzahl):
        gr = groessen[k % 4]
        t += paket((x, y, z), gr, gier=gier + ((k * 13) % 17) - 8, logo=(k % 2 == 1), billig=billig)
        y += gr[1]
    return t


def transport_a1_0():
    """Ein Stapel Pakete auf dem Boden."""
    return _paketstapel(0.62, 0.0, 0.05, 3)


def _gitterbox(x, z, b, h, tf, rollen=False):
    t = []
    y0 = 0.08 if rollen else 0.0
    t.append(glatt("gitter_boden", (b, 0.03, tf), (x, y0 + 0.015, z), "stahl"))
    for sx in (-1, 1):
        for sz in (-1, 1):
            px, pz = x + sx * (b * 0.5 - 0.015), z + sz * (tf * 0.5 - 0.015)
            t.append(glatt("gitter_pfosten", (0.03, h, 0.03), (px, y0 + h * 0.5, pz), "stahl"))
            if rollen:
                t.append(kugel("gitter_rolle", 0.04, (px, 0.04, pz), "gummi", stufen=1))
    for y in (y0 + h * 0.5, y0 + h - 0.015):
        for s in (-1, 1):
            t.append(glatt("gitter_holm", (b, 0.02, 0.02), (x, y, z + s * (tf * 0.5 - 0.015)), "stahl_hell"))
            t.append(glatt("gitter_holm", (0.02, 0.02, tf), (x + s * (b * 0.5 - 0.015), y, z), "stahl_hell"))
    for k in range(1, 4):
        u = -0.5 + k * 0.25
        for s in (-1, 1):
            t.append(glatt("gitter_stab", (0.012, h - 0.04, 0.012), (x + u * b, y0 + h * 0.5, z + s * (tf * 0.5 - 0.015)), "stahl_hell"))
            t.append(glatt("gitter_stab", (0.012, h - 0.04, 0.012), (x + s * (b * 0.5 - 0.015), y0 + h * 0.5, z + u * tf), "stahl_hell"))
    return t, y0 + 0.03


def transport_a1_1():
    """Gitterbox, halb voll mit Paketen."""
    t, yb = _gitterbox(0.62, 0.05, 0.70, 0.62, 0.70)
    t += paket((0.47, yb, -0.10), (0.34, 0.26, 0.32), gier=4)
    t += paket((0.78, yb, -0.08), (0.28, 0.22, 0.28), gier=-6, logo=True)
    t += paket((0.58, yb, 0.22), (0.38, 0.28, 0.26), gier=2)
    t += paket((0.60, yb + 0.28, 0.18), (0.26, 0.18, 0.20), gier=-10, band="akzent")
    return t


def transport_a1_2():
    """Rollcontainer, bis oben voll."""
    t, yb = _gitterbox(0.62, 0.02, 0.72, 1.10, 0.66, rollen=True)
    y = yb
    for ebene in range(3):
        for (dx, dz, gr, g) in ((-0.16, -0.14, (0.34, 0.28, 0.30), 3), (0.17, -0.14, (0.30, 0.24, 0.28), -4),
                                (-0.14, 0.16, (0.36, 0.30, 0.28), -2), (0.17, 0.16, (0.28, 0.26, 0.26), 5)):
            if ebene == 2 and dz > 0 and dx > 0:
                continue
            t += paket((0.62 + dx, y, 0.02 + dz), gr, gier=g + ebene * 3, logo=(ebene == 1 and dx < 0), band="akzent" if (ebene == 2 and dx < 0) else "klebeband", billig=True)
        y += 0.31
    return t


def transport_a1_3():
    """Paketrutsche vom Regal herab in eine Gitterbox, Pakete unterwegs."""
    t = []
    rx = 0.62
    oben = (rx, 1.12, -0.50)
    unten = (rx, 0.68, 0.10)
    laenge = math.dist((oben[1], oben[2]), (unten[1], unten[2]))
    neig = math.degrees(math.atan2(oben[1] - unten[1], unten[2] - oben[2]))
    mitte = ((oben[0] + unten[0]) * 0.5, (oben[1] + unten[1]) * 0.5, (oben[2] + unten[2]) * 0.5)
    d = (neig, 0, 0)
    t.append(kasten("rutsche", (0.46, 0.03, laenge), mitte, "stahl_hell", d, rund=(0.01, 1)))
    for s in (-1, 1):
        t.append(glatt("rutsche_rand", (0.03, 0.10, laenge), punkt(mitte, d, (s * 0.245, 0.04, 0)), "akzent", d))
    # zwei Pakete unterwegs, mit der Rutsche geneigt
    for k, u in enumerate((-0.30, 0.08)):
        p = punkt(mitte, d, (0, 0.015 + 0.08, u))
        t.append(rund1("paket", (0.24, 0.16, 0.22), p, "karton", d, r=0.01))
        t.append(glatt("band", (0.05, 0.004, 0.224), punkt(mitte, d, (0, 0.015 + 0.161, u)), "akzent" if k == 0 else "klebeband", d))
    # Stuetzen der Rutsche
    for s in (-1, 1):
        fuss = punkt(mitte, d, (s * 0.20, 0, laenge * 0.35))
        t.append(stab("rutsche_stuetze", (fuss[0], 0.0, fuss[2]), fuss, 0.016, "stahl", seiten=6))
    # Auffang-Gitterbox unten
    g, yb = _gitterbox(rx, 0.34, 0.66, 0.56, 0.44)
    t += g
    t += paket((rx - 0.14, yb, 0.30), (0.28, 0.22, 0.26), gier=8, billig=True)
    t += paket((rx + 0.15, yb, 0.36), (0.24, 0.20, 0.22), gier=-12, logo=True, billig=True)
    # Schild
    t.append(stab("schild_stange", (rx + 0.36, 0.0, -0.20), (rx + 0.36, 1.20, -0.20), 0.014, "tinte", seiten=6))
    t.append(glatt("schild_fuss", (0.18, 0.03, 0.18), (rx + 0.36, 0.015, -0.20), "tinte"))
    t.append(rund1("schild", (0.03, 0.22, 0.30), (rx + 0.36, 1.26, -0.20), "akzent", r=0.01))
    t.append(glatt("schild_pfeil", (0.006, 0.05, 0.16), (rx + 0.36 - 0.018, 1.26, -0.20), "shirt_weiss"))
    t.append(glatt("schild_pfeil", (0.006, 0.05, 0.16), (rx + 0.36 + 0.018, 1.26, -0.20), "shirt_weiss"))
    return t


# Platz 2: Waage (hinten links)
V_X, V_Z = -0.72, -0.74


def transport_a2_0():
    """Kuechenwaage auf einer Kiste, ein Paeckchen darauf."""
    t = [rund1("kiste", (0.44, 0.42, 0.40), (V_X, 0.21, V_Z), "birke_dunkel")]
    for k in range(2):
        t.append(glatt("kiste_latte", (0.445, 0.04, 0.405), (V_X, 0.12 + k * 0.18, V_Z), "birke"))
    y = 0.422
    t.append(rund1("kuechenwaage", (0.20, 0.04, 0.22), (V_X, y + 0.02, V_Z), "shirt_weiss", r=0.01))
    t.append(glatt("waage_anzeige", (0.08, 0.02, 0.006), (V_X, y + 0.02, V_Z + 0.112), "schirm"))
    t += paket((V_X, y + 0.04, V_Z - 0.01), (0.14, 0.08, 0.12), gier=10)
    return t


def _paketwaage(x, z, b, gross=False):
    t = [rund1("waage", (b, 0.07, b), (x, 0.035, z), "stahl" if gross else "grau_dunkel", r=0.012)]
    t.append(glatt("waage_platte", (b - 0.04, 0.012, b - 0.04), (x, 0.076, z), "stahl_hell"))
    return t


def transport_a2_1():
    """Paketwaage am Boden mit kleinem Anzeigekasten."""
    t = _paketwaage(V_X, V_Z, 0.40)
    t += paket((V_X, 0.082, V_Z), (0.28, 0.20, 0.24), gier=6)
    t.append(stab("waage_kabel", (V_X + 0.20, 0.03, V_Z), (V_X + 0.28, 0.02, V_Z + 0.20), 0.006, "tinte", seiten=4))
    t.append(rund1("waage_display", (0.14, 0.08, 0.05), (V_X + 0.28, 0.04, V_Z + 0.24), "grau_dunkel", (-30, -20, 0), r=0.008))
    t.append(glatt("display_zahl", (0.10, 0.04, 0.004), punkt((V_X + 0.28, 0.04, V_Z + 0.24), (-30, -20, 0), (0, 0, 0.027)), "schirm_gruen", (-30, -20, 0)))
    return t


def _saeule(x, z, h, schirm_art="balken"):
    t = [rund1("saeule", (0.08, h, 0.08), (x, h * 0.5 + 0.07, z), "tinte")]
    kopf = (x, h + 0.14, z + 0.02)
    d = (-20, 0, 0)
    t.append(rund1("saeule_kopf", (0.26, 0.18, 0.04), kopf, "tinte", d, r=0.01))
    t += schirm_inhalt(kopf, d, 0.22, 0.14, schirm_art, tiefe=0.021)
    return t


W_PX, W_PZ = V_X + 0.10, V_Z + 0.02       # Plattform Mitte (0,50 breit)


def transport_a2_2():
    """Plattformwaage mit Paketturm und Anzeige-Saeule."""
    t = _paketwaage(W_PX, W_PZ, 0.50, gross=True)
    t += _saeule(-0.96, -0.90, 0.92, "kurve")
    t += _paketstapel(W_PX, 0.082, W_PZ, 3, gier=0)
    return t


def transport_a2_3():
    """Waage mit Scanner-Tor: Plattform, Tor mit Lichtbalken, Saeule, Handscanner."""
    t = _paketwaage(W_PX, W_PZ, 0.50, gross=True)
    t.append(glatt("waage_akzent", (0.50, 0.02, 0.006), (W_PX, 0.05, W_PZ + 0.253), "akzent"))
    tx = W_PX - 0.30
    for tz in (W_PZ - 0.21, W_PZ + 0.21):
        t.append(rund1("tor_pfosten", (0.06, 1.06, 0.06), (tx, 0.53, tz), "tinte"))
    t.append(rund1("tor_balken", (0.10, 0.08, 0.54), (tx + 0.02, 1.10, W_PZ), "tinte"))
    t.append(glatt("tor_licht", (0.10, 0.02, 0.40), (tx + 0.03, 1.05, W_PZ), "leucht_orange"))
    t.append(glatt("tor_strahl", (0.40, 0.004, 0.40), (W_PX, 0.085, W_PZ), "leucht_orange"))
    t += paket((W_PX, 0.09, W_PZ), (0.32, 0.26, 0.28), gier=5, logo=True)
    t += _saeule(-0.96, -0.36, 0.80, "schlange")
    # Handscanner im Halter an der Saeule
    sx, sz = -0.96 + 0.07, -0.36
    t.append(glatt("halter", (0.04, 0.10, 0.06), (sx, 0.70, sz), "stahl"))
    t.append(rund1("scanner", (0.05, 0.14, 0.07), (sx + 0.02, 0.78, sz), "akzent", (0, 0, -15), r=0.01))
    t.append(glatt("scanner_fenster", (0.004, 0.03, 0.05), (sx + 0.06, 0.84, sz), "leucht_orange", (0, 0, -15)))
    return t


# Platz 3: Abholung (vorn links)
A_X, A_Z = -0.46, 0.42


def _fahrrad(x, z, gier, rahmen="shirt_blau", vorderrad=True):
    d = (0, gier, 0)
    r = 0.22
    t = []
    hinten = punkt((x, r + 0.02, z), d, (-0.34, 0, 0))
    vorn = punkt((x, r + 0.02, z), d, (0.34, 0, 0))
    t += speichenrad(hinten, r, gier)
    if vorderrad:
        t += speichenrad(vorn, r, gier)
    tret = punkt((x, 0, z), d, (-0.04, 0.24, 0))
    sattel = punkt((x, 0, z), d, (-0.14, 0.62, 0))
    lenk = punkt((x, 0, z), d, (0.24, 0.64, 0))
    oben = punkt((x, 0, z), d, (0.20, 0.54, 0))
    rohre = [(hinten, tret), (tret, sattel), (sattel, oben), (tret, oben), (hinten, sattel)]
    if vorderrad:
        rohre.append((oben, vorn))
    for a, b in rohre:
        t.append(stab("rahmen", a, b, 0.014, rahmen, seiten=5))
    t.append(stab("lenkstange", oben, lenk, 0.013, "stahl_hell", seiten=5))
    t.append(stab("lenker", punkt(lenk, d, (0, 0, -0.18)), punkt(lenk, d, (0, 0, 0.18)), 0.013, "tinte", seiten=5))
    t.append(kasten("sattel", (0.16, 0.04, 0.08), (sattel[0], sattel[1] + 0.02, sattel[2]), "tinte", d, rund=(0.012, 1)))
    return t


def transport_a3_0():
    """Ein Fahrrad mit Packtasche."""
    t = _fahrrad(A_X, A_Z, 0)
    t.append(glatt("gepaecktraeger", (0.24, 0.015, 0.14), (A_X - 0.32, 0.46, A_Z), "stahl_hell"))
    t.append(stab("traeger_strebe", (A_X - 0.44, 0.46, A_Z), (A_X - 0.34, 0.22, A_Z), 0.008, "stahl_hell", seiten=4))
    for s in (-1, 1):
        t.append(rund1("packtasche", (0.20, 0.20, 0.06), (A_X - 0.32, 0.36, A_Z + s * 0.11), "akzent" if s > 0 else "shirt_schwarz", r=0.015))
    return t


def transport_a3_1():
    """Lastenrad mit Kiste vorn."""
    # Hinterteil wie ein Fahrrad (ohne Vorderrad), vorn Kiste ueber kleinem Rad
    bx, z = -0.48, A_Z
    t = _fahrrad(bx, z, 0, rahmen="akzent", vorderrad=False)
    rv = 0.13
    vx = -0.04
    t += speichenrad((vx, rv + 0.02, z), rv, 0)
    t.append(stab("lastenholm", (bx + 0.10, 0.26, z), (vx, rv + 0.02, z), 0.016, "akzent", seiten=5))
    kx = vx - 0.06
    t.append(kasten("lastenkiste", (0.34, 0.26, 0.42), (kx, 0.46, z), "birke", rund=(0.02, 1)))
    t.append(glatt("kiste_logo", (0.14, 0.12, 0.006), (kx, 0.46, z + 0.213), "akzent"))
    t += paket((kx, 0.59, z - 0.03), (0.24, 0.14, 0.22), gier=8)
    return t


def transport_a3_2():
    """Kleintransporter mit orangem Streifen."""
    return transporter((A_X, 0, A_Z), 0, laenge=1.10, breite=0.54, hoehe=0.66)


def transport_a3_3():
    """Zwei Transporter, einer mit Dachlicht, Paket davor."""
    t = transporter((A_X, 0, -0.01), 0, laenge=1.08, breite=0.50, hoehe=0.64, dach_licht=True)
    t += transporter((A_X, 0, 0.74), 0, laenge=1.08, breite=0.50, hoehe=0.64, mat="akzent", streifen="shirt_weiss", dach_licht=True)
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
    "figur": None,
}


# =============================================================================
# Station 5: station_special -- Der Drop (Buehne)
# Buehne x -1,02..0,38, z -1,02..0,12, Hoehe 0,16, Rueckwand bei z -0,99.
# Platz 1: auf der Buehne, ab m3 Laufsteg nach vorn (x -0,52..-0,12).
# Platz 2: hinten rechts (x 0,46..1,06, z -1,06..-0,30) -- Kasse.
# Platz 3: vorn rechts (x 0,00..1,06, z -0,20..1,06) -- Warteschlange.
# =============================================================================

B_X = (-1.02, 0.38)
B_Z = (-1.02, 0.12)
B_H = 0.16


def special_basis():
    t = []
    x0, x1 = B_X
    z0, z1 = B_Z
    bx, bz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    t.append(kasten("buehne", (x1 - x0, B_H, z1 - z0), (bx, B_H * 0.5, bz), "birke_dunkel", rund=(0.02, 2)))
    t.append(glatt("buehne_belag", (x1 - x0 - 0.04, 0.004, z1 - z0 - 0.04), (bx, B_H + 0.001, bz), "birke"))
    t.append(glatt("buehne_kante", (x1 - x0 - 0.06, 0.03, 0.006), (bx, B_H * 0.5, z1 + 0.001), "akzent"))
    rw_z = -0.985
    t.append(kasten("rueckwand", (x1 - x0, 1.90, 0.05), (bx, B_H + 0.95, rw_z), "tinte", rund=(0.02, 2)))
    # Logo-Scheibe mit Shirt
    t.append(zylinder("logo_scheibe", 0.30, 0.012, (bx, B_H + 1.22, rw_z + 0.031), "akzent", seiten=20, dreh=(90, 0, 0), rund=(0, 0)))
    t += shirt_zeichen((bx, B_H + 1.22, rw_z + 0.031), (0, 0, 0), 0.34, "shirt_weiss", 0.010)
    for s in (-1, 1):
        t.append(glatt("streifen", (0.04, 1.84, 0.006), (bx + s * 0.62, B_H + 0.95, rw_z + 0.027), "stahl"))
    # zwei Spots oben
    for s in (-1, 1):
        sx = bx + s * 0.48
        t.append(stab("spot_arm", (sx, B_H + 1.90, rw_z), (sx, B_H + 1.98, rw_z + 0.16), 0.012, "stahl", seiten=4))
        t.append(zylinder("spot", 0.06, 0.14, (sx, B_H + 1.94, rw_z + 0.22), "tinte", seiten=10, dreh=(-60, 0, 0), radius_oben=0.045))
        t.append(zylinder("spot_licht", 0.05, 0.006, punkt((sx, B_H + 1.94, rw_z + 0.22), (-60, 0, 0), (0, -0.072, 0)), "licht_warm", seiten=10, dreh=(-60, 0, 0), rund=(0, 0)))
    return t


S_Y = B_H + 0.005


def _stange_buehne(anzahl, z=-0.66, x=-0.30):
    t = kleiderstange((x, S_Y, z), 1.00, 1.30, mat="tinte")
    farben = ("akzent", "shirt_weiss", "shirt_schwarz", "shirt_mint", "shirt_senf")
    for k in range(anzahl):
        xk = x - 0.36 + k * (0.72 / max(anzahl - 1, 1))
        t += shirt_haengend((xk, S_Y + 1.30, z), 90, farben[k % len(farben)])
    return t


def special_a1_0():
    """Kleiderstange mit vier Shirts."""
    return _stange_buehne(4)


def special_a1_1():
    """Schaufensterpuppe mit Hoodie vor der Stange."""
    t = _stange_buehne(3)
    t += puppe((-0.30, S_Y, -0.18), 20, "akzent", hoodie=True)
    return t


def special_a1_2():
    """Zwei Puppen, eine mit Kappe."""
    t = _stange_buehne(2)
    t += puppe((-0.62, S_Y, -0.22), 25, "akzent", hoodie=True)
    t += puppe((0.04, S_Y, -0.22), -15, "shirt_schwarz", kappe="akzent")
    return t


def special_a1_3():
    """Laufsteg nach vorn mit Lichtkante, zwei Puppen, eine davon am Ende."""
    t = []
    lx0, lx1 = -0.52, -0.12
    lz0, lz1 = 0.13, 1.04
    lx, lz = (lx0 + lx1) * 0.5, (lz0 + lz1) * 0.5
    lh = 0.14
    t.append(kasten("laufsteg", (lx1 - lx0, lh, lz1 - lz0), (lx, lh * 0.5, lz), "tinte", rund=(0.015, 1)))
    t.append(glatt("laufsteg_belag", (lx1 - lx0 - 0.06, 0.004, lz1 - lz0 - 0.04), (lx, lh + 0.001, lz), "stahl"))
    for s in (-1, 1):
        t.append(glatt("laufsteg_licht", (0.012, 0.02, lz1 - lz0 - 0.02), (lx + s * ((lx1 - lx0) * 0.5 + 0.002), lh * 0.6, lz), "leucht_orange"))
    t.append(glatt("laufsteg_licht", ((lx1 - lx0) - 0.02, 0.02, 0.012), (lx, lh * 0.6, lz1 + 0.002), "leucht_orange"))
    t += puppe((lx, lh + 0.002, lz1 - 0.24), 0, "akzent", hoodie=True, kappe="shirt_schwarz")
    t += puppe((-0.72, S_Y, -0.40), 25, "shirt_schwarz", hoodie=True)
    t += puppe((0.10, S_Y, -0.40), -25, "shirt_weiss", kappe="akzent")
    return t


# Platz 2: Kasse (hinten rechts)
K_X, K_Z = 0.76, -0.70


def special_a2_0():
    """Kassenbox auf einer Kiste."""
    t = [rund1("kiste", (0.40, 0.40, 0.40), (K_X, 0.20, K_Z), "birke_dunkel")]
    for k in range(2):
        t.append(glatt("kiste_latte", (0.405, 0.04, 0.405), (K_X, 0.11 + k * 0.18, K_Z), "birke"))
    t.append(rund1("kassenbox", (0.22, 0.09, 0.16), (K_X, 0.445, K_Z), "stahl", (0, -12, 0), r=0.01))
    t.append(glatt("kassenbox_griff", (0.08, 0.012, 0.02), (K_X, 0.496, K_Z), "tinte", (0, -12, 0)))
    t.append(glatt("schein", (0.10, 0.004, 0.05), (K_X + 0.05, 0.402, K_Z + 0.14), "shirt_mint", (0, 20, 0)))
    return t


def _stehtisch(x, z, h, platte=0.40, mat="birke"):
    t = [zylinder("stehtisch_platte", platte * 0.5, 0.03, (x, h - 0.015, z), mat, seiten=12)]
    t.append(stab("stehtisch_saeule", (x, 0.03, z), (x, h - 0.03, z), 0.025, "tinte", seiten=8))
    t.append(zylinder("stehtisch_fuss", 0.16, 0.03, (x, 0.015, z), "tinte", seiten=10, rund=(0, 0)))
    return t


def _terminal(x, y, z, gier):
    d = (0, gier, 0)
    t = [rund1("terminal", (0.08, 0.03, 0.16), (x, y + 0.015, z), "tinte", d, r=0.008)]
    t.append(glatt("terminal_schirm", (0.06, 0.004, 0.06), punkt((x, y + 0.031, z), d, (0, 0, -0.035)), "schirm_blau", d))
    t.append(glatt("terminal_tasten", (0.06, 0.004, 0.05), punkt((x, y + 0.031, z), d, (0, 0, 0.04)), "stahl_hell", d))
    return t


def special_a2_1():
    """Stehtisch mit Kartenterminal und Kassenbox."""
    t = _stehtisch(K_X, K_Z, 1.00)
    t += _terminal(K_X + 0.06, 1.002, K_Z + 0.04, -20)
    t.append(rund1("kassenbox", (0.18, 0.08, 0.14), (K_X - 0.08, 1.042, K_Z - 0.04), "stahl", (0, 10, 0), r=0.01))
    return t


def _tabletkasse(x, y, z, gier):
    d = (0, gier, 0)
    t = [zylinder("tablet_fuss", 0.06, 0.02, (x, y + 0.01, z), "stahl_hell", seiten=10, rund=(0, 0))]
    t.append(stab("tablet_hals", (x, y + 0.02, z), (x, y + 0.14, z - 0.02), 0.015, "stahl_hell", seiten=6))
    kopf = (x, y + 0.22, z)
    kd = verkette(d, (-30, 0, 0))
    t.append(rund1("tablet", (0.26, 0.18, 0.016), kopf, "tinte", kd, r=0.006))
    t += schirm_inhalt(kopf, kd, 0.22, 0.14, "plan", tiefe=0.009)
    return t


def special_a2_2():
    """Tablet-Kasse auf Podest, Terminal daneben, Tueten."""
    t = [rund1("podest", (0.44, 0.96, 0.40), (K_X, 0.48, K_Z), "shirt_weiss", r=0.02)]
    t.append(glatt("podest_streifen", (0.445, 0.05, 0.405), (K_X, 0.80, K_Z), "akzent"))
    t += _tabletkasse(K_X - 0.04, 0.962, K_Z, -15)
    t += _terminal(K_X + 0.15, 0.962, K_Z + 0.08, -25)
    return t


def special_a2_3():
    """Kassentheke: lange Theke mit Tablet-Kasse, Terminal, Tueten und Leuchtband."""
    t = []
    tx, tz = K_X + 0.02, K_Z + 0.02
    tb, tt, th = 0.52, 0.72, 0.98
    t.append(kasten("theke", (tb, th, tt), (tx, th * 0.5, tz), "tinte", rund=(0.03, 2)))
    t.append(kasten("theke_platte", (tb + 0.06, 0.04, tt + 0.06), (tx, th + 0.02, tz), "birke", rund=(0.012, 1)))
    t.append(glatt("theke_front", (0.006, th - 0.20, tt - 0.10), (tx - tb * 0.5 - 0.002, th * 0.52, tz), "akzent"))
    t.append(glatt("theke_licht", (0.006, 0.03, tt - 0.04), (tx - tb * 0.5 - 0.004, 0.08, tz), "leucht_orange"))
    t += shirt_zeichen((tx - tb * 0.5 - 0.004, th * 0.55, tz), (0, -90, 0), 0.30, "tinte", 0.0)
    y = th + 0.042
    t += _tabletkasse(tx, y, tz - 0.12, -60)
    t += _terminal(tx + 0.02, y, tz + 0.16, -70)
    # Tueten mit Logo
    for k, (dz, mat) in enumerate(((-0.30, "akzent"), (0.28, "shirt_weiss"))):
        t.append(rund1("tuete", (0.16, 0.20, 0.06), (tx + 0.10, y + 0.10, tz + dz), mat, (0, -20, 0), r=0.008))
        t.append(stab("tuete_henkel", (tx + 0.10, y + 0.20, tz + dz - 0.05), (tx + 0.10, y + 0.26, tz + dz), 0.005, "tinte", seiten=4))
    t.append(kugel("klingel", 0.03, (tx - 0.14, y + 0.02, tz + 0.02), "stahl_hell", stufen=1, skala=(1, 0.6, 1)))
    return t


# Platz 3: Warteschlange (vorn rechts)
def special_a3_0():
    """Ein einzelner Absperrpfosten."""
    t, _ = pfosten((0.55, 0.0, 0.42))
    return t


def _schlange(punkte):
    t = []
    koepfe = []
    for p in punkte:
        teile, kopf = pfosten(p)
        t += teile
        koepfe.append(kopf)
    for a, b in zip(koepfe, koepfe[1:]):
        t.append(stab("absperrband", a, b, 0.012, "akzent", seiten=4))
    return t


def special_a3_1():
    """Zwei Pfosten mit Absperrband."""
    return _schlange([(0.30, 0.0, 0.42), (0.92, 0.0, 0.42)])


def special_a3_2():
    """Wartebereich: vier Pfosten im Zickzack, Bodenmarkierung."""
    t = _schlange([(0.12, 0.0, 0.26), (0.92, 0.0, 0.26), (0.92, 0.0, 0.70), (0.12, 0.0, 0.70)])
    for k in range(3):
        t.append(glatt("fussmarke", (0.14, 0.004, 0.08), (0.30 + k * 0.24, 0.002, 0.90), "akzent" if k == 2 else "shirt_weiss"))
    return t


def special_a3_3():
    """Wartebereich mit Neon-Schild (Shirt-Umriss) auf einem Mast."""
    t = _schlange([(0.12, 0.0, 0.26), (0.92, 0.0, 0.26), (0.92, 0.0, 0.70), (0.12, 0.0, 0.70), (0.12, 0.0, 0.96)])
    for k in range(2):
        t.append(glatt("fussmarke", (0.14, 0.004, 0.08), (0.40 + k * 0.28, 0.002, 0.90), "akzent"))
    mx, mz = 0.90, 0.02
    t.append(stab("mast", (mx, 0.03, mz), (mx, 1.36, mz), 0.022, "tinte", seiten=8))
    t.append(zylinder("mast_fuss", 0.10, 0.03, (mx, 0.015, mz), "tinte", seiten=8, rund=(0, 0)))
    ny = 1.60
    d = (0, 45, 0)
    t.append(kasten("neon_platte", (0.44, 0.44, 0.03), (mx, ny, mz), "tinte", d, rund=(0.015, 1)))
    r = 0.011
    s = 0.34
    umriss = [(-0.25, 0.35), (-0.5, 0.2), (-0.38, 0.0), (-0.25, 0.08), (-0.25, -0.35), (0.25, -0.35),
              (0.25, 0.08), (0.38, 0.0), (0.5, 0.2), (0.25, 0.35), (-0.25, 0.35)]
    for (ax, ay), (bx, by) in zip(umriss, umriss[1:]):
        t.append(stab("neon", punkt((mx, ny, mz), d, (ax * s * 1.1, ay * s, 0.028)), punkt((mx, ny, mz), d, (bx * s * 1.1, by * s, 0.028)), r, "leucht_orange", seiten=4))
    t.append(kugel("neon_punkt", 0.028, punkt((mx, ny + 0.02, mz), d, (0, 0, 0.028)), "leucht_orange", stufen=1))
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
    "figur": None,
}

STATIONEN = {"intake": INTAKE, "buffer": BUFFER, "processing": PROCESSING,
             "transport": TRANSPORT, "special": SPECIAL}
wg.STATIONEN = STATIONEN


# =============================================================================
# Fluss-Teil, Altmodelle, Gesamtbudget
# =============================================================================

def fluss_teil():
    """Kleines Paket mit orangem Kreuzband, Ursprung = Mitte, 0,30 m breit."""
    b, h, t = 0.30, 0.20, 0.24
    wg.alles_loeschen()
    teile = [kasten("paket", (b, h, t), (0, 0, 0), "karton", rund=(0.02, 2))]
    teile.append(glatt("band", (0.06, h + 0.006, t + 0.006), (0, 0, 0), "akzent"))
    teile.append(glatt("band", (b + 0.006, h + 0.006, 0.06), (0, 0, 0), "akzent"))
    teile.append(glatt("etikett", (0.08, 0.004, 0.06), (0.08, h * 0.5 + 0.004, 0.06), "papier"))
    obj = wg.zusammenfuegen(teile, "fluss_teil")
    wg.exportieren(obj, AUSGABE_FLUSS)
    g = wg.grenzen(obj)
    print("  fluss_teil: %d Dreiecke, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % ((wg.dreiecke(obj),) + g))


def _stufe_oder_kleiner(stufen, m):
    kandidaten = [s for s in sorted(stufen) if s <= m]
    return kandidaten[-1] if kandidaten else None


def altmodelle(station):
    daten = STATIONEN[station]
    for k in (1, 2, 3):
        wg.alles_loeschen()
        teile = daten["basis"]()
        for platz, stufen in daten["plaetze"].items():
            s = _stufe_oder_kleiner(stufen.keys(), k)
            if s is not None:
                teile += stufen[s]()
        name = "station_%s_%d" % (station, k)
        obj = wg.zusammenfuegen(teile, name)
        wg.exportieren(obj, os.path.join(AUSGABE, name + ".glb"))
        print("  %-42s %5d Dreiecke" % (name, wg.dreiecke(obj)))


def gesamtbudget(station):
    daten = STATIONEN[station]
    wg.alles_loeschen()
    summe = wg.dreiecke(wg.zusammenfuegen(daten["basis"](), "b"))
    for platz, stufen in daten["plaetze"].items():
        groesste = 0
        for m, bauen in stufen.items():
            wg.alles_loeschen()
            groesste = max(groesste, wg.dreiecke(wg.zusammenfuegen(bauen(), "p")))
        summe += groesste
    zeichen = "ok" if summe <= BUDGET_GESAMT else "!! UEBER BUDGET"
    print("  Gesamt (Basis + groesste Stufe je Platz): %d / %d  %s" % (summe, BUDGET_GESAMT, zeichen))
    return 0 if summe <= BUDGET_GESAMT else 1


# =============================================================================
# Symbole: Render wie build_symbole_wg.py, dazu 6 px Kontur in Tinte
# =============================================================================

import build_symbole_wg as sym  # noqa: E402

sym.AUSGABE = AUSGABE_UI
ALLE_Y = sym.ALLE_Y
sym.AZIMUT = {(s, p): 30 for s in STATIONEN for p in range(4)}
sym.AZIMUT.update({
    ("buffer", 2): 50, ("buffer", 3): 20,
    ("transport", 3): 35, ("transport", 2): 30,
    ("special", 0): 25, ("special", 2): -40, ("special", 3): 25,
    ("processing", 2): 20,
})
sym.MOTIVE = {
    ("intake", 2, 2): {"behalten": ["musterwand", "lochblech", "wandbein", "wandfuss", "stoff"]},
    ("intake", 2, 3): {"weg": [(["probe"], ALLE_Y)]},
    ("intake", 3, 3): {"weg": [(["kuebel", "blatt"], ALLE_Y)]},
    ("buffer", 1, 3): {"behalten": ["karussell_fuss", "karussell_saeule", "karussell_nabe", "arm", "palette",
                                    "palette_shirt", "kopfarm", "sieb", "sieb_gaze", "karussell_kappe"]},
    ("buffer", 2, 2): {"weg": [(["paket"], ALLE_Y), (["shirt"], (1.05, 9.0))]},
    ("buffer", 2, 3): {"weg": [(["shirt"], (0.8, 1.2))]},
    ("processing", 3, 3): {"weg": [(["seide", "seide_bausch"], ALLE_Y)]},
}

KONTUR_PX = 6.0
TINTE_SRGB = np.array([0x1B, 0x17, 0x26], dtype=np.float32) / 255.0


def kontur_nachbearbeiten(pfad, ausblenden):
    """Sticker-Stil: 6 px Tinten-Kontur um die Silhouette (kantengeglaettet),
    kein weicher Schatten. Werte in den Bildpuffern sind sRGB."""
    g = sym.GROESSE
    bild = bpy.data.images.load(pfad)
    px = np.array(bild.pixels[:], dtype=np.float32).reshape(g, g, 4)
    bpy.data.images.remove(bild)
    a = px[:, :, 3].copy()
    if ausblenden:
        h = g * 0.30
        y = np.arange(g, dtype=np.float32)
        t = np.clip(y / h, 0.0, 1.0)
        a *= (t * t * (3.0 - 2.0 * t))[:, None]
    rand = int(math.ceil(KONTUR_PX)) + 1
    p = np.pad(a, rand)
    dil = np.zeros_like(a)
    for dy in range(-rand, rand + 1):
        for dx in range(-rand, rand + 1):
            w = min(1.0, max(0.0, KONTUR_PX + 0.5 - math.hypot(dx, dy)))
            if w <= 0.0:
                continue
            ausschnitt = p[rand + dy:rand + dy + g, rand + dx:rand + dx + g]
            np.maximum(dil, ausschnitt * w, out=dil)
    a_neu = a + dil * (1.0 - a)
    rgb = (px[:, :, :3] * a[:, :, None] + TINTE_SRGB * (dil * (1.0 - a))[:, :, None]) / np.maximum(a_neu, 1e-6)[:, :, None]
    aus = np.dstack([rgb, a_neu]).astype(np.float32)
    ziel = bpy.data.images.new("symbol", width=g, height=g, alpha=True)
    ziel.pixels[:] = aus.ravel()
    ziel.filepath_raw = pfad
    ziel.file_format = "PNG"
    ziel.save()
    bpy.data.images.remove(ziel)


sym.nachbearbeiten = kontur_nachbearbeiten


# =============================================================================
# Ablauf
# =============================================================================

def main():
    a = wg.argumente()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    print("")
    print("=== STATIONEN WELT 3 (N21) ===")
    os.makedirs(AUSGABE, exist_ok=True)
    os.makedirs(VORSCHAU, exist_ok=True)
    gesamt = 0
    stationen = [s for s in STATIONEN if not a["nur"] or s in a["nur"]]
    for station in stationen:
        print("--", station)
        gesamt += wg.baue_station(station, export=not a["kein_export"])
        gesamt += gesamtbudget(station)
        if not a["kein_export"]:
            altmodelle(station)
        if a["vorschau"]:
            wg.vorschau_station(station)
        if a["klein"]:
            wg.vorschau_station(station, klein=True)
        if a["nah"]:
            wg.vorschau_nah(station, [3, 3, 3], "m3")
            wg.vorschau_nah(station, [0, 0, 0], "m0")
    if not a["kein_export"] and not a["nur"]:
        fluss_teil()
    if "--symbole" in args:
        os.makedirs(AUSGABE_UI, exist_ok=True)
        anzahl = 0
        for station in stationen:
            anzahl += len(sym.symbole_station(station))
        sym.kontaktbogen(stationen)
        print("  %d Symbole" % anzahl)
    print("")
    print("  Probleme gesamt: %d" % gesamt)


if __name__ == "__main__":
    main()
