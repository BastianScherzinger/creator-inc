## K6 1c Fenster-Diaet: Ortsblase, Erklaerblasen-Zeitfenster, Raum-Menue-Liste,
## Kapitel ohne Fenster -- alles ohne SceneTree-Frames.
extends GdUnitTestSuite


func test_ortsblase_kuerzt_auf_hoechstens_n_zeichen_am_wortende() -> void:
	var lang: String = "Eins zwei drei vier fuenf sechs sieben acht neun zehn elf zwoelf dreizehn vierzehn fuenfzehn sechzehn siebzehn."
	var kurz: String = OrtsBlase.kuerze(lang, 90)
	assert_int(kurz.length()).is_less_equal(90)
	assert_bool(kurz.ends_with("…")).is_true()
	assert_str(OrtsBlase.kuerze("Kurz.", 90)).is_equal("Kurz.")


func test_ortsblase_schlange_hoechstens_zwei_und_verfall() -> void:
	var wartend: Array[Dictionary] = []
	for i in range(4):
		OrtsBlase.einreihen(wartend, {"id": "n%d" % i, "alter": 0.0}, 2)
	assert_int(wartend.size()).is_equal(2)
	assert_str(String(wartend[0]["id"])).is_equal("n2")
	OrtsBlase.altern(wartend, 19.0, 20.0)
	assert_int(wartend.size()).is_equal(2)
	OrtsBlase.altern(wartend, 1.5, 20.0)
	assert_int(wartend.size()).is_equal(0)


func test_ortsblase_weicht_plakette_nach_oben_aus() -> void:
	var groesse := Vector2(300.0, 80.0)
	var anker := Vector2(360.0, 700.0)
	# Ohne Hindernis: direkt ueber dem Anker.
	var frei: Vector2 = OrtsBlase.platz(anker, groesse, [], 200.0, 1100.0, 720.0, 16.0, 20.0)
	assert_float(frei.y).is_equal(700.0 - 80.0 - 20.0)
	# Plakette genau dort: die Blase steht darueber und schneidet sie nicht.
	var plakette := Rect2(Vector2(300.0, 560.0), Vector2(160.0, 90.0))
	var hindernisse: Array[Rect2] = [plakette]
	var p: Vector2 = OrtsBlase.platz(anker, groesse, hindernisse, 200.0, 1100.0, 720.0, 16.0, 20.0)
	assert_bool(p != Vector2.INF).is_true()
	assert_bool(Rect2(p, groesse).intersects(plakette)).is_false()
	assert_float(p.y + groesse.y).is_less_equal(plakette.position.y)


func test_ortsblase_weicht_unter_den_anker_aus_wenn_oben_voll() -> void:
	var groesse := Vector2(300.0, 80.0)
	var hindernisse: Array[Rect2] = [Rect2(Vector2(0.0, 150.0), Vector2(720.0, 400.0))]
	var p: Vector2 = OrtsBlase.platz(Vector2(360.0, 500.0), groesse, hindernisse, 200.0, 1100.0, 720.0, 16.0, 20.0)
	assert_bool(p != Vector2.INF).is_true()
	assert_float(p.y).is_greater_equal(550.0)
	assert_bool(Rect2(p, groesse).intersects(hindernisse[0])).is_false()


func test_ortsblase_wartet_wenn_nirgends_platz() -> void:
	var groesse := Vector2(300.0, 80.0)
	var hindernisse: Array[Rect2] = [Rect2(Vector2(0.0, 150.0), Vector2(720.0, 1000.0))]
	var p: Vector2 = OrtsBlase.platz(Vector2(360.0, 500.0), groesse, hindernisse, 200.0, 1100.0, 720.0, 16.0, 20.0)
	assert_bool(p == Vector2.INF).is_true()


func test_ortsblase_werte_aus_hinweise_json() -> void:
	assert_float(Kartenmarker.hinweis("blase_dauer_s")).is_equal(4.0)
	assert_int(int(Kartenmarker.hinweis("blasen_max"))).is_equal(2)
	assert_int(int(Kartenmarker.hinweis("blase_zeichen_max"))).is_equal(90)
	assert_float(Kartenmarker.hinweis("kapitel_glanz_s")).is_less_equal(2.0)


func test_erklaerblasen_nur_im_tutorial_oder_in_den_ersten_minuten() -> void:
	var bis: float = Kartenmarker.hinweis("symbol_blase_bis_s")
	assert_float(bis).is_greater(0.0)
	assert_bool(Hud.symbol_erlaubt(true, bis * 10.0, bis)).is_true()
	assert_bool(Hud.symbol_erlaubt(false, bis * 0.5, bis)).is_true()
	assert_bool(Hud.symbol_erlaubt(false, bis + 1.0, bis)).is_false()


func test_raum_menue_liste_enthaelt_alle_kaeufe_billigste_zuerst() -> void:
	var kern := GameCore.new(null, 0)
	var liste: Array[Dictionary] = kern.kaeufe_im_raum(Kartenmarker.START_RAUM)
	assert_int(liste.size()).is_greater(0)
	for i in range(1, liste.size()):
		assert_float(float(liste[i]["preis"])).is_greater_equal(float(liste[i - 1]["preis"]))
	# Die Empfehlung ist einer davon.
	var e: Dictionary = kern.empfehlung_im_raum(Kartenmarker.START_RAUM)
	var gefunden: bool = false
	for k in liste:
		if String(k["art"]) == String(e["art"]) and String(k["station"]) == String(e["station"]) \
				and String(k["platz"]) == String(e["platz"]):
			gefunden = true
	assert_bool(gefunden).is_true()


func test_kapitelwechsel_meldet_kein_fenster() -> void:
	var kern := GameCore.new(null, 0)
	var schlange := ModalSchlange.zuruecksetzen()
	schlange.verzoegert = false
	kern.kapital = 1.0e15
	for id in kern.bereiche.ids():
		kern.kaufe_bereich(id)
	assert_array(schlange.wartend()).not_contains([&"kapitel"])
	assert_bool(ModalSchlange.REIHENFOLGE.has(&"kapitel")).is_false()


func test_pc_steuerung_zahl_in_exponentenschreibweise() -> void:
	assert_str(PcSteuerung._zahl(1234.5)).is_equal("1234.5")
	assert_str(PcSteuerung._zahl(4.322e7)).is_equal("4.322e+7")
	assert_str(PcSteuerung._zahl(9.9999e14)).is_equal("1.000e+15")
