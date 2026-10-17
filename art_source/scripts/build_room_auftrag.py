"""Erzeugt die Raummodule fuer Welt 2 "auftrag" -- denselben Grundriss wie
Welt 1, ein paar Monate spaeter (docs/WELTEN.md, Abschnitt "Welt 2 -- auftrag").

Aufruf:
    blender --background --python art_source/scripts/build_room_auftrag.py

WIEDERERKENNUNG IST DIE AUSSAGE (docs/WELTEN.md, docs/STORY.md AKT 2): Der
Spieler soll das Zimmer aus Welt 1 sofort wiedererkennen -- gleicher
Grundriss, gleiches Laminat, gleiches Fensterband, gleicher Heizkoerper,
gleiche Wandfarbe. Deshalb ist dieses Skript zu grossen Teilen eine Kopie von
build_room_zimmer.py und keine Neuerfindung: wo nichts geaendert werden soll,
steht hier exakt derselbe Code, dieselbe Palette, dieselben Masse.

Was sich aendert, aendert sich gezielt und einzeln:
- raum_fliese_weg: die Laufwege sind nach Monaten Arbeit staerker abgetreten,
  also HELLER als in Welt 1 (die Fliese selbst wird nicht breiter -- breitere
  Wege entstehen erst dadurch, dass beim Verlegen im Level mehr Rasterfelder
  mit diesem Modul belegt werden, das ist eine Aufgabe der Kartendaten, nicht
  dieses Bausteins).
- alles andere im Raum-Baukasten bleibt unveraendert.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Die Werte unten sind bereits so zurueckgerechnet -- uebernommen 1:1 aus
# build_room_zimmer.py, denn die Palette dort ist bereits korrekt gerechnet
# und soll sich fuer die unveraenderten Elemente auch nicht verschieben.
PALETTE = {
    # Laminat, Wand, Rahmen, Heizkoerper, Kabel, Textil: identisch zu Welt 1.
    # Das ist Absicht, nicht Traegheit -- siehe Modulkommentar oben.
    "boden_a":    (0.043, 0.026, 0.013, 1.0),   # Laminatdiele, Ton 1
    "boden_b":    (0.026, 0.015, 0.008, 1.0),   # Laminatdiele, Ton 2
    # boden_weg ist der einzige geaenderte Farbwert im ganzen Raum-Baukasten:
    # in Welt 1 war s ~ 0,33 (linear 0,087). Nach Monaten Laufweg ist die
    # Stelle sichtbar heller ausgetreten, s ~ 0,42 -> linear = 0,42^2,2.
    # Verhaeltnis der Kanaele zueinander bleibt erhalten (gleicher Laminatton,
    # nur staerker abgerieben), nur die Helligkeit steigt.
    "boden_weg":  (0.148, 0.104, 0.061, 1.0),   # Laufweg -- noch heller getreten
    "wand":      (0.128, 0.120, 0.107, 1.0),   # angeschmutztes Beige, kein Buero-Grau
    "wand_unten":(0.082, 0.077, 0.069, 1.0),   # Sockelleiste
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # globaler Rahmen-/Metallton (wie Welt 1)
    "heizkoerper":(0.302, 0.268, 0.199, 1.0),   # altes Weiss, leicht vergilbt
    "kabel":      (0.006, 0.006, 0.008, 1.0),   # Kunststoff der Steckdosenleiste
    "textil":     (0.268, 0.218, 0.173, 1.0),   # verwaschenes Handtuch -- der Waeschestaender bleibt
}

AUSGABE = "project/assets/room/auftrag"


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
# Vier Dielen pro Modul statt einer Fliese, unveraendert aus Welt 1: eine Diele
# ist 1 x 0,25 Einheiten, vier Stueck ergeben ein Rasterfeld von 1x1.

def verbinden(teile, name):
    """Verschmilzt mehrere Quader zu EINEM Mesh.

    Das ist kein Aufraeumen, sondern Pflicht fuer alle Bodenmodule:
    RoomBuilder legt den Boden als MultiMeshInstance3D an, und ein MultiMesh
    kann genau EIN Mesh vervielfaeltigen. Es nimmt deshalb das erste, das es
    im glTF findet.

    Genau daran ist Welt 1 zuerst gescheitert: eine Bodenkachel bestand aus
    vier einzelnen Dielen, und im Spiel lag daraufhin pro Rasterfeld genau
    eine Diele statt vier -- als helle Streifen im Abstand von einem Meter,
    mit Loechern dazwischen. Der Fehler war im Bild deutlich und im Code
    unsichtbar, weil beide Seiten fuer sich richtig waren. Diese Funktion
    verhindert, dass Welt 2 denselben Fehler wiederholt.
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
        # 0,98 x 0,245 x 0,025 -- exakt wie in Welt 1, damit die Fugenoptik
        # zwischen beiden Welten identisch bleibt (Wiedererkennung).
        teile.append(quader("diele_%d" % i, (0.98, 0.245, 0.025), (0.0, y, 0.0), mat_name))
    return verbinden(teile, "boden")


def fliese_a():
    return _dielen("boden_a")


def fliese_b():
    return _dielen("boden_b")


def fliese_weg():
    """Heller getretene Dielen fuer die Laufwege. Nach ein paar Monaten
    Auftragsarbeit sind dieselben Wege noch staerker ausgetreten als in
    Welt 1 -- deshalb greift dieses Modul auf den helleren Palettenwert
    "boden_weg" oben zu, nicht auf einen eigenen."""
    return _dielen("boden_weg")


# --- Wandmodule ---------------------------------------------------------------
# Unveraendert aus Welt 1 -- Wiedererkennung ist die Aussage, siehe Kopf-
# kommentar. Gleiche Masse, gleiche Palette, gleicher Aufbau.

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
    """Wandsegment mit Tuerdurchgang -- weiterhin der einzige Weg rein und
    raus. Oben ein Sturz, damit es eine Oeffnung ist und keine Luecke."""
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
    """Wandsegment mit Fenster -- weiterhin nur eines, klein und hoch (siehe
    docs/WELTEN.md, "Was gleich bleibt": Fensterband)."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.90), (0.0, 0.0, 0.45), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.42), (0.0, 0.0, 1.99), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.06), (0.0, 0.0, 0.93), "rahmen"))
    teile.append(quader("fensterrahmen", (0.10, 0.16, 0.84), (0.0, 0.0, 1.38), "rahmen"))
    return teile


# --- Ausstattung ---------------------------------------------------------------
# Ebenfalls unveraendert: Heizkoerper, Steckdosenleiste und der
# Waeschestaender bleiben exakt wie in Welt 1 stehen. Der Staender ist
# ausdruecklich keine Nachlaessigkeit -- docs/WELTEN.md nennt ihn woertlich
# "der Witz": alles um ihn herum ist ernster geworden, er nicht.

def heizkoerper():
    """Rippenheizkoerper an der Wand. Ohne die Rippen ist es nur eine Kiste
    an der Wand -- sie sind das ganze Erkennungsmerkmal."""
    teile = []
    teile.append(quader("ruecken", (0.80, 0.06, 0.60), (0.0, 0.0, 0.45), "heizkoerper"))
    rippen = 4
    for i in range(rippen):
        x = -0.30 + i * (0.60 / (rippen - 1))
        teile.append(quader("rippe_%d" % i, (0.10, 0.10, 0.58), (x, -0.05, 0.45), "heizkoerper"))
    return teile


def steckdosenleiste():
    """Mehrfachsteckdose mit zu vielen Steckern -- die Ueberlastung ist die
    Pointe, unveraendert aus Welt 1."""
    teile = []
    teile.append(quader("koerper", (0.42, 0.10, 0.045), (0.0, 0.0, 0.0), "kabel"))
    slots = (-0.16, -0.08, 0.0, 0.08)
    for i, x in enumerate(slots):
        teile.append(quader("stecker_%d" % i, (0.05, 0.06, 0.05), (x, 0.06, 0.045), "rahmen"))
    teile.append(quader("adapter_huckepack", (0.06, 0.05, 0.06), (0.08, 0.10, 0.11), "kabel"))
    teile.append(quader("kabel_strang", (0.05, 0.30, 0.03), (0.0, -0.22, -0.02), "kabel"))
    return teile


def gestell():
    """Waeschestaender -- bleibt Zug fuer Zug wie in Welt 1 (raum_gestell
    dort), samt asymmetrisch durchhaengendem Handtuch. docs/WELTEN.md sagt es
    woertlich: 'Der Waeschestaender bleibt -- das ist der Witz'."""
    teile = []
    for x in (-0.55, 0.55):
        seite = "l" if x < 0 else "r"
        teile.append(quader("staender_%s" % seite, (0.05, 0.05, 1.10), (x, 0.0, 0.55), "rahmen"))
    for i, z in enumerate((0.35, 0.68, 1.00)):
        teile.append(quader("sprosse_%d" % i, (1.10, 0.04, 0.04), (0.0, 0.0, z), "rahmen"))
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
    print("=== RAUMMODULE WELT 2 -- AUFTRAG ===")
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
