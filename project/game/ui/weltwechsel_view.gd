## Der ganze Bildschirm fuer die grossen Momente: die Eroeffnung, das Angebot,
## in die naechste Welt zu gehen, und der Abspann.
##
## Der Weltwechsel ist der staerkste Moment, den ein Idle-Game haben kann: Nicht
## eine groessere Zahl, sondern ein anderer Ort und ein anderes Leben. Er bekommt
## deshalb als einziges Ereignis im Spiel den ganzen Bildschirm -- als Plakat
## im Stil "Sticker-Pop": Grund in der Akzentfarbe, der Titel als schraeg
## geklebter Aufkleber, die Figur der neuen Welt als Chip daneben.
##
## Er wird ANGEBOTEN, nicht ausgeloest. Wer gerade dabei ist, die letzte Station
## auszubauen, soll nicht mitten im Zug woanders hin geschoben werden. Und wer
## das Angebot wegdrueckt, bekommt es beim naechsten Start wieder -- ein
## einmaliges Weglegen des Handys darf den wichtigsten Moment nicht kosten.
##
## Welche der drei Arten gerade laeuft, erkennt die Ansicht am Titel: Er steht
## in der Themendatei entweder unter "eroeffnung", "weltwechsel" oder "abspann".
## Der Aufrufer (main.gd) uebergibt nur Texte.
class_name WeltwechselView
extends Control

enum Art { EROEFFNUNG, WELTWECHSEL, ABSPANN }

## Der Aufbau ist langsam. Das ist der Punkt: Alles andere im Spiel ist schnell
## und beilaeufig, und dieser Moment soll sich anders anfuehlen als alles davor.
const EINBLENDEN: float = 0.5
const VERZOEGERUNG_TEXT: float = 0.7
const VERZOEGERUNG_KNOPF: float = 1.8
## Die Eroeffnung ist der ERSTE Bildschirm -- dort wartet niemand gern.
const VERZOEGERUNG_KNOPF_START: float = 0.9
const NEIGUNG_TITEL: float = -3.0
const NEIGUNG_FIGUR: float = 4.0
## Eine Chat-Blase der Eroeffnung bleibt so lange allein, bevor die naechste kommt.
const CHAT_PAUSE: float = 1.25
const CHAT_START: float = 1.0
## Abspann: Sekunden je Textzeile, je Credit-Zeile, Hoehe einer Credit-Zeile.
const ABSPANN_ZEILE: float = 1.2
const ABSPANN_CREDIT: float = 1.0
const ABSPANN_CREDIT_HOEHE: float = 36.0

## Aufkleber am Rand: Symbol, Anker (0..1), Kante, Neigung.
const DEKOR: Array = [
	["stern", Vector2(0.08, 0.10), 96.0, -14.0],
	["muenze", Vector2(0.86, 0.12), 110.0, 12.0],
]

## "Neu in dieser Welt": Anzahl Karten, Kartenbreite, Bildhoehe, Neigung je Karte.
const NEU_ANZAHL: int = 3
const NEU_KARTE_BREITE: float = 188.0
const NEU_BILD_HOEHE: float = 130.0
const NEU_NEIGUNG: Array = [-2.0, 1.5, -1.0]

signal angenommen

var art: Art = Art.WELTWECHSEL
var _grund: ColorRect
var _dekor: Control
var _kicker: PanelContainer
var _kicker_text: Label
var _titel_feld: PanelContainer
var _titel: Label
var _figur: PanelContainer
var _portrait_buehne: Control   ## grosses Portrait der genannten Figur (nur Weltwechsel)
var _figur_text: Label
var _text_feld: PanelContainer
var _text: Label
var _knopf: Button
var _hinweis_feld: PanelContainer
var _hinweis_text: Label
var _boni_text: Label
## "Neu in dieser Welt": die ersten Stationen der kommenden Welt (nur Weltwechsel).
var _neu_box: VBoxContainer
var _neu_titel: Label
var _neu_reihe: HBoxContainer
## Abspann: Text erscheint Zeile fuer Zeile, danach rollen die Credit-Zeilen herein.
var _roll_feld: Control
var _roll_box: VBoxContainer
var _abspann_ablauf: Tween
## Eroeffnung als Chat: Blasen erscheinen nacheinander, ein Tipp zeigt die naechste.
var _chat_box: VBoxContainer
var _chat_blasen: Array[Control] = []
var _chat_index: int = 0
var _chat_rest: float = 0.0


## Aufbau in _init, nicht in _ready: Der Aufrufer darf zeige() direkt nach
## new() aufrufen, auch bevor die Ansicht im Baum haengt.
func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	# Nimmt Eingaben an: Solange das Angebot steht, soll nichts dahinter
	# versehentlich getroffen werden.
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()
	_baue()


func _baue() -> void:
	_grund = ColorRect.new()
	_grund.color = UiStil.akzent()
	_grund.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_grund.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_grund)

	_dekor = Control.new()
	_dekor.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dekor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_dekor)
	for eintrag in DEKOR:
		var bild := UiStil.symbolbild(String(eintrag[0]), float(eintrag[2]))
		var anker: Vector2 = eintrag[1]
		bild.anchor_left = anker.x
		bild.anchor_right = anker.x
		bild.anchor_top = anker.y
		bild.anchor_bottom = anker.y
		var halb: float = float(eintrag[2]) * 0.5
		bild.offset_left = -halb
		bild.offset_right = halb
		bild.offset_top = -halb
		bild.offset_bottom = halb
		bild.pivot_offset = Vector2(halb, halb)
		bild.rotation_degrees = float(eintrag[3])
		_dekor.add_child(bild)

	var rand := MarginContainer.new()
	rand.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rand.add_theme_constant_override("margin_left", UiStil.A6 + UiStil.A2)
	rand.add_theme_constant_override("margin_right", UiStil.A6 + UiStil.A2)
	rand.add_theme_constant_override("margin_top", 150)
	rand.add_theme_constant_override("margin_bottom", 72)
	rand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rand)

	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A5)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rand.add_child(spalte)

	var oben := Control.new()
	oben.size_flags_vertical = Control.SIZE_EXPAND_FILL
	oben.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(oben)
	_portrait_buehne = CenterContainer.new()
	_portrait_buehne.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_portrait_buehne.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait_buehne.visible = false
	oben.add_child(_portrait_buehne)

	# Kleiner Chip ueber dem Titel ("Naechste Welt").
	_kicker = PanelContainer.new()
	_kicker.add_theme_stylebox_override("panel", UiStil.chip(UiStil.TINTE, float(UiStil.A4), float(UiStil.A1 + 2), 0.0))
	_kicker.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_kicker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kicker_text = UiStil.label("", UiStil.GR_KLEIN + 2, UiStil.PAPIER, UiStil.FETT)
	_kicker.add_child(_kicker_text)
	spalte.add_child(_kicker)

	_titel_feld = PanelContainer.new()
	var tstil := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 4, UiStil.KONTUR + 1, float(UiStil.A5),
		UiStil.SCHATTEN_Y * 2.0)
	_titel_feld.add_theme_stylebox_override("panel", tstil)
	_titel_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiStil.drehe(_titel_feld, NEIGUNG_TITEL)
	spalte.add_child(_titel_feld)
	_titel = UiStil.label("", UiStil.GR_RIESIG, UiStil.TINTE, UiStil.FETT)
	_titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_titel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_titel.add_theme_constant_override("line_spacing", -12)
	_titel_feld.add_child(_titel)

	# Die Figur der neuen Welt als Aufkleber, schraeg rechts unter dem Titel.
	_figur = PanelContainer.new()
	_figur.add_theme_stylebox_override("panel", UiStil.chip(UiStil.TINTE, float(UiStil.A5), float(UiStil.A2), 3.0))
	_figur.size_flags_horizontal = Control.SIZE_SHRINK_END
	_figur.mouse_filter = Control.MOUSE_FILTER_IGNORE
	UiStil.drehe(_figur, NEIGUNG_FIGUR)
	_figur_text = UiStil.label("", UiStil.GR_GROSS, UiStil.PAPIER, UiStil.FETT)
	_figur.add_child(_figur_text)
	spalte.add_child(_figur)

	_text_feld = PanelContainer.new()
	_text_feld.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A5)))
	_text_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(_text_feld)
	_text = UiStil.label("", UiStil.GR_MITTEL, UiStil.TINTE, UiStil.TEXT_GEWICHT)
	_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.add_theme_constant_override("line_spacing", 6)
	_text_feld.add_child(_text)

	# Die Eroeffnung als Chat -- statt des Textplakats (nur, wenn die Themendatei
	# `eroeffnung.chat` hat).
	_chat_box = VBoxContainer.new()
	_chat_box.add_theme_constant_override("separation", UiStil.A3)
	_chat_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chat_box.visible = false
	spalte.add_child(_chat_box)

	# Credit-Zeilen des Abspanns: rollen langsam nach oben in ein beschnittenes Feld.
	_roll_feld = Control.new()
	_roll_feld.clip_contents = true
	_roll_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_roll_feld.visible = false
	spalte.add_child(_roll_feld)
	_roll_box = VBoxContainer.new()
	_roll_box.add_theme_constant_override("separation", UiStil.A1)
	_roll_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_roll_feld.add_child(_roll_box)

	# Der Pflichthinweis des Abspanns: klein, Nebentext, eigener ruhiger Rahmen.
	_hinweis_feld = PanelContainer.new()
	_hinweis_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER_2, UiStil.RADIUS_KNOPF,
		UiStil.KONTUR_CHIP, float(UiStil.A3), 0.0))
	_hinweis_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hinweis_feld.visible = false
	spalte.add_child(_hinweis_feld)
	_hinweis_text = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
	_hinweis_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_hinweis_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hinweis_feld.add_child(_hinweis_text)

	var unten := Control.new()
	unten.size_flags_vertical = Control.SIZE_EXPAND_FILL
	unten.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(unten)
	var neu_mitte := CenterContainer.new()
	neu_mitte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	neu_mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	unten.add_child(neu_mitte)
	_neu_box = VBoxContainer.new()
	_neu_box.add_theme_constant_override("separation", UiStil.A3)
	_neu_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_neu_box.visible = false
	neu_mitte.add_child(_neu_box)
	_neu_titel = UiStil.label("", UiStil.GR_KLEIN + 2, UiStil.TINTE, UiStil.FETT)
	_neu_titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_neu_box.add_child(_neu_titel)
	_neu_reihe = HBoxContainer.new()
	_neu_reihe.add_theme_constant_override("separation", UiStil.A3)
	_neu_reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_neu_box.add_child(_neu_reihe)

	_knopf = UiStil.kaufknopf(UiStil.KAUFEN, 128.0)
	_knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TITEL))
	_knopf.add_theme_font_size_override("font_size", UiStil.GR_TITEL)
	_knopf.pressed.connect(func() -> void: angenommen.emit())
	spalte.add_child(_knopf)
	# "Von vorn" klingt nach Loeschen -- darunter steht, was bleibt.
	_boni_text = UiStil.label("", UiStil.GR_KLEIN + 2, UiStil.TINTE, UiStil.FETT)
	_boni_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boni_text.visible = false
	spalte.add_child(_boni_text)


## Welche Figur nennt der Text ("mit Roman")? Schluessel der Portraits oder "".
## Nimmt die ERSTE genannte Figur; die Namen stehen in UiStil.PORTRAIT_FIGUREN.
static func figur_im_text(text: String) -> String:
	var klein: String = text.to_lower()
	var bester: String = ""
	var beste_pos: int = -1
	for schluessel in UiStil.PORTRAIT_FIGUREN.values():
		var pos: int = klein.find(String(schluessel))
		if pos >= 0 and (beste_pos < 0 or pos < beste_pos):
			beste_pos = pos
			bester = String(schluessel)
	return bester


## Grosses Portrait der genannten Figur im freien Raum ueber dem Titel.
func _setze_portrait(figur_text: String) -> void:
	for k in _portrait_buehne.get_children():
		k.queue_free()
	var name: String = figur_im_text(figur_text) if art == Art.WELTWECHSEL else ""
	var ok: bool = not name.is_empty() and UiStil.portrait(name, "jubelnd") != null
	_portrait_buehne.visible = ok
	if not ok:
		return
	var kante: float = 300.0
	var bild: Control = UiStil.avatar(name, UiStil.PAPIER, kante, "jubelnd")
	bild.custom_minimum_size = Vector2(kante, kante)
	UiStil.drehe(bild, -4.0)
	_portrait_buehne.add_child(bild)


## Die ersten Stationen der kommenden Welt als Karten mit Bild und Namen.
## Alles aus der Themendatei der neuen Welt; fehlt ein Bild, entfaellt die Karte.
func _baue_neu(welt_art: Art, naechstes: ThemeData) -> void:
	for kind in _neu_reihe.get_children():
		kind.queue_free()
	_neu_box.visible = false
	if welt_art != Art.WELTWECHSEL or naechstes == null:
		return
	var anzahl: int = 0
	for station_id in naechstes.station_ids():
		if anzahl >= NEU_ANZAHL:
			break
		var pfad: String = "res://assets/ui/%s/%s.png" % [naechstes.id, String(station_id)]
		if not ResourceLoader.exists(pfad):
			continue
		var karte := PanelContainer.new()
		karte.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
			UiStil.KONTUR, float(UiStil.A3)))
		karte.custom_minimum_size = Vector2(NEU_KARTE_BREITE, 0.0)
		karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var inhalt := VBoxContainer.new()
		inhalt.add_theme_constant_override("separation", UiStil.A1)
		inhalt.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte.add_child(inhalt)
		var bild := TextureRect.new()
		bild.texture = load(pfad) as Texture2D
		bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		bild.custom_minimum_size = Vector2(0.0, NEU_BILD_HOEHE)
		bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inhalt.add_child(bild)
		var name := UiStil.label(naechstes.station_name(station_id), UiStil.GR_KLEIN + 2, UiStil.TINTE, UiStil.FETT)
		name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		inhalt.add_child(name)
		UiStil.drehe(karte, NEU_NEIGUNG[anzahl % NEU_NEIGUNG.size()])
		_neu_reihe.add_child(karte)
		anzahl += 1
	_neu_titel.text = UiText.t("neu_in_welt")
	_neu_titel.add_theme_color_override("font_color", UiStil.text_auf(UiStil.akzent_von(naechstes)))
	_neu_box.visible = anzahl > 0


## Welche Art zeigt dieser Titel? Nur die Themendatei weiss es.
static func art_fuer(titel: String, thema_daten: ThemeData) -> Art:
	if thema_daten == null or titel.is_empty():
		return Art.WELTWECHSEL
	if titel == String(thema_daten.abschnitt("eroeffnung").get("titel", "")):
		return Art.EROEFFNUNG
	if titel == String(thema_daten.abschnitt("abspann").get("titel", "")):
		return Art.ABSPANN
	return Art.WELTWECHSEL


func zeige(titel: String, text: String, knopf_text: String) -> void:
	var thema_daten: ThemeData = UiStil.welt_thema()
	art = art_fuer(titel, thema_daten)
	var akzent: Color = UiStil.akzent()
	var figur: String = ""
	var kicker: String = ""
	match art:
		Art.WELTWECHSEL:
			# Das Plakat steht schon in der Farbe der KOMMENDEN Welt.
			var naechstes: ThemeData = UiStil.naechstes_thema()
			if naechstes != null:
				akzent = UiStil.akzent_von(naechstes)
			if thema_daten != null:
				figur = String(thema_daten.abschnitt("weltwechsel").get("figur", ""))
			kicker = UiText.t("naechste_welt")
		Art.ABSPANN:
			kicker = UiText.t("bogen_fertig")
		Art.EROEFFNUNG:
			kicker = ""
	_grund.color = akzent
	_kicker_text.text = kicker
	_kicker.visible = not kicker.is_empty()
	_titel.text = titel
	# Der Titel der Eroeffnung ist der Spielname -- er darf plakativ gross sein.
	_titel.add_theme_font_size_override("font_size",
		UiStil.GR_POSTER if art == Art.EROEFFNUNG else UiStil.GR_RIESIG)
	_titel.add_theme_font_override("font", UiStil.schrift(UiStil.FETT,
		UiStil.GR_POSTER if art == Art.EROEFFNUNG else UiStil.GR_RIESIG))
	_figur_text.text = figur
	_figur.visible = not figur.is_empty()
	_setze_portrait(figur)
	_baue_neu(art, UiStil.naechstes_thema())
	# Abspann: Der Pflichthinweis (keine Anlageberatung) haengt main.gd an den
	# Text. Er bekommt einen eigenen, leisen Block -- im Fliesstext las er sich
	# wie ein weiterer Satz der Geschichte.
	var hinweis: String = ""
	if art == Art.ABSPANN and thema_daten != null:
		hinweis = String(thema_daten.abschnitt("abspann").get("hinweis", ""))
		if not hinweis.is_empty() and text.contains(hinweis):
			text = text.replace(hinweis, "").strip_edges()
	_hinweis_text.text = hinweis
	_hinweis_feld.visible = not hinweis.is_empty()
	_boni_text.text = UiText.t("neuanfang_hinweis") if art == Art.ABSPANN else ""
	_boni_text.visible = art == Art.ABSPANN
	_boni_text.add_theme_color_override("font_color", UiStil.text_auf(akzent))
	_text.text = text
	_text_feld.visible = not text.is_empty()
	var credits: Array = []
	if art == Art.ABSPANN and thema_daten != null:
		credits = thema_daten.abschnitt("abspann").get("zeilen", []) as Array
	_baue_rolltext(credits)
	var chat: Array = []
	if art == Art.EROEFFNUNG and thema_daten != null:
		chat = thema_daten.abschnitt("eroeffnung").get("chat", []) as Array
	_baue_chat(chat, thema_daten)
	if not chat.is_empty():
		_text_feld.visible = false
	_knopf.text = knopf_text if not knopf_text.is_empty() else UiText.t("weiter")

	# Gestaffelt einblenden statt alles auf einmal. Der Knopf kommt zuletzt und
	# absichtlich spaet: Wer ihn sofort sieht, drueckt ihn, ohne gelesen zu
	# haben -- und verpasst genau den Moment, fuer den die Szene da ist.
	var knopf_warten: float = VERZOEGERUNG_KNOPF_START if art == Art.EROEFFNUNG else VERZOEGERUNG_KNOPF
	modulate.a = 0.0
	for teil in [_kicker, _titel_feld, _figur, _text_feld, _knopf, _dekor, _portrait_buehne, _neu_box]:
		(teil as Control).modulate.a = 0.0
	_knopf.disabled = true
	var chat_zeit: float = CHAT_START + CHAT_PAUSE * float(chat.size())
	if not chat.is_empty():
		# Der Knopf kommt erst, wenn der Chat zu Ende ist -- ein Tipp beschleunigt.
		knopf_warten = chat_zeit

	var text_zeilen: int = 0
	if art == Art.ABSPANN:
		text_zeilen = text.split(String.chr(10), false).size()
		knopf_warten = VERZOEGERUNG_TEXT + ABSPANN_ZEILE * float(text_zeilen) + ABSPANN_CREDIT * float(credits.size() + 2) + 1.0

	var ablauf := create_tween()
	ablauf.tween_property(self, "modulate:a", 1.0, EINBLENDEN)
	_klebe(_dekor, 0.1, 1.08)
	_klebe(_kicker, 0.2, 1.2)
	_klebe(_titel_feld, 0.3, 1.25)
	_klebe(_figur, VERZOEGERUNG_TEXT * 0.8, 1.35)
	_klebe(_portrait_buehne, 0.25, 1.15)
	_klebe(_text_feld, VERZOEGERUNG_TEXT, 1.08)
	_klebe(_neu_box, VERZOEGERUNG_TEXT + 0.35, 1.08)
	if chat.is_empty():
		_klebe(_knopf, knopf_warten, 1.12)
	if art == Art.ABSPANN:
		_text.visible_characters = 0
	if art == Art.ABSPANN:
		_starte_abspann(text_zeilen, credits.size())
	elif chat.is_empty():
		var freigabe := create_tween()
		freigabe.tween_interval(knopf_warten)
		freigabe.tween_callback(func() -> void: _knopf.disabled = false)
	else:
		# Der Knopf liegt bis zur letzten Blase unsichtbar -- sonst steht er
		# neben einem halb leeren Chat und zieht den Blick weg.
		_knopf.modulate.a = 0.0


## Ein Teil "klebt" sich auf das Plakat: taucht leicht vergroessert auf und
## federt auf seine Groesse zurueck.
func _klebe(teil: Control, verzoegerung: float, von: float) -> void:
	var t := create_tween()
	t.tween_interval(verzoegerung)
	t.tween_callback(func() -> void:
		teil.pivot_offset = teil.size * 0.5
		teil.scale = Vector2(von, von))
	t.tween_property(teil, "modulate:a", 1.0, 0.12)
	t.parallel().tween_property(teil, "scale", Vector2.ONE, UiStil.DAUER_KAUF) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


# --- Abspann: Text und Rolltext ------------------------------------------------------

func _baue_rolltext(credits: Array) -> void:
	for kind in _roll_box.get_children():
		kind.queue_free()
	_roll_feld.visible = not credits.is_empty()
	if credits.is_empty():
		return
	for eintrag in credits:
		var l := UiStil.label(String(eintrag), UiStil.GR_MITTEL, UiStil.text_auf(UiStil.akzent()), UiStil.FETT)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.custom_minimum_size = Vector2(0.0, ABSPANN_CREDIT_HOEHE)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_roll_box.add_child(l)
	var hoehe: float = (ABSPANN_CREDIT_HOEHE + float(UiStil.A1)) * float(credits.size())
	_roll_feld.custom_minimum_size = Vector2(0.0, hoehe)
	_roll_box.anchor_left = 0.0
	_roll_box.anchor_right = 1.0
	_roll_box.anchor_top = 0.0
	_roll_box.anchor_bottom = 0.0
	_roll_box.offset_left = 0.0
	_roll_box.offset_right = 0.0
	_roll_box.offset_top = hoehe
	_roll_box.offset_bottom = hoehe
	_roll_box.modulate.a = 0.0


## Erst erscheint der Text Zeichen fuer Zeichen, dann rollen die Credits langsam
## nach oben, zuletzt wird der Knopf frei. Ein Tipp springt ans Ende.
func _starte_abspann(text_zeilen: int, credit_zeilen: int) -> void:
	_abspann_ablauf = create_tween()
	var t := _abspann_ablauf
	t.tween_interval(VERZOEGERUNG_TEXT)
	t.tween_property(_text, "visible_ratio", 1.0, ABSPANN_ZEILE * float(maxi(text_zeilen, 1)))
	if credit_zeilen > 0:
		t.tween_callback(func() -> void: _roll_box.modulate.a = 1.0)
		t.tween_property(_roll_box, "offset_top", 0.0, ABSPANN_CREDIT * float(credit_zeilen + 2)) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	t.tween_interval(1.0)
	t.tween_callback(func() -> void:
		_knopf.disabled = false
		_klebe(_knopf, 0.0, 1.12))
	_knopf.modulate.a = 0.0
	_knopf.disabled = true


# --- Eroeffnung als Chat -------------------------------------------------------------

func _baue_chat(chat: Array, thema_daten: ThemeData) -> void:
	for kind in _chat_box.get_children():
		kind.queue_free()
	_chat_blasen.clear()
	_chat_index = 0
	_chat_box.visible = not chat.is_empty()
	set_process(not chat.is_empty())
	if chat.is_empty():
		return
	_chat_rest = CHAT_START
	var vorher: String = ""
	for eintrag in chat:
		var d: Dictionary = eintrag as Dictionary
		var von: String = String(d.get("von", ""))
		var blase: Control = _chat_blase(von, String(d.get("text", "")), thema_daten, von != vorher)
		vorher = von
		blase.modulate.a = 0.0
		_chat_box.add_child(blase)
		_chat_blasen.append(blase)


## Eine Blase: links mit Portrait (Figur), rechts in Tinte (der Spieler, "du").
func _chat_blase(von: String, text: String, thema_daten: ThemeData, mit_kopf: bool) -> Control:
	var ich: bool = von == "du"
	var farbe: Color = UiStil.absender_farbe(thema_daten, von)
	var name: String = WeltTexte.absender(thema_daten, von)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if ich:
		zeile.alignment = BoxContainer.ALIGNMENT_END
	elif mit_kopf:
		zeile.add_child(UiStil.avatar(name if not name.is_empty() else von, farbe, 72.0))
	else:
		var luecke := Control.new()
		luecke.custom_minimum_size = Vector2(72.0, 0.0)
		luecke.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(luecke)
	var feld := PanelContainer.new()
	var stil: StickerBox
	if ich:
		stil = UiStil.sticker(UiStil.TINTE, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
			UiStil.SCHATTEN_Y, UiStil.PAPIER)
		stil.flaeche.corner_radius_bottom_right = 4
		stil.schatten.corner_radius_bottom_right = 4
		feld.size_flags_horizontal = Control.SIZE_SHRINK_END
	else:
		stil = UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
			UiStil.SCHATTEN_Y, farbe)
		stil.flaeche.corner_radius_top_left = 4
		stil.schatten.corner_radius_top_left = 4
		feld.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stil.content_margin_left = float(UiStil.A4)
	stil.content_margin_right = float(UiStil.A4)
	feld.add_theme_stylebox_override("panel", stil)
	feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", 0)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	feld.add_child(spalte)
	if not ich and mit_kopf and not name.is_empty():
		spalte.add_child(UiStil.label(name, UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT))
	var t := UiStil.label(text, UiStil.GR_MITTEL - 1, UiStil.PAPIER if ich else UiStil.TINTE,
		UiStil.FETT if ich else UiStil.TEXT_GEWICHT)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	t.custom_minimum_size = Vector2(300.0, 0.0)
	spalte.add_child(t)
	zeile.add_child(feld)
	return zeile


func _process(delta: float) -> void:
	if _chat_blasen.is_empty() or _chat_index > _chat_blasen.size():
		return
	_chat_rest -= delta
	if _chat_rest <= 0.0:
		_chat_naechste()


func _gui_input(ereignis: InputEvent) -> void:
	if _abspann_ablauf != null and _abspann_ablauf.is_valid() and _abspann_ablauf.is_running():
		var tip := ereignis as InputEventMouseButton
		if tip != null and tip.pressed and tip.button_index == MOUSE_BUTTON_LEFT:
			_abspann_ablauf.custom_step(100.0)
		return
	# Ein Tipp zeigt die naechste Blase sofort.
	if _chat_blasen.is_empty() or _chat_index >= _chat_blasen.size():
		return
	var m := ereignis as InputEventMouseButton
	if m != null and m.pressed and m.button_index == MOUSE_BUTTON_LEFT:
		_chat_naechste()


func _chat_naechste() -> void:
	if _chat_index >= _chat_blasen.size():
		return
	var blase: Control = _chat_blasen[_chat_index]
	_chat_index += 1
	_chat_rest = CHAT_PAUSE
	Haptik.puls(10)
	blase.pivot_offset = Vector2(blase.size.x * 0.1, blase.size.y * 0.5)
	blase.scale = Vector2(0.85, 0.85)
	var t := create_tween().set_parallel(true)
	t.tween_property(blase, "modulate:a", 1.0, 0.12)
	t.tween_property(blase, "scale", Vector2.ONE, UiStil.DAUER_KAUF) 		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if _chat_index >= _chat_blasen.size():
		# Letzte Blase: Jetzt darf der Spieler anfangen.
		_chat_rest = 1.0e9
		var fertig := create_tween()
		fertig.tween_interval(0.35)
		fertig.tween_callback(func() -> void:
			_knopf.disabled = false
			_klebe(_knopf, 0.0, 1.12))
