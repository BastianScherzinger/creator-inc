## Werkzeug (nur für Vorschaubilder): startet main.tscn als Kind und ruft die U3-Prüfschalter
## auf, solange main.gd sie nicht selbst verdrahtet hat. Aufruf: tools/u3_serie.sh.
extends Node


func _ready() -> void:
	var haupt: Node = (load("res://game/main.tscn") as PackedScene).instantiate()
	add_child(haupt)
	await get_tree().create_timer(1.2).timeout
	U3Pruefung.anwenden(haupt, haupt.get("kern"), haupt.get("thema"), haupt.get("_hud"),
		haupt.get("_audio"), OS.get_cmdline_user_args())
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var i: int = args.find("--bild")
	var name: String = args[i + 1] if i >= 0 and i + 1 < args.size() else "u3"
	var warte: float = 3.5
	var w: int = args.find("--warte")
	if w >= 0 and w + 1 < args.size():
		warte = float(args[w + 1])
	await get_tree().create_timer(warte).timeout
	get_viewport().get_texture().get_image().save_png("user://%s.png" % name)
	get_tree().quit()
