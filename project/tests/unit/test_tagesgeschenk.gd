## Tagesgeschenk, Fortschrittsmarken und die Migration v3 -> v4.
extends GdUnitTestSuite

const TAG: int = 20000


func _kern() -> GameCore:
	return GameCore.new(BalanceData.fuer_welt("zimmer"), 0)


func test_erstes_geschenk_ist_sofort_da_und_zaehlt_tag_1() -> void:
	var kern := _kern()
	assert_bool(kern.geschenk_verfuegbar(TAG)).is_true()
	assert_int(kern.geschenk_serientag(TAG)).is_equal(1)
	var vorher: float = kern.kapital
	var betrag: float = kern.loese_geschenk_ein(TAG)
	assert_float(betrag).is_greater(0.0)
	assert_float(kern.kapital).is_equal_approx(vorher + betrag, 0.001)


func test_am_selben_tag_nur_einmal() -> void:
	var kern := _kern()
	kern.loese_geschenk_ein(TAG)
	assert_bool(kern.geschenk_verfuegbar(TAG)).is_false()
	assert_float(kern.loese_geschenk_ein(TAG)).is_equal(0.0)


func test_serie_waechst_an_aufeinanderfolgenden_tagen() -> void:
	var kern := _kern()
	var betraege: Array[float] = []
	for i in range(kern.geschenk_serientage()):
		assert_int(kern.geschenk_serientag(TAG + i)).is_equal(i + 1)
		betraege.append(kern.loese_geschenk_ein(TAG + i))
	for i in range(1, betraege.size()):
		assert_float(betraege[i]).is_greater(betraege[i - 1])
	# Nach dem letzten Serientag beginnt die Serie von vorn.
	assert_int(kern.geschenk_serientag(TAG + kern.geschenk_serientage())).is_equal(1)


func test_ausgelassener_tag_setzt_nur_zurueck() -> void:
	var kern := _kern()
	kern.loese_geschenk_ein(TAG)
	kern.loese_geschenk_ein(TAG + 1)
	assert_int(kern.geschenk_serientag(TAG + 3)).is_equal(1)
	assert_float(kern.loese_geschenk_ein(TAG + 3)).is_greater(0.0)


func test_zurueckgedrehte_uhr_gibt_nichts() -> void:
	var kern := _kern()
	kern.loese_geschenk_ein(TAG + 5)
	assert_bool(kern.geschenk_verfuegbar(TAG + 2)).is_false()


func test_geschenk_ueberlebt_speichern_und_weltwechsel() -> void:
	var kern := _kern()
	kern.loese_geschenk_ein(TAG)
	var text: String = JSON.stringify(kern.to_save().to_dict())
	var zurueck := _kern()
	zurueck.from_save(SaveData.from_dict(JSON.parse_string(text) as Dictionary))
	assert_bool(zurueck.geschenk_verfuegbar(TAG)).is_false()
	assert_int(zurueck.geschenk_serientag(TAG + 1)).is_equal(2)
	zurueck.wechsle_welt()
	assert_bool(zurueck.geschenk_verfuegbar(TAG)).is_false()


func test_v3_stand_laedt_mit_geschenk_und_marken() -> void:
	var v3: Dictionary = {
		"schema_version": 3, "kapital": 500.0, "welt_index": 0,
		"stationen": {}, "unlocks": [], "bereiche": [], "ziele": [],
		"nachrichten": {"empfangen": ["nachricht_01"], "gelesen": 1},
		"momente": {"angetippt": 2},
	}
	var migriert: Dictionary = SaveData.migrieren(v3)
	assert_int(int(migriert["schema_version"])).is_equal(SaveData.SCHEMA_VERSION)
	var stand: SaveData = SaveData.from_dict(migriert)
	assert_int(stand.tagesgeschenk["letzter_tag"]).is_equal(0)
	assert_array(stand.marken).is_empty()
	var kern := _kern()
	kern.from_save(stand)
	assert_float(kern.kapital).is_equal_approx(500.0, 0.001)
	assert_bool(kern.geschenk_verfuegbar(TAG)).is_true()


func test_marken_werden_bei_25_50_75_bereit_und_zahlen_einmal() -> void:
	var kern := _kern()
	assert_int(kern.marken_liste().size()).is_equal(3)
	assert_bool(kern.marken_liste()[0]["bereit"]).is_false()
	assert_float(kern.loese_marke_ein(&"fortschritt_25")).is_equal(0.0)
	var bereit: Array = []
	kern.bus.progress_mark_ready.connect(func(id: StringName) -> void: bereit.append(String(id)))
	kern.kapital = 1.0e15
	for i in range(60):
		kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 50)
		kern.upgrade_station_mehrfach(Ids.STATION_PROCESSING, 50)
	kern.tick(0.25)
	assert_float(kern.weltwechsel_fortschritt()).is_greater(0.0)
	var vorher: float = kern.kapital
	for m in kern.marken_liste():
		if bool(m["bereit"]):
			assert_float(kern.loese_marke_ein(StringName(String(m["id"])))).is_greater(0.0)
			assert_float(kern.loese_marke_ein(StringName(String(m["id"])))).is_equal(0.0)
	assert_float(kern.kapital).is_greater_equal(vorher)
