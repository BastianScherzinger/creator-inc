"""Erzeugt die Raummodule fuer Welt 1 "zimmer" -- den Baukasten fuer die
allererste Karte des Spiels (docs/WELTEN.md, Abschnitt "Welt 1 -- zimmer").

Aufruf:
    blender --background --python art_source/scripts/build_room_zimmer.py

Gleicher Baukasten-Gedanke wie im Amt-Vorbild (build_room_amt.py): einzelne
Fliesen, Wandsegmente und Ecken werden im Spiel zu einem Grundriss
zusammengesetzt. Der Grundriss selbst ist mit 11 x 9 Fliesen kleiner als das
Amt -- Enge ist hier die Aussage, kein Sparzwang.

Rastermass: eine Rasterzelle = 1 Einheit = 1 Meter. Alles rastet darauf.

ABWEICHUNG vom Amt-Vorbild beim Boden: Das Zimmer hat Laminat, keine Fliesen.
Eine Laminatdiele ist LAENGLICH (1 x 0,25), nicht quadratisch. Damit das
Verlege-Raster trotzdem bei 1x1 bleibt, fasst EIN Modul gleich vier Dielen
zu einem Rasterfeld zusammen -- die Diele ist ein optisches Detail, keine
eigene Rasterzelle.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Die Werte unten sind bereits so zurueckgerechnet -- siehe build_room_amt.py,
# dort ist derselbe Fehler drei Mal in Folge passiert.
PALETTE = {
    # Laminat statt Linoleum: waermerer, braunerer Unterton als im Amt.
    # Zwei Dielentoene reichen fuer ein Verlegemuster -- ein dritter waere
    # im Schachbrett kaum vom ersten zu unterscheiden gewesen.
    "boden_a":    (0.043, 0.026, 0.013, 1.0),   # Laminatdiele, Ton 1
    "boden_b":    (0.026, 0.015, 0.008, 1.0),   # Laminatdiele, Ton 2
    "boden_weg":  (0.087, 0.061, 0.036, 1.0),   # Laufweg -- heller getreten
    "wand":      (0.128, 0.120, 0.107, 1.0),   # angeschmutztes Beige, kein Buero-Grau
    "wand_unten":(0.082, 0.077, 0.069, 1.0),   # Sockelleiste
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # globaler Rahmen-/Metallton (wie Amt)
    "heizkoerper":(0.302, 0.268, 0.199, 1.0),   # altes Weiss, leicht vergilbt
    "kabel":      (0.006, 0.006, 0.008, 1.0),   # Kunststoff der Steckdosenleiste
    "textil":     (0.268, 0.218, 0.173, 1.0),   # verwaschenes Handtuch
}

AUSGABE = "project/assets/room/zimmer"


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


# --- Bodenmodule -------------------------------------------------------------
# Vier Dielen pro Modul statt einer Fliese: eine Diele ist 1 x 0,25 Einheiten,
# also laenglich wie echtes Laminat. Vier Stueck hintereinander ergeben genau
# ein Rasterfeld -- das Verlegeraster bleibt 1x1, obwohl die Geometrie darin
# eine eigene Feinstruktur hat.

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
    tiefen = (-0.375, -0.125, 0.125, 0.375)
    for i, y in enumerate(tiefen):
        # 0,23 statt 0,25 Tiefe: die Luecke zwischen den Dielen ist die Fuge,
        # ganz wie die 0,98 statt 1,0 bei den Amt-Fliesen dort die Fuge war.
        # FLACH: 0,025 statt 0,08 Hoehe.
        #
        # Bei den quadratischen Amt-Fliesen war eine Kante von 0,08 unauffaellig,
        # weil sie neben einer Flaeche von 0,98 lag. Eine Diele ist aber nur
        # 0,25 tief -- dieselbe Kante nimmt hier ein Drittel des Sichtfeldes
        # ein. Im Vorschaubild lag deshalb kein Boden im Raum, sondern
        # Deckenbalken. Flach gilt: Die Fuge soll man ahnen, nicht sehen.
        teile.append(quader("diele_%d" % i, (0.98, 0.245, 0.025), (0.0, y, 0.0), mat_name))
    return verbinden(teile, "boden")


def fliese_a():
    return _dielen("boden_a")


def fliese_b():
    return _dielen("boden_b")


def fliese_weg():
    """Heller getretene Dielen fuer die Laufwege -- dieselbe Idee wie im Amt
    (raum_fliese_weg dort), nur auf Laminat statt Linoleum."""
    return _dielen("boden_weg")


# --- Wandmodule ---------------------------------------------------------------
# Strukturell identisch zum Amt-Vorbild: Wiedererkennung ist Absicht
# (docs/WELTEN.md, "Wiedererkennung ist die Aussage" gilt schon in Welt 2,
# aber die Bauteile selbst sind welt-uebergreifend derselbe Baukasten).

def wand_segment():
    """Ein Meter Wand mit Sockelleiste. Ohne die Leiste stoesst die Wand hart
    auf den Boden und wirkt wie eine gestellte Platte."""
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
    """Wandsegment mit Tuerdurchgang -- der einzige Weg rein und raus in
    einem 14-Quadratmeter-Zimmer. Oben ein Sturz, damit es eine Oeffnung ist
    und keine Luecke."""
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
    """Wandsegment mit Fenster -- laut docs/WELTEN.md nur EINES, klein und
    hoch. Das Modul bleibt trotzdem das Standard-Fensterband aus dem
    Baukasten; die Kuerze der Welt entscheidet ueber die Stueckzahl, nicht
    ueber ein Sondermodul."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.90), (0.0, 0.0, 0.45), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.42), (0.0, 0.0, 1.99), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.06), (0.0, 0.0, 0.93), "rahmen"))
    teile.append(quader("fensterrahmen", (0.10, 0.16, 0.84), (0.0, 0.0, 1.38), "rahmen"))
    return teile


# --- Ausstattung ---------------------------------------------------------------

def heizkoerper():
    """Rippenheizkoerper an der Wand. Ohne die Rippen ist es nur eine Kiste
    an der Wand -- sie sind das ganze Erkennungsmerkmal, wie die Aktentasche
    beim NPC (ART_DIRECTION 7.1: erzaehlende Details sind billiger als
    Detailverfeinerung)."""
    teile = []
    teile.append(quader("ruecken", (0.80, 0.06, 0.60), (0.0, 0.0, 0.45), "heizkoerper"))
    rippen = 4
    for i in range(rippen):
        x = -0.30 + i * (0.60 / (rippen - 1))
        teile.append(quader("rippe_%d" % i, (0.10, 0.10, 0.58), (x, -0.05, 0.45), "heizkoerper"))
    return teile


def steckdosenleiste():
    """Mehrfachsteckdose mit zu vielen Steckern -- die Ueberlastung ist die
    Pointe. Ein Huckepack-Adapter auf einem der Slots erzaehlt das ohne Text:
    hier haengt mehr dran, als die Leiste eigentlich hergibt."""
    teile = []
    teile.append(quader("koerper", (0.42, 0.10, 0.045), (0.0, 0.0, 0.0), "kabel"))
    slots = (-0.16, -0.08, 0.0, 0.08)
    for i, x in enumerate(slots):
        teile.append(quader("stecker_%d" % i, (0.05, 0.06, 0.05), (x, 0.06, 0.045), "rahmen"))
    teile.append(quader("adapter_huckepack", (0.06, 0.05, 0.06), (0.08, 0.10, 0.11), "kabel"))
    teile.append(quader("kabel_strang", (0.05, 0.30, 0.03), (0.0, -0.22, -0.02), "kabel"))
    return teile


def gestell():
    """Waeschestaender -- nach D3 nur als Silhouette benannt (raum_gestell),
    nicht als Rolle. Zwei Staender, drei Sprossen, ein Handtuch, das laenger
    haengt als die anderen: das genuegt als Erkennungszeichen, ganz ohne
    Stoffsimulation."""
    teile = []
    for x in (-0.55, 0.55):
        seite = "l" if x < 0 else "r"
        teile.append(quader("staender_%s" % seite, (0.05, 0.05, 1.10), (x, 0.0, 0.55), "rahmen"))
    for i, z in enumerate((0.35, 0.68, 1.00)):
        teile.append(quader("sprosse_%d" % i, (1.10, 0.04, 0.04), (0.0, 0.0, z), "rahmen"))
    # Das Handtuch haengt ueber der mittleren Sprosse und schlaegt asymmetrisch
    # durch -- ein Merkmal, keine Verzierung.
    teile.append(quader("handtuch", (0.34, 0.03, 0.42), (0.20, 0.03, 0.47), "textil"))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_heizkoerper": heizkoerper,
    "raum_steckdosenleiste": steckdosenleiste,
    "raum_gestell": gestell,
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
    print("=== RAUMMODULE WELT 1 -- ZIMMER ===")
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
