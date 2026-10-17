## Standortkarte (K6 Meta-Schleife): die sechs Welten als Standorte EINER Firma
## auf einem Pfad, unten der erste, oben der letzte -- nach oben wischen heisst
## wachsen.
##
## Je Standort: Ueberblicksbild der Welt (assets/ui/standorte/<welt>.png, erzeugt
## von tools/standort_bilder.gd), Band mit dem Weltnamen aus theme.json, Chip
## "Einkommen xN" (welt_faktor_pro_welt der Welt hoch ihre Position) und ein
## Zustand: geschafft (Haken + Siegel), aktuell (pulsierender Rahmen, "Du bist
## hier"), gesperrt (Schloss + "Schliesse zuerst <aktuelle Welt> ab").
##
## Ein Tipp wechselt NIE die Welt: Der Kern kennt nur `wechsle_welt()` vorwaerts.
## Er zeigt einen kurzen Hinweis.
##
## Einbau: `StandortkarteView.oeffnen(parent, kern, themen)` -- legt eine eigene
## CanvasLayer ueber alles und gibt die Ansicht zurueck. Werte stehen in
## data/ui/standortkarte.json, Texte unter `standort_*` in data/i18n/de.json.
class_name StandortkarteView
extends Control

signal geschlossen

enum Zustand { GESCHAFFT, AKTUELL, GESPERRT }

const DATEN: String = "res://data/ui/standortkarte.json"

static var _konfig: Dictionary = {}

var kern: GameCore = null
var welten: WorldData = null
var aktuell: int = 0
## welt_id -> ThemeData
var themen: Dictionary = {}

var _grund: TextureRect
var _scroll: WischScroll
var _inhalt: _Pfad
var _strahlen: _Strahlen
var _standorte: Array[Control] = []
var _bilder: Array[TextureRect] = []
var _erkenner: Array[TippErkenner] = []
var _rahmen: Panel = null
var _hinweis: PanelContainer
var _hinweis_text: Label
var _hinweis_lauf: Tween = null
var _scroll_lauf: Tween = null


# --- Oeffnen ----------------------------------------------------------------------

## Oeffnet die Karte ueber allem (eigene CanvasLayer unter `parent`).
## `themen`: welt_id -> ThemeData; fehlende Themen laedt die Karte selbst.
static func oeffnen(parent: Node, kern_daten: GameCore, themen_daten: Dictionary = {}) -> StandortkarteView:
	var ebene := CanvasLayer.new()
	ebene.layer = int(konfig().get("ebene", 60))
	var ansicht := StandortkarteView.new()
	ansicht.einrichten(kern_daten, themen_daten)
	ebene.add_child(ansicht)
	if parent != null:
		parent.add_child(ebene)
	return ansicht


static func konfig() -> Dictionary:
	if _konfig.is_empty():
		var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATEN))
		_konfig = roh as Dictionary if roh is Dictionary else {"_": ""}
	return _konfig


static func _k(name: String, ersatz: float) -> float:
	return float(konfig().get(name, ersatz))


static func _farbe(name: String, ersatz: Color) -> Color:
	return UiStil.farbe(String(konfig().get(name, "")), ersatz)


# --- Reine Logik (getestet) ---------------------------------------------------------

static func zustand(index: int, aktueller_index: int) -> Zustand:
	if index < aktueller_index:
		return Zustand.GESCHAFFT
	if index == aktueller_index:
		return Zustand.AKTUELL
	return Zustand.GESPERRT


## Einkommensfaktor eines Standorts: welt_faktor_pro_welt der Welt hoch ihre
## Position -- genau der Faktor, mit dem der Kern dort rechnet (ohne Erfahrung
## und Erfolge, die gelten fuer alle Standorte gleich).
static func einkommen_faktor(welt_daten: WorldData, index: int) -> float:
	var balance: BalanceData = BalanceData.fuer_welt(welt_daten.id(index))
	return pow(balance.welt_faktor_pro_welt, float(index))


## "×1", "×10", "×1.000" -- ganze Faktoren ohne Nachkommastelle, sehr grosse
## mit den Kurzformen aus UiStil.zahl.
static func faktor_text(faktor: float) -> String:
	var ganz: float = roundf(faktor)
	var text: String = UiStil.zahl(faktor)
	if absf(faktor - ganz) < 0.01 and ganz < 1.0e6:
		var ziffern: String = str(int(ganz))
		text = ""
		while ziffern.length() > 3:
			text = "." + ziffern.right(3) + text
			ziffern = ziffern.left(ziffern.length() - 3)
		text = ziffern + text
	return UiText.t("standort_faktor") % text


func welt_name(index: int) -> String:
	var thema: ThemeData = thema_von(index)
	return thema.welt_name if thema != null else welten.id(index)


func thema_von(index: int) -> ThemeData:
	var id: String = welten.id(index)
	if not themen.has(id):
		themen[id] = ThemeData.laden(id)
	return themen[id] as ThemeData


## Der Hinweis nach einem Tipp auf einen Standort.
func hinweis_fuer(index: int) -> String:
	match zustand(index, aktuell):
		Zustand.AKTUELL:
			return UiText.t("standort_tipp_hier") % welt_name(index)
		Zustand.GESCHAFFT:
			return UiText.t("standort_tipp_geschafft") % welt_name(index)
	return UiText.t("standort_tipp_gesperrt") % welt_name(aktuell)


func anzahl() -> int:
	return _standorte.size()


func standort(index: int) -> Control:
	return _standorte[index]


func hinweis_text() -> String:
	return _hinweis_text.text if _hinweis_text != null else ""


# --- Aufbau -----------------------------------------------------------------------

func einrichten(kern_daten: GameCore, themen_daten: Dictionary = {}) -> void:
	kern = kern_daten
	welten = kern.welten if kern != null and kern.welten != null else WorldData.laden()
	aktuell = kern.welt_index if kern != null else 0
	themen = themen_daten.duplicate()
	_baue()


func _baue() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP

	_grund = TextureRect.new()
	_grund.texture = _verlauf()
	_grund.stretch_mode = TextureRect.STRETCH_SCALE
	_grund.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_grund.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_grund)
	_grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

	_scroll = WischScroll.new()
	add_child(_scroll)
	_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	_scroll.follow_focus = false
	_scroll.gui_input.connect(_auf_scroll_eingabe)

	_inhalt = _Pfad.new()
	_inhalt.mouse_filter = Control.MOUSE_FILTER_PASS
	_inhalt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_inhalt)
	var n: int = welten.anzahl()
	_inhalt.custom_minimum_size.y = _k("rand_oben", 150.0) + float(n) * _k("standort_hoehe", 520.0) + _k("rand_unten", 120.0)
	_inhalt.resized.connect(ordne)

	_strahlen = _Strahlen.new()
	_strahlen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_inhalt.add_child(_strahlen)

	for i in range(n):
		_baue_standort(i)

	_baue_kopf()
	_baue_hinweis()
	ordne()


## Ordnet die Standorte fuer die Breite `breite` (Standard: eigene Breite).
## Unten der erste Standort, oben der letzte. Der Weg zwischen zwei Standorten
## laeuft abwechselnd rechts und links an den Bildern vorbei.
func ordne(breite: float = -1.0) -> void:
	var b: float = breite if breite > 0.0 else _inhalt.size.x
	if b <= 0.0:
		b = float(ProjectSettings.get_setting("display/window/size/viewport_width", 720))
	var n: int = _standorte.size()
	var hoehe: float = _k("standort_hoehe", 520.0)
	var versatz: float = _k("versatz_x", 0.0)
	var bild_b: float = _k("bild_breite", 440.0)
	var bild_h: float = _k("bild_hoehe", 330.0)
	var band_b: float = _k("banner_breite", 470.0)
	var band_y: float = bild_h - _k("banner_ueberlappung", 34.0)
	var chip_unten: float = band_y + _k("banner_hoehe", 78.0) + _k("chip_abstand", 4.0) + _k("chip_hoehe", 74.0)
	var mitten: Array[Vector2] = []
	var sperren: Array[Rect2] = []
	for i in range(n):
		var block: Control = _standorte[i]
		var seite: float = -1.0 if i % 2 == 0 else 1.0
		block.size = Vector2(b, hoehe)
		block.position = Vector2(seite * versatz, _k("rand_oben", 150.0) + float(n - 1 - i) * hoehe)
		var mitte_x: float = block.position.x + b * 0.5
		mitten.append(Vector2(mitte_x, block.position.y))
		var einzug: float = bild_b * _k("pfad_bild_einzug", 0.2)
		sperren.append(Rect2(mitte_x - bild_b * 0.5 + einzug, block.position.y, bild_b - einzug * 2.0, bild_h))
		sperren.append(Rect2(mitte_x - band_b * 0.5, block.position.y + band_y, band_b, chip_unten - band_y))
		if i == aktuell:
			var rand: float = _k("rahmen_rand", 18.0)
			sperren.append(Rect2(mitte_x - bild_b * 0.5 - rand, block.position.y - rand,
				bild_b + rand * 2.0, bild_h + rand * 2.0))
	var wege: Array = []
	var aussen: float = _k("pfad_aussen", 300.0)
	for i in range(n - 1):
		# Weg i fuehrt von Standort i (unten) zu Standort i+1 (oben).
		var seite: float = 1.0 if i % 2 == 0 else -1.0
		var unten: Vector2 = mitten[i]
		var oben: Vector2 = mitten[i + 1]
		var p0 := Vector2(unten.x + seite * bild_b * _k("pfad_start", 0.3), unten.y + bild_h * _k("pfad_start_hoehe", 0.3))
		var p3 := Vector2(oben.x + seite * band_b * _k("pfad_ende", 0.42), oben.y + chip_unten)
		var p1 := Vector2(b * 0.5 + seite * aussen, lerpf(p0.y, p3.y, _k("pfad_zug", 0.3)))
		var p2 := Vector2(b * 0.5 + seite * aussen, lerpf(p3.y, p0.y, _k("pfad_zug", 0.3)))
		wege.append([p0, p1, p2, p3])
	_inhalt.setze_pfad(wege, sperren, aktuell)
	if aktuell >= 0 and aktuell < mitten.size():
		var kante: float = b * 2.0
		_strahlen.size = Vector2(kante, kante)
		_strahlen.position = mitten[aktuell] + Vector2(0.0, bild_h * 0.5) - _strahlen.size * 0.5
		_strahlen.pivot_offset = _strahlen.size * 0.5


func _baue_standort(i: int) -> void:
	var z: Zustand = zustand(i, aktuell)
	var block := Control.new()
	block.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_inhalt.add_child(block)
	_standorte.append(block)

	var bild_b: float = _k("bild_breite", 440.0)
	var bild_h: float = _k("bild_hoehe", 330.0)
	# Alles in einer Spalte, horizontal in der Blockmitte.
	var spalte := Control.new()
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.set_anchors_preset(Control.PRESET_CENTER_TOP)
	spalte.anchor_left = 0.5
	spalte.anchor_right = 0.5
	spalte.offset_left = -_k("banner_breite", 470.0) * 0.5
	spalte.offset_right = _k("banner_breite", 470.0) * 0.5
	spalte.offset_top = 0.0
	spalte.offset_bottom = _k("standort_hoehe", 520.0)
	block.add_child(spalte)
	var mitte_x: float = _k("banner_breite", 470.0) * 0.5

	if z == Zustand.AKTUELL:
		_rahmen = Panel.new()
		var rahmen_stil := StyleBoxFlat.new()
		rahmen_stil.bg_color = Color(UiStil.WEISS, 0.18)
		rahmen_stil.border_color = UiStil.akzent_von(thema_von(i))
		rahmen_stil.set_border_width_all(int(_k("rahmen_dicke", 8.0)))
		rahmen_stil.set_corner_radius_all(int(_k("rahmen_radius", 48.0)))
		rahmen_stil.anti_aliasing = true
		_rahmen.add_theme_stylebox_override("panel", rahmen_stil)
		_rahmen.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var rand: float = _k("rahmen_rand", 18.0)
		_rahmen.position = Vector2(mitte_x - bild_b * 0.5 - rand, -rand)
		_rahmen.size = Vector2(bild_b + rand * 2.0, bild_h + rand * 2.0)
		_rahmen.pivot_offset = _rahmen.size * 0.5
		spalte.add_child(_rahmen)

	var bild := TextureRect.new()
	bild.texture = _bild_von(welten.id(i))
	bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	bild.position = Vector2(mitte_x - bild_b * 0.5, 0.0)
	bild.size = Vector2(bild_b, bild_h)
	bild.mouse_filter = Control.MOUSE_FILTER_STOP
	if z == Zustand.GESPERRT:
		var grau: float = _k("gesperrt_grau", 0.65)
		bild.modulate = Color(grau, grau, minf(1.0, grau * _k("gesperrt_blau", 1.1)), 1.0)
	spalte.add_child(bild)
	_bilder.append(bild)
	var erkenner := TippErkenner.new()
	_erkenner.append(erkenner)
	bild.gui_input.connect(func(e: InputEvent) -> void:
		if erkenner.auswerten(e, bild.get_global_transform_with_canvas()):
			auf_tipp(i))

	match z:
		Zustand.GESCHAFFT:
			_baue_geschafft(spalte, mitte_x, bild_h)
		Zustand.AKTUELL:
			_baue_hier(spalte, mitte_x, i)
		Zustand.GESPERRT:
			_baue_gesperrt(spalte, mitte_x, bild_h)

	var band := _Banner.new()
	band.farbe_band = _farbe("banner_farbe", UiStil.WARNUNG)
	band.farbe_kante = _farbe("banner_kante", UiStil.WARNUNG_TEXT)
	band.schwanz = _k("banner_schwanz", 46.0)
	band.versatz = _k("banner_versatz", 14.0)
	band.mouse_filter = Control.MOUSE_FILTER_IGNORE
	band.position = Vector2(0.0, bild_h - _k("banner_ueberlappung", 34.0))
	band.size = Vector2(_k("banner_breite", 470.0), _k("banner_hoehe", 78.0))
	spalte.add_child(band)
	var name_label: Label = UiStil.label_kontur(welt_name(i).to_upper(), int(_k("banner_schrift", 34.0)))
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	name_label.clip_text = true
	name_label.name = "Name"
	band.add_child(name_label)
	name_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	name_label.offset_left = band.schwanz
	name_label.offset_right = -band.schwanz
	name_label.offset_bottom = -band.versatz

	var chip := PanelContainer.new()
	chip.name = "Chip"
	chip.add_theme_stylebox_override("panel", UiStil.sticker(_farbe("chip_farbe", UiStil.TINTE),
		UiStil.RADIUS_KNOPF, UiStil.KONTUR, UiStil.A2))
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var chip_b: float = _k("chip_breite", 250.0)
	chip.position = Vector2(mitte_x - chip_b * 0.5, band.position.y + band.size.y + _k("chip_abstand", 4.0))
	chip.custom_minimum_size = Vector2(chip_b, _k("chip_hoehe", 74.0))
	spalte.add_child(chip)
	var reihe := HBoxContainer.new()
	reihe.alignment = BoxContainer.ALIGNMENT_CENTER
	reihe.add_theme_constant_override("separation", UiStil.A3)
	reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(reihe)
	var muenze := PanelContainer.new()
	muenze.add_theme_stylebox_override("panel", UiStil.chip(UiStil.GOLD, UiStil.A1, UiStil.A1, 0.0))
	muenze.mouse_filter = Control.MOUSE_FILTER_IGNORE
	muenze.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	muenze.add_child(UiStil.symbolbild("pfeil_hoch", _k("chip_symbol", 44.0)))
	reihe.add_child(muenze)
	var texte := VBoxContainer.new()
	texte.add_theme_constant_override("separation", 0)
	texte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reihe.add_child(texte)
	texte.add_child(UiStil.label(UiText.t("standort_einkommen"), int(_k("chip_schrift_klein", 20.0)),
		_farbe("chip_text_farbe", UiStil.WEISS), UiStil.FETT))
	var faktor := UiStil.label(faktor_text(einkommen_faktor(welten, i)), int(_k("chip_schrift_gross", 32.0)),
		UiStil.WEISS, UiStil.FETT)
	faktor.name = "Faktor"
	texte.add_child(faktor)
	if z == Zustand.GESPERRT:
		chip.modulate = Color(UiStil.WEISS, _k("gesperrt_chip_deckkraft", 0.8))


func _baue_geschafft(spalte: Control, mitte_x: float, bild_h: float) -> void:
	var kante: float = _k("haken_kante", 110.0)
	var kreis := PanelContainer.new()
	kreis.add_theme_stylebox_override("panel", UiStil.sticker(_farbe("siegel_farbe", UiStil.KAUFEN),
		UiStil.RADIUS_CHIP, UiStil.KONTUR, UiStil.A3))
	kreis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kreis.size = Vector2(kante, kante)
	kreis.position = Vector2(mitte_x - kante * 0.5, bild_h * 0.5 - kante * 0.75)
	var haken: TextureRect = UiStil.symbolbild("haken", kante - float(UiStil.A3) * 2.0)
	haken.modulate = UiStil.WEISS
	kreis.add_child(haken)
	spalte.add_child(kreis)
	var siegel: Label = UiStil.label_kontur(UiText.t("standort_geschafft").to_upper(),
		int(_k("siegel_schrift", 40.0)), UiStil.WEISS)
	siegel.name = "Siegel"
	siegel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	siegel.size = Vector2(spalte.offset_right - spalte.offset_left, _k("siegel_schrift", 40.0) * 1.6)
	siegel.position = Vector2(0.0, kreis.position.y + kante + float(UiStil.A1))
	siegel.pivot_offset = siegel.size * 0.5
	siegel.rotation_degrees = _k("siegel_drehung_grad", -8.0)
	spalte.add_child(siegel)


func _baue_hier(spalte: Control, mitte_x: float, i: int) -> void:
	var chip := PanelContainer.new()
	chip.name = "Hier"
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.akzent_von(thema_von(i)), UiStil.A4, UiStil.A2, UiStil.SCHATTEN_Y))
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var text: Label = UiStil.label(UiText.t("standort_hier"), int(_k("hier_schrift", 26.0)),
		UiStil.akzent_text_von(thema_von(i)), UiStil.FETT)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	chip.add_child(text)
	spalte.add_child(chip)
	var breite: float = _k("hier_breite", 230.0)
	chip.custom_minimum_size = Vector2(breite, 0.0)
	chip.position = Vector2(mitte_x - breite * 0.5, -_k("hier_hoehe_ueber", 56.0))


func _baue_gesperrt(spalte: Control, mitte_x: float, bild_h: float) -> void:
	var kante: float = _k("schloss_kante", 120.0)
	var schloss: TextureRect = UiStil.symbolbild("schloss", kante)
	schloss.modulate = _farbe("schloss_farbe", UiStil.GOLD)
	schloss.position = Vector2(mitte_x - kante * 0.5, bild_h * 0.5 - kante * 0.85)
	spalte.add_child(schloss)
	var text: Label = UiStil.label_kontur(UiText.t("standort_gesperrt") % welt_name(aktuell),
		int(_k("gesperrt_schrift", 28.0)), UiStil.WEISS)
	text.name = "Gesperrt"
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.size = Vector2(spalte.offset_right - spalte.offset_left, kante)
	text.position = Vector2(0.0, schloss.position.y + kante + float(UiStil.A1))
	spalte.add_child(text)


func _baue_kopf() -> void:
	# Weicher Uebergang oben: Titel und Kreuz stehen nie direkt auf einem Bild.
	var verlauf := Gradient.new()
	var oben: Color = _farbe("hintergrund_oben", UiStil.AKZENT_STANDARD)
	verlauf.set_color(0, oben)
	verlauf.set_color(1, Color(oben, 0.0))
	var tex := GradientTexture2D.new()
	tex.gradient = verlauf
	tex.fill_from = Vector2(0.5, 0.0)
	tex.fill_to = Vector2(0.5, 1.0)
	var schleier := TextureRect.new()
	schleier.texture = tex
	schleier.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	schleier.stretch_mode = TextureRect.STRETCH_SCALE
	schleier.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(schleier)
	schleier.set_anchors_preset(Control.PRESET_TOP_WIDE)
	schleier.anchor_right = 1.0
	schleier.offset_bottom = _k("kopf_verlauf", 170.0)

	# Der Titel sitzt auf einem eigenen Aufkleber: beim Blaettern liegt sonst ein
	# Standortbild darunter und die Schrift verschwimmt (QA 17.10.).
	var titel_feld := PanelContainer.new()
	titel_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	titel_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.TINTE, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3)))
	var titel: Label = UiStil.label(UiText.t("standort_titel"), int(_k("titel_schrift", 44.0)), UiStil.WEISS, UiStil.FETT)
	titel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	titel_feld.add_child(titel)
	add_child(titel_feld)
	titel_feld.position = Vector2(_k("kopf_rand", 24.0), _k("kopf_oben", 28.0))

	var kante: float = _k("schliessen_kante", 88.0)
	var zu := Button.new()
	zu.name = "Schliessen"
	zu.custom_minimum_size = Vector2(kante, kante)
	zu.focus_mode = Control.FOCUS_NONE
	UiStil.faerbe_knopf(zu, UiStil.WARNUNG)
	zu.icon = UiStil.symbol("schliessen")
	zu.expand_icon = true
	zu.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zu.add_theme_constant_override("icon_max_width", int(kante * 0.5))
	zu.add_theme_color_override("icon_normal_color", UiStil.WEISS)
	zu.add_theme_color_override("icon_pressed_color", UiStil.WEISS)
	zu.add_theme_color_override("icon_hover_color", UiStil.WEISS)
	add_child(zu)
	zu.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	zu.offset_left = -kante - _k("kopf_rand", 24.0)
	zu.offset_right = -_k("kopf_rand", 24.0)
	zu.offset_top = _k("kopf_oben", 28.0)
	zu.offset_bottom = _k("kopf_oben", 28.0) + kante
	zu.pressed.connect(schliessen)


func _baue_hinweis() -> void:
	_hinweis = PanelContainer.new()
	_hinweis.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, UiStil.A4))
	_hinweis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hinweis.visible = false
	_hinweis_text = UiStil.label("", int(_k("hinweis_schrift", 26.0)), UiStil.TINTE, UiStil.FETT)
	_hinweis_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hinweis_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hinweis.add_child(_hinweis_text)
	add_child(_hinweis)
	_hinweis.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hinweis.anchor_left = 0.0
	_hinweis.anchor_right = 1.0
	_hinweis.offset_left = _k("kopf_rand", 24.0) * 2.0
	_hinweis.offset_right = -_k("kopf_rand", 24.0) * 2.0
	_hinweis.offset_bottom = -_k("hinweis_unten", 64.0)
	_hinweis.offset_top = _hinweis.offset_bottom - _k("hinweis_hoehe", 110.0)
	_hinweis.grow_vertical = Control.GROW_DIRECTION_BEGIN


func _verlauf() -> GradientTexture2D:
	var verlauf := Gradient.new()
	verlauf.set_color(0, _farbe("hintergrund_oben", UiStil.AKZENT_STANDARD))
	verlauf.set_color(1, _farbe("hintergrund_unten", UiStil.GOLD))
	var tex := GradientTexture2D.new()
	tex.gradient = verlauf
	tex.fill_from = Vector2(0.5, 0.0)
	tex.fill_to = Vector2(0.5, 1.0)
	tex.width = 4
	tex.height = 256
	return tex


static func _bild_von(welt_id: String) -> Texture2D:
	var pfad: String = String(konfig().get("bild_pfad", "")) % welt_id
	if ResourceLoader.exists(pfad):
		return load(pfad) as Texture2D
	push_warning("Standortbild fehlt: %s (tools/standort_bilder.gd laufen lassen)" % pfad)
	return UiStil.symbol("haus")


# --- Leben ------------------------------------------------------------------------

func _ready() -> void:
	_starte_puls()
	_springe_zu_aktuell.call_deferred()


func _starte_puls() -> void:
	var takt: float = 1.0 / maxf(0.1, _k("puls_hz", 1.1))
	var skala: float = _k("puls_skala", 1.06)
	if _rahmen != null:
		var t := _rahmen.create_tween().set_loops()
		t.tween_property(_rahmen, "scale", Vector2(skala, skala), takt * 0.5).set_trans(Tween.TRANS_SINE)
		t.tween_property(_rahmen, "scale", Vector2.ONE, takt * 0.5).set_trans(Tween.TRANS_SINE)
	var dreh := _strahlen.create_tween().set_loops()
	dreh.tween_property(_strahlen, "rotation", TAU, _k("strahlen_umlauf", 40.0)).from(0.0)


## Beim Oeffnen: vom vorigen Standort sanft zum aktuellen gleiten.
func _springe_zu_aktuell() -> void:
	if not is_inside_tree():
		return
	await get_tree().process_frame
	if not is_inside_tree() or aktuell >= _standorte.size():
		return
	var ziel: float = scroll_ziel(aktuell, _scroll.size.y)
	var start: float = scroll_ziel(maxi(0, aktuell - 1), _scroll.size.y)
	_scroll.scroll_vertical = int(start)
	_scroll_lauf = create_tween()
	_scroll_lauf.tween_property(_scroll, "scroll_vertical", int(ziel), _k("scroll_dauer", 0.5)) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Scrollwert, bei dem Standort `index` mittig im Bild steht (geklemmt).
func scroll_ziel(index: int, sicht_hoehe: float) -> float:
	var block: Control = _standorte[index]
	var mitte: float = block.position.y + _k("standort_hoehe", 520.0) * 0.5
	var hoechstens: float = maxf(0.0, _inhalt.custom_minimum_size.y - sicht_hoehe)
	return clampf(mitte - sicht_hoehe * 0.5, 0.0, hoechstens)


## Ein Finger auf der Karte hat Vorrang vor dem Gleiten (schnelles Wischen
## kaempft nie gegen eine laufende Animation).
func _auf_scroll_eingabe(e: InputEvent) -> void:
	if e is InputEventScreenTouch or e is InputEventScreenDrag or e is InputEventMouseButton:
		if _scroll_lauf != null and _scroll_lauf.is_valid():
			_scroll_lauf.kill()


func auf_tipp(index: int) -> void:
	_hinweis_text.text = hinweis_fuer(index)
	_hinweis.visible = true
	if index < _bilder.size():
		UiStil.aufploppen(_bilder[index], _k("tipp_ploppen", 0.92))
	if not is_inside_tree():
		return
	Haptik.puls(int(_k("haptik_ms", 12.0)))
	if _hinweis_lauf != null and _hinweis_lauf.is_valid():
		_hinweis_lauf.kill()
	_hinweis.modulate.a = 1.0
	UiStil.aufploppen(_hinweis)
	_hinweis_lauf = create_tween()
	_hinweis_lauf.tween_interval(_k("hinweis_dauer", 1.8))
	_hinweis_lauf.tween_property(_hinweis, "modulate:a", 0.0, UiStil.DAUER_KAUF)
	_hinweis_lauf.tween_callback(func() -> void: _hinweis.visible = false)


func schliessen() -> void:
	geschlossen.emit()
	var ebene: Node = get_parent()
	if ebene is CanvasLayer and ebene.get_child_count() == 1:
		ebene.queue_free()
	else:
		queue_free()


func _notification(was: int) -> void:
	if was == NOTIFICATION_WM_GO_BACK_REQUEST and is_inside_tree():
		schliessen()


# --- Zeichnungen --------------------------------------------------------------------

## Inhalt der Scrollflaeche: zeichnet die gepunkteten Wege zwischen den
## Standorten (je Weg eine kubische Kurve). Punkte unter Bild, Band und Chip
## entfallen -- der Weg verschwindet hinter dem Standort statt durch ihn.
class _Pfad extends Control:
	var _wege: Array = []
	var _sperren: Array[Rect2] = []
	var _aktuell: int = 0

	func setze_pfad(wege: Array, sperren: Array[Rect2], aktueller_index: int) -> void:
		_wege = wege
		_sperren = sperren
		_aktuell = aktueller_index
		queue_redraw()

	func wege() -> int:
		return _wege.size()

	## Alle sichtbaren Punkte von Weg `i` (fuer Zeichnen und Tests).
	func punkte(i: int) -> Array[Vector2]:
		var ergebnis: Array[Vector2] = []
		var w: Array = _wege[i] as Array
		var p0: Vector2 = w[0]
		var p1: Vector2 = w[1]
		var p2: Vector2 = w[2]
		var p3: Vector2 = w[3]
		var abstand: float = StandortkarteView._k("punkt_abstand", 30.0)
		# Die Kurve ist kuerzer als der Kontrollpolygonzug: Faktor aus den Daten.
		var laenge: float = (p0.distance_to(p1) + p1.distance_to(p2) + p2.distance_to(p3)) \
			* StandortkarteView._k("pfad_glaettung", 0.8)
		var schritte: int = maxi(2, int(laenge / abstand))
		for s in range(schritte + 1):
			var p: Vector2 = p0.bezier_interpolate(p1, p2, p3, float(s) / float(schritte))
			var frei: bool = true
			for r in _sperren:
				if r.has_point(p):
					frei = false
					break
			if frei:
				ergebnis.append(p)
		return ergebnis

	func _draw() -> void:
		var r: float = StandortkarteView._k("punkt_radius", 9.0)
		var offen: Color = StandortkarteView._farbe("punkt_farbe_offen", UiStil.WEISS)
		var zu: Color = StandortkarteView._farbe("punkt_farbe_gesperrt", UiStil.TINTE_3)
		for i in range(_wege.size()):
			var farbe: Color = offen if i + 1 <= _aktuell else zu
			for p in punkte(i):
				draw_circle(p + Vector2(0.0, UiStil.SCHATTEN_Y_MARKER), r, Color(UiStil.TINTE, 0.3))
				draw_circle(p, r, farbe)


## Sonnenstrahlen hinter dem aktuellen Standort.
class _Strahlen extends Control:
	func _draw() -> void:
		var n: int = int(StandortkarteView._k("strahlen_anzahl", 14.0))
		var farbe: Color = StandortkarteView._farbe("strahlen_farbe", UiStil.PAPIER)
		farbe.a = StandortkarteView._k("strahlen_deckkraft", 0.35)
		var m: Vector2 = size * 0.5
		var r: float = size.x * 0.5
		var breite: float = PI / float(maxi(1, n))
		for i in range(n):
			var w: float = TAU * float(i) / float(n)
			var ecken := PackedVector2Array([m, m + Vector2.from_angle(w - breite * 0.5) * r,
				m + Vector2.from_angle(w + breite * 0.5) * r])
			draw_colored_polygon(ecken, farbe)


## Band mit Schwalbenschwanz-Enden, wie ein aufgeklebtes Banner.
class _Banner extends Control:
	var farbe_band: Color = UiStil.WARNUNG
	var farbe_kante: Color = UiStil.WARNUNG_TEXT
	var schwanz: float = 46.0
	var versatz: float = 14.0

	func _draw() -> void:
		var w: float = size.x
		var h: float = size.y
		var v: float = versatz
		var t: float = schwanz
		var kerbe: float = t * 0.45
		var links := PackedVector2Array([Vector2(0.0, v), Vector2(t * 1.6, v), Vector2(t * 1.6, h),
			Vector2(0.0, h), Vector2(kerbe, (v + h) * 0.5)])
		var rechts := PackedVector2Array([Vector2(w, v), Vector2(w - t * 1.6, v), Vector2(w - t * 1.6, h),
			Vector2(w, h), Vector2(w - kerbe, (v + h) * 0.5)])
		for teil in [links, rechts]:
			draw_colored_polygon(teil as PackedVector2Array, farbe_kante)
			var zu := (teil as PackedVector2Array).duplicate()
			zu.append(zu[0])
			draw_polyline(zu, UiStil.TINTE, float(UiStil.KONTUR_CHIP), true)
		var band := PackedVector2Array([Vector2(t, 0.0), Vector2(w - t, 0.0), Vector2(w - t, h - v),
			Vector2(t, h - v)])
		# Harter Schatten unter dem Band, dann das Band, dann die Kontur.
		draw_rect(Rect2(Vector2(t, UiStil.SCHATTEN_Y), Vector2(w - t * 2.0, h - v)), UiStil.TINTE)
		draw_colored_polygon(band, farbe_band)
		draw_rect(Rect2(Vector2(t, h - v - UiStil.SCHATTEN_Y * 2.0), Vector2(w - t * 2.0, UiStil.SCHATTEN_Y * 2.0)),
			Color(farbe_kante, 0.6))
		var zu_band := band.duplicate()
		zu_band.append(zu_band[0])
		draw_polyline(zu_band, UiStil.TINTE, float(UiStil.KONTUR), true)
