"""Kleine bewegte Kulissen-Requisiten fuer das Lebendigkeits-System (e_lebendig.gd).

Aufruf:
    blender --background --python art_source/scripts/build_world_lebendig.py

Jede Datei hat ihren Ursprung am Boden in der Mitte des Teils (Godot: +y oben,
Vorderseite +z). Teile, die sich einzeln bewegen sollen (Luefter, Pakete, Wolken,
Glanzstreifen), sind EIGENE Objekte mit dem Ursprung in ihrer Mitte -- das
Lebendig-System findet sie ueber `animation.teil` (Namensbestandteil) und dreht
oder verschiebt sie um genau diesen Ursprung. Fahrzeuge/Figuren sind EIN Mesh.

Erzeugt:
    world/zimmer/welt_katze.glb              W1  Katze, laeuft durch den Flur
    world/webseiten/welt_passant.glb         W3  Passant auf dem Gehweg
    world/buero/welt_stapler_lebendig.glb    W4  Gabelstapler (<= 2.500 Dreiecke)
    world/buero/welt_foerderband.glb         W4  Foerderband mit Paketen (paket_*)
    world/produkt/welt_luefter_schlot.glb    W5  3 Luefter (luefter_*) + Schlot
    world/kapital/welt_wolken_hoch.glb       W6  Wolken knapp ueber der Terrasse (wolke_*)
    world/kapital/welt_poolglanz.glb         W6  Glanzstreifen auf dem Pool (glanz_*)

Farbraum: Hex-Werte sind Bildschirmfarben; hier wird mit ^2,2 nach linear
umgerechnet (siehe CLAUDE.md, glTF speichert linear).
"""

import bpy
import bmesh
import math
import os

AUSGABE = "project/assets/world"


def lin(hexwert):
    h = hexwert.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (r ** 2.2, g ** 2.2, b ** 2.2)


MATS = {}


def mat(name, hexwert, emission=0.0, alpha=1.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    c = lin(hexwert)
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], alpha)
    b.inputs["Roughness"].default_value = 1.0
    if "Metallic" in b.inputs:
        b.inputs["Metallic"].default_value = 0.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.0
    if emission > 0.0:
        b.inputs["Emission Color"].default_value = (c[0], c[1], c[2], 1.0)
        b.inputs["Emission Strength"].default_value = emission
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            pass
        try:
            m.blend_method = "BLEND"
        except Exception:
            pass
    MATS[name] = m
    return m


def bl(p):
    """Godot (x, y, z) -> Blender (x, -z, y)."""
    return (p[0], -p[2], p[1])


class Teil:
    """Ein Objekt aus mehreren Koerpern, Koordinaten in Godot, relativ zum Ursprung."""

    def __init__(self, name, ort=(0.0, 0.0, 0.0)):
        self.name = name
        self.ort = ort
        self.v = []
        self.f = []   # (indices, matname)
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def flaeche(self, ids, m):
        self.f.append((ids, self._mi(m)))

    def quader(self, c, s, m, dreh_y=0.0):
        cx, cy, cz = c
        sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2
        n = len(self.v)
        ca, sa = math.cos(dreh_y), math.sin(dreh_y)
        for ix in (-1, 1):
            for iy in (-1, 1):
                for iz in (-1, 1):
                    x, z = ix * sx, iz * sz
                    self.v.append((cx + x * ca + z * sa, cy + iy * sy, cz - x * sa + z * ca))
        # Indizes: x-y-z in Reihenfolge (-,-,-),(-,-,+),(-,+,-),(-,+,+),(+,-,-),...
        q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for ids in q:
            self.flaeche([n + i for i in ids], m)

    def zyl(self, c, r, h, achse, m, seg=10, r2=None):
        """Zylinder mit Achse 'x' | 'y' | 'z', Mittelpunkt c, Hoehe h."""
        if r2 is None:
            r2 = r
        n = len(self.v)
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            for t, rr in ((-h / 2, r), (h / 2, r2)):
                if achse == "y":
                    p = (rr * ca, t, rr * sa)
                elif achse == "x":
                    p = (t, rr * ca, rr * sa)
                else:
                    p = (rr * ca, rr * sa, t)
                self.v.append((c[0] + p[0], c[1] + p[1], c[2] + p[2]))
        for k in range(seg):
            a0, a1 = 2 * k, 2 * ((k + 1) % seg)
            self.flaeche([n + a0, n + a1, n + a1 + 1, n + a0 + 1], m)
        self.flaeche([n + 2 * k for k in range(seg)][::-1], m)
        self.flaeche([n + 2 * k + 1 for k in range(seg)], m)

    def kugel(self, c, r, m, streck=(1.0, 1.0, 1.0), ring=5, seg=8):
        n = len(self.v)
        for i in range(1, ring):
            th = math.pi * i / ring
            for k in range(seg):
                ph = 2 * math.pi * k / seg
                self.v.append((c[0] + r * streck[0] * math.sin(th) * math.cos(ph),
                               c[1] + r * streck[1] * math.cos(th),
                               c[2] + r * streck[2] * math.sin(th) * math.sin(ph)))
        top = len(self.v)
        self.v.append((c[0], c[1] + r * streck[1], c[2]))
        bot = len(self.v)
        self.v.append((c[0], c[1] - r * streck[1], c[2]))
        for i in range(ring - 2):
            for k in range(seg):
                a = n + i * seg + k
                b = n + i * seg + (k + 1) % seg
                self.flaeche([a, a + seg, b + seg, b], m)
        for k in range(seg):
            self.flaeche([top, n + (k + 1) % seg, n + k], m)
            self.flaeche([bot, n + (ring - 2) * seg + k, n + (ring - 2) * seg + (k + 1) % seg], m)

    def objekt(self):
        me = bpy.data.meshes.new(self.name)
        vs = [bl(p) for p in self.v]
        me.from_pydata(vs, [], [list(reversed(ids)) if False else ids for ids, _ in self.f])
        for m in self.mats:
            me.materials.append(MATS[m])
        for i, (_, mi) in enumerate(self.f):
            me.polygons[i].material_index = mi
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(self.name, me)
        ob.location = bl(self.ort)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def dreiecke(objs):
    n = 0
    for o in objs:
        for p in o.data.polygons:
            n += len(p.vertices) - 2
    return n


def exportieren(name, ordner, teile):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    objs = [t.objekt() for t in teile]
    pfad = os.path.join(AUSGABE, ordner, name + ".glb")
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=pfad, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_materials="EXPORT", export_cameras=False,
                              export_lights=False, export_texcoords=False)
    print("  -> %s/%s: %d Dreiecke" % (ordner, name, dreiecke(objs)))


def alles_mats():
    mat("katze", "#8A8F98")
    mat("katze_bauch", "#F3EEE6")
    mat("katze_dunkel", "#3B3F47")
    mat("jacke", "#3D5A80")
    mat("hose", "#2B2B2B")
    mat("haut", "#D9A77E")
    mat("haar", "#3B2A20")
    mat("tasche", "#FF7A1A")
    mat("gelb", "#F2C230")
    mat("dunkel", "#2B2B2B")
    mat("grau", "#6B7177")
    mat("gabel", "#454B52")
    mat("karton", "#C9A06B")
    mat("karton2", "#B48A55")
    mat("band", "#3A3F45")
    mat("rolle", "#9AA3AB")
    mat("tuerkis", "#12B5A5")
    mat("stahl", "#5C6270")
    mat("alu", "#A9B2C0")
    mat("ziegel", "#59627A")
    mat("led", "#8B5CF6", emission=2.0)
    mat("warn", "#F2C230")
    mat("wolke", "#FFFFFF", emission=0.55, alpha=0.78)
    mat("wolke2", "#F4F7FB", emission=0.5, alpha=0.7)
    mat("glanz", "#E8FBFF", emission=3.0)


# --- W1 ---------------------------------------------------------------------

def katze():
    """Graue Tigerkatze, ~0,4 lang: Ohren, Streifen, weisse Pfoten, Schwanz steil nach oben."""
    t = Teil("welt_katze")
    t.quader((0, 0.17, 0), (0.15, 0.15, 0.36), "katze")
    t.quader((0, 0.115, 0.03), (0.12, 0.05, 0.2), "katze_bauch")
    for z in (-0.11, -0.03, 0.05):
        t.quader((0, 0.248, z), (0.154, 0.012, 0.035), "katze_dunkel")
    t.kugel((0, 0.27, 0.2), 0.085, "katze", ring=4, seg=8)
    for sx in (-1, 1):
        t.zyl((sx * 0.05, 0.355, 0.2), 0.035, 0.07, "y", "katze", seg=3, r2=0.004)
        t.quader((sx * 0.036, 0.285, 0.275), (0.022, 0.026, 0.012), "gelb")
        for sz in (-0.12, 0.12):
            t.quader((sx * 0.045, 0.07, sz), (0.05, 0.14, 0.05), "katze")
            t.quader((sx * 0.045, 0.015, sz + 0.008), (0.056, 0.03, 0.066), "katze_bauch")
    t.quader((0, 0.248, 0.285), (0.06, 0.04, 0.03), "katze_bauch")
    t.quader((0, 0.262, 0.302), (0.022, 0.016, 0.01), "katze_dunkel")
    t.quader((0, 0.27, -0.205), (0.04, 0.1, 0.04), "katze")
    t.quader((0, 0.365, -0.21), (0.036, 0.1, 0.036), "katze_dunkel")
    t.quader((0, 0.455, -0.19), (0.034, 0.1, 0.034), "katze")
    t.quader((0, 0.51, -0.17), (0.036, 0.04, 0.036), "katze_dunkel")
    return [t]


# --- W3 ---------------------------------------------------------------------

def passant():
    t = Teil("welt_passant")
    for sx in (-1, 1):
        t.quader((sx * 0.1, 0.4, 0), (0.14, 0.8, 0.16), "hose")
    t.quader((0, 1.12, 0), (0.46, 0.55, 0.26), "jacke")
    for sx in (-1, 1):
        t.quader((sx * 0.3, 1.1, 0), (0.1, 0.5, 0.12), "jacke")
    t.kugel((0, 1.62, 0), 0.19, "haut", ring=5, seg=8)
    t.kugel((0, 1.68, -0.02), 0.2, "haar", streck=(1.0, 0.7, 1.0), ring=4, seg=8)
    t.quader((0.36, 0.78, 0.04), (0.14, 0.3, 0.3), "tasche")
    return [t]


# --- W4 ---------------------------------------------------------------------

def stapler():
    t = Teil("welt_stapler_lebendig")
    t.quader((0, 0.55, -0.35), (1.0, 0.7, 1.1), "gelb")          # Heck/Gehaeuse
    t.quader((0, 0.3, 0.2), (0.9, 0.3, 0.8), "gelb")             # Bug
    t.quader((0, 0.62, -0.95), (0.9, 0.12, 0.25), "dunkel")      # Gegengewicht
    for sx in (-1, 1):
        for sz in (-0.7, 0.55):
            t.zyl((sx * 0.55, 0.28, sz), 0.28, 0.2, "x", "dunkel", seg=12)
    t.quader((0, 0.98, -0.15), (0.7, 0.08, 0.45), "dunkel")      # Sitz
    t.quader((0, 1.25, -0.4), (0.7, 0.5, 0.08), "dunkel")        # Lehne
    for sx in (-1, 1):
        t.quader((sx * 0.4, 1.35, 0.15), (0.06, 1.0, 0.06), "gelb")   # Schutzdach-Streben
        t.quader((sx * 0.4, 1.35, -0.7), (0.06, 1.0, 0.06), "gelb")
    t.quader((0, 1.88, -0.28), (0.95, 0.07, 1.0), "gelb")        # Dach
    for sx in (-1, 1):
        t.quader((sx * 0.28, 1.0, 0.75), (0.08, 1.9, 0.12), "gabel")  # Hubmast
        t.quader((sx * 0.28, 0.07, 1.2), (0.12, 0.07, 0.8), "gabel")  # Gabel
    t.quader((0, 1.9, 0.75), (0.7, 0.08, 0.12), "gabel")
    t.quader((0, 0.9, 0.7), (0.7, 0.08, 0.1), "gabel")
    t.quader((0, 0.28, 1.2), (0.55, 0.28, 0.5), "karton")        # Last: eine Kiste
    t.quader((0, 0.78, 1.2), (0.5, 0.25, 0.4), "karton2")
    t.quader((0.0, 2.0, -0.28), (0.12, 0.1, 0.12), "warn")       # Blinkleuchte
    t.quader((0.0, 0.5, 0.62), (0.5, 0.18, 0.05), "dunkel")      # Streifen
    return [t]


def foerderband():
    """Band 4,6 lang entlang x, Pakete als eigene Objekte (paket_*)."""
    t = Teil("welt_foerderband_rahmen")
    L, B = 4.6, 0.8
    t.quader((0, 0.72, 0), (L, 0.12, B), "band")
    for sz in (-1, 1):
        t.quader((0, 0.84, sz * (B / 2 + 0.03)), (L, 0.14, 0.06), "stahl")
    for sx in (-1, 0, 1):
        for sz in (-1, 1):
            t.quader((sx * (L / 2 - 0.2), 0.34, sz * 0.3), (0.08, 0.68, 0.08), "stahl")
    for sx in (-1, 1):
        t.zyl((sx * (L / 2), 0.72, 0), 0.1, B, "z", "rolle", seg=10)
    t.quader((L / 2 + 0.25, 0.4, 0), (0.45, 0.8, 0.7), "tuerkis")  # Antrieb
    teile = [t]
    kartons = [(-1.8, "karton", (0.5, 0.36, 0.5)), (-0.6, "karton2", (0.42, 0.3, 0.45)),
               (0.6, "karton", (0.55, 0.4, 0.5)), (1.8, "karton2", (0.45, 0.32, 0.46))]
    for i, (x, m, s) in enumerate(kartons):
        p = Teil("paket_%d" % (i + 1), ort=(x, 0.78 + s[1] / 2, 0))
        p.quader((0, 0, 0), s, m)
        p.quader((0, s[1] / 2 + 0.003, 0), (0.07, 0.01, s[2] + 0.01), "karton" if m == "karton2" else "karton2")
        teile.append(p)
    return teile


# --- W5 ---------------------------------------------------------------------

def luefter_schlot():
    """Frontwand mit 3 Luefterkreisen (Vorderseite +z, Drehachse z) und einem Schlot rechts."""
    r = Teil("welt_luefter_rahmen")
    b = 3 * 1.1 + 0.2
    r.quader((0, 0.9, 0), (b, 1.6, 0.4), "stahl")
    for sx in (-1, 1):
        r.quader((sx * (b / 2 - 0.1), 0.1, 0), (0.2, 0.2, 0.5), "dunkel")
    r.quader((0, 1.72, 0.16), (b - 0.1, 0.06, 0.06), "led")
    r.quader((0, 0.12, 0.16), (b - 0.1, 0.06, 0.06), "led")
    # Schlot rechts neben der Wand
    sx0 = b / 2 + 0.55
    r.zyl((sx0, 1.6, 0), 0.42, 3.2, "y", "ziegel", seg=10, r2=0.34)
    r.zyl((sx0, 3.25, 0), 0.4, 0.14, "y", "dunkel", seg=10)
    r.quader((sx0, 0.15, 0), (1.0, 0.3, 1.0), "stahl")
    teile = [r]
    for i in range(3):
        cx = (i - 1) * 1.1
        f = Teil("luefter_%d" % (i + 1), ort=(cx, 0.9, 0.24))
        f.zyl((0, 0, 0), 0.5, 0.04, "z", "dunkel", seg=14)
        for j in range(4):
            a = j * math.pi / 2 + 0.3 * i
            f.quader((0.25 * math.cos(a), 0.25 * math.sin(a), 0.04), (0.5, 0.17, 0.02), "alu")
            # Blatt gedreht: Quader wird um z gedreht, daher Eckpunkte nachtraeglich drehen
            n = 8
            for k in range(len(f.v) - n, len(f.v)):
                x, y, z = f.v[k]
                x0, y0 = x - 0.25 * math.cos(a), y - 0.25 * math.sin(a)
                f.v[k] = (0.25 * math.cos(a) + x0 * math.cos(a) - y0 * math.sin(a),
                          0.25 * math.sin(a) + x0 * math.sin(a) + y0 * math.cos(a), z)
        f.zyl((0, 0, 0.05), 0.1, 0.06, "z", "dunkel", seg=8)
        teile.append(f)
    return teile


# --- W6 ---------------------------------------------------------------------

def wolken():
    """Drei Wolken, hoch ueber der Terrasse (y 7-8). Jede ein eigenes Objekt."""
    teile = []
    cfg = [("wolke_1", (-3.0, 7.0, 0.0), 1.0, "wolke"), ("wolke_2", (4.0, 7.6, -2.0), 1.3, "wolke2"),
           ("wolke_3", (9.0, 6.8, 3.0), 0.9, "wolke")]
    for name, ort, s, m in cfg:
        w = Teil(name, ort=ort)
        for (dx, dy, dz, rr) in ((0, 0, 0, 1.3), (1.3, -0.15, 0.2, 1.0), (-1.3, -0.2, -0.1, 0.95),
                                 (0.5, 0.35, 0.1, 0.95), (2.3, -0.3, 0.0, 0.7)):
            w.kugel((dx * s, dy * s, dz * s), rr * s, m, streck=(1.4, 0.55, 1.0), ring=4, seg=8)
        teile.append(w)
    return teile


def poolglanz():
    teile = []
    for i, (x, z, l) in enumerate(((-0.8, -0.5, 0.55), (0.2, 0.0, 0.7), (0.9, 0.5, 0.5), (-0.3, 0.6, 0.45))):
        g = Teil("glanz_%d" % (i + 1), ort=(x, 0.335, z))
        g.quader((0, 0.0, 0), (l, 0.012, 0.07), "glanz")
        teile.append(g)
    return teile


def main():
    alles_mats()
    exportieren("welt_katze", "zimmer", katze())
    exportieren("welt_passant", "webseiten", passant())
    exportieren("welt_stapler_lebendig", "buero", stapler())
    exportieren("welt_foerderband", "buero", foerderband())
    exportieren("welt_luefter_schlot", "produkt", luefter_schlot())
    exportieren("welt_wolken_hoch", "kapital", wolken())
    exportieren("welt_poolglanz", "kapital", poolglanz())


main()
