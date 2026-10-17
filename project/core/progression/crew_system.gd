## Crew-Karten: je Station ein Mitarbeiter mit Rang I bis III (Design-Overhaul 15.10.).
##
## Eine Karte wird gegen Geld gekauft und hebt die Leistung ihrer Station um
## einen festen Gesamtfaktor (z. B. 1,10 / 1,20 / 1,35). Freigeschaltet wird sie
## durch eine Bedingung aus den Daten -- meist "Ziel-Kette des Raums fertig" --,
## sonst ab einer Stationsstufe. Das System kennt weder Namen noch Portraets
## (die stehen im Thema), nur IDs, Preise und Faktoren.
##
## Rang n+1 gibt es erst nach Rang n. Der Kern bleibt der Rechner: die Karte
## wirkt ueber `faktor()`, den GameCore in den Faktor der Station einrechnet.
class_name CrewSystem
extends RefCounted

const PFAD_STANDARD: String = "res://data/balance/crew_standard.json"

var _raenge: Dictionary = {}    ## String -> Array[{kosten, faktor}]
var _frei: Dictionary = {}      ## String -> Bedingung (Dictionary); fehlt -> frei_ab_stufe
var _stand: Dictionary = {}     ## String -> int (gekaufter Rang)
var frei_ab_stufe: int = 8
var karte_ab_stufe: int = 4     ## darunter zeigt das Menue keine Crew-Zeile


## `welt_crew`: balance.crew; `stationen`: balance.stationen (fuer basis_kosten);
## `kosten_faktor`: balance.crew_kosten_faktor (Regler fuer alle Preise der Welt).
func _init(welt_crew: Dictionary = {}, stationen: Dictionary = {}, kosten_faktor: float = 1.0, standard: Dictionary = {}) -> void:
	var std: Dictionary = standard if not standard.is_empty() else lade_standard()
	frei_ab_stufe = int(std.get("frei_ab_stufe", frei_ab_stufe))
	karte_ab_stufe = int(std.get("karte_ab_stufe", karte_ab_stufe))
	var std_raenge: Array = std.get("raenge", []) as Array
	for id in Ids.ALL_STATIONS:
		var schluessel: String = String(id)
		if not stationen.has(schluessel):
			continue
		var eigen: Dictionary = welt_crew.get(schluessel, {}) as Dictionary
		var liste: Array = []
		if not (eigen.get("raenge", []) as Array).is_empty():
			for r in (eigen["raenge"] as Array):
				liste.append({"kosten": float((r as Dictionary).get("kosten", 0.0)) * kosten_faktor,
					"faktor": float((r as Dictionary).get("faktor", 1.0))})
		else:
			var basis: float = float((stationen[schluessel] as Dictionary).get("basis_kosten", 0.0))
			for r in std_raenge:
				liste.append({"kosten": basis * float((r as Dictionary).get("kosten_x_basis", 0.0)) * kosten_faktor,
					"faktor": float((r as Dictionary).get("faktor", 1.0))})
		_raenge[schluessel] = liste
		if eigen.has("frei"):
			_frei[schluessel] = eigen["frei"] as Dictionary


static func lade_standard() -> Dictionary:
	if not FileAccess.file_exists(PFAD_STANDARD):
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(PFAD_STANDARD))
	return roh as Dictionary if roh is Dictionary else {}


func hat(station_id: StringName) -> bool:
	return not (_raenge.get(String(station_id), []) as Array).is_empty()


func max_rang(station_id: StringName) -> int:
	return (_raenge.get(String(station_id), []) as Array).size()


func rang(station_id: StringName) -> int:
	return int(_stand.get(String(station_id), 0))


func ist_max(station_id: StringName) -> bool:
	return rang(station_id) >= max_rang(station_id)


## Gesamtfaktor auf die Station beim aktuellen Rang (1.0 ohne Karte).
func faktor(station_id: StringName) -> float:
	return faktor_bei(station_id, rang(station_id))


func faktor_bei(station_id: StringName, bei_rang: int) -> float:
	if bei_rang <= 0:
		return 1.0
	var liste: Array = _raenge.get(String(station_id), []) as Array
	if liste.is_empty():
		return 1.0
	return float((liste[mini(bei_rang, liste.size()) - 1] as Dictionary).get("faktor", 1.0))


## Die Rang-Liste einer Station: [{kosten, faktor}] in Reihenfolge.
func raenge(station_id: StringName) -> Array:
	return _raenge.get(String(station_id), []) as Array


## Preis des naechsten Rangs, 0.0 wenn es keinen gibt.
func kosten_naechster(station_id: StringName) -> float:
	if ist_max(station_id):
		return 0.0
	return float(((_raenge[String(station_id)] as Array)[rang(station_id)] as Dictionary).get("kosten", 0.0))


## Freischaltbedingung der Station oder ein leeres Dictionary (dann: frei_ab_stufe).
func frei_bedingung(station_id: StringName) -> Dictionary:
	return _frei.get(String(station_id), {}) as Dictionary


## Setzt den Rang um eins hoch. Bezahlen und Pruefen macht der Kern.
func erhoehe(station_id: StringName) -> bool:
	if not hat(station_id) or ist_max(station_id):
		return false
	_stand[String(station_id)] = rang(station_id) + 1
	return true


func anzahl_gekauft() -> int:
	var summe: int = 0
	for schluessel in _stand.keys():
		summe += int(_stand[schluessel])
	return summe


func to_dict() -> Dictionary:
	var d: Dictionary = {}
	for schluessel in _stand.keys():
		if int(_stand[schluessel]) > 0:
			d[String(schluessel)] = int(_stand[schluessel])
	return d


func apply_dict(d: Dictionary) -> void:
	_stand.clear()
	for schluessel in d.keys():
		var id := StringName(String(schluessel))
		if hat(id):
			_stand[String(schluessel)] = clampi(int(d[schluessel]), 0, max_rang(id))
