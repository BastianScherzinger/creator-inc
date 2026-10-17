"""Erzeugt die fuenf Chibi-Figuren der WG-Welt als GLB -- mit getrennten Teilen.

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_figuren_wg.py
    blender --background --python art_source/scripts/build_figuren_wg.py -- --ohne-vorschau

Die Dateien sind nach ihrer SILHOUETTE benannt (Regel D3 / ADR-010):
figur_kapuze, figur_kapuze_sitzend, figur_dutt, figur_muetze, figur_cap.
Welche Silhouette welche Rolle spielt, steht in den Themendaten, nicht hier.

Aufbau jeder Datei (Godot-Sicht, Y oben, Figur schaut nach +Z):

    figur            Empty, Ursprung am Boden zwischen den Fuessen
    └─ koerper       Ursprung Huefte
       ├─ kopf       Ursprung Hals
       ├─ arm_l      Ursprung Schulter (Figur-links = +X)
       ├─ arm_r      Ursprung Schulter (Figur-rechts = -X)
       ├─ bein_l     Ursprung Hueftgelenk
       └─ bein_r     Ursprung Hueftgelenk

Alle Teile haben in Ruhe die Drehung NULL -- die Grundhaltung steckt im Mesh.
Godot kann deshalb direkt `rotation.x = sin(t) * amplitude` setzen.

Warum Arme und Beine nicht aufreissen: Jedes Glied beginnt mit einer Kugelkappe,
deren Mittelpunkt exakt im Drehpunkt liegt. Dreht sich das Glied um diesen Punkt,
bleibt die Kappe an Ort und Stelle -- es entsteht nie ein Spalt.

Die gesamte Geometrie wird hier aus Zahlen erzeugt (keine bpy.ops-Primitive,
keine Modifier), damit jeder Lauf dieselbe Geometrie liefert.
Nach dem Export wird jede GLB zurueckgelesen und die Hierarchie geprueft; die
Vorschaubilder entstehen ausschliesslich aus diesen zurueckgelesenen Dateien.
Farben werden linear eingetragen: linear = (c/255)^2,2.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Vector, Matrix

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.abspath(os.path.join(HIER, "..", ".."))
AUSGABE = os.path.join(WURZEL, "project", "assets", "characters", "zimmer")
VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "team_figuren")

BUDGET_DREIECKE = 1800   # Release-Plan 14.10. §5 (vorher 1.200): Platz fuer Tintenkontur und grosse Augen

# --- Release-Plan §5 "Figuren krasser" ---------------------------------------
KONTUR_AN = True
TINTE = "#1B1726"
SAETTIGUNG = 1.25
KOPF_SKAL = 1.15          # Kopf um den Hals-Drehpunkt vergroessert (Silhouette)
SCHUH_SKAL = 1.2
AUSDRUCK = "neutral"      # neutral | jubel | schock  (Portraets, build_portraits.py)
# Dreiecke und Versatz (m) der Huelle je Teil -- Teilnamen = Godot-Skelett
KONTUR_ZIEL = {"koerper": 120, "kopf": 150, "arm_l": 34, "arm_r": 34, "bein_l": 44, "bein_r": 44}
KONTUR_ABSTAND = {"koerper": 0.017, "kopf": 0.019, "arm_l": 0.013, "arm_r": 0.013,
                  "bein_l": 0.013, "bein_r": 0.014}


# =============================================================================
# Farben und Materialien
# =============================================================================

def farbe(hexwert):
    """'#RRGGBB' -> lineares RGBA fuer Blender (sRGB-Wert hoch 2,2)."""
    h = hexwert.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4)) + (1.0,)


def farbe_figur(hexwert):
    """Wie farbe(), aber Saettigung +25 % (Sticker-Pop). Haut, Augen, Tinte und
    fast graue Toene bleiben unveraendert."""
    import colorsys
    if hexwert.upper() in ("#F2C7A0", "#2B2320", "#EE9C8E", TINTE, "#FFFFFF"):
        return farbe(hexwert)
    h = hexwert.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
    if ss >= 0.12:
        ss = min(1.0, ss * SAETTIGUNG)
    r, g, b = colorsys.hsv_to_rgb(hh, ss, vv)
    return (r ** 2.2, g ** 2.2, b ** 2.2, 1.0)


def material(hexwert):
    """Ein Material je Farbe, matt, einseitig (Rueckseiten werden verworfen)."""
    name = "farbe_" + hexwert.lstrip("#").lower()
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    try:
        mat.use_nodes = True
    except Exception:
        pass
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = farbe_figur(hexwert)
        bsdf.inputs["Roughness"].default_value = 0.9
        bsdf.inputs["Metallic"].default_value = 0.0
    mat.diffuse_color = farbe_figur(hexwert)
    mat.use_backface_culling = True
    return mat


# =============================================================================
# Bau: sammelt Punkte und Flaechen eines Teils, bevor es ein Objekt wird
# =============================================================================

class Bau:
    def __init__(self, name):
        self.name = name
        self.punkte = []
        self.flaechen = []
        self.farben = []          # je Flaeche ein Hexwert

    def dazu(self, geo, matrix=None):
        punkte, flaechen, farben = geo
        versatz = len(self.punkte)
        for p in punkte:
            v = Vector(p)
            self.punkte.append(matrix @ v if matrix is not None else v)
        self.flaechen += [tuple(i + versatz for i in f) for f in flaechen]
        self.farben += farben

    def drehen(self, zentrum, matrix3):
        """Dreht alle Punkte um `zentrum` (baked Pose, Objekt bleibt ungedreht)."""
        z = Vector(zentrum)
        self.punkte = [z + matrix3 @ (p - z) for p in self.punkte]

    def verschieben(self, v):
        v = Vector(v)
        self.punkte = [p + v for p in self.punkte]

    def dreiecke(self):
        return sum(len(f) - 2 for f in self.flaechen)

    def objekt(self, drehpunkt):
        """Legt das Blender-Objekt an; der Ursprung liegt am Drehpunkt."""
        d = Vector(drehpunkt)
        punkte = self.punkte
        if self.name == "kopf" and KOPF_SKAL != 1.0:
            punkte = [d + (p - d) * KOPF_SKAL for p in punkte]
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([p - d for p in punkte], [], self.flaechen)
        palette = []
        for hexwert in self.farben:
            if hexwert not in palette:
                palette.append(hexwert)
        for hexwert in palette:
            me.materials.append(material(hexwert))
        for poly, hexwert in zip(me.polygons, self.farben):
            poly.material_index = palette.index(hexwert)
        me.validate()
        if KONTUR_AN and self.name in KONTUR_ZIEL:
            huelle_dazu(me)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(62.0))
        obj = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(obj)
        return obj


def huelle_dazu(me):
    """Tintenkontur: vereinfachte, nach aussen versetzte Kopie des Netzes mit
    umgedrehter Windung (Inverted Hull). Mit Backface-Culling sieht man nur die
    Rueckseiten -- ein Rand ohne Z-Kampf, ohne Shader, im selben Teil/Skelett."""
    pts = bmesh.new()
    pts.from_mesh(me)
    h = bmesh.new()
    for v in pts.verts:
        h.verts.new(v.co)
    pts.free()
    bmesh.ops.remove_doubles(h, verts=h.verts[:], dist=0.0008)
    # Konvexe Huelle: geschlossen, ohne Luecken -- die Kontur umschliesst Hut, Zopf, Kamera
    erg = bmesh.ops.convex_hull(h, input=h.verts[:], use_existing_faces=False)
    behalten = set(erg["geom"])
    bmesh.ops.delete(h, geom=[f for f in h.faces if f not in behalten], context="FACES_ONLY")
    bmesh.ops.delete(h, geom=[e for e in h.edges if not e.link_faces], context="EDGES")
    bmesh.ops.delete(h, geom=[v for v in h.verts if not v.link_faces], context="VERTS")
    bmesh.ops.triangulate(h, faces=h.faces[:])
    tmp = bpy.data.meshes.new("rp_e_huelle")
    h.to_mesh(tmp)
    h.free()
    tobj = bpy.data.objects.new("rp_e_huelle", tmp)
    bpy.context.scene.collection.objects.link(tobj)
    ziel = KONTUR_ZIEL[me.name]
    if len(tmp.polygons) > ziel:
        mod = tobj.modifiers.new("d", "DECIMATE")
        mod.ratio = ziel / float(len(tmp.polygons))
    bpy.context.view_layer.update()
    ev = tobj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    hm = bpy.data.meshes.new_from_object(ev)
    bpy.data.objects.remove(tobj)
    bpy.data.meshes.remove(tmp)
    hb = bmesh.new()
    hb.from_mesh(hm)
    hb.normal_update()
    abst = KONTUR_ABSTAND[me.name]
    for v in hb.verts:
        v.co = v.co + v.normal * abst
    me.materials.append(material(TINTE))
    slot = len(me.materials) - 1
    bm = bmesh.new()
    bm.from_mesh(me)
    vs = [bm.verts.new(v.co) for v in hb.verts]
    for f in hb.faces:
        try:
            neu = bm.faces.new([vs[v.index] for v in reversed(f.verts)])
        except ValueError:
            continue
        neu.material_index = slot
    bm.to_mesh(me)
    bm.free()
    hb.free()
    bpy.data.meshes.remove(hm)


def drehung(x=0.0, y=0.0, z=0.0):
    """Euler in Grad -> 3x3-Matrix (Reihenfolge XYZ)."""
    from mathutils import Euler
    return Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ").to_matrix()


def ausrichtung(richtung, rolle=None):
    """3x3-Matrix, die die lokale +Z-Achse auf `richtung` legt."""
    r = Vector(richtung).normalized()
    hilf = Vector((0.0, -1.0, 0.0)) if rolle is None else Vector(rolle)
    if abs(r.dot(hilf.normalized())) > 0.95:
        hilf = Vector((1.0, 0.0, 0.0))
    x = hilf.cross(r).normalized()
    y = r.cross(x).normalized()
    return Matrix((x, y, r)).transposed()


def platz(position, matrix3=None):
    m = matrix3.to_4x4() if matrix3 is not None else Matrix.Identity(4)
    m.translation = Vector(position)
    return m


def _farbwahl(farbe_oder_fn, *args):
    return farbe_oder_fn(*args) if callable(farbe_oder_fn) else farbe_oder_fn


# =============================================================================
# Grundformen -- jede liefert (punkte, flaechen, farben)
# =============================================================================

def drehkoerper(profil, seg, farbe_fn, sx=1.0, sy=1.0, verformen=None):
    """Rotationskoerper entlang lokal +Z. profil = [(t, radius), ...];
    Radius 0 am Anfang/Ende wird zum Pol. Querschnitt elliptisch (sx, sy).
    farbe_fn(t_mitte) -> Hexwert."""
    punkte, flaechen, farben = [], [], []
    ringe = []
    pole = {}
    for i, (t, r) in enumerate(profil):
        if r <= 0.0 and i in (0, len(profil) - 1):
            pole[i] = len(punkte)
            punkte.append((0.0, 0.0, t))
            ringe.append(None)
            continue
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            p = (r * sx * math.cos(a), r * sy * math.sin(a), t)
            if verformen:
                p = verformen(p)
            ring.append(len(punkte))
            punkte.append(p)
        ringe.append(ring)
    for i in range(len(profil) - 1):
        a, b = ringe[i], ringe[i + 1]
        tm = 0.5 * (profil[i][0] + profil[i + 1][0])
        hexwert = _farbwahl(farbe_fn, tm)
        for j in range(seg):
            k = (j + 1) % seg
            if a is None:
                flaechen.append((pole[i], b[k], b[j]))
            elif b is None:
                flaechen.append((a[j], a[k], pole[i + 1]))
            else:
                flaechen.append((a[j], a[k], b[k], b[j]))
            farben.append(hexwert)
    return punkte, flaechen, farben


def _spow(v, e):
    return math.copysign(abs(v) ** e, v)


def kugel(radien, seg, ringe, farbe_fn, e_hoch=1.0, e_rund=1.0, boden=None, verformen=None):
    """Ellipsoid / Superellipsoid um den Ursprung. e < 1 macht es kastiger.
    boden: kappt die Unterseite bei -boden*rz (flache Sohle).
    farbe_fn(x, y, z) bekommt die normierte Flaechenmitte."""
    rx, ry, rz = radien
    punkte, flaechen, farben = [], [], []
    unten = len(punkte)
    punkte.append((0.0, 0.0, -rz if boden is None else -rz * boden))
    reihen = []
    for i in range(1, ringe):
        phi = -math.pi / 2.0 + math.pi * i / ringe
        cp, sp = _spow(math.cos(phi), e_hoch), _spow(math.sin(phi), e_hoch)
        reihe = []
        for j in range(seg):
            th = 2.0 * math.pi * j / seg
            ct, st = _spow(math.cos(th), e_rund), _spow(math.sin(th), e_rund)
            z = rz * sp
            if boden is not None:
                z = max(z, -rz * boden)
            p = (rx * cp * ct, ry * cp * st, z)
            if verformen:
                p = verformen(p)
            reihe.append(len(punkte))
            punkte.append(p)
        reihen.append(reihe)
    oben = len(punkte)
    punkte.append((0.0, 0.0, rz))
    if verformen:
        punkte[unten] = verformen(punkte[unten])
        punkte[oben] = verformen(punkte[oben])

    def wahl(ids):
        m = [sum(punkte[i][k] for i in ids) / len(ids) for k in range(3)]
        return _farbwahl(farbe_fn, m[0] / rx, m[1] / ry, m[2] / rz)

    for j in range(seg):
        k = (j + 1) % seg
        f = (unten, reihen[0][k], reihen[0][j])
        flaechen.append(f)
        farben.append(wahl(f))
    for i in range(len(reihen) - 1):
        a, b = reihen[i], reihen[i + 1]
        for j in range(seg):
            k = (j + 1) % seg
            f = (a[j], a[k], b[k], b[j])
            flaechen.append(f)
            farben.append(wahl(f))
    for j in range(seg):
        k = (j + 1) % seg
        f = (reihen[-1][j], reihen[-1][k], oben)
        flaechen.append(f)
        farben.append(wahl(f))
    return punkte, flaechen, farben


def rohr(linie, radius, seg, farbe_fn, geschlossen=False, kappen=True, radius_fn=None):
    """Schlauch entlang einer Punktfolge (Kordel, Buegel, Stulpe, Riemen).
    farbe_fn(index_anteil 0..1) -> Hexwert."""
    pts = [Vector(p) for p in linie]
    n = len(pts)
    punkte, flaechen, farben = [], [], []
    tangenten = []
    for i in range(n):
        if geschlossen:
            t = pts[(i + 1) % n] - pts[(i - 1) % n]
        else:
            t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tangenten.append(t.normalized())
    ref = Vector((0.0, 0.0, 1.0))
    if abs(tangenten[0].dot(ref)) > 0.9:
        ref = Vector((1.0, 0.0, 0.0))
    normal = (ref - tangenten[0] * ref.dot(tangenten[0])).normalized()
    ringe = []
    for i in range(n):
        t = tangenten[i]
        normal = (normal - t * normal.dot(t)).normalized()
        bi = t.cross(normal)
        r = radius_fn(i / max(n - 1, 1)) if radius_fn else radius
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            ring.append(len(punkte))
            punkte.append(tuple(pts[i] + (normal * math.cos(a) + bi * math.sin(a)) * r))
        ringe.append(ring)
    spannen = n if geschlossen else n - 1
    for i in range(spannen):
        a, b = ringe[i], ringe[(i + 1) % n]
        hexwert = _farbwahl(farbe_fn, (i + 0.5) / spannen)
        for j in range(seg):
            k = (j + 1) % seg
            flaechen.append((a[j], a[k], b[k], b[j]))
            farben.append(hexwert)
    if not geschlossen and kappen:
        for ende, ring, t, anteil in ((0, ringe[0], -tangenten[0], 0.0),
                                      (n - 1, ringe[-1], tangenten[-1], 1.0)):
            r = radius_fn(anteil) if radius_fn else radius
            pol = len(punkte)
            punkte.append(tuple(pts[ende] + t * r * 0.8))
            for j in range(seg):
                k = (j + 1) % seg
                if ende == 0:
                    flaechen.append((ring[k], ring[j], pol))
                else:
                    flaechen.append((ring[j], ring[k], pol))
                farben.append(_farbwahl(farbe_fn, anteil))
    return punkte, flaechen, farben


def schneiden(geo, ebenen):
    """Schneidet eine Form mit Ebenen und wirft die Seite weg, in die die
    Normale zeigt. geo in Weltkoordinaten. ebenen = [(punkt, normale), ...]."""
    punkte, flaechen, farben = geo
    palette = sorted(set(farben))
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in punkte]
    for f, hexwert in zip(flaechen, farben):
        face = bm.faces.new([vs[i] for i in f])
        face.material_index = palette.index(hexwert)
    for co, no in ebenen:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=Vector(co),
                               plane_no=Vector(no).normalized(), clear_outer=True)
    bm.verts.index_update()
    neu_p = [tuple(v.co) for v in bm.verts]
    neu_f = [tuple(v.index for v in f.verts) for f in bm.faces]
    neu_c = [palette[f.material_index] for f in bm.faces]
    bm.free()
    return neu_p, neu_f, neu_c


def verschoben(geo, matrix):
    punkte, flaechen, farben = geo
    return [tuple(matrix @ Vector(p)) for p in punkte], flaechen, farben


def auf_flaeche(zentrum, radien, richtung, einsinken=0.0):
    """Punkt auf einem Ellipsoid in Blickrichtung `richtung` (plus Normale)."""
    d = Vector(richtung).normalized()
    rx, ry, rz = radien
    s = 1.0 / math.sqrt((d.x / rx) ** 2 + (d.y / ry) ** 2 + (d.z / rz) ** 2)
    p = Vector(zentrum) + d * s
    n = Vector((d.x * s / rx ** 2, d.y * s / ry ** 2, d.z * s / rz ** 2)).normalized()
    return p - n * einsinken, n


# =============================================================================
# Gemeinsames Skelett (Blender-Koordinaten: Z oben, Figur schaut nach -Y)
# =============================================================================

HUEFTE = Vector((0.0, 0.0, 0.28))
HALS = Vector((0.0, 0.0, 0.625))
SCHULTER = {"arm_l": Vector((0.165, 0.0, 0.545)), "arm_r": Vector((-0.165, 0.0, 0.545))}
HUEFTGELENK = {"bein_l": Vector((0.085, 0.0, 0.28)), "bein_r": Vector((-0.085, 0.0, 0.28))}
KOPF_MITTE = Vector((0.0, 0.0, 0.86))
KOPF_R = (0.25, 0.225, 0.235)

HAUT = "#F2C7A0"
AUGE = "#2B2320"
WANGE = "#EE9C8E"

RUMPF_TIEFE = 0.80
RUMPF_PROFIL = [(0.19, 0.0), (0.205, 0.10), (0.24, 0.160), (0.30, 0.182), (0.42, 0.175),
                (0.52, 0.160), (0.585, 0.130), (0.625, 0.080), (0.645, 0.0)]


def rumpf_radius(z):
    for (z0, r0), (z1, r1) in zip(RUMPF_PROFIL, RUMPF_PROFIL[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.0


def rumpf_punkt(x, z, hinten=False, abstand=0.0):
    """Punkt auf der Rumpfoberflaeche (vorn oder hinten) auf Hoehe z."""
    r = rumpf_radius(z)
    y = RUMPF_TIEFE * math.sqrt(max(r * r - x * x, 0.0)) + abstand
    return Vector((x, y if hinten else -y, z))


def neues_skelett():
    return {
        "koerper": [Bau("koerper"), HUEFTE.copy()],
        "kopf": [Bau("kopf"), HALS.copy()],
        "arm_l": [Bau("arm_l"), SCHULTER["arm_l"].copy()],
        "arm_r": [Bau("arm_r"), SCHULTER["arm_r"].copy()],
        "bein_l": [Bau("bein_l"), HUEFTGELENK["bein_l"].copy()],
        "bein_r": [Bau("bein_r"), HUEFTGELENK["bein_r"].copy()],
    }


def pose(teile, namen, zentrum, matrix3):
    """Backt eine Drehung um `zentrum` in Mesh UND Drehpunkte der genannten Teile."""
    z = Vector(zentrum)
    for n in namen:
        teile[n][0].drehen(z, matrix3)
        teile[n][1] = z + matrix3 @ (teile[n][1] - z)


# =============================================================================
# Bauteile
# =============================================================================

def rumpf(bau, oben, unten, grenze=0.30, bund=None):
    """Rumpf als weicher Tropfen. `bund` = Farbe eines Saums knapp ueber der Grenze."""
    def fn(t):
        if t < grenze:
            return unten
        if bund and t < grenze + 0.05:
            return bund
        return oben
    bau.dazu(drehkoerper(RUMPF_PROFIL, 10, fn, sy=RUMPF_TIEFE))


def arm(bau, schulter, richtung, aermel, aermel_ende=0.20, hand=HAUT, laenge=0.30):
    """Arm mit Kugelkappe im Drehpunkt und kugeliger Hand am Ende."""
    k = laenge / 0.30
    profil = [(-0.055, 0.0), (-0.03, 0.046), (0.02, 0.054), (0.19 * k, 0.046),
              (0.205 * k, 0.043), (0.255 * k, 0.052), (0.30 * k, 0.0)]
    fn = lambda t: aermel if t < aermel_ende * k else hand
    bau.dazu(drehkoerper(profil, 8, fn), platz(schulter, ausrichtung(richtung)))


def hand_punkt(schulter, richtung, laenge=0.30):
    return Vector(schulter) + Vector(richtung).normalized() * (0.255 * laenge / 0.30)


def bein(bau, huefte, hose, schuh, sohle, knoechel=None, pantoffel=False):
    """Stehendes Bein: Kugelkappe im Hueftgelenk, kurzer Stummel, runder Schuh."""
    profil = [(-0.07, 0.0), (-0.04, 0.058), (0.0, 0.068), (0.12, 0.058),
              (0.19, 0.050), (0.215, 0.0)]
    fn = lambda t: knoechel if (knoechel and t > 0.155) else hose
    bau.dazu(drehkoerper(profil, 6, fn), platz(huefte, ausrichtung((0, 0, -1))))
    x = huefte.x * 1.06
    schuh_an(bau, Vector((x, -0.03, 0.0)), schuh, sohle, pantoffel)


def schuh_an(bau, boden_punkt, schuh, sohle, pantoffel=False, ringe=5):
    if pantoffel:
        radien = (0.072 * SCHUH_SKAL, 0.105 * SCHUH_SKAL, 0.052)
        geo = kugel(radien, 8, 4, schuh, e_hoch=0.9, e_rund=0.9, boden=0.55)
        hoehe = radien[2] * 0.55
    else:
        radien = (0.066 * SCHUH_SKAL, 0.102 * SCHUH_SKAL, 0.052 * SCHUH_SKAL)
        geo = kugel(radien, 8, ringe, lambda x, y, z: sohle if z < -0.45 else schuh,
                    e_hoch=0.7, e_rund=0.85, boden=0.75)
        hoehe = radien[2] * 0.75
    bau.dazu(geo, platz(boden_punkt + Vector((0, 0, hoehe))))


LID = "#E3AE86"
MUND_DUNKEL = "#4A1B24"
ZUNGE = "#F0708A"
GLANZ = "#FFFFFF"


def augen(bau, zentrum, radien, iris=AUGE, blick=(0.0, 0.0), lid=0.0, groesse=1.0,
          hoehe=-0.13, abstand=0.37):
    """Grosse Augen: Weiss + Pupille + Glanzpunkt (je Auge ~64 Dreiecke).
    blick = (nach innen/aussen, hoch/runter) in Metern, lid = Anteil des
    Auges, den ein Lid von oben verdeckt. AUSDRUCK steuert jubel/schock."""
    oben = Vector((0, 0, 1))
    g = groesse * (1.18 if AUSDRUCK == "schock" else 1.0)
    rx, ry = 0.050 * g, 0.062 * g
    for s in (1.0, -1.0):
        p, n = auf_flaeche(zentrum, radien, (s * abstand, -1.0, hoehe), einsinken=0.004)
        a = ausrichtung(n, oben)
        if AUSDRUCK == "jubel":
            bogen = [p + a @ Vector((rx * u, 0.012 + 0.036 * (1.0 - u * u) - 0.020, 0.012))
                     for u in (-1.0, -0.5, 0.0, 0.5, 1.0)]
            bau.dazu(rohr(bogen, 0.0125, 3, AUGE, kappen=True))
            continue
        bau.dazu(kugel((rx, ry, 0.020), 10, 3, GLANZ), platz(p, a))
        pr = 0.55 if AUSDRUCK == "schock" else 1.0
        px = s * -blick[0] + 0.0
        po = p + a @ Vector((px, blick[1] + 0.004, 0.011))
        bau.dazu(kugel((0.034 * g * pr, 0.044 * g * pr, 0.016), 6, 3, iris), platz(po, a))
        gl = po + a @ Vector((-0.011 * g, 0.017 * g, 0.009))
        bau.dazu(kugel((0.0125 * g, 0.0135 * g, 0.008), 4, 2, GLANZ), platz(gl, a))
        if lid > 0.0:
            unten = ry * (1.0 - 2.0 * lid)
            h = (ry - unten) / 2.0 + 0.006
            bau.dazu(kugel((rx + 0.006, h, 0.023), 8, 3, LID),
                     platz(p + a @ Vector((0.0, (ry + unten) / 2.0 + 0.004, 0.003)), a))


def mund_ausdruck(bau, zentrum, radien, breite=0.13, hoehe=-0.37, laecheln=0.07, farbe_mund="#8C3B34"):
    """Mund je nach AUSDRUCK: Laechelbogen, offenes Lachen oder rundes 'O'."""
    oben = Vector((0, 0, 1))
    if AUSDRUCK == "neutral":
        linie = []
        for i in range(5):
            u = -1.0 + 2.0 * i / 4
            dz = hoehe - laecheln * (1.0 - u * u)
            linie.append(auf_flaeche(zentrum, radien, (u * breite, -1.0, dz), einsinken=-0.002)[0])
        bau.dazu(rohr(linie, 0.0075, 3, farbe_mund, kappen=False))
        return
    p, n = auf_flaeche(zentrum, radien, (0.0, -1.0, hoehe - 0.03), einsinken=0.004)
    a = ausrichtung(n, oben)
    if AUSDRUCK == "jubel":
        halb = lambda q: (q[0], min(q[1], 0.0) * 1.15, q[2])
        bau.dazu(kugel((0.085, 0.062, 0.018), 10, 4, MUND_DUNKEL, verformen=halb), platz(p + a @ Vector((0, 0.03, 0)), a))
        bau.dazu(kugel((0.045, 0.026, 0.010), 6, 3, ZUNGE), platz(p + a @ Vector((0, -0.032, 0.012)), a))
    else:
        bau.dazu(kugel((0.040, 0.054, 0.018), 8, 4, MUND_DUNKEL), platz(p + a @ Vector((0, -0.01, 0)), a))


def gesicht(bau, zentrum, radien, schlaefrig=False, iris=AUGE, blick=(0.0, 0.0), mund=None, lid_stufe=0.0):
    """Grosse Augen und rosige Wangen. mund = Laecheln-Staerke (None = kein Mund)."""
    oben = Vector((0, 0, 1))
    augen(bau, zentrum, radien, iris=iris, blick=blick, lid=max(0.45 if schlaefrig else 0.0, lid_stufe))
    for s in (1.0, -1.0):
        p, n = auf_flaeche(zentrum, radien, (s * 0.64, -1.0, -0.38), einsinken=0.005)
        bau.dazu(kugel((0.040, 0.024, 0.008), 6, 3, WANGE), platz(p, ausrichtung(n, oben)))
    if mund is not None:
        mund_ausdruck(bau, zentrum, radien, breite=0.11, hoehe=-0.37, laecheln=mund)


def verformt(geo, fn):
    punkte, flaechen, farben = geo
    return [fn(p) for p in punkte], flaechen, farben


def kopf_mit_haut(bau, verdeckt=(), seg=14, ringe=10):
    """Hautkopf. `verdeckt` = Schnittebenen fuer Flaechen, die unter Haar oder
    Muetze liegen und nie zu sehen sind -- spart ein Drittel der Dreiecke.
    Haut und Haarschale MUESSEN dieselbe Aufteilung haben, sonst stechen die
    Ecken der Haut durch die flachen Facetten der Schale."""
    geo = verschoben(kugel(KOPF_R, seg, ringe, HAUT), platz(KOPF_MITTE))
    if verdeckt:
        geo = schneiden(geo, verdeckt)
    bau.dazu(geo)


def haar_ebene(stirn_z, neigung):
    a = math.radians(neigung)
    return KOPF_MITTE + Vector((0, -0.215, stirn_z)), Vector((0, -math.cos(a), -math.sin(a)))


def haarschale(bau, haar, stirn_z=0.09, neigung=55.0, oben_offen=None, seg=14, ringe=10):
    """Haar als Schale ueber dem Kopf, vorn schraeg angeschnitten (Stirn frei).
    oben_offen: zusaetzliche Ebene, falls eine Muetze den Scheitel verdeckt."""
    c = KOPF_MITTE
    radien = (KOPF_R[0] + 0.012, KOPF_R[1] + 0.015, KOPF_R[2] + 0.013)
    geo = verschoben(kugel(radien, seg, ringe, haar), platz(c + Vector((0, 0.012, 0.012))))
    ebenen = [haar_ebene(stirn_z, neigung)]
    if oben_offen:
        ebenen.append(oben_offen)
    bau.dazu(schneiden(geo, ebenen))


def unter_haar(stirn_z, neigung, abstand=0.06):
    """Schnittebene fuer die Kopfhaut: entfernt, was hinter der Haarlinie liegt."""
    p, n = haar_ebene(stirn_z, neigung)
    return p - n * abstand, -n


# =============================================================================
# Die Figuren
# =============================================================================

HOODIE = "#3B3F48"
HOODIE_RAND = "#555B68"
HOODIE_TASCHE = "#32363E"
HOODIE_FALTE = "#464B57"
SCHATTEN = "#1E2026"
JEANS = "#4A6FA5"
SNEAKER = "#F4F4F1"
SNEAKER_SOHLE = "#C3C8CF"
KORDEL = "#E6E3DC"
KORDEL_ENDE = "#9AA1AA"


def kapuze_kopf(bau):
    """Die Kapuze IST der Kopf -- kein Gesicht, nur ein dunkler Schatten (ADR-021)."""
    c = KOPF_MITTE + Vector((0.0, 0.012, 0.0))
    R = (0.262, 0.246, 0.250)
    tiefe = 0.20

    def zipfel(p):
        # Hinten oben laeuft die Kapuze spitz zu -- so liest sie sich auch von
        # hinten als Kapuze und nicht als Kugel.
        x, y, z = p
        if y > 0 and z > 0:
            w = (y / R[1]) * (z / R[2])
            y += 0.075 * w
            z += 0.035 * w
        return (x, y, z)

    def lippe(p):
        # Der Rand der Oeffnung ist nicht eben: oben ragt der Stoff ueber die
        # Stirn, an den Seiten und unten weicht er zurueck. Ohne das sieht die
        # Kapuze von der Seite aus wie ein Taucherhelm.
        # Zusaetzlich wird vorn seitlich etwas zusammengezogen: die Oeffnung
        # wird ein stehendes Oval statt eines runden Bullauges.
        x, y, z = p[0] - c.x, p[1] - c.y, p[2] - c.z
        if y >= 0.0:
            return tuple(p)
        w = min(-y / R[1], 1.0) ** 2
        dy = w * (0.11 * (x / R[0]) ** 2 - 0.075 * (z / R[2]) + 0.02)
        return (c.x + x * (1.0 - 0.14 * w), p[1] + dy, p[2])

    # 16 Segmente: dann liegt eine Punktspalte exakt in der Mitte (vorn und
    # hinten), und die Naht kann genau auf ihr laufen statt zu schweben.
    SEG, RINGE = 16, 9
    schale = verschoben(kugel(R, SEG, RINGE, HOODIE, verformen=zipfel), platz(c))
    schale = schneiden(schale, [(c + Vector((0, -tiefe, 0)), (0, -1, 0.0))])
    bau.dazu(verformt(schale, lippe))

    # Schatten der Oeffnung: dunkler Pfropfen, zurueckgesetzt; die unsichtbare
    # Rueckhaelfte wird weggeschnitten.
    pfropfen = verschoben(kugel((0.215, 0.075, 0.21), 8, 6, SCHATTEN), platz(c + Vector((0, -0.095, -0.004))))
    pfropfen = schneiden(pfropfen, [(c + Vector((0, -0.095, 0)), (0, 1, 0))])
    bau.dazu(verformt(pfropfen, lippe))

    # Wulst um die Oeffnung
    f = math.sqrt(1.0 - (tiefe / R[1]) ** 2)
    a, b = R[0] * f, R[2] * f
    linie = [lippe(Vector((c.x + a * math.cos(t), c.y - tiefe + 0.002, c.z + b * math.sin(t))))
             for t in (2 * math.pi * i / 14 for i in range(14))]
    bau.dazu(rohr(linie, 0.024, 4, HOODIE_RAND, geschlossen=True))

    # Naht ueber Scheitel und Hinterkopf -- bricht die dunkle Flaeche von hinten.
    # Sie folgt exakt der mittleren Punktspalte der Schale (vorn -> Pol -> hinten).
    naht = []
    for seite, ring_idx in ([(-1.0, i) for i in (7, 8)] + [(0.0, None)] + [(1.0, i) for i in (8, 7, 6, 5, 4)]):
        if seite == 0.0:
            roh = Vector((0.0, 0.0, R[2]))
        else:
            phi = -math.pi / 2.0 + math.pi * ring_idx / RINGE
            roh = Vector((0.0, seite * R[1] * math.cos(phi), R[2] * math.sin(phi)))
        roh = Vector(zipfel(tuple(roh)))
        naht.append(Vector(lippe(c + roh)))
    bau.dazu(rohr(naht, 0.008, 4, HOODIE_RAND))

    # Kordeln -- haengen aus der Oeffnung ueber die Brust
    for s in (1.0, -1.0):
        start = Vector(lippe(Vector((s * 0.055, c.y - tiefe - 0.01, c.z - b * 0.9))))
        linie = [start,
                 (s * 0.062, -0.172, 0.60),
                 rumpf_punkt(s * 0.066, 0.49, abstand=0.014)]
        bau.dazu(rohr(linie, 0.011, 4, lambda t: KORDEL_ENDE if t >= 0.99 else KORDEL))


def kapuze_rumpf(bau):
    rumpf(bau, HOODIE, JEANS, grenze=0.285, bund=HOODIE_RAND)
    # Bauchtasche -- flach, sonst steht sie von der Seite als Kasten ab
    bau.dazu(kugel((0.116, 0.016, 0.060), 8, 4, HOODIE_TASCHE, e_hoch=0.55, e_rund=0.55),
             platz(rumpf_punkt(0.0, 0.375, abstand=-0.002)))
    # Wo die hochgezogene Kapuze am Ruecken ansetzt, faellt der Stoff als
    # V-foermiger Lappen auf die Schultern -- etwas heller, damit man es auch
    # am Schreibtisch von hinten sieht.
    lappen = kugel((0.14, 0.05, 0.095), 10, 4, HOODIE_FALTE,
                   verformen=lambda p: (p[0], p[1], p[2] - 0.045 * math.cos(min(abs(p[0]) / 0.14, 1.0) * math.pi / 2) ** 2))
    bau.dazu(lappen, platz(rumpf_punkt(0.0, 0.59, hinten=True, abstand=-0.022)))


def figur_kapuze():
    t = neues_skelett()
    kapuze_rumpf(t["koerper"][0])
    kapuze_kopf(t["kopf"][0])
    for n, s in (("arm_l", 1.0), ("arm_r", -1.0)):
        arm(t[n][0], t[n][1], (s * 0.17, 0.0, -1.0), HOODIE)
    for n in ("bein_l", "bein_r"):
        bein(t[n][0], t[n][1], JEANS, SNEAKER, SNEAKER_SOHLE)
    return t


SITZ_HOEHE = 0.47
TISCH_HOEHE = 0.74


def figur_kapuze_sitzend():
    """Sitzt am Schreibtisch, Ruecken zur Kamera. Ursprung: Boden unter Sitzmitte."""
    t = neues_skelett()
    kapuze_rumpf(t["koerper"][0])
    kapuze_kopf(t["kopf"][0])
    hoch = Vector((0, 0, SITZ_HOEHE + 0.07 - HUEFTE.z))   # Po sinkt 2 cm ins Polster
    for n in ("koerper", "kopf"):
        t[n][0].verschieben(hoch)
        t[n][1] += hoch
    for n in ("arm_l", "arm_r", "bein_l", "bein_r"):
        t[n][1] += hoch
    huefte = t["koerper"][1]
    pose(t, ["koerper", "kopf", "arm_l", "arm_r"], huefte, drehung(x=7.0))
    pose(t, ["kopf"], t["kopf"][1], drehung(x=5.0))

    # Arme nach vorn auf die Tischplatte, wie beim Tippen
    for n, s in (("arm_l", 1.0), ("arm_r", -1.0)):
        schulter = t[n][1]
        hand = Vector((s * 0.115, -0.345, TISCH_HOEHE + 0.05))
        arm(t[n][0], schulter, hand - schulter, HOODIE, laenge=(hand - schulter).length / 0.85)

    # Beine: Oberschenkel nach vorn, Unterschenkel haengen
    for n in ("bein_l", "bein_r"):
        b, h = t[n]
        knie = h + Vector((h.x * 0.06, -0.215, -0.01))
        oberschenkel = [(-0.07, 0.0), (-0.04, 0.060), (0.0, 0.070), (0.215, 0.060), (0.24, 0.0)]
        b.dazu(drehkoerper(oberschenkel, 6, JEANS), platz(h, ausrichtung(knie - h)))
        richtung = Vector((0.0, -0.10, -1.0)).normalized()
        unterschenkel = [(-0.062, 0.0), (-0.035, 0.052), (0.0, 0.060), (0.15, 0.052), (0.20, 0.0)]
        b.dazu(drehkoerper(unterschenkel, 6, JEANS), platz(knie, ausrichtung(richtung)))
        knoechel = knie + richtung * 0.19
        schuh_an(b, Vector((knoechel.x, knoechel.y - 0.03, knoechel.z - 0.045)), SNEAKER, SNEAKER_SOHLE, ringe=4)
    return t


PULLI = "#FF6FA8"      # Mira: Absenderfarbe aus theme.json
PULLI_BUND = "#E85A94"
HAAR_BRAUN = "#6B4630"
HAAR_BRAUE = "#4A2F20"
HOSE_DUNKEL = "#3E4052"
PANTOFFEL = "#EFA7A0"
KOPFHOERER = "#F6F5F1"
KOPFHOERER_POLSTER = "#B9BEC6"


def figur_dutt():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, PULLI, HOSE_DUNKEL, grenze=0.285, bund=PULLI_BUND)
    # Grosse Kopfhoerer um den Hals: Buegel hinten um den Nacken, die beiden
    # Muscheln liegen vorn auf dem Schluesselbein -- zwei weisse Scheiben
    # links und rechts vom Kinn sind auf 60 px das Erkennungszeichen.
    muschel = {}
    for s in (1.0, -1.0):
        muschel[s] = Vector((s * 0.140, -0.080, 0.605))
    linie = [muschel[1.0] + Vector((-0.005, 0.03, 0.035))]
    for i in range(1, 6):
        w = math.pi * i / 6
        linie.append(Vector((0.150 * math.cos(w), 0.145 * math.sin(w) + 0.0, 0.64 + 0.025 * math.sin(w))))
    linie.append(muschel[-1.0] + Vector((0.005, 0.03, 0.035)))
    k.dazu(rohr(linie, 0.017, 4, KOPFHOERER, kappen=False))
    for s in (1.0, -1.0):
        achse = Vector((s * 0.75, -0.35, 0.55))
        k.dazu(kugel((0.086, 0.086, 0.038), 8, 3,
                     lambda x, y, z: KOPFHOERER_POLSTER if z < -0.2 else KOPFHOERER,
                     e_hoch=0.55, e_rund=1.0),
               platz(muschel[s], ausrichtung(achse, (0, 0, 1))))

    kopf = t["kopf"][0]
    kopf_mit_haut(kopf, verdeckt=[unter_haar(0.09, 55.0)])
    haarschale(kopf, HAAR_BRAUN)
    kopf.dazu(kugel((0.098, 0.094, 0.092), 8, 5, HAAR_BRAUN),
              platz(KOPF_MITTE + Vector((0.0, 0.075, 0.25))))
    gesicht(kopf, KOPF_MITTE, KOPF_R, iris="#4A2F20", blick=(0.0, -0.004), mund=0.0, lid_stufe=0.30)
    # Freundlich-skeptisch: eine Braue gerade, die andere hochgezogen
    extra = {"jubel": 0.05, "schock": 0.10}.get(AUSDRUCK, 0.0)
    for s, hoch in ((1.0, 0.10 + extra), (-1.0, extra)):
        braue = [auf_flaeche(KOPF_MITTE, KOPF_R, (s * sx, -1.0, sz + hoch * k), einsinken=-0.002)[0]
                 for sx, sz, k in ((0.24, 0.17, 0.4), (0.36, 0.20, 1.0), (0.48, 0.16, 0.8))]
        kopf.dazu(rohr(braue, 0.0105, 3, HAAR_BRAUE))
    # Freundlich-skeptisch: Kopf leicht schief
    pose(t, ["kopf"], t["kopf"][1], drehung(y=-7.0))

    for n, s in (("arm_l", 1.0), ("arm_r", -1.0)):
        arm(t[n][0], t[n][1], (s * 0.20, 0.0, -1.0), PULLI)
    for n in ("bein_l", "bein_r"):
        bein(t[n][0], t[n][1], HOSE_DUNKEL, PANTOFFEL, PANTOFFEL, pantoffel=True)
    return t


BEANIE = "#F59E0B"     # Tobi: Absenderfarbe aus theme.json
BEANIE_STULPE = "#D98306"
HOODIE_HELL = "#A7ACB5"
HOODIE_HELL_TASCHE = "#979DA7"
JOGGER = "#5B606C"
JOGGER_BUND = "#4C505B"
SCHUH_DUNKEL = "#474B55"
SOHLE_HELL = "#E6E6E3"
HAAR_DUNKEL = "#5A3E2B"
BECHER = "#F5F2EA"
KAFFEE = "#5B3A26"


def figur_muetze():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, HOODIE_HELL, JOGGER, grenze=0.285, bund=HOODIE_HELL_TASCHE)
    k.dazu(kugel((0.115, 0.016, 0.06), 8, 4, HOODIE_HELL_TASCHE, e_hoch=0.55, e_rund=0.55),
           platz(rumpf_punkt(0.0, 0.375, abstand=-0.002)))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    # Muetzenrand: vorn knapp ueber den Augenbrauen, hinten tiefer
    neigung_rand = 12.0
    rand_z = lambda y: c.z + 0.07 - math.tan(math.radians(neigung_rand)) * y
    ueber_rand = (c + Vector((0, 0, 0.12)), Vector((0, math.tan(math.radians(neigung_rand)), 1.0)).normalized())
    kopf_mit_haut(kopf, verdeckt=[ueber_rand], seg=12, ringe=9)
    haarschale(kopf, HAAR_DUNKEL, stirn_z=0.06, neigung=58.0, oben_offen=ueber_rand, seg=12, ringe=9)
    gesicht(kopf, KOPF_MITTE, KOPF_R, schlaefrig=False, iris="#3B2A1E", mund=0.07, lid_stufe=0.0)
    # Beanie: eng anliegende Kuppel, hinten leicht abgesackt, dicke Stulpe, Bommel
    R = (0.258, 0.238, 0.262)

    def schlapp(p):
        x, y, z = p
        if z > 0:
            w = (z / R[2]) ** 2
            y += 0.065 * w
            z += 0.02 * w
        return (x, y, z)

    kuppel = verschoben(kugel(R, 12, 7, BEANIE, verformen=schlapp), platz(c + Vector((0, 0.012, 0.02))))
    kuppel = schneiden(kuppel, [(Vector((0, 0, rand_z(0.0) + 0.02)),
                                 Vector((0, -math.tan(math.radians(neigung_rand)), -1.0)).normalized())])
    kopf.dazu(kuppel)
    # Stulpe als eigener Ring -- ein umgeschlagener Rand. Oben kleiner als die
    # Kuppel, unten groesser: beide Kanten stecken ineinander, kein Spalt.
    stulpe = [(0.0, 0.252), (0.012, 0.268), (0.050, 0.268), (0.066, 0.234)]
    kopf.dazu(drehkoerper(stulpe, 12, BEANIE_STULPE, sy=0.93),
              platz(Vector((0, 0.012, rand_z(0.012) - 0.004)), drehung(x=-neigung_rand)))
    kopf.dazu(kugel((0.064, 0.064, 0.060), 6, 4, BEANIE_STULPE),
              platz(c + Vector((0.0, 0.095, 0.30))))

    for nb in ("bein_l", "bein_r"):
        bein(t[nb][0], t[nb][1], JOGGER, SCHUH_DUNKEL, SOHLE_HELL, knoechel=JOGGER_BUND)

    # Linker Arm haengt, rechter Arm haelt den Becher vor die Brust
    arm(t["arm_l"][0], t["arm_l"][1], (0.14, 0.02, -1.0), HOODIE_HELL)
    schulter = t["arm_r"][1]
    richtung = Vector((0.07, -0.25, -0.13))
    arm(t["arm_r"][0], schulter, richtung, HOODIE_HELL)
    hand = hand_punkt(schulter, richtung)
    becher = [(-0.058, 0.0), (-0.055, 0.045), (0.050, 0.049), (0.054, 0.0)]
    mitte = hand + Vector((0.035, -0.035, 0.035))
    t["arm_r"][0].dazu(drehkoerper(becher, 8, lambda z: KAFFEE if z > 0.051 else BECHER), platz(mitte))
    henkel = [mitte + Vector((-0.045 - 0.028 * math.sin(math.pi * i / 4), 0.0, 0.03 * math.cos(math.pi * i / 4)))
              for i in range(5)]
    t["arm_r"][0].dazu(rohr(henkel, 0.010, 4, BECHER, kappen=False))

    # Verschlafen: leicht nach vorn gesackt, Kopf haengt ein wenig
    pose(t, ["koerper", "kopf", "arm_l", "arm_r"], t["koerper"][1], drehung(x=5.0))
    pose(t, ["kopf"], t["kopf"][1], drehung(x=7.0, y=5.0))
    return t


CAP = "#D9483B"
CAP_SCHIRM = "#C43E33"
SHIRT = "#F4F2EE"
HOSE_NAVY = "#2F3A4F"
SCHUH_GRAU = "#3A3A3C"
HAAR_KUMPEL = "#3F2E24"
RUCKSACK = "#6F8F4E"
RUCKSACK_TASCHE = "#5F7D41"
RUCKSACK_RIEMEN = "#4E6636"


def figur_cap():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, SHIRT, HOSE_NAVY, grenze=0.285)
    # Rucksack
    k.dazu(kugel((0.150, 0.080, 0.175), 8, 5, RUCKSACK, e_hoch=0.6, e_rund=0.6),
           platz((0.0, 0.205, 0.43)))
    k.dazu(kugel((0.105, 0.035, 0.085), 8, 3, RUCKSACK_TASCHE, e_hoch=0.6, e_rund=0.6),
           platz((0.0, 0.282, 0.37)))
    for s in (1.0, -1.0):
        linie = [(s * 0.095, 0.13, 0.575), (s * 0.10, 0.02, 0.625),
                 rumpf_punkt(s * 0.10, 0.575, abstand=0.01), rumpf_punkt(s * 0.105, 0.43, abstand=0.008)]
        k.dazu(rohr(linie, 0.016, 3, RUCKSACK_RIEMEN))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    unter_cap = (c + Vector((0, 0, 0.10)), Vector((0, -0.10, 1.0)).normalized())
    kopf_mit_haut(kopf, verdeckt=[unter_cap], seg=12, ringe=9)
    haarschale(kopf, HAAR_KUMPEL, stirn_z=0.06, neigung=52.0, oben_offen=unter_cap, seg=12, ringe=9)
    gesicht(kopf, KOPF_MITTE, KOPF_R, mund=0.08)
    R = (0.264, 0.250, 0.250)
    kuppel = verschoben(kugel(R, 12, 8, CAP), platz(c + Vector((0, 0.01, 0.035))))
    kuppel = schneiden(kuppel, [(c + Vector((0, 0, 0.065)), (0, 0.10, -1.0))])
    kopf.dazu(kuppel)
    kopf.dazu(kugel((0.19, 0.15, 0.016), 10, 4, CAP_SCHIRM, e_hoch=0.8, e_rund=0.9),
              platz(c + Vector((0.0, -0.215, 0.075)), drehung(x=12.0)))
    kopf.dazu(kugel((0.022, 0.022, 0.014), 6, 2, CAP_SCHIRM), platz(c + Vector((0, 0.01, 0.287))))

    arm(t["arm_r"][0], t["arm_r"][1], (-0.17, 0.0, -1.0), SHIRT, aermel_ende=0.09)
    # Linke Hand halb erhoben -- winkt
    arm(t["arm_l"][0], t["arm_l"][1], (0.80, -0.18, 0.62), SHIRT, aermel_ende=0.09)
    for n in ("bein_l", "bein_r"):
        bein(t[n][0], t[n][1], HOSE_NAVY, SCHUH_GRAU, SOHLE_HELL)
    return t


# --- Nur fuer Portraets (nicht in FIGUREN: kein Spiel-Modell) -----------------
KIND_SHIRT = "#4FB286"
KIND_STREIFEN = "#F4F2EE"
KIND_HAAR = "#6B4A2B"
ONKEL_JACKE = "#8B5E3C"
ONKEL_HAAR = "#9A9AA3"
ONKEL_HOSE = "#4A4F5C"


def figur_kind():
    """Nachbarskind: gruenes Shirt, wuscheliges braunes Haar, grosse neugierige Augen."""
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, KIND_SHIRT, HOSE_NAVY, grenze=0.285)
    k.dazu(kugel((0.118, 0.020, 0.030), 8, 3, KIND_STREIFEN, e_hoch=0.6, e_rund=0.6),
           platz(rumpf_punkt(0.0, 0.50, abstand=-0.002)))
    kopf = t["kopf"][0]
    c = KOPF_MITTE
    kopf_mit_haut(kopf, seg=12, ringe=9)
    haarschale(kopf, KIND_HAAR, stirn_z=0.08, neigung=48.0, seg=12, ringe=9)
    gesicht(kopf, KOPF_MITTE, KOPF_R, mund=0.09, iris="#2B6CB0")
    for dx, dy, dz, r in ((0.10, 0.0, 0.27, 0.07), (-0.08, 0.02, 0.28, 0.06), (0.0, 0.05, 0.30, 0.07)):
        kopf.dazu(kugel((r, r, r), 6, 4, KIND_HAAR), platz(c + Vector((dx, dy, dz))))
    arm(t["arm_r"][0], t["arm_r"][1], (-0.17, 0.0, -1.0), KIND_SHIRT, aermel_ende=0.09)
    arm(t["arm_l"][0], t["arm_l"][1], (0.80, -0.18, 0.62), KIND_SHIRT, aermel_ende=0.09)
    for n in ("bein_l", "bein_r"):
        bein(t[n][0], t[n][1], HOSE_NAVY, SCHUH_GRAU, SOHLE_HELL)
    return t


def figur_onkel():
    """Der Onkel: braune Strickjacke, graues Haar, hohe Stirn, Schnauzer."""
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, ONKEL_JACKE, ONKEL_HOSE, grenze=0.285)
    k.dazu(kugel((0.040, 0.016, 0.200), 6, 4, "#F4F2EE", e_hoch=0.6, e_rund=0.6),
           platz(rumpf_punkt(0.0, 0.50, abstand=-0.002)))
    kopf = t["kopf"][0]
    c = KOPF_MITTE
    kopf_mit_haut(kopf, seg=12, ringe=9)
    haarschale(kopf, ONKEL_HAAR, stirn_z=0.13, neigung=60.0, seg=12, ringe=9)
    gesicht(kopf, KOPF_MITTE, KOPF_R, mund=0.05, iris="#3B2A1E")
    kopf.dazu(kugel((0.085, 0.022, 0.026), 8, 3, ONKEL_HAAR, e_hoch=0.7, e_rund=0.7),
              platz(c + Vector((0.0, -0.235, -0.095))))
    arm(t["arm_r"][0], t["arm_r"][1], (-0.17, 0.0, -1.0), ONKEL_JACKE, aermel_ende=0.09)
    arm(t["arm_l"][0], t["arm_l"][1], (0.14, 0.02, -1.0), ONKEL_JACKE, aermel_ende=0.09)
    for n in ("bein_l", "bein_r"):
        bein(t[n][0], t[n][1], ONKEL_HOSE, SCHUH_GRAU, SOHLE_HELL)
    return t


FIGUREN = {
    "figur_kapuze": figur_kapuze,
    "figur_kapuze_sitzend": figur_kapuze_sitzend,
    "figur_dutt": figur_dutt,
    "figur_muetze": figur_muetze,
    "figur_cap": figur_cap,
}

KINDER = ["kopf", "arm_l", "arm_r", "bein_l", "bein_r"]


# =============================================================================
# Export
# =============================================================================

def szene_leeren():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
                  bpy.data.lights, bpy.data.worlds):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def godot(v):
    """Blender (x, y, z) -> Godot (x, z, -y)."""
    return (round(v[0], 3), round(v[2], 3), round(-v[1], 3))


def exportieren(name, teile):
    szene_leeren()
    wurzel = bpy.data.objects.new("figur", None)
    wurzel.empty_display_size = 0.2
    bpy.context.scene.collection.objects.link(wurzel)
    kp = teile["koerper"][1]
    koerper = teile["koerper"][0].objekt(kp)
    koerper.parent = wurzel
    koerper.location = kp
    objekte = [koerper]
    for n in KINDER:
        obj = teile[n][0].objekt(teile[n][1])
        obj.parent = koerper
        obj.location = teile[n][1] - kp
        objekte.append(obj)
    bpy.context.view_layer.update()

    dreiecke = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objekte)
    zs = [(o.matrix_world @ v.co).z for o in objekte for v in o.data.vertices]
    os.makedirs(AUSGABE, exist_ok=True)
    pfad = os.path.join(AUSGABE, name + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=pfad, export_format="GLB", use_selection=False,
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False, export_animations=False,
    )
    je_teil = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objekte}
    return pfad, dreiecke, min(zs), max(zs), je_teil


def pruefen(name):
    """Liest die GLB zurueck und prueft Hierarchie, Ursprung und Drehung."""
    szene_leeren()
    pfad = os.path.join(AUSGABE, name + ".glb")
    bpy.ops.import_scene.gltf(filepath=pfad)
    objs = {o.name: o for o in bpy.data.objects}
    fehler = []
    erwartet = {"figur": None, "koerper": "figur"}
    erwartet.update({n: "koerper" for n in KINDER})
    for n, eltern in erwartet.items():
        o = objs.get(n)
        if o is None:
            fehler.append("fehlt: " + n)
            continue
        ist = o.parent.name if o.parent else None
        if ist != eltern:
            fehler.append("%s haengt an %s statt %s" % (n, ist, eltern))
        o.rotation_mode = "XYZ"
        if max(abs(a) for a in o.rotation_euler) > 1e-4:
            fehler.append("%s ist gedreht" % n)
    zeilen = []
    for n in ["koerper"] + KINDER:
        if n in objs:
            o = objs[n]
            zeilen.append("      %-8s lokal %-22s welt %s" % (n, godot(o.location), godot(o.matrix_world.translation)))
    return fehler, zeilen


# =============================================================================
# Vorschau
# =============================================================================

HINTERGRUND = "#F4EEE6"
BODEN_HOLZ = "#D9A66B"


def flacher_kasten(name, groesse, mitte, hexwert, eltern=None):
    """Einfacher Quader fuer Platzhalter-Moebel (nur Vorschau)."""
    hx, hy, hz = groesse[0] / 2, groesse[1] / 2, groesse[2] / 2
    mx, my, mz = mitte
    p = [(mx + sx * hx, my + sy * hy, mz + sz * hz)
         for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    b = Bau(name)
    b.dazu((p, f, [hexwert] * 6))
    obj = b.objekt(Vector((0, 0, 0)))
    obj.data.set_sharp_from_angle(angle=math.radians(30.0))
    if eltern:
        obj.parent = eltern
    return obj


def vorschau_szene(boden=BODEN_HOLZ):
    szene_leeren()
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = 32
    except Exception:
        pass
    sc.view_settings.view_transform = "Standard"
    sc.render.film_transparent = False
    welt = bpy.data.worlds.new("welt")
    sc.world = welt
    try:
        welt.use_nodes = True
    except Exception:
        pass
    bg = welt.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = farbe(HINTERGRUND)
    bg.inputs["Strength"].default_value = 0.9
    licht = bpy.data.lights.new("sonne", "SUN")
    licht.energy = 3.2
    licht.angle = math.radians(12.0)
    sonne = bpy.data.objects.new("sonne", licht)
    sc.collection.objects.link(sonne)
    sonne.rotation_euler = Vector((-0.45, -0.7, 1.0)).to_track_quat("Z", "Y").to_euler()
    b = Bau("boden")
    b.dazu(([(-20, -20, 0), (20, -20, 0), (20, 20, 0), (-20, 20, 0)], [(0, 1, 2, 3)], [boden]))
    b.objekt(Vector((0, 0, 0)))


def figur_laden(name, ort, drehung_z=0.0):
    vorher = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(AUSGABE, name + ".glb"))
    neu = [o for o in bpy.data.objects if o not in vorher]
    teile = {}
    for o in neu:
        o.rotation_mode = "XYZ"
        teile[o.name.split(".")[0]] = o
    wurzel = teile["figur"]
    wurzel.location = Vector(ort)
    wurzel.rotation_euler = (0.0, 0.0, math.radians(drehung_z))
    return teile


def hocker(ort):
    """Platzhalter-Sitz fuer die sitzende Figur in den Reihenbildern."""
    x, y = ort[0], ort[1]
    flacher_kasten("hocker", (0.40, 0.40, 0.47), (x, y + 0.02, SITZ_HOEHE / 2), "#8C8F96")


def kamera(ziel, richtung, breite, px_x, px_y):
    sc = bpy.context.scene
    cam_daten = bpy.data.cameras.new("kamera")
    cam_daten.type = "ORTHO"
    cam_daten.ortho_scale = breite
    cam_daten.clip_end = 100.0
    cam = bpy.data.objects.new("kamera", cam_daten)
    sc.collection.objects.link(cam)
    d = Vector(richtung).normalized()
    cam.location = Vector(ziel) + d * 20.0
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x = px_x
    sc.render.resolution_y = px_y
    sc.render.resolution_percentage = 100
    return cam


def rendern(dateiname):
    sc = bpy.context.scene
    os.makedirs(VORSCHAU, exist_ok=True)
    sc.render.filepath = os.path.join(VORSCHAU, dateiname)
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


def hochskalieren(dateiname, faktor, ziel):
    """Pixelgenau vergroessern -- damit man die 60-px-Fassung beurteilen kann."""
    import numpy as np
    img = bpy.data.images.load(os.path.join(VORSCHAU, dateiname))
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    gross = px.repeat(faktor, axis=0).repeat(faktor, axis=1)
    neu = bpy.data.images.new("gross", w * faktor, h * faktor, alpha=True)
    neu.pixels.foreach_set(gross.ravel())
    neu.filepath_raw = os.path.join(VORSCHAU, ziel)
    neu.file_format = "PNG"
    neu.save()
    bpy.data.images.remove(img)
    bpy.data.images.remove(neu)


REIHE = ["figur_kapuze", "figur_dutt", "figur_muetze", "figur_cap", "figur_kapuze_sitzend"]


def reihe_aufstellen(achse, abstand, drehung_z=0.0):
    achse = Vector(achse).normalized()
    alle = {}
    for i, name in enumerate(REIHE):
        ort = achse * (abstand * (i - (len(REIHE) - 1) / 2.0))
        if name.endswith("sitzend"):
            hocker(ort)
        alle[name] = figur_laden(name, ort, drehung_z)
    return alle


def vorschau_alles():
    iso = Vector((1.0, -1.0, 1.0))

    # (a) frontal und von hinten
    vorschau_szene(boden="#E9DFD2")
    reihe_aufstellen((1, 0, 0), 0.9)
    kamera((0, 0, 0.74), (0, -1, 0.0), 4.9, 1750, 580)
    rendern("a_frontal.png")
    kamera((0, 0, 0.74), (0, 1, 0.0), 4.9, 1750, 580)
    rendern("a_hinten.png")

    # (b) Spiel-Isometrie gross und auf ~60 px Figurhoehe
    vorschau_szene()
    reihe_aufstellen((1, 1, 0), 1.0)
    kamera((0, 0, 0.55), iso, 5.2, 1600, 900)
    rendern("b_iso_gross.png")
    px_je_m = 56.0
    kamera((0, 0, 0.55), iso, 5.2, int(5.2 * px_je_m), int(5.2 * px_je_m * 9 / 16))
    rendern("b_iso_60px.png")
    hochskalieren("b_iso_60px.png", 4, "b_iso_60px_x4.png")

    # (c) sitzend am Platzhalter-Tisch
    for variante, richtung, drehung_z in (("c_sitzend_hinten_oben.png", (0.45, 1.0, 1.05), 0.0),
                                         ("c_sitzend_iso.png", iso, -135.0)):
        vorschau_szene()
        gruppe = bpy.data.objects.new("gruppe", None)
        bpy.context.scene.collection.objects.link(gruppe)
        gruppe.rotation_euler = (0, 0, math.radians(drehung_z))
        holz, grau = "#B98655", "#5E626B"
        flacher_kasten("tischplatte", (1.20, 0.70, 0.04), (0, -0.62, TISCH_HOEHE - 0.02), holz, gruppe)
        for x in (-0.55, 0.55):
            for y in (-0.92, -0.32):
                flacher_kasten("tischbein", (0.05, 0.05, TISCH_HOEHE - 0.04),
                               (x, y, (TISCH_HOEHE - 0.04) / 2), holz, gruppe)
        flacher_kasten("bildschirm", (0.55, 0.04, 0.34), (0, -0.82, TISCH_HOEHE + 0.25), "#2B2E35", gruppe)
        flacher_kasten("tastatur", (0.40, 0.14, 0.02), (0, -0.40, TISCH_HOEHE + 0.01), "#D8D8D8", gruppe)
        flacher_kasten("sitz", (0.46, 0.46, 0.07), (0, 0.02, SITZ_HOEHE - 0.035), grau, gruppe)
        flacher_kasten("saeule", (0.06, 0.06, SITZ_HOEHE - 0.07), (0, 0.02, (SITZ_HOEHE - 0.07) / 2), grau, gruppe)
        flacher_kasten("lehne", (0.42, 0.06, 0.34), (0, 0.27, SITZ_HOEHE + 0.25), grau, gruppe)
        teile = figur_laden("figur_kapuze_sitzend", (0, 0, 0))
        teile["figur"].parent = gruppe
        kamera((0, 0, 0.8), richtung, 2.1, 1000, 1000)
        rendern(variante)

    # (d) Probe-Pose: Glieder um +-30 Grad gedreht
    for vorz, datei in ((1.0, "d_pose_plus"), (-1.0, "d_pose_minus")):
        vorschau_szene(boden="#E9DFD2")
        alle = reihe_aufstellen((0, 1, 0), 0.95)
        for teile in alle.values():
            teile["arm_l"].rotation_euler.x = math.radians(30.0 * vorz)
            teile["arm_r"].rotation_euler.x = math.radians(-30.0 * vorz)
            teile["bein_l"].rotation_euler.x = math.radians(-30.0 * vorz)
            teile["bein_r"].rotation_euler.x = math.radians(30.0 * vorz)
            teile["kopf"].rotation_euler.x = math.radians(10.0 * vorz)
        kamera((0, 0, 0.74), (1, 0, 0.12), 5.2, 1750, 600)
        rendern(datei + "_seite.png")
        kamera((0, 0, 0.64), (1, -0.8, 0.5), 5.8, 1750, 800)
        rendern(datei + "_schraeg.png")


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    print("")
    print("=== CHIBI-FIGUREN WG ===")
    ok = True
    for name, bauen in FIGUREN.items():
        szene_leeren()
        teile = bauen()
        pfad, dreiecke, zmin, zmax, je_teil = exportieren(name, teile)
        kb = os.path.getsize(pfad) / 1024.0
        warnung = "" if dreiecke <= BUDGET_DREIECKE else "  << UEBER BUDGET"
        print("  %-22s %4d Dreiecke  Hoehe %.3f m (min %.3f)  %5.1f KB%s"
              % (name, dreiecke, zmax, zmin, kb, warnung))
        print("      " + "  ".join("%s %d" % kv for kv in je_teil.items()))
        fehler, zeilen = pruefen(name)
        for z in zeilen:
            print(z)
        for f in fehler:
            ok = False
            print("      FEHLER: " + f)
    print("  Hierarchie-Pruefung: " + ("OK" if ok else "FEHLER"))
    if "--ohne-vorschau" not in args:
        vorschau_alles()
        print("  Vorschau: " + VORSCHAU)


if __name__ == "__main__":
    main()
