"""Architektur-Baukasten fuer die WG-Karte von Welt 1 (docs/WELT1_TIEFE.md,
Abschnitte 3 und 10, TASK 074a).

Aufruf:
    blender --background --python art_source/scripts/build_room_wg.py

Erzeugt nach project/assets/room/zimmer/:
    wg_boden_*   Bodenmodule 1 x 1 m, Oberkante y = 0, 0,06 dick nach unten
    wg_wand_*    Wandsegmente 1 m entlang lokal X, 0,2 dick, Ursprung unten Mitte
    wg_gelaender Metallgelaender 1 m
    wg_pfosten_* Eck-Saeulen 0,22 x 0,22
und eine Uebersicht nach art_source/vorschau/team_a/module.png.

Jede Datei enthaelt GENAU EIN Mesh (mehrere Materialien darin sind erlaubt):
Der Grundriss-Bauer legt Boeden und Waende als MultiMesh an, und ein MultiMesh
vervielfaeltigt nur das erste Mesh, das es findet (siehe verbinden() in
build_room_zimmer.py -- dort ist genau das einmal schiefgegangen).

Dieses Skript ist zugleich die Werkzeugkiste fuer build_einrichtung_wg_a.py:
Palette, Koordinaten-Umrechnung, Grundkoerper, Export und Vorschau-Render
stehen hier und werden dort importiert.

KOORDINATEN: Alle Funktionen hier nehmen GODOT-Koordinaten entgegen
(x rechts, y oben, z zum Betrachter). Blender ist z-oben; glTF-Export mit
export_yup=True macht aus Blender (x, y, z) wieder Godot (x, z, -y).
Umgekehrt landet eine Godot-Position (gx, gy, gz) in Blender bei
(gx, -gz, gy). Wer hier baut, denkt nur noch in Godot.

LOKALE KONVENTION DER WANDMODULE: lokal +z ist die Innenseite (Fensterbank,
Blickseite). Eine Rueckwand braucht keine Drehung; eine linke Wand (Innenseite
nach +x) dreht um +90 Grad um y, eine rechte Wand um -90 Grad.
"""

import bpy
import bmesh
import math
import os
import sys
from mathutils import Matrix, Vector

WURZEL = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
AUSGABE_MODULE = os.path.join(WURZEL, "project", "assets", "room", "zimmer")
AUSGABE_VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "team_a")


# --- Farbe --------------------------------------------------------------------
# ACHTUNG Farbraum: glTF speichert baseColorFactor LINEAR, Godot zeigt
# albedo_color in sRGB. Deshalb wird JEDER Hex-Ton hier je Kanal mit
# linear = (c/255)^2,2 zurueckgerechnet. Wer einen Ton direkt als 0..1 eintraegt,
# bekommt im Spiel eine ausgewaschene, viel zu helle Flaeche.

def farbe(hexwert, alpha=1.0):
    h = hexwert.lstrip("#")
    kanaele = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple([c ** 2.2 for c in kanaele] + [alpha])


# name: (hex, roughness, metallic, alpha)
# Die Namen beschreiben Stoff und Ton, nie eine Spielrolle (Regel D3).
PALETTE = {
    # Architektur
    "wand_creme":      ("#F2E3CC", 0.85, 0.0, 1.0),
    "wand_kappe":      ("#C8925A", 0.75, 0.0, 1.0),
    "wand_leiste":     ("#E0CBAA", 0.80, 0.0, 1.0),
    "rahmen_weiss":    ("#F7F3EC", 0.60, 0.0, 1.0),
    "glas_hell":       ("#BFE3F2", 0.25, 0.0, 1.0),
    "tuer_holz":       ("#D9A870", 0.75, 0.0, 1.0),
    "metall_dunkel":   ("#4A4F57", 0.50, 0.30, 1.0),
    # Boeden
    "holz_hell_a":     ("#D9A66B", 0.80, 0.0, 1.0),
    "holz_hell_a2":    ("#D39F63", 0.80, 0.0, 1.0),
    "holz_hell_b":     ("#CF9A5E", 0.80, 0.0, 1.0),
    "holz_hell_b2":    ("#D6A367", 0.80, 0.0, 1.0),
    "holz_fuge":       ("#A8744A", 0.90, 0.0, 1.0),
    "holz_flur_a":     ("#B9824E", 0.80, 0.0, 1.0),
    "holz_flur_a2":    ("#B27B48", 0.80, 0.0, 1.0),
    "holz_flur_b":     ("#B47D4A", 0.80, 0.0, 1.0),
    "holz_flur_b2":    ("#BE8854", 0.80, 0.0, 1.0),
    "holz_flur_fuge":  ("#8C5E38", 0.90, 0.0, 1.0),
    "fliese_hell":     ("#E8E4DC", 0.55, 0.0, 1.0),
    "fliese_hell2":    ("#E2DDD3", 0.55, 0.0, 1.0),
    "fliese_fuge":     ("#CFC8BC", 0.90, 0.0, 1.0),
    "fliese_blau":     ("#9CC7DE", 0.45, 0.0, 1.0),
    "fliese_blau2":    ("#8DBCD6", 0.45, 0.0, 1.0),
    "fliese_blau_fuge":("#DCEBF1", 0.90, 0.0, 1.0),
    "deck_holz":       ("#8A6446", 0.85, 0.0, 1.0),
    "deck_holz2":      ("#825D40", 0.85, 0.0, 1.0),
    "deck_fuge":       ("#56402F", 0.95, 0.0, 1.0),
}

_EIGENE_PALETTE = {}


def palette_erweitern(eintraege):
    """Die Einrichtung bringt ihre eigenen Toene mit, nutzt aber dieselbe
    material()-Funktion -- so heisst ein Ton ueberall gleich."""
    _EIGENE_PALETTE.update(eintraege)


def material(name):
    vorhanden = bpy.data.materials.get(name)
    if vorhanden:
        return vorhanden
    eintrag = PALETTE.get(name) or _EIGENE_PALETTE[name]
    if isinstance(eintrag, str):
        # Alias: fast gleiche Toene teilen sich EIN Material -- jede Surface
        # ist in Godot ein eigener Draw Call.
        return material(eintrag)
    hexwert, rauh, metall, alpha = eintrag
    mat = bpy.data.materials.new(name=name)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = farbe(hexwert)
    bsdf.inputs["Roughness"].default_value = rauh
    bsdf.inputs["Metallic"].default_value = metall
    mat.diffuse_color = farbe(hexwert)
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "BLENDED"
    return mat


# --- Koordinaten ----------------------------------------------------------------

def G(x, y, z):
    """Godot-Position -> Blender-Vektor."""
    return Vector((x, -z, y))


# --- Grundkoerper ---------------------------------------------------------------
# Alle Koerper entstehen direkt als bmesh in Godot-Massen, ohne Operatoren --
# schneller und frei von Kontext-Fallen im Hintergrundmodus.

def _objekt(name, bm, mat_name, glatt=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    if isinstance(mat_name, (list, tuple)):
        for m in mat_name:
            me.materials.append(material(m))
    else:
        me.materials.append(material(mat_name))
    if glatt:
        for p in me.polygons:
            p.use_smooth = True
    return obj


def _rund(obj, breite, segmente=2):
    """Bevel-Modifier: weiche Kanten statt Kloetze (Asset-Vertrag 10.1).
    harden_normals haelt die grossen Flaechen flach und rundet nur die Fase --
    so wirkt die Kante weich, ohne dass die ganze Kiste wie Seife aussieht."""
    if breite <= 0:
        return obj
    for p in obj.data.polygons:
        p.use_smooth = True
    mod = obj.modifiers.new("rund", "BEVEL")
    mod.width = breite
    mod.segments = segmente
    mod.limit_method = "NONE"
    mod.harden_normals = True
    mod.use_clamp_overlap = True
    return obj


def kasten(name, groesse, mitte, mat_name, rund=0.0, segmente=2, unten=True):
    """Quader, groesse/mitte in Godot (sx, sy, sz) / (x, y, z).
    unten=False laesst die Bodenflaeche weg (steht auf dem Boden, nie sichtbar)."""
    sx, sy, sz = groesse
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = G(v.co.x * sx, v.co.z * sy, -v.co.y * sz) + G(*mitte)
    bm.normal_update()
    if not unten and rund <= 0:
        bm.faces.ensure_lookup_table()
        weg = [f for f in bm.faces if f.normal.z < -0.9]
        bmesh.ops.delete(bm, geom=weg, context="FACES_ONLY")
    obj = _objekt(name, bm, mat_name)
    return _rund(obj, rund, segmente)


def zylinder(name, radius, hoehe, unten_mitte, mat_name, seiten=10,
             radius_oben=None, rund=0.0, segmente=1, deckel=True):
    """Stehender Zylinder/Kegelstumpf, Unterkante bei unten_mitte (Godot)."""
    bm = bmesh.new()
    r2 = radius if radius_oben is None else radius_oben
    bmesh.ops.create_cone(bm, cap_ends=deckel, cap_tris=False, segments=seiten,
                          radius1=radius, radius2=r2, depth=hoehe)
    ux, uy, uz = unten_mitte
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.y, v.co.z + hoehe / 2.0)) + G(ux, uy, uz)
    obj = _objekt(name, bm, mat_name)
    me = obj.data
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(50))
    if rund > 0:
        _rund(obj, rund, segmente)
    return obj


def liegender_zylinder(name, radius, laenge, mitte, achse, mat_name, seiten=10, deckel=True):
    """Zylinder entlang Godot-Achse 'x' oder 'z' (Rohre, Stangen, Rollen)."""
    obj = zylinder(name, radius, laenge, (0, -laenge / 2.0, 0), mat_name, seiten, deckel=deckel)
    if achse == "x":
        dreh = Matrix.Rotation(math.radians(90), 4, "Y")
    else:  # Godot z = Blender -y
        dreh = Matrix.Rotation(math.radians(90), 4, "X")
    obj.data.transform(dreh)
    obj.data.transform(Matrix.Translation(G(*mitte)))
    return obj


def kugel(name, radius, mitte, mat_name, stauchung=1.0, ringe=5, seiten=8):
    """Niedrig aufgeloeste Kugel -- fuer Blattwerk, Kissenballen, Obst."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seiten, v_segments=ringe, radius=radius)
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.y, v.co.z * stauchung)) + G(*mitte)
    obj = _objekt(name, bm, mat_name, glatt=True)
    return obj


def profil_x(name, punkte, x0, x1, mat_name, enden=True):
    """Extrudiert ein Profil [(z, y), ...] (Godot) entlang x von x0 bis x1.
    Fuer Wandkappen und Leisten: die Rundung sitzt nur an den Laengskanten,
    die Stirnseiten bleiben plan -- sonst entstuende an jeder Modulfuge
    eine Kerbe."""
    bm = bmesh.new()
    links = [bm.verts.new(G(x0, y, z)) for (z, y) in punkte]
    rechts = [bm.verts.new(G(x1, y, z)) for (z, y) in punkte]
    n = len(punkte)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((links[i], links[j], rechts[j], rechts[i]))
    if enden:
        bm.faces.new(list(reversed(links)))
        bm.faces.new(rechts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _objekt(name, bm, mat_name)
    return obj


def rundprofil(z0, z1, y0, y1, r, schritte=2):
    """Rechteckprofil mit abgerundeten OBEREN Ecken (Radius r), gegen den
    Uhrzeigersinn, fuer profil_x()."""
    pkt = [(z0, y0), (z1, y0)]
    for k in range(schritte + 1):
        a = math.radians(90.0 * k / schritte)
        pkt.append((z1 - r + r * math.cos(a), y1 - r + r * math.sin(a)))
    for k in range(schritte + 1):
        a = math.radians(90.0 + 90.0 * k / schritte)
        pkt.append((z0 + r + r * math.cos(a), y1 - r + r * math.sin(a)))
    return pkt


def kissen_platte(name, x0, x1, z0, z1, y_oben, y_fuss, fase, mat_name):
    """Flache 'Kissen'-Platte fuer Dielen und Fliesen: plane Oberseite, rundum
    eine schraege Fase hinab auf y_fuss. Keine Unterseite, keine Seitenwaende --
    zehn Dreiecke, und die Fuge entsteht als feine V-Nut zwischen Nachbarn."""
    bm = bmesh.new()
    unten = [bm.verts.new(G(x, y_fuss, z)) for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
    oben = [bm.verts.new(G(x, y_oben, z)) for (x, z) in
            ((x0 + fase, z0 + fase), (x1 - fase, z0 + fase), (x1 - fase, z1 - fase), (x0 + fase, z1 - fase))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((unten[i], unten[j], oben[j], oben[i]))
    bm.faces.new(oben)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    return _objekt(name, bm, mat_name)


# --- Zusammenfuegen, Transformieren, Export -----------------------------------

def transformieren(teile, x=0.0, z=0.0, y=0.0, dreh_grad=0.0):
    """Setzt eine lokal gebaute Gruppe an (x, y, z) und dreht sie um Godot-y.
    Godot-y entspricht Blender-z, und die Achsabbildung ist eine echte Drehung
    (Determinante +1) -- der Winkel bleibt also derselbe."""
    m = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh_grad), 4, "Z")
    for obj in teile:
        obj.matrix_world = m @ obj.matrix_world
    return teile


def alles_loeschen():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for datum in list(block):
            if datum.users == 0:
                block.remove(datum)


def verbinden(teile, name):
    """Verschmilzt alle Teile zu EINEM Mesh mit Ursprung im Weltnullpunkt.

    Modifier (Bevel) und Transformationen werden VORHER eingebacken, damit die
    Datei genau das enthaelt, was die Vorschau zeigt -- und damit der
    Ursprung wirklich die Modul- bzw. Zonenmitte ist."""
    teile = [t for t in teile if t is not None]
    for obj in bpy.data.objects:
        obj.select_set(False)
    for obj in teile:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = teile[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.data.name = name
    # Gleichnamige Materialien sind durch das Zusammenfuegen mehrfach im
    # Slot-Stapel -- einmal zusammenlegen, dann entstehen im glTF weniger
    # Primitives und in Godot weniger Draw Calls.
    _slots_zusammenlegen(obj)
    return obj


def _slots_zusammenlegen(obj):
    me = obj.data
    erster = {}
    umbiegen = {}
    for i, mat in enumerate(me.materials):
        if mat.name in erster:
            umbiegen[i] = erster[mat.name]
        else:
            erster[mat.name] = i
    if not umbiegen:
        return
    for p in me.polygons:
        if p.material_index in umbiegen:
            p.material_index = umbiegen[p.material_index]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.material_slot_remove_unused()


def dreiecke(obj):
    me = obj.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def masse(obj):
    """Bounding Box in Godot-Achsen: (min x, max x), (min y, max y), (min z, max z)."""
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    return ((min(xs), max(xs)), (min(zs), max(zs)), (-max(ys), -min(ys)))


def exportieren(obj, pfad):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=pfad, export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_materials="EXPORT",
        export_cameras=False, export_lights=False, export_texcoords=False,
    )


def importieren(pfad, x=0.0, z=0.0, y=0.0, dreh_grad=0.0):
    """Holt ein fertiges GLB fuer die Vorschau zurueck -- die Vorschau zeigt so
    die exportierten Dateien, nicht nur die Bauteile im Speicher."""
    vorher = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=pfad)
    neu = [o for o in bpy.data.objects if o not in vorher]
    wurzeln = [o for o in neu if o.parent is None]
    m = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh_grad), 4, "Z")
    for o in wurzeln:
        o.matrix_world = m @ o.matrix_world
    return neu


# --- Vorschau-Render -----------------------------------------------------------

def vorschau_rendern(pfad, ziel, ortho, aufloesung=1080, hintergrund="#F6DCC6"):
    """Orthografische Kamera aus Godot-Richtung (1, 1, 1) auf ziel (Godot),
    warmes Hauptlicht mit Schatten plus kuehle Aufhellung, Pfirsich-Grund.
    Eevee im Hintergrundmodus; Standard-Farbtransformation, damit die Toene
    so erscheinen wie spaeter unter Godots Standard-Tonemapping."""
    szene = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(o, do_unlink=True)

    zielvek = G(*ziel)
    richtung = Vector((1.0, -1.0, 1.0)).normalized()
    cam_daten = bpy.data.cameras.new("vorschau_kamera")
    cam_daten.type = "ORTHO"
    cam_daten.ortho_scale = ortho
    cam_daten.clip_start = 0.1
    cam_daten.clip_end = 400.0
    cam = bpy.data.objects.new("vorschau_kamera", cam_daten)
    szene.collection.objects.link(cam)
    cam.location = zielvek + richtung * 120.0
    cam.rotation_euler = (-richtung).to_track_quat("-Z", "Y").to_euler()
    szene.camera = cam

    def sonne(name, energie, farbe_hex, richtung_blender, schatten, winkel):
        daten = bpy.data.lights.new(name, "SUN")
        daten.energy = energie
        daten.color = farbe(farbe_hex)[:3]
        daten.use_shadow = schatten
        daten.angle = math.radians(winkel)
        obj = bpy.data.objects.new(name, daten)
        szene.collection.objects.link(obj)
        obj.rotation_euler = (-Vector(richtung_blender).normalized()).to_track_quat("-Z", "Y").to_euler()
        return obj

    # Hauptlicht von vorn oben, leicht von rechts: beide dem Betrachter
    # zugewandten Wandseiten (+x, +z) bekommen Licht, Schatten fallen nach
    # hinten links unter die Dinge -- weich und aufgeraeumt wie im Konzeptbild.
    sonne("licht_haupt", 2.2, "#FFE9CF", G(0.45, 1.0, 0.65), True, 12.0)
    sonne("licht_auf", 0.55, "#E4ECFF", G(-0.9, 0.55, 0.25), False, 30.0)

    # Welt: Kamera sieht den Pfirsich-Grund in voller Staerke, die Szene
    # bekommt davon nur ein gedaempftes Umgebungslicht.
    welt = bpy.data.worlds.new("vorschau_welt")
    if welt.node_tree is None:
        welt.use_nodes = True
    baum = welt.node_tree
    for n in list(baum.nodes):
        baum.nodes.remove(n)
    ausgang = baum.nodes.new("ShaderNodeOutputWorld")
    licht = baum.nodes.new("ShaderNodeBackground")
    licht.inputs["Color"].default_value = farbe("#FFF1E2")
    licht.inputs["Strength"].default_value = 0.5
    grund = baum.nodes.new("ShaderNodeBackground")
    grund.inputs["Color"].default_value = farbe(hintergrund)
    grund.inputs["Strength"].default_value = 1.0
    pfad_knoten = baum.nodes.new("ShaderNodeLightPath")
    mischen = baum.nodes.new("ShaderNodeMixShader")
    baum.links.new(pfad_knoten.outputs["Is Camera Ray"], mischen.inputs["Fac"])
    baum.links.new(licht.outputs["Background"], mischen.inputs[1])
    baum.links.new(grund.outputs["Background"], mischen.inputs[2])
    baum.links.new(mischen.outputs["Shader"], ausgang.inputs["Surface"])
    szene.world = welt

    szene.render.engine = "BLENDER_EEVEE"
    szene.eevee.taa_render_samples = 32
    szene.eevee.use_shadows = True
    try:
        szene.eevee.use_fast_gi = True
    except Exception:
        pass
    szene.view_settings.view_transform = "Standard"
    szene.view_settings.look = "None"
    szene.render.resolution_x = aufloesung
    szene.render.resolution_y = aufloesung
    szene.render.resolution_percentage = 100
    szene.render.film_transparent = False
    szene.render.image_settings.file_format = "PNG"
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    szene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)


# ==============================================================================
# BODENMODULE
# ==============================================================================
# Aufbau je Modul: eine Tragplatte in Fugenfarbe (Oberkante knapp unter 0,
# Unterkante -0,06) und darauf "Kissen"-Dielen oder -Fliesen mit Oberkante
# genau y = 0. Die Fuge ist eine feine V-Nut -- man soll sie ahnen, nicht
# sehen (Lehre aus build_room_zimmer.py: zu tiefe Fugen wirken wie Balken).
# Seitenflaechen der Tragplatte sind nur am Kartenrand sichtbar.

BODEN_DICKE = 0.06


def _tragplatte(mat_name, y_oben):
    return kasten("tragplatte", (1.0, BODEN_DICKE + y_oben, 1.0),
                  (0.0, (y_oben - BODEN_DICKE) / 2.0, 0.0), mat_name, unten=False)


def _dielen(reihen, fuge_mat, fase=0.006):
    """reihen: Liste von (breite_z, [(x0, x1, mat), ...]) von hinten nach vorn.
    Dielen laufen entlang x; Stossfugen innerhalb einer Reihe versetzt, damit
    das Raster nicht als Meter-Gitter auffaellt."""
    teile = [_tragplatte(fuge_mat, -0.008)]
    z = -0.5
    for breite, stuecke in reihen:
        for x0, x1, mat in stuecke:
            teile.append(kissen_platte("diele", x0, x1, z, z + breite, 0.0, -0.008, fase, mat))
        z += breite
    return teile


# Verlegeregel fuer a/b (zweite Vorschau-Runde): Jede Dielenreihe besteht
# aus zwei Stuecken mit den Toenen (t1 | t2) in a und (t2 | t1) in b. Liegen
# a und b im Schachbrett nebeneinander, hat die Diele an der Modulgrenze
# links und rechts DENSELBEN Ton -- sie liest sich als eine durchlaufende
# Diele, und das Meterraster verschwindet. Die Stossfuge liegt in a und b an
# verschiedenen Stellen, dadurch entstehen unregelmaessige Dielenlaengen.
# (Erster Anlauf: a hell, b dunkel -> deutliches Karomuster wie Parkettfliesen.)

def _dielen_ab(reihen_toene, fugen_a, fugen_b, breite, variante, fuge_mat):
    reihen = []
    for (t1, t2), fa, fb in zip(reihen_toene, fugen_a, fugen_b):
        if variante == "a":
            reihen.append((breite, [(-0.5, fa, t1), (fa, 0.5, t2)]))
        else:
            reihen.append((breite, [(-0.5, fb, t2), (fb, 0.5, t1)]))
    return _dielen(reihen, fuge_mat)


_HOLZ_TOENE = [("holz_hell_a", "holz_hell_b"), ("holz_hell_b2", "holz_hell_a"),
               ("holz_hell_a2", "holz_hell_b"), ("holz_hell_b", "holz_hell_a2")]
_HOLZ_FUGEN_A = (-0.12, 0.2, -0.3, 0.1)
_HOLZ_FUGEN_B = (0.25, -0.2, 0.15, -0.35)

# Flur: schmalere Dielen als im Zimmer, fuenf Reihen statt vier -- der lange
# Flur "laeuft" optisch und hebt sich vom hellen Zimmerboden ab.
_FLUR_TOENE = [("holz_flur_a", "holz_flur_b"), ("holz_flur_b2", "holz_flur_a"),
               ("holz_flur_a2", "holz_flur_b2"), ("holz_flur_b", "holz_flur_a2"),
               ("holz_flur_a", "holz_flur_b2")]
_FLUR_FUGEN_A = (0.05, -0.25, 0.3, -0.1, 0.18)
_FLUR_FUGEN_B = (-0.3, 0.2, -0.15, 0.35, -0.22)


def boden_holz_a():
    return _dielen_ab(_HOLZ_TOENE, _HOLZ_FUGEN_A, _HOLZ_FUGEN_B, 0.25, "a", "holz_fuge")


def boden_holz_b():
    return _dielen_ab(_HOLZ_TOENE, _HOLZ_FUGEN_A, _HOLZ_FUGEN_B, 0.25, "b", "holz_fuge")


def boden_flur_a():
    return _dielen_ab(_FLUR_TOENE, _FLUR_FUGEN_A, _FLUR_FUGEN_B, 0.2, "a", "holz_flur_fuge")


def boden_flur_b():
    return _dielen_ab(_FLUR_TOENE, _FLUR_FUGEN_A, _FLUR_FUGEN_B, 0.2, "b", "holz_flur_fuge")


def _fliesen(anzahl, fuge_mat, mat_fn, fase):
    teile = [_tragplatte(fuge_mat, -0.006)]
    kante = 1.0 / anzahl
    for i in range(anzahl):
        for k in range(anzahl):
            x0 = -0.5 + i * kante
            z0 = -0.5 + k * kante
            teile.append(kissen_platte("fliese", x0, x0 + kante, z0, z0 + kante,
                                       0.0, -0.006, fase, mat_fn(i, k)))
    return teile


def boden_fliese_a():
    return _fliesen(2, "fliese_fuge", lambda i, k: "fliese_hell", 0.014)


def boden_fliese_b():
    # Eine Fliese minimal dunkler: im Verbund entsteht ein unregelmaessiges
    # Wolkenmuster statt eines Schachbretts.
    return _fliesen(2, "fliese_fuge",
                    lambda i, k: "fliese_hell2" if (i, k) == (1, 0) else "fliese_hell", 0.014)


def boden_bad_a():
    return _fliesen(4, "fliese_blau_fuge", lambda i, k: "fliese_blau", 0.009)


def boden_bad_b():
    dunkler = {(0, 1), (2, 3), (3, 0)}
    return _fliesen(4, "fliese_blau_fuge",
                    lambda i, k: "fliese_blau2" if (i, k) in dunkler else "fliese_blau", 0.009)


def boden_deck():
    """Holzdeck: fuenf Bretter mit echten, dunklen Spalten dazwischen -- anders
    als innen darf man hier die Fuge sehen, sie ist das Erkennungsmerkmal."""
    teile = [_tragplatte("deck_fuge", -0.03)]
    breite = 0.2
    for i in range(5):
        z0 = -0.5 + i * breite + 0.012
        z1 = -0.5 + (i + 1) * breite - 0.012
        mat = "deck_holz2" if i % 2 else "deck_holz"
        teile.append(kasten("brett", (1.0, 0.03, z1 - z0), (0.0, -0.015, (z0 + z1) / 2.0),
                            mat, unten=False))
    return teile


# ==============================================================================
# WANDMODULE
# ==============================================================================
# Puppenhaus-Schnitt: Koerper Creme, Kappe Holz (in der Dicke 2 cm je Seite
# ueberstehend, in der Laenge exakt 1 m -- sonst ueberlappen Nachbarn und
# flackern), schmale Fussleiste. Rundung nur an den Laengskanten.

WAND_DICKE = 0.20
KAPPE_DICKE = 0.24
KAPPE_HOEHE = 0.06
LEISTE_HOEHE = 0.08
LEISTE_DICKE = 0.22
HOEHE = {"voll": 2.4, "halb": 1.2, "sockel": 0.35}
TUER_HOEHE = 2.05      # Oberkante Tuersturz
TUER_PFOSTEN_X = 0.45  # Mitte der Tuerpfosten
TUER_PFOSTEN_B = 0.10  # Breite eines Pfostens (x)
TUER_TIEFE = 0.26      # Tiefe des Rahmens (z), etwas mehr als die Wand


def _kappe(hoehe, x0=-0.5, x1=0.5):
    d = KAPPE_DICKE / 2.0
    return profil_x("kappe", rundprofil(-d, d, hoehe - KAPPE_HOEHE, hoehe, 0.025),
                    x0, x1, "wand_kappe")


def _leiste(hoehe, x0=-0.5, x1=0.5):
    d = LEISTE_DICKE / 2.0
    return profil_x("leiste", rundprofil(-d, d, 0.0, hoehe, 0.012, 1), x0, x1, "wand_leiste")


def _koerper(x0, x1, y0, y1):
    d = WAND_DICKE / 2.0
    return profil_x("koerper", [(-d, y0), (d, y0), (d, y1), (-d, y1)], x0, x1, "wand_creme")


def _leistenhoehe(hoehe):
    return min(LEISTE_HOEHE, hoehe * 0.2)


def _wand(hoehe):
    return [_koerper(-0.5, 0.5, 0.0, hoehe - KAPPE_HOEHE + 0.001),
            _kappe(hoehe), _leiste(_leistenhoehe(hoehe))]


def wand_voll():
    return _wand(HOEHE["voll"])


def wand_halb():
    return _wand(HOEHE["halb"])


def wand_sockel():
    return _wand(HOEHE["sockel"])


def wand_voll_fenster():
    """Fenster mittig 0,9 breit, Bruestung 0,9, Oberkante 2,0. Weisser Rahmen
    mit Sprossenkreuz, hellblaues Glas, Fensterbank innen (lokal +z) tief
    genug fuer Kraeutertoepfe."""
    h = HOEHE["voll"]
    ox, u, o = 0.45, 0.90, 2.00
    teile = [
        _koerper(-0.5, 0.5, 0.0, u),
        _koerper(-0.5, 0.5, o, h - KAPPE_HOEHE + 0.001),
        _koerper(-0.5, -ox, u, o),
        _koerper(ox, 0.5, u, o),
        _kappe(h), _leiste(_leistenhoehe(h)),
    ]
    r = 0.06   # Rahmenbreite in der Ansicht
    t = 0.12   # Rahmentiefe
    teile.append(kasten("rahmen_l", (r, o - u, t), (-ox + r / 2, (u + o) / 2, 0.0), "rahmen_weiss"))
    teile.append(kasten("rahmen_r", (r, o - u, t), (ox - r / 2, (u + o) / 2, 0.0), "rahmen_weiss"))
    teile.append(kasten("rahmen_o", (2 * ox - 2 * r, r, t), (0.0, o - r / 2, 0.0), "rahmen_weiss"))
    teile.append(kasten("rahmen_u", (2 * ox - 2 * r, r, t), (0.0, u + r / 2, 0.0), "rahmen_weiss"))
    teile.append(kasten("sprosse", (0.04, o - u - 2 * r, 0.08), (0.0, (u + o) / 2, 0.0), "rahmen_weiss"))
    teile.append(kasten("kaempfer", (2 * ox - 2 * r, 0.04, 0.08), (0.0, 1.62, 0.0), "rahmen_weiss"))
    teile.append(kasten("glas", (2 * ox - 2 * r, o - u - 2 * r, 0.02), (0.0, (u + o) / 2, 0.0), "glas_hell"))
    # Fensterbank: innen 0,13 vor der Wandflaeche, aussen ein schmaler Tropfrand.
    teile.append(kasten("fensterbank", (0.96, 0.04, 0.36), (0.0, u - 0.02, 0.05),
                        "rahmen_weiss", rund=0.012, segmente=2))
    return teile


def _tuerrahmen():
    """Schlanker Holzrahmen: zwei Pfosten bei x = +-0,45 bis 2,05 m und ein
    Sturz. Er ragt ueber halbhohe Waende hinaus -- das ist Absicht und im
    Konzeptbild genauso: Tueren lesen sich als Tueren, nicht als Luecken."""
    teile = []
    b, t, h = TUER_PFOSTEN_B, TUER_TIEFE, TUER_HOEHE
    for s in (-1, 1):
        teile.append(kasten("pfosten", (b, h - 0.1, t), (s * TUER_PFOSTEN_X, (h - 0.1) / 2, 0.0),
                            "wand_kappe", rund=0.015, segmente=2))
    teile.append(kasten("sturz", (2 * TUER_PFOSTEN_X + b, 0.1, t), (0.0, h - 0.05, 0.0),
                        "wand_kappe", rund=0.02, segmente=2))
    # Schwelle: 1 cm flach -- man sieht, wo der Raum wechselt, stolpert aber nicht.
    teile.append(kasten("schwelle", (2 * TUER_PFOSTEN_X - b, 0.012, WAND_DICKE),
                        (0.0, 0.006, 0.0), "wand_kappe", unten=False))
    return teile


def wand_halb_tuer():
    return _tuerrahmen()


def wand_sockel_tuer():
    """Wohnungstuer in der Sockelkante. Das Tuerblatt steht halb offen nach
    AUSSEN (lokal -z): Scharnier am linken Pfosten, 105 Grad aufgeschwenkt.
    Ab 90 Grad liegt die freie Kante hinter der Scharnierlinie und ragt nie in
    den Durchgang; nach aussen gedreht versperrt es auch innen keinen Laufweg."""
    teile = _tuerrahmen()
    blatt_b, blatt_h, blatt_d = 0.78, 1.93, 0.045
    blatt = [
        kasten("tuerblatt", (blatt_b, blatt_h, blatt_d), (blatt_b / 2, blatt_h / 2 + 0.012, 0.0),
               "tuer_holz", rund=0.012, segmente=2),
    ]
    for seite in (-1, 1):
        for y in (0.55, 1.42):
            blatt.append(kasten("fuellung", (0.52, 0.64, 0.012),
                                (blatt_b / 2, y, seite * (blatt_d / 2 + 0.004)), "wand_kappe"))
        blatt.append(kugel("klinke", 0.035, (blatt_b - 0.09, 1.0, seite * (blatt_d / 2 + 0.03)),
                           "metall_dunkel", ringe=4, seiten=6))
    scharnier_x = -TUER_PFOSTEN_X + TUER_PFOSTEN_B / 2
    # Drehung um +105 Grad (Godot-y): die Blattkante bei lokal +x wandert nach
    # -z, also nach aussen, und liegt dann knapp hinter der Scharnierlinie.
    transformieren(blatt, x=scharnier_x, z=-TUER_TIEFE / 2 + 0.01, dreh_grad=105.0)
    teile += blatt
    return teile


def gelaender():
    """Balkongelaender 1 m: runder Handlauf bei 1,0 m, Unterholm, acht Staebe.
    Die Stabteilung (12,5 cm) geht an den Modulgrenzen nahtlos weiter."""
    teile = []
    teile.append(profil_x("handlauf", rundprofil(-0.035, 0.035, 0.95, 1.0, 0.02), -0.5, 0.5, "metall_dunkel"))
    teile.append(kasten("unterholm", (1.0, 0.035, 0.04), (0.0, 0.10, 0.0), "metall_dunkel"))
    for i in range(8):
        x = -0.4375 + i * 0.125
        teile.append(kasten("stab", (0.022, 0.83, 0.022), (x, 0.535, 0.0), "metall_dunkel"))
    return teile


def _pfosten(hoehe):
    """Eck-Saeule 0,22 x 0,22: verdeckt die Stossfuge, wo zwei Waende sich
    treffen. Kappe 0,27 im Quadrat, allseitig gerundet, weil sie frei steht."""
    lh = _leistenhoehe(hoehe)
    return [
        kasten("saeule", (0.22, hoehe - KAPPE_HOEHE + 0.002, 0.22),
               (0.0, (hoehe - KAPPE_HOEHE) / 2 + 0.001, 0.0), "wand_creme", unten=False),
        kasten("saeule_kappe", (0.27, KAPPE_HOEHE, 0.27), (0.0, hoehe - KAPPE_HOEHE / 2, 0.0),
               "wand_kappe", rund=0.022, segmente=2),
        kasten("saeule_leiste", (0.24, lh, 0.24), (0.0, lh / 2, 0.0), "wand_leiste", unten=False),
    ]


def pfosten_voll():
    return _pfosten(HOEHE["voll"])


def pfosten_halb():
    return _pfosten(HOEHE["halb"])


def pfosten_sockel():
    return _pfosten(HOEHE["sockel"])


MODULE = {
    "wg_boden_holz_a": boden_holz_a,
    "wg_boden_holz_b": boden_holz_b,
    "wg_boden_flur_a": boden_flur_a,
    "wg_boden_flur_b": boden_flur_b,
    "wg_boden_fliese_a": boden_fliese_a,
    "wg_boden_fliese_b": boden_fliese_b,
    "wg_boden_bad_a": boden_bad_a,
    "wg_boden_bad_b": boden_bad_b,
    "wg_boden_deck": boden_deck,
    "wg_wand_voll": wand_voll,
    "wg_wand_voll_fenster": wand_voll_fenster,
    "wg_wand_halb": wand_halb,
    "wg_wand_halb_tuer": wand_halb_tuer,
    "wg_wand_sockel": wand_sockel,
    "wg_wand_sockel_tuer": wand_sockel_tuer,
    "wg_gelaender": gelaender,
    "wg_pfosten_voll": pfosten_voll,
    "wg_pfosten_halb": pfosten_halb,
    "wg_pfosten_sockel": pfosten_sockel,
}


def modul_pfad(name):
    return os.path.join(AUSGABE_MODULE, name + ".glb")


def module_bauen():
    print("")
    print("=== WG-MODULE WELT 1 ===")
    for name, bauen in MODULE.items():
        alles_loeschen()
        obj = verbinden(bauen(), name)
        pfad = modul_pfad(name)
        exportieren(obj, pfad)
        (x0, x1), (y0, y1), (z0, z1) = masse(obj)
        print("  %-22s %4d Dreiecke  x %+.3f..%+.3f  y %+.3f..%+.3f  z %+.3f..%+.3f  %2d Mat  %5.1f KB"
              % (name, dreiecke(obj), x0, x1, y0, y1, z0, z1, len(obj.data.materials),
                 os.path.getsize(pfad) / 1024.0))


# Fuer die Uebersicht: welches Modul flankiert ein Sondermodul links und rechts.
_NACHBAR = {
    "wg_wand_voll_fenster": "wg_wand_voll",
    "wg_wand_halb_tuer": "wg_wand_halb",
    "wg_wand_sockel_tuer": "wg_wand_sockel",
}


def module_vorschau():
    """Zwei Uebersichten: Boeden als 3x3-Flecken (zeigt, ob die Verlegung
    nahtlos ist) und Waende als Dreierzeilen mit Pfosten-Ecke -- so sieht man
    Stossfugen und Anschluesse."""
    alles_loeschen()
    boeden = [n for n in MODULE if n.startswith("wg_boden")]
    for i, name in enumerate(boeden):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                importieren(modul_pfad(name), x=(i % 5) * 3.4 + dx, z=(i // 5) * 3.4 + dz)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_boeden.png"), (6.8, 0.0, 1.7), 13.0)

    alles_loeschen()
    zeilen = [
        ("wg_wand_voll", "wg_wand_voll_fenster", "wg_pfosten_voll"),
        ("wg_wand_halb", "wg_wand_halb_tuer", "wg_pfosten_halb"),
        ("wg_wand_sockel", "wg_wand_sockel_tuer", "wg_pfosten_sockel"),
    ]
    for r, (wand, sonder, pfosten) in enumerate(zeilen):
        z = r * 3.0
        # Eine Ecke: Rueckwand entlang x, linke Wand entlang z, Pfosten im Stoss.
        for dx, modul in ((0, wand), (1, sonder), (2, wand)):
            importieren(modul_pfad(modul), x=dx, z=z)
        importieren(modul_pfad(pfosten), x=-0.5, z=z)
        importieren(modul_pfad(wand), x=-0.5, z=z + 0.5, dreh_grad=90.0)
        importieren(modul_pfad(wand), x=-0.5, z=z + 1.5, dreh_grad=90.0)
        importieren(modul_pfad("wg_boden_holz_a"), x=0, z=z + 1)
        importieren(modul_pfad("wg_boden_holz_b"), x=1, z=z + 1)
        importieren(modul_pfad("wg_boden_holz_a"), x=2, z=z + 1)
    for dx in range(3):
        importieren(modul_pfad("wg_gelaender"), x=4.5 + dx, z=0.0)
        importieren(modul_pfad("wg_boden_deck"), x=4.5 + dx, z=0.5)
    vorschau_rendern(os.path.join(AUSGABE_VORSCHAU, "module_waende.png"), (2.5, 0.8, 3.2), 10.0)


if __name__ == "__main__":
    module_bauen()
    if "--ohne-vorschau" not in sys.argv:
        module_vorschau()
