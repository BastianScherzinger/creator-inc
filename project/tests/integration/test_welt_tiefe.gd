## Prueft Welt 1 in Idle-Tycoon-Tiefe (ADR-021, docs/WELT1_TIEFE.md).
##
## Obergrenze, Ausstattung, Raeume, Abschluss, Ziele, Tipp-Momente, Nachrichten
## und der Spielstand dazu. Alles headless -- wie der Rest des Kerns.
extends GdUnitTestSuite

const FIXTURE_V2: String = "res://tests/fixtures/saves/save_v2.json"


func _kern() -> GameCore:
	return GameCore.new(BalanceData.fuer_welt("zimmer"), 0)


func _reich(kern: GameCore) -> GameCore:
	kern.kapital = 1.0e15
	return kern


func _alles_kaufen(kern: GameCore) -> void:
	_reich(kern)
	for bereich_id in kern.bereiche.ids():
		kern.kaufe_bereich(bereich_id)
	for id in Ids.ALL_STATIONS:
		kern.upgrade_station_mehrfach(id, -1)
		var station: StationModel = kern.kette.station(id)
		for p in station.ausstattung:
			while kern.kaufe_ausstattung(id, p.id):
				pass


# --- Daten ---------------------------------------------------------------------

func test_balance_von_welt_1_ist_gueltig() -> void:
	var balance := BalanceData.fuer_welt("zimmer")
	assert_bool(balance.validieren()) \
		.override_failure_message("\n".join(balance.fehler)).is_true()
	assert_str(String(balance.abschluss)).is_equal("alles")


func test_abschluss_alles_ohne_obergrenze_wird_abgelehnt() -> void:
	# Eine Welt, die bei "alles" endet, braucht fuer alles ein Ende -- sonst
	# ist sie eine Sackgasse, die niemand bemerkt, bis er drinsteckt.
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	(roh["stationen"]["station_buffer"] as Dictionary).erase("max_stufe")
	var balance := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(balance.validieren()).is_false()


func test_unbekannter_bedingungstyp_faellt_auf() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	(roh["ziele"] as Array)[0]["typ"] = "stationstufe"
	var balance := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(balance.validieren()).is_false()


func test_auch_die_anderen_welten_enden_bei_100_prozent() -> void:
	# Seit N02 sind alle Welten in Tiefe (vorher liefen 2-6 ueber die Schwelle).
	var kern := GameCore.new(BalanceData.fuer_welt("webseiten"), 2)
	assert_bool(kern.welt_hat_abschluss()).is_true()
	assert_bool(kern.bereiche.hat_bereiche()).is_true()


func test_eine_welt_ohne_tiefe_endet_weiter_an_der_schwelle() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/webseiten.json")) as Dictionary
	roh.erase("abschluss")
	roh.erase("bereiche")
	var kern := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 2)
	assert_bool(kern.welt_hat_abschluss()).is_false()
	assert_bool(kern.bereiche.hat_bereiche()).is_false()


# --- Obergrenze und Mehrfachkauf -----------------------------------------------

func test_station_endet_an_ihrer_obergrenze() -> void:
	var kern := _reich(_kern())
	var gekauft: int = kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, -1)
	var station: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	assert_int(station.stufe).is_equal(station.max_stufe)
	assert_int(gekauft).is_equal(station.max_stufe - 1)
	assert_bool(kern.upgrade_station(Ids.STATION_INTAKE)).is_false()


func test_mehrfachkauf_kauft_nur_was_das_geld_hergibt() -> void:
	var kern := _kern()
	var vorschau: Array = kern.vorschau_mehrfach(Ids.STATION_INTAKE, 10)
	kern.kapital = float(vorschau[1]) - 1.0
	var gekauft: int = kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 10)
	assert_int(gekauft).is_equal(9)


func test_mehrfachkauf_meldet_einmal() -> void:
	var kern := _reich(_kern())
	var zaehler := {"n": 0}
	kern.bus.station_upgraded.connect(func(_id: StringName, _s: int) -> void: zaehler["n"] += 1)
	kern.upgrade_station_mehrfach(Ids.STATION_BUFFER, 10)
	assert_int(int(zaehler["n"])).is_equal(1)


func test_vorschau_ohne_geld_zeigt_den_naechsten_preis() -> void:
	var kern := _kern()
	kern.kapital = 0.0
	var vorschau: Array = kern.vorschau_mehrfach(Ids.STATION_INTAKE, -1)
	assert_int(int(vorschau[0])).is_equal(0)
	assert_float(float(vorschau[1])).is_greater(0.0)


# --- Ausstattung ---------------------------------------------------------------

func test_ausstattung_ist_unter_ihrer_stufe_gesperrt() -> void:
	var kern := _reich(_kern())
	# ausstattung_3 der Idee gibt es erst ab Stationsstufe 25
	assert_bool(kern.kaufe_ausstattung(Ids.STATION_INTAKE, &"ausstattung_3")).is_false()
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 24)
	assert_bool(kern.kaufe_ausstattung(Ids.STATION_INTAKE, &"ausstattung_3")).is_true()


func test_ausstattung_macht_die_station_schneller() -> void:
	var kern := _reich(_kern())
	var station: StationModel = kern.kette.station(Ids.STATION_PROCESSING)
	var vorher: float = station.durchsatz()
	assert_bool(kern.kaufe_ausstattung(Ids.STATION_PROCESSING, &"ausstattung_2")).is_true()
	assert_float(station.durchsatz()).is_greater(vorher)


func test_ausstattung_endet_bei_ihrer_hoechststufe() -> void:
	var kern := _reich(_kern())
	var p: EquipmentSlot = kern.kette.station(Ids.STATION_PROCESSING).platz(&"ausstattung_2")
	for i in range(20):
		kern.kaufe_ausstattung(Ids.STATION_PROCESSING, &"ausstattung_2")
	assert_int(p.stufe).is_equal(p.max_stufe)


func test_modellstufe_folgt_den_schwellen() -> void:
	var p := EquipmentSlot.new(&"ausstattung_1", {})
	var erwartet: Array[int] = [0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3]
	for stufe in range(11):
		p.stufe = stufe
		assert_int(p.modellstufe()).is_equal(erwartet[stufe])


func test_gesperrte_station_hat_keine_kaufbare_ausstattung() -> void:
	var kern := _reich(_kern())
	assert_bool(kern.kaufe_ausstattung(Ids.STATION_TRANSPORT, &"ausstattung_1")).is_false()


# --- Raeume --------------------------------------------------------------------

func test_raum_schaltet_seine_station_im_kern_frei() -> void:
	var kern := _reich(_kern())
	assert_bool(kern.kette.station(Ids.STATION_TRANSPORT).freigeschaltet).is_false()
	assert_bool(kern.kaufe_bereich(&"bereich_1")).is_true()
	var upload: StationModel = kern.kette.station(Ids.STATION_TRANSPORT)
	assert_bool(upload.freigeschaltet).is_true()
	assert_int(upload.stufe).is_greater_equal(1)
	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_TRANSPORT)).is_true()


func test_raum_laesst_sich_nur_einmal_kaufen() -> void:
	var kern := _reich(_kern())
	assert_bool(kern.kaufe_bereich(&"bereich_2")).is_true()
	var kapital: float = kern.kapital
	assert_bool(kern.kaufe_bereich(&"bereich_2")).is_false()
	assert_float(kern.kapital).is_equal(kapital)


func test_raum_mit_bonus_hebt_das_einkommen() -> void:
	var kern := _reich(_kern())
	var vorher: float = kern.einkommen_pro_sekunde()
	var erfolge_vorher: float = kern.erfolge_faktor()
	kern.kaufe_bereich(&"bereich_2")        # alle x1,25
	# Der erste Raum ist selbst ein Erfolg (Weltfaktor) -- der gehoert nicht zum Raumbonus.
	var bereinigt: float = kern.einkommen_pro_sekunde() * erfolge_vorher / kern.erfolge_faktor()
	assert_float(bereinigt).is_equal_approx(vorher * 1.25, vorher * 0.001)


func test_raum_mit_voraussetzung_wartet() -> void:
	var kern := _reich(_kern())
	assert_bool(kern.kaufe_bereich(&"bereich_5")).is_false()
	# Raum 3b (bereich_6) liegt in Welt 1 zwischen Raum 3 und 4 (K3 B1): erst der Reihe nach.
	assert_bool(kern.kaufe_bereich(&"bereich_4")).is_false()
	kern.kaufe_bereich(&"bereich_3")
	kern.kaufe_bereich(&"bereich_6")
	kern.kaufe_bereich(&"bereich_4")
	assert_bool(kern.kaufe_bereich(&"bereich_5")).is_true()


func test_ohne_geld_kein_raum() -> void:
	var kern := _kern()
	kern.kapital = 10.0
	assert_bool(kern.kaufe_bereich(&"bereich_1")).is_false()
	assert_bool(kern.bereiche.ist_gekauft(&"bereich_1")).is_false()


# --- Abschluss -----------------------------------------------------------------

func test_welt_ist_am_anfang_nicht_fertig() -> void:
	var kern := _kern()
	assert_bool(kern.welt_abgeschlossen()).is_false()
	assert_float(kern.weltwechsel_fortschritt()).is_less(0.1)


func test_fast_alles_ist_nicht_alles() -> void:
	var kern := _kern()
	_alles_kaufen(kern)
	# Eine einzige Ausstattungsstufe zuruecknehmen
	var p: EquipmentSlot = kern.kette.station(Ids.STATION_SPECIAL).platz(&"ausstattung_3")
	p.stufe -= 1
	assert_bool(kern.welt_abgeschlossen()).is_false()
	assert_float(kern.weltwechsel_fortschritt()).is_less(1.0)


func test_alles_gekauft_gibt_den_weltwechsel_frei() -> void:
	var kern := _kern()
	var meldungen := {"welt": 0, "unlock": 0}
	kern.bus.world_completed.connect(func() -> void: meldungen["welt"] += 1)
	kern.bus.unlocked.connect(func(id: StringName) -> void:
		if id == Ids.UNLOCK_WORLD_2:
			meldungen["unlock"] += 1)
	_alles_kaufen(kern)
	assert_bool(kern.welt_abgeschlossen()).is_true()
	assert_float(kern.weltwechsel_fortschritt()).is_equal_approx(1.0, 0.0001)
	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_WORLD_2)).is_true()
	for i in range(10):
		kern.tick(0.25)
	# Genau EINMAL -- ein zweites Mal waere ein zweiter Weltwechsel-Bildschirm.
	assert_int(int(meldungen["welt"])).is_equal(1)
	assert_int(int(meldungen["unlock"])).is_equal(1)


func test_nach_dem_abschluss_geht_es_in_welt_2() -> void:
	var kern := _kern()
	_alles_kaufen(kern)
	assert_bool(kern.wechsle_welt()).is_true()
	assert_str(kern.welt_id()).is_equal("auftrag")
	assert_float(kern.welt_verdient).is_equal(0.0)


# --- Ziele ---------------------------------------------------------------------

func test_immer_drei_ziele_sichtbar() -> void:
	var kern := _kern()
	assert_int(kern.ziele.sichtbar().size()).is_equal(3)
	assert_str(String(kern.ziele.sichtbar()[0]["id"])).is_equal("ziel_01")


func test_unerfuelltes_ziel_zahlt_nichts() -> void:
	var kern := _kern()
	assert_float(kern.loese_ziel_ein(&"ziel_01")).is_equal(0.0)


func test_erfuelltes_ziel_zahlt_und_rueckt_nach() -> void:
	var kern := _reich(_kern())
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 7)
	kern.kapital = 0.0
	var betrag: float = kern.loese_ziel_ein(&"ziel_01")
	assert_float(betrag).is_greater_equal(40.0)
	assert_float(kern.kapital).is_equal_approx(betrag, 0.001)
	# Das naechste Ziel im Pfad rueckt nach (die Reihenfolge steht in den Daten).
	assert_str(String(kern.ziele.sichtbar()[0]["id"])).is_equal(String((kern.balance.ziele[1] as Dictionary)["id"]))
	# Kein zweites Mal
	assert_float(kern.loese_ziel_ein(&"ziel_01")).is_equal(0.0)


func test_ziel_ausserhalb_der_sichtbaren_wartet() -> void:
	# Ziel 04 (Flur) ist erfuellt, aber noch nicht an der Reihe.
	var kern := _reich(_kern())
	kern.kaufe_bereich(&"bereich_1")
	assert_float(kern.loese_ziel_ein(&"ziel_04")).is_equal(0.0)


func test_erfuelltes_ziel_wird_einmal_gemeldet() -> void:
	var kern := _reich(_kern())
	var gemeldet := {"n": 0}
	kern.bus.goal_completed.connect(func(_id: StringName) -> void: gemeldet["n"] += 1)
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 7)
	for i in range(8):
		kern.tick(0.25)
	assert_int(int(gemeldet["n"])).is_equal(1)


# --- Tipp-Momente ---------------------------------------------------------------

func test_moment_erscheint_und_zahlt_beim_antippen() -> void:
	var kern := _kern()
	var erschienen := {"station": &""}
	kern.bus.moment_appeared.connect(func(id: StringName, _d: float) -> void: erschienen["station"] = id)
	for i in range(int(155.0 / 0.25)):   # abstand_max 150 s (K3 B1)
		kern.tick(0.25)
		if kern.momente.laeuft():
			break
	assert_bool(kern.momente.laeuft()).is_true()
	assert_bool(Ids.ALL_STATIONS.has(erschienen["station"] as StringName)).is_true()
	var vorher: float = kern.kapital
	var betrag: float = kern.tippe_moment()
	assert_float(betrag).is_greater_equal(5.0)
	assert_float(kern.kapital).is_equal_approx(vorher + betrag, 0.001)
	assert_int(kern.momente.angetippt_gesamt).is_equal(1)
	assert_bool(kern.momente.laeuft()).is_false()


func test_moment_verschwindet_leise() -> void:
	var m := MomentSystem.new({"aktiv": true, "abstand_min": 1.0, "abstand_max": 1.0, "dauer": 2.0})
	var kandidaten: Array[StringName] = [Ids.STATION_INTAKE]
	m.tick(1.5, kandidaten)
	assert_bool(m.laeuft()).is_true()
	m.tick(2.5, kandidaten)
	assert_bool(m.laeuft()).is_false()
	assert_int(m.angetippt_gesamt).is_equal(0)


func test_grosser_moment_zahlt_mehr() -> void:
	var klein := MomentSystem.new({"aktiv": true, "abstand_min": 1.0, "abstand_max": 1.0,
		"belohnung_sekunden": 30.0, "gross_chance": 0.0})
	var gross := MomentSystem.new({"aktiv": true, "abstand_min": 1.0, "abstand_max": 1.0,
		"belohnung_sekunden": 30.0, "gross_chance": 1.0, "gross_sekunden": 300.0})
	var kandidaten: Array[StringName] = [Ids.STATION_INTAKE]
	klein.tick(1.5, kandidaten)
	gross.tick(1.5, kandidaten)
	assert_bool(gross.gross).is_true()
	assert_float(gross.antippen(10.0)).is_equal_approx(klein.antippen(10.0) * 10.0, 0.001)


func test_mehreinnahme_ist_null_wenn_die_station_nicht_bremst() -> void:
	# Die Aufnahme bremst am Anfang nicht -- ihre Stufe bringt kein Einkommen.
	var kern := _kern()
	var jetzt: float = kern.einkommen_pro_sekunde()
	assert_float(kern.einkommen_danach(Ids.STATION_PROCESSING)).is_equal_approx(jetzt, 0.0001)
	assert_float(kern.einkommen_danach(Ids.STATION_INTAKE)).is_greater(jetzt)
	# Und die Probe veraendert nichts
	assert_int(kern.kette.station(Ids.STATION_INTAKE).stufe).is_equal(1)


func test_ohne_kandidaten_kein_moment() -> void:
	var m := MomentSystem.new({"aktiv": true, "abstand_min": 1.0, "abstand_max": 1.0})
	var leer: Array[StringName] = []
	m.tick(5.0, leer)
	assert_bool(m.laeuft()).is_false()


func test_moment_tippen_ohne_blase_zahlt_nichts() -> void:
	var kern := _kern()
	assert_float(kern.tippe_moment()).is_equal(0.0)


# --- Nachrichten ----------------------------------------------------------------

func test_die_erste_nachricht_kommt_sofort() -> void:
	var kern := _kern()
	kern.tick(0.25)
	assert_array(kern.nachrichten.empfangen()).contains_exactly(["nachricht_01"])
	assert_int(kern.nachrichten.ungelesen()).is_equal(1)
	kern.nachrichten.markiere_gelesen()
	assert_int(kern.nachrichten.ungelesen()).is_equal(0)


func test_nachrichten_kommen_in_reihenfolge() -> void:
	var kern := _reich(_kern())
	# Die Bedingung von Nachricht 5 (Flur) ist erfuellt, 2 und 3 noch nicht.
	kern.kaufe_bereich(&"bereich_1")
	kern.tick(0.25)
	assert_bool(kern.nachrichten.empfangen().has("nachricht_05")).is_false()


# --- Spielstand -------------------------------------------------------------------

func test_rundlauf_behaelt_die_tiefe() -> void:
	var kern := _reich(_kern())
	kern.kaufe_bereich(&"bereich_1")
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 12)
	kern.kaufe_ausstattung(Ids.STATION_INTAKE, &"ausstattung_2")
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 4)
	kern.loese_ziel_ein(&"ziel_01")
	kern.tick(0.25)
	var einkommen: float = kern.einkommen_pro_sekunde()

	var text: String = JSON.stringify(kern.to_save().to_dict())
	var zurueck := _kern()
	zurueck.from_save(SaveData.from_dict(JSON.parse_string(text) as Dictionary))

	assert_bool(zurueck.bereiche.ist_gekauft(&"bereich_1")).is_true()
	assert_bool(zurueck.kette.station(Ids.STATION_TRANSPORT).freigeschaltet).is_true()
	assert_int(zurueck.kette.station(Ids.STATION_INTAKE).platz(&"ausstattung_2").stufe).is_equal(1)
	assert_bool(zurueck.ziele.ist_eingeloest("ziel_01")).is_true()
	assert_array(zurueck.nachrichten.empfangen()).contains(["nachricht_01"])
	assert_float(zurueck.einkommen_pro_sekunde()).is_equal_approx(einkommen, einkommen * 0.0001)


func test_v2_stand_passt_in_die_neue_welt() -> void:
	var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_V2)) as Dictionary
	var stand: SaveData = SaveData.from_dict(SaveData.migrieren(roh))
	assert_int(stand.schema_version).is_equal(SaveData.SCHEMA_VERSION)

	var kern := _kern()
	kern.from_save(stand)
	# Ueber der heutigen Obergrenze -> gekappt, nicht abgelehnt
	assert_int(kern.kette.station(Ids.STATION_INTAKE).stufe).is_equal(50)
	# Upload war frei -> der Flur gilt als gekauft
	assert_bool(kern.bereiche.ist_gekauft(&"bereich_1")).is_true()
	# Der alte Weltwechsel bei 90 Stufen gilt nicht mehr
	assert_bool(kern.fortschritt.ist_frei(Ids.UNLOCK_WORLD_2)).is_false()
	assert_float(kern.kapital).is_equal_approx(98765.25, 0.001)
	# Nichts Ungelesenes aus einer Geschichte, die es damals nicht gab
	assert_int(kern.nachrichten.ungelesen()).is_equal(0)
