## Das Geschenk an der Fortschrittsleiste (Marken bei 25/50/75 %), drei Zustaende:
##   ZU         gedaempft, mit Schloss -- noch nicht erreicht
##   ERREICHBAR wackelt (Rotation +-9 Grad, PULS_HZ) -- jetzt einloesbar
##   OFFEN      voll, mit Haken -- schon geholt
## Reine Darstellung; wer sie benutzt, setzt nur den Zustand.
class_name GeschenkMarke
extends Control

enum Zustand { ZU, ERREICHBAR, OFFEN }

var zustand: Zustand = Zustand.ZU
var _bild: TextureRect
var _zeichen: TextureRect
var _zeit: float = 0.0


func _init(kante: float = 40.0) -> void:
	custom_minimum_size = Vector2(kante, kante)
	size = custom_minimum_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bild = UiStil.symbolbild("geschenk", kante)
	_bild.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_bild)
	_zeichen = UiStil.symbolbild("schloss", kante * 0.36)
	_zeichen.size = Vector2(kante * 0.36, kante * 0.36)
	_zeichen.position = Vector2(kante * 0.64, kante * 0.64)
	_zeichen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_zeichen)
	setze_zustand(Zustand.ZU)


func setze_zustand(neu: Zustand) -> void:
	zustand = neu
	pivot_offset = size * 0.5
	match neu:
		Zustand.ZU:
			# Fast deckend, nur leicht entsaettigt: Sie bleibt als Geschenk erkennbar.
			_bild.modulate = Color(0.82, 0.78, 0.72, 0.95)
			_zeichen.texture = UiStil.symbol("schloss")
			_zeichen.visible = true
		Zustand.ERREICHBAR:
			_bild.modulate = Color.WHITE
			_zeichen.visible = false
		Zustand.OFFEN:
			_bild.modulate = Color.WHITE
			_zeichen.texture = UiStil.symbol("haken")
			_zeichen.visible = true
	if neu != Zustand.ERREICHBAR:
		rotation = 0.0
		scale = Vector2.ONE
	set_process(neu == Zustand.ERREICHBAR)


func _process(delta: float) -> void:
	_zeit += delta
	rotation = deg_to_rad(9.0) * sin(_zeit * TAU * UiStil.PULS_HZ)
	var s: float = 1.0 + (UiStil.PULS_SKALA - 1.0) * (0.5 + 0.5 * sin(_zeit * TAU * UiStil.PULS_HZ * 2.0))
	scale = Vector2(s, s)
