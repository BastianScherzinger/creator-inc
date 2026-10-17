# Creator Inc: Idle Tycoon

Ein Idle-Tycoon für Android: Du startest mit einem Handy im WG-Zimmer, nimmst die ersten
Clips auf und baust daraus Schritt für Schritt eine eigene Firma, über sechs Standorte von
der WG bis zum Portfolio. Räume kaufen, Ausbauten verbessern, Mitarbeiter einstellen,
Aufträge abholen. Das Geld läuft weiter, auch wenn das Spiel zu ist.

**Eigenes Übungsprojekt** von Bastian Scherzinger
([Webagentur Scherzinger](https://webagentur-scherzinger.com/projekte/creator-inc/)).
Kostenlos, ohne Werbung, ohne Käufe, ohne Konto. Der Spielstand bleibt auf dem Gerät.

## Download

Die fertige APK liegt unter **Releases** dieses Repositorys (`creator-inc.apk`, immer die neueste Fassung).
Auf dem Handy öffnen und die Installation aus dieser Quelle erlauben. Android 7.0 oder neuer
(64 und 32 Bit ARM).

## Technik

- **Godot 4.7**, GDScript, streng typisiert
- `project/core/` — Wirtschaft, Fortschritt, Speicherstand ohne Nodes (headless testbar)
- `project/game/` — alles Sichtbare, liest nur, was der Kern berechnet
- `project/data/` — alle Zahlen und Texte als JSON (Welten, Balance, Story)
- `art_source/scripts/` — Räume, Möbel und Figuren entstehen per Skript in Blender, die Klänge per Python-Synthese
- Mehr: `CLAUDE.md` (Regeln und Befehle), `docs/ARCHITECTURE.md`, `docs/PC_TEST.md`

## Bauen und testen

Voraussetzungen: Godot 4.7 (`godot_console` im PATH), Android-SDK und JDK für den Export
(`tools/check_env.ps1` prüft die Versionen).

```powershell
.\validate.ps1 -SkipBuild        # Schichten, Sperrwörter, Import, Unit- und Integrationstests, Balance
.\validate.ps1                   # dasselbe plus Android-Debug-Build
.\tools\release_apk.ps1          # Download-APK build\creatorinc.apk
bash tools/pc_test.sh --frisch   # Spiel am PC per Befehl bedienen (docs/PC_TEST.md)
```

## Lizenz

Code und eigene Assets: MIT (siehe `LICENSE`). Schriften Nunito und Bricolage Grotesque:
SIL Open Font License. Testframework gdUnit4: MIT. Das App-Symbol entstand mit einem
KI-Bildgenerator.

---

## English

*Creator Inc: Idle Tycoon* is a free Android idle tycoon game: grow a one-phone bedroom
channel into a company across six locations. It is a personal practice project by Bastian
Scherzinger, built with Godot 4.7 — no ads, no in-app purchases, no account, save data stays
on the device. Download the APK from **Releases**. Code is MIT-licensed (see `LICENSE`).
