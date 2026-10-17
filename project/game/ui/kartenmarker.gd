## Was ueber der Karte schwebt: Raum-Plaketten, Stationsschilder und
## Kaufpfeile an Stationen, der Blitz am Engpass und die Tipp-Blasen.
##
## 2D-Elemente, jedes Bild an die Bildschirmposition eines Weltpunkts gesetzt.
## Als 3D-Label waeren sie beim Herauszoomen unlesbar klein und beim Heranzoomen
## riesig; ein Schild soll IMMER gleich gross und lesbar sein, egal wie weit man
## weg ist.
##
## Jedes antippbare Element hat eine unsichtbare Tippflaeche von mindestens
## `tippziel_min_px` (data/ui/hinweise.json, 96 logische px = 48 dp), auch wenn
## der sichtbare Aufkleber kleiner ist.
##
## K3 A2 -- Hinweis-Vokabular (docs/neu/K3_PLAN.md Abschnitt 1; A/B-Urteil 16.10.):
##   Ueberblick (Zoom > lod_grenze_zoom): nur Raum-Plaketten in der Raummitte.
##               Liegt der naechste Raum ausserhalb: ein Pfeil-Tab am Rand.
##   Im Raum:    Stationsschilder flach unter der Station, ohne Stiel; passt ein
##               Schild nicht ins freie Bild, faellt es weg statt zu wandern.
##               Jede Station mit bezahlbarem Ausbau: gruener Pfeil am Schild,
##               sonst grau mit Sparring; der EINE beste Kauf (GameCore.empfehlung)
##               gross und pulsend mit Preis, bei Ausstattung mit Werkzeug + Name.
## K4 P1.2/P1.3 -- Jede Raum-Plakette sagt genau EINE Sache, ueber Form und Farbe:
##   kaufbar  gruen, dunkler Kreis mit Pfeil      (jetzt etwas Lohnendes kaufbar)
##   fast     gelb, Fortschrittsring um den Pfeil (bald bezahlbar)
##   gesperrt grau, Schloss und Preis             (Raum noch zu)
##   bremst   rot, Warnzeichen                    (hier sitzt der Engpass)
##   ruhig    Papier, nur der Name                (nichts zu tun)
## Es pulsiert genau EIN Ziel: der naechste Raum, wenn er bezahlbar ist, sonst der
## Raum bzw. (im Raum) die Station des besten Kaufs. Alles andere steht still.
## K6 1c (Bastian 16.10., ersetzt den Sofortkauf aus f354b66): Ein Tipp auf eine
## Raum-Plakette -- gruen, gelb oder grau -- oeffnet DIREKT das Menue dieses Raums
## (Schnellkauf: oben die beste Verbesserung gross, darunter alle uebrigen mit Kaufknopf).
## Kein Langdruck mehr. Auf der Pille stehen Nutzen (+X €/s) und Preis.
## Der Kern rechnet (empfehlung(), empfehlung_im_raum(), bereich_info()), der Marker zeigt nur.
class_name Kartenmarker
extends Control

signal station_getippt(id: StringName)
signal bereich_getippt(id: StringName)
## Plakette im Ueberblick angetippt: Schnellkauf statt Raumfahrt (K4 P1.1).
signal bereich_schnellkauf(id: StringName)
## Das Schild klebt am Bildrand (der Raum liegt ausserhalb): ein Tipp fuehrt die
## Kamera hin und oeffnet nichts (RELEASE_PLAN 2.D, Paket A).
signal bereich_richtung(id: StringName)
signal moment_getippt(von: Vector2)
## Der Stapel ist abgeraeumt, der Schub laeuft (K3 B2).
signal stapel_getippt(station_id: StringName, schub_sekunden: float)
signal auftrag_getippt(von: Vector2)

const HINWEISE_PFAD: String = "res://data/ui/hinweise.json"
## Der Pseudo-Raum der Startzone (wie Menues.START_RAUM / GameCore.START_RAUM).
const START_RAUM: StringName = &"start"

## Hoehen ueber dem Weltpunkt, an denen die Zeichen schweben.
## Ueber dem Modell schwebt der Kaufchip, wenn kein Schild steht (Stern-Moment: Startpunkt).
const HOEHE_BADGE: float = 1.9
const HOEHE_BLASE: float = 3.0
const HOEHE_AUFTRAG: float = 3.2

var kern: GameCore
var kamera: Camera3D
var thema: ThemeData
var station_positionen: Dictionary = {}    ## StringName -> Vector3
var bereich_positionen: Dictionary = {}    ## StringName -> Vector3

var _schilder: Dictionary = {}     ## bereich_id -> Control (Tippflaeche der Raum-Plakette)
## Mindestabstand von Abzeichen, Schildern und Namen zum Bildrand (Safe Area).
const SEITENRAND: float = 14.0

var _badges: Dictionary = {}       ## station_id -> Control (Name, Stufe, Sterne)
var _pfeile: Dictionary = {}       ## station_id -> Control (Tippflaeche um PfeilZeichen)
var _kauf: Control                 ## EIN Kaufchip: der beste Kauf (GameCore.empfehlung)
var _kauf_preis: Label
var _kauf_name: Label
var _kauf_symbol: TextureRect
var _kauf_station: StringName = &""
var _tab: Control                  ## Pfeil-Tab am Rand
var _tab_bereich: StringName = &""
var _namen: Dictionary = {}        ## station_id -> Control
var _blase: TextureButton
var _auftrag: TextureButton
## Lieferkiste und Stapel (K3 B2): Aufkleber ueber dem Ort, Tippflaeche >= 96 px.
var _kiste: Control
var _kiste_bild: TextureRect
var _kiste_titel: Label
var _stapel: Control
var _stapel_ring: StapelRing
var _zeit: float = 0.0
## Oberkante des offenen Sheets (-1 = keins).
var sheet_oben: float = -1.0
## Waehrend des Tutorials zeigt dessen Pfeil auf das Ziel -- Pfeile und Blitz
## stuenden genau dort und verdeckten ihn.
var tutorial_aktiv: bool = false
## Der gezeigte beste Kauf (Form von GameCore.empfehlung()) und seit wann er steht.
## Neu gerechnet bei money_changed, hoechstens alle `empfehlung_takt_s`; ein anderer
## Kauf loest ihn erst nach `pfeil_haltezeit_s` ab (der Pfeil springt sonst staendig).
var _empfehlung: Dictionary = {}
var _empfehlung_seit: float = 0.0
var _empfehlung_rest: float = 0.0
var _empfehlung_alt: bool = true
## Je gekauftem Raum der beste Kauf (GameCore.empfehlung_im_raum), im Takt der Empfehlung.
var _raum_kauf: Dictionary = {}
## Station -> Raum (Bereich oder START_RAUM), beim Aufbau gefuellt.
var _raum_der_station: Dictionary = {}
## Der EINE Raum, dessen Plakette pulsiert, und ob das Ziel der Raumkauf selbst ist
## (dann pulsiert im Raum auch nicht der Kaufchip, sondern Plakette bzw. Rand-Tab).
var _ziel_raum: StringName = &""
var _ziel_ist_raum: bool = false
## Unterkante der oberen Bedienung (Kopfleiste, Zielleiste). Die Hud setzt sie.
var oben_frei: float = 270.0

var _h: Dictionary = {}
## Tippflaechen mit Langdruck: [TippErkenner, Control, Callable] -- je Bild abgefragt.
var _langdruecker: Array = []

static var _hinweise_cache: Dictionary = {}


## Die Werte aus data/ui/hinweise.json (einmal gelesen). Fehlt die Datei, laut.
static func hinweise() -> Dictionary:
	if not _hinweise_cache.is_empty():
		return _hinweise_cache
	if not FileAccess.file_exists(HINWEISE_PFAD):
		push_warning("Hinweis-Daten fehlen: %s" % HINWEISE_PFAD)
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(HINWEISE_PFAD))
	if roh is Dictionary:
		_hinweise_cache = roh as Dictionary
	else:
		push_warning("Hinweis-Daten unlesbar: %s" % HINWEISE_PFAD)
	return _hinweise_cache


static func hinweis(schluessel: String) -> float:
	return float(hinweise().get(schluessel, 0.0))


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_h = hinweise()


func _tippziel() -> float:
	return maxf(float(_h.get("tippziel_min_px", 0.0)), UiStil.TIPPZIEL)


func aufbauen(k: GameCore, cam: Camera3D, stationen: Dictionary, bereiche: Dictionary) -> void:
	kern = k
	kamera = cam
	station_positionen = stationen
	bereich_positionen = bereiche
	for kind in get_children():
		kind.queue_free()
	_schilder.clear()
	_langdruecker.clear()
	_badges.clear()
	_pfeile.clear()
	_kauf = null
	_kauf_station = &""
	_empfehlung = {}
	_empfehlung_alt = true
	_empfehlung_rest = 0.0
	_namen.clear()
	if kern != null and kern.bus != null and not kern.bus.money_changed.is_connected(_auf_geld):
		kern.bus.money_changed.connect(_auf_geld)

	# Namen zuerst: Sie liegen unter allem anderen.
	for id in station_positionen.keys():
		var name_feld := _baue_name(id)
		add_child(name_feld)
		_namen[id] = name_feld

	_raum_der_station.clear()
	_raum_kauf.clear()
	_ziel_raum = &""
	_ziel_ist_raum = false
	for bereich_id in _plaketten_raeume():
		var plakette := _baue_plakette(bereich_id)
		plakette.name = "Plakette_%s" % String(bereich_id)
		add_child(plakette)
		_schilder[bereich_id] = plakette
		for sid in Menues.stationen_des_raums(kern, bereich_id):
			_raum_der_station[sid] = bereich_id
	_tab = _baue_tab()
	_tab.name = "Randtab"
	add_child(_tab)

	for id in station_positionen.keys():
		var badge := _baue_badge(id)
		badge.name = "Schild_%s" % String(id)
		add_child(badge)
		_badges[id] = badge
		var pfeil := _baue_pfeil(id)
		pfeil.name = "Pfeil_%s" % String(id)
		add_child(pfeil)
		_pfeile[id] = pfeil
	_kauf = _baue_kaufchip()
	_kauf.name = "Kaufchip"
	add_child(_kauf)

	_blase = _baue_blase("herz", 110.0)
	_blase.name = "Blase"
	_tippbar(_blase, func() -> void:
		moment_getippt.emit(_blase.get_global_rect().get_center()))
	_baue_kiste()
	_baue_stapel()
	_auftrag = _baue_blase("geschenk", 104.0)
	_auftrag.name = "Auftrag"
	_tippbar(_auftrag, func() -> void:
		auftrag_getippt.emit(_auftrag.get_global_rect().get_center()))


## Raeume mit Plakette: die Startzone und jeder Bereich, dessen Lage bekannt ist.
func _plaketten_raeume() -> Array[StringName]:
	var liste: Array[StringName] = []
	if bereich_positionen.has(START_RAUM):
		liste.append(START_RAUM)
	for bereich_id in kern.bereiche.ids():
		if bereich_positionen.has(bereich_id):
			liste.append(bereich_id)
	return liste


func _auf_geld(_neu: float, _differenz: float) -> void:
	_empfehlung_alt = true


func _baue_blase(symbol: String, kante: float) -> TextureButton:
	var b := TextureButton.new()
	b.texture_normal = UiStil.symbol(symbol)
	b.ignore_texture_size = true
	b.stretch_mode = TextureButton.STRETCH_KEEP_ASPECT_CENTERED
	b.custom_minimum_size = Vector2(kante, kante)
	b.size = b.custom_minimum_size
	b.visible = false
	add_child(b)
	return b


## Eine unsichtbare Tippflaeche um einen sichtbaren Aufkleber.
func _tippflaeche(inhalt: Control, aktion: Callable, lang: Callable = Callable()) -> MarginContainer:
	var flaeche := MarginContainer.new()
	for seite in ["margin_left", "margin_right", "margin_top", "margin_bottom"]:
		flaeche.add_theme_constant_override(seite, UiStil.A2)
	flaeche.custom_minimum_size = Vector2(_tippziel(), _tippziel())
	flaeche.mouse_filter = Control.MOUSE_FILTER_STOP
	inhalt.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	inhalt.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	inhalt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	flaeche.add_child(inhalt)
	var lang_mit_druck: Callable = Callable()
	if lang.is_valid():
		lang_mit_druck = func() -> void:
			UiStil.eindruecken(inhalt)
			lang.call()
	_tippbar(flaeche, func() -> void:
		UiStil.eindruecken(inhalt)
		aktion.call(), lang_mit_druck)
	flaeche.visible = false
	return flaeche


## Ein Tipp auf `feld` (Druck + Loslassen innerhalb der Tippschwelle, Maus ODER
## Touch, genau einmal) ruft `aktion` -- fuer jede Tippflaeche der Karte gleich.
## Frueher zaehlte nur das Maus-Loslassen; das kam nicht an, wenn das Feld
## zwischendurch kurz unsichtbar war (Godot nimmt ihm dann den Maus-Fokus).
## `lang` (optional): Langdruck statt Tipp (abgefragt in _pruefe_langdruecke).
func _tippbar(feld: Control, aktion: Callable, lang: Callable = Callable()) -> void:
	var erkenner := TippErkenner.new()
	if lang.is_valid():
		_langdruecker.append([erkenner, feld, lang])
	feld.gui_input.connect(func(e: InputEvent) -> void:
		var nach_bild: Transform2D = feld.get_global_transform() if feld.is_inside_tree() else Transform2D.IDENTITY
		if erkenner.auswerten(e, nach_bild):
			print("tipp: marker %s" % String(feld.name))
			aktion.call())


## Die Raum-Plakette: links das Zustandszeichen (Kreis), rechts Name und EIN Wert.
## Im Ueberblick oeffnet ein Tipp den Schnellkauf, sonst das Raum-Panel.
func _baue_plakette(bereich_id: StringName) -> MarginContainer:
	var schild := PanelContainer.new()
	schild.name = "Schild"
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	schild.add_child(zeile)
	var zeichen := PlakettenZeichen.new()
	zeichen.name = "Zeichen"
	var kante: float = hinweis("plakette_zeichen_px")
	zeichen.custom_minimum_size = Vector2(kante, kante)
	zeichen.ring = hinweis("pfeil_ring_px")
	zeichen.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(zeichen)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", -4)
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(spalte)
	var name_label := UiStil.label(_raum_name(bereich_id), UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	name_label.name = "Name"
	name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(name_label)
	# K6 §4.3: Nutzen und Preis auf der Pille ("+3,2 €/s  1.282").
	var wert_zeile := HBoxContainer.new()
	wert_zeile.add_theme_constant_override("separation", UiStil.A2)
	wert_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(wert_zeile)
	var nutzen := UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	nutzen.name = "Nutzen"
	nutzen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	nutzen.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	nutzen.visible = false
	wert_zeile.add_child(nutzen)
	var wert := UiStil.label("", UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT)
	wert.name = "Wert"
	wert.mouse_filter = Control.MOUSE_FILTER_IGNORE
	wert_zeile.add_child(wert)
	return _tippflaeche(schild, func() -> void: plakette_getippt(bereich_id))


## Tipp auf eine Plakette (K6 1c): immer das Raum-Menue (Schnellkauf mit Liste), egal welcher
## Zustand und welche Zoomstufe -- man soll nicht erst suchen muessen. Gekauft wird im Menue.
func plakette_getippt(bereich_id: StringName) -> void:
	print("tipp: plakette %s -> sheet" % bereich_id)
	bereich_schnellkauf.emit(bereich_id)


## Langdruecke je Bild abfragen; ein unsichtbares Feld verliert seinen Druck.
func _pruefe_langdruecke() -> void:
	for eintrag in _langdruecker:
		var erkenner: TippErkenner = eintrag[0] as TippErkenner
		var feld: Control = eintrag[1] as Control
		if not is_instance_valid(feld) or not feld.is_visible_in_tree():
			erkenner.abbrechen()
			continue
		if erkenner.pruefe_langdruck():
			(eintrag[2] as Callable).call()


func _raum_name(bereich_id: StringName) -> String:
	var name: String = WeltTexte.bereich(thema, bereich_id, "name")
	if name.is_empty():
		name = WeltTexte.kette(thema, "start" if bereich_id == START_RAUM else String(bereich_id))
	if name.is_empty() and thema != null:
		name = thema.welt_name
	return name


## Der Pfeil-Tab am Bildrand: der naechste kaufbare Raum liegt ausserhalb.
func _baue_tab() -> MarginContainer:
	var schild := PanelContainer.new()
	schild.name = "Schild"
	var s := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A1))
	s.content_margin_left = float(UiStil.A2)
	s.content_margin_right = float(UiStil.A2)
	schild.add_theme_stylebox_override("panel", s)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", 0)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	schild.add_child(spalte)
	# Container setzen die Drehung ihrer Kinder zurueck -- der Pfeil dreht sich
	# deshalb in einem schlichten Halter.
	var kante: float = hinweis("tab_symbol_px")
	var halter := Control.new()
	halter.custom_minimum_size = Vector2(kante, kante)
	halter.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	halter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(halter)
	var pfeil := UiStil.symbolbild("kaufpfeil", kante)
	pfeil.name = "Symbol"
	pfeil.size = Vector2(kante, kante)
	pfeil.pivot_offset = Vector2(kante, kante) * 0.5
	halter.add_child(pfeil)
	var preis := UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	preis.name = "Preis"
	preis.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	spalte.add_child(preis)
	return _tippflaeche(schild, func() -> void:
		if _tab_bereich != &"":
			bereich_richtung.emit(_tab_bereich))


## Der Name einer Station als kleiner Papier-Aufkleber (heute im Abzeichen; bleibt aus).
func _baue_name(station_id: StringName) -> MarginContainer:
	var chip := PanelContainer.new()
	chip.name = "Chip"
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.PAPIER, float(UiStil.A3), 2.0, 2.0))
	var l := UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE, UiStil.FETT)
	l.name = "Name"
	chip.add_child(l)
	return _tippflaeche(chip, func() -> void: station_getippt.emit(station_id))


## Das Stationsschild: Name, "Lv 17", darunter Sterne. Engpass: roter Blitz links
## und roter Rand. Antippen oeffnet das Menue der Station.
func _baue_badge(station_id: StringName) -> MarginContainer:
	var chip := PanelContainer.new()
	chip.name = "Chip"
	var aussen := HBoxContainer.new()
	aussen.add_theme_constant_override("separation", UiStil.A1)
	aussen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(aussen)
	var blitz := _blitz_zeichen()
	blitz.name = "Blitz"
	blitz.visible = false
	aussen.add_child(blitz)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", 0)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	aussen.add_child(spalte)
	var name_zeile := UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	name_zeile.name = "StationsName"
	name_zeile.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(name_zeile)
	var zeile := HBoxContainer.new()
	zeile.alignment = BoxContainer.ALIGNMENT_CENTER
	zeile.add_theme_constant_override("separation", UiStil.A1)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(zeile)
	var l := UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	l.name = "Stufe"
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zeile.add_child(l)
	var sterne := CenterContainer.new()
	sterne.name = "Sterne"
	sterne.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(sterne)
	return _tippflaeche(chip, func() -> void: station_getippt.emit(station_id))


## Roter Kreis mit Blitz: "diese Station bremst".
func _blitz_zeichen() -> PanelContainer:
	var kreis := PanelContainer.new()
	var s := UiStil.chip(UiStil.WARNUNG, 2.0, 2.0, 0.0)
	kreis.add_theme_stylebox_override("panel", s)
	kreis.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	kreis.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kreis.add_child(UiStil.symbolbild("blitz", 30.0))
	return kreis


## Der Kaufpfeil an einem Stationsschild: gruen oder grau mit Sparring.
func _baue_pfeil(station_id: StringName) -> MarginContainer:
	var zeichen := PfeilZeichen.new()
	zeichen.name = "Pfeil"
	var kante: float = hinweis("pfeil_kante_px")
	zeichen.custom_minimum_size = Vector2(kante, kante)
	zeichen.ring = hinweis("pfeil_ring_px")
	var feld := _tippflaeche(zeichen, func() -> void: station_getippt.emit(station_id))
	return feld


## Der Kaufchip: Limette, Symbol (Pfeil oder Werkzeug), bei Ausstattung der Name,
## dann der Preis -- derselbe Preis wie im Menue (GameCore.empfehlung()).
func _baue_kaufchip() -> MarginContainer:
	var chip := PanelContainer.new()
	chip.name = "Chip"
	var s: StickerBox = UiStil.sticker(UiStil.KAUFEN, UiStil.RADIUS_CHIP, UiStil.KONTUR_CHIP, 0.0,
		UiStil.SCHATTEN_Y_MARKER)
	s.flaeche.set_border_width_all(UiStil.KONTUR)
	s.content_margin_left = float(UiStil.A1)
	s.content_margin_right = float(UiStil.A3)
	s.content_margin_top = float(UiStil.A1)
	s.content_margin_bottom = float(UiStil.A1)
	chip.add_theme_stylebox_override("panel", s)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A1)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(zeile)
	_kauf_symbol = UiStil.symbolbild("kaufpfeil", hinweis("kaufchip_symbol_px"))
	_kauf_symbol.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(_kauf_symbol)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", -6)
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(spalte)
	_kauf_name = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	_kauf_name.visible = false
	spalte.add_child(_kauf_name)
	_kauf_preis = UiStil.label("", UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT)
	_kauf_preis.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	spalte.add_child(_kauf_preis)
	return _tippflaeche(chip, func() -> void:
		if _kauf_station != &"":
			station_getippt.emit(_kauf_station))


# --- Empfehlung (der EINE beste Kauf) --------------------------------------------

## Welche Empfehlung steht als Naechstes? Rein, damit testbar.
## `alt`: bisher gezeigt, `alt_preis_jetzt`: dessen heutiger Preis (nach einem Kauf
## steigt er), `gehalten_s`: wie lange `alt` schon steht.
## Ein anderer Kauf loest den alten erst nach `haltezeit` ab -- ausser der alte ist
## nicht mehr bezahlbar oder es gibt gar keinen mehr.
static func waehle_empfehlung(alt: Dictionary, neu: Dictionary, alt_preis_jetzt: float,
		kapital: float, gehalten_s: float, haltezeit: float) -> Dictionary:
	if neu.is_empty() or alt.is_empty():
		return neu
	if _gleicher_kauf(alt, neu):
		return neu
	if alt_preis_jetzt <= 0.0 or kapital < alt_preis_jetzt or gehalten_s >= haltezeit:
		return neu
	var gehalten: Dictionary = alt.duplicate()
	gehalten["preis"] = alt_preis_jetzt
	return gehalten


static func _gleicher_kauf(a: Dictionary, b: Dictionary) -> bool:
	return String(a.get("art", "")) == String(b.get("art", "")) \
		and StringName(String(a.get("station", ""))) == StringName(String(b.get("station", ""))) \
		and StringName(String(a.get("platz", ""))) == StringName(String(b.get("platz", "")))


## Der heutige Preis eines Kaufs aus empfehlung() (0 = gibt es nicht mehr).
static func preis_jetzt(k: GameCore, kauf: Dictionary) -> float:
	var sid: StringName = StringName(String(kauf.get("station", "")))
	var s: StationModel = k.kette.station(sid)
	if s == null or not s.freigeschaltet:
		return 0.0
	match String(kauf.get("art", "")):
		"stufe":
			return s.naechste_kosten() if s.kann_ausbauen() else 0.0
		"platz":
			var pid: StringName = StringName(String(kauf.get("platz", "")))
			for p in s.ausstattung:
				if p.id == pid:
					return 0.0 if p.ist_max() else p.naechste_kosten()
			return 0.0
		"crew":
			return k.crew.kosten_naechster(sid) if not k.crew.ist_max(sid) else 0.0
	return 0.0


## Zustand des Pfeils einer Station: &"bester" (Ausbau ist der beste Kauf),
## &"werkzeug" (Ausstattung/Crew dieser Station ist der beste Kauf), &"gruen"
## (Ausbau bezahlbar), &"grau" (Ausbau moeglich, noch zu teuer), &"" (nichts).
static func pfeil_zustand(k: GameCore, station_id: StringName, empfehlung: Dictionary) -> StringName:
	var s: StationModel = k.kette.station(station_id)
	if s == null or not s.freigeschaltet:
		return &""
	# K7: Wird auf einen nahen Raum gespart, leuchtet kein Ausbau gruen.
	if k.sparziel() != &"":
		return &"grau" if s.kann_ausbauen() else &""
	if not empfehlung.is_empty() and StringName(String(empfehlung.get("station", ""))) == station_id:
		return &"bester" if String(empfehlung.get("art", "")) == "stufe" else &"werkzeug"
	if not s.kann_ausbauen():
		return &""
	return &"gruen" if k.kapital >= s.naechste_kosten() else &"grau"


## Sparstand des Ausbaus einer Station, 0..1 (Ring am grauen Pfeil).
static func pfeil_anteil(k: GameCore, station_id: StringName) -> float:
	var s: StationModel = k.kette.station(station_id)
	if s == null or not s.kann_ausbauen():
		return 0.0
	return clampf(k.kapital / maxf(s.naechste_kosten(), 1.0e-9), 0.0, 1.0)


## Empfehlung neu rechnen (bei money_changed, gedrosselt) und die Hysterese anwenden.
func aktualisiere_empfehlung(delta: float = 0.0, erzwingen: bool = false) -> void:
	_empfehlung_seit += delta
	_empfehlung_rest -= delta
	if not erzwingen and (not _empfehlung_alt or _empfehlung_rest > 0.0):
		return
	_empfehlung_alt = false
	_empfehlung_rest = hinweis("empfehlung_takt_s")
	var neu: Dictionary = kern.empfehlung()
	# Nur Stationen, die auf der Karte stehen, koennen einen Pfeil tragen.
	if not neu.is_empty() and not station_positionen.has(StringName(String(neu.get("station", "")))):
		neu = {}
	var gewaehlt_neu: Dictionary = waehle_empfehlung(_empfehlung, neu, preis_jetzt(kern, _empfehlung) if not _empfehlung.is_empty() else 0.0,
		kern.kapital, _empfehlung_seit, hinweis("pfeil_haltezeit_s"))
	if not _gleicher_kauf(gewaehlt_neu, _empfehlung) or gewaehlt_neu.is_empty() != _empfehlung.is_empty():
		_empfehlung_seit = 0.0
	_empfehlung = gewaehlt_neu
	_aktualisiere_raeume()


## Je gekauftem Raum der beste Kauf und das EINE Ziel, das pulsiert (K4 P1.3).
func _aktualisiere_raeume() -> void:
	_raum_kauf.clear()
	for bereich_id in _schilder.keys():
		if bereich_id == START_RAUM or kern.bereiche.ist_gekauft(bereich_id):
			_raum_kauf[bereich_id] = kern.empfehlung_im_raum(bereich_id)
	var naechster: StringName = _naechster_bereich()
	var naechster_preis: float = kern.bereiche.kosten(naechster) if naechster != &"" else INF
	var station: StringName = StringName(String(_empfehlung.get("station", "")))
	_ziel_raum = ziel_raum(naechster, kern.kapital >= naechster_preis,
		_raum_der_station.get(station, &"") as StringName)
	_ziel_ist_raum = _ziel_raum != &"" and _ziel_raum == naechster and kern.kapital >= naechster_preis


## Welcher Raum pulsiert? Rein, damit testbar. Ein bezahlbarer neuer Raum ist der
## groessere Schritt und geht vor; sonst der Raum des besten Kaufs; sonst keiner.
static func ziel_raum(naechster: StringName, naechster_bezahlbar: bool, raum_der_empfehlung: StringName) -> StringName:
	if naechster != &"" and naechster_bezahlbar:
		return naechster
	return raum_der_empfehlung


## Zustand einer Raum-Plakette (K4 P1.2), rein und testbar. `info` aus
## GameCore.bereich_info, `bester` aus empfehlung_im_raum (nur gekaufte Raeume),
## `bremst`: der Engpass steht in diesem Raum. Ergebnis {zustand, preis, anteil}.
static func plaketten_zustand(info: Dictionary, bester: Dictionary, kapital: float,
		bremst: bool, fast_ab: float) -> Dictionary:
	if info.is_empty():
		return {"zustand": &"ruhig", "preis": 0.0, "anteil": 0.0}
	if not bool(info.get("gekauft", false)):
		var kosten: float = float(info.get("kosten", 0.0))
		var anteil_raum: float = clampf(kapital / maxf(kosten, 1.0e-9), 0.0, 1.0)
		var z: StringName = &"gesperrt"
		if bool(info.get("verfuegbar", false)):
			if kapital >= kosten:
				z = &"kaufbar"
			elif anteil_raum >= fast_ab:
				z = &"fast"
		return {"zustand": z, "preis": kosten, "anteil": anteil_raum}
	if bester.is_empty():
		return {"zustand": &"bremst" if bremst else &"ruhig", "preis": 0.0, "anteil": 1.0}
	var preis: float = float(bester.get("preis", 0.0))
	var anteil: float = clampf(kapital / maxf(preis, 1.0e-9), 0.0, 1.0)
	var zustand: StringName = &"ruhig"
	if kapital >= preis:
		zustand = &"kaufbar"
	elif bremst:
		zustand = &"bremst"
	elif anteil >= fast_ab:
		zustand = &"fast"
	return {"zustand": zustand, "preis": preis, "anteil": anteil}


## Der Zustand, den die Plakette dieses Raums gerade zeigt (fuer Tests und Vorschau).
func plakette_von(bereich_id: StringName) -> StringName:
	var flaeche: Control = _schilder.get(bereich_id) as Control
	return StringName(String(flaeche.get_meta("zustand", ""))) if flaeche != null else &""


## Der Raum, der gerade pulsiert.
func ziel() -> StringName:
	return _ziel_raum


## Die Station, deren Ring in der Welt pulsieren darf: die des besten Kaufs -- ausser
## das Ziel ist gerade ein Raumkauf, im Ueberblick (dort pulsiert die Plakette) oder
## waehrend des Tutorials. Sonst keine.
func puls_station() -> StringName:
	if tutorial_aktiv or _ziel_ist_raum or kamera == null or ist_ueberblick():
		return &""
	return StringName(String(_empfehlung.get("station", "")))


## Die gezeigte Empfehlung (fuer Tests und das Tutorial).
func empfehlung() -> Dictionary:
	return _empfehlung


## Text des Kaufchips: Preis; bei Ausstattung zusaetzlich deren Name.
func _fuelle_kaufchip() -> void:
	var art: String = String(_empfehlung.get("art", ""))
	_kauf_preis.text = UiStil.preis(float(_empfehlung.get("preis", 0.0)))
	var name_text: String = ""
	if art == "platz":
		var sid: StringName = StringName(String(_empfehlung.get("station", "")))
		name_text = WeltTexte.platz_name(thema, sid, StringName(String(_empfehlung.get("platz", ""))))
	elif art == "crew":
		name_text = UiText.t("crew_anheuern")
	_kauf_name.text = name_text
	_kauf_name.visible = not name_text.is_empty()
	_kauf_symbol.texture = UiStil.symbol("kaufpfeil" if art == "stufe" or art.is_empty() else "werkzeug")


# --- Jedes Bild -------------------------------------------------------------------

func _zoom() -> float:
	return kamera.size if kamera != null else 0.0


## Ueberblick: weit herausgezoomt -- nur Raum-Plaketten.
func ist_ueberblick() -> bool:
	return _zoom() > hinweis("lod_grenze_zoom")


## Unterkante der freien Karte: Sheet-Oberkante oder Menueleiste.
func _unten_frei() -> float:
	var unten: float = get_viewport_rect().size.y - Menueleiste.HOEHE
	if sheet_oben >= 0.0:
		unten = minf(unten, sheet_oben)
	return unten


## Liegt ein Rechteck ganz im freien Bild (unter den Leisten, ueber Menue/Sheet)?
func _ganz_frei(r: Rect2) -> bool:
	var breite: float = get_viewport_rect().size.x
	return r.position.y >= oben_frei and r.end.y <= _unten_frei() \
		and r.position.x >= 0.0 and r.end.x <= breite


func _process(delta: float) -> void:
	if kern == null or kamera == null or not is_instance_valid(kamera):
		return
	_zeit += delta
	var wippen: float = sin(_zeit * 3.0) * 6.0
	aktualisiere_empfehlung(delta)
	_pruefe_langdruecke()

	_zeige_plaketten()

	var engpass: StringName = kern.kette.bottleneck()
	var ueberblick: bool = ist_ueberblick()
	# Sichtbarkeit je Feld GENAU EINMAL je Bild setzen: Ein Feld, das kurz auf
	# unsichtbar und gleich wieder auf sichtbar springt, verliert in Godot den
	# Maus-Fokus -- das Loslassen eines Tipps kam dann nie an (Fehler K6-1).
	var kauf_zeigen: bool = false
	_kauf_station = &""
	var beste: StringName = StringName(String(_empfehlung.get("station", ""))) if not tutorial_aktiv else &""
	if beste != &"":
		_fuelle_kaufchip()
	for id in _badges.keys():
		var station: StationModel = kern.kette.station(id)
		var aktiv: bool = station != null and station.freigeschaltet
		var badge: Control = _badges[id]
		var pfeil: Control = _pfeile.get(id) as Control
		var pfeil_zeigen: bool = false
		badge.visible = aktiv and not ueberblick and _setze_schild(badge, id)
		if badge.visible:
			_aktualisiere_badge(badge, station, id == engpass and not tutorial_aktiv, id)
		# Der beste Kauf: der Chip (im Ueberblick sagt das die Plakette). Sonst der
		# kleine Pfeil am Schild.
		if aktiv and id == beste and not ueberblick:
			kauf_zeigen = _setze_kaufchip(badge, id, wippen)
		elif pfeil != null and badge.visible and not tutorial_aktiv:
			pfeil_zeigen = _setze_pfeil(pfeil, badge, id)
		if pfeil != null:
			pfeil.visible = pfeil_zeigen
		# Der Name steht im Abzeichen; der alte Namenschip bleibt aus.
		(_namen[id] as Control).visible = false
	_kauf.visible = kauf_zeigen

	_zeige_kiste()
	_zeige_stapel()
	if kern.momente.laeuft() and kern.momente.art == MomentSystem.ART_BLASE \
			and station_positionen.has(kern.momente.station):
		# Ein grosser Moment sieht anders aus: groesser, ein Geschenk statt eines Herzens.
		var gross: bool = kern.momente.gross
		_blase.texture_normal = UiStil.symbol("geschenk" if gross else "herz")
		_blase.size = Vector2(150.0, 150.0) if gross else Vector2(110.0, 110.0)
		_blase.visible = _setze(_blase, station_positionen[kern.momente.station] as Vector3 + Vector3(0, HOEHE_BLASE, 0), wippen * 1.5)
		_blase.pivot_offset = _blase.size * 0.5
		var s: float = 1.0 + 0.07 * sin(_zeit * 6.0)
		_blase.scale = Vector2(s, s)
		# Die letzten fuenf Sekunden wird die Blase durchsichtiger -- ohne Zahl,
		# ohne Warnung. Sie geht, wie sie gekommen ist.
		_blase.modulate.a = clampf(kern.momente.rest / 5.0, 0.35, 1.0)
	else:
		_blase.visible = false

	var sonder: StringName = Ids.STATION_SPECIAL
	var wartet_auftrag: bool = kern.auftraege.wartend > 0 and station_positionen.has(sonder) \
		and kern.kette.station(sonder) != null and kern.kette.station(sonder).freigeschaltet
	_auftrag.visible = wartet_auftrag and _setze(_auftrag, station_positionen[sonder] as Vector3 + Vector3(0, HOEHE_AUFTRAG, 0), wippen)
	_entzerre()


## Das Schild liegt flach unter der Station (Plattenvorderkante), ohne Stiel.
## Passt es dort nicht ganz ins freie Bild, faellt es weg -- ein verschobenes
## Schild zeigte auf die falsche Station.
func _setze_schild(badge: Control, id: StringName) -> bool:
	var pos: Vector3 = station_positionen[id] as Vector3
	if kamera.is_position_behind(pos):
		return false
	var fuss: Vector2 = kamera.unproject_position(pos)
	var groesse: Vector2 = badge.size if badge.size != Vector2.ZERO else badge.get_combined_minimum_size()
	badge.position = fuss + Vector2(-groesse.x * 0.5, hinweis("schild_versatz_y_px") - groesse.y * 0.5)
	var sichtbar: Rect2 = _sichtbar(badge)
	return _ganz_frei(sichtbar)


## Das sichtbare Rechteck eines Elements (ohne den unsichtbaren Tipprand), in Bildpixeln.
func _sichtbar(feld: Control) -> Rect2:
	if feld.get_child_count() == 0:
		return Rect2(feld.position, feld.size)
	var inhalt: Control = feld.get_child(0) as Control
	if inhalt == null:
		return Rect2(feld.position, feld.size)
	return Rect2(feld.position + inhalt.position, inhalt.size)


## Der kleine Pfeil sitzt rechts oben am sichtbaren Schild.
func _setze_pfeil(pfeil: Control, badge: Control, id: StringName) -> bool:
	var zustand: StringName = pfeil_zustand(kern, id, _empfehlung)
	if zustand != &"gruen" and zustand != &"grau":
		return false
	var zeichen: PfeilZeichen = pfeil.get_child(0) as PfeilZeichen
	zeichen.gruen = zustand == &"gruen"
	zeichen.anteil = pfeil_anteil(kern, id)
	zeichen.queue_redraw()
	var ecke: Rect2 = _sichtbar(badge)
	_an_ecke(pfeil, Vector2(ecke.end.x, ecke.position.y), Vector2(0.3, 0.75))
	pfeil.scale = Vector2.ONE
	return true


## Legt den SICHTBAREN Inhalt eines Feldes so, dass sein Punkt `anteil` (0..1 je
## Achse) auf `punkt` liegt -- der Pfeil sitzt an der Schildecke, ohne den Namen
## zu verdecken; die Tippflaeche ringsum zaehlt nicht.
func _an_ecke(feld: Control, punkt: Vector2, anteil: Vector2) -> void:
	if feld.size == Vector2.ZERO:
		feld.size = feld.get_combined_minimum_size()
	var innen: Rect2 = _sichtbar(feld)
	var versatz: Vector2 = innen.position - feld.position
	feld.position = punkt - innen.size * anteil - versatz


## Der Kaufchip der besten Station sitzt an der Ecke des Schilds (statt des
## kleinen Pfeils). Steht kein Schild, schwebt er ueber der Station. Pulst und
## ist `bester_skala`-mal so gross wie ein Pfeil.
func _setze_kaufchip(badge: Control, id: StringName, wippen: float) -> bool:
	_kauf.reset_size()
	var groesse: Vector2 = _kauf.size
	if badge.visible:
		var ecke: Rect2 = _sichtbar(badge)
		_an_ecke(_kauf, Vector2(ecke.end.x, ecke.position.y), Vector2(0.2, 0.8))
	else:
		var welt: Vector3 = (station_positionen[id] as Vector3) + Vector3(0, HOEHE_BADGE, 0)
		if kamera.is_position_behind(welt):
			return false
		var ueber: Vector2 = kamera.unproject_position(welt)
		# Steht die Station nicht im Bild, zeigt kein Chip am Rand ins Leere.
		if ueber.x < 0.0 or ueber.x > get_viewport_rect().size.x:
			return false
		_kauf.position = ueber - groesse * 0.5
	_kauf.position.y += wippen * 0.3
	var breite: float = get_viewport_rect().size.x
	_kauf.position.x = clampf(_kauf.position.x, 0.0, maxf(0.0, breite - groesse.x))
	if not _ganz_frei(_sichtbar(_kauf)):
		return false
	_kauf_station = id
	_kauf.pivot_offset = groesse * 0.5
	var basis: float = hinweis("bester_skala")
	# Genau ein Puls (K4 P1.3): Ist der naechste Raum das Ziel, steht der Chip still.
	var puls: float = _puls() if not _ziel_ist_raum else 1.0
	_kauf.scale = Vector2(basis * puls, basis * puls)
	return true


## Skalierung des EINEN Pulses in diesem Bild.
func _puls() -> float:
	return 1.0 + (hinweis("puls_skala") - 1.0) * (0.5 + 0.5 * sin(_zeit * TAU * hinweis("puls_hz")))


## Raum-Plaketten in der Raummitte, nur wenn die Mitte im Bild ist.
## Im Ueberblick alle Raeume; im Raum nur gesperrte (gekaufte zeigen dort ihre
## Stationsschilder). Liegt der naechste kaufbare Raum ausserhalb: Pfeil-Tab.
func _zeige_plaketten() -> void:
	var ueberblick: bool = ist_ueberblick()
	var naechster: StringName = _naechster_bereich()
	var tab_zeigen: bool = false
	_tab_bereich = &""
	for bereich_id in _schilder.keys():
		var flaeche: Control = _schilder[bereich_id]
		var info: Dictionary = kern.bereich_info(bereich_id)
		var gekauft: bool = bool(info.get("gekauft", false))
		var mitte: Vector3 = bereich_positionen[bereich_id] as Vector3
		var im_bild: bool = false
		if not kamera.is_position_behind(mitte):
			var p: Vector2 = kamera.unproject_position(mitte)
			im_bild = p.x >= 0.0 and p.x <= get_viewport_rect().size.x and p.y >= oben_frei and p.y <= _unten_frei()
		var zeigen: bool = false
		if not im_bild:
			if bereich_id == naechster and not gekauft:
				tab_zeigen = _zeige_tab(bereich_id, info)
		elif ueberblick or not gekauft:
			_fuelle_plakette(flaeche, bereich_id, info)
			zeigen = _setze(flaeche, mitte, 0.0) and _ganz_frei(_sichtbar(flaeche))
		# Nur eine echte Aenderung setzen (siehe _process: Maus-Fokus).
		flaeche.visible = zeigen
	_tab.visible = tab_zeigen


func _fuelle_plakette(flaeche: Control, bereich_id: StringName, info: Dictionary) -> void:
	var schild: PanelContainer = flaeche.get_child(0) as PanelContainer
	var engpass: StringName = kern.kette.bottleneck()
	var bremst: bool = not tutorial_aktiv and engpass != &"" and _raum_der_station.get(engpass, &"") == bereich_id
	var z: Dictionary = plaketten_zustand(info, _raum_kauf.get(bereich_id, {}) as Dictionary, kern.kapital,
		bremst, hinweis("plakette_fast_ab_anteil"))
	# K7 Sparen: Liegt ein naher Raum im Sparfenster, ist ER das Ziel (zeigt den Sparstand),
	# gekaufte Raeume leuchten dann nicht gruen.
	var sparziel: StringName = kern.sparziel()
	if sparziel != &"":
		if bereich_id == sparziel:
			if z["zustand"] != &"kaufbar":
				z["zustand"] = &"fast"
		elif bool(info.get("gekauft", false)) and z["zustand"] == &"kaufbar":
			z["zustand"] = &"ruhig"
	var zustand: StringName = z["zustand"] as StringName
	var anteil: float = float(z["anteil"])
	var zeichen: PlakettenZeichen = schild.find_child("Zeichen", true, false) as PlakettenZeichen
	if zeichen.zustand != zustand or not is_equal_approx(zeichen.anteil, anteil):
		zeichen.zustand = zustand
		zeichen.anteil = anteil
		zeichen.queue_redraw()
	zeichen.visible = zustand != &"ruhig"
	var wert: Label = schild.find_child("Wert", true, false) as Label
	var nutzen: Label = schild.find_child("Nutzen", true, false) as Label
	var mehr: float = float((_raum_kauf.get(bereich_id, {}) as Dictionary).get("mehr", 0.0))
	var mit_nutzen: bool = bool(info.get("gekauft", false)) and mehr >= 0.05 \
		and zustand != &"bremst" and zustand != &"ruhig"
	nutzen.text = UiText.t("einnahmen_plus") % UiStil.zahl(mehr) if mit_nutzen else ""
	nutzen.visible = not nutzen.text.is_empty()
	match zustand:
		&"bremst":
			wert.text = UiText.t("engpass_kurz")
		&"ruhig":
			wert.text = ""
		_:
			wert.text = UiStil.preis(float(z["preis"]))
	wert.visible = not wert.text.is_empty()
	wert.add_theme_color_override("font_color", UiStil.TINTE_2 if zustand == &"gesperrt" else UiStil.TINTE)
	if flaeche.get_meta("zustand", "") != String(zustand):
		var war: String = String(flaeche.get_meta("zustand", ""))
		flaeche.set_meta("zustand", String(zustand))
		schild.add_theme_stylebox_override("panel", _schild_stil(UiStil.plaketten_farbe(zustand), zustand != &"ruhig"))
		if zustand == &"kaufbar" and not war.is_empty():
			UiStil.aufploppen(schild, 0.8)
	# Wichtigkeit fuer die Platzvergabe: Ziel > kaufbar > bremst > fast > gesperrt > ruhig.
	var prio: float = float({&"kaufbar": 5.0, &"bremst": 4.0, &"fast": 3.0, &"gesperrt": 1.0}.get(zustand, 0.0))
	flaeche.set_meta("prio", prio + anteil + (10.0 if bereich_id == _ziel_raum else 0.0))
	var aufbau: Array = [wert.text, zeichen.visible, nutzen.text]
	if flaeche.get_meta("aufbau", []) != aufbau:
		flaeche.set_meta("aufbau", aufbau)
		flaeche.reset_size()
	# Genau ein Puls (K4 P1.3): nur das Ziel; alle anderen Plaketten stehen still.
	schild.pivot_offset = schild.size * 0.5
	if bereich_id == _ziel_raum and not tutorial_aktiv:
		var p: float = _puls()
		schild.scale = Vector2(p, p)
	elif schild.scale != Vector2.ONE and not _ploppt(schild):
		schild.scale = Vector2.ONE


## P1.9 (K5): Das sichtbare Element zu einem Symbol -- Plakettenzustand (kaufbar, fast,
## gesperrt, bremst), Kiste oder Stapel -- als Anker fuer die einmalige Erklaer-Blase.
## null, wenn gerade keins ganz im freien Bild steht. Nur Anker, keine Logik.
func hinweis_anker(art: StringName) -> Control:
	var kandidaten: Array = []
	match art:
		&"kiste":
			kandidaten = [_kiste]
		&"stapel":
			kandidaten = [_stapel]
		_:
			for flaeche in _schilder.values():
				if String((flaeche as Control).get_meta("zustand", "")) == String(art):
					kandidaten.append(flaeche)
	for k in kandidaten:
		var c: Control = k as Control
		if c != null and c.is_visible_in_tree() and _ganz_frei(_sichtbar(c)):
			return c
	return null


## Sichtbares Rechteck eines Ankers (Bildschirmkoordinaten; der Marker fuellt das Bild).
func anker_rechteck(feld: Control) -> Rect2:
	return _sichtbar(feld)


## Laeuft gerade das Aufploppen (UiStil.aufploppen)? Dann nicht dazwischenfunken.
func _ploppt(schild: Control) -> bool:
	return schild.scale.x < 1.0 - 1.0e-3


## Pfeil-Tab am linken oder rechten Rand, auf der Hoehe des Raums (geklemmt).
func _zeige_tab(bereich_id: StringName, info: Dictionary) -> bool:
	var mitte: Vector3 = bereich_positionen[bereich_id] as Vector3
	var ziel: Vector2 = kamera.unproject_position(mitte)
	if kamera.is_position_behind(mitte):
		return false
	var flaeche: Vector2 = get_viewport_rect().size
	var schild: PanelContainer = _tab.get_child(0) as PanelContainer
	(schild.find_child("Preis", true, false) as Label).text = UiStil.preis(float(info.get("naechster_preis", 0.0)))
	_tab.reset_size()
	var groesse: Vector2 = _tab.size
	var links: bool = ziel.x < flaeche.x * 0.5
	var x: float = 0.0 if links else flaeche.x - groesse.x
	var y: float = clampf(ziel.y - groesse.y * 0.5, oben_frei, _unten_frei() - groesse.y)
	_tab.position = Vector2(x, y)
	if not _ganz_frei(_sichtbar(_tab)):
		return false
	var symbol_bild: TextureRect = schild.find_child("Symbol", true, false) as TextureRect
	symbol_bild.rotation = (ziel - _tab.position - groesse * 0.5).angle() + PI * 0.5
	_tab_bereich = bereich_id
	schild.pivot_offset = schild.size * 0.5
	var p: float = _puls() if bereich_id == _ziel_raum and not tutorial_aktiv else 1.0
	schild.scale = Vector2(p, p)
	return true


## Bildschirm-Kollisionsprufung: Abzeichen, Pfeile und Kaufchip haben Vorrang;
## ein Raumschild, das darauf liegt, weicht zur naechsten freien Stelle aus.
func _entzerre() -> void:
	var fest: Array[Rect2] = []
	for id in _badges.keys():
		var b: Control = _badges[id]
		if b.visible:
			fest.append(_sichtbar(b))
		var n: Control = _namen[id]
		if n.visible:
			fest.append(_sichtbar(n))
		var pf: Control = _pfeile.get(id) as Control
		if pf != null and pf.visible:
			fest.append(_sichtbar(pf))
	if _kauf.visible:
		fest.append(_sichtbar(_kauf))
	# Kiste und Stapel sind Momente: Plaketten weichen ihnen aus, nicht umgekehrt.
	for moment_feld in [_kiste, _stapel]:
		if moment_feld != null and (moment_feld as Control).visible:
			fest.append(_sichtbar(moment_feld as Control))
	if _tab != null and is_instance_valid(_tab) and _tab.visible:
		# Der Rand-Tab bleibt am Rand und weicht dem Kaufchip nur nach oben/unten aus.
		var tab_r: Rect2 = _sichtbar(_tab)
		if _kauf.visible and _kollidiert(tab_r, [_sichtbar(_kauf)] as Array[Rect2]):
			var chip_r: Rect2 = _sichtbar(_kauf)
			var unter: float = chip_r.end.y + 6.0
			var ueber: float = chip_r.position.y - tab_r.size.y - 6.0
			var ziel_y: float = unter if unter + tab_r.size.y <= _unten_frei() else ueber
			if ziel_y < oben_frei:
				_tab.visible = false
			else:
				_tab.position.y += ziel_y - tab_r.position.y
		if _tab.visible:
			fest.append(_sichtbar(_tab))
	var flaeche: Vector2 = get_viewport_rect().size
	var unten: float = _unten_frei() - float(UiStil.A3)
	var rand: float = float(UiStil.A2)
	var grenzen := Rect2(rand, oben_frei, flaeche.x - 2.0 * rand, maxf(unten - oben_frei, 0.0))
	var ids: Array[StringName] = []
	var wunsch: Array[Rect2] = []
	var prio: Array[float] = []
	var versaetze: Array[Vector2] = []
	for bereich_id in _schilder.keys():
		var s: Control = _schilder[bereich_id]
		if not s.visible:
			continue
		# Gerechnet wird mit dem sichtbaren Schild; die Tippflaeche darf ueberlappen.
		var innen: Rect2 = _sichtbar(s)
		# Ein pulsierendes Schild waechst um die Mitte -- sein Platz ist der vergroesserte.
		var inhalt: Control = s.get_child(0) as Control
		var wachs: float = maxf(inhalt.scale.x, 1.0) if inhalt != null else 1.0
		if wachs > 1.0:
			innen = innen.grow_individual(innen.size.x * (wachs - 1.0) * 0.5, innen.size.y * (wachs - 1.0) * 0.5,
				innen.size.x * (wachs - 1.0) * 0.5, innen.size.y * (wachs - 1.0) * 0.5)
		ids.append(bereich_id)
		wunsch.append(innen)
		prio.append(float(s.get_meta("prio", 0.0)))
		versaetze.append(innen.position - s.position)
	var maximal: int = int(hinweis("plaketten_max"))
	var plaetze: Array[Vector2] = platziere_schilder(wunsch, prio, fest, grenzen, maximal, true)
	for k in range(ids.size()):
		var s2: Control = _schilder[ids[k]]
		if not plaetze[k].is_finite():
			s2.visible = false
			continue
		s2.position = plaetze[k] - versaetze[k]


## Platzvergabe fuer Raum-Schilder in Bildschirmkoordinaten (rein, testbar). `wunsch` sind die
## Rechtecke an ihrem Wunschort, `prio` ihre Wichtigkeit (hoeher = zuerst), `fest` was nicht
## weichen darf. Ergebnis je Schild: linke obere Ecke, oder Vector2.INF = ausblenden.
## Hoechstens `maximal` Schilder bleiben; keines liegt auf einem anderen oder einem festen
## Rechteck. Mit `ausblenden` faellt ein Schild ohne freien Platz weg, sonst bleibt es stehen.
static func platziere_schilder(wunsch: Array[Rect2], prio: Array[float], fest: Array[Rect2],
		grenzen: Rect2, maximal: int, ausblenden: bool = true) -> Array[Vector2]:
	var ergebnis: Array[Vector2] = []
	ergebnis.resize(wunsch.size())
	var reihenfolge: Array[int] = []
	for k in range(wunsch.size()):
		reihenfolge.append(k)
		ergebnis[k] = Vector2.INF
	reihenfolge.sort_custom(func(a: int, b: int) -> bool:
		if not is_equal_approx(prio[a], prio[b]):
			return prio[a] > prio[b]
		return a < b)
	var belegt: Array[Rect2] = fest.duplicate()
	var gesetzt: int = 0
	for k in reihenfolge:
		if gesetzt >= maximal:
			break
		var r: Rect2 = wunsch[k]
		var ort: Vector2 = r.position
		if _kollidiert(r, belegt):
			var bester: Vector2 = Vector2.INF
			var bester_abstand: float = INF
			for h in belegt:
				var kandidaten: Array[Vector2] = [
					Vector2(r.position.x, h.end.y + 6.0),
					Vector2(r.position.x, h.position.y - r.size.y - 6.0),
					Vector2(h.end.x + 6.0, r.position.y),
					Vector2(h.position.x - r.size.x - 6.0, r.position.y),
				]
				for kand in kandidaten:
					if kand.y < grenzen.position.y or kand.y + r.size.y > grenzen.end.y 							or kand.x < grenzen.position.x or kand.x + r.size.x > grenzen.end.x:
						continue
					var d: float = kand.distance_to(r.position)
					if d < bester_abstand and not _kollidiert(Rect2(kand, r.size), belegt):
						bester_abstand = d
						bester = kand
			if not bester.is_finite():
				if ausblenden:
					continue
			else:
				ort = bester
		ergebnis[k] = ort
		belegt.append(Rect2(ort, r.size))
		gesetzt += 1
	return ergebnis


static func _kollidiert(r: Rect2, fest: Array[Rect2]) -> bool:
	for h in fest:
		if h.grow(4.0).intersects(r):
			return true
	return false


## Bildschirmrechtecke aller gerade sichtbaren Marker. Die Tutorial-Hand weicht ihnen aus.
func sichtbare_rechtecke() -> Array[Rect2]:
	var liste: Array[Rect2] = []
	var quellen: Array = []
	quellen.append_array(_schilder.values())
	quellen.append_array(_badges.values())
	quellen.append_array(_pfeile.values())
	quellen.append_array(_namen.values())
	quellen.append_array([_kauf, _blase, _auftrag, _tab, _kiste, _stapel])
	for q in quellen:
		var c: Control = q as Control
		if c != null and is_instance_valid(c) and c.is_visible_in_tree():
			liste.append(c.get_global_rect())
	return liste


## Alle Tippflaechen (fuer test_tippflaechen): Abzeichen, Pfeile, Plaketten, Chip, Tab.
func tippflaechen() -> Array[Control]:
	var liste: Array[Control] = []
	for q in _schilder.values() + _badges.values() + _pfeile.values() + [_kauf, _tab, _kiste, _stapel]:
		var c: Control = q as Control
		if c != null and is_instance_valid(c):
			liste.append(c)
	return liste


func _naechster_bereich() -> StringName:
	for bereich_id in kern.bereiche.ids():
		if kern.bereiche.verfuegbar(bereich_id):
			return bereich_id
	return &""


## Stufe, Sterne und Engpass am Abzeichen -- nur bei Aenderung neu gebaut.
## Sterne erst ab `sterne_ab_stufe`, Engpass als roter Blitz links.
func _aktualisiere_badge(badge: Control, station: StationModel, engpass: bool = false,
		station_id: StringName = &"") -> void:
	var name_text: String = WeltTexte.station_name(thema, station_id) if station_id != &"" else ""
	var zustand: Array = [station.stufe, station.sterne(), station.sterne_moeglich(), UiStil.akzent(), engpass, name_text]
	if badge.get_meta("zustand", []) == zustand:
		return
	badge.set_meta("zustand", zustand)
	var chip: PanelContainer = badge.get_child(0) as PanelContainer
	var st: StickerBox = UiStil.badge_box()
	st.content_margin_top = 2.0
	st.content_margin_bottom = 2.0
	if engpass:
		st.flaeche.border_color = UiStil.WARNUNG
		st.flaeche.set_border_width_all(UiStil.KONTUR + 2)
		st.content_margin_left = 2.0
	chip.add_theme_stylebox_override("panel", st)
	(chip.find_child("Blitz", true, false) as Control).visible = engpass
	var l: Label = chip.find_child("Stufe", true, false) as Label
	l.text = UiText.t("lv") % station.stufe if UiText.hat("lv") else str(station.stufe)
	l.add_theme_color_override("font_color", UiStil.text_auf(UiStil.akzent()))
	var n: Label = chip.find_child("StationsName", true, false) as Label
	n.text = name_text
	n.visible = not name_text.is_empty()
	n.add_theme_color_override("font_color", UiStil.text_auf(UiStil.akzent()))
	var sterne: CenterContainer = chip.find_child("Sterne", true, false) as CenterContainer
	for kind in sterne.get_children():
		kind.queue_free()
	var moeglich: int = mini(station.sterne_moeglich(), 5)
	var zeigen: bool = moeglich > 0 and station.stufe >= int(hinweis("sterne_ab_stufe"))
	sterne.visible = zeigen
	if zeigen:
		sterne.add_child(Sheet.sterne(mini(station.sterne(), moeglich), moeglich, 18.0))
	badge.reset_size()


## Setzt ein Element mittig ueber einen Weltpunkt. false, wenn der Punkt nicht
## im Bild ist -- dann bleibt das Element unsichtbar statt am Rand zu kleben.
func _setze(element: Control, welt: Vector3, versatz_y: float) -> bool:
	if kamera.is_position_behind(welt):
		return false
	var p: Vector2 = kamera.unproject_position(welt)
	var groesse: Vector2 = element.size
	if groesse == Vector2.ZERO:
		groesse = element.get_combined_minimum_size()
	element.position = p - groesse * 0.5 + Vector2(0.0, versatz_y)
	var flaeche: Vector2 = get_viewport_rect().size
	# Abzeichen und Schilder bleiben ganz im Bild ("v 10" am linken Rand war abgeschnitten).
	element.position.x = clampf(element.position.x, SEITENRAND, maxf(SEITENRAND, flaeche.x - groesse.x - SEITENRAND))
	return p.x > -80.0 and p.y > -80.0 and p.x < flaeche.x + 80.0 and p.y < flaeche.y + 80.0


func _schild_stil(farbe: Color, verfuegbar: bool) -> StyleBox:
	var s := UiStil.chip(farbe, float(UiStil.A3), float(UiStil.A1), UiStil.SCHATTEN_Y_MARKER if verfuegbar else 0.0)
	s.flaeche.set_border_width_all(UiStil.KONTUR)
	s.content_margin_left = float(UiStil.A2)
	s.content_margin_right = float(UiStil.A4)
	return s


# --- Lieferkiste und Stapel (K3 B2) ---------------------------------------------

## Groesse der Aufkleber in logischen px. Die Tippflaeche liegt darum herum und
## ist nie kleiner als das Tippziel (96).
const KISTE_KANTE: float = 132.0
const STAPEL_KANTE: float = 112.0
const HOEHE_KISTE: float = 1.7


## Die Kiste: Aufkleber, darunter ihr Titel aus der Themendatei (momente.kiste.titel).
## Ein Tipp geht denselben Weg wie jeder Moment (moment_getippt -> Hud -> Kern),
## damit Muenzflug und Meldung an einer Stelle bleiben.
func _baue_kiste() -> void:
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", 0)
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	_kiste_bild = UiStil.symbolbild("kiste", KISTE_KANTE)
	_kiste_bild.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	spalte.add_child(_kiste_bild)
	var chip := PanelContainer.new()
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.PAPIER, float(UiStil.A3), float(UiStil.A1)))
	chip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kiste_titel = Label.new()
	_kiste_titel.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_KLEIN))
	_kiste_titel.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
	_kiste_titel.add_theme_color_override("font_color", UiStil.TINTE)
	_kiste_titel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(_kiste_titel)
	spalte.add_child(chip)
	_kiste = _tippflaeche(spalte, func() -> void:
		moment_getippt.emit(_kiste_bild.get_global_rect().get_center()))
	_kiste.name = "Kiste"
	add_child(_kiste)


func _kisten_titel() -> String:
	if thema == null:
		return ""
	var k: Dictionary = thema.abschnitt("momente").get("kiste", {}) as Dictionary
	return String(k.get("titel", ""))


func _zeige_kiste() -> void:
	if not kern.momente.ist_kiste() or kern.welten == null:
		_kiste.visible = false
		return
	var titel: String = _kisten_titel()
	if _kiste_titel.text != titel:
		_kiste_titel.text = titel
	# K6 Welle 2: Die Kiste spricht fuer sich (huepft, wackelt) -- kein Textschild, das
	# ueber den Stationsnamen liegt (Handybefund 17.10.: "Ein Paket ..." auf "Idee").
	(_kiste_titel.get_parent() as Control).visible = false
	_kiste.size = _kiste.get_combined_minimum_size()
	var ort: Vector3 = Lieferkiste.ort(kern.welten, kern.welt_index)
	var hops: float = -absf(sin(_zeit * 4.0)) * 10.0
	_kiste.visible = _setze(_kiste, ort + Vector3(0.0, HOEHE_KISTE, 0.0), hops)
	_weiche_kaufchip_aus(_kiste)
	# Wackeln in Stoessen wie die 3D-Kiste; die letzten fuenf Sekunden blasser.
	_kiste_bild.pivot_offset = _kiste_bild.size * Vector2(0.5, 0.9)
	var phase: float = fmod(_zeit, Lieferkiste.WACKEL_TAKT)
	if phase < Lieferkiste.WACKEL_DAUER:
		var f: float = phase / Lieferkiste.WACKEL_DAUER
		_kiste_bild.rotation = sin(f * TAU * 2.0) * 0.16 * (1.0 - f)
	else:
		_kiste_bild.rotation = 0.0
	_kiste.modulate.a = clampf(kern.momente.rest / 5.0, 0.35, 1.0)
	# Pruefschalter --kiste-tipp: tippt die Kiste nach kurzer Zeit selbst an
	# (Vorschau des Muenzflugs ohne Finger).
	if _kiste.visible and kern.momente.dauer - kern.momente.rest > 2.0 \
			and OS.is_debug_build() and OS.get_cmdline_user_args().has("--kiste-tipp"):
		moment_getippt.emit(_kiste_bild.get_global_rect().get_center())


## Liegt der Aufkleber auf dem Kaufchip, rueckt er seitlich weg -- der Chip
## bleibt an seiner Station, er ist der wichtigere Hinweis.
func _weiche_kaufchip_aus(feld: Control) -> void:
	if not feld.visible or _kauf == null or not _kauf.visible:
		return
	var chip: Rect2 = _sichtbar(_kauf)
	var r: Rect2 = _sichtbar(feld)
	if not chip.grow(6.0).intersects(r):
		return
	var breite: float = get_viewport_rect().size.x
	var rechts: float = chip.end.x + 8.0 - r.position.x
	var links: float = chip.position.x - 8.0 - r.end.x
	var dx: float = rechts if r.position.x + rechts + r.size.x <= breite - SEITENRAND else links
	feld.position.x += dx


## Der Stapel: ein pulsierender Ring mit Zaehler um die wartenden Teile. Der Tipp
## raeumt ab und startet den Schub (GameCore.tippe_stapel) -- kein Geld.
func _baue_stapel() -> void:
	_stapel_ring = StapelRing.new()
	_stapel_ring.custom_minimum_size = Vector2(STAPEL_KANTE, STAPEL_KANTE)
	_stapel = _tippflaeche(_stapel_ring, _tippe_stapel)
	_stapel.name = "Stapel"
	add_child(_stapel)


func _zeige_stapel() -> void:
	var fluss: ClipFluss = ClipFluss.aktuell
	if not kern.momente.ist_stapel() or fluss == null or not is_instance_valid(fluss):
		_stapel.visible = false
		return
	var id: StringName = kern.momente.station
	var anzahl: int = fluss.stapel_anzahl(id)
	var ort: Vector3 = fluss.stapel_ort(id)
	if anzahl < fluss.stapel_antippbar_ab() or ort == Vector3.INF:
		_stapel.visible = false
		return
	_stapel_ring.anzahl = anzahl
	_stapel_ring.puls = 0.5 + 0.5 * sin(_zeit * 6.0)
	_stapel_ring.queue_redraw()
	_stapel.size = _stapel.get_combined_minimum_size()
	_stapel.visible = _setze(_stapel, ort, 0.0)
	_weiche_kaufchip_aus(_stapel)
	_stapel.modulate.a = clampf(kern.momente.rest / 5.0, 0.35, 1.0)
	if _stapel.visible and kern.momente.dauer - kern.momente.rest > 2.0 \
			and OS.is_debug_build() and OS.get_cmdline_user_args().has("--stapel-tipp"):
		_tippe_stapel()


func _tippe_stapel() -> void:
	var fluss: ClipFluss = ClipFluss.aktuell
	var id: StringName = kern.momente.station
	var von: Vector2 = _stapel.get_global_rect().get_center()
	var sekunden: float = kern.tippe_stapel(id)
	if sekunden <= 0.0:
		return
	if fluss != null and is_instance_valid(fluss):
		fluss.raeume_ab(id)
	_stapel.visible = false
	_schub_zeichen(von, sekunden)
	stapel_getippt.emit(id, sekunden)


## Mittlere Juice-Stufe: Funken aus dem Ring, "×2 · 0:30" steigt auf.
func _schub_zeichen(von: Vector2, sekunden: float) -> void:
	for i in range(STERN_BURST_ANZAHL):
		var funke: TextureRect = UiStil.symbolbild("stern", 26.0)
		funke.size = Vector2(26.0, 26.0)
		funke.position = von - funke.size * 0.5
		add_child(funke)
		var weg: Vector2 = Vector2.from_angle(TAU * float(i) / float(STERN_BURST_ANZAHL)) * 80.0
		var t := create_tween().set_parallel(true)
		t.tween_property(funke, "position", funke.position + weg, STERN_DAUER * 0.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		t.tween_property(funke, "modulate:a", 0.0, STERN_DAUER * 0.5)
		t.chain().tween_callback(funke.queue_free)
	var zeile := Label.new()
	var ganz: int = int(sekunden)
	var faktor: String = ("%.1f" % kern.balance.schub_faktor).rstrip("0").rstrip(".").replace(".", ",")
	zeile.text = UiText.t("boost_laeuft") % [faktor, "%d:%02d" % [ganz / 60, ganz % 60]]
	zeile.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_GROSS))
	zeile.add_theme_font_size_override("font_size", UiStil.GR_GROSS)
	zeile.add_theme_color_override("font_color", UiStil.KAUFEN)
	zeile.add_theme_color_override("font_outline_color", UiStil.TINTE)
	zeile.add_theme_constant_override("outline_size", 10)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(zeile)
	zeile.size = zeile.get_combined_minimum_size()
	zeile.position = von - zeile.size * 0.5 - Vector2(0.0, STAPEL_KANTE * 0.5)
	var f := create_tween().set_parallel(true)
	f.tween_property(zeile, "position:y", zeile.position.y - 90.0, 1.1).set_ease(Tween.EASE_OUT)
	f.tween_property(zeile, "modulate:a", 0.0, 0.6).set_delay(0.5)
	f.chain().tween_callback(zeile.queue_free)


## Ring um den Stapel: Kontur, Kaufen-Ring im Puls, Zaehler "×n" unten rechts.
class StapelRing extends Control:
	var anzahl: int = 0
	var puls: float = 0.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var m: Vector2 = size * 0.5
		var r: float = minf(size.x, size.y) * 0.5 - 6.0
		var innen: float = r * (0.86 + 0.1 * puls)
		draw_arc(m, innen, 0.0, TAU, 48, UiStil.TINTE, 12.0, true)
		draw_arc(m, innen, 0.0, TAU, 48, UiStil.KAUFEN, 6.0, true)
		# Innen das wartende Teil: Rueckt der Ring dem Kaufchip aus, bleibt lesbar,
		# was er meint.
		var teil: Texture2D = UiStil.symbol("clip")
		if teil != null:
			var k: float = innen * 1.05
			draw_texture_rect(teil, Rect2(m - Vector2(k, k) * 0.5, Vector2(k, k)), false)
		var schrift: Font = UiStil.schrift(UiStil.FETT, UiStil.GR_MITTEL)
		var text: String = "×%d" % anzahl
		var g: Vector2 = schrift.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, UiStil.GR_MITTEL)
		var mitte: Vector2 = m + Vector2(r * 0.6, r * 0.6)
		var kasten := Rect2(mitte - g * 0.5 - Vector2(8.0, 2.0), g + Vector2(16.0, 4.0))
		draw_style_box(UiStil.chip(UiStil.KAUFEN, 0.0, 0.0), kasten)
		draw_string(schrift, Vector2(kasten.position.x + 8.0, mitte.y + g.y * 0.3), text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, UiStil.GR_MITTEL, UiStil.TINTE)


## Der Stern-Moment an der Station (DESIGN_OVERHAUL 4.2): ein Burst aus Sternen
## am Abzeichen, dann fliegt EIN grosser Stern zu `ziel` (die Sternreihe im
## Menue). Gesamt <= 0,8 s, ohne Vollbild. Das Stationsmenue ruft es nach dem Kauf.
const STERN_DAUER: float = 0.8
const STERN_BURST_ANZAHL: int = 8


func stern_moment(station_id: StringName, ziel: Vector2) -> void:
	if kamera == null or not station_positionen.has(station_id):
		return
	var welt: Vector3 = (station_positionen[station_id] as Vector3) + Vector3(0.0, HOEHE_BADGE, 0.0)
	if kamera.is_position_behind(welt):
		return
	var von: Vector2 = kamera.unproject_position(welt)
	for i in range(STERN_BURST_ANZAHL):
		var kleiner: TextureRect = UiStil.symbolbild("stern", 30.0)
		kleiner.size = Vector2(30.0, 30.0)
		kleiner.pivot_offset = kleiner.size * 0.5
		kleiner.position = von - kleiner.size * 0.5
		kleiner.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(kleiner)
		var winkel: float = TAU * float(i) / float(STERN_BURST_ANZAHL)
		var weg: Vector2 = Vector2.from_angle(winkel) * 90.0
		var t := create_tween().set_parallel(true)
		t.tween_property(kleiner, "position", kleiner.position + weg, STERN_DAUER * 0.45) \
			.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		t.tween_property(kleiner, "modulate:a", 0.0, STERN_DAUER * 0.45)
		t.tween_property(kleiner, "scale", Vector2(0.3, 0.3), STERN_DAUER * 0.45).from(Vector2.ONE)
		t.chain().tween_callback(kleiner.queue_free)
	var gross: TextureRect = UiStil.symbolbild("stern", 72.0)
	gross.size = Vector2(72.0, 72.0)
	gross.pivot_offset = gross.size * 0.5
	gross.position = von - gross.size * 0.5
	gross.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(gross)
	var f := create_tween()
	f.tween_property(gross, "scale", Vector2(1.4, 1.4), STERN_DAUER * 0.3).from(Vector2(0.3, 0.3)) \
		.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	f.tween_property(gross, "position", ziel - gross.size * 0.5, STERN_DAUER * 0.7) \
		.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN)
	f.parallel().tween_property(gross, "scale", Vector2(0.4, 0.4), STERN_DAUER * 0.7)
	f.tween_callback(gross.queue_free)


## Die Pfeilform (Spitze, Schultern, Schaft) um `m`, Groesse `e` (Anteile des Radius).
static func pfeil_form(m: Vector2, e: float) -> PackedVector2Array:
	return PackedVector2Array([
		m + Vector2(0.0, -e), m + Vector2(e * 0.85, -e * 0.05), m + Vector2(e * 0.38, -e * 0.05),
		m + Vector2(e * 0.38, e * 0.85), m + Vector2(-e * 0.38, e * 0.85),
		m + Vector2(-e * 0.38, -e * 0.05), m + Vector2(-e * 0.85, -e * 0.05)])


## Das Zustandszeichen einer Raum-Plakette (K4 P1.2): Form UND Farbe je Zustand,
## damit es auch ohne Farbsehen eindeutig bleibt.
class PlakettenZeichen extends Control:
	var zustand: StringName = &""
	var anteil: float = 0.0
	var ring: float = 7.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var m: Vector2 = size * 0.5
		var r: float = minf(size.x, size.y) * 0.5
		var innen: float = r - float(UiStil.KONTUR)
		draw_circle(m, r, UiStil.TINTE)
		match zustand:
			&"kaufbar":
				# Dunkler Kreis, Limetten-Pfeil: "jetzt".
				var form: PackedVector2Array = Kartenmarker.pfeil_form(m, innen * 0.7)
				draw_colored_polygon(form, UiStil.KAUFEN)
			&"fast":
				# Heller Kreis, Ring fuellt sich, Pfeil noch grau: "bald".
				draw_circle(m, innen, UiStil.PAPIER)
				draw_arc(m, innen - ring * 0.5, 0.0, TAU, 40, UiStil.PAPIER_2, ring, true)
				if anteil > 0.0:
					draw_arc(m, innen - ring * 0.5, -PI * 0.5, -PI * 0.5 + TAU * anteil, 40,
						UiStil.TINTE, ring, true)
				var form: PackedVector2Array = Kartenmarker.pfeil_form(m, (innen - ring) * 0.62)
				draw_colored_polygon(form, UiStil.TINTE_3)
			&"gesperrt", &"bremst":
				draw_circle(m, innen, UiStil.PAPIER)
				var bild: Texture2D = UiStil.symbol("schloss" if zustand == &"gesperrt" else "warnung")
				if bild != null:
					var k: float = innen * 1.45
					draw_texture_rect(bild, Rect2(m - Vector2(k, k) * 0.5, Vector2(k, k)), false)


## Der kleine Kaufpfeil: gruener Kreis mit Pfeil = Ausbau bezahlbar;
## grauer Kreis mit Fortschrittsring = noch nicht (Ring = gespart / Preis).
class PfeilZeichen extends Control:
	var gruen: bool = false
	var anteil: float = 0.0
	var ring: float = 6.0

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _draw() -> void:
		var m: Vector2 = size * 0.5
		var r: float = minf(size.x, size.y) * 0.5
		draw_circle(m, r, UiStil.TINTE)
		var innen: float = r - float(UiStil.KONTUR)
		draw_circle(m, innen, UiStil.KAUFEN if gruen else UiStil.PAPIER_2)
		if not gruen and anteil > 0.0:
			draw_arc(m, innen - ring * 0.5, -PI * 0.5, -PI * 0.5 + TAU * anteil, 40,
				UiStil.KAUFEN_TIEF, ring, true)
		# Pfeil nach oben: Spitze, Schultern, Schaft (Anteile des Radius).
		var spitze: PackedVector2Array = Kartenmarker.pfeil_form(m, innen * 0.62)
		draw_colored_polygon(spitze, UiStil.PAPIER if gruen else UiStil.TINTE_3)
		var umriss := spitze.duplicate()
		umriss.append(spitze[0])
		draw_polyline(umriss, UiStil.TINTE, 2.0, true)
