# HELLO WORLD

**Vom ersten Clip zum eigenen Konzern.**

Ein Idle-Tycoon über den Weg von einem geliehenen Laptop zur finanziellen
Unabhängigkeit — als Web-Entwickler. Kein Fantasiegeschäft, sondern der Beruf,
den es wirklich gibt, mit den Problemen, die es wirklich gibt.

---

## 1. Warum dieses Thema trägt

**Es gibt das Spiel noch nicht.** Es gibt Idle-Games über Bäckereien, Minen,
Krankenhäuser, Bauernhöfe. Es gibt „Programmier"-Klicker, die aus Witzen über
Kaffee und Semikolons bestehen. Es gibt keinen Idle-Tycoon, der die Arbeit
eines Entwicklers ernst nimmt und trotzdem Spaß macht.

**Die Zielgruppe findet sich wieder.** Jeder, der schon einmal eine Seite
deployed hat, kennt den Moment, in dem das Deployment endlich durchläuft. Jeder,
der Inhalte veröffentlicht hat, kennt den Unterschied zwischen 400 Aufrufen und
126.000. Diese Momente sind bereits emotional aufgeladen — das Spiel muss sie
nur einsammeln.

**Es ist werbefähig.** Anders als das erste Thema dieses Projekts (siehe
ADR-003) verstößt nichts hier gegen die Publisher-Beschränkungen von Google.
Keine Substanzen, kein Glücksspiel, keine Grauzone.

**Die Kette ist echt.** Der Ablauf einer Kundenwebseite ist real eine
Fließkette mit einem Engpass:

```
Anfrage → Konzept → Umsetzung → Deployment → Betreuung
```

Genau diese fünf Glieder bildet die Engine bereits ab (`Ids.CHAIN`). Das
Thema wurde nicht auf die Mechanik gebogen — die Mechanik war zufällig schon
richtig.

---

## 2. Der Bogen

Sechs Welten. Jede ist ein anderer Ort, eine andere Größenordnung und ein
anderes Gefühl. Die Mechanik bleibt dieselbe, die Bedeutung ändert sich.

| # | Welt | Ort | Womit man Geld macht | Erste Ausbaustufe kostet | Nach einer Stunde |
|---|------|-----|----------------------|--------------------------|--------------------|
| 1 | **Das Zimmer** | 14 m², Matratze, alter Laptop | Aufrufe auf Clips | 25 € | ~557 Tsd |
| 2 | **Der erste Auftrag** | dasselbe Zimmer, zweiter Monitor | ein bezahltes Skript | 250 € | ~5,6 Mio |
| 3 | **Die Webseiten** | Schreibtisch am Fenster | Kundenseiten | 2.500 € | ~56 Mio |
| 4 | **Das Büro** | echte Räume, andere Menschen | mehrere Projekte parallel | 25.000 € | ~557 Mio |
| 5 | **Das Produkt** | Loft, Bildschirme, Server | eigenes Produkt, Abos | 250.000 € | ~5,6 Mrd |
| 6 | **Der Ausstieg** | ein ruhiger Raum | Kapital arbeitet allein | 2,5 Mio € | ~16,7 Mrd |

**Jede Welt ist genau eine Größenordnung größer als die vorige** — Kosten *und*
Einnahmen mal zehn. Das Tempo bleibt dabei gleich: Würde nur das Einkommen
wachsen, wäre jede Welt zehnmal schneller durch als die vorige, und der Bogen
wäre eine Rutschbahn. Die Zahlen oben sind **gemessen**, nicht geschätzt
(`tools/balance_sim.gd` prüft jede Welt einzeln).

Welt 6 fällt aus der Zehnerreihe, und zwar absichtlich: Sie ist die einzige mit
einer echten Tempobremse und erreicht deshalb rund ein Drittel dessen, was die
reine Skalierung ergäbe. Der Ausstieg soll sich anders anfühlen als alles
davor — langsamer, mit mehr Platz zwischen den Ereignissen.

**Der Kern des Bogens:** In Welt 1 tauscht man Zeit gegen Geld. In Welt 6
arbeitet Geld ohne Zeit. Alles dazwischen ist der Übergang. Jede Welt nimmt
eine Fessel weg — und legt eine neue an, die größer ist.

---

## 3. Die drei Säulen

### Säule 1 — Der Engpass ist die Botschaft

Die Kette hat immer genau ein schwächstes Glied, es ist **sichtbar** (Stau,
Farbe, Warteschlange), und es zu beheben ist die einzige Handlung, die zählt.
Wer die Lieblingsstation ausbaut statt der roten, kommt nicht weiter.

Das ist nicht nur Spielmechanik. Es ist die Lektion aus dem VintedBot: nicht
„funktioniert es?", sondern „funktioniert es unter den Bedingungen, die
tatsächlich gelten?".

### Säule 2 — Fortschritt ist erzählt, nicht nur beziffert

Eine Zahl, die größer wird, ist kein Spiel. Jeder Ausbau hat einen Namen, der
etwas erzählt („zweiter Monitor", „Skript statt Handarbeit", „endlich ein
Stuhl mit Lehne"). Jeder Meilenstein hat einen Satz. Jeder Weltwechsel hat
eine Szene.

### Säule 3 — Ehrlichkeit als Stil

Das Spiel verkauft keinen Traum vom mühelosen Reichtum. Es zeigt, dass die
Idee weiter trägt als die Umsetzung, dass Testabdeckung fehlt, dass ein
Projekt an 1,5 GB Arbeitsspeicher scheitern kann. **Der Ton ist trocken,
nicht zynisch. Wer es geschafft hat, hat gearbeitet, nicht gewonnen.**

---

## 4. Was der Spieler tatsächlich tut

**Minute 1–2:** Ein Clip ist hochgeladen. Aufrufe ticken hoch. Man tippt auf
das Handy und baut es aus. Das erste Geld kommt.

**Minute 3–15:** Die Kette wird sichtbar. Idee → Aufnahme → Schnitt → Upload.
Irgendwo staut es sich. Man merkt: Es bringt nichts, mehr Ideen zu haben, wenn
der Schnitt nicht hinterherkommt.

**Minute 15–60:** Die erste Automatisierung. Clips gehen im Stapel raus. Dann
kommt **der Kommentar** — jemand fragt, ob man etwas bauen kann. Welt 2 öffnet.

**Stunde 2–10:** Kunden, Seiten, Deployment, SEO. Die Beträge wachsen um
Größenordnungen. Man stellt den ersten Menschen ein und merkt, dass Menschen
keine Stationen sind.

**Danach:** Produkt statt Auftrag. Abos statt Rechnungen. Und am Ende ein
Bildschirm, auf dem Zahlen laufen, während man nichts tut — was das ganze
Spiel über das Ziel war und sich am Ende seltsam leer anfühlen darf.

---

## 5. Vorlage: eine echte Biografie

Der Bogen folgt lose der Geschichte des Entwicklers dieses Spiels
(GitHub-Profil `BastianScherzinger`). Das ist kein Selbstporträt — die
Spielfigur ist namenlos und bleibt es. Aber die **Details** stammen aus der
Wirklichkeit, und das ist der Grund, warum sie funktionieren:

- Mit 11 bei Scratch angefangen, mit 16 nach dem Realschulabschluss bewusst
  wieder bei `hello world`
- TikTok von null: Projekte laufen besser als Tutorials — zwei Videos mit
  126.000 und 100.000 Aufrufen
- Der erste bezahlte Auftrag entstand **aus einem Kommentar unter einem Video**
- Dieser Auftrag scheiterte fast am Arbeitsspeicher: 1,5 GB für einen echten
  Browser, das Hosting-Paket gab 200 MB her. Browser raus, HTML direkt geparst.
- Eine Datei mit über tausend Zeilen wurde zur Sucherei — aufgeteilt nach
  Zuständigkeiten
- Sieben produktive Kundenseiten, eigene Produktseite mit 135 Stadtseiten
- Ein Bestellsystem, das nach der Übergabe dem Wirt gehört, nicht dem Erbauer

**Regel für alle Texte:** Kein Firmenname, kein Kundenname, keine Domain aus
der Wirklichkeit landet im Spiel. Die *Situationen* werden übernommen, die
*Namen* sind erfunden.

---

## 6. Name

**HELLO WORLD** — kurz, im Store aussprechbar, für die Zielgruppe sofort
lesbar, und es trägt den Bogen: Das Spiel beginnt mit den zwei Wörtern, mit
denen jeder anfängt, und endet bei einem Konzern.

Untertitel im Store: *Vom ersten Clip zum eigenen Konzern.*

Verworfene Kandidaten und warum:
- *Antrag auf Reichtum* — gehörte zum alten Behördenthema (ADR-015)
- *PUSH* — zu belegt, im Store nicht auffindbar
- *Zeile für Zeile* — schön, aber zu leise für eine Store-Kachel
- *Idle Dev Tycoon* — beschreibt das Genre statt das Spiel

---

## 7. Was dieses Dokument nicht ist

Es ist kein Ersatz für `GAME_DESIGN.md` (Mechanik und Zahlen), `STORY.md`
(Erzählung), `WELTEN.md` (Bauplan je Welt) oder `ARCHITECTURE.md`. Es hält
fest, **warum** dieses Spiel und nicht ein anderes.
