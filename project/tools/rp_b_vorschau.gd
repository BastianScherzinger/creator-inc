## Vorschau einzelner Ansichten von Paket B ohne das ganze Spiel (Release-Plan 8):
##   godot_console --path project --resolution 540x1200 -s res://tools/rp_b_vorschau.gd -- <modus> <ausgabe.png> [welt]
## Modi: offline, geschenk, juice, eroeffnung, avatar
extends SceneTree

var _modus: String = "offline"
var _ausgabe: String = "user://rp_b.png"
var _welt: int = 0
var _bereich: Control
var _t: float = 0.0
var _gemacht: bool = false
var _saft: Saft
var _hud: Hud
var _kern: GameCore
var _thema: ThemeData
var _gekauft: bool = false


func _initialize() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	if args.size() > 0:
		_modus = args[0]
	if args.size() > 1:
		_ausgabe = args[1]
	if args.size() > 2:
		_welt = int(args[2])
	var kern := GameCore.new(null, _welt)
	var thema: ThemeData = ThemeData.laden(kern.welt_id())
	UiStil.setze_welt(thema)
	var ebene := CanvasLayer.new()
	root.add_child(ebene)
	var grund := ColorRect.new()
	grund.color = Color("e8c9a0")
	grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ebene.add_child(grund)
	_bereich = Control.new()
	_bereich.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_bereich.theme = UiStil.thema()
	ebene.add_child(_bereich)
	match _modus:
		"offline":
			var v := OfflineView.new()
			_bereich.add_child(v)
			v.zeige(5400.0, 183450.0, thema, true)
		"geschenk":
			kern.einkommen_pro_sekunde()
			var g := GeschenkView.new()
			_bereich.add_child(g)
			g.zeige({"tag": 3, "serie_max": 7, "betrag": 74200.0, "faktor": 1.3,
				"tage": [1.0, 1.15, 1.3, 1.45, 1.6, 1.8, 2.0]})
		"eroeffnung":
			var roh: Dictionary = thema.abschnitt("eroeffnung")
			if not roh.has("chat"):
				roh["chat"] = [
					{"von": "mo", "text": "Bruder. Drei Aufrufe."},
					{"von": "mo", "text": "Zwei warst du."},
					{"von": "mo", "text": "Der dritte war ich. Du schuldest mir einen Gaming-PC."},
					{"von": "du", "text": "Okay."}]
			var w := WeltwechselView.new()
			_bereich.add_child(w)
			w.zeige(String(thema.abschnitt("eroeffnung").get("titel", "")), "x", "Anfangen")
		"kauf":
			kern.kapital = 5.0e6
			_kern = kern
			_thema = thema
		"avatar":
			var spalte := HBoxContainer.new()
			spalte.position = Vector2(40.0, 200.0)
			_bereich.add_child(spalte)
			for n in ["Mo", "Younes", "Roman", "X"]:
				spalte.add_child(UiStil.avatar(n, Color("3d7bff"), 96.0))
		"juice":
			var kopf := Kopfleiste.new()
			_bereich.add_child(kopf)
			_saft = Saft.new()
			_saft.kopfleiste = kopf
			_bereich.add_child(_saft)
			kopf.setze(12884.0, 124.0, "Die WG", 0.31, true)
			kopf.setze_marken([{"id": "a", "wert": 0.25, "bereit": false, "eingeloest": true},
				{"id": "b", "wert": 0.5, "bereit": true, "eingeloest": false},
				{"id": "c", "wert": 0.75, "bereit": false, "eingeloest": false}])


func _process(delta: float) -> bool:
	_t += delta
	if _modus == "juice" and _saft != null and not _gemacht and _t > 0.4:
		_gemacht = true
		var mitte: Vector2 = Vector2(270.0, 700.0)
		_saft.blitz()
		_saft.funken(mitte, UiStil.KAUFEN, 22)
		_saft.konfetti(mitte + Vector2(0.0, -60.0), 48)
		_saft.stempel(mitte + Vector2(0.0, -200.0), "×1,5")
		_saft.betrag(mitte + Vector2(0.0, -60.0), "+3,4 €/s", UiStil.KAUFEN)
		_saft.muenzen(mitte, 10)
	if _modus == "kauf" and _hud == null and _t > 0.2:
		var audio := AudioDirector.new()
		root.add_child(audio)
		var werbung := AdServiceStub.new()
		root.add_child(werbung)
		_hud = Hud.new()
		_bereich.add_child(_hud)
		_hud.aufbauen(_kern, _thema, audio, werbung)
		_hud.zeige_station(&"station_processing")
	if _modus == "kauf" and _hud != null and not _gekauft and _t > 1.2:
		_gekauft = true
		_hud.stationsmenue.menge_index = 1
		_hud.stationsmenue._auf_ausbau()
	var warte: float = 1.5 if _modus == "kauf" else 0.65 if _modus == "juice" else 3.0
	if _modus != "juice" and _modus != "kauf":
		warte = 3.0
	if _t > (warte + (3.5 if _modus == "eroeffnung" else 0.0)) and not (_modus == "juice" and _t < warte):
		var bild: Image = root.get_texture().get_image()
		bild.save_png(_ausgabe)
		quit()
	return false
