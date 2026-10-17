#!/usr/bin/env python3
"""Auswertung der lokalen Messdatei (K3 C3, docs/neu/K3_AB_BEWERTUNG.md).

Holen:  adb shell run-as tech.wvmit.helloworld cat files/messung.json > messung.json
        (oder im Spiel "Messdaten kopieren" und in eine Datei einfuegen)
Lesen:  python tools/messung_bericht.py messung.json [--json] [--nur karte=b,pfeil=b]

Je Variantenkombination (Schirme karte, plakette, pfeil, zoom, boost) werden die
Kennzahlen fuer K1, K2, K4 aus den Sitzungen gerechnet. K3 (Lesbarkeit) und K5
(Ruhe) kommen aus Bildern, nicht aus dieser Datei.
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict

SCHIRME = ["karte", "plakette", "pfeil", "zoom", "boost"]
TIPPS = ("tipp_station", "tipp_plakette", "tipp_leer")
SINNVOLL = ("tipp_station", "tipp_plakette")
# Ein Dopamin-Moment: Raum, Moment (getippt), Angebot genommen; Kauf zaehlt hier nicht.
JUICE = ("raum", "moment", "angebot_genommen")


def lade(pfad):
    with open(pfad, encoding="utf-8-sig") as f:
        text = f.read()
    # adb auf Windows liefert CRLF; run-as kann eine Fehlerzeile vorneweg setzen.
    anfang = text.find("{")
    if anfang < 0:
        sys.exit("keine JSON-Daten in " + pfad)
    return json.loads(text[anfang:])


def dauer(ereignisse):
    ts = [e["t"] for e in ereignisse]
    return max(ts) if ts else 0.0


def erstes(ereignisse, arten, nach=None):
    for e in ereignisse:
        if e["e"] in arten and (nach is None or nach(e)):
            return e["t"]
    return None


def kennzahlen(s):
    ev = s.get("ereignisse", [])
    minuten = max(dauer(ev) / 60.0, 1e-9)
    tipps = [e for e in ev if e["e"] in TIPPS]
    leer = [e for e in tipps if e["e"] == "tipp_leer"]
    kaeufe = [e for e in ev if e["e"] == "kauf"]
    raeume = sorted(e["t"] for e in ev if e["e"] == "raum")
    juice = sorted(e["t"] for e in ev if e["e"] in JUICE)
    luecken = [b - a for a, b in zip([0.0] + juice, juice + [dauer(ev)])]
    angebote = {a: sum(1 for e in ev if e["e"] == a)
                for a in ("angebot_gezeigt", "angebot_genommen", "angebot_abgelehnt")}
    return {
        "dauer_min": minuten if ev else 0.0,
        "k1_erster_tipp_s": erstes(ev, ("erster_tipp",)),
        "k1_erster_sinnvoller_tipp_s": erstes(ev, SINNVOLL),
        "k1_erster_kauf_s": erstes(ev, ("kauf",)),
        "k2_tipps": len(tipps),
        "k2_leertipp_anteil": (len(leer) / len(tipps)) if tipps else None,
        "leertipps_pro_min": len(leer) / minuten,
        "kaeufe_pro_min": len(kaeufe) / minuten,
        "raum_2_s": raeume[0] if len(raeume) > 0 else None,
        "raum_3_s": raeume[1] if len(raeume) > 1 else None,
        "k4_juice_pro_min": len(juice) / minuten,
        "k4_juice_pro_min_erste10": sum(1 for t in juice if t <= 600) / min(10.0, minuten),
        "k4_laengste_pause_s": max(luecken) if luecken else None,
        "angebote": angebote,
    }


def mittel(werte):
    werte = [w for w in werte if w is not None]
    return statistics.mean(werte) if werte else None


def fmt(wert, nachkomma=1, suffix=""):
    if wert is None:
        return "-"
    return f"{wert:.{nachkomma}f}{suffix}"


def schluessel(s, schirme):
    ab = s.get("ab", {})
    return ", ".join(f"{k}={ab[k]}" for k in schirme if k in ab) or "(ohne Varianten)"


def filter_ab(sitzungen, text):
    if not text:
        return sitzungen
    soll = dict(p.split("=", 1) for p in text.split(",") if "=" in p)
    return [s for s in sitzungen if all(s.get("ab", {}).get(k) == v for k, v in soll.items())]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("datei")
    ap.add_argument("--json", action="store_true", help="Kennzahlen als JSON ausgeben")
    ap.add_argument("--nur", default="", help="nur Sitzungen mit diesen Varianten, z. B. karte=b,pfeil=a")
    ap.add_argument("--je", default=",".join(SCHIRME),
                    help="Schirme, nach denen gruppiert wird (Standard: alle fuenf)")
    a = ap.parse_args()
    daten = lade(a.datei)
    schirme = [x for x in a.je.split(",") if x]
    sitzungen = filter_ab(daten.get("sitzungen", []), a.nur)
    if not sitzungen:
        sys.exit("keine passenden Sitzungen")

    gruppen = defaultdict(list)
    for s in sitzungen:
        gruppen[schluessel(s, schirme)].append(s)

    ergebnis = {}
    for name, liste in sorted(gruppen.items()):
        je = [kennzahlen(s) for s in liste]
        ergebnis[name] = {"sitzungen": [int(s.get("sitzung", 0)) for s in liste],
                          "je_sitzung": je,
                          "mittel": {k: mittel([j[k] for j in je]) for k in je[0] if k != "angebote"}}
    if a.json:
        print(json.dumps(ergebnis, indent=1, ensure_ascii=False))
        return

    for name, e in ergebnis.items():
        m = e["mittel"]
        print(f"\n=== {name}   ({len(e['sitzungen'])} Sitzung(en): {e['sitzungen']}) ===")
        print(f"  Dauer (Mittel)                       {fmt(m['dauer_min'])} min")
        print(f"  K1 erster Tipp                       {fmt(m['k1_erster_tipp_s'])} s      (Ziel <= 3)")
        print(f"  K1 erster sinnvoller Tipp            {fmt(m['k1_erster_sinnvoller_tipp_s'])} s      (Ziel <= 3)")
        print(f"  K1 erster Kauf                       {fmt(m['k1_erster_kauf_s'])} s")
        print(f"  K2 Tipps / Leertippanteil            {fmt(m['k2_tipps'], 0)} / {fmt(None if m['k2_leertipp_anteil'] is None else m['k2_leertipp_anteil'] * 100, 0, ' %')}   (Ziel <= 10 %)")
        print(f"  Leertipps pro Minute                 {fmt(m['leertipps_pro_min'], 2)}")
        print(f"  Kaeufe pro Minute                    {fmt(m['kaeufe_pro_min'], 2)}")
        print(f"  Zeit bis Raum 2 / Raum 3             {fmt(m['raum_2_s'])} s / {fmt(m['raum_3_s'])} s")
        print(f"  K4 Juice pro Minute (gesamt/Min 1-10) {fmt(m['k4_juice_pro_min'], 2)} / {fmt(m['k4_juice_pro_min_erste10'], 2)}   (Ziel >= 2 in Min 1-10)")
        print(f"  K4 laengste Pause ohne Juice         {fmt(m['k4_laengste_pause_s'])} s   (Ziel <= 180)")
        ang = defaultdict(int)
        for j in e["je_sitzung"]:
            for k, v in j["angebote"].items():
                ang[k] += v
        print(f"  Angebote gezeigt/genommen/abgelehnt  {ang['angebot_gezeigt']} / {ang['angebot_genommen']} / {ang['angebot_abgelehnt']}")
    print("\nHinweis: K3 (Lesbarkeit) und K5 (Ruhe) werden aus Bildern bewertet, nicht aus der Messdatei.")


if __name__ == "__main__":
    main()
