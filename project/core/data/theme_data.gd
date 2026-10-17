## Laedt die Anzeigetexte aus data/themes/<name>/theme.json.
##
## Diese Klasse ist die Bruecke ueber die Guardrail D3 (ADR-010): Systeme
## sprechen ueber neutrale IDs, die Oberflaeche fragt hier nach dem Text.
##
## In dieser Datei steht KEIN einziger thematischer Begriff -- sie kennt nur
## Schluessel und Pfade. Genau deshalb ist ein Themenwechsel eine
## Datenaenderung geblieben und kein Rewrite.
class_name ThemeData
extends RefCounted

const BASIS_PFAD: String = "res://data/themes/%s/theme.json"
const STANDARD: String = "zimmer"

## Ersatzthema fuer Welten, deren Texte noch nicht geschrieben sind.
const ERSATZ: String = "neutral"

var id: String = ""
var welt_name: String = ""
var welt_untertitel: String = ""
var waehrung: String = ""

var _stationen: Dictionary = {}
var _upgrades: Dictionary = {}
var _npc_typen: Dictionary = {}
var _sonstiges: Dictionary = {}


## Faellt auf ein NEUTRALES Thema zurueck, wenn eine Welt noch keine Texte hat.
##
## BAUGERUEST, kein Dauerzustand -- dieselbe Ueberlegung wie bei den
## Stationsmodellen: Ohne Ersatz liesse sich eine Welt erst betreten, wenn
## ihr letzter Satz geschrieben ist. Bei sechs Welten waere das eine Sperre
## gegen die eigene Arbeit: Raum, Kamera, Beleuchtung und Balance einer neuen
## Welt lassen sich lange vor den Texten beurteilen.
##
## Die Warnung ist der Teil, der zaehlt. Sie verhindert, dass ein Platzhalter
## unbemerkt in die Auslieferung rutscht.
static func laden(theme_id: String = STANDARD) -> ThemeData:
	var pfad: String = BASIS_PFAD % theme_id
	if not FileAccess.file_exists(pfad):
		var ersatz: String = BASIS_PFAD % ERSATZ
		if theme_id != ERSATZ and FileAccess.file_exists(ersatz):
			push_warning("Welt '%s' hat noch keine Texte -- es laeuft '%s'"
				% [theme_id, ERSATZ])
			return laden(ERSATZ)
		push_error("Theme nicht gefunden: %s" % pfad)
		return null
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	if roh == null or not (roh is Dictionary):
		push_error("Theme-JSON ungueltig: %s" % pfad)
		return null

	var daten := ThemeData.new()
	var d: Dictionary = roh as Dictionary
	daten.id = String(d.get("id", theme_id))
	daten.welt_name = String(d.get("welt_name", ""))
	daten.welt_untertitel = String(d.get("welt_untertitel", ""))
	daten.waehrung = String(d.get("waehrung", ""))
	daten._stationen = d.get("stationen", {}) as Dictionary
	daten._upgrades = d.get("upgrades", {}) as Dictionary
	daten._npc_typen = d.get("npc_typen", {}) as Dictionary
	daten._sonstiges = d
	return daten


## Die Stationen dieser Welt in der Reihenfolge der Themendatei.
func station_ids() -> Array[StringName]:
	var ids: Array[StringName] = []
	for k in _stationen.keys():
		ids.append(StringName(String(k)))
	return ids


## Anzeigename einer Station. Faellt auf die aufbereitete ID zurueck, damit
## ein fehlender Eintrag sichtbar wird, ohne das Spiel abstuerzen zu lassen.
func station_name(station_id: StringName) -> String:
	var eintrag: Dictionary = _stationen.get(String(station_id), {}) as Dictionary
	var name: String = String(eintrag.get("name", ""))
	if name.is_empty():
		return String(station_id).replace("station_", "").capitalize()
	return name


func station_beschreibung(station_id: StringName) -> String:
	var eintrag: Dictionary = _stationen.get(String(station_id), {}) as Dictionary
	return String(eintrag.get("beschreibung", ""))


## Hinweis, der erscheint, wenn genau diese Station der Engpass ist.
## Das ist die textliche Ergaenzung zum sichtbaren Stau -- nicht sein Ersatz.
func engpass_hinweis(station_id: StringName) -> String:
	var eintrag: Dictionary = _stationen.get(String(station_id), {}) as Dictionary
	return String(eintrag.get("engpass_hinweis", ""))


## Name des naechsten Ausbauschritts einer Station.
## Die Liste wiederholt sich zyklisch -- so hat jedes Upgrade einen Namen,
## ohne dass fuer 150 Stufen 150 Texte geschrieben werden muessen.
func upgrade_name(station_id: StringName, stufe: int) -> String:
	var liste: Array = _upgrades.get(String(station_id), []) as Array
	if liste.is_empty():
		return "Ausbauen"
	return String(liste[stufe % liste.size()])


func npc_name(typ: String) -> String:
	return String(_npc_typen.get(typ, ""))


## Ein ganzer Abschnitt der Themendatei.
##
## `text()` reicht eine Ebene tief. Das Tutorial braucht zwei -- Schritt-ID,
## dann Feld -- und genau dafuer ist das hier da, statt an der Aufrufstelle
## im Dictionary zu wuehlen.
func abschnitt(schluessel: String) -> Dictionary:
	var wert: Variant = _sonstiges.get(schluessel, {})
	return wert as Dictionary if wert is Dictionary else {}


## Ein beliebiger Wert der obersten Ebene (z. B. eine Liste wie "kapitel"); null, wenn er fehlt.
func wert(schluessel: String) -> Variant:
	return _sonstiges.get(schluessel, null)


## Ein Wert aus dem Darstellungsblock "stil" der Themendatei (z. B. die
## Akzentfarbe als Hex-Text). Leer, wenn die Welt keinen hat -- die Oberflaeche
## faellt dann auf ihren Standard zurueck.
func stil(schluessel: String) -> String:
	return String(abschnitt("stil").get(schluessel, ""))


func text(schluessel: String, unterschluessel: String = "") -> String:
	var wert: Variant = _sonstiges.get(schluessel, "")
	if wert is Dictionary and not unterschluessel.is_empty():
		return String((wert as Dictionary).get(unterschluessel, ""))
	return String(wert)
