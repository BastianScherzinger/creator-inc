"""Erzeugt die Stationsmodule fuer Welt 5 "produkt" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_produkt.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und Kommentarstil
folgen der Strukturvorlage art_source/scripts/build_stations_webseiten.py:
manche Stufen bauen woertlich auf der vorigen auf, andere ersetzen das
schlichtere Vorgaenger-Teil durch ein reicheres Aequivalent. Hauptsache, jede
Stufe ist unzweifelhaft mehr/besser als die vorige (ART_DIRECTION R4).

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist in Welt 3 ein Telefon auf einem Tresen, hier ein Bildschirm,
der Leads von allein anzeigt. Die Zuordnung steht in
data/themes/produkt/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 5 --
produkt"; Kette laut Auftrag: Leads -> Vorlage -> Ausspielung ->
Infrastruktur -> Abo):
    intake      Leads          1 Bildschirm+Liste -> 2 Bildschirme, Karte -> Monitorwand+Punkte
    buffer      Vorlage        Musterblatt -> Regal mit Varianten -> Baukasten aus Bloecken
    processing  Ausspielung    1 Server -> 3 Server nebeneinander -> Reihe, gleiche Leuchte im Takt
    transport   Infrastruktur  Netzwerkschrank -> +Kuehlung -> 2 Schraenke+Trasse+Notstrom
    special     Abo            1 Zaehler -> Bildschirm mit Kurve -> grosse Kennzahlwand

HINWEIS ZUR PALETTE: build_room_produkt.py ist waehrend dieser Aufgabe
fertig geworden -- seine Palette wird hier uebernommen, nicht die von
build_room_buero.py. "rahmen" ist woertlich dessen Wert (der globale
Metallton, den auch der Raum unveraendert weiterfuehrt). "led_gruen" und
"akzent_teal" sind ebenfalls woertlich uebernommen: der Raum fuehrt fuer
Welt 5 bewusst ein gesaettigteres Leuchten-Gruen ein (statt des sonst
ueberall gleichen led_gruen aus build_stations_zimmer.py) und einen
Cyan-Gruenton fuer die Kartenpunkte (dort "karte_punkt_glut") -- hier
"akzent_teal" genannt, weil eine Station keine Emission exportiert, nur die
Basisfarbe. "kuehlung_hell/_dunkel" sind die Wand- bzw. Schrankfront-Toene
des Raums, hier fuer die Kuehlung der Infrastruktur zweitverwendet, damit
kein einziger Ton in dieser Datei erfunden ist, der nicht auch im Raum
vorkommt oder global ist. Nur "akzent_gold" (dieselbe Bedeutung wie in
Welt 3: wachsender Ertrag) und "notiz" (das projektweite Papier, wie in
build_stations_zimmer.py/build_stations_webseiten.py) kommen von
ausserhalb des Raums. "bildschirm" und "bildschirm_rahmen" sind die
globalen Toene, die in JEDER Welt identisch sind.

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
    # -- woertlich aus build_room_produkt.py uebernommen --
    "rahmen":         (0.557, 0.592, 0.659, 1.0),  # globaler Metall-/Rahmenton, dort unveraendert
    "led_gruen":      (0.015, 0.699, 0.071, 1.0),  # Welt-5-eigenes, gesaettigtes Leuchten-Gruen
    "akzent_teal":    (0.001, 0.893, 0.531, 1.0),  # dort "karte_punkt_glut" -- derselbe Datenpunkt
    "kuehlung_hell":  (0.325, 0.349, 0.388, 1.0),  # dort "wand" -- helle Loft-Wandfarbe, hier Kuehlgehaeuse
    "kuehlung_dunkel":(0.018, 0.019, 0.020, 1.0),  # dort "schrank_front" -- fast schwarz, hier Kuehlgitter

    # -- projektweit / global identisch in jeder Welt (Begruendung in build_stations_zimmer.py) --
    "notiz":             (0.900, 0.870, 0.800, 1.0),  # Papier, hier: das Musterblatt
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # dunkles Geraetegehaeuse
    "bildschirm":        (0.066, 0.344, 0.680, 1.0),  # JEDER Bildschirm glueht so

    # -- frisch fuer Welt 5, nach linear = s^2,2 gerechnet (mit python -c geprueft) --
    "akzent_gold": (0.701, 0.389, 0.046, 1.0),  # #d9a63f -- special: wachsender Bestand (wie Welt 3)
}

AUSGABE = "project/assets/stations/produkt"


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


# --- Station 1: Leads ----------------------------------------------------------
# Welt 5: Leads kommen von allein, niemand tippt eine Anfrage. Waechst von
# einem Bildschirm mit Liste zu zwei Bildschirmen (einer zeigt eine Karte) zu
# einer Monitorwand mit aufleuchtenden Punkten -- von "eine Quelle" zu
# "ueberall gleichzeitig".

def intake_1():
    """Ein Bildschirm mit Liste auf einer schlichten Ablage -- die Liste
    fuellt sich von selbst, zwei Zeilen genuegen, um das zu zeigen."""
    teile = []
    teile.append(quader("ablage", (0.34, 0.24, 0.02), (0.0, 0.0, 0.62), "rahmen"))
    teile.append(quader("monitor_fuss", (0.10, 0.08, 0.02), (0.0, -0.02, 0.645), "bildschirm_rahmen"))
    teile.append(quader("monitor_rahmen", (0.28, 0.02, 0.20), (0.0, -0.06, 0.80), "bildschirm_rahmen"))
    teile.append(quader("monitor_schirm", (0.24, 0.006, 0.16), (0.0, -0.054, 0.80), "bildschirm"))
    teile.append(quader("liste_zeile_0", (0.18, 0.004, 0.014), (0.0, -0.057, 0.845), "akzent_teal"))
    teile.append(quader("liste_zeile_1", (0.18, 0.004, 0.014), (0.0, -0.057, 0.815), "notiz"))
    return teile


def intake_2():
    """Zwei Bildschirme auf einem Tisch -- einer zeigt weiter die Liste, der
    zweite eine Karte mit Punkten, die aufleuchten. Ersetzt die Ablage
    vollstaendig durch einen richtigen Arbeitsplatz."""
    teile = []
    teile.append(quader("tisch_platte", (0.86, 0.36, 0.03), (0.0, 0.0, 0.72), "rahmen"))
    for dx in (-0.36, 0.36):
        teile.append(quader("tisch_bein", (0.03, 0.30, 0.70), (dx, 0.0, 0.36), "bildschirm_rahmen"))
    for i, dx in enumerate((-0.20, 0.20)):
        teile.append(quader("monitor_fuss_%d" % i, (0.09, 0.07, 0.02), (dx, -0.08, 0.745), "bildschirm_rahmen"))
        teile.append(quader("monitor_rahmen_%d" % i, (0.24, 0.02, 0.17), (dx, -0.12, 0.895), "bildschirm_rahmen"))
        teile.append(quader("monitor_schirm_%d" % i, (0.20, 0.006, 0.13), (dx, -0.114, 0.895), "bildschirm"))
    teile.append(quader("liste_zeile", (0.14, 0.004, 0.012), (-0.20, -0.116, 0.925), "notiz"))
    teile.append(quader("karte_punkt_0", (0.02, 0.004, 0.02), (0.15, -0.116, 0.94), "akzent_teal"))
    teile.append(quader("karte_punkt_1", (0.02, 0.004, 0.02), (0.27, -0.116, 0.87), "akzent_teal"))
    return teile


def intake_3():
    """Eine Monitorwand -- neun Kacheln an einer Wandflaeche, vier davon
    leuchten gerade auf. Ersetzt die zwei Einzelbildschirme vollstaendig:
    aus einem Arbeitsplatz ist eine Anzeige geworden, an der niemand mehr
    sitzen muss."""
    teile = []
    teile.append(quader("wandpanel", (1.10, 0.04, 0.86), (0.0, -0.30, 1.05), "bildschirm_rahmen"))
    reihen = (0.76, 1.05, 1.34)
    spalten = (-0.34, 0.0, 0.34)
    leucht_index = {0, 2, 5, 7}
    idx = 0
    for r, hz in enumerate(reihen):
        for s, dx in enumerate(spalten):
            farbe = "akzent_teal" if idx in leucht_index else "bildschirm"
            teile.append(quader("kachel_%d" % idx, (0.30, 0.006, 0.24), (dx, -0.278, hz), farbe))
            idx += 1
    teile.append(quader("tisch_platte", (0.80, 0.34, 0.03), (0.0, 0.0, 0.585), "rahmen"))
    for dx in (-0.32, 0.32):
        teile.append(quader("tisch_bein", (0.03, 0.28, 0.57), (dx, 0.0, 0.285), "bildschirm_rahmen"))
    teile.append(quader("tastatur", (0.22, 0.09, 0.012), (0.0, 0.08, 0.601), "kuehlung_dunkel"))
    return teile


# --- Station 2: Vorlage ---------------------------------------------------------
# Welt 5: aus einer einzelnen Loesung wird eine wiederverwendbare Vorlage.
# Waechst vom Musterblatt zum Regal mit Varianten zum Baukasten aus
# austauschbaren Bloecken -- von "eine Antwort" zu "ein Baukasten fuer alle
# Antworten".

def buffer_1():
    """Ein Musterblatt auf einem Staender -- die eine Vorlage, aus der
    spaeter alles andere abgeleitet wird."""
    teile = []
    teile.append(quader("staender_fuss", (0.20, 0.14, 0.02), (0.0, 0.0, 0.02), "rahmen"))
    teile.append(quader("staender_pfosten", (0.02, 0.02, 0.40), (0.0, 0.0, 0.21), "bildschirm_rahmen"))
    teile.append(quader("blatt", (0.28, 0.012, 0.36), (0.0, 0.0, 0.55), "notiz"))
    teile.append(quader("blatt_linie_0", (0.20, 0.006, 0.012), (0.0, -0.008, 0.62), "akzent_gold"))
    teile.append(quader("blatt_linie_1", (0.20, 0.006, 0.012), (0.0, -0.008, 0.58), "bildschirm_rahmen"))
    return teile


def buffer_2():
    """Ein Regal mit mehreren Varianten -- aus der einen Vorlage ist eine
    Sammlung geworden. Ersetzt den Staender vollstaendig durch ein Regal,
    das mehrere fertige Varianten zugleich zeigt."""
    teile = []
    for x in (-0.28, 0.28):
        teile.append(quader("seite_%s" % ("l" if x < 0 else "r"), (0.03, 0.24, 0.80), (x, 0.0, 0.40), "rahmen"))
    for i, z in enumerate((0.02, 0.28, 0.54)):
        teile.append(quader("boden_%d" % i, (0.56, 0.24, 0.02), (0.0, 0.0, z), "rahmen"))
    varianten = [(-0.16, 0.16, "notiz"), (0.0, 0.16, "akzent_gold"), (0.16, 0.16, "notiz"),
                 (-0.10, 0.42, "akzent_teal"), (0.10, 0.42, "notiz")]
    for i, (dx, dz, farbe) in enumerate(varianten):
        teile.append(quader("variante_%d" % i, (0.11, 0.20, 0.22), (dx, 0.0, dz), farbe))
    return teile


def buffer_3():
    """Ein Baukasten aus austauschbaren Bloecken auf einem Tisch -- ersetzt
    das Regal vollstaendig: keine fertigen Varianten mehr, sondern
    Bausteine, aus denen sich jede Variante neu zusammensetzt. Drei
    Bausteinfarben genuegen, mehr wuerde nur unruhig wirken."""
    teile = []
    teile.append(quader("tisch_platte", (0.90, 0.42, 0.03), (0.0, 0.0, 0.585), "rahmen"))
    for dx in (-0.38, 0.38):
        teile.append(quader("tisch_bein", (0.03, 0.36, 0.57), (dx, 0.0, 0.285), "bildschirm_rahmen"))
    block_farben = ["akzent_gold", "akzent_teal", "notiz"]
    idx = 0
    for gx in range(3):
        for gy in range(3):
            farbe = block_farben[(gx + gy) % 3]
            dx = -0.20 + gx * 0.20
            dy = -0.06 + gy * 0.06
            teile.append(quader("block_%d" % idx, (0.16, 0.05, 0.12), (dx, dy, 0.665), farbe))
            idx += 1
    teile.append(quader("block_lose_0", (0.16, 0.05, 0.12), (0.34, 0.10, 0.665), "akzent_gold"))
    teile.append(quader("block_lose_1", (0.16, 0.05, 0.12), (0.34, -0.10, 0.665), "akzent_teal"))
    return teile


# --- Station 3: Ausspielung ------------------------------------------------------
# Welt 5: dieselbe Loesung, hundertfach ausgespielt. Waechst vom einzelnen
# Server zu drei Servern nebeneinander zu einer ganzen Reihe, alle mit
# derselben Leuchte im selben Takt -- Gleichklang statt Einzelstueck.

def _server(name, position):
    x, y, z = position
    teile = []
    teile.append(quader("%s_gehaeuse" % name, (0.28, 0.20, 0.10), (x, y, z), "bildschirm_rahmen"))
    teile.append(quader("%s_led" % name, (0.02, 0.01, 0.01), (x + 0.11, y - 0.09, z), "led_gruen"))
    return teile


def processing_1():
    """Ein Server auf einem kleinen Regalbrett -- der Anfang der
    Ausspielung, noch ein Einzelstueck."""
    teile = []
    for dx in (-0.16, 0.16):
        teile.append(quader("traeger", (0.03, 0.20, 0.40), (dx, 0.0, 0.20), "rahmen"))
    teile.append(quader("brett", (0.40, 0.22, 0.025), (0.0, 0.0, 0.405), "rahmen"))
    teile += _server("server", (0.0, 0.0, 0.465))
    return teile


def processing_2():
    """Drei Server nebeneinander in einem kleinen Rack -- ersetzt das
    Regalbrett vollstaendig durch einen eigenen Schrank fuer drei Geraete
    gleichzeitig."""
    teile = []
    for dx in (-0.20, 0.20):
        teile.append(quader("rack_seite", (0.03, 0.26, 0.50), (dx, 0.0, 0.25), "rahmen"))
    teile.append(quader("rack_deckel", (0.43, 0.26, 0.03), (0.0, 0.0, 0.515), "bildschirm_rahmen"))
    teile.append(quader("rack_boden", (0.43, 0.26, 0.03), (0.0, 0.0, 0.015), "bildschirm_rahmen"))
    for i, hz in enumerate((0.12, 0.25, 0.38)):
        teile += _server("server_%d" % i, (0.0, 0.0, hz))
    return teile


def processing_3():
    """Eine ganze Reihe Server -- sechs Geraete in einem hohen Rack, alle
    mit derselben Leuchte auf derselben Hoehe: nicht einzeln geschaltet,
    sondern im Takt. Das ist der Hebel dieser Welt in einem Bild."""
    teile = []
    for dx in (-0.22, 0.22):
        teile.append(quader("rack_seite", (0.03, 0.28, 0.98), (dx, 0.0, 0.49), "rahmen"))
    teile.append(quader("rack_deckel", (0.47, 0.28, 0.03), (0.0, 0.0, 0.995), "bildschirm_rahmen"))
    teile.append(quader("rack_boden", (0.47, 0.28, 0.03), (0.0, 0.0, 0.015), "bildschirm_rahmen"))
    hoehen = (0.11, 0.24, 0.37, 0.50, 0.63, 0.76)
    for i, hz in enumerate(hoehen):
        teile += _server("server_%d" % i, (0.0, 0.0, hz))
    return teile


# --- Station 4: Infrastruktur -----------------------------------------------------
# Welt 5: das, was die Ausspielung traegt. Waechst vom einzelnen
# Netzwerkschrank zu Schrank plus Kuehlung zu zwei Schraenken mit
# Kabeltrasse und Notstrom -- von "ein Geraet" zu "eine Anlage, die nicht
# ausfallen darf".

def _schrank(name, position):
    x, y, z = position
    teile = []
    teile.append(quader("%s_korpus" % name, (0.34, 0.28, 0.90), (x, y, z + 0.45), "bildschirm_rahmen"))
    teile.append(quader("%s_tuer" % name, (0.30, 0.02, 0.84), (x, y - 0.15, z + 0.45), "rahmen"))
    for i, hz in enumerate((0.20, 0.45, 0.70)):
        teile.append(quader("%s_lueftung_%d" % (name, i), (0.22, 0.006, 0.03), (x, y - 0.161, z + hz), "kuehlung_dunkel"))
    return teile


def transport_1():
    """Ein Netzwerkschrank -- ein Geraet, das die Kette am Laufen haelt."""
    return _schrank("schrank", (0.0, 0.0, 0.0))


def transport_2():
    """Schrank plus eigene Kuehlung daneben -- ersetzt nichts, ergaenzt:
    ein Geraet allein reicht nicht mehr, es braucht eine eigene Kuehlung."""
    teile = []
    teile += _schrank("schrank", (-0.20, 0.0, 0.0))
    teile.append(quader("kuehlung_korpus", (0.26, 0.24, 0.50), (0.32, 0.0, 0.25), "kuehlung_hell"))
    for i, hz in enumerate((0.14, 0.30)):
        teile.append(quader("kuehlung_gitter_%d" % i, (0.18, 0.006, 0.05), (0.32, -0.121, hz), "kuehlung_dunkel"))
    teile.append(quader("kabelkanal", (0.66, 0.05, 0.03), (0.06, 0.14, 0.015), "rahmen"))
    return teile


def transport_3():
    """Zwei Schraenke, eine Kabeltrasse an der Decke und ein
    Notstromgeraet -- ersetzt die einzelne Kuehlung durch eine ganze
    Anlage: zwei Schraenke statt einem, eine geordnete Trasse statt loser
    Kabel, und ein Akku fuer den Fall, dass der Strom ausfaellt."""
    teile = []
    teile += _schrank("schrank_a", (-0.40, 0.0, 0.0))
    teile += _schrank("schrank_b", (0.02, 0.0, 0.0))
    teile.append(quader("kabeltrasse", (0.90, 0.10, 0.03), (-0.18, -0.16, 0.98), "rahmen"))
    for i, dx in enumerate((-0.50, -0.10, 0.30)):
        teile.append(quader("kabelbuendel_%d" % i, (0.02, 0.02, 0.13), (dx, -0.16, 0.915), "bildschirm_rahmen"))
    teile.append(quader("notstrom_gehaeuse", (0.28, 0.26, 0.42), (0.42, 0.0, 0.21), "kuehlung_hell"))
    for i, dx in enumerate((-0.07, 0.07)):
        teile.append(quader("notstrom_akku_%d" % i, (0.10, 0.02, 0.10), (0.42 + dx, -0.13, 0.30), "kuehlung_dunkel"))
    return teile


# --- Station 5: Abo ---------------------------------------------------------------
# Welt 5: der Bestand, der Erlös bringt, solange er gehalten wird. Waechst
# vom einzelnen Zaehler zum Bildschirm mit steigender Kurve zur grossen
# Kennzahlwand -- von "eine Zahl" zu "ein Ueberblick".

def special_1():
    """Ein einzelner Zaehler auf einem schlanken Staender -- die
    einfachste Form, den Bestand sichtbar zu machen."""
    teile = []
    teile.append(quader("staender_fuss", (0.16, 0.12, 0.02), (0.0, 0.0, 0.02), "rahmen"))
    teile.append(quader("staender_saeule", (0.03, 0.03, 0.50), (0.0, 0.0, 0.27), "bildschirm_rahmen"))
    teile.append(quader("zaehler_gehaeuse", (0.22, 0.10, 0.14), (0.0, 0.0, 0.585), "bildschirm_rahmen"))
    teile.append(quader("zaehler_schirm", (0.17, 0.006, 0.09), (0.0, -0.045, 0.585), "bildschirm"))
    teile.append(quader("ziffer_0", (0.04, 0.004, 0.05), (-0.03, -0.048, 0.585), "akzent_gold"))
    teile.append(quader("ziffer_1", (0.04, 0.004, 0.05), (0.03, -0.048, 0.585), "akzent_gold"))
    return teile


def special_2():
    """Ein Bildschirm mit steigender Kurve -- ersetzt den Zaehler
    vollstaendig: nicht mehr eine Zahl, sondern eine Richtung."""
    teile = []
    teile.append(quader("monitor_fuss", (0.12, 0.09, 0.02), (0.0, -0.05, 0.62), "bildschirm_rahmen"))
    teile.append(quader("monitor_hals", (0.02, 0.02, 0.14), (0.0, -0.05, 0.695), "rahmen"))
    teile.append(quader("monitor_rahmen", (0.34, 0.02, 0.24), (0.0, -0.09, 0.895), "bildschirm_rahmen"))
    teile.append(quader("monitor_schirm", (0.30, 0.006, 0.20), (0.0, -0.084, 0.895), "bildschirm"))
    kurve = [(-0.10, 0.815, 0.02), (-0.02, 0.845, 0.03), (0.06, 0.885, 0.04), (0.13, 0.935, 0.05)]
    for i, (dx, dz, hoehe) in enumerate(kurve):
        teile.append(quader("kurve_%d" % i, (0.04, 0.004, hoehe), (dx, -0.086, dz), "akzent_gold"))
    return teile


def special_3():
    """Eine grosse Kennzahlwand -- ersetzt den Einzelbildschirm
    vollstaendig durch eine Wand aus mehreren Feldern und Balken: der
    Bestand ist zu gross geworden fuer einen einzigen Blick."""
    teile = []
    teile.append(quader("wandpanel", (1.10, 0.04, 0.70), (0.0, -0.30, 1.10), "bildschirm_rahmen"))
    felder = [(-0.34, 1.30), (0.0, 1.30), (0.34, 1.30), (-0.34, 1.00), (0.0, 1.00), (0.34, 1.00)]
    for i, (dx, dz) in enumerate(felder):
        teile.append(quader("kennzahl_feld_%d" % i, (0.28, 0.01, 0.20), (dx, -0.278, dz), "bildschirm"))
    balken = [(-0.34, 0.03, 0.855), (0.0, 0.05, 0.865), (0.34, 0.07, 0.875), (0.17, 0.04, 0.86), (-0.17, 0.06, 0.87)]
    for i, (dx, hoehe, dz) in enumerate(balken):
        teile.append(quader("balken_%d" % i, (0.05, 0.004, hoehe), (dx, -0.278, dz), "akzent_gold"))
    teile.append(quader("tisch_platte", (0.70, 0.32, 0.03), (0.0, 0.0, 0.585), "rahmen"))
    for dx in (-0.28, 0.28):
        teile.append(quader("tisch_bein", (0.03, 0.26, 0.57), (dx, 0.0, 0.285), "bildschirm_rahmen"))
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
    print("=== STATIONSMODULE WELT 5 -- PRODUKT ===")
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
