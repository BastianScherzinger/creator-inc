## Die Kopfleiste: Rang-Stern mit Balken, zwei grosse Zahlen (Geld und +EUR/s),
## Weltfortschritt, Zahnrad.
##
## Oben stehen Informationen, unten ist Bedienung (ART_DIRECTION 5). Die Leiste
## ist deshalb bis auf drei Stellen nicht antippbar: der Stern (oeffnet den Fortschritt),
## der Weltfortschritt (oeffnet die Uebersicht) und das Zahnrad.
##
## Der Rang steht als Stern mit kleinem Balken links -- wie der Ruf in Idle Bank Tycoon.
## Kein Rang-Chip, keine Rang-Toasts: Ein Aufstieg fuellt den Balken und laesst den Stern
## aufploppen, mehr nicht. Der Stern erscheint erst nach dem Tutorial.
##
## Das Welt-Ziel (z. B. "Der Gaming-PC", sonst der Weltname) steht als Chip in der Akzentfarbe UEBER dem Balken, die
## Prozentzahl NEBEN dem Balken. Vorher teilten sich Name und Prozent eine
## Zeile -- bei laengeren Namen lag "5,0 %" mitten im Wort.
class_name Kopfleiste
extends Control

signal fortschritt_gedrueckt
signal einstellungen_gedrueckt
## Eine bereite Geschenk-Marke auf dem Weltbalken wurde angetippt (ID aus kern.marken_liste()).
signal marke_getippt(marke_id: StringName)
## Die Leiste ist hoeher geworden als HOEHE (groessere Schrift, zweite Zeile im Fortschrittsfeld).
signal hoehe_geaendert

## Die angezeigte Zahl laeuft dem Kapital weich hinterher, statt zu springen.
## Ein Zaehler, der sichtbar hochlaeuft, ist Belohnung; einer, der springt, ist
## eine Zahl.
const ZAEHL_TEMPO: float = 10.0
const HOEHE: float = 100.0
## Abstand von oben: Statusleiste und Kamera-Aussparung (Safe Area).
const OBEN: float = 46.0
## Kantenlaenge einer Geschenk-Marke auf dem Weltbalken.
const MARKE: float = 34.0
## Rang-Stern links: Kantenlaenge des Sterns und Breite seiner Spalte.
const STERN_KANTE: float = 66.0
const STERN_BREITE: float = 78.0
## Wie oft der Stern beim Hud nachfragt (Sekunden) -- billig, aber nicht jeden Frame.
const STERN_TAKT: float = 0.4

var geld_feld: PanelContainer
var _zeile: HBoxContainer
var muenze: TextureRect
var _kapital: Label
var _einkommen: Label
var _stern_feld: PanelContainer
var _stern_zahl: Label
var _stern_balken: ProgressBar
var _stern_rang: int = 0
var _stern_manuell: bool = false
var _stern_takt: float = 0.0
var _fortschritt_feld: PanelContainer
var _welt_chip: PanelContainer
var _welt: Label
var _marke_hinweis: Label
var _prozent: Label
var _balken: ProgressBar
var _angezeigt: float = 0.0
var _ziel: float = 0.0
var _akzent_gesetzt: Color = Color(0, 0, 0, 0)
var _einkommen_zuletzt: String = ""
var _marken: Array[Control] = []
var _marken_ebene: Control
var _marken_signatur: String = "-"


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	offset_top = OBEN
	offset_left = float(UiStil.A4)
	offset_right = -float(UiStil.A4)
	offset_bottom = OBEN + HOEHE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_baue()


func _baue() -> void:
	var zeile := HBoxContainer.new()
	zeile.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(zeile)
	_zeile = zeile
	zeile.minimum_size_changed.connect(_passe_hoehe_an)

	# Rang-Stern: Stern mit der Rangzahl, darunter ein kleiner Balken bis zum naechsten Rang.
	_stern_feld = PanelContainer.new()
	_stern_feld.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	_stern_feld.custom_minimum_size = Vector2(STERN_BREITE, 0.0)
	_stern_feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_stern_feld.mouse_filter = Control.MOUSE_FILTER_STOP
	_stern_feld.visible = false
	_stern_feld.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			UiStil.eindruecken(_stern_feld)
			fortschritt_gedrueckt.emit())
	zeile.add_child(_stern_feld)
	var stern_spalte := VBoxContainer.new()
	stern_spalte.add_theme_constant_override("separation", 0)
	stern_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	stern_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stern_feld.add_child(stern_spalte)
	var stern_halter := Control.new()
	stern_halter.custom_minimum_size = Vector2(STERN_KANTE, STERN_KANTE)
	stern_halter.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	stern_halter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stern_spalte.add_child(stern_halter)
	var stern_bild := UiStil.symbolbild("stern", STERN_KANTE)
	stern_bild.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	stern_halter.add_child(stern_bild)
	_stern_zahl = UiStil.label("1", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_stern_zahl.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_stern_zahl.offset_top = 6.0
	_stern_zahl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_stern_zahl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	stern_halter.add_child(_stern_zahl)
	_stern_balken = UiStil.neuer_balken(12.0, UiStil.GOLD)
	_stern_balken.custom_minimum_size = Vector2(STERN_BREITE - 6.0, 12.0)
	_stern_balken.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	stern_spalte.add_child(_stern_balken)

	# Geld: zwei grosse Zahlen, Kontostand und +EUR/s.
	geld_feld = PanelContainer.new()
	var gstil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0)
	gstil.content_margin_left = float(UiStil.A2)
	gstil.content_margin_right = float(UiStil.A3)
	geld_feld.add_theme_stylebox_override("panel", gstil)
	geld_feld.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	geld_feld.size_flags_stretch_ratio = 1.0
	geld_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(geld_feld)
	var geld := HBoxContainer.new()
	geld.add_theme_constant_override("separation", UiStil.A2)
	geld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	geld_feld.add_child(geld)
	muenze = UiStil.symbolbild("muenze", 54.0)
	muenze.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	geld.add_child(muenze)
	var geld_spalte := VBoxContainer.new()
	geld_spalte.add_theme_constant_override("separation", -8)
	geld_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	geld_spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	geld_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	geld.add_child(geld_spalte)
	_kapital = UiStil.label("0 €", UiStil.GR_TITEL, UiStil.TINTE, UiStil.FETT)
	_kapital.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_kapital.clip_text = true
	geld_spalte.add_child(_kapital)
	_einkommen = UiStil.label("", UiStil.GR_MITTEL, UiStil.PLUS_TEXT, UiStil.FETT)
	_einkommen.clip_text = true
	_einkommen.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_einkommen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	geld_spalte.add_child(_einkommen)

	# Fortschritt der Welt
	_fortschritt_feld = PanelContainer.new()
	var fstil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0)
	fstil.content_margin_left = float(UiStil.A2)
	fstil.content_margin_right = float(UiStil.A3)
	fstil.content_margin_top = float(UiStil.A2)
	fstil.content_margin_bottom = float(UiStil.A2)
	_fortschritt_feld.add_theme_stylebox_override("panel", fstil)
	_fortschritt_feld.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_fortschritt_feld.mouse_filter = Control.MOUSE_FILTER_STOP
	_fortschritt_feld.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			UiStil.eindruecken(_fortschritt_feld)
			fortschritt_gedrueckt.emit())
	_fortschritt_feld.visible = false
	zeile.add_child(_fortschritt_feld)
	var fort_spalte := VBoxContainer.new()
	fort_spalte.add_theme_constant_override("separation", UiStil.A2)
	fort_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	fort_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fortschritt_feld.add_child(fort_spalte)

	_welt_chip = PanelContainer.new()
	_welt_chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fort_spalte.add_child(_welt_chip)
	_welt = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE, UiStil.FETT)
	_welt.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_welt.clip_text = true
	_welt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_welt_chip.add_child(_welt)

	var balken_zeile := HBoxContainer.new()
	balken_zeile.add_theme_constant_override("separation", UiStil.A2)
	balken_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fort_spalte.add_child(balken_zeile)
	_balken = UiStil.neuer_balken(18.0)
	_balken.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_balken.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	balken_zeile.add_child(_balken)
	# Ebene fuer die Geschenk-Marken: liegt auf dem Balken, nimmt keine Eingabe,
	# nur die Marken selbst sind antippbar.
	_marken_ebene = Control.new()
	_marken_ebene.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_marken_ebene.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_balken.add_child(_marken_ebene)
	_balken.resized.connect(_lege_marken)
	_prozent = UiStil.label("", UiStil.GR_KLEIN + 2, UiStil.TINTE, UiStil.FETT)
	_prozent.custom_minimum_size = Vector2(64.0, 0.0)
	_prozent.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	balken_zeile.add_child(_prozent)
	# Name der naechsten Zwischenmarke ("Stativ steht") -- leer, wenn keine aussteht.
	_marke_hinweis = UiStil.label("", UiStil.GR_KLEIN - 2, UiStil.TINTE, UiStil.FETT)
	_marke_hinweis.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_marke_hinweis.clip_text = true
	_marke_hinweis.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_marke_hinweis.visible = false
	fort_spalte.add_child(_marke_hinweis)

	# Einstellungen
	var zahnrad := TextureButton.new()
	zahnrad.texture_normal = UiStil.symbol("zahnrad")
	zahnrad.ignore_texture_size = true
	zahnrad.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	zahnrad.custom_minimum_size = Vector2(UiStil.TIPPZIEL - 20.0, UiStil.TIPPZIEL - 20.0)
	var zahnrad_feld := PanelContainer.new()
	var zstil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0)
	zstil.set_content_margin_all(float(UiStil.A1 + 2))
	zahnrad_feld.add_theme_stylebox_override("panel", zstil)
	zahnrad_feld.custom_minimum_size = Vector2(UiStil.TIPPZIEL, UiStil.TIPPZIEL)
	zahnrad_feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zahnrad_feld.add_child(zahnrad)
	zahnrad.pressed.connect(func() -> void:
		UiStil.eindruecken(zahnrad_feld)
		einstellungen_gedrueckt.emit())
	zeile.add_child(zahnrad_feld)
	_faerbe_akzent()


func _faerbe_akzent() -> void:
	var farbe: Color = UiStil.akzent()
	if farbe == _akzent_gesetzt:
		return
	_akzent_gesetzt = farbe
	_welt_chip.add_theme_stylebox_override("panel", UiStil.chip(farbe, float(UiStil.A2), 1.0, 0.0))
	_welt.add_theme_color_override("font_color", UiStil.akzent_text())
	UiStil.faerbe_balken(_balken, farbe)


func setze(kapital: float, einkommen: float, welt_text: String, anteil: float, zeige_fortschritt: bool) -> void:
	_faerbe_akzent()
	_ziel = kapital
	if absf(_angezeigt - _ziel) > absf(_ziel) * 0.5 and _ziel < _angezeigt:
		# Nach einem grossen Kauf nicht langsam herunterzaehlen -- das saehe
		# aus, als liefe das Geld davon.
		_angezeigt = _ziel
	var einkommen_text: String = "+%s %s" % [_einkommen_kurz(einkommen), UiText.t("pro_sekunde")]
	_einkommen.text = einkommen_text
	# Steigt das Einkommen, federt die Zahl kurz auf -- man SIEHT, dass der Kauf wirkte.
	if not _einkommen_zuletzt.is_empty() and einkommen_text != _einkommen_zuletzt and _einkommen.is_inside_tree():
		_einkommen_feder()
	_einkommen_zuletzt = einkommen_text
	_welt.text = welt_text
	# Unter zehn Prozent mit Nachkommastelle: "0 %" nach fuenf Minuten Arbeit
	# sagt, dass nichts passiert ist. "0,8 %" sagt, dass es angefangen hat.
	if anteil < 0.1:
		_prozent.text = ("%.1f %%" % (floorf(anteil * 1000.0) / 10.0)).replace(".", ",")
	else:
		_prozent.text = "%d %%" % int(floorf(anteil * 100.0))
	_balken.value = anteil
	# Das Weltziel steht in der eigenen Leiste unter dem Kopf (Hud); das Feld hier bleibt
	# als stiller Datenhalter bestehen, damit alte Aufrufer nicht brechen, und ist nie sichtbar.
	_fortschritt_feld.visible = false


func _process(delta: float) -> void:
	_stern_takt -= delta
	if _stern_takt <= 0.0:
		_stern_takt = STERN_TAKT
		_hole_rang()
	if is_equal_approx(_angezeigt, _ziel):
		return
	_angezeigt = lerpf(_angezeigt, _ziel, clampf(delta * ZAEHL_TEMPO, 0.0, 1.0))
	if absf(_angezeigt - _ziel) < maxf(absf(_ziel) * 0.0005, 0.5):
		_angezeigt = _ziel
	_setze_kapital(_geld_text(_angezeigt))


## Setzt den Kontostand und verkleinert die Schrift stufenweise, bis er ganz ins Feld passt
## ("197,8 Mio €" stand vorher als "197,8 Mi..." da).
func _setze_kapital(text: String) -> void:
	_kapital.text = text
	var breite: float = _kapital.size.x
	if breite <= 8.0:
		return
	var schrift: Font = _kapital.get_theme_font("font")
	var gr: int = UiStil.GR_TITEL
	while gr > UiStil.GR_TITEL - 14 and schrift.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, gr).x > breite:
		gr -= 2
	_kapital.add_theme_font_size_override("font_size", gr)


## Geld hat immer eine Einheit: "12.531 EUR-Zeichen" statt nackter Zahl (Befund B6).
static func _geld_text(wert: float) -> String:
	return UiStil.zahl(wert) + " €"


## Breite Einkommen kuerzen (K/Mio), damit die Level-Pille daneben nie ueberlappt.
static func _einkommen_kurz(wert: float) -> String:
	if wert >= 100000.0 and wert < 1.0e6:
		return "%.0f K" % (wert / 1000.0)
	if wert >= 10000.0 and wert < 1.0e6:
		return ("%.1f K" % (wert / 1000.0)).replace(".", ",")
	return UiStil.zahl(wert)


## `rang_name` (ab P2 der Name des Rangs, z. B. "Hobby") steht hinter der Zahl; leer = nur "Rang 3".
## Name der naechsten Zwischenmarke unter dem Balken; leer blendet die Zeile aus.
func setze_marke_hinweis(text: String) -> void:
	_marke_hinweis.text = text
	_marke_hinweis.visible = not text.is_empty()


## Laengster Rangname, der noch in den Chip passt. Laengere Namen stehen nur im Rang-Up-Moment;
## der Chip zeigt dann die Nummer.
const RANG_NAME_MAX: int = 11


## Text des Rang-Chips: der Rangname, wenn er Platz hat, sonst "Rang N" (K2 4.1).
static func rang_chip_text(rang: int, rang_name: String) -> String:
	if not rang_name.is_empty() and rang_name.length() <= RANG_NAME_MAX:
		return rang_name
	return UiText.t("rang") % rang


## Rang-Chip und Rang-Toasts gibt es nicht mehr (K6 4.6): Der Rang steht als Stern links.
## Die Funktion bleibt, damit alte Aufrufer nicht brechen; sie zeigt nichts mehr an.
func setze_level(_level: int, _rang_name: String = "") -> void:
	pass


## Frueher: Rang-Chip an/aus. Der Chip ist weg; der Stern entscheidet selbst (nach dem Tutorial).
func zeige_rang(_sichtbar: bool) -> void:
	pass


## Rang-Stern direkt setzen: `rang` (1 ...), `anteil` (0 ... 1) = Weg zum naechsten Rang.
## Wer das aufruft, steuert den Stern selbst; ohne Aufruf fragt er das Hud (siehe _hole_rang).
## Ein neuer, hoeherer Rang laesst den Stern aufploppen -- stumm, kein Fenster.
func setze_rang(rang: int, anteil: float) -> void:
	_stern_manuell = true
	_zeige_rang(rang, anteil, true)


func _zeige_rang(rang: int, anteil: float, sichtbar: bool) -> void:
	_stern_feld.visible = sichtbar
	_stern_zahl.text = str(rang)
	_stern_balken.value = clampf(anteil, 0.0, 1.0)
	if _stern_rang != 0 and rang > _stern_rang and is_inside_tree():
		UiStil.aufploppen(_stern_feld, 0.7)
	_stern_rang = rang


## Fragt das Hud (der Eltern-Knoten) nach Rang und Fortschritt zum naechsten Rang. Im
## Tutorial bleibt der Stern weg: Ein Rang ohne Erklaerung ist nur eine Zahl.
func _hole_rang() -> void:
	if _stern_manuell:
		return
	var hud: Hud = get_parent() as Hud
	if hud == null or hud.kern == null:
		return
	var info: Dictionary = hud.kern.spieler_level_info()
	var rang: int = int(info.get("rang", 1))
	var von: int = int(info.get("schwelle", 0))
	var bis: int = int(info.get("naechste_schwelle", von))
	var anteil: float = 1.0 if bis <= von else clampf(float(int(info.get("punkte", 0)) - von) / float(bis - von), 0.0, 1.0)
	_zeige_rang(rang, anteil, not hud.tutorial_aktiv)


func zeige_sofort() -> void:
	_angezeigt = _ziel
	_setze_kapital(_geld_text(_angezeigt))


## Die Muenze zuckt, wenn Geld ankommt -- das Ziel der fliegenden Muenzen.
func muenze_puls() -> void:
	UiStil.aufploppen(muenze, 1.2)


## Rechts neben der Einkommenszeile -- dort erscheinen Verluste (Welt 6).
func einkommen_rechts() -> Vector2:
	# Das Label ist so breit wie das Geldfeld -- gemessen wird der TEXT.
	var r: Rect2 = _einkommen.get_global_rect()
	# Unter dem Geldfeld statt in der Einkommenszeile: dort sitzt rechts die Level-Pille,
	# und die rote Zahl lief ueber sie hinweg.
	var unten: float = geld_feld.get_global_rect().end.y - 2.0
	return Vector2(r.position.x + float(UiStil.A2), unten)


## Unterkante der Leiste in Bildschirmkoordinaten -- alles darunter richtet sich danach.
static func unterkante() -> float:
	return OBEN + HOEHE


## Tatsaechliche Unterkante: waechst der Inhalt ueber HOEHE hinaus (grosse Schrift auf
## dem Handy), liegt sie tiefer. Der Stapel darunter richtet sich danach (K3-Fix 4).
func unterkante_ist() -> float:
	var inhalt: float = _zeile.get_combined_minimum_size().y if _zeile != null else 0.0
	return OBEN + maxf(HOEHE, inhalt)


func _ready() -> void:
	_passe_hoehe_an.call_deferred()


func _passe_hoehe_an() -> void:
	offset_bottom = unterkante_ist()
	hoehe_geaendert.emit()


func _einkommen_feder() -> void:
	_einkommen.pivot_offset = Vector2(0.0, _einkommen.size.y * 0.5)
	var t := create_tween()
	t.tween_property(_einkommen, "scale", Vector2(1.15, 1.15), 0.08)
	t.tween_property(_einkommen, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## Geschenk-Marken auf dem Weltbalken. `marken` = `kern.marken_liste()`:
## Dictionaries {id, wert (0..1), bereit, eingeloest}. Eine bereite Marke pulsiert
## in Gold; ein Tipp darauf meldet `marke_getippt`. Neu gebaut wird nur, wenn
## sich etwas geaendert hat.
func setze_marken(marken: Array) -> void:
	var signatur: String = ""
	for m in marken:
		var d0: Dictionary = m as Dictionary
		signatur += "%s:%s:%s;" % [d0.get("id", ""), d0.get("bereit", false), d0.get("eingeloest", false)]
	if signatur == _marken_signatur:
		return
	_marken_signatur = signatur
	for m in _marken:
		m.queue_free()
	_marken.clear()
	for m in marken:
		var d: Dictionary = m as Dictionary
		var geholt: bool = bool(d.get("eingeloest", false))
		var bereit: bool = bool(d.get("bereit", false))
		var knopf := GeschenkMarke.new(MARKE)
		knopf.setze_zustand(GeschenkMarke.Zustand.OFFEN if geholt else (
			GeschenkMarke.Zustand.ERREICHBAR if bereit else GeschenkMarke.Zustand.ZU))
		knopf.mouse_filter = Control.MOUSE_FILTER_STOP if bereit else Control.MOUSE_FILTER_IGNORE
		var marke_id := StringName(String(d.get("id", "")))
		knopf.gui_input.connect(func(e: InputEvent) -> void:
			if bereit and UiStil.ist_tipp(e):
				marke_getippt.emit(marke_id))
		knopf.set_meta("anteil", float(d.get("wert", 0.0)))
		knopf.set_meta("id", String(marke_id))
		_marken_ebene.add_child(knopf)
		_marken.append(knopf)
	_lege_marken()


## Bildschirmmitte einer Marke -- dort starten Muenzen und Funken.
func marke_mitte(marke_id: StringName) -> Vector2:
	for m in _marken:
		if StringName(String(m.get_meta("id", ""))) == marke_id:
			return m.get_global_rect().get_center()
	return _balken.get_global_rect().get_center()


func _lege_marken() -> void:
	for m in _marken:
		m.position = Vector2(_balken.size.x * float(m.get_meta("anteil", 0.0)) - MARKE * 0.5,
			_balken.size.y * 0.5 - MARKE * 0.5)

