# Store-Bilder — Werkzeug (Screenshots kommen am Ende)

Ablauf, wenn die Pakete A–E fertig sind:
1. Auf dem Handy mit Release-nahem Stand (`--store --frisch --tiefe N --welt N --menue …` in `user://start_args.txt`, danach löschen).
2. Rohaufnahme je Motiv mit `.\tools\screenshot.ps1` → als `shots/store_roh_<nr>_<name>.png` ablegen.
3. `python art_source/icon/store_bilder.py` → 1080 × 2160 nach `docs/store_bilder/<nr>_<name>.png`.
4. `python art_source/icon/store_bilder.py --pruefen` → prüft Anzahl (2–8), Seitenverhältnis ≤ 2:1, Größe ≤ 8 MB, Feature 1024 × 500, Icon 512 × 512 und baut `docs/store_bilder/_kontaktbogen.png` zum Ansehen.

Empfohlene Reihenfolge (7 Bilder): 1 Eröffnungs-Chat · 2 Welt 1 Zimmer mit Panel · 3 Welt 2 Studio · 4 Welt 3 Merch-Laden · 5 Welt 4 oder 5 · 6 Welt 6 Portfolio · 7 Tagesgeschenk/Offline-Karte.
Regeln: keine Debug-Knöpfe, kein Preis-/„Gratis“-Text, keine Geld-Versprechen, keine fremden Marken.
Feature-Grafik: `art_source/icon/feature.svg` (Text über `feature_text.py`), Icon `project/assets/icon/icon_512.png`.
Die alten Bilder in `docs/store_bilder/` stammen vom alten Stand und werden ersetzt.

## Stand 15.10.2026 (neues Design, Q1)
Neue Bilder: `docs/release/store/q1_*.png` (8 Screenshots + Feature-Grafik). Erzeugt mit `tools/serie.sh`-Aufnahmen (PC, 720 × 1590, Fenster auf Bildschirmhöhe gekappt)
und `python art_source/icon/q1_store_compose.py <Rohordner>`: auf 1080 × 2160 hochskaliert (~1,13×) mit Schlagzeile und Farbfläche je Welt.
Für schärfere Bilder besser vom Handy aufnehmen (siehe oben). Beim Aufnehmen waren Story-Banner und Szenen per Projektkopie ausgeblendet.
