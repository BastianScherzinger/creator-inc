## Der Abschluss einer Welt: was man geschafft hat, und die Nachricht, die alles
## aendert (ADR-021).
##
## Nach achtzig Minuten kam vorher dieselbe Textkarte wie beim Start -- der
## groesste Moment der Welt verpuffte. Jetzt steht er fuer sich: die Zahlen des
## Weges, dann die Nachricht als Chat, mit der eigenen Antwort darunter. Erst
## danach kommt der Weltwechsel.
class_name AbschlussView
extends Control

signal angenommen

const SCHRITT: float = 0.4

var _knopf: Button
## Den Jingle spielt, wer einen AudioDirector hat (main.gd setzt ihn).
var audio: AudioDirector
var _saft: Saft
var _zahl_labels: Array[Label] = []


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()


func zeige(titel: String, zahlen: Array, von: String, nachricht: String, antwort: String, knopf_text: String) -> void:
	# Die Antwort ("Morgen.") antwortet auf die LETZTE Nachricht der Welt --
	# die steht fest in der Themendatei. Was der Aufrufer als zuletzt
	# empfangen meldet, kann eine andere sein (Reihenfolge, frischer Stand).
	var thema_daten: ThemeData = UiStil.welt_thema()
	if thema_daten != null:
		var alle: Dictionary = thema_daten.abschnitt("nachrichten")
		if not alle.is_empty():
			var letzte: Dictionary = alle[alle.keys()[alle.size() - 1]] as Dictionary
			von = WeltTexte.absender(thema_daten, String(letzte.get("von", "")))
			nachricht = String(letzte.get("text", nachricht))
	var akzent: Color = UiStil.akzent()
	var grund := ColorRect.new()
	grund.color = akzent
	grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(grund)

	var rand := MarginContainer.new()
	rand.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for seite in ["margin_left", "margin_right"]:
		rand.add_theme_constant_override(seite, UiStil.A6)
	rand.add_theme_constant_override("margin_top", 110)
	rand.add_theme_constant_override("margin_bottom", 64)
	add_child(rand)

	var spalte := VBoxContainer.new()
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.add_theme_constant_override("separation", UiStil.A5)
	rand.add_child(spalte)

	var stern := UiStil.symbolbild("stern", 132.0)
	stern.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	spalte.add_child(stern)

	var kopf_feld := PanelContainer.new()
	kopf_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 4,
		UiStil.KONTUR + 1, float(UiStil.A4), UiStil.SCHATTEN_Y * 2.0))
	UiStil.drehe(kopf_feld, -2.5)
	spalte.add_child(kopf_feld)
	var kopf := UiStil.label(titel, UiStil.GR_ZAHL + 4, UiStil.TINTE, UiStil.FETT)
	kopf.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	kopf.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kopf_feld.add_child(kopf)

	var tafel := PanelContainer.new()
	tafel.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A5)))
	spalte.add_child(tafel)
	var liste := VBoxContainer.new()
	liste.add_theme_constant_override("separation", UiStil.A2)
	tafel.add_child(liste)
	for eintrag in zahlen:
		var zeile := HBoxContainer.new()
		var name := UiStil.label(String((eintrag as Array)[0]), UiStil.GR_MITTEL - 2, UiStil.TINTE_2, UiStil.FETT)
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		zeile.add_child(name)
		var wert := UiStil.label(String((eintrag as Array)[1]), UiStil.GR_GROSS - 2, UiStil.TINTE, UiStil.FETT)
		wert.set_meta("ziel", String((eintrag as Array)[1]))
		_zahl_labels.append(wert)
		zeile.add_child(wert)
		liste.add_child(zeile)

	# Die Nachricht als Chat -- Avatar in der Farbe des Absenders.
	var farbe: Color = _farbe_fuer(von)
	var chat := HBoxContainer.new()
	chat.add_theme_constant_override("separation", UiStil.A3)
	if not von.is_empty():
		chat.add_child(UiStil.avatar(von, farbe, 64.0, "jubelnd"))
	var blase := PanelContainer.new()
	var bstil := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
		UiStil.SCHATTEN_Y, farbe if not von.is_empty() else UiStil.TINTE)
	bstil.content_margin_left = float(UiStil.A4)
	bstil.content_margin_right = float(UiStil.A4)
	bstil.flaeche.corner_radius_top_left = 4
	bstil.schatten.corner_radius_top_left = 4
	blase.add_theme_stylebox_override("panel", bstil)
	blase.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var bspalte := VBoxContainer.new()
	bspalte.add_theme_constant_override("separation", 0)
	blase.add_child(bspalte)
	if not von.is_empty():
		bspalte.add_child(UiStil.label(von, UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT))
	var btext := UiStil.label(nachricht, UiStil.GR_MITTEL - 1, UiStil.TINTE, UiStil.TEXT_GEWICHT)
	btext.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bspalte.add_child(btext)
	chat.add_child(blase)
	spalte.add_child(chat)

	# Die eigene Antwort: rechts, Tinte -- die Spielfigur hat keine Farbe.
	var antwort_blase := PanelContainer.new()
	var astil := UiStil.sticker(UiStil.TINTE, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
		UiStil.SCHATTEN_Y, UiStil.PAPIER)
	astil.content_margin_left = float(UiStil.A5)
	astil.content_margin_right = float(UiStil.A5)
	astil.flaeche.corner_radius_bottom_right = 4
	astil.schatten.corner_radius_bottom_right = 4
	antwort_blase.add_theme_stylebox_override("panel", astil)
	antwort_blase.size_flags_horizontal = Control.SIZE_SHRINK_END
	antwort_blase.add_child(UiStil.label(antwort, UiStil.GR_MITTEL, UiStil.PAPIER, UiStil.FETT))
	antwort_blase.visible = not antwort.is_empty()
	spalte.add_child(antwort_blase)

	_knopf = UiStil.kaufknopf(UiStil.KAUFEN, 120.0)
	_knopf.text = knopf_text
	_knopf.add_theme_font_size_override("font_size", UiStil.GR_TITEL - 4)
	_knopf.pressed.connect(func() -> void: angenommen.emit())
	spalte.add_child(_knopf)

	# Gestaffelt: Titel, Zahlen, dann die Nachricht, dann die Antwort, dann der Knopf.
	var teile: Array[Control] = [stern, kopf_feld, tafel, chat, antwort_blase, _knopf]
	for i in range(teile.size()):
		teile[i].modulate.a = 0.0
		var t := create_tween()
		t.tween_interval(0.25 + float(i) * SCHRITT)
		t.tween_property(teile[i], "modulate:a", 1.0, 0.15)
		t.tween_callback(UiStil.aufploppen.bind(teile[i], 0.85))
	_knopf.disabled = true
	_saft = Saft.new()
	add_child(_saft)
	_feier(tafel)
	# Der Stern atmet weiter, solange der Bildschirm steht -- ein stehendes Bild
	# wirkt nach der Feier wie abgestuerzt.
	var atmen := stern.create_tween().set_loops()
	atmen.tween_interval(1.2)
	atmen.tween_callback(func() -> void: stern.pivot_offset = stern.size * 0.5)
	atmen.tween_property(stern, "scale", Vector2(1.12, 1.12), 0.5).set_trans(Tween.TRANS_SINE)
	atmen.parallel().tween_property(stern, "rotation_degrees", 6.0, 0.5).set_trans(Tween.TRANS_SINE)
	atmen.tween_property(stern, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_SINE)
	atmen.parallel().tween_property(stern, "rotation_degrees", -6.0, 0.5).set_trans(Tween.TRANS_SINE)
	var freigabe := create_tween()
	freigabe.tween_interval(0.25 + float(teile.size()) * SCHRITT)
	freigabe.tween_callback(func() -> void:
		if is_instance_valid(_knopf):
			_knopf.disabled = false)


## Die Farbe eines Absenders, von dem nur der Anzeigename bekannt ist.
func _farbe_fuer(anzeigename: String) -> Color:
	var thema_daten: ThemeData = UiStil.welt_thema()
	if thema_daten == null:
		return UiStil.akzent()
	var absender: Dictionary = thema_daten.abschnitt("absender")
	for schluessel in absender.keys():
		if String(absender[schluessel]) == anzeigename:
			return UiStil.absender_farbe(thema_daten, String(schluessel))
	return UiStil.akzent()


# --- Feier: Konfetti, Muenzregen, Hochzaehlen, Jingle ---------------------------------

func _feier(tafel: Control) -> void:
	if audio != null:
		audio.spiele(&"fanfare")
	Haptik.puls(Haptik.DAUER_FEIER)
	var flaeche: Vector2 = get_viewport_rect().size
	var anfang := create_tween()
	anfang.tween_interval(0.25)
	anfang.tween_callback(func() -> void:
		_saft.blitz(UiStil.WEISS, 0.35, 0.25)
		_saft.konfetti(Vector2(flaeche.x * 0.12, flaeche.y * 0.78), 50)
		_saft.konfetti(Vector2(flaeche.x * 0.88, flaeche.y * 0.78), 50)
		_saft.regen("muenze", 30))
	var nach := create_tween()
	nach.tween_interval(1.6)
	nach.tween_callback(func() -> void:
		_saft.konfetti(Vector2(flaeche.x * 0.5, flaeche.y * 0.55), 40))
	# Die Zahlen der Tafel laufen hoch, sobald sie erscheinen (die Tafel ist Teil 3 der Staffel).
	var zaehlen := create_tween()
	zaehlen.tween_interval(0.25 + 2.0 * SCHRITT)
	zaehlen.tween_callback(func() -> void:
		for l in _zahl_labels:
			_zaehle_hoch(l, String(l.get_meta("ziel", ""))))


## Zahlen wie "1.234 €" oder "1,2 Mio €" zaehlen von 0 hoch; alles andere
## ("1 Std 30 Min", "5/9") bleibt stehen -- Text laesst sich nicht sinnvoll zaehlen.
func _zaehle_hoch(l: Label, ziel: String) -> void:
	var r := RegEx.new()
	r.compile("^([0-9]+(?:\\.[0-9]{3})*)(?:,([0-9]+))?((?: .*)?)$")
	var m: RegExMatch = r.search(ziel)
	if m == null:
		return
	var ganz: String = m.get_string(1).replace(".", "")
	var nach: String = m.get_string(2)
	var rest: String = m.get_string(3)
	var wert: float = float(ganz + ("." + nach if not nach.is_empty() else ""))
	if wert <= 0.0:
		return
	var stellen: int = nach.length()
	var t := create_tween()
	t.tween_method(func(f: float) -> void:
		var jetzt: float = wert * f
		var text: String
		if stellen > 0:
			text = ("%." + str(stellen) + "f") % jetzt
			text = text.replace(".", ",")
		else:
			text = UiStil.zahl(floorf(jetzt)) if jetzt >= 1000.0 else str(int(jetzt))
		l.text = text + rest, 0.0, 1.0, 1.1).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	t.tween_callback(func() -> void: l.text = ziel)
