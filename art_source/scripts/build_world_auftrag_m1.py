"""M1 (D1_ART_DIRECTION, Paket M) -- Landmarken fuer Welt 2 "auftrag" (Das Studio).

Aufruf:
    blender --background --python art_source/scripts/build_world_auftrag_m1.py

Erzeugt nach project/assets/world/auftrag/ (Ursprung = Kulisse-Position x, z auf
Hofniveau, y bereits eingerechnet):
    welt_rolltor      Hofmauer mit halb hochgerolltem, schiefem Rolltor und Graffiti
                      (Story: "das klemmt"), Lampe darueber. Vorderseite lokal +z.
    welt_kastenwagen  alter weisser Kastenwagen mit Beule, Nase nach +x
    welt_neonschild   Mast mit "ON AIR"-Leuchtschild (Neon pink, leuchtet)
    welt_hofleuchte   Hoflampe mit warmem Licht
Der Akzent Pink kommt in dieser Welt nur als Licht vor (Neon, Kabel), nie als Lack.
Farben sRGB-Hex; farbe() in build_room_wg.py rechnet linear = s^2,2 zurueck.
"""

import math
import os
import sys
import time

import bpy
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_einrichtung_auftrag as ea  # noqa: E402
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, transformieren, alles_loeschen,
    verbinden, exportieren, dreiecke, palette_erweitern,
)
from build_einrichtung_wg_a import stab  # noqa: E402

G0 = ea.AUSSEN_Y + 0.03   # Hofniveau (Oberkante Boden aussen)

palette_erweitern({
    "m1_van": ("#DAD3C5", 0.55, 0.1, 1.0),
    "m1_van_dunkel": ("#B5AC9B", 0.6, 0.1, 1.0),
    "m1_van_glas": ("#2F3B4E", 0.2, 0.0, 1.0),
    "m1_reifen": ("#25262B", 0.9, 0.0, 1.0),
    "m1_chrom": ("#C9CDD3", 0.3, 0.6, 1.0),
    "m1_rucklicht": ("#FF4B3A", 0.4, 0.0, 1.0),
    "m1_neon": ("#FF4FA3", 0.4, 0.0, 1.0),
    "m1_lampe": ("#FFC37A", 0.4, 0.0, 1.0),
    "m1_tafel": ("#2A2E3A", 0.5, 0.0, 1.0),
    "m1_tor": ("#8A929C", 0.5, 0.45, 1.0),
    "m1_tor_dunkel": ("#6E7680", 0.55, 0.45, 1.0),
})
ea.LEUCHTEND.update({"m1_neon": 1.2, "m1_lampe": 2.2, "m1_rucklicht": 1.5})


def kippen(teile, y_mitte, grad):
    """Dreht Teile um die Betrachter-Achse (Godot z) um (0, y_mitte, 0) -- das schiefe Tor."""
    m = (Matrix.Translation(G(0, y_mitte, 0)) @ Matrix.Rotation(math.radians(grad), 4, "Y")
         @ Matrix.Translation(-G(0, y_mitte, 0)))
    for t in teile:
        t.matrix_world = m @ t.matrix_world
    return teile


def rolltor():
    teile = []
    for sx in (-1, 1):
        teile += transformieren(ea.nachbarwand(2.9, 1.7, []), x=sx * 3.0, y=G0, z=0.0)
    # Sturz ueber der Oeffnung
    teile.append(kasten("sturz", (3.4, 0.7, 0.4), (0, G0 + 2.05, 0), "s_ziegel"))
    teile.append(kasten("sturz_kappe", (3.46, 0.1, 0.46), (0, G0 + 2.45, 0), "s_beton_kappe"))
    for sx in (-1, 1):
        teile.append(kasten("pfosten", (0.16, 2.3, 0.3), (sx * 1.6, G0 + 1.15, 0.0), "s_stahl", rund=0.02))
    teile.append(kasten("dunkel", (3.1, 2.0, 0.05), (0, G0 + 1.0, -0.14), "kunststoff_dunkel"))
    # halb hochgerolltes Tor: unten offen, schief (links tiefer als rechts)
    tor = [kasten("tor", (3.0, 0.95, 0.07), (0, G0 + 1.5, 0.02), "m1_tor", rund=0.01, segmente=1)]
    for i in range(7):
        tor.append(kasten("rille", (3.0, 0.025, 0.085), (0, G0 + 1.1 + i * 0.13, 0.02), "m1_tor_dunkel"))
    # Graffiti: bunte Flaechen auf dem Tor
    tor.append(kasten("tag_band", (1.5, 0.28, 0.01), (-0.45, G0 + 1.62, 0.062), "s_wandpink"))
    tor.append(kasten("tag_band2", (0.9, 0.18, 0.01), (0.25, G0 + 1.35, 0.062), "s_blau"))
    tor.append(liegender_zylinder("tag_kreis", 0.2, 0.01, (0.95, G0 + 1.6, 0.062), "z", "s_gelb", seiten=12))
    tor.append(kasten("tag_blitz", (0.12, 0.5, 0.01), (-1.2, G0 + 1.5, 0.062), "s_mint"))
    teile += kippen(tor, G0 + 1.5, 4.0)
    # Griffleiste am Tor: haengt unten, wirkt wie abgebrochen
    teile.append(kasten("kasten_oben", (3.1, 0.22, 0.3), (0, G0 + 1.95, 0.0), "s_stahl", rund=0.02))
    # Lampe ueber dem Tor
    teile.append(stab("arm", (0, G0 + 2.7, 0.2), (0, G0 + 2.7, 0.55), 0.05, "s_stahl"))
    teile.append(kasten("lampe", (0.5, 0.1, 0.22), (0, G0 + 2.75, 0.6), "s_stahl", rund=0.02))
    teile.append(kasten("licht", (0.42, 0.03, 0.16), (0, G0 + 2.68, 0.6), "m1_lampe"))
    return teile


def kastenwagen():
    t = []
    t.append(kasten("aufbau", (3.7, 1.75, 1.8), (-0.55, G0 + 1.22, 0), "m1_van", rund=0.1, segmente=2))
    t.append(kasten("haube", (1.1, 0.8, 1.76), (1.9, G0 + 0.8, 0), "m1_van", rund=0.1, segmente=2))
    t.append(kasten("scheibe", (0.06, 0.62, 1.5), (1.33, G0 + 1.45, 0), "m1_van_glas"))
    for s in (-1, 1):
        t.append(kasten("fenster", (0.9, 0.5, 0.02), (1.0, G0 + 1.55, s * 0.905), "m1_van_glas"))
        t.append(kasten("streifen", (3.7, 0.16, 0.02), (-0.55, G0 + 0.95, s * 0.905), "s_orange"))
    # Beule und Rostfleck an der Seite
    t.append(kasten("beule", (0.55, 0.38, 0.02), (-1.0, G0 + 1.3, 0.906), "m1_van_dunkel"))
    t.append(kasten("rost", (0.3, 0.2, 0.02), (-1.5, G0 + 0.6, 0.906), "m1_tor_dunkel"))
    t.append(kasten("stossfaenger", (0.12, 0.18, 1.7), (2.5, G0 + 0.45, 0), "m1_chrom"))
    t.append(kasten("heck", (0.1, 0.18, 1.7), (-2.43, G0 + 0.45, 0), "m1_chrom"))
    for s in (-1, 1):
        t.append(kasten("scheinwerfer", (0.05, 0.16, 0.3), (2.46, G0 + 0.78, s * 0.6), "s_licht"))
        t.append(kasten("ruecklicht", (0.05, 0.28, 0.14), (-2.43, G0 + 0.95, s * 0.8), "m1_rucklicht"))
    for wx in (-1.5, 1.6):
        for s in (-1, 1):
            t.append(liegender_zylinder("rad", 0.36, 0.24, (wx, G0 + 0.36, s * 0.78), "z", "m1_reifen", seiten=10))
            t.append(liegender_zylinder("nabe", 0.2, 0.26, (wx, G0 + 0.36, s * 0.78), "z", "m1_chrom", seiten=8))
    return t


STRICHE = {
    "O": [((0, 0), (0.34, 0)), ((0.34, 0), (0.34, 0.5)), ((0.34, 0.5), (0, 0.5)), ((0, 0.5), (0, 0))],
    "N": [((0, 0), (0, 0.5)), ((0, 0.5), (0.34, 0)), ((0.34, 0), (0.34, 0.5))],
    "A": [((0, 0), (0.17, 0.5)), ((0.17, 0.5), (0.34, 0)), ((0.07, 0.2), (0.27, 0.2))],
    "I": [((0.17, 0), (0.17, 0.5))],
    "R": [((0, 0), (0, 0.5)), ((0, 0.5), (0.34, 0.5)), ((0.34, 0.5), (0.34, 0.25)), ((0.34, 0.25), (0, 0.25)),
          ((0.12, 0.25), (0.34, 0))],
}


def neonschild():
    t = []
    t.append(zylinder("mast", 0.09, 3.6, (0, G0, 0), "m1_tafel", seiten=8, radius_oben=0.07))
    t.append(zylinder("fuss", 0.2, 0.12, (0, G0, 0), "s_stahl", seiten=8))
    yc = G0 + 4.15
    t.append(kasten("tafel", (3.5, 1.1, 0.12), (0, yc, 0), "m1_tafel", rund=0.03, segmente=1))
    for sx in (-0.9, 0.9):
        t.append(stab("strebe", (sx, G0 + 3.2, 0.0), (sx, yc - 0.5, 0.0), 0.05, "m1_tafel"))
    # Rahmen
    z = 0.08
    for a, b in (((-1.65, yc - 0.48), (1.65, yc - 0.48)), ((1.65, yc - 0.48), (1.65, yc + 0.48)),
                 ((1.65, yc + 0.48), (-1.65, yc + 0.48)), ((-1.65, yc + 0.48), (-1.65, yc - 0.48))):
        t.append(stab("rahmen", (a[0], a[1], z), (b[0], b[1], z), 0.035, "m1_neon"))
    # Schrift "ON AIR"
    x = -1.28
    for zeichen in "ON AIR":
        if zeichen == " ":
            x += 0.26
            continue
        for (u0, v0), (u1, v1) in STRICHE[zeichen]:
            t.append(stab("buchstabe", (x + u0, yc - 0.25 + v0, z), (x + u1, yc - 0.25 + v1, z), 0.055, "m1_neon"))
        x += 0.34 + 0.16
    return t


def hofleuchte():
    t = []
    t.append(zylinder("fuss", 0.16, 0.14, (0, G0, 0), "s_stahl", seiten=8))
    t.append(zylinder("mast", 0.07, 3.3, (0, G0, 0), "s_stahl", seiten=7, radius_oben=0.05))
    t.append(stab("arm", (0, G0 + 3.25, 0), (0.7, G0 + 3.35, 0), 0.05, "s_stahl"))
    t.append(zylinder("schirm", 0.33, 0.14, (0.8, G0 + 3.18, 0), "s_stahl", seiten=10, radius_oben=0.07))
    t.append(zylinder("licht", 0.26, 0.03, (0.8, G0 + 3.15, 0), "m1_lampe", seiten=10))
    t.append(kugel("birne", 0.1, (0.8, G0 + 3.12, 0), "m1_lampe", ringe=3, seiten=6))
    return t


ASSETS = {
    "welt_rolltor": rolltor,
    "welt_kastenwagen": kastenwagen,
    "welt_neonschild": neonschild,
    "welt_hofleuchte": hofleuchte,
}


def main():
    print("")
    print("=== M1 LANDMARKEN WELT 2 ===")
    for name, bauen in ASSETS.items():
        for versuch in range(4):
            try:
                alles_loeschen()
                teile = bauen()
                obj = verbinden(teile, name)
                ea.leuchten_setzen()
                pfad = os.path.join(ea.AUSGABE, name + ".glb")
                exportieren(obj, pfad)
                break
            except OSError as e:  # Errno 22 solange Godot parallel importiert
                print("  Export-Fehler %s, Wiederholung %d" % (e, versuch + 1))
                time.sleep(2.0)
        print("  %-20s %5d Dreiecke  %2d Mat  %6.1f KB"
              % (name, dreiecke(obj), len(obj.data.materials), os.path.getsize(pfad) / 1024.0))


if __name__ == "__main__":
    main()
