## Ein Menue, das von unten ueber die Karte faehrt (Bottom Sheet).
##
## Wie im Genre: Die Karte bleibt oben sichtbar, das Menue liegt ueber der
## Menueleiste, ein Wisch nach unten oder das Kreuz schliesst es. Ein Vollbild-
## Dialog wuerde den Ort verdecken, um den es gerade geht -- man soll den neuen
## Bildschirm auf dem Schreibtisch erscheinen SEHEN, waehrend man ihn kauft.
##
## Sticker-Pop: ruhige Papierflaeche, oben ein Titelstreifen in der Akzentfarbe
## der Welt. Darin Titel und Schliessen-Knopf; Unterklassen haengen weitere
## Teile in `kopf` und fuellen `inhalt`.
class_name Sheet
extends Control

signal geschlossen

const DAUER: float = 0.22
const EINFAHRT: float = 120.0

## Abstand von unten: Hoehe der Menueleiste. Die Hud setzt ihn.
var unten_frei: float = 150.0

var karte: PanelContainer
var streifen: PanelContainer
var kopf: HBoxContainer
var titel: Label
var inhalt: VBoxContainer
var _schliessen: TextureButton
var _offen: bool = false
var _ziehen_start: float = -1.0
var _tween: Tween
var _akzent_gesetzt: Color = Color(0, 0, 0, 0)


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	visible = false

	karte = PanelContainer.new()
	karte.add_theme_stylebox_override("panel", _stil())
	karte.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	karte.grow_vertical = Control.GROW_DIRECTION_BEGIN
	karte.mouse_filter = Control.MOUSE_FILTER_STOP
	karte.gui_input.connect(_auf_eingabe)
	add_child(karte)

	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A3)
	karte.add_child(spalte)

	# Griff oben -- zeigt, dass man das Menue wegwischen kann.
	var griff_zeile := CenterContainer.new()
	griff_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(griff_zeile)
	var griff := Panel.new()
	griff.custom_minimum_size = Vector2(72.0, 8.0)
	var griff_stil := StyleBoxFlat.new()
	griff_stil.bg_color = UiStil.TINTE_3
	griff_stil.set_corner_radius_all(UiStil.RADIUS_CHIP)
	griff.add_theme_stylebox_override("panel", griff_stil)
	griff.mouse_filter = Control.MOUSE_FILTER_IGNORE
	griff_zeile.add_child(griff)

	streifen = PanelContainer.new()
	streifen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(streifen)

	kopf = HBoxContainer.new()
	kopf.add_theme_constant_override("separation", UiStil.A3)
	kopf.mouse_filter = Control.MOUSE_FILTER_IGNORE
	streifen.add_child(kopf)

	titel = UiStil.label("", UiStil.GR_GROSS + 2, UiStil.TINTE, UiStil.FETT)
	titel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	titel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	titel.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	titel.clip_text = true
	kopf.add_child(titel)

	_schliessen = TextureButton.new()
	_schliessen.texture_normal = UiStil.symbol("schliessen")
	_schliessen.ignore_texture_size = true
	_schliessen.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	_schliessen.custom_minimum_size = Vector2(UiStil.TIPPZIEL, UiStil.TIPPZIEL * 0.8)
	_schliessen.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_schliessen.pressed.connect(schliessen)
	kopf.add_child(_schliessen)

	inhalt = VBoxContainer.new()
	inhalt.add_theme_constant_override("separation", UiStil.A4)
	spalte.add_child(inhalt)
	_faerbe_akzent()


func _stil() -> StyleBox:
	var s := UiStil.sticker(UiStil.papier_welt(), UiStil.RADIUS_KARTE + 10, UiStil.KONTUR, float(UiStil.A4), 0.0,
		UiStil.akzent_tief())
	s.flaeche.corner_radius_bottom_left = 0
	s.flaeche.corner_radius_bottom_right = 0
	s.flaeche.border_width_bottom = 0
	s.content_margin_top = float(UiStil.A3)
	s.content_margin_bottom = float(UiStil.A5)
	return s


## Der Titelstreifen folgt der Welt. Geprueft bei jedem Oeffnen -- nach einem
## Weltwechsel steht die neue Farbe da, ohne dass jemand Bescheid sagen muss.
func _faerbe_akzent() -> void:
	var farbe: Color = UiStil.akzent()
	if farbe == _akzent_gesetzt:
		return
	_akzent_gesetzt = farbe
	karte.add_theme_stylebox_override("panel", _stil())
	var s := UiStil.sticker(farbe, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0)
	s.content_margin_left = float(UiStil.A4)
	s.content_margin_right = float(UiStil.A2)
	s.content_margin_top = float(UiStil.A2)
	s.content_margin_bottom = float(UiStil.A2)
	streifen.add_theme_stylebox_override("panel", s)
	titel.add_theme_color_override("font_color", UiStil.akzent_text())
	akzent_geaendert()


## Unterklassen faerben hier ihre eigenen Teile im Titelstreifen nach.
func akzent_geaendert() -> void:
	pass


func ist_offen() -> bool:
	return _offen


func oeffnen() -> void:
	_faerbe_akzent()
	karte.offset_left = 0.0
	karte.offset_right = 0.0
	visible = true
	aktualisiere()
	if _offen:
		return
	_setze_versatz(EINFAHRT)
	_offen = true
	# Einfahren von unten ueber den ABSTAND von unten, nicht ueber die Position:
	# Menues bauen ihren Inhalt beim Oeffnen neu, die Hoehe waechst noch
	# waehrend der Bewegung. Eine festgeschriebene Position schob das Menue
	# dann ueber die Menueleiste.
	karte.modulate.a = 0.0
	if _tween != null:
		_tween.kill()
	var t := create_tween().set_parallel(true)
	_tween = t
	t.tween_method(_setze_versatz, EINFAHRT, 0.0, DAUER).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(karte, "modulate:a", 1.0, DAUER * 0.7)


func _setze_versatz(versatz: float) -> void:
	karte.offset_bottom = -unten_frei + versatz
	karte.offset_top = karte.offset_bottom - karte.get_combined_minimum_size().y


## Wird der Inhalt kuerzer (weniger Ziele), schrumpft die Karte mit -- von
## allein wuerde sie nur wachsen.
func _process(_delta: float) -> void:
	if _offen and karte.size.y > karte.get_combined_minimum_size().y + 1.0:
		karte.offset_top = karte.offset_bottom - karte.get_combined_minimum_size().y


func schliessen() -> void:
	if not _offen:
		return
	_offen = false
	if _tween != null:
		_tween.kill()
	var t := create_tween().set_parallel(true)
	_tween = t
	t.tween_method(_setze_versatz, 0.0, EINFAHRT, DAUER * 0.8).set_ease(Tween.EASE_IN)
	t.tween_property(karte, "modulate:a", 0.0, DAUER * 0.8)
	t.chain().tween_callback(func() -> void:
		if not _offen:
			visible = false
			_setze_versatz(0.0))
	geschlossen.emit()


## Ohne Ausblenden zu: Wechselt die Hud zu einem anderen Menue, darf das alte
## nicht als Geist durchschimmern (Befund B1: zwei Panels zugleich).
func schliessen_sofort() -> void:
	if not _offen and not visible:
		return
	_offen = false
	if _tween != null:
		_tween.kill()
	visible = false
	karte.modulate.a = 1.0
	_setze_versatz(0.0)
	geschlossen.emit()


## Hoehe der Karte, fuer die Kamera: Sie faehrt die gewaehlte Station ueber das Menue.
func kartenhoehe() -> float:
	return karte.size.y


## Wird von der Hud aufgerufen, wenn sich Geld oder Zustand geaendert haben.
func aktualisiere() -> void:
	pass


## Werte aus data/ui/sheet.json (einmal gelesen).
static var _konfig: Dictionary = {}


static func konfig() -> Dictionary:
	if _konfig.is_empty():
		var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/ui/sheet.json"))
		if roh is Dictionary:
			_konfig = roh as Dictionary
	return _konfig


## Ab dieser Bewegung ist eine Beruehrung ein Wisch und kein Tipp.
static func tipp_schwelle() -> float:
	return float(konfig().get("tipp_schwelle_px", 14.0))


## Unterkante des Kopfbereichs (Griff + Titelstreifen) in Koordinaten der Karte.
## Nur dort beginnende Wische duerfen das Menue schliessen -- ein Wisch im
## Inhalt scrollt, auch wenn er schnell ist oder ueber den Rand hinausgeht.
func kopfzone_bis() -> float:
	var stil: StyleBox = karte.get_theme_stylebox("panel")
	var oben: float = stil.get_margin(SIDE_TOP) if stil != null else 0.0
	var spalte: BoxContainer = streifen.get_parent() as BoxContainer
	var trenn: float = float(spalte.get_theme_constant("separation")) if spalte != null else 0.0
	var griff_zeile: Control = spalte.get_child(0) as Control if spalte != null else null
	var griff_h: float = griff_zeile.get_combined_minimum_size().y if griff_zeile != null else 0.0
	return oben + griff_h + trenn + maxf(streifen.size.y, streifen.get_combined_minimum_size().y)


## Nach unten wischen schliesst -- aber nur ein Wisch, der im Kopf beginnt.
## Jede Beruehrung im Panel gehoert dem Panel und erreicht nie die Karte.
func _auf_eingabe(ereignis: InputEvent) -> void:
	if ereignis is InputEventScreenTouch:
		var b := ereignis as InputEventScreenTouch
		_ziehen_start = b.position.y if b.pressed and b.position.y <= kopfzone_bis() else -1.0
		karte.accept_event()
	elif ereignis is InputEventScreenDrag:
		karte.accept_event()
		if _ziehen_start < 0.0:
			return
		var d := ereignis as InputEventScreenDrag
		if d.position.y - _ziehen_start > float(konfig().get("schliess_wisch_px", 90.0)):
			_ziehen_start = -1.0
			schliessen()


# --- Bausteine fuer Unterklassen --------------------------------------------------

## Der Hauptknopf (Limette). `farbe` und `tief` bleiben fuer alte Aufrufer --
## eine andere Flaeche als Limette ist nur fuer Belohnungen (Gold) gedacht.
static func kaufknopf(farbe: Color = UiStil.KAUFEN, _tief: Color = UiStil.TINTE) -> Button:
	return UiStil.kaufknopf(farbe)


## Eine Papierkarte innerhalb eines Sheets.
static func innenkarte(innen: float = UiStil.A3) -> PanelContainer:
	var karte_neu := PanelContainer.new()
	karte_neu.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, innen))
	return karte_neu


static func balken_mit_text() -> Array:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A1 + 2)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var text := UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT)
	box.add_child(text)
	var balken := UiStil.neuer_balken(20.0)
	box.add_child(balken)
	return [box, text, balken]


static func sterne(anzahl: int, von: int, kante: float = 30.0) -> HBoxContainer:
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", 0)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for i in range(von):
		zeile.add_child(UiStil.symbolbild("stern" if i < anzahl else "stern_leer", kante))
	return zeile


## Die Kaufpille (K6 4.3) -- dasselbe Muster wie UiStil.kaufpille, hier fuer
## alle Sheets bequem zur Hand. Mit `pille` wird nur neu beschriftet.
static func kaufpille(daten: Dictionary, pille: Button = null) -> Button:
	return UiStil.kaufpille(daten, pille)


## Wert aus dem Abschnitt `bereich` von data/ui/sheet.json (z. B. "raum_panel").
static func konfig_wert(bereich: String, schluessel: String, ersatz: Variant) -> Variant:
	var abschnitt: Variant = konfig().get(bereich, {})
	if abschnitt is Dictionary:
		return (abschnitt as Dictionary).get(schluessel, ersatz)
	return ersatz


## Hoechste Kartenhoehe fuer ein Sheet, das `anteil` der Bildhoehe samt
## Menueleiste (`unten_frei`) nicht ueberschreiten soll -- die Welt bleibt oben.
func max_kartenhoehe(anteil: float) -> float:
	var voll: float = size.y
	if voll <= 1.0 and is_inside_tree():
		voll = get_viewport().get_visible_rect().size.y
	return maxf(voll * anteil - unten_frei, 160.0)


## Der Glanz nach einem Kauf: ein heller Streifen huscht ueber die Pille.
func pille_glanz(pille: Button) -> void:
	var streifen_k: ColorRect = pille.get_node_or_null("Glanz") as ColorRect if pille != null else null
	if streifen_k == null or not pille.is_inside_tree():
		return
	var dauer: float = float(konfig_wert("raum_panel", "glanz_s", 0.42))
	streifen_k.visible = true
	streifen_k.size.y = pille.size.y
	streifen_k.position = Vector2(-streifen_k.size.x, 0.0)
	var t := create_tween()
	t.tween_property(streifen_k, "position:x", pille.size.x, dauer).set_trans(Tween.TRANS_SINE)
	t.tween_callback(func() -> void: streifen_k.visible = false)
