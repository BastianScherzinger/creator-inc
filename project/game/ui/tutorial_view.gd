## Zeigt den laufenden Tutorialschritt: eine Karte mit Text, ein pulsierender
## Ring um das gemeinte Element und ein Pfeil, der darauf zeigt.
##
## Die Entscheidung, WELCHER Schritt laeuft, faellt in TutorialAblauf. Hier
## steht nur, wie er aussieht.
##
## Kein abdunkelnder Vollbild-Schleier und keine Eingabesperre: Wer schon weiss,
## was er tut, soll weiterspielen koennen, waehrend der Hinweis steht. Ein
## Tutorial, das die Hand fuehrt, nimmt die Hand -- und ein Idle-Game lebt
## davon, dass man selbst darauf kommt.
##
## Sticker-Pop: Der Ring ist ein Aufkleber -- dicke Tinte aussen, Akzentfarbe
## innen, harter Schatten. Vorher war es ein duennes gelbes Rechteck, das auf
## dem Holzboden fast verschwand und nach Platzhalter aussah.
class_name TutorialView
extends Control

## Der Ring atmet, statt zu blinken. Blinken zieht den Blick mit Gewalt und
## macht nach dem dritten Mal nervoes; Atmen fuehrt ihn.
const PULS_DAUER: float = 1.4
const RING_FARBE_STAERKE: float = 7.0
const RING_TINTE_STAERKE: float = 13.0
const RING_RAND: float = 12.0
## Radius des Rings um einen Punkt in der Welt (Station, Raum).
const WELT_RADIUS: float = 84.0
const PFEIL_ABSTAND: float = 18.0
## Pfeile der Kette: Abstand zum Ring, Staerke und Laenge der Spitze.
const KETTE_ABSTAND: float = 22.0
const KETTE_STAERKE: float = 10.0
const KETTE_KOPF: float = 34.0
## Platzbedarf der seitlich liegenden Hand (Laenge zum Ziel hin, halbe Hoehe) und
## Versatz, mit dem sie bei Kollision nach oben/unten ausweicht.
const HAND_LAENGE: float = 140.0
const HAND_HALBE_HOEHE: float = 46.0
const HAND_AUSWEICH_Y: float = 60.0
## Randpfeil (K7): Liegt das Ziel ausserhalb des Bildes, steht statt des Rings ein Pfeil am
## Rand, der in seine Richtung zeigt. Vorher hielt die Ansicht den Ring am Rand fest -- dort
## stand eine ANDERE Station, und der Spieler tippte die falsche (Schritt "upload").
## Radius des Aufklebers, Abstand zum Bildrand, Laenge der Spitze.
const RAND_PFEIL_RADIUS: float = 44.0
const RAND_PFEIL_ABSTAND: float = 20.0
const RAND_PFEIL_SPITZE: float = 22.0

signal ueberspringen_gedrueckt
## Der Spieler tippt den Randpfeil: Die Kamera darf einmal zum Ziel schieben (K6 4.1: vom
## Spieler ausgeloest).
signal rand_pfeil_gedrueckt

var _karte: PanelContainer
var _streifen: Panel
var _titel: Label
var _text: Label
var _ueberspringen: Button

## Wohin zeigt der Ring? Entweder ein Control oder ein Punkt in der Welt --
## die Stationen sind keine Oberflaechenelemente, muessen aber gezeigt werden.
var _ziel_control: Control = null
var _ziel_welt: Vector3 = Vector3.ZERO
var _hat_ziel_welt: bool = false
var _kamera: Camera3D = null

## Liefert die Bildschirmrechtecke der Marker (Abzeichen, Pillen), denen die Hand ausweicht.
var meide: Callable = Callable()

## Die Kette (K2 3, "kette"): Weltpunkte der Stationen in Reihenfolge. Zwischen ihnen zeichnet
## die Ansicht Pfeile; der Ring der langsamsten Station wird dann rot (Rot gehoert dem Engpass).
var _kette: Array[Vector3] = []
var _ring_rot: bool = false

var _zeit: float = 0.0
var _hand: ZeigeHand = null
## Nur der Rahmen, keine Hand: das Ziel zeigt etwas, das man noch nicht antippen kann
## (Ziel-Geschenk, solange das Ziel nicht erreicht ist).
var _ohne_hand: bool = false
## Das Porträt der Figur, die den Hinweis spricht (Schlüssel aus dem Thema; Standard "mo").
var _figur: String = "mo"
var _figur_feld: Control = null
var _aussen: HBoxContainer = null
## Kompakt (ein Sheet ist offen): nur der Text als schmale Zeile, ohne Titel und
## Porträt -- das Sheet behält den Platz, die Welt bleibt oben sichtbar.
var _kompakt: bool = false
var _basis_titel: String = ""
var _basis_text: String = ""
var _zusatz: String = ""
## Zeigt die Hand von oben auf einen Knopf der Menueleiste, hebt sich die Karte um
## ihre Hoehe an -- sonst lag der Finger mitten im Kartentext.
const HAND_HUB: float = 96.0
var _unten: float = 0.0
var _hub: float = 0.0
## Oberkante des freien Kartenbereichs (unter Kopfleiste und Auftragskarten).
var _oben: float = 0.0
## Randpfeil: Knopf (Tippziel), Mitte und Richtung zum Ziel; aktiv nur, solange das Ziel
## ausserhalb des freien Bereichs liegt.
var _pfeil_knopf: Button = null
var _pfeil_aktiv: bool = false
var _pfeil_mitte: Vector2 = Vector2.ZERO
var _pfeil_richtung: Vector2 = Vector2.RIGHT


func _ready() -> void:
	# set_anchors_UND_offsets_preset, nicht nur set_anchors_preset: Letzteres
	# rechnet die Offsets so um, dass das AKTUELLE Rechteck erhalten bleibt --
	# bei einem frisch erzeugten Control ist das (0,0,0,0). Die Ansicht war
	# damit null Pixel breit, und die Karte darin schrumpfte auf ihre
	# Minimalbreite. Im Bild sah es aus wie ein Gestaltungsfehler.
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# Der Tutorial-Layer darf keine Eingaben schlucken -- nur der
	# Ueberspringen-Knopf nimmt welche an.
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = UiStil.thema()
	_baue_karte()
	_hand = ZeigeHand.new()
	add_child(_hand)
	_baue_pfeil_knopf()
	visible = false


## Unsichtbarer Knopf ueber dem gezeichneten Randpfeil -- das Tippziel (>= 48 dp).
func _baue_pfeil_knopf() -> void:
	_pfeil_knopf = Button.new()
	_pfeil_knopf.flat = true
	for zustand in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		_pfeil_knopf.add_theme_stylebox_override(zustand, StyleBoxEmpty.new())
	var seite: float = maxf(UiStil.TIPPZIEL, RAND_PFEIL_RADIUS * 2.0 + 16.0)
	_pfeil_knopf.size = Vector2(seite, seite)
	_pfeil_knopf.mouse_filter = Control.MOUSE_FILTER_STOP
	_pfeil_knopf.visible = false
	_pfeil_knopf.pressed.connect(func() -> void: rand_pfeil_gedrueckt.emit())
	add_child(_pfeil_knopf)


## Mitte des Randpfeils, solange er steht, sonst (-1,-1) -- fuer die PC-Testumgebung.
func rand_pfeil_punkt() -> Vector2:
	return _pfeil_mitte if _pfeil_aktiv and visible else Vector2(-1.0, -1.0)


## Weltpunkt, auf den der Ring zeigt (fuer die Kamerafahrt nach dem Randpfeil).
func ziel_welt() -> Variant:
	return _ziel_welt if _hat_ziel_welt else null


## Oberkante des freien Bereichs: Darueber stehen Kopfleiste und Auftragskarten.
func setze_oben(oben: float) -> void:
	_oben = oben


func _baue_karte() -> void:
	_karte = PanelContainer.new()
	# UNTEN verankert, direkt ueber der Bedienung -- und wachsend nach OBEN.
	#
	# Vier Anlaeufe hat diese Zeile gebraucht, und drei davon waren am PC
	# eingestellt. Das PC-Vorschaufenster wurde auf die Bildschirmhoehe gekappt
	# und hatte damit ein anderes Seitenverhaeltnis als das Handy: Dort stand
	# die Karte unter dem Raum, auf dem Geraet mitten darauf. Eine Position von
	# OBEN gemessen stimmt nur fuer eine Bildschirmhoehe. Von UNTEN gemessen
	# stimmt sie fuer alle, weil die Bedienung selbst unten verankert ist.
	_karte.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_karte.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_karte.offset_left = float(UiStil.A4)
	_karte.offset_right = -float(UiStil.A4)
	_karte.offset_top = -272.0
	_karte.offset_bottom = -272.0
	_karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var stil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A4))
	stil.content_margin_left = float(UiStil.A3)
	_karte.add_theme_stylebox_override("panel", stil)
	add_child(_karte)

	var aussen := HBoxContainer.new()
	aussen.add_theme_constant_override("separation", UiStil.A4)
	aussen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_karte.add_child(aussen)
	_aussen = aussen

	# Ein Streifen in der Akzentfarbe: Der Hinweis gehoert zur Welt.
	_streifen = Panel.new()
	_streifen.custom_minimum_size = Vector2(10.0, 0.0)
	_streifen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	aussen.add_child(_streifen)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A1)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	aussen.add_child(box)

	# Titel und Ausstieg in EINER Zeile.
	#
	# Untereinander brauchte die Karte 360 Pixel, und die passen zwischen
	# Raum und Aktionsknopf nicht hinein -- im Vorschaubild lag die Karte auf
	# dem Ausbau-Feld. Der Ausstieg braucht seine 88 Pixel Tippziel ohnehin
	# nur in der Hoehe, und die teilt er sich hier mit dem Titel.
	var kopf := HBoxContainer.new()
	kopf.add_theme_constant_override("separation", UiStil.A3)
	kopf.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(kopf)

	_titel = UiStil.label("", UiStil.GR_GROSS - 2, UiStil.TINTE, UiStil.FETT)
	_titel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_titel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_titel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kopf.add_child(_titel)

	# Der Ausstieg ist leise und rechts: Er muss gross genug zum Treffen sein,
	# darf aber nicht wie die empfohlene Handlung aussehen: flacher Text,
	# kein Aufkleber.
	_ueberspringen = Button.new()
	_ueberspringen.flat = true
	for zustand in ["normal", "hover", "pressed", "hover_pressed", "focus"]:
		_ueberspringen.add_theme_stylebox_override(zustand, StyleBoxEmpty.new())
	_ueberspringen.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
	_ueberspringen.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_KLEIN))
	_ueberspringen.add_theme_color_override("font_color", UiStil.TINTE_2)
	_ueberspringen.add_theme_color_override("font_hover_color", UiStil.TINTE)
	_ueberspringen.add_theme_color_override("font_pressed_color", UiStil.TINTE)
	_ueberspringen.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL * 0.75)
	_ueberspringen.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	_ueberspringen.mouse_filter = Control.MOUSE_FILTER_STOP
	_ueberspringen.pressed.connect(func() -> void: ueberspringen_gedrueckt.emit())
	kopf.add_child(_ueberspringen)

	_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.TEXT_GEWICHT)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.max_lines_visible = 4
	_text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	box.add_child(_text)


## Einen Schritt anzeigen. Leerer Titel bedeutet: nichts zeigen.
func zeige(titel: String, text: String, ueberspringen_text: String, figur: String = "mo") -> void:
	if titel.is_empty() and text.is_empty():
		visible = false
		if _hand != null:
			_hand.verbirg()
		return
	_setze_figur(figur)
	var neu: bool = _basis_titel != titel or not visible
	_basis_titel = titel
	_basis_text = text
	_zusatz = ""
	_zeige_texte()
	_ueberspringen.text = ueberspringen_text
	var streifen_stil := StyleBoxFlat.new()
	streifen_stil.bg_color = UiStil.akzent()
	streifen_stil.set_corner_radius_all(UiStil.RADIUS_CHIP)
	streifen_stil.border_color = UiStil.TINTE
	streifen_stil.set_border_width_all(UiStil.KONTUR_CHIP)
	_streifen.add_theme_stylebox_override("panel", streifen_stil)
	visible = true
	_zeit = 0.0
	if neu:
		UiStil.aufploppen.call_deferred(_karte, 0.94)
	queue_redraw()


## Nur der Text wechselt (Platzhalter wie "+0,9 €/s" aendern sich laufend); die Karte poppt nicht neu auf.
func setze_text(text: String) -> void:
	if text == _basis_text:
		return
	_basis_text = text
	_zeige_texte()


## Die Pfeile der Kette ein- oder ausschalten. Leer = aus. `rot`: Der Ring der Zielstation ist rot.
func setze_kette(punkte: Array[Vector3], rot: bool, kamera: Camera3D = null) -> void:
	_kette = punkte
	if kamera != null:
		_kamera = kamera
	_ring_rot = rot and not punkte.is_empty()


## Kompakte Zeile, solange ein Sheet offen ist.
func setze_kompakt(kompakt: bool) -> void:
	if kompakt == _kompakt:
		return
	_kompakt = kompakt
	_zeige_texte()


## Zusatzzeile (z. B. "Noch 120 €"), wenn das Ziel gerade nicht erreichbar ist.
func setze_zusatz(zusatz: String) -> void:
	if zusatz == _zusatz:
		return
	_zusatz = zusatz
	_zeige_texte()


func _zeige_texte() -> void:
	if _titel == null:
		return
	var text: String = _basis_text
	if not _zusatz.is_empty():
		text += "  " + _zusatz if _kompakt else "
" + _zusatz
	if _kompakt:
		_titel.text = text
		_text.visible = false
	else:
		_titel.text = _basis_titel
		_text.text = text
		_text.visible = true
	if _figur_feld != null:
		_figur_feld.visible = not _kompakt
	# K6 1c (Handy-Befund 2): ueber einem offenen Panel hoechstens zwei Zeilen, ohne Ausstieg --
	# Panel, Zielleiste und Karte verdeckten zusammen zwei Drittel des Bildes.
	_titel.max_lines_visible = 2 if _kompakt else -1
	_titel.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS if _kompakt else TextServer.OVERRUN_NO_TRIMMING
	_ueberspringen.visible = not _kompakt
	_titel.add_theme_font_size_override("font_size", UiStil.GR_TEXT if _kompakt else UiStil.GR_GROSS - 2)


## Wie viel Platz unten frei bleiben muss: Menueleiste oder offenes Menue.
## Die Karte steht immer DARUEBER -- ein Hinweis, der das verdeckt, worauf er
## zeigt, ist keiner.
func setze_unten(abstand: float) -> void:
	if _karte == null:
		return
	_unten = abstand
	_setze_karte_offset()


func _setze_karte_offset() -> void:
	_karte.offset_top = -_unten - _hub - float(UiStil.A4)
	_karte.offset_bottom = -_unten - _hub - float(UiStil.A4)


func _setze_hub(hub: float) -> void:
	if is_equal_approx(hub, _hub) or _karte == null:
		return
	_hub = hub
	_setze_karte_offset()


func kartenhoehe() -> float:
	return _karte.size.y if _karte != null and _karte.visible else 0.0


## Karte weg, Hand und Ring bleiben: Das offene Panel sagt schon alles.
func setze_karte_aus(aus: bool) -> void:
	if _karte != null:
		_karte.visible = not aus


func verbergen() -> void:
	visible = false
	_kette = []
	_ring_rot = false
	if _hand != null:
		_hand.verbirg()


## Das Porträt links in der Karte -- die Figur spricht, statt dass ein Kasten belehrt.
func _setze_figur(figur: String) -> void:
	if _aussen == null or (figur == _figur and _figur_feld != null):
		return
	_figur = figur
	if _figur_feld != null:
		_figur_feld.queue_free()
		_figur_feld = null
	if UiStil.portrait(figur) == null:
		return
	_figur_feld = UiStil.avatar(figur, UiStil.akzent(), 96.0)
	_aussen.add_child(_figur_feld)
	_aussen.move_child(_figur_feld, 1)
	_figur_feld.visible = not _kompakt


func setze_ohne_hand(ohne: bool) -> void:
	_ohne_hand = ohne


func zeige_auf_control(ziel: Control) -> void:
	_ziel_control = ziel
	_hat_ziel_welt = false


func zeige_auf_welt(punkt: Vector3, kamera: Camera3D) -> void:
	_ziel_welt = punkt
	_kamera = kamera
	_hat_ziel_welt = true
	_ziel_control = null


func ohne_ziel() -> void:
	_ziel_control = null
	_hat_ziel_welt = false


func _process(delta: float) -> void:
	if not visible:
		return
	_zeit += delta
	_aktualisiere_pfeil()
	queue_redraw()


## Liegt der Weltpunkt ausserhalb des freien Bereichs (Bild ohne Kopfleiste oben und ohne
## Karte/Menue unten), steht der Randpfeil am Rand dieses Bereichs in Richtung des Ziels.
func _aktualisiere_pfeil() -> void:
	var aktiv: bool = false
	if _ziel_control == null and _hat_ziel_welt and _kamera != null and is_instance_valid(_kamera) \
			and not _kamera.is_position_behind(_ziel_welt):
		var frei: Rect2 = _freier_bereich()
		var p: Vector2 = _kamera.unproject_position(_ziel_welt)
		if not frei.has_point(p) and frei.size.x > 0.0 and frei.size.y > 0.0:
			aktiv = true
			var mitte: Vector2 = frei.get_center()
			var richtung: Vector2 = (p - mitte).normalized()
			var innen: Rect2 = frei.grow(-(RAND_PFEIL_RADIUS + RAND_PFEIL_ABSTAND))
			if innen.size.x <= 0.0 or innen.size.y <= 0.0:
				innen = Rect2(mitte, Vector2.ZERO)
			# Schnitt des Strahls Mitte -> Ziel mit dem inneren Rechteck.
			var tx: float = INF
			var ty: float = INF
			if absf(richtung.x) > 0.0001:
				tx = ((innen.end.x if richtung.x > 0.0 else innen.position.x) - mitte.x) / richtung.x
			if absf(richtung.y) > 0.0001:
				ty = ((innen.end.y if richtung.y > 0.0 else innen.position.y) - mitte.y) / richtung.y
			_pfeil_mitte = mitte + richtung * maxf(minf(tx, ty), 0.0)
			_pfeil_richtung = richtung
	_pfeil_aktiv = aktiv
	if _pfeil_knopf != null:
		_pfeil_knopf.visible = aktiv
		if aktiv:
			_pfeil_knopf.position = _pfeil_mitte - _pfeil_knopf.size * 0.5


## Der Teil des Bildes, in dem ein Ring sinnvoll steht: unter Kopfleiste/Auftragskarten,
## ueber Tutorialkarte bzw. offenem Menue.
func _freier_bereich() -> Rect2:
	var sicht: Vector2 = get_viewport_rect().size
	var unten: float = sicht.y - _unten
	if _karte != null and _karte.visible:
		unten = minf(unten, _karte.get_global_rect().position.y)
	var oben: float = clampf(_oben, 0.0, unten)
	return Rect2(0.0, oben, sicht.x, unten - oben)


func _draw() -> void:
	var akzent: Color = UiStil.WARNUNG if _ring_rot else UiStil.akzent()
	_zeichne_kette()
	var anteil: float = fmod(_zeit, PULS_DAUER) / PULS_DAUER
	var atmen: float = sin(_zeit * TAU / PULS_DAUER) * 3.0
	var rechteck: Rect2 = Rect2()
	var mitte: Vector2
	var hub: float = 0.0
	var radius: float = 0.0
	if _ziel_control != null and _ziel_control.is_visible_in_tree():
		rechteck = _ziel_control.get_global_rect().grow(RING_RAND + atmen)
		mitte = rechteck.get_center()
	elif _hat_ziel_welt and _kamera != null and is_instance_valid(_kamera):
		# Hinter der Kamera liegende Punkte wuerden gespiegelt auf dem Schirm
		# landen -- ein Ring an der falschen Stelle ist schlimmer als keiner.
		if _kamera.is_position_behind(_ziel_welt):
			_hand.verbirg()
			return
		# Ziel ausserhalb: Randpfeil statt Ring. Den Ring am Rand festzuhalten setzte ihn
		# auf eine andere Station (K7).
		if _pfeil_aktiv:
			_zeichne_rand_pfeil(atmen)
			_hand.verbirg()
			_setze_hub.call_deferred(0.0)
			return
		mitte = _kamera.unproject_position(_ziel_welt)
		radius = WELT_RADIUS + atmen
	else:
		_hand.verbirg()
		_setze_hub(0.0)
		return

	# (hub wird unten gesetzt; Rueckkehr ohne Menueleisten-Ziel bringt die Karte zurueck.)
	# Aeussere Welle: weitet sich und verblasst.
	var welle: Color = akzent
	welle.a = (1.0 - anteil) * 0.7
	var weitung: float = RING_RAND * 2.5 * anteil
	if radius > 0.0:
		draw_arc(mitte, radius + weitung, 0.0, TAU, 64, welle, RING_FARBE_STAERKE)
		_zeichne_ring_kreis(mitte, radius, akzent)
		# Die Hand liegt neben dem Ring, nicht darunter: Unter dem Ziel stehen Raumkauf-Pille,
		# Namenschip und Lv-Abzeichen der Nachbarstationen. Gewaehlt wird die breitere Seite.
		var links_frei: bool = mitte.x >= get_viewport_rect().size.x - mitte.x
		var seite: int = 1 if links_frei else -1
		var abstand: float = radius + RING_TINTE_STAERKE * 0.5
		var dy: float = 0.0
		var wahl: Vector2 = _hand_platz(mitte, abstand, seite)
		seite = int(wahl.x)
		dy = wahl.y
		_hand.zeige_bei(Vector2(mitte.x - float(seite) * abstand, mitte.y + dy), false, seite)
	else:
		_zeichne_rahmen(rechteck.grow(weitung), welle, RING_FARBE_STAERKE)
		_zeichne_ring_rahmen(rechteck, akzent)
		# Die Zeigehand: von unten auf das Ziel. Breite Knoepfe am unteren Rand (Hauptknopf
		# eines Panels): Die Hand tippt am rechten Ende in den Knopf, statt Text zu verdecken.
		if _ohne_hand:
			_hand.verbirg()
			_setze_hub.call_deferred(0.0)
			return
		var breit: bool = rechteck.size.x > 360.0
		var x: float = rechteck.end.x - 80.0 if breit else mitte.x
		var y: float = mitte.y - 6.0 if breit else mitte.y + rechteck.size.y * 0.2
		var ganz_unten: bool = not breit and rechteck.position.y > get_viewport_rect().size.y - Menueleiste.HOEHE * 1.5
		if ganz_unten:
			# Menueleiste: unter dem Knopf ist kein Platz, die Hand kommt von oben.
			_hand.zeige_bei(Vector2(mitte.x, rechteck.position.y - PFEIL_ABSTAND), true)
			hub = HAND_HUB
		else:
			_hand.zeige_bei(Vector2(x, y))
	_setze_hub.call_deferred(hub)


## Pfeile von Station zu Station: dicke Tinte aussen, Akzent innen, wie der Ring. Sie laufen in
## Richtung der Kette und pulsieren leicht mit; die Enden bleiben vor den Ringen der Stationen.
func _zeichne_kette() -> void:
	if _kette.size() < 2 or _kamera == null or not is_instance_valid(_kamera):
		return
	var schub: float = 0.5 + 0.5 * sin(_zeit * TAU / PULS_DAUER)
	for i in range(_kette.size() - 1):
		if _kamera.is_position_behind(_kette[i]) or _kamera.is_position_behind(_kette[i + 1]):
			continue
		var von: Vector2 = _kamera.unproject_position(_kette[i])
		var nach: Vector2 = _kamera.unproject_position(_kette[i + 1])
		var weg: Vector2 = nach - von
		if weg.length() < (WELT_RADIUS + KETTE_ABSTAND) * 2.0 + 20.0:
			continue
		var richtung: Vector2 = weg.normalized()
		var a: Vector2 = von + richtung * (WELT_RADIUS + KETTE_ABSTAND)
		var b: Vector2 = nach - richtung * (WELT_RADIUS + KETTE_ABSTAND)
		var seite: Vector2 = Vector2(-richtung.y, richtung.x)
		var spitze: Vector2 = b
		var fuss: Vector2 = b - richtung * KETTE_KOPF
		var schatten := Vector2(0.0, UiStil.SCHATTEN_Y)
		var farbe: Color = UiStil.akzent().lerp(Color.WHITE, 0.25 * schub)
		draw_line(a + schatten, fuss + schatten, UiStil.TINTE, KETTE_STAERKE + 8.0)
		draw_line(a, fuss, UiStil.TINTE, KETTE_STAERKE + 8.0)
		draw_line(a, fuss, farbe, KETTE_STAERKE)
		var kopf := PackedVector2Array([spitze, fuss + seite * KETTE_KOPF * 0.62, fuss - seite * KETTE_KOPF * 0.62])
		var kopf_rand := PackedVector2Array([
			spitze + richtung * 6.0, fuss + seite * (KETTE_KOPF * 0.62 + 6.0), fuss - seite * (KETTE_KOPF * 0.62 + 6.0)])
		draw_colored_polygon(kopf_rand, UiStil.TINTE)
		draw_colored_polygon(kopf, farbe)


## Waehlt Seite (x: +1/-1) und senkrechten Versatz (y) der Hand so, dass sie keinen Marker
## verdeckt. Bevorzugt die breitere Seite ohne Versatz; sonst die Stelle mit der kleinsten
## ueberdeckten Flaeche.
func _hand_platz(mitte: Vector2, abstand: float, bevorzugt: int) -> Vector2:
	var marker: Array[Rect2] = []
	if meide.is_valid():
		marker = meide.call()
	var kandidaten: Array[Vector2] = []
	for versatz in [0.0, -HAND_AUSWEICH_Y, HAND_AUSWEICH_Y]:
		kandidaten.append(Vector2(float(bevorzugt), versatz))
		kandidaten.append(Vector2(float(-bevorzugt), versatz))
	var bestes: Vector2 = kandidaten[0]
	var wenigste: float = INF
	var sicht: Rect2 = Rect2(Vector2.ZERO, get_viewport_rect().size)
	for k in kandidaten:
		var s: int = int(k.x)
		var spitze := Vector2(mitte.x - float(s) * abstand, mitte.y + k.y)
		var x0: float = spitze.x - HAND_LAENGE if s == 1 else spitze.x
		var r := Rect2(x0, spitze.y - HAND_HALBE_HOEHE, HAND_LAENGE, HAND_HALBE_HOEHE * 2.0)
		var flaeche: float = 0.0
		for m in marker:
			var u: Rect2 = r.intersection(m)
			flaeche += u.size.x * u.size.y
		# Ragt die Hand aus dem Bild, zaehlt das wie eine Kollision.
		var drin: Rect2 = r.intersection(sicht)
		flaeche += r.size.x * r.size.y - drin.size.x * drin.size.y
		if flaeche < wenigste:
			wenigste = flaeche
			bestes = k
		if flaeche <= 0.0:
			break
	return bestes


## Der Randpfeil: runder Aufkleber (Schatten, Tinte, Akzent) mit einer Spitze, die zum Ziel
## zeigt. Er atmet wie der Ring und schiebt sich leicht in Zielrichtung.
func _zeichne_rand_pfeil(atmen: float) -> void:
	var r: Vector2 = _pfeil_richtung
	var mitte: Vector2 = _pfeil_mitte + r * atmen
	var schatten := Vector2(0.0, UiStil.SCHATTEN_Y)
	var radius: float = RAND_PFEIL_RADIUS
	draw_circle(mitte + schatten, radius + RING_TINTE_STAERKE * 0.5, UiStil.TINTE)
	draw_circle(mitte, radius + RING_TINTE_STAERKE * 0.5, UiStil.TINTE)
	draw_circle(mitte, radius, UiStil.akzent())
	# Spitze ausserhalb des Kreises, in Zielrichtung.
	var quer: Vector2 = Vector2(-r.y, r.x)
	var fuss: Vector2 = mitte + r * (radius - 4.0)
	var spitze: Vector2 = mitte + r * (radius + RAND_PFEIL_SPITZE)
	var breite: float = RAND_PFEIL_SPITZE * 0.9
	draw_colored_polygon(PackedVector2Array([spitze + r * 7.0, fuss + quer * (breite + 7.0), fuss - quer * (breite + 7.0)]), UiStil.TINTE)
	draw_colored_polygon(PackedVector2Array([spitze, fuss + quer * breite, fuss - quer * breite]), UiStil.akzent())
	# Innen ein Pfeil aus Tinte -- auch ohne Farbe lesbar.
	var a: Vector2 = mitte - r * radius * 0.45
	var b: Vector2 = mitte + r * radius * 0.4
	draw_line(a, b, UiStil.TINTE, 8.0)
	draw_colored_polygon(PackedVector2Array([b + r * 12.0, b - r * 6.0 + quer * 14.0, b - r * 6.0 - quer * 14.0]), UiStil.TINTE)


## Der Ring um einen Weltpunkt: harter Schatten, Tinte, Akzent.
func _zeichne_ring_kreis(mitte: Vector2, radius: float, akzent: Color) -> void:
	var schatten := Vector2(0.0, UiStil.SCHATTEN_Y)
	draw_arc(mitte + schatten, radius, 0.0, TAU, 64, UiStil.TINTE, RING_TINTE_STAERKE)
	draw_arc(mitte, radius, 0.0, TAU, 64, UiStil.TINTE, RING_TINTE_STAERKE)
	draw_arc(mitte, radius, 0.0, TAU, 64, akzent, RING_FARBE_STAERKE)


## Der Ring um ein Bedienelement: abgerundetes Rechteck in denselben Schichten.
func _zeichne_ring_rahmen(r: Rect2, akzent: Color) -> void:
	_zeichne_rahmen(Rect2(r.position + Vector2(0.0, UiStil.SCHATTEN_Y), r.size), UiStil.TINTE, RING_TINTE_STAERKE)
	_zeichne_rahmen(r, UiStil.TINTE, RING_TINTE_STAERKE)
	_zeichne_rahmen(r, akzent, RING_FARBE_STAERKE)


func _zeichne_rahmen(r: Rect2, farbe: Color, staerke: float) -> void:
	var box := StyleBoxFlat.new()
	box.draw_center = false
	box.border_color = farbe
	box.set_border_width_all(int(staerke))
	box.set_corner_radius_all(UiStil.RADIUS_KARTE + 6)
	box.anti_aliasing = true
	var halb: float = staerke * 0.5
	draw_style_box(box, r.grow(halb))
