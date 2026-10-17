## Nur das drehende Teil dreht sich -- in allen sechs Welten.
##
## Fehler (Geraetetest 15.10.): Im Flur von Welt 5 drehte sich der ganze Rahmen
## der Luefterwand mit. Ursache: Die Teilesuche nahm `contains("luefter")` und traf
## so auch "welt_luefter_rahmen". Hier wird mit den echten Modellen geprueft, dass
## jeder per Daten gedrehte Knoten ein Blatt-Teil ist: nicht die Wurzel, nicht
## groesser als das halbe Modell, und sein Mittelpunkt liegt auf der Drehachse.
extends GdUnitTestSuite

const MAX_ABWEICHUNG: float = 0.35   ## Mittelpunkt hoechstens so weit (Anteil der Teilgroesse) neben der Achse


func _modell(welt_id: String, datei: String) -> Node3D:
	for pfad in ["res://assets/world/%s/%s.glb" % [welt_id, datei], "res://assets/world/gemeinsam/%s.glb" % datei]:
		if ResourceLoader.exists(pfad):
			return (load(pfad) as PackedScene).instantiate() as Node3D
	return null


## AABB aller Meshes unterhalb von `wurzel`, im lokalen Raum von `bezug`.
func _aabb(wurzel: Node, bezug: Node3D) -> AABB:
	var ergebnis := AABB()
	var erstes: bool = true
	var liste: Array[Node] = [wurzel]
	while not liste.is_empty():
		var n: Node = liste.pop_back()
		for kind in n.get_children():
			liste.append(kind)
		var m := n as MeshInstance3D
		if m == null or m.mesh == null:
			continue
		# Transform von m relativ zu bezug.
		var t: Transform3D = Transform3D.IDENTITY
		var k: Node = m
		while k != null and k != bezug:
			if k is Node3D:
				t = (k as Node3D).transform * t
			k = k.get_parent()
		var box: AABB = t * m.mesh.get_aabb()
		ergebnis = box if erstes else ergebnis.merge(box)
		erstes = false
	return ergebnis


func test_gedrehte_knoten_sind_nur_das_drehende_teil() -> void:
	var regeln: Dictionary = LebendigDaten.laden_regeln()
	var welten: WorldData = WorldData.laden()
	var geprueft: int = 0
	for i in welten.anzahl():
		var welt_id: String = welten.id(i)
		for eintrag in (welten.welt(i).get("kulisse", []) as Array):
			var e: Dictionary = eintrag as Dictionary
			var anim: Dictionary = LebendigDaten.animation(e, regeln)
			if anim.is_empty() or String(anim["typ"]) != "drehen":
				continue
			var datei: String = String(e.get("datei", ""))
			var modell: Node3D = _modell(welt_id, datei)
			assert_object(modell).override_failure_message("%s/%s: Modell fehlt" % [welt_id, datei]).is_not_null()
			if modell == null:
				continue
			add_child(modell)
			var l := Lebendig.new()
			l.baue_kulisse([e], [modell])
			var gedreht: Array[Node3D] = l._a_knoten
			assert_int(gedreht.size()).override_failure_message(
				"%s/%s: 'drehen' trifft keinen Knoten (teil '%s')" % [welt_id, datei, String(anim["teil"])]).is_greater(0)
			var ganz: AABB = _aabb(modell, modell)
			for k in gedreht:
				geprueft += 1
				var wo: String = "%s/%s -> Knoten '%s'" % [welt_id, datei, String(k.name)]
				assert_bool(k != modell).override_failure_message(wo + ": das ganze Modell dreht sich").is_true()
				var teil: AABB = _aabb(k, k)
				var achse: Vector3 = anim["achse"] as Vector3
				# Teil deutlich kleiner als das Ganze (Rahmen/Wand dreht sich nicht mit).
				assert_bool(teil.get_longest_axis_size() < ganz.get_longest_axis_size() * 0.5).override_failure_message(
					wo + ": zu gross fuer ein drehendes Teil (%s gegen %s)" % [teil.size, ganz.size]).is_true()
				# Pivot: Mittelpunkt des Teils liegt nahe an der Drehachse durch den Knotenursprung.
				var mitte: Vector3 = teil.get_center()
				var quer: Vector3 = mitte - achse.normalized() * mitte.dot(achse.normalized())
				assert_bool(quer.length() <= teil.get_longest_axis_size() * MAX_ABWEICHUNG).override_failure_message(
					wo + ": Drehpunkt liegt %.2f neben der Mitte des Teils" % quer.length()).is_true()
			l.free()
			modell.queue_free()
	assert_int(geprueft).override_failure_message("keine einzige Drehanimation geprueft").is_greater(0)


func test_teilesuche_trifft_nur_namen_die_so_beginnen() -> void:
	var wurzel := Node3D.new()
	for n in ["welt_luefter_rahmen", "luefter_1", "luefter_2"]:
		var k := Node3D.new()
		k.name = n
		wurzel.add_child(k)
	var l := Lebendig.new()
	var treffer: Array[Node3D] = []
	l._sammle_knoten(wurzel, "luefter", treffer)
	assert_int(treffer.size()).is_equal(2)
	for k in treffer:
		assert_str(String(k.name)).starts_with("luefter_")
	l.free()
	wurzel.free()
