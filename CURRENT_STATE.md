# CURRENT STATE

**Stand 2026-10-17 nachmittags — neue Lage:** Creator Inc ist jetzt **Bastians eigenes Übungsprojekt** (nicht mehr Florin/WVM-IT). Verteilung als **freier APK-Download** (GitHub Releases, Projektseite https://webagentur-scherzinger.com/projekte/creator-inc/), Quellcode offen (MIT, `LICENSE`, `README.md`). Keine Werbung: die ▶-Angebote sind reine Boni (`ads.json` stub, 1 s). Release-Paket `com.scherzinger.creatorinc`, Download-APK über Preset „Android APK“ + `tools/release_apk.ps1` (Debug-Keystore dieses PCs). Datenschutz-Link → `.../projekte/creator-inc/datenschutz/`. Öffentlicher Schnappschuss ohne Historie: `docs/release/OEFFENTLICH_PRUEFUNG.md` + `tools/oeffentlich_ausschluss.txt`. Google Play nur optional später über Bastians eigenes Konto; die Florin-Übergabe (`docs/release/UEBERGABE_FLORIN.md`, `ADMOB.md`) ist überholt.

**Stand 2026-10-17 früh (Nacht 16./17.10., Name „Creator Inc: Idle Tycoon“):** validate grün (648 Tests, 0 Waisen, Balance im Korridor, 6 Welten vollständig). Nicht gepusht (Bastians Vorgabe). Commits seit f354b66: aa54881 Welle 1c/1d (Fenster-Diät, Ortsblasen, Plakette öffnet Raum-Menü, 8 Szenen je Welt, Standortkarte), 2e01bef **Welle 2 im Idle-Bank-Tycoon-Stil** (Raum-Panel `game/ui/raum_panel.gd`, Auftragskarten + Auftragsbrett `auftragsbrett.gd`, Kopfleiste mit Rang-Stern, Unterleiste mit Boost-Mitte, Tagesgeschenk als Symbol am Rand, Kasse mit Geldstapel `game/world/kassenstapel.gd`, Mitarbeiter-Figuren mit Namensschild, Kunden, Offline-Karte ×2), e42a4bd/a28ef65 **Umbenennung** (Release-Paket `com.scherzinger.creatorinc`, Debug-Build bleibt `tech.wvmit.helloworld` zum Testen am Handy), 4e22549 QA aller Welten (`docs/neu/K7_DURCHSPIELEN.md`) + **Sparen auf den nächsten Raum** (`balance.sparen`), Store-Bilder vom Handy (`docs/release/store/handy_*.png`), Feature-Grafik, Play-Checkliste. Release-AAB mit Debug-Key: 78,9 MB, `tools/release_aab.ps1` endet sauber.

**Stand 2026-10-15 (Design-Overhaul integriert):** validate gruen (322 Tests, 0 Waisen, Balance im Korridor, 6 Welten vollstaendig). Plan: `docs/DESIGN_OVERHAUL_2026-10-15.md`. Sieben Commits (Kern, Stationen/Marker, HUD, Story/Moment, Optik, Welten-Texte, Doku) plus Handy-Fix; nicht gepusht. Alle UI-Experimente `aktiv=a` (`data/experimente.json`), B-Code noch nicht geloescht. Handy-Test I1: Shots `shots/handy/i1_*.png`; Moment-Vollbild und Crew-Karte noch nicht gesehen.

**Stand 2026-10-15 (I2, Welt-Optik + Lebendigkeit integriert):** validate gruen. Commits: Story-Bibel, UI-Politur, Symbole/Key-Art, Welt-Optik M1-M3, Lebendigkeit E (worlds.json mit himmel/glow/partikel/animation/emission_puls, `skala` je Kulisse), Integration-Fixes. Hud: Speicher als Kurzzeile (voll: eine Zeile mit Knopf), Tagesaufgabe als Chip einklappbar. `tools/serie.sh` setzt bei `--tiefe` automatisch `--moment aus`. `einrichtung_romans_buero.glb` geloescht. Nicht gepusht.

**Letzte Aktualisierung:** 2026-10-15 (Release-Nacht, Integration der Pakete A-F) -- Plan: `docs/RELEASE_PLAN_2026-10-14.md`

## Neu seit 2026-10-14 (Release 1.0.0 in Vorbereitung)

- **A:** Tippen trifft Raum/Station sauber (Strahl gegen Objekthoehe), Raum-Panel fuer jeden Raum inkl. Startzone, Richtungs-Chips am Bildrand.
- **B:** Stationsmenue mit Juice (Konfetti, Blitz, Haptik), Offline-Bericht mit Figur, Tagesgeschenk, Fortschrittsmarken in der Kopfleiste, Banner-Warteschlange.
- **C+D:** Kern (Tagesgeschenk, Marken, Bedingungstypen), Story neu (22 Nachrichten je Welt, Eroeffnungs-Chat, Offline-Saetze). Generator: `tools/story/` (LIESMICH dort).
- **E:** Figuren mit neuen Augen/Konturen, Portraets `assets/ui/portraits/<figur>_<neutral|jubelnd|geschockt>.png` (UiStil.avatar nimmt sie; Abschluss zeigt jubelnd).
- **F:** Release-Vorbereitung: Paketname `tech.wvmit.helloworld`, Version 1.0.0, `tools/release_aab.ps1`, Datenschutz/Store-Texte, neue Sounds (stern, fanfare, konfetti, geschenk, zaehlen, kauf, levelup).
- `.gitignore`: Gradle-Zwischenstaende von `project/android/build` ignoriert, `.gdignore` dort ist versioniert.
- Handy: neue App `tech.wvmit.helloworld` ist eine eigene App; die alte Debug-App `com.scherzinger.helloworld` (Bastians Spielstand) bleibt unangetastet.
- Stand validate: siehe letzte Commit-Nachricht (Integration).

---

**Letzte Aktualisierung:** 2026-09-17 (morgens) · Nachtschicht nach `docs/NACHT_PLAN.md`

---

## Wo das Projekt steht

**HELLO WORLD**: ein Idle-Tycoon über sechs Welten, erzählt von Figuren
(ADR-022, `docs/STORY.md`). Vom Handy auf dem Bücherstapel bis zum Portfolio
über der Stadt:

| # | ID | Welt | Figur | Simulator bis 100 % |
|---|---|---|---|---|
| 1 | `zimmer` | Die WG – Ziel: der erste Gaming-PC | Mo | 81:20 |
| 2 | `auftrag` | Das Studio (Hinterhof-Garage) | Younes | 62:06 |
| 3 | `webseiten` | Der Merch-Laden | Roman | 64:19 |
| 4 | `buero` | Das Lager (mehrere Shops) | Roman | 61:58 |
| 5 | `produkt` | Die Farm (Rechenfarm) | Selin | 66:49 |
| 6 | `kapital` | Das Portfolio (Missionen: Aktien, Immobilien, Schmuck, Kunst) | Selin + alle | 69:31 |

**Alle sechs Welten haben die Tiefe von Welt 1:** Zonen-Karte mit fünf
kaufbaren Räumen, fünf Stationen mit je drei Ausstattungsplätzen und
sichtbaren Modellstufen, 25 Ziele, 15 Nachrichten, Tipp-Momente und
Abschluss bei 100 %. Die Durchspielprobe `--durchspielen --alle-welten` läuft
ohne Absturz bis zum Abspann.

## Neu seit 2026-09-11

- **Story neu** (ADR-022): Mo, Younes, Roman, Selin; Mira und Tobi bleiben in
  der WG. Der Faden um den Kommentar ist entfallen. Die Texte stehen in allen
  sechs `theme.json`.
- **Design-System „Sticker-Pop“** (`game/ui/ui_stil.gd`, `sticker_box.gd`):
  Tintenkontur, harter Schatten, Papiergrund, Bricolage Grotesque (SIL OFL),
  Akzentfarbe je Welt aus `theme.json` → `stil`. Das Handy ist ein Chat mit
  Figurenfarben (`absender_farben`). Eröffnung und Weltwechsel sind Plakate.
- **Engine:** Wand- und Bodenmodule je Welt (`worlds.json` → `module`),
  Einrichtungs-Varianten aus Daten, Licht je Welt (`licht_vorlagen`),
  Fluss-Teil je Welt, mehrere Darsteller, gemeinsame Figuren
  (`assets/characters/gemeinsam/`). Dazu die neuen Zieltypen
  `ausstattung_station`, `freigeschaltet` und `alle` (Missionen).
  Die Sondermechaniken blockieren den Abschluss nicht mehr
  (Einzelheiten: `NACHT_PLAN.md` → Engine-Notizen).
- **Werkzeuge:** `tools/welt_sim.gd -- <welt>` (einzelne Welt mit Zeitpunkten
  der Ziele und Nachrichten), Schalter `--alle-welten`, `--bild <name>`.
- **Assets:** Figuren-Crew (8), Karten, Stationen und Symbole der Welten 2–6.
  Die Skripte liegen in `art_source/scripts/*_neu.py`,
  `build_einrichtung_<welt>.py`, `build_stationen_<welt>.py` und
  `build_figuren_crew.py`.

## Zahlen

| Größe | Wert |
|---|---|
| Tests | 232, grün |
| `validate.ps1` | grün (7/7) |
| APK Debug | 47,5 MB |
| Welten in Tiefe | 6 |
| Durchspielprobe alle Welten (jeder Moment angetippt) | 313 min bis zum Abspann |

## Offen

Siehe `NEXT_SESSION.md`.
