# DESIGN-OVERHAUL 2026-10-15 — „auf ein anderes Level“

**Auftrag (Bastian, Handy-Test 1.0.0):** Design und Stationen nicht besser, Menüs nicht selbsterklärend, zu wenig Dopamin, Story ohne Zug, man sieht nicht, wo man upgraden kann, zu wenig Ziele/Level — aber übersichtlich. Dazu Nachtrag: A/B-Vergleich je Kernbildschirm, Balance-A/B, mehr Parallelität (Welt-Polierer).
**Grundlage:** `handy1.png`/`handy2.png` (Gerät), `shots/serie/b_station.png`, `a_raum_gekauft.png`, `04_ziele.png`, `07_handy.png`; Referenzen unten. Regeln aus `CLAUDE.md` gelten (D3-Sperrwörter, Werte in `data/`, Kern rechnet, Screenshot nach jeder Änderung).

---

## 1. Referenzanalyse — was die Top-Spiele gleich machen

| Muster | Idle Miner Tycoon (Kolibri) | Eatventure (Lessmore) | My Perfect Hotel (SayGames) | Idle Bank / Supermarket / Hotel Empire (Codigames u. a.) |
|---|---|---|---|---|
| **Upgrade sichtbar in der Welt** | Jeder Schacht trägt ein **Level-Abzeichen** („Level 70“) direkt am Gebäude; weiße Pfeile zeigen auf die nächste Aktion; Zähler „50/7000“ über dem Bau; Knopf „New Shaft“ mit **Zeigehand** | Neue Stationen als **gepunktete Umrisse**, Kiste wackelt wenn kaufbar; „Perfect/Instant/Double“-Etiketten an Stationen; rotes „!“ am Seitenrand-Icon | Schwebende **„Upgrade · 10K“-Knöpfe** am Objekt; Ziel-Leiste oben „OBJECTIVES: Upgrade Hotel 9/84“ | Grüner Pfeil-Button über dem Raum; graue Räume = gesperrt, farbig = aktiv (PocketGamer rügt Zoning als Hauptproblem) |
| **Stations-Panel** | Porträt links, großer **grüner Hoch-Pfeil + „Next boost at level 100“**, 5 Wertzeilen mit **vorher → +Delta in Grün**, x1/x10/x50/Max, ein großer grüner „Upgrade · 31,5K“ | **Ein** Kärtchen: „Level 1 · Fish n’ Chips“, 5 Sterne als Meilensteine, Balken zum nächsten Stern, Gewinn + Takt, **ein** blauer Preisknopf. Fertig. | Vertikale **Level-Leiter** (lvl 25…35), jede Stufe mit Belohnung („+15 % Hotel income“, „+8 % speed“, Schloss bei 27), unten „LEVEL 26 · UPGRADE“ | Tabs „UPGRADE ǀ MANAGER (Schloss)“, Zeilen „Sitzgelegenheiten +131 · MAX LEVEL“; Hotel Empire: Objekt, Satz, „UPGRADE 350“ grün, Effekt „+7.20 +4.80“, Raster mit 8 Gegenständen + Level-Badge |
| **Ziele** | Quest-Zeile oben mit Belohnung | — (Fortschritt = Sterne) | „DAILY QUESTS 0/5“ Karte, je Quest Belohnung + „GO“-Knopf, der hinspringt | Drei Ebenen: Quests füllen Balken → Balken füllt Meilenstein → Meilensteine = Prestige (PocketGamer) |
| **Manager/Karten** | Karten mit Porträt, Rang (Junior/Senior/Executive), Effekt („−40 % Upgrade Cost“) | Ausrüstung in Seltenheitsfarben (weiß/grün/lila/orange) | Skins/Abilities-Tabs | Supermarket „Epic Upgrades“: Karte = Level, Icon, **+200 %**, Preis |
| **HUD** | Oben 3 Währungen; unten 5 Knöpfe, Mitte = Zeit-Boost | Oben Cash + Gems + **×3,2 Multiplikator**; unten 5 Knöpfe, Mitte **„Boost ×5 · +10 min“** | Oben Geld, Ziel-Leiste, Gems; unten 4 Knöpfe | Oben Geld/Gems; rechts Spalte mit Shop/Boost/Schloss |
| **Story** | keine | keine | keine | Idle Bank: Figur mit Sprechblase („I’m allowed to…“) als Vollbild-Porträt |
| **Onboarding** | Zeigehand auf dem nächsten Knopf, nichts anderes aktiv | „Let’s UPGRADE the loader“ als Sprechblase + Hand | Hand + nur ein Ziel | — |

**Belege:** [GDC-2019-Deconstruct](https://mobilefreetoplay.com/gdc-2019-deconstructing-idle-miner-tycoon/) · [Kolibri: 8 Lektionen — „core loop visible on one screen“, choke points](https://www.gameanalytics.com/blog/making-a-hit-idle-game-eight-lessons-from-kolibri-games) · [PocketGamer: Idle Bank Tycoon](http://www.pocketgamer.biz/game-analysis-deconstructing-idle-bank-tycoon-by-kolibri-games/) · [PocketGamer: Eatventure vs Cat Snack Bar](https://www.pocketgamer.biz/feature/82671/eatventure-vs-cat-snack-bar-an-analysis-of-both-games/) · [LevelWinner Eatventure-UI](https://www.levelwinner.com/eatventure-beginners-guide-tips-tricks-strategies/) · [My Perfect Hotel Guide](https://www.whisperofthehouse.com/my-perfect-hotel) · [AdVenture-Capitalist-Onboarding: weniger auf einmal](https://www.globalgamesforum.com/ctv/idle-game-design-lessons-from-developing-adventure-capitalist) · Bildbelege: Google-Play-Galerien Idle Miner/Eatventure, Google-Bilder „Idle Bank Tycoon Haupthalle“, „My Perfect Hotel lvl 26 upgrade“, „Idle Supermarket Management/Epic Upgrades“, „Hotel Empire Room 101“ (am 15.10. angesehen).

**Die fünf Gesetze daraus:** (1) **Ein Knopf pro Bildschirm** ist groß und farbig, alles andere ist Papier. (2) **Jede Zahl zeigt vorher → nachher.** (3) **Der Fortschritt zur nächsten Belohnung ist immer sichtbar** (Stern-Balken, Level-Leiter, Ziel-Leiste). (4) **In der Welt sieht man Level und Kaufbarkeit ohne Panel** (Badge + Pfeil + Hand). (5) **Belohnung = Ereignis**: Vollbild-Moment mit Zahl, die hochzählt, nicht eine Textpille.

---

## 2. Wir heute vs. Top-Spiele (Befund aus den Handy-Bildern)

| # | Befund (handy1/handy2) | Verstoß gegen Gesetz |
|---|---|---|
| B1 | **Zwei Panels gleichzeitig** (Stationsmenü schimmert hinter dem Raum-Panel durch; „AUSBAUEN · in 0:12“ als Geist). Raum-Panel = 55 % des Bildes. | Fokus: nie zwei Sheets. Bug in `Hud._oeffne`/`Sheet`. |
| B2 | Raum-Panel beginnt mit **Erklärsatz + Haus-Icon**; die Stationskarte darunter ist ein halbes Stationsmenü (3 Ausstattungskarten mit Preisen). Nichts ist größer als das andere. | (1), (2): keine Hierarchie, keine Hauptaktion. |
| B3 | Stationsmenü: „Noch 3 bis ×1,5“ nur Text, Nutzenkarte „Bremst nicht. Engpass ist Idee“ grau, Ausbauen-Knopf gleich hoch wie x1/x10/MAX. Drei Ausstattungskarten mit je 5 Zeilen Kleintext. | (1), (3): Stern-Meilenstein ist kein Ereignis, Preis- und Nutzenzahl zu klein. |
| B4 | In der Welt: Namenschips („Idee“, „Upload“), ein Pfeil, ein Münz-Icon, ein Warndreieck, „+2,2“ fliegend — **kein Level, keine Sterne**, Stationen sehen aus wie Möbel (Upload = Bücherregal). | (4): Station ist nicht als Station lesbar. |
| B5 | Zielkarte verschwindet, sobald ein Panel offen ist; Ziele-Menü = Liste gleich aussehender Zeilen mit Gold-Knopf, kein Zusammenhang „warum“. | (3): kein ständiger Fortschritt zur Belohnung. |
| B6 | Kopfleiste: „9,9“ ohne Einheit, Geschenk-Marken unbeschriftet; untere Leiste 5 Knöpfe, Mitte ein Blitz mit „3:52“ (unklar: Boost oder Countdown?). | Lesbarkeit in 1 s. |
| B7 | Story = Chatliste mit Initialen-Kreis; die Eröffnung ist ein Chat, aber danach keine Figur mehr sichtbar. 22 Nachrichten pro Welt beschreiben, der Spieler wählt nie. | Kein Konflikt, kein Geheimnis. |
| B8 | „+Geld“-Debugknopf im Bild, Tutorial-Hand fehlt nach dem 1. Schritt. | Onboarding. |

Bleibt (gut): Sticker-Pop-Grundstil, Kopfleisten-Form, Welt-Modelle, Konfetti/Münzflug, Porträts, Figuren-Jubel.

---

## 3. Design-System — Ergänzungen für `game/ui/ui_stil.gd` (nur Darstellungswerte)

```
# Farben (neu/geändert)
KAUFEN      #B6F03C  bleibt — aber NUR auf dem einen Hauptknopf und dem Welt-Pfeil
KAUFEN_TIEF #7FB81C  Schatten/Kontur des Hauptknopfs (vorher Tinte: wirkte wie Rahmen, nicht wie Taste)
STERN_BALKEN #FFC21A (GOLD) ausschließlich für Stern-Fortschritt; Akzent für Welt-Fortschritt
GESPERRT    #D9D0C0  Fläche gesperrter Karten, Text TINTE_3 (nie Kaufen-Grün auf Gesperrtem)
LEVEL_BADGE Akzent der Welt, Text text_auf(akzent); Kontur KONTUR_CHIP

# Typo (720 logisch) — vier Stufen reichen, alles andere raus
GR_HINWEIS 18 (nur Chips/Untertitel), GR_TEXT 22, GR_TITEL 32, GR_ZAHL 44, GR_HELD 64 (Belohnungs-Moment)
PREIS auf Hauptknopf: GR_ZAHL;  NUTZEN („+3,4 €/s“): GR_TITEL in PLUS_TEXT;  Nebenwerte: GR_TEXT TINTE_2

# Maße
KNOPF_PRIMAER_H 104   (vorher 88 = wie alles andere; Eatventure-Preisknopf ≈ 14 % der Sheet-Höhe)
KNOPF_SEKUNDAER_H 72  (x1/x10/MAX, „Zur Station →“)
SHEET_MAX 0.56        Anteil der Bildhöhe, den ein Sheet maximal deckt (Welt bleibt sichtbar)
BADGE_H 40            Level-Abzeichen in der Welt, Schrift GR_HINWEIS FETT, immer gleich groß (Screen-Space)
SCHATTEN_Y_PRIMAER 6  Hauptknopf hebt sich 2 px mehr als Karten
A7 48                 Abstand zwischen Abschnitten im Sheet (A6 32 innerhalb)

# Bewegung (neu, alle abschaltbar)
DAUER_ZAEHLEN 0.8     Zahlen zählen hoch (Belohnung, Offline, Abschluss)
DAUER_PULS 1.2 Hz     Ring/Pfeil-Puls „kaufbar“ (Scale 1,0→1,08)
DAUER_SZENE_EIN 0.25  Figuren-Popup von unten, TRANS_BACK
```

**Knopf-Hierarchie (verbindlich):** Primär = Limette, 104 hoch, Preis GR_ZAHL + zweite Zeile Nutzen; genau **einer** je Sheet. Sekundär = Papier mit Kontur, 72 hoch. Tertiär = Chip (Akzent-Rand, kein Schatten). Gesperrt = GESPERRT-Fläche, Schloss, „ab Stufe N“ + Mini-Balken — **nie** ein Preis.
**Panel-Stile:** Titelstreifen Akzent (bleibt), danach **Held-Zeile** (das, was man als Nächstes bekommt), dann Hauptknopf, dann Rest. Nie Erklärtext vor der Zahl.

---

## 4. Wireframes (Text)

**4.1 HUD**
```
┌ [€] 41.882 €            ┐ ┌ DIE WG ────── 13 % ┐ [⚙]
│     +6,5 €/s  (federt)  │ │ ▓▓░░░🎁░░🎁░░🎁   │      ← Marken mit Tooltip „25 %: 2 Min Einkommen“
└─────────────────────────┘ └────────────────────┘
┌ 🎯 ZIEL  Schnitt auf Stufe 10   ▓▓▓▓▓░░ 7/10   🎁 +2,4 Tsd ┐   ← Ziele-Leiste, IMMER sichtbar (auch bei Sheet)
└ [→ hin]                                             (tipp) ┘     1 Hauptziel; Tipp = Kamera + Panel springen hin
                     ... Welt ...
            [🎁 Tagesgeschenk]  [⚡ Boost ×2 · 3:52]          ← schwebend rechts, nur wenn verfügbar
┌ 🔧 Ausbau ⁹ │ 🎯 Ziele ¹ │  ⚡ BOOST  │ 📱 Handy ³ │ 🏠 Welt ┐   Mitte: Boost-Knopf mit Restzeit, sonst „Boost bereit“
```
Regeln: Geld immer mit „€“; Abzeichen nur, wenn **jetzt** kaufbar/einlösbar (Idle-Miner-Regel), nicht „Anzahl Stationen“.

**4.2 Stations-Panel** (Sheet ≤ 56 %)
```
┌ [Icon 72] SCHNITT  ·  Stufe 17        ★★☆☆☆          [×] ┐  Titelstreifen Akzent
│ Der Laptop. Aus Aufnahmen werden Clips.                   │  1 Satz, GR_TEXT, TINTE_2
├───────────────────────────────────────────────────────────┤
│ ★ Nächster Stern ×1,5 in 3 Stufen   ▓▓▓▓▓▓▓░░░  17/20     │  Gold-Balken (Gesetz 3)
│ 18/Min → 21/Min      Einkommen +3,4 €/s                   │  Held-Zeile: vorher → nachher, Delta GR_TITEL grün
│      ⚠ Bremst nicht – Engpass ist IDEE  [Zur Idee →]     │  nur wenn nicht Engpass; Chip, nicht Fläche
├───────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────┐ ┌────┐┌────┐┌────┐      │
│ │ ▲ AUSBAUEN        2.327 €     │ │ x1 ││x10 ││MAX │      │  Primär 104 hoch, 60 % Breite; Preis GR_ZAHL
│ │   +3,4 €/s · in 0:12          │ └────┘└────┘└────┘      │  zweite Zeile: Nutzen / Wartezeit
│ └───────────────────────────────┘                          │
├─ Ausstattung ─────────────────────────────────────────────┤
│ [🖥 Bildschirm] Stufe 4 · Großer Monitor   +25 %  [10.252 €]│  Zeile statt Karte: Icon, Name, Nutzen, Preisknopf 72
│ [💻 Rechner]    Stufe 4 · Gaming-Laptop     +25 %  [ 1.025 €]│  „Lohnt sich“-Chip auf GENAU einem Knopf
│ [🪑 Stuhl]      🔒 ab Stufe 25   ▓▓▓░░ 17/25               │  gesperrt: kein Preis
└───────────────────────────────────────────────────────────┘
```
Kauf-Feedback (bleibt, wird stärker): Preis zählt runter, Delta fliegt als „+3,4 €/s“ GR_TITEL zur Kopfleiste, 6 Münzen, Haptik. **Stern erreicht:** Gold-Blitz, Stern springt in die Titelzeile, „×1,5“ in GR_HELD 0,8 s über der Station, Ton `stern`, Figur der Station jubelt.

**4.3 Raum-Panel** (ersetzt die Sackgasse; nie zugleich mit Stations-Panel offen)
```
┌ [Raumbild 96] DER FLUR          Bonus: Alles ×1,25 ✓   [×] ┐
├ Hier kannst du ausbauen ────────────────────────────────────┤
│ [Icon] Upload   Stufe 10 ★☆☆   +0,2 €/s     [▲ 4.366 €]    │  1 Zeile je Station: Tipp = Stationspanel, Knopf kauft direkt
│ [Icon] Netz     Stufe 5        +0,1 €/s     [   46 Tsd ]    │  (Ausstattung als eigene Zeile nur, wenn sie der „Lohnt sich“-Kauf ist)
├ Ziel-Kette dieses Raums ───────────────────────────────────┤
│ ✓ Upload Stufe 5  →  ● Upload Stufe 15 ▓▓▓░ 10/15 🎁 1,2 Tsd  →  ○ Netz Stufe 10 🎁                            │
├─────────────────────────────────────────────────────────────┤
│ Nächster Raum: DIE KÜCHE · 2.000 €  „Alle Stationen ×1,25“  [→]│  Sekundär; gesperrt-Zustand: „Tobi wohnt noch hier“ + Bedingung
└─────────────────────────────────────────────────────────────┘
```
Kaufbarer Raum: Held-Zeile = **„Danach hier: ⚙ Upload (neue Station) · Alles ×1,25“**, dann Primärknopf „KAUFEN · 2.000 €“, Erklärsatz zuletzt.

**4.4 Welt-Marker über Stationen** (`kartenmarker.gd`, Screen-Space, immer gleich groß)
```
   [ Lv 17 ★★ ]        ← Level-Badge (Akzent) + bis zu 5 Mini-Sterne; Tipp öffnet Panel
   ▲ 2.327 €           ← Kaufpfeil Limette + Preis NUR wenn bezahlbar UND Mehreinnahme > 0 (pulst 1,2 Hz)
   ⚠                   ← Engpass-Rot, ersetzt den Pfeil nicht, steht darüber
   🎁                  ← erfülltes Ziel an dieser Station: Geschenk statt Pfeil
```
Stationen bekommen eine **Bodenplatte** (flacher Sticker-Rahmen 2,2 × 2,2 m im Akzent, 4 % Höhe, gesperrt grau) — damit „Station“ von „Möbel“ unterscheidbar ist (Eatventure-Prinzip). Gesperrte Station = gepunkteter Umriss + Schloss, erste Stufe sichtbar als Silhouette.

**4.5 Ziele-Leiste** (HUD, oben, bleibt bei offenem Sheet sichtbar, rutscht ggf. über das Sheet)
1 Hauptziel (Kette der Welt) + optional 1 Tagesaufgabe; Belohnung sichtbar; Tipp bei erfüllt = einlösen (Münzen fliegen, Zahl zählt), Tipp sonst = **springt hin** (Kamera + Panel). Ziele-Menü wird **Ketten-Ansicht**: je Raum eine Kette ✓→●→○ mit Belohnungen, Welt-Missionen oben.

**4.6 Onboarding** (`tutorial_view.gd`): eine **Zeigehand** (SVG `hand.svg`, Sticker-Stil) hüpft 1 Hz auf dem nächsten sinnvollen Element; Texte bleiben als Sprechblase mit Mo-Porträt. Nach dem Tutorial zeigt die Hand weiter — **nur** wenn 60 s lang nichts getippt wurde und ein lohnender Kauf bezahlbar ist (Idle-Miner-Regel: Hand = „hier weiter“). Debug-„+Geld“ nur im Debug-Build unten links, halbtransparent.

**4.7 Story-Szenen** (`szene_view.gd`, neu): Figuren-Popup unten (40 % Höhe) mit **Porträt 220 px** (neutral/jubelnd/geschockt), Name-Chip in Absenderfarbe, Sprechblase GR_TITEL, 1–3 Blasen nacheinander (Tipp = weiter), optional **zwei Antwort-Chips** (ein Wort; wirkt nur auf Laune/Text, nie auf Geld). Nur an **Schlüsselmomenten** (Weltstart, jeder Raumkauf, 50 %, Cliffhanger, Abschluss); alle anderen Nachrichten bleiben Banner (3,5 s) + Handy. Handy-Chat bekommt Porträts statt Initialen und die Antworten des Spielers als rechte Blase.

**4.8 Belohnungs-Momente** (Vollbild-Karte, SCHLEIER): Zahl zählt 0 → Betrag (0,8 s, Ton `zaehlen`), Konfetti, Münzen zur Kopfleiste, Haptik 40 ms, Figur jubelnd. Gilt für: Ziel eingelöst (ab 200 €), Marke 25/50/75 %, Tagesgeschenk, Offline-Rückkehr, Raumkauf, Stern. Kleine Ziele (< 200 €) bleiben Münzflug.

---

## 5. Progression — mehr Ziele, dosiert

| Ebene | Was | Wo (Daten) | Sichtbar |
|---|---|---|---|
| **Ziel-Ketten je Raum** | 3 Ziele je Raum (Station → Ausstattung → Stern), 5 Räume + Start = 18 + 7 Welt-Missionen = 25 (Anzahl bleibt, Struktur neu) | `data/balance/<welt>.json` → `ziele[].kette: "bereich_1"` | Raum-Panel, Ziele-Menü, Leiste |
| **Sterne je Station** | bleibt (alle 10 Stufen ×1,5); 5 Sterne = „Meisterstation“, Bodenplatte Gold | vorhanden | Badge, Panel, Welt |
| **Crew-Karten** (Manager) | je Station 1 Karte: Figur der Welt + Rang I–III; Kauf mit €, Effekt +10/20/35 % Leistung der Station; Freischaltung durch Ziel-Kette des Raums | `data/balance/<welt>.json` → `crew.station_x: {stufen:[…kosten, faktor]}`; Namen/Porträt in `theme.json` → `crew` | Stations-Panel Tab „Crew“ (gesperrt mit Schloss bis Kette 1 fertig) |
| **Tagesaufgaben** | 2 je Kalendertag („Kaufe 5 Stufen“, „Löse 1 Ziel ein“), Belohnung 3 Min Einkommen | `data/balance/tagesaufgaben.json` | Ziele-Leiste Slot 2 |
| **Erfolge** | 12 weltübergreifend (erster Stern, erster Raum, 5 Sterne, Welt 1 fertig, 3 Tage Serie …), Belohnung dauerhaft +1 % Welt-Faktor | `data/balance/erfolge.json` | Fortschritt-Menü, Abschnitt „Erfolge“ |
| **Level des Spielers** | Summe eingelöster Ziele = Level (1…150), Level-Up = Moment (4.8) | Kern zählt | Kopfleiste links unter Geld: „Lv 12“ |

Dosierung: Die Leiste zeigt **nie mehr als 2 Aufgaben**. Crew erst ab Raum 2, Tagesaufgaben erst ab Welt-Fortschritt 20 %, Erfolge nur im Menü + Moment. Werte via `balance_sim` prüfen (Abschluss je Welt weiter 60–90 min).

---

## 6. Story-Überarbeitung — Bogen, Konflikt, Geheimnis

**Bogen:** Drei Aufrufe → Portfolio über der Stadt. **Konflikt je Welt** (Druck, der treibt): W1 Miete/Tobis Auszug (das Zimmer wird frei — oder Mira holt eine Fremde rein), W2 Younes’ Perfektion vs. Rolltor-Deadline, W3 380 Shirts = Schulden bei Roman, W4 Menschen statt Tabelle, W5 Strom/Risiko, W6 „gefährlich“: Gier gegen Streuung.
**Geheimnis (Hook über 6 Welten): „Wer war der dritte Aufruf?“** Mo behauptet, er war’s. W2 Younes: „Mo war beim Zocken.“ W3 Roman zählt: „Zwei aus deinem Netz. Einer aus einem anderen Bundesland.“ W4 Selin meldet sich „über Mo“. W5 Selin: „Ich hab deine Clips von Anfang an gesehen. Alle.“ W6, vorletzte Nachricht (ihr einziger Satz mit Gefühl): „Drei Aufrufe. Einer war ich. Ich hab nichts gesagt. Ich sag nie was.“ Danach Mo: „Ich hab’s gesagt, damit du weitermachst.“ Letzte: der Kanal — jemand Neues, drei Aufrufe.
**Wiederkehrende Momente:** Mo isst in jeder Welt mit (Szene bei 50 %), Younes’ „noch ein Take“, Romans Tabelle schrumpft (7 → 3 → 1 Reiter), Selins „Das ist Physik“. Jede Welt: Szene am Start (Problem), Szene je Raum (Figur reagiert auf den Raum, nicht auf die Zahl), Szene 50 % (Mo), Cliffhanger (neue Figur mit Problem).

**Zehn Beispielszenen (Popup, je 2–3 Blasen, Antwort-Chips in Klammern):**
1. **W1 Start, Mo (jubelnd):** „Bruder. Drei Aufrufe.“ / „Zwei warst du. Der dritte war ich.“ / „Jetzt kaufen wir einen Gaming-PC. Fang an.“ (Okay. / Mit was?)
2. **W1 Flur gekauft, Mira (neutral):** „Der Router steht im Flur. Das WLAN im Bad ist jetzt besser als in meinem Zimmer.“ / „Danke?“ (Gern. / Sorry.)
3. **W1 50 %, Mo (jubelnd):** „1.000 Aufrufe. 400 davon ich. Ich hab ein zweites Konto.“ / „Tobi kocht für drei. Rate, wer der dritte ist.“ (Du. / Immer du.)
4. **W1 Zimmer frei, Tobi (geschockt → neutral):** „Ich zieh aus. Der Topf bleibt.“ / „Mach was draus. Aber nicht laut nach 22 Uhr.“ (Versprochen. / Kein Versprechen.)
5. **W1 Cliffhanger, Younes (neutral, unbekannte Nummer):** „Mo sagt, du schneidest.“ / „Ich hab eine Garage und ein Rolltor, das klemmt.“ / „Bring Kaffee.“ (Wann? / Welcher Kaffee?)
6. **W2 Start, Younes:** „Kein Kaffee. Ich hab’s notiert.“ / „Take 1. Nicht reden.“ (Ok. / …)
7. **W2 Stern-Meilenstein, Younes (jubelnd — einziges Mal):** „Take 14 war gut. Take 15 war besser.“ / „Wir nehmen 16.“ / „…gut so.“ (Gut so? / Nochmal?)
8. **W3 Start, Roman (neutral):** „380 Shirts. Weil 400 zu rund war.“ / „Die Tabelle hat sieben Reiter. Reiter drei ist deine Schuld.“ (Wie viel? / Zeig.)
9. **W4 Raum 3, Jana (ein Wort):** „Ja.“ / Roman (geschockt): „Sie hat die Pausenzeiten geändert. Ohne zu fragen. Sie hatte recht. Mir ist schwindelig.“ (Lass sie. / Tabelle weg.)
10. **W6 vorletzte, Selin (neutral, dann jubelnd):** „Drei Aufrufe. Einer war ich.“ / „Ich hab nichts gesagt. Ich sag nie was.“ / „Jetzt hab ich’s gesagt. Zurück zu den Kurven.“ (Danke. / Ich wusste es.)
Regeln bleiben (STORY.md 1–12); neu: (13) Szenen sind max. 3 Blasen, Antworten 1 Wort, (14) jede Welt hat 5 Szenen + 17 Banner-Nachrichten = 22, (15) eine Szene pro Welt deutet das Geheimnis an.

---

## 7. A/B-Vergleich (heute, ehrlich) und Varianten-Schalter (später)

**Heute, ohne Nutzerdaten:** Je Kernbildschirm zwei Varianten rendern (`--variante a|b`, Schalter in `data/experimente.json`, nur Darstellung) → `tools/ab_montage.py` legt `shots/ab/<schirm>_ab.png` nebeneinander (PC-Vorschau + Handy-Screenshot). Bewertung in `docs/nacht/ab_bewertung.md` mit **festen Kriterien, je 0–2 Punkte:** (K1) In 1 s lesbar: Name, Stufe, Preis, Nutzen bei 50 % Skalierung; (K2) „Was tippe ich als Nächstes?“ — genau ein Element ist das größte/farbigste; (K3) Belohnungsgefühl: Fortschritt zur nächsten Belohnung sichtbar + Moment beim Kauf; (K4) Welt bleibt sichtbar (Sheet ≤ 56 %); (K5) Sticker-Pop konsistent (eine Effektart). Gewinner ≥ 7/10 wird übernommen, Verlierer gelöscht (kein toter Code). Bildschirme: Stations-Panel (A: Held-Zeile oben / B: Level-Leiter wie My Perfect Hotel), Raum-Panel (A: Stationszeilen / B: Ziel-Kette oben), HUD-Ziele-Leiste (A: eine Zeile / B: Karte mit Balken), Story-Szene (A: Popup unten / B: Vollbild wie Idle Bank).
**Balance-A/B:** `balance_sim.gd -- --variante b` liest `data/balance/experimente/<welt>_b.json` (Overlay über das Original). Messgrößen, die der Simulator ausgibt: Zeit bis erstes Upgrade, Upgrades pro Minute in den ersten 10 Minuten, Zeit bis Raum 2, Zeit bis erster Stern, Abschluss. Ziel: erstes Upgrade < 10 s, ≥ 1,5 Upgrades/min in Minute 1–10, Raum 2 < 4 min.
**Nach Release:** `data/experimente.json` → `{"aktiv": {"stations_panel": "a"}, "varianten": {...}}`; Auswahl pro Installation deterministisch aus dem Spielstand-Zufallswert (kein Netz, keine Erhebung, kein Analytics — DSGVO-neutral). Ehrlich gesagt: **ohne Datenerhebung lässt sich ein A/B-Test nicht auswerten**; der Schalter erlaubt nur, Testern (Florins geschlossener Test) Variante A oder B zu geben und Rückmeldung per Formular/Chat zu sammeln. Messung in der App bleibt bewusst aus.

---

## 8. Bau-Pakete — 5 UI/Kern-Agenten + 6 Welt-Polierer + Leitung, exklusive Schreibrechte

Leitung (Opus) legt um 0:00 fest: i18n-Schlüssel (alle neuen Texte in `data/i18n/de.json` — **nur Leitung schreibt dort**), Token-Namen (§3) in `docs/nacht/rp2_schnittstellen.md`, Datenschema für Ketten/Crew/Tagesaufgaben/Erfolge/Experimente in `docs/nacht/rp2_schema.md`. `game/main.gd` gehört der Leitung (Nähte). Wünsche: `docs/nacht/wuensche2_<von>_an_<an>.md`. Scratchpad-Präfix `ov_<paket>_`. Kein `validate.ps1` durch Agenten, kein `--import` während Blender läuft.

| Paket | Ziel | Dateien (exklusiv) | Abnahme (Vorschau + Kriterien) |
|---|---|---|---|
| **U1 · Stations-Panel + Marker** (Sonnet) | §4.2, §4.4 Badge/Pfeil/Geschenk, Stern-Moment, Crew-Tab (liest Kern-API von U4) | `game/ui/stationsmenue.gd`, `game/ui/kartenmarker.gd`, `game/world/ausstattungs_station.gd` (Bodenplatte/Ring), `assets/ui/symbole/hand.svg`, `stern_klein.svg`, `tests/unit/test_stationsmenue.gd` | `serie.sh ov_station --tiefe 2 --menue station_processing`, `ov_station_eng --tiefe 1 --menue station_intake`, `ov_marker --tiefe 2`: K1–K5 ≥ 7/10; Hauptknopf 104 hoch, einzige Limette; Delta ≥ GR_TITEL; Badge an jeder Station lesbar bei Zoom-Start; gesperrte Karte ohne Preis |
| **U2 · HUD, Ziele-Leiste, Raum-Panel, Ziele-Menü** (Sonnet) | §4.1, §4.3, §4.5; Bug B1 (nur ein Sheet); Boost-Knopf-Text; Level in Kopfleiste | `game/ui/hud.gd`, `kopfleiste.gd`, `menueleiste.gd`, `sheet.gd`, `menues.gd`, `tests/unit/test_hud.gd` | `serie.sh ov_hud --tiefe 1`, `ov_raum --tiefe 2 --menue bereich_1`, `ov_raum_kauf --menue bereich_2`, `ov_ziele --tiefe 2 --menue ziele`: Leiste bei offenem Sheet sichtbar; genau ein Sheet; Raum-Panel ≤ 56 %; Kette ✓●○ lesbar |
| **U3 · Szenen, Onboarding, Momente** (Sonnet) | §4.6–4.8: `szene_view.gd` neu, Hand, Belohnungs-Vollbild, Handy-Chat mit Porträts/Antworten, Eröffnung als Szene | neu `game/ui/szene_view.gd`, `game/ui/moment_view.gd`, `tutorial_view.gd`, `tutorial_ablauf.gd`, `saft.gd`, `geschenk_view.gd`, `offline_view.gd`, `abschluss_view.gd`, `weltwechsel_view.gd`, `haptik.gd`, `data/tutorial/tutorial.json`, `data/audio/sounds.json`, `tests/unit/test_tutorial_ablauf.gd` | `serie.sh ov_szene --ohne-eroeffnung --szene nachricht_01` (Schalter neu), `ov_hand --mit-tutorial`, `ov_moment --tiefe 2 --moment ziel`, `ov_offline --offline 5400`: Porträt ≥ 220 px, Blase GR_TITEL, Antwort-Chips ≥ 88 hoch; Hand hüpft auf dem richtigen Element; Zahl zählt hoch |
| **U4 · Kern + Daten + A/B-Werkzeuge** (Sonnet) | §5 Ketten (`kette`), Crew, Tagesaufgaben, Erfolge, Spieler-Level, Save-Migration; §7 Schalter + Overlay + Montage + Messgrößen | `core/**`, `data/balance/geschenk.json`, neu `data/balance/tagesaufgaben.json`, `erfolge.json`, `data/balance/experimente/**`, `data/experimente.json`, `tools/balance_sim.gd`, `tools/welt_sim.gd`, neu `tools/ab_montage.py`, `tests/unit/test_*kern*.gd`, `tests/integration/**` | alle Kern-Tests grün; `balance_sim` je Welt 60–90 min + neue Messgrößen im Ausdruck; `welt_sim -- zimmer` zeigt Ketten und Crew-Freischaltung; Migration alter Spielstände getestet |
| **U5 · Stil + Stations-Optik** (Sonnet, Blender + GDScript) | §3 Tokens in `ui_stil.gd`; Bodenplatten/Umrisse als Modelle; Stations-Modelle „lesbarer“ (größer, Akzentfarbe, Stufe sichtbar); `worlds.json` (Schild-/Stationspositionen, nimmt Wünsche der Welt-Agenten an) | `game/ui/ui_stil.gd`, `sticker_box.gd`, `data/worlds/worlds.json`, `art_source/scripts/build_stationen_*.py`, `build_platten.py` neu, Ausgaben `project/assets/stations/**` | `serie.sh ov_welt1 --tiefe 3`, `ov_welt3 --welt 3 --tiefe 3`, `ov_welt6 --welt 6 --tiefe 3`: Station von Möbel in 1 s unterscheidbar; Stufe 1/5/10 visuell verschieden; keine Ersatzwelt-Warnung; Dreiecke je Station ≤ 2.500 |
| **W1–W6 · Welt-Polierer** (6 × Sonnet) | §6 für ihre Welt: 5 Szenen + 17 Nachrichten, Konflikt, Geheimnis-Andeutung, Raumtexte „danach hier“, Crew-Namen; Ziel-Ketten und Crew-Werte ihrer Welt nach `rp2_schema.md`; Vorschaubilder ihrer Welt prüfen (Lesbarkeit, Modelle, Licht) | `data/themes/<welt>/theme.json`, `data/balance/<welt>.json` (nur Abschnitte `ziele`, `nachrichten`, `crew`, `tagesaufgaben_pool`), `docs/nacht/lesung_<welt>.md`; Wünsche an U5 (`worlds.json`) und U4 (Schema) als Wunschdateien | JSON valide, keine Sperrwörter außerhalb themes, `welt_sim -- <welt>` listet 22 Nachrichten mit Zeitpunkten, 5 davon `szene: true`; Lesung komplett; `serie.sh ov_w<n>_* --welt n` angesehen, Befunde als Wünsche |

**Uhr (erste spielbare Fassung nach ~2 h, dann Iteration):**
- 0:00 Leitung: Schnittstellen, Schema, i18n-Schlüssel, Token-Namen. Alle 11 starten. U5 liefert Tokens in den ersten 20 min (U1/U2/U3 bauen gegen die Namen).
- 0:20–2:00 **Phase 1 „spielbar“:** U1 Panel + Badge; U2 Ein-Sheet-Fix + Ziele-Leiste + Raum-Panel; U3 Szene + Hand; U4 Ketten + Schalter; U5 Bodenplatten; W1 zuerst Welt 1 (Szenen), W2–W6 Lesung + Ketten.
- 2:00 **Schreibstopp 1.** Leitung: `--import`, `validate.ps1 -SkipBuild`, `deploy.ps1` → **Handy-Runde 1 (Bastian, 15 min, Kriterien K1–K5 je Bildschirm)**; parallel `ab_montage.py` für die vier A/B-Bildschirme.
- 2:20–4:30 **Phase 2:** Gewinner-Varianten festziehen, Verlierer löschen; Crew-Tab, Tagesaufgaben, Erfolge, Momente; U5 Stations-Modelle; Welt-Agenten Runde 2 (Vorschaubilder ihrer Welt, Wünsche an U5).
- 4:30 **Schreibstopp 2** (Blender-Export-Stopp 4:15). Leitung: import, `validate.ps1` mit Build, `deploy.ps1`, Handy-Runde 2.
- 5:15 Commits je Paket (eine Task = ein Commit), `CURRENT_STATE.md`, `NEXT_SESSION.md`, `docs/STORY.md` (Regeln 13–15), Store-Screenshots neu.

**Abnahme-Checkliste Handy (K1–K5 je Bildschirm, 0–2 Punkte):** Start (Szene, Hand), Stations-Panel (Engpass + Nicht-Engpass), Raum-Panel (gekauft, kaufbar, gesperrt), Ziele-Leiste bei offenem Sheet, Stern-Moment, Ziel-Moment, Tagesgeschenk, Welt 3 und Welt 6 Marker-Dichte (nicht überflutet: max. 1 Pfeil + 1 Warnung + Badges sichtbar). Unter 7/10 → zurück an das Paket, nur dieses schreibt.
