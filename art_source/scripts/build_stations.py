"""Erzeugt die Stationsmodule fuer Welt 1 als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations.py

Drei Stationen, je drei Ausbaustufen -- neun Dateien. Die Stufen bauen
AUFEINANDER AUF: Stufe 2 zeigt das Modul von Stufe 1 plus das neue Teil.
Dadurch sieht der Spieler nicht nur "etwas anderes", sondern "mehr als
vorher" -- Fortschritt statt Austausch (ART_DIRECTION R4).

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3
Dieselbe ID ist in Welt 1 eine Wartebank und in Welt 2 ein Posteingang.
Die Zuordnung steht in data/themes/<welt>/theme.json.

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Eine sitzende Figur ist rund 1,2 Einheiten hoch, ein Tisch 0,75.
"""

import bpy
import os
import math

PALETTE = {
    "moebel":  (0.271, 0.298, 0.361, 1.0),   # #454c5c Grund mittel
    "hell":    (0.557, 0.592, 0.659, 1.0),   # #8e97a8 Grund hell
    "holz":    (0.788, 0.718, 0.604, 1.0),   # #c9b79a Amtsbeige
    "akzent":  (0.949, 0.663, 0.231, 1.0),   # #f2a93b Aktion
    "papier":  (0.961, 0.945, 0.910, 1.0),   # #f5f1e8
    "gruen":   (0.357, 0.451, 0.310, 1.0),   # Gummibaum
}

AUSGABE = "project/assets/stations/amt"


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


def quader(name, groesse, position, mat_name, drehung_z=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = groesse
    if drehung_z:
        obj.rotation_euler = (0.0, 0.0, math.radians(drehung_z))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material(mat_name))
    return obj


def zylinder(name, radius, hoehe, position, mat_name, seiten=8):
    """Acht Seiten reichen: Bei dieser Kameradistanz ist der Unterschied zu
    einem runden Zylinder nicht sichtbar, kostet aber das Dreifache."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Station 1: Annahme -----------------------------------------------------
# Welt 1: der Wartebereich. Waechst vom einzelnen Stuhl zur Sitzreihe
# mit Nummernanzeige -- also von "hier sitzt zufaellig jemand" zu
# "hier ist ein Ort, an dem man wartet".

def stuhl(x, mat="moebel"):
    teile = []
    teile.append(quader("sitz", (0.44, 0.42, 0.07), (x, 0.0, 0.45), mat))
    teile.append(quader("lehne", (0.44, 0.07, 0.46), (x, -0.18, 0.71), mat))
    for dx in (-0.17, 0.17):
        for dy in (-0.16, 0.16):
            teile.append(quader("bein", (0.05, 0.05, 0.44),
                                (x + dx, dy, 0.22), "hell"))
    return teile


def intake_1():
    """Ein einzelner Stuhl. Mehr hast du am Anfang nicht."""
    return stuhl(0.0)


def intake_2():
    """Drei Stuehle -- aus dem Platz wird eine Reihe."""
    teile = []
    for x in (-0.52, 0.0, 0.52):
        teile += stuhl(x)
    return teile


def intake_3():
    """Sitzreihe plus Nummernanzeige. Jetzt ist es ein Wartebereich."""
    teile = []
    for x in (-0.52, 0.0, 0.52):
        teile += stuhl(x)
    # Standsaeule mit Anzeige
    teile.append(zylinder("saeule", 0.06, 1.5, (0.95, -0.30, 0.75), "hell"))
    teile.append(quader("anzeige_rahmen", (0.42, 0.10, 0.30), (0.95, -0.30, 1.62), "moebel"))
    teile.append(quader("anzeige_flaeche", (0.34, 0.04, 0.22), (0.95, -0.36, 1.62), "akzent"))
    return teile


# --- Station 2: Puffer ------------------------------------------------------
# Welt 1: deine Mappe. Waechst vom losen Stapel zum Regal --
# von "Chaos" zu "System".

def buffer_1():
    """Ein Stapel Papier auf dem Boden. Ordnung sieht anders aus."""
    teile = []
    for i, (dx, dy, dz, dreh) in enumerate([
            (0.0, 0.0, 0.03, 0.0), (0.03, 0.02, 0.09, 7.0), (-0.02, 0.01, 0.15, -5.0)]):
        teile.append(quader("stapel_%d" % i, (0.34, 0.44, 0.055),
                            (dx, dy, dz), "papier", dreh))
    return teile


def buffer_2():
    """Zwei Stapel und eine Ablage -- erste Struktur."""
    teile = buffer_1()
    teile.append(quader("ablage_boden", (0.52, 0.60, 0.05), (0.62, 0.0, 0.28), "moebel"))
    for dx in (-0.22, 0.22):
        teile.append(quader("ablage_wange", (0.05, 0.58, 0.30),
                            (0.62 + dx, 0.0, 0.15), "hell"))
    for i in range(2):
        teile.append(quader("ablage_papier_%d" % i, (0.36, 0.46, 0.06),
                            (0.62, 0.0, 0.34 + i * 0.07), "papier", 4.0 * i))
    return teile


def buffer_3():
    """Ein richtiges Regal mit Ordnern. Aus dem Stapel wurde Ablage."""
    teile = buffer_2()
    teile.append(quader("regal_rueck", (1.10, 0.06, 1.10), (0.0, -0.34, 0.72), "moebel"))
    for hoehe in (0.42, 0.80, 1.18):
        teile.append(quader("regal_boden", (1.10, 0.56, 0.05), (0.0, -0.06, hoehe), "moebel"))
    # Ordner -- der Akzent macht sie als Inhalt lesbar
    for reihe, hoehe in enumerate((0.50, 0.88)):
        for i in range(4):
            x = -0.38 + i * 0.25
            teile.append(quader("ordner_%d_%d" % (reihe, i), (0.20, 0.44, 0.28),
                                (x, -0.06, hoehe), "akzent" if (i + reihe) % 3 == 0 else "holz"))
    return teile


# --- Station 3: Bearbeitung -------------------------------------------------
# Welt 1: der Klapptisch. Waechst vom Klemmbrett auf den Knien zum
# eingerichteten Arbeitsplatz.

def processing_1():
    """Klemmbrett auf den Knien. Ein Arbeitsplatz ist das noch nicht."""
    teile = []
    teile.append(quader("brett", (0.42, 0.56, 0.04), (0.0, 0.0, 0.62), "holz", 8.0))
    teile.append(quader("klemme", (0.20, 0.07, 0.05), (0.0, 0.22, 0.66), "hell"))
    teile.append(quader("blatt", (0.34, 0.44, 0.01), (0.0, -0.02, 0.65), "papier", 8.0))
    return teile


def processing_2():
    """Ein Klapptisch. Jetzt hast du eine Flaeche."""
    teile = []
    teile.append(quader("platte", (1.10, 0.66, 0.05), (0.0, 0.0, 0.74), "holz"))
    for dx in (-0.46, 0.46):
        teile.append(quader("bein_paar", (0.06, 0.58, 0.72), (dx, 0.0, 0.37), "hell"))
    teile.append(quader("blatt", (0.34, 0.44, 0.01), (-0.22, 0.04, 0.77), "papier", 6.0))
    teile.append(quader("stift", (0.03, 0.20, 0.03), (0.10, -0.06, 0.78), "akzent", 24.0))
    return teile


def processing_3():
    """Eingerichteter Platz: Tisch, Ablagekorb, Lampe, Thermoskanne.
    Die Gegenstaende erzaehlen mehr als jede Detailverfeinerung."""
    teile = processing_2()
    # Ablagekorb
    teile.append(quader("korb_boden", (0.40, 0.30, 0.03), (0.40, 0.14, 0.79), "moebel"))
    for dy in (-0.14, 0.14):
        teile.append(quader("korb_wand", (0.40, 0.03, 0.12), (0.40, 0.14 + dy, 0.85), "moebel"))
    teile.append(quader("korb_papier", (0.32, 0.24, 0.07), (0.40, 0.14, 0.84), "papier"))
    # Lampe -- der warme Akzent macht den Platz bewohnt
    teile.append(zylinder("lampe_fuss", 0.10, 0.03, (-0.44, -0.20, 0.78), "hell"))
    teile.append(zylinder("lampe_arm", 0.02, 0.42, (-0.44, -0.20, 0.99), "hell"))
    teile.append(quader("lampe_schirm", (0.20, 0.16, 0.10), (-0.38, -0.20, 1.22), "akzent", -18.0))
    # Thermoskanne
    teile.append(zylinder("kanne", 0.07, 0.26, (0.02, 0.24, 0.90), "moebel"))
    teile.append(zylinder("kanne_deckel", 0.075, 0.04, (0.02, 0.24, 1.05), "akzent"))
    return teile


# --- Station 4: Transport ---------------------------------------------------
# Welt 1: der Kumpel. Er spricht Leute an und bringt sie zu dir.
# Dargestellt als sein Platz -- ein Hocker, spaeter ein eigener kleiner Stand.

def transport_1():
    """Ein Hocker an der Wand. Mehr braucht er nicht."""
    teile = []
    teile.append(quader("hocker_sitz", (0.40, 0.40, 0.07), (0.0, 0.0, 0.52), "moebel"))
    for dx in (-0.15, 0.15):
        for dy in (-0.15, 0.15):
            teile.append(quader("hocker_bein", (0.05, 0.05, 0.50),
                                (dx, dy, 0.25), "hell"))
    return teile


def transport_2():
    """Hocker plus Stehtisch -- er hat jetzt einen Platz, kein Eck."""
    teile = transport_1()
    teile.append(zylinder("stehtisch_fuss", 0.22, 0.05, (0.70, 0.0, 0.03), "moebel"))
    teile.append(zylinder("stehtisch_saeule", 0.05, 0.98, (0.70, 0.0, 0.50), "hell"))
    teile.append(zylinder("stehtisch_platte", 0.34, 0.05, (0.70, 0.0, 1.00), "holz"))
    teile.append(quader("zettel", (0.24, 0.30, 0.02), (0.70, 0.0, 1.04), "papier", 12.0))
    return teile


def transport_3():
    """Eigener kleiner Stand mit Aufsteller. Er gehoert jetzt dazu."""
    teile = transport_2()
    teile.append(quader("aufsteller_fuss", (0.50, 0.36, 0.05), (-0.75, 0.0, 0.03), "moebel"))
    teile.append(quader("aufsteller_tafel", (0.56, 0.06, 1.00), (-0.75, 0.0, 0.55), "hell",
                        drehung_z=0.0))
    teile.append(quader("aufsteller_text", (0.44, 0.03, 0.62), (-0.75, -0.05, 0.62), "akzent"))
    return teile


# --- Station 5: Sonderfaelle ------------------------------------------------
# Welt 1: der Sachbearbeiter, der dir Faelle zuschiebt. Dargestellt als der
# Uebergabepunkt -- ein Rollwagen, spaeter ein ganzer Aktenberg.

def special_1():
    """Ein Rollwagen mit einem Stapel. Der erste Fall, den er dir zuschiebt."""
    teile = []
    teile.append(quader("wagen_platte", (0.70, 0.50, 0.05), (0.0, 0.0, 0.72), "moebel"))
    teile.append(quader("wagen_boden", (0.70, 0.50, 0.04), (0.0, 0.0, 0.26), "moebel"))
    for dx in (-0.31, 0.31):
        for dy in (-0.21, 0.21):
            teile.append(quader("wagen_strebe", (0.04, 0.04, 0.72), (dx, dy, 0.38), "hell"))
    teile.append(quader("wagen_stapel", (0.46, 0.36, 0.14), (0.0, 0.0, 0.81), "papier"))
    return teile


def special_2():
    """Zwei Stapel und ein Griff -- es wird regelmaessig."""
    teile = special_1()
    teile.append(quader("wagen_griff", (0.06, 0.46, 0.06), (0.38, 0.0, 0.96), "hell"))
    teile.append(quader("wagen_stapel_2", (0.42, 0.32, 0.16), (0.0, 0.0, 0.36), "akzent"))
    return teile


def special_3():
    """Ein ganzer Aktenberg. Er vertraut dir inzwischen alles an."""
    teile = special_2()
    for i, (dx, dy, dz, dreh) in enumerate([
            (-0.10, 0.06, 0.98, 6.0), (0.08, -0.04, 1.12, -9.0), (0.0, 0.02, 1.26, 3.0)]):
        teile.append(quader("berg_%d" % i, (0.44, 0.34, 0.13), (dx, dy, dz),
                            "akzent" if i % 2 else "papier", dreh))
    return teile


STATIONEN = {
    "station_intake_1": intake_1,
    "station_intake_2": intake_2,
    "station_intake_3": intake_3,
    "station_buffer_1": buffer_1,
    "station_buffer_2": buffer_2,
    "station_buffer_3": buffer_3,
    "station_processing_1": processing_1,
    "station_processing_2": processing_2,
    "station_processing_3": processing_3,
    "station_transport_1": transport_1,
    "station_transport_2": transport_2,
    "station_transport_3": transport_3,
    "station_special_1": special_1,
    "station_special_2": special_2,
    "station_special_3": special_3,
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
    print("=== STATIONSMODULE WELT 1 ===")
    gesamt = 0
    for name, bauen in STATIONEN.items():
        alles_loeschen()
        teile = bauen()
        pfad = os.path.abspath(os.path.join(AUSGABE, name + ".glb"))
        exportieren(pfad)
        dreiecke = sum(len(o.data.polygons) * 2 for o in teile if o.type == "MESH")
        gesamt += dreiecke
        print("  %-24s %2d Teile  ~%4d Dreiecke  %5.1f KB"
              % (name, len(teile), dreiecke, os.path.getsize(pfad) / 1024.0))
    print("")
    print("  %d Module, zusammen ~%d Dreiecke" % (len(STATIONEN), gesamt))
    print("  Budget laut ART_DIRECTION: unter 2000 je Stationsmodul")


if __name__ == "__main__":
    main()
