"""Erzeugt die Raummodule fuer Welt 4 "buero" -- den Baukasten fuer die
vierte Karte des Spiels (docs/WELTEN.md, Abschnitt "Welt 4 -- buero").

Aufruf:
    blender --background --python art_source/scripts/build_room_buero.py

Welt 4 ist der Nachfolger von Welt 3 (build_room_webseiten.py): gleiche
Materialsprache -- dasselbe Parkett, dieselbe helle Buerowand, derselbe
Rahmenton --, aber groesser (Grundriss 17 x 13 statt 13 x 11) und mit mehr
Menschen (docs/WELTEN.md: "Vier Schreibtische, drei davon besetzt").

DAS NEUE AN DIESER WELT IST DIE INNENWAND (raum_innenwand, raum_innentuer):
Welt 4 hat als erste Karte zwei Bereiche. Die Innenwand steht mitten im Raum
und wird deshalb -- anders als jede Aussenwand, die nur von der Innenseite
gesehen wird -- von BEIDEN Seiten gesehen. Zwei Entscheidungen loesen das:
  1. Sie ist duenner (0,10 statt 0,14 Meter) -- eine Trennwand ist keine
     tragende Wand, und das darf man ihr ansehen.
  2. Sie ist NIEDRIGER (1,9 statt 2,2 Meter). Das ist der eigentliche Grund:
     in der isometrischen Ansicht von schraeg oben verdeckt eine raumhohe
     Wand alles dahinter. Bei 1,9 Metern sieht die Kamera ueber sie hinweg
     in den zweiten Bereich, trotzdem liest sie sich als Wand und nicht als
     blosse Absperrung.
Beide Module sind volle Quader (quader() baut immer einen Wuerfel, nie ein
einseitiges Blech) und bekommen deshalb ihre Sockelleiste zweimal -- je einen
eigenen Streifen pro Seite statt eines einzigen mittigen Blocks wie bei der
Aussenwand, wo ohnehin nur eine Seite je gesehen wird.

Rastermass: eine Rasterzelle = 1 Einheit = 1 Meter. Aussenwandhoehe 2,20 wie
in jeder anderen Welt, Innenwandhoehe 1,90 (siehe oben).
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
#
# Boden-, Wand- und Rahmenton sind woertlich aus build_room_webseiten.py
# uebernommen (nicht neu gerechnet) -- das ist die "gleiche Materialsprache"
# aus dem Auftrag: Welt 4 ist derselbe Beruf, nur gewachsen. Nur die neuen
# Objekte (Pinnwand, Kuehlschrank) bekommen eigene, dafuer neu gerechnete
# Toene.
PALETTE = {
    # Parkett, unveraendert aus Welt 3 uebernommen.
    "boden_a":    (0.349, 0.211, 0.105, 1.0),   # Parkettdiele, Ton 1 (heller)
    "boden_b":    (0.238, 0.144, 0.072, 1.0),   # Parkettdiele, Ton 2 (dunkler)
    "boden_weg":  (0.531, 0.321, 0.160, 1.0),   # Laufweg -- heller getreten
    # Helle Buerowand, unveraendert aus Welt 3 uebernommen -- gilt fuer
    # Aussenwand UND Innenwand, es ist dasselbe Gebaeude.
    "wand":       (0.485, 0.442, 0.372, 1.0),   # helle Buero-Wand
    "wand_unten": (0.173, 0.158, 0.133, 1.0),   # Sockelleiste, gleicher Ton dunkler
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # globaler Rahmen-/Metallton (wie ueberall)
    # Neu fuer Welt 4: Pinnwand statt Whiteboard -- s=0,62/0,46/0,32, ein
    # Kork-Braun, damit man sieht "hier steckt Papier", nicht "hier klebt
    # Marker ab".
    "pinnwand_flaeche": (0.349, 0.181, 0.082, 1.0),
    "notiz":      (0.900, 0.870, 0.800, 1.0),   # Zettel-Ton 1, aus Welt 3 uebernommen
    # Zweiter Zettel-Ton (s=0,80/0,82/0,84 -- ein kuehles, gedaempftes
    # Recyclingpapier) fuer Abwechslung: mehrere Menschen pinnen hier an,
    # nicht eine einzelne Person mit einem Zettelblock.
    "notiz_b":    (0.612, 0.646, 0.681, 1.0),
    # Kuehlschrank: zwei Weisstoene (Korpus/Tuer, s=0,86 bzw. 0,78) plus der
    # globale Rahmenton fuer den Griff -- genau drei Materialtoene (R2).
    "kuehlschrank_korpus": (0.718, 0.718, 0.699, 1.0),
    "kuehlschrank_tuer":   (0.579, 0.579, 0.579, 1.0),
}

AUSGABE = "project/assets/room/buero"


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
# Zwei Dielen pro Modul, wie in Welt 3 -- dasselbe breite Parkett.

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
    """Heller getretenes Parkett fuer die Laufwege, wie in Welt 3."""
    return _dielen("boden_weg")


# --- Aussenwandmodule ---------------------------------------------------------
# Strukturell identisch zu Welt 3 (Wiedererkennung ist Absicht, ART_DIRECTION
# Abschnitt 9) -- Aussenwaende aendern sich zwischen Welten nicht, nur der
# Raum drumherum waechst.

def wand_segment():
    """Ein Meter Aussenwand mit Sockelleiste."""
    teile = []
    teile.append(quader("wand", (1.0, 0.14, 2.20), (0.0, 0.0, 1.10), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    return teile


def wand_ecke():
    """Innenecke der Aussenwand -- zwei Segmente im rechten Winkel."""
    teile = []
    teile.append(quader("wand_a", (1.0, 0.14, 2.20), (0.0, 0.0, 1.10), "wand"))
    teile.append(quader("sockel_a", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_b", (0.14, 1.0, 2.20), (0.43, -0.43, 1.10), "wand"))
    teile.append(quader("sockel_b", (0.20, 1.0, 0.14), (0.43, -0.43, 0.07), "wand_unten"))
    return teile


def wand_tuer():
    """Aussenwandsegment mit Tuerdurchgang, mit Sturz und Rahmen."""
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
    """Fensterband -- wie in Welt 3, mehr Tageslicht als ein einzelnes
    kleines Fenster."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.60), (0.0, 0.0, 0.30), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.28), (0.0, 0.0, 2.06), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.06), (0.0, 0.0, 0.63), "rahmen"))
    teile.append(quader("fensterrahmen_mitte", (0.08, 0.16, 1.23), (0.0, 0.0, 1.275), "rahmen"))
    teile.append(quader("fensterrahmen_quer", (1.00, 0.16, 0.06), (0.0, 0.0, 1.275), "rahmen"))
    return teile


# --- Innenwandmodule -----------------------------------------------------------
# Das Neue an Welt 4 (siehe Modulkopf-Kommentar): duenner (0,10), niedriger
# (1,9) und beidseitig sichtbar, weil sie mitten im Raum steht statt am Rand.

def innenwand_segment():
    """Ein Meter Innenwand -- Trennwand zwischen den zwei Bereichen aus
    docs/WELTEN.md, keine tragende Wand.

    0,10 statt 0,14 Meter Dicke: eine Trennwand ist duenner, das darf man ihr
    ansehen. 1,90 statt 2,20 Meter Hoehe: das ist die eigentliche Loesung
    fuer die Isometrie-Kamera. Eine raumhohe Wand mitten im Grundriss wuerde
    in der schraegen Aufsicht den ganzen zweiten Bereich verdecken -- bei
    1,90 Metern sieht man daran vorbei und liest trotzdem "Wand", nicht
    "Absperrung".

    quader() baut immer einen vollen Wuerfel -- nie ein einseitiges Blech --,
    darum hat dieses Segment automatisch Flaechen nach beiden Seiten. Weil
    aber wirklich BEIDE Seiten von Spielern gesehen werden (anders als bei
    der Aussenwand, die nur von innen sichtbar ist), bekommt die
    Sockelleiste zwei eigene, duenne Streifen -- je einen pro Wandflaeche --
    statt eines einzigen mittigen Blocks."""
    teile = []
    teile.append(quader("innenwand", (1.0, 0.10, 1.90), (0.0, 0.0, 0.95), "wand"))
    for seite, y in (("a", -0.075), ("b", 0.075)):
        teile.append(quader("innensockel_%s" % seite, (1.0, 0.05, 0.14), (0.0, y, 0.07), "wand_unten"))
    return teile


def innentuer():
    """Innenwand mit Durchgang -- die Verbindung zwischen den zwei
    Bereichen. Gleiche Dicke und Hoehe wie raum_innenwand (0,10 / 1,90):
    beide Module muessen zueinander passen, sonst springt die Wand an der
    Naht.

    Der Sturz ist flacher als bei der Aussentuer (0,14 statt 0,34 Meter),
    weil von der ohnehin schon niedrigen Innenwand sonst kaum noch etwas als
    Sturz uebrig bliebe -- die Durchgangshoehe bleibt mit 1,76 Metern
    trotzdem bequem hoch genug."""
    teile = []
    for dx in (-0.72, 0.72):
        teile.append(quader("tuer_pfosten", (0.56, 0.10, 1.90), (dx, 0.0, 0.95), "wand"))
        for seite, y in (("a", -0.075), ("b", 0.075)):
            teile.append(quader("tuer_sockel_%s" % seite, (0.56, 0.05, 0.14), (dx, y, 0.07), "wand_unten"))
    teile.append(quader("tuer_sturz", (2.00, 0.10, 0.14), (0.0, 0.0, 1.83), "wand"))
    return teile


# --- Ausstattung ---------------------------------------------------------------
# Welt 4 ist eingerichtet und benutzt (Auftrag Punkt 7): eine Pinnwand mit
# mehreren Zetteln statt eines einzelnen Whiteboards, ein Kuehlschrank statt
# nur einer Kaffeemaschine -- das ist ein Buero mit mehreren Leuten, kein
# Durchgangszimmer.

def pinnwand():
    """Pinnwand mit vier Zetteln in zwei Toenen und leicht schiefen Winkeln
    -- unordentlicher als das Whiteboard aus Welt 3, weil hier mehrere
    Menschen gleichzeitig anpinnen, nicht eine einzelne Person mit einem
    Marker. Kork statt Lackflaeche: ein Blatt Papier steckt, es klebt
    nicht."""
    teile = []
    teile.append(quader("flaeche", (0.90, 0.05, 0.62), (0.0, 0.0, 1.30), "pinnwand_flaeche"))
    teile.append(quader("rahmen_o", (0.94, 0.07, 0.04), (0.0, 0.0, 1.63), "rahmen"))
    teile.append(quader("rahmen_u", (0.94, 0.07, 0.04), (0.0, 0.0, 0.97), "rahmen"))
    teile.append(quader("rahmen_l", (0.04, 0.07, 0.66), (-0.45, 0.0, 1.30), "rahmen"))
    teile.append(quader("rahmen_r", (0.04, 0.07, 0.66), (0.45, 0.0, 1.30), "rahmen"))
    teile.append(quader("notiz_a", (0.11, 0.02, 0.09), (-0.28, -0.04, 1.42), "notiz", (0.0, 0.0, -6.0)))
    teile.append(quader("notiz_b", (0.10, 0.02, 0.08), (-0.05, -0.04, 1.48), "notiz_b", (0.0, 0.0, 4.0)))
    teile.append(quader("notiz_c", (0.10, 0.02, 0.08), (0.18, -0.04, 1.18), "notiz", (0.0, 0.0, 8.0)))
    teile.append(quader("notiz_d", (0.11, 0.02, 0.09), (0.30, -0.04, 1.45), "notiz_b", (0.0, 0.0, -5.0)))
    return teile


def kuehlschrank():
    """Kuehlschrank -- die Ausstattung, die zeigt, dass hier tatsaechlich
    gearbeitet wird (Auftrag Punkt 7): eine Kaffeemaschine allein wirkt nach
    Durchgangszimmer, ein Kuehlschrank nach Buero-Alltag mit mehreren
    Leuten. Zwei Weisstoene (Korpus, Tuer) plus der globale Rahmenton fuer
    Griff und Sockel -- genau drei Materialtoene (R2)."""
    teile = []
    teile.append(quader("korpus", (0.55, 0.55, 1.50), (0.0, 0.0, 0.75), "kuehlschrank_korpus"))
    teile.append(quader("tuer", (0.53, 0.04, 0.95), (0.0, -0.295, 0.75), "kuehlschrank_tuer"))
    teile.append(quader("griff", (0.03, 0.03, 0.36), (0.20, -0.33, 0.85), "rahmen"))
    teile.append(quader("sockel", (0.55, 0.55, 0.05), (0.0, 0.0, 0.025), "rahmen"))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_innenwand": innenwand_segment,
    "raum_innentuer": innentuer,
    "raum_pinnwand": pinnwand,
    "raum_kuehlschrank": kuehlschrank,
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
    print("=== RAUMMODULE WELT 4 -- BUERO ===")
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
