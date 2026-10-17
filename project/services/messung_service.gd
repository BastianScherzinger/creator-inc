## Lokale Messung fuer Handytests und die A/B-Auswertung (K3 C3).
##
## Schreibt ausschliesslich nach user://messung.json. Kein Netz, kein
## Personenbezug: keine Geraete-ID, keine Uhrzeit, nur Sekunden seit dem Start
## der Sitzung und die Welt. Die Datei ist ein Ringpuffer -- erreicht sie eine
## Grenze aus data/services/messung.json, fallen die aeltesten Ereignisse weg.
##
## Die Uhr ist austauschbar (`uhr`), damit Tests ohne SceneTree-Frames laufen;
## geschrieben wird gedrosselt ueber `tick()` und beim Sitzungsende.
class_name MessungService
extends RefCounted

const PFAD: String = "user://messung.json"
const GRENZEN_PFAD: String = "res://data/services/messung.json"

## Liefert Millisekunden; Tests ersetzen sie.
var uhr: Callable = func() -> int: return Time.get_ticks_msec()
var pfad: String = PFAD
var aktiv: bool = true

var _grenzen: Dictionary = {}
var _sitzungen: Array = []
var _sitzung: Dictionary = {}
var _gesamt: int = 0
var _start_ms: int = 0
var _erster_tipp_gemeldet: bool = false
var _schmutzig: bool = false
var _rest: float = 0.0


func _init(datei: String = PFAD, grenzen: Dictionary = {}) -> void:
	pfad = datei
	_grenzen = grenzen if not grenzen.is_empty() else lade_grenzen()
	aktiv = bool(_grenzen.get("aktiv", true))
	_lese_vorhandene()


static func lade_grenzen() -> Dictionary:
	if not FileAccess.file_exists(GRENZEN_PFAD):
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(GRENZEN_PFAD))
	return roh as Dictionary if roh is Dictionary else {}


## Beginnt eine neue Sitzung. `ab` = aktive A/B-Varianten {schirm: "a"|"b"}.
func starte(welt: String, ab: Dictionary, start_args: String = "") -> void:
	if not aktiv:
		return
	var nummer: int = 1
	for s in _sitzungen:
		nummer = maxi(nummer, int((s as Dictionary).get("sitzung", 0)) + 1)
	_start_ms = int(uhr.call())
	_erster_tipp_gemeldet = false
	_sitzung = {"sitzung": nummer, "ab": ab.duplicate(), "args": start_args, "ereignisse": []}
	_sitzungen.append(_sitzung)
	ereignis(&"start", welt, null)


## Ein Ereignis ohne Tipp-Logik. Unbekannte Arten werden verworfen.
func ereignis(art: StringName, welt: String, daten: Variant = null) -> void:
	if not aktiv or _sitzung.is_empty():
		return
	if not (_grenzen.get("ereignisse", []) as Array).has(String(art)):
		push_warning("Messung: unbekanntes Ereignis '%s'" % String(art))
		return
	var stellen: int = int(_grenzen.get("nachkommastellen", 1))
	var t: float = snappedf(float(int(uhr.call()) - _start_ms) / 1000.0, pow(10.0, -float(stellen)))
	var eintrag: Dictionary = {"t": t, "e": String(art), "w": welt}
	if daten != null:
		eintrag["d"] = daten
	(_sitzung["ereignisse"] as Array).append(eintrag)
	_gesamt += 1
	_schmutzig = true
	_kuerze()


## Ein Tipp: meldet beim ersten Tipp der Sitzung zusaetzlich `erster_tipp`.
## `art` ist `tipp_leer`, `tipp_station` oder `tipp_plakette`.
func tipp(art: StringName, welt: String, daten: Variant = null) -> void:
	if not aktiv or _sitzung.is_empty():
		return
	if not _erster_tipp_gemeldet:
		_erster_tipp_gemeldet = true
		ereignis(&"erster_tipp", welt, String(art))
	ereignis(art, welt, daten)


func sitzung_ende(welt: String) -> void:
	ereignis(&"sitzung_ende", welt, null)
	speichere()


## Gedrosseltes Schreiben (alle `speichern_alle_sekunden`), vom Hauptknoten gerufen.
func tick(delta: float) -> void:
	if not aktiv or not _schmutzig:
		return
	_rest += delta
	if _rest >= float(_grenzen.get("speichern_alle_sekunden", 15.0)):
		speichere()


func speichere() -> bool:
	_rest = 0.0
	if not aktiv:
		return false
	var datei := FileAccess.open(pfad, FileAccess.WRITE)
	if datei == null:
		push_warning("Messung: Datei nicht schreibbar (%s)" % pfad)
		return false
	datei.store_string(als_json())
	datei.close()
	_schmutzig = false
	return true


func als_json() -> String:
	return JSON.stringify({"version": int(_grenzen.get("version", 1)), "sitzungen": _sitzungen})


func anzahl_ereignisse() -> int:
	return _gesamt


func anzahl_sitzungen() -> int:
	return _sitzungen.size()


## Alle Ereignisse der laufenden Sitzung (Tests, Debug).
func ereignisse() -> Array:
	return (_sitzung.get("ereignisse", []) as Array).duplicate() if not _sitzung.is_empty() else []


func _lese_vorhandene() -> void:
	if not FileAccess.file_exists(pfad):
		return
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	if not (roh is Dictionary):
		return
	var liste: Variant = (roh as Dictionary).get("sitzungen", [])
	if not (liste is Array):
		return
	for s in liste as Array:
		if s is Dictionary and (s as Dictionary).get("ereignisse") is Array:
			_sitzungen.append(s)
			_gesamt += ((s as Dictionary)["ereignisse"] as Array).size()
	_kuerze()


## Ringpuffer: zuerst zu viele Sitzungen, dann zu viele Ereignisse -- immer von
## den aeltesten her. Die laufende Sitzung bleibt bestehen.
func _kuerze() -> void:
	var max_sitzungen: int = maxi(1, int(_grenzen.get("max_sitzungen", 12)))
	while _sitzungen.size() > max_sitzungen and not is_same(_sitzungen[0], _sitzung):
		_gesamt -= ((_sitzungen[0] as Dictionary)["ereignisse"] as Array).size()
		_sitzungen.remove_at(0)
	var max_ereignisse: int = maxi(1, int(_grenzen.get("max_ereignisse", 3000)))
	while _gesamt > max_ereignisse and not _sitzungen.is_empty():
		var liste: Array = (_sitzungen[0] as Dictionary)["ereignisse"] as Array
		if liste.is_empty():
			if is_same(_sitzungen[0], _sitzung):
				break
			_sitzungen.remove_at(0)
			continue
		liste.remove_at(0)
		_gesamt -= 1
