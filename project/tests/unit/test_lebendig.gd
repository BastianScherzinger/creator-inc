## Lebendigkeits-System: der Daten-Parser (fehlende Schluessel, falsche Typen,
## beide Schreibweisen, Obergrenzen) und der Lauf der Animationen.
## Kein Schluessel darf je einen Fehler ausloesen -- was nicht lesbar ist, ist leer.
extends GdUnitTestSuite

var _regeln: Dictionary


func before_test() -> void:
	_regeln = LebendigDaten.laden_regeln()


# --- Himmel -----------------------------------------------------------------

func test_ohne_himmel_ist_leer() -> void:
	assert_bool(LebendigDaten.himmel({}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.himmel({"himmel": null}, _regeln).is_empty()).is_true()


func test_himmel_falsche_typen_sind_leer() -> void:
	assert_bool(LebendigDaten.himmel({"himmel": 5}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.himmel({"himmel": "blau"}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.himmel({"himmel": {"oben": 3, "unten": [1]}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.himmel({"himmel": {"oben": "kein_hex"}}, _regeln).is_empty()).is_true()


func test_himmel_beide_schreibweisen() -> void:
	var a: Dictionary = LebendigDaten.himmel({"himmel": {"oben": "112233", "unten": "#445566"}}, _regeln)
	var b: Dictionary = LebendigDaten.himmel({"himmel": {"zenit": "112233", "horizont": "445566"}}, _regeln)
	var c: Dictionary = LebendigDaten.himmel({"himmel": ["112233", "445566"]}, _regeln)
	for h in [a, b, c]:
		assert_bool((h as Dictionary)["oben"] == Color("112233")).is_true()
		assert_bool((h as Dictionary)["unten"] == Color("445566")).is_true()


func test_himmel_nur_eine_farbe_genuegt() -> void:
	var h: Dictionary = LebendigDaten.himmel({"himmel": {"oben": "ff0000"}}, _regeln)
	assert_bool(h["unten"] == Color("ff0000")).is_true()


func test_sterne_sind_gedeckelt_und_mond_optional() -> void:
	var h: Dictionary = LebendigDaten.himmel({"himmel": {"oben": "000000", "sterne": 100000, "mond": true}}, _regeln)
	assert_int(int((h["sterne"] as Dictionary)["anzahl"])).is_equal(LebendigDaten.grenze(_regeln, "max_sterne"))
	assert_bool((h["mond"] as Dictionary).is_empty()).is_false()
	var ohne: Dictionary = LebendigDaten.himmel({"himmel": {"oben": "000000", "sterne": "viele", "mond": "ja"}}, _regeln)
	assert_bool((ohne["sterne"] as Dictionary).is_empty()).is_true()
	assert_bool((ohne["mond"] as Dictionary).is_empty()).is_true()


# --- Glow -------------------------------------------------------------------

func test_glow_nur_wenn_gesetzt() -> void:
	assert_bool(LebendigDaten.glow({}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.glow({"glow": false}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.glow({"glow": "an"}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.glow({"glow": 0}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.glow({"glow": true}, _regeln).is_empty()).is_false()
	assert_float(float(LebendigDaten.glow({"glow": 0.4}, _regeln)["intensitaet"])).is_equal_approx(0.4, 0.001)


func test_glow_werte_werden_begrenzt() -> void:
	var g: Dictionary = LebendigDaten.glow({"glow": {"intensitaet": 99, "intensity_x": 1, "schwelle": -3}}, _regeln)
	assert_float(float(g["intensitaet"])).is_less_equal(2.0)
	assert_float(float(g["schwelle"])).is_greater_equal(0.0)


# --- Partikel ---------------------------------------------------------------

func test_partikel_ungueltige_eintraege_fallen_weg() -> void:
	var quelle: Array = [5, "x", {}, {"typ": 7}, {"typ": "gibtsnicht"}, {"typ": "staub", "x": 1.0, "z": 2.0, "menge": 4}]
	var liste: Array[Dictionary] = LebendigDaten.partikel([quelle, "kaputt", null], _regeln)
	assert_int(liste.size()).is_equal(1)
	assert_str(String(liste[0]["typ"])).is_equal("staub")
	assert_float(float(liste[0]["x"])).is_equal(1.0)


func test_partikel_menge_und_systeme_gedeckelt() -> void:
	var quelle: Array = []
	for i in 50:
		quelle.append({"typ": "dampf", "menge": 100000})
	var liste: Array[Dictionary] = LebendigDaten.partikel([quelle], _regeln)
	assert_int(liste.size()).is_equal(LebendigDaten.grenze(_regeln, "max_partikel_systeme"))
	assert_int(int(liste[0]["menge"])).is_equal(LebendigDaten.grenze(_regeln, "max_partikel_menge"))


func test_partikel_alias_und_art() -> void:
	var liste: Array[Dictionary] = LebendigDaten.partikel([[{"art": "Rauch"}, {"typ": "Vögel"}]], _regeln)
	assert_int(liste.size()).is_equal(2)
	assert_str(String(liste[0]["typ"])).is_equal("dampf")
	assert_str(String(liste[1]["typ"])).is_equal("voegel")


# --- Animation --------------------------------------------------------------

func test_animation_fehlt_oder_kaputt_ist_leer() -> void:
	assert_bool(LebendigDaten.animation({}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": 3}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": {"typ": "fliegen"}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": {"tempo": 2}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": []}, _regeln).is_empty()).is_true()


func test_animation_standardwerte_aus_den_daten() -> void:
	var a: Dictionary = LebendigDaten.animation({"animation": {"typ": "drehen"}}, _regeln)
	assert_str(String(a["typ"])).is_equal("drehen")
	assert_bool(a["achse"] == Vector3.UP).is_true()
	assert_float(float(a["tempo"])).is_equal(float(((_regeln["animation"] as Dictionary)["drehen"] as Dictionary)["tempo"]))


func test_animation_text_statt_dictionary_und_alias() -> void:
	assert_str(String(LebendigDaten.animation({"animation": "wippen"}, _regeln)["typ"])).is_equal("wackeln")
	assert_str(String(LebendigDaten.animation({"animation": [5, {"typ": "driften"}]}, _regeln)["typ"])).is_equal("treiben")


func test_animation_achse_formen() -> void:
	assert_bool(LebendigDaten.achse("x", Vector3.UP) == Vector3.RIGHT).is_true()
	assert_bool(LebendigDaten.achse([0, 0, 2], Vector3.UP) == Vector3.BACK).is_true()
	assert_bool(LebendigDaten.achse({"x": 0, "y": 0, "z": -1}, Vector3.UP) == Vector3.FORWARD).is_true()
	assert_bool(LebendigDaten.achse("quer", Vector3.UP) == Vector3.UP).is_true()
	assert_bool(LebendigDaten.achse([0, 0, 0], Vector3.UP) == Vector3.UP).is_true()
	assert_bool(LebendigDaten.achse(7, Vector3.UP) == Vector3.UP).is_true()


func test_fahren_braucht_zwei_gueltige_punkte() -> void:
	assert_bool(LebendigDaten.animation({"animation": {"typ": "fahren"}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": {"typ": "fahren", "route": [{"x": 1, "z": 1}]}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.animation({"animation": {"typ": "fahren", "route": [{"x": "a", "z": 1}, {"x": 2, "z": 2}]}}, _regeln).is_empty()).is_true()
	var ok: Dictionary = LebendigDaten.animation({"animation": {"typ": "fahren", "route": [{"x": 0, "z": 0, "warten": 3}, [4, 0], {"x": 4, "z": 4}]}}, _regeln)
	assert_int((ok["route"] as PackedVector3Array).size()).is_equal(3)
	assert_float((ok["warten"] as PackedFloat32Array)[0]).is_equal(3.0)
	assert_str(String(ok["modus"])).is_equal("schleife")


func test_fahren_unbekannter_modus_wird_schleife() -> void:
	var a: Dictionary = LebendigDaten.animation({"animation": {"typ": "fahren", "modus": 4, "route": [[0, 0], [1, 1]]}}, _regeln)
	assert_str(String(a["modus"])).is_equal("schleife")


# --- Emission-Puls ----------------------------------------------------------

func test_puls_formen() -> void:
	assert_bool(LebendigDaten.emission_puls({}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.emission_puls({"emission_puls": "ja"}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.emission_puls({"emission_puls": false}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.emission_puls({"emission_puls": {"hz": 0}}, _regeln).is_empty()).is_true()
	assert_bool(LebendigDaten.emission_puls({"emission_puls": true}, _regeln).is_empty()).is_false()
	assert_float(float(LebendigDaten.emission_puls({"emission_puls": 2.0}, _regeln)["hz"])).is_equal(2.0)


func test_puls_max_nie_kleiner_als_min() -> void:
	var p: Dictionary = LebendigDaten.emission_puls({"emission_puls": {"hz": 1, "min": 3, "max": 1}}, _regeln)
	assert_float(float(p["max"])).is_greater_equal(float(p["min"]))


func test_puls_unlesbare_farbe_ist_keine_farbe() -> void:
	var p: Dictionary = LebendigDaten.emission_puls({"emission_puls": {"farbe": 12}}, _regeln)
	assert_bool(bool(p["mit_farbe"])).is_false()
	var q: Dictionary = LebendigDaten.emission_puls({"emission_puls": {"farbe": "8b5cf6"}}, _regeln)
	assert_bool(bool(q["mit_farbe"])).is_true()


# --- Regeln -----------------------------------------------------------------

func test_regeldatei_fehlt_dann_gelten_die_grenzen_des_notfalls() -> void:
	var r: Dictionary = LebendigDaten.laden_regeln("res://gibt_es_nicht.json")
	assert_int(LebendigDaten.grenze(r, "max_animiert")).is_greater(0)
	assert_bool(LebendigDaten.animation({"animation": {"typ": "drehen"}}, r).is_empty()).is_false()


# --- Lauf -------------------------------------------------------------------

func _kulisse_mit_mesh() -> Node3D:
	var k := Node3D.new()
	var m := MeshInstance3D.new()
	m.mesh = BoxMesh.new()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.2, 0.4, 0.8)
	m.set_surface_override_material(0, mat)
	k.add_child(m)
	return k


func test_ohne_daten_passiert_nichts() -> void:
	var l := Lebendig.new()
	var k: Node3D = _kulisse_mit_mesh()
	l.baue_kulisse([{"datei": "x"}, 5, null], [k, null, k])
	l.baue_partikel([null, 3, "x"])
	assert_bool(l.is_processing()).is_false()
	assert_int(int(l.zaehler()["animiert"])).is_equal(0)
	l.free()
	k.free()


func test_animationen_laufen_und_sind_gedeckelt() -> void:
	var l := Lebendig.new()
	var eintraege: Array = []
	var knoten: Array = []
	for i in 60:
		eintraege.append({"datei": "x", "animation": {"typ": "treiben", "achse": "x", "tempo": 1.0, "weite": 2.0}})
		knoten.append(_kulisse_mit_mesh())
	l.baue_kulisse(eintraege, knoten)
	assert_int(int(l.zaehler()["animiert"])).is_equal(LebendigDaten.grenze(_regeln, "max_animiert"))
	assert_bool(l.is_processing()).is_true()
	var k: Node3D = knoten[0] as Node3D
	var vorher: Vector3 = k.position
	l._process(0.1)
	l._process(0.1)
	assert_bool(k.position.is_equal_approx(vorher)).is_false()
	l.free()
	for n in knoten:
		(n as Node).free()


func test_puls_aendert_die_helligkeit_und_dupliziert_das_material() -> void:
	var l := Lebendig.new()
	var k: Node3D = _kulisse_mit_mesh()
	var original: Material = (k.get_child(0) as MeshInstance3D).get_active_material(0)
	l.baue_kulisse([{"emission_puls": {"hz": 1.0, "min": 0.0, "max": 2.0}}], [k])
	assert_int(int(l.zaehler()["puls"])).is_equal(1)
	var mat: StandardMaterial3D = (k.get_child(0) as MeshInstance3D).get_active_material(0) as StandardMaterial3D
	assert_bool(mat.emission_enabled).is_true()
	l._process(0.1)
	var a: float = mat.emission_energy_multiplier
	l._process(0.2)
	assert_bool(is_equal_approx(a, mat.emission_energy_multiplier)).is_false()
	l.free()
	k.free()
	assert_object(original).is_not_null()


func test_fahrzeug_faehrt_die_route() -> void:
	var l := Lebendig.new()
	var k := Node3D.new()
	l.baue_kulisse([{"animation": {"typ": "fahren", "tempo": 2.0, "modus": "einmal", "pause": 1.0,
		"route": [{"x": 0, "z": 0}, {"x": 0, "z": 4}]}}], [k])
	assert_int(int(l.zaehler()["fahrzeuge"])).is_equal(1)
	for i in 10:
		l._process(0.1)
	assert_float(k.position.z).is_between(1.5, 2.5)
	for i in 15:
		l._process(0.1)
	assert_bool(k.visible).is_false()
	for i in 20:
		l._process(0.1)
	assert_bool(k.visible).is_true()
	l.free()
	k.free()
