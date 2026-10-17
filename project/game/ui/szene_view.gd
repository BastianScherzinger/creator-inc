## Eine Story-Szene: Die Figur steht gross im Bild, spricht in 1 bis 3 Blasen,
## und der Spieler antwortet mit einem Wort (DESIGN_OVERHAUL 4.7).
##
## Zwei Darstellungen (A/B-Vergleich, Schalter `--variante a|b`):
##   a -- Popup unten, Porträt 220 px ragt aus der Karte, die Welt bleibt sichtbar
##   b -- Vollbild in der Farbe der Figur, Porträt gross in der Mitte (Idle-Bank-Art)
##
## Die Antworten wirken nur auf Stimmung und Text, nie auf Geld. Die Ansicht
## rechnet nichts: Sie bekommt ein Dictionary und meldet, was gewählt wurde.
##
## Szenen-Dictionary (alles außer Text optional):
##   von, ausdruck ("neutral"|"jubelnd"|"geschockt"),
##   blasen: [String | {von, ausdruck, text}]  oder  text (Zeilenumbruch = neue Blase),
##   antworten: [String | {text, reaktion, auftrag}]    oder  antwort (eine einzelne)
##
## K3 B3: Eine Antwort mit `auftrag` (Ziel-ID) startet eine Aufgabe: Nach dem
## Schliessen springt die Oberflaeche zu diesem Ziel (der naechste Vorfahre mit
## `springe_zu_ziel`, also das HUD) -- offen: hinfuehren, erfuellt: einloesen.
class_name SzeneView
extends Control

## Gewählt (oder weitergetippt): `index` = -1, wenn es keine Antwort gab.
signal beendet(index: int, antwort_text: String)
## Eine Antwort mit `auftrag` wurde gewählt (Ziel-ID); kommt direkt nach `beendet`.
signal auftrag_gewaehlt(ziel_id: String)

const PORTRAIT_KANTE: float = 220.0
const PORTRAIT_KANTE_B: float = 440.0
const ANTWORT_H: float = 96.0
const BLASE_MIN_H: float = 120.0

## Wird vom Prüfschalter `--variante` gesetzt; sonst "a".
static var standard_variante: String = "a"

var variante: String = "a"

var _thema: ThemeData
var _audio: AudioDirector
var _blasen: Array = []
var _antworten: Array = []
var _index: int = -1
var _tippt: bool = false
var _wartet_auf_antwort: bool = false
var _gewaehlt: int = -1
var _gewaehlt_text: String = ""
var _auftrag: String = ""
var _schliesst: bool = false

var _huelle: Control
var _portrait_flaeche: Control
var _portrait: Control
var _name_chip: PanelContainer
var _name_label: Label
var _text: Label
var _hinweis: Label
var _antwort_zeile: HBoxContainer
var _grund: ColorRect
var _tipp_tween: Tween


# --- Daten -----------------------------------------------------------------------

## Macht aus einer Nachricht der Themendatei (`von`, `text`, optional `blasen`,
## `antwort`/`antworten`, `ausdruck`) eine Szene.
static func szene_aus_nachricht(n: Dictionary) -> Dictionary:
	return n.duplicate(true)


## Die Eröffnung (`eroeffnung.chat`: Blasen der Figur und "du") als Szene:
## die Figur-Zeilen werden ALLE Blasen (keine Kappung), die ersten "du"-Zeilen die
## Antworten. Gibt es keine "du"-Zeile, ersetzt der Knopf `eroeffnung.knopf` den
## Antwortchip (K2 Regel 20: Antwortchips erst ab Welt 2).
static func szene_aus_eroeffnung(texte: Dictionary) -> Dictionary:
	var blasen: Array = []
	var antworten: Array = []
	var von: String = ""
	for e in (texte.get("chat", []) as Array):
		var d: Dictionary = e as Dictionary
		var absender: String = String(d.get("von", ""))
		if absender == "du":
			antworten.append(String(d.get("text", "")))
		else:
			if von.is_empty():
				von = absender
			blasen.append({"von": absender, "text": String(d.get("text", ""))})
	if antworten.is_empty() and not String(texte.get("knopf", "")).is_empty():
		antworten.append(String(texte.get("knopf", "")))
	return {"von": von, "blasen": blasen, "antworten": antworten.slice(0, 2)}


## Vereinheitlicht eine Szene: Blasen als {von, ausdruck, text}, Antworten als {text, reaktion}.
static func normalisiere(szene: Dictionary) -> Dictionary:
	var von: String = String(szene.get("von", ""))
	# `stimmung` ist der Name in den Themendateien (ov_schema.md 8); gleiche Bedeutung.
	var ausdruck: String = String(szene.get("ausdruck", szene.get("stimmung", szene.get("pose", "neutral"))))
	var blasen: Array = []
	var roh: Variant = szene.get("blasen", null)
	if roh is Array:
		for b in (roh as Array):
			if b is Dictionary:
				var d: Dictionary = b as Dictionary
				blasen.append({"von": String(d.get("von", von)),
					"ausdruck": String(d.get("ausdruck", d.get("stimmung", d.get("pose", ausdruck)))),
					"text": String(d.get("text", ""))})
			else:
				blasen.append({"von": von, "ausdruck": ausdruck, "text": String(b)})
	else:
		for teil in String(szene.get("text", "")).split("\n", false):
			blasen.append({"von": von, "ausdruck": ausdruck, "text": teil.strip_edges()})
	var antworten: Array = []
	var a: Variant = szene.get("antworten", null)
	if a is Array:
		for x in (a as Array):
			if x is Dictionary:
				antworten.append({"text": String((x as Dictionary).get("text", "")),
					"reaktion": String((x as Dictionary).get("reaktion", "")),
					"auftrag": String((x as Dictionary).get("auftrag", ""))})
			else:
				antworten.append({"text": String(x), "reaktion": "", "auftrag": ""})
	elif not String(szene.get("antwort", "")).is_empty():
		antworten.append({"text": String(szene.get("antwort", "")), "reaktion": "", "auftrag": ""})
	return {"von": von, "blasen": blasen, "antworten": antworten}


## Baut eine Szenenansicht auf `eltern` (eine CanvasLayer oder ein Control) und zeigt sie.
static func zeige_szene(eltern: Node, szene: Dictionary, thema: ThemeData,
		audio: AudioDirector = null, variante_wahl: String = "") -> SzeneView:
	var ansicht := SzeneView.new()
	ansicht.variante = variante_wahl if not variante_wahl.is_empty() else standard_variante
	eltern.add_child(ansicht)
	ansicht.zeige(szene, thema, audio)
	return ansicht


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()


# --- Aufbau ----------------------------------------------------------------------

func zeige(szene: Dictionary, thema: ThemeData, audio: AudioDirector = null) -> void:
	_thema = thema
	_audio = audio
	var n: Dictionary = normalisiere(szene)
	_blasen = (n["blasen"] as Array).filter(func(b: Variant) -> bool:
		return not String((b as Dictionary)["text"]).is_empty())
	_antworten = n["antworten"] as Array
	if _blasen.is_empty():
		push_warning("Szene ohne Text")
		beendet.emit(-1, "")
		queue_free()
		return
	if variante == "b":
		_baue_b()
	else:
		_baue_a()
	_naechste_blase()
	_einblenden()


func _farbe(von: String) -> Color:
	return UiStil.absender_farbe(_thema, von) if _thema != null else UiStil.akzent()


func _name(von: String) -> String:
	if _thema == null:
		return von
	var s: String = WeltTexte.absender(_thema, von)
	return von.capitalize() if s.is_empty() else s


## Porträt der Figur; ohne Bild der runde Avatar mit Initiale.
func _portrait_control(von: String, ausdruck: String, kante: float) -> Control:
	var bild: Texture2D = UiStil.portrait(von, ausdruck)
	if bild == null:
		# Figuren, die das Thema (noch) nicht als Absender führt: Datei direkt suchen.
		var pfad: String = UiStil.PORTRAIT_PFAD % [von, ausdruck]
		if ResourceLoader.exists(pfad):
			bild = load(pfad) as Texture2D
	if bild != null:
		var tr := TextureRect.new()
		tr.texture = bild
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(kante, kante)
		tr.size = Vector2(kante, kante)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		return tr
	var av: PanelContainer = UiStil.avatar(_name(von), _farbe(von), kante * 0.8)
	av.size = Vector2(kante * 0.8, kante * 0.8)
	return av


## Vollbild-Variante: Das Porträt ist unten abgeschnitten -- ein runder Rahmen macht
## daraus ein Bild statt eines schwebenden Kopfes.
func _im_kreis(inhalt: Control, farbe: Color, kante: float) -> Control:
	var kreis := PanelContainer.new()
	kreis.add_theme_stylebox_override("panel", UiStil.sticker(farbe.lightened(0.3), UiStil.RADIUS_CHIP,
		UiStil.KONTUR + 1, 0.0, UiStil.SCHATTEN_Y_PRIMAER))
	kreis.custom_minimum_size = Vector2(kante, kante)
	kreis.size = Vector2(kante, kante)
	kreis.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	kreis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inhalt.custom_minimum_size = Vector2(kante, kante)
	kreis.add_child(inhalt)
	return kreis


func _baue_a() -> void:
	_huelle = Control.new()
	_huelle.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_huelle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_huelle)

	_grund = ColorRect.new()
	_grund.color = Color(UiStil.SCHLEIER.r, UiStil.SCHLEIER.g, UiStil.SCHLEIER.b, 0.38)
	_grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_grund.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_grund)
	move_child(_grund, 0)

	var karte := PanelContainer.new()
	karte.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	karte.grow_vertical = Control.GROW_DIRECTION_BEGIN
	karte.offset_left = float(UiStil.A4)
	karte.offset_right = -float(UiStil.A4)
	karte.offset_top = -float(UiStil.A5)
	karte.offset_bottom = -float(UiStil.A5)
	karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var stil: StickerBox = UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 6, UiStil.KONTUR + 1,
		float(UiStil.A4), UiStil.SCHATTEN_Y * 2.0)
	karte.add_theme_stylebox_override("panel", stil)
	_huelle.add_child(karte)

	var aussen := VBoxContainer.new()
	aussen.add_theme_constant_override("separation", UiStil.A3)
	aussen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	karte.add_child(aussen)

	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	aussen.add_child(zeile)

	# Die Porträtspalte hat nur 170 px Höhe -- das Bild (220) ragt 70 px über die Karte.
	_portrait_flaeche = Control.new()
	_portrait_flaeche.custom_minimum_size = Vector2(PORTRAIT_KANTE, 170.0)
	_portrait_flaeche.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(_portrait_flaeche)

	var rechts := VBoxContainer.new()
	rechts.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rechts.add_theme_constant_override("separation", UiStil.A2)
	rechts.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(rechts)
	_baue_namenschild(rechts)
	_baue_text(rechts, UiStil.GR_TITEL, BLASE_MIN_H)
	_baue_hinweis(rechts)

	_antwort_zeile = HBoxContainer.new()
	_antwort_zeile.add_theme_constant_override("separation", UiStil.A3)
	_antwort_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	aussen.add_child(_antwort_zeile)


func _baue_b() -> void:
	_huelle = Control.new()
	_huelle.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_huelle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_huelle)

	_grund = ColorRect.new()
	_grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_grund.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_huelle.add_child(_grund)

	var rand := MarginContainer.new()
	rand.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rand.add_theme_constant_override("margin_left", UiStil.A5)
	rand.add_theme_constant_override("margin_right", UiStil.A5)
	rand.add_theme_constant_override("margin_top", 96)
	rand.add_theme_constant_override("margin_bottom", UiStil.A6)
	rand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_huelle.add_child(rand)

	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A3)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rand.add_child(spalte)

	_portrait_flaeche = CenterContainer.new()
	_portrait_flaeche.custom_minimum_size = Vector2(0.0, PORTRAIT_KANTE_B)
	_portrait_flaeche.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_portrait_flaeche.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(_portrait_flaeche)

	_baue_namenschild(spalte)
	_name_chip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER

	var blase := PanelContainer.new()
	blase.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 6,
		UiStil.KONTUR + 1, float(UiStil.A5), UiStil.SCHATTEN_Y * 2.0))
	blase.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(blase)
	var inhalt := VBoxContainer.new()
	inhalt.add_theme_constant_override("separation", UiStil.A2)
	inhalt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	blase.add_child(inhalt)
	_baue_text(inhalt, UiStil.GR_TITEL, BLASE_MIN_H)
	_baue_hinweis(inhalt)

	_antwort_zeile = HBoxContainer.new()
	_antwort_zeile.add_theme_constant_override("separation", UiStil.A3)
	_antwort_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_antwort_zeile.custom_minimum_size = Vector2(0.0, ANTWORT_H)
	spalte.add_child(_antwort_zeile)


func _baue_namenschild(eltern: Control) -> void:
	_name_chip = PanelContainer.new()
	_name_chip.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_name_chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name_label = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_name_chip.add_child(_name_label)
	eltern.add_child(_name_chip)


func _baue_text(eltern: Control, groesse: int, min_hoehe: float) -> void:
	_text = UiStil.label("", groesse, UiStil.TINTE, UiStil.FETT)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_text.custom_minimum_size = Vector2(0.0, min_hoehe)
	eltern.add_child(_text)


func _baue_hinweis(eltern: Control) -> void:
	_hinweis = UiStil.label(U3Text.t("szene_weiter"), UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.FETT)
	_hinweis.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	eltern.add_child(_hinweis)


func _einblenden() -> void:
	if variante == "b":
		_huelle.modulate.a = 0.0
		create_tween().tween_property(_huelle, "modulate:a", 1.0, 0.2)
		return
	_huelle.position.y = 520.0
	_grund.modulate.a = 0.0
	var t := create_tween().set_parallel(true)
	t.tween_property(_huelle, "position:y", 0.0, UiStil.DAUER_SZENE_EIN) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(_grund, "modulate:a", 1.0, UiStil.DAUER_SZENE_EIN)


# --- Ablauf ----------------------------------------------------------------------

func _naechste_blase() -> void:
	_index += 1
	_zeige_blase(_blasen[_index] as Dictionary)


## Prüfhilfe: gleich zur n-ten Blase springen (-1 = letzte), z. B. um die Antworten zu sehen.
func springe_zu(n: int) -> void:
	var ziel: int = _blasen.size() - 1 if n < 0 else mini(n, _blasen.size() - 1)
	while _index < ziel:
		_naechste_blase()


func _zeige_blase(b: Dictionary) -> void:
	var von: String = String(b["von"])
	var ausdruck: String = String(b["ausdruck"])
	var farbe: Color = _farbe(von)
	_name_chip.add_theme_stylebox_override("panel", UiStil.chip(farbe, float(UiStil.A4), float(UiStil.A1 + 2), 2.0))
	_name_label.text = _name(von)
	_name_label.add_theme_color_override("font_color", UiStil.text_auf(farbe))
	if variante == "b":
		_grund.color = farbe.darkened(0.35)

	if _portrait != null:
		_portrait.queue_free()
	var kante: float = PORTRAIT_KANTE_B if variante == "b" else PORTRAIT_KANTE
	_portrait = _portrait_control(von, ausdruck, kante)
	if variante == "b":
		_portrait = _im_kreis(_portrait, farbe, kante)
	_portrait_flaeche.add_child(_portrait)
	if variante != "b":
		_portrait.position = Vector2(0.0, -70.0)
	_portrait.pivot_offset = _portrait.size * 0.5
	_portrait.scale = Vector2(0.82, 0.82)
	var pt := _portrait.create_tween()
	pt.tween_property(_portrait, "scale", Vector2.ONE, UiStil.DAUER_KAUF) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if ausdruck == "jubelnd":
		var hup := _portrait.create_tween().set_loops(2)
		hup.tween_property(_portrait, "rotation_degrees", -4.0, 0.12)
		hup.tween_property(_portrait, "rotation_degrees", 4.0, 0.12)
		hup.chain().tween_property(_portrait, "rotation_degrees", 0.0, 0.1)
	elif ausdruck == "geschockt":
		var zit := _portrait.create_tween().set_loops(3)
		zit.tween_property(_portrait, "position:x", _portrait.position.x - 6.0, 0.04)
		zit.tween_property(_portrait, "position:x", _portrait.position.x + 6.0, 0.04)
		zit.chain().tween_property(_portrait, "position:x", _portrait.position.x, 0.04)

	_text.text = String(b["text"])
	# Lange Sätze eine Stufe kleiner, damit die Karte nicht über 40 % wächst.
	_text.add_theme_font_size_override("font_size",
		UiStil.GR_TITEL if _text.text.length() <= 70 else UiStil.GR_GROSS)
	_text.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TITEL))
	_hinweis.visible = false
	_leere_antworten()
	_tippe_text()
	if _audio != null:
		_audio.spiele(&"blase")
	Haptik.puls(10)


func _tippe_text() -> void:
	_tippt = true
	_text.visible_characters = 0
	var n: int = _text.text.length()
	var dauer: float = minf(float(n) * U3Text.schwelle("tipp_sekunden_je_zeichen", 0.022),
		U3Text.schwelle("tipp_max_sekunden", 1.0))
	if _tipp_tween != null and _tipp_tween.is_valid():
		_tipp_tween.kill()
	_tipp_tween = create_tween()
	_tipp_tween.tween_property(_text, "visible_characters", n, maxf(dauer, 0.05))
	_tipp_tween.tween_callback(_text_fertig)


func _text_fertig() -> void:
	_tippt = false
	_text.visible_characters = -1
	var letzte: bool = _index >= _blasen.size() - 1
	if letzte and not _antworten.is_empty() and _gewaehlt < 0:
		_zeige_antworten()
		return
	_hinweis.text = U3Text.t("szene_ende") if letzte else U3Text.t("szene_weiter")
	_hinweis.visible = true


func _leere_antworten() -> void:
	for k in _antwort_zeile.get_children():
		k.queue_free()
	_wartet_auf_antwort = false


func _zeige_antworten() -> void:
	_wartet_auf_antwort = true
	_hinweis.visible = false
	for i in range(mini(_antworten.size(), 2)):
		var a: Dictionary = _antworten[i] as Dictionary
		var k: Button = UiStil.nebenknopf(String(a["text"]), ANTWORT_H)
		k.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		k.add_theme_font_size_override("font_size", UiStil.GR_MITTEL)
		# Akzentfläche: Die Antwort ist die Handlung dieser Szene.
		UiStil.faerbe_knopf(k, UiStil.akzent())
		for zustand in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
			k.add_theme_color_override(zustand, UiStil.text_auf(UiStil.akzent()))
		k.pressed.connect(_waehle.bind(i))
		_antwort_zeile.add_child(k)
		k.modulate.a = 0.0
		var t := k.create_tween()
		t.tween_interval(0.08 * i)
		t.tween_property(k, "modulate:a", 1.0, 0.12)
		t.parallel().tween_callback(func() -> void: UiStil.aufploppen(k, 0.9))


func _waehle(i: int) -> void:
	if _gewaehlt >= 0 or _schliesst:
		return
	_gewaehlt = i
	var a: Dictionary = _antworten[i] as Dictionary
	_gewaehlt_text = String(a["text"])
	_auftrag = String(a.get("auftrag", ""))
	Haptik.puls(Haptik.DAUER_KAUF)
	_leere_antworten()
	var reaktion: String = String(a.get("reaktion", ""))
	if reaktion.is_empty():
		_schliesse()
		return
	# Die Figur antwortet noch einmal -- danach genügt ein Tipp.
	var von: String = String((_blasen[_index] as Dictionary)["von"])
	_blasen.append({"von": von, "ausdruck": "neutral", "text": reaktion})
	_naechste_blase()


func _gui_input(ereignis: InputEvent) -> void:
	if not UiStil.ist_tipp(ereignis) or _schliesst:
		return
	if _tippt:
		if _tipp_tween != null and _tipp_tween.is_valid():
			_tipp_tween.kill()
		_text_fertig()
		return
	if _wartet_auf_antwort:
		return
	if _index < _blasen.size() - 1:
		_naechste_blase()
		return
	_schliesse()


## Die Ziel-ID, die die gewählte Antwort startet (leer = keine). Für Tests.
func gewaehlter_auftrag() -> String:
	return _auftrag


## Der nächste Vorfahre, der zu einem Ziel springen kann (das HUD); null ohne.
func _ziel_springer() -> Node:
	var k: Node = get_parent()
	while k != null:
		if k.has_method("springe_zu_ziel"):
			return k
		k = k.get_parent()
	return null


func _schliesse() -> void:
	if _schliesst:
		return
	_schliesst = true
	var t := create_tween().set_parallel(true)
	if variante == "b":
		t.tween_property(_huelle, "modulate:a", 0.0, 0.18)
	else:
		t.tween_property(_huelle, "position:y", 520.0, 0.18).set_ease(Tween.EASE_IN)
		t.tween_property(_grund, "modulate:a", 0.0, 0.18)
	t.chain().tween_callback(func() -> void:
		var springer: Node = _ziel_springer() if not _auftrag.is_empty() else null
		beendet.emit(_gewaehlt, _gewaehlt_text)
		if not _auftrag.is_empty():
			auftrag_gewaehlt.emit(_auftrag)
			if springer != null:
				# Erst nach dem Schliessen: sonst schliesst das HUD die Szene gleich mit.
				springer.call_deferred("springe_zu_ziel", _auftrag)
		var eltern: Node = get_parent()
		# Eine CanvasLayer, die nur für diese Szene da war, geht mit.
		if eltern is CanvasLayer and eltern.get_child_count() == 1:
			eltern.queue_free()
		else:
			queue_free())
