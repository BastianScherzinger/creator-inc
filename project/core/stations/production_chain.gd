## Die Kette aus Annahme -> Puffer -> Abarbeitung.
##
## Hier steht das zentrale Designprinzip des Spiels in Code (GAME_DESIGN.md 2):
## Der effektive Durchsatz ist das Minimum der Kette. Das schwaechste Glied
## bestimmt alles -- und genau dieses Glied macht die Praesentation sichtbar,
## als Warteschlange oder Stapel.
##
## Deshalb ist `bottleneck()` nicht bloss eine Kennzahl, sondern das
## Steuerungssignal, das dem Spieler das Tutorial ersetzt.
class_name ProductionChain
extends RefCounted

var stations: Dictionary = {}          ## StringName -> StationModel
var transport_faktor: float = 1.0      ## Automatisierung, ab Station 4

var _letzter_engpass: StringName = &""


func _init(station_liste: Array = []) -> void:
	for s in station_liste:
		var modell: StationModel = s
		stations[modell.id] = modell


func station(id: StringName) -> StationModel:
	return stations.get(id) as StationModel


## Der effektive Durchsatz pro Sekunde: das Minimum der Kette,
## anschliessend mit dem Transportfaktor multipliziert.
func effektiver_durchsatz() -> float:
	var minimum: float = INF
	for id in Ids.CHAIN:
		var s: StationModel = stations.get(id) as StationModel
		if s == null:
			continue
		minimum = min(minimum, s.durchsatz())
	if is_inf(minimum):
		return 0.0
	return minimum * transport_faktor


## Welche Station bremst gerade? Bei Gleichstand gewinnt die frueheste in
## Flussrichtung -- der Spieler soll den Stau dort beheben, wo er entsteht.
func bottleneck() -> StringName:
	var minimum: float = INF
	var engpass: StringName = &""
	for id in Ids.CHAIN:
		var s: StationModel = stations.get(id) as StationModel
		if s == null:
			continue
		var d: float = s.durchsatz()
		if d < minimum:
			minimum = d
			engpass = id
	return engpass


## Prueft, ob der Engpass gewechselt hat, und meldet das genau einmal.
## Die Praesentation haengt daran ihre sichtbaren Effekte auf.
func check_bottleneck_changed(bus: EventBus) -> void:
	var jetzt: StringName = bottleneck()
	if jetzt != _letzter_engpass:
		_letzter_engpass = jetzt
		if bus != null and jetzt != &"":
			bus.bottleneck_changed.emit(jetzt)


## Wie viel Leistung liegt brach, weil andere Stationen schneller sind?
## Nuetzlich fuer Debug-Overlay und Balancing: Ein hoher Wert bedeutet,
## dass der Spieler an der falschen Stelle investiert hat.
func ungenutzte_kapazitaet() -> float:
	var eng: float = effektiver_durchsatz() / max(transport_faktor, 0.001)
	var summe: float = 0.0
	for id in Ids.CHAIN:
		var s: StationModel = stations.get(id) as StationModel
		if s == null:
			continue
		summe += max(0.0, s.durchsatz() - eng)
	return summe
