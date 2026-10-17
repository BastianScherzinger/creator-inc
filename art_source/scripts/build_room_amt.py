"""Erzeugt die Raummodule fuer Welt 1 -- den Baukasten fuer eine ganze Karte.

Aufruf:
    blender --background --python art_source/scripts/build_room_amt.py

Bisher schwebte ein Podest im Nichts. Ein Idle-Tycoon braucht aber einen
ORT, in dem man sich befindet: Fliesenboden, Waende, Tuer, Ecken. Erst dann
wirkt die Karte wie ein Amt und nicht wie eine Testszene.

MODULBAUKASTEN statt fertigem Raum (ART_DIRECTION 7): Einzelne Fliesen,
Wandsegmente und Ecken werden im Spiel zu einem Grundriss zusammengesetzt.
Damit ist Welt 2 eine andere Anordnung derselben Teile -- und ein groesserer
Raum kostet keine neue Modellierung.

Rastermass: eine Fliese = 1 Einheit = 1 Meter. Alles rastet darauf.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Drei Runden "der Boden wird einfach nicht dunkler" hatten genau diese Ursache.
PALETTE = {
    # Deutlich dunkler als zuerst gewaehlt: Bei der Beleuchtung der Szene
    # ueberstrahlte der helle Boden alles und zog den Blick nach unten.
    # Der Boden ist Grundflaeche, kein Hauptdarsteller (ART_DIRECTION R3).
    "boden_a":  (0.048, 0.053, 0.068, 1.0),   # Linoleum, Ton 1
    "boden_b":  (0.065, 0.072, 0.090, 1.0),   # Linoleum, Ton 2
    "boden_weg":(0.098, 0.107, 0.130, 1.0),   # Laufweg -- heller getreten
    "wand":     (0.175, 0.188, 0.222, 1.0),
    "wand_unten":(0.088, 0.096, 0.116, 1.0),  # Sockelleiste
    "rahmen":   (0.557, 0.592, 0.659, 1.0),
    "akzent":   (0.949, 0.663, 0.231, 1.0),
}

AUSGABE = "project/assets/room/amt"


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


def quader(name, groesse, position, mat_name):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = groesse
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material(mat_name))
    return obj


# --- Bodenmodule ------------------------------------------------------------
# Drei Varianten derselben Fliese. Im Spiel im Schachbrett verlegt ergibt das
# ein Linoleummuster -- und ohne Muster wirkt ein Boden wie eine leere Flaeche.

def fliese_a():
    return [quader("fliese", (0.98, 0.98, 0.08), (0.0, 0.0, 0.0), "boden_a")]


def fliese_b():
    return [quader("fliese", (0.98, 0.98, 0.08), (0.0, 0.0, 0.0), "boden_b")]


def fliese_weg():
    """Heller getretene Fliese fuer die Laufwege. Sie zeigt, wo Menschen
    langgehen -- eine Spur, die das Amt seit Jahren benutzt."""
    return [quader("fliese", (0.98, 0.98, 0.08), (0.0, 0.0, 0.0), "boden_weg")]


# --- Wandmodule -------------------------------------------------------------

def wand_segment():
    """Ein Meter Wand mit Sockelleiste. Die Leiste ist entscheidend: Ohne sie
    stoesst die Wand hart auf den Boden und wirkt wie eine gestellte Platte."""
    teile = []
    teile.append(quader("wand", (1.0, 0.14, 2.20), (0.0, 0.0, 1.10), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    return teile


def wand_ecke():
    """Innenecke -- zwei Segmente im rechten Winkel."""
    teile = []
    teile.append(quader("wand_a", (1.0, 0.14, 2.20), (0.0, 0.0, 1.10), "wand"))
    teile.append(quader("sockel_a", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_b", (0.14, 1.0, 2.20), (0.43, -0.43, 1.10), "wand"))
    teile.append(quader("sockel_b", (0.20, 1.0, 0.14), (0.43, -0.43, 0.07), "wand_unten"))
    return teile


def wand_tuer():
    """Wandsegment mit Tuerdurchgang -- der Eingang, durch den alle kommen.
    Oben ein Sturz, damit es eine Oeffnung ist und keine Luecke."""
    teile = []
    for dx in (-0.72, 0.72):
        teile.append(quader("tuer_pfosten", (0.56, 0.14, 2.20), (dx, 0.0, 1.10), "wand"))
        teile.append(quader("tuer_sockel", (0.56, 0.20, 0.14), (dx, 0.0, 0.07), "wand_unten"))
    teile.append(quader("tuer_sturz", (2.00, 0.14, 0.34), (0.0, 0.0, 2.03), "wand"))
    teile.append(quader("tuer_rahmen_l", (0.08, 0.20, 1.86), (-0.46, 0.0, 0.93), "rahmen"))
    teile.append(quader("tuer_rahmen_r", (0.08, 0.20, 1.86), (0.46, 0.0, 0.93), "rahmen"))
    teile.append(quader("tuer_rahmen_o", (1.00, 0.20, 0.08), (0.0, 0.0, 1.86), "rahmen"))
    return teile


def wand_fenster():
    """Wandsegment mit Fensterband -- bringt Struktur in lange Wandflaechen.
    Ohne Unterbrechung wirken fuenf Meter Wand wie eine Mauer."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.90), (0.0, 0.0, 0.45), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.42), (0.0, 0.0, 1.99), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.06), (0.0, 0.0, 0.93), "rahmen"))
    teile.append(quader("fensterrahmen", (0.10, 0.16, 0.84), (0.0, 0.0, 1.38), "rahmen"))
    return teile


# --- Ausstattung ------------------------------------------------------------

def muelleimer():
    teile = []
    teile.append(quader("korpus", (0.30, 0.30, 0.52), (0.0, 0.0, 0.26), "wand_unten"))
    teile.append(quader("deckel", (0.34, 0.34, 0.05), (0.0, 0.0, 0.54), "rahmen"))
    return teile


def wanduhr():
    """Die Uhr, auf die alle schauen. Ein winziges Detail mit grosser Wirkung
    -- in einem Wartezimmer ist sie das meistbetrachtete Objekt."""
    teile = []
    teile.append(quader("gehaeuse", (0.36, 0.06, 0.36), (0.0, 0.0, 0.0), "rahmen"))
    teile.append(quader("blatt", (0.28, 0.03, 0.28), (0.0, -0.04, 0.0), "boden_weg"))
    teile.append(quader("zeiger_lang", (0.03, 0.02, 0.20), (0.0, -0.06, 0.05), "akzent"))
    teile.append(quader("zeiger_kurz", (0.13, 0.02, 0.03), (0.05, -0.06, 0.0), "akzent"))
    return teile


def automat():
    """Getraenkeautomat -- steht in jedem Amt und ist immer halb leer."""
    teile = []
    teile.append(quader("korpus", (0.76, 0.62, 1.80), (0.0, 0.0, 0.90), "wand_unten"))
    teile.append(quader("scheibe", (0.56, 0.05, 1.10), (-0.06, -0.30, 1.10), "boden_weg"))
    teile.append(quader("bedienfeld", (0.16, 0.05, 0.60), (0.28, -0.30, 1.10), "rahmen"))
    teile.append(quader("ausgabe", (0.50, 0.08, 0.22), (0.0, -0.28, 0.30), "rahmen"))
    for i in range(3):
        teile.append(quader("dose_%d" % i, (0.10, 0.03, 0.14),
                            (-0.24 + i * 0.18, -0.33, 1.34), "akzent"))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_muelleimer": muelleimer,
    "raum_uhr": wanduhr,
    "raum_automat": automat,
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
    print("=== RAUMMODULE WELT 1 ===")
    gesamt = 0
    for name, bauen in MODULE.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt += dreiecke
        print("  %-22s %2d Teile  ~%3d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, os.path.getsize(pfad) / 1024.0))
    print("")
    print("  %d Module, zusammen ~%d Dreiecke" % (len(MODULE), gesamt))


if __name__ == "__main__":
    main()
