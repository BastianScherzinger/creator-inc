# PC-Testumgebung (`--pc-test`, `--pc-test-live`)

Das Spiel am PC bedienen wie am Handy -- schneller als ueber ADB, ohne Geraet.
Die Befehle werden als echte `InputEventScreenTouch`/`ScreenDrag` eingespeist
(`Input.parse_input_event`), also durch dieselbe Kette wie ein Finger. Godot leitet
Finger 0 zusaetzlich als Maus weiter, deshalb greifen Knoepfe, Sheets und Wisch-Logik.
Nur in Debug-/Editor-Builds aktiv (`OS.is_debug_build()`); im Release macht der Schalter nichts.
Code: `project/tools/pc_test/pc_steuerung.gd`, eingehaengt mit einer Zeile am Ende von `main.gd::_ready`.

## Start

```bash
bash tools/pc_test.sh --frisch                        # Fenster 540x1200, Ordner shots/pc_live
bash tools/pc_test.sh --frisch --welt 6 --tiefe 3     # beliebige Pruefschalter davor
PC_ORDNER=/pfad bash tools/pc_test.sh --frisch        # anderer Ordner
bash tools/pc_cmd.sh "tipp 270 640"                   # Befehl senden, Logzeile kommt zurueck
bash tools/pc_cmd.sh "bild x"                         # gibt den Bildpfad aus
bash tools/pc_cmd.sh ende                             # Spiel beenden
```

PowerShell: `.\tools\pc_test.ps1 --frisch` und `.\tools\pc_test.ps1 -Befehl "tipp 270 640"`.
Unter Git-Bash setzen die Skripte `MSYS_NO_PATHCONV=1` selbst.

Skriptmodus (Datei abarbeiten, dann beenden; Ordner = Ordner der Datei, absoluter Pfad):
`godot_console --path project --resolution 540x1200 -- --frisch --pc-test C:/pfad/befehle.txt`

Live: `befehle.txt` wird alle 200 ms gelesen; nur Zeilen mit Zeilenende zaehlen. Jede Zeile
bekommt in `log.txt` eine Antwort `[t=12.3] #5 tipp 270 640 -> traf: ...` (`#5` = Zeilennummer in `befehle.txt`).
Zeilen mit `#` am Anfang und Leerzeilen werden uebersprungen.

## Befehle

Koordinaten in Bildschirmpixeln des Fensters (540x1200) oder in Prozent (`50%`).

| Befehl | Wirkung |
|---|---|
| `tipp x y` · `doppeltipp x y` · `halten x y ms` | ein Finger; Antwort nennt das Control darunter |
| `wisch x1 y1 x2 y2 ms` | Finger zieht von A nach B (echte Drag-Folge, bildweise) |
| `pinch cx cy faktor ms` | zwei Finger (Index 0/1) waagerecht um die Mitte; Faktor >1 auseinander = hinein, <1 = heraus. Antwort: Zoom vorher / beim Loslassen / kurz danach (Pinch rastet nicht ein, K6 §4.1) |
| `warte s` | echte Sekunden (unabhaengig von `zeitraffer`) |
| `zeitraffer f` | `Engine.time_scale` (0,1 bis 50) |
| `bild name` | Screenshot `<ordner>/name.png` und `name_50.png` (halbe Groesse) |
| `was x y` | oberstes Control, das Eingaben annimmt (Pfad, Klasse, Text, `mouse_filter`), davor ignorierte mit Text; sonst der 3D-Treffer (Station/Zone) |
| `zustand` | Geld, Einkommen/s, Welt, Rang, gekaufte Raeume, offenes Fenster der ModalSchlange, wartende Fenster, offenes Panel, Kamera-Zoom und -Stufe |
| `geld n` | Kapital um n erhoehen |
| `welt n` | auf Welt n vorspulen (nur vorwaerts; fuer eine fruehere Welt mit `--welt n` starten) |
| `messen` | ab jetzt zaehlen: Fenster (ModalSchlange, ohne leichte) und gleichzeitige Textebenen je Bild |
| `bericht` | Ergebnis der Messung: `Fenster=n [art@Spielzeit] MaxTextebenen=n Mehrfach={rand+ort:Bilder} Spielzeit=min Kaeufe=n (je min) Momente=n (je min)`; Kaeufe = Stufen + Ausstattung + Raeume |
| `empfehlung` | bester bezahlbarer Kauf des Kerns und sein Bildschirmpunkt (negativ = ausserhalb des Bildes) |
| `spur an` / `spur aus` | `spiele` nennt danach die ersten Tippziele und die Zahl der Wische (Fehlersuche) |
| `textebenen` | was gerade an Text ueber der Karte steht (`fenster:<art>`, `rand`, `erklaer`, `ort`, `tutorial`) und warum keine Ortsblase kommt |
| `spiele s` | s echte Sekunden selbst spielen: Fenster weitertippen, Kaufknopf im Menue, gruene Plakette, fertiges Ziel, Rand-Tab, Station des besten Kaufs (echte Tipps); am Ende Menues zu. Tippt auch den Tutorial-Ring (Station), holt fertige Ziele im Auftragsbrett, wischt/zoomt, wenn der beste Kauf ausserhalb des Bildes liegt |
| `bild_bei ebene name [max_s]` | spielen wie `spiele`, bis die Textebene (z. B. `ort`) steht, dann Bild |
| `ende` | Spiel beenden |

## Beispiele

Frisch starten, erste Minuten (Eroeffnung ist eine Szene mit Textbox, Antworten muessen angetippt werden):

```
tipp 270 1090        # Textbox: naechste Blase (mehrfach, mit warte 2 dazwischen)
tipp 270 1133        # "Los geht's"
was 328 430          # liegt Pinnwand/Idee-Station unter dem Punkt?
tipp 328 430         # Stationsmenue "Idee" oeffnet
zustand              # Panel=Stationsmenue (Idee)
wisch 270 1050 270 800 400   # Wisch im Menue: es darf nicht schliessen
tipp 488 657         # X schliesst
doppeltipp 400 300   # Ueberblick
```

Welt 6 laden: `bash tools/pc_test.sh --frisch --welt 6 --tiefe 3 --moment aus`

Fenster-Diaet pruefen (K6 1c): `messen`, `zeitraffer 5`, `spiele 60`, `bericht` -- zaehlt Fenster und
gleichzeitige Textebenen der ersten 5 Spielminuten. Offline: `--tiefe 3 --ohne-eroeffnung --offline 7200`.

Pinch: `pinch 270 300 0.4 600` (heraus), `pinch 270 300 2.5 600` (hinein). Die Finger duerfen nicht auf
einem Control mit `mouse_filter=STOP` oder unter einer Szene beginnen -- sonst bekommt die Kamera nichts.
Vorher mit `was` pruefen und `zustand` auf `Fenster=keins`.

## Hinweise

- Ein offenes Fenster (Szene mit Antworten, Moment) verschluckt alles; `zustand` zeigt `Fenster=`.
- `--tiefe N` feuert Momente/Szenen; `--moment aus` unterdrueckt die Popups (siehe `tools/serie.sh`).
- `--frisch` speichert nichts. Ohne `--frisch` wird der Stand des PCs (user://) geladen und gespeichert.
- Der Godot-Ausgabestrom steht in `<ordner>/godot.txt`.
