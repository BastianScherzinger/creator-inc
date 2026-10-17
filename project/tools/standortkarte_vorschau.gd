## Vorschau der Standortkarte ohne das ganze Spiel -> shots/serie/<bild>.png
##   godot_console --path project --resolution 540x1200 -s res://tools/standortkarte_vorschau.gd -- --welt 3 --bild k7_karte
## Optional: --tipp <position 1..6> zeigt den Hinweis nach einem Tipp,
##           --scroll <px> setzt die Scrollposition statt des Gleitens zum aktuellen Standort.
extends SceneTree

const WARTE_BILDER: int = 70

var _bilder: int = 0
var _ansicht: StandortkarteView = null
var _ziel: String = ""
var _tipp: int = -1
var _scroll: int = -1


func _initialize() -> void:
	var a: PackedStringArray = OS.get_cmdline_user_args()
	var welt: int = maxi(1, int(_wert(a, "--welt", "1"))) - 1
	_ziel = ProjectSettings.globalize_path("res://../shots/serie/%s.png" % _wert(a, "--bild", "standortkarte"))
	_tipp = int(_wert(a, "--tipp", "0")) - 1
	_scroll = int(_wert(a, "--scroll", "-1"))
	var welten: WorldData = WorldData.laden()
	welt = mini(welt, welten.anzahl() - 1)
	var kern := GameCore.new(BalanceData.fuer_welt(welten.id(welt)), welt)
	_ansicht = StandortkarteView.oeffnen(root, kern, {})


func _process(_delta: float) -> bool:
	_bilder += 1
	if _bilder == WARTE_BILDER - 30 and _tipp >= 0:
		_ansicht.auf_tipp(_tipp)
	if _bilder == WARTE_BILDER - 25 and _scroll >= 0:
		_ansicht._scroll.scroll_vertical = _scroll
	if _bilder >= WARTE_BILDER:
		DirAccess.make_dir_recursive_absolute(_ziel.get_base_dir())
		root.get_texture().get_image().save_png(_ziel)
		print("BILD ", _ziel)
		quit()
	return false


static func _wert(a: PackedStringArray, schalter: String, ersatz: String) -> String:
	var i: int = a.find(schalter)
	return a[i + 1] if i >= 0 and i + 1 < a.size() else ersatz
