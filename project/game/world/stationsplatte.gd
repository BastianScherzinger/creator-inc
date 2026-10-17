## Bodenplatte unter einer Station (DESIGN_OVERHAUL 4.4, Paket U5).
##
## Eine flache, abgerundete Platte im Akzent der Welt macht aus einem Moebel eine
## STATION (Eatventure-Prinzip). Gesperrt: grauer gepunkteter Umriss statt Platte.
## Meisterstation (5 Sterne): goldener Rand.
##
## Modelle: assets/stations/gemeinsam/platte.glb und umriss.glb (build_platten.py).
## Die Materialien sind weiss; die Farbe kommt hier per Multiplikation.
class_name Stationsplatte
extends Node3D

const PLATTE: String = "res://assets/stations/gemeinsam/platte.glb"
const UMRISS: String = "res://assets/stations/gemeinsam/umriss.glb"
const GRAU := Color("f1e9d8")   ## Papier-Creme: auf dem dunklen Schleier gesperrter Raeume lesbar

var _platte: Node3D
var _umriss: Node3D
var _rand_mat: StandardMaterial3D
var _flaeche_mat: StandardMaterial3D
var _akzent: Color = Color("3d7bff")


func _init() -> void:
	_platte = _lade(PLATTE)
	_umriss = _lade(UMRISS)
	if _platte != null:
		add_child(_platte)
		_rand_mat = _material(_platte, "platte_rand")
		_flaeche_mat = _material(_platte, "platte_flaeche")
	if _umriss != null:
		add_child(_umriss)
		var m: StandardMaterial3D = _material(_umriss, "umriss")
		if m != null:
			m.albedo_color = GRAU
		_umriss.visible = false
	# Leicht unter dem Ring (y 0,03) und den Moebeln, aber ueber dem Boden.
	position = Vector3.ZERO


func _lade(pfad: String) -> Node3D:
	if not ResourceLoader.exists(pfad):
		push_warning("Plattenmodell fehlt: %s" % pfad)
		return null
	return (load(pfad) as PackedScene).instantiate() as Node3D


## Eigene Materialkopie, damit nicht alle Stationen dieselbe Farbe teilen.
func _material(wurzel: Node, name: String) -> StandardMaterial3D:
	for kind in _alle_meshes(wurzel):
		var mesh: Mesh = kind.mesh
		for i in range(mesh.get_surface_count()):
			var m: Material = kind.get_active_material(i)
			if m != null and m.resource_name == name and m is StandardMaterial3D:
				var kopie: StandardMaterial3D = (m as StandardMaterial3D).duplicate() as StandardMaterial3D
				kind.set_surface_override_material(i, kopie)
				return kopie
	return null


func _alle_meshes(wurzel: Node) -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	if wurzel is MeshInstance3D:
		out.append(wurzel as MeshInstance3D)
	for k in wurzel.get_children():
		out.append_array(_alle_meshes(k))
	return out


func setze_akzent(akzent: Color) -> void:
	_akzent = akzent
	if _rand_mat != null:
		_rand_mat.albedo_color = _stufen_farbe as Color if _stufen_farbe != null else akzent
	if _flaeche_mat != null:
		# Hell getoente Flaeche statt kaltem Weiss: ruhiger, bleibt als Platte lesbar.
		_flaeche_mat.albedo_color = akzent.lerp(Color("fff7ea"), 0.62)


func setze_gesperrt(gesperrt: bool) -> void:
	if _platte != null:
		_platte.visible = not gesperrt
	if _umriss != null:
		_umriss.visible = gesperrt


## Meisterstation: goldener Rand.
func setze_meister(meister: bool) -> void:
	if _rand_mat != null:
		if _stufen_farbe != null and not meister:
			_rand_mat.albedo_color = _stufen_farbe as Color
			return
		_rand_mat.albedo_color = Color("ffc21a") if meister else _akzent


## Stufen-Optik (K3 A1 "Buehne"): keine Knoepfe, keine Wimpel. Die Stufe steht
## nur in der Randfarbe (Akzent, Silber ab 3 Sternen, Gold ab 5 bzw. als
## Meister) und in der Plattengroesse. So sieht man die Stufe ohne Panel.
var _sterne_letzt: Vector2i = Vector2i(-1, -1)

const GOLD := Color("ffc21a")
const SILBER := Color("cfd8e3")
const BUEHNE_GROESSE: float = 1.25       ## Platte +25 % gegenueber dem Modell
const BUEHNE_WACHSTUM: float = 1.10      ## ab 3 Sternen noch einmal +10 %
const STERNE_SILBER: int = 3
const STERNE_GOLD: int = 5

var _stufen_farbe: Variant = null        ## Randfarbe der Stufe, null = Akzent


func setze_sterne(sterne: int, moeglich: int) -> void:
	# Der Akzent steht erst nach dem Bau fest (Hud meldet die Welt spaeter).
	setze_akzent(UiStil.akzent())
	setze_meister(moeglich > 0 and sterne >= moeglich)
	var schluessel := Vector2i(sterne, moeglich)
	if schluessel == _sterne_letzt:
		return
	_sterne_letzt = schluessel
	_setze_stufe(sterne, moeglich)


## Plattenfaktor und Randfarbe einer Stufe (rein, damit testbar).
static func buehne_stufe(sterne: int, moeglich: int) -> Dictionary:
	var meister: bool = moeglich > 0 and sterne >= moeglich
	var farbe: Variant = null
	if meister or sterne >= STERNE_GOLD:
		farbe = GOLD
	elif sterne >= STERNE_SILBER:
		farbe = SILBER
	var faktor: float = BUEHNE_GROESSE * (BUEHNE_WACHSTUM if sterne >= STERNE_SILBER else 1.0)
	return {"faktor": faktor, "farbe": farbe}


func _setze_stufe(sterne: int, moeglich: int) -> void:
	var stufe: Dictionary = buehne_stufe(sterne, moeglich)
	_stufen_farbe = stufe["farbe"]
	var f: float = float(stufe["faktor"])
	if _platte != null:
		_platte.scale = Vector3(f, 1.0, f)
	if _umriss != null:
		_umriss.scale = Vector3(f, 1.0, f)
	if _rand_mat != null:
		_rand_mat.albedo_color = _stufen_farbe as Color if _stufen_farbe != null else _akzent


## Der Welt-Akzent wird von der Hud erst nach dem Bau gesetzt -- nachziehen.
func _process(_delta: float) -> void:
	var a: Color = UiStil.akzent()
	if a != _akzent:
		setze_akzent(a)
		setze_meister(_sterne_letzt.y > 0 and _sterne_letzt.x >= _sterne_letzt.y)
		_sterne_letzt = Vector2i(-1, -1)
