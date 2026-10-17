## Eine Station mit sichtbarer Ausstattung (ADR-021).
##
## Statt drei Gesamtmodellen je Stufe: EIN Grundmodell plus drei Plaetze, deren
## Modelle einzeln wechseln. Wer den Monitor kauft, sieht den Monitor erscheinen
## -- nicht einen anderen Schreibtisch. Alle Dateien einer Station haben
## denselben Ursprung, jedes Teil liegt schon an seinem Platz.
##
## Dieselbe oeffentliche Schnittstelle wie StationView, damit main.gd beide
## Arten gleich behandelt.
class_name AusstattungsStation
extends Node3D

const PFAD: String = "res://assets/stations/%s/%s.glb"
const FARBE_ENGPASS := Color("e5533c")
const FARBE_AUSWAHL := Color("ffb21e")
## Limette wie der Kaufen-Knopf (UiStil.KAUFEN): "Hier kannst du jetzt kaufen."
const FARBE_KAUFEN := Color("b6f03c")
const KAUFEN_HZ: float = 1.2
## Deckkraft des ruhigen Limetten-Rings (bezahlbar, aber nicht der empfohlene Kauf).
const KAUFEN_RUHIG: float = 0.6

var station_id: StringName
var _welt: String = ""
var _basis: Node3D
var _plaetze: Dictionary = {}          ## platz_id -> Array[Node3D] (Index = Modellstufe)
var _ring: MeshInstance3D
var _ring_material: StandardMaterial3D
var _ist_engpass: bool = false
var _upgrade: bool = false
## Diese Station ist DER empfohlene naechste Kauf: nur dann pulsiert der Ring (K4 P1.3).
var _puls: bool = false
var _gesperrt: bool = false
var _zeit: float = 0.0
var _schleier: StandardMaterial3D
var _platte: Stationsplatte


func aufbauen(id: StringName, position_welt: Vector3, welt_id: String, platz_ids: Array[StringName] = []) -> void:
	station_id = id
	position = position_welt
	_welt = welt_id

	_basis = _lade("%s_basis" % String(id))
	if _basis != null:
		add_child(_basis)

	for platz_id in platz_ids:
		var stufen: Array[Node3D] = []
		for m in range(4):
			var teil: Node3D = _lade("%s_%s_%d" % [String(id), String(platz_id), m], m > 0)
			if teil != null:
				teil.visible = false
				add_child(teil)
			stufen.append(teil)
		_plaetze[platz_id] = stufen

	# Ring am Boden: rot und atmend am Engpass, kurz gelb beim Antippen.
	_ring_material = StandardMaterial3D.new()
	_ring_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_ring_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_ring_material.albedo_color = Color(FARBE_ENGPASS, 0.0)
	var torus := TorusMesh.new()
	# Der Ring bleibt INNERHALB der 2,2-m-Flaeche der Station. Mit 1,22 m griff er
	# auf die Nachbarstation ueber und schien sie zu umschliessen (Review Welt 1-4).
	torus.inner_radius = 0.9
	torus.outer_radius = 1.04
	torus.rings = 32
	torus.ring_segments = 4
	_ring = MeshInstance3D.new()
	_ring.mesh = torus
	_ring.material_override = _ring_material
	_ring.scale = Vector3(1.0, 0.05, 1.0)
	_ring.position = Vector3(0.0, 0.03, 0.0)
	_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_ring)

	# U5: Bodenplatte macht die Station als Station lesbar (ov_wuensche_u5_an_u1.md).
	_platte = Stationsplatte.new()
	_platte.setze_akzent(UiStil.akzent())
	add_child(_platte)
	move_child(_platte, 0)

	_schleier = StandardMaterial3D.new()
	_schleier.albedo_color = Color(0.13, 0.15, 0.22, 0.74)
	_schleier.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_schleier.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_schleier.render_priority = 1


func _lade(name: String, pflicht: bool = true) -> Node3D:
	var pfad: String = PFAD % [_welt, name]
	if not ResourceLoader.exists(pfad):
		if pflicht:
			push_warning("Stationsmodell fehlt: %s" % pfad)
		return null
	return (load(pfad) as PackedScene).instantiate() as Node3D


## Die Stufe veraendert hier nichts am Modell -- sichtbar ist die Ausstattung.
func setze_stufe(_stufe: int) -> void:
	pass


func setze_ausstattung(platz_id: StringName, modellstufe: int, mit_auftritt: bool = false) -> void:
	var stufen: Array = _plaetze.get(platz_id, []) as Array
	var neu: Node3D = null
	for m in range(stufen.size()):
		var teil: Node3D = stufen[m] as Node3D
		if teil == null:
			continue
		var sichtbar: bool = m == modellstufe
		if sichtbar and not teil.visible:
			neu = teil
		teil.visible = sichtbar
	if neu != null and mit_auftritt:
		# Das neue Teil faellt von oben an seinen Platz und federt nach.
		var ziel_y: float = neu.position.y
		neu.position.y = ziel_y + 1.2
		neu.scale = Vector3(0.6, 0.6, 0.6)
		var t := create_tween().set_parallel(true)
		t.tween_property(neu, "position:y", ziel_y, 0.45).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		t.tween_property(neu, "scale", Vector3.ONE, 0.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		_funken()


## Setzt den Ring unter die sichtbare Mitte des Modells (worlds.json "schild").
func setze_ring_versatz(versatz: Vector3) -> void:
	if _ring != null:
		_ring.position = Vector3(versatz.x, 0.03, versatz.z)
	if _platte != null:
		_platte.position = Vector3(versatz.x, 0.0, versatz.z)


func setze_gesperrt(gesperrt: bool) -> void:
	_gesperrt = gesperrt
	if _platte != null:
		_platte.setze_akzent(UiStil.akzent())
		_platte.setze_gesperrt(gesperrt)
	_schleier_auf(self, gesperrt)


func setze_engpass(ist_engpass: bool) -> void:
	_ist_engpass = ist_engpass


## Sterne der Station: bei allen moeglichen Sternen (Meisterstation) wird die
## Bodenplatte golden. main.gd ruft das mit station.sterne() auf.
func setze_sterne(sterne: int, moeglich: int) -> void:
	if _platte != null:
		_platte.setze_meister(moeglich > 0 and sterne >= moeglich)
		_platte.setze_sterne(sterne, moeglich)


## Ein Kauf ist bezahlbar: Der Ring leuchtet ruhig in Limette und geht vor dem
## roten Engpass-Ring -- das Rot sagt WO es klemmt, die Limette "kauf jetzt".
## Pulsieren (1,2 Hz) darf nur der EINE empfohlene Kauf (`puls`, K4 P1.3).
func setze_upgrade(an: bool, puls: bool = false) -> void:
	_upgrade = an
	_puls = an and puls


func erscheinen() -> void:
	setze_gesperrt(false)
	scale = Vector3(0.7, 0.05, 0.7)
	var t := create_tween()
	t.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(self, "scale", Vector3.ONE, 0.55)
	_funken()


func blitzen() -> void:
	_ring_material.albedo_color = Color(FARBE_AUSWAHL, 0.95)
	_zeit = -0.25


## Kurzes Aufhuepfen beim Stufenkauf.
func huepfen() -> void:
	if _basis == null:
		return
	var t := create_tween()
	t.tween_property(_basis, "scale", Vector3(1.06, 0.92, 1.06), 0.08)
	t.tween_property(_basis, "scale", Vector3.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_funken()


func _process(delta: float) -> void:
	_zeit += delta
	if _zeit < 0.0:
		return
	var alpha: float = 0.0
	var ring_farbe: Color = FARBE_ENGPASS
	if _upgrade and not _gesperrt:
		ring_farbe = FARBE_KAUFEN
		if _puls:
			alpha = 0.55 + 0.4 * sin(_zeit * TAU * KAUFEN_HZ)
			# Der Ring atmet auch in der Groesse: 1,0 -> 1,08 (UiStil.PULS_SKALA).
			var puls: float = 1.0 + (UiStil.PULS_SKALA - 1.0) * (0.5 + 0.5 * sin(_zeit * TAU * UiStil.PULS_HZ))
			_ring.scale = Vector3(puls, 0.05, puls)
		else:
			alpha = KAUFEN_RUHIG
			_ring.scale = Vector3(1.0, 0.05, 1.0)
	elif _ist_engpass and not _gesperrt:
		alpha = 0.45 + 0.35 * sin(_zeit * 4.0)
		_ring.scale = Vector3(1.0, 0.05, 1.0)
	else:
		_ring.scale = Vector3(1.0, 0.05, 1.0)
	var farbe: Color = _ring_material.albedo_color
	var ziel := Color(ring_farbe, alpha)
	_ring_material.albedo_color = farbe.lerp(ziel, clampf(delta * 10.0, 0.0, 1.0))


func _schleier_auf(wurzel: Node, an: bool) -> void:
	if wurzel is GeometryInstance3D and wurzel != _ring:
		(wurzel as GeometryInstance3D).material_overlay = _schleier if an else null
	for kind in wurzel.get_children():
		_schleier_auf(kind, an)


func _funken() -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 24
	p.lifetime = 0.8
	p.explosiveness = 1.0
	p.direction = Vector3.UP
	p.spread = 70.0
	p.initial_velocity_min = 2.0
	p.initial_velocity_max = 4.0
	p.gravity = Vector3(0.0, -7.0, 0.0)
	p.scale_amount_min = 0.06
	p.scale_amount_max = 0.14
	var mesh := BoxMesh.new()
	mesh.size = Vector3.ONE
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_color = Color("ffd23e")
	mesh.material = mat
	p.mesh = mesh
	p.position = Vector3(0.0, 1.0, 0.0)
	add_child(p)
	p.emitting = true
	get_tree().create_timer(1.5).timeout.connect(p.queue_free)
