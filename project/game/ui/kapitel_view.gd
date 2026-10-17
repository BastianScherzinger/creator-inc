## Kapitelzeile (K6 1c, §3.2 "Keine Kapitelkarte als Modal"): Das laufende Kapitel
## steht als kleine Zeile IN der Zielleiste ("Kapitel 2 · Zu wenig Platz"). Beim
## Wechsel laeuft ein kurzer Glanz darueber (Aufploppen + Lichtstreif, zusammen
## hoechstens `kapitel_glanz_s` aus data/ui/hinweise.json) -- kein Fenster, kein Tipp.
##
## Die Zeile rechnet nichts: Text kommt von aussen (Hud.kapitel_zeile).
class_name KapitelZeile
extends Label

var _streif: TextureRect
var _ablauf: Tween


func _init() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_KLEIN - 2))
	add_theme_font_size_override("font_size", UiStil.GR_KLEIN - 2)
	add_theme_color_override("font_color", UiStil.TINTE_2)
	# K7: Die Zeile steht ohne Flaeche auf der Karte. In dunklen Welten (Studio, Farm) war
	# graue Tinte auf Nachtblau unlesbar -- ein heller Rand traegt sie auf jedem Grund.
	add_theme_color_override("font_outline_color", UiStil.PAPIER)
	add_theme_constant_override("outline_size", UiStil.KONTUR + 2)
	visible = false
	_streif = TextureRect.new()
	var verlauf := Gradient.new()
	verlauf.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
	verlauf.colors = PackedColorArray([Color(1, 1, 1, 0), Color(1, 1, 1, 0.85), Color(1, 1, 1, 0)])
	var tex := GradientTexture2D.new()
	tex.gradient = verlauf
	tex.width = 64
	tex.height = 8
	_streif.texture = tex
	_streif.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_streif.stretch_mode = TextureRect.STRETCH_SCALE
	_streif.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_streif.visible = false
	add_child(_streif)


## Setzt den Text. `glaenzen`: der Wechsel soll gesehen werden (neues Kapitel).
func setze(zeile: String, glaenzen: bool) -> void:
	visible = not zeile.is_empty()
	if zeile.to_upper() == text and not glaenzen:
		return
	text = zeile.to_upper()
	if glaenzen and visible and is_inside_tree():
		glanz()


## Kurzer Glanz: Zeile ploppt auf, wird kurz gold, ein Lichtstreif laeuft einmal durch.
func glanz() -> void:
	var dauer: float = minf(Kartenmarker.hinweis("kapitel_glanz_s"), 2.0)
	if dauer <= 0.0:
		return
	if _ablauf != null and _ablauf.is_valid():
		_ablauf.kill()
	pivot_offset = size * 0.5
	var breite: float = maxf(size.x, 1.0)
	_streif.size = Vector2(breite * 0.35, size.y)
	_streif.position = Vector2(-breite * 0.35, 0.0)
	_streif.visible = true
	add_theme_color_override("font_color", UiStil.GOLD_TEXT)
	_ablauf = create_tween()
	_ablauf.tween_property(self, "scale", Vector2(1.08, 1.08), dauer * 0.15).from(Vector2.ONE) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_ablauf.parallel().tween_property(_streif, "position:x", breite, dauer * 0.55).set_delay(dauer * 0.1)
	_ablauf.tween_property(self, "scale", Vector2.ONE, dauer * 0.2)
	_ablauf.tween_interval(dauer * 0.15)
	_ablauf.tween_callback(func() -> void:
		_streif.visible = false
		add_theme_color_override("font_color", UiStil.TINTE_2))
