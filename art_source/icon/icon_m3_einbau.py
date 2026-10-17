"""Baut aus gpt/m3.png (Bastians Wahl 15.10.2026) alle Icon-Dateien des Spiels.
Adaptive Icon: Hintergrund = m3 stark weichgezeichnet (blaues Leuchten), Vordergrund =
m3 auf 72 % mit weichem Kreisrand, damit der Launcher-Ausschnitt (66,7 %) fast das ganze
Motiv zeigt. Aufruf: python art_source/icon/icon_m3_einbau.py"""
import os
from PIL import Image, ImageDraw, ImageFilter

HIER = os.path.dirname(os.path.abspath(__file__))
ZIEL = os.path.join(HIER, "..", "..", "project", "assets", "icon")
FINAL = os.path.join(HIER, "final")

quelle = Image.open(os.path.join(HIER, "gpt", "m3.png")).convert("RGBA").resize((1024, 1024), Image.LANCZOS)

os.makedirs(FINAL, exist_ok=True)
quelle.save(os.path.join(FINAL, "icon_1024.png"))
for groesse in (512, 432, 192, 128):
    quelle.resize((groesse, groesse), Image.LANCZOS).save(os.path.join(ZIEL, f"icon_{groesse}.png"))
quelle.resize((512, 512), Image.LANCZOS).save(os.path.join(FINAL, "icon_512.png"))

A = 432
hg = quelle.resize((A, A), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28)).convert("RGB")
hg.save(os.path.join(ZIEL, "icon_adaptiv_hg.png"))
hg.save(os.path.join(FINAL, "adaptive_bg_432.png"))

anteil = 0.72
n = round(A * anteil)
motiv = quelle.resize((n, n), Image.LANCZOS)
maske = Image.new("L", (n * 4, n * 4), 0)
ImageDraw.Draw(maske).ellipse((0, 0, n * 4 - 1, n * 4 - 1), fill=255)
maske = maske.resize((n, n), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
motiv.putalpha(maske)
vg = Image.new("RGBA", (A, A), (0, 0, 0, 0))
vg.alpha_composite(motiv, ((A - n) // 2, (A - n) // 2))
vg.save(os.path.join(ZIEL, "icon_adaptiv_vg.png"))
vg.save(os.path.join(FINAL, "adaptive_fg_432.png"))

# Kontrollbild: Launcher-Kreis (66,7 % Ausschnitt) aus hg + vg
probe = hg.convert("RGBA")
probe.alpha_composite(vg)
k = round(A * 72 / 108)
rand = (A - k) // 2
aus = probe.crop((rand, rand, rand + k, rand + k)).resize((288, 288), Image.LANCZOS)
km = Image.new("L", (288, 288), 0)
ImageDraw.Draw(km).ellipse((0, 0, 287, 287), fill=255)
bogen = Image.new("RGBA", (288 * 2 + 30, 288), (28, 28, 32, 255))
bogen.paste(aus, (0, 0), km)
bogen.paste(quelle.resize((288, 288), Image.LANCZOS), (318, 0))
bogen.save(os.path.join(FINAL, "m3_launcher_probe.png"))
print("fertig")
