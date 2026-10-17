## K3: Menues bleiben beim Scrollen offen, ein Wisch ist nie ein Tipp.
##
## Ursache des Fehlers "Menue geht beim Scrollen weg" (Handy, 16.10.): Das Sheet
## schloss bei JEDEM Wisch nach unten, der mehr als 90 px weit ging -- auch wenn der
## Finger im Inhalt lag. Wer die Liste hochscrollen wollte (Finger nach unten) und
## am oberen Rand anstiess, schloss das Menue. Jetzt zaehlt nur ein Wisch, der im
## Kopf (Griff + Titelstreifen) beginnt.
extends GdUnitTestSuite


func _menue() -> Stationsmenue:
	var kern := GameCore.new()
	kern.kapital = 1.0e9
	var m := Stationsmenue.new()
	m.kern = kern
	m.thema = ThemeData.laden(kern.welt_id())
	add_child(m)
	m.zeige_station(Ids.CHAIN[0])
	m.oeffnen()
	return m


func _beruehrung(m: Sheet, pos: Vector2, gedrueckt: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.position = pos
	e.pressed = gedrueckt
	m._auf_eingabe(e)


func _zug(m: Sheet, pos: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.position = pos
	m._auf_eingabe(e)


## Ein Wisch von `von` nach `bis` in `schritte` Schritten (1 = ein einziger Sprung).
func _wisch(m: Sheet, von: Vector2, bis: Vector2, schritte: int) -> void:
	_beruehrung(m, von, true)
	for i in range(1, schritte + 1):
		_zug(m, von.lerp(bis, float(i) / float(schritte)))
	_beruehrung(m, bis, false)


func test_konfig_hat_schwellen() -> void:
	assert_float(Sheet.tipp_schwelle()).is_greater(0.0)
	assert_float(float(Sheet.konfig()["schliess_wisch_px"])).is_greater(Sheet.tipp_schwelle())
	var rahmen := WischScroll.new()
	assert_int(rahmen.scroll_deadzone).is_equal(int(Sheet.tipp_schwelle()))
	rahmen.free()


func test_wisch_im_inhalt_schliesst_nie() -> void:
	var m: Stationsmenue = _menue()
	var start_y: float = m.kopfzone_bis() + 120.0
	# langsam, schnell (ein Sprung), ueber den Kartenrand hinaus, nach oben
	var faelle: Array[Array] = [
		[Vector2(100.0, start_y), Vector2(100.0, start_y + 400.0), 40],
		[Vector2(100.0, start_y), Vector2(100.0, start_y + 400.0), 1],
		[Vector2(100.0, start_y), Vector2(100.0, start_y + 2000.0), 3],
		[Vector2(100.0, start_y), Vector2(100.0, -300.0), 5],
		[Vector2(100.0, start_y), Vector2(900.0, start_y + 600.0), 8],
	]
	for f in faelle:
		_wisch(m, f[0] as Vector2, f[1] as Vector2, f[2] as int)
		assert_bool(m.ist_offen()).override_failure_message("Wisch im Inhalt %s schloss das Menue" % [f]).is_true()
	m.queue_free()


func test_wisch_im_kopf_schliesst() -> void:
	var m: Stationsmenue = _menue()
	_wisch(m, Vector2(100.0, 10.0), Vector2(100.0, 10.0 + 200.0), 10)
	assert_bool(m.ist_offen()).is_false()
	m.queue_free()


func test_kurzer_oder_aufwaerts_gerichteter_wisch_im_kopf_laesst_offen() -> void:
	var m: Stationsmenue = _menue()
	_wisch(m, Vector2(100.0, 10.0), Vector2(100.0, 10.0 + 40.0), 5)
	assert_bool(m.ist_offen()).is_true()
	_wisch(m, Vector2(100.0, 20.0), Vector2(100.0, -200.0), 5)
	assert_bool(m.ist_offen()).is_true()
	m.queue_free()


func test_wisch_zustand_haengt_nicht_ueber_beruehrungen() -> void:
	var m: Stationsmenue = _menue()
	# Beruehrung im Kopf, losgelassen; danach ein langer Zug OHNE neue Beruehrung
	# (z. B. Finger kam von aussen) darf nichts schliessen.
	_beruehrung(m, Vector2(100.0, 10.0), true)
	_beruehrung(m, Vector2(100.0, 12.0), false)
	_zug(m, Vector2(100.0, 500.0))
	assert_bool(m.ist_offen()).is_true()
	m.queue_free()


func test_beruehrung_im_panel_wird_als_behandelt_markiert() -> void:
	# Eingaben im Panel erreichen nie die Karte: _auf_eingabe nimmt jedes Touch-/Drag-
	# Ereignis an (accept_event); Karte und Kamera sehen es nicht mehr.
	var m: Stationsmenue = _menue()
	var quelltext: String = FileAccess.get_file_as_string("res://game/ui/sheet.gd")
	assert_int(quelltext.count("karte.accept_event()")).is_greater_equal(2)
	var scroll_text: String = FileAccess.get_file_as_string("res://game/ui/wisch_scroll.gd")
	assert_bool(scroll_text.contains("accept_event()")).is_true()
	m.queue_free()
