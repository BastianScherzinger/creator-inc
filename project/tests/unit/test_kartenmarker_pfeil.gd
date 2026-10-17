## K3 A2: Pfeil-Zustaende auf der Karte kommen aus GameCore.empfehlung(), der
## Kaufchip nennt denselben Preis wie das Menue (Befund k3_09: 1.281 vs. 1.454),
## und es pulst nie mehr als EIN Pfeil.
extends GdUnitTestSuite


func _marker(kern: GameCore) -> Kartenmarker:
	var kamera: Camera3D = auto_free(Camera3D.new())
	kamera.projection = Camera3D.PROJECTION_ORTHOGONAL
	kamera.size = 14.0
	add_child(kamera)
	kamera.look_at_from_position(Vector3(12.0, 12.0, 12.0), Vector3.ZERO)
	var m: Kartenmarker = auto_free(Kartenmarker.new())
	m.thema = ThemeData.laden(kern.welt_id())
	add_child(m)
	var bereiche: Dictionary = kern.welten.bereich_positionen(kern.welt_index)
	bereiche[Kartenmarker.START_RAUM] = Vector3.ZERO
	m.aufbauen(kern, kamera, kern.welten.stationen_anzeige(kern.welt_index), bereiche)
	return m


## Der Preis, den das Menue fuer diesen Kauf zeigt.
func _menue_preis(kern: GameCore, kauf: Dictionary) -> float:
	var sid: StringName = StringName(String(kauf["station"]))
	match String(kauf["art"]):
		"stufe":
			return float(kern.vorschau_mehrfach(sid, 1)[1])
		"platz":
			for p in kern.kette.station(sid).ausstattung:
				if p.id == StringName(String(kauf["platz"])):
					return p.naechste_kosten()
		"crew":
			return kern.crew.kosten_naechster(sid)
	return -1.0


func _kaufe(kern: GameCore, kauf: Dictionary) -> void:
	var sid: StringName = StringName(String(kauf["station"]))
	match String(kauf["art"]):
		"stufe":
			kern.upgrade_station(sid)
		"platz":
			kern.kaufe_ausstattung(sid, StringName(String(kauf["platz"])))
		"crew":
			kern.kaufe_crew(sid)


func test_hinweis_daten_sind_da() -> void:
	assert_bool(FileAccess.file_exists(Kartenmarker.HINWEISE_PFAD)).is_true()
	assert_float(Kartenmarker.hinweis("tippziel_min_px")).is_greater_equal(96.0)
	assert_float(Kartenmarker.hinweis("pfeil_haltezeit_s")).is_greater(0.0)
	assert_float(Kartenmarker.hinweis("lod_grenze_zoom")).is_greater(0.0)


func test_chip_preis_ist_menue_preis_und_hoechstens_ein_bester() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var m: Kartenmarker = _marker(kern)
	var arten: Dictionary = {}
	for runde in range(60):
		kern.kapital = 2000.0 + float(runde) * 150.0
		m._empfehlung = {}
		m.aktualisiere_empfehlung(0.0, true)
		var e: Dictionary = m.empfehlung()
		# Die Empfehlung ist die des Kerns (keine eigene Rechnung im Marker).
		var k: Dictionary = kern.empfehlung()
		assert_bool(Kartenmarker._gleicher_kauf(e, k) and e.is_empty() == k.is_empty()).is_true()
		var beste: int = 0
		for id in m.station_positionen.keys():
			var z: StringName = Kartenmarker.pfeil_zustand(kern, id, e)
			if z == &"bester" or z == &"werkzeug":
				beste += 1
		assert_int(beste).override_failure_message("Runde %d: %d pulsende Pfeile" % [runde, beste]).is_less_equal(1)
		if e.is_empty():
			continue
		arten[String(e["art"])] = true
		m._fuelle_kaufchip()
		assert_str(m._kauf_preis.text).override_failure_message(
			"Runde %d: Chip %s, Menue %s (%s)" % [runde, m._kauf_preis.text,
			UiStil.preis(_menue_preis(kern, e)), e]).is_equal(UiStil.preis(_menue_preis(kern, e)))
		_kaufe(kern, e)
		m._empfehlung_alt = true
	assert_bool(arten.has("stufe")).is_true()


func test_zustaende_gruen_grau_bester() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var id: StringName = Ids.CHAIN[0]
	var s: StationModel = kern.kette.station(id)
	kern.kapital = s.naechste_kosten() * 0.5
	assert_str(String(Kartenmarker.pfeil_zustand(kern, id, {}))).is_equal("grau")
	assert_float(Kartenmarker.pfeil_anteil(kern, id)).is_equal_approx(0.5, 0.001)
	kern.kapital = s.naechste_kosten() * 2.0
	assert_str(String(Kartenmarker.pfeil_zustand(kern, id, {}))).is_equal("gruen")
	var stufe: Dictionary = {"art": "stufe", "station": id, "platz": &"", "preis": s.naechste_kosten(), "mehr": 1.0}
	assert_str(String(Kartenmarker.pfeil_zustand(kern, id, stufe))).is_equal("bester")
	var platz: Dictionary = {"art": "platz", "station": id, "platz": &"x", "preis": 1.0, "mehr": 1.0}
	assert_str(String(Kartenmarker.pfeil_zustand(kern, id, platz))).is_equal("werkzeug")
	# Gesperrte Station: kein Pfeil.
	var gesperrt: StationModel = kern.kette.station(Ids.STATION_TRANSPORT)
	if gesperrt != null and not gesperrt.freigeschaltet:
		assert_str(String(Kartenmarker.pfeil_zustand(kern, Ids.STATION_TRANSPORT, {}))).is_equal("")


func test_hysterese_haelt_den_pfeil() -> void:
	var a: Dictionary = {"art": "stufe", "station": &"s1", "platz": &"", "preis": 100.0, "mehr": 1.0}
	var b: Dictionary = {"art": "stufe", "station": &"s2", "platz": &"", "preis": 90.0, "mehr": 1.0}
	# Anderer Kauf, alter noch bezahlbar, Haltezeit nicht um: der alte bleibt.
	assert_str(String(Kartenmarker.waehle_empfehlung(a, b, 100.0, 500.0, 0.5, 2.0)["station"])).is_equal("s1")
	# Haltezeit um: der neue.
	assert_str(String(Kartenmarker.waehle_empfehlung(a, b, 100.0, 500.0, 2.5, 2.0)["station"])).is_equal("s2")
	# Alter nicht mehr bezahlbar (z. B. gerade gekauft, Preis gestiegen): sofort der neue.
	assert_str(String(Kartenmarker.waehle_empfehlung(a, b, 800.0, 500.0, 0.5, 2.0)["station"])).is_equal("s2")
	# Gehaltener Kauf traegt seinen HEUTIGEN Preis.
	assert_float(float(Kartenmarker.waehle_empfehlung(a, b, 120.0, 500.0, 0.5, 2.0)["preis"])).is_equal(120.0)
	# Gar nichts mehr: leer.
	assert_bool(Kartenmarker.waehle_empfehlung(a, {}, 100.0, 500.0, 0.5, 2.0).is_empty()).is_true()


func test_bereich_info_zaehlt_kaeufe_und_sparstand() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.kapital = 0.0
	var start: Dictionary = kern.bereich_info(GameCore.START_RAUM)
	assert_bool(bool(start["gekauft"])).is_true()
	assert_int(int(start["kaeufe_bezahlbar"])).is_equal(0)
	assert_float(float(start["naechster_preis"])).is_greater(0.0)
	kern.kapital = 1.0e9
	start = kern.bereich_info(GameCore.START_RAUM)
	assert_int(int(start["kaeufe_bezahlbar"])).is_greater(0)
	assert_float(float(start["anteil_gespart"])).is_equal(1.0)
	var erster: StringName = kern.bereiche.ids()[0]
	kern.kapital = kern.bereiche.kosten(erster) * 0.25
	var raum: Dictionary = kern.bereich_info(erster)
	assert_bool(bool(raum["gekauft"])).is_false()
	assert_float(float(raum["naechster_preis"])).is_equal(kern.bereiche.kosten(erster))
	assert_float(float(raum["anteil_gespart"])).is_equal_approx(0.25, 0.001)
	assert_int(int(raum["kaeufe_bezahlbar"])).is_equal(0)


func test_jede_station_hat_einen_pfeil_und_jeder_raum_eine_plakette() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var m: Kartenmarker = _marker(kern)
	# A/B-Urteil 16.10.: immer Pfeile je Station und Raum-Plaketten (frueher Variante b).
	assert_int(m._pfeile.size()).is_equal(m._badges.size())
	assert_bool(m._schilder.has(Kartenmarker.START_RAUM)).is_true()


## K3-Fix 1: Raum-Plaketten ueberlappen im Ueberblick nie, hoechstens `maximal` bleiben, und die
## wichtigste (hoechste Prio) gewinnt den Platz.
func test_plaketten_ueberlappen_nie_und_hoechstens_sechs() -> void:
	var wunsch: Array[Rect2] = []
	var prio: Array[float] = []
	for k in range(9):
		wunsch.append(Rect2(100.0 + float(k) * 10.0, 400.0, 160.0, 60.0))
		prio.append(float(k))
	var grenzen := Rect2(8.0, 200.0, 524.0, 800.0)
	var fest: Array[Rect2] = []
	var plaetze: Array[Vector2] = Kartenmarker.platziere_schilder(wunsch, prio, fest, grenzen, 6, true)
	var gesetzt: Array[Rect2] = []
	for k in range(plaetze.size()):
		if plaetze[k].is_finite():
			gesetzt.append(Rect2(plaetze[k], wunsch[k].size))
	assert_int(gesetzt.size()).is_less_equal(6)
	assert_int(gesetzt.size()).is_greater(0)
	for a in range(gesetzt.size()):
		assert_bool(grenzen.encloses(gesetzt[a])).is_true()
		for b in range(a + 1, gesetzt.size()):
			assert_bool(gesetzt[a].intersects(gesetzt[b])).override_failure_message("Plaketten %d und %d ueberlappen" % [a, b]).is_false()
	# Die hoechste Prio (Index 8) ist dabei, die niedrigste (0) nicht.
	assert_bool(plaetze[8].is_finite()).is_true()
	assert_bool(plaetze[0].is_finite()).is_false()


func test_plakette_weicht_festen_rechtecken_aus() -> void:
	var wunsch: Array[Rect2] = [Rect2(100.0, 400.0, 160.0, 60.0)]
	var prio: Array[float] = [1.0]
	var fest: Array[Rect2] = [Rect2(90.0, 390.0, 200.0, 80.0)]
	var plaetze: Array[Vector2] = Kartenmarker.platziere_schilder(wunsch, prio, fest, Rect2(8.0, 200.0, 524.0, 800.0), 6, true)
	assert_bool(plaetze[0].is_finite()).is_true()
	assert_bool(fest[0].intersects(Rect2(plaetze[0], wunsch[0].size))).is_false()


func test_sparen_auf_nahen_raum_macht_ausbauten_grau() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var id: StringName = Ids.CHAIN[0]
	kern.kapital = 1.0e9
	assert_bool(kern.kaufe_bereich(kern.bereiche.ids()[0])).is_true()   # erst ab Raum 2
	var raum: StringName = kern.bereiche.ids()[1]
	var preis: float = kern.bereiche.kosten(raum)
	# Knapp unter dem Raumpreis, Raum im Sparfenster: kein gruener Ausbau.
	kern.kapital = preis * 0.9
	if kern.sparziel() == raum:
		assert_str(String(Kartenmarker.pfeil_zustand(kern, id, {}))).is_equal("grau")
	# Raum bezahlbar: er bleibt das Ziel, bis er gekauft ist -- danach wieder gruen.
	kern.kapital = preis * 1.5
	if kern.sparziel() == raum:
		assert_str(String(Kartenmarker.pfeil_zustand(kern, id, {}))).is_equal("grau")
		assert_bool(kern.kaufe_bereich(raum)).is_true()
	assert_str(String(kern.sparziel())).is_not_equal(String(raum))
