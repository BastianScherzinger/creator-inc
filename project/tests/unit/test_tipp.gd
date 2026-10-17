## Ein Tippen zaehlt genau einmal (RELEASE_PLAN 2.E).
##
## Godot spiegelt jeden Touch als Mausereignis und umgekehrt; beide erreichen
## `gui_input`. Frueher feuerte jede Tippflaeche deshalb doppelt.
extends GdUnitTestSuite


func _touch(gedrueckt: bool) -> InputEventScreenTouch:
	var e := InputEventScreenTouch.new()
	e.pressed = gedrueckt
	e.position = Vector2(10.0, 10.0)
	return e


func _maus(gedrueckt: bool, taste: MouseButton = MOUSE_BUTTON_LEFT) -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.pressed = gedrueckt
	e.button_index = taste
	e.position = Vector2(10.0, 10.0)
	return e


func test_ist_tipp_zaehlt_nur_das_loslassen_der_linken_maustaste() -> void:
	assert_bool(UiStil.ist_tipp(_maus(false))).is_true()
	assert_bool(UiStil.ist_tipp(_maus(true))).is_false()
	assert_bool(UiStil.ist_tipp(_maus(false, MOUSE_BUTTON_RIGHT))).is_false()


func test_touch_allein_ist_kein_tipp() -> void:
	assert_bool(UiStil.ist_tipp(_touch(false))).is_false()
	assert_bool(UiStil.ist_tipp(_touch(true))).is_false()


func test_tippbar_feuert_bei_touch_und_maus_genau_einmal() -> void:
	var karte := PanelContainer.new()
	var zaehler: Array = [0]
	Menues._tippbar(karte, func() -> void: zaehler[0] += 1)
	# So kommt ein Fingertipp am Geraet an: Touch UND gespiegelte Maus.
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		karte.gui_input.emit(e)
	assert_int(zaehler[0]).is_equal(1)
	karte.free()


func test_tippbar_ignoriert_ein_wischen() -> void:
	var karte := PanelContainer.new()
	var zaehler: Array = [0]
	Menues._tippbar(karte, func() -> void: zaehler[0] += 1)
	var los := _maus(false)
	los.position = Vector2(200.0, 10.0)
	karte.gui_input.emit(_maus(true))
	karte.gui_input.emit(los)
	assert_int(zaehler[0]).is_equal(0)
	karte.free()


func test_tippflaeche_der_hud_zaehlt_einmal() -> void:
	# Dieselbe Regel gilt fuer jede Tippflaeche, die ist_tipp benutzt.
	var zaehler: Array = [0]
	var fl := Control.new()
	fl.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			zaehler[0] += 1)
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		fl.gui_input.emit(e)
	assert_int(zaehler[0]).is_equal(1)
	fl.free()


# --- Lieferkiste und Stapel (K3 B2) ---------------------------------------------

func _marker_mit_moment(art: StringName) -> Kartenmarker:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.momente.erzwinge(art)
	for i in range(400):
		kern.tick(0.25)
		if kern.momente.laeuft() and kern.momente.art == art:
			break
	var m := Kartenmarker.new()
	m.kern = kern
	m._baue_kiste()
	m._baue_stapel()
	return m


func test_kiste_und_stapel_haben_tippflaechen_von_96_px() -> void:
	var m := _marker_mit_moment(MomentSystem.ART_KISTE)
	for feld in [m._kiste, m._stapel]:
		var c: Control = feld as Control
		assert_float(c.custom_minimum_size.x).is_greater_equal(96.0)
		assert_float(c.custom_minimum_size.y).is_greater_equal(96.0)
	assert_bool(m.tippflaechen().has(m._kiste)).is_true()
	assert_bool(m.tippflaechen().has(m._stapel)).is_true()
	m.free()


func test_kiste_feuert_bei_touch_und_maus_genau_einmal() -> void:
	var m := _marker_mit_moment(MomentSystem.ART_KISTE)
	var zaehler: Array = [0]
	m.moment_getippt.connect(func(_von: Vector2) -> void: zaehler[0] += 1)
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		m._kiste.gui_input.emit(e)
	assert_int(zaehler[0]).is_equal(1)
	m.free()


func test_stapel_tipp_raeumt_genau_einmal_ab() -> void:
	var m := _marker_mit_moment(MomentSystem.ART_STAPEL)
	add_child(m)
	assert_bool(m.kern.momente.ist_stapel()).is_true()
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		m._stapel.gui_input.emit(e)
	assert_int(m.kern.momente.stapel_gesamt).is_equal(1)
	assert_bool(m.kern.schub_laeuft()).is_true()
	m.free()
