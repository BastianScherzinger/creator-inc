## Ereignisse, die der Simulationskern nach aussen meldet.
##
## Der Kern sendet -- er weiss nie, wer zuhoert. Die Praesentation abonniert.
## Diese Richtung ist die Architekturentscheidung ADR-004 und darf nicht
## umgedreht werden: Sobald der Kern die Darstellung kennt, ist er nicht mehr
## ohne Szene testbar.
##
## Bewusst RefCounted statt Node: core/ darf keine Godot-Nodes verwenden.
class_name EventBus
extends RefCounted

## Kapital hat sich geaendert. `differenz` ist positiv bei Einnahmen.
signal money_changed(neuer_stand: float, differenz: float)

## Eine Station wurde ausgebaut.
signal station_upgraded(station_id: StringName, neue_stufe: int)

## Der Engpass der Kette hat gewechselt. Das ist das wichtigste Signal des
## Spiels -- die Praesentation macht daraus die sichtbare Warteschlange.
signal bottleneck_changed(station_id: StringName)

## Ein Durchsatz-Zyklus wurde abgeschlossen (fuer Effekte und Zahlen-Popups).
signal throughput_tick(menge: float, erloes: float)

## Etwas wurde freigeschaltet.
signal unlocked(unlock_id: StringName)

## Ein Meilenstein wurde erreicht.
signal milestone_reached(milestone_id: StringName)

## Offline-Ertrag wurde beim Start verrechnet.
signal offline_progress_applied(sekunden: float, erloes: float)

## Eine harte Obergrenze deckelt gerade den Durchsatz.
## `anteil` ist die Auslastung (1.0 = am Anschlag), `aktiv` false nach dem Umbau.
signal limit_changed(anteil: float, aktiv: bool)

## Ein Tick hat Geld gekostet (Welt 6, Risiko). `betrag` ist positiv und genau
## das, was vom Kapital abgezogen wurde. Kaeufe melden sich NICHT hier -- sie
## erscheinen nur als negative Differenz in money_changed.
signal loss_tick(betrag: float)

## Der Abonnentenbestand hat sich geaendert (Welt 5).
## `abwanderung` ist der Verlust pro Sekunde -- die Zahl, die weh tut.
signal bestand_changed(bestand: float, abwanderung: float)

## Der Spieler ist in eine neue Welt gewechselt.
signal world_changed(welt_index: int, welt_id: String)

## Ein Belohnungsschub hat begonnen oder ist ausgelaufen.
## `rest_sekunden` ist beim Auslaufen 0 -- die Oberflaeche braucht kein
## eigenes Mitzaehlen.
signal boost_changed(faktor: float, rest_sekunden: float)

## Ein Sonderauftrag steht bereit oder wurde eingeloest.
signal special_order_available(order_id: StringName, bonus: float)
signal special_order_completed(order_id: StringName, erloes: float)

# --- Welt in die Tiefe (ADR-021) ----------------------------------------------

## Ein Ausstattungsplatz wurde gekauft oder hochgelevelt.
signal equipment_upgraded(station_id: StringName, platz_id: StringName, neue_stufe: int)

## Ein Raum der Karte wurde gekauft.
signal area_bought(bereich_id: StringName)

## Ein neues Kapitel der Welt beginnt (0-basiert; K5). Nur durch einen Raumkauf.
signal chapter_started(index: int)

## Ein sichtbares Ziel ist erfuellt und kann eingeloest werden.
signal goal_completed(ziel_id: StringName)

## Ein Ziel wurde eingeloest.
signal goal_claimed(ziel_id: StringName, belohnung: float)

## Ueber einer Station ist eine Tipp-Blase erschienen.
signal moment_appeared(station_id: StringName, dauer: float)

## Eine Tipp-Blase ist vorbei -- angetippt (mit Belohnung) oder leise verschwunden.
signal moment_ended(station_id: StringName, angetippt: bool, belohnung: float)

## Eine Nachricht ist aufs Handy gekommen.
signal message_received(nachricht_id: StringName)

## Die Welt ist vollstaendig abgeschlossen (100 %).
signal world_completed()

## Eine Fortschrittsmarke (25/50/75 % der Welt) ist erreicht und kann abgeholt werden.
signal progress_mark_ready(mark_id: StringName)

## Eine Fortschrittsmarke wurde abgeholt.
signal progress_mark_claimed(mark_id: StringName, belohnung: float)

## Das Tagesgeschenk wurde abgeholt: Serientag (1..n) und Betrag.
signal daily_gift_claimed(serientag: int, betrag: float)

# --- Design-Overhaul 15.10.: Sterne, Crew, Tagesaufgaben, Erfolge, Level ------

## Eine Station hat einen neuen Stern erreicht (`sterne` = Anzahl jetzt).
signal star_reached(station_id: StringName, sterne: int)

## Eine Crew-Karte wurde gekauft (`rang` 1..3).
signal crew_hired(station_id: StringName, rang: int)

## Eine Tagesaufgabe ist erfuellt / wurde eingeloest.
signal daily_task_completed(aufgabe_id: StringName)
signal daily_task_claimed(aufgabe_id: StringName, belohnung: float)

## Ein Erfolg ist erreicht; `bonus` ist der dauerhafte Zuwachs des Weltfaktors.
signal achievement_unlocked(erfolg_id: StringName, bonus: float)

## Der Firmen-Rang des Spielers ist gestiegen (K2 P2a). Kommt zusaetzlich zu
## player_level_up; `name_id` ist der i18n-Schluessel des Rangnamens.
signal rank_up(rang: int, name_id: StringName)

## Der Rang des Spielers ist gestiegen (alter Name, traegt die Rangnummer).
signal player_level_up(level: int)
