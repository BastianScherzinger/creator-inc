## Raum betreten (K2 6.2, P5c): Jeder Raum jeder Welt hat eine Raumkarte mit Name,
## Satz und -- gekauft -- dem, was er bringt; die Kamera rechnet einen Zoom, der in
## die Ansicht hineinfaehrt, und kennt den Rueckweg.
extends GdUnitTestSuite

const KameraSkript := preload("res://game/world/world_camera.gd")
const FLAECHE: Vector2 = Vector2(720.0, 1280.0)


func test_jeder_bereich_jeder_welt_hat_name_text_und_nutzen() -> void:
	for i in WorldData.laden().anzahl():
		var kern := GameCore.new(BalanceData.fuer_welt(WorldData.laden().id(i)), i)
		var thema: ThemeData = ThemeData.laden(kern.welt_id())
		for id in kern.bereiche.ids():
			var w: String = "%s/%s" % [kern.welt_id(), id]
			assert_str(WeltTexte.bereich(thema, id, "name")).override_failure_message(w + ": kein Name").is_not_empty()
			assert_str(WeltTexte.bereich(thema, id, "text")).override_failure_message(w + ": kein Satz").is_not_empty()
			# Was der Raum bringt: Bonus oder neue Station -- sonst weiss man nicht, wofuer man zahlt.
			assert_str(WeltTexte.bonus(thema, kern, id)).override_failure_message(w + ": bringt nichts Sichtbares").is_not_empty()
			assert_int(Menues.zonen_des_raums(kern, id).size()).override_failure_message(w + ": keine Zone").is_greater(0)


func test_raum_zoom_waechst_mit_der_raumgroesse_und_respektiert_die_daten() -> void:
	var klein: Dictionary = {"x1": 0, "x2": 3, "z1": 0, "z2": 4}
	var gross: Dictionary = {"x1": 0, "x2": 8, "z1": 0, "z2": 8}
	var z_klein: float = KameraSkript.raum_zoom(klein, FLAECHE, 600.0)
	var z_gross: float = KameraSkript.raum_zoom(gross, FLAECHE, 600.0)
	assert_float(z_klein).is_greater(0.0)
	assert_float(z_gross).is_greater(z_klein)
	# Ein niedrigeres Panel (weniger freie Hoehe) darf den Zoom nie verkleinern.
	assert_float(KameraSkript.raum_zoom(klein, FLAECHE, 200.0)).is_greater_equal(z_klein)
	var fest: Dictionary = {"x1": 0, "x2": 3, "z1": 0, "z2": 4, "zoom": 9.5}
	assert_float(KameraSkript.raum_zoom(fest, FLAECHE, 600.0)).is_equal(9.5)


func test_raum_zoom_jeder_zone_liegt_im_zoombereich_der_welt() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		for eintrag in welten.zonen(i):
			var z: float = KameraSkript.raum_zoom(eintrag as Dictionary, FLAECHE, 600.0)
			assert_float(z).override_failure_message("%s/%s: Zoom %.1f" % [
				welten.id(i), (eintrag as Dictionary).get("id", ""), z]).is_between(1.0, 80.0)


## K6 (Bastian 16.10.): Keine Rueckfahrt mehr -- nach dem Schliessen eines Menues bleibt die Kamera.
func test_kamera_faehrt_nach_dem_raum_nicht_zurueck() -> void:
	var kamera: Camera3D = auto_free(KameraSkript.new())
	add_child(kamera)
	assert_bool(kamera.hat_rueckkehr()).is_false()
	kamera.setze_welt_zoom(14.0)
	kamera.setze_blickpunkt(Vector3(1.0, 0.0, 2.0))
	kamera.betrete(Vector3(5.0, 0.8, -5.0), 400.0, 9.0)
	assert_bool(kamera.hat_rueckkehr()).is_false()
	assert_bool(kamera.kehre_zurueck()).is_false()


# --- K3 A3: Zoom-Stufen und Startblick ------------------------------------------------------

const OBEN: float = 170.0      ## wie main.gd START_OBEN
const UNTEN: float = 150.0     ## Menueleiste.HOEHE


func test_jede_welt_hat_zwei_stufen_im_zoombereich() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var roh: Dictionary = welten.welt(i).get("karte", {}) as Dictionary
		var karte: Dictionary = welten.karte(i)
		var stufen: Dictionary = roh.get("zoom_stufen", {}) as Dictionary
		var w: String = welten.id(i)
		assert_bool(stufen.has("raum") and stufen.has("ueberblick")).override_failure_message(w + ": zoom_stufen fehlen").is_true()
		var raum: float = float(stufen.get("raum", 0.0))
		var ueber: float = float(stufen.get("ueberblick", 0.0))
		assert_float(raum).override_failure_message(w + ": raum").is_between(float(karte["zoom_min"]), float(karte["zoom_max"]))
		assert_float(ueber).override_failure_message(w + ": ueberblick").is_between(float(karte["zoom_min"]), float(karte["zoom_max"]))
		assert_float(ueber).override_failure_message(w + ": ueberblick <= raum").is_greater(raum * 1.5)


func test_ueberblick_zeigt_die_ganze_karte() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var stufen: Dictionary = (welten.welt(i).get("karte", {}) as Dictionary).get("zoom_stufen", {}) as Dictionary
		if stufen.is_empty() or welten.zonen(i).is_empty():
			continue
		var ganz: Dictionary = KameraSkript.ansicht_fuer(welten.zonen(i), Vector2(720.0, 1600.0), OBEN, UNTEN)
		assert_float(float(ganz["zoom"])).override_failure_message("%s: ganze Karte braucht %.1f" % [
			welten.id(i), float(ganz["zoom"])]).is_less_equal(float(stufen["ueberblick"]) / 0.85)


## K3-Fix 1: Der Ueberblick zoomt naeher als "passt gerade so" (Karte gross statt leerer Himmel),
## aber nicht so nah, dass mehr als die Ecken der Karte fehlen.
func test_ueberblick_zeigt_die_karte_gross() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var stufen: Dictionary = (welten.welt(i).get("karte", {}) as Dictionary).get("zoom_stufen", {}) as Dictionary
		if stufen.is_empty() or welten.zonen(i).is_empty():
			continue
		var ganz: Dictionary = KameraSkript.ansicht_fuer(welten.zonen(i), Vector2(720.0, 1600.0), OBEN, UNTEN)
		assert_float(float(stufen["ueberblick"])).override_failure_message(welten.id(i) + ": Ueberblick nicht naeher als die ganze Karte").is_less(float(ganz["zoom"]))
		assert_float(float(stufen["ueberblick"])).override_failure_message(welten.id(i) + ": Ueberblick zu nah").is_greater(float(ganz["zoom"]) * 0.85)


## K3-Fix 2: Die Ansicht eines Raums zentriert die Mitte der Stationen (nicht des Raums).
func test_punkte_ansicht_zentriert_auf_die_stationen() -> void:
	var punkte: Array = [Vector3(0.0, 0.0, 0.0), Vector3(4.0, 0.0, 2.0)]
	var a: Dictionary = KameraSkript.punkte_ansicht(punkte, 2.0, Vector2(720.0, 1600.0), OBEN, UNTEN)
	assert_vector(a["mitte"] as Vector3).is_equal(Vector3(2.0, 0.0, 1.0))
	assert_float(float(a["zoom"])).is_greater(0.0)
	assert_bool(KameraSkript.punkte_ansicht([], 2.0, Vector2(720.0, 1600.0), OBEN, UNTEN).is_empty()).is_true()


## Startblick: Startraum + gekaufte Raeume + naechster Raum liegen ganz im freien
## Streifen -- fuer jede Welt und jeden Kaufstand, gemessen an der echten Kamera.
func test_startblick_zeigt_gekaufte_raeume_und_den_naechsten() -> void:
	var welten: WorldData = WorldData.laden()
	var kamera: Camera3D = auto_free(KameraSkript.new())
	add_child(kamera)
	var flaeche: Vector2 = kamera.get_viewport().get_visible_rect().size
	for i in welten.anzahl():
		if welten.zonen(i).is_empty():
			continue
		var karte: Dictionary = welten.karte(i)
		kamera.setze_grenzen(karte["grenzen"] as Rect2, float(karte["zoom_min"]), float(karte["zoom_max"]))
		var bereiche: Array[String] = []
		for eintrag in welten.zonen(i):
			var b: String = String((eintrag as Dictionary).get("bereich", ""))
			if b != "" and not bereiche.has(b):
				bereiche.append(b)
		for gekauft in range(bereiche.size() + 1):
			var zonen: Array = [welten.startzone(i)]
			for eintrag in welten.zonen(i):
				var b: String = String((eintrag as Dictionary).get("bereich", ""))
				if b != "" and bereiche.find(b) <= gekauft:
					zonen.append(eintrag)
			var ansicht: Dictionary = KameraSkript.ansicht_fuer(zonen, flaeche, OBEN, UNTEN)
			var wer: String = "%s, %d gekauft" % [welten.id(i), gekauft]
			assert_float(float(ansicht["zoom"])).override_failure_message(wer + ": Zoom ueber zoom_max").is_less_equal(float(karte["zoom_max"]))
			kamera.zeige_ansicht(ansicht["blick"] as Vector3, float(ansicht["zoom"]))
			for z in zonen:
				for x in [float(z["x1"]), float(z["x2"])]:
					for zz in [float(z["z1"]), float(z["z2"])]:
						var p: Vector2 = kamera.unproject_position(Vector3(x, 0.0, zz))
						assert_bool(p.x >= -1.0 and p.x <= flaeche.x + 1.0 and p.y >= OBEN - 1.0 and p.y <= flaeche.y - UNTEN + 1.0) \
							.override_failure_message("%s: Ecke %s (%s) liegt bei %s" % [wer, Vector2(x, zz), z.get("id", ""), p]).is_true()


func test_naechste_stufe_und_doppeltipp() -> void:
	var stufen: Dictionary = {&"raum": 16.0, &"ueberblick": 64.0}
	assert_str(String(KameraSkript.naechste_stufe(20.0, stufen))).is_equal("raum")
	assert_str(String(KameraSkript.naechste_stufe(31.0, stufen))).is_equal("raum")       # Mitte im Verhaeltnis: 32
	assert_str(String(KameraSkript.naechste_stufe(33.0, stufen))).is_equal("ueberblick")
	assert_str(String(KameraSkript.naechste_stufe(20.0, {}))).is_equal("")
	assert_bool(KameraSkript.ist_doppeltipp(1000, Vector2(100, 100), 1300, Vector2(120, 110))).is_true()
	assert_bool(KameraSkript.ist_doppeltipp(1000, Vector2(100, 100), 1500, Vector2(100, 100))).is_false()
	assert_bool(KameraSkript.ist_doppeltipp(1000, Vector2(100, 100), 1200, Vector2(300, 100))).is_false()


func test_stufen_wechsel_und_rasten() -> void:
	var kamera: Camera3D = auto_free(KameraSkript.new())
	add_child(kamera)
	kamera.setze_grenzen(Rect2(-10.0, -10.0, 20.0, 20.0), 10.0, 60.0)
	kamera.setze_stufen(16.0, 58.0)
	# Die Stufe folgt der Schwelle (K6), nicht der naechsten Raststufe.
	kamera.setze_welt_zoom(kamera.schwelle - 2.0)
	assert_str(String(kamera.stufe())).is_equal("raum")
	assert_str(String(kamera.doppeltipp_ziel())).is_equal("ueberblick")
	kamera.setze_welt_zoom(50.0)
	assert_str(String(kamera.doppeltipp_ziel())).is_equal("raum")
	# Stufen werden in den Zoombereich geklemmt.
	kamera.setze_stufen(4.0, 99.0)
	assert_float(float(kamera.stufen[&"raum"])).is_equal(10.0)
	assert_float(float(kamera.stufen[&"ueberblick"])).is_equal(60.0)
