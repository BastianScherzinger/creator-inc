## Die Kasse (K6 2c): Geld liegt als Stapel am Ende der Kette, ab n Sekunden
## antippbar. Der Bonus ist klein (<= 2 % des Einkommens ueber die Zeit), nie ein
## Verlust, und der Kern bucht das Einkommen weiter selbst.
extends GdUnitTestSuite


func _system() -> MomentSystem:
	return MomentSystem.new({"aktiv": true, "kasse_ab_s": 20.0, "kasse_max_s": 90.0, "kasse_anteil": 0.018})


func _kandidaten() -> Array[StringName]:
	return [Ids.STATION_INTAKE, MomentSystem.KISTE]


func test_kasse_nicht_bereit_vor_ab() -> void:
	var m := _system()
	m.tick(10.0, _kandidaten())
	assert_bool(m.kasse_bereit()).is_false()
	assert_float(m.kasse_antippen(100.0)).is_equal(0.0)
	m.tick(10.0, _kandidaten())
	assert_bool(m.kasse_bereit()).is_true()


func test_kasse_fuellt_nur_wenn_etwas_arbeitet() -> void:
	var m := _system()
	var leer: Array[StringName] = []
	m.tick(60.0, leer)
	assert_float(m.kasse_fuell).is_equal(0.0)


func test_kasse_deckel_und_leeren() -> void:
	var m := _system()
	m.tick(500.0, _kandidaten())
	assert_float(m.kasse_fuell).is_equal(90.0)
	var betrag: float = m.kasse_antippen(10.0)
	assert_float(betrag).is_equal_approx(10.0 * 90.0 * 0.018, 0.0001)
	assert_float(m.kasse_fuell).is_equal(0.0)
	assert_bool(m.kasse_bereit()).is_false()


func test_bonus_hoechstens_zwei_prozent_des_einkommens() -> void:
	# Jede Minute sofort antippen, sobald bereit: der Bonus je Minute bleibt unter 2 %.
	var einkommen: float = 50.0
	var m := _system()
	var bonus: float = 0.0
	var sekunden: float = 3600.0
	var t: float = 0.0
	while t < sekunden:
		m.tick(0.25, _kandidaten())
		t += 0.25
		if m.kasse_bereit():
			bonus += m.kasse_antippen(einkommen)
	assert_float(bonus).is_less(einkommen * sekunden * 0.02)
	assert_float(bonus).is_greater(0.0)


func test_bonus_nie_negativ() -> void:
	var m := _system()
	m.tick(50.0, _kandidaten())
	assert_float(m.kasse_betrag(-5.0)).is_equal(0.0)


func test_anteil_ist_gedeckelt() -> void:
	var m := MomentSystem.new({"aktiv": true, "kasse_anteil": 0.5})
	assert_float(m.kasse_anteil).is_less_equal(0.02)


func test_balance_hat_kasse_schluessel() -> void:
	var b: BalanceData = BalanceData.fuer_welt("zimmer")
	assert_bool(b.momente.has("kasse_ab_s")).is_true()


func test_kern_bucht_einkommen_unabhaengig_von_kasse() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	for i in range(200):
		kern.tick(0.25)
	var vorher: float = kern.kapital
	var betrag: float = kern.momente.kasse_antippen(kern.einkommen_pro_sekunde())
	assert_float(kern.kapital).is_equal(vorher)
	assert_float(betrag).is_greater_equal(0.0)
