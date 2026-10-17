## Das Tagesgeschenk: ein Symbol am rechten Rand und eine kompakte Karte, kein Fenster beim Start.
##
## Der Kern (C) entscheidet, ob ein Geschenk da ist, wie hoch es ist und welcher
## Serientag gilt (`kern.geschenk_bereit()`); die Ansicht zeigt es. Das Symbol am Rand
## pulsiert, solange ein Geschenk bereit ist, und verschwindet danach bis zum naechsten
## Kalendertag. Ein Tipp darauf oeffnet die kompakte Karte (sieben Felder mit dem
## Faktor je Serientag, heute leuchtet, der Betrag zaehlt hoch); ein Tipp daneben
## schliesst sie wieder. Abholen ist Saft: Muenzen fliegen, Funken, Betrag steigt auf.
## Reisst die Serie, faengt sie ohne Strafe bei Tag 1 an -- das steht hier nicht,
## die Karte zeigt nur, wo man ist.
##
## Einbau (main.gd, nach dem Offline-Bericht, statt der Modal-Schlange):
##   GeschenkView.biete_am_rand(self, kern, _hud.saft, _audio)
##
## Die alte Form `zeige_falls_bereit` (Karte sofort, mit Schleier) bleibt fuer Aufrufer, die
## das Geschenk bewusst als Fenster wollen (Vorschau, Tests).
class_name GeschenkView
extends Control

## `position` ist die Bildschirmmitte des Knopfes -- dort starten die Muenzen.
signal abholen(position: Vector2)
## Mit Werbung: `faktor` ist der Gesamtfaktor des Betrags (2 = doppelt).
signal abholen_doppelt(position: Vector2, faktor: float)
## Die Karte wurde ohne Abholen geschlossen (Tipp daneben).
signal geschlossen

const ZAEHL_DAUER: float = 1.0
## Ebene des Rand-Symbols: ueber dem Hud, unter allen Fenstern (die liegen auf 16).
const EBENE_RAND: int = 6
const KARTE_BREITE: float = 560.0
## Symbolgroesse am Rand (Tippziel >= 48 dp = 96 logische px bei 2x; 88 plus Hitbox-Rand).
const RAND_KANTE: float = 88.0
const RAND_ABSTAND: float = 10.0
## Obere Kante des Rand-Symbols als Anteil der Bildhoehe.
const RAND_HOEHE_ANTEIL: float = 0.30

var _karte: PanelContainer
var _betrag: Label
var _knopf: Button
var _doppelt: Button
var _summe: float = 0.0
## Obere Kante der Karte in Pixeln; negativ = Bildmitte. Das Rand-Symbol setzt es.
var karte_oben: float = -1.0
## Mit Schleier (altes Fenster) oder nur ein Fang-Feld, das beim Tipp daneben schliesst.
var mit_schleier: bool = false


## Das Symbol am rechten Rand. Es baut sich eine eigene Ebene unter `eltern`, fragt den Kern
## selbst, ob heute ein Geschenk da ist (auch spaeter, etwa nach Mitternacht), und verbucht
## es bei Tipp auf "Abholen". Gibt das Symbol zurueck.
static func biete_am_rand(eltern: Node, kern: GameCore, saft: Saft = null,
		audio: AudioDirector = null) -> RandSymbol:
	var ebene := CanvasLayer.new()
	ebene.layer = EBENE_RAND
	eltern.add_child(ebene)
	var symbol := RandSymbol.new()
	symbol.kern = kern
	symbol.saft = saft
	symbol.audio = audio
	ebene.add_child(symbol)
	symbol.pruefe()
	return symbol


## Baut Ebene und Karte, wenn heute ein Geschenk da ist (altes Fenster mit Schleier),
## und verbucht es bei Tipp auf "Abholen". Gibt die Karte zurueck oder null.
static func zeige_falls_bereit(eltern: Node, kern: GameCore, saft: Saft = null,
		audio: AudioDirector = null) -> GeschenkView:
	var info: Dictionary = kern.geschenk_bereit()
	if info.is_empty():
		return null
	var ebene := CanvasLayer.new()
	ebene.layer = 16
	eltern.add_child(ebene)
	var ansicht := GeschenkView.new()
	ansicht.mit_schleier = true
	ebene.add_child(ansicht)
	ansicht.zeige(info)
	ansicht.verbinde(kern, saft, audio, func() -> void: ebene.queue_free())
	# Der Dienst ist ueber die Gruppe "werbung" erreichbar (main.gd haengt ihn in den Baum).
	var baum: SceneTree = eltern.get_tree() if eltern.is_inside_tree() else null
	if baum != null:
		ansicht.biete_doppelt(baum.get_first_node_in_group(&"werbung") as AdService)
	return ansicht


## Verdrahtet "Abholen" mit dem Kern: buchen, Saft, Ton, danach `fertig`.
func verbinde(kern: GameCore, saft: Saft, audio: AudioDirector, fertig: Callable) -> void:
	var auszahlen: Callable = func(von: Vector2, faktor: float) -> void:
		var betrag: float = kern.geschenk_abholen()
		if betrag > 0.0 and faktor > 1.0:
			# Mit Werbung: der Betrag noch einmal (K3 C1, geschenk_doppelt).
			Hud.schreibe_gut(kern, betrag * (faktor - 1.0))
			betrag *= faktor
		if betrag > 0.0 and saft != null:
			saft.muenzen(von, 18)
			saft.funken(von, UiStil.GOLD, 20)
			saft.betrag(von + Vector2(0.0, -80.0), "+" + UiStil.zahl(betrag), UiStil.GOLD)
		if audio != null:
			audio.spiele(&"geschenk")
		fertig.call()
	abholen.connect(func(von: Vector2) -> void: auszahlen.call(von, 1.0))
	abholen_doppelt.connect(func(von: Vector2, faktor: float) -> void: auszahlen.call(von, faktor))


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	theme = UiStil.thema()


## `info` = kern.geschenk_bereit(): {tag, serie_max, betrag, faktor, tage}.
func zeige(info: Dictionary) -> void:
	var tag: int = int(info.get("tag", 1))
	var serie_max: int = int(info.get("serie_max", 7))
	_summe = float(info.get("betrag", 0.0))
	var faktoren: Array = info.get("tage", []) as Array

	# Fang-Feld: ein Tipp daneben schliesst die Karte (kein OK-Druecken noetig).
	var fang := ColorRect.new()
	fang.color = UiStil.SCHLEIER if mit_schleier else Color(0, 0, 0, 0.0)
	fang.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fang.mouse_filter = Control.MOUSE_FILTER_STOP
	fang.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			schliesse())
	add_child(fang)

	_karte = PanelContainer.new()
	_karte.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE + 6,
		UiStil.KONTUR, float(UiStil.A4), UiStil.SCHATTEN_Y * 2.0))
	_karte.custom_minimum_size = Vector2(KARTE_BREITE, 0.0)
	_karte.mouse_filter = Control.MOUSE_FILTER_STOP
	if karte_oben >= 0.0:
		var spalte := VBoxContainer.new()
		spalte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(spalte)
		var abstand := Control.new()
		abstand.custom_minimum_size = Vector2(0.0, karte_oben)
		abstand.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(abstand)
		_karte.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		spalte.add_child(_karte)
	else:
		var mitte := CenterContainer.new()
		mitte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(mitte)
		mitte.add_child(_karte)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A3)
	_karte.add_child(box)

	# Kopf: Geschenk-Symbol links, Titel und Tag rechts daneben.
	var kopf := HBoxContainer.new()
	kopf.add_theme_constant_override("separation", UiStil.A3)
	box.add_child(kopf)
	var geschenk := UiStil.symbolbild("geschenk", 84.0)
	geschenk.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	kopf.add_child(geschenk)
	var kopf_text := VBoxContainer.new()
	kopf_text.add_theme_constant_override("separation", UiStil.A1)
	kopf_text.alignment = BoxContainer.ALIGNMENT_CENTER
	kopf_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	kopf.add_child(kopf_text)
	var titel := UiStil.label(UiText.t("geschenk_titel"), UiStil.GR_MITTEL + 2, UiStil.TINTE, UiStil.FETT)
	titel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kopf_text.add_child(titel)
	var chip := PanelContainer.new()
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.akzent(), float(UiStil.A3), float(UiStil.A1), 2.0))
	chip.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	chip.add_child(UiStil.label(UiText.t("geschenk_tag") % [tag, serie_max], UiStil.GR_KLEIN,
		UiStil.akzent_text(), UiStil.FETT))
	kopf_text.add_child(chip)

	# Die Serie: ein Feld je Tag. Vergangene mit Haken, heute in Gold.
	var reihe := HBoxContainer.new()
	reihe.alignment = BoxContainer.ALIGNMENT_CENTER
	reihe.add_theme_constant_override("separation", UiStil.A1)
	box.add_child(reihe)
	for i in range(serie_max):
		reihe.add_child(_tagesfeld(i + 1, tag, float(faktoren[i]) if i < faktoren.size() else 1.0))

	var zahl_feld := PanelContainer.new()
	zahl_feld.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A2), UiStil.SCHATTEN_Y))
	box.add_child(zahl_feld)
	var zahl_zeile := HBoxContainer.new()
	zahl_zeile.alignment = BoxContainer.ALIGNMENT_CENTER
	zahl_zeile.add_theme_constant_override("separation", UiStil.A3)
	zahl_feld.add_child(zahl_zeile)
	zahl_zeile.add_child(UiStil.symbolbild("muenze", 56.0))
	_betrag = UiStil.label(UiText.t("offline_ertrag") % "0", UiStil.GR_ZAHL, UiStil.TINTE, UiStil.FETT)
	zahl_zeile.add_child(_betrag)

	_knopf = Sheet.kaufknopf()
	_knopf.text = UiText.t("geschenk_abholen")
	_knopf.pressed.connect(func() -> void:
		_knopf.disabled = true
		Haptik.puls(Haptik.DAUER_STERN)
		abholen.emit(_knopf.get_global_rect().get_center()))
	box.add_child(_knopf)

	_karte.modulate.a = 0.0
	UiStil.aufploppen.call_deferred(_karte, 0.85)
	create_tween().tween_property(_karte, "modulate:a", 1.0, 0.15)
	var zaehlen := create_tween()
	zaehlen.tween_interval(0.3)
	zaehlen.tween_method(func(anteil: float) -> void:
		_betrag.text = UiText.t("offline_ertrag") % UiStil.zahl(_summe * anteil),
		0.0, 1.0, ZAEHL_DAUER).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	zaehlen.tween_callback(func() -> void: UiStil.aufploppen(_betrag, 1.15))


## Schliesst die Karte ohne Abholen (Tipp daneben). Das Geschenk bleibt bereit.
func schliesse() -> void:
	geschlossen.emit()
	queue_free()


## Ein Feld der Serie: Faktor darunter, Haken oder Geschenk darueber.
func _tagesfeld(nr: int, heute: int, faktor: float) -> Control:
	var ist_heute: bool = nr == heute
	var vorbei: bool = nr < heute
	var feld := PanelContainer.new()
	var farbe: Color = UiStil.GOLD if ist_heute else (UiStil.PAPIER_2 if not vorbei else UiStil.KAUFEN)
	var stil := UiStil.sticker(farbe, UiStil.RADIUS_KNOPF - 4,
		UiStil.KONTUR if ist_heute else UiStil.KONTUR_CHIP, float(UiStil.A1),
		UiStil.SCHATTEN_Y if ist_heute else 0.0)
	feld.add_theme_stylebox_override("panel", stil)
	feld.custom_minimum_size = Vector2(64.0 if ist_heute else 56.0, 84.0 if ist_heute else 76.0)
	feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var spalte := VBoxContainer.new()
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.add_theme_constant_override("separation", 0)
	feld.add_child(spalte)
	var bild := UiStil.symbolbild("haken" if vorbei else "geschenk", 28.0)
	bild.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	bild.modulate = Color(1, 1, 1, 1.0 if (ist_heute or vorbei) else 0.45)
	spalte.add_child(bild)
	var f := UiStil.label("×" + Stationsmenue.faktor_text(faktor), UiStil.GR_KLEIN - 2, UiStil.TINTE,
		UiStil.FETT)
	f.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	spalte.add_child(f)
	var n := UiStil.label(str(nr), UiStil.GR_KLEIN - 4, UiStil.TINTE_2, UiStil.FETT)
	n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	spalte.add_child(n)
	return feld


## Das Angebot "doppelt" (K3 C1): ein zweiter Knopf ueber "Abholen", mit dem Betrag
## im Text. Wer ihn nicht antippt, holt das Geschenk wie immer ab.
func biete_doppelt(dienst: AdService) -> void:
	if dienst == null or _knopf == null or not dienst.ist_bereit(&"geschenk_doppelt"):
		return
	var faktor: float = float(dienst.wert(&"geschenk_doppelt", "faktor", 2.0))
	_doppelt = Sheet.kaufknopf(UiStil.GOLD)
	_doppelt.text = UiText.t("werbung_geschenk_doppelt") % UiStil.zahl(_summe * (faktor - 1.0))
	_doppelt.custom_minimum_size = Vector2(0.0, 80.0)
	var box: Node = _knopf.get_parent()
	box.add_child(_doppelt)
	box.move_child(_doppelt, _knopf.get_index())
	var beschriftung: String = _doppelt.text
	_doppelt.pressed.connect(func() -> void:
		_doppelt.disabled = true
		_doppelt.text = UiText.t("werbung_laeuft")
		dienst.zeige_belohnt(&"geschenk_doppelt"))
	dienst.belohnung_verdient.connect(func(p: StringName) -> void:
		if p == &"geschenk_doppelt" and is_instance_valid(_knopf):
			_knopf.disabled = true
			Haptik.puls(Haptik.DAUER_STERN)
			abholen_doppelt.emit(_knopf.get_global_rect().get_center(), faktor))
	dienst.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void:
		if is_instance_valid(_doppelt):
			_doppelt.disabled = false
			_doppelt.text = beschriftung)
	dienst.melde_angebot(&"geschenk_doppelt")


## Das Symbol am rechten Rand. Pulsiert, solange ein Geschenk bereit ist; ein Tipp
## oeffnet die Karte. Nichts bereit = nichts zu sehen.
class RandSymbol extends Control:
	var kern: GameCore
	var saft: Saft
	var audio: AudioDirector
	var _knopf: Control
	var _bild: TextureRect
	var _punkt: PanelContainer
	var _karte: GeschenkView
	var _puls: float = 0.0
	var _takt: float = 0.0
	var _bereit: bool = false

	func _init() -> void:
		set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		theme = UiStil.thema()
		visible = false
		# Hitbox = ganze Flaeche des Symbols (Tippziel), das Bild liegt darauf.
		_knopf = Control.new()
		_knopf.mouse_filter = Control.MOUSE_FILTER_STOP
		_knopf.custom_minimum_size = Vector2(RAND_KANTE, RAND_KANTE)
		_knopf.size = Vector2(RAND_KANTE, RAND_KANTE)
		_knopf.gui_input.connect(func(e: InputEvent) -> void:
			if UiStil.ist_tipp(e):
				_oeffne())
		add_child(_knopf)
		var flaeche := PanelContainer.new()
		flaeche.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		flaeche.offset_bottom = -UiStil.SCHATTEN_Y
		flaeche.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var stil := UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_KARTE, UiStil.KONTUR, 0.0, UiStil.SCHATTEN_Y)
		stil.set_content_margin_all(12.0)
		flaeche.add_theme_stylebox_override("panel", stil)
		_knopf.add_child(flaeche)
		_bild = UiStil.symbolbild("geschenk", RAND_KANTE - 24.0)
		flaeche.add_child(_bild)
		# Roter Zahl-Punkt: da wartet etwas.
		_punkt = PanelContainer.new()
		var ps := UiStil.chip(UiStil.WARNUNG, 8.0, 0.0, 0.0)
		ps.flaeche.border_color = UiStil.PAPIER
		ps.flaeche.set_border_width_all(UiStil.KONTUR_CHIP)
		_punkt.add_theme_stylebox_override("panel", ps)
		_punkt.custom_minimum_size = Vector2(32.0, 32.0)
		_punkt.size = Vector2(32.0, 32.0)
		_punkt.position = Vector2(RAND_KANTE - 22.0, -12.0)
		_punkt.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var z := UiStil.label("1", UiStil.GR_KLEIN - 2, UiStil.WEISS, UiStil.FETT)
		z.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		z.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_punkt.add_child(z)
		_knopf.add_child(_punkt)

	func _ready() -> void:
		get_viewport().size_changed.connect(_lege)
		_lege()

	## Am rechten Rand, im oberen Drittel: ueber der Welt, unter Kopf- und Zielleiste.
	func _lege() -> void:
		var flaeche: Vector2 = get_viewport_rect().size if is_inside_tree() else Vector2(720.0, 1280.0)
		_knopf.position = Vector2(flaeche.x - RAND_KANTE - RAND_ABSTAND, flaeche.y * RAND_HOEHE_ANTEIL)

	## Fragt den Kern: Ist heute ein Geschenk da? Zeigt oder versteckt das Symbol entsprechend.
	func pruefe() -> void:
		if kern == null:
			return
		var da: bool = not kern.geschenk_bereit().is_empty()
		if da == _bereit and visible == da:
			return
		_bereit = da
		visible = da
		if da and is_inside_tree():
			UiStil.aufploppen(_knopf, 0.2)

	func ist_bereit() -> bool:
		return _bereit

	func _oeffne() -> void:
		if _karte != null and is_instance_valid(_karte):
			return
		var info: Dictionary = kern.geschenk_bereit()
		if info.is_empty():
			pruefe()
			return
		if audio != null:
			audio.spiele(&"tipp")
		UiStil.aufploppen(_knopf, 0.85)
		_karte = GeschenkView.new()
		# Die Karte sitzt unter dem Symbol, innerhalb des Bildes.
		var hoehe: float = get_viewport_rect().size.y
		_karte.karte_oben = clampf(_knopf.position.y + RAND_KANTE + 14.0, 0.0, hoehe * 0.5)
		get_parent().add_child(_karte)
		_karte.zeige(info)
		_karte.verbinde(kern, saft, audio, func() -> void:
			if is_instance_valid(_karte):
				_karte.queue_free()
			pruefe())
		var baum: SceneTree = get_tree()
		if baum != null:
			_karte.biete_doppelt(baum.get_first_node_in_group(&"werbung") as AdService)

	func _process(delta: float) -> void:
		_takt -= delta
		if _takt <= 0.0:
			_takt = 1.5
			pruefe()
		if not visible:
			return
		_puls += delta
		var s: float = 1.0 + 0.06 * sin(_puls * 4.0)
		_knopf.pivot_offset = _knopf.size * 0.5
		_knopf.scale = Vector2(s, s)
		# Alle paar Sekunden ein kurzes Wackeln: "Hier wartet etwas."
		var phase: float = fmod(_puls, 3.6)
		_knopf.rotation = deg_to_rad(8.0 * sin(phase * 22.0) * maxf(0.0, 1.0 - phase / 0.6)) if phase < 0.6 else 0.0
