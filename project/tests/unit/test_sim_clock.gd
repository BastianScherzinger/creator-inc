## Prueft den festen Takt und die Offline-Rechnung.
##
## Der wichtigste Test hier ist test_takt_ist_unabhaengig_von_der_bildrate:
## Wenn er faellt, haengt der Verdienst des Spielers davon ab, wie schnell
## sein Handy ist. Das waere ein stiller, schwer auffindbarer Fehler.
extends GdUnitTestSuite


func test_ein_tick_nach_einer_viertelsekunde() -> void:
	var uhr := SimClock.new()
	assert_int(uhr.advance(0.25)).is_equal(1)


func test_kein_tick_bei_zu_wenig_zeit() -> void:
	var uhr := SimClock.new()
	assert_int(uhr.advance(0.1)).is_equal(0)
	# Der Rest bleibt erhalten und wird beim naechsten Mal mitgezaehlt
	assert_int(uhr.advance(0.2)).is_equal(1)


func test_takt_ist_unabhaengig_von_der_bildrate() -> void:
	# 4 Sekunden in 30-fps-Schritten
	var langsam := SimClock.new()
	var ticks_langsam: int = 0
	for i in range(120):
		ticks_langsam += langsam.advance(1.0 / 30.0)

	# Dieselben 4 Sekunden in 120-fps-Schritten
	var schnell := SimClock.new()
	var ticks_schnell: int = 0
	for i in range(480):
		ticks_schnell += schnell.advance(1.0 / 120.0)

	assert_int(ticks_langsam).is_equal(ticks_schnell)
	assert_int(ticks_langsam).is_equal(16)   # 4s / 0,25s


func test_grosser_sprung_wird_gekappt() -> void:
	# Ein Sprung von einer Stunde darf nicht 14400 Ticks am Stueck ausloesen --
	# dafuer gibt es die Offline-Rechnung.
	var uhr := SimClock.new()
	assert_int(uhr.advance(3600.0)).is_equal(16)


func test_negative_zeit_erzeugt_nichts() -> void:
	var uhr := SimClock.new()
	assert_int(uhr.advance(-5.0)).is_equal(0)
	assert_int(uhr.advance(0.0)).is_equal(0)


func test_offline_unter_der_obergrenze() -> void:
	var uhr := SimClock.new()
	# 1 Stunde, Durchsatz 2/s, Rate 0,5 -> 3600 * 2 * 0,5 = 3600
	assert_float(uhr.offline_ertrag(2.0, 3600.0)).is_equal_approx(3600.0, 0.01)


func test_offline_wird_bei_vier_stunden_gekappt() -> void:
	var uhr := SimClock.new()
	# 8 Stunden Abwesenheit liefern exakt den Ertrag von 4 Stunden
	var acht_stunden: float = uhr.offline_ertrag(1.0, 8.0 * 3600.0)
	var vier_stunden: float = uhr.offline_ertrag(1.0, 4.0 * 3600.0)
	assert_float(acht_stunden).is_equal_approx(vier_stunden, 0.01)
	# Und das sind 4h * 3600s * 1,0 * 0,5
	assert_float(acht_stunden).is_equal_approx(7200.0, 0.01)


func test_offline_ohne_durchsatz_ist_null() -> void:
	var uhr := SimClock.new()
	assert_float(uhr.offline_ertrag(0.0, 3600.0)).is_equal(0.0)


func test_erweiterte_obergrenze_wirkt() -> void:
	var uhr := SimClock.new()
	uhr.offline_obergrenze_sekunden = 12.0 * 3600.0
	# Mit 12h-Obergrenze bringen 8h auch 8h Anrechnung
	assert_float(uhr.anrechenbare_offline_sekunden(8.0 * 3600.0)).is_equal_approx(8.0 * 3600.0, 0.1)


func test_abwesenheit_aus_zeitstempeln() -> void:
	assert_float(SimClock.abwesenheit(1000, 4600)).is_equal_approx(3600.0, 0.01)


func test_zurueckgestellte_uhr_erzeugt_keinen_negativen_ertrag() -> void:
	# Systemzeit zurueckgedreht -> 0, nicht negativ
	assert_float(SimClock.abwesenheit(5000, 1000)).is_equal(0.0)


func test_erster_start_ohne_zeitstempel() -> void:
	assert_float(SimClock.abwesenheit(0, 999999)).is_equal(0.0)
