"""Erzeugt die Stationsmodule fuer Welt 3 "webseiten" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_webseiten.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und Kommentarstil
folgen bewusst art_source/scripts/build_stations_zimmer.py, der Struktur-
vorlage dieser Aufgabe: manche Stufen bauen woertlich auf der vorigen auf
(teile = vorherige() + neu), andere ersetzen das schlichtere Vorgaenger-Teil
durch ein reicheres Aequivalent. Hauptsache, jede Stufe ist unzweifelhaft
mehr/besser als die vorige.

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist im Zimmer ein Zettel auf dem Boden, hier ein Telefon auf
einem Empfangstresen. Die Zuordnung steht in data/themes/webseiten/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 3 --
webseiten"; die Kette ist woertlich die Pipeline einer Webagentur):
    intake      Anfrage      Telefon+Zettel -> Tresen+Posteingang -> Empfang+Bildschirm
    buffer      Konzept      Skizzenblock -> Korkwand+Faeden -> Whiteboard+Stehtisch
    processing  Umsetzung    Laptop am Tisch -> 2 Monitore -> 2 Arbeitsplaetze, 3 Monitore
    transport   Deployment   Server im Regal -> Rack, 3 Einschuebe -> volles Rack+Kabelfuehrung
    special     Betreuung    Ordner auf Tisch -> Regal+Kalender -> Kennzahl-Bildschirm+Stuhl

DER UNTERSCHIED ZU WELT 1 IST DIE HALBE ARBEIT: Welt 1 ist improvisiert
(Buecherstapel als Monitorstaender, schiefe Lampe, loses Kabel). Welt 3 ist
eingerichtet -- jedes Modul steht von Anfang an auf einem echten, geraden
Tisch oder Regal, nie auf dem Boden oder auf einem Buecherstapel. Schon
station_processing_1 zeigt das: ein Laptop auf einem schlichten Tisch, nicht
auf dem Boden wie im Zimmer.

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Harte Groessenregel dieser Aufgabe: jedes Modul passt in 1,8 x 1,8
Grundflaeche, hoechstens 1,6 hoch, Ursprung in der Mitte der Grundflaeche auf
z = 0.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. linear = s^2,2. Die meisten Toene unten sind woertlich
# aus build_room_webseiten.py und build_world_webseiten.py uebernommen, damit
# diese Stationen im selben Raum stehen und wie dieselben Moebel wirken --
# das ist der Auftrag: "Uebernimm die Palette, damit die Stationen im selben
# Raum stehen koennen, ohne herauszufallen." Zwei Toene sind global und in
# jeder Welt identisch (siehe build_stations_zimmer.py, dort schon so
# begruendet); zwei sind frisch fuer diese Welt nach derselben Formel
# gerechnet und mit node -e nachgerechnet, nicht nur von Hand geschaetzt.
PALETTE = {
    # -- woertlich uebernommen aus build_room_webseiten.py / build_world_webseiten.py --
    "rahmen":            (0.557, 0.592, 0.659, 1.0),  # globaler Metall-/Rahmenton
    "holz_hell":          (0.300, 0.210, 0.126, 1.0),  # helles Regalholz (Birke), wie raum_regal
    "holz_schreibtisch": (0.325, 0.234, 0.163, 1.0),  # noch helleres Tischplatten-Holz, IKEA-hell
    "ordner":            (0.596, 0.480, 0.330, 1.0),  # Aktenordner, Amtsbeige-Signaturfarbe
    "ordner_akzent":     (0.090, 0.120, 0.173, 1.0),  # vereinzelter dunkelblauer Ordnerruecken
    "whiteboard":        (0.820, 0.820, 0.800, 1.0),  # weisse Schreibflaeche
    "notiz":             (0.900, 0.870, 0.800, 1.0),  # Papier/Notiz, auch als allgemeines Papier
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # dunkles Geraetegehaeuse: Laptop, Monitor, Telefon, Server
    "tastatur":          (0.218, 0.218, 0.214, 1.0),  # heller Kunststoff, Tastatur/Maus

    # -- global identisch in jeder Welt (Begruendung in build_stations_zimmer.py) --
    "bildschirm": (0.066, 0.344, 0.680, 1.0),   # JEDER Bildschirm glueht so
    "led_gruen":  (0.104, 0.530, 0.198, 1.0),   # Betriebs-/Statusleuchte

    # -- frisch fuer Welt 3, nach linear = s^2,2 gerechnet (mit node -e geprueft) --
    "akzent_rot":  (0.548, 0.040, 0.040, 1.0),  # #c23b3b -- intake: neue Anfrage, dringend
    "akzent_gold": (0.701, 0.389, 0.046, 1.0),  # #d9a63f -- special: Kennzahl im Aufwind
}

AUSGABE = "project/assets/stations/webseiten"


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
    einem runden Zylinder zu unterscheiden, aber deutlich billiger."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Station 1: Anfrage -------------------------------------------------------
# Welt 3: das erste Kettenglied ist hier ein echter Arbeitsplatz, nie der
# Boden. Waechst vom Telefon mit Notizzettel zum kleinen Tresen mit
# Posteingang zum Empfangsplatz mit Bildschirm, an dem Anfragen sichtbar
# auflaufen -- von "eine Nachricht" zu "ein Vorgang, der eingeht".

def _telefon(position):
    """Ein Telefon -- Koerper plus leuchtende Vorderseite, wie in
    build_stations_zimmer.py, aber ohne den Wackelkontakt: hier steht es
    aufrecht auf einer Flaeche, nie auf dem Boden."""
    x, y, z = position
    teile = []
    teile.append(quader("telefon_koerper", (0.09, 0.02, 0.16), (x, y, z), "bildschirm_rahmen"))
    teile.append(quader("telefon_schirm", (0.075, 0.006, 0.14), (x, y - 0.011, z), "bildschirm"))
    return teile


def intake_1():
    """Ein Telefon mit Notizzettel auf einer Ablage -- mehr ist eine Anfrage
    am ersten Tag nicht. Der rote Punkt oben am Telefon ist die neue
    Nachricht, sparsam gesetzt (ein Akzent, nicht viele)."""
    teile = []
    teile.append(quader("ablage", (0.34, 0.24, 0.02), (0.0, 0.0, 0.30), "holz_schreibtisch"))
    teile.append(quader("notizzettel", (0.16, 0.12, 0.008), (-0.10, 0.02, 0.315), "notiz", -8.0))
    teile += _telefon((0.10, -0.02, 0.395))
    teile.append(quader("telefon_marker", (0.015, 0.008, 0.015), (0.135, -0.03, 0.465), "akzent_rot"))
    return teile


def intake_2():
    """Ein kleiner Tresen mit Ablage und Posteingang -- aus der einzelnen
    Notiz ist ein Stapel Post geworden. Eine der Ecken ragt heraus: das ist
    die dringende Anfrage (roter Marker), der Rest wartet ordentlich."""
    teile = []
    teile.append(quader("tresen_korpus", (0.62, 0.32, 0.62), (0.0, 0.0, 0.31), "holz_schreibtisch"))
    teile.append(quader("tresen_platte", (0.68, 0.38, 0.03), (0.0, 0.0, 0.635), "holz_hell"))
    teile.append(quader("ablage", (0.32, 0.22, 0.02), (0.0, 0.03, 0.665), "rahmen"))
    briefe = [(-0.06, 0.685, -6.0), (0.02, 0.700, 8.0), (-0.02, 0.715, -3.0), (0.06, 0.730, 10.0)]
    for i, (dx, dz, dreh) in enumerate(briefe):
        teile.append(quader("brief_%d" % i, (0.20, 0.14, 0.012), (dx, 0.03, dz), "notiz", dreh))
    teile.append(quader("brief_marker", (0.05, 0.03, 0.006), (0.06, 0.03, 0.737), "akzent_rot", 10.0))
    return teile


def intake_3():
    """Ein Empfangsplatz mit Bildschirm, an dem Anfragen sichtbar auflaufen
    -- ersetzt den Tresen vollstaendig durch einen groesseren Empfang (vgl.
    Klemmbrett-zu-Tisch-Prinzip der Vorlage). Die Zeilen auf dem Bildschirm
    sind eine Warteliste; zwei davon sind rot markiert -- neue Anfragen, die
    gerade erst eingegangen sind."""
    teile = []
    teile.append(quader("tresen_front", (0.90, 0.36, 0.75), (0.0, 0.0, 0.375), "holz_schreibtisch"))
    teile.append(quader("tresen_platte", (0.98, 0.44, 0.03), (0.0, 0.0, 0.765), "holz_hell"))
    teile.append(quader("monitor_fuss", (0.12, 0.09, 0.02), (0.0, -0.05, 0.79), "bildschirm_rahmen"))
    teile.append(quader("monitor_hals", (0.02, 0.02, 0.16), (0.0, -0.05, 0.87), "rahmen"))
    teile.append(quader("monitor_rahmen", (0.34, 0.02, 0.24), (0.0, -0.09, 1.07), "bildschirm_rahmen"))
    teile.append(quader("monitor_schirm", (0.30, 0.006, 0.20), (0.0, -0.084, 1.07), "bildschirm"))
    zeilen = [(0.985, "notiz"), (1.030, "akzent_rot"), (1.075, "notiz"), (1.120, "akzent_rot")]
    for i, (dz, farbe) in enumerate(zeilen):
        teile.append(quader("warteliste_%d" % i, (0.24, 0.004, 0.016), (0.0, -0.086, dz), farbe))
    teile.append(quader("tastatur", (0.20, 0.08, 0.012), (0.0, 0.10, 0.771), "tastatur"))
    briefe = [(-0.32, 0.700, -5.0), (-0.24, 0.712, 6.0)]
    for i, (dx, dz, dreh) in enumerate(briefe):
        teile.append(quader("brief_%d" % i, (0.18, 0.13, 0.012), (dx, 0.05, dz), "notiz", dreh))
    return teile


# --- Station 2: Konzept -------------------------------------------------------
# Welt 3: aus der spontanen Skizze wird sichtbare Struktur. Waechst vom
# Skizzenblock zur Korkwand mit Faeden zum grossen Whiteboard mit Stehtisch --
# von "ein Gedanke" zu "ein Plan, an dem mehrere Personen stehen koennen".

def buffer_1():
    """Ein Block mit Skizze -- eine grobe Webseiten-Struktur aus wenigen
    Strichen: Kopfzeile, zwei Inhaltsbloecke. Ein Strich ist dunkelblau
    hervorgehoben -- das ist der Teil, der zuerst gebaut wird."""
    teile = []
    teile.append(quader("block", (0.30, 0.22, 0.015), (0.0, 0.0, 0.315), "notiz"))
    teile.append(quader("skizze_kopf", (0.20, 0.006, 0.018), (0.0, -0.01, 0.335), "bildschirm_rahmen"))
    teile.append(quader("skizze_inhalt_a", (0.20, 0.006, 0.014), (0.0, -0.01, 0.358), "ordner_akzent"))
    teile.append(quader("skizze_inhalt_b", (0.20, 0.006, 0.014), (0.0, -0.01, 0.378), "bildschirm_rahmen"))
    teile.append(quader("stift", (0.012, 0.10, 0.012), (0.13, 0.05, 0.323), "rahmen", 22.0))
    return teile


def buffer_2():
    """Eine Korkwand mit Kaertchen und Faeden -- die einzelne Skizze ist eine
    Sammlung verbundener Gedanken geworden. Ein Kaertchen sticht dunkelblau
    hervor: der Teil des Konzepts, der schon feststeht."""
    teile = []
    teile.append(quader("wand_fuss", (0.64, 0.32, 0.05), (0.0, 0.0, 0.03), "holz_hell"))
    for dx in (-0.24, 0.24):
        teile.append(quader("wand_bein", (0.05, 0.05, 0.66), (dx, 0.0, 0.36), "rahmen"))
    teile.append(quader("wand_flaeche", (0.78, 0.05, 0.60), (0.0, 0.0, 0.72), "ordner"))
    karten = [(-0.26, 0.90, -6.0, "notiz"), (0.02, 0.96, 5.0, "ordner_akzent"),
              (0.24, 0.84, -8.0, "notiz"), (-0.10, 0.66, 7.0, "notiz"),
              (0.16, 0.60, -4.0, "notiz")]
    for i, (dx, dz, dreh, farbe) in enumerate(karten):
        teile.append(quader("karte_%d" % i, (0.13, 0.014, 0.10), (dx, -0.045, dz), farbe, dreh))
    faeden = [(-0.13, 0.93, 42.0, 0.16), (0.13, 0.90, -30.0, 0.18), (0.03, 0.72, 70.0, 0.20)]
    for i, (dx, dz, dreh, laenge) in enumerate(faeden):
        teile.append(quader("faden_%d" % i, (laenge, 0.006, 0.006), (dx, -0.048, dz), "bildschirm_rahmen", dreh))
    return teile


def buffer_3():
    """Ein grosses Whiteboard mit Struktur, davor ein Stehtisch -- ersetzt
    die Korkwand vollstaendig: aus verstreuten Kaertchen ist eine geordnete
    Flaeche geworden, an der man gemeinsam steht statt sitzt. Die goldene
    Markierung zeigt den Teil des Plans, der Geld bringt -- dieselbe Farbe
    wie bei special, weil beide vom Ertrag handeln, hier aber nur einmal und
    sparsam gesetzt."""
    teile = []
    teile.append(quader("board_flaeche", (1.00, 0.05, 0.66), (0.0, -0.30, 1.10), "whiteboard"))
    teile.append(quader("board_rahmen_o", (1.04, 0.07, 0.04), (0.0, -0.30, 1.45), "rahmen"))
    teile.append(quader("board_rahmen_u", (1.04, 0.07, 0.04), (0.0, -0.30, 0.75), "rahmen"))
    teile.append(quader("board_rahmen_l", (0.04, 0.07, 0.70), (-0.50, -0.30, 1.10), "rahmen"))
    teile.append(quader("board_rahmen_r", (0.04, 0.07, 0.70), (0.50, -0.30, 1.10), "rahmen"))
    teile.append(quader("struktur_kasten_a", (0.22, 0.01, 0.12), (-0.28, -0.275, 1.28), "bildschirm_rahmen"))
    teile.append(quader("struktur_kasten_b", (0.22, 0.01, 0.12), (0.02, -0.275, 1.28), "bildschirm_rahmen"))
    teile.append(quader("struktur_kasten_c", (0.22, 0.01, 0.12), (-0.13, -0.275, 1.00), "akzent_gold"))
    teile.append(quader("struktur_linie_a", (0.14, 0.01, 0.02), (-0.13, -0.275, 1.14), "bildschirm_rahmen", 20.0))
    teile.append(quader("struktur_linie_b", (0.14, 0.01, 0.02), (0.14, -0.275, 1.14), "bildschirm_rahmen", -20.0))
    teile.append(quader("stehtisch_platte", (0.42, 0.42, 0.03), (0.0, 0.30, 1.02), "holz_schreibtisch"))
    teile.append(zylinder("stehtisch_saeule", 0.035, 0.96, (0.0, 0.30, 0.535), "rahmen"))
    teile.append(quader("stehtisch_fuss", (0.30, 0.30, 0.03), (0.0, 0.30, 0.045), "rahmen"))
    return teile


# --- Station 3: Umsetzung -----------------------------------------------------
# Welt 3: der eigentliche Bau. Waechst vom Laptop auf schlichtem Tisch zum
# Schreibtisch mit zwei Monitoren zu zwei Arbeitsplaetzen mit drei Monitoren
# -- von "eine Person, ein Geraet" zu "ein Team, das nebeneinander arbeitet".

def processing_1():
    """Ein Laptop auf einem schlichten Tisch -- anders als im Zimmer steht
    hier von Anfang an ein echter Tisch darunter, kein Boden."""
    teile = []
    teile.append(quader("tisch_platte", (0.50, 0.36, 0.03), (0.0, 0.0, 0.585), "holz_schreibtisch"))
    for dx in (-0.20, 0.20):
        teile.append(quader("tisch_bein", (0.03, 0.30, 0.57), (dx, 0.0, 0.285), "rahmen"))
    teile.append(quader("laptop_deck", (0.30, 0.20, 0.02), (0.0, 0.0, 0.61), "bildschirm_rahmen"))
    teile.append(quader("laptop_lehne", (0.30, 0.02, 0.19), (0.0, -0.10, 0.695), "bildschirm_rahmen"))
    teile.append(quader("laptop_schirm", (0.25, 0.006, 0.15), (0.0, -0.094, 0.695), "bildschirm"))
    return teile


def processing_2():
    """Schreibtisch mit zwei Monitoren -- ersetzt den Laptop vollstaendig:
    aus einem Geraet ist ein Arbeitsplatz geworden. Ein Blatt aus einer
    Vorlagensammlung liegt bereit."""
    teile = []
    teile.append(quader("tisch_platte", (0.90, 0.42, 0.03), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    for dx in (-0.40, 0.40):
        teile.append(quader("tisch_bein", (0.03, 0.36, 0.70), (dx, 0.0, 0.36), "rahmen"))
    for i, dx in enumerate((-0.22, 0.22)):
        teile.append(quader("monitor_fuss_%d" % i, (0.10, 0.08, 0.02), (dx, -0.08, 0.745), "bildschirm_rahmen"))
        teile.append(quader("monitor_rahmen_%d" % i, (0.26, 0.02, 0.18), (dx, -0.12, 0.905), "bildschirm_rahmen"))
        teile.append(quader("monitor_schirm_%d" % i, (0.22, 0.006, 0.14), (dx, -0.114, 0.905), "bildschirm"))
    teile.append(quader("tastatur", (0.26, 0.10, 0.012), (0.0, 0.10, 0.741), "tastatur"))
    teile.append(quader("maus", (0.05, 0.08, 0.02), (0.18, 0.12, 0.745), "tastatur"))
    teile.append(quader("vorlage", (0.16, 0.20, 0.01), (0.38, 0.14, 0.735), "notiz", -8.0))
    return teile


def processing_3():
    """Zwei Arbeitsplaetze nebeneinander, drei Monitore, Tastaturen -- ein
    langer Tisch statt einem, eine Trennwand markiert die zwei Plaetze. Der
    linke Platz hat zwei Monitore, der rechte einen -- drei zusammen, wie im
    Auftrag verlangt."""
    teile = []
    teile.append(quader("tisch_platte", (1.60, 0.44, 0.03), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    for dx in (-0.74, -0.25, 0.25, 0.74):
        teile.append(quader("tisch_bein", (0.03, 0.38, 0.70), (dx, 0.0, 0.36), "rahmen"))
    teile.append(quader("trenner", (0.02, 0.30, 0.30), (0.0, -0.05, 0.895), "rahmen"))
    for i, dx in enumerate((-0.58, -0.26)):
        teile.append(quader("monitor_a_fuss_%d" % i, (0.09, 0.07, 0.02), (dx, -0.08, 0.745), "bildschirm_rahmen"))
        teile.append(quader("monitor_a_rahmen_%d" % i, (0.22, 0.02, 0.16), (dx, -0.12, 0.885), "bildschirm_rahmen"))
        teile.append(quader("monitor_a_schirm_%d" % i, (0.18, 0.006, 0.12), (dx, -0.114, 0.885), "bildschirm"))
    teile.append(quader("monitor_b_fuss", (0.10, 0.08, 0.02), (0.42, -0.08, 0.745), "bildschirm_rahmen"))
    teile.append(quader("monitor_b_rahmen", (0.24, 0.02, 0.17), (0.42, -0.12, 0.895), "bildschirm_rahmen"))
    teile.append(quader("monitor_b_schirm", (0.20, 0.006, 0.13), (0.42, -0.114, 0.895), "bildschirm"))
    teile.append(quader("tastatur_a", (0.22, 0.09, 0.012), (-0.42, 0.10, 0.741), "tastatur"))
    teile.append(quader("tastatur_b", (0.22, 0.09, 0.012), (0.42, 0.10, 0.741), "tastatur"))
    teile.append(quader("maus_a", (0.045, 0.07, 0.02), (-0.28, 0.11, 0.745), "tastatur"))
    teile.append(quader("maus_b", (0.045, 0.07, 0.02), (0.56, 0.11, 0.745), "tastatur"))
    return teile


# --- Station 4: Deployment ----------------------------------------------------
# Welt 3: die Automatisierung der ganzen Kette. Waechst vom kleinen Server im
# Regal zum Rack mit drei Einschueben zum vollen Rack mit Statusleuchten und
# geordneter Kabelfuehrung -- von "ein Geraet" zu "Infrastruktur".

def transport_1():
    """Ein kleiner Server im Regal -- ein Brett, zwei Traeger, ein Geraet mit
    Betriebsleuchte. Das Kabel liegt sauber senkrecht, nicht lose wie im
    Zimmer."""
    teile = []
    for dx in (-0.16, 0.16):
        teile.append(quader("traeger", (0.03, 0.20, 0.42), (dx, 0.0, 0.21), "rahmen"))
    teile.append(quader("brett", (0.40, 0.22, 0.025), (0.0, 0.0, 0.425), "holz_hell"))
    teile.append(quader("server_gehaeuse", (0.30, 0.18, 0.08), (0.0, 0.0, 0.478), "bildschirm_rahmen"))
    teile.append(quader("server_led", (0.02, 0.01, 0.01), (0.12, -0.08, 0.478), "led_gruen"))
    teile.append(quader("kabel", (0.01, 0.01, 0.42), (0.16, 0.09, 0.21), "bildschirm_rahmen"))
    return teile


def transport_2():
    """Ein Rack mit drei Einschueben -- ersetzt Regal und Einzelgeraet durch
    einen eigenen kleinen Schrank. Ein Kabelkanal am Fuss haelt die
    Zuleitung geordnet."""
    teile = []
    for dx in (-0.18, 0.18):
        teile.append(quader("rack_rahmen", (0.03, 0.26, 0.56), (dx, 0.0, 0.30), "bildschirm_rahmen"))
    teile.append(quader("rack_deckel", (0.39, 0.26, 0.03), (0.0, 0.0, 0.59), "rahmen"))
    teile.append(quader("rack_boden", (0.39, 0.26, 0.03), (0.0, 0.0, 0.03), "rahmen"))
    for i, hz in enumerate((0.15, 0.30, 0.45)):
        teile.append(quader("einschub_%d" % i, (0.32, 0.22, 0.11), (0.0, 0.0, hz), "bildschirm_rahmen"))
        if i != 1:
            teile.append(quader("einschub_led_%d" % i, (0.02, 0.01, 0.01), (0.12, -0.12, hz), "led_gruen"))
    teile.append(quader("kabelkanal", (0.39, 0.06, 0.03), (0.0, 0.13, 0.045), "rahmen"))
    return teile


def transport_3():
    """Ein volles Rack mit Statusleuchten und Kabelfuehrung -- mehr
    Einschuebe, mehrere Leuchten, und an der Seite ein gebuendeltes Kabelpaar
    statt loser Strippen. Eine goldene Leuchte zwischen den gruenen zeigt
    einen laufenden Sondervorgang -- Statusleuchten duerfen vom Bildschirm-
    blau abweichen, das ist hier bewusst genutzt."""
    teile = []
    for dx in (-0.20, 0.20):
        teile.append(quader("rack_rahmen", (0.03, 0.30, 1.10), (dx, 0.0, 0.58), "bildschirm_rahmen"))
    teile.append(quader("rack_deckel", (0.43, 0.30, 0.03), (0.0, 0.0, 1.13), "rahmen"))
    teile.append(quader("rack_boden", (0.43, 0.30, 0.03), (0.0, 0.0, 0.03), "rahmen"))
    hoehen = (0.16, 0.33, 0.50, 0.67, 0.84, 1.01)
    for i, hz in enumerate(hoehen):
        teile.append(quader("einschub_%d" % i, (0.36, 0.26, 0.10), (0.0, 0.0, hz),
                            "bildschirm_rahmen" if i % 2 else "rahmen"))
        if i in (0, 2, 4):
            farbe = "akzent_gold" if i == 2 else "led_gruen"
            teile.append(quader("einschub_led_%d" % i, (0.02, 0.01, 0.01), (0.14, -0.14, hz), farbe))
    teile.append(quader("kabelkanal", (0.43, 0.06, 0.03), (0.0, 0.15, 0.045), "rahmen"))
    for i, dz in enumerate((0.20, 1.06)):
        teile.append(quader("kabelbuendel_%d" % i, (0.015, 0.015, 0.86 if i == 0 else 0.10),
                            (0.24, 0.15, 0.10 + (0.43 if i == 0 else 1.01)), "bildschirm_rahmen"))
    return teile


# --- Station 5: Betreuung ------------------------------------------------------
# Welt 3: der Erloes, der weiterlaeuft. Waechst vom einzelnen Ordner auf dem
# Tisch zum Regal mit Kundenordnern und Kalender zum Bildschirm mit
# Kennzahlen davor ein Besprechungsstuhl -- von "eine Akte" zu "ein
# Kundenstamm, den man im Blick behaelt".

def special_1():
    """Ein Ordner auf dem Tisch -- eine einzelne laufende Betreuung, noch
    ohne System."""
    teile = []
    teile.append(quader("tisch_platte", (0.44, 0.34, 0.03), (0.0, 0.0, 0.585), "holz_schreibtisch"))
    for dx in (-0.17, 0.17):
        teile.append(quader("tisch_bein", (0.03, 0.28, 0.57), (dx, 0.0, 0.285), "rahmen"))
    teile.append(quader("ordner", (0.10, 0.22, 0.30), (0.0, 0.0, 0.75), "ordner"))
    teile.append(quader("stift", (0.012, 0.10, 0.012), (0.12, -0.02, 0.607), "akzent_gold", 18.0))
    return teile


def special_2():
    """Ein Regal mit Kundenordnern und ein Kalender -- aus der einzelnen
    Akte ist ein Bestand geworden. Der goldene Strich auf dem Kalender
    markiert den heutigen Tag -- derselbe Ton wie die Kennzahl in Stufe 3,
    weil beide vom laufenden Ertrag handeln."""
    teile = []
    for x in (-0.24, 0.24):
        seite = "l" if x < 0 else "r"
        teile.append(quader("seite_%s" % seite, (0.04, 0.24, 1.00), (x, 0.0, 0.50), "holz_hell"))
    for i, z in enumerate((0.02, 0.36, 0.70)):
        teile.append(quader("boden_%d" % i, (0.52, 0.24, 0.03), (0.0, 0.0, z), "holz_hell"))
    ordner_pos = [(-0.16, 0.19, "ordner"), (-0.02, 0.19, "ordner_akzent"), (0.14, 0.19, "ordner"),
                  (-0.10, 0.53, "ordner")]
    for i, (dx, dz, farbe) in enumerate(ordner_pos):
        teile.append(quader("ordner_%d" % i, (0.09, 0.20, 0.32), (dx, 0.0, dz), farbe))
    teile.append(quader("kalender_basis", (0.18, 0.10, 0.02), (0.30, 0.16, 0.71), "rahmen"))
    teile.append(quader("kalender_block", (0.16, 0.08, 0.14), (0.30, 0.16, 0.78), "notiz"))
    teile.append(quader("kalender_markierung", (0.10, 0.01, 0.015), (0.30, 0.12, 0.80), "akzent_gold"))
    return teile


def special_3():
    """Ein Bildschirm mit Kennzahlen, davor ein Besprechungsstuhl -- ersetzt
    das Regal vollstaendig: aus Akten ist ein Gespraech geworden. Die drei
    goldenen Balken auf dem Schirm steigen -- Betreuung bringt hier
    dauerhafte Grundeinnahme, keinen Einmalbetrag (docs/WELTEN.md)."""
    teile = []
    teile.append(quader("monitor_fuss", (0.12, 0.09, 0.02), (0.0, -0.30, 0.79), "bildschirm_rahmen"))
    teile.append(quader("monitor_hals", (0.02, 0.02, 0.14), (0.0, -0.30, 0.86), "rahmen"))
    teile.append(quader("monitor_rahmen", (0.36, 0.02, 0.26), (0.0, -0.34, 1.06), "bildschirm_rahmen"))
    teile.append(quader("monitor_schirm", (0.32, 0.006, 0.22), (0.0, -0.334, 1.06), "bildschirm"))
    balken = [(-0.10, 0.03, 0.960), (0.02, 0.05, 0.975), (0.14, 0.08, 1.000)]
    for i, (dx, hoehe, dz) in enumerate(balken):
        teile.append(quader("kennzahl_balken_%d" % i, (0.06, 0.004, hoehe), (dx, -0.332, dz), "akzent_gold"))
    x, y = 0.0, 0.28
    teile.append(quader("stuhl_sitz", (0.36, 0.34, 0.05), (x, y, 0.36), "bildschirm_rahmen"))
    teile.append(quader("stuhl_lehne", (0.36, 0.05, 0.36), (x, y + 0.15, 0.56), "bildschirm_rahmen"))
    for dx in (-0.15, 0.15):
        teile.append(quader("stuhl_armlehne", (0.04, 0.20, 0.03), (x + dx, y - 0.02, 0.44), "rahmen"))
    teile.append(zylinder("stuhl_saeule", 0.035, 0.32, (x, y, 0.18), "rahmen"))
    teile.append(quader("stuhl_fuss_x", (0.40, 0.04, 0.03), (x, y, 0.03), "rahmen"))
    teile.append(quader("stuhl_fuss_y", (0.04, 0.40, 0.03), (x, y, 0.03), "rahmen"))
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
    print("=== STATIONSMODULE WELT 3 -- WEBSEITEN ===")
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
