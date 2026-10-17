## Das Tagesgeschenk: ein Geschenk je Kalendertag, eine Serie bis zu sieben Tagen.
##
## Reine Daten und Regeln, ohne Uhr: Der Kalendertag kommt als Zahl von aussen
## (`heute()` liefert ihn fuer das echte Spiel, Tests geben ihn selbst vor).
##
## Serie: Wer am Tag nach der letzten Abholung kommt, setzt die Serie fort
## (Faktor steigt). Wer einen Tag auslaesst, faengt bei Tag 1 wieder an --
## ohne Strafe, nur ohne Bonus. Nach dem letzten Serientag beginnt die Serie
## von vorn. Ein Tag, der VOR dem letzten liegt (Uhr zurueckgestellt), gibt
## nichts: sonst liesse sich das Geschenk durch Datum-Drehen vervielfachen.
##
## Der Betrag selbst wird vom Kern berechnet (er kennt das Einkommen).
class_name Tagesgeschenk
extends RefCounted

const PFAD: String = "res://data/balance/geschenk.json"

var sekunden: float = 600.0
var minimum: float = 100.0
var serie_faktoren: Array[float] = [1.0]

## Zuletzt abgeholter Serientag (1..n), 0 = noch nie abgeholt.
var serientag: int = 0

## Kalendertag der letzten Abholung (Tage seit 1970, lokal), 0 = nie.
var letzter_tag: int = 0


func _init(daten: Dictionary = {}) -> void:
	var roh: Dictionary = daten
	if roh.is_empty():
		roh = lade_roh()
	var t: Dictionary = roh.get("tagesgeschenk", {}) as Dictionary
	sekunden = float(t.get("sekunden", sekunden))
	minimum = float(t.get("minimum", minimum))
	var liste: Array = t.get("serie_faktoren", []) as Array
	if not liste.is_empty():
		serie_faktoren.clear()
		for f in liste:
			serie_faktoren.append(float(f))


static func lade_roh() -> Dictionary:
	if not FileAccess.file_exists(PFAD):
		return {}
	var text: String = FileAccess.get_file_as_string(PFAD)
	var roh: Variant = JSON.parse_string(text)
	return roh as Dictionary if roh is Dictionary else {}


## Der heutige Kalendertag (lokale Zeit), als Tage seit 1970.
static func heute() -> int:
	var lokal: float = Time.get_unix_time_from_system() \
		+ float(Time.get_time_zone_from_system().get("bias", 0)) * 60.0
	return int(floor(lokal / 86400.0))


func tage_in_serie() -> int:
	return serie_faktoren.size()


## Ist an diesem Tag ein Geschenk abzuholen?
func verfuegbar(tag: int) -> bool:
	return tag > letzter_tag


## Welcher Serientag (1..n) wuerde an diesem Tag abgeholt?
func naechster_serientag(tag: int) -> int:
	if letzter_tag <= 0 or serientag <= 0:
		return 1
	if tag == letzter_tag + 1 and serientag < tage_in_serie():
		return serientag + 1
	return 1


func faktor_fuer(tag_in_serie: int) -> float:
	var i: int = clampi(tag_in_serie - 1, 0, serie_faktoren.size() - 1)
	return serie_faktoren[i]


## Verbucht die Abholung. Gibt den abgeholten Serientag zurueck, 0 wenn nichts da war.
func abholen(tag: int) -> int:
	if not verfuegbar(tag):
		return 0
	var abgeholt: int = naechster_serientag(tag)
	serientag = abgeholt
	letzter_tag = tag
	return abgeholt


func to_dict() -> Dictionary:
	return {"serientag": serientag, "letzter_tag": letzter_tag}


func apply_dict(daten: Dictionary) -> void:
	serientag = maxi(int(daten.get("serientag", 0)), 0)
	letzter_tag = maxi(int(daten.get("letzter_tag", 0)), 0)
