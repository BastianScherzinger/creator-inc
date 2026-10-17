## Prueft die Klangentscheidungen -- ohne Audiohardware.
##
## Die teuren Fehler eines Spielklangs sind Entscheidungsfehler: ein Klang,
## der viermal pro Sekunde feuert, oder einer, der bei Stufe 80 zum Fiepen
## wird. Genau die stehen hier.
extends GdUnitTestSuite

const REGELN_PFAD: String = "res://data/audio/sounds.json"


func _regeln() -> AudioRegeln:
	return AudioRegeln.new(AudioRegeln.laden(REGELN_PFAD))


func test_zuordnung_ist_lesbar_und_vollstaendig() -> void:
	var daten: Dictionary = AudioRegeln.laden(REGELN_PFAD)
	assert_bool(daten.has("ereignisse")).is_true()

	# Jedes Ereignis MUSS einen Klang benennen -- ein leerer Eintrag waere
	# stiller Ausfall statt Fehler.
	var ereignisse: Dictionary = daten["ereignisse"] as Dictionary
	assert_int(ereignisse.size()).is_greater(0)
	for schluessel in ereignisse.keys():
		var regel: Dictionary = ereignisse[schluessel] as Dictionary
		assert_str(String(regel.get("klang", ""))).is_not_empty()


func test_jede_klangdatei_existiert() -> void:
	# Ein Tippfehler im JSON wuerde sonst erst auf dem Geraet auffallen --
	# und dort als Stille, also gar nicht.
	for name in _regeln().benoetigte_klaenge():
		assert_bool(ResourceLoader.exists("res://assets/audio/%s.wav" % name)) \
			.override_failure_message("Klangdatei fehlt: %s" % name).is_true()


func test_unbekanntes_ereignis_bleibt_stumm() -> void:
	assert_bool(_regeln().entscheide(&"gibt_es_nicht", 0.0).is_empty()).is_true()


func test_sperre_verhindert_dauerfeuer() -> void:
	var regeln: AudioRegeln = _regeln()
	# Der Hinweis hat die laengste Sperre, weil sein Ereignis am oeftesten
	# eintritt. Zweimal im selben Moment darf er nicht kommen.
	assert_bool(regeln.entscheide(&"hinweis", 10.0).is_empty()).is_false()
	assert_bool(regeln.entscheide(&"hinweis", 10.1).is_empty()).is_true()
	assert_bool(regeln.entscheide(&"hinweis", 20.0).is_empty()).is_false()


func test_engpasswechsel_bleibt_ueber_eine_stunde_ertraeglich() -> void:
	# Der Engpass kann rechnerisch bei jedem Tick wechseln (viermal pro
	# Sekunde). Ueber eine Stunde waeren das 14.400 Klaenge. Diese Zahl ist
	# der eigentliche Grund fuer die Sperre -- also wird sie gemessen.
	var regeln: AudioRegeln = _regeln()
	var gespielt: int = 0
	var t: float = 0.0
	while t < 3600.0:
		if not regeln.entscheide(&"hinweis", t).is_empty():
			gespielt += 1
		t += 0.25
	assert_int(gespielt).is_less_equal(1500)


func test_globale_sperre_laesst_nur_das_erste_durch() -> void:
	# Ausbau, Meilenstein und Freischaltung treffen regelmaessig im selben
	# Bild zusammen. Dann soll EIN Klang kommen, nicht drei uebereinander.
	var regeln: AudioRegeln = _regeln()
	assert_bool(regeln.entscheide(&"ausbau", 5.0, 3).is_empty()).is_false()
	assert_bool(regeln.entscheide(&"meilenstein", 5.0).is_empty()).is_true()
	assert_bool(regeln.entscheide(&"freischaltung", 5.0).is_empty()).is_true()
	# Kurz danach ist wieder Platz
	assert_bool(regeln.entscheide(&"meilenstein", 5.5).is_empty()).is_false()


func test_tonhoehe_steigt_mit_der_stufe() -> void:
	var regeln: AudioRegeln = _regeln()
	var erste: float = float(regeln.entscheide(&"ausbau", 0.0, 1)["tonhoehe"])
	var spaetere: float = float(regeln.entscheide(&"ausbau", 1.0, 6)["tonhoehe"])
	assert_float(erste).is_equal_approx(1.0, 0.001)
	assert_bool(spaetere > erste).is_true()


func test_tonhoehe_setzt_am_meilenstein_zurueck() -> void:
	# Alle zwoelf Stufen greift ein Meilenstein-Multiplikator. Die Tonleiter
	# setzt dort neu an -- sonst waere Stufe 80 ein Fiepen.
	var regeln: AudioRegeln = _regeln()
	var stufe_1: float = float(regeln.entscheide(&"ausbau", 0.0, 1)["tonhoehe"])
	var stufe_13: float = float(regeln.entscheide(&"ausbau", 1.0, 13)["tonhoehe"])
	var stufe_25: float = float(regeln.entscheide(&"ausbau", 2.0, 25)["tonhoehe"])
	assert_float(stufe_13).is_equal_approx(stufe_1, 0.001)
	assert_float(stufe_25).is_equal_approx(stufe_1, 0.001)


func test_tonhoehe_bleibt_auch_bei_hohen_stufen_im_rahmen() -> void:
	var regeln: AudioRegeln = _regeln()
	for stufe in range(1, 400):
		var wahl: Dictionary = regeln.entscheide(&"ausbau", float(stufe) * 10.0, stufe)
		assert_float(float(wahl["tonhoehe"])).is_between(0.9, 1.35)


func test_stumm_entscheidet_negativ_statt_leise_zu_spielen() -> void:
	var regeln: AudioRegeln = _regeln()
	regeln.ton_an = false
	assert_bool(regeln.entscheide(&"ausbau", 0.0, 1).is_empty()).is_true()
	regeln.ton_an = true
	assert_bool(regeln.entscheide(&"ausbau", 0.0, 1).is_empty()).is_false()
