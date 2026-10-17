## Leben fuer die Figuren: Wippen, Kopfdrehen und Jubel.
##
## Die Figuren standen stumm da. Jetzt atmen sie im Takt (Wippen auf der
## Koerperskalierung), schauen sich langsam um (Kopfdrehung) und freuen sich,
## wenn an ihrer Station gekauft wird: Sprung, Arme hoch, Landung mit Stauchung.
##
## Figuren erzeugen kein Geld (ADR-007) -- hier wird nur dargestellt.
##
## Hoheitsgrenzen: Die Wurzel jeder Figur gehoert main.gd (Erscheinen) bzw.
## Bewohner (Laufweg). FigurLeben fasst nur `koerper`, `kopf` und die Arme an,
## und diese erst NACH ihren Besitzern (Reihenfolge im Baum), damit der Jubel
## das Gehen und Atmen kurz uebersteuert.
class_name FigurLeben
extends Node3D

const WIPP_HZ: float = 1.6
const WIPP_STAERKE: float = 0.025
const KOPF_HZ: float = 0.18
const KOPF_WINKEL: float = 0.38
const JUBEL_HOEHE: float = 0.3
const JUBEL_DAUER: float = 0.45
const ARME_HOCH: float = -2.7
const STAUCHUNG: float = 0.12
const STATION_RADIUS: float = 3.2

var _eintraege: Array[Dictionary] = []
var _stationen: Dictionary = {}
var _zeit: float = 0.0


func aufbauen(figuren: Array[Node3D], bus: EventBus, stationen: Dictionary) -> void:
	_eintraege.clear()
	_stationen = stationen
	for i in range(figuren.size()):
		var figur: Node3D = figuren[i]
		if figur == null or not is_instance_valid(figur):
			continue
		var koerper: Node3D = figur.find_child("koerper", true, false) as Node3D
		if koerper == null:
			continue
		_eintraege.append({
			"figur": figur,
			"koerper": koerper,
			"kopf": figur.find_child("kopf", true, false),
			"arm_l": figur.find_child("arm_l", true, false),
			"arm_r": figur.find_child("arm_r", true, false),
			"basis_y": koerper.position.y,
			"phase": float(i) * 1.7,
			"jubel": -1.0,
			"hops": 1,
			"verzoegerung": 0.0,
		})
	if bus != null:
		if not bus.station_upgraded.is_connected(_auf_stufe):
			bus.station_upgraded.connect(_auf_stufe)
		if not bus.equipment_upgraded.is_connected(_auf_platz):
			bus.equipment_upgraded.connect(_auf_platz)


## Jubel aller Figuren in `radius` Metern um einen Weltpunkt (Raumkauf).
func jubel_an(position_welt: Vector3, radius: float) -> void:
	var n: int = 0
	for e in _eintraege:
		var figur: Node3D = e["figur"] as Node3D
		if not _lebt(figur):
			continue
		if Vector2(figur.global_position.x - position_welt.x, figur.global_position.z - position_welt.z).length() <= radius:
			_starte(e, 1, float(n) * 0.07)
			n += 1


## Alle springen, gestaffelt (Weltabschluss, ca. 2 s).
func jubel_alle() -> void:
	var n: int = 0
	for e in _eintraege:
		if _lebt(e["figur"] as Node3D):
			_starte(e, 4, float(n) * 0.09)
			n += 1


## Alle Figuren an einer Station freuen sich.
func jubel_station(station_id: StringName) -> void:
	if _stationen.has(station_id):
		jubel_an(_stationen[station_id] as Vector3, STATION_RADIUS)


func _auf_stufe(station_id: StringName, _stufe: int) -> void:
	jubel_station(station_id)


func _auf_platz(station_id: StringName, _platz: StringName, _stufe: int) -> void:
	jubel_station(station_id)


func _lebt(figur: Node3D) -> bool:
	return figur != null and is_instance_valid(figur) and figur.is_inside_tree() and figur.visible


func _starte(e: Dictionary, hops: int, verzoegerung: float) -> void:
	e["hops"] = hops
	e["jubel"] = 0.0
	e["verzoegerung"] = verzoegerung


func _process(delta: float) -> void:
	_zeit += delta
	for e in _eintraege:
		var figur: Node3D = e["figur"] as Node3D
		if figur == null or not is_instance_valid(figur):
			continue
		if not figur.visible:
			continue
		var koerper: Node3D = e["koerper"] as Node3D
		var phase: float = float(e["phase"])
		var jubel: float = float(e["jubel"])
		var kopf: Node3D = e["kopf"] as Node3D
		if kopf != null:
			kopf.rotation.y = sin(_zeit * KOPF_HZ * TAU + phase) * KOPF_WINKEL
		var stauchung: float = 0.0
		if jubel >= 0.0:
			if float(e["verzoegerung"]) > 0.0:
				e["verzoegerung"] = float(e["verzoegerung"]) - delta
			else:
				jubel += delta
				e["jubel"] = jubel
				var gesamt: float = JUBEL_DAUER * float(e["hops"])
				if jubel >= gesamt:
					e["jubel"] = -1.0
					koerper.position.y = float(e["basis_y"])
					_arme(e, 0.0, false)
				else:
					var f: float = fmod(jubel, JUBEL_DAUER) / JUBEL_DAUER
					# Hoch mit Schwung, runter mit Gewicht; vor der Landung Stauchung.
					koerper.position.y = float(e["basis_y"]) + JUBEL_HOEHE * sin(PI * f)
					stauchung = STAUCHUNG * maxf(0.0, (f - 0.82) / 0.18) + STAUCHUNG * maxf(0.0, 1.0 - f / 0.12) * 0.5
					_arme(e, ARME_HOCH * minf(1.0, jubel / 0.12), true)
		koerper.scale.y = 1.0 + WIPP_STAERKE * sin(_zeit * WIPP_HZ * TAU + phase) - stauchung
		koerper.scale.x = 1.0 + stauchung * 0.5
		koerper.scale.z = 1.0 + stauchung * 0.5


func _arme(e: Dictionary, winkel: float, aktiv: bool) -> void:
	if not aktiv:
		return
	for name in ["arm_l", "arm_r"]:
		var arm: Node3D = e[name] as Node3D
		if arm != null:
			arm.rotation.x = winkel
