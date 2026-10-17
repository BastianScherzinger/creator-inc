# K3 · PLAN — „Eine Bühne, ein Pfeil, ein Grund zu bleiben“

**Stand:** 2026-10-15 · Commit 11d8b89 · Rolle: Lead Game Designer (Fable) · Auftraggeber: Bastian (Handy-Urteil, verbindlich)
**Grundlagen:** `K2_NEUKONZEPT.md` (Wellen 1–3 umgesetzt), `P6_PACING.md`, `K3_RECHERCHE_IDLE.md` (30 Maßnahmen), `K3_BEFUND_SPIELTEST.md` (Belege `shots/k3_test/`).
**Regeln, die weiter gelten:** D3/ADR-010 (Themenbegriffe nur in `data/themes/` und `data/i18n/`), keine Werte im Code, Kern rechnet, Darstellung zeigt, kein Commit bei rotem `validate.ps1`, jede sichtbare Änderung endet mit einem angesehenen Screenshot.
**Maßeinheiten:** Oberfläche logisch 720 px breit ≈ 360 dp → **48 dp = 96 logische px**; in der 540er-Vorschau 72 px. (`kartenmarker.gd` rechnet heute mit 88 — wird auf 96 angehoben.)

---

## 1. Leitbild und Designprinzipien

### Leitbild in fünf Sätzen

1. HELLO WORLD ist ein Idle-Tycoon, bei dem man auf einen Blick sieht, **was** man aufbaut, **wo** man tippen muss und **was** es bringt.
2. Die Karte ist eine **Bühne** aus wenigen großen Formen, keine Puppenstube aus Kleinteilen: große Platten, dicke Wände, ein Schild je Ding.
3. Alle 10–15 Minuten passiert etwas Großes mit Namen (Raum, Crew, Auftrag, Rang), und dazwischen gibt es in der Welt immer etwas zu tippen.
4. Mo erzählt eine Geschichte, bei der man weiterbauen will, weil jeder gekaufte Raum die Welt sichtbar verändert und ein nächstes Versprechen zeigt.
5. Werbung ist ein Geschenk mit Preisschild: Man sieht vorher, was man bekommt, es lohnt sich spürbar, und ohne sie kommt man genauso durch.

### Hinweis-Vokabular — ein Symbol je Bedeutung, fester Ort

| Symbol | Bedeutung | Fester Ort | Zustände |
|---|---|---|---|
| **Pfeil ⬆ grün** | Ausbau dieser Station ist bezahlbar und bringt mehr | rechts oben am Stationsschild | grau mit Fortschrittsring = noch nicht bezahlbar (Ring = gespart/Preis) |
| **Pfeil ⬆ groß, pulsend** | *der eine* beste Kauf (`GameCore.empfehlung()`) | genau eine Station | nie zwei gleichzeitig |
| **Werkzeug 🔧 + Name** | beste Wahl ist eine Ausstattung („Notizen · 1.281“) | statt des Pfeils an derselben Stelle | Preis = Menüpreis, immer |
| **Blitz rot** | Engpass, diese Station bremst | am Stationsschild links + roter Plattenrand | ersetzt die rote Karte oben |
| **Raum-Plakette** | Name des Raums + „⬆ n“ (n bezahlbare Käufe im Raum) | Raummitte, nur wenn Raummitte im Bild | gesperrt: 🔒 + Preis + Sparbalken; ab 80 % Puls; bezahlbar: Limette pulsend |
| **Silhouette** | das kommt hier (neue Station) | im gesperrten Raum, volle Größe, dunkel | — |
| **Kiste (wackelt)** | Lieferung zum Tippen | vor der Eingangstür / im Flur | verschwindet nach 20 s |
| **„!“ über Figur** | Mini-Aufgabe | über dem Kopf von Mo/Mira/Tobi usw. | — |
| **▶ + Gegenwert** | Werbung | immer im Knopf („▶ ×2 · 30 Min“), nie allein | grau in Sperrzeit |
| **Pfeil-Tab am Rand** | nächster kaufbarer Raum liegt außerhalb | nur linker/rechter Bildrand | nie in der Bildmitte |

### Weitere Prinzipien

- **Zoom-Lesbarkeit:** Im *Überblick* nur Raum-Plaketten und Silhouetten; im *Raum* nur Stationsschilder, Pfeile, Ausstattung. Je Zoomstufe **eine** Art Schild.
- **Oben höchstens zwei Leisten** (Kopfleiste + Zielleiste). Engpass-Karte und Speicherleiste wandern in Schild bzw. Zielleiste.
- **Ein Modal zur Zeit** (Offline → Geschenk → Szene → Moment).
- **Deko ≤ 5 Teile je Raum**, an der Wand, entsättigt, niedriger als Stationen. Stationen sind die größten und kräftigsten Objekte im Raum.
- **Tippfläche ≥ 96 logische px** für alles Tippbare, Hitbox getrennt von der Grafik.
- **Juice-Stufen:** klein (Zahl), mittel (Funken), groß (Münzregen + Haptik) nur für Raum, Stern, Rang, Auftrag.
- **Kern rechnet:** Pfeil, Plakettenzahl, Sparbalken kommen aus `GameCore` (`empfehlung()`, `bereich_info()`), die Darstellung zeigt nur.

---

## 2. Arbeitspakete in Wellen

Besetzung je Welle: **3 Schreiber parallel**. Je Datei genau ein Besitzer je Welle. `validate.ps1` läuft nur, wenn niemand schreibt. Scratchpad-Präfix `k3_<paket>_`. Vorschauen immer `bash tools/serie.sh k3<paket>_<name> …` (setzt `--frisch`). Handy: `.\deploy.ps1`, Prüfschalter über `user://start_args.txt`, Bild mit `.\tools\screenshot.ps1` nach `shots/k3_handy/<paket>_<name>.png`.

### Welle A — sofort sichtbar am Handy

#### A1 · Bühne: Karte aufräumen

- **Ziel:** H1, H2, M2 aus dem Befund: Flächen statt Kleinteile, Stationen dominieren, gesperrte Räume klar dunkler.
- **Dateien (exklusiv):**
  - `project/game/world/grundriss_bauer.gd`: `_baue_boden` → **eine Bodenplatte je Zone** (ein Mesh mit 3-cm-Fase, Farbe aus Modultyp) statt Schachbrett `(ix+iz)%2`; `_baue_waende` → **durchgehende Blöcke** je Wandabschnitt zwischen Türen (Dicke 0,35 m, eine Deckfarbe), keine Pfosten; `_baue_sperre`/`_baue_umriss` → Strichel, Kartons, Absperrband weg, stattdessen **Stations-Silhouette** (Mesh der kommenden Station, dunkles Unshaded-Material) auf gestrichelter Platte; `_schleier_auf` → Schleier auf ≈ 55 % Helligkeit. Variante `karte=a` (heute) bleibt bis zur A/B-Entscheidung hinter `Experimente.variante("karte")` erhalten.
  - `project/game/world/stationsplatte.gd`: `setze_sterne` → Knöpfe und Wimpel streichen; Stufe über Randfarbe (Akzent → Silber ab 3 → Gold ab 5) und Plattengröße (+10 % ab 3 Sternen); Platte +25 % Grundgröße.
  - `art_source/scripts/build_einrichtung_*.py` (6 Welten): Deko je Zone auf ≤ 5 Teile, an die Wand, entsättigt; `moebel_bericht()` bricht bei > 5 je Zone laut ab. `project/assets/world/**` (Export, dann `--import`).
  - neu `project/tests/unit/test_grundriss_buehne.gd`.
- **Abnahme (Screenshot):** `serie.sh k3a1_ueberblick --store --zoom 22` und `--tiefe 2 --zoom 22` neben `k3_26`/`k3_08`: keine Fugen, keine Pfosten, keine Strichel, keine Kartons; gesperrter Raum messbar dunkler (≤ 60 % Helligkeit des gekauften Nachbarraums); WG-Zimmer ≤ 5 Deko; Stationen sind die größten Objekte; Start ohne Ersatzwelt-Warnung in allen sechs Welten.
- **Tests:** `test_grundriss_buehne` (eine Boden-Instanz je Zone, null Pfosten-Instanzen, Silhouette je gesperrtem Bereich), `test_tippflaechen`, `test_alle_welten_tiefe` grün.
- **Risiko:** Blender-Export Errno 22 bei parallelem Import (Skripte wiederholen); Look verliert „bewohnt“ → drei kräftige Deko-Blöcke je Raum, nicht null.

#### A2 · Raum-Plaketten, Nächstes-Upgrade-Pfeil, Klickziele ≥ 48 dp

- **Ziel:** H3, H5, M1, M3, M4, N1, N2, N4: Man sieht sofort, wo es etwas zu tun gibt und was es bringt.
- **Dateien (exklusiv):**
  - `project/game/ui/kartenmarker.gd`: `_waehle_beste` (:599, dupliziert `game_core.gd::empfehlung()` :1412) **streichen**, stattdessen `kern.empfehlung()` bei `money_changed` (Hysterese `data/ui/hinweise.json → pfeil_haltezeit_s: 2`); `_baue_badge`/`_aktualisiere_badge` → Pfeil-Zustand (grün / grau+Ring / groß+Puls / Werkzeug), Blitz statt Warndreieck, Sterne erst ab Lv 10, **kein Stiel** (Schild flach an der Plattenvorderkante, sonst ausblenden statt verschieben); `_baue_kaufchip` → Chip ≥ 96 × 96 logische px, Preis = `empfehlung().preis`; `_baue_schild` → **Raum-Plakette** in Raummitte (Name / „⬆ n“ bzw. 🔒 Preis + Sparbalken aus `bereich_info()`), nur sichtbar wenn Raummitte im Bild; `_klemme_an_rand` → nur Pfeil-Tab am linken/rechten Rand; LOD nach Zoom (`lod_grenze_zoom: 18`); `_tippflaeche` Mindestmaß 96.
  - `project/game/ui/hud.gd`: Engpass-Pille streichen; Marken-Toast nach 3 s ausblenden (N4); `oben_frei` neu messen; Szene/Moment an `ModalSchlange` anmelden (Schnittstelle aus A3).
  - `project/game/ui/stationsmenue.gd`: Kaufknopf „1.454 · +0,4 €/s“, Held-Zeile nur €/s, Einheiten/Min klein (N1).
  - `project/game/ui/menues.gd`: Fortschritt-Titel = `welt_ziel` (N2). `project/core/game_core.gd` nur `bereich_info()`: zusätzlich `kaeufe_bezahlbar: int`, `naechster_preis: float`, `anteil_gespart: float`.
  - neu `project/data/ui/hinweise.json` (Haltezeit, LOD-Grenze, Mindestmaß, Pulsfrequenz).
  - Tests: `test_tippflaechen.gd` (+ jede Plakette/Chip ≥ 96), neu `test_kartenmarker_pfeil.gd` (Zustände aus `empfehlung()`, Chip-Preis == Menüpreis, nie zwei pulsende Pfeile).
- **Abnahme (Screenshot):** `serie.sh k3a2_t2 --store --tiefe 2 --zoom 22` und `--zoom 12`: im Überblick nur Plaketten, im Raum nur Schilder; genau ein pulsender Pfeil; keine rote Karte oben; kein Stiel; Richtungs-Tab nur am Rand; `k3_09`-Fehler (1.281 vs. 1.454) weg. Handy: Tipp auf Plakette öffnet Raum-Panel, Tipp auf Pfeil kauft bzw. öffnet Station.
- **Risiko:** Plaketten überlappen in kleinen Welten (W2/W3) → `_entzerre` beibehalten; Pfeil springt zu oft → Hysterese.

#### A3 · Zoom-Stufen, Pinch-Hinweis, Modal-Warteschlange, `--ab`-Schalter

- **Ziel:** M6, M7, N8; A/B-Grundlage für Abschnitt 3.
- **Dateien (exklusiv):**
  - `project/game/world/world_camera.gd`: zwei Raststufen `raum`/`ueberblick` aus `worlds.json → karte.zoom_stufen`; neu `springe_stufe(stufe: StringName)`; Pinch rastet beim Loslassen auf die nähere Stufe (stufenlos während der Geste); **Doppeltipp auf Boden ohne Treffer** wechselt die Stufe; `InputEventMagnifyGesture` für Trackpad.
  - `project/data/worlds/worlds.json` nur `karte`: `zoom_min/zoom_max` auf 10–26 (W2/W3 `zoom_max` so, dass die ganze Karte passt), `zoom_stufen {raum, ueberblick}`, `start` = Überblick aller gekauften Räume plus nächster.
  - neu `project/game/ui/modal_schlange.gd`: `anmelden(art: StringName, zeigen: Callable)`, Reihenfolge `offline → geschenk → szene → moment`, `naechstes()` nach `fertig`-Signal; `project/game/main.gd`: `_zeige_offline_bericht` (:1477) und Tagesgeschenk über die Schlange; nach dem ersten Raumkauf Kamera auf Überblick + einmalige Mo-Blase; `--tiefe` setzt `--store` mit (N8); `--ab karte=b,pfeil=a` parsen.
  - `project/core/data/experimente.gd`: `override` wird `Dictionary` je Schirm (`--ab schirm=variante,…`), `--variante a|b` bleibt als globaler Rückfall; `project/data/experimente.json`: neue Schirme `karte`, `plakette`, `pfeil`, `zoom`, `boost`.
  - `data/themes/*/theme.json` nur `tutorial.zoom` („Mit zwei Fingern ziehst du die Karte groß und klein.“, ≤ 90 Zeichen), `data/i18n/de.json` (Knopf „Ganze Karte“).
  - Tests: `test_raumkarte.gd` (Stufen im Zoombereich, Startzoom zeigt gekaufte Räume + nächsten), neu `test_modal_schlange.gd`, `test_kern_overhaul.gd` (`--ab` je Schirm).
- **Abnahme (Screenshot):** `--tiefe 3 --offline`: genau ein Modal (k3_36-Fehler weg); `--ab karte=a` vs. `--ab karte=b` liefern verschiedene Bilder; Handy: Doppeltipp wechselt Stufe, Pinch rastet, nach Flur-Kauf erscheint die Zoom-Blase genau einmal.
- **Risiko:** Pinch ist am PC nicht prüfbar → Handy Pflicht; Doppeltipp darf keinen Kauf auslösen → nur auf Boden ohne Treffer.

### Welle B — Tempo-Loch und Welt-Aufgaben (nach Welle A)

#### B1 · Pacing: Raumkurve glätten, Lückenprüfung

- **Ziel:** H4: kein Raumabstand > 15 min, kein Endspurt in 10 Minuten.
- **Dateien (exklusiv):** `project/data/balance/*.json`: `bereiche.bereich_4.kosten` ≈ ×0,3, `bereich_5.kosten` ≈ ×2–3 (jeder Schritt ≈ ×10); neu `bereiche.bereich_6` („Raum 3b“, Deko-Zone wird Bonusraum, Preis zwischen Raum 3 und 4; W3 ohne Deko-Zone → nur Missionskette); `crew.*.frei` so, dass die erste Crew vor Raum 4 kommt; Ziele `ziel_auftrag_1..3` mit `kette: "auftrag"` zwischen Raum 3 und 4; `momente.abstand_min/max` 90/150, neu `momente.stapel_schub_sekunden: 30`. `data/worlds/worlds.json` nur `zonen[].bereich` für Raum 6. `tools/abschluss_sim.gd`: größte Lücke zwischen Raumkäufen (`raum_luecke_max: 900`), Endspurt (`raum5_bis_ende_min: 480`), Einkommenssprung Raum 4 → Ende ≤ ×100; `tools/balance_sim.gd` gibt die drei Werte aus. `tests/unit/test_balance_data.gd`. neu `docs/neu/K3_PACING.md`.
- **Abnahme:** `welt_sim` für alle sechs: größte Raumlücke ≤ 15 min, Raum 5 → Abschluss ≥ 8 min, Korridor aus P6 grün, Einstieg unverändert (erstes Upgrade < 10 s, Raum 2 < 4 min); Durchspielprobe `--alle-welten` ohne Absturz.

#### B2 · Lieferkiste und Clip-Stapel tippen

- **Ziel:** M9: in der Welt gibt es alle 1,5–2,5 Minuten etwas Großes zum Tippen.
- **Dateien (exklusiv):** neu `game/world/lieferkiste.gd` (3D-Kiste vor der Tür, wackelt, 20 s), `game/world/clip_fluss.gd` (Stapel ab 4 Clips tippbar), `game/ui/kartenmarker.gd` (Kiste-Marker ≥ 96 px), `core/simulation/moment_system.gd` (Arten `&"kiste"`/`&"stapel"`), `core/game_core.gd` nur `tippe_stapel(station_id) -> float` und `_momente_kandidaten`. Tests: `test_tipp.gd`, neu `test_moment_system.gd`.
- **Abnahme:** Kiste ≥ 72 px sichtbar (Vorschau), Tipp → Moment-Belohnung mit Münzflug; Stapel am Engpass antippbar.

#### B3 · Story und Welt-Aufgaben

- **Ziel:** Story trägt über das Loch; man hat einen Grund, den nächsten Raum zu wollen.
- **Dateien (exklusiv):** `data/themes/<welt>/theme.json` (alle Blöcke außer `tutorial.zoom`): neu `auftraege` (3 Mini-Aufgaben je Welt: Figur, Satz ≤ 90 Zeichen, Dank-Satz; IDs `ziel_auftrag_1..3`), zwei Szenen im Loch (`nachricht_23`, `nachricht_24`), `bereiche.bereich_6`, `momente.kiste`; `game/world/e_lebendig.gd` („!“ über der Figur, Tipp → Szene → `springe_zu_ziel`), `game/ui/szene_view.gd` (Antwortchip startet Auftrag), `docs/STORY.md`, `docs/nacht/ids_welten.md`.
- **Abnahme:** zwischen Raum 3 und 4 mindestens 2 Szenen und 3 Zielabschlüsse; Sperrwort-Prüfung grün; jede Nachricht allein verständlich.
- **Risiko:** „!“ nur, wenn kein Pfeil pulst.

### Welle C — Werbung, die sich lohnt (parallel zu B möglich)

#### C1 · Platzierungen und Dauer-Boost

- **Dateien (exklusiv):** `data/services/ads.json`: `schub` → Sperre 0, `hoechstzahl_pro_sitzung` 8; neu `raum_sofort` (ab `anteil_gespart ≥ 0,7`, Rest geschenkt, 1 je Raum), `ziel_doppelt` (Sperre 600 s), `kiste` (ohne Werbung 1 min Einkommen, mit ▶ 15 min), `geschenk_doppelt`, `crew_ziehen` (1/Tag); global `mindestabstand_sekunden: 180`, `hoechstzahl_pro_tag: 10`, `erst_ab: {spielzeit_s: 300, bereich: bereich_1}`, `offline_verdoppeln.faktor: 3`. `data/balance/*.json` nur `schub`: Dauer 1800 s, stapelbar bis 14400 s. `services/ad_service_stub.gd` (globales Limit, Startschutz, Tageszähler im Save). `game/ui/menueleiste.gd` (Boost-Knopf dauerhaft, „▶ ×2 · 30 Min“), `hud.gd`, `menues.gd` (Raum-Panel `raum_sofort`), `offline_view.gd` (▶ ×3), `geschenk_view.gd` (▶ ×2). `data/i18n/de.json` nur `werbung_*`. Tests: `test_belohnungsschub.gd`, neu `test_ad_limits.gd`.
- **Abnahme:** Boost-Knopf mit Gegenwert lesbar; „Rest geschenkt ▶“ nur ab 70 %; Offline ▶ ×3; vor Minute 5 nirgends ein ▶.
- **Risiko:** Zu starker Boost entwertet Käufe → mit `welt_sim --mit-boost` messen (Korridor darf um ≤ 20 % sinken).

#### C2 · Einwilligung (UMP) und AdMob vorbereiten

- `services/ad_service_admob.gd` (initialize → UMP → erst dann laden), Android-Plugin, `export_presets.cfg`, `docs/release/ADMOB.md` (Schritte für Florins Konto, Data-Safety, Datenschutz). `ads.json → anbieter` bleibt `"stub"` bis zur Freigabe. Kein Keystore/Token im Repo; Play-Policy vorher klären.

#### C3 · Lokale Messung und A/B-Auswertung

- neu `services/messung_service.gd` (lokal `user://messung.json`, kein Netz, kein Personenbezug; Ereignisse `start`, `erster_tipp`, `tipp_leer`, `tipp_station`, `tipp_plakette`, `kauf`, `raum`, `moment`, `angebot_*`, `sitzung_ende`), Hooks in `game/main.gd`, neu `tools/messung_bericht.py`, neu `docs/neu/K3_AB_BEWERTUNG.md`, Debug-Knopf „Messdaten kopieren“.

### Reihenfolge

```
Welle A (parallel):  A1 | A2 | A3   → validate → Handy-Test → A/B-Urteil Karte/Plakette/Pfeil/Zoom
Welle B (parallel):  B1 | B2 | B3   → welt_sim alle Welten → Handy-Test Loch
Welle C (parallel):  C1 | C2 | C3   → Handy-Test Werbung (Stub) → A/B boost
```

Verlierer-Varianten werden nach dem Urteil aus dem Code gestrichen.

---

## 3. A/B-Plan

`--ab karte=a|b,plakette=a|b,pfeil=a|b,zoom=a|b,boost=a|b` — PC-Kommandozeile oder `user://start_args.txt`.

| Schirm | a | b | Hypothese |
|---|---|---|---|
| `karte` | heute: Kacheln, Modulwände, Strichel | Bühne (A1) | b wirkt ruhiger, Stationen werden schneller gefunden |
| `plakette` | Stationsschilder immer, ein Kaufchip | Raum-Plaketten im Überblick, Schilder im Raum | b beantwortet „wo verbessern?“ in < 2 s |
| `pfeil` | nur der beste Kauf hat einen Pfeil | alle bezahlbaren grün, bester groß und pulsend | b erhöht Käufe/min, ohne Rauschen |
| `zoom` | freier Pinch 10–26 + Knopf „Ganze Karte“ | zwei Raststufen + Doppeltipp | b hat weniger Fehltipps |
| `boost` | Boost im Menü wie heute | Dauerknopf mit Gegenwert | b verdoppelt Antipp-Rate |

**Beurteilung durch die KI:** je Variante PC-Vorschau (auch auf 50 % verkleinert) und zwei Handy-Sitzungen à 5 Minuten (`--frisch`, Tipps per `adb shell input tap` nach festem Protokoll), Messdatei per `adb pull`. Raster 0–2 Punkte, Gewinner ab 7/10, Ergebnis in `K3_AB_BEWERTUNG.md`:

| Kriterium | Messung | Ziel |
|---|---|---|
| K1 Zeit bis zum ersten richtigen Tipp | `erster_tipp − start`; Elemente scannen bis Pfeil | ≤ 3 s, ≤ 3 Elemente |
| K2 Fehltipps | `tipp_leer` / alle Tipps | ≤ 10 % |
| K3 Lesbarkeit in 1 s | 50-%-Bild: Pfeil, Plakette, Preis erkennbar | 0 Textelemente < 11 px |
| K4 Dopamin-Momente pro Minute | Juice-Ereignisse je Minute | Min. 1–10 ≥ 2/min, danach ≥ 0,5/min, nie > 3 min ohne |
| K5 Ruhe | gleichzeitig sichtbare Hinweise im Überblick | ≤ 6; Leisten oben ≤ 2 |

Qualitativ: „Weiß ich nach 10 s, was ich aufbaue, wo ich tippe, was es bringt?“

**Erst mit echten Spielern messbar:** D1/D3/D7-Retention, Opt-in- und Abschlussquote Werbung, Sitzungslänge, eCPM → geschlossener Play-Test, Tester senden ihre lokale Messdatei. Unter ~200 Spielern je Gruppe zählen nur K1–K4.

---

## 4. Pacing-Ziele

**Welt-Längen aus P6 bleiben** (Sim. 75–80 / 70–80 / 80–90 / 90–100 / 100–110 / 110–120 min). Das Loch war nie die Länge, sondern die Verteilung.

| Regel | Wert (Sim.) | Prüfung |
|---|---|---|
| Größte Lücke zwischen zwei Raumkäufen | ≤ 15 min | `abschluss_sim.gd → raum_luecke_max` |
| Größte Lücke zwischen zwei Großereignissen | ≤ 12 min | `welt_sim` Ereignisliste |
| Endspurt Raum 5 → Abschluss | ≥ 8 min; Einkommen Raum 4 → Ende ≤ ×100 | `abschluss_sim.gd` |
| Erste 10-Minuten-Sitzung | ≥ 2 Räume, ≥ 1 Rang, ≥ 4 Käufe/min | Einstieg wie bisher |

Zielzeiten Welt 1: Raum 1 3:35 · Raum 2 ~8 · Raum 3 ~20 · Raum 3b ~32 · Raum 4 ~45 · Raum 5 ~60 · Abschluss 75–80. Hebel nur in Daten, keine Formeländerung in `cost_curve.gd`.

---

## 5. Was wir bewusst NICHT tun

- Keine Interstitials, keine Banner, keine Zwangswerbung; nichts vor Minute 5 / vor Raum 1.
- Kein freier Zoom 7–34, keine Variante C „Fokusraum“ — erst wenn der Handy-Test zeigt, dass A + B nicht reichen.
- Keine Online-Telemetrie, kein Firebase, kein Netz in 1.0.
- Keine neuen Welten, keine Events/Live-Ops, kein Reset-Prestige, keine Hartwährung/IAP-Kopplung in dieser Runde.
- Keine Formeländerung im Kern. Neu im Kern nur `tippe_stapel`, Moment-Arten, `bereich_info`-Felder.
- Kein Neubau der Stationsmodelle, keine neue Schrift, kein neues Design-System. Sticker-Pop bleibt.
- Keine Texte außerhalb von `data/themes` und `data/i18n`, keine Zahlen im Code, kein `validate.ps1` während Agenten schreiben, kein Commit durch Agenten.
