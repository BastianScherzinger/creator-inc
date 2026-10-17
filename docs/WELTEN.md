# WELTEN — Bauplan

**Stand:** 2026-09-17 · ADR-022 (neuer Bogen „Vom Zimmer zum Portfolio“)

Sechs Welten, eine Mechanik. Dieses Dokument ist die **verbindliche
Spezifikation** für Assets, Themendaten und Balance. Wer eine Welt baut, baut
sie hiernach. Die Geschichte steht in `docs/STORY.md`, die Einzelheiten der
Nacht in `docs/NACHT_PLAN.md` und `docs/nacht/`.

---

## 0. Was in jeder Welt gleich ist

Die Engine kennt fünf Stationen mit **neutralen IDs** (`Ids.CHAIN`). Sie
bedeuten in jeder Welt etwas anderes, aber ihre Funktion ist identisch:

| ID | Funktion | Regel |
|---|---|---|
| `station_intake` | erzeugt Nachschub | Beginn der Kette |
| `station_buffer` | puffert | zwischen Annahme und Arbeit |
| `station_processing` | erzeugt Erlös | Ende der Kette |
| `station_transport` | **multipliziert die ganze Kette** | frei mit `bereich_1` |
| `station_special` | Sondermechanik der Welt | frei mit `bereich_3` |

**Der Durchsatz ist das Minimum der drei Kettenglieder.** Das ist der Engpass,
und er ist immer sichtbar.

Jede Welt hat **fünf kaufbare Bereiche** mit derselben Rolle:
`bereich_1` schaltet transport frei · `bereich_2` alle ×1,25 ·
`bereich_3` schaltet special frei · `bereich_4` eine Station ×1,5 ·
`bereich_5` alle ×1,5 (erst nach `bereich_4`). Dazu kommt eine offene Zone
als Deko. Jede Station hat **drei Ausstattungsplätze** mit vier Modellstufen
(Namen: `docs/nacht/ausstattung_welten.md`). 25 Ziele, 15 Nachrichten je Welt
(IDs und Auslöser: `docs/nacht/ids_welten.md`).

**Regel D3 gilt ausnahmslos:** Kein thematischer Begriff außerhalb von
`data/themes/<welt>/` und `data/i18n/`. Die Welt-IDs bleiben die alten
(Spielstände, Tests, Ordner), ihr Inhalt ist neu.

**Ordnerkonvention je Welt** (`<welt>` = Themen-ID):

```
project/data/themes/<welt>/theme.json     alle Texte
project/data/balance/<welt>.json          alle Zahlen
project/data/worlds/worlds.json           Karte, Zonen, Stationspositionen
project/assets/room/<welt>/               Raummodule
project/assets/world/<welt>/              Einrichtungen, Requisiten
project/assets/stations/<welt>/           Stationen und Ausstattung
project/assets/characters/gemeinsam/      Figuren aller Welten
```

---

## Überblick

| # | ID | Titel | Figur | Akzent | Besonderheit |
|---|---|---|---|---|---|
| 1 | `zimmer` | Die WG | Mo | Blau `#3D7BFF` | — (die Grundmechanik) |
| 2 | `auftrag` | Das Studio | Younes | Pink `#FF4FA3` | Speicher-Limit, Umbau |
| 3 | `webseiten` | Der Merch-Laden | Roman | Orange `#FF7A1A` | Stammkunden |
| 4 | `buero` | Das Lager | Roman | Türkis `#12B5A5` | Personen, Überlast |
| 5 | `produkt` | Die Farm | Selin | Violett `#8B5CF6` | Bestand, Verzögerung |
| 6 | `kapital` | Das Portfolio | Selin + alle | Gold `#F2B200` | Risiko, Missionen, Abspann |

Die Spielfigur ist „Du“: Kapuze, gesichtslos, sitzt überall am Schnitt-,
Pack- oder Kontrollplatz (`station_processing`).

---

## Welt 1 — `zimmer` · „Die WG“ · mit Mo

> Dein erster Clip hat drei Aufrufe. Ziel: der erste Gaming-PC.

**Frage:** Reicht ein Handy auf einem Bücherstapel?

| Station | Name |
|---|---|
| intake | **Idee** |
| buffer | **Aufnahme** |
| processing | **Schnitt** |
| transport | **Upload** |
| special | **Der Stream** |

**Karte:** eine ganze WG. Start im eigenen Zimmer · `flur` (Upload) ·
`kueche` (×1,25) · `wohnzimmer` (Stream) · `balkon` (Aufnahme ×1,5) ·
`freies_zimmer` (Tobis Zimmer, ×1,5) · offen: `bad`, `miras_zimmer`.
**Nebenfiguren:** Mira, Tobi. **Ende:** Der Gaming-PC leuchtet.
Details: `docs/WELT1_TIEFE.md`.

---

## Welt 2 — `auftrag` · „Das Studio“ · mit Younes

> Eine Garage im Hinterhof, ein Rolltor, das klemmt.

**Frage:** Kann man gut sein, wenn man schnell sein muss?

| Station | Name | Was man sieht |
|---|---|---|
| intake | **Konzept** | Stehtisch vor der Storyboard-Wand |
| buffer | **Dreh** | Set-Podest, Kamera auf Schiene |
| processing | **Schnitt** | der Gaming-PC aus Welt 1, jetzt mit Farbkorrektur |
| transport | **Render-Server** | Container im Hof |
| special | **Sponsoren** | Lounge im Greenscreen-Raum |

**Karte** (x −10…10, z −8…6): Start `garage` · `hof` (Render-Server) ·
`requisite` (×1,25) · `greenscreen` (Sponsoren) · `dach` (Dreh ×1,5) ·
`kino` (×1,5) · offen: `younes_ecke`.

**Besonderheit: Speicher-Limit.** Rohmaterial füllt die Platten. Ab einer
Grenze bringt Ausbauen nichts mehr; erst der Umbau „Render-Server mit Archiv“
(`unlock_umbau`, Ziel 06) hebt sie auf. Er ist jederzeit kaufbar, das Limit
blockiert den Abschluss nie.

**Ende:** Younes sagt zum ersten Mal „gut so“. Roman meldet sich.

---

## Welt 3 — `webseiten` · „Der Merch-Laden“ · mit Roman

> Ein Eckladen mit Schaufenster und einer Werkstatt dahinter.

**Frage:** Kauft das jemand, weil er dich mag, oder weil es gut ist?

| Station | Name | Was man sieht |
|---|---|---|
| intake | **Design** | Zeichentisch |
| buffer | **Druck** | Werkbank mit Presse |
| processing | **Verpacken** | Packtisch |
| transport | **Versand** | Paketregal |
| special | **Der Drop** | Bühne mit Kleiderstange |

**Karte** (x −10…10, z −8…6): Start `werkstatt` · `laden` (Versand) ·
`lager` / „Der Keller“ (×1,25) · `showroom` (Drop) · `fotostudio`
(Druck ×1,5) · `siebdruck` / „Das Hinterzimmer“ (×1,5) · offen: `romans_buero`.

**Besonderheit: Stammkunden.** Der Drop hebt nicht den Preis je Stück,
sondern bringt eine laufende Grundeinnahme, unabhängig von der Kette, auch
offline.

**Ende:** Jemand trägt deinen Hoodie vor der Tür. Roman hat eine Halle gefunden.

---

## Welt 4 — `buero` · „Das Lager“ · mit Roman

> Eine Halle am Stadtrand. Vier Shops, ein Förderband und Roman mit Klemmbrett.

**Frage:** Kann man abgeben?

| Station | Name | Was man sieht |
|---|---|---|
| intake | **Bestellungen** | Stehpult mit vier Shop-Bildschirmen |
| buffer | **Hochregal** | Regal, Stapler, Scanner |
| processing | **Packteam** | Packtischreihe, drei Plätze = drei Personen |
| transport | **Förderband** | Bandsegment im Gang |
| special | **Großhändler** | Besprechungstisch |

**Karte** (x −12…12, z −9…7): Start `packhalle` · `gang` (Förderband) ·
`wareneingang` (×1,25) · `buero_shops` / „Das Händler-Büro“ (Großhändler) ·
`hochregal` (Regal ×1,5) · `rampe` (×1,5) · offen: `pausenraum`.

**Besonderheit: Personen.** Das Packteam sind Menschen. Kommt mehr herein, als
das Team schafft, wird **weniger** fertig. Wer das Team nachzieht (Stufen oder
Personen), hebt die Überlast sofort auf.
**Nebenfigur:** Jana, die erste Packerin (nur im Chat).

**Ende:** Das Lager läuft auch nachts. Selin schreibt von einer unbekannten Nummer.

---

## Welt 5 — `produkt` · „Die Farm“ · mit Selin

> Eine alte Fabrikhalle, Backstein, Sheddach. Selin steht im Stromkasten.

**Frage:** Was, wenn die Arbeit von allein weiterläuft?

| Station | Name | Was man sieht |
|---|---|---|
| intake | **Strom** | Verteilerkasten |
| buffer | **Rigs** | Gitterregal mit Rechenkarten |
| processing | **Blöcke** | Kontrollpult |
| transport | **Kühlung** | Lüftungskanal |
| special | **Staking** | Pult mit Knoten und Kurve |

**Karte** (x −12…12, z −9…7): Start `halle` · `kabeltrasse` (Kühlung) ·
`trafo` (×1,25) · `kontrollraum` (Staking) · `solardach` (Strom ×1,5) ·
`rackhalle_2` (×1,5) · offen: `selins_labor`.

**Besonderheit: Bestand.** Der Durchsatz erzeugt keinen Erlös, sondern
Bestand, der pro Sekunde auszahlt und von allein schrumpft. Jeder Ausbau
wirkt mit rund 30 Sekunden Verzögerung. Staking hebt den Erlös je Bestand.

**Grenze:** Keine echten Coin-Namen. Selin sagt es selbst: ein Spiel mit Zahlen.

**Ende:** Die Farm summt, niemand muss danebenstehen.

---

## Welt 6 — `kapital` · „Das Portfolio“ · mit Selin und allen

> Ganz oben über der Stadt. Glaswände, ein leerer Tresor, eine Liste von Selin.

**Frage:** War das das Ziel?

| Station | Name | Was man sieht |
|---|---|---|
| intake | **Marktdaten** | Designertisch mit Bildschirmen |
| buffer | **Analyse** | Glastisch mit Kurven |
| processing | **Depot** | Ledersessel: Aktien, Anleihen, Rohstoffe |
| transport | **Streuung** | Globus-Podest |
| special | **Dividenden** | Sideboard im Boardroom |

**Karte** (x −12…12, z −9…7): Start `lounge` · `galerie` (Streuung) ·
`tresor` (Schmuck & Uhren, ×1,25) · `boardroom` (Dividenden) ·
`immobilien` (Stadtmodell, Analyse ×1,5) · `kunstsalon` (Kunst & Oldtimer,
×1,5) · offen: `dachterrasse` (Party am Ende).

**Besonderheit: Risiko.** Ein Tick kann negativ sein. Streuung senkt den
Ausschlag, nicht den Mittelwert; ab rund 20 Stufen gibt es keine
Verlust-Ticks mehr.

**Missionen** (als Ziele): 11 Schmuck & Uhren · 17 Alle Aktien im Depot ·
19 Goldbarren-Vitrine · 20 Alle Immobilien · 24 Kunst & Oldtimer.

**Grenze, die nicht überschritten wird:** Keine echten Firmen, kein
Glücksspiel, keine Lootboxen, keine Anlageberatung. Der Abspann sagt das
ausdrücklich (Pflichthinweis).

**Ende:** Alle sitzen auf der Dachterrasse. Abspann: „Der Zähler läuft weiter.
Du musst nicht mehr hinsehen. Angefangen hat es mit drei Aufrufen.“
Danach Neuanfang mit dauerhaften Multiplikatoren.

---

## Figuren je Welt

| Welt | an einer Station | im Chat |
|---|---|---|
| 1 | Mo | Mo, Mira, Tobi, Dein Kanal |
| 2 | Younes | Younes, Mo, Dein Kanal, eine Marke |
| 3 | Roman, später Younes | Roman, Mo, Younes, Dein Shop, eine Kundin |
| 4 | Roman, später Younes | Roman, Mo, Younes, Dein Shop, ein Großhändler, Selin (unbekannte Nummer) |
| 5 | Selin, später Roman | Selin, Roman, Mo, Dein Kanal |
| 6 | Selin, Roman, Younes, Mo | Selin, Roman, Mo, Younes, Dein Kanal |

Positionen und Dateien: `docs/nacht/karten_welten.md`.

## Eine Welt gilt als fertig, wenn …

1. sie ohne eine einzige Ersatzwelt-Warnung startet,
2. jede Nachrichten- und Ziel-ID einen Text hat und jeder Absender einen Namen,
3. der Balance-Simulator Abschluss 100 % im Zielkorridor meldet,
4. ein angesehener Screenshot jede Zone, jede Station und den Abschluss zeigt.
