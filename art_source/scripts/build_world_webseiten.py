"""Erzeugt die Kulisse fuer Welt 3 "webseiten" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 3 -- webseiten").

Aufruf:
    blender --background --python art_source/scripts/build_world_webseiten.py

Reine Deko wie in Welt 1 (build_world_zimmer.py) -- kein Spielsystem haengt
daran. Deshalb liegt sie unter assets/world/<welt>/.

Die Requisiten stammen aus docs/WELTEN.md und docs/STORY.md:
    "Ein Schreibtisch am Fenster. Zwei Bildschirme, eine Tastatur, die nicht
     mehr wackelt. An der Wand haengen ausgedruckte Screenshots von Seiten,
     die online sind."

Gefuehl laut Spezifikation: Beruf. Es ist Arbeit, und sie traegt. Anders als
im Zimmer (Klapptisch, Umzugskiste, Pizzakarton) ist hier alles einmal
gekauft und bleibt stehen -- kein wackeliges Bein, kein schiefes Gelenk mehr.
Der Rollcontainer, das Ordnerregal und der Schreibtisch sind die sichtbare
Antwort auf die Frage "Beruf oder Zufall?" aus AKT 3 (docs/STORY.md).
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
# Die Werte unten sind bereits so zurueckgerechnet -- dieselbe Rueckrechnung
# wie in build_room_webseiten.py, damit Moebel und Raum zueinander passen.
PALETTE = {
    "holz_schreibtisch": (0.325, 0.234, 0.163, 1.0),  # helles Buero-Holz, IKEA-hell
    "bein_metall":       (0.557, 0.592, 0.659, 1.0),  # derselbe globale Rahmenton wie im Raum
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # dunkles Monitorgehaeuse
    "bildschirm_glas":   (0.008, 0.010, 0.014, 1.0),  # Bildschirm aus, leicht blaeulich
    "tastatur":          (0.218, 0.218, 0.214, 1.0),  # heller Kunststoff
    "container_korpus":  (0.388, 0.388, 0.380, 1.0),  # heller Metall-/Laminatkorpus
    "container_front":   (0.268, 0.268, 0.260, 1.0),  # Schubladenfront, etwas dunkler
    "regal_holz":        (0.300, 0.210, 0.126, 1.0),  # helles Regalholz, wie im Raum-Regal
    "ordner":            (0.596, 0.480, 0.330, 1.0),  # Aktenordner -- Amtsbeige-Signaturfarbe
    "ordner_akzent":     (0.090, 0.120, 0.173, 1.0),  # vereinzelte dunkelblaue Ruecken
    "gruen_gesund":      (0.094, 0.268, 0.080, 1.0),  # kraeftiges Gruen -- der Pflanze geht es gut
    "topf":              (0.268, 0.147, 0.113, 1.0),  # Terrakotta-Topf
    "topf_rand":         (0.099, 0.054, 0.042, 1.0),  # Topfrand, dunkler
    "erde":              (0.015, 0.009, 0.005, 1.0),  # Blumenerde
    "rahmen_bild":       (0.029, 0.027, 0.025, 1.0),  # dunkler, schmaler Bilderrahmen
    "ausdruck_papier":   (0.900, 0.870, 0.800, 1.0),  # ausgedrucktes Blatt, hell
    "ausdruck_inhalt":   (0.200, 0.240, 0.268, 1.0),  # abstrakter Screenshot-Inhalt, kuehl
    "stuhl_polster":     (0.056, 0.052, 0.062, 1.0),  # Buerostuhl-Polster, dunkel neutral
    "tasse":             (0.268, 0.268, 0.260, 1.0),  # Kaffeetasse auf dem Schreibtisch
}

AUSGABE = "project/assets/world/webseiten"


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

def schreibtisch():
    """Schreibtisch mit zwei Monitoren, Tastatur, Maus und einer Tasse --
    docs/WELTEN.md woertlich: 'Zwei Bildschirme, eine Tastatur, die nicht
    mehr wackelt.' Vier gleich lange Beine sind hier kein Fehler wie beim
    Klapptisch im Zimmer, sondern die Pointe: nichts wackelt mehr."""
    teile = []
    teile.append(quader("platte", (1.60, 0.75, 0.04), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    beine = ((-0.74, -0.33), (0.74, -0.33), (-0.74, 0.33), (0.74, 0.33))
    for i, (x, y) in enumerate(beine):
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.70), (x, y, 0.35), "bein_metall"))
    for i, x in enumerate((-0.30, 0.30)):
        teile.append(quader("monitor_fuss_%d" % i, (0.10, 0.08, 0.10), (x, -0.20, 0.79), "bildschirm_rahmen"))
        teile.append(quader("monitor_screen_%d" % i, (0.46, 0.03, 0.30), (x, -0.28, 1.02), "bildschirm_glas"))
    teile.append(quader("tastatur", (0.34, 0.13, 0.02), (0.0, 0.18, 0.745), "tastatur"))
    teile.append(quader("maus", (0.05, 0.08, 0.02), (0.22, 0.18, 0.745), "tastatur"))
    teile.append(zylinder("tasse", 0.035, 0.08, (-0.55, 0.20, 0.78), "tasse"))
    return teile


def rollcontainer():
    """Rollcontainer unter dem Schreibtisch -- drei Schubladen, vier Rollen.
    Er ist die sichtbare Antwort darauf, dass hier jetzt Unterlagen sortiert
    statt gestapelt werden."""
    teile = []
    teile.append(quader("korpus", (0.42, 0.55, 0.58), (0.0, 0.0, 0.31), "container_korpus"))
    for i, z in enumerate((0.14, 0.33, 0.52)):
        teile.append(quader("front_%d" % i, (0.38, 0.03, 0.16), (0.0, -0.29, z), "container_front"))
        teile.append(quader("griff_%d" % i, (0.14, 0.02, 0.02), (0.0, -0.31, z), "bein_metall"))
    for i, (x, y) in enumerate(((-0.17, -0.22), (0.17, -0.22), (-0.17, 0.22), (0.17, 0.22))):
        teile.append(zylinder("rolle_%d" % i, 0.03, 0.04, (x, y, 0.03), "bein_metall", 6))
    return teile


def ordnerregal():
    """Freistehendes Ordnerregal -- deutlich groesser als das raum_regal an
    der Wand. Ein Fach bleibt bewusst frei: volle Regale wirken zugestellt,
    nicht aufgeraeumt (dieselbe Regel wie beim raum_regal)."""
    teile = []
    for x in (-0.32, 0.32):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.05, 0.32, 1.60), (x, 0.0, 0.80), "regal_holz"))
    for i, z in enumerate((0.02, 0.42, 0.82, 1.22, 1.58)):
        teile.append(quader("boden_%d" % i, (0.62, 0.32, 0.03), (0.0, 0.0, z), "regal_holz"))
    # Zwei volle Faecher, ein leeres obendrauf -- je drei Ordner, einer davon
    # in einem gedaempften Blauton fuer etwas Abwechslung im Regal.
    faecher = (0.42, 0.82)
    for f, z in enumerate(faecher):
        for i, x in enumerate((-0.18, 0.0, 0.18)):
            mat = "ordner_akzent" if (f == 0 and i == 1) else "ordner"
            teile.append(quader("ordner_%d_%d" % (f, i), (0.10, 0.28, 0.36), (x, 0.0, z + 0.205), mat))
    return teile


def pflanze():
    """Pflanze, der es gut geht -- Gegenstueck zur knapp ueberlebenden
    Pflanze im Zimmer. Die Blaetter stehen aufrechter (15-25 statt 28-38
    Grad Neigung) und es sind mehr davon: derselbe Gegenstand, ein
    sichtbar anderer Zustand, ganz ohne Text (ART_DIRECTION R4)."""
    teile = []
    teile.append(zylinder("topf", 0.18, 0.28, (0.0, 0.0, 0.14), "topf"))
    teile.append(zylinder("topf_rand", 0.20, 0.04, (0.0, 0.0, 0.29), "topf_rand"))
    teile.append(zylinder("erde", 0.17, 0.03, (0.0, 0.0, 0.275), "erde"))
    teile.append(zylinder("stamm", 0.025, 0.55, (0.0, 0.0, 0.565), "gruen_gesund", 6))
    for i, (winkel, hoehe, laenge, neigung) in enumerate([
            (0,   0.78, 0.26, 18.0),
            (60,  0.74, 0.24, 22.0),
            (120, 0.80, 0.27, 16.0),
            (180, 0.76, 0.25, 24.0),
            (240, 0.72, 0.23, 20.0),
            (300, 0.78, 0.26, 18.0)]):
        rad = math.radians(winkel)
        teile.append(quader("blatt_%d" % i, (laenge, 0.10, 0.02),
                            (math.cos(rad) * 0.06, math.sin(rad) * 0.06, hoehe),
                            "gruen_gesund", (0.0, neigung, winkel)))
    return teile


def bild():
    """Gerahmter Ausdruck an der Wand -- ein Screenshot einer Seite, die
    online ist (docs/WELTEN.md). Der Inhalt bleibt abstrakt (Kopfzeile +
    Flaeche), keine lesbare Schrift und keine thematische Rollenbenennung --
    die Silhouette einer Webseite genuegt, um die Aussage zu tragen."""
    teile = []
    teile.append(quader("rahmen", (0.46, 0.03, 0.36), (0.0, 0.0, 0.0), "rahmen_bild"))
    teile.append(quader("papier", (0.40, 0.01, 0.30), (0.0, -0.02, 0.0), "ausdruck_papier"))
    teile.append(quader("kopfzeile", (0.34, 0.005, 0.04), (0.0, -0.03, 0.115), "ausdruck_inhalt"))
    teile.append(quader("inhalt", (0.34, 0.005, 0.16), (0.0, -0.03, -0.02), "ausdruck_inhalt"))
    return teile


def stuhl():
    """Buerostuhl mit Armlehnen, gerader Lehne -- kein ausgeleiertes Gelenk
    mehr wie im Zimmer. Die Armlehnen sind das einzige neue Merkmal
    gegenueber dem Zimmer-Stuhl und genuegen, um 'aufgestiegen' zu sagen."""
    teile = []
    teile.append(quader("sitz", (0.46, 0.46, 0.06), (0.0, 0.0, 0.46), "stuhl_polster"))
    teile.append(quader("lehne", (0.42, 0.06, 0.50), (0.0, -0.22, 0.75), "stuhl_polster"))
    teile.append(zylinder("saeule", 0.04, 0.40, (0.0, 0.0, 0.23), "bein_metall"))
    teile.append(quader("fuss_x", (0.60, 0.06, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    teile.append(quader("fuss_y", (0.06, 0.60, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    for x in (-0.24, 0.24):
        teile.append(quader("armlehne", (0.06, 0.30, 0.05), (x, -0.05, 0.58), "bein_metall"))
    return teile


REQUISITEN = {
    "welt_schreibtisch": schreibtisch,
    "welt_rollcontainer": rollcontainer,
    "welt_ordnerregal": ordnerregal,
    "welt_pflanze": pflanze,
    "welt_bild": bild,
    "welt_stuhl": stuhl,
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
    print("=== KULISSE WELT 3 -- WEBSEITEN ===")
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
