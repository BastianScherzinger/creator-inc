## K6 Paket 2d: Unterleiste im Stil von Idle Bank Tycoon, Kopfleiste mit zwei Zahlen und
## Rang-Stern, Tagesgeschenk als Rand-Symbol statt Fenster beim Start.
extends GdUnitTestSuite


func _leiste() -> Menueleiste:
	var leiste: Menueleiste = auto_free(Menueleiste.new())
	add_child(leiste)
	return leiste


# --- Unterleiste ------------------------------------------------------------------

func test_vier_knoepfe_und_die_mitte() -> void:
	assert_int(Menueleiste.PUNKTE.size()).is_equal(5)
	assert_that(Menueleiste.PUNKTE[2]).is_equal(&"schub")


func test_zu_beginn_ist_kein_knopf_da() -> void:
	var leiste: Menueleiste = _leiste()
	for punkt in Menueleiste.PUNKTE:
		leiste.setze_frei(punkt, false)
	assert_int(leiste.anzahl_sichtbar()).is_equal(0)
	assert_bool(leiste.visible).is_false()


func test_jeder_platz_hat_ein_symbol_das_es_gibt() -> void:
	for punkt in Menueleiste.PUNKTE:
		var name: String = String(Menueleiste.SYMBOLE[punkt])
		assert_bool(ResourceLoader.exists(UiStil.symbol_pfad(name))).override_failure_message(name).is_true()


func test_boost_mitte_erscheint_erst_mit_der_freischaltung() -> void:
	var leiste: Menueleiste = _leiste()
	for punkt in Menueleiste.PUNKTE:
		leiste.setze_frei(punkt, false)
	assert_bool(leiste.ist_frei(&"schub")).is_false()
	assert_bool(leiste.setze_frei(&"schub", true)).is_true()
	assert_bool(leiste.ist_frei(&"schub")).is_true()
	assert_bool(leiste.visible).is_true()


func test_der_faktor_steht_im_kreis() -> void:
	var leiste: Menueleiste = _leiste()
	leiste.setze_text(&"schub", "▶ ×1,5 · 30 Min")
	assert_str(leiste._mitte_faktor.text).is_equal("×1,5")
	leiste.setze_text(&"schub", "×2 · 12:30")
	assert_str(leiste._mitte_faktor.text).is_equal("×2")
	# Ohne Faktor im Text bleibt der letzte stehen (Pause-Anzeige).
	leiste.setze_text(&"schub", "Pause 4:10")
	assert_str(leiste._mitte_faktor.text).is_equal("×2")


func test_abzeichen_zaehlt_und_verschwindet_bei_null() -> void:
	var leiste: Menueleiste = _leiste()
	leiste.setze_abzeichen(&"handy", 3)
	var punkt: PanelContainer = leiste._abzeichen[&"handy"][0]
	assert_bool(punkt.visible).is_true()
	assert_str((leiste._abzeichen[&"handy"][1] as Label).text).is_equal("3")
	leiste.setze_abzeichen(&"handy", 150)
	assert_str((leiste._abzeichen[&"handy"][1] as Label).text).is_equal("99+")
	leiste.setze_abzeichen(&"handy", 0)
	assert_bool(punkt.visible).is_false()


func test_bereiter_boost_ist_gruen_und_hat_hof() -> void:
	var leiste: Menueleiste = _leiste()
	leiste.setze_schub_zustand(&"aus")
	assert_bool(leiste._glut.visible).is_false()
	leiste.setze_schub_zustand(&"bereit")
	assert_bool(leiste._glut.visible).is_true()
	assert_bool(leiste._mitte_video.visible).is_true()
	leiste.setze_schub_zustand(&"laeuft")
	assert_bool(leiste._glut.visible).is_false()


func test_jeder_platz_ist_mindestens_48dp_hoch_und_breit() -> void:
	# 48 dp = 96 logische Pixel bei 720 Breite auf 360 dp.
	assert_float(Menueleiste.PLATZ_BREITE).is_greater_equal(96.0)
	assert_float(Menueleiste.HOEHE).is_greater_equal(96.0)


# --- Kopfleiste -------------------------------------------------------------------

func test_kopfleiste_rang_stern_zeigt_rang_und_balken() -> void:
	var kopf: Kopfleiste = auto_free(Kopfleiste.new())
	add_child(kopf)
	kopf.setze_rang(4, 0.5)
	assert_bool(kopf._stern_feld.visible).is_true()
	assert_str(kopf._stern_zahl.text).is_equal("4")
	assert_float(kopf._stern_balken.value).is_equal(0.5)


func test_kopfleiste_ohne_rang_chip() -> void:
	var kopf: Kopfleiste = auto_free(Kopfleiste.new())
	add_child(kopf)
	# Die alten Aufrufe laufen ins Leere, nichts bricht und nichts erscheint.
	kopf.setze_level(7, "Creator")
	kopf.zeige_rang(true)
	assert_bool(kopf._stern_feld.visible).is_false()


func test_kopfleiste_geld_wird_nie_aufgerundet() -> void:
	assert_str(Kopfleiste._geld_text(999.9)).is_not_equal("1.000 €")
	assert_str(Kopfleiste._geld_text(0.99)).is_not_equal("1 €")


# --- Tagesgeschenk ----------------------------------------------------------------

func test_geschenk_symbol_am_rand_ohne_fenster() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var symbol: GeschenkView.RandSymbol = GeschenkView.biete_am_rand(self, kern)
	# Ein frischer Kern hat heute ein Geschenk: das Symbol steht da, eine Karte nicht.
	assert_bool(symbol.visible).is_equal(not kern.geschenk_bereit().is_empty())
	assert_bool(symbol._karte == null).is_true()
	symbol.get_parent().queue_free()


func test_geschenk_symbol_ohne_geschenk_ist_unsichtbar() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	if not kern.geschenk_bereit().is_empty():
		kern.geschenk_abholen()
	var symbol: GeschenkView.RandSymbol = GeschenkView.biete_am_rand(self, kern)
	assert_bool(symbol.visible).is_false()
	symbol.get_parent().queue_free()


func test_geschenk_karte_schliesst_ohne_abholen() -> void:
	var ansicht: GeschenkView = auto_free(GeschenkView.new())
	add_child(ansicht)
	ansicht.zeige({"tag": 2, "serie_max": 7, "betrag": 123.0, "faktor": 1.2, "tage": [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5]})
	var zaehler: Array[int] = [0]
	ansicht.geschlossen.connect(func() -> void: zaehler[0] += 1)
	ansicht.schliesse()
	assert_int(zaehler[0]).is_equal(1)
