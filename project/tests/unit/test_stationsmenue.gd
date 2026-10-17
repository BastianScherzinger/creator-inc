## Prueft das Stationsmenue (DESIGN_OVERHAUL 4.2): EIN Hauptknopf, 104 hoch,
## Preis gross; Ausstattung als Zeilen; gesperrte Zeile ohne Preis.
extends GdUnitTestSuite


func _menue(kapital: float = 1.0e9) -> Stationsmenue:
	var kern := GameCore.new()
	kern.kapital = kapital
	var m := Stationsmenue.new()
	m.kern = kern
	m.thema = ThemeData.laden(kern.welt_id())
	add_child(m)
	m.zeige_station(Ids.CHAIN[0])
	return m


func test_faktor_text() -> void:
	assert_str(Stationsmenue.faktor_text(1.5)).is_equal("1,5")
	assert_str(Stationsmenue.faktor_text(2.0)).is_equal("2")


func test_hauptknopf_ist_104_hoch_und_preis_gross() -> void:
	var m: Stationsmenue = _menue()
	assert_float(m._ausbau.custom_minimum_size.y).is_equal(UiStil.KNOPF_PRIMAER_H)
	assert_int(m._ausbau_preis.get_theme_font_size("font_size")).is_equal(UiStil.GR_ZAHL)
	assert_bool(m._ausbau_preis.text.contains("€")).is_true()
	m.queue_free()


func test_ausstattung_sind_zeilen_mit_preisknopf() -> void:
	var m: Stationsmenue = _menue()
	var kern: GameCore = m.kern
	var station: StationModel = kern.kette.station(Ids.CHAIN[0])
	assert_int(m._karten.get_child_count()).is_equal(station.ausstattung.size())
	for kind in m._karten.get_children():
		var knopf: Button = kind.find_child("Knopf", true, false) as Button
		assert_object(knopf).is_not_null()
		assert_float(knopf.custom_minimum_size.y).is_equal(UiStil.KNOPF_SEKUNDAER_H)
	m.queue_free()


func test_gesperrte_zeile_zeigt_keinen_preis() -> void:
	var m: Stationsmenue = _menue()
	var kern: GameCore = m.kern
	var station: StationModel = kern.kette.station(Ids.CHAIN[0])
	for p in station.ausstattung:
		if p.freigegeben(station.stufe):
			continue
		var karte_p: Control = m._platz_knoepfe[p.id] as Control
		var knopf: Button = karte_p.find_child("Knopf", true, false) as Button
		assert_bool(knopf.disabled).is_true()
		assert_str(knopf.text).is_equal(UiText.t("ab_stufe") % p.ab_stufe)
		assert_bool(knopf.text.contains("€")).is_false()
	m.queue_free()


func test_hauptknopf_gesperrt_wenn_zu_teuer() -> void:
	var m: Stationsmenue = _menue(0.0)
	assert_bool(m._ausbau.disabled).is_true()
	m.queue_free()


func test_erklaersatz_steht_unter_den_ausstattungskarten() -> void:
	var m: Stationsmenue = _menue()
	var eltern: Node = m._beschreibung.get_parent()
	assert_object(eltern).is_same(m._karten.get_parent())
	assert_bool(m._beschreibung.get_index() > m._karten.get_index()).is_true()
	m.queue_free()


func test_heldzone_zeigt_genau_eine_einheit() -> void:
	var m: Stationsmenue = _menue()
	var einheit: String = WeltTexte.einheit(m.thema, Ids.CHAIN[0])
	var gross: String = m._nutzen_euro.text
	var klein: String = m._nutzen_leistung.text
	# Wenn die grosse Zeile die Einheit traegt, steht sie in der kleinen nicht noch einmal.
	if gross.contains(einheit):
		assert_bool(klein.contains(einheit)).is_false()
	m.queue_free()
