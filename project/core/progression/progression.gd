## Freischaltungen und Meilensteine.
##
## Prueft datengetriebene Bedingungen aus data/balance/<welt>.json.
## Jede Freischaltung feuert genau einmal -- ein zweites Mal waere im besten
## Fall ein doppelter Belohnungston, im schlimmsten eine doppelte Auszahlung.
class_name Progression
extends RefCounted

var freigeschaltet: Dictionary = {}   ## String -> true
var _bedingungen: Dictionary = {}     ## String -> {typ, schwelle}


func _init(unlock_definitionen: Dictionary = {}) -> void:
	_bedingungen = unlock_definitionen


func ist_frei(unlock_id: StringName) -> bool:
	return freigeschaltet.has(String(unlock_id))


## Markiert eine Freischaltung ohne Bedingungspruefung (fuer das Laden
## eines Spielstands).
func setze_frei(unlock_id: StringName) -> void:
	freigeschaltet[String(unlock_id)] = true


## Prueft alle Bedingungen und meldet neu erreichte Freischaltungen.
## Gibt die Liste der in diesem Aufruf neu freigeschalteten IDs zurueck.
func pruefe(kapital: float, stufen_gesamt: int, bus: EventBus = null) -> Array[StringName]:
	var neu: Array[StringName] = []
	for schluessel in _bedingungen.keys():
		if freigeschaltet.has(schluessel):
			continue
		var bedingung: Dictionary = _bedingungen[schluessel] as Dictionary
		if _erfuellt(bedingung, kapital, stufen_gesamt):
			freigeschaltet[schluessel] = true
			var id := StringName(schluessel)
			neu.append(id)
			if bus != null:
				bus.unlocked.emit(id)
	return neu


func _erfuellt(bedingung: Dictionary, kapital: float, stufen_gesamt: int) -> bool:
	var typ: String = String(bedingung.get("typ", ""))
	var schwelle: float = float(bedingung.get("schwelle", 0.0))
	match typ:
		"kapital":
			return kapital >= schwelle
		"stufen_gesamt":
			return float(stufen_gesamt) >= schwelle
		_:
			push_warning("Unbekannter Unlock-Typ: %s" % typ)
			return false


func to_array() -> Array[String]:
	var liste: Array[String] = []
	for schluessel in freigeschaltet.keys():
		liste.append(String(schluessel))
	return liste


func apply_array(liste: Array[String]) -> void:
	freigeschaltet.clear()
	for eintrag in liste:
		freigeschaltet[eintrag] = true
