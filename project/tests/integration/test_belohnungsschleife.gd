## Prueft die Belohnungsschleife: Aufruf -> Signal -> Wirkung im Kern.
##
## Der Stub ist im Spiel ABSICHTLICH asynchron -- er braucht Sekunden, kann
## fehlschlagen und kennt Sperrzeiten. Genau diese Faelle stehen hier:
## Sperrzeit, Limit, Ladefehler, zweiter Aufruf waehrend der erste laeuft.
##
## Die Tests setzen die Dauer auf 0 und bekommen die Antwort sofort. Grund:
## Im gdUnit-Lauf werden keine SceneTree-Frames verarbeitet, ein Timer laeuft
## dort nie ab. Getestet wird deshalb die ENTSCHEIDUNG, nicht die Uhr --
## und das ist ohnehin die Seite, an der Fehler weh tun.
extends GdUnitTestSuite

const PLATZIERUNG := &"schub"


func _stub() -> AdServiceStub:
	var stub := auto_free(AdServiceStub.new()) as AdServiceStub
	add_child(stub)
	# Sofort antworten -- siehe Kopfkommentar.
	stub.dauer_sekunden = 0.0
	stub.fehlerquote = 0.0
	return stub


func test_platzierungen_sind_konfiguriert() -> void:
	var daten: Dictionary = AdServiceStub.laden()
	var platzierungen: Dictionary = daten.get("platzierungen", {}) as Dictionary
	assert_bool(platzierungen.has("schub")).is_true()
	assert_bool(platzierungen.has("offline_verdoppeln")).is_true()


func test_waehrend_der_vorfuehrung_ist_nichts_bereit() -> void:
	# Die Oberflaeche braucht diesen Zwischenzustand, sonst laesst sich der
	# Knopf zweimal druecken und die Belohnung doppelt kassieren.
	var stub: AdServiceStub = _stub()
	stub.dauer_sekunden = 60.0        # laeuft und laeuft
	assert_bool(stub.ist_bereit(PLATZIERUNG)).is_true()
	stub.zeige_belohnt(PLATZIERUNG)
	assert_bool(stub.ist_bereit(PLATZIERUNG)).is_false()


func test_belohnung_wird_gemeldet() -> void:
	var stub: AdServiceStub = _stub()
	var verdient: Array = []
	stub.belohnung_verdient.connect(func(p: StringName) -> void: verdient.append(p))
	stub.zeige_belohnt(PLATZIERUNG)
	assert_int(verdient.size()).is_equal(1)


func test_belohnung_wirkt_im_kern() -> void:
	var stub: AdServiceStub = _stub()
	var kern := GameCore.new()
	for id in Ids.CHAIN:
		var station: StationModel = kern.kette.station(id)
		if station != null:
			station.stufe = 5
	stub.belohnung_verdient.connect(func(_p: StringName) -> void: kern.starte_schub())

	var vorher: float = kern.einkommen_pro_sekunde()
	stub.zeige_belohnt(PLATZIERUNG)

	assert_bool(kern.schub_laeuft()).is_true()
	assert_float(kern.einkommen_pro_sekunde()).is_greater(vorher)


func test_sperrzeit_greift_nach_der_ersten_belohnung() -> void:
	# Ohne Sperrzeit koennte man Werbung am Stueck ansehen und den Schub
	# beliebig stapeln -- die Balance-Kurve waere hinfaellig.
	var stub: AdServiceStub = _stub()
	stub.zeige_belohnt(PLATZIERUNG)

	assert_float(stub.sperrzeit_rest(PLATZIERUNG)).is_greater(0.0)
	assert_bool(stub.ist_bereit(PLATZIERUNG)).is_false()


func test_zweiter_aufruf_waehrend_der_erste_laeuft_wird_abgewiesen() -> void:
	var stub: AdServiceStub = _stub()
	stub.dauer_sekunden = 60.0
	var abgewiesen: Array = []
	stub.nicht_verfuegbar.connect(func(_p: StringName, g: String) -> void:
		abgewiesen.append(g))
	stub.zeige_belohnt(PLATZIERUNG)
	stub.zeige_belohnt(PLATZIERUNG)
	assert_int(abgewiesen.size()).is_equal(1)


func test_unbekannte_platzierung_meldet_sich_statt_zu_schweigen() -> void:
	# Ein Tippfehler im Platzierungsnamen wuerde sonst als Knopf erscheinen,
	# der einfach nichts tut.
	var stub: AdServiceStub = _stub()
	var abgewiesen: Array = []
	stub.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void:
		abgewiesen.append(true))
	stub.zeige_belohnt(&"gibt_es_nicht")
	assert_int(abgewiesen.size()).is_equal(1)


func test_ladefehler_meldet_nicht_verfuegbar_statt_belohnung() -> void:
	var stub: AdServiceStub = _stub()
	stub.fehlerquote = 1.0
	var verdient: Array = []
	var abgewiesen: Array = []
	stub.belohnung_verdient.connect(func(_p: StringName) -> void: verdient.append(true))
	stub.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void:
		abgewiesen.append(true))
	stub.zeige_belohnt(PLATZIERUNG)
	assert_int(verdient.size()).is_equal(0)
	assert_int(abgewiesen.size()).is_equal(1)
	# Und der Fehlschlag darf keine Sperrzeit ausloesen -- der Spieler hat
	# nichts bekommen, also darf er es sofort nochmal versuchen.
	assert_float(stub.sperrzeit_rest(PLATZIERUNG)).is_equal_approx(0.0, 0.001)
