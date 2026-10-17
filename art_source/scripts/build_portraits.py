"""Rendert Portraetkarten der Crew und der WG-Figuren (Release-Plan 14.10. §5).

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_portraits.py
    blender --background --python art_source/scripts/build_portraits.py -- mo selin

Ausgabe: project/assets/ui/portraits/<figur>_<ausdruck>.png
    figur    mo, younes, roman, selin, mira, tobi, kind, onkel
    ausdruck neutral, jubelnd, geschockt
256 x 256, transparenter Hintergrund, weisser Sticker-Rand mit duenner Tinte.
Es wird KEINE GLB geschrieben; die Figuren kommen aus denselben Bauteilen wie
build_figuren_crew.py / build_figuren_wg.py (gleiche Augen, gleiche Kontur).

Ablauf: Blender rendert 512 px grosse Rohbilder in einen Temp-Ordner, danach
erledigt das System-Python (Pillow) Verkleinern und Sticker-Rand.
"""

import os
import shutil
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.abspath(os.path.join(HIER, "..", ".."))
ZIEL = os.path.join(WURZEL, "project", "assets", "ui", "portraits")
ROH = os.path.join(tempfile.gettempdir(), "rp_e_portraits_roh")

AUSDRUECKE = [("neutral", "neutral"), ("jubelnd", "jubel"), ("geschockt", "schock")]
FIGUREN = ["mo", "younes", "roman", "selin", "mira", "tobi", "kind", "onkel"]
SIZE = 256
ORTHO = 1.10          # Meter pro Bildbreite
ZENTRUM = (0.0, 0.0, 0.90)


def nachbearbeiten(figuren):
    """Systempython: Rohbild -> 256 px, Sticker-Rand."""
    from PIL import Image, ImageFilter
    os.makedirs(ZIEL, exist_ok=True)
    for name in os.listdir(ROH):
        if not name.endswith(".png"):
            continue
        img = Image.open(os.path.join(ROH, name)).convert("RGBA")
        klein = img.convert("RGBa").resize((SIZE, SIZE), Image.LANCZOS).convert("RGBA")
        a = klein.split()[3]
        weiss = a.filter(ImageFilter.MaxFilter(11)).point(lambda v: 255 if v > 40 else 0)
        tinte = weiss.filter(ImageFilter.MaxFilter(5)).point(lambda v: 255 if v > 40 else 0)
        weiss = weiss.filter(ImageFilter.GaussianBlur(0.8))
        tinte = tinte.filter(ImageFilter.GaussianBlur(0.8))
        aus = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        aus.paste(Image.new("RGBA", (SIZE, SIZE), (27, 23, 38, 255)), mask=tinte)
        aus.paste(Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255)), mask=weiss)
        aus.alpha_composite(klein)
        aus.save(os.path.join(ZIEL, name))
        print("  ", os.path.join(ZIEL, name))


def rendern(figuren):
    import bpy
    import math
    from mathutils import Vector
    sys.path.insert(0, HIER)
    import build_figuren_wg as wg
    import build_figuren_crew as crew

    bauer = {"mo": crew.figur_cap, "younes": crew.figur_buckethat, "roman": crew.figur_brille,
             "selin": crew.figur_zopf, "mira": wg.figur_dutt, "tobi": wg.figur_muetze,
             "kind": wg.figur_kind, "onkel": wg.figur_onkel}
    if os.path.isdir(ROH):
        shutil.rmtree(ROH)
    os.makedirs(ROH)
    for fig in figuren:
        for datei, ausdruck in AUSDRUECKE:
            wg.AUSDRUCK = ausdruck
            wg.szene_leeren()
            teile = bauer[fig]()
            wg.vorschau_szene()
            bpy.data.objects.remove(bpy.data.objects["boden"], do_unlink=True)
            sc = bpy.context.scene
            sc.render.film_transparent = True
            sc.render.image_settings.color_mode = "RGBA"
            wurzel = bpy.data.objects.new("figur", None)
            sc.collection.objects.link(wurzel)
            kp = teile["koerper"][1]
            koerper = teile["koerper"][0].objekt(kp)
            koerper.parent = wurzel
            koerper.location = kp
            for n in ("kopf", "arm_l", "arm_r"):
                if n.startswith("arm"):
                    continue          # Buste: nur Kopf und Schultern
                obj = teile[n][0].objekt(teile[n][1])
                obj.parent = koerper
                obj.location = teile[n][1] - kp
                if n == "kopf" and ausdruck == "jubel":
                    obj.rotation_euler = (math.radians(-9.0), 0.0, math.radians(-5.0))
                if n == "kopf" and ausdruck == "schock":
                    obj.rotation_euler = (math.radians(4.0), 0.0, 0.0)
            wg.kamera(ZENTRUM, (0.20, -1.0, 0.08), ORTHO, 512, 512)
            wg.VORSCHAU = ROH
            wg.rendern("%s_%s.png" % (fig, datei))
            print("  gerendert: %s_%s" % (fig, datei))


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--nachbearbeiten" in args:
        nachbearbeiten(FIGUREN)
        return
    figuren = [a for a in args if a in FIGUREN] or FIGUREN
    print("=== PORTRAETS ===")
    rendern(figuren)
    # System-Python mit Pillow suchen (ohne -I: Pillow liegt oft im Benutzerordner)
    for py in (shutil.which("python"), shutil.which("py")):
        if py and subprocess.run([py, "-c", "import PIL"]).returncode == 0:
            subprocess.run([py, os.path.abspath(__file__), "--", "--nachbearbeiten"], check=True)
            break
    else:
        print("  FEHLER: kein Python mit Pillow -- spaeter: python build_portraits.py -- --nachbearbeiten")
    print("  Ausgabe: " + ZIEL)


if __name__ == "__main__":
    main()
