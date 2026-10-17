# K3 · A/B-Bewertung (Vorlage)

**Zweck:** Pro Variante (Schirme `karte`, `plakette`, `pfeil`, `zoom`, `boost`) belegen, welche gewinnt. Quelle: lokale Messdatei (`MessungService`, kein Netz, kein Personenbezug) plus Bilder. Plan: `K3_PLAN.md` Abschnitt 3.

## 1. Raster (0–2 Punkte je Kriterium, Gewinner ab 7/10)

| Kriterium | Messung | Ziel | 0 | 1 | 2 |
|---|---|---|---|---|---|
| K1 Zeit bis zum ersten richtigen Tipp | `messung_bericht.py`: „erster sinnvoller Tipp“ | ≤ 3 s, ≤ 3 Elemente | > 8 s | 3–8 s | ≤ 3 s |
| K2 Fehltipps | Leertippanteil | ≤ 10 % | > 25 % | 10–25 % | ≤ 10 % |
| K3 Lesbarkeit in 1 s | 50-%-Bild: Pfeil, Plakette, Preis erkennbar | 0 Textelemente < 11 px | > 2 | 1–2 | 0 |
| K4 Dopamin-Momente/Min | „Juice pro Minute“ (Raum + Moment + Angebot genommen) | Min. 1–10 ≥ 2/min, danach ≥ 0,5/min, nie > 3 min ohne | Pause > 180 s | Pause ≤ 180 s, Rate knapp | Rate und Pause erfüllt |
| K5 Ruhe | Bild: gleichzeitig sichtbare Hinweise im Überblick | ≤ 6; Leisten oben ≤ 2 | > 9 | 7–9 | ≤ 6 |

K1, K2, K4 liefert der Bericht, K3 und K5 kommen aus Bildern (`tools/screenshot.ps1`, auf 50 % verkleinert). Zusätzlich qualitativ: „Weiß ich nach 10 s, was ich aufbaue, wo ich tippe, was es bringt?“

Zusatzkennzahlen im Bericht: Leertipps/Min, Käufe/Min, Zeit bis Raum 2/3, Angebote gezeigt/genommen/abgelehnt.

## 2. Ereignisse der Messdatei

`start` (mit `ab` = aktive Varianten und `args`), `erster_tipp`, `tipp_leer`, `tipp_station`, `tipp_plakette`, `kauf`, `raum`, `moment`, `angebot_gezeigt`, `angebot_genommen`, `angebot_abgelehnt`, `sitzung_ende`. Jedes mit `t` (Sekunden seit Start), `w` (Welt), optional `d`. Grenzen (Ringpuffer) in `project/data/services/messung.json`. Datei: `user://messung.json`.

## 3. Ablauf der Handyrunde

Je Variante **zwei Sitzungen à 5 Minuten**, immer `--frisch` (kein Spielstand), Tipps nach festem Protokoll (siehe 3.3). Ein Schirm wird geprüft, alle anderen bleiben auf ihrem Standard (`data/experimente.json → aktiv`).

### 3.1 Reihenfolge (ein Schirm je Runde, B/A abwechselnd gegen Positionseffekt)

| Lauf | start_args | 
|---|---|
| 1 | `--frisch --ab karte=a` |
| 2 | `--frisch --ab karte=b` |
| 3 | `--frisch --ab karte=b` |
| 4 | `--frisch --ab karte=a` |

Danach dasselbe für `plakette`, `pfeil`, `zoom` (`boost` erst nach Welle C1). Ein Lauf = eine Sitzung (App vorher mit `am force-stop` beenden).

### 3.2 Befehle (Handy per ADB, Debug-Build, Paket `tech.wvmit.helloworld`)

```powershell
adb shell am force-stop tech.wvmit.helloworld
adb shell run-as tech.wvmit.helloworld rm -f files/save.json files/save.backup.json files/start_args.txt
# Varianten setzen (Debug-Builds lesen user://start_args.txt):
adb shell "run-as tech.wvmit.helloworld sh -c 'echo --frisch --ab karte=b > files/start_args.txt'"
adb shell monkey -p tech.wvmit.helloworld 1        # App starten
# ... 5 Minuten nach Protokoll tippen ...
adb shell am force-stop tech.wvmit.helloworld      # schreibt sitzung_ende nicht immer: Home-Taste vorher druecken
adb shell run-as tech.wvmit.helloworld cat files/messung.json > messung.json
python tools/messung_bericht.py messung.json
```

Alternativ im Spiel (Debug-Build): Knopf „Messdaten kopieren“ links über „+Geld“ legt das JSON in die Zwischenablage.
`start_args.txt` danach löschen, sonst startet jede Sitzung mit denselben Schaltern. Die Messdatei sammelt sich über Läufe (bis 12 Sitzungen); zum Trennen vorher `adb shell run-as tech.wvmit.helloworld rm -f files/messung.json`.

### 3.3 Tipp-Protokoll (immer gleich)

1. Nichts tippen, bis das Bild steht (Zeit läuft ab App-Start).
2. Dann so, wie ein neuer Spieler es täte: den zuerst auffälligen Hinweis tippen, kaufen, wiederholen; ein Moment/Geschenk, das erscheint, wird getippt.
3. Fünf Minuten, dann Home-Taste.
4. Pro Lauf zwei Bilder (Überblick, Raum), später auf 50 % verkleinert für K3/K5.

## 4. Auswertung

```powershell
python tools/messung_bericht.py messung.json --je karte        # nur ein Schirm gruppiert
python tools/messung_bericht.py messung.json --nur karte=b     # nur diese Sitzungen
python tools/messung_bericht.py messung.json --json > k3_messung.json
```

Unter ~200 Spielern je Gruppe zählen nur K1–K4; Retention, Werbe-Opt-in und eCPM sind erst mit einem geschlossenen Play-Test messbar (Tester senden ihre lokale Messdatei).

## 5. Ergebnis Handyrunde 16.10.2026 (Claude, Redmi Note 12 Pro, Build bfcedea)

**Einschränkung:** Gespielt hat die KI per `adb input tap` mit Bild nach jedem Schritt. K1-Zeiten (29–53 s) messen die Bedenkzeit der KI, nicht das Spiel, und zählen nicht. Bewertet wurden Bilder (K3/K5), Treffer der Tipps (K2) und die Spiel-Taktung (K4). Karte lief als natürlicher Neustart (Eröffnung + Tutorial bis Raum 2, je 5 min); Plakette, Pfeil und Zoom mit `--tiefe 2 --ohne-eroeffnung` (keine Messung, nur Bilder). Bilder: `shots/k3_ab/`.

| Schirm | Variante | Befund | Urteil |
|---|---|---|---|
| karte | a | Raum voll Möbel, Teppich, Bett; Stationen gehen darin unter. Leertipps 20 % (2 von 10). | – |
| karte | b | Stationsplatten klar, Raum ruhig, 0 % Leertipps (0 von 4). Wirkt etwas leer. | **b gewinnt** |
| plakette | a | Überblick mit ~11 Elementen (4 Stationsblasen, 3 Pfeile, Texte „Alles ×1,15 · Tobi wohnt …“), überlappend. | – |
| plakette | b | 7 Raumplaketten, lesbar, kaum Überlappung. | **b gewinnt** |
| pfeil | a | Im Raum kein einziger Hinweis sichtbar, obwohl alles bezahlbar ist (bester Kauf liegt außerhalb). | – |
| pfeil | b | Grüne Pfeile an jeder bezahlbaren Station, man sieht sofort, wo es weitergeht. | **b gewinnt** |
| zoom | a | Knopf „Ganze Karte“ liegt über dem Raum-Panel und verdeckt dort einen Kaufknopf. Antippen einer Raumplakette zoomt + öffnet Raumliste (gut). | – |
| zoom | b | Doppeltipp ohne verdeckende Knöpfe; Hinweisblase einmalig. Pinch nicht prüfbar (adb kann kein Zwei-Finger). | **b gewinnt** |
| boost | a/b | Nicht prüfbar: der Boost-Platz erscheint erst ab Rang 3 (`erfolge.json`), in 5 min nicht erreicht. | offen |

**K4 Dopamin-Takt (aus der Messdatei, beide Karten-Läufe):** 0,4–0,6 Momente/Min in den ersten 5 Minuten, Ziel ≥ 2. Längste Pause 147 s (Ziel ≤ 180 erfüllt). → Der Einstieg ist zu textlastig und zu arm an Belohnungen; das ist der größte Hebel.

**Weitere Befunde (Handy):**
1. Überblick: Plaketten überlappen (Flur unter Küche, Tonstudio), Karte nimmt nur das untere Drittel ein, oben leerer Himmel.
2. Raum-Zoom zentriert auf die Tippstelle, nicht auf den Raum: Stationen am Rand, Mitte leerer Boden.
3. Geldanzeige rundet auf: „200 €“ sichtbar, Kaufknopf grau, Hinweis „Noch 0,8 €“.
4. Zielleiste überdeckt die zweite Zeile der Fortschrittsbox („Als Nächstes: …“).
5. Tutorial-Hand zeigt auf das Ziel-Geschenk (+40), bevor das Ziel erreicht ist.
6. Nach `--tiefe` kommen 10+ Fenster hintereinander (Nachrichten, Kauf, Stern) – Testartefakt, aber auch nach langer Offline-Zeit denkbar → ModalSchlange bündeln.

**Gewinner:** karte b, plakette b, pfeil b, zoom b (= bisheriger Standard in `data/experimente.json`). Verliererzweige werden gestrichen, sobald Bastian zugestimmt hat. Boost wird nach Rang 3 nachgeprüft.

## 6. Ergebnistabelle (Raster)

| Schirm | Variante | Sitzungen | K1 (s) | K1 Pkt | K2 (%) | K2 Pkt | K3 Pkt | K4 /Min | K4 Pkt | K5 Pkt | Summe /10 | Urteil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| karte | a | | | | | | | | | | | |
| karte | b | | | | | | | | | | | |
| plakette | a | | | | | | | | | | | |
| plakette | b | | | | | | | | | | | |
| pfeil | a | | | | | | | | | | | |
| pfeil | b | | | | | | | | | | | |
| zoom | a | | | | | | | | | | | |
| zoom | b | | | | | | | | | | | |
| boost | a | | | | | | | | | | | |
| boost | b | | | | | | | | | | | |

**Qualitatives Urteil je Schirm:** _(offen)_

**Gewinner → `data/experimente.json → aktiv` setzen, Verlierer aus dem Code streichen.**
