# K3 B1 · Pacing: Raumkurve glätten, Lückenprüfung

Stand: 16.10.2026. Messung: `welt_sim.gd` (optimaler Spieler, ohne Rang-Übertrag), `balance_sim.gd` Exit 0, alle 475 Tests grün, Durchspielprobe `--alle-welten` ohne Absturz.

## Ergebnis je Welt (vorher = P6-Stand, nachher = jetzt)

| Welt | Raumkäufe vorher (R1 R2 R3 R4 R5) | Raumkäufe nachher (R1 R2 R3 **3b** R4 R5) | größte Raumlücke vorher → nachher | R5 → Abschluss | Abschluss (Korridor) | Upgrades/Min Einstieg |
|---|---|---|---|---|---|---|
| 1 zimmer | 3:35 9:58 22:49 62:35 68:43 | 3:33 10:11 21:20 31:20 44:10 54:29 | 39:46 → **12:50** | 10:12 → 21:43 | 78:55 → 76:12 (75–80) | 4,30 → 3,90 |
| 2 auftrag | 3:53 11:54 29:20 62:59 66:36 | 3:51 11:40 23:14 34:13 45:07 54:02 | 33:39 → **11:34** | 8:17 → 20:02 | 74:53 → 74:04 (70–80) | 4,00 → 3,90 |
| 3 webseiten | 3:43 12:31 26:27 62:49 65:15 | 3:41 12:39 23:00 – 34:51 47:05 | 36:22 → **12:14** | 19:40 → 38:50 | 84:55 → 85:55 (80–90) | 3,40 → 3,40 |
| 4 buero | 3:48 11:43 32:26 75:00 83:29 | 3:46 11:53 22:53 32:43 40:56 52:44 | 42:34 → **11:48** | 16:01 → 38:14 | 99:30 → 90:58 (90–100) | 3,80 → 3,80 |
| 5 produkt | 3:35 12:27 38:16 93:05 93:51 | 3:48 11:43 23:15 34:15 44:41 57:16 | 54:49 → **12:35** | 14:34 → 50:27 | 108:25 → 107:43 (100–110) | 3,20 → 3,20 |
| 6 kapital | 3:56 12:01 38:49 101:51 104:52 | 3:50 12:10 23:04 34:48 45:21 49:08 | 63:02 → **11:44** | 14:26 → 64:59 | 119:18 → 114:07 (110–120) | 3,10 → 3,00 |

Einstieg: erstes Upgrade 0:01–0:08 (Grenze 10 s), Raum 2 (bereich_1) 3:33–3:51 (Grenze 4:00), Kaufpause im Einstieg ≤ 82 s. Die Raumlücke ist in allen Welten ≤ 15 min (Grenze `raum_luecke_max` 900 s), Raum 5 → Abschluss ≥ 8 min (Grenze `raum5_bis_ende_min` 480 s; knappster Wert Welt 2 mit 20:02).

Welt 3 hat keinen 6. Raum (keine freie Zone im Grundriss); dort reichen drei Räume zwischen Raum 2 und Abschluss: Lücke 12:14.

## Nicht erreicht (nur ausgegeben, nicht geprüft)

* **Einkommen Raum 4 → Ende ≤ ×100:** gemessen ×2.700 (W3) bis ×20.000 (W5/W6, W1 ×11.700). Vorher ×61 (W3) bis ×2.550 (W1). Grund: Das Einkommen hängt am Ende fast allein an der Ausstattung/Crew-Kette (Produkt der Faktoren), und die letzten Käufe sind klein gegen das Einkommen. Mit reinen Kosten-/Wachstumswerten lässt sich ×100 nicht halten, ohne die Welt-Korridore zu sprengen (R4 müsste ~5 min vor dem Ende liegen, R5 danach). Der Wert wird in `bericht()` ausgegeben (`Pacing:`-Zeile), `raum4_sprung()` steht bereit, ist aber nicht in `ZIELE`.
* **Großereignis-Lücke ≤ 12 min:** W1–W4 erfüllt (8:20 / 9:58 / 10:20 / 11:52), W5 15:35 (bei 72:51), W6 23:26 (bei 72:34). Ursache ist der Simulator: Crew-Ränge 2/3 und Rang-Aufstiege kauft/erreicht er erst spät (nur wenn „bezahlbar und lohnend“). Auch ausgegeben, nicht geprüft (`gross_luecke()`). Wer das schließen will, braucht eine andere Kauf-Regel für Crew im Simulator oder mehr Rang-Schwellen in Welt 5/6.

## Geänderte Werte (Daten)

| Hebel | Änderung |
|---|---|
| `bereiche.bereich_6` („Raum 3b“) | neu in W1, W2, W4, W5, W6 (nicht W3): Zonen `bad`, `younes_ecke`, `pausenraum`, `selins_labor`, `dachterrasse` (`worlds.json`, nur `zonen[].bereich`). `nach: bereich_3`, Bonus alle ×1,06; Kosten je Welt zwischen Raum 3 und 4 (W1 17,3 Tsd. … W6 842 Mio.). Kaufreihenfolge = Reihenfolge im JSON (3 → 6 → 4 → 5). |
| `bereich_3` | Kosten gesenkt (W1 25 Tsd. → 20,5 Tsd., W6 2,5 Mrd. → 633 Mio.), damit Raum 3 früher kommt |
| `bereich_4` | Kosten ≈ ×0,1…0,3; `nach: bereich_6` (W3: `nach: bereich_3`); Bonus einheitlich alle ×1,12 (vorher eine Station ×1,5) |
| `bereich_5` | Kosten ≈ ×0,05…0,15; Bonus alle ×1,15 (vorher alle ×1,5) |
| Stationen `wachstum` | W1 1,27 → 1,284 · W2 1,28 → 1,291 · W3 1,282 → 1,289 · W4 1,302 → 1,311 · W5 1,315 → 1,337 · W6 1,332 → 1,355 (Räume früher/billiger verkürzen die Welt, das Wachstum gleicht aus; Korridore halten) |
| Stationen `basis_kosten` | je ×(altes/neues Wachstum)³, damit die ersten Stufen so billig bleiben wie vorher (Einstieg) |
| Ziele | neu `ziel_auftrag_1..3`, `kette: "auftrag"`, direkt hinter dem Raum-3-Ziel; Typ `station_stufe` (Annahme-Station, Verarbeitung, Transport) mit Stufen, die der Simulator zwischen Raum 3 und Raum 4 erreicht (W1 23/21/13 … W6 17/17/10) |
| Nachrichten | `nachricht_23` (Raum 3 gekauft) und `nachricht_24` (Kette `auftrag` fertig) hinter der Raum-3-Nachricht, `nachricht_15` bleibt letzte; je Welt 24 Nachrichten |
| `momente` | `abstand_min/max` 90/150, `stapel_schub_sekunden` 30, `kiste_sekunden` 60 |
| `crew.*.frei` | Typ „Kette bereich_n fertig“ → „Raum bereich_n gekauft“ (die Ketten fertig sind erst nach 40–90 min): die erste Crew kommt in allen Welten vor Raum 4 (W1 29:57 … W6 39:19; W4 59:58 liegt nach Raum 4, die Welt hat die längste Kette) |
| `erfolge.json` Rang-Schwellen | je 3 Punkte mehr je Welt (Aufträge); Rang 4/5/6 in Welt 1: 14/24/34 → 11/17/26, damit zwischen den Räumen ein Rang fällt; letzte Schwelle 461 |
| `ziel_minuten` | unverändert |

## Messwerkzeuge und Code (nur was nötig war)

* `tools/abschluss_sim.gd`: `ZIELE` mit `raum_luecke_max: 900` und `raum5_bis_ende_min: 480` (gelten für `_standard` und `zimmer`), neue Methoden `raum_luecke()`, `raum5_bis_ende()`, `raum4_sprung()`, `gross_luecke()`, Großereignis-Liste (Raum, Crew, Auftrag, Rang), Einkommen-Verlauf je Minute, Kauf-Protokoll. `bericht()` druckt die Zeile `Pacing:` – damit gibt `balance_sim.gd` die Werte aus, ohne selbst geändert zu sein.
* `tools/welt_sim.gd`: Ausgabe „Einkommen/s alle 5 min“ und „Grossereignisse“; neuer Schalter `--kaeufe` (jeder Kauf mit Preis und Einkommen danach).
* `tests/unit/test_balance_data.gd`: `test_k3_pacing_daten_in_jeder_welt`, `test_k3_pacing_grenzen_im_simulator`. Angepasst wegen neuer Daten: `test_alle_welten_tiefe` (6 Räume außer W3, 24 Nachrichten), `test_welt_tiefe` (Raumreihenfolge 3 → 6 → 4, Moment-Wartezeit 155 s).
* **Außerhalb der Dateiliste, bewusst und klein:** `core/data/balance_data.gd::_pruefe_ketten` lässt `kette: "auftrag"` zu, `core/game_core.gd::ketten_ids` führt „auftrag“ als Kette (sonst fiel `test_jedes_ziel_gehoert_zu_genau_einer_kette`). Ohne diese zwei Zeilen sind die Aufträge ungültig.

## Hinweise an die Leitung

* Figuren in den 6.-Raum-Zonen: Welt 2 `younes_ecke`, Welt 5 `selins_labor` sind Wohnorte von Younes/Selin und jetzt bis zum Kauf von Raum 3b gesperrt. Die Darstellung der Sperre läuft über Daten (`bereich`), wurde aber nicht am Handy angesehen.
* Die Raumkosten sind mit dem Optimierer eingestellt; wer sie ändert, misst neu (`welt_sim -- <welt>`): Der Simulator kauft Räume nicht streng nach Preis, sondern nach Amortisation, die Kurve Kosten → Kaufzeit ist stufig.
* Rang-Übertrag (`--mit-rang`) wurde nach dem Umbau nicht neu gemessen.
