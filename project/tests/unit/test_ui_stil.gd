## Prueft das Design-System "Sticker-Pop" (docs/NACHT_PLAN.md 3).
##
## Die Farben selbst sind Geschmack. Pruefbar ist, ob sie ihre Regeln
## einhalten: jede Welt hat einen gueltigen Akzent, Text darauf ist lesbar,
## Nebentext hat genug Kontrast, und Weltwechsel setzt den Akzent wirklich um.
extends GdUnitTestSuite

const WELTEN: Array[String] = ["zimmer", "auftrag", "webseiten", "buero", "produkt", "kapital"]
## Grosse, fette Schrift (Titelstreifen) darf 3 : 1 haben (WCAG AA gross).
const KONTRAST_GROSS: float = 3.0
const KONTRAST_TEXT: float = 4.5


func after_test() -> void:
	UiStil.setze_welt(null, null)


func test_jede_welt_hat_einen_gueltigen_akzent() -> void:
	for welt in WELTEN:
		var thema := ThemeData.laden(welt)
		assert_object(thema).is_not_null()
		var hex: String = thema.stil("akzent")
		assert_bool(Color.html_is_valid(hex)).override_failure_message("Akzent fehlt: " + welt).is_true()
		assert_bool(Color.html_is_valid(thema.stil("akzent_text"))).is_true()


func test_text_auf_dem_akzent_ist_lesbar() -> void:
	for welt in WELTEN:
		var thema := ThemeData.laden(welt)
		var grund: Color = UiStil.akzent_von(thema)
		var schrift: Color = UiStil.akzent_text_von(thema)
		assert_float(UiStil.kontrast(grund, schrift)) \
			.override_failure_message("Akzenttext zu schwach in " + welt) \
			.is_greater_equal(KONTRAST_GROSS)


func test_die_akzente_der_welten_unterscheiden_sich() -> void:
	var gesehen: Dictionary = {}
	for welt in WELTEN:
		var farbe: String = UiStil.akzent_von(ThemeData.laden(welt)).to_html(false)
		assert_bool(gesehen.has(farbe)).override_failure_message("Akzent doppelt: " + welt).is_false()
		gesehen[farbe] = true


func test_nebentext_und_kaufschrift_haben_genug_kontrast() -> void:
	assert_float(UiStil.kontrast(UiStil.PAPIER, UiStil.TINTE_2)).is_greater_equal(KONTRAST_TEXT)
	assert_float(UiStil.kontrast(UiStil.PAPIER_2, UiStil.TINTE_2)).is_greater_equal(KONTRAST_TEXT)
	assert_float(UiStil.kontrast(UiStil.PAPIER, UiStil.PLUS_TEXT)).is_greater_equal(KONTRAST_TEXT)
	assert_float(UiStil.kontrast(UiStil.KAUFEN, UiStil.TINTE)).is_greater_equal(KONTRAST_TEXT)
	# Auf Limette steht immer Tinte, nie Weiss.
	assert_that(UiStil.text_auf(UiStil.KAUFEN)).is_equal(UiStil.TINTE)


func test_setze_welt_wechselt_den_akzent() -> void:
	var erste := ThemeData.laden("zimmer")
	var zweite := ThemeData.laden("auftrag")
	UiStil.setze_welt(erste, zweite)
	assert_that(UiStil.akzent()).is_equal(UiStil.akzent_von(erste))
	assert_object(UiStil.naechstes_thema()).is_same(zweite)
	UiStil.setze_welt(zweite, null)
	assert_that(UiStil.akzent()).is_equal(UiStil.akzent_von(zweite))
	assert_that(UiStil.akzent()).is_not_equal(UiStil.akzent_von(erste))


func test_absender_ohne_eigene_farbe_bekommt_den_akzent() -> void:
	var thema := ThemeData.laden("zimmer")
	assert_that(UiStil.absender_farbe(thema, "niemand_bekanntes")).is_equal(UiStil.akzent_von(thema))


func test_kaputte_farbe_faellt_auf_ersatz_zurueck() -> void:
	assert_that(UiStil.farbe("", UiStil.GOLD)).is_equal(UiStil.GOLD)
	assert_that(UiStil.farbe("kein-hex", UiStil.GOLD)).is_equal(UiStil.GOLD)
	assert_that(UiStil.farbe("#FF4D3D", UiStil.GOLD)).is_equal(Color("ff4d3d"))


func test_knopfstil_gedrueckt_ohne_schatten_und_tiefer() -> void:
	var stile: Dictionary = UiStil.knopf_stile(UiStil.KAUFEN)
	var normal: StickerBox = stile["normal"] as StickerBox
	var gedrueckt: StickerBox = stile["pressed"] as StickerBox
	assert_float(normal.druck).is_equal(0.0)
	assert_float(gedrueckt.druck).is_equal(1.0)
	assert_float(gedrueckt.content_margin_top - normal.content_margin_top).is_equal(UiStil.EINDRUCK_Y)
	assert_float(normal.schatten_y).is_equal(UiStil.SCHATTEN_Y)


func test_karten_sind_hoechstens_achtzehn_rund() -> void:
	var box: StickerBox = UiStil.karte(UiStil.PAPIER, 34, 4, 30.0)
	assert_int(box.flaeche.corner_radius_top_left).is_equal(UiStil.RADIUS_KARTE)
	assert_int(box.flaeche.border_width_top).is_equal(UiStil.KONTUR)


func test_zahlen_bleiben_deutsch() -> void:
	assert_str(UiStil.zahl(12480.0)).is_equal("12.480")
	assert_str(UiStil.zahl(5573127.0)).is_equal("5,5 Mio")
	assert_str(UiStil.zahl(3.5)).is_equal("3,5")


# --- Paket B: Faktor-Text, Portraits, Haptik --------------------------------------

func test_faktor_text_ist_menschenlesbar() -> void:
	assert_str(Stationsmenue.faktor_text(1.5)).is_equal("1,5")
	assert_str(Stationsmenue.faktor_text(2.0)).is_equal("2")
	assert_str(Stationsmenue.faktor_text(1.15)).is_equal("1,15")


func test_avatar_ohne_portrait_zeigt_das_handy_symbol_statt_der_initiale() -> void:
	var avatar: PanelContainer = auto_free(UiStil.avatar("Mo", Color.BLUE, 64.0))
	assert_int(avatar.get_child_count()).is_equal(1)
	assert_bool(avatar.get_child(0) is TextureRect).is_true()


func test_unbekannter_absender_hat_keine_figur() -> void:
	UiStil.setze_welt(ThemeData.laden("zimmer"))
	assert_str(UiStil.portrait_figur("gibt_es_nicht")).is_empty()
	assert_str(UiStil.portrait_figur("")).is_empty()


func test_haptik_schalter_wirkt_und_laesst_sich_zuruecksetzen() -> void:
	var vorher: bool = Haptik.ist_an()
	Haptik.an = false
	Haptik.puls(20)    # darf nicht abstuerzen, auch ohne Geraet
	assert_bool(Haptik.ist_an()).is_false()
	Haptik.an = vorher


func test_weltwechsel_plakat_kennt_die_figur_jeder_welt() -> void:
	for welt in WELTEN:
		var figur: String = String(ThemeData.laden(welt).abschnitt("weltwechsel").get("figur", ""))
		assert_str(WeltwechselView.figur_im_text(figur)) 			.override_failure_message("Keine Figur erkannt in " + welt + ": " + figur).is_not_empty()


## K3-Fix 3: nie aufrunden. 199,6 darf nicht "200" werden -- sonst steht ein Betrag da, der den
## Preis zu erreichen scheint, und der Kaufknopf bleibt grau.
func test_zahl_rundet_nie_auf() -> void:
	assert_str(UiStil.zahl(199.2)).is_equal("199")
	assert_str(UiStil.zahl(199.99)).is_equal("199")
	assert_str(UiStil.zahl(9.96)).is_equal("9,9")
	assert_str(UiStil.zahl(1999.9)).is_equal("1.999")
	assert_str(UiStil.zahl(5599999.0)).is_equal("5,5 Mio")
	assert_str(UiStil.zahl(200.0)).is_equal("200")
	assert_str(UiStil.zahl(0.3)).is_equal("0,3")


## Der Preis rundet nie ab: Zeigt das Guthaben (abgerundet) mindestens den Preis (aufgerundet),
## reicht das Guthaben wirklich.
func test_preis_rundet_nie_ab_und_passt_zum_guthaben() -> void:
	assert_str(UiStil.preis(199.2)).is_equal("200")
	assert_str(UiStil.preis(200.0)).is_equal("200")
	assert_str(UiStil.preis(9.01)).is_equal("9,1")
	var preis: float = 200.0
	var kapital: float = 199.99
	assert_bool(UiStil.zahl(kapital) == UiStil.preis(preis)).is_false()
	kapital = 200.0
	assert_str(UiStil.zahl(kapital)).is_equal(UiStil.preis(preis))
