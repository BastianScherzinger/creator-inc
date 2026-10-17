## Die Liste der Welten und ihre Reihenfolge.
##
## Bis hierher kannte das Spiel genau eine Welt, und ihr Name stand an drei
## Stellen im Code. Sechs Welten gehen so nicht: Jede Stelle, die "amt" kennt,
## ist eine Stelle, die beim Weltwechsel vergessen werden kann.
##
## Diese Klasse ist die EINZIGE Stelle, die weiss, welche Welten es gibt.
## Alles andere fragt hier nach. Eine Welt hinzuzufuegen ist damit eine
## Datenaenderung (ADR-010, jetzt auf die Weltebene gehoben).
##
## Kein Node, kein Rendering -- gehoert nach core/ und ist headless pruefbar.
class_name WorldData
extends RefCounted

const PFAD: String = "res://data/worlds/worlds.json"

## Fallback, wenn die Datei fehlt. Bewusst KEIN leeres Array: Ein Spiel ohne
## Welt startet nicht, und ein Absturz beim Start ist schwerer zu deuten als
## eine Welt, die anders aussieht als erwartet.
const NOTFALL_ID: String = "zimmer"

var welten: Array = []          ## Array[Dictionary]


static func laden(pfad: String = PFAD) -> WorldData:
	var daten := WorldData.new()
	if not FileAccess.file_exists(pfad):
		push_error("Weltliste fehlt: %s" % pfad)
		daten.welten = [daten._notfall()]
		return daten
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	if not (geparst is Dictionary):
		push_error("Weltliste nicht lesbar: %s" % pfad)
		daten.welten = [daten._notfall()]
		return daten
	daten.welten = (geparst as Dictionary).get("welten", []) as Array
	daten.roh_vorlagen = (geparst as Dictionary).get("licht_vorlagen", {}) as Dictionary
	if daten.welten.is_empty():
		push_error("Weltliste ist leer: %s" % pfad)
		daten.welten = [daten._notfall()]
	return daten


func anzahl() -> int:
	return welten.size()


## Die Welt an dieser Stelle im Bogen. Ein Index ausserhalb der Liste liefert
## die letzte Welt statt eines Fehlers -- wer durch ist, bleibt am Ende
## stehen, statt in eine leere Szene zu fallen.
func welt(index: int) -> Dictionary:
	if welten.is_empty():
		return _notfall()
	return welten[clampi(index, 0, welten.size() - 1)] as Dictionary


func id(index: int) -> String:
	return String(welt(index).get("id", NOTFALL_ID))


func index_von(welt_id: String) -> int:
	for i in range(welten.size()):
		if String((welten[i] as Dictionary).get("id", "")) == welt_id:
			return i
	return -1


func ist_letzte(index: int) -> bool:
	return index >= welten.size() - 1


func raum_breite(index: int) -> int:
	return int(welt(index).get("raum_breite", 11))


func raum_tiefe(index: int) -> int:
	return int(welt(index).get("raum_tiefe", 9))


func zoom_start(index: int) -> float:
	return float(welt(index).get("zoom_start", 24.0))


## Die Requisiten dieser Welt als Liste von [datei, position, drehung].
##
## Die Aufbereitung passiert hier und nicht in der Praesentation: Die
## Praesentation soll Objekte setzen, nicht JSON auseinandernehmen.
func kulisse(index: int) -> Array:
	var liste: Array = []
	for eintrag in (welt(index).get("kulisse", []) as Array):
		var d: Dictionary = eintrag as Dictionary
		liste.append([
			String(d.get("datei", "")),
			Vector3(float(d.get("x", 0.0)), 0.0, float(d.get("z", 0.0))),
			float(d.get("drehung", 0.0)),
		])
	return liste


## Alles, was der Raumbauer ueber den Grundriss wissen muss: wo die Tuer
## sitzt, wo Fenster sitzen, was im Raum steht.
##
## Als EIN Dictionary statt vier Einzelabfragen: Der Grundriss ist eine
## zusammengehoerige Aussage, und wer eine Welt ergaenzt, soll nicht an vier
## Stellen etwas hinzufuegen muessen.
func grundriss(index: int) -> Dictionary:
	var w: Dictionary = welt(index)
	return {
		"tuer_x": w.get("tuer_x", 3),
		"fenster_x": w.get("fenster_x", [-4, -2, 5]),
		"fenster_z": w.get("fenster_z", [-3, 1, 4]),
		"ausstattung": w.get("ausstattung", []),
		"laufwege": w.get("laufwege", []),
	}


## Die Weltpositionen der fuenf Stationen.
##
## Sie standen als Konstante in main.gd -- richtig fuer genau einen Grundriss.
## Im engen Zimmer von Welt 1 haetten zwei davon in der Wand gestanden.
##
## ACHTUNG ISOMETRIE: Die Kamera ist um 45 Grad gedreht, deshalb verlaeuft die
## Weltdiagonale (1,0,1) auf dem Bildschirm SENKRECHT. Im Hochformat ist das
## die einzige Richtung mit Platz -- die Kette gehoert auf diese Diagonale.
func stationen(index: int) -> Dictionary:
	var roh: Dictionary = welt(index).get("stationen", {}) as Dictionary
	var positionen: Dictionary = {}
	for schluessel in roh.keys():
		var p: Dictionary = roh[schluessel] as Dictionary
		positionen[StringName(String(schluessel))] = Vector3(
			float(p.get("x", 0.0)), 0.0, float(p.get("z", 0.0)))
	return positionen


## Wo Schild, Engpass-Ring und Treffer einer Station sitzen: ihre Position plus
## der optionale Versatz "schild": {"x", "z"}. Fuer Modelle, deren sichtbare
## Mitte nicht auf dem Ursprung liegt (gemessen mit tools/stations_mitte.gd).
func stationen_anzeige(index: int) -> Dictionary:
	var positionen: Dictionary = stationen(index)
	var roh: Dictionary = welt(index).get("stationen", {}) as Dictionary
	for schluessel in roh.keys():
		var versatz: Dictionary = (roh[schluessel] as Dictionary).get("schild", {}) as Dictionary
		var id := StringName(String(schluessel))
		positionen[id] = (positionen[id] as Vector3) + Vector3(
			float(versatz.get("x", 0.0)), 0.0, float(versatz.get("z", 0.0)))
	return positionen


## Wie sich die Figuren in dieser Welt verhalten.
##
## Der Standard ist "kunden" -- wer kommt, stellt sich an. Welt 1 setzt
## "zuschauer": Die meisten schauen kurz zu und gehen wieder. Das ist die
## ehrliche Darstellung von Reichweite und der Grund, warum sich Welt 1
## anders anfuehlt als alles danach.
func figuren(index: int) -> Dictionary:
	var f: Dictionary = welt(index).get("figuren", {}) as Dictionary
	return {
		"modus": String(f.get("modus", "kunden")),
		"bleibt_anteil": float(f.get("bleibt_anteil", 1.0)),
		"verweildauer": float(f.get("verweildauer", 1.6)),
	}


## --- Karte in voller Tiefe (ADR-021) -------------------------------------------

## Hat diese Welt einen Grundriss aus Zonen und Waenden statt eines Rechtecks?
func hat_zonen(index: int) -> bool:
	return not (welt(index).get("zonen", []) as Array).is_empty()


func zonen(index: int) -> Array:
	return welt(index).get("zonen", []) as Array


func waende(index: int) -> Array:
	return welt(index).get("waende", []) as Array


## Kameragrenzen, Zoombereich und Startblick. Welten ohne Eintrag bekommen die
## Werte, die bisher fest in der Kamera standen.
func karte(index: int) -> Dictionary:
	var k: Dictionary = welt(index).get("karte", {}) as Dictionary
	var g: Dictionary = k.get("grenzen", {}) as Dictionary
	var start: Dictionary = k.get("start", {}) as Dictionary
	return {
		"grenzen": Rect2(
			float(g.get("x1", -6.0)), float(g.get("z1", -6.0)),
			float(g.get("x2", 6.0)) - float(g.get("x1", -6.0)),
			float(g.get("z2", 6.0)) - float(g.get("z1", -6.0))),
		"zoom_min": float(k.get("zoom_min", 10.0)),
		"zoom_max": float(k.get("zoom_max", 44.0)),
		"start": Vector3(float(start.get("x", 0.6)), 0.0, float(start.get("z", 0.6))),
	}


## Wo das Schild eines Bereichs steht: die Mitte seiner ersten Zone.
func bereich_positionen(index: int) -> Dictionary:
	var ergebnis: Dictionary = {}
	for eintrag in zonen(index):
		var z: Dictionary = eintrag as Dictionary
		var bereich: String = String(z.get("bereich", ""))
		if bereich.is_empty() or ergebnis.has(StringName(bereich)):
			continue
		ergebnis[StringName(bereich)] = Vector3(
			(float(z.get("x1", 0)) + float(z.get("x2", 0))) * 0.5, 0.0,
			(float(z.get("z1", 0)) + float(z.get("z2", 0))) * 0.5)
	return ergebnis


## Welche Zone liegt an einem Weltpunkt? Leeres Dictionary, wenn keine.
##
## Erst zaehlt nur das Innere der Zone (Boden liegt von x1-0,5 bis x2+0,5). Erst
## wenn dort nichts trifft, gilt ein Rand von 0,5 m -- sonst gewinnt an jeder
## Raumgrenze die frueher gelistete Zone (RELEASE_PLAN 2.B).
func zone_an(index: int, punkt: Vector3) -> Dictionary:
	for rand in [0.0, 0.5]:
		for eintrag in zonen(index):
			var z: Dictionary = eintrag as Dictionary
			if zone_enthaelt(z, punkt, rand):
				return z
	return {}


## Liegt der Punkt in der Zone, mit `rand` Metern Zugabe?
static func zone_enthaelt(z: Dictionary, punkt: Vector3, rand: float = 0.0) -> bool:
	var x_ok: bool = punkt.x >= float(z.get("x1", 0)) - 0.5 - rand and punkt.x <= float(z.get("x2", 0)) + 0.5 + rand
	var z_ok: bool = punkt.z >= float(z.get("z1", 0)) - 0.5 - rand and punkt.z <= float(z.get("z2", 0)) + 0.5 + rand
	return x_ok and z_ok


## In welcher Zone steht eine Station? Leeres Dictionary, wenn in keiner.
func zone_der_station(index: int, station_id: StringName) -> Dictionary:
	var positionen: Dictionary = stationen(index)
	if not positionen.has(station_id):
		return {}
	return zone_an(index, positionen[station_id] as Vector3)


## Alle Stationen, die in dieser Zone stehen (Reihenfolge der Kette).
func stationen_in_zone(index: int, zone: Dictionary) -> Array[StringName]:
	var treffer: Array[StringName] = []
	var positionen: Dictionary = stationen(index)
	for id in Ids.ALL_STATIONS:
		if positionen.has(id) and zone_enthaelt(zone, positionen[id] as Vector3, 0.0):
			treffer.append(id)
	return treffer


## Die Startzone: die erste Zone ohne Bereich, in der Stationen stehen.
func startzone(index: int) -> Dictionary:
	for eintrag in zonen(index):
		var z: Dictionary = eintrag as Dictionary
		if String(z.get("bereich", "")).is_empty() and not stationen_in_zone(index, z).is_empty():
			return z
	return {}


## Die Figurenangaben so, wie sie in worlds.json stehen (Bewohner, Darsteller,
## Spielfigur). figuren() liefert nur die Felder der Warteschlangen-Welten.
func figuren_roh(index: int) -> Dictionary:
	return welt(index).get("figuren", {}) as Dictionary


func stationsmodell(index: int) -> String:
	return String(welt(index).get("stationsmodell", "stufen"))


## Die Darsteller einer Welt als Liste -- das alte einzelne Objekt gilt weiter.
func darsteller(index: int) -> Array:
	var roh: Variant = figuren_roh(index).get("darsteller", [])
	if roh is Dictionary:
		return [] if (roh as Dictionary).is_empty() else [roh]
	return roh as Array if roh is Array else []


## Welche Boden- und Wandmodule der Grundriss nimmt.
##
## Fehlt der Eintrag, gilt die Tabelle von Welt 1 (Dateien wg_*). "standard" ist
## die Tabelle aus dem Asset-Vertrag (boden_<typ>_a, wand_voll, ...). Ein
## Dictionary nennt die Dateien selbst: {"boeden": {typ: [a, b]},
## "waende": {typ: [wand, tuer, fenster, pfosten]}} -- was darin fehlt, kommt
## aus der Standardtabelle.
func module(index: int) -> Variant:
	return welt(index).get("module", "")


## Licht der Welt als fertiges Dictionary (Farben als Hex-Text, Energien, Schatten).
##
## "licht" darf ein Name aus "licht_vorlagen" sein ("warm") oder ein Dictionary,
## das einzelne Werte der warmen Vorlage ueberschreibt. Ohne Eintrag bekommen
## Welten mit Grundriss das warme Licht, alle anderen das alte.
func licht(index: int) -> Dictionary:
	var w: Dictionary = welt(index)
	var roh: Variant = w.get("licht", "warm" if hat_zonen(index) else "alt")
	var vorlagen: Dictionary = _licht_vorlagen()
	if roh is Dictionary:
		var ergebnis: Dictionary = (vorlagen.get("warm", {}) as Dictionary).duplicate(true)
		ergebnis.merge(roh as Dictionary, true)
		return ergebnis
	var name: String = String(roh)
	if not vorlagen.has(name):
		push_warning("Lichtvorlage '%s' fehlt in worlds.json -- es gilt 'warm'" % name)
		name = "warm"
	return (vorlagen.get(name, {}) as Dictionary).duplicate(true)


## Die Vorlagen aus worlds.json, sonst die bisherigen Werte als Notfall.
var roh_vorlagen: Dictionary = {}

func _licht_vorlagen() -> Dictionary:
	if not roh_vorlagen.is_empty():
		return roh_vorlagen
	return {
		"warm": {"hintergrund": "e9d8bf", "umgebung": "ffe8cc", "umgebung_energie": 0.38,
			"sonne": "ffe9c9", "sonne_energie": 0.85, "schatten": true},
		"alt": {"hintergrund": "2a2f3a", "umgebung": "6b7183", "umgebung_energie": 0.6,
			"sonne": "ffffff", "sonne_energie": 1.1, "schatten": false},
	}


func _notfall() -> Dictionary:
	return {
		"id": NOTFALL_ID,
		"raum_breite": 11,
		"raum_tiefe": 9,
		"zoom_start": 24.0,
		"kulisse": [],
	}
