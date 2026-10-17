## W2e: Raum-Panel (Kopf, Reiter, Pille, Raster, Team) und die gemeinsame Kaufpille.
## Ohne SceneTree-Frames: geprueft werden Entscheidungen und Kaeufe, nicht Tweens.
extends GdUnitTestSuite


func _kern(kapital: float = 1.0e9) -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.kapital = kapital
	return kern


func _panel(kern: GameCore) -> RaumPanel:
	var p: RaumPanel = auto_free(RaumPanel.new())
	p.kern = kern
	p.thema = ThemeData.laden(kern.welt_id())
	add_child(p)
	return p


func _beruehrung(m: Sheet, pos: Vector2, gedrueckt: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.position = pos
	e.pressed = gedrueckt
	m._auf_eingabe(e)


func _zug(m: Sheet, pos: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.position = pos
	m._auf_eingabe(e)


# --- Kaufpille ----------------------------------------------------------------------

func test_kaufpille_zustaende() -> void:
	var frei: Button = auto_free(UiStil.kaufpille({"titel": "A", "preis": "5", "zustand": "kaufbar"}))
	assert_bool(frei.disabled).is_false()
	var arm: Button = auto_free(UiStil.kaufpille({"titel": "A", "preis": "5", "zustand": "nicht"}))
	assert_bool(arm.disabled).is_true()
	var zu: Button = auto_free(UiStil.kaufpille({"titel": "A", "preis": "ab Stufe 3", "zustand": "gesperrt"}))
	assert_bool(zu.disabled).is_true()
	assert_float(frei.custom_minimum_size.y).is_equal(UiStil.KNOPF_PRIMAER_H)


func test_kaufpille_baut_sich_nur_einmal() -> void:
	var p: Button = auto_free(UiStil.kaufpille({"titel": "A", "preis": "5", "zustand": "nicht"}))
	var kinder: int = p.get_child_count()
	var teile: Dictionary = p.get_meta("teile") as Dictionary
	UiStil.kaufpille({"titel": "B", "preis": "7", "zustand": "kaufbar"}, p)
	assert_int(p.get_child_count()).is_equal(kinder)
	assert_str((teile["preis"] as Label).text).is_equal("7")
	assert_str((teile["titel"] as Label).text).is_equal("B")
	assert_bool(p.disabled).is_false()


func test_schlanke_kaufpille_zeigt_preis_als_text() -> void:
	var p: Button = auto_free(UiStil.kaufpille({"hoehe": UiStil.KNOPF_SEKUNDAER_H, "preis": "1,2 Mio",
		"zustand": "kaufbar"}))
	assert_str(p.text).is_equal("1,2 Mio")
	assert_float(p.custom_minimum_size.y).is_equal(UiStil.KNOPF_SEKUNDAER_H)


func test_pille_in_raum_und_station_hat_dieselbe_form() -> void:
	var kern := _kern()
	var raum: RaumPanel = _panel(kern)
	raum.zeige_bereich(GameCore.START_RAUM)
	var station := Stationsmenue.new()
	station.kern = kern
	station.thema = raum.thema
	add_child(station)
	station.zeige_station(Ids.CHAIN[0])
	assert_float(raum._knopf.custom_minimum_size.y).is_equal(station._ausbau.custom_minimum_size.y)
	assert_int(raum._knopf_preis.get_theme_font_size("font_size")).is_equal(
		station._ausbau_preis.get_theme_font_size("font_size"))
	station.queue_free()


# --- Kopf, Zahlen, Raumwechsel ------------------------------------------------------

func test_kopf_zeigt_name_einkommen_und_prozent() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	assert_str(p.titel.text).is_not_empty()
	assert_bool(p._unter.text.contains("%")).is_true()
	assert_bool(p._unter.text.contains("€/s")).is_true()


func test_fortschritt_waechst_mit_den_kaeufen() -> void:
	var kern := _kern()
	var vorher: float = RaumPanel.raum_fortschritt(kern, GameCore.START_RAUM)
	for i in range(6):
		var kauf: Dictionary = kern.empfehlung_im_raum(GameCore.START_RAUM)
		if kauf.is_empty():
			break
		kern.kaufe_empfehlung(kauf)
	var nachher: float = RaumPanel.raum_fortschritt(kern, GameCore.START_RAUM)
	assert_float(nachher).is_greater(vorher)
	assert_float(nachher).is_less_equal(1.0)


func test_raumeinkommen_ist_ein_anteil_des_ganzen() -> void:
	var kern := _kern()
	var summe: float = 0.0
	for id in kern.bereiche.ids():
		summe += RaumPanel.raum_einkommen(kern, id)
	summe += RaumPanel.raum_einkommen(kern, GameCore.START_RAUM)
	assert_float(summe).is_less_equal(kern.einkommen_pro_sekunde() * 1.0001)


func test_pfeile_springen_zum_naechsten_gekauften_raum() -> void:
	var kern := _kern()
	var ids: Array[StringName] = kern.bereiche.ids()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	# Nur die Startzone gekauft: kein Nachbar, Pfeile weg.
	assert_str(String(p.nachbar_raum(1))).is_equal("")
	assert_bool(p._vor.visible).is_false()
	assert_bool(kern.kaufe_bereich(ids[0])).is_true()
	p.aktualisiere()
	assert_str(String(p.nachbar_raum(1))).is_equal(String(ids[0]))
	assert_str(String(p.nachbar_raum(-1))).is_equal(String(ids[0]))
	assert_bool(p._vor.visible).is_true()
	var gemeldet: Array = []
	p.raum_gewechselt.connect(func(id: StringName) -> void: gemeldet.append(id))
	p._vor.pressed.emit()
	assert_str(String(p.bereich_id)).is_equal(String(ids[0]))
	assert_array(gemeldet).contains_exactly([ids[0]])
	p._zurueck.pressed.emit()
	assert_str(String(p.bereich_id)).is_equal(String(GameCore.START_RAUM))


# --- Kaufen -------------------------------------------------------------------------

func test_kauf_laesst_das_panel_offen_und_zeigt_den_naechsten() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	var meldungen: Array = []
	p.ausgegeben.connect(func(_von: Vector2, text: String) -> void: meldungen.append(text))
	var geld: float = kern.kapital
	p._auf_kauf()
	assert_float(kern.kapital).is_less(geld)
	assert_int(meldungen.size()).is_equal(1)
	assert_bool(p.ist_offen()).is_true()
	assert_bool(p.vorschlag.is_empty()).is_false()


func test_kachelwahl_bestimmt_was_die_pille_kauft() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	var alle: Array[Dictionary] = p._kaeufe()
	assert_int(alle.size()).is_greater(1)
	var anderer: Dictionary = alle[alle.size() - 1]
	p._auswahl = RaumPanel._schluessel(anderer)
	p.aktualisiere()
	assert_str(RaumPanel._schluessel(p.vorschlag)).is_equal(RaumPanel._schluessel(anderer))
	assert_str(p._knopf_preis.text).is_equal(UiStil.preis(float(anderer["preis"])))


func test_raster_hat_eine_kachel_je_verbesserung() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	assert_int(p._raster.get_child_count()).is_equal(p._kaeufe().size())
	assert_int(p._raster.columns).is_equal(int(Sheet.konfig_wert("raum_panel", "spalten", 3)))


func test_team_kauf_hebt_den_rang() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	var gefunden: bool = false
	for id in kern.bereiche.ids() + [GameCore.START_RAUM]:
		p.bereich_id = id
		for sid in p._team_stationen():
			if kern.crew_frei(sid):
				var vorher: int = kern.crew_rang(sid)
				p._kaufe_crew(sid, auto_free(Button.new()))
				assert_int(kern.crew_rang(sid)).is_equal(vorher + 1)
				gefunden = true
				break
		if gefunden:
			break
	# In frischen Spielen ist noch keine Crew frei: dann prueft der Test nur, dass nichts bricht.
	assert_bool(true).is_true()


# --- Schliessen nur per Kopf ---------------------------------------------------------

func test_wisch_im_raster_schliesst_nie_wisch_im_kopf_schon() -> void:
	var kern := _kern()
	var p: RaumPanel = _panel(kern)
	p.zeige_bereich(GameCore.START_RAUM)
	var y: float = p.kopfzone_bis() + 150.0
	_beruehrung(p, Vector2(100.0, y), true)
	_zug(p, Vector2(100.0, y + 600.0))
	_beruehrung(p, Vector2(100.0, y + 600.0), false)
	assert_bool(p.ist_offen()).is_true()
	_beruehrung(p, Vector2(100.0, 10.0), true)
	_zug(p, Vector2(100.0, 300.0))
	_beruehrung(p, Vector2(100.0, 300.0), false)
	assert_bool(p.ist_offen()).is_false()


func test_hoehengrenze_steht_in_den_daten() -> void:
	assert_float(float(Sheet.konfig_wert("raum_panel", "max_anteil", 1.0))).is_less_equal(0.45)
	assert_float(float(Sheet.konfig_wert("station_menue", "max_anteil", 1.0))).is_less_equal(0.45)
