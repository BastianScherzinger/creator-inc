"""Stationen der Welt `kapital` (Nachtplan N51) als GLB, dazu Symbole,
Fluss-Teil und Vorschaublaetter.

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_stationen_kapital_neu.py -- --vorschau --symbole
    (--nur intake,buffer  --kein_export)

Vertrag (docs/NACHT_PLAN.md 5, docs/nacht/ausstattung_welten.md, Welt 6):
    project/assets/stations/kapital/station_<id>_basis.glb
    project/assets/stations/kapital/station_<id>_ausstattung_<n>_<m>.glb
    project/assets/stations/kapital/station_<id>_<1|2|3>.glb      (Altmodelle)
    project/assets/world/kapital/fluss_teil.glb                   (Goldmuenze, <= 0,35 m)
    project/assets/ui/kapital/station_<id>[_ausstattung_<n>_<m>].png

Werkzeuge kommen aus build_stationen_wg.py / build_stationen_buero.py
(Pruefung, Export, Symbole mit 6-px-Kontur). Koordinaten: GODOT, Vorderseite +z.
Budget: Station mit voller Ausstattung <= 3.000 Dreiecke.
"""

import bpy
import math
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
sys.dont_write_bytecode = True
import build_stationen_wg as wg  # noqa: E402
import build_symbole_wg as sy  # noqa: E402
from build_stationen_wg import (  # noqa: E402
    kasten, zylinder, stab, kugel, ring, punkt, verkette, monitor, laptop, schirm_inhalt,
)

PROJEKT = wg.PROJEKT
AUSGABE = os.path.join(PROJEKT, "project", "assets", "stations", "kapital")
AUSGABE_UI = os.path.join(PROJEKT, "project", "assets", "ui", "kapital")
AUSGABE_FLUSS = os.path.join(PROJEKT, "project", "assets", "world", "kapital", "fluss_teil.glb")
VORSCHAU = os.path.join(PROJEKT, "art_source", "vorschau", "kapital", "stationen")

# Die Werkzeuge (Sticker, Vorschau, Budget) aus dem Lager-Skript uebernehmen.
import build_stationen_buero as bu  # noqa: E402

BUDGET_GESAMT = 3000
bu.BUDGET_GESAMT = BUDGET_GESAMT
bu.AUSGABE = AUSGABE
bu.AUSGABE_UI = AUSGABE_UI
bu.VORSCHAU = VORSCHAU
wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU
wg.BUDGET_BASIS = 1100
wg.BUDGET_AUSSTATTUNG = 1100
sy.AUSGABE = AUSGABE_UI

wg.PALETTE.update({
    "k_messing":      ("#F2B200", 0.0),
    "k_gold":         ("#FFC62E", 0.0),
    "k_gold_dunkel":  ("#D99A0B", 0.0),
    "k_holz_dunkel":  ("#5B3A26", 0.0),
    "k_holz":         ("#8A5A3A", 0.0),
    "k_leder":        ("#8E4A2A", 0.0),
    "k_leder_dunkel": ("#5E321E", 0.0),
    "k_marmor":       ("#F4F1EC", 0.0),
    "k_marmor_ader":  ("#E3C789", 0.0),
    "k_glas":         ("#CFEAF4", 0.0),
    "k_samt_gruen":   ("#2F7A64", 0.0),
    "k_samt_blau":    ("#35558F", 0.0),
    "k_creme":        ("#F3EBDD", 0.0),
    "k_schwarz":      ("#26262B", 0.0),
    "k_weiss":        ("#FAF8F4", 0.0),
    "k_rot":          ("#C8423A", 0.0),
    "k_rosa":         ("#F4A7B9", 0.0),
    "k_meer":         ("#3F8FD0", 0.0),
    "k_land":         ("#7CC46A", 0.0),
    "k_tafel":        ("#1F2A38", 0.0),
    "k_eis":          ("#DDF3FA", 0.0),
    "k_sekt":         ("#F7E08E", 0.0),
    "k_wasser":       ("#8FD3F0", 0.0),
    "k_kachel_a":     ("#5B8FD6", 0.0),
    "k_kachel_b":     ("#E0664F", 0.0),
    "k_kachel_c":     ("#5DBE8A", 0.0),
    "k_kachel_d":     ("#9C82E0", 0.0),
    "k_stahl":        ("#9DA4AD", 0.0),
    "k_licht_gold":   ("#FFD76A", 1.3),
    "k_licht_gruen":  ("#5BE07A", 1.2),
    "k_licht_rot":    ("#FF5A4A", 1.2),
    "k_holo":         ("#7FE3FF", 1.4),
    "k_feuer":        ("#FF9A2A", 1.8),
    "k_karte_licht":  ("#4FB0FF", 0.9),
})

# Glas durchscheinend: material() von wg ergaenzen.
_ALPHA = {"k_glas": 0.35, "k_holo": 0.55, "k_wasser": 0.8}
_orig_material = wg.material


def _material(name):
    mat = _orig_material(name)
    if name in _ALPHA and mat.get("_alpha_gesetzt") is None:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Alpha"].default_value = _ALPHA[name]
        bsdf.inputs["Roughness"].default_value = 0.1
        mat.surface_render_method = "BLENDED"
        mat["_alpha_gesetzt"] = 1
    return mat


wg.material = _material


# =============================================================================
# Helfer
# =============================================================================

def q(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0), r=None):
    if r is None:
        m = min(groesse)
        r = (min(0.012, m * 0.18), 1) if m >= 0.04 else (0.0, 0)
    return kasten(name, groesse, pos, mat, dreh, rund=r)


def f(name, groesse, pos, mat, dreh=(0.0, 0.0, 0.0)):
    return kasten(name, groesse, pos, mat, dreh, rund=(0.0, 0))


def z(name, r, h, unten, mat, seiten=12, r_oben=None, dreh=(0, 0, 0)):
    """Zylinder, unten = Mitte der Unterseite."""
    return zylinder(name, r, h, (unten[0], unten[1] + h / 2, unten[2]), mat, seiten=seiten,
                    radius_oben=r_oben, dreh=dreh, rund=(0, 0))


def L(pos, gier, off):
    return punkt(pos, (0, gier, 0), off)


def sessel(pos, gier=0.0, b=0.62, t=0.6, mat="k_leder", fuss="k_messing", lehne_h=0.42):
    """Club-Sessel, Sitz schaut nach lokal +z (Lehne bei -z). pos = Mitte unten."""
    d = (0, gier, 0)
    sh = 0.44
    tt = [
        q("sessel_sockel", (b, 0.24, t), L(pos, gier, (0, 0.10 + 0.12, 0)), mat, d, r=(0.03, 1)),
        q("sessel_kissen", (b - 0.2, 0.08, t - 0.16), L(pos, gier, (0, 0.34 + 0.04 + 0.001, 0.05)), mat, d, r=(0.03, 1)),
        q("sessel_lehne", (b, lehne_h, 0.16), L(pos, gier, (0, sh + lehne_h / 2 - 0.1, -t / 2 + 0.08)), mat, d, r=(0.04, 1)),
    ]
    for s in (-1, 1):
        tt.append(q("sessel_arm", (0.10, 0.2, t - 0.16), L(pos, gier, (s * (b / 2 - 0.05), 0.34 + 0.1, 0.07)), mat, d, r=(0.03, 1)))
        for v in (-1, 1):
            tt.append(f("sessel_fuss", (0.04, 0.10, 0.04), L(pos, gier, (s * (b / 2 - 0.06), 0.05, v * (t / 2 - 0.06))), fuss, d))
    return tt


def sofa(pos, gier=0.0, b=1.0, t=0.55, mat="k_samt_gruen"):
    d = (0, gier, 0)
    tt = [
        q("sofa_sockel", (b, 0.26, t), L(pos, gier, (0, 0.08 + 0.13, 0)), mat, d, r=(0.03, 1)),
        q("sofa_lehne", (b, 0.34, 0.14), L(pos, gier, (0, 0.34 + 0.17 - 0.05, -t / 2 + 0.07)), mat, d, r=(0.04, 1)),
    ]
    for s in (-1, 1):
        tt.append(q("sofa_arm", (0.12, 0.18, t), L(pos, gier, (s * (b / 2 - 0.06), 0.34 + 0.09, 0)), mat, d, r=(0.03, 1)))
        tt.append(q("sofa_kissen", (b / 2 - 0.14, 0.07, t - 0.2), L(pos, gier, (s * (b / 4 - 0.04), 0.34 + 0.036, 0.05)), "k_creme", d, r=(0.025, 1)))
        for v in (-1, 1):
            tt.append(f("sofa_fuss", (0.04, 0.08, 0.04), L(pos, gier, (s * (b / 2 - 0.06), 0.04, v * (t / 2 - 0.06))), "k_messing", d))
    return tt


def rundtisch(pos, r=0.2, h=0.5, platte="k_marmor", fuss="k_messing"):
    x, y, zz = pos
    return [
        z("tisch_platte", r, 0.03, (x, y + h - 0.03, zz), platte, seiten=14),
        z("tisch_saeule", 0.025, h - 0.03, (x, y + 0.02, zz), fuss, seiten=6),
        z("tisch_fuss", r * 0.6, 0.02, (x, y, zz), fuss, seiten=10),
    ]


def sockel(pos, b=0.3, h=0.8, mat="k_marmor"):
    x, y, zz = pos
    return [q("sockel", (b, h, b), (x, y + h / 2, zz), mat, r=(0.01, 1)),
            f("sockel_kante", (b + 0.03, 0.03, b + 0.03), (x, y + h - 0.015, zz), "k_messing")]


def rahmen(pos, dreh, b, h, motiv="papier", rahmen_mat="k_messing", tiefe=0.03):
    """Bilderrahmen, pos = Mitte, Bild zeigt nach lokal +z."""
    tt = [f("rahmen", (b, h, tiefe), pos, rahmen_mat, dreh),
          f("bild", (b - 0.06, h - 0.06, 0.004), punkt(pos, dreh, (0, 0, tiefe / 2 + 0.002)), motiv, dreh)]
    return tt


def zertifikat(pos, dreh, b=0.3, h=0.38):
    tt = rahmen(pos, dreh, b, h, "k_creme")
    tt.append(f("siegel", (0.06, 0.06, 0.004), punkt(pos, dreh, (b * 0.25, -h * 0.28, 0.02)), "k_rot", dreh))
    for k in range(3):
        tt.append(f("zeile", (b * 0.6, 0.012, 0.004), punkt(pos, dreh, (0, h * 0.25 - k * 0.05, 0.02)), "grau_mittel", dreh))
    return tt


def muenze(pos, r=0.05, liegend=True, dreh=(0, 0, 0)):
    x, y, zz = pos
    if liegend:
        return [z("muenze", r, 0.014, (x, y, zz), "k_gold", seiten=12),
                z("muenze_rand", r * 0.7, 0.002, (x, y + 0.014, zz), "k_gold_dunkel", seiten=10)]
    return [zylinder("muenze", r, 0.014, (x, y, zz), "k_gold", seiten=12, dreh=dreh, rund=(0, 0))]


def muenzstapel(pos, n, r=0.045):
    x, y, zz = pos
    return [z("stapel", r, 0.013 * n, (x, y, zz), "k_gold", seiten=10),
            z("stapel_oben", r * 0.7, 0.002, (x, y + 0.013 * n, zz), "k_gold_dunkel", seiten=8)]


def barren(pos, gier=0.0, s=1.0):
    d = (0, gier, 0)
    return [f("barren", (0.18 * s, 0.035 * s, 0.08 * s), L(pos, gier, (0, 0.0175 * s, 0)), "k_gold", d),
            f("barren_oben", (0.14 * s, 0.018 * s, 0.05 * s), L(pos, gier, (0, 0.035 * s + 0.009 * s, 0)), "k_gold", d)]


def barrenpyramide(pos, lagen=3, s=1.0):
    x, y, zz = pos
    tt = []
    hy = y
    for l in range(lagen):
        n = lagen - l
        for i in range(n):
            tt += barren((x + (i - (n - 1) / 2) * 0.19 * s, hy, zz), 0.0, s)
        hy += 0.054 * s
    return tt


def glas_sekt(pos, s=1.0):
    x, y, zz = pos
    return [z("glas_fuss", 0.028 * s, 0.006, (x, y, zz), "k_glas", seiten=8),
            z("glas_stiel", 0.006 * s, 0.08 * s, (x, y + 0.006, zz), "k_glas", seiten=5),
            z("glas_kelch", 0.012 * s, 0.07 * s, (x, y + 0.086 * s, zz), "k_sekt", seiten=8, r_oben=0.03 * s)]


def flasche(pos, mat="k_samt_gruen", h=0.3):
    x, y, zz = pos
    return [z("flasche", 0.04, h * 0.65, (x, y, zz), mat, seiten=8),
            z("flasche_hals", 0.015, h * 0.35, (x, y + h * 0.65, zz), mat, seiten=6, r_oben=0.013),
            z("flasche_kappe", 0.017, 0.035, (x, y + h - 0.03, zz), "k_gold", seiten=6)]


def pflanze_hoch(pos, g=1.0):
    x, y, zz = pos
    tt = [z("topf", 0.13 * g, 0.34 * g, (x, y, zz), "k_weiss", seiten=10, r_oben=0.15 * g),
          z("topf_rand", 0.155 * g, 0.03, (x, y + 0.34 * g, zz), "k_messing", seiten=10)]
    for i, (dx, dy, dz, r) in enumerate(((0, 0.75, 0, 0.2), (0.1, 0.55, 0.05, 0.16), (-0.09, 0.6, -0.06, 0.15), (0.02, 0.95, 0.03, 0.14))):
        tt.append(kugel("blatt", r * g, (x + dx * g, y + dy * g, zz + dz * g), "pflanze" if i % 2 == 0 else "pflanze_dunkel", stufen=1, skala=(1, 0.85, 1)))
    tt.append(stab("stamm", (x, y + 0.3 * g, zz), (x, y + 0.7 * g, zz), 0.015, "k_holz", seiten=5))
    return tt


def tafel_ticker(pos, dreh, b, h, zeilen=4):
    """Dunkle Kurstafel mit leuchtenden Zeilen (ohne Schrift)."""
    tt = [f("tafel", (b, h, 0.04), pos, "k_tafel", dreh),
          f("tafel_rahmen", (b + 0.04, 0.03, 0.05), punkt(pos, dreh, (0, h / 2 + 0.015, 0)), "k_messing", dreh)]
    for k in range(zeilen):
        yy = h / 2 - (k + 0.8) * h / (zeilen + 0.6)
        tt.append(f("ticker", (b * 0.42, h * 0.07, 0.004), punkt(pos, dreh, (-b * 0.22, yy, 0.022)), "schirm", dreh))
        tt.append(f("ticker", (b * 0.2, h * 0.07, 0.004), punkt(pos, dreh, (b * 0.25, yy, 0.022)),
                    "k_licht_gruen" if k % 3 != 1 else "k_licht_rot", dreh))
    return tt


def staffelei(pos, h=1.3, b=0.5):
    x, y, zz = pos
    return [stab("staffel_bein", (x - b * 0.4, y, zz + 0.08), (x - 0.03, y + h, zz - 0.02), 0.014, "k_holz_dunkel", 5),
            stab("staffel_bein", (x + b * 0.4, y, zz + 0.08), (x + 0.03, y + h, zz - 0.02), 0.014, "k_holz_dunkel", 5),
            stab("staffel_bein", (x, y, zz - 0.2), (x, y + h * 0.95, zz - 0.04), 0.012, "k_holz_dunkel", 5),
            f("staffel_ablage", (b * 0.8, 0.025, 0.06), (x, y + h * 0.42, zz + 0.05), "k_holz_dunkel")]


# =============================================================================
# intake -- Marktdaten. Designertisch hinten, Stuhl davor.
# Platz 1 Tisch links + dahinter, Platz 2 rechts, Platz 3 vorn links.
# =============================================================================

I_H = 0.74
I_AUF = I_H + 0.002
I_TZ = -0.68


def intake_basis():
    t = [q("tisch_platte", (1.3, 0.04, 0.6), (-0.2, I_H - 0.02, I_TZ), "k_marmor", r=(0.012, 1)),
         f("tisch_zarge", (1.2, 0.05, 0.5), (-0.2, I_H - 0.065, I_TZ), "k_holz_dunkel")]
    for sx in (-0.78, 0.38):
        for sz in (-0.92, -0.44):
            t.append(stab("tisch_bein", (sx, 0.0, sz), (sx + (0.04 if sx > 0 else -0.04) * 0, I_H - 0.09, sz), 0.018, "k_messing", 6))
    # Designerstuhl, schaut zum Tisch (-z)
    c = (-0.2, 0.0, -0.02)
    t.append(q("stuhl_sitz", (0.46, 0.06, 0.44), (c[0], 0.46, c[2]), "k_leder", r=(0.02, 1)))
    t.append(q("stuhl_lehne", (0.46, 0.34, 0.05), (c[0], 0.68, c[2] + 0.2), "k_leder", (-8, 0, 0), r=(0.02, 1)))
    for sx in (-0.19, 0.19):
        for sz in (-0.17, 0.17):
            t.append(stab("stuhl_bein", (c[0] + sx * 1.1, 0, c[2] + sz * 1.1), (c[0] + sx, 0.43, c[2] + sz), 0.012, "k_messing", 5))
    t += pflanze_hoch((0.85, 0.0, 0.8), 0.7)
    return t


def _zwei_monitore():
    t = []
    for x in (-0.62, -0.18):
        t += monitor((x, I_AUF, -0.84), (0, 0, 0), 0.42, 0.26, "kurve", fuss_hoehe=0.1)
    t.append(q("tastatur", (0.36, 0.02, 0.12), (-0.4, I_AUF + 0.01, -0.58), "k_schwarz"))
    return t


def intake_a1_0():
    t = [f("staender", (0.16, 0.012, 0.12), (-0.4, I_AUF + 0.006, -0.72), "k_messing"),
         f("staender_steg", (0.03, 0.14, 0.02), (-0.4, I_AUF + 0.07, -0.78), "k_messing", (20, 0, 0))]
    p = (-0.4, I_AUF + 0.13, -0.75)
    t.append(f("tablet", (0.26, 0.18, 0.012), p, "k_schwarz", (-20, 0, 0)))
    t += schirm_inhalt(p, (-20, 0, 0), 0.23, 0.15, "kurve", tiefe=0.007)
    return t


def intake_a1_1():
    return _zwei_monitore()


def _monitorrahmen(x0=-0.36, z0=-0.9, reihen=(0.98, 1.24)):
    t = [f("halter_fuss", (0.3, 0.02, 0.18), (x0, I_AUF + 0.01, z0), "k_schwarz"),
         f("halter_stange", (0.04, reihen[-1] - I_AUF, 0.04), (x0, (reihen[-1] + I_AUF) / 2, z0 - 0.03), "k_schwarz")]
    for y in reihen:
        t.append(f("halter_quer", (1.0, 0.03, 0.03), (x0, y, z0 - 0.05), "k_schwarz"))
        for k, x in enumerate((x0 - 0.34, x0, x0 + 0.34)):
            p = (x, y, z0 - 0.01)
            t.append(f("gehaeuse", (0.33, 0.22, 0.03), p, "k_schwarz"))
            t += schirm_inhalt(p, (0, 0, 0), 0.3, 0.19, ("kurve", "balken", "schlange")[(k + int(y * 10)) % 3], tiefe=0.017)
    return t


def intake_a1_2():
    return _monitorrahmen()


def intake_a1_3():
    t = _zwei_monitore()
    cx, cy, cz = -0.35, 1.42, -1.02
    t.append(f("wand_rahmen", (1.12, 0.68, 0.05), (cx, cy, cz), "k_schwarz"))
    for r in range(2):
        for s in range(3):
            p = (cx - 0.36 + s * 0.36, cy + 0.16 - r * 0.32, cz + 0.026)
            t += schirm_inhalt(p, (0, 0, 0), 0.34, 0.3, ("kurve", "balken", "video", "schlange", "kurve", "plan")[r * 3 + s], tiefe=0.0)
    for x in (-0.86, 0.16):
        t.append(f("wand_bein", (0.04, cy - 0.34, 0.04), (x, (cy - 0.34) / 2, cz), "k_schwarz"))
        t.append(f("wand_fuss", (0.08, 0.02, 0.1), (x, 0.01, cz + 0.02), "k_schwarz"))
    return t


I_N = (0.8, -0.62)


def _hocker_n():
    return rundtisch((I_N[0], 0, I_N[1]), 0.2, 0.46, "k_holz_dunkel")


def intake_a2_0():
    t = _hocker_n()
    t.append(f("zeitung", (0.28, 0.02, 0.2), (I_N[0], 0.472, I_N[1]), "papier", (0, 12, 0)))
    t.append(f("zeitung_bild", (0.1, 0.003, 0.08), (I_N[0] - 0.05, 0.483, I_N[1]), "grau_mittel", (0, 12, 0)))
    for k in range(3):
        t.append(f("zeitung_zeile", (0.1, 0.003, 0.012), (I_N[0] + 0.07, 0.483, I_N[1] - 0.05 + k * 0.04), "grau_hell", (0, 12, 0)))
    return t


def intake_a2_1():
    t = _hocker_n()
    y = 0.462
    t.append(q("radio", (0.3, 0.18, 0.12), (I_N[0], y + 0.09, I_N[1]), "k_holz", r=(0.02, 1)))
    t.append(z("radio_lautsprecher", 0.05, 0.01, (I_N[0] - 0.06, y + 0.09, I_N[1] + 0.06), "k_creme", seiten=10, dreh=(90, 0, 0)))
    t.append(f("radio_skala", (0.09, 0.05, 0.006), (I_N[0] + 0.08, y + 0.11, I_N[1] + 0.062), "k_licht_gold"))
    t.append(stab("antenne", (I_N[0] + 0.1, y + 0.18, I_N[1]), (I_N[0] + 0.2, y + 0.42, I_N[1] - 0.05), 0.005, "k_stahl", 4))
    return t


def _schrank_n(h=0.42):
    return [q("lowboard", (0.48, h, 0.4), (I_N[0], h / 2, I_N[1] - 0.2), "k_holz_dunkel", r=(0.015, 1)),
            f("lowboard_griff", (0.2, 0.015, 0.01), (I_N[0], h * 0.6, I_N[1]), "k_messing")]


def intake_a2_2():
    t = _schrank_n()
    t += monitor((I_N[0], 0.422, I_N[1] - 0.25), (0, 0, 0), 0.46, 0.3, "video", fuss_hoehe=0.03)
    return t


def intake_a2_3():
    x, zz = I_N[0], I_N[1] - 0.22
    t = [f("saeule_fuss", (0.46, 0.04, 0.34), (x, 0.02, zz), "k_schwarz"),
         f("saeule", (0.08, 1.6, 0.06), (x, 0.84, zz - 0.04), "k_schwarz")]
    for r in range(2):
        for s in range(2):
            p = (x - 0.12 + s * 0.24, 1.3 - r * 0.22, zz)
            t.append(f("gehaeuse", (0.23, 0.2, 0.03), p, "k_schwarz"))
            t += schirm_inhalt(p, (0, 0, 0), 0.2, 0.17, ("video", "chat", "balken", "kurve")[r * 2 + s], tiefe=0.017)
    t.append(f("laufband", (0.5, 0.06, 0.03), (x, 1.55, zz), "k_schwarz"))
    t.append(f("laufband_licht", (0.46, 0.03, 0.004), (x, 1.55, zz + 0.017), "k_licht_gold"))
    return t


I_K = (-0.78, 0.68)


def intake_a3_0():
    t = rundtisch((I_K[0], 0, I_K[1]), 0.2, 0.55)
    t += wg.tasse((I_K[0], 0.552, I_K[1]), "k_weiss", hoehe=0.07, radius=0.035)
    return t


def intake_a3_1():
    t = rundtisch((I_K[0], 0, I_K[1]), 0.2, 0.55)
    x, y, zz = I_K[0] + 0.05, 0.552, I_K[1] - 0.03
    t += [z("kanne_unten", 0.05, 0.08, (x, y, zz), "k_stahl", seiten=8, r_oben=0.04),
          z("kanne_oben", 0.04, 0.09, (x, y + 0.08, zz), "k_stahl", seiten=8, r_oben=0.05),
          z("kanne_deckel", 0.03, 0.02, (x, y + 0.17, zz), "k_schwarz", seiten=8),
          f("kanne_griff", (0.02, 0.07, 0.02), (x - 0.07, y + 0.12, zz), "k_schwarz")]
    t += wg.tasse((I_K[0] - 0.09, 0.552, I_K[1] + 0.08), "k_weiss", hoehe=0.07, radius=0.035)
    return t


def _siebtraeger(x, y, zz, s=1.0):
    return [q("maschine", (0.3 * s, 0.3 * s, 0.26 * s), (x, y + 0.15 * s, zz), "k_stahl", r=(0.02, 1)),
            f("maschine_band", (0.302 * s, 0.05 * s, 0.262 * s), (x, y + 0.24 * s, zz), "k_rot"),
            f("maschine_griff", (0.12, 0.02, 0.03), (x, y + 0.12 * s, zz + 0.16 * s), "k_schwarz"),
            z("maschine_tasse", 0.025, 0.04, (x, y + 0.01, zz + 0.08 * s), "k_weiss", seiten=6)]


def intake_a3_2():
    x, zz = I_K[0], I_K[1] - 0.02
    t = [f("wagen_boden", (0.48, 0.03, 0.4), (x, 0.2, zz), "k_holz_dunkel"),
         q("wagen_platte", (0.5, 0.03, 0.42), (x, 0.74, zz), "k_marmor")]
    for sx in (-0.22, 0.22):
        for sz in (-0.18, 0.18):
            t.append(f("wagen_bein", (0.03, 0.72, 0.03), (x + sx, 0.38, zz + sz), "k_messing"))
            t.append(z("wagen_rad", 0.03, 0.02, (x + sx, 0.0, zz + sz), "k_schwarz", seiten=6))
    t += _siebtraeger(x - 0.05, 0.755, zz - 0.02, 0.9)
    t += wg.tasse((x + 0.17, 0.755, zz + 0.1), "k_weiss", hoehe=0.06, radius=0.03, voll=False)
    return t


def intake_a3_3():
    x, zz = -0.8, 0.6
    t = [q("theke", (0.55, 0.9, 0.9), (x, 0.45, zz), "k_holz_dunkel", r=(0.02, 1)),
         q("theke_platte", (0.6, 0.04, 0.95), (x, 0.92, zz), "k_marmor", r=(0.012, 1)),
         f("theke_band", (0.004, 0.05, 0.86), (x + 0.277, 0.2, zz), "k_messing"),
         f("theke_band", (0.004, 0.05, 0.86), (x + 0.277, 0.7, zz), "k_messing")]
    t += _siebtraeger(x, 0.94, zz - 0.18)
    t += [z("muehle", 0.06, 0.2, (x + 0.02, 0.94, zz + 0.17), "k_schwarz", seiten=8),
          z("muehle_bohnen", 0.07, 0.1, (x + 0.02, 1.14, zz + 0.17), "k_holz", seiten=8, r_oben=0.09)]
    for k in range(3):
        t += wg.tasse((x - 0.1 + k * 0.1, 0.94, zz + 0.38), "k_weiss", hoehe=0.06, radius=0.028, voll=k == 1)
    return t


INTAKE = {
    "basis": intake_basis,
    "plaetze": {
        1: {0: intake_a1_0, 1: intake_a1_1, 2: intake_a1_2, 3: intake_a1_3},
        2: {0: intake_a2_0, 1: intake_a2_1, 2: intake_a2_2, 3: intake_a2_3},
        3: {0: intake_a3_0, 1: intake_a3_1, 2: intake_a3_2, 3: intake_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.10,
    "figur": None,
}


# =============================================================================
# processing -- Depot. Ledersessel (Blick -z), Beistelltisch vorn links.
# Platz 1 hinten links (Aktien), Platz 2 hinten rechts (Anleihen),
# Platz 3 vorn rechts (Rohstoffe). Sitzpunkt (0 | 0,48 | 0,05) bleibt frei.
# =============================================================================

P_SITZ = (0.0, 0.48, 0.05)


def processing_basis():
    t = sessel((0.0, 0.0, 0.05), 180.0, b=0.7, t=0.66, mat="k_leder", lehne_h=0.5)
    t += rundtisch((-0.66, 0.0, 0.42), 0.2, 0.5, "k_marmor")
    t += wg.tasse((-0.7, 0.502, 0.4), "k_weiss", hoehe=0.06, radius=0.03)
    t.append(q("teppich", (1.0, 0.012, 0.86), (0.0, 0.006, 0.05), "k_samt_blau", r=(0.0, 0)))
    return t


def processing_a1_0():
    t = staffelei((-0.55, 0.0, -0.78), 1.1, 0.5)
    t += zertifikat((-0.55, 0.72, -0.72), (-8, 0, 0), 0.36, 0.46)
    return t


def _paneel(x=-0.58, zz=-0.96, b=0.94, h=1.6):
    return [q("paneel", (b, h, 0.06), (x, h / 2 + 0.02, zz), "k_holz_dunkel", r=(0.01, 1)),
            f("paneel_fuss", (b + 0.04, 0.02, 0.16), (x, 0.01, zz + 0.02), "k_messing")]


def processing_a1_1():
    t = _paneel()
    for (dx, y, b, h) in ((-0.2, 1.25, 0.32, 0.4), (0.2, 1.25, 0.32, 0.4), (-0.2, 0.75, 0.32, 0.4), (0.2, 0.8, 0.3, 0.3)):
        t += zertifikat((-0.58 + dx, y, -0.915), (0, 0, 0), b, h)
    return t


def processing_a1_2():
    t = _paneel()
    t += tafel_ticker((-0.58, 1.1, -0.9), (0, 0, 0), 0.84, 0.86, 5)
    t += zertifikat((-0.58, 0.42, -0.915), (0, 0, 0), 0.3, 0.26)
    return t


def processing_a1_3():
    t = processing_a1_2()
    t += sockel((-0.88, 0.0, -0.58), 0.24, 0.8, "k_holz_dunkel")
    x, y, zz = -0.88, 0.8, -0.58
    t += [f("glocke_buegel", (0.03, 0.26, 0.03), (x - 0.07, y + 0.13, zz), "k_holz_dunkel"),
          f("glocke_buegel", (0.03, 0.26, 0.03), (x + 0.07, y + 0.13, zz), "k_holz_dunkel"),
          f("glocke_quer", (0.18, 0.03, 0.04), (x, y + 0.27, zz), "k_holz_dunkel"),
          z("glocke", 0.1, 0.14, (x, y + 0.08, zz), "k_gold", seiten=12, r_oben=0.045),
          kugel("glocke_kloeppel", 0.02, (x, y + 0.06, zz), "k_gold_dunkel", stufen=1)]
    return t


A_X = 0.6


def _bank():
    return [q("bank", (0.64, 0.08, 0.36), (A_X, 0.34, -0.8), "k_leder_dunkel", r=(0.02, 1)),
            f("bank_gestell", (0.6, 0.02, 0.3), (A_X, 0.12, -0.8), "k_messing")] + \
        [f("bank_bein", (0.03, 0.3, 0.03), (A_X + sx, 0.15, -0.8 + sz), "k_messing")
         for sx in (-0.28, 0.28) for sz in (-0.14, 0.14)]


def processing_a2_0():
    t = _bank()
    t.append(q("mappe", (0.3, 0.03, 0.22), (A_X - 0.08, 0.396, -0.8), "k_leder", (0, 10, 0), r=(0.008, 1)))
    t.append(f("mappe_band", (0.3, 0.004, 0.03), (A_X - 0.08, 0.413, -0.8), "k_messing", (0, 10, 0)))
    return t


def processing_a2_1():
    t = processing_a2_0()
    x, y, zz = A_X + 0.14, 0.38, -0.8
    t += [q("koffer", (0.36, 0.26, 0.1), (x, y + 0.13, zz), "k_schwarz", r=(0.012, 1)),
          f("koffer_griff", (0.1, 0.03, 0.02), (x, y + 0.275, zz), "k_leder"),
          f("koffer_schloss", (0.03, 0.02, 0.006), (x - 0.1, y + 0.23, zz + 0.052), "k_gold"),
          f("koffer_schloss", (0.03, 0.02, 0.006), (x + 0.1, y + 0.23, zz + 0.052), "k_gold")]
    return t


BINDER = ["k_samt_blau", "k_rot", "k_samt_gruen", "k_creme", "k_leder"]


def processing_a2_2():
    x, zz, b, h = A_X, -0.88, 0.86, 1.3
    t = [q("regal_hinten", (b, h, 0.03), (x, h / 2, zz - 0.13), "k_holz_dunkel", r=(0.0, 0))]
    for s in (-1, 1):
        t.append(f("regal_seite", (0.03, h, 0.3), (x + s * (b / 2 - 0.015), h / 2, zz), "k_holz_dunkel"))
    for i, y in enumerate((0.03, 0.45, 0.87, 1.28)):
        t.append(f("regal_boden", (b, 0.03, 0.3), (x, y, zz), "k_holz_dunkel"))
        if i < 3:
            for k in range(9):
                t.append(f("ordner", (0.07, 0.34, 0.25), (x - 0.35 + k * 0.087, y + 0.19, zz + 0.01), BINDER[(k + i) % 5]))
    return t


def processing_a2_3():
    x, zz, b, h = A_X, -0.86, 0.86, 1.55
    t = [q("archiv", (b, h, 0.36), (x, h / 2, zz), "k_holz", r=(0.015, 1)),
         f("archiv_deckel", (b + 0.03, 0.03, 0.39), (x, h + 0.015, zz), "k_holz_dunkel")]
    for r in range(4):
        for s in range(2):
            y = 0.22 + r * 0.37
            xx = x - 0.21 + s * 0.42
            t.append(f("schublade", (0.38, 0.32, 0.006), (xx, y, zz + 0.182), "k_holz_dunkel"))
            t.append(f("schild", (0.1, 0.05, 0.004), (xx, y + 0.08, zz + 0.186), "k_creme"))
            t.append(f("griff", (0.12, 0.02, 0.02), (xx, y - 0.02, zz + 0.195), "k_messing"))
    return t


R_P = (0.78, 0.0, 0.66)


def processing_a3_0():
    t = sockel(R_P, 0.3, 0.8)
    t.append(f("muenzstaender", (0.1, 0.02, 0.06), (R_P[0], 0.81, R_P[2]), "k_holz_dunkel"))
    t += muenze((R_P[0], 0.82 + 0.07, R_P[2]), 0.07, liegend=False, dreh=(90, 0, 0))
    return t


def processing_a3_1():
    t = sockel(R_P, 0.3, 0.8)
    for i, (dx, dz, n) in enumerate(((-0.07, -0.06, 6), (0.06, -0.05, 9), (-0.04, 0.07, 4), (0.07, 0.07, 7))):
        t += muenzstapel((R_P[0] + dx, 0.802, R_P[2] + dz), n, 0.045)
    return t


def processing_a3_2():
    x, zz = R_P[0], R_P[2]
    t = [q("tisch", (0.56, 0.04, 0.46), (x, 0.6, zz), "k_holz_dunkel", r=(0.01, 1))]
    for sx in (-0.24, 0.24):
        for sz in (-0.19, 0.19):
            t.append(f("tisch_bein", (0.03, 0.58, 0.03), (x + sx, 0.29, zz + sz), "k_messing"))
    t += barrenpyramide((x, 0.622, zz), 3, 1.0)
    return t


def processing_a3_3():
    x, zz = R_P[0], R_P[2]
    t = [q("vitrine_sockel", (0.52, 0.5, 0.52), (x, 0.25, zz), "k_holz_dunkel", r=(0.015, 1)),
         f("vitrine_kante", (0.54, 0.02, 0.54), (x, 0.51, zz), "k_messing"),
         f("vitrine_glas", (0.46, 0.78, 0.46), (x, 0.91, zz), "k_glas"),
         f("vitrine_deckel", (0.52, 0.04, 0.52), (x, 1.32, zz), "k_messing"),
         f("vitrine_boden", (0.44, 0.02, 0.44), (x, 0.9, zz), "k_glas")]
    t += barrenpyramide((x, 0.521, zz), 2, 1.0)
    t += barren((x - 0.09, 0.911, zz), 20.0)
    t += barren((x + 0.09, 0.911, zz + 0.02), -15.0)
    t.append(z("vitrine_licht", 0.06, 0.01, (x, 1.29, zz), "k_licht_gold", seiten=8))
    return t


PROCESSING = {
    "basis": processing_basis,
    "plaetze": {
        1: {0: processing_a1_0, 1: processing_a1_1, 2: processing_a1_2, 3: processing_a1_3},
        2: {0: processing_a2_0, 1: processing_a2_1, 2: processing_a2_2, 3: processing_a2_3},
        3: {0: processing_a3_0, 1: processing_a3_1, 2: processing_a3_2, 3: processing_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.10,
    "figur": [("sitz", P_SITZ)],
    "frei": [(P_SITZ[0], P_SITZ[2], 0.3, 1.3)],
}


# =============================================================================
# buffer -- Analyse. Glastisch in der Mitte, Selin steht links (-0,9 | 0,3).
# Platz 1 auf dem Tisch (m3 Rechenschrank hinten links), Platz 2 hinten
# rechts (Charts), Platz 3 vorn (Beratung).
# =============================================================================

B_H = 0.74
B_AUF = B_H + 0.024
B_T = (0.15, -0.12)


def buffer_basis():
    x, zz = B_T
    t = [f("glasplatte", (1.1, 0.02, 0.62), (x, B_H, zz), "k_glas"),
         f("glas_boden", (0.9, 0.02, 0.44), (x, 0.2, zz), "k_glas")]
    for sx in (-0.5, 0.5):
        for sz in (-0.25, 0.25):
            t.append(f("bein", (0.035, B_H - 0.01, 0.035), (x + sx, (B_H - 0.01) / 2, zz + sz), "k_messing"))
        t.append(f("bein_quer", (0.03, 0.03, 0.5), (x + sx, B_H - 0.03, zz), "k_messing"))
        t.append(f("bein_quer", (0.03, 0.03, 0.5), (x + sx, 0.19, zz), "k_messing"))
    t.append(f("traverse", (1.0, 0.03, 0.03), (x, B_H - 0.03, zz - 0.26), "k_messing"))
    t += [f("ablage_buch", (0.24, 0.04, 0.18), (x + 0.25, 0.23, zz), "k_samt_blau"),
          f("ablage_buch", (0.22, 0.03, 0.17), (x + 0.25, 0.265, zz), "k_creme")]
    return t


def buffer_a1_0():
    x, zz = B_T[0] - 0.12, B_T[1] + 0.05
    return [f("notizbuch", (0.2, 0.02, 0.26), (x, B_AUF, zz), "k_leder", (0, 15, 0)),
            f("notiz_seite", (0.17, 0.003, 0.23), (x, B_AUF + 0.011, zz), "papier", (0, 15, 0)),
            stab("stift", (x + 0.14, B_AUF + 0.006, zz - 0.1), (x + 0.16, B_AUF + 0.006, zz + 0.06), 0.006, "k_gold", 5)]


def buffer_a1_1():
    return laptop((B_T[0] - 0.12, B_AUF - 0.01, B_T[1]), (0, -90, 0), 0.38, 0.26, mat="k_stahl", inhalt="kurve")


def buffer_a1_2():
    x, zz = B_T[0] - 0.05, B_T[1]
    t = monitor((x + 0.12, B_AUF - 0.01, zz), (0, -90, 0), 0.5, 0.3, "kurve", fuss_hoehe=0.1)
    t.append(q("tastatur", (0.13, 0.02, 0.36), (x - 0.18, B_AUF, zz), "k_schwarz"))
    t.append(q("rechner", (0.14, 0.34, 0.3), (x + 0.28, B_AUF - 0.01 + 0.17, zz - 0.02), "k_schwarz", r=(0.012, 1)))
    t.append(f("rechner_led", (0.006, 0.2, 0.01), (x + 0.21, B_AUF + 0.17, zz + 0.1), "k_licht_gold"))
    return t


def buffer_a1_3():
    t = buffer_a1_1()
    x, zz = -0.76, -0.85
    t += [q("rack", (0.5, 1.6, 0.36), (x, 0.8, zz), "k_schwarz", r=(0.015, 1)),
          f("rack_tuer", (0.44, 1.5, 0.006), (x, 0.82, zz + 0.182), "k_tafel")]
    for k in range(9):
        t.append(f("rack_led", (0.3, 0.02, 0.004), (x - 0.04, 0.2 + k * 0.155, zz + 0.186), "k_licht_gruen" if k % 3 else "k_holo"))
        t.append(f("rack_led", (0.03, 0.02, 0.004), (x + 0.16, 0.2 + k * 0.155, zz + 0.186), "k_licht_gold"))
    return t


C_X, C_Z = 0.55, -0.85


def _kurve(pos, dreh, b, h, mat="k_licht_gruen", n=5, dicke=0.018):
    """Aufsteigende Zickzack-Kurve aus schmalen Staeben in der lokalen x/y-Ebene."""
    werte = (0.15, 0.35, 0.25, 0.6, 0.5, 0.85, 0.95)[:n + 1]
    t = []
    for i in range(n):
        a = punkt(pos, dreh, (-b / 2 + b * i / n, -h / 2 + h * werte[i], 0))
        e = punkt(pos, dreh, (-b / 2 + b * (i + 1) / n, -h / 2 + h * werte[i + 1], 0))
        t.append(stab("kurve", a, e, dicke / 2, mat, 4))
    return t


def buffer_a2_0():
    t = staffelei((C_X, 0.0, C_Z), 1.5, 0.6)
    p = (C_X, 1.05, C_Z + 0.07)
    t.append(f("flipchart", (0.6, 0.8, 0.02), p, "papier", (-8, 0, 0)))
    t += _kurve(punkt(p, (-8, 0, 0), (0, 0, 0.02)), (-8, 0, 0), 0.44, 0.5, "k_samt_blau", 4, 0.02)
    return t


def _stellwand(mat="k_weiss", h_bis=1.65, b=0.95):
    t = [f("tafel", (b, 0.75, 0.03), (C_X, h_bis - 0.375, C_Z), mat)]
    t.append(f("tafel_rahmen", (b + 0.03, 0.03, 0.04), (C_X, h_bis, C_Z), "k_messing"))
    for s in (-1, 1):
        t.append(f("tafel_stiel", (0.03, h_bis, 0.03), (C_X + s * (b / 2 + 0.03), h_bis / 2, C_Z), "k_messing"))
        t.append(f("tafel_fuss", (0.05, 0.03, 0.36), (C_X + s * (b / 2 + 0.03), 0.015, C_Z), "k_messing"))
    return t


def buffer_a2_1():
    t = _stellwand("k_weiss")
    t += _kurve((C_X - 0.1, 1.28, C_Z + 0.02), (0, 0, 0), 0.6, 0.5, "k_samt_blau", 5, 0.015)
    t.append(f("notiz", (0.12, 0.12, 0.004), (C_X + 0.32, 1.45, C_Z + 0.017), "gelb"))
    return t


def buffer_a2_2():
    t = _stellwand("k_glas", 1.75)
    t += _kurve((C_X, 1.38, C_Z + 0.022), (0, 0, 0), 0.8, 0.55, "k_licht_gold", 6, 0.02)
    t += _kurve((C_X, 1.3, C_Z + 0.024), (0, 0, 0), 0.8, 0.35, "k_holo", 4, 0.014)
    return t


def buffer_a2_3():
    t = _stellwand("k_tafel", 1.75)
    for k in range(6):
        hk = 0.12 + 0.07 * k
        t.append(f("balken", (0.08, hk, 0.006), (C_X - 0.33 + k * 0.13, 1.03 + hk / 2, C_Z + 0.02),
                   "k_licht_gold" if k == 5 else "k_holo"))
    t += _kurve((C_X, 1.38, C_Z + 0.03), (0, 0, 0), 0.8, 0.5, "k_licht_gruen", 6, 0.016)
    return t


def buffer_a3_0():
    return sessel((0.72, 0.0, 0.74), 180.0 + 20.0, b=0.54, t=0.52, mat="k_samt_gruen")


def buffer_a3_1():
    return buffer_a3_0() + sessel((0.0, 0.0, 0.74), 180.0 - 15.0, b=0.54, t=0.52, mat="k_samt_gruen")


def buffer_a3_2():
    t = sessel((0.72, 0.0, 0.74), 180.0 + 25.0, b=0.52, t=0.5, mat="k_samt_blau")
    t += sessel((-0.22, 0.0, 0.74), 180.0 - 25.0, b=0.52, t=0.5, mat="k_samt_blau")
    t += rundtisch((0.26, 0.0, 0.9), 0.14, 0.42)
    t += wg.tasse((0.24, 0.422, 0.88), "k_weiss", hoehe=0.06, radius=0.028)
    return t


def buffer_a3_3():
    t = sessel((0.84, 0.0, 0.74), -90.0, b=0.52, t=0.48, mat="k_leder")
    t += sessel((-0.2, 0.0, 0.8), 90.0, b=0.52, t=0.48, mat="k_leder")
    x, zz = 0.32, 0.8
    t += [z("feuer_sockel", 0.24, 0.24, (x, 0.0, zz), "k_marmor", seiten=12),
          z("feuer_schale", 0.2, 0.08, (x, 0.24, zz), "k_schwarz", seiten=12, r_oben=0.24),
          z("feuer_glut", 0.17, 0.01, (x, 0.3, zz), "k_licht_gold", seiten=10)]
    for dx, dz, h in ((0.0, 0.0, 0.32), (0.08, 0.04, 0.2), (-0.07, -0.03, 0.24), (0.02, -0.08, 0.17)):
        t.append(z("flamme", 0.05, h, (x + dx, 0.31, zz + dz), "k_feuer", seiten=6, r_oben=0.004))
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
    "figur": [("steh", (-0.9, 0.0, 0.3))],
    "frei": [(-0.9, 0.3, 0.26, 1.7)],
}


# =============================================================================
# transport -- Streuung. Rundes Podest in der Mitte (Platz 1 steht darauf),
# Platz 2 links (Branchen), Platz 3 rechts (Tresor).
# =============================================================================

T_P = 0.13      # Podesthoehe


def transport_basis():
    return [z("podest", 0.55, T_P - 0.02, (0, 0, -0.05), "k_marmor", seiten=20),
            z("podest_ring", 0.56, 0.02, (0, T_P - 0.02, -0.05), "k_messing", seiten=20),
            z("podest_licht", 0.5, 0.004, (0, 0.03, -0.05), "k_licht_gold", seiten=20, r_oben=0.5)] + \
        [z("podest_stufe", 0.35, 0.01, (0, T_P - 0.009, -0.05), "k_marmor_ader", seiten=16)]


def _globus(pos, r, stand_h):
    x, y, zz = pos
    t = [z("globus_fuss", r * 0.55, 0.03, (x, y, zz), "k_holz_dunkel", seiten=10),
         z("globus_stiel", 0.02, stand_h, (x, y + 0.03, zz), "k_messing", seiten=6)]
    c = (x, y + 0.03 + stand_h + r, zz)
    t.append(kugel("globus", r, c, "k_meer", stufen=2))
    for dx, dy, dz, s in ((0.5, 0.3, 0.6, 0.45), (-0.55, 0.1, 0.55, 0.4), (0.1, -0.5, 0.7, 0.35), (0.7, -0.2, -0.1, 0.3), (-0.2, 0.6, -0.4, 0.35)):
        n = math.sqrt(dx * dx + dy * dy + dz * dz)
        t.append(kugel("land", r * s, (c[0] + dx / n * r * 0.82, c[1] + dy / n * r * 0.82, c[2] + dz / n * r * 0.82),
                       "k_land", stufen=1, skala=(1, 0.7, 1)))
    t.append(ring("globus_ring", r + 0.03, 0.008, c, "k_messing", dreh=(90, 0, 20), segmente=16, quer=4, anteil=0.55))
    return t


def transport_a1_0():
    return _globus((0, T_P + 0.002, -0.05), 0.2, 0.62)


def _kartentafel(leucht=False):
    t = []
    y0, h, b, zz = T_P + 0.55, 0.62, 0.92, -0.2
    for s in (-1, 1):
        t.append(f("karte_stiel", (0.04, y0 + h - T_P, 0.04), (s * (b / 2 - 0.05), T_P + (y0 + h - T_P) / 2 + 0.002, zz), "k_messing"))
        t.append(f("karte_fuss", (0.08, 0.02, 0.3), (s * (b / 2 - 0.05), T_P + 0.012, zz), "k_messing"))
    t.append(f("karte", (b, h, 0.03), (0, y0 + h / 2, zz), "k_tafel" if leucht else "k_meer"))
    land = "k_licht_gold" if leucht else "k_land"
    for (dx, dy, bb, hh) in ((-0.3, 0.12, 0.18, 0.2), (-0.22, -0.14, 0.1, 0.22), (0.02, 0.12, 0.12, 0.14),
                            (0.05, -0.1, 0.12, 0.2), (0.25, 0.12, 0.26, 0.16), (0.32, -0.18, 0.12, 0.08)):
        t.append(f("kontinent", (bb, hh, 0.006), (dx, y0 + h / 2 + dy, zz + 0.018), land))
    if leucht:
        for (dx, dy) in ((-0.3, 0.14), (0.05, -0.05), (0.28, 0.1), (-0.2, -0.16), (0.32, -0.17)):
            t.append(kugel("punkt", 0.022, (dx, y0 + h / 2 + dy, zz + 0.03), "k_licht_rot", stufen=1))
        t.append(f("karte_glanz", (b + 0.02, 0.02, 0.05), (0, y0 + h + 0.01, zz), "k_karte_licht"))
    return t


def transport_a1_1():
    return _kartentafel(False) + _globus((0.0, T_P + 0.002, 0.2), 0.1, 0.2)


def transport_a1_2():
    return _kartentafel(True) + _globus((0.0, T_P + 0.002, 0.2), 0.1, 0.2)


def transport_a1_3():
    c = (0, 1.05, -0.05)
    t = [z("holo_sockel", 0.3, 0.1, (0, T_P + 0.002, -0.05), "k_schwarz", seiten=16),
         z("holo_linse", 0.24, 0.01, (0, T_P + 0.102, -0.05), "k_holo", seiten=16),
         z("holo_strahl", 0.22, 0.45, (0, T_P + 0.11, -0.05), "k_holo", seiten=12, r_oben=0.06),
         kugel("holo_kugel", 0.34, c, "k_holo", stufen=2)]
    for w in (0, 60, 120):
        t.append(ring("holo_meridian", 0.35, 0.006, c, "k_licht_gold", dreh=(90, w, 0), segmente=16, quer=3))
    t.append(ring("holo_aequator", 0.36, 0.006, c, "k_licht_gold", segmente=16, quer=3))
    t.append(ring("holo_bahn", 0.46, 0.01, c, "k_holo", dreh=(20, 0, 10), segmente=18, quer=3))
    return t


S_X = -0.84


def transport_a2_0():
    t = sockel((S_X, 0.0, -0.1), 0.26, 0.8)
    t.append(q("ordner", (0.07, 0.3, 0.24), (S_X, 0.8 + 0.15, -0.1), "k_samt_blau", (0, 0, 8)))
    t.append(f("ordner_schild", (0.004, 0.08, 0.05), (S_X + 0.037, 0.97, -0.1), "k_creme", (0, 0, 8)))
    return t


def _ordnerbank(n=8):
    t = [q("bord", (0.36, 0.5, 0.9), (S_X, 0.25, -0.1), "k_holz_dunkel", r=(0.012, 1)),
         f("bord_kante", (0.38, 0.02, 0.92), (S_X, 0.51, -0.1), "k_messing")]
    for k in range(n):
        t.append(f("ordner", (0.25, 0.3, 0.07), (S_X, 0.52 + 0.15, -0.46 + k * 0.1), BINDER[k % 5]))
    return t


def transport_a2_1():
    return _ordnerbank()


def _kachelwand(zz=-0.1, b=1.3, h=1.3):
    t = [f("kachelwand", (0.05, h, b), (S_X - 0.1, 0.35 + h / 2, zz), "k_weiss"),
         f("kachelwand_fuss", (0.3, 0.03, 0.5), (S_X - 0.05, 0.015, zz), "k_messing"),
         f("kachelwand_stiel", (0.05, 0.36, 0.08), (S_X - 0.1, 0.18, zz), "k_messing")]
    mats = ["k_kachel_a", "k_kachel_b", "k_kachel_c", "k_kachel_d", "k_gold"]
    for r in range(4):
        for s in range(4):
            t.append(f("kachel", (0.006, 0.26, 0.26), (S_X - 0.072, 0.35 + 0.17 + r * 0.31, zz - 0.465 + s * 0.31), mats[(r * 3 + s) % 5]))
    return t


def transport_a2_2():
    return _kachelwand()


def transport_a2_3():
    x = S_X - 0.08
    t = [z("mobile_fuss", 0.16, 0.03, (x, 0, -0.5), "k_messing", seiten=10),
         f("mobile_mast", (0.04, 1.7, 0.04), (x, 0.85, -0.5), "k_messing"),
         f("mobile_arm", (0.03, 0.03, 1.1), (x, 1.68, 0.02), "k_messing")]
    mats = ["k_kachel_a", "k_kachel_b", "k_kachel_c", "k_kachel_d", "k_gold"]
    for i, (dz, y, w) in enumerate(((-0.25, 1.2, 20), (0.0, 0.95, -30), (0.22, 1.3, 45), (0.45, 1.05, 10), (-0.05, 1.45, -15))):
        t.append(stab("faden", (x, 1.665, dz), (x, y + 0.1, dz), 0.003, "k_schwarz", 3))
        t.append(q("kachel", (0.02, 0.2, 0.2), (x, y, dz), mats[i], (0, w, 0), r=(0.0, 0)))
    return t


V_X = 0.84


def transport_a3_0():
    t = rundtisch((V_X, 0.0, 0.1), 0.2, 0.46, "k_holz_dunkel")
    t += [q("kassette", (0.26, 0.1, 0.18), (V_X, 0.46 + 0.05, 0.1), "k_stahl", r=(0.01, 1)),
          f("kassette_griff", (0.1, 0.015, 0.02), (V_X, 0.57, 0.1), "k_schwarz"),
          f("kassette_schloss", (0.03, 0.03, 0.004), (V_X, 0.52, 0.19), "k_gold")]
    return t


def _tresortuer(x, y, zz, b, h, rad=0.05):
    return [f("tuer", (b, h, 0.012), (x, y, zz), "k_stahl"),
            z("rad", rad, 0.03, (x, y, zz), "k_messing", seiten=10, dreh=(90, 0, 0)),
            f("speiche", (rad * 3, 0.012, 0.012), (x, y, zz + 0.03), "k_messing"),
            f("speiche", (0.012, rad * 3, 0.012), (x, y, zz + 0.03), "k_messing")]


def transport_a3_1():
    t = [q("pfeiler", (0.4, 1.3, 0.34), (V_X, 0.65, -0.2), "k_holz_dunkel", r=(0.012, 1)),
         f("pfeiler_kante", (0.42, 0.03, 0.36), (V_X, 1.31, -0.2), "k_messing")]
    t += _tresortuer(V_X, 0.9, -0.2 + 0.172, 0.32, 0.34, 0.06)
    return t


def transport_a3_2():
    t = [q("schrank", (0.42, 0.95, 0.44), (V_X, 0.475, -0.1), "k_schwarz", r=(0.02, 1)),
         f("schrank_sockel", (0.44, 0.05, 0.46), (V_X, 0.025, -0.1), "k_messing")]
    t += _tresortuer(V_X, 0.52, -0.1 + 0.222, 0.34, 0.8, 0.07)
    t.append(z("zahlenrad", 0.035, 0.02, (V_X - 0.1, 0.7, -0.1 + 0.232), "k_gold", seiten=10, dreh=(90, 0, 0)))
    return t


def transport_a3_3():
    x = 0.77
    t = [q("tresor_block", (0.26, 1.45, 1.3), (x, 0.725, -0.1), "k_stahl", r=(0.02, 1)),
         f("tresor_kante", (0.28, 0.04, 1.32), (x, 1.47, -0.1), "k_messing")]
    c = (0.93, 0.72, -0.1)
    t.append(zylinder("tresor_tuer", 0.52, 0.06, c, "k_messing", seiten=20, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(zylinder("tresor_ring", 0.4, 0.02, (c[0] + 0.04, c[1], c[2]), "k_gold_dunkel", seiten=18, dreh=(0, 0, 90), rund=(0, 0)))
    t.append(zylinder("tresor_nabe", 0.09, 0.08, (c[0] + 0.08, c[1], c[2]), "k_stahl", seiten=10, dreh=(0, 0, 90), rund=(0, 0)))
    for w in (0, 60, 120):
        t.append(f("tresor_speiche", (0.02, 0.5, 0.03), (c[0] + 0.13, c[1], c[2]), "k_stahl", (w, 0, 0)))
    for dy, dz in ((0.3, 0.3), (-0.3, 0.3), (0.3, -0.3), (-0.3, -0.3)):
        t.append(kugel("bolzen", 0.03, (c[0] + 0.035, c[1] + dy, c[2] + dz), "k_stahl", stufen=1))
    return t


TRANSPORT = {
    "basis": transport_basis,
    "plaetze": {
        1: {0: transport_a1_0, 1: transport_a1_1, 2: transport_a1_2, 3: transport_a1_3},
        2: {0: transport_a2_0, 1: transport_a2_1, 2: transport_a2_2, 3: transport_a2_3},
        3: {0: transport_a3_0, 1: transport_a3_1, 2: transport_a3_2, 3: transport_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": -1.10,
    "figur": None,
}


# =============================================================================
# special -- Dividenden. Sideboard hinten (Platz 2 steht darauf), Platz 1
# vorn in der Mitte, Platz 3 rechts. Roman (-0,9 | 0,5), Younes (0,9 | 0,9).
# =============================================================================

D_H = 0.72
D_AUF = D_H + 0.025
D_Z = -0.82


def special_basis():
    t = [q("sideboard", (1.6, D_H - 0.12, 0.42), (0, 0.12 + (D_H - 0.12) / 2, D_Z), "k_holz_dunkel", r=(0.015, 1)),
         q("sideboard_platte", (1.66, 0.022, 0.46), (0, D_H + 0.011, D_Z), "k_marmor", r=(0.006, 1))]
    for k in range(4):
        x = -0.6 + k * 0.4
        t.append(f("front", (0.37, D_H - 0.2, 0.006), (x, 0.12 + (D_H - 0.12) / 2, D_Z + 0.212), "k_holz"))
        t.append(f("griff", (0.012, 0.14, 0.02), (x + (0.14 if k % 2 == 0 else -0.14), 0.44, D_Z + 0.222), "k_messing"))
    for sx in (-0.74, 0.74):
        for sz in (-0.16, 0.16):
            t.append(f("bein", (0.03, 0.12, 0.03), (sx, 0.06, D_Z + sz), "k_messing"))
    t += pflanze_hoch((-0.97, 0.0, -0.85), 0.6)
    return t


U_P = (-0.08, 0.0, -0.12)


def special_a1_0():
    t = sockel(U_P, 0.3, 0.55)
    x, y, zz = U_P[0], 0.552, U_P[2]
    t += [kugel("schwein", 0.12, (x, y + 0.13, zz), "k_rosa", stufen=2, skala=(1.25, 1.0, 0.95)),
          z("schwein_ruessel", 0.04, 0.04, (x + 0.15, y + 0.13, zz), "k_rosa", seiten=8, dreh=(0, 0, 90)),
          f("schwein_schlitz", (0.07, 0.01, 0.012), (x, y + 0.25, zz), "k_schwarz"),
          kugel("schwein_ohr", 0.035, (x + 0.08, y + 0.23, zz - 0.05), "k_rosa", stufen=1, skala=(1, 1.2, 0.5)),
          kugel("schwein_ohr", 0.035, (x + 0.08, y + 0.23, zz + 0.05), "k_rosa", stufen=1, skala=(1, 1.2, 0.5))]
    for sx in (-0.07, 0.07):
        for sz in (-0.05, 0.05):
            t.append(z("schwein_bein", 0.025, 0.05, (x + sx, y, zz + sz), "k_rosa", seiten=6))
    t += muenze((x + 0.06, y, zz + 0.1), 0.03)
    return t


def special_a1_1():
    t = sockel(U_P, 0.36, 0.55)
    x, y, zz = U_P[0], 0.552, U_P[2]
    t += [q("kasse", (0.3, 0.14, 0.26), (x, y + 0.07, zz), "k_gold", r=(0.015, 1)),
          q("kasse_aufsatz", (0.22, 0.14, 0.12), (x, y + 0.21, zz - 0.06), "k_gold", (-15, 0, 0), r=(0.012, 1)),
          f("kasse_anzeige", (0.14, 0.06, 0.006), (x, y + 0.24, zz), "k_licht_gold", (-15, 0, 0)),
          f("kasse_lade", (0.26, 0.05, 0.006), (x, y + 0.035, zz + 0.132), "k_gold_dunkel")]
    for r in range(2):
        for s in range(3):
            t.append(f("taste", (0.04, 0.012, 0.03), (x - 0.06 + s * 0.06, y + 0.146, zz + 0.04 + r * 0.05), "k_creme"))
    return t


def special_a1_2():
    x, zz = U_P[0], U_P[2]
    t = [z("becken", 0.36, 0.22, (x, 0, zz), "k_marmor", seiten=18),
         z("wasser", 0.32, 0.005, (x, 0.2, zz), "k_wasser", seiten=16),
         z("saeule", 0.05, 0.5, (x, 0.2, zz), "k_marmor", seiten=8),
         z("schale", 0.16, 0.06, (x, 0.62, zz), "k_messing", seiten=12, r_oben=0.2),
         z("schale_wasser", 0.17, 0.005, (x, 0.675, zz), "k_wasser", seiten=12),
         z("spitze", 0.03, 0.2, (x, 0.68, zz), "k_gold", seiten=6, r_oben=0.005),
         z("strahl", 0.16, 0.44, (x, 0.2, zz), "k_wasser", seiten=12, r_oben=0.19)]
    for i in range(7):
        w = i * 2 * math.pi / 7
        t += muenze((x + math.cos(w) * 0.22, 0.207, zz + math.sin(w) * 0.22), 0.025)
    return t


def special_a1_3():
    x, zz = U_P[0], U_P[2]
    t = sockel((x, 0.0, zz), 0.4, 0.3, "k_holz_dunkel")
    t.append(z("saeule", 0.035, 1.2, (x, 0.3, zz), "k_gold", seiten=8, r_oben=0.015))
    for i in range(14):
        w = i * 0.9
        r = 0.08 + 0.012 * i
        y = 1.45 - i * 0.075
        if i % 3 == 0:
            t.append(kugel("tropfen", 0.035, (x + math.cos(w) * r, y, zz + math.sin(w) * r), "k_gold", stufen=1, skala=(1, 1.4, 1)))
        else:
            t += muenze((x + math.cos(w) * r, y, zz + math.sin(w) * r), 0.035, liegend=False, dreh=(90, math.degrees(w), 0))
    t.append(kugel("krone", 0.07, (x, 1.52, zz), "k_licht_gold", stufen=1))
    return t


def special_a2_0():
    return glas_sekt((0.0, D_AUF, D_Z + 0.05), 1.2)


def special_a2_1():
    x, zz = -0.35, D_Z
    t = [z("kuehler", 0.1, 0.2, (x, D_AUF, zz), "k_messing", seiten=10, r_oben=0.12),
         z("eis", 0.11, 0.01, (x, D_AUF + 0.19, zz), "k_eis", seiten=10)]
    t += [stab("flasche", (x, D_AUF + 0.05, zz), (x + 0.04, D_AUF + 0.3, zz), 0.04, "k_samt_gruen", 8),
          stab("flasche_hals", (x + 0.04, D_AUF + 0.3, zz), (x + 0.055, D_AUF + 0.4, zz), 0.016, "k_gold", 6)]
    t += glas_sekt((0.0, D_AUF, D_Z + 0.05), 1.2)
    t += glas_sekt((0.15, D_AUF, D_Z + 0.02), 1.2)
    return t


def special_a2_2():
    t = [z("tablett", 0.24, 0.015, (0.05, D_AUF, D_Z), "k_messing", seiten=16)]
    y = D_AUF + 0.015
    for lage, (n, r) in enumerate(((6, 0.15), (3, 0.08), (1, 0.0))):
        for i in range(n):
            w = i * 2 * math.pi / max(n, 1) + lage
            t += glas_sekt((0.05 + math.cos(w) * r, y, D_Z + math.sin(w) * r), 1.1)
        y += 0.17
    t += special_a2_1()[:4]
    return t


def special_a2_3():
    x0, zz = 0.0, D_Z - 0.1
    t = [f("barregal_rueck", (1.3, 0.72, 0.02), (x0, D_AUF + 0.36, zz - 0.09), "k_holz_dunkel"),
         f("barregal_licht", (1.2, 0.02, 0.02), (x0, D_AUF + 0.7, zz - 0.07), "k_licht_gold")]
    for s in (-1, 1):
        t.append(f("barregal_seite", (0.02, 0.72, 0.2), (x0 + s * 0.64, D_AUF + 0.36, zz), "k_messing"))
    for y in (0.3, 0.62):
        t.append(f("barregal_boden", (1.26, 0.02, 0.2), (x0, D_AUF + y, zz), "k_glas"))
    mats = ["k_samt_gruen", "k_gold_dunkel", "k_rot", "k_holz", "k_eis"]
    for k in range(5):
        t += flasche((x0 - 0.5 + k * 0.25, D_AUF, zz + 0.02), mats[k % 5], 0.26)
        if k < 4:
            t += flasche((x0 - 0.4 + k * 0.27, D_AUF + 0.31, zz), mats[(k + 2) % 5], 0.24)
    t += glas_sekt((0.2, D_AUF, D_Z + 0.14), 1.1)
    t += glas_sekt((0.36, D_AUF, D_Z + 0.12), 1.1)
    return t


G_X = 0.8


def special_a3_0():
    return sessel((G_X, 0.0, 0.0), -90.0, b=0.52, t=0.5, mat="k_samt_blau")


def special_a3_1():
    return sofa((G_X, 0.0, 0.0), -90.0, b=1.0, t=0.52, mat="k_samt_blau")


def special_a3_2():
    t = sofa((G_X + 0.02, 0.0, -0.05), -90.0, b=0.9, t=0.5, mat="k_samt_blau")
    t += rundtisch((0.44, 0.0, 0.22), 0.1, 0.38, "k_marmor")
    t += glas_sekt((0.44, 0.382, 0.22), 0.9)
    t += pflanze_hoch((0.95, 0.0, 0.48), 0.45)
    return t


def special_a3_3():
    x, zz = G_X - 0.05, 0.0
    t = [q("buehne", (0.62, 0.14, 0.98), (x, 0.07, zz), "k_holz_dunkel", r=(0.012, 1)),
         f("buehne_kante", (0.64, 0.02, 1.0), (x, 0.15, zz), "k_messing"),
         z("mikro_fuss", 0.1, 0.02, (x - 0.12, 0.16, zz + 0.2), "k_schwarz", seiten=8),
         f("mikro_stange", (0.02, 1.25, 0.02), (x - 0.12, 0.16 + 0.625, zz + 0.2), "k_schwarz"),
         kugel("mikro", 0.035, (x - 0.16, 1.45, zz + 0.2), "k_gold", stufen=1, skala=(1, 1.4, 1)),
         q("pult", (0.34, 0.9, 0.3), (x + 0.12, 0.16 + 0.45, zz - 0.2), "k_holz", r=(0.012, 1)),
         f("pult_platte", (0.38, 0.03, 0.34), (x + 0.1, 1.08, zz - 0.2), "k_marmor", (0, 0, 12)),
         f("pult_emblem", (0.12, 0.12, 0.004), (x + 0.12, 0.7, zz - 0.048), "k_gold")]
    for k in range(3):
        t.append(z("spot", 0.03, 0.03, (x + 0.25, 0.16, zz - 0.4 + k * 0.4), "k_licht_gold", seiten=6))
    return t


SPECIAL = {
    "basis": special_basis,
    "plaetze": {
        1: {0: special_a1_0, 1: special_a1_1, 2: special_a1_2, 3: special_a1_3},
        2: {0: special_a2_0, 1: special_a2_1, 2: special_a2_2, 3: special_a2_3},
        3: {0: special_a3_0, 1: special_a3_1, 2: special_a3_2, 3: special_a3_3},
    },
    "flaeche": (-1.1, 1.1, -1.1, 1.1),
    "wand_z": None,
    "figur": [("steh", (-0.9, 0.0, 0.5)), ("steh", (0.9, 0.0, 0.9))],
    "frei": [(-0.9, 0.5, 0.26, 1.7), (0.9, 0.9, 0.26, 1.7)],
}


# =============================================================================
# Ablauf
# =============================================================================

STATIONEN = {"intake": INTAKE, "buffer": BUFFER, "processing": PROCESSING,
             "transport": TRANSPORT, "special": SPECIAL}
wg.STATIONEN = STATIONEN
bu.STATIONEN = STATIONEN

sy.AZIMUT = {
    ("intake", 0): 30, ("intake", 1): 20, ("intake", 2): 20, ("intake", 3): 30,
    ("buffer", 0): 35, ("buffer", 1): -40, ("buffer", 2): 20, ("buffer", 3): 20,
    ("processing", 0): 30, ("processing", 1): 20, ("processing", 2): 25, ("processing", 3): 30,
    ("transport", 0): 30, ("transport", 1): 25, ("transport", 2): 60, ("transport", 3): 60,
    ("special", 0): 30, ("special", 1): 25, ("special", 2): 25, ("special", 3): -60,
}
sy.MOTIVE = {}
sy.nachbearbeiten = bu.sticker
sy.FUELLUNG = 0.78


def fluss_teil():
    """Goldmuenze ohne Praegung, aufrecht, Ursprung Mitte, Durchmesser 0,3."""
    wg.alles_loeschen()
    teile = [zylinder("muenze", 0.15, 0.04, (0, 0, 0), "k_gold", seiten=20, dreh=(90, 0, 0), rund=(0.008, 1)),
             zylinder("muenze_feld", 0.115, 0.046, (0, 0, 0), "k_gold_dunkel", seiten=20, dreh=(90, 0, 0), rund=(0, 0)),
             zylinder("muenze_mitte", 0.07, 0.05, (0, 0, 0), "k_gold", seiten=16, dreh=(90, 0, 0), rund=(0, 0))]
    obj = wg.zusammenfuegen(teile, "fluss_teil")
    wg.exportieren(obj, AUSGABE_FLUSS)
    g = wg.grenzen(obj)
    print("  fluss_teil: %d Dreiecke, Masse %.2f x %.2f x %.2f" % (wg.dreiecke(obj), g[1] - g[0], g[3] - g[2], g[5] - g[4]))


def main():
    a = bu.argumente()
    print("")
    print("=== STATIONEN KAPITAL (N51) ===")
    probleme = 0
    budgets = {}
    for station in STATIONEN:
        if a["nur"] and station not in a["nur"]:
            continue
        print("--", station)
        probleme += wg.baue_station(station, export=not a["kein_export"])
        budgets[station], _ = bu.budget_pruefen(station)
        if not a["kein_export"]:
            bu.altmodelle(station)
        if a["vorschau"]:
            bu.vorschau_stufen(station)
        if a["symbole"]:
            os.makedirs(AUSGABE_UI, exist_ok=True)
            sy.symbole_station(station)
    if a["symbole"]:
        sy.kontaktbogen([s for s in STATIONEN if not a["nur"] or s in a["nur"]])
    if not a["kein_export"] and not a["nur"]:
        fluss_teil()
    print("")
    for s, n in budgets.items():
        print("  %-12s volle Ausstattung %5d Dreiecke%s" % (s, n, "" if n <= BUDGET_GESAMT else "  !! ueber Budget"))
    print("  Probleme gesamt: %d" % probleme)


if __name__ == "__main__":
    main()
