## Jede Station und jeder Raum jeder Welt hat eine erreichbare Tippflaeche UND eine
## Antwort (Geraetetest 15.10.: "in manche Zimmer komme ich nicht hinein").
##
## Die Treffer-Geometrie ist reine Rechnung (TrefferKarte): Hier wird mit der echten
## Kamerarichtung durch jede Zone und jede Station jeder Welt geschossen. Ausserdem
## muss jede Zone etwas ausloesen: ein Bereichs-Panel, das Start-Panel oder -- fuer
## Zonen ohne Kauf -- die Nebenraum-Karte aus theme.json.
extends GdUnitTestSuite

const TrefferKarte := preload("res://game/world/treffer_karte.gd")
const RICHTUNG: Vector3 = Vector3(-1.0, -1.0, -1.0)   ## Kamera: aus +x/+y/+z nach unten
## Mindestanteil der Bodenpunkte einer Zone, an denen der Tipp bei dieser Zone (oder
## einer Station darin) landet. Waende und Stationen der Nachbarn verdecken Teile.
const MIN_ANTEIL: float = 0.25


func _tippe(karte: RefCounted, ziel: Vector3) -> Dictionary:
	return karte.finde(ziel - RICHTUNG.normalized() * 40.0, RICHTUNG)


func test_jede_station_jeder_welt_ist_antippbar() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var stationen: Dictionary = welten.stationen_anzeige(i)
		assert_int(stationen.size()).is_greater(0)
		var karte: RefCounted = TrefferKarte.new()
		karte.bauen(stationen, welten.zonen(i), welten.waende(i))
		for id in stationen.keys():
			var t: Dictionary = _tippe(karte, (stationen[id] as Vector3) + Vector3(0.0, 0.8, 0.0))
			assert_str(String(t["art"])).override_failure_message(
				"%s: Station %s nicht antippbar" % [welten.id(i), id]).is_equal("station")
			assert_str(String(t["station"])).override_failure_message(
				"%s: Tipp auf %s landet bei %s" % [welten.id(i), id, t["station"]]).is_equal(String(id))


func test_jede_zone_jeder_welt_hat_eine_tippflaeche_und_eine_antwort() -> void:
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var welt_id: String = welten.id(i)
		var thema: ThemeData = ThemeData.laden(welt_id)
		var stationen: Dictionary = welten.stationen_anzeige(i)
		var karte: RefCounted = TrefferKarte.new()
		karte.bauen(stationen, welten.zonen(i), welten.waende(i))
		var start_id: String = String(welten.startzone(i).get("id", "-"))
		for eintrag in welten.zonen(i):
			var z: Dictionary = eintrag as Dictionary
			var zid: String = String(z.get("id", ""))
			# 1) Erreichbar: genug Bodenpunkte der Zone fuehren zu ihr.
			var summe: int = 0
			var treffer: int = 0
			var x: float = float(z["x1"])
			while x <= float(z["x2"]):
				var zz: float = float(z["z1"])
				while zz <= float(z["z2"]):
					summe += 1
					var t: Dictionary = _tippe(karte, Vector3(x, 0.0, zz))
					var gleiche_zone: bool = not (t["zone"] as Dictionary).is_empty() \
						and String((t["zone"] as Dictionary).get("id", "")) == zid
					var station_hier: bool = String(t["art"]) == "station" \
						and WorldData.zone_enthaelt(z, stationen[t["station"]] as Vector3, 0.5)
					if gleiche_zone or station_hier:
						treffer += 1
					zz += 1.0
				x += 1.0
			assert_float(float(treffer) / float(summe)).override_failure_message(
				"%s/%s: nur %d von %d Bodenpunkten fuehren zur Zone" % [welt_id, zid, treffer, summe]).is_greater_equal(MIN_ANTEIL)
			# 2) Antwort: Bereich, Start oder Nebenraum-Karte.
			var hat_antwort: bool = String(z.get("bereich", "")) != "" or zid == start_id \
				or not WeltTexte.nebenraum(thema, StringName(zid), "name").is_empty()
			assert_bool(hat_antwort).override_failure_message(
				"%s/%s: Tipp auf diesen Raum bewirkt nichts (kein Bereich, kein Start, kein Nebenraum-Text)" % [welt_id, zid]).is_true()


## K3 A2 (H5): Jede Tippflaeche auf der Karte -- Stationsschild, Pfeil, Raum-Plakette,
## Kaufchip, Rand-Tab -- ist in jeder Welt mindestens 96 x 96 logische px (48 dp) gross,
## auch wenn der sichtbare Aufkleber kleiner ist.
func test_jede_kartenmarke_jeder_welt_ist_mindestens_48_dp() -> void:
	var mindest: float = Kartenmarker.hinweis("tippziel_min_px")
	assert_float(mindest).is_greater_equal(96.0)
	var welten: WorldData = WorldData.laden()
	for i in welten.anzahl():
		var kern := GameCore.new(BalanceData.fuer_welt(welten.id(i)), i)
		var kamera: Camera3D = auto_free(Camera3D.new())
		kamera.projection = Camera3D.PROJECTION_ORTHOGONAL
		add_child(kamera)
		var m: Kartenmarker = auto_free(Kartenmarker.new())
		m.thema = ThemeData.laden(welten.id(i))
		add_child(m)
		var bereiche: Dictionary = welten.bereich_positionen(i)
		bereiche[Kartenmarker.START_RAUM] = Vector3.ZERO
		m.aufbauen(kern, kamera, welten.stationen_anzeige(i), bereiche)
		var flaechen: Array[Control] = m.tippflaechen()
		assert_int(flaechen.size()).is_greater(welten.stationen_anzeige(i).size())
		for f in flaechen:
			var groesse: Vector2 = f.get_combined_minimum_size()
			assert_bool(groesse.x >= mindest and groesse.y >= mindest).override_failure_message(
				"%s: Tippflaeche %s nur %s" % [welten.id(i), f.name, groesse]).is_true()
			assert_int(f.mouse_filter).is_equal(Control.MOUSE_FILTER_STOP)
