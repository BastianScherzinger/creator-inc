## Prueft, dass JEDE Welt allein aus Daten in voller Tiefe laeuft (NACHT_PLAN N02).
##
## Daten (worlds.json, Balance), die neuen Datenwege (Module je Welt, Licht als
## Dictionary, mehrere Darsteller, Varianten) und die Sondermechaniken im
## Zusammenspiel mit dem Abschluss bei 100 %.
extends GdUnitTestSuite

const TAKT: float = SimClock.TICK_DAUER


func _welten() -> WorldData:
	return WorldData.laden()


func _kern(index: int) -> GameCore:
	var welten := _welten()
	return GameCore.new(BalanceData.fuer_welt(welten.id(index)), index)


## Kauft alles, was die Welt hergibt -- so, wie ein Spieler es am Ende getan hat.
func _alles_kaufen(kern: GameCore, mit_umbau: bool = true) -> void:
	kern.kapital = 1.0e30
	if mit_umbau and kern.limit_gilt():
		kern.kaufe_umbau()
	for bereich_id in kern.bereiche.ids():
		kern.kaufe_bereich(bereich_id)
	for id in Ids.ALL_STATIONS:
		kern.upgrade_station_mehrfach(id, -1)
		var station: StationModel = kern.kette.station(id)
		for p in station.ausstattung:
			while kern.kaufe_ausstattung(id, p.id):
				pass


# --- Daten ----------------------------------------------------------------------

func test_jede_welt_hat_gueltige_balance_in_tiefe() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		var id: String = welten.id(i)
		var b := BalanceData.fuer_welt(id)
		assert_bool(b.validieren()).override_failure_message(
			"%s: %s" % [id, "\n".join(b.fehler)]).is_true()
		assert_str(String(b.abschluss)).override_failure_message(id).is_equal("alles")
		# Fuenf Raeume; ausser in "webseiten" kommt Raum 3b (bereich_6) dazu (K3 B1).
		assert_int(b.bereiche.size()).override_failure_message(id).is_equal(5 if id == "webseiten" else 6)
		assert_str(String((b.bereiche["bereich_1"] as Dictionary).get("schaltet_frei", ""))).is_equal("unlock_transport")
		assert_str(String((b.bereiche["bereich_3"] as Dictionary).get("schaltet_frei", ""))).is_equal("unlock_special")
		assert_str(String((b.bereiche["bereich_5"] as Dictionary).get("nach", ""))).is_equal("bereich_4")
		assert_int(b.ziele.size()).override_failure_message(id).is_greater_equal(20)
		assert_int(b.nachrichten.size()).override_failure_message(id).is_equal(24)   # 22 + nachricht_23/24 (K3 B3)
		var letzte: Dictionary = (b.nachrichten[b.nachrichten.size() - 1] as Dictionary).get("ausloeser", {}) as Dictionary
		assert_str(String(letzte.get("typ", ""))).override_failure_message(id).is_equal("abschluss")
		for sid in Ids.ALL_STATIONS:
			var st: Dictionary = b.stationen[String(sid)] as Dictionary
			assert_int((st.get("ausstattung", {}) as Dictionary).size()) \
				.override_failure_message("%s/%s" % [id, sid]).is_equal(3)


func test_jede_welt_hat_eine_karte_aus_zonen() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		var id: String = welten.id(i)
		assert_bool(welten.hat_zonen(i)).override_failure_message(id).is_true()
		assert_str(welten.stationsmodell(i)).override_failure_message(id).is_equal("ausstattung")
		assert_str(String(welten.figuren(i)["modus"])).override_failure_message(id).is_equal("wg")
		# Jeder Bereich hat eine Zone, sonst gibt es nichts zum Antippen.
		var bereiche: Dictionary = welten.bereich_positionen(i)
		for n in range(1, 6):
			assert_bool(bereiche.has(StringName("bereich_%d" % n))) \
				.override_failure_message("%s: bereich_%d ohne Zone" % [id, n]).is_true()
		# Jede Station steht in einer Zone, special in der Zone von bereich_3.
		var stationen: Dictionary = welten.stationen(i)
		for sid in Ids.ALL_STATIONS:
			assert_bool(stationen.has(sid)).override_failure_message("%s: %s" % [id, sid]).is_true()
			var zone: Dictionary = welten.zone_an(i, stationen[sid] as Vector3)
			assert_bool(zone.is_empty()).override_failure_message(
				"%s: %s steht ausserhalb der Zonen" % [id, sid]).is_false()
		var sonder_zone: Dictionary = welten.zone_an(i, stationen[Ids.STATION_SPECIAL] as Vector3)
		assert_str(String(sonder_zone.get("bereich", ""))).override_failure_message(id).is_equal("bereich_3")


func test_neue_welten_nutzen_die_standardmodule() -> void:
	var welten := _welten()
	# Welt 1 hat seit der Welt-Optik (M1) eine eigene Modultabelle (Dictionary), alle anderen die Standardmodule.
	assert_bool(welten.module(0) is Dictionary).is_true()
	for i in range(1, welten.anzahl()):
		assert_str(String(welten.module(i))).override_failure_message(welten.id(i)).is_equal("standard")


# --- Datenwege der Darstellung ----------------------------------------------------

func test_modultabelle_welt_1_bleibt_wie_sie_war() -> void:
	var bauer := GrundrissBauer.new()
	bauer.waehle_module("")
	assert_array(bauer.boden_module("holz")).contains_exactly(["wg_boden_holz_a", "wg_boden_holz_b"])
	assert_str(String(bauer.wand_satz("voll")[0])).is_equal("wg_wand_voll")
	bauer.free()


func test_standardtabelle_nennt_die_vertragsdateien() -> void:
	var bauer := GrundrissBauer.new()
	bauer.waehle_module("standard")
	assert_array(bauer.boden_module("pflaster")).contains_exactly(["boden_pflaster_a", "boden_pflaster_b"])
	assert_array(bauer.wand_satz("voll")).contains_exactly(
		["wand_voll", "wand_halb_tuer", "wand_voll_fenster", "pfosten_voll"])
	assert_str(String(bauer.wand_satz("gelaender")[3])).is_empty()
	# Fehlt ein Modul, springt das von Welt 1 ein.
	assert_str(GrundrissBauer.ersatz_name("boden_marmor_b")).is_equal("wg_boden_holz_b")
	assert_str(GrundrissBauer.ersatz_name("wand_sockel_tuer")).is_equal("wg_wand_sockel_tuer")
	bauer.free()


func test_eigene_modultabelle_ueberschreibt_nur_was_sie_nennt() -> void:
	var bauer := GrundrissBauer.new()
	bauer.waehle_module({"boeden": {"holz": ["x_a", "x_b"]}, "waende": {"halb": ["h", "ht", "h", "hp"]}})
	assert_array(bauer.boden_module("holz")).contains_exactly(["x_a", "x_b"])
	assert_array(bauer.boden_module("beton")).contains_exactly(["boden_beton_a", "boden_beton_b"])
	assert_str(String(bauer.wand_satz("halb")[0])).is_equal("h")
	assert_str(String(bauer.wand_satz("voll")[0])).is_equal("wand_voll")
	bauer.free()


func test_varianten_der_einrichtung_kommen_aus_den_daten() -> void:
	var z := {"einrichtung": "einrichtung_x",
		"varianten": {"gesperrt": "_a", "verfuegbar": "_b", "gekauft": "_c"}}
	assert_str(GrundrissBauer.einrichtung_fuer(z, "gesperrt")).is_equal("einrichtung_x_a")
	assert_str(GrundrissBauer.einrichtung_fuer(z, "verfuegbar")).is_equal("einrichtung_x_b")
	assert_str(GrundrissBauer.einrichtung_fuer(z, "gekauft")).is_equal("einrichtung_x_c")
	# Ohne Endung fuer "verfuegbar" gilt die fuer "gesperrt".
	(z["varianten"] as Dictionary).erase("verfuegbar")
	assert_str(GrundrissBauer.einrichtung_fuer(z, "verfuegbar")).is_equal("einrichtung_x_a")
	# Ohne Varianten bleibt die Datei, wie sie ist.
	assert_str(GrundrissBauer.einrichtung_fuer({"einrichtung": "e"}, "gesperrt")).is_equal("e")


func test_welt_1_erzaehlt_das_freie_zimmer_weiter() -> void:
	var welten := _welten()
	var gefunden: bool = false
	for z in welten.zonen(0):
		if not (z as Dictionary).get("varianten", {}).is_empty():
			gefunden = true
			assert_str(GrundrissBauer.einrichtung_fuer(z, "gesperrt")).ends_with("_bewohnt")
			assert_str(GrundrissBauer.einrichtung_fuer(z, "gekauft")).ends_with("_studio")
	assert_bool(gefunden).is_true()


func test_licht_als_vorlage_und_als_dictionary() -> void:
	var welten := _welten()
	# Die Vorlage "warm" gibt es weiter (Welt 1 setzt seit M1 ein eigenes Licht als Dictionary).
	var vorlage := WorldData.new()
	vorlage.welten = [{"id": "v", "zonen": [{"id": "z"}], "licht": "warm"}]
	var warm: Dictionary = vorlage.licht(0)
	assert_str(String(warm["hintergrund"])).is_equal("e9d8bf")
	assert_bool(bool(warm["schatten"])).is_true()
	for i in range(0, welten.anzahl()):
		var l: Dictionary = welten.licht(i)
		for feld in ["hintergrund", "umgebung", "umgebung_energie", "sonne", "sonne_energie", "schatten"]:
			assert_bool(l.has(feld)).override_failure_message("%s: %s" % [welten.id(i), feld]).is_true()
		assert_bool(Color.html_is_valid(String(l["hintergrund"]))).is_true()
	# Ein Dictionary ueberschreibt nur, was es nennt.
	var eigen := WorldData.new()
	eigen.welten = [{"id": "x", "zonen": [{"id": "z"}], "licht": {"sonne_energie": 2.0}}]
	var l2: Dictionary = eigen.licht(0)
	assert_float(float(l2["sonne_energie"])).is_equal(2.0)
	assert_str(String(l2["hintergrund"])).is_equal("e9d8bf")
	# Ohne Grundriss und ohne Angabe: das alte Licht.
	eigen.welten = [{"id": "y"}]
	assert_bool(bool(eigen.licht(0)["schatten"])).is_false()


func test_darsteller_als_liste_und_als_einzelnes_objekt() -> void:
	var welten := _welten()
	assert_int(welten.darsteller(0).size()).is_equal(1)
	assert_int(welten.darsteller(5).size()).is_greater(1)
	var eigen := WorldData.new()
	eigen.welten = [{"id": "x", "figuren": {"darsteller": {"figur": "a"}}}]
	assert_int(eigen.darsteller(0).size()).is_equal(1)
	eigen.welten = [{"id": "x", "figuren": {}}]
	assert_int(eigen.darsteller(0).size()).is_equal(0)


# --- Abschluss und Sondermechaniken -------------------------------------------------

func test_jede_welt_ist_abschliessbar() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		var kern := _kern(i)
		var fertig := {"n": 0}
		kern.bus.world_completed.connect(func() -> void: fertig["n"] += 1)
		_alles_kaufen(kern)
		# Gekauft wurde mit geschenktem Geld -- "verdient" muss man nachtragen.
		kern.welt_verdient = 1.0e30
		kern.tick(TAKT)
		# Ziele einloesen, wie es ein Spieler tut (Welt 1 hat eine Nachricht,
		# die auf ein eingeloestes Ziel wartet).
		for runde in range(12):
			for ziel in kern.ziele.sichtbar():
				kern.loese_ziel_ein(StringName(String(ziel.get("id", ""))))
		assert_bool(kern.welt_abgeschlossen()).override_failure_message(welten.id(i)).is_true()
		assert_float(kern.weltwechsel_fortschritt()).is_equal_approx(1.0, 0.0001)
		assert_int(int(fertig["n"])).override_failure_message(welten.id(i)).is_equal(1)
		assert_int(kern.nachrichten.empfangen().size()).override_failure_message(welten.id(i)) \
			.is_equal(kern.balance.nachrichten.size())
		# Alle Ziele ausser Tipp-Momenten sind erfuellt.
		for ziel in kern.balance.ziele:
			var d: Dictionary = ziel as Dictionary
			if String(d.get("typ", "")) == "momente":
				continue
			assert_bool(GoalSystem.erfuellt(d, kern.messwert)) \
				.override_failure_message("%s: %s" % [welten.id(i), d.get("id", "")]).is_true()


func test_das_limit_blockiert_den_abschluss_nicht() -> void:
	var kern := _kern(1)
	assert_bool(kern.limit_gilt()).is_true()
	_alles_kaufen(kern, false)
	kern.tick(TAKT)
	assert_bool(kern.welt_abgeschlossen()).is_true()
	# Und der Umbau bleibt danach kaufbar.
	assert_bool(kern.kaufe_umbau()).is_true()


func test_umbau_ist_ein_ziel() -> void:
	var kern := _kern(1)
	var ziel := {"typ": "freigeschaltet", "unlock": "unlock_umbau", "wert": 1}
	assert_bool(kern.bedingung_erfuellt(ziel)).is_false()
	kern.kapital = kern.umbau_kosten()
	kern.kaufe_umbau()
	assert_bool(kern.bedingung_erfuellt(ziel)).is_true()


func test_grundeinnahme_laeuft_ohne_die_kette() -> void:
	var kern := _kern(2)
	assert_float(kern.grundeinnahme()).is_equal(0.0)
	kern.kapital = 1.0e30
	kern.kaufe_bereich(&"bereich_3")
	var sonder: StationModel = kern.kette.station(Ids.STATION_SPECIAL)
	assert_bool(sonder.freigeschaltet).is_true()
	var eine: float = kern.grundeinnahme()
	assert_float(eine).is_greater(0.0)
	kern.upgrade_station(Ids.STATION_SPECIAL)
	assert_float(kern.grundeinnahme()).is_greater(eine)
	# Die Kette steht still -- die Stammkunden zahlen weiter.
	for id in Ids.CHAIN:
		kern.kette.station(id).stufe = 0
	var vorher: float = kern.welt_verdient
	for n in range(8):
		kern.tick(TAKT)
	assert_float(kern.welt_verdient - vorher).is_greater(0.0)
	assert_float(kern.station_leistung(Ids.STATION_SPECIAL)).is_equal_approx(kern.grundeinnahme(), 0.001)


func test_im_bestand_zeigt_der_kauf_seine_wirkung_sofort_an() -> void:
	var kern := _kern(4)
	var eng: StringName = kern.kette.bottleneck()
	var jetzt: float = kern.einkommen_pro_sekunde()
	assert_float(kern.einkommen_danach(eng) - jetzt).is_greater(0.0)


func test_im_bestand_wirkt_die_sonderstation() -> void:
	var kern := _kern(4)
	kern.kapital = 1.0e30
	kern.kaufe_bereich(&"bereich_3")
	var vorher: float = kern.einkommen_pro_sekunde()
	kern.upgrade_station_mehrfach(Ids.STATION_SPECIAL, 10)
	assert_float(kern.einkommen_pro_sekunde()).is_greater(vorher)


func test_verlust_ticks_gehen_nie_unter_null() -> void:
	var kern := _kern(5)
	for id in Ids.CHAIN:
		kern.kette.station(id).stufe = 20
	var verluste := {"n": 0}
	kern.bus.throughput_tick.connect(func(_m: float, erloes: float) -> void:
		if erloes < 0.0:
			verluste["n"] += 1)
	kern.kapital = 0.0
	for n in range(400):
		kern.tick(TAKT)
		assert_float(kern.kapital).is_greater_equal(0.0)
	# Ohne Streuung gibt es Verlust-Ticks -- das ist die Mechanik.
	assert_int(int(verluste["n"])).is_greater(0)


func test_ein_verlust_ist_klein_und_genau_der_abzug() -> void:
	var kern := _kern(5)
	for id in Ids.CHAIN:
		kern.kette.station(id).stufe = 20
	kern.kapital = 1.66e7
	var protokoll := {"groesster": 0.0, "n": 0, "passt": true, "vorher": kern.kapital}
	kern.bus.loss_tick.connect(func(betrag: float) -> void:
		protokoll["n"] += 1
		protokoll["groesster"] = maxf(float(protokoll["groesster"]), betrag))
	kern.bus.money_changed.connect(func(neu: float, differenz: float) -> void:
		# Gemeldet wird genau, was sich am Kapital geaendert hat.
		if absf((neu - float(protokoll["vorher"])) - differenz) > maxf(absf(differenz) * 1.0e-6, 0.01):
			protokoll["passt"] = false
		protokoll["vorher"] = neu)
	for n in range(400):
		kern.tick(TAKT)
	assert_int(int(protokoll["n"])).is_greater(0)
	assert_bool(bool(protokoll["passt"])).is_true()
	# Ein Tick dauert 0,25 s; der Ausschlag liegt unter 1,3 -- ein Verlust ist
	# also hoechstens eine halbe Sekunde Einkommen, nie Milliarden.
	assert_float(float(protokoll["groesster"])).is_less_equal(kern.einkommen_pro_sekunde() * 0.5)


func test_kaeufe_sind_keine_verluste() -> void:
	var kern := _kern(5)
	var verluste := {"n": 0}
	kern.bus.loss_tick.connect(func(_b: float) -> void: verluste["n"] += 1)
	kern.kapital = 1.0e12
	kern.kaufe_bereich(&"bereich_1")
	kern.upgrade_station_mehrfach(Ids.STATION_INTAKE, 20)
	kern.kaufe_ausstattung(Ids.STATION_INTAKE, &"ausstattung_1")
	assert_int(int(verluste["n"])).is_equal(0)


func test_mission_aus_mehreren_teilen() -> void:
	var kern := _kern(5)
	var mission := {"typ": "alle", "wert": 1, "bedingungen": [
		{"typ": "bereich", "bereich": "bereich_2", "wert": 1},
		{"typ": "ausstattung_station", "station": "station_processing", "wert": 3}]}
	assert_float(kern.messwert(mission)).is_equal(0.0)
	kern.kapital = 1.0e30
	kern.kaufe_bereich(&"bereich_2")
	assert_float(kern.messwert(mission)).is_equal_approx(0.5, 0.001)
	assert_bool(kern.bedingung_erfuellt(mission)).is_false()
	kern.upgrade_station_mehrfach(Ids.STATION_PROCESSING, 30)
	for platz in [&"ausstattung_1", &"ausstattung_2", &"ausstattung_3"]:
		kern.kaufe_ausstattung(Ids.STATION_PROCESSING, platz)
	assert_float(kern.messwert({"typ": "ausstattung_station", "station": "station_processing"})).is_equal(3.0)
	assert_bool(kern.bedingung_erfuellt(mission)).is_true()


func test_alle_als_bedingung_wird_geprueft() -> void:
	var roh: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/balance/kapital.json")) as Dictionary
	(roh["ziele"] as Array)[0] = {"id": "ziel_01", "typ": "alle", "bedingungen": [{"typ": "gibtsnicht"}]}
	var b := BalanceData.aus_text(JSON.stringify(roh))
	assert_bool(b.validieren()).is_false()
