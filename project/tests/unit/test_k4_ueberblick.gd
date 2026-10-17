## K4 P1.1-P1.3: Ueberblick-Schnellkauf, Plakettenzustaende, genau ein Puls.
## Ohne SceneTree-Frames: geprueft werden Entscheidungen und Kaeufe, nicht Tweens.
extends GdUnitTestSuite


func _kern() -> GameCore:
	return GameCore.new(BalanceData.fuer_welt("zimmer"), 0)


func _schnellkauf(kern: GameCore) -> Menues.Schnellkauf:
	var s: Menues.Schnellkauf = auto_free(Menues.Schnellkauf.new())
	s.kern = kern
	s.thema = ThemeData.laden(kern.welt_id())
	add_child(s)
	return s


func _marker(kern: GameCore) -> Kartenmarker:
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


# --- Kern: beste Verbesserung eines Raums ------------------------------------------

func test_empfehlung_im_raum_zeigt_auch_zu_teure_kaeufe() -> void:
	var kern := _kern()
	kern.kapital = 0.0
	var arm: Dictionary = kern.empfehlung_im_raum(GameCore.START_RAUM)
	assert_bool(arm.is_empty()).is_false()
	assert_float(float(arm["preis"])).is_greater(0.0)
	kern.kapital = 1.0e9
	var reich: Dictionary = kern.empfehlung_im_raum(GameCore.START_RAUM)
	assert_float(float(reich["mehr"])).is_greater(0.0)
	assert_float(float(reich["preis"])).is_less_equal(kern.kapital)


func test_empfehlung_im_raum_nur_stationen_des_raums() -> void:
	var kern := _kern()
	kern.kapital = 1.0e9
	var ids: Array[StringName] = Menues.stationen_des_raums(kern, GameCore.START_RAUM)
	for runde in range(20):
		var kauf: Dictionary = kern.empfehlung_im_raum(GameCore.START_RAUM)
		if kauf.is_empty():
			break
		assert_bool(ids.has(StringName(String(kauf["station"])))).is_true()
		assert_bool(kern.kaufe_empfehlung(kauf)).is_true()


# --- Schnellkauf-Panel ---------------------------------------------------------------

func test_schnellkauf_bleibt_offen_und_zeigt_den_naechsten_kauf() -> void:
	var kern := _kern()
	kern.kapital = 1.0e7
	var s := _schnellkauf(kern)
	s.zeige_bereich(GameCore.START_RAUM)
	assert_bool(s.ist_offen()).is_true()
	assert_bool(s.vorschlag.is_empty()).is_false()
	assert_str(s._knopf_preis.text).is_equal(UiStil.preis(float(s.vorschlag["preis"])))
	assert_bool(s._knopf.disabled).is_false()
	var vorher_geld: float = kern.kapital
	var vorher_ertrag: float = kern.einkommen_pro_sekunde()
	var ausgegeben: Array = []
	s.ausgegeben.connect(func(_von: Vector2, text: String) -> void: ausgegeben.append(text))
	for i in range(5):
		s._auf_kauf()
	assert_float(kern.kapital).is_less(vorher_geld)
	assert_float(kern.einkommen_pro_sekunde()).is_greater(vorher_ertrag)
	assert_int(ausgegeben.size()).is_equal(5)
	# Kaufserie: das Panel ist noch offen und hat schon den naechsten Vorschlag.
	assert_bool(s.ist_offen()).is_true()
	assert_bool(s.vorschlag.is_empty()).is_false()


func test_schnellkauf_ohne_geld_kauft_nichts() -> void:
	var kern := _kern()
	kern.kapital = 0.0
	var s := _schnellkauf(kern)
	s.zeige_bereich(GameCore.START_RAUM)
	assert_bool(s._knopf.disabled).is_true()
	assert_bool(s._fehlt.visible).is_true()
	var stufen: int = 0
	for id in Ids.ALL_STATIONS:
		var st: StationModel = kern.kette.station(id)
		if st != null:
			stufen += st.stufe
	s._auf_kauf()
	var danach: int = 0
	for id in Ids.ALL_STATIONS:
		var st: StationModel = kern.kette.station(id)
		if st != null:
			danach += st.stufe
	assert_int(danach).is_equal(stufen)


func test_schnellkauf_gesperrter_raum_kauft_den_raum() -> void:
	var kern := _kern()
	var raum: StringName = kern.bereiche.ids()[0]
	assert_bool(kern.bereiche.ist_gekauft(raum)).is_false()
	kern.kapital = kern.bereiche.kosten(raum) * 0.5
	var s := _schnellkauf(kern)
	s.zeige_bereich(raum)
	assert_bool(s.vorschlag.is_empty()).is_true()
	assert_str(s._knopf_preis.text).is_equal(UiStil.preis(kern.bereiche.kosten(raum)))
	assert_bool(s._knopf.disabled).is_true()
	kern.kapital = kern.bereiche.kosten(raum) + 1.0
	s.aktualisiere()
	assert_bool(s._knopf.disabled).is_false()
	s._auf_kauf()
	assert_bool(kern.bereiche.ist_gekauft(raum)).is_true()
	assert_bool(s.ist_offen()).is_false()


func test_raum_ansehen_meldet_den_raum() -> void:
	var kern := _kern()
	var s := _schnellkauf(kern)
	s.zeige_bereich(GameCore.START_RAUM)
	var gemeldet: Array = []
	s.raum_ansehen.connect(func(id: StringName) -> void: gemeldet.append(id))
	s._ansehen.pressed.emit()
	assert_array(gemeldet).contains_exactly([GameCore.START_RAUM])
	assert_float(s._ansehen.custom_minimum_size.y).is_greater_equal(UiStil.TIPPZIEL)


# --- Plakettenzustaende (P1.2) --------------------------------------------------------

func test_plakette_sagt_genau_eine_sache() -> void:
	var fast: float = Kartenmarker.hinweis("plakette_fast_ab_anteil")
	assert_float(fast).is_greater(0.0)
	var zu: Dictionary = {"gekauft": false, "verfuegbar": false, "kosten": 100.0}
	assert_str(String(Kartenmarker.plaketten_zustand(zu, {}, 1000.0, false, fast)["zustand"])).is_equal("gesperrt")
	var offen: Dictionary = {"gekauft": false, "verfuegbar": true, "kosten": 100.0}
	assert_str(String(Kartenmarker.plaketten_zustand(offen, {}, 100.0, false, fast)["zustand"])).is_equal("kaufbar")
	assert_str(String(Kartenmarker.plaketten_zustand(offen, {}, 100.0 * fast, false, fast)["zustand"])).is_equal("fast")
	assert_str(String(Kartenmarker.plaketten_zustand(offen, {}, 1.0, false, fast)["zustand"])).is_equal("gesperrt")
	var gekauft: Dictionary = {"gekauft": true, "verfuegbar": true, "kosten": 0.0}
	var kauf: Dictionary = {"art": "stufe", "station": &"x", "preis": 50.0, "mehr": 1.0}
	assert_str(String(Kartenmarker.plaketten_zustand(gekauft, kauf, 60.0, true, fast)["zustand"])).is_equal("kaufbar")
	assert_str(String(Kartenmarker.plaketten_zustand(gekauft, kauf, 10.0, true, fast)["zustand"])).is_equal("bremst")
	assert_str(String(Kartenmarker.plaketten_zustand(gekauft, kauf, 49.0, false, fast)["zustand"])).is_equal("fast")
	assert_str(String(Kartenmarker.plaketten_zustand(gekauft, kauf, 1.0, false, fast)["zustand"])).is_equal("ruhig")
	assert_str(String(Kartenmarker.plaketten_zustand(gekauft, {}, 1.0, false, fast)["zustand"])).is_equal("ruhig")
	# Jeder Zustand hat seine eigene Flaechenfarbe.
	var farben: Dictionary = {}
	for z in [&"kaufbar", &"fast", &"gesperrt", &"bremst", &"ruhig"]:
		farben[UiStil.plaketten_farbe(z).to_html()] = true
	assert_int(farben.size()).is_equal(5)


# --- Genau ein Puls (P1.3) -------------------------------------------------------------

func test_ziel_raum_bezahlbarer_raum_geht_vor() -> void:
	assert_str(String(Kartenmarker.ziel_raum(&"bereich_1", true, &"start"))).is_equal("bereich_1")
	assert_str(String(Kartenmarker.ziel_raum(&"bereich_1", false, &"start"))).is_equal("start")
	assert_str(String(Kartenmarker.ziel_raum(&"", false, &""))).is_equal("")


func test_genau_eine_plakette_pulsiert_im_ueberblick() -> void:
	var kern := _kern()
	kern.kapital = 5000.0
	var m := _marker(kern)
	assert_bool(m.ist_ueberblick()).is_true()
	m.aktualisiere_empfehlung(0.0, true)
	assert_bool(m._schilder.has(m.ziel())).is_true()
	# Zu einem Zeitpunkt, an dem der Puls nicht gerade durch 1,0 geht.
	m._zeit = 0.2 / Kartenmarker.hinweis("puls_hz")
	m._process(0.0)
	var pulsierend: int = 0
	for bereich_id in m._schilder.keys():
		var schild: Control = (m._schilder[bereich_id] as Control).get_child(0) as Control
		if schild.scale.x > 1.0 + 1.0e-4:
			pulsierend += 1
			assert_str(String(bereich_id)).is_equal(String(m.ziel()))
	assert_int(pulsierend).is_less_equal(1)
	# Im Ueberblick schwebt kein Kaufchip (die Plakette sagt es), und keine Station pulsiert.
	assert_bool(m._kauf.visible).is_false()
	assert_str(String(m.puls_station())).is_equal("")


func test_im_raum_pulsiert_nur_die_station_des_besten_kaufs() -> void:
	var kern := _kern()
	# Genug fuer einen Ausbau, aber noch nicht fuer den naechsten Raum.
	kern.kapital = kern.bereiche.kosten(kern.bereiche.ids()[0]) * 0.9
	var m := _marker(kern)
	m.kamera.size = 10.0
	m.aktualisiere_empfehlung(0.0, true)
	var beste: StringName = StringName(String(m.empfehlung().get("station", "")))
	assert_bool(beste != &"").is_true()
	assert_bool(m.puls_station() == beste).override_failure_message(
		"%s != %s" % [m.puls_station(), beste]).is_true()
	# Ist der naechste Raum bezahlbar, ist ER das Ziel -- dann pulsiert keine Station.
	kern.kapital = kern.bereiche.kosten(kern.bereiche.ids()[0]) + 1.0
	m.aktualisiere_empfehlung(0.0, true)
	assert_str(String(m.ziel())).is_equal(String(kern.bereiche.ids()[0]))
	assert_str(String(m.puls_station())).is_equal("")
