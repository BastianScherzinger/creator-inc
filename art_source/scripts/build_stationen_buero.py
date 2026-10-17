"""Erzeugt die Stationen der Welt `buero` (Nachtplan N31) als GLB, dazu die
Symbole, das Fluss-Teil und die Vorschaublaetter.

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_stationen_buero.py
    blender --background --python art_source/scripts/build_stationen_buero.py -- --vorschau
    blender --background --python art_source/scripts/build_stationen_buero.py -- --nur processing --vorschau
    blender --background --python art_source/scripts/build_stationen_buero.py -- --symbole
    blender --background --python art_source/scripts/build_stationen_buero.py -- --kein_export --vorschau

Vertrag (docs/NACHT_PLAN.md Paragraf 5, docs/nacht/ausstattung_welten.md):
    project/assets/stations/buero/station_<id>_basis.glb
    project/assets/stations/buero/station_<id>_ausstattung_<n>_<m>.glb   n = 1..3, m = 0..3
    project/assets/stations/buero/station_<id>_<1|2|3>.glb               Altmodelle (Basis + alle Plaetze auf m)
    project/assets/world/buero/fluss_teil.glb                            <= 0,35 m, Ursprung Mitte
    project/assets/ui/buero/station_<id>.png, station_<id>_ausstattung_<n>_<m>.png   256 x 256

Werkzeuge (Quader, Zylinder, Export, Ueberschneidungspruefung, Vorschau)
kommen unveraendert aus build_stationen_wg.py, die Grundformen der Personen
aus build_figuren_wg.py. Dieses Skript setzt nur Ausgabeordner, Palette und
die Stationen selbst.

Koordinaten: alle Masse sind GODOT-Koordinaten (y oben, Vorderseite +z).
Godot (x, y, z) = Blender (x, -z, y). Farben linear: (c/255)^2,2.
Dateinamen neutral (ADR-010).

Budget: Station mit voller Ausstattung (Basis + jeder Platz in seiner
teuersten Stufe) <= 3.500 Dreiecke. Wird am Ende je Station gemeldet.
"""

import bpy
import math
import os
import sys

import numpy as np
from mathutils import Matrix, Vector

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import build_stationen_wg as wg  # noqa: E402
import build_figuren_wg as fg  # noqa: E402
import build_symbole_wg as sy  # noqa: E402
from build_stationen_wg import (  # noqa: E402
    kasten, zylinder, stab, kugel, ring, keil, punkt, verkette, material,
)

PROJEKT = wg.PROJEKT
AUSGABE = os.path.join(PROJEKT, "project", "assets", "stations", "buero")
AUSGABE_UI = os.path.join(PROJEKT, "project", "assets", "ui", "buero")
AUSGABE_FLUSS = os.path.join(PROJEKT, "project", "assets", "world", "buero", "fluss_teil.glb")
VORSCHAU = os.path.join(PROJEKT, "art_source", "vorschau", "buero_stationen")

BUDGET_GESAMT = 3500

wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU
wg.BUDGET_BASIS = 1100
wg.BUDGET_AUSSTATTUNG = 1300
sy.AUSGABE = AUSGABE_UI

# --- Palette: Lagerhalle, warm-bunt, Akzent Tuerkis #12B5A5 -------------------
wg.PALETTE.update({
    "stahl":          ("#AEB5BE", 0.0),
    "stahl_dunkel":   ("#5B636E", 0.0),
    "regal_blau":     ("#3F6DB8", 0.0),
    "traverse":       ("#F28A2E", 0.0),
    "tuerkis":        ("#12B5A5", 0.0),
    "tuerkis_dunkel": ("#0D8C80", 0.0),
    "tuerkis_hell":   ("#9BE3DA", 0.0),
    "tuerkis_licht":  ("#3FE6D4", 1.3),
    "karton_hell":    ("#E2BC86", 0.0),
    "karton_dunkel":  ("#8E6437", 0.0),
    "band_braun":     ("#B3864C", 0.0),
    "paletten_holz":  ("#D2A56A", 0.0),
    "warn_gelb":      ("#F7C51E", 0.0),
    "gummi":          ("#2C2F36", 0.0),
    "folie":          ("#D4EBF1", 0.0),
    "leder":          ("#9A5634", 0.0),
    "leder_dunkel":   ("#6E3A22", 0.0),
    "gold_metall":    ("#E8B93C", 0.0),
    "licht_rot":      ("#FF5A4A", 1.3),
    "licht_gruen":    ("#5BE07A", 1.3),
    "licht_gelb":     ("#FFD54A", 1.3),
    "matte":          ("#3B4250", 0.0),
    "akte_blau":      ("#5B8FD6", 0.0),
    "akte_rot":       ("#E0664F", 0.0),
    "akte_gelb":      ("#F2C14E", 0.0),
    "tafel":          ("#F4F1EA", 0.0),
    "kunststoff":     ("#E9E4DA", 0.0),
    "v_boden":        ("#D6CFC3", 0.0),
})


def farbmat(name):
    return material(name)


# =============================================================================
# Kleine Personen (Chibi, Stil build_figuren_wg.py, stark vereinfacht)
# Gebaut in Blender-Koordinaten (Z oben, Blick -Y = Godot +z), Ursprung
# zwischen den Fuessen. Eine Person kostet rund 450 Dreiecke.
# =============================================================================

HAUT = ("#F2C7A0", "#D19A70", "#9A6440")
REFLEX = "#E4E8EC"
WESTE_ORANGE = "#FF8A2A"
WESTE_GELB = "#F2D23A"
WESTE_TUERKIS = "#12B5A5"
LICHT_HEX = "#FFF1B0"            # wird beim Anlegen zum leuchtenden Material
SONDERFARBEN = {LICHT_HEX: "licht_warm"}


def _geo(bau):
    return bau.punkte, bau.flaechen, bau.farben


def _gesicht(b, zentrum, radien):
    oben = Vector((0, 0, 1))
    for s in (1.0, -1.0):
        p, n = fg.auf_flaeche(zentrum, radien, (s * 0.36, -1.0, -0.10), einsinken=0.006)
        b.dazu(fg.kugel((0.022, 0.031, 0.012), 5, 3, fg.AUGE), fg.platz(p, fg.ausrichtung(n, oben)))
        p, n = fg.auf_flaeche(zentrum, radien, (s * 0.62, -1.0, -0.40), einsinken=0.005)
        b.dazu(fg.kugel((0.034, 0.020, 0.008), 5, 2, fg.WANGE), fg.platz(p, fg.ausrichtung(n, oben)))
    # kleines Laecheln: flacher dunkler Bogen
    p, n = fg.auf_flaeche(zentrum, radien, (0.0, -1.0, -0.42), einsinken=0.004)
    b.dazu(fg.kugel((0.030, 0.012, 0.006), 5, 2, "#8C3B34"), fg.platz(p, fg.ausrichtung(n, oben)))


def _kopf(haar, haarfarbe, haut, extra, muetze_farbe):
    """Kopf als eigener Bau (wird danach um den Hals geneigt)."""
    k = fg.Bau("kopf")
    c = fg.KOPF_MITTE
    seg, ringe = 8, 5
    if haar in ("muetze", "cap"):
        rand_z = c.z + 0.105
        ueber = (Vector((0, 0, rand_z + 0.015)), Vector((0, 0.05, 1.0)).normalized())
        fg.kopf_mit_haut(k, verdeckt=[ueber], seg=seg, ringe=ringe)
        fg.haarschale(k, haarfarbe, stirn_z=0.06, neigung=56.0, oben_offen=ueber, seg=seg, ringe=ringe)
        R = (0.262, 0.247, 0.20)
        kuppel = fg.verschoben(fg.kugel(R, seg, 4, muetze_farbe, e_hoch=0.8), fg.platz(c + Vector((0, 0.01, 0.095))))
        kuppel = fg.schneiden(kuppel, [(Vector((0, 0, rand_z + 0.03)), Vector((0, 0, -1.0)))])
        k.dazu(kuppel)
        if haar == "muetze":
            stulpe = [(0.0, 0.254), (0.012, 0.272), (0.060, 0.272), (0.072, 0.250)]
            k.dazu(fg.drehkoerper(stulpe, seg, muetze_farbe, sy=0.94), fg.platz(Vector((0, 0.01, rand_z - 0.012))))
        else:
            # Schirm nach hinten (Kappe verkehrt herum)
            k.dazu(fg.kugel((0.12, 0.13, 0.014), 6, 2, muetze_farbe),
                   fg.platz(c + Vector((0, 0.25, 0.115)), fg.drehung(x=-12)))
            k.dazu(fg.kugel((0.06, 0.02, 0.03), 5, 2, "#F4F2EE"), fg.platz(c + Vector((0, 0.235, 0.14))))
    else:
        stirn, neigung = (0.08, 52.0) if haar != "locken" else (0.10, 50.0)
        fg.kopf_mit_haut(k, verdeckt=[fg.unter_haar(stirn, neigung)], seg=seg, ringe=ringe)
        fg.haarschale(k, haarfarbe, stirn_z=stirn, neigung=neigung, seg=seg, ringe=ringe)
        if haar == "zopf":
            k.dazu(fg.kugel((0.055, 0.05, 0.12), 6, 4, haarfarbe),
                   fg.platz(c + Vector((0, 0.27, -0.06)), fg.drehung(x=-20)))
            k.dazu(fg.kugel((0.035, 0.035, 0.02), 5, 2, "#12B5A5"), fg.platz(c + Vector((0, 0.255, 0.05))))
        elif haar == "dutt":
            k.dazu(fg.kugel((0.085, 0.08, 0.075), 6, 4, haarfarbe), fg.platz(c + Vector((0, 0.10, 0.225))))
        elif haar == "locken":
            for off in ((0.11, 0.03, 0.19), (-0.11, 0.03, 0.19), (0.0, -0.06, 0.225), (0.0, 0.13, 0.18)):
                k.dazu(fg.kugel((0.075, 0.075, 0.06), 5, 3, haarfarbe), fg.platz(c + Vector(off)))
    _gesicht(k, c, fg.KOPF_R)
    if "headset" in extra:
        bogen = [Vector((math.cos(a) * 0.272, 0.0, c.z + 0.02 + math.sin(a) * 0.255))
                 for a in (0.15, 0.9, math.pi / 2, math.pi - 0.9, math.pi - 0.15)]
        k.dazu(fg.rohr(bogen, 0.012, 3, "#3A3E46"))
        for s in (1, -1):
            k.dazu(fg.kugel((0.035, 0.05, 0.05), 5, 3, "#2E3138"), fg.platz(Vector((s * 0.268, 0.0, c.z + 0.0))))
        mik = [Vector((0.27, -0.03, c.z - 0.03)), Vector((0.22, -0.16, c.z - 0.10)), Vector((0.12, -0.22, c.z - 0.12))]
        k.dazu(fg.rohr(mik, 0.007, 3, "#3A3E46"))
        k.dazu(fg.kugel((0.02, 0.02, 0.02), 5, 2, "#12B5A5"), fg.platz(Vector((0.11, -0.225, c.z - 0.12))))
    if "stirnlampe" in extra:
        band = [Vector((math.cos(a) * 0.263, math.sin(a) * 0.243, c.z + 0.085)) for a in
                [2 * math.pi * i / 8 for i in range(8)]]
        k.dazu(fg.rohr(band, 0.012, 3, "#2E3138", geschlossen=True))
        k.dazu(fg.kugel((0.045, 0.035, 0.035), 6, 3, "#3A3E46"), fg.platz(Vector((0, -0.255, c.z + 0.085))))
        k.dazu(fg.kugel((0.032, 0.012, 0.026), 6, 2, LICHT_HEX), fg.platz(Vector((0, -0.29, c.z + 0.085))))
    return k


def chibi(haar="kurz", haarfarbe="#6B4630", haut=HAUT[0], weste=WESTE_ORANGE, pulli="#77808F",
          hose="#565E4C", schuh="#474B55", hand=None, extra=(), arme="box", nicken=6.0,
          muetze_farbe="#3E6FA8"):
    b = fg.Bau("person")
    hand = hand or haut

    def rumpf_farbe(t):
        if t < 0.29:
            return hose
        if weste and 0.37 < t < 0.41:
            return REFLEX
        return weste or pulli
    profil = [(0.19, 0.0), (0.205, 0.10), (0.29, 0.178), (0.37, 0.176), (0.41, 0.174),
              (0.585, 0.125), (0.645, 0.0)]
    b.dazu(fg.drehkoerper(profil, 8, rumpf_farbe, sy=fg.RUMPF_TIEFE))

    # Arme
    arm_profil = [(-0.05, 0.0), (0.0, 0.05), (0.19, 0.045), (0.25, 0.052), (0.30, 0.0)]
    for s in (1.0, -1.0):
        schulter = Vector((s * 0.165, 0.0, 0.545))
        if arme == "box":
            r = (s * 0.26, -0.93, -0.10)
        elif arme == "tablet":
            r = (-s * 0.42, -0.80, -0.05)
        elif arme == "zeigen" and s < 0:
            r = (-0.35, -0.55, 0.75)
        elif arme == "zeigen":
            r = (-0.40, -0.80, -0.40)
        else:
            r = (s * 0.17, 0.0, -1.0)
        b.dazu(fg.drehkoerper(arm_profil, 6, lambda t: pulli if t < 0.19 else hand),
               fg.platz(schulter, fg.ausrichtung(r)))

    # Beine mit Schuhen
    bein_profil = [(-0.06, 0.0), (0.0, 0.062), (0.17, 0.052), (0.215, 0.0)]
    for s in (1.0, -1.0):
        huefte = Vector((s * 0.085, 0.0, 0.28))
        b.dazu(fg.drehkoerper(bein_profil, 6, hose), fg.platz(huefte, fg.ausrichtung((0, 0, -1))))
        b.dazu(fg.kugel((0.066, 0.102, 0.052), 6, 3, lambda x, y, z: "#3A3530" if z < -0.3 else schuh,
                        e_hoch=0.7, e_rund=0.85, boden=0.75),
               fg.platz(Vector((s * 0.09, -0.03, 0.039))))

    k = _kopf(haar, haarfarbe, haut, extra, muetze_farbe)
    k.drehen(fg.HALS, fg.drehung(x=nicken))
    b.dazu(_geo(k))
    return b


def person(pos, gier=0.0, **stil):
    """Legt eine Person an Godot-Position `pos` (Fuesse) an, Blick Godot +z
    gedreht um `gier` Grad. Gibt eine Liste mit EINEM Objekt zurueck."""
    b = chibi(**stil)
    me = bpy.data.meshes.new("person")
    me.from_pydata([tuple(p) for p in b.punkte], [], b.flaechen)
    palette = []
    for h in b.farben:
        if h not in palette:
            palette.append(h)
    for h in palette:
        me.materials.append(material(SONDERFARBEN[h]) if h in SONDERFARBEN else fg.material(h))
    for poly, h in zip(me.polygons, b.farben):
        poly.material_index = palette.index(h)
    me.validate()
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(62.0))
    obj = bpy.data.objects.new("person", me)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = (Matrix.Translation(Vector((pos[0], -pos[2], pos[1])))
                        @ Matrix.Rotation(math.radians(gier), 4, "Z"))
    return [obj]


def gedreht(bauen, gier):
    """Baufunktion, deren Teile danach um Godot-y (= Blender-z) gedreht werden."""
    def neu():
        m = Matrix.Rotation(math.radians(gier), 4, "Z")
        teile = bauen()
        for o in teile:
            o.matrix_world = m @ o.matrix_world
        return teile
    neu.__name__ = bauen.__name__
    neu.__doc__ = bauen.__doc__
    return neu


def hand_godot(pos, gier, s, arme="box"):
    """Godot-Position der Hand (s = +1 Figur-links) -- fuer Dinge in der Hand."""
    if arme == "box":
        r = Vector((s * 0.26, -0.93, -0.10))
    else:
        r = Vector((-s * 0.42, -0.80, -0.05))
    h = Vector((s * 0.165, 0.0, 0.545)) + r.normalized() * 0.255
    h = Matrix.Rotation(math.radians(gier), 3, "Z") @ h
    return (pos[0] + h.x, pos[1] + h.z, pos[2] - h.y)


# =============================================================================
# Wiederkehrende Gegenstaende der Lagerhalle
# =============================================================================

def q(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0), r=None):
    """Quader mit sparsamer Rundung: ab 4 cm eine Fase-Stufe, sonst keine."""
    if r is None:
        m = min(groesse)
        r = (min(0.012, m * 0.18), 1) if m >= 0.04 else (0.0, 0)
    return kasten(name, groesse, pos, mat, dreh, rund=r)


def flach(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0)):
    return kasten(name, groesse, pos, mat, dreh, rund=(0.0, 0))


def walze(name, radius, laenge, pos, mat, achse="x", seiten=8):
    """Zylinder quer liegend (Achse Godot-x oder -z), pos = Mitte."""
    dreh = (0, 0, 90) if achse == "x" else (90, 0, 0)
    return zylinder(name, radius, laenge, pos, mat, seiten=seiten, dreh=dreh, rund=(0, 0))


def paket(pos, b, h, t, gier=0.0, band="band_braun", mat="karton", seiten=True, rund=True):
    """Paket, pos = Mitte unten. Klebeband oben laengs, optional an den Seiten."""
    d = (0, gier, 0)
    m = min(b, h, t)
    teile = [kasten("paket", (b, h, t), punkt(pos, d, (0, h * 0.5, 0)), mat, d,
                    rund=(min(0.012, m * 0.12), 1) if rund else (0.0, 0))]
    if band:
        bb = max(0.03, min(0.06, t * 0.28))
        teile.append(flach("band", (b - 0.02, 0.003, bb), punkt(pos, d, (0, h + 0.0015, 0)), band, d))
        if seiten:
            for s in (-1, 1):
                teile.append(flach("band", (0.003, h * 0.45, bb), punkt(pos, d, (s * (b * 0.5 + 0.0015), h * 0.72, 0)), band, d))
    return teile


def offener_karton(pos, b, h, t, gier=0.0, mat="karton"):
    """Offener Karton mit zwei aufgeklappten Laschen, pos = Mitte unten."""
    d = (0, gier, 0)
    teile = [kasten("karton", (b, h, t), punkt(pos, d, (0, h * 0.5, 0)), mat, d, rund=(0.006, 1))]
    teile.append(flach("innen", (b - 0.03, 0.003, t - 0.03), punkt(pos, d, (0, h + 0.0015, 0)), "karton_dunkel", d))
    L = t * 0.42
    w = math.radians(50.0)
    for s in (-1, 1):
        mitte = (0, h + math.sin(w) * L * 0.5 + 0.004, s * (t * 0.5 + math.cos(w) * L * 0.5 + 0.004))
        teile.append(flach("lasche", (b - 0.012, 0.004, L), punkt(pos, d, mitte), "karton_hell", verkette(d, (-s * 50, 0, 0))))
    return teile


def palette(pos, b=0.80, t=0.60, gier=0.0):
    """Holzpalette, pos = Mitte unten. Hoehe 0,11."""
    d = (0, gier, 0)
    teile = [q("palette", (b, 0.025, t), punkt(pos, d, (0, 0.0975, 0)), "paletten_holz", d, r=(0.004, 1))]
    for s in (-1, 0, 1):
        teile.append(flach("kufe", (0.08, 0.085, t - 0.02), punkt(pos, d, (s * (b * 0.5 - 0.05), 0.0425, 0)), "holz", d))
    for s in (-1, 1):
        teile.append(flach("fuge", (b - 0.02, 0.002, 0.012), punkt(pos, d, (0, 0.111, s * t * 0.2)), "holz_dunkel", d))
    return teile


def inhalt(pos, dreh, b, h, art, tiefe=0.0):
    """Leuchtende Flaeche mit wenig Inhalt (spart Dreiecke). Zeigt nach lokal +z."""
    t = [flach("schirm", (b, h, 0.004), punkt(pos, dreh, (0, 0, tiefe)), "schirm", dreh)]
    z = tiefe + 0.0035
    if art == "shop":            # Kopfzeile + zwei Kacheln
        t.append(flach("i", (b * 0.84, h * 0.16, 0.003), punkt(pos, dreh, (0, h * 0.32, z)), "schirm_blau", dreh))
        t.append(flach("i", (b * 0.38, h * 0.46, 0.003), punkt(pos, dreh, (-b * 0.22, -h * 0.13, z)), "schirm_orange", dreh))
        t.append(flach("i", (b * 0.38, h * 0.46, 0.003), punkt(pos, dreh, (b * 0.22, -h * 0.13, z)), "tuerkis_licht", dreh))
    elif art == "kurve":
        for k in range(3):
            hk = h * (0.25 + 0.22 * k)
            t.append(flach("i", (b * 0.18, hk, 0.003), punkt(pos, dreh, (-b * 0.25 + k * b * 0.25, -h * 0.4 + hk * 0.5, z)),
                           "schirm_gruen" if k == 2 else "schirm_blau", dreh))
    elif art == "liste":
        for k, (lg, mat) in enumerate(((0.8, "schirm_blau"), (0.6, "tuerkis_licht"), (0.7, "schirm_orange"))):
            t.append(flach("i", (b * lg, h * 0.14, 0.003), punkt(pos, dreh, (-b * 0.42 + b * lg * 0.5, h * 0.26 - k * h * 0.27, z)), mat, dreh))
    elif art == "karte":         # eine grosse Zahl-Kachel
        t.append(flach("i", (b * 0.7, h * 0.5, 0.003), punkt(pos, dreh, (0, 0.0, z)), "tuerkis_licht", dreh))
    elif art == "scan":
        t.append(flach("i", (b * 0.6, h * 0.1, 0.003), punkt(pos, dreh, (0, 0.0, z)), "licht_rot", dreh))
        t.append(flach("i", (b * 0.3, h * 0.2, 0.003), punkt(pos, dreh, (0, h * 0.3, z)), "schirm_gruen", dreh))
    return t


def bildschirm(pos, dreh, b, h, art="shop", fuss=True, fuss_hoehe=0.08):
    """Schlanker Monitor. Mit Fuss: pos = Mitte unten am Fuss, sonst Mitte
    der Gehaeuse-Unterkante. Bildschirm schaut nach lokal +z."""
    t = []
    unten = 0.0
    if fuss:
        t.append(flach("fuss", (b * 0.34, 0.014, 0.13), punkt(pos, dreh, (0, 0.007, -0.02)), "grau_dunkel", dreh))
        t.append(flach("hals", (0.04, fuss_hoehe + 0.04, 0.025), punkt(pos, dreh, (0, 0.014 + (fuss_hoehe + 0.04) * 0.5, -0.045)), "grau_dunkel", dreh))
        unten = 0.014 + fuss_hoehe
    mitte = punkt(pos, dreh, (0, unten + h * 0.5, 0))
    t.append(q("gehaeuse", (b, h, 0.03), mitte, "schwarz", dreh, r=(0.008, 1)))
    t += inhalt(mitte, dreh, b * 0.9, h * 0.84, art, tiefe=0.016)
    return t


def tastatur(pos, dreh, b=0.34, t=0.11):
    return [flach("tastatur", (b, 0.016, t), punkt(pos, dreh, (0, 0.008, 0)), "grau_dunkel", dreh),
            flach("tasten", (b * 0.88, 0.004, t * 0.7), punkt(pos, dreh, (0, 0.018, 0)), "grau_hell", dreh)]


def tischgestell(x0, x1, z0, z1, hoehe, platte="holz_hell", bein="stahl_dunkel", dicke=0.035, beine=None):
    """Tisch mit Platte und vier (oder `beine`) Stahlbeinen."""
    t = [q("platte", (x1 - x0, dicke, z1 - z0), ((x0 + x1) * 0.5, hoehe - dicke * 0.5, (z0 + z1) * 0.5), platte, r=(0.01, 1))]
    xs = beine or (x0 + 0.05, x1 - 0.05)
    for x in xs:
        for z in (z0 + 0.05, z1 - 0.05):
            t.append(flach("bein", (0.04, hoehe - dicke, 0.04), (x, (hoehe - dicke) * 0.5, z), bein))
    return t


def warnlicht(pos, mat="licht_gelb", hoehe=0.10):
    """Rundumleuchte, pos = Mitte unten."""
    x, y, z = pos
    return [zylinder("leuchte_fuss", 0.045, 0.03, (x, y + 0.015, z), "grau_dunkel", seiten=8, rund=(0, 0)),
            zylinder("leuchte", 0.035, hoehe, (x, y + 0.03 + hoehe * 0.5, z), mat, seiten=8, radius_oben=0.028, rund=(0, 0))]


def bodenmarke(x, z, b, t, mat="warn_gelb"):
    """Rechteckige Klebeband-Markierung am Boden (vier Streifen)."""
    y = 0.0025
    return [flach("marke", (b, 0.005, 0.05), (x, y, z - t * 0.5 + 0.025), mat),
            flach("marke", (b, 0.005, 0.05), (x, y, z + t * 0.5 - 0.025), mat),
            flach("marke", (0.05, 0.005, t - 0.1), (x - b * 0.5 + 0.025, y, z), mat),
            flach("marke", (0.05, 0.005, t - 0.1), (x + b * 0.5 - 0.025, y, z), mat)]


def fussabdruecke(x, z, mat="tuerkis"):
    t = []
    for s in (-1, 1):
        t.append(kugel("abdruck", 0.05, (x + s * 0.08, 0.003, z + 0.02), mat, stufen=1, skala=(0.7, 0.05, 1.1)))
    return t


def pflanze_gross(pos, g=1.0):
    x, y, z = pos
    t = [zylinder("topf", 0.12 * g, 0.24 * g, (x, y + 0.12 * g, z), "tuerkis", seiten=8, radius_oben=0.14 * g, rund=(0, 0))]
    for i in range(5):
        w = 2 * math.pi * i / 5
        t.append(kugel("blatt", 0.12 * g, (x + math.cos(w) * 0.09 * g, y + (0.36 + 0.06 * (i % 2)) * g, z + math.sin(w) * 0.09 * g),
                       "pflanze" if i % 2 == 0 else "pflanze_dunkel", stufen=1, skala=(1.0, 0.8, 1.0)))
    t.append(kugel("blatt", 0.12 * g, (x, y + 0.52 * g, z), "pflanze", stufen=1))
    return t


# =============================================================================
# Station 1: station_intake -- Stehpult (Basis), Bildschirme hinten (Platz 1),
# Kundendienst links (Platz 2), Drucker rechts (Platz 3).
# =============================================================================

I_X0, I_X1, I_Z0, I_Z1, I_H = -0.55, 0.25, -0.50, -0.02, 0.82
I_AUF = I_H + 0.001
I_MX = (I_X0 + I_X1) * 0.5


def intake_basis():
    t = []
    cz, w, d = (I_Z0 + I_Z1) * 0.5, I_X1 - I_X0, I_Z1 - I_Z0
    t.append(q("platte", (w + 0.04, 0.035, d + 0.02), (I_MX, I_H - 0.0175, cz), "holz_hell", r=(0.01, 1)))
    for x in (I_X0 + 0.03, I_X1 - 0.03):
        t.append(q("wange", (0.04, I_H - 0.035, d - 0.04), (x, (I_H - 0.035) * 0.5, cz), "stahl_dunkel"))
        t.append(flach("fuss", (0.08, 0.03, d + 0.06), (x, 0.015, cz), "stahl_dunkel"))
    t.append(q("boden", (w - 0.10, 0.025, d - 0.08), (I_MX, 0.30, cz), "holz"))
    t.append(q("rueckwand", (w - 0.10, 0.34, 0.02), (I_MX, 0.60, I_Z0 + 0.04), "tuerkis", r=(0.006, 1)))
    t.append(stab("fussstange", (I_X0 + 0.05, 0.13, cz + 0.12), (I_X1 - 0.05, 0.13, cz + 0.12), 0.014, "stahl", seiten=6))
    # im Fach: flache Kartons und ein Ordner
    t += paket((I_MX - 0.12, 0.3125, cz + 0.02), 0.34, 0.06, 0.30, band=None, mat="karton_hell")
    t.append(q("ordner", (0.06, 0.26, 0.24), (I_MX + 0.20, 0.3125 + 0.13, cz), "akte_blau", r=(0.008, 1)))
    # auf der Platte vorn: Tastatur, Maus, Ablage mit Bestellzetteln
    t += tastatur((I_MX - 0.06, I_AUF, -0.15), (0, -3, 0))
    t.append(kugel("maus", 0.035, (I_MX + 0.17, I_AUF + 0.018, -0.14), "grau_dunkel", stufen=1, skala=(0.75, 0.5, 1.15)))
    ax, az = I_X0 + 0.07, -0.14
    t.append(q("ablage", (0.11, 0.04, 0.22), (ax, I_AUF + 0.02, az), "tuerkis_dunkel", r=(0.006, 1)))
    for k in range(3):
        t.append(flach("zettel", (0.09, 0.004, 0.19), (ax + 0.004 * k, I_AUF + 0.042 + k * 0.005, az + 0.006 * k), "papier", (0, 4 * k, 0)))
    # Matte vor dem Pult
    t.append(q("matte", (0.90, 0.014, 0.48), (I_MX, 0.007, 0.30), "matte", r=(0.005, 1)))
    t.append(flach("matte_rand", (0.84, 0.003, 0.03), (I_MX, 0.0155, 0.50), "tuerkis"))
    return t


def _zwei_monitore():
    t = bildschirm((I_MX - 0.21, I_AUF, -0.40), (0, 10, 0), 0.38, 0.25, "shop", fuss_hoehe=0.10)
    t += bildschirm((I_MX + 0.21, I_AUF, -0.40), (0, -10, 0), 0.38, 0.25, "liste", fuss_hoehe=0.10)
    return t


def intake_a1_0():
    """Ein Bildschirm."""
    return bildschirm((I_MX, I_AUF, -0.40), (0, 0, 0), 0.44, 0.28, "shop", fuss_hoehe=0.10)


def intake_a1_1():
    """Zwei Bildschirme."""
    return _zwei_monitore()


def intake_a1_2():
    """Vier Bildschirme an einer Saeule."""
    t = [flach("klemme", (0.12, 0.03, 0.08), (I_MX, I_AUF + 0.015, -0.46), "grau_dunkel")]
    t.append(stab("saeule", (I_MX, I_AUF + 0.03, -0.46), (I_MX, 1.52, -0.46), 0.02, "stahl", seiten=6))
    arten = (("shop", "kurve"), ("liste", "karte"))
    for r, y in enumerate((0.90, 1.19)):
        t.append(stab("quer", (I_MX - 0.21, y + 0.13, -0.47), (I_MX + 0.21, y + 0.13, -0.47), 0.014, "stahl", seiten=4))
        for s, x in enumerate((I_MX - 0.21, I_MX + 0.21)):
            t += bildschirm((x, y, -0.43), (0, 6 if s == 0 else -6, 0), 0.40, 0.26, arten[r][s], fuss=False)
    return t


def intake_a1_3():
    """Dashboard-Wand hinter dem Pult, dazu zwei Bildschirme."""
    t = _zwei_monitore()
    wz, mx, my, wb, wh = -0.93, -0.18, 1.45, 1.60, 1.00
    t.append(q("wand", (wb, wh, 0.06), (mx, my, wz), "schwarz", r=(0.012, 1)))
    arten = (("shop", "kurve", "liste"), ("karte", "shop", "kurve"))
    for r, dy in enumerate((0.235, -0.235)):
        for s, dx in enumerate((-0.52, 0.0, 0.52)):
            t += inhalt((mx + dx, my + dy, wz), (0, 0, 0), 0.48, 0.42, arten[r][s], tiefe=0.031)
    t.append(q("leiste", (wb, 0.05, 0.09), (mx, my + wh * 0.5 + 0.025, wz), "tuerkis", r=(0.01, 1)))
    t.append(flach("leiste_licht", (wb - 0.1, 0.02, 0.003), (mx, my + wh * 0.5 + 0.025, wz + 0.047), "tuerkis_licht"))
    for x in (mx - 0.67, mx + 0.67):
        t.append(flach("stuetze", (0.06, my - wh * 0.5 + 0.02, 0.04), (x, (my - wh * 0.5 + 0.02) * 0.5, wz - 0.05), "stahl_dunkel"))
        t.append(q("stuetze_fuss", (0.08, 0.03, 0.24), (x, 0.015, wz - 0.04), "stahl_dunkel", r=(0.006, 1)))
    return t


# Platz 2: Kundendienst links
I_K = (-0.86, 0.25)


def _beistelltisch():
    x, z = I_K
    return [zylinder("tischplatte", 0.20, 0.03, (x, 0.585, z), "holz_hell", seiten=12, rund=(0.008, 1)),
            stab("tischsaeule", (x, 0.02, z), (x, 0.57, z), 0.025, "stahl_dunkel", seiten=6),
            zylinder("tischfuss", 0.15, 0.02, (x, 0.01, z), "stahl_dunkel", seiten=10, rund=(0, 0))]


def _headset_staender(x, y, z, farbe="grau_dunkel", gier=0.0):
    t = [zylinder("hs_fuss", 0.05, 0.015, (x, y + 0.0075, z), "stahl_dunkel", seiten=8, rund=(0, 0)),
         stab("hs_stange", (x, y + 0.015, z), (x, y + 0.20, z), 0.008, "stahl", seiten=4)]
    t.append(ring("hs_buegel", 0.075, 0.011, (x, y + 0.20, z), farbe, dreh=(90, gier, 0), segmente=8, quer=4, anteil=0.5))
    for s in (-1, 1):
        p = punkt((x, y + 0.20, z), (0, gier, 0), (s * 0.075, -0.005, 0))
        t.append(zylinder("hs_muschel", 0.035, 0.03, p, "gummi", seiten=8, dreh=(0, gier, 90), rund=(0, 0)))
    p = punkt((x, y + 0.20, z), (0, gier, 0), (0.075, -0.02, 0))
    q2 = punkt((x, y + 0.20, z), (0, gier, 0), (0.03, -0.07, 0.07))
    t.append(stab("hs_mikro", p, q2, 0.005, farbe, seiten=3))
    t.append(kugel("hs_kapsel", 0.012, q2, "tuerkis", stufen=1))
    return t


def intake_a2_0():
    """Altes Tischtelefon auf einem Beistelltisch."""
    x, z = I_K
    y = 0.60
    t = _beistelltisch()
    d = (0, 25, 0)
    t.append(q("telefon", (0.18, 0.06, 0.15), punkt((x, y, z), d, (0, 0.03, 0)), "rot", d, r=(0.015, 1)))
    t.append(flach("tasten", (0.08, 0.004, 0.07), punkt((x, y, z), d, (0.03, 0.062, 0.03)), "papier", d))
    t.append(q("hoerer", (0.05, 0.035, 0.20), punkt((x, y, z), d, (-0.055, 0.078, 0)), "rot", d, r=(0.012, 1)))
    a = punkt((x, y, z), d, (-0.07, 0.03, 0.08))
    b = punkt((x, y, z), d, (-0.14, 0.01, 0.13))
    t.append(stab("schnur", a, b, 0.006, "rot", seiten=3))
    return t


def intake_a2_1():
    """Headset auf Staender, Notizblock."""
    x, z = I_K
    t = _beistelltisch()
    t += _headset_staender(x - 0.05, 0.60, z - 0.04, gier=90)
    t.append(flach("block", (0.10, 0.008, 0.14), (x + 0.08, 0.604, z + 0.06), "gelb", (0, 15, 0)))
    t.append(stab("stift", (x + 0.05, 0.612, z + 0.10), (x + 0.12, 0.612, z + 0.01), 0.006, "tuerkis", seiten=4))
    return t


def _schmaler_tisch(z0, z1, h=0.62):
    return tischgestell(-1.07, -0.65, z0, z1, h, platte="holz_hell")


def intake_a2_2():
    """Zwei Headsets auf einem schmalen Tisch, Trennwand dazwischen."""
    t = _schmaler_tisch(-0.25, 0.80)
    y = 0.621
    t += _headset_staender(-0.86, y, 0.02, gier=90)
    t += _headset_staender(-0.86, y, 0.55, gier=90, farbe="tuerkis_dunkel")
    t.append(q("trenner", (0.38, 0.28, 0.02), (-0.86, y + 0.14, 0.28), "tuerkis_hell", r=(0.006, 1)))
    for z in (0.14, 0.66):
        t.append(flach("block", (0.10, 0.008, 0.13), (-0.76, y + 0.004, z), "gelb", (0, -10, 0)))
    return t


def intake_a2_3():
    """Callcenter-Insel: zwei Plaetze mit Bildschirm und Headset, Leuchte."""
    t = _schmaler_tisch(-0.30, 0.98)
    y = 0.621
    for z in (-0.28, 0.33, 0.96):
        t.append(q("trenner", (0.40, 0.34, 0.025), (-0.86, y + 0.17, z), "tuerkis", r=(0.006, 1)))
        t.append(flach("trenner_licht", (0.36, 0.015, 0.03), (-0.86, y + 0.345, z), "tuerkis_licht"))
    for i, z in enumerate((0.03, 0.64)):
        t += bildschirm((-0.97, y, z), (0, 90, 0), 0.30, 0.20, ("liste", "shop")[i], fuss_hoehe=0.05)
        t += _headset_staender(-0.74, y, z - 0.16, gier=90, farbe="grau_dunkel")
        t += tastatur((-0.78, y, z + 0.06), (0, 90, 0), b=0.24, t=0.09)
    # Leuchte am hinteren Ende
    t.append(stab("mast", (-1.02, y, -0.20), (-1.02, 1.30, -0.20), 0.012, "stahl_dunkel", seiten=4))
    t.append(kugel("signal", 0.06, (-1.02, 1.34, -0.20), "tuerkis_licht", stufen=1))
    return t


# Platz 3: Drucker rechts
I_D = (0.78, 0.25)


def _tintenstrahler(x, y, z, gier=-20):
    d = (0, gier, 0)
    p = (x, y, z)
    return [q("drucker", (0.36, 0.13, 0.26), punkt(p, d, (0, 0.065, 0)), "kunststoff", d, r=(0.02, 1)),
            flach("einzug", (0.22, 0.14, 0.008), punkt(p, d, (0, 0.17, -0.12)), "grau_hell", verkette(d, (-20, 0, 0))),
            flach("blatt", (0.19, 0.12, 0.003), punkt(p, d, (0, 0.18, -0.108)), "papier", verkette(d, (-20, 0, 0))),
            flach("ausgabe", (0.22, 0.008, 0.10), punkt(p, d, (0, 0.03, 0.17)), "grau_hell", d),
            flach("tasten", (0.06, 0.004, 0.03), punkt(p, d, (0.12, 0.131, 0.07)), "licht_gruen", d)]


def intake_a3_0():
    """Kleiner Tintenstrahler auf einer Kunststoffkiste."""
    x, z = I_D
    t = [q("kiste", (0.44, 0.30, 0.36), (x, 0.15, z), "akte_blau", (0, -8, 0), r=(0.02, 1))]
    t.append(flach("griff", (0.12, 0.03, 0.004), punkt((x, 0.0, z), (0, -8, 0), (0, 0.24, 0.181)), "grau_dunkel", (0, -8, 0)))
    t += _tintenstrahler(x, 0.301, z)
    return t


def _laserdrucker(x, y, z, gier=-10, mat="grau_hell"):
    d = (0, gier, 0)
    p = (x, y, z)
    t = [q("laser", (0.40, 0.26, 0.36), punkt(p, d, (0, 0.13, 0)), mat, d, r=(0.02, 1))]
    t.append(flach("schacht", (0.28, 0.004, 0.14), punkt(p, d, (-0.02, 0.261, -0.04)), "grau_dunkel", d))
    t.append(flach("blatt", (0.20, 0.004, 0.13), punkt(p, d, (-0.02, 0.265, -0.03)), "papier", d))
    t.append(flach("schublade", (0.34, 0.006, 0.003), punkt(p, d, (0, 0.06, 0.181)), "grau_mittel", d))
    t.append(flach("anzeige", (0.07, 0.035, 0.004), punkt(p, d, (0.12, 0.22, 0.181)), "tuerkis_licht", d))
    return t


def intake_a3_1():
    """Laserdrucker auf einem Rollschrank."""
    x, z = I_D
    t = [q("schrank", (0.48, 0.48, 0.44), (x, 0.24 + 0.03, z), "holz", r=(0.015, 1))]
    for s in (-1, 1):
        for u in (-1, 1):
            t.append(zylinder("rolle", 0.03, 0.03, (x + s * 0.19, 0.03, z + u * 0.17), "gummi", seiten=6, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(flach("tuer_fuge", (0.003, 0.40, 0.003), (x, 0.28, z + 0.2215), "holz_dunkel"))
    t += _laserdrucker(x, 0.511, z)
    return t


def _etikettendrucker(x, y, z, mat="kunststoff", gier=0.0):
    d = (0, gier, 0)
    p = (x, y, z)
    return [q("etikett", (0.18, 0.13, 0.20), punkt(p, d, (0, 0.065, 0)), mat, d, r=(0.02, 1)),
            flach("etikett_band", (0.004, 0.08, 0.08), punkt(p, d, (-0.092, 0.07, 0.02)), "papier", d),
            flach("etikett_led", (0.004, 0.02, 0.04), punkt(p, d, (-0.092, 0.11, -0.05)), "licht_gruen", d)]


def _rollenbahn(x, z0, z1, y, breite=0.26, n=7):
    t = []
    for s in (-1, 1):
        t.append(flach("bahn_rand", (0.025, 0.05, z1 - z0), (x + s * (breite * 0.5 + 0.0125), y + 0.025, (z0 + z1) * 0.5), "stahl"))
    for i in range(n):
        z = z0 + 0.04 + i * (z1 - z0 - 0.08) / (n - 1)
        t.append(walze("rolle", 0.018, breite, (x, y + 0.03, z), "stahl_dunkel", seiten=6))
    return t


def intake_a3_2():
    """Etikettenstrasse: Tisch mit Rollenbahn, zwei Etikettendruckern, Paketen."""
    t = tischgestell(0.45, 1.08, -0.62, 0.92, 0.62, platte="holz_hell")
    y = 0.621
    t += _rollenbahn(0.64, -0.58, 0.88, y)
    for z in (-0.30, 0.45):
        t += _etikettendrucker(0.95, y, z)
    for z, g in ((-0.05, 4), (0.62, -6)):
        t += paket((0.64, y + 0.05, z), 0.22, 0.14, 0.18, gier=g, seiten=False)
        t.append(flach("etikett", (0.08, 0.003, 0.06), punkt((0.64, y + 0.05, z), (0, g, 0), (0.04, 0.144, 0.04)), "papier", (0, g, 0)))
    return t


def intake_a3_3():
    """Druckzentrum: grosses Multifunktionsgeraet und Etikettentisch."""
    t = []
    x, z = 0.78, -0.36
    t.append(q("mfg_unten", (0.56, 0.44, 0.48), (x, 0.22, z), "kunststoff", r=(0.015, 1)))
    for k in range(2):
        t.append(flach("fach", (0.48, 0.006, 0.003), (x, 0.13 + k * 0.15, z + 0.2415), "grau_mittel"))
    t.append(q("mfg_oben", (0.56, 0.30, 0.48), (x, 0.59, z), "grau_hell", r=(0.015, 1)))
    t.append(q("deckel", (0.50, 0.04, 0.42), (x, 0.76, z), "grau_mittel", r=(0.01, 1)))
    t.append(flach("ausgabe", (0.34, 0.01, 0.20), (x - 0.04, 0.55, z + 0.30), "grau_hell"))
    for k in range(3):
        t.append(flach("papier", (0.24, 0.004, 0.17), (x - 0.04, 0.557 + k * 0.006, z + 0.30), "papier"))
    t.append(q("bedienfeld", (0.22, 0.03, 0.14), (x + 0.15, 0.78, z + 0.22), "schwarz", (-25, 0, 0), r=(0.006, 1)))
    t += inhalt((x + 0.15, 0.785, z + 0.225), (-115, 0, 0), 0.18, 0.10, "karte", tiefe=0.0)
    t.append(flach("status", (0.50, 0.02, 0.003), (x, 0.47, z + 0.2415), "tuerkis_licht"))
    # Etikettentisch davor
    t += tischgestell(0.47, 1.08, 0.02, 0.96, 0.62, platte="holz_hell")
    y = 0.621
    for zz in (0.22, 0.72):
        t += _etikettendrucker(0.94, y, zz, mat="tuerkis")
    t.append(walze("rolle_gross", 0.06, 0.12, (0.64, y + 0.06, 0.20), "papier", achse="x", seiten=10))
    t += paket((0.64, y, 0.66), 0.24, 0.16, 0.20, gier=-8, band="tuerkis", seiten=False)
    return t


INTAKE = {
    "basis": intake_basis,
    "plaetze": {
        1: {0: intake_a1_0, 1: intake_a1_1, 2: intake_a1_2, 3: intake_a1_3},
        2: {0: intake_a2_0, 1: intake_a2_1, 2: intake_a2_2, 3: intake_a2_3},
        3: {0: intake_a3_0, 1: intake_a3_1, 2: intake_a3_2, 3: intake_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": None,
}


def platte(name, a, b, breite, dicke, mat):
    """Flaches Brett von Punkt a nach Punkt b (Mittellinie, Godot)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    laenge = math.sqrt(dx * dx + dy * dy + dz * dz)
    gier = math.degrees(math.atan2(dx, dz))
    neig = math.degrees(math.asin(-dy / laenge))
    mitte = ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
    return flach(name, (breite, dicke, laenge), mitte, mat, (neig, gier, 0))


# =============================================================================
# Station 2: station_buffer -- Regalgrundgestell hinten (Basis und Platz 1),
# Stapler vorn links (Platz 2), Scanner vorn rechts (Platz 3).
# =============================================================================

R_X = (-0.96, 0.40)            # Staender-Mitten links/rechts
R_Z = (-1.00, -0.50)           # Staender-Mitten hinten/vorn
R_MX = (R_X[0] + R_X[1]) * 0.5
R_MZ = (R_Z[0] + R_Z[1]) * 0.5
R_BL = R_X[1] - R_X[0] - 0.064  # Traverse zwischen den Staendern, je 2 mm Luft
R_T = 0.34                     # Kartontiefe


def _staender(y0, h):
    t = []
    for x in R_X:
        for z in R_Z:
            t.append(q("staender", (0.06, h, 0.06), (x, y0 + h * 0.5, z), "regal_blau", r=(0.01, 1)))
        a, b = R_Z
        t.append(stab("strebe", (x, y0 + 0.08, a), (x, y0 + 0.08, b), 0.012, "regal_blau", seiten=4))
        t.append(stab("strebe", (x, y0 + 0.10, a), (x, y0 + h * 0.5, b), 0.010, "regal_blau", seiten=4))
        t.append(stab("strebe", (x, y0 + h * 0.52, b), (x, y0 + h - 0.08, a), 0.010, "regal_blau", seiten=4))
        t.append(stab("strebe", (x, y0 + h - 0.05, a), (x, y0 + h - 0.05, b), 0.012, "regal_blau", seiten=4))
    return t


def _ebene(y, licht=False):
    """Traversenpaar plus Gitterboden. Oberkante des Bodens: y + 0.047."""
    t = []
    for z in R_Z:
        t.append(flach("traverse", (R_BL, 0.07, 0.04), (R_MX, y, z), "traverse"))
    t.append(flach("gitterboden", (R_BL, 0.012, 0.44), (R_MX, y + 0.041, R_MZ), "stahl"))
    if licht:
        t.append(flach("traverse_licht", (R_BL - 0.1, 0.018, 0.003), (R_MX, y, R_Z[1] + 0.0215), "tuerkis_licht"))
    else:
        for k in range(3):
            t.append(flach("schild", (0.07, 0.035, 0.003), (R_X[0] + 0.25 + k * 0.45, y, R_Z[1] + 0.0215), "papier"))
    return t


def _fuellen(y_boden, reihe):
    """reihe: (x, breite, hoehe, art, gier). art: braun, tuerkis, kiste, folie, flach"""
    t = []
    for x, b, h, art, g in reihe:
        p = (x, y_boden, R_MZ)
        if art == "kiste":
            t.append(q("kiste", (b, h, R_T), punkt(p, (0, g, 0), (0, h * 0.5, 0)), "akte_blau", (0, g, 0), r=(0.012, 1)))
            t.append(flach("kiste_griff", (b * 0.4, 0.03, 0.003), punkt(p, (0, g, 0), (0, h * 0.7, R_T * 0.5 + 0.002)), "grau_dunkel", (0, g, 0)))
        elif art == "folie":
            t.append(q("folie", (b, h, R_T + 0.02), punkt(p, (0, g, 0), (0, h * 0.5, 0)), "folie", (0, g, 0), r=(0.02, 1)))
            t.append(flach("folie_band", (b + 0.004, 0.03, R_T + 0.024), punkt(p, (0, g, 0), (0, h * 0.6, 0)), "tuerkis", (0, g, 0)))
        else:
            band = "tuerkis" if art == "tuerkis" else "band_braun"
            t += paket(p, b, h, R_T, gier=g, band=band, seiten=False, rund=(art != "flach"))
    return t


def buffer_basis():
    t = _staender(0.0, 1.20)
    for x in R_X:
        for z in R_Z:
            t.append(flach("fussplatte", (0.11, 0.01, 0.11), (x, 0.005, z), "stahl_dunkel"))
        t.append(q("anfahrschutz", (0.10, 0.30, 0.05), (x, 0.15, R_Z[1] + 0.06), "warn_gelb", r=(0.012, 1)))
        t.append(flach("anfahrschutz_streifen", (0.102, 0.05, 0.052), (x, 0.18, R_Z[1] + 0.06), "schwarz"))
    t += _ebene(0.14)
    t += palette((R_X[0] + 0.36, 0.187, R_MZ), b=0.56, t=0.44)
    t.append(flach("bodenlinie", (1.56, 0.005, 0.05), (R_MX, 0.0025, -0.36), "warn_gelb"))
    return t


def buffer_a1_0():
    """Ein Fach mit zwei Kartons."""
    t = _ebene(0.62)
    t += _fuellen(0.667, [(-0.66, 0.40, 0.28, "braun", 3), (-0.18, 0.30, 0.22, "tuerkis", -5)])
    return t


def buffer_a1_1():
    """Regal halb: zwei Faecher, einige Kartons, einer auf der Palette."""
    t = _ebene(0.62) + _ebene(1.10)
    t += _fuellen(0.667, [(-0.70, 0.36, 0.30, "braun", 2), (-0.28, 0.34, 0.26, "tuerkis", -4), (0.15, 0.30, 0.20, "braun", 6)])
    t += _fuellen(1.147, [(-0.62, 0.40, 0.26, "braun", -3)])
    t += _fuellen(0.302, [(R_X[0] + 0.36, 0.40, 0.22, "braun", 5)])
    return t


def buffer_a1_2():
    """Regal voll: alle Faecher gefuellt, Kisten, Palette beladen."""
    t = _ebene(0.62) + _ebene(1.10)
    t += _fuellen(0.667, [(-0.74, 0.34, 0.32, "braun", 2), (-0.37, 0.34, 0.26, "tuerkis", -3),
                          (-0.01, 0.30, 0.30, "kiste", 0), (0.25, 0.20, 0.22, "braun", 5)])
    t += _fuellen(1.147, [(-0.72, 0.38, 0.30, "kiste", 0), (-0.32, 0.36, 0.26, "braun", 4), (0.10, 0.40, 0.32, "tuerkis", -2)])
    t += _fuellen(0.302, [(R_X[0] + 0.36, 0.44, 0.24, "braun", 3)])
    t += _fuellen(0.188, [(0.12, 0.40, 0.34, "folie", 0)])
    return t


def buffer_a1_3():
    """Hochregal bis zur Decke: vier Faecher, Leuchtleisten, Rundumleuchte."""
    t = _staender(1.202, 1.16)
    t += _ebene(0.62, licht=True) + _ebene(1.10, licht=True) + _ebene(1.60, licht=True) + _ebene(2.08, licht=True)
    t += _fuellen(0.667, [(-0.74, 0.34, 0.32, "braun", 2), (-0.37, 0.34, 0.26, "tuerkis", -3),
                          (-0.01, 0.30, 0.30, "kiste", 0), (0.25, 0.20, 0.22, "braun", 5)])
    t += _fuellen(1.147, [(-0.72, 0.38, 0.30, "kiste", 0), (-0.32, 0.36, 0.26, "braun", 4), (0.10, 0.40, 0.32, "tuerkis", -2)])
    t += _fuellen(1.647, [(-0.60, 0.62, 0.36, "folie", 0), (-0.02, 0.44, 0.30, "tuerkis", 3)])
    t += _fuellen(2.127, [(-0.74, 0.32, 0.20, "flach", 4), (-0.38, 0.34, 0.18, "kiste", 0), (0.00, 0.34, 0.20, "flach", -4)])
    t += _fuellen(0.302, [(R_X[0] + 0.36, 0.44, 0.24, "braun", 3)])
    t += _fuellen(0.188, [(0.12, 0.40, 0.34, "folie", 0)])
    t += warnlicht((R_X[1], 2.362, R_Z[1]), "tuerkis_licht", hoehe=0.08)
    t.append(flach("schild_oben", (0.50, 0.14, 0.02), (R_MX, 2.30, R_Z[1] + 0.035), "tuerkis"))
    t.append(flach("schild_zahl", (0.30, 0.07, 0.003), (R_MX, 2.30, R_Z[1] + 0.0465), "papier"))
    return t


# Platz 2: Foerdermittel vorn links, Blick/Gabeln nach -z
S_X = -0.60


def buffer_a2_0():
    """Sackkarre mit einem Karton."""
    x = S_X
    t = [flach("schaufel", (0.34, 0.02, 0.20), (x, 0.01, 0.40), "stahl_dunkel")]
    for s in (-1, 1):
        t.append(stab("holm", (x + s * 0.13, 0.03, 0.31), (x + s * 0.13, 1.00, 0.14), 0.016, "rot", seiten=6))
        t.append(walze("rad", 0.09, 0.05, (x + s * 0.20, 0.09, 0.24), "gummi", seiten=10))
        t.append(walze("nabe", 0.035, 0.052, (x + s * 0.20, 0.09, 0.24), "stahl", seiten=6))
    for y, z in ((0.40, 0.25), (0.70, 0.20)):
        t.append(stab("quer", (x - 0.13, y, z), (x + 0.13, y, z), 0.01, "rot", seiten=4))
    t.append(stab("griff", (x - 0.13, 1.00, 0.14), (x + 0.13, 1.00, 0.14), 0.02, "gummi", seiten=6))
    t += paket((x, 0.021, 0.46), 0.30, 0.30, 0.26, gier=2, band="band_braun")
    return t


def _hubwagen_lang(x, z_vorn, laenge, mat="rot"):
    t = []
    z_mitte = z_vorn - 0.06 - laenge * 0.5
    for s in (-1, 1):
        t.append(flach("gabel", (0.10, 0.05, laenge), (x + s * 0.15, 0.045, z_mitte), mat))
        t.append(walze("gabelrad", 0.022, 0.06, (x + s * 0.15, 0.022, z_vorn - 0.06 - laenge + 0.05), "gummi", seiten=6))
    t.append(q("koerper", (0.34, 0.14, 0.12), (x, 0.10, z_vorn - 0.02), mat, r=(0.015, 1)))
    t.append(zylinder("pumpe", 0.035, 0.18, (x, 0.24, z_vorn - 0.01), "stahl", seiten=8, rund=(0, 0)))
    t.append(walze("lenkrad", 0.05, 0.08, (x, 0.05, z_vorn + 0.02), "gummi", seiten=8))
    griff = (x, 0.95, z_vorn + 0.05)
    t.append(stab("deichsel", (x, 0.30, z_vorn - 0.01), griff, 0.018, "stahl_dunkel", seiten=6))
    t.append(ring("griff", 0.07, 0.015, (griff[0], griff[1] + 0.06, griff[2]), "gummi", dreh=(90, 0, 0), segmente=8, quer=3))
    return t


def buffer_a2_1():
    """Hubwagen unter einer Palette mit Karton."""
    x = S_X
    t = _hubwagen_lang(x, 0.92, 0.86)
    t += palette((x, 0.02, 0.40), b=0.60, t=0.70)
    t += paket((x, 0.131, 0.40), 0.40, 0.30, 0.36, gier=6, band="tuerkis")
    return t


def _stapler(x, farbe, gewicht, dach, leuchte, hub=0.0, akku=False):
    t = []
    t.append(q("rumpf", (0.56, 0.34, 0.60), (x, 0.31, 0.55), farbe, r=(0.03, 1)))
    t.append(q("gegengewicht", (0.58, 0.28, 0.16), (x, 0.26, 0.90), gewicht, r=(0.03, 1)))
    t.append(q("sitz", (0.28, 0.08, 0.24), (x, 0.52, 0.66), "gummi", r=(0.02, 1)))
    t.append(q("lehne", (0.28, 0.22, 0.06), (x, 0.66, 0.79), "gummi", r=(0.02, 1)))
    for s in (-1, 1):
        for z in (0.30, 0.84):
            t.append(stab("dachstrebe", (x + s * 0.25, 0.48, z), (x + s * 0.25, 1.12, z), 0.018, "stahl_dunkel", seiten=4))
        t.append(walze("vorderrad", 0.13, 0.10, (x + s * 0.24, 0.13, 0.36), "gummi", seiten=10))
        t.append(walze("hinterrad", 0.10, 0.08, (x + s * 0.25, 0.10, 0.80), "gummi", seiten=8))
        t.append(flach("mast", (0.05, 1.10, 0.06), (x + s * 0.18, 0.57, 0.20), "stahl_dunkel"))
        t.append(flach("gabel", (0.08, 0.04, 0.40), (x + s * 0.12, 0.04 + hub, -0.06), "stahl_dunkel"))
    t.append(flach("mast_quer", (0.42, 0.05, 0.05), (x, 1.10, 0.20), "stahl_dunkel"))
    t.append(flach("gabeltraeger", (0.44, 0.18, 0.04), (x, 0.13 + hub, 0.15), "stahl_dunkel"))
    t.append(q("dach", (0.60, 0.04, 0.64), (x, 1.14, 0.57), dach, r=(0.012, 1)))
    t.append(stab("lenksaeule", (x, 0.48, 0.36), (x, 0.68, 0.46), 0.015, "gummi", seiten=4))
    t.append(ring("lenkrad", 0.07, 0.012, (x, 0.69, 0.47), "gummi", dreh=(60, 0, 0), segmente=8, quer=3))
    t.append(flach("scheinwerfer", (0.10, 0.05, 0.004), (x + 0.20, 0.40, 0.2485), "licht_warm"))
    t += warnlicht((x, 1.16, 0.78), leuchte, hoehe=0.07)
    if akku:
        t.append(flach("akku", (0.004, 0.08, 0.22), (x + 0.282, 0.36, 0.60), "licht_gruen"))
        t.append(flach("streifen", (0.004, 0.04, 0.58), (x + 0.282, 0.22, 0.55), "papier"))
    return t


def buffer_a2_2():
    """Gabelstapler."""
    return _stapler(S_X, "warn_gelb", "stahl_dunkel", "stahl_dunkel", "licht_gelb")


def buffer_a2_3():
    """E-Stapler in Tuerkis, Palette mit Ware auf der gehobenen Gabel."""
    x = S_X
    hub = 0.42
    t = _stapler(x, "tuerkis", "kunststoff", "tuerkis_dunkel", "tuerkis_licht", hub=hub, akku=True)
    t.append(flach("palette_gabel", (0.48, 0.03, 0.42), (x, 0.08 + hub + 0.015, -0.05), "paletten_holz"))
    t += paket((x, 0.111 + hub, -0.05), 0.40, 0.26, 0.36, gier=0, band="tuerkis")
    return t


# Platz 3: Scanner vorn rechts
C_X, C_Z = 0.72, 0.42


def buffer_a3_0():
    """Klemmbrett an einem Pfosten."""
    x, z = C_X, C_Z
    t = [zylinder("pfostenfuss", 0.12, 0.03, (x, 0.015, z), "stahl_dunkel", seiten=10, rund=(0, 0)),
         stab("pfosten", (x, 0.03, z), (x, 1.02, z), 0.022, "warn_gelb", seiten=6)]
    t.append(q("klemmbrett", (0.24, 0.32, 0.015), (x, 0.80, z + 0.035), "holz", r=(0.005, 1)))
    t.append(flach("klemmbrett_blatt", (0.20, 0.25, 0.003), (x, 0.79, z + 0.0445), "papier"))
    t.append(flach("klemme", (0.10, 0.04, 0.012), (x, 0.95, z + 0.048), "stahl"))
    for k in range(3):
        t.append(flach("zeile", (0.14, 0.012, 0.003), (x - 0.01, 0.86 - k * 0.05, z + 0.047), "grau_mittel"))
    t.append(stab("stift", (x + 0.14, 0.72, z + 0.05), (x + 0.15, 0.88, z + 0.05), 0.007, "tuerkis", seiten=4))
    return t


def _pult(x, z, hoehe=0.90):
    return [zylinder("pultfuss", 0.14, 0.03, (x, 0.015, z), "stahl_dunkel", seiten=10, rund=(0, 0)),
            stab("pultsaeule", (x, 0.03, z), (x, hoehe - 0.03, z), 0.03, "stahl", seiten=6),
            q("pultplatte", (0.36, 0.03, 0.28), (x, hoehe, z), "tuerkis_dunkel", (-18, 0, 0), r=(0.008, 1))]


def buffer_a3_1():
    """Handscanner in der Ladeschale auf einem Pult."""
    x, z = C_X, C_Z
    t = _pult(x, z)
    d = (-18, 0, 0)
    p = (x, 0.90, z)
    t.append(q("schale", (0.10, 0.04, 0.16), punkt(p, d, (-0.08, 0.035, 0)), "gummi", d, r=(0.008, 1)))
    t.append(q("scanner", (0.06, 0.06, 0.15), punkt(p, d, (-0.08, 0.085, 0)), "warn_gelb", d, r=(0.015, 1)))
    t.append(flach("scanner_licht", (0.04, 0.03, 0.003), punkt(p, d, (-0.08, 0.085, 0.077)), "licht_rot", d))
    t.append(q("mini_schirm", (0.14, 0.02, 0.10), punkt(p, d, (0.09, 0.025, 0.0)), "schwarz", d, r=(0.005, 1)))
    t += inhalt(punkt(p, d, (0.09, 0.036, 0.0)), verkette(d, (-90, 0, 0)), 0.12, 0.08, "scan")
    return t


def buffer_a3_2():
    """Scanner-Tor mit roter Lichtlinie."""
    t = []
    z = C_Z
    for x in (0.30, 1.00):
        t.append(q("torpfosten", (0.08, 1.30, 0.12), (x, 0.65, z), "stahl", r=(0.012, 1)))
        t.append(flach("torfuss", (0.14, 0.02, 0.24), (x, 0.01, z), "stahl_dunkel"))
    t.append(q("torbalken", (0.82, 0.10, 0.14), (0.65, 1.35, z), "regal_blau", r=(0.015, 1)))
    t.append(flach("scanlinie", (0.60, 0.004, 0.03), (0.65, 1.298, z), "licht_rot"))
    for x in (0.344, 0.956):
        t.append(flach("sensor", (0.004, 0.50, 0.03), (x, 0.70, z), "licht_rot"))
    t.append(q("anzeige", (0.18, 0.13, 0.03), (1.00, 1.05, z + 0.075), "schwarz", r=(0.006, 1)))
    t += inhalt((1.00, 1.05, z + 0.075), (0, 0, 0), 0.15, 0.10, "scan", tiefe=0.016)
    t.append(flach("spur", (0.56, 0.005, 0.30), (0.65, 0.0025, z), "warn_gelb"))
    return t


def buffer_a3_3():
    """Kamera-Tor: Traverse mit drei Kameras, Leuchtstreifen, Bildschirm."""
    t = []
    z = C_Z
    for x in (0.22, 1.02):
        t.append(q("torpfosten", (0.08, 1.62, 0.14), (x, 0.81, z), "kunststoff", r=(0.015, 1)))
        t.append(flach("torfuss", (0.08, 0.02, 0.26), (x, 0.01, z), "stahl_dunkel"))
        s = 1 if x < 0.5 else -1
        t.append(flach("torlicht", (0.004, 1.30, 0.04), (x + s * 0.042, 0.80, z), "tuerkis_licht"))
    for dz in (-0.05, 0.05):
        t.append(flach("traverse", (0.92, 0.05, 0.03), (0.62, 1.65, z + dz), "stahl_dunkel"))
    for k in range(5):
        xa = 0.24 + k * 0.155
        t.append(stab("fachwerk", (xa, 1.63, z), (xa + 0.155, 1.67, z), 0.008, "stahl_dunkel", seiten=3))
    for xk in (0.40, 0.64, 0.88):
        t.append(q("kamera", (0.10, 0.08, 0.12), (xk, 1.58, z), "schwarz", r=(0.012, 1)))
        t.append(zylinder("linse", 0.03, 0.03, (xk, 1.525, z), "tuerkis_licht", seiten=8, rund=(0, 0)))
    t.append(flach("scanfeld", (0.70, 0.005, 0.40), (0.64, 0.0025, z), "tuerkis"))
    t.append(q("tor_schirm", (0.24, 0.18, 0.03), (0.92, 1.25, z + 0.09), "schwarz", r=(0.008, 1)))
    t += inhalt((0.92, 1.25, z + 0.09), (0, 0, 0), 0.21, 0.15, "scan", tiefe=0.016)
    t += warnlicht((1.02, 1.62, z), "licht_gruen", hoehe=0.07)
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
# Station 3: station_processing -- lange Packtischreihe (Basis). Drei
# Personenplaetze hinter dem Tisch, Blick +z zur Kamera:
# Platz 1 x = -0,66, Platz 2 x = 0, Platz 3 x = +0,66. Alles, was ein Platz
# zusaetzlich mitbringt, steht hinter seiner Person (z < -0,45) oder auf
# seinem Tischabschnitt.
# =============================================================================

P_H = 0.46
P_AUF = P_H + 0.001
P_Z0, P_Z1 = 0.0, 0.50
P_PZ = -0.19
P_X = {1: -0.60, 2: 0.0, 3: 0.60}
P_DREH = 45.0   # Reihe liegt quer im Bild: lokal +z zeigt zur Kamera (+1, 0, +1)


def processing_basis():
    t = tischgestell(-0.90, 0.90, P_Z0, P_Z1, P_H, platte="holz_hell", beine=(-0.85, 0.0, 0.85))
    t.append(flach("kante", (1.80, 0.03, 0.006), (0.0, P_H - 0.02, P_Z1 + 0.004), "tuerkis"))
    t.append(flach("ablage", (1.74, 0.025, 0.38), (0.0, 0.13, (P_Z0 + P_Z1) * 0.5), "holz"))
    for x, n in ((-0.50, 3), (0.32, 2)):
        for k in range(n):
            t.append(flach("karton_flach", (0.40, 0.035, 0.30), (x + 0.01 * k, 0.1605 + k * 0.036, 0.26 - 0.008 * k), "karton_hell" if k % 2 else "karton", (0, 3 * k, 0)))
    # Papierrolle vorn an der Tischkante
    for x in (-0.20, 0.20):
        t.append(flach("rollenhalter", (0.02, 0.10, 0.06), (x, P_H - 0.085, P_Z1 + 0.035), "stahl_dunkel"))
    t.append(walze("papierrolle", 0.045, 0.36, (0.0, P_H - 0.11, P_Z1 + 0.05), "papier", seiten=10))
    # Lichtbruecke ueber der Reihe
    bz = -0.52
    for x in (-0.93, 0.93):
        t.append(flach("pfosten", (0.04, 1.56, 0.04), (x, 0.78, bz), "stahl_dunkel"))
        t.append(flach("pfosten_fuss", (0.08, 0.02, 0.12), (x, 0.01, bz), "stahl_dunkel"))
    t.append(q("bruecke", (1.90, 0.05, 0.06), (0.0, 1.58, bz), "stahl_dunkel", r=(0.01, 1)))
    for x in (-0.60, 0.0, 0.60):
        t.append(flach("lampe", (0.30, 0.04, 0.10), (x, 1.535, bz), "tuerkis"))
        t.append(flach("lampe_licht", (0.26, 0.004, 0.07), (x, 1.513, bz), "licht_warm"))
    return t


def _platz_marke(p, mat="warn_gelb"):
    x = P_X[p]
    t = bodenmarke(x, P_PZ, 0.50, 0.40, mat)
    t += fussabdruecke(x, P_PZ + 0.02, "tuerkis" if mat == "warn_gelb" else "papier")
    return t


def _flacher_karton(p, dx=0.0):
    return paket((P_X[p] + dx, P_AUF, 0.27), 0.36, 0.03, 0.28, gier=6, band=None, mat="karton_hell", rund=False)


def _in_haenden(p, mat="karton"):
    return offener_karton((P_X[p], P_AUF, 0.12), 0.34, 0.13, 0.22, mat=mat)


def _abroller(x, z, gier=20.0):
    d = (0, gier, 0)
    p = (x, P_AUF, z)
    return [q("abroller", (0.05, 0.10, 0.20), punkt(p, d, (0, 0.06, 0)), "tuerkis", d, r=(0.01, 1)),
            ring("abroller_band", 0.045, 0.02, punkt(p, d, (0, 0.10, 0.02)), "band_braun", verkette(d, (0, 0, 90)), segmente=6, quer=3),
            q("abroller_griff", (0.03, 0.08, 0.04), punkt(p, d, (0, 0.042, -0.09)), "gummi", d, r=(0, 0))]


def _klebeband(x, z):
    return [ring("klebeband", 0.04, 0.018, (x, P_AUF + 0.018, z), "band_braun", segmente=8, quer=4)]


def processing_a1_0():
    """Leerer Platz: Markierung am Boden, flacher Karton wartet."""
    return _platz_marke(1) + _flacher_karton(1)


PERSON_1 = dict(haar="zopf", haarfarbe="#3A2A22", haut=HAUT[0], weste=WESTE_ORANGE, pulli="#7A6BC4",
                hose="#3F4A66", schuh="#F4F4F1")


def processing_a1_1():
    """Eine Packerin mit offenem Karton, Klebeband."""
    x = P_X[1]
    t = person((x, 0.0, P_PZ), **PERSON_1)
    t += _in_haenden(1)
    t += _klebeband(x - 0.22, 0.38)
    t += paket((x + 0.19, P_AUF, 0.38), 0.18, 0.012, 0.16, gier=-10, band=None, mat="papier", rund=False)
    return t


def _tablet_staender(x, z, gier=25.0):
    d = (0, gier, 0)
    p = (x, P_AUF, z)
    t = [flach("staender", (0.10, 0.012, 0.10), punkt(p, d, (0, 0.006, 0)), "stahl_dunkel", d)]
    m = punkt(p, d, (0, 0.10, 0.0))
    dd = verkette(d, (-28, 0, 0))
    t.append(q("tablet", (0.24, 0.17, 0.014), m, "schwarz", dd, r=(0.006, 1)))
    t += inhalt(m, dd, 0.21, 0.14, "liste", tiefe=0.008)
    return t


def _handscanner(x, z, gier=-30.0):
    d = (0, gier, 0)
    p = (x, P_AUF, z)
    return [q("scanner", (0.05, 0.05, 0.14), punkt(p, d, (0, 0.03, 0)), "warn_gelb", d, r=(0.012, 1)),
            q("scanner_griff", (0.04, 0.03, 0.05), punkt(p, d, (0, 0.02, -0.08)), "gummi", d, r=(0, 0)),
            flach("scanner_licht", (0.03, 0.02, 0.003), punkt(p, d, (0, 0.03, 0.072)), "licht_rot", d)]


def processing_a1_2():
    """Packerin mit Tablet: Auftrag auf dem Staender, Handscanner, Paketstapel."""
    x = P_X[1]
    t = person((x, 0.0, P_PZ), hand="#12B5A5", **PERSON_1)
    t += _in_haenden(1)
    t += _tablet_staender(x - 0.22, 0.36)
    t += _handscanner(x + 0.22, 0.38)
    t += paket((-0.53, 0.0, -0.66), 0.34, 0.24, 0.30, gier=8, band="tuerkis")
    t += paket((-0.53, 0.241, -0.66), 0.26, 0.18, 0.24, gier=-6, band="tuerkis", seiten=False)
    return t


def processing_a1_3():
    """Teamleitung: tuerkise Weste, Headset, Tablet in der Hand, Kennzahl-
    Bildschirm hinter ihr, fertige Pakete am Tischende."""
    x = P_X[1]
    stil = dict(PERSON_1)
    stil.update(weste=WESTE_TUERKIS, pulli="#F4F2EE", extra=("headset",), arme="tablet", nicken=16.0)
    t = person((x, 0.0, P_PZ), **stil)
    h = hand_godot((x, 0.0, P_PZ), 0.0, 1, "tablet")
    m = (x, h[1] + 0.05, h[2] + 0.04)
    dd = (-115, 0, 0)
    t.append(q("tablet", (0.26, 0.18, 0.014), m, "schwarz", dd, r=(0.006, 1)))
    t += inhalt(m, dd, 0.23, 0.15, "kurve", tiefe=0.008)
    t += bodenmarke(x, P_PZ, 0.50, 0.40, "tuerkis")
    # Kennzahl-Bildschirm auf Saeule
    sx, sz = -0.55, -0.72
    t.append(zylinder("saeulenfuss", 0.16, 0.03, (sx, 0.015, sz), "stahl_dunkel", seiten=10, rund=(0, 0)))
    t.append(stab("saeule", (sx, 0.03, sz), (sx, 1.06, sz), 0.03, "stahl", seiten=6))
    d = (0, 20, 0)
    t.append(q("tafel", (0.46, 0.32, 0.04), (sx, 1.22, sz + 0.02), "schwarz", d, r=(0.01, 1)))
    t += inhalt((sx, 1.22, sz + 0.02), d, 0.41, 0.27, "kurve", tiefe=0.021)
    t.append(q("tafel_kappe", (0.46, 0.035, 0.05), (sx, 1.395, sz + 0.02), "tuerkis", d, r=(0.008, 1)))
    t += warnlicht((sx, 1.413, sz + 0.02), "tuerkis_licht", hoehe=0.07)
    # fertige Pakete am linken Tischende
    t += paket((-0.76, P_AUF, 0.33), 0.20, 0.14, 0.20, gier=10, band="tuerkis", seiten=False)
    t += paket((-0.76, P_AUF + 0.141, 0.33), 0.16, 0.10, 0.16, gier=-8, band="tuerkis", seiten=False)
    t.append(flach("klemmbrett", (0.16, 0.008, 0.22), (x + 0.22, P_AUF + 0.004, 0.36), "holz", (0, -12, 0)))
    t.append(flach("blatt", (0.13, 0.003, 0.17), (x + 0.22, P_AUF + 0.0095, 0.37), "papier", (0, -12, 0)))
    return t


PERSON_2 = dict(haar="muetze", haarfarbe="#2E211B", haut=HAUT[1], weste=WESTE_ORANGE, pulli="#77808F",
                hose="#565E4C", schuh="#6E5A48", muetze_farbe="#3E6FA8")


def processing_a2_0():
    """Leerer Platz: Markierung am Boden, flacher Karton wartet."""
    return _platz_marke(2) + _flacher_karton(2)


def processing_a2_1():
    """Ein Packer mit Karton und Klebebandabroller."""
    x = P_X[2]
    t = person((x, 0.0, P_PZ), **PERSON_2)
    t += _in_haenden(2)
    t += _abroller(x + 0.22, 0.36)
    return t


def _hubwagen(x, z_vorn, laenge=0.62, gier=0.0, mat="rot"):
    """Hubwagen, Deichsel vorn bei z_vorn, Gabeln nach -z."""
    t = []
    z_mitte = z_vorn - 0.06 - laenge * 0.5
    for s in (-1, 1):
        t.append(flach("gabel", (0.10, 0.05, laenge), (x + s * 0.15, 0.045, z_mitte), mat))
        t.append(walze("gabelrad", 0.022, 0.06, (x + s * 0.15, 0.022, z_vorn - 0.06 - laenge + 0.05), "gummi", seiten=6))
    t.append(q("koerper", (0.34, 0.14, 0.12), (x, 0.10, z_vorn - 0.02), mat, r=(0.015, 1)))
    t.append(zylinder("pumpe", 0.035, 0.18, (x, 0.24, z_vorn - 0.01), "stahl", seiten=8, rund=(0, 0)))
    t.append(walze("lenkrad", 0.05, 0.08, (x, 0.05, z_vorn + 0.02), "gummi", seiten=8))
    griff = (x, 0.50, z_vorn - 0.42)
    t.append(stab("deichsel", (x, 0.30, z_vorn - 0.01), griff, 0.018, "stahl_dunkel", seiten=6))
    t.append(ring("griff", 0.06, 0.014, (griff[0], griff[1] + 0.05, griff[2] - 0.01), "gummi", dreh=(90, 0, 0), segmente=6, quer=3))
    return t


def processing_a2_2():
    """Packer mit Hubwagen: Palette mit Kartons hinter ihm."""
    x = P_X[2]
    t = person((x, 0.0, P_PZ), **PERSON_2)
    t += _in_haenden(2)
    t += _abroller(x + 0.22, 0.36)
    t += _hubwagen(x, -0.52)
    t.append(flach("palette_last", (0.52, 0.06, 0.50), (x, 0.10, -0.89), "paletten_holz"))
    t += paket((x - 0.11, 0.131, -0.92), 0.24, 0.22, 0.28, gier=4, band="tuerkis")
    t += paket((x + 0.13, 0.131, -0.86), 0.22, 0.16, 0.24, gier=-8, band="tuerkis", seiten=False, rund=False)
    t += paket((x - 0.10, 0.352, -0.92), 0.18, 0.14, 0.20, gier=12, band="band_braun", seiten=False, rund=False)
    return t


def processing_a2_3():
    """Zweiter Packtisch hinter dem Packer: Karton, Luftpolsterrolle, Lampe."""
    x = P_X[2]
    t = person((x, 0.0, P_PZ), **PERSON_2)
    t += _in_haenden(2)
    t += _abroller(x + 0.22, 0.36)
    t += tischgestell(x - 0.31, x + 0.31, -1.12, -0.66, P_H, platte="tuerkis_hell")
    t.append(flach("kante2", (0.62, 0.03, 0.006), (x, P_H - 0.02, -1.124), "tuerkis"))
    t += offener_karton((x - 0.10, P_AUF, -0.88), 0.26, 0.12, 0.20, gier=6)
    t += paket((x + 0.17, P_AUF, -0.92), 0.18, 0.12, 0.18, gier=-10, band="tuerkis", seiten=False, rund=False)
    t += paket((x + 0.17, P_AUF + 0.121, -0.92), 0.14, 0.09, 0.14, gier=8, band="tuerkis", seiten=False, rund=False)
    # Luftpolsterrolle auf einem Halter
    for dx in (-0.14, 0.14):
        t.append(flach("halter", (0.02, 0.30, 0.04), (x + dx, P_H + 0.15, -1.08), "stahl_dunkel"))
    t.append(walze("folienrolle", 0.09, 0.24, (x, P_H + 0.24, -1.05), "folie", seiten=10))
    # Lampe am Tisch
    t.append(stab("lampenarm", (x - 0.26, P_AUF, -1.06), (x - 0.26, 0.95, -1.06), 0.012, "stahl_dunkel", seiten=4))
    t.append(stab("lampenarm", (x - 0.26, 0.95, -1.06), (x - 0.14, 0.92, -0.92), 0.012, "stahl_dunkel", seiten=4))
    t.append(keil("lampenschirm", (0.12, 0.08, 0.12), (x - 0.14, 0.87, -0.92), "tuerkis", dreh=(180, 0, 0)))
    t.append(kugel("lampenlicht", 0.03, (x - 0.14, 0.83, -0.92), "licht_warm", stufen=1))
    return t


PERSON_3A = dict(haar="cap", haarfarbe="#2A1E18", haut=HAUT[2], weste=WESTE_GELB, pulli="#E0664F",
                 hose="#4A6FA5", schuh="#F4F4F1", muetze_farbe="#E0664F")
PERSON_3B = dict(haar="dutt", haarfarbe="#B5562E", haut=HAUT[0], weste=WESTE_ORANGE, pulli="#3F6DB8",
                 hose="#3E4052", schuh="#474B55", hand="#D9A441")
PERSON_3C = dict(haar="locken", haarfarbe="#1E1A18", haut=HAUT[1], weste=WESTE_ORANGE, pulli="#2F3A4F",
                 hose="#3E4052", schuh="#2C2F36", extra=("stirnlampe",))


def processing_a3_0():
    """Leerer Platz: Markierung am Boden, flacher Karton wartet."""
    return _platz_marke(3) + _flacher_karton(3)


def processing_a3_1():
    """Aushilfe: Kappe verkehrt, gelbe Weste, Karton schief, Papierknaeuel."""
    x = P_X[3]
    t = person((x, 0.0, P_PZ), **PERSON_3A)
    t += offener_karton((x, P_AUF, 0.12), 0.34, 0.13, 0.22, gier=-7)
    t.append(kugel("knaeuel", 0.045, (x + 0.22, P_AUF + 0.047, 0.38), "papier", stufen=1))
    t.append(kugel("knaeuel", 0.04, (x - 0.22, P_AUF + 0.042, 0.40), "papier", stufen=1))
    return t


def _paketstapel(x, z, band="tuerkis", n=3):
    t = []
    y = 0.0
    for k, (b, h, tt, g) in enumerate(((0.36, 0.24, 0.30, 4), (0.30, 0.20, 0.26, -6), (0.24, 0.16, 0.20, 10))[:n]):
        t += paket((x, y, z), b, h, tt, gier=g, band=band, seiten=(k == 0))
        y += h + 0.001
    return t


def processing_a3_2():
    """Profi-Packerin: Handschuhe, Abroller, ordentlicher Paketstapel."""
    x = P_X[3]
    t = person((x, 0.0, P_PZ), **PERSON_3B)
    t += _in_haenden(3)
    t += _abroller(x + 0.22, 0.36, gier=-15)
    t += _paketstapel(0.53, -0.66)
    return t


def processing_a3_3():
    """Nachtschicht: Stirnlampe, Arbeitsleuchte auf Stativ, Thermoskanne."""
    x = P_X[3]
    t = person((x, 0.0, P_PZ), **PERSON_3C)
    t += _in_haenden(3)
    t += _abroller(x + 0.22, 0.36, gier=-15)
    t.append(zylinder("thermos", 0.035, 0.18, (x - 0.22, P_AUF + 0.092, 0.38), "tuerkis_dunkel", seiten=8, rund=(0, 0)))
    t.append(zylinder("thermos_deckel", 0.036, 0.04, (x - 0.22, P_AUF + 0.20, 0.38), "stahl", seiten=8, rund=(0, 0)))
    # Arbeitsleuchte auf Dreibein, auf den Tisch gerichtet
    lx, lz, kopf = 0.66, -0.70, 1.16
    for i in range(3):
        w = math.radians(30 + 120 * i)
        t.append(stab("stativbein", (lx, kopf * 0.55, lz), (lx + math.cos(w) * 0.15, 0.0, lz + math.sin(w) * 0.15), 0.013, "stahl_dunkel", seiten=4))
    t.append(stab("stativsaeule", (lx, kopf * 0.5, lz), (lx, kopf, lz), 0.016, "warn_gelb", seiten=6))
    d = (35, -15, 0)
    t.append(q("strahler", (0.26, 0.20, 0.08), punkt((lx, kopf + 0.10, lz), d, (0, 0, 0)), "warn_gelb", d, r=(0.015, 1)))
    t.append(flach("strahler_glas", (0.22, 0.16, 0.004), punkt((lx, kopf + 0.10, lz), d, (0, 0, 0.042)), "licht_warm", d))
    return t


PROCESSING = {
    "basis": gedreht(processing_basis, P_DREH),
    "plaetze": {
        1: {0: gedreht(processing_a1_0, P_DREH), 1: gedreht(processing_a1_1, P_DREH), 2: gedreht(processing_a1_2, P_DREH), 3: gedreht(processing_a1_3, P_DREH)},
        2: {0: gedreht(processing_a2_0, P_DREH), 1: gedreht(processing_a2_1, P_DREH), 2: gedreht(processing_a2_2, P_DREH), 3: gedreht(processing_a2_3, P_DREH)},
        3: {0: gedreht(processing_a3_0, P_DREH), 1: gedreht(processing_a3_1, P_DREH), 2: gedreht(processing_a3_2, P_DREH), 3: gedreht(processing_a3_3, P_DREH)},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": None,
}


import bmesh  # noqa: E402


def bogen(name, mitte, r0, r1, a0, a1, y0, y1, mat, seg=6):
    """Ringsektor als Koerper. Winkel a: Punkt = mitte + r * (-sin a, -cos a)
    in (x, z). Grad."""
    bm = bmesh.new()
    schnitte = []
    for i in range(seg + 1):
        a = math.radians(a0 + (a1 - a0) * i / seg)
        ring4 = []
        for r, y in ((r0, y0), (r1, y0), (r1, y1), (r0, y1)):
            gx, gz = mitte[0] - r * math.sin(a), mitte[1] - r * math.cos(a)
            ring4.append(bm.verts.new((gx, -gz, y)))
        schnitte.append(ring4)
    for i in range(seg):
        a, b = schnitte[i], schnitte[i + 1]
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(list(reversed(schnitte[0])))
    bm.faces.new(schnitte[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = wg._objekt_aus_bmesh(name, bm, mat)
    return obj


# =============================================================================
# Station 4: station_transport -- Bandsegment in der Mitte (Basis), Platz 1
# setzt das Band links fort, Platz 2 treibt es von hinten an, Platz 3
# sortiert am rechten Ende.
# =============================================================================

T_H = 0.55          # Oberkante Gurt
T_B = 0.40          # Bandbreite (Mitte der Seitenwangen)


def band(x0, x1, z=0.0, beine=True, gurt="gummi", akzent="tuerkis"):
    """Gerades Gurtband entlang x."""
    t = []
    L = x1 - x0
    cx = (x0 + x1) * 0.5
    for s in (-1, 1):
        t.append(flach("wange", (L, 0.10, 0.04), (cx, T_H - 0.03, z + s * T_B * 0.5), "stahl_dunkel"))
        t.append(flach("wange_streifen", (L - 0.04, 0.025, 0.003), (cx, T_H - 0.03, z + s * (T_B * 0.5 + 0.0215)), akzent))
    t.append(flach("gurt", (L - 0.01, 0.03, T_B - 0.042), (cx, T_H - 0.015, z), gurt))
    t.append(walze("umlenkung", 0.03, T_B - 0.05, (x0 + 0.035, T_H - 0.035, z), "stahl", achse="z", seiten=6))
    if beine:
        for x in (x0 + 0.07, x1 - 0.07):
            for s in (-1, 1):
                t.append(flach("bein", (0.04, T_H - 0.08, 0.04), (x, (T_H - 0.08) * 0.5, z + s * (T_B * 0.5 - 0.005)), "stahl"))
            t.append(flach("bein_quer", (0.03, 0.03, T_B), (x, 0.14, z), "stahl"))
    return t


def transport_basis():
    t = band(-0.50, 0.50)
    t += paket((-0.22, T_H + 0.001, 0.0), 0.24, 0.16, 0.22, gier=8, band="band_braun")
    t += paket((0.20, T_H + 0.001, 0.0), 0.20, 0.14, 0.18, gier=-12, band="tuerkis", seiten=False)
    # Lichtschranke
    for s in (-1, 1):
        t.append(flach("schranke", (0.03, 0.14, 0.03), (0.40, T_H + 0.09, s * 0.235), "warn_gelb"))
    t.append(flach("schranke_licht", (0.01, 0.01, 0.44), (0.40, T_H + 0.12, 0.0), "licht_rot"))
    return t


def transport_a1_0():
    """Kurze Rollenbahn."""
    t = []
    x0, x1 = -0.85, -0.505
    cx = (x0 + x1) * 0.5
    for s in (-1, 1):
        t.append(flach("wange", (x1 - x0, 0.07, 0.04), (cx, T_H - 0.035, s * T_B * 0.5), "stahl"))
        for x in (x0 + 0.05, x1 - 0.05):
            t.append(flach("bein", (0.04, T_H - 0.07, 0.04), (x, (T_H - 0.07) * 0.5, s * (T_B * 0.5 - 0.005)), "stahl"))
    for k in range(5):
        t.append(walze("rolle", 0.025, T_B - 0.05, (x0 + 0.04 + k * 0.066, T_H - 0.025, 0.0), "stahl_dunkel", achse="z", seiten=6))
    return t


def transport_a1_1():
    """Langes Band links angesetzt."""
    t = band(-1.10, -0.505)
    t += paket((-0.84, T_H + 0.001, 0.02), 0.22, 0.14, 0.20, gier=15, band="band_braun", seiten=False)
    return t


K_MITTE = (-0.505, 0.375)
K_R0, K_R1 = 0.175, 0.575


def _kurve():
    t = []
    rm = (K_R0 + K_R1) * 0.5
    t.append(bogen("kurve_gurt", K_MITTE, K_R0 + 0.022, K_R1 - 0.022, 0, 90, T_H - 0.03, T_H, "gummi", seg=6))
    for r in (K_R0, K_R1):
        t.append(bogen("kurve_wange", K_MITTE, r - 0.02, r + 0.02, 0, 90, T_H - 0.08, T_H + 0.02, "stahl_dunkel", seg=6))
    t.append(bogen("kurve_streifen", K_MITTE, K_R1 + 0.02, K_R1 + 0.023, 5, 85, T_H - 0.045, T_H - 0.015, "tuerkis", seg=5))
    a = math.radians(45)
    for r in (K_R0 + 0.02, K_R1 - 0.02):
        x, z = K_MITTE[0] - r * math.sin(a), K_MITTE[1] - r * math.cos(a)
        t.append(flach("bein", (0.04, T_H - 0.08, 0.04), (x, (T_H - 0.08) * 0.5, z), "stahl"))
    # gerades Stueck Richtung +z
    x = K_MITTE[0] - rm
    z0, z1 = K_MITTE[1] + 0.005, 1.02
    L = z1 - z0
    for s in (-1, 1):
        t.append(flach("wange", (0.04, 0.10, L), (x + s * T_B * 0.5 * 0.99, T_H - 0.03, (z0 + z1) * 0.5), "stahl_dunkel"))
        t.append(flach("bein", (0.04, T_H - 0.08, 0.04), (x + s * (T_B * 0.5 - 0.005), (T_H - 0.08) * 0.5, z1 - 0.08), "stahl"))
    t.append(flach("wange_streifen", (0.003, 0.025, L - 0.04), (x + T_B * 0.5 + 0.0215, T_H - 0.03, (z0 + z1) * 0.5), "tuerkis"))
    t.append(flach("gurt", (T_B - 0.042, 0.03, L - 0.01), (x, T_H - 0.015, (z0 + z1) * 0.5), "gummi"))
    return t, x


def transport_a1_2():
    """Kurve nach vorn mit geradem Anschluss."""
    t, x = _kurve()
    t += paket((x, T_H + 0.001, 0.78), 0.20, 0.14, 0.22, gier=-6, band="band_braun", seiten=False)
    return t


def transport_a1_3():
    """Weiche: Kurve, Schwenkarm, Abzweig nach rechts, Rundumleuchte."""
    t, x = _kurve()
    # Abzweig nach +x
    t += band(x + T_B * 0.5 + 0.025, -0.30, z=0.80, beine=True)
    # Schwenkarm am linken Rand
    px, pz = x + T_B * 0.5 + 0.06, 0.55
    t.append(zylinder("schwenk_saeule", 0.035, 0.22, (px, T_H + 0.02, pz), "stahl_dunkel", seiten=8, rund=(0, 0)))
    t.append(platte("schwenkarm", (px, T_H + 0.07, pz), (x - 0.10, T_H + 0.07, 0.80), 0.03, 0.08, "tuerkis"))
    t.append(flach("schwenk_licht", (0.004, 0.03, 0.30), (px - 0.12, T_H + 0.12, 0.64), "tuerkis_licht", (0, -55, 0)))
    t += warnlicht((px, T_H + 0.13, pz), "licht_gelb", hoehe=0.08)
    t += paket((x, T_H + 0.001, 0.52), 0.20, 0.14, 0.20, gier=8, band="tuerkis", seiten=False)
    t += paket((-0.45, T_H + 0.001, 0.80), 0.18, 0.13, 0.18, gier=-4, band="tuerkis", seiten=False)
    return t


# Platz 2: Antrieb hinter dem Band
def _motor(x, farbe="tuerkis"):
    z = -0.42
    t = [q("motorbock", (0.30, 0.28, 0.22), (x, 0.14, z), "stahl_dunkel", r=(0.015, 1))]
    t.append(walze("motor", 0.09, 0.26, (x, 0.37, z), farbe, seiten=10))
    t.append(walze("motor_deckel", 0.07, 0.03, (x - 0.145, 0.37, z), "stahl", seiten=10))
    for k in range(3):
        t.append(walze("rippe", 0.095, 0.012, (x - 0.06 + k * 0.06, 0.37, z), "stahl_dunkel", seiten=10))
    t.append(q("riemenschutz", (0.06, 0.26, 0.19), (x + 0.12, 0.44, -0.33), "warn_gelb", r=(0.012, 1)))
    t.append(stab("kabel", (x + 0.05, 0.47, z - 0.02), (x + 0.05, 0.02, z - 0.16), 0.01, "gummi", seiten=4))
    return t


def transport_a2_0():
    """Handkurbel an einem Getriebekasten."""
    x, z = 0.25, -0.33
    t = [flach("stuetze", (0.05, 0.36, 0.05), (x, 0.18, z), "stahl")]
    t.append(q("getriebe", (0.16, 0.14, 0.10), (x, 0.43, z), "regal_blau", r=(0.015, 1)))
    t.append(stab("welle", (x, 0.45, z + 0.05), (x, 0.45, -0.232), 0.012, "stahl", seiten=6))
    t.append(stab("welle", (x, 0.43, z - 0.05), (x, 0.43, z - 0.10), 0.012, "stahl", seiten=6))
    t.append(flach("kurbelarm", (0.03, 0.18, 0.02), (x, 0.36, z - 0.11), "stahl_dunkel", (0, 0, 20)))
    t.append(stab("kurbelgriff", (x + 0.03, 0.28, z - 0.11), (x + 0.03, 0.28, z - 0.22), 0.016, "rot", seiten=6))
    return t


def transport_a2_1():
    """Elektromotor mit Riemenschutz."""
    return _motor(0.12)


def transport_a2_2():
    """Zwei Motoren."""
    return _motor(-0.28) + _motor(0.22)


def transport_a2_3():
    """Steuerschrank mit Bildschirm, Tastern, Not-Aus; zwei Motoren."""
    t = _motor(-0.28) + _motor(0.22)
    sx, sz = -0.02, -0.86
    t.append(flach("sockel", (0.66, 0.08, 0.30), (sx, 0.04, sz), "stahl_dunkel"))
    t.append(q("schrank", (0.64, 1.06, 0.28), (sx, 0.61, sz), "kunststoff", r=(0.02, 1)))
    vz = sz + 0.141
    t.append(flach("tuerfuge", (0.004, 0.96, 0.003), (sx + 0.05, 0.61, vz), "grau_mittel"))
    t.append(flach("schirmrahmen", (0.30, 0.22, 0.006), (sx - 0.12, 0.90, vz), "schwarz"))
    t += inhalt((sx - 0.12, 0.90, vz + 0.003), (0, 0, 0), 0.26, 0.18, "liste")
    for k, mat in enumerate(("licht_gruen", "licht_gelb", "tuerkis_licht")):
        t.append(zylinder("taster", 0.025, 0.02, (sx + 0.14 + k * 0.0, 0.98 - k * 0.09, vz + 0.01), mat, seiten=8, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(zylinder("notaus_ring", 0.05, 0.02, (sx - 0.12, 0.60, vz + 0.01), "warn_gelb", seiten=10, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(zylinder("notaus", 0.035, 0.04, (sx - 0.12, 0.60, vz + 0.03), "rot", seiten=10, dreh=(90, 0, 0), rund=(0, 0)))
    t.append(flach("warnschild", (0.12, 0.10, 0.003), (sx + 0.16, 0.40, vz), "warn_gelb", (0, 0, 0)))
    t.append(flach("kabelkanal", (0.10, 0.03, 0.18), (sx, 0.015, sz + 0.24), "stahl"))
    t += warnlicht((sx + 0.2, 1.14, sz), "tuerkis_licht", hoehe=0.08)
    return t


# Platz 3: Sortierung am rechten Ende
def _kiste(x, z, b=0.44, h=0.34, t_=0.44, mat="akte_blau", inhalt_=True):
    t = [flach("kistenboden", (b, 0.03, t_), (x, 0.015, z), mat)]
    for s in (-1, 1):
        t.append(flach("kistenwand", (0.03, h, t_), (x + s * (b * 0.5 - 0.015), h * 0.5, z), mat))
        t.append(flach("kistenwand", (b - 0.06, h, 0.03), (x, h * 0.5, z + s * (t_ * 0.5 - 0.015)), mat))
    if inhalt_:
        t += paket((x - 0.04, 0.03, z + 0.02), 0.22, 0.20, 0.20, gier=20, band="band_braun", seiten=False, rund=False)
        t += paket((x + 0.08, 0.03, z - 0.08), 0.16, 0.26, 0.16, gier=-10, band="tuerkis", seiten=False, rund=False)
    return t


def transport_a3_0():
    """Eine Kiste am Bandende."""
    return _kiste(0.82, 0.0)


def _rutsche(a, b, breite=0.34, mat="stahl"):
    t = [platte("rutsche", a, b, breite, 0.02, mat)]
    dx, dz = b[0] - a[0], b[2] - a[2]
    L = math.hypot(dx, dz)
    nx, nz = -dz / L, dx / L
    for s in (-1, 1):
        o = (nx * s * breite * 0.5, nz * s * breite * 0.5)
        pa = (a[0] + o[0], a[1] + 0.04, a[2] + o[1])
        pb = (b[0] + o[0], b[1] + 0.04, b[2] + o[1])
        t.append(platte("rutsche_rand", pa, pb, 0.02, 0.08, "tuerkis"))
    return t


def transport_a3_1():
    """Rutsche vom Band in eine Kiste."""
    t = _rutsche((0.53, T_H - 0.04, 0.0), (0.93, 0.40, 0.0))
    t.append(stab("rutsche_stuetze", (0.62, 0.02, 0.0), (0.62, 0.47, 0.0), 0.015, "stahl_dunkel", seiten=4))
    t += _kiste(0.86, 0.0, b=0.44, h=0.30, t_=0.44, inhalt_=False)
    t += paket((0.84, 0.03, 0.04), 0.20, 0.16, 0.20, gier=25, band="band_braun", seiten=False, rund=False)
    return t


def transport_a3_2():
    """Sortierweiche: Drehteller, drei Rutschen, drei Behaelter."""
    t = [q("weichentisch", (0.26, 0.05, 0.34), (0.66, T_H - 0.03, 0.0), "stahl_dunkel", r=(0.01, 1))]
    t.append(flach("weichenbein", (0.05, T_H - 0.06, 0.05), (0.66, (T_H - 0.06) * 0.5, 0.0), "stahl"))
    t.append(zylinder("drehteller", 0.13, 0.02, (0.66, T_H + 0.005, 0.0), "tuerkis", seiten=12, rund=(0, 0)))
    t.append(flach("klappe", (0.03, 0.06, 0.22), (0.66, T_H + 0.045, 0.0), "warn_gelb", (0, 35, 0)))
    for z, mat in ((-0.62, "akte_rot"), (0.0, "akte_blau"), (0.62, "akte_gelb")):
        zi = max(-0.12, min(0.12, z))
        t += _rutsche((0.76, T_H - 0.03, zi), (0.90, 0.36, z * 0.85), breite=0.20)
        t += _kiste(0.90, z, b=0.34, h=0.28, t_=0.30, mat=mat, inhalt_=False)
    t += paket((0.90, 0.03, 0.62), 0.16, 0.14, 0.16, gier=12, band="tuerkis", seiten=False, rund=False)
    return t


def transport_a3_3():
    """Sortierroboter mit Paket im Greifer, zwei Rollbehaelter."""
    t = []
    bx = 0.86
    t.append(zylinder("roboter_sockel", 0.16, 0.30, (bx, 0.15, 0.0), "stahl_dunkel", seiten=12, rund=(0.01, 1)))
    t.append(ring("roboter_ring", 0.21, 0.012, (bx, 0.015, 0.0), "tuerkis_licht", segmente=16, quer=3))
    t.append(zylinder("roboter_dreh", 0.12, 0.14, (bx, 0.37, 0.0), "tuerkis", seiten=12, rund=(0.01, 1)))
    schulter, ellbogen, hand = (bx, 0.48, 0.0), (bx - 0.02, 1.05, -0.12), (0.62, 1.00, 0.0)
    t.append(stab("oberarm", schulter, ellbogen, 0.06, "tuerkis", seiten=8))
    t.append(kugel("gelenk", 0.08, ellbogen, "kunststoff", stufen=1))
    t.append(kugel("gelenk", 0.07, schulter, "kunststoff", stufen=1))
    t.append(stab("unterarm", ellbogen, hand, 0.045, "kunststoff", seiten=8))
    t.append(q("greifer", (0.12, 0.06, 0.12), (hand[0], hand[1] - 0.05, hand[2]), "stahl_dunkel", r=(0.01, 1)))
    t.append(zylinder("sauger", 0.04, 0.05, (hand[0], hand[1] - 0.105, hand[2]), "tuerkis_licht", seiten=8, rund=(0, 0)))
    t += paket((hand[0], hand[1] - 0.29, hand[2]), 0.22, 0.16, 0.20, gier=10, band="tuerkis", seiten=False)
    for z in (-0.68, 0.68):
        t += _kiste(0.84, z, b=0.40, h=0.36, t_=0.36, mat="stahl", inhalt_=True)
    t.append(flach("sicherheitslinie", (0.05, 0.005, 1.60), (0.58, 0.0025, 0.0), "warn_gelb"))
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
# Station 5: station_special -- Besprechungstisch in der Mitte (Basis),
# Vertraege links/hinten links (Platz 1), Muster hinten (Platz 2),
# Gaeste vorn und rechts (Platz 3).
# =============================================================================

G_H = 0.74
G_AUF = G_H + 0.001


def special_basis():
    t = [q("tischplatte", (1.10, 0.045, 0.62), (-0.05, G_H - 0.0225, -0.05), "holz", r=(0.015, 1))]
    t.append(flach("tischkante", (1.06, 0.012, 0.003), (-0.05, G_H - 0.022, 0.2715), "tuerkis"))
    for x in (-0.38, 0.28):
        t.append(q("tischwange", (0.06, G_H - 0.06, 0.36), (x, (G_H - 0.045) * 0.5, -0.05), "stahl_dunkel"))
        t.append(flach("tischfuss", (0.09, 0.025, 0.50), (x, 0.0125, -0.05), "stahl_dunkel"))
    t.append(flach("tischlaeufer", (0.18, 0.003, 0.56), (0.18, G_AUF + 0.0015, -0.05), "tuerkis_hell"))
    # Karaffe und Glaeser
    t.append(zylinder("karaffe", 0.05, 0.20, (0.20, G_AUF + 0.10, -0.12), "folie", seiten=10, radius_oben=0.03, rund=(0, 0)))
    t.append(zylinder("wasser", 0.046, 0.08, (0.20, G_AUF + 0.045, -0.12), "hellblau", seiten=10, rund=(0, 0)))
    for x, z in ((0.10, 0.02), (0.30, 0.04)):
        t.append(zylinder("glas", 0.03, 0.09, (x, G_AUF + 0.045, z), "folie", seiten=8, rund=(0, 0)))
    t += pflanze_klein((0.36, G_AUF, -0.26))
    return t


def pflanze_klein(pos):
    x, y, z = pos
    t = [zylinder("topf", 0.06, 0.09, (x, y + 0.045, z), "kunststoff", seiten=8, rund=(0, 0))]
    for i in range(3):
        w = 2 * math.pi * i / 3
        t.append(kugel("blatt", 0.06, (x + math.cos(w) * 0.04, y + 0.13, z + math.sin(w) * 0.04), "pflanze", stufen=1))
    return t


# Platz 1: Vertraege
def _mappe(x, z, gier, mat="akte_blau", y=G_AUF):
    return [q("mappe", (0.24, 0.022, 0.32), (x, y + 0.011, z), mat, (0, gier, 0), r=(0.006, 1)),
            flach("mappe_blatt", (0.20, 0.004, 0.28), (x, y + 0.024, z), "papier", (0, gier + 3, 0))]


def _aktenstapel(x, z, n, y=G_AUF):
    t = []
    farben = ("akte_blau", "akte_rot", "akte_gelb", "papier", "tuerkis")
    for k in range(n):
        t.append(flach("akte", (0.24, 0.035, 0.31), (x, y + 0.0175 + k * 0.036, z), farben[k % 5], (0, (k * 37) % 13 - 6, 0)))
    return t


def special_a1_0():
    """Eine Mappe mit Stift."""
    t = _mappe(-0.33, -0.08, 12)
    t.append(stab("stift", (-0.20, G_AUF + 0.03, 0.05), (-0.12, G_AUF + 0.03, -0.05), 0.006, "gold_metall", seiten=4))
    return t


def special_a1_1():
    """Zwei Aktenstapel."""
    return _aktenstapel(-0.40, -0.12, 5) + _aktenstapel(-0.14, 0.02, 3)


def _aktenschrank(x, z):
    t = [q("schrank", (0.44, 1.00, 0.48), (x, 0.50, z), "stahl", r=(0.02, 1))]
    for k in range(4):
        y = 0.14 + k * 0.235
        t.append(flach("schublade", (0.38, 0.20, 0.004), (x, y, z + 0.242), "kunststoff"))
        t.append(flach("griff", (0.14, 0.02, 0.012), (x, y + 0.05, z + 0.248), "stahl_dunkel"))
        t.append(flach("etikett", (0.08, 0.035, 0.003), (x, y - 0.03, z + 0.2455), ("akte_blau", "akte_rot", "akte_gelb", "tuerkis")[k]))
    t += _aktenstapel(x, z, 3, y=1.001)
    return t


def special_a1_2():
    """Aktenschrank hinten links, Mappe auf dem Tisch."""
    return _aktenschrank(-0.85, -0.78) + _mappe(-0.33, -0.08, 12)


def special_a1_3():
    """Tresor mit Goldbarren, Aktenschrank, Aktenstapel."""
    t = _aktenschrank(-0.85, -0.78)
    x, z = -0.86, -0.02
    t.append(flach("tresor_sockel", (0.48, 0.05, 0.50), (x, 0.025, z), "stahl_dunkel"))
    t.append(q("tresor", (0.46, 0.62, 0.48), (x, 0.36, z), "stahl_dunkel", r=(0.03, 1)))
    t.append(q("tresortuer", (0.04, 0.52, 0.40), (x + 0.24, 0.36, z), "grau_mittel", r=(0.012, 1)))
    t.append(zylinder("tresorrad", 0.07, 0.03, (x + 0.27, 0.40, z), "gold_metall", seiten=10, dreh=(0, 0, 90), rund=(0, 0)))
    for w in (0, 60, 120):
        t.append(flach("speiche", (0.012, 0.18, 0.014), (x + 0.29, 0.40, z), "gold_metall", (w, 0, 0)))
    t.append(flach("tresor_licht", (0.004, 0.02, 0.40), (x + 0.261, 0.64, z), "tuerkis_licht"))
    for k, (dx, dz) in enumerate(((-0.08, -0.08), (0.06, -0.08), (-0.01, 0.06))):
        t.append(keil("barren", (0.14, 0.05, 0.07), (x + dx, 0.695 + 0.025, z + dz), "gold_metall", dreh=(0, 90, 0)))
    t.append(keil("barren", (0.14, 0.05, 0.07), (x - 0.01, 0.745 + 0.025, z - 0.01), "gold_metall", dreh=(0, 90, 0)))
    t += _aktenstapel(-0.40, -0.12, 4) + _mappe(-0.18, 0.04, -6, "tuerkis")
    return t


# Platz 2: Muster hinten
def special_a2_0():
    """Ein Musterkarton."""
    return offener_karton((0.25, 0.0, -0.78), 0.40, 0.30, 0.34, gier=8)


def special_a2_1():
    """Palette mit drei Kartons."""
    t = palette((0.25, 0.0, -0.78), b=0.80, t=0.50)
    t += paket((0.06, 0.111, -0.80), 0.34, 0.28, 0.40, gier=3, band="tuerkis")
    t += paket((0.44, 0.111, -0.78), 0.32, 0.22, 0.36, gier=-5, band="band_braun", seiten=False)
    t += paket((0.08, 0.392, -0.80), 0.26, 0.18, 0.30, gier=10, band="tuerkis", seiten=False)
    return t


def special_a2_2():
    """Zwei Paletten, eine davon in Folie."""
    t = palette((-0.12, 0.0, -0.78), b=0.66, t=0.50)
    t += paket((-0.22, 0.111, -0.80), 0.30, 0.28, 0.40, gier=3, band="tuerkis")
    t += paket((0.06, 0.111, -0.78), 0.22, 0.20, 0.34, gier=-6, band="band_braun", seiten=False)
    t += palette((0.66, 0.0, -0.78), b=0.66, t=0.50)
    t.append(q("folienstapel", (0.60, 0.52, 0.46), (0.66, 0.111 + 0.26, -0.78), "folie", r=(0.03, 1)))
    t.append(flach("folienband", (0.604, 0.05, 0.464), (0.66, 0.111 + 0.32, -0.78), "tuerkis"))
    t.append(flach("folienetikett", (0.16, 0.10, 0.003), (0.66, 0.111 + 0.40, -0.548), "papier"))
    return t


def special_a2_3():
    """Musterwand mit drei beleuchteten Boeden und Leuchtschild."""
    t = []
    wx, wz = 0.28, -0.98
    t.append(q("musterwand", (1.50, 1.80, 0.08), (wx, 0.90, wz), "holz_hell", r=(0.015, 1)))
    t.append(q("schild", (1.50, 0.18, 0.10), (wx, 1.89, wz + 0.01), "tuerkis", r=(0.015, 1)))
    t.append(flach("schild_licht", (1.20, 0.04, 0.003), (wx, 1.89, wz + 0.0615), "papier"))
    farben = ("akte_rot", "tuerkis", "akte_gelb", "lila", "akte_blau", "orange", "gruen_hell", "rosa")
    i = 0
    for y in (0.50, 0.95, 1.40):
        t.append(flach("boden", (1.40, 0.03, 0.24), (wx, y, wz + 0.16), "holz"))
        t.append(flach("boden_licht", (1.30, 0.006, 0.02), (wx, y - 0.018, wz + 0.26), "licht_warm"))
        for k in range(4):
            x = wx - 0.52 + k * 0.35
            mat = farben[i % len(farben)]
            if (i % 3) == 0:
                t.append(zylinder("flasche", 0.05, 0.22, (x, y + 0.125, wz + 0.16), mat, seiten=8, radius_oben=0.03, rund=(0, 0)))
            elif (i % 3) == 1:
                t.append(q("schachtel", (0.18, 0.16, 0.14), (x, y + 0.095, wz + 0.16), mat, (0, 10, 0), r=(0.012, 1)))
            else:
                t.append(kugel("dose", 0.08, (x, y + 0.095, wz + 0.16), mat, stufen=1, skala=(1.0, 0.8, 1.0)))
            i += 1
    for x in (wx - 0.55, wx + 0.55):
        t.append(flach("wandfuss", (0.08, 0.03, 0.40), (x, 0.015, wz + 0.16), "stahl_dunkel"))
    return t


# Platz 3: Gaeste
def _klappstuhl(x, z, gier):
    d = (0, gier, 0)
    p = (x, 0.0, z)
    t = [flach("sitz", (0.36, 0.03, 0.34), punkt(p, d, (0, 0.44, 0)), "tuerkis", d),
         flach("lehne", (0.36, 0.12, 0.02), punkt(p, d, (0, 0.76, -0.19)), "tuerkis", d)]
    for s in (-1, 1):
        t.append(stab("klappbein", punkt(p, d, (s * 0.17, 0.012, 0.16)), punkt(p, d, (s * 0.17, 0.84, -0.20)), 0.012, "stahl", seiten=4))
        t.append(stab("klappbein", punkt(p, d, (s * 0.15, 0.012, -0.18)), punkt(p, d, (s * 0.15, 0.43, 0.10)), 0.012, "stahl", seiten=4))
    return t


def _stuhl(x, z, gier, mat="tuerkis"):
    d = (0, gier, 0)
    p = (x, 0.0, z)
    t = [q("sitz", (0.40, 0.05, 0.38), punkt(p, d, (0, 0.45, 0)), mat, d, r=(0.015, 1)),
         q("lehne", (0.40, 0.30, 0.04), punkt(p, d, (0, 0.72, -0.18)), mat, d, r=(0.012, 1))]
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(stab("stuhlbein", punkt(p, d, (sx * 0.17, 0.43, sz * 0.16)), punkt(p, d, (sx * 0.18, 0.0, sz * 0.17)), 0.012, "stahl_dunkel", seiten=4))
    return t


def _sessel(x, z, gier, breite=0.62, kissen=1, mat="leder", akzent="tuerkis"):
    d = (0, gier, 0)
    p = (x, 0.0, z)
    t = [q("sockel", (breite, 0.22, 0.58), punkt(p, d, (0, 0.15, 0)), mat, d, r=(0.03, 1)),
         q("ruecken", (breite, 0.40, 0.14), punkt(p, d, (0, 0.46, -0.22)), mat, d, r=(0.04, 1))]
    for s in (-1, 1):
        t.append(q("armlehne", (0.12, 0.20, 0.58), punkt(p, d, (s * (breite * 0.5 - 0.06), 0.36, 0)), "leder_dunkel", d, r=(0.03, 1)))
    innen = breite - 0.26
    for k in range(kissen):
        kb = innen / kissen
        kx = -innen * 0.5 + kb * (k + 0.5)
        t.append(q("kissen", (kb - 0.01, 0.09, 0.42), punkt(p, d, (kx, 0.305, 0.04)), mat, d, r=(0.03, 1)))
    t.append(q("zierkissen", (0.20, 0.18, 0.07), punkt(p, d, (-innen * 0.25, 0.46, -0.12)), akzent, verkette(d, (-15, 0, 8)), r=(0.03, 1)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(flach("sesselfuss", (0.05, 0.04, 0.05), punkt(p, d, (sx * (breite * 0.5 - 0.06), 0.02, sz * 0.23)), "holz_dunkel", d))
    return t


def special_a3_0():
    """Ein Klappstuhl."""
    return _klappstuhl(-0.05, 0.60, 180)


def special_a3_1():
    """Drei Stuehle."""
    return _stuhl(-0.32, 0.60, 180) + _stuhl(0.25, 0.60, 180, "akte_gelb") + _stuhl(0.80, -0.05, -90)


def special_a3_2():
    """Zwei Ledersessel vorn, ein dritter rechts."""
    return _sessel(-0.30, 0.72, 180) + _sessel(0.40, 0.72, 180) + _sessel(0.80, -0.08, -90, breite=0.56)


def special_a3_3():
    """Lounge: Sofa, Sessel, Beistelltisch mit Lampe, grosse Pflanze."""
    t = _sessel(-0.08, 0.73, 180, breite=1.24, kissen=2)
    t += _sessel(0.80, -0.08, -90, breite=0.56, akzent="akte_gelb")
    bx, bz = 0.86, 0.46
    t.append(zylinder("beistell_platte", 0.14, 0.03, (bx, 0.50, bz), "holz", seiten=10, rund=(0.008, 1)))
    t.append(stab("beistell_fuss", (bx, 0.0, bz), (bx, 0.485, bz), 0.02, "gold_metall", seiten=6))
    t.append(zylinder("lampenfuss", 0.03, 0.12, (bx + 0.03, 0.575, bz - 0.03), "gold_metall", seiten=6, rund=(0, 0)))
    t.append(kugel("lampe", 0.07, (bx + 0.03, 0.70, bz - 0.03), "licht_warm", stufen=1))
    t.append(zylinder("glas", 0.025, 0.08, (bx - 0.06, 0.555, bz + 0.05), "tuerkis_hell", seiten=6, rund=(0, 0)))
    t += pflanze_gross((0.88, 0.0, 0.88), g=0.9)
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


# =============================================================================
# Bauen, Pruefen, Exportieren
# =============================================================================

STATIONEN = {}
for _name, _daten in (("intake", "INTAKE"), ("buffer", "BUFFER"), ("processing", "PROCESSING"),
                      ("transport", "TRANSPORT"), ("special", "SPECIAL")):
    if _daten in globals():
        STATIONEN[_name] = globals()[_daten]
wg.STATIONEN = STATIONEN


_alt_liegt_innen = wg._liegt_innen


def _ort_melden(obj, baum):
    """Wie _liegt_innen, meldet bei Ueberschneidung aber den Ort (Godot)."""
    return _alt_liegt_innen(obj, baum)


_alt_bvh_overlap = None


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


def dreiecke_je_datei(station):
    """{(platz, stufe): Dreiecke} -- jede Datei einzeln gebaut."""
    zahlen = {}
    for name, bauen, platz, stufe in wg.alle_dateien(station):
        wg.alles_loeschen()
        obj = wg.zusammenfuegen(bauen(), name)
        zahlen[(platz, stufe)] = wg.dreiecke(obj)
    return zahlen


def budget_pruefen(station):
    zahlen = dreiecke_je_datei(station)
    basis = zahlen[(0, 0)]
    teuerste = {}
    for (platz, stufe), n in zahlen.items():
        if platz:
            teuerste[platz] = max(teuerste.get(platz, 0), n)
    voll = basis + sum(teuerste.values())
    alle_m3 = basis + sum(zahlen.get((p, 3), 0) for p in (1, 2, 3))
    status = "ok" if voll <= BUDGET_GESAMT else "UEBER BUDGET"
    print("  Budget %s: Basis %d + Plaetze %s = %d (alle m3: %d) / %d  %s"
          % (station, basis, [teuerste[p] for p in sorted(teuerste)], voll, alle_m3, BUDGET_GESAMT, status))
    return voll, zahlen


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


def fluss_teil():
    """Kleines Paket mit tuerkisem Klebeband, Ursprung in der Mitte."""
    wg.alles_loeschen()
    b, h, t = 0.30, 0.20, 0.24
    teile = [kasten("paket", (b, h, t), (0, 0, 0), "karton", rund=(0.02, 2))]
    teile.append(flach("band", (b - 0.03, 0.004, 0.06), (0, h * 0.5 + 0.002, 0), "tuerkis"))
    teile.append(flach("band", (0.06, 0.004, t - 0.03), (0, h * 0.5 + 0.0025, 0), "tuerkis"))
    for s in (-1, 1):
        teile.append(flach("band", (0.004, h * 0.6, 0.06), (s * (b * 0.5 + 0.002), h * 0.18, 0), "tuerkis"))
        teile.append(flach("band", (0.06, h * 0.6, 0.004), (0, h * 0.18, s * (t * 0.5 + 0.002)), "tuerkis"))
    teile.append(flach("etikett", (0.10, 0.07, 0.004), (0.07, -0.02, t * 0.5 + 0.003), "papier"))
    teile.append(flach("strich", (0.07, 0.012, 0.004), (0.07, -0.005, t * 0.5 + 0.005), "grau_dunkel"))
    obj = wg.zusammenfuegen(teile, "fluss_teil")
    wg.exportieren(obj, AUSGABE_FLUSS)
    g = wg.grenzen(obj)
    print("  fluss_teil: %d Dreiecke, Masse %.2f x %.2f x %.2f" % (wg.dreiecke(obj), g[1] - g[0], g[3] - g[2], g[5] - g[4]))


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

# Blick-Azimut je (station, platz); 0 = Basis-Symbol. 0 Grad = von vorn (+z).
sy.AZIMUT = {
    ("intake", 0): 35, ("intake", 1): 20, ("intake", 2): 70, ("intake", 3): 30,
    ("buffer", 0): 35, ("buffer", 1): 25, ("buffer", 2): 50, ("buffer", 3): 30,
    ("processing", 0): 60, ("processing", 1): 55, ("processing", 2): 55, ("processing", 3): 55,
    ("transport", 0): 35, ("transport", 1): 40, ("transport", 2): 30, ("transport", 3): 30,
    ("special", 0): 35, ("special", 1): 30, ("special", 2): 30, ("special", 3): 25,
}
sy.MOTIVE = globals().get("SYMBOL_MOTIVE", {})


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


def vorschau_stufen(station, groesse=760):
    """2 x 2: alle Plaetze auf m0, m1, m2, m3 -- Spielwinkel aus (+1,+1,+1)."""
    os.makedirs(VORSCHAU, exist_ok=True)
    kacheln = []
    for m in range(4):
        wg.alles_loeschen()
        wg.licht_und_welt()
        for name, bauen, platz, stufe in wg.alle_dateien(station):
            if platz == 0 or stufe == m:
                wg.zusammenfuegen(bauen(), name)
        wg._umgebung(station, Vector((0, 0, 0)))
        wg._beschriftung("m%d" % m, Vector((1.25, -1.25, -0.75)), groesse=0.22)
        wg._kamera_iso((0.0, 0.0, 0.85), 3.5, (groesse, groesse))
        pfad = os.path.join(VORSCHAU, "_tmp_%s_%d.png" % (station, m))
        bpy.context.scene.render.filepath = pfad
        bpy.ops.render.render(write_still=True)
        kacheln.append(_png_lesen(pfad))
        os.remove(pfad)
    oben = np.concatenate([kacheln[2], kacheln[3]], axis=1)   # Blender-Zeilen laufen von unten
    unten = np.concatenate([kacheln[0], kacheln[1]], axis=1)
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
            "kein_export": "--kein_export" in args, "nur": nur, "streifen": "--streifen" in args}


def main():
    a = argumente()
    print("")
    print("=== STATIONEN BUERO (N31) ===")
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
        budgets[station], _ = budget_pruefen(station)
        if not a["kein_export"]:
            altmodelle(station)
        if a["vorschau"]:
            vorschau_stufen(station)
        if a["streifen"]:
            wg.vorschau_station(station)
        if a["symbole"]:
            os.makedirs(AUSGABE_UI, exist_ok=True)
            sy.symbole_station(station)
    if a["symbole"]:
        sy.kontaktbogen(list(STATIONEN))
    if not a["kein_export"] and not a["nur"]:
        fluss_teil()
    print("")
    for s, n in budgets.items():
        print("  %-12s volle Ausstattung %5d Dreiecke%s" % (s, n, "" if n <= BUDGET_GESAMT else "  !! ueber Budget"))
    print("  Probleme gesamt: %d" % probleme)


if __name__ == "__main__":
    main()
