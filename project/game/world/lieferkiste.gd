## Die Lieferkiste (K3 B2): eine Kiste steht an der Tuer, wackelt und will
## angetippt werden. Nach `momente.dauer` Sekunden ist sie leise wieder weg.
##
## Nur Darstellung: Ob und wann eine Kiste da ist, entscheidet der Kern
## (MomentSystem, Art "kiste"); was sie bringt, rechnet er auch. Getippt wird
## der Aufkleber im Kartenmarker (Tippflaeche >= 96 px) -- die 3D-Kiste ist im
## Ueberblick nur ein paar Pixel gross und waere allein kein Tippziel.
##
## Zweite Belohnungsstufe (Welle C, Werbung): Der Kern nimmt sie ueber
## MomentSystem.antippen(..., sekunden) an; die Kiste selbst aendert sich nicht.
class_name Lieferkiste
extends Node3D

const KANTE: float = 0.78           ## Seitenlaenge der Kiste in Metern
const WACKEL_TAKT: float = 1.3      ## alle so viele Sekunden ein Wackler
const WACKEL_DAUER: float = 0.45
const WACKEL_WINKEL: float = 0.22   ## Radiant
const ABSTAND_TUER: float = 1.0     ## so weit steht die Kiste vor der Tuer, in der Startzone
const KARTON := Color("c98f55")
const KARTON_DUNKEL := Color("a46d3a")
const BAND := Color("efe2c2")

var kern: GameCore
var _koerper: Node3D
var _zeit: float = 0.0
var _sichtbar_vorher: bool = false
var _abgang: Tween


## Wo die Kiste steht: worlds.json -> karte.kiste {x, z}, sonst vor der Tuer der
## Startzone, die in den ersten kaufbaren Raum fuehrt (der Flur). Welten ohne
## Zonen: vorn in der Raummitte.
static func ort(welten: WorldData, index: int) -> Vector3:
	var w: Dictionary = welten.welt(index)
	var karte: Dictionary = w.get("karte", {}) as Dictionary
	if karte.has("kiste"):
		var k: Dictionary = karte["kiste"] as Dictionary
		return Vector3(float(k.get("x", 0.0)), 0.0, float(k.get("z", 0.0)))
	var start: Dictionary = welten.startzone(index)
	if start.is_empty():
		return Vector3(0.0, 0.0, float(welten.raum_tiefe(index)) * 0.25)
	var x1: float = float(start.get("x1", 0))
	var x2: float = float(start.get("x2", 0))
	var z1: float = float(start.get("z1", 0))
	var z2: float = float(start.get("z2", 0))
	var mitte := Vector3((x1 + x2) * 0.5, 0.0, (z1 + z2) * 0.5)
	var beste: Vector3 = Vector3.INF
	var beste_flur: bool = false
	var erster: String = _erster_bereich(welten, index)
	for eintrag in welten.waende(index):
		var wand: Dictionary = eintrag as Dictionary
		var fest: float = float(wand.get("fest", 0.0))
		var entlang_x: bool = String(wand.get("achse", "x")) == "x"
		for t in (wand.get("tueren", []) as Array):
			var tuer := Vector3(float(t), 0.0, fest) if entlang_x else Vector3(fest, 0.0, float(t))
			if not WorldData.zone_enthaelt(start, tuer, 0.1):
				continue
			# Liegt die Tuer auf dem Rand der Startzone? Dann einen Schritt nach innen.
			var innen: Vector3 = tuer
			if entlang_x:
				innen.z += ABSTAND_TUER if tuer.z < mitte.z else -ABSTAND_TUER
			else:
				innen.x += ABSTAND_TUER if tuer.x < mitte.x else -ABSTAND_TUER
			var draussen: Vector3 = tuer + (tuer - innen)
			var flur: bool = not erster.is_empty() \
				and String(welten.zone_an(index, draussen).get("bereich", "")) == erster
			if beste == Vector3.INF or (flur and not beste_flur):
				beste = innen
				beste_flur = flur
	return mitte if beste == Vector3.INF else beste


## Wo Anfragen eintreffen: worlds.json -> karte.eingang {x, z}; sonst links neben
## der ersten Station der Kette.
static func eingang_ort(welten: WorldData, index: int, erste: Vector3) -> Vector3:
	var karte: Dictionary = welten.welt(index).get("karte", {}) as Dictionary
	if karte.has("eingang"):
		var e: Dictionary = karte["eingang"] as Dictionary
		return Vector3(float(e.get("x", 0.0)), 0.0, float(e.get("z", 0.0)))
	return erste + Vector3(-1.6, 0.0, 0.2)


## Der erste kaufbare Raum: der erste Bereich in der Zonenliste.
static func _erster_bereich(welten: WorldData, index: int) -> String:
	for eintrag in welten.zonen(index):
		var bereich: String = String((eintrag as Dictionary).get("bereich", ""))
		if not bereich.is_empty():
			return bereich
	return ""


func aufbauen(k: GameCore) -> void:
	kern = k
	position = ort(kern.welten, kern.welt_index)
	_koerper = Node3D.new()
	add_child(_koerper)
	_baue_kiste()
	visible = false
	if OS.is_debug_build() and OS.get_cmdline_user_args().has("--kiste"):
		kern.momente.erzwinge(MomentSystem.ART_KISTE)


## Ein Karton mit Klebeband: zwei Farben, klare Kanten, dunkler als der Aufkleber
## darueber -- er ist Ort, nicht Hinweis.
func _baue_kiste() -> void:
	var karton := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(KANTE, KANTE * 0.82, KANTE)
	karton.mesh = box
	karton.material_override = _stoff(KARTON)
	karton.position.y = KANTE * 0.41
	_koerper.add_child(karton)
	for drehung in [0.0, PI * 0.5]:
		var band := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(KANTE * 1.02, KANTE * 0.84, KANTE * 0.18)
		band.mesh = b
		band.material_override = _stoff(BAND)
		band.position.y = KANTE * 0.41
		band.rotation.y = drehung
		_koerper.add_child(band)
	var deckel := MeshInstance3D.new()
	var d := BoxMesh.new()
	d.size = Vector3(KANTE * 1.06, KANTE * 0.1, KANTE * 1.06)
	deckel.mesh = d
	deckel.material_override = _stoff(KARTON_DUNKEL)
	deckel.position.y = KANTE * 0.84
	_koerper.add_child(deckel)


func _stoff(farbe: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = farbe
	m.roughness = 0.9
	return m


func _process(delta: float) -> void:
	if kern == null:
		return
	var da: bool = kern.momente.ist_kiste()
	if da and not _sichtbar_vorher:
		_erscheine()
	elif not da and _sichtbar_vorher:
		_verschwinde(kern.momente.letzte_art == MomentSystem.ART_KISTE)
	_sichtbar_vorher = da
	if not da:
		return
	_zeit += delta
	# Wackeln in Stoessen, nicht dauernd: Ein Dauerwackeln liest sich wie Deko.
	var phase: float = fmod(_zeit, WACKEL_TAKT)
	if phase < WACKEL_DAUER:
		var f: float = phase / WACKEL_DAUER
		_koerper.rotation.z = sin(f * TAU * 2.0) * WACKEL_WINKEL * (1.0 - f)
		_koerper.position.y = sin(f * PI) * KANTE * 0.18
	else:
		_koerper.rotation.z = 0.0
		_koerper.position.y = 0.0


func _erscheine() -> void:
	if _abgang != null and _abgang.is_valid():
		_abgang.kill()
	visible = true
	_zeit = 0.0
	_koerper.scale = Vector3.ONE * 0.2
	var t := create_tween()
	t.tween_property(_koerper, "scale", Vector3.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## Angetippt: ein Hopser, dann klappt sie zusammen. Verpasst: sie schrumpft leise.
func _verschwinde(angetippt: bool) -> void:
	_abgang = create_tween()
	if angetippt:
		_abgang.tween_property(_koerper, "position:y", KANTE * 0.7, 0.16).set_ease(Tween.EASE_OUT)
		_abgang.parallel().tween_property(_koerper, "scale", Vector3(1.25, 0.8, 1.25), 0.16)
		_abgang.tween_property(_koerper, "scale", Vector3(0.01, 0.01, 0.01), 0.22).set_ease(Tween.EASE_IN)
	else:
		_abgang.tween_property(_koerper, "scale", Vector3(0.01, 0.01, 0.01), 0.4).set_ease(Tween.EASE_IN)
	_abgang.tween_callback(func() -> void:
		visible = false
		_koerper.position.y = 0.0
		_koerper.rotation.z = 0.0)
