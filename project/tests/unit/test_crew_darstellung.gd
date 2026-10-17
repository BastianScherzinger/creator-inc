## K6 2a: Mitarbeiter-Figuren an den Stationen und Kunden-Figuren (nur Darstellung).
## Die Datenfunktionen (LebendigDaten) laufen reine Logik; die Figuren selbst werden ohne
## Frames aufgebaut (gleiche_an) und ueber den Kern gesteuert. Der Kern bleibt unveraendert.
extends GdUnitTestSuite

const WELTEN: Array[String] = ["zimmer", "auftrag", "webseiten", "buero", "produkt", "kapital"]


func _regeln() -> Dictionary:
	return LebendigDaten.laden_regeln()


## Ein Kern mit eigener Crew an der Annahme (Freischaltung ueber die Stationsstufe) in Welt `welt`.
func _kern(welt: String, index: int) -> GameCore:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/%s.json" % welt)) as Dictionary
	roh["crew_kosten_faktor"] = 1.0
	roh["crew"] = {"station_intake": {"raenge": [
		{"kosten": 100.0, "faktor": 1.1}, {"kosten": 1000.0, "faktor": 1.2},
		{"kosten": 10000.0, "faktor": 1.35}]}}
	return GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), index)


# --- Daten ------------------------------------------------------------------------

func test_raenge_sehen_verschieden_aus() -> void:
	var r: Dictionary = _regeln()
	var eins: Dictionary = LebendigDaten.crew_rang_look(1, r)
	var zwei: Dictionary = LebendigDaten.crew_rang_look(2, r)
	var drei: Dictionary = LebendigDaten.crew_rang_look(3, r)
	assert_bool(eins.is_empty()).is_false()
	assert_float(float(zwei["skala"])).is_greater(float(eins["skala"]))
	assert_float(float(drei["skala"])).is_greater(float(zwei["skala"]))
	assert_bool(bool(eins["kopfhoerer"])).is_false()
	assert_bool(bool(zwei["kopfhoerer"])).is_true()
	assert_bool(bool(drei["brosche"])).is_true()
	assert_bool(bool(drei["ring"])).is_true()
	assert_bool(LebendigDaten.crew_rang_look(0, r).is_empty()).is_true()
	assert_bool(LebendigDaten.crew_rang_look(4, r).is_empty()).is_true()


func test_platz_aus_den_weltdaten_sonst_standard() -> void:
	var r: Dictionary = _regeln()
	var figuren: Dictionary = {"plaetze": {"station_intake": {"x": 1.5, "z": -0.5, "blick": 90}}}
	var p: Dictionary = LebendigDaten.crew_platz(figuren, "station_intake", r)
	assert_float(float(p["x"])).is_equal(1.5)
	assert_float(float(p["blick"])).is_equal(90.0)
	var std: Dictionary = LebendigDaten.crew_platz({}, "station_buffer", r)
	var vorgabe: Dictionary = (r["crew"] as Dictionary)["platz_standard"] as Dictionary
	assert_float(float(std["z"])).is_equal(float(vorgabe["z"]))


func test_modellname_aus_portrait_figur_oder_ersatz() -> void:
	var r: Dictionary = _regeln()
	var absender: Dictionary = {"mo": "figur_cap"}
	assert_str(LebendigDaten.crew_modell({"portrait": "mo"}, absender, r, 0)).is_equal("figur_cap")
	assert_str(LebendigDaten.crew_modell({"portrait": "figur_packer"}, absender, r, 0)).is_equal("figur_packer")
	assert_str(LebendigDaten.crew_modell({"portrait": "x", "figur": "figur_zopf"}, absender, r, 0)).is_equal("figur_zopf")
	var ersatz: String = LebendigDaten.crew_modell({"portrait": "unbekannt"}, absender, r, 1)
	assert_bool(ersatz.begins_with("figur_")).is_true()


func test_kunden_intervall_sinkt_mit_dem_durchsatz() -> void:
	var r: Dictionary = _regeln()
	assert_float(LebendigDaten.kunden_intervall(0.0, r)).is_less(0.0)
	var langsam: float = LebendigDaten.kunden_intervall(1.0, r)
	var mittel: float = LebendigDaten.kunden_intervall(1000.0, r)
	var schnell: float = LebendigDaten.kunden_intervall(1.0e9, r)
	assert_float(mittel).is_less(langsam)
	assert_float(schnell).is_less(mittel)
	assert_float(schnell).is_greater(0.5)


func test_kunden_weg_nur_mit_start_und_ziel() -> void:
	assert_bool(LebendigDaten.kunden_weg({}).is_empty()).is_true()
	var welt: Dictionary = {"figuren": {"kunden": {"start": {"x": -5, "z": 2}, "ziel": {"x": 1, "z": 2}}}}
	var w: Dictionary = LebendigDaten.kunden_weg(welt)
	assert_vector(w["start"] as Vector3).is_equal(Vector3(-5, 0, 2))
	assert_vector(w["ziel"] as Vector3).is_equal(Vector3(1, 0, 2))
	welt["eingang"] = {"x": 3.0, "z": 4.0}
	assert_vector(LebendigDaten.kunden_weg(welt)["ziel"] as Vector3).is_equal(Vector3(3, 0, 4))


func test_jede_welt_hat_kundenweg_und_namen_fuer_jede_station() -> void:
	var welten: WorldData = WorldData.laden()
	for i in WELTEN.size():
		var welt: Dictionary = welten.welt(i)
		assert_bool(LebendigDaten.kunden_weg(welt).is_empty()).override_failure_message(
			"Welt %s ohne figuren.kunden" % WELTEN[i]).is_false()
		var thema: ThemeData = ThemeData.laden(WELTEN[i])
		var crew: Dictionary = thema.abschnitt("crew")
		for id in Ids.ALL_STATIONS:
			var e: Dictionary = crew.get(String(id), {}) as Dictionary
			assert_bool(String(e.get("name", "")).is_empty()).override_failure_message(
				"Welt %s: crew.%s ohne name" % [WELTEN[i], String(id)]).is_false()
			for rang in [1, 2, 3]:
				assert_bool(LebendigDaten.crew_titel(e, rang).is_empty()).is_false()


# --- Figuren ----------------------------------------------------------------------

func test_ohne_crew_keine_figur_dann_erscheint_sie_mit_rang() -> void:
	var kern: GameCore = _kern("zimmer", 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	var crew := Lebendig.CrewFiguren.new(_regeln())
	add_child(crew)
	crew.gleiche_an(kern, thema)
	assert_array(crew.stationen_mit_figur()).is_empty()
	kern.kapital = 1.0e9
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	crew.gleiche_an(kern, thema)
	assert_array(crew.stationen_mit_figur()).contains(["station_intake"])
	assert_int(crew.rang_von("station_intake")).is_equal(1)
	var figur: Node3D = crew.figur("station_intake")
	assert_object(figur).is_not_null()
	var s1: float = figur.scale.x
	# Rang 2: groesser, mit Kopfhoerer; Rang 3: noch groesser.
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	crew.gleiche_an(kern, thema)
	assert_int(crew.rang_von("station_intake")).is_equal(2)
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	crew.gleiche_an(kern, thema)
	assert_int(crew.rang_von("station_intake")).is_equal(3)
	# Der Auftritt laeuft ueber Tweens (kein Frame im Test): die Zielgroesse steht im Eintrag.
	assert_float(float(((crew._eintraege["station_intake"]) as Dictionary)["skala"])).is_greater(s1 - 0.001)
	crew.queue_free()


func test_figur_steht_an_der_station_plus_platz() -> void:
	var kern: GameCore = _kern("zimmer", 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	kern.kapital = 1.0e9
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	kern.kaufe_crew(Ids.STATION_INTAKE)
	var crew := Lebendig.CrewFiguren.new(_regeln())
	add_child(crew)
	crew.gleiche_an(kern, thema)
	var station: Vector3 = kern.welten.stationen(0)[Ids.STATION_INTAKE] as Vector3
	var platz: Dictionary = LebendigDaten.crew_platz(kern.welten.figuren_roh(0), "station_intake", _regeln())
	var f: Node3D = crew.figur("station_intake")
	assert_float(f.position.x).is_equal_approx(station.x + float(platz["x"]), 0.001)
	assert_float(f.position.z).is_equal_approx(station.z + float(platz["z"]), 0.001)
	crew.queue_free()


func test_kern_bleibt_unveraendert_durch_die_darstellung() -> void:
	var kern: GameCore = _kern("zimmer", 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	kern.kapital = 1.0e9
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	kern.kaufe_crew(Ids.STATION_INTAKE)
	var vorher: float = kern.kapital
	var rang: int = kern.crew_rang(Ids.STATION_INTAKE)
	var crew := Lebendig.CrewFiguren.new(_regeln())
	add_child(crew)
	for n in 3:
		crew.gleiche_an(kern, thema)
	assert_float(kern.kapital).is_equal(vorher)
	assert_int(kern.crew_rang(Ids.STATION_INTAKE)).is_equal(rang)
	crew.queue_free()
