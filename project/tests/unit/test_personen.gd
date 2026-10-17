## Prueft die Personen-Mechanik aus Welt 4.
##
## Sie ist der einzige Ort im Spiel, an dem mehr Druck WENIGER Leistung
## bedeutet -- und die einzige Stelle, an der es schadet, eine andere Station
## auszubauen. Wer Akquise und Planung hochzieht, ohne das Team mitwachsen zu
## lassen, verliert Durchsatz.
##
## Genau das muss messbar sein. Sonst ist es eine Behauptung im Text.
extends GdUnitTestSuite


func _buero(stufen: int = 10) -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt("buero"), 3)
	for id in Ids.CHAIN:
		var s: StationModel = kern.kette.station(id)
		if s != null:
			s.stufe = stufen
	return kern


func test_nur_welt_4_kennt_ueberlastung() -> void:
	assert_bool(BalanceData.fuer_welt("buero").personen_aktiv).is_true()
	for andere in ["zimmer", "auftrag", "webseiten", "produkt", "kapital"]:
		assert_bool(BalanceData.fuer_welt(andere).personen_aktiv) \
			.override_failure_message("Welt '%s' sollte keine Ueberlastung kennen" % andere).is_false()


func test_ausgeglichene_kette_hat_keine_ueberlastung() -> void:
	var kern: GameCore = _buero()
	assert_float(kern.personen_faktor()).is_equal_approx(1.0, 0.0001)
	assert_float(kern.ueberlastung()).is_equal_approx(0.0, 0.0001)


func test_zulauf_hochziehen_ohne_team_SENKT_den_durchsatz() -> void:
	# Das ist die Aussage der ganzen Mechanik. Ohne diesen Test koennte die
	# Ueberlastung irgendetwas tun und niemand wuerde es merken.
	var kern: GameCore = _buero()
	var vorher: float = kern.durchsatz()

	kern.kette.station(Ids.STATION_INTAKE).stufe = 60
	kern.kette.station(Ids.STATION_BUFFER).stufe = 60

	assert_float(kern.durchsatz()) \
		.override_failure_message("Ueberlastetes Team muss WENIGER schaffen, nicht gleich viel") \
		.is_less(vorher)


func test_dieselbe_handlung_schadet_in_welt_3_nicht() -> void:
	# Der Gegenbeweis: In jeder anderen Welt kann Ueberkapazitaet im Zulauf
	# nichts VERSCHLECHTERN. Sie bringt hoechstens nichts.
	#
	# Absichtlich "nicht kleiner" und nicht "genau gleich": Die Stationen
	# liefern bei gleicher Stufe unterschiedlich viel -- basis_durchsatz und
	# Multiplikator sind je Station andere. Wer den Zulauf anhebt, kann den
	# Engpass also auf die Verarbeitung verschieben und damit sogar ETWAS
	# gewinnen. Der erste Anlauf dieses Tests nahm gleiche Leistung an und
	# schlug bei 1000 gegen 1200 fehl -- der Fehler lag im Test, nicht im Spiel.
	var kern := GameCore.new(BalanceData.fuer_welt("webseiten"), 2)
	for id in Ids.CHAIN:
		kern.kette.station(id).stufe = 10
	var vorher: float = kern.durchsatz()
	kern.kette.station(Ids.STATION_INTAKE).stufe = 60
	kern.kette.station(Ids.STATION_BUFFER).stufe = 60
	assert_float(kern.durchsatz()) 		.override_failure_message("Ausserhalb von Welt 4 darf Zulauf nie schaden") 		.is_greater_equal(vorher)


func test_das_team_nachziehen_stellt_alles_wieder_her() -> void:
	# Die Mechanik darf keine Sackgasse sein: Wer den Fehler bemerkt, muss ihn
	# beheben koennen.
	var kern: GameCore = _buero()
	kern.kette.station(Ids.STATION_INTAKE).stufe = 60
	kern.kette.station(Ids.STATION_BUFFER).stufe = 60
	var gebremst: float = kern.durchsatz()

	kern.kette.station(Ids.STATION_PROCESSING).stufe = 60

	assert_float(kern.personen_faktor()).is_equal_approx(1.0, 0.0001)
	assert_float(kern.durchsatz()).is_greater(gebremst)


func test_ueberlastete_menschen_arbeiten_langsamer_nicht_gar_nicht() -> void:
	# Ein Rest bleibt immer. Das ist kein Balancing-Detail, sondern die
	# Aussage: Ueberlastung macht langsam, nicht handlungsunfaehig.
	var kern: GameCore = _buero()
	kern.kette.station(Ids.STATION_INTAKE).stufe = 400
	kern.kette.station(Ids.STATION_BUFFER).stufe = 400
	assert_float(kern.personen_faktor()).is_greater_equal(kern.balance.personen_minimum - 0.0001)
	assert_float(kern.durchsatz()).is_greater(0.0)


func test_leichte_ueberlastung_wird_noch_verziehen() -> void:
	# Unterhalb der Schwelle passiert nichts. Eine Mechanik, die bei jedem
	# Ungleichgewicht sofort zuschlaegt, waere nur nervig.
	var kern: GameCore = _buero()
	kern.kette.station(Ids.STATION_INTAKE).stufe = 11
	kern.kette.station(Ids.STATION_BUFFER).stufe = 11
	assert_float(kern.personen_faktor()).is_equal_approx(1.0, 0.0001)
