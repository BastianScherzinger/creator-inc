## Lesezugriff auf data/tutorial/u3_texte.json: Bedientexte und Darstellungsschwellen
## der Szenen, Momente und der Zeigehand (Paket U3).
class_name U3Text
extends RefCounted

const PFAD: String = "res://data/tutorial/u3_texte.json"

static var _daten: Dictionary = {}


static func _lade() -> void:
	if not _daten.is_empty():
		return
	if not FileAccess.file_exists(PFAD):
		push_error("U3-Texte fehlen: %s" % PFAD)
		_daten = {"_": 1}
		return
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(PFAD))
	_daten = geparst as Dictionary if geparst is Dictionary else {"_": 1}


static func t(schluessel: String) -> String:
	_lade()
	var texte: Dictionary = _daten.get("texte", {}) as Dictionary
	if not texte.has(schluessel):
		push_warning("U3-Text fehlt: %s" % schluessel)
		return "[%s]" % schluessel
	return String(texte[schluessel])


static func schwelle(schluessel: String, ersatz: float = 0.0) -> float:
	_lade()
	var s: Dictionary = _daten.get("schwellen", {}) as Dictionary
	return float(s.get(schluessel, ersatz))
