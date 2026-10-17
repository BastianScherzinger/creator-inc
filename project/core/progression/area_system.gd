## Raeume, die man kauft (ADR-021).
##
## Die Karte ist groesser als das, was dem Spieler gehoert. Am Anfang ist es ein
## Zimmer; der Rest der Wohnung ist sichtbar, aber gesperrt. Ein Bereich ist ein
## EINMALKAUF, der entweder eine Station freischaltet, einen dauerhaften Faktor
## gibt oder beides.
##
## Warum Kauf statt Schwelle: Eine Freischaltung ueber einen Kapitalstand
## passiert dem Spieler. Einen Raum kauft er -- und in dem Moment gehoert er ihm.
## Das ist derselbe Unterschied wie zwischen einem Geschenk und einem Besitz.
##
## Kennt nur neutrale IDs (bereich_1 ...). Was ein Bereich IST, sagt das Thema.
class_name AreaSystem
extends RefCounted

const BONUS_ALLE: String = "alle"

var _definitionen: Dictionary = {}   ## String -> Dictionary, Reihenfolge = Kaufreihenfolge
var _gekauft: Dictionary = {}        ## String -> true


func _init(definitionen: Dictionary = {}) -> void:
	_definitionen = definitionen


func hat_bereiche() -> bool:
	return not _definitionen.is_empty()


func ids() -> Array[StringName]:
	var liste: Array[StringName] = []
	for schluessel in _definitionen.keys():
		liste.append(StringName(String(schluessel)))
	return liste


func anzahl() -> int:
	return _definitionen.size()


func anzahl_gekauft() -> int:
	return _gekauft.size()


func ist_gekauft(bereich_id: StringName) -> bool:
	return _gekauft.has(String(bereich_id))


func existiert(bereich_id: StringName) -> bool:
	return _definitionen.has(String(bereich_id))


func kosten(bereich_id: StringName) -> float:
	return float(_def(bereich_id).get("kosten", 0.0))


## Welcher Bereich muss vorher gekauft sein? Leer, wenn keiner.
##
## Die Voraussetzung ist erzaehlerisch: Das freie Zimmer gibt es erst, wenn
## jemand auszieht. Ein Raum, den man schon kaufen koennte, bevor die
## Geschichte ihn hergibt, waere ein Loch in der Geschichte.
func voraussetzung(bereich_id: StringName) -> StringName:
	return StringName(String(_def(bereich_id).get("nach", "")))


## Kaufbar = noch nicht gekauft und Voraussetzung erfuellt. Ob das Geld
## reicht, entscheidet der Kern -- ein Bereich kennt kein Konto.
func verfuegbar(bereich_id: StringName) -> bool:
	if not existiert(bereich_id) or ist_gekauft(bereich_id):
		return false
	var vorher: StringName = voraussetzung(bereich_id)
	return vorher == &"" or ist_gekauft(vorher)


func schaltet_frei(bereich_id: StringName) -> StringName:
	return StringName(String(_def(bereich_id).get("schaltet_frei", "")))


## Markiert als gekauft. Gibt false zurueck, wenn es nichts zu kaufen gab.
func kaufe(bereich_id: StringName) -> bool:
	if not verfuegbar(bereich_id):
		return false
	_gekauft[String(bereich_id)] = true
	return true


## Setzt ohne Pruefung -- fuer Spielstaende und die Aufwaertskompatibilitaet.
func setze_gekauft(bereich_id: StringName) -> void:
	if existiert(bereich_id):
		_gekauft[String(bereich_id)] = true


## Der Faktor, den alle GEKAUFTEN Bereiche zusammen einer Station geben.
func faktor_fuer(station_id: StringName) -> float:
	var f: float = 1.0
	for schluessel in _gekauft.keys():
		var bonus: Dictionary = _def(StringName(String(schluessel))).get("bonus", {}) as Dictionary
		if bonus.is_empty():
			continue
		var ziel: String = String(bonus.get("ziel", BONUS_ALLE))
		if ziel == BONUS_ALLE or ziel == String(station_id):
			f *= float(bonus.get("faktor", 1.0))
	return f


## Der Faktor, den EIN Bereich geben wuerde -- fuer das Menue und den Simulator.
func bonus(bereich_id: StringName) -> Dictionary:
	return _def(bereich_id).get("bonus", {}) as Dictionary


func anteil() -> float:
	if _definitionen.is_empty():
		return 1.0
	return float(_gekauft.size()) / float(_definitionen.size())


func to_array() -> Array[String]:
	var liste: Array[String] = []
	for schluessel in _gekauft.keys():
		liste.append(String(schluessel))
	return liste


func apply_array(liste: Array) -> void:
	_gekauft.clear()
	for eintrag in liste:
		setze_gekauft(StringName(String(eintrag)))


func _def(bereich_id: StringName) -> Dictionary:
	return _definitionen.get(String(bereich_id), {}) as Dictionary
