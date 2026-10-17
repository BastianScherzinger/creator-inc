"""Bodenplatte und Umriss fuer Stationen (DESIGN_OVERHAUL 4.4, Paket U5).

Aufruf:
    blender --background --python art_source/scripts/build_platten.py

Ausgabe nach project/assets/stations/gemeinsam/:
    platte.glb   Material "platte_rand" (WEISS, wird im Spiel mit Welt-Akzent bzw.
                 Gold/Grau multipliziert) und "platte_flaeche" (Papier, hell).
                 2,0 x 2,0 m, Hoehe 0,07 m, Ursprung = Stationsursprung, y = 0.
    umriss.glb   gepunkteter Umriss (16 Striche) fuer GESPERRTE Stationen,
                 Material "umriss" (WEISS, im Spiel grau getoent).

Godot-Koordinaten (y oben); Export mit export_yup=True.
Farben: glTF speichert linear -> (c/255)^2,2.
"""
import bpy
import bmesh
import math
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
AUS = os.path.abspath(os.path.join(HIER, "..", "..", "project", "assets", "stations", "gemeinsam"))


def farbe(hexwert):
    h = hexwert.lstrip("#")
    return tuple(((int(h[i:i + 2], 16) / 255.0) ** 2.2) for i in (0, 2, 4)) + (1.0,)


def material(name, hexwert):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = farbe(hexwert)
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Metallic"].default_value = 0.0
    return mat


def leeren():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def kasten(name, bx, bz, h, y0, radius, mat):
    """Abgerundeter Kasten in Godot-Massen; Blender: (x, -z, y)."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    o = bpy.context.active_object
    o.name = name
    o.scale = (bx, bz, h)
    o.location = (0.0, 0.0, y0 + h / 2.0)
    bpy.ops.object.transform_apply(scale=True, location=False)
    bev = o.modifiers.new("b", "BEVEL")
    bev.width = radius
    bev.segments = 4
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(60.0)
    bpy.ops.object.modifier_apply(modifier="b")
    o.data.materials.append(mat)
    return o


def verbinden(objekte, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objekte:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objekte[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    return o


def exportieren(obj, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    for versuch in range(4):
        try:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.export_scene.gltf(
                filepath=pfad, export_format="GLB", use_selection=True,
                export_apply=True, export_yup=True, export_materials="EXPORT",
                export_cameras=False, export_lights=False)
            return
        except OSError as e:  # Errno 22, solange Godot parallel importiert
            print("Export wiederholt:", e)
            time.sleep(2.0)
    raise SystemExit("Export gescheitert: " + pfad)


def dreiecke(obj):
    return sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)


def platte():
    leeren()
    rand = kasten("rand", 2.0, 2.0, 0.07, 0.0, 0.16, material("platte_rand", "#FFFFFF"))
    flaeche = kasten("flaeche", 1.66, 1.66, 0.085, 0.0, 0.10, material("platte_flaeche", "#FFF7EA"))
    o = verbinden([rand, flaeche], "platte")
    print("platte Dreiecke:", dreiecke(o))
    exportieren(o, os.path.join(AUS, "platte.glb"))


def umriss():
    leeren()
    mat = material("umriss", "#FFFFFF")
    teile = []
    seite = 2.04
    n = 4  # Striche je Seite
    laenge = 0.34
    for s in range(4):
        for i in range(n):
            t = (i + 0.5) / n - 0.5          # -0.375 .. 0.375
            along = t * (seite - 0.2)
            bx, bz = (laenge, 0.07) if s % 2 == 0 else (0.07, laenge)
            px = along if s % 2 == 0 else (seite / 2 - 0.035) * (1 if s == 1 else -1)
            pz = (seite / 2 - 0.035) * (1 if s == 0 else -1) if s % 2 == 0 else along
            teile.append(kasten("s%d_%d" % (s, i), bx, bz, 0.05, 0.0, 0.02, mat))
            teile[-1].location = (px, -pz, 0.025)
    o = verbinden(teile, "umriss")
    print("umriss Dreiecke:", dreiecke(o))
    exportieren(o, os.path.join(AUS, "umriss.glb"))


platte()
umriss()
