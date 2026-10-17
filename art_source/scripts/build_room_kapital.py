"""Erzeugt die Raummodule fuer Welt 6 "kapital" -- den Baukasten fuer die
sechste und letzte Karte des Spiels (docs/WELTEN.md, Abschnitt "Welt 6 --
kapital"; docs/STORY.md, "AKT 6 -- Der Ausstieg").

Aufruf:
    blender --background --python art_source/scripts/build_room_kapital.py

DAS ENDE DES BOGENS. Nach dem Loft aus Welt 5 (Sichtbeton, zu viele
Bildschirme, ein Stahltraeger unter der Decke) kommt der kleinste und
leerste Raum im ganzen Spiel -- und das ist die Aussage, nicht ein Mangel
(Auftrag: "Baue nicht mehr Requisiten, als hier stehen"). Drei Entscheidungen
setzen das um:
  1. Grundriss 9 x 9 statt 17 x 13 -- kleiner als sogar Welt 1 (11 x 9). Der
     Bogen endet so klein, wie er angefangen hat, nur mit anderem Grund.
  2. Dunkles Holz statt Sichtbeton oder Buero-Parkett -- die Materialsprache
     bricht ein zweites Mal, diesmal von kuehl/industriell zu warm/still.
     Der globale Metall-Rahmenton aus jeder anderen Welt wird hier komplett
     ersetzt durch dunkel gebeiztes Holz (holz_dunkel) -- selbst Fenster- und
     Tuerrahmen sind hier Holz, kein Metall. Das ist die konsequenteste
     Abgrenzung von Welt 5 im ganzen Skript.
  3. Nur zwei zusaetzliche Raummodule (raum_kamin, raum_buecherwand) statt
     drei wie in Welt 5 -- weniger Bauteile fuer den Raum, der am wenigsten
     zeigen soll.

Rastermass: eine Rasterzelle = 1 Einheit = 1 Meter. Wandhoehe 2,20 wie in
jeder anderen Welt.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Alle Werte unten sind bereits so zurueckgerechnet.
#
# Durchgehend warme, dunkle Toene (R > G > B statt des kuehlen R < G < B aus
# Welt 5) -- der zweite Bruch der Materialsprache, diesmal weg vom Loft.
PALETTE = {
    # Dunkles Holz statt Sichtbeton oder Parkett -- zwei gedeckte Braun-
    # toene fuer die Dielenfelder, ein etwas hellerer, wärmerer Laufweg.
    "boden_a":    (0.043, 0.018, 0.006, 1.0),
    "boden_b":    (0.023, 0.009, 0.003, 1.0),
    "boden_weg":  (0.071, 0.032, 0.011, 1.0),
    # Warme, dunkle Wand -- kein Beton, kein Buero-Beige, sondern gedaempftes
    # Taupe-Anthrazit. Ruhe statt Helligkeit ist hier die Aussage.
    "wand":       (0.029, 0.020, 0.015, 1.0),
    "wand_unten": (0.006, 0.004, 0.003, 1.0),
    # Dunkel gebeiztes Holz ersetzt den globalen Metall-Rahmenton aus jeder
    # anderen Welt -- auch Fenster- und Tuerrahmen sind hier Holz.
    "holz_dunkel": (0.018, 0.006, 0.002, 1.0),
    # Kamin: warmer, dunkler Naturstein fuer den Umriss, fast schwarze
    # Feueroeffnung, gluehende Glut mit echter Emission (einziges Modul in
    # dieser Welt mit Emission -- Gegenstueck zur Stadtkarte in Welt 5).
    "kamin_stein":     (0.018, 0.015, 0.013, 1.0),
    "kamin_oeffnung":  (0.0, 0.0, 0.0, 1.0),
    "kamin_glut":      (0.099, 0.006, 0.0, 1.0),
    "kamin_glut_glut": (0.793, 0.047, 0.0, 1.0),
    # Buecherwand: drei gedaempfte Ruecken-Toene statt bunter Deko-Farben
    # (ART_DIRECTION R3 gilt auch hier) -- gerade genug Abwechslung, um nach
    # gelesenen statt dekorativ hingestellten Buechern auszusehen.
    "buch_a": (0.071, 0.006, 0.004, 1.0),
    "buch_b": (0.009, 0.029, 0.036, 1.0),
    "buch_c": (0.061, 0.043, 0.009, 1.0),
}

AUSGABE = "project/assets/room/kapital"


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
    """Wie material(), aber mit echter Emission -- reserviert fuer die Glut
    im Kamin, das Gegenstueck zur leuchtenden Stadtkarte in Welt 5. Dort war
    die Emission das einzige Zeichen von Aktivitaet in einem ueberfuellten
    Raum; hier ist sie das einzige warme Licht in einem fast leeren."""
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = PALETTE[name]
        bsdf.inputs["Roughness"].default_value = 0.7
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


# --- Bodenmodule -------------------------------------------------------------
# Zwei Dielen pro Modul, wie in jeder anderen Welt -- breites, dunkles Holz.

def verbinden(teile, name):
    """Verschmilzt mehrere Quader zu EINEM Mesh.

    Das ist kein Aufraeumen, sondern Pflicht fuer alle Bodenmodule:
    RoomBuilder legt den Boden als MultiMeshInstance3D an, und ein MultiMesh
    kann genau EIN Mesh vervielfaeltigen. Es nimmt deshalb das erste, das es
    im glTF findet.

    Beim ersten Anlauf bestand eine Bodenkachel aus vier einzelnen Dielen. Im
    Spiel lag daraufhin pro Rasterfeld genau eine Diele statt vier -- als
    helle Streifen im Abstand von einem Meter, mit Loechern dazwischen. Der
    Fehler war im Bild deutlich und im Code unsichtbar, weil beide Seiten fuer
    sich richtig waren.
    """
    if not teile:
        return []
    for obj in bpy.data.objects:
        obj.select_set(False)
    for obj in teile:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = teile[0]
    bpy.ops.object.join()
    verbunden = bpy.context.view_layer.objects.active
    verbunden.name = name
    return [verbunden]


def _dielen(mat_name):
    teile = []
    tiefen = (-0.245, 0.245)
    for i, y in enumerate(tiefen):
        teile.append(quader("diele_%d" % i, (0.98, 0.485, 0.03), (0.0, y, 0.0), mat_name))
    return verbinden(teile, "boden")


def fliese_a():
    return _dielen("boden_a")


def fliese_b():
    return _dielen("boden_b")


def fliese_weg():
    """Heller abgetretenes dunkles Holz fuer die Laufwege -- der einzige
    Pfad in einem Raum, der sonst kaum begangen wird."""
    return _dielen("boden_weg")


# --- Wandmodule ----------------------------------------------------------------
# Struktur wie in jeder anderen Welt, Farbe und Fenster deutlich ruhiger:
# ein grosses, ungeteiltes Fenster statt eines Sprossenrasters -- je weniger
# Linien, desto ruhiger das Bild.

def wand_segment():
    """Ein Meter Wand mit Sockelleiste."""
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
    """Wandsegment mit Tuerdurchgang -- Rahmen aus holz_dunkel statt Metall,
    der einzigen Welt im Spiel ohne Metall-Tuerrahmen."""
    teile = []
    for dx in (-0.72, 0.72):
        teile.append(quader("tuer_pfosten", (0.56, 0.14, 2.20), (dx, 0.0, 1.10), "wand"))
        teile.append(quader("tuer_sockel", (0.56, 0.20, 0.14), (dx, 0.0, 0.07), "wand_unten"))
    teile.append(quader("tuer_sturz", (2.00, 0.14, 0.34), (0.0, 0.0, 2.03), "wand"))
    teile.append(quader("tuer_rahmen_l", (0.08, 0.20, 1.86), (-0.46, 0.0, 0.93), "holz_dunkel"))
    teile.append(quader("tuer_rahmen_r", (0.08, 0.20, 1.86), (0.46, 0.0, 0.93), "holz_dunkel"))
    teile.append(quader("tuer_rahmen_o", (1.00, 0.20, 0.08), (0.0, 0.0, 1.86), "holz_dunkel"))
    return teile


def wand_fenster():
    """Ein grosses, ruhiges Fenster -- keine Sprossen, nur ein Rahmen. Das
    ist der bewusste Gegensatz zum Sprossenraster aus Welt 5 (raum_wand_
    fenster dort): weniger Linien im Bild, weil der Raum weniger zeigen
    soll. Die Oeffnung ist trotzdem gross (0,20 bis 2,00), das Fenster bleibt
    das hellste Element im Raum."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.20), (0.0, 0.0, 0.10), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.20), (0.0, 0.0, 2.10), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.05), (0.0, 0.0, 0.20), "holz_dunkel"))
    teile.append(quader("fensterrahmen_mitte", (0.07, 0.16, 1.80), (0.0, 0.0, 1.10), "holz_dunkel"))
    return teile


# --- Zusaetzliche Raummodule -----------------------------------------------
# Nur zwei, so wie es das Kapitel verlangt: Kamin und Buecherwand. Beide
# stehen an der Wand wie raum_regal/raum_whiteboard aus fruehen Welten, aber
# ihr Inhalt ist der eines Zuhauses, keines Buero mehr.

def kamin():
    """Kamin mit gluehender Glut -- die einzige Waermequelle im Raum und die
    einzige Emission dieser Welt (Gegenstueck zur Stadtkarte aus Welt 5,
    siehe Modulkopf). Der Sims darueber ist der einzige "Rahmenton"-Ersatz
    hier: dunkles Holz auf Stein, kein Metall."""
    teile = []
    teile.append(quader("sockel", (0.90, 0.30, 0.10), (0.0, 0.0, 0.05), "kamin_stein"))
    teile.append(quader("wange_l", (0.14, 0.24, 0.80), (-0.40, 0.0, 0.45), "kamin_stein"))
    teile.append(quader("wange_r", (0.14, 0.24, 0.80), (0.40, 0.0, 0.45), "kamin_stein"))
    teile.append(quader("sturz", (0.90, 0.24, 0.10), (0.0, 0.0, 0.90), "kamin_stein"))
    teile.append(quader("oeffnung", (0.58, 0.06, 0.55), (0.0, 0.0, 0.35), "kamin_oeffnung"))
    teile.append(quader("sims", (1.00, 0.28, 0.06), (0.0, 0.0, 1.00), "holz_dunkel"))
    teile.append(quader_leuchtend("glut", (0.36, 0.02, 0.08), (0.0, -0.02, 0.10), "kamin_glut", 2.0))
    return teile


def buecherwand():
    """Eingebautes Bücherregal, vier Faecher, eines bewusst leer -- dieselbe
    Regel wie beim raum_regal aus Welt 3 ('aufgeraeumt heisst hier: sichtbar
    geordnet, mit Luft dazwischen'), nur hoeher und mit gelesenen statt
    abgehefteten Buechern. Kein Whiteboard-Ersatz, sondern das Gegenteil
    davon: es wird hier nichts mehr geplant, nur noch gelesen."""
    teile = []
    for x in (-0.30, 0.30):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.05, 0.30, 1.90), (x, 0.0, 0.95), "holz_dunkel"))
    for i, z in enumerate((0.03, 0.50, 0.97, 1.44)):
        teile.append(quader("boden_%d" % i, (0.65, 0.30, 0.04), (0.0, 0.0, z), "holz_dunkel"))
    faecher = ((0.50, "buch_a"), (0.97, "buch_b"))
    for z, mat in faecher:
        for i, x in enumerate((-0.16, 0.16)):
            teile.append(quader("buch_%s_%d" % (mat, i), (0.12, 0.24, 0.34), (x, 0.0, z + 0.19), mat))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_kamin": kamin,
    "raum_buecherwand": buecherwand,
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
    print("=== RAUMMODULE WELT 6 -- KAPITAL ===")
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
