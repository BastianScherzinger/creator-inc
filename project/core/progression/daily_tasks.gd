## Tagesaufgaben: zwei kleine Aufgaben je Kalendertag (Design-Overhaul 15.10.).
##
## Reine Regeln ohne Uhr: der Kalendertag kommt als Zahl von aussen (wie beim
## Tagesgeschenk). Die Auswahl ist deterministisch aus dem Tag -- zwei Geraete
## am selben Tag bekommen dieselben Aufgaben, und ein Neustart wuerfelt nicht um.
##
## Gezaehlt werden Ereignisse (Stufen gekauft, Ziel eingeloest, ...), die der
## Kern meldet. Die Belohnung (Einkommen x Sekunden) berechnet ebenfalls der Kern.
class_name DailyTasks
extends RefCounted

const PFAD: String = "res://data/balance/tagesaufgaben.json"

var pro_tag: int = 2
var ab_fortschritt: float = 0.2

var _pool: Array = []                ## Array[Dictionary]
var _tag: int = 0
var _gewaehlt: Array[String] = []
var _stand: Dictionary = {}          ## id -> float
var _eingeloest: Dictionary = {}     ## id -> true
var _gemeldet: Dictionary = {}       ## id -> true


## `welt_pool` ergaenzt den globalen Pool; gleiche `id` ueberschreibt ihn.
func _init(welt_pool: Array = [], daten: Dictionary = {}) -> void:
	var roh: Dictionary = daten if not daten.is_empty() else lade_roh()
	pro_tag = int(roh.get("pro_tag", pro_tag))
	ab_fortschritt = float(roh.get("ab_fortschritt", ab_fortschritt))
	for eintrag in (roh.get("pool", []) as Array):
		_pool.append(eintrag)
	for eintrag in welt_pool:
		var d: Dictionary = eintrag as Dictionary
		var ersetzt: bool = false
		for i in range(_pool.size()):
			if String((_pool[i] as Dictionary).get("id", "")) == String(d.get("id", "")):
				_pool[i] = d
				ersetzt = true
				break
		if not ersetzt:
			_pool.append(d)


static func lade_roh() -> Dictionary:
	if not FileAccess.file_exists(PFAD):
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(PFAD))
	return roh as Dictionary if roh is Dictionary else {}


func tag() -> int:
	return _tag


## Stellt den Tag ein. Neuer Tag = neue Aufgaben (und alter Stand weg).
## Mit `aktiv` false bleibt die Liste leer, bis die Welt weit genug ist.
func aktualisiere(heute: int, aktiv: bool) -> void:
	if heute != _tag:
		_tag = heute
		_gewaehlt.clear()
		_stand.clear()
		_eingeloest.clear()
		_gemeldet.clear()
	if _gewaehlt.is_empty() and aktiv:
		_waehle(heute)


func _waehle(heute: int) -> void:
	if _pool.is_empty():
		return
	var zufall := RandomNumberGenerator.new()
	zufall.seed = heute * 7919 + 17
	var reihenfolge: Array = range(_pool.size())
	# Fisher-Yates mit dem festen Zufall dieses Tages.
	for i in range(reihenfolge.size() - 1, 0, -1):
		var j: int = zufall.randi_range(0, i)
		var tmp: Variant = reihenfolge[i]
		reihenfolge[i] = reihenfolge[j]
		reihenfolge[j] = tmp
	var zaehler_genutzt: Dictionary = {}
	for index in reihenfolge:
		if _gewaehlt.size() >= pro_tag:
			break
		var d: Dictionary = _pool[index] as Dictionary
		var art: String = String(d.get("zaehler", ""))
		if zaehler_genutzt.has(art):
			continue
		zaehler_genutzt[art] = true
		_gewaehlt.append(String(d.get("id", "")))


func gewaehlt() -> Array[String]:
	return _gewaehlt


func definition(aufgabe_id: String) -> Dictionary:
	for eintrag in _pool:
		if String((eintrag as Dictionary).get("id", "")) == aufgabe_id:
			return eintrag as Dictionary
	return {}


func soll(aufgabe_id: String) -> float:
	return float(definition(aufgabe_id).get("wert", 1.0))


func ist(aufgabe_id: String) -> float:
	return float(_stand.get(aufgabe_id, 0.0))


func erfuellt(aufgabe_id: String) -> bool:
	return ist(aufgabe_id) >= soll(aufgabe_id)


func ist_eingeloest(aufgabe_id: String) -> bool:
	return _eingeloest.has(aufgabe_id)


## Zaehlt ein Ereignis. Gibt die Aufgaben zurueck, die dadurch GERADE erfuellt
## wurden (jede genau einmal).
func zaehle(zaehler: String, menge: float) -> Array[String]:
	var neu: Array[String] = []
	for aufgabe_id in _gewaehlt:
		if String(definition(aufgabe_id).get("zaehler", "")) != zaehler:
			continue
		if _eingeloest.has(aufgabe_id):
			continue
		_stand[aufgabe_id] = ist(aufgabe_id) + menge
		if erfuellt(aufgabe_id) and not _gemeldet.has(aufgabe_id):
			_gemeldet[aufgabe_id] = true
			neu.append(aufgabe_id)
	return neu


## Markiert als eingeloest, wenn erfuellt. Gibt die Definition zurueck oder {}.
func einloesen(aufgabe_id: String) -> Dictionary:
	if not _gewaehlt.has(aufgabe_id) or _eingeloest.has(aufgabe_id) or not erfuellt(aufgabe_id):
		return {}
	_eingeloest[aufgabe_id] = true
	return definition(aufgabe_id)


func to_dict() -> Dictionary:
	return {
		"tag": _tag,
		"gewaehlt": _gewaehlt.duplicate(),
		"stand": _stand.duplicate(),
		"eingeloest": _eingeloest.keys(),
	}


func apply_dict(d: Dictionary) -> void:
	_tag = int(d.get("tag", 0))
	_gewaehlt.clear()
	for eintrag in (d.get("gewaehlt", []) as Array):
		_gewaehlt.append(String(eintrag))
	_stand.clear()
	var roh_stand: Dictionary = d.get("stand", {}) as Dictionary
	for schluessel in roh_stand.keys():
		_stand[String(schluessel)] = float(roh_stand[schluessel])
	_eingeloest.clear()
	for eintrag in (d.get("eingeloest", []) as Array):
		_eingeloest[String(eintrag)] = true
	_gemeldet.clear()
	for aufgabe_id in _gewaehlt:
		if erfuellt(aufgabe_id):
			_gemeldet[aufgabe_id] = true
