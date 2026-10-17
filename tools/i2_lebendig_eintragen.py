"""Einmal-Werkzeug I2: traegt die Lebendig-Daten (licht.himmel/glow/partikel, kulisse[].animation,
emission_puls) textgenau in data/worlds/worlds.json ein, ohne die Handformatierung zu zerstoeren.
Idempotent: Eintraege, die schon da sind, werden nicht doppelt gesetzt."""
import json
import re
import sys

PFAD = "project/data/worlds/worlds.json"
T = "\t"


def j(x):
    return json.dumps(x, ensure_ascii=False, separators=(", ", ": "))


DATEN = {
    "zimmer": {
        "licht": {
            "himmel": {"oben": "bcd9ee", "unten": "dfe9d0"},
            "partikel": [
                {"typ": "staub", "x": 2, "z": 2, "menge": 10, "radius": 4},
                {"typ": "voegel", "x": -4, "z": -6, "menge": 3},
            ],
        },
        "kulisse": {
            "welt_strasse": {"emission_puls": {"hz": 0.3, "min": 0.75, "max": 1.25}},
            "welt_auto_klein": {"animation": {"typ": "fahren", "tempo": 2.2, "modus": "einmal", "pause": 6,
                                              "blick_versatz": 90, "route": [[0, 0], [-26, 0]]}},
            "welt_balkon_deko": {"animation": {"typ": "wackeln", "tempo": 0.5, "winkel": 1.5}},
        },
    },
    "auftrag": {
        "licht": {
            "himmel": {"oben": "2a2145", "unten": "4b3d63", "sterne": 18},
            "glow": {"intensitaet": 0.4, "staerke": 0.8, "schwelle": 1.0},
            "partikel": [
                {"typ": "motten", "x": 11.8, "z": 10.4, "menge": 5},
                {"typ": "staub", "x": 0, "z": 0, "menge": 8, "radius": 5},
            ],
        },
        "kulisse": {
            "welt_neonschild": {"emission_puls": {"hz": 0.8, "min": 0.5, "max": 1.5, "form": "flackern"}},
            "welt_hofleuchte": {"emission_puls": {"hz": 0.25, "min": 0.8, "max": 1.2}},
            "welt_rolltor": {"emission_puls": {"hz": 0.6, "min": 0.3, "max": 1.6, "form": "blinken"}},
            "welt_kastenwagen": {"animation": {"typ": "fahren", "tempo": 2.0, "modus": "einmal", "pause": 8,
                                               "blick_versatz": -90, "route": [[3, 11.35], [-14, 11.35]]}},
        },
    },
    "webseiten": {
        "licht": {
            "himmel": {"oben": "b6cce2", "unten": "cfd8e0"},
            "partikel": [{"typ": "staub", "x": 0, "z": 0, "menge": 10, "radius": 5}],
        },
        "kulisse": {
            "umgebung": {"emission_puls": {"hz": 0.4, "min": 0.8, "max": 1.2}},
            "welt_lieferwagen": {"animation": {"typ": "fahren", "tempo": 2.5, "modus": "hin_und_her",
                                               "route": [{"x": 9.4, "z": 3.9, "warten": 4}, {"x": 9.4, "z": 12},
                                                         {"x": 2, "z": 12, "warten": 4}]}},
        },
    },
    "buero": {
        "licht": {
            "himmel": {"oben": "a9b8c4", "unten": "b9c4cc"},
            "partikel": [
                {"typ": "staub", "x": 0, "z": 0, "menge": 12, "radius": 5},
                {"typ": "voegel", "x": -6, "z": -8, "menge": 3},
            ],
        },
        "kulisse": {
            "welt_lkw": {"animation": {"typ": "fahren", "tempo": 2.5, "modus": "hin_und_her",
                                       "route": [{"x": 4.5, "z": -12.9, "warten": 5}, {"x": 4.5, "z": -6},
                                                 {"x": 10, "z": -6, "warten": 5}]}},
        },
    },
    "produkt": {
        "licht": {
            "himmel": {"oben": "0b0a18", "unten": "1e1b2e", "sterne": 40, "mond": {"x": 0.8, "y": 0.08}},
            "glow": {"intensitaet": 0.5, "staerke": 0.9, "schwelle": 1.0},
            "partikel": [
                {"typ": "dampf", "x": 8, "z": -12, "menge": 12},
                {"typ": "funken", "x": -2, "z": -10, "menge": 14, "intervall": 3},
                {"typ": "motten", "x": 6, "z": -6, "menge": 5},
            ],
        },
        "kulisse": {
            "umgebung": {"emission_puls": {"hz": 0.5, "min": 0.6, "max": 1.3}},
            "welt_luefterwand": {"emission_puls": {"hz": 1.6, "min": 0.3, "max": 2.0, "form": "blinken"}},
        },
    },
    "kapital": {
        "licht": {
            "himmel": {"oben": "8a92bc", "unten": "d9a77c"},
            "glow": {"intensitaet": 0.4, "staerke": 0.8, "schwelle": 1.0},
            "partikel": [
                {"typ": "voegel", "x": -6, "z": -8, "menge": 4},
                {"typ": "staub", "x": 0, "z": 2, "menge": 10},
            ],
        },
        "kulisse": {
            "umgebung": {"emission_puls": {"hz": 0.2, "min": 0.8, "max": 1.2}},
            "welt_kran": {"emission_puls": {"hz": 0.8, "min": 0.2, "max": 1.8, "form": "blinken"}},
            "welt_wolken": {"animation": {"typ": "treiben", "achse": "x", "tempo": 0.5, "weite": 4}},
        },
    },
}


def main() -> None:
    text = open(PFAD, encoding="utf-8", newline="").read()
    crlf = "\r\n" in text
    text = text.replace("\r\n", "\n")
    for welt, d in DATEN.items():
        start = text.index('"id": "%s"' % welt)
        # --- kulisse zuerst (steht hinter licht), damit Positionen davor stabil bleiben
        k0 = text.index('"kulisse": [', start)
        for datei, zusatz in d["kulisse"].items():
            b = text.index('"datei": "%s"' % datei, k0)
            ende = text.index("}", b)
            block = text[b:ende]
            if all(('"%s"' % s) in block for s in zusatz):
                continue
            m = re.search(r'"drehung": [-0-9.]+', block)
            ins = "".join(",\n%s%s%s" % (T * 5, '"%s": ' % s, j(v)) for s, v in zusatz.items())
            pos = b + m.end()
            text = text[:pos] + ins + text[pos:]
        # --- licht
        l0 = text.index('"licht": {', start)
        l1 = text.index("\n" + T * 3 + "},", l0)
        if '"himmel"' not in text[l0:l1]:
            ins = "".join("\n%s%s: %s," % (T * 4, '"%s"' % s, j(v)) for s, v in d["licht"].items())
            pos = l0 + len('"licht": {')
            text = text[:pos] + ins + text[pos:]
    if crlf:
        text = text.replace("\n", "\r\n")
    open(PFAD, "w", encoding="utf-8", newline="").write(text)
    json.loads(open(PFAD, encoding="utf-8").read())
    print("ok")


if __name__ == "__main__":
    sys.exit(main())
