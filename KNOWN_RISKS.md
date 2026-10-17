# RISIKOMATRIX

**Stand:** 2026-09-10 · W = Wahrscheinlichkeit, A = Auswirkung (1 = gering, 5 = existenziell)

---

## Die drei Risiken, die dieses Projekt tatsächlich töten können

### ~~R-01~~ — Werbeeinnahmen brechen wegen des Themas weg ✅ ERLEDIGT 2026-09-10
**Durch den Themenwechsel vollständig entfallen** (ADR-015). Ein Bürgeramt löst keine Publisher Restriction aus; Google Ads schaltet normal, die Altersfreigabe fällt von 18+ auf voraussichtlich USK 6. Monetarisierung zurück auf Ads + IAP (ADR-016).

**Die Lehre, die bleibt:** Dass dieser Wechsel eine Datenänderung statt eines Neuanfangs war, ist ausschließlich ADR-010 (Theme-Schicht) zu verdanken. Die Guardrail bleibt in Kraft.

### R-02 — Asset-Produktion wird zum Flaschenhals 🔴 W4 · A5
Der klassische Tod von Ein-Personen-Spieleprojekten. Der Code ist in Wochen fertig, die Grafik nie.
- **Frühwarnsignal:** Eine Station braucht länger als **zwei Abende** vom Konzept bis ins Spiel.
- **Gegenmaßnahme:** 3D statt 2D (ADR-003) — ein Rig trägt alle Varianten. Blender-Python-Automatisierung. Modulbaukasten mit festem Rastermaß. Platzhaltergeometrie bis Phase 5, damit Spielmechanik nie auf Grafik wartet.
- **Notfallplan:** Radikale Stilvereinfachung (einfarbige Flächen, geometrische Grundformen) ist jederzeit möglich, wenn die Silhouetten-Regel von Anfang an eingehalten wurde.

### R-03 — Das Projekt schläft ein 🔴 W4 · A5
Bei einem mehrmonatigen Feierabendprojekt das statistisch wahrscheinlichste Ende — und das am seltensten eingeplante.
- **Frühwarnsignal:** Mehr als zwei Wochen ohne Commit.
- **Gegenmaßnahme:** Der First Playable ist bewusst klein geschnitten (Phase 4), damit früh etwas Spielbares existiert. Jede Task endet mit einem sichtbaren Ergebnis. `NEXT_SESSION.md` sorgt dafür, dass ein Wiedereinstieg nach Wochen keine Einarbeitung kostet.

---

## Technische Risiken

| ID | Risiko | W | A | Frühwarnsignal | Gegenmaßnahme |
|---|---|---|---|---|---|
| R-04 | Performance auf Low-End-Android | 3 | 4 | Bildrate unter 45 auf dem Testgerät. **Achtung:** Das Testgerät (Redmi Note 12 Pro 5G, 6 GB) ist stärker als unsere Untergrenze — gutes Gefühl dort beweist nichts für schwächere Geräte (ADR-017) | Budgets ab Phase 3 messen; Entwicklungsmaschine mit UHD 620 als eingebauter Wächter; NPC-Obergrenze und Pooling ab Beginn |
| R-05 | Save-Korruption bei Nutzern | 2 | 5 | Absturzberichte beim Start | Atomares Schreiben, Backup-Slot, Prüfsumme (ADR-006); Migrationen einzeln getestet; eingefrorene Fixtures pro Version |
| R-06 | Build-Pipeline bricht nach Werkzeug-Update | 3 | 2 | `validate.ps1` rot ohne Codeänderung | Werkzeugversionen in `CURRENT_STATE.md` festgehalten; keine automatischen Updates während einer Phase |
| R-07 | Ads-/IAP-Plugin verwaist | 3 | 3 | Kein Release des Plugins seit über 12 Monaten | Interface-Abstraktion (ADR-009) macht den Anbieterwechsel zu einer Datei; Alternativen vor Phase 8 prüfen |
| ~~R-08~~ | ~~Godot-Export-Vorlage unterstützt API 36 nicht~~ | — | — | — | ✅ **ENTKRÄFTET am 2026-09-10.** Gemessen am gebauten APK mit `apkanalyzer`: Godot 4.7.2 liefert von Haus aus `targetSdk 36` und `minSdk 24` — exakt die Vorgaben aus ADR-011, ohne Gradle-Build |
| R-09 | Qualität AI-generierten Codes | 3 | 3 | Tests grün, Verhalten trotzdem falsch | Headless-Core mit echten Zahlenprüfungen statt Attrappen-Tests; Balance-Simulator (TASK 012); jede sichtbare Änderung per Screenshot beurteilt |
| R-10 | Speicherplatz auf der Entwicklungsmaschine | 3 | 3 | Unter 15 GB frei | Kein Android Studio, kein Emulator; Build-Artefakte regelmäßig löschen; Auslagerung des SDK auf ein externes Laufwerk als Notfallplan |

---

## Produkt- und Marktrisiken

| ID | Risiko | W | A | Frühwarnsignal | Gegenmaßnahme |
|---|---|---|---|---|---|
| R-11 | Store-Ablehnung wegen des Themas | 1 | 5 | Ablehnung im ersten Review | Stark entschärft durch ADR-015. Verbleibend: keine realen Behörden, Wappen, Dienstsiegel oder Formulare nachbilden; App darf nicht amtlich wirken (`PLAY_COMPLIANCE.md` §2) |
| R-12 | Altersfreigabe schränkt ein | 1 | 2 | IARC-Ergebnis | Entfallen durch ADR-015 (voraussichtlich USK 6). Fragebogen dennoch wahrheitsgemäß ausfüllen — Falschangaben führen zur Entfernung |
| R-13 | Scope Creep | 4 | 3 | Neue Systeme vor Abschluss von Phase 5 | Roadmap ist bindend; neue Ideen wandern nach `docs/BACKLOG.md`, nicht in die laufende Phase |
| R-14 | Das Spiel macht keinen Spaß | 3 | 5 | Testspieler legt vor Minute 10 weg | Genau dafür existiert Phase 5. Die Frage wird **vor** der teuren Weltproduktion gestellt, nicht danach |
| R-15 | Wirtschaftliche Erwartung wird enttäuscht | 4 | 2 | — | **Ehrliche Einordnung:** Idle-Tycoons sind ein gesättigtes Genre. Ohne Marketingbudget sind organische Downloads im niedrigen vierstelligen Bereich das realistische Ergebnis, kein fünfstelliger Umsatz. Der belastbare Gewinn dieses Projekts ist zunächst die aufgebaute Kompetenz und eine wiederverwendbare Codebasis für weitere Titel |
| R-16 | Lizenz-/Copyright-Fehler bei Assets | 2 | 4 | Asset ohne Eintrag in `ASSET_LICENSES.md` | Guardrail D4; jedes externe Asset wird bei Aufnahme dokumentiert, nicht rückwirkend |
| R-18 | D-U-N-S-Nummer verzögert den Release | 3 | 3 | Antrag nach 3 Wochen ohne Rückmeldung | Bis zu 30 Tage Bearbeitung, Google gewährt **keine** Ausnahme. Deshalb sofort beantragen, lange vor dem Release |
| R-17 | Upload-Keystore geht verloren | 2 | 5 | — | Keystore außerhalb des Repositories, Sicherungskopie an einem zweiten Ort. Ohne ihn ist kein Update der veröffentlichten App mehr möglich |

---

## Was bewusst als Risiko akzeptiert wird

| Akzeptiert | Begründung |
|---|---|
| Saves sind manipulierbar | Offline-Einzelspieler ohne Ranglisten — der Schaden trifft nur den Spieler selbst. Wirksamer Schutz wäre unverhältnismäßiger Aufwand |
| Keine serverseitige Kaufvalidierung im MVP | Erst ab nennenswertem Umsatz wirtschaftlich sinnvoll; die Schnittstelle ist darauf vorbereitet |
| Godot hat ein kleineres Plugin-Ökosystem als Unity | Bewusst eingegangen für Speicherbedarf, Build-Geschwindigkeit und Agenten-Bearbeitbarkeit (ADR-001) |
| Kein Emulator | Echtes Gerät ist auf dieser Hardware schneller und ehrlicher (ADR-013) |
