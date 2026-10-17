"""K3 A1 "Buehne": Einrichtung je Zone auf hoechstens 5 Deko-Bloecke.

Bastians Handy-Urteil (docs/neu/K3_BEFUND_SPIELTEST.md H1/H2): Die Raeume sind
mit Deko ueberladen, die Stationen gehen unter. Messlatte Eatventure / My
Perfect Hotel: je Raum hoechstens 3-5 Deko-Teile, alle an der Wand, entsaettigt.
Die Mitte gehoert den Stationen.

Dieses Skript baut die Einrichtungen NICHT neu, sondern liest die fertigen
Exporte der sieben build_einrichtung_*.py-Skripte (eine GLB je Zone) und
schreibt daneben einrichtung_<zone>_buehne.glb:

  1. Das Mesh wird in zusammenhaengende Teile zerlegt (gleiche Eckpositionen).
  2. Teile, deren Huellquader sich beruehren, bilden einen Block -- ein Tisch
     mit Stuehlen und Tasse ist EIN Block, eine Kuechenzeile auch.
  3. Flache Teile auf dem Boden (Teppiche, Laeufer, Matten) fallen weg.
  4. Es bleiben hoechstens HOECHSTZAHL Bloecke, und nur solche an der Wand
     (Abstand zum Zonenrand <= WAND_NAEHE), die groessten zuerst.
  5. Alle Materialien werden entsaettigt (SAETTIGUNG).

Variante "a" der Karte (heute) laedt weiter die vollen Dateien; die Buehne
(Variante "b", GrundrissBauer.ist_buehne) laedt die _buehne-Dateien.

Aufruf (nach jedem Lauf eines build_einrichtung_*.py erneut):
    blender --background --python art_source/scripts/build_einrichtung_buehne.py
    blender --background --python art_source/scripts/build_einrichtung_buehne.py -- zimmer auftrag
danach:  godot_console --headless --path project --import

moebel_bericht() bricht LAUT ab (Exit 1), wenn eine Zone mehr als
HOECHSTZAHL_PFLICHT Bloecke behaelt.
"""

import bpy
import colorsys
import json
import os
import sys
import time

sys.dont_write_bytecode = True

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(SKRIPT_ORDNER))
WELTEN_JSON = os.path.join(WURZEL, "project", "data", "worlds", "worlds.json")
WELT_ORDNER = os.path.join(WURZEL, "project", "assets", "world")
ENDUNG = "_buehne"

HOECHSTZAHL = 4              # so viele Bloecke behaelt eine Zone hoechstens (Ziel)
HOECHSTZAHL_PFLICHT = 5      # Regel aus K3_PLAN: mehr ist ein Fehler
WAND_NAEHE = 0.75            # m: so nah muss ein Block am Zonenrand stehen
MIN_VOLUMEN = 0.05           # m3 (Grundflaeche x Hoehe): Kleinkram faellt weg
FLACH = 0.045                # m: flacher Teil am Boden = Teppich -> faellt weg
DRAHT_DICKE = 0.04           # m: duenner als das (und lang, in der Luft) = Draht
FUELLGRAD = 0.06             # Oberflaeche / Huellflaeche darunter = Draht, Kette
KLEINTEIL = 0.002            # m3: Huellquader kleiner als das = Kleinteil
HAENGT_AB = 1.2              # m: Bloecke, die erst hier beginnen, haengen nur
BERUEHRT = 0.02              # m: Abstand, ab dem zwei Teile einen Block bilden
SAETTIGUNG = 0.55            # Faktor auf die Saettigung aller Toene
HELLER = 0.04                # leicht aufhellen, damit Deko hinter Stationen zuruecktritt

# Je Datei von Hand: Punkte (Godot-Zonenkoordinaten x, z), deren Block bleiben
# MUSS bzw. wegfaellt -- fuer Faelle, in denen "gross und an der Wand" danebenliegt.
BEHALTEN = {
    # Befund H2: Matratze, Kleiderstange, Pflanze bleiben -- der Rest geht.
    "zimmer/einrichtung_zimmer": [(-2.38, 2.6), (3.1, 0.25), (-3.12, 0.92)],
}
WEGLASSEN = {
    # Groesser als jede Station und mitten im Blick (Vorschau k3a1_r3).
    "auftrag/einrichtung_hof": [(7.7, 0.0)],
    "kapital/einrichtung_dachterrasse": [(2.0, 1.6)],
}


# --- Welten lesen -----------------------------------------------------------------

def zonen_dateien(auswahl):
    """[(welt, datei, breite, tiefe)] fuer alle Zonen mit Einrichtung."""
    with open(WELTEN_JSON, encoding="utf-8") as f:
        daten = json.load(f)
    out = []
    for welt in daten["welten"]:
        wid = welt["id"]
        if auswahl and wid not in auswahl:
            continue
        for z in welt.get("zonen", []):
            datei = z.get("einrichtung", "")
            if not datei:
                continue
            breite = float(z["x2"]) - float(z["x1"]) + 1.0
            tiefe = float(z["z2"]) - float(z["z1"]) + 1.0
            namen = [datei]
            varianten = z.get("varianten", {})
            if varianten:
                namen = sorted({datei + endung for endung in varianten.values()})
            for name in namen:
                out.append((wid, name, breite, tiefe))
    return out


# --- Zerlegen ---------------------------------------------------------------------

class Vereinigung:
    def __init__(self, n):
        self.eltern = list(range(n))

    def finde(self, a):
        while self.eltern[a] != a:
            self.eltern[a] = self.eltern[self.eltern[a]]
            a = self.eltern[a]
        return a

    def vereine(self, a, b):
        ra, rb = self.finde(a), self.finde(b)
        if ra != rb:
            self.eltern[rb] = ra


def teile_finden(mesh):
    """Zusammenhaengende Flaechengruppen. Verbunden ist, was Eckpositionen teilt
    (glTF trennt Ecken an harten Kanten -- der Index allein reicht nicht)."""
    n = len(mesh.polygons)
    uf = Vereinigung(n)
    erster = {}
    ecken = [v.co.copy() for v in mesh.vertices]
    for p in mesh.polygons:
        for vi in p.vertices:
            c = ecken[vi]
            schluessel = (round(c.x * 1000), round(c.y * 1000), round(c.z * 1000))
            if schluessel in erster:
                uf.vereine(erster[schluessel], p.index)
            else:
                erster[schluessel] = p.index
    gruppen = {}
    for p in mesh.polygons:
        gruppen.setdefault(uf.finde(p.index), []).append(p.index)
    teile = []
    for flaechen in gruppen.values():
        punkte = [ecken[vi] for fi in flaechen for vi in mesh.polygons[fi].vertices]
        # Blender (x, y, z) -> Godot (x, z, -y)
        gx = [c.x for c in punkte]
        gy = [c.z for c in punkte]
        gz = [-c.y for c in punkte]
        teile.append({"flaechen": flaechen,
                      "inhalt": sum(mesh.polygons[fi].area for fi in flaechen),
                      "min": (min(gx), min(gy), min(gz)),
                      "max": (max(gx), max(gy), max(gz))})
    return teile


def _beruehren(a, b, abstand):
    for i in range(3):
        if a["min"][i] > b["max"][i] + abstand or b["min"][i] > a["max"][i] + abstand:
            return False
    return True


def bloecke_bilden(teile):
    """Teile, deren Huellquader sich beruehren, werden zu Bloecken. Flache Teile
    am Boden (Teppiche) verbinden nichts -- sonst waere alles auf einem Teppich
    ein Block."""
    feste = [t for t in teile if not ist_flach(t) and not ist_draht(t)]
    uf = Vereinigung(len(feste))
    for i in range(len(feste)):
        for j in range(i + 1, len(feste)):
            if _beruehren(feste[i], feste[j], BERUEHRT):
                uf.vereine(i, j)
    gruppen = {}
    for i, t in enumerate(feste):
        gruppen.setdefault(uf.finde(i), []).append(t)
    bloecke = []
    for glieder in gruppen.values():
        mn = tuple(min(t["min"][k] for t in glieder) for k in range(3))
        mx = tuple(max(t["max"][k] for t in glieder) for k in range(3))
        flaechen = [f for t in glieder for f in t["flaechen"]]
        bloecke.append({"min": mn, "max": mx, "flaechen": flaechen})
    # Draehte (Lichterketten, Kabel, Stangen) verbinden nichts; sie gehoeren zu
    # dem Block, in dem ihre Mitte liegt (Kleiderstange), sonst fallen sie weg.
    for t in teile:
        if ist_flach(t) or not ist_draht(t):
            continue
        mitte = [(t["min"][k] + t["max"][k]) / 2.0 for k in range(3)]
        for b in bloecke:
            if all(b["min"][k] - 0.05 <= mitte[k] <= b["max"][k] + 0.05 for k in range(3)):
                b["flaechen"].extend(t["flaechen"])
                break
    # Was nur in der Luft haengt (Lampen, Lichterketten-Birnen), ist kein Block.
    bloecke = [b for b in bloecke if b["min"][1] <= HAENGT_AB]
    flach = [f for t in teile if ist_flach(t) for f in t["flaechen"]]
    return bloecke, flach


def ist_draht(t):
    """Lang, duenn, waagerecht und ueber dem Boden: Lichterkette, Kabel, Stange."""
    masse = [t["max"][k] - t["min"][k] for k in range(3)]
    # Duenn verteilt (Lichterkette als ein Stueck, Kabel im Bogen): die echte
    # Oberflaeche ist winzig gegen die Huelle -- verbindet nichts.
    huelle = 2.0 * (masse[0] * masse[1] + masse[1] * masse[2] + masse[0] * masse[2])
    if huelle > 0.5 and t["inhalt"] < huelle * FUELLGRAD:
        return True
    if t["min"][1] < 0.25:
        return False
    # Kleinteil in der Luft (Birne einer Lichterkette, Kettenglied, Tasse):
    # verbindet nichts, haengt sich nur an den Block, in dem es liegt.
    if masse[0] * masse[1] * masse[2] < KLEINTEIL:
        return True
    return min(masse) < DRAHT_DICKE and max(masse[0], masse[2]) > 0.5


def ist_flach(t):
    return t["max"][1] - t["min"][1] <= FLACH and t["max"][1] <= FLACH + 0.02


def volumen(b):
    dx = b["max"][0] - b["min"][0]
    dy = min(b["max"][1] - max(b["min"][1], 0.0), 1.6)
    dz = b["max"][2] - b["min"][2]
    return dx * max(dy, 0.05) * dz


def wandabstand(b, breite, tiefe):
    hx, hz = breite / 2.0, tiefe / 2.0
    return min(b["min"][0] + hx, hx - b["max"][0], b["min"][2] + hz, hz - b["max"][2])


def _enthaelt(b, punkt):
    x, z = punkt
    return b["min"][0] - 0.05 <= x <= b["max"][0] + 0.05 and b["min"][2] - 0.05 <= z <= b["max"][2] + 0.05


def auswaehlen(bloecke, schluessel, breite, tiefe):
    muss = BEHALTEN.get(schluessel, [])
    weg = WEGLASSEN.get(schluessel, [])
    for b in bloecke:
        b["vol"] = volumen(b)
        b["wand"] = wandabstand(b, breite, tiefe)
        b["muss"] = any(_enthaelt(b, p) for p in muss)
        b["weg"] = any(_enthaelt(b, p) for p in weg)
    if muss:
        # Von Hand gewaehlt: genau diese Bloecke, sonst nichts.
        kandidaten = [b for b in bloecke if b["muss"] and not b["weg"]]
        kandidaten.sort(key=lambda b: -b["vol"])
        return kandidaten[:HOECHSTZAHL_PFLICHT]
    kandidaten = [b for b in bloecke if not b["weg"] and (
        b["wand"] <= WAND_NAEHE and b["vol"] >= MIN_VOLUMEN)]
    kandidaten.sort(key=lambda b: (not b["muss"], -b["vol"]))
    return kandidaten[:HOECHSTZAHL]


# --- Bericht ----------------------------------------------------------------------

BERICHT = []


def moebel_bericht():
    """Je Zone: Bloecke vorher/nachher. Bricht LAUT ab, wenn eine Zone mehr als
    HOECHSTZAHL_PFLICHT Bloecke behaelt (K3_PLAN A1)."""
    print("")
    print("=== BUEHNE: Deko-Bloecke je Zone (Regel: hoechstens %d) ===" % HOECHSTZAHL_PFLICHT)
    zu_viel = []
    for welt, datei, vorher, nachher, flach, groessen in BERICHT:
        print("  %-10s %-40s %3d -> %d   (Teppiche weg: %d)  %s"
              % (welt, datei, vorher, nachher, flach, groessen))
        if nachher > HOECHSTZAHL_PFLICHT:
            zu_viel.append(datei)
    if zu_viel:
        print("")
        print("!!! ZU VIELE DEKO-BLOECKE: %s" % ", ".join(zu_viel))
        sys.exit(1)


# --- Blender ----------------------------------------------------------------------

def leeren():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importieren(pfad):
    bpy.ops.import_scene.gltf(filepath=pfad)
    netze = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in bpy.data.objects:
        o.select_set(o in netze)
    bpy.context.view_layer.objects.active = netze[0]
    if len(netze) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in list(bpy.data.objects):
        if o != obj:
            bpy.data.objects.remove(o, do_unlink=True)
    return obj


def flaechen_loeschen(obj, behalten):
    maske = [False] * len(obj.data.polygons)
    for i in range(len(maske)):
        maske[i] = i not in behalten
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.polygons.foreach_set("select", maske)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")


def _linear_zu_srgb(c):
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _srgb_zu_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def entsaettigen(obj):
    for slot in obj.material_slots:
        mat = slot.material
        if mat is None or mat.name.endswith(ENDUNG):
            continue
        kopie = mat.copy()
        kopie.name = mat.name + ENDUNG
        if kopie.node_tree is not None:
            for knoten in kopie.node_tree.nodes:
                if knoten.type == "BSDF_PRINCIPLED":
                    farbe = knoten.inputs["Base Color"].default_value
                    r, g, b = (_linear_zu_srgb(farbe[i]) for i in range(3))
                    h, s, v = colorsys.rgb_to_hsv(r, g, b)
                    s *= SAETTIGUNG
                    v = min(1.0, v + HELLER * (1.0 - v))
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    knoten.inputs["Base Color"].default_value = (
                        _srgb_zu_linear(r), _srgb_zu_linear(g), _srgb_zu_linear(b), farbe[3])
        slot.material = kopie


def exportieren(obj, pfad):
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    for versuch in range(6):
        try:
            bpy.ops.export_scene.gltf(
                filepath=pfad, export_format="GLB", use_selection=True,
                export_apply=True, export_yup=True, export_materials="EXPORT",
                export_cameras=False, export_lights=False,
            )
            return
        except (OSError, RuntimeError) as fehler:
            # Errno 22, solange Godot parallel importiert (CLAUDE.md).
            print("    Export-Fehler (%s), Versuch %d" % (fehler, versuch + 1))
            time.sleep(1.5)
    raise SystemExit("Export gescheitert: %s" % pfad)


def datei_bauen(welt, datei, breite, tiefe):
    quelle = os.path.join(WELT_ORDNER, welt, datei + ".glb")
    if not os.path.exists(quelle):
        print("  FEHLT: %s" % quelle)
        return
    leeren()
    obj = importieren(quelle)
    teile = teile_finden(obj.data)
    bloecke, flach = bloecke_bilden(teile)
    gewaehlt = auswaehlen(bloecke, "%s/%s" % (welt, datei), breite, tiefe)
    behalten = set(f for b in gewaehlt for f in b["flaechen"])
    groessen = " ".join("%.2f@(%+.1f,%+.1f)%s" % (
        b["vol"], (b["min"][0] + b["max"][0]) / 2, (b["min"][2] + b["max"][2]) / 2,
        "*" if b["muss"] else "") for b in gewaehlt)
    if "--alle" in sys.argv:
        for b in sorted(bloecke, key=lambda b: -volumen(b)):
            print("      Block %.2f  x %+.2f..%+.2f  y %.2f..%.2f  z %+.2f..%+.2f" % (
                volumen(b), b["min"][0], b["max"][0], b["min"][1], b["max"][1], b["min"][2], b["max"][2]))
    BERICHT.append((welt, datei, len(bloecke), len(gewaehlt), len(flach) > 0, groessen))
    ziel = os.path.join(WELT_ORDNER, welt, datei + ENDUNG + ".glb")
    if not behalten:
        # Leere Zone: ein unsichtbar kleines Dreieck waere Tarnung -- lieber eine
        # leere Szene ohne Mesh exportieren geht nicht; daher ein Hinweis.
        print("  LEER: %s/%s behaelt keinen Block" % (welt, datei))
    flaechen_loeschen(obj, behalten)
    entsaettigen(obj)
    obj.name = datei + ENDUNG
    obj.data.name = datei + ENDUNG
    exportieren(obj, ziel)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    auswahl = [a for a in argumente if not a.startswith("--")]
    for welt, datei, breite, tiefe in zonen_dateien(auswahl):
        print("--- %s/%s (%g x %g)" % (welt, datei, breite, tiefe))
        datei_bauen(welt, datei, breite, tiefe)
    moebel_bericht()
    print("=== FERTIG ===")


if __name__ == "__main__":
    main()
