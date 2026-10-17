## K5: Kapitel (Kern), Entscheidungen im Spielstand, Sammelfenster (P1.7) und
## Symbol-Erklaerung (P1.9) -- alles ohne SceneTree-Frames.
extends GdUnitTestSuite

const LISTE: Array = [
	{"id": "kapitel_1", "titel": "A", "ab_bereich": "", "aufgabe": "a", "entscheidung": "nachricht_05"},
	{"id": "kapitel_2", "titel": "B", "ab_bereich": "bereich_2", "aufgabe": "b", "entscheidung": "nachricht_06"},
	{"id": "kapitel_3", "titel": "C", "ab_bereich": "bereich_3", "aufgabe": "c", "entscheidung": "nachricht_09"},
	{"id": "kapitel_4", "titel": "D", "ab_bereich": "bereich_4", "aufgabe": "d", "entscheidung": "nachricht_11"},
]


func _kern() -> GameCore:
	var kern := GameCore.new(null, 0)
	kern.setze_kapitel(LISTE)
	return kern


func test_aktuelles_kapitel_ist_das_letzte_gekaufte() -> void:
	var k := KapitelSystem.new(LISTE)
	assert_int(k.anzahl()).is_equal(4)
	assert_int(k.index_fuer([])).is_equal(0)
	assert_int(k.index_fuer(["bereich_1"])).is_equal(0)
	assert_int(k.index_fuer(["bereich_1", "bereich_2"])).is_equal(1)
	# Reihenfolge der Kaeufe egal: Massgeblich ist das letzte Kapitel mit gekauftem Raum.
	assert_int(k.index_fuer(["bereich_4"])).is_equal(3)
	assert_int(KapitelSystem.new([]).index_fuer(["bereich_2"])).is_equal(-1)


func test_wechsel_nur_vorwaerts() -> void:
	assert_int(KapitelSystem.wechsel(0, 1)).is_equal(1)
	assert_int(KapitelSystem.wechsel(1, 1)).is_equal(-1)
	assert_int(KapitelSystem.wechsel(2, 1)).is_equal(-1)
	assert_int(KapitelSystem.wechsel(-1, -1)).is_equal(-1)


func test_entscheidung_gehoert_zum_kapitel() -> void:
	var k := KapitelSystem.new(LISTE)
	assert_str(k.kapitel_der_entscheidung("nachricht_06")).is_equal("kapitel_2")
	assert_str(k.kapitel_der_entscheidung("nachricht_07")).is_empty()
	assert_str(k.kapitel_der_entscheidung("")).is_empty()


func test_raumkauf_meldet_neues_kapitel_genau_einmal() -> void:
	var kern := _kern()
	var gemeldet: Array[int] = []
	kern.bus.chapter_started.connect(func(i: int) -> void: gemeldet.append(i))
	kern.kapital = 1.0e15
	for id in kern.bereiche.ids():
		kern.kaufe_bereich(id)
	assert_array(gemeldet).contains_exactly([1, 2, 3])
	assert_int(kern.kapitel_index()).is_equal(3)


func test_entscheidung_aendert_keine_wirtschaft_und_ueberlebt_den_spielstand() -> void:
	var kern := _kern()
	var einkommen: float = kern.einkommen_pro_sekunde()
	var kapital: float = kern.kapital
	assert_int(kern.entscheidung("kapitel_2")).is_equal(-1)
	kern.merke_entscheidung("kapitel_2", 1)
	kern.merke_entscheidung("kapitel_1", 0)
	assert_float(kern.einkommen_pro_sekunde()).is_equal(einkommen)
	assert_float(kern.kapital).is_equal(kapital)
	# Rundweg durch JSON: Zahlen kommen als float zurueck und muessen int werden.
	var text: String = JSON.stringify(kern.to_save().to_dict())
	var stand: SaveData = SaveData.from_dict(JSON.parse_string(text) as Dictionary)
	var schluessel: String = "%s/kapitel_2" % kern.welt_id()
	assert_bool(stand.entscheidungen.has(schluessel)).is_true()
	assert_bool(typeof(stand.entscheidungen[schluessel]) == TYPE_INT).is_true()
	var neu := _kern()
	neu.from_save(stand)
	assert_int(neu.entscheidung("kapitel_2")).is_equal(1)
	assert_int(neu.entscheidung("kapitel_1")).is_equal(0)


func test_alter_stand_ohne_neue_felder_laedt_fehlerfrei() -> void:
	var roh: Dictionary = _kern().to_save().to_dict()
	roh.erase("entscheidungen")
	roh.erase("hinweise")
	var stand: SaveData = SaveData.from_dict(roh)
	assert_dict(stand.entscheidungen).is_empty()
	assert_array(stand.hinweise).is_empty()
	var kern := _kern()
	kern.from_save(stand)
	assert_int(kern.entscheidung("kapitel_1")).is_equal(-1)


func test_kaputte_felder_werden_bereinigt() -> void:
	var roh: Dictionary = _kern().to_save().to_dict()
	roh["entscheidungen"] = {"x/kapitel_1": 7.0}
	roh["hinweise"] = ["kaufbar", 3]
	var stand: SaveData = SaveData.from_dict(roh)
	assert_int(int(stand.entscheidungen["x/kapitel_1"])).is_equal(1)
	assert_array(stand.hinweise).contains_exactly(["kaufbar", "3"])


## K6 1c: Nicht jedes Kapitel hat eine Entscheidung. Jede eingetragene verweist auf eine
## Szene mit zwei Antworten, und jede Welt hat mindestens eine.
func test_jede_welt_hat_vier_kapitel_und_entscheidungs_szenen() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var thema: ThemeData = ThemeData.laden(welten.id(i))
		var liste: Variant = thema.wert("kapitel")
		assert_bool(liste is Array).is_true()
		var k := KapitelSystem.new(liste as Array)
		assert_int(k.anzahl()).is_equal(4)
		var entscheidungen: int = 0
		for n in k.anzahl():
			var e: Dictionary = k.eintrag(n)
			assert_str(String(e.get("titel", ""))).is_not_empty()
			var id: String = String(e.get("entscheidung", ""))
			if id.is_empty():
				continue
			entscheidungen += 1
			var nachricht: Dictionary = WeltTexte.nachricht(thema, id)
			assert_bool(bool(nachricht.get("szene", false))).override_failure_message(
				"%s: %s ist keine Szene" % [welten.id(i), id]).is_true()
			assert_int((nachricht.get("antworten", []) as Array).size()).is_equal(2)
		assert_int(entscheidungen).override_failure_message("%s: keine Entscheidung" % welten.id(i)).is_greater_equal(1)


func test_symbol_hinweis_kommt_einmal_in_fester_reihenfolge() -> void:
	assert_str(SymbolHinweise.naechste([], [&"gesperrt", &"kaufbar"])).is_equal("kaufbar")
	assert_str(SymbolHinweise.naechste(["kaufbar"], [&"gesperrt", &"kaufbar"])).is_equal("gesperrt")
	assert_str(SymbolHinweise.naechste(["kaufbar", "gesperrt"], [&"gesperrt", &"kaufbar"])).is_empty()
	for art in SymbolHinweise.ARTEN:
		assert_bool(UiText.hat("symbol_" + String(art))).is_true()


func test_nur_der_raumkauf_ist_vollbild() -> void:
	var vollbild: Array = Kartenmarker.hinweise().get("vollbild_momente", []) as Array
	assert_array(vollbild).contains_exactly(["raum"])
