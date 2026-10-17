## Lieferkiste und Stapel (K3 B2): die Arten der Tipp-Momente.
##
## Regeln: Kiste und Stapel wechseln sich ab, die Kiste zahlt Geld, der Stapel
## nur einen Schub (kein doppeltes Geld), der Schub schlaeft offline, und ein
## Spielstand traegt keinen halben Moment mit.
extends GdUnitTestSuite


func _system(extra: Dictionary = {}) -> MomentSystem:
	var p: Dictionary = {"aktiv": true, "abstand_min": 1.0, "abstand_max": 1.0, "dauer": 20.0,
		"belohnung_sekunden": 10.0, "belohnung_minimum": 0.0}
	p.merge(extra, true)
	return MomentSystem.new(p)


func _kandidaten(mit_kiste: bool = true) -> Array[StringName]:
	var k: Array[StringName] = [Ids.STATION_INTAKE, Ids.STATION_BUFFER]
	if mit_kiste:
		k.append(MomentSystem.KISTE)
	return k


func _kern() -> GameCore:
	return GameCore.new(BalanceData.fuer_welt("zimmer"), 0)


## Laesst den Kern laufen, bis ein Moment der gewuenschten Art steht.
func _warte_auf(kern: GameCore, art: StringName) -> void:
	kern.momente.erzwinge(art)
	for i in range(400):
		kern.tick(0.25)
		if kern.momente.laeuft() and kern.momente.art == art:
			return


func test_kiste_zuerst_dann_stapel_im_wechsel() -> void:
	var m := _system()
	m.stapel_ziel = Ids.STATION_BUFFER
	var arten: Array[StringName] = []
	for i in range(4):
		m.tick(1.5, _kandidaten())
		arten.append(m.art)
		m.tick(25.0, _kandidaten())   # verfaellt leise
	assert_array(arten).is_equal([MomentSystem.ART_KISTE, MomentSystem.ART_STAPEL,
		MomentSystem.ART_KISTE, MomentSystem.ART_STAPEL])


func test_stapel_steht_am_engpass() -> void:
	var m := _system()
	m.stapel_ziel = Ids.STATION_BUFFER
	m.erzwinge(MomentSystem.ART_STAPEL)
	m.tick(0.25, _kandidaten())
	assert_bool(m.ist_stapel()).is_true()
	assert_str(String(m.station)).is_equal(String(Ids.STATION_BUFFER))


func test_ohne_kiste_und_stapel_bleibt_die_blase() -> void:
	var m := _system()
	m.tick(1.5, _kandidaten(false))
	assert_str(String(m.art)).is_equal(String(MomentSystem.ART_BLASE))


func test_kiste_allein_ist_kein_kandidat() -> void:
	# Ohne arbeitende Station kommt auch keine Lieferung.
	var m := _system()
	var nur_kiste: Array[StringName] = [MomentSystem.KISTE]
	m.tick(5.0, nur_kiste)
	assert_bool(m.laeuft()).is_false()


func test_grosser_moment_bleibt_blase() -> void:
	var m := _system({"gross_chance": 1.0, "gross_sekunden": 100.0})
	m.tick(1.5, _kandidaten())
	assert_str(String(m.art)).is_equal(String(MomentSystem.ART_BLASE))
	assert_bool(m.gross).is_true()


func test_kiste_zahlt_und_zweite_stufe_dockt_an() -> void:
	var m := _system({"kiste_sekunden": 60.0})
	m.tick(1.5, _kandidaten())
	assert_bool(m.ist_kiste()).is_true()
	assert_float(m.belohnung(2.0)).is_equal_approx(120.0, 0.001)
	# Die zweite Stufe (Werbung, Welle C) ersetzt nur die Sekunden.
	assert_float(m.belohnung(2.0, 900.0)).is_equal_approx(1800.0, 0.001)
	assert_float(m.antippen(2.0)).is_equal_approx(120.0, 0.001)
	assert_str(String(m.letzte_art)).is_equal(String(MomentSystem.ART_KISTE))
	assert_bool(m.laeuft()).is_false()


func test_kiste_ohne_eigenen_wert_zahlt_wie_eine_blase() -> void:
	var m := _system()
	assert_float(m.kiste_sekunden).is_equal_approx(m.belohnung_sekunden, 0.001)


func test_stapel_zahlt_nie_geld() -> void:
	var m := _system({"stapel_schub_sekunden": 30.0})
	m.stapel_ziel = Ids.STATION_BUFFER
	m.erzwinge(MomentSystem.ART_STAPEL)
	m.tick(0.25, _kandidaten())
	assert_float(m.antippen(100.0)).is_equal(0.0)
	assert_bool(m.ist_stapel()).is_true()
	# Nur an der richtigen Station, und nur einmal.
	assert_float(m.stapel_antippen(Ids.STATION_INTAKE)).is_equal(0.0)
	assert_float(m.stapel_antippen(Ids.STATION_BUFFER)).is_equal_approx(30.0, 0.001)
	assert_float(m.stapel_antippen(Ids.STATION_BUFFER)).is_equal(0.0)
	assert_int(m.stapel_gesamt).is_equal(1)


func test_kern_stapel_gibt_schub_aber_kein_geld() -> void:
	var kern := _kern()
	_warte_auf(kern, MomentSystem.ART_STAPEL)
	assert_bool(kern.momente.ist_stapel()).is_true()
	assert_str(String(kern.momente.station)).is_equal(String(kern.kette.bottleneck()))
	var vorher: float = kern.kapital
	var schub_vorher: float = kern.schub_rest
	var sekunden: float = kern.tippe_stapel(kern.momente.station)
	assert_float(sekunden).is_greater(0.0)
	assert_float(kern.kapital).is_equal(vorher)
	assert_float(kern.schub_rest).is_equal_approx(schub_vorher + sekunden, 0.001)
	assert_bool(kern.schub_laeuft()).is_true()
	# Zweiter Tipp: nichts mehr da.
	assert_float(kern.tippe_stapel(kern.momente.station)).is_equal(0.0)


func test_kern_stapel_ohne_moment_ist_null() -> void:
	var kern := _kern()
	assert_float(kern.tippe_stapel(kern.kette.bottleneck())).is_equal(0.0)
	assert_bool(kern.schub_laeuft()).is_false()


func test_kern_kiste_zahlt_ueber_tippe_moment() -> void:
	var kern := _kern()
	_warte_auf(kern, MomentSystem.ART_KISTE)
	assert_bool(kern.momente.ist_kiste()).is_true()
	var vorher: float = kern.kapital
	var betrag: float = kern.tippe_moment()
	assert_float(betrag).is_greater(0.0)
	assert_float(kern.kapital).is_equal_approx(vorher + betrag, 0.001)


func test_stapel_schub_laesst_offline_ertrag_unberuehrt() -> void:
	var ohne := _kern()
	var mit := _kern()
	_warte_auf(ohne, MomentSystem.ART_STAPEL)
	_warte_auf(mit, MomentSystem.ART_STAPEL)
	assert_float(mit.tippe_stapel(mit.momente.station)).is_greater(0.0)
	var k_ohne: float = ohne.kapital
	var k_mit: float = mit.kapital
	var e_ohne: float = ohne.wende_offline_an(3600.0)
	var e_mit: float = mit.wende_offline_an(3600.0)
	assert_float(e_mit).is_equal_approx(e_ohne, 0.0001)
	assert_float(mit.kapital - k_mit).is_equal_approx(ohne.kapital - k_ohne, 0.0001)


func test_spielstand_traegt_schub_aber_keinen_halben_moment() -> void:
	var kern := _kern()
	_warte_auf(kern, MomentSystem.ART_STAPEL)
	kern.tippe_stapel(kern.momente.station)
	_warte_auf(kern, MomentSystem.ART_KISTE)
	assert_bool(kern.momente.ist_kiste()).is_true()
	var stand: SaveData = SaveData.from_dict(kern.to_save().to_dict())
	var neu := _kern()
	neu.from_save(stand)
	assert_bool(neu.momente.laeuft()).is_false()
	assert_int(neu.momente.angetippt_gesamt).is_equal(kern.momente.angetippt_gesamt)
	assert_float(neu.schub_rest).is_equal_approx(kern.schub_rest, 0.001)


func test_kiste_steht_in_jeder_welt_frei_in_der_startzone() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var ort: Vector3 = Lieferkiste.ort(welten, i)
		var start: Dictionary = welten.startzone(i)
		assert_bool(WorldData.zone_enthaelt(start, ort, 0.0)).override_failure_message(
			"%s: Kiste %s nicht in der Startzone" % [welten.id(i), ort]).is_true()
		var stationen: Dictionary = welten.stationen(i)
		for id in stationen.keys():
			var abstand: float = Vector2(ort.x, ort.z).distance_to(
				Vector2((stationen[id] as Vector3).x, (stationen[id] as Vector3).z))
			assert_float(abstand).override_failure_message(
				"%s: Kiste steht auf %s" % [welten.id(i), id]).is_greater(1.0)


## K4: In der Frueh-Phase kommen Momente dichter, danach gilt der normale Abstand.
func test_fruehphase_verkuerzt_den_abstand() -> void:
	var m := MomentSystem.new({"aktiv": true, "abstand_min": 90.0, "abstand_max": 90.0, "dauer": 20.0,
		"frueh_bis_s": 100.0, "frueh_abstand_min": 10.0, "frueh_abstand_max": 10.0})
	assert_float(m.naechster_abstand()).is_equal(10.0)
	var kandidaten: Array[StringName] = [&"station_intake"]
	m.tick(101.0, kandidaten)
	assert_float(m.naechster_abstand()).is_equal(90.0)


func test_ohne_fruehphase_bleibt_alles_wie_vorher() -> void:
	var m := MomentSystem.new({"aktiv": true, "abstand_min": 90.0, "abstand_max": 90.0})
	assert_float(m.naechster_abstand()).is_equal(90.0)
