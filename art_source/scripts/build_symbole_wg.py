"""Rendert die Ausstattungs- und Stations-Symbole der WG (TASK 075).

Aufruf:
    blender --background --python art_source/scripts/build_symbole_wg.py
    blender --background --python art_source/scripts/build_symbole_wg.py -- --nur intake

Ausgabe (project/assets/ui/zimmer/, 256 x 256, transparenter Hintergrund):
    station_<id>_ausstattung_<n>_<m>.png    m = 1..3, NUR das Ausstattungsteil
    station_<id>.png                        Basis mit allen Plaetzen auf m3
Dazu ein Kontaktbogen auf Kartenfarbe (#FFF6E9) nach
art_source/vorschau/team_stationen/symbole_kontaktbogen.png.

Die Geometrie kommt 1:1 aus build_stationen_wg.py (dieselben Baufunktionen),
Symbol und Modell koennen also nicht auseinanderlaufen. Kamera und Licht sind
fuer alle Symbole gleich: orthografisch, 3/4-Ansicht leicht von oben
(Hoehenwinkel 26 Grad), weiches Hauptlicht von links oben, Aufhellung von
rechts. Nur der Blick-Azimut folgt der Vorderseite des jeweiligen Teils --
ein Bildschirm, der nach +z schaut, wird von vorn gezeigt, ein Stuhl, dessen
Sitz zum Tisch (-z) zeigt, ebenfalls von vorn. Jedes Motiv wird auf 80 % der
Bildflaeche eingepasst.
"""

import bpy
import math
import os
import sys

import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_stationen_wg as wg  # noqa: E402

AUSGABE = os.path.join(wg.PROJEKT, "project", "assets", "ui", "zimmer")
GROESSE = 256
FUELLUNG = 0.80
HOEHENWINKEL = 26.0

# Azimut in Grad: 0 = Kamera auf Godot +z, positiv dreht zur +x-Seite.
AZIMUT = {
    ("intake", 0): 30, ("intake", 1): 30, ("intake", 2): 20, ("intake", 3): 25,
    ("processing", 0): 30, ("processing", 1): 25, ("processing", 2): 30, ("processing", 3): 200,
    ("transport", 0): 30, ("transport", 1): 25, ("transport", 2): 20, ("transport", 3): 20,
    ("buffer", 0): 45, ("buffer", 1): 65, ("buffer", 2): -55, ("buffer", 3): -35,
    ("special", 0): 20, ("special", 1): -30, ("special", 2): -20, ("special", 3): -30,
}


# Bildaufbau je Symbol. Eine Stufe verteilt sich im Spiel oft ueber die ganze
# Station (Notizbuch auf dem Hocker, Zettel an der Pinnwand) -- als Symbol
# waere das ein leeres Bild mit zwei Kruemeln. Deshalb darf ein Symbol Teile
# weglassen oder naeher zusammenruecken. Es zeigt trotzdem nur Geometrie
# dieser Stufe, nie die Basis.
#   behalten:     nur diese Teilnamen
#   weg:          diese Teilnamen entfernen (optional nur in einem Hoehenband)
#   verschieben:  (Teilnamen, Versatz in Godot-Metern, Hoehenband der Teilmitte)
#   skalieren:    (Teilnamen, Faktor) um die gemeinsame Mitte, VOR dem Verschieben
#   fokus_ab:     Bildausschnitt nur ueber dieser Hoehe; darunter blendet das
#                 Symbol weich aus (lange Stativbeine)
ALLE_Y = (-9.0, 9.0)
MOTIVE = {
    ("intake", 1, 1): {"behalten": ["umschlag", "seite", "zeile", "stift"]},
    ("intake", 1, 2): {"behalten": ["zettel", "faden"]},
    ("intake", 1, 3): {"behalten": ["wb_rahmen", "wb_flaeche", "skizze", "kurve", "bein", "bein_hinten", "ablage", "marker"]},
    ("intake", 3, 2): {"skalieren": [(["kette_kabel", "kette_birne"], 0.5)],
                       "verschieben": [(["kette_kabel", "kette_birne"], (0.69, -0.30, -0.05), ALLE_Y)]},
    ("intake", 3, 3): {"behalten": ["lampe_fuss", "lampe_stange", "lampe_arm", "lampe_kabel", "lampe_fassung", "lampe_hals", "lampe_birne"],
                       "fokus_ab": 0.85},
    ("processing", 2, 2): {"verschieben": [(["tastatur", "reihe"], (-0.40, 0.0, 0.22), ALLE_Y),
                                           (["maus"], (-0.50, 0.0, 0.24), ALLE_Y)]},
    ("processing", 2, 3): {"verschieben": [(["tastatur", "glow", "tastenreihe"], (0.62, -0.742, 0.42), ALLE_Y),
                                           (["maus", "maus_led"], (0.50, -0.746, 0.44), ALLE_Y)]},
    ("transport", 1, 2): {"verschieben": [(["repeater", "led", "antenne"], (0.62, 0.80, -0.34), (-1.0, 0.5))]},
    ("transport", 1, 3): {"weg": [(["netzkabel", "knick", "stecker"], (-1.0, 0.6))],
                          "verschieben": [(["repeater", "led", "antenne"], (0.62, 0.80, -0.30), (-1.0, 0.5))]},
    ("special", 2, 2): {"verschieben": [(["kissen", "decke", "streifen"], (-0.72, -0.38, -0.36), ALLE_Y)]},
    ("special", 2, 3): {"weg": [(["kissen", "decke", "streifen"], ALLE_Y)],
                        "verschieben": [(["topf", "stamm", "blatt"], (0.55, 0.0, -1.22), ALLE_Y)]},
    ("buffer", 1, 1): {"fokus_ab": 0.55, "fokus_art": "filter"},
    ("buffer", 1, 2): {"fokus_ab": 0.75, "fokus_art": "filter"},
    ("buffer", 1, 3): {"fokus_ab": 0.75, "fokus_art": "filter"},
    ("buffer", 2, 1): {"fokus_ab": 0.80},
    ("buffer", 2, 2): {"fokus_ab": 0.90},
    ("buffer", 2, 3): {"fokus_ab": 0.90},
    ("buffer", 3, 2): {"fokus_ab": 1.00, "fokus_art": "filter"},
    ("buffer", 3, 3): {"verschieben": [(["paneel", "noppe", "paneel_bein"], (0.22, 0.0, 0.12), ALLE_Y)]},
}


def _basisname(obj):
    return obj.name.split(".")[0]


def _mitte_y(obj):
    """Godot-Hoehe der Teilmitte (Blender z der Bounding-Box-Mitte)."""
    ecken = [obj.matrix_world @ Vector(e) for e in obj.bound_box]
    return sum(e.z for e in ecken) / 8.0


def motiv_anwenden(teile, regeln):
    if not regeln:
        return teile
    behalten = regeln.get("behalten")
    ergebnis = []
    for obj in teile:
        name = _basisname(obj)
        y = _mitte_y(obj)
        loeschen = behalten is not None and name not in behalten
        for namen, (y0, y1) in regeln.get("weg", []):
            if name in namen and y0 <= y <= y1:
                loeschen = True
        if loeschen:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        ergebnis.append(obj)
    for namen, faktor in regeln.get("skalieren", []):
        gruppe = [o for o in ergebnis if _basisname(o) in namen]
        if not gruppe:
            continue
        ecken = [o.matrix_world @ Vector(e) for o in gruppe for e in o.bound_box]
        mitte = sum(ecken, Vector()) / len(ecken)
        m = Matrix.Translation(mitte) @ Matrix.Scale(faktor, 4) @ Matrix.Translation(-mitte)
        for o in gruppe:
            o.matrix_world = m @ o.matrix_world
    for obj in ergebnis:
        name = _basisname(obj)
        y = _mitte_y(obj)
        for namen, (dx, dy, dz), (y0, y1) in regeln.get("verschieben", []):
            if name in namen and y0 <= y <= y1:
                obj.matrix_world = Matrix.Translation(Vector((dx, -dz, dy))) @ obj.matrix_world
    return ergebnis


def blickrichtung(azimut):
    """Richtung von der Szene zur Kamera, in Blender-Koordinaten."""
    a, h = math.radians(azimut), math.radians(HOEHENWINKEL)
    gx, gy, gz = math.sin(a) * math.cos(h), math.sin(h), math.cos(a) * math.cos(h)
    return Vector((gx, -gz, gy)).normalized()


def kamera_einpassen(objekte, azimut, fokus_ab=None, fokus_art="klemmen"):
    sc = bpy.context.scene
    richtung = blickrichtung(azimut)
    rot = (-richtung).to_track_quat("-Z", "Y").to_matrix()
    rechts, oben = rot.col[0], rot.col[1]
    punkte = [o.matrix_world @ v.co for o in objekte for v in o.data.vertices]
    if fokus_ab is not None and fokus_art == "filter":
        # nur was oben ist, zaehlt (Stativbeine spreizen sonst den Rahmen)
        punkte = [p for p in punkte if p.z >= fokus_ab]
    elif fokus_ab is not None:
        # Punkte unter der Fokushoehe auf sie hochziehen: lange Stangen
        # haben nur Endpunkte, ein reiner Filter wuerde sie ganz verlieren.
        punkte = [Vector((p.x, p.y, max(p.z, fokus_ab))) for p in punkte]
    us = [p.dot(rechts) for p in punkte]
    vs = [p.dot(oben) for p in punkte]
    ws = [p.dot(richtung) for p in punkte]
    breite, hoehe = max(us) - min(us), max(vs) - min(vs)
    mitte = rechts * ((max(us) + min(us)) * 0.5) + oben * ((max(vs) + min(vs)) * 0.5) + richtung * ((max(ws) + min(ws)) * 0.5)
    cam_data = bpy.data.cameras.new("kamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(breite, hoehe) / FUELLUNG
    cam_data.clip_end = 100.0
    cam = bpy.data.objects.new("kamera", cam_data)
    sc.collection.objects.link(cam)
    cam.matrix_world = Matrix.Translation(mitte + richtung * 20.0) @ rot.to_4x4()
    sc.camera = cam


def licht_symbol(azimut):
    """Wie die Vorschau, aber das Hauptlicht dreht mit der Kamera mit --
    sonst waere ein von hinten gezeigter Stuhl im Gegenlicht."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 64
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = GROESSE
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    welt = bpy.data.worlds.get("welt") or bpy.data.worlds.new("welt")
    sc.world = welt
    welt.use_nodes = True
    bg = welt.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = wg.farbe("#FFF3E3")
    bg.inputs["Strength"].default_value = 1.0
    a = math.radians(azimut)
    for name, (dx, dy, dz), staerke, schatten in (
            ("sonne", (-0.6, -1.0, -0.5), 2.4, True),
            ("fuell", (0.9, -0.3, -0.4), 0.7, False)):
        # Richtung im Kamera-Azimut-System (Godot), dann nach Blender
        gx = dx * math.cos(a) + dz * math.sin(a)
        gz = -dx * math.sin(a) + dz * math.cos(a)
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = staerke
        ld.angle = math.radians(20.0)
        ld.use_shadow = schatten
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.rotation_euler = Vector((gx, -gz, dy)).normalized().to_track_quat("-Z", "Y").to_euler()


def _weich(feld, radius):
    """Kastenfilter, dreimal -> annaehernd gaussisch."""
    for _ in range(3):
        for achse in (0, 1):
            k = 2 * radius + 1
            p = np.pad(feld, [(radius + 1, radius) if a == achse else (0, 0) for a in (0, 1)], mode="edge")
            c = np.cumsum(p, axis=achse)
            if achse == 0:
                feld = (c[k:, :] - c[:-k, :]) / k
            else:
                feld = (c[:, k:] - c[:, :-k]) / k
    return feld


def nachbearbeiten(pfad, ausblenden):
    """Weicher Schlagschatten nach unten (hebt weisse Teile von der cremefarbenen
    Karte ab) und, bei angeschnittenen Motiven, ein weiches Ausblenden am
    unteren Rand. Zeile 0 ist in Blender die UNTERSTE Bildzeile."""
    bild = bpy.data.images.load(pfad)
    px = np.array(bild.pixels[:], dtype=np.float32).reshape(GROESSE, GROESSE, 4)
    bpy.data.images.remove(bild)
    a = px[:, :, 3].copy()
    if ausblenden:
        h = GROESSE * 0.30
        y = np.arange(GROESSE, dtype=np.float32)
        t = np.clip(y / h, 0.0, 1.0)
        a *= (t * t * (3.0 - 2.0 * t))[:, None]
    versatz = 4
    schatten = np.zeros_like(a)
    schatten[:-versatz, :] = a[versatz:, :]
    schatten = np.clip(_weich(schatten, 4) * 0.30, 0.0, 1.0)
    farbe_s = np.array(wg.farbe("#3A2A1E")[:3], dtype=np.float32)
    a_neu = a + schatten * (1.0 - a)
    rgb = (px[:, :, :3] * a[:, :, None] + farbe_s * (schatten * (1.0 - a))[:, :, None]) / np.maximum(a_neu, 1e-6)[:, :, None]
    aus = np.dstack([rgb, a_neu]).astype(np.float32)
    ziel = bpy.data.images.new("symbol", width=GROESSE, height=GROESSE, alpha=True)
    ziel.pixels[:] = aus.ravel()
    ziel.filepath_raw = pfad
    ziel.file_format = "PNG"
    ziel.save()
    bpy.data.images.remove(ziel)


def rendern(bauliste, azimut, pfad, regeln=None):
    wg.alles_loeschen()
    objekte = []
    for bauen in bauliste:
        teile = motiv_anwenden(bauen(), regeln)
        if teile:
            objekte.append(wg.zusammenfuegen(teile, "motiv"))
    licht_symbol(azimut)
    fokus = (regeln or {}).get("fokus_ab")
    kamera_einpassen(objekte, azimut, fokus, (regeln or {}).get("fokus_art", "klemmen"))
    bpy.context.scene.render.filepath = pfad
    bpy.ops.render.render(write_still=True)
    nachbearbeiten(pfad, fokus is not None)


def symbole_station(station):
    daten = wg.STATIONEN[station]
    pfade = []
    for platz, stufen in daten["plaetze"].items():
        for stufe in (1, 2, 3):
            name = "station_%s_ausstattung_%d_%d.png" % (station, platz, stufe)
            pfad = os.path.join(AUSGABE, name)
            rendern([stufen[stufe]], AZIMUT[(station, platz)], pfad, MOTIVE.get((station, platz, stufe)))
            pfade.append(pfad)
    pfad = os.path.join(AUSGABE, "station_%s.png" % station)
    rendern([daten["basis"]] + [stufen[3] for stufen in daten["plaetze"].values()], AZIMUT[(station, 0)], pfad)
    pfade.append(pfad)
    return pfade


def kontaktbogen(stationen):
    """Alle Symbole auf Kartenfarbe, eine Zeile je Station:
    Station | Platz 1 m1..m3 | Platz 2 m1..m3 | Platz 3 m1..m3."""
    karte = np.array(wg.farbe("#FFF6E9")[:3])
    rand = 12
    spalten = 10
    zeilen = len(stationen)
    b = spalten * (GROESSE + rand) + rand
    h = zeilen * (GROESSE + rand) + rand
    bogen = np.ones((h, b, 4), dtype=np.float32)
    bogen[:, :, :3] = np.array(wg.farbe("#E8DCCB")[:3])
    for z, station in enumerate(stationen):
        namen = ["station_%s.png" % station] + ["station_%s_ausstattung_%d_%d.png" % (station, p, m)
                                                 for p in (1, 2, 3) for m in (1, 2, 3)]
        for s, name in enumerate(namen):
            bild = bpy.data.images.load(os.path.join(AUSGABE, name))
            px = np.array(bild.pixels[:], dtype=np.float32).reshape(GROESSE, GROESSE, 4)
            bpy.data.images.remove(bild)
            alpha = px[:, :, 3:4]
            farbe = px[:, :, :3] * alpha + karte * (1.0 - alpha)
            # Bildzeilen laufen in Blender von unten nach oben
            y0 = h - (rand + z * (GROESSE + rand)) - GROESSE
            x0 = rand + s * (GROESSE + rand)
            bogen[y0:y0 + GROESSE, x0:x0 + GROESSE, :3] = farbe
    ziel = bpy.data.images.new("kontaktbogen", width=b, height=h, alpha=True)
    ziel.pixels[:] = bogen.ravel()
    ziel.filepath_raw = os.path.join(wg.VORSCHAU, "symbole_kontaktbogen.png")
    ziel.file_format = "PNG"
    os.makedirs(wg.VORSCHAU, exist_ok=True)
    ziel.save()
    print("  Kontaktbogen:", ziel.filepath_raw)


def main():
    a = wg.argumente()
    os.makedirs(AUSGABE, exist_ok=True)
    print("")
    print("=== SYMBOLE WG (TASK 075) ===")
    stationen = [s for s in wg.STATIONEN if not a["nur"] or s in a["nur"]]
    anzahl = 0
    for station in stationen:
        anzahl += len(symbole_station(station))
        print("  %s fertig" % station)
    kontaktbogen(stationen)
    print("  %d Symbole" % anzahl)


if __name__ == "__main__":
    main()
