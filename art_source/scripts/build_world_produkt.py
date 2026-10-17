"""Erzeugt die Kulisse fuer Welt 5 "produkt" als glTF-Dateien
(docs/WELTEN.md, Abschnitt "Welt 5 -- produkt"; docs/STORY.md, "AKT 5 -- Das
Produkt").

Aufruf:
    blender --background --python art_source/scripts/build_world_produkt.py

Reine Deko wie in jeder anderen Welt -- kein Spielsystem haengt daran.
Deshalb liegt sie unter assets/world/<welt>/.

Schreibtisch und Stuhl sind woertlich aus build_world_webseiten.py /
build_world_buero.py uebernommen (Wiedererkennung ist Absicht, ART_DIRECTION
Abschnitt 9) -- dasselbe erzaehlerische Argument wie beim Traeger im Raum-
Skript: Welt 5 ist "dieselbe Arbeit, hundertfach ausgespielt" (docs/WELTEN.md).
Der Arbeitsplatz selbst hat sich nicht veraendert, nur seine Umgebung. Neu
sind welt_sofa (jetzt wird auch gewohnt, nicht nur gearbeitet), welt_
monitorwand ("zu viele Bildschirme" woertlich aus der Raumbeschreibung) und
welt_kiste -- anders als die halb ausgepackte Umzugskiste aus Welt 1 ist das
hier eine geschlossene, verklebte Versandkiste: kein Einzug mehr, sondern
Auslieferung in Stueckzahl.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- hier ist schon einmal viel Zeit verloren gegangen:
# glTF speichert baseColorFactor LINEAR, Godot zeigt albedo_color in sRGB.
# Ein Wert von 0,10 hier erscheint im Spiel als 0,35 Helligkeit (0,10^(1/2,2)).
# Wer die gewuenschte Bildschirmhelligkeit s kennt, rechnet linear = s^2,2.
#
# Schreibtisch/Stuhl-Toene sind woertlich aus build_world_webseiten.py
# uebernommen (nicht neu gerechnet) -- nur die drei neuen Requisiten
# bekommen eigene, frisch gerechnete Farben.
PALETTE = {
    "holz_schreibtisch": (0.325, 0.234, 0.163, 1.0),  # unveraendert aus Welt 3/4
    "bein_metall":       (0.557, 0.592, 0.659, 1.0),  # globaler Rahmenton, unveraendert
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # unveraendert
    "bildschirm_glas":   (0.008, 0.010, 0.014, 1.0),  # unveraendert -- Bildschirm aus
    "tastatur":          (0.218, 0.218, 0.214, 1.0),  # unveraendert
    "stuhl_polster":     (0.056, 0.052, 0.062, 1.0),  # unveraendert
    "tasse":             (0.268, 0.268, 0.260, 1.0),  # unveraendert
    "gruen_gesund":      (0.094, 0.268, 0.080, 1.0),  # unveraendert -- der Pflanze geht es gut
    "topf":              (0.268, 0.147, 0.113, 1.0),  # unveraendert
    "topf_rand":         (0.099, 0.054, 0.042, 1.0),  # unveraendert
    "erde":              (0.015, 0.009, 0.005, 1.0),  # unveraendert
    # Neu: Sofa -- gedaempftes Anthrazit mit leichtem Kaltton (s=0,28/0,26/
    # 0,30), Wohnmoebel statt Buero-Polster, deshalb ein eigener Ton statt
    # Wiederverwendung von stuhl_polster.
    "sofa_polster": (0.061, 0.052, 0.071, 1.0),
    # Neu: Monitorwand -- dieselben Bildschirm-Toene wie oben fuer die
    # meisten Panels, plus ein einzelnes "an"-Panel (kuehles Blauweiss),
    # damit die Wand nach Aktivitaet aussieht, ohne der Stadtkarte im Raum
    # die Pointe zu stehlen (die bleibt das einzige Modul mit Emission).
    "monitor_an": (0.047, 0.099, 0.268, 1.0),
    # Neu: Versandkiste -- helles Kartonbraun plus ein etwas hellerer,
    # neutralerer Ton fuer das Klebeband quer ueber dem Deckel.
    "kiste_pappe": (0.349, 0.279, 0.181, 1.0),
    "kiste_band":  (0.485, 0.428, 0.268, 1.0),
}

AUSGABE = "project/assets/world/produkt"


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
    """Schreibtisch mit zwei Monitoren -- unveraendert aus Welt 3/4
    uebernommen (Modulkopf-Kommentar): derselbe Arbeitsplatz, jetzt
    vervielfacht in einem Loft statt in einem Buero."""
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


def stuhl():
    """Buerostuhl mit Armlehnen -- unveraendert aus Welt 3/4 uebernommen."""
    teile = []
    teile.append(quader("sitz", (0.46, 0.46, 0.06), (0.0, 0.0, 0.46), "stuhl_polster"))
    teile.append(quader("lehne", (0.42, 0.06, 0.50), (0.0, -0.22, 0.75), "stuhl_polster"))
    teile.append(zylinder("saeule", 0.04, 0.40, (0.0, 0.0, 0.23), "bein_metall"))
    teile.append(quader("fuss_x", (0.60, 0.06, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    teile.append(quader("fuss_y", (0.06, 0.60, 0.04), (0.0, 0.0, 0.03), "bein_metall"))
    for x in (-0.24, 0.24):
        teile.append(quader("armlehne", (0.06, 0.30, 0.05), (x, -0.05, 0.58), "bein_metall"))
    return teile


def sofa():
    """Ein Sofa im Arbeitsraum -- das erste im ganzen Spiel (docs/WELTEN.md:
    'Loft'). Es sagt: hier wird nicht nur gearbeitet, hier wird auch
    gewohnt. Ein einzelnes Kissen genuegt als erzaehlendes Detail (ART_
    DIRECTION 7.1), mehr braucht die Silhouette nicht."""
    teile = []
    teile.append(quader("sitzflaeche", (1.20, 0.65, 0.18), (0.0, 0.0, 0.28), "sofa_polster"))
    teile.append(quader("lehne", (1.20, 0.15, 0.45), (0.0, -0.32, 0.55), "sofa_polster"))
    for x in (-0.60, 0.60):
        teile.append(quader("armlehne_%s" % ("l" if x < 0 else "r"),
                             (0.15, 0.65, 0.35), (x, 0.0, 0.37), "sofa_polster"))
    for i, (x, y) in enumerate(((-0.48, -0.28), (0.48, -0.28), (-0.48, 0.28), (0.48, 0.28))):
        teile.append(quader("bein_%d" % i, (0.05, 0.05, 0.16), (x, y, 0.08), "bein_metall"))
    teile.append(quader("kissen", (0.28, 0.10, 0.28), (0.35, -0.05, 0.46), "bildschirm_rahmen", (0.0, 0.0, 12.0)))
    return teile


def monitorwand():
    """Freistehende Bildschirmwand -- 'zu viele Bildschirme' woertlich aus
    docs/WELTEN.md. Sechs Panels auf einer Rueckwand statt vier Rahmenteilen:
    guenstiger in Dreiecken und die Panels selbst tragen die Kontur. Ein
    einzelnes Panel ist 'an' (monitor_an) -- kuehl blau-weiss statt aus --,
    der Rest bleibt dunkel: genug Kontrast, um nach Aktivitaet auszusehen,
    ohne der Stadtkarte im Raum (raum_stadtkarte) die einzige Emission im
    Spiel streitig zu machen."""
    teile = []
    teile.append(quader("rueckwand", (1.50, 0.04, 0.92), (0.0, 0.0, 1.30), "bildschirm_rahmen"))
    positionen = [(x, z) for z in (1.58, 1.30, 1.02) for x in (-0.47, 0.47)]
    for i, (x, z) in enumerate(positionen):
        mat = "monitor_an" if i == 4 else "bildschirm_glas"
        teile.append(quader("panel_%d" % i, (0.44, 0.02, 0.24), (x, -0.03, z), mat))
    teile.append(quader("stuetze_l", (0.05, 0.05, 0.85), (-0.55, 0.30, 0.425), "bein_metall"))
    teile.append(quader("stuetze_r", (0.05, 0.05, 0.85), (0.55, 0.30, 0.425), "bein_metall"))
    teile.append(quader("standfuss", (1.20, 0.30, 0.04), (0.0, 0.30, 0.02), "bein_metall"))
    return teile


def pflanze():
    """Pflanze, der es gut geht -- unveraendert aus Welt 3/4 uebernommen."""
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


def kiste():
    """Geschlossene, verklebte Versandkiste -- der Gegenentwurf zur halb
    offenen Umzugskiste aus Welt 1 (dort: nie ausgepackt, hier: fertig
    verpackt und unterwegs). Zwei Kartons statt einem: das Bild von
    Stueckzahl statt Einzelstueck, mit minimaler zusaetzlicher Geometrie."""
    teile = []
    teile.append(quader("karton_gross", (0.44, 0.44, 0.40), (0.0, 0.0, 0.20), "kiste_pappe"))
    teile.append(quader("band_gross_a", (0.46, 0.06, 0.02), (0.0, 0.0, 0.41), "kiste_band"))
    teile.append(quader("band_gross_b", (0.06, 0.46, 0.02), (0.0, 0.0, 0.41), "kiste_band"))
    teile.append(quader("karton_klein", (0.26, 0.26, 0.24), (0.12, 0.10, 0.52), "kiste_pappe", (0.0, 0.0, 8.0)))
    teile.append(quader("band_klein", (0.28, 0.05, 0.01), (0.12, 0.10, 0.645), "kiste_band", (0.0, 0.0, 8.0)))
    return teile


REQUISITEN = {
    "welt_schreibtisch": schreibtisch,
    "welt_stuhl": stuhl,
    "welt_sofa": sofa,
    "welt_monitorwand": monitorwand,
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
    print("=== KULISSE WELT 5 -- PRODUKT ===")
    gesamt = 0
    for name, bauen in REQUISITEN.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt += dreiecke
        print("  %-22s %2d Teile  ~%4d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, os.path.getsize(pfad) / 1024.0))
    print("")
    print("  %d Requisiten, zusammen ~%d Dreiecke" % (len(REQUISITEN), gesamt))


if __name__ == "__main__":
    main()
