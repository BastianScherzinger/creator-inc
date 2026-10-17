## Die Rueckkehr-Karte: Waehrend du weg warst, hat dein Team gearbeitet.
##
## Der Offline-Ertrag ist ein GESCHENK, nie ein entgangener Gewinn (GAME_DESIGN
## 5.4). Die Karte macht daraus einen Moment: Das Portrait der Welt-Figur spricht
## einen Satz, der Betrag zaehlt von 0 hoch (Tween, 1,2 s), beim Einsammeln
## fliegen Muenzen. Aufgerufen wird sie von main.gd::_zeige_offline_bericht
## (docs/nacht/rp_schnittstellen.md 2).
##
## Die Karte rechnet nichts: Der Erloes ist laengst im Kern verbucht.
class_name OfflineView
extends Control

## `position` ist die Bildschirmmitte des Knopfes -- dort starten die Muenzen.
signal weiter(position: Vector2)
signal verdoppeln_gedrueckt

const ZAEHL_DAUER: float = 1.2
const ZAEHL_START: float = 0.45

var _betrag: Label
var _karte: PanelContainer
var _knopf: Button
var _verdoppeln: Button
var _erloes: float = 0.0
var _gezaehlt: float = 0.0
var _faktor: float = 1.0
var _fertig: bool = false


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()


## `thema` liefert Figur (`offline_bericht.von`) und Saetze (`offline_bericht.saetze`);
## fehlt beides, bleibt der Text `offline_bericht.text` bzw. die Standardzeile.
## `max_sekunden` = Offline-Deckel des Spielers (kern.uhr.offline_obergrenze_sekunden); 0 = Grundwert aus der Balance.
func zeige(sekunden: float, erloes: float, thema: ThemeData, verdoppeln_moeglich: bool,
		max_sekunden: float = 0.0) -> void:
	_erloes = erloes
	var schleier := ColorRect.new()
	schleier.color = UiStil.SCHLEIER
	schleier.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	schleier.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(schleier)

	var mitte := CenterContainer.new()
	mitte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(mitte)

	_karte = PanelContainer.new()
	var stil := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 10, UiStil.KONTUR + 1, float(UiStil.A5),
		UiStil.SCHATTEN_Y * 2.0)
	_karte.add_theme_stylebox_override("panel", stil)
	_karte.custom_minimum_size = Vector2(600.0, 0.0)
	mitte.add_child(_karte)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A4)
	_karte.add_child(box)

	# Kopf: Portrait der Figur, daneben Titel und Abwesenheit.
	var bericht: Dictionary = thema.abschnitt("offline_bericht") if thema != null else {}
	var von: String = String(bericht.get("von", ""))
	var kopf := HBoxContainer.new()
	kopf.add_theme_constant_override("separation", UiStil.A4)
	box.add_child(kopf)
	var farbe: Color = UiStil.absender_farbe(thema, von) if not von.is_empty() else UiStil.akzent()
	var name: String = WeltTexte.absender(thema, von) if not von.is_empty() else ""
	var avatar: PanelContainer = UiStil.avatar(name if not name.is_empty() else UiText.t("offline_titel"), farbe, 120.0)
	if UiStil.portrait(von) == null and UiStil.portrait(name) == null:
		# Ohne Portrait: die Uhr, wie bisher -- ein Kreis mit "W" waere falsch.
		avatar = PanelContainer.new()
		avatar.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_CHIP,
			UiStil.KONTUR, float(UiStil.A2), 2.0))
		avatar.custom_minimum_size = Vector2(120.0, 120.0)
		avatar.add_child(UiStil.symbolbild("uhr", 96.0))
	kopf.add_child(avatar)
	var titelspalte := VBoxContainer.new()
	titelspalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	titelspalte.alignment = BoxContainer.ALIGNMENT_CENTER
	titelspalte.add_theme_constant_override("separation", 0)
	kopf.add_child(titelspalte)
	var titel := UiStil.label(UiText.t("offline_titel"), UiStil.GR_TITEL - 4, UiStil.TINTE, UiStil.FETT)
	titel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	titelspalte.add_child(titel)
	titelspalte.add_child(UiStil.label(UiText.t("offline_weg") % WeltTexte.dauer(sekunden),
		UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT))

	# Ein Satz der Figur als Sprechblase.
	var satz: String = _satz(bericht, sekunden)
	if not satz.is_empty():
		var blase := PanelContainer.new()
		var bstil := UiStil.sticker(UiStil.PAPIER_2, UiStil.RADIUS_KARTE, UiStil.KONTUR_CHIP, float(UiStil.A3),
			0.0, farbe)
		bstil.flaeche.corner_radius_top_left = 4
		blase.add_theme_stylebox_override("panel", bstil)
		var t := UiStil.label(satz, UiStil.GR_MITTEL - 2, UiStil.TINTE, UiStil.TEXT_GEWICHT)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		blase.add_child(t)
		box.add_child(blase)

	# Der Betrag: gross, Gold, zaehlt hoch.
	var zahl_feld := PanelContainer.new()
	zahl_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3), UiStil.SCHATTEN_Y))
	box.add_child(zahl_feld)
	var zahl_zeile := HBoxContainer.new()
	zahl_zeile.alignment = BoxContainer.ALIGNMENT_CENTER
	zahl_zeile.add_theme_constant_override("separation", UiStil.A3)
	zahl_feld.add_child(zahl_zeile)
	zahl_zeile.add_child(UiStil.symbolbild("muenze", 72.0))
	_betrag = UiStil.label(UiText.t("offline_ertrag") % "0", UiStil.GR_HELD, UiStil.TINTE, UiStil.FETT)
	zahl_zeile.add_child(_betrag)

	# Balken der Offlinezeit: "2 Std 14 Min von 4 Std" -- der Deckel ist der Rueckkehrgrund.
	var deckel: float = max_sekunden if max_sekunden > 0.0 else BalanceData.laden().offline_obergrenze
	var gezaehlt_s: float = minf(sekunden, deckel)
	var balken_box := VBoxContainer.new()
	balken_box.add_theme_constant_override("separation", UiStil.A1)
	box.add_child(balken_box)
	balken_box.add_child(UiStil.label(UiText.t("offline_balken") % [WeltTexte.dauer(gezaehlt_s),
		WeltTexte.dauer(deckel)], UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT))
	var leiste: ProgressBar = UiStil.neuer_balken(24.0, UiStil.akzent())
	leiste.add_theme_stylebox_override("background", UiStil.balken_grund())
	leiste.value = clampf(gezaehlt_s / deckel, 0.0, 1.0)
	balken_box.add_child(leiste)

	# Zwei Knoepfe nebeneinander: gruen ▶ ×2 (freiwillig), gold Einsammeln.
	var knoepfe := HBoxContainer.new()
	knoepfe.add_theme_constant_override("separation", UiStil.A3)
	box.add_child(knoepfe)
	if verdoppeln_moeglich:
		_verdoppeln = Sheet.kaufknopf(UiStil.KAUFEN)
		# Der Gegenwert steht im Knopf: Faktor aus ads.json, Betrag = was DAZUkommt.
		_faktor = AdServiceStub.faktor(&"offline_verdoppeln")
		var faktor_text: String = ("%.1f" % _faktor).rstrip("0").rstrip(".").replace(".", ",")
		_verdoppeln.text = UiText.t("werbung_offline_x") % [faktor_text, UiStil.zahl(erloes * (_faktor - 1.0))]
		_verdoppeln.custom_minimum_size = Vector2(0.0, 96.0)
		_verdoppeln.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_verdoppeln.pressed.connect(func() -> void:
			_verdoppeln.disabled = true
			_verdoppeln.text = UiText.t("werbung_laeuft")
			verdoppeln_gedrueckt.emit())
		# Das Angebot ist jetzt sichtbar (Messung); scheitert die Werbung, geht der Knopf wieder auf.
		var dienst: AdService = get_tree().get_first_node_in_group(&"werbung") as AdService if is_inside_tree() else null
		if dienst != null:
			dienst.melde_angebot(&"offline_verdoppeln")
			var beschriftung: String = _verdoppeln.text
			dienst.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void:
				if is_instance_valid(_verdoppeln):
					_verdoppeln.disabled = false
					_verdoppeln.text = beschriftung)
			# Kein Folgefenster: Die Zahl in der Karte springt auf den doppelten Betrag,
			# der Knopf verschwindet, ein Tipp sammelt ein.
			dienst.belohnung_verdient.connect(func(p: StringName) -> void:
				if p == &"offline_verdoppeln" and is_instance_valid(_verdoppeln):
					verdoppelt_zeigen())
		knoepfe.add_child(_verdoppeln)
	_knopf = Sheet.kaufknopf(UiStil.GOLD)
	_knopf.text = UiText.t("offline_einsammeln")
	_knopf.custom_minimum_size = Vector2(0.0, 96.0)
	_knopf.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_knopf.pressed.connect(_einsammeln)
	knoepfe.add_child(_knopf)

	# Ein Tipp irgendwo ausserhalb der Karte sammelt ebenfalls ein.
	schleier.mouse_filter = Control.MOUSE_FILTER_STOP
	schleier.gui_input.connect(func(ereignis: InputEvent) -> void:
		var tipp: bool = ereignis is InputEventMouseButton and (ereignis as InputEventMouseButton).pressed 			or ereignis is InputEventScreenTouch and (ereignis as InputEventScreenTouch).pressed
		if tipp:
			_einsammeln())

	# Auftritt: Karte ploppt, dann zaehlt der Betrag.
	_karte.modulate.a = 0.0
	UiStil.aufploppen.call_deferred(_karte, 0.8)
	var t_ein := create_tween()
	t_ein.tween_property(_karte, "modulate:a", 1.0, 0.15)
	var zaehlen := create_tween()
	zaehlen.tween_interval(ZAEHL_START)
	zaehlen.tween_method(_setze_betrag, 0.0, 1.0, ZAEHL_DAUER).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	zaehlen.tween_callback(func() -> void:
		Haptik.puls(Haptik.DAUER_KAUF)
		UiStil.aufploppen(_betrag, 1.15))


func _setze_betrag(anteil: float) -> void:
	_gezaehlt = _erloes * anteil
	_betrag.text = UiText.t("offline_ertrag") % UiStil.zahl(_gezaehlt)


## Ein Satz der Figur; Platzhalter %d = Zahl Stunden/Minuten wird nicht benutzt --
## die Saetze stehen fertig in der Themendatei. Fehlt `saetze`, gilt `text`
## (dort steht ein %d fuer die gerechnete Menge, die es hier nicht gibt) -- dann
## lieber gar kein Satz.
func _satz(bericht: Dictionary, _sekunden: float) -> String:
	var saetze: Array = bericht.get("saetze", []) as Array
	if saetze.is_empty():
		return ""
	return String(saetze[randi() % saetze.size()])


func _einsammeln() -> void:
	if _fertig:
		return
	_fertig = true
	Haptik.puls(Haptik.DAUER_MENGE)
	var quelle: Control = _betrag if _betrag != null else _knopf
	weiter.emit(quelle.get_global_rect().get_center())


## Nach der Werbung: Betrag auf den vollen Wert, Werbeknopf weg. Kein zweites Fenster.
func verdoppelt_zeigen() -> void:
	_erloes *= _faktor
	_gezaehlt = _erloes
	_betrag.text = UiText.t("offline_ertrag") % UiStil.zahl(_erloes)
	UiStil.aufploppen(_betrag, 1.2)
	Haptik.puls(Haptik.DAUER_KAUF)
	if is_instance_valid(_verdoppeln):
		_verdoppeln.visible = false
