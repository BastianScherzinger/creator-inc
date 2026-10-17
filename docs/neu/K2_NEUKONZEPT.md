# K2 · NEUKONZEPT — „Man versteht, was man aufbaut“

**Stand:** 2026-10-15 · Rolle: Lead Game Designer · Auslöser: Bastians Handy-Test („Story absolut unklar, man weiß nicht, was man macht und verbessert“)
**Art:** Analyse und Konzept. Kein Code, keine Datenänderung, kein Commit. Bekannte Fehler (Menü nicht scrollbar, Räume nicht betretbar, drehender Rahmen am Lüfter) bearbeitet ein anderes Team und werden hier nur erwähnt.
**Messlatte:** Idle Miner Tycoon, Eatventure, My Perfect Hotel, Idle Bank Tycoon.
**Regeln, die weiter gelten:** D3/ADR-010 (Themenbegriffe nur in `data/themes/` und `data/i18n/`), keine Werte im Code, Kern rechnet, Darstellung zeigt.

---

## 0. Das Kernproblem in drei Sätzen

1. **Das Spiel sagt dem Spieler nie, was er aufbaut.** Die Eröffnung wird auf drei Blasen gekappt, der Satz mit dem Ziel („Jetzt kaufen wir einen Gaming-PC“) erscheint nie; danach reden drei Stimmen (Mo, Mira, Tutorialkarte) über drei verschiedene Dinge (Aufrufe, Miete, Pinnwand).
2. **Die Texte sind Pointen für Eingeweihte, keine Spielinformation.** 132 Nachrichten erzählen Running Gags (Reiter drei, Problem das Rolltor, Mo zählt sich mit), die sich aufeinander beziehen, aber als 3,5-Sekunden-Banner oder stumm im Handy ankommen — kein Satz sagt, was sich im Geschäft gerade verändert hat oder was als Nächstes dran ist.
3. **Fortschritt ist nicht fühlbar, weil er inflationär ist.** Level = Anzahl eingelöster Ziele (211 im Bogen), also ein Level-Up alle 2–3 Minuten ohne Inhalt; Welt und Karte heißen „Die WG 13 %“ statt „Gaming-PC 13 %“; der Spieler sieht Prozent, aber nicht, worauf.

---

## 1. Befund — wie das Spiel heute wirklich funktioniert

### 1.1 Core Loop (Kern, `core/`)

Fünf Stationen mit neutralen IDs bilden in jeder Welt dieselbe Kette: `station_intake` → `station_buffer` → `station_processing`; Durchsatz = Minimum der drei (Engpass). `station_transport` multipliziert die Kette (frei mit Raum 1), `station_special` ist die Sondermechanik (frei mit Raum 3). Jede Station: bis zu 50 Stufen (transport/special 30), alle 10 Stufen ein „Stern“ ×1,5, drei Ausstattungsplätze mit je 10 Stufen und sichtbaren Modellwechseln bei 1/5/10. Fünf kaufbare Räume je Welt (200 € → 2 Mio € in Welt 1), jede Welt endet bei 100 % = alles gekauft (`balance/zimmer.json:6 "abschluss": "alles"`). Dazu: Ziele (33–37 je Welt), Tipp-Momente, Boost („Algorithmus“), Crew-Karten, Tagesaufgaben, Tagesgeschenk, Fortschrittsmarken, Erfolge, Offline-Ertrag. Die Mechanik ist solide und gemessen (Simulator: Welt 1 in 77–81 min, Welten 2–6 je 62–70 min, Gesamt 313 min mit Momenten).

**Das ist nicht das Problem.** Das Problem ist, dass nichts davon dem Spieler als Geschäft erklärt wird.

### 1.2 Was der Spieler in der ersten Minute tatsächlich sieht

| Sekunde | Was erscheint | Quelle | Warum es nicht trägt |
|---|---|---|---|
| 0 | Key-Art + Titel „HELLO WORLD“ + Chatkarte Mo: „Bruder.“ → „Dein erster Clip hat drei Aufrufe.“ → „Zwei davon warst du.“ → Antwortchip „Und jetzt?“ | `themes/zimmer/theme.json:193–218`, `szene_view.gd:77` (`blasen.slice(0, 3)`) | Die Blasen 4 und 6 („Der dritte war ich“, **„Jetzt kaufen wir einen Gaming-PC …“**) werden abgeschnitten. Der Antwortchip hat keine Reaktion. **Das Ziel wird nie genannt.** |
| ~5 | Tutorialkarte „Idee — Die Pinnwand: Hier fängt jeder Clip an. Gerade ist sie am langsamsten — tipp sie an.“ | `theme.json:127–130` | „Idee“ ist ein Stationsname, der nach nichts aussieht (eine Pinnwand). Warum eine Pinnwand Geld bringt, sagt niemand. |
| ~5 | gleichzeitig: `nachricht_01` (Mira, Szene: „Miete ist am Ersten. Der Kanal zahlt keine.“ / „Tobi überlegt auszuziehen“) wird ausgelöst, aber während des Tutorials unterdrückt und landet stumm im Handy | `balance/zimmer.json:608–614`, `hud.gd:555` | Drittes Thema (Miete, Tobi) ohne Zusammenhang zur Pinnwand. Sichtbar erst nach dem Tutorial — dann ohne Kontext. |
| ~20 | Tutorial „Schneller werden — Ein paar Stufen, und die Pinnwand ist nicht mehr das Problem. Dann ist es etwas anderes.“ | `theme.json:131–134` | Sagt nicht, was Ausbauen bringt (mehr Geld pro Sekunde). |
| ~60 | HUD: Kopfleiste „41 € · +1,1 €/s“, Weltleiste „DIE WG · 2 %“, Chip „Rang 1“, fünf Knöpfe (Ausbau · Ziele · Algorithmus · Handy · Fortschritt) | `kopfleiste.gd:256`, `menueleiste.gd:23`, `theme.json:755` | Prozent wovon? „Algorithmus“ als Knopfname ist Insider. Fünf Menüs offen, bevor der Spieler weiß, was ein Clip ist. |

**Ergebnis:** Ein Neuling kennt nach 60 Sekunden weder das Geschäft (Clips → Aufrufe → Geld), noch das Ziel (Gaming-PC), noch den Grund fürs Ausbauen (€/s).

### 1.3 Warum die Texte als „Insider/Slang“ ankommen

Nicht der Wortschatz ist das Problem (es gibt kaum echten Slang), sondern dass fast jede Nachricht **eine Pointe ohne Spielinformation** ist und **auf etwas verweist, das der Spieler nie gelesen hat**:

| Text (Datei:Zeile) | Was fehlt |
|---|---|
| „Abonnent Nummer 1. Das bin ich. Ein Danke reicht.“ (`zimmer/theme.json:453`) | Keine Aussage über das Geschäft. |
| „100 Aufrufe. 61 davon Mo. Bei Aufruf Nr. 3 steht: Herkunft unbekannt.“ (`:458`) | „Herkunft unbekannt“ ist ein Geheimnis-Faden (S1-Bibel), den niemand angekündigt hat — liest sich wie ein Fehler. |
| „Ich hab ausgerechnet, was ein Gaming-PC kostet. Setz dich hin. Der Stuhl kostet extra.“ (`:494`) | Der Spieler weiß nicht, dass der Gaming-PC das Ziel ist (siehe 1.2). |
| „380 Shirts. Weil 400 zu rund war. Du zahlst sie ab. Reiter drei.“ (`webseiten/theme.json`, `nachricht_01`) | Erste Nachricht der Welt 3: „Reiter drei“ ist ein Gag aus Romans Tabelle, den es nur in späteren Nachrichten gibt. |
| „Kein Kaffee. Ich hab's notiert. Miete zahlen wir hier in Videos.“ (`auftrag/theme.json`, `nachricht_01`) | Callback auf Welt-1-Cliffhanger; sagt nicht, was im Studio zu tun ist. |
| „Du bist der mit den drei Aufrufen. Die Halle hat Starkstrom … Die Sicherung hat 63 Ampere. Mo hat einen Wasserkocher.“ (`produkt/theme.json`, `nachricht_01`) | 160 Zeichen, Banner kappt bei 85. „Rigs“, „Blöcke“, „Staking“ (Stationsnamen) sind Krypto-Fachwörter, die 14- bis 40-Jährige nicht sicher kennen. |
| Boost-Knopf „Der Algorithmus“ / „Der Algorithmus mag dich“ (`zimmer/theme.json:154–157`) | Creator-Insider. In Welt 2 „Viral-Push“, Welt 6 „Marktfenster“ — fünf Namen für denselben Knopf. |
| Stationsnamen „Idee / Aufnahme / Schnitt / Upload / Der Stream“ | Für sich verständlich — aber nie als Kette erklärt. Niemand sagt „Ein Clip geht durch drei Schritte“. |
| Rang-Chip „Rang 1“, Welt-Leiste „13 %“, Marken 🎁 ohne Beschriftung (`de.json:118`, V1-Kritik A2) | Zwei Fortschrittszahlen ohne Bezugsgröße. |

Dazu kommen die Mechanik-Meldungen des Overhauls („Bremst gerade“, „Bringt gerade nichts – Engpass: Idee“, „Noch 3 bis ×1,5“), die korrekt sind, aber ohne Einführung wie Warnungen wirken.

### 1.4 Level/Rang heute

`erfolge.json:3`: `"spieler_level": {"max": 150, "ziele_je_level": 1}` · `achievements.gd:65`: `level = 1 + ziele_gesamt / ziele_je_level`. Welt 1 hat 33 Ziele, der Bogen 211. Folge: **Level-Up alle 2–3 Minuten** (Welt 1: 33 Level-Ups in 80 min), Deckel 150 ist mitten in Welt 5 erreicht, danach passiert nichts mehr. Der Level-Up-Moment zeigt „Level 3“ und eine nackte „3“ (V1 A6) — kein Inhalt, keine Freischaltung. Genau das, was Bastian beschreibt: „bei jeder Belohnung ein neues Level“.

### 1.5 Tutorial heute

Sechs Schritte (`tutorial/tutorial.json`): Station wählen → 6 Stufen → 1 Ausstattung → 2× Engpass gesehen → Ziele-Menü öffnen → Flur kaufen. Mechanisch richtig, aber: (a) kein Schritt nennt das Geschäft oder das Ziel, (b) alle fünf Menüknöpfe sind von Anfang an aktiv, (c) Welten 2–6 haben dieselben Tutorial-IDs, aber neue Mechaniken (Speicher, Stammkunden, Überlast, Bestand, Risiko) werden nie eingeführt.

### 1.6 Karte heute

Welt 1: 23 × 17 m, 8 Zonen (Zimmer + 5 kaufbare + Bad, Miras Zimmer als Deko). Gesperrte Räume: Schleier + Tür-Pille „Die Küche · 2.000 €“. Es fehlt: **was** man im Raum bekommt (Station-Silhouette), **warum** (Bonus in Klartext), und ein Blick über die Welt hinaus (keine Stadt-/Standortkarte: Der Spieler sieht nie, dass sechs Standorte auf ihn warten). Welten 2–6 nutzen denselben Grundriss (D1 A0), gemildert durch Kulissen.

---

## 2. Prämisse und Pitch (a)

**Prämisse in einem Satz:**
> Du baust aus einem Handy-Clip mit drei Aufrufen Schritt für Schritt deine eigene Firma auf — von der WG bis zum Firmensitz über der Stadt — und dein bester Freund Mo ist von Anfang an dabei.

**Elevator Pitch (Store, 3 Sätze):**
> Dein erster Clip hat drei Aufrufe — zwei davon warst du selbst. Bau daraus ein echtes Geschäft: erst ein Zimmer mit Handy und Laptop, dann ein Studio, ein eigener Laden, ein Lager, ein Rechenzentrum und am Ende eine Firmenzentrale über der Stadt. Jede Station, die du ausbaust, steht sichtbar im Raum. Jeder Raum, den du kaufst, bringt neue Möglichkeiten. Und Mo isst dabei alle Chips.

**Wer ist Mo?** Dein bester Freund seit der Schule, dein erster Zuschauer, später dein erster Mitarbeiter und Mitgründer. Er ist **die eine Stimme, die dem Spieler erklärt, was los ist** — Tutorial, Ziel der Welt, Offline-Bericht, Raumkauf. Alle anderen Figuren (Mira, Tobi, Younes, Roman, Jana, Selin) sind Farbe; sie dürfen witzig sein, aber nie die einzige Informationsquelle.

**Welches Business?** Eine Creator-Firma, die wächst: Clips → Auftragsvideos → eigene Marke (Merch) → Logistik → eigene Technik → Beteiligungen. IDs, Mechanik und Räume bleiben. Nur die **Bedeutung** wird jetzt in jeder Welt in einem Satz gesagt.

**Ziel je Welt — ein Gegenstand/Ereignis, das man kaufen oder erreichen kann (steht dauerhaft in der Kopfleiste):**

| Welt | Ort | Was du aufbaust | Welt-Ziel (Leistenname) | Wie es endet |
|---|---|---|---|---|
| 1 `zimmer` | Die WG | Deinen Kanal: Idee → Aufnahme → Schnitt → Upload | **Der Gaming-PC** | Das Paket kommt, der PC bootet. Younes bietet die Garage an. |
| 2 `auftrag` | Das Studio (Garage) | Bezahlte Videos für Kunden | **Das Studio gehört euch** (Younes' Onkel verkauft die Garage) | Younes sagt einmal „gut so“. Roman meldet sich mit 380 Shirts. |
| 3 `webseiten` | Der Laden | Deine eigene Marke: Design → Druck → Verpacken → Versand | **1.000 Shirts verkauft / der Laden ist abbezahlt** | Jemand trägt deinen Hoodie vor der Tür. Roman hat eine Halle. |
| 4 `buero` | Das Lager | Ein Team, das ohne dich arbeitet | **Der Großhändler-Vertrag** | Das Lager läuft nachts. Selin schreibt. |
| 5 `produkt` | Das Rechenzentrum (heute „Die Farm“) | Eigene Technik: Strom → Server → Rechenleistung, die andere mieten | **Die Halle läuft von allein** | Niemand muss mehr danebenstehen. Selin: „Ganz oben liegt eine Liste.“ |
| 6 `kapital` | Die Zentrale (heute „Das Portfolio“) | Deine Firma beteiligt sich an anderen Gründern | **Alle sind da** (Dachterrasse) | Jemand Neues mit drei Aufrufen. „Ich schreib ihm.“ |

Welt 5 und 6 behalten IDs, Mechanik und Räume; sie werden nur **umgedeutet** (Rechenzentrum statt Krypto-Farm, Beteiligungen statt Aktien). Das ist optional (Paket P7) und löst nebenbei den Pflichthinweis-Druck („keine Anlageberatung“) — er bleibt trotzdem stehen.

---

## 3. Die ersten 10 Minuten, Bild für Bild (b)

Grundregel: **Eine Stimme (Mo), ein Ziel (Gaming-PC), ein Knopf pro Bildschirm.** Alles, was der Spieler nicht braucht, ist noch nicht da. Zeiten laut Simulator-Einstieg (erstes Upgrade < 10 s, 4+ Upgrades/min, Raum 2 bei ~3:30).

| Zeit | Bild | Was der Spieler sieht | Was er tippt | Belohnung / Freischaltung |
|---|---|---|---|---|
| 0:00 | **Key-Art** (bleibt, bester Bildschirm) | Fassade, Titel. Mo-Szene, **3 Blasen**: „Dein erster Clip hat drei Aufrufe.“ → „Zwei warst du. Einer war ich.“ → „Lass uns daraus was machen. Ziel: dein erster Gaming-PC.“ | Knopf **„Los geht's“** (kein Antwortchip) | — |
| 0:05 | **Zimmer, leer-ruhig** | Nur Kopfleiste (30 €, +0 €/s) und **Welt-Ziel-Leiste „Der Gaming-PC · 0 %“**. Keine Menüleiste, keine Marken, keine Badges. Zeigehand auf der Pinnwand. Mo-Blase unten: „Deine Ideen hängen an der Pinnwand. Tipp drauf.“ | Pinnwand | Stationsmenü öffnet |
| 0:10 | **Stationsmenü „Ideen“** (Held-Zeile: 1 → 2 Ideen/Min · +0,5 €/s) | Hand auf dem Limetten-Knopf „AUSBAUEN · 25 €“. Mo: „Mehr Ideen = mehr Clips = mehr Geld. Bau aus.“ | AUSBAUEN (1×) | Münzflug, +€/s in der Kopfleiste zählt hoch |
| 0:20 | Menü schließt automatisch; Kamera zeigt **die Kette**: drei Stationen mit **Pfeilen** Ideen → Aufnahme → Schnitt (einmalige Einblendung, Sticker-Stil) | Mo: „Jeder Clip geht durch drei Schritte. Der langsamste bremst alle.“ Die langsamste pulst rot. | rote Station | Stationsmenü |
| 0:30 | Stationsmenü Aufnahme/Schnitt | Hand auf AUSBAUEN. Mo: „Rot heißt: hier klemmt's. Immer zuerst das Rote.“ | 2–3× AUSBAUEN | — |
| 0:50 | **Erstes Ziel** erscheint als Karte oben (Zielleiste): „Schnitt auf Stufe 5 · 🎁 50 €“ | Mo: „Dein erstes Ziel. Schaffst du in einer Minute.“ | weiter ausbauen | Bei Erfüllung: Zielleiste wird gold, „HOLEN“ |
| 1:40 | **Belohnungsmoment** (Vollbild, Zahl zählt 0 → 50) | Mo jubelnd: „50 €. Der PC rückt näher.“ Welt-Ziel-Leiste springt sichtbar (0 → 3 %). | HOLEN | +50 €, **Zielleiste bleibt ab jetzt** |
| 2:00 | **Ausstattung**: Im Stationsmenü Aufnahme leuchtet die Zeile „Kamera · Handy auf Büchern → Kleines Stativ · 60 €“ | Mo: „Ein Stativ. Steht dann wirklich da. Und macht schneller.“ Hand auf dem Zeilenknopf. | Kaufen | Modell im Raum wechselt sichtbar (Moment „Gekauft: Kleines Stativ“) |
| 2:30 | **Rang 2 „Hobby“** (erster Rang-Up, Vollbild) | „Rang 2 · Hobby“ + eine Zeile: „Neu: Ziele-Übersicht“. Menüleiste erscheint mit **einem** Knopf (Ziele). | Weiter | Freischaltung Ziele-Menü |
| 3:30 | **Der Flur** (200 €): Tür-Schild mit Silhouette der neuen Station, „Neu: Upload · 200 €“ | Mo: „Hinter der Tür steht der Router. Kauf den Flur, dann laden deine Clips von allein hoch.“ Hand auf der Tür. | Tür → Raum-Panel → KAUFEN | **Raumkauf-Moment** (bleibt wie `p_raum`): Schleier fällt, Upload erscheint, Figur läuft rein |
| 4:00 | Upload-Station | Mo: „Upload macht alles schneller — je höher, desto mehr Reichweite.“ Kein Zwang zum Kauf. **Tutorial endet.** Menüleiste bekommt Knopf „Ausbau“ (Übersicht). | frei | **Handy** erscheint beim ersten Chat-Eingang (siehe 5.4), nicht vorher |
| 5:00 | Erste echte Nachricht (Banner + Handy): Mira: „Dein Zimmer sieht aus wie ein Studio. Und meine Lampe ist weg.“ | Handy-Knopf mit Punkt | optional | — |
| 6:00 | **Rang 3 „Creator“** | „Neu: Trend-Boost“ — Boost-Knopf erscheint in der Mitte; Mo: „Wenn ein Clip läuft, läuft er. Boost = 2× für 4 Minuten.“ | Boost (einmal gratis, ohne Werbung) | Boost ×2 |
| 8:00 | Küche in Sicht (2.000 €): Tür-Schild „Alle Stationen ×1,25 · 2.000 €“; Zielleiste zeigt „Die Küche kaufen · 🎁 2 Min Einkommen“ | Mo: „Die Küche. Tobi kocht, alle werden schneller.“ | sparen / Boost | — |
| 10:00 | Küche gekauft (Simulator 8:15) → **Rang 4 „Kanal“** | „Neu: Crew“ (Mo als erste Crew-Karte an der Aufnahme) + Fortschritt-Menü (Welt-Übersicht) | Crew ansehen | ab hier Normalbetrieb; Tagesgeschenk erst am 2. Tag, Tagesaufgaben ab 20 % (bleibt) |

**Was bis Minute 10 NICHT passiert:** kein Werbeangebot, keine Marken-Tooltips, kein „Rang 1“-Chip ohne Erklärung, keine Mira/Tobi-Szene mit Antwortchips, kein Geheimnis („Herkunft unbekannt“), keine fünf Menüs.

---

## 4. Progression und Pacing (c)

### 4.1 Rang statt Level — Meilensteine, nicht Zähler

**Prinzip:** Der Rang ist der **Firmen-Rang** über den ganzen Bogen, 30 Stufen (5 je Welt), jede mit Namen, jede schaltet etwas frei oder bringt einen dauerhaften Bonus. Rang-Ups sind **Ereignisse** (Vollbild, Zahl zählt hoch, eine Zeile „Neu: …“), weil sie selten sind: in Welt 1 fünf statt 33.

**Datenmodell (minimal, passt in `erfolge.json`):** statt `ziele_je_level` eine Schwellenliste über **Punkte**. Punkte = gewichtete Ziele: normales Ziel 1, Raumziel (`typ: bereich`) 3, Welt-Mission (`kette: welt`) 5, Weltabschluss 10. Werte in Daten, Kern zählt.

```
"rang": {
  "punkte": {"ziel": 1, "bereich": 3, "mission": 5, "welt_fertig": 10},
  "schwellen": [0, 2, 8, 16, 28, 45,   62, 80, 100, 122, 146,   172, 200, 230, 262, 296,  ...],
  "freischaltung": {"2": "menue_ziele", "3": "schub", "4": "crew+fortschritt", "5": "tagesaufgaben", ...}
}
```

Richtwert je Welt (Welt 1 hat 33 Ziele ≈ 33 + 5·2 + 3·4 + 10 = 65 Punkte): Rang-Ups bei ~3 %, 12 %, 25 %, 45 %, 70 % des Weltfortschritts — also nach ~2, ~8, ~20, ~40, ~60 Minuten (Simulator) bzw. 1,5× für echte Spieler. Welt 2–6 analog (jede Welt +5 Ränge). Rang 30 = Abspann. Prestige (Neuanfang) fügt Sterne am Rang an statt Zahlen.

**Rangnamen (in `i18n/de.json`, weltneutral, oder je Welt in `theme.json` → `raenge[]`):**

| Rang | Name | Freischaltung / Bonus |
|---|---|---|
| 1 | Anfang | — |
| 2 | Hobby | Ziele-Menü |
| 3 | Creator | Boost (Trend-Boost) |
| 4 | Kanal | Crew-Karten, Fortschritt-Menü |
| 5 | Kleines Team | Tagesaufgaben, Offline-Obergrenze 4 → 6 h |
| 6 (W2) | Auftragnehmer | Umbau-Mechanik Speicher wird erklärt |
| 7–10 | Studio-Chef … Produktionsfirma | +2 % Einkommen je Rang (ersetzt Erfolgs-Bonus-Inflation) |
| 11–15 (W3) | Marke, Ladenbesitzer … | Stammkunden erklärt; Offline 6 → 8 h |
| 16–20 (W4) | Arbeitgeber … | Überlast erklärt; Offline 8 → 12 h |
| 21–25 (W5) | Betreiber … | Bestand erklärt |
| 26–30 (W6) | Gründer, Investor, … „Hello World“ | Risiko erklärt; Rang 30 = Abspann |

Die Namen sind thematisch → `data/i18n/de.json` ist erlaubt (D3). Die Rang-Logik bleibt neutral in `achievements.gd`.

### 4.2 Zielsystem — drei Ebenen, immer sichtbar

| Ebene | Was | Sichtbar | Bestand heute |
|---|---|---|---|
| **Welt-Ziel** (1 je Welt) | „Der Gaming-PC“ = 100 % der Welt; Leiste oben mit den drei Marken 25/50/75 % als **Zwischenschritte mit Namen** („Stativ steht“, „Erster Stream“, „Paket bestellt“) | Kopfleiste, dauerhaft | Welt-Leiste + Marken existieren; nur Beschriftung fehlt (`theme.json` → `welt_ziel`, `marken_namen[]`) |
| **Aktuelles Ziel** (1 sichtbar) | Kette je Raum, wie heute (`ziele[].kette`) | Zielleiste, auch bei offenem Sheet | existiert |
| **Tagesaufgaben** (2 je Tag ab 20 %) | wie heute | Chip „HEUTE“ | existiert |

Änderung an den Zielen selbst: **keine neuen Ziele**, aber jedes Ziel bekommt im Thema einen Halbsatz „warum“ (`ziel_formate` → zusätzlich `ziel_warum.<typ>`), z. B. „Schnitt auf Stufe 10 — damit die Aufnahmen nicht liegen bleiben.“ Die Zielleiste zeigt ihn nur im Ziele-Menü.

### 4.3 Zeitplan Welt 1–6

Simulator (optimal) heute: W1 77–81 min · W2 64 · W3 69 · W4 64 · W5 62 · W6 63 → 6,5 h; echte Spieler ~1,5–2× → 10–13 h aktiv. Top-Idle-Referenz: erste Welt am ersten Tag fertig, dann 2–5 Tage je Welt mit Offline-Phasen.

**Vorschlag (ohne Formeländerung, nur Daten):**

| Welt | Ziel aktiv (Sim.) | Ziel real inkl. Offline | Stellschrauben (`balance/<welt>.json`) |
|---|---|---|---|
| 1 | 75–80 min | Tag 1 (2 Sitzungen) | bleibt; `luecke_max` 360 s bleibt |
| 2 | 70–80 min | Tag 2 | `ziel_belohnung_faktor` 0,5 → 0,4; Offline-Obergrenze 6 h ab Rang 5 |
| 3 | 80–90 min | Tag 2–3 | `ziel_belohnung_faktor` 0,35; Raum 4/5 `kosten` +20 % |
| 4 | 90–100 min | Tag 3–4 | `ziel_belohnung_faktor` 0,3; Raum 5 +25 %; Offline 8 h |
| 5 | 100–110 min | Tag 4–6 | `ziel_belohnung_faktor` 0,3; Raum 4/5 +30 %; Offline 12 h |
| 6 | 110–120 min | Tag 6–8 | `ziel_belohnung_faktor` 0,25; Missionen bleiben |

Der Korridor in `validate.ps1`/`balance_sim.gd` (60–90 min) muss dafür je Welt parametrisierbar werden (Paket P6). Einstieg bleibt unverändert (erstes Upgrade < 10 s, Raum 2 < 4 min) — das ist bereits gut.

### 4.4 Rang-Up-Moment (ersetzt den leeren Level-Up)

Vollbild: Porträt Mo jubelnd, Held-Zahl „Rang 4“ zählt 3 → 4, Name „Kanal“, **eine** Zeile „Neu: Crew-Karten“ oder „+2 % Einkommen“, Knopf „Weiter“. Nie ohne Inhalt.

---

## 5. Story-Auslieferung (d)

### 5.1 Regeln (ersetzen STORY.md §Ton 1–12 nicht, ergänzen sie als 13–20)

13. **Jede Nachricht ist allein verständlich.** Kein Satz setzt eine frühere Nachricht voraus. Running Gags nur als Zugabe hinter einer Information.
14. **Mindestens die Hälfte jeder Welt sagt etwas über das Geschäft:** was sich geändert hat, was als Nächstes lohnt, was das Welt-Ziel ist.
15. **Blase ≤ 90 Zeichen, Banner ≤ 85, Antwort ≤ 14** (Platzgrenzen aus S1). Ein Gedanke je Blase.
16. **Wortschatz: Alltagsdeutsch.** Verboten ohne Erklärung im selben Satz: Algorithmus, Reiter, Take, Drop, Rig, Block, Staking, Streuung, Dividende, Render, Greenscreen, Fulfillment. Erlaubt: Clip, Aufrufe, Upload, Stream, Shirt, Paket, Server, Strom.
17. **„Bruder“ höchstens einmal je Welt** (Mos Eröffnung). Danach Name oder nichts.
18. **Geheimnis-Faden („der dritte Aufruf“) erst ab Welt 2**, und nur in Szenen, nie in Bannern. In Welt 1 bleibt es ein Witz („Einer war ich“), kein Rätsel.
19. **Tutorial, Welt-Ziel, Raumkauf, Rang-Up, Offline-Bericht: immer Mo.** Andere Figuren tragen Stimmung, nie Pflichtinformation.
20. **Start jeder Welt = Szene mit drei Blasen**, die (1) den Ort, (2) das Geschäft, (3) das Welt-Ziel nennt. Antwortchips erst ab Welt 2.

D3 bleibt: alle Texte in `data/themes/<welt>/theme.json` und `data/i18n/de.json`.

### 5.2 Ton

Kurz, warm, konkret. Mo redet wie ein Freund, der sich freut — nicht wie ein Komiker. Zahlen bleiben krumm (380, 2:51 Uhr), aber nur dort, wo sie etwas bedeuten. Jede Szene: ein Lacher, ein Haken — und der Haken ist das nächste Ziel.

### 5.3 Beispiel-Neutexte für die ersten 10 Szenen (Welt 1, alle ≤ 90 Zeichen)

| # | Auslöser (bleibt) | Figur | Blasen | Antwort (ab Szene 4) |
|---|---|---|---|---|
| 1 | Eröffnung (`eroeffnung.chat`) | Mo | „Dein erster Clip hat drei Aufrufe.“ · „Zwei warst du. Einer war ich.“ · „Lass uns daraus was machen. Ziel: dein erster Gaming-PC.“ | Knopf „Los geht's“ |
| 2 | `nachricht_01` (Start, **jetzt Mo**, Banner statt Szene) | Mo | „Ideen, Aufnahme, Schnitt. Drei Schritte, ein Clip. Das Rote bremst.“ | — |
| 3 | `nachricht_02` (1 Ausstattung) | Mira | „Dein Zimmer sieht aus wie ein Studio. Und meine Lampe ist weg. Zufall?“ | — |
| 4 | `nachricht_05` (Flur gekauft, Szene) | Mo → Mira | Mo: „Der Router steht im Flur. Deine Clips laden jetzt von allein hoch.“ · Mira: „Das WLAN im Bad ist jetzt besser als in meinem Zimmer.“ · Mira: „Danke?“ | „Gern.“ / „Sorry.“ |
| 5 | `nachricht_04` (500 € verdient) | Dein Kanal | „100 Aufrufe. 61 davon Mo. Die anderen 39 sind echt.“ | — |
| 6 | `nachricht_16` (11 %) | Mo | „Ich hab nachgeschaut, was der Gaming-PC kostet. Wir schaffen das. Irgendwann.“ | — |
| 7 | `nachricht_06` (Küche gekauft, Szene) | Tobi → Mo | Tobi: „Die Küche ist frei. Ich koch für drei.“ · Mo: „Wer isst, schneidet schneller. Alles läuft jetzt ×1,25.“ · Tobi: „Mo zählt als zwei.“ | „Guten Appetit.“ / „Ich auch?“ |
| 8 | `nachricht_18` (29 %) | Dein Kanal | „1.000 Aufrufe. Die ersten Leute, die du nicht kennst, schauen zu.“ | — |
| 9 | `nachricht_09` (Wohnzimmer gekauft, Szene) | Mo | „Sofa, Fernseher, Chat. Ab heute streamen wir abends.“ · „Der Chat zahlt mit. Jeder Clip bringt jetzt mehr.“ · „Vier Zuschauer haben zugesagt. Zwei davon bin ich.“ | „Deal.“ / „Zwei?“ (Reaktionen bleiben) |
| 10 | `nachricht_20` (51 %, Szene) | Mo → Tobi | Mo: „1.000 Leute gleichzeitig im Stream!“ · Mo: „Halbzeit. Der PC ist zur Hälfte bezahlt.“ · Tobi: „Wer hat auf meinen Kühlschrank geschrieben?“ | „Mo.“ / „Ich?“ |

Danach unverändert möglich: `nachricht_11` (Tobi zieht aus), `nachricht_12` (Cousine), `nachricht_21` (Paket piept), `nachricht_22` (Er bootet), `nachricht_15` (Younes). Ersetzt werden `nachricht_03` („Abonnent Nummer 1“ → „Dein Clip hat 8 Stufen hinter sich. Nächstes Ziel: der Flur.“) und `nachricht_04`-Nachsatz „Herkunft unbekannt“ (raus aus Welt 1, Regel 18).

### 5.4 Kanäle

| Kanal | Wofür | Regel |
|---|---|---|
| **Szene** (Popup, Porträt, ≤ 3 Blasen, Antworten) | Weltstart, jeder Raumkauf, 50 %, Cliffhanger, Abschluss (5 je Welt, wie heute) | Nur außerhalb des Tutorials. Die Startszene läuft **statt** Tutorialtext, nicht parallel. |
| **Mo-Sprechblase in der Welt** | Tutorial, Rang-Up-Hinweis, „hier weiter“ nach 60 s Stillstand | Eine Stimme. Ersetzt die Tutorialkarte mit Titel. |
| **Banner** (3,5 s) + Handy | alle übrigen Nachrichten | Handy-Knopf erscheint erst mit der ersten Banner-Nachricht (Minute ~5). |
| **Raum-Panel „Danach hier“** | was der Raum bringt | bleibt, Text aus `bereiche.<id>.danach`. |

---

## 6. Karte und Räume (e)

### 6.1 Was der Spieler sehen muss (jede Welt)

1. **Gesperrter Raum = Versprechen, nicht Schleier.** Statt grauem Schleier: dunkle Silhouette des Raums, in der Mitte der **gepunktete Umriss der neuen Station** (Eatventure-Regel) und ein Tür-Schild mit zwei Zeilen: „Neu: Upload“ / „200 €“. Bonusräume: „Alles ×1,25“ / „2.000 €“. Kaufbar → Schild pulst in Limette; nicht kaufbar → Papier mit Mini-Balken „1.240 / 2.000“.
2. **Ein Schild je Station** (V1 B7): oben Lv + Sterne, unten Preis-Pfeil **oder** Engpass-Warnung, nie beides. Name nur im Schild.
3. **Welt-Ziel-Marke in der Welt:** Der Gegenstand des Welt-Ziels steht als **Silhouette an seinem Platz** (W1: PC-Umriss auf dem Schreibtisch, der sich mit 25/50/75 % füllt; W2: Schild „Studio – zu verkaufen“ am Rolltor; W3: Schaufenster-Puppe; W4: Vertragsmappe am Tisch; W5: Serverreihe; W6: leere Stühle auf der Dachterrasse). So sieht man das Ziel, ohne die Leiste zu lesen.
4. **Kamera-Fokus beim Raumkauf:** Kamera fährt in den Raum, Schleier fällt, Station erscheint, Figur geht hinein, Mo-Blase „Danach hier: …“. (Bestehender `p_raum`-Moment, nur mit Kamerafahrt.)

### 6.2 Raum-Betreten-Logik (Ziel-Verhalten; der Bug „Räume nicht betretbar“ liegt beim anderen Team)

- Tipp auf **freien Raum** → Kamera zoomt auf den Raum (Zoom-Stufe aus `worlds.json` → `zonen[].zoom`, neu), Raum-Panel öffnet (≤ 56 % Höhe): Stationen im Raum als Zeilen mit Direktkauf, Zielkette des Raums, „Nächster Raum“. Tipp außerhalb → Kamera zurück zur Weltansicht.
- Tipp auf **gesperrten Raum** → Raum-Panel im Kaufzustand: Held-Zeile „Danach hier: Upload (neue Station)“, Primärknopf „KAUFEN · 200 €“, Erklärsatz zuletzt; bei Bedingung („Tobi wohnt noch hier“) Chip mit Bedingung, kein Preis.
- Tipp auf **Station** → Stationsmenü (wie heute). Tipp auf Tür-Schild = Tipp auf Raum.
- Richtungs-Chips am Bildrand (bestehend) führen zum nächsten kaufbaren Raum.

### 6.3 Erweiterung je Welt

| Welt | Heute | Erweiterung (Daten in `worlds.json`, Modelle in `art_source/`) |
|---|---|---|
| alle | 5 kaufbare Räume + 1–2 Deko-Zonen | **Deko-Zone wird 6. Raum** (spät, nach Raum 5, nur Bonus + Figur): W1 Miras Zimmer („Mira zieht mit ein: Crew-Rang III gratis“), W2 Younes' Ecke, W3 Romans Büro, W4 Pausenraum, W5 Selins Labor, W6 Dachterrasse (Abschlussparty als Raum). Kein neuer Zieltyp nötig (`typ: bereich`). |
| alle | Welt = Innenraum | **Außenwelt als Rahmen:** W1 Treppenhaus/Straße mit Fahrrad, W2 Hinterhof mit Container (existiert als Zone), W3 Ladenstraße, W4 Ladehof (Zone existiert), W5 Solardach, W6 Stadt unter dem Penthouse (V1 fordert das). Kulisse, kein Spielraum. |
| alle | kein Blick über die Welt hinaus | **Standortkarte** (neuer Bildschirm im Fortschritt-Menü und beim Weltwechsel): sechs Orte als Sticker auf einer Stadtkarte — WG, Garage, Eckladen, Halle, Fabrik, Hochhaus. Gekauft = farbig mit Rang-Sternen, aktuell = pulsend, kommend = Silhouette mit Vorbedingung „Welt 2 ab Gaming-PC“. Das ist das Idle-Miner-„Kontinente“-Gefühl: Man sieht, dass das Business wächst. |
| 1 | WG 23 × 17 | Balkon bekommt Außenlicht-Effekt (bereits Tageslicht-Bonus), Bad als Deko bleibt |
| 3 | Laden ohne Kunden | Schaufenster-Zone zur Straße mit 2 laufenden Kunden-Figuren (Lebendigkeit, bestehende Routen) |
| 6 | Wolke über Galerie | Stadt-Silhouette unter dem Penthouse (V1 B6) |

---

## 7. Umsetzungsplan in Paketen (f)

Reihenfolge so, dass **nach P1 das größte Verständnisproblem gelöst ist**. Kennzeichnung ‖ = parallel von getrennten Sonnet-Bauagenten ohne Dateikonflikt. Leitung (Opus) hält `game/main.gd`, `data/i18n/de.json` und `validate.ps1` exklusiv. Aufwand in Agentenstunden.

### P1 · „Man versteht, was man aufbaut“ (Welt 1) — 4–6 h, keine Abhängigkeit

| Teil | Dateien (exklusiv) | Was | Aufwand |
|---|---|---|---|
| **P1a ‖ Texte W1** | `data/themes/zimmer/theme.json` | Eröffnung auf 3 Blasen mit Ziel (5.3 #1); `nachricht_01` → Mo, Banner (5.3 #2); `nachricht_03/04/16/05/06/09/18/20` nach 5.3; Tutorial-Texte (3.) als Mo-Sätze; `belohnung.schub_*` „Trend-Boost“ statt „Algorithmus“; `menue.schub` „Boost“; neu `welt_ziel: "Der Gaming-PC"`, `marken_namen: ["Stativ steht","Erster Stream","Paket bestellt"]`; `ziel_warum.<typ>`. Keine neuen IDs. | 2 h |
| **P1b ‖ Szene/Eröffnung** | `game/ui/szene_view.gd`, `tests/unit/test_szene_view.gd` (neu) | `szene_aus_eroeffnung`: alle Blasen zeigen (blättern in Dreiergruppen) oder Eröffnung ohne Antwortchip mit Knopf aus `eroeffnung.knopf`; Reaktion bei fehlender Reaktion = kein Chip. | 1 h |
| **P1c ‖ HUD-Beschriftung** | `game/ui/kopfleiste.gd`, `game/ui/hud.gd` (nur Welt-Leiste), `game/ui/welt_texte.gd` | Welt-Leiste zeigt `welt_ziel` statt Weltname; Marken bekommen `marken_namen` als Tooltip-Toast beim ersten Erreichen; Rang-Chip liest `rang_name` (vorbereitet für P2, bis dahin „Rang %d“). | 1,5 h |
| **P1d ‖ Tutorial-Schweigen** | `game/ui/hud.gd::_auf_nachricht` (Zeile ~549–560) | Szenen, die im Tutorial fällig werden, werden **nach** Tutorialende als Szene gezeigt (Warteschlange), nicht stumm ins Handy gelegt. Banner-Nachrichten im Tutorial bleiben stumm. | 1 h |

Abhängigkeiten: keine untereinander (P1c und P1d sind beide in `hud.gd` → **ein** Agent für P1c+P1d).
**Abnahme:** `godot_console --path project --resolution 540x1200 -- --frisch --mit-tutorial`: Erster Bildschirm nennt „Gaming-PC“; nach dem Tutorial erscheint keine Mira-Szene mit „Miete“; Kopfleiste zeigt „Der Gaming-PC · x %“; `bash tools/serie.sh k2_eroeff --frisch` angesehen; Sperrwort-Prüfung grün; 322 Tests grün. Handy-Test Bastian: „Was baust du auf?“ in Minute 1 beantwortbar.

### P2 · Rang-System — 5–7 h, unabhängig von P1 (‖ zu P1)

| Teil | Dateien | Was |
|---|---|---|
| **P2a Kern** | `core/progression/achievements.gd`, `core/game_core.gd` (nur `spieler_level*`, `_pruefe_level`), `data/balance/erfolge.json`, `tests/unit/test_achievements.gd` (neu), Save-Migration in `core/save/` | Punkte + Schwellen (4.1); `spieler_level_info()` liefert zusätzlich `name_id`, `freischaltung`, `naechste_schwelle`; Freischaltungs-Abfrage `ist_frei(feature)`. Alte Stände: Rang aus Punkten neu berechnen. |
| **P2b Darstellung** | `game/ui/moment_view.gd` (Rang-Up), `game/ui/menueleiste.gd` (Knöpfe nach `ist_frei`), `data/i18n/de.json` (Rangnamen, „Neu: …“-Zeilen — **Leitung schreibt**) | Rang-Up-Moment mit Inhalt (4.4); Menüleiste blendet Knöpfe ein, Handy erst mit erster Nachricht. |

Abhängigkeit: P2b braucht die API aus P2a (Schnittstelle vorab in `docs/neu/k2_schnittstellen.md` festlegen, dann ‖).
**Abnahme:** `welt_sim -- zimmer` zeigt 5 Rang-Ups mit Zeitpunkten (~2, 8, 20, 40, 60 min); `--durchspielen --alle-welten` endet bei Rang 30; Vorschau Rang-Up zeigt Zahl + Name + „Neu: …“.

### P3 · Tutorial 2.0 — 4–5 h, nach P1 (braucht Mo-Blase) und P2b (Menü-Gating)

| Dateien | Was |
|---|---|
| `data/tutorial/tutorial.json`, `game/ui/tutorial_view.gd`, `game/ui/tutorial_ablauf.gd`, `game/ui/zeige_hand.gd`, `tests/unit/test_tutorial_ablauf.gd`; `game/main.gd` (Leitung: Ketten-Einblendung, Auto-Schließen nach erstem Ausbau) | Schritte nach §3: waehlen → ausbauen (1 Stufe, nicht 6) → kette_gesehen (neu, Einblendung mit Pfeilen) → engpass → ziel_erfuellt (neu) → ausstattung → bereich_1. Tutorialkarte wird Mo-Sprechblase ohne Titel. Welten 2–6: Kurz-Einführung mit 2 Schritten (`neu_hier`, `besonderheit`) je Welt, Texte in `theme.json → tutorial` (‖ von den P4-Agenten geschrieben). |

**Abnahme:** `--frisch --mit-tutorial`: erstes Upgrade < 10 s, Tutorial endet bei Raum 1 (~3:30), währenddessen nie zwei Textquellen gleichzeitig; `--welt 2 --mit-tutorial` zeigt die Speicher-Einführung.

### P4 · Story-Texte Welten 2–6 — je 2–3 h, 5 Agenten ‖ (ein Agent = eine `theme.json`), unabhängig von P1–P3

| Agent | Datei | Was |
|---|---|---|
| W2…W6 | `data/themes/<welt>/theme.json` | Startszene nach Regel 20 (Ort, Geschäft, Welt-Ziel); `welt_ziel`, `marken_namen`, `ziel_warum`; alle 22 Nachrichten gegen Regeln 13–18 prüfen und kürzen (≤ 85/90 Zeichen); Boost-Name vereinheitlichen („Boost“ in `menue.schub`, Welt-Beiname nur im Titel); Tutorial-Kurztexte `neu_hier`/`besonderheit`; Welt 5/6 nur Wortschatz (Rigs → Server, Blöcke → Rechenleistung, Staking → Dauerkunden, Streuung → Verteilung) — Umdeutung selbst ist P7. |

Prüfung je Agent: `welt_sim -- <welt>` (22 Nachrichten, 5 Szenen), Sperrwort-Skript, Lesung `docs/neu/lesung_<welt>.md`. Lesung durch einen sechsten Agenten (Redaktion, nur lesen) gegen Regel 13: „Versteht man jede Nachricht allein?“

### P5 · Karte und Räume — 8–12 h, nach P1 (Texte „Danach hier“), ‖ zu P2–P4 in Teilen

| Teil | Dateien | Was |
|---|---|---|
| **P5a ‖ Gesperrte Räume** | `game/world/grundriss_bauer.gd` (Schleier → Silhouette), `game/ui/kartenmarker.gd` (Tür-Schild zweizeilig, Stations-Umriss), `data/worlds/worlds.json` (nur `schild`-Versätze, `zonen[].zoom`) | 6.1 Punkt 1–2 |
| **P5b ‖ Welt-Ziel-Marke** | `art_source/scripts/build_zielmarken.py` neu, `project/assets/world/<welt>/zielmarke_*.glb`, `game/world/` (neuer Node `ZielMarke`), `worlds.json` (`zielmarke: {x,z}`) | 6.1 Punkt 3 (Silhouette füllt sich mit 25/50/75 %) |
| **P5c** (nach Bugfix „Räume nicht betretbar“ des anderen Teams) | `game/ui/hud.gd` (Raum-Panel), `game/world/world_camera.gd` | 6.2 Kamera-Fokus und Kaufmoment mit Fahrt |
| **P5d ‖ Standortkarte** | neu `game/ui/standortkarte_view.gd`, `assets/ui/standorte/*.svg` (6 Sticker), `game/ui/menues.gd` (Eintrag im Fortschritt-Menü), `weltwechsel_view.gd` (Karte vor dem Plakat) | 6.3 Standortkarte |
| **P5e ‖ 6. Raum je Welt** | `data/worlds/worlds.json` (Zone → `bereich_6`), `data/balance/<welt>.json` (`bereiche.bereich_6`, 1 Ziel), `data/themes/<welt>/theme.json` (`bereiche.bereich_6`) — **Konflikt mit P4** → erst nach P4 | 6.3 |

### P6 · Pacing Welten 2–6 — 3–4 h, nach P2 (Rang-Belohnungen verändern Einnahmen), nach P4

| Dateien | Was |
|---|---|
| `data/balance/{auftrag,webseiten,buero,produkt,kapital}.json`, `tools/balance_sim.gd` (Korridor je Welt aus Daten: `balance/<welt>.json → ziel_minuten: [min,max]`), `validate.ps1` (liest Korridor) | Tabelle 4.3 umsetzen, messen, Offline-Obergrenze je Rang. |

### P7 · Umdeutung Welt 5/6 (optional) — 6–8 h, nach P4, ‖ zu P5/P6

`data/themes/produkt/theme.json`, `data/themes/kapital/theme.json`, `docs/STORY.md`, `docs/WELTEN.md`, Store-Texte. Rechenzentrum statt Krypto-Farm, Beteiligungen statt Depot. Mechanik (Bestand, Risiko) bleibt; nur Namen und Sätze. Pflichthinweis bleibt.

### Parallelitätsübersicht

```
Welle 1 (sofort, 8 Agenten):  P1a | P1b | P1c+P1d | P2a | P4-W2 | P4-W3 | P4-W4 | P4-W5 | P4-W6
Welle 2 (nach Welle 1):       P2b | P3 | P5a | P5b | P5d | P6-Vorbereitung (Korridor-Parameter)
Welle 3 (nach Bugfix-Team):   P5c | P5e | P6 | P7
```

Schreibrechte: je Datei genau ein Agent je Welle. `game/main.gd`, `data/i18n/de.json`, `validate.ps1`: nur Leitung. Scratchpad-Präfix `k2_<paket>_`. Kein `validate.ps1` durch Agenten.

---

## 8. Was bewusst bleibt

Sticker-Pop, Stationsmenü-Hierarchie, Zielleiste, Kaufmoment, Welt 2/5 bei Nacht, Lebendigkeit, Mo-Sprechblase in der Welt, Schrift (V1 Teil C) — alles unangetastet. Die Mechanik (Kette, Sterne, Ausstattung, Räume, Crew, Momente) bleibt. Verändert wird, **was der Spieler darüber erfährt und wann**.

## 9. Nicht in diesem Konzept

- Bekannte Fehler: Menü nicht scrollbar, Räume nicht betretbar, drehender Rahmen um einen Lüfter (W5) — anderes Team. P5c wartet darauf.
- Monetarisierung, Werbung, Push — unverändert (GAME_DESIGN §10/11).
- Store-Bilder neu (V1 B8) — nach P1/P5.
