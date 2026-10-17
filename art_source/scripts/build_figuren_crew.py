"""Erzeugt die gemeinsamen Chibi-Figuren fuer alle Welten als GLB.

Aufruf (aus dem Projektordner):
    blender --background --python art_source/scripts/build_figuren_crew.py
    blender --background --python art_source/scripts/build_figuren_crew.py -- --ohne-vorschau

Ausgabe: project/assets/characters/gemeinsam/
    figur_kapuze, figur_kapuze_sitzend   (identisch mit der WG-Vorlage)
    figur_cap        Cap rueckwaerts, Bartschatten, gruene Jacke
    figur_buckethat  Fischerhut, schwarzes Shirt, Kamera am Riemen, kurzer Bart
    figur_brille     blonder Undercut, runde Brille, Latzhose mit Farbklecksen
    figur_zopf       hoher Zopf, Weste, Werkzeugguertel, Headset
    figur_packer     Warnweste, kurze Strickmuetze, Arbeitshandschuhe
    figur_anzug      Anzug, Krawatte, Aktenkoffer
Zusaetzlich wird figur_cap nach project/assets/characters/zimmer/ kopiert
(gleiches Skelett, gleicher Ursprung wie bisher).

Die Dateien sind nach ihrer SILHOUETTE benannt (Regel D3 / ADR-010).

Grundformen, Skelett, Export und Rueckleseprobe kommen unveraendert aus
build_figuren_wg.py -- dieselben Masse, dieselben Teilnamen
(figur -> koerper -> kopf/arm_l/arm_r/bein_l/bein_r), dieselben Drehpunkte.
Godot animiert damit alle Figuren gleich.
Farben werden als sRGB-Hex notiert und linear eingetragen (farbe()).
"""

import bpy
import math
import os
import shutil
import sys
from mathutils import Vector

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import build_figuren_wg as wg  # noqa: E402
from build_figuren_wg import (  # noqa: E402
    Bau, drehung, ausrichtung, platz, drehkoerper, kugel, rohr, schneiden,
    verschoben, auf_flaeche, neues_skelett, pose, rumpf, rumpf_punkt,
    hand_punkt, unter_haar,
    KOPF_MITTE, KOPF_R, HAUT, RUMPF_TIEFE,
)

WURZEL = wg.WURZEL
AUSGABE = os.path.join(WURZEL, "project", "assets", "characters", "gemeinsam")
AUSGABE_WG = os.path.join(WURZEL, "project", "assets", "characters", "zimmer")
VORSCHAU = os.path.join(WURZEL, "art_source", "vorschau", "crew")
wg.AUSGABE = AUSGABE
wg.VORSCHAU = VORSCHAU

BUDGET_DREIECKE = wg.BUDGET_DREIECKE

if os.environ.get("CREW_ZAEHLEN"):
    # Hilfe beim Sparen: jede dazu()-Zeile mit ihren Dreiecken ausgeben
    import inspect
    _dazu = Bau.dazu

    def _zaehlend(self, geo, matrix=None):
        stapel = [f for f in inspect.stack()[1:] if f.filename.endswith("crew.py")]
        zeile = stapel[0].lineno if stapel else 0
        print("        Z%d %s %d" % (zeile, self.name, sum(len(f) - 2 for f in geo[1])))
        _dazu(self, geo, matrix)
    Bau.dazu = _zaehlend

MUND = "#8C3B34"


# =============================================================================
# Schlanke Grundteile
# Rumpf, Arme, Beine, Gesicht, Haut und Haar kosten in der Vorlage schon rund
# 1.000 Dreiecke. Fuer Figuren mit Zubehoer werden sie hier etwas sparsamer
# gebaut (gleiche Masse, gleiche Drehpunkte, gleiche Kugelkappen).
# =============================================================================

def arm_crew(bau, schulter, richtung, aermel, aermel_ende=0.20, hand=HAUT, laenge=0.30):
    """Wie wg.arm, aber mit 6 statt 8 Segmenten."""
    k = laenge / 0.30
    profil = [(-0.055, 0.0), (-0.03, 0.046), (0.02, 0.054), (0.19 * k, 0.046),
              (0.205 * k, 0.043), (0.255 * k, 0.052), (0.30 * k, 0.0)]
    fn = lambda t: aermel if t < aermel_ende * k else hand
    bau.dazu(drehkoerper(profil, 6, fn), platz(schulter, ausrichtung(richtung)))


def bein_crew(bau, huefte, hose, schuh, sohle, knoechel=None):
    """Wie wg.bein, aber der Schuh mit 4 statt 5 Ringen."""
    profil = [(-0.07, 0.0), (-0.04, 0.058), (0.0, 0.068), (0.12, 0.058),
              (0.19, 0.050), (0.215, 0.0)]
    fn = lambda t: knoechel if (knoechel and t > 0.155) else hose
    bau.dazu(drehkoerper(profil, 6, fn), platz(huefte, ausrichtung((0, 0, -1))))
    wg.schuh_an(bau, Vector((huefte.x * 1.06, -0.03, 0.0)), schuh, sohle, ringe=4)


def glieder(t, aermel, hose, schuh, sohle, aermel_ende=0.20, hand=HAUT, knoechel=None, arme=True):
    if arme:
        for n, s in (("arm_l", 1.0), ("arm_r", -1.0)):
            arm_crew(t[n][0], t[n][1], (s * 0.17, 0.0, -1.0), aermel, aermel_ende, hand)
    for n in ("bein_l", "bein_r"):
        bein_crew(t[n][0], t[n][1], hose, schuh, sohle, knoechel)


def bart_farbe(bart, stirn_vorn, seite, hinten=0.02):
    """Farbfunktion fuer die Haut: unterhalb der Bartlinie Bartfarbe.
    Oberkante vorn (y = -0,22) auf stirn_vorn, seitlich (y = 0) auf seite."""
    steig = (seite - stirn_vorn) / 0.22

    def fn(x, y, z):
        oy, oz = y * KOPF_R[1], z * KOPF_R[2]
        if oy < hinten and oz < seite + steig * oy:
            return bart
        return HAUT
    return fn


def kopf_haut(bau, verdeckt=(), farbe_fn=HAUT, seg=12, ringe=9):
    geo = verschoben(kugel(KOPF_R, seg, ringe, farbe_fn), platz(KOPF_MITTE))
    if verdeckt:
        geo = schneiden(geo, list(verdeckt))
    bau.dazu(geo)


def haar(bau, farbe_fn, ebenen, dicke=(0.012, 0.015, 0.013), versatz=(0, 0.012, 0.012), seg=12, ringe=9):
    """Haarschale wie in der Vorlage, aber mit frei waehlbaren Schnittebenen."""
    radien = tuple(r + d for r, d in zip(KOPF_R, dicke))
    geo = verschoben(kugel(radien, seg, ringe, farbe_fn), platz(KOPF_MITTE + Vector(versatz)))
    bau.dazu(schneiden(geo, list(ebenen)))


def brauen(bau, farbe, hoch=0.0, dicke=0.0105, radien=KOPF_R):
    """hoch = Anhebung beider Brauen oder (links, rechts). AUSDRUCK hebt zusaetzlich."""
    extra = {"jubel": 0.05, "schock": 0.10}.get(wg.AUSDRUCK, 0.0)
    for s in (1.0, -1.0):
        h = hoch[0 if s > 0 else 1] if isinstance(hoch, (tuple, list)) else hoch
        h += extra
        linie = [auf_flaeche(KOPF_MITTE, radien, (s * sx, -1.0, sz + h * k), einsinken=-0.002)[0]
                 for sx, sz, k in ((0.23, 0.185, 0.5), (0.36, 0.230, 1.0), (0.49, 0.19, 0.8))]
        bau.dazu(rohr(linie, dicke, 3, farbe, kappen=False))


def mund(bau, radien=KOPF_R, breite=0.13, hoehe=-0.37, laecheln=0.07, farbe=MUND):
    """Kleiner Laechelbogen (neutral), offenes Lachen (jubel) oder 'O' (schock)."""
    wg.mund_ausdruck(bau, KOPF_MITTE, radien, breite, hoehe, laecheln, farbe)


def gesicht_crew(bau, braue, laecheln=0.07, braue_hoch=0.0, mund_hoehe=-0.37, mund_breite=0.13,
                 braue_dicke=0.0105, iris=wg.AUGE, blick=(0.0, 0.0), lid=0.0):
    """Grosse Augen (Weiss, Pupille, Glanz), Wangen, Brauen, Mund."""
    c, oben = KOPF_MITTE, Vector((0, 0, 1))
    wg.augen(bau, c, KOPF_R, iris=iris, blick=blick, lid=lid)
    for s in (1.0, -1.0):
        p, n = auf_flaeche(c, KOPF_R, (s * 0.64, -1.0, -0.40), einsinken=0.005)
        bau.dazu(kugel((0.040, 0.024, 0.008), 6, 2, wg.WANGE), platz(p, ausrichtung(n, oben)))
    brauen(bau, braue, hoch=braue_hoch, dicke=braue_dicke)
    mund(bau, breite=mund_breite, hoehe=mund_hoehe, laecheln=laecheln)


def flach(bau, groesse, ort, hexwert, e=0.55, matrix3=None, seg=6, ringe=3):
    """Flaches, abgerundetes Polster (Tasche, Patch, Klecks).
    groesse = (breite, hoehe, dicke) in der Flaeche."""
    bau.dazu(kugel(groesse, seg, ringe, hexwert, e_hoch=e, e_rund=e), platz(ort, matrix3))


def auf_rumpf(x, z, abstand=0.0, hinten=False):
    """Punkt auf dem Rumpf plus Ausrichtung (lokal +Z nach aussen, +Y nach oben)."""
    p = rumpf_punkt(x, z, hinten=hinten, abstand=abstand)
    r = max(wg.rumpf_radius(z), 1e-3)
    n = Vector((x / r, (1 if hinten else -1) / RUMPF_TIEFE * math.sqrt(max(1 - (x / r) ** 2, 0.0)), 0.0))
    return p, ausrichtung(n, (0, 0, 1))


def linie_auf_rumpf(bau, x, zs, dicke, hexwert, hinten=False, abstand=0.004):
    bau.dazu(rohr([rumpf_punkt(x, z, hinten=hinten, abstand=abstand) for z in zs], dicke, 3, hexwert,
                  kappen=False))


def ring_um_rumpf(bau, z0, z1, extra, hexwert):
    """Band um den Rumpf (Guertel, Reflexstreifen). 10 Segmente wie der Rumpf,
    damit die Ecken genau uebereinander liegen."""
    r0 = wg.rumpf_radius(z0) + extra * 0.4
    r1 = wg.rumpf_radius(z1) + extra * 0.4
    zm = 0.5 * (z0 + z1)
    rm = wg.rumpf_radius(zm) + extra
    bau.dazu(drehkoerper([(z0, r0), (zm, rm), (z1, r1)], 10, hexwert, sy=RUMPF_TIEFE))


# =============================================================================
# Figur: Cap rueckwaerts
# =============================================================================

JACKE_GRUEN = "#3D7BFF"          # Mo: Absenderfarbe (theme.json absender_farben)
JACKE_GRUEN_DUNKEL = "#2C62DB"
SHIRT_WEISS = "#F4F2EE"
CAP_BLAU = "#FFC93C"
CAP_BLAU_DUNKEL = "#1B1726"
KETTE_GOLD = "#FFC93C"
HAAR_SCHWARZBRAUN = "#3A2A22"
BRAUE_DUNKEL = "#2E211B"
BARTSCHATTEN = "#D2AA8E"
JEANS_DUNKEL = "#3F5A86"
SNEAKER = "#F4F4F1"
SOHLE = "#C3C8CF"


def figur_cap():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, JACKE_GRUEN, JEANS_DUNKEL, grenze=0.285, bund=JACKE_GRUEN_DUNKEL)
    # Offene Jacke: weisses Shirt als Streifen vorn, dunkle Kanten daneben
    p, m = auf_rumpf(0.0, 0.46, abstand=-0.004)
    flach(k, (0.058, 0.13, 0.014), p, SHIRT_WEISS, matrix3=m)
    for s in (1.0, -1.0):
        linie_auf_rumpf(k, s * 0.058, (0.33, 0.46, 0.59), 0.011, JACKE_GRUEN_DUNKEL)
        p, m = auf_rumpf(s * 0.115, 0.36, abstand=-0.003)
        flach(k, (0.04, 0.03, 0.010), p, JACKE_GRUEN_DUNKEL, matrix3=m, ringe=2)
    kragen = [Vector((0.115 * math.cos(w), 0.092 * math.sin(w), 0.612 - 0.012 * math.sin(w)))
              for w in (2 * math.pi * i / 8 for i in range(8))]
    k.dazu(rohr(kragen, 0.02, 3, JACKE_GRUEN_DUNKEL, geschlossen=True))

    # Goldkette mit Anhaenger: Erkennungszeichen neben der Kappe
    kette = []
    for i in range(10):
        w = 2 * math.pi * i / 10
        vorn = max(0.0, -math.sin(w))
        x = 0.128 * math.cos(w)
        kette.append(rumpf_punkt(x, 0.605 - 0.125 * vorn * vorn, hinten=math.sin(w) > 0.05, abstand=0.016))
    k.dazu(rohr(kette, 0.017, 3, KETTE_GOLD, geschlossen=True))
    k.dazu(kugel((0.046, 0.014, 0.046), 6, 3, KETTE_GOLD, e_hoch=0.7, e_rund=0.7),
           platz(rumpf_punkt(0.0, 0.482, abstand=0.026), ausrichtung((0, -1, -0.15), (0, 0, 1))))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    unter_cap = (c + Vector((0, 0, 0.10)), Vector((0, 0.10, 1.0)).normalized())
    kopf_haut(kopf, [unter_cap], bart_farbe(BARTSCHATTEN, -0.125, -0.03))
    haar(kopf, HAAR_SCHWARZBRAUN, [wg.haar_ebene(0.07, 50.0), unter_cap])
    gesicht_crew(kopf, BRAUE_DUNKEL, laecheln=0.10, braue_hoch=0.05, mund_hoehe=-0.35, iris="#3A2A22", blick=(0.0, 0.006))
    # Cap: vorn hoch, hinten tiefer, Schirm zeigt nach hinten
    R = (0.264, 0.250, 0.250)
    kuppel = verschoben(kugel(R, 12, 7, CAP_BLAU), platz(c + Vector((0, 0.01, 0.035))))
    kuppel = schneiden(kuppel, [(c + Vector((0, 0, 0.07)), (0, -0.10, -1.0))])
    kopf.dazu(kuppel)
    kopf.dazu(kugel((0.215, 0.18, 0.020), 8, 3, CAP_BLAU_DUNKEL, e_hoch=0.8, e_rund=0.9),
              platz(c + Vector((0.0, 0.250, 0.06)), drehung(x=-14.0)))
    kopf.dazu(kugel((0.022, 0.022, 0.014), 6, 2, CAP_BLAU_DUNKEL), platz(c + Vector((0, 0.01, 0.287))))

    arm_crew(t["arm_r"][0], t["arm_r"][1], (-0.17, 0.0, -1.0), JACKE_GRUEN)
    # Linke Hand erhoben -- winkt (wie die bisherige Fassung)
    arm_crew(t["arm_l"][0], t["arm_l"][1], (0.80, -0.18, 0.62), JACKE_GRUEN)
    glieder(t, None, JEANS_DUNKEL, SNEAKER, SOHLE, arme=False)
    return t


# =============================================================================
# Figur: Fischerhut
# =============================================================================

HUT_DUNKEL = "#F2E8D5"
HUT_BAND = "#FF4FA3"
SHIRT_SCHWARZ = "#FF4FA3"       # Younes: Absenderfarbe
SHIRT_SCHWARZ_SAUM = "#E83E8E"
BART_DUNKEL = "#4A3528"
HOSE_SAND = "#C9AE84"
SCHUH_DUNKEL = "#474B55"
KAMERA = "#E2DDD2"
KAMERA_DUNKEL = "#3A3D44"
LINSE = "#6A8FBF"
RIEMEN = "#C8925A"


def figur_buckethat():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, SHIRT_SCHWARZ, HOSE_SAND, grenze=0.285, bund=SHIRT_SCHWARZ_SAUM)
    # Kamera vor der Brust, Riemen um den Nacken
    kam = rumpf_punkt(0.0, 0.440, abstand=0.036)
    k.dazu(kugel((0.100, 0.044, 0.064), 6, 3,
                 lambda x, y, z: KAMERA_DUNKEL if z < -0.3 else KAMERA, e_hoch=0.5, e_rund=0.5),
           platz(kam))
    objektiv = [(0.0, 0.042), (0.046, 0.042), (0.052, 0.033), (0.055, 0.0)]
    k.dazu(drehkoerper(objektiv, 6, lambda tt: LINSE if tt > 0.035 else KAMERA_DUNKEL),
           platz(kam + Vector((-0.016, -0.026, -0.002)), ausrichtung((0, -1, 0), (0, 0, 1))))
    for s in (1.0, -1.0):
        riemen = [kam + Vector((s * 0.066, 0.0, 0.02)),
                  rumpf_punkt(s * 0.085, 0.53, abstand=0.010),
                  rumpf_punkt(s * 0.090, 0.595, abstand=0.010),
                  Vector((s * 0.07, 0.06, 0.643))]
        k.dazu(rohr(riemen, 0.008, 3, RIEMEN, kappen=False))
    k.dazu(rohr([Vector((0.07, 0.06, 0.643)), Vector((0.0, 0.112, 0.646)), Vector((-0.07, 0.06, 0.643))],
                0.008, 3, RIEMEN, kappen=False))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    unter_hut = (c + Vector((0, 0, 0.13)), Vector((0, 0.17, 1.0)).normalized())
    kopf_haut(kopf, [unter_hut], bart_farbe(BART_DUNKEL, -0.118, 0.01))
    haar(kopf, HAAR_SCHWARZBRAUN, [wg.haar_ebene(0.07, 52.0), unter_hut])
    gesicht_crew(kopf, BRAUE_DUNKEL, laecheln=0.03, braue_hoch=-0.03, mund_hoehe=-0.40,
                 mund_breite=0.10, braue_dicke=0.012, iris="#3A2A22", blick=(0.0, -0.003), lid=0.25)
    # Kurzer Bart: etwas Volumen am Kinn, Schnurrbart ueber dem Mund
    kopf.dazu(kugel((0.085, 0.05, 0.042), 8, 4, BART_DUNKEL), platz(c + Vector((0, -0.150, -0.150)), drehung(x=-30.0)))
    schnurr = [auf_flaeche(c, KOPF_R, (u, -1.0, -0.29 - 0.04 * abs(u) / 0.14), einsinken=-0.004)[0]
               for u in (-0.14, 0.0, 0.14)]
    kopf.dazu(rohr(schnurr, 0.011, 3, BART_DUNKEL, kappen=False))

    # Fischerhut: Krone plus abfallende Krempe, in den Nacken geschoben
    hut = Bau("hut")
    krone = [(0.0, 0.262), (0.15, 0.246), (0.215, 0.19), (0.235, 0.0)]
    hut.dazu(drehkoerper(krone, 12, lambda tt: HUT_BAND if tt < 0.05 else HUT_DUNKEL, sy=0.98))
    krempe = [(0.030, 0.252), (-0.040, 0.385), (-0.026, 0.390), (0.042, 0.252)]
    hut.dazu(drehkoerper(krempe, 12, HUT_DUNKEL, sy=0.98))
    hut.drehen((0, 0, 0), drehung(x=-12.0))
    hut.verschieben(c + Vector((0, 0.012, 0.095)))
    kopf.dazu((hut.punkte, hut.flaechen, hut.farben))

    glieder(t, SHIRT_SCHWARZ, HOSE_SAND, SCHUH_DUNKEL, SOHLE, aermel_ende=0.09)
    return t


# =============================================================================
# Figur: Brille, Undercut, Latzhose
# =============================================================================

HAAR_BLOND = "#EDCB80"
HAAR_BLOND_KURZ = "#CDAA70"
BRAUE_BLOND = "#A8844E"
BRILLE = "#1B1726"
LATZ = "#FF7A1A"            # Roman: Absenderfarbe
LATZ_NAHT = "#E0640A"
KNOPF = "#E6C35C"
SCHUH_ROT = "#E0663F"
KLECKSE = ["#FF4FA3", "#FFB020", "#33C3B0", "#8B5CF6"]


def figur_brille():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, SHIRT_WEISS, LATZ, grenze=0.33)
    # Latz vorn, Traeger ueber die Schultern bis in den Hosenbund hinten
    p, m = auf_rumpf(0.0, 0.43, abstand=-0.004)
    flach(k, (0.115, 0.10, 0.014), p, LATZ, matrix3=m, e=0.45)
    for s in (1.0, -1.0):
        traeger = [rumpf_punkt(s * 0.088, 0.515, abstand=0.004),
                   rumpf_punkt(s * 0.098, 0.585, abstand=0.008),
                   Vector((s * 0.105, 0.0, 0.642)),
                   rumpf_punkt(s * 0.090, 0.55, hinten=True, abstand=0.008),
                   rumpf_punkt(s * 0.060, 0.32, hinten=True, abstand=0.004)]
        k.dazu(rohr(traeger, 0.013, 3, LATZ_NAHT, kappen=False))
        k.dazu(kugel((0.014, 0.014, 0.008), 6, 2, KNOPF), platz(rumpf_punkt(s * 0.088, 0.512, abstand=0.016)))
    # Farbkleckse auf Latz und Hose
    for (x, z, g), hexwert in zip(((0.07, 0.40, 0.022), (-0.05, 0.47, 0.017),
                                   (-0.11, 0.29, 0.022), (0.12, 0.26, 0.018)), KLECKSE):
        p, m = auf_rumpf(x, z, abstand=0.004 if abs(x) < 0.10 else 0.0)
        flach(k, (g, g * 0.8, 0.005), p, hexwert, matrix3=m, e=0.9, ringe=2)
    t["bein_l"][0].dazu(kugel((0.018, 0.006, 0.014), 6, 2, KLECKSE[0], e_hoch=0.9, e_rund=0.9),
                        platz(Vector((0.10, -0.062, 0.14))))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    kopf_haut(kopf, [unter_haar(0.10, 60.0)])
    # Undercut: kurze Seiten unten, darueber das volle Deckhaar mit Tolle
    deck_grenze = (c + Vector((0, 0, 0.125)), Vector((0, -0.18, 1.0)).normalized())
    haar(kopf, HAAR_BLOND_KURZ,
         [wg.haar_ebene(0.10, 60.0), deck_grenze,
          (c + Vector((0, 0.10, -0.02)), Vector((0, -0.55, -1.0)).normalized())],
         dicke=(0.005, 0.006, 0.005), versatz=(0, 0.004, 0.004))
    haar(kopf, HAAR_BLOND,
         [(c + Vector((0, 0, 0.105)), Vector((0, 0.18, -1.0)).normalized()), wg.haar_ebene(0.13, 42.0)],
         dicke=(0.020, 0.026, 0.040), versatz=(0, 0.004, 0.018))
    kopf.dazu(kugel((0.12, 0.085, 0.065), 8, 4, HAAR_BLOND, e_hoch=0.9),
              platz(c + Vector((0.03, -0.13, 0.225)), drehung(x=-25.0, y=-10.0)))
    gesicht_crew(kopf, BRAUE_BLOND, laecheln=0.05, braue_hoch=(0.10, -0.01), mund_breite=0.10, braue_dicke=0.012,
                 iris="#2E4A7A", blick=(0.0, 0.004))
    # Runde Brille vor den Augen
    mitte = {}
    for s in (1.0, -1.0):
        p, n = auf_flaeche(c, KOPF_R, (s * 0.36, -1.0, -0.08), einsinken=-0.030)
        mitte[s] = p
        a = ausrichtung(n, (0, 0, 1))
        ring = [p + a @ Vector((0.080 * math.cos(w), 0.078 * math.sin(w), 0.0))
                for w in (2 * math.pi * i / 8 for i in range(8))]
        kopf.dazu(rohr(ring, 0.0125, 3, BRILLE, geschlossen=True))
        aussen = p + a @ Vector((s * 0.080, 0.0, 0.0))
        buegel = [aussen, auf_flaeche(c, KOPF_R, (s * 1.0, -0.62, -0.05), einsinken=-0.006)[0]]
        kopf.dazu(rohr(buegel, 0.0065, 3, BRILLE, kappen=False))
    steg = [mitte[1.0] + Vector((-0.080, -0.004, 0.006)),
            auf_flaeche(c, KOPF_R, (0.0, -1.0, -0.02), einsinken=-0.012)[0],
            mitte[-1.0] + Vector((0.080, -0.004, 0.006))]
    kopf.dazu(rohr(steg, 0.0095, 3, BRILLE, kappen=False))
    pose(t, ["kopf"], t["kopf"][1], drehung(y=5.0))

    glieder(t, SHIRT_WEISS, LATZ, SCHUH_ROT, "#F2EEE8", aermel_ende=0.09)
    return t


# =============================================================================
# Figur: Zopf, Weste, Werkzeugguertel, Headset
# =============================================================================

WESTE = "#8B5CF6"
WESTE_DUNKEL = "#7447DB"
HEMD_HELL = "#ECE9F2"
HAAR_ZOPF = "#3A2A30"
BRAUE_ZOPF = "#2F2126"
HOSE_ARBEIT = "#4F5566"
STIEFEL = "#80583A"
STIEFEL_SOHLE = "#5A3E2A"
GUERTEL = "#8A5A3A"
GUERTEL_TASCHE = "#A36D45"
SCHNALLE = "#D9D4C8"
WERKZEUG = "#B7BDC6"
GRIFF_GELB = "#F2B200"
HEADSET = "#1B1726"
HEADSET_POLSTER = "#8B5CF6"


def figur_zopf():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, WESTE, HOSE_ARBEIT, grenze=0.285)
    # Hemd als Streifen vorn zwischen den Westenkanten
    p, m = auf_rumpf(0.0, 0.50, abstand=-0.004)
    flach(k, (0.050, 0.095, 0.013), p, HEMD_HELL, matrix3=m)
    for s in (1.0, -1.0):
        linie_auf_rumpf(k, s * 0.050, (0.40, 0.50, 0.60), 0.010, WESTE_DUNKEL)
    # Werkzeugguertel mit zwei Taschen, darin Schluessel und Schraubendreher
    ring_um_rumpf(k, 0.265, 0.315, 0.012, GUERTEL)
    flach(k, (0.024, 0.02, 0.008), rumpf_punkt(0.0, 0.29, abstand=0.012), SCHNALLE, ringe=2)
    for x in (0.12, -0.13):
        p, m = auf_rumpf(x, 0.275, abstand=0.022)
        flach(k, (0.042, 0.052, 0.028), p, GUERTEL_TASCHE, matrix3=m, e=0.5)
    oben_l = rumpf_punkt(0.12, 0.30, abstand=0.03)
    k.dazu(rohr([oben_l, oben_l + Vector((0.01, -0.005, 0.10))], 0.009, 3, WERKZEUG, kappen=False))
    k.dazu(kugel((0.022, 0.008, 0.018), 6, 2, WERKZEUG), platz(oben_l + Vector((0.012, -0.006, 0.11))))
    oben_r = rumpf_punkt(-0.13, 0.30, abstand=0.03)
    k.dazu(rohr([oben_r, oben_r + Vector((-0.012, -0.004, 0.075))], 0.013, 3, GRIFF_GELB))

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    kopf_haut(kopf, [unter_haar(0.11, 58.0)])
    haar(kopf, HAAR_ZOPF, [wg.haar_ebene(0.11, 58.0)])
    gesicht_crew(kopf, BRAUE_ZOPF, laecheln=0.04, braue_hoch=-0.01, iris="#5A2E7A", blick=(0.0, 0.002))
    # Hoher Zopf: Knoten hinten oben, Band, Schwanz faellt in den Nacken
    knoten = c + Vector((0.0, 0.18, 0.15))
    kopf.dazu(kugel((0.060, 0.060, 0.060), 6, 3, HAAR_ZOPF), platz(knoten))
    kopf.dazu(drehkoerper([(0.0, 0.040), (0.03, 0.040)], 6, WESTE),
              platz(knoten + Vector((0, 0.035, 0.02)), ausrichtung((0, 1.0, 0.45))))
    schwanz = [knoten + Vector((0, 0.05, 0.035)), c + Vector((0, 0.30, 0.17)), c + Vector((0, 0.36, 0.09)),
               c + Vector((0, 0.35, 0.00)), c + Vector((0, 0.31, -0.13)), c + Vector((0, 0.27, -0.22))]
    kopf.dazu(rohr(schwanz, 0.05, 5, HAAR_ZOPF,
                   radius_fn=lambda u: 0.044 + 0.018 * math.sin(math.pi * min(u * 1.6, 1.0)) * (1 - u) - 0.024 * u))
    # Headset: Buegel ueber den Scheitel, Muscheln, Mikrofonarm links
    buegel = [Vector((0.276 * math.cos(w), 0.0, 0.272 * math.sin(w))) + c + Vector((0, -0.01, 0.0))
              for w in (math.pi * i / 6 for i in range(7))]
    kopf.dazu(rohr(buegel, 0.018, 3, HEADSET, kappen=False))
    for s in (1.0, -1.0):
        kopf.dazu(kugel((0.074, 0.082, 0.036), 6, 2,
                        lambda x, y, z: HEADSET_POLSTER if z < 0.3 else HEADSET, e_hoch=0.6),
                  platz(c + Vector((s * 0.262, -0.01, -0.01)), ausrichtung((s, 0, 0), (0, 0, 1))))
    mikro = [c + Vector((0.285, -0.03, -0.03)), c + Vector((0.255, -0.13, -0.08)),
             c + Vector((0.17, -0.215, -0.10)), c + Vector((0.10, -0.24, -0.10))]
    kopf.dazu(rohr(mikro, 0.007, 3, HEADSET, kappen=False))
    kopf.dazu(kugel((0.024, 0.024, 0.024), 6, 2, WESTE), platz(mikro[-1]))

    glieder(t, HEMD_HELL, HOSE_ARBEIT, STIEFEL, STIEFEL_SOHLE, aermel_ende=0.17, knoechel=STIEFEL)
    pose(t, ["kopf"], t["kopf"][1], drehung(y=-4.0))
    return t


# =============================================================================
# Figur: Warnweste, kurze Muetze
# =============================================================================

WARNWESTE = "#FF8A2A"
REFLEX = "#E4E8EC"
PULLI_GRAU = "#77808F"
HOSE_CARGO = "#565E4C"
HOSE_CARGO_TASCHE = "#4B5242"
MUETZE_KURZ = "#3E6FA8"
MUETZE_STULPE = "#335E91"
HANDSCHUH = "#D9A441"
HAAR_BRAUN = "#6B4630"
BRAUE_BRAUN = "#4A2F20"


def figur_packer():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, WARNWESTE, HOSE_CARGO, grenze=0.285)
    ring_um_rumpf(k, 0.370, 0.400, 0.007, REFLEX)
    ring_um_rumpf(k, 0.440, 0.470, 0.007, REFLEX)
    # Pulli-Ausschnitt oben (die Weste ist aermellos)
    p, m = auf_rumpf(0.0, 0.575, abstand=-0.003)
    flach(k, (0.055, 0.035, 0.012), p, PULLI_GRAU, matrix3=m)
    for s in (1.0, -1.0):
        linie_auf_rumpf(k, s * 0.092, (0.40, 0.50, 0.595), 0.011, REFLEX, abstand=0.006)
        linie_auf_rumpf(k, s * 0.092, (0.40, 0.50, 0.595), 0.011, REFLEX, hinten=True, abstand=0.006)
    # Seitentaschen der Cargohose
    for n, s in (("bein_l", 1.0), ("bein_r", -1.0)):
        flach(t[n][0], (0.032, 0.040, 0.010), Vector((s * 0.145, -0.02, 0.19)), HOSE_CARGO_TASCHE,
              matrix3=ausrichtung((s, -0.3, 0), (0, 0, 1)), ringe=2)

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    rand_z = c.z + 0.105
    ueber_rand = (Vector((0, 0, rand_z + 0.015)), Vector((0, 0.05, 1.0)).normalized())
    kopf_haut(kopf, [ueber_rand])
    haar(kopf, HAAR_BRAUN, [wg.haar_ebene(0.06, 56.0), ueber_rand])
    gesicht_crew(kopf, BRAUE_BRAUN, laecheln=0.06, braue_hoch=0.01)
    # Kurze Hafenmuetze: sitzt hoch, flache Kuppe, dicke Stulpe
    R = (0.262, 0.246, 0.20)
    kuppel = verschoben(kugel(R, 12, 6, MUETZE_KURZ, e_hoch=0.8), platz(c + Vector((0, 0.01, 0.095))))
    kuppel = schneiden(kuppel, [(Vector((0, 0, rand_z + 0.03)), Vector((0, 0, -1.0)))])
    kopf.dazu(kuppel)
    stulpe = [(0.0, 0.254), (0.036, 0.276), (0.072, 0.250)]
    kopf.dazu(drehkoerper(stulpe, 12, MUETZE_STULPE, sy=0.94), platz(Vector((0, 0.01, rand_z - 0.012))))

    glieder(t, PULLI_GRAU, HOSE_CARGO, "#6E5A48", "#3F342B", aermel_ende=0.19, hand=HANDSCHUH,
            knoechel=HOSE_CARGO)
    return t


# =============================================================================
# Figur: Anzug
# =============================================================================

ANZUG = "#3A4768"
ANZUG_REVERS = "#2E3955"
KRAWATTE = "#E0A91E"
HAAR_ANZUG = "#4A3A34"
SCHUH_BRAUN = "#5A3D2B"
KOFFER = "#7A5236"
KOFFER_BESCHLAG = "#E0C27A"


def figur_anzug():
    t = neues_skelett()
    k = t["koerper"][0]
    rumpf(k, ANZUG, ANZUG, grenze=0.285)
    # Hemd-V, Krawatte, Revers, Knoepfe, Einstecktuch
    p, m = auf_rumpf(0.0, 0.535, abstand=-0.004)
    flach(k, (0.050, 0.075, 0.013), p, SHIRT_WEISS, matrix3=m)
    p, m = auf_rumpf(0.0, 0.50, abstand=0.008)
    flach(k, (0.020, 0.075, 0.008), p, KRAWATTE, matrix3=m, e=0.8)
    flach(k, (0.018, 0.014, 0.010), rumpf_punkt(0.0, 0.585, abstand=0.010), KRAWATTE, e=0.8, ringe=2)
    for s in (1.0, -1.0):
        revers = [rumpf_punkt(s * 0.062, 0.605, abstand=0.004), rumpf_punkt(s * 0.050, 0.52, abstand=0.008),
                  rumpf_punkt(s * 0.020, 0.43, abstand=0.006)]
        k.dazu(rohr(revers, 0.014, 3, ANZUG_REVERS, kappen=False))
    for z in (0.40, 0.35):
        k.dazu(kugel((0.010, 0.010, 0.006), 6, 2, ANZUG_REVERS), platz(rumpf_punkt(0.0, z, abstand=0.004)))
    p, m = auf_rumpf(0.10, 0.52, abstand=0.003)
    flach(k, (0.022, 0.010, 0.006), p, SHIRT_WEISS, matrix3=m, ringe=2)

    kopf = t["kopf"][0]
    c = KOPF_MITTE
    kopf_haut(kopf, [unter_haar(0.10, 56.0)])
    haar(kopf, HAAR_ANZUG, [wg.haar_ebene(0.10, 56.0)])
    # Seitenscheitel: flache Welle vorn ueber der Stirn, zur Seite gekaemmt
    kopf.dazu(kugel((0.13, 0.075, 0.04), 8, 4, HAAR_ANZUG, e_hoch=0.9),
              platz(c + Vector((0.04, -0.125, 0.205)), drehung(x=-38.0, y=12.0)))
    gesicht_crew(kopf, "#3A2C27", laecheln=0.05)

    arm_crew(t["arm_l"][0], t["arm_l"][1], (0.17, 0.0, -1.0), ANZUG, aermel_ende=0.19)
    schulter = t["arm_r"][1]
    richtung = Vector((-0.12, 0.0, -1.0))
    arm_crew(t["arm_r"][0], schulter, richtung, ANZUG, aermel_ende=0.19)
    hand = hand_punkt(schulter, richtung)
    # Aktenkoffer haengt an der rechten Hand
    a = t["arm_r"][0]
    koffer = hand + Vector((-0.005, 0.0, -0.105))
    a.dazu(kugel((0.03, 0.12, 0.08), 8, 3, KOFFER, e_hoch=0.45, e_rund=0.45), platz(koffer))
    griff = [hand + Vector((0.0, 0.04, -0.035)), hand + Vector((0.0, 0.03, 0.0)),
             hand + Vector((0.0, -0.03, 0.0)), hand + Vector((0.0, -0.04, -0.035))]
    a.dazu(rohr(griff, 0.008, 3, KOFFER_BESCHLAG, kappen=False))
    for dy in (0.07, -0.07):
        a.dazu(kugel((0.034, 0.010, 0.010), 6, 2, KOFFER_BESCHLAG), platz(koffer + Vector((0.0, dy, 0.07))))
    glieder(t, None, ANZUG, SCHUH_BRAUN, "#3E2A1E", arme=False)
    return t


FIGUREN = {
    "figur_kapuze": wg.figur_kapuze,
    "figur_kapuze_sitzend": wg.figur_kapuze_sitzend,
    "figur_cap": figur_cap,
    "figur_buckethat": figur_buckethat,
    "figur_brille": figur_brille,
    "figur_zopf": figur_zopf,
    "figur_packer": figur_packer,
    "figur_anzug": figur_anzug,
}


# =============================================================================
# Vorschau
# =============================================================================

def zusammensetzen(dateien, ziel):
    """Einzelbilder nebeneinander zu einem Streifen."""
    import numpy as np
    teile = []
    for d in dateien:
        img = bpy.data.images.load(os.path.join(VORSCHAU, d))
        w, h = img.size
        teile.append(np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4))
        bpy.data.images.remove(img)
    streifen = np.concatenate(teile, axis=1)
    h, w = streifen.shape[:2]
    neu = bpy.data.images.new("streifen", w, h, alpha=True)
    neu.pixels.foreach_set(streifen.ravel())
    neu.filepath_raw = os.path.join(VORSCHAU, ziel)
    neu.file_format = "PNG"
    neu.save()
    bpy.data.images.remove(neu)
    for d in dateien:
        os.remove(os.path.join(VORSCHAU, d))


ANSICHTEN = [
    ("vorn", (0.0, -1.0, 0.10)),
    ("dreiviertel", (0.85, -1.0, 0.30)),
    ("spiel", (1.0, -1.0, 1.0)),      # Godot (+1, +1, +1)
    ("hinten", (-0.5, 1.0, 0.25)),
]


def vorschau_einzeln(name):
    wg.vorschau_szene(boden="#E9DFD2")
    if name.endswith("sitzend"):
        wg.hocker((0, 0, 0))
    wg.figur_laden(name, (0, 0, 0))
    dateien = []
    for ansicht, richtung in ANSICHTEN:
        wg.kamera((0, 0, 0.64), richtung, 1.45, 520, 700)
        datei = "_%s_%s.png" % (name, ansicht)
        wg.rendern(datei)
        dateien.append(datei)
    zusammensetzen(dateien, name + ".png")


def gruppe():
    namen = list(FIGUREN.keys())
    iso = Vector((1.0, -1.0, 1.0))
    # frontal
    wg.vorschau_szene(boden="#E9DFD2")
    for i, name in enumerate(namen):
        ort = Vector((0.85 * (i - (len(namen) - 1) / 2.0), 0, 0))
        if name.endswith("sitzend"):
            wg.hocker(ort)
        wg.figur_laden(name, ort)
    wg.kamera((0, 0, 0.66), (0, -1, 0.12), 7.2, 2000, 440)
    wg.rendern("gruppe_vorn.png")
    wg.kamera((0, 0, 0.66), (0, 1, 0.12), 7.2, 2000, 440)
    wg.rendern("gruppe_hinten.png")
    # Spielwinkel, Reihe quer zur Blickrichtung
    wg.vorschau_szene()
    achse = Vector((1, 1, 0)).normalized()
    for i, name in enumerate(namen):
        ort = achse * (0.95 * (i - (len(namen) - 1) / 2.0))
        if name.endswith("sitzend"):
            wg.hocker(ort)
        wg.figur_laden(name, ort)
    wg.kamera((0, 0, 0.55), iso, 8.6, 2000, 700)
    wg.rendern("gruppe_spiel.png")
    px_je_m = 56.0
    wg.kamera((0, 0, 0.55), iso, 8.6, int(8.6 * px_je_m), int(8.6 * px_je_m * 0.35))
    wg.rendern("gruppe_spiel_60px.png")
    wg.hochskalieren("gruppe_spiel_60px.png", 4, "gruppe_spiel_60px_x4.png")
    os.remove(os.path.join(VORSCHAU, "gruppe_spiel_60px.png"))
    # Probe-Pose: Glieder um +-30 Grad gedreht (Spalten an Gelenken?)
    wg.vorschau_szene(boden="#E9DFD2")
    for i, name in enumerate(namen):
        ort = Vector((0.85 * (i - (len(namen) - 1) / 2.0), 0, 0))
        if name.endswith("sitzend"):
            wg.hocker(ort)
        teile = wg.figur_laden(name, ort, drehung_z=-60.0)
        teile["arm_l"].rotation_euler.x = math.radians(35.0)
        teile["arm_r"].rotation_euler.x = math.radians(-35.0)
        teile["bein_l"].rotation_euler.x = math.radians(-30.0)
        teile["bein_r"].rotation_euler.x = math.radians(30.0)
        teile["kopf"].rotation_euler.x = math.radians(12.0)
    wg.kamera((0, 0, 0.66), (0.3, -1, 0.35), 7.2, 2000, 520)
    wg.rendern("gruppe_pose.png")


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    nur = [a for a in args if a.startswith("figur_")]
    print("")
    print("=== CHIBI-FIGUREN GEMEINSAM ===")
    ok = True
    for name, bauen in FIGUREN.items():
        wg.szene_leeren()
        teile = bauen()
        pfad, dreiecke, zmin, zmax, je_teil = wg.exportieren(name, teile)
        kb = os.path.getsize(pfad) / 1024.0
        warnung = "" if dreiecke <= BUDGET_DREIECKE else "  << UEBER BUDGET"
        if dreiecke > BUDGET_DREIECKE:
            ok = False
        print("  %-22s %4d Dreiecke  Hoehe %.3f m (min %.3f)  %5.1f KB%s"
              % (name, dreiecke, zmax, zmin, kb, warnung))
        print("      " + "  ".join("%s %d" % kv for kv in je_teil.items()))
        fehler, zeilen = wg.pruefen(name)
        for z in zeilen:
            print(z)
        for f in fehler:
            ok = False
            print("      FEHLER: " + f)
    ziel = os.path.join(AUSGABE_WG, "figur_cap.glb")
    shutil.copyfile(os.path.join(AUSGABE, "figur_cap.glb"), ziel)
    print("  kopiert: " + ziel)
    print("  Pruefung: " + ("OK" if ok else "FEHLER"))
    if "--ohne-vorschau" not in args:
        os.makedirs(VORSCHAU, exist_ok=True)
        for name in FIGUREN:
            if not nur or name in nur:
                vorschau_einzeln(name)
        if "--ohne-gruppe" not in args:
            gruppe()
        print("  Vorschau: " + VORSCHAU)


if __name__ == "__main__":
    main()
