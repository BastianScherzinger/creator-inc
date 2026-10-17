## Prueft die Regeln der belohnten Werbung (K3 C1): Startschutz, Mindestabstand,
## Tageslimit, Sperrzeit je Platzierung, Sitzungslimit, Tageszaehler.
##
## Alles ohne SceneTree-Frames: Die Dauer ist 0, die Uhr ist eine Zahl, die der
## Test selbst weiterstellt. Getestet wird die Entscheidung, nicht die Wartezeit.
extends GdUnitTestSuite

var _zeit: Array = [1000.0]    ## Referenztyp, damit die Lambda ihn sieht
var _tag: Array = ["2026-10-16"]


func _stub() -> AdServiceStub:
	var stub := auto_free(AdServiceStub.new()) as AdServiceStub
	stub.dauer_sekunden = 0.0
	stub.fehlerquote = 0.0
	_zeit[0] = 1000.0
	_tag[0] = "2026-10-16"
	stub.uhr = func() -> float: return float(_zeit[0])
	stub.datum = func() -> String: return String(_tag[0])
	return stub


func _weiter(sekunden: float) -> void:
	_zeit[0] = float(_zeit[0]) + sekunden


func _ansehen(stub: AdServiceStub, platzierung: StringName) -> int:
	var treffer: Array = [0]
	var f: Callable = func(_p: StringName) -> void: treffer[0] += 1
	stub.belohnung_verdient.connect(f)
	stub.zeige_belohnt(platzierung)
	stub.belohnung_verdient.disconnect(f)
	return int(treffer[0])


func test_neue_platzierungen_sind_konfiguriert() -> void:
	var stub: AdServiceStub = _stub()
	for id in [&"schub", &"offline_verdoppeln", &"raum_sofort", &"ziel_doppelt", &"kiste",
			&"geschenk_doppelt", &"crew_ziehen"]:
		assert_bool(stub.kennt(id)).is_true()


func test_konfiguration_nennt_die_vereinbarten_werte() -> void:
	var daten: Dictionary = AdServiceStub.laden()
	assert_float(float(daten.get("mindestabstand_sekunden", 0.0))).is_equal(180.0)
	assert_int(int(daten.get("hoechstzahl_pro_tag", 0))).is_equal(10)
	var ab: Dictionary = daten.get("erst_ab", {}) as Dictionary
	assert_float(float(ab.get("spielzeit_s", 0.0))).is_equal(300.0)
	assert_str(String(ab.get("bereich", ""))).is_equal("bereich_1")
	assert_float(AdServiceStub.faktor(&"offline_verdoppeln")).is_equal(2.0)
	var stub: AdServiceStub = _stub()
	assert_float(float(stub.wert(&"raum_sofort", "ab_anteil", 0.0))).is_equal(0.7)
	assert_float(float(stub.wert(&"ziel_doppelt", "sperrzeit_sekunden", 0.0))).is_equal(600.0)
	assert_int(int(stub.wert(&"crew_ziehen", "hoechstzahl_pro_tag", 0))).is_equal(1)


func test_startschutz_vor_fuenf_minuten_kein_angebot() -> void:
	var stub: AdServiceStub = _stub()
	stub.setze_stand(299.0, func(_id: StringName) -> bool: return true)
	assert_bool(stub.ist_bereit(&"schub")).is_false()
	assert_str(stub.grund(&"schub")).is_equal("start")
	assert_int(_ansehen(stub, &"schub")).is_equal(0)
	stub.setze_stand(300.0, func(_id: StringName) -> bool: return true)
	assert_bool(stub.ist_bereit(&"schub")).is_true()


func test_vor_minute_fuenf_nirgends_ein_werbeknopf() -> void:
	# Jede konfigurierte Platzierung ist in den ersten fuenf Minuten nicht bereit
	# (auch Offline-Karte und Geschenk) -- ohne ist_bereit zeigt keine Oberflaeche ein ▶.
	var stub: AdServiceStub = _stub()
	var platzierungen: Dictionary = AdServiceStub.laden().get("platzierungen", {}) as Dictionary
	assert_int(platzierungen.size()).is_greater(0)
	for id in platzierungen.keys():
		stub.setze_stand(0.0, func(_b: StringName) -> bool: return true)
		assert_bool(stub.ist_bereit(StringName(id))).is_false()
		stub.setze_stand(299.9, func(_b: StringName) -> bool: return true)
		assert_bool(stub.ist_bereit(StringName(id))).is_false()
		assert_int(_ansehen(stub, StringName(id))).is_equal(0)


func test_startschutz_wartet_auch_auf_den_ersten_raum() -> void:
	var stub: AdServiceStub = _stub()
	stub.setze_stand(5000.0, func(_id: StringName) -> bool: return false)
	assert_bool(stub.ist_bereit(&"schub")).is_false()
	stub.setze_stand(5000.0, func(id: StringName) -> bool: return id == &"bereich_1")
	assert_bool(stub.ist_bereit(&"schub")).is_true()


func test_mindestabstand_gilt_fuer_alle_platzierungen() -> void:
	var stub: AdServiceStub = _stub()
	assert_int(_ansehen(stub, &"schub")).is_equal(1)
	# Eine ANDERE Platzierung ist trotzdem gesperrt: nie zwei Werbungen hintereinander.
	assert_bool(stub.ist_bereit(&"kiste")).is_false()
	assert_str(stub.grund(&"kiste")).is_equal("abstand")
	assert_float(stub.sperrzeit_rest(&"kiste")).is_equal_approx(180.0, 0.01)
	_weiter(179.0)
	assert_bool(stub.ist_bereit(&"kiste")).is_false()
	_weiter(2.0)
	assert_bool(stub.ist_bereit(&"kiste")).is_true()


func test_boost_hat_keine_eigene_sperre_nur_den_mindestabstand() -> void:
	var stub: AdServiceStub = _stub()
	assert_int(_ansehen(stub, &"schub")).is_equal(1)
	_weiter(181.0)
	assert_bool(stub.ist_bereit(&"schub")).is_true()


func test_ziel_doppelt_hat_zehn_minuten_sperre() -> void:
	var stub: AdServiceStub = _stub()
	assert_int(_ansehen(stub, &"ziel_doppelt")).is_equal(1)
	_weiter(200.0)
	assert_bool(stub.ist_bereit(&"ziel_doppelt")).is_false()
	assert_bool(stub.ist_bereit(&"schub")).is_true()
	_weiter(400.0)
	assert_bool(stub.ist_bereit(&"ziel_doppelt")).is_true()


func test_tageslimit_zehn_dann_ist_schluss_und_der_naechste_tag_beginnt_neu() -> void:
	var stub: AdServiceStub = _stub()
	var ausgenommen: Array[StringName] = [&"schub", &"raum_sofort", &"kiste"]
	var n: int = 0
	for i in range(10):
		# Reihum, damit kein Sitzungslimit vor dem Tageslimit greift.
		assert_int(_ansehen(stub, ausgenommen[i % ausgenommen.size()])).is_equal(1)
		n += 1
		_weiter(181.0)
	assert_int(n).is_equal(10)
	assert_int(stub.rest_heute()).is_equal(0)
	assert_str(stub.grund(&"kiste")).is_equal("tag")
	assert_int(_ansehen(stub, &"kiste")).is_equal(0)
	_tag[0] = "2026-10-17"
	assert_int(stub.rest_heute()).is_equal(10)
	assert_bool(stub.ist_bereit(&"kiste")).is_true()


func test_sitzungslimit_boost_acht() -> void:
	var stub: AdServiceStub = _stub()
	for i in range(8):
		_tag[0] = "tag%d" % i     # jeder Durchgang ein neuer Tag: nur das Sitzungslimit zaehlt
		assert_int(_ansehen(stub, &"schub")).is_equal(1)
		_weiter(181.0)
	_tag[0] = "tag9"
	assert_str(stub.grund(&"schub")).is_equal("sitzung")


func test_crew_ziehen_hoechstens_einmal_am_tag() -> void:
	var stub: AdServiceStub = _stub()
	assert_int(_ansehen(stub, &"crew_ziehen")).is_equal(1)
	_weiter(500.0)
	assert_str(stub.grund(&"crew_ziehen")).is_equal("tag")
	_tag[0] = "2026-10-17"
	assert_bool(stub.ist_bereit(&"crew_ziehen")).is_true()


func test_ablehnen_kostet_nichts() -> void:
	# Ein Ladefehler zaehlt weder gegen das Tageslimit noch loest er den Abstand aus.
	var stub: AdServiceStub = _stub()
	stub.fehlerquote = 1.0
	stub.zeige_belohnt(&"schub")
	assert_int(stub.rest_heute()).is_equal(10)
	assert_bool(stub.ist_bereit(&"kiste")).is_true()


func test_tageszaehler_ueberlebt_speichern_und_laden() -> void:
	var stub: AdServiceStub = _stub()
	_ansehen(stub, &"crew_ziehen")
	var gespeichert: Dictionary = stub.zaehler_als_dict()
	var neu: AdServiceStub = _stub()
	neu.zaehler_laden(gespeichert)
	assert_int(neu.rest_heute()).is_equal(9)
	assert_str(neu.grund(&"crew_ziehen")).is_equal("tag")
	# Ein Zaehler von gestern zaehlt heute nicht mehr.
	_tag[0] = "2026-10-18"
	assert_int(neu.rest_heute()).is_equal(10)


func test_angebot_gezeigt_wird_gemeldet() -> void:
	var stub: AdServiceStub = _stub()
	var gemeldet: Array = []
	stub.angebot_gezeigt.connect(func(p: StringName) -> void: gemeldet.append(p))
	stub.melde_angebot(&"kiste")
	assert_int(gemeldet.size()).is_equal(1)
	assert_str(String(gemeldet[0])).is_equal("kiste")
