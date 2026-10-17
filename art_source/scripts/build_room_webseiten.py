"""Erzeugt die Raummodule fuer Welt 3 "webseiten" -- den Baukasten fuer die
dritte Karte des Spiels (docs/WELTEN.md, Abschnitt "Welt 3 -- webseiten").

Aufruf:
    blender --background --python art_source/scripts/build_room_webseiten.py

Derselbe Baukasten-Gedanke wie in Welt 1 (build_room_zimmer.py): einzelne
Fliesen, Wandsegmente und Ecken werden im Spiel zu einem Grundriss
zusammengesetzt. Der Grundriss ist mit 13 x 11 Fliesen groesser als das
Zimmer (11 x 9) -- aus Enge ist Platz geworden.

DER UNTERSCHIED ZU WELT 1 IST DIE HALBE ARBEIT (Auftragstext): Welt 1 ist ein
14-Quadratmeter-Zimmer, eng und dunkel. Welt 3 ist ein Arbeitsplatz --
heller, groesser, aufgeraeumt. Das druecken diese Module in drei Entscheidungen
aus, nicht in Text:
  1. Parkett statt Laminat: breitere Dielen (zwei statt vier je Rasterfeld),
     waermerer UND heller abgestimmter Ton.
  2. Ein hohes Fensterband statt einem kleinen, hohen Fenster -- mehr
     Tageslicht faellt in den Raum, das Fenster ist eine Aussage, kein
     Zugestaendnis.
  3. Ausstattung, die nach Beruf aussieht statt nach Uebergang: Regal mit
     Ordnern, Whiteboard, Kaffeemaschine statt Heizkoerper und
     Steckdosenleiste.

Rastermass: eine Rasterzelle = 1 Einheit = 1 Meter. Alles rastet darauf.
Wandhoehe 2,20 Meter, wie in jeder anderen Welt -- nur der Raum drumherum
aendert sich.
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
# Diese Welt soll SICHTBAR heller sein als das Zimmer (dort z. B. boden_a bei
# Bildschirmhelligkeit s=0,25). Die Bodentoene hier liegen bei s=0,52..0,75,
# die Wand bei s=0,72 -- kein feiner Unterschied, sondern ein Sprung, den man
# auf einem Standbild sofort sieht, ohne einen einzigen Text zu lesen.
PALETTE = {
    # Parkett statt Laminat: gleiche warme Holzfaerbung wie im Zimmer
    # (R:G:B ungefaehr 1 : 0,60 : 0,30), aber deutlich heller gefahren --
    # das ist der "wohliger und wärmer" aus docs/WELTEN.md.
    "boden_a":    (0.349, 0.211, 0.105, 1.0),   # Parkettdiele, Ton 1 (heller)
    "boden_b":    (0.238, 0.144, 0.072, 1.0),   # Parkettdiele, Ton 2 (dunkler)
    "boden_weg":  (0.531, 0.321, 0.160, 1.0),   # Laufweg -- heller getreten
    # Saubere, helle Wand statt "angeschmutztem Beige" -- derselbe Beige-
    # Grundton wie die Amtsbeige-Signaturfarbe (ART_DIRECTION Abschnitt 3),
    # nur ohne den Schmutz-Unterton des Zimmers.
    "wand":       (0.485, 0.442, 0.372, 1.0),   # helle Buero-Wand
    "wand_unten": (0.173, 0.158, 0.133, 1.0),   # Sockelleiste, gleicher Ton dunkler
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # globaler Rahmen-/Metallton (wie ueberall)
    "holz_hell":  (0.300, 0.210, 0.126, 1.0),   # helles Regalholz (Birke, kein Pressspan)
    "ordner":     (0.596, 0.480, 0.330, 1.0),   # Aktenordner -- die Amtsbeige-Signaturfarbe
    "whiteboard": (0.820, 0.820, 0.800, 1.0),   # weisse Schreibflaeche
    "notiz":      (0.900, 0.870, 0.800, 1.0),   # Papier-Notiz, gedaempft (keine Deko-Buntheit)
    "maschine":   (0.036, 0.036, 0.040, 1.0),   # dunkles Kunststoffgehaeuse
    "kanne_glas": (0.099, 0.054, 0.020, 1.0),   # Glaskanne mit Kaffee -- bernsteinfarben
}

AUSGABE = "project/assets/room/webseiten"


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


# --- Bodenmodule -------------------------------------------------------------
# Zwei Dielen pro Modul statt vier wie im Zimmer: eine Parkettdiele ist in der
# Realitaet breiter als eine Laminatdiele. Das Verlege-Raster bleibt trotzdem
# bei 1x1 -- die Diele ist ein optisches Detail, keine eigene Rasterzelle.

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
    # Zwei breite Dielen statt vier schmaler (Zimmer-Vorbild): 0,485 Tiefe
    # je Diele statt 0,245. Weniger, breitere Fugen -- das ist der optische
    # Unterschied zwischen Laminat und echtem Parkett, nicht nur die Farbe.
    tiefen = (-0.245, 0.245)
    for i, y in enumerate(tiefen):
        # 0,03 statt 0,025 Hoehe: minimal kraeftiger als das Laminat im
        # Zimmer, damit das Parkett wertiger wirkt -- aber nicht so hoch,
        # dass die Kante wieder wie ein Deckenbalken aussieht (dieselbe
        # Falle wie im Zimmer-Skript beschrieben).
        teile.append(quader("diele_%d" % i, (0.98, 0.485, 0.03), (0.0, y, 0.0), mat_name))
    return verbinden(teile, "boden")


def fliese_a():
    return _dielen("boden_a")


def fliese_b():
    return _dielen("boden_b")


def fliese_weg():
    """Heller getretenes Parkett fuer die Laufwege -- dieselbe Idee wie im
    Zimmer (raum_fliese_weg dort), nur auf breiterer Diele."""
    return _dielen("boden_weg")


# --- Wandmodule ---------------------------------------------------------------
# Strukturell identisch zum Zimmer-Baukasten (Wiedererkennung ist Absicht,
# ART_DIRECTION Abschnitt 9) -- nur Farbe und Fenstermodul unterscheiden sich.

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
    """Wandsegment mit Tuerdurchgang. Oben ein Sturz, damit es eine Oeffnung
    ist und keine Luecke."""
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
    """Fensterband statt Zimmer-Fenster -- laut docs/WELTEN.md eine "echte
    Wand mit Fensterband". Die Oeffnung ist bewusst kein Fenster mehr, das
    knapp in eine Wand passt, sondern ein durchgehendes Querband: tiefere
    Bruestung, hoehere Oeffnung, ein Kaemferriegel quer durch die Mitte, der
    beim Aneinanderreihen mehrerer Module wie ein zusammenhaengendes Band
    wirkt. Kein Glas-Mesh -- die Oeffnung bleibt wie im Zimmer/Amt-Vorbild
    leer, das Licht kommt durch das Fehlen von Geometrie, nicht durch einen
    Shader."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.60), (0.0, 0.0, 0.30), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.28), (0.0, 0.0, 2.06), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.06), (0.0, 0.0, 0.63), "rahmen"))
    teile.append(quader("fensterrahmen_mitte", (0.08, 0.16, 1.23), (0.0, 0.0, 1.275), "rahmen"))
    teile.append(quader("fensterrahmen_quer", (1.00, 0.16, 0.06), (0.0, 0.0, 1.275), "rahmen"))
    return teile


# --- Ausstattung ---------------------------------------------------------------
# Anders als im Zimmer (Heizkoerper, Steckdosenleiste) ist die Ausstattung
# hier die eines Berufs: Ordner statt Umzugskisten, Whiteboard statt
# Waeschestaender, Kaffeemaschine statt improvisiertem Nichts.

def regal():
    """Buero-Regal mit Ordnern -- halb gefuellt, nicht ueberladen. Volle
    Regale wirken vernachlaessigt, leere wirken unbenutzt; aufgeraeumt heisst
    hier: sichtbar geordnet, mit Luft dazwischen (docs-Auftrag: 'aufgeraeumt'
    muss man auf einen Blick sehen, nicht nur lesen)."""
    teile = []
    for x in (-0.28, 0.28):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.04, 0.28, 1.20), (x, 0.0, 0.60), "holz_hell"))
    for i, z in enumerate((0.02, 0.42, 0.82, 1.18)):
        teile.append(quader("boden_%d" % i, (0.60, 0.28, 0.03), (0.0, 0.0, z), "holz_hell"))
    # Drei Ordner auf zwei der drei Faecher -- das dritte bleibt frei.
    teile.append(quader("ordner_0", (0.10, 0.22, 0.36), (-0.15, 0.0, 0.61), "ordner"))
    teile.append(quader("ordner_1", (0.10, 0.22, 0.36), (0.02, 0.0, 0.61), "ordner"))
    teile.append(quader("ordner_2", (0.10, 0.22, 0.36), (-0.10, 0.0, 1.01), "ordner"))
    return teile


def whiteboard():
    """Whiteboard mit zwei Notizzetteln. Die Notizen sind gedaempftes Papier,
    keine bunten Post-its -- Saettigung bleibt Antippbarem vorbehalten
    (ART_DIRECTION R3), auch in der Kulisse."""
    teile = []
    teile.append(quader("flaeche", (0.90, 0.04, 0.62), (0.0, 0.0, 1.30), "whiteboard"))
    teile.append(quader("rahmen_o", (0.94, 0.06, 0.04), (0.0, 0.0, 1.63), "rahmen"))
    teile.append(quader("rahmen_u", (0.94, 0.06, 0.04), (0.0, 0.0, 0.97), "rahmen"))
    teile.append(quader("rahmen_l", (0.04, 0.06, 0.66), (-0.45, 0.0, 1.30), "rahmen"))
    teile.append(quader("rahmen_r", (0.04, 0.06, 0.66), (0.45, 0.0, 1.30), "rahmen"))
    teile.append(quader("notiz_a", (0.10, 0.01, 0.08), (-0.20, -0.03, 1.40), "notiz"))
    teile.append(quader("notiz_b", (0.10, 0.01, 0.08), (0.10, -0.03, 1.20), "notiz"))
    return teile


def kaffeemaschine():
    """Filterkaffeemaschine -- kein Vollautomat, das waere zu viel Wohlstand
    fuer den Anfang dieser Welt. Die Glaskanne ist das ganze Erkennungs-
    merkmal (ART_DIRECTION 7.1: erzaehlende Details statt Detailverfeinerung)."""
    teile = []
    teile.append(quader("korpus", (0.26, 0.22, 0.32), (0.0, 0.0, 0.16), "maschine"))
    teile.append(quader("kopf", (0.22, 0.18, 0.06), (0.0, 0.0, 0.35), "maschine"))
    teile.append(quader("warmhalteplatte", (0.20, 0.18, 0.02), (0.0, 0.0, 0.01), "rahmen"))
    teile.append(zylinder("kanne", 0.08, 0.18, (0.0, 0.02, 0.09), "kanne_glas"))
    teile.append(quader("henkel", (0.02, 0.04, 0.10), (0.10, 0.02, 0.10), "rahmen"))
    teile.append(quader("knopf", (0.04, 0.02, 0.02), (0.0, -0.10, 0.35), "rahmen"))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_regal": regal,
    "raum_whiteboard": whiteboard,
    "raum_kaffeemaschine": kaffeemaschine,
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
    print("=== RAUMMODULE WELT 3 -- WEBSEITEN ===")
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
