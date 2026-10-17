## Rueckmeldungen, die sich gut anfuehlen: Meldungen von oben, fliegende
## Muenzen, aufsteigende Betraege.
##
## "Saft" ist das Genre-Wort dafuer, und es ist kein Schmuck: Ein Kauf ohne
## Rueckmeldung fuehlt sich an, als waere nichts passiert (ART_DIRECTION 6).
class_name Saft
extends Control

const MELDUNG_DAUER: float = 1.6   ## plus Ein-/Ausblenden: gesamt <= 2 s
## Eine Chat-Nachricht bleibt laenger: Sie ist Geschichte, kein Zuruf -- und man
## soll sie lesen koennen, auch wenn man gerade kauft.
const CHAT_DAUER: float = 3.5
## Die Meldung haengt unter der Zeile aus Zielkarte und Engpass -- eine
## Meldung, die das naechste Ziel verdeckt, nimmt genau in dem Moment die
## Orientierung weg, in dem etwas passiert ist.
const MELDUNG_OBEN: float = Kopfleiste.OBEN + Kopfleiste.HOEHE + UiStil.TIPPZIEL + 28.0
const RAND: float = 16.0
## Zuege (nicht Chats) stehen UNTEN ueber der Menueleiste, ueber dem herausragenden
## Boost-Knopf (Abstand >= 16): Dort verdecken sie keinen Marker in der Welt.
const MELDUNG_UNTEN: float = Menueleiste.HOEHE + 50.0 + 16.0

## Der Spieler hat auf das Chat-Banner getippt (die Hud oeffnet dann das Handy).
signal chat_getippt

var kopfleiste: Kopfleiste
## Zusaetzlicher Abstand nach unten, wenn die Hud oben mehr zeigt (Speicher-Leiste).
var zusatz_oben: float = 0.0
## Hoehe, die ein offenes Menue von unten belegt (die Hud setzt sie). Die untere
## Meldung steht ueber dem Menue statt auf seinen Zeilen.
var menue_hoehe: Callable = Callable()
## K6 1c: Solange `halt` true liefert (Blase oder Tutorialkarte spricht), wartet die naechste
## Meldung -- eine Textquelle zur Zeit. Die Hud stoesst je Bild an (anstossen).
var halt: Callable = Callable()
var _meldungen: Array[Array] = []
var _letzter_betrag: String = ""
var _letzter_betrag_ms: int = 0
var _meldung_laeuft: bool = false
var _aktuelles_feld: Control = null
## Waehrend ein Moment offen ist, halten Banner und Zahlen still: Banner warten in
## der Schlange, Zahlen entfallen (sie lagen sonst ueber dem abgedunkelten Moment).
var pausiert: bool = false:
	set(wert):
		if wert == pausiert:
			return
		pausiert = wert
		if pausiert:
			if _aktuelles_feld != null and is_instance_valid(_aktuelles_feld):
				_aktuelles_feld.visible = false
		elif not _meldung_laeuft:
			_naechste()


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


## Eine Meldung unter der Kopfleiste. Immer nur eine auf einmal.
func meldung(titel: String, text: String, symbol: String = "geschenk") -> void:
	if titel.is_empty() and text.is_empty():
		return
	# Meldungen derselben Art (z. B. Raumkaeufe) stauen sich nicht:
	# die neueste ersetzt die wartende.
	for i in range(_meldungen.size() - 1, -1, -1):
		if _meldungen[i][3] == null and String(_meldungen[i][2]) == symbol:
			_meldungen.remove_at(i)
	_meldungen.append([titel, text, symbol, null, 0])
	if not _meldung_laeuft and not pausiert:
		_naechste()


## Eine Chat-Nachricht als Meldung: Avatar in der Farbe des Absenders.
func chat(absender: String, text: String, farbe: Color) -> void:
	if text.is_empty():
		return
	# Nachrichten laufen nacheinander (je Banner-Dauer). Nur wenn sich mehr als
	# zwei stauen (Rueckkehr, Zeitraffer), faellt die aelteste weg und wird
	# beim neuesten als "weitere" mitgezaehlt.
	var weitere: int = 0
	var wartende: Array[int] = []
	for i in _meldungen.size():
		if _meldungen[i][3] != null:
			wartende.append(i)
	while wartende.size() >= 2:
		var alt: int = wartende.pop_front()
		weitere += 1 + int(_meldungen[alt][4])
		_meldungen.remove_at(alt)
		for j in wartende.size():
			wartende[j] -= 1
	_meldungen.append([absender, text, "", farbe, weitere])
	if not _meldung_laeuft and not pausiert:
		_naechste()


## Startet die naechste wartende Meldung, sobald nichts mehr haelt (je Bild von der Hud).
func anstossen() -> void:
	if not _meldung_laeuft and not _meldungen.is_empty() and not pausiert and not _haelt():
		_naechste()


## Laeuft gerade eine Meldung (fuer die Ortsblase: nie zwei Textquellen)?
func meldung_laeuft() -> bool:
	return _meldung_laeuft and _aktuelles_feld != null and is_instance_valid(_aktuelles_feld)


func _haelt() -> bool:
	return halt.is_valid() and bool(halt.call())


func _naechste() -> void:
	if _meldungen.is_empty() or pausiert or _haelt():
		_meldung_laeuft = false
		_aktuelles_feld = null
		return
	_meldung_laeuft = true
	var e: Array = _meldungen.pop_front()
	var ist_chat: bool = e[3] != null
	var feld := PanelContainer.new()
	# DECKEND. Die Meldung lag vorher halbdurchsichtig ueber der Karte und war
	# vor dem Holzboden unlesbar. Sie blendet nur ganz kurz ein und aus.
	# Eine schmale Pille statt einer grossen Karte: Sie verdeckt die Karte
	# nur kurz und nur in einer Zeile.
	var stil := UiStil.chip(UiStil.PAPIER, float(UiStil.A4), float(UiStil.A1), UiStil.SCHATTEN_Y)
	stil.flaeche.set_border_width_all(UiStil.KONTUR)
	stil.content_margin_left = float(UiStil.A2)
	feld.add_theme_stylebox_override("panel", stil)
	feld.mouse_filter = Control.MOUSE_FILTER_STOP if ist_chat else Control.MOUSE_FILTER_IGNORE
	if ist_chat:
		feld.gui_input.connect(func(ev: InputEvent) -> void:
			var m := ev as InputEventMouseButton
			if m != null and m.pressed and m.button_index == MOUSE_BUTTON_LEFT:
				chat_getippt.emit())
	var unten: bool = not ist_chat
	feld.set_anchors_preset(Control.PRESET_CENTER_BOTTOM if unten else Control.PRESET_CENTER_TOP)
	feld.grow_horizontal = Control.GROW_DIRECTION_BOTH
	if unten:
		feld.grow_vertical = Control.GROW_DIRECTION_BEGIN
	var unten_abstand: float = MELDUNG_UNTEN
	if unten and menue_hoehe.is_valid():
		unten_abstand = maxf(MELDUNG_UNTEN, float(menue_hoehe.call()) + 20.0)
	var oben: float = -unten_abstand if unten else MELDUNG_OBEN + zusatz_oben
	var eigenschaft: String = "offset_bottom" if unten else "offset_top"
	var weg: float = -40.0 if unten else 40.0
	feld.set(eigenschaft, oben)
	add_child(feld)
	_aktuelles_feld = feld
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	feld.add_child(zeile)
	if ist_chat:
		# Absenderfarbe als linke Kante (D1 C9), Rand bleibt Tinte.
		var kante := Panel.new()
		kante.custom_minimum_size = Vector2(8.0, 0.0)
		kante.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var kb := StyleBoxFlat.new()
		kb.bg_color = e[3] as Color
		kb.set_corner_radius_all(4)
		kante.add_theme_stylebox_override("panel", kb)
		zeile.add_child(kante)
		zeile.add_child(UiStil.avatar(String(e[0]), e[3] as Color, 44.0))
	else:
		var bild := UiStil.symbolbild(String(e[2]), 44.0)
		bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile.add_child(bild)
	if not String(e[0]).is_empty():
		var kopf_spalte := VBoxContainer.new()
		kopf_spalte.add_theme_constant_override("separation", -4)
		kopf_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
		kopf_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(kopf_spalte)
		var kopf := UiStil.label(String(e[0]), UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
		kopf_spalte.add_child(kopf)
		if ist_chat and int(e[4]) > 0:
			kopf_spalte.add_child(UiStil.label(UiText.t("weitere") % int(e[4]), UiStil.GR_KLEIN - 2,
				UiStil.TINTE_2, UiStil.FETT))
	if not String(e[1]).is_empty():
		var t := UiStil.label(String(e[1]), UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		t.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		if ist_chat:
			# Chats brechen zweizeilig um, statt mitten im Satz abzubrechen.
			t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			t.max_lines_visible = 2
			t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		else:
			t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			t.clip_text = true
		# Eine Zeile, hoechstens so breit wie der Bildschirm erlaubt.
		var breite: float = UiStil.schrift(UiStil.TEXT_GEWICHT, UiStil.GR_KLEIN).get_string_size(
			String(e[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, UiStil.GR_KLEIN).x
		t.custom_minimum_size = Vector2(minf(breite + 4.0, 400.0 if ist_chat else 320.0), 0.0)
		zeile.add_child(t)
	feld.modulate.a = 0.0
	var ablauf := create_tween()
	ablauf.tween_property(feld, "modulate:a", 1.0, 0.1)
	ablauf.parallel().tween_property(feld, eigenschaft, oben, UiStil.DAUER_KAUF) \
		.from(oben - weg).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	ablauf.tween_interval(CHAT_DAUER if ist_chat else MELDUNG_DAUER)
	ablauf.tween_property(feld, eigenschaft, oben - weg * 0.75, 0.18).set_ease(Tween.EASE_IN)
	ablauf.parallel().tween_property(feld, "modulate:a", 0.0, 0.18)
	ablauf.tween_callback(feld.queue_free)
	ablauf.tween_callback(_naechste)


## Muenzen fliegen von `von` zur Muenze in der Kopfleiste. Das Geld KOMMT an --
## man sieht, wohin es geht.
func muenzen(von: Vector2, anzahl: int = 8) -> void:
	if kopfleiste == null:
		return
	var ziel: Vector2 = kopfleiste.muenze.get_global_rect().get_center()
	for i in range(anzahl):
		var m := UiStil.symbolbild("muenze", 46.0)
		m.size = Vector2(46.0, 46.0)
		m.position = von - m.size * 0.5 + Vector2(randf_range(-40, 40), randf_range(-30, 30))
		add_child(m)
		var start: Vector2 = m.position
		var mitte: Vector2 = (start + ziel) * 0.5 + Vector2(randf_range(-160, 160), randf_range(-120, 40))
		var t := create_tween()
		t.tween_interval(i * 0.045)
		t.tween_method(func(f: float) -> void:
			var a: Vector2 = start.lerp(mitte, f)
			var b: Vector2 = mitte.lerp(ziel - m.size * 0.5, f)
			m.position = a.lerp(b, f), 0.0, 1.0, 0.55).set_ease(Tween.EASE_IN)
		t.tween_callback(func() -> void:
			m.queue_free()
			kopfleiste.muenze_puls())


## Ein Betrag steigt ueber einem Bildschirmpunkt auf -- mittig darueber und
## immer ganz im Bild. Vorher stand er mit festem Versatz links vom Punkt und
## klebte an Stationen am Bildrand halb ausserhalb.
func betrag(an: Vector2, text: String, farbe: Color = UiStil.GOLD) -> void:
	if pausiert:
		return
	# Gleiche Werte kurz hintereinander werden zu einer Zahl: sonst stapeln sich
	# zwei "+7,1" uebereinander und lesen sich wie ein Fehler.
	var jetzt: int = Time.get_ticks_msec()
	if text == _letzter_betrag and jetzt - _letzter_betrag_ms < 900:
		return
	_letzter_betrag = text
	_letzter_betrag_ms = jetzt
	var l := UiStil.label_kontur(text, UiStil.GR_TITEL, farbe)
	add_child(l)
	var groesse: Vector2 = l.get_combined_minimum_size()
	var flaeche: Vector2 = get_viewport_rect().size
	var pos: Vector2 = an - groesse * 0.5
	pos.x = clampf(pos.x, RAND, flaeche.x - groesse.x - RAND)
	pos.y = clampf(pos.y, Kopfleiste.unterkante() + RAND, flaeche.y - Menueleiste.HOEHE - groesse.y)
	l.position = pos
	l.pivot_offset = groesse * 0.5
	l.scale = Vector2(0.6, 0.6)
	var t := create_tween().set_parallel(true)
	t.tween_property(l, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(l, "position:y", pos.y - 90.0, 0.9).set_ease(Tween.EASE_OUT)
	t.tween_property(l, "modulate:a", 0.0, 0.35).set_delay(0.55)
	t.chain().tween_callback(l.queue_free)


## Ein Verlust, rot und ohne Muenzen -- ehrlich, aber kurz. `an` ist die
## LINKE Kante: Die Zahl steht klein neben dem Einkommen in der Kopfleiste und
## sinkt nur ein Stueck. Frei ueber der Karte landete sie auf dem Ziel-Chip.
func verlust(an: Vector2, text: String) -> void:
	if pausiert:
		return
	var l := UiStil.label(text, UiStil.GR_KLEIN + 1, UiStil.WARNUNG_TEXT, UiStil.FETT)
	add_child(l)
	var groesse: Vector2 = l.get_combined_minimum_size()
	var flaeche: Vector2 = get_viewport_rect().size
	var pos: Vector2 = an - Vector2(0.0, groesse.y * 0.5)
	pos.x = clampf(pos.x, RAND, flaeche.x - groesse.x - RAND)
	l.position = pos
	var t := create_tween().set_parallel(true)
	t.tween_property(l, "position:y", pos.y + 12.0, 0.8).set_ease(Tween.EASE_OUT)
	t.tween_property(l, "modulate:a", 0.0, 0.3).set_delay(0.5)
	t.chain().tween_callback(l.queue_free)


# --- Kauf-Rueckmeldung: Funken, Konfetti, Blitz, Aufschlag, Flug -------------------
#
# Alles mit Tween und CPUParticles2D: keine Shader, keine GPU-Partikel, kein
# Teilchen ueber 60 Stueck. Jeder Effekt raeumt sich selbst auf.

const FUNKEN_DAUER: float = 0.7
const KONFETTI_DAUER: float = 1.5


## Ein Funkenstoss an einem Bildschirmpunkt.
func funken(von: Vector2, farbe: Color = UiStil.KAUFEN, anzahl: int = 14) -> void:
	var p := _partikel(von, anzahl, FUNKEN_DAUER)
	p.direction = Vector2(0.0, -1.0)
	p.spread = 180.0
	p.initial_velocity_min = 180.0
	p.initial_velocity_max = 420.0
	p.gravity = Vector2(0.0, 700.0)
	p.scale_amount_min = 5.0
	p.scale_amount_max = 11.0
	var verlauf := Gradient.new()
	verlauf.set_color(0, Color(UiStil.WEISS, 1.0))
	verlauf.add_point(0.25, farbe)
	verlauf.set_color(verlauf.get_point_count() - 1, Color(farbe, 0.0))
	p.color_ramp = verlauf
	p.emitting = true


## Bunter Regen: Akzent, Gold, Limette, Weiss, Rot.
func konfetti(von: Vector2, anzahl: int = 40) -> void:
	var p := _partikel(von, mini(anzahl, 60), KONFETTI_DAUER)
	p.direction = Vector2(0.0, -1.0)
	p.spread = 70.0
	p.initial_velocity_min = 380.0
	p.initial_velocity_max = 760.0
	p.gravity = Vector2(0.0, 1100.0)
	p.damping_min = 40.0
	p.damping_max = 120.0
	p.angular_velocity_min = -540.0
	p.angular_velocity_max = 540.0
	p.scale_amount_min = 7.0
	p.scale_amount_max = 14.0
	var farben := Gradient.new()
	farben.offsets = PackedFloat32Array([0.0, 0.25, 0.5, 0.75, 1.0])
	farben.colors = PackedColorArray([UiStil.akzent(), UiStil.GOLD, UiStil.KAUFEN, UiStil.WEISS, UiStil.WARNUNG])
	p.color_initial_ramp = farben
	var ausblenden := Gradient.new()
	ausblenden.set_color(0, Color(1, 1, 1, 1))
	ausblenden.add_point(0.7, Color(1, 1, 1, 1))
	ausblenden.set_color(ausblenden.get_point_count() - 1, Color(1, 1, 1, 0))
	p.color_ramp = ausblenden
	p.emitting = true


func _partikel(von: Vector2, anzahl: int, dauer: float) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.position = von
	p.amount = anzahl
	p.lifetime = dauer
	p.one_shot = true
	p.explosiveness = 1.0
	p.emitting = false
	p.local_coords = false
	add_child(p)
	get_tree().create_timer(dauer + 0.3).timeout.connect(p.queue_free)
	return p


## Ein kurzer Farbblitz ueber dem ganzen Bild (Stern-Meilenstein).
func blitz(farbe: Color = UiStil.GOLD, deckkraft: float = 0.25, dauer: float = 0.15) -> void:
	var r := ColorRect.new()
	r.color = Color(farbe, deckkraft)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(r)
	var t := create_tween()
	t.tween_property(r, "modulate:a", 0.0, dauer).from(1.0)
	t.tween_callback(r.queue_free)


## Eine grosse Zahl ("x1,5") schlaegt auf einen Punkt, bleibt kurz und verpufft.
func aufschlag(an: Vector2, text: String, farbe: Color = UiStil.GOLD) -> void:
	var l := UiStil.label_kontur(text, UiStil.GR_RIESIG, farbe)
	add_child(l)
	var groesse: Vector2 = l.get_combined_minimum_size()
	var flaeche: Vector2 = get_viewport_rect().size
	var pos: Vector2 = an - groesse * 0.5
	pos.x = clampf(pos.x, RAND, flaeche.x - groesse.x - RAND)
	pos.y = clampf(pos.y, Kopfleiste.unterkante() + RAND, flaeche.y - Menueleiste.HOEHE - groesse.y)
	l.position = pos
	l.pivot_offset = groesse * 0.5
	l.rotation = deg_to_rad(-6.0)
	l.scale = Vector2(2.4, 2.4)
	l.modulate.a = 0.0
	var t := create_tween()
	t.tween_property(l, "modulate:a", 1.0, 0.06)
	t.parallel().tween_property(l, "scale", Vector2.ONE, 0.22).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_interval(0.6)
	t.tween_property(l, "position:y", pos.y - 50.0, 0.4).set_ease(Tween.EASE_IN)
	t.parallel().tween_property(l, "modulate:a", 0.0, 0.4)
	t.tween_callback(l.queue_free)


## Ein Symbol fliegt von `von` nach `zu` (z. B. der Stern vom Balken in die
## Sternzeile) und federt dort kurz auf.
func flug(symbol: String, von: Vector2, zu: Vector2, kante: float = 56.0, dauer: float = 0.5) -> void:
	var b := UiStil.symbolbild(symbol, kante)
	b.size = Vector2(kante, kante)
	b.pivot_offset = b.size * 0.5
	b.position = von - b.size * 0.5
	add_child(b)
	var ziel: Vector2 = zu - b.size * 0.5
	var t := create_tween()
	t.tween_property(b, "scale", Vector2(1.5, 1.5), dauer * 0.35).from(Vector2(0.4, 0.4)) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(b, "position", ziel, dauer * 0.65).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	t.parallel().tween_property(b, "scale", Vector2.ONE, dauer * 0.65)
	t.tween_callback(b.queue_free)


## Ein Regen aus Symbolen von oben (Weltabschluss: Muenzregen).
func regen(symbol: String = "muenze", anzahl: int = 28, dauer: float = 2.4) -> void:
	var flaeche: Vector2 = get_viewport_rect().size
	var p := CPUParticles2D.new()
	p.position = Vector2(flaeche.x * 0.5, -40.0)
	p.amount = mini(anzahl, 60)
	p.lifetime = dauer
	p.one_shot = true
	p.explosiveness = 0.35
	p.emitting = false
	p.local_coords = false
	p.texture = UiStil.symbol(symbol)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(flaeche.x * 0.5, 10.0)
	p.direction = Vector2(0.0, 1.0)
	p.spread = 12.0
	p.initial_velocity_min = 380.0
	p.initial_velocity_max = 760.0
	p.gravity = Vector2(0.0, 500.0)
	p.angular_velocity_min = -240.0
	p.angular_velocity_max = 240.0
	p.scale_amount_min = 0.35
	p.scale_amount_max = 0.7
	add_child(p)
	p.emitting = true
	get_tree().create_timer(dauer + 0.5).timeout.connect(p.queue_free)
