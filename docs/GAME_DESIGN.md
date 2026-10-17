# GAME DESIGN — „Antrag auf Reichtum"

**Stand:** 2026-09-10 · international: *Claim to Fortune* · Konzept: ADR-018

---

## 1. Die Idee in einem Satz

Du sitzt im Wartezimmer eines Amtes, hilfst dem Menschen neben dir beim Formular — und arbeitest dich von dort über eigene kleine IT-Aufträge bis zur eigenen Firma hoch.

**Warum der Titel:** „Antrag auf Reichtum" sagt beides in drei Worten — den Amtsjargon und das Ziel. Er ist als Wortspiel sofort verständlich, klingt trocken statt marktschreierisch und funktioniert auch international (*Claim to Fortune* — „claim" ist Antrag und Anspruch zugleich).

---

## 2. Warum diese Geschichte trägt

Die entscheidende Frage jedes Idle-Games lautet: **Warum soll ich das ausbauen?**

Bei einem reinen Behörden-Tycoon gibt es darauf keine gute Antwort. „Ich optimiere Verwaltungsvorgänge" ist kein Wunsch, den jemand hat.

**„Ich arbeite mich hier raus" ist einer.** Jeder versteht ihn sofort, niemand muss ihn erklärt bekommen. Und er liefert etwas, das Zahlen allein nie können: einen Grund, morgen wieder aufzumachen.

Der zweite Vorteil ist der Weltwechsel. Bisher wäre Welt 2 nur *größer* gewesen. Jetzt ist sie ein **Statuswechsel** — man verlässt das Amt und meldet ein Gewerbe an. Das ist kein Zahlensprung, das ist ein anderes Leben.

**Wichtig für den Ton:** Das Amt ist nicht der Feind. Die Sachbearbeiter sind selbst überlastete Menschen, die Wartenden keine Karikaturen. Der Humor zielt auf das *System* — auf Formulare in dreifacher Ausfertigung, auf Wartenummern, auf den Kopierer, der immer klemmt. Nie auf die Leute darin (Guardrail D2).

---

## 3. Die Leiter

Fünf Sprossen. **Gebaut werden die ersten beiden**, die Architektur trägt den Rest ohne Codeänderung.

| # | Welt | Was du tust | Stimmung |
|---|---|---|---|
| 1 | **Amt für Grundsicherung** | Du hilfst Wartenden mit ihrem Papierkram, gegen kleine Gegenleistungen | Neonröhre, Resopal, Nummernanzeige, Gummibaum |
| 2 | **Die Bude** | Eigenes Gewerbe: kleine IT-Aufträge aus der Nachbarschaft | Küchentisch, alter Laptop, Kabelsalat, Pizzakarton |
| 3 | *Büro über dem Imbiss* | Erste Angestellte, erste echte Kunden | zwei Schreibtische, Dönerduft durchs Fenster |
| 4 | *Das Startup* | Mehrere Teams, richtige Projekte | Großraum, Kaffeevollautomat, Whiteboards |
| 5 | *Der Glaspalast* | Konzern | Glas, Beton, Empfangstresen |

**Der Übergang von 1 auf 2 ist der wichtigste Moment des ganzen Spiels.** Er heißt **„Gewerbe anmelden"** — und ausgerechnet dafür braucht man ein Formular. Der letzte Antrag im Amt ist der, mit dem man es verlässt. Diese Pointe trägt das ganze Konzept.

---

## 4. Das zentrale Designprinzip: Der Engpass ist der Kompass

Die drei Kernstationen bilden in **jeder** Welt dieselbe Kette — nur die Bedeutung wechselt:

```
 ANNAHME  ──►  PUFFER  ──►  BEARBEITUNG
```

| Welt | Annahme | Puffer | Bearbeitung |
|---|---|---|---|
| **1 — Amt** | Wartende sprechen dich an | Dein Stapel offener Fälle | Du füllst aus, sie zahlen dir was |
| **2 — Bude** | Aufträge kommen rein | Deine To-do-Liste | Du reparierst, du stellst Rechnung |

Zu jedem Zeitpunkt bremst genau ein Glied — und das ist **ohne ein Wort Text sichtbar**:

| Engpass | Was man sieht | Was man intuitiv tut |
|---|---|---|
| Annahme zu langsam | Kaum jemand kommt bei dir an | Sichtbarer werden, ansprechbarer sein |
| Puffer zu klein | Zettel stapeln sich, der Überblick geht verloren | Ordnung schaffen, Ablage aufrüsten |
| Bearbeitung zu langsam | Die Schlange wächst, Leute tippen auf die Uhr | Schneller arbeiten, Hilfe holen |

**Beim Amt ist der Engpass nicht nur ein Signal — er ist die Pointe.** Eine wachsende Warteschlange versteht in Deutschland jeder ohne Erklärung.

*Auf dem Gerät nachgewiesen:* Annahme auf Stufe 15 ausgebaut → Engpass wandert auf den Puffer → Schlange wächst auf 13 Wartende → Einkommen bleibt unverändert. Der Spieler sieht, dass er an der falschen Stelle investiert hat, ohne dass es ihm jemand sagt.

---

## 5. Core Loop

```
      ┌──────────────────────────────────────────────────┐
      │                                                  │
      ▼                                                  │
  BEOBACHTEN ──► ENGPASS ERKENNEN ──► INVESTIEREN ──► SICHTBARE
                  (Schlange/Stapel)     (Upgrade)      VERBESSERUNG
                                                          │
                                                          ▼
                                      NEUER ENGPASS ◄── MEHR EINKOMMEN
                                            │
                                            ▼
                            MEILENSTEIN ──► FREISCHALTUNG ──► NEUES ZIEL
```

**Zykluslängen:** Mikro 20–60 s · Meso 8–15 min · Makro (Welt) 6–12 Stunden

---

## 6. Stationen

Fünf insgesamt, **zum Start nur drei sichtbar**. Fünf konkurrierende Systeme in Minute 1 überfordern auf einem 6"-Display; jede weitere Station ist eine Belohnung.

| # | Neutrale ID | Welt 1 | Welt 2 | Frei ab |
|---|---|---|---|---|
| 1 | `station_intake` | **Der Wartebereich** — wer dich anspricht | **Der Posteingang** | Start |
| 2 | `station_buffer` | **Deine Mappe** — offene Fälle | **Die To-do-Liste** | Start |
| 3 | `station_processing` | **Der Klapptisch** — wo du ausfüllst | **Der Schreibtisch** | Start |
| 4 | `station_transport` | **Der Kumpel** — bringt dir Leute | **Das Ticketsystem** | ~Min. 12 |
| 5 | `station_special` | **Der Beamte** — schiebt dir Fälle zu | **Der Firmenkunde** | ~Min. 25 |

**Vor Station 4 trägst du alles selbst** — durch Antippen. Absicht: Erst wenn das Tippen als lästig empfunden wurde, fühlt sich die erste Automatisierung wie Befreiung an. **Automatisierung muss verdient sein, sonst ist sie wertlos.**

### Upgrade-Achsen mit Charakter

Upgrades sind keine abstrakten „+10 %", sondern Gegenstände mit eigener Geschichte:

**Welt 1:** ein zweiter Kugelschreiber, der wirklich schreibt · eine Klarsichthülle · ein eigener Klapphocker statt Stehen · ein Ordner mit Register · ein Taschenrechner · eine Thermoskanne (du hältst länger durch) · ein Klemmbrett (plötzlich wirkst du offiziell)

**Welt 2:** mehr RAM · eine zweite Festplatte · ein Bürostuhl statt Küchenstuhl · ein zweiter Monitor · schnelleres Internet · eine Kaffeemaschine · ein Werkzeugkoffer

Diese Konkretheit ist der halbe Charme. „Klemmbrett gekauft — du wirkst jetzt offiziell" ist ein besseres Upgrade als „Annahmegeschwindigkeit +12 %".

---

## 7. Wirtschaftsformeln

Werte in `data/balance/*.json`, ohne Codeänderung anpassbar (ADR-005).

### 7.1 Upgrade-Kosten — exponentiell
```
kosten(n) = basis_kosten × wachstum^(n-1)      wachstum = 1,15
```

### 7.2 Ertrag — linear plus Meilensteine
```
ertrag(n) = basis × n × multiplikator × meilenstein_faktor^(n ÷ intervall)
```
`intervall` = **12** · `faktor` = **1,7**

**Warum Meilensteine unverzichtbar sind:** Ein rein linearer Ertrag kommt gegen exponentielle Kosten nicht an. Der Balance-Simulator hat es vorgerechnet: Ohne sie kostet Stufe 100 **sieben Tage Wartezeit**, das Spiel wäre nach ~40 Stufen tot.

Im Spiel heißen die Meilensteine **„Routine"**: Alle 12 Stufen wird eine Tätigkeit zur Gewohnheit und geht spürbar schneller von der Hand. Das ist auch erzählerisch richtig — man wird wirklich besser in dem, was man oft tut.

### 7.3 Durchsatz
```
effektiver_durchsatz = min(annahme, puffer, bearbeitung) × transport_faktor
```
Das `min()` **ist** der Engpass aus §4 — mathematisch und visuell dasselbe.

### 7.4 Offline-Ertrag
```
ertrag = durchsatz × min(abwesend, obergrenze) × rate       rate = 0,5
```
Obergrenze **4 Stunden**, per Upgrade auf 12 erweiterbar.

Der Bericht beim Öffnen ist ein **Geschenk**, nie eine Mahnung: „In deiner Abwesenheit sind 47 Fälle durchgegangen." Niemals „du hast X verpasst".

### 7.5 Zielkurve (am Simulator kalibriert, Regressionsschutz in `validate.ps1`)

| Zeit | Verdient | Stufen | Einkommen/s | Was passiert |
|---|---|---|---|---|
| 0:30 | 30 | 4 | 1,1 | Der erste Fünfer |
| 2:00 | 150 | 7 | 2,2 | Es spricht sich herum |
| 5:00 | 930 | 20 | 7,0 | Deine Mappe quillt über |
| 12:00 | 10.000 | 61 | 37 | **Der Kumpel hilft** — erste Automatisierung |
| 25:00 | 73.000 | 102 | 108 | **Der Beamte schiebt dir Fälle zu** |
| 40:00 | 243.000 | 127 | 226 | Dein Platz sieht aus wie ein Arbeitsplatz |
| 60:00 | 557.000 | 145 | 409 | **Gewerbeanmeldung** rückt in Reichweite |

---

## 8. Der Großauftrag — Daily-Return-Anker

**Welt 1:** Alle paar Stunden kommt jemand mit einem Fall, der es in sich hat — der Rentner mit dem Schuhkarton voller Belege, die Familie mit fünf Anträgen auf einmal, der Beamte, der dir heimlich einen Stapel zuschiebt.

**Welt 2:** Ein Firmenkunde mit einem Projekt, das eine Woche Umsatz auf einmal bringt.

| Parameter | Wert | Begründung |
|---|---|---|
| Intervall | **4 Stunden** | Deckt sich mit der Offline-Obergrenze |
| Wartezeit | **unbegrenzt** | **Kein Verfall** — der Fall wartet, bis du kommst. Im Amt ist das sogar realistisch |
| Strafe bei Verpassen | **keine** | Ein Spiel, das bestraft, wenn man lebt, wird deinstalliert |
| Stapelung | max. **2** | Nach 12 Stunden warten zwei — Willkommensbonus ohne Farmbarkeit |
| Bonus | 1,5–2,5× | Groß genug, um ein Ereignis zu sein |
| Benachrichtigung | **opt-in, standardmäßig aus** | Erst nach dem dritten erfolgreichen Fall angeboten |

---

## 9. Die Figuren

Humor aus Wiedererkennung und Persönlichkeit, nie aus Herabwürdigung.

### Welt 1 — im Amt

| Archetyp | Verhalten | Effekt |
|---|---|---|
| **Der Rentner mit dem Schuhkarton** | Bringt Belege von 1997 mit, erzählt zu jedem eine Geschichte | Dauert ewig, zahlt aber gut und kommt wieder |
| **Die Alleinerziehende in Eile** | Kind an der Hand, Termin in 20 Minuten | Kurze Geduld, dankbar bei Tempo |
| **Der Erstantragsteller** | Weiß nicht, wo er anfangen soll, schämt sich etwas | Braucht Zuwendung, wird zum Stammgast |
| **Der Wutbürger** | „Ich will den Vorgesetzten sprechen" | Blockiert, senkt die Geduld der Umstehenden |
| **Die Studentin mit Frist** | Heute ist der letzte Tag | Zahlt Expresszuschlag |
| **Der freundliche Sachbearbeiter** | Sieht, was du tust, und drückt ein Auge zu | Löst den Großauftrag aus |

**Der freundliche Sachbearbeiter ist wichtig für den Ton.** Er ist der Beweis, dass das Spiel sich nicht über Behörden lustig macht, sondern über Bürokratie — und dass darin Menschen arbeiten, die es auch nicht leicht haben.

### Welt 2 — in der Bude

Der Kiosk-Besitzer mit dem WLAN-Problem · die Nachbarin mit dem vollen Laptop · der Kleinunternehmer, der eine Website braucht · der Bekannte, der „nur mal kurz" fragt und drei Stunden bleibt.

**Verbindliche Regeln:** Keine realen Behörden, Wappen, Dienstsiegel oder Formularnummern. Keine erkennbar minderjährigen Figuren als Kunden. Keine Herabwürdigung von Erwerbslosen — sie sind Menschen mit einem Anliegen, keine Pointe.

---

## 10. Spielerreise

| Zeitpunkt | Erlebnis | Was hält |
|---|---|---|
| **Minute 1** | Jemand neben dir versteht sein Formular nicht. Du hilfst. Fünf Euro | Belohnung vor jeder Erklärung |
| **Minute 5** | Es spricht sich herum, mehr Leute kommen | *Ich werde gebraucht* |
| **Minute 15** | Jemand hilft dir beim Sortieren | *Es läuft auch ohne mich* |
| **Minute 60** | Dein Eckchen sieht aus wie ein Arbeitsplatz | Stolz auf sichtbaren Besitz |
| **Tag 2** | Offline-Bericht plus wartender Fall | Rückkehr wird belohnt |
| **Tag 7** | **Gewerbeanmeldung** — du verlässt das Amt | Der stärkste Moment des Spiels |
| **Tag 30** | Die Bude läuft, Welt 3 wird sichtbar | Identifikation mit dem eigenen Ding |

**Warum jemand freiwillig eine Rewarded Ad ansieht:** Weil ihm 40 Sekunden vor dem nächsten Upgrade das Geld fehlt und genau dann **„Überstunden einlegen"** angeboten wird — auf seine Anfrage hin, nie ungefragt eingeblendet.

**Warum jemand kauft:** Um Wartezeit abzukürzen oder seinen Platz zu verschönern. Kein gekaufter Vorteil ist für Fortschritt notwendig.

---

## 11. Bewusst nicht gebaut

| Mechanik | Grund |
|---|---|
| Energie-/Ausdauer-System | Bestraft Spielen |
| Verfallende Timer mit Verlust | Erzeugt Angst statt Freude |
| Zwangs-Interstitials | Häufigste 1-Stern-Ursache im Genre |
| Lootboxen | Regulatorisches Risiko, Vertrauensverlust |
| Pay-to-win | Zerstört die Progressionskurve |
| PvP / Ranglisten | Macht ein entspanntes Spiel zu Stress |
| Ungefragte Push-Nachrichten | Schnellster Weg zur Deinstallation |
| Spott über Erwerbslose oder Beamte | Falscher Ton, reales Reputations- und Policy-Risiko |
| Reale Behördennamen und Wappen | Rechtlich geschützt, teils strafbewehrt |
