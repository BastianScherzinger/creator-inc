"""Erzeugt die Kulisse fuer Welt 6 "kapital" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 6 -- kapital"; docs/STORY.md, "AKT 6 -- Der
Ausstieg").

Aufruf:
    blender --background --python art_source/scripts/build_world_kapital.py

Reine Deko wie in jeder anderen Welt -- kein Spielsystem haengt daran.

GENAU SECHS REQUISITEN, NICHT MEHR (Auftrag: "Baue nicht mehr Requisiten, als
hier stehen. Ein voller Raum waere das Gegenteil dessen, was der Akt
erzaehlt."): welt_sessel, welt_beistelltisch, welt_stehlampe, welt_
bildschirm, welt_teppich, welt_pflanze. Jede einzelne bleibt bei der
niedrigsten Teilezahl, die noch als das erkennbar ist, was sie darstellt --
das ist hier die Detailtreue selbst, nicht ein Sparzwang: docs/WELTEN.md
woertlich "Ein Sessel, ein Bildschirm, sonst nichts."

welt_bildschirm ist die einzige Requisite mit Emission in dieser Kulisse
(schwacher, kuehler Schimmer): "Die Zahlen laufen weiter, ob man hinsieht
oder nicht" (docs/WELTEN.md) -- der Bildschirm ist an, obwohl niemand davor
sitzt, wenn die Kamera in den Raum schaut.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Alle Werte unten sind bereits so zurueckgerechnet, passend zu
# build_room_kapital.py (dieselbe warme, dunkle Materialsprache).
PALETTE = {
    "holz_dunkel": (0.018, 0.006, 0.002, 1.0),  # wie im Raum -- Holz statt Metall ueberall
    # Sessel: warmes, dunkles Leder statt des kalten Buero-Polsters aus
    # jeder anderen Welt.
    "sessel_polster": (0.036, 0.011, 0.005, 1.0),
    # Stehlampe: gedaempftes Altmessing fuer Fuss und Stange, ein warmer,
    # heller Stoffschirm, plus Emission fuer das Licht selbst.
    "lampe_metall": (0.013, 0.008, 0.004, 1.0),
    "lampe_schirm": (0.268, 0.199, 0.119, 1.0),
    "lampe_licht":      (0.173, 0.133, 0.047, 1.0),
    "lampe_licht_glut": (1.0, 0.699, 0.268, 1.0),
    # Bildschirm: dunkler Rahmen wie ueberall im Spiel, aber die Flaeche hat
    # -- als einzige in dieser Kulisse -- eine schwache Emission (siehe
    # Modulkopf).
    "bildschirm_rahmen": (0.001, 0.001, 0.002, 1.0),
    "bildschirm_glas":      (0.006, 0.013, 0.023, 1.0),
    "bildschirm_glas_glut": (0.099, 0.268, 0.531, 1.0),
    # Teppich: gedeckter Rotbraunton mit dunklerem Rand.
    "teppich_grund": (0.071, 0.036, 0.018, 1.0),
    "teppich_rand":  (0.023, 0.013, 0.006, 1.0),
    # Pflanze: ruhiges, gedaemptes Gruen statt des kraeftigen Buero-Gruens
    # aus jeder anderen Welt -- weniger Behauptung, mehr Bestand.
    "gruen_ruhig": (0.009, 0.036, 0.006, 1.0),
    "topf":        (0.029, 0.011, 0.006, 1.0),
    "topf_rand":   (0.009, 0.004, 0.002, 1.0),
    "erde":        (0.0, 0.0, 0.0, 1.0),
}

AUSGABE = "project/assets/world/kapital"


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


def material_leuchtend(name, staerke):
    """Wie material(), aber mit echter Emission -- reserviert fuer Lampe und
    Bildschirm, die beiden einzigen Lichtquellen dieser Kulisse."""
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = PALETTE[name]
        bsdf.inputs["Roughness"].default_value = 0.5
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = PALETTE[name + "_glut"]
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = staerke
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


def quader_leuchtend(name, groesse, position, mat_name, staerke, drehung=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = groesse
    if any(drehung):
        obj.rotation_euler = tuple(math.radians(w) for w in drehung)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material_leuchtend(mat_name, staerke))
    return obj


def zylinder(name, radius, hoehe, position, mat_name, seiten=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


def zylinder_leuchtend(name, radius, hoehe, position, mat_name, staerke, seiten=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material_leuchtend(mat_name, staerke))
    return obj


# --- Die Requisiten -----------------------------------------------------------
# Genau sechs, nicht mehr (Modulkopf). Jede bleibt bei der Teilezahl, die
# ihre Silhouette noch traegt -- weniger Deko-Aufwand als in jeder anderen
# Welt, weil hier weniger stehen soll.

def sessel():
    """Ein einzelner Sessel -- docs/WELTEN.md woertlich. Breiter und tiefer
    als jeder Buerostuhl im Spiel, mit vollen Armlehnen statt duenner
    Metallstreben: ein Moebelstueck zum Bleiben, nicht zum Arbeiten."""
    teile = []
    teile.append(quader("sitz", (0.62, 0.60, 0.16), (0.0, 0.0, 0.26), "sessel_polster"))
    teile.append(quader("lehne", (0.62, 0.14, 0.55), (0.0, -0.27, 0.55), "sessel_polster"))
    for x in (-0.32, 0.32):
        teile.append(quader("armlehne_%s" % ("l" if x < 0 else "r"),
                             (0.14, 0.58, 0.32), (x, 0.0, 0.42), "sessel_polster"))
    for i, (x, y) in enumerate(((-0.24, -0.22), (0.24, -0.22), (-0.24, 0.22), (0.24, 0.22))):
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.16), (x, y, 0.08), "holz_dunkel"))
    return teile


def beistelltisch():
    """Kleiner runder Beistelltisch neben dem Sessel -- drei Zylinder
    genuegen fuer Platte, Saeule und Fuss."""
    teile = []
    teile.append(zylinder("platte", 0.24, 0.03, (0.0, 0.0, 0.47), "holz_dunkel", 10))
    teile.append(zylinder("saeule", 0.04, 0.42, (0.0, 0.0, 0.24), "holz_dunkel", 8))
    teile.append(zylinder("fuss", 0.16, 0.03, (0.0, 0.0, 0.015), "holz_dunkel", 10))
    return teile


def stehlampe():
    """Stehlampe mit Stoffschirm -- die zweite Lichtquelle im Raum, neben
    dem Kamin (raum_kamin im Raumskript). Warmes Licht statt kaltem
    Bildschirmlicht, deshalb eigene Emissionsfarbe (lampe_licht_glut)."""
    teile = []
    teile.append(zylinder("fuss", 0.14, 0.03, (0.0, 0.0, 0.015), "lampe_metall", 10))
    teile.append(zylinder("stange", 0.02, 1.30, (0.0, 0.0, 0.68), "lampe_metall", 8))
    teile.append(quader("schirm", (0.30, 0.30, 0.26), (0.0, 0.0, 1.46), "lampe_schirm"))
    teile.append(zylinder_leuchtend("licht", 0.08, 0.08, (0.0, 0.0, 1.46), "lampe_licht", 1.8, 8))
    return teile


def bildschirm():
    """Ein einzelner Bildschirm auf schmalem Staender -- docs/WELTEN.md
    woertlich. Die Flaeche schimmert schwach (material_leuchtend), weil die
    Zahl dahinter weiterlaeuft, ob man hinsieht oder nicht (docs/WELTEN.md:
    'Die Zahlen laufen weiter, ob man hinsieht oder nicht')."""
    teile = []
    teile.append(quader("fuss", (0.30, 0.20, 0.02), (0.0, 0.0, 0.01), "holz_dunkel"))
    teile.append(quader("stange", (0.03, 0.03, 0.30), (0.0, 0.0, 0.16), "bildschirm_rahmen"))
    teile.append(quader("rahmen", (0.46, 0.03, 0.30), (0.0, 0.0, 0.36), "bildschirm_rahmen"))
    teile.append(quader_leuchtend("glas", (0.42, 0.01, 0.26), (0.0, -0.02, 0.36), "bildschirm_glas", 0.8))
    return teile


def teppich():
    """Flacher Teppich unter dem Sessel -- Rand und Grundflaeche in zwei
    Toenen, mehr Musterung braucht die Silhouette nicht."""
    teile = []
    teile.append(quader("rand", (1.80, 1.30, 0.02), (0.0, 0.0, 0.01), "teppich_rand"))
    teile.append(quader("grund", (1.60, 1.10, 0.015), (0.0, 0.0, 0.0175), "teppich_grund"))
    return teile


def pflanze():
    """Ruhige Pflanze mit vier statt sechs Blaettern und gedaemptem Gruen --
    weniger Behauptung als in jeder anderen Welt, passend zum leersten Raum
    im Spiel."""
    teile = []
    teile.append(zylinder("topf", 0.16, 0.26, (0.0, 0.0, 0.13), "topf"))
    teile.append(zylinder("topf_rand", 0.18, 0.04, (0.0, 0.0, 0.27), "topf_rand"))
    teile.append(zylinder("erde", 0.15, 0.03, (0.0, 0.0, 0.255), "erde"))
    teile.append(zylinder("stamm", 0.025, 0.45, (0.0, 0.0, 0.475), "gruen_ruhig", 6))
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (20,  0.66, 0.24, 20.0),
            (110, 0.62, 0.22, 24.0),
            (200, 0.68, 0.25, 18.0),
            (290, 0.64, 0.23, 22.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.10, 0.02),
                            (math.cos(rad) * 0.05, math.sin(rad) * 0.05, hoehe),
                            "gruen_ruhig", (0.0, neigung, winkel)))
    return teile


REQUISITEN = {
    "welt_sessel": sessel,
    "welt_beistelltisch": beistelltisch,
    "welt_stehlampe": stehlampe,
    "welt_bildschirm": bildschirm,
    "welt_teppich": teppich,
    "welt_pflanze": pflanze,
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
    print("=== KULISSE WELT 6 -- KAPITAL ===")
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
