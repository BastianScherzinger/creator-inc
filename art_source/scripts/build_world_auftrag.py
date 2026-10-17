"""Erzeugt die Kulisse fuer Welt 2 "auftrag" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 2 -- auftrag", docs/STORY.md AKT 2).

Aufruf:
    blender --background --python art_source/scripts/build_world_auftrag.py

Dasselbe Zimmer wie in Welt 1, ein paar Monate spaeter. Wiedererkennung ist
die Aussage -- deshalb ist dieses Skript kein Neuentwurf, sondern eine
gezielte Fortschreibung von build_world_zimmer.py: Grundform und Bauweise der
unveraenderten Requisiten (Matratze) sind uebernommen, jede geaenderte
Requisitur ist einzeln begruendet.

Was sich aendert (docs/WELTEN.md):
    "zweiter Monitor, ein echter Stuhl, die Umzugskiste ist ein Regal
     geworden, die Pizzakartons sind weg. Der Waeschestaender bleibt."
Der zweite Monitor gehoert zur Station "Bauen" (project/assets/stations/),
nicht zur Weltkulisse, und wird deshalb hier nicht gebaut -- der Modul-
vertrag dieser Datei nennt ausschliesslich die sechs Requisiten unten.

Die Pizzakartons (welt_karton aus Welt 1) fallen ersatzlos weg: Es wird
gearbeitet, nicht mehr nur ueberlebt.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Werte, die aus Welt 1 uebernommen werden, sind 1:1 aus build_world_zimmer.py
# kopiert. Neue Werte (Schreibtisch, echter Stuhl, gesuendere Pflanze) sind
# nach derselben Formel frisch gerechnet.
PALETTE = {
    "matratze":     (0.052, 0.056, 0.071, 1.0),   # abgewetzter grau-blauer Bezug, unveraendert
    "decke":        (0.106, 0.082, 0.056, 1.0),   # waermer als die Matratze, unveraendert
    "holz_tisch":   (0.048, 0.028, 0.014, 1.0),   # gedecktes Massivholz -- dunkler und satter
                                                   # als der billige Dekorton des alten Klapptischs,
                                                   # weil es jetzt ein richtiges Moebelstueck ist
    "metall":       (0.173, 0.181, 0.199, 1.0),   # Beschlaege, Regalfach-Inhalt, unveraendert
    "stoff_stuhl":  (0.061, 0.043, 0.026, 1.0),   # Stoffbezug eines echten Stuhls -- waermer und
                                                   # heller als das dunkle Kunstlederpolster des
                                                   # kaputten Buerostuhls aus Welt 1
    "holz_stuhl":   (0.056, 0.032, 0.015, 1.0),   # Stuhlgestell aus Holz statt Metallsaeule
    "pappe":        (0.082, 0.047, 0.023, 1.0),   # Wellpappe, hell -- fuer die geschlossene Kiste
    "pappe_dunkel": (0.029, 0.018, 0.009, 1.0),   # Wellpappe, Schattenseite/Deckelinnenflaeche
    "papier":       (0.220, 0.203, 0.173, 1.0),   # Stapel Papier/Unterlagen auf der Ablage
    "gruen_besser": (0.067, 0.107, 0.036, 1.0),   # kraeftigeres Gruen als "gruen_knapp" in Welt 1 --
                                                   # der Pflanze geht es besser, s ~ 0,29 statt 0,24
    "erde":         (0.015, 0.009, 0.005, 1.0),   # Blumenerde, unveraendert
    "regal_holz":   (0.029, 0.020, 0.011, 1.0),   # dunkles Pressspan-Holz, unveraendert
}

AUSGABE = "project/assets/world/auftrag"


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

def matratze():
    """Matratze direkt auf dem Boden -- unveraendert aus Welt 1. Sie steht
    nicht auf der Liste dessen, was sich aendert (docs/WELTEN.md), und bleibt
    deshalb bewusst identisch: Wiedererkennung braucht ein Ankerstueck, das
    sich ueberhaupt nicht bewegt hat."""
    teile = []
    teile.append(quader("matratze_koerper", (2.00, 1.30, 0.22), (0.0, 0.0, 0.11), "matratze"))
    teile.append(quader("kissen", (0.55, 0.40, 0.14), (-0.65, 0.0, 0.29), "decke"))
    teile.append(quader("decke_haupt", (1.55, 1.10, 0.10), (0.25, 0.0, 0.27), "decke", (0.0, 0.0, 4.0)))
    teile.append(quader("decke_wulst", (0.50, 1.05, 0.16), (0.85, 0.0, 0.30), "decke", (0.0, 0.0, -6.0)))
    return teile


def schreibtisch():
    """Aus dem wackeligen Klapptisch (welt_klapptisch, Welt 1) ist ein
    richtiger Tisch geworden: vier gleich lange, gerade Beine statt eines
    schiefen, eine Zarge unter der Platte fuer Stabilitaet. Das eine
    Merkmal, das den alten Tisch trug -- das schiefe Bein -- ist genau das
    Merkmal, das jetzt fehlt. Kein Wackeln mehr ist hier die Pointe, nicht
    ein neues Detail."""
    teile = []
    teile.append(quader("platte", (1.20, 0.65, 0.04), (0.0, 0.0, 0.74), "holz_tisch"))
    teile.append(quader("zarge_vorn", (1.10, 0.03, 0.08), (0.0, -0.29, 0.68), "holz_tisch"))
    beine = ((-0.55, -0.28), (0.55, -0.28), (-0.55, 0.28), (0.55, 0.28))
    for i, (x, y) in enumerate(beine):
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.74), (x, y, 0.37), "holz_tisch"))
    # Schublade -- ein Griff genuegt, um "richtiges Moebelstueck" statt
    # "Tischplatte auf Stelzen" zu sagen.
    teile.append(quader("schublade", (0.34, 0.02, 0.10), (0.30, -0.30, 0.66), "metall"))
    teile.append(quader("griff", (0.14, 0.02, 0.02), (0.30, -0.315, 0.66), "metall"))
    return teile


def stuhl():
    """Ein echter Stuhl statt des kaputten: gerade Lehne, gerade Beine, keine
    Rollen und keine Saeule. docs/WELTEN.md nennt ihn ausdruecklich 'gerade,
    mit Lehne' -- das genaue Gegenteil des einen Merkmals, das den alten
    Buerostuhl definiert hat (die ausgeleierte, schiefe Lehne aus Welt 1)."""
    teile = []
    teile.append(quader("sitz", (0.42, 0.42, 0.05), (0.0, 0.0, 0.46), "stoff_stuhl"))
    teile.append(quader("lehne", (0.42, 0.04, 0.48), (0.0, -0.19, 0.70), "stoff_stuhl"))
    beine = ((-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17))
    for i, (x, y) in enumerate(beine):
        teile.append(quader("bein_%d" % i, (0.04, 0.04, 0.46), (x, y, 0.23), "holz_stuhl"))
    return teile


def regal():
    """Aus der Umzugskiste (welt_kiste in Welt 1, dort als Nachttisch benutzt)
    ist ein richtiges Regal geworden -- und es ist voller: jedes Fach traegt
    jetzt etwas, nicht nur die oberen zwei. Das erzaehlt denselben Fortschritt
    wie das Regal aus Welt 1 schon zeigte (halb leer = gerade erst
    angefangen), nur eine Stufe weiter."""
    teile = []
    for x in (-0.28, 0.28):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.04, 0.28, 1.20), (x, 0.0, 0.60), "regal_holz"))
    for i, z in enumerate((0.02, 0.42, 0.82, 1.18)):
        teile.append(quader("boden_%d" % i, (0.60, 0.28, 0.03), (0.0, 0.0, z), "regal_holz"))
    teile.append(quader("gegenstand_a", (0.18, 0.16, 0.20), (-0.15, 0.0, 0.52), "pappe"))
    teile.append(quader("gegenstand_b", (0.14, 0.14, 0.34), (0.16, 0.0, 0.99), "metall"))
    # Die zwei zusaetzlichen Gegenstaende sind der ganze Unterschied zu Welt 1:
    # das unterste Fach ist jetzt belegt, und das oberste traegt einen
    # weiteren Stapel statt Leere.
    teile.append(quader("gegenstand_c", (0.50, 0.22, 0.16), (0.0, 0.0, 0.10), "pappe"))
    teile.append(quader("gegenstand_d", (0.16, 0.14, 0.12), (-0.14, 0.0, 1.24), "papier"))
    return teile


def pflanze():
    """Derselben Pflanze wie in Welt 1 geht es jetzt besser: kraeftigeres
    Gruen (Palette 'gruen_besser') und steilere, vollere Blaetter (42 bis 55
    Grad statt 28 bis 38). Noch immer nicht ueppig -- nur ein Schritt weiter
    weg vom 'gerade so am Leben' aus Welt 1, und noch weiter entfernt vom
    ganz vertrockneten Gegenstueck im Amt."""
    teile = []
    teile.append(zylinder("topf", 0.16, 0.24, (0.0, 0.0, 0.12), "erde"))
    teile.append(zylinder("topf_rand", 0.18, 0.04, (0.0, 0.0, 0.25), "regal_holz"))
    teile.append(zylinder("stamm", 0.025, 0.52, (0.0, 0.0, 0.51), "gruen_besser", 6))
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (0,   0.70, 0.24, 46.0),
            (90,  0.64, 0.22, 42.0),
            (180, 0.74, 0.26, 55.0),
            (270, 0.66, 0.22, 44.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.10, 0.02),
                            (math.cos(rad) * 0.06, math.sin(rad) * 0.06, hoehe),
                            "gruen_besser", (0.0, neigung, winkel)))
    return teile


def kiste():
    """Die alte Umzugskiste ist jetzt eine ANDERE Kiste: geschlossen und als
    Ablage genutzt, nicht mehr als halb ausgepackter Nachttisch. Beide
    Klappen liegen flach zu statt schraeg offen zu stehen -- das ist der
    ganze Unterschied zu welt_kiste in Welt 1 -- und obendrauf liegt ein
    Stapel Papier, der 'Ablage' sagt, ohne dass es einen Text braucht."""
    teile = []
    teile.append(quader("koerper", (0.42, 0.42, 0.42), (0.0, 0.0, 0.21), "pappe"))
    teile.append(quader("deckel", (0.42, 0.42, 0.03), (0.0, 0.0, 0.435), "pappe_dunkel"))
    teile.append(quader("papierstapel", (0.24, 0.18, 0.05), (0.05, -0.02, 0.475), "papier"))
    return teile


REQUISITEN = {
    "welt_matratze": matratze,
    "welt_schreibtisch": schreibtisch,
    "welt_stuhl": stuhl,
    "welt_regal": regal,
    "welt_pflanze": pflanze,
    "welt_kiste": kiste,
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
    print("=== KULISSE WELT 2 -- AUFTRAG ===")
    gesamt = 0
    for name, bauen in REQUISITEN.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt += dreiecke
        print("  %-18s %2d Teile  ~%4d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, os.path.getsize(pfad) / 1024.0))
    print("")
    print("  %d Requisiten, zusammen ~%d Dreiecke" % (len(REQUISITEN), gesamt))


if __name__ == "__main__":
    main()
