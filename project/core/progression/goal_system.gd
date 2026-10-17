## Ziele: ein fester Pfad durch die Welt, immer drei davon sichtbar (ADR-021).
##
## Das Fernziel (Welt abschliessen) ist zu weit weg, um heute Abend zu tragen.
## Ein Nahziel ist jetzt: "Bring den Schnitt auf Stufe 10". Drei gleichzeitig,
## weil einer zu wenig Wahl laesst und zehn eine Liste sind, die man nicht liest.
##
## Ein erfuelltes Ziel wird nicht still verbucht, sondern EINGELOEST. Der Moment
## des Abholens ist die Belohnung -- ein Betrag, der von allein aufs Konto
## wandert, wird nicht bemerkt.
##
## Das System weiss nicht, WAS gemessen wird. Es bekommt eine Messfunktion vom
## Kern: bedingung -> aktueller Wert. So bleiben Ziele reine Daten.
class_name GoalSystem
extends RefCounted

const SICHTBAR: int = 3

var _definitionen: Array = []        ## Array[Dictionary] in fester Reihenfolge
var _eingeloest: Dictionary = {}     ## String -> true
var _gemeldet: Dictionary = {}       ## String -> true (erfuellt schon gemeldet)


func _init(definitionen: Array = []) -> void:
	_definitionen = definitionen


func hat_ziele() -> bool:
	return not _definitionen.is_empty()


func anzahl() -> int:
	return _definitionen.size()


func anzahl_eingeloest() -> int:
	return _eingeloest.size()


func ist_eingeloest(ziel_id: String) -> bool:
	return _eingeloest.has(ziel_id)


## Die naechsten offenen Ziele in Pfad-Reihenfolge.
func sichtbar(anzahl_max: int = SICHTBAR) -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for eintrag in _definitionen:
		var d: Dictionary = eintrag as Dictionary
		if _eingeloest.has(String(d.get("id", ""))):
			continue
		liste.append(d)
		if liste.size() >= anzahl_max:
			break
	return liste


func definitionen() -> Array:
	return _definitionen


func definition(ziel_id: String) -> Dictionary:
	for eintrag in _definitionen:
		if String((eintrag as Dictionary).get("id", "")) == ziel_id:
			return eintrag as Dictionary
	return {}


## 0.0 bis 1.0.
static func fortschritt(ziel: Dictionary, messen: Callable) -> float:
	var soll: float = float(ziel.get("wert", 1.0))
	if soll <= 0.0:
		return 1.0
	var ist: float = float(messen.call(ziel))
	return clampf(ist / soll, 0.0, 1.0)


static func erfuellt(ziel: Dictionary, messen: Callable) -> bool:
	return fortschritt(ziel, messen) >= 1.0


## Meldet sichtbare Ziele, die GERADE erfuellt wurden -- jedes genau einmal.
## Gibt die IDs zurueck, die in diesem Durchlauf neu erfuellt waren.
func pruefe(messen: Callable, bus: EventBus = null) -> Array[String]:
	var neu: Array[String] = []
	for ziel in sichtbar():
		var ziel_id: String = String(ziel.get("id", ""))
		if _gemeldet.has(ziel_id):
			continue
		if erfuellt(ziel, messen):
			_gemeldet[ziel_id] = true
			neu.append(ziel_id)
			if bus != null:
				bus.goal_completed.emit(StringName(ziel_id))
	return neu


func einloesbar(messen: Callable) -> int:
	var anzahl_bereit: int = 0
	for ziel in sichtbar():
		if erfuellt(ziel, messen):
			anzahl_bereit += 1
	return anzahl_bereit


## Loest ein Ziel ein, wenn es sichtbar und erfuellt ist. Gibt die Definition
## zurueck (fuer die Belohnung) oder ein leeres Dictionary.
##
## Nur SICHTBARE Ziele: Wer Ziel 14 schon erfuellt hat, waehrend Ziel 3 offen
## ist, bekommt es, sobald es an der Reihe ist. Sonst liefe der Pfad nicht
## mehr in einer Reihenfolge, und die Geschichte in den Zielen auch nicht.
func einloesen(ziel_id: String, messen: Callable) -> Dictionary:
	for ziel in sichtbar():
		if String(ziel.get("id", "")) != ziel_id:
			continue
		if not erfuellt(ziel, messen):
			return {}
		_eingeloest[ziel_id] = true
		return ziel
	return {}


func to_array() -> Array[String]:
	var liste: Array[String] = []
	for schluessel in _eingeloest.keys():
		liste.append(String(schluessel))
	return liste


func apply_array(liste: Array) -> void:
	_eingeloest.clear()
	_gemeldet.clear()
	for eintrag in liste:
		_eingeloest[String(eintrag)] = true
