## Prueft das Ende des Bogens und den Neuanfang.
##
## Ein Idle-Game ohne Neuanfang endet in einer Sackgasse: Die letzte Welt ist
## irgendwann ausgebaut, und dann passiert nichts mehr. Diese Tests halten
## fest, was beim Neuanfang bleibt und was neu beginnt -- der Unterschied ist
## die ganze Aussage.
extends GdUnitTestSuite


func _kern_in_letzter_welt() -> GameCore:
	var welten := WorldData.laden()
	var letzte: int = welten.anzahl() - 1
	return GameCore.new(BalanceData.fuer_welt(welten.id(letzte)), letzte)


func test_der_bogen_gilt_erst_als_beendet_wenn_die_letzte_welt_durch_ist() -> void:
	# Nicht "letzte Welt betreten", sondern "letzte Welt DURCH". Sonst waere
	# der Abspann der Anfang von Welt 6 statt ihres Endes.
	var kern: GameCore = _kern_in_letzter_welt()
	assert_bool(kern.bogen_beendet()).is_false()
	kern.fortschritt.setze_frei(Ids.UNLOCK_WORLD_2)
	assert_bool(kern.bogen_beendet()).is_true()


func test_in_fruehen_welten_ist_der_bogen_nie_beendet() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.fortschritt.setze_frei(Ids.UNLOCK_WORLD_2)
	assert_bool(kern.bogen_beendet()).is_false()


func test_neuanfang_setzt_zurueck_an_den_start() -> void:
	var kern: GameCore = _kern_in_letzter_welt()
	for id in Ids.CHAIN:
		var s: StationModel = kern.kette.station(id)
		if s != null:
			s.stufe = 40
	kern.kapital = 999999.0
	kern.neuanfang()

	assert_int(kern.welt_index).is_equal(0)
	assert_int(kern.durchlaeufe).is_equal(1)
	assert_float(kern.kapital).is_equal_approx(kern.balance.start_kapital, 0.001)
	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_WORLD_2)).is_false()


func test_was_bleibt_ist_der_beleg_dass_es_stattgefunden_hat() -> void:
	# gesamt_verdient und Spielzeit duerfen NIE zurueckgesetzt werden. Sie
	# sind das Einzige, was belegt, dass der erste Bogen gespielt wurde.
	var kern: GameCore = _kern_in_letzter_welt()
	kern.gesamt_verdient = 12345.0
	kern.spielzeit = 6789.0
	kern.neuanfang()
	assert_float(kern.gesamt_verdient).is_equal_approx(12345.0, 0.001)
	assert_float(kern.spielzeit).is_equal_approx(6789.0, 0.001)


func test_der_zweite_durchlauf_ist_deutlich_schneller() -> void:
	# Ohne spuerbaren Vorsprung fuehlt sich der Neuanfang wie Bestrafung an.
	var erst := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var zweit := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	zweit.durchlaeufe = 1
	for id in Ids.CHAIN:
		for k in [erst, zweit]:
			var s: StationModel = k.kette.station(id)
			if s != null:
				s.stufe = 5
	assert_float(zweit.einkommen_pro_sekunde()).is_greater(erst.einkommen_pro_sekunde() * 3.0)


func test_durchlaeufe_ueberleben_speichern_und_laden() -> void:
	var kern: GameCore = _kern_in_letzter_welt()
	kern.neuanfang()
	kern.neuanfang()

	var neu := GameCore.new()
	neu.from_save(kern.to_save())
	assert_int(neu.durchlaeufe).is_equal(2)
	assert_int(neu.welt_index).is_equal(0)


func test_jede_welt_hat_einen_abspann_hinweis() -> void:
	# Der Pflichthinweis muss in JEDEM Thema stehen, auch im Platzhalter --
	# Welt 6 handelt von Kapital, und kein Satz des Spiels darf als
	# Anlageberatung lesbar sein. Ein fehlender Hinweis waere kein
	# Schoenheitsfehler, sondern ein Store-Problem.
	var welten := WorldData.laden()
	for i in range(welten.anzahl()):
		var thema: ThemeData = ThemeData.laden(welten.id(i))
		assert_object(thema).is_not_null()
		var hinweis: String = String(thema.abschnitt("abspann").get("hinweis", ""))
		assert_str(hinweis) \
			.override_failure_message("Abspann-Hinweis fehlt in Welt '%s'" % welten.id(i)) \
			.is_not_empty()
		assert_bool(hinweis.contains("[Text fehlt]")) \
			.override_failure_message("Welt '%s' hat nur einen Platzhalter als Pflichthinweis" % welten.id(i)) \
			.is_false()
