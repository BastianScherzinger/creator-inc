# NAME — Neuer Titel für das Spiel (Arbeitsname „HELLO WORLD“ entfällt)

Stand: 2026-10-16. Recherche per Websuche; Marken- und Store-Prüfung sind **nicht abschließend** (siehe „Grenzen“).

## 1. Erkenntnisse zu Namen und Store-Optimierung

- Play-Titel: max. 30 Zeichen (seit 29.09.2021), Kurzbeschreibung max. 80. Titel-Wörter zählen bei Google Play am stärksten für das Ranking; Keyword-Stopfen, Emojis, „best/#1“ und Handlungsaufforderungen sind verboten bzw. schaden der Conversion (AppRadar, Gummicube, AppTweak).
- Es gibt auf Google Play keinen Untertitel; seine Rolle übernimmt die Kurzbeschreibung. Der Untertitel unten gilt für den App Store (falls später iOS) und als Grafik-Slogan.
- Übliche Muster erfolgreicher Idle-Tycoons: „Idle <Thema> Tycoon“ (Idle Billionaire Tycoon, Idle Shop Manager), „<Marke>: Idle Tycoon“ (Storage Empire-Idle Tycoon, Startup Empire - Idle Tycoon, Video Game Tycoon: Idle Empire), „Idle <Thema> Empire“. Das Schema „Eigenname + Doppelpunkt + Genre-Schlagwort“ trägt die Auffindbarkeit (idle, tycoon) und lässt Platz für eine eigene Marke.
- Quellen: apptweak.com/en/aso-blog/how-to-shorten-your-app-name-on-the-play-store, gummicube.com/how-aso-works-google, appradar.com/academy/app-title, Beispielseiten auf apps.apple.com (Idle Billionaire Tycoon id1609172151, Startup Empire - Idle Tycoon id1615068325, Idle Game Tycoon id1536591912).

## 2. Kandidaten und Kollisionsprüfung

Ergebnis „keine Treffer“ heißt nur: Die Websuche fand nichts. Direkter Play-Store-Suchlauf war nicht möglich.

| # | Titel | Zeichen | Befund |
|---|---|---|---|
| 1 | Creator Inc: Idle Tycoon | 24 | Kein gleichnamiger Titel gefunden. Ähnlich: „Idle Streamer! Film Maker Game“, „Video Game Tycoon: Idle Empire“ (anderer Name). |
| 2 | Gründerzimmer: Idle Tycoon | 26 | Kein Treffer. Umlaut im Titel; international schwer sprechbar. |
| 3 | Vom Zimmer zum Konzern | 22 | Kein Treffer. Nur Deutsch, kein Genre-Schlagwort im Titel. |
| 4 | Idle Startup Empire | 19 | **Kollision/Nähe:** „Startup Empire - Idle Tycoon“ (App Store, IT-Startup), „Idle Startup Tycoon“ (Browserspiel). Zu nah, verworfen. |
| 5 | Zimmerfirma: Idle Tycoon | 24 | Kein Treffer; „Zimmerfirma“ liest sich wie Zimmerei/Handwerk. Missverständlich. |
| 6 | Startup Stube: Idle Tycoon | 26 | **Kollision:** „startupstube“ ist das Gründerzentrum der FH Vorarlberg (Österreich, gleiches Land wie das Konto). Verworfen. |
| 7 | Firmenaufbau: Idle Tycoon | 25 | Kein Treffer; reiner Gattungsbegriff, kaum schutzfähig, nüchtern. |
| 8 | WG Imperium: Idle Tycoon | 24 | Kein Treffer. „WG“ nur im deutschen Raum verständlich, „Imperium“ passt nur halb zu einem kleinen Geschäft. |
| 9 | Mein Imperium: Idle Tycoon | 26 | Kein Treffer, aber sehr generisch („Imperium“-Titel zahlreich: Giga Industry Empire, Empire Clicker). |
| 10 | Idle Creator Empire | 19 | Kein exakter Treffer; viele „Idle … Empire“-Titel in der Nähe. Austauschbar. |
| 11 | Firma ganz groß: Idle Tycoon | 28 | Kein Treffer. Lang, schlecht sprechbar auf Englisch. |
| 12 | Zimmer Tycoon: Idle Firma | 25 | Kein Treffer; mischt Deutsch und Englisch ungeschickt. |

Grenzen: EUIPO (euipo.europa.eu/eSearch) und DPMA (register.dpma.de) sind dynamische Suchmasken, per Websuche nicht abfragbar. **Vor Veröffentlichung** „Creator Inc“ dort in Klasse 9 (Software), 41 (Spiele) prüfen; Play-Store-Direktsuche nach dem Titel in DE und EN von Hand machen. „Inc“ ist ein Gattungsanhang, die Unterscheidungskraft liegt in „Creator“; beschreibend für Content-Creator-Themen, deshalb nur geringer Markenschutz zu erwarten (rechtlich unkritisch, aber schwer exklusiv zu halten).

## 3. Favoriten

1. **Creator Inc: Idle Tycoon** — Empfehlung.
2. **Gründerzimmer: Idle Tycoon** — deutscher Charme, sagt „Gründen aus dem Zimmer“ sofort.
3. **Vom Zimmer zum Konzern** — erzählt den Bogen am besten, aber ohne „Idle/Tycoon“ im Titel.

### Begründung der Empfehlung

- „Idle Tycoon“ im Titel nennt Genre und Suchbegriffe; der Doppelpunkt-Aufbau ist im Store üblich.
- „Creator“ greift Spielstart (junger Creator) und Figuren auf, „Inc“ sagt „Firma“ und wird in DE und EN gleich verstanden. Keine Droge, kein Glücksspiel, keine Marke, keine Person.
- Gleich auf Deutsch und Englisch, kein Umlaut, später keine Umbenennung für die englische Fassung nötig.
- Der Wachstumsgedanke (Zimmer → Zentrale) steht in Kurzbeschreibung und Untertitel, nicht im Titel; so bleibt der Titel auch über Welt 6 hinaus passend.
- Schwäche: „Creator“ engt auf Content-Themen ein, obwohl später Merch, Lager, Rechenzentrum folgen. Wer das vermeiden will: Favorit 2.

## 4. Metadaten zur Empfehlung

- **Titel:** Creator Inc: Idle Tycoon (24)
- **Paketname:** `com.scherzinger.creatorinc` (nur Kleinbuchstaben). Achtung: Bisher `tech.wvmit.helloworld`. Der Paketname ist nach Veröffentlichung unveränderlich; Umstellung berührt `export_presets.cfg`, Handy-Reset-Befehl in CLAUDE.md und `docs/release/UEBERGABE_FLORIN.md`.
  - Für Favorit 2: `tech.wvmit.gruenderzimmer`.
- **Kurzbeschreibung DE (≤ 80):** „Vom WG-Zimmer zur eigenen Firma: Idle-Tycoon zum Aufbauen und Ausbauen.“ (73 Zeichen)
- **Kurzbeschreibung EN (≤ 80):** „Build your own business from a tiny room: the idle tycoon that grows with you.“ (79 Zeichen)
- **Untertitel (App Store, 30, bzw. Grafik-Slogan):** „Bau deine eigene Firma auf“ (25)
- **5 Schlüsselwörter** (für Beschreibung und Kurztext): Idle, Tycoon, Firma aufbauen, Unternehmen, Business-Simulation
  (weitere für die Langbeschreibung: Imperium, Startup, Manager, Offline-Verdienst)
- **Icon-Text:** Möglichst keiner; Icon als Bild (Kapuzenfigur oder Laptop im Zimmer). Falls Schrift: nur „CI“ als Monogramm, mindestens 40 % der Iconhöhe, auf Handy-Größe 48 dp prüfen.

## 5. Offene Punkte

- Vor Verfestigung: Play-Store-Suche von Hand (DE/EN), EUIPO/DPMA-Recherche (siehe oben).
- Ordnername „cannabisgame“ ist nicht Teil dieses Auftrags und wurde nicht angefasst; Umbenennung erst nach Entscheidung, da Pfade in Skripten und Memory stehen.
