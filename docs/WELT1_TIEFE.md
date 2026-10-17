# WELT 1 IN DIE TIEFE — Bauplan und Taskliste

**Stand:** 2026-09-11 · **Status:** in Arbeit · Entscheidung: ADR-021

> Auftrag: Welt 1 so ausbauen, dass sie mit echten Idle-Tycoons mithalten
> kann. Große Karte, die man schwenken und zoomen kann. Ein Menü unten wie in
> den Spielen des Genres. Alles auf der Karte ist antippbar und öffnet ein
> eigenes kleines Menü. Jede Station hat Ausstattung, die man einzeln kauft
> und hochlevelt („auf dem Schreibtisch einen neuen Bildschirm kaufen").
> Wer in Welt 1 **alles** gekauft und ausgebaut hat, kommt in Welt 2.
>
> Vorbild für Tiefe und Bedienung: *Idle Bank Tycoon*. Ziel ist nicht die
> Kopie, sondern dieselbe Qualität mit einer Geschichte, die mehr trägt.

Dieses Dokument ist **die Arbeitsgrundlage** für diese Phase. Neue Ideen
landen unten in der Taskliste (§ 12), nicht im Kopf.

Konzeptbilder (per Bildgenerator, nur als Stilvorlage, nicht im Spiel):
`art_source/konzept/wg_karte.png` · `art_source/konzept/ui_stationsmenue.png`

---

## 1. Was sich ändert — in einem Absatz

Aus dem 14-m²-Zimmer wird **die ganze WG**. Am Anfang gehört dem Spieler nur
das eigene Zimmer; der Rest der Wohnung ist da, aber abgesperrt, dunkel, mit
Kartons und Absperrband. Geld wird nicht mehr nur in Stufen gesteckt, sondern
in **drei Dinge**: Stufen einer Station, **Ausstattung** an der Station (mit
eigenen Stufen und sichtbarem Modell) und **Räume** der Wohnung. Ein
**Ziele-Menü** führt durch die Welt, ein **Handy** erzählt die Geschichte in
Nachrichten, **Tipp-Momente** auf der Karte belohnen Aufmerksamkeit. Welt 1
ist abgeschlossen, wenn der Fortschritt bei 100 % steht.

---

## 2. Die Psychologie — warum man weiterspielt

Jedes Element hat einen Grund. Kein Element nutzt Verlustangst oder Druck;
die Regel aus `GAME_DESIGN.md` gilt weiter: **Ein Spiel, das bestraft, wenn
man lebt, wird deinstalliert.**

| Mechanismus | Umsetzung | Warum es wirkt |
|---|---|---|
| **Zielgradient** | Weltfortschritt in %, oben immer sichtbar, drei Teilbalken (Stationen · Ausstattung · Räume) | Je näher ein Ziel, desto stärker der Zug. 87 % lässt niemand liegen. |
| **Sichtbarer Besitz** | Jeder Kauf verändert das Modell auf der Karte: der zweite Monitor steht wirklich da | Was man sieht, gehört einem. Eine Zahl gehört niemandem. |
| **Offene Schleifen** | Gesperrte Räume sind sichtbar, mit Preis. Ausstattungs-Karten zeigen die nächste Stufe schon als Silhouette | Unerledigtes bleibt im Kopf (Zeigarnik). |
| **Nahziel statt Fernziel** | Immer genau drei Ziele im Ziele-Menü, das erste fast erreicht | Das Fernziel ist zu weit, das Nahziel ist jetzt. |
| **Belohnung zum Abholen** | Erfüllte Ziele werden **eingelöst** (Tippen), nicht still verbucht | Der Moment des Abholens ist die Belohnung. |
| **Variable Belohnung** | Tipp-Momente („Ein Clip zieht an") erscheinen zu zufälligen Zeiten über Stationen | Unvorhersehbares hält die Aufmerksamkeit — ohne Einsatz, ohne Glücksspiel. |
| **Kompetenz** | Der Engpass bleibt der Kompass: rot, gestaut, im Menü markiert | Wer versteht, warum es schneller wird, fühlt sich klug, nicht bloß reich. |
| **Erzählte Neugier** | Nachrichten im Handy, rotes Abzeichen bei Ungelesenem, Geschichte wird durch Fortschritt freigeschaltet | „Was schreibt Mira als Nächstes?" ist ein Grund, der keine Zahl ist. |
| **Meilenstein-Feier** | Sterne an Stationen und Ausstattung, bei jedem Stern ein kurzer Auftritt | Treppen statt Rampe: Stufen, auf denen man kurz steht. |
| **Geschenk statt Schuld** | Offline-Ertrag wird als Geschenk gezeigt, nie als verpasster Gewinn | bewährt, bleibt |

**Was bewusst fehlt:** tägliche Anmeldepflicht mit Serienverlust,
Energie-Systeme, Countdown-Angebote, Premiumwährung, gekaufter Fortschritt.
Werbung bleibt Angebot (`Der Algorithmus`), nie Bedingung.

---

## 3. Die Karte — die WG

### 3.1 Grundriss

Raster in Metern, Feldmitten ganzzahlig. Grundfläche **x −11…11 (23) ×
z −9…7 (17)** — fast viermal so groß wie das alte Zimmer (11 × 9), dazu der
Garten drumherum. Die Kamera schaut aus Richtung (+1, +1, +1): **„oben im
Bild" ist die Weltrichtung (−1, 0, −1).**

```
            x: −11 ………… −3 │ −2 ……… 3 │ 4 …… 7 │ 8 …… 11
z −9…−4   WOHNZIMMER (9×6)  │ KÜCHE    │ BAD    │ BALKON
          [bereich_3]       │ [ber._2] │ offen  │ [bereich_4]
          ──────────────────┴──────────┴────────┴──────────
z −3…0    FLUR (23×4)  [bereich_1]                  Haustür →
          ────────────────┬───────────┬────────────────────
z  1…7    FREIES ZIMMER   │ DEIN      │ MIRAS ZIMMER
          (8×7)           │ ZIMMER    │ (8×7) offen, Deko
          [bereich_5]     │ (7×7) START│
```

| Zone | Felder | Boden | Rolle |
|---|---|---|---|
| Dein Zimmer | x −3…3, z 1…7 | helles Holz | **Start.** Idee, Aufnahme, Schnitt |
| Flur | x −11…11, z −3…0 | dunkleres Holz | `bereich_1` · Upload am Router |
| Küche | x −2…3, z −9…−4 | Fliesen hell | `bereich_2` · Bonus „Nervennahrung" |
| Wohnzimmer | x −11…−3, z −9…−4 | helles Holz, Teppich | `bereich_3` · Der Kommentar (Sofa) |
| Balkon | x 8…11, z −9…−4 | Holzdeck | `bereich_4` · Bonus „Tageslicht" |
| Freies Zimmer | x −11…−4, z 1…7 | helles Holz | `bereich_5` · wird zum Studio |
| Bad | x 4…7, z −9…−4 | blaue Fliesen | offen, Deko, Figuren gehen hin |
| Miras Zimmer | x 4…11, z 1…7 | helles Holz | offen, Deko, Mira wohnt dort |

### 3.2 Wände

Puppenhaus-Schnitt wie im Konzeptbild: Außenwände hinten hoch, innen halbhoch,
vorn nur ein Sockel. Wände liegen auf Feldkanten (x.5 / z.5).

| Typ | Höhe | Wo |
|---|---|---|
| `voll` | 2,4 m | Rückseite (z −9,5) und linke Seite (x −11,5), mit Fenstern |
| `halb` | 1,2 m | alle Innenwände |
| `sockel` | 0,35 m | Vorderseite (z 7,5) und rechte Seite (x 11,5) |
| `gelaender` | 1,0 m | Balkon außen |

Türlücken (1 Feld breit, mit Türrahmen): Flur→Wohnzimmer x −9, →Küche x 0,
→Bad x 5, →Balkon x 9 (Glastür) · Flur→Freies Zimmer x −8, →Dein Zimmer x 0,
→Miras Zimmer x 7 · Wohnzimmer↔Küche z −5 · Haustür rechts z −1.

Die genaue Liste steht in `data/worlds/worlds.json` unter `grundriss` — das
hier ist die Absicht, dort ist die Wahrheit.

### 3.3 Gesperrte Räume

Ein nicht gekaufter Bereich ist **da, aber nicht deins**: Boden und Möbel
dunkel eingefärbt, Kartonstapel, gelb-schwarzes Absperrband, darüber ein
schwebendes Schloss-Schild mit Preis. Antippen öffnet das Bereichsmenü.
Beim Kauf: Band fällt, Kartons verschwinden, Licht geht an (0,8 s), Konfetti
aus Staub, Nachricht aufs Handy.

### 3.4 Stationen auf der Karte

| Station | Name (Thema) | Ort | Position (x, z) | blickt nach |
|---|---|---|---|---|
| `station_intake` | Idee — Pinnwand mit Regal | Dein Zimmer, hinten links | (−2,0, 1,7) | +z |
| `station_processing` | Schnitt — Schreibtisch | Dein Zimmer, hinten rechts | (1,8, 1,8) | +z |
| `station_buffer` | Aufnahme — Handy-Set mit Licht | Dein Zimmer, Mitte | (0,0, 4,6) | +x (Kamera links vom Set) |
| `station_transport` | Upload — Router-Regal | Flur, an der Wand | (2,6, −2,6) | +z |
| `station_special` | Der Kommentar — Sofa mit Couchtisch | Wohnzimmer | (−7,8, −6,2) | +x (Fernseher an der rechten Wand) |

Jede Station belegt höchstens **2,2 × 2,2 m** um ihren Ursprung. Diese Fläche
bleibt in den Raumeinrichtungen frei.

### 3.5 Leben auf der Karte

- **Die Spielfigur** sitzt am Schreibtisch: Kapuze, von hinten, **kein
  Gesicht** (ADR-021). Sie wippt beim Tippen, dreht sich beim Kauf kurz um.
- **Clips fließen** als kleine leuchtende Karten von Station zu Station
  (Idee → Aufnahme → Schnitt → Upload). Wo der Engpass ist, **stapeln sie
  sich sichtbar**. Das ersetzt die Zuschauer-Schlange der alten Welt 1.
- **Mira** (Mitbewohnerin, Dutt, Kopfhörer) und **Tobi** (Mitbewohner,
  Mütze, Kaffeebecher) laufen ihren Tagesablauf ab: Küche, Bad, Zimmer, Flur.
  Tobi wohnt im Freien Zimmer, bis er auszieht.
- **Ein Kumpel** steht als Darsteller am Aufnahme-Set, sobald das Licht
  Stufe 1 hat.
- **Tipp-Momente**: grüne Blasen über Stationen (siehe § 6).

Figuren erzeugen **kein Geld** (Regel unverändert).

---

## 4. Die Wirtschaft von Welt 1

### 4.1 Station

- Stufen **1 … `max_stufe`** (Kette 50, Upload und Kommentar 30).
- Meilenstein alle 10 Stufen = **ein Stern**, Leistung ×`meilenstein_faktor`.
- Kaufen in **×1 / ×10 / MAX** (MAX = so viele, wie das Geld reicht).

### 4.2 Ausstattung

Jede Station hat **drei Ausstattungsplätze** (`ausstattung_1…3`), jeder mit
Stufen **0 … 10**.

- Stufe 0 = Anfangszustand (das Handy auf dem Bücherstapel).
- Freigabe ab einer Stationsstufe (`ab_stufe`) — sichtbar als Schloss mit
  „ab Stufe 20".
- Jede Stufe erhöht die Leistung der Station: Faktor
  `1 + bonus_je_stufe × stufe`.
- **Drei sichtbare Modellstufen** bei Stufe 1, 4 und 8 (= die drei Sterne
  der Ausstattung). Stufe 0 hat ein eigenes Modell oder keins. Jeder Stern
  multipliziert zusätzlich mit `stern_faktor` (1,2): Das neue Modell ist auch
  in der Kasse ein Ereignis.
- Kosten: `basis_kosten × wachstum^stufe`.

### 4.3 Räume (Bereiche)

Einmalkauf. Ein Bereich kann eine Station freischalten (`schaltet_frei`)
und/oder einen **dauerhaften Faktor** geben (`bonus`: auf alle Stationen
oder auf eine).

| Bereich | schaltet frei | Bonus |
|---|---|---|
| `bereich_1` Flur | `unlock_transport` (Upload) | — |
| `bereich_2` Küche | — | alle ×1,5 |
| `bereich_3` Wohnzimmer | `unlock_special` (Kommentar) | — |
| `bereich_4` Balkon | — | Aufnahme ×2 |
| `bereich_5` Freies Zimmer | — | alle ×2 |

Ein Bereich kann eine Voraussetzung haben (`nach`): Das Freie Zimmer gibt es
erst, wenn Tobi auszieht — ausgelöst durch den Balkon.

### 4.4 Weltabschluss

Welt 1 ist **fertig**, wenn

- alle Stationen auf `max_stufe`,
- alle Ausstattung auf Stufe 10,
- alle Bereiche gekauft sind.

**Fortschritt** = Mittel aus drei Anteilen (Stufen · Ausstattungsstufen ·
Bereiche). Drei gleich gewichtete Balken, weil sonst die 230 Stationsstufen
die 5 Räume unsichtbar machen würden.

Bei 100 % erscheint der Abschluss (statt der alten Stufen-Schwelle): kurze
Feier, letzte Nachricht, dann der Weltwechsel-Bildschirm.

Welten **ohne** `max_stufe` und Ausstattung (heute 2 bis 6) funktionieren
unverändert über `unlock_world_2`. Sie ziehen später nach (§ 12).

### 4.5 Zielzeit

| Messpunkt (Simulator, aktiv, ohne Werbung, ohne Tipp-Momente) | Ziel |
|---|---|
| erster Kauf | < 15 s |
| erste Ausstattung | < 90 s |
| Flur gekauft | 3–5 min (gemessen: 3:23) |
| Wohnzimmer (Kommentar) | 20–30 min (gemessen: 24:03) |
| **Welt 1 abgeschlossen** | **75–110 min** (gemessen: 81:20) |
| längste Wartezeit auf *irgendeinen* sinnvollen Kauf | ≤ 90 s in den ersten 15 min, ≤ 310 s danach — das Sparen auf einen Raum darf fünf Minuten dauern (gemessen: 49 s / 303 s) |

Mit Offline-Ertrag, Tipp-Momenten und Zielen ist das in echter Spielzeit ein
Nachmittag oder zwei Abende. Das ist die Größenordnung der ersten Bank in
Idle Bank Tycoon.

---

### 4.6 Was die Messung gelehrt hat

- **Gleichstand am Engpass lähmt einen naiven Spieler.** Stehen zwei
  Kettenglieder gleichauf, bringt jedes einzeln exakt null. Der erste
  Simulator hat deshalb nach vier Minuten aufgehört zu kaufen. Ein Mensch
  sieht das Rot und baut beide aus — der Simulator tut das jetzt auch.
- **Der Stern-Faktor verdreifacht das Tempo.** Mit ihm war die Welt in 26
  Minuten durch. Erst steileres Kostenwachstum (Stationen 1,27, Ausstattung
  2,35) hat die Kurve auf rund 80 Minuten gezogen, ohne den Einstieg zu bremsen.
- **Die Sonderstation brauchte eine Wirkung.** Vorher schaltete sie nur
  Großaufträge frei; in einer Welt, die man durch *alles* Kaufen abschließt,
  wären das dreißig wirkungslose Pflichtkäufe gewesen. Jetzt hebt sie den
  Erlös je Clip.
- **Stationen wurden bisher in der Darstellung freigeschaltet.** Der
  Simulator hat Upload und Kommentar deshalb nie mitgerechnet. Das liegt jetzt
  im Kern.

Werkzeuge: `tools/abschluss_sim.gd` (Teil von `balance_sim.gd`),
`tools/abschluss_tuning.gd` (Varianten nebeneinander).

## 5. Ziele

Ein fester Pfad aus rund 25 Zielen je Welt. **Immer drei sichtbar.** Ein
erfülltes Ziel bleibt stehen, bis es eingelöst wird (Tippen, Münzregen).

Bedingungstypen: `station_stufe` · `ausstattung_stufe` ·
`ausstattung_gesamt` · `bereich` · `verdient` · `momente` · `sterne`.
Belohnung: `sekunden` Einkommen (skaliert mit dem Spiel), mindestens
`minimum`.

Zahlen in `data/balance/zimmer.json` → `ziele`, Texte im Thema → `ziele`.

---

## 6. Tipp-Momente

- Alle 40–90 s (Zufall mit festem Startwert) erscheint über einer
  freigeschalteten Station eine grüne Blase.
- Sie bleibt 20 s. Antippen = **30 s Einkommen** (mindestens 5 €).
- Nicht angetippt: Sie verschwindet leise. **Keine Strafe, kein Zähler, der
  „verpasst" sagt.**
- Höchstens eine gleichzeitig. Offline gibt es keine.

---

## 7. Das Handy — Geschichte in Nachrichten

Nachrichten werden durch Ereignisse ausgelöst (Stufe, Kauf, Bereich,
Verdienst, Ziel). Absender: **Plattform**, **Mira**, **Tobi**,
**der Kommentar**. Ungelesenes = rotes Abzeichen am Menüpunkt.

Der Bogen von Welt 1 in Nachrichten:

1. Plattform: Dein Clip hat drei Aufrufe.
2. Mira: warum ihre Lampe verkehrt herum in deinem Zimmer steht.
3. Tobi: ob du dir wirklich ein Stativ gekauft hast.
4. Plattform: die ersten hundert Follower.
5. Mira: Router im Flur, WLAN im Bad plötzlich gut. Danke?
6. Tobi: kocht für drei.
7. Plattform: tausend Aufrufe auf einem Clip.
8. **Der Kommentar**: eine Frage, keine Meinung.
9. Mira: die Nachbarn winken, seit du auf dem Balkon filmst.
10. Plattform: ein Clip geht durch die Decke.
11. Tobi: zieht zum Ersten aus — ob du sein Zimmer willst.
12. Mira: ein Studio. In einer WG. Okay.
13. Der Kommentar: 240 Euro. Wann kannst du anfangen? → Weltwechsel

**Tonregel unverändert:** trocken, nicht zynisch. Niemand wird belehrt.
Keine realen Namen von Firmen, Plattformen oder Personen.

---

## 8. Bedienung

### 8.1 Aufbau des Bildschirms

```
┌──────────────────────────────────────┐
│ (€) 12.480        [Welt 1 ▓▓▓░ 42 %] ⚙│  Kopfleiste
│     +125 /s                          │
│                                      │
│          K A R T E                   │  schwenken, zoomen, antippen
│   (Blasen, Schilder, Engpass-Ring)   │
│                                      │
├──────────────────────────────────────┤
│  Bottom Sheet (nur wenn offen)       │
├──────────────────────────────────────┤
│ Ausbau   Ziele   (⚡)   Handy   Laden │  Menüleiste
└──────────────────────────────────────┘
```

### 8.2 Kopfleiste
- Münze + Kapital (groß, zählt weich hoch) · darunter „+x /s"
- Weltfortschritt als Chip, antippbar → Fortschritts-Menü (drei Balken,
  Liste der Räume)
- Zahnrad → Einstellungen (Ton, später Sprache)

### 8.3 Menüleiste (unten, immer sichtbar)
| Punkt | öffnet | Abzeichen |
|---|---|---|
| **Ausbau** | Liste aller Stationen mit Schnellkauf | Zahl bezahlbarer Käufe |
| **Ziele** | drei aktive Ziele | Zahl einlösbarer Ziele |
| **⚡ Algorithmus** (Mitte, groß, rund) | Belohnungsschub | leuchtet, wenn bereit |
| **Handy** | Nachrichten | Zahl ungelesener |
| **Laden** | Laden (heute leer) | — |

### 8.4 Stationsmenü (Bottom Sheet)
Wie im Konzeptbild: Symbol, Name, „Stufe 17/50", Sterne, Balken bis zum
nächsten Stern · **grüner Ausbau-Knopf** mit Preis · Umschalter ×1/×10/MAX ·
drei **Ausstattungs-Karten** (Bild, Name der nächsten Stufe, Stufe x/10,
Sterne, Preisknopf oder Schloss „ab Stufe 20") · Engpass-Chip, wenn diese
Station bremst · Leistung jetzt → nach dem Kauf.

Die Kamera fährt beim Öffnen so, dass die Station **über** dem Sheet steht.

### 8.5 Bereichsmenü
Name, ein Satz, was dort entsteht, Bonus, Preis-Knopf. Gesperrt durch
Voraussetzung: statt Preis der Satz, worauf man wartet.

### 8.6 Stil
- Cremeweiße Karten (`#FFF6E9`), Rand warmes Beige, 20 px Radius, weicher
  Schatten
- Kaufen **Grün** `#3DBE4B` mit dunklerer Unterkante (Tiefe) · Aktion/Akzent
  **Gelb-Orange** `#FFB21E` · Warnung/Engpass **Rot** `#E5533C` · Text
  dunkelbraun `#3A2A1E`
- Schrift: **Nunito** (SIL OFL), Black für Zahlen und Titel, Bold für Text
- Tippen: 80 ms Eindrücken (Skalierung 0,94), Kauf: 350 ms Überschwingen
- Tippziele ≥ 48 dp, Safe Area oben

---

## 9. Kamera

- Grenzen **aus den Daten** (`kamera.grenzen` je Welt), mit weichem Rand statt
  harter Wand.
- Pinch-Zoom **um den Punkt zwischen den Fingern**, nicht um die Bildmitte.
- Mausrad am PC um den Mauszeiger.
- Schwung nach dem Loslassen.
- Antippen trifft über Strahl gegen Trefferkörper (Stationen, Bereiche,
  Blasen) statt über den Abstand zu fünf Punkten.
- Fokusfahrt (0,35 s) auf die gewählte Station.
- Zoomgrenzen je Welt aus den Daten.

---

## 10. Asset-Vertrag (für das Team)

**Alle Dateinamen neutral** (Regel D3): Sie beschreiben Silhouette oder Platz,
nie die Rolle. Farben in Blender **linear** eintragen (`linear = s^2,2`).

### 10.1 Stil (verbindlich)
- Warm, hell, freundlich — Konzeptbild `wg_karte.png`
- Kanten **abgerundet** (Bevel, 2 Segmente), keine harten Klötze
- Wandfarbe Creme `#F2E3CC`, Wandkappe Holz `#C8925A`, Böden warmes Holz
  `#D9A66B`/`#CF9A5E`, Fliesen `#E8E4DC`, Bad `#9CC7DE`, Deck `#8A6446`
- Pflanzen kräftiges Grün `#5DA84A`, Akzente gesättigt, aber nicht grell
- Budget: Möbel ≤ 600 Dreiecke, Station mit Ausstattung ≤ 3.000, Figur ≤ 1.200

### 10.2 Dateien
```
project/assets/room/zimmer/        Boden- und Wandmodule (MultiMesh-tauglich: EIN Mesh)
project/assets/world/zimmer/       Raumeinrichtungen: einrichtung_<zone>.glb (Ursprung = Zonenmitte)
                                   sperre_*.glb (Kartons, Band, Schild)
                                   garten_*.glb
project/assets/stations/zimmer/    <station>_basis.glb
                                   <station>_ausstattung_<n>_<modellstufe 0..3>.glb
project/assets/characters/zimmer/  figur_*.glb (Teile getrennt benannt: kopf, koerper, arm_l, arm_r, bein_l, bein_r)
project/assets/ui/zimmer/          <station>_ausstattung_<n>.png, 256 × 256, transparent
art_source/scripts/                build_*_wg.py (reproduzierbar, headless)
```

---

## 11. Architektur

- **Kern** (headless, getestet): `StationModel` bekommt `max_stufe` und
  Ausstattung; neu `AreaSystem` (Bereiche), `GoalSystem` (Ziele),
  `MomentSystem` (Tipp-Momente), `StoryFeed` (Nachrichten-Auslöser),
  `WorldCompletion` (Abschluss). `GameCore` bindet sie ein.
- **Spielstand Schema 3**: Ausstattung je Station, Bereiche, Ziele,
  Nachrichten. Migration v2 → v3 mit eingefrorener Fixture.
- **Darstellung**: `game/ui/` bekommt Theme, Kopfleiste, Menüleiste,
  Sheets. `game/world/` bekommt den Grundriss-Bauer mit Zonen und Wänden.
- **Balance-Simulator** spielt Welt 1 bis 100 % mit einer Kaufstrategie
  (bester Ertrag je Euro) und misst die Abschlusszeit.

---

## 12. Taskliste

Status: ⬜ offen · 🔶 in Arbeit · ✅ fertig

| # | Aufgabe | Status |
|---|---|---|
| 060 | Bauplan, Konzeptbilder, ADR-021 | ✅ |
| 061 | Kern: max_stufe, Ausstattung, Bereiche, Weltabschluss + Tests | ✅ |
| 062 | Kern: Ziele + Tests | ✅ |
| 063 | Kern: Tipp-Momente + Tests | ✅ |
| 064 | Kern: Nachrichten-Auslöser + Tests | ✅ |
| 065 | Spielstand Schema 3, Migration, Fixture v2 | ✅ |
| 066 | Balance Welt 1 neu, Simulator mit Kaufstrategie, Abschlusszeit | ✅ |
| 067 | UI-Grundlage: Theme, Schrift, Symbole | ✅ |
| 068 | Kopfleiste und Menüleiste | ✅ |
| 069 | Stationsmenü mit ×1/×10/MAX und Ausstattung | ✅ |
| 070 | Bereichsmenü, Schilder auf der Karte | ✅ |
| 071 | Ziele-, Handy-, Ausbau-, Fortschritts-Menü | ✅ |
| 072 | Kamera: Grenzen, Fokus, Pinch um Mittelpunkt, Strahl-Treffer | ✅ |
| 073 | Grundriss-Bauer: Zonen, Wände, gesperrte Bereiche | ✅ |
| 074 | Assets: Architektur und Raumeinrichtungen (Team) | ✅ |
| 075 | Assets: Stationen und Ausstattung 5 × 3 × 4 + Symbole (Team) | ✅ |
| 076 | Assets: Figuren (Team) | ✅ |
| 077 | Leben: Clip-Fluss, Mitbewohner-Wege, Figur am Platz | ✅ |
| 078 | Saft: Kauf-Animation, Sterne, Bereichs-Eröffnung, Abschluss-Feier, Klänge | 🔶 |
| 079 | Tutorial auf die neue Bedienung | ✅ |
| 080 | Durchspielprobe Welt 1 → Welt 2, Screenshots aller Menüs, Geräte-FPS | ✅ |
| 081 | Spieler-Blick: Kritik von außen, Korrekturschleifen | ✅ Runde 1 |
| 082 | Unterlagen, Stand, Store-Bilder | ⬜ |

### Neu aufgenommen während der Arbeit
| # | Aufgabe | Status |
|---|---|---|
| 083 | Zielkarte oben links auf dem Spielfeld (abgeschaut bei Idle Bank Tycoon) | ✅ |
| 084 | Durchspielprobe im echten Spiel (`--durchspielen`): Welt 1 → Welt 2 im Zeitraffer | ✅ |
| 085 | Vier neue Klänge: Münzen, Ausstattung platziert, Raum bezogen, Blase | ✅ |
| 086 | Fernseher im Wohnzimmer steht hinter der halben Wand und ist kaum zu sehen | ⬜ |
| 087 | Welt 2 hat die neue Bedienung, aber noch Licht und Stil der alten Welten | ⬜ |
| 088 | Glow für leuchtende Materialien (Bildschirme, Lichterketten) auf dem Gerät messen | ⬜ |

### Korrekturschleife 1 — Spieler-Blick von außen (2026-09-11)

Ein unabhängiger Reviewer (Rolle: Mobile-Designer und Vielspieler des Genres)
hat die Bilderserie `shots/serie/` bewertet. Umgesetzt:

| Befund | Änderung |
|---|---|
| „Leistung 60 → 120“ versprach Verdopplung, das Einkommen stieg um nichts | Menü zeigt die **echte Mehreinnahme** („+0,1 €/s“), Leistung nur noch klein in % (`GameCore.einkommen_danach`) |
| Man musste raten, was sich lohnt | Gelber Chip **„Lohnt sich“** auf dem Kauf mit der höchsten Mehreinnahme je Euro |
| Deaktivierte Knöpfe unlesbar (Weiß auf Beige, ~1,5 : 1) | Dunkle Schrift, dazu **„in 0:42“** bis bezahlbar |
| Die Namen der nächsten Modelle standen nirgends | Ausstattungskarten zeigen **„Zwei Monitore (Stufe 10)“** |
| Ziel 1 („Idee auf Stufe 5“) widersprach der Engpass-Lektion | Ziel 1 ist jetzt „10 Stufen insgesamt“ |
| Stufe 9 und 10 der Ausstattung änderten nichts Sichtbares | Modellstufen bei **1, 5 und 10** — der letzte Kauf zeigt das Endmodell |
| Beim Start sieben Dinge gleichzeitig | Während des Tutorials schweigen Zielkarte, Engpass-Hinweis und Abzeichen |
| Tutorialkarte lag auf der Station | Kamerafokus rechnet die Karte mit ein |
| Handy-Abzeichen blieb bei offenem Handy stehen | Gelesen beim Öffnen |
| Leerer Laden in der Menüleiste | Platz 5 ist **Fortschritt**; der Laden wohnt in den Einstellungen |
| Rote Scheiben wie Müll auf dem Boden, Rot bedeutete alles | Clips sind **weiße Kärtchen**, Rot gehört dem Engpass |
| Kaum Geld über der Kette | Jeder Clip, der die Kette verlässt, zeigt seinen Ertrag |
| Variable Belohnung nur im Zeitpunkt | **Große Momente** (8 %): Geschenk statt Herz, 2 Minuten Einkommen |
| Wichtigstes Schild am Rand abgeschnitten | Das Schild des nächsten kaufbaren Raums bleibt am Bildschirmrand |
| „…“ am freien Zimmer | „Tobi wohnt noch hier.“ |
| Unbezahlbare Preise in Grün | Braun, Grün heißt kaufbar |
| „0 %“ nach Minuten Arbeit | Unter 10 % mit Nachkommastelle |
| Weltwechsel verpuffte nach 80 Minuten | **Abschluss-Bildschirm**: Zahlen des Weges, letzte Nachricht als Chat, eigene Antwort „Morgen.“ |
| 9,2 Mio € auf dem Konto, Höhepunkt „240 Euro“ | Weltwechsel und letzte Nachricht nennen keinen Betrag mehr |
| Web-Entwickler-Bogen kam aus dem Nichts | Früh angedeutet: „ein halb fertiges Skript“, der Clip über das Skript, das Anzeigen ausliest |
| Grammatik („Der Flur beziehen“), „hochgegangen“, abgenutzter Witz | Texte korrigiert |

**Nicht übernommen:** Währung „Aufrufe“ statt € — ein Monitor, den man mit
Aufrufen bezahlt, wäre ein größerer Bruch als der, den es beheben soll.

**Gemessen danach:** Welt 1 ohne Tipp-Momente 81:20, mit jedem Moment
angetippt 61 min (Durchspielprobe). Aufmerksamkeit lohnt sich, ist aber keine
Pflicht.

### Ideen für später (nicht diese Phase)
- Paketbote bringt gekaufte Ausstattung durch die Haustür
- Tag-Nacht-Wechsel im Fenster je nach Uhrzeit
- Welten 2 bis 6 auf dieselbe Tiefe bringen (Ausstattung, Räume, Ziele)
- Spielfigur wechselt zwischen Stationen
- Haustier in der WG (Katze von Mira), das man antippen kann
