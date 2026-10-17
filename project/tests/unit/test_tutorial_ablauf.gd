## Prueft die Einfuehrung als Zustandsmaschine.
##
## Der teuerste Fehler eines Tutorials ist eine Bedingung, die niemand
## erfuellen kann: Es meldet sie keiner, die Leute deinstallieren einfach.
## Deshalb steht hier nicht nur, dass die Schritte einzeln funktionieren,
## sondern dass ein normaler Spielverlauf durch ALLE hindurchkommt.
extends GdUnitTestSuite

const ABLAUF_PFAD: String = "res://data/tutorial/tutorial.json"
## Die Einfuehrung laeuft genau einmal: in Welt 1.
const THEMA: String = "zimmer"


func _ablauf() -> TutorialAblauf:
	return TutorialAblauf.new(TutorialAblauf.laden(ABLAUF_PFAD))


func test_ablauf_ist_lesbar_und_hat_schritte() -> void:
	assert_int(_ablauf().anzahl_schritte()).is_greater(0)


func test_jeder_schritt_hat_id_ziel_und_bedingung() -> void:
	var daten: Dictionary = TutorialAblauf.laden(ABLAUF_PFAD)
	for eintrag in (daten["schritte"] as Array):
		var schritt: Dictionary = eintrag as Dictionary
		assert_str(String(schritt.get("id", ""))).is_not_empty()
		assert_str(String(schritt.get("ziel", ""))).is_not_empty()
		var bedingung: Dictionary = schritt.get("abschluss", {}) as Dictionary
		assert_str(String(bedingung.get("typ", ""))).is_not_empty()
		assert_bool(bedingung.has("wert")).is_true()


func test_jeder_schritt_hat_texte_im_thema() -> void:
	# Ein Schritt ohne Text erscheint als leere Karte -- der Spieler sieht
	# einen Rahmen und weiss nicht, was er soll. Das faellt sonst erst auf
	# dem Geraet auf.
	var thema: ThemeData = ThemeData.laden(THEMA)
	assert_object(thema).is_not_null()
	var texte: Dictionary = thema.abschnitt("tutorial")
	assert_str(String(texte.get("ueberspringen", ""))).is_not_empty()

	var daten: Dictionary = TutorialAblauf.laden(ABLAUF_PFAD)
	for eintrag in (daten["schritte"] as Array):
		var id: String = String((eintrag as Dictionary).get("id", ""))
		var text_eintrag: Dictionary = texte.get(id, {}) as Dictionary
		assert_str(String(text_eintrag.get("titel", ""))) \
			.override_failure_message("Titel fehlt fuer Schritt '%s'" % id).is_not_empty()
		assert_str(String(text_eintrag.get("text", ""))) \
			.override_failure_message("Text fehlt fuer Schritt '%s'" % id).is_not_empty()


func test_falsche_meldung_schaltet_nicht_weiter() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	assert_bool(ablauf.melde(&"stufen_gesamt", 99)).is_false()
	assert_int(ablauf.schritt).is_equal(0)


func test_falsche_station_schaltet_nicht_weiter() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	assert_bool(ablauf.melde(&"station_gewaehlt", "station_processing")).is_false()
	assert_bool(ablauf.melde(&"station_gewaehlt", "station_intake")).is_true()
	assert_int(ablauf.schritt).is_equal(1)


## Spielt den Verlauf aus K2 3 durch: Pinnwand, ausbauen, rote Station antippen, ausbauen,
## erstes Ziel, Belohnung holen, Ausstattung, Flur, Upload. Gibt die Schritt-IDs in der
## Reihenfolge zurueck, in der sie erschienen sind.
func _normaler_verlauf(ablauf: TutorialAblauf) -> Array[String]:
	var ids: Array[String] = [ablauf.aktuelle_id()]
	var ereignisse: Array = [
		[&"station_gewaehlt", "station_intake"],
		[&"stufen_gesamt", 4],
		[&"engpass_gewaehlt", "station_buffer"],
		[&"stufen_gesamt", 6],
		[&"ziel_erfuellt", "ziel_01"],
		[&"ziele_eingeloest", 1],
		[&"ausstattung_gekauft", 1],
		[&"bereich_gekauft", "bereich_1"],
		[&"station_gewaehlt", "station_transport"],
	]
	for e in ereignisse:
		if ablauf.melde(e[0] as StringName, e[1]) and not ablauf.beendet:
			ids.append(ablauf.aktuelle_id())
	return ids


func test_ein_normaler_spielverlauf_kommt_durch_alle_schritte() -> void:
	# DAS ist der eigentliche Test: Ein Spieler, der einfach spielt, muss ankommen, ohne
	# dass irgendwo eine Bedingung wartet, die er nie ausloest.
	var ablauf: TutorialAblauf = _ablauf()
	var ids: Array[String] = _normaler_verlauf(ablauf)
	assert_bool(ablauf.beendet) 		.override_failure_message(
			"Tutorial haengt bei Schritt %d ('%s') fest" % [ablauf.schritt, ablauf.aktuelle_id()]) 		.is_true()
	assert_array(ids).is_equal(["waehlen", "ausbauen", "kette", "rot", "erstes_ziel", "belohnung",
		"ausstattung", "flur", "upload"])


func test_schrittreihenfolge_folgt_k2_tabelle() -> void:
	var ids: Array[String] = []
	for eintrag in (TutorialAblauf.laden(ABLAUF_PFAD)["schritte"] as Array):
		ids.append(String((eintrag as Dictionary)["id"]))
	assert_array(ids).is_equal(["waehlen", "ausbauen", "kette", "rot", "erstes_ziel", "belohnung",
		"ausstattung", "flur", "upload"])


func test_tutorial_endet_nach_dem_upload_nicht_vorher() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.melde(&"station_gewaehlt", "station_intake")
	ablauf.melde(&"stufen_gesamt", 4)
	ablauf.melde(&"engpass_gewaehlt", "station_buffer")
	ablauf.melde(&"stufen_gesamt", 6)
	ablauf.melde(&"ziel_erfuellt", "ziel_01")
	ablauf.melde(&"ziele_eingeloest", 1)
	ablauf.melde(&"ausstattung_gekauft", 1)
	ablauf.melde(&"bereich_gekauft", "bereich_1")
	assert_bool(ablauf.beendet).is_false()
	assert_str(ablauf.aktuelle_id()).is_equal("upload")
	ablauf.melde(&"station_gewaehlt", "station_transport")
	assert_bool(ablauf.beendet).is_true()


func test_engpass_antippen_zaehlt_nur_seit_beginn_des_schritts() -> void:
	# Die Pinnwand IST am Anfang der Engpass: Wer sie im ersten Schritt antippt, hat damit
	# nicht schon die rote Station der Kette angetippt.
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.melde(&"engpass_gewaehlt", "station_intake")      # zu frueh
	ablauf.melde(&"station_gewaehlt", "station_intake")
	ablauf.melde(&"stufen_gesamt", 4)
	assert_str(ablauf.aktuelle_id()).is_equal("kette")
	ablauf.melde(&"engpass_gewaehlt", "station_buffer")
	assert_str(ablauf.aktuelle_id()).is_equal("rot")


func test_zielleiste_erscheint_erst_im_ersten_ziel_schritt() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	assert_bool(ablauf.zeigt("zielleiste")).is_false()
	ablauf.melde(&"station_gewaehlt", "station_intake")
	ablauf.melde(&"stufen_gesamt", 4)
	ablauf.melde(&"engpass_gewaehlt", "station_buffer")
	assert_bool(ablauf.zeigt("zielleiste")).is_false()
	ablauf.melde(&"stufen_gesamt", 6)
	assert_str(ablauf.aktuelle_id()).is_equal("erstes_ziel")
	assert_bool(ablauf.zeigt("zielleiste")).is_true()
	# Beendet: alles ist da.
	ablauf.ueberspringen()
	assert_bool(ablauf.zeigt("zielleiste")).is_true()


func test_ziel_schon_erfuellt_ueberspringt_nicht_die_belohnung() -> void:
	# Ist das erste Ziel erfuellt, bevor der Schritt beginnt, geht es zur Belohnung -- und dort
	# wartet der Ablauf, bis das Ziel wirklich eingeloest ist.
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.melde(&"ziel_erfuellt", "ziel_01")
	ablauf.melde(&"station_gewaehlt", "station_intake")
	ablauf.melde(&"stufen_gesamt", 4)
	ablauf.melde(&"engpass_gewaehlt", "station_buffer")
	ablauf.melde(&"stufen_gesamt", 6)
	assert_str(ablauf.aktuelle_id()).is_equal("belohnung")


func test_absolute_messwerte_nach_neustart_reichen_nach() -> void:
	# Stand mitten im Tutorial: Der Zaehler ist leer, die Stufen sind aber schon da.
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.apply_dict({"schritt": 1, "beendet": false})
	assert_str(ablauf.aktuelle_id()).is_equal("ausbauen")
	ablauf.melde(&"stufen_gesamt", 5)
	assert_str(ablauf.aktuelle_id()).is_equal("kette")


func test_zaehlende_ereignisse_laufen_auch_vor_ihrem_schritt_mit() -> void:
	# Eine Ausstattung, die vor ihrem Schritt gekauft wurde, zaehlt trotzdem.
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.melde(&"ausstattung_gekauft", 1)
	ablauf.melde(&"station_gewaehlt", "station_intake")
	ablauf.melde(&"stufen_gesamt", 4)
	ablauf.melde(&"engpass_gewaehlt", "station_buffer")
	ablauf.melde(&"stufen_gesamt", 6)
	ablauf.melde(&"ziel_erfuellt", "ziel_01")
	ablauf.melde(&"ziele_eingeloest", 1)
	assert_str(ablauf.aktuelle_id()).is_equal("flur")


func test_jede_karte_sagt_was_der_ausbau_bewirkt() -> void:
	# Bastians Befund: Man versteht nicht, was man verbessert. Jede Karte, die zum Handeln
	# auffordert, nennt deshalb die Wirkung (Geld/Einkommen/schneller/Reichweite/Belohnung ...).
	var thema: ThemeData = ThemeData.laden(THEMA)
	var texte: Dictionary = thema.abschnitt("tutorial")
	var wirkung: Array[String] = ["Geld", "mehr", "schneller", "bremst", "Reichweite", "hochladen", "Belohnung", "Gaming-PC", "Idee"]
	for id in ["ausbauen", "kette", "rot", "erstes_ziel", "belohnung", "ausstattung", "flur", "upload"]:
		var text: String = String((texte[id] as Dictionary)["text"])
		var hat: bool = false
		for w in wirkung:
			hat = hat or text.contains(w)
		assert_bool(hat).override_failure_message("Karte '%s' sagt nicht, was es bringt: %s" % [id, text]).is_true()
		assert_int(text.length()).override_failure_message("Karte '%s' zu lang (%d)" % [id, text.length()]).is_less(130)


func test_kein_werbeangebot_und_keine_marken_im_tutorial_text() -> void:
	var texte: Dictionary = ThemeData.laden(THEMA).abschnitt("tutorial")
	for id in texte.keys():
		if String(id).begins_with("_") or texte[id] is String:
			continue
		var gesamt: String = JSON.stringify(texte[id])
		for verboten in ["Werbung", "Algorithmus", "Rang", "Marke"]:
			assert_bool(gesamt.contains(verboten)).override_failure_message("%s enthaelt %s" % [id, verboten]).is_false()


func test_ueberspringen_beendet_sofort_und_endgueltig() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.ueberspringen()
	assert_bool(ablauf.beendet).is_true()
	assert_bool(ablauf.aktueller().is_empty()).is_true()
	assert_bool(ablauf.melde(&"station_gewaehlt", "station_intake")).is_false()


func test_stand_ueberlebt_speichern_und_laden() -> void:
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.melde(&"station_gewaehlt", "station_intake")
	var gespeichert: Dictionary = ablauf.to_dict()

	var neu: TutorialAblauf = _ablauf()
	neu.apply_dict(gespeichert)
	assert_int(neu.schritt).is_equal(ablauf.schritt)
	assert_str(neu.aktuelle_id()).is_equal(ablauf.aktuelle_id())


func test_stand_jenseits_der_schrittliste_gilt_als_durch() -> void:
	# Entsteht, wenn eine spaetere Fassung Schritte ENTFERNT. Dann ist das
	# Tutorial durch, nicht kaputt.
	var ablauf: TutorialAblauf = _ablauf()
	ablauf.apply_dict({"schritt": 999, "beendet": false})
	assert_bool(ablauf.beendet).is_true()
	assert_bool(ablauf.aktueller().is_empty()).is_true()


# --- Paket U3: Szenen, Momente, Zeigehand -----------------------------------------

func test_szene_aus_einzelner_antwort_wird_ein_chip() -> void:
	var s: Dictionary = SzeneView.normalisiere({"von": "mo", "text": "Eins.\nZwei.", "antwort": "Danke."})
	assert_int((s["blasen"] as Array).size()).is_equal(2)
	assert_str(String(((s["blasen"] as Array)[0] as Dictionary)["ausdruck"])).is_equal("neutral")
	assert_int((s["antworten"] as Array).size()).is_equal(1)


func test_szene_blasen_erben_figur_und_ausdruck() -> void:
	var s: Dictionary = SzeneView.normalisiere({"von": "tobi", "ausdruck": "geschockt",
		"blasen": ["A", {"von": "mira", "text": "B"}], "antworten": ["x", {"text": "y", "reaktion": "z"}]})
	var b: Array = s["blasen"] as Array
	assert_str(String((b[0] as Dictionary)["von"])).is_equal("tobi")
	assert_str(String((b[0] as Dictionary)["ausdruck"])).is_equal("geschockt")
	assert_str(String((b[1] as Dictionary)["von"])).is_equal("mira")
	assert_str(String(((s["antworten"] as Array)[1] as Dictionary)["reaktion"])).is_equal("z")


func test_kleine_ziele_sind_kein_moment() -> void:
	assert_bool(MomentView.ist_moment("ziel", 50.0)).is_false()
	assert_bool(MomentView.ist_moment("ziel", 200.0)).is_true()
	assert_bool(MomentView.ist_moment("stern", 0.0)).is_true()


func test_zeigehand_erst_nach_ruhe_und_mit_ziel() -> void:
	assert_bool(ZeigeHand.soll_zeigen(59.0, 60.0, true)).is_false()
	assert_bool(ZeigeHand.soll_zeigen(61.0, 60.0, false)).is_false()
	assert_bool(ZeigeHand.soll_zeigen(61.0, 60.0, true)).is_true()
	assert_float(U3Text.schwelle("hand_leerlauf_sekunden")).is_equal(60.0)
