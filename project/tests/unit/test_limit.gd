## Prueft die harte Obergrenze aus Welt 2.
##
## Sie ist der einzige Ort im Spiel, an dem Ausbauen NICHT hilft. Genau das
## muss messbar sein -- sonst waere sie nur ein Text, der etwas behauptet.
extends GdUnitTestSuite

const TAKT: float = SimClock.TICK_DAUER


func _kern_mit_limit() -> GameCore:
	var balance := BalanceData.fuer_welt("auftrag")
	var kern := GameCore.new(balance, 1)
	return kern


func _baue_aus(kern: GameCore, stufen: int) -> void:
	for id in Ids.CHAIN:
		var station: StationModel = kern.kette.station(id)
		if station != null:
			station.stufe = stufen


func test_welt_2_hat_ueberhaupt_ein_limit() -> void:
	assert_bool(_kern_mit_limit().limit_gilt()).is_true()


func test_erste_welt_hat_keins() -> void:
	# Das Limit gehoert zu Welt 2 und darf nirgends sonst auftauchen.
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	assert_bool(kern.limit_gilt()).is_false()
	assert_bool(is_inf(kern.obergrenze())).is_true()


func test_ausbauen_hilft_bis_zur_grenze() -> void:
	var kern: GameCore = _kern_mit_limit()
	_baue_aus(kern, 1)
	var klein: float = kern.durchsatz()
	_baue_aus(kern, 4)
	assert_float(kern.durchsatz()).is_greater(klein)


func test_ausbauen_hilft_JENSEITS_der_grenze_nicht_mehr() -> void:
	# Das ist die Aussage der ganzen Mechanik.
	var kern: GameCore = _kern_mit_limit()
	_baue_aus(kern, 30)
	var am_anschlag: float = kern.durchsatz()
	_baue_aus(kern, 60)
	assert_float(kern.durchsatz()).is_equal_approx(am_anschlag, am_anschlag * 0.0001)
	# Die Kette KOENNTE deutlich mehr -- das ist der Unterschied, den die
	# Oberflaeche zeigen muss.
	assert_float(kern.roher_durchsatz()).is_greater(am_anschlag * 1.5)


func test_auslastung_meldet_den_anschlag() -> void:
	var kern: GameCore = _kern_mit_limit()
	_baue_aus(kern, 1)
	assert_float(kern.limit_auslastung()).is_less(1.0)
	_baue_aus(kern, 60)
	assert_float(kern.limit_auslastung()).is_greater(1.0)


func test_umbau_hebt_die_grenze_auf() -> void:
	var kern: GameCore = _kern_mit_limit()
	_baue_aus(kern, 60)
	var gedeckelt: float = kern.durchsatz()

	kern.kapital = kern.umbau_kosten()
	assert_bool(kern.kaufe_umbau()).is_true()

	assert_bool(kern.limit_gilt()).is_false()
	assert_float(kern.durchsatz()).is_greater(gedeckelt * 1.5)
	assert_float(kern.durchsatz()).is_equal_approx(kern.roher_durchsatz(), 0.001)


func test_umbau_ohne_geld_geht_nicht() -> void:
	var kern: GameCore = _kern_mit_limit()
	kern.kapital = kern.umbau_kosten() - 0.01
	assert_bool(kern.kaufe_umbau()).is_false()
	assert_bool(kern.limit_gilt()).is_true()


func test_umbau_kostet_genau_einmal() -> void:
	var kern: GameCore = _kern_mit_limit()
	kern.kapital = kern.umbau_kosten() * 3.0
	kern.kaufe_umbau()
	var rest: float = kern.kapital
	assert_bool(kern.kaufe_umbau()).is_false()
	assert_float(kern.kapital).is_equal_approx(rest, 0.001)


func test_umbau_ueberlebt_speichern_und_laden() -> void:
	var kern: GameCore = _kern_mit_limit()
	kern.kapital = kern.umbau_kosten()
	kern.kaufe_umbau()

	var neu: GameCore = _kern_mit_limit()
	neu.from_save(kern.to_save())
	assert_bool(neu.limit_gilt()).is_false()


func test_das_limit_deckelt_auch_den_ertrag() -> void:
	# Ein Limit, das nur die Anzeige deckelt, waere eine Luege.
	var kern: GameCore = _kern_mit_limit()
	_baue_aus(kern, 60)
	var vorher: float = kern.gesamt_verdient
	for i in range(40):
		kern.tick(TAKT)
	var mit_limit: float = kern.gesamt_verdient - vorher

	var frei: GameCore = _kern_mit_limit()
	_baue_aus(frei, 60)
	frei.kapital = frei.umbau_kosten()
	frei.kaufe_umbau()
	var vorher_frei: float = frei.gesamt_verdient
	for i in range(40):
		frei.tick(TAKT)
	assert_float(frei.gesamt_verdient - vorher_frei).is_greater(mit_limit * 1.5)
