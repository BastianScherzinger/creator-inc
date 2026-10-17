## Misst, wo die Stationsmodelle einer Welt wirklich stehen: Mitte der
## Bodenflaeche (AABB aus Basis + hoechster Ausstattungsstufe) relativ zum
## Ursprung. Weicht sie deutlich ab, gehoert ein "schild"-Versatz nach worlds.json.
##   godot_console --headless --path project -s res://tools/stations_mitte.gd
extends SceneTree


func _init() -> void:
	var welten := WorldData.laden()
	for i in range(welten.anzahl()):
		var welt: String = welten.id(i)
		for id in Ids.ALL_STATIONS:
			var box := AABB()
			var leer: bool = true
			var namen: Array[String] = ["%s_basis" % id]
			for n in range(1, 4):
				namen.append("%s_ausstattung_%d_3" % [id, n])
			for name in namen:
				var pfad: String = "res://assets/stations/%s/%s.glb" % [welt, name]
				if not ResourceLoader.exists(pfad):
					continue
				var knoten: Node3D = (load(pfad) as PackedScene).instantiate() as Node3D
				for b in _boxen(knoten, Transform3D.IDENTITY):
					box = b if leer else box.merge(b)
					leer = false
				knoten.free()
			if leer:
				print("%-10s %-20s fehlt" % [welt, id])
				continue
			var mitte: Vector3 = box.get_center()
			print("%-10s %-20s mitte x %+.2f z %+.2f   groesse %.1f x %.1f" % [
				welt, id, mitte.x, mitte.z, box.size.x, box.size.z])
	quit()


func _boxen(knoten: Node, t: Transform3D) -> Array[AABB]:
	var liste: Array[AABB] = []
	var eigen: Transform3D = t
	if knoten is Node3D:
		eigen = t * (knoten as Node3D).transform
	if knoten is MeshInstance3D and (knoten as MeshInstance3D).mesh != null:
		liste.append(eigen * (knoten as MeshInstance3D).mesh.get_aabb())
	for kind in knoten.get_children():
		liste.append_array(_boxen(kind, eigen))
	return liste
