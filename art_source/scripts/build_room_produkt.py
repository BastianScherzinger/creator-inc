"""Erzeugt die Raummodule fuer Welt 5 "produkt" -- den Baukasten fuer die
fuenfte Karte des Spiels (docs/WELTEN.md, Abschnitt "Welt 5 -- produkt";
docs/STORY.md, "AKT 5 -- Das Produkt").

Aufruf:
    blender --background --python art_source/scripts/build_room_produkt.py

DAS ENDE DES BOGENS BEGINNT HIER. Welt 3 und 4 waren derselbe Beruf in
groesseren Raeumen -- Parkett, helle Buerowand, Regal und Pinnwand. Welt 5
bricht bewusst mit dieser Materialsprache, weil die Story es verlangt: "Was,
wenn ich es nur einmal baue?" ist kein Buero-Gefuehl mehr, sondern ein
Loft-Gefuehl. Drei Entscheidungen tragen das:
  1. Sichtbeton statt Parkett -- kuehles Grau statt warmem Holz, grosse
     glatte Flaechen statt kleinteiliger Dielenoptik.
  2. Ein extrem hohes Fensterband -- die Oeffnung reicht fast vom Boden bis
     zur Decke (0,20 bis 2,05 statt 0,60 bis 1,92 wie in Welt 3/4), mit einem
     Sprossenraster aus zwei Querriegeln: das liest sich sofort als
     Industriefenster, nicht als aufgehuebschtes Buerofenster.
  3. Ein Stahltraeger unter der Decke (raum_traeger) -- das Detail, das ein
     Loft erst zum Loft macht. Er haengt sichtbar unter der Decke statt in
     der Wand zu stecken, weil ein Loft seine Tragstruktur zeigt statt sie
     zu verkleiden.

Zwei weitere neue Module tragen die Szene aus docs/WELTEN.md woertlich:
raum_serverschrank ("Bildschirme") und raum_stadtkarte ("eine Karte mit
Staedtenamen, auf der laufend etwas aufleuchtet, ohne dass jemand klickt").
Die Stadtkarte ist deshalb das einzige Modul im ganzen Spiel mit einem
tatsaechlich leuchtenden Material (Emission) -- jedes andere Bildschirm-
Material in jeder anderen Welt ist bewusst "aus" (dunkles, kuehles Glas), weil
dort niemand zusieht. Hier soll er, ohne dass jemand klickt.

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
# Der Sprung zu Welt 3/4 ist Absicht (siehe Modulkopf): kuehles Beton-Grau
# statt warmem Holzton, damit der Unterschied auf einem Standbild sofort
# sichtbar ist, ganz ohne Text.
PALETTE = {
    # Sichtbeton statt Parkett -- neutrales, leicht kuehles Grau (R < G < B),
    # zwei Toene fuer die grossen Estrichfelder plus ein hellerer, wärmerer
    # Laufweg (mehr begangen, mehr abgerieben).
    "boden_a":    (0.279, 0.302, 0.325, 1.0),
    "boden_b":    (0.148, 0.164, 0.181, 1.0),
    "boden_weg":  (0.428, 0.401, 0.349, 1.0),
    # Gestrichene Loft-Wand -- kuehler und heller als die Buerowand aus Welt
    # 3/4, aber kein reines Weiss (ein reines Weiss wuerde nach Galerie statt
    # nach benutztem Loft aussehen).
    "wand":       (0.325, 0.349, 0.388, 1.0),
    "wand_unten": (0.043, 0.047, 0.056, 1.0),
    # Globaler Rahmenton wie in jeder anderen Welt uebernommen -- Fenster-
    # und Tuerrahmen bleiben Metall, das ist ueberall dasselbe Material.
    "rahmen":     (0.557, 0.592, 0.659, 1.0),
    # Stahltraeger -- dunkles, warmes Eisen statt glaenzendem Buero-Metall.
    "traeger":    (0.029, 0.026, 0.023, 1.0),
    # Serverschrank: fast schwarzer Korpus, minimal hellere Frontklappe --
    # zwei Toene reichen (R2), der Schrank soll ein Moebel sein, kein Bild.
    "schrank_korpus": (0.008, 0.009, 0.009, 1.0),
    "schrank_front":  (0.018, 0.019, 0.020, 1.0),
    # Zwei kleine Statusleuchten -- gesaettigt, weil sie tatsaechlich
    # antippbar wirken sollen (ART_DIRECTION R3 gilt fuer Deko genauso wie
    # fuer echte UI: Saettigung bleibt seltenen Ausnahmen vorbehalten, aber
    # ein Blink-LED ist so eine Ausnahme).
    "led_gruen":  (0.015, 0.699, 0.071, 1.0),
    "led_amber":  (0.699, 0.173, 0.001, 1.0),
    # Stadtkarte: fast schwarze Flaeche (der Bildschirm ist an, aber dunkel
    # hinterlegt wie jede Karten-App bei Nacht) und ein gesaettigter
    # Cyan-Gruenton fuer die Punkte -- Basisfarbe UND separate Emission
    # (siehe material_leuchtend).
    "karte_flaeche": (0.0, 0.001, 0.001, 1.0),
    "karte_punkt":       (0.006, 0.388, 0.268, 1.0),
    "karte_punkt_glut":  (0.001, 0.893, 0.531, 1.0),
}

AUSGABE = "project/assets/room/produkt"


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
    """Wie material(), aber mit echter Emission.

    Nur die Stadtkarte (Auftrag: "auf der laufend etwas aufleuchtet, ohne
    dass jemand klickt") bekommt dieses Material. Jeder andere Bildschirm im
    Spiel ist als "aus" gebaut -- dunkles, leicht blaeuliches Glas ohne
    Emission --, weil dort niemand zusieht. Die Karte ist die einzige
    Ausnahme, und die Ausnahme ist der ganze Punkt der Szene."""
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = PALETTE[name]
        bsdf.inputs["Roughness"].default_value = 0.6
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
# Zwei Estrichfelder pro Modul -- keine Dielenoptik mehr, Sichtbeton hat keine
# Maserung. Die Zweiteilung bleibt trotzdem bestehen, weil sie die einzige
# Quelle fuer die leichte Fugen-/Schattenlinie zwischen den beiden Feldern
# ist, die eine grossflaechige Estrichflaeche erst als verlegtes Feld statt
# als eine einzige texturlose Platte lesbar macht.

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


def _felder(mat_name):
    teile = []
    tiefen = (-0.245, 0.245)
    for i, y in enumerate(tiefen):
        teile.append(quader("feld_%d" % i, (0.98, 0.485, 0.03), (0.0, y, 0.0), mat_name))
    return verbinden(teile, "boden")


def fliese_a():
    return _felder("boden_a")


def fliese_b():
    return _felder("boden_b")


def fliese_weg():
    """Heller abgeriebener Estrich fuer die Laufwege -- derselbe Gedanke wie
    in jeder anderen Welt, nur auf Beton statt Parkett oder Laminat."""
    return _felder("boden_weg")


# --- Wandmodule ----------------------------------------------------------------
# Struktur wie in jeder anderen Welt (Wiedererkennung ist Absicht), nur Farbe
# und Fenstermodul unterscheiden sich deutlich -- siehe Modulkopf.

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
    """Wandsegment mit Tuerdurchgang, mit Sturz und Rahmen."""
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
    """Industriefenster -- die Oeffnung reicht fast vom Boden bis zur Decke
    (0,20 bis 2,05 statt 0,60 bis 1,92 wie in Welt 3/4) und wird von zwei
    Querriegeln in drei Felder geteilt. Das ist der Unterschied zwischen
    einem Buerofenster und einem Loft-Fenster: nicht die Groesse allein,
    sondern das Sprossenraster, das man aus jedem Fabrikloft kennt."""
    teile = []
    teile.append(quader("wand_unter", (1.0, 0.14, 0.20), (0.0, 0.0, 0.10), "wand"))
    teile.append(quader("sockelleiste", (1.0, 0.20, 0.14), (0.0, 0.0, 0.07), "wand_unten"))
    teile.append(quader("wand_ueber", (1.0, 0.14, 0.15), (0.0, 0.0, 2.125), "wand"))
    teile.append(quader("fensterbrett", (1.0, 0.26, 0.05), (0.0, 0.0, 0.20), "rahmen"))
    teile.append(quader("fensterrahmen_mitte", (0.07, 0.16, 1.85), (0.0, 0.0, 1.125), "rahmen"))
    teile.append(quader("fensterrahmen_quer_a", (1.00, 0.16, 0.05), (0.0, 0.0, 0.75), "rahmen"))
    teile.append(quader("fensterrahmen_quer_b", (1.00, 0.16, 0.05), (0.0, 0.0, 1.50), "rahmen"))
    return teile


# --- Zusaetzliche Raummodule -----------------------------------------------
# Alle drei stehen woertlich in docs/WELTEN.md: Serverschrank, Stadtkarte,
# Deckentraeger. Sie tragen das "Hebel"-Gefuehl (dieselbe Arbeit, hundertfach
# ausgespielt) sichtbar in den Raum, ohne ein einziges Wort zu benutzen.

def serverschrank():
    """Serverschrank mit drei Trennleisten (angedeutete Rack-Einheiten) und
    drei Statusleuchten. Details bleiben abstrakt (R1: Silhouette statt
    Detailverfeinerung) -- die Leuchten allein sagen 'hier laeuft etwas',
    ganz ohne lesbare Beschriftung."""
    teile = []
    teile.append(quader("korpus", (0.60, 0.55, 1.90), (0.0, 0.0, 0.95), "schrank_korpus"))
    teile.append(quader("front", (0.56, 0.04, 1.86), (0.0, -0.255, 0.95), "schrank_front"))
    for i, z in enumerate((0.55, 0.95, 1.35)):
        teile.append(quader("trennleiste_%d" % i, (0.56, 0.05, 0.02), (0.0, -0.28, z), "rahmen"))
    for i, (x, mat) in enumerate(((-0.18, "led_gruen"), (0.0, "led_gruen"), (0.18, "led_amber"))):
        teile.append(quader("led_%d" % i, (0.03, 0.02, 0.03), (x, -0.28, 1.72), mat))
    return teile


def stadtkarte():
    """Wandhaengender Bildschirm mit einer Karte -- fuenf Punkte in
    unregelmaessigem Muster leuchten, keiner davon reagiert auf einen Klick
    (Auftrag: 'ohne dass jemand klickt'). Struktur wie ein Whiteboard/eine
    Pinnwand (Flaeche plus Rahmen), aber die Flaeche ist ein Bildschirm, kein
    Papier, und leuchtet deshalb tatsaechlich (material_leuchtend)."""
    teile = []
    teile.append(quader("flaeche", (0.90, 0.05, 0.62), (0.0, 0.0, 1.30), "karte_flaeche"))
    teile.append(quader("rahmen_o", (0.94, 0.07, 0.04), (0.0, 0.0, 1.63), "rahmen"))
    teile.append(quader("rahmen_u", (0.94, 0.07, 0.04), (0.0, 0.0, 0.97), "rahmen"))
    teile.append(quader("rahmen_l", (0.04, 0.07, 0.66), (-0.45, 0.0, 1.30), "rahmen"))
    teile.append(quader("rahmen_r", (0.04, 0.07, 0.66), (0.45, 0.0, 1.30), "rahmen"))
    punkte = ((-0.30, 1.44), (-0.08, 1.20), (0.14, 1.46), (0.30, 1.16), (0.02, 1.34))
    for i, (x, z) in enumerate(punkte):
        teile.append(quader_leuchtend("punkt_%d" % i, (0.035, 0.02, 0.035), (x, -0.035, z),
                                       "karte_punkt", 2.5))
    return teile


def traeger():
    """Ein Meter Stahltraeger unter der Decke, als I-Profil angedeutet
    (Ober-/Untergurt plus Steg): Reihen davon machen aus einem Raum mit
    Aussenwaenden ein Loft. Er haengt sichtbar unter der Decke (Oberkante
    bei 2,20 -- der Traeger beginnt darunter), weil ein Loft seine
    Tragstruktur zeigt statt sie in der Wand zu verstecken."""
    teile = []
    teile.append(quader("gurt_oben", (0.94, 0.28, 0.05), (0.0, 0.0, 2.150), "traeger"))
    teile.append(quader("steg", (0.94, 0.05, 0.20), (0.0, 0.0, 2.000), "traeger"))
    teile.append(quader("gurt_unten", (0.94, 0.24, 0.05), (0.0, 0.0, 1.875), "traeger"))
    for x in (-0.44, 0.44):
        teile.append(quader("niete_%d" % (0 if x < 0 else 1), (0.03, 0.03, 0.03), (x, 0.0, 2.150), "rahmen"))
    return teile


MODULE = {
    "raum_fliese_a": fliese_a,
    "raum_fliese_b": fliese_b,
    "raum_fliese_weg": fliese_weg,
    "raum_wand": wand_segment,
    "raum_wand_ecke": wand_ecke,
    "raum_wand_tuer": wand_tuer,
    "raum_wand_fenster": wand_fenster,
    "raum_serverschrank": serverschrank,
    "raum_stadtkarte": stadtkarte,
    "raum_traeger": traeger,
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
    print("=== RAUMMODULE WELT 5 -- PRODUKT ===")
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
