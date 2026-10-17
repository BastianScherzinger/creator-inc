"""Erzeugt die Stationsmodule fuer Welt 1 "zimmer" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_zimmer.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und Kommentarstil
folgen bewusst art_source/scripts/build_stations.py (Welt "amt"): manche
Stufen bauen wortwoertlich auf der vorigen auf (teile = vorherige() + neu),
andere ersetzen das improvisierte Vorgaenger-Teil durch ein reicheres
Aequivalent -- genau wie dort schon Klemmbrett zu Tisch wurde. Beides ist im
Sinne von ART_DIRECTION R4 richtig: Hauptsache, Stufe 2 ist unzweifelhaft
mehr/besser als Stufe 1.

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist im Amt eine Wartebank, hier ein Klapptisch mit Handy drauf.
Die Zuordnung steht in data/themes/zimmer/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 1 -- zimmer"):
    intake      Idee        Zettel -> Pinnwand -> Whiteboard
    buffer      Aufnahme    Handy auf Buechern -> Stativ -> Stativ+2 Leuchten+Mikro
    processing  Schnitt     alter Laptop -> +Monitor auf Buechern -> 2 Monitore+Staender
    transport   Upload      Router -> Router+NAS -> kleines Rack
    special     Kommentar   ein Telefon -> +Notizblock -> +zweiter Stuhl

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Harte Groessenregel dieser Aufgabe (staerker als das allgemeine Stationsbudget
aus ART_DIRECTION 7): jedes Modul passt in 1,8 x 1,8 Grundflaeche, hoechstens
1,6 hoch, Ursprung in der Mitte der Grundflaeche auf z = 0.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- siehe build_room_zimmer.py, dort ist der Fehler drei
# Mal in Folge passiert: glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. linear = s^2,2. Alle Werte unten sind so gerechnet.
#
# Fuenf Eintraege sind woertlich aus build_room_zimmer.py uebernommen (dort
# bereits korrekt gerechnet) -- Rahmen/Kabel/Textil/Heizkoerper/Sockel sollen
# in diesem Zimmer genau gleich aussehen, egal ob sie an einer Wand oder an
# einer Station haengen. Die uebrigen Eintraege fehlten dort und sind hier
# frisch aus ihrem sRGB-Zielwert gerechnet, NICHT aus den (nicht gamma-
# korrigierten) Zahlen in build_stations.py kopiert -- sonst waere der
# Fehler nur an einer neuen Stelle wiederholt worden.
PALETTE = {
    # -- uebernommen aus build_room_zimmer.py --
    "rahmen":     (0.557, 0.592, 0.659, 1.0),   # #8e97a8 globaler Metallton
    "kabel":      (0.006, 0.006, 0.008, 1.0),   # fast schwarzer Kunststoff
    "textil":     (0.268, 0.218, 0.173, 1.0),   # verwaschener Stoff/Kork-Ton
    "heizkoerper":(0.302, 0.268, 0.199, 1.0),   # vergilbtes Weiss, alter Kunststoff
    "wand_unten": (0.082, 0.077, 0.069, 1.0),   # dunkler Rahmen-/Sockelton

    # -- ergaenzt, frisch nach linear = s^2,2 gerechnet --
    "papier":            (0.916, 0.883, 0.812, 1.0),  # #f5f1e8 Papier
    "holz":              (0.592, 0.482, 0.330, 1.0),  # #c9b79a Amtsbeige: Tisch, Buecher, Stative
    "moebel":            (0.056, 0.070, 0.106, 1.0),  # #454c5c Grund mittel: Gehaeuse, Gestelle
    "akzent_warm":       (0.891, 0.405, 0.040, 1.0),  # #f2a93b Aktion: Marker, Pins, warme Lampe
    "bildschirm":        (0.066, 0.344, 0.680, 1.0),  # #4a9dd6 Akzent kuehl: JEDER Bildschirm glueht so
    "led_gruen":         (0.104, 0.530, 0.198, 1.0),  # #5bbf7a Erfolg: Geraete-Betriebsleuchte
    "kunststoff_dunkel": (0.029, 0.033, 0.041, 1.0),  # neutrales Dunkelgrau: Laptop-, Handy-, Router-Gehaeuse
}

AUSGABE = "project/assets/stations/zimmer"


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
    einem runden Zylinder nicht sichtbar, kostet aber das Dreifache. Achtung
    beim Budgetieren: Blender zaehlt jede Deckflaeche als EIN Vieleck, das
    beim Export in (seiten - 2) Dreiecke zerfaellt -- ein Zylinder mit acht
    Seiten hat real 4*8-4 = 28 Dreiecke, nicht die 20, die die einfache
    "Polygone * 2"-Formel unten anzeigt. Deshalb wird hier bewusst sparsam
    mit Zylindern budgetiert, nicht nach der Anzeige."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Station 1: Idee ---------------------------------------------------------
# Welt 1: der Anfang eines Gedankens. Waechst vom einzelnen Zettel auf dem
# Boden zur Pinnwand mit mehreren Zetteln zum Whiteboard mit Struktur --
# von "ein Einfall" zu "ein Plan".

def intake_1():
    """Ein einzelner Zettel auf dem Boden, ein Stift daneben. Mehr ist eine
    Idee am ersten Tag nicht."""
    teile = []
    teile.append(quader("zettel", (0.30, 0.22, 0.01), (0.0, 0.0, 0.01), "papier", 12.0))
    teile.append(quader("stift", (0.02, 0.16, 0.02), (0.22, -0.10, 0.015), "akzent_warm", 38.0))
    return teile


def intake_2():
    """Eine Pinnwand auf einem Staender, mehrere Zettel dran -- aus dem
    losen Einfall ist eine Sammlung geworden. Die Zettel tragen abwechselnd
    Papier- und Markerfarbe: manche sind nur Notizen, manche schon markiert."""
    teile = []
    teile.append(quader("tafel_fuss", (0.66, 0.34, 0.05), (0.0, 0.0, 0.03), "holz"))
    teile.append(quader("tafel_flaeche", (0.78, 0.06, 0.62), (0.0, 0.0, 0.35), "textil"))
    positionen = [(-0.24, 0.46, -8.0), (0.05, 0.50, 5.0), (0.26, 0.40, -4.0),
                  (-0.10, 0.30, 10.0), (0.14, 0.22, -12.0)]
    for i, (dx, dz, dreh) in enumerate(positionen):
        farbe = "akzent_warm" if i % 3 == 0 else "papier"
        teile.append(quader("zettel_%d" % i, (0.13, 0.02, 0.10),
                            (dx, -0.035, dz), farbe, dreh))
    return teile


def intake_3():
    """Ein Whiteboard mit gezeichneter Struktur und einer Stiftablage --
    NICHT die Pinnwand plus Zusatz, sondern ihr Nachfolger: aus wild
    gepinnten Zetteln ist eine geordnete Flaeche geworden (vgl. Klemmbrett zu
    Tisch in build_stations.py). Die drei Stiftfarben sind absichtlich die
    drei Akzenttoene der anderen Stationen -- als liefen hier alle Faeden
    zusammen."""
    teile = []
    teile.append(quader("staender_fuss", (0.80, 0.36, 0.05), (0.0, 0.0, 0.03), "holz"))
    for dx in (-0.34, 0.34):
        teile.append(quader("staender_bein", (0.05, 0.05, 0.86), (dx, 0.20, 0.46), "moebel"))
    teile.append(quader("board", (0.92, 0.05, 0.68), (0.0, -0.02, 0.92), "papier"))
    # Struktur: zwei Kaesten mit Verbindungslinie -- die Idee hat jetzt Form.
    teile.append(quader("struktur_kasten_a", (0.20, 0.01, 0.14), (-0.24, -0.05, 1.02), "akzent_warm"))
    teile.append(quader("struktur_kasten_b", (0.20, 0.01, 0.14), (0.22, -0.05, 0.84), "bildschirm"))
    teile.append(quader("struktur_linie", (0.24, 0.01, 0.02), (-0.01, -0.05, 0.94), "akzent_warm", 24.0))
    # Ablage mit drei Stiften
    teile.append(quader("ablage", (0.30, 0.06, 0.03), (0.0, 0.18, 0.56), "holz"))
    for i, farbe in enumerate(("akzent_warm", "bildschirm", "led_gruen")):
        teile.append(quader("stift_%d" % i, (0.02, 0.14, 0.02),
                            (-0.10 + i * 0.10, 0.16, 0.58), farbe, 4.0 * i))
    return teile


# --- Station 2: Aufnahme -----------------------------------------------------
# Welt 1: die Kamera. Waechst vom Handy auf Buechern zum echten Stativ mit
# Reflektor zum Stativ mit zwei Leuchten und Galgenmikrofon -- von
# "improvisiert" zu "ausgeruestet".

def _handy(position):
    """Ein Telefon -- Koerper plus leuchtende Vorderseite. Wird von mehreren
    Stationen gebraucht (buffer und special zeigen beide ein Handy), deshalb
    als eigene Funktion wie stuhl() im Amt-Vorbild."""
    x, y, z = position
    teile = []
    teile.append(quader("handy_koerper", (0.09, 0.02, 0.16), (x, y, z), "kunststoff_dunkel"))
    teile.append(quader("handy_schirm", (0.075, 0.006, 0.14), (x, y - 0.011, z), "bildschirm"))
    return teile


def buffer_1():
    """Handy auf einem Buecherstapel, die Schreibtischlampe schief daneben
    -- das ist noch kein Aufnahmeplatz, nur ein Behelf."""
    teile = []
    for i, (dz, dreh) in enumerate([(0.02, 0.0), (0.06, 6.0)]):
        teile.append(quader("buch_%d" % i, (0.20, 0.15, 0.035), (-0.10, 0.05, dz), "holz", dreh))
    teile += _handy((-0.10, 0.05, 0.16))
    # Lampe -- "schief" heisst hier: Schirm und Arm sind gegeneinander
    # verdreht, nicht sauber ausgerichtet wie an einem echten Arbeitsplatz.
    teile.append(quader("lampe_fuss", (0.10, 0.10, 0.02), (0.30, -0.10, 0.02), "moebel"))
    teile.append(quader("lampe_arm", (0.03, 0.03, 0.30), (0.30, -0.10, 0.17), "rahmen", 14.0))
    teile.append(quader("lampe_schirm", (0.14, 0.10, 0.08), (0.27, -0.16, 0.32), "akzent_warm", -20.0))
    return teile


def _stativ_mit_handy():
    """Ein echtes Stativ: Mittelsaeule, drei radial gespreizte Fuesse, Kopf,
    Handy. Wird von Stufe 2 und Stufe 3 gebraucht -- das Stativ bleibt,
    nur was daneben steht, wird mehr."""
    teile = []
    teile.append(zylinder("stativ_saeule", 0.025, 0.62, (0.0, 0.10, 0.35), "rahmen"))
    for i in range(3):
        winkel = math.radians(90.0 + i * 120.0)
        dx, dy = math.cos(winkel) * 0.22, 0.10 + math.sin(winkel) * 0.22
        teile.append(quader("stativ_fuss_%d" % i, (0.28, 0.035, 0.035), (dx, dy, 0.02), "rahmen",
                            math.degrees(winkel)))
    teile.append(quader("stativ_kopf", (0.14, 0.10, 0.03), (0.0, 0.10, 0.67), "moebel"))
    teile += _handy((0.0, 0.06, 0.75))
    return teile


def buffer_2():
    """Echtes Stativ plus Reflektor -- der Behelf ist Ausruestung
    geworden."""
    teile = _stativ_mit_handy()
    teile.append(zylinder("reflektor_stab", 0.02, 0.62, (-0.45, 0.05, 0.32), "rahmen"))
    teile.append(quader("reflektor_flaeche", (0.02, 0.34, 0.44), (-0.45, 0.05, 0.64), "papier", 8.0))
    return teile


def buffer_3():
    """Stativ, zwei Leuchten und ein Mikrofon am Galgen -- der Reflektor
    reichte fuer ein Interview nicht mehr, jetzt wird produziert."""
    teile = _stativ_mit_handy()
    for i, dx in enumerate((-0.42, 0.42)):
        teile.append(quader("leuchte_stab_%d" % i, (0.03, 0.03, 0.56), (dx, 0.05, 0.30), "rahmen"))
        teile.append(quader("leuchte_panel_%d" % i, (0.24, 0.02, 0.30), (dx, 0.05 - 0.02 * (i * 2 - 1), 0.60),
                            "papier"))
    # Galgenmikrofon: Fuss, Arm, Kapsel -- der Arm haengt schraeg ueber
    # den Aufnahmeplatz, wie ein echter Boom-Arm.
    teile.append(quader("galgen_fuss", (0.12, 0.12, 0.03), (0.0, -0.35, 0.02), "moebel"))
    teile.append(quader("galgen_arm", (0.03, 0.50, 0.03), (0.0, -0.15, 0.60), "rahmen", 0.0))
    teile.append(quader("galgen_kapsel", (0.05, 0.05, 0.09), (0.0, 0.08, 0.55), "kunststoff_dunkel"))
    return teile


# --- Station 3: Schnitt ------------------------------------------------------
# Welt 1: der Schnittplatz. Waechst vom alten Laptop zum Laptop mit zweitem
# Monitor auf Buechern zu zwei Monitoren auf echtem Staender mit externer
# Tastatur -- von "ein Geraet" zu "ein Arbeitsplatz".

def processing_1():
    """Ein alter Laptop, aufgeklappt, ein Kabel, das lose danebenliegt --
    mehr Arbeitsplatz ist das noch nicht."""
    teile = []
    teile.append(quader("laptop_deck", (0.32, 0.22, 0.02), (0.0, 0.0, 0.03), "heizkoerper"))
    teile.append(quader("laptop_lehne", (0.32, 0.02, 0.20), (0.0, -0.11, 0.14), "heizkoerper"))
    teile.append(quader("laptop_schirm", (0.27, 0.006, 0.16), (0.0, -0.104, 0.14), "bildschirm"))
    teile.append(quader("kabel_lose", (0.02, 0.24, 0.01), (0.22, 0.10, 0.005), "kabel", 30.0))
    return teile


def processing_2():
    """Laptop plus zweiter Monitor auf einem Buecherstapel -- die zweite
    Flaeche ist behelfsmaessig erhoeht, nicht eingerichtet."""
    teile = processing_1()
    for i, (dz, dreh) in enumerate([(0.02, 0.0), (0.06, -5.0), (0.10, 4.0)]):
        teile.append(quader("buch_%d" % i, (0.22, 0.17, 0.035), (0.36, 0.02, dz), "holz", dreh))
    teile.append(quader("monitor_rahmen", (0.26, 0.02, 0.18), (0.36, -0.06, 0.24), "kunststoff_dunkel"))
    teile.append(quader("monitor_schirm", (0.22, 0.006, 0.14), (0.36, -0.054, 0.24), "bildschirm"))
    return teile


def processing_3():
    """Zwei Monitore auf einem echten Staender, externe Tastatur und Maus --
    aus dem Behelf ist ein richtiger Schnittplatz geworden. Ersetzt das
    Buecher-Provisorium vollstaendig, statt es nur zu ergaenzen."""
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
    teile.append(quader("maus", (0.05, 0.08, 0.03), (0.20, 0.12, 0.44), "kunststoff_dunkel"))
    return teile


# --- Station 4: Upload -------------------------------------------------------
# Welt 1: der Versand. Waechst vom einzelnen Router zum Router mit kleinem
# NAS zu einem kleinen Rack mit mehreren Einschueben -- von "ein Blinklicht"
# zu "eine Infrastruktur".

def transport_1():
    """Ein Router mit einer blinkenden Leuchte -- der Akzent ist bewusst
    winzig, wie in ART_DIRECTION gefordert: sparsam, aber unuebersehbar."""
    teile = []
    teile.append(quader("router_gehaeuse", (0.22, 0.14, 0.035), (0.0, 0.0, 0.02), "kunststoff_dunkel"))
    for i, dx in enumerate((-0.06, 0.06)):
        teile.append(quader("router_antenne_%d" % i, (0.015, 0.015, 0.16), (dx, 0.0, 0.12), "rahmen",
                            6.0 * (i * 2 - 1)))
    teile.append(quader("router_led", (0.02, 0.01, 0.01), (0.08, -0.06, 0.045), "led_gruen"))
    return teile


def transport_2():
    """Router plus ein kleines NAS daneben -- es ist jetzt mehr als ein
    Blinklicht, es ist ein kleines System."""
    teile = transport_1()
    teile.append(quader("nas_gehaeuse", (0.16, 0.16, 0.14), (0.24, 0.02, 0.09), "moebel"))
    for i, dz in enumerate((0.04, 0.11)):
        teile.append(quader("nas_schacht_%d" % i, (0.10, 0.005, 0.025), (0.24, -0.075, dz), "rahmen"))
    teile.append(quader("nas_led", (0.015, 0.008, 0.008), (0.29, -0.075, 0.14), "led_gruen"))
    return teile


def transport_3():
    """Ein kleines Rack mit mehreren Einschueben -- ersetzt den Router
    vollstaendig: aus einem Geraet auf dem Tisch ist ein eigener Schrank
    geworden. Nur zwei der fuenf Einschuebe leuchten -- alles leuchtend
    waere Dekoration, kein Signal (ART_DIRECTION R3)."""
    teile = []
    for dx in (-0.20, 0.20):
        teile.append(quader("rack_rahmen", (0.03, 0.30, 0.62), (dx, 0.0, 0.33), "moebel"))
    teile.append(quader("rack_deckel", (0.43, 0.30, 0.03), (0.0, 0.0, 0.65), "moebel"))
    teile.append(quader("rack_boden", (0.43, 0.30, 0.03), (0.0, 0.0, 0.03), "moebel"))
    hoehen = (0.11, 0.21, 0.31, 0.41, 0.51)
    for i, hz in enumerate(hoehen):
        teile.append(quader("einschub_%d" % i, (0.36, 0.26, 0.07), (0.0, 0.0, hz),
                            "kunststoff_dunkel" if i % 2 else "rahmen"))
        if i in (1, 3):
            teile.append(quader("einschub_led_%d" % i, (0.02, 0.01, 0.01), (0.14, -0.14, hz), "led_gruen"))
    return teile


# --- Station 5: Der Kommentar ------------------------------------------------
# Welt 1: der Auftrag, der aus einem Kommentar entsteht. Waechst vom
# einzelnen Telefon auf dem Tisch zum Telefon mit Notizblock zum zweiten
# Stuhl davor -- von "eine Nachricht" zu "ein Gegenueber".

def special_1():
    """Ein einzelnes Telefon auf dem Tisch. Noch ist es nur eine
    Benachrichtigung."""
    teile = []
    teile.append(quader("tisch_platte", (0.50, 0.36, 0.03), (0.0, 0.0, 0.38), "holz"))
    for dx in (-0.20, 0.20):
        teile.append(quader("tisch_bein", (0.04, 0.30, 0.36), (dx, 0.0, 0.19), "rahmen"))
    teile += _handy((0.0, 0.02, 0.475))
    return teile


def special_2():
    """Telefon plus Notizblock mit Anforderungen -- aus der Nachricht ist
    eine Aufgabe geworden. Die drei kurzen Striche sind die Anforderungen:
    lesbar als Liste, ohne dass ein Buchstabe modelliert werden muss."""
    teile = special_1()
    teile.append(quader("notizblock", (0.20, 0.26, 0.015), (-0.16, 0.00, 0.395), "papier", -6.0))
    for i in range(3):
        teile.append(quader("notiz_zeile_%d" % i, (0.13, 0.012, 0.004),
                            (-0.16, -0.07 + i * 0.05, 0.404), "akzent_warm", -6.0))
    return teile


def special_3():
    """Ein zweiter Stuhl davor -- jemand sitzt dir jetzt gegenueber. Der
    Stuhl allein erzaehlt das, ganz ohne Figur: er steht zugewandt zum
    Tisch, nicht danebengeschoben."""
    teile = special_2()
    x = 0.0
    y = 0.42
    teile.append(quader("stuhl_sitz", (0.34, 0.32, 0.05), (x, y, 0.34), "moebel"))
    teile.append(quader("stuhl_lehne", (0.34, 0.05, 0.34), (x, y + 0.14, 0.54), "moebel"))
    for dx in (-0.13, 0.13):
        for dy in (-0.12, 0.12):
            teile.append(quader("stuhl_bein", (0.04, 0.04, 0.34), (x + dx, y + dy, 0.17), "rahmen"))
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
    print("=== STATIONSMODULE WELT 1 -- ZIMMER ===")
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
