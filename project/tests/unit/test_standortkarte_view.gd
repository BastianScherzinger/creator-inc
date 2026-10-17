## K7 Standortkarte: sechs Standorte, Zustaende, Einkommensfaktor, Hinweise.
## Ohne SceneTree-Frames: Die Ansicht wird gebaut, aber nie in den Baum gehaengt.
extends GdUnitTestSuite


func _kern(index: int) -> GameCore:
	var welten: WorldData = WorldData.laden()
	return GameCore.new(BalanceData.fuer_welt(welten.id(index)), index)


func _karte(index: int) -> StandortkarteView:
	var ansicht: StandortkarteView = StandortkarteView.oeffnen(null, _kern(index), {})
	return ansicht


func _frei(ansicht: StandortkarteView) -> void:
	var ebene: Node = ansicht.get_parent()
	ebene.free()


func test_zustand_vor_auf_nach_der_aktuellen_welt() -> void:
	assert_int(StandortkarteView.zustand(0, 2)).is_equal(StandortkarteView.Zustand.GESCHAFFT)
	assert_int(StandortkarteView.zustand(2, 2)).is_equal(StandortkarteView.Zustand.AKTUELL)
	assert_int(StandortkarteView.zustand(5, 2)).is_equal(StandortkarteView.Zustand.GESPERRT)


func test_einkommen_faktor_entspricht_dem_kern() -> void:
	var welten: WorldData = WorldData.laden()
	for i in range(welten.anzahl()):
		var kern: GameCore = _kern(i)
		var ohne_rest: float = kern.welt_faktor() / (kern.erfahrungsfaktor() * kern.erfolge_faktor())
		assert_float(StandortkarteView.einkommen_faktor(welten, i)).is_equal_approx(ohne_rest, ohne_rest * 1.0e-6)
	assert_float(StandortkarteView.einkommen_faktor(welten, 0)).is_equal(1.0)


func test_faktor_text_ganz_mit_tausenderpunkt() -> void:
	assert_str(StandortkarteView.faktor_text(1.0)).is_equal("×1")
	assert_str(StandortkarteView.faktor_text(10.0)).is_equal("×10")
	assert_str(StandortkarteView.faktor_text(1000.0)).is_equal("×1.000")
	assert_str(StandortkarteView.faktor_text(100000.0)).is_equal("×100.000")


func test_karte_hat_alle_standorte_in_reihenfolge_von_unten_nach_oben() -> void:
	var ansicht: StandortkarteView = _karte(2)
	assert_int(ansicht.anzahl()).is_equal(WorldData.laden().anzahl())
	ansicht.ordne(720.0)
	for i in range(ansicht.anzahl() - 1):
		# Der erste Standort steht unten: groesseres y als der naechste.
		assert_float(ansicht.standort(i).position.y).is_greater(ansicht.standort(i + 1).position.y)
	_frei(ansicht)


func test_banner_zeigt_den_weltnamen_aus_dem_thema() -> void:
	var ansicht: StandortkarteView = _karte(0)
	var name: Label = ansicht.standort(1).find_child("Name", true, false) as Label
	assert_object(name).is_not_null()
	assert_str(name.text).is_equal(ThemeData.laden(WorldData.laden().id(1)).welt_name.to_upper())
	var faktor: Label = ansicht.standort(1).find_child("Faktor", true, false) as Label
	assert_str(faktor.text).is_equal(StandortkarteView.faktor_text(StandortkarteView.einkommen_faktor(WorldData.laden(), 1)))
	_frei(ansicht)


func test_zustaende_sind_sichtbar() -> void:
	var ansicht: StandortkarteView = _karte(2)
	assert_object(ansicht.standort(0).find_child("Siegel", true, false)).is_not_null()
	assert_object(ansicht.standort(2).find_child("Hier", true, false)).is_not_null()
	var gesperrt: Label = ansicht.standort(4).find_child("Gesperrt", true, false) as Label
	assert_object(gesperrt).is_not_null()
	assert_str(gesperrt.text).contains(ansicht.welt_name(2))
	assert_object(ansicht.standort(4).find_child("Siegel", true, false)).is_null()
	_frei(ansicht)


func test_tipp_zeigt_hinweis_und_wechselt_nie_die_welt() -> void:
	var ansicht: StandortkarteView = _karte(2)
	ansicht.auf_tipp(0)
	assert_str(ansicht.hinweis_text()).contains(ansicht.welt_name(0))
	ansicht.auf_tipp(5)
	assert_str(ansicht.hinweis_text()).contains(ansicht.welt_name(2))
	ansicht.auf_tipp(2)
	assert_str(ansicht.hinweis_text()).is_equal(UiText.t("standort_tipp_hier") % ansicht.welt_name(2))
	assert_int(ansicht.kern.welt_index).is_equal(2)
	_frei(ansicht)


func test_scroll_ziel_bleibt_im_bereich() -> void:
	var ansicht: StandortkarteView = _karte(5)
	ansicht.ordne(720.0)
	for i in range(ansicht.anzahl()):
		var ziel: float = ansicht.scroll_ziel(i, 1280.0)
		assert_float(ziel).is_greater_equal(0.0)
		assert_float(ziel).is_less_equal(maxf(0.0, ansicht._inhalt.custom_minimum_size.y - 1280.0))
	# Der oberste Standort steht ganz oben: Scrollwert 0.
	assert_float(ansicht.scroll_ziel(ansicht.anzahl() - 1, 1280.0)).is_equal(0.0)
	_frei(ansicht)


func test_alle_texte_stehen_in_i18n() -> void:
	for schluessel in ["standort_titel", "standort_einkommen", "standort_faktor", "standort_geschafft",
			"standort_hier", "standort_gesperrt", "standort_tipp_hier", "standort_tipp_geschafft",
			"standort_tipp_gesperrt"]:
		assert_bool(UiText.hat(String(schluessel))).is_true()


func test_standortbilder_liegen_fuer_jede_welt_vor() -> void:
	var welten: WorldData = WorldData.laden()
	var muster: String = String(StandortkarteView.konfig().get("bild_pfad", ""))
	for i in range(welten.anzahl()):
		assert_bool(ResourceLoader.exists(muster % welten.id(i))).is_true()
