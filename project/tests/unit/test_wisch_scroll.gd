## Menues lassen sich auf dem Handy wischen (Geraetetest 15.10.).
##
## Ein Control mit mouse_filter STOP schluckt den Wisch -- der ScrollContainer
## dahinter bekommt ihn nie. Alle Scroll-Bereiche sind deshalb WischScroll; er stellt
## alle Nachfahren von STOP auf PASS (auch spaeter eingehaengte Zeilen).
extends GdUnitTestSuite


func _hud() -> Hud:
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	kern.kapital = 1.0e9
	var thema: ThemeData = ThemeData.laden("zimmer")
	var audio: AudioDirector = auto_free(AudioDirector.new())
	add_child(audio)
	var hud: Hud = auto_free(Hud.new())
	add_child(hud)
	hud.aufbauen(kern, thema, audio, auto_free(AdServiceStub.new()))
	return hud


func _sammle(wurzel: Node, ausgabe: Array[Node]) -> void:
	ausgabe.append(wurzel)
	for k in wurzel.get_children():
		_sammle(k, ausgabe)


func _pruefe_menues(hud: Hud) -> int:
	var alle: Array[Node] = []
	_sammle(hud, alle)
	var rahmen: int = 0
	for n in alle:
		assert_bool(n is ScrollContainer and not (n is WischScroll)).override_failure_message(
			"%s ist ein einfacher ScrollContainer -- WischScroll nehmen" % hud.get_path_to(n)).is_false()
		if n is WischScroll:
			rahmen += 1
			var unter: Array[Node] = []
			_sammle(n, unter)
			for u in unter:
				if u == n or not (u is Control):
					continue
				assert_int((u as Control).mouse_filter).override_failure_message(
					"%s (%s) steht auf STOP und schluckt den Wisch" % [hud.get_path_to(u), u.get_class()]
					).is_not_equal(Control.MOUSE_FILTER_STOP)
	return rahmen


func test_alle_menues_haben_wischbare_scrollbereiche() -> void:
	var hud: Hud = _hud()
	hud.aktualisiere()
	hud.zeige_station(Ids.CHAIN[0])
	var n1: int = _pruefe_menues(hud)
	hud._oeffne(hud.zielemenue)
	hud._oeffne(hud.handymenue)
	hud._oeffne(hud.ausbaumenue)
	hud.zeige_bereich(&"bereich_1")
	hud.zeige_bereich(Menues.START_RAUM)
	hud.zeige_nebenraum(&"bad")
	var n2: int = _pruefe_menues(hud)
	assert_int(n1).is_greater_equal(1)
	assert_int(n2).is_greater_equal(4)


func test_knoepfe_im_scrollbereich_bleiben_antippbar() -> void:
	var rahmen := WischScroll.new()
	add_child(rahmen)
	var liste := VBoxContainer.new()
	rahmen.add_child(liste)
	var knopf := Button.new()
	liste.add_child(knopf)   # spaeter eingehaengt, wie bei neu gebauten Menuezeilen
	assert_int(knopf.mouse_filter).is_equal(Control.MOUSE_FILTER_PASS)
	var zaehler: Array[int] = [0]
	knopf.pressed.connect(func() -> void: zaehler[0] += 1)
	knopf.pressed.emit()
	assert_int(zaehler[0]).is_equal(1)
	rahmen.queue_free()


func test_kein_einfacher_scrollcontainer_im_quelltext() -> void:
	var gefunden: Array[String] = []
	var verzeichnisse: Array[String] = ["res://game"]
	while not verzeichnisse.is_empty():
		var pfad: String = verzeichnisse.pop_back()
		for datei in DirAccess.get_files_at(pfad):
			if not datei.ends_with(".gd") or datei == "wisch_scroll.gd":
				continue
			if FileAccess.get_file_as_string(pfad + "/" + datei).contains("ScrollContainer.new()"):
				gefunden.append(pfad + "/" + datei)
		for unter in DirAccess.get_directories_at(pfad):
			verzeichnisse.append(pfad + "/" + unter)
	assert_array(gefunden).override_failure_message("ScrollContainer.new() statt WischScroll.new(): %s" % [gefunden]).is_empty()
