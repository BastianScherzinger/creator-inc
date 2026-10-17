"""Erzeugt die Stationsmodule fuer Welt 2 "auftrag" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_auftrag.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und Kommentarstil
folgen bewusst art_source/scripts/build_stations_zimmer.py: manche Stufen
bauen wortwoertlich auf der vorigen auf (teile = vorherige() + neu), andere
ersetzen das improvisierte Vorgaenger-Teil vollstaendig durch ein reicheres
Aequivalent. Das ist im Sinne von ART_DIRECTION R4 richtig: Hauptsache, Stufe
2 ist unzweifelhaft mehr/besser als Stufe 1.

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist im Zimmer der Welt 1 ein Klapptisch mit Handy, hier eine
Nachricht, die hereinkommt. Die Zuordnung steht in
data/themes/auftrag/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 2 --
auftrag", und die Aufgabenstellung dieses Skripts):
    intake      Anfrage     Handy+Nachricht -> +Notizzettel -> Postfach-Board
    buffer      Klaeren     Block+3 Fragen -> +Skizze -> Korkwand+Pfeile
    processing  Bauen       Laptop -> +2. Monitor auf Buechern -> 2 Monitore+Tastatur+Kabelbuendel
    transport   Ausliefern  USB-Stick -> +kleiner Server -> 2 Geraete+Netzteil
    special     Der Engpass Speicherriegel -> +Luefter -> offenes Gehaeuse (WEGGENOMMEN, nicht dazugebaut)

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Harte Groessenregel dieser Aufgabe: jedes Modul passt in 1,8 x 1,8
Grundflaeche, hoechstens 1,6 hoch, Ursprung in der Mitte der Grundflaeche auf
z = 0. Dreiecksbudget: Stufe 1 <= 90, Stufe 2 <= 150, Stufe 3 <= 240.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. linear = s^2,2. Diese Palette ist NICHT neu erfunden:
# Die fuenf uebernommenen Eintraege (rahmen, kabel, textil, heizkoerper,
# wand_unten) stehen woertlich so in build_room_auftrag.py -- dort bereits
# korrekt gerechnet, und dasselbe Zimmer soll an der Station genauso aussehen
# wie an der Wand. Die restlichen Eintraege sind das globale Spielpalette aus
# docs/ART_DIRECTION.md Abschnitt 3 (Amtsbeige, Aktion, Erfolg, Akzent kuehl,
# Papier, Grund dunkel/mittel), bereits korrekt nach s^2,2 gerechnet in
# build_stations_zimmer.py -- diese Werte werden von dort uebernommen, nicht
# neu ausgerechnet, damit ein Bildschirm in Welt 2 exakt so blau glueht wie in
# Welt 1.
PALETTE = {
    # -- woertlich aus build_room_auftrag.py (dort aus build_room_zimmer.py) --
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # #8e97a8 globaler Metallton
    "kabel":      (0.006, 0.006, 0.008, 1.0),   # fast schwarzer Kunststoff
    "textil":     (0.268, 0.218, 0.173, 1.0),   # verwaschener Stoff/Kork-Ton
    "heizkoerper":(0.302, 0.268, 0.199, 1.0),   # vergilbtes Weiss, alter Kunststoff
    "wand_unten": (0.082, 0.077, 0.069, 1.0),   # dunkler Rahmen-/Sockelton

    # -- woertlich aus build_stations_zimmer.py, dort frisch nach s^2,2 --
    "papier":            (0.916, 0.883, 0.812, 1.0),  # #f5f1e8 Papier
    "holz":              (0.592, 0.482, 0.330, 1.0),  # #c9b79a Amtsbeige: Tisch, Buecher
    "moebel":            (0.056, 0.070, 0.106, 1.0),  # #454c5c Grund mittel: Gehaeuse, Gestelle
    "akzent_warm":       (0.891, 0.405, 0.040, 1.0),  # #f2a93b Aktion: Marker, Zettel-Zeilen
    "bildschirm":        (0.066, 0.344, 0.680, 1.0),  # #4a9dd6 Akzent kuehl: JEDER Bildschirm glueht so
    "led_gruen":         (0.104, 0.530, 0.198, 1.0),  # #5bbf7a Erfolg: Geraete-Betriebsleuchte
    "kunststoff_dunkel": (0.029, 0.033, 0.041, 1.0),  # neutrales Dunkelgrau: Laptop-, Handy-, Stick-Gehaeuse
}

AUSGABE = "project/assets/stations/auftrag"


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


def _handy(position):
    """Ein Telefon -- Koerper plus leuchtende Vorderseite. Wird von intake_1
    gebraucht und von intake_2 weiterverwendet, wie stuhl() im Amt-Vorbild."""
    x, y, z = position
    teile = []
    teile.append(quader("handy_koerper", (0.09, 0.02, 0.16), (x, y, z), "kunststoff_dunkel"))
    teile.append(quader("handy_schirm", (0.075, 0.006, 0.14), (x, y - 0.011, z), "bildschirm"))
    return teile


# --- Station 1: Anfrage -------------------------------------------------------
# Welt 2: die eingehende Nachricht. Waechst vom Handy mit einer Nachricht zum
# Handy mit Anforderungszettel zu einem kleinen Postfach-Board mit mehreren
# Faechern -- von "eine Frage" zu "mehrere offene Anfragen gleichzeitig".

def intake_1():
    """Ein Handy mit einer eingehenden Nachricht -- eine einzelne Anfrage,
    mehr nicht. Der Balken ueber dem Schirm ist die Benachrichtigung, die es
    noch nicht gab, als das Zimmer aus Welt 1 nur ein Zuschauer-Kommentar
    war."""
    teile = []
    teile += _handy((0.0, 0.0, 0.08))
    teile.append(quader("nachricht_balken", (0.06, 0.004, 0.025), (0.0, -0.013, 0.12), "akzent_warm"))
    return teile


def intake_2():
    """Handy plus ein Notizzettel mit den Anforderungen daneben -- aus der
    einen Nachricht ist eine Liste von Wuenschen geworden, die jemand anders
    geschrieben hat (docs/STORY.md, AKT 2: 'Das ist neu: Bisher hast du
    entschieden, was gebaut wird')."""
    teile = intake_1()
    teile.append(quader("notizzettel", (0.20, 0.24, 0.012), (0.22, 0.02, 0.006), "papier", -8.0))
    for i in range(3):
        teile.append(quader("anforderung_%d" % i, (0.13, 0.01, 0.004),
                            (0.22, -0.06 + i * 0.05, 0.014), "akzent_warm", -8.0))
    return teile


def intake_3():
    """Ein kleines Postfach-Board mit sechs Faechern, drei davon belegt --
    ersetzt Handy und Zettel vollstaendig: aus der einen Nachricht ist ein
    richtiger Posteingang geworden, mit mehreren offenen Anfragen zugleich."""
    teile = []
    teile.append(quader("board_fuss", (0.64, 0.30, 0.04), (0.0, 0.0, 0.02), "holz"))
    teile.append(quader("board_rahmen", (0.60, 0.05, 0.46), (0.0, 0.0, 0.28), "moebel"))
    faecher = []
    for row in range(2):
        for col in range(3):
            dx = -0.18 + col * 0.18
            dz = 0.16 + row * 0.18
            faecher.append((dx, dz))
    for i, (dx, dz) in enumerate(faecher):
        teile.append(quader("fach_%d" % i, (0.15, 0.03, 0.15), (dx, -0.01, dz), "rahmen"))
    belegte = (0, 2, 4)
    for idx, i in enumerate(belegte):
        dx, dz = faecher[i]
        farbe = "akzent_warm" if idx % 2 == 0 else "papier"
        teile.append(quader("nachricht_%d" % i, (0.10, 0.01, 0.10), (dx, -0.03, dz), farbe))
    return teile


# --- Station 2: Klaeren -------------------------------------------------------
# Welt 2: die Rueckfrage. Waechst vom Block mit drei Fragen zum Block mit
# Skizze zu einer eigenen Korkwand mit Skizze und Pfeilen -- von "was ist
# gemeint" zu "so ist es gemeint".

def buffer_1():
    """Ein Notizblock mit drei kurzen Fragezeilen und einem Stift -- die
    ersten Rueckfragen, bevor ueberhaupt gebaut wird."""
    teile = []
    teile.append(quader("block", (0.22, 0.28, 0.02), (0.0, 0.0, 0.01), "papier"))
    for i in range(3):
        teile.append(quader("frage_%d" % i, (0.14, 0.012, 0.004),
                            (0.0, -0.08 + i * 0.07, 0.022), "akzent_warm"))
    teile.append(quader("stift", (0.02, 0.16, 0.02), (0.16, 0.02, 0.015), "akzent_warm", 20.0))
    return teile


def buffer_2():
    """Block plus eine Skizze auf einem eigenen Blatt daneben -- aus der
    Rueckfrage ist eine erste Antwort auf Papier geworden."""
    teile = buffer_1()
    teile.append(quader("skizze_blatt", (0.24, 0.30, 0.012), (0.30, 0.0, 0.006), "papier", 10.0))
    teile.append(quader("skizze_kasten_a", (0.09, 0.01, 0.09), (0.26, -0.06, 0.02), "bildschirm", 10.0))
    teile.append(quader("skizze_kasten_b", (0.09, 0.01, 0.09), (0.34, 0.05, 0.02), "akzent_warm", 10.0))
    teile.append(quader("skizze_linie", (0.10, 0.01, 0.02), (0.30, -0.005, 0.02), "moebel", 10.0))
    return teile


def buffer_3():
    """Eine kleine Korkwand mit Skizze und Pfeilen -- ersetzt Block und Blatt
    vollstaendig: aus losen Notizen ist eine Uebersicht geworden, an der man
    stehend nachdenkt statt sitzend zu kritzeln."""
    teile = []
    teile.append(quader("kork_fuss", (0.60, 0.30, 0.05), (0.0, 0.0, 0.03), "holz"))
    for dx in (-0.26, 0.26):
        teile.append(quader("kork_bein", (0.04, 0.04, 0.70), (dx, 0.10, 0.38), "moebel"))
    teile.append(quader("kork_flaeche", (0.72, 0.05, 0.56), (0.0, 0.0, 0.76), "textil"))
    teile.append(quader("skizze_kasten_a", (0.14, 0.01, 0.12), (-0.18, -0.03, 0.86), "bildschirm"))
    teile.append(quader("skizze_kasten_b", (0.14, 0.01, 0.12), (0.16, -0.03, 0.66), "akzent_warm"))
    teile.append(quader("pfeil_1", (0.18, 0.01, 0.02), (-0.02, -0.03, 0.76), "akzent_warm", 18.0))
    teile.append(quader("pfeil_2", (0.14, 0.01, 0.02), (0.0, -0.03, 0.60), "akzent_warm", -30.0))
    for i in range(3):
        teile.append(quader("pin_%d" % i, (0.015, 0.01, 0.015),
                            (-0.20 + i * 0.18, -0.035, 0.90 - 0.02 * i), "rahmen"))
    return teile


# --- Station 3: Bauen ---------------------------------------------------------
# Welt 2: der Arbeitsplatz. Waechst vom aufgeklappten Laptop zum Laptop mit
# zweitem Monitor auf Buechern zu zwei Monitoren mit externer Tastatur und
# gebuendeltem Kabel -- von "ein Geraet" zu "ein aufgeraeumter Arbeitsplatz".

def processing_1():
    """Ein Laptop, aufgeklappt -- der Editor ist offen, mehr Ausruestung
    braucht der Anfang nicht."""
    teile = []
    teile.append(quader("laptop_deck", (0.32, 0.22, 0.02), (0.0, 0.0, 0.03), "kunststoff_dunkel"))
    teile.append(quader("laptop_lehne", (0.32, 0.02, 0.20), (0.0, -0.11, 0.14), "kunststoff_dunkel"))
    teile.append(quader("laptop_schirm", (0.27, 0.006, 0.16), (0.0, -0.104, 0.14), "bildschirm"))
    return teile


def processing_2():
    """Laptop plus zweiter Monitor auf einem Buecherstapel -- die zweite
    Flaeche kommt behelfsmaessig dazu, genau wie in Welt 1: der zweite
    Bildschirm ist da, bevor der Schreibtisch dafuer da ist."""
    teile = processing_1()
    for i, (dz, dreh) in enumerate([(0.02, 0.0), (0.06, -4.0), (0.10, 5.0)]):
        teile.append(quader("buch_%d" % i, (0.22, 0.17, 0.035), (0.34, 0.02, dz), "holz", dreh))
    teile.append(quader("monitor_rahmen", (0.24, 0.02, 0.16), (0.34, -0.05, 0.22), "kunststoff_dunkel"))
    teile.append(quader("monitor_schirm", (0.20, 0.006, 0.12), (0.34, -0.044, 0.22), "bildschirm"))
    return teile


def processing_3():
    """Zwei Monitore auf einem echten Tisch, externe Tastatur und ein
    gebuendeltes Kabel -- ersetzt das Buecher-Provisorium vollstaendig. Das
    Kabelbuendel ist die Pointe: in Welt 1 lag ein Kabel lose auf dem Tisch
    (processing_1 dort), hier ist es zusammengebunden -- derselbe Fortschritt
    von 'improvisiert' zu 'ausgeruestet', nur eine Station weiter."""
    teile = []
    teile.append(quader("tisch_platte", (0.90, 0.40, 0.03), (0.0, 0.0, 0.42), "holz"))
    for dx in (-0.38, 0.38):
        teile.append(quader("tisch_bein", (0.04, 0.34, 0.40), (dx, 0.0, 0.20), "rahmen"))
    for i, dx in enumerate((-0.22, 0.22)):
        teile.append(quader("monitor_fuss_%d" % i, (0.10, 0.08, 0.02), (dx, -0.06, 0.44), "moebel"))
        teile.append(quader("monitor_hals_%d" % i, (0.02, 0.02, 0.16), (dx, -0.06, 0.53), "rahmen"))
        teile.append(quader("monitor_rahmen_%d" % i, (0.24, 0.02, 0.16), (dx, -0.10, 0.65), "kunststoff_dunkel"))
        teile.append(quader("monitor_schirm_%d" % i, (0.20, 0.006, 0.12), (dx, -0.094, 0.65), "bildschirm"))
    teile.append(quader("tastatur", (0.28, 0.10, 0.015), (0.0, 0.10, 0.435), "kunststoff_dunkel"))
    teile.append(quader("kabelbuendel", (0.05, 0.05, 0.05), (0.20, 0.12, 0.445), "kabel"))
    return teile


# --- Station 4: Ausliefern ----------------------------------------------------
# Welt 2: die Uebergabe. Waechst vom einzelnen USB-Stick zum Stick mit
# kleinem Server zu zwei gestapelten Geraeten mit eigenem Netzteil -- von
# "ein Medium in der Hand" zu "eine kleine, eigene Infrastruktur".

def transport_1():
    """Ein USB-Stick auf dem Boden -- die Auslieferung beginnt so klein wie
    moeglich: ein einzelnes Speichermedium, von Hand uebergeben."""
    teile = []
    teile.append(quader("stick_koerper", (0.05, 0.02, 0.16), (0.0, 0.0, 0.08), "kunststoff_dunkel"))
    teile.append(quader("stick_stecker", (0.03, 0.014, 0.05), (0.0, 0.0, 0.185), "rahmen"))
    teile.append(quader("stick_led", (0.02, 0.006, 0.01), (0.0, -0.011, 0.14), "led_gruen"))
    return teile


def transport_2():
    """USB-Stick plus ein kleiner Einplatinen-Server mit eigener Leuchte --
    aus dem einzelnen Medium ist ein kleines System geworden, das selbst
    online steht."""
    teile = transport_1()
    teile.append(quader("board_gehaeuse", (0.16, 0.12, 0.03), (0.20, 0.0, 0.015), "moebel"))
    teile.append(quader("board_platine", (0.13, 0.09, 0.006), (0.20, 0.0, 0.033), "kunststoff_dunkel"))
    teile.append(quader("board_led", (0.015, 0.006, 0.008), (0.25, -0.03, 0.037), "led_gruen"))
    return teile


def transport_3():
    """Zwei kleine Geraete uebereinander plus ein eigenes Netzteil --
    ersetzt den Einzelserver vollstaendig: aus einem Board ist ein kleiner
    Stapel mit eigener Stromversorgung geworden, robust genug fuer einen
    zahlenden Auftraggeber."""
    teile = []
    teile.append(quader("geraet_unten", (0.20, 0.16, 0.05), (0.0, 0.0, 0.025), "moebel"))
    teile.append(quader("geraet_oben", (0.16, 0.13, 0.04), (0.0, 0.0, 0.07), "kunststoff_dunkel"))
    teile.append(quader("led_unten", (0.015, 0.006, 0.008), (0.08, -0.06, 0.03), "led_gruen"))
    teile.append(quader("led_oben", (0.015, 0.006, 0.008), (0.06, -0.05, 0.075), "led_gruen"))
    teile.append(quader("netzteil", (0.10, 0.08, 0.04), (0.24, 0.0, 0.02), "moebel"))
    teile.append(quader("netzkabel", (0.10, 0.02, 0.015), (0.16, 0.0, 0.02), "kabel"))
    for i, dz in enumerate((0.04, 0.075)):
        teile.append(quader("luefter_schlitz_%d" % i, (0.10, 0.005, 0.008), (0.0, 0.075, dz), "rahmen"))
    return teile


# --- Station 5: Der Engpass ---------------------------------------------------
# Welt 2: das Speicherproblem. Waechst vom einzelnen Speicherriegel zum
# Riegel mit Luefter zu einem offenen Gehaeuse mit sichtbarem Innenleben --
# ABER anders als bei den anderen vier Stationen ist die letzte Stufe kein
# "mehr", sondern ein "weniger": der leere Sockel dort, wo eben noch der
# Riegel steckte, zeigt, dass etwas WEGGENOMMEN wurde (docs/STORY.md, AKT 2:
# "Den Browser raus, das HTML direkt lesen ... um etwas wegzunehmen").

def special_1():
    """Ein einzelner Speicherriegel, aufrecht -- das Problem faengt klein
    an: zu wenig Arbeitsspeicher fuer einen echten Browser."""
    teile = []
    teile.append(quader("riegel_platine", (0.14, 0.015, 0.30), (0.0, 0.0, 0.16), "moebel"))
    teile.append(quader("riegel_kontakte", (0.14, 0.02, 0.03), (0.0, 0.0, 0.015), "rahmen"))
    for i, dx in enumerate((-0.045, 0.0, 0.045)):
        teile.append(quader("chip_%d" % i, (0.03, 0.012, 0.05), (dx, 0.0, 0.28), "kunststoff_dunkel"))
    return teile


def special_2():
    """Speicherriegel plus ein kleiner Luefter daneben -- es wird versucht,
    das Problem mit mehr Technik zu erschlagen, statt es zu loesen. Genau
    dieser Holzweg ist die Vorstufe zur Erkenntnis in special_3."""
    teile = special_1()
    teile.append(quader("luefter_rahmen", (0.16, 0.03, 0.16), (0.24, 0.0, 0.10), "rahmen"))
    teile.append(quader("luefter_rotor", (0.10, 0.015, 0.10), (0.24, 0.0, 0.10), "moebel", 45.0))
    return teile


def special_3():
    """Ein offenes Gehaeuse mit sichtbarem Innenleben -- der leere Sockel an
    der Stelle, an der eben noch der Speicherriegel steckte, ist die
    Aussage: Hier wurde etwas WEGGENOMMEN, nicht dazugebaut. Das ersetzt
    special_2 vollstaendig, wie schon intake_3/buffer_3/processing_3 ihre
    Vorstufe ersetzen -- nur ist der Grund hier ein anderer: nicht weil das
    Provisorium einer besseren Loesung wich (mehr Luefter haetten das
    Speicherproblem nie geloest), sondern weil die Loesung im Weglassen lag.
    Eine Seite des Gehaeuses fehlt bewusst (nur drei Waende plus Pfosten,
    keine vierte Flaeche) -- das Innenleben liegt offen, wie nach dem Umbau."""
    teile = []
    teile.append(quader("gehaeuse_boden", (0.50, 0.36, 0.02), (0.0, 0.0, 0.01), "moebel"))
    teile.append(quader("gehaeuse_rueckwand", (0.50, 0.02, 0.40), (0.0, 0.17, 0.21), "moebel"))
    teile.append(quader("gehaeuse_seite", (0.02, 0.36, 0.40), (-0.24, 0.0, 0.21), "rahmen"))
    for dx, dy in ((-0.23, -0.17), (0.23, -0.17), (-0.23, 0.17), (0.23, 0.17)):
        teile.append(quader("rahmen_pfosten", (0.02, 0.02, 0.40), (dx, dy, 0.21), "rahmen"))
    teile.append(quader("mainboard", (0.40, 0.28, 0.01), (0.0, 0.0, 0.03), "kunststoff_dunkel"))
    teile.append(quader("sockel_leer", (0.14, 0.03, 0.006), (0.05, -0.05, 0.036), "rahmen"))
    teile.append(quader("luefter_rest", (0.12, 0.02, 0.12), (-0.15, 0.10, 0.20), "rahmen"))
    teile.append(quader("status_led", (0.02, 0.01, 0.01), (0.18, -0.12, 0.04), "led_gruen"))
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
    print("=== STATIONSMODULE WELT 2 -- AUFTRAG ===")
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


if __name__ == "__main__":
    main()
