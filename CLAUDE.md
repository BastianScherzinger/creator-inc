# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt

**Creator Inc: Idle Tycoon** (bis 16.10.2026 „HELLO WORLD“; Ordnername bleibt `cannabisgame`) — mobiler Idle-Management-Tycoon für Android. Seit 17.10.2026 Bastians eigenes Übungsprojekt: freier APK-Download, Quellcode offen (MIT).
Godot 4.7.x, GDScript. Der Aufstieg vom ersten hochgeladenen Clip bis zum
Portfolio, erzählt von Figuren (Mo, Younes, Roman, Selin), über **sechs Welten**
(ADR-022): `zimmer` (Die WG) → `auftrag` (Das Studio) → `webseiten` (Der
Merch-Laden) → `buero` (Das Lager) → `produkt` (Die Farm) → `kapital` (Das
Portfolio). Die IDs sind historisch, der Inhalt steht in den Themen-Dateien.

**Stand:** Alle sechs Welten in Idle-Tycoon-Tiefe (ADR-021/022), Design-System
„Sticker-Pop“ (`game/ui/ui_stil.gd`). Tagesaktueller Stand: `CURRENT_STATE.md`.
Letzte Arbeitsgrundlage und Taskliste: **`docs/NACHT_PLAN.md`** (dazu
`docs/nacht/`: Karten, Ausstattung, IDs je Welt).

## Vor dem Start jeder Session lesen

0. `docs/NACHT_PLAN.md` — Bogen, Karten, Design-System, Taskliste (Muster für die Tiefe: `docs/WELT1_TIEFE.md`)
1. `NEXT_SESSION.md` und `CURRENT_STATE.md` — was genau als Nächstes zu tun ist, wo das Projekt steht
2. `docs/KONZEPT.md` — warum dieses Spiel und nicht ein anderes
3. `docs/WELTEN.md` — der verbindliche Bauplan je Welt
4. `docs/STORY.md` — Figuren, sechs Welten in Nachrichten, Tonregeln
5. `docs/ROADMAP.md` — die Aufgabenliste bis zum Release

Architekturentscheidungen (ADR-001 ff.) stehen in `MASTER_DECISIONS.md` im Wurzelverzeichnis.

## Befehle

```powershell
.\validate.ps1          # Tor vor JEDEM Commit, 7 Schritte: Schichtentrennung → Sperrwörter → Import →
                        # Unit+Integration → Balance-Sim → Android-Debug-Build → keine Ersatzwelt
.\validate.ps1 -SkipBuild   # dasselbe ohne Android-Build (schneller)
.\deploy.ps1            # Build → Installation aufs Handy → Start → gefiltertes Log
.\tools\release_apk.ps1  # Download-APK build\creatorinc.apk (Preset Android APK, Paket com.scherzinger.creatorinc, Debug-Keystore)
.\tools\release_aab.ps1  # Play-Bundle build\creatorinc.aab (Preset Android Release, nur falls später Google Play)
.\tools\check_env.ps1   # Werkzeuge und Versionen prüfen
.\tools\screenshot.ps1  # Screenshot vom Gerät holen — nach jeder sichtbaren Änderung ansehen
.\tools\vorschau.ps1    # PC-Vorschau im Handyformat 540×1200 (Layout-Check ohne ADB)
bash tools/pc_test.sh --frisch   # PC-Testumgebung: Spiel per Befehl bedienen (tipp/wisch/pinch/was/zustand/bild) mit bash tools/pc_cmd.sh "tipp 270 640" — docs/PC_TEST.md

# Einzelnen Test ausführen (immer godot_console, nie godot!)
godot_console --headless --path project -s res://addons/gdUnit4/bin/GdUnitCmdTool.gd --ignoreHeadlessMode -a res://tests/unit/test_cost_curve.gd

# Balance prüfen (Welt 1 bis 100 %, Welten 2–6 je 60 Minuten)
godot_console --headless --path project -s res://tools/balance_sim.gd
godot_console --headless --path project -s res://tools/abschluss_tuning.gd   # Balance-Varianten nebeneinander

# Durchspielprobe im echten Spiel: Welt 1 im Zeitraffer bis zum Weltwechsel (~25 s)
godot_console --path project --resolution 540x1200 -- --frisch --durchspielen
# ... durch alle sechs Welten bis zum Abspann (~3 min)
godot_console --path project --resolution 540x1200 -- --frisch --durchspielen --alle-welten
# Eine Welt einzeln simulieren, mit Zeitpunkten aller Ziele und Nachrichten
godot_console --headless --path project -s res://tools/welt_sim.gd -- kapital

# Vorschaubild mit Prüfschaltern -> shots/serie/<name>.png
bash tools/serie.sh 04_ziele --tiefe 2 --menue ziele
```

Prüfschalter (PC-Kommandozeile oder `user://start_args.txt` auf dem Handy):
`--frisch` (Spielstand ignorieren, nichts speichern) · `--tiefe N` (N Räume + Stufen/Ausstattung
vorspulen) · `--menue <station_id|bereich_id|ziele|handy|ausbau|fortschritt|einstellungen>` ·
`--zoom N` · `--welt N` · `--store` (ohne Tutorial/Debug-Knopf) · `--ohne-eroeffnung` ·
`--mit-tutorial` · `--wechsel` · `--abschluss` · `--reich` · `--durchspielen` · `--alle-welten` · `--bild <name>`

## Architektur in fünf Sätzen

1. **`project/core/`** enthält reines GDScript ohne Nodes — Wirtschaft, Fortschritt, Speicherstand. Headless in Millisekunden testbar.
2. **`project/game/`** enthält alles Sichtbare und stellt ausschließlich dar, was der Core berechnet hat.
3. Kommunikation läuft nur über Event- und Command-Bus; `core/` darf **niemals** etwas aus `game/` importieren.
4. **`project/data/`** enthält alle Werte — JSON für Zahlen und Texte. Kein Wert steht im Code.
   `data/worlds/worlds.json` ist die **einzige** Stelle, die weiß, welche Welten es gibt: Reihenfolge, Raumgröße, Startzoom, Tür- und Fensterpositionen, Ausstattung, Requisiten, Laufwege, Stationspositionen. Eine Welt hinzuzufügen heißt: dort einen Eintrag ergänzen plus `data/themes/<id>/theme.json` und `data/balance/<id>.json`. **Kein Code ändert sich dabei.**
5. **`project/services/`** kapselt Werbung und Käufe hinter Interfaces mit Stub-Implementierungen (`ad_service`, `store_service`; Analytics gibt es noch nicht).

Details: `docs/ARCHITECTURE.md`

## Nicht verhandelbare Regeln

- **D3 / ADR-010:** Kein thematischer Begriff außerhalb von `data/themes/` und `data/i18n/`. Systeme sprechen nur neutrale IDs (`station_intake`, `station_buffer`, `station_processing`). `validate.ps1` erzwingt das mit einer Sperrwortliste und schlägt nachweislich an — auch bei Kommentaren.
- **NPCs erzeugen kein Geld.** Der Core rechnet, NPCs stellen dar. Sonst bricht der Offline-Ertrag.
- **Keine Werte im Code.** Zahlen gehören nach `data/balance/*.json`.
- **Kein Commit bei rotem `validate.ps1`.**
- **Nicht validieren, während parallel jemand Dateien schreibt.** Läuft ein Agent oder ein Generator, kann `validate.ps1` auf einem halb geschriebenen Stand rot werden, obwohl nichts kaputt ist — und der nächste Lauf ist grün. Erst warten, bis alle Schreiber fertig sind, dann prüfen. Ein rotes Tor, dessen Ursache man nicht kennt, ist schlimmer als gar keins.
- **Baugerüste müssen laut sein.** Fehlt einer Welt ein Stationsmodell, ein Raummodul oder die Themendatei, springt eine Ersatzwelt ein — mit `push_warning`. Eine Welt gilt erst als fertig, wenn sie **ohne eine einzige Ersatzwelt-Warnung** startet. Ein Baugerüst, das niemand bemerkt, wird ausgeliefert.
- **Jede sichtbare Änderung endet mit einem angesehenen Screenshot** — Touch-Ziele ≥ 48 dp, Lesbarkeit, Kontrast, Safe Area.
- **`targetSdk = 36`** ist Play-Store-Pflicht, nicht verhandelbar.
- Keine Keystores, Keys oder Tokens im Repository.

## Konventionen

- GDScript streng typisiert: `var x: float = 0.0`, `func f(a: int) -> String:`
- Dateien und Ordner `snake_case`, Klassen `PascalCase`
- Deutsch für Dokumentation und Commit-Nachrichten, Englisch für Bezeichner im Code
- Eine Task aus `ROADMAP.md` = ein Commit
- Neue Ideen wandern nach `docs/BACKLOG.md`, nicht in die laufende Phase

## Fallstricke

- **In Skripten immer `godot_console.exe`, nie `godot.exe`** — Letzteres ist eine GUI-Anwendung, PowerShell wartet nicht darauf und liefert keinen Exit-Code.
- **Nie `$ErrorActionPreference = 'Stop'` zusammen mit `2>&1` auf Godot** — dessen Fortschrittsausgabe geht auf stderr und würde unter PowerShell 5.1 als Fehler gewertet.
- **`sdkmanager` ist deprecated** — SDK-Pakete mit `android sdk install "<paket>"` installieren. Das Tool stürzt beim Beenden ab (Exit `0xC0000409`), obwohl die Installation erfolgreich war: **Erfolg an den Dateien prüfen, nicht am Exit-Code.**
- **GDScript-Lambdas erfassen Werte, keine Referenzen.** `var n: int = 0` plus `func(): n += 1` in einer Lambda erhöht die äußere Variable **nicht**. Für Zähler ein Dictionary oder Array nehmen (Referenztypen).
- **JSON kennt keinen Unterschied zwischen `7` und `7.0`.** Nach `JSON.parse_string` sind alle Zahlen `float`. Wer Typen braucht, muss beim Laden explizit casten — `SaveData.from_dict` macht das.
- **gdUnit4 bricht eine Suite beim ersten Fehler ab.** Die Zusammenfassung meldet dann `n test cases`, wobei `n` nur die *gelaufenen* sind — es sieht aus, als gäbe es die restlichen Tests nicht. Bei überraschend kleiner Testzahl immer den ersten Fehler beheben und neu laufen lassen, nicht nach fehlenden Tests suchen.
- **In gdUnit4 laufen keine SceneTree-Frames.** `SceneTree.create_timer(...)` läuft im Testlauf nie ab, und eine abgekoppelte Coroutine wacht nie wieder auf. Zeitabhängiges deshalb so bauen, dass die Wartezeit auf 0 gesetzt werden kann (siehe `AdServiceStub._warte`) — getestet wird die Entscheidung, nicht die Uhr.
- **`get_tree()` ist null, solange ein Node nicht im Baum hängt.** Dienste dürfen davon nicht abhängen; `Engine.get_main_loop() as SceneTree` funktioniert immer.
- **Konfiguration in `_init()` laden, nicht in `_ready()`.** `_ready()` läuft erst beim Eintritt in den Baum und überschreibt dann Werte, die der Aufrufer direkt nach `add_child()` gesetzt hat.
- **`set_anchors_preset()` behält die Offsets** und rechnet sie auf das *aktuelle* Rechteck um — bei einem frisch erzeugten Control ist das `(0,0,0,0)`, das Element ist damit unsichtbar null Pixel groß. Für Vollflächen `set_anchors_and_offsets_preset()` nehmen.
- **glTF speichert `baseColorFactor` linear, Godot zeigt `albedo_color` in sRGB.** 0,10 im Blender-Skript erscheinen im Spiel als 0,35 Helligkeit. Aus der gewünschten Bildschirmhelligkeit zurückrechnen: `linear = s^2,2`.
- **Godot merkt Änderungen an bereits importierten Assets nicht immer.** Ändern sich Materialfarben trotz `--import` nicht, `project/.godot/imported/` löschen und neu importieren.
- **Die PC-Vorschau muss das Seitenverhältnis des Geräts haben.** `vorschau.ps1` rendert deshalb 540 × 1200, nicht 1080 × 2400 — ein Fenster, das höher ist als der Bildschirm, kappt Windows auf die Bildschirmhöhe, und die Vorschau lief dann breiter als das Handy. Alles, was von *oben* positioniert war, stand auf dem Gerät woanders. Positionen in der unteren Bedienung **von unten** verankern.
- **Logisch ist die Oberfläche 720 breit**, nicht 1080 (`stretch/mode = canvas_items`, Basis 720 × 1280). Feste Pixelwerte wie `540` für „Bildmitte" sind falsch — `get_viewport().get_visible_rect().size` verwenden.
- **Play lehnt Telefon-Screenshots über 2 : 1 ab.** Geräteaufnahmen (1080 × 2400 = 2,22 : 1) sind ungültig; `art_source/icon/store_bilder.py` bringt sie auf 1080 × 2160.
- **Prüfschalter auf dem Handy:** Android hat keine Kommandozeile. Debug-Builds lesen `user://start_args.txt` (per `adb shell run-as … files/start_args.txt`). Danach löschen, sonst startet jede Sitzung in derselben Welt.
- **`min_sdk`/`target_sdk` im Export-Preset leer lassen** — sie sind nur mit Gradle-Build überschreibbar; die Vorlage liefert bereits 36/24.

- **`art_source/` liegt außerhalb von `project/`** — sonst importiert Godot `.blend`-Dateien und bläht das Paket auf.
- **Debug-Builds nur für `arm64-v8a`** — halbiert die Build-Zeit.
- **Fester Simulationstakt 0,25 s**, niemals `delta` direkt in Wirtschaftsrechnungen verwenden — sonst hängt der Ertrag an der Bildrate.
- **Meilenstein-Multiplikatoren sind Pflicht, kein Bonus** (alle 12 Stufen ×1,7). Ohne sie kostet Stufe 100 sieben Tage Wartezeit und das Spiel stirbt nach ~40 Stufen. Der Balance-Simulator prüft das.
- **Balance messen, nicht raten:** Nach jeder Änderung an `data/balance/*.json` läuft `tools/balance_sim.gd` — 60 Spielminuten in 4 Sekunden, mit Zielkurven-Vergleich.

### Seit ADR-021 (Welt 1 in die Tiefe)

- **Variable Schrift: Das OpenType-Tag muss eine Zahl sein.** `variation_opentype = {"wght": 900}` wird stillschweigend ignoriert, und Nunito bleibt ExtraLight. Richtig: `TextServerManager.get_primary_interface().name_to_tag("wght")` als Schlüssel (`UiStil.schrift`).
- **Kein Filmic-Tonemapping bei warmem Umgebungslicht.** Die Karte wurde fast weiß. Das warme Licht steht in `main.gd::_baue_licht` — Änderungen immer mit Vorschaubild prüfen.
- **Backslash-Zeilenfortsetzungen nie über Bash-Heredoc oder `sed` schreiben.** Das Bash-Werkzeug macht aus `\` + Zeilenumbruch ein wörtliches `\n` — in GDScript ein Parse-Fehler, und die Vorschau hängt bis zum Timeout. Solche Stellen mit dem Edit-Werkzeug ändern, oder Python-Skripte per Write-Werkzeug als Datei ablegen.
- **PowerShell `Set-Content -Encoding utf8` schreibt ein BOM.** Für `.gd` und `.json` das Edit-Werkzeug nehmen.
- **Neue `class_name` sind erst nach `--import` bekannt.** Vorher melden Tests „Could not find type“. `godot_console --headless --path project --import` einmal laufen lassen.
- **Wandmodule haben die Innenseite bei lokal +z.** Außenwände vorn brauchen 180°, rechts −90° (`drehung` in `worlds.json`), sonst öffnet die Wohnungstür nach innen.
- **Stationen schaltet der KERN frei**, nicht die Darstellung (`GameCore._aktiviere`). Früher stand das in `main.gd` — der Simulator hat zwei Stationen deshalb nie mitgerechnet.
- **Zwei Kettenglieder gleichauf am Engpass bringen einzeln exakt null.** Ein Simulator, der nur echte Mehreinnahmen zählt, hört dann auf zu kaufen (`AbschlussSim._mehreinkommen`).
- **Vorschauen immer mit `--frisch`.** Sonst trägt jede Vorschau den Stand der vorigen mit (Willkommen-Dialog, fremdes Kapital).
- **Gesperrte Räume: Schleier über `material_overlay`**, nicht über geänderte Materialien. Böden deshalb je Zone als eigenes MultiMesh, Wände gemeinsam.
- **Idle Bank Tycoon auf dem Handy ist der Spielstand des Nutzers.** Nur ansehen, nichts antippen.

### Seit ADR-022 (sechs Welten in Tiefe, Sticker-Pop)

- **Welt-Tiefe hängt nur an Daten:** `zonen` (GrundrissBauer statt RoomBuilder), `stationsmodell: "ausstattung"`, `figuren.modus: "wg"`, `module: "standard"` (Dateinamen `boden_<typ>_a/_b`, `wand_*`, `pfosten_*` aus `docs/NACHT_PLAN.md` §5). Figuren und Sperren werden erst in der eigenen Welt gesucht, dann in `assets/*/gemeinsam/`.
- **Stationsflächen, Türen und Wege je Welt** stehen in `docs/nacht/karten_welten.md`. **Ziel- und Nachrichten-IDs** stehen in `docs/nacht/ids_welten.md`. Texte müssen dieselben IDs tragen.
- **Neue oder geänderte GLB aus Blender sind erst nach `--import` sichtbar.** Vorher meldet das Spiel „Stationsmodell fehlt“, obwohl die Datei da ist.
- **Parallele Vorschauen mit `--bild <name>`.** `tools/serie.sh` macht das jetzt selbst. Sonst überschreiben sich die Läufe gegenseitig `vorschau.png`.
- **Verluste (Welt 6) nur über `EventBus.loss_tick`.** Eine negative Differenz in `money_changed` ist ein Kauf. Sie als Verlust anzuzeigen ergab „−1000 Mrd“.
- **Schild und Ring einer Station** lassen sich über `"schild": {"x","z"}` je Station in `worlds.json` verschieben. `tools/stations_mitte.gd` misst, wie weit ein Modell von seinem Ursprung abweicht.
- **Akzentfarbe, Absenderfarben, Missionsnamen und Bereichssymbole** stehen in `theme.json` (`stil`, `absender_farben`, `ziele.<id>`, `bereiche.<id>.symbol`), nie im Code.
- **Mehrere Agenten teilen sich den Scratchpad.** Hilfsskripte deshalb mit eindeutigem Präfix benennen; Agenten haben sich dort gegenseitig `teil2.py` überschrieben.
- **Blender-Export scheitert sporadisch mit Errno 22,** solange Godot parallel importiert. Die Skripte der Welten 2–6 wiederholen den Export deshalb.
- **Lange Agentenläufe können am Wochenlimit der API abbrechen.** Agenten lassen sich danach per Nachricht an ihrem Stand fortsetzen. Zwischenstände früh committen.
- **Handy-Spielstand zurücksetzen:** `adb shell run-as tech.wvmit.helloworld rm -f files/save.json files/save.backup.json` (vorher `am force-stop`). Paketname seit 1.0.0 `tech.wvmit.helloworld`; die frühere Debug-App `com.scherzinger.helloworld` ist eine eigene App (Bastians alter Spielstand) und wird nicht angefasst.
- **`tools/story/story.py` und `build.py` überschreiben die von Hand polierten `theme.json`/`balance/*.json`** — sie brechen ohne `--erzwingen` ab; nur nach Sicherung erzwingen.
- **`project/android/build/.gdignore` darf nie fehlen** (sonst importiert Godot die Gradle-Vorlage, Gradle bricht ab). Gradle-Erzeugnisse (`build/build`, `libs`, `.gradle`) stehen in `.gitignore`.
