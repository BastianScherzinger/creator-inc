## Vorschau Paket 2d: Hud mit hohem Rang (alle fuenf Plaetze), Rand-Symbol fuers Geschenk,
## optional die offene Karte.
##   godot_console --path project --resolution 540x1200 -s res://tools/w2d_vorschau.gd -- <modus> <ausgabe.png> [rang]
## Modi: voll (Leiste + Rand-Symbol), karte (zusaetzlich offene Karte), mitte (nur Boost-Mitte frei)
extends SceneTree

var _modus: String = "voll"
var _ausgabe: String = "user://w2d.png"
var _t: float = 0.0
var _hud: Hud
var _symbol: GeschenkView.RandSymbol
var _geoeffnet: bool = false


func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() > 0:
		_modus = args[0]
	if args.size() > 1:
		_ausgabe = args[1]
	var rang: int = int(args[2]) if args.size() > 2 else 5
	var kern := GameCore.new(BalanceData.fuer_welt("zimmer"), 0)
	var thema: ThemeData = ThemeData.laden(kern.welt_id())
	UiStil.setze_welt(thema)
	kern.kapital = 69133.0
	kern.bogen["punkte"] = kern.erfolge.schwelle(rang) + 3
	kern.bogen["schub"] = 1
	kern._pruefe_level()
	var ebene := CanvasLayer.new()
	root.add_child(ebene)
	var grund := ColorRect.new()
	grund.color = Color("9fc27a")
	grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ebene.add_child(grund)
	var bereich := Control.new()
	bereich.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bereich.theme = UiStil.thema()
	ebene.add_child(bereich)
	var audio := AudioDirector.new()
	root.add_child(audio)
	var werbung := AdServiceStub.new()
	root.add_child(werbung)
	_hud = Hud.new()
	bereich.add_child(_hud)
	_hud.aufbauen(kern, thema, audio, werbung)
	if _modus == "mitte":
		for p in Menueleiste.PUNKTE:
			_hud.menueleiste.setze_frei(p, p == &"schub")
	_symbol = GeschenkView.biete_am_rand(bereich, kern, _hud.saft, audio)


func _process(delta: float) -> bool:
	_t += delta
	if _modus == "karte" and not _geoeffnet and _t > 0.8:
		_geoeffnet = true
		_symbol._oeffne()
	if _t > 2.9 and _modus != "mitte":
		_hud.menueleiste.setze_schub_zustand(&"bereit")
	if _t > 3.2:
		var bild: Image = root.get_texture().get_image()
		bild.save_png(_ausgabe)
		quit()
	return false
