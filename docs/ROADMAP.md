# ROADMAP & TASK-LISTE

**Stand:** 2026-09-11 · **Phasen 0–5 abgeschlossen (TASK 001–025)** · nächste Phase: **6 — Die sechs Welten**

> **Seit ADR-020 gilt ein neuer Bogen.** Das Spiel heißt HELLO WORLD und
> erzählt den Aufstieg vom ersten hochgeladenen Clip bis zur finanziellen
> Unabhängigkeit — sechs Welten statt zwei. Die Phasen 6 bis 12 unten sind
> daraufhin neu aufgelöst. Die Phasen 0 bis 5 stehen unverändert, weil sie
> gelaufen sind wie beschrieben; nur ihr Thema hat sich geändert, und genau
> das war die Wette von ADR-010.

Granularität: Jede Task ist von einem AI-Agenten in einem Durchgang implementier- **und** testbar. Kein Commit, solange `validate.ps1` rot ist.

---

## Phasenübersicht

| Phase | Inhalt | Status | Abnahme |
|---|---|---|---|
| 0 | Recherche | ✅ fertig | `RESEARCH_SUMMARY.md`, `PLAY_COMPLIANCE.md` liegen vor |
| 1 | Architektur | ✅ fertig | 14 ADRs, `ARCHITECTURE.md`, `GAME_DESIGN.md` |
| 2 | Entwicklungsumgebung | ✅ fertig | Werkzeuge laufen, `validate.ps1` grün in 82 s, Build 24–47 s |
| 3 | Core-Prototyp | ✅ fertig | 79 Tests grün, Balance im Zielkorridor, `validate.ps1` in 102 s |
| 4 | First Playable | ✅ fertig | 12-Punkte-Kette auf dem Redmi Note 12 Pro vollständig durchlaufen |
| 5 | Vertical Slice | offen | Frage „Macht das Spaß?" beantwortbar |
| 5 | Vertical Slice | ✅ fertig | Audio, Tutorial, Belohnungsschleife, Laden — 124 Tests grün |
| 6 | Die sechs Welten | ✅ fertig | Alle sechs vollständig, validate.ps1 Stufe 7 grün |
| 7 | Die vier Sondermechaniken | ✅ fertig | Limit, Menschen, Bestand, Schwankung |
| 8 | Rahmen und Abspann | ✅ fertig | Erster Bildschirm, Neuanfang, Ende, App-Symbol |
| 9 | Politur | offen | Performance-Budget, Übergänge, Kleinigkeiten |
| 10 | QA | offen | Gerätematrix, Regressionssuite, Fremdtest |
| 11 | Release-Vorbereitung | offen | AAB signiert, Store-Eintrag, Data Safety |
| 12 | Play-Release | offen | Live |

---

## PHASE 2 — Entwicklungsumgebung

### TASK 001 — Werkzeuge installieren ✅ ERLEDIGT 2026-09-10
**Ziel:** Godot 4.7.2, Android SDK (Platform-Tools + Build-Tools + Platform 36), scrcpy einsatzbereit.
**Warum:** Ohne diese vier ist keine einzige weitere Task ausführbar.
**Abhängigkeiten:** Freigabe des Auftraggebers (Speicherbedarf, siehe `OPEN_QUESTIONS.md` Q1).
**Vorgehen:** Installation ausschließlich über `winget` bzw. offizielle Downloads. Vorhandenes **JDK 17 wiederverwenden** — nicht neu installieren. Speicherplatz vor und nach messen.
**Ergebnis:** `godot --version`, `adb version`, `scrcpy --version` liefern Ausgaben.
**Test:** `tools/check_env.ps1` prüft alle Werkzeuge und meldet Versionen.
**DoD:** Skript grün, Versionen in `CURRENT_STATE.md` eingetragen, Speicherverbrauch dokumentiert.

### TASK 002 — Godot-Projekt anlegen ✅ ERLEDIGT 2026-09-10
**Ziel:** `project/` mit Renderer „Compatibility", Hochformat, `targetSdk 36`, Ordnergerüst aus `ARCHITECTURE.md`.
**Warum:** Fundament. Falsche Projekteinstellungen später zu ändern ist teuer.
**Abhängigkeiten:** TASK 001.
**Ergebnis:** Godot öffnet das Projekt fehlerfrei, `godot --headless --quit` endet mit Code 0.
**Test:** Headless-Import ohne Fehlerausgabe.
**DoD:** Projekt öffnet, Ordner existieren, `.gitignore` greift, Commit.

### TASK 003 — Android-Export einrichten ✅ ERLEDIGT 2026-09-10 (Gerätetest offen)
**Ziel:** Debug-Keystore, Export-Preset, erster APK-Build.
**Warum:** Der Weg aufs Gerät muss vor dem ersten Feature stehen, nicht danach.
**Abhängigkeiten:** TASK 002.
**Ergebnis:** Ein leeres Projekt startet auf dem echten Gerät.
**Test:** `deploy.ps1` baut, installiert, startet, zeigt Logs. Zykluszeit wird gemessen.
**DoD:** App läuft auf dem Handy, scrcpy spiegelt sie auf den Monitor, Dauer in `docs/ANDROID.md` notiert.

### TASK 004 — Testframework und `validate.ps1` ✅ ERLEDIGT 2026-09-10
**Ziel:** gdUnit4 eingebunden (gegen GUT gegengeprüft), Validierungsskript mit allen Stufen.
**Warum:** Ab hier gilt „kein Commit ohne grün".
**Abhängigkeiten:** TASK 002.
**Ergebnis:** `validate.ps1` läuft durch, ein absichtlich fehlerhafter Test bricht es rot.
**DoD:** Beide Fälle nachgewiesen, Laufzeit dokumentiert.
**Ergebnis:** gdUnit4 v6.2.1, 5 Prüfstufen, grün in 82 s (ohne Build 28 s). Rot-Nachweis geführt: ein kaputter Test **und** ein Themenbegriff in `core/` brechen den Lauf mit Exit 1 und nennen Datei bzw. Testnamen. ADR-008 damit von „vorläufig" auf „entschieden".

---

## PHASE 3 — Core-Prototyp (vollständig headless)

### TASK 005 — Verträge und Ereignisbus ✅ ERLEDIGT
`core/contracts/`: Ereignis- und Kommandodefinitionen, `EventBus`, `CommandBus`. **Test:** Kommando ausgelöst → Ereignis empfangen.

### TASK 006 — Wirtschaftsmodell ✅ ERLEDIGT
Geld, Ertragsrate, Kostenformel `basis × 1.16^(n-1)`, Ertrag `basis × n × qualität`. **Test:** Bekannte Stufen ergeben exakt die Werte aus `GAME_DESIGN.md` §5.1.

### TASK 007 — Stationsmodell und Engpassrechnung ✅ ERLEDIGT
Drei Stationen als Kette, `min()`-Durchsatz, `bottleneck_changed`-Ereignis. **Test:** Bei künstlich gedrosselter Produktion meldet das System genau diese Station als Engpass.

### TASK 008 — Simulationstakt und Offline-Ertrag ✅ ERLEDIGT
Fester 0,25-s-Schritt, Nachholrechnung mit 4-Stunden-Obergrenze und Rate 0,5. **Test:** 8 Stunden Abwesenheit liefern exakt den Ertrag von 4 Stunden × 0,5 — und ist unabhängig von der Bildrate.

### TASK 009 — Balance-Daten aus JSON ✅ ERLEDIGT
Alle Zahlen nach `data/balance/`, Validator für fehlende/ungültige Werte. **Test:** Manipulierte JSON bricht mit klarer Fehlermeldung ab.

### TASK 010 — Save-System ✅ ERLEDIGT
Versioniertes JSON, atomares Schreiben, Backup-Slot, Prüfsumme, Migrationsgerüst. **Test:** Speichern→Laden ist identisch; halb geschriebene Datei fällt sauber auf das Backup zurück; Fixture der Version 1 lädt.

### TASK 011 — Fortschritt und Freischaltungen ✅ ERLEDIGT
Meilensteine, Freischaltbedingungen aus Daten. **Test:** Kapitalschwelle löst Freischaltung genau einmal aus.

### TASK 012 — Balance-Simulator ✅ ERLEDIGT
Werkzeug, das 60 Spielminuten headless durchrechnet und die Kurve aus `GAME_DESIGN.md` §5.5 ausgibt. **Warum:** Macht Balancing zur Messung statt zum Bauchgefühl. **DoD:** Ausgabe liegt innerhalb ±25 % der Zielkurve.

---

## PHASE 4 — First Playable

### TASK 013 — Weltszene, Kamera, Eingabe ✅ ERLEDIGT
Orthographische Kamera, Schwenken/Zoomen mit Grenzen, Tap-vs-Drag-Schwelle. **Test:** Auf dem Gerät geprüft, Screenshots beurteilt.

### TASK 014 — Stationsdarstellung mit drei Ausbaustufen ✅ ERLEDIGT
Platzhaltergeometrie, sichtbare Stufenwechsel. **DoD:** Stufenwechsel ist ohne Text erkennbar.

### TASK 015 — HUD-Grundgerüst ✅ ERLEDIGT
Kapital, Ertragsrate, Upgrade-Schaltfläche, Android-Zurück-Taste. **DoD:** Touch-Ziele ≥ 48 dp, per Screenshot nachgemessen.

### TASK 016 — Erster NPC mit Zustandsautomat ✅ ERLEDIGT
Ein Kunde: erscheinen → laufen → warten → bedient werden → gehen. Pooling ab Beginn. **Test:** 100 Zyklen ohne Speicherwachstum.

### TASK 017 — Spielstand-Kreislauf im Spiel ✅ ERLEDIGT
Automatisches Speichern, Laden beim Start, Offline-Bericht. **DoD:** Die 12-Punkte-Kette des First Playable läuft auf dem echten Gerät vollständig durch.

---

## PHASE 5 — Vertical Slice

TASK 018 Art Direction festlegen (Palette, Typografie, Silhouetten) · TASK 019 Blender-Pipeline für einen NPC inkl. Variantenskript · TASK 020 Erste echte Assets für eine Station · TASK 021 UI im finalen Stil · TASK 022 Audio-Grundgerüst · TASK 023 Tutorial (datengetrieben, überspringbar) · TASK 024 Ad-/Store-Stubs mit Belohnungsschleife · TASK 025 Shop sichtbar, leer · **TASK 026 Themen-Entscheidung A/B/C treffen** (siehe `OPEN_QUESTIONS.md` Q2)

**Abnahme Phase 5:** Eine unbeteiligte Person spielt 15 Minuten ohne Erklärung und kann danach sagen, ob es Spaß gemacht hat.

---

## Phasen 6–12

Werden am Ende von Phase 5 in Tasks aufgelöst — vorher wäre die Planung Fiktion, weil die Erkenntnisse aus dem Vertical Slice die Prioritäten verschieben werden.

Grobe Inhalte: Welt 1 vollständig (5 Stationen, Progression, Großabnehmer) · Welt 2 aus derselben Datenstruktur (Beweis für Erweiterbarkeit) · echte SDKs hinter unveränderten Interfaces · Performance-Politur gegen das Budget · Gerätematrix und Regressionssuite · Store-Eintrag, Data Safety, signiertes AAB · Release.


---

# PHASE 6 — Die sechs Welten

Jede Welt braucht vier Dinge: **Raum** (Module + Requisiten), **Stationen**
(5 × 3 Ausbaustufen), **Texte** (`data/themes/<id>/theme.json`) und **Balance**
(`data/balance/<id>.json`). Erst wenn alle vier stehen, ist eine Welt fertig.

Der Bauplan je Welt steht verbindlich in `docs/WELTEN.md`, die Erzählung in
`docs/STORY.md`.

**Reihenfolge — und warum sie so ist:** Nach Welt 1 und Welt 3 ist der Bogen
von „nichts" bis „Beruf" durchgehend spielbar. Das ist die kleinste Fassung,
die man einem Fremden in die Hand geben kann, und sie ist der eigentliche Test
des ganzen Projekts.

### TASK 026 — Welt 1 „Das Zimmer" ✅ ERLEDIGT 2026-09-11
Raum (10 Module), Requisiten (7), Texte vollständig. Offen: eigene
Stationsmodelle, eigene Balance.

### TASK 027 — Weltsystem ✅ ERLEDIGT 2026-09-11
`worlds.json` als einzige Stelle, die die Welten kennt. `WorldData`,
`BalanceData.fuer_welt()`, `GameCore.wechsle_welt()`, Weltwechsel-Bildschirm,
Ersatzwelten mit Warnung für noch nicht gebaute Teile.

### TASK 028 — Stationsmodelle Welt 1 ✅ ERLEDIGT 2026-09-11
15 Module (5 Stationen × 3 Stufen) für `zimmer`. Jede Stufe muss aus der
isometrischen Aufsicht an der Silhouette erkennbar sein.
**DoD:** Keine Ersatzwelt-Warnung mehr beim Start in Welt 1.

### TASK 029 — Balance für alle sechs Welten ✅ ERLEDIGT 2026-09-11
Je Welt eine Datei, Größenordnungen nach `docs/KONZEPT.md`. Der
Balance-Simulator prüft **jede** Welt einzeln.
**DoD:** `balance_sim.gd` gibt sechs Ergebniszeilen aus, alle im Korridor.

### TASK 030 — Welt 3 „Die Webseiten"
Das Herz des Spiels und die längste Welt. Raum 13 × 11, hell, Parkett,
Schreibtisch am Fenster, gerahmte Ausdrucke an der Wand.
Kette: Anfrage → Konzept → Umsetzung → Deployment → Betreuung.
**DoD:** Welt 3 ohne eine einzige Ersatzwelt-Warnung spielbar.

### TASK 031 — Welt 2 „Der erste Auftrag"
Derselbe Raum wie Welt 1, aber verändert: zweiter Monitor, echter Stuhl, die
Umzugskiste ist ein Regal geworden. Wiedererkennung ist die Aussage.

### TASK 032 — Welt 4 „Das Büro"
Erster Raum mit **Innenwand** — der Raumbaukasten braucht dafür ein
Innenwand-Segment und eine Innentür.

### TASK 033 — Welt 5 „Das Produkt"
Loft, viele Bildschirme, eine Karte mit aufleuchtenden Städtenamen.

### TASK 034 — Welt 6 „Der Ausstieg"
Kleinster Raum, stärkste Szene. Sessel, ein Bildschirm, sonst nichts.

### TASK 035 — Figuren je Welt
Welt 1 zeigt **Zuschauer**, nicht Kunden: Silhouetten, die auftauchen, kurz
bleiben und meistens nichts dalassen. Ab Welt 2 Auftraggeber mit Tasche, ab
Welt 4 Angestellte. Die wiederkehrenden Figuren aus `docs/STORY.md` müssen an
der Silhouette erkennbar sein.

---

# PHASE 7 — Die drei Sondermechaniken

Sie sind der Grund, warum sich die Welten unterscheiden statt nur anders
auszusehen. Jede ist ein eigenes System im Kern, headless testbar.

### TASK 036 — Das Limit (Welt 2) ✅ ERLEDIGT 2026-09-11
Eine harte Obergrenze, die durch Ausbau **nicht** verschwindet. Nur ein Umbau
hebt sie. Der einzige Moment im Spiel, in dem Ausbauen nicht hilft.

### TASK 037 — Menschen (Welt 4) ✅ ERLEDIGT 2026-09-11
Eingestellte Personen mit Namen, Stärke und Schwäche. Eine überlastete Person
wird **langsamer** — der einzige Ort, an dem mehr Druck weniger Leistung
bedeutet.

### TASK 038 — Bestand (Welt 5) ✅ ERLEDIGT 2026-09-11
Erlös pro Abonnent statt pro Durchsatz. Der Bestand wächst mit Arbeit und
schrumpft ohne Betreuung. Zum ersten Mal muss man etwas **halten**.

### TASK 039 — Risiko (Welt 6) ✅ ERLEDIGT 2026-09-11
Ein Tick kann negativ sein. Streuung senkt den Ausschlag, nicht den
Mittelwert. **Grenze:** kein echtes Glücksspiel, keine Lootboxen, keine
Anleitung zu echten Investitionen.

---

# PHASE 8 — Rahmen und Abspann

### TASK 040 — Erster Bildschirm ✅ ERLEDIGT 2026-09-11
Erster Start, Fortsetzen, Neuanfang.

### TASK 041 — Neuanfang mit dauerhaften Faktoren ✅ ERLEDIGT 2026-09-11
Nach Welt 6 von vorn — mit Multiplikatoren. Der Raum aus Akt 1 sieht beim
zweiten Mal anders aus.

### TASK 042 — Abspann ✅ ERLEDIGT 2026-09-11
Der letzte Satz lässt offen, ob das Ziel ein gutes war. Dazu der ausdrückliche
Hinweis, dass dies ein Spiel ist und keine Anleitung.

### TASK 043 — App-Symbol und Store-Bilder
Symbol, Feature-Grafik, sechs Screenshots — einer je Welt.

---

# PHASE 8b — Welt 1 in Idle-Tycoon-Tiefe ✅ (2026-09-11, ADR-021)

Eingeschoben vor der Politur: große WG-Karte, Ausstattung, Räume, Ziele,
Nachrichten, Tipp-Momente, neue Bedienung, Welt 1 endet bei 100 %.
**Eigene Taskliste mit TASK 060–088 in `docs/WELT1_TIEFE.md` §12.** Offen
daraus: 082 (Store-Bilder), 086 (Fernseher), 087 (Welt 2 im neuen Look),
088 (Glow). Danach folgen die Welten 2 bis 6 in dieselbe Tiefe.

---

# PHASE 9 — Politur

### TASK 044 — Übergänge zwischen Welten
Der Wechsel darf nicht schneiden. Ausblenden, Aufbau, Einblenden.

### TASK 045 — Performance-Budget je Welt
60 FPS auf dem Redmi in **jeder** Welt, auch in Welt 4 mit zwei Räumen.
Gemessen, nicht geschätzt.

### TASK 046 — Kleinigkeiten
Zahlenformate, Tippziele, Safe Area, Textlängen in allen Meldungen.

---

# PHASE 10 — QA

### TASK 047 — Fremdtest
Eine unbeteiligte Person spielt 30 Minuten ohne Erklärung. Danach: Hat es Spaß
gemacht, und war klar, was zu tun war?

### TASK 048 — Gerätematrix
Mindestens drei Geräte, davon eines mit wenig Arbeitsspeicher.

### TASK 049 — Regressionssuite
Speicherstände aus jeder Welt einfrieren und gegen jede neue Fassung laden.

---

# PHASE 11 — Release-Vorbereitung

### TASK 050 — Play Compliance auf den neuen Bogen prüfen ✅ ERLEDIGT 2026-09-11
`PLAY_COMPLIANCE.md` stammt aus der Behördenzeit. Neu zu prüfen: Welt 6
(Kapital) darf nicht als Finanzberatung oder Glücksspiel gelesen werden.

### TASK 051 — Datenschutzerklärung und Data Safety ✅ ENTWURF 2026-09-11 (drei Felder auszufüllen, URL zu veröffentlichen)
Was die App speichert (nur lokal), was die SDKs später speichern.

### TASK 052 — Signiertes AAB
Keystore außerhalb des Repositories, Signatur über Umgebungsvariablen.

### TASK 053 — Store-Eintrag ✅ ENTWURF 2026-09-11 (docs/STORE_EINTRAG.md)
Titel, Kurzbeschreibung, Beschreibung, Kategorie, Altersfreigabe.

---

# PHASE 12 — Release

### TASK 054 — Interner Test
### TASK 055 — Geschlossener Test
### TASK 056 — Produktion
