"""TASK 074b -- Einrichtung der WG-Karte, Teil B (docs/WELT1_TIEFE.md, 3 und 10).

Aufruf (headless, reproduzierbar):
    blender --background --python art_source/scripts/build_einrichtung_wg_b.py
    blender --background --python art_source/scripts/build_einrichtung_wg_b.py -- wohnzimmer balkon
    blender --background --python art_source/scripts/build_einrichtung_wg_b.py -- --ohne-vorschau

Erzeugt nach project/assets/world/zimmer/:
    einrichtung_wohnzimmer, einrichtung_balkon, einrichtung_freies_zimmer_{bewohnt,leer,studio},
    einrichtung_miras_zimmer, einrichtung_garten, wg_fundament, sperre_{kartons,band,schild}
und Vorschaubilder nach art_source/vorschau/team_b/.

Arbeitsweise: ALLES wird in Godot-Koordinaten gebaut (Y oben, Vorderseite +z)
und erst ganz am Ende einmal nach Blender gedreht -- Godot (x, y, z) wird
Blender (x, -z, y). So stehen die Zahlen im Skript genau so da wie im
Bauplan, und niemand muss beim Lesen im Kopf Achsen tauschen.

Jedes Asset ist EIN Mesh mit mehreren Materialien. Die Einzelteile werden
direkt in ein gemeinsames BMesh geschrieben (keine hunderte Objekte, kein
join-Operator), die Rundung entsteht per bmesh-Bevel schon beim Erzeugen.
"""

import bpy
import bmesh
import math
import os
import random
import sys
from contextlib import contextmanager
from mathutils import Matrix, Vector

SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(SKRIPT_ORDNER))
AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "zimmer")
VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "team_b")

# Bodenhoehe des Gartens: Unterkante des Fundaments (Oberkante -0,02, 0,45 hoch).
GARTEN_Y = -0.47
# Oberkante der Fensterbank im Wandmodul wg_wand_voll_fenster (build_room_wg.py:
# Bruestung 0,9, Bank 0,13 tief, 0,96 breit). Die Toepfe stehen darauf.
FENSTERBANK_Y = 0.90

# ACHTUNG Farbraum: glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. Die Palette steht hier als sRGB-Hex (so wie im
# Konzept und in WELT1_TIEFE.md), farbe() rechnet linear = s^2,2 zurueck.
PALETTE = {
    # Holz und Moebelflaechen
    "holz_hell": "#D9A66B", "holz_mittel": "#C8925A", "holz_dunkel": "#9A6A45",
    "holz_rot": "#B7774C", "weiss": "#F5F0E8", "creme": "#F2E3CC",
    "grau_hell": "#CFCAC4", "grau": "#8E8A8F", "anthrazit": "#4A4A52",
    "schwarz": "#2B2B31", "metall": "#B9BDC4", "metall_dunkel": "#5E6068",
    "gold": "#F4B731", "gold_dunkel": "#C98A1C",
    # Stoffe
    "stoff_blau": "#5E78A8", "stoff_blau_dunkel": "#3F5680", "stoff_senf": "#E3A93E",
    "stoff_rosa": "#EBA9A6", "stoff_salbei": "#9CB88C", "stoff_terracotta": "#CF7652",
    "stoff_creme": "#F0E4D2", "stoff_grau": "#9A96A0", "stoff_petrol": "#3F7F86",
    "stoff_lila": "#9C86C9", "stoff_rot": "#D05C4E", "stoff_jeans": "#5873A0",
    "stoff_weiss": "#FBF7F0",
    "teppich_beige": "#DCCBB2", "teppich_grau": "#B3ACA4", "teppich_rosa": "#E9C3B6",
    "teppich_blau": "#9DB3D1", "teppich_gruen": "#B9CBA3",
    # Pflanzen
    "pflanze": "#5DA84A", "pflanze_dunkel": "#3F8B3E", "pflanze_hell": "#8BC45A",
    "erde": "#6B4A33", "topf_terra": "#C8734A", "topf_weiss": "#EEE7DC",
    "topf_grau": "#9C968E", "rattan": "#D2A86E", "rattan_dunkel": "#B68A52",
    # Technik
    "bildschirm": "#232833", "bildschirm_an": "#8EC0F0", "licht_warm": "#FFD27A",
    "licht_lampe": "#FFE8B8", "neon_rosa": "#FF5C9E", "softbox": "#FFF6E6",
    "greenscreen": "#45C267", "akustik": "#5B6275", "akustik_hell": "#7A8196",
    # Buecher
    "buch_rot": "#C9574A", "buch_blau": "#4F77B0", "buch_gruen": "#6FA35A",
    "buch_gelb": "#E8B84A", "buch_creme": "#EADCC0", "buch_lila": "#8C72B8",
    # Kartons und Absperrung
    "karton": "#D09C66", "karton_dunkel": "#B8844F", "klebeband": "#9C6B3C",
    "etikett": "#F7F2E8", "gelb": "#F4C430", "band_schwarz": "#2B2B2B",
    # Aussen
    "stein_hell": "#D8CFC2", "stein": "#B8B0A5", "stein_dunkel": "#9A938A",
    "trittplatte": "#D3CABD", "rasen": "#8DC262", "rasen_dunkel": "#79B356",
    "busch": "#5DA84A", "busch_dunkel": "#4B9444", "busch_hell": "#7DBE55",
    "stamm": "#8A6446", "blume_rosa": "#F29BB5", "blume_gelb": "#F6D04D",
    "blume_weiss": "#FAF6EE", "blume_lila": "#B59BE3", "blume_rot": "#E86A5C",
    "blume_orange": "#F2A04A",
    # nur fuer die Vorschau (wird nie exportiert)
    "vs_boden": "#D9A66B", "vs_deck": "#8A6446", "vs_wand": "#F2E3CC",
    "vs_kappe": "#C8925A", "vs_glas": "#BFE0F0", "vs_gelaender": "#5A5A62",
    "vs_fliese": "#E8E4DC", "vs_bad": "#9CC7DE", "vs_dunkel": "#3A3A46",
}

# Leuchtende Materialien: Staerke der Emission (Farbe = Grundfarbe).
LEUCHTEND = {
    "bildschirm_an": 1.2, "licht_warm": 3.0, "licht_lampe": 2.0,
    "neon_rosa": 3.5, "softbox": 1.6,
}
# Jedes Material ist in Godot eine eigene Oberflaeche und damit ein eigener
# Draw Call. Fast gleiche Toene werden deshalb beim Bauen zusammengelegt --
# die Namen oben bleiben als Absicht im Code lesbar.
MATERIAL_ALIAS = {
    "buch_rot": "stoff_rot", "buch_blau": "stoff_blau", "buch_gruen": "stoff_salbei",
    "buch_gelb": "stoff_senf", "buch_creme": "stoff_creme", "buch_lila": "stoff_lila",
    "metall_dunkel": "anthrazit", "band_schwarz": "schwarz", "etikett": "weiss",
    "rattan_dunkel": "holz_mittel", "erde": "stamm", "grau_hell": "stoff_creme",
}
RAUHEIT = {"gold": 0.45, "gold_dunkel": 0.5, "metall": 0.5, "bildschirm": 0.4, "vs_glas": 0.2}


def farbe(hexwert, alpha=1.0):
    """sRGB-Hex -> lineare RGBA-Werte fuer glTF (linear = s^2,2)."""
    h = hexwert.lstrip("#")
    return tuple((int(h[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4)) + (alpha,)


def material(name):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    try:
        mat.use_nodes = True
    except Exception:
        pass
    grund = farbe(PALETTE[name])
    mat.diffuse_color = grund
    bsdf = None
    if mat.node_tree:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf = node
    if bsdf:
        bsdf.inputs["Base Color"].default_value = grund
        bsdf.inputs["Roughness"].default_value = RAUHEIT.get(name, 0.8)
        bsdf.inputs["Metallic"].default_value = 0.0
        if name in LEUCHTEND:
            bsdf.inputs["Emission Color"].default_value = grund
            bsdf.inputs["Emission Strength"].default_value = LEUCHTEND[name]
    return mat


# --- Geometrie-Baukasten (Godot-Koordinaten) ------------------------------------

def _trs(x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, rz=0.0):
    return (Matrix.Translation((x, y, z))
            @ Matrix.Rotation(math.radians(ry), 4, "Y")
            @ Matrix.Rotation(math.radians(rx), 4, "X")
            @ Matrix.Rotation(math.radians(rz), 4, "Z"))


# Godot (x, y, z) -> Blender (x, -z, y). Echte Drehung (Determinante +1),
# die Flaechenorientierung bleibt also erhalten.
GODOT_NACH_BLENDER = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _abrunden(bm, r, seg, winkel=None):
    if r <= 0.002:
        return
    if winkel is None:
        kanten = list(bm.edges)
    else:
        kanten = [e for e in bm.edges
                  if e.is_manifold and e.calc_face_angle(0.0) > math.radians(winkel)]
    if not kanten:
        return
    ecken = {v for e in kanten for v in e.verts}
    bmesh.ops.bevel(bm, geom=list(ecken) + kanten, offset=r, offset_type="OFFSET",
                    segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)


def rundrechteck(w, h, rad, eseg=3):
    """Umriss eines Rechtecks mit runden Ecken, gegen den Uhrzeigersinn."""
    rad = max(0.001, min(rad, w / 2 - 1e-4, h / 2 - 1e-4))
    pkt = []
    for cx, cy, start in ((w / 2 - rad, h / 2 - rad, 0), (-w / 2 + rad, h / 2 - rad, 90),
                          (-w / 2 + rad, -h / 2 + rad, 180), (w / 2 - rad, -h / 2 + rad, 270)):
        for k in range(eseg + 1):
            a = math.radians(start + 90.0 * k / eseg)
            pkt.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pkt


def ellipse(w, h, n=16, rng=None, zitter=0.0):
    pkt = []
    for i in range(n):
        a = 2 * math.pi * i / n
        f = 1.0 + (rng.uniform(-zitter, zitter) if rng else 0.0)
        pkt.append((w / 2 * math.cos(a) * f, h / 2 * math.sin(a) * f))
    return pkt


class Bau:
    """Sammelt Einzelteile in EINEM BMesh. Gruppen verschieben/drehen alles,
    was innerhalb von `with b.an(...)` entsteht."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.stapel = [Matrix.Identity(4)]
        self.dreiecke = 0

    @contextmanager
    def an(self, x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, rz=0.0, s=1.0):
        m = self.stapel[-1] @ _trs(x, y, z, ry, rx, rz) @ Matrix.Scale(s, 4)
        self.stapel.append(m)
        try:
            yield
        finally:
            self.stapel.pop()

    def _mat(self, name):
        name = MATERIAL_ALIAS.get(name, name)
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def _einfuegen(self, bm, mat, lokal):
        bmesh.ops.transform(bm, matrix=self.stapel[-1] @ lokal, verts=bm.verts)
        idx = self._mat(mat)
        neu = {v: self.bm.verts.new(v.co) for v in bm.verts}
        for f in bm.faces:
            try:
                nf = self.bm.faces.new([neu[v] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = idx
            nf.smooth = True
            self.dreiecke += len(f.verts) - 2
        bm.free()

    # -- Grundkoerper -----------------------------------------------------------
    def kasten(self, mat, sx, sy, sz, x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, rz=0.0, r=0.02, seg=1):
        """Quader, Ursprung unten Mitte."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, sy / 2, 0), verts=bm.verts)
        _abrunden(bm, min(r, 0.45 * min(sx, sy, sz)), seg)
        self._einfuegen(bm, mat, _trs(x, y, z, ry, rx, rz))

    def zylinder(self, mat, rad, h, x=0.0, y=0.0, z=0.0, seg=12, rad_oben=None,
                 ry=0.0, rx=0.0, rz=0.0, r=0.0, seg_r=1):
        """Zylinder/Kegelstumpf entlang +y, Ursprung unten Mitte."""
        bm = bmesh.new()
        ro = rad if rad_oben is None else rad_oben
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                              radius1=rad, radius2=ro, depth=h)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, "X"), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, h / 2, 0), verts=bm.verts)
        grenze = min(rad, ro if ro > 0 else rad, h)
        _abrunden(bm, min(r, 0.45 * grenze), seg_r, winkel=50)
        self._einfuegen(bm, mat, _trs(x, y, z, ry, rx, rz))

    def kugel(self, mat, rad, x=0.0, y=0.0, z=0.0, sx=1.0, sy=1.0, sz=1.0, fein=2,
              ry=0.0, rx=0.0, rz=0.0):
        """Kugel/Ellipsoid, Ursprung Mitte. fein: 1 = 20, 2 = 80 Dreiecke; 'uv' = 48."""
        bm = bmesh.new()
        if fein == "uv":
            bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=rad)
        elif fein == "blatt":
            bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=3, radius=rad)
        else:
            bmesh.ops.create_icosphere(bm, subdivisions=fein, radius=rad)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        self._einfuegen(bm, mat, _trs(x, y, z, ry, rx, rz))

    def dreh(self, mat, profil, x=0.0, y=0.0, z=0.0, seg=12, ry=0.0, rx=0.0, rz=0.0,
             geschlossen=False, versatz=0.0):
        """Drehkoerper um +y. Profil [(radius, hoehe)], aussen von unten nach oben;
        Radius 0 = Pol. geschlossen verbindet den letzten mit dem ersten Ring."""
        bm = bmesh.new()
        ringe = []
        for rad, hy in profil:
            if rad <= 1e-5:
                ringe.append([bm.verts.new((0.0, hy, 0.0))])
            else:
                ringe.append([bm.verts.new((rad * math.cos(2 * math.pi * i / seg + versatz), hy,
                                            rad * math.sin(2 * math.pi * i / seg + versatz)))
                              for i in range(seg)])
        paare = list(zip(ringe[:-1], ringe[1:]))
        if geschlossen:
            paare.append((ringe[-1], ringe[0]))
        for a, c in paare:
            if len(a) == 1 and len(c) == 1:
                continue
            for i in range(seg):
                j = (i + 1) % seg
                try:
                    if len(a) == 1:
                        bm.faces.new((a[0], c[i], c[j]))
                    elif len(c) == 1:
                        bm.faces.new((a[i], c[0], a[j]))
                    else:
                        bm.faces.new((a[i], c[i], c[j], a[j]))
                except ValueError:
                    pass
        self._einfuegen(bm, mat, _trs(x, y, z, ry, rx, rz))

    def rohr(self, mat, punkte, rad, seg=6, kappen=True, geschlossen=False):
        """Rohr entlang eines Polygonzugs (Punkte in lokalen Koordinaten)."""
        bm = bmesh.new()
        pkt = [Vector(p) for p in punkte]
        n = len(pkt)
        tang = []
        for i in range(n):
            if geschlossen:
                t = (pkt[(i + 1) % n] - pkt[i]).normalized() + (pkt[i] - pkt[i - 1]).normalized()
            elif i == 0:
                t = pkt[1] - pkt[0]
            elif i == n - 1:
                t = pkt[-1] - pkt[-2]
            else:
                t = (pkt[i + 1] - pkt[i]).normalized() + (pkt[i] - pkt[i - 1]).normalized()
            tang.append(t.normalized())
        ref = Vector((0, 1, 0)) if abs(tang[0].y) < 0.9 else Vector((1, 0, 0))
        nrm = tang[0].cross(ref).normalized()
        ringe = []
        for i in range(n):
            if i > 0:
                nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
            bi = tang[i].cross(nrm)
            ringe.append([bm.verts.new(pkt[i] + (nrm * math.cos(2 * math.pi * k / seg)
                                                 + bi * math.sin(2 * math.pi * k / seg)) * rad)
                          for k in range(seg)])
        paare = list(zip(ringe[:-1], ringe[1:]))
        if geschlossen:
            paare.append((ringe[-1], ringe[0]))
        for a, c in paare:
            for k in range(seg):
                j = (k + 1) % seg
                bm.faces.new((a[k], a[j], c[j], c[k]))
        if kappen and not geschlossen:
            bm.faces.new(list(reversed(ringe[0])))
            bm.faces.new(ringe[-1])
        self._einfuegen(bm, mat, Matrix.Identity(4))

    def prisma(self, mat, umriss, dicke, x=0.0, y=0.0, z=0.0, ry=0.0, rx=0.0, rz=0.0, r=0.0, seg_r=1):
        """Umriss [(u, v)] gegen den Uhrzeigersinn in der lokalen XY-Ebene,
        entlang z um die Dicke extrudiert (mittig)."""
        bm = bmesh.new()
        unten = [bm.verts.new((u, v, -dicke / 2)) for u, v in umriss]
        oben = [bm.verts.new((u, v, dicke / 2)) for u, v in umriss]
        n = len(umriss)
        bm.faces.new(list(reversed(unten)))
        bm.faces.new(oben)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((unten[i], unten[j], oben[j], oben[i]))
        _abrunden(bm, r, seg_r, winkel=40)
        self._einfuegen(bm, mat, _trs(x, y, z, ry, rx, rz))

    def platte(self, mat, w, d, h, x=0.0, y=0.0, z=0.0, rad=0.05, ry=0.0, r=0.0, eseg=3):
        """Liegende Platte mit runden Ecken (Tischplatte, Teppich), Ursprung unten Mitte."""
        self.prisma(mat, rundrechteck(w, d, rad, eseg), h, x=x, y=y + h / 2, z=z, ry=ry, rx=-90, r=r)

    def scheibe(self, mat, umriss, h, x=0.0, y=0.0, z=0.0, ry=0.0, r=0.0):
        """Liegende Scheibe mit beliebigem Umriss, Ursprung unten."""
        self.prisma(mat, umriss, h, x=x, y=y + h / 2, z=z, ry=ry, rx=-90, r=r)

    def tafel(self, mat, w, h, t, x=0.0, y=0.0, z=0.0, rad=0.04, ry=0.0, rx=0.0, r=0.0, eseg=3):
        """Stehende Tafel mit runden Ecken, Vorderseite +z, Ursprung unten an der Rueckseite."""
        with self.an(x=x, y=y, z=z, ry=ry, rx=rx):
            self.prisma(mat, rundrechteck(w, h, rad, eseg), t, y=h / 2, z=t / 2, r=r)

    # -- Abschluss ----------------------------------------------------------------
    def objekt(self, name):
        bmesh.ops.transform(self.bm, matrix=GODOT_NACH_BLENDER, verts=self.bm.verts)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(material(m))
        me.set_sharp_from_angle(angle=math.radians(50))
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        mod = obj.modifiers.new("gewichtet", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
        mod.mode = "FACE_AREA"
        mod.weight = 50
        with bpy.context.temp_override(object=obj, active_object=obj,
                                       selected_objects=[obj], selected_editable_objects=[obj]):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return obj


def dreiecke_von(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def masse_von(obj):
    """Ausdehnung in Godot-Achsen (x, y, z) als (min, max)-Paare."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.z for v in obj.data.vertices]
    zs = [-v.co.y for v in obj.data.vertices]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


# =============================================================================
# Gemeinsame Bausteine. Konvention: Ursprung unten Mitte, Vorderseite +z,
# Rueckseite -z (steht an der Wand). Gedreht wird von aussen mit b.an(ry=...).
# =============================================================================

def topf(b, rad=0.14, h=0.24, mat="topf_terra", seg=10):
    """Blumentopf mit Rand und Erde."""
    b.dreh(mat, [(0.0, 0.0), (rad * 0.72, 0.0), (rad * 0.95, h * 0.82), (rad * 1.05, h * 0.84),
                 (rad * 1.05, h), (rad * 0.9, h), (0.0, h * 0.9)], seg=seg)
    b.zylinder("erde", rad * 0.9, 0.01, y=h * 0.9, seg=seg)


def pflanze_klein(b, rng, rad=0.09, mat_topf="topf_weiss", gruen="pflanze"):
    """Kleine Topfpflanze fuer Fensterbank, Regal, Tisch (~120 Dreiecke)."""
    h = rad * 1.6
    topf(b, rad, h, mat_topf, seg=8)
    for i in range(3):
        a = rng.uniform(0, 2 * math.pi) + i * 2.1
        d = rad * 0.45
        b.kugel(gruen if i != 1 else "pflanze_hell", rad * rng.uniform(0.75, 0.95),
                x=math.cos(a) * d, y=h + rad * (0.6 + 0.35 * i), z=math.sin(a) * d, sy=0.85, fein=1)


def pflanze_blatt(b, rng, h=1.3, rad_topf=0.22, mat_topf="topf_weiss", blaetter=9, max_rad=0.55):
    """Grosse Blattpflanze: Stiele mit ovalen Blaettern, die nach aussen kippen.
    max_rad begrenzt die Ausladung, damit keine Blattspitze durch eine Wand sticht."""
    th = rad_topf * 1.5 if mat_topf else 0.0
    if mat_topf:
        topf(b, rad_topf, th, mat_topf, seg=10)
    for i in range(blaetter):
        a = 2 * math.pi * i / blaetter + rng.uniform(-0.25, 0.25)
        hoehe = th + (h - th) * (0.45 + 0.55 * ((i * 5) % blaetter) / blaetter)
        weit = rng.uniform(0.14, 0.26) * (h / 1.3)
        laenge = rng.uniform(0.2, 0.26) * (h / 1.3) + 0.04
        s = min(1.0, max_rad / (weit + 1.75 * laenge))
        weit *= s
        laenge *= s
        spitze = Vector((math.cos(a) * weit, hoehe, math.sin(a) * weit))
        b.rohr("pflanze_dunkel", [(0, th, 0), (spitze.x * 0.4, (th + hoehe) * 0.55, spitze.z * 0.4), spitze.to_tuple()],
               0.012, seg=4)
        mat = "pflanze" if i % 3 else "pflanze_hell"
        # Blatt: flaches Ellipsoid, laengs nach aussen, leicht haengend
        with b.an(x=spitze.x, y=spitze.y, z=spitze.z, ry=-math.degrees(a) + 90):
            b.kugel(mat, 1.0, z=laenge * 0.8, sx=laenge * 0.42, sy=0.025, sz=laenge,
                    rx=rng.uniform(12, 30), fein="blatt")


def pflanze_busch(b, rng, h=0.9, rad_topf=0.18, mat_topf="topf_terra", blueten=None):
    """Buschige Pflanze aus runden Blattballen, optional mit Blueten."""
    th = rad_topf * 1.4 if mat_topf else 0.0
    if mat_topf:
        topf(b, rad_topf, th, mat_topf, seg=10)
    ballen = 4 if h > 0.6 else 3
    for i in range(ballen):
        a = 2 * math.pi * i / ballen + rng.uniform(-0.4, 0.4)
        d = rad_topf * (0.5 if i else 0.0)
        rr = (h - th) * rng.uniform(0.38, 0.48)
        yy = th + rr * 0.8 + (h - th - rr * 1.6) * (i / max(1, ballen - 1))
        b.kugel(["pflanze", "pflanze_dunkel", "pflanze_hell"][i % 3], rr,
                x=math.cos(a) * d, y=yy, z=math.sin(a) * d, sy=0.9, fein=2)
    if blueten:
        for i in range(7):
            a = rng.uniform(0, 2 * math.pi)
            rr = (h - th) * 0.42
            yy = th + rng.uniform(0.35, 0.95) * (h - th)
            b.kugel(blueten[i % len(blueten)], 0.045, x=math.cos(a) * rr * 0.95,
                    y=yy, z=math.sin(a) * rr * 0.95, fein=1)


def buecherreihe(b, rng, breite, hoehe_max, tiefe=0.2, x0=0.0, y=0.0, z=0.0, kippen=True):
    """Buecher nebeneinander, von x0 aus nach +x. Gibt die belegte Breite zurueck."""
    farben = ["buch_rot", "buch_blau", "buch_gruen", "buch_gelb", "buch_creme", "buch_lila"]
    x = x0
    while x < x0 + breite - 0.06:
        dicke = rng.uniform(0.1, 0.18)
        h = hoehe_max * rng.uniform(0.72, 0.98)
        b.kasten(rng.choice(farben), dicke, h, tiefe * rng.uniform(0.85, 1.0), x=x + dicke / 2, y=y, z=z, r=0.0)
        x += dicke + 0.005
    if kippen and x0 + breite - x > 0.05:
        b.kasten(rng.choice(farben), 0.05, hoehe_max * 0.85, tiefe * 0.9,
                 x=x + 0.1, y=y, z=z, rz=-22, r=0.0)
    return x - x0


def buecherstapel(b, rng, n=3, x=0.0, y=0.0, z=0.0, ry=0.0):
    farben = ["buch_rot", "buch_blau", "buch_gruen", "buch_gelb", "buch_creme", "buch_lila"]
    hoehe = y
    with b.an(x=x, z=z, ry=ry):
        for i in range(n):
            d = rng.uniform(0.035, 0.06)
            b.kasten(rng.choice(farben), rng.uniform(0.2, 0.26), d, rng.uniform(0.15, 0.19),
                     y=hoehe, ry=rng.uniform(-12, 12), r=0.0)
            hoehe += d
    return hoehe


def bild(b, w, h, motiv="berge", rahmen="holz_mittel", t=0.035):
    """Gerahmtes Bild ohne Schrift, haengt mit der Rueckseite an z = 0."""
    b.kasten(rahmen, w, h, t, z=t / 2, r=0.008)
    iw, ih = w - 0.08, h - 0.08
    zv = t + 0.002
    if motiv == "berge":
        b.kasten("teppich_blau", iw, ih, 0.004, y=0.04, z=zv, r=0.0)
        b.prisma("pflanze", [(-iw / 2, 0), (iw * 0.05, 0), (-iw * 0.18, ih * 0.55)], 0.006, y=0.04, z=zv + 0.003)
        b.prisma("pflanze_dunkel", [(-iw * 0.25, 0), (iw / 2, 0), (iw * 0.2, ih * 0.7)], 0.006, y=0.04, z=zv + 0.005)
        b.zylinder("blume_gelb", ih * 0.1, 0.006, x=-iw * 0.28, y=0.04 + ih * 0.75, z=zv + 0.003, rx=90, seg=10)
    elif motiv == "sonne":
        b.kasten("stoff_creme", iw, ih, 0.004, y=0.04, z=zv, r=0.0)
        b.zylinder("stoff_terracotta", min(iw, ih) * 0.3, 0.006, y=0.04 + ih * 0.55, z=zv, rx=90, seg=14)
        b.kasten("stoff_senf", iw, ih * 0.28, 0.006, y=0.04, z=zv + 0.002, r=0.0)
    elif motiv == "welle":
        b.kasten("stoff_weiss", iw, ih, 0.004, y=0.04, z=zv, r=0.0)
        b.kasten("stoff_petrol", iw, ih * 0.35, 0.006, y=0.04, z=zv + 0.002, r=0.0)
        b.kugel("stoff_petrol", iw * 0.3, x=-iw * 0.2, y=0.04 + ih * 0.35, z=zv, sy=ih * 0.3 / (iw * 0.3), sz=0.02, fein="uv")
        b.zylinder("stoff_rosa", min(iw, ih) * 0.14, 0.006, x=iw * 0.22, y=0.04 + ih * 0.72, z=zv, rx=90, seg=10)
    else:  # bloecke
        b.kasten("stoff_creme", iw, ih, 0.004, y=0.04, z=zv, r=0.0)
        b.kasten("stoff_rosa", iw * 0.45, ih * 0.55, 0.006, x=-iw * 0.22, y=0.04 + ih * 0.1, z=zv + 0.002, r=0.0)
        b.kasten("stoff_blau", iw * 0.35, ih * 0.4, 0.006, x=iw * 0.2, y=0.04 + ih * 0.45, z=zv + 0.004, r=0.0)
        b.kasten("stoff_senf", iw * 0.2, ih * 0.2, 0.006, x=iw * 0.25, y=0.04 + ih * 0.12, z=zv + 0.004, r=0.0)


def teppich(b, w, d, x=0.0, z=0.0, grund="teppich_beige", rand="teppich_grau", ry=0.0, rund=False):
    """Flacher Teppich (Oberkante 0,016) mit abgesetztem Rand."""
    with b.an(x=x, z=z, ry=ry):
        if rund:
            b.scheibe(rand, ellipse(w, d, 20), 0.010)
            b.scheibe(grund, ellipse(w - 0.16, d - 0.16, 20), 0.006, y=0.010)
        else:
            b.platte(rand, w, d, 0.010, rad=0.06)
            b.platte(grund, w - 0.16, d - 0.16, 0.006, y=0.010, rad=0.04)


def fensterbank(b, breite=0.96, tiefe=0.13):
    """Die Fensterbank gehoert zum Wandmodul wg_wand_voll_fenster (Oberkante
    0,90, 0,13 vor der Wandflaeche, 0,96 breit -- build_room_wg.py). Eine
    zweite hier waere deckungsgleich und wuerde flimmern; die Einrichtung
    stellt nur die Toepfe darauf. Die Funktion bleibt als Merkposten stehen."""
    return


def karton(b, sx, sy, sz, x=0.0, y=0.0, z=0.0, ry=0.0, mat="karton", etikett=True):
    """Umzugskarton mit Klebeband ueber Deckel und Stirnseiten."""
    with b.an(x=x, y=y, z=z, ry=ry):
        b.kasten(mat, sx, sy, sz, r=0.012)
        band = 0.07
        b.kasten("klebeband", band, 0.004, sz + 0.004, y=sy - 0.001, r=0.0)
        b.kasten("klebeband", band, sy * 0.35, 0.004, y=sy * 0.65, z=sz / 2 + 0.001, r=0.0)
        b.kasten("klebeband", band, sy * 0.35, 0.004, y=sy * 0.65, z=-sz / 2 - 0.001, r=0.0)
        b.kasten("karton_dunkel", sx * 0.96, 0.004, 0.012, y=sy - 0.001, r=0.0)  # Deckelfuge
        if etikett:
            b.kasten("etikett", min(0.16, sx * 0.4), 0.09, 0.004, x=sx * 0.22, y=sy * 0.35, z=sz / 2 + 0.002, r=0.0)


def lichterkette(b, punkte, durchhang=0.08, abstand=0.22, rad=0.034):
    """Kabel zwischen Befestigungspunkten mit Durchhang, warme Kugeln daran."""
    kabel = []
    for a, c in zip(punkte[:-1], punkte[1:]):
        a, c = Vector(a), Vector(c)
        n = max(3, int((c - a).length / 0.12))
        for i in range(n):
            t = i / n
            p = a.lerp(c, t)
            p.y -= durchhang * 4 * t * (1 - t)
            kabel.append(p)
    kabel.append(Vector(punkte[-1]))
    b.rohr("anthrazit", [p.to_tuple() for p in kabel], 0.005, seg=4, kappen=False)
    laenge = 0.0
    naechste = abstand * 0.5
    for p, q in zip(kabel[:-1], kabel[1:]):
        s = (q - p).length
        while laenge + s >= naechste:
            t = (naechste - laenge) / s
            m = p.lerp(q, t)
            b.kugel("licht_warm", rad, x=m.x, y=m.y - rad * 1.2, z=m.z, sy=1.2, fein=1)
            naechste += abstand
        laenge += s


def stehlampe(b, h=1.6, schirm="stoff_creme"):
    b.zylinder("anthrazit", 0.15, 0.03, seg=14, r=0.01)
    b.zylinder("anthrazit", 0.015, h - 0.3, y=0.03, seg=6)
    b.kugel("licht_lampe", 0.07, y=h - 0.2, fein=1)
    b.dreh(schirm, [(0.24, h - 0.36), (0.16, h), (0.15, h - 0.01), (0.23, h - 0.35)], seg=14, geschlossen=True)


def tischlampe(b, schirm="stoff_creme", h=0.4):
    b.zylinder("metall_dunkel", 0.07, 0.025, seg=10, r=0.008)
    b.zylinder("metall_dunkel", 0.01, h * 0.55, y=0.025, seg=6)
    b.kugel("licht_lampe", 0.04, y=h * 0.62, fein=1)
    b.dreh(schirm, [(0.13, h * 0.5), (0.09, h), (0.085, h - 0.005), (0.125, h * 0.5 + 0.005)], seg=12, geschlossen=True)


def tasse(b, mat="weiss", x=0.0, y=0.0, z=0.0):
    b.dreh(mat, [(0.0, 0.0), (0.035, 0.0), (0.04, 0.09), (0.034, 0.09), (0.0, 0.08)], x=x, y=y, z=z, seg=8)


# =============================================================================
# Moebel
# =============================================================================

def buecherregal(b, rng, w=1.5, h=1.8, d=0.34, mat="holz_mittel", faecher=5, deko=True):
    s = 0.04
    b.kasten(mat, s, h, d, x=-w / 2 + s / 2, r=0.0)
    b.kasten(mat, s, h, d, x=w / 2 - s / 2, r=0.0)
    b.kasten(mat, w + 0.02, s, d + 0.01, y=h - s, r=0.0)
    b.kasten(mat, w - 2 * s, 0.08, d - 0.02, y=0.0, r=0.0)
    b.kasten("holz_dunkel", w - 2 * s, h - 0.1, 0.015, y=0.06, z=-d / 2 + 0.01, r=0.0)
    innen = w - 2 * s
    fach_h = (h - 0.08 - s) / faecher
    for i in range(faecher):
        y0 = 0.08 + i * fach_h
        if i > 0:
            b.kasten(mat, innen, 0.025, d - 0.03, y=y0 - 0.025, r=0.0)
        art = (i * 7 + rng.randint(0, 2)) % 4
        x0 = -innen / 2 + 0.02
        if deko and art == 3:
            buecherreihe(b, rng, innen * 0.45, fach_h - 0.07, 0.22, x0=x0, y=y0, z=0.0)
            vase = rng.choice(["topf_terra", "stoff_petrol", "weiss"])
            b.dreh(vase, [(0.0, 0.0), (0.05, 0.0), (0.065, 0.1), (0.03, 0.18), (0.0, 0.18)], x=innen * 0.25, y=y0, seg=7)
            b.kugel("pflanze", 0.06, x=innen * 0.25, y=y0 + 0.22, sy=0.9, fein=1)
        elif deko and art == 1:
            buecherstapel(b, rng, 3, x=-innen * 0.3, y=y0, z=0.02)
            buecherreihe(b, rng, innen * 0.5, fach_h - 0.07, 0.22, x0=-innen * 0.05, y=y0, z=0.0, kippen=False)
        else:
            buecherreihe(b, rng, innen * rng.uniform(0.6, 0.9), fach_h - 0.07, 0.22, x0=x0, y=y0, z=0.0)


def sessel(b, stoff="stoff_senf", holz="holz_dunkel"):
    for sx in (-0.3, 0.3):
        for sz in (-0.28, 0.28):
            b.zylinder(holz, 0.025, 0.14, x=sx, z=sz, seg=6, rad_oben=0.018)
    b.kasten(stoff, 0.78, 0.22, 0.74, y=0.12, r=0.06, seg=2)
    b.kasten(stoff, 0.78, 0.55, 0.2, y=0.3, z=-0.28, rx=-8, r=0.08, seg=2)
    for sx in (-0.33, 0.33):
        b.kasten(stoff, 0.14, 0.26, 0.66, x=sx, y=0.3, z=0.02, r=0.06)
    b.kasten("stoff_creme", 0.52, 0.1, 0.55, y=0.32, z=0.05, r=0.045, seg=2)


def beistelltisch(b, mat="holz_mittel", h=0.5):
    b.zylinder("anthrazit", 0.16, 0.02, seg=10, r=0.008)
    b.zylinder("anthrazit", 0.02, h - 0.04, y=0.02, seg=6)
    b.zylinder(mat, 0.24, 0.035, y=h - 0.035, seg=16, r=0.012)


def tv_board(b, rng, breite=1.8, tiefe=0.45, hoehe=0.42, mat="holz_hell"):
    for sx in (-breite / 2 + 0.08, breite / 2 - 0.08):
        for sz in (-tiefe / 2 + 0.07, tiefe / 2 - 0.07):
            b.zylinder("holz_dunkel", 0.022, 0.1, x=sx, z=sz, seg=6)
    b.kasten(mat, breite, hoehe - 0.1, tiefe, y=0.1, r=0.02)
    for i, fx in enumerate((-breite / 3, 0.0, breite / 3)):
        b.kasten("holz_mittel" if i != 1 else "weiss", breite / 3 - 0.04, hoehe - 0.18, 0.012,
                 x=fx, y=0.14, z=tiefe / 2, r=0.0)
        b.kasten("metall_dunkel", 0.12, 0.018, 0.02, x=fx, y=hoehe - 0.1, z=tiefe / 2 + 0.01, r=0.0)


def fernseher(b, breite=1.3, hoehe=0.74):
    b.kasten("metall_dunkel", 0.36, 0.015, 0.2, r=0.006)
    b.kasten("metall_dunkel", 0.06, 0.08, 0.04, y=0.01, z=-0.02, r=0.0)
    b.kasten("schwarz", breite, hoehe, 0.05, y=0.06, z=-0.02, r=0.015)
    b.kasten("bildschirm", breite - 0.05, hoehe - 0.05, 0.006, y=0.085, z=0.006, r=0.0)
    b.kasten("anthrazit", breite * 0.6, hoehe * 0.55, 0.05, y=0.06 + hoehe * 0.2, z=-0.07, r=0.02)


def plattenschrank(b, rng, w=1.0, h=0.55, d=0.4):
    """Niedriger Schrank mit Plattenspieler und Plattenkiste."""
    for sx in (-w / 2 + 0.06, w / 2 - 0.06):
        b.kasten("holz_dunkel", 0.04, 0.12, d - 0.06, x=sx, r=0.0)
    b.kasten("holz_rot", w, h - 0.12, d, y=0.12, r=0.02)
    b.kasten("holz_dunkel", w - 0.08, 0.02, d - 0.04, y=0.3, z=0.01, r=0.0)
    for i in range(7):
        b.kasten(rng.choice(["buch_blau", "schwarz", "buch_rot", "stoff_senf"]), 0.02, 0.2, 0.28,
                 x=-w / 2 + 0.1 + i * 0.045, y=0.32, z=0.02, rz=rng.uniform(-6, 6), r=0.0)
    with b.an(x=0.18, y=h):
        b.kasten("weiss", 0.4, 0.09, 0.32, r=0.02)
        b.zylinder("schwarz", 0.13, 0.012, y=0.09, seg=14)
        b.zylinder("buch_rot", 0.04, 0.014, y=0.09, seg=8)
        b.rohr("metall", [(0.15, 0.12, -0.1), (0.15, 0.12, 0.05), (0.08, 0.11, 0.1)], 0.008, seg=4)


def korb_mit_decke(b, decke="stoff_terracotta"):
    b.dreh("rattan", [(0.0, 0.0), (0.2, 0.0), (0.24, 0.34), (0.22, 0.34), (0.18, 0.03), (0.0, 0.03)],
           seg=12, geschlossen=False)
    b.kugel(decke, 0.2, y=0.34, sy=0.45, fein=2)
    b.kasten("stoff_creme", 0.18, 0.2, 0.08, y=0.32, x=0.08, z=0.02, rz=-20, r=0.03)


def konsole_stehend(b):
    b.kasten("weiss", 0.1, 0.34, 0.26, r=0.03)
    b.kasten("schwarz", 0.04, 0.33, 0.24, y=0.005, r=0.0)
    b.kasten("bildschirm_an", 0.012, 0.012, 0.01, x=0.03, y=0.3, z=0.131, r=0.0)


def sideboard(b, rng, w=1.4, h=0.62, d=0.42, mat="weiss"):
    for sx in (-w / 2 + 0.08, w / 2 - 0.08):
        for sz in (-d / 2 + 0.07, d / 2 - 0.07):
            b.zylinder("holz_dunkel", 0.022, 0.16, x=sx, z=sz, seg=6, rad_oben=0.015)
    b.kasten(mat, w, h - 0.16, d, y=0.16, r=0.025)
    b.kasten("holz_mittel", w + 0.02, 0.035, d + 0.02, y=h - 0.01, r=0.012)
    for i in range(3):
        fx = -w / 3 + i * w / 3
        b.kasten("holz_hell" if i == 1 else mat, w / 3 - 0.03, h - 0.24, 0.012, x=fx, y=0.2, z=d / 2, r=0.0)
        b.kugel("holz_dunkel", 0.02, x=fx + (0.12 if i != 1 else 0.0), y=h * 0.62, z=d / 2 + 0.02, fein=1)


# =============================================================================
# Wohnzimmer -- 9 x 6, Ursprung Zonenmitte. Frei: Station x -1,9..0,9 / z -1,4..1,0,
# Tuergaenge vorn (x -2) und rechts (z 1,5).
# =============================================================================

def einrichtung_wohnzimmer(b):
    rng = random.Random(31)
    # Grosser flacher Teppich -- reicht unter die Station und bis vor den Fernseher
    teppich(b, 5.0, 3.3, x=0.45, z=-0.4, grund="teppich_beige", rand="teppich_grau")

    # TV-Board an der rechten (halben) Wand, blickt nach -x zum Sofa.
    # Oberkante Fernseher 1,17 m -- unter der Wandkappe (1,2 m).
    with b.an(x=4.0, z=-0.6, ry=-90):
        tv_board(b, rng)
        with b.an(y=0.42, z=-0.05):
            fernseher(b)
        with b.an(x=0.8, y=0.42, z=-0.12):
            konsole_stehend(b)
        with b.an(x=-0.8, y=0.42, z=-0.1):
            pflanze_klein(b, rng, rad=0.08, mat_topf="topf_terra")

    # Rueckwand (voll): Buecherregal zwischen den Fenstern, Pflanzen auf den Baenken
    with b.an(z=-2.9 + 0.17):
        buecherregal(b, rng, w=1.5, h=1.85, d=0.34)
    with b.an(x=-0.45, y=1.85, z=-2.75):
        pflanze_klein(b, rng, rad=0.1, mat_topf="topf_terra")
    for fx in (-2.0, 2.0):
        with b.an(x=fx, z=-2.9):
            fensterbank(b)
            with b.an(x=-0.28, y=FENSTERBANK_Y, z=0.065):
                pflanze_klein(b, rng, rad=0.08, mat_topf="topf_terra")
            with b.an(x=0.26, y=FENSTERBANK_Y, z=0.065):
                pflanze_klein(b, rng, rad=0.065, mat_topf="topf_weiss", gruen="pflanze_dunkel")
    with b.an(x=-1.1, z=-2.5):
        pflanze_busch(b, rng, h=1.05, rad_topf=0.2, mat_topf="topf_grau")
    with b.an(x=-3.3, y=1.25, z=-2.9):
        bild(b, 0.7, 0.9, "sonne", rahmen="holz_dunkel")
    with b.an(x=2.0, z=-2.9 + 0.21):
        plattenschrank(b, rng)
    with b.an(x=1.7, y=0.55, z=-2.62):
        pflanze_klein(b, rng, rad=0.085, mat_topf="topf_weiss")

    # Leseecke hinten links: Stehlampe, Sessel, Beistelltisch, Pouf
    with b.an(x=-4.0, z=-2.55):
        stehlampe(b)
    with b.an(x=-3.35, z=-1.95, ry=45):
        sessel(b)
    with b.an(x=-3.98, z=-1.1):
        beistelltisch(b)
        tasse(b, "stoff_terracotta", x=0.08, y=0.5, z=0.05)
        buecherstapel(b, rng, 2, x=-0.05, y=0.5, z=-0.04, ry=20)
    b.kugel("stoff_salbei", 0.26, x=-2.55, y=0.17, z=-2.45, sy=0.66, fein=2)

    # Linke Wand (voll): Fenster mit Pflanze, Sideboard mit zwei Bildern
    with b.an(x=-4.4, z=-0.5, ry=90):
        fensterbank(b)
        with b.an(x=0.2, y=FENSTERBANK_Y, z=0.065):
            pflanze_klein(b, rng, rad=0.08, mat_topf="topf_weiss")
        with b.an(x=-0.25, y=FENSTERBANK_Y, z=0.065):
            pflanze_klein(b, rng, rad=0.065, mat_topf="topf_terra", gruen="pflanze_hell")
    with b.an(x=-4.4 + 0.22, z=1.62, ry=90):
        sideboard(b, rng)
        with b.an(x=-0.45, y=0.64):
            pflanze_klein(b, rng, rad=0.09, mat_topf="topf_grau")
        buecherstapel(b, rng, 3, x=0.1, y=0.64, z=0.0, ry=8)
        b.dreh("stoff_petrol", [(0.0, 0.0), (0.06, 0.0), (0.08, 0.12), (0.035, 0.24), (0.04, 0.28), (0.0, 0.27)],
               x=0.48, y=0.64, seg=10)
    with b.an(x=-4.4, z=1.2, y=1.05, ry=90):
        bild(b, 0.6, 0.8, "berge")
    with b.an(x=-4.4, z=2.05, y=1.2, ry=90):
        bild(b, 0.62, 0.5, "bloecke", rahmen="weiss")

    # Grosse Zimmerpflanze hinten rechts neben dem Fernseher, Pflanzen vorn
    with b.an(x=3.72, z=-2.35):
        pflanze_blatt(b, rng, h=1.55, rad_topf=0.22, mat_topf="topf_weiss", blaetter=10)
    # Vorn liegt alles hinter der halben Wand im Sichtschatten -- dort nur
    # eine hohe Pflanze, die ueber die Kappe schaut.
    with b.an(x=-3.8, z=2.35):
        pflanze_blatt(b, rng, h=1.7, rad_topf=0.2, mat_topf="topf_terra", blaetter=9)
    with b.an(x=-2.5, z=-1.55, ry=15):
        korb_mit_decke(b)
    # Standlautsprecher links und rechts vom TV-Board
    for lz in (-1.75, 0.55):
        with b.an(x=4.08, z=lz, ry=-90):
            b.kasten("holz_dunkel", 0.24, 0.95, 0.26, r=0.02)
            b.zylinder("schwarz", 0.07, 0.01, y=0.7, z=0.13, rx=90, seg=10)
            b.zylinder("schwarz", 0.045, 0.01, y=0.38, z=0.13, rx=90, seg=10)


# =============================================================================
# Balkon -- 4 x 6. Gelaender hinten und rechts, halbe Wand links, vorn halb mit
# Glastuer bei x -0,5. Frei: Tuergang.
# =============================================================================

def kraut(b, rng, x=0.0, y=0.0, z=0.0):
    with b.an(x=x, y=y, z=z):
        b.dreh(rng.choice(["topf_terra", "topf_weiss"]),
               [(0.0, 0.0), (0.045, 0.0), (0.06, 0.1), (0.065, 0.11), (0.0, 0.1)], seg=7)
        b.kugel(rng.choice(["pflanze_hell", "pflanze"]), rng.uniform(0.07, 0.085),
                x=rng.uniform(-0.015, 0.015), y=0.17, z=rng.uniform(-0.015, 0.015), sy=1.1, fein=1)


def klappstuhl(b, holz="holz_mittel", kissen=None):
    for sx in (-0.2, 0.2):
        b.kasten("anthrazit", 0.025, 0.5, 0.025, x=sx, z=0.02, rx=22, r=0.0)
        b.kasten("anthrazit", 0.025, 0.5, 0.025, x=sx, z=0.02, rx=-22, r=0.0)
        b.kasten("anthrazit", 0.025, 0.5, 0.025, x=sx, y=0.44, z=-0.2, rx=-10, r=0.0)
    for i in range(3):
        b.kasten(holz, 0.46, 0.025, 0.11, y=0.44, z=-0.13 + i * 0.13, r=0.008)
    for i in range(2):
        b.kasten(holz, 0.46, 0.09, 0.022, y=0.62 + i * 0.13, z=-0.21 - i * 0.02, rx=-10, r=0.008)
    if kissen:
        b.kasten(kissen, 0.38, 0.06, 0.36, y=0.465, z=0.0, r=0.03, seg=2)


def bistrotisch(b, h=0.72):
    b.zylinder("anthrazit", 0.2, 0.025, seg=12, r=0.01)
    b.zylinder("anthrazit", 0.022, h - 0.05, y=0.025, seg=6)
    b.zylinder("anthrazit", 0.34, 0.03, y=h - 0.03, seg=18, r=0.012)


def laterne(b, h=0.46):
    b.kasten("schwarz", 0.24, 0.04, 0.24, r=0.012)
    for sx in (-0.1, 0.1):
        for sz in (-0.1, 0.1):
            b.kasten("schwarz", 0.022, h - 0.12, 0.022, x=sx, y=0.04, z=sz, r=0.0)
    b.kasten("schwarz", 0.25, 0.03, 0.25, y=h - 0.09, r=0.01)
    b.dreh("schwarz", [(0.18, h - 0.06), (0.0, h + 0.02)], seg=4, versatz=math.pi / 4)
    b.dreh("schwarz", [(0.0, h - 0.06), (0.18, h - 0.06)], seg=4, versatz=math.pi / 4)
    b.rohr("schwarz", [(0.0, h + 0.02, 0.0), (-0.05, h + 0.06, 0.0), (0.0, h + 0.11, 0.0), (0.05, h + 0.06, 0.0),
                       (0.0, h + 0.02, 0.0)], 0.009, seg=4)
    b.zylinder("stoff_weiss", 0.045, 0.14, y=0.04, seg=8)
    b.kugel("licht_warm", 0.05, y=0.23, sy=1.4, fein=1)


def giesskanne(b):
    b.dreh("stoff_petrol", [(0.0, 0.0), (0.1, 0.0), (0.1, 0.22), (0.07, 0.25), (0.0, 0.25)], seg=10)
    b.rohr("stoff_petrol", [(0.08, 0.05, 0.0), (0.2, 0.2, 0.0), (0.26, 0.28, 0.0)], 0.018, seg=5)
    b.rohr("stoff_petrol", [(-0.09, 0.2, 0.0), (-0.14, 0.26, 0.0), (-0.06, 0.32, 0.0), (0.05, 0.26, 0.0)], 0.013, seg=4)


def pflanzkasten(b, rng, laenge=1.3, breite=0.32, h=0.4, mat="holz_dunkel", blueten=("blume_rosa", "blume_weiss")):
    """Langer Pflanzkasten entlang lokal z, mit Blumenbuescheln."""
    b.kasten(mat, breite, h, laenge, r=0.02)
    b.kasten("erde", breite - 0.06, 0.02, laenge - 0.06, y=h - 0.03, r=0.0)
    n = max(2, int(laenge / 0.36))
    for i in range(n):
        z = -laenge / 2 + laenge * (i + 0.5) / n
        b.kugel(["pflanze", "pflanze_hell", "pflanze_dunkel"][i % 3], 0.17, y=h + 0.08, z=z, sy=0.85, fein=2)
        for k in range(2):
            a = rng.uniform(0, 2 * math.pi)
            b.kugel(blueten[(i + k) % len(blueten)], 0.048, x=math.cos(a) * 0.12, y=h + 0.12 + rng.uniform(0, 0.08),
                    z=z + math.sin(a) * 0.12, fein=1)


def einrichtung_balkon(b):
    rng = random.Random(42)
    teppich(b, 1.9, 1.9, x=0.35, z=-0.85, grund="teppich_gruen", rand="stoff_creme", rund=True)

    # Kleiner Lieblingsort: Bistrotisch mit zwei Klappstuehlen
    with b.an(x=0.35, z=-0.85):
        bistrotisch(b)
        tasse(b, "stoff_senf", x=-0.1, y=0.72, z=0.08)
        tasse(b, "weiss", x=0.12, y=0.72, z=-0.06)
        with b.an(x=0.0, y=0.72, z=-0.18):
            pflanze_klein(b, rng, rad=0.06, mat_topf="topf_terra")
    with b.an(x=-0.4, z=-0.75, ry=90):
        klappstuhl(b, kissen="stoff_senf")
    with b.an(x=0.55, z=-1.7, ry=-15):
        klappstuhl(b)

    # Pflanzkuebel in den Ecken und am Gelaender
    with b.an(x=-1.45, z=-2.45):
        b.kasten("holz_dunkel", 0.62, 0.5, 0.62, r=0.025)
        for i in range(3):
            b.kasten("holz_mittel", 0.64, 0.1, 0.64, y=0.06 + i * 0.15, r=0.02)
        b.kasten("erde", 0.54, 0.02, 0.54, y=0.47, r=0.0)
        with b.an(y=0.46):
            pflanze_blatt(b, rng, h=1.1, rad_topf=0.24, mat_topf=None, blaetter=11, max_rad=0.45)
    with b.an(x=-1.55, z=-1.35):
        pflanze_busch(b, rng, h=0.7, rad_topf=0.17, mat_topf="topf_weiss", blueten=("blume_lila",))
    with b.an(x=1.5, z=-2.45):
        pflanze_busch(b, rng, h=1.15, rad_topf=0.26, mat_topf="topf_grau",
                      blueten=("blume_rosa", "blume_weiss", "blume_gelb"))
    with b.an(x=1.68, z=0.35):
        pflanzkasten(b, rng, laenge=1.6, blueten=("blume_rosa", "blume_lila", "blume_weiss"))
    with b.an(x=1.45, z=1.75):
        pflanze_busch(b, rng, h=0.95, rad_topf=0.2, mat_topf="topf_terra", blueten=("blume_orange", "blume_gelb"))

    # Kraeuterregal an der halben Wand links (Hoehe 1,05 -- unter der Kappe)
    with b.an(x=-1.9 + 0.17, z=0.2, ry=90):
        for sx in (-0.38, 0.38):
            b.kasten("holz_mittel", 0.035, 1.05, 0.32, x=sx, r=0.01)
        for i, yy in enumerate((0.12, 0.5, 0.88)):
            b.kasten("holz_mittel", 0.74, 0.03, 0.3, y=yy, r=0.0)
            for k in range(3 if i == 0 else 2):
                kraut(b, rng, x=-0.24 + k * 0.24 + (0.12 if i > 0 else 0.0), y=yy + 0.03, z=0.0)

    with b.an(x=-1.5, z=1.3):
        laterne(b)
    with b.an(x=-1.45, z=0.95, ry=-60):
        giesskanne(b)

    # Lichterkette entlang des Gelaenders (hinten und rechts)
    lichterkette(b, [(-1.85, 1.0, -2.9), (-0.6, 1.0, -2.9), (0.65, 1.0, -2.9), (1.9, 1.0, -2.9)],
                 durchhang=0.14, abstand=0.24)
    lichterkette(b, [(1.9, 1.0, -2.9), (1.9, 1.0, -1.75), (1.9, 1.0, -0.6), (1.9, 1.0, 0.55),
                     (1.9, 1.0, 1.7), (1.9, 1.0, 2.85)], durchhang=0.14, abstand=0.24)


# =============================================================================
# Freies Zimmer -- Moebel fuer die drei Varianten
# =============================================================================

def bett(b, rng, w=1.4, l=2.05, holz="holz_mittel", decke="stoff_blau", laken="stoff_weiss",
         kissen=("stoff_weiss",), ungemacht=False, tagesdecke=None):
    """Bett, Kopfende an -z."""
    for sx in (-w / 2 + 0.06, w / 2 - 0.06):
        for sz in (-l / 2 + 0.06, l / 2 - 0.06):
            b.kasten(holz, 0.06, 0.12, 0.06, x=sx, z=sz, r=0.0)
    b.kasten(holz, w, 0.16, l, y=0.1, r=0.02)
    b.kasten(holz, w + 0.04, 0.72, 0.07, y=0.0, z=-l / 2 - 0.02, r=0.03)
    b.kasten(laken, w - 0.08, 0.2, l - 0.1, y=0.24, z=0.02, r=0.05)
    if ungemacht:
        # zerwuehlte Decke: zwei verdrehte Lagen, ein Zipfel haengt ueber die Kante
        b.kasten(decke, w * 0.8, 0.12, l * 0.52, x=0.08, y=0.4, z=0.28, ry=8, r=0.05, seg=2)
        b.kasten(decke, w * 0.62, 0.14, l * 0.32, x=-0.12, y=0.46, z=-0.05, ry=-18, rz=6, r=0.06)
        b.kasten(decke, 0.1, 0.36, l * 0.4, x=w / 2 + 0.02, y=0.12, z=0.45, rz=-8, r=0.04)
        b.kasten(kissen[0], 0.55, 0.13, 0.36, x=-0.25, y=0.43, z=-l / 2 + 0.3, ry=-20, rz=10, r=0.06)
    else:
        b.kasten(decke, w - 0.02, 0.1, l * 0.66, y=0.42, z=l * 0.16, r=0.045, seg=2)
        b.kasten(laken, w - 0.04, 0.11, 0.18, y=0.42, z=l * 0.16 - l * 0.33 - 0.02, r=0.045)
        if tagesdecke:
            b.kasten(tagesdecke, w + 0.03, 0.04, 0.45, y=0.5, z=l / 2 - 0.35, r=0.02)
            b.kasten(tagesdecke, 0.04, 0.25, 0.45, x=w / 2 + 0.01, y=0.27, z=l / 2 - 0.35, r=0.015)
        for i, k in enumerate(kissen):
            kx = (-w / 4 + i * w / 2) if len(kissen) > 1 else 0.0
            b.kasten(k, w / 2 - 0.1 if len(kissen) > 1 else w - 0.3, 0.16, 0.34,
                     x=kx, y=0.42, z=-l / 2 + 0.26, rx=-12, r=0.07)


def schreibtisch(b, w=1.5, d=0.68, h=0.75, platte="holz_hell", beine="anthrazit", schubfach=True):
    b.kasten(platte, w, 0.035, d, y=h - 0.035, r=0.012)
    for sx in (-w / 2 + 0.05, w / 2 - 0.05):
        for sz in (-d / 2 + 0.05, d / 2 - 0.05):
            if schubfach and sx > 0:
                continue
            b.kasten(beine, 0.04, h - 0.035, 0.04, x=sx, z=sz, r=0.0)
    if schubfach:
        b.kasten(platte, 0.42, h - 0.035, d - 0.04, x=w / 2 - 0.23, r=0.015)
        for i in range(3):
            b.kasten("weiss", 0.38, 0.19, 0.012, x=w / 2 - 0.23, y=0.05 + i * 0.22, z=d / 2 - 0.01, r=0.0)
            b.kasten(beine, 0.1, 0.015, 0.02, x=w / 2 - 0.23, y=0.2 + i * 0.22, z=d / 2 + 0.005, r=0.0)


def monitor(b, breite=0.62, hoehe=0.36):
    b.kasten("metall_dunkel", 0.22, 0.015, 0.16, r=0.005)
    b.kasten("metall_dunkel", 0.04, 0.2, 0.03, y=0.01, z=-0.04, r=0.0)
    b.kasten("schwarz", breite, hoehe, 0.035, y=0.12, z=-0.03, r=0.012)
    b.kasten("bildschirm_an", breite - 0.04, hoehe - 0.04, 0.005, y=0.14, z=-0.01, r=0.0)
    b.kasten("anthrazit", 0.46, 0.02, 0.15, z=0.25, r=0.006)
    b.kugel("anthrazit", 0.03, x=0.33, y=0.015, z=0.25, sy=0.5, sz=1.4, fein=1)


def gamingstuhl(b, akzent="stoff_rot"):
    """Vorderseite +z, Lehne hinten."""
    for i in range(5):
        a = 90 + i * 72
        b.kasten("schwarz", 0.05, 0.035, 0.3, x=math.sin(math.radians(a)) * 0.13, y=0.06,
                 z=math.cos(math.radians(a)) * 0.13, ry=a, r=0.0)
        b.kugel("schwarz", 0.035, x=math.sin(math.radians(a)) * 0.28, y=0.035,
                z=math.cos(math.radians(a)) * 0.28, fein=1)
    b.zylinder("metall", 0.025, 0.36, y=0.08, seg=6)
    b.kasten("schwarz", 0.54, 0.1, 0.52, y=0.42, r=0.045, seg=2)
    b.kasten(akzent, 0.3, 0.02, 0.44, y=0.515, r=0.0)
    with b.an(y=0.46, z=-0.27, rx=-10):
        b.kasten("schwarz", 0.52, 0.82, 0.12, r=0.05, seg=2)
        b.kasten(akzent, 0.1, 0.72, 0.02, x=-0.15, y=0.04, z=0.06, r=0.0)
        b.kasten(akzent, 0.1, 0.72, 0.02, x=0.15, y=0.04, z=0.06, r=0.0)
        b.kasten(akzent, 0.28, 0.12, 0.05, y=0.62, z=0.07, r=0.025)
    for sx in (-0.29, 0.29):
        b.kasten("schwarz", 0.04, 0.2, 0.04, x=sx, y=0.5, r=0.0)
        b.kasten("anthrazit", 0.07, 0.03, 0.26, x=sx, y=0.7, r=0.012)


def sitzsack(b, farbe_sack="stoff_senf"):
    b.kugel(farbe_sack, 0.42, y=0.2, sy=0.55, fein=2)
    b.kugel(farbe_sack, 0.32, y=0.42, z=-0.2, sy=0.75, sz=0.7, fein=2)


def gitarre(b):
    """Akustikgitarre, Decke +z, Hals nach +y."""
    b.kugel("holz_hell", 0.2, y=0.22, sz=0.25, fein="uv")
    b.kugel("holz_hell", 0.155, y=0.48, sz=0.3, fein="uv")
    b.zylinder("schwarz", 0.055, 0.02, y=0.36, z=0.035, rx=90, seg=10)
    b.kasten("holz_dunkel", 0.14, 0.025, 0.02, y=0.18, z=0.045, r=0.0)
    b.kasten("holz_dunkel", 0.055, 0.5, 0.035, y=0.6, r=0.0)
    b.kasten("schwarz", 0.08, 0.16, 0.035, y=1.08, r=0.01)


def poster(b, w, h, motiv, rahmen="schwarz"):
    """Angelehnt: Unterkante vorn, oben zur Wand (-z) gekippt."""
    with b.an(rx=-11):
        bild(b, w, h, motiv, rahmen=rahmen, t=0.025)


def waeschehaufen(b, rng):
    farben = ["stoff_rot", "stoff_jeans", "stoff_grau", "stoff_weiss", "stoff_petrol", "schwarz"]
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.0, 0.25)
        b.kugel(farben[i], rng.uniform(0.16, 0.24), x=math.cos(a) * d, y=0.05 + i * 0.02, z=math.sin(a) * d,
                sx=rng.uniform(1.0, 1.5), sy=0.3, ry=rng.uniform(0, 180), fein="uv")
    b.kasten("stoff_jeans", 0.14, 0.04, 0.5, x=0.3, y=0.0, z=0.1, ry=35, r=0.02)


def minikuehlschrank(b):
    b.kasten("weiss", 0.48, 0.62, 0.5, r=0.035)
    b.kasten("grau_hell", 0.46, 0.008, 0.012, y=0.5, z=0.25, r=0.0)
    b.kasten("metall", 0.03, 0.2, 0.03, x=0.18, y=0.25, z=0.26, r=0.0)
    b.kasten("buch_gruen", 0.1, 0.1, 0.005, x=-0.1, y=0.3, z=0.25, ry=0, r=0.0)
    for i, m in enumerate(("stoff_petrol", "buch_gelb")):
        b.zylinder(m, 0.033, 0.13, x=-0.1 + i * 0.1, y=0.62, z=0.05, seg=8)


def hantel(b, x=0.0, z=0.0, ry=0.0):
    with b.an(x=x, z=z, ry=ry):
        b.zylinder("metall", 0.015, 0.34, x=-0.17, y=0.07, rz=-90, seg=6)
        for sx in (-0.12, 0.12):
            b.zylinder("schwarz", 0.07, 0.06, x=sx - 0.03, y=0.07, rz=-90, seg=10, r=0.01)


def pizzakarton(b, rng, n=2):
    for i in range(n):
        with b.an(y=i * 0.045, ry=rng.uniform(-15, 15)):
            b.kasten("karton", 0.36, 0.045, 0.36, r=0.008)
            b.zylinder("stoff_rot", 0.07, 0.005, y=0.045, seg=8)


def wuerfelregal(b, rng, spalten=3, reihen=2, fach=0.38, d=0.38, mat="weiss"):
    """Wuerfelregal, gefuellt mit Kisten, Spielen und Kleinkram."""
    s = 0.03
    w, h = spalten * fach + s, reihen * fach + s
    for i in range(spalten + 1):
        b.kasten(mat, s, h, d, x=-w / 2 + s / 2 + i * fach, r=0.0 if 0 < i < spalten else 0.01)
    for k in range(reihen + 1):
        b.kasten(mat, w, s, d, y=k * fach, r=0.0 if 0 < k < reihen else 0.01)
    inhalt = ["kiste", "spiele", "figur", "kiste_b", "buecher", "leer"]
    rng.shuffle(inhalt)
    for i in range(spalten):
        for k in range(reihen):
            cx, cy = -w / 2 + s + fach / 2 + i * fach - s / 2, k * fach + s
            art = inhalt[(i + k * spalten) % len(inhalt)]
            if art in ("kiste", "kiste_b"):
                b.kasten("stoff_grau" if art == "kiste" else "rattan", fach - 0.06, fach - 0.08, d - 0.04, x=cx, y=cy,
                         r=0.02)
            elif art == "spiele":
                for j in range(5):
                    b.kasten(rng.choice(["buch_blau", "buch_rot", "schwarz", "buch_gruen"]), 0.025, 0.19, 0.14,
                             x=cx - 0.1 + j * 0.03, y=cy, r=0.0)
            elif art == "figur":
                b.zylinder("stoff_rot", 0.05, 0.14, x=cx - 0.06, y=cy, seg=8)
                b.kugel("stoff_creme", 0.055, x=cx - 0.06, y=cy + 0.19, fein=1)
                b.kugel("buch_gelb", 0.07, x=cx + 0.09, y=cy + 0.07, fein=1)
            elif art == "buecher":
                buecherreihe(b, rng, fach - 0.08, fach - 0.08, 0.22, x0=cx - fach / 2 + 0.03, y=cy, kippen=False)


def einrichtung_freies_zimmer_bewohnt(b):
    rng = random.Random(51)
    teppich(b, 2.4, 2.2, x=-2.3, z=1.6, grund="teppich_blau", rand="stoff_blau_dunkel")
    # Zockerecke: niedriges Board mit Fernseher an der linken (vollen) Wand, Sitzsack davor
    with b.an(x=-3.68, z=1.55, ry=90):
        tv_board(b, rng, breite=1.4, tiefe=0.4, hoehe=0.4, mat="schwarz")
        with b.an(y=0.4, z=-0.05):
            fernseher(b, breite=1.0, hoehe=0.58)
        with b.an(x=0.58, y=0.4, z=0.02, ry=90):
            b.kasten("schwarz", 0.3, 0.07, 0.24, r=0.02)
            b.kasten("buch_blau", 0.2, 0.004, 0.02, y=0.07, z=0.1, r=0.0)
    with b.an(x=-2.05, z=1.5, ry=-90):
        sitzsack(b, "stoff_rot")
    with b.an(x=-2.55, z=2.2, ry=30):
        b.kasten("schwarz", 0.16, 0.04, 0.1, r=0.015)
    with b.an(x=0.75, z=-3.4 + 0.2):
        wuerfelregal(b, rng)
        with b.an(x=0.3, y=0.79):
            pflanze_klein(b, rng, rad=0.09, mat_topf="topf_grau", gruen="pflanze_hell")
        tasse(b, "stoff_senf", x=-0.35, y=0.79, z=0.05)
    # Obstkiste als Nachttisch, mit Lampe und Dose
    with b.an(x=-1.95, z=-3.15):
        b.kasten("holz_hell", 0.44, 0.34, 0.34, r=0.015)
        b.kasten("holz_dunkel", 0.38, 0.26, 0.01, y=0.04, z=0.17, r=0.0)
        with b.an(x=-0.08, y=0.34):
            tischlampe(b, schirm="anthrazit", h=0.36)
        b.zylinder("stoff_petrol", 0.033, 0.13, x=0.12, y=0.34, z=0.06, seg=8)
    # Ungemachtes Bett hinten links, Kopfende an der Rueckwand
    with b.an(x=-3.0, z=-3.4 + 1.05):
        bett(b, rng, decke="stoff_petrol", kissen=("stoff_weiss",), ungemacht=True, holz="holz_dunkel")
    with b.an(x=-1.7, z=-0.75):
        waeschehaufen(b, rng)
    with b.an(x=-1.55, z=0.55):
        pizzakarton(b, rng)
    # Schreibtisch mit Monitor hinten rechts, Gaming-Stuhl davor
    with b.an(x=2.15, z=-3.4 + 0.36):
        schreibtisch(b, w=1.6, platte="schwarz", beine="metall_dunkel")
        with b.an(y=0.75, z=-0.1):
            monitor(b, breite=0.7, hoehe=0.38)
        tasse(b, "stoff_rot", x=-0.6, y=0.75, z=0.15)
        b.zylinder("buch_gelb", 0.033, 0.13, x=0.55, y=0.75, z=0.12, seg=8)
        b.zylinder("stoff_petrol", 0.033, 0.13, x=0.62, y=0.0, z=0.45, rz=90, seg=8)
    with b.an(x=2.05, z=-2.3, ry=165):
        gamingstuhl(b)
        b.kasten("stoff_rot", 0.5, 0.25, 0.08, y=0.95, z=-0.36, rx=-10, r=0.04)  # Hoodie ueber der Lehne
    with b.an(x=3.55, z=-3.12):
        minikuehlschrank(b)
    # Rechte Wand: angelehnte Poster; Hanteln mitten im Weg
    with b.an(x=3.7, z=-1.5, ry=-90):
        poster(b, 0.62, 0.88, "welle")
    with b.an(x=3.62, z=-0.65, ry=-90):
        poster(b, 0.5, 0.7, "bloecke", rahmen="weiss")
    hantel(b, x=0.4, z=0.2, ry=20)
    hantel(b, x=0.65, z=0.45, ry=-35)
    # Linke Wand: Gitarre neben dem Fenster, Kaktus auf der Fensterbank, Poster an der Wand
    with b.an(x=-3.55, z=2.9, ry=90, rx=-14):
        gitarre(b)
    with b.an(x=-3.9, z=0.0, ry=90):
        fensterbank(b)
        with b.an(x=0.15, y=FENSTERBANK_Y, z=0.065):
            b.dreh("topf_terra", [(0.0, 0.0), (0.05, 0.0), (0.065, 0.1), (0.0, 0.09)], seg=8)
            b.dreh("pflanze", [(0.0, 0.09), (0.045, 0.1), (0.05, 0.2), (0.03, 0.27), (0.0, 0.28)], seg=8)
    with b.an(x=-3.9, y=1.1, z=-1.9, ry=90):
        bild(b, 0.6, 0.85, "sonne", rahmen="schwarz", t=0.015)
    with b.an(x=-3.5, z=0.68):
        stehlampe(b, h=1.5, schirm="anthrazit")
    # Skateboard mitten im Zimmer, Waeschestaender mit Shirts
    with b.an(x=0.9, z=2.0, ry=-25):
        b.kasten("stoff_senf", 0.22, 0.02, 0.8, y=0.07, r=0.01)
        for sz in (-0.25, 0.25):
            b.kasten("metall", 0.16, 0.03, 0.04, y=0.04, z=sz, r=0.0)
            for sx in (-0.08, 0.08):
                b.zylinder("weiss", 0.03, 0.03, x=sx - 0.015, y=0.03, z=sz, rz=-90, seg=6)
    with b.an(x=1.9, z=0.9, ry=30):
        for sx in (-0.45, 0.45):
            b.kasten("metall", 0.025, 0.95, 0.025, x=sx, z=0.2, rx=-12, r=0.0)
            b.kasten("metall", 0.025, 0.95, 0.025, x=sx, z=-0.2, rx=12, r=0.0)
        for sz in (-0.08, 0.0, 0.08):
            b.kasten("metall", 0.9, 0.015, 0.015, y=0.92, z=sz, r=0.0)
        for i, (m, sx) in enumerate((("stoff_rot", -0.25), ("stoff_weiss", 0.05), ("stoff_jeans", 0.3))):
            b.kasten(m, 0.26, 0.4 - 0.08 * i, 0.03, x=sx, y=0.52 + 0.08 * i, z=-0.08 + 0.08 * i, r=0.012)


def bettgestell(b, w=1.4, l=2.05, holz="holz_dunkel"):
    for sx in (-w / 2 + 0.05, w / 2 - 0.05):
        for sz in (-l / 2 + 0.05, l / 2 - 0.05):
            b.kasten(holz, 0.07, 0.3, 0.07, x=sx, z=sz, r=0.0)
    for sx in (-w / 2 + 0.03, w / 2 - 0.03):
        b.kasten(holz, 0.06, 0.14, l, x=sx, y=0.14, r=0.015)
    for sz in (-l / 2 + 0.03, l / 2 - 0.03):
        b.kasten(holz, w, 0.14, 0.06, y=0.14, z=sz, r=0.015)
    for i in range(8):
        b.kasten("holz_hell", w - 0.12, 0.02, 0.09, y=0.22, z=-l / 2 + 0.2 + i * (l - 0.4) / 7, r=0.0)
    b.kasten(holz, w + 0.04, 0.72, 0.07, z=-l / 2 - 0.02, r=0.03, seg=2)


def teppichrolle(b, laenge=1.8, rad=0.14):
    """Aufgerollter Teppich, liegt entlang lokal x."""
    b.zylinder("teppich_rosa", rad, laenge, x=-laenge / 2, y=rad, rz=-90, seg=12, r=0.03)
    for sx in (-laenge * 0.3, laenge * 0.3):
        b.zylinder("holz_hell", rad + 0.01, 0.03, x=sx - 0.015, y=rad, rz=-90, seg=12)
    b.zylinder("stoff_terracotta", rad * 0.6, 0.01, x=laenge / 2, y=rad, rz=-90, seg=10)


def lampe_ohne_schirm(b, h=1.55):
    b.zylinder("anthrazit", 0.17, 0.035, seg=12, r=0.012)
    b.zylinder("anthrazit", 0.022, h - 0.12, y=0.03, seg=6)
    b.zylinder("metall_dunkel", 0.045, 0.08, y=h - 0.12, seg=8)
    b.kugel("licht_lampe", 0.08, y=h + 0.02, sy=1.25, fein=2)
    b.rohr("schwarz", [(0.0, 0.02, 0.0), (0.25, 0.01, 0.1), (0.6, 0.01, 0.05)], 0.008, seg=4)


def besen(b):
    """Lehnt: Stiel nach +y, gekippt wird von aussen."""
    b.zylinder("holz_hell", 0.014, 1.2, y=0.12, seg=6)
    b.kasten("stoff_rot", 0.3, 0.06, 0.07, y=0.09, r=0.015)
    b.kasten("stoff_senf", 0.28, 0.1, 0.05, y=0.0, r=0.0)


def socke(b):
    b.kasten("weiss", 0.09, 0.03, 0.24, r=0.013)
    b.kasten("weiss", 0.09, 0.03, 0.14, x=0.0, z=0.15, ry=0, r=0.013)
    b.kasten("stoff_rot", 0.092, 0.032, 0.03, z=-0.1, r=0.0)
    b.kasten("weiss", 0.09, 0.03, 0.12, x=0.05, z=0.22, ry=70, r=0.013)


def klebebandrolle(b):
    b.dreh("klebeband", [(0.05, 0.0), (0.06, 0.0), (0.06, 0.05), (0.05, 0.05)], seg=12, geschlossen=True)
    b.dreh("karton_dunkel", [(0.035, 0.0), (0.05, 0.0), (0.05, 0.05), (0.035, 0.05)], seg=12, geschlossen=True)


def einrichtung_freies_zimmer_leer(b):
    rng = random.Random(52)
    with b.an(x=-3.0, z=-3.4 + 1.05):
        bettgestell(b)
    # Kartonberg in der Mitte rechts, zweiter Stapel links
    with b.an(x=1.3, z=-0.5, ry=8):
        karton(b, 0.55, 0.42, 0.45, x=-0.3, ry=-3)
        karton(b, 0.52, 0.44, 0.44, x=0.3, z=0.05, ry=5, mat="karton_dunkel", etikett=False)
        karton(b, 0.5, 0.4, 0.42, x=0.0, z=-0.52, ry=-8)
        karton(b, 0.48, 0.38, 0.4, x=-0.22, y=0.42, z=0.02, ry=10)
        karton(b, 0.42, 0.34, 0.36, x=0.1, y=0.42, z=-0.5, ry=-14, mat="karton_dunkel")
        karton(b, 0.4, 0.32, 0.34, x=-0.18, y=0.8, z=0.0, ry=22, etikett=False)
        with b.an(x=0.1, y=0.76, z=-0.48):
            klebebandrolle(b)
    with b.an(x=-1.6, z=1.4, ry=-12):
        karton(b, 0.6, 0.46, 0.45)
        karton(b, 0.5, 0.36, 0.4, y=0.46, ry=18, mat="karton_dunkel")
    with b.an(x=-2.9, z=-0.3, ry=-8):
        karton(b, 0.5, 0.4, 0.42)
    with b.an(x=1.2, z=1.9, ry=10):
        teppichrolle(b)
    with b.an(x=2.9, z=-3.0):
        lampe_ohne_schirm(b)
    # Besen lehnt am Kartonberg, Kehrblech davor
    with b.an(x=2.05, z=-0.2, ry=100, rx=-14):
        besen(b)
    with b.an(x=2.2, z=0.25, ry=20):
        b.kasten("stoff_blau", 0.26, 0.012, 0.22, r=0.004)
        b.kasten("stoff_blau", 0.26, 0.08, 0.02, z=-0.11, r=0.004)
        b.kasten("stoff_blau", 0.04, 0.03, 0.18, y=0.05, z=-0.2, r=0.0)
    with b.an(x=-0.2, z=1.0, ry=35, s=1.3):
        socke(b)
    # Stehleiter mit Farbeimer an der rechten Wand, Muellsack neben der Tuer
    with b.an(x=3.3, z=1.3, ry=-90):
        for sz, winkel in ((-0.3, 12), (0.3, -12)):
            for sx in (-0.22, 0.22):
                b.kasten("metall", 0.04, 1.3, 0.035, x=sx, z=sz, rx=winkel, r=0.0)
        for i in range(3):
            yy = 0.33 + i * 0.3
            b.kasten("metall", 0.44, 0.03, 0.12, y=yy, z=0.3 - yy * 0.2126 - 0.02, r=0.0)
        b.kasten("metall_dunkel", 0.46, 0.05, 0.2, y=1.26, r=0.01)
    with b.an(x=2.3, z=1.0):
        b.dreh("weiss", [(0.0, 0.0), (0.13, 0.0), (0.15, 0.3), (0.0, 0.3)], seg=12)
        b.zylinder("stoff_salbei", 0.135, 0.01, y=0.3, seg=12)
        b.rohr("metall", [(-0.14, 0.28, 0.0), (0.0, 0.4, 0.0), (0.14, 0.28, 0.0)], 0.006, seg=4)
    with b.an(x=-1.6, z=-2.9):
        b.kugel("schwarz", 0.26, y=0.24, sy=0.95, fein=2)
        b.kugel("schwarz", 0.07, y=0.52, sy=1.4, fein=1)
    with b.an(x=-3.9, z=0.0, ry=90):
        fensterbank(b)


# =============================================================================
# Studio-Variante
# =============================================================================

def dreibein(b, h=1.5, spreiz=0.3, mat="schwarz"):
    for i in range(3):
        a = math.radians(i * 120 + 30)
        b.rohr(mat, [(math.cos(a) * spreiz, 0.0, math.sin(a) * spreiz), (0.0, 0.35, 0.0)], 0.012, seg=4)
    b.zylinder(mat, 0.016, h - 0.35, y=0.35, seg=6)


def greenscreen(b, w=2.4, h=2.05, vor=0.8):
    """Stoff haengt an einer Querstange zwischen zwei Staendern und laeuft
    als Hohlkehle nach vorn (+z) auf den Boden aus."""
    for sx in (-w / 2 - 0.08, w / 2 + 0.08):
        with b.an(x=sx):
            dreibein(b, h=h + 0.1, spreiz=0.25)
    b.zylinder("metall_dunkel", 0.018, w + 0.3, x=-w / 2 - 0.15, y=h + 0.02, rz=-90, seg=6)
    umriss = [(-0.01, h), (0.02, h), (0.02, 0.35)]
    for k in range(1, 5):
        a = math.radians(180 + 90 * k / 5)
        umriss.append((0.35 + 0.33 * math.cos(a), 0.35 + 0.33 * math.sin(a)))
    umriss += [(0.35, 0.02), (vor, 0.02), (vor, 0.004)]
    innen = [(0.35, 0.004)]
    for k in range(4, 0, -1):
        a = math.radians(180 + 90 * k / 5)
        innen.append((0.35 + 0.35 * math.cos(a), 0.35 + 0.35 * math.sin(a)))
    innen += [(-0.01, 0.35)]
    profil = umriss + innen
    # Profil liegt in (z, y); prisma extrudiert entlang lokal z -> um y drehen
    pkt = [(-zz, yy) for zz, yy in profil]
    b.prisma("greenscreen", pkt, w, ry=90, z=0.0)


def softbox(b):
    """Softbox auf Stativ, leuchtet nach +z."""
    dreibein(b, h=1.55, spreiz=0.28)
    with b.an(y=1.55, rx=12):
        b.dreh("schwarz", [(0.0, -0.25), (0.08, -0.25), (0.42, 0.05), (0.4, 0.06), (0.0, 0.06)],
               seg=4, versatz=math.pi / 4, rx=90)
        b.kasten("softbox", 0.54, 0.54, 0.02, y=-0.27, z=0.05, r=0.0)


def kamera_stativ(b):
    """Kamera auf Slider und Stativ, Objektiv nach +z."""
    dreibein(b, h=1.25, spreiz=0.34)
    b.kasten("metall_dunkel", 0.08, 0.04, 0.9, y=1.25, r=0.01)
    b.kasten("schwarz", 0.1, 0.04, 0.12, y=1.29, z=0.1, r=0.008)
    with b.an(y=1.33, z=0.1):
        b.kasten("schwarz", 0.2, 0.14, 0.12, r=0.02)
        b.kasten("anthrazit", 0.08, 0.05, 0.08, x=0.05, y=0.14, r=0.01)
        b.zylinder("anthrazit", 0.05, 0.14, y=0.07, z=0.06, rx=90, seg=10, r=0.01)
        b.zylinder("bildschirm_an", 0.035, 0.005, y=0.07, z=0.2, rx=90, seg=8)
        b.kasten("bildschirm", 0.14, 0.09, 0.015, x=-0.1, y=0.16, z=-0.06, ry=-20, r=0.0)


def gaestesofa(b, stoff="stoff_salbei"):
    for sx in (-0.62, 0.62):
        for sz in (-0.28, 0.28):
            b.zylinder("holz_dunkel", 0.025, 0.12, x=sx, z=sz, seg=6, rad_oben=0.018)
    b.kasten(stoff, 1.4, 0.22, 0.76, y=0.1, r=0.06, seg=2)
    b.kasten(stoff, 1.4, 0.48, 0.2, y=0.3, z=-0.28, rx=-6, r=0.07, seg=2)
    for sx in (-0.64, 0.64):
        b.kasten(stoff, 0.14, 0.34, 0.74, x=sx, y=0.2, r=0.06)
    for sx in (-0.29, 0.29):
        b.kasten(stoff, 0.56, 0.1, 0.56, x=sx, y=0.31, z=0.06, r=0.045)
    b.kasten("stoff_senf", 0.34, 0.3, 0.12, x=-0.38, y=0.42, z=-0.1, rx=-15, ry=12, r=0.06, seg=2)


def akustikpaneel(b):
    """Schaumstoff-Paneel auf zwei Fuessen, Vorderseite +z."""
    for sx in (-0.3, 0.3):
        b.kasten("schwarz", 0.06, 0.03, 0.4, x=sx, r=0.0)
        b.zylinder("metall_dunkel", 0.014, 0.35, x=sx, y=0.03, seg=6)
    b.kasten("akustik", 0.7, 1.2, 0.06, y=0.3, r=0.02)
    for i in range(4):
        for k in range(3):
            m = "akustik_hell" if (i + k) % 2 else "akustik"
            b.kasten(m, 0.2, 0.26, 0.04 if m == "akustik" else 0.06, x=-0.22 + k * 0.22, y=0.36 + i * 0.28,
                     z=0.03, r=0.0)


def neon_play(b):
    """Leuchtschild ohne Schrift: abgerundeter Rahmen mit Play-Dreieck. Rueckseite z = 0."""
    b.tafel("anthrazit", 0.9, 0.62, 0.02, rad=0.1)
    rahmen = [(u, v + 0.31, 0.04) for u, v in rundrechteck(0.78, 0.5, 0.1, 3)]
    b.rohr("neon_rosa", rahmen, 0.014, seg=5, geschlossen=True)
    dreieck = []
    ecken = [(-0.1, 0.44), (-0.1, 0.18), (0.14, 0.31)]
    for i in range(3):
        a, c = ecken[i], ecken[(i + 1) % 3]
        for t in (0.15, 0.85):
            dreieck.append((a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t, 0.04))
    b.rohr("neon_rosa", dreieck, 0.016, seg=5, geschlossen=True)


def regal_requisiten(b, rng, w=1.2, h=1.0, d=0.36):
    s = 0.035
    for sx in (-w / 2 + s / 2, w / 2 - s / 2):
        b.kasten("weiss", s, h, d, x=sx, r=0.0)
    for yy in (0.0, h * 0.48, h - s):
        b.kasten("weiss", w, s, d, y=yy, r=0.01 if yy > h * 0.5 else 0.0)
    y1, y2 = s, h * 0.48 + s
    # unten: Kisten und Buecher
    b.kasten("rattan", 0.34, 0.3, 0.3, x=-0.33, y=y1, r=0.02)
    buecherreihe(b, rng, 0.45, 0.36, 0.24, x0=0.05, y=y1, z=0.0)
    # mitte: kleiner Pokal, Ball, Mini-Ringlicht
    b.dreh("gold", [(0.0, 0.0), (0.06, 0.0), (0.06, 0.03), (0.02, 0.05), (0.02, 0.12), (0.07, 0.2),
                    (0.07, 0.25), (0.0, 0.22)], x=-0.38, y=y2, seg=6)
    b.kugel("stoff_rot", 0.09, x=-0.1, y=y2 + 0.09, fein="uv")
    ring = [(0.25 + 0.12 * math.cos(2 * math.pi * k / 8), y2 + 0.2 + 0.12 * math.sin(2 * math.pi * k / 8), 0.0)
            for k in range(8)]
    b.rohr("licht_lampe", ring, 0.015, seg=4, geschlossen=True)
    b.zylinder("schwarz", 0.012, 0.08, x=0.25, y=y2, seg=5)
    # oben: Pflanze und Kamera-Attrappe
    kraut(b, rng, x=-0.3, y=h)
    with b.an(x=0.25, y=h):
        b.kasten("schwarz", 0.18, 0.12, 0.1, r=0.0)
        b.zylinder("anthrazit", 0.045, 0.08, y=0.06, z=0.05, rx=90, seg=10)


def einrichtung_freies_zimmer_studio(b):
    rng = random.Random(53)
    teppich(b, 2.4, 2.8, x=2.2, z=-1.3, grund="teppich_grau", rand="anthrazit")
    # Set: Greenscreen an der Rueckwand, Gaestesofa davor, Kamera gegenueber
    with b.an(x=2.2, z=-3.2):
        greenscreen(b)
    with b.an(x=2.2, z=-2.6):
        gaestesofa(b)
    with b.an(x=2.2, z=0.55, ry=180):
        kamera_stativ(b)
    with b.an(x=0.75, z=-0.95, ry=137):
        softbox(b)
    with b.an(x=3.6, z=-0.85, ry=-140):
        softbox(b)
    # Ecke hinten links: Akustikpaneele mit Pflanze dazwischen
    with b.an(x=-3.05, z=-3.15):
        akustikpaneel(b)
    with b.an(x=-3.6, z=-2.2, ry=90):
        akustikpaneel(b)
    with b.an(x=-3.5, z=-3.0):
        pflanze_blatt(b, rng, h=1.2, rad_topf=0.18, mat_topf="topf_weiss", blaetter=8, max_rad=0.38)
    # Linke Wand: Regal mit Requisiten, darueber das Neon-Zeichen, Fenster mit Pflanze
    with b.an(x=-3.9 + 0.18, z=2.1, ry=90):
        regal_requisiten(b, rng)
    with b.an(x=-3.9, y=1.3, z=2.1, ry=90):
        neon_play(b)
    with b.an(x=-3.9, z=0.0, ry=90):
        fensterbank(b)
        with b.an(x=-0.2, y=FENSTERBANK_Y, z=0.065):
            pflanze_klein(b, rng, rad=0.08, mat_topf="topf_terra")
    # Beistelltisch am Sofa, Mikrofon am Galgen
    with b.an(x=3.45, z=-2.55):
        beistelltisch(b, mat="weiss", h=0.5)
        tasse(b, "stoff_senf", x=0.05, y=0.5)
    with b.an(x=1.3, z=-1.75):
        dreibein(b, h=1.1, spreiz=0.22)
        b.rohr("schwarz", [(0.0, 1.1, 0.0), (0.25, 1.25, -0.25), (0.45, 1.1, -0.42)], 0.012, seg=4)
        b.kugel("anthrazit", 0.05, x=0.47, y=1.05, z=-0.44, sy=1.6, fein=1)
    # Kleiderstange mit Outfits an der linken Wand
    with b.an(x=-3.55, z=-1.15, ry=90):
        for sx in (-0.5, 0.5):
            b.kasten("metall", 0.03, 1.45, 0.03, x=sx, r=0.0)
            b.kasten("metall", 0.03, 0.03, 0.4, x=sx, r=0.0)
        b.kasten("metall", 1.03, 0.03, 0.03, y=1.42, r=0.0)
        for i, m in enumerate(("stoff_senf", "stoff_blau", "schwarz", "stoff_rosa", "stoff_petrol")):
            b.kasten(m, 0.06, 0.62 + 0.08 * (i % 2), 0.4, x=-0.38 + i * 0.19, y=0.78 - 0.08 * (i % 2), r=0.03)
    # Es bleibt eine WG: der Sitzsack ist geblieben, Pflanzen vorn
    with b.an(x=-1.7, z=1.9, ry=40):
        sitzsack(b, "stoff_rot")
    with b.an(x=-3.45, z=3.05):
        pflanze_busch(b, rng, h=0.9, rad_topf=0.18, mat_topf="topf_terra")
    with b.an(x=3.55, z=-2.05):
        pflanze_busch(b, rng, h=1.0, rad_topf=0.19, mat_topf="topf_grau")
    with b.an(x=0.3, z=2.4):
        pflanze_blatt(b, rng, h=1.25, rad_topf=0.19, mat_topf="topf_weiss", blaetter=8)


# =============================================================================
# Miras Zimmer -- 8 x 7. Ruhig, ordentlich, studentisch.
# =============================================================================

MIRA_SITZ = (-2.8, 0.46, 0.3)   # Sitzflaeche des Schreibtischstuhls (Godot lokal), Blick nach -x


def kleiderschrank(b, w=1.1, h=1.85, d=0.6, mat="weiss"):
    b.kasten("holz_mittel", w - 0.04, 0.08, d - 0.04, r=0.0)
    b.kasten(mat, w, h - 0.08, d, y=0.08, r=0.025)
    b.kasten("holz_mittel", w + 0.03, 0.04, d + 0.03, y=h - 0.01, r=0.015)
    for sx in (-w / 4, w / 4):
        b.kasten("creme", w / 2 - 0.03, h - 0.2, 0.012, x=sx, y=0.14, z=d / 2, r=0.0)
        b.kasten("holz_dunkel", 0.02, 0.22, 0.03, x=sx + (0.2 if sx < 0 else -0.2), y=0.95, z=d / 2 + 0.015, r=0.0)


def nachttisch(b, mat="holz_hell"):
    for sx in (-0.18, 0.18):
        for sz in (-0.14, 0.14):
            b.kasten("holz_dunkel", 0.03, 0.14, 0.03, x=sx, z=sz, r=0.0)
    b.kasten(mat, 0.45, 0.34, 0.38, y=0.14, r=0.02)
    b.kasten("weiss", 0.4, 0.13, 0.01, y=0.3, z=0.19, r=0.0)
    b.kugel("holz_dunkel", 0.018, y=0.365, z=0.2, fein=1)


def holzstuhl(b, holz="holz_hell", kissen="stoff_rosa"):
    """Vorderseite +z, Lehne an -z. Sitzhoehe 0,46."""
    for sx in (-0.19, 0.19):
        for sz in (-0.18, 0.18):
            b.kasten(holz, 0.035, 0.42, 0.035, x=sx, z=sz, r=0.0)
    b.kasten(holz, 0.44, 0.035, 0.42, y=0.42, r=0.01)
    for sx in (-0.19, 0.19):
        b.kasten(holz, 0.035, 0.46, 0.035, x=sx, y=0.455, z=-0.19, rx=-6, r=0.0)
    b.kasten(holz, 0.44, 0.1, 0.03, y=0.8, z=-0.23, rx=-6, r=0.012)
    b.kasten(holz, 0.4, 0.04, 0.025, y=0.62, z=-0.21, rx=-6, r=0.0)
    if kissen:
        b.kasten(kissen, 0.38, 0.045, 0.36, y=0.455, z=0.01, r=0.02, seg=2)


def laptop(b):
    b.kasten("metall", 0.34, 0.02, 0.24, r=0.006)
    b.kasten("grau_hell", 0.28, 0.002, 0.1, y=0.02, z=-0.03, r=0.0)
    with b.an(y=0.01, z=-0.115, rx=-14):
        b.kasten("metall", 0.34, 0.23, 0.012, r=0.005)
        b.kasten("bildschirm_an", 0.3, 0.19, 0.004, y=0.02, z=0.007, r=0.0)


def kopfhoerer(b):
    bogen = [(0.09 * math.cos(math.radians(a)), 0.09 * math.sin(math.radians(a)) + 0.02, 0.0)
             for a in range(0, 181, 30)]
    with b.an(rx=-90):
        b.rohr("stoff_lila", bogen, 0.01, seg=4)
    for sx in (-0.09, 0.09):
        b.zylinder("anthrazit", 0.04, 0.03, x=sx, seg=8, r=0.008)


def yogamatte(b, farbe_matte="stoff_lila", laenge=1.7):
    """Ausgerollt entlang lokal x, das Ende bei +x noch eingerollt."""
    b.platte(farbe_matte, laenge, 0.6, 0.008, x=-0.06, rad=0.02)
    b.zylinder(farbe_matte, 0.065, 0.6, x=laenge / 2, y=0.065, z=-0.3, rx=90, seg=10, r=0.01)
    b.kasten("stoff_salbei", 0.23, 0.1, 0.15, x=laenge / 2 + 0.3, z=-0.1, ry=20, r=0.02)


def katzenkoerbchen(b):
    b.dreh("rattan", [(0.0, 0.0), (0.28, 0.0), (0.33, 0.17), (0.3, 0.19), (0.25, 0.06), (0.0, 0.06)], seg=14)
    b.kugel("stoff_rosa", 0.25, y=0.08, sy=0.22, fein=2)
    b.kugel("stoff_rot", 0.05, x=0.45, y=0.05, z=0.18, fein=1)
    b.rohr("stoff_rot", [(0.45, 0.01, 0.23), (0.55, 0.005, 0.3), (0.6, 0.005, 0.25)], 0.005, seg=4)


def waeschekorb(b):
    b.dreh("rattan", [(0.0, 0.0), (0.18, 0.0), (0.21, 0.45), (0.19, 0.46), (0.16, 0.03), (0.0, 0.03)], seg=10)
    b.kasten("rattan_dunkel", 0.43, 0.04, 0.43, y=0.3, r=0.0)
    b.kugel("stoff_weiss", 0.17, y=0.42, sy=0.35, fein="uv")
    b.kasten("stoff_salbei", 0.08, 0.2, 0.2, x=0.19, y=0.3, rz=-15, r=0.02)


def einrichtung_miras_zimmer(b):
    rng = random.Random(61)
    teppich(b, 2.6, 2.1, x=0.3, z=0.7, grund="teppich_rosa", rand="stoff_creme", rund=True)

    # Rueckwand links der Tuer: grosses Buecherregal, daneben der Waeschekorb
    with b.an(x=-2.9, z=-3.4 + 0.18):
        buecherregal(b, rng, w=1.6, h=1.7, d=0.36, mat="weiss", faecher=5)
    with b.an(x=-2.55, y=1.7, z=-3.25):
        pflanze_klein(b, rng, rad=0.1, mat_topf="topf_terra")
    with b.an(x=-1.72, z=-3.1):
        waeschekorb(b)

    # Rueckwand rechts der Tuer: Kleiderschrank, Nachttisch, Bett
    with b.an(x=1.0, z=-3.4 + 0.3):
        kleiderschrank(b)
    with b.an(x=1.2, y=1.85, z=-3.2):
        b.dreh("rattan", [(0.0, 0.0), (0.16, 0.0), (0.17, 0.2), (0.0, 0.2)], seg=10)
    with b.an(x=1.9, z=-3.4 + 0.2):
        nachttisch(b)
        with b.an(x=-0.06, y=0.48, z=-0.03):
            tischlampe(b, schirm="stoff_senf", h=0.36)
        buecherstapel(b, rng, 2, x=0.08, y=0.48, z=0.08)
    with b.an(x=3.0, z=-3.4 + 1.05):
        bett(b, rng, w=1.5, decke="stoff_salbei", laken="stoff_weiss",
             kissen=("stoff_weiss", "stoff_rosa"), holz="holz_hell", tagesdecke="stoff_senf")
    lichterkette(b, [(2.2, 1.12, -3.37), (2.75, 1.12, -3.37), (3.3, 1.12, -3.37), (3.85, 1.12, -3.37)],
                 durchhang=0.1, abstand=0.2)

    # Linke Wand: Schreibtisch mit Laptop, Buechern, Lampe; Stuhl davor
    with b.an(x=-3.9 + 0.34, z=0.3, ry=90):
        schreibtisch(b, w=1.4, platte="holz_hell", beine="holz_mittel", schubfach=True)
        with b.an(x=-0.05, y=0.75, z=0.06):
            laptop(b)
        buecherstapel(b, rng, 4, x=0.45, y=0.75, z=-0.12, ry=5)
        with b.an(x=-0.52, y=0.75, z=-0.15):
            tischlampe(b, schirm="stoff_creme", h=0.42)
        tasse(b, "stoff_salbei", x=0.3, y=0.75, z=0.18)
        with b.an(x=-0.4, y=0.75, z=0.18, ry=30):
            kopfhoerer(b)
        with b.an(x=0.25, y=0.75, z=-0.22):
            pflanze_klein(b, rng, rad=0.07, mat_topf="topf_weiss")
    with b.an(x=MIRA_SITZ[0], z=MIRA_SITZ[2], ry=-90):
        holzstuhl(b)
    lichterkette(b, [(-3.88, 1.12, -0.5), (-3.88, 1.12, 0.3), (-3.88, 1.12, 1.1)], durchhang=0.1, abstand=0.2)
    with b.an(x=-3.5, z=-1.3):
        pflanze_blatt(b, rng, h=1.3, rad_topf=0.2, mat_topf="topf_terra", blaetter=9, max_rad=0.45)

    # Auf dem runden Teppich: niedriger Tisch mit Teekanne, zwei Bodenkissen
    with b.an(x=0.3, z=0.7):
        b.zylinder("holz_hell", 0.38, 0.035, y=0.3, seg=16, r=0.012)
        for i in range(3):
            a = math.radians(90 + i * 120)
            b.kasten("holz_mittel", 0.035, 0.3, 0.035, x=math.cos(a) * 0.26, z=math.sin(a) * 0.26, r=0.0)
        b.dreh("weiss", [(0.0, 0.0), (0.07, 0.0), (0.09, 0.07), (0.05, 0.14), (0.02, 0.16), (0.0, 0.16)],
               y=0.335, seg=10)
        b.rohr("weiss", [(0.07, 0.38, 0.0), (0.14, 0.43, 0.0), (0.17, 0.46, 0.0)], 0.012, seg=4)
        tasse(b, "stoff_rosa", x=-0.18, y=0.335, z=0.12)
        tasse(b, "stoff_salbei", x=0.05, y=0.335, z=-0.22)
        buecherstapel(b, rng, 1, x=-0.12, y=0.335, z=-0.1, ry=30)
    b.kugel("stoff_salbei", 0.3, x=-0.55, y=0.07, z=0.95, sy=0.28, fein=2)
    b.kugel("stoff_senf", 0.28, x=0.85, y=0.07, z=1.5, sy=0.28, fein=2)
    # Vorn: Yogamatte, Katzenkoerbchen (leer), Pflanzen
    with b.an(x=-1.3, z=2.45):
        yogamatte(b)
    with b.an(x=3.15, z=-0.55):
        katzenkoerbchen(b)
    with b.an(x=3.45, z=3.0):
        pflanze_busch(b, rng, h=0.7, rad_topf=0.16, mat_topf="topf_weiss", blueten=("blume_rosa",))
    with b.an(x=-3.45, z=3.0):
        pflanze_busch(b, rng, h=0.95, rad_topf=0.19, mat_topf="topf_terra")


# @@TEIL3@@

# =============================================================================
# Sperr-Objekte fuer gesperrte Raeume
# =============================================================================

def sperre_kartons(b):
    """Drei beklebte Umzugskartons, ~0,87 m hoch, Ursprung unten Mitte."""
    karton(b, 0.52, 0.42, 0.42, x=-0.27, ry=-4)
    karton(b, 0.50, 0.40, 0.44, x=0.27, z=0.02, ry=6, mat="karton_dunkel", etikett=False)
    karton(b, 0.50, 0.44, 0.40, x=0.02, y=0.42, z=0.01, ry=11)


def sperre_band(b):
    """Zwei Absperrpfosten im Abstand 2,0 m entlang x, gelb-schwarzes Band."""
    for px in (-1.0, 1.0):
        with b.an(x=px):
            b.zylinder("band_schwarz", 0.16, 0.06, seg=10, r=0.02)
            for i in range(4):
                b.zylinder("gelb" if i % 2 == 0 else "band_schwarz", 0.03, 0.19, y=0.06 + i * 0.19, seg=8)
            b.zylinder("band_schwarz", 0.05, 0.08, y=0.82, seg=8, r=0.012)
    # Band: abwechselnde Segmente, leicht durchhaengend
    n = 14
    x0, x1, yb = -0.955, 0.955, 0.855
    pkt = []
    for i in range(n + 1):
        t = i / n
        pkt.append((x0 + (x1 - x0) * t, yb - 0.07 * 4 * t * (1 - t)))
    for i in range(n):
        (ax, ay), (cx, cy) = pkt[i], pkt[i + 1]
        laenge = math.hypot(cx - ax, cy - ay)
        winkel = math.degrees(math.atan2(cy - ay, cx - ax))
        with b.an(x=(ax + cx) / 2, y=(ay + cy) / 2, rz=winkel):
            b.kasten("gelb" if i % 2 == 0 else "band_schwarz", laenge + 0.002, 0.075, 0.008, y=-0.0375, r=0.0)


def vorhaengeschloss(b, s=1.0):
    """Goldenes Vorhaengeschloss, Vorderseite +z, Ursprung unten Mitte des Koerpers."""
    with b.an(s=s):
        b.kasten("gold", 0.30, 0.24, 0.10, r=0.035, seg=2)
        b.kasten("gold_dunkel", 0.27, 0.02, 0.105, y=0.035, r=0.008)
        # Buegel: Halbkreis mit zwei geraden Beinen
        bogen = [(-0.095, 0.2, 0.0), (-0.095, 0.3, 0.0)]
        for k in range(1, 10):
            a = math.pi - math.pi * k / 10
            bogen.append((0.095 * math.cos(a), 0.3 + 0.095 * math.sin(a), 0.0))
        bogen += [(0.095, 0.3, 0.0), (0.095, 0.2, 0.0)]
        b.rohr("gold_dunkel", bogen, 0.026, seg=6)
        # Schluesselloch
        b.zylinder("schwarz", 0.03, 0.012, y=0.14, z=0.05, rx=90, seg=10)
        b.prisma("schwarz", [(-0.012, 0.0), (0.012, 0.0), (0.02, -0.07), (-0.02, -0.07)], 0.012,
                 y=0.14, z=0.052)


def sperre_schild(b):
    """Aufsteller ~0,7 m mit runder Tafel und grossem goldenem Schloss vorn."""
    b.kasten("holz_dunkel", 0.46, 0.05, 0.26, r=0.02)
    b.kasten("holz_dunkel", 0.06, 0.26, 0.05, y=0.05, z=-0.02, r=0.012)
    b.tafel("holz_dunkel", 0.66, 0.46, 0.05, y=0.2, z=-0.05, rad=0.1, r=0.012)
    b.tafel("creme", 0.58, 0.38, 0.02, y=0.24, z=-0.002, rad=0.07)
    with b.an(y=0.2, z=0.08):
        vorhaengeschloss(b, s=1.2)


# =============================================================================
# Vorschau -- nichts hiervon wird exportiert
# =============================================================================

WAND_HOEHE = {"voll": 2.4, "halb": 1.2, "sockel": 0.35, "gelaender": 1.0}


def vorschau_wand(b, seite, typ, oeffnungen, w, d):
    """Platzhalter-Wand auf einer Zonenkante. oeffnungen: [(art, lage)]."""
    entlang_x = seite in ("hinten", "vorn")
    linie = {"hinten": -d / 2, "vorn": d / 2, "links": -w / 2, "rechts": w / 2}[seite]
    laenge = w if entlang_x else d
    hoehe = WAND_HOEHE[typ]

    def stueck(a, c, y0, y1, mat="vs_wand", dicke=0.2):
        if c - a < 0.01 or y1 - y0 < 0.005:
            return
        m = (a + c) / 2
        if entlang_x:
            b.kasten(mat, c - a, y1 - y0, dicke, x=m, y=y0, z=linie, r=0.0)
        else:
            b.kasten(mat, dicke, y1 - y0, c - a, x=linie, y=y0, z=m, r=0.0)

    if typ == "gelaender":
        n = int(laenge / 0.45)
        for i in range(n + 1):
            u = -laenge / 2 + laenge * i / n
            stueck(u - 0.03, u + 0.03, 0.0, 1.0, "vs_gelaender", 0.06)
        stueck(-laenge / 2, laenge / 2, 0.96, 1.02, "vs_gelaender", 0.09)
        stueck(-laenge / 2, laenge / 2, 0.08, 0.12, "vs_gelaender", 0.05)
        return
    schnitte = sorted((lage - (0.45 if art == "fenster" else 0.5), lage + (0.45 if art == "fenster" else 0.5), art)
                      for art, lage in oeffnungen)
    u = -laenge / 2
    for a, c, art in schnitte:
        stueck(u, a, 0.0, hoehe)
        stueck(u, a, hoehe, hoehe + 0.03, "vs_kappe", 0.24)
        if art == "fenster":
            stueck(a, c, 0.0, FENSTERBANK_Y - 0.04)
            stueck(a, c, 2.0, hoehe)
            stueck(a, c, hoehe, hoehe + 0.03, "vs_kappe", 0.24)
            stueck(a, c, FENSTERBANK_Y, 2.0, "vs_glas", 0.04)
            stueck(a - 0.03, c + 0.03, FENSTERBANK_Y - 0.04, FENSTERBANK_Y, "weiss", 0.46)
        elif typ == "voll":
            stueck(a, c, 2.1, hoehe)
            stueck(a, c, hoehe, hoehe + 0.03, "vs_kappe", 0.24)
        if art in ("tuer", "glastuer"):
            stueck(a, a + 0.06, 0.0, min(hoehe, 2.1) if typ == "voll" else 2.1, "vs_kappe", 0.24)
            stueck(c - 0.06, c, 0.0, min(hoehe, 2.1) if typ == "voll" else 2.1, "vs_kappe", 0.24)
        u = c
    stueck(u, laenge / 2, 0.0, hoehe)
    stueck(u, laenge / 2, hoehe, hoehe + 0.03, "vs_kappe", 0.24)


def vorschau_zone(b, zone):
    w, d = zone["w"], zone["d"]
    b.kasten(zone.get("boden", "vs_boden"), w, 0.08, d, y=-0.08, r=0.0)
    for seite, typ, oeffnungen in zone["waende"]:
        vorschau_wand(b, seite, typ, oeffnungen, w, d)
    # Freiflaechen als rote Rahmenlinie auf dem Boden
    for x0, x1, z0, z1 in zone.get("frei", []):
        for (a, c, e, f) in ((x0, x1, z0, z0), (x0, x1, z1, z1), (x0, x0, z0, z1), (x1, x1, z0, z1)):
            b.kasten("buch_rot", max(0.03, c - a), 0.022, max(0.03, f - e), x=(a + c) / 2, z=(e + f) / 2, r=0.0)
    if zone.get("sofa_platzhalter"):
        sx, sz = zone["sofa_platzhalter"]
        b.kasten("vs_gelaender", 0.9, 0.75, 2.0, x=sx - 0.3, z=sz, r=0.06)
        b.kasten("vs_gelaender", 0.6, 0.4, 1.0, x=sx + 0.9, z=sz, r=0.03)


def alles_loeschen():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def rendern(datei, ziel, ausdehnung, ortho=None, aufloesung=1080):
    """Orthografische Kamera aus Godot-Richtung (1, 1, 1) auf ziel (Godot)."""
    szene = bpy.context.scene
    szene.render.engine = "BLENDER_EEVEE"
    szene.render.resolution_x = aufloesung
    szene.render.resolution_y = aufloesung
    szene.render.resolution_percentage = 100
    szene.view_settings.view_transform = "Standard"
    try:
        szene.eevee.taa_render_samples = 48
    except Exception:
        pass
    szene.render.film_transparent = False

    welt = bpy.data.worlds.new("vorschau")
    szene.world = welt
    try:
        welt.use_nodes = True
    except Exception:
        pass
    nt = welt.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    aus = nt.nodes.new("ShaderNodeOutputWorld")
    licht = nt.nodes.new("ShaderNodeBackground")
    licht.inputs["Color"].default_value = farbe("#FFE9D6")
    licht.inputs["Strength"].default_value = 0.45
    grund = nt.nodes.new("ShaderNodeBackground")
    grund.inputs["Color"].default_value = farbe("#F7DCC6")
    grund.inputs["Strength"].default_value = 1.0
    pfad = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pfad.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(licht.outputs["Background"], mix.inputs[1])
    nt.links.new(grund.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], aus.inputs["Surface"])

    def sonne(name, richtung_godot, staerke, hexfarbe, winkel=8.0, schatten=True):
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = staerke
        ld.color = farbe(hexfarbe)[:3]
        ld.angle = math.radians(winkel)
        ld.use_shadow = schatten
        ob = bpy.data.objects.new(name, ld)
        szene.collection.objects.link(ob)
        gx, gy, gz = richtung_godot           # Richtung, AUS der das Licht kommt
        v = Vector((gx, -gz, gy)).normalized()
        ob.rotation_euler = v.to_track_quat("Z", "Y").to_euler()

    sonne("haupt", (0.55, 1.0, 0.75), 2.3, "#FFE0B8", winkel=10)
    sonne("aufheller", (-0.8, 0.7, 0.3), 0.5, "#DDE6FF", schatten=False)

    zx, zy, zz = ziel
    blick = Vector((1.0, -1.0, 1.0)).normalized()
    ziel_b = Vector((zx, -zz, zy))
    cam_d = bpy.data.cameras.new("kamera")
    cam_d.type = "ORTHO"
    cam_d.clip_end = 400.0
    cam = bpy.data.objects.new("kamera", cam_d)
    szene.collection.objects.link(cam)
    cam.location = ziel_b + blick * 120.0
    quat = blick.to_track_quat("Z", "Y")
    cam.rotation_euler = quat.to_euler()
    if ortho is None:
        rechts = quat @ Vector((1, 0, 0))
        oben = quat @ Vector((0, 1, 0))
        (x0, x1), (y0, y1), (z0, z1) = ausdehnung
        us, vs = [], []
        for gx in (x0, x1):
            for gy in (y0, y1):
                for gz in (z0, z1):
                    p = Vector((gx, -gz, gy)) - ziel_b
                    us.append(p.dot(rechts))
                    vs.append(p.dot(oben))
        ortho = 1.08 * max(max(us) - min(us), max(vs) - min(vs))
        mitte = (max(us) + min(us)) / 2 * rechts + (max(vs) + min(vs)) / 2 * oben
        cam.location += mitte
    cam_d.ortho_scale = ortho
    szene.camera = cam
    os.makedirs(os.path.dirname(datei), exist_ok=True)
    szene.render.filepath = datei
    bpy.ops.render.render(write_still=True)


# @@TEIL4@@
ZONEN = {
    "wohnzimmer": {
        "welt": (-7.0, -6.5), "w": 9.0, "d": 6.0,
        "waende": [("hinten", "voll", [("fenster", -2.0), ("fenster", 2.0)]),
                   ("links", "voll", [("fenster", -0.5)]),
                   ("rechts", "halb", [("tuer", 1.5)]),
                   ("vorn", "halb", [("tuer", -2.0)])],
        "frei": [(-1.9, 0.9, -1.4, 1.0), (-2.6, -1.4, 1.8, 3.0), (3.2, 4.5, 0.9, 2.1)],
        "sofa_platzhalter": (-0.8, 0.3),
        "varianten": [("einrichtung_wohnzimmer", einrichtung_wohnzimmer)],
    },
    "balkon": {
        "welt": (9.5, -6.5), "w": 4.0, "d": 6.0, "boden": "vs_deck",
        "waende": [("hinten", "gelaender", []), ("rechts", "gelaender", []),
                   ("links", "halb", []), ("vorn", "halb", [("glastuer", -0.5)])],
        "frei": [(-1.1, 0.1, 1.8, 3.0)],
        "varianten": [("einrichtung_balkon", einrichtung_balkon)],
    },
    "freies_zimmer": {
        "welt": (-7.5, 4.0), "w": 8.0, "d": 7.0,
        "waende": [("hinten", "halb", [("tuer", -0.5)]), ("links", "voll", [("fenster", 0.0)]),
                   ("rechts", "halb", []), ("vorn", "sockel", [])],
        "frei": [(-1.1, 0.1, -3.5, -2.3)],
        "varianten": [("einrichtung_freies_zimmer_bewohnt", einrichtung_freies_zimmer_bewohnt),
                      ("einrichtung_freies_zimmer_leer", einrichtung_freies_zimmer_leer),
                      ("einrichtung_freies_zimmer_studio", einrichtung_freies_zimmer_studio)],
    },
    "miras_zimmer": {
        "welt": (7.5, 4.0), "w": 8.0, "d": 7.0,
        "waende": [("hinten", "halb", [("tuer", -0.5)]), ("links", "halb", []),
                   ("rechts", "sockel", []), ("vorn", "sockel", [])],
        "frei": [(-1.1, 0.1, -3.5, -2.3)],
        "varianten": [("einrichtung_miras_zimmer", einrichtung_miras_zimmer)],
    },
}


# =============================================================================
# Aussen: Garten (Weltkoordinaten) und Fundament
# =============================================================================

GEBAEUDE = (-11.8, 11.8, -9.8, 7.8)     # Gebaeude + 0,3 Rand: dort liegt NICHTS
GARTEN = (-17.0, 17.0, -14.0, 12.0)
TUER_WEG_Z = -1.0
# M1: Flaechen, die der Garten frei lassen soll (x, z, Radius) -- Weg, Hecke, Fahrradstaender usw.
# werden von build_world_zimmer_m1.py eingetragen, bevor der Garten gebaut wird.
ZUSATZ_BELEGT = []
RASEN_AUSSEN = (16.0, 12.1)             # Halbachsen des Rasenrings


def baum(b, rng, h=3.2, rad=1.2):
    b.dreh("stamm", [(0.0, 0.0), (0.17, 0.0), (0.12, h * 0.25), (0.09, h * 0.55), (0.0, h * 0.55)], seg=7)
    b.rohr("stamm", [(0.0, h * 0.35, 0.0), (0.35, h * 0.5, 0.1)], 0.05, seg=4)
    ballen = [(0.0, h - rad * 0.9, 0.0, rad)]
    for i in range(3):
        a = rng.uniform(0, 2 * math.pi) + i * 2.1
        ballen.append((math.cos(a) * rad * 0.45, h - rad * 1.2 + rng.uniform(-0.1, 0.2),
                       math.sin(a) * rad * 0.45, rad * rng.uniform(0.62, 0.75)))
    for i, (x, y, z, r) in enumerate(ballen):
        b.kugel(["busch", "busch_dunkel", "busch_hell", "busch"][i], r, x=x, y=y, z=z, sy=0.88, fein=2)


def tanne(b, rng, h=3.4, rad=0.95):
    b.zylinder("stamm", 0.12, h * 0.25, seg=6)
    for i in range(3):
        y0 = h * (0.18 + 0.24 * i)
        r = rad * (1.0 - 0.24 * i)
        b.zylinder("busch_dunkel" if i != 1 else "busch", r, h * 0.42, y=y0, rad_oben=0.0, seg=8,
                   ry=rng.uniform(0, 45))


def busch(b, rng, rad=0.6, h=None, blueten=None):
    h = h if h is not None else rad * 1.2
    n = 3 if rad > 0.35 else 2
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi) + i * 2.4
        d = rad * 0.45 if i else 0.0
        r = rad * (1.0 if i == 0 else rng.uniform(0.62, 0.78))
        sy = min(0.95, (h / 2) / r) if i == 0 else min(0.95, (h * 0.8 / 2) / r)
        b.kugel(["busch", "busch_hell", "busch_dunkel"][i % 3], r, x=math.cos(a) * d, y=r * sy,
                z=math.sin(a) * d, sy=sy, fein=2)
    if blueten:
        for i in range(5):
            a = rng.uniform(0, 2 * math.pi)
            b.kugel(blueten[i % len(blueten)], 0.06, x=math.cos(a) * rad * 0.75, y=h * rng.uniform(0.45, 0.8),
                    z=math.sin(a) * rad * 0.75, fein=1)


def blumen(b, rng, farben):
    """Bluetenpolster: Blattkissen mit Bluetenkoepfen obenauf (ohne Stiele -- spart Dreiecke)."""
    b.kugel("busch_hell", 0.2, y=0.07, sy=0.55, fein=2)
    for i in range(5):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.05, 0.15)
        b.kugel(farben[i % len(farben)], 0.055, x=math.cos(a) * d, y=0.15 + rng.uniform(0.0, 0.05),
                z=math.sin(a) * d, sy=0.7, fein=1)


def rasenring(b, rng, n=72):
    """Rasen als EIN Ring ums Haus: innen genau am Sperrbereich, aussen weich
    und unregelmaessig. Nur Oberseite und Aussenkante -- von unten sieht ihn niemand."""
    cz = (GEBAEUDE[2] + GEBAEUDE[3]) / 2
    hx_i, hz_i = GEBAEUDE[1] + 0.05, (GEBAEUDE[3] - GEBAEUDE[2]) / 2 + 0.05
    hx_a, hz_a = RASEN_AUSSEN
    bm = bmesh.new()
    innen, aussen_o, aussen_u = [], [], []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        k = min(hx_i / max(abs(c), 1e-6), hz_i / max(abs(s), 1e-6))
        innen.append(bm.verts.new((c * k, 0.02, cz + s * k)))
        wob = 1.0 + 0.025 * math.sin(3 * t + 0.7) + 0.02 * math.sin(7 * t) + rng.uniform(-0.01, 0.01)
        ax = math.copysign(abs(c) ** 0.4, c) * hx_a * wob
        az = math.copysign(abs(s) ** 0.4, s) * hz_a * wob
        aussen_o.append(bm.verts.new((ax, 0.02, cz + az)))
        aussen_u.append(bm.verts.new((ax * 1.004, 0.0, cz + az * 1.004)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((innen[i], innen[j], aussen_o[j], aussen_o[i]))
        bm.faces.new((aussen_o[i], aussen_o[j], aussen_u[j], aussen_u[i]))
    b._einfuegen(bm, "rasen", Matrix.Identity(4))


def stein(b, rng, groesse=0.3, mat="stein"):
    b.kugel(mat, groesse, y=groesse * 0.25, sx=rng.uniform(0.9, 1.4), sy=rng.uniform(0.45, 0.7),
            sz=rng.uniform(0.8, 1.1), ry=rng.uniform(0, 180), rz=rng.uniform(-10, 10), fein=1)


def _frei(x, z, rad):
    gx0, gx1, gz0, gz1 = GEBAEUDE
    if gx0 - rad < x < gx1 + rad and gz0 - rad < z < gz1 + rad:
        return False
    if x > gx1 - 0.2 and abs(z - TUER_WEG_Z) < 0.9 + rad:
        return False
    # nur auf dem Rasenring (Superellipse wie in rasenring(), mit Rand)
    cz = (gz0 + gz1) / 2
    if (abs(x) / (RASEN_AUSSEN[0] - rad)) ** 5 + (abs(z - cz) / (RASEN_AUSSEN[1] - rad)) ** 5 > 0.9:
        return False
    return GARTEN[0] + rad < x < GARTEN[1] - rad and GARTEN[2] + rad < z < GARTEN[3] - rad


def einrichtung_garten(b):
    rng = random.Random(74)
    belegt = list(ZUSATZ_BELEGT)

    def platz(x, z, rad):
        if not _frei(x, z, rad):
            return False
        if any(math.hypot(x - px, z - pz) < rad + pr for px, pz, pr in belegt):
            return False
        belegt.append((x, z, rad))
        return True

    with b.an(y=GARTEN_Y):
        rasenring(b, rng)

        # Trittplatten von der Wohnungstuer nach +x, mit Stufe am Fundament
        b.kasten("trittplatte", 0.5, 0.23, 1.1, x=12.15, z=TUER_WEG_Z, r=0.03, seg=2)
        x = 12.85
        i = 0
        while x < 16.7:
            with b.an(x=x, z=TUER_WEG_Z + (0.12 if i % 2 else -0.1), ry=rng.uniform(0, 40)):
                b.scheibe("trittplatte", ellipse(0.62, 0.52, 8, rng, 0.08), 0.06, y=0.0, r=0.018)
            x += 0.72
            i += 1

        # Baeume hinten und links (verdecken aus der Kamera nichts)
        baeume = [(-13.8, -11.2, "rund"), (-10.6, -12.2, "tanne"), (-6.8, -11.9, "rund"), (-2.4, -12.0, "rund"),
                  (1.8, -12.2, "tanne"), (6.0, -12.0, "rund"), (9.9, -11.7, "rund"), (13.2, -11.0, "tanne"),
                  (-14.8, -7.6, "rund"), (-15.2, -3.2, "tanne"), (-14.8, 1.2, "rund"), (-14.9, 5.0, "rund"),
                  (-13.9, 8.9, "tanne")]
        for bx, bz, art in baeume:
            belegt.append((bx, bz, 1.1))
            with b.an(x=bx + rng.uniform(-0.2, 0.2), z=bz + rng.uniform(-0.2, 0.2), ry=rng.uniform(0, 360)):
                if art == "rund":
                    baum(b, rng, h=rng.uniform(2.9, 3.8), rad=rng.uniform(1.05, 1.3))
                else:
                    tanne(b, rng, h=rng.uniform(3.2, 4.0), rad=rng.uniform(0.85, 1.0))
        # Grosse Buesche zwischen den Baeumen
        versuche = 0
        n = 0
        while n < 10 and versuche < 400:
            versuche += 1
            if rng.random() < 0.55:
                bx, bz = rng.uniform(-16.0, 16.0), rng.uniform(-13.0, -10.4)
            else:
                bx, bz = rng.uniform(-16.6, -12.2), rng.uniform(-9.5, 11.5)
            r = rng.uniform(0.55, 0.85)
            if platz(bx, bz, r):
                with b.an(x=bx, z=bz):
                    busch(b, rng, rad=r, h=r * 1.5, blueten=("blume_rosa", "blume_weiss") if n % 3 == 0 else None)
                n += 1

        # Vorn und rechts: nur Niedriges (<= 0,6 m), locker verteilt
        def streuen(anzahl, rad_bereich, bauen):
            gesetzt = 0
            versuche = 0
            while gesetzt < anzahl and versuche < 600:
                versuche += 1
                if rng.random() < 0.55:
                    px, pz = rng.uniform(-11.5, 16.6), rng.uniform(8.2, 11.6)
                else:
                    px, pz = rng.uniform(12.2, 16.6), rng.uniform(-9.5, 8.0)
                r = rng.uniform(*rad_bereich)
                if platz(px, pz, r):
                    with b.an(x=px, z=pz, ry=rng.uniform(0, 360)):
                        bauen(r)
                    gesetzt += 1

        streuen(14, (0.3, 0.45), lambda r: busch(b, rng, rad=r, h=min(0.55, r * 1.25),
                                                  blueten=("blume_gelb", "blume_weiss") if rng.random() < 0.35 else None))
        farbsaetze = [("blume_rosa", "blume_weiss"), ("blume_gelb", "blume_orange"), ("blume_lila", "blume_weiss"),
                      ("blume_rot", "blume_gelb")]
        streuen(16, (0.18, 0.22), lambda r: blumen(b, rng, rng.choice(farbsaetze)))
        streuen(12, (0.15, 0.3), lambda r: stein(b, rng, r, rng.choice(["stein", "stein_dunkel", "stein_hell"])))
        # auch hinten und links ein paar Steine und Blumen am Rand
        for _ in range(10):
            px, pz = rng.uniform(-16.5, -12.3), rng.uniform(-13.5, 11.5)
            if platz(px, pz, 0.25):
                with b.an(x=px, z=pz):
                    (blumen(b, rng, rng.choice(farbsaetze)) if rng.random() < 0.5 else stein(b, rng, 0.25))


def wg_fundament(b):
    """Sockelplatte unter dem Gebaeude -- EIN Mesh, ein Material."""
    b.kasten("stein_hell", 23.8, 0.45, 17.8, y=-0.47, z=-1.0, r=0.08, seg=2)


def gesamt_vorschau():
    b = Bau()
    wg_fundament(b)
    einrichtung_garten(b)
    b.objekt("vs_aussen")
    b = Bau()
    # Platzhalter fuer die Zonen der anderen Agenten
    fremde = [
        {"welt": (0.5, -6.5), "w": 6.0, "d": 6.0, "boden": "vs_fliese",
         "waende": [("hinten", "voll", [("fenster", 0.0)]), ("rechts", "halb", [])]},
        {"welt": (5.5, -6.5), "w": 4.0, "d": 6.0, "boden": "vs_bad",
         "waende": [("hinten", "voll", [("fenster", 0.0)])]},
        {"welt": (0.0, -1.5), "w": 23.0, "d": 4.0, "boden": "holz_mittel",
         "waende": [("links", "voll", []), ("rechts", "sockel", [("tuer", 0.5)])]},
        {"welt": (0.0, 4.0), "w": 7.0, "d": 7.0, "boden": "vs_boden",
         "waende": [("vorn", "sockel", [])]},
    ]
    for zone in fremde:
        with b.an(x=zone["welt"][0], z=zone["welt"][1]):
            vorschau_zone(b, zone)
    for zone_id, zone in ZONEN.items():
        with b.an(x=zone["welt"][0], z=zone["welt"][1]):
            vorschau_zone(b, {k: v for k, v in zone.items() if k not in ("frei", "sofa_platzhalter")})
            bauen = zone["varianten"][0][1]
            bauen(b)
    b.objekt("vs_haus")
    rendern(os.path.join(VORSCHAU, "gesamt_wg.png"), (0.0, 0.0, -1.0),
            ((-17.0, 17.0), (-0.5, 4.0), (-14.0, 12.0)), aufloesung=1600)

# =============================================================================
# Ablauf
# =============================================================================

def exportieren(obj, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=pfad, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False,
    )


def sperren_vorschau(name, bauen):
    b = Bau()
    b.kasten("vs_dunkel", 4.0, 0.08, 4.0, y=-0.08, r=0.0)
    b.objekt("vs_boden")
    breit = 1.25 if name == "sperre_band" else 0.6
    rendern(os.path.join(VORSCHAU, name + ".png"), (0.0, 0.4, 0.0),
            ((-breit, breit), (0.0, 0.95), (-0.35, 0.35)), aufloesung=720)


ASSETS = {}   # name -> (bauen, vorschau); wird unten befuellt


def registrieren():
    for name, bauen in (("sperre_kartons", sperre_kartons), ("sperre_band", sperre_band),
                        ("sperre_schild", sperre_schild)):
        ASSETS[name] = (bauen, lambda n=name, f=bauen: sperren_vorschau(n, f))
    for zone_id, zone in ZONEN.items():
        for variante, bauen in zone["varianten"]:
            ASSETS[variante] = (bauen, lambda v=variante, z=zone: zonen_vorschau(v, z))
    ASSETS["einrichtung_garten"] = (einrichtung_garten, None)
    ASSETS["wg_fundament"] = (wg_fundament, None)


def zonen_vorschau(name, zone):
    b = Bau()
    vorschau_zone(b, zone)
    b.objekt("vs_raum")
    w, d = zone["w"], zone["d"]
    rendern(os.path.join(VORSCHAU, name + ".png"), (0.0, 0.6, 0.0),
            ((-w / 2 - 0.1, w / 2 + 0.1), (0.0, 2.4), (-d / 2 - 0.1, d / 2 + 0.1)))


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ohne_vorschau = "--ohne-vorschau" in argumente
    nur_gesamt = "--gesamt" in argumente
    auswahl = [a for a in argumente if not a.startswith("--")]
    registrieren()
    print("")
    print("=== EINRICHTUNG WG, TEIL B ===")
    zeilen = []
    for name, (bauen, vorschau) in ASSETS.items():
        if nur_gesamt:
            break
        if auswahl and not any(a in name for a in auswahl):
            continue
        alles_loeschen()
        b = Bau()
        bauen(b)
        obj = b.objekt(name)
        pfad = os.path.join(AUSGABE, name + ".glb")
        exportieren(obj, pfad)
        (x0, x1), (y0, y1), (z0, z1) = masse_von(obj)
        zeile = "  %-38s %6d Dreiecke  %2d Mat.  x %6.2f..%6.2f  y %5.2f..%5.2f  z %6.2f..%6.2f  %6.1f KB" % (
            name, dreiecke_von(obj), len(obj.data.materials), x0, x1, y0, y1, z0, z1,
            os.path.getsize(pfad) / 1024.0)
        print(zeile)
        zeilen.append(zeile)
        if vorschau and not ohne_vorschau:
            vorschau()
    if (not auswahl or "gesamt" in " ".join(argumente)) and not ohne_vorschau:
        alles_loeschen()
        gesamt_vorschau()
    print("")
    for z in zeilen:
        print(z)


if __name__ == "__main__":
    main()
