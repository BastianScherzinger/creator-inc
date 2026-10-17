# TECHNISCHE ARCHITEKTUR

**Stand:** 2026-09-10 · Engine: Godot 4.7.x · Sprache: GDScript (streng typisiert)

---

## 1. Grundprinzip: Zwei Welten, eine Richtung

```
        EINGABE
           │
           ▼
   ┌───────────────┐   Kommandos    ┌──────────────────┐
   │  PRÄSENTATION │ ─────────────► │  SIMULATION CORE │
   │   (game/)     │                │     (core/)      │
   │  Nodes,Szenen │ ◄───────────── │  reines GDScript │
   │  UI, NPCs     │    Ereignisse  │  KEINE Nodes     │
   └───────────────┘                └──────────────────┘
        sichtbar                        deterministisch
     nicht testbar                 headless testbar (ms)
```

**Die eine Regel, die alles trägt:** `core/` darf nichts aus `game/` importieren — niemals. Kein `Node`, kein `Sprite3D`, kein `get_tree()`, kein `await`. Ein Verstoß wird vom Lint-Schritt in `validate.ps1` erkannt und bricht den Build.

**Warum das entscheidend ist:** Der gesamte Wirtschaftskern lässt sich damit in Millisekunden ohne Fenster testen. Ein Balancing-Durchlauf über 60 simulierte Spielminuten dauert Bruchteile einer Sekunde statt 60 Minuten. Für ein agentengetriebenes Projekt ist das der Unterschied zwischen „ich vermute, das ist ausgewogen" und „ich habe es 1.000-mal durchgerechnet".

---

## 2. Projektstruktur

```
cannabisgame/
├── CLAUDE.md                   Einstieg für jede künftige Session
├── MASTER_PLAN.md              Vollständige Spezifikation
├── MASTER_DECISIONS.md         Alle ADRs
├── CURRENT_STATE.md            Was existiert, was läuft
├── NEXT_SESSION.md             Startpunkt des nächsten Laufs
├── OPEN_QUESTIONS.md           Offene Entscheidungen
├── KNOWN_RISKS.md              Risikomatrix
├── validate.ps1                DER Prüfbefehl vor jedem Commit
├── deploy.ps1                  Build → Handy → Log, ein Schritt
│
├── docs/                       Fachdokumentation
│
├── project/                    ► GODOT-PROJEKT (project.godot)
│   ├── core/                   ◄ KEINE Godot-Nodes, rein logisch
│   │   ├── economy/            Geld, Ertrag, Durchsatz, Engpassrechnung
│   │   ├── progression/        Stufen, Freischaltungen, Meilensteine
│   │   ├── stations/           Stationsmodelle, Upgrade-Regeln
│   │   ├── simulation/         Zeitschritt, Offline-Ertrag, Aufträge
│   │   ├── save/               Serialisierung, Versionierung, Migration
│   │   └── contracts/          Event- und Kommandodefinitionen
│   │
│   ├── game/                   ◄ Alles Sichtbare
│   │   ├── world/              Weltszenen, Kamera, Wegpunkte
│   │   ├── stations/           Stationsvisualisierung, Ausbaustufen
│   │   ├── npc/                NPC-Szene, Zustandsautomat, Pool
│   │   ├── ui/                 HUD, Menüs, Shop, Tutorial
│   │   └── fx/                 Partikel, Zahlen-Popups, Übergänge
│   │
│   ├── services/               ◄ Außenwelt, immer als Interface
│   │   ├── ad_service.gd       abstrakt + Stub + (später) AdMob
│   │   ├── store_service.gd    abstrakt + Stub + (später) Billing
│   │   ├── analytics.gd        abstrakt + Stub
│   │   └── platform.gd         Android-Besonderheiten, Back-Button
│   │
│   ├── data/                   ◄ Alle Werte, kein Code
│   │   ├── stations/*.tres     Struktur & Asset-Referenzen
│   │   ├── npcs/*.tres         NPC-Typdefinitionen
│   │   ├── worlds/*.tres       Weltlayouts, Wegpunkte
│   │   ├── balance/*.json      Kosten, Erträge, Timer
│   │   ├── themes/<name>/      ◄ D3: NUR hier stehen Themenbegriffe
│   │   └── i18n/*.json         de.json, en.json
│   │
│   ├── assets/                 Exportierte Game-Assets (.glb, .png, .ogg)
│   └── tests/                  gdUnit4: unit/, integration/, fixtures/
│
├── art_source/                 ◄ NICHT im Export: .blend, Skripte
│   ├── characters/
│   ├── props/
│   └── scripts/                Blender-Python-Automatisierung
│
└── tools/                      Build-, Validierungs-, Screenshot-Skripte
```

**Warum `art_source/` außerhalb von `project/` liegt:** Godot importiert alles unterhalb des Projektordners. `.blend`-Dateien haben in der App nichts zu suchen — sie würden Importzeit und Paketgröße aufblähen.

---

## 3. Kernsysteme

### 3.1 Simulation Core

| Modul | Verantwortung | Ausdrücklich nicht |
|---|---|---|
| `Economy` | Geld, Ertragsraten, Durchsatz, `min()`-Engpass | Weiß nichts über Anzeige |
| `StationModel` | Stufe, Kosten, Kapazität, Ertrag pro Station | Kennt keine Meshes |
| `Progression` | Freischaltungen, Meilensteine, Weltfortschritt | Kennt keine Szenen |
| `SimClock` | Fester Zeitschritt (**0,25 s**), Offline-Nachholrechnung | Kein `_process()` |
| `OrderSystem` | Großabnehmer-Aufträge, Timer, Bonus | Keine Benachrichtigungs-API |
| `SaveModel` | Zustand ↔ Wörterbuch, `schema_version` | Kein Dateizugriff |

**Fester Zeitschritt (0,25 s):** Die Simulation läuft in gleichmäßigen Schritten, unabhängig von der Bildrate. Auf einem 30-fps- und einem 120-fps-Gerät kommt exakt dasselbe Ergebnis heraus. Das ist die Grundlage für reproduzierbare Tests und für Offline-Ertrag, der sich nicht von der Framerate beeinflussen lässt.

### 3.2 Ereignisfluss

```gdscript
# Präsentation → Core (Kommando)
CommandBus.dispatch(UpgradeStationCommand.new("station_sales"))

# Core → Präsentation (Ereignis)
EventBus.station_upgraded.emit("station_sales", 4)
EventBus.money_changed.emit(1250.0, +75.0)
EventBus.bottleneck_changed.emit("station_storage")
```

Alle Ereignistypen sind in `core/contracts/` deklariert. Die Präsentation abonniert; der Core sendet und weiß nie, wer zuhört.

### 3.3 NPC-System (ADR-007)

```
        ┌──────────────────── Pool (vorinstanziiert) ────────────┐
        │                                                        │
   [SPAWNING] ──► [WALKING] ──► [WORKING] ──► [RETURNING] ──► [DESPAWN]
                      │                                           │
                      └──────── A* über Wegpunkt-Graph ───────────┘
```

- **Pooling:** feste Anzahl vorinstanziierter NPCs, Wiederverwendung statt Instanziierung — vermeidet Ruckler durch Speicherzuweisung
- **Gestaffelte Aktualisierung:** NPCs verteilen sich auf 4 Gruppen, pro Frame wird eine Gruppe aktualisiert → ein Viertel der Last
- **Obergrenze:** 24 sichtbare NPCs (Startwert, in Phase 5 am Gerät zu prüfen)
- **Bewegung:** Interpolation entlang des Pfads, kein Physiksystem, keine Kollisionsabfragen
- **Verbindlich:** NPCs erzeugen **kein** Geld. Sie stellen dar, was der Core bereits berechnet hat.

### 3.4 Kamera & Eingabe (ADR-003)

- Orthographische Kamera in fester Isometrie-Neigung
- Ein-Finger-Ziehen = Schwenken (mit Trägheit), Zwei-Finger = Zoom
- **Tap-vs-Drag-Schwelle:** unter 12 px Bewegung und unter 200 ms = Tap, sonst Ziehen
- Schwenkgrenzen an die Weltausdehnung gekoppelt — die Karte kann nie verloren gehen
- Auswahl über Raycast auf eine dedizierte Kollisionsebene, nicht über sichtbare Geometrie
- UI liegt in einem separaten `CanvasLayer`; Eingaben in der UI erreichen die Welt nie
- Touch-Ziele mindestens **48 dp**; Safe-Area für Notches wird respektiert

### 3.5 Save-System (ADR-006)

```
speichern:  Modell → Wörterbuch → JSON → save.tmp → fsync → rename → save.json
                                                   └► vorherige Datei → save.backup.json

laden:      save.json → Prüfsumme ok? ──ja──► Version prüfen → Migrationskette → Modell
                              │
                              └──nein──► save.backup.json versuchen
                                              │
                                              └── beides defekt → Neustart mit Meldung
```

Migrationen liegen als `migrate_v1_to_v2()` einzeln vor und werden **jede für sich** getestet, mit einer eingefrorenen Fixture-Datei pro Version in `tests/fixtures/saves/`.

### 3.6 Theme-Schicht (ADR-010, Guardrail D3)

```gdscript
# ✗ VERBOTEN — thematischer Begriff im System
if station.name == "Cannabis-Anbau":

# ✓ RICHTIG — neutrale ID, Anzeigename aus dem Theme
if station.id == "station_production":
    label.text = Theme.display_name("station_production")
```

`validate.ps1` durchsucht `core/`, `game/` und `services/` nach einer Sperrwortliste. Ein Treffer außerhalb von `data/themes/` bricht den Build. Damit ist D3 nicht eine Absichtserklärung, sondern eine mechanisch erzwungene Eigenschaft.

---

## 4. Performance-Budget

| Größe | Ziel | Grenzwert | Messung |
|---|---|---|---|
| Bildrate | 60 fps | nie unter 30 | Godot-Monitor + `adb shell dumpsys gfxinfo` |
| Draw Calls | < 150 | 250 | Godot-Debugger |
| Dreiecke sichtbar | < 120k | 200k | Godot-Debugger |
| Texturspeicher | < 96 MB | 128 MB | Godot-Monitor |
| RAM gesamt | < 350 MB | 450 MB | `adb shell dumpsys meminfo` |
| AAB-Größe | < 60 MB | 100 MB | Build-Ausgabe |
| Start bis erster Frame | < 2 s | 4 s | manuelle Messung |
| Sichtbare NPCs | 24 | 40 | Debug-Overlay |

**Referenzgerät als Untergrenze:** Ein Mittelklasse-Android von etwa 2020 mit 4 GB RAM. `[ANNAHME — anzupassen, sobald das reale Testgerät bekannt ist]`

**Eingebauter Wächter:** Die Entwicklungsmaschine hat eine Intel UHD 620. Was dort einbricht, bricht auf Low-End-Android erst recht ein.

---

## 5. Sicherheit

| Bereich | Maßnahme |
|---|---|
| Save-Manipulation | Prüfsumme erkennt Beschädigung. Manipulation wird **nicht** verhindert — bei Offline-Einzelspieler wäre das Aufwand ohne Nutzen (ADR-006) |
| Kaufvalidierung | Clientseitige Prüfung des Billing-Ergebnisses; serverseitige Validierung erst bei nennenswertem Umsatz (dokumentierter Grenzfall) |
| Berechtigungen | Nur das Nötigste. `AD_ID` erst, wenn Werbung tatsächlich integriert wird — und dann im Data-Safety-Formular deklariert |
| Signing-Keys | Keystore ausschließlich außerhalb des Repositories, Pfad über Umgebungsvariable, Sicherungskopie offline. **Ein verlorener Upload-Key kostet die App** |
| Secrets | `.gitignore` deckt `*.keystore`, `*.jks`, `export_credentials.cfg`, `.env` ab |
| Debug-Werkzeuge | Debug-Overlay und Cheats werden über `OS.is_debug_build()` kompiliert und sind im Release nicht erreichbar |

---

## 6. Fehlerbehandlung & Diagnose

- `Log.gd` mit Stufen (debug/info/warn/error); im Release nur ab `warn`
- Jeder Systemfehler nennt System, Datei und wiederherstellbaren Zustand
- Kein stiller Fehlschlag: Ein fehlendes Datenfeld bricht im Debug hart ab und wird im Release protokolliert plus Standardwert
- Debug-Overlay (nur Debug-Build): Bildrate, Speicher, NPC-Anzahl, aktueller Engpass, Kapital, Zeitraffer ×1/×10/×100, Geld-Cheat
