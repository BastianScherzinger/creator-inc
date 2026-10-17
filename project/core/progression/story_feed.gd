## Die Geschichte in Nachrichten (ADR-021).
##
## Keine Zwischensequenzen, keine Dialogbaeume: Die Geschichte kommt aufs Handy,
## wenn im Spiel etwas passiert ist. Mira fragt nach ihrer Lampe, nachdem man
## das Licht ausgebaut hat -- und nicht vorher.
##
## Die Nachrichten kommen IN REIHENFOLGE. Ist die Bedingung von Nachricht 9
## schon erfuellt, waehrend Nachricht 5 noch wartet, kommt 9 danach. Eine
## Geschichte, deren Saetze in beliebiger Reihenfolge eintreffen, erzaehlt
## nichts mehr.
##
## Kennt nur IDs und Bedingungen. Absender und Text stehen im Thema (D3).
class_name StoryFeed
extends RefCounted

var _definitionen: Array = []        ## Array[Dictionary]
var _empfangen: Array[String] = []   ## IDs in Empfangsreihenfolge
var _gelesen: int = 0                ## wie viele davon gelesen


func _init(definitionen: Array = []) -> void:
	_definitionen = definitionen


func hat_nachrichten() -> bool:
	return not _definitionen.is_empty()


func empfangen() -> Array[String]:
	return _empfangen.duplicate()


func ungelesen() -> int:
	return maxi(_empfangen.size() - _gelesen, 0)


func markiere_gelesen() -> void:
	_gelesen = _empfangen.size()


## Stellt zu, was faellig ist -- der Reihe nach, bis eine Bedingung nicht
## erfuellt ist. Gibt die neu zugestellten IDs zurueck.
func pruefe(erfuellt: Callable, bus: EventBus = null) -> Array[String]:
	var neu: Array[String] = []
	while _empfangen.size() < _definitionen.size():
		var naechste: Dictionary = _definitionen[_empfangen.size()] as Dictionary
		var ausloeser: Dictionary = naechste.get("ausloeser", {}) as Dictionary
		if not bool(erfuellt.call(ausloeser)):
			break
		var nachricht_id: String = String(naechste.get("id", ""))
		_empfangen.append(nachricht_id)
		neu.append(nachricht_id)
		if bus != null:
			bus.message_received.emit(StringName(nachricht_id))
	return neu


func to_dict() -> Dictionary:
	return {"empfangen": _empfangen.duplicate(), "gelesen": _gelesen}


func apply_dict(daten: Dictionary) -> void:
	_empfangen.clear()
	for eintrag in (daten.get("empfangen", []) as Array):
		_empfangen.append(String(eintrag))
	_gelesen = clampi(int(daten.get("gelesen", 0)), 0, _empfangen.size())
