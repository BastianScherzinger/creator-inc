# K6 · KONZEPT — „Eine Firma, die man wachsen sieht“

**Stand:** 2026-10-16 · Rolle: Lead Game Designer · Auslöser: Bastians Handy-Urteil vom 16.10. (Auto-Zoom, Plaketten nicht antippbar, Popup-Flut, überlappende Nachrichten, „nur kleine Bugs“, „Konzept überdenken“, „echtes Unternehmen“).
**Art:** Diagnose, Konzept, Umsetzungsplan. Kein Code, keine Datenänderung, kein Commit.
**Grundlagen:** K2–K4 (gelesen), `K3_AB_BEWERTUNG.md` §5, Handybilder `shots/k3_ab/*_k.png`, `shots/serie/k4_*.png`, `shots/k5/*.png`, der **unbestätigte Arbeitsbaum vom 16.10.** (15 geänderte Dateien, Kapitelsystem, `vollbild_momente: ["raum"]`), drei Recherchen (Monetarisierung/Retention, Kernschleife/UI, Psychologie/Postmortems; Quellen in §9).
**Kennzeichnung:** **[B, Qn]** belegt aus gelesener Quelle · **[B-V]** Anbieterquelle mit Eigeninteresse · **[A]** abgeleitet oder eigener Befund aus Bild/Code. Ehrlich vorab: Für **kein** Referenzspiel gibt es eine belegte Zoom- oder Popup-Regel; alle Kamera- und Fensterregeln unten sind aus Bastians Urteil, NN/g und dem eigenen Code abgeleitet.
**Regeln, die weiter gelten:** D3/ADR-010, Kern rechnet, Darstellung zeigt; keine Werte im Code; kein Commit bei rotem `validate.ps1`; jede sichtbare Änderung endet mit einem angesehenen Screenshot.

---

## 1. Ehrliche Diagnose — warum HELLO WORLD sich nicht wie ein Top-Idle-Game anfühlt

Die Mechanik ist gesund (Kette, Engpass, Sterne, Räume, gemessene Balance). Der Fehler liegt in dem, was der Spieler **tut, sieht und ertragen muss**. Sechs Befunde, geordnet nach Schwere.

### 1.1 Kernschleife: Es gibt nur eine Handlung — „Zahl ausbauen“

- Der Spieler tippt Ausbauen, eine Zahl steigt, Geld steigt. Es kommt nichts herein (kein Kunde, keine Anfrage), es geht nichts hinaus (kein Paket, kein Clip, der jemanden erreicht), niemand wird eingestellt. „Clips/Min“ und „Ideen/Min“ sind Prozesswerte, keine Firma. [A, Code `stationsmenue.gd`, Bilder `b1_raum_k`, `a1_12_k`]
- In jedem belegten Top-Spiel bleibt **eine manuelle Handlung in der Welt Spielerjob**: Geldstapel einsammeln (My Perfect Hotel, Burger Please), Trinkgeld-Münzen (Eatventure), Fahrer wecken (Idle Lumber), Lieferwagen leeren (Idle Supermarket) [B, Q10 Q12 Q13 Q15 Q24]. Jurasek zu My Perfect Hotel: „Automate the mundane parts and keep the satisfying actions in the player's hands“ [B, Q15]. HELLO WORLD automatisiert **alles** ab Sekunde 1; Kiste und Clip-Stapel (K3 B2) sind richtige Ansätze, aber nur alle 90–150 s und ohne Bezug zum Geschäft.
- Folge: K4-Messung 0,4–0,6 Belohnungsmomente/Minute in den ersten 5 Minuten (Ziel ≥ 2) [A, K3_AB §5].

### 1.2 Fantasie „echtes Unternehmen“: Die Figuren reden, statt zu arbeiten

- Mo, Mira, Tobi erscheinen als Chat-Absender und Szenen-Porträts. Keiner von ihnen ist **Mitarbeiter mit Platz im Raum**, keiner ist Kunde. „Crew“ ist eine Karte mit Faktor 1,1 → 1,2 → 1,35 (`balance/zimmer.json → crew`), kein Mensch. [A]
- Die Aufträge (K3 B3, „Clip für die Bäckerei“) sind das einzige System, das sich nach Geschäft anfühlt — und sie kommen erst nach Raum 3 (Minute ~21) und genau einmal je Welt. [A, K3_PACING]
- Referenz: Idle Bank zeigt Kundenschlangen und ein Statistik-Panel je Raum; Hotel Empire markiert jedes Möbel mit „Most profitable“/„Losses!“ und zieht Löhne ab; Idle Lumber hat ein Auftragsbrett mit drei Kundenaufträgen; Two Point Studios: „We want you to care about them“ [B, Q3 Q20 Q24 Q32]. Das Gefühl „echte Firma“ entsteht dort aus **Menschen, Kunden, Aufträgen und Kosten**, nicht aus Stationsnamen.

### 1.3 UI: Zu viele Ebenen gleichzeitig, und die Plakette ist kein Knopf

- `b1_ueberblick_k.png` zeigt gleichzeitig: Kopfleiste (4 Zahlen: 52 €, +2,4 €/s, 7,5 %, 4/5 +50), Zielleiste, 7 Raumplaketten mit vier verschiedenen Zeichen, Tutorial-Hand, Mo-Karte „Kenne ich schon“, Debug-Knopf. `k5_hinweis.png`: Erklärblase („Gelb: Gleich hast du genug …“) **und** Tobi-Szene **und** Zielleiste gleichzeitig — drei Textquellen. Hodent: in der Lernphase sind „3 items to process at the same time THE MAXIMUM“ [B, Q2].
- **Plakette:** Tipp öffnet im Überblick ein Sheet (Schnellkauf, `k4_schnell_raum.png`), im Raum zoomt die Kamera und öffnet eine Liste. Nie kauft der erste Tipp. Auf Bastians Handy stand der ältere Build (vor f355365) — dort führte der Tipp direkt in die Raumfahrt. Eatventure: „Tipp auf Station = sofort kaufen“ [B, Q10]; Idle Office: Pfeil-Icon am Raum = Level-up [B, Q8]. **Das ist Bastians Punkt „kann nicht einfach draufdrücken“.** [A]
- **Stationsmenü:** sieben Blöcke (Kopf, Stern, Engpass/Leistung, Kaufknopf, x1/x10/MAX, drei Ausstattungszeilen, Fußtext) — `b1_raum_k.png`. Eatventure hält das Upgrade-Menü bewusst minimal und sortiert billig → teuer [B, Q10]; PocketGamer.biz: „minimalistische Shop-Gestaltung“ [B, Q7-K3].
- **Kaufknopf-Muster ist dreimal verschieden:** grauer Pfeil-Knopf „82 € AUSBAUEN · in 0:01“, grüne Pille „40“ mit „+26 %“, Raum-Knopf „20.543 KAUFEN“ + „Noch 7.628 €“. [A, Bilder]

### 1.4 Popups: Jede Belohnung will ein Fenster

- Vor dem 16.10. waren Rang, Stern, Ziel, Marke, Raum, Kapitel je ein Vollbild. Der Arbeitsbaum vom 16.10. reduziert auf `vollbild_momente: ["raum"]` — richtig — **führt aber gleichzeitig neue Fenster ein:** Kapitelkarte mit „Weiter“-Knopf (`k5_kapitel.png`), Sammelfenster „6 Belohnungen“ (`k5_sammel.png`), Erklärblasen je Symbol. Dazu Szenen mit Antwortchips bei jedem Raumkauf, 24 Nachrichten je Welt, Tagesaufgaben-Chip, Marken-Toasts. [A]
- NN/g: Jede Unterbrechung „translates in lost time and effort“, Modals erzeugen „an extra goal — to dismiss the dialog“, Übernutzung erodiert Vertrauen, Modals nur für Kritisches [B, Q26]. Referenz-Idle-Games zeigen **ein** Modal je Sitzungsstart (Offline-Ertrag + Ad ×2) und sonst Zustand in der Welt [B, Q10 Q12 Q24].

### 1.5 Story: Zu viel, am falschen Ort, ohne Folge

- 24 Nachrichten × 6 Welten, 5+ Szenen je Welt, 4 Entscheidungen je Welt ohne Wirtschaftswirkung („Mo im Tresor lassen?“). Die K5-Regel „jede Nachricht zeigt auf eine Handlung“ ist gut, aber die Menge bleibt. Eatventure, Idle Miner, Burger Please tragen **keine** Dialogstory und sind die Umsatzführer [B, Q5 Q10 Q14]; Lessmore: „no long texts, no big tutorial“, Visuals „telling stories without requiring text“ [B, Q14]. Story darf bleiben — als **Mitarbeiter, die im Raum stehen**, nicht als Fenster.

### 1.6 Kamera: Vier automatische Fahrten, die der Spieler nicht ausgelöst hat

Aus `main.gd` und `world_camera.gd` [A, Code]:
1. Tipp auf Raum/Station → `kamera.betrete()` / `fokussiere()` (fährt hin, zoomt ein).
2. Menü schließen → `_pruefe_rueckfahrt()` → `kehre_zurueck()` (fährt zurück, zoomt aus).
3. Pinch loslassen → `raste_ein()` auf die nähere Raststufe (springt).
4. Nach dem ersten Raumkauf → `springe_stufe(UEBERBLICK)` (zoomt aus).
Jede einzelne ist begründbar; zusammen ergeben sie „es zoomt automatisch rein und raus“. Kein Referenzspiel hat belegte Kamerafahrten beim Kauf; die Kamera folgt dort dem Finger (Scroll) oder der Figur [A, Q-UI „nicht gefunden“].

**Kurz:** HELLO WORLD ist ein gut gemessener Zahlen-Motor mit einer Erzählschicht obendrauf. Top-Spiele sind eine **Welt, in der man arbeitet**, mit einem dünnen Zahlen-HUD darüber.

---

## 2. Das neue Konzept

### 2.1 Spielerfantasie in einem Satz

> **Ich baue aus einem WG-Zimmer eine Firma, die ich beim Wachsen zusehen kann: Aufträge kommen rein, meine Leute arbeiten sichtbar, Geld liegt am Ende der Kette, und jeder Kauf verändert den Raum.**

### 2.2 Drei Schleifen

**Kernschleife (Sekunden) — „Auftrag rein, Arbeit, Kasse“**
1. Ein **Auftrag** erscheint am Eingang der Kette (W1: Anfrage-Karte an der Pinnwand mit Absender „Bäckerei Kurz“; W3: Kundenfigur am Ladentisch; W4: Paketstapel am Wareneingang). Der Kern erzeugt ihn aus dem bestehenden Durchsatz; er ist **Darstellung**, kein neues Wirtschaftsobjekt.
2. Er wandert sichtbar durch die drei Stationen (bestehender `clip_fluss`). Am Engpass staut er sich — das ist der rote Zustand, ohne Schild.
3. Am Ende liegt **Geld auf der Kasse** (W1: auf dem Schreibtisch neben dem Laptop). Es wird automatisch gebucht (Kern), aber **ein Stapel ab n Einheiten ist tippbar** und zahlt einen kleinen Bonus (= bestehender `tippe_stapel`, auf jede Welt und auf die Kasse verlegt). Tippen ist nie Pflicht, nur Lust.
4. Der Spieler tippt die **grüne Plakette** des Raums oder den **Pfeil** an der Station: **ein Tipp = ein Kauf**. Zahl springt, Figur reagiert, Modell wechselt bei Stufe 1/5/10.

**Sitzungsschleife (8–10 Minuten) — „Zurück, aufräumen, einen Schritt weiter“**
Offline-Bericht (ein Fenster, mit ▶ ×2) → Kasse leeren (ein Tipp) → 3–6 Ausbauten über Plaketten → ein **Auftrag annehmen oder abliefern** (Auftragsbrett, immer genau einer aktiv, immer mit Absender und Belohnung) → ein **Mitarbeiter eingestellt** oder **Raum gekauft** (alle 10–15 min nach Simulator) → Boost gezündet (ab Minute 5) → Sitzungsende mit einem sichtbaren Ziel „Noch 7.600 € bis zum Wohnzimmer“. Kolibri plant mit ~10-Minuten-Sitzungen [B, Q19]; GameAnalytics misst Median 3–3,5 min, Top-Quartil ~5 min [B, Q25].

**Meta-Schleife (Tage) — „Standorte“**
- Welt-Ziel je Welt (Gaming-PC …) bleibt die große Leiste.
- **Sechs Welten = sechs Standorte** der einen Firma. Der Wechsel ist Expansion, kein Reset — belegt als Standardmuster (neue Stadt/Bank/Hotel; Supermarket, Lumber, Eatventure, Hotel) [B, Q10 Q13 Q24 Q1], nur dass bei uns nichts verloren geht. Die Standortkarte (K2 §6.3) zeigt das; alte Standorte **laufen weiter** und zahlen eine kleine Grundrente (wie Burger Please: „alte Filialen laufen weiter, per Karte abholen“ [B, Q2-UI]).
- **Mitarbeiterstamm** wächst über Standorte (Mo ab W1, Mira/Tobi, Younes ab W2, Roman ab W3, Jana ab W4, Selin ab W5). Jeder ist eine Figur mit Platz, Rang 1–3 und sichtbarem Modellwechsel. Das ersetzt Crew-Karten.
- **Firmenwert** als eine Zahl, die nie sinkt (Summe gekaufter Räume, Stufen, Mitarbeiter, Standorte) — im Fortschrittsmenü, nicht im HUD.
- Tag 2+: Tagesaufgaben werden zu drei „Kundenanfragen“ im Auftragsbrett (dasselbe System, kein eigener Chip).

### 2.3 Was der Spieler aufbaut und SIEHT (je Welt gleich, Namen aus `theme.json`)

| Ding | Heute | Neu | Kern/Darstellung |
|---|---|---|---|
| **Mitarbeiter** | Crew-Karte (Faktor) | Figur an der Station; „Einstellen“ = Rang 1, „Befördern“ = Rang 2/3; Namensschild über der Figur, Modell wechselt (Hoodie → Headset → Chef-Stuhl). W1: Mo (Aufnahme), Mira (Schnitt), Tobi (Idee) | Kern unverändert (`crew.raenge`), nur Darstellung + Texte |
| **Kunden/Aufträge** | 1 Auftrag je Welt nach Raum 3; Ziele als Liste | **Auftragsbrett:** immer genau 1 aktiver Auftrag = das aktuelle Ziel, mit Absender, Satz, Belohnung. Ziele bekommen `absender` + `satz` in `theme.json` (`ziel_formate` bleiben Fallback). Nach Abgabe liegt die Belohnung als Paket/Umschlag auf der Kasse (tippen). | Ziele-System bleibt; Texte + Darstellung |
| **Auftragsfluss** | Clip-Stapel am Engpass | Anfrage-Karte am Eingang, Einheiten wandern, Stapel am Engpass, **Geld auf der Kasse** am Ende | `clip_fluss.gd` + neuer Kassenpunkt in `worlds.json` |
| **Räume** | Schleier + Plakette | bleibt; Silhouette der neuen Station (K2) | — |
| **Firmenwert / Welt-Ziel** | % + Marken + Rang-Chip | Welt-Ziel-Leiste **ohne** Rang-Chip und Marken-Symbole; Marken nur als dünne Striche; Rang nur noch im Fortschrittsmenü | Darstellung |
| **Standorte** | Weltwechsel-Plakat | Standortkarte, alte Standorte sichtbar „läuft · +x €/min“ | Kern: kleine Grundrente je abgeschlossener Welt (Daten) |

### 2.4 Rolle der Figuren und der Story

- **Mo ist die einzige Erklärstimme** (K2 Regel 19 bleibt). Alle anderen Figuren sind **Mitarbeiter oder Kunden mit Platz im Raum**. Eine Nachricht erscheint **am Ort** als Sprechblase über der Figur (max. 90 Zeichen, 4 s, nie zwei gleichzeitig) und liegt danach im Posteingang. Sie erscheint **nur**, wenn sie eine Handlung hat (Kauf, Auftrag, Freischaltung) oder ein Raum gekauft wurde.
- **Szenen (Porträt-Popup mit Antworten): höchstens 3 je Welt** — Weltstart, Halbzeit, Cliffhanger. Raumkäufe sind der Raum-Moment (Vollbild bleibt), keine zusätzliche Szene.
- **Entscheidungen: höchstens 1 je Welt**, in der Halbzeit-Szene, mit einer sichtbaren Folge im Raum (Mos Namensschild hängt / hängt nicht). Die übrigen 18 Entscheidungen des Arbeitsbaums werden Antworten ohne Chip (Text bleibt im Posteingang).
- **Kapitel:** bleiben als Daten (`kapitel[]`), erscheinen aber **nie als Fenster**: Die Zielleiste trägt in der zweiten Zeile „Kapitel 2 · Zu wenig Platz“, 3 s eingeblendet beim Wechsel, dann klein stehend.
- Tonregeln 1–24 aus `STORY.md` gelten weiter. Neu: **Regel 25: Kein Text, der nicht neben einer Figur stehen könnte.**

### 2.5 Systeme: bleibt / umgebaut / gestrichen

| System | Entscheidung | Begründung |
|---|---|---|
| Kette, Engpass, Stufen, Sterne, Ausstattung, Räume, Welt-Ziel, Offline, Boost, Lieferkiste, Stapel, sechs Welten, Balance-Korridore | **bleibt** | gemessen, gesund; Choke-Points sind laut Kolibri „die Basis eurer Monetarisierung“ [B, Q19] |
| Raum-Plaketten (K4 P1.2/1.3) | **umgebaut zum Kaufknopf** (§4.3) | „Tipp = Handlung“ [B, Q10]; Bastians Punkt 2 |
| Crew-Karten | **umgebaut zu Mitarbeitern** (Figur, Name, Rang) | Fantasie; Idle Bank/Mafia/Lumber zeigen Manager als Personen/Karten [B, Q3 Q23 Q24] |
| Ziele + Tagesaufgaben + Aufträge | **zusammengelegt zum Auftragsbrett** (1 aktiv, 3 sichtbar) | drei sichtbare Missionen ist Genre-Standard (Bank, Office, Mafia, Lumber) [B, Q3 Q8 Q23 Q24] |
| Rang (30 Stufen) | **bleibt im Kern, stumm in der Darstellung**: Chip raus, Vollbild raus, Freischaltungen als Mo-Blase am neuen Knopf | K2-Rang löst Menü-Gating; das Fenster dazu ist der Spam, den Bastian meint |
| Kapitelkarte (K5, Arbeitsbaum) | **kein Modal**, Zeile in der Zielleiste | NN/g: Modals nicht für „nonessential information“ [B, Q26] |
| Sammelfenster „n Belohnungen“ (K5) | **nur im Offline-Bericht**, sonst gestrichen | ein Fenster je Sitzungsstart ist Genre-Standard [B, Q10 Q12] |
| Erklärblasen je Symbol (K5 P1.9) | **ins Tutorial** (eine Legende, einmal), sonst gestrichen | nie zwei Textquellen |
| Szenen bei jedem Raumkauf, 4 Entscheidungen/Welt | **gestrichen** (→ 3 Szenen, 1 Entscheidung je Welt) | §1.5 |
| Marken-Toasts, Stern-Toasts, Erfolge-Fenster, „Kenne ich schon“, Nebenraum-Karten | **gestrichen** | Rauschen ohne Handlung |
| Fortschritt-Menü als eigener Knopf | **gestrichen**, Inhalt unter Aufträge → Reiter „Firma“ | weniger Menüs |
| Automatische Kamerafahrten (4 Stück) | **gestrichen**, außer einmal im Tutorial (§4.1) | Bastians Punkt 1 |
| Pinch-Einrasten | **gestrichen** (stufenlos 10–zoom_max) ; Doppeltipp bleibt als freiwilliger Sprung | „das soll man selbst einstellen“ |
| x1/x10/MAX | **bleibt**, aber nur im Stationsmenü, Standard „x1“, zuletzt gewählt gemerkt | belegt für Idle Miner [B, K4] |
| Reset-Prestige, Hartwährung, Lootboxen, Events, Interstitials | **nicht in 1.0** | §6, §8 |

---

## 3. Psychologie-Plan

Grundlage: Kompetenz + Autonomie tragen Bindung („controls that were easily mastered; feedback that was clear and consistent“) [B, Q1]; Zielgradient: Tempo steigt nahe am Ziel, nach der Belohnung „post-reward reset“ [B, Q3]; Pecorella: „Goals and achievements spread moments of joy across the experience“, „Make It Bumpy“ [B, Q6]; Erwartung zählt mehr als die Belohnung selbst — Dopamin kodiert den Vorhersagefehler [A, Schultz]; „The novelty of big numbers on their own is largely gone“ [B, Q7].

### 3.1 Echte Belohnungsmomente (was sie auslöst, wie oft, wie groß)

| # | Moment | Auslöser | Phase 0–5 min | 5–30 min | Sitzung 2+ | Darstellung (Juice-Stufe) |
|---|---|---|---|---|---|---|
| 1 | **Kauf** (Plakette/Pfeil) | Tipp | 4–6/min | 2–4/min | 1–3/min | klein: Zahl springt, Münzflug, Figur nickt |
| 2 | **Modellwechsel** (Stufe 1/5/10 Ausstattung) | Kauf | 1–2 | alle 3–5 min | je Sitzung 1–2 | mittel: Objekt ploppt auf, 1 s Funken, Blase der Figur („Endlich ein Stativ“) |
| 3 | **Stern** (×1,5 alle 10 Stufen) | Kauf | 1 (Min 4–5) | alle 4–6 min | 2–4/Sitzung | mittel: Schild blitzt gold, Ton, Zahl „×1,5“ 1,5 s über der Station |
| 4 | **Kasse leeren / Stapel tippen** | Stapel ≥ n | 2–3 | alle 1,5–2,5 min | je Rückkehr 1 | klein–mittel: Geldstapel fliegt in die Kopfleiste |
| 5 | **Auftrag abgeliefert** (Ziel erfüllt) | Zielbedingung | 2 | alle 3–6 min | 3–6/Sitzung | mittel: Umschlag auf der Kasse, Tipp → Betrag zählt hoch in der Leiste; **kein Fenster** |
| 6 | **Mitarbeiter eingestellt / befördert** | Kauf | 0 | 1 (Min ~30 W1) | 1/Sitzung | groß: Figur kommt durch die Tür, Namensschild, Konfetti klein |
| 7 | **Raum gekauft** | Kauf | 1 (Min ~3:30) | alle 10–13 min | 1/Sitzung | groß: **einziges Vollbild im Spielfluss** (Schleier fällt, Station erscheint, Figur läuft rein) |
| 8 | **Lieferkiste** | Kern-Moment | 1 | alle 2–4 min | 1–2 | mittel; mit ▶-Option (15 min Einkommen) |
| 9 | **Fast geschafft** (Plakette gelb ≥ 60 %, Puls ab 80 %) | Kapital | 1–2 | dauernd 1 sichtbar | — | Zielgradient [B, Q3]: Füllring auf der Plakette, kein Text |
| 10 | **Offline-Bericht** | Rückkehr | — | — | 1/Sitzung | **ein** Fenster, Mo, Betrag zählt, ▶ ×2 |
| 11 | **Boost** | Spieler | 0 (Geschenk-Boost ab Min 5) | 1 | 1–2 | Knopf atmet, Welt bekommt Lichtkante, Zahlen laufen schneller |
| 12 | **Welt-Ziel-Marke** (25/50/75 %) | Fortschritt | — | 1 | — | Leiste füllt mit Strich, Silhouette des Gaming-PC füllt sich (K2 §6.1) — stumm |
| 13 | **Weltabschluss / neuer Standort** | 100 % | — | — | Tag 1–2 | groß: Abschluss-Szene + Standortkarte (Vollbild, einmal je Welt) |

**Takt-Ziel (messbar):** Minute 1–10 ≥ 2 Momente/min, danach ≥ 0,5/min, nie > 3 min ohne (K3 K4). Kiste + Kasse + Auftrag zusammen erfüllen das in der Simulation, ohne Fenster.

**Variable Belohnung ohne Glücksspiel:** Kiste und Momente haben variable Höhe (schon da: `gross_chance 0,08`), aber **nie Niete** und **nie gegen Geld**. Zufällige Gratis-Belohnungen fallen nicht unter die Play-Pflicht zur Wahrscheinlichkeitsangabe [B, Q12-Psy; A]. Keine Truhen gegen Hartwährung in 1.0.

**Verlustaversion offline:** Deckel 4 h → 12 h über Ränge bleibt; der Bericht sagt „Du hättest mehr verdient: Kauf das Wohnzimmer“ **nicht** — wir strafen nicht (Hodent: „Avoid punishing states“ [B, Q2]). Der Deckel selbst ist der Rückkehrgrund [B, Q6 Q10].

### 3.2 Spam-Liste — was NICHT mehr passiert

- Kein Rang-/Level-Fenster, kein „Aufgestiegen“ (auch nicht als Sammel-Eintrag).
- Kein Erfolgs-Fenster, keine Erfolge-Toasts. Erfolge bleiben als Liste im Menü.
- Keine Kapitelkarte als Modal.
- Kein Sammelfenster „n Belohnungen“ außer im Offline-Bericht.
- Keine Szene beim Raumkauf (der Raum-Moment ist die Szene).
- Keine Marken-Toasts, keine Stern-Toasts am Rand; Stern und Modellwechsel passieren **am Objekt**.
- Keine Erklärblase, solange ein Fenster, eine Szene oder die Tutorial-Hand aktiv ist. Genau eine Erklärblase je Symbol, nur im Tutorial.
- Keine zwei Textquellen gleichzeitig (Zielleiste zählt nicht als Text, solange sie sich nicht ändert).
- Kein „Kenne ich schon“-Knopf in Blasen (Blasen verschwinden von selbst nach 4 s).
- Kein Banner „Nachricht von Mira“ — Nachrichten ohne Handlung gehen still in den Posteingang (Abzeichen zählt).
- Kein Werbeangebot vor Minute 5 / vor Raum 1, nie als Fenster, nie bei Geldmangel (My Perfect Hotel tut genau das und wird dafür in Reviews abgestraft [B, Q1-Mon]).

---

## 4. UI-Grundgesetz

### 4.1 Kamera — nur der Spieler bewegt sie

1. **Keine automatische Fahrt** beim Tipp auf Raum, Station, Plakette, beim Öffnen oder Schließen eines Menüs, nach einem Kauf. Streichen: `_betrete_zone` → `kamera.betrete`, `_pruefe_rueckfahrt`, `_fokussiere_punkt` bei Stationstipp, `springe_stufe(UEBERBLICK)` nach Raum 1.
2. **Pinch ist stufenlos** zwischen `zoom_min` und `zoom_max` und rastet **nicht** ein (`raste_ein` nur noch für Mausrad am PC). Wischen bleibt wie heute (Finger-exakt).
3. **Doppeltipp auf freien Boden** springt zwischen Raum- und Überblicksstufe — freiwillig, vom Spieler ausgelöst. Das ist die einzige Fahrt im Normalspiel.
4. **Menüs dürfen die Karte nicht verschieben.** Ein Sheet deckt höchstens 45 % der Höhe; liegt das Tippziel darunter, ist das die Entscheidung des Spielers (er kann wischen). Ausnahme: das Tutorial (Punkt 5).
5. **Genau zwei Kamerafahrten im Tutorial:** (a) Sekunde 0 → Fahrt vom Überblick auf das Zimmer (Ankommen), (b) nach dem ersten Raumkauf (Minute ~3:30) einmal hinaus auf den Überblick mit Mos Satz „Mit zwei Fingern zoomst du. Doppeltipp springt.“ Danach nie wieder.
6. **Startzoom je Sitzung = letzter Zoom des Spielers** (im Spielstand), nicht `zoom_start`. Erststart: Raumstufe auf dem Zimmer.
7. Richtungs-Tabs am Rand bleiben (nächster kaufbarer Raum außerhalb des Bildes); Tipp darauf fährt hin — ausgelöst vom Spieler, erlaubt.

Referenz: Für kein Referenzspiel ist eine Kaufkamera belegt; Kamera folgt Finger oder Figur [A, Recherche UI „nicht gefunden“]. Bastians Urteil ist hier die Quelle.

### 4.2 Tippziele

- Alles Tippbare ≥ 96 logische px (48 dp), Hitbox getrennt von der Grafik (K3, bleibt). Plaketten ≥ 96 × 56 px, Pfeile 96 × 96.
- **Trefferreihenfolge bei Überlappung:** Plakette/Pfeil > Stapel/Kiste > Figur („!“) > Station > Raumboden > nichts. Ein Tipp trifft genau eines.
- Tipp auf „nichts“ schließt offene Sheets, sonst nichts (kein Zoom, keine Fahrt).

### 4.3 Ein Kaufknopf-Muster — überall dasselbe

**Die Pille:** links Symbol, Mitte Name + Nutzen (`+12 €/s` oder `Neu: Upload`), rechts Preis. Vier Zustände, Form **und** Farbe:

| Zustand | Aussehen | Tipp |
|---|---|---|
| bezahlbar | Limette, schwarzer Text, Preis fett | **kauft sofort** (ein Tipp) |
| fast (≥ 60 %) | Papier, Füllring am Preis, ab 80 % Puls | öffnet Sheet mit „Noch 1.240 €“ und ▶-Option ab 70 % (Raum) |
| nicht bezahlbar | Papier, Preis grau | öffnet Sheet (Information) |
| gesperrt | Papier, Schloss, Bedingung statt Preis („nach dem Wohnzimmer“) | Sheet mit Bedingung |

Dieses Muster gilt für: **Raum-Plakette im Überblick** (Nutzen = bester Kauf im Raum, Preis = sein Preis; Tipp kauft genau diesen Kauf), **Stationspfeil im Raum** (Tipp kauft eine Stufe), **Ausstattungszeile**, **Mitarbeiter-Zeile**, **Raumkauf**, **Sheet-Hauptknopf**. Langdruck (0,4 s) auf eine Plakette öffnet das Raum-Sheet mit allen Käufen des Raums — für die, die wählen wollen.
Referenzen: Eatventure Tipp = Kauf [B, Q10]; Hotel Empire zeigt Profit blau + Zuwachs grün im Knopf [B, Q20]; Idle Office Pfeil-Icon = Level-up am Raum [B, Q8]. Risiko Fehlkauf: nur günstigste Stufe/x1 per Direkttipp; x10/MAX nur im Stationsmenü.

### 4.4 Popup-Regeln

| Ebene | Was | Höchstens | Schließt sich |
|---|---|---|---|
| **Fenster (modal)** | Offline-Bericht · Raum-Moment · Weltstart/Halbzeit/Cliffhanger-Szene · Weltabschluss · Weltwechsel · Einstellungen | **1 je Anlass, max. 1 je Sitzungsstart** (Offline). Nie zwei hintereinander ohne Spieleraktion dazwischen (Raum-Moment nach Offline wartet bis zum ersten Tipp). | Knopf oder Tipp außerhalb |
| **Sheet (halbhoch)** | Raum-Sheet, Stationsmenü, Auftragsbrett, Posteingang | 1 zur Zeit, ≤ 45 % Höhe, Karte bleibt tippbar | Tipp außerhalb, Wischen nach unten |
| **Blase in der Welt** | Mo/Figur-Satz ≤ 90 Zeichen | 1 zur Zeit, 4 s, Warteschlange max. 2, Rest still in den Posteingang | von selbst |
| **Toast oben** | nur Systemdinge („Gespeichert“, „Keine Verbindung“) | 1, 2 s | von selbst |
| **Am Objekt** | Stern ×1,5, Modellwechsel, +Betrag | beliebig, 1–1,5 s | von selbst |

Regel: **Solange ein Fenster oder eine Blase steht, erscheint keine zweite Textquelle.** Die `ModalSchlange` setzt das durch; `LEICHT` (Blasen) wartet, bis das Fenster zu ist, und verfällt nach 20 s ungelesen.

### 4.5 Menüstruktur — was es überhaupt noch gibt

Unten **drei Knöpfe + Boost in der Mitte**, oben **ein** Zahnrad:

| Knopf | Inhalt | Ersetzt |
|---|---|---|
| **Firma** (Werkzeug) | Liste aller Käufe im aktuellen Standort, sortiert billig → teuer (Eatventure [B, Q10]), erste Zeile hervorgehoben „Beste Wahl“; Reiter: Ausbau · Leute · Räume | Ausbau-Menü, Crew-Menü |
| **Boost** (Mitte, ▶ ×1,5 · 30 Min) | Dauerknopf; vor Minute 5 unsichtbar | Schub-Knopf |
| **Aufträge** (Klemmbrett) | 1 aktiver Auftrag groß, 2 weitere, Tagesanfragen ab Tag 2; Reiter „Standorte“ (Standortkarte, Firmenwert, Rang, Erfolge-Liste) | Ziele, Tagesaufgaben-Chip, Fortschritt-Menü |
| **Posteingang** (Handy) | Nachrichtenverlauf, Antworten | Handy |
| Zahnrad | Ton, Haptik, Datenschutz, Spielstand | Einstellungen |

Freischaltung über den Rang (bleibt): Start **ohne** Leiste; Firma ab Rang 2 (~Min 2), Aufträge ab Rang 2, Boost ab Rang 3 (~Min 6), Posteingang mit der ersten Nachricht. Jede Freischaltung = Knopf ploppt auf + eine Mo-Blase, kein Fenster. Idle Bank schaltet Manager ab Ruf 6, Business-Modus ab 7 frei [B, Q3].

### 4.6 Kopfleiste — zwei Zahlen

Links: **Kontostand** + `+€/s`. Rechts: **Welt-Ziel-Leiste** („Der Gaming-PC · 29 %“), Marken als dünne Striche ohne Symbole, zweite Zeile Kapitel-Titel klein. Weg: Rang-Chip, „Anfang“, Geschenk-Symbole auf der Leiste. Darunter die **Zielleiste = aktiver Auftrag** (Absender-Symbol, Satz, Balken, Belohnung) — die einzige weitere Leiste. Zwei Leisten oben, nie drei (K3).

### 4.7 Visuelle Hierarchie (Reihenfolge der Aufmerksamkeit)

1. Grün pulsierend = genau **ein** Ding (der beste Kauf). 2. Rot = genau **ein** Ding (Engpass, als Stau/Plattenrand, kein Schild). 3. Gelb = fast (Füllring). 4. Figuren mit Namensschild. 5. Papier = alles Übrige. Deko ≤ 5 Teile je Raum, entsättigt (K3). Schrift nie < 11 px in der 540er-Vorschau. Sticker-Pop bleibt.

---

## 5. Onboarding — die ersten 5 Minuten, Sekunde für Sekunde

Prinzipien: eine Stimme, ein Knopf, erstes Upgrade < 10 s, Werbung nie vor Minute 5 [B, Q17 Q19]; Supersonic verlor „60 % during the tutorial“ bei zu schnellem Mechanikwechsel [B-V, Q17]; AFK Arena: Tutorial < 5 min, kein IAP/Ad-Popup beim Start [B-V, Q22]; Burger Please: „etwa eine Viertelminute“ Tutorial, nur rote Pfeile [B, Q2-UI].

| Zeit | Bild | Spieler | Spiel antwortet | Kamera |
|---|---|---|---|---|
| 0:00 | Key-Art, Titel | tippt „Los geht's“ | — | — |
| 0:02 | Fahrt vom Überblick ins Zimmer (2 s). Mo steht neben der Pinnwand. Kopfleiste nur „30 €“. Keine Leisten, keine Knöpfe. | sieht zu | Mo-Blase: „Dein erster Clip hat drei Aufrufe. Zwei warst du.“ | **Fahrt 1 (einzige)** |
| 0:06 | Grüner Pfeil pulst an der Pinnwand, Hand zeigt | tippt Pfeil | **Kauf.** Zahl „+0,5 €/s“ fliegt hoch, Pinnwand bekommt Zettel. Mo: „Mehr Ideen, mehr Clips, mehr Geld.“ | steht |
| 0:12 | Pfeil pulst weiter | tippt 2–3× | Käufe. Erste Anfrage-Karte erscheint an der Pinnwand und wandert zur Aufnahme | steht |
| 0:25 | Aufnahme staut (rot: Karten stapeln sich). Pfeil wechselt zur Aufnahme | tippt | Mo: „Rot heißt Stau. Das Rote zuerst.“ Kauf, Stau löst sich sichtbar | steht |
| 0:45 | Erster Clip erreicht den Schnitt → **Geld liegt auf dem Schreibtisch** (Stapel) | tippt Stapel | Münzen fliegen, +8 €. Mo: „Fertige Clips bringen Geld. Liegt was da, nimm's mit.“ | steht |
| 1:00 | Zielleiste erscheint: **Auftrag „Mira: Ein Clip für die WG-Party · Schnitt Stufe 5 · 50 €“** | baut weiter | Mo: „Dein erster Auftrag. Steht oben.“ | steht |
| 1:40 | Auftrag erfüllt → Umschlag auf der Kasse | tippt Umschlag | +50 € zählt in die Kopfleiste; Welt-Ziel-Leiste erscheint und springt 0 → 3 % „Der Gaming-PC“. Mo: „Jeder Auftrag bringt den PC näher.“ **Kein Fenster.** | steht |
| 2:00 | Ausstattungszeile im Stationsmenü leuchtet (erste Sheet-Öffnung: Tipp auf das Stationsschild) | kauft Stativ | **Modellwechsel:** Handy auf Büchern → Stativ. Mo: „Steht jetzt wirklich da.“ Sheet schließt von selbst | steht |
| 2:30 | **Rang 2** (stumm): Knopf **Firma** und **Aufträge** ploppen unten auf | sieht | Mo: „Unten: alles, was du kaufen kannst, billigstes zuerst.“ | steht |
| 3:00 | Flur-Plakette wird gelb (Füllring), ab 80 % Puls | sieht/spart | — | steht |
| 3:30 | Plakette grün | tippt Plakette | **Raum-Moment (Vollbild):** Schleier fällt, Router erscheint, Mo läuft hin. „Dein Upload läuft von allein.“ | nach dem Fenster **Fahrt 2:** hinaus auf Überblick, Mo: „Zwei Finger zoomen. Doppeltipp springt.“ |
| 3:45 | Überblick: 2 Plaketten aktiv, Rest Papier/Schloss | zoomt selbst | — | Spieler |
| 4:00 | Tutorial endet (Hand weg). Posteingang-Knopf erscheint mit erster stiller Nachricht (Mira) | frei | — | Spieler |
| 5:00 | Erste **Lieferkiste** vor der Tür (ohne ▶); Boost-Knopf erscheint grau mit „Geschenk“ (10 min, ohne Werbung) | tippt | Kiste zahlt 1 min Einkommen; Boost läuft, Welt bekommt Lichtkante | Spieler |

Bis Minute 5 **nicht**: Werbung, Szene mit Antworten, Kapitelkarte, Rang-Fenster, Handy-Banner, mehr als eine Blase, mehr als zwei Leisten. Erste Szene (Antwort) frühestens bei der Küche (~Min 10).

---

## 6. Werbung

**Markt, belegt:** Zwei Lager — **Rewarded-only** (Kolibri: ~60 % des Umsatzes aus Werbung, ~8 Ads/Spieler/Tag, 52 % Ad-Engagement; Eatventure: Mehrheit Werbeumsatz, kein No-Ads-Produkt) [B, Q19 Q4-Mon Q6-Mon] und **Interstitial-schwer + billiges No-Ads** (My Perfect Hotel: Interstitial ab 2:19, Tester 528 Rewarded in 19 Sitzungen, No-Ads ~10 $; Burger Please: 30 Interstitials in Sitzung 1, No-Ads 3,99 $; Supercent ~70/30 Ads/IAP) [B, Q1-Mon Q10-Mon; A, Q12-Mon]. Ein Entwickler berichtete −33 % D1 nach Einführung von Interstitials [B, Q13-Mon]; Azur Games erzielte +7 % LTV mit skippbaren Interstitials **nur** bei 7–8 Rewarded/Tag [B-V, Q29-Mon]. eCPM Rewarded Android Europa ≈ 5 $ (Appodeal Q4 2024), US 13–30 $ je Sample, Deutschland nicht einzeln belegt [B-V, Q27-Mon]. Rechenbeispiel (K3 §7.4): bei 1.000 DAU und 6 Ads/Tag ≈ 30 $/Tag — Werbung trägt erst mit Reichweite.

**Entscheidung für 1.0:** Rewarded-only, wie `ads.json` es schon anlegt. Interstitials sind eine offene Entscheidung (§8.1).

### 6.1 Platzierungen (alle mit Gegenwert im Knopf, alle in `data/services/ads.json`)

| Platzierung | Wo | Gegenwert | Warum Spieler sie gern nehmen |
|---|---|---|---|
| **Boost** | Dauerknopf Mitte unten | ×1,5 · 30 Min, stapelbar 2 h; erster Boost geschenkt | Standard in allen Referenzen [B, Q3 Q13 Q23 Q24]; sichtbar, planbar |
| **Willkommen zurück ×2** | Offline-Bericht | Offline-Ertrag ×2 (Empfehlung: Faktor 2 statt heute 3 — Idle Bank/Eatventure ×2; ×3 wirkt wie Druck) | größter Betrag der Sitzung, Spieler ist ausgeruht [B, Q3 Q10] |
| **Lieferkiste** | vor der Tür, alle 2–4 min | ohne ▶ 1 min Einkommen, mit ▶ 15 min | Eatventure-Investor: „leuchtet, verschwindet“ [B, Q10]; Wahl bleibt |
| **Rest geschenkt** | Raum-Sheet ab 70 % gespart | Raum sofort | Zielgradient-Moment, einmal je Raum (K3 C1) |
| **Auftrag ×2** | Umschlag auf der Kasse | Belohnung des Auftrags ×2 | My Perfect Hotel/Idle Office verdoppeln Quest-/Level-Belohnung per Ad [B, Q1-Mon Q8] |
| **Agent kommt** (ab Welt 2) | Figur läuft herein, 20 s | großer Betrag (Mystery, variabel) | variable Höhe, nie Niete [B, Q6-Psy] |

### 6.2 Frequenz und Schutz

- Erst ab **Minute 5 und Raum 1** (steht in `ads.json → erst_ab`).
- Höchstens **ein** ▶ gleichzeitig sichtbar außer dem Dauer-Boost; Mindestabstand 180 s; 10/Tag (steht); Zielbereich 5–8/Tag/aktivem Spieler [B, Q19].
- Ablehnen kostet nichts; jede Platzierung hat die Ohne-Werbung-Variante (Kiste 1 min, Offline ×1, Raum sparen).

### 6.3 Nie

- Keine Interstitials, keine Banner, keine App-Open-Ads in 1.0.
- Keine Werbung als Fenster, bei Geldmangel, beim Schließen eines Menüs, im Tutorial, als Bedingung für Fortschritt.
- Kein Boost-Faktor, der den Korridor um > 20 % drückt (`welt_sim --mit-boost`).
- Kein „No-Ads“-Kauf, solange es nichts Erzwungenes gibt, das er entfernen würde.
- Einwilligung (UMP) vor der ersten Anzeige, `anbieter: "stub"` bis Florins AdMob-Konto und `docs/release/ADMOB.md` fertig sind.

---

## 7. Umsetzungsplan in Wellen

Jede Welle ≤ 1 Tag Agentenarbeit je Paket, Pakete einer Welle laufen parallel, **je Datei genau ein Besitzer je Welle**. `game/main.gd`, `data/i18n/de.json`, `validate.ps1`, `data/ui/hinweise.json`: nur Leitung. `validate.ps1` erst, wenn alle Schreiber fertig sind. Scratchpad-Präfix `k6_<paket>_`. Vorschauen `bash tools/serie.sh k6<paket>_<name> …`; Bedienprüfung am PC über die Testumgebung `bash tools/pc_test.sh --frisch …` + `bash tools/pc_cmd.sh "tipp|wisch|pinch|zustand|bild"` (`docs/PC_TEST.md`, echte Touch-Ereignisse, Log je Befehl); Handy `.\deploy.ps1` + `.\tools\screenshot.ps1` nach `shots/k6/`.

**Vorab (Leitung, 1 h):** Der Arbeitsbaum vom 16.10. (Kapitelsystem, Sammelfenster, Erklärblasen) wird **nicht** so committed. Behalten: `vollbild_momente`, Rang/Stern als „kleiner Weg“, Szenen-Entstauung (nur neueste), Kapitel-Daten im Kern. Zurückbauen in Welle 1c: Kapitelkarte als Modal, Sammelfenster außerhalb Offline, Erklärblasen außerhalb Tutorial.

### Welle 1 — Bastians vier Punkte, sofort am Handy prüfbar

| Paket | Dateien (exklusiv) | Was | Abnahme |
|---|---|---|---|
| **1a Kamera** | `game/world/world_camera.gd`, `game/main.gd` (nur Kamera-Aufrufe: `_betrete_zone`, `_pruefe_rueckfahrt`, `_fokussiere_punkt`, `_fokussiere_station`, Zeile ~1588), `data/worlds/worlds.json` (nur `karte`), `core/save/save_data.gd` (Feld `zoom`), `tests/unit/test_raumkarte.gd` | §4.1: alle vier Fahrten raus, Pinch ohne Einrasten, Doppeltipp bleibt, Zoom im Spielstand, zwei Tutorial-Fahrten über `tutorial_ereignis` | PC (`bash tools/pc_test.sh --frisch --tiefe 2`, dann `pc_cmd.sh`): `zustand` → Zoom merken, `tipp` auf Raum, `tipp` ins Leere, `pinch 20 60` loslassen → `zustand` zeigt **denselben bzw. den selbst gewählten Zoom**, keine Fahrt im Log. `grep -n "betrete(\|kehre_zurueck(\|fokussiere(" game/main.gd` liefert nur noch die zwei Tutorial-Stellen. Handy: Pinch → Loslassen → Bild bleibt stehen (2 Screenshots); Menü öffnen/schließen bewegt die Karte nicht; App neu starten → letzter Zoom |
| **1b Plakette = Kaufknopf** | `game/ui/kartenmarker.gd`, `game/ui/menues.gd` (nur `Schnellkauf`, `Bereichsmenue`), `core/game_core.gd` (nur `kaufe_empfehlung(bereich_id) -> bool`, delegiert an bestehende Kauf-Befehle), `tests/unit/test_kartenmarker_pfeil.gd` (+ neu `test_plakette_kauf.gd`) | §4.3: Tipp auf grüne Plakette kauft den empfohlenen Kauf sofort (Münzflug, Zahl), Langdruck 0,4 s öffnet Raum-Sheet; gelb/grau/Schloss öffnen Sheet; Plakette zeigt Nutzen + Preis statt Zahl allein; Stationspfeil im Raum kauft eine Stufe | PC (`pc_test.sh --frisch --tiefe 2 --ueberblick`): `pc_cmd.sh "tipp <Plakette>"` → Log `traf: plakette bereich_1`, `zustand` zeigt Stufe +1 und **kein offenes Sheet**; `bild` vor/nach angesehen. Test: Kauf nur im Zustand `kaufbar`, nie doppelt bei Doppeltipp (Sperre 350 ms). Handy: 10 Plakettentipps = 10 Käufe, 0 Fehlkäufe |
| **1c Fenster-Diät** | `game/ui/hud.gd`, `game/ui/kapitel_view.gd`, `game/ui/moment_view.gd`, `game/ui/modal_schlange.gd`, `game/ui/saft.gd`, `game/ui/symbol_hinweise.gd`, `data/ui/hinweise.json` (Leitung schreibt Werte zu: `blase_dauer_s 4`, `blasen_max 2`, `kapitel_als_fenster false`), `tests/unit/test_modal_schlange.gd` | §3.2, §4.4: Kapitel → Zeile in der Zielleiste; Sammelfenster nur im Offline-Bericht; Erklärblasen nur bei `tutorial_aktiv`; eine Blase zur Zeit, Warteschlange 2, Verfall 20 s; Raum-Moment nach Offline wartet auf ersten Tipp; Rang-Chip aus der Kopfleiste | PC: `serie.sh k6_1c_tiefe --tiefe 3 --offline 7200`: genau **ein** Fenster (Offline), danach Bild ohne Fenster bis zum Tipp. `--tiefe 2 --kapitel 2`: kein Modal, Zeile sichtbar. Test: `ModalSchlange` zeigt nie zwei nicht-leichte Arten hintereinander ohne `spieler_tipp`. Handy 5 min: ≤ 2 Fenster insgesamt (Offline + 1 Raum) |
| **1d Nachrichten W1–W6** (6 Agenten, je eine Datei) | `data/themes/<welt>/theme.json` (alles außer `tutorial.zoom`) | §2.4: Szenen auf 3 je Welt (`szene:true` nur Start, Halbzeit, Cliffhanger), Entscheidungen auf 1 je Welt (`antworten` sonst entfernen, Reaktion als zweite Blase), alle Nachrichten ≤ 90 Zeichen, jede mit Handlung; Ziele bekommen `absender` + `satz` (Vorbereitung Welle 2) | `welt_sim -- <welt>`: 3 Szenen, 1 Entscheidung, 0 Blasen > 90 Zeichen (neuer Check in `test_balance_data`/`test_themen`); Sperrwort-Prüfung grün; Lesung: jede Nachricht nennt Raum oder Station |
| **1e Handy-Protokoll** (Leitung) | `docs/neu/K6_HANDYTEST.md`, `shots/k6/` | festes 5-Minuten-Protokoll (K3_AB §3.3) mit Zählung: Fenster, Blasen gleichzeitig, Fehltipps, Käufe/min, Kamerabewegungen ohne Finger | Tabelle ausgefüllt, Bilder angesehen; Bastian bekommt Build + drei Fragen (§8) |

Reihenfolge: 1a ‖ 1b ‖ 1c ‖ 1d (6×) → Import → `validate.ps1 -SkipBuild` → `deploy.ps1` → 1e. Konflikt: `hud.gd` nur in 1c; 1b ruft bestehendes `hud.zeige_schnellkauf` nicht mehr aus dem Marker, sondern `kern.kaufe_empfehlung` — kein Schreibzugriff auf `hud.gd`.

### Welle 2 — Firma sichtbar: Mitarbeiter, Auftragsbrett, drei Menüs

| Paket | Dateien | Was | Abnahme |
|---|---|---|---|
| **2a Mitarbeiter** | `game/world/e_lebendig.gd`, `game/world/e_lebendig_daten.gd`, `game/world/station_view.gd` (Namensschild), `data/worlds/worlds.json` (nur `figuren.plaetze`), `data/themes/*/theme.json` (nur `crew.<station>.{name, titel_1..3}`), `assets/characters/gemeinsam/` (3 Rang-Varianten je Figur, Blender-Skript `art_source/scripts/build_crew_raenge.py`), `tests/unit/test_crew_darstellung.gd` | Crew-Rang 1 = Figur erscheint an der Station durch die Tür, Namensschild; Rang 2/3 = Modellwechsel; Kern unverändert | `serie.sh k6_2a_crew --tiefe 3`: Figuren an 3 Stationen mit Schildern; Rangkauf im Sim → Modell wechselt; keine Ersatzwelt-Warnung in 6 Welten |
| **2b Auftragsbrett** | `game/ui/menues.gd` (nur `Zielemenue` → `Auftragsbrett`, `Fortschrittsmenue` einfalten), `game/ui/hud.gd` (nur Zielleiste), `core/game_core.gd` (nur `ziel_info` + `absender`), `tests/unit/test_auftragsbrett.gd` | 1 aktiver Auftrag groß mit Absender/Satz/Belohnung, 2 weitere, Tagesanfragen als Reiter; Belohnung als Umschlag auf der Kasse (Darstellung 2c) | `serie.sh k6_2b_brett --menue ziele --tiefe 2`: Absender sichtbar; Zielleiste zeigt Absender-Symbol |
| **2c Kasse + Anfrage** | `game/world/clip_fluss.gd`, `game/world/lieferkiste.gd` (Umschlag-Variante), `data/worlds/worlds.json` (nur `kasse {x,z}`, `eingang {x,z}` je Welt), `core/simulation/moment_system.gd` (Art `&"kasse"`), `tests/unit/test_moment_system.gd` | Anfrage-Karte am Eingang, Geldstapel an der Kasse ab n Einheiten tippbar (nutzt `tippe_stapel`), Umschlag nach Auftrag | `serie.sh k6_2c_kasse --tiefe 1 --zoom 14`: Stapel auf der Kasse sichtbar ≥ 72 px; Test: Stapelbonus ≤ 2 % des Einkommens/min |
| **2d Menüleiste 3+1** | `game/ui/menueleiste.gd`, `game/ui/kopfleiste.gd`, `data/balance/erfolge.json` (nur `freischaltung`), `data/i18n/de.json` (Leitung) | Firma · Boost · Aufträge · Posteingang; Kopfleiste zwei Zahlen; Rang-Chip weg | `serie.sh k6_2d_leiste --tiefe 2`: 3 Knöpfe + Mitte; `--store --frisch`: 0 Knöpfe bei Start |
| **2e Kaufpille überall** | `game/ui/stationsmenue.gd`, `game/ui/sheet.gd`, `game/ui/ui_stil.gd` (nur `kaufpille()`), `tests/unit/test_tippflaechen.gd` | ein Muster (§4.3) in Stationsmenü, Ausstattung, Raum-Sheet, Firma-Liste; Stationsmenü auf 4 Blöcke (Kopf, Pille, x1/x10/MAX klein, Liste) | `serie.sh k6_2e_station --menue station_processing --tiefe 2`: 4 Blöcke, Pille identisch zu Raum-Sheet |

### Welle 3 — Onboarding neu, Werbung sichtbar, Messung

| Paket | Dateien | Was | Abnahme |
|---|---|---|---|
| **3a Tutorial 5 min** | `data/tutorial/tutorial.json`, `game/ui/tutorial_ablauf.gd`, `game/ui/tutorial_view.gd`, `game/ui/zeige_hand.gd`, `data/themes/zimmer/theme.json` (nur `tutorial`), `tests/unit/test_tutorial_ablauf.gd` | Ablauf aus §5: Pfeil-Kauf statt Menü, Stapel-Tipp, Auftrag statt „Ziel“, Legende der Symbole als eine Blase, zwei Kamerafahrten | `--frisch --mit-tutorial` Durchlauf mit Zeitstempeln: erstes Upgrade < 10 s, Fenster bis Min 5 = 1 (Raum), Blasen gleichzeitig ≤ 1, Werbung 0 |
| **3b Werbeplätze** | `data/services/ads.json`, `services/ad_service_stub.gd`, `game/ui/offline_view.gd`, `game/ui/geschenk_view.gd`, `data/balance/*.json` (nur `schub`), `tests/unit/test_ad_limits.gd` | Offline ×2 statt ×3, Auftrag ×2, Agent ab W2, Dauerknopf-Text | `--tiefe 3 --offline 7200`: Knopf „▶ ×2 · +12.480 €“; vor Minute 5 nirgends ▶ (Test) |
| **3c Messung** | `services/messung_service.gd`, `tools/messung_bericht.py` | Ereignisse `fenster_auf`, `blase`, `kamera_auto`, `kauf_plakette`; Bericht zählt Fenster/Sitzung, Momente/min | Bericht aus Handy-Sitzung zeigt Fenster ≤ 2, Momente/min ≥ 2 (Min 1–10) |
| **3d Standortkarte + Grundrente** | `game/ui/standortkarte_view.gd` (neu), `game/ui/weltwechsel_view.gd`, `core/game_core.gd` (nur `grundrente()`), `data/balance/*.json` (nur `grundrente`), `assets/ui/standorte/` | sechs Standorte, alte laufen weiter | `--wechsel`: Karte vor dem Plakat; `welt_sim` Korridore unverändert (Grundrente ≤ 3 % Einkommen) |

### Welle 4 — Welten 2–6 nachziehen, Politur, Release-Bilder

Figuren/Kasse/Eingang je Welt in `worlds.json` + Blender (5 Agenten ‖, je Welt), Store-Screenshots neu (`art_source/icon/store_bilder.py`), Handy-Test über 3 Tage (Offline, Tag-2-Anfragen), Backlog-Pflege.

**Gesamtabnahme nach Welle 2 (Handy, Bastian):** „Zoomt die Kamera von allein?“ nein · „Kann ich die grüne Plakette drücken und es passiert sofort was?“ ja · „Wie viele Fenster in 5 Minuten?“ ≤ 2 · „Weiß ich, was ich aufbaue?“ Firma mit Leuten, Aufträgen, Kasse.

---

## 8. Offene Entscheidungen für Bastian (je mit Empfehlung)

1. **Interstitials und No-Ads-Kauf?** Markt zeigt beide Lager (§6). **Empfehlung: Nein in 1.0** — Rewarded-only wie Kolibri/Eatventure, messen, in 1.1 höchstens skippbare Interstitials mit 180-s-Cooldown **plus** No-Ads 3,99 €, wenn ≥ 5 Rewarded/Tag/Spieler erreicht sind (Azur-Schwelle).
2. **Ein Tipp auf die Plakette kauft sofort — oder zwei Tipps (Sheet)?** Fehlkauf-Risiko gegen Tempo. **Empfehlung: ein Tipp kauft** (nur x1, nur im grünen Zustand, Langdruck öffnet das Sheet). Das ist der belegte Eatventure-Weg und Bastians Wunsch.
3. **Geld auf der Kasse zum Antippen?** Bringt Handlung in die Welt, ist aber eine Pflichtgefühl-Mechanik, wenn der Stapel groß wird. **Empfehlung: ja, als kleiner Bonus (≤ 2 % des Einkommens), nie als Verlust** — Einkommen bucht der Kern weiter automatisch.
4. **Story-Umfang: 3 Szenen + 1 Entscheidung je Welt, Rest als Blasen/Posteingang?** Es gehen 2–3 Szenen und 3 Entscheidungen je Welt verloren, die gerade erst geschrieben wurden. **Empfehlung: ja** — die Figuren gewinnen als Mitarbeiter im Raum mehr, als die Fenster ihnen geben.
5. **Pinch ganz frei (kein Einrasten) oder sanftes Einrasten nur bei Stillstand > 1 s?** **Empfehlung: ganz frei**, Doppeltipp als einziger Sprung, Zoom im Spielstand. Wenn Bastian nach einer Woche „zu fummelig“ sagt, kommt das sanfte Einrasten als Daten-Schalter zurück (`karte.rasten: true`).

---

## 9. Quellen

Kürzel „-Mon“ = Rechercheblock Monetarisierung, „-Psy“ = Psychologie/Postmortems, „-UI“ = Kernschleife/UI; ohne Zusatz = Nummer im jeweils genannten Block oder K3/K4-Quelle.

| Kürzel | Quelle | URL |
|---|---|---|
| Q1 | Ryan/Rigby/Przybylski, PENS-Zusammenfassung (SDT) | https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/ |
| Q2 | Celia Hodent, Gamer's Brain UX Onboarding | https://celiahodent.com/gamers-brain-ux-onboarding/ |
| Q3 | Kivetz/Urminsky/Zheng, Goal Gradient (Chicago Booth) · Idle-Bank-Guide (LevelWinner) | https://www.chicagobooth.edu/review/going-goal · https://www.levelwinner.com/idle-bank-tycoon-money-empire-guide-tips-tricks-strategies/ |
| Q5 | Pecorella, „The rise of games you (mostly) don't play“ | https://www.gamedeveloper.com/design/the-rise-of-games-you-mostly-don-t-play |
| Q6 | Pecorella GDC 2015 Folien | https://www.slideshare.net/slideshow/idle-games-gdc2015final/45563367 |
| Q7 | Math of Idle Games III | https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii |
| Q8 | Idle Office Tycoon Guide (LevelWinner) | https://www.levelwinner.com/idle-office-tycoon-beginners-guide-tips-tricks-strategies/ |
| Q10 | Eatventure Beginner's Guide (LevelWinner) | https://www.levelwinner.com/eatventure-beginners-guide-tips-tricks-strategies/ |
| Q12 | Pizza Ready Guide (LevelWinner) · Google Play Payments Policy §7 | https://www.levelwinner.com/pizza-ready-guide-tips-tricks-strategies/ · https://support.google.com/googleplay/android-developer/answer/9858738 |
| Q13 | Idle Supermarket Tycoon Guide (Gamezebo) | https://www.gamezebo.com/walkthroughs/idle-supermarket-tycoon-guide-tips-cheats-and-strategies/ |
| Q14 | PocketGamer.biz Interview Lessmore | https://www.pocketgamer.biz/interview/80009/we-sit-down-with-lessmore-to-talking-pitching-indie-development-and-eatventure/ |
| Q15 | Jurasek, „900 seconds with My Perfect Hotel“ | https://martinjurasek.substack.com/p/900-seconds-with-my-perfect-hotel |
| Q17 | Supersonic, Optimizing FTUE [B-V] | https://supersonic.com/learn/blog/optimizing-ftue/ |
| Q19 | GameAnalytics, Eight lessons from Kolibri | https://www.gameanalytics.com/blog/making-a-hit-idle-game-eight-lessons-from-kolibri-games |
| Q20 | Hotel Empire Tycoon Tips (PocketGamer) · Kolibri MVP (PocketGamer.biz) | https://www.pocketgamer.com/hotel-empire-tycoon/hotel-empire-tycoon-tips-and-cheats/ · https://www.pocketgamer.biz/how-kolibri-went-from-minimal-viable-product-to-70-million-installs-for-its-idle-games/ |
| Q22 | Udonis FTUE [B-V] | https://www.blog.udonis.co/mobile-marketing/mobile-games/first-time-user-experience |
| Q23 | Idle Mafia Guide (LevelWinner) | https://www.levelwinner.com/idle-mafia-beginners-guide-tips-cheats-strategies-to-grow-your-syndicate-and-expand-your-territory-fast/ |
| Q24 | Lumber Inc Guide (LevelWinner) | https://www.levelwinner.com/lumber-inc-guide-tips-tricks-strategies-to-build-a-lumber-empire/ |
| Q25 | GameAnalytics Benchmarks 2025/2026 | https://www.gameanalytics.com/reports/2026-mobile-pc-gaming-benchmarks · https://gamedevreports.substack.com/p/gameanalytics-mobile-gaming-benchmarks |
| Q26 | NN/g, Modal & Nonmodal Dialogs | https://www.nngroup.com/articles/modal-nonmodal-dialog/ |
| Q32 | Retronauts, Two Point Hospital developers | https://retronauts.com/article/848/two-point-hospital-the-developers-speak |
| Q1-Mon | ArpuBrothers, My Perfect Hotel Deconstruction | https://arpubrothers.com/blog/my-perfect-hotel-arcade-idle-deconstruction/ |
| Q2-UI | ArpuBrothers, Burger Please Deconstruction | https://arpubrothers.com/blog/burger-please-deconstruction-of-the-game/ |
| Q4-Mon | Pangle, Kolibri Case [B-V] | https://www.pangleglobal.com/resource/5e95889b678921000f41e6f4 |
| Q6-Mon | PocketGamer.biz, Eatventure vs Cat Snack Bar | https://www.pocketgamer.biz/eatventure-vs-cat-snack-bar-an-analysis-of-both-games/ |
| Q10-Mon | PocketGamer.biz/AppQuantum, Idle Bank Deconstruction | https://www.pocketgamer.biz/game-analysis-deconstructing-idle-bank-tycoon-by-kolibri-games/ |
| Q12-Mon | Gamigion, Supercent 70/30 [A] | https://www.gamigion.com/supercents-meteoric-rise-on-the-hybrid-casual-gaming-scene/ |
| Q13-Mon | Tengyuan, Ads Removal Trends (Feb 2025) | https://tengyuan.substack.com/p/recent-trends-in-using-ads-removal |
| Q27-Mon | Playio, eCPM Benchmarks (Appodeal/Tenjin) [B-V] | https://blog.playio.co/mobile-game-ecpm-benchmarks-2026 |
| Q29-Mon | Azur Games, Ad-Monetization Setup [B-V] | https://azurgames.com/blog/the-nuances-of-our-ad-monetization-setup-when-to-replace-rewarded-ads-with-interstitials-and-when-its-better-not-to-show-ads-at-all/ |
| Q-Ret | AppQuantum Idle-Benchmark D1 50 / D7 20 / D30 5 | https://appquantum.com/news/december-2023/appquantum-deconstructs-idle-bank-tycoon-what-makes-this-game-one-of-the-most-successful-projects-by-kolibri-games.html |
| Q-Naavik | Naavik, What happened to idle games | https://naavik.co/digest/ygg-idle-games/ |
| Schultz | Dopamin = Vorhersagefehler, PNAS 2011 [A, nur Suche] | https://www.pnas.org/doi/10.1073/pnas.1014269108 |

**Retention-Anker für spätere Messung:** AppQuantum-Idle-Benchmark D1 50 % / D7 20 % / D30 5 % [B, Q-Ret]; GameAnalytics-Median aller Mobile-Games D1 ~22 %, Top-Quartil > 30 %, D7 < 4 % bzw. 6–7 % [B, Q25]; Supercent-Mindestschwelle D1 ≥ 35 % [B, Q2-UI]; Kolibri-Prototyp 63–81 % D1 ohne Meta [B, Q19]. Unter ~200 Spielern je Gruppe zählen nur Verhaltensmaße (K3 §3).
