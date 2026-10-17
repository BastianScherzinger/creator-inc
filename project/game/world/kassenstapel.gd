## Die Kasse (K6 2c): Am Ende der Kette liegt sichtbar Geld auf einem Tisch.
##
## Das Geld waechst als Stapel (Scheine und Muenzsaeulen). Ab `kasse_ab_s` ist es
## antippbar: Der Tipp bringt einen kleinen Bonus (MomentSystem.kasse_antippen,
## hoechstens ein paar Prozent des Einkommens) -- das Einkommen selbst bucht der
## Kern weiter automatisch, nie als Verlust, nie als Pflicht.
##
## Nur Darstellung: Wie voll die Kasse ist und was ein Tipp bringt, rechnet der
## Kern. Die Tippflaeche ist EIN fester Kreis von 96 px, der sich nie ein- und
## ausblendet (nur Filter STOP/IGNORE), und der TippErkenner wertet die Eingabe
## aus -- so verschluckt keine flackernde Flaeche einen Tipp.
class_name Kassenstapel
extends Node3D

## Bildposition der Kasse, Betrag -- fuer Zahl, Muenzflug, Ton.
signal getippt(bild_position: Vector2, betrag: float)

const FELD: float = 96.0
const PLATTE := Color("8a5a3a")
const PLATTE_OBEN := Color("56687f")
const SCHEIN := Color("5fae6b")
const SCHEIN_DUNKEL := Color("3f8a52")
const BAND := Color("f3e7c6")
const GOLD := Color("f6c542")
const GOLD_HELL := Color("ffe58a")
const MAX_SCHEINE: int = 10
const MAX_SAEULE: int = 7
const SAEULEN: int = 3

var kern: GameCore
var _stapel: Node3D
var _scheine: Array[Node3D] = []
var _saeulen: Array[Array] = [[], [], []]
var _glanz: MeshInstance3D
var _zeichen: Sprite3D
var _feld: Control
var _erkenner: TippErkenner
var _bereit: bool = false
var _zeit: float = 0.0
var _leert: bool = false


## Wo die Kasse steht: worlds.json -> karte.kasse {x, z}; sonst rechts neben dem
## Ende der Kette.
static func ort(welten: WorldData, index: int, ende: Vector3) -> Vector3:
	var karte: Dictionary = welten.welt(index).get("karte", {}) as Dictionary
	if karte.has("kasse"):
		var k: Dictionary = karte["kasse"] as Dictionary
		return Vector3(float(k.get("x", 0.0)), 0.0, float(k.get("z", 0.0)))
	return ende + Vector3(1.6, 0.0, 1.2)


func aufbauen(k: GameCore, platz: Vector3) -> void:
	kern = k
	position = platz
	_baue_tisch()
	_stapel = Node3D.new()
	_stapel.position.y = 0.62
	_stapel.scale = Vector3.ONE * 1.5
	add_child(_stapel)
	_zeichen = Sprite3D.new()
	_zeichen.texture = UiStil.symbol("muenze")
	_zeichen.pixel_size = 0.0021
	_zeichen.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_zeichen.shaded = false
	_zeichen.no_depth_test = true
	_zeichen.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	_zeichen.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_zeichen.visible = false
	add_child(_zeichen)
	var ebene := CanvasLayer.new()
	ebene.layer = 0
	add_child(ebene)
	_feld = Control.new()
	_feld.name = "KasseFlaeche"
	_feld.size = Vector2(FELD, FELD)
	_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ebene.add_child(_feld)
	_erkenner = TippErkenner.new()
	_feld.gui_input.connect(func(e: InputEvent) -> void:
		var nach_bild: Transform2D = _feld.get_global_transform() if _feld.is_inside_tree() else Transform2D.IDENTITY
		if _erkenner.auswerten(e, nach_bild):
			tippe())
	_aktualisiere_teile(0.0)
	# Vorschau-Schalter (nur Debug): --kasse fuellt sie und blickt hin, --kasse-tipp tippt sie an.
	if OS.is_debug_build() and OS.get_cmdline_user_args().has("--kasse"):
		kern.momente.kasse_fuell = kern.momente.kasse_max_s
		_blicke_hin.call_deferred()


func _blicke_hin() -> void:
	var n: Node = get_viewport().get_camera_3d()
	while n != null:
		if n.has_method(&"setze_blickpunkt"):
			n.call(&"setze_blickpunkt", global_position)
			return
		n = n.get_parent()


func _baue_tisch() -> void:
	var platte := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(2.0, 0.5, 1.4)
	platte.mesh = b
	platte.material_override = _stoff(PLATTE, 0.0, 0.8)
	platte.position.y = 0.25
	add_child(platte)
	var deckel := MeshInstance3D.new()
	var d := BoxMesh.new()
	d.size = Vector3(2.1, 0.1, 1.5)
	deckel.mesh = d
	deckel.material_override = _stoff(PLATTE_OBEN, 0.1, 0.5)
	deckel.position.y = 0.55
	add_child(deckel)
	# Ein heller Streifen an der Kante: macht aus dem Klotz einen Tresen.
	var leiste := MeshInstance3D.new()
	var l := BoxMesh.new()
	l.size = Vector3(2.12, 0.04, 0.1)
	leiste.mesh = l
	leiste.material_override = _stoff(BAND, 0.0, 0.6)
	leiste.position = Vector3(0.0, 0.62, 0.7)
	add_child(leiste)
	_glanz = MeshInstance3D.new()
	var ring := CylinderMesh.new()
	ring.top_radius = 1.25
	ring.bottom_radius = 1.25
	ring.height = 0.02
	_glanz.mesh = ring
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(GOLD, 0.0)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_glanz.material_override = m
	_glanz.position.y = 0.04
	_glanz.visible = false
	add_child(_glanz)


func _stoff(farbe: Color, metall: float, rauh: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = farbe
	m.metallic = metall
	m.roughness = rauh
	return m


func _muenze() -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = 0.2
	c.bottom_radius = 0.2
	c.height = 0.07
	mi.mesh = c
	var m := _stoff(GOLD, 0.7, 0.28)
	m.emission_enabled = true
	m.emission = Color("9a6c14")
	m.emission_energy_multiplier = 0.7
	mi.material_override = m
	# Geprägte Fläche oben: ein hellerer, leicht eingelassener Kreis -- das glänzt.
	var flaeche := MeshInstance3D.new()
	var fc := CylinderMesh.new()
	fc.top_radius = 0.15
	fc.bottom_radius = 0.15
	fc.height = 0.012
	flaeche.mesh = fc
	var fm := _stoff(GOLD_HELL, 0.9, 0.18)
	fm.emission_enabled = true
	fm.emission = Color("b88a20")
	fm.emission_energy_multiplier = 0.8
	flaeche.material_override = fm
	flaeche.position.y = 0.036
	mi.add_child(flaeche)
	return mi


func _schein(nr: int) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.74, 0.05, 0.42)
	mi.mesh = b
	mi.material_override = _stoff(SCHEIN if nr % 2 == 0 else SCHEIN_DUNKEL, 0.1, 0.55)
	# Kein Lineal: jeder Schein liegt eine Spur schief.
	mi.rotation.y = sin(float(nr) * 2.3) * 0.18
	mi.position = Vector3(-0.5 + sin(float(nr) * 1.7) * 0.03, 0.03 + float(nr) * 0.052, 0.0)
	# Eine Banderole auf dem obersten Schein-Buendel macht es zum Geld.
	var band := MeshInstance3D.new()
	var bb := BoxMesh.new()
	bb.size = Vector3(0.14, 0.056, 0.44)
	band.mesh = bb
	band.material_override = _stoff(BAND, 0.0, 0.6)
	mi.add_child(band)
	return mi


## Wie voll ist die Kasse, 0..1?
func fuellung() -> float:
	return clampf(kern.momente.kasse_fuell / maxf(kern.momente.kasse_max_s, 0.001), 0.0, 1.0)


func _aktualisiere_teile(f: float) -> void:
	var n_scheine: int = 1 + int(round(f * float(MAX_SCHEINE - 1)))
	while _scheine.size() < n_scheine:
		var s: MeshInstance3D = _schein(_scheine.size())
		_stapel.add_child(s)
		_poppen(s)
		_scheine.append(s)
	while _scheine.size() > n_scheine:
		_scheine.pop_back().queue_free()
	var n_saeule: int = 1 + int(round(f * float(MAX_SAEULE - 1)))
	for i in range(SAEULEN):
		var ziel: int = maxi(1, n_saeule - i * 2)
		var liste: Array = _saeulen[i]
		while liste.size() < ziel:
			var mz: MeshInstance3D = _muenze()
			mz.position = Vector3(0.1 + float(i) * 0.46, 0.04 + float(liste.size()) * 0.075, -0.28 + float(i) * 0.28)
			mz.rotation.y = float(liste.size() + i) * 0.7
			_stapel.add_child(mz)
			_poppen(mz)
			liste.append(mz)
		while liste.size() > ziel:
			(liste.pop_back() as Node).queue_free()


func _poppen(n: Node3D) -> void:
	var ziel: Vector3 = n.scale
	n.scale = ziel * 0.3
	create_tween().tween_property(n, "scale", ziel, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _process(delta: float) -> void:
	if kern == null:
		return
	_zeit += delta
	if not _leert:
		_aktualisiere_teile(fuellung())
	_bereit = kern.momente.kasse_bereit()
	# Bereit: ein weicher Goldschein auf dem Tisch und eine schwebende Muenze.
	_glanz.visible = _bereit
	_zeichen.visible = _bereit
	if _bereit:
		var puls: float = 0.5 + 0.5 * sin(_zeit * 4.0)
		(_glanz.material_override as StandardMaterial3D).albedo_color = Color(GOLD, 0.18 + 0.22 * puls)
		_zeichen.position = Vector3(0.0, 2.4 + 0.12 * sin(_zeit * 3.0), 0.0)
		_stapel.rotation.z = 0.0
	_setze_feld()
	if _bereit and _zeit > 3.0 and OS.is_debug_build() and OS.get_cmdline_user_args().has("--kasse-tipp"):
		tippe()


## Die Tippflaeche folgt der Kasse im Bild. Sie bleibt immer im Baum und sichtbar
## (kein Flackern); nur der Mausfilter schaltet.
func _setze_feld() -> void:
	var kamera: Camera3D = get_viewport().get_camera_3d() if is_inside_tree() else null
	if kamera == null or _feld == null:
		return
	var welt: Vector3 = global_position + Vector3(0.0, 1.0, 0.0)
	var da: bool = _bereit and not kamera.is_position_behind(welt)
	var p: Vector2 = kamera.unproject_position(welt)
	_feld.position = p - _feld.size * 0.5
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	da = da and p.x > 0.0 and p.y > 0.0 and p.x < flaeche.x and p.y < flaeche.y
	_feld.mouse_filter = Control.MOUSE_FILTER_STOP if da else Control.MOUSE_FILTER_IGNORE
	if not da:
		_erkenner.abbrechen()


## Mitte der Tippflaeche in Bildpixeln.
func bild_mitte() -> Vector2:
	return _feld.position + _feld.size * 0.5


## Ein Tipp (auch fuer Tests/Vorschau): Bonus buchen, Geld fliegt hoch.
func tippe() -> float:
	if kern == null or not kern.momente.kasse_bereit() or _leert:
		return 0.0
	var betrag: float = _buche()
	if betrag <= 0.0:
		return 0.0
	var von: Vector2 = bild_mitte()
	_leere_stapel()
	_rueckmeldung(von, betrag)
	getippt.emit(von, betrag)
	return betrag


func _buche() -> float:
	if kern.has_method(&"tippe_kasse"):
		return float(kern.call(&"tippe_kasse"))
	var betrag: float = kern.momente.kasse_antippen(kern.einkommen_pro_sekunde(), kern.bus)
	if betrag > 0.0:
		kern.kapital += betrag
		kern.gesamt_verdient += betrag
		kern.welt_verdient += betrag
		kern.bus.money_changed.emit(kern.kapital, betrag)
	return betrag


## Alle Scheine und Muenzen steigen auf und sind weg; dann waechst der Stapel neu.
func _leere_stapel() -> void:
	_leert = true
	var t := create_tween().set_parallel(true)
	var alle: Array[Node3D] = []
	alle.append_array(_scheine)
	for liste in _saeulen:
		for n in (liste as Array):
			alle.append(n as Node3D)
	var k: int = 0
	for n in alle:
		t.tween_property(n, "position:y", n.position.y + 1.8, 0.4).set_ease(Tween.EASE_OUT).set_delay(float(k) * 0.02)
		t.tween_property(n, "scale", Vector3(0.05, 0.05, 0.05), 0.4).set_ease(Tween.EASE_IN).set_delay(float(k) * 0.02)
		k += 1
	t.chain().tween_callback(func() -> void:
		for n in alle:
			if is_instance_valid(n):
				n.queue_free()
		_scheine.clear()
		for liste in _saeulen:
			(liste as Array).clear()
		_leert = false)


## Zahl, Muenzflug zur Geldanzeige, Ton, Vibration -- vorhandenen Saft nutzen. Kein Fenster.
func _rueckmeldung(von: Vector2, betrag: float) -> void:
	Haptik.puls(Haptik.DAUER_MENGE)
	var wurzel: Node = get_tree().root
	for n in wurzel.find_children("*", "Saft", true, false):
		var saft: Saft = n as Saft
		saft.muenzen(von, 9)
		saft.betrag(von, "+" + UiStil.zahl(betrag))
		saft.funken(von, UiStil.GOLD, 10)
		break
	for n in wurzel.find_children("*", "AudioDirector", true, false):
		(n as AudioDirector).spiele(&"muenzen")
		break
