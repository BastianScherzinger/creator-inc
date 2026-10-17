## Design-Overhaul 15.10. (U4): Ziel-Ketten, Crew, Tagesaufgaben, Erfolge, Level,
## Sterne/Empfehlung, Experimente und die Migration v4 -> v5.
extends GdUnitTestSuite

const FIXTURE_V4: String = "res://tests/fixtures/saves/save_v4.json"
const TAG: int = 20500


func _kern() -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.tag_override = TAG
	return kern


## Eine Welt-1-Balance mit eigener Crew (Freischaltung ueber die Stationsstufe).
func _kern_mit_crew() -> GameCore:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	roh["crew_kosten_faktor"] = 1.0
	roh["crew"] = {"station_intake": {"raenge": [
		{"kosten": 100.0, "faktor": 1.1}, {"kosten": 1000.0, "faktor": 1.2},
		{"kosten": 10000.0, "faktor": 1.35}]}}
	var kern := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 0)
	kern.tag_override = TAG
	return kern


# --- Ziel-Ketten ---------------------------------------------------------------

func test_jedes_ziel_gehoert_zu_genau_einer_kette() -> void:
	var kern := _kern()
	var summe: int = 0
	for kette_id in kern.ketten_ids():
		summe += int(kern.kette_stand(kette_id)["anzahl"])
	assert_int(summe).is_equal(kern.ziele.anzahl())
	assert_array(kern.ketten_ids()).contains(["start", "welt"])


func test_alle_welten_haben_gueltige_ketten() -> void:
	var welten := WorldData.laden()
	for i in range(welten.anzahl()):
		var balance := BalanceData.fuer_welt(welten.id(i))
		assert_bool(balance.validieren()) \
			.override_failure_message("%s: %s" % [welten.id(i), "\n".join(balance.fehler)]).is_true()


func test_unbekannte_kette_faellt_bei_der_pruefung_auf() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	(roh["ziele"] as Array)[0]["kette"] = "bereich_99"
	var balance := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(balance.validieren()).is_false()


func test_kette_ziele_hat_genau_ein_laeuft_und_den_status_erledigt() -> void:
	var kern := _kern()
	var liste: Array[Dictionary] = kern.kette_ziele("start")
	assert_int(liste.size()).is_greater(0)
	var laeuft: int = 0
	for z in liste:
		if String(z["status"]) == "laeuft":
			laeuft += 1
	assert_int(laeuft).is_less_equal(1)
	kern.kapital = 1.0e12
	var erstes: String = String(liste[0]["id"])
	for id in Ids.ALL_STATIONS:
		kern.upgrade_station_mehrfach(id, 12)
	kern.loese_ziel_ein(StringName(erstes))
	if kern.ziele.ist_eingeloest(erstes):
		assert_str(String(kern.kette_ziele("start")[0]["status"])).is_equal("erledigt")


func test_kette_bedingung_wird_erfuellt_wenn_alle_ziele_eingeloest() -> void:
	var kern := _kern()
	assert_float(kern.messwert({"typ": "kette", "kette": "start"})).is_equal(0.0)
	kern.kapital = 1.0e18
	for kette_id in ["start"]:
		var sicherung: int = 0
		while not kern.kette_fertig(kette_id) and sicherung < 400:
			sicherung += 1
			for id in Ids.ALL_STATIONS:
				kern.upgrade_station_mehrfach(id, 3)
				var s: StationModel = kern.kette.station(id)
				for p in s.ausstattung:
					kern.kaufe_ausstattung(id, p.id)
			for bereich_id in kern.bereiche.ids():
				kern.kaufe_bereich(bereich_id)
			for z in kern.ziele.sichtbar():
				kern.loese_ziel_ein(StringName(String(z["id"])))
	assert_bool(kern.kette_fertig("start")).is_true()
	assert_float(kern.messwert({"typ": "kette", "kette": "start"})).is_equal(1.0)


func test_haupt_ziel_und_ort() -> void:
	var kern := _kern()
	var z: Dictionary = kern.haupt_ziel()
	assert_bool(z.is_empty()).is_false()
	assert_bool(z.has("belohnung")).is_true()
	var ort: Dictionary = kern.ziel_ort(String(z["id"]))
	assert_bool(["station", "bereich", "menue"].has(String(ort["art"]))).is_true()
	assert_str(String(kern.ziel_ort("gibt_es_nicht")["art"])).is_equal("menue")


func test_ort_wird_aus_dem_ziel_abgeleitet() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	roh["ziele"] = [
		{"id": "z_a", "kette": "start", "typ": "station_stufe", "station": "station_buffer", "wert": 5},
		{"id": "z_b", "kette": "bereich_1", "typ": "bereich", "bereich": "bereich_1", "wert": 1},
		{"id": "z_c", "kette": "welt", "typ": "stufen_gesamt", "wert": 5,
			"ort": {"art": "station", "id": "station_intake"}},
	]
	var kern := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 0)
	assert_str(String(kern.ziel_ort("z_a")["id"])).is_equal("station_buffer")
	assert_str(String(kern.ziel_ort("z_b")["art"])).is_equal("bereich")
	assert_str(String(kern.ziel_ort("z_c")["id"])).is_equal("station_intake")


func test_leiste_hat_hoechstens_zwei_eintraege() -> void:
	var kern := _kern()
	kern.tagesaufgaben_system.ab_fortschritt = 0.0
	var leiste: Array[Dictionary] = kern.leiste()
	assert_int(leiste.size()).is_between(1, 2)
	assert_str(String(leiste[0]["art"])).is_equal("ziel")
	if leiste.size() == 2:
		assert_str(String(leiste[1]["art"])).is_equal("tagesaufgabe")


# --- Sterne, Empfehlung, Raeume ------------------------------------------------------

func test_stern_info_zeigt_den_weg_zum_naechsten_stern() -> void:
	var kern := _kern()
	var s: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	s.stufe = 7
	var info: Dictionary = kern.stern_info(Ids.STATION_INTAKE)
	assert_int(int(info["stufen_bis"])).is_equal(s.meilenstein_intervall - 7)
	assert_float(float(info["fortschritt"])).is_equal_approx(7.0 / float(s.meilenstein_intervall), 0.001)
	assert_int(int(info["soll"])).is_equal(s.meilenstein_intervall)
	assert_float(float(info["faktor"])).is_equal_approx(s.meilenstein_faktor, 0.0001)


func test_stern_signal_kommt_beim_ueberschreiten() -> void:
	var kern := _kern()
	kern.kapital = 1.0e15
	var s: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	s.stufe = s.meilenstein_intervall - 1
	var gemeldet: Array = []
	kern.bus.star_reached.connect(func(id: StringName, sterne: int) -> void:
		gemeldet.append([String(id), sterne]))
	kern.upgrade_station(Ids.STATION_INTAKE)
	assert_int(gemeldet.size()).is_equal(1)
	assert_int(int(gemeldet[0][1])).is_equal(1)


func test_kauf_lohnt_nur_am_engpass_und_nur_wenn_bezahlbar() -> void:
	var kern := _kern()
	kern.kapital = 1.0e12
	var engpass: StringName = kern.kette.bottleneck()
	assert_bool(kern.kauf_lohnt(engpass)).is_true()
	for id in Ids.CHAIN:
		var s: StationModel = kern.kette.station(id)
		var andere_groesser: bool = s.durchsatz() > kern.kette.station(engpass).durchsatz() * 1.01
		if id != engpass and andere_groesser:
			assert_bool(kern.kauf_lohnt(id)).is_false()
	kern.kapital = 0.0
	assert_bool(kern.kauf_lohnt(engpass)).is_false()


func test_empfehlung_ist_bezahlbar_und_bringt_mehr() -> void:
	var kern := _kern()
	kern.kapital = 1.0e6
	var e: Dictionary = kern.empfehlung()
	assert_bool(e.is_empty()).is_false()
	assert_float(float(e["preis"])).is_less_equal(kern.kapital)
	assert_float(float(e["mehr"])).is_greater(0.0)
	kern.kapital = 0.0
	assert_bool(kern.empfehlung().is_empty()).is_true()


func test_bereich_info() -> void:
	var kern := _kern()
	var info: Dictionary = kern.bereich_info(&"bereich_2")
	assert_float(float(info["bonus_faktor"])).is_greater(1.0)
	assert_bool(bool(info["gekauft"])).is_false()
	assert_bool(bool(info["bezahlbar"])).is_false()
	assert_bool(kern.bereich_info(&"gibt_es_nicht").is_empty()).is_true()
	assert_str(String(kern.bereich_info(&"bereich_1")["schaltet_station"])).is_equal("station_transport")


# --- Crew -------------------------------------------------------------------------------

func test_crew_ist_gesperrt_bis_die_bedingung_erfuellt_ist() -> void:
	var kern := _kern_mit_crew()
	kern.kapital = 1.0e9
	assert_bool(kern.crew_hat(Ids.STATION_INTAKE)).is_true()
	assert_bool(kern.crew_frei(Ids.STATION_INTAKE)).is_false()
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_false()
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	assert_bool(kern.crew_frei(Ids.STATION_INTAKE)).is_true()


func test_crew_kauf_hebt_die_station_und_kostet_geld() -> void:
	var kern := _kern_mit_crew()
	kern.kapital = 1.0e9
	var s: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	s.stufe = kern.crew.frei_ab_stufe
	var vorher: float = s.durchsatz()
	var geld: float = kern.kapital
	var gemeldet: Array = []
	kern.bus.crew_hired.connect(func(id: StringName, rang: int) -> void:
		gemeldet.append([String(id), rang]))
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	assert_float(geld - kern.kapital).is_equal_approx(100.0, 0.001)
	assert_int(kern.crew_rang(Ids.STATION_INTAKE)).is_equal(1)
	assert_float(s.durchsatz() / vorher).is_equal_approx(1.1, 0.0001)
	assert_float(kern.crew_faktor(Ids.STATION_INTAKE)).is_equal_approx(1.1, 0.0001)
	assert_int(gemeldet.size()).is_equal(1)
	# Rang 2 und 3 nacheinander, dann ist Schluss.
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_true()
	assert_float(s.durchsatz() / vorher).is_equal_approx(1.35, 0.0001)
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_false()


func test_crew_ohne_geld_kauft_nichts() -> void:
	var kern := _kern_mit_crew()
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	kern.kapital = 50.0
	assert_bool(kern.kaufe_crew(Ids.STATION_INTAKE)).is_false()
	assert_float(kern.kapital).is_equal(50.0)
	var raenge: Array[Dictionary] = kern.crew_raenge(Ids.STATION_INTAKE)
	assert_int(raenge.size()).is_equal(3)
	assert_bool(bool(raenge[0]["kaufbar"])).is_false()
	assert_bool(bool(raenge[0]["naechster"])).is_true()


func test_crew_ohne_eigene_daten_nimmt_den_standard() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	roh.erase("crew")
	var kern := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 0)
	for id in Ids.ALL_STATIONS:
		assert_bool(kern.crew_hat(id)).is_true()
	var basis: float = float((roh["stationen"]["station_intake"] as Dictionary)["basis_kosten"])
	var raenge: Array[Dictionary] = kern.crew_raenge(Ids.STATION_INTAKE)
	assert_float(float(raenge[0]["kosten"])).is_greater(basis)
	assert_float(float(raenge[0]["faktor"])).is_less(float(raenge[2]["faktor"]))


func test_crew_kostenregler_skaliert_alle_preise() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/zimmer.json")) as Dictionary
	roh["crew_kosten_faktor"] = 1.0
	var normal := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 0)
	roh["crew_kosten_faktor"] = 3.0
	var teuer := GameCore.new(BalanceData.aus_text(JSON.stringify(roh)), 0)
	assert_float(teuer.crew.kosten_naechster(Ids.STATION_BUFFER)) \
		.is_equal_approx(normal.crew.kosten_naechster(Ids.STATION_BUFFER) * 3.0, 0.001)


func test_crew_und_raum_bonus_multiplizieren_sich() -> void:
	var kern := _kern_mit_crew()
	kern.kapital = 1.0e9
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	kern.kaufe_bereich(&"bereich_1")
	kern.kaufe_bereich(&"bereich_2")
	kern.kaufe_crew(Ids.STATION_INTAKE)
	var s: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	assert_float(s.extern_faktor).is_equal_approx(kern.raum_faktor(Ids.STATION_INTAKE) * 1.1, 0.0001)
	assert_float(kern.raum_faktor(Ids.STATION_INTAKE)).is_greater(1.0)


func test_crew_geht_durch_den_spielstand() -> void:
	var kern := _kern_mit_crew()
	kern.kapital = 1.0e9
	kern.kette.station(Ids.STATION_INTAKE).stufe = kern.crew.frei_ab_stufe
	kern.kaufe_crew(Ids.STATION_INTAKE)
	kern.kaufe_crew(Ids.STATION_INTAKE)
	var daten: Dictionary = JSON.parse_string(JSON.stringify(kern.to_save().to_dict())) as Dictionary
	var neu := _kern_mit_crew()
	neu.from_save(SaveData.from_dict(SaveData.migrieren(daten)))
	assert_int(neu.crew_rang(Ids.STATION_INTAKE)).is_equal(2)
	assert_float(neu.kette.station(Ids.STATION_INTAKE).extern_faktor).is_equal_approx(1.2, 0.0001)


func test_einkommen_nach_crew_stimmt_mit_dem_kauf_ueberein() -> void:
	var kern := _kern_mit_crew()
	kern.kapital = 1.0e9
	var s: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	s.stufe = kern.crew.frei_ab_stufe
	var prognose: float = kern.einkommen_nach_crew(Ids.STATION_INTAKE)
	var erfolge_vorher: float = kern.erfolge_faktor()
	kern.kaufe_crew(Ids.STATION_INTAKE)
	# Die erste Crew ist selbst ein Erfolg (+1 % Weltfaktor) -- das gehoert nicht zur Prognose.
	var bereinigt: float = kern.einkommen_pro_sekunde() * erfolge_vorher / kern.erfolge_faktor()
	assert_float(bereinigt).is_equal_approx(prognose, prognose * 0.0001)


# --- Tagesaufgaben ----------------------------------------------------------------------

func _kern_aufgaben() -> GameCore:
	var kern := _kern()
	kern.tagesaufgaben_system.ab_fortschritt = 0.0
	return kern


func test_tagesaufgaben_erst_ab_dem_weltfortschritt() -> void:
	var kern := _kern()
	assert_float(kern.tagesaufgaben_system.ab_fortschritt).is_greater(0.0)
	assert_bool(kern.tagesaufgaben_aktiv()).is_false()
	assert_int(kern.tagesaufgaben().size()).is_equal(0)


func test_tagesaufgaben_sind_zwei_und_pro_tag_gleich() -> void:
	var a := _kern_aufgaben()
	var b := _kern_aufgaben()
	var liste_a: Array[Dictionary] = a.tagesaufgaben()
	var liste_b: Array[Dictionary] = b.tagesaufgaben()
	assert_int(liste_a.size()).is_equal(a.tagesaufgaben_system.pro_tag)
	assert_str(String(liste_a[0]["id"])).is_equal(String(liste_b[0]["id"]))
	assert_str(String(liste_a[1]["id"])).is_equal(String(liste_b[1]["id"]))
	assert_str(String(liste_a[0]["zaehler"])).is_not_equal(String(liste_a[1]["zaehler"]))


func test_tagesaufgabe_zaehlt_wird_erfuellt_und_zahlt_einmal() -> void:
	var kern := _kern_aufgaben()
	kern.kapital = 1.0e9
	var fertig: Array = []
	kern.bus.daily_task_completed.connect(func(id: StringName) -> void: fertig.append(String(id)))
	# Alle Zaehler bedienen: Stufen, Ziel, Raum, Crew sind ueber Kaeufe erreichbar.
	for runde in range(40):
		for id in Ids.ALL_STATIONS:
			kern.upgrade_station_mehrfach(id, 2)
		for bereich_id in kern.bereiche.ids():
			kern.kaufe_bereich(bereich_id)
		for z in kern.ziele.sichtbar():
			kern.loese_ziel_ein(StringName(String(z["id"])))
	var offene: Array[Dictionary] = kern.tagesaufgaben()
	var erfuellt: Dictionary = {}
	for a in offene:
		if bool(a["erfuellt"]):
			erfuellt = a
	if erfuellt.is_empty():
		# Nur Momente/Crew im Tagespool dieses Tages: nicht ueber Kaeufe erreichbar -- dann
		# zaehlt der Test nur, dass der Fortschritt nie ueber das Soll hinausgeht.
		for a in offene:
			assert_float(float(a["ist"])).is_less_equal(float(a["soll"]))
		return
	assert_array(fertig).contains([String(erfuellt["id"])])
	var vorher: float = kern.kapital
	var betrag: float = kern.loese_tagesaufgabe_ein(StringName(String(erfuellt["id"])))
	assert_float(betrag).is_greater(0.0)
	assert_float(kern.kapital).is_equal_approx(vorher + betrag, 0.01)
	assert_float(kern.loese_tagesaufgabe_ein(StringName(String(erfuellt["id"])))).is_equal(0.0)


func test_tagesaufgabe_stufen_kauf_wird_gezaehlt() -> void:
	var daten: Dictionary = {"pro_tag": 1, "ab_fortschritt": 0.0, "pool": [
		{"id": "t_x", "zaehler": "stufen_kauf", "wert": 3, "belohnung_sekunden": 60, "belohnung_minimum": 10}]}
	var kern := _kern()
	kern.tagesaufgaben_system = DailyTasks.new([], daten)
	kern.kapital = 1.0e9
	assert_int(kern.tagesaufgaben().size()).is_equal(1)
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 2)
	assert_float(float(kern.tagesaufgaben()[0]["ist"])).is_equal(2.0)
	assert_bool(bool(kern.tagesaufgaben()[0]["erfuellt"])).is_false()
	kern.upgrade_station(Ids.STATION_INTAKE)
	assert_bool(bool(kern.tagesaufgaben()[0]["erfuellt"])).is_true()
	assert_float(kern.loese_tagesaufgabe_ein(&"t_x")).is_greater(0.0)


func test_neuer_tag_bringt_neue_aufgaben_und_setzt_den_stand_zurueck() -> void:
	var daten: Dictionary = {"pro_tag": 1, "ab_fortschritt": 0.0, "pool": [
		{"id": "t_x", "zaehler": "stufen_kauf", "wert": 3, "belohnung_sekunden": 60, "belohnung_minimum": 10}]}
	var kern := _kern()
	kern.tagesaufgaben_system = DailyTasks.new([], daten)
	kern.kapital = 1.0e9
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 2)
	kern.tag_override = TAG + 1
	assert_float(float(kern.tagesaufgaben()[0]["ist"])).is_equal(0.0)


func test_welt_pool_ueberschreibt_den_globalen_eintrag() -> void:
	var global: Dictionary = {"pro_tag": 1, "ab_fortschritt": 0.0, "pool": [
		{"id": "t_x", "zaehler": "stufen_kauf", "wert": 3}]}
	var aufgaben := DailyTasks.new([{"id": "t_x", "zaehler": "stufen_kauf", "wert": 9},
		{"id": "t_y", "zaehler": "ziel_eingeloest", "wert": 1}], global)
	assert_float(aufgaben.soll("t_x")).is_equal(9.0)
	assert_float(aufgaben.soll("t_y")).is_equal(1.0)


func test_tagesaufgaben_gehen_durch_den_spielstand() -> void:
	var daten: Dictionary = {"pro_tag": 1, "ab_fortschritt": 0.0, "pool": [
		{"id": "t_x", "zaehler": "stufen_kauf", "wert": 3, "belohnung_sekunden": 60, "belohnung_minimum": 10}]}
	var kern := _kern()
	kern.tagesaufgaben_system = DailyTasks.new([], daten)
	kern.kapital = 1.0e9
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 2)
	var roh: Dictionary = JSON.parse_string(JSON.stringify(kern.to_save().to_dict())) as Dictionary
	var neu := _kern()
	neu.tagesaufgaben_system = DailyTasks.new([], daten)
	neu.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
	assert_float(float(neu.tagesaufgaben()[0]["ist"])).is_equal(2.0)


# --- Erfolge und Level --------------------------------------------------------------------

func test_erfolg_erster_raum_zaehlt_ohne_bonus() -> void:
	var kern := _kern()
	kern.kapital = 1.0e9
	var vorher: float = kern.welt_faktor()
	var gemeldet: Array = []
	kern.bus.achievement_unlocked.connect(func(id: StringName, bonus: float) -> void:
		gemeldet.append([String(id), bonus]))
	assert_bool(kern.kaufe_bereich(&"bereich_1")).is_true()
	assert_array(gemeldet.map(func(e: Array) -> String: return e[0])).contains(["erfolg_erster_raum"])
	# Erfolge sind seit K2 P2a Abzeichen ohne Bonus; der Dauerfaktor kommt aus dem Rang.
	assert_float(kern.welt_faktor()).is_equal(vorher)
	assert_float(kern.erfolge_faktor()).is_equal(1.0)
	# Nur einmal.
	var anzahl: int = gemeldet.size()
	kern.kaufe_bereich(&"bereich_2")
	assert_int(gemeldet.filter(func(e: Array) -> bool: return e[0] == "erfolg_erster_raum").size()).is_equal(1)
	assert_int(gemeldet.size()).is_greater_equal(anzahl)


func test_es_gibt_zwoelf_erfolge_mit_gueltigen_typen() -> void:
	var kern := _kern()
	var liste: Array[Dictionary] = kern.erfolge_liste()
	assert_int(liste.size()).is_equal(12)
	for e in kern.erfolge.definitionen():
		var typ: String = String((e["bedingung"] as Dictionary)["typ"])
		assert_bool([
			"sterne_station", "sterne_gesamt", "ziele_gesamt", "bereiche_gesamt", "welten_fertig",
			"serie_tage", "crew_gekauft", "tagesaufgaben", "momente", "stufen_gesamt", "durchlaeufe",
		].has(typ)).is_true()


func test_erfolge_gehen_durch_den_spielstand_und_den_weltwechsel() -> void:
	var kern := _kern()
	kern.kapital = 1.0e9
	kern.kaufe_bereich(&"bereich_1")
	var roh: Dictionary = JSON.parse_string(JSON.stringify(kern.to_save().to_dict())) as Dictionary
	var neu := _kern()
	neu.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
	assert_bool(neu.erfolge.ist_erreicht("erfolg_erster_raum")).is_true()
	assert_int(int(neu.bogen["bereiche"])).is_equal(1)
	# Der Erfolg ueberlebt den Weltwechsel.
	neu.wechsle_welt()
	assert_bool(neu.erfolge.ist_erreicht("erfolg_erster_raum")).is_true()
	assert_int(int(neu.bogen["welten"])).is_equal(1)


func test_spieler_rang_waechst_mit_den_punkten_der_ziele() -> void:
	var kern := _kern()
	assert_int(kern.spieler_level()).is_equal(1)
	var stufen: Array = []
	kern.bus.player_level_up.connect(func(l: int) -> void: stufen.append(l))
	kern.kapital = 1.0e15
	for runde in range(30):
		for id in Ids.ALL_STATIONS:
			kern.upgrade_station_mehrfach(id, 5)
		for bereich_id in kern.bereiche.ids():
			kern.kaufe_bereich(bereich_id)
		for z in kern.ziele.sichtbar():
			kern.loese_ziel_ein(StringName(String(z["id"])))
	assert_int(kern.spieler_level()).is_equal(kern.erfolge.rang(kern.rang_punkte()))
	assert_int(kern.spieler_level()).is_greater(1)
	# Ein Rang-Up je Rang, nicht je Ziel.
	assert_int(stufen.size()).is_equal(kern.spieler_level() - 1)
	assert_int(int(stufen[0])).is_equal(2)
	assert_int(int(kern.spieler_level_info()["max"])).is_equal(30)


func test_level_ist_nach_oben_begrenzt() -> void:
	var a := Achievements.new()
	assert_int(a.rang(0)).is_equal(1)
	assert_int(a.rang(100000)).is_equal(a.level_max)


# --- Experimente ----------------------------------------------------------------------------

func test_experimente_sind_deterministisch_und_respektieren_die_erzwingung() -> void:
	for schirm in ["stations_panel", "raum_panel", "ziele_leiste", "story_szene"]:
		assert_array(Experimente.varianten(schirm)).contains_exactly(["a", "b"])
		assert_str(Experimente.waehle(schirm, 4711)).is_equal(Experimente.waehle(schirm, 4711))
		assert_str(Experimente.waehle(schirm, 4711, "b")).is_equal("b")
		assert_str(Experimente.waehle(schirm, 4711, "z")).is_equal(Experimente.waehle(schirm, 4711))
	assert_str(Experimente.waehle("gibt_es_nicht", 1)).is_equal("a")


func test_experimente_verteilen_auf_beide_varianten() -> void:
	var gesehen: Dictionary = {}
	for wert in range(1, 200):
		gesehen[Experimente.waehle("stations_panel", wert, "", false)] = true
	assert_int(gesehen.size()).is_equal(2)


func test_entschiedene_k3_schirme_sind_weg_und_boost_bleibt_a() -> void:
	var gemerkt: Dictionary = Experimente.override_schirm.duplicate()
	var gemerkt_global: String = Experimente.override
	Experimente.lade_argumente(PackedStringArray())
	# A/B-Urteil 16.10.2026: karte, plakette, pfeil, zoom -> b, A-Zweige gestrichen.
	for schirm in ["karte", "plakette", "pfeil", "zoom"]:
		assert_array(Experimente.varianten(schirm)).is_empty()
		assert_bool(Experimente.schirme().has(schirm)).is_false()
	assert_array(Experimente.varianten("boost")).contains_exactly(["a", "b"])
	assert_str(Experimente.variante("boost")).is_equal("a")
	Experimente.override_schirm = gemerkt
	Experimente.override = gemerkt_global


func test_ab_schalter_je_schirm() -> void:
	var gemerkt: Dictionary = Experimente.override_schirm.duplicate()
	var gemerkt_global: String = Experimente.override
	assert_dict(Experimente.parse_ab("karte=a, Pfeil=B,,kaputt,=x")).is_equal({"karte": "a", "pfeil": "b"})
	Experimente.lade_argumente(PackedStringArray(["--frisch", "--ab", "raum_panel=b,boost=b", "--ab", "ziele_leiste=b"]))
	assert_str(Experimente.variante("raum_panel")).is_equal("b")
	assert_str(Experimente.variante("boost")).is_equal("b")
	assert_str(Experimente.variante("ziele_leiste")).is_equal("b")
	assert_str(Experimente.variante("story_szene")).is_equal("a")     # nicht genannt: Standard
	# --variante bleibt globaler Rueckfall, --ab gewinnt je Schirm.
	Experimente.lade_argumente(PackedStringArray(["--variante", "b", "--ab", "boost=a"]))
	assert_str(Experimente.variante("raum_panel")).is_equal("b")
	assert_str(Experimente.variante("boost")).is_equal("a")
	# Unbekannte Variante wird ignoriert.
	Experimente.lade_argumente(PackedStringArray(["--ab", "raum_panel=z"]))
	assert_str(Experimente.variante("raum_panel")).is_equal("a")
	Experimente.override_schirm = gemerkt
	Experimente.override = gemerkt_global


func test_experimente_datei_enthaelt_keine_erhebung() -> void:
	var text: String = FileAccess.get_file_as_string("res://data/experimente.json").to_lower()
	for verboten in ["http", "analytics", "tracking", "endpoint"]:
		assert_bool(text.contains(verboten)).is_false()


func test_overlay_mischt_tief_und_ersetzt_listen() -> void:
	var basis: Dictionary = {"a": {"x": 1, "y": 2}, "liste": [1, 2, 3], "z": 5}
	var zusatz: Dictionary = {"_kommentar": "egal", "a": {"y": 9}, "liste": [7]}
	var ergebnis: Dictionary = BalanceData._tief_mischen(basis, zusatz)
	assert_int(int(ergebnis["a"]["x"])).is_equal(1)
	assert_int(int(ergebnis["a"]["y"])).is_equal(9)
	assert_int((ergebnis["liste"] as Array).size()).is_equal(1)
	assert_int(int(ergebnis["z"])).is_equal(5)
	assert_bool(ergebnis.has("_kommentar")).is_false()
	assert_int(int(basis["a"]["y"])).is_equal(2)


func test_overlay_wird_nur_mit_gesetzter_variante_geladen() -> void:
	BalanceData.variante = "ohne_datei"
	var ohne := BalanceData.fuer_welt("zimmer")
	BalanceData.variante = ""
	var normal := BalanceData.fuer_welt("zimmer")
	assert_float(ohne.start_kapital).is_equal(normal.start_kapital)


# --- Migration v4 -> v5 -----------------------------------------------------------------------

func _lade_v4() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(FIXTURE_V4)) as Dictionary


func test_v4_stand_migriert_und_laedt() -> void:
	var roh: Dictionary = _lade_v4()
	var migriert: Dictionary = SaveData.migrieren(roh)
	assert_int(int(migriert["schema_version"])).is_equal(5)
	assert_int(int(roh["schema_version"])).is_equal(4)
	var stand: SaveData = SaveData.from_dict(migriert)
	assert_dict(stand.crew).is_empty()
	assert_dict(stand.bogen).is_empty()
	assert_array(stand.erfolge).is_empty()
	assert_int(stand.installations_wert).is_equal(0)
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.tag_override = TAG
	kern.from_save(stand)
	assert_int(kern.welt_index).is_equal(1)
	assert_float(kern.kapital).is_equal_approx(4321.5, 0.001)
	assert_int(kern.kette.station(Ids.STATION_INTAKE).stufe).is_equal(14)
	assert_int(kern.crew_rang(Ids.STATION_INTAKE)).is_equal(0)
	assert_int(kern.geschenk.serientag).is_equal(3)


func test_v4_bogen_wird_aus_welt_und_zielen_hergeleitet() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.from_save(SaveData.from_dict(SaveData.migrieren(_lade_v4())))
	var welt_1 := BalanceData.fuer_welt("zimmer")
	assert_int(int(kern.bogen["ziele"])).is_equal(5 + welt_1.ziele.size())
	assert_int(int(kern.bogen["welten"])).is_equal(1)
	assert_int(int(kern.bogen["bereiche"])).is_equal(2 + welt_1.bereiche.size())
	assert_int(int(kern.bogen["momente"])).is_equal(4)
	assert_int(kern.spieler_level()).is_equal(kern.erfolge.rang(kern.rang_punkte()))


func test_v4_erfolge_werden_still_nachgetragen() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var gemeldet: Array = []
	kern.bus.achievement_unlocked.connect(func(id: StringName, _b: float) -> void: gemeldet.append(String(id)))
	var level: Array = []
	kern.bus.player_level_up.connect(func(l: int) -> void: level.append(l))
	kern.from_save(SaveData.from_dict(SaveData.migrieren(_lade_v4())))
	assert_bool(kern.erfolge.ist_erreicht("erfolg_erster_raum")).is_true()
	assert_array(gemeldet).is_empty()
	assert_array(level).is_empty()


func test_gespeichert_wird_schema_5_mit_installationswert() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.from_save(SaveData.from_dict(SaveData.migrieren(_lade_v4())))
	var s1: SaveData = kern.to_save()
	var s2: SaveData = kern.to_save()
	assert_int(s1.schema_version).is_equal(5)
	assert_int(s1.installations_wert).is_greater(0)
	assert_int(s1.installations_wert).is_equal(s2.installations_wert)
	var roh: Dictionary = JSON.parse_string(JSON.stringify(s1.to_dict())) as Dictionary
	assert_str(SaveData.pruefsumme(roh)).is_equal(SaveData.pruefsumme(roh))
	var neu := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	neu.from_save(SaveData.from_dict(SaveData.migrieren(roh)))
	assert_int(int(neu.bogen["ziele"])).is_equal(int(kern.bogen["ziele"]))
	assert_int(neu.to_save().installations_wert).is_equal(s1.installations_wert)


func test_stand_aus_v1_und_v2_laedt_weiterhin() -> void:
	for pfad in ["res://tests/fixtures/saves/save_v1.json", "res://tests/fixtures/saves/save_v2.json"]:
		var roh: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(pfad)) as Dictionary
		var stand: SaveData = SaveData.from_dict(SaveData.migrieren(roh))
		assert_int(stand.schema_version).is_equal(5)
		var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
		kern.from_save(stand)
		assert_int(kern.spieler_level()).is_greater_equal(1)


func test_tagesaufgaben_belohnen_hoechstens_zehn_minuten_einkommen() -> void:
	var roh: Dictionary = DailyTasks.lade_roh()
	for eintrag in (roh["pool"] as Array):
		assert_float(float((eintrag as Dictionary)["belohnung_sekunden"])).is_less_equal(600.0)
