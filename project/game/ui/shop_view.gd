## Der Laden. Heute mit leerem Regal.
##
## Ein leerer Zustand ist kein Sonderfall, den man spaeter nachreicht -- er ist
## der haeufigste Zustand jeder Liste: beim ersten Start, bei Netzproblemen,
## wenn der Store nicht antwortet. Wird er erst gebaut, wenn er auffaellt,
## sieht der Spieler bis dahin eine weisse Flaeche und haelt sie fuer einen
## Absturz.
##
## Deshalb sagt der leere Laden hier ausdruecklich, dass er leer ist, dass das
## in Ordnung ist, und dass man nichts verpasst.
class_name ShopView
extends Control

signal geschlossen

var _liste: VBoxContainer
var _leer_hinweis: PanelContainer
var _dienst: StoreService
var _kopf: PanelContainer
var _titel: Label


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# Der Laden nimmt Eingaben an -- er liegt ueber dem Spiel und soll
	# verhindern, dass man versehentlich dahinter tippt.
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()
	_baue()
	visible = false


func _baue() -> void:
	# Deckend, nicht durchscheinend. Der Laden ist ein eigener Bildschirm, kein
	# Schleier ueber dem Spiel -- ein halbdurchsichtiger Hintergrund, durch den
	# Geldzahlen ticken, sieht nach Fehler aus, nicht nach Absicht.
	var grund := ColorRect.new()
	grund.color = UiStil.PAPIER_2
	grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	grund.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(grund)

	var rand := MarginContainer.new()
	rand.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rand.add_theme_constant_override("margin_left", UiStil.A5)
	rand.add_theme_constant_override("margin_right", UiStil.A5)
	rand.add_theme_constant_override("margin_top", int(Kopfleiste.OBEN) + UiStil.A4)
	rand.add_theme_constant_override("margin_bottom", UiStil.A6 + UiStil.A5)
	add_child(rand)

	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A5)
	rand.add_child(spalte)

	_kopf = PanelContainer.new()
	spalte.add_child(_kopf)
	var kopf_zeile := HBoxContainer.new()
	kopf_zeile.add_theme_constant_override("separation", UiStil.A3)
	_kopf.add_child(kopf_zeile)
	kopf_zeile.add_child(UiStil.symbolbild("tasche", 64.0))
	_titel = UiStil.label(UiText.t("laden"), UiStil.GR_TITEL, UiStil.TINTE, UiStil.FETT)
	_titel.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	kopf_zeile.add_child(_titel)

	# Die Produktliste. Heute leer, morgen nicht -- deshalb steht sie schon da.
	var rollbar := WischScroll.new()
	rollbar.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rollbar.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	spalte.add_child(rollbar)

	_liste = VBoxContainer.new()
	_liste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_liste.size_flags_vertical = Control.SIZE_EXPAND_FILL
	# Mittig: Solange nichts im Regal liegt, steht der Hinweis dort, wo der
	# Blick ohnehin hinfaellt, statt oben zu kleben und darunter ein Loch zu
	# lassen. Mit Produkten fuellt die Liste die Flaeche und es faellt nicht auf.
	_liste.alignment = BoxContainer.ALIGNMENT_CENTER
	_liste.add_theme_constant_override("separation", UiStil.A4)
	rollbar.add_child(_liste)

	_leer_hinweis = Sheet.innenkarte(float(UiStil.A5))
	_liste.add_child(_leer_hinweis)
	var leer_spalte := VBoxContainer.new()
	leer_spalte.add_theme_constant_override("separation", UiStil.A3)
	_leer_hinweis.add_child(leer_spalte)
	var leer_bild := UiStil.symbolbild("geschenk", 96.0)
	leer_bild.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	leer_spalte.add_child(leer_bild)
	var leer_titel := UiStil.label(UiText.t("laden_leer_titel"), UiStil.GR_GROSS, UiStil.TINTE, UiStil.FETT)
	leer_titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	leer_spalte.add_child(leer_titel)
	# Der Ton ist Absicht: kein "kommt bald", das nach Ausrede klingt, und
	# kein leeres Versprechen. Die Aussage ist, dass niemand etwas verpasst.
	var leer_text := UiStil.label(UiText.t("laden_leer_text"), UiStil.GR_MITTEL - 2, UiStil.TINTE_2,
		UiStil.TEXT_GEWICHT)
	leer_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	leer_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	leer_spalte.add_child(leer_text)

	var wiederherstellen := UiStil.nebenknopf(UiText.t("laden_wiederherstellen"), UiStil.TIPPZIEL + 16.0)
	wiederherstellen.pressed.connect(_auf_wiederherstellen)
	spalte.add_child(wiederherstellen)

	var schliessen := UiStil.kaufknopf(UiStil.PAPIER, 120.0)
	schliessen.text = UiText.t("zurueck")
	schliessen.pressed.connect(func() -> void:
		visible = false
		geschlossen.emit())
	spalte.add_child(schliessen)


func verbinde(dienst: StoreService) -> void:
	_dienst = dienst
	_dienst.kauf_beendet.connect(_auf_kauf_beendet)
	_dienst.wiederherstellung_beendet.connect(_auf_wiederherstellung)


func oeffnen() -> void:
	visible = true
	# Der Kopf traegt den Akzent der Welt, in der man gerade ist.
	var stil := UiStil.karte(UiStil.akzent(), UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3))
	_kopf.add_theme_stylebox_override("panel", stil)
	_titel.add_theme_color_override("font_color", UiStil.akzent_text())
	aktualisieren()


func aktualisieren() -> void:
	if _dienst == null or _liste == null:
		return
	# Alles ausser dem Leer-Hinweis neu aufbauen.
	for kind in _liste.get_children():
		if kind != _leer_hinweis:
			kind.queue_free()

	var produkte: Array = _dienst.katalog()
	_leer_hinweis.visible = produkte.is_empty()
	for eintrag in produkte:
		_liste.add_child(_baue_zeile(eintrag as Dictionary))


func _baue_zeile(produkt: Dictionary) -> Control:
	var feld := Sheet.innenkarte(float(UiStil.A3))
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A4)
	feld.add_child(zeile)

	var name := UiStil.label(String(produkt.get("name_schluessel", produkt.get("id", ""))), UiStil.GR_MITTEL,
		UiStil.TINTE, UiStil.FETT)
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	zeile.add_child(name)

	var besessen: bool = bool(produkt.get("besessen", false))
	var knopf := UiStil.kaufknopf(UiStil.KAUFEN, UiStil.TIPPZIEL + 16.0)
	knopf.text = UiText.t("gekauft") if besessen else String(produkt.get("preis_text", ""))
	knopf.disabled = besessen
	knopf.custom_minimum_size.x = 220.0
	var id := StringName(String(produkt.get("id", "")))
	knopf.pressed.connect(func() -> void:
		knopf.disabled = true
		_dienst.kaufen(id))
	zeile.add_child(knopf)
	return feld


func _auf_wiederherstellen() -> void:
	if _dienst != null:
		_dienst.wiederherstellen()


func _auf_kauf_beendet(_produkt_id: StringName, _ergebnis: int) -> void:
	aktualisieren()


func _auf_wiederherstellung(_anzahl: int) -> void:
	aktualisieren()
