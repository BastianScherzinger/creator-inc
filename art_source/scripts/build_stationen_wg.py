"""Erzeugt die Stationen der WG (Welt 1 in die Tiefe, TASK 075) als GLB.

Aufruf:
    blender --background --python art_source/scripts/build_stationen_wg.py
    blender --background --python art_source/scripts/build_stationen_wg.py -- --vorschau
    blender --background --python art_source/scripts/build_stationen_wg.py -- --nur intake

Vertrag (docs/WELT1_TIEFE.md, Paragraf 10):
    station_<id>_basis.glb
    station_<id>_ausstattung_<n>_<m>.glb     n = 1..3 (Platz), m = 0..3 (Modellstufe)

Alle Dateien einer Station teilen sich EINEN Ursprung (Stationsursprung,
Boden y = 0). Jedes Teil liegt also schon an seinem Platz; das Spiel blendet
pro Platz genau eine Modellstufe ein. Die Plaetze duerfen sich untereinander
und mit der Basis nie ueberschneiden -- `pruefe_ueberschneidungen()` testet
das fuer JEDE Kombination (paarweise genuegt, weil Ueberschneidung eine
Paar-Eigenschaft ist) mit einem Dreiecks-BVH und bricht den Lauf nicht ab,
meldet aber laut.

Koordinaten: ALLE Masse in diesem Skript sind GODOT-Koordinaten (y oben,
Vorderseite +z). Die Helfer rechnen um: Godot (x, y, z) -> Blender (x, -z, y).
Exportiert wird mit export_yup=True, das dreht es wieder zurueck.

Farben: glTF speichert baseColorFactor LINEAR, Godot zeigt albedo in sRGB.
Deshalb geht jede Farbe durch farbe("#hex") -> (c/255)^2,2.

Dateinamen neutral (ADR-010): Die Datei heisst nach Station und Platz, nie
nach dem Gegenstand, der gerade darin steht.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HIER = os.path.dirname(os.path.abspath(__file__))
PROJEKT = os.path.abspath(os.path.join(HIER, "..", ".."))
AUSGABE = os.path.join(PROJEKT, "project", "assets", "stations", "zimmer")
VORSCHAU = os.path.join(PROJEKT, "art_source", "vorschau", "team_stationen")

BUDGET_BASIS = 1200
BUDGET_AUSSTATTUNG = 700


# --- Farben ------------------------------------------------------------------

def farbe(hexwert, alpha=1.0):
    """sRGB-Hex -> lineares RGBA. linear = (c/255)^2,2 je Kanal."""
    h = hexwert.lstrip("#")
    return tuple(((int(h[i:i + 2], 16) / 255.0) ** 2.2) for i in (0, 2, 4)) + (alpha,)


# name: (sRGB-Hex, Leuchtstaerke). Warm, hell, gesaettigt aber nicht grell
# (WELT1_TIEFE 10.1). Holz der Moebel bewusst dunkler/roetlicher als der
# Boden (#D9A66B), sonst verschwinden Tische im Boden.
PALETTE = {
    "holz":          ("#B87842", 0.0),   # Moebelholz mittel
    "holz_hell":     ("#DDAE74", 0.0),   # Platten, Regalboeden
    "holz_dunkel":   ("#7E4E2C", 0.0),   # Rahmen, Beine
    "kork":          ("#C99661", 0.0),
    "creme":         ("#F6EEDF", 0.0),   # Whiteboard, Lampenschirm aussen
    "papier":        ("#FFFBF2", 0.0),
    "grau_dunkel":   ("#3A3E46", 0.0),   # Geraete
    "grau_mittel":   ("#6E747E", 0.0),
    "grau_hell":     ("#B9BEC6", 0.0),   # Metall, Klebeband
    "schwarz":       ("#23252A", 0.0),
    "stoff_grau":    ("#7D828C", 0.0),   # Sofa
    "stoff_hell":    ("#9CA1AA", 0.0),   # Sofakissen
    "teppich":       ("#D98C6A", 0.0),   # runder Teppich am Set
    "stoffwand":     ("#5FA39E", 0.0),   # Hintergrund-Stoff
    "gelb":          ("#FFD54A", 0.0),
    "orange":        ("#FFB21E", 0.0),
    "rosa":          ("#FF93A8", 0.0),
    "hellblau":      ("#86CCF2", 0.0),
    "gruen_hell":    ("#97D77E", 0.0),
    "rot":           ("#E5533C", 0.0),
    "blau":          ("#3C86E0", 0.0),   # Netzwerkkabel, Stuhlakzent
    "lila":          ("#8C6BD6", 0.0),
    "pflanze":       ("#5DA84A", 0.0),
    "pflanze_dunkel":("#3F8A3A", 0.0),
    "topf":          ("#D0764A", 0.0),
    "karton":        ("#C49A64", 0.0),
    "beige_alt":     ("#CDBFA6", 0.0),   # vergilbter alter Kunststoff
    "teppich_grau":  ("#BDB5AA", 0.0),   # Wohnzimmerteppich
    "senf":          ("#E0A73C", 0.0),
    # leuchtend
    "schirm":        ("#CDEBFF", 0.55),  # Bildschirmgrund
    "schirm_blau":   ("#4A9DD6", 0.55),  # angedeuteter Inhalt
    "schirm_orange": ("#FFB21E", 0.55),
    "schirm_gruen":  ("#3DBE4B", 0.55),
    "schirm_rot":    ("#E5533C", 0.55),
    "licht_warm":    ("#FFE6A8", 1.2),   # Lampen, Kerze, Lichterkette
    "licht_weiss":   ("#FFFFFF", 1.0),   # Ringlicht, Softbox
    "led_gruen":     ("#5BE07A", 1.2),
    "led_blau":      ("#4FB0FF", 1.2),
    "rgb_magenta":   ("#E04FD0", 1.2),
    "rgb_cyan":      ("#3FD6F0", 1.2),
}


def material(name):
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    hexwert, leuchten = PALETTE[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    lin = farbe(hexwert)
    bsdf.inputs["Base Color"].default_value = lin
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
    if leuchten > 0.0:
        bsdf.inputs["Emission Color"].default_value = lin
        bsdf.inputs["Emission Strength"].default_value = leuchten
    mat.diffuse_color = lin
    return mat


# --- Koordinaten -------------------------------------------------------------

# Godot -> Blender: bx = gx, by = -gz, bz = gy
_C = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))


def _godot_rotation(dreh):
    """Euler in Grad um Godot-Achsen (rx, ry, rz). Reihenfolge: erst z, dann
    x (Neigung), zuletzt y (Gieren) -- so bleibt 'ry' immer die Blickrichtung
    auf dem Boden, egal wie das Teil geneigt ist."""
    rx, ry, rz = (math.radians(a) for a in dreh)
    m = (Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
         @ Matrix.Rotation(rz, 3, "Z"))
    return _C @ m @ _C.transposed()


def _setze_transform(obj, pos, dreh):
    rot = _godot_rotation(dreh).to_4x4()
    obj.matrix_world = Matrix.Translation(Vector((pos[0], -pos[2], pos[1]))) @ rot


def _objekt_aus_bmesh(name, bm, mat_name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    me.materials.append(material(mat_name))
    return obj


def _bevel(obj, breite, segmente):
    if segmente <= 0 or breite <= 0.0:
        return
    mod = obj.modifiers.new("bevel", "BEVEL")
    mod.width = breite
    mod.segments = segmente
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(35.0)
    mod.harden_normals = True
    for poly in obj.data.polygons:
        poly.use_smooth = True


def kasten(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0), rund=None):
    """Quader, Masse in Godot (breite x, hoehe y, tiefe z). Kanten werden je
    nach kleinster Kante abgerundet: ab 5 cm zwei Segmente, ab 1,5 cm eins,
    darunter gar nicht (die Rundung waere unsichtbar, kostet aber Dreiecke).
    `rund` erzwingt (breite, segmente)."""
    sx, sy, sz = groesse
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)
    obj = _objekt_aus_bmesh(name, bm, mat)
    kleinste = min(groesse)
    if rund is None:
        # Zwei Segmente kosten 108 Dreiecke je Quader, eins 44, keins 12.
        # Zwei nur dort, wo die Rundung aus der Kameradistanz sichtbar ist.
        if kleinste >= 0.08 and max(groesse) >= 0.30:
            rund = (min(0.022, kleinste * 0.3), 2)
        elif kleinste >= 0.015:
            rund = (min(0.015, kleinste * 0.3), 1)
        else:
            rund = (0.0, 0)
    _bevel(obj, rund[0], rund[1])
    _setze_transform(obj, pos, dreh)
    return obj


def zylinder(name, radius, hoehe, pos, mat, seiten=12, dreh=(0.0, 0.0, 0.0),
             radius_oben=None, rund=None):
    """Zylinder/Kegelstumpf entlang Godot-y, Mittelpunkt bei pos."""
    bm = bmesh.new()
    r2 = radius if radius_oben is None else radius_oben
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seiten,
                          radius1=radius, radius2=r2, depth=hoehe)
    obj = _objekt_aus_bmesh(name, bm, mat)
    if rund is None:
        rund = (min(0.012, radius * 0.25, hoehe * 0.25), 1) if radius >= 0.075 and hoehe >= 0.02 else (0.0, 0)
    if rund[1] > 0:
        _bevel(obj, rund[0], rund[1])
    else:
        for poly in obj.data.polygons:
            poly.use_smooth = True
        obj.data.set_sharp_from_angle(angle=math.radians(50.0))
    _setze_transform(obj, pos, dreh)
    return obj


def stab(name, a, b, radius, mat, seiten=6):
    """Zylinder von Punkt a nach Punkt b (Godot). Fuer Stative, Arme, Kabel."""
    va = Vector((a[0], -a[2], a[1]))
    vb = Vector((b[0], -b[2], b[1]))
    d = vb - va
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seiten,
                          radius1=radius, radius2=radius, depth=d.length)
    obj = _objekt_aus_bmesh(name, bm, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.set_sharp_from_angle(angle=math.radians(70.0))
    rot = Vector((0.0, 0.0, 1.0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    obj.matrix_world = Matrix.Translation((va + vb) * 0.5) @ rot
    return obj


def kugel(name, radius, pos, mat, stufen=2, skala=(1.0, 1.0, 1.0), dreh=(0.0, 0.0, 0.0)):
    """Ikosaeder-Kugel, geglaettet. stufen=1: 20 Dreiecke, 2: 80."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=stufen, radius=radius)
    bmesh.ops.scale(bm, vec=Vector((skala[0], skala[2], skala[1])), verts=bm.verts)
    obj = _objekt_aus_bmesh(name, bm, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    _setze_transform(obj, pos, dreh)
    return obj


def ring(name, radius, dicke, pos, mat, dreh=(0.0, 0.0, 0.0), segmente=16, quer=6, anteil=1.0):
    """Torus, liegt flach (Achse Godot-y). Mit dreh=(90,..) aufstellen.
    anteil < 1: offener Bogen (Kopfhoererbuegel), beginnt bei lokal +x."""
    bm = bmesh.new()
    verts = []
    offen = anteil < 0.999
    n_ring = segmente + 1 if offen else segmente
    for i in range(n_ring):
        u = 2.0 * math.pi * anteil * i / segmente
        reihe = []
        for j in range(quer):
            v = 2.0 * math.pi * j / quer
            r = radius + dicke * math.cos(v)
            reihe.append(bm.verts.new((r * math.cos(u), r * math.sin(u), dicke * math.sin(v))))
        verts.append(reihe)
    for i in range(segmente):
        k = i + 1 if offen else (i + 1) % segmente
        for j in range(quer):
            bm.faces.new((verts[i][j], verts[k][j], verts[k][(j + 1) % quer], verts[i][(j + 1) % quer]))
    obj = _objekt_aus_bmesh(name, bm, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    _setze_transform(obj, pos, dreh)
    return obj


def keil(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0)):
    """Pyramidenstumpf (Softbox, Lampenschirm eckig): unten groesse[0] x
    groesse[2], oben 35 %. Achse Godot-y."""
    sx, sy, sz = groesse
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=4,
                          radius1=0.7071, radius2=0.7071 * 0.35, depth=1.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.radians(45.0), 3, "Z"))
    bmesh.ops.scale(bm, vec=Vector((sx, sz, sy)), verts=bm.verts)
    obj = _objekt_aus_bmesh(name, bm, mat)
    _bevel(obj, min(0.012, min(groesse) * 0.2), 1)
    _setze_transform(obj, pos, dreh)
    return obj


def lokal(basis_pos, basis_dreh_y, offset):
    """Punkt relativ zu einem gedrehten Teil (Drehung nur um Godot-y)."""
    a = math.radians(basis_dreh_y)
    ox, oy, oz = offset
    return (basis_pos[0] + ox * math.cos(a) + oz * math.sin(a),
            basis_pos[1] + oy,
            basis_pos[2] - ox * math.sin(a) + oz * math.cos(a))


def _mg(dreh):
    rx, ry, rz = (math.radians(a) for a in dreh)
    return (Matrix.Rotation(ry, 3, "Y") @ Matrix.Rotation(rx, 3, "X")
            @ Matrix.Rotation(rz, 3, "Z"))


def punkt(pos, dreh, off):
    """Punkt `off` im lokalen System eines Teils mit Position pos und
    Drehung dreh (alles Godot) -> Godot-Weltpunkt."""
    v = Vector(pos) + _mg(dreh) @ Vector(off)
    return (v.x, v.y, v.z)


def verkette(dreh_aussen, dreh_innen):
    """Drehung eines Unterteils (dreh_innen, relativ) in einem gedrehten
    Traeger (dreh_aussen) -> Euler (Godot, gleiche Konvention y-x-z)."""
    m = _mg(dreh_aussen) @ _mg(dreh_innen)
    sx = max(-1.0, min(1.0, -m[1][2]))
    rx = math.asin(sx)
    if abs(math.cos(rx)) > 1e-6:
        ry = math.atan2(m[0][2], m[2][2])
        rz = math.atan2(m[1][0], m[1][1])
    else:
        ry = math.atan2(-m[2][0], m[0][0])
        rz = 0.0
    return (math.degrees(rx), math.degrees(ry), math.degrees(rz))


# --- Wiederkehrende Gegenstaende ---------------------------------------------
# Alle nehmen Position (Godot) und Drehung (Godot-Euler, Grad) und geben eine
# Liste von Objekten zurueck. Masse leicht uebertrieben: aus der Isometrie
# muss ein Handy ein Handy sein, auch wenn es real nur 15 cm hat.

def _flach(name, b, h, pos, dreh, off, mat):
    return kasten(name, (b, h, 0.003), punkt(pos, dreh, off), mat, dreh, rund=(0, 0))


def schirm_inhalt(pos, dreh, breite, hoehe, art="balken", tiefe=0.0):
    """Leuchtende Flaeche mit angedeutetem Inhalt (keine Schrift, keine
    Logos). pos = Mitte der Flaeche, Flaeche liegt in der lokalen x/y-Ebene
    und zeigt nach lokal +z."""
    t = [kasten("schirm", (breite, hoehe, 0.004), punkt(pos, dreh, (0, 0, tiefe)), "schirm", dreh, rund=(0, 0))]
    z = tiefe + 0.0035
    b, h = breite, hoehe
    if art == "balken":        # Kopfzeile + Kachel + zwei Zeilen
        t.append(_flach("i", b * 0.84, h * 0.14, pos, dreh, (0, h * 0.33, z), "schirm_blau"))
        t.append(_flach("i", b * 0.36, h * 0.40, pos, dreh, (-b * 0.22, -h * 0.12, z), "schirm_orange"))
        for k in range(2):
            t.append(_flach("i", b * 0.36, h * 0.09, pos, dreh, (b * 0.22, h * 0.02 - k * h * 0.2, z), "schirm_blau"))
    elif art == "kurve":       # aufsteigendes Balkendiagramm
        for k in range(4):
            hk = h * (0.2 + 0.17 * k)
            mat = "schirm_gruen" if k == 3 else "schirm_blau"
            t.append(_flach("i", b * 0.14, hk, pos, dreh, (-b * 0.3 + k * b * 0.2, -h * 0.38 + hk * 0.5, z), mat))
    elif art == "video":       # Vorschaubild + Seitenleiste + Zeitleiste
        t.append(_flach("i", b * 0.6, h * 0.5, pos, dreh, (-b * 0.1, h * 0.12, z), "schirm_blau"))
        t.append(_flach("i", b * 0.84, h * 0.08, pos, dreh, (0, -h * 0.32, z), "schirm_orange"))
        t.append(_flach("i", b * 0.18, h * 0.5, pos, dreh, (b * 0.33, h * 0.12, z), "schirm_gruen"))
    elif art == "schlange":    # Warteschlangen-Balken
        for k, (lg, mat) in enumerate(((0.8, "schirm_gruen"), (0.55, "schirm_orange"), (0.35, "schirm_blau"))):
            t.append(_flach("i", b * lg, h * 0.16, pos, dreh, (-b * 0.42 + b * lg * 0.5, h * 0.25 - k * h * 0.27, z), mat))
    elif art == "plan":        # Kalenderraster
        for r in range(2):
            for s in range(3):
                mat = "schirm_orange" if (r, s) == (0, 1) else "schirm_blau"
                t.append(_flach("i", b * 0.24, h * 0.3, pos, dreh, (-b * 0.29 + s * b * 0.29, h * 0.17 - r * h * 0.38, z), mat))
    elif art == "chat":        # Sprechblasen
        t.append(_flach("i", b * 0.6, h * 0.16, pos, dreh, (-b * 0.12, h * 0.28, z), "schirm_blau"))
        t.append(_flach("i", b * 0.55, h * 0.16, pos, dreh, (b * 0.14, 0.0, z), "schirm_gruen"))
        t.append(_flach("i", b * 0.5, h * 0.16, pos, dreh, (-b * 0.14, -h * 0.28, z), "schirm_blau"))
    return t


def handy(pos, dreh, inhalt="chat", gross=1.0):
    """Handy, pos = Mitte, Bildschirm zeigt nach lokal +z."""
    b, h, d = 0.10 * gross, 0.19 * gross, 0.016
    t = [kasten("handy", (b, h, d), pos, "grau_dunkel", dreh, rund=(0.006, 1))]
    t += schirm_inhalt(pos, dreh, b * 0.82, h * 0.86, inhalt, tiefe=d * 0.5 + 0.001)
    return t


def laptop(pos, dreh, breite=0.40, tiefe=0.28, winkel=105.0, mat="grau_mittel", inhalt="video", dicke=0.022):
    """Laptop, pos = Mitte der Unterseite. Deckel klappt an der Hinterkante
    (lokal -z) auf, Bildschirm schaut nach lokal +z."""
    t = []
    t.append(kasten("deck", (breite, dicke, tiefe), punkt(pos, dreh, (0, dicke * 0.5, 0)), mat, dreh, rund=(0.008, 1)))
    t.append(kasten("tasten", (breite * 0.82, 0.003, tiefe * 0.42), punkt(pos, dreh, (0, dicke + 0.0015, -tiefe * 0.1)), "grau_dunkel", dreh, rund=(0, 0)))
    t.append(kasten("pad", (breite * 0.26, 0.003, tiefe * 0.2), punkt(pos, dreh, (0, dicke + 0.0015, tiefe * 0.3)), "grau_hell", dreh, rund=(0, 0)))
    neig = winkel - 90.0
    innen = (-neig, 0, 0)
    d2 = verkette(dreh, innen)
    sh = tiefe * 0.92
    mitte_lokal = Vector((0, dicke, -tiefe * 0.5 + 0.012)) + _mg(innen) @ Vector((0, sh * 0.5 + 0.004, -0.004))
    mitte = punkt(pos, dreh, tuple(mitte_lokal))
    t.append(kasten("deckel", (breite, sh, 0.016), mitte, mat, d2, rund=(0.006, 1)))
    t += schirm_inhalt(mitte, d2, breite * 0.86, sh * 0.8, inhalt, tiefe=0.0095)
    return t


def monitor(pos, dreh, breite, hoehe, inhalt="video", fuss=True, fuss_hoehe=0.12):
    """Monitor. Mit Fuss: pos = Mitte unten am Fuss. Ohne: pos = Mitte der
    Gehaeuse-Unterkante. Bildschirm schaut nach lokal +z."""
    t = []
    d = 0.035
    unten = 0.0
    if fuss:
        t.append(kasten("fuss", (breite * 0.36, 0.018, 0.16), punkt(pos, dreh, (0, 0.009, -0.03)), "grau_dunkel", dreh, rund=(0.006, 1)))
        t.append(kasten("hals", (0.05, fuss_hoehe + 0.05, 0.03), punkt(pos, dreh, (0, 0.018 + (fuss_hoehe + 0.05) * 0.5, -0.05)), "grau_dunkel", dreh))
        unten = 0.018 + fuss_hoehe
    mitte = punkt(pos, dreh, (0, unten + hoehe * 0.5, 0))
    t.append(kasten("gehaeuse", (breite, hoehe, d), mitte, "schwarz", dreh, rund=(0.01, 2)))
    t += schirm_inhalt(mitte, dreh, breite * 0.9, hoehe * 0.84, inhalt, tiefe=d * 0.5 + 0.001)
    return t


def buecher(pos, dreh, anzahl, breite=0.26, tiefe=0.20, dicke=0.045,
            farben=("rot", "hellblau", "gelb", "gruen_hell")):
    """Buecherstapel, pos = Mitte unten. Gibt (teile, hoehe) zurueck."""
    t = []
    y = 0.0
    versatz = (0.0, 6.0, -4.0, 8.0, -7.0, 3.0)
    for i in range(anzahl):
        d = verkette(dreh, (0, versatz[i % len(versatz)], 0))
        t.append(kasten("buch", (breite, dicke, tiefe), punkt(pos, dreh, (0, y + dicke * 0.5, 0)),
                        farben[i % len(farben)], d, rund=(0.006, 1)))
        y += dicke
    return t, y


def tasse(pos, mat="creme", hoehe=0.10, radius=0.045, voll=True):
    t = [zylinder("tasse", radius, hoehe, (pos[0], pos[1] + hoehe * 0.5, pos[2]), mat, seiten=10)]
    if voll:
        t.append(zylinder("inhalt", radius * 0.8, 0.004, (pos[0], pos[1] + hoehe + 0.001, pos[2]), "holz_dunkel", seiten=8, rund=(0, 0)))
    t.append(ring("henkel", radius * 0.42, 0.009, (pos[0] + radius + 0.012, pos[1] + hoehe * 0.5, pos[2]), mat,
                  dreh=(90, 0, 0), segmente=6, quer=4))
    return t


def pflanze(pos, groesse=1.0, topf_mat="topf", blaetter=5):
    """Topfpflanze, pos = Mitte unten. Blaetter als gestauchte Kugeln."""
    g = groesse
    t = [zylinder("topf", 0.07 * g, 0.10 * g, (pos[0], pos[1] + 0.05 * g, pos[2]), topf_mat, seiten=8, radius_oben=0.085 * g)]
    for i in range(blaetter):
        w = 2.0 * math.pi * i / blaetter
        r = 0.06 * g
        mat = "pflanze" if i % 2 == 0 else "pflanze_dunkel"
        t.append(kugel("blatt", 0.065 * g, (pos[0] + math.cos(w) * r, pos[1] + (0.16 + 0.03 * (i % 2)) * g, pos[2] + math.sin(w) * r),
                       mat, stufen=1, skala=(1.0, 0.6, 1.0)))
    t.append(kugel("blatt_oben", 0.07 * g, (pos[0], pos[1] + 0.24 * g, pos[2]), "pflanze", stufen=1, skala=(0.9, 0.85, 0.9)))
    return t


def zettel(pos, dreh, groesse, mat):
    """Flaches Blatt/Klebezettel. pos = Mitte, liegt in lokaler x/y-Ebene."""
    return kasten("zettel", (groesse[0], groesse[1], 0.004), pos, mat, dreh, rund=(0, 0))


# =============================================================================
# Station 1: station_intake -- Ideen-Ecke
# Vorderseite +z, Ruecken an halbhoher Wand (z ~ -1,1).
# Hintere Reihe von links: Whiteboard-Platz (Platz 1, m3) | Pinnwand (Basis) |
# Tisch (Basis). Davor: Boden vor der Pinnwand (Platz 1, m0) und Hocker
# (Basis, Platz 1 legt ab m1 das Notizbuch darauf). Tischplatte links =
# Platz 3, rechts = Platz 2. Stehlampe rechts vorn = Platz 3, m3.
# =============================================================================

I_TISCH_X = (0.30, 1.08)
I_TISCH_Z = (-1.04, -0.60)
I_TISCH_H = 0.74
I_AUF = I_TISCH_H + 0.002                    # Dinge auf der Platte: 2 mm Luft
I_PINN = {"x": -0.19, "b": 0.86, "unten": 0.80, "h": 0.62, "z": -0.925}
I_HOCKER = (0.70, -0.26)
I_HOCKER_H = 0.46
I_KORK_VORNE = I_PINN["z"] + 0.015 + 0.012   # Vorderflaeche des Korks


def intake_basis():
    t = []
    x0, x1 = I_TISCH_X
    z0, z1 = I_TISCH_Z
    tx, tz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
    tb, td = x1 - x0, z1 - z0
    # Tisch mit Regalboden
    t.append(kasten("platte", (tb, 0.04, td), (tx, I_TISCH_H - 0.02, tz), "holz_hell"))
    for sx in (x0 + 0.025, x1 - 0.025):
        t.append(kasten("seite", (0.04, I_TISCH_H - 0.042, td - 0.02), (sx, (I_TISCH_H - 0.042) * 0.5, tz), "holz"))
    t.append(kasten("boden", (tb - 0.10, 0.03, td - 0.06), (tx, 0.22, tz), "holz"))
    t.append(kasten("rueckwand", (tb - 0.10, 0.28, 0.02), (tx, 0.55, z0 + 0.03), "holz"))
    # im Regal: stehende Buecher und ein Karton
    for i, (dx, mat, h) in enumerate(((-0.28, "rot", 0.22), (-0.235, "hellblau", 0.25), (-0.19, "gelb", 0.20), (-0.145, "gruen_hell", 0.23))):
        t.append(kasten("buch", (0.04, h, 0.18), (tx + dx, 0.235 + h * 0.5 + 0.001, tz + 0.02), mat, (0, 0, -8 if i == 3 else 0), rund=(0.006, 1)))
    t.append(kasten("karton", (0.26, 0.17, 0.26), (tx + 0.17, 0.235 + 0.086, tz + 0.03), "karton", (0, 6, 0)))
    # Pinnwand auf Staender
    p = I_PINN
    mitte_y = p["unten"] + p["h"] * 0.5
    t.append(kasten("rahmen", (p["b"], p["h"], 0.03), (p["x"], mitte_y, p["z"]), "holz_dunkel", rund=(0.012, 2)))
    t.append(kasten("kork", (p["b"] - 0.08, p["h"] - 0.08, 0.012), (p["x"], mitte_y, p["z"] + 0.015 + 0.006 - 0.001), "kork", rund=(0, 0)))
    for dx in (-p["b"] * 0.5 + 0.07, p["b"] * 0.5 - 0.07):
        t.append(kasten("bein", (0.04, p["unten"] + p["h"] - 0.05, 0.04), (p["x"] + dx, (p["unten"] + p["h"] - 0.05) * 0.5, p["z"] - 0.04), "holz_dunkel"))
        t.append(kasten("fuss", (0.05, 0.035, 0.30), (p["x"] + dx, 0.0175, -0.90), "holz_dunkel"))
    # Hocker
    hx, hz = I_HOCKER
    t.append(zylinder("sitz", 0.17, 0.05, (hx, I_HOCKER_H - 0.025, hz), "orange", seiten=16, rund=(0.015, 2)))
    for i in range(4):
        w = math.radians(45 + 90 * i)
        oben = (hx + math.cos(w) * 0.10, I_HOCKER_H - 0.05, hz + math.sin(w) * 0.10)
        unten = (hx + math.cos(w) * 0.15, 0.0, hz + math.sin(w) * 0.15)
        t.append(stab("bein", oben, unten, 0.018, "holz_dunkel"))
    t.append(ring("strebe", 0.125, 0.012, (hx, 0.17, hz), "holz_dunkel", segmente=12, quer=4))
    return t


def _notizbuch_auf_hocker():
    hx, hz = I_HOCKER
    y = I_HOCKER_H + 0.003
    t = []
    t.append(kasten("umschlag", (0.30, 0.012, 0.22), (hx, y + 0.006, hz), "blau", (0, -12, 0), rund=(0.004, 1)))
    for s in (-1, 1):
        t.append(kasten("seite", (0.135, 0.008, 0.20), punkt((hx, y + 0.016, hz), (0, -12, 0), (s * 0.072, 0, 0)), "papier", (0, -12, s * -2.5), rund=(0, 0)))
    for k in range(3):
        t.append(kasten("zeile", (0.09, 0.002, 0.012), punkt((hx, y + 0.021, hz), (0, -12, 0), (-0.072, 0, -0.05 + k * 0.045)), "grau_mittel", (0, -12, 0), rund=(0, 0)))
    t.append(stab("stift", punkt((hx, y + 0.028, hz), (0, -12, 0), (0.03, 0, 0.07)), punkt((hx, y + 0.028, hz), (0, -12, 0), (0.12, 0, -0.06)), 0.009, "rot"))
    return t


def _zettel_an_pinnwand(liste):
    """liste: (x relativ zur Pinnwandmitte, y absolut, breite, hoehe, mat, drehung)"""
    t = []
    for dx, y, b, h, mat, rz in liste:
        t.append(zettel((I_PINN["x"] + dx, y, I_KORK_VORNE + 0.003), (0, 0, rz), (b, h), mat))
    return t


def intake_a1_0():
    """Lose Zettel auf dem Boden vor der Pinnwand, zwei zerknuellt, einer
    einsam angepinnt."""
    t = []
    for x, z, r, mat in ((-0.44, -0.48, 18, "papier"), (-0.14, -0.40, -25, "papier"), (-0.04, -0.56, 40, "creme"), (-0.30, -0.18, 70, "papier")):
        t.append(kasten("blatt", (0.22, 0.004, 0.29), (x, 0.004, z), mat, (0, r, 0), rund=(0, 0)))
    t.append(kugel("knaeuel", 0.05, (0.04, 0.052, -0.22), "papier", stufen=1))
    t.append(kugel("knaeuel", 0.045, (-0.58, 0.047, -0.26), "creme", stufen=1))
    t += _zettel_an_pinnwand([(0.12, 1.14, 0.20, 0.26, "papier", -6)])
    t.append(kugel("nadel", 0.014, (I_PINN["x"] + 0.11, 1.24, I_KORK_VORNE + 0.012), "rot", stufen=1))
    return t


def intake_a1_1():
    """Notizbuch mit Stift auf dem Hocker, drei ordentlich angepinnte Blaetter."""
    t = _notizbuch_auf_hocker()
    t += _zettel_an_pinnwand([(-0.22, 1.15, 0.20, 0.26, "papier", 4), (0.05, 1.18, 0.20, 0.26, "papier", -3), (0.25, 1.02, 0.14, 0.14, "gelb", 5)])
    for dx, y in ((-0.22, 1.26), (0.05, 1.29)):
        t.append(kugel("nadel", 0.014, (I_PINN["x"] + dx, y, I_KORK_VORNE + 0.012), "rot", stufen=1))
    return t


def _pinnwand_voll():
    farben = ("gelb", "rosa", "hellblau", "gruen_hell", "orange")
    liste = []
    i = 0
    for r, y in enumerate((1.27, 1.14, 1.01, 0.89)):
        for s in range(5):
            if (r, s) in ((3, 4), (0, 0)):
                continue
            dx = -0.30 + s * 0.15 + (0.02 if r % 2 else 0.0)
            rz = ((i * 37) % 13) - 6
            liste.append((dx, y, 0.11, 0.11, farben[(i * 3 + r) % 5], rz))
            i += 1
    t = _zettel_an_pinnwand(liste)
    # roter Faden verbindet drei Ideen
    kx = I_PINN["x"]
    zf = I_KORK_VORNE + 0.009
    t.append(stab("faden", (kx - 0.29, 1.27, zf), (kx + 0.02, 1.14, zf), 0.005, "rot", seiten=4))
    t.append(stab("faden", (kx + 0.02, 1.14, zf), (kx + 0.30, 1.26, zf), 0.005, "rot", seiten=4))
    return t


def intake_a1_2():
    """Pinnwand voll bunter Klebezettel, Notizbuch bleibt."""
    return _notizbuch_auf_hocker() + _pinnwand_voll()


I_WB_POS = (-0.84, 0.0, -0.36)
I_WB_DREH = 58.0


def intake_a1_3():
    """Zusaetzlich ein Whiteboard auf Staffelei mit bunten Skizzen."""
    t = intake_a1_2()
    d = (0, I_WB_DREH, 0)
    p = I_WB_POS
    b, h, unten = 0.70, 0.52, 0.72
    my = unten + h * 0.5
    t.append(kasten("wb_rahmen", (b, h, 0.03), punkt(p, d, (0, my, 0)), "grau_hell", d, rund=(0.01, 1)))
    t.append(kasten("wb_flaeche", (b - 0.05, h - 0.05, 0.004), punkt(p, d, (0, my, 0.0155)), "papier", d, rund=(0, 0)))
    zf = 0.0195
    # Skizzen: Kasten -> Pfeil -> Kasten, darunter eine Kurve aus drei Strichen
    for (u, v, bb, hh, mat) in ((-0.20, 0.10, 0.16, 0.12, "hellblau"), (0.14, 0.12, 0.18, 0.10, "gruen_hell"),
                                (-0.03, 0.12, 0.10, 0.018, "rot"), (0.22, -0.13, 0.10, 0.08, "gelb")):
        t.append(kasten("skizze", (bb, hh, 0.003), punkt(p, d, (u, my + v, zf)), mat, d, rund=(0, 0)))
    for k, (u0, v0, u1, v1) in enumerate(((-0.28, -0.18, -0.16, -0.10), (-0.16, -0.10, -0.04, -0.15), (-0.04, -0.15, 0.10, -0.04))):
        t.append(stab("kurve", punkt(p, d, (u0, my + v0, zf)), punkt(p, d, (u1, my + v1, zf)), 0.008, "blau", seiten=4))
    # Staffelei: zwei Beine vorn, eins hinten, Ablage mit Stiften
    for s in (-1, 1):
        t.append(stab("bein", punkt(p, d, (s * 0.26, my + h * 0.45, -0.03)), punkt(p, d, (s * 0.30, 0.0, 0.10)), 0.016, "holz"))
    t.append(stab("bein_hinten", punkt(p, d, (0, my + h * 0.4, -0.04)), punkt(p, d, (0, 0.0, -0.26)), 0.016, "holz"))
    t.append(kasten("ablage", (b * 0.9, 0.025, 0.07), punkt(p, d, (0, unten - 0.012, 0.045)), "holz", d))
    for k, mat in enumerate(("rot", "blau", "gruen_hell")):
        t.append(kasten("marker", (0.11, 0.02, 0.02), punkt(p, d, (-0.12 + k * 0.08, unten + 0.011, 0.05)), mat, d, rund=(0, 0)))
    return t


# Platz 2: rechte Tischhaelfte
I_A2 = (0.87, I_AUF, -0.84)


def _tablet_auf_staender(pos, breite, hoehe, alt, neigung=22.0):
    t = []
    d = (-neigung, 0, 0)
    rahmen = "grau_dunkel" if alt else "schwarz"
    # Klappstaender: Grundplatte + schraege Stuetze
    t.append(kasten("staender", (breite * 0.5, 0.012, 0.13), (pos[0], pos[1] + 0.006, pos[2]), "grau_mittel", rund=(0.004, 1)))
    t.append(kasten("stuetze", (breite * 0.4, 0.14, 0.012), punkt((pos[0], pos[1] + 0.07, pos[2] - 0.045), (-40, 0, 0), (0, 0, 0)), "grau_mittel", (-40, 0, 0), rund=(0, 0)))
    m = (pos[0], pos[1] + 0.02 + hoehe * 0.5 * math.cos(math.radians(neigung)), pos[2] + 0.02)
    dicke = 0.028 if alt else 0.014
    t.append(kasten("tablet", (breite, hoehe, dicke), m, rahmen, d, rund=(0.008, 1)))
    rand = 0.035 if alt else 0.015
    t += schirm_inhalt(m, d, breite - rand * 2, hoehe - rand * 2, "balken", tiefe=dicke * 0.5 + 0.001)
    return t


def intake_a2_1():
    """Altes, dickes Tablet mit breitem Rand auf einem Klappstaender."""
    t = _tablet_auf_staender(I_A2, 0.26, 0.19, alt=True)
    # Sprung im Glas (zwei dunkle Striche)
    return t


def _tastatur(pos, dreh, breite, tiefe, mat="grau_dunkel", tasten="grau_hell"):
    t = [kasten("tastatur", (breite, 0.018, tiefe), (pos[0], pos[1] + 0.009, pos[2]), mat, dreh, rund=(0.006, 1))]
    for r in range(3):
        t.append(kasten("reihe", (breite * 0.86, 0.004, tiefe * 0.18), punkt((pos[0], pos[1] + 0.02, pos[2]), dreh, (0, 0, -tiefe * 0.28 + r * tiefe * 0.28)), tasten, dreh, rund=(0, 0)))
    return t


def intake_a2_2():
    """Neues schlankes Tablet, dazu eine Tastatur davor."""
    x, y, z = I_A2
    t = _tablet_auf_staender((x, y, z - 0.06), 0.30, 0.21, alt=False)
    t += _tastatur((x, y, z + 0.13), (0, -4, 0), 0.30, 0.10)
    return t


def intake_a2_3():
    """Kleiner Monitor mit Kurven, davor Tastatur, Tablet liegt daneben."""
    x, y, z = I_A2
    t = monitor((x, y, z - 0.06), (0, -8, 0), 0.36, 0.25, "kurve", fuss_hoehe=0.10)
    t += _tastatur((x - 0.02, y, z + 0.14), (0, -4, 0), 0.30, 0.10)
    return t


# Platz 3: linke Tischhaelfte, Lichterkette oben an der Pinnwand, Stehlampe
I_A3_TASSE = (0.44, I_AUF, -0.72)
I_A3_PFLANZE = (0.43, I_AUF, -0.93)


def intake_a3_0():
    """Eine leere, kalte Tasse."""
    return tasse(I_A3_TASSE, "grau_hell", voll=False)


def intake_a3_1():
    """Voller Kaffeebecher und eine Minipflanze."""
    t = tasse(I_A3_TASSE, "orange", hoehe=0.12, radius=0.05)
    t += pflanze(I_A3_PFLANZE, 0.8)
    return t


def _lichterkette():
    t = []
    p = I_PINN
    y0 = p["unten"] + p["h"] + 0.03
    x0, x1 = p["x"] - p["b"] * 0.5 - 0.02, p["x"] + p["b"] * 0.5 + 0.02
    zf = p["z"] + 0.06
    n = 6
    punkte = []
    for i in range(n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u
        durchhang = 0.035 * math.sin(math.pi * ((u * 3.0) % 1.0))
        punkte.append((x, y0 - durchhang, zf))
    for a, b in zip(punkte, punkte[1:]):
        t.append(stab("kette_kabel", a, b, 0.004, "gruen_hell", seiten=3))
    farben = ("licht_warm", "orange", "licht_warm", "rosa")
    for i, (x, y, z) in enumerate(punkte[1:-1]):
        t.append(kugel("kette_birne", 0.024, (x, y - 0.026, z), "licht_warm" if i % 2 == 0 else "orange", stufen=1, skala=(1, 1.3, 1)))
    return t


def _box():
    x, y, z = 0.56, I_AUF, -0.74
    t = [kasten("box", (0.14, 0.075, 0.07), (x, y + 0.0375, z), "lila", (0, -20, 0), rund=(0.02, 1))]
    t.append(kasten("gitter", (0.10, 0.05, 0.004), punkt((x, y + 0.0375, z), (0, -20, 0), (0, 0, 0.036)), "grau_dunkel", (0, -20, 0), rund=(0, 0)))
    return t


def intake_a3_2():
    """Dazu eine Bluetooth-Box und eine Lichterkette ueber der Pinnwand."""
    t = intake_a3_1()
    t += _box()
    t += _lichterkette()
    return t


def intake_a3_3():
    """Dazu eine Stehlampe mit grosser leuchtender Gluehbirne."""
    t = intake_a3_2()
    # Bogenlampe zwischen Pinnwand und Hocker, die Birne haengt ueber der
    # Tischkante -- vorn genug, dass sie nichts auf der Platte verdeckt.
    fx, fz = 0.17, -0.40
    bx, bz = 0.36, -0.50
    t.append(zylinder("lampe_fuss", 0.10, 0.03, (fx, 0.015, fz), "grau_dunkel", seiten=8, rund=(0, 0)))
    t.append(stab("lampe_stange", (fx, 0.03, fz), (fx, 1.36, fz), 0.016, "grau_dunkel", seiten=6))
    t.append(stab("lampe_arm", (fx, 1.36, fz), (bx, 1.44, bz), 0.014, "grau_dunkel", seiten=6))
    t.append(stab("lampe_kabel", (bx, 1.44, bz), (bx, 1.33, bz), 0.005, "schwarz", seiten=4))
    t.append(zylinder("lampe_fassung", 0.028, 0.05, (bx, 1.31, bz), "holz_dunkel", seiten=8, rund=(0, 0)))
    t.append(zylinder("lampe_hals", 0.03, 0.03, (bx, 1.27, bz), "licht_warm", seiten=8, radius_oben=0.026, rund=(0, 0)))
    t.append(kugel("lampe_birne", 0.10, (bx, 1.17, bz), "licht_warm", stufen=2, skala=(1, 1.1, 1)))
    return t


INTAKE = {
    "basis": intake_basis,
    "plaetze": {
        1: {0: intake_a1_0, 1: intake_a1_1, 2: intake_a1_2, 3: intake_a1_3},
        2: {1: intake_a2_1, 2: intake_a2_2, 3: intake_a2_3},
        3: {0: intake_a3_0, 1: intake_a3_1, 2: intake_a3_2, 3: intake_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),        # x0, x1, z0, z1
    "wand_z": -1.10,
    "wand_x": None,
    "figur": None,
}

# =============================================================================
# Station 3: station_processing -- Schreibtisch
# Vorderseite +z, Ruecken an halbhoher Wand (z ~ -1,1). Platte 1,6 x 0,7 auf
# 0,74 m. Hintere Tischhaelfte = Platz 1 (Bildschirm), vordere Tischhaelfte
# plus rechts neben dem Tisch = Platz 2 (Rechner), vor dem Tisch = Platz 3
# (Stuhl). Sitzflaeche aller Stuhlstufen: y = 0,48, Mitte (0 | +0,05).
# =============================================================================

P_TISCH_H = 0.74
P_AUF = P_TISCH_H + 0.002
P_TISCH_Z = -0.70          # Mitte der Platte, Tiefe 0,7 -> z -1,05 .. -0,35
P_SITZ = (0.0, 0.48, 0.05)
P_PAD = (0.40, P_AUF, -0.52)


def processing_basis():
    t = []
    t.append(kasten("platte", (1.60, 0.04, 0.70), (0.0, P_TISCH_H - 0.02, P_TISCH_Z), "holz_hell", rund=(0.014, 2)))
    # links ein Rollcontainer-artiger Schubladenblock, rechts zwei Beine
    t.append(kasten("block", (0.40, 0.69, 0.62), (-0.57, 0.345, -0.72), "holz"))
    for i in range(3):
        y = 0.12 + i * 0.215
        t.append(kasten("schublade", (0.35, 0.18, 0.02), (-0.57, y, -0.40), "holz_hell", rund=(0.006, 1)))
        t.append(kasten("griff", (0.10, 0.018, 0.018), (-0.57, y + 0.04, -0.38), "grau_dunkel", rund=(0, 0)))
    for z in (-0.99, -0.41):
        t.append(kasten("bein", (0.05, 0.70, 0.05), (0.74, 0.35, z), "holz_dunkel"))
    t.append(kasten("strebe", (0.04, 0.05, 0.54), (0.74, 0.12, -0.70), "holz_dunkel"))
    t.append(kasten("blende", (1.06, 0.12, 0.02), (0.20, 0.64, -1.00), "holz", rund=(0.006, 1)))
    # Mauspad
    t.append(kasten("mauspad", (0.30, 0.004, 0.24), (P_PAD[0], P_PAD[1] + 0.002, P_PAD[2]), "blau", rund=(0, 0)))
    # Kabel ueber die Hinterkante zur Steckdosenleiste am Boden
    t.append(stab("kabel", (0.32, P_TISCH_H + 0.004, -0.98), (0.32, P_TISCH_H + 0.004, -1.035), 0.007, "schwarz", seiten=4))
    t.append(stab("kabel", (0.32, P_TISCH_H + 0.004, -1.035), (0.30, 0.012, -1.04), 0.007, "schwarz", seiten=4))
    t.append(stab("kabel", (0.30, 0.012, -1.04), (0.10, 0.012, -0.92), 0.007, "schwarz", seiten=4))
    t.append(kasten("leiste", (0.30, 0.045, 0.07), (-0.05, 0.023, -0.90), "papier", (0, 12, 0), rund=(0.01, 1)))
    t.append(kasten("schalter", (0.03, 0.01, 0.03), punkt((-0.05, 0.05, -0.90), (0, 12, 0), (0.11, 0, 0)), "rot", (0, 12, 0), rund=(0, 0)))
    # Papierkorb mit Knaeuel
    t.append(zylinder("korb", 0.12, 0.26, (-0.66, 0.13, -0.16), "grau_hell", seiten=10, radius_oben=0.14, rund=(0, 0)))
    t.append(zylinder("korb_innen", 0.12, 0.004, (-0.66, 0.24, -0.16), "grau_dunkel", seiten=10, rund=(0, 0)))
    t.append(kugel("knaeuel", 0.05, (-0.63, 0.285, -0.14), "papier", stufen=1))
    return t


def processing_a1_1():
    """Kleiner Monitor auf einem Buecherstapel."""
    t, h = buecher((0.08, P_AUF, -0.92), (0, 3, 0), 3, breite=0.34, tiefe=0.22, dicke=0.05)
    t += monitor((0.08, P_AUF + h + 0.002, -0.88), (0, -4, 0), 0.44, 0.29, "balken", fuss_hoehe=0.06)
    return t


def processing_a1_2():
    """Grosser Monitor auf Standfuss."""
    return monitor((0.02, P_AUF, -0.86), (0, 0, 0), 0.72, 0.43, "video", fuss_hoehe=0.13)


def processing_a1_3():
    """Zwei Monitore an einem Schwenkarm, leicht nach innen gedreht."""
    t = []
    sx, sz = 0.0, -0.99
    t.append(kasten("klemme", (0.14, 0.03, 0.10), (sx, P_AUF + 0.015, sz), "grau_dunkel", rund=(0.008, 1)))
    t.append(stab("saeule", (sx, P_AUF + 0.03, sz), (sx, 1.24, sz), 0.022, "grau_hell", seiten=8))
    for s in (-1, 1):
        mx = s * 0.335
        t.append(stab("arm", (sx, 1.20, sz), (mx * 0.75, 1.21, -0.93), 0.016, "grau_hell", seiten=6))
        t += monitor((mx, 1.02, -0.88), (0, -s * 12, 0), 0.64, 0.38, "video" if s < 0 else "kurve", fuss=False)
    return t


def _mb_laptop_alt(pos, dreh):
    """Alter, dicker Laptop mit Klebeband an Deckel und Ecke."""
    t = laptop(pos, dreh, breite=0.42, tiefe=0.29, winkel=112, mat="beige_alt", inhalt="balken", dicke=0.036)
    # Klebeband: ueber die linke obere Deckelecke und quer ueber die
    # Handballenauflage -- silbern, damit es nicht wie ein Zettel aussieht.
    d2 = verkette(dreh, (-22, 0, 0))
    deckel_mitte = punkt(pos, dreh, (0, 0.036 + 0.125, -0.145 - 0.05))
    t.append(kasten("klebeband", (0.05, 0.14, 0.022), punkt(deckel_mitte, d2, (-0.17, 0.08, 0.0)), "grau_hell", verkette(d2, (0, 0, 45)), rund=(0, 0)))
    t.append(kasten("klebeband", (0.05, 0.14, 0.022), punkt(deckel_mitte, d2, (0.18, -0.07, 0.0)), "grau_hell", verkette(d2, (0, 0, -30)), rund=(0, 0)))
    t.append(kasten("klebeband", (0.18, 0.006, 0.045), punkt(pos, dreh, (0.10, 0.039, 0.10)), "grau_hell", verkette(dreh, (0, 25, 0)), rund=(0, 0)))
    return t


def processing_a2_0():
    """Alter verbeulter Laptop, mit Klebeband geflickt."""
    return _mb_laptop_alt((-0.05, P_AUF, -0.52), (0, 6, 0))


def processing_a2_1():
    """Laptop auf einem Kuehlpad mit blau leuchtender Vorderkante."""
    t = []
    x, z = -0.05, -0.55
    d = (8, 4, 0)
    mitte = (x, P_AUF + 0.045, z)
    t.append(kasten("kuehlpad", (0.48, 0.03, 0.36), mitte, "grau_dunkel", d, rund=(0.008, 1)))
    t.append(kasten("steg", (0.44, 0.05, 0.03), punkt((x, P_AUF + 0.025, z), (0, 4, 0), (0, 0, -0.15)), "grau_dunkel", (0, 4, 0), rund=(0.006, 1)))
    t.append(kasten("led", (0.40, 0.012, 0.006), punkt(mitte, d, (0, 0, 0.181)), "led_blau", d, rund=(0, 0)))
    t.append(ring("luefter", 0.08, 0.012, punkt(mitte, d, (0.12, 0.0, 0.04)), "led_blau", d, segmente=10, quer=4))
    t += laptop(punkt(mitte, d, (0, 0.016, 0.0)), d, breite=0.40, tiefe=0.28, winkel=108, mat="grau_mittel", inhalt="video")
    return t


def _maus(pos, mat="grau_dunkel", akzent=None):
    t = [kugel("maus", 0.04, (pos[0], pos[1] + 0.023, pos[2]), mat, stufen=1, skala=(0.75, 0.5, 1.15))]
    if akzent:
        t.append(kasten("maus_led", (0.012, 0.006, 0.03), (pos[0], pos[1] + 0.041, pos[2] - 0.015), akzent, rund=(0, 0)))
    return t


def processing_a2_2():
    """Neuer, schlanker Laptop links, externe Tastatur und Maus."""
    t = laptop((-0.47, P_AUF, -0.60), (0, 20, 0), breite=0.36, tiefe=0.25, winkel=106, mat="grau_hell", inhalt="balken", dicke=0.016)
    t += _tastatur((0.0, P_AUF, -0.50), (0, 0, 0), 0.44, 0.14, mat="papier", tasten="grau_hell")
    t += _maus((P_PAD[0], P_AUF + 0.004, P_PAD[2]), "papier")
    return t


def processing_a2_3():
    """PC-Tower mit RGB neben dem Tisch, mechanische Tastatur, Gaming-Maus."""
    t = []
    tx, tz = 0.95, -0.78
    t.append(kasten("tower", (0.22, 0.50, 0.46), (tx, 0.25 + 0.004, tz), "schwarz", rund=(0.014, 1)))
    t.append(kasten("fuesse", (0.18, 0.004, 0.40), (tx, 0.002, tz), "grau_dunkel", rund=(0, 0)))
    t.append(kasten("rgb_front", (0.022, 0.40, 0.004), (tx - 0.06, 0.26, tz + 0.232), "rgb_cyan", rund=(0, 0)))
    t.append(kasten("glas", (0.004, 0.36, 0.34), (tx + 0.112, 0.27, tz), "grau_dunkel", rund=(0, 0)))
    for k, y in enumerate((0.36, 0.18)):
        t.append(ring("luefter", 0.065, 0.013, (tx + 0.118, y, tz + 0.06), "rgb_magenta" if k == 0 else "rgb_cyan", (0, 0, 90), segmente=12, quer=4))
    t.append(kasten("knopf", (0.03, 0.01, 0.01), (tx + 0.05, 0.47, tz + 0.232), "led_blau", rund=(0, 0)))
    # mechanische Tastatur mit Unterglow
    kx, kz = 0.0, -0.50
    t.append(kasten("tastatur", (0.46, 0.03, 0.16), (kx, P_AUF + 0.019, kz), "schwarz", rund=(0.008, 1)))
    t.append(kasten("glow", (0.44, 0.006, 0.14), (kx, P_AUF + 0.003, kz), "rgb_magenta", rund=(0, 0)))
    for r, mat in enumerate(("creme", "creme", "orange", "creme")):
        t.append(kasten("tastenreihe", (0.40 if r < 3 else 0.22, 0.016, 0.028), (kx - (0.0 if r < 3 else 0.06), P_AUF + 0.042, kz - 0.05 + r * 0.034), mat, rund=(0, 0)))
    t += _maus((P_PAD[0], P_AUF + 0.004, P_PAD[2]), "schwarz", akzent="rgb_cyan")
    return t


def _sternfuss(x, z, radius, mat="grau_dunkel", rollen=True):
    t = []
    for i in range(5):
        w = math.radians(90 + i * 72)
        ende = (x + math.cos(w) * radius, 0.05 if rollen else 0.022, z + math.sin(w) * radius)
        t.append(stab("fussarm", (x, 0.08, z), ende, 0.02, mat, seiten=5))
        if rollen:
            t.append(kasten("rolle", (0.04, 0.04, 0.04), (ende[0], 0.02, ende[2]), "schwarz", rund=(0, 0)))
    return t


def processing_a3_0():
    """Roter Plastikhocker mit vier gespreizten Beinen."""
    x, y, z = P_SITZ
    t = [kasten("sitz", (0.34, 0.035, 0.34), (x, y - 0.0175, z), "rot", rund=(0.012, 1))]
    for sx in (-1, 1):
        for sz in (-1, 1):
            t.append(stab("bein", (x + sx * 0.12, y - 0.03, z + sz * 0.12), (x + sx * 0.16, 0.0, z + sz * 0.16), 0.022, "rot", seiten=4))
    t.append(kasten("strebe", (0.30, 0.02, 0.02), (x, 0.16, z + 0.145), "rot", rund=(0, 0)))
    t.append(kasten("strebe", (0.30, 0.02, 0.02), (x, 0.16, z - 0.145), "rot", rund=(0, 0)))
    t.append(kasten("loch", (0.10, 0.004, 0.03), (x, y + 0.001, z), "grau_dunkel", rund=(0, 0)))
    return t


def processing_a3_1():
    """Einfacher Buerostuhl: Sitz, Rueckenlehne, Gasfeder, Sternfuss."""
    x, y, z = P_SITZ
    t = [kasten("sitz", (0.44, 0.07, 0.44), (x, y - 0.035, z), "grau_mittel", rund=(0.02, 1))]
    t.append(stab("feder", (x, 0.08, z), (x, y - 0.07, z), 0.025, "grau_hell", seiten=6))
    t.append(stab("traeger", (x, y - 0.05, z + 0.20), (x, y + 0.12, z + 0.25), 0.018, "grau_dunkel", seiten=4))
    t.append(kasten("lehne", (0.40, 0.30, 0.05), (x, y + 0.26, z + 0.25), "grau_mittel", (-6, 0, 0), rund=(0.02, 1)))
    t += _sternfuss(x, z, 0.26)
    return t


def processing_a3_2():
    """Guter Buerostuhl: hohe Netzlehne, Armlehnen, Lordosenstuetze."""
    x, y, z = P_SITZ
    t = [kasten("sitz", (0.50, 0.08, 0.48), (x, y - 0.04, z), "grau_dunkel", rund=(0.025, 2))]
    t.append(stab("feder", (x, 0.08, z), (x, y - 0.08, z), 0.028, "grau_hell", seiten=6))
    t.append(stab("traeger", (x, y - 0.05, z + 0.22), (x, y + 0.10, z + 0.29), 0.02, "grau_hell", seiten=4))
    t.append(kasten("lehne_rahmen", (0.48, 0.54, 0.04), (x, y + 0.36, z + 0.30), "schwarz", (-8, 0, 0), rund=(0.02, 2)))
    t.append(kasten("lehne_netz", (0.40, 0.44, 0.006), punkt((x, y + 0.36, z + 0.30), (-8, 0, 0), (0, 0, -0.022)), "grau_mittel", (-8, 0, 0), rund=(0, 0)))
    t.append(kasten("lehne_netz_hinten", (0.40, 0.44, 0.006), punkt((x, y + 0.36, z + 0.30), (-8, 0, 0), (0, 0, 0.022)), "grau_mittel", (-8, 0, 0), rund=(0, 0)))
    t.append(kasten("lordose", (0.36, 0.07, 0.03), punkt((x, y + 0.24, z + 0.30), (-8, 0, 0), (0, 0, -0.035)), "blau", (-8, 0, 0), rund=(0.01, 1)))
    for s in (-1, 1):
        t.append(stab("armstuetze", (x + s * 0.23, y - 0.02, z + 0.10), (x + s * 0.24, y + 0.19, z + 0.06), 0.018, "grau_hell", seiten=4))
        t.append(kasten("armauflage", (0.07, 0.03, 0.26), (x + s * 0.24, y + 0.205, z + 0.02), "schwarz", rund=(0.01, 1)))
    t += _sternfuss(x, z, 0.29, mat="grau_hell")
    return t


def processing_a3_3():
    """Gaming-Stuhl: hohe Schalenlehne mit Seitenwangen, Kopfkissen,
    orange Zierstreifen."""
    x, y, z = P_SITZ
    t = [kasten("sitz", (0.52, 0.09, 0.50), (x, y - 0.045, z), "schwarz", rund=(0.03, 2))]
    for s in (-1, 1):
        t.append(kasten("sitzwange", (0.05, 0.05, 0.46), (x + s * 0.25, y + 0.02, z + 0.01), "orange", rund=(0, 0)))
    t.append(stab("feder", (x, 0.08, z), (x, y - 0.09, z), 0.03, "grau_dunkel", seiten=6))
    lehne = (x, y + 0.40, z + 0.31)
    d = (-10, 0, 0)
    t.append(kasten("lehne", (0.50, 0.74, 0.09), lehne, "schwarz", d, rund=(0.035, 2)))
    for s in (-1, 1):
        t.append(kasten("wange", (0.07, 0.50, 0.10), punkt(lehne, d, (s * 0.25, -0.06, -0.04)), "orange", verkette(d, (0, s * 18, 0)), rund=(0.02, 1)))
    t.append(kasten("streifen", (0.10, 0.60, 0.006), punkt(lehne, d, (0, -0.03, -0.047)), "orange", d, rund=(0, 0)))
    t.append(kasten("streifen_hinten", (0.10, 0.60, 0.006), punkt(lehne, d, (0, -0.03, 0.047)), "orange", d, rund=(0, 0)))
    t.append(kasten("kopfkissen", (0.30, 0.12, 0.06), punkt(lehne, d, (0, 0.26, -0.08)), "grau_dunkel", d, rund=(0.025, 1)))
    for s in (-1, 1):
        t.append(stab("armstuetze", (x + s * 0.25, y - 0.02, z + 0.12), (x + s * 0.26, y + 0.20, z + 0.08), 0.02, "grau_dunkel", seiten=4))
        t.append(kasten("armauflage", (0.08, 0.035, 0.28), (x + s * 0.26, y + 0.215, z + 0.03), "schwarz", rund=(0.012, 1)))
    t += _sternfuss(x, z, 0.31, mat="schwarz", rollen=False)
    return t


PROCESSING = {
    "basis": processing_basis,
    "plaetze": {
        1: {1: processing_a1_1, 2: processing_a1_2, 3: processing_a1_3},
        2: {0: processing_a2_0, 1: processing_a2_1, 2: processing_a2_2, 3: processing_a2_3},
        3: {0: processing_a3_0, 1: processing_a3_1, 2: processing_a3_2, 3: processing_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.10,
    "figur": [("sitz", P_SITZ)],
}

# =============================================================================
# Station 2: station_buffer -- Aufnahme-Set
# Blickachse +x: Stoffwand bei x ~ -1,0 (Vorderseite +x), Darsteller-Platz
# bei (-0,5 | 0) bleibt frei, Kamera rechts bei (+0,7 | +0,2) zeigt nach -x.
# Licht bei (+0,4 | -0,8), Ton bei (-0,1 | +0,8).
# =============================================================================

B_TEPPICH = (0.05, 0.0, 0.0)
B_AUF = 0.017                   # Oberkante Teppich + Luft
B_DARSTELLER = (-0.5, 0.0)
B_KAMERA = (0.70, 0.20)
B_LICHT = (0.42, -0.74)
B_TON = (-0.10, 0.80)


def gier_zu(von, nach):
    """Gierwinkel (Grad), damit lokal +z von `von` nach `nach` zeigt."""
    return math.degrees(math.atan2(nach[0] - von[0], nach[1] - von[1]))


def stativ(x, z, kopf_hoehe, spreizung, dicke=0.014, mat="grau_dunkel", saeule_mat="grau_hell", y0=B_AUF):
    """Dreibein: Beine vom Kopf (etwas unterhalb) schraeg zum Boden, Saeule
    bis zum Kopf. Gibt die Teile zurueck."""
    t = []
    ansatz = kopf_hoehe * 0.72
    for i in range(3):
        w = math.radians(30 + 120 * i)
        t.append(stab("bein", (x, ansatz, z), (x + math.cos(w) * spreizung, y0 + dicke, z + math.sin(w) * spreizung), dicke, mat, seiten=4))
    t.append(stab("saeule", (x, ansatz - 0.04, z), (x, kopf_hoehe, z), dicke * 1.3, saeule_mat, seiten=6))
    return t


def buffer_basis():
    t = []
    tx, _, tz = B_TEPPICH
    t.append(zylinder("teppich", 0.95, 0.012, (tx, 0.006, tz), "teppich", seiten=24, rund=(0, 0)))
    t.append(zylinder("teppich_ring", 0.80, 0.003, (tx, 0.0135, tz), "creme", seiten=24, rund=(0, 0)))
    t.append(zylinder("teppich_innen", 0.74, 0.003, (tx, 0.0136, tz), "teppich", seiten=24, rund=(0, 0)))
    # Markierung des Darsteller-Platzes: gelbes Klebeband-Kreuz
    dx, dz = B_DARSTELLER
    for w in (45, -45):
        t.append(kasten("kreuz", (0.30, 0.003, 0.05), (dx, 0.0165, dz), "gelb", (0, w, 0), rund=(0, 0)))
    # Hintergrund: zwei Staender, Querstange, Stoff in vier Falten
    wx = -1.00
    for s in (-1, 1):
        z = s * 0.74
        t.append(stab("staender", (wx, 0.03, z), (wx, 1.78, z), 0.016, "grau_dunkel", seiten=6))
        t.append(kasten("fuss", (0.28, 0.03, 0.04), (-0.94, 0.015, z), "grau_dunkel", rund=(0, 0)))
        t.append(kasten("fuss_quer", (0.04, 0.03, 0.26), (wx, 0.015, z - s * 0.08), "grau_dunkel", rund=(0, 0)))
    t.append(stab("querstange", (wx, 1.76, -0.76), (wx, 1.76, 0.76), 0.014, "grau_hell", seiten=6))
    for i in range(4):
        z = -0.525 + i * 0.35
        t.append(kasten("stoff", (0.02, 1.66, 0.365), (wx + 0.035 + (0.012 if i % 2 else 0.0), 0.90, z), "stoffwand", (0, 7 if i % 2 else -7, 0), rund=(0, 0)))
    return t


# --- Platz 1: Kamera -----------------------------------------------------------

def buffer_a1_0():
    """Handy hochkant auf einem Karton mit Buecherstapel."""
    x, z = B_KAMERA
    t = [kasten("karton", (0.36, 0.36, 0.36), (x, 0.18 + B_AUF, z), "karton", (0, 10, 0), rund=(0.015, 1))]
    t.append(kasten("klebestreifen", (0.37, 0.004, 0.06), (x, 0.36 + B_AUF + 0.002, z), "beige_alt", (0, 10, 0), rund=(0, 0)))
    b, h = buecher((x, 0.364 + B_AUF, z), (0, 4, 0), 3, breite=0.26, tiefe=0.20, dicke=0.05)
    t += b
    y = 0.364 + B_AUF + h
    t += handy((x + 0.02, y + 0.10, z), (-8, 90, 0), "video", gross=1.15)
    t.append(tasse((x - 0.07, y, z + 0.0), "creme", hoehe=0.08, radius=0.035, voll=False)[0])
    return t


def buffer_a1_1():
    """Handy quer auf einem kleinen Stativ."""
    x, z = B_KAMERA
    kopf = 0.86
    t = stativ(x, z, kopf, 0.20, dicke=0.011)
    t.append(kasten("kopf", (0.05, 0.04, 0.05), (x, kopf + 0.02, z), "grau_dunkel", rund=(0, 0)))
    t.append(kasten("halter", (0.02, 0.05, 0.20), (x, kopf + 0.07, z), "grau_dunkel", rund=(0, 0)))
    t += handy((x + 0.02, kopf + 0.08, z), (0, 90, 90), "video", gross=1.1)
    return t


def buffer_a1_2():
    """Grosses Stativ, Handy im Gimbal mit orangem Griff."""
    x, z = B_KAMERA
    kopf = 1.18
    t = stativ(x, z, kopf, 0.30, dicke=0.016)
    t.append(kasten("kopf", (0.08, 0.05, 0.08), (x, kopf + 0.025, z), "schwarz", rund=(0.01, 1)))
    t.append(zylinder("griff", 0.03, 0.16, (x, kopf + 0.13, z), "orange", seiten=8, rund=(0, 0)))
    t.append(kasten("motor", (0.06, 0.06, 0.06), (x, kopf + 0.24, z), "schwarz", rund=(0.012, 1)))
    t.append(kasten("arm", (0.03, 0.03, 0.16), (x, kopf + 0.24, z - 0.10), "schwarz", rund=(0, 0)))
    t.append(kasten("arm2", (0.03, 0.14, 0.03), (x, kopf + 0.30, z - 0.17), "schwarz", rund=(0, 0)))
    t += handy((x + 0.02, kopf + 0.37, z - 0.06), (0, 90, 90), "video", gross=1.2)
    t.append(kasten("led", (0.004, 0.012, 0.012), (x + 0.032, kopf + 0.16, z), "led_gruen", rund=(0, 0)))
    return t


def buffer_a1_3():
    """Systemkamera auf stabilem Stativ, oben ein Kontrollmonitor."""
    x, z = B_KAMERA
    kopf = 1.18
    t = stativ(x, z, kopf, 0.34, dicke=0.02, mat="schwarz", saeule_mat="grau_dunkel")
    for i in range(3):                 # Spinne zwischen den Beinen
        w = math.radians(30 + 120 * i)
        t.append(stab("spinne", (x, 0.45, z), (x + math.cos(w) * 0.21, 0.45 - 0.0, z + math.sin(w) * 0.21), 0.009, "grau_dunkel", seiten=4))
    t.append(kasten("neiger", (0.10, 0.06, 0.10), (x, kopf + 0.03, z), "grau_dunkel", rund=(0.012, 1)))
    t.append(stab("schwenkgriff", (x + 0.04, kopf + 0.04, z), (x + 0.30, kopf - 0.02, z + 0.10), 0.012, "schwarz", seiten=4))
    body = (x, kopf + 0.14, z)
    t.append(kasten("gehaeuse", (0.14, 0.13, 0.20), body, "schwarz", rund=(0.02, 2)))
    t.append(kasten("griffwulst", (0.06, 0.12, 0.05), (x - 0.01, kopf + 0.14, z + 0.10), "grau_dunkel", rund=(0.015, 1)))
    t.append(zylinder("objektiv", 0.058, 0.16, (x - 0.15, kopf + 0.135, z), "grau_dunkel", seiten=12, dreh=(0, 0, 90), rund=(0.008, 1)))
    t.append(zylinder("fokusring", 0.062, 0.03, (x - 0.12, kopf + 0.135, z), "orange", seiten=12, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(zylinder("linse", 0.045, 0.004, (x - 0.232, kopf + 0.135, z), "schirm_blau", seiten=12, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(kasten("display", (0.004, 0.08, 0.13), (x + 0.072, kopf + 0.14, z), "schirm", rund=(0, 0)))
    t.append(kasten("rec", (0.02, 0.01, 0.02), (x + 0.03, kopf + 0.21, z + 0.07), "rot", rund=(0, 0)))
    # Kontrollmonitor auf Gelenkarm, zur Bedienerseite (+x) gedreht
    t.append(stab("gelenk", (x, kopf + 0.205, z - 0.04), (x + 0.02, kopf + 0.30, z - 0.04), 0.01, "grau_dunkel", seiten=4))
    mon = (x + 0.03, kopf + 0.37, z - 0.04)
    d = (-12, 90, 0)
    t.append(kasten("monitor", (0.24, 0.16, 0.03), mon, "schwarz", d, rund=(0.01, 1)))
    t += schirm_inhalt(mon, d, 0.21, 0.13, "video", tiefe=0.016)
    return t


# --- Platz 2: Licht ------------------------------------------------------------

def buffer_a2_0():
    """Miras Schreibtischlampe, verkehrt herum: der Schirm steht auf dem
    Boden und leuchtet in den Teppich, der Fuss zeigt in die Luft."""
    x, z = B_LICHT
    y = B_AUF
    d = (0, gier_zu(B_LICHT, B_DARSTELLER), 0)
    t = [zylinder("schirm", 0.13, 0.15, (x, y + 0.075, z), "hellblau", seiten=12, radius_oben=0.05, rund=(0, 0))]
    t.append(zylinder("glut", 0.125, 0.003, (x, y + 0.0015, z), "licht_warm", seiten=12, rund=(0, 0)))
    gelenk = punkt((x, y, z), d, (0.0, 0.40, 0.10))
    t.append(stab("arm_unten", (x, y + 0.15, z), gelenk, 0.013, "grau_hell", seiten=6))
    oben = punkt((x, y, z), d, (0.0, 0.58, -0.06))
    t.append(stab("arm_oben", gelenk, oben, 0.013, "grau_hell", seiten=6))
    t.append(kugel("gelenk", 0.025, gelenk, "grau_dunkel", stufen=1))
    t.append(zylinder("fuss", 0.10, 0.03, (oben[0], oben[1] + 0.015, oben[2]), "hellblau", seiten=12, rund=(0, 0)))
    t.append(kasten("schalter", (0.03, 0.015, 0.02), (oben[0], oben[1] + 0.037, oben[2]), "grau_dunkel", rund=(0, 0)))
    return t


def _ringlicht(radius, hoehe, spreizung, dicke):
    x, z = B_LICHT
    gier = gier_zu(B_LICHT, B_DARSTELLER) - 32.0     # etwas zur Kamera gedreht: bleibt aus der Isometrie rund
    t = stativ(x, z, hoehe - radius - 0.02, spreizung, dicke=dicke)
    mitte = (x, hoehe, z)
    t.append(stab("buegel", (x, hoehe - radius - 0.03, z), (x, hoehe - radius + 0.01, z), dicke * 1.2, "grau_dunkel", seiten=6))
    t.append(ring("ring", radius, radius * 0.13, mitte, "licht_weiss", (90, gier, 0), segmente=18, quer=5))
    t.append(ring("ring_ruecken", radius, radius * 0.09, punkt(mitte, (0, gier, 0), (0, 0, -radius * 0.08)), "grau_dunkel", (90, gier, 0), segmente=18, quer=4))
    return t, mitte, gier


def buffer_a2_1():
    """Kleines Ringlicht auf leichtem Lampenstativ."""
    t, mitte, gier = _ringlicht(0.17, 1.12, 0.22, 0.011)
    return t


def buffer_a2_2():
    """Grosses Ringlicht mit Handyhalter in der Mitte."""
    t, mitte, gier = _ringlicht(0.31, 1.38, 0.30, 0.015)
    t.append(stab("halter", (mitte[0], mitte[1] - 0.31, mitte[2]), mitte, 0.01, "grau_dunkel", seiten=4))
    t.append(kasten("klammer", (0.12, 0.04, 0.03), mitte, "grau_dunkel", (0, gier, 0), rund=(0, 0)))
    return t


def _softbox(pos_boden, hoehe, groesse):
    x, z = pos_boden
    gier = gier_zu(pos_boden, B_DARSTELLER)
    t = stativ(x, z, hoehe - 0.10, 0.26, dicke=0.014)
    kopf = (x, hoehe, z)
    d = (-90 + 12, gier, 0)          # Pyramide liegt: Spitze nach hinten, Diffusor zum Darsteller, leicht nach unten
    t.append(keil("softbox", (groesse, groesse * 0.62, groesse * 0.72), punkt(kopf, (0, gier, 0), (0, 0, -groesse * 0.1)), "schwarz", d))
    front = punkt(kopf, (12, gier, 0), (0, 0, groesse * 0.21))
    t.append(kasten("diffusor", (groesse * 0.94, groesse * 0.68, 0.012), front, "licht_weiss", (12, gier, 0), rund=(0, 0)))
    t.append(stab("halter", (x, hoehe - 0.10, z), punkt(kopf, (0, gier, 0), (0, 0, -groesse * 0.36)), 0.014, "grau_dunkel", seiten=4))
    return t


def buffer_a2_3():
    """Zwei Softboxen, beide auf den Darsteller gerichtet."""
    return _softbox((0.14, -0.76), 1.36, 0.50) + _softbox((0.82, -0.44), 1.24, 0.46)


# --- Platz 3: Ton --------------------------------------------------------------

def buffer_a3_0():
    """Kopfhoerer, achtlos auf dem Teppich."""
    x, z = B_TON
    y = B_AUF
    d = (0, 25, 0)
    t = []
    t.append(ring("buegel", 0.115, 0.016, punkt((x, y, z), d, (0, 0.017, 0.02)), "schwarz", (0, 25, 0), segmente=10, quer=4, anteil=0.5))
    for s in (-1, 1):
        t.append(zylinder("muschel", 0.055, 0.04, punkt((x, y, z), d, (s * 0.115, 0.03, 0.02)), "grau_dunkel", seiten=10, dreh=(0, 25, 0), rund=(0, 0)))
        t.append(zylinder("polster", 0.045, 0.012, punkt((x, y, z), d, (s * 0.115, 0.056, 0.02)), "orange", seiten=10, dreh=(0, 25, 0), rund=(0, 0)))
    t.append(stab("kabel", punkt((x, y, z), d, (0.115, 0.01, 0.07)), punkt((x, y, z), d, (0.26, 0.004, 0.12)), 0.005, "schwarz", seiten=3))
    return t


def buffer_a3_1():
    """Ansteckmikro auf einem Ministativ, daneben der Funkempfaenger."""
    x, z = B_TON
    t = stativ(x, z, 0.28, 0.10, dicke=0.008)
    t.append(stab("schwanenhals", (x, 0.28, z), (x - 0.06, 0.40, z - 0.05), 0.007, "grau_dunkel", seiten=4))
    t.append(kugel("windschutz", 0.035, (x - 0.07, 0.43, z - 0.06), "schwarz", stufen=1))
    t.append(kasten("sender", (0.10, 0.14, 0.04), (x + 0.20, B_AUF + 0.07, z + 0.05), "schwarz", (0, 20, 0), rund=(0.01, 1)))
    t.append(kasten("led", (0.02, 0.012, 0.004), punkt((x + 0.20, B_AUF + 0.11, z + 0.05), (0, 20, 0), (0.02, 0, 0.021)), "rot", (0, 20, 0), rund=(0, 0)))
    t.append(stab("antenne", (x + 0.19, B_AUF + 0.14, z + 0.05), (x + 0.19, B_AUF + 0.24, z + 0.05), 0.005, "grau_dunkel", seiten=3))
    t.append(stab("kabel", (x - 0.07, 0.40, z - 0.06), (x + 0.17, B_AUF + 0.05, z + 0.06), 0.004, "schwarz", seiten=3))
    return t


def _galgen(spitze, hinten, hoehe):
    """Galgenstativ am Tonplatz. spitze/hinten: (x, y, z) der Armenden."""
    x, z = B_TON
    t = stativ(x, z, hoehe, 0.26, dicke=0.015, mat="schwarz", saeule_mat="grau_dunkel")
    gelenk = (x, hoehe, z)
    t.append(kugel("gelenk", 0.03, gelenk, "grau_dunkel", stufen=1))
    t.append(stab("arm", gelenk, spitze, 0.012, "grau_hell", seiten=6))
    t.append(stab("arm_hinten", gelenk, hinten, 0.012, "grau_hell", seiten=6))
    t.append(zylinder("gegengewicht", 0.045, 0.10, hinten, "schwarz", seiten=8, rund=(0, 0)))
    return t


def buffer_a3_2():
    """Richtmikrofon mit Fell am Galgen ueber dem Darsteller-Platz."""
    spitze = (-0.34, 1.88, 0.36)
    t = _galgen(spitze, (0.02, 1.54, 1.02), 1.58)
    t.append(stab("abhaenger", spitze, (-0.34, 1.80, 0.36), 0.008, "grau_dunkel", seiten=4))
    t.append(kasten("fell", (0.09, 0.09, 0.34), (-0.36, 1.76, 0.30), "grau_mittel", (-25, 0, 0), rund=(0.03, 1)))
    return t


def buffer_a3_3():
    """Studiomikrofon mit Spinne und Popschutz am Galgen, dazu ein
    Akustikpaneel auf Staender."""
    spitze = (-0.36, 1.92, 0.36)
    t = _galgen(spitze, (0.02, 1.56, 1.02), 1.60)
    mic = (-0.40, 1.73, 0.33)
    t.append(stab("abhaenger", spitze, (mic[0], mic[1] + 0.12, mic[2]), 0.008, "grau_dunkel", seiten=4))
    t.append(ring("spinne", 0.07, 0.008, (mic[0], mic[1] + 0.10, mic[2]), "grau_dunkel", segmente=10, quer=3))
    t.append(zylinder("korb", 0.05, 0.20, mic, "grau_hell", seiten=10, rund=(0, 0)))
    t.append(kugel("kappe", 0.05, (mic[0], mic[1] - 0.10, mic[2]), "grau_hell", stufen=1))
    t.append(zylinder("ring", 0.054, 0.03, (mic[0], mic[1] + 0.02, mic[2]), "orange", seiten=10, rund=(0, 0)))
    t.append(ring("popschutz", 0.08, 0.006, (mic[0] - 0.02, mic[1] - 0.04, mic[2] - 0.13), "schwarz", (90, -30, 0), segmente=10, quer=3))
    t.append(zylinder("popschutz_stoff", 0.075, 0.003, (mic[0] - 0.02, mic[1] - 0.04, mic[2] - 0.13), "grau_dunkel", seiten=10, dreh=(90, -30, 0), rund=(0, 0)))
    # Akustikpaneel: Schaumstoff mit Noppenraster, schaut nach +x
    px, pz = -0.66, 0.82
    t.append(kasten("paneel", (0.06, 0.80, 0.50), (px, 0.62, pz), "grau_dunkel", rund=(0.015, 1)))
    for r in range(4):
        for s in range(3):
            t.append(kasten("noppe", (0.03, 0.16, 0.13), (px + 0.045, 0.34 + r * 0.185, pz - 0.155 + s * 0.155), "lila" if (r + s) % 2 else "grau_mittel", rund=(0, 0)))
    for s in (-1, 1):
        t.append(stab("paneel_bein", (px - 0.01, 0.24, pz + s * 0.18), (px - 0.10, B_AUF + 0.012, pz + s * 0.20), 0.012, "schwarz", seiten=4))
        t.append(stab("paneel_bein", (px - 0.01, 0.24, pz + s * 0.18), (px + 0.06, B_AUF + 0.012, pz + s * 0.20), 0.012, "schwarz", seiten=4))
    return t


BUFFER = {
    "basis": buffer_basis,
    "plaetze": {
        1: {0: buffer_a1_0, 1: buffer_a1_1, 2: buffer_a1_2, 3: buffer_a1_3},
        2: {0: buffer_a2_0, 1: buffer_a2_1, 2: buffer_a2_2, 3: buffer_a2_3},
        3: {0: buffer_a3_0, 1: buffer_a3_1, 2: buffer_a3_2, 3: buffer_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (B_DARSTELLER[0], 0.0, B_DARSTELLER[1]))],
    "frei": [(B_DARSTELLER[0], B_DARSTELLER[1], 0.28, 1.55)],     # x, z, Radius, Hoehe
}

# =============================================================================
# Station 4: station_transport -- Upload-Regal im Flur
# Vorderseite +z, Ruecken an halbhoher Wand (z ~ -0,6). Nur 1,8 x 1,4.
# Sideboard 1,2 x 0,45, 0,8 hoch. Oberseite dreigeteilt: links Platz 1
# (Netz, dazu der Boden links neben dem Regal), Mitte Platz 3 (Reichweite),
# rechts Platz 2 (Planung).
# =============================================================================

T_H = 0.80
T_AUF = T_H + 0.002
T_Z = -0.33                     # Mitte der Tiefe: z -0,555 .. -0,105
T_NETZ = (-0.41, T_AUF, -0.36)
T_REICH = (0.0, T_AUF, -0.33)
T_PLAN = (0.42, T_AUF, -0.33)


def transport_basis():
    t = []
    b, d = 1.20, 0.45
    t.append(kasten("platte", (b, 0.035, d), (0.0, T_H - 0.0175, T_Z), "holz_hell", rund=(0.012, 2)))
    t.append(kasten("korpus_boden", (b - 0.04, 0.03, d - 0.04), (0.0, 0.115, T_Z), "holz"))
    for sx in (-b * 0.5 + 0.02, 0.0, b * 0.5 - 0.02):
        t.append(kasten("seite", (0.035, T_H - 0.13, d - 0.03), (sx, 0.10 + (T_H - 0.13) * 0.5 - 0.0, T_Z), "holz"))
    t.append(kasten("rueckwand", (b - 0.06, T_H - 0.14, 0.02), (0.0, 0.10 + (T_H - 0.14) * 0.5, T_Z - d * 0.5 + 0.02), "holz_dunkel", rund=(0, 0)))
    t.append(kasten("zwischenboden", (b * 0.5 - 0.05, 0.025, d - 0.06), (-0.30, 0.44, T_Z), "holz"))
    # links offen: Korb unten, Buecher oben
    t.append(kasten("korb", (0.40, 0.22, 0.30), (-0.30, 0.13 + 0.112, T_Z + 0.02), "karton", rund=(0.02, 1)))
    t.append(kasten("korb_rand", (0.41, 0.03, 0.31), (-0.30, 0.13 + 0.215, T_Z + 0.02), "holz_hell", rund=(0.01, 1)))
    for i, (dx, mat, h) in enumerate(((-0.46, "hellblau", 0.24), (-0.42, "rosa", 0.21), (-0.38, "gelb", 0.25), (-0.30, "gruen_hell", 0.20))):
        t.append(kasten("buch", (0.035, h, 0.20), (dx, 0.4525 + h * 0.5 + 0.001, T_Z + 0.03), mat, (0, 0, -14 if i == 3 else 0), rund=(0.006, 1)))
    # rechts eine Tuer mit Griff
    t.append(kasten("tuer", (b * 0.5 - 0.05, T_H - 0.16, 0.025), (0.30, 0.10 + (T_H - 0.16) * 0.5 + 0.01, T_Z + d * 0.5 - 0.01), "holz_hell", rund=(0.008, 1)))
    t.append(kasten("griff", (0.02, 0.12, 0.02), (0.08, 0.48, T_Z + d * 0.5 + 0.012), "grau_dunkel", rund=(0, 0)))
    # Beine
    for sx in (-0.54, 0.54):
        for sz in (T_Z - 0.17, T_Z + 0.17):
            t.append(zylinder("bein", 0.022, 0.10, (sx, 0.05, sz), "holz_dunkel", seiten=6, radius_oben=0.03, rund=(0, 0)))
    return t


# --- Platz 1: Netz -------------------------------------------------------------

def _router(pos, breite, tiefe, mat, antennen, led_mat="led_gruen", leds=1, dreh=0.0):
    x, y, z = pos
    d = (0, dreh, 0)
    t = [kasten("router", (breite, 0.05, tiefe), (x, y + 0.025, z), mat, d, rund=(0.012, 1))]
    for i in range(leds):
        t.append(kasten("led", (0.018, 0.008, 0.006), punkt((x, y + 0.03, z), d, (-breite * 0.3 + i * 0.045, 0, tiefe * 0.5 + 0.002)), led_mat, d, rund=(0, 0)))
    for u, neig in antennen:
        fuss = punkt((x, y + 0.05, z), d, (u, 0, -tiefe * 0.35))
        spitze = punkt((x, y + 0.05, z), d, (u + math.sin(math.radians(neig)) * 0.25, 0.25 * math.cos(math.radians(neig)), -tiefe * 0.35 - 0.02))
        t.append(stab("antenne", fuss, spitze, 0.011, "schwarz" if mat != "beige_alt" else "grau_mittel", seiten=5))
    return t


def transport_a1_0():
    """Alter vergilbter Router mit einer schiefen Antenne und einer LED."""
    return _router(T_NETZ, 0.28, 0.19, "beige_alt", [(0.09, 24)], leds=1, dreh=-8)


def transport_a1_1():
    """Schwarzer Router mit drei Antennen und LED-Reihe."""
    return _router(T_NETZ, 0.34, 0.21, "schwarz", [(-0.13, -14), (0.0, 0), (0.13, 14)], led_mat="led_blau", leds=5)


def _mesh(pos, hoehe=0.27, radius=0.085):
    x, y, z = pos
    t = [zylinder("mesh", radius, hoehe, (x, y + hoehe * 0.5, z), "papier", seiten=12, radius_oben=radius * 0.85, rund=(0.012, 1))]
    t.append(zylinder("mesh_ring", radius * 0.86, 0.012, (x, y + hoehe + 0.007, z), "led_blau", seiten=12, rund=(0, 0)))
    return t


def _repeater():
    x, z = -0.80, 0.02
    t = [kasten("repeater", (0.12, 0.18, 0.09), (x, 0.09, z), "papier", (0, 20, 0), rund=(0.02, 1))]
    t.append(kasten("led", (0.016, 0.016, 0.004), punkt((x, 0.13, z), (0, 20, 0), (0, 0, 0.047)), "led_blau", (0, 20, 0), rund=(0, 0)))
    for s in (-1, 1):
        t.append(stab("antenne", punkt((x, 0.18, z), (0, 20, 0), (s * 0.04, 0, -0.02)), punkt((x, 0.32, z), (0, 20, 0), (s * 0.07, 0, -0.03)), 0.009, "papier", seiten=4))
    return t


def transport_a1_2():
    """Mesh-Router auf dem Regal, Repeater am Boden daneben."""
    x, y, z = T_NETZ
    return _mesh((x - 0.08, y, z - 0.04)) + _mesh((x + 0.09, y, z + 0.10), hoehe=0.16, radius=0.065) + _repeater()


def transport_a1_3():
    """Dazu ein Switch mit Leuchtdioden, und ein blaues Netzwerkkabel laeuft
    am Regal herunter und am Boden entlang."""
    x, y, z = T_NETZ
    t = _mesh((x - 0.07, y, z - 0.07)) + _repeater()
    sw = (x + 0.02, y, z + 0.16)
    t.append(kasten("switch", (0.30, 0.05, 0.12), (sw[0], y + 0.025, sw[2]), "grau_hell", rund=(0.01, 1)))
    for i in range(6):
        t.append(kasten("port", (0.03, 0.022, 0.004), (sw[0] - 0.11 + i * 0.044, y + 0.022, sw[2] + 0.061), "schwarz", rund=(0, 0)))
        t.append(kasten("led", (0.014, 0.008, 0.004), (sw[0] - 0.11 + i * 0.044, y + 0.041, sw[2] + 0.061), "led_gruen" if i != 4 else "orange", rund=(0, 0)))
    weg = [(sw[0] - 0.11, y + 0.02, sw[2] + 0.075), (-0.575, y + 0.014, sw[2] + 0.10), (-0.617, y + 0.012, sw[2] + 0.10),
           (-0.628, y - 0.04, sw[2] + 0.10), (-0.63, 0.012, -0.08), (-0.66, 0.009, 0.28), (-0.88, 0.009, 0.52)]
    for a, b in zip(weg, weg[1:]):
        t.append(stab("netzkabel", a, b, 0.009, "blau", seiten=5))
    for p in weg[1:-1]:
        t.append(kugel("knick", 0.009, p, "blau", stufen=1))
    t.append(kasten("stecker", (0.03, 0.02, 0.04), (weg[-1][0], 0.012, weg[-1][2]), "hellblau", (0, 35, 0), rund=(0, 0)))
    return t


# --- Platz 2: Planung ----------------------------------------------------------

def transport_a2_0():
    """Ein einzelner Notizzettel, daneben ein Kuli."""
    x, y, z = T_PLAN
    t = [kasten("zettel", (0.17, 0.004, 0.17), (x, y + 0.002, z + 0.06), "gelb", (0, 14, 0), rund=(0, 0))]
    for k in range(2):
        t.append(kasten("zeile", (0.09, 0.002, 0.012), punkt((x, y + 0.005, z + 0.06), (0, 14, 0), (0, 0, -0.03 + k * 0.04)), "grau_mittel", (0, 14, 0), rund=(0, 0)))
    t.append(stab("kuli", (x + 0.10, y + 0.009, z - 0.02), (x + 0.20, y + 0.009, z + 0.07), 0.008, "blau", seiten=5))
    return t


def transport_a2_1():
    """Aufstellkalender mit roter Kopfleiste und Tagesraster."""
    x, y, z = T_PLAN
    t = []
    d = (-14, -10, 0)
    mitte = (x, y + 0.125, z + 0.03)
    t.append(kasten("aufsteller", (0.32, 0.24, 0.012), mitte, "papier", d, rund=(0, 0)))
    t.append(kasten("aufsteller_hinten", (0.30, 0.24, 0.012), punkt((x, y + 0.12, z - 0.09), (0, -10, 0), (0, 0, 0)), "karton", (14, -10, 0), rund=(0, 0)))
    t.append(kasten("kopf", (0.32, 0.06, 0.004), punkt(mitte, d, (0, 0.09, 0.008)), "rot", d, rund=(0, 0)))
    t.append(stab("spirale", punkt(mitte, d, (-0.15, 0.12, 0.0)), punkt(mitte, d, (0.15, 0.12, 0.0)), 0.009, "grau_hell", seiten=4))
    for r in range(3):
        for s in range(5):
            mat = "orange" if (r, s) == (1, 2) else "grau_hell"
            t.append(kasten("tag", (0.04, 0.035, 0.003), punkt(mitte, d, (-0.116 + s * 0.058, 0.02 - r * 0.052, 0.008)), mat, d, rund=(0, 0)))
    return t


def transport_a2_2():
    """Tablet mit Wochenplan auf einem Staender."""
    x, y, z = T_PLAN
    return _tablet_auf_staender((x, y, z - 0.02), 0.34, 0.24, alt=False)[:3] + \
        schirm_inhalt((x, y + 0.02 + 0.12 * math.cos(math.radians(22)), z), (-22, 0, 0), 0.31, 0.21, "plan", tiefe=0.0095)


def transport_a2_3():
    """Kleiner Bildschirm mit Warteschlangen-Balken, Klebezettel am Rand."""
    x, y, z = T_PLAN
    t = monitor((x, y, z - 0.02), (0, -10, 0), 0.36, 0.25, "schlange", fuss_hoehe=0.09)
    t.append(kasten("klebezettel", (0.06, 0.06, 0.004), punkt((x, y + 0.108 + 0.25, z - 0.02), (0, -10, 0), (0.17, 0.0, 0.02)), "rosa", (0, -10, -12), rund=(0, 0)))
    return t


# --- Platz 3: Reichweite -------------------------------------------------------

def transport_a3_1():
    """Zweites Handy liegt am Ladekabel."""
    x, y, z = T_REICH
    t = handy((x, y + 0.01, z + 0.07), (-90, 20, 0), "chat", gross=1.25)
    weg = [(x - 0.03, y + 0.005, z - 0.05), (x - 0.09, y + 0.005, z - 0.10), (x - 0.06, y + 0.005, z - 0.17)]
    for a, b in zip(weg, weg[1:]):
        t.append(stab("ladekabel", a, b, 0.005, "papier", seiten=3))
    t.append(kasten("netzteil", (0.06, 0.05, 0.05), (x - 0.06, y + 0.025, z - 0.19), "papier", (0, 25, 0), rund=(0.01, 1)))
    return t


def _dock(x, y, z, handys, abstand=0.12, gier=0.0):
    t = [kasten("dock", (abstand * handys + 0.04, 0.05, 0.12), (x, y + 0.025, z), "holz", (0, gier, 0), rund=(0.015, 1))]
    inhalte = ("chat", "video", "balken")
    for i in range(handys):
        u = (i - (handys - 1) * 0.5) * abstand
        t += handy(punkt((x, y + 0.13, z), (0, gier, 0), (u, 0, 0.0)), (-12, gier, 0), inhalte[i % 3], gross=1.0)
        t.append(kasten("led", (0.02, 0.006, 0.004), punkt((x, y + 0.03, z), (0, gier, 0), (u, 0, 0.061)), "led_gruen", (0, gier, 0), rund=(0, 0)))
    return t


def transport_a3_2():
    """Ladestaender mit drei Handys."""
    x, y, z = T_REICH
    return _dock(x, y, z - 0.02, 3, abstand=0.115)


def transport_a3_3():
    """Kleine Serverbox mit Leuchtdioden, daneben ein Handy im Dock."""
    x, y, z = T_REICH
    t = []
    sx, sz = x - 0.075, z - 0.02
    t.append(kasten("server", (0.22, 0.33, 0.30), (sx, y + 0.165, sz), "grau_dunkel", rund=(0.02, 2)))
    for i in range(4):
        t.append(kasten("schacht", (0.18, 0.04, 0.006), (sx, y + 0.065 + i * 0.058, sz + 0.152), "schwarz", rund=(0, 0)))
        t.append(kasten("led", (0.016, 0.014, 0.004), (sx + 0.065, y + 0.065 + i * 0.058, sz + 0.156), "led_blau" if i % 2 else "led_gruen", rund=(0, 0)))
    t.append(kasten("leiste", (0.18, 0.022, 0.004), (sx, y + 0.29, sz + 0.152), "led_blau", rund=(0, 0)))
    t += _dock(x + 0.13, y, z + 0.02, 1, gier=-15)
    return t


TRANSPORT = {
    "basis": transport_basis,
    "plaetze": {
        1: {0: transport_a1_0, 1: transport_a1_1, 2: transport_a1_2, 3: transport_a1_3},
        2: {0: transport_a2_0, 1: transport_a2_1, 2: transport_a2_2, 3: transport_a2_3},
        3: {1: transport_a3_1, 2: transport_a3_2, 3: transport_a3_3},
    },
    "flaeche": (-0.9, 0.9, -0.7, 0.7),
    "wand_z": -0.60,
    "figur": None,
}

# =============================================================================
# Station 5: station_special -- Sofa-Ecke im Wohnzimmer
# Blickachse +x (dort in 4 m der Fernseher). Sofa bei (-0,5 | 0), Couchtisch
# bei (+0,5 | 0). Flaeche x -1,9 .. +0,9, z -1,4 .. +1,0.
# Couchtisch: +z-Haelfte = Platz 1, -z-Haelfte = Platz 3. Das +z-Sitzkissen
# bleibt frei (Sitzplatz der Figur). Platz 2 liegt auf der -z-Sofahaelfte
# und in den Ecken hinter/neben dem Sofa. Platz 3 m3 (Sessel) steht bei
# (+0,45 | -0,97), dem Sofa schraeg zugewandt.
# =============================================================================

S_AUF = 0.012                       # Oberkante Teppich + Luft
S_SITZ = (-0.40, 0.40, 0.34)        # Huefte der sitzenden Figur, Blick +x
S_TISCH_H = 0.42
S_TISCH = (0.50, 0.0)
S_BILDSCHIRM_GIER = -30.0           # Geraete auf dem Tisch: zum Sofa UND zur Kamera


def special_basis():
    t = []
    t.append(kasten("teppich", (2.02, 0.01, 1.90), (-0.13, 0.005, 0.0), "teppich_grau", rund=(0, 0)))
    sx = -0.50
    # Sofa: Sockel, zwei Sitzkissen, Lehne mit zwei Rueckenkissen, Armlehnen
    t.append(kasten("sockel", (0.86, 0.18, 1.40), (sx, 0.04 + S_AUF + 0.09, 0.0), "stoff_grau"))
    for z in (-0.345, 0.345):
        t.append(kasten("sitzkissen", (0.64, 0.17, 0.68), (-0.40, 0.31 + 0.005, z), "stoff_hell", rund=(0.04, 2)))
        t.append(kasten("rueckenkissen", (0.16, 0.36, 0.66), (-0.66, 0.58, z), "stoff_hell", (0, 0, 10), rund=(0.045, 2)))
    t.append(kasten("lehne", (0.20, 0.58, 1.40), (-0.85, 0.04 + S_AUF + 0.29, 0.0), "stoff_grau", rund=(0.04, 2)))
    for s in (-1, 1):
        t.append(kasten("armlehne", (0.90, 0.42, 0.17), (sx - 0.02, 0.04 + S_AUF + 0.21, s * 0.785), "stoff_grau", rund=(0.05, 2)))
    for bx in (-0.88, -0.14):
        for bz in (-0.78, 0.78):
            t.append(kasten("fuss", (0.05, 0.04, 0.05), (bx, S_AUF + 0.02, bz), "holz_dunkel", rund=(0, 0)))
    # Couchtisch mit Ablage
    tx, tz = S_TISCH
    t.append(kasten("tischplatte", (0.60, 0.04, 1.00), (tx, S_TISCH_H - 0.02, tz), "holz_hell", rund=(0.015, 2)))
    t.append(kasten("ablage", (0.50, 0.025, 0.86), (tx, 0.14, tz), "holz"))
    for dx in (-0.26, 0.26):
        for dz in (-0.44, 0.44):
            t.append(kasten("tischbein", (0.04, S_TISCH_H - 0.04 - S_AUF, 0.04), (tx + dx, S_AUF + (S_TISCH_H - 0.04 - S_AUF) * 0.5, tz + dz), "holz_dunkel", rund=(0, 0)))
    # auf der Ablage: Spielkonsolen-Controller und zwei Zeitschriften
    t.append(kasten("zeitschrift", (0.22, 0.012, 0.30), (tx - 0.05, 0.159, tz - 0.20), "hellblau", (0, 8, 0), rund=(0, 0)))
    t.append(kasten("zeitschrift", (0.22, 0.012, 0.30), (tx - 0.03, 0.171, tz - 0.18), "rosa", (0, -6, 0), rund=(0, 0)))
    t.append(kasten("controller", (0.14, 0.035, 0.09), (tx + 0.05, 0.172, tz + 0.22), "grau_dunkel", (0, 20, 0), rund=(0.015, 1)))
    return t


# --- Platz 1: Antworten ----------------------------------------------------------

def special_a1_0():
    """Das Handy liegt auf dem Sofa."""
    return handy((-0.17, 0.40 + 0.005 + 0.009, -0.02), (-90, 35, 0), "chat", gross=1.2)


def _handyhalter(x, z, gier):
    t = [kasten("halter_fuss", (0.10, 0.015, 0.10), (x, S_TISCH_H + 0.0095, z), "holz", (0, gier, 0), rund=(0, 0))]
    t.append(kasten("halter_lehne", (0.07, 0.14, 0.015), punkt((x, S_TISCH_H + 0.08, z), (0, gier, 0), (0, 0, -0.03)), "holz", (-18, gier, 0), rund=(0, 0)))
    t += handy(punkt((x, S_TISCH_H + 0.12, z), (0, gier, 0), (0, 0, -0.005)), (-18, gier, 0), "chat", gross=1.15)
    return t


def special_a1_1():
    """Handy auf einem Holzstaender auf dem Couchtisch."""
    return _handyhalter(0.52, 0.22, S_BILDSCHIRM_GIER)


def special_a1_2():
    """Tablet mit Tastatur-Huelle auf dem Couchtisch."""
    x, z = 0.54, 0.22
    g = S_BILDSCHIRM_GIER
    t = []
    tast = punkt((x, S_TISCH_H + 0.002, z), (0, g, 0), (0, 0, 0.08))
    t += _tastatur(tast, (0, g, 0), 0.32, 0.13, mat="grau_dunkel", tasten="grau_hell")
    t.append(kasten("huelle", (0.32, 0.20, 0.012), punkt((x, S_TISCH_H + 0.105, z), (0, g, 0), (0, 0, -0.03)), "orange", (-18, g, 0), rund=(0, 0)))
    mitte = punkt((x, S_TISCH_H + 0.108, z), (0, g, 0), (0, 0, -0.018))
    t += schirm_inhalt(mitte, (-18, g, 0), 0.28, 0.17, "chat", tiefe=0.0)
    return t


def special_a1_3():
    """Aufgeklappter Laptop, daneben das Handy."""
    x, z = 0.50, 0.24
    t = laptop((x, S_TISCH_H + 0.002, z), (0, S_BILDSCHIRM_GIER, 0), breite=0.40, tiefe=0.28, winkel=108, mat="grau_hell", inhalt="chat", dicke=0.02)
    t += tasse((0.72, S_TISCH_H + 0.002, 0.42), "rot", hoehe=0.10, radius=0.045)
    return t


# --- Platz 2: Gemuetlichkeit -----------------------------------------------------

def _kissen_decke():
    t = []
    t.append(kasten("kissen", (0.13, 0.30, 0.30), (-0.45, 0.58, -0.36), "orange", (0, -12, 12), rund=(0.05, 1)))
    t.append(kasten("kissen", (0.30, 0.28, 0.12), (-0.36, 0.59, -0.60), "senf", (-14, 8, 0), rund=(0.045, 1)))
    decke = (-0.26, 0.40 + 0.005 + 0.028, -0.42)
    t.append(kasten("decke", (0.26, 0.05, 0.36), decke, "rot", (0, 18, 0), rund=(0.02, 1)))
    for k in (-1, 1):
        t.append(kasten("streifen", (0.265, 0.052, 0.03), punkt(decke, (0, 18, 0), (0, 0, k * 0.11)), "creme", (0, 18, 0), rund=(0, 0)))
    return t


def special_a2_1():
    """Zwei Kissen und eine gefaltete Decke auf der freien Sofahaelfte."""
    return _kissen_decke()


def _stehlampe():
    x, z = -1.30, -0.95
    t = [zylinder("fuss", 0.16, 0.03, (x, S_AUF + 0.015, z), "grau_dunkel", seiten=10, rund=(0, 0))]
    t.append(stab("stange", (x, S_AUF + 0.03, z), (x, 1.42, z), 0.016, "holz_dunkel", seiten=6))
    t.append(zylinder("schirm", 0.21, 0.28, (x, 1.52, z), "creme", seiten=12, radius_oben=0.15, rund=(0, 0)))
    t.append(zylinder("glut", 0.195, 0.004, (x, 1.378, z), "licht_warm", seiten=10, rund=(0, 0)))
    return t


def special_a2_2():
    """Dazu eine warme Stehlampe hinter dem Sofa."""
    return _kissen_decke() + _stehlampe()


def special_a2_3():
    """Dazu eine grosse Pflanze und ein Beistelltisch mit Kerze."""
    t = _kissen_decke() + _stehlampe()
    t += grosse_pflanze((-1.42, S_AUF, 0.60))
    bx, bz = -0.46, -1.16
    t.append(zylinder("beistell_platte", 0.20, 0.03, (bx, 0.50, bz), "holz_hell", seiten=12, rund=(0, 0)))
    t.append(stab("beistell_bein", (bx, S_AUF + 0.02, bz), (bx, 0.485, bz), 0.02, "holz_dunkel", seiten=6))
    t.append(zylinder("beistell_fuss", 0.13, 0.02, (bx, S_AUF + 0.01, bz), "holz_dunkel", seiten=10, rund=(0, 0)))
    t.append(zylinder("kerzenglas", 0.05, 0.10, (bx + 0.02, 0.516 + 0.05, bz), "creme", seiten=8, rund=(0, 0)))
    t.append(kugel("flamme", 0.022, (bx + 0.02, 0.64, bz), "licht_warm", stufen=1, skala=(1, 1.6, 1)))
    return t


# --- Platz 3: Kontakt ------------------------------------------------------------

def _notizblock(x, z, gier):
    t = [kasten("block", (0.20, 0.014, 0.27), (x, S_TISCH_H + 0.009, z), "gelb", (0, gier, 0), rund=(0, 0))]
    for k in range(4):
        t.append(kasten("zeile", (0.14, 0.002, 0.012), punkt((x, S_TISCH_H + 0.017, z), (0, gier, 0), (0, 0, -0.08 + k * 0.05)), "grau_mittel", (0, gier, 0), rund=(0, 0)))
    t.append(stab("stift", punkt((x, S_TISCH_H + 0.024, z), (0, gier, 0), (0.12, 0, -0.10)), punkt((x, S_TISCH_H + 0.024, z), (0, gier, 0), (0.13, 0, 0.08)), 0.009, "blau", seiten=5))
    return t


def grosse_pflanze(pos):
    """Grosse Zimmerpflanze: Topf, Stamm, lange Blaetter, die schraeg nach
    oben und aussen stehen -- liest sich aus der Isometrie als Pflanze, nicht
    als gruener Klumpen."""
    x, y, z = pos
    t = [zylinder("topf", 0.15, 0.34, (x, y + 0.17, z), "topf", seiten=10, radius_oben=0.19, rund=(0, 0))]
    t.append(stab("stamm", (x, y + 0.34, z), (x, y + 0.95, z), 0.02, "holz_dunkel", seiten=5))
    blaetter = ((0, 0.52, 30), (72, 0.60, 42), (144, 0.55, 25), (216, 0.66, 38), (288, 0.58, 30),
                (36, 0.82, 55), (180, 0.86, 50), (300, 0.92, 60), (110, 0.95, 65))
    for i, (w, h, neig) in enumerate(blaetter):
        d = (-neig, w, 0)
        mitte = punkt((x, y + h, z), d, (0, 0, 0.19))
        t.append(kugel("blatt", 1.0, mitte, "pflanze" if i % 2 == 0 else "pflanze_dunkel", stufen=1, skala=(0.10, 0.025, 0.21), dreh=d))
    return t


def special_a3_1():
    """Notizblock mit Stift auf dem Couchtisch."""
    return _notizblock(0.46, -0.26, 10)


def _mappe_karten():
    t = [kasten("mappe", (0.27, 0.03, 0.36), (0.50, S_TISCH_H + 0.017, -0.28), "blau", (0, -6, 0), rund=(0.01, 1))]
    t.append(kasten("mappe_gummi", (0.275, 0.032, 0.012), (0.50, S_TISCH_H + 0.018, -0.16), "schwarz", (0, -6, 0), rund=(0, 0)))
    for i in range(4):
        t.append(kasten("karte", (0.10, 0.008, 0.06), (0.70, S_TISCH_H + 0.006 + i * 0.009, -0.07), "papier" if i < 3 else "orange", (0, 12 + i * 4, 0), rund=(0, 0)))
    return t


def special_a3_2():
    """Visitenkarten-Stapel und eine Mappe, der Block liegt obenauf."""
    t = _mappe_karten()
    blk = _notizblock(0.49, -0.29, 4)
    for o in blk:
        o.location.z += 0.033      # Blender-z = Godot-y: auf die Mappe
    return t + blk


def special_a3_3():
    """Ein Sessel fuer Gaeste, dem Sofa schraeg zugewandt. Mappe und
    Karten bleiben liegen."""
    t = _mappe_karten()
    x, z = 0.43, -0.93
    g = gier_zu((x, z), (-0.10, 0.0))
    d = (0, g, 0)
    m = (x, 0.0, z)
    t.append(kasten("sessel_sockel", (0.66, 0.20, 0.64), punkt(m, d, (0, S_AUF + 0.06 + 0.10, 0)), "stoffwand", d, rund=(0.04, 2)))
    t.append(kasten("sessel_kissen", (0.50, 0.12, 0.52), punkt(m, d, (0, S_AUF + 0.36 + 0.005, 0.04)), "stoff_hell", d, rund=(0.04, 2)))
    t.append(kasten("sessel_lehne", (0.66, 0.46, 0.16), punkt(m, d, (0, S_AUF + 0.06 + 0.43, -0.25)), "stoffwand", verkette(d, (-8, 0, 0)), rund=(0.05, 2)))
    for s in (-1, 1):
        t.append(kasten("sessel_arm", (0.10, 0.22, 0.56), punkt(m, d, (s * 0.29, S_AUF + 0.06 + 0.31, 0.02)), "stoffwand", d, rund=(0.04, 1)))
        for v in (-1, 1):
            t.append(stab("sessel_bein", punkt(m, d, (s * 0.26, S_AUF + 0.062, v * 0.24)), punkt(m, d, (s * 0.29, S_AUF + 0.02, v * 0.27)), 0.018, "holz_dunkel", seiten=5))
    return t


SPECIAL = {
    "basis": special_basis,
    "plaetze": {
        1: {0: special_a1_0, 1: special_a1_1, 2: special_a1_2, 3: special_a1_3},
        2: {1: special_a2_1, 2: special_a2_2, 3: special_a2_3},
        3: {1: special_a3_1, 2: special_a3_2, 3: special_a3_3},
    },
    "flaeche": (-1.9, 0.9, -1.4, 1.0),
    "wand_z": None,
    "figur": [("sitz", S_SITZ)],
    "frei": [(S_SITZ[0], S_SITZ[2], 0.18, 1.1)],
}

STATIONEN = {"intake": INTAKE, "buffer": BUFFER, "processing": PROCESSING,
             "transport": TRANSPORT, "special": SPECIAL}


# =============================================================================
# Bauen, Pruefen, Exportieren
# =============================================================================

def alles_loeschen():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def zusammenfuegen(teile, name):
    """Alle Teile zu EINEM Mesh (ein Knoten in Godot, je Material eine
    Oberflaeche). Modifikatoren (Bevel) werden dabei angewendet, die
    Transformation eingebacken -- der Ursprung ist danach exakt der
    Stationsursprung."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in teile:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = teile[0]
    bpy.ops.object.convert(target="MESH")
    if len(teile) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = name
    obj.data.name = name
    return obj


def dreiecke(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def dateiname(station, platz=None, stufe=None):
    if platz is None:
        return "station_%s_basis" % station
    return "station_%s_ausstattung_%d_%d" % (station, platz, stufe)


def alle_dateien(station):
    daten = STATIONEN[station]
    yield dateiname(station), daten["basis"], 0, 0
    for platz, stufen in daten["plaetze"].items():
        for stufe, bauen in stufen.items():
            yield dateiname(station, platz, stufe), bauen, platz, stufe


def exportieren(obj, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=pfad, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False,
    )


def grenzen(obj):
    """(xmin, xmax, ymin, ymax, zmin, zmax) in GODOT-Koordinaten."""
    xs = [v.co.x for v in obj.data.vertices]
    gz = [-v.co.y for v in obj.data.vertices]
    gy = [v.co.z for v in obj.data.vertices]
    return (min(xs), max(xs), min(gy), max(gy), min(gz), max(gz))


def teile_statistik(bauen):
    """Dreiecke je Teilname (nach Bevel) -- fuer die Budgetsuche."""
    alles_loeschen()
    teile = bauen()
    deps = bpy.context.evaluated_depsgraph_get()
    summe = {}
    for o in teile:
        me = o.evaluated_get(deps).to_mesh()
        summe[o.name.split(".")[0]] = summe.get(o.name.split(".")[0], 0) + sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(deps).to_mesh_clear()
    print("     " + ", ".join("%s %d" % kv for kv in sorted(summe.items(), key=lambda kv: -kv[1])))


def pruefe_station(station, objekte):
    """objekte: {(platz, stufe): obj}, Basis = (0, 0). Meldet Budget,
    Flaeche, Wand und Ueberschneidungen. Gibt Zahl der Probleme zurueck."""
    daten = STATIONEN[station]
    probleme = 0
    x0, x1, z0, z1 = daten["flaeche"]
    for (platz, stufe), obj in objekte.items():
        g = grenzen(obj)
        tol = 0.005
        if g[0] < x0 - tol or g[1] > x1 + tol or g[4] < z0 - tol or g[5] > z1 + tol or g[2] < -tol:
            print("  !! %s ausserhalb der Flaeche: x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f" % ((obj.name,) + g))
            probleme += 1
        if daten.get("wand_z") is not None and g[4] < daten["wand_z"] + 0.04:
            print("  !! %s beruehrt die Wand: z min %.3f" % (obj.name, g[4]))
            probleme += 1
        for fx, fz, fr, fh in (daten.get("frei") or []) if platz != 0 else []:
            # Figurenplatz: kein Eckpunkt ueber dem Boden (ab 3 cm) im Zylinder
            for v in obj.data.vertices:
                gx, gy, gz = v.co.x, v.co.z, -v.co.y
                if 0.03 < gy < fh and (gx - fx) ** 2 + (gz - fz) ** 2 < fr * fr:
                    print("  !! %s ragt in den freien Figurenplatz (%.2f | %.2f | %.2f)" % (obj.name, gx, gy, gz))
                    probleme += 1
                    break
        budget = BUDGET_BASIS if platz == 0 else BUDGET_AUSSTATTUNG
        if dreiecke(obj) > budget:
            print("  !! %s ueber Budget: %d > %d Dreiecke" % (obj.name, dreiecke(obj), budget))
            probleme += 1
    deps = bpy.context.evaluated_depsgraph_get()
    baeume = {k: BVHTree.FromObject(o, deps) for k, o in objekte.items()}
    schluessel = sorted(objekte.keys())
    for i, a in enumerate(schluessel):
        for b in schluessel[i + 1:]:
            if a[0] == b[0]:
                continue           # Stufen desselben Platzes sind nie gleichzeitig sichtbar
            paare = baeume[a].overlap(baeume[b])
            innen = _liegt_innen(objekte[a], baeume[b]) or _liegt_innen(objekte[b], baeume[a])
            if paare or innen:
                print("  !! Ueberschneidung %s <-> %s (%d Dreieckspaare%s)"
                      % (objekte[a].name, objekte[b].name, len(paare), ", enthalten" if innen else ""))
                probleme += 1
    return probleme


def _liegt_innen(obj, baum):
    """Ist der erste Eckpunkt von obj innerhalb des geschlossenen Koerpers
    `baum`? Strahl nach oben, Treffer zaehlen (ungerade = innen)."""
    if not obj.data.vertices:
        return False
    start = obj.data.vertices[0].co.copy()
    richtung = Vector((0.0013, 0.0007, 1.0)).normalized()
    treffer = 0
    p = start
    for _ in range(40):
        loc, _n, _i, _d = baum.ray_cast(p, richtung)
        if loc is None:
            break
        treffer += 1
        p = loc + richtung * 1e-4
    return treffer % 2 == 1


def baue_station(station, export=True):
    """Baut jede Datei einzeln (sauberer Export), dann alle zusammen fuer
    die Pruefung."""
    zeilen = []
    if export:
        for name, bauen, platz, stufe in alle_dateien(station):
            alles_loeschen()
            obj = zusammenfuegen(bauen(), name)
            pfad = os.path.join(AUSGABE, name + ".glb")
            exportieren(obj, pfad)
            zeilen.append((name, dreiecke(obj), os.path.getsize(pfad) / 1024.0))
    alles_loeschen()
    objekte = {}
    for name, bauen, platz, stufe in alle_dateien(station):
        objekte[(platz, stufe)] = zusammenfuegen(bauen(), name)
    if not export:
        zeilen = [(o.name, dreiecke(o), 0.0) for o in objekte.values()]
    for name, tri, kb in zeilen:
        print("  %-42s %5d Dreiecke  %6.1f KB" % (name, tri, kb))
    probleme = pruefe_station(station, objekte)
    for name, bauen, platz, stufe in alle_dateien(station):
        grenze = BUDGET_BASIS if platz == 0 else BUDGET_AUSSTATTUNG
        if dict((z[0], z[1]) for z in zeilen)[name] > grenze:
            print("   Teile von", name)
            teile_statistik(bauen)
    print("  -> %s: %d Probleme" % (station, probleme))
    return probleme


# =============================================================================
# Vorschau-Blaetter (nur fuer die Qualitaetsschleife, nichts davon wird exportiert)
# =============================================================================

VORSCHAU_FARBEN = {
    "v_boden": ("#D9A66B", 0.0),
    "v_wand": ("#F2E3CC", 0.0),
    "v_kappe": ("#C8925A", 0.0),
    "v_figur": ("#8A93A6", 0.0),
}
PALETTE.update(VORSCHAU_FARBEN)


def _kamera_iso(ziel, breite, aufloesung):
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new("kamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = breite
    cam_data.clip_end = 200.0
    cam = bpy.data.objects.new("kamera", cam_data)
    sc.collection.objects.link(cam)
    richtung = Vector((1.0, -1.0, 1.0)).normalized()
    cam.location = Vector(ziel) + richtung * 40.0
    cam.rotation_euler = (-richtung).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = aufloesung
    return cam


def licht_und_welt(transparent=False, hintergrund="#F4EEE6"):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 48
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    welt = bpy.data.worlds.get("welt") or bpy.data.worlds.new("welt")
    sc.world = welt
    welt.use_nodes = True
    bg = welt.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = farbe(hintergrund)
    bg.inputs["Strength"].default_value = 0.9
    for name, richtung, staerke, schatten in (("sonne", (-0.45, -0.8, -1.0), 2.6, True),
                                              ("fuell", (0.8, 0.3, -0.6), 0.6, False)):
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = staerke
        ld.angle = math.radians(12.0)
        ld.use_shadow = schatten
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = Vector(richtung).normalized().to_track_quat("-Z", "Y").to_euler()


def _verschieben(obj, versatz_blender):
    obj.matrix_world = Matrix.Translation(versatz_blender) @ obj.matrix_world


def _umgebung(station, versatz):
    daten = STATIONEN[station]
    x0, x1, z0, z1 = daten["flaeche"]
    t = []
    t.append(kasten("boden", (x1 - x0 + 0.6, 0.02, z1 - z0 + 0.6), ((x0 + x1) * 0.5, -0.011, (z0 + z1) * 0.5), "v_boden", rund=(0, 0)))
    if daten.get("wand_z") is not None:
        wz = daten["wand_z"] - 0.06
        t.append(kasten("wand", (x1 - x0 + 0.6, 1.2, 0.12), ((x0 + x1) * 0.5, 0.6, wz), "v_wand", rund=(0, 0)))
        t.append(kasten("kappe", (x1 - x0 + 0.62, 0.03, 0.14), ((x0 + x1) * 0.5, 1.215, wz), "v_kappe", rund=(0, 0)))
    for art, (fx, fy, fz) in daten.get("figur") or []:
        if art == "sitz":          # Huefte auf Sitzpunkt, Blick -z (oder gegeben)
            t.append(kugel("rumpf", 0.17, (fx, fy + 0.26, fz), "v_figur", stufen=2, skala=(1.0, 1.6, 0.8)))
            t.append(kugel("kopf", 0.17, (fx, fy + 0.66, fz), "v_figur", stufen=2))
        else:
            t.append(zylinder("beine", 0.12, 0.6, (fx, 0.3, fz), "v_figur", seiten=10, rund=(0, 0)))
            t.append(kugel("rumpf", 0.19, (fx, 0.85, fz), "v_figur", stufen=2, skala=(1.0, 1.5, 0.8)))
            t.append(kugel("kopf", 0.19, (fx, 1.35, fz), "v_figur", stufen=2))
    for o in t:
        _verschieben(o, versatz)
    return t


def _beschriftung(text, pos_blender, groesse=0.35):
    cu = bpy.data.curves.new("text", "FONT")
    cu.body = text
    cu.size = groesse
    cu.align_x = "CENTER"
    ob = bpy.data.objects.new("text", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos_blender
    ob.rotation_euler = Vector((1.0, -1.0, 1.0)).normalized().to_track_quat("Z", "Y").to_euler()
    ob.data.materials.append(material("schwarz"))
    return ob


def vorschau_station(station, klein=False):
    daten = STATIONEN[station]
    plaetze = daten["plaetze"]

    def stufe_oder_naechste(platz, m):
        verfuegbar = sorted(plaetze[platz].keys())
        if m in verfuegbar:
            return m
        kleiner = [s for s in verfuegbar if s <= m]
        return kleiner[-1] if kleiner else None

    varianten = [("alles m0", [0, 0, 0]), ("alles m1", [1, 1, 1]), ("alles m2", [2, 2, 2]),
                 ("alles m3", [3, 3, 3]), ("gemischt 3/1/2", [3, 1, 2]), ("gemischt 0/3/3", [0, 3, 3])]
    alles_loeschen()
    licht_und_welt()
    abstand = 3.6
    rechts = Vector((1.0, 1.0, 0.0)).normalized()
    x0, x1, z0, z1 = daten["flaeche"]
    mitte = Vector(((x0 + x1) * 0.5, -(z0 + z1) * 0.5, 0.5))
    for i, (titel, stufen) in enumerate(varianten):
        versatz = rechts * (i * abstand)
        teile = []
        for name, bauen, platz, stufe in alle_dateien(station):
            if platz == 0 or stufe == stufe_oder_naechste(platz, stufen[platz - 1]):
                if platz != 0 and stufe != stufen[platz - 1] and stufen[platz - 1] == 0:
                    continue
                obj = zusammenfuegen(bauen(), name)
                _verschieben(obj, versatz)
                teile.append(obj)
        _umgebung(station, versatz)
        unten = mitte + versatz + Vector((1.3, -1.3, -1.6))
        _beschriftung(titel, unten)
    ziel = mitte + rechts * (abstand * (len(varianten) - 1) * 0.5)
    # klein: etwa die Pixelgroesse, mit der eine Station im Spiel erscheint
    # (~190 px Breite je Station) -- Lesbarkeitsprobe der Stufen.
    _kamera_iso(ziel, abstand * len(varianten) + 0.4, (1140, 290) if klein else (3000, 760))
    pfad = os.path.join(VORSCHAU, "station_%s_iso%s.png" % (station, "_klein" if klein else ""))
    os.makedirs(VORSCHAU, exist_ok=True)
    bpy.context.scene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)
    print("  Vorschau:", pfad)


def vorschau_nah(station, stufen, titel):
    """Ein grosses Einzelbild (eine Kombination), fuer Detailkontrolle."""
    daten = STATIONEN[station]
    alles_loeschen()
    licht_und_welt()
    for name, bauen, platz, stufe in alle_dateien(station):
        if platz == 0 or stufe == stufen[platz - 1]:
            zusammenfuegen(bauen(), name)
    _umgebung(station, Vector((0, 0, 0)))
    x0, x1, z0, z1 = daten["flaeche"]
    _kamera_iso(((x0 + x1) * 0.5, -(z0 + z1) * 0.5, 0.55), max(x1 - x0, z1 - z0) * 1.45, (1100, 1000))
    pfad = os.path.join(VORSCHAU, "station_%s_nah_%s.png" % (station, titel))
    bpy.context.scene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)
    print("  Vorschau:", pfad)


def argumente():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    nur = None
    if "--nur" in args:
        nur = args[args.index("--nur") + 1].split(",")
    return {"vorschau": "--vorschau" in args, "nah": "--nah" in args, "klein": "--klein" in args,
            "kein_export": "--kein_export" in args, "nur": nur}


def main():
    a = argumente()
    print("")
    print("=== STATIONEN WG (TASK 075) ===")
    gesamt = 0
    for station in STATIONEN:
        if a["nur"] and station not in a["nur"]:
            continue
        print("--", station)
        gesamt += baue_station(station, export=not a["kein_export"])
        if a["vorschau"]:
            vorschau_station(station)
        if a["klein"]:
            vorschau_station(station, klein=True)
        if a["nah"]:
            vorschau_nah(station, [3, 3, 3], "m3")
            vorschau_nah(station, [0, 0, 0], "m0")
    print("")
    print("  Probleme gesamt: %d" % gesamt)


if __name__ == "__main__":
    main()
