## Prueft, was der Pruefschalter --tiefe N im Kern hinterlaesst (Welt als Argument).
##   godot_console --headless --path project -s res://tools/tiefe_probe.gd -- 6 3
extends SceneTree


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var welt: int = int(args[0]) - 1 if args.size() > 0 else 5
	var n: int = int(args[1]) if args.size() > 1 else 3
	var kern := GameCore.new(null, welt)
	kern.kapital = 1.0e12
	var ids: Array[StringName] = kern.bereiche.ids()
	for i in range(mini(n, ids.size())):
		print("Bereich %s: %s" % [ids[i], kern.kaufe_bereich(ids[i])])
	for id in Ids.ALL_STATIONS:
		print("%s: +%d" % [id, kern.upgrade_station_mehrfach(id, n * 8)])
	print("stufen_gesamt=%d kapital=%s" % [kern.stufen_gesamt(), kern.kapital])
	for z in kern.ziele.sichtbar():
		print("%s fortschritt %.2f" % [z.get("id"), GoalSystem.fortschritt(z, kern.messwert)])
	quit()
