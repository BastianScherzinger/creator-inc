## Eine Figur, die ihren Tagesablauf durch die Karte laeuft (ADR-021, WELT1_TIEFE 3.5).
##
## Mira geht vom Schreibtisch ins Bad, in die Kueche und zurueck. Tobi kocht und
## sitzt auf dem Balkon -- bis er auszieht. Die Wege stehen in worlds.json als
## Punktfolgen durch die Tueren; hier steht nur, wie man sie ablaeuft.
##
## Figuren erzeugen kein Geld (ADR-007). Sie erzaehlen, dass hier Menschen wohnen.
class_name Bewohner
extends Node3D

const TEMPO: float = 1.25          ## Meter pro Sekunde
const DREH_TEMPO: float = 9.0

var _route: Array = []
var _index: int = 0
var _warten: float = 0.0
var _zeit: float = 0.0
var _modell: Node3D
var _koerper: Node3D
var _arme: Array[Node3D] = []
var _beine: Array[Node3D] = []
var _ziel_winkel: float = 0.0
var _laeuft: bool = false


func aufbauen(pfad: String, route: Array, startversatz: int = 0) -> bool:
	if not ResourceLoader.exists(pfad) or route.is_empty():
		return false
	_modell = (load(pfad) as PackedScene).instantiate() as Node3D
	add_child(_modell)
	_koerper = _modell.find_child("koerper", true, false) as Node3D
	for name in ["arm_l", "arm_r"]:
		var t: Node3D = _modell.find_child(name, true, false) as Node3D
		if t != null:
			_arme.append(t)
	for name in ["bein_l", "bein_r"]:
		var t: Node3D = _modell.find_child(name, true, false) as Node3D
		if t != null:
			_beine.append(t)
	_route = route
	_index = startversatz % route.size()
	position = _punkt(_index)
	_warten = float((route[_index] as Dictionary).get("warten", 0.0)) * 0.5
	_zeit = randf() * 10.0
	return true


func _punkt(i: int) -> Vector3:
	var p: Dictionary = _route[i] as Dictionary
	return Vector3(float(p.get("x", 0.0)), 0.0, float(p.get("z", 0.0)))


func _process(delta: float) -> void:
	if _route.is_empty() or not visible:
		return
	_zeit += delta
	if _warten > 0.0:
		_warten -= delta
		_laeuft = false
		var halt: Dictionary = _route[_index] as Dictionary
		if halt.has("blick"):
			_ziel_winkel = deg_to_rad(float(halt["blick"]))
	else:
		var naechster: int = (_index + 1) % _route.size()
		var ziel: Vector3 = _punkt(naechster)
		var weg: Vector3 = ziel - position
		var schritt: float = TEMPO * delta
		if weg.length() <= schritt:
			position = ziel
			_index = naechster
			_warten = float((_route[_index] as Dictionary).get("warten", 0.0))
		else:
			position += weg.normalized() * schritt
			_ziel_winkel = atan2(weg.x, weg.z)
			_laeuft = true
	rotation.y = lerp_angle(rotation.y, _ziel_winkel, clampf(delta * DREH_TEMPO, 0.0, 1.0))
	_bewege_glieder()


func _bewege_glieder() -> void:
	var schwung: float = sin(_zeit * 9.0) * 0.45 if _laeuft else 0.0
	for i in range(_beine.size()):
		_beine[i].rotation.x = schwung * (1.0 if i == 0 else -1.0)
	for i in range(_arme.size()):
		_arme[i].rotation.x = -schwung * 0.7 * (1.0 if i == 0 else -1.0)
	if _koerper != null:
		# Beim Gehen ein leichtes Wippen, im Stehen ein langsames Atmen.
		_koerper.position.y = _koerper_basis_y() + (absf(sin(_zeit * 9.0)) * 0.035 if _laeuft else sin(_zeit * 1.8) * 0.006)


var _basis_y: float = -1.0

func _koerper_basis_y() -> float:
	if _basis_y < 0.0 and _koerper != null:
		_basis_y = _koerper.position.y
	return _basis_y
