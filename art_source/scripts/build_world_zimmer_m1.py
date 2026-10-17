"""M1 (D1_ART_DIRECTION, Paket M) -- Aussenbereich und Landmarken fuer Welt 1 "zimmer".

Aufruf:
    blender --background --python art_source/scripts/build_world_zimmer_m1.py

Erzeugt nach project/assets/world/zimmer/ (einrichtung_garten wird mit neuen
Sperrflaechen neu gebaut, der Rest ist neu):
    welt_strasse      Gehweg, Strasse mit Mittellinie, Hecke mit Tor, Trampelpfad zum Eingang,
                      Strassenlaterne (leuchtet), Briefkastenanlage
    welt_fahrraeder   Fahrradstaender mit zwei Raedern (Vorgarten)
    welt_tonnen       Muelltonnen-Trio (blau, gelb, braun)
    welt_auto_klein   zwei geparkte Autos auf der Strasse
    welt_balkon_deko  Satellitenschuessel + Antenne am Balkon-Gelaender
    welt_laeufer      Laeufer-Teppich im Flur (rot-creme, blaue Streifen)

Alles in GODOT-Koordinaten (x rechts, y oben, z zum Betrachter), Ursprung der
Dateien = Weltnullpunkt (Kulisse x 0, z 0, Drehung 0). Rasen-Oberkante y = -0,45.
Farben als sRGB-Hex (Bau.farbe() rechnet linear = s^2,2 zurueck).
"""

import math
import os
import random
import sys
import time

import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_einrichtung_wg_b as wb  # noqa: E402

Y0 = wb.GARTEN_Y + 0.02   # Rasen-Oberkante

wb.PALETTE.update({
    # Strasse und Gehweg
    "m1_asphalt": "#4D5058", "m1_asphalt_hell": "#5A5E67", "m1_linie": "#EDE7D6",
    "m1_gehweg": "#C9C1B2", "m1_gehweg_fuge": "#A9A193", "m1_bordstein": "#B5AEA2",
    "m1_pfad": "#CDB892", "m1_pfad_dunkel": "#BBA57C",
    # Hecke
    "m1_hecke_a": "#4E9A47", "m1_hecke_b": "#3F8541", "m1_hecke_c": "#62AE4E",
    # Tonnen
    "m1_tonne_grau": "#5F646C", "m1_tonne_blau": "#3C7BC4", "m1_tonne_gelb": "#EBC534",
    "m1_tonne_braun": "#7B5238",
    # Fahrraeder
    "m1_rad_gelb": "#E8B431", "m1_rad_petrol": "#2F8E92", "m1_reifen": "#25262B",
    # Autos
    "m1_auto_rot": "#C94E3B", "m1_auto_petrol": "#3E8C94", "m1_glas_dunkel": "#38465A",
    "m1_rucklicht": "#FF4B3A", "m1_chrom": "#C9CDD3",
    # Briefkasten / Laterne / Schuessel
    "m1_briefkasten": "#59616C", "m1_gelb_post": "#F2C230", "m1_schuessel": "#E9E6DF",
    "m1_mast": "#4B4F57",
    # Laeufer
    "m1_laeufer_rot": "#B4483B", "m1_laeufer_creme": "#EFE0C2", "m1_laeufer_blau": "#3F6FD8",
})
wb.LEUCHTEND.update({"m1_rucklicht": 1.6})
wb.RAUHEIT.update({"m1_auto_rot": 0.45, "m1_auto_petrol": 0.45, "m1_chrom": 0.3, "m1_glas_dunkel": 0.2})

Bau = wb.Bau


# ------------------------------------------------------------------ Bausteine

def rad_rund(b, x, y, z, r, mat="m1_reifen", dicke=0.03, rohr_r=0.022):
    pts = []
    for k in range(14):
        a = 2 * math.pi * k / 14
        pts.append((x + r * math.cos(a), y + r * math.sin(a), z))
    b.rohr(mat, pts, rohr_r, seg=5, geschlossen=True)
    b.rohr("metall", [(x - r, y, z), (x + r, y, z)], 0.005, seg=3)
    b.rohr("metall", [(x, y - r, z), (x, y + r, z)], 0.005, seg=3)


def velo(b, mat_rahmen, x=0.0, z=0.0, ry=0.0):
    """Fahrrad entlang x, Vorderrad bei +x."""
    with b.an(x=x, z=z, ry=ry):
        for wx in (-0.52, 0.52):
            rad_rund(b, wx, 0.34, 0.0, 0.33)
        rahmen = [((-0.52, 0.34, 0), (0.0, 0.30, 0)), ((0.0, 0.30, 0), (-0.2, 0.70, 0)),
                  ((-0.2, 0.70, 0), (-0.52, 0.34, 0)), ((-0.2, 0.70, 0), (0.36, 0.68, 0)),
                  ((0.0, 0.30, 0), (0.36, 0.68, 0)), ((0.36, 0.68, 0), (0.52, 0.34, 0))]
        for a, c in rahmen:
            b.rohr(mat_rahmen, [a, c], 0.017, seg=5)
        b.rohr("metall", [(0.36, 0.68, 0), (0.33, 0.9, 0)], 0.014, seg=4)
        b.rohr("schwarz", [(0.33, 0.9, -0.22), (0.33, 0.9, 0.22)], 0.014, seg=4)
        b.kasten("schwarz", 0.22, 0.045, 0.1, x=-0.22, y=0.72, r=0.015)
        b.zylinder("metall", 0.012, 0.18, x=-0.2, y=0.7, seg=4)
        b.kasten("metall", 0.06, 0.02, 0.07, x=0.0, y=0.17, z=0.1, r=0.005)  # Pedal


def fahrradstaender(b, x, z, ry=0.0):
    with b.an(x=x, z=z, ry=ry):
        for i in range(4):
            zz = -0.9 + i * 0.6
            b.rohr("metall", [(0, 0, zz - 0.15), (0, 0.55, zz - 0.15), (0, 0.78, zz), (0, 0.55, zz + 0.15),
                              (0, 0, zz + 0.15)], 0.02, seg=5)
        b.kasten("m1_gehweg", 0.5, 0.03, 2.2, y=0.0, r=0.01)
        velo(b, "m1_rad_gelb", x=0.0, z=-0.6, ry=90)
        velo(b, "m1_rad_petrol", x=0.0, z=0.0, ry=90)


def tonne(b, x, z, deckel, ry=0.0):
    with b.an(x=x, z=z, ry=ry):
        b.kasten("m1_tonne_grau", 0.55, 0.88, 0.62, y=0.10, r=0.06, seg=2)
        b.kasten(deckel, 0.6, 0.07, 0.68, y=0.96, r=0.03, seg=2)
        b.kasten("schwarz", 0.3, 0.04, 0.05, y=1.0, z=0.3, r=0.01)
        b.zylinder("m1_reifen", 0.09, 0.06, x=-0.2, y=0.0, z=-0.28, seg=8, rx=90)
        b.zylinder("m1_reifen", 0.09, 0.06, x=0.2, y=0.0, z=-0.28, seg=8, rx=90)
        b.kasten("weiss", 0.28, 0.2, 0.01, y=0.5, z=0.32, r=0.005)   # Aufkleber


def auto(b, farbe, x, z, ry=0.0):
    with b.an(x=x, z=z, ry=ry):
        b.kasten(farbe, 3.5, 0.55, 1.62, y=0.28, r=0.13, seg=2)
        b.kasten(farbe, 1.95, 0.52, 1.5, x=-0.1, y=0.78, r=0.15, seg=2)
        b.kasten("m1_glas_dunkel", 1.99, 0.34, 1.52, x=-0.1, y=0.88, r=0.08, seg=1)
        b.kasten(farbe, 1.7, 0.05, 1.4, x=-0.1, y=1.28, r=0.02)
        for sx in (-1.1, 1.0):
            for sz in (-0.78, 0.78):
                b.zylinder("m1_reifen", 0.31, 0.22, x=sx, y=0.31, z=sz, seg=10, rx=90)
                b.zylinder("m1_chrom", 0.17, 0.225, x=sx, y=0.31, z=sz, seg=8, rx=90)
        for sz in (-0.6, 0.6):
            b.kasten("licht_lampe", 0.05, 0.12, 0.28, x=1.76, y=0.52, z=sz, r=0.01)
            b.kasten("m1_rucklicht", 0.05, 0.1, 0.3, x=-1.76, y=0.52, z=sz, r=0.01)
        b.kasten("m1_chrom", 0.05, 0.1, 0.5, x=1.77, y=0.3, r=0.01)


def laterne(b, x, z, h=3.7):
    with b.an(x=x, z=z):
        b.zylinder("m1_mast", 0.09, h, seg=8, rad_oben=0.06)
        b.rohr("m1_mast", [(0, h, 0), (0, h + 0.2, 0), (0.55, h + 0.28, 0)], 0.04, seg=5)
        b.kasten("m1_mast", 0.5, 0.1, 0.26, x=0.65, y=h + 0.2, r=0.03)
        b.kasten("licht_lampe", 0.42, 0.03, 0.2, x=0.65, y=h + 0.18, r=0.01)


def hecke(b, x0, x1, z, rng):
    x = x0
    i = 0
    while x < x1:
        l = min(1.3, x1 - x)
        h = rng.uniform(0.7, 0.9)
        b.kasten(("m1_hecke_a", "m1_hecke_b", "m1_hecke_c")[i % 3], l + 0.05, h, 0.7, x=x + l / 2, z=z, r=0.22, seg=2)
        x += l
        i += 1


def briefkaesten(b, x, z, ry=0.0):
    with b.an(x=x, z=z, ry=ry):
        for sx in (-0.5, 0.5):
            b.kasten("m1_mast", 0.07, 0.95, 0.07, x=sx, r=0.01)
        for i in range(3):
            xx = -0.38 + i * 0.38
            b.kasten("m1_briefkasten", 0.34, 0.3, 0.2, x=xx, y=0.95, r=0.02)
            b.kasten("schwarz", 0.2, 0.015, 0.01, x=xx, y=1.17, z=0.105)
            b.kasten("weiss", 0.2, 0.06, 0.01, x=xx, y=1.04, z=0.105)
        b.kasten("m1_gelb_post", 0.34, 0.3, 0.2, x=0.0, y=1.3, r=0.02)


# -------------------------------------------------------------------- Objekte

def strasse(b):
    rng = random.Random(77)
    with b.an(y=Y0):
        # Gehweg
        b.kasten("m1_gehweg", 44.0, 0.07, 1.3, x=0.0, y=-0.02, z=11.95, r=0.02)
        for i in range(-21, 22):
            b.kasten("m1_gehweg_fuge", 0.03, 0.002, 1.3, x=i * 1.0 + 0.5, y=0.049, z=11.95, r=0.0)
        b.kasten("m1_bordstein", 44.0, 0.12, 0.22, x=0.0, y=-0.06, z=12.72, r=0.03)
        # Strasse (Asphaltflaeche, flacher als der Gehweg)
        b.kasten("m1_asphalt", 44.0, 0.04, 5.0, x=0.0, y=-0.1, z=15.3, r=0.01)
        for i in range(-9, 10):
            b.kasten("m1_linie", 1.3, 0.004, 0.14, x=i * 2.4, y=-0.058, z=15.3, r=0.0)
        b.kasten("m1_gehweg", 44.0, 0.04, 0.4, x=0.0, y=-0.1, z=18.1, r=0.01)
        # Hecke mit Tor (Lücke bei x = 13.6 .. 15.6)
        hecke(b, -16.0, 13.4, 10.9, rng)
        hecke(b, 15.8, 17.0, 10.9, rng)
        # Trampelpfad: von der Wohnungstuer ostwaerts und dann sued zum Tor
        for z in [-1.0 + i * 0.55 for i in range(0, 25)]:
            with b.an(x=14.6 + rng.uniform(-0.12, 0.12), z=z, ry=rng.uniform(0, 30)):
                b.kasten("m1_pfad" if int(z * 10) % 2 else "m1_pfad_dunkel", rng.uniform(1.0, 1.25), 0.025,
                         rng.uniform(0.5, 0.62), y=0.0, r=0.01)
        for x in [12.4 + i * 0.5 for i in range(0, 5)]:
            with b.an(x=x, z=-1.0 + rng.uniform(-0.1, 0.1), ry=rng.uniform(0, 30)):
                b.kasten("m1_pfad_dunkel", 0.6, 0.025, 0.7, y=0.0, r=0.01)
        # Tor-Pfosten
        for px in (13.4, 15.8):
            b.kasten("m1_mast", 0.12, 1.1, 0.12, x=px, z=10.9, r=0.015)
        # Strassenlaterne auf dem Gehweg
        laterne(b, 1.5, 12.0)
        laterne(b, -12.5, 12.0)
        briefkaesten(b, 16.4, 10.0, ry=-90)
        # Baum auf dem Gehweg
        with b.an(x=-7.5, z=12.0):
            b.kasten("m1_gehweg_fuge", 1.0, 0.04, 1.0, y=0.0, r=0.02)
            b.zylinder("stamm", 0.1, 1.9, y=0.0, seg=7, rad_oben=0.07)
            b.kugel("m1_hecke_a", 1.0, y=2.5, sy=0.9, fein=2)
            b.kugel("m1_hecke_c", 0.7, x=0.5, y=2.2, z=0.2, sy=0.85, fein=2)


def fahrraeder(b):
    with b.an(y=Y0):
        fahrradstaender(b, 8.2, 9.2, ry=-90)


def tonnen(b):
    with b.an(y=Y0):
        for i, c in enumerate(("m1_tonne_blau", "m1_tonne_gelb", "m1_tonne_braun")):
            tonne(b, 11.0 + i * 0.72, 9.6, c)


def autos(b):
    with b.an(y=Y0 - 0.06):
        auto(b, "m1_auto_rot", -4.5, 14.4)
        auto(b, "m1_auto_petrol", 8.5, 16.3, ry=180)


def balkon_deko(b):
    # am rechten Balkon-Gelaender (x = 11.5), aussen
    with b.an(x=11.85, z=-5.5):
        b.kasten("m1_mast", 0.06, 1.4, 0.06, y=0.0, r=0.01)
        b.kasten("m1_mast", 0.35, 0.05, 0.05, y=1.1, x=-0.15, r=0.01)
        with b.an(x=0.1, y=1.45, ry=0):
            b.kugel("m1_schuessel", 0.34, sx=0.35, sy=1.0, sz=1.0, rz=0.0, fein=2)
            b.rohr("m1_mast", [(0.04, 0, 0), (0.45, 0.0, 0.0)], 0.012, seg=4)
            b.kugel("m1_mast", 0.05, x=0.47, fein=1)
        # Antenne
        b.kasten("m1_mast", 0.04, 1.0, 0.04, x=-0.2, y=1.1, z=0.25, r=0.01)
        for i in range(4):
            b.kasten("m1_mast", 0.02, 0.02, 0.5 - i * 0.08, x=-0.2, y=1.4 + i * 0.18, z=0.25, r=0.003)


def laeufer(b):
    with b.an(y=0.0):
        b.kasten("m1_laeufer_creme", 20.8, 0.010, 1.5, z=-1.5)
        b.kasten("m1_laeufer_rot", 20.6, 0.014, 1.3, z=-1.5)
        for dz in (-0.42, 0.42):
            b.kasten("m1_laeufer_blau", 20.5, 0.018, 0.09, z=-1.5 + dz)
        for dz in (-0.3, 0.3):
            b.kasten("m1_laeufer_creme", 20.5, 0.018, 0.02, z=-1.5 + dz)
        for sx in (-1, 1):
            for k in range(8):
                b.kasten("m1_laeufer_creme", 0.18, 0.006, 0.02, x=sx * 10.5, z=-2.15 + k * 0.18)


def garten(b):
    wb.einrichtung_garten(b)


ASSETS = {
    "welt_strasse": strasse,
    "welt_fahrraeder": fahrraeder,
    "welt_tonnen": tonnen,
    "welt_auto_klein": autos,
    "welt_balkon_deko": balkon_deko,
    "welt_laeufer": laeufer,
    "einrichtung_garten": garten,
}


def sperrflaechen():
    """Was der Garten frei lassen soll: Pfad, Hecke, Fahrradstaender, Tonnen, Briefkaesten."""
    f = []
    for z in range(-2, 11):
        f.append((14.6, float(z), 0.95))
    for x in range(12, 17):
        f.append((float(x), -1.0, 0.8))
    for x in range(-17, 18):
        f.append((float(x), 10.9, 0.95))
    f += [(8.2, 9.2, 1.5), (8.2, 8.2, 1.2), (8.2, 10.2, 1.2), (11.8, 9.6, 1.4), (12.6, 9.6, 0.9),
          (16.4, 10.0, 0.9), (12.0, -5.5, 1.0)]
    return f


def main():
    wb.ZUSATZ_BELEGT[:] = sperrflaechen()
    print("")
    print("=== M1 AUSSEN WELT 1 ===")
    auswahl = [a for a in (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) if not a.startswith("--")]
    for name, bauen in ASSETS.items():
        if auswahl and name not in auswahl:
            continue
        for versuch in range(4):
            try:
                wb.alles_loeschen()
                b = Bau()
                bauen(b)
                obj = b.objekt(name)
                pfad = os.path.join(wb.AUSGABE, name + ".glb")
                wb.exportieren(obj, pfad)
                break
            except OSError as e:  # Errno 22 solange Godot parallel importiert
                print("  Export-Fehler %s, Wiederholung %d" % (e, versuch + 1))
                time.sleep(2.0)
        print("  %-22s %6d Dreiecke  %2d Mat  %6.1f KB"
              % (name, wb.dreiecke_von(obj), len(obj.data.materials), os.path.getsize(pfad) / 1024.0))


if __name__ == "__main__":
    main()
