"""Erzeugt die Kulisse fuer Welt 1 (Amt) als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_world_amt.py

Die Kulisse macht aus einer grauen Platte einen ORT. Sie ist reine Deko --
kein Spielsystem haengt daran. Deshalb liegt sie unter assets/world/<welt>/:
Welt 2 bekommt denselben Satz Dateinamen mit anderen Gegenstaenden.

Die Requisiten stammen aus docs/STORY.md 3:
    "Neonroehre, von der eine flackert. Resopaltresen. Ein Gummibaum, den
     seit Jahren niemand giesst. Die Nummernanzeige springt von 47 auf 49."

Der Gummibaum ist die wichtigste davon -- er ist in Welt 1 vertrocknet und
lebt in Welt 5 wieder. Diese Geschichte erzaehlt niemand, man sieht sie nur.
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
    "moebel":  (0.271, 0.298, 0.361, 1.0),
    "hell":    (0.557, 0.592, 0.659, 1.0),
    # Deutlich dunkler: Bei 0,79 leuchteten die Wartebaenke heller als
    # jede Station und wurden zum Hauptmotiv des Bildes.
    "holz":    (0.218, 0.190, 0.152, 1.0),
    "akzent":  (0.949, 0.663, 0.231, 1.0),
    "papier":  (0.961, 0.945, 0.910, 1.0),
    "welk":    (0.451, 0.427, 0.290, 1.0),   # vertrocknetes Blattgruen
    "erde":    (0.294, 0.259, 0.227, 1.0),
    "wand":    (0.365, 0.396, 0.463, 1.0),
}

AUSGABE = "project/assets/world/amt"


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


# --- Die Requisiten ---------------------------------------------------------

def tresen():
    """Resopaltresen mit drei Schaltern. Die Trennscheiben sind das Detail,
    das ihn unverwechselbar macht -- ohne sie waere es nur ein langer Tisch."""
    teile = []
    teile.append(quader("tresen_korpus", (5.60, 0.80, 1.05), (0.0, 0.0, 0.52), "moebel"))
    teile.append(quader("tresen_platte", (5.90, 0.98, 0.08), (0.0, 0.0, 1.09), "holz"))
    # Drei Arbeitsplaetze, dazwischen Trennscheiben
    for i, x in enumerate((-1.85, 0.0, 1.85)):
        teile.append(quader("schalter_nische_%d" % i, (1.30, 0.10, 0.30),
                            (x, 0.42, 0.94), "hell"))
        teile.append(quader("schalter_nummer_%d" % i, (0.24, 0.04, 0.20),
                            (x, -0.44, 1.42), "akzent"))
        teile.append(zylinder("schalter_pfosten_%d" % i, 0.03, 0.60,
                              (x, -0.44, 1.12), "hell"))
    for x in (-0.92, 0.92):
        teile.append(quader("trennscheibe", (0.05, 0.90, 0.70), (x, 0.0, 1.48), "hell"))
    return teile


def wand():
    """Rueckwand mit Aushaengen. Die vergilbten Zettel am schwarzen Brett
    erzaehlen, dass hier seit Jahren dasselbe haengt."""
    teile = []
    # Niedriger als eine echte Wand: Bei isometrischer Aufsicht verdeckt eine
    # 3,40 hohe Flaeche die halbe Szene. 2,10 deutet den Raum an, ohne ihn
    # zuzustellen -- im Vorschaubild sofort sichtbar geworden.
    teile.append(quader("wand_flaeche", (12.0, 0.20, 2.10), (0.0, 0.0, 1.05), "wand"))
    # Sockelleiste -- ohne sie wirkt die Wand wie eine schwebende Platte
    teile.append(quader("wand_sockel", (12.0, 0.26, 0.16), (0.0, 0.0, 0.08), "moebel"))
    # Schwarzes Brett mit Aushaengen
    teile.append(quader("brett", (2.20, 0.06, 1.10), (-3.60, -0.12, 1.20), "moebel"))
    for i, (dx, dz, dreh) in enumerate([(-0.60, 0.30, 2.0), (0.10, 0.25, -3.0),
                                         (0.62, -0.20, 1.5), (-0.30, -0.32, -2.0)]):
        teile.append(quader("aushang_%d" % i, (0.46, 0.02, 0.34),
                            (-3.60 + dx, -0.16, 1.20 + dz * 0.7), "papier", (0.0, dreh, 0.0)))
    # Hinweisschild
    teile.append(quader("schild", (1.40, 0.05, 0.30), (3.20, -0.12, 1.60), "akzent"))
    return teile


def pflanze():
    """Der Gummibaum. Vertrocknet -- die Blaetter haengen nach unten und die
    Farbe ist ausgeblichen.

    In Welt 5 kommt dieselbe Pflanze wieder, dann in Gruen und aufrecht.
    Niemand erklaert das. Man sieht es."""
    teile = []
    teile.append(zylinder("topf", 0.30, 0.42, (0.0, 0.0, 0.21), "erde"))
    teile.append(zylinder("topf_rand", 0.33, 0.06, (0.0, 0.0, 0.44), "moebel"))
    teile.append(zylinder("stamm", 0.05, 1.10, (0.0, 0.0, 0.95), "welk", 6))
    # Blaetter haengen fast senkrecht nach unten -- DAS ist das ganze Merkmal.
    #
    # Zweimal falsch herum gebaut: Bei Rotation um Y wandert die X-Achse nach
    # (cos t, 0, -sin t). Ein NEGATIVER Winkel hebt das Blatt also an, statt es
    # haengen zu lassen -- die Pflanze sah aus wie ein aufgespannter Schirm.
    # Und selbst +46 Grad war noch zu flach: Ein trauriges Blatt haengt steil.
    #
    # Die Ansatzpunkte sind zusaetzlich gestaffelt. Alle auf einer Hoehe
    # ergaeben eine Krone -- gewollt ist eine Pflanze, die aufgibt.
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (0,   1.16, 0.40, 74.0),
            (72,  0.98, 0.34, 80.0),
            (144, 1.24, 0.38, 68.0),
            (216, 0.86, 0.30, 84.0),
            (288, 1.06, 0.36, 77.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.15, 0.025),
                            (math.cos(rad) * 0.13, math.sin(rad) * 0.13, hoehe),
                            "welk", (0.0, neigung, winkel)))
    return teile


def deckenlampe():
    """Neonroehre in Kastenfassung. Sie haengt tief -- das druckt den Raum
    nach unten und macht ihn eng."""
    teile = []
    teile.append(quader("fassung", (2.40, 0.34, 0.14), (0.0, 0.0, 0.0), "hell"))
    teile.append(quader("roehre", (2.20, 0.22, 0.06), (0.0, 0.0, -0.08), "papier"))
    for dx in (-0.90, 0.90):
        teile.append(quader("aufhaengung", (0.04, 0.04, 0.50), (dx, 0.0, 0.32), "hell"))
    return teile


def sitzbank():
    """Wartebank an der Wand -- fuer die Leute, die nicht bei dir anstehen.
    Sie fuellt den Raum und macht ihn zu einem Wartezimmer."""
    teile = []
    teile.append(quader("bank_sitz", (3.20, 0.50, 0.09), (0.0, 0.0, 0.45), "holz"))
    teile.append(quader("bank_lehne", (3.20, 0.08, 0.48), (0.0, -0.21, 0.72), "holz"))
    for dx in (-1.40, 0.0, 1.40):
        teile.append(quader("bank_bein", (0.08, 0.44, 0.44), (dx, 0.0, 0.22), "moebel"))
    return teile


REQUISITEN = {
    "welt_tresen": tresen,
    "welt_wand": wand,
    "welt_pflanze": pflanze,
    "welt_lampe": deckenlampe,
    "welt_bank": sitzbank,
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
    print("=== KULISSE WELT 1 ===")
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
