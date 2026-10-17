# NEXT SESSION

**Für den nächsten Claude-Code-Lauf. Zuerst lesen, dann handeln.**

---

## Stand 2026-10-17 nachmittags (zuerst lesen)

- **Stand 2026-10-17 nachmittags — neue Lage:** Creator Inc ist jetzt **Bastians eigenes Übungsprojekt** (nicht mehr Florin/WVM-IT). Verteilung als **freier APK-Download** (GitHub Releases, Projektseite https://webagentur-scherzinger.com/projekte/creator-inc/), Quellcode offen (MIT, `LICENSE`, `README.md`). Keine Werbung: die ▶-Angebote sind reine Boni (`ads.json` stub, 1 s). Release-Paket `com.scherzinger.creatorinc`, Download-APK über Preset „Android APK“ + `tools/release_apk.ps1` (Debug-Keystore dieses PCs). Datenschutz-Link → `.../projekte/creator-inc/datenschutz/`. Öffentlicher Schnappschuss ohne Historie: `docs/release/OEFFENTLICH_PRUEFUNG.md` + `tools/oeffentlich_ausschluss.txt`. Google Play nur optional später über Bastians eigenes Konto; die Florin-Übergabe (`docs/release/UEBERGABE_FLORIN.md`, `ADMOB.md`) ist überholt.
- Die Florin-Punkte unten (Upload-Key, wvm-it.tech-Datenschutz, Play-Konto) entfallen.

## Stand 2026-10-17 früh (zuerst lesen)

- Spiel heißt jetzt **Creator Inc: Idle Tycoon**. Was in der Nacht passiert ist: `CURRENT_STATE.md` oben, Befunde `docs/neu/K7_DURCHSPIELEN.md`, Release `docs/release/PLAY_CHECKLISTE.md`.
- **Bastian:** am Handy spielen (App heißt dort „Creator Inc“, Paket noch `tech.wvmit.helloworld`), Urteil abgeben; Preis-/Boost-Fragen offen (Boost-A/B erst ab Rang 3 prüfbar).
- **Florin:** Upload-Key, Datenschutzerklärung unter `https://wvm-it.tech/creatorinc/datenschutz` veröffentlichen (oder Adresse in `project/data/services/rechtliches.json` ändern), Play-Konto, 12 Tester × 14 Tage, Formulare.
- **Offen (KI):** Entscheidungen aus K7 §3/§4 (Szenen bei Raumkäufen W5/W6, Fortschritt-/Ziele-Knopf neben Auftragsbrett, „Los geht's“ bei Moment-Aufträgen), Umschlag auf der Kasse nach Auftrag, Gelände W4–W6 beim größten Zoom, `bundletool validate`.
- Werkzeuge: `bash tools/pc_test.sh --frisch` + `tools/pc_cmd.sh "spiele 60"|bericht|bild` (Autospieler), `bash tools/store_handy.sh <name> <s> [schalter]` (Store-Bild vom Handy).

---

## Stand 2026-10-15 nachts (I2)

- Welt-Optik + Lebendigkeit committet, validate gruen, nicht gepusht. Offen: (1) im Startbild sind Fahrzeuge/Strassen meist ausserhalb des Ausschnitts (W1 Auto, W2 Kastenwagen, W4 LKW, W6 Wolken nicht sichtbar) -> Kamera-Ausschnitt oder Kulissen naeher an die Stationskette; (2) W4 hat keinen Stapler/Foerderband als eigene Kulisse (Foerdern wirkt nur mit Texturen); (3) Hud im Zustand "Speicher voll" noch ~22 % Bildhoehe, normal ~17 %; (4) Handy: Moment-Popups bei `--tiefe` verdecken die Welt (Handy hat kein `--moment aus`); (5) Partikel-Positionen in W2-W6 geschaetzt, nachjustieren.

---


## Stand 2026-10-15 nachts (I1)

- Overhaul integriert und committet, validate gruen, nicht gepusht. B-Code der A/B-Experimente noch loeschen (alle A).
- Handy-Befunde offen: (1) Tutorial-Karte bleibt ueber jedem Sheet sichtbar und frisst Welt-Platz; (2) Sheet deckt ~60-70 % statt 56 %; (3) Tutorial-Ring bleibt auf dem ausgegrauten Ausbauen-Knopf; (4) Eroeffnung: Deko-Icon scheint hinter Chat-Blase; (5) Vollbild-Moment und Crew-Karte per Handy noch ungeprueft (Ziele loesen nur Muenzflug +Zahl aus).

---

## Stand 2026-10-15 (zuerst lesen)

- Pakete A-F integriert (siehe `CURRENT_STATE.md`). Nicht gepusht.
- **Florin muss:** Play-Konto/Upload-Key/Datenschutz-URL/Store-Eintrag nach `docs/release/UEBERGABE_FLORIN.md`; Bastian baut das Bundle mit `.	ools
elease_aab.ps1 -Keystore ... -Alias ...`.
- **Offen:** Handy-Test der neuen App `tech.wvmit.helloworld` (FPS, Tipp-Log je Tipp genau eine `tipp:`-Zeile), `store.json` fuellen (Laden-Knopf im Release), Werbe-IDs (`ads.json`, aktuell Stub), Kauf-/Level-Sounds (`sfx_kauf`, `sfx_levelup`) noch nicht in `sounds.json` verdrahtet.

---

## Startbefehl

```
Lies CLAUDE.md, CURRENT_STATE.md und docs/NACHT_PLAN.md (Taskliste, Engine-Notizen)
sowie docs/nacht/review_welten_1_4.md und review_welten_5_6.md. Alle sechs Welten sind in Tiefe spielbar.
Weiter mit dem Feedback des Nutzers vom Handy und den offenen Punkten unten.
```

---

## Ausgangslage (2026-09-17, Nachtschicht)

Der Nutzer wollte (zusammengefasst):
- **Welt 1 fertig**, vom Start über das Design bis zu sauber antippbaren Stellen
- **Neues Design-System**: frisch, eigenständig, nicht überdesignt, bedienbar wie ein Idle-Game
- **Story mit Figuren**, ohne Textwände:
  - Mo: der erste Gaming-PC
  - Younes: starke Videos
  - Roman: Merch-Shop, dann mehrere Versand-Shops
  - Selin: Krypto-Farm, dann Millionen anlegen
  - dazu Missionen: alle Aktien, Immobilien, Schmuck
- **Jede Welt als ganzes Level**, komplett fertig und hochwertig
- **Arbeitsweise:** mit Agenten, genauer Planung und Abhaken

Umgesetzt wurde das nach `docs/NACHT_PLAN.md` (ADR-022).
Zwischen etwa 02:30 und 07:00 Uhr stand die Arbeit still, weil das Wochenlimit
der API erreicht war.

## Wissensstand in Kürze

- **Was fertig ist:** alle sechs Welten in Tiefe mit Karten, Stationen,
  Ausstattung, Räumen, Zielen, Chats und Abschluss. Dazu das Design-System
  Sticker-Pop und die Figuren-Crew. `validate.ps1` ist grün (232 Tests,
  APK 47,6 MB), die Durchspielprobe läuft bis zum Abspann. Letzter Commit:
  „Welt 6: Missionen-Streifen …“ plus Übergabe.
- **Wo was steht:**
  - Bogen, Karten, Design-Tokens, Taskliste und Engine-Notizen: `docs/NACHT_PLAN.md`
  - Karten, Ausstattung, IDs und die beiden Reviews je Welt: `docs/nacht/`
  - Texte: `docs/STORY.md` (Quelle) und `data/themes/<welt>/theme.json` (im Spiel)
  - Entscheidung: ADR-022
- **So arbeitet das Team** (hat sich bewährt):
  - Eine Leitung plus Agenten mit getrennten Schreibrechten: Engine
    (`core/`, `game/` ohne `ui/`, `worlds.json`, Balance), UI (`game/ui/`,
    Symbole, i18n), je Welt ein Blender-Agent für die Karte und einer für die
    Stationen, ein Text-Agent für die Themen.
  - Danach ein Reviewer auf eine Bilderserie. Leitung prüft jedes Ergebnis per
    Vorschaubild, `validate.ps1` erst, wenn niemand mehr schreibt.
  - Die Prompt-Vorlagen stehen sinngemäß in `NACHT_PLAN.md` §5/§6.
- **Blender-Skripte je Welt:** `art_source/scripts/build_room_<welt>_neu.py`,
  `build_einrichtung_<welt>.py`, `build_stationen_<welt>.py` (Welt 6:
  `build_stationen_kapital_neu.py`), `build_figuren_crew.py`,
  `build_symbole_sticker.py`. Vorschauen liegen unter
  `art_source/vorschau/<welt>/` (nicht im Git).

## Offen

1. **Der Nutzer spielt jetzt auf dem Handy.** Am 17.09. um ~09:10 wurde die neue
   Fassung installiert und der Spielstand gelöscht; er beginnt frisch in Welt 1.
   **Sein Feedback hat Vorrang vor allem anderen.** Die FPS der Welten 2–6 auf
   dem Gerät sind noch nicht gemessen.
2. **Noch offene Review-Befunde** (beide Reviews in `docs/nacht/`, Umgesetztes steht in den Commits vom 17.09.):
   - **Welt 6:** Missionen-Streifen und Bereichssymbole sind erledigt. Offen: Goldrand und Mission-Chip in der Zielliste mit einem echten Stand prüfen. Die anderen Welten könnten ebenfalls Bereichssymbole bekommen (`bereiche.<id>.symbol`).
   - **Abspann:** Die Dachterrasse mit allen vier Figuren sollte als Bild bzw. Szene erscheinen, nicht nur als Text.
   - **Preisschilder gesperrter Räume** schweben, ohne dass der Raum zu sehen ist.
   - **Modelle ragen über ihre Stationsfläche hinaus:** Welt 2 Dreh-Set, Welt 3 Drucktisch. Das ist in den Blender-Skripten zu beheben.
   - **Welt 4:** Die cyanfarbenen Parkplätze in `umgebung.glb` sind zu grell.
3. **Welt 3** reagiert sehr stark auf das Wachstum der Grundeinnahme
   (1,13 → 65 min, 1,10 → 127 min). Mit echten Spielern nachmessen.
4. **Glas und Alpha** in Welt 4 und 6: Sortierung und Sperrschleier auf dem
   Gerät ansehen.
5. **Auf dem Gerät messen:** FPS in den Welten 2–6 (größere Karten, mehr
   Emission).
6. **Store:** neue Store-Bilder und `STORE_EINTRAG.md` passend zum neuen Bogen.
   Klären, ob der Titel HELLO WORLD bleibt (Entscheidung des Nutzers).
7. **Play-Richtlinie:** Der Nachtrag steht in `docs/PLAY_COMPLIANCE_HELLOWORLD.md` §9. Offen ist, ob der Fragebogen zum simulierten Glücksspiel durch die Verlust-Ticks in Welt 6 berührt wird.
8. **Aufräumen:** alte `welt_*.glb` und `raum_*`-Einzelmöbel der Welten 2–6
   entfernen, sobald nichts mehr darauf verweist.
