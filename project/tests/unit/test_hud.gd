## Hud: nie zwei Menues zugleich, Ziele-Leiste, Ziel-Kette eines Raums.
extends GdUnitTestSuite


func _hud() -> Hud:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	var audio: AudioDirector = auto_free(AudioDirector.new())
	add_child(audio)
	var hud: Hud = auto_free(Hud.new())
	add_child(hud)
	hud.aufbauen(kern, thema, audio, auto_free(AdServiceStub.new()))
	return hud


func test_nie_zwei_menues_zugleich() -> void:
	var hud: Hud = _hud()
	hud._oeffne(hud.zielemenue)
	assert_bool(hud.zielemenue.ist_offen()).is_true()
	hud._oeffne(hud.handymenue)
	assert_bool(hud.handymenue.ist_offen()).is_true()
	# Das alte Menue ist SOFORT weg -- kein Geist, der ausblendet.
	assert_bool(hud.zielemenue.ist_offen()).is_false()
	assert_bool(hud.zielemenue.visible).is_false()
	hud.zeige_bereich(&"bereich_1")
	assert_bool(hud.schnellkauf.ist_offen()).is_true()
	assert_bool(hud.handymenue.visible).is_false()


func test_ziele_leiste_bleibt_bei_offenem_menue_sichtbar() -> void:
	var hud: Hud = _hud()
	hud.aktualisiere()
	hud._oeffne(hud.ausbaumenue)
	hud.aktualisiere()
	assert_bool(hud._zielkarte.visible).is_true()


func test_kette_eines_raums_hat_hoechstens_drei_glieder_und_ein_aktuelles() -> void:
	var hud: Hud = _hud()
	var kette: Array[Dictionary] = Menues.kette_anzeige(hud.kern, &"bereich_1")
	assert_int(kette.size()).is_between(1, 3)
	var aktuelle: int = 0
	for e in kette:
		if String(e["zustand"]) == "jetzt":
			aktuelle += 1
	assert_int(aktuelle).is_equal(1)


func test_schliessen_sofort_laesst_kein_halbes_menue_zurueck() -> void:
	var sheet: Sheet = auto_free(Sheet.new())
	add_child(sheet)
	sheet.oeffnen()
	sheet.schliessen_sofort()
	assert_bool(sheet.ist_offen()).is_false()
	assert_bool(sheet.visible).is_false()
	assert_float(sheet.karte.modulate.a).is_equal(1.0)


## --- P-Paket (Handy-Befunde 15.10.) -------------------------------------------------

func _alle_knoepfe(wurzel: Node, gefunden: Array[Button] = []) -> Array[Button]:
	for kind in wurzel.get_children():
		if kind is Button:
			gefunden.append(kind as Button)
		_alle_knoepfe(kind, gefunden)
	return gefunden


func test_ausbau_liste_bezahlbar_ist_limette_sonst_gedaempft() -> void:
	var hud: Hud = _hud()
	hud.kern.kapital = 1.0e12
	hud._oeffne(hud.ausbaumenue)
	hud.ausbaumenue.aktualisiere()
	var limetten: int = 0
	for k in _alle_knoepfe(hud.ausbaumenue._liste):
		if k.disabled:
			continue
		var stil: StickerBox = k.get_theme_stylebox("normal") as StickerBox
		assert_object(stil).is_not_null()
		assert_bool(stil.flaeche.bg_color == UiStil.KAUFEN).is_true()
		limetten += 1
	assert_int(limetten).is_greater(0)
	hud.kern.kapital = 0.0
	hud.ausbaumenue.aktualisiere()
	for k in _alle_knoepfe(hud.ausbaumenue._liste):
		if k.disabled:
			var aus: StickerBox = k.get_theme_stylebox("normal") as StickerBox
			assert_bool(aus.flaeche.bg_color == UiStil.KAUFEN).is_false()


func test_saft_haelt_banner_und_zahlen_waehrend_eines_moments_zurueck() -> void:
	var saft: Saft = auto_free(Saft.new())
	add_child(saft)
	saft.pausiert = true
	saft.betrag(Vector2(200.0, 400.0), "+1,0")
	saft.chat("Mira", "Hallo", Color.WHITE)
	assert_int(saft.get_child_count()).is_equal(0)
	saft.pausiert = false
	# Das wartende Banner kommt nach dem Moment dran.
	assert_int(saft.get_child_count()).is_equal(1)


func test_raum_moment_hat_genau_einen_knopf_und_ein_band() -> void:
	var ebene: Control = auto_free(Control.new())
	add_child(ebene)
	var ansicht: MomentView = MomentView.zeige_moment(ebene, {"art": "raum", "betrag": 0.0, "figur": "mo",
		"titel": "Gekauft: Der Flur", "text_gross": "Upload", "band": "Neu",
		"bild": "res://assets/ui/zimmer/station_intake.png"}, ThemeData.laden("zimmer"))
	assert_int(_alle_knoepfe(ansicht).size()).is_equal(1)
	assert_object(ansicht._strahlen).is_not_null()


func test_tutorialziel_im_offenen_raum_panel_ist_dessen_hauptknopf() -> void:
	var hud: Hud = _hud()
	hud.zeige_bereich(&"bereich_1")
	assert_object(hud.control_fuer("bereich_1")).is_same(hud.schnellkauf._knopf)
	assert_object(hud.control_fuer("bereich_2")).is_null()


func test_raum_panel_zeigt_den_erklaersatz_nicht_zusaetzlich() -> void:
	var hud: Hud = _hud()
	hud.zeige_bereich(&"bereich_1")
	# K6 Welle 2: Raeume oeffnen nur noch das Raum-Panel, die alte Raumliste bleibt zu.
	assert_bool(hud.bereichsmenue.ist_offen()).is_false()
	assert_bool(hud.schnellkauf.ist_offen()).is_true()


func test_tutorialkarte_aus_nimmt_keinen_platz() -> void:
	var ansicht: TutorialView = auto_free(TutorialView.new())
	add_child(ansicht)
	ansicht.setze_karte_aus(true)
	assert_float(ansicht.kartenhoehe()).is_equal(0.0)


func test_levelup_moment_zaehlt_level_hoch_und_nennt_nutzen() -> void:
	var ansicht: MomentView = auto_free(MomentView.new())
	add_child(ansicht)
	ansicht.zeige({"art": "levelup", "zahl": 12, "betrag": 0.0, "zaehl_von": 11, "zaehl_bis": 12,
		"vorlage": UiText.t("levelup_zahl"), "untertitel": UiText.t("levelup_nutzen") % [13, 30]},
		ThemeData.laden("zimmer"))
	# Start: die alte Stufe, mit Wort davor -- nie eine nackte Zahl.
	assert_str(ansicht._zahl.text).is_equal("Rang 11")
	assert_bool(ansicht._zahl.text.begins_with("Rang")).is_true()


func test_kopfleiste_nennt_den_spielerrang() -> void:
	assert_str(UiText.t("rang") % 3).is_equal("Rang 3")
	assert_bool(UiText.t("rang").contains("Lv")).is_false()
	# Die Stations-Badges behalten "Lv".
	assert_str(UiText.t("lv") % 3).is_equal("Lv 3")


func test_weltwechsel_erkennt_die_figur_im_text() -> void:
	assert_str(WeltwechselView.figur_im_text("mit Roman")).is_equal("roman")
	assert_str(WeltwechselView.figur_im_text("mit Selin und allen")).is_equal("selin")
	assert_str(WeltwechselView.figur_im_text("")).is_equal("")
