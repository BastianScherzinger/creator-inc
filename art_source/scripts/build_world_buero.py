"""Erzeugt die Kulisse fuer Welt 4 "buero" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 4 -- buero"; docs/STORY.md, "AKT 4 -- Das
Buero").

Aufruf:
    blender --background --python art_source/scripts/build_world_buero.py

Reine Deko wie in Welt 3 (build_world_webseiten.py) -- kein Spielsystem
haengt daran. Deshalb liegt sie unter assets/world/<welt>/.

Welt 4 ist derselbe Beruf wie Welt 3, nur gewachsen: "Vier Schreibtische,
drei davon besetzt" (docs/WELTEN.md) statt eines einzelnen Arbeitsplatzes.
Zwei Requisiten sind deshalb neu und beide erzaehlen "mehr Menschen, nicht
mehr Zeug":
  - welt_besprechungstisch: ein Tisch fuer das Team, nicht fuer eine Person
    -- die "Team"-Station aus der Kette wird hier sichtbar Moebel.
  - welt_garderobe: ein Kleiderstaender mit haengender Jacke und Hut -- das
    Buero ist gerade benutzt, jemand ist gleich da oder gerade gegangen.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
#
# Die meisten Toene sind woertlich aus build_world_webseiten.py uebernommen
# (gleiche Materialsprache, derselbe Beruf) -- nur die Garderobe braucht
# zwei neue, eigens gerechnete Farben.
PALETTE = {
    "holz_schreibtisch": (0.325, 0.234, 0.163, 1.0),  # helles Buero-Holz, IKEA-hell
    "bein_metall":       (0.557, 0.592, 0.659, 1.0),  # derselbe globale Rahmenton wie im Raum
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # dunkles Monitorgehaeuse
    "bildschirm_glas":   (0.008, 0.010, 0.014, 1.0),  # Bildschirm aus, leicht blaeulich
    "tastatur":          (0.218, 0.218, 0.214, 1.0),  # heller Kunststoff
    "container_korpus":  (0.388, 0.388, 0.380, 1.0),  # heller Metall-/Laminatkorpus
    "container_front":   (0.268, 0.268, 0.260, 1.0),  # Schubladenfront, etwas dunkler
    "gruen_gesund":      (0.094, 0.268, 0.080, 1.0),  # kraeftiges Gruen -- der Pflanze geht es gut
    "topf":              (0.268, 0.147, 0.113, 1.0),  # Terrakotta-Topf
    "topf_rand":         (0.099, 0.054, 0.042, 1.0),  # Topfrand, dunkler
    "erde":              (0.015, 0.009, 0.005, 1.0),  # Blumenerde
    "stuhl_polster":     (0.056, 0.052, 0.062, 1.0),  # Buerostuhl-Polster, dunkel neutral
    "tasse":             (0.268, 0.268, 0.260, 1.0),  # Kaffeetasse auf dem Schreibtisch
    # Neu fuer die Garderobe: gedaempftes Dunkelblau fuer die Jacke
    # (s=0,18/0,20/0,26 -- Stoff, kein Polster, deshalb ein eigener Ton statt
    # Wiederverwendung von stuhl_polster) und ein fast schwarzer Filzton fuer
    # den Hut.
    "jacke_stoff": (0.023, 0.029, 0.052, 1.0),
    "hut_stoff":   (0.006, 0.005, 0.005, 1.0),
}

AUSGABE = "project/assets/world/buero"


def alles_loeschen():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def material(name):
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = PALETTE[name]
        bsdf.inputs["Roughness"].default_value = 1.0
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = 0.0
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.0
    return mat


def quader(name, groesse, position, mat_name, drehung=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = groesse
    if any(drehung):
        obj.rotation_euler = tuple(math.radians(w) for w in drehung)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material(mat_name))
    return obj


def zylinder(name, radius, hoehe, position, mat_name, seiten=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Die Requisiten -----------------------------------------------------------

def schreibtisch():
    """Schreibtisch mit zwei Monitoren, Tastatur, Maus und einer Tasse --
    derselbe Arbeitsplatz wie in Welt 3, hier vervielfacht auf vier
    Schreibtische im Grundriss (docs/WELTEN.md)."""
    teile = []
    teile.append(quader("platte", (1.60, 0.75, 0.04), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    beine = ((-0.74, -0.33), (0.74, -0.33), (-0.74, 0.33), (0.74, 0.33))
    for i, (x, y) in enumerate(beine):
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.70), (x, y, 0.35), "bein_metall"))
    for i, x in enumerate((-0.30, 0.30)):
        teile.append(quader("monitor_fuss_%d" % i, (0.10, 0.08, 0.10), (x, -0.20, 0.79), "bildschirm_rahmen"))
        teile.append(quader("monitor_screen_%d" % i, (0.46, 0.03, 0.30), (x, -0.28, 1.02), "bildschirm_glas"))
    teile.append(quader("tastatur", (0.34, 0.13, 0.02), (0.0, 0.18, 0.745), "tastatur"))
    teile.append(quader("maus", (0.05, 0.08, 0.02), (0.22, 0.18, 0.745), "tastatur"))
    teile.append(zylinder("tasse", 0.035, 0.08, (-0.55, 0.20, 0.78), "tasse"))
    return teile


def stuhl():
    """Buerostuhl mit Armlehnen -- wie in Welt 3, derselbe aufgestiegene
    Stuhl, nur jetzt vierfach im Raum."""
    teile = []
    teile.append(quader("sitz", (0.46, 0.46, 0.06), (0.0, 0.0, 0.46), "stuhl_polster"))
    teile.append(quader("lehne", (0.42, 0.06, 0.50), (0.0, -0.22, 0.75), "stuhl_polster"))
    teile.append(zylinder("saeule", 0.04, 0.40, (0.0, 0.0, 0.23), "bein_metall"))
    teile.append(quader("fuss_x", (0.60, 0.06, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    teile.append(quader("fuss_y", (0.06, 0.60, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    for x in (-0.24, 0.24):
        teile.append(quader("armlehne", (0.06, 0.30, 0.05), (x, -0.05, 0.58), "bein_metall"))
    return teile


def rollcontainer():
    """Rollcontainer unter dem Schreibtisch -- wie in Welt 3, ein Container
    pro Arbeitsplatz."""
    teile = []
    teile.append(quader("korpus", (0.42, 0.55, 0.58), (0.0, 0.0, 0.31), "container_korpus"))
    for i, z in enumerate((0.14, 0.33, 0.52)):
        teile.append(quader("front_%d" % i, (0.38, 0.03, 0.16), (0.0, -0.29, z), "container_front"))
        teile.append(quader("griff_%d" % i, (0.14, 0.02, 0.02), (0.0, -0.31, z), "bein_metall"))
    for i, (x, y) in enumerate(((-0.17, -0.22), (0.17, -0.22), (-0.17, 0.22), (0.17, 0.22))):
        teile.append(zylinder("rolle_%d" % i, 0.03, 0.04, (x, y, 0.03), "bein_metall", 6))
    return teile


def besprechungstisch():
    """Grosser Tisch fuer das Team, nicht fuer eine Person -- die
    'Team'-Station aus der Kette (docs/WELTEN.md) wird hier sichtbares
    Moebel im zweiten Raumbereich. Sechs Beine statt vier: bei 2,4 Metern
    Laenge braucht die Platte in der Mitte Unterstuetzung, sonst haengt sie
    sichtbar durch."""
    teile = []
    teile.append(quader("platte", (2.40, 1.10, 0.05), (0.0, 0.0, 0.74), "holz_schreibtisch"))
    for x in (-1.05, 0.0, 1.05):
        for y in (-0.45, 0.45):
            teile.append(quader("bein_%d_%d" % (int(x * 100), int(y * 100)),
                                (0.06, 0.06, 0.70), (x, y, 0.37), "bein_metall"))
    teile.append(quader("querstrebe", (2.00, 0.05, 0.04), (0.0, 0.0, 0.42), "bein_metall"))
    return teile


def pflanze():
    """Pflanze, der es gut geht -- wie in Welt 3, dasselbe Zeichen dafuer,
    dass hier laenger gearbeitet wird als nur vorbeigeschaut."""
    teile = []
    teile.append(zylinder("topf", 0.18, 0.28, (0.0, 0.0, 0.14), "topf"))
    teile.append(zylinder("topf_rand", 0.20, 0.04, (0.0, 0.0, 0.29), "topf_rand"))
    teile.append(zylinder("erde", 0.17, 0.03, (0.0, 0.0, 0.275), "erde"))
    teile.append(zylinder("stamm", 0.025, 0.55, (0.0, 0.0, 0.565), "gruen_gesund", 6))
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (0,   0.78, 0.26, 18.0),
            (60,  0.74, 0.24, 22.0),
            (120, 0.80, 0.27, 16.0),
            (180, 0.76, 0.25, 24.0),
            (240, 0.72, 0.23, 20.0),
            (300, 0.78, 0.26, 18.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.10, 0.02),
                            (math.cos(rad) * 0.06, math.sin(rad) * 0.06, hoehe),
                            "gruen_gesund", (0.0, neigung, winkel)))
    return teile


def garderobe():
    """Kleiderstaender mit haengender Jacke und Hut -- das Buero ist gerade
    benutzt, jemand ist gleich da oder erst kurz gegangen (Auftrag Punkt 7:
    'es arbeiten Menschen hier'). Drei Materialtoene: Metallgestell, Jacke,
    Hut (R2)."""
    teile = []
    teile.append(zylinder("fuss", 0.16, 0.03, (0.0, 0.0, 0.015), "bein_metall", 8))
    teile.append(zylinder("stange", 0.025, 1.65, (0.0, 0.0, 0.85), "bein_metall", 8))
    for i, winkel in enumerate((0.0, 90.0, 180.0, 270.0)):
        rad = math.radians(winkel)
        teile.append(quader("haken_%d" % i, (0.10, 0.03, 0.03),
                            (math.cos(rad) * 0.05, math.sin(rad) * 0.05, 1.55),
                            "bein_metall", (0.0, 0.0, winkel)))
    # Jacke haengt an einem der Haken -- ein einzelner Quader genuegt fuer
    # die Silhouette (R1), Details waeren hier nur Draw-Calls ohne Nutzen.
    teile.append(quader("jacke", (0.32, 0.10, 0.55), (0.0, 0.07, 1.15), "jacke_stoff"))
    teile.append(zylinder("hut_krempe", 0.14, 0.02, (0.0, 0.0, 1.68), "hut_stoff", 8))
    teile.append(zylinder("hut_kopf", 0.09, 0.10, (0.0, 0.0, 1.74), "hut_stoff", 8))
    return teile


REQUISITEN = {
    "welt_schreibtisch": schreibtisch,
    "welt_stuhl": stuhl,
    "welt_rollcontainer": rollcontainer,
    "welt_besprechungstisch": besprechungstisch,
    "welt_pflanze": pflanze,
    "welt_garderobe": garderobe,
}


def exportieren(pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=pfad, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False,
    )


def main():
    print("")
    print("=== KULISSE WELT 4 -- BUERO ===")
    gesamt = 0
    for name, bauen in REQUISITEN.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt += dreiecke
        print("  %-22s %2d Teile  ~%4d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, os.path.getsize(pfad) / 1024.0))
    print("")
    print("  %d Requisiten, zusammen ~%d Dreiecke" % (len(REQUISITEN), gesamt))


if __name__ == "__main__":
    main()
