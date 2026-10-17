# NACHTPLAN 2026-09-17 — Vom Zimmer zum Portfolio

**Auftrag des Nutzers (01:25 Uhr, bis 10:00 Uhr):** Welt 1 fertig machen, vom Start
über das Design bis zu sauber antippbaren Stellen. Danach jede Welt mit neuem
Design, einem **eigenen Design-System**, das frisch aussieht und trotzdem wie ein
Idle-Game funktioniert. Kurze Story ohne Textwände, aber mit **Figuren**:
Mohammed (erster Gaming-PC), Younes (starke Videos), Roman (Merch-Shop,
mehrere Versand-Shops), eine Frau (Krypto-Farm, dann Millionen investieren).
Dazu Extra-Missionen: alle Aktien, alle Immobilien, Schmuck und mehr kaufen.
Vollständig spielbar, nichts halb.

Entscheidung dazu: **ADR-022** in `MASTER_DECISIONS.md`.

---

## 1. Der neue Bogen

Die sechs Welt-IDs bleiben (Spielstände, Tests, Ordner). Ihr **Inhalt** wechselt:

| # | ID (bleibt) | Titel | Figur | Worum es geht | Akzentfarbe |
|---|---|---|---|---|---|
| 1 | `zimmer` | Die WG | **Mohammed („Mo“)**, bester Kumpel | Clips drehen, bis der erste Gaming-PC dasteht | Blau `#3D7BFF` |
| 2 | `auftrag` | Das Studio | **Younes**, Kameramann | Younes wird angestellt, ihr dreht große Videos in einer Hinterhof-Garage | Pink `#FF4FA3` |
| 3 | `webseiten` | Der Merch-Laden | **Roman**, Designer mit Laden-Traum | Eigener Merch: entwerfen, drucken, packen, verschicken, Drops | Orange `#FF7A1A` |
| 4 | `buero` | Das Lager | **Roman** (jetzt Partner) | Mehrere Online-Shops, eine Lagerhalle, ein Packteam | Türkis `#12B5A5` |
| 5 | `produkt` | Die Farm | **Selin**, Ingenieurin | Eine stillgelegte Fabrikhalle wird zur Krypto-Farm | Violett `#8B5CF6` |
| 6 | `kapital` | Das Portfolio | **Selin** + alle | Millionen anlegen. Missionen: alle Aktien, alle Immobilien, Schmuck, Uhren, Kunst | Gold `#F2B200` |

Die Spielfigur bleibt **„Du“**: gesichtslos, Kapuze, von hinten.
Die Nebenfiguren haben Gesichter und schreiben im Handy. **Mira** und **Tobi**
bleiben die Mitbewohner in Welt 1. Der Kommentar-Faden (Web-Entwickler) entfällt.

### Tonregeln (gelten weiter, leicht gelockert)
- Nachrichten **kurz**: höchstens zwei Sätze, Chat-Ton, gern mit Witz.
- Keine Ausrufezeichen-Kaskaden. Ein einzelnes „!“ in einem Chat ist erlaubt,
  wenn eine Figur so schreibt (Mo tut das).
- Kein Traum vom mühelosen Reichtum. Jede Welt ist Arbeit.
- **Welt 5/6:** Das ist ein Spiel. Kein echter Coin- oder Firmenname, keine
  Anlageberatung. Der Hinweis im Abspann bleibt Pflicht.
- Keine echten Marken, Plattformen oder Personen.

### Figuren-Steckbriefe (für Modelle und Texte)
| Figur | Aussehen (Chibi, ≤ 1.200 Dreiecke) | Stimme |
|---|---|---|
| Du | Kapuzenpulli grau-blau, von hinten | antwortet selten, dann knapp |
| Mo | Cap rückwärts, dunkles Haar, Bart-Schatten, grüne Jacke | Gamer, begeistert, „Bruder“, schreibt schnell |
| Younes | Bucket-Hat, schwarzes T-Shirt, Kamera um den Hals, kurzer Bart | ruhig, Perfektionist, „noch ein Take“ |
| Roman | blonder Undercut, Brille, Latzhose mit Farbklecksen | Design-Nerd, trocken, rechnet alles nach |
| Selin | lange dunkle Haare im Zopf, Weste, Werkzeuggürtel, Headset | Ingenieurin, klar, nüchtern, wenig Geduld für Hype |
| Mira | Dutt, Kopfhörer (Welt 1) | trocken |
| Tobi | Mütze, Kaffeebecher (Welt 1) | freundlich |

---

## 2. Die Welten im Detail

Für alle neuen Karten gilt das Raster von Welt 1: Feldmitten ganzzahlig, Wände
auf x.5 / z.5. Die Kamera schaut aus (+1, +1, +1), **„oben im Bild“ = (−1, 0, −1)**.
Hohe Wände nur hinten (kleinstes z) und links (kleinstes x), innen halbhoch,
vorn und rechts ein Sockel. Jede Welt hat **5 kaufbare Bereiche**
(`bereich_1…5`) mit derselben Rolle wie in Welt 1:
`bereich_1` schaltet `unlock_transport` frei, `bereich_3` schaltet
`unlock_special` frei, `bereich_2`/`bereich_4`/`bereich_5` geben Faktoren,
`bereich_5` erst `nach` `bereich_4`.

Stationspositionen: je 2,2 × 2,2 m frei. Jede Station hat 3 Ausstattungsplätze
mit **4 Modellstufen** (0 = Anfang, 1/2/3 = die drei Sterne bei Stufe 1/5/10).

### Welt 2 — `auftrag` · „Das Studio“ (Younes)
Hinterhof mit Garage. Grundfläche **x −10…10, z −8…6**.
| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| `garage` (Start) | x −3…3, z 0…6 | `beton` | Set, Kamera, Schnittplatz |
| `hof` | x −10…10, z −3…−1 | `pflaster` | `bereich_1` · Render-Server im Container |
| `requisite` | x −10…−4, z −8…−4 | `holz` | `bereich_2` · Requisitenlager, alle ×1,25 |
| `greenscreen` | x −3…3, z −8…−4 | `studio` | `bereich_3` · Sponsoren-Lounge (Sonderstation) |
| `dach` | x 4…10, z −8…−4 | `deck` | `bereich_4` · Dachdreh, Dreh ×1,5 |
| `kino` | x −10…−4, z 0…6 | `teppich` | `bereich_5` · Vorführraum, alle ×1,5 |
| `younes_ecke` | x 4…10, z 0…6 | `holz` | offen · Younes' Schnittecke, Deko |
Stationen: intake **Konzept** (Storyboard-Wand) · buffer **Dreh** (Set mit
Kamera auf Schiene) · processing **Schnitt** (der Gaming-PC aus Welt 1, jetzt mit
Farbkorrektur) · transport **Render-Server** (Hof) · special **Sponsoren**
(Lounge im Greenscreen-Raum).
Besonderheit: **Speicher-Limit** (bestehende Mechanik): Rohmaterial füllt die
Platten. Umbau „Render-Server mit Archiv“.

### Welt 3 — `webseiten` · „Der Merch-Laden“ (Roman)
Eckladen mit Werkstatt. Grundfläche **x −10…10, z −8…6**.
| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| `werkstatt` (Start) | x −3…3, z 0…6 | `beton` | Design, Druck, Packtisch |
| `laden` | x −10…10, z −3…−1 | `fliese` | `bereich_1` · Verkaufsraum und Paketausgabe |
| `lager` | x −10…−4, z −8…−4 | `beton` | `bereich_2` · Regale, alle ×1,25 |
| `showroom` | x −3…3, z −8…−4 | `holz` | `bereich_3` · Drop-Bühne (Sonderstation) |
| `fotostudio` | x 4…10, z −8…−4 | `studio` | `bereich_4` · Produktfotos, Druck ×1,5 |
| `siebdruck` | x −10…−4, z 0…6 | `beton` | `bereich_5` · zweite Druckstraße, alle ×1,5 |
| `romans_buero` | x 4…10, z 0…6 | `holz` | offen · Romans Zeichentisch |
Stationen: intake **Design** · buffer **Druck** · processing **Verpacken** ·
transport **Versand** · special **Der Drop** (Stammkunden: laufende Einnahmen,
bestehende Mechanik).

### Welt 4 — `buero` · „Das Lager“ (Roman)
Lagerhalle, offen, Stahlträger. Grundfläche **x −12…12, z −9…7**.
| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| `packhalle` (Start) | x −4…4, z 1…7 | `hallenboden` | Bestellungen, Regal, Packteam |
| `gang` | x −12…12, z −3…0 | `hallenboden_linie` | `bereich_1` · Förderband |
| `wareneingang` | x −12…−5, z −9…−4 | `hallenboden` | `bereich_2` · alle ×1,25 |
| `buero_shops` | x −4…4, z −9…−4 | `teppich` | `bereich_3` · Großhändler-Büro (Sonderstation) |
| `hochregal` | x 5…12, z −9…−4 | `hallenboden` | `bereich_4` · Regal ×1,5 |
| `rampe` | x −12…−5, z 1…7 | `asphalt` | `bereich_5` · Laderampe mit Transportern, alle ×1,5 |
| `pausenraum` | x 5…12, z 1…7 | `fliese` | offen · Kicker, Kaffee |
Stationen: intake **Bestellungen** (vier Shop-Bildschirme) · buffer
**Hochregal** · processing **Packteam** (Personen-Mechanik) · transport
**Förderband** · special **Großhändler**.

### Welt 5 — `produkt` · „Die Farm“ (Selin)
Alte Fabrikhalle, Backstein, Sheddach. Grundfläche **x −12…12, z −9…7**.
| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| `halle` (Start) | x −4…4, z 1…7 | `hallenboden` | Strom, Rigs, Kontrollpult |
| `kabeltrasse` | x −12…12, z −3…0 | `gitterrost` | `bereich_1` · Kühlung |
| `trafo` | x −12…−5, z −9…−4 | `beton` | `bereich_2` · Trafostation, alle ×1,25 |
| `kontrollraum` | x −4…4, z −9…−4 | `teppich` | `bereich_3` · Staking-Pult (Sonderstation) |
| `solardach` | x 5…12, z −9…−4 | `deck` | `bereich_4` · Solarpaneele, Strom ×1,5 |
| `rackhalle_2` | x −12…−5, z 1…7 | `hallenboden` | `bereich_5` · zweite Rig-Halle, alle ×1,5 |
| `selins_labor` | x 5…12, z 1…7 | `fliese` | offen · Selins Werkbank |
Stationen: intake **Strom** · buffer **Rigs** · processing **Blöcke**
(Kontrollpult, erzeugt Erlös) · transport **Kühlung** · special **Staking**
(Bestand-Mechanik).

### Welt 6 — `kapital` · „Das Portfolio“ (Selin und alle)
Penthouse-Etage über der Stadt, Glaswände. Grundfläche **x −12…12, z −9…7**.
| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| `lounge` (Start) | x −4…4, z 1…7 | `parkett` | Marktdaten, Analyse, Depot |
| `galerie` | x −12…12, z −3…0 | `marmor` | `bereich_1` · Streuung |
| `tresor` | x −12…−5, z −9…−4 | `marmor` | `bereich_2` · **Schmuck & Uhren**, alle ×1,25 |
| `boardroom` | x −4…4, z −9…−4 | `parkett` | `bereich_3` · Dividenden (Sonderstation) |
| `immobilien` | x 5…12, z −9…−4 | `parkett` | `bereich_4` · **Immobilien** (Stadtmodell), Analyse ×1,5 |
| `kunstsalon` | x −12…−5, z 1…7 | `marmor` | `bereich_5` · **Kunst & Oldtimer**, alle ×1,5 |
| `dachterrasse` | x 5…12, z 1…7 | `deck` | offen · Pool, Party am Ende |
Stationen: intake **Marktdaten** · buffer **Analyse** · processing **Depot** ·
transport **Streuung** · special **Dividenden** (Risiko-Mechanik).
**Missionen** (als Ziele): „Alle Aktien im Depot“ (Depot-Ausstattung auf 10),
„Alle Immobilien“ (Bereich + Ausstattung), „Schmuck-Sammlung komplett“ usw.

---

## 3. Design-System „Sticker-Pop“

Richtung: Karten und Knöpfe wie **Aufkleber**. Dunkle Tinten-Kontur, harter
versetzter Schatten ohne Weichzeichnung, cremiges Papier als Grund, eine
kräftige Grotesk-Schrift. Je Welt **eine** Akzentfarbe, die Farbe der Figur.
Das ist im Idle-Genre selten (dort sind weiche Verläufe und Glanz üblich) und
bleibt trotzdem ruhig, weil es nur **eine** Effektart gibt: die harte Kante.

| Token | Wert | Rolle |
|---|---|---|
| `papier` | `#FFF7EA` | Kartenfläche |
| `papier_2` | `#F3E9D8` | ruhige Fläche, Leisten, deaktiviert |
| `tinte` | `#1B1726` | Kontur, Text, harter Schatten |
| `tinte_2` | `#5A5368` | Nebentext (Kontrast ≥ 4,5 : 1 auf Papier) |
| `kaufen` | `#B6F03C` | Kaufen (Limette), **Text in Tinte** |
| `warnung` | `#FF4D3D` | nur Engpass |
| `akzent` | je Welt (§ 1) | Titel-Chips, Balken, Figuren-Absender |
| `gold` | `#FFC21A` | Münze, Sterne |
| Kontur | 3 px (Knöpfe, Karten), 2 px (Chips) | |
| Schatten | 0 / 4 px, Tinte, **keine** Unschärfe; gedrückt 0 / 1 px + 3 px nach unten | |
| Radius | 18 (Karten), 14 (Knöpfe), 999 (Chips) | |
| Abstände | 4 · 8 · 12 · 16 · 24 · 32 | |
| Schrift | **Bricolage Grotesque** (SIL OFL): ExtraBold für Zahlen/Titel, SemiBold für Text | |

Regeln:
- Eine Hauptaktion je Sheet (Limette). Alles andere Papier mit Kontur.
- Zahlen tabellarisch und groß, Einheiten klein daneben.
- Figuren-Nachrichten tragen die Akzentfarbe der Figur als Sprechblasenrand.
- Bewegung: 80 ms Eindrücken (Schatten verschwindet, Karte rutscht 3 px),
  Kauf: 300 ms Überschwingen. Sonst nichts.
- Tippziele ≥ 48 dp, Safe Area oben.

---

## 4. Taskliste der Nacht

Status: ⬜ offen · 🔶 in Arbeit · ✅ fertig · ❌ verworfen (mit Grund)

| # | Aufgabe | Wer | Status |
|---|---|---|---|
| N01 | Nachtplan, ADR-022, Schrift | Leitung | ✅ |
| N02 | Engine: Tiefe für jede Welt (Bodentypen/Module je Welt aus Daten, Figuren je Welt, Fluss-Symbol je Welt, Licht je Welt, Sondermechaniken + Abschluss 100 %, Simulator für alle Welten) | Agent Engine | ✅ 230 Tests, Sim 65–92 min je Welt |
| N03 | Design-System Sticker-Pop in `game/ui/`, Akzent je Welt, Welt-1-Politur (Start, Tipp-Ziele, Überlagerungen) | Agent UI | ✅ Sticker-Pop in allen Ansichten, 10 UI-Tests |
| N04 | Figuren: Du, Mo, Younes, Roman, Selin (+ Varianten), gemeinsam für alle Welten | Agent Figuren | ✅ 8 Figuren, `art_source/vorschau/crew/gruppe_spiel.png` |
| N05 | Welt 1: Story mit Mo, Gaming-PC als Ziel, Texte, Nachrichten | Leitung | ✅ Texte (Modelle folgen) |
| N10–N14 | Welt 2: Architektur+Einrichtung · Stationen+Ausstattung+Symbole · Daten (worlds/theme/balance) · Integration+Sim · Review | Team | ✅ im Spiel geprüft (`shots/nacht/lt_w2.png`), Sim 81:41 |
| N20–N24 | Welt 3: dito | Team | ✅ im Spiel geprüft (`shots/serie/lt_w3*.png`), Sim 65:01 |
| N30–N34 | Welt 4: dito | Team | ✅ im Spiel geprüft (`shots/serie/lt_w4*.png`), Sim 83:07 |
| N40–N44 | Welt 5: dito | Team | ✅ im Spiel geprüft (`shots/serie/lt_w5*.png`), Sim 66:49 |
| N50–N54 | Welt 6: dito, inklusive Missionen und Abspann | Team | ✅ im Spiel geprüft (`shots/serie/lt_w6*.png`), Sim 69:31, Verlustanzeige korrigiert |
| N60 | Durchspielprobe aller sechs Welten im Zeitraffer, Gerät, FPS | Leitung | ✅ PC: alle 6 Welten bis Abspann, 313 min Spielzeit (`shots/nacht/durchspiel.log`) · ❌ Gerät: Handy ab 07:00 nicht angeschlossen |
| N61 | Unterlagen: STORY.md, WELTEN.md, CURRENT_STATE, NEXT_SESSION, Store-Text | Leitung | ✅ außer Store-Text (→ NEXT_SESSION) |
| N62 | validate grün, Commits je Block | Leitung | ✅ 08:18 grün (7/7, APK 47,5 MB), 5 Commits |

## Verlauf
- 01:25 Start · 02:00 Team gestartet (Engine, UI, Figuren, W2/W3/W4 Assets)
- 07:37–08:15 Engine, UI, alle Blender-Welten fertig; Review Welt 1–4 (20 Befunde) umgesetzt
- 08:18 validate grün, Durchspielprobe aller Welten, Commits
- ca. 02:30–07:00 **Wochenlimit der API erreicht**: alle Agenten außer den Figuren mitten in der Arbeit gestoppt. 07:01 fortgesetzt, dazu W5, W6 und Texte gestartet.

## 5. Asset-Vertrag für die Welten 2–6 (verbindlich)

Vorbild in allem: die Dateien von Welt 1 (`assets/*/zimmer/`) und ihre Skripte
(`art_source/scripts/build_room_wg.py`, `build_einrichtung_wg_a.py`,
`build_stationen_wg.py`, `build_symbole_wg.py`, `build_figuren_wg.py`).
Koordinaten: Godot (x, y, z) = Blender (x, −z, y). Farben **linear**
(`linear = (c/255)^2,2`). Kanten abgerundet. Warm-helle Lichtstimmung wie die WG,
aber jede Welt mit eigener Materialpalette. Budgets wie Welt 1 (Möbel ≤ 600,
Station mit Ausstattung ≤ 3.000, Figur ≤ 1.200 Dreiecke).

```
assets/room/<welt>/     boden_<typ>_a.glb, boden_<typ>_b.glb   je Bodentyp der Zonentabelle, 1×1 m, EIN Mesh
                        wand_voll.glb, wand_voll_fenster.glb, wand_halb.glb, wand_halb_tuer.glb,
                        wand_sockel.glb, wand_sockel_tuer.glb, gelaender.glb,
                        pfosten_voll.glb, pfosten_halb.glb, pfosten_sockel.glb
                        (Maße und Ursprung exakt wie wg_wand_* / wg_pfosten_* in room/zimmer;
                         Innenseite bei lokal +z; Höhen 2,4 / 1,2 / 0,35 / 1,0 m)
                        dazu die 7 Altmodule raum_fliese_a, raum_fliese_b, raum_fliese_weg,
                        raum_wand, raum_wand_ecke, raum_wand_tuer, raum_wand_fenster
                        (für validate Schritt 7; dürfen einfache Varianten sein)
assets/world/<welt>/    einrichtung_<zone>.glb    je Zone, Ursprung = Zonenmitte, Stationsflächen frei
                        umgebung.glb              was um das Gebäude liegt (Hof, Straße, Stadt), Ursprung 0,0
                        fundament.glb             Sockel unter der ganzen Grundfläche (+1 m Rand)
                        fluss_teil.glb            das kleine Ding, das zwischen den Stationen fliegt (≤ 0,35 m)
assets/stations/<welt>/ <station>_basis.glb
                        <station>_ausstattung_<n>_<0|1|2|3>.glb   n = 1..3; Stufe 0 darf fehlen
                        dazu station_<id>_1/_2/_3.glb (Altmodelle, dürfen = Basis sein)
assets/ui/<welt>/       <station>.png, <station>_ausstattung_<n>_<1|2|3>.png   256×256, transparent
assets/characters/gemeinsam/   figur_kapuze_sitzend (Du), figur_kapuze, figur_cap (Mo),
                        figur_buckethat (Younes), figur_brille (Roman), figur_zopf (Selin)
art_source/scripts/     build_room_<welt>_neu.py, build_einrichtung_<welt>.py,
                        build_stationen_<welt>.py, build_figuren_crew.py
```

Die Zonen-IDs aus § 2 sind die Dateinamen der Einrichtungen. Zonen-IDs wie
`garage` oder `tresor` beschreiben Orte, keine Spielrollen, und liegen nur in
Daten und Assets (nie im Code).

## 6. Regeln fürs Team
- **Schreibrechte sind getrennt.** Jeder Agent bekommt seine Ordner. `worlds.json`
  schreibt immer nur **ein** Agent zur selben Zeit (Integration).
- Blender-Agenten: kein Godot, kein `validate.ps1`, kein git. Vorschau-Renders
  ansehen, mindestens zwei Korrekturrunden.
- Code-Agenten: Tests grün halten, `validate.ps1 -SkipBuild` erst, wenn die
  Leitung sagt, dass niemand sonst schreibt. Sonst gezielte Testläufe.
- Regel D3 gilt: keine Themenwörter in Code und Dateinamen.

## Engine-Notizen (N02)

Stand 07:40. Alle sechs Welten laufen im Tiefenmodus allein aus Daten.
Übersichten für das Team: `docs/nacht/karten_welten.md` (Stationsflächen, Türen,
Wege, Figuren), `docs/nacht/ids_welten.md` (Ziele, Nachrichten, Bereiche).

### Datenwege (neu)
- **Module je Welt:** `worlds.json › module`. Fehlt es, gilt die WG-Tabelle
  (`wg_*`, Welt 1). `"standard"` = Asset-Vertrag § 5 (`boden_<typ>_a/_b`,
  `wand_*`, `pfosten_*`, `gelaender`). Ein Dictionary überschreibt einzelne Typen.
  Fehlt einer Welt ein Standardmodul, springt das WG-Modul ein — mit `push_warning`.
- **Sperren** (`sperre_*`): erst `assets/world/<welt>/`, dann `assets/world/gemeinsam/`
  (dorthin kopiert). **Figuren** und **Kulisse**: erst eigene Welt, dann `gemeinsam/`.
- **Varianten** einer Einrichtung: `zone.varianten = {gesperrt, verfuegbar, gekauft}`
  (Endungen). Welt 1 trägt das jetzt für das freie Zimmer; die alte
  Dateisuche nach `_bewohnt` ist entfernt.
- **Licht:** `licht` ist ein Name aus `licht_vorlagen` (oben in worlds.json) oder
  ein Dictionary (`hintergrund`, `umgebung`, `umgebung_energie`, `sonne`,
  `sonne_energie`, `schatten`, `sonne_richtung{x,y}`), das die warme Vorlage
  überschreibt. Kein Tonemapping.
- **Fluss-Teil:** `assets/world/<welt>/fluss_teil.glb` fliegt statt des Kärtchens
  (dreht sich langsam); ohne Datei bleibt das Kärtchen.
- **Figuren:** `darsteller` darf eine Liste sein (altes Objekt gilt weiter).
  `ab` = `{bereich}` oder `{station, platz, stufe}` oder `{station, stufe}` oder eine
  volle Bedingung mit `typ`. Bewohner kennen zusätzlich `ab` und `bis`
  (`bis` blendet sie aus, sobald erfüllt). `solange_nicht_verfuegbar` bleibt für
  Welt 1 — für Bereiche ohne Voraussetzung taugt es nicht (sie sind ab Start
  verfügbar), deshalb `bis`.
- **Bedingungstypen neu:** `ausstattung_station`, `freigeschaltet`, `alle`
  (Missionen; Messwert = erfüllter Anteil).
- **Prüfschalter neu:** `--alle-welten` (mit `--durchspielen`: ganzer Bogen bis
  zum Abspann), `--bild <name>` (eigene Vorschaudatei).
- **Werkzeug neu:** `tools/welt_sim.gd -- <welt> …` spielt einzelne Welten bis
  100 % und listet die Zeitpunkte aller Ziele und Nachrichten.

### Sondermechaniken mit Abschluss „alles“ — was vereinfacht wurde
- **Welt 2 Limit:** unverändert (Obergrenze × Weltfaktor, Umbau als Kauf).
  Neu: Ziel `ziel_06` und Nachricht `nachricht_06` hängen am Umbau
  (`freigeschaltet unlock_umbau`). Das Limit zählt nicht zum Fortschritt und
  blockiert den Abschluss nie (Test). Der Simulator kennt den Umbau als Kauf
  und baut an der Wand nicht mehr über die Engpass-Abkürzung weiter.
  Obergrenze 25, Umbau 1.800 (je × Weltfaktor) → Umbau bei ~10 min.
- **Welt 3 Stammkunden:** neu im Kern. `sonder.grundeinnahme_aktiv` — die
  Sonderstation liefert eine eigene Einnahme je Sekunde
  (`basis_durchsatz × Stufe × Sterne × Ausstattung × Räume × grundeinnahme_wachstum^(Stufe−1)
  × Weltfaktor`), unabhängig von der Kette, auch offline. Kern erhalten („läuft
  weiter, wenn die Kette steht“); vereinfacht: kein wachsender Kundenstamm mit
  Verzögerung — der hätte jedem Kauf im Menü eine Mehreinnahme von 0 gezeigt.
  Das Stufenwachstum (1,13) ist nötig, weil eine linear wachsende Einnahme gegen
  exponentielle Kosten nach wenigen Stufen bedeutungslos wird.
- **Welt 4 Personen:** unverändert (Überlastung der Verarbeitung). Die drei
  Ausstattungsplätze des Packteams **sind** die Personen — jede eingestellte
  Person hebt die Leistung und damit die Überlastung auf. Keine Sackgasse: Am
  Ende stehen alle Stationen gleich hoch, die Last liegt unter der Schwelle.
- **Welt 5 Bestand:** zwei Korrekturen im Kern. (1) Die Sonderstation (Staking)
  wirkte im Bestand gar nicht — jetzt hebt `erloes_faktor` auch den Erlös je
  Bestand. (2) Mehreinnahme und Simulator rechnen mit dem **Gleichgewicht**
  (`GameCore.einkommen_ziel`), sonst brachte jeder Kauf rechnerisch null.
- **Welt 6 Risiko:** Ausschlag 1,3 → ohne Streuung sind ~12 % der Ticks
  **Verlust-Ticks** (`_verliere`: nie unter 0 € Kapital, netto gebucht, damit der
  Mittelwert ehrlich bleibt). Streuung 0,02 je Stufe; ab ~20 Stufen keine Verluste
  mehr. Missionen als Ziele: `ziel_11` Schmuck & Uhren (bereich_2 + Tresor-Platz),
  `ziel_17` alle Aktien (Depot-Ausstattung 30), `ziel_19` Goldbarren,
  `ziel_20` alle Immobilien (bereich_4 + Analyse-Ausstattung 30),
  `ziel_24` Kunst & Oldtimer (bereich_5 + Dividenden-Ausstattung 30).

### Balance (tools/balance_sim.gd, ohne Tipp-Momente)
Welt 2–6 sind aus `zimmer.json` erzeugt (Geld × 10^Index, weil der Kern den
Durchsatz mit `welt_faktor_pro_welt^Index` multipliziert), dazu je Welt die
Mechanik und kleine Stellschrauben.

| Welt | Abschluss | längste Kaufpause |
|---|---|---|
| zimmer | 81:20 (unverändert) | 303 s |
| auftrag | 62:06 | 238 s |
| webseiten | 64:19 | 314 s |
| buero | 61:58 | 238 s |
| produkt | 66:49 | 197 s |
| kapital | 69:31 | 186 s |

Nachtrag 08:15 (Review Welt 1–4): Ausstattungsplätze einer Station haben jetzt
eine Preisstaffel 1 : 3 : 9 (nach `ab_stufe`), Wachstum 2,75 statt 2,25 (Welt 3:
Ausstattung ×0,6, Stationen ×1,2, späte Räume ×1,2–1,3). Vorher lagen Plätze bis
Faktor 60 auseinander. Licht der Welten 3–6 gedämpft (Welt 6 überstrahlte).
Verlust-Ticks melden sich eigens über `EventBus.loss_tick`; die Anzeige
„-1000 Mrd“ kam aus der UI, die Käufe als Verlust zählte (Wunsch an die UI).
Stationsring auf 1,04 m (bleibt in der 2,2-m-Fläche). Kamera fährt jetzt auch zu
Räumen, die über Schild, Ausbauliste oder Karte geöffnet werden.

Nachtrag 08:45 (Review W10): Kamera der Welten 2–6 startet hinter der
Startzone (z 1,0 bzw. 1,8), damit die Startzone mittig zwischen Kopfzeile und
Menüleiste steht; `zoom_start` 14/15, `zoom_max` 24/26 statt 32/36. Welt 1
unverändert. Stationen dürfen `"schild": {"x", "z"}` tragen (Versatz für Schild,
Ring, Treffer, Fokus; `WorldData.stationen_anzeige`). Gemessen mit
`tools/stations_mitte.gd`: Die Modelle stehen fast mittig (≤ 0,54 m), Versätze
nur ab 0,25 m eingetragen (W2 processing/transport, W3 intake, W5 processing,
W6 special).

### Offen
- Welt 3 ist sehr empfindlich gegenüber `grundeinnahme_wachstum`
  (1,14 → 58 min, 1,13 → 65 min, 1,10 → 127 min). Mit echten Spielern messen.
- Station-, Einrichtungs- und Bodenmodelle der Welten 3–6 fehlen noch
  teilweise → laute Warnungen, Ersatzböden aus Welt 1, Stationen nur als Schild.
- `WeltTexte.ziel` soll Zieltexte je ID bevorzugen (Wunsch an die UI,
  `docs/nacht/wuensche_engine_an_ui.md`).
