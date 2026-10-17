## Belohnungs-Moment: Vollbild-Karte, auf der die Zahl hochzählt (DESIGN_OVERHAUL 4.8).
##
## Gesetz 5: Belohnung ist ein EREIGNIS, keine Textpille. Die Karte zeigt die
## Figur jubelnd, einen Titel, die große Zahl (GR_HELD), die in 0,8 s von 0
## hochzählt, Konfetti und Haptik; ein Tipp auf "Einsammeln" lässt die Münzen
## zur Kopfleiste fliegen.
##
## Die Karte rechnet nichts: Der Betrag ist längst im Kern verbucht, sie zeigt ihn nur.
##
## Arten: ziel, marke, geschenk, raum, stern, offline, levelup -- sie bestimmen
## nur Titel, Symbol und Klang. Ob ein Ziel groß genug für einen Moment ist,
## sagt `ist_moment()` (Schwelle in data/tutorial/u3_texte.json).
class_name MomentView
extends Control

## `position` = Bildschirmmitte des Knopfes; dort starten die Münzen.
signal eingesammelt(position: Vector2)

const SYMBOLE: Dictionary = {
	"ziel": "ziel", "marke": "stern", "geschenk": "geschenk", "raum": "haus",
	"stern": "stern", "offline": "uhr", "levelup": "pfeil_hoch", "sammel": "geschenk",
}
const KLAENGE: Dictionary = {
	"ziel": &"meilenstein", "marke": &"fanfare", "geschenk": &"geschenk", "raum": &"raum",
	"stern": &"stern", "offline": &"geschenk", "levelup": &"levelup", "sammel": &"fanfare",
}
const TICKS: int = 14

var _saft: Saft
var _audio: AudioDirector
var _karte: PanelContainer
var _zahl: Label
var _knopf: Button
var _betrag: float = 0.0
var _text_gross: String = ""
var _art: String = "ziel"
var _vorlage: String = "+%s"
var _ganzzahl: bool = false   ## Zaehlt eine ganze Zahl (z. B. Level) von `zaehl_von` bis `zaehl_bis`, ohne Muenze
var _zaehl_von: int = 0
var _zaehl_bis: int = 0
var _fertig: bool = false
## K6 1c (Bastian: "kein OK-Druecken"): > 0 = schliesst nach so vielen Sekunden von selbst,
## ein Tipp irgendwohin schliesst sofort, kein Knopf. Aus `daten.auto_s`.
var _auto_s: float = 0.0
var _geschlossen: bool = false
var _strahlen: Strahlenkranz
var _buehne_haupt: Control


## Ab welchem Betrag ist ein Ziel ein Moment (sonst: nur Münzflug)?
static func ist_moment(art: String, betrag: float) -> bool:
	if art == "ziel":
		return betrag >= U3Text.schwelle("ziel_moment_ab", 200.0)
	return true


## Die eine Zeile unter dem Rang (K2 4.4): "Neu: Crew-Karten" oder, wenn der Rang nichts
## freischaltet, "Neu: +0,5 % Einkommen". Nie leer. Schaltet ein Rang mehreres frei, steht
## es in einer Zeile ("Neu: Crew-Karten · Fortschritt-Übersicht"). Die Texte stehen unter
## rang_neu_<merkmal> in data/i18n; ein Merkmal ohne Text wird uebersprungen.
static func neu_zeile(freischaltung: Array, bonus_prozent: float) -> String:
	var teile: PackedStringArray = []
	for m in freischaltung:
		var schluessel: String = "rang_neu_" + String(m)
		if UiText.hat(schluessel):
			var t: String = UiText.t(schluessel)
			if not teile.is_empty():
				# Nur der erste Teil traegt das "Neu:" -- die weiteren hängen kurz an.
				var doppelpunkt: int = t.find(": ")
				t = t.substr(doppelpunkt + 2) if doppelpunkt >= 0 else t
			teile.append(t)
	if not teile.is_empty():
		return " · ".join(teile)
	var zahl: String = ("%.1f" % bonus_prozent).replace(".", ",")
	if zahl.ends_with(",0"):
		zahl = zahl.substr(0, zahl.length() - 2)
	return UiText.t("rang_neu_bonus") % zahl


## Daten des Rang-Up-Moments (K2 4.4): Mo jubelnd, die Rangzahl zaehlt von der alten zur neuen,
## der Rangname ist der Titel, darunter die EINE Zeile "Neu: ...". Knopf "Weiter".
## `info` ist GameCore.spieler_level_info(); `bonus_prozent` der Einkommensbonus je Rang.
static func rang_daten(rang: int, rang_name: String, freischaltung: Array, bonus_prozent: float) -> Dictionary:
	return {"art": "levelup", "zahl": rang, "betrag": 0.0, "zaehl_von": maxi(rang - 1, 1),
		"zaehl_bis": rang, "vorlage": UiText.t("levelup_zahl"), "titel": rang_name,
		"untertitel": neu_zeile(freischaltung, bonus_prozent), "figur": "mo", "ausdruck": "jubelnd"}


## `daten`: art, titel (sonst Standard der Art), untertitel, betrag (€, zählt hoch),
## text_gross (statt Betrag, z. B. "×1,5"), figur (Absender-Schlüssel), ausdruck,
## knopf, vorlage (Format der Zahl, Standard "+%s"), symbol.
static func zeige_moment(eltern: Node, daten: Dictionary, thema: ThemeData, saft: Saft = null,
		audio: AudioDirector = null) -> MomentView:
	var ansicht := MomentView.new()
	eltern.add_child(ansicht)
	ansicht.zeige(daten, thema, saft, audio)
	return ansicht


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()


func standard_titel(art: String, daten: Dictionary) -> String:
	var schluessel: String = "moment_" + art
	var t: String = U3Text.t(schluessel)
	if t.contains("%d"):
		return t % int(daten.get("zahl", 0))
	return t


func zeige(daten: Dictionary, thema: ThemeData, saft: Saft = null, audio: AudioDirector = null) -> void:
	_saft = saft
	_audio = audio
	_art = String(daten.get("art", "ziel"))
	_betrag = float(daten.get("betrag", 0.0))
	_text_gross = String(daten.get("text_gross", ""))
	_vorlage = String(daten.get("vorlage", "+%s"))
	_auto_s = float(daten.get("auto_s", 0.0))
	_ganzzahl = daten.has("zaehl_bis")
	_zaehl_bis = int(daten.get("zaehl_bis", 0))
	_zaehl_von = int(daten.get("zaehl_von", maxi(_zaehl_bis - 1, 0)))
	var titel: String = String(daten.get("titel", ""))
	if titel.is_empty():
		titel = standard_titel(_art, daten)

	var schleier := ColorRect.new()
	schleier.color = Color(UiStil.SCHLEIER.r, UiStil.SCHLEIER.g, UiStil.SCHLEIER.b, 0.78)
	schleier.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	schleier.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(schleier)

	var mitte := CenterContainer.new()
	mitte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(mitte)

	_karte = PanelContainer.new()
	_karte.custom_minimum_size = Vector2(640.0, 0.0)
	_karte.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 10,
		UiStil.KONTUR + 1, float(UiStil.A5), UiStil.SCHATTEN_Y * 2.0))
	mitte.add_child(_karte)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_karte.add_child(box)

	# Buehne: Strahlenkranz, dahinter/davor Figur (rund gerahmt, nie abgeschnitten)
	# oder Stations-Bild; bei Raumkaeufen dazu das Band "NEU".
	box.add_child(_baue_buehne(daten))

	var titel_chip := PanelContainer.new()
	titel_chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.akzent(), float(UiStil.A5), float(UiStil.A2), 3.0))
	titel_chip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var tl := UiStil.label(titel, UiStil.GR_GROSS, UiStil.akzent_text(), UiStil.FETT)
	tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	titel_chip.add_child(tl)
	box.add_child(titel_chip)

	# Die große Zahl: Gold-Sticker, GR_HELD. Beim Raumkauf steht dort nur der Name
	# der neuen Station als Schrift -- kein zweiter Kasten, der wie ein Knopf aussieht.
	if _art == "sammel" and _betrag <= 0.0 and _text_gross.is_empty():
		# Sammelfenster ohne Geld: Die Zeilen sind der Inhalt, keine leere Zahl darueber.
		_zahl = tl
	elif _art == "raum" or (_art == "sammel" and _betrag <= 0.0):
		_zahl = UiStil.label(_text_gross, UiStil.GR_HELD - 8, UiStil.TINTE, UiStil.FETT)
		_zahl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_zahl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(_zahl)
	else:
		var zahl_feld := PanelContainer.new()
		zahl_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_KARTE,
			UiStil.KONTUR, float(UiStil.A4), UiStil.SCHATTEN_Y_PRIMAER))
		box.add_child(zahl_feld)
		var zeile := HBoxContainer.new()
		zeile.alignment = BoxContainer.ALIGNMENT_CENTER
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zahl_feld.add_child(zeile)
		if _text_gross.is_empty() and not _ganzzahl:
			zeile.add_child(UiStil.symbolbild("muenze", 76.0))
		# Sammelfenster: mehrere Werte in einer Zeile ("×1,5 ×1,5 ×2") -- kleiner, damit sie passen.
		var lang: bool = _art == "sammel" and _text_gross.length() > 10
		_zahl = UiStil.label("", UiStil.GR_TITEL if lang else UiStil.GR_HELD, UiStil.TINTE, UiStil.FETT)
		if lang:
			_zahl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			_zahl.custom_minimum_size = Vector2(520.0, 0.0)
		_zahl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		zeile.add_child(_zahl)
		if _ganzzahl:
			_zahl.text = _vorlage % str(_zaehl_von)
		else:
			_zahl.text = _text_gross if not _text_gross.is_empty() else _vorlage % "0"

	# Sammelfenster mit mehreren Arten: eine Zeile je Art (Symbol, Text, Werte).
	var zeilen: Array = daten.get("zeilen", []) as Array
	if not zeilen.is_empty():
		box.add_child(_baue_zeilen(zeilen))

	var unter: String = String(daten.get("untertitel", ""))
	if not unter.is_empty():
		# Beim Rang-Up ist die Zeile "Neu: ..." die eigentliche Nachricht: gross und dunkel.
		var rang_zeile: bool = _art == "levelup"
		var u := UiStil.label(unter, UiStil.GR_MITTEL if rang_zeile else UiStil.GR_TEXT,
			UiStil.TINTE if rang_zeile else UiStil.TINTE_2, UiStil.FETT if rang_zeile else UiStil.TEXT_GEWICHT)
		u.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		u.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		box.add_child(u)

	_knopf = Sheet.kaufknopf()
	var standard_knopf: String = U3Text.t("moment_einsammeln") if _betrag > 0.0 else U3Text.t("szene_ende")
	_knopf.text = String(daten.get("knopf", standard_knopf))
	_knopf.disabled = true
	_knopf.pressed.connect(_einsammeln)
	box.add_child(_knopf)
	if _auto_s > 0.0:
		_knopf.visible = false
		get_tree().create_timer(_auto_s).timeout.connect(_schliesse_auto)

	_ablauf()


## Die Zeilen des Sammelfensters: Papier-Streifen mit Symbol, Text links, Werte rechts.
func _baue_zeilen(zeilen: Array) -> Control:
	var liste := VBoxContainer.new()
	liste.add_theme_constant_override("separation", UiStil.A2)
	liste.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for z in zeilen:
		var zeile_daten: Dictionary = z as Dictionary
		var streifen := PanelContainer.new()
		streifen.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER_2, UiStil.RADIUS_KNOPF,
			UiStil.KONTUR_CHIP, float(UiStil.A3), 2.0))
		streifen.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var reihe := HBoxContainer.new()
		reihe.add_theme_constant_override("separation", UiStil.A3)
		reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
		streifen.add_child(reihe)
		var sym: TextureRect = UiStil.symbolbild(String(zeile_daten.get("symbol", "stern")), 48.0)
		sym.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		reihe.add_child(sym)
		# Links der Satz ("4 neue Sterne"), darunter die Werte -- sie duerfen umbrechen.
		var spalte := VBoxContainer.new()
		spalte.add_theme_constant_override("separation", 0)
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		reihe.add_child(spalte)
		spalte.add_child(UiStil.label(String(zeile_daten.get("text", "")), UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT))
		var wert_text: String = String(zeile_daten.get("wert", ""))
		if not wert_text.is_empty():
			var wert := UiStil.label(wert_text, UiStil.GR_TEXT, UiStil.GOLD_TEXT, UiStil.FETT)
			wert.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			spalte.add_child(wert)
		liste.add_child(streifen)
	return liste


## Die Feier-Buehne: Strahlenkranz hinten, davor das Stations-Bild (falls da) und die
## Figur im runden Rahmen. Alles liegt in einem festen Feld, die Teile werden bei jeder
## Groessenaenderung neu mittig gesetzt.
func _baue_buehne(daten: Dictionary) -> Control:
	var buehne := Control.new()
	buehne.custom_minimum_size = Vector2(0.0, 300.0)
	buehne.mouse_filter = Control.MOUSE_FILTER_IGNORE
	buehne.clip_contents = true
	_strahlen = Strahlenkranz.new()
	_strahlen.custom_minimum_size = Vector2(300.0, 300.0)
	buehne.add_child(_strahlen)

	var figur: String = String(daten.get("figur", ""))
	var bild_pfad: String = String(daten.get("bild", ""))
	var station_bild: Texture2D = null
	if not bild_pfad.is_empty() and ResourceLoader.exists(bild_pfad):
		station_bild = load(bild_pfad) as Texture2D
	var teile: Array = []   # [Control, Versatz]
	var haupt: Control = null
	if station_bild != null:
		var tr := TextureRect.new()
		tr.texture = station_bild
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(210.0, 210.0)
		tr.size = tr.custom_minimum_size
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		buehne.add_child(tr)
		haupt = tr
		teile.append([tr, Vector2(20.0, 0.0)])
		if UiStil.portrait(figur, String(daten.get("ausdruck", "jubelnd"))) != null:
			var kleine: Control = UiStil.avatar(figur, UiStil.akzent(), 112.0, String(daten.get("ausdruck", "jubelnd")))
			kleine.size = Vector2(112.0, 112.0)
			buehne.add_child(kleine)
			teile.append([kleine, Vector2(-150.0, 70.0)])
	else:
		var ausdruck: String = String(daten.get("ausdruck", "jubelnd"))
		if UiStil.portrait(figur, ausdruck) != null:
			var gross: Control = UiStil.avatar(figur, UiStil.akzent(), 220.0, ausdruck)
			gross.size = Vector2(220.0, 220.0)
			buehne.add_child(gross)
			haupt = gross
			teile.append([gross, Vector2.ZERO])
		else:
			var sym: Control = UiStil.symbolbild(String(daten.get("symbol", SYMBOLE.get(_art, "stern"))), 150.0)
			sym.size = Vector2(150.0, 150.0)
			buehne.add_child(sym)
			haupt = sym
			teile.append([sym, Vector2.ZERO])
	var band_text: String = String(daten.get("band", ""))
	if not band_text.is_empty():
		var band := PanelContainer.new()
		band.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.WARNUNG, 14, UiStil.KONTUR_CHIP,
			float(UiStil.A3), 3.0))
		band.add_child(UiStil.label(band_text.to_upper(), UiStil.GR_TEXT, UiStil.WEISS, UiStil.FETT))
		band.rotation = deg_to_rad(12.0)
		band.mouse_filter = Control.MOUSE_FILTER_IGNORE
		buehne.add_child(band)
		teile.append([band, Vector2(110.0, -100.0)])
	_buehne_haupt = haupt
	buehne.resized.connect(func() -> void:
		var m: Vector2 = buehne.size * 0.5
		_strahlen.size = Vector2(buehne.size.x, buehne.size.y)
		_strahlen.position = Vector2.ZERO
		for t in teile:
			var c: Control = t[0]
			var g: Vector2 = c.get_combined_minimum_size().max(c.size)
			c.size = g
			c.pivot_offset = g * 0.5
			c.position = m - g * 0.5 + (t[1] as Vector2))
	return buehne


func _ablauf() -> void:
	_karte.modulate.a = 0.0
	UiStil.aufploppen.call_deferred(_karte, 0.78)
	create_tween().tween_property(_karte, "modulate:a", 1.0, 0.15)
	if _audio != null:
		_audio.spiele(KLAENGE.get(_art, &"meilenstein") as StringName)
	var mitte: Vector2 = get_viewport_rect().size * 0.5
	if _saft != null:
		_saft.konfetti(mitte + Vector2(0.0, -200.0), 60)
		_saft.blitz(UiStil.GOLD, 0.25, 0.2)
	if _buehne_haupt != null:
		_buehne_haupt.scale = Vector2(0.3, 0.3)
		create_tween().tween_property(_buehne_haupt, "scale", Vector2.ONE, 0.55).set_delay(0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	Haptik.puls(40)

	var t := create_tween()
	t.tween_interval(0.35)
	if _ganzzahl:
		# Ganze Zahl (Level): zaehlt Schritt fuer Schritt von der alten zur neuen Stufe.
		var schritte: int = maxi(_zaehl_bis - _zaehl_von, 1)
		var letzte: Array[int] = [-1]
		t.tween_method(func(anteil: float) -> void:
			var wert: int = _zaehl_von + int(round(anteil * float(_zaehl_bis - _zaehl_von)))
			_zahl.text = _vorlage % str(wert)
			var tick: int = int(anteil * float(schritte))
			if tick != letzte[0]:
				letzte[0] = tick
				if _audio != null:
					_audio.spiele(&"zaehlen", tick),
			0.0, 1.0, UiStil.DAUER_ZAEHLEN).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
		t.tween_callback(func() -> void:
			_zahl.text = _vorlage % str(_zaehl_bis))
	elif _text_gross.is_empty() and _betrag > 0.0:
		# Die Zahl zählt hoch; jeder Schritt tickt (Tonhöhe steigt mit der Kennzahl).
		var letzter: Array[int] = [-1]
		t.tween_method(func(anteil: float) -> void:
			_zahl.text = _vorlage % UiStil.zahl(_betrag * anteil)
			var tick: int = int(anteil * TICKS)
			if tick != letzter[0]:
				letzter[0] = tick
				if _audio != null:
					_audio.spiele(&"zaehlen", tick),
			0.0, 1.0, UiStil.DAUER_ZAEHLEN).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
		t.tween_callback(func() -> void:
			_zahl.text = _vorlage % UiStil.zahl(_betrag))
	else:
		t.tween_interval(UiStil.DAUER_ZAEHLEN * 0.5)
	t.tween_callback(func() -> void:
		_fertig = true
		_knopf.disabled = false
		UiStil.aufploppen(_zahl, 1.18)
		Haptik.puls(Haptik.DAUER_STERN))


## Ohne Knopf (auto_s): ein Tipp irgendwohin schliesst sofort, auch mitten in der Feier.
func _gui_input(ereignis: InputEvent) -> void:
	if _auto_s > 0.0 and UiStil.ist_tipp(ereignis):
		accept_event()
		_schliesse_auto()


func _schliesse_auto() -> void:
	if _geschlossen or not is_inside_tree():
		return
	_fertig = true
	_einsammeln()


func _einsammeln() -> void:
	if not _fertig or _geschlossen:
		return
	_fertig = false
	_geschlossen = true
	var pos: Vector2 = _knopf.get_global_rect().get_center()
	if _saft != null and _betrag > 0.0:
		_saft.muenzen(pos, 14)
		_saft.funken(pos, UiStil.GOLD, 16)
	eingesammelt.emit(pos)
	var eltern: Node = get_parent()
	if eltern is CanvasLayer and eltern.get_child_count() == 1:
		eltern.queue_free()
	else:
		queue_free()


## Strahlenkranz: weicher Schein und langsam drehende Strahlen hinter der Figur.
class Strahlenkranz extends Control:
	var _zeit: float = 0.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _process(delta: float) -> void:
		_zeit += delta
		queue_redraw()

	func _draw() -> void:
		var m: Vector2 = size * 0.5
		var r: float = minf(size.x, size.y) * 0.5
		var strahlen: int = 14
		for i in strahlen:
			var a0: float = _zeit * 0.35 + TAU * float(i) / strahlen
			var a1: float = a0 + TAU / strahlen * 0.5
			var weit: float = r * 1.9
			draw_colored_polygon(PackedVector2Array([m, m + Vector2.from_angle(a0) * weit,
				m + Vector2.from_angle(a1) * weit]), Color(UiStil.GOLD, 0.30))
		for k in 5:
			draw_circle(m, r * (0.95 - 0.13 * k), Color(1.0, 0.95, 0.7, 0.16))
