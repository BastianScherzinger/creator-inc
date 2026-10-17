## Auftragsbrett (Welle 2b): Auftragsliste aus dem Kern, Texte aus dem Thema, Abholen, Ort.
extends GdUnitTestSuite


func _kern() -> GameCore:
	return GameCore.new(BalanceData.fuer_welt("zimmer"), 0)


func test_auftraege_sind_hoechstens_drei_und_haben_absender_und_satz() -> void:
	var kern: GameCore = _kern()
	var thema: ThemeData = ThemeData.laden("zimmer")
	var liste: Array[Dictionary] = Auftragsbrett.auftraege_von(kern, thema)
	assert_int(liste.size()).is_between(1, Auftragsbrett.ANZAHL)
	for e in liste:
		assert_str(String(e["id"])).is_not_empty()
		assert_float(float(e["fortschritt"])).is_between(0.0, 1.0)
	var texte: Dictionary = Auftragsbrett.texte_von(thema)
	var erster: Dictionary = liste[0]
	if texte.has(String(erster["id"])):
		assert_str(String(erster["absender"])).is_not_empty()
		assert_str(String(erster["satz"])).is_not_empty()


func test_ziel_info_unbekannt_ist_leer() -> void:
	assert_bool(_kern().ziel_info("gibt_es_nicht").is_empty()).is_true()


func test_ziel_info_ohne_texte_hat_leere_felder() -> void:
	var kern: GameCore = _kern()
	var id: String = String(kern.ziele.sichtbar()[0].get("id", ""))
	var info: Dictionary = kern.ziel_info(id)
	assert_str(String(info["absender"])).is_empty()
	assert_str(String(info["satz"])).is_empty()


func test_erfuellte_auftraege_stehen_vorn_und_lassen_sich_abholen() -> void:
	var kern: GameCore = _kern()
	kern.kapital = 1.0e9
	var vorher: int = kern.ziele.anzahl_eingeloest()
	# Stufen kaufen, bis irgendein Auftrag bereit ist.
	for i in range(400):
		for id in kern.kette.stations.keys():
			kern.upgrade_station(id as StringName)
		if String(kern.auftragskarten(3)[0]["status"]) == "bereit":
			break
	var erster: Dictionary = kern.auftragskarten(3)[0]
	if String(erster["status"]) != "bereit":
		return
	kern.loese_ziel_ein(StringName(String(erster["id"])))
	assert_int(kern.ziele.anzahl_eingeloest()).is_greater(vorher)


func test_ziel_ort_zeigt_immer_auf_station_oder_raum() -> void:
	var kern: GameCore = _kern()
	for e in kern.auftragskarten(3):
		var ort: Dictionary = Auftragsbrett.ziel_ort(kern, String(e["id"]))
		assert_array(["station", "bereich"]).contains([String(ort["art"])])
		assert_str(String(ort["id"])).is_not_empty()


func test_kurztext_und_zaehler() -> void:
	assert_str(Auftragsbrett.zaehler_text({"ist": 3.0, "soll": 10.0})).is_equal("3/10")
	assert_str(Auftragsbrett.zaehler_text({"ist": 1.0, "soll": 1.0})).is_empty()
	assert_str(Auftragsbrett.absender_name(null, "mo")).is_equal("Mo")
