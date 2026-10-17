## K2 P2a: Firmen-Rang statt Level -- Punkte, Schwellen, Freischalt-Abfrage,
## Rang-Up-Signal und Migration alter Staende.
extends GdUnitTestSuite

const FIXTURE_V4: String = "res://tests/fixtures/saves/save_v4.json"
const TAG: int = 20500


func _kern() -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.tag_override = TAG
	return kern


## Spielt, was ohne Zeitablauf geht: ausbauen, Raeume kaufen, Ziele einloesen --
## bis nichts mehr dazukommt. Die ganze Welt schafft das nicht (Verdienst-, Moment-
## und Fortschrittsziele brauchen Zeit); fuer Punkte reicht ein Teil.
func _spiele_teil(kern: GameCore) -> void:
	kern.kapital = 1.0e18
	for runde in range(40):
		var vorher: int = kern.ziele.anzahl_eingeloest()
		for id in Ids.ALL_STATIONS:
			kern.upgrade_station_mehrfach(id, 10)
		for bereich_id in kern.bereiche.ids():
			kern.kaufe_bereich(bereich_id)
		for z in kern.ziele.sichtbar():
			kern.loese_ziel_ein(StringName(String(z["id"])))
		kern.kapital = 1.0e18
		if kern.ziele.anzahl_eingeloest() == vorher and runde > 3:
			break


## Summe der Punkte aller bisher eingeloesten Ziele, aus den Daten gerechnet.
func _erwartete_punkte(kern: GameCore) -> int:
	var summe: int = 0
	for id in kern.ziele.to_array():
		summe += kern.erfolge.ziel_punkte(kern.ziele.definition(id))
	return summe


func _welt_punkte(welt_id: String) -> int:
	var a := Achievements.new()
	var summe: int = 0
	for z in BalanceData.fuer_welt(welt_id).ziele:
		summe += a.ziel_punkte(z as Dictionary)
	return summe


# --- Punkte ----------------------------------------------------------------------

func test_punkte_gewichten_ziel_raumziel_und_mission() -> void:
	var a := Achievements.new()
	assert_int(a.ziel_punkte({"typ": "station_stufe"})).is_equal(1)
	assert_int(a.ziel_punkte({"typ": "bereich"})).is_equal(3)
	assert_int(a.ziel_punkte({"typ": "station_stufe", "kette": "welt"})).is_equal(5)
	# Mission schlaegt Raumziel.
	assert_int(a.ziel_punkte({"typ": "bereich", "kette": "welt"})).is_equal(5)
	assert_int(a.welt_fertig_punkte()).is_equal(10)


func test_eingeloeste_ziele_zaehlen_gewichtet() -> void:
	var kern := _kern()
	assert_int(kern.rang_punkte()).is_equal(0)
	_spiele_teil(kern)
	assert_int(kern.ziele.anzahl_eingeloest()).is_greater(3)
	assert_int(kern.rang_punkte()).is_equal(_erwartete_punkte(kern))
	assert_int(kern.rang_punkte()).is_greater_equal(kern.ziele.anzahl_eingeloest())


func test_welt_fertig_bringt_zehn_punkte_einmal() -> void:
	var kern := _kern()
	kern._zaehle_welt_fertig()
	assert_int(kern.rang_punkte()).is_equal(10)
	kern._zaehle_welt_fertig()
	assert_int(kern.rang_punkte()).is_equal(10)
	assert_int(int(kern.bogen["welten"])).is_equal(1)


# --- Schwellen -------------------------------------------------------------------

func test_dreissig_raenge_mit_aufsteigenden_schwellen() -> void:
	var a := Achievements.new()
	assert_int(a.level_max).is_equal(30)
	assert_int(a.schwellen.size()).is_equal(30)
	assert_int(a.schwellen[0]).is_equal(0)
	for i in range(1, a.schwellen.size()):
		assert_int(a.schwellen[i]).is_greater(a.schwellen[i - 1])


func test_rang_30_braucht_alle_punkte_des_bogens() -> void:
	var a := Achievements.new()
	var gesamt: int = 0
	var welten := WorldData.laden()
	for i in range(welten.anzahl()):
		gesamt += _welt_punkte(welten.id(i)) + a.welt_fertig_punkte()
	assert_int(a.schwelle(30)).is_equal(gesamt)
	assert_int(a.rang(gesamt)).is_equal(30)
	assert_int(a.rang(gesamt - 1)).is_equal(29)
	assert_int(a.rang(gesamt * 3)).is_equal(30)


func test_welt_eins_hat_fuenf_raenge_nach_dem_start() -> void:
	var a := Achievements.new()
	var welt_1: int = _welt_punkte("zimmer") + a.welt_fertig_punkte()
	assert_int(a.rang(0)).is_equal(1)
	assert_int(a.rang(welt_1)).is_equal(6)
	assert_int(a.rang(welt_1 - 1)).is_equal(6)
	# Der naechste Rang gehoert erst in Welt 2.
	assert_int(a.schwelle(7)).is_greater(welt_1 - a.welt_fertig_punkte() - 1)


func test_naechste_schwelle_und_ende() -> void:
	var a := Achievements.new()
	assert_int(a.naechste_schwelle(1)).is_equal(a.schwelle(2))
	assert_int(a.naechste_schwelle(30)).is_equal(-1)


# --- Rang-Info, Signal, Bonus -------------------------------------------------------

func test_info_liefert_name_freischaltung_und_schwelle() -> void:
	var kern := _kern()
	kern.bogen["punkte"] = kern.erfolge.schwelle(2)
	var info: Dictionary = kern.spieler_level_info()
	assert_int(int(info["rang"])).is_equal(2)
	assert_int(int(info["level"])).is_equal(2)
	assert_int(int(info["max"])).is_equal(30)
	assert_str(String(info["name_id"])).is_equal("rang_name_2")
	assert_array(info["freischaltung"] as Array).contains(["menue_ziele"])
	assert_int(int(info["naechste_schwelle"])).is_equal(kern.erfolge.schwelle(3))


func test_rangnamen_stehen_fuer_alle_raenge_in_i18n() -> void:
	var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/i18n/de.json")) as Dictionary
	for r in range(1, 31):
		assert_bool(roh.has("rang_name_%d" % r)).is_true()
		assert_str(String(roh["rang_name_%d" % r])).is_not_empty()


func test_rang_up_signal_kommt_je_rang_mit_namen() -> void:
	var kern := _kern()
	var raenge: Array = []
	var alt: Array = []
	kern.bus.rank_up.connect(func(r: int, n: StringName) -> void: raenge.append([r, String(n)]))
	kern.bus.player_level_up.connect(func(l: int) -> void: alt.append(l))
	kern.bogen["punkte"] = kern.erfolge.schwelle(4)
	kern._pruefe_level()
	assert_int(raenge.size()).is_equal(3)
	assert_int(int(raenge[0][0])).is_equal(2)
	assert_str(String(raenge[0][1])).is_equal("rang_name_2")
	assert_array(alt).is_equal([2, 3, 4])
	kern._pruefe_level()
	assert_int(raenge.size()).is_equal(3)


func test_echtes_ziel_loest_rang_up_aus() -> void:
	var kern := _kern()
	var alt: Array = []
	kern.bus.player_level_up.connect(func(l: int) -> void: alt.append(l))
	_spiele_teil(kern)
	assert_int(kern.spieler_level()).is_equal(kern.erfolge.rang(kern.rang_punkte()))
	assert_int(alt.size()).is_equal(kern.spieler_level() - 1)


func test_rang_bonus_ersetzt_erfolgs_bonus() -> void:
	var kern := _kern()
	for d in kern.erfolge.definitionen():
		assert_float(float((d as Dictionary)["bonus"])).is_equal(0.0)
	assert_float(kern.erfolge_faktor()).is_equal(1.0)
	kern.bogen["punkte"] = kern.erfolge.schwelle(11)
	assert_float(kern.erfolge_faktor()).is_equal_approx(
		1.0 + kern.erfolge.bonus_je_rang * 10.0, 0.0001)
	assert_float(kern.welt_faktor()).is_equal_approx(kern.erfolge_faktor() * kern.erfahrungsfaktor(), 0.0001)


# --- Freischalt-Abfrage --------------------------------------------------------------

func test_ist_frei_haengt_am_rang() -> void:
	var kern := _kern()
	assert_bool(kern.ist_frei("menue_ziele")).is_false()
	assert_bool(kern.ist_frei("schub")).is_false()
	kern.bogen["punkte"] = kern.erfolge.schwelle(2)
	assert_bool(kern.ist_frei("menue_ziele")).is_true()
	assert_bool(kern.ist_frei("schub")).is_false()
	kern.bogen["punkte"] = kern.erfolge.schwelle(4)
	assert_bool(kern.ist_frei("schub")).is_true()
	assert_bool(kern.ist_frei("crew")).is_true()
	assert_bool(kern.ist_frei("menue_fortschritt")).is_true()
	assert_bool(kern.ist_frei("tagesaufgaben")).is_false()


func test_unbekannte_merkmale_sind_frei() -> void:
	var kern := _kern()
	assert_bool(kern.ist_frei("gibt_es_nicht")).is_true()
	assert_bool(kern.ist_frei("menue_ausbau")).is_true()


# --- Migration -------------------------------------------------------------------------

func _roundtrip(kern: GameCore, ohne_punkte: bool) -> GameCore:
	var roh: Dictionary = JSON.parse_string(JSON.stringify(kern.to_save().to_dict())) as Dictionary
	if ohne_punkte:
		(roh["bogen"] as Dictionary).erase("punkte")
	var neu := _kern()
	neu.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
	return neu


func test_punkte_ueberleben_speichern_und_laden() -> void:
	var kern := _kern()
	_spiele_teil(kern)
	kern.bogen["punkte"] = int(kern.bogen["punkte"]) + 10
	var neu := _roundtrip(kern, false)
	assert_int(neu.rang_punkte()).is_equal(kern.rang_punkte())
	assert_int(neu.spieler_level()).is_equal(kern.spieler_level())


func test_altstand_ohne_punkte_wird_aus_den_zielen_hergeleitet() -> void:
	var kern := _kern()
	_spiele_teil(kern)
	var neu := _roundtrip(kern, true)
	assert_int(neu.rang_punkte()).is_equal(kern.rang_punkte())
	assert_int(neu.spieler_level()).is_equal(kern.spieler_level())


func test_altstand_mitten_in_welt_eins_bekommt_passenden_rang() -> void:
	var kern := _kern()
	kern.kapital = 1.0e18
	for runde in range(3):
		for id in Ids.ALL_STATIONS:
			kern.upgrade_station_mehrfach(id, 10)
		for z in kern.ziele.sichtbar():
			kern.loese_ziel_ein(StringName(String(z["id"])))
	assert_int(kern.ziele.anzahl_eingeloest()).is_greater(0)
	var neu := _roundtrip(kern, true)
	assert_int(neu.rang_punkte()).is_equal(kern.rang_punkte())
	assert_int(neu.rang_punkte()).is_greater_equal(kern.ziele.anzahl_eingeloest())


func test_laden_loest_kein_rang_up_aus() -> void:
	var kern := _kern()
	_spiele_teil(kern)
	assert_int(kern.spieler_level()).is_greater(1)
	var roh: Dictionary = JSON.parse_string(JSON.stringify(kern.to_save().to_dict())) as Dictionary
	(roh["bogen"] as Dictionary).erase("punkte")
	var neu := _kern()
	var raenge: Array = []
	neu.bus.rank_up.connect(func(r: int, _n: StringName) -> void: raenge.append(r))
	neu.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
	assert_array(raenge).is_empty()
	# Und auch das naechste Ziel meldet keine alten Raenge nach.
	assert_int(neu.spieler_level()).is_equal(kern.spieler_level())


func test_v4_stand_rechnet_vorige_welt_voll_und_aktuelle_nach_zielen() -> void:
	var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_V4)) as Dictionary
	var stand: SaveData = SaveData.from_dict(SaveData.migrieren(roh))
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.from_save(stand)
	var a := Achievements.new()
	var erwartet: int = 0
	for i in range(kern.welt_index):
		erwartet += _welt_punkte(String(kern.welten.id(i))) + a.welt_fertig_punkte()
	for z in BalanceData.fuer_welt(kern.welt_id()).ziele:
		if stand.ziele.has(String((z as Dictionary)["id"])):
			erwartet += a.ziel_punkte(z as Dictionary)
	assert_int(kern.rang_punkte()).is_equal(erwartet)
	assert_int(kern.spieler_level()).is_equal(a.rang(erwartet))
	assert_int(kern.spieler_level()).is_greater_equal(6)


func test_alte_staende_v1_und_v2_laden_ohne_absturz_mit_rang() -> void:
	for pfad in ["res://tests/fixtures/saves/save_v1.json", "res://tests/fixtures/saves/save_v2.json"]:
		var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(pfad)) as Dictionary
		var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
		kern.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
		assert_int(kern.spieler_level()).is_between(1, 30)
		assert_int(kern.rang_punkte()).is_greater_equal(0)
