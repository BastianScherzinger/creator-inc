## Prueft den Kern im Zusammenspiel: Wirtschaft, Kette, Takt, Fortschritt.
extends GdUnitTestSuite


func _kern() -> GameCore:
	return GameCore.new(BalanceData.laden())


func test_start_ist_spielbar() -> void:
	var kern := _kern()
	# Die drei Startstationen laufen, es flieszt sofort Einkommen --
	# der Spieler soll in Minute 1 belohnt werden, nicht warten.
	assert_bool(kern.einkommen_pro_sekunde() > 0.0).is_true()
	assert_int(kern.stufen_gesamt()).is_equal(3)


func test_kapital_waechst_ueber_zeit() -> void:
	var kern := _kern()
	var vorher: float = kern.kapital
	for i in range(40):     # 10 Sekunden in 0,25er Schritten
		kern.tick(0.25)
	assert_bool(kern.kapital > vorher).is_true()
	assert_float(kern.spielzeit).is_equal_approx(10.0, 0.01)


func test_upgrade_ohne_geld_scheitert() -> void:
	var kern := _kern()
	kern.kapital = 0.0
	assert_bool(kern.upgrade_station(Ids.STATION_INTAKE)).is_false()


func test_upgrade_zieht_geld_ab_und_hebt_stufe() -> void:
	var kern := _kern()
	kern.kapital = 10000.0
	var stufe_vorher: int = kern.kette.station(Ids.STATION_INTAKE).stufe
	var preis: float = kern.kette.station(Ids.STATION_INTAKE).naechste_kosten()

	assert_bool(kern.upgrade_station(Ids.STATION_INTAKE)).is_true()
	assert_int(kern.kette.station(Ids.STATION_INTAKE).stufe).is_equal(stufe_vorher + 1)
	assert_float(kern.kapital).is_equal_approx(10000.0 - preis, 0.01)


func test_gesperrte_station_laesst_sich_nicht_ausbauen() -> void:
	var kern := _kern()
	kern.kapital = 1000000.0
	assert_bool(kern.upgrade_station(Ids.STATION_TRANSPORT)).is_false()


func test_upgrade_meldet_ereignisse() -> void:
	var kern := _kern()
	kern.kapital = 10000.0
	var upgrades: Array = []
	kern.bus.station_upgraded.connect(
		func(id: StringName, stufe: int) -> void: upgrades.append([id, stufe]))

	kern.upgrade_station(Ids.STATION_INTAKE)
	assert_int(upgrades.size()).is_equal(1)
	assert_str(String(upgrades[0][0])).is_equal(String(Ids.STATION_INTAKE))


func test_offline_ertrag_wird_gutgeschrieben() -> void:
	var kern := _kern()
	var vorher: float = kern.kapital
	var erloes: float = kern.wende_offline_an(3600.0)
	assert_bool(erloes > 0.0).is_true()
	assert_float(kern.kapital).is_equal_approx(vorher + erloes, 0.01)


func test_offline_wird_bei_der_obergrenze_gekappt() -> void:
	var a := _kern()
	var b := _kern()
	# 24 Stunden bringen nicht mehr als die Obergrenze von 4 Stunden
	assert_float(a.wende_offline_an(24.0 * 3600.0)) \
		.is_equal_approx(b.wende_offline_an(4.0 * 3600.0), 0.01)


## Kapitalschwellen gibt es seit ADR-021 nur noch in den Welten ohne Raeume --
## Welt 1 schaltet ueber gekaufte Raeume frei (test_welt_tiefe.gd). Geprueft
## wird deshalb an Welt 2, damit der alte Weg nicht unbemerkt verschwindet.
## Seit alle Welten in Tiefe sind (N02), schaltet keine ausgelieferte Welt mehr
## ueber Kapitalschwellen frei -- die Mechanik selbst gibt es weiter. Die Suite
## baut sich deshalb eine Balance mit Schwellen.
func _kern_mit_schwellen() -> GameCore:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/auftrag.json")) as Dictionary
	roh["unlocks"] = {
		"unlock_transport": {"typ": "kapital", "schwelle": 30000.0},
		"unlock_special": {"typ": "kapital", "schwelle": 150000.0},
	}
	return GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 1)


func test_freischaltung_bei_kapitalschwelle() -> void:
	var kern := _kern_mit_schwellen()
	var meldungen: Array[StringName] = []
	kern.bus.unlocked.connect(func(id: StringName) -> void: meldungen.append(id))

	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_TRANSPORT)).is_false()
	kern.kapital = 50000.0          # Schwelle laut Balance: 30000
	kern.tick(0.25)
	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_TRANSPORT)).is_true()
	assert_bool(meldungen.has(Ids.UNLOCK_TRANSPORT)).is_true()
	# Die Station laeuft jetzt auch im KERN -- nicht erst, wenn die
	# Darstellung sie freischaltet.
	assert_bool(kern.kette.station(Ids.STATION_TRANSPORT).freigeschaltet).is_true()


func test_freischaltung_feuert_nur_einmal() -> void:
	var kern := _kern_mit_schwellen()
	# ACHTUNG GDScript: Lambdas erfassen Werte, keine Referenzen. Ein
	# "var anzahl: int" wuerde in der Lambda kopiert, die Erhoehung waere
	# ausserhalb unsichtbar. Deshalb ein Dictionary als Zaehler -- das ist
	# ein Referenztyp.
	var zaehler := {"n": 0}
	kern.bus.unlocked.connect(func(_id: StringName) -> void: zaehler["n"] += 1)
	kern.kapital = 50000.0
	for i in range(20):
		kern.tick(0.25)
	# Trotz 20 Ticks ueber der Schwelle nur eine Meldung pro Freischaltung
	assert_int(int(zaehler["n"])).is_equal(kern.fortschritt.to_array().size())
	assert_bool(int(zaehler["n"]) > 0).is_true()


func test_spielstand_rundlauf_ueber_den_kern() -> void:
	var kern := _kern()
	kern.kapital = 4242.0
	kern.upgrade_station(Ids.STATION_INTAKE)
	kern.upgrade_station(Ids.STATION_BUFFER)
	var stufen_vorher: int = kern.stufen_gesamt()
	var kapital_vorher: float = kern.kapital

	var stand: SaveData = kern.to_save()
	var neuer_kern := _kern()
	neuer_kern.from_save(stand)

	assert_float(neuer_kern.kapital).is_equal_approx(kapital_vorher, 0.01)
	assert_int(neuer_kern.stufen_gesamt()).is_equal(stufen_vorher)


func test_engpass_wandert_beim_ausbauen() -> void:
	# Das Kernversprechen des Designs im Zusammenspiel:
	# Wer den Engpass behebt, bekommt einen neuen -- und immer mehr Durchsatz.
	var kern := _kern()
	kern.kapital = 1000000.0
	var gesehen := {}
	kern.bus.bottleneck_changed.connect(
		func(id: StringName) -> void: gesehen[String(id)] = true)

	var durchsatz_start: float = kern.einkommen_pro_sekunde()
	for i in range(15):
		kern.upgrade_station(kern.kette.bottleneck())

	assert_bool(kern.einkommen_pro_sekunde() > durchsatz_start).is_true()
	# Alle drei Kettenglieder waren im Laufe des Ausbaus einmal der Engpass
	assert_int(gesehen.size()).is_greater_equal(2)
