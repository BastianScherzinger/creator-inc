# K3 · BEFUND SPIELTEST — „Karte zu kleinteilig, Räume überladen, man weiß nicht, wo man klicken soll"

**Stand:** 2026-10-15 · Commit 11d8b89 · Rolle: Spieletester + Game Designer · **Art:** nur Prüfung und Doku, kein Code, kein Commit.
**Auslöser:** Bastians Handy-Urteil: „die Karte muss noch besser werden, das sind zu viele kleine einzelne Bausteine, so unübersichtlich und so zerbrechlich sieht das Spiel aus“ · direkt sehen, wo man klicken muss · Zimmer überladen · wissen, wo man was verbessern muss · Zoom (Pinch) · Story länger, aber nicht ewig an einem Level · in der Welt etwas zu tun haben · Werbung soll sich lohnen.
**Messlatte:** Idle Miner Tycoon, Eatventure, My Perfect Hotel.

**Wie getestet:**
- PC-Vorschau 540 × 1200, 37 Bilder unter `shots/k3_test/k3_*.png` (jedes angesehen). Schalter: `--mit-tutorial`, `--tutorial-schritt N`, `--store`, `--tiefe 1/2/3/5`, `--zoom 7/24/34/40`, `--menue …`, `--welt 2–6`, `--moment raum/levelup`, `--offline`.
- `tools/welt_sim.gd` für alle sechs Welten (Zeitpunkte von Räumen, Zielen, Nachrichten, Rängen).
- Durchspielprobe `--frisch --durchspielen --alle-welten` (Zeitraffer im echten Spiel).
- **Handy:** `adb devices` war leer, also kein Gerät verbunden und keine Geräteaufnahmen. Alles unten stammt aus der PC-Vorschau. Umrechnung für Klickziele: 540 px Vorschaubreite ≈ 360 dp, also 1 px ≈ 0,67 dp und **48 dp ≈ 72 px**.

**Hinweis zu Vorschau-Artefakten:** Mit `--tiefe` bleibt der Rang auf „Anfang“ (es werden keine Ziele eingelöst), und Szenen von übersprungenen Raumkäufen stauen sich und erscheinen über offenen Menüs (k3_40, k3_36). Das wird unten nur dort als Fehler gewertet, wo es auch im echten Spiel passieren kann.

---

## 0. Kurzurteil

Die Mechanik und das Tempo der ersten 4 Minuten sind auf Top-Idle-Niveau: erster Kauf nach 1 s, Flur nach 3:35, Rang 2 nach 2:26, das Tutorial ist klar und spricht mit einer Stimme. **Bastians Urteil stimmt aber in allen Punkten**, und es hat drei Ursachen:

1. **Die Karte besteht aus Kleinteilen statt aus Flächen.** Böden im 1-m-Schachbrett (a/b-Kacheln), Wände aus 1-m-Modulen mit Pfosten, gestrichelte Bauplatz-Umrisse, je Station 5 Stern-Knöpfe, 4 Eckpfosten mit Wimpeln, ein Schild am langen Stiel, fliegende Clip-Kärtchen, dazu 14–20 Deko-Möbel je Raum (WG-Zimmer 14 auf 7 × 7 m, Welt 2 insgesamt 146 gesetzte Möbel). Auf 360 dp Breite wird daraus Rauschen. Die Stationen, um die es geht, sind nicht größer und nicht kräftiger als ein Wäscheständer.
2. **Der nächste Klick ist nur einmal auf der ganzen Karte markiert**, und zwar mit einem kleinen Chip (~63 × 23 dp), der oft auf eine Ausstattung statt auf den Ausbau zeigt und einen anderen Preis nennt als die Ausbau-Liste.
3. **Das Tempo hat in jeder Welt ein Loch von 34–63 Minuten ohne neuen Raum** (zwischen Raum 3 und 4), danach kommen Raum 4, Raum 5 und der Abschluss in wenigen Minuten hintereinander, und das Einkommen springt um das 1000- bis 3000-Fache. Das ist „ewig an einem Level hängen“ und „am Ende zu schnell“ zugleich.

---

## 1. Probleme nach Schwere

### HOCH

#### H1 · Karte wirkt kleinteilig und zerbrechlich
- **Beleg:** `shots/k3_test/k3_26_w1_t0_zoommax.png` (ganze WG), `k3_10_w1_t5_zoom34.png`, `k3_25_w3_zoommax.png`, `k3_15_w1_zoom7.png`
- **Was man sieht:** Wände aus vielen kurzen Segmenten mit Pfosten, Böden als sichtbares Schachbrett, limettengrüne Strichel um jeden gesperrten Raum, Absperrband und Pfosten im Flur, Kartons. Gesperrte und gekaufte Räume unterscheiden sich kaum (der große helle Raum unten rechts in k3_26 sieht gleich aus wie das eigene Zimmer). Unter der Wohnung nehmen Straße, Hecke und Auto in der Startansicht ein Viertel des Bildes ein.
- **Ursache:**
  - `game/world/grundriss_bauer.gd:145`: Böden als 1-m-Schachbrett `(ix + iz) % 2` aus `boden_<typ>_a/_b`. Wände je 1-m-Modul plus Pfosten (`WAENDE`, :35–40).
  - `grundriss_bauer.gd:343–381` `_baue_umriss`: gestrichelter Rahmen (Strich 0,55 m) um jeden gesperrten Raum. Dazu `_sperre` mit Kartons und Absperrband (:320–340).
  - Schleier über `material_overlay` ist zu schwach. Gesperrte Räume bleiben fast so hell wie gekaufte.
- **Lösung:** siehe Variante A/B in Abschnitt 3. Kurz gesagt: **eine Bodenplatte je Raum** (ein Mesh, eine Farbe, leichte Fase, keine Fugen). Wände als **durchgehende dicke Blöcke** (≥ 0,35 m, eine Deckfarbe oben, keine Pfosten). Gesperrte Räume **deutlich dunkel/entsättigt (≈ 55 %)** statt Strichel-Rahmen. Absperrband und Kartons weg, dafür ein großes Schild. Startzoom so wählen, dass Straße und Garten höchstens 10 % des Bildes einnehmen.

#### H2 · Räume mit Deko überladen, Stationen gehen unter
- **Beleg:** `k3_08_w1_store_t0.png` (Zimmer: Matratze, Gitarre, Rucksack, Sitzsack, Pizza, Sneaker, Wäscheständer, Kartons, Kleiderstange, Lampe …), `k3_21_w3_t2.png` (Laden: Kartons überall), `k3_22_w4_t2.png`, `k3_20_w2_t2.png`
- **Zahlen:** `art_source/scripts/build_einrichtung_wg_a.py:646–670` setzt 14 Möbel in das 7 × 7-m-Zimmer, das außerdem drei Stationen trägt. Gesamt je Welt (`setzen(`-Aufrufe): Welt 2: 146, Welt 4: 135, Welt 5: 127, Welt 3: 112, Welt 6: 75.
- **Ursache:** Die Einrichtung soll „bewohnt“ wirken (WELT1_TIEFE). Auf dem Handy konkurriert aber jedes Deko-Teil mit den Stationen und den Ausstattungsmodellen, die eigentlich den Fortschritt zeigen sollen. Deko und Ausstattung haben dieselbe Größe und dieselben Farben.
- **Lösung:** Faustregel der Messlatte (Eatventure, My Perfect Hotel): **je Raum höchstens 3–5 Deko-Teile, alle an den Wänden, niedrig und entsättigt.** Die Mitte gehört den Stationen. Stationen und Ausstattung **20–30 % größer skalieren** und als einzige Objekte kräftig färben (Weltakzent). Konkret Welt 1 Zimmer: Matratze, Kleiderstange, Pflanze bleiben; Pizza, Sneaker, Rucksack, Gitarre, Steckdosenleiste, Kartons, Wäscheständer, Sitzsack streichen. Prüfwert für jedes Blender-Skript: `moebel_bericht()` um eine Höchstzahl je Zone ergänzen (z. B. 5) und laut melden.

#### H3 · Man sieht nicht, wo man klicken soll und was sich lohnt
- **Beleg:** `k3_09_w1_store_t2.png` (12.884 €, alle drei Stationen bezahlbar, aber nur über „Idee“ steht ein Chip „⬆ 1.281“), `k3_13_w1_menue_ausbau.png` (dieselbe Idee kostet in der Liste **1.454**), `k3_38_raum_start.png` (die 1.281 gehören zur Ausstattung „Notizen“), Welten 2–6 `k3_20`–`k3_24` (kein einziger Kaufchip im Bild)
- **Ursache:** `game/ui/kartenmarker.gd:598–628` `_waehle_beste`: genau **eine** Station bekommt den Chip. Ist der beste Kauf eine Ausstattung, zeigt der Chip deren Preis, sagt aber nicht, dass es eine Ausstattung ist. Beim Tippen landet man im Stationsmenü, wo der große grüne Knopf etwas anderes kostet. Die Stationsschilder selbst (`_aktualisiere_badge`, :632 ff.) zeigen nur „Lv 17 ☆☆☆☆☆“ und keinen Preis und keinen Kaufzustand.
- **Lösung (Idle-Miner/Eatventure-Regel):** **Jede Station, deren Ausbau bezahlbar ist, bekommt einen grünen Pfeil am Schild.** Die beste bekommt zusätzlich Puls und Größe 1,2. Nicht bezahlbar ergibt einen grauen Pfeil mit Fortschrittsring, wie viel noch fehlt. Ausstattungs-Tipp als eigenes Symbol (Werkzeug statt Pfeil) mit dem Namen des Teils, z. B. „Notizen 1.281“. Den Chip mindestens 72 × 72 px groß machen (siehe H5).

#### H4 · Tempo: ein Loch von 34–63 Minuten ohne neuen Raum in jeder Welt, danach ein Endspurt in wenigen Minuten
- **Beleg (welt_sim, Logs `k3_sim_<welt>.txt` im Scratchpad):**

| Welt | Raum 3 | Raum 4 | **Loch** | Raum 5 | Abschluss | Einkommen Raum 5 → Ende |
|---|---|---|---|---|---|---|
| 1 WG | 22:49 | 62:35 | **40 min** | 68:43 | 78:55 | 13 Tsd/s → 12,9 Mio/s (×1000) |
| 2 Studio | 29:20 | 62:59 | **34 min** | 66:36 | 74:53 | 378 Tsd/s → 129 Mio/s |
| 3 Laden | 26:27 | 62:49 | **36 min** | 65:15 | 84:55 | 11 Mio/s → 245 Mio/s |
| 4 Lager | 32:26 | 75:00 | **43 min** | 83:29 | 99:30 | 31 Mio/s → 11,6 Mrd/s |
| 5 Farm | 38:16 | 93:05 | **55 min** | 93:51 | 108:25 | 268 Mio/s → 125 Mrd/s |
| 6 Portfolio | 38:49 | 101:51 | **63 min** | 104:52 | 119:18 | 5,9 Mrd/s → 1,17 Bio/s |

- In der Durchspielprobe im echten Spiel (`--alle-welten`, ohne Absturz bis zum Abspann, **416 min Spielzeit**; Welten 61/58/60/72/76/~89 min) ist es gleich: Welt 4 steht von 30 bis 60 min bei „Räume 3/5“ und springt dann in 10 min von 19,9 Mio/s auf 7,7 Mrd/s. Welt 6 steht 40 min (30 → 70) bei „Räume 3/5“ und springt dann in 10 min von 1,9 auf 61 Mrd/s.
- Die Ränge verdichten sich am Ende: In Welt 3–6 kommen Rang 7, 8 und 9 im selben Augenblick (welt_sim „R7 84:55 · R8 84:55“). Die erste Crew kommt in Welt 4 erst nach 68 min.
- **Ursache:** Raumpreise in `data/balance/<welt>.json` → `bereiche` wachsen je Raum um ×10. Der Schritt Raum 3 → 4 ist der größte (W1 25 Tsd → 300 Tsd = ×12; W2 ×18; W3 ×19,5; W4 25 Mio → 600 Mio = ×24; W5 ×24; W6 ×24), während das Einkommen in dieser Phase noch linear wächst. Raum 4 → 5 ist dagegen nur ×3,3–9. Die Meilenstein-Multiplikatoren (alle 12 Stufen ×1,7) zünden erst gesammelt, wenn man genug Geld für mehrere Stufen hat. Dann explodiert das Einkommen und Raum 4 und 5 sind sofort bezahlbar. Die Verlängerung aus K2 P6 hat nur die **Wartezeit vor Raum 4** verlängert, nicht mehr Inhalt gebracht.
- **Lösung:**
  1. **Raumkurve glätten:** Raum 4 billiger (≈ ×0,3), Raum 5 teurer (≈ ×2–3), sodass jeder Schritt ≈ ×10 bleibt. Ziel: alle 10–15 min etwas Großes (Raum, Stern, Crew, Rang). Den Korridor in `balance_sim.gd` um eine Prüfung **„größte Lücke zwischen zwei Raumkäufen ≤ 18 min“** ergänzen.
  2. **Inhalt ins Loch legen:** zwischen Raum 3 und 4 die erste Crew (heute 35–68 min), einen Zwischenraum (den 6. Raum aus K2 6.3 vorziehen, als Raum 3b) und eine Missionskette mit drei Schritten.
  3. **Endspurt bremsen:** den Wert der Meilenstein-Multiplikatoren je Welt ab Stufe 36 flacher machen (z. B. ×1,5) oder den Abschluss an ein letztes Ziel binden, das Zeit braucht (Weltziel-Objekt bauen, 3–5 min Bauzeit, mit Werbung verkürzbar, siehe Abschnitt 4).

#### H5 · Klickziele unter 48 dp auf der Karte
- **Beleg:** `k3_09` (Kaufchip „⬆ 1.281“ ≈ 95 × 35 px ≈ **63 × 23 dp**), Stationsschilder ≈ 85 × 52 px ≈ **57 × 35 dp**, Türschilder ≈ 130 × 55 px ≈ 87 × 37 dp, Knöpfe x1/x10/MAX ≈ 55 × 65 px ≈ 37 × 43 dp (`k3_07`), Zahnrad ≈ 65 px ≈ 43 dp
- **Ursache:** `kartenmarker.gd` baut die Schilder auf Textgröße (`UiStil.GR_TEXT`, Chip mit `KAUF_ABSTAND_Y -58`). `_tippflaeche` liegt nur auf dem sichtbaren Schild.
- **Lösung:** Unsichtbare Tippfläche um jedes Schild und jeden Chip auf **mindestens 72 × 72 px (48 dp)** vergrößern, ohne die Grafik zu vergrößern. Den Kaufchip selbst auf ≥ 64 px Höhe bringen. Die ganze Stationsplatte zählt als Tippziel (das ist laut Release-Paket A schon so, der Text auf dem Schild sagt es aber nicht). Die x1/x10/MAX-Knöpfe auf ≥ 72 px Breite bringen.

### MITTEL

#### M1 · Schilder hängen an langen Stielen und überlappen
- **Beleg:** `k3_15_w1_zoom7.png` (das Schild „Aufnahme“ hängt weit neben der Station, eine lange weiße Linie quer durchs Bild), `k3_10` (Idee/Aufnahme/Schnitt-Schilder übereinander), `k3_21` (Figur verdeckt „Druck“)
- **Ursache:** `kartenmarker.gd:395–410`: Das Schild wird auf `HOEHE_BADGE 1.9` projiziert und an den Bildrand oder unter das Banner geklemmt, und der Stiel (`_stiele`) verbindet es dann über große Strecken mit `HOEHE_ANKER 0.5`.
- **Lösung:** Das Schild flach **auf** die Plattenvorderkante legen (Eatventure), ohne Stiel. Beim Herauszoomen (Zoom > 24) nur Name plus Pfeil zeigen, Stufe und Sterne erst ab Zoom < 18. Kann ein Schild nicht über seiner Station stehen, wird es ausgeblendet und nicht verschoben.

#### M2 · Doppelte und dreifache Stern-Anzeige als Kleinteile
- **Beleg:** `k3_06_w1_tiefe5.png`, `k3_05`: Schild „☆☆☆☆☆“, dazu 5 Knöpfe an der Plattenkante, ab 2 Sternen 4 Eckpfosten mit Wimpel, dazu Ring und Clip-Kärtchen
- **Ursache:** `game/world/stationsplatte.gd:96–135` `setze_sterne` (CylinderMesh-Knöpfe Radius 0,085 m, BoxMesh-Pfosten 0,06 m). Auf dem Handy ist ein Knopf ≈ 3 px groß, das liest sich als Krümel.
- **Lösung:** Sterne **nur** im Schild. Die Plattenstufe nur über die Randfarbe zeigen (Akzent, dann Silber ab 3, dann Gold ab 5) und über die Plattengröße (mit Stern 3 wächst sie um 10 %). Knöpfe und Wimpel streichen. Fünf leere Sterne bei „Lv 1“ ausblenden, sonst wirkt der Anfang wie „0 von 5 geschafft“.

#### M3 · Oben vier Informationsschichten übereinander
- **Beleg:** `k3_08` (Kopfleiste, Zielleiste, rote Karte „Bremst gerade Idee“, Mo-Banner: ~300 px von 1200), `k3_20_w2_t2.png` (Welt 2 zusätzlich Speicherleiste mit „Archiv bauen“: ~270 px nur für Leisten)
- **Ursache:** `hud.gd:1240` (Engpass-Karte), `hud.gd:733` (Zielkarte), Speicherleiste Welt 2, Banner im `_stapel`.
- **Lösung:** Die Engpass-Karte streichen. Der rote Ring an der Station plus der rote Pfeil am Schild reichen (das Tutorial hat „Rot heißt: hier klemmt's“ schon erklärt). Die Speicherleiste in Welt 2 in die Zielleiste einklappen (eine Zeile). Höchstens zwei Leisten oben.

#### M4 · Türschilder und Richtungs-Chips verdecken Stationen
- **Beleg:** `k3_38_raum_start.png` („Das Wohnzimmer · 25.000 €“ liegt mitten auf der Aufnahme), `k3_11_w1_t2_zoom24.png` (Schild „Alles ×1,5 · Tobi wohnt noch hier“ auf der Aufnahme), `k3_08` („Neu: Der Stream 25.000“ über dem Schnitt)
- **Ursache:** `kartenmarker.gd:310–324`: `_klemme_an_rand` zieht das Schild des nächsten Raums ins Bild. Weil oben die Leisten und unten das Sheet liegen, ist der freie Streifen schmal und das Schild landet in der Bildmitte. Die Bereichsposition ist der Türpunkt und nicht die Raummitte.
- **Lösung:** Richtungs-Chips nur **am linken oder rechten Bildrand**, als schmaler Pfeil-Tab (Idle Miner). Das Raumschild in die Raummitte setzen und nur zeigen, wenn die Raummitte im Bild ist. Für Bedingungsräume („Tobi wohnt noch hier“) nur ein Schloss-Symbol, den Text erst im Raum-Panel.

#### M5 · Gesperrter Raum zeigt nicht, was man bekommt
- **Beleg:** `k3_33_tut7_flur.png` (Mo: „Hinter der Tür steht der Router“, im Bild sind aber ein Absperrpfosten und ein roter Teppich zu sehen, kein Router), `k3_12_w1_menue_bereich1.png`
- **Ursache:** K2 P5a (Stationsumriss im gesperrten Raum) ist nur als Strichel-Rahmen um die Zone umgesetzt, nicht als Silhouette der neuen Station (`grundriss_bauer.gd:343`).
- **Lösung:** Im gesperrten Raum steht die neue Station als **dunkle Silhouette in voller Größe** auf einer gestrichelten Platte, darüber ein großes Schild „Neu: Upload · 200 €“. Ab bezahlbar pulst das Schild in Limette.

#### M6 · Zoom: Pinch gibt es, aber man erfährt es nicht, und die Grenzen sind ungünstig
- **Befund:** Pinch ist eingebaut (`game/world/world_camera.gd:176–196`, `_pinch`), dazu das Mausrad (:108–116). Grenzen je Welt aus `worlds.json` → `karte.zoom_min/zoom_max`: W1 7–34 (Start 14), W2/W3 7–24 (Start 14/16), W4/W5 7–26, W6 7–34 (Start 21).
- **Probleme:**
  - Es gibt keinen Hinweis und keine Knöpfe. Wer nicht von sich aus mit zwei Fingern zieht, bleibt bei Startzoom 14 und sieht nur 3 Stationen und keine anderen Räume (`k3_08`). Das erklärt „unübersichtlich“: Man sieht die Wohnung nie als Ganzes, solange man nicht zoomt.
  - Zoom 7 ist zu nah (`k3_15`: Schilder an langen Stielen, Möbel bildfüllend). Zoom 34 in W1 ist zu weit (`k3_10`: Schrift im Schild ≈ 9 px).
  - In W2/W3 deckt `zoom_max 24` nicht die ganze Karte ab (`k3_25`: `--zoom 40` wird auf 24 gekappt).
  - `world_camera.gd`: `InputEventMagnifyGesture` wird nicht ausgewertet (betrifft nur Trackpads, auf Android unkritisch). Pinch selbst muss auf dem Gerät noch geprüft werden (kein Handy verbunden).
- **Lösung:** Startzoom so, dass **alle gekauften Räume plus der nächste** ins Bild passen (dynamisch aus den Zonen, wie `raum_zoom` es für einzelne Räume schon tut). Zoombereich auf etwa 10–26 einengen. Beim ersten Raumkauf zoomt die Kamera automatisch hinaus und Mo sagt einmal „Mit zwei Fingern zoomen“. Optional ein kleiner Knopf „Ganze Karte“ am Rand.

#### M7 · Zwei Modale gleichzeitig: Offline-Bericht unter einer Szene
- **Beleg:** `k3_36_offline.png`: Die Rückkehr-Karte ist ausgegraut, darüber liegt Mos Szene. Man weiß nicht, was man zuerst tippen soll.
- **Ursache:** `main.gd:1475–1489` (Offline-Bericht auf `CanvasLayer 15`) und die Szenen-Warteschlange (`szene_view.gd`) prüfen nicht, ob schon ein Modal offen ist. Mit `--tiefe` ist es verstärkt, kann aber auch im echten Spiel passieren, wenn beim Start eine Szene fällig ist.
- **Lösung:** Eine zentrale Modal-Warteschlange (Offline-Bericht, dann Tagesgeschenk, dann Szene, dann Moment), immer nur eins.

#### M8 · Werbung: nur zwei Platzierungen, und eine verrät nicht, dass es Werbung ist
- **Bestand:** `data/services/ads.json`: `schub` (×2 für 240 s, Sperre 300 s, 8 je Sitzung, `hud.gd:532–543`; der erste Boost ist gratis) und `offline_verdoppeln` (`main.gd:1485`). `anbieter: "stub"`.
- **Beleg:** `k3_36_offline.png`: Der Knopf „Verdoppeln (+39.697)“ hat kein Video-Symbol. Der Boost-Knopf erscheint erst ab Rang 3.
- **Probleme:** ×2 für 4 Minuten ist im Vergleich mit der Messlatte schwach (Idle Miner: ×2 für 4 h stapelbar, Eatventure: ×2 Umsatz 1–2 h oder Sofortgeld = 1–2 h Einkommen). Im 40-Minuten-Loch (H4) gibt es nichts, das eine Werbung wirklich lohnend macht.
- **Lösung:** siehe Abschnitt 4.

#### M9 · „In der Welt etwas zu tun haben“: die Welt bietet kaum Tipp-Anlässe
- **Beleg:** `k3_08`–`k3_24`: Außer den Stationen gibt es nichts zu tippen. Die Tipp-Momente (Herz/Geschenk-Blase, `kartenmarker.gd:427–440`) kommen selten, und die fliegenden Clip-Kärtchen (`clip_fluss.gd`) kann man nicht antippen.
- **Lösung:** siehe Abschnitt 5.

### NIEDRIG

| # | Problem | Beleg | Ursache | Lösung |
|---|---|---|---|---|
| N1 | Tutorial nennt „+0,1 €/s“, das Menü zeigt „+60 Ideen/Min“ und „+100 %“, also drei Einheiten für dieselbe Stufe | `k3_30_tut1_ausbauen.png` | `stationsmenue.gd` Held-Zeile + Knopfzeile | Im Knopf und in der Held-Zeile nur „+0,1 €/s“, Ideen/Min klein darunter |
| N2 | Fortschrittsmenü heißt „Das Zimmer · Fortschritt“, die Kopfleiste „Der Gaming-PC“ | `k3_37_fortschritt.png` | `menues.gd` Titel aus Weltname | Titel = `welt_ziel` |
| N3 | Raumkauf-Moment sagt nur „Gekauft: Der Flur / Upload“, nicht was es bringt | `k3_34_moment_raum.png` | `moment_view.gd` | Zeile „Kette ×2 · neue Station“ aus `bereiche.<id>.danach` |
| N4 | Hinweis-Toast „★ Stativ steht · Der Gaming-PC“ bleibt unten mitten auf der Karte stehen | `k3_09`, `k3_13` | Markentoast im HUD-Stapel | Nach 3 s ausblenden oder in die Kopfleiste ziehen |
| N5 | Welt 2 dunkel und kontrastarm, rosa Platten auf dunklem Holz schlecht zu unterscheiden | `k3_20`, `k3_27` | `worlds.json` → `licht` Welt 2 | Umgebungslicht +20 %, Platten heller |
| N6 | Welt-2-Tutorial: Der Ring liegt auf einer Glaswand, das Schild „Dreh“ ist halb verdeckt | `k3_27_w2_start.png` | `worlds.json` Station/`schild` Welt 2 | `schild`-Versatz, Ring über `ANZEIGE_POSITIONEN` |
| N7 | Durchspielprobe und welt_sim messen unterschiedlich (W1 61 vs. 79 min, W3 60 vs. 85 min) | Logs | Probe tippt Momente/Boost, Sim nicht | Beide Werte im Korridor ausweisen, sonst wird P6 doppelt gezählt |
| N8 | Bei `--tiefe` erscheinen das Tutorial (Hand + Mo-Karte bei Lv 41) und gestaute Szenen über Menüs | `k3_06`, `k3_40` | `main.gd:1221` überspringt das Tutorial nur mit `--store` | `--tiefe` setzt `--store` mit, Szenen beim Vorspulen verwerfen |
| N9 | Kein Gerät für die Pinch-Prüfung | `adb devices` leer | — | Auf dem Handy: Pinch, Grenzen und Tippflächen nachprüfen |

---

## 2. Die ersten 5 Minuten aus Sicht eines neuen Spielers

| Zeit | Was passiert (Bild) | Urteil |
|---|---|---|
| 0:00 | Key-Art, Mo: „Dein erster Clip hat drei Aufrufe.“ (`k3_01`) | Stark, bester Bildschirm des Spiels |
| 0:05 | Zimmer, Hand zeigt auf den Ring um die Pinnwand, Mo erklärt (`k3_03`) | Gut. Die Pinnwand selbst ist im Ring kaum zu erkennen (Hocker im Vordergrund, Pinnwand hinten an der Wand). |
| 0:10 | Stationsmenü, Hand auf AUSBAUEN (`k3_30`) | Gut, aber drei Einheiten (N1) |
| 0:20 | Kette mit Pfeilen, roter Ring (`k3_31`) | Sehr gut, genau richtig |
| 1:09 | Zielleiste mit Hand (`k3_32`) | Gut |
| 2:26 | Rang 2 | Gut (Rang-Moment `k3_35` mit „Neu: …“) |
| 3:35 | Flur: Ring um einen Absperrpfosten, „Hinter der Tür steht der Router“ (`k3_33`) | Schwach: Man sieht keinen Router und keinen Raum, nur einen Teppichstreifen (M5) |
| 4–5 | Danach frei: drei Stationen, ein Chip, zwei Türschilder, rote Warnkarte, Mo-Banner (`k3_08`) | Hier kippt es: viele Signale, aber kein klares „tipp hier“ (H3, M3) |

---

## 3. Varianten-Skizzen für eine aufgeräumte Karte

Alle drei behalten Kern, Daten-IDs, Sticker-Pop und Stationsmodelle. Sie ändern nur `grundriss_bauer.gd`, `stationsplatte.gd`, `kartenmarker.gd`, die Einrichtungs-Skripte und `worlds.json` (Zoom).

### Variante A · „Bühne“: Bodenplatten statt Kacheln, dicke Wände, wenige große Möbelblöcke (empfohlen)

```
 ┌━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┓      ━ = Wand 0,35 m dick, durchgehend,
 ┃  ZIMMER          ┃  FLUR        ┃          eine Deckfarbe, keine Pfosten
 ┃ ╭────╮  ╭────╮   ┃  ▓▓▓▓▓▓▓▓    ┃      ╭─╮ = Stationsplatte 2,4 × 2,4 m,
 ┃ │IDEE│  │SCHN│   ┃  ▓ UPLOAD ▓  ┃          Rand in Akzentfarbe, Schild flach
 ┃ │ ⬆  │  │ ⬆  │   ┃  ▓ 200 €  ▓  ┃          vorn auf der Platte (Name + Pfeil)
 ┃ ╰────╯  ╰────╯   ┃  ▓▓▓▓▓▓▓▓    ┃      ▓ = gesperrt: Raum 55 % dunkel,
 ┃ ╭────╮   [Bett]  ┃              ┃          Stations-Silhouette + großes Schild
 ┃ │AUFN│   [Regal] ┃              ┃      [ ] = höchstens 3 Deko-Blöcke je Raum,
 ┃ ╰────╯           ┃              ┃          an der Wand, entsättigt
 ┗━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┛
```
- **Boden:** ein Mesh je Zone (eine Farbe, 3-cm-Fase am Rand) statt Schachbrett. Die Holzmaserung als Textur, nicht als Fugen.
- **Wände:** halbhoch (0,9 m), dick, durchgehend. Außenwand vorn weglassen (Puppenhaus-Schnitt), damit keine Wand Stationen verdeckt.
- **Möbel:** Deko je Raum auf 3 Blöcke zusammenfassen (z. B. „Bett + Nachttisch“ als ein Teil). Stationen +25 % größer.
- **Warum:** Das ist der Look von My Perfect Hotel und Eatventure. Wenige große Formen wirken stabil und hochwertig, und das Auge findet sofort die drei Plattformen. Diese Variante löst H1, H2 und M2 direkt.

### Variante B · „Raum-Plakette“: jeder Raum ist eine Karte mit eigener Upgrade-Plakette

```
 ╔═══════════════════╗ ╔═══════════════════╗
 ║ DAS ZIMMER  ★★☆   ║ ║ DIE KÜCHE  🔒      ║
 ║ [Plakette: ⬆ 3]   ║ ║ Alles ×1,25        ║
 ║   ◉ IDEE  ◉ SCHN  ║ ║ ███ 1.240/2.000 €  ║
 ║   ◉ AUFN          ║ ║                    ║
 ╚═══════════════════╝ ╚═══════════════════╝
```
- An der Raumecke hängt eine **Plakette** mit der Zahl bezahlbarer Upgrades im Raum („⬆ 3“). Tippen öffnet das bestehende Raum-Panel (`k3_38`, das schon gut ist). Gesperrt: Preis mit Sparbalken.
- Herausgezoomt (Zoom > 22) blenden Stationsschilder aus, und **nur die Plaketten bleiben**. Hineingezoomt erscheinen die Stationsschilder.
- **Warum:** löst „wo muss ich was verbessern“ auf Raumebene (Idle Miner: eine Schacht-Plakette je Ebene). Die Karte wird bei jedem Zoom lesbar, weil es je Zoomstufe nur **eine** Art Schild gibt. Lässt sich mit Variante A kombinieren.

### Variante C · „Fokusraum“: ein Raum groß, die anderen als Kacheln am Rand

```
 ┌──────────────────────────────┐
 │  Kopfleiste / Ziel           │
 │ ┌──────────────────────────┐ │
 │ │   AKTIVER RAUM, Zoom 12  │ │   Wischen links/rechts = nächster Raum
 │ │   3 Stationen groß       │ │   (Kamera fährt, wie P5c-Betreten)
 │ └──────────────────────────┘ │
 │ [Zimmer][Flur][Küche🔒][Wohn🔒]│  ← Raumleiste: Plakette + Preis je Raum
 │  Menüleiste                  │
 └──────────────────────────────┘
```
- Die Kamera steht immer auf **einem** Raum (Zoom wie `raum_zoom`). Eine Raumleiste über der Menüleiste zeigt alle Räume als Kacheln mit „⬆ n“ oder Preis. Pinch bleibt für die Gesamtansicht.
- **Warum:** maximal übersichtlich auf 360 dp, die Klickziele werden automatisch groß. Nachteil: Man verliert das Gefühl, durch eine Wohnung zu gehen, und es gibt mehr UI-Arbeit. Gut als Notlösung, falls A + B auf kleinen Geräten nicht reichen.

**Empfehlung:** A + B zusammen. A macht die Karte ruhig, B sagt pro Raum, wo es etwas zu tun gibt. C erst, wenn ein Handy-Test zeigt, dass A + B nicht reichen.

---

## 4. Werbung, die sich lohnt (Rewarded Ads)

Grundsatz aus `ads.json` bleibt: **Angebot, nie Bedingung.** Jede Platzierung zeigt ein Video-Symbol und den Gegenwert in Zeit („= 2 Std. Einkommen“).

| Platzierung (neu = ★) | Wo | Gegenwert | Warum es sich lohnt |
|---|---|---|---|
| `schub` (vorhanden) | Boost-Knopf | heute ×2 / 4 min → **×2 / 30 min, stapelbar bis 4 h** (`hoechstdauer_sekunden` 1800 gibt es schon) | Lohnt erst, wenn man danach weg sein darf (Idle-Miner-Muster) |
| `offline_verdoppeln` (vorhanden) | Rückkehr-Karte | ×2 → **×3** | Größter Einzelbetrag, braucht Video-Symbol |
| ★ `raum_sofort` | Raum-Panel, wenn ≥ 70 % gespart | Restbetrag geschenkt | Wirkt genau im Loch aus H4. Eine Werbung je Raum. |
| ★ `ziel_doppelt` | Zielleiste „Holen“ | Zielbelohnung ×2 | Einmal je 10 min, kleiner, aber häufiger Anlass |
| ★ `kiste` | Lieferkiste/Paket fliegt über die Karte (siehe 5) | tippen = 1 min Einkommen, mit Werbung = 15 min | Der Tipp-Anlass in der Welt |
| ★ `crew_ziehen` | Crew-Karte | eine Karte gratis | Die erste Crew kommt heute erst nach 35–68 min |
| ★ `geschenk_doppelt` | Tagesgeschenk | ×2 | Täglicher Grund zum Zurückkommen |

Die Limits stehen in `ads.json` (Sperre, Höchstzahl je Sitzung). Kein Wert im Code.

---

## 5. „In der Welt etwas zu tun haben“

1. **Lieferkiste / Paket** (alle 2–3 min): fliegt über die Karte oder steht vor der Tür und ist groß und tippbar (≥ 72 px). Ohne Werbung kleine Belohnung, mit Werbung große (siehe `kiste`). Thema je Welt in `theme.json` (Paket, Kundenanruf, Serverwarnung …).
2. **Clip-Stapel antippen:** Vor der bremsenden Station stapeln sich die Clips schon (`clip_fluss.gd`, `STAPEL_MAX 8`). Ein Tipp auf den Stapel räumt ihn ab (+ kurzer Schub an dieser Station). Das erklärt den Engpass spielerisch.
3. **Figuren mit Sprechblase:** Mo, Mira und Tobi bekommen gelegentlich ein „!“ über dem Kopf. Tippen zeigt eine Mini-Aufgabe („Bring Tobi den Topf zurück“ = Ziel), die auch die Story über das 40-Minuten-Loch trägt.
4. **Tipp-Momente häufiger** (heute selten, `kern.momente`), aber kleiner: eher alle 90 s statt nur zu Meilensteinen.

---

## 6. Story-Tempo

Nachrichten sind gut über die Zeit verteilt (W1: n08 32:16, n19 39:44, n10 47:57, n20 54:42), aber **Szenen und Freischaltungen fehlen im Loch** zwischen Raum 3 und 4. In Welt 5/6 liegen 15–25 min zwischen zwei Nachrichten (W6: n08 50:03 → n19 74:41 → n10 88:59). Vorschlag: zwei Szenen mit Mini-Auftrag (siehe 5.3) und eine Missionskette (`kette`) mit drei Zwischenzielen in jedes Loch legen. Die Gesamtlänge (~6,5 h Sim., ~10–13 h real) bleibt.

---

## 7. Bildverzeichnis (`shots/k3_test/`)

| Bild | Inhalt |
|---|---|
| k3_01/02 | Eröffnung (mit/ohne Tutorial) |
| k3_03 | Erster Spielbildschirm mit Tutorial |
| k3_04–06 | Welt 1, `--tiefe 1/3/5` (mit Tutorial-Artefakt) |
| k3_07 | Stationsmenü Idee |
| k3_08/09 | Welt 1 ohne Tutorial, Tiefe 0/2 |
| k3_10/11/15/26 | Zoom 34/24/7/34 |
| k3_12/13/14 | Raum-Panel Flur, Ausbau-Liste, Ziele |
| k3_20–24 | Welten 2–6, Tiefe 2 |
| k3_25 | Welt 3 Zoomgrenze |
| k3_27 | Welt 2 Tutorialstart |
| k3_30–33 | Tutorialschritte 1/2/4/7 |
| k3_34/35/36 | Momente Raum/Rang, Offline-Bericht |
| k3_37/38/39/40 | Fortschritt, Raum-Panel Zimmer, Handy, Stationsmenü Aufnahme |
