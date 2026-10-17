## K2 P2b: Menue-Gating nach Rang, Rang-Up-Moment mit Inhalt, Rang-Chip, Offline-Obergrenzen,
## "Warum"-Zeile der Ziele und der erste gratis Boost.
extends GdUnitTestSuite


func _kern(rang: int = 1) -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	if rang > 1:
		kern.bogen["punkte"] = kern.erfolge.schwelle(rang)
	return kern


# --- Menue-Gating -----------------------------------------------------------------

func test_rang_1_im_tutorial_hat_keine_einzige_taste() -> void:
	var kern: GameCore = _kern()
	for punkt in Menueleiste.PUNKTE:
		assert_bool(Hud.menue_frei(punkt, kern, true)).override_failure_message("%s ist frei" % punkt).is_false()


func test_ausbau_kommt_mit_dem_ende_des_tutorials() -> void:
	var kern: GameCore = _kern()
	assert_bool(Hud.menue_frei(&"ausbau", kern, true)).is_false()
	assert_bool(Hud.menue_frei(&"ausbau", kern, false)).is_true()


func test_ziele_ab_rang_2_boost_ab_3_fortschritt_ab_4() -> void:
	assert_bool(Hud.menue_frei(&"ziele", _kern(1), false)).is_false()
	assert_bool(Hud.menue_frei(&"ziele", _kern(2), false)).is_true()
	assert_bool(Hud.menue_frei(&"schub", _kern(2), false)).is_false()
	assert_bool(Hud.menue_frei(&"schub", _kern(3), false)).is_true()
	assert_bool(Hud.menue_frei(&"fortschritt", _kern(3), false)).is_false()
	assert_bool(Hud.menue_frei(&"fortschritt", _kern(4), false)).is_true()


func test_ziele_menue_ist_schon_im_tutorial_da_sobald_rang_2() -> void:
	# K2 3, Minute 2:30: Der erste Rang-Up bringt den ersten Knopf, mitten im Tutorial.
	assert_bool(Hud.menue_frei(&"ziele", _kern(2), true)).is_true()


func test_handy_erst_mit_der_ersten_nachricht() -> void:
	var kern: GameCore = _kern(5)
	assert_bool(Hud.menue_frei(&"handy", kern, false)).is_false()
	kern.nachrichten.apply_dict({"empfangen": ["nachricht_01"], "gelesen": 0})
	assert_bool(Hud.menue_frei(&"handy", kern, false)).is_true()
	# ... aber nicht mitten im Tutorial.
	assert_bool(Hud.menue_frei(&"handy", kern, true)).is_false()


func test_gesperrte_knoepfe_fehlen_in_der_leiste() -> void:
	var leiste: Menueleiste = auto_free(Menueleiste.new())
	add_child(leiste)
	for punkt in Menueleiste.PUNKTE:
		leiste.setze_frei(punkt, false)
	assert_int(leiste.anzahl_sichtbar()).is_equal(0)
	assert_bool(leiste.visible).is_false()
	leiste.setze_frei(&"ziele", true)
	assert_int(leiste.anzahl_sichtbar()).is_equal(1)
	assert_bool(leiste.visible).is_true()
	assert_bool(leiste.ist_frei(&"ziele")).is_true()
	assert_bool(leiste.ist_frei(&"schub")).is_false()
	assert_bool(leiste.setze_frei(&"schub", true)).is_true()    # neu erschienen
	assert_bool(leiste.setze_frei(&"schub", true)).is_false()   # schon da


func test_hud_zeichnet_leiste_bei_rang_up_neu() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	var audio: AudioDirector = auto_free(AudioDirector.new())
	add_child(audio)
	var hud: Hud = auto_free(Hud.new())
	add_child(hud)
	hud.aufbauen(kern, thema, audio, auto_free(AdServiceStub.new()))
	assert_bool(hud.menueleiste.ist_frei(&"ziele")).is_false()
	assert_bool(hud.menueleiste.ist_frei(&"ausbau")).is_true()   # kein Tutorial in diesem Test
	hud.tutorial_aktiv = true
	assert_bool(hud.menueleiste.visible).is_false()
	kern.bogen["punkte"] = kern.erfolge.schwelle(2)
	kern._pruefe_level()
	assert_bool(hud.menueleiste.ist_frei(&"ziele")).is_true()
	assert_bool(hud.menueleiste.visible).is_true()
	assert_bool(hud.menueleiste.ist_frei(&"ausbau")).is_false()
	hud.tutorial_aktiv = false
	assert_bool(hud.menueleiste.ist_frei(&"ausbau")).is_true()
	hud.momente_verwerfen()


# --- Rang-Up-Moment ---------------------------------------------------------------

func test_rang_moment_hat_zahl_name_und_genau_eine_zeile() -> void:
	var kern: GameCore = _kern(4)
	var daten: Dictionary = MomentView.rang_daten(4, UiText.t("rang_name_4"), kern.erfolge.freischaltung_bei(4),
		kern.erfolge.bonus_je_rang * 100.0)
	assert_str(String(daten["titel"])).is_equal("Kanal")
	assert_int(int(daten["zaehl_bis"])).is_equal(4)
	assert_int(int(daten["zaehl_von"])).is_equal(3)
	assert_str(String(daten["vorlage"]) % "4").is_equal("Rang 4")
	var zeile: String = String(daten["untertitel"])
	assert_str(zeile).is_equal("Neu: Crew-Karten · Fortschritt-Übersicht")
	assert_bool(zeile.contains("\n")).is_false()
	assert_str(String(daten["figur"])).is_equal("mo")
	assert_str(String(daten["ausdruck"])).is_equal("jubelnd")


func test_rang_moment_ist_nie_ohne_inhalt() -> void:
	# Jeder Rang des ganzen Bogens: nicht leer, beginnt mit "Neu:", ein Name ist da.
	var kern: GameCore = _kern()
	for rang in range(2, kern.erfolge.level_max + 1):
		var name_id: String = kern.rang_name_id(rang)
		assert_bool(UiText.hat(name_id)).override_failure_message("Rangname fehlt: " + name_id).is_true()
		var zeile: String = MomentView.neu_zeile(kern.erfolge.freischaltung_bei(rang), kern.erfolge.bonus_je_rang * 100.0)
		assert_str(zeile).override_failure_message("Rang %d ohne Zeile" % rang).is_not_empty()
		assert_bool(zeile.begins_with("Neu: ")).override_failure_message("Rang %d: %s" % [rang, zeile]).is_true()
		assert_bool(zeile.contains("[")).override_failure_message("Platzhalter sichtbar: " + zeile).is_false()
		assert_bool(zeile.contains("%")).is_equal(zeile.contains("% Einkommen"))


func test_rang_ohne_freischaltung_nennt_den_einkommensbonus() -> void:
	assert_str(MomentView.neu_zeile([], 0.5)).is_equal("Neu: +0,5 % Einkommen")
	assert_str(MomentView.neu_zeile([], 2.0)).is_equal("Neu: +2 % Einkommen")
	# Ein Merkmal ohne Text zaehlt nicht -- dann bleibt der Bonus.
	assert_str(MomentView.neu_zeile(["unbekanntes_merkmal"], 0.5)).is_equal("Neu: +0,5 % Einkommen")


func test_rang_2_nennt_die_ziele_uebersicht() -> void:
	var kern: GameCore = _kern()
	assert_str(MomentView.neu_zeile(kern.erfolge.freischaltung_bei(2), 0.5)).is_equal("Neu: Ziele-Übersicht")


func test_rang_up_signal_baut_den_moment_mit_name_und_zeile() -> void:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var thema: ThemeData = ThemeData.laden("zimmer")
	var audio: AudioDirector = auto_free(AudioDirector.new())
	add_child(audio)
	var hud: Hud = auto_free(Hud.new())
	add_child(hud)
	hud.aufbauen(kern, thema, audio, auto_free(AdServiceStub.new()))
	kern.bogen["punkte"] = kern.erfolge.schwelle(2)
	kern._pruefe_level()
	# Bastian 16.10.: Der Rang ist kein Vollbild mehr, sondern ein kurzer Hinweis am Rand
	# (Saft-Meldung) -- mit derselben einen Zeile "Neu: ...".
	assert_object(hud._moment).is_null()
	var untertitel: String = ""
	for kind in hud.saft.find_children("*", "Label", true, false):
		var label := kind as Label
		if label.text.begins_with("Neu:"):
			untertitel = label.text
	assert_str(untertitel).is_equal("Neu: Ziele-Übersicht")
	hud.momente_verwerfen()


# --- Rang-Chip --------------------------------------------------------------------

func test_rang_chip_zeigt_den_namen_wenn_platz_ist_sonst_die_nummer() -> void:
	assert_str(Kopfleiste.rang_chip_text(3, "Creator")).is_equal("Creator")
	assert_str(Kopfleiste.rang_chip_text(25, "Infrastruktur-Chef")).is_equal("Rang 25")
	assert_str(Kopfleiste.rang_chip_text(1, "")).is_equal("Rang 1")


func test_kein_rangname_ist_in_den_ersten_fuenf_raengen_zu_lang_fuer_den_chip() -> void:
	for rang in range(1, 6):
		var name: String = UiText.t("rang_name_%d" % rang)
		if rang != 5:   # "Kleines Team" ist zu lang und faellt auf die Nummer zurueck
			assert_str(Kopfleiste.rang_chip_text(rang, name)).is_equal(name)


# --- Offline-Obergrenzen ----------------------------------------------------------

func test_offline_obergrenze_waechst_mit_dem_rang() -> void:
	var kern: GameCore = _kern()
	var basis: float = kern.balance.offline_obergrenze
	assert_float(kern.erfolge.offline_obergrenze(1, basis)).is_equal(basis)
	assert_float(kern.erfolge.offline_obergrenze(4, basis)).is_equal(basis)
	assert_float(kern.erfolge.offline_obergrenze(5, basis)).is_equal(6.0 * 3600.0)
	assert_float(kern.erfolge.offline_obergrenze(11, basis)).is_equal(8.0 * 3600.0)
	assert_float(kern.erfolge.offline_obergrenze(16, basis)).is_equal(12.0 * 3600.0)
	assert_float(kern.erfolge.offline_obergrenze(30, basis)).is_equal(12.0 * 3600.0)


func test_offline_ertrag_nutzt_die_obergrenze_des_ranges() -> void:
	var klein: GameCore = _kern(1)
	var gross: GameCore = _kern(5)
	klein.kapital = 0.0
	gross.kapital = 0.0
	var a: float = klein.wende_offline_an(24.0 * 3600.0)
	var b: float = gross.wende_offline_an(24.0 * 3600.0)
	assert_float(a).is_greater(0.0)
	assert_float(b / a).is_between(1.4, 1.6)   # 6 h gegen 4 h


# --- Ziel-Warum -------------------------------------------------------------------

func test_ziel_warum_steht_unter_normalen_zielen_nicht_unter_missionen() -> void:
	var thema: ThemeData = ThemeData.laden("zimmer")
	var warum: String = Menues.Zielemenue.ziel_warum_text(thema, {"typ": "station_stufe"})
	assert_str(warum).is_not_empty()
	assert_str(warum).is_equal(WeltTexte.ziel_warum(thema, "station_stufe"))
	assert_str(Menues.Zielemenue.ziel_warum_text(thema, {"typ": "station_stufe", "kette": "welt"})).is_empty()
	assert_str(Menues.Zielemenue.ziel_warum_text(thema, {"typ": "gibt_es_nicht"})).is_empty()


# --- Der erste Boost ist gratis ---------------------------------------------------

func test_erster_boost_zaehlt_im_bogen_und_ueberlebt_speichern() -> void:
	var kern: GameCore = _kern(3)
	assert_int(int(kern.bogen.get("schub", -1))).is_equal(0)
	kern.starte_schub()
	assert_int(int(kern.bogen["schub"])).is_equal(1)
	var stand: SaveData = kern.to_save()
	var neu := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	neu.from_save(stand)
	assert_int(int(neu.bogen["schub"])).is_equal(1)


# --- Erstes Ziel als Moment (Tutorial) ------------------------------------------------

func _hud_mit_kern(kern: GameCore) -> Hud:
	var thema: ThemeData = ThemeData.laden("zimmer")
	var audio: AudioDirector = auto_free(AudioDirector.new())
	add_child(audio)
	var hud: Hud = auto_free(Hud.new())
	add_child(hud)
	hud.aufbauen(kern, thema, audio, auto_free(AdServiceStub.new()))
	return hud


func test_erstes_ziel_im_tutorial_ist_ein_moment_auch_unter_der_schwelle() -> void:
	var hud: Hud = _hud_mit_kern(_kern())
	var ohne: Dictionary = hud._ziel_moment_daten(50.0)
	assert_bool(ohne.has("erzwingen")).is_false()
	assert_bool(hud.moment_zeigen(ohne)).is_false()
	hud.tutorial_aktiv = true
	var mit: Dictionary = hud._ziel_moment_daten(50.0)
	assert_bool(bool(mit.get("erzwingen", false))).is_true()
	assert_str(String(mit["titel"])).is_equal("Dein erstes Ziel!")
	assert_str(String(mit["untertitel"])).contains("Gaming-PC")
	# Bastian 16.10.: Ziele sind kein Vollbild mehr (nur noch der Raumkauf, data/ui/hinweise.json).
	assert_bool(hud.moment_zeigen(mit)).is_false()
	assert_bool(hud.moment_zeigen({"art": "raum", "betrag": 0.0, "titel": "x"})).is_true()
	hud.momente_verwerfen()


func test_crew_karten_erst_ab_dem_rang_aus_den_daten() -> void:
	var kern: GameCore = _kern()
	kern.kapital = 1.0e9
	kern.upgrade_station_mehrfach(&"station_intake", 30)
	kern.kaufe_bereich(&"bereich_1")
	var hud: Hud = _hud_mit_kern(kern)
	hud.stationsmenue.zeige_station(&"station_intake")
	hud.stationsmenue.aktualisiere()
	assert_bool(kern.ist_frei("crew")).is_false()
	assert_bool(hud.stationsmenue._crew_platz.visible).is_false()
	kern.bogen["punkte"] = kern.erfolge.schwelle(4)
	hud.stationsmenue.aktualisiere()
	assert_bool(kern.ist_frei("crew")).is_true()
	# Ab Rang 4 entscheidet wieder nur die Crew-Regel selbst (eigene Freigabe der Station).
	assert_bool(hud.stationsmenue._crew_platz.visible).is_equal(kern.crew_hat(&"station_intake") and kern.crew_frei(&"station_intake"))
	hud.momente_verwerfen()
