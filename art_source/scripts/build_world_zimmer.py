"""Erzeugt die Kulisse fuer Welt 1 "zimmer" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 1 -- zimmer").

Aufruf:
    blender --background --python art_source/scripts/build_world_zimmer.py

Die Kulisse macht aus dem leeren Raum ein bewohntes Zimmer. Sie ist reine
Deko -- kein Spielsystem haengt daran. Deshalb liegt sie unter
assets/world/<welt>/, genau wie beim Amt-Vorbild (build_world_amt.py).

Die Requisiten stammen aus docs/WELTEN.md:
    "14 Quadratmeter. Eine Matratze, ein Klapptisch, ein Laptop mit lauter
     Lueftung. Die Schreibtischlampe steht falsch herum, weil sie so als
     Ringlicht taugt."

Gefuehl laut Spezifikation: eng, dunkel, aber nicht traurig. Es ist der
Anfang, nicht das Ende -- deshalb bleibt die Pflanze hier "gerade so am
Leben", waehrend ihr Gegenstueck im Amt (welt_pflanze dort) bereits
vertrocknet ist. Zwei verschiedene Geschichten mit demselben Requisit.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Die Werte unten sind bereits so zurueckgerechnet -- siehe build_world_amt.py,
# dort ist derselbe Fehler drei Mal in Folge passiert.
PALETTE = {
    "matratze":     (0.052, 0.056, 0.071, 1.0),   # abgewetzter grau-blauer Bezug
    "decke":        (0.106, 0.082, 0.056, 1.0),   # waermer als die Matratze
    "holz_wackel":  (0.056, 0.032, 0.015, 1.0),   # billiges Holzdekor, Klapptisch
    "metall":       (0.173, 0.181, 0.199, 1.0),   # Tisch-/Stuhlgestell, Regalfach-Inhalt
    "stuhl":        (0.013, 0.011, 0.015, 1.0),   # dunkles Polster
    "pappe":        (0.082, 0.047, 0.023, 1.0),   # Wellpappe, hell
    "pappe_dunkel": (0.029, 0.018, 0.009, 1.0),   # Wellpappe, Schattenseite/Innenflaeche
    "gruen_knapp":  (0.043, 0.071, 0.023, 1.0),   # gedaempftes Gruen -- kein Vollgruen
    "erde":         (0.015, 0.009, 0.005, 1.0),   # Blumenerde
    "regal_holz":   (0.029, 0.020, 0.011, 1.0),   # dunkles Pressspan-Holz
}

AUSGABE = "project/assets/world/zimmer"


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
    """Matratze direkt auf dem Boden -- kein Bettgestell, das waere schon ein
    Moebelstueck und wuerde das Zimmer zu eingerichtet wirken lassen. Decke
    und Kissen liegen schraeg und ungleichmaessig: ein sauber gefaltetes
    Rechteck saehe aus wie ein Katalogfoto, keine improvisierte Schlafstelle."""
    teile = []
    teile.append(quader("matratze_koerper", (2.00, 1.30, 0.22), (0.0, 0.0, 0.11), "matratze"))
    teile.append(quader("kissen", (0.55, 0.40, 0.14), (-0.65, 0.0, 0.29), "decke"))
    teile.append(quader("decke_haupt", (1.55, 1.10, 0.10), (0.25, 0.0, 0.27), "decke", (0.0, 0.0, 4.0)))
    teile.append(quader("decke_wulst", (0.50, 1.05, 0.16), (0.85, 0.0, 0.30), "decke", (0.0, 0.0, -6.0)))
    return teile


def klapptisch():
    """Wackeliger Klapptisch -- ein Bein leicht schief, das ist die ganze
    Pointe. Vier identische Beine waeren ein Moebelkatalog, kein Alltag
    (ART_DIRECTION 7.1: genau ein Merkmal je Objekt, nicht mehrere)."""
    teile = []
    teile.append(quader("platte", (1.00, 0.60, 0.04), (0.0, 0.0, 0.72), "holz_wackel"))
    beine = ((-0.42, -0.24), (0.42, -0.24), (-0.42, 0.24), (0.42, 0.24))
    for i, (x, y) in enumerate(beine):
        dreh = (2.0, 0.0, 0.0) if i == 3 else (0.0, 0.0, 0.0)  # das wackelige Bein
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.70), (x, y, 0.35), "metall", dreh))
    return teile


def stuhl():
    """Buerostuhl mit schiefer Lehne -- das Gelenk ist ausgeleiert und haelt
    den Winkel nicht mehr. Der Sitz selbst bleibt gerade: sonst sieht es nach
    einem umgekippten Stuhl aus statt nach einem kaputten Gelenk."""
    teile = []
    teile.append(quader("sitz", (0.46, 0.46, 0.06), (0.0, 0.0, 0.46), "stuhl"))
    teile.append(quader("lehne", (0.42, 0.06, 0.50), (0.0, -0.22, 0.75), "stuhl", (8.0, 0.0, 0.0)))
    teile.append(zylinder("saeule", 0.04, 0.40, (0.0, 0.0, 0.23), "metall"))
    teile.append(quader("fuss_x", (0.60, 0.06, 0.04), (0.0, 0.0, 0.03), "metall"))
    teile.append(quader("fuss_y", (0.06, 0.60, 0.04), (0.0, 0.0, 0.03), "metall"))
    return teile


def kiste():
    """Umzugskiste als Nachttisch -- nie ausgepackt, jetzt Moebelstueck. Die
    Klappen stehen noch halb offen, das erzaehlt mehr als ein sauber
    geschlossener Wuerfel und kostet keine zusaetzliche Geometrie, nur eine
    Rotation."""
    teile = []
    teile.append(quader("koerper", (0.42, 0.42, 0.42), (0.0, 0.0, 0.21), "pappe"))
    teile.append(quader("klappe_a", (0.40, 0.20, 0.03), (0.0, -0.10, 0.43), "pappe_dunkel", (10.0, 0.0, 0.0)))
    teile.append(quader("klappe_b", (0.40, 0.20, 0.03), (0.0, 0.10, 0.43), "pappe_dunkel", (-10.0, 0.0, 0.0)))
    return teile


def karton():
    """Flacher Pizzakarton -- der Beweis, dass hier gearbeitet und nicht
    gekocht wird. Der Deckel steht einen Spalt offen, sonst koennte es jede
    beliebige flache Kiste sein."""
    teile = []
    teile.append(quader("boden", (0.34, 0.34, 0.035), (0.0, 0.0, 0.018), "pappe"))
    teile.append(quader("deckel", (0.34, 0.34, 0.02), (0.0, -0.02, 0.05), "pappe_dunkel", (3.0, 0.0, 0.0)))
    return teile


def pflanze():
    """Pflanze, der es gerade so reicht. Anders als der vertrocknete
    Gummibaum im Amt (welt_pflanze dort haengt mit 68-84 Grad fast
    senkrecht) nicken diese Blaetter nur -- 28 bis 38 Grad. Genug Gruen, um
    nicht aufgegeben zu haben, aber weit weg von ueppig."""
    teile = []
    teile.append(zylinder("topf", 0.16, 0.24, (0.0, 0.0, 0.12), "erde"))
    teile.append(zylinder("topf_rand", 0.18, 0.04, (0.0, 0.0, 0.25), "regal_holz"))
    teile.append(zylinder("stamm", 0.025, 0.50, (0.0, 0.0, 0.50), "gruen_knapp", 6))
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (0,   0.66, 0.22, 34.0),
            (90,  0.60, 0.20, 28.0),
            (180, 0.70, 0.24, 38.0),
            (270, 0.62, 0.20, 30.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.10, 0.02),
                            (math.cos(rad) * 0.06, math.sin(rad) * 0.06, hoehe),
                            "gruen_knapp", (0.0, neigung, winkel)))
    return teile


def regal():
    """Schmales Regal, halb leer -- die oberen Faecher tragen etwas, das
    unterste bleibt frei. Das erzaehlt 'gerade erst angefangen', ganz ohne
    Text (ART_DIRECTION R4: Fortschritt ist sichtbar, nicht numerisch --
    hier steht dasselbe Prinzip schon vor dem ersten Ausbau)."""
    teile = []
    for x in (-0.28, 0.28):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.04, 0.28, 1.20), (x, 0.0, 0.60), "regal_holz"))
    for i, z in enumerate((0.02, 0.42, 0.82, 1.18)):
        teile.append(quader("boden_%d" % i, (0.60, 0.28, 0.03), (0.0, 0.0, z), "regal_holz"))
    teile.append(quader("gegenstand_a", (0.18, 0.16, 0.20), (-0.15, 0.0, 0.52), "pappe"))
    teile.append(quader("gegenstand_b", (0.14, 0.14, 0.34), (0.16, 0.0, 0.99), "metall"))
    return teile


REQUISITEN = {
    "welt_matratze": matratze,
    "welt_klapptisch": klapptisch,
    "welt_stuhl": stuhl,
    "welt_kiste": kiste,
    "welt_karton": karton,
    "welt_pflanze": pflanze,
    "welt_regal": regal,
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
    print("=== KULISSE WELT 1 -- ZIMMER ===")
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
