## Der Tipp trifft das, was man sieht (RELEASE_PLAN 2.A/2.B).
##
## Gerechnet wird mit der Kamerarichtung der Karte (aus +x/+y/+z nach unten) und
## den echten Zonen und Waenden der WG aus worlds.json.
extends GdUnitTestSuite

const TrefferKarte := preload("res://game/world/treffer_karte.gd")
const RICHTUNG: Vector3 = Vector3(-1.0, -1.0, -1.0)

var _welten: WorldData
var _karte: RefCounted


func before_test() -> void:
	_welten = WorldData.laden()
	_karte = TrefferKarte.new()
	_karte.bauen(_welten.stationen_anzeige(0), _welten.zonen(0), _welten.waende(0))


## Der Strahl, der den sichtbaren Punkt `ziel` trifft.
func _tippe(ziel: Vector3) -> Dictionary:
	var ursprung: Vector3 = ziel - RICHTUNG.normalized() * 40.0
	return _karte.finde(ursprung, RICHTUNG)


func _zone(treffer: Dictionary) -> String:
	return String((treffer["zone"] as Dictionary).get("id", ""))


func test_wandkrone_der_kueche_trifft_die_kueche() -> void:
	# Hintere Kuechenwand: 2,4 m hoch. Mit der Bodenebene fiel der Tipp aus der Karte.
	var t: Dictionary = _tippe(Vector3(0.5, 2.4, -9.5))
	assert_str(String(t["art"])).is_equal("zone")
	assert_str(_zone(t)).is_equal("kueche")


func test_mitte_der_kuechenrueckwand_trifft_die_kueche() -> void:
	assert_str(_zone(_tippe(Vector3(0.5, 1.4, -9.5)))).is_equal("kueche")


func test_fluremoebel_treffen_den_flur() -> void:
	var t: Dictionary = _tippe(Vector3(6.0, 0.8, -1.5))
	assert_str(String(t["art"])).is_equal("zone")
	assert_str(_zone(t)).is_equal("flur")


func test_kuechenboden_trifft_die_kueche() -> void:
	assert_str(_zone(_tippe(Vector3(0.5, 0.0, -6.0)))).is_equal("kueche")


func test_boden_hinter_der_halbhohen_wand_gehoert_der_wand() -> void:
	# Die Sichtlinie auf diesen Kuechenboden laeuft ueber die 1,2-m-Wand zum Flur.
	assert_str(_zone(_tippe(Vector3(-6.0, 0.0, -4.2)))).is_equal("flur")


func test_station_hat_vorrang_vor_dem_raum() -> void:
	var t: Dictionary = _tippe(Vector3(1.8, 0.9, 1.65))
	assert_str(String(t["art"])).is_equal("station")
	assert_str(String(t["station"])).is_equal("station_processing")


func test_station_ist_auch_in_der_hoehe_treffbar() -> void:
	# Oben auf dem Monitor, 1,4 m: die Bodenebene lag um 1,4 m daneben.
	var t: Dictionary = _tippe(Vector3(1.8, 1.4, 1.65))
	assert_str(String(t["station"])).is_equal("station_processing")


func test_startzimmer_wird_erkannt() -> void:
	assert_str(_zone(_tippe(Vector3(-2.5, 0.0, 6.0)))).is_equal("zimmer")


func test_ausserhalb_der_karte_trifft_nichts() -> void:
	var t: Dictionary = _tippe(Vector3(40.0, 0.0, 40.0))
	assert_str(String(t["art"])).is_equal("nichts")


func test_zone_an_nimmt_zuerst_das_innere() -> void:
	# x = -3,4 liegt im Rand des Zimmers (bis -3,5) und im Inneren des
	# Wohnzimmers erst bei z < -3,5; hier: Punkt im Rand beider -- das Innere gewinnt.
	# Flur z -3..0 (Boden bis -3,5), Kueche z -9..-4 (Boden bis -3,5): bei z = -3,6
	# liegt der Punkt im Inneren der Kueche und im Rand des Flurs.
	var z: Dictionary = _welten.zone_an(0, Vector3(0.0, 0.0, -3.6))
	assert_str(String(z.get("id", ""))).is_equal("kueche")
	# Und bei z = -3,4 im Inneren des Flurs (Rand der Kueche).
	z = _welten.zone_an(0, Vector3(0.0, 0.0, -3.4))
	assert_str(String(z.get("id", ""))).is_equal("flur")


func test_zone_der_station() -> void:
	assert_str(String(_welten.zone_der_station(0, &"station_intake").get("id", ""))).is_equal("zimmer")
	assert_str(String(_welten.zone_der_station(0, &"station_transport").get("id", ""))).is_equal("flur")
	assert_str(String(_welten.zone_der_station(0, &"station_special").get("id", ""))).is_equal("wohnzimmer")


func test_startzone_ist_das_zimmer() -> void:
	assert_str(String(_welten.startzone(0).get("id", ""))).is_equal("zimmer")
	assert_int(_welten.stationen_in_zone(0, _welten.startzone(0)).size()).is_equal(3)


func test_jede_welt_hat_eine_startzone() -> void:
	for i in range(_welten.anzahl()):
		assert_bool(_welten.startzone(i).is_empty()).override_failure_message("Welt %d" % i).is_false()
