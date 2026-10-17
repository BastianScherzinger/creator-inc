## K2 P1: Die Eroeffnung zeigt ALLE Blasen (kein Kappen auf drei), ohne Antwortchip
## mit dem Knopf aus der Themendatei; Welt-Ziel und Zwischenmarken stehen im Thema.
extends GdUnitTestSuite


func test_eroeffnung_zeigt_alle_blasen() -> void:
	var texte: Dictionary = {"chat": [
		{"von": "mo", "text": "Eins."}, {"von": "mo", "text": "Zwei."},
		{"von": "mo", "text": "Drei."}, {"von": "mo", "text": "Vier."}]}
	var szene: Dictionary = SzeneView.szene_aus_eroeffnung(texte)
	assert_int((szene["blasen"] as Array).size()).is_equal(4)
	assert_str(String(szene["von"])).is_equal("mo")


func test_eroeffnung_ohne_du_zeile_hat_den_knopf_als_einzige_antwort() -> void:
	var texte: Dictionary = {"knopf": "Los geht's", "chat": [{"von": "mo", "text": "Hallo."}]}
	var szene: Dictionary = SzeneView.szene_aus_eroeffnung(texte)
	var antworten: Array = szene["antworten"] as Array
	assert_int(antworten.size()).is_equal(1)
	assert_str(String(antworten[0])).is_equal("Los geht's")


func test_eroeffnung_mit_du_zeile_behaelt_den_antwortchip() -> void:
	var texte: Dictionary = {"knopf": "Anfangen", "chat": [
		{"von": "mo", "text": "Hallo."}, {"von": "du", "text": "Und jetzt?"}]}
	var antworten: Array = SzeneView.szene_aus_eroeffnung(texte)["antworten"] as Array
	assert_int(antworten.size()).is_equal(1)
	assert_str(String(antworten[0])).is_equal("Und jetzt?")


func test_welt_1_eroeffnung_nennt_das_ziel_in_der_letzten_blase() -> void:
	var thema: ThemeData = ThemeData.laden("zimmer")
	var szene: Dictionary = SzeneView.szene_aus_eroeffnung(thema.abschnitt("eroeffnung"))
	var blasen: Array = szene["blasen"] as Array
	assert_int(blasen.size()).is_equal(3)
	assert_str(String((blasen[2] as Dictionary)["text"])).contains("Gaming-PC")
	assert_int((szene["antworten"] as Array).size()).is_equal(1)


func test_welt_ziel_und_marken_namen_stehen_im_thema() -> void:
	var thema: ThemeData = ThemeData.laden("zimmer")
	assert_str(WeltTexte.welt_ziel(thema)).is_equal("Der Gaming-PC")
	assert_str(WeltTexte.marke_name(thema, "fortschritt_25")).is_equal("Stativ steht")
	assert_str(WeltTexte.marke_name(thema, "fortschritt_75")).is_equal("Paket bestellt")
	assert_str(WeltTexte.marke_name(thema, "gibt_es_nicht")).is_empty()


func test_welt_ziel_faellt_ohne_eintrag_auf_den_untertitel_zurueck() -> void:
	var thema: ThemeData = ThemeData.laden("kapital")
	var ziel: String = WeltTexte.welt_ziel(thema)
	assert_str(ziel).is_not_empty()
