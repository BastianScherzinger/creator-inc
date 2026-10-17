## Der Spielstand muss in JEDER Welt vollstaendig zurueckkommen.
##
## Jede Welt bringt eigenen Zustand mit: Welt 2 den Umbau, Welt 5 den
## Abonnentenbestand, Welt 6 die Schwankung, alle den Schub. Ein Feld, das
## beim Speichern vergessen wird, faellt im Spiel erst auf, wenn jemand die
## App schliesst und zurueckkommt -- also genau dann, wenn es am meisten weh
## tut und am schlechtesten zu reproduzieren ist.
##
## Diese Suite spielt jede Welt kurz an, speichert, laedt und vergleicht.
extends GdUnitTestSuite

const TAKT: float = SimClock.TICK_DAUER


func _welten() -> WorldData:
	return WorldData.laden()


## Spielt eine Welt so weit an, dass ueberall etwas drinsteht.
func _angespielt(index: int) -> GameCore:
	var welten := _welten()
	var kern := GameCore.new(BalanceData.fuer_welt(welten.id(index)), index)
	for id in Ids.CHAIN:
		var s: StationModel = kern.kette.station(id)
		if s != null:
			s.stufe = 7 + index
	kern.starte_schub()
	for i in range(80):
		kern.tick(TAKT)
	return kern


func test_jede_welt_ueberlebt_speichern_und_laden() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		var welt_id: String = welten.id(i)
		var kern: GameCore = _angespielt(i)
		var stand: SaveData = kern.to_save()

		var neu := GameCore.new(BalanceData.fuer_welt(welt_id), i)
		neu.from_save(stand)

		assert_int(neu.welt_index) \
			.override_failure_message("Welt '%s': Weltindex verloren" % welt_id).is_equal(i)
		assert_float(neu.kapital) \
			.override_failure_message("Welt '%s': Kapital verloren" % welt_id) \
			.is_equal_approx(kern.kapital, maxf(kern.kapital * 0.0001, 0.01))
		assert_float(neu.gesamt_verdient) \
			.override_failure_message("Welt '%s': Gesamtverdienst verloren" % welt_id) \
			.is_equal_approx(kern.gesamt_verdient, maxf(kern.gesamt_verdient * 0.0001, 0.01))
		assert_int(neu.stufen_gesamt()) \
			.override_failure_message("Welt '%s': Ausbaustufen verloren" % welt_id) \
			.is_equal(kern.stufen_gesamt())
		assert_float(neu.schub_rest) \
			.override_failure_message("Welt '%s': Schub verloren" % welt_id) \
			.is_equal_approx(kern.schub_rest, 0.01)
		assert_float(neu.bestand) \
			.override_failure_message("Welt '%s': Bestand verloren" % welt_id) \
			.is_equal_approx(kern.bestand, maxf(kern.bestand * 0.0001, 0.01))


func test_das_einkommen_ist_nach_dem_laden_dasselbe() -> void:
	# Der eigentliche Beweis: Nicht die Felder zaehlen, sondern was das Spiel
	# daraus macht. Ein vergessenes Feld faellt hier auf, auch wenn niemand
	# daran gedacht hat, es einzeln zu pruefen.
	var welten := _welten()
	for i in range(welten.anzahl()):
		var welt_id: String = welten.id(i)
		var kern: GameCore = _angespielt(i)
		var neu := GameCore.new(BalanceData.fuer_welt(welt_id), i)
		neu.from_save(kern.to_save())
		assert_float(neu.einkommen_pro_sekunde()) \
			.override_failure_message("Welt '%s': Einkommen nach dem Laden anders" % welt_id) \
			.is_equal_approx(kern.einkommen_pro_sekunde(),
				maxf(kern.einkommen_pro_sekunde() * 0.001, 0.01))


func test_der_umbau_aus_welt_2_geht_nicht_verloren() -> void:
	# Der teuerste Einzelzustand des Spiels: Wer ihn bezahlt hat und nach dem
	# Neustart wieder vor der Wand steht, hoert auf zu spielen.
	var kern := GameCore.new(BalanceData.fuer_welt("auftrag"), 1)
	kern.kapital = kern.umbau_kosten()
	assert_bool(kern.kaufe_umbau()).is_true()

	var neu := GameCore.new(BalanceData.fuer_welt("auftrag"), 1)
	neu.from_save(kern.to_save())
	assert_bool(neu.limit_gilt()).is_false()


func test_ein_leerer_spielstand_startet_die_erste_welt() -> void:
	# Der haeufigste Fall ueberhaupt: der allererste Start.
	var kern := GameCore.new()
	kern.from_save(SaveData.new())
	assert_int(kern.welt_index).is_equal(0)
	assert_int(kern.durchlaeufe).is_equal(0)
	assert_bool(kern.bogen_beendet()).is_false()
