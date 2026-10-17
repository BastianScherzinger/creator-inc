# K7 · DURCHSPIELEN — QA-Lauf am PC (Stand a28ef65 + Arbeitsbaum)

**Stand:** 2026-10-16 · Rolle: QA-Lead · Werkzeug: `tools/pc_test.sh` / `pc_cmd.sh` (Fenster 540×1200).
**Bilder:** `shots/k7/<name>.png` (Kopie, `shots/` ist gitignoriert; `shots/pc_live/` wird vom nächsten Lauf überschrieben).
**Tor:** `validate.ps1 -SkipBuild` GRÜN (647 Tests, 0 Fehler, 0 Waisen, Balance im Korridor, 6 Welten ohne Ersatzwelt).
**Nicht committet.** `docs/release/store_eintrag.md` ist im Arbeitsbaum geändert — nicht von diesem Lauf.

Ablauf je Welt: `--frisch` (W1) bzw. `--frisch --welt n --tiefe 2` (W2–6), `zeitraffer 5`, `messen`, 3–5 × `spiele 60`, `bericht`, danach gezielt: Raumplakette → Raum-Panel → VERBESSERN, Reiter Team, ‹ ›, Auftragskarte → Brett → Abholen / Los geht's, Kasse, Boost, Handy, Einstellungen (Ton an/aus), Standort-Pin, Weltabschluss/-wechsel (`--abschluss`), Offline-Karte (`--offline 7200`). Godot-Log: in keinem Lauf `SCRIPT ERROR` oder `push_error`.

---

## 1. Messwerte (`bericht`)

| Welt | Spielzeit | Fenster (Zeitpunkte) | Fenster / 5 min | Käufe / min | Momente / min | nächste Räume |
|---|---|---|---|---|---|---|
| W1 frisch | 25,6 min | moment@225 s, szene@248 s | 2 in min 0–5, danach 0 (Ø 0,4) | 3,0 | 0,7 | Raum 2 (Flur) 3:45 · Raum 3 (Küche) ~26–28 min |
| W1 frisch (1. Lauf, 5 min) | 5,1 min | moment@248 s, szene@270 s | 2 | 2,6 | 1,6 | Raum 2 4:08 |
| W2 tiefe 2 | 15,5 min | szene@14, szene@387, moment@743 | 1,0 | 2,9 | 0,4 | nächster Raum 12,4 min |
| W3 tiefe 2 | 15,6 min | szene@151, moment@623, szene@726, szene@749 | 1,3 | 4,2 | 0,4 | nächster Raum 10,4 min |
| W4 tiefe 2 | 15,7 min | szene@13, moment@186, moment@903 | 1,0 | 2,8 | 0,4 | 3,1 min · 15,1 min |
| W5 tiefe 2 | 15,6 min | szene@13, szene@41, moment@291, szene@314, moment@390 | 1,6 | 2,4 | 0,4 | 4,9 min · 6,5 min |
| W6 tiefe 2 | 14,3 min | szene@4, szene@34, szene@133, moment@168, moment@356 | 1,75 | 2,3 | 0,4 | 2,8 min · 5,9 min |

MaxTextebenen: überall 1, nur W1-Lauf 1: 2 (`ort+tutorial` 7 Bilder — Ortsblase und Tutorialkarte gleichzeitig).
**Vorbehalt:** Die Zahlen kommen vom Autospieler. Er kauft jede grüne Plakette sofort (Raum-Käufe dadurch später als bei einem sparenden Spieler) und tippt keine Lieferkiste gezielt — „Momente/min“ ist eine Untergrenze. W1 Raum 3 bei ~27 min liegt deshalb weit über K6 (10–13 min); `balance_sim` misst den Korridor als eingehalten.

---

## 2. Behoben (Datei · was)

| # | Befund | Bild | Datei | Änderung |
|---|---|---|---|---|
| 1 | **Tutorial „upload“:** Ring wurde am Rand festgehalten und stand auf „Schnitt“ — Spieler tippt falsch | `r4` | `game/ui/tutorial_view.gd`, `game/main.gd` | Liegt das Ziel außerhalb des freien Bereichs (unter Kopfleiste/Aufträgen, über Karte/Menü), steht statt Ring ein **Randpfeil** (Aufkleber, atmet, Spitze zum Ziel, Tippziel ≥ 104 px). Tipp darauf → Kamera schiebt einmal sanft (0,6 s, ohne Zoom) zum Ziel (`_auf_tutorial_rand_pfeil`). Ring-Klemmung entfernt. Nachweis `u6` (Pfeil) → Tipp → Upload getippt, Tutorial durch |
| 2 | Nach dem Tutorial kamen **zwei Szenen hintereinander**, die erste veraltet („Tipp auf die Pinnwand …“ nach dem Flur-Kauf) | `r5`, `u7` | `game/ui/hud.gd` `_spiele_szenen_nach_tutorial` | nur die neueste Szene (wie die dokumentierte P1.7-Regel); ältere stehen im Handy |
| 3 | Raum-Panel: **Reiter Team** öffnete mit der Rollhöhe der Ausbau-Liste (erste Karte halb weg) | `a4` | `game/ui/raum_panel.gd` | Liste springt bei Reiter- und Raumwechsel nach oben |
| 4 | Raum-Panel **‹ ›**: Panelhöhe sprang je Raum, Pfeile/X wanderten — der nächste Tipp auf › traf die Karte und schloss das Panel | `a5`, `w4_p2` | `game/ui/raum_panel.gd` | beim Blättern bleibt die Kartenhöhe mindestens wie zuvor (`_hoehe_halten`); Nachweis: 4 × › auf derselben Stelle, Panel bleibt (`w4_r4`) |
| 5 | Raum-Panel zeigte in einem Raum ohne Käufe die **Kacheln des vorigen Raums** („Hier ist alles ausgebaut“ + kaufbare Kacheln) | `w4_p2` | `game/ui/raum_panel.gd` | Signatur-Rücksetzwert `SIG_NEU` statt `""` (leere Liste hat Signatur `""`) |
| 6 | **Werbeangebot „▶ Nochmal +5.342 €“** lag nach „Abholen“ mitten auf der Liste des Auftragsbretts | `a7` | `game/ui/hud.gd` `_zeige_angebot` | steht über dem offenen Sheet (`ad1`) |
| 7 | Laufende **Ertragszahl** („+2.568“) stand auf Kopf und X des offenen Bretts/Panels | `w2_brett` | `game/ui/hud.gd` `_auf_geld`, `zeige_clip_ertrag` | entfällt, wenn die Station unter einem offenen Menü liegt (`_unter_menue`) |
| 8 | **Kapitelzeile** in dunklen Welten unlesbar (graue Tinte auf Nachtblau) | `w2_start` | `game/ui/kapitel_view.gd` | heller Konturrand (Papier); lesbar auf hell und dunkel (`w4_s`, `w5_m3`) |
| 9 | Auftragskarte: **„Ausstattungsstuf-en“** mitten im Wort gebrochen | `w3_vor` | `game/ui/hud.gd` `_passe_kartenschrift` | Schrift wird bis GR_KLEIN−3 (≈ 11 px in der 540er-Vorschau) kleiner, bis das längste Wort passt (`w4_q`) |
| 10 | **Weltabschluss und Szene gleichzeitig** (zwei Fenster, zwei Textquellen) | `ww1` | `game/main.gd`, `game/ui/modal_schlange.gd` | Abschluss läuft über die Modal-Schlange (neue Art `abschluss`, nach `offline`, ohne Abstand) und bleibt „offen“, bis der Weltwechsel angenommen ist; wartende Szenen der alten Welt werden dann verworfen. Durchspielprobe zeigt weiter direkt. Nachweis: `Fenster=abschluss Wartend=[szene×3]` → Wechsel `ww3` → Welt 2 |
| 11 | PC-Autospieler (nur Werkzeug) | — | `tools/pc_test/pc_steuerung.gd` | tippt den Randpfeil; drückt den bezahlbaren Umbau (W2 „Archiv bauen“ — vorher stand W2 15 min bei 250 €/s); schließt ein offenes Menü, wenn eine Szene darauf wartet (vorher 60 s Stillstand); tippt in der Abholpause nicht mehr die Zielleiste (vorher 1 min Brett auf/zu ohne Kauf in W3) |

---

## 3. Befunde je Welt (offen = nicht behoben)

### Welt 1 — Die WG (frisch, mit Tutorial)
- Tutorial läuft durch, Randpfeil siehe #1. Eröffnung, Tutorialkarte, Plakette, VERBESSERN (3 × getippt, 3 Käufe, nichts verschluckt), Team, Brett/Abholen, Kasse (+645 €), Handy, Einstellungen (Ton an/aus/an hält), Standortkarte, Fortschritt, Ziele: alle reagieren.
- **Offen:** Raumkauf Küche bringt Raum-Moment **und** Tobi-Szene mit drei Blasen (`a0`) — K6 §3.2 „keine Szene beim Raumkauf“. Daten (`szene: true` an Bereichs-Nachrichten).
- **Offen:** Kassenstapel „×8“ halb unter der Plakette „Das Zimmer“ (`a0`); Ertragszahl „+80“ über der Plakette „Tonstudio im Bad“ (`a1`) — kosmetisch.
- **Offen:** Unten stehen **Ausbau, Ziele, Boost, Handy, Fortschritt** (`a1`) — K6 §4.5 streicht Fortschritt und Ziele (→ Aufträge). Außerdem Brett (über Karten) und Ziele-Menü (Knopf) doppelt (`b5`).

### Welt 2 — Das Studio
- Speicher-Mechanik: Ohne „Archiv bauen“ bleibt das Einkommen stehen; Knopf ist sichtbar und funktioniert. (Autospieler kannte ihn nicht — behoben #11.)
- **Offen (Entscheidung):** „Los geht's!“ bei „3 Momente antippen“ öffnet das Stationsmenü **Schnitt** (`w2_los`) — der Auftrag hat keinen Ort, die Rückfallregel nimmt den Engpass. Ein Test (`test_ziel_ort_zeigt_immer_auf_station_oder_raum`) legt das fest. **Empfehlung:** für `momente` Brett schließen und Kiste/Moment pulsieren lassen; Test dann bewusst anpassen.
- **Offen:** Tagesaufgabe „HEUTE Kaufe 5 Stufen … Holen“ als **dritte Leiste** oben (`w2_m3`) — K6 §4.6 „zwei Leisten, nie drei“.

### Welt 3 — Der Merch-Laden
- Entscheidungsszene (zwei Antworten) korrekt; Abholen im Brett funktioniert, Karten rücken nach.
- **Offen:** Plakette „Der Merch-Laden **+0,0 €/s** 2,1 Mio“ — die Empfehlung im Raum ist ein Kauf ohne Mehrertrag (Station nicht Engpass). **Empfehlung:** ohne Mehrertrag „Engpass: …“ statt „+0,0 €/s“ oder Engpass-Kauf vorschlagen.
- **Offen:** zwei Szenen 23 s auseinander nach einem Raumkauf (szene@726/749).

### Welt 4 — Das Lager
- #4/#5 hier gefunden und behoben.
- **Offen:** reiner Bonusraum (Pausenraum, „Alles ×1,06“) zeigt nach dem Kauf „0 €/s · 0 % ausgebaut“ + „Hier ist alles ausgebaut.“ (`w4_r4`). **Empfehlung:** Kopfzeile „Alles ×1,06“ statt €/s und %.
- **Offen:** Bei `zoom_max` 75 ist das Gelände nicht ganz im Bild (`w4_m3`); Autospieler wischt ~32×/min, weil der beste Kauf oft außerhalb liegt. Kamera-Grenzen/zoom_max in `worlds.json` prüfen.

### Welt 5 — Die Farm
- Kapitelzeile jetzt lesbar (#8).
- **Offen:** zwei Szenen in den ersten 41 s (szene@13/41), Raum-Moment + Szene 23 s später (291/314). Viel Leerfläche unter dem Gelände bei maximalem Zoom (`w5_m3`).

### Welt 6 — Das Portfolio
- **Offen:** drei Szenen in 133 s (szene@4/34/133) — K6 §2.4 „höchstens 3 Szenen je Welt“ wird mit `--tiefe 2` in zwei Minuten verbraucht (vorgespulte Auslöser). Am frischen Weltstart nachmessen.

### Welt-übergreifend
- **Weltwechsel:** Abschluss → „Das Studio · Los“ → Welt 2 läuft (`ww3`). Fix #10.
- **Offline-Karte** (`off1`): Betrag, Balken „2 Std von 4 Std“, Einsammeln funktionieren. Der ▶×2-Knopf erscheint mit `--frisch` nicht (Werbe-Startschutz 300 s Spielzeit, `ads.json erst_ab`) — mit echtem Spielstand prüfen. Der Kontostand oben enthält den Betrag schon, bevor man „Einsammeln“ tippt.
- **Standortkarte** (`b3`, `w3_karte`): Titel „Deine Standorte“ steht ohne Fläche auf der obersten Karte. **Empfehlung:** Titel auf eine Leiste/Verlauf legen.
- **Momente/min 0,4–0,7** (Ziel K6 ≥ 2 in min 1–10) — mit Vorbehalt oben; Lieferkiste/Kasse kommen selten.
- Kein Befund: Geld-/Zahlenformat (Tsd/Mio/Mrd, Komma) überall richtig; keine leeren Zustände außer #5; keine Kamerafahrt ohne Finger außer der dokumentierten Panel-Schiebung (K6 1c).

---

## 4. Für Bastian (Entscheidungen, nicht umgesetzt)

1. Szenen bei Raumkäufen streichen (K6 §3.2) — betrifft `szene: true` an `bereich`-Auslösern in `balance/*.json`.
2. Fortschritt-Knopf und Ziele-Menü streichen bzw. in Aufträge falten (K6 §4.5); Tagesaufgabe nicht als dritte Leiste (K6 §4.6).
3. „Los geht's“ bei Moment-Aufträgen (siehe W2).
4. Bonusraum-Kopfzeile (siehe W4), „+0,0 €/s“-Empfehlung (siehe W3).
5. zoom_max/Kamera-Grenzen W4–W6.
