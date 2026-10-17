## Prueft den Balance-Loader und vor allem seinen Validator.
##
## Der Validator ist die Versicherung gegen stille Tippfehler in den Daten.
## Deshalb wird hier nicht nur geprueft, dass gute Daten durchgehen, sondern
## vor allem, dass schlechte Daten zuverlaessig auffliegen.
extends GdUnitTestSuite


func _minimal_json(ueberschreiben: Dictionary = {}) -> String:
	var stationen := {}
	for id in Ids.ALL_STATIONS:
		stationen[String(id)] = {
			"basis_kosten": 25.0,
			"wachstum": 1.16,
			"basis_durchsatz": 1.0,
			"start_stufe": 1,
		}
	var daten := {
		"start_kapital": 0.0,
		"erloes_pro_einheit": 1.0,
		"offline": {"rate": 0.5, "obergrenze_sekunden": 14400.0,
			"obergrenze_ausgebaut_sekunden": 43200.0},
		"stationen": stationen,
		"unlocks": {"unlock_transport": {"typ": "kapital", "schwelle": 3000.0}},
	}
	daten.merge(ueberschreiben, true)
	return JSON.stringify(daten)


func test_echte_balance_datei_ist_gueltig() -> void:
	# Der wichtigste Test der Datei: Die ausgelieferten Werte muessen passen.
	var daten := BalanceData.laden()
	assert_object(daten).is_not_null()
	var gueltig: bool = daten.validieren()
	if not gueltig:
		for f in daten.fehler:
			push_error(f)
	assert_bool(gueltig).is_true()


func test_alle_stationen_der_kette_vorhanden() -> void:
	var daten := BalanceData.laden()
	for id in Ids.CHAIN:
		assert_bool(daten.stationen.has(String(id))).is_true()


func test_gute_daten_gehen_durch() -> void:
	var daten := BalanceData.aus_text(_minimal_json())
	assert_bool(daten.validieren()).is_true()
	assert_int(daten.fehler.size()).is_equal(0)


func test_fehlende_station_faellt_auf() -> void:
	var roh: Dictionary = JSON.parse_string(_minimal_json())
	(roh["stationen"] as Dictionary).erase(String(Ids.STATION_BUFFER))
	var daten := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(daten.validieren()).is_false()
	assert_str(" ".join(daten.fehler)).contains("station_buffer")


func test_unbekannte_station_faellt_auf() -> void:
	var roh: Dictionary = JSON.parse_string(_minimal_json())
	(roh["stationen"] as Dictionary)["station_tippfehler"] = {
		"basis_kosten": 1.0, "wachstum": 1.1, "basis_durchsatz": 1.0}
	var daten := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(daten.validieren()).is_false()
	assert_str(" ".join(daten.fehler)).contains("Unbekannte Station")


func test_wachstum_unter_eins_faellt_auf() -> void:
	# Waere fatal: Die Kosten wuerden mit jeder Stufe sinken.
	var roh: Dictionary = JSON.parse_string(_minimal_json())
	((roh["stationen"] as Dictionary)[String(Ids.STATION_INTAKE)] as Dictionary)["wachstum"] = 0.9
	var daten := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(daten.validieren()).is_false()
	assert_str(" ".join(daten.fehler)).contains("wachstum")


func test_absurd_hohes_wachstum_faellt_auf() -> void:
	var roh: Dictionary = JSON.parse_string(_minimal_json())
	((roh["stationen"] as Dictionary)[String(Ids.STATION_INTAKE)] as Dictionary)["wachstum"] = 3.0
	var daten := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(daten.validieren()).is_false()


func test_negative_kosten_fallen_auf() -> void:
	var roh: Dictionary = JSON.parse_string(_minimal_json())
	((roh["stationen"] as Dictionary)[String(Ids.STATION_INTAKE)] as Dictionary)["basis_kosten"] = -5.0
	var daten := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(daten.validieren()).is_false()


func test_unsinnige_offline_rate_faellt_auf() -> void:
	var daten := BalanceData.aus_text(_minimal_json({
		"offline": {"rate": 1.7, "obergrenze_sekunden": 14400.0,
			"obergrenze_ausgebaut_sekunden": 43200.0}}))
	assert_bool(daten.validieren()).is_false()
	assert_str(" ".join(daten.fehler)).contains("offline.rate")


func test_ausgebaute_obergrenze_kleiner_als_grundgrenze_faellt_auf() -> void:
	var daten := BalanceData.aus_text(_minimal_json({
		"offline": {"rate": 0.5, "obergrenze_sekunden": 14400.0,
			"obergrenze_ausgebaut_sekunden": 3600.0}}))
	assert_bool(daten.validieren()).is_false()


func test_kaputtes_json_gibt_null() -> void:
	assert_object(BalanceData.aus_text("{ das ist kein json")).is_null()


func test_erzeugte_stationen_haben_die_startstufe() -> void:
	var daten := BalanceData.laden()
	var liste := daten.erzeuge_stationen()
	assert_int(liste.size()).is_equal(Ids.ALL_STATIONS.size())
	var kette := ProductionChain.new(liste)
	# Die drei Startstationen laufen, die spaeteren sind gesperrt
	assert_bool(kette.station(Ids.STATION_INTAKE).freigeschaltet).is_true()
	assert_bool(kette.station(Ids.STATION_TRANSPORT).freigeschaltet).is_false()
	# Und die Kette liefert vom ersten Moment an Durchsatz
	assert_bool(kette.effektiver_durchsatz() > 0.0).is_true()


func test_ziel_minuten_wird_gelesen_und_geprueft() -> void:
	var gut := BalanceData.aus_text(_minimal_json({"ziel_minuten": [90, 100]}))
	assert_bool(gut.validieren()).is_true()
	assert_int(gut.ziel_minuten.size()).is_equal(2)
	var verkehrt := BalanceData.aus_text(_minimal_json({"ziel_minuten": [100, 90]}))
	assert_bool(verkehrt.validieren()).is_false()
	assert_str(" ".join(verkehrt.fehler)).contains("ziel_minuten")
	var zu_kurz := BalanceData.aus_text(_minimal_json({"ziel_minuten": [90]}))
	assert_bool(zu_kurz.validieren()).is_false()


## P6: jede Welt mit Abschluss "alles" nennt ihren Simulator-Korridor in den Daten (K2 4.3).
func test_jede_welt_hat_einen_korridor_in_den_daten() -> void:
	var erwartet := {"zimmer": [75, 80], "auftrag": [70, 80], "webseiten": [80, 90],
		"buero": [90, 100], "produkt": [100, 110], "kapital": [110, 120]}
	for welt_id in erwartet:
		var b := BalanceData.fuer_welt(welt_id)
		assert_bool(b != null).is_true()
		assert_float(float(b.ziel_minuten[0])).is_equal(float(erwartet[welt_id][0]))
		assert_float(float(b.ziel_minuten[1])).is_equal(float(erwartet[welt_id][1]))


## K3 B1: Tempo-Loch. Jede Welt hat die drei Auftraege zwischen Raum 3 und 4, die
## Momente-Abstaende 90/150 und den Stapel-Schub; die Lueckenpruefung steht im Simulator.
func test_k3_pacing_daten_in_jeder_welt() -> void:
	var welten := WorldData.laden()
	for i in range(welten.anzahl()):
		var id: String = welten.id(i)
		var b := BalanceData.fuer_welt(id)
		assert_bool(b.validieren()).override_failure_message("%s: %s" % [id, "
".join(b.fehler)]).is_true()
		var auftraege: int = 0
		for z in b.ziele:
			if String((z as Dictionary).get("kette", "")) == "auftrag":
				auftraege += 1
				assert_str(String((z as Dictionary)["id"])).starts_with("ziel_auftrag_")
		assert_int(auftraege).override_failure_message(id).is_equal(3)
		assert_float(float(b.momente.get("abstand_min", 0.0))).override_failure_message(id).is_equal(90.0)
		assert_float(float(b.momente.get("abstand_max", 0.0))).override_failure_message(id).is_equal(150.0)
		assert_float(float(b.momente.get("stapel_schub_sekunden", 0.0))).override_failure_message(id).is_equal(30.0)
		assert_bool(b.bereiche.has("bereich_6")).override_failure_message(id).is_equal(id != "webseiten")


## Die Pruefwerte der Raumluecke gibt es und sie sind die Plan-Werte (K3 Abschnitt 4).
func test_k3_pacing_grenzen_im_simulator() -> void:
	for schluessel in ["_standard", "zimmer"]:
		var z: Dictionary = AbschlussSim.ZIELE[schluessel] as Dictionary
		assert_float(float(z["raum_luecke_max"])).is_equal(900.0)
		assert_float(float(z["raum5_bis_ende_min"])).is_equal(480.0)
