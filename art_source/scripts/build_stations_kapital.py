"""Erzeugt die Stationsmodule fuer Welt 6 "kapital" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_kapital.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und
Kommentarstil folgen der Strukturvorlage
art_source/scripts/build_stations_webseiten.py.

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist in Welt 5 eine Monitorwand, hier ein einzelnes schmales
Display. Die Zuordnung steht in data/themes/kapital/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 6 --
kapital"; Kette laut Auftrag: Signal -> Analyse -> Position -> Streuung ->
Ausschuettung):
    intake      Signal        1 kleines Display -> 2 Displays -> schmaler Bildschirm, ruhige Linie
    buffer      Analyse       aufgeschlagenes Buch -> +Notizen -> Pult mit Unterlagen
    processing  Position      1 Balken -> 3 Balken, versch. Hoehe -> Balkenfeld
    transport   Streuung      2 Balken -> 4 Balken -> 8 Balken, ALLE gleich hoch
    special     Ausschuettung kleine Schale -> Schale mit Inhalt -> ruhiger Ablagetisch

WICHTIG (Auftrag, woertlich): "Diese Station-Sets sind die KLEINSTEN und
RUHIGSTEN des Spiels." Deshalb bleibt jede Stufe hier deutlich UNTER dem
Dreiecksbudget statt es auszureizen (siehe Zaehlung im Kopf jeder
Bau-Funktion), es gibt keine Leuchten im Takt, keine Statusanzeigen und
keine Kabel -- nur Buch, Balken und Schale. Wo Welt 5 fuer wachsenden
Ertrag "akzent_gold" einsetzt, tut diese Welt das bewusst NICHT: Balken und
Inhalt bleiben in gedeckten Toenen. Das Zurueckhalten selbst ist die
Aussage.

HINWEIS ZUR PALETTE: build_room_kapital.py ist waehrend dieser Aufgabe
fertig geworden -- seine Palette wird hier uebernommen, nicht die von
build_room_buero.py. Wichtigste Entscheidung des Raums, hier fortgesetzt:
DIESE WELT HAT KEIN METALL. Der globale Rahmenton ("rahmen"), der in jeder
anderen Welt fuer Fuesse, Staender und Tischbeine steht, kommt in dieser
Datei kein einziges Mal vor -- "holz_dunkel" (woertlich der Wert von dort)
uebernimmt jede dieser Rollen. Das ist keine Kleinigkeit, sondern die
konsequente Fortsetzung dessen, was der Raum bereits vormacht (selbst
Fenster- und Tuerrahmen sind dort Holz, kein Metall). "buch_einband" ist
woertlich der Wert von dessen "buch_a" (ein gedaempfter Rot-Braun-Ton fuer
Bucheinband) -- derselbe Ton wie in der Buecherwand des Raums, damit das
Buch der Analyse-Station wie eines der Buecher dort aussieht. "bildschirm"
ist der globale Bildschirmton aus JEDER Welt und wird hier NUR beim
Signal-Display verwendet, sonst nirgends -- diese Welt hat keine
Statusleuchten (kein "led_gruen", kein Blinken). "papier" und "balken_ton"
sind frisch fuer diese Datei nach linear = s^2,2 gerechnet (mit `python -c`
nachgerechnet) und bewusst warm/gedaempft gehalten (R > G > B), damit sie
zur warmen, dunklen Materialsprache des Raums passen statt zum kuehlen Grau
aus Welt 5.

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Harte Groessenregel dieser Aufgabe: jedes Modul passt in 1,8 x 1,8
Grundflaeche, hoechstens 1,6 hoch, Ursprung in der Mitte der Grundflaeche auf
z = 0.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. linear = s^2,2. Herkunft jedes Tons steht oben im
# Modulkopf-Kommentar.
PALETTE = {
    # -- woertlich aus build_room_kapital.py uebernommen --
    "holz_dunkel":  (0.018, 0.006, 0.002, 1.0),  # dort global statt Metall -- hier jeder Fuss/Staender/Tisch
    "buch_einband": (0.071, 0.006, 0.004, 1.0),  # dort "buch_a" -- derselbe Einband wie in der Buecherwand

    # -- global identisch in jeder Welt (Begruendung in build_stations_zimmer.py) --
    # Nur an EINER Stelle benutzt (station_intake, das Signal-Display) --
    # diese Welt hat sonst keine Bildschirme und kein led_gruen.
    "bildschirm": (0.066, 0.344, 0.680, 1.0),

    # -- frisch fuer Welt 6, nach linear = s^2,2 gerechnet (mit python -c geprueft),
    # bewusst warm statt kuehl (R > G > B), damit sie zur Materialsprache des
    # Raums passen --
    "papier":     (0.694, 0.592, 0.399, 1.0),  # #d8c9a8 -- gealtertes Papier, waermer als das globale Weiss
    "balken_ton": (0.157, 0.106, 0.060, 1.0),  # #6e5c47 -- gedaempftes warmes Taupe, bewusst kein Gold
}

AUSGABE = "project/assets/stations/kapital"


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
    """Acht Seiten wie in der Vorlage -- bei dieser Kameradistanz nicht von
    einem runden Zylinder zu unterscheiden. Einzige Verwendung in dieser
    Datei: die Schale von station_special, weil eine Schale aus Quadern
    sofort wie eine Kiste aussieht."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Station 1: Signal -----------------------------------------------------------
# Welt 6: eine einzelne Zahl, keine Warteliste, kein Alarm. Waechst von
# einem kleinen Display zu zwei Displays zu einem schmalen Bildschirm mit
# einer ruhigen Linie -- absichtlich KEINE steigende Kurve wie in Welt 5,
# das waere zu laut fuer diesen Raum.

def intake_1():
    """Ein kleines Display mit einer Zahl auf einem schmalen Staender --
    ~40 Dreiecke, weit unter dem Budget von 90: Zurueckhaltung von der
    ersten Stufe an."""
    teile = []
    teile.append(quader("staender_fuss", (0.14, 0.10, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(quader("display_rahmen", (0.16, 0.02, 0.11), (0.0, 0.0, 0.185), "holz_dunkel"))
    teile.append(quader("display_schirm", (0.13, 0.006, 0.08), (0.0, -0.011, 0.185), "bildschirm"))
    teile.append(quader("ziffer", (0.05, 0.004, 0.03), (0.0, -0.014, 0.185), "papier"))
    return teile


def intake_2():
    """Zwei Displays auf einer schmalen Ablage -- ersetzt den einzelnen
    Staender durch eine Ablage fuer zwei Zahlen zugleich. Immer noch kein
    Bildschirm groesser als eine Handflaeche."""
    teile = []
    teile.append(quader("ablage", (0.42, 0.14, 0.02), (0.0, 0.0, 0.30), "holz_dunkel"))
    for i, dx in enumerate((-0.13, 0.13)):
        teile.append(quader("display_rahmen_%d" % i, (0.15, 0.02, 0.10), (dx, 0.0, 0.365), "holz_dunkel"))
        teile.append(quader("display_schirm_%d" % i, (0.12, 0.006, 0.07), (dx, -0.011, 0.365), "bildschirm"))
        teile.append(quader("ziffer_%d" % i, (0.045, 0.004, 0.025), (dx, -0.014, 0.365), "papier"))
    return teile


def intake_3():
    """Ein schmaler Bildschirm mit einer ruhigen Linie auf einem hohen
    Staender -- ersetzt die zwei Displays vollstaendig durch einen
    einzelnen, schlanken Bildschirm. Eine gerade Linie, keine Kurve: das
    Signal beruhigt sich, es feuert nicht."""
    teile = []
    teile.append(quader("staender_fuss", (0.18, 0.14, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(quader("staender_saeule", (0.03, 0.03, 0.66), (0.0, 0.0, 0.35), "holz_dunkel"))
    teile.append(quader("schirm_rahmen", (0.40, 0.02, 0.16), (0.0, 0.0, 0.72), "holz_dunkel"))
    teile.append(quader("schirm_flaeche", (0.36, 0.006, 0.12), (0.0, -0.011, 0.72), "bildschirm"))
    teile.append(quader("linie", (0.30, 0.004, 0.008), (0.0, -0.014, 0.72), "papier"))
    return teile


# --- Station 2: Analyse -----------------------------------------------------------
# Welt 6: kein Whiteboard, kein Baukasten -- ein Buch. Waechst vom
# aufgeschlagenen Buch zu Buch plus Notizen zu einem Pult mit Unterlagen --
# von "lesen" zu "einen Platz zum Arbeiten haben", nie lauter als das.

def buffer_1():
    """Ein aufgeschlagenes Buch, sonst nichts -- drei Quader, das ist die
    ganze Station."""
    teile = []
    teile.append(quader("einband", (0.30, 0.22, 0.02), (0.0, 0.0, 0.02), "buch_einband"))
    teile.append(quader("seite_l", (0.14, 0.20, 0.012), (-0.075, 0.0, 0.037), "papier", -3.0))
    teile.append(quader("seite_r", (0.14, 0.20, 0.012), (0.075, 0.0, 0.037), "papier", 3.0))
    return teile


def buffer_2():
    """Buch plus ein paar Notizen daneben -- ergaenzt, ersetzt nichts.
    Aus dem Lesen ist ein Vergleichen geworden."""
    teile = []
    teile.append(quader("einband", (0.30, 0.22, 0.02), (-0.14, 0.0, 0.02), "buch_einband"))
    teile.append(quader("seite_l", (0.14, 0.20, 0.012), (-0.215, 0.0, 0.037), "papier", -3.0))
    teile.append(quader("seite_r", (0.14, 0.20, 0.012), (-0.065, 0.0, 0.037), "papier", 3.0))
    notizen = [(0.18, 0.05, -6.0), (0.30, 0.10, 5.0), (0.20, 0.16, -4.0)]
    for i, (dx, dz, dreh) in enumerate(notizen):
        teile.append(quader("notiz_%d" % i, (0.12, 0.14, 0.008), (dx, 0.0, 0.014 * (i + 1)), "papier", dreh))
    return teile


def buffer_3():
    """Ein Pult mit Unterlagen -- ersetzt Buch und Notizen vollstaendig
    durch einen eigenen Arbeitsplatz: aus einzelnen Blaettern ist ein
    fester Platz fuer die Analyse geworden."""
    teile = []
    teile.append(quader("pult_fuss", (0.20, 0.16, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(quader("pult_saeule", (0.04, 0.04, 0.64), (0.0, 0.0, 0.34), "holz_dunkel"))
    teile.append(quader("pult_platte", (0.44, 0.32, 0.03), (0.0, 0.0, 0.66), "holz_dunkel", 0.0))
    unterlagen = [(-0.10, 0.66, -6.0), (0.04, 0.665, 4.0), (0.14, 0.67, -3.0)]
    for i, (dx, dz, dreh) in enumerate(unterlagen):
        teile.append(quader("unterlage_%d" % i, (0.16, 0.20, 0.008), (dx, -0.02, dz), "papier", dreh))
    return teile


# --- Station 3: Position ----------------------------------------------------------
# Welt 6: keine Warteschlange, kein Durchsatz -- ein Balken, der eine
# Groesse zeigt. Waechst von einem einzelnen Balken zu drei Balken
# unterschiedlicher Hoehe zu einem Balkenfeld.

def processing_1():
    """Ein einzelner Balken auf einem Sockel -- zwei Quader, kleiner geht
    in diesem Spiel keine Station."""
    teile = []
    teile.append(quader("sockel", (0.24, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(quader("balken", (0.14, 0.14, 0.36), (0.0, 0.0, 0.21), "balken_ton"))
    return teile


def processing_2():
    """Drei Balken unterschiedlicher Hoehe auf demselben Sockel -- aus
    einer Position sind mehrere geworden, unterschiedlich gewichtet."""
    teile = []
    teile.append(quader("sockel", (0.50, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    hoehen = [(-0.15, 0.30), (0.0, 0.46), (0.15, 0.20)]
    for i, (dx, hoehe) in enumerate(hoehen):
        teile.append(quader("balken_%d" % i, (0.11, 0.14, hoehe), (dx, 0.0, 0.02 + hoehe / 2.0), "balken_ton"))
    return teile


def processing_3():
    """Ein Balkenfeld -- sechs Balken auf einem breiten Sockel, weiterhin
    weit unter dem Budget: mehr Positionen, aber keine lauter als die
    andere."""
    teile = []
    teile.append(quader("sockel", (0.90, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    hoehen = [0.22, 0.34, 0.28, 0.42, 0.18, 0.30]
    for i, hoehe in enumerate(hoehen):
        dx = -0.375 + i * 0.15
        teile.append(quader("balken_%d" % i, (0.09, 0.13, hoehe), (dx, 0.0, 0.02 + hoehe / 2.0), "balken_ton"))
    return teile


# --- Station 4: Streuung ----------------------------------------------------------
# Welt 6: Streuung heisst Gleichmass, nicht Vielfalt. Waechst von zwei
# Balken zu vier zu acht -- und ALLE acht sind gleich hoch. Das ist der
# einzige Unterschied zu Position: dort variiert die Hoehe, hier nicht.

def _gleiche_balken(anzahl, sockel_breite):
    teile = []
    teile.append(quader("sockel", (sockel_breite, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    abstand = (sockel_breite - 0.14) / max(anzahl - 1, 1)
    start = -(anzahl - 1) * abstand / 2.0
    for i in range(anzahl):
        dx = start + i * abstand
        teile.append(quader("balken_%d" % i, (0.10, 0.13, 0.30), (dx, 0.0, 0.17), "balken_ton"))
    return teile


def transport_1():
    """Zwei Balken nebeneinander, gleich hoch -- der Anfang der Streuung."""
    return _gleiche_balken(2, 0.40)


def transport_2():
    """Vier Balken, weiterhin alle gleich hoch -- mehr Streuung, gleiches
    Gewicht je Balken."""
    return _gleiche_balken(4, 0.66)


def transport_3():
    """Acht Balken, alle exakt gleich hoch -- Streuung heisst Gleichmass,
    keine Position sticht hervor. 9 Teile, ~108 Dreiecke: weiterhin unter
    dem halben Budget dieser Stufe."""
    return _gleiche_balken(8, 1.10)


# --- Station 5: Ausschuettung ------------------------------------------------------
# Welt 6: das Ende der Kette, so leise wie der Rest des Raums. Waechst von
# einer kleinen Schale zu Schale mit Inhalt zu einem ruhigen Ablagetisch --
# der Inhalt ist ein Papierstapel, bewusst keine Muenzen oder Chips (harte
# Grenze des Auftrags: kein Gluecksspiel-Bild).

def special_1():
    """Eine kleine, leere Schale -- ein Zylinder auf einem Sockel, zwei
    Teile."""
    teile = []
    teile.append(quader("sockel", (0.20, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(zylinder("schale", 0.14, 0.06, (0.0, 0.0, 0.06), "holz_dunkel"))
    return teile


def special_2():
    """Dieselbe Schale, jetzt mit Inhalt -- ein kleiner Papierstapel darin,
    kein Geld-Symbol, nur Papier."""
    teile = []
    teile.append(quader("sockel", (0.20, 0.20, 0.02), (0.0, 0.0, 0.02), "holz_dunkel"))
    teile.append(zylinder("schale", 0.14, 0.06, (0.0, 0.0, 0.06), "holz_dunkel"))
    for i, hz in enumerate((0.10, 0.12, 0.14)):
        teile.append(quader("inhalt_%d" % i, (0.09 - i * 0.01, 0.09 - i * 0.01, 0.014), (0.0, 0.0, hz), "papier"))
    return teile


def special_3():
    """Ein ruhiger Ablagetisch mit derselben Schale darauf -- ersetzt den
    Sockel durch einen kleinen Tisch, mehr Ruhe entsteht durch Platz
    drumherum, nicht durch mehr Gegenstaende."""
    teile = []
    teile.append(quader("tisch_platte", (0.46, 0.34, 0.03), (0.0, 0.0, 0.42), "holz_dunkel"))
    for dx in (-0.18, 0.18):
        for dy in (-0.13, 0.13):
            teile.append(quader("tisch_bein_%d_%d" % (int(dx * 100), int(dy * 100)), (0.03, 0.03, 0.40), (dx, dy, 0.20), "holz_dunkel"))
    teile.append(zylinder("schale", 0.14, 0.06, (0.0, 0.0, 0.465), "holz_dunkel"))
    for i, hz in enumerate((0.505, 0.525)):
        teile.append(quader("inhalt_%d" % i, (0.09 - i * 0.01, 0.09 - i * 0.01, 0.014), (0.0, 0.0, hz), "papier"))
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
    print("=== STATIONSMODULE WELT 6 -- KAPITAL ===")
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
    print("  Budget dieser Aufgabe: Stufe 1 <= 90, Stufe 2 <= 150, Stufe 3 <= 240 Dreiecke")
    print("  (diese Welt bleibt bewusst deutlich darunter -- Zurueckhaltung ist die Aussage)")


if __name__ == "__main__":
    main()
