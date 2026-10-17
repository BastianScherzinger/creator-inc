# P6 Pacing (K2 §4.3)

Stand: 15.10.2026. Messung: `welt_sim.gd` (optimaler Spieler), ohne und mit Rang-Übertrag (`-- --mit-rang`).

## Korridor aus Daten
`data/balance/<welt>.json → "ziel_minuten": [min, max]` (Simulator-Minuten). `BalanceData.ziel_minuten` liest und prüft das Feld (0 < min < max); `AbschlussSim.pruefe()` nimmt es für die Abschlusszeit, sonst gilt der Standard (60–100 min). `balance_sim.gd` und `validate.ps1` brauchen keine Änderung: sie rufen `pruefe()` auf.

## Ergebnis (Abschlusszeit, min:s)
| Welt | Korridor | vorher ohne Rang | nachher ohne Rang | vorher mit Rang | nachher mit Rang |
|---|---|---|---|---|---|
| 1 zimmer | 75–80 | 78:55 | 78:55 | 78:55 | 78:55 |
| 2 auftrag | 70–80 | 65:37 | 74:53 | 63:48 | 72:56 |
| 3 webseiten | 80–90 | 71:03 | 84:55 | 66:53 | 80:27 |
| 4 buero | 90–100 | 64:56 | 99:30 | 59:12 | 90:41 |
| 5 produkt | 100–110 | 62:59 | 108:25 | 57:25 | 95:28 (4,5 min unter Korridor) |
| 6 kapital | 110–120 | 64:00 | 119:18 | 56:04 | 106:16 (3,7 min unter Korridor) |

Summe ohne Rang: 6,5 h -> 8,4 h. Der Korridor-Lauf (`balance_sim.gd`, ohne Rang) ist in allen sechs Welten grün.

Mit Rang liegen W5/W6 unter dem Korridor: der Rang-Bonus (+0,5 % je Rang, bis +13 %) verkürzt die späten Welten um ~12 min, der Korridor ist nur 10 min breit. Ohne Rang bewusst an der Obergrenze, mit Rang knapp darunter. Wer das enger will, muss `bonus_je_rang` senken (nicht in P6).

## Geänderte Werte
| Welt | `ziel_belohnung_faktor` | Raum 4 / Raum 5 `kosten` | Stations-`wachstum` (alle 5, vorher 1,27) |
|---|---|---|---|
| 2 | 0,35 -> 0,25 | 3 Mio -> 4,5 Mio / 20 Mio -> 30 Mio | 1,28 |
| 3 | 0,5 -> 0,2 | 39 Mio -> 58,5 Mio / 260 Mio -> 520 Mio | 1,282 |
| 4 | 0,5 -> 0,2 | 300 Mio -> 600 Mio / 2 Mrd -> 4 Mrd | 1,302 |
| 5 | 0,5 -> 0,2 | 3 Mrd -> 6 Mrd / 10 Mrd -> 20 Mrd | 1,315 |
| 6 | 0,35 -> 0,2 | 30 Mrd -> 60 Mrd / 200 Mrd -> 400 Mrd | 1,332 |

Abweichung von der K2-Tabelle: Faktor und Raumkosten allein reichten nicht (Raumkosten wirken nur logarithmisch, +50 % Raum = ca. +1 min). Der eigentliche Hebel für W3–W6 ist `wachstum` der Stationen (Daten, keine Formeländerung): +0,01 ≈ +8–12 min. Die Ziel-Belohnungen sind mit 0,2 deutlich kleiner (weniger „jede Belohnung ein Sprung“). Welt 1 unverändert.

## Einstieg (unverändert gut)
Erstes Upgrade 0:01–0:08, Raum 2 zwischen 3:35 und 3:56, Upgrades/Min 3,1–4,3 (Welt 1: 0:01 / 3:35 / 4,30). Kaufpause im Einstieg ≤ 82 s (Grenze 90).

## Rang-Schwellen (`erfolge.json`)
Welt 1 unverändert (Rang 2/3/4/5/6 bei 2:26 / 7:07 / 12:47 / 38:16 / 68:43). In Welt 4 lagen Rang 17 und 18 bei 205/208 Punkten (mit Rang-Übertrag 4 s auseinander). Neu: 204 / 209 / 216 (vorher 205 / 208 / 214); mit Rang jetzt Rang 17 2:32, Rang 18 8:54, Rang 19 22:05. Punkte je Ziel sind zeitunabhängig, die Rang-Zeiten dehnen sich daher mit den Welten mit (W6 mit Rang: R27 3:32, R28 11:51, R29 85:04, R30 106:16).

## Tests
`tests/unit/test_balance_data.gd` (+2: Feld lesen/prüfen, jede Welt hat ihren Korridor), `test_rang`, `test_kern_overhaul`, `test_game_core` grün. `balance_sim.gd` Exit 0.
