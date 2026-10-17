## Prueft das zentrale Designprinzip: Der Engpass bestimmt alles.
## Diese Tests sind wichtiger als sie aussehen -- wenn die Engpassrechnung
## falsch ist, zeigt das Spiel dem Spieler den falschen Handlungsbedarf an,
## und das gesamte Steuerungskonzept aus GAME_DESIGN.md 2 bricht zusammen.
extends GdUnitTestSuite


func _kette(intake: int, buffer: int, processing: int) -> ProductionChain:
	var params := {"basis_durchsatz": 1.0}
	var a := StationModel.new(Ids.STATION_INTAKE, params)
	var b := StationModel.new(Ids.STATION_BUFFER, params)
	var c := StationModel.new(Ids.STATION_PROCESSING, params)
	a.stufe = intake
	b.stufe = buffer
	c.stufe = processing
	return ProductionChain.new([a, b, c])


func test_durchsatz_ist_das_minimum() -> void:
	# 5 / 3 / 9 -> das Minimum ist 3
	var kette := _kette(5, 3, 9)
	assert_float(kette.effektiver_durchsatz()).is_equal_approx(3.0, 0.001)


func test_engpass_wird_korrekt_benannt() -> void:
	assert_str(String(_kette(5, 3, 9).bottleneck())).is_equal(String(Ids.STATION_BUFFER))
	assert_str(String(_kette(2, 8, 9).bottleneck())).is_equal(String(Ids.STATION_INTAKE))
	assert_str(String(_kette(7, 8, 1).bottleneck())).is_equal(String(Ids.STATION_PROCESSING))


func test_bei_gleichstand_gewinnt_die_fruehere_station() -> void:
	# Alle gleich -> der Spieler soll am Anfang der Kette ansetzen
	assert_str(String(_kette(4, 4, 4).bottleneck())).is_equal(String(Ids.STATION_INTAKE))


func test_ausbau_des_engpasses_erhoeht_den_durchsatz() -> void:
	var kette := _kette(5, 3, 9)
	var vorher: float = kette.effektiver_durchsatz()
	kette.station(Ids.STATION_BUFFER).stufe = 6
	var nachher: float = kette.effektiver_durchsatz()
	assert_bool(nachher > vorher).is_true()
	# Neuer Engpass ist jetzt die Annahme mit Stufe 5
	assert_float(nachher).is_equal_approx(5.0, 0.001)
	assert_str(String(kette.bottleneck())).is_equal(String(Ids.STATION_INTAKE))


func test_ausbau_neben_dem_engpass_bringt_nichts() -> void:
	# Das ist die wichtigste Aussage des Designs: Wer an der falschen
	# Station investiert, sieht keinen Fortschritt.
	var kette := _kette(5, 3, 9)
	var vorher: float = kette.effektiver_durchsatz()
	kette.station(Ids.STATION_PROCESSING).stufe = 50
	assert_float(kette.effektiver_durchsatz()).is_equal_approx(vorher, 0.001)


func test_stufe_null_blockiert_die_gesamte_kette() -> void:
	assert_float(_kette(9, 0, 9).effektiver_durchsatz()).is_equal(0.0)


func test_transportfaktor_multipliziert() -> void:
	var kette := _kette(5, 5, 5)
	kette.transport_faktor = 2.0
	assert_float(kette.effektiver_durchsatz()).is_equal_approx(10.0, 0.001)


func test_gesperrte_station_blockiert() -> void:
	var kette := _kette(5, 5, 5)
	kette.station(Ids.STATION_BUFFER).freigeschaltet = false
	assert_float(kette.effektiver_durchsatz()).is_equal(0.0)


func test_engpasswechsel_wird_genau_einmal_gemeldet() -> void:
	var bus := EventBus.new()
	var meldungen: Array[StringName] = []
	bus.bottleneck_changed.connect(func(id: StringName) -> void: meldungen.append(id))

	var kette := _kette(5, 3, 9)
	kette.check_bottleneck_changed(bus)
	kette.check_bottleneck_changed(bus)   # unveraendert -> keine zweite Meldung
	assert_int(meldungen.size()).is_equal(1)
	assert_str(String(meldungen[0])).is_equal(String(Ids.STATION_BUFFER))

	kette.station(Ids.STATION_BUFFER).stufe = 6
	kette.check_bottleneck_changed(bus)   # jetzt wechselt er
	assert_int(meldungen.size()).is_equal(2)
	assert_str(String(meldungen[1])).is_equal(String(Ids.STATION_INTAKE))


func test_ungenutzte_kapazitaet() -> void:
	# 5 / 3 / 9 bei Engpass 3 -> brach liegen (5-3) + (3-3) + (9-3) = 8
	assert_float(_kette(5, 3, 9).ungenutzte_kapazitaet()).is_equal_approx(8.0, 0.001)
	# Perfekt ausbalanciert -> nichts liegt brach
	assert_float(_kette(4, 4, 4).ungenutzte_kapazitaet()).is_equal_approx(0.0, 0.001)


func test_upgrade_gibt_preis_zurueck_und_hebt_stufe() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE, {"basis_kosten": 25.0, "wachstum": 1.16})
	assert_float(s.naechste_kosten()).is_equal_approx(25.0, 0.01)
	var preis: float = s.upgrade()
	assert_float(preis).is_equal_approx(25.0, 0.01)
	assert_int(s.stufe).is_equal(1)
	assert_float(s.naechste_kosten()).is_equal_approx(29.0, 0.01)


func test_save_rundlauf_behaelt_stufe() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE)
	s.stufe = 7
	s.freigeschaltet = false
	var kopie := StationModel.new(Ids.STATION_INTAKE)
	kopie.apply_dict(s.to_dict())
	assert_int(kopie.stufe).is_equal(7)
	assert_bool(kopie.freigeschaltet).is_false()


func test_balance_wird_nicht_aus_dem_save_uebernommen() -> void:
	# Ein alter Spielstand darf ein neues Balancing nicht blockieren.
	var alt := StationModel.new(Ids.STATION_INTAKE, {"basis_kosten": 999.0})
	alt.stufe = 3
	var neu := StationModel.new(Ids.STATION_INTAKE, {"basis_kosten": 25.0})
	neu.apply_dict(alt.to_dict())
	assert_int(neu.stufe).is_equal(3)
	assert_float(neu.basis_kosten).is_equal(25.0)


# --- Meilenstein-Multiplikatoren --------------------------------------------
# Ohne sie stirbt die Progression: Bei Stufe 100 kostet eine weitere Stufe
# sonst sieben Tage Wartezeit. Der Balance-Simulator hat das aufgedeckt.

func test_ohne_meilenstein_kein_bonus() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE, {
		"basis_durchsatz": 1.0, "meilenstein_intervall": 12, "meilenstein_faktor": 1.7})
	s.stufe = 11
	assert_int(s.meilensteine_erreicht()).is_equal(0)
	assert_float(s.meilenstein_bonus()).is_equal_approx(1.0, 0.001)
	assert_float(s.durchsatz()).is_equal_approx(11.0, 0.001)


func test_meilenstein_verdoppelt_wie_konfiguriert() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE, {
		"basis_durchsatz": 1.0, "meilenstein_intervall": 12, "meilenstein_faktor": 1.7})
	s.stufe = 12
	assert_int(s.meilensteine_erreicht()).is_equal(1)
	assert_float(s.meilenstein_bonus()).is_equal_approx(1.7, 0.001)
	# 12 Stufen * Faktor 1.7
	assert_float(s.durchsatz()).is_equal_approx(20.4, 0.001)


func test_meilensteine_stapeln_sich() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE, {
		"basis_durchsatz": 1.0, "meilenstein_intervall": 12, "meilenstein_faktor": 1.7})
	s.stufe = 36
	assert_int(s.meilensteine_erreicht()).is_equal(3)
	assert_float(s.meilenstein_bonus()).is_equal_approx(pow(1.7, 3), 0.001)


func test_stufen_bis_meilenstein() -> void:
	var s := StationModel.new(Ids.STATION_INTAKE, {"meilenstein_intervall": 12})
	s.stufe = 0
	assert_int(s.stufen_bis_meilenstein()).is_equal(12)
	s.stufe = 11
	assert_int(s.stufen_bis_meilenstein()).is_equal(1)
	s.stufe = 12
	assert_int(s.stufen_bis_meilenstein()).is_equal(12)


func test_meilenstein_haelt_die_progression_am_leben() -> void:
	# Der eigentliche Zweck: Bei hohen Stufen darf die Kaufzeit nicht explodieren.
	var basis_kosten: float = 25.0
	var wachstum: float = 1.15
	var s := StationModel.new(Ids.STATION_INTAKE, {
		"basis_kosten": basis_kosten, "wachstum": wachstum,
		"basis_durchsatz": 1.0, "meilenstein_intervall": 12, "meilenstein_faktor": 1.7})
	s.stufe = 100

	var mit_meilenstein: float = CostCurve.wartezeit_bis_naechste_stufe(
		basis_kosten, wachstum, s.stufe, 0.0, s.durchsatz())

	var ohne := StationModel.new(Ids.STATION_INTAKE, {
		"basis_kosten": basis_kosten, "wachstum": wachstum,
		"basis_durchsatz": 1.0, "meilenstein_intervall": 0})
	ohne.stufe = 100
	var ohne_meilenstein: float = CostCurve.wartezeit_bis_naechste_stufe(
		basis_kosten, wachstum, ohne.stufe, 0.0, ohne.durchsatz())

	# Bei Stufe 100 sind 8 Meilensteine erreicht: Faktor 1.7^8 = rund 70.
	# Die Wartezeit ist damit um mehr als das Fuenfzigfache kuerzer -- das ist
	# der Unterschied zwischen einem lebendigen und einem toten Spiel.
	assert_bool(mit_meilenstein < ohne_meilenstein / 50.0).is_true()
	assert_float(ohne_meilenstein / mit_meilenstein).is_equal_approx(pow(1.7, 8), 1.0)
