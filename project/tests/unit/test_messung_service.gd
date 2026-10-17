## K3 C3: Die lokale Messung -- Ereignisse, Ringpuffer, Datei, Datenschutz.
## Ohne SceneTree-Frames: Die Uhr ist ein Wert, den der Test selbst vorstellt.
extends GdUnitTestSuite

const TESTDATEI: String = "user://test_messung.json"

var _ms: Array[int] = [0]


func _dienst(grenzen: Dictionary = {}) -> MessungService:
	if FileAccess.file_exists(TESTDATEI):
		DirAccess.remove_absolute(TESTDATEI)
	_ms[0] = 0
	var g: Dictionary = MessungService.lade_grenzen()
	g.merge(grenzen, true)
	var dienst := MessungService.new(TESTDATEI, g)
	dienst.uhr = func() -> int: return _ms[0]
	return dienst


func after_test() -> void:
	if FileAccess.file_exists(TESTDATEI):
		DirAccess.remove_absolute(TESTDATEI)


func test_start_traegt_varianten_und_welt() -> void:
	var d := _dienst()
	d.starte("w1", {"karte": "b", "pfeil": "a"})
	var liste: Array = d.ereignisse()
	assert_int(liste.size()).is_equal(1)
	assert_str(String((liste[0] as Dictionary)["e"])).is_equal("start")
	assert_str(String((liste[0] as Dictionary)["w"])).is_equal("w1")
	var daten: Dictionary = JSON.parse_string(d.als_json()) as Dictionary
	var sitzung: Dictionary = (daten["sitzungen"] as Array)[0] as Dictionary
	assert_str(String((sitzung["ab"] as Dictionary)["karte"])).is_equal("b")


func test_zeit_seit_start_in_sekunden() -> void:
	var d := _dienst()
	d.starte("w1", {})
	_ms[0] = 4250
	d.ereignis(&"kauf", "w1", "x")
	var letztes: Dictionary = d.ereignisse().back() as Dictionary
	assert_float(float(letztes["t"])).is_equal_approx(4.3, 0.051)
	assert_str(String(letztes["d"])).is_equal("x")


func test_erster_tipp_nur_einmal() -> void:
	var d := _dienst()
	d.starte("w1", {})
	d.tipp(&"tipp_leer", "w1")
	d.tipp(&"tipp_station", "w1", "a")
	d.tipp(&"tipp_plakette", "w1", "b")
	var arten: Array[String] = []
	for e in d.ereignisse():
		arten.append(String((e as Dictionary)["e"]))
	assert_int(arten.count("erster_tipp")).is_equal(1)
	assert_array(arten).is_equal(["start", "erster_tipp", "tipp_leer", "tipp_station", "tipp_plakette"])


func test_unbekanntes_ereignis_wird_verworfen() -> void:
	var d := _dienst()
	d.starte("w1", {})
	d.ereignis(&"dein_name", "w1")
	assert_int(d.anzahl_ereignisse()).is_equal(1)


func test_ringpuffer_haelt_grenze_und_wirft_aeltestes_weg() -> void:
	var d := _dienst({"max_ereignisse": 10})
	d.starte("w1", {})
	for i in range(50):
		_ms[0] = i * 1000
		d.ereignis(&"kauf", "w1", i)
	assert_int(d.anzahl_ereignisse()).is_equal(10)
	assert_int(int((d.ereignisse()[0] as Dictionary)["d"])).is_equal(40)
	assert_int(int((d.ereignisse().back() as Dictionary)["d"])).is_equal(49)


func test_sitzungen_begrenzt_und_nummeriert() -> void:
	var g: Dictionary = {"max_sitzungen": 3}
	if FileAccess.file_exists(TESTDATEI):
		DirAccess.remove_absolute(TESTDATEI)
	for i in range(5):
		var d := MessungService.new(TESTDATEI, MessungService.lade_grenzen().merged(g, true))
		d.uhr = func() -> int: return 0
		d.starte("w1", {})
		d.sitzung_ende("w1")
	var d2 := MessungService.new(TESTDATEI, MessungService.lade_grenzen().merged(g, true))
	assert_int(d2.anzahl_sitzungen()).is_equal(3)
	var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TESTDATEI)) as Dictionary
	var nummern: Array[int] = []
	for s in roh["sitzungen"] as Array:
		nummern.append(int((s as Dictionary)["sitzung"]))
	assert_array(nummern).is_equal([3, 4, 5])


func test_speichern_und_zurueckladen() -> void:
	var d := _dienst()
	d.starte("w1", {"karte": "a"})
	d.ereignis(&"raum", "w1", {"id": "bereich_1", "n": 1})
	assert_bool(d.speichere()).is_true()
	assert_bool(FileAccess.file_exists(TESTDATEI)).is_true()
	var neu := MessungService.new(TESTDATEI, MessungService.lade_grenzen())
	assert_int(neu.anzahl_ereignisse()).is_equal(2)


func test_tick_drosselt_das_schreiben() -> void:
	var d := _dienst({"speichern_alle_sekunden": 10.0})
	d.starte("w1", {})
	d.tick(5.0)
	assert_bool(FileAccess.file_exists(TESTDATEI)).is_false()
	d.tick(6.0)
	assert_bool(FileAccess.file_exists(TESTDATEI)).is_true()


func test_inaktiv_schreibt_nichts() -> void:
	var d := _dienst({"aktiv": false})
	d.starte("w1", {})
	d.ereignis(&"kauf", "w1")
	assert_int(d.anzahl_ereignisse()).is_equal(0)
	assert_bool(d.speichere()).is_false()
	assert_bool(FileAccess.file_exists(TESTDATEI)).is_false()


func test_kein_personenbezug_in_der_datei() -> void:
	var d := _dienst()
	d.starte("w1", {"karte": "a"})
	d.tipp(&"tipp_station", "w1", "x")
	d.sitzung_ende("w1")
	var erlaubt: Array[String] = ["version", "sitzungen", "sitzung", "ab", "args", "ereignisse", "t", "e", "w", "d"]
	var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TESTDATEI)) as Dictionary
	for schluessel in roh.keys():
		assert_bool(erlaubt.has(String(schluessel))).is_true()
	for s in roh["sitzungen"] as Array:
		for schluessel in (s as Dictionary).keys():
			assert_bool(erlaubt.has(String(schluessel))).is_true()
		for e in (s as Dictionary)["ereignisse"] as Array:
			for schluessel in (e as Dictionary).keys():
				assert_bool(erlaubt.has(String(schluessel))).is_true()


func test_alle_ereignisse_der_aufgabe_sind_erlaubt() -> void:
	var g: Dictionary = MessungService.lade_grenzen()
	for art in ["start", "erster_tipp", "tipp_leer", "tipp_station", "tipp_plakette", "kauf", "raum",
			"moment", "angebot_gezeigt", "angebot_genommen", "angebot_abgelehnt", "sitzung_ende"]:
		assert_bool((g["ereignisse"] as Array).has(art)).is_true()
