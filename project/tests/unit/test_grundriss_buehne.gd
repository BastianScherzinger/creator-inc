## K3 A1 "Buehne": Die Karte besteht aus wenigen grossen Formen (K3_PLAN A1).
##
## Je Zone EINE Bodenplatte, Waende als Bloecke ohne Pfosten, gesperrte Raeume
## dunkel mit Silhouette statt Strichel und Kartons, Stationsplatten ohne
## Knoepfe und Wimpel. (A/B-Urteil 16.10.: nur noch diese Karte.)
extends GdUnitTestSuite


func _welten() -> WorldData:
	return WorldData.laden()


func _bauer(welten: WorldData, i: int) -> GrundrissBauer:
	var bauer: GrundrissBauer = auto_free(GrundrissBauer.new())
	bauer.bauen(welten.id(i), welten.zonen(i), welten.waende(i), welten.module(i))
	return bauer


func _kern(welten: WorldData, i: int) -> GameCore:
	return GameCore.new(BalanceData.fuer_welt(welten.id(i)), i)


func test_eine_bodenplatte_je_zone_in_jeder_welt() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		if not welten.hat_zonen(i):
			continue
		var bauer := _bauer(welten, i)
		for z in welten.zonen(i):
			var zone_id: String = String((z as Dictionary).get("id", ""))
			var boden: Node = bauer.get_node("Zone_%s/Boden" % zone_id)
			assert_int(boden.get_child_count()).override_failure_message(
				"%s/%s: %d Boden-Instanzen" % [welten.id(i), zone_id, boden.get_child_count()]).is_equal(1)
			assert_bool(boden.get_child(0) is MeshInstance3D).is_true()


func test_waende_ohne_pfosten_und_ohne_module() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		if not welten.hat_zonen(i):
			continue
		var bauer := _bauer(welten, i)
		var waende: Node = bauer.get_node("Waende")
		assert_int(waende.get_child_count()).is_greater(0)
		for kind in waende.get_children():
			var name: String = String(kind.name)
			assert_bool(name.begins_with("Block_") or name.begins_with("Kappe_") or name == "Fenster") \
				.override_failure_message("%s: unerwartetes Wandteil %s" % [welten.id(i), name]).is_true()
			assert_bool(name.to_lower().contains("pfosten")).is_false()
			var mm: MultiMesh = (kind as MultiMeshInstance3D).multimesh
			assert_bool(mm.mesh is BoxMesh).override_failure_message(
				"%s: %s ist kein Block" % [welten.id(i), name]).is_true()


func test_gesperrter_raum_zeigt_silhouette_statt_strichel_und_kartons() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		if not welten.hat_zonen(i):
			continue
		var kern := _kern(welten, i)
		var bauer := _bauer(welten, i)
		bauer.aktualisiere(kern)
		var stationen: Dictionary = welten.stationen(i)
		for z in welten.zonen(i):
			var zd: Dictionary = z as Dictionary
			var bereich := StringName(String(zd.get("bereich", "")))
			if bereich == &"" or kern.bereiche.ist_gekauft(bereich):
				continue
			var sperre: Node = bauer.get_node_or_null("Sperre_%s" % String(zd.get("id", "")))
			assert_object(sperre).override_failure_message("%s: keine Sperre" % welten.id(i)).is_not_null()
			# Keine Strichel, keine Kartons, kein Band -- nur Silhouetten.
			for kind in sperre.get_children():
				assert_str(String(kind.name)).starts_with("Silhouette_")
			for id in stationen.keys():
				var p: Vector3 = stationen[id] as Vector3
				var drin: bool = p.x >= float(zd["x1"]) - 0.5 and p.x <= float(zd["x2"]) + 0.5 \
					and p.z >= float(zd["z1"]) - 0.5 and p.z <= float(zd["z2"]) + 0.5
				var station: StationModel = kern.kette.station(StringName(id))
				if not drin or station == null or station.freigeschaltet:
					continue
				var silhouette: Node = sperre.get_node_or_null("Silhouette_%s" % String(id))
				assert_object(silhouette).override_failure_message(
					"%s: Silhouette fuer %s fehlt" % [welten.id(i), String(id)]).is_not_null()
				assert_int(silhouette.get_child_count()).is_greater(0)


func test_gesperrter_boden_hoechstens_60_prozent_so_hell() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		if not welten.hat_zonen(i):
			continue
		var kern := _kern(welten, i)
		var bauer := _bauer(welten, i)
		bauer.aktualisiere(kern)
		for z in welten.zonen(i):
			var zone_id: String = String((z as Dictionary).get("id", ""))
			if not bool(bauer._gesperrt.get(zone_id, false)):
				continue
			var mat: StandardMaterial3D = (bauer.get_node("Zone_%s/Boden/Platte" % zone_id) as MeshInstance3D).material_override as StandardMaterial3D
			var offen: Color = bauer._boden_farbe[zone_id] as Color
			assert_float(mat.albedo_color.get_luminance()).override_failure_message(
				"%s/%s zu hell" % [welten.id(i), zone_id]).is_less_equal(offen.get_luminance() * 0.6)


func test_jede_einrichtung_hat_eine_buehnen_datei() -> void:
	var welten := _welten()
	for i in range(welten.anzahl()):
		if not welten.hat_zonen(i):
			continue
		for z in welten.zonen(i):
			var zd: Dictionary = z as Dictionary
			if String(zd.get("einrichtung", "")).is_empty():
				continue
			for zustand in ["gesperrt", "verfuegbar", "gekauft"]:
				var datei: String = GrundrissBauer.einrichtung_fuer(zd, zustand) + GrundrissBauer.BUEHNE_DATEI
				var pfad: String = GrundrissBauer.WELT_PFAD % [welten.id(i), datei]
				assert_bool(ResourceLoader.exists(pfad)).override_failure_message(pfad + " fehlt").is_true()


func test_platte_mit_fase_hat_oberseite_bei_null() -> void:
	var mesh: ArrayMesh = GrundrissBauer.platten_mesh(4.0, 3.0, 0.06, 0.03)
	var aabb: AABB = mesh.get_aabb()
	assert_float(aabb.end.y).is_equal_approx(0.0, 0.001)
	assert_float(aabb.position.y).is_equal_approx(-0.06, 0.001)
	assert_float(aabb.size.x).is_equal_approx(4.0, 0.001)


func test_stationsplatte_stufe_ueber_farbe_und_groesse() -> void:
	var s0: Dictionary = Stationsplatte.buehne_stufe(0, 5)
	assert_float(float(s0["faktor"])).is_equal_approx(1.25, 0.001)
	assert_object(s0["farbe"]).is_null()
	var s3: Dictionary = Stationsplatte.buehne_stufe(3, 5)
	assert_float(float(s3["faktor"])).is_equal_approx(1.375, 0.001)
	assert_bool(s3["farbe"] == Stationsplatte.SILBER).is_true()
	var s5: Dictionary = Stationsplatte.buehne_stufe(5, 5)
	assert_bool(s5["farbe"] == Stationsplatte.GOLD).is_true()
	# Meister schon bei weniger moeglichen Sternen: Gold.
	assert_bool(Stationsplatte.buehne_stufe(2, 2)["farbe"] == Stationsplatte.GOLD).is_true()


func test_stationsplatte_ohne_knoepfe_und_wimpel() -> void:
	var platte: Stationsplatte = auto_free(Stationsplatte.new())
	var vorher: int = platte.get_child_count()
	platte.setze_sterne(3, 5)
	# Kein Stufen-Knoten mit Knoepfen und Pfosten.
	assert_int(platte.get_child_count()).is_equal(vorher)
