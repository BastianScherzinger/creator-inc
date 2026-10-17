"""Erzeugt die Stationsmodule fuer Welt 4 "buero" als glTF-Dateien.

Aufruf:
    blender --background --python art_source/scripts/build_stations_buero.py

Fuenf Stationen, je drei Ausbaustufen -- 15 Dateien. Aufbau und Kommentarstil
folgen bewusst art_source/scripts/build_stations_webseiten.py, der
Strukturvorlage dieser Aufgabe: manche Stufen bauen woertlich auf der vorigen
auf (teile = vorherige() + neu), andere ersetzen das schlichtere
Vorgaenger-Teil durch ein reicheres Aequivalent. Hauptsache, jede Stufe ist
unzweifelhaft mehr/besser als die vorige.

Benennung nach FUNKTION, nicht nach Gegenstand (ADR-010):
    station_intake_1..3 / station_buffer_1..3 / station_processing_1..3 /
    station_transport_1..3 / station_special_1..3
Dieselbe ID ist in den Webseiten ein Telefon auf einem Empfangstresen, hier
ein Telefon mit einer Liste auf einer Ablage. Die Zuordnung steht in
data/themes/buero/theme.json.

Was die fuenf Stufen in DIESER Welt zeigen (docs/WELTEN.md, "Welt 4 --
buero"; Auftrag Punkt 3):
    intake      Akquise      Telefon+Liste -> Tisch+Bildschirm+Pinnwand -> zwei Arbeitsplaetze+Wandtafel mit Leads
    buffer      Planung      Kalender an der Wand -> Planungstafel mit Karten in Spalten -> grosse Tafel mit Zeitleiste+Stehtisch
    processing  Team         EIN Schreibtisch+Stuhl -> zwei Schreibtische+Trennwand -> vier Schreibtische im Block+Kabelfuehrung
    transport   Werkzeuge    kleiner Server -> Rack mit Statusleuchten -> Rack+Wandbildschirm mit gruenen Haekchen
    special     Grosskunde   ein dicker Ordner -> Besprechungstisch+2 Stuehle -> Besprechungstisch+6 Stuehle+Praesentationsbildschirm

DIE AUSSAGE DIESER WELT IN GEOMETRIE (Auftrag Punkt 3): Stufe fuer Stufe
kommen bei "processing" ARBEITSPLAETZE dazu, nicht Geraete -- ein zweiter
Schreibtisch, eine Trennwand, ein dritter Platz, ein vierter Schreibtisch mit
gemeinsamer Kabelfuehrung. Deshalb bekommt processing bewusst KEINE Monitore:
in jeder anderen Welt wird die "processing"-Station technisch aufgeruestet,
hier wird sie stattdessen besetzt. Das ist der Unterschied zu Welt 3, wo
"Umsetzung" von einem Laptop zu zwei Arbeitsplaetzen mit drei Monitoren
waechst -- hier waechst dieselbe Stufenfolge ohne ein einziges zusaetzliches
Geraet.

Der Massstab folgt dem Rastermass aus ART_DIRECTION 7: 1 Einheit = 1 Meter.
Harte Groessenregel dieser Aufgabe: jedes Modul passt in 1,8 x 1,8
Grundflaeche, hoechstens 1,6 hoch, Ursprung in der Mitte der Grundflaeche auf
z = 0.
"""

import bpy
import os
import math

# ACHTUNG Farbraum -- glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. linear = s^2,2. Die meisten Toene unten sind
# woertlich aus build_room_buero.py und build_world_buero.py uebernommen,
# damit diese Stationen im selben Raum stehen und wie dieselben Moebel
# wirken wie das Buero drumherum (dieselbe Begruendung wie in
# build_stations_webseiten.py: "Uebernimm die Palette, damit die Stationen
# im selben Raum stehen koennen, ohne herauszufallen"). Zwei Toene sind
# global und in jeder Welt identisch (siehe build_stations_zimmer.py, dort
# schon so begruendet); zwei sind frisch fuer diese Welt nach derselben
# Formel gerechnet und mit einem kurzen Python-Aufruf nachgerechnet, nicht
# nur von Hand geschaetzt.
PALETTE = {
    # -- woertlich uebernommen aus build_room_buero.py --
    "rahmen":            (0.557, 0.592, 0.659, 1.0),  # globaler Metall-/Rahmenton
    "pinnwand_flaeche":  (0.349, 0.181, 0.082, 1.0),  # Kork, wie raum_pinnwand
    "notiz":             (0.900, 0.870, 0.800, 1.0),  # Zettel-Ton 1
    "notiz_b":           (0.612, 0.646, 0.681, 1.0),  # Zettel-Ton 2, kuehles Recyclingpapier

    # -- woertlich uebernommen aus build_world_buero.py (derselbe Beruf, dieselben Moebel) --
    "holz_schreibtisch": (0.325, 0.234, 0.163, 1.0),  # helles Buero-Holz, IKEA-hell
    "bildschirm_rahmen": (0.022, 0.022, 0.024, 1.0),  # dunkles Geraetegehaeuse: Telefon, Monitor, Rack
    "tastatur":          (0.218, 0.218, 0.214, 1.0),  # heller Kunststoff
    "stuhl_polster":     (0.056, 0.052, 0.062, 1.0),  # Buerostuhl-Polster, dunkel neutral

    # -- global identisch in jeder Welt (Begruendung in build_stations_zimmer.py) --
    "bildschirm": (0.066, 0.344, 0.680, 1.0),   # JEDER Bildschirm glueht so
    "led_gruen":  (0.104, 0.530, 0.198, 1.0),   # Betriebs-/Statusleuchte, auch das gruene Haekchen

    # -- frisch fuer Welt 4, nach linear = s^2,2 gerechnet und mit Python nachgerechnet --
    "akzent_rot":  (0.592, 0.025, 0.021, 1.0),  # #c9302c -- intake: neuer, dringender Lead
    "akzent_gold": (0.701, 0.330, 0.020, 1.0),  # #d99a2b -- special: der Grosskunde, wichtiger Termin
}

AUSGABE = "project/assets/stations/buero"


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
    einem runden Zylinder zu unterscheiden, aber deutlich billiger. ACHTUNG
    beim Budgetieren (siehe build_stations_zimmer.py): ein Zylinder mit acht
    Seiten hat real 4*8-4 = 28 Dreiecke, nicht die 20, die die einfache
    "Polygone * 2"-Formel der print-Ausgabe unten anzeigt -- deshalb wird
    hier bewusst sparsam mit Zylindern budgetiert."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=seiten, radius=radius,
                                        depth=hoehe, location=position)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material(mat_name))
    return obj


# --- Station 1: Akquise --------------------------------------------------------
# Welt 4: das erste Kettenglied bleibt der Kontakt nach aussen, jetzt fuer
# mehrere Projekte gleichzeitig. Waechst vom Telefon mit einer Liste zum
# Schreibtisch mit Bildschirm und Pinnwand zu zwei Arbeitsplaetzen mit
# Wandtafel -- von "eine Person nimmt Anfragen an" zu "ein kleines Team
# sortiert sie".

def _telefon(position):
    """Ein Telefon -- Koerper plus leuchtende Vorderseite, wie in
    build_stations_webseiten.py: aufrecht auf einer Flaeche, nie auf dem
    Boden."""
    x, y, z = position
    teile = []
    teile.append(quader("telefon_koerper", (0.09, 0.02, 0.16), (x, y, z), "bildschirm_rahmen"))
    teile.append(quader("telefon_schirm", (0.075, 0.006, 0.14), (x, y - 0.011, z), "bildschirm"))
    return teile


def intake_1():
    """Ein Telefon mit einer Liste auf der Ablage -- zwei uebereinandergelegte
    Blaetter statt eines einzelnen Zettels: hier laufen bereits mehrere
    Anfragen auf, nicht nur eine. Der rote Strich markiert die dringende
    Zeile."""
    teile = []
    teile.append(quader("ablage", (0.36, 0.26, 0.02), (0.0, 0.0, 0.30), "holz_schreibtisch"))
    teile.append(quader("liste_a", (0.17, 0.13, 0.006), (-0.10, 0.03, 0.314), "notiz", -6.0))
    teile.append(quader("liste_b", (0.16, 0.12, 0.006), (-0.11, 0.03, 0.321), "notiz_b", 3.0))
    teile += _telefon((0.11, -0.02, 0.395))
    teile.append(quader("liste_marker", (0.10, 0.006, 0.008), (-0.10, 0.01, 0.328), "akzent_rot", -6.0))
    return teile


def intake_2():
    """Ein Schreibtisch mit Bildschirm und Pinnwand -- aus der Liste auf der
    Ablage ist ein echter Arbeitsplatz geworden: ein Bildschirm fuer den
    Ueberblick, eine Pinnwand fuer alles, was noch offen ist."""
    teile = []
    teile.append(quader("tisch_platte", (0.62, 0.40, 0.03), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    for dx in (-0.26, 0.26):
        teile.append(quader("tisch_bein", (0.03, 0.34, 0.70), (dx, 0.0, 0.36), "rahmen"))
    teile.append(quader("monitor_fuss", (0.10, 0.08, 0.02), (0.0, -0.10, 0.745), "bildschirm_rahmen"))
    teile.append(quader("monitor_rahmen", (0.26, 0.02, 0.18), (0.0, -0.14, 0.905), "bildschirm_rahmen"))
    teile.append(quader("monitor_schirm", (0.22, 0.006, 0.14), (0.0, -0.134, 0.905), "bildschirm"))
    teile.append(quader("pinnwand_flaeche", (0.34, 0.03, 0.26), (0.42, 0.0, 0.98), "pinnwand_flaeche"))
    teile.append(quader("pinnwand_rahmen_o", (0.36, 0.04, 0.02), (0.42, 0.0, 1.115), "rahmen"))
    teile.append(quader("pinnwand_rahmen_u", (0.36, 0.04, 0.02), (0.42, 0.0, 0.845), "rahmen"))
    teile.append(quader("notiz_a", (0.08, 0.01, 0.07), (0.36, -0.02, 1.02), "notiz", -8.0))
    teile.append(quader("notiz_b", (0.08, 0.01, 0.07), (0.48, -0.02, 0.94), "notiz_b", 6.0))
    return teile


def intake_3():
    """Zwei Arbeitsplaetze an einem gemeinsamen Tisch, dazwischen ein
    Trenner, dahinter eine Wandtafel mit Leads -- ersetzt den einzelnen
    Bildschirm vollstaendig durch ein kleines Team, das gemeinsam an der
    Akquise sitzt. Die Zeilen auf der Tafel sind Leads, zwei davon rot
    markiert -- neu und noch nicht bearbeitet."""
    teile = []
    teile.append(quader("tisch_platte", (1.30, 0.42, 0.03), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    for dx in (-0.58, 0.58):
        teile.append(quader("tisch_bein", (0.03, 0.36, 0.70), (dx, 0.0, 0.36), "rahmen"))
    teile.append(quader("trenner", (0.02, 0.28, 0.26), (0.0, -0.05, 0.87), "rahmen"))
    for i, dx in enumerate((-0.34, 0.34)):
        teile.append(quader("monitor_stand_%d" % i, (0.20, 0.02, 0.16), (dx, -0.12, 0.885), "bildschirm_rahmen"))
        teile.append(quader("monitor_schirm_%d" % i, (0.16, 0.006, 0.12), (dx, -0.114, 0.885), "bildschirm"))
        teile.append(quader("tastatur_%d" % i, (0.20, 0.09, 0.012), (dx, 0.10, 0.741), "tastatur"))
    teile.append(quader("wandtafel_flaeche", (0.90, 0.04, 0.50), (0.0, -0.42, 1.30), "pinnwand_flaeche"))
    teile.append(quader("wandtafel_rahmen_o", (0.94, 0.05, 0.03), (0.0, -0.42, 1.555), "rahmen"))
    teile.append(quader("wandtafel_rahmen_u", (0.94, 0.05, 0.03), (0.0, -0.42, 1.045), "rahmen"))
    teile.append(quader("wandtafel_rahmen_l", (0.03, 0.05, 0.52), (-0.465, -0.42, 1.30), "rahmen"))
    teile.append(quader("wandtafel_rahmen_r", (0.03, 0.05, 0.52), (0.465, -0.42, 1.30), "rahmen"))
    zeilen = [(1.42, "akzent_rot"), (1.34, "notiz"), (1.26, "akzent_rot")]
    for i, (dz, farbe) in enumerate(zeilen):
        teile.append(quader("lead_%d" % i, (0.70, 0.01, 0.05), (0.0, -0.40, dz), farbe))
    return teile


# --- Station 2: Planung ---------------------------------------------------------
# Welt 4: aus dem eigenen Notizzettel wird ein Plan, den mehrere Personen
# lesen koennen. Waechst vom Kalender an der Wand zur Planungstafel mit
# Karten in Spalten zur grossen Tafel mit Zeitleiste plus Stehtisch -- von
# "ein Termin" zu "ein Ablauf, an dem das ganze Buero steht".

def buffer_1():
    """Ein Kalender an der Wand -- eine Halterung, ein Block, ein goldener
    Strich fuer den heutigen Termin. Mehr braucht ein einzelner Planer am
    ersten Tag nicht."""
    teile = []
    teile.append(quader("halterung", (0.22, 0.03, 0.16), (0.0, 0.0, 0.90), "rahmen"))
    teile.append(quader("kalender_block", (0.20, 0.02, 0.14), (0.0, -0.02, 0.90), "notiz"))
    teile.append(quader("kalender_markierung", (0.14, 0.006, 0.02), (0.0, -0.035, 0.94), "akzent_gold"))
    teile.append(quader("kalender_ring", (0.20, 0.02, 0.012), (0.0, -0.025, 0.975), "rahmen"))
    return teile


def buffer_2():
    """Eine Planungstafel mit Karten in drei Spalten -- ersetzt den
    Kalender vollstaendig durch ein Board, an dem mehrere Projekte
    gleichzeitig ihren Stand zeigen. Zwei senkrechte Linien trennen die
    Spalten, die goldene Karte markiert das Projekt, das gerade beim
    Grosskunden liegt."""
    teile = []
    teile.append(quader("tafel_fuss", (0.70, 0.32, 0.05), (0.0, 0.0, 0.03), "holz_schreibtisch"))
    for dx in (-0.30, 0.30):
        teile.append(quader("tafel_bein", (0.05, 0.05, 0.90), (dx, 0.0, 0.48), "rahmen"))
    teile.append(quader("tafel_flaeche", (0.86, 0.05, 0.62), (0.0, 0.0, 0.98), "notiz"))
    for dx in (-0.14, 0.14):
        teile.append(quader("spalten_linie", (0.01, 0.06, 0.60), (dx, -0.03, 0.98), "rahmen"))
    karten = [(-0.30, 1.14, "notiz"), (-0.28, 0.92, "notiz_b"),
              (0.0, 1.10, "notiz"), (0.02, 0.86, "akzent_gold"),
              (0.30, 1.16, "notiz_b")]
    for i, (dx, dz, farbe) in enumerate(karten):
        teile.append(quader("karte_%d" % i, (0.10, 0.012, 0.08), (dx, -0.035, dz), farbe))
    return teile


def buffer_3():
    """Eine grosse Tafel mit Zeitleiste, davor ein Stehtisch -- ersetzt die
    Planungstafel vollstaendig: aus einzelnen Karten ist ein Ablauf mit
    Meilensteinen geworden. Drei goldene Marker sitzen auf der Linie, einer
    davon ist der naechste Termin."""
    teile = []
    teile.append(quader("board_flaeche", (1.10, 0.05, 0.64), (0.0, -0.30, 1.12), "notiz"))
    for dz, name in ((1.46, "board_rahmen_o"), (0.80, "board_rahmen_u")):
        teile.append(quader(name, (1.14, 0.07, 0.04), (0.0, -0.30, dz), "rahmen"))
    for dx, name in ((-0.57, "board_rahmen_l"), (0.57, "board_rahmen_r")):
        teile.append(quader(name, (0.04, 0.07, 0.70), (dx, -0.30, 1.13), "rahmen"))
    teile.append(quader("zeitleiste_linie", (0.94, 0.01, 0.02), (0.0, -0.275, 1.13), "bildschirm_rahmen"))
    marker = [(-0.32, "akzent_gold"), (0.02, "notiz_b"), (0.34, "akzent_gold")]
    for i, (dx, farbe) in enumerate(marker):
        teile.append(quader("meilenstein_%d" % i, (0.05, 0.01, 0.10), (dx, -0.272, 1.13), farbe))
    teile.append(quader("stehtisch_platte", (0.42, 0.42, 0.03), (0.0, 0.30, 1.02), "holz_schreibtisch"))
    teile.append(zylinder("stehtisch_saeule", 0.035, 0.96, (0.0, 0.30, 0.535), "rahmen"))
    teile.append(quader("stehtisch_fuss", (0.30, 0.30, 0.03), (0.0, 0.30, 0.045), "rahmen"))
    return teile


# --- Station 3: Team -------------------------------------------------------------
# Welt 4, die eigentliche Aussage der Welt (Auftrag Punkt 3): hier waechst
# NICHT die Ausruestung, sondern die Zahl der besetzten Plaetze. EIN
# Schreibtisch mit Stuhl -> zwei Schreibtische mit Trennwand -> vier
# Schreibtische im Block mit gemeinsamer Kabelfuehrung. Kein Modul dieser
# Stufenfolge bekommt einen Monitor -- absichtlich, siehe Modulkopf.

def _stuhl_einfach(position, drehung_z=0.0):
    """Ein schlichter Buerostuhl -- Sitz, Lehne, ein einzelner Quader als
    Saeule-plus-Fuss (spart Dreiecke gegenueber vier Einzelteilen, ohne die
    Silhouette zu verlieren). Wird von processing_1 und processing_2
    gebraucht, deshalb als eigene Funktion; processing_3 braucht wegen der
    vierfachen Bestuhlung eine noch knappere Variante (siehe dort)."""
    x, y = position
    teile = []
    teile.append(quader("stuhl_sitz", (0.36, 0.34, 0.05), (x, y, 0.46), "stuhl_polster", drehung_z))
    teile.append(quader("stuhl_lehne", (0.34, 0.05, 0.34), (x, y + 0.145, 0.66), "stuhl_polster", drehung_z))
    teile.append(quader("stuhl_bein", (0.30, 0.30, 0.42), (x, y, 0.21), "rahmen", drehung_z))
    return teile


def processing_1():
    """EIN Schreibtisch mit Stuhl -- der erste besetzte Platz dieser Welt.
    Kein Bildschirm, kein Geraet: nur die Flaeche, an der jemand sitzt."""
    teile = []
    teile.append(quader("tisch_platte", (0.70, 0.40, 0.03), (0.0, 0.0, 0.72), "holz_schreibtisch"))
    for dx in (-0.30, 0.30):
        teile.append(quader("tisch_bein", (0.03, 0.34, 0.70), (dx, 0.0, 0.36), "rahmen"))
    teile += _stuhl_einfach((0.0, 0.34))
    return teile


def processing_2():
    """Zwei Schreibtische, eine Trennwand dazwischen -- ersetzt den
    einzelnen Platz vollstaendig durch zwei nebeneinander, ohne dass ein
    einziges Geraet dazukommt. Die Trennwand ist neu: der erste Hinweis,
    dass hier mehr als eine Person sitzt. Je Tisch genuegt ein zentrales
    Bein (Budget), das reicht bei dieser Kameradistanz voellig aus."""
    teile = []
    for i, dx in enumerate((-0.44, 0.44)):
        teile.append(quader("tisch_platte_%d" % i, (0.62, 0.40, 0.03), (dx, 0.0, 0.72), "holz_schreibtisch"))
        teile.append(quader("tisch_bein_%d" % i, (0.10, 0.10, 0.70), (dx, 0.0, 0.36), "rahmen"))
    teile.append(quader("trenner", (0.03, 0.26, 0.34), (0.0, 0.0, 0.90), "rahmen"))
    teile += _stuhl_einfach((-0.44, 0.34))
    teile += _stuhl_einfach((0.44, 0.34))
    return teile


def _stuhl_block(position, drehung_z=0.0):
    """Stuhl auf die Silhouette verkuerzt -- ein einzelner Quader (R1),
    genau wie bei special_3. Wird bei vier Stuehlen auf einmal gebraucht:
    processing_3 muesste sonst allein fuer die Bestuhlung ein Vielfaches des
    Dreiecksbudgets aufbrauchen."""
    x, y = position
    return [quader("stuhl", (0.34, 0.34, 0.46), (x, y, 0.23), "stuhl_polster", drehung_z)]


def processing_3():
    """Vier Schreibtische im Block, gemeinsame Kabelfuehrung -- ersetzt die
    zwei getrennten Plaetze durch einen 2x2-Block: vier Tischplatten stossen
    in der Mitte aneinander, darunter laeuft ein einzelner Kabelkanal statt
    vier einzelner Kabel. Das ist der Punkt der ganzen Stufenfolge: vier
    besetzte Plaetze, kein einziges zusaetzliches Geraet."""
    teile = []
    positionen = [(-0.42, -0.32), (0.42, -0.32), (-0.42, 0.32), (0.42, 0.32)]
    for i, (dx, dy) in enumerate(positionen):
        teile.append(quader("tisch_platte_%d" % i, (0.60, 0.44, 0.03), (dx, dy, 0.72), "holz_schreibtisch"))
        teile.append(quader("tisch_bein_%d" % i, (0.10, 0.10, 0.70), (dx, dy, 0.36), "rahmen"))
    teile.append(quader("kabelkanal_x", (1.44, 0.06, 0.03), (0.0, 0.0, 0.44), "bildschirm_rahmen"))
    teile.append(quader("kabelkanal_y", (0.06, 1.04, 0.03), (0.0, 0.0, 0.44), "bildschirm_rahmen"))
    for i, (dx, dy) in enumerate(positionen):
        vorzeichen = 1.0 if dy < 0 else -1.0
        teile += _stuhl_block((dx, dy + vorzeichen * 0.34))
    return teile


# --- Station 4: Werkzeuge ---------------------------------------------------------
# Welt 4: die Automatisierung, die Menschen Arbeit abnimmt statt sie
# schneller zu machen (docs/STORY.md: "Nicht schneller arbeiten. Weniger
# arbeiten muessen."). Waechst vom kleinen Server zum Rack mit
# Statusleuchten zum Rack mit Wandbildschirm, der sich selbst prueft.

def transport_1():
    """Ein kleiner Server -- ein Brett, zwei Traeger, ein Geraet mit
    Betriebsleuchte. Genau wie in Welt 3, aber das ist hier erst der
    Anfang: die Werkzeuge dieser Welt wachsen zu mehr als einem Geraet."""
    teile = []
    for dx in (-0.16, 0.16):
        teile.append(quader("traeger", (0.03, 0.20, 0.42), (dx, 0.0, 0.21), "rahmen"))
    teile.append(quader("brett", (0.40, 0.22, 0.025), (0.0, 0.0, 0.425), "holz_schreibtisch"))
    teile.append(quader("server_gehaeuse", (0.30, 0.18, 0.08), (0.0, 0.0, 0.478), "bildschirm_rahmen"))
    teile.append(quader("server_led", (0.02, 0.01, 0.01), (0.12, -0.08, 0.478), "led_gruen"))
    teile.append(quader("kabel", (0.01, 0.01, 0.42), (0.16, 0.09, 0.21), "bildschirm_rahmen"))
    return teile


def transport_2():
    """Ein Rack mit drei Einschueben und Statusleuchten -- ersetzt den
    Einzelserver vollstaendig durch einen eigenen kleinen Schrank. Zwei
    gruene Leuchten zeigen laufende Automatisierungen."""
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
    """Ein Rack plus Wandbildschirm mit gruenen Haekchen -- der Bildschirm
    ist die eigentliche Aussage: er zeigt, dass die Werkzeuge sich selbst
    pruefen, ohne dass jemand nachsehen muss (docs/WELTEN.md). Jedes
    Haekchen besteht aus zwei kurzen, gegeneinander gedrehten Balken --
    lesbar als Haken, nicht nur als Strich."""
    teile = []
    for dx in (-0.18, 0.18):
        teile.append(quader("rack_rahmen", (0.03, 0.28, 0.86), (dx, 0.0, 0.45), "bildschirm_rahmen"))
    teile.append(quader("rack_deckel", (0.39, 0.28, 0.03), (0.0, 0.0, 0.89), "rahmen"))
    teile.append(quader("rack_boden", (0.39, 0.28, 0.03), (0.0, 0.0, 0.03), "rahmen"))
    for i, hz in enumerate((0.16, 0.35, 0.54)):
        teile.append(quader("einschub_%d" % i, (0.32, 0.24, 0.11), (0.0, 0.0, hz),
                            "bildschirm_rahmen" if i % 2 else "rahmen"))
        if i != 1:
            teile.append(quader("einschub_led_%d" % i, (0.02, 0.01, 0.01), (0.13, -0.13, hz), "led_gruen"))
    teile.append(quader("kabelkanal", (0.39, 0.06, 0.03), (0.0, 0.15, 0.045), "rahmen"))
    teile.append(quader("wandschirm_rahmen", (0.36, 0.02, 0.26), (0.36, -0.04, 1.10), "bildschirm_rahmen"))
    teile.append(quader("wandschirm_schirm", (0.32, 0.006, 0.22), (0.36, -0.034, 1.10), "bildschirm"))
    haekchen = [(0.25, 1.16), (0.36, 1.10), (0.47, 1.04)]
    for i, (dx, dz) in enumerate(haekchen):
        teile.append(quader("haekchen_a_%d" % i, (0.03, 0.006, 0.012), (dx - 0.025, -0.028, dz - 0.02), "led_gruen", 40.0))
        teile.append(quader("haekchen_b_%d" % i, (0.05, 0.006, 0.012), (dx + 0.01, -0.028, dz), "led_gruen", -35.0))
    return teile


# --- Station 5: Grosskunde ---------------------------------------------------------
# Welt 4: das Ende dieses Akts (docs/STORY.md, "Ein Grosskunde will
# dasselbe noch einmal, fuer zwoelf Standorte"). Waechst vom einzelnen
# dicken Ordner zum Besprechungstisch mit zwei Stuehlen zum Besprechungstisch
# mit sechs Stuehlen und Praesentationsbildschirm -- von "eine Akte" zu
# "ein Auftrag, der zum Produkt wird".

def special_1():
    """Ein einzelner dicker Ordner auf einem kleinen Tisch -- der
    Grosskunde ist hier noch nicht mehr als eine einzelne, sehr dicke
    Akte."""
    teile = []
    teile.append(quader("tisch_platte", (0.44, 0.34, 0.03), (0.0, 0.0, 0.585), "holz_schreibtisch"))
    for dx in (-0.17, 0.17):
        teile.append(quader("tisch_bein", (0.03, 0.28, 0.57), (dx, 0.0, 0.285), "rahmen"))
    teile.append(quader("ordner", (0.14, 0.24, 0.34), (0.0, 0.0, 0.77), "rahmen"))
    teile.append(quader("ordner_ruecken", (0.145, 0.03, 0.34), (0.0, -0.12, 0.77), "akzent_gold"))
    return teile


def special_2():
    """Ein Besprechungstisch mit zwei Stuehlen -- ersetzt den kleinen Tisch
    vollstaendig: aus der Akte ist ein Gespraech geworden. Der Ordner liegt
    noch auf dem Tisch, aber jetzt sitzen zwei Leute daran."""
    teile = []
    teile.append(quader("tisch_platte", (1.10, 0.62, 0.04), (0.0, 0.0, 0.74), "holz_schreibtisch"))
    for dx in (-0.48, 0.48):
        for dy in (-0.24, 0.24):
            teile.append(quader("tisch_bein", (0.04, 0.04, 0.70), (dx, dy, 0.37), "rahmen"))
    teile.append(quader("ordner", (0.10, 0.18, 0.20), (0.30, 0.0, 0.86), "rahmen"))
    teile += _stuhl_einfach((0.0, -0.42))
    teile += _stuhl_einfach((0.0, 0.42), 180.0)
    return teile


def special_3():
    """Ein Besprechungstisch mit sechs Stuehlen und Praesentationsbildschirm
    -- ersetzt den kleinen Besprechungstisch vollstaendig: das ist kein
    Gespraech mehr unter zwei Leuten, das ist eine Praesentation vor einem
    Grosskunden mit zwoelf Standorten. Die Stuehle sind auf die Silhouette
    verkuerzt (ein Quader pro Sitz), sonst wuerde allein die Bestuhlung das
    Dreiecksbudget sprengen."""
    teile = []
    teile.append(quader("tisch_platte", (1.80, 0.80, 0.04), (0.0, 0.0, 0.74), "holz_schreibtisch"))
    for dx in (-0.80, 0.0, 0.80):
        for dy in (-0.32, 0.32):
            teile.append(quader("tisch_bein", (0.04, 0.04, 0.70), (dx, dy, 0.37), "rahmen"))
    plaetze = [(-0.65, -0.52), (0.0, -0.52), (0.65, -0.52),
               (-0.65, 0.52), (0.0, 0.52), (0.65, 0.52)]
    for i, (dx, dy) in enumerate(plaetze):
        teile.append(quader("stuhl_%d" % i, (0.30, 0.30, 0.44), (dx, dy, 0.22), "stuhl_polster"))
    teile.append(quader("schirm_stand", (0.10, 0.08, 0.10), (0.0, 0.86, 0.79), "bildschirm_rahmen"))
    teile.append(quader("schirm_hals", (0.02, 0.02, 0.16), (0.0, 0.86, 0.87), "rahmen"))
    teile.append(quader("schirm_rahmen", (0.42, 0.02, 0.30), (0.0, 0.90, 1.10), "bildschirm_rahmen"))
    teile.append(quader("schirm_flaeche", (0.38, 0.006, 0.26), (0.0, 0.894, 1.10), "bildschirm"))
    teile.append(quader("schirm_balken", (0.06, 0.004, 0.10), (-0.10, 0.892, 1.06), "akzent_gold"))
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
    print("=== STATIONSMODULE WELT 4 -- BUERO ===")
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
