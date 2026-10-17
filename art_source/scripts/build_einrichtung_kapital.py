"""Raumeinrichtungen fuer Welt 6 `kapital` -- das Penthouse (Nachtplan N50).

Aufruf:
    blender --background --python art_source/scripts/build_einrichtung_kapital.py
    (optional nach "--": <zone> ... | --ohne-vorschau | --nur-vorschau | aussen)

Voraussetzung: build_room_kapital_neu.py ist gelaufen.

Erzeugt project/assets/world/kapital/:
    einrichtung_<zone>.glb  EIN Mesh je Zone, Ursprung = Zonenmitte
    umgebung.glb            Stadt tief unten ringsum, der Turm unter dem Penthouse
    fundament.glb           Dachplatte unter der Grundflaeche (+1 m Rand)
und Vorschaubilder nach art_source/vorschau/kapital/.

Grundriss (worlds.json / docs/nacht/karten_welten.md):
    lounge       x -4..4,   z 1..7   parkett (Start)
    galerie      x -12..12, z -3..0  marmor  bereich_1
    tresor       x -12..-5, z -9..-4 marmor  bereich_2
    boardroom    x -4..4,   z -9..-4 parkett bereich_3
    immobilien   x 5..12,   z -9..-4 parkett bereich_4
    kunstsalon   x -12..-5, z 1..7   marmor  bereich_5
    dachterrasse x 5..12,   z 1..7   deck    offen

Koordinaten: GODOT, Moebel lokal mit Vorderseite +z, Ursprung Mitte unten.
Keine echten Marken, Logos oder Kunstwerke.
"""

import bpy
import math
import os
import random
import sys
from mathutils import Matrix

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_room_wg import (  # noqa: E402
    G, kasten, zylinder, liegender_zylinder, kugel, transformieren, alles_loeschen,
    verbinden, dreiecke, masse, exportieren, vorschau_rendern, palette_erweitern, material, WURZEL,
)
import build_einrichtung_wg_a as wa  # noqa: E402
from build_einrichtung_wg_a import (  # noqa: E402
    stab, pflanze, teppich, setzen, moebel_bericht, freiflaechen_pruefen,
)
import build_room_kapital_neu as raum  # noqa: E402

AUSGABE = os.path.join(WURZEL, "project", "assets", "world", "kapital")
VORSCHAU = raum.AUSGABE_VORSCHAU
ZONEN_BUDGET = 8000
UMGEBUNG_BUDGET = 14000

palette_erweitern({
    "k6e_messing":     ("#F2B200", 0.35, 0.45, 1.0),
    "k6e_gold":        ("#FFC62E", 0.30, 0.55, 1.0),
    "k6e_messing_leg": ("#C98F12", 0.40, 0.45, 1.0),
    "k6e_holz_dunkel": ("#5B3A26", 0.60, 0.0, 1.0),
    "k6e_holz":        ("#9A6843", 0.65, 0.0, 1.0),
    "k6e_leder":       ("#8E4A2A", 0.60, 0.0, 1.0),
    "k6e_marmor":      ("#F4F1EC", 0.30, 0.0, 1.0),
    "k6e_weiss":       ("#FAF8F4", 0.70, 0.0, 1.0),
    "k6e_creme":       ("#F1E6D2", 0.90, 0.0, 1.0),
    "k6e_samt_gruen":  ("#2F7A64", 0.90, 0.0, 1.0),
    "k6e_samt_blau":   ("#35558F", 0.90, 0.0, 1.0),
    "k6e_samt_rosa":   ("#E7A3A0", 0.90, 0.0, 1.0),
    "k6e_senf":        ("#E0A63A", 0.90, 0.0, 1.0),
    "k6e_schwarz":     ("#26262B", 0.50, 0.2, 1.0),
    "k6e_anthrazit":   ("#4B4A52", 0.60, 0.0, 1.0),
    "k6e_grau":        ("#B9B5AE", 0.80, 0.0, 1.0),
    "k6e_rot":         ("#C8423A", 0.60, 0.0, 1.0),
    "k6e_tuerkis":     ("#2FB3A8", 0.60, 0.0, 1.0),
    "k6e_teppich":     ("#E9DCC6", 0.95, 0.0, 1.0),
    "k6e_teppich_rand": ("#C9A15A", 0.95, 0.0, 1.0),
    "k6e_glas":        ("#CFEAF4", 0.08, 0.0, 0.35),
    "k6e_topf":        ("#F4F1EC", 0.70, 0.0, 1.0),
    "k6e_modell":      ("#F7F4EE", 0.80, 0.0, 1.0),
    "k6e_modell_gruen": ("#9CCB7E", 0.90, 0.0, 1.0),
    "k6e_modell_blau": ("#8CC4E8", 0.40, 0.0, 1.0),
    "k6e_plan":        ("#DCE9F5", 0.90, 0.0, 1.0),
    "k6e_plan_linie":  ("#3F6FB0", 0.90, 0.0, 1.0),
    "k6e_bild_a":      ("#F2C14E", 0.90, 0.0, 1.0),
    "k6e_bild_b":      ("#E0664F", 0.90, 0.0, 1.0),
    "k6e_bild_c":      ("#5B8FD6", 0.90, 0.0, 1.0),
    "k6e_bild_d":      ("#7CC46A", 0.90, 0.0, 1.0),
    "k6e_auto":        ("#B8323A", 0.30, 0.2, 1.0),
    "k6e_auto_creme":  ("#F2E6CF", 0.40, 0.0, 1.0),
    "k6e_chrom":       ("#D9DDE2", 0.20, 0.8, 1.0),
    "k6e_reifen":      ("#2A2A2E", 0.90, 0.0, 1.0),
    "k6e_pool":        ("#58C7E8", 0.15, 0.0, 0.85),
    "k6e_pool_boden":  ("#8FDDF0", 0.60, 0.0, 1.0),
    "k6e_stoff_weiss": ("#FBF7EF", 0.95, 0.0, 1.0),
    "k6e_stoff_gold":  ("#F2C66B", 0.95, 0.0, 1.0),
    "k6e_juwel_rot":   ("#E0405A", 0.20, 0.0, 1.0),
    "k6e_juwel_gruen": ("#35C28A", 0.20, 0.0, 1.0),
    "k6e_juwel_blau":  ("#4F8FF0", 0.20, 0.0, 1.0),
    "k6e_perle":       ("#FFF8EE", 0.30, 0.0, 1.0),
    # leuchtend
    "k6e_licht":       ("#FFE2A0", 0.50, 0.0, 1.0),
    "k6e_diamant":     ("#DDF6FF", 0.10, 0.0, 1.0),
    "k6e_fenster_an":  ("#FFD98A", 0.50, 0.0, 1.0),
    "k6e_schirm":      ("#8CD4FF", 0.40, 0.0, 1.0),
    # Stadt
    "k6e_haus_a":      ("#5E6A92", 0.90, 0.0, 1.0),
    "k6e_haus_b":      ("#4E5F88", 0.90, 0.0, 1.0),
    "k6e_haus_c":      ("#7C6487", 0.90, 0.0, 1.0),
    "k6e_haus_d":      ("#44577F", 0.90, 0.0, 1.0),
    "k6e_haus_e":      ("#566D8A", 0.90, 0.0, 1.0),
    "k6e_turm":        ("#B7A38A", 0.80, 0.0, 1.0),
    "k6e_fenster":     ("#2C3856", 0.30, 0.0, 1.0),
    "k6e_dach":        ("#6E6A72", 0.90, 0.0, 1.0),
    "k6e_rasen":       ("#8DC262", 0.90, 0.0, 1.0),
    "k6e_platte":      ("#E4DDD2", 0.85, 0.0, 1.0),
    "k6e_platte_kante": ("#C9BFB0", 0.85, 0.0, 1.0),
    "k6e_dach_a":      ("#E0BC96", 0.9, 0.0, 1.0),
    "k6e_dach_b":      ("#CDAAA2", 0.9, 0.0, 1.0),
    "k6e_dach_c":      ("#AFC0D2", 0.9, 0.0, 1.0),
    "k6e_dachpool":    ("#4FC3E8", 0.2, 0.0, 1.0),
    "k6e_dachgruen":   ("#4C7A55", 0.9, 0.0, 1.0),
    "k6e_stadtboden":  ("#2A3148", 0.95, 0.0, 1.0),
    "k6e_fluss":       ("#3C5A8C", 0.15, 0.4, 1.0),
    "k6e_strassenlicht": ("#FFB45A", 0.5, 0.0, 1.0),
    "k6e_warnlicht":   ("#FF4A3A", 0.5, 0.0, 1.0),
    "k6e_wolke":       ("#F6D2BE", 0.95, 0.0, 1.0),
    "k6e_kran":        ("#E0A020", 0.60, 0.1, 1.0),
    "k6e_pad":         ("#4A4D56", 0.80, 0.0, 1.0),
    "k6e_pad_rand":    ("#FFF1D6", 0.60, 0.0, 1.0),
    "k6e_buchs":       ("#2E5B3C", 0.85, 0.0, 1.0),
    "k6e_buchs_hell":  ("#3F7A50", 0.85, 0.0, 1.0),
    "k6e_ticker_g":    ("#5CF08A", 0.40, 0.0, 1.0),
    "k6e_ticker_r":    ("#FF6A5A", 0.40, 0.0, 1.0),
    "k6e_strasse":     ("#2D3144", 0.90, 0.0, 1.0),
    "stamm":           ("#8A6446", 0.90, 0.0, 1.0),
})

LEUCHTEND = {"k6e_strassenlicht": 1.1, "k6e_warnlicht": 2.2, "k6e_pad_rand": 0.5, "k6e_ticker_g": 1.6,
            "k6e_ticker_r": 1.4, "k6e_pool": 0.5, "k6e_dachpool": 0.7, "k6e_licht": 1.6, "k6e_diamant": 1.2, "k6e_fenster_an": 1.7, "k6e_schirm": 0.8}


def leucht_materialien():
    for name, staerke in LEUCHTEND.items():
        mat = material(name)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Emission Color"].default_value = mat.diffuse_color
        bsdf.inputs["Emission Strength"].default_value = staerke


def bei(teile, x=0.0, y=0.0, z=0.0, dreh=0.0):
    teile = [t for t in teile if t is not None]
    transformieren(teile, x=x, z=z, y=y, dreh_grad=dreh)
    return teile


def box(name, s, m, mat, r=0.0, seg=1):
    return kasten(name, s, m, mat, rund=r, segmente=seg)


def zyl(name, r, h, unten, mat, seiten=10, r_oben=None):
    return zylinder(name, r, h, unten, mat, seiten=seiten, radius_oben=r_oben)


# ==============================================================================
# MOEBEL
# ==============================================================================

def sofa(b=2.0, t=0.9, stoff="k6e_samt_gruen", kissen="k6e_creme"):
    teile = [
        box("sofa_sockel", (b, 0.26, t), (0, 0.21, 0), stoff, r=0.04),
        box("sofa_lehne", (b, 0.42, 0.2), (0, 0.5, -t / 2 + 0.1), stoff, r=0.06),
        box("sofa_arm_l", (0.18, 0.24, t), (-b / 2 + 0.09, 0.44, 0), stoff, r=0.06),
        box("sofa_arm_r", (0.18, 0.24, t), (b / 2 - 0.09, 0.44, 0), stoff, r=0.06),
    ]
    n = 2 if b < 1.6 else 3
    sb = (b - 0.36) / n
    for i in range(n):
        teile.append(box("sofa_sitz", (sb - 0.02, 0.1, t - 0.26), (-b / 2 + 0.18 + sb * (i + 0.5), 0.39, 0.08), stoff, r=0.04))
    teile.append(box("sofa_kissen", (0.36, 0.3, 0.1), (-b / 2 + 0.42, 0.58, -t / 2 + 0.26), kissen, r=0.05))
    teile.append(box("sofa_kissen", (0.34, 0.28, 0.1), (b / 2 - 0.44, 0.58, -t / 2 + 0.26), "k6e_senf", r=0.05))
    for sx in (-1, 1):
        for sz in (-1, 1):
            teile.append(box("sofa_fuss", (0.05, 0.08, 0.05), (sx * (b / 2 - 0.08), 0.04, sz * (t / 2 - 0.08)), "k6e_messing"))
    return teile


def sessel(stoff="k6e_samt_blau", b=0.8, t=0.8):
    return [
        box("sessel_sockel", (b, 0.26, t), (0, 0.21, 0), stoff, r=0.05),
        box("sessel_lehne", (b, 0.44, 0.2), (0, 0.52, -t / 2 + 0.1), stoff, r=0.07),
        box("sessel_arm_l", (0.16, 0.22, t), (-b / 2 + 0.08, 0.44, 0), stoff, r=0.06),
        box("sessel_arm_r", (0.16, 0.22, t), (b / 2 - 0.08, 0.44, 0), stoff, r=0.06),
        box("sessel_sitz", (b - 0.32, 0.1, t - 0.24), (0, 0.39, 0.07), stoff, r=0.04),
        zyl("sessel_fuss", 0.2, 0.08, (0, 0, 0), "k6e_messing", seiten=8),
    ]


def couchtisch(r=0.45, h=0.4, platte="k6e_marmor"):
    return [
        zyl("ct_platte", r, 0.05, (0, h - 0.05, 0), platte, seiten=16),
        zyl("ct_fuss", r * 0.55, h - 0.05, (0, 0, 0), "k6e_messing", seiten=12, r_oben=r * 0.4),
    ]


def beistell(h=0.55):
    return [zyl("bt_platte", 0.22, 0.03, (0, h - 0.03, 0), "k6e_marmor", seiten=12),
            zyl("bt_fuss", 0.03, h - 0.03, (0, 0, 0), "k6e_messing", seiten=6),
            zyl("bt_teller", 0.16, 0.02, (0, 0, 0), "k6e_messing", seiten=10)]


def bogenlampe(h=2.0, weit=1.0):
    teile = [box("bl_sockel", (0.34, 0.12, 0.34), (0, 0.06, 0), "k6e_marmor", r=0.02)]
    punkte = [(0, 0.12), (0.05, h * 0.6), (weit * 0.4, h), (weit * 0.8, h * 0.97), (weit, h * 0.86)]
    for (ax, ay), (bx, by) in zip(punkte, punkte[1:]):
        teile.append(stab("bl_bogen", (ax, ay, 0), (bx, by, 0), 0.03, "k6e_messing"))
    teile.append(zyl("bl_schirm", 0.2, 0.16, (weit, h * 0.86 - 0.14, 0), "k6e_messing", seiten=12, r_oben=0.06))
    teile.append(kugel("bl_licht", 0.07, (weit, h * 0.86 - 0.15, 0), "k6e_licht", ringe=4, seiten=6))
    return teile


def topfpflanze(g=1.0, stil="hoch"):
    """Buchsbaum-Kegel im Marmorkuebel (Welt 6 kennt keinen Kugelbusch)."""
    teile = [box("topf", (0.34 * g, 0.4 * g, 0.34 * g), (0, 0.2 * g, 0), "k6e_marmor", r=0.02),
             box("topf_rand", (0.38 * g, 0.04 * g, 0.38 * g), (0, 0.4 * g, 0), "k6e_messing")]
    if stil == "hoch":
        teile.append(zyl("kegel", 0.26 * g, 0.9 * g, (0, 0.42 * g, 0), "k6e_buchs", seiten=8, r_oben=0.04 * g))
    else:
        teile.append(zyl("kegel_a", 0.27 * g, 0.4 * g, (0, 0.42 * g, 0), "k6e_buchs", seiten=8, r_oben=0.13 * g))
        teile.append(zyl("kegel_b", 0.19 * g, 0.4 * g, (0, 0.74 * g, 0), "k6e_buchs_hell", seiten=8, r_oben=0.03 * g))
    return teile


def olivenbaum(g=1.0):
    """Hoher Buchsbaum-Kegel auf Stamm im Kuebel (Name bleibt, damit die Zonen gleich bleiben)."""
    teile = [box("kuebel", (0.6 * g, 0.5 * g, 0.6 * g), (0, 0.25 * g, 0), "k6e_anthrazit", r=0.03),
             box("kuebel_rand", (0.64 * g, 0.04 * g, 0.64 * g), (0, 0.5 * g, 0), "k6e_messing"),
             zyl("stamm", 0.045 * g, 0.7 * g, (0, 0.5 * g, 0), "stamm", seiten=6),
             zyl("kegel_u", 0.42 * g, 0.7 * g, (0, 1.05 * g, 0), "k6e_buchs", seiten=8, r_oben=0.18 * g),
             zyl("kegel_o", 0.3 * g, 0.6 * g, (0, 1.6 * g, 0), "k6e_buchs_hell", seiten=8, r_oben=0.03 * g)]
    return teile


def sockel_mit(teile_oben, b=0.45, h=0.9, mat="k6e_marmor"):
    teile = [box("sockel", (b, h, b), (0, h / 2, 0), mat, r=0.015),
             box("sockel_kante", (b + 0.04, 0.03, b + 0.04), (0, h - 0.015, 0), "k6e_messing")]
    return teile + bei(teile_oben, y=h)


def skulptur(stil=0):
    if stil == 0:     # gestapelte Kiesel
        return [kugel("kiesel", 0.2, (0, 0.14, 0), "k6e_anthrazit", stauchung=0.6, ringe=5, seiten=8),
                kugel("kiesel", 0.15, (0.03, 0.36, 0), "k6e_weiss", stauchung=0.6, ringe=5, seiten=8),
                kugel("kiesel", 0.1, (-0.02, 0.52, 0.01), "k6e_gold", stauchung=0.65, ringe=4, seiten=8)]
    if stil == 1:     # Ring auf Stab
        teile = [stab("stab", (0, 0, 0), (0, 0.4, 0), 0.04, "k6e_schwarz")]
        for i in range(10):
            w = i * math.pi / 5
            teile.append(kugel("ring", 0.06, (math.cos(w) * 0.26, 0.66 + math.sin(w) * 0.26, 0), "k6e_gold", ringe=4, seiten=6))
        return teile
    if stil == 2:     # Spirale aus Wuerfeln
        teile = []
        for i in range(7):
            w = i * 0.55
            teile.append(box("wuerfel", (0.14, 0.12, 0.14), (math.cos(w) * 0.1, 0.06 + i * 0.12, math.sin(w) * 0.1),
                             ("k6e_weiss", "k6e_bild_c", "k6e_gold")[i % 3]))
        return teile
    # Figur abstrakt: Tropfen
    return [zyl("form", 0.2, 0.5, (0, 0, 0), "k6e_bild_b", seiten=10, r_oben=0.05),
            kugel("kopf", 0.13, (0, 0.62, 0), "k6e_bild_b", ringe=5, seiten=8)]


def bank(b=1.6, t=0.45, polster="k6e_leder"):
    return [box("bank_polster", (b, 0.12, t), (0, 0.4, 0), polster, r=0.04),
            box("bank_gestell_l", (0.06, 0.34, t - 0.06), (-b / 2 + 0.12, 0.17, 0), "k6e_messing"),
            box("bank_gestell_r", (0.06, 0.34, t - 0.06), (b / 2 - 0.12, 0.17, 0), "k6e_messing")]


def gemaelde(b=1.0, h=0.8, seed=0, rahmen="k6e_messing"):
    """Freies Farbfeldbild -- geometrische Formen, kein bekanntes Werk."""
    rng = random.Random(seed)
    farben = ["k6e_bild_a", "k6e_bild_b", "k6e_bild_c", "k6e_bild_d", "k6e_samt_gruen", "k6e_creme"]
    teile = [box("rahmen", (b, h, 0.05), (0, 0, 0), rahmen, r=0.01),
             box("leinwand", (b - 0.08, h - 0.08, 0.01), (0, 0, 0.026), rng.choice(["k6e_creme", "k6e_weiss"]))]
    for i in range(3):
        fb, fh = rng.uniform(0.2, 0.45) * b, rng.uniform(0.2, 0.45) * h
        fx = rng.uniform(-b / 2 + 0.05 + fb / 2, b / 2 - 0.05 - fb / 2)
        fy = rng.uniform(-h / 2 + 0.05 + fh / 2, h / 2 - 0.05 - fh / 2)
        teile.append(box("form", (fb, fh, 0.006), (fx, fy, 0.033 + i * 0.002), farben[(seed + i) % len(farben)]))
    return teile


def staffelei_bild(b=0.9, h=0.7, seed=0):
    teile = [stab("st_bein", (-0.35, 0, 0.15), (-0.04, 1.7, 0), 0.04, "k6e_holz_dunkel"),
             stab("st_bein", (0.35, 0, 0.15), (0.04, 1.7, 0), 0.04, "k6e_holz_dunkel"),
             stab("st_bein", (0, 0, -0.4), (0, 1.6, -0.02), 0.035, "k6e_holz_dunkel"),
             box("st_ablage", (0.8, 0.04, 0.1), (0, 0.72, 0.13), "k6e_holz_dunkel")]
    bild = bei(gemaelde(b, h, seed), y=0.74 + h / 2, z=0.1)
    for t in bild:
        t.matrix_world = Matrix.Translation(G(0, 0.74 + h / 2, 0.1)) @ Matrix.Rotation(math.radians(-8), 4, "X") @ \
            Matrix.Translation(-G(0, 0.74 + h / 2, 0.1)) @ t.matrix_world
    return teile + bild


def stellwand(b=2.0, h=2.0, bilder=((0, 1.0, 0.8, 0.6),), seed=0, mat="k6e_weiss"):
    teile = [box("stellwand", (b, h, 0.12), (0, h / 2 + 0.04, 0), mat, r=0.01),
             box("stellwand_fuss", (b, 0.04, 0.3), (0, 0.02, 0), "k6e_messing")]
    for i, (x, y, bb, hh) in enumerate(bilder):
        teile += bei(gemaelde(bb, hh, seed + i), x=x, y=y, z=0.085)
        teile.append(box("spot", (0.05, 0.05, 0.14), (x, h + 0.02, 0.1), "k6e_messing"))
    return teile


def absperrung(punkte, h=0.9):
    teile = []
    for (x, z) in punkte:
        teile += [zyl("pf_fuss", 0.12, 0.03, (x, 0, z), "k6e_messing", seiten=8),
                  zyl("pf_stange", 0.025, h, (x, 0.03, z), "k6e_messing", seiten=6),
                  kugel("pf_kopf", 0.045, (x, h + 0.04, z), "k6e_messing", ringe=4, seiten=6)]
    for (ax, az), (bx, bz) in zip(punkte, punkte[1:]):
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        teile.append(stab("kordel", (ax, h - 0.05, az), (mx, h - 0.25, mz), 0.03, "k6e_rot"))
        teile.append(stab("kordel", (mx, h - 0.25, mz), (bx, h - 0.05, bz), 0.03, "k6e_rot"))
    return teile


# --- Tresor ---------------------------------------------------------------------

def vitrine(b=1.2, t=0.6, h=1.0, seed=0, art="schmuck"):
    rng = random.Random(seed)
    teile = [box("vit_sockel", (b, 0.85, t), (0, 0.425, 0), "k6e_holz_dunkel", r=0.02),
             box("vit_kante", (b + 0.03, 0.03, t + 0.03), (0, 0.865, 0), "k6e_messing"),
             box("vit_samt", (b - 0.08, 0.02, t - 0.08), (0, 0.89, 0), "k6e_samt_blau"),
             box("vit_glas", (b - 0.02, 0.36, t - 0.02), (0, 1.07, 0), "k6e_glas"),
             box("vit_deckel", (b + 0.02, 0.02, t + 0.02), (0, 1.26, 0), "k6e_messing")]
    y = 0.9
    for i in range(6):
        x = -b / 2 + 0.14 + i * (b - 0.28) / 5
        zz = rng.uniform(-0.1, 0.1)
        if art == "schmuck":
            k = i % 3
            if k == 0:     # Kette auf Buste
                teile.append(zyl("buste", 0.05, 0.16, (x, y, zz), "k6e_samt_blau", seiten=6, r_oben=0.03))
                for j in range(5):
                    w = j * math.pi / 4 + math.pi
                    teile.append(kugel("perle", 0.018, (x + math.cos(w) * 0.06, y + 0.12 + math.sin(w) * 0.06, zz + 0.05), "k6e_perle", ringe=3, seiten=5))
            elif k == 1:   # Ring mit Stein
                teile.append(zyl("ring", 0.035, 0.012, (x, y, zz), "k6e_gold", seiten=8))
                teile.append(kugel("stein", 0.03, (x, y + 0.04, zz), rng.choice(["k6e_juwel_rot", "k6e_juwel_gruen", "k6e_juwel_blau"]), ringe=3, seiten=6))
            else:          # Kissen mit Brosche
                teile.append(box("kissen", (0.12, 0.03, 0.12), (x, y + 0.015, zz), "k6e_creme"))
                teile.append(kugel("brosche", 0.035, (x, y + 0.04, zz), "k6e_diamant", ringe=3, seiten=6))
        else:              # Uhren
            teile.append(box("uhr_kissen", (0.1, 0.06, 0.08), (x, y + 0.03, zz), "k6e_creme"))
            teile.append(zyl("uhr", 0.035, 0.015, (x, y + 0.06, zz), "k6e_gold" if i % 2 else "k6e_chrom", seiten=10))
    return teile


def uhrenwand(b=2.2, h=1.9):
    teile = [box("uw_wand", (b, h, 0.1), (0, h / 2, 0), "k6e_holz_dunkel", r=0.01),
             box("uw_kante", (b, 0.04, 0.14), (0, h, 0), "k6e_messing")]
    teile.append(box("uw_samt", (b - 0.2, 1.1, 0.02), (0, 1.05, 0.055), "k6e_samt_blau"))
    for r in range(2):
        for s in range(5):
            x = -b / 2 + 0.3 + s * (b - 0.6) / 4
            y = 0.8 + r * 0.5
            teile.append(liegender_zylinder("uw_uhr", 0.09, 0.03, (x, y, 0.08), "z",
                                            "k6e_gold" if (r + s) % 2 else "k6e_chrom", seiten=8))
            teile.append(box("uw_ziffer", (0.1, 0.1, 0.006), (x, y, 0.098), "k6e_weiss"))
            teile.append(box("uw_band", (0.05, 0.14, 0.01), (x, y - 0.14, 0.07), "k6e_leder"))
    teile.append(box("uw_licht", (b - 0.1, 0.03, 0.04), (0, h - 0.06, 0.07), "k6e_licht"))
    return teile


def diamant_podest():
    teile = [zyl("dp_sockel", 0.35, 0.95, (0, 0, 0), "k6e_marmor", seiten=12, r_oben=0.28),
             zyl("dp_kissen", 0.2, 0.06, (0, 0.95, 0), "k6e_samt_rosa", seiten=10),
             zyl("dp_oben", 0.12, 0.07, (0, 1.11, 0), "k6e_diamant", seiten=8, r_oben=0.17),
             zyl("dp_unten", 0.001, 0.12, (0, 0.99, 0), "k6e_diamant", seiten=8, r_oben=0.17),
             zyl("dp_haube", 0.26, 0.55, (0, 1.01, 0), "k6e_glas", seiten=12),
             zyl("dp_lichtring", 0.3, 0.02, (0, 0.93, 0), "k6e_licht", seiten=12)]
    teile += absperrung([(-0.7, 0.7), (0.7, 0.7)])
    return teile


def tresortuer(r=0.95):
    teile = [box("tt_rahmen", (2.4, 2.3, 0.3), (0, 1.15, 0), "k6e_grau", r=0.03),
             liegender_zylinder("tt_tuer", r, 0.14, (0, 1.15, 0.18), "z", "k6e_messing", seiten=24),
             liegender_zylinder("tt_ring", r * 0.78, 0.04, (0, 1.15, 0.27), "z", "k6e_gold", seiten=20),
             liegender_zylinder("tt_nabe", 0.14, 0.12, (0, 1.15, 0.33), "z", "k6e_chrom", seiten=10),
             liegender_zylinder("tt_halo", r * 1.14, 0.02, (0, 1.15, 0.16), "z", "k6e_licht", seiten=24)]
    for w in (0, 60, 120):
        g = kasten("tt_speiche", (0.06, 0.9, 0.05), (0, 0, 0), "k6e_chrom")
        g.matrix_world = Matrix.Translation(G(0, 1.15, 0.38)) @ Matrix.Rotation(math.radians(w), 4, "Y")
        teile.append(g)
    for i in range(8):
        w = i * math.pi / 4
        teile.append(liegender_zylinder("tt_bolzen", 0.05, 0.1, (math.cos(w) * r * 0.9, 1.15 + math.sin(w) * r * 0.9, 0.28), "z", "k6e_chrom", seiten=6))
    return teile


# --- Boardroom ---------------------------------------------------------------------

def konferenztisch(l=3.2, b=1.1):
    return [box("kt_platte", (b, 0.05, l), (0, 0.74, 0), "k6e_holz_dunkel", r=0.02),
            box("kt_intarsie", (0.08, 0.004, l - 0.4), (0, 0.767, 0), "k6e_messing"),
            box("kt_fuss", (0.2, 0.7, l * 0.25), (0, 0.36, -l * 0.28), "k6e_marmor", r=0.02),
            box("kt_fuss", (0.2, 0.7, l * 0.25), (0, 0.36, l * 0.28), "k6e_marmor", r=0.02)]


def chefsessel():
    return [box("cs_sitz", (0.52, 0.12, 0.5), (0, 0.46, 0), "k6e_leder", r=0.04),
            box("cs_lehne", (0.5, 0.62, 0.1), (0, 0.84, -0.22), "k6e_leder", r=0.04),
            zyl("cs_saeule", 0.035, 0.38, (0, 0.02, 0), "k6e_chrom", seiten=6),
            box("cs_kreuz", (0.56, 0.03, 0.06), (0, 0.03, 0), "k6e_chrom"),
            box("cs_kreuz", (0.06, 0.03, 0.56), (0, 0.03, 0), "k6e_chrom")]


def bildschirmwand(b=2.2, h=1.2):
    return [box("bw_rahmen", (b, h, 0.08), (0, 0.6 + h / 2, 0), "k6e_schwarz", r=0.01),
            box("bw_bild", (b - 0.1, h - 0.1, 0.01), (0, 0.6 + h / 2, 0.045), "k6e_schirm"),
            box("bw_balken", (0.2, 0.3, 0.004), (-0.5, 0.95, 0.052), "k6e_gold"),
            box("bw_balken", (0.2, 0.5, 0.004), (-0.2, 1.05, 0.052), "k6e_gold"),
            box("bw_balken", (0.2, 0.7, 0.004), (0.1, 1.15, 0.052), "k6e_gold"),
            box("bw_staender", (0.9, 0.6, 0.3), (0, 0.3, 0), "k6e_holz_dunkel", r=0.02)]


# --- Immobilien ------------------------------------------------------------------

def stadtmodell(b=3.0, t=1.7, seed=5):
    rng = random.Random(seed)
    h = 0.8
    teile = [box("sm_tisch", (b, 0.06, t), (0, h - 0.03, 0), "k6e_holz_dunkel", r=0.02),
             box("sm_platte", (b - 0.1, 0.03, t - 0.1), (0, h + 0.015, 0), "k6e_modell")]
    for sx in (-1, 1):
        teile.append(box("sm_wange", (0.08, h - 0.06, t - 0.3), (sx * (b / 2 - 0.25), (h - 0.06) / 2, 0), "k6e_holz_dunkel"))
    y = h + 0.03
    teile.append(box("sm_fluss", (b - 0.1, 0.004, 0.16), (0, y + 0.002, 0.25), "k6e_modell_blau"))
    teile.append(box("sm_park", (0.5, 0.004, 0.35), (-0.9, y + 0.002, -0.35), "k6e_modell_gruen"))
    for i in range(5):
        teile.append(kugel("sm_baum", 0.05, (-1.05 + i * 0.08, y + 0.05, -0.35 + (i % 2) * 0.12), "pflanze", ringe=3, seiten=5))
    for gx in range(9):
        for gz in range(4):
            x = -b / 2 + 0.3 + gx * (b - 0.6) / 8
            zz = -t / 2 + 0.2 + gz * 0.3
            if abs(zz - 0.25) < 0.14 or (x < -0.55 and x > -1.2 and zz < -0.1):
                continue
            hh = rng.choice((0.06, 0.1, 0.14, 0.2, 0.32)) * (1.6 if abs(x) < 0.5 else 1.0)
            mat = "k6e_gold" if rng.random() < 0.18 else "k6e_modell"
            teile.append(box("sm_haus", (0.16, hh, 0.16), (x, y + hh / 2, zz), mat))
    return teile


def hochhausmodell(h=1.0, seed=0):
    rng = random.Random(seed)
    teile = []
    y = 0.0
    b = 0.3
    for i in range(3):
        hh = h * (0.5, 0.3, 0.2)[i]
        teile.append(box("hm_stufe", (b, hh, b), (0, y + hh / 2, 0), rng.choice(["k6e_modell", "k6e_modell_blau"])))
        teile.append(box("hm_band", (b + 0.01, 0.015, b + 0.01), (0, y + hh, 0), "k6e_gold"))
        y += hh
        b *= 0.75
    teile.append(stab("hm_spitze", (0, y, 0), (0, y + 0.18, 0), 0.015, "k6e_gold"))
    return sockel_mit(teile, 0.45, 0.8)


def plantisch(b=1.4, t=0.8):
    teile = [box("pt_platte", (b, 0.04, t), (0, 0.92, 0), "k6e_holz", r=0.01)]
    for sx in (-1, 1):
        teile.append(box("pt_bein", (0.05, 0.9, t - 0.1), (sx * (b / 2 - 0.08), 0.45, 0), "k6e_anthrazit"))
    for i, (x, zz, w) in enumerate(((-0.3, 0.0, 8), (0.25, -0.05, -6), (0.05, 0.12, 3))):
        g = kasten("pt_plan", (0.6, 0.004, 0.42), (0, 0, 0), "k6e_plan")
        g.matrix_world = Matrix.Translation(G(x, 0.942 + i * 0.002, zz)) @ Matrix.Rotation(math.radians(w), 4, "Z")
        teile.append(g)
        for k in range(3):
            l = kasten("pt_linie", (0.4, 0.004, 0.012), (0, 0, 0), "k6e_plan_linie")
            l.matrix_world = g.matrix_world @ Matrix.Translation(G(0, 0.002, -0.12 + k * 0.12))
            teile.append(l)
    teile.append(liegender_zylinder("pt_rolle", 0.05, 0.7, (0.35, 0.99, -0.28), "x", "k6e_plan", seiten=8))
    return teile


def plantafel(b=1.2, h=0.9):
    teile = [box("pl_tafel", (b, h, 0.04), (0, 0.9 + h / 2, 0), "k6e_plan"),
             box("pl_rahmen", (b + 0.04, 0.04, 0.06), (0, 0.9 + h, 0), "k6e_messing"),
             stab("pl_bein", (-b / 2 + 0.1, 0, 0.2), (-b / 2 + 0.1, 0.9 + h, 0), 0.04, "k6e_messing"),
             stab("pl_bein", (b / 2 - 0.1, 0, 0.2), (b / 2 - 0.1, 0.9 + h, 0), 0.04, "k6e_messing")]
    for k in range(4):
        teile.append(box("pl_linie", (b * 0.7, 0.012, 0.004), (0, 1.0 + k * 0.2, 0.022), "k6e_plan_linie"))
    teile.append(box("pl_grundriss", (0.3, 0.3, 0.004), (b * 0.25, 1.35, 0.024), "k6e_plan_linie"))
    return teile


# --- Kunstsalon ------------------------------------------------------------------

def oldtimer():
    """Freier Oldtimer-Entwurf (kein reales Modell): Rot mit Creme, Chrom."""
    teile = [zyl("dt_teller", 1.55, 0.12, (0, 0, 0), "k6e_marmor", seiten=20),
             zyl("dt_ring", 1.57, 0.03, (0, 0.1, 0), "k6e_messing", seiten=24),
             zyl("dt_licht", 1.45, 0.005, (0, 0.121, 0), "k6e_licht", seiten=24)]
    y = 0.12
    auto = [
        box("au_wanne", (1.5, 0.36, 3.0), (0, 0.42, 0), "k6e_auto", r=0.1, seg=1),
        box("au_trittbrett", (1.62, 0.05, 1.6), (0, 0.3, 0), "k6e_auto_creme", r=0.02),
        box("au_kabine", (1.26, 0.42, 1.2), (0, 0.8, -0.2), "k6e_auto_creme", r=0.1, seg=1),
        box("au_scheibe", (1.1, 0.34, 0.04), (0, 0.84, 0.4), "k6e_glas"),
        box("au_seitenfenster", (1.28, 0.26, 0.8), (0, 0.84, -0.2), "k6e_fenster"),
        box("au_grill", (0.7, 0.24, 0.05), (0, 0.46, 1.5), "k6e_chrom", r=0.02),
        box("au_stange", (1.6, 0.06, 0.08), (0, 0.3, 1.55), "k6e_chrom", r=0.02),
        box("au_stange", (1.6, 0.06, 0.08), (0, 0.3, -1.55), "k6e_chrom", r=0.02),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            auto.append(kugel("au_kotfluegel", 0.42, (sx * 0.62, 0.42, sz * 0.95), "k6e_auto", stauchung=0.75, ringe=4, seiten=8))
            auto.append(liegender_zylinder("au_rad", 0.3, 0.2, (sx * 0.68, 0.3, sz * 0.95), "x", "k6e_reifen", seiten=10))
            auto.append(liegender_zylinder("au_felge", 0.16, 0.22, (sx * 0.68, 0.3, sz * 0.95), "x", "k6e_chrom", seiten=6))
        auto.append(kugel("au_lampe", 0.1, (sx * 0.5, 0.66, 1.3), "k6e_chrom", ringe=4, seiten=8))
        auto.append(kugel("au_lampe_glas", 0.07, (sx * 0.5, 0.66, 1.37), "k6e_licht", ringe=3, seiten=6))
    bei(auto, y=y, dreh=60.0)
    return teile + auto


# --- Dachterrasse ------------------------------------------------------------------

def pool(b=2.8, t=2.2):
    teile = [box("pool_rand", (b, 0.3, t), (0, 0.15, 0), "k6e_marmor", r=0.03),
             box("pool_wasser", (b - 0.3, 0.006, t - 0.3), (0, 0.304, 0), "k6e_pool")]
    for k in range(3):
        teile.append(box("pool_welle", (0.5, 0.004, 0.03), (-0.6 + k * 0.6, 0.309, -0.4 + k * 0.35), "k6e_weiss"))
    for sx in (-0.15, 0.15):
        teile.append(stab("leiter", (b / 2 - 0.4 + sx, 0.3, -t / 2 + 0.15), (b / 2 - 0.4 + sx, 0.85, -t / 2 + 0.1), 0.03, "k6e_chrom"))
    teile.append(liegender_zylinder("ring", 0.18, 0.1, (-0.5, 0.36, 0.3), "z", "k6e_rot", seiten=10))
    return teile


def liege():
    teile = [box("li_rahmen", (0.62, 0.1, 1.7), (0, 0.24, 0.1), "k6e_holz", r=0.02),
             box("li_polster", (0.56, 0.06, 1.2), (0, 0.32, 0.35), "k6e_stoff_weiss", r=0.02),
             box("li_handtuch", (0.4, 0.02, 0.5), (0, 0.36, 0.45), "k6e_stoff_gold")]
    g = box("li_lehne", (0.56, 0.06, 0.6), (0, 0, 0), "k6e_stoff_weiss", r=0.02)
    g.matrix_world = Matrix.Translation(G(0, 0.5, -0.55)) @ Matrix.Rotation(math.radians(40), 4, "X")
    teile.append(g)
    for sx in (-0.26, 0.26):
        for sz in (-0.65, 0.85):
            teile.append(box("li_bein", (0.05, 0.2, 0.05), (sx, 0.1, sz), "k6e_holz"))
    return teile


def sonnenschirm(r=1.1, h=2.3):
    return [zyl("ss_fuss", 0.25, 0.08, (0, 0, 0), "k6e_anthrazit", seiten=8),
            zyl("ss_mast", 0.03, h, (0, 0.08, 0), "k6e_holz", seiten=6),
            zyl("ss_dach", r, 0.35, (0, h - 0.25, 0), "k6e_stoff_weiss", seiten=8, r_oben=0.05),
            zyl("ss_rand", r + 0.01, 0.06, (0, h - 0.27, 0), "k6e_stoff_gold", seiten=8)]


def lichterkette(punkte, h=2.6, n=5):
    teile = []
    for (x, z) in punkte:
        teile.append(zyl("lk_pfosten", 0.04, h, (x, 0, z), "k6e_anthrazit", seiten=6))
        teile.append(zyl("lk_fuss", 0.16, 0.12, (x, 0, z), "k6e_anthrazit", seiten=8))
    for (ax, az), (bx, bz) in zip(punkte, punkte[1:]):
        pk = []
        for i in range(n + 1):
            s = i / n
            pk.append((ax + (bx - ax) * s, h - 0.05 - math.sin(s * math.pi) * 0.4, az + (bz - az) * s))
        for p, q in zip(pk, pk[1:]):
            teile.append(stab("lk_kabel", p, q, 0.012, "k6e_schwarz"))
        for p in pk[1:-1]:
            teile.append(kugel("lk_birne", 0.05, (p[0], p[1] - 0.06, p[2]), "k6e_licht", ringe=3, seiten=5))
    return teile


def aussenbar(b=2.2):
    teile = [box("ab_theke", (b, 1.0, 0.6), (0, 0.5, 0), "k6e_holz", r=0.03),
             box("ab_platte", (b + 0.1, 0.05, 0.7), (0, 1.02, 0.02), "k6e_marmor", r=0.01),
             box("ab_band", (b, 0.06, 0.01), (0, 0.8, 0.305), "k6e_messing"),
             box("ab_regal", (b, 0.04, 0.3), (0, 1.5, -0.55), "k6e_holz_dunkel"),
             box("ab_regal_rueck", (b, 1.0, 0.06), (0, 1.3, -0.7), "k6e_holz_dunkel")]
    farben = ["k6e_samt_gruen", "k6e_gold", "k6e_rot", "k6e_tuerkis"]
    for i in range(6):
        teile.append(zyl("ab_flasche", 0.04, 0.26, (-b / 2 + 0.3 + i * 0.32, 1.52, -0.55), farben[i % 4], seiten=6))
    for i in range(3):
        x = -b / 2 + 0.45 + i * 0.65
        teile += [zyl("ab_hocker", 0.2, 0.06, (x, 0.72, 0.62), "k6e_leder", seiten=10),
                  zyl("ab_hocker_bein", 0.03, 0.72, (x, 0, 0.62), "k6e_messing", seiten=6),
                  zyl("ab_hocker_fuss", 0.16, 0.03, (x, 0, 0.62), "k6e_messing", seiten=8)]
    teile.append(zyl("ab_glas", 0.04, 0.12, (0.3, 1.045, 0.1), "k6e_glas", seiten=6))
    return teile


def pflanzkasten(b=2.0, t=0.5, rng=None, busch=(0.2, 0.28)):
    rng = rng or random.Random(3)
    teile = [box("pk_kasten", (b, 0.5, t), (0, 0.25, 0), "k6e_anthrazit", r=0.02)]
    n = max(2, int(b / 0.4))
    for i in range(n):
        x = -b / 2 + 0.2 + i * (b - 0.4) / max(1, n - 1)
        teile.append(kugel("pk_busch", rng.uniform(*busch), (x, 0.5 + busch[0] * 0.6, rng.uniform(-0.02, 0.02)),
                           "pflanze" if i % 2 else "pflanze_dunkel", stauchung=0.8, ringe=4, seiten=7))
    return teile


# ==============================================================================
# ZONEN (Zonenkoordinaten, Ursprung Zonenmitte)
# ==============================================================================

def tickerwand(b=2.8, h=0.9, y0=1.3):
    """Kursanzeige an der Wand: dunkle Tafel, gruene Kurve, rote Ausschlaege (alles leuchtend)."""
    teile = [box("tk_rahmen", (b, h, 0.06), (0, y0 + h / 2, 0), "k6e_schwarz", r=0.01),
             box("tk_kopf", (b - 0.1, 0.05, 0.01), (0, y0 + h - 0.08, 0.035), "k6e_gold")]
    pts = [(-1.2, 0.15), (-0.9, 0.3), (-0.6, 0.22), (-0.3, 0.45), (0.0, 0.38), (0.3, 0.6), (0.6, 0.5), (0.9, 0.68),
           (1.2, 0.74)]
    for i in range(len(pts) - 1):
        teile.append(stab("kurve", (pts[i][0], y0 + 0.05 + pts[i][1] * 0.8, 0.04),
                          (pts[i + 1][0], y0 + 0.05 + pts[i + 1][1] * 0.8, 0.04), 0.03, "k6e_ticker_g"))
    for i, (x, hh, m) in enumerate(((-1.1, 0.12, "k6e_ticker_r"), (-0.5, 0.2, "k6e_ticker_g"), (0.2, 0.1, "k6e_ticker_r"),
                                    (0.8, 0.16, "k6e_ticker_g"), (1.15, 0.1, "k6e_ticker_r"))):
        teile.append(box("tk_balken", (0.09, hh, 0.01), (x, y0 + 0.1 + hh / 2, 0.035), m))
    return teile


def teleskop():
    teile = []
    for w in (0, 120, 240):
        a = math.radians(w)
        teile.append(stab("bein", (math.cos(a) * 0.3, 0.0, math.sin(a) * 0.3), (0, 1.0, 0), 0.03, "k6e_messing_leg"))
    teile.append(zyl("kopf", 0.08, 0.12, (0, 1.0, 0), "k6e_messing", seiten=8))
    teile.append(stab("rohr", (0.0, 1.1, 0.0), (0.4, 1.5, 0.2), 0.11, "k6e_messing"))
    teile.append(stab("okular", (-0.05, 1.08, -0.03), (-0.2, 1.0, -0.1), 0.05, "k6e_chrom"))
    return teile


def goldkugel():
    return [kugel("gk", 0.38, (0, 0.46, 0), "k6e_gold", ringe=6, seiten=12)]


def einrichtung_lounge():
    setzen("teppich_links", teppich(2.6, 2.4, "k6e_teppich", "k6e_teppich_rand"), x=-2.9, z=1.8)
    setzen("sofa_links", sofa(2.2, 0.9), x=-3.85, z=1.7, dreh=90)
    setzen("couchtisch_links", couchtisch(0.42), x=-2.55, z=1.7)
    setzen("sessel_links", sessel("k6e_senf", 0.76, 0.76), x=-2.4, z=3.0, dreh=180)
    setzen("bogenlampe", bogenlampe(2.0, 1.0), x=-4.1, z=0.4)
    setzen("teppich_rechts", teppich(2.4, 2.4, "k6e_teppich", "k6e_teppich_rand"), x=3.0, z=1.9)
    setzen("sofa_rechts", sofa(2.0, 0.86, "k6e_samt_blau"), x=3.9, z=1.8, dreh=-90)
    setzen("couchtisch_rechts", couchtisch(0.38, 0.38, "k6e_holz_dunkel"), x=2.8, z=1.8)
    setzen("sessel_rechts", sessel("k6e_samt_gruen", 0.76, 0.76), x=2.6, z=3.0, dreh=180)
    konsole = [box("konsole", (1.8, 0.45, 0.4), (0, 0.225, 0), "k6e_holz_dunkel", r=0.02),
               box("konsole_platte", (1.84, 0.03, 0.44), (0, 0.465, 0), "k6e_marmor"),
               zyl("schale", 0.18, 0.08, (-0.4, 0.48, 0), "k6e_gold", seiten=12, r_oben=0.22),
               zyl("vase", 0.07, 0.3, (0.5, 0.48, 0), "k6e_samt_gruen", seiten=8, r_oben=0.04)]
    konsole += bei(pflanze(0.35, "k6e_topf", "busch"), x=0.1, y=0.48)
    setzen("konsole", konsole, x=-0.2, z=3.1)
    setzen("pflanze_hinten_l", topfpflanze(1.2), x=-4.0, z=-2.9)
    setzen("pflanze_hinten_r", topfpflanze(1.2), x=4.0, z=-2.9)
    setzen("olive_vorn", olivenbaum(0.7), x=1.3, z=3.05)


def einrichtung_galerie():
    setzen("stellwand_l", stellwand(2.2, 1.5, ((-0.5, 0.95, 0.8, 0.6), (0.55, 0.9, 0.6, 0.7)), seed=11), x=-9.9, z=-1.55)
    setzen("stellwand_r", stellwand(2.2, 1.5, ((-0.5, 0.9, 0.7, 0.8), (0.5, 0.95, 0.8, 0.55)), seed=21), x=9.9, z=-1.55)
    setzen("stellwand_m", stellwand(2.0, 1.5, ((0.0, 0.9, 1.2, 0.7),), seed=31), x=-3.2, z=-1.55)
    for i, x in enumerate((-6.3, 1.6, 6.2)):
        setzen("skulptur_%d" % i, sockel_mit(skulptur(i), 0.45, 0.8), x=x, z=-1.45)
    setzen("bank_l", bank(1.6), x=-2.5, z=-0.35, dreh=180)
    setzen("bank_r", bank(1.6), x=9.8, z=-0.4, dreh=180)
    setzen("bank_m", bank(1.4, polster="k6e_samt_gruen"), x=-10.3, z=-0.4, dreh=180)
    for i, x in enumerate((-11.0, -4.0, 4.0, 11.0)):
        setzen("kasten_%d" % i, pflanzkasten(1.8, 0.34, random.Random(40 + i), (0.13, 0.16)), x=x * 0.98, z=1.64)
    setzen("olive_l", olivenbaum(0.85), x=-11.9, z=-1.4)
    setzen("olive_r", olivenbaum(0.85), x=11.9, z=-1.5)
    setzen("teppich_gang", teppich(15.0, 0.9, "k6e_samt_blau", "k6e_teppich_rand"), x=0.0, z=0.9)


def einrichtung_tresor():
    setzen("tresortuer", tresortuer(0.95), x=0.0, z=-2.65)
    setzen("uhrenwand", uhrenwand(2.2, 1.9), x=-3.72, z=-0.5, dreh=90)
    setzen("vitrine_a", vitrine(1.2, 0.6, seed=1), x=-2.0, z=-1.4)
    setzen("vitrine_b", vitrine(1.2, 0.6, seed=2, art="uhren"), x=2.2, z=-1.4)
    setzen("vitrine_c", vitrine(1.2, 0.6, seed=3), x=2.4, z=1.3, dreh=-90)
    setzen("vitrine_d", vitrine(1.2, 0.6, seed=4, art="uhren"), x=-2.2, z=1.6)
    setzen("diamant", diamant_podest(), x=0.0, z=-1.05)
    setzen("laeufer", teppich(1.0, 3.6, "k6e_rot", "k6e_teppich_rand"), x=0.25, z=1.0)
    setzen("pflanze_a", topfpflanze(1.1), x=3.55, z=-2.55)
    setzen("pflanze_b", topfpflanze(1.1), x=-3.55, z=-2.55)
    setzen("pflanze_c", topfpflanze(1.0, "busch"), x=3.55, z=2.55)


def einrichtung_boardroom():
    setzen("teppich", teppich(2.6, 4.6, "k6e_teppich", "k6e_teppich_rand"), x=-2.7, z=-0.2)
    setzen("tisch", konferenztisch(3.6, 1.1), x=-2.7, z=-0.2)
    for i, zz in enumerate((-1.3, -0.2, 0.9)):
        setzen("sessel_l%d" % i, chefsessel(), x=-3.75, z=zz, dreh=90)
        setzen("sessel_r%d" % i, chefsessel(), x=-1.65, z=zz, dreh=-90)
    setzen("sessel_kopf", chefsessel(), x=-2.7, z=-2.35)
    tisch_deko = []
    for zz in (-1.3, -0.2, 0.9):
        tisch_deko.append(box("mappe", (0.24, 0.02, 0.32), (-0.3, 0.775, zz), "k6e_leder"))
        tisch_deko.append(box("mappe", (0.24, 0.02, 0.32), (0.3, 0.775, zz), "k6e_leder"))
    tisch_deko.append(zyl("karaffe", 0.06, 0.24, (0.0, 0.765, 0.35), "k6e_glas", seiten=8, r_oben=0.03))
    setzen("tisch_deko", tisch_deko, x=-2.7, z=-0.2)
    setzen("bildschirmwand", bildschirmwand(2.2, 1.2), x=0.8, z=-2.55)
    setzen("tickerwand", tickerwand(2.8, 0.9, 1.15), x=-2.7, z=-2.78)
    setzen("sessel_a", sessel("k6e_samt_blau", 0.76, 0.76), x=3.7, z=0.0, dreh=-90)
    setzen("sessel_b", sessel("k6e_samt_blau", 0.76, 0.76), x=3.7, z=1.55, dreh=-90)
    setzen("beistell", beistell(), x=3.8, z=0.78)
    setzen("olive", olivenbaum(0.85), x=3.8, z=-2.3)
    setzen("pflanze_vorn", topfpflanze(1.0), x=-4.0, z=2.5)


def einrichtung_immobilien():
    setzen("teppich", teppich(3.6, 2.4, "k6e_teppich", "k6e_teppich_rand"), x=0.0, z=-1.2)
    setzen("stadtmodell", stadtmodell(3.0, 1.7), x=0.0, z=-1.3)
    for i, (x, zz, h) in enumerate(((-3.2, -2.3, 1.0), (-2.35, -2.45, 0.75), (3.2, -2.3, 1.2), (2.3, -2.45, 0.8))):
        setzen("hochhaus_%d" % i, hochhausmodell(h, i), x=x, z=zz)
    setzen("plantisch", plantisch(1.4, 0.8), x=2.9, z=0.7, dreh=-90)
    setzen("plantafel", plantafel(1.2, 0.9), x=-3.35, z=0.5, dreh=90)
    setzen("olive", olivenbaum(0.8), x=3.4, z=2.3)
    setzen("pflanze", topfpflanze(1.1), x=-3.5, z=2.4)


def einrichtung_kunstsalon():
    setzen("oldtimer", oldtimer(), x=0.25, z=1.6)
    setzen("stellwand_links", stellwand(2.4, 1.8, ((-0.55, 1.05, 0.9, 1.0), (0.6, 1.1, 0.8, 0.6)), seed=51), x=-3.6, z=-1.6, dreh=90)
    setzen("stellwand_hinten", stellwand(2.0, 1.6, ((0.0, 1.0, 1.4, 0.8),), seed=61), x=2.5, z=-3.0)
    setzen("staffelei_a", staffelei_bild(0.9, 0.7, 71), x=-2.6, z=1.2, dreh=60)
    setzen("staffelei_b", staffelei_bild(0.7, 0.9, 81), x=-2.7, z=2.8, dreh=80)
    setzen("skulptur_a", sockel_mit(goldkugel(), 0.55, 0.8), x=2.6, z=-1.7)
    setzen("skulptur_b", sockel_mit(skulptur(2), 0.45, 0.7), x=-2.3, z=-2.8)
    setzen("bank", bank(1.6, polster="k6e_samt_rosa"), x=3.1, z=1.6, dreh=-90)
    setzen("pflanze", topfpflanze(1.1), x=-3.5, z=3.0)
    setzen("pflanze_b", topfpflanze(1.0, "busch"), x=3.5, z=3.0)


def einrichtung_dachterrasse():
    setzen("pool", pool(3.0, 2.2), x=2.0, z=1.6)
    setzen("liege_a", liege(), x=-2.95, z=1.75)
    setzen("liege_b", liege(), x=-1.95, z=1.75)
    setzen("schirm", sonnenschirm(1.0), x=-2.45, z=0.05)
    setzen("bar", aussenbar(2.2), x=2.4, z=-2.6)
    setzen("lichterkette", lichterkette([(-3.7, -3.2), (-3.7, 3.2), (3.7, 3.2)]), x=0.0, z=0.0)
    setzen("kasten_rechts", pflanzkasten(1.6, 0.45), x=3.6, z=-0.8, dreh=90)
    setzen("olive", olivenbaum(0.8), x=-3.3, z=-2.6)
    setzen("olive_b", olivenbaum(0.7), x=0.9, z=3.0)
    setzen("teleskop", teleskop(), x=3.3, z=3.0, dreh=0)


# ==============================================================================
# AUSSEN (Weltkoordinaten, Ursprung 0,0)
# ==============================================================================
# Gebaeude: Waende x -12,5..12,5, z -9,5..7,5. Die Dachplatte steht 1 m ueber.
# Darunter der Turm, ringsum die Stadt deutlich TIEFER -- das Penthouse
# schwebt oben. Vorn und rechts liegt nichts ueber der Dachplatte.

FUND = (-13.5, 13.5, -10.5, 8.5)
PLATTE_Y = -0.03


def platte(name, x0, x1, z0, z1, y_oben, y_unten, mat, r=0.0):
    return box(name, (x1 - x0, y_oben - y_unten, z1 - z0), ((x0 + x1) / 2, (y_oben + y_unten) / 2, (z0 + z1) / 2), mat, r=r)


def fundament():
    return [platte("dachplatte", FUND[0], FUND[1], FUND[2], FUND[3], PLATTE_Y, -0.55, "k6e_platte", r=0.04),
            platte("dachkante", FUND[0] - 0.05, FUND[1] + 0.05, FUND[2] - 0.05, FUND[3] + 0.05, -0.42, -0.5, "k6e_messing")]


def hochhaus(x0, x1, z0, z1, oben, unten, farbe, rng, hoehe_fenster=8.0):
    """Dammerungs-Haus: Fensterbaender je Geschoss, ein Teil davon erleuchtet."""
    teile = [platte("haus", x0, x1, z0, z1, oben, unten, farbe)]
    y = oben - 1.4
    while y > max(unten, oben - hoehe_fenster):
        for (achse, a0, a1, fest) in (("x", z0, z1, x1 + 0.01), ("z", x0, x1, z1 + 0.01)):
            laenge = (a1 - a0) - 0.8
            drittel = laenge / 2.0
            for k in range(2):
                mat = "k6e_fenster_an" if rng.random() < 0.45 else "k6e_fenster"
                mitte = a0 + 0.4 + drittel * (k + 0.5)
                if achse == "x":
                    teile.append(box("fenster_x", (0.02, 0.9, drittel - 0.12), (fest, y, mitte), mat))
                else:
                    teile.append(box("fenster_z", (drittel - 0.12, 0.9, 0.02), (mitte, y, fest), mat))
        y -= 3.2
    # Dach: warm angestrahlte Kappe, darauf je nach Los Technik, Pool, Antenne oder Dachgarten
    dach = ("k6e_dach_a", "k6e_dach_b", "k6e_dach_c")[int(abs(x0 * 7 + z0 * 3)) % 3]
    teile.append(platte("dachkappe", x0 - 0.12, x1 + 0.12, z0 - 0.12, z1 + 0.12, oben + 0.2, oben, dach))
    k = rng.random()
    mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
    if k < 0.25:      # Technik
        teile.append(box("technik", (min(2.0, x1 - x0 - 1), 0.9, min(1.6, z1 - z0 - 1)), (mx, oben + 0.65, mz), "k6e_dach"))
    elif k < 0.5:     # Dachpool, leuchtend
        teile.append(platte("dachpool", x0 + 0.7, x1 - 0.7, z0 + 0.9, z1 - 0.9, oben + 0.26, oben + 0.2, "k6e_dachpool"))
    elif k < 0.7:     # Antenne mit Warnlicht
        teile.append(stab("antenne", (mx, oben + 0.2, mz), (mx, oben + 3.4, mz), 0.08, "k6e_dach"))
        teile.append(box("warnlicht", (0.2, 0.2, 0.2), (mx, oben + 3.5, mz), "k6e_warnlicht"))
    elif k < 0.85:    # Dachgarten
        teile.append(platte("dachgarten", x0 + 0.5, x1 - 0.5, z0 + 0.5, z1 - 0.5, oben + 0.3, oben + 0.2, "k6e_dachgruen"))
        teile.append(box("leuchtschild", (1.6, 0.5, 0.06), (mx, oben + 1.0, z1 - 0.7), "k6e_strassenlicht"))
    return teile


def kran(h=46.0, ausleger=14.0):
    """Turmdrehkran, zeigt mit dem Ausleger nach +x; Ursprung = Fuss."""
    teile = [box("mast", (0.8, h, 0.8), (0, h / 2, 0), "k6e_kran"),
             box("ausleger", (ausleger + 5.0, 0.6, 0.6), (ausleger / 2 - 2.5, h + 0.3, 0), "k6e_kran"),
             box("gegen", (3.5, 1.4, 1.0), (-4.8, h + 0.2, 0), "k6e_dach"),
             box("kabine", (1.0, 1.0, 1.0), (0.9, h - 0.6, 0.9), "k6e_kran"),
             stab("spitze", (0, h + 0.6, 0), (0, h + 4.0, 0), 0.12, "k6e_kran"),
             stab("seil", (0, h + 4.0, 0), (ausleger - 3.0, h + 0.6, 0), 0.06, "k6e_dach"),
             box("haken", (0.3, 0.8, 0.3), (ausleger - 3.0, h - 3.5, 0), "k6e_kran"),
             stab("hubseil", (ausleger - 3.0, h + 0.3, 0), (ausleger - 3.0, h - 3.1, 0), 0.05, "k6e_dach"),
             box("warnlicht", (0.3, 0.3, 0.3), (0, h + 4.2, 0), "k6e_warnlicht")]
    return teile


def heliport():
    """Hochhaus mit Landeplatz und Lichterring; Ursprung Mitte Dach (y = Dachhoehe)."""
    teile = [zyl("pad", 3.4, 0.25, (0, 0, 0), "k6e_pad", seiten=16),
             zyl("pad_ring", 3.0, 0.02, (0, 0.25, 0), "k6e_pad_rand", seiten=16)]
    teile += [box("h_links", (0.35, 0.03, 2.2), (-0.7, 0.28, 0), "k6e_pad_rand"),
              box("h_rechts", (0.35, 0.03, 2.2), (0.7, 0.28, 0), "k6e_pad_rand"),
              box("h_mitte", (1.4, 0.03, 0.35), (0, 0.28, 0), "k6e_pad_rand")]
    for i in range(12):
        w = i * math.pi / 6
        teile.append(box("pad_licht", (0.18, 0.18, 0.18), (math.cos(w) * 3.45, 0.2, math.sin(w) * 3.45), "k6e_warnlicht"))
    return teile


def wolkenbank(rng, x0, x1, z0, z1, y, anzahl=9):
    teile = []
    for i in range(anzahl):
        r = rng.uniform(2.4, 4.4)
        teile.append(kugel("wolke", r, (rng.uniform(x0, x1), y + rng.uniform(-0.8, 0.8), rng.uniform(z0, z1)),
                           "k6e_wolke", stauchung=0.32, ringe=4, seiten=8))
    return teile


def umgebung():
    rng = random.Random(606)
    teile = []
    # der eigene Turm unter dem Penthouse
    teile.append(platte("turm", -12.9, 12.9, -9.9, 7.9, -0.55, -40.0, "k6e_turm"))
    y = -2.2
    while y > -40:
        teile.append(box("turm_band_x", (0.03, 1.4, 17.2), (12.915, y, -1.0), "k6e_fenster"))
        teile.append(box("turm_band_z", (25.2, 1.4, 0.03), (0.0, y, 7.915), "k6e_fenster"))
        y -= 3.3
    teile.append(box("turm_licht", (25.2, 0.12, 0.04), (0.0, -1.0, 7.93), "k6e_fenster_an"))
    teile.append(box("turm_licht", (0.04, 0.12, 17.2), (12.93, -1.0, -1.0), "k6e_fenster_an"))
    farben = ["k6e_haus_a", "k6e_haus_b", "k6e_haus_c", "k6e_haus_d", "k6e_haus_e"]
    for gx in range(-3, 4):
        for gz in range(-3, 4):
            cx, cz = gx * 16.0, gz * 16.0 - 1.0
            if abs(cx) < 20 and abs(cz) < 17:
                continue
            if (gx, gz) == (-2, -1):     # hier steht der Heliport-Turm
                continue
            if cx >= 0 and cz >= -17:    # vorn/rechts uebernimmt die Nahstadt
                continue
            hinten = cx < 0 or cz < 0
            for k in range(1 if max(abs(gx), abs(gz)) == 3 else 2):
                bx = cx + (-3.5 if k == 0 else 3.5) + rng.uniform(-0.8, 0.8)
                bz = cz + rng.uniform(-2.0, 2.0)
                b = rng.uniform(4.0, 6.0)
                t = rng.uniform(4.5, 8.0)
                oben = rng.uniform(-14.0, -6.0) if hinten else rng.uniform(-24.0, -12.0)
                # Skyline: weit hinten ragen einzelne Tuerme ueber das Penthouse hinaus
                if hinten and cx <= 0 and cz <= 0 and (gx <= -2 or gz <= -2) and rng.random() < 0.45:
                    oben = rng.uniform(1.0, 14.0)
                teile += hochhaus(bx - b / 2, bx + b / 2, bz - t / 2, bz + t / 2, oben, -40.0,
                                  farben[(gx * 3 + gz + k) % 5], rng, 6.5 if oben < 0 else 10.0)
    # Nahstadt: Haeuserschluchten direkt vor und rechts vom Turm, alle unter der Dachplatte
    ring = []
    for reihe, (z0, tief) in enumerate(((10.5, 0), (18.0, 1), (25.5, 2))):
        for i in range(-2, 5):
            ring.append((i * 7.0 + rng.uniform(-1.0, 1.0), z0 + rng.uniform(-0.5, 0.5), tief))
    for spalte, (x0, tief) in enumerate(((16.0, 0), (23.5, 1), (31.0, 2))):
        for j in range(-3, 2):
            ring.append((x0 + rng.uniform(-0.5, 0.5), j * 7.0 + 1.5 + rng.uniform(-1.0, 1.0), tief))
    for (bx, bz, tief) in ring:
        b = rng.uniform(4.0, 5.4)
        t = rng.uniform(4.0, 5.4)
        oben = rng.uniform(-4.0, -9.0) - tief * 4.5 + rng.uniform(-2.0, 2.0)
        oben = min(oben, -4.6)
        teile += hochhaus(bx - b / 2, bx + b / 2, bz - t / 2, bz + t / 2, oben, -40.0,
                          farben[(int(bx * 3 + bz) + tief) % 5], rng, 8.5)
    # Heliport-Turm (hinten links)
    teile.append(platte("heliturm", -32.0, -24.0, -20.0, -12.0, -3.0, -40.0, "k6e_haus_b"))
    teile += bei(heliport(), x=-28.0, y=-3.0, z=-16.0)
    # Stadtboden: dunkle Daemmerung, Strassen mit warmem Licht, ein Fluss
    teile.append(platte("stadtboden", -80, 80, -80, 80, -40.0, -40.5, "k6e_stadtboden"))
    for i in range(-5, 5):
        teile.append(platte("strasse_x", -80, 80, i * 16.0 + 7.0 - 1.5, i * 16.0 + 7.0 + 1.5, -39.95, -40.0, "k6e_strasse"))
        teile.append(platte("strasse_z", i * 16.0 + 8.0 - 1.5, i * 16.0 + 8.0 + 1.5, -80, 80, -39.94, -40.0, "k6e_strasse"))
        teile.append(platte("licht_x", -80, 80, i * 16.0 + 7.0 - 0.15, i * 16.0 + 7.0 + 0.15, -39.9, -39.95, "k6e_strassenlicht"))
        teile.append(platte("licht_z", i * 16.0 + 8.0 - 0.15, i * 16.0 + 8.0 + 0.15, -80, 80, -39.89, -39.94, "k6e_strassenlicht"))
    teile.append(platte("fluss", 40.0, 52.0, -80, 80, -39.8, -40.0, "k6e_fluss"))
    return teile


def landmark_kran():
    return bei(kran(), x=-34.0, y=-40.0, z=-34.0)


def landmark_wolken():
    rng = random.Random(77)
    return (wolkenbank(rng, 14.0, 30.0, 4.0, 16.0, -10.5, 5) + wolkenbank(rng, 0.0, 22.0, 11.0, 22.0, -13.0, 5))


LANDMARKS = {"welt_kran": landmark_kran, "welt_wolken": landmark_wolken}


# ==============================================================================
# TABELLE, HUELLE, ABLAUF
# ==============================================================================

def _hinten(x, z_wand):
    return (x, z_wand + 0.5, 1.2, 1.0, "Tuer hinten x=%g" % x)


def _vorn(x, z_wand):
    return (x, z_wand - 0.5, 1.2, 1.0, "Tuer vorn x=%g" % x)


ZONEN = {
    "lounge": {
        "breite": 9.0, "tiefe": 7.0, "welt": (0.0, 4.0), "boden": "parkett", "bau": einrichtung_lounge,
        "frei": [(-2.4, -2.35, 2.2, 2.2, "Station intake"), (2.2, -2.35, 2.2, 2.2, "Station processing"),
                 (0.0, 0.7, 2.2, 2.2, "Station buffer"), _hinten(0.0, -3.5),
                 (-0.05, -2.3, 0.9, 2.4, "Laufweg zur Figur")],
        "ortho": 11.0,
    },
    "galerie": {
        "breite": 25.0, "tiefe": 4.0, "welt": (0.0, -1.5), "boden": "marmor", "bau": einrichtung_galerie,
        "frei": [(4.0, -0.8, 2.2, 2.2, "Station transport"), (0.0, 0.9, 17.0, 1.0, "Laufgang z -0,6"),
                 _hinten(-8.0, -2.0), _hinten(0.0, -2.0), _hinten(8.0, -2.0),
                 _vorn(-8.0, 2.0), _vorn(0.0, 2.0), _vorn(8.0, 2.0),
                 (12.0, -0.5, 1.0, 1.2, "Tuer rechts z=-2"), (-5.5, -0.1, 1.0, 1.0, "Wartepunkt")],
        "ortho": 18.0,
    },
    "tresor": {
        "breite": 8.0, "tiefe": 6.0, "welt": (-8.5, -6.5), "boden": "marmor", "bau": einrichtung_tresor,
        "frei": [_vorn(0.5, 3.0), (0.25, 1.25, 1.0, 2.0, "Laufweg"), (0.0, 0.5, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
    "boardroom": {
        "breite": 9.0, "tiefe": 6.0, "welt": (0.0, -6.5), "boden": "parkett", "bau": einrichtung_boardroom,
        "frei": [(0.8, -0.1, 2.2, 2.2, "Station special"), (-0.1, 0.4, 0.6, 0.6, "Figur special"),
                 _vorn(0.0, 3.0), (0.0, 1.6, 1.0, 1.4, "Laufweg")],
        "ortho": 10.0,
    },
    "immobilien": {
        "breite": 8.0, "tiefe": 6.0, "welt": (8.5, -6.5), "boden": "parkett", "bau": einrichtung_immobilien,
        "frei": [_vorn(-0.5, 3.0), (-0.25, 1.4, 1.0, 2.4, "Laufweg"), (0.0, 0.3, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
    "kunstsalon": {
        "breite": 8.0, "tiefe": 7.0, "welt": (-8.5, 4.0), "boden": "marmor", "bau": einrichtung_kunstsalon,
        "frei": [_hinten(0.5, -3.5), (0.25, -2.0, 1.0, 3.0, "Laufweg"), (0.0, -0.5, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
    "dachterrasse": {
        "breite": 8.0, "tiefe": 7.0, "welt": (8.5, 4.0), "boden": "deck", "bau": einrichtung_dachterrasse,
        "frei": [_hinten(-0.5, -3.5), (-0.5, -2.1, 1.0, 1.4, "Laufweg Tuer"),
                 (-0.25, -0.9, 1.0, 2.4, "Laufweg"), (0.0, 0.2, 1.0, 1.0, "Wartepunkt")],
        "ortho": 10.0,
    },
}


def _waende_aus_json():
    import json
    pfad_json = os.path.join(WURZEL, "project", "data", "worlds", "worlds.json")
    with open(pfad_json, encoding="utf-8") as datei:
        daten = json.load(datei)
    for w in daten["welten"]:
        if w.get("id") == "kapital":
            return w["waende"]
    return []


SATZ = {
    "voll": ["wand_voll", "wand_halb_tuer", "wand_voll_fenster", "pfosten_voll"],
    "halb": ["wand_halb", "wand_halb_tuer", "wand_halb", "pfosten_halb"],
    "sockel": ["wand_sockel", "wand_sockel_tuer", "wand_sockel", "pfosten_sockel"],
    "gelaender": ["gelaender", "gelaender", "gelaender", ""],
}
RANG = {"pfosten_voll": 3, "pfosten_halb": 2, "pfosten_sockel": 1, "": 0}


def huelle():
    liste = []
    pfosten = {}
    for w in _waende_aus_json():
        satz = SATZ[w["typ"]]
        achse_x = w["achse"] == "x"
        grad = w.get("drehung", 0.0 if achse_x else 90.0)
        feld = w["von"] + 0.5
        while feld < w["bis"]:
            modul = satz[0]
            if any(abs(t - feld) < 0.01 for t in w["tueren"]):
                modul = satz[1]
            elif any(abs(fe - feld) < 0.01 for fe in w["fenster"]):
                modul = satz[2]
            x, zz = (feld, w["fest"]) if achse_x else (w["fest"], feld)
            liste.append((modul, x, zz, grad))
            feld += 1.0
        for ende in (w["von"], w["bis"]):
            p = (ende, w["fest"]) if achse_x else (w["fest"], ende)
            if RANG[satz[3]] > RANG.get(pfosten.get(p, ""), 0):
                pfosten[p] = satz[3]
    for (x, zz), modul in pfosten.items():
        liste.append((modul, x, zz, 0.0))
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        for i in range(int(zone["breite"])):
            for k in range(int(zone["tiefe"])):
                ix = int(round(wx - zone["breite"] / 2 + 0.5 + i))
                iz = int(round(wz - zone["tiefe"] / 2 + 0.5 + k))
                ab = "a" if (ix + iz) % 2 == 0 else "b"
                liste.append(("boden_%s_%s" % (zone["boden"], ab), ix, iz, 0.0))
    return liste


def pfad(name):
    return os.path.join(AUSGABE, name + ".glb")


def _neu():
    alles_loeschen()
    del wa.MOEBEL[:]
    leucht_materialien()


ERGEBNIS = {}


def _abschluss(obj, name, budget, fehler=0):
    n = dreiecke(obj)
    (x0, x1), (y0, y1), (z0, z1) = masse(obj)
    ziel = pfad(name)
    exportieren(obj, ziel)
    print("  -> %s: %d Dreiecke (Budget %d)%s, %d Materialien, %.0f KB"
          % (name, n, budget, "  <-- UEBER BUDGET" if n > budget else "", len(obj.data.materials),
             os.path.getsize(ziel) / 1024.0))
    print("     BBox x %+.2f..%+.2f  y %.2f..%.2f  z %+.2f..%+.2f" % (x0, x1, y0, y1, z0, z1))
    print("     Freiflaechen-/Wandpruefung: %s" % ("OK" if fehler == 0 else "%d VERLETZUNGEN" % fehler))
    ERGEBNIS[name] = n
    return fehler


def zone_bauen(name):
    _neu()
    zone = ZONEN[name]
    zone["bau"]()
    print("")
    print("=== EINRICHTUNG %s (%g x %g) ===" % (name.upper(), zone["breite"], zone["tiefe"]))
    moebel_bericht()
    fehler = freiflaechen_pruefen(zone)
    obj = verbinden([t for _, teile in wa.MOEBEL for t in teile], "einrichtung_%s" % name)
    return _abschluss(obj, "einrichtung_" + name, ZONEN_BUDGET, fehler)


def aussen_bauen():
    _neu()
    obj = verbinden(umgebung(), "umgebung")
    print("")
    print("=== UMGEBUNG ===")
    _abschluss(obj, "umgebung", UMGEBUNG_BUDGET)
    hoch = [v.co for v in obj.data.vertices
            if (-v.co.y > FUND[3] + 0.05 or v.co.x > FUND[1] + 0.05) and v.co.z > PLATTE_Y]
    print("     Hoehenregel vorn/rechts: %s" % ("OK" if not hoch else "%d Punkte zu hoch" % len(hoch)))
    for lname, lbau in LANDMARKS.items():
        _neu()
        obj = verbinden(lbau(), lname)
        print("=== %s ===" % lname.upper())
        _abschluss(obj, lname, 3000)
    _neu()
    obj = verbinden(fundament(), "fundament")
    print("=== FUNDAMENT ===")
    _abschluss(obj, "fundament", 500)


_VORLAGEN = {}


def instanz(datei, x=0.0, z=0.0, dreh=0.0, y=0.0):
    vorlage = _VORLAGEN.get(datei)
    m = Matrix.Translation(G(x, y, z)) @ Matrix.Rotation(math.radians(dreh), 4, "Z")
    if vorlage is None:
        vorher = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=datei)
        neu = [o for o in bpy.data.objects if o not in vorher and o.type == "MESH"]
        vorlage = [(o, o.matrix_world.copy()) for o in neu]
        _VORLAGEN[datei] = vorlage
        for o, basis in vorlage:
            o.matrix_world = m @ basis
        return
    for o, basis in vorlage:
        k = o.copy()
        bpy.context.scene.collection.objects.link(k)
        k.matrix_world = m @ basis


STATIONEN_WELT = {"intake": (-2.4, 1.65), "buffer": (0.0, 4.7), "processing": (2.2, 1.65),
                  "transport": (4.0, -2.3), "special": (0.8, -6.6)}


def karte_aufstellen(mit_umgebung=True, mit_stationen=True):
    alles_loeschen()
    _VORLAGEN.clear()
    for modul, x, zz, dreh in huelle():
        instanz(raum.modul_pfad(modul), x=x, z=zz, dreh=dreh)
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        instanz(pfad("einrichtung_" + name), x=wx, z=wz)
    instanz(pfad("fundament"))
    if mit_umgebung:
        instanz(pfad("umgebung"))
    if mit_stationen:
        ordner = os.path.join(WURZEL, "project", "assets", "stations", "kapital")
        for st, (x, zz) in STATIONEN_WELT.items():
            datei = os.path.join(ordner, "station_%s_3.glb" % st)
            if os.path.exists(datei):
                instanz(datei, x=x, z=zz)


def vorschau(nur_karte=False):
    karte_aufstellen()
    raum.rendern(os.path.join(VORSCHAU, "gesamt_kapital.png"), (0.0, 0.0, -1.0), 44.0, aufloesung=1600)
    raum.rendern(os.path.join(VORSCHAU, "karte_kapital.png"), (0.0, 0.5, -1.0), 27.0, aufloesung=1600)
    if nur_karte:
        return
    for name, zone in ZONEN.items():
        wx, wz = zone["welt"]
        raum.rendern(os.path.join(VORSCHAU, "zone_%s.png" % name), (wx, 0.6, wz), zone["ortho"], aufloesung=900)


def main():
    argumente = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    gewaehlt = [a for a in argumente if a in ZONEN]
    nur_aussen = "aussen" in argumente and not gewaehlt
    fehler = 0
    if "--nur-vorschau" not in argumente:
        if not nur_aussen:
            for name in (gewaehlt or list(ZONEN)):
                fehler += zone_bauen(name)
        if not gewaehlt or "aussen" in argumente:
            aussen_bauen()
    if "--ohne-vorschau" not in argumente:
        vorschau(nur_karte="--nur-karte" in argumente)
    print("")
    for k, v in ERGEBNIS.items():
        print("  %-30s %6d Dreiecke" % (k, v))
    print("=== FERTIG: %s ===" % ("alle Freiflaechen frei" if fehler == 0 else "%d Verletzungen" % fehler))


if __name__ == "__main__":
    main()
