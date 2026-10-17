## Allgemeine Bedienwoerter aus data/i18n/<sprache>.json.
##
## Thematische Begriffe kommen aus dem Thema (ThemeData), allgemeine Woerter wie
## "Ausbauen" oder "Stufe" von hier. Beides stand bisher verstreut als Literal im
## Code -- eine zweite Sprache haette bedeutet, jede Datei zu oeffnen.
class_name UiText
extends RefCounted

const PFAD: String = "res://data/i18n/%s.json"

static var _woerter: Dictionary = {}


static func t(schluessel: String) -> String:
	if _woerter.is_empty():
		_lade("de")
	var wert: Variant = _woerter.get(schluessel, null)
	if wert == null:
		push_warning("Bedientext fehlt: %s" % schluessel)
		return "[%s]" % schluessel
	return String(wert)


## Gibt es den Schluessel? (Fuer Texte, die aus Daten-IDs gebildet werden.)
static func hat(schluessel: String) -> bool:
	if _woerter.is_empty():
		_lade("de")
	return _woerter.has(schluessel)


static func _lade(sprache: String) -> void:
	var pfad: String = PFAD % sprache
	if not FileAccess.file_exists(pfad):
		push_error("Sprachdatei fehlt: %s" % pfad)
		_woerter = {"_": ""}
		return
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	_woerter = roh as Dictionary if roh is Dictionary else {"_": ""}
