## P1.9 (K4/K5): Das Hinweis-Vokabular wird EINMAL erklaert. Beim ersten Auftreten
## jedes Plakettenzustands (kaufbar, fast, gesperrt, bremst) und von Stapel und
## Kiste erscheint eine kleine Sprechblase am Element ("Gruen: Hier kannst du
## jetzt kaufen."), danach nie wieder (gesehen-Flags im Spielstand, SaveData.hinweise).
##
## Nie zusammen mit einem Fenster: Die Blase stellt sich hinten in die
## ModalSchlange (Art "hinweis") und macht Platz, sobald sich etwas anderes
## anmeldet. Sie kommt auch nicht, solange ein Panel offen ist, die Tutorialkarte
## spricht oder eine Ortsblase steht -- es fordert immer nur EINE Ebene etwas (P1.7).
## K6 1c: nur noch im Tutorial bzw. in den ersten Spielminuten (`symbol_blase_bis_s`,
## Hud.symbol_erlaubt) -- danach kennt man die Zeichen.
##
## Texte: data/i18n (symbol_<art>), Zeiten: data/ui/hinweise.json.
class_name SymbolHinweise
extends Control

## Reihenfolge, in der erklaert wird, wenn mehreres zugleich neu ist.
const ARTEN: Array[StringName] = [&"kaufbar", &"fast", &"bremst", &"gesperrt", &"kiste", &"stapel"]

signal gesehen_geaendert

var marker: Kartenmarker
## Darf jetzt erklaert werden? (Hud: kein Panel, kein Tutorial, keine Pruefvorschau.)
var darf: Callable = Callable()

var _gesehen: Array[String] = []
var _rest: float = 0.0
var _ruhe: float = 0.0
var _blase: Control
var _blase_anker: Control
var _blase_rest: float = 0.0
var _fertig: Callable = Callable()


## Die naechste Art, die erklaert werden soll: die erste noch ungesehene, die gerade
## sichtbar ist. "" = nichts. Rein, ohne Baum (getestet).
static func naechste(gesehen: Array, sichtbar: Array) -> String:
	for art in ARTEN:
		if not gesehen.has(String(art)) and (sichtbar.has(art) or sichtbar.has(String(art))):
			return String(art)
	return ""


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func gesehen() -> Array[String]:
	return _gesehen.duplicate()


func gesehen_setzen(liste: Array) -> void:
	_gesehen.clear()
	for e in liste:
		if not _gesehen.has(String(e)):
			_gesehen.append(String(e))


func ist_offen() -> bool:
	return _blase != null and is_instance_valid(_blase)


func _process(delta: float) -> void:
	if ist_offen():
		_folge_anker(delta)
		return
	var schlange: ModalSchlange = ModalSchlange.global()
	if schlange.ist_beschaeftigt():
		_ruhe = 0.0
		return
	_ruhe += delta
	_rest -= delta
	if _rest > 0.0:
		return
	_rest = Kartenmarker.hinweis("symbol_blase_takt_s")
	if _ruhe < Kartenmarker.hinweis("symbol_blase_pause_s") or marker == null:
		return
	if darf.is_valid() and not bool(darf.call()):
		return
	var sichtbar: Array[StringName] = []
	for art in ARTEN:
		if not _gesehen.has(String(art)) and marker.hinweis_anker(art) != null:
			sichtbar.append(art)
	var art_jetzt: String = naechste(_gesehen, sichtbar)
	if art_jetzt.is_empty() or not UiText.hat("symbol_" + art_jetzt):
		return
	schlange.anmelden(&"hinweis", func(fertig: Callable) -> void: _zeige(StringName(art_jetzt), fertig))


func _zeige(art: StringName, fertig: Callable) -> void:
	var anker: Control = marker.hinweis_anker(art) if marker != null else null
	if anker == null:
		fertig.call()
		return
	_gesehen.append(String(art))
	gesehen_geaendert.emit()
	_fertig = fertig
	_blase_anker = anker
	_blase_rest = Kartenmarker.hinweis("symbol_blase_dauer_s")
	var farbe: Color = UiStil.GOLD if art == &"kiste" or art == &"stapel" else UiStil.plaketten_farbe(art)
	_blase = _baue_blase(UiText.t("symbol_" + String(art)), farbe)
	add_child(_blase)
	_setze_position()
	UiStil.aufploppen.call_deferred(_blase, 0.6)
	# Alles andere geht vor: Meldet sich ein Fenster an, raeumt die Blase das Feld.
	var schlange: ModalSchlange = ModalSchlange.global()
	if not schlange.angemeldet.is_connected(_auf_anmeldung):
		schlange.angemeldet.connect(_auf_anmeldung)


func _auf_anmeldung(art: StringName) -> void:
	if ModalSchlange.LEICHT.has(art):
		return
	schliesse()


## Blase weg und die Schlange freigeben.
func schliesse() -> void:
	if ist_offen():
		_blase.queue_free()
	_blase = null
	_blase_anker = null
	var f: Callable = _fertig
	_fertig = Callable()
	if f.is_valid():
		f.call()


func _input(ereignis: InputEvent) -> void:
	# Jeder Tipp schliesst die Blase -- der Tipp selbst geht trotzdem durch.
	if ist_offen() and (ereignis is InputEventScreenTouch or ereignis is InputEventMouseButton) and ereignis.is_pressed():
		schliesse.call_deferred()


func _folge_anker(delta: float) -> void:
	_blase_rest -= delta
	if _blase_rest <= 0.0 or _blase_anker == null or not is_instance_valid(_blase_anker) \
			or not _blase_anker.is_visible_in_tree():
		schliesse()
		return
	_setze_position()


## Ueber dem Element, waagerecht mittig, im Bild gehalten; passt es oben nicht, darunter.
func _setze_position() -> void:
	if _blase == null or _blase_anker == null or marker == null:
		return
	var r: Rect2 = marker.anker_rechteck(_blase_anker)
	var karte: Control = _blase.get_node("Karte") as Control
	var groesse: Vector2 = karte.get_combined_minimum_size()
	karte.size = groesse
	_blase.size = groesse
	var breite: float = get_viewport_rect().size.x
	var x: float = clampf(r.get_center().x - groesse.x * 0.5, float(UiStil.A4), breite - groesse.x - float(UiStil.A4))
	var y: float = r.position.y - groesse.y - float(UiStil.A3)
	var oben: bool = y >= marker.oben_frei
	if not oben:
		y = r.end.y + float(UiStil.A3)
	_blase.position = Vector2(x, y)
	var zipfel: Control = _blase.get_node_or_null("Zipfel") as Control
	if zipfel != null:
		zipfel.position = Vector2(clampf(r.get_center().x - x, 28.0, groesse.x - 28.0) - 10.0,
			groesse.y - 12.0 if oben else -8.0)


func _baue_blase(text: String, farbe: Color) -> Control:
	# Aussen ein freies Control: darin hinten der Zipfel, davor die Karte. (In einem
	# Container wuerde der Zipfel auf Kartengroesse gezogen.)
	var blase := Control.new()
	blase.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var zipfel := Panel.new()
	zipfel.name = "Zipfel"
	zipfel.size = Vector2(20.0, 20.0)
	zipfel.pivot_offset = Vector2(10.0, 10.0)
	zipfel.rotation_degrees = 45.0
	zipfel.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, 3, UiStil.KONTUR, 0.0, 0.0))
	zipfel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	blase.add_child(zipfel)
	var karte := PanelContainer.new()
	karte.name = "Karte"
	karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	karte.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3), UiStil.SCHATTEN_Y))
	var reihe := HBoxContainer.new()
	reihe.add_theme_constant_override("separation", UiStil.A2)
	reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Farbpunkt im Ton des Zeichens: Die Blase erklaert genau diese Farbe.
	var punkt := Panel.new()
	punkt.custom_minimum_size = Vector2(22.0, 22.0)
	punkt.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	punkt.add_theme_stylebox_override("panel", UiStil.sticker(farbe, UiStil.RADIUS_CHIP, UiStil.KONTUR_CHIP, 0.0, 0.0))
	punkt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reihe.add_child(punkt)
	var l := UiStil.label(text, UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(Kartenmarker.hinweis("symbol_blase_breite_px") - 60.0, 0.0)
	reihe.add_child(l)
	karte.add_child(reihe)
	blase.add_child(karte)
	return blase
