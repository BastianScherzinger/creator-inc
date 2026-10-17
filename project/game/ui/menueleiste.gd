## Die Menueleiste unten: vier Knoepfe und in der Mitte der grosse runde Boost-Knopf.
##
## Fuenf feste Plaetze wie in jedem Spiel des Genres (Vorbild: die Unterleiste von
## Idle Bank Tycoon): Firma, Auftraege, BOOST (Mitte), Posteingang, Fortschritt.
## Die Mitte gehoert dem Belohnungsschub -- gross, rund, ragt ueber die Leiste, steht
## als "BOOST x1,5" im Kreis. Er ist das einzige Angebot im Spiel, und es steht dort,
## wo der Daumen ohnehin liegt, statt als Pop-up zu unterbrechen.
##
## Jeder Platz ist als GANZES antippbar (Symbol und Beschriftung, volle Hoehe
## der Leiste). Die Symbole sitzen auf einer Kachel; wartet etwas, sitzt ein roter
## Zahl-Punkt an ihrer Ecke: einloesbare Ziele, ungelesene Nachrichten, bezahlbare Kaeufe.
##
## Gesperrte Plaetze fehlen ganz (Freischaltung nach Rang, siehe erfolge.json). Ein
## neu erscheinender Platz ploppt auf; die Mitte kommt mit einem Ring, der sich ausbreitet.
class_name Menueleiste
extends Control

signal gewaehlt(schluessel: StringName)

const HOEHE: float = 150.0
## Fuenfter Platz: der Fortschritt (Rang). Ein Laden-Knopf waere bei leerem Regal
## eine Enttaeuschung mit Abzeichen-Platz; der Laden wohnt in den Einstellungen.
const PUNKTE: Array[StringName] = [&"ausbau", &"ziele", &"schub", &"handy", &"fortschritt"]
const SYMBOLE: Dictionary = {
	&"ausbau": "werkzeug", &"ziele": "ziel", &"schub": "blitz", &"handy": "handy", &"fortschritt": "stern",
}
## Breite eines Platzes. Fest, damit wenige Knoepfe nicht auf die ganze Leistenbreite
## gezogen werden, sondern mittig nebeneinander stehen.
const PLATZ_BREITE: float = 136.0
const KANTE_SEITE: float = 68.0
const KANTE_MITTE: float = 120.0
## Wie weit der Mittelknopf ueber die Leiste ragt.
const MITTE_UEBERSTAND: float = 30.0
## Wie gross das Symbol in seiner Kachel ist (Anteil der Kachel).
const SYMBOL_ANTEIL: float = 0.66
const PUNKT_KANTE: float = 32.0
const ERSCHEINEN_DAUER: float = 0.55

var _knoepfe: Dictionary = {}     ## schluessel -> Control (Symbolbereich, fuer das Tutorial)
var _plaetze: Dictionary = {}     ## schluessel -> Button (der ganze Platz; hier wird ein-/ausgeblendet)
var _texte: Dictionary = {}       ## schluessel -> Label
var _abzeichen: Dictionary = {}   ## schluessel -> [PanelContainer, Label]
var _mitte: PanelContainer
var _mitte_titel: Label
var _mitte_faktor: Label
var _mitte_video: Control
var _glut: Panel
var _puls: float = 0.0
var _schub_bereit: bool = false
## Der Boost laeuft gerade (Dauer-Boost, K3 C1): Knopf bleibt farbig, atmet aber nicht.
var _schub_laeuft: bool = false
var _akzent_gesetzt: Color = Color(0, 0, 0, 0)
var _grund: PanelContainer
var _grund_farbe: Color = Color(0, 0, 0, 0)
var _faktor_regel: RegEx
## Platzhalter links und rechts: halten den Boost in der Mitte, wenn eine Seite weniger Knoepfe hat.
var _abstand_links: Control
var _abstand_rechts: Control


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	offset_top = -HOEHE
	offset_bottom = 0.0
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_faktor_regel = RegEx.new()
	_faktor_regel.compile("×\\s*([0-9]+(?:[.,][0-9]+)?)")
	_baue()


func _baue() -> void:
	var grund := PanelContainer.new()
	grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	grund.offset_top = MITTE_UEBERSTAND - 8.0
	_grund = grund
	_faerbe_grund()
	grund.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(grund)

	var zeile := HBoxContainer.new()
	zeile.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	zeile.add_theme_constant_override("separation", 0)
	zeile.alignment = BoxContainer.ALIGNMENT_CENTER
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(zeile)

	_abstand_links = _neuer_abstand()
	zeile.add_child(_abstand_links)
	for schluessel in PUNKTE:
		var mitte: bool = schluessel == &"schub"
		# Der ganze Platz ist ein flacher Knopf; Kachel und Text liegen darauf.
		var platz := Button.new()
		platz.flat = true
		for zustand in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
			platz.add_theme_stylebox_override(zustand, StyleBoxEmpty.new())
		platz.size_flags_horizontal = Control.SIZE_FILL
		platz.custom_minimum_size = Vector2(PLATZ_BREITE, HOEHE)
		zeile.add_child(platz)
		_plaetze[schluessel] = platz

		var spalte := VBoxContainer.new()
		spalte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		spalte.offset_top = 0.0 if mitte else MITTE_UEBERSTAND + 2.0
		spalte.offset_bottom = -float(UiStil.A2)
		spalte.add_theme_constant_override("separation", 2)
		spalte.alignment = BoxContainer.ALIGNMENT_CENTER if not mitte else BoxContainer.ALIGNMENT_BEGIN
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		platz.add_child(spalte)

		var kante: float = KANTE_MITTE if mitte else KANTE_SEITE
		var halter := Control.new()
		halter.custom_minimum_size = Vector2(kante, kante)
		halter.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		halter.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(halter)

		if mitte:
			_baue_mitte(halter)
		else:
			_baue_kachel(halter, String(SYMBOLE[schluessel]), kante)
		_knoepfe[schluessel] = halter

		var s: StringName = schluessel
		platz.pressed.connect(func() -> void:
			UiStil.aufploppen(halter, 0.9)
			gewaehlt.emit(s))

		# Der rote Zahl-Punkt an der Ecke der Kachel.
		var punkt := PanelContainer.new()
		punkt.add_theme_stylebox_override("panel", _abzeichen_stil())
		punkt.custom_minimum_size = Vector2(PUNKT_KANTE, PUNKT_KANTE)
		punkt.position = Vector2(kante - PUNKT_KANTE * 0.62, -PUNKT_KANTE * 0.3)
		punkt.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var zahl := UiStil.label("", UiStil.GR_KLEIN - 2, UiStil.WEISS, UiStil.FETT)
		zahl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		zahl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		punkt.add_child(zahl)
		punkt.visible = false
		halter.add_child(punkt)
		_abzeichen[schluessel] = [punkt, zahl]

		var text := UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE, UiStil.FETT)
		text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		text.clip_text = true
		spalte.add_child(text)
		_texte[schluessel] = text
	_abstand_rechts = _neuer_abstand()
	zeile.add_child(_abstand_rechts)
	_faerbe_mitte()


func _neuer_abstand() -> Control:
	var a := Control.new()
	a.mouse_filter = Control.MOUSE_FILTER_IGNORE
	a.custom_minimum_size = Vector2.ZERO
	return a


## Der Boost steht immer genau in der Mitte: hat die eine Seite weniger sichtbare Knoepfe, fuellt
## ein Platzhalter die Luecke. Ohne Boost stehen die sichtbaren Knoepfe einfach mittig nebeneinander.
func _balanciere() -> void:
	var links: int = 0
	var rechts: int = 0
	for schluessel in [&"ausbau", &"ziele"]:
		links += 1 if ist_frei(schluessel) else 0
	for schluessel in [&"handy", &"fortschritt"]:
		rechts += 1 if ist_frei(schluessel) else 0
	var mit_mitte: bool = ist_frei(&"schub")
	_abstand_links.custom_minimum_size.x = PLATZ_BREITE * float(maxi(0, rechts - links)) if mit_mitte else 0.0
	_abstand_rechts.custom_minimum_size.x = PLATZ_BREITE * float(maxi(0, links - rechts)) if mit_mitte else 0.0


## Eine Seitenkachel: Papier mit Kontur und hartem Schatten, das Symbol gross darauf.
func _baue_kachel(halter: Control, symbol: String, kante: float) -> void:
	var kachel := PanelContainer.new()
	kachel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	kachel.offset_bottom = -UiStil.SCHATTEN_Y
	kachel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var stil := UiStil.sticker(UiStil.PAPIER_2, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0, UiStil.SCHATTEN_Y)
	stil.set_content_margin_all(kante * (1.0 - SYMBOL_ANTEIL) * 0.5)
	kachel.add_theme_stylebox_override("panel", stil)
	halter.add_child(kachel)
	var bild := UiStil.symbolbild(symbol, kante * SYMBOL_ANTEIL)
	bild.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bild.size_flags_vertical = Control.SIZE_EXPAND_FILL
	kachel.add_child(bild)


## Der runde Mittelknopf: "BOOST" und der Faktor im Kreis, dahinter ein atmender Hof,
## in der Ecke das Video-Zeichen (der Boost kommt gegen ein freiwilliges Video).
func _baue_mitte(halter: Control) -> void:
	_glut = Panel.new()
	_glut.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_glut.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var hof := StyleBoxFlat.new()
	hof.bg_color = Color(UiStil.KAUFEN, 0.38)
	hof.set_corner_radius_all(999)
	hof.anti_aliasing = true
	_glut.add_theme_stylebox_override("panel", hof)
	_glut.visible = false
	halter.add_child(_glut)

	_mitte = PanelContainer.new()
	_mitte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	halter.add_child(_mitte)
	var innen := VBoxContainer.new()
	innen.alignment = BoxContainer.ALIGNMENT_CENTER
	innen.add_theme_constant_override("separation", -4)
	innen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mitte.add_child(innen)
	_mitte_titel = UiStil.label(UiText.t("boost_titel"), UiStil.GR_KLEIN + 2, UiStil.TINTE, UiStil.FETT)
	_mitte_titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	innen.add_child(_mitte_titel)
	_mitte_faktor = UiStil.label("", UiStil.GR_GROSS + 6, UiStil.TINTE, UiStil.FETT)
	_mitte_faktor.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	innen.add_child(_mitte_faktor)

	# Video-Zeichen: kleine Tintenscheibe mit Play-Dreieck an der unteren Ecke.
	var video := PanelContainer.new()
	var vstil := UiStil.sticker(UiStil.TINTE, 999, UiStil.KONTUR_CHIP, 0.0, 0.0, UiStil.PAPIER)
	vstil.set_content_margin_all(5.0)
	video.add_theme_stylebox_override("panel", vstil)
	video.custom_minimum_size = Vector2(36.0, 36.0)
	video.position = Vector2(KANTE_MITTE - 32.0, -6.0)
	video.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var play := UiStil.symbolbild("play", 22.0)
	play.modulate = UiStil.WEISS
	video.add_child(play)
	halter.add_child(video)
	_mitte_video = video


## Die Kante der Leiste folgt der Welt (akzent_tief).
func _faerbe_grund() -> void:
	var kante: Color = UiStil.akzent_tief()
	if kante == _grund_farbe:
		return
	_grund_farbe = kante
	var stil := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 10, UiStil.KONTUR, 0.0, 0.0, kante)
	stil.flaeche.corner_radius_bottom_left = 0
	stil.flaeche.corner_radius_bottom_right = 0
	stil.flaeche.border_width_bottom = 0
	_grund.add_theme_stylebox_override("panel", stil)


## Der rote Zahl-Punkt: Rot heisst hier "da wartet etwas", mit Papierkante abgesetzt.
func _abzeichen_stil() -> StyleBox:
	var s := UiStil.chip(UiStil.WARNUNG, 8.0, 0.0, 0.0)
	s.flaeche.border_color = UiStil.PAPIER
	s.flaeche.set_border_width_all(UiStil.KONTUR_CHIP)
	return s


func _faerbe_mitte() -> void:
	var an: bool = _schub_bereit or _schub_laeuft
	var farbe: Color = UiStil.KAUFEN if _schub_bereit else (UiStil.akzent() if _schub_laeuft else UiStil.PAPIER_2)
	if farbe == _akzent_gesetzt:
		return
	_akzent_gesetzt = farbe
	var s := UiStil.sticker(farbe, UiStil.RADIUS_CHIP, UiStil.KONTUR + 1, 0.0,
		UiStil.SCHATTEN_Y_PRIMAER if an else 0.0)
	s.set_content_margin_all(10.0)
	_mitte.add_theme_stylebox_override("panel", s)
	var schrift: Color = UiStil.text_auf(farbe) if an else Color(UiStil.TINTE, 0.55)
	_mitte_titel.add_theme_color_override("font_color", schrift)
	_mitte_faktor.add_theme_color_override("font_color", schrift)
	_mitte_video.visible = _schub_bereit
	if _glut != null:
		_glut.visible = _schub_bereit


## Blendet einen Platz ein oder aus (Rang-Gating, K2 4.1). Ein gesperrter Knopf ist gar nicht da,
## nicht ausgegraut. Ist KEIN Platz sichtbar, verschwindet die ganze Leiste. Gibt true zurueck,
## wenn der Platz dadurch neu erschienen ist.
func setze_frei(schluessel: StringName, frei: bool) -> bool:
	var platz: Button = _plaetze.get(schluessel) as Button
	if platz == null:
		return false
	var neu: bool = frei and not platz.visible
	platz.visible = frei
	visible = anzahl_sichtbar() > 0
	_balanciere()
	if neu and is_inside_tree():
		if schluessel == &"schub":
			_erscheine_mitte()
		else:
			UiStil.aufploppen(_knoepfe[schluessel] as Control, 0.3)
	return neu


## Der Boost erscheint: der Kreis waechst aus dem Nichts, ein Ring breitet sich aus.
func _erscheine_mitte() -> void:
	var halter: Control = _knoepfe[&"schub"] as Control
	halter.pivot_offset = halter.size * 0.5
	halter.scale = Vector2(0.05, 0.05)
	var t := halter.create_tween()
	t.tween_property(halter, "scale", Vector2.ONE, ERSCHEINEN_DAUER).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	var ring := Panel.new()
	ring.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rs := StyleBoxFlat.new()
	rs.bg_color = Color(0, 0, 0, 0)
	rs.border_color = UiStil.KAUFEN
	rs.set_border_width_all(8)
	rs.set_corner_radius_all(999)
	rs.anti_aliasing = true
	ring.add_theme_stylebox_override("panel", rs)
	halter.add_child(ring)
	ring.pivot_offset = halter.size * 0.5
	ring.scale = Vector2(0.9, 0.9)
	var r := ring.create_tween().set_parallel(true)
	r.tween_property(ring, "scale", Vector2(2.1, 2.1), 0.7).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	r.tween_property(ring, "modulate:a", 0.0, 0.7)
	r.chain().tween_callback(ring.queue_free)


func anzahl_sichtbar() -> int:
	var n: int = 0
	for schluessel in PUNKTE:
		var platz: Button = _plaetze.get(schluessel) as Button
		if platz != null and platz.visible:
			n += 1
	return n


func ist_frei(schluessel: StringName) -> bool:
	var platz: Button = _plaetze.get(schluessel) as Button
	return platz != null and platz.visible


func setze_text(schluessel: StringName, text: String) -> void:
	var l: Label = _texte.get(schluessel) as Label
	if l != null:
		l.text = text
	# Der Faktor steht gross im Kreis: aus dem Text der Mitte ("▶ ×1,5 · 30 Min") gelesen.
	if schluessel == &"schub":
		var treffer: RegExMatch = _faktor_regel.search(text)
		if treffer != null:
			_mitte_faktor.text = "×" + treffer.get_string(1)


func setze_abzeichen(schluessel: StringName, anzahl: int) -> void:
	var eintrag: Array = _abzeichen.get(schluessel, []) as Array
	if eintrag.is_empty():
		return
	var feld: PanelContainer = eintrag[0]
	var war: bool = feld.visible
	feld.visible = anzahl > 0
	(eintrag[1] as Label).text = str(anzahl) if anzahl < 100 else "99+"
	if feld.visible and not war:
		UiStil.aufploppen(feld, 0.3)


## Zustand des Mittelknopfs: &"aus" (grau), &"bereit" (gruen, atmet: antippen lohnt),
## &"laeuft" (Boost aktiv, ruhig, in der Akzentfarbe).
func setze_schub_zustand(zustand: StringName) -> void:
	_schub_laeuft = zustand == &"laeuft"
	setze_schub_bereit(zustand == &"bereit")


func setze_schub_bereit(bereit: bool) -> void:
	_schub_bereit = bereit
	# Vergleicht selbst: Die Farbe haengt an Bereitschaft UND Akzent der Welt.
	_faerbe_mitte()
	if not bereit and _mitte != null:
		_mitte.scale = Vector2.ONE
		if _glut != null:
			_glut.scale = Vector2.ONE


func knopf(schluessel: StringName) -> Control:
	return _knoepfe.get(schluessel) as Control


func _process(delta: float) -> void:
	_faerbe_grund()
	if not _schub_bereit:
		return
	# Der bereite Schub atmet -- sanft genug, um nicht zu nerven; der Hof atmet dagegen.
	_puls += delta
	var s: float = 1.0 + 0.04 * sin(_puls * 3.2)
	_mitte.pivot_offset = _mitte.size * 0.5
	_mitte.scale = Vector2(s, s)
	var h: float = 1.1 + 0.1 * sin(_puls * 3.2 + PI)
	_glut.pivot_offset = _glut.size * 0.5
	_glut.scale = Vector2(h, h)
