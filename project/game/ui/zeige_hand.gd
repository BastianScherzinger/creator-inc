## Die Zeigehand: ein Sticker-Finger, der 1 Hz auf das nächste sinnvolle Element
## hüpft (DESIGN_OVERHAUL 4.6, Idle-Miner-Regel: Hand = "hier weiter").
##
## Zwei Einsatzarten:
##   * Tutorial: TutorialView ruft `zeige_bei(spitze)` jeden Frame mit dem Ziel.
##   * Leerlauf: `ZeigeHand.leerlauf(eltern, anbieter)` -- die Hand erscheint nur,
##     wenn der Spieler `hand_leerlauf_sekunden` (60) lang nichts getippt hat UND der
##     Anbieter einen Punkt liefert (z. B. ein bezahlbarer, lohnender Kauf).
##     Jeder Tipp versteckt sie und setzt die Uhr zurück.
##
## Gezeichnet wird selbst (kein Asset nötig); liegt `assets/ui/symbole/hand.svg`
## vor (U1), wird dieses Bild genommen.
class_name ZeigeHand
extends Control

const SVG_PFAD: String = "res://assets/ui/symbole/hand.svg"
## Ein Sprung pro Sekunde, 22 px hoch.
const HUEPF_HZ: float = 1.0
const HUEPF_HOEHE: float = 22.0
const KANTE: float = 92.0

## Gibt den Bildschirmpunkt zurück, auf den die Hand zeigen soll,
## oder Vector2(-1, -1) (= nichts Lohnendes).
var anbieter: Callable = Callable()
var _spitze: Vector2 = Vector2(-1.0, -1.0)
var _aktiv: bool = false
var _von_oben: bool = false
## 0 = von unten/oben wie `_von_oben`; +1 = Hand liegt links vom Ziel (zeigt nach rechts),
## -1 = Hand liegt rechts vom Ziel (zeigt nach links).
var _seite: int = 0
var _zeit: float = 0.0
var _ruhe: float = 0.0
var _leerlauf: bool = false
var _bild: Texture2D = null


## Leerlauf-Hand: hängt sich an `eltern` und wacht selbst.
static func leerlauf(eltern: Node, anbieter_funktion: Callable) -> ZeigeHand:
	var h := ZeigeHand.new()
	h._leerlauf = true
	h.anbieter = anbieter_funktion
	eltern.add_child(h)
	return h


## Reine Regel (testbar): zeigen, wenn lange genug Ruhe war und es ein Ziel gibt.
static func soll_zeigen(ruhe: float, schwelle: float, hat_ziel: bool) -> bool:
	return hat_ziel and ruhe >= schwelle


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	z_index = 50
	if ResourceLoader.exists(SVG_PFAD):
		_bild = load(SVG_PFAD) as Texture2D


## Hand auf diesen Punkt setzen (Fingerspitze). Tutorial ruft das jeden Frame.
## `von_oben`: Die Hand kommt von oben und zeigt nach unten (für Ziele am unteren Rand,
## unter denen kein Platz für eine Hand ist).
func zeige_bei(spitze: Vector2, von_oben: bool = false, seite: int = 0) -> void:
	_spitze = spitze
	_von_oben = von_oben
	_seite = seite
	_aktiv = true
	queue_redraw()


func verbirg() -> void:
	_aktiv = false
	queue_redraw()


func _input(e: InputEvent) -> void:
	if not _leerlauf:
		return
	if e is InputEventMouseButton or e is InputEventScreenTouch:
		_ruhe = 0.0
		if _aktiv:
			verbirg()


func _process(delta: float) -> void:
	_zeit += delta
	if _leerlauf:
		# P1.7: Steht ein Fenster offen (oder wartet eins), zeigt die Hand nicht.
		if ModalSchlange.global().ist_beschaeftigt():
			_ruhe = 0.0
			if _aktiv:
				verbirg()
			return
		_ruhe += delta
		if _ruhe >= U3Text.schwelle("hand_leerlauf_sekunden", 60.0):
			var punkt: Vector2 = anbieter.call() if anbieter.is_valid() else Vector2(-1.0, -1.0)
			if soll_zeigen(_ruhe, 0.0, punkt.x >= 0.0):
				zeige_bei(punkt)
			else:
				_aktiv = false
	if _aktiv:
		queue_redraw()


func _draw() -> void:
	if not _aktiv:
		return
	# Hüpfen: abs(sin) -- die Hand tippt aufs Ziel und hebt sich wieder.
	var hup: float = absf(sin(_zeit * PI * HUEPF_HZ)) * HUEPF_HOEHE
	var winkel: float = PI if _von_oben else 0.0
	if _seite != 0:
		winkel = float(_seite) * PI * 0.5
	draw_set_transform(_spitze, winkel)
	var s: Vector2 = Vector2(10.0 if not _von_oben else -10.0, 12.0 + hup)
	if _bild != null:
		draw_texture_rect(_bild, Rect2(s - Vector2(KANTE * 0.3, 0.0), Vector2(KANTE, KANTE)), false)
		return
	# Zeigefinger, Handballen, Daumen -- erst alle Umrisse (Tinte), dann die Flächen (Weiß).
	var teile: Array[Rect2] = [
		Rect2(s + Vector2(-15.0, 0.0), Vector2(30.0, 74.0)),     # Zeigefinger
		Rect2(s + Vector2(-38.0, 52.0), Vector2(76.0, 62.0)),    # Handballen
		Rect2(s + Vector2(-56.0, 70.0), Vector2(34.0, 24.0)),    # Daumen
	]
	var schatten := Vector2(0.0, UiStil.SCHATTEN_Y)
	for r in teile:
		_teil(Rect2(r.position + schatten, r.size), UiStil.TINTE, 5.0)
	for r in teile:
		_teil(r, UiStil.TINTE, 5.0)
	for r in teile:
		_teil(r, UiStil.WEISS, 0.0)


func _teil(r: Rect2, farbe: Color, wachs: float) -> void:
	var box := StyleBoxFlat.new()
	box.bg_color = farbe
	box.set_corner_radius_all(int(minf(r.size.x, r.size.y) * 0.5) if r.size.x < 40.0 else 20)
	box.anti_aliasing = true
	draw_style_box(box, r.grow(wachs))
