"""Erzeugt alle NPC-Archetypen als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_npcs.py

Die Modelle sind nach ihrer SILHOUETTE benannt, nicht nach einer Rolle:
npc_gebeugt, npc_kapuze, npc_rucksack. Das ist kein Schoenheitsfehler, sondern
Absicht (ADR-010) -- dieselbe gebeugte Figur ist in Welt 1 ein Rentner und in
Welt 4 ein Bote. Waeren die Dateien nach Rollen benannt, haetten sie das Thema
in den Code getragen. Der Waechter in validate.ps1 hat genau das gemeldet.

Welche Silhouette welche Rolle spielt, steht in data/themes/<welt>/theme.json.

Jeder Archetyp unterscheidet sich in SILHOUETTE, nicht nur in Farbe -- auf einem
6-Zoll-Display ist die Umrissform das Einzige, was zuverlaessig ankommt
(ART_DIRECTION R1). Ein Hut, ein Rucksack, gebeugte Haltung: Das erkennt man
auch, wenn die Figur 40 Pixel hoch ist. Eine andere Jackenfarbe nicht.

Aufbau nach ADR-019: getrennte, benannte Module. Der Spielcode faerbt gezielt
die Kleidungsteile ein und laesst Kopf und Accessoire unberuehrt -- das
funktioniert nur, weil die Teile einzeln benannt sind.
"""

import bpy
import sys
import os
import math

PALETTE = {
    "kleidung": (0.271, 0.298, 0.361, 1.0),   # #454c5c
    "haut":     (0.788, 0.718, 0.604, 1.0),   # #c9b79a
    "akzent":   (0.949, 0.663, 0.231, 1.0),   # #f2a93b
}

AUSGABE = "project/assets/characters"


def alles_loeschen():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.objects):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def material(name):
    """Flaches Material -- reine Farbflaeche, kein Glanz (ART_DIRECTION R2)."""
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


def quader(name, groesse, position, mat_name, drehung_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = groesse
    if drehung_z:
        obj.rotation_euler = (0.0, 0.0, math.radians(drehung_z))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material(mat_name))
    return obj


def grundfigur(hoehe_faktor=1.0, beugung=0.0):
    """Rumpf, Kopf, Arme, Beine. `beugung` neigt den Oberkoerper nach vorn --
    das allein macht aus einer Figur einen alten Menschen."""
    h = hoehe_faktor
    teile = []

    teile.append(quader("rumpf", (0.42, 0.24, 0.62 * h), (0.0, 0.0, 1.05 * h), "kleidung"))
    kopf = quader("kopf", (0.26, 0.24, 0.28), (0.0, beugung * 0.30, 1.52 * h), "haut")
    teile.append(kopf)

    for seite, x in (("links", -0.30), ("rechts", 0.30)):
        teile.append(quader("arm_" + seite, (0.13, 0.15, 0.52 * h),
                            (x, 0.0, 1.02 * h), "kleidung"))
    for seite, x in (("links", -0.13), ("rechts", 0.13)):
        teile.append(quader("bein_" + seite, (0.16, 0.18, 0.74 * h),
                            (x, 0.0, 0.37 * h), "kleidung"))
    return teile


# --- Die Archetypen ---------------------------------------------------------
# Jeder bekommt genau EIN unverwechselbares Merkmal. Mehr wuerde die
# Silhouette verwaschen statt sie zu schaerfen.

def npc_standard():
    teile = grundfigur()
    teile.append(quader("tasche", (0.30, 0.12, 0.24), (0.40, 0.0, 0.78), "akzent", 6.0))
    return teile


def npc_gebeugt():
    """Kleiner, gebeugt, mit Hut und Schuhkarton. Die Beugung erkennt man
    auch aus der Entfernung -- sie ist das eigentliche Merkmal."""
    teile = grundfigur(hoehe_faktor=0.88, beugung=1.0)
    teile.append(quader("hut_krempe", (0.36, 0.34, 0.04), (0.0, 0.30, 1.50), "kleidung"))
    teile.append(quader("hut_kopf", (0.24, 0.22, 0.14), (0.0, 0.30, 1.58), "kleidung"))
    # Der Schuhkarton -- gross, unhandlich, mit beiden Haenden getragen
    teile.append(quader("karton", (0.44, 0.34, 0.26), (0.0, 0.34, 0.86), "akzent"))
    return teile


def npc_schritt():
    """Aufrecht, in Bewegung: ein Bein vorgesetzt. Umhaengetasche."""
    teile = grundfigur()
    for t in teile:
        if t.name == "bein_rechts":
            t.location.y = 0.18
    teile.append(quader("umhaengetasche", (0.26, 0.14, 0.30), (-0.36, 0.10, 0.92), "akzent", -8.0))
    teile.append(quader("riemen", (0.06, 0.06, 0.52), (-0.20, 0.06, 1.20), "akzent", -14.0))
    return teile


def npc_kapuze():
    """Kapuze, Haende in den Taschen -- schmale, zurueckhaltende Silhouette.
    Kein Accessoire: Er hat nichts dabei, er weiss ja nicht mal, was er braucht."""
    teile = grundfigur()
    teile.append(quader("kapuze", (0.34, 0.32, 0.30), (0.0, -0.06, 1.54), "kleidung"))
    for t in teile:
        if t.name.startswith("arm_"):
            t.location.y = 0.08
            t.scale = (1.0, 1.0, 0.86)
    return teile


def npc_breit():
    """Breitere Schultern, aufrechte Haltung, Zeigefinger-Arm erhoben.
    Auch ohne Gesicht als aufgebracht lesbar."""
    teile = grundfigur()
    for t in teile:
        if t.name == "rumpf":
            t.scale = (1.18, 1.0, 1.0)
        if t.name == "arm_rechts":
            t.location.z = 1.34
            t.rotation_euler = (0.0, math.radians(-38.0), 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    return teile


def npc_rucksack():
    """Rucksack auf dem Ruecken -- deutlich sichtbare Ausbuchtung hinten."""
    teile = grundfigur()
    teile.append(quader("rucksack", (0.34, 0.22, 0.42), (0.0, -0.26, 1.10), "akzent"))
    return teile


def npc_traeger():
    """Aufrecht, mit Aktenstapel vor der Brust. Helle Kleidung (Hemd) --
    er gehoert sichtbar auf die andere Seite des Tresens."""
    teile = grundfigur()
    teile.append(quader("aktenstapel_1", (0.34, 0.26, 0.08), (0.0, 0.28, 1.02), "akzent"))
    teile.append(quader("aktenstapel_2", (0.32, 0.24, 0.07), (0.0, 0.28, 1.10), "haut"))
    teile.append(quader("aktenstapel_3", (0.33, 0.25, 0.08), (0.0, 0.28, 1.17), "akzent"))
    return teile


ARCHETYPEN = {
    "npc_standard": npc_standard,
    "npc_gebeugt": npc_gebeugt,
    "npc_schritt": npc_schritt,
    "npc_kapuze": npc_kapuze,
    "npc_breit": npc_breit,
    "npc_rucksack": npc_rucksack,
    "npc_traeger": npc_traeger,
}


def exportieren(pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=pfad,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )


def main():
    print("")
    print("=== NPC-ARCHETYPEN ===")
    gesamt_dreiecke = 0
    for name, bauen in ARCHETYPEN.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt_dreiecke += dreiecke
        groesse = os.path.getsize(pfad) / 1024.0
        print("  %-20s %2d Teile  ~%3d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, groesse))

    print("")
    print("  %d Archetypen, zusammen ~%d Dreiecke" % (len(ARCHETYPEN), gesamt_dreiecke))
    print("  Budget laut ART_DIRECTION: unter 900 je Figur")


if __name__ == "__main__":
    main()
