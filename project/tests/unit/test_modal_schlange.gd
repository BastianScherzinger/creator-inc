## K3 A3 (Befund M7) / K5 P1.7 / K6 1c: Immer nur ein Modal, Reihenfolge
## eroeffnung -> offline -> geschenk -> moment -> szene -> hinweis; nie zwei Fenster
## hintereinander ohne Spielzeit (abstand_s) bzw. Tipp (Moment) dazwischen.
extends GdUnitTestSuite


func _schlange() -> ModalSchlange:
	var s := ModalSchlange.new()
	s.verzoegert = false
	return s


func test_reihenfolge_nach_art_nicht_nach_anmeldung() -> void:
	var s := ModalSchlange.new()
	s.verzoegert = true     # gesammelt, wie im Spiel innerhalb eines Bildes
	var log: Array[String] = []
	var fertige: Dictionary = {}
	for art in [&"szene", &"moment", &"geschenk", &"offline"]:
		s.anmelden(art, func(fertig: Callable) -> void:
			log.append(String(art))
			fertige[art] = fertig)
	assert_bool(s.ist_offen()).is_false()
	s.naechstes()
	assert_array(log).contains_exactly(["offline"])
	(fertige[&"offline"] as Callable).call()
	s.naechstes()
	(fertige[&"geschenk"] as Callable).call()
	s.naechstes()
	(fertige[&"moment"] as Callable).call()
	s.naechstes()
	assert_array(log).contains_exactly(["offline", "geschenk", "moment", "szene"])


func test_nie_zwei_offen() -> void:
	var s := _schlange()
	var offen: Array[int] = [0]
	var max_offen: Array[int] = [0]
	var fertige: Array[Callable] = []
	for i in range(5):
		s.anmelden(&"szene", func(fertig: Callable) -> void:
			offen[0] += 1
			max_offen[0] = maxi(max_offen[0], offen[0])
			fertige.append(func() -> void:
				offen[0] -= 1
				fertig.call()))
	while not fertige.is_empty():
		var f: Callable = fertige.pop_front()
		f.call()
	assert_int(max_offen[0]).is_equal(1)
	assert_bool(s.ist_offen()).is_false()


func test_spaeter_wichtigeres_wartet_bis_offenes_zu_ist() -> void:
	var s := _schlange()
	var log: Array[String] = []
	var fertige: Dictionary = {}
	s.anmelden(&"szene", func(fertig: Callable) -> void:
		log.append("szene")
		fertige["szene"] = fertig)
	s.anmelden(&"offline", func(fertig: Callable) -> void:
		log.append("offline")
		fertige["offline"] = fertig)
	assert_array(log).contains_exactly(["szene"])
	assert_array(s.wartend()).contains_exactly([&"offline"])
	(fertige["szene"] as Callable).call()
	assert_array(log).contains_exactly(["szene", "offline"])


func test_doppeltes_fertig_schliesst_nicht_das_naechste() -> void:
	var s := _schlange()
	var fertige: Array[Callable] = []
	s.anmelden(&"offline", func(fertig: Callable) -> void: fertige.append(fertig))
	s.anmelden(&"moment", func(fertig: Callable) -> void: fertige.append(fertig))
	fertige[0].call()
	assert_str(String(s.offene_art())).is_equal("moment")
	fertige[0].call()     # alter Knopf noch einmal -- darf den Moment nicht schliessen
	assert_str(String(s.offene_art())).is_equal("moment")


func test_node_rueckgabe_schliesst_beim_verlassen_des_baums() -> void:
	var s := _schlange()
	var knoten := Node.new()
	var wurzel: Node = (Engine.get_main_loop() as SceneTree).root
	s.anmelden(&"offline", func() -> Node:
		wurzel.add_child(knoten)
		return knoten)
	assert_bool(s.ist_offen()).is_true()
	wurzel.remove_child(knoten)
	assert_bool(s.ist_offen()).is_false()
	knoten.free()


func test_null_rueckgabe_heisst_nichts_gezeigt() -> void:
	var s := _schlange()
	var log: Array[String] = []
	s.anmelden(&"geschenk", func() -> Node: return null)
	s.anmelden(&"szene", func(_f: Callable) -> void: log.append("szene"))
	assert_array(log).contains_exactly(["szene"])
	assert_str(String(s.offene_art())).is_equal("szene")


func test_verwerfen_entfernt_gestaute_szenen() -> void:
	var s := _schlange()
	s.anmelden(&"offline", func(_f: Callable) -> void: pass)
	s.anmelden(&"szene", func(_f: Callable) -> void: pass)
	s.anmelden(&"szene", func(_f: Callable) -> void: pass)
	assert_int(s.verwerfe(&"szene")).is_equal(2)
	assert_array(s.wartend()).is_empty()


func test_globale_schlange_ist_eine() -> void:
	var a := ModalSchlange.zuruecksetzen()
	assert_object(ModalSchlange.global()).is_same(a)


func test_moment_vor_szene_und_hinweis_zuletzt_kein_kapitel_mehr() -> void:
	var s := ModalSchlange.new()
	s.verzoegert = true
	for art in [&"hinweis", &"szene", &"moment", &"eroeffnung"]:
		s.anmelden(art, func(_f: Callable) -> void: pass)
	assert_array(s.wartend()).contains_exactly([&"eroeffnung", &"moment", &"szene", &"hinweis"])
	assert_bool(ModalSchlange.REIHENFOLGE.has(&"kapitel")).is_false()


func test_null_rueckgabe_zaehlt_nicht_als_fenster() -> void:
	var s := _schlange()
	var gezeigt: Array[String] = []
	s.gezeigt.connect(func(art: StringName) -> void: gezeigt.append(String(art)))
	s.anmelden(&"moment", func() -> Node: return null)
	s.anmelden(&"szene", func(_f: Callable) -> void: pass)
	assert_array(gezeigt).contains_exactly(["szene"])
	assert_int(s.anzahl_gezeigt()).is_equal(1)


func test_leichtes_modal_hoert_jede_anmeldung() -> void:
	var s := _schlange()
	var gehoert: Array[String] = []
	s.angemeldet.connect(func(art: StringName) -> void: gehoert.append(String(art)))
	var fertig_hinweis: Array[Callable] = []
	s.anmelden(&"hinweis", func(f: Callable) -> void: fertig_hinweis.append(f))
	s.anmelden(&"szene", func(_f: Callable) -> void: pass)
	assert_array(gehoert).contains_exactly(["hinweis", "szene"])
	assert_str(String(s.offene_art())).is_equal("hinweis")
	fertig_hinweis[0].call()
	assert_str(String(s.offene_art())).is_equal("szene")
	assert_bool(ModalSchlange.LEICHT.has(&"hinweis")).is_true()



# --- K6 1c: Abstand zwischen Fenstern ------------------------------------------------

func _mit_abstand() -> ModalSchlange:
	var s := _schlange()
	s.abstand_s = 20.0
	return s


func test_szene_nach_fenster_wartet_abstand_spielzeit() -> void:
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	var log: Array[String] = []
	s.anmelden(&"offline", func(f: Callable) -> void:
		log.append("offline")
		fertige.append(f))
	s.anmelden(&"szene", func(f: Callable) -> void:
		log.append("szene")
		fertige.append(f))
	fertige[0].call()
	assert_array(log).contains_exactly(["offline"])
	assert_bool(s.ist_offen()).is_false()
	s.ticke(19.0)
	assert_array(log).contains_exactly(["offline"])
	s.ticke(1.5)
	assert_array(log).contains_exactly(["offline", "szene"])


func test_spielzeit_laeuft_nicht_unter_offenem_fenster() -> void:
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	s.anmelden(&"offline", func(f: Callable) -> void: fertige.append(f))
	s.ticke(60.0)     # Fenster offen: zaehlt nicht
	fertige[0].call()
	assert_float(s.seit_letztem_fenster()).is_equal(0.0)


func test_raum_moment_nach_offline_wartet_auf_ersten_tipp() -> void:
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	var log: Array[String] = []
	s.anmelden(&"offline", func(f: Callable) -> void:
		log.append("offline")
		fertige.append(f))
	s.anmelden(&"moment", func(f: Callable) -> void:
		log.append("moment")
		fertige.append(f))
	fertige[0].call()
	s.ticke(100.0)
	assert_array(log).contains_exactly(["offline"])
	assert_bool(s.bereit_wartend()).is_false()
	s.melde_tipp()
	assert_array(log).contains_exactly(["offline", "moment"])


func test_nie_zwei_fenster_ohne_spieler_dazwischen() -> void:
	# Fuenf Szenen und ein Moment stauen sich: ohne Tipp und ohne Spielzeit kommt nach dem
	# ersten Fenster keins mehr.
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	for i in range(5):
		s.anmelden(&"szene", func(f: Callable) -> void: fertige.append(f))
	s.anmelden(&"moment", func(f: Callable) -> void: fertige.append(f))
	assert_int(s.anzahl_gezeigt()).is_equal(1)
	fertige[0].call()
	assert_int(s.anzahl_gezeigt()).is_equal(1)
	assert_bool(s.ist_offen()).is_false()


func test_vom_spieler_angetippt_kommt_ohne_abstand() -> void:
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	s.anmelden(&"offline", func(f: Callable) -> void: fertige.append(f))
	fertige[0].call()
	s.anmelden(&"szene", func(f: Callable) -> void: fertige.append(f), true)
	assert_str(String(s.offene_art())).is_equal("szene")


func test_eroeffnung_und_offline_ohne_abstand_hinweis_zaehlt_nicht() -> void:
	var s := _mit_abstand()
	var fertige: Array[Callable] = []
	s.anmelden(&"eroeffnung", func(f: Callable) -> void: fertige.append(f))
	s.anmelden(&"offline", func(f: Callable) -> void: fertige.append(f))
	fertige[0].call()
	assert_str(String(s.offene_art())).is_equal("offline")
	fertige[1].call()
	s.anmelden(&"hinweis", func(f: Callable) -> void: fertige.append(f))
	assert_str(String(s.offene_art())).is_equal("hinweis")
	assert_int(s.anzahl_gezeigt()).is_equal(2)


func test_abstand_steht_in_hinweise_json() -> void:
	assert_float(Kartenmarker.hinweis("fenster_abstand_s")).is_equal(20.0)


func test_sofort_erledigtes_startet_den_abstand_nicht_neu() -> void:
	# Eine gestaute, verworfene Szene (ruft fertig sofort) ist kein Fenster: Der Abstand laeuft weiter.
	var s := _mit_abstand()
	s.ticke(5.0)
	s.anmelden(&"geschenk", func(f: Callable) -> void: f.call())
	assert_float(s.seit_letztem_fenster()).is_greater(4.0)
	assert_int(s.anzahl_gezeigt()).is_equal(0)
