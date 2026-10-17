## K6 (Bastian 16.10.): Plaketten reagieren auf jeden Tipp, und den Zoom bestimmt der Spieler.
##
## Fehler 1: Ein Tipp auf eine Raum-Plakette im Ueberblick tat nichts. Die Plakette
## wurde jedes Bild kurz unsichtbar und wieder sichtbar gesetzt; Godot nimmt einem
## Feld dabei den Maus-Fokus, das Maus-Loslassen kam nie an -- und gezaehlt wurde
## nur das Maus-Loslassen. Jetzt: TippErkenner (Maus ODER Touch, Druck + Loslassen
## innerhalb der Schwelle) und die Sichtbarkeit wird je Bild genau einmal gesetzt.
## Fehler 2: Nach dem Pinch rastete die Kamera ein. Jetzt bleibt der Zoom.
extends GdUnitTestSuite

const KameraSkript := preload("res://game/world/world_camera.gd")
const SCHWELLE: float = 14.0


func _touch(gedrueckt: bool, pos: Vector2 = Vector2(10.0, 10.0), index: int = 0) -> InputEventScreenTouch:
	var e := InputEventScreenTouch.new()
	e.pressed = gedrueckt
	e.position = pos
	e.index = index
	return e


func _zug(pos: Vector2, index: int = 0) -> InputEventScreenDrag:
	var e := InputEventScreenDrag.new()
	e.position = pos
	e.index = index
	return e


func _maus(gedrueckt: bool, pos: Vector2 = Vector2(10.0, 10.0)) -> InputEventMouseButton:
	var e := InputEventMouseButton.new()
	e.pressed = gedrueckt
	e.button_index = MOUSE_BUTTON_LEFT
	e.position = pos
	return e


func _maus_zug(pos: Vector2) -> InputEventMouseMotion:
	var e := InputEventMouseMotion.new()
	e.position = pos
	e.button_mask = MOUSE_BUTTON_MASK_LEFT
	return e


## Wie viele Tipps erkennt ein frischer Erkenner in dieser Folge?
func _tipps(folge: Array, schwelle: float = SCHWELLE) -> int:
	var erkenner := TippErkenner.new(schwelle)
	var n: int = 0
	for e in folge:
		if erkenner.auswerten(e as InputEvent):
			n += 1
	return n


# --- TippErkenner ----------------------------------------------------------------------

func test_schwelle_kommt_aus_sheet_json() -> void:
	assert_float(TippErkenner.new().schwelle).is_equal(Sheet.tipp_schwelle())
	assert_float(Sheet.tipp_schwelle()).is_greater(0.0)


func test_finger_am_geraet_touch_und_gespiegelte_maus_zaehlt_einmal() -> void:
	assert_int(_tipps([_touch(true), _maus(true), _touch(false), _maus(false)])).is_equal(1)
	assert_int(_tipps([_maus(true), _touch(true), _maus(false), _touch(false)])).is_equal(1)


## Der eigentliche Fehler: Das Maus-Loslassen fehlt (Feld verlor den Maus-Fokus).
func test_tipp_ohne_maus_loslassen_zaehlt_ueber_touch() -> void:
	assert_int(_tipps([_maus(true), _touch(true), _touch(false)])).is_equal(1)


func test_nur_maus_und_nur_touch_zaehlen_je_einmal() -> void:
	assert_int(_tipps([_maus(true), _maus(false)])).is_equal(1)
	assert_int(_tipps([_touch(true), _touch(false)])).is_equal(1)


func test_kleines_zittern_unter_der_schwelle_ist_ein_tipp() -> void:
	var p := Vector2(10.0 + SCHWELLE - 1.0, 10.0)
	assert_int(_tipps([_touch(true), _zug(p), _touch(false, p)])).is_equal(1)
	assert_int(_tipps([_maus(true), _maus_zug(p), _maus(false, p)])).is_equal(1)


func test_wisch_ueber_der_schwelle_ist_kein_tipp() -> void:
	var weit := Vector2(10.0 + SCHWELLE + 30.0, 10.0)
	# Hin und zurueck: Das Loslassen liegt wieder am Start, gezaehlt wird trotzdem nicht.
	assert_int(_tipps([_touch(true), _zug(weit), _zug(Vector2(10.0, 10.0)), _touch(false)])).is_equal(0)
	assert_int(_tipps([_maus(true), _maus_zug(weit), _maus(false)])).is_equal(0)
	assert_int(_tipps([_maus(true), _maus(false, weit)])).is_equal(0)
	assert_int(_tipps([_touch(true), _touch(false, weit)])).is_equal(0)


func test_zweiter_finger_macht_den_tipp_zum_pinch() -> void:
	assert_int(_tipps([_touch(true), _maus(true), _touch(true, Vector2(200.0, 10.0), 1),
		_touch(false, Vector2(200.0, 10.0), 1), _touch(false), _maus(false)])).is_equal(0)


func test_loslassen_ohne_druck_zaehlt_nicht() -> void:
	assert_int(_tipps([_touch(false), _maus(false)])).is_equal(0)


func test_verwaister_druck_stoert_den_naechsten_tipp_nicht() -> void:
	# Druck ohne Loslassen (Feld war weg), dann ein ganz normaler Tipp woanders.
	var dort := Vector2(300.0, 300.0)
	assert_int(_tipps([_maus(true), _touch(true, dort), _maus(true, dort), _touch(false, dort), _maus(false, dort)])).is_equal(1)


func test_feld_bewegt_sich_unter_ruhendem_finger() -> void:
	# Lokal wandert der Punkt (das Feld folgt der Karte), im Bild steht der Finger still.
	var erkenner := TippErkenner.new(SCHWELLE)
	erkenner.auswerten(_touch(true, Vector2(10.0, 10.0)), Transform2D(0.0, Vector2(100.0, 100.0)))
	var los := _touch(false, Vector2(-30.0, 10.0))
	assert_bool(erkenner.auswerten(los, Transform2D(0.0, Vector2(140.0, 100.0)))).is_true()


# --- Kartenmarker: jede Tippflaeche nimmt den TippErkenner ---------------------------------

func _marker() -> Kartenmarker:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.kapital = 5000.0
	var kamera: Camera3D = auto_free(Camera3D.new())
	kamera.projection = Camera3D.PROJECTION_ORTHOGONAL
	kamera.size = 40.0
	add_child(kamera)
	kamera.look_at_from_position(Vector3(12.0, 12.0, 12.0), Vector3.ZERO)
	var m: Kartenmarker = auto_free(Kartenmarker.new())
	m.thema = ThemeData.laden(kern.welt_id())
	add_child(m)
	var bereiche: Dictionary = kern.welten.bereich_positionen(kern.welt_index)
	bereiche[Kartenmarker.START_RAUM] = Vector3.ZERO
	m.aufbauen(kern, kamera, kern.welten.stationen_anzeige(kern.welt_index), bereiche)
	return m


func test_plakette_im_ueberblick_oeffnet_schnellkauf_auch_ohne_maus_loslassen() -> void:
	var m := _marker()
	m.kern.kapital = 0.0
	assert_bool(m.ist_ueberblick()).is_true()
	var gemeldet: Array[StringName] = []
	m.bereich_schnellkauf.connect(func(id: StringName) -> void: gemeldet.append(id))
	var bereich: StringName = m._schilder.keys()[0] as StringName
	var plakette: Control = m._schilder[bereich] as Control
	for e in [_maus(true), _touch(true), _touch(false)]:
		plakette.gui_input.emit(e)
	assert_int(gemeldet.size()).is_equal(1)
	assert_str(String(gemeldet[0])).is_equal(String(bereich))
	# Am Geraet: Touch + gespiegelte Maus -- weiterhin genau einmal.
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		plakette.gui_input.emit(e)
	assert_int(gemeldet.size()).is_equal(2)


func test_rand_tab_kaufchip_und_blase_zaehlen_genau_einmal() -> void:
	var m := _marker()
	var zaehler: Dictionary = {"moment": 0, "auftrag": 0}
	m.moment_getippt.connect(func(_von: Vector2) -> void: zaehler["moment"] += 1)
	m.auftrag_getippt.connect(func(_von: Vector2) -> void: zaehler["auftrag"] += 1)
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		m._blase.gui_input.emit(e)
		m._auftrag.gui_input.emit(e)
	assert_int(int(zaehler["moment"])).is_equal(1)
	assert_int(int(zaehler["auftrag"])).is_equal(1)
	var richtung: Array[StringName] = []
	m.bereich_richtung.connect(func(id: StringName) -> void: richtung.append(id))
	m._tab_bereich = m._schilder.keys()[0] as StringName
	for e in [_maus(true), _touch(true), _touch(false)]:
		m._tab.gui_input.emit(e)
	assert_int(richtung.size()).is_equal(1)


## Die Ursache von Fehler 1: Eine sichtbare Plakette darf in einem Bild nie kurz
## unsichtbar werden -- das nimmt ihr den Maus-Fokus.
func test_sichtbare_plakette_flackert_nicht_unsichtbar() -> void:
	var m := _marker()
	m._process(0.0)
	var wechsel: Array = [0]
	for flaeche in m._schilder.values():
		var c: Control = flaeche as Control
		if c.visible:
			c.visibility_changed.connect(func() -> void: wechsel[0] += 1)
	if m._tab.visible:
		m._tab.visibility_changed.connect(func() -> void: wechsel[0] += 1)
	for i in range(3):
		m._process(0.0)
	assert_int(int(wechsel[0])).is_equal(0)


# --- Kamera: der Spieler bestimmt den Zoom ------------------------------------------------

func _kamera() -> Camera3D:
	var kamera: Camera3D = auto_free(KameraSkript.new())
	add_child(kamera)
	kamera.setze_grenzen(Rect2(-10.0, -10.0, 20.0, 20.0), 10.0, 65.0)
	kamera.setze_stufen(16.0, 59.0)
	return kamera


func _pinch(kamera: Camera3D, von: float, bis: float) -> void:
	var mitte := Vector2(360.0, 600.0)
	kamera._unhandled_input(_touch(true, mitte - Vector2(von * 0.5, 0.0), 0))
	kamera._unhandled_input(_touch(true, mitte + Vector2(von * 0.5, 0.0), 1))
	var schritte: int = 8
	for k in range(1, schritte + 1):
		var abstand: float = lerpf(von, bis, float(k) / schritte)
		kamera._unhandled_input(_zug(mitte - Vector2(abstand * 0.5, 0.0), 0))
		kamera._unhandled_input(_zug(mitte + Vector2(abstand * 0.5, 0.0), 1))
	kamera._unhandled_input(_touch(false, mitte + Vector2(bis * 0.5, 0.0), 1))
	kamera._unhandled_input(_touch(false, mitte - Vector2(bis * 0.5, 0.0), 0))


func test_pinch_rastet_nicht_ein() -> void:
	var kamera := _kamera()
	kamera.setze_welt_zoom(40.0)
	_pinch(kamera, 110.0, 160.0)
	var nach_pinch: float = kamera.zoom()
	assert_float(nach_pinch).is_less(40.0)
	# Keine Fahrt, kein Einrasten -- auch nach ein paar Bildern nicht.
	for i in range(10):
		kamera._process(0.1)
	assert_float(kamera.zoom()).is_equal_approx(nach_pinch, 0.001)
	assert_float(kamera.size).is_equal_approx(nach_pinch, 0.001)


func test_zoom_frei_bis_zu_den_grenzen() -> void:
	var kamera := _kamera()
	kamera.setze_welt_zoom(30.0)
	_pinch(kamera, 110.0, 520.0)
	assert_float(kamera.zoom()).is_greater_equal(10.0)
	_pinch(kamera, 520.0, 30.0)
	assert_float(kamera.zoom()).is_less_equal(65.0)
	# Zwischen den Stufen bleibt jeder Wert stehen.
	kamera.setze_welt_zoom(33.0)
	assert_float(kamera.zoom()).is_equal(33.0)


func test_stufe_folgt_dem_aktuellen_zoom() -> void:
	var kamera := _kamera()
	var schwelle: float = Kartenmarker.hinweis("lod_grenze_zoom")
	assert_float(kamera.schwelle).is_equal(schwelle)
	kamera.setze_welt_zoom(schwelle - 1.0)
	assert_str(String(kamera.stufe())).is_equal("raum")
	assert_str(String(kamera.doppeltipp_ziel())).is_equal("ueberblick")
	kamera.setze_welt_zoom(schwelle + 1.0)
	assert_str(String(kamera.stufe())).is_equal("ueberblick")
	assert_str(String(kamera.doppeltipp_ziel())).is_equal("raum")
	assert_str(String(KameraSkript.stufe_fuer(schwelle + 0.01, schwelle))).is_equal("ueberblick")
	assert_str(String(KameraSkript.stufe_fuer(schwelle, schwelle))).is_equal("raum")


func test_betrete_aendert_den_zoom_nur_nach_doppeltipp() -> void:
	var kamera := _kamera()
	kamera.setze_welt_zoom(40.0)
	kamera.setze_blickpunkt(Vector3.ZERO)
	# Sichtbarer Raum, kein Doppeltipp: nichts bewegt sich.
	var blick: Vector3 = kamera.blickpunkt()
	kamera.betrete(Vector3(1.0, 0.8, 1.0), 400.0, 16.0, 0.0)
	assert_float(kamera.zoom()).is_equal(40.0)
	assert_vector(kamera.blickpunkt()).is_equal(blick)
	assert_bool(kamera.hat_rueckkehr()).is_false()
	assert_bool(kamera.kehre_zurueck()).is_false()
	# Nach einem Doppeltipp (bewusste Geste) darf betrete zoomen.
	kamera._doppeltipp_offen = true
	kamera.betrete(Vector3(1.0, 0.8, 1.0), 400.0, 16.0, 0.0)
	assert_bool(kamera._doppeltipp_offen).is_false()
	# Jede neue Beruehrung nimmt dem Doppeltipp das Recht auf die Fahrt.
	kamera._doppeltipp_offen = true
	kamera._input(_touch(true))
	assert_bool(kamera._doppeltipp_offen).is_false()


func test_ruck_beim_raumkauf_bewegt_nichts() -> void:
	var kamera := _kamera()
	var vorher: Vector3 = kamera.global_position
	kamera.ruck()
	assert_vector(kamera.global_position).is_equal(vorher)


# --- K6 §4.3: Plakette = Kaufknopf --------------------------------------------------------

func _tippe(feld: Control) -> void:
	for e in [_touch(true), _maus(true), _touch(false), _maus(false)]:
		feld.gui_input.emit(e)


func test_langdruck_meldet_genau_einmal_und_ist_dann_kein_tipp() -> void:
	var erkenner := TippErkenner.new(SCHWELLE, 400)
	assert_bool(erkenner.auswerten(_touch(true), Transform2D.IDENTITY, 1000)).is_false()
	assert_bool(erkenner.pruefe_langdruck(1399)).is_false()
	assert_bool(erkenner.pruefe_langdruck(1400)).is_true()
	assert_bool(erkenner.pruefe_langdruck(1500)).is_false()
	assert_bool(erkenner.auswerten(_touch(false), Transform2D.IDENTITY, 1600)).is_false()
	# Der naechste kurze Druck ist wieder ein Tipp.
	erkenner.auswerten(_touch(true, Vector2(40.0, 40.0)), Transform2D.IDENTITY, 2000)
	assert_bool(erkenner.pruefe_langdruck(2100)).is_false()
	assert_bool(erkenner.auswerten(_touch(false, Vector2(40.0, 40.0)), Transform2D.IDENTITY, 2100)).is_true()


func test_langdruck_wert_kommt_aus_sheet_json() -> void:
	assert_int(TippErkenner.new().langdruck_ms).is_equal(int(Sheet.konfig().get("langdruck_ms", -1)))
	assert_int(TippErkenner.new().langdruck_ms).is_greater(0)


func test_gruene_plakette_oeffnet_das_raummenue_und_kauft_nicht_sofort() -> void:
	# K6 1c (Bastian 16.10.): Tipp = Menue des Raums, kein Sofortkauf mehr.
	var m := _marker()
	m.kern.kapital = 1.0e9
	m._process(0.0)
	var raum: StringName = Kartenmarker.START_RAUM
	assert_str(String(m.plakette_von(raum))).is_equal("kaufbar")
	var sheets: Array[StringName] = []
	m.bereich_schnellkauf.connect(func(id: StringName) -> void: sheets.append(id))
	var kapital_vorher: float = m.kern.kapital
	_tippe(m._schilder[raum] as Control)
	assert_array(sheets).contains_exactly([raum])
	assert_float(m.kern.kapital).is_equal(kapital_vorher)


func test_nicht_gruene_plakette_oeffnet_den_schnellkauf_und_kauft_nichts() -> void:
	var m := _marker()
	m.kern.kapital = 0.0
	m._process(0.0)
	var raum: StringName = Kartenmarker.START_RAUM
	assert_str(String(m.plakette_von(raum))).is_not_equal("kaufbar")
	var geld: float = m.kern.kapital
	var sheets: Array[StringName] = []
	m.bereich_schnellkauf.connect(func(id: StringName) -> void: sheets.append(id))
	_tippe(m._schilder[raum] as Control)
	assert_int(sheets.size()).is_equal(1)
	assert_float(m.kern.kapital).is_equal(geld)


func test_gruene_plakette_zeigt_nutzen_und_preis() -> void:
	var m := _marker()
	m.kern.kapital = 1.0e9
	m.aktualisiere_empfehlung(0.0, true)
	m._process(0.0)
	var schild: Control = (m._schilder[Kartenmarker.START_RAUM] as Control).get_child(0) as Control
	var nutzen: Label = schild.find_child("Nutzen", true, false) as Label
	var wert: Label = schild.find_child("Wert", true, false) as Label
	assert_str(nutzen.text).starts_with("+")
	assert_bool(nutzen.visible).is_true()
	assert_str(wert.text).is_not_empty()


# --- K6 §4.1.6: der Zoom steht im Spielstand ------------------------------------------------

func test_kamera_im_spielstand_rundlauf_und_alter_stand() -> void:
	var s := SaveData.new()
	assert_bool(s.kamera.is_empty()).is_true()
	s.kamera = {"welt": 2, "zoom": 23.6, "x": 1.5, "z": -2.0}
	var zurueck: SaveData = SaveData.from_dict(JSON.parse_string(JSON.stringify(s.to_dict())) as Dictionary)
	assert_int(int(zurueck.kamera["welt"])).is_equal(2)
	assert_float(float(zurueck.kamera["zoom"])).is_equal_approx(23.6, 0.001)
	assert_float(float(zurueck.kamera["z"])).is_equal_approx(-2.0, 0.001)
	# Ein Stand von vor K6 hat kein Feld: leer, kein Fehler.
	var alt: Dictionary = s.to_dict()
	alt.erase("kamera")
	assert_bool(SaveData.from_dict(alt).kamera.is_empty()).is_true()
