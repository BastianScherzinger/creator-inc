# Öffentlich-Prüfung — Schnappschuss für das Repo `creator-inc`

Stand 17.10.2026 nachmittags. Gescannt: alle 3.812 getrackten Dateien (`git ls-files`),
Textdateien bis 3 MB (Bilder, Modelle, Klänge, `.import`, `.so`, `.jar` übersprungen).
Ausschlussliste zum Kopieren: `tools/oeffentlich_ausschluss.txt`. Nichts wurde gelöscht.

Der öffentliche Stand wird **ohne alte Git-Historie** veröffentlicht (frischer Schnappschuss);
in der Historie stehen u. a. frühere Themen und interne Commits.

## Ergebnis je Prüfpunkt

| Prüfpunkt | Treffer | Bewertung |
|---|---|---|
| Telefonnummern | 0 | – |
| E-Mail-Adressen | `OPEN_QUESTIONS.md`, `docs/DUNS_ANTRAG.md` (je die Geschäftsadresse …05@gmail.com) | Adresse steht ohnehin im Impressum der Agenturseite; beide Dateien trotzdem ausgeschlossen (intern). Der Commit-Autor im Schnappschuss trägt dieselbe Adresse. |
| Wohnanschrift | `docs/DUNS_ANTRAG.md` | **ausschließen** |
| Jobcenter/Grundsicherung | `MASTER_DECISIONS.md`, `docs/GAME_DESIGN.md`, `data/themes/amt/theme.json` | nur Spielthema („Amt für Grundsicherung“, frei erfunden) — unbedenklich |
| Provision | 0 | – |
| Schlüssel/Token/Passwörter | `docs/ANDROID.md` (Platzhalter `<...>`), `project/android/build/config.gradle` (Godot-Standard „android“ des Debug-Keystores) | unbedenklich, kein echter Schlüssel. Keystores sind per `.gitignore` ausgeschlossen. |
| Florin / WVM-IT | 29 Dateien, davon echte Treffer in Release-/AdMob-Doku | interne Release-Doku ausschließen (Liste); „Feier“ in Spielcode/Themen ist das deutsche Wort (Abschlussfeier) |
| Dateien > 20 MB | 0 | – |
| Sperrwörter in Dateinamen | 0 | – |
| Sperrwörter in Inhalten | Doku des früheren Themas (`MASTER_DECISIONS.md`, `MASTER_PLAN.md`, `MASTER_PROMPT_V2.md`, `docs/RESEARCH_SUMMARY.md`, `docs/PLAY_COMPLIANCE.md`, `docs/ARCHITECTURE.md`, `docs/neu/K3_RECHERCHE_IDLE.md`, `docs/release/NAME.md`), `validate.ps1` (die Sperrwort-Prüfung selbst), `CLAUDE.md`/`tools/ab_montage.py` (Ordnername) | „grow“ in gdUnit4/UI-Code ist Godots `grow_horizontal` (Fehlalarm). Recherche-Dateien mit Drogenbegriffen ausschließen; Entscheidungsdoku (`MASTER_DECISIONS.md`, ADR-015 Themenwechsel) darf bleiben — sie erklärt den Wechsel sachlich. `validate.ps1` muss bleiben (Build/Tests). |

## Vorschlag

1. Schnappschuss = `git ls-files` minus `tools/oeffentlich_ausschluss.txt`.
2. Vor dem Push im Schnappschuss erneut scannen (Skript-Muster wie oben), dann `validate.ps1` dort laufen lassen.
3. Store-Bilder (`docs/release/store/`, 15,5 MB) dürfen bleiben — sie zeigen nur das Spiel.
4. Offen zur Entscheidung (Bastian): `MASTER_DECISIONS.md`/`MASTER_PLAN.md` erwähnen das frühere Thema; zum Ausblenden einfach in die Ausschlussliste aufnehmen (der Code hängt nicht daran).
