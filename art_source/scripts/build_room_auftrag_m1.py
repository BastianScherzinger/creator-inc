"""M1 (D1_ART_DIRECTION, Paket M) -- neue Boeden fuer Welt 2 "auftrag" (Das Studio).

Aufruf:
    blender --background --python art_source/scripts/build_room_auftrag_m1.py

Erzeugt nach project/assets/room/auftrag/ (nur neue Dateien):
    boden_garage_a/_b        Beton mit Oelflecken und Reifenspur
    boden_hofpflaster_a/_b   dunkles Pflaster mit Moosfugen
    boden_riffelblech_a/_b   Stahlblech mit Riffelung (Requisitenlager)
    boden_estrich_a/_b       roher Estrich (Younes' Ecke)
    boden_bitumen_a/_b       Dachpappe mit Nahtstreifen (Dach)
    boden_kinoteppich_a/_b   dunkelroter Teppich mit feinem Muster (Kino)
Gleiche Ausmasse wie die bestehenden boden_*-Module (1 x 1 m, y 0 .. -0,06).
Farben sRGB-Hex; farbe() in build_room_wg.py rechnet linear = s^2,2 zurueck.
"""

import math
import os
import random
import sys
import time

import bmesh
import bpy

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_room_auftrag_neu as modul  # noqa: E402
from build_room_wg import (  # noqa: E402
    G, kissen_platte, alles_loeschen, verbinden, exportieren, dreiecke, masse,
    palette_erweitern, _objekt,
)

_tragplatte = modul._tragplatte

palette_erweitern({
    # Garage: Beton, Oel, Reifen
    "m1_garage_a": ("#8D8A85", 0.80, 0.0, 1.0),
    "m1_garage_b": ("#84817C", 0.80, 0.0, 1.0),
    "m1_garage_fuge": ("#5E5B57", 0.95, 0.0, 1.0),
    "m1_oel": ("#45423F", 0.35, 0.0, 1.0),
    "m1_reifen": ("#6A6762", 0.90, 0.0, 1.0),
    # Hof: dunkles Pflaster, Moos
    "m1_hof_a": ("#6A5F57", 0.90, 0.0, 1.0),
    "m1_hof_b": ("#5C524B", 0.90, 0.0, 1.0),
    "m1_hof_c": ("#756A61", 0.90, 0.0, 1.0),
    "m1_hof_d": ("#63554C", 0.90, 0.0, 1.0),
    "m1_hof_fuge": ("#3E4631", 0.95, 0.0, 1.0),
    # Riffelblech
    "m1_blech": ("#6F7378", 0.45, 0.45, 1.0),
    "m1_blech_rippe": ("#9199A1", 0.35, 0.55, 1.0),
    "m1_blech_fuge": ("#3D4046", 0.80, 0.2, 1.0),
    # Estrich
    "m1_estrich_a": ("#8E8A84", 0.90, 0.0, 1.0),
    "m1_estrich_b": ("#86827C", 0.90, 0.0, 1.0),
    "m1_estrich_fleck": ("#7A766F", 0.95, 0.0, 1.0),
    "m1_estrich_fuge": ("#5F5B56", 0.95, 0.0, 1.0),
    # Bitumen
    "m1_bitumen": ("#524F4D", 0.95, 0.0, 1.0),
    "m1_bitumen_2": ("#4A4846", 0.95, 0.0, 1.0),
    "m1_bitumen_kies": ("#6D6A66", 0.95, 0.0, 1.0),
    "m1_bitumen_naht": ("#8A857E", 0.90, 0.0, 1.0),
    # Kinoteppich
    "m1_kino": ("#6B2A33", 0.97, 0.0, 1.0),
    "m1_kino_muster": ("#84404A", 0.97, 0.0, 1.0),
    "m1_kino_fuge": ("#4D1D25", 0.97, 0.0, 1.0),
})


def _flach(name, punkte, mat, y=0.0008):
    bm = bmesh.new()
    pk = [bm.verts.new(G(x, y, z)) for (x, z) in punkte]
    f = bm.faces.new(pk)
    bm.normal_update()
    if f.normal.z < 0:
        f.normal_flip()
    return _objekt(name, bm, mat)


def _fleck(cx, cz, rx, rz, mat, rng, n=7, y=0.0008):
    pts = [(cx + rx * math.cos(2 * math.pi * k / n) * rng.uniform(0.7, 1.15),
            cz + rz * math.sin(2 * math.pi * k / n) * rng.uniform(0.7, 1.15)) for k in range(n)]
    return _flach("fleck", pts, mat, y)


def boden_garage(v):
    rng = random.Random(41 if v == "a" else 42)
    haupt = "m1_garage_a" if v == "a" else "m1_garage_b"
    teile = [_tragplatte("m1_garage_fuge", -0.004),
             kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.008, haupt)]
    # Reifenspur: zwei schmale Streifen quer durchs Modul (laeuft ueber Modulgrenzen weiter)
    for z in (-0.28, 0.28):
        teile.append(_flach("spur", [(-0.5, z - 0.07), (0.5, z - 0.07), (0.5, z + 0.07), (-0.5, z + 0.07)],
                            "m1_reifen", 0.0006))
    for _ in range(2 if v == "a" else 3):
        teile.append(_fleck(rng.uniform(-0.3, 0.3), rng.uniform(-0.35, 0.35), rng.uniform(0.07, 0.17),
                            rng.uniform(0.06, 0.13), "m1_oel", rng, y=0.0010))
    return teile


def boden_hofpflaster(v):
    teile = [_tragplatte("m1_hof_fuge", -0.012)]
    toene = ["m1_hof_a", "m1_hof_b", "m1_hof_c", "m1_hof_a", "m1_hof_d", "m1_hof_c",
             "m1_hof_b", "m1_hof_a", "m1_hof_c", "m1_hof_d", "m1_hof_b", "m1_hof_a"]
    if v == "b":
        toene = toene[5:] + toene[:5]
    k = 0
    for r in range(4):
        z0 = -0.5 + r * 0.25
        stoesse = [-0.5, 0.0, 0.5] if r % 2 == 0 else [-0.5, -0.25, 0.25, 0.5]
        for i in range(len(stoesse) - 1):
            teile.append(kissen_platte("stein", stoesse[i], stoesse[i + 1], z0, z0 + 0.25,
                                       0.0, -0.012, 0.024, toene[k % len(toene)]))
            k += 1
    return teile


def boden_riffelblech(v):
    teile = [_tragplatte("m1_blech_fuge", -0.004),
             kissen_platte("blech", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.006, "m1_blech")]
    # Riffel: kurze Rauten-Striche im Halbmeterraster, wechselnde Richtung
    for i in range(4):
        for k in range(4):
            cx, cz = -0.375 + i * 0.25, -0.375 + k * 0.25
            wag = ((i + k) % 2 == 0) == (v == "a")
            a, b = (0.085, 0.016) if wag else (0.016, 0.085)
            teile.append(_flach("rippe", [(cx - a, cz - b), (cx + a, cz - b), (cx + a, cz + b), (cx - a, cz + b)],
                                "m1_blech_rippe", 0.0012))
    return teile


def boden_estrich(v):
    rng = random.Random(51 if v == "a" else 52)
    haupt = "m1_estrich_a" if v == "a" else "m1_estrich_b"
    teile = [_tragplatte("m1_estrich_fuge", -0.004),
             kissen_platte("platte", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.007, haupt)]
    for _ in range(3):
        teile.append(_fleck(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0.1, 0.22),
                            rng.uniform(0.08, 0.18), "m1_estrich_fleck", rng))
    return teile


def boden_bitumen(v):
    rng = random.Random(61 if v == "a" else 62)
    teile = [_tragplatte("m1_bitumen_2", -0.004),
             kissen_platte("bahn", -0.5, 0.5, -0.5, 0.5, 0.0, -0.004, 0.004,
                           "m1_bitumen" if v == "a" else "m1_bitumen_2")]
    # Nahtstreifen der Dachbahn
    x = -0.1 if v == "a" else 0.18
    teile.append(_flach("naht", [(x - 0.012, -0.5), (x + 0.012, -0.5), (x + 0.012, 0.5), (x - 0.012, 0.5)],
                        "m1_bitumen_naht", 0.0008))
    for _ in range(9):
        teile.append(_fleck(rng.uniform(-0.42, 0.42), rng.uniform(-0.42, 0.42), rng.uniform(0.02, 0.05),
                            rng.uniform(0.02, 0.05), "m1_bitumen_kies", rng, n=5, y=0.0010))
    return teile


def boden_kinoteppich(v):
    teile = [_tragplatte("m1_kino_fuge", -0.002),
             kissen_platte("flor", -0.5, 0.5, -0.5, 0.5, 0.0, -0.002, 0.002, "m1_kino")]
    punkte = ((-0.25, -0.25), (0.25, 0.25)) if v == "a" else ((0.25, -0.25), (-0.25, 0.25))
    for (cx, cz) in punkte:
        r = 0.09
        teile.append(_flach("raute", [(cx, cz - r), (cx + r, cz), (cx, cz + r), (cx - r, cz)], "m1_kino_muster", 0.0008))
    return teile


MODULE = {}
for _typ, _fn in (("garage", boden_garage), ("hofpflaster", boden_hofpflaster),
                  ("riffelblech", boden_riffelblech), ("estrich", boden_estrich),
                  ("bitumen", boden_bitumen), ("kinoteppich", boden_kinoteppich)):
    for _v in ("a", "b"):
        MODULE["boden_%s_%s" % (_typ, _v)] = (lambda f=_fn, v=_v: f(v))


def main():
    print("")
    print("=== M1 BOEDEN WELT 2 ===")
    for name, bauen in MODULE.items():
        for versuch in range(4):
            try:
                alles_loeschen()
                obj = verbinden(bauen(), name)
                pfad = modul.modul_pfad(name)
                exportieren(obj, pfad)
                break
            except OSError as e:  # Errno 22 solange Godot parallel importiert
                print("  Export-Fehler %s, Wiederholung %d" % (e, versuch + 1))
                time.sleep(2.0)
        (x0, x1), (y0, y1), (z0, z1) = masse(obj)
        print("  %-26s %4d Dreiecke  y %+.3f..%+.3f  %5.1f KB"
              % (name, dreiecke(obj), y0, y1, os.path.getsize(pfad) / 1024.0))
    # Wand-/Tuermodule mit neuer Palette (dunklerer Ziegel, Stahltuer) neu schreiben
    if "--ohne-waende" not in sys.argv:
        for name, bauen in modul.MODULE.items():
            if name.startswith("boden_"):
                continue
            for versuch in range(4):
                try:
                    alles_loeschen()
                    obj = verbinden(bauen(), name)
                    exportieren(obj, modul.modul_pfad(name))
                    break
                except OSError as e:
                    print("  Export-Fehler %s, Wiederholung %d" % (e, versuch + 1))
                    time.sleep(2.0)
        print("  Wand-/Tuermodule neu geschrieben")


if __name__ == "__main__":
    main()
