"""M1 (D1_ART_DIRECTION, Paket M) -- zusaetzliche Boeden fuer Welt 1 "zimmer".

Aufruf:
    blender --background --python art_source/scripts/build_room_wg_m1.py

Erzeugt nach project/assets/room/zimmer/ (nur neue Dateien, nichts Bestehendes):
    wg_boden_teppich_a/_b    Wohnzimmer: Flokati-Beige mit hellen und dunklen Flocken
    wg_boden_holzhell_a/_b   freies Zimmer: Kiefer hell abgezogen (frisch ausgezogen)
    wg_boden_schach_a/_b     Kueche: Schachbrett-Fliese 0,5 m, Fuge hell
Der Laeufer im Flur ist kein Bodenmodul, sondern die Kulisse welt_laeufer
(build_world_zimmer_m1.py) -- ein Modul kennt seine Zeile im Flur nicht.

Farben als sRGB-Hex, farbe() in build_room_wg.py rechnet linear = s^2,2 zurueck.
Alle Modul-Ausmasse wie wg_boden_* (1 x 1 m, Oberkante 0, 0,06 nach unten).
"""

import os
import random
import sys

import bmesh
import bpy
import math

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_room_wg as rw  # noqa: E402
from build_room_wg import (  # noqa: E402
    G, kissen_platte, alles_loeschen, verbinden, exportieren, dreiecke, masse,
    palette_erweitern, _objekt, AUSGABE_MODULE,
)

palette_erweitern({
    # Flokati: warmes Beige, Flocken heller / dunkler
    "m1_flokati":        ("#E4D6BE", 0.97, 0.0, 1.0),
    "m1_flokati_hell":   ("#F1E8D6", 0.97, 0.0, 1.0),
    "m1_flokati_dunkel": ("#D2C0A4", 0.97, 0.0, 1.0),
    "m1_flokati_fuge":   ("#BFAE92", 0.97, 0.0, 1.0),
    # Kiefer hell abgezogen
    "m1_abg_a":  ("#E6C694", 0.80, 0.0, 1.0),
    "m1_abg_b":  ("#DDBB85", 0.80, 0.0, 1.0),
    "m1_abg_c":  ("#E9CB9C", 0.80, 0.0, 1.0),
    "m1_abg_d":  ("#D9B67F", 0.80, 0.0, 1.0),
    "m1_abg_fuge": ("#B88F5E", 0.90, 0.0, 1.0),
    # Kuechen-Schachbrett
    "m1_schach_hell":   ("#F0E9D9", 0.50, 0.0, 1.0),
    "m1_schach_dunkel": ("#B9AE9A", 0.50, 0.0, 1.0),
    "m1_schach_fuge":   ("#D8CFBE", 0.90, 0.0, 1.0),
})


def _flocke(cx, cz, r, mat, rng):
    bm = bmesh.new()
    pk = [bm.verts.new(G(cx + r * math.cos(w) * rng.uniform(0.75, 1.15), 0.0007,
                         cz + r * math.sin(w) * rng.uniform(0.75, 1.15)))
          for w in [k * math.pi / 3.0 for k in range(6)]]
    f = bm.faces.new(pk)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt("flocke", bm, mat)


def boden_teppich(variante):
    teile = [rw._tragplatte("m1_flokati_fuge", -0.002),
             kissen_platte("flor", -0.5, 0.5, -0.5, 0.5, 0.0, -0.002, 0.003, "m1_flokati")]
    rng = random.Random(31 if variante == "a" else 32)
    for i in range(7):
        teile.append(_flocke(rng.uniform(-0.38, 0.38), rng.uniform(-0.38, 0.38),
                             rng.uniform(0.08, 0.17),
                             "m1_flokati_hell" if i % 2 == 0 else "m1_flokati_dunkel", rng))
    return teile


_ABG_TOENE = [("m1_abg_a", "m1_abg_b"), ("m1_abg_c", "m1_abg_a"),
              ("m1_abg_d", "m1_abg_c"), ("m1_abg_b", "m1_abg_d")]


def boden_holzhell(variante):
    return rw._dielen_ab(_ABG_TOENE, rw._HOLZ_FUGEN_A, rw._HOLZ_FUGEN_B, 0.25, variante, "m1_abg_fuge")


def boden_schach(variante):
    # 0,5-m-Fliesen: a und b sind gleich -- im Meterraster laeuft das Schachbrett durch.
    return rw._fliesen(2, "m1_schach_fuge",
                       lambda i, k: "m1_schach_hell" if (i + k) % 2 == 0 else "m1_schach_dunkel", 0.010)


MODULE = {
    "wg_boden_teppich_a": lambda: boden_teppich("a"),
    "wg_boden_teppich_b": lambda: boden_teppich("b"),
    "wg_boden_holzhell_a": lambda: boden_holzhell("a"),
    "wg_boden_holzhell_b": lambda: boden_holzhell("b"),
    "wg_boden_schach_a": lambda: boden_schach("a"),
    "wg_boden_schach_b": lambda: boden_schach("b"),
}


def main():
    print("")
    print("=== M1 BOEDEN WELT 1 ===")
    for name, bauen in MODULE.items():
        for versuch in range(4):
            try:
                alles_loeschen()
                obj = verbinden(bauen(), name)
                pfad = os.path.join(AUSGABE_MODULE, name + ".glb")
                exportieren(obj, pfad)
                break
            except OSError as e:  # Errno 22 solange Godot parallel importiert
                print("  Export-Fehler %s, Wiederholung %d" % (e, versuch + 1))
                import time
                time.sleep(2.0)
        (x0, x1), (y0, y1), (z0, z1) = masse(obj)
        print("  %-22s %4d Dreiecke  y %+.3f..%+.3f  %5.1f KB"
              % (name, dreiecke(obj), y0, y1, os.path.getsize(pfad) / 1024.0))


if __name__ == "__main__":
    main()
