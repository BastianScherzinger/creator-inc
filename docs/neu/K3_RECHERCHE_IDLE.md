# K3 · RECHERCHE — Was Top-Idle-/Tycoon-Spiele anders machen als HELLO WORLD

**Stand:** 2026-10-15 · Art: Recherche und Abgleich. Kein Code, keine Datenänderung, kein Commit.
**Auslöser:** Handy-Test Bastian: Karte „aus zu vielen kleinen Einzelbausteinen“, unübersichtlich, „zerbrechlich“; man sieht nicht, wo man klicken muss; Zimmer überladen; unklar, was man verbessern soll; Zoom fehlt; Story soll länger tragen; Geld über Rewarded Ads.
**Vorgänger:** `docs/neu/K2_NEUKONZEPT.md` (Story/Verständlichkeit, Rang, Tutorial, Karte). K3 ergänzt: **Lesbarkeit der Welt, Upgrade-Führung, Zoom, Belohnungsschleifen, Werbung.**

---

## 0. Lesehinweis: Wie belastbar ist das?

Ehrlich vorab. Die Web-Recherche (WebSearch/WebFetch) hat **wenig direkt Belastbares** zu den einzelnen Spielen geliefert. Es gibt keine frei zugänglichen Deconstructor-of-Fun-Analysen für diese Titel, die sich abrufen ließen; GDC-Vault-Seiten sind hinter Login. Was belegt ist, steht mit URL und Kennung unten. Alles andere ist gekennzeichnet:

- **[B]** = belegt durch eine abgerufene Quelle (URL im Quellenverzeichnis, Abschnitt 11).
- **[B-V]** = belegt, aber Anbieterquelle mit Eigeninteresse (Ad-Netzwerke, SDK-Firmen) — Richtung glaubhaft, Zahlen mit Vorsicht.
- **[W]** = Allgemeinwissen/Vorwissen des Recherchierenden, in dieser Sitzung **nicht** per Quelle bestätigt.
- **[V]** = Vermutung/Schlussfolgerung für HELLO WORLD.

**Lücken (nicht gefunden, nichts erfunden):** My Perfect Hotel (Kamera, Pfeile, Tutorial) — nur Store-Reviews gefunden; Idle Lumber Empire — keine Treffer; Idle Theme Park — nur Store-Texte; Cafeland/Hotel Empire Tycoon — nicht gezielt gefunden; eCPM speziell für Idle-Spiele — nicht gefunden (nur allgemein für Spiele); Session-Zahlen je Spiel außer Idle Miner. Wo diese Spiele unten vorkommen, ist es Vorwissen **[W]** und gehört vor einer Entscheidung am Handy gegengeprüft (jeweils 10 Minuten Spielen reichen).

---

## 1. Die zehn wichtigsten Erkenntnisse (Kurzfassung)

1. **Eine Schleife, ein Bildschirm.** Kolibri nennt als Kernregel: die ganze Kernschleife (Abbauen → Transportieren → Verkaufen → Upgraden) ist auf **einem** Bildschirm sichtbar, verbunden durch „Choke Points“ (Engpässe), die das Tempo bestimmen [B: Q3, Q4]. HELLO WORLD hat dieselbe Engpasskette (Idee → Aufnahme → Schnitt), zeigt sie aber verteilt über 23×17 m und viele Räume.
2. **Orientierung ist das bekannteste Zonen-Problem.** Die Idle-Bank-Tycoon-Analyse nennt „Zoning“ ausdrücklich als großes Problem: Spieler können Abteilungen nicht Bereichen zuordnen und finden nicht, wo sie tippen müssen — selbst bei nur zwei aktiven Zonen. Idle Office Tycoon löst es mit **Wänden um jede Zone** [B: Q5]. Das ist Bastians Befund fast wörtlich.
3. **Eatventure führt über Hinweis-Symbole, nicht über Text:** wackelnde Kiste = neue Station, gepunktete Quadrate = freie Stationsplätze, leuchtende drehende Münzen = Trinkgeld einsammeln, Kiste = neuer Mitarbeiter wartet, leuchtender Investor = tippen (nach Werbung), Pfeil unten rechts = Upgrade-Menü, großer Knopf unten = Werbe-Boost [B: Q6]. Jedes Ding hat **genau ein** Symbol an **genau einem** Ort.
4. **Upgrades stehen sortiert:** Im Eatventure-Pfeilmenü sind Upgrades „vom billigsten zum teuersten“ gelistet; jeder Tipp füllt einen Fortschrittsbalken, voller Balken = Stern = Gewinn der Station ×2 [B: Q6]. „Was soll ich verbessern?“ beantwortet das Spiel durch Reihenfolge, nicht durch Nachdenken.
5. **Die wichtigsten Werbeplätze sind immer dieselben drei:** (a) Boost (×2 Einkommen für Zeit, stapelbar), (b) „Willkommen zurück“ — Offline-Ertrag verdoppeln, (c) Sofort-Geldmenge/Truhe. Belegt für Idle Miner Tycoon, Idle Bank Tycoon, Eatventure [B: Q1, Q5, Q6, B-V].
6. **Werbung ist Haupteinnahme der Genre-Marktführer:** Kolibri gibt ca. 60 % der Einnahmen aus Werbung an, ~8 Werbungen pro Spieler und Tag, 52 % Ad-Engagement, Sitzung ≈ 10 Minuten [B: Q3, Q4] (Zahlenquelle intern widersprüchlich, siehe 7.1).
7. **Neues muss alle paar Minuten kommen, aber als „Ding“, nicht als Zahl.** Eatventure: nach Erreichen einer Verdienstschwelle öffnet eine wackelnde Kiste eine neue Station; die nächste Speise schaltet sich bei einem Verdienstniveau frei [B: Q6, Q7]. HELLO WORLD vergibt „Level“ als Zähler — K2 hat das schon erkannt (Rang statt Level).
8. **Visuelle Progression gegen „fühlt sich nach Prestige gleich an“.** Das GDC-2019-Fazit zu Idle Miner: neue visuelle Minen geben einen Grund weiterzumachen; das „visual progression problem“ ist das Kernrisiko [B: Q2]. HELLO WORLD hat sechs Welten mit eigener Optik — das ist ein echter Vorteil, wenn die Welt-Karte ihn sichtbar macht.
9. **Rewarded Ads funktionieren, wenn der Spieler den Gewinn vor dem Tippen sieht:** konkrete Beschriftung der Belohnung, auffindbarer Knopf, nie zu Sitzungsbeginn, Belohnung wertvoll, aber nicht so groß, dass sie Käufe entwertet [B-V: Q8, Q9, Q10].
10. **Die Werbe-Infrastruktur im Spiel ist schon halb da:** `AdServiceStub` mit Platzierungen „Schub“ und „Offline verdoppelt“, `ad_service_admob.gd` als Gerüst mit TODOs (kein echter SDK-Aufruf). Der Rest ist Platzierung, Texte und Einbau [aus Repo gelesen].

---

## 2. Methodik und Referenzspiele

| Spiel | Studio | Was die Quellen hergeben | Qualität |
|---|---|---|---|
| Idle Miner Tycoon | Kolibri | GDC-2019-Zusammenfassung, Lektionen, Stundenstatistik, Wiki/Guides | gut |
| Idle Bank Tycoon | Kolibri | ausführliche PocketGamer.biz-Analyse (Zonen, Monetarisierung, Retention) | **sehr gut** |
| Eatventure | Lessmore | PocketGamer.biz (Vergleich mit Cat Snack Bar), zwei Guides mit UI-Hinweisen | gut |
| AdVenture Capitalist | Hyper Hippo | Prestige-Mathematik (Gamasutra/Gamedeveloper), Fan-Foren | mittel |
| My Perfect Hotel | SayGames | nur Reviews: „Schleife = nächstes Upgrade/Mitarbeiter“, „Upgrades dauern später ewig“, „viele Anzeigen“ | dünn |
| Idle Supermarket Tycoon / Idle Theme Park | Codigames | Store-Texte; „No more Ads“ als Kauf (11,99 $ in Supermarket) | dünn |
| Idle Lumber Empire, Cafeland/Hotel Empire, Idle Office Tycoon | — | Lumber/Cafeland: nichts; Office nur indirekt über Bank-Analyse | Lücke |

Für die Lesbarkeitsfragen ist der Kern also: **Idle Miner, Idle Bank, Eatventure.** Die Empfehlungen in Abschnitt 9 stützen sich darauf, nicht auf die dünn belegten Spiele.

---

## 3. Karte und Weltdesign

### 3.1 Was belegt ist

| Beobachtung | Spiel | Quelle |
|---|---|---|
| Ganze Kernschleife auf einem Bildschirm; Engpässe verbinden die Stufen | Idle Miner | Q3, Q4 [B] |
| Isometrisches 2D-Raster „fast nötig für strategische, langlebige Bindung“ (Meinung des Autors) | Idle Miner (GDC 2019) | Q2 [B, Meinung] |
| Schacht-Mine als lange vertikale Struktur: neue Schächte nach unten, jeder Schacht gleich aufgebaut (Wiederholung statt Vielfalt) | Idle Miner | Q11 [B] |
| Aufzug und Lager bremsen die Mine, wenn nicht mitgezogen — Hinweis darauf, wo es sich staut, sieht man an gefüllten Loren/Aufzügen (Anzeige = Ursache) | Idle Miner | Q12 [B] |
| Zonen schwer zuordenbar: Spieler wissen nicht, welche Abteilung wo ist und wo man tippt | Idle Bank | Q5 [B] |
| Wände um jede Zone helfen bei der Orientierung | Idle Office | Q5 [B] |
| Hinweis-Symbole: wackelnde Kiste, gepunktete freie Plätze, leuchtende Münzen, Kiste, Investor, Pfeil unten rechts, Boost-Knopf unten | Eatventure | Q6 [B] |
| Neue Station öffnet sich über eine wackelnde Kiste, sobald ein Betrag verdient ist | Eatventure | Q6 [B] |
| Stationen sind **Slots**: 3. Platz (Burger) öffnet bei Stufe 5 in der ersten Stadt | Eatventure | Q7 [B] |
| Tippen auf eine Station zeigt in der Upgrade-Taste den Gewinn oben links, damit man Produkte vergleicht | Eatventure | Q6 [B] |
| Minimalistische Shop- und Upgrade-Gestaltung, um Kaufentscheidungen einfach zu halten | Eatventure | Q7 [B] |
| Kamera/Zoom je Spiel | alle | **nicht belegt** — nur Vorwissen unten |

### 3.2 Vorwissen, nicht aus Quellen bestätigt [W]

- Eatventure und My Perfect Hotel zeigen **einen** Raum oder ein Stockwerk pro Bildschirm; Erweiterung = Kamera schwenkt nach unten/seitlich bzw. neues „Restaurant“ ist ein eigener Bildschirm. Kein stufenloser Zoom über die ganze Welt.
- Idle Miner hat vertikales Scrollen entlang der Schächte; Zoom ist ein „Rauszoomen“ auf Gesamtübersicht (Mine als Streifen), kein freies Kamera-Fliegen.
- Die Welt ist in diesen Spielen **flach gebaut**: wenige, große, tippbare Objekte; Figuren laufen, aber Dekor ist wenig.

Das Muster dahinter ist belegt genug, um zu handeln: **die Welt ist eine Bedienoberfläche, kein Diorama.**

### 3.3 Abgleich mit Bastians Befund

| Befund Handy | Wahrscheinliche Ursache | Was die Referenzen tun |
|---|---|---|
| „viele kleine Einzelbausteine, zerbrechlich“ | 23×17 m Grundriss, 8 Zonen, 5 Stationen mit je 3 Ausstattungsplätzen (K2 §1.6), Welt als 3D-Raum aus Modulen | Ein Bildschirm = eine Entscheidung. Eatventure: Slots, nicht Modelle. Bank: Zonenwände. |
| „man sieht nicht, wo man klicken muss“ | Tippflächen = Objektgröße (Strahl gegen Objekthöhe, Paket A), keine einheitliche „Hier tippen“-Sprache | Jede tippbare Sache trägt ein Schild/Symbol; ein Symbol = eine Funktion (Q6). |
| „Zimmer überladen“ | 3 Ausstattungsplätze × 5 Stationen + Deko + Figuren + Marker + Schilde | Wenige große Silhouetten; Details erst im Zoom/Menü. |
| „man weiß nicht, was man verbessern soll“ | Fünf Stationen mit eigenen Menüs, Engpass-Hinweis nur als Text im Menü | Sortierte Upgrade-Liste (billigstes zuerst), ein „Nächstes Upgrade“-Pfeil, Engpass **in der Welt** an der Station sichtbar. |
| „Zoomen fehlt“ | Startzoom je Welt (`worlds.json`), `--zoom N` nur Prüfschalter | Kein freier Zoom belegt; aber „Raus = Übersicht, Rein = Raum“ als Zweistufigkeit ist plausibel [V]. |

### 3.4 Empfehlungen Karte (Details in Abschnitt 9)

1. **Zwei feste Zoom-Stufen statt freiem Zoom:** *Überblick* (alle Räume als Silhouetten + Schilder, nichts anderes) und *Raum* (ein Raum füllt den Bildschirm, 1 Station im Fokus). Doppeltipp/Pinch springt dazwischen. Freier Zoom bringt auf dem Handy mehr Verlorensein als Nutzen [V].
2. **Zone = sichtbarer Kasten:** Wand-/Bodenfarbe je Raum klar verschieden, Raumname als Schild (Idle-Office-Lösung, Q5).
3. **Pro Raum: 1 große Hauptstation + max. 3 Nebenobjekte** [V, Richtwert]. Ausstattung (die 3 Plätze) erst im Raumzoom sichtbar, im Überblick weggeblendet (LOD).
4. **Alles Tippbare bekommt dieselbe Plakette** (Stufe + Preis-Pfeil oder Warnung, wie K2 §6.1 Nr. 2) und wird erst ab einer Mindestgröße gezeichnet: Tippfläche ≥ 48 dp (Material) bzw. 44 pt (Apple HIG) [B-V: Q13]. Bei 540×1200 Referenz ≈ 8–9 % der Breite.
5. **Engpass in die Welt:** An der bremsenden Station pulsiert ein Symbol; in Idle Miner zeigt der Stau (volle Loren) die Ursache [B: Q12].

---

## 4. UI-Muster

### 4.1 Upgrade-Panels und Fortschrittsbalken

| Muster | Beleg | Übertrag |
|---|---|---|
| Tippen kauft sofort, Balken füllt sich, voller Balken = Stern/×2 | Eatventure Q6 [B] | HELLO WORLD hat „Stern alle 10 Stufen ×1,5“ — gleiche Idee. Balken **an der Plakette** zeigen, nicht nur im Menü. |
| Liste „billigstes zuerst“ | Eatventure Q6 [B] | Upgrade-Liste im Menü sortieren; erstes = Hervorhebung „Beste Wahl“ [V]. |
| Gewinn je Station vergleichbar (Zahl in der Kaufen-Taste) | Eatventure Q6 [B] | Kaufen-Taste zeigt **„+0,4 €/s“**, nicht nur den Preis. |
| Meilensteine in drei Ebenen: Quests, Balken auf dem Bildschirm, Balken im Menü | Idle Bank Q5 [B] | HELLO WORLD hat Ziele (HUD-Chip + Menü). Gut, wenn der Chip nur **ein** Ziel zeigt. |
| Meilenstein-Multiplikatoren (z. B. bei 300/400/500 Einheiten ×) erzeugen Kaufschübe | Math of Idle Games Q14 [B] | Passt zu „Stern alle 10 Stufen“; Abstand 10 ist kurz genug. |
| Ungleichmäßiges Tempo (Phasen langsam/schnell) als gewolltes Gestaltungsmittel | Q14 [B] | Welt 1 einheitlich 77–81 min; Spitzen/Flauten gezielt einbauen [V]. |

### 4.2 Zahlenformat und Farbsprache

- Zahlenformat: Idle Miner nutzt Kurzformen und nach Billion „aa, ab…“ [B: Q12]. Für HELLO WORLD (Welt 1 bis 2 Mio €) reicht „1,2 Mio €“; **Buchstabenstufen erst nötig, wenn Zahlen > 10¹² erreicht werden** — laut `balance` offenbar nicht [V].
- Farbsprache grün = leistbar: in den Quellen **nicht ausdrücklich belegt** [W]. K2 plant bereits „Limette pulsiert = kaufbar“; das ist konsistent. Ergänzung [V]: **drei Zustände, drei Formen, nicht nur Farbe** (Barrierefreiheit): kaufbar = Limette + Puls, fast kaufbar = Papier + Mini-Balken, unleistbar = Papier ohne Puls.
- Seltenheit über Farbstufen weiß/grün/violett/orange bei Eatventure-Ausrüstung [B: Q6] — Genre-Konvention, auch für Crew-Karten nutzbar.

### 4.3 Onboarding / FTUE (erste 5 Minuten)

**Belegt (allgemein, nicht idle-spezifisch):**
- FTUE soll mit dem packendsten Mechanismus beginnen, Funktionen **schrittweise** freischalten, Brotkrumen statt Überladung [B-V: Q15].
- Trichtermessung je Schritt; ein D1 von ca. 45 % wird als gutes Zeichen für ein FTUE genannt (Einzelstimme) [B-V: Q15].
- Kolibri-Prototyp: D1 63–81 % *ohne* IAP, Social, Lokalisierung, Mediation, Langzeitmotivation — also ein reduzierter Kern bindet bereits stark [B: Q3].

**Eatventure-Ablauf (belegt):** eine Zitronenade-Bude, **ein** Mitarbeiter, **ein** Produkt; erste Gewinne ins erste Produkt, das schaltet Edelsteine, neue Arbeitsplätze und neue Produkte frei; Mitarbeiter-Kiste ist ein sichtbares „Neuer Mitarbeiter wartet“; Investoren ab Phase 3 [B: Q6, Q16]. Alles, was kommt, kommt **als Ding mit Symbol**.

**Idle Bank (belegt):** Manager ab Ruf-Stufe 6, Business-Modus ab 7, Events ab Tag 2 — Freischaltung nach Rängen, nicht alles auf einmal [B: Q5].

**Folgerung für HELLO WORLD** [V, anschließend an K2 §3/§P3]:
- Minute 0–1: ein Ziel nennen (K2 macht das), **ein** tippbares Objekt, **ein** Hinweis-Pfeil.
- Minute 1–3: Menüknöpfe stufenweise freischalten (heute alle fünf sofort — K2 §1.5).
- Minute 3–5: erste „neues Ding“-Überraschung (Raum 2), mit Kamerafahrt (K2 §6.1 Nr. 4), danach erstes Zusammenspiel mit Werbung **nicht vor** Minute 5 (Q9, Q10).

---

## 5. Psychologie und Dopamin

Wichtig: Für die Psychologie lieferte die Recherche **Grundlagenliteratur**, nicht Idle-Analysen. Übertrag ist Schlussfolgerung.

### 5.1 Goal-Gradient und Near-Miss

- Je näher am Ziel, desto höher Motivation und positive Stimmung; ein erneutes Verfehlen steigert Frust (Scientific Reports 2024, Wordle-Studie) [B: Q17].
- Beinahe-Treffer sind erregender als andere Ausgänge; in zielgerichteten Kontexten (nicht im Glücksspiel) ist das ein legitimer Hebel [B: Q17].
- **Übertrag [V]:** Der Mini-Balken „1.240 / 2.000“ am gesperrten Raum (K2 §6.1) ist genau diese Mechanik. Ergänzen: bei ≥ 80 % Balken leichtes Pulsen, bei 100 % Aufleuchten + Ton.
- **Grenze:** Near-Miss ist ethisch heikel, wenn er künstlich ist (Zufall). Bei HELLO WORLD ist er echt (Geld ist bald da) — das ist die saubere Variante. Keine „Fast gewonnen“-Zufallsboxen.

### 5.2 Endowed Progress, Sunk Cost, Prestige

- Endowed Progress („schon etwas erreicht“): Definition belegt, Anwendung nicht [B: Q17]. **Übertrag [V]:** Das Welt-Ziel (Gaming-PC) mit vorgefülltem Umriss zeigen („Silhouette füllt sich 25/50/75 %“ in K2 §6.1 Nr. 3) und der erste Rang kommt nach < 60 s.
- Prestige: AdVenture Capitalist nutzt Engelsinvestoren = Reset gegen permanenten Prozentbonus; Ertrag ~ Wurzel der Lebenseinnahmen, Verdopplung braucht ~3–4× Einnahmen [B: Q14, Q18]. Idle Miner: Prestige **optional**, Spieler erweitern auf viele Minen und behalten die alte [B: Q2].
- Idle Bank: Prestige erst nach **allen** Meilensteinen, Reset + Belohnungen + neue Bank, weiches Geld bleibt [B: Q5].
- **HELLO WORLD:** Weltwechsel ist bereits eine Art sanftes Prestige ohne Reset (sechs Welten). Das ist laut Genre-Logik gut: kein Zwang zum Zurücksetzen [V]. Kein Reset-Prestige für 1.0 einbauen.

### 5.3 Variable Belohnungen

- Idle Miner: pro Stunde über die Spielerschaft 316 Boosts (2× bis 2.000× plus Mystery-Boosts), 100 Truhen (Hauptquelle für Arbeiterkarten), 19 Super-Manager pro Stunde mit Edelsteinen, 14 Rerolls [B: Q19]. Das ist Streuung: **kleine häufige Gewinne, selten große.**
- Eatventure: Investoren tauchen auf, leuchten, verschwinden wieder, wenn ignoriert [B: Q16] — zeitlich variable Gelegenheit.
- **Übertrag [V]:** „Mystery-Boost“ (Wert vorher unbekannt) als Werbebelohnung; **Kleinstes Los** gibt immer etwas, nie Niete.

### 5.4 Juice

Belegt nur allgemeines Material [B-V: Q20]:
- Schütteln 50–300 ms, abklingend; große Effekte nur für große Momente; drei Stufen (klein/mittel/groß); wenige Kanäle pro Ereignis; Überfrachtung schadet ("Juice Overload").
- Zu Haptik und Idle-Spezifika **nichts Belegtes.**

**Übertrag [V]:** HELLO WORLD hat bereits Konfetti, Blitz, Haptik (Paket B). Risiko ist eher **Dauer-Juice**: bei jedem Tick Münzen = Rauschen; das verstärkt den Eindruck „überladen“. Regel: Routine-Einnahmen nur als kleine Zahl über der Station, Münzregen **nur** für Raumkauf, Stern, Rang.

### 5.5 Sitzungslänge und Rückkehr

- Idle Miner: Sitzung ≈ 10 Minuten, ca. 8 Werbungen pro Spieler und Tag, Ad-Engagement 52 % [B: Q3, Q4].
- Eatventure: Offline-Ertrag bis 3 h gedeckelt, Rückkehr-Bonus per Werbung verdoppelbar [B: Q6].
- Eatventure „Helfer“-Einladung ab Tag 4–5: alle 30 Min kann man einen Helfer für 5 Min einladen; Helfer wirken wie Spieler, sind aber keine echten [B: Q7].
- HELLO WORLD: Offline Rate 0,5, Obergrenze 4 h (ausgebaut 12 h) [aus `balance/zimmer.json`]. K2 plant höhere Deckel in späteren Welten.
- **Folgerung [V]:** Eine 10-Minuten-Sitzung ist die Planungsgröße. Heute braucht Welt 1 ~80 min aktiv = 8 Sitzungen. Pro Sitzung sollte **mindestens ein „neues Ding“** passieren (siehe 6).

### 5.6 Sammeln

- Idle Miner: Super-Manager mit Edelsteinen anheuern, Rerolls; Arbeiterkarten aus Truhen [B: Q19]. Idle Bank: Managerkarten, Seltenheit, „Evolve“-Währung [B: Q5]. Eatventure: Kleidung (Hut/Körper/Hand), jede Teile einer Kategorie tauschbar, damit man nicht gezielt jagen muss [B: Q7].
- **HELLO WORLD** hat Crew-Karten. Kleine Lehre aus Eatventure: **nicht-zielgerichtet tauschbar** ist weniger frustrierend [V].

---

## 6. Progressionstempo

### 6.1 Was belegt ist

| Größe | Wert | Quelle |
|---|---|---|
| Idle Miner: D1 des Prototyps | 63–81 % | Q3 [B] |
| Idle Bank: D1 / D3 / D7 / D14 / D30 | 48 % / 35 % / 20 % / 15 % / 5 % (letzte vier als Benchmark gelistet) | Q5 [B] |
| Idle Bank: Abfall nach Tag 3 = zu langsame Anfangsprogression; Tage 7–30 = zu wenig Inhalt | Autorenschluss | Q5 [B, Meinung] |
| Idle Miner: wöchentliche Updates, > 160 Updates, gestuftes Ausrollen 1/5/20/100 % | Q3 [B] |
| Eatventure: Station auf max. Stufe 150 | Q6 [B] |
| Eatventure: etwa ein Jahr von Start bis große regelmäßige Käufe | Q7 [B] |
| Offline: Eatventure 3 h | Q6 [B] |

**Nicht belegt:** konkrete Dauer von „Gebiet 1, 2, 3“ in Stunden je Spiel. Die Recherche liefert **keine** vergleichbaren Zahlen. Aussage in K2 („Top-Idle-Referenz: erste Welt am ersten Tag fertig, dann 2–5 Tage je Welt“) bleibt damit **unbelegt [W]** — als Planungsannahme tauglich, nicht als Fakt zitierbar.

### 6.2 Rhythmus „neues Ding“

Aus Eatventure/Idle Bank ableitbar [V]: alle **2–4 Minuten** ein sichtbares Neues (Station, Slot, Mitarbeiter, Raum), alle **10–15 Minuten** ein großes (Stadt/Restaurant/Bank, Event), alle **Tage** ein Meta-Ding (Event, Welt). HELLO WORLD heute (K2 §1.4): Level-Up alle 2–3 Min **ohne Inhalt** — Rhythmus stimmt, Inhalt fehlt. K2-Rang-System löst das.

### 6.3 Story länger tragen

Bastian: „nicht zu lange an einem Level hängen, nicht zu kurz.“ Aus den Daten:
- Idle Bank verliert nach Tag 3 (zu langsam am Anfang) und ab Tag 7 (zu wenig Inhalt) — beide Fehler sind für „zu kurz / zu lang“ zugleich Warnung [B: Q5].
- Tempo-Hebel in den Daten, **nicht** im Code (HELLO WORLD-Regel): `ziel_belohnung_faktor` je Welt, Offline-Deckel, Raumkosten (K2 §4.3).
- **Zwischenziele in der Welt:** je Welt 3 Sub-Ziele à 15–25 min (Raum 2–3, Raum 4–5, Abschluss), jedes mit Neuem [V]. Bastians „zu lange an einem Level“ ist am wahrscheinlichsten das **Warten auf Raum 4/5** (200 € → 2 Mio €, Faktor 10.000) [aus Repo; Zusammenhang V].
- Wöchentliche Updates + gestaffelter Rollout als Muster für Live-Betrieb [B: Q3] — mit Experiment-Mechanik `data/experimente.json` bereits angelegt.

---

## 7. Monetarisierung mit Rewarded Ads

### 7.1 Was die Marktführer tun

| Platzierung | Spiel | Beleg |
|---|---|---|
| **Boost** (Knopf unten im Spiel: Einkommen ×2 für Zeit; mehrfach drückbar = verlängert) | Idle Miner | Q1 [B-V, Pangle-Fallstudie] |
| **Willkommen zurück** (Offline-Geld verdoppeln) | Idle Miner, Idle Bank, Eatventure | Q1, Q5, Q6 |
| **Boost 5 Min, stapelbar bis 1 h**, großer Knopf unten | Eatventure | Q6 |
| **Investor** (leuchtet, tippen → Werbung → große Geldsumme; verschwindet, wenn ignoriert) | Eatventure | Q6, Q16 |
| **Manager verkaufen** → 100 % Rückerstattung statt 50 % per Werbung | Idle Miner | Q12 |
| **Sofort-Geld**, skaliert auf Einkommen pro Sekunde | Idle Bank | Q5 |
| **2× Einkommen für 2 Stunden pro Werbung** | Idle Bank | Q5 |
| **Glühbirnen verdoppeln** (3× mit Hartwährung) | Idle Bank | Q5 |
| **Grüne Truhe bis 5× per Werbung öffnen**, alle 2 h neue | Idle Bank | Q5 |
| Weitere Hartwährung in kleinen Mengen | Idle Bank | Q5 |

**Muster:** *Immer* gibt es dieselbe Struktur: **Doppelt (Zeit), Doppelt (Offline), Geschenk (Truhe/Investor)**. Wer „Doppelt für Hartwährung“ danebenstellt (Idle Bank: ×2 per Werbung, ×3 per Edelsteinen), verbindet Werbung und Käufe sauber [B: Q5].

**Lücken in Eatventure laut PocketGamer.biz:** kein Rewarded-Speed-up, kein Starter Pack, kein No-Ads-Angebot — überraschend wenig Werbung, trotzdem hohe Einnahmen (US 54,3 % des Umsatzes; RPD US doppelt so hoch wie Cat Snack Bar) [B: Q7].

**Frequenz:** AdMob/Pangle/Mobvista: kein einheitlicher Wert. Drei Einzelwerte:
- 5–8 Werbungen je 20–50 Minuten Spielzeit bei Casual (Pangle) [B-V: Q10].
- 2–3 pro Tag (Mobvista) [B-V: Q21].
- Idle Miner real: ~8 pro Spieler und Tag [B: Q3, Q4].
→ Das heißt: **~5–10 freiwillige Werbungen pro Tag und aktivem Spieler** ist das, was der Markt zeigt. Was „fair“ ist, hängt an der Freiwilligkeit, nicht an der Zahl.

**Interstitials:** Die Quellen sind für Idle-Spiele uneindeutig. My Perfect Hotel wird in Reviews für „viele Anzeigen“ und eine Werbefrei-Kauf-Beschwerde genannt [B: Q22], Idle Supermarket verkauft „No more Ads“ für 11,99 $ [B: Q23] — beides Hinweise auf Zwangswerbung bei Teilen des Genres. Eatventure und Idle Miner arbeiten vorwiegend mit Rewarded [B: Q6, Q1]. **Empfehlung [V]: keine Interstitials in 1.0.** Der Auftrag lautet „freiwillig schauen“; Zwangswerbung widerspricht dem und gibt schlechte Bewertungen.

### 7.2 Best Practices (Google/Pangle/Unity)

1. **Reward im Knopf nennen** („Video ansehen: 2 Stunden ×2“), nicht „Video ansehen“ [B-V: Q10].
2. **Auffindbar und konsistent platziert**, kontrastreich, mit subtiler Bewegung [B-V: Q10].
3. **Nie in den ersten Sekunden/vor dem Tutorial**; an natürlichen Pausen [B-V: Q9].
4. **Opt-in-Pop-ups erhöhen Entdeckung**; Platz dort, wo alle Spieler irgendwann landen (z. B. Hauptbildschirm, Sitzungsende) [B: Q24].
5. **Belohnung wertvoll, aber nicht kaufzerstörend** (Game Insight: 5 Rubine je Werbung, große Mengen bleiben IAP) [B: Q24].
6. **Variable Belohnungshöhe motiviert** (Habby: Edelsteine unterschiedlicher Werte) [B: Q24].
7. **Benchmarks:** > 50 % der täglichen Spieler schauen mind. eine Rewarded; ≥ 80 % Abschlussquote; Sichtbarkeit und Abschluss messen [B: Q24].
8. **Opt-in-Quote:** Entwickler berichten 20–40 % höhere Opt-in-Raten gegenüber anderen Formaten [B: Q24].
9. **Fallstudien Google:** CookApps + 86 % Werbeumsatz, TutoTOONS + 20 %, Four Thirty-Three + 15 % (nach angepasster Platzierung/Prompt) [B-V: Q24; sind Google-eigene Marketingfälle, Einzelfälle].
10. **A/B testen** (z. B. Firebase) [B: Q24].
11. **Verlustmoment-Angebot:** direkt nach verlorenem Boxkampf, 10 s Entscheidungszeit [B: Q24]. Bei HELLO WORLD gibt es keine Niederlage — das Gegenstück ist der **Moment, in dem Geld bald reicht** („Noch 40 € — mit Werbung sofort“) [V].

### 7.3 Was Spieler fair finden

Die Quellen sind **alle von Werbefirmen**; es gibt keine neutrale Studie. Richtungswerte:
- Unity-Report: 46 % bevorzugen Rewarded (vs. 29 % Vollbild-Pop-up, 20 % Banner, 5 % Standard-Interstitial); „immer“ 18 %, „manchmal“ 44 %, „selten“ 16 %, „nie“ 22 %; 39 % der Entwickler sahen längere/häufigere Rückkehr nach Rewarded, nur 9 % weniger Bindung [B-V: Q25].
- Tapjoy (US-Umfrage, 2017/2019): 76–79 % ziehen Opt-in-Rewarded gegenüber Zwangswerbung vor [B-V: Q26].
- Gameloft 2025: 64 % finden Rewarded akzeptabel, 75 % neutral bis positiv [B-V: Q27].
- Playio: Spieler, die Rewarded nutzen, haben bis zu 3,5× höhere Bindung — Korrelation, kein Beweis der Ursache [B-V: Q28].

**Fairness-Regel [V, aus dem Gesamtbild]:** (1) Ablehnen kostet nichts und das Spiel geht normal weiter [B-V: Q29]. (2) Belohnung entspricht dem, was draufsteht. (3) Fortschritt ist **auch ohne Werbung** möglich (Tempo, nicht Zugang). (4) Kein Dauerbombardement: max. ein Angebot gleichzeitig sichtbar, Cooldown. (5) Nie ein Angebot während Tippen/Spielen aufpoppen, das den Fluss unterbricht.

### 7.4 Einnahmenrahmen (eCPM)

Belegte Werte für **Spiele allgemein**, Rewarded Video (Q4 2024, Appodeal; Werte aus Diagrammen abgelesen): Nordamerika iOS ≈ 13,6 $, Android ≈ 9,0 $; Europa iOS ≈ 8,9 $, Android ≈ 5,1 $; Lateinamerika iOS ≈ 3,4 $, Android ≈ 1,8 $ [B-V: Q30]. Eine andere Quelle (Tenjin × CAS, Q2 2024, nur Spiele) nennt US iOS 24,39 $ und US Android 30,25 $; Quellen weichen um bis zu Faktor 2 ab, Q4 ist 20–40 % teurer als Q1 [B-V: Q30]. Deutschland ist **nicht** einzeln belegt.

**Rechenbeispiel [V], ausdrücklich keine Prognose:** Annahme DACH-Android-Rewarded eCPM 4–8 $ (Zwischenwert Europa Android 5,1 $), 6 Werbungen/Tag/aktivem Spieler → 6 × 5 $ / 1000 = **0,03 $ je Spieler und Tag**. Bei 1.000 täglichen Spielern ≈ 30 $/Tag. Heißt: Werbung trägt erst mit **Reichweite** (Tausende DAU); Platzierungsqualität ändert den Faktor 2, nicht den Faktor 100. Einzige belegte Aussage zu Eatventure: US-Spieler sind der Hebel (54 % des Umsatzes) [B: Q7].

### 7.5 Stand HELLO WORLD (aus dem Repo)

- `services/ad_service.gd` (Interface), `ad_service_stub.gd` (aktiv in `main.gd:82`), `ad_service_admob.gd` (Gerüst, TODOs für `MobileAds.initialize`, UMP-Einwilligung, `RewardedAd.show`).
- Belohnungs-Texte `belohnung.schub_*` / `offline_verdoppelt_*` / `nichts_da_*` in den Themen-Dateien; `main.gd:834` `_auf_belohnung(platzierung)` kennt **Schub** und **Offline verdoppelt**.
- `core/economy/cost_curve.gd:6` Kommentar: „Rewarded Ad später als Erleichterung wirkt statt als Erpressung“ — die Haltung ist bereits im Kern.
- **Fehlt:** Einwilligung (UMP/DSGVO — für Deutschland Pflicht [W]), Frequenzlimits, Cooldown, Messung (Analytics gibt es laut CLAUDE.md nicht), Truhe/Investor-Platzierung, Sichtbarkeit des Knopfs im HUD.

---

## 8. Story und Meta: Gefühl „ich baue ein Business auf“

### 8.1 Was belegt ist

- Idle Miner: „World Map mit freischaltbaren Gebieten“ kam per Update; Kontinente mit eigenem Geld (Normal, Eis, Feuer, Dämmerung, Dusk, Uralt) [B: Q3, Q12].
- Eatventure: Lemonade-Stand → Snackbar → Café → Fast-Food-Kette; jeder Schritt ist **Renovierung**, die das Bild ändert [B: Q6]. Kleidungskisten erscheinen beim Phasenwechsel [B: Q6].
- Idle Bank: Kunden werden über Marketing angezogen; jede Abteilung hat sichtbare Wirkung; neue Bank (#6) per Update [B: Q5]. Empfohlene Meta: Immobilien, handelbare Firmenanteile, Manager-Resort [B, Autorenmeinung: Q5].
- Kolibri empfiehlt Events nahe an die Kern-Ökonomie zu legen; Event-Minen steigerten den Umsatz sichtbar [B: Q2].

### 8.2 Übertrag

| Idle-Muster | HELLO WORLD heute | Lücke / Idee |
|---|---|---|
| Sichtbares Wachstum der Welt (Renovierung) | Bodenmodule/Ausstattung mit Modellwechsel bei Stufe 1/5/10 | Gut. Im **Überblickszoom** muss der Unterschied sichtbar sein (große Stufen, nicht Details). |
| Kundenstrom (Eatventure: Kunden laufen) | Figuren-Routen | Sichtbare „Aufrufe“ als Besucher-Figuren/Zähler-Blasen [V] |
| Karte / Kontinente | Sechs Welten, kein Übersichtsbild | K2 §6.3 Standortkarte — passt exakt zu Q3/Q12. |
| Meta nach Hauptspiel | Crew, Tagesgeschenk, Marken | Q5: Meta ist bei Bank „dünn“ und kostet Bindung ab Tag 7 — also **eine** zweite Ebene planen (z. B. Crew-Ausflüge als Expedition, [V]). |
| Events | Keine | Q2/Q5: Events sind Retentions-Treiber; für 1.0 zu groß, für 1.1 vormerken. |

---

## 9. Abgleich HELLO WORLD und priorisierte Maßnahmen

### 9.1 Was die Referenzspiele anders machen als wir

1. **Weniger Objekte, größer, mit einheitlichem Hinweis-Vokabular** (Q5, Q6). Wir: viele kleine Bausteine, Hinweise uneinheitlich.
2. **Neues kommt als Ding mit Symbol** (wackelnde Kiste, gepunktete Slots; Q6). Wir: Zähler („Level“) und Prozent.
3. **Upgrade-Reihenfolge wird vom Spiel gelöst** (billigstes zuerst, Gewinn in der Taste; Q6). Wir: fünf Menüs, Engpass-Text.
4. **Werbung ist ein Teil der Welt** (Investor läuft herein, Boost-Knopf dauerhaft; Q6). Wir: Stub-Platzierungen, nicht im HUD sichtbar.
5. **Zonen sind abgegrenzt** (Wände, Q5). Wir: 8 Zonen ohne klare Grenzsprache.
6. **Ein Bildschirm = eine Entscheidung** (Q3/Q4). Wir: Raum 23×17 m.
7. **Wöchentliche Updates/Staged Rollout** (Q3). Wir: Experimentdatei da, Betrieb fehlt.

### 9.2 Maßnahmenliste (Wirkung / Aufwand, geordnet nach Priorität)

Skala: Wirkung H/M/N (hoch/mittel/niedrig) · Aufwand S (< 3 h) / M (3–8 h) / L (> 8 h). **Quelle** zeigt Beleg ([B]) oder Vermutung ([V]). Alle Werte weiterhin in Daten (D3/ADR-010, keine Zahlen im Code).

**A · Lesbarkeit und Führung (löst Bastians Kernbefund)**

| # | Maßnahme | Wirk. | Aufw. | Beleg |
|---|---|---|---|---|
| 1 | **Ein einheitliches Hinweis-Vokabular** (5 Symbole): Pfeil = Upgrade möglich, wackelnde Kiste = Neues freischaltbar, gepunktete Umriss = leerer Platz, leuchtende Münzen = einsammeln, Engpass-Blitz = bremst. Je Ding genau ein Symbol an fester Stelle | H | M | Q6 [B] |
| 2 | **Hauptfrage lösen: „Nächstes Upgrade“-Pfeil** — ein einziger pulsierender Pfeil in der Welt an die Station mit bestem Gewinn je Euro (Berechnung im Kern `core/`, nur anzeigen) | H | M | Q6 (sortiert), [V] |
| 3 | **Kaufen-Taste zeigt Gewinn** („+0,4 €/s“) neben dem Preis | H | S | Q6 [B] |
| 4 | **Upgrade-Liste im Menü billigstes zuerst**, erste Zeile hervorgehoben | M | S | Q6 [B] |
| 5 | **Zwei feste Zoom-Stufen** (Überblick / Raum), Doppeltipp und Pinch springen; Plakettengröße zoomabhängig | H | M | [V], Q5 |
| 6 | **Im Überblick nur Silhouetten + Schilder**, Ausstattung und Deko ausgeblendet (LOD) | H | M | Q5, Q3 |
| 7 | **Raumgrenzen sichtbar**: eigene Bodenfarbe + Wandkante + Raumschild je Zone | M | M | Q5 [B] |
| 8 | **Mindest-Tippfläche 48 dp** für alle tippbaren Dinge, Hitbox getrennt vom Modell | M | S | Q13 [B-V] |
| 9 | **Dekor abbauen:** max. 1 Hauptstation + 3 Nebenobjekte je Raum im Raumzoom; Rest nur als Ausstattungsstufe an der Station | M | M | [V] |
| 10 | **Gesperrte Räume als Versprechen**: Umriss der neuen Station + Schild „Neu: Upload · 200 €“ (K2 §6.1) | H | M | Q6 [B] |
| 11 | **Engpass in der Welt** an der bremsenden Station (Symbol), nicht nur im Menü | H | S | Q12 [B] |
| 12 | **Menüs gestaffelt freischalten** (K2 P3): erst nur Tippen+Upgrade, Ziele ab Minute 3, Handy ab Raum 2 usw. | H | M | Q15 [B-V] |

**B · Tempo, Belohnung, Neues**

| # | Maßnahme | Wirk. | Aufw. | Beleg |
|---|---|---|---|---|
| 13 | **Rang statt Level** mit Inhalt je Rang (K2 P2) | H | M | Q5 (Rang-Freischaltungen) |
| 14 | **„Neues Ding“-Takt**: alle 2–4 min ein sichtbares Neues, alle 10–15 min ein großes (Datenliste je Welt prüfen) | H | M | [V], Q6 |
| 15 | **Zwischenziel-Kette in Welt 1**: Raum 2 < 4 min (steht), Raum 3 bei ~20 min, Raum 4 bei ~40 min, Raum 5 bei ~65 min; Preissprünge 200 € → 2 Mio € glätten | H | M | Q5 (Abbruch Tag 3) [V] |
| 16 | **Juice-Tiering**: klein (Zahl), mittel (Funken), groß (Münzregen + Haptik) — Routine nie groß | M | S | Q20 [B-V] |
| 17 | **Mini-Balken + Puls ab 80 %** an gesperrten Räumen/Stationen (Goal-Gradient) | M | S | Q17 [B] |
| 18 | **Standortkarte** der sechs Welten (K2 §6.3) | M | M | Q3, Q12 |
| 19 | **Besucher/Aufrufe sichtbar machen** (Figuren, Zähler-Blasen) für „Business wächst“ | M | M | Q6 [V] |
| 20 | **Zufälliges Gelegenheits-Ereignis** („Investor“-Äquivalent: Agent/Produzent läuft herein, nur mit Werbung/ohne Werbung kleine Summe) | M | M | Q6, Q16 [B] |

**C · Werbung (Rewarded)**

| # | Maßnahme | Wirk. | Aufw. | Beleg |
|---|---|---|---|---|
| 21 | **Dauer-Boost-Knopf** im HUD unten („Algorithmus“ ×2 für 5 Min, stapelbar bis 1 h), Reward im Knopf beschriftet | H | S | Q1, Q6 [B-V] |
| 22 | **Willkommen zurück ×2** (Offline) — Platzierung steht in `main.gd`, Text schärfen („Aufrufe von 4 h verdoppeln“) | H | S | Q1, Q5, Q6 |
| 23 | **Geschenkplatzierung** (Truhe/Investor; Wert variabel, Mystery) mit Cooldown | M | M | Q5, Q24 |
| 24 | **Werbung nie vor Minute 5 / vor erstem Raumkauf**; Tutorial-Schutz | H | S | Q9 |
| 25 | **„Noch X €“-Angebot**: wenn Geld in < 60 s reicht, Angebot „Sofort · Werbung“ am Kaufknopf — Goal-Gradient-Moment | M | S | Q24 (Verlustmoment) [V] |
| 26 | **Hartwährungs-Alternative** (×2 per Werbung, ×3 per Münze) für spätere IAP-Verknüpfung | N | M | Q5 |
| 27 | **Messung einbauen** (Analytics fehlt): Angebot gezeigt / angetippt / abgeschlossen je Platzierung — ohne Messung keine A/B-Tests | H | M | Q24 [B-V] |
| 28 | **Einwilligung (UMP/DSGVO)** vor erster Anzeige; `ad_service_admob.gd` füllen; Testgeräte | H (Pflicht) | M | [W] |
| 29 | **Keine Interstitials in 1.0** (bewusste Entscheidung festhalten) | H | S | Q22, Q23 |
| 30 | **Frequenzlimit** im Daten-JSON: z. B. max. 1 Angebot pro 3 min sichtbar, Cooldown je Platzierung | M | S | Q10, Q21 |

### 9.3 A/B-Testideen (Hypothese, Messgröße)

Voraussetzung: Maßnahme 27 (Messung). Zuteilung per `experimente.json`, Spieler dauerhaft einer Gruppe.

1. **Zwei Zoom-Stufen vs. aktueller Startzoom.**
   Hypothese: Der Überblickszoom senkt Orientierungsverluste.
   Messgröße: Zeit bis zum ersten Raumkauf; Anteil Tipps auf nichts-Treffer; D1-Retention.
2. **„Nächstes Upgrade“-Pfeil an/aus.**
   Hypothese: Der Pfeil erhöht die Upgrade-Rate in den ersten 10 Minuten und senkt Abbrüche vor Minute 8.
   Messgröße: Upgrades je Minute (min 1–10); Anteil Spieler mit ≥ 2 Räumen nach 10 Minuten; D1.
3. **Boost-Knopf: dauerhaft sichtbar vs. nur im Menü.**
   Hypothese: Dauerhaft sichtbarer Knopf verdoppelt die Opt-in-Rate, ohne D1/D3 zu senken.
   Messgröße: Anteil DAU mit ≥ 1 abgeschlossener Rewarded (Ziel laut Q24 > 50 %); Abschlussquote (Ziel ≥ 80 %); D1/D3.
4. **Beschriftung: „Video ansehen“ vs. „2 Std. ×2 Einnahmen“.**
   Hypothese: Konkrete Belohnung erhöht Antipp- und Abschlussrate.
   Messgröße: Angebote angetippt / gezeigt; Abschluss / angetippt.
5. **Erste Werbung ab Minute 5 vs. ab Minute 15.**
   Hypothese: Frühe Werbung bringt mehr Einnahmen pro Spieler, senkt aber D1.
   Messgröße: Rewarded je DAU am Tag 1; D1; Tutorial-Abschluss.
6. *(optional)* **Rang-Up mit Inhalt vs. altes Level.** Messgröße: Sitzungen pro Tag; Wiederkehr nach Rang-Up.

Statistik-Hinweis [V]: Bei wenigen Spielern (< einige Hundert je Gruppe) sind D1-Unterschiede < 5 Prozentpunkte nicht verlässlich; zuerst auf Verhaltens-Messgrößen (Zeit bis Raumkauf, Tipp-Treffer) stützen.

### 9.4 Reihenfolge (Vorschlag)

1. **Sofort (Tage):** 3, 4, 8, 11, 17, 21, 22, 24, 29, 30, 16 — klein, mit hoher Sichtwirkung auf Bastians Befund.
2. **Danach (1–2 Wochen):** 1, 2, 5, 6, 7, 10, 12, 13, 15 + 27/28 (Messung, Einwilligung als Voraussetzung für Werbung).
3. **Später:** 9, 14, 18, 19, 20, 23, 25 und A/B-Tests 1–5.

---

## 10. Risiken und offene Fragen

- **Belegbarkeit:** Zahlen zur Kamera/Zoom je Spiel und zu Zeiten je Gebiet sind nicht belegt; vor Festlegen von Zoom-Stufen 10 Minuten Eatventure/Idle Miner/My Perfect Hotel auf dem Handy spielen und Screenshots in `docs/neu/` ablegen [V].
- **eCPM-Annahmen** stammen aus Anbieterberichten und weichen bis Faktor 2; Deutschland nicht einzeln belegt. Kein Umsatzziel daraus ableiten.
- **Fairness-Umfragen** sind von Werbefirmen; Richtung ja, Prozentwerte nein als Maßstab.
- **Rechtliches:** Einwilligung (UMP/DSGVO), Kinderschutz-Einstufung und „Cannabis“-Spielname/Thema im Play-Store (Werbepolicy) vor dem Einbau von AdMob klären [W].
- **Funktion vor Design:** Alle Karten-Änderungen (Zoom, LOD, Plaketten) laufen über `worlds.json` und Darstellungsschicht; der Kern bleibt unberührt. `validate.ps1` nach jedem Schritt.
- **Offene Frage an Bastian:** Wie viele Werbungen pro Tag hält er für „freiwillig“? Richtwert aus Markt: 5–10 [B].

---

## 11. Quellenverzeichnis

| Kennung | Quelle | URL |
|---|---|---|
| Q1 | Pangle: Kolibri Games / Idle Miner Tycoon Fallstudie (Rewarded-Platzierungen, Boost, Willkommen zurück) | https://www.pangleglobal.com/resource/27816 |
| Q2 | Mobile Free to Play: „GDC 2019: Deconstructing Idle Miner Tycoon“ | https://mobilefreetoplay.com/gdc-2019-deconstructing-idle-miner-tycoon/ |
| Q3 | GameAnalytics: „Eight lessons from Kolibri Games“ | https://www.gameanalytics.com/blog/making-a-hit-idle-game-eight-lessons-from-kolibri-games |
| Q4 | WN Hub: „Secrets of creating successful idle games from Kolibri Games“ | https://wnhub.io/news/other/item-16505 |
| Q5 | PocketGamer.biz: „Game analysis: Deconstructing Idle Bank Tycoon by Kolibri Games“ | http://www.pocketgamer.biz/game-analysis-deconstructing-idle-bank-tycoon-by-kolibri-games/ |
| Q6 | LevelWinner: Eatventure Beginner's Guide | https://www.levelwinner.com/eatventure-beginners-guide-tips-tricks-strategies/ |
| Q7 | PocketGamer.biz: „Eatventure vs Cat Snack Bar“ (AppQuantum) | https://www.pocketgamer.biz/feature/82671/eatventure-vs-cat-snack-bar-an-analysis-of-both-games/ |
| Q8 | Google AdMob: Rewarded Ads Playbook | https://admob.google.co.in/home/resources/rewarded-ads-playbook/ |
| Q9 | Applixir: Best practices (Werbung nicht in den ersten Sekunden) | https://www.applixir.com/?p=2944 |
| Q10 | Pangle: Best Practices for Rewarded Video Ad Placement in Mobile Games | https://www.pangleglobal.com/resource/27805 |
| Q11 | IdleMinerTycoon Wiki (Fandom) | https://idleminertycoon.fandom.com/wiki/File:Ancient_Boost.PNG |
| Q12 | BlueStacks: Beginner Miner's Guide to Idle Miner Tycoon | https://www.bluestacks.com/blog/game-guides/idle-miner-tycoon/idt-beginner-guide-en.html |
| Q13 | Touch-Target-Größen (Apple 44 pt / Material 48 dp), Sekundärquelle | https://blog.openreplay.com/improving-tap-targets-mobile-ux/ |
| Q14 | Gamedeveloper.com: „The Math of Idle Games, Part III“ | https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii |
| Q15 | PocketGamer.biz: „First impressions count: creating the ultimate FTUE“ (nur Suchzusammenfassung, nicht vollständig abgerufen) | http://www.pocketgamer.biz/first-impressions-count-creating-the-ultimate-first-time-user-experience/ |
| Q16 | PocketGamer.com: Eatventure Tips and Tricks | https://www.pocketgamer.com/eatventure/tips-and-tricks |
| Q17 | Scientific Reports 2024 (Wordle, Goal-Gradient/Near-Miss), via DOAJ; Goal-Gradient-Überblick | https://doaj.org/article/cdde8b4e865c4a929ed8887df870cf17 · https://yukaichou.com/behavioral-analysis/goal-gradient-hypothesis-hull-kivetz-motivation-acceleration/ |
| Q18 | AdVenture Capitalist (Fan-/Steam-Diskussionen, geringe Qualität) | https://steamcommunity.com/app/346900/discussions/0/620712364025150697 |
| Q19 | Kolibri Games: „What happens in one hour of Idle Miner Tycoon“ | https://www.kolibrigames.com/blog/what-happens-in-one-hour-of-idle-miner-tycoon/ |
| Q20 | Wayline: Juice Overload / Game Feel | https://www.wayline.io/blog/juice-overload-sensory-feedback-hurts-gameplay |
| Q21 | Mobvista: Rewarded Ads | https://xmp.mobvista.com/en-blog/docs/Rewarded-Ads |
| Q22 | Store-/Review-Zusammenfassung My Perfect Hotel (SayGames) | https://game-solver.com/my-perfect-hotel/ |
| Q23 | App-Store-Eintrag Idle Supermarket Tycoon („No more Ads“) | https://apppricinglab.com/app/apple/1442064951 |
| Q24 | wie Q8 (Fallstudien CookApps, TutoTOONS, Four Thirty-Three, Game Insight, Habby; Benchmarks) | https://admob.google.co.in/home/resources/rewarded-ads-playbook/ |
| Q25 | GamesBeat: Unity-Report „majority of mobile gamers are open to incentivized video ads“ | https://gamesbeat.com/unity-the-majority-of-mobile-gamers-are-open-to-engaging-with-incentivized-video-ads/ |
| Q26 | PocketGamer.biz: Tapjoy Modern Mobile Gamer Report | https://www.pocketgamer.biz/tapjoy-modern-mobile-gamer-report/ |
| Q27 | Gameloft for Brands: „Rewarded ads: the format players trust and remember“ | https://www.gameloft.com/for-brands/news/rewarded-ads-the-format-players-trust-and-remember |
| Q28 | Playio: Impact of rewarded ads on user retention | https://blog.playio.co/impact-of-rewarded-ads-on-user-retention |
| Q29 | AdPushUp / iion: Rewarded Video best practices (Ablehnen ohne Nachteil) | https://iion.io/blog/rewarded-video-ads-7-essential-best-practices-for-2023 |
| Q30 | Playio: Mobile game eCPM benchmarks 2026 (fasst Appodeal Q4 2024, Tenjin × CAS Q2 2024, Playwire 2025 zusammen) | https://blog.playio.co/mobile-game-ecpm-benchmarks-2026 |

Hinweis: Q9, Q21, Q22, Q29 stammen aus Suchergebnis-Zusammenfassungen, die Seiten selbst wurden nicht vollständig abgerufen; Q15 ebenso. Q17 und Q18 sind Rand- bzw. Foren­quellen.

---

## Anhang: Repo-Fundstellen (nur gelesen, nichts geändert)

- `CLAUDE.md`, `CURRENT_STATE.md`, `docs/neu/K2_NEUKONZEPT.md` (§1.2–1.6, §4.3, §6).
- `project/services/ad_service.gd`, `ad_service_stub.gd`, `ad_service_admob.gd` (TODOs Zeilen 42, 55).
- `project/game/main.gd:82–84, 834–858` (Belohnungs-Callback: Schub, Offline verdoppelt, „nichts da“).
- `project/data/balance/zimmer.json` (`offline.rate` 0,5; `obergrenze_sekunden` 14.400; ausgebaut 43.200).
- `project/core/economy/cost_curve.gd:6` (Haltung „Werbung als Erleichterung“).
