## Das Menue einer Station -- im Stil von Idle Bank Tycoon: vier Bloecke, EINE Pille.
##
## Von oben (W2e, docs/neu/K6_KONZEPT.md 4.3):
##   1. Kopf: Symbol, Name, Stufe, Sterne, darunter "Noch 3 bis x1,5" mit duennem Balken
##   2. Die Kaufpille: Ausbauen, Preis gross, "+3,4 €/s" -- identisch zum Raum-Panel
##   3. x1 / x10 / MAX, klein
##   4. Liste (scrollt, schliesst nie): Hinweiszeile (Engpass), Crew, Ausstattung
##
## Alle Kaeufe gehen als Kommando an den Kern. Das Menue rechnet nichts selbst --
## es fragt (`einkommen_danach`, `station_leistung_danach`) und zeigt an.
##
## Jeder Kauf feiert: Zahl steigt auf, Muenzen fliegen, Funken, Vibration, ein Glanz
## huscht ueber die Pille; ein Stern-Meilenstein bekommt zusaetzlich Blitz,
## Aufschlag-Zahl und einen fliegenden Stern. Es kommt nie ein Fenster.
class_name Stationsmenue
extends Sheet

signal abgelehnt

const MENGEN: Array[int] = [1, 10, -1]
const ICON_PFAD: String = "res://assets/ui/%s/%s.png"
const MUENZEN_EINZEL: int = 6
const MUENZEN_MENGE: int = 14
## Zeilenhoehe der Ausstattung und Hoehe ihres Preisknopfs (KNOPF_SEKUNDAER_H).
const ZEILE_H: float = 80.0
const PREIS_KNOPF_B: float = 176.0

var kern: GameCore
var thema: ThemeData
var station_id: StringName = &""
var menge_index: int = 0
var _icon: TextureRect
var _stufe: Label
var _sterne_platz: HBoxContainer
var _stern_text: Label
var _stern_zaehler: Label
var _stern_balken: ProgressBar
var _stern_block: Control
var _hinweis_zeile: HBoxContainer
var _ausbau: Button
var _ausbau_preis: Label
var _ausbau_sub: Label
var _ausbau_titel: Label
var _mengen_knoepfe: Array[Button] = []
var _nutzen_euro: Label
var _nutzen_leistung: Label
var _spring_knopf: Button
var _spring_id: StringName = &""
var _lohnt_ausbau: PanelContainer
var _engpass: PanelContainer
var _mengen_zeile: HBoxContainer
var _karten: VBoxContainer
var _crew_platz: VBoxContainer
var _scroll: WischScroll
var _scroll_inhalt: VBoxContainer
var _crew_sig: String = ""
var _beschreibung: Label
var _platz_knoepfe: Dictionary = {}    ## platz_id -> PanelContainer
## Mehreinnahme je naechstem Kauf, bei jedem Aktualisieren neu gerechnet.
var _mehr_stufe: float = 0.0
var _mehr_platz: Dictionary = {}       ## platz_id -> float


func _init() -> void:
	super()
	_baue()


func _baue() -> void:
	# Kopf: Symbol der Station vor dem Titel, auf einem Papierfeld im Streifen.
	var icon_feld := PanelContainer.new()
	var ifeld := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KNOPF, UiStil.KONTUR_CHIP, 2.0, 0.0)
	icon_feld.add_theme_stylebox_override("panel", ifeld)
	icon_feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	icon_feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_icon = TextureRect.new()
	_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_icon.custom_minimum_size = Vector2(72.0, 72.0)
	icon_feld.add_child(_icon)
	kopf.add_child(icon_feld)
	kopf.move_child(icon_feld, 0)

	var titel_spalte := VBoxContainer.new()
	titel_spalte.add_theme_constant_override("separation", -2)
	titel_spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	titel_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	titel_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kopf.add_child(titel_spalte)
	kopf.move_child(titel_spalte, 1)
	titel.reparent(titel_spalte)

	var stufen_zeile := HBoxContainer.new()
	stufen_zeile.add_theme_constant_override("separation", UiStil.A2)
	stufen_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	titel_spalte.add_child(stufen_zeile)
	_stufe = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_stufe.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	stufen_zeile.add_child(_stufe)
	_sterne_platz = HBoxContainer.new()
	_sterne_platz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	stufen_zeile.add_child(_sterne_platz)

	# Was die Station tut: ein Satz, klein -- die Zahl kommt vor dem Erklaertext.
	_beschreibung = UiStil.label("", UiStil.GR_HINWEIS + 2, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
	# Umbrechen statt abschneiden: Der Satz steht im Scroll-Bereich, ist er laenger,
	# wischt man ihn hoch. Mit clip_text endete er frueher mitten im Wort.
	_beschreibung.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_beschreibung.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_baue_stern_block(titel_spalte)
	# Block 2 und 3: die Pille und die Mengen. Block 4: die Liste.
	_baue_pille()
	_baue_mengen()

	# Hinweis, Crew und Ausstattung scrollen in einem Rahmen: Das Sheet deckt die Welt
	# nie weiter zu als max_anteil (_passe_hoehe).
	_scroll = WischScroll.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	inhalt.add_child(_scroll)
	var scroll_inhalt := VBoxContainer.new()
	scroll_inhalt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll_inhalt.add_theme_constant_override("separation", UiStil.A3)
	scroll_inhalt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_scroll.add_child(scroll_inhalt)
	_scroll_inhalt = scroll_inhalt
	# Der umbrochene Erklaersatz kennt seine Hoehe erst nach dem Layout: dann nachmessen.
	scroll_inhalt.minimum_size_changed.connect(_passe_hoehe)

	_baue_hinweiszeile()
	scroll_inhalt.add_child(_hinweis_zeile)

	_crew_platz = VBoxContainer.new()
	_crew_platz.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scroll_inhalt.add_child(_crew_platz)

	# Ausstattung als Zeilen, nicht als Kartenreihe.
	_karten = VBoxContainer.new()
	_karten.add_theme_constant_override("separation", UiStil.A2)
	scroll_inhalt.add_child(_karten)
	# Der graue Erklaersatz steht UNTER den Karten: erst die Zahl, dann die Erklaerung.
	scroll_inhalt.add_child(_beschreibung)
	inhalt.add_theme_constant_override("separation", UiStil.A3)
	akzent_geaendert()


## Block 1, unterer Teil: "Noch 3 bis x1,5", Zaehler und ein duenner Gold-Balken im Kopf.
func _baue_stern_block(spalte: VBoxContainer) -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A1)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stern_block = box
	spalte.add_child(box)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(zeile)
	_stern_text = UiStil.label("", UiStil.GR_KLEIN, UiStil.akzent_text(), UiStil.FETT)
	_stern_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_stern_text.clip_text = true
	_stern_text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	zeile.add_child(_stern_text)
	_stern_zaehler = UiStil.label("", UiStil.GR_KLEIN, UiStil.akzent_text(), UiStil.FETT)
	zeile.add_child(_stern_zaehler)
	_stern_balken = UiStil.neuer_balken(10.0, UiStil.STERN_BALKEN)
	box.add_child(_stern_balken)


## Hinweiszeile am Anfang der Liste: nur sichtbar, wenn etwas zu sagen ist -- der
## Engpass sitzt woanders (mit Sprung dorthin), oder DIESE Station bremst.
func _baue_hinweiszeile() -> void:
	_hinweis_zeile = HBoxContainer.new()
	_hinweis_zeile.add_theme_constant_override("separation", UiStil.A2)
	_hinweis_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hinweis_zeile.visible = false
	_nutzen_euro = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT)
	_nutzen_euro.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_nutzen_euro.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_nutzen_euro.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hinweis_zeile.add_child(_nutzen_euro)
	_nutzen_leistung = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT)
	_nutzen_leistung.visible = false
	_hinweis_zeile.add_child(_nutzen_leistung)
	_spring_knopf = Button.new()
	UiStil.faerbe_knopf(_spring_knopf, UiStil.PAPIER)
	_spring_knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
	_spring_knopf.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
	_spring_knopf.size_flags_horizontal = Control.SIZE_SHRINK_END
	_spring_knopf.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_spring_knopf.custom_minimum_size = Vector2(170.0, UiStil.TIPPZIEL * 0.6)
	_spring_knopf.pressed.connect(_auf_springen)
	_spring_knopf.visible = false
	_hinweis_zeile.add_child(_spring_knopf)
	_lohnt_ausbau = _lohnt_chip()
	_hinweis_zeile.add_child(_lohnt_ausbau)
	_engpass = PanelContainer.new()
	_engpass.add_theme_stylebox_override("panel", UiStil.chip(UiStil.WARNUNG, float(UiStil.A3), 2.0))
	_engpass.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_engpass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var engpass_box := HBoxContainer.new()
	engpass_box.add_theme_constant_override("separation", UiStil.A1 + 2)
	_engpass.add_child(engpass_box)
	engpass_box.add_child(UiStil.symbolbild("warnung", 28.0))
	engpass_box.add_child(UiStil.label(UiText.t("bremst"), UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT))
	_hinweis_zeile.add_child(_engpass)


## Block 2: die Kaufpille -- dasselbe Muster wie im Raum-Panel.
func _baue_pille() -> void:
	_ausbau = UiStil.kaufpille({"hoehe": UiStil.KNOPF_PRIMAER_H, "titel": "", "preis": "", "zustand": "nicht",
		"euro": true})
	_ausbau.pressed.connect(_auf_ausbau)
	inhalt.add_child(_ausbau)
	var teile: Dictionary = _ausbau.get_meta("teile") as Dictionary
	_ausbau_preis = teile["preis"] as Label
	_ausbau_sub = teile["nutzen"] as Label
	_ausbau_titel = teile["titel"] as Label


## Block 3: x1 / x10 / MAX, klein und ruhig.
func _baue_mengen() -> void:
	_mengen_zeile = HBoxContainer.new()
	_mengen_zeile.add_theme_constant_override("separation", UiStil.A2)
	inhalt.add_child(_mengen_zeile)
	var h: float = float(Sheet.konfig_wert("station_menue", "mengen_h", 56.0))
	for i in range(MENGEN.size()):
		var m := Button.new()
		m.focus_mode = Control.FOCUS_NONE
		m.text = "x%d" % MENGEN[i] if MENGEN[i] > 0 else UiText.t("max")
		m.custom_minimum_size = Vector2(60.0, h)
		m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		m.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		m.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		var index: int = i
		m.pressed.connect(func() -> void:
			menge_index = index
			Haptik.puls(10)
			aktualisiere())
		_mengen_zeile.add_child(m)
		_mengen_knoepfe.append(m)


func akzent_geaendert() -> void:
	if _stufe != null:
		_stufe.add_theme_color_override("font_color", UiStil.akzent_text())


func zeige_station(id: StringName) -> void:
	var neu: bool = id != station_id
	station_id = id
	if neu:
		_baue_karten()
	oeffnen()


func _baue_karten() -> void:
	for kind in _karten.get_children():
		kind.queue_free()
	_platz_knoepfe.clear()
	var station: StationModel = kern.kette.station(station_id)
	if station == null:
		return
	for p in station.ausstattung:
		_karten.add_child(_baue_zeile(p))
	_karten.visible = not station.ausstattung.is_empty()


## Eine Ausstattungs-Zeile: Symbol, Name + Stufe, Nutzen, Preisknopf.
func _baue_zeile(p: EquipmentSlot) -> PanelContainer:
	var karte_neu := PanelContainer.new()
	karte_neu.set_meta("stil", &"")
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.custom_minimum_size = Vector2(0.0, ZEILE_H - 2.0 * float(UiStil.A2) - 6.0)
	karte_neu.add_child(zeile)

	var bild := TextureRect.new()
	bild.name = "Bild"
	bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	bild.custom_minimum_size = Vector2(60.0, 60.0)
	bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(bild)

	var text_spalte := VBoxContainer.new()
	text_spalte.add_theme_constant_override("separation", 0)
	text_spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_spalte.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text_spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(text_spalte)

	var name_zeile := HBoxContainer.new()
	name_zeile.add_theme_constant_override("separation", UiStil.A2)
	name_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text_spalte.add_child(name_zeile)
	var name := UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	name.name = "Name"
	name_zeile.add_child(name)
	var lohnt := _lohnt_chip()
	lohnt.name = "Lohnt"
	name_zeile.add_child(lohnt)

	# Stufe, Sterne und aktuelles Modell in einer Zeile.
	var unter := HBoxContainer.new()
	unter.add_theme_constant_override("separation", UiStil.A2)
	unter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	text_spalte.add_child(unter)
	var sterne_zeile := CenterContainer.new()
	sterne_zeile.name = "Sterne"
	sterne_zeile.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	unter.add_child(sterne_zeile)
	var stufe := UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.FETT)
	stufe.name = "Stufe"
	stufe.clip_text = true
	stufe.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	stufe.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	unter.add_child(stufe)

	# Sperre: wie weit ist die Station von der Freigabe? Nur gesperrt sichtbar.
	var sperre := UiStil.neuer_balken(10.0, UiStil.GOLD)
	sperre.name = "Sperrbalken"
	sperre.visible = false
	sperre.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text_spalte.add_child(sperre)

	var nutzen := UiStil.label("", UiStil.GR_TEXT, UiStil.PLUS_TEXT, UiStil.FETT)
	nutzen.name = "Nutzen"
	nutzen.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	nutzen.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(nutzen)

	var knopf: Button = UiStil.kaufpille({"hoehe": UiStil.KNOPF_SEKUNDAER_H, "preis": "", "zustand": "nicht"})
	knopf.name = "Knopf"
	knopf.custom_minimum_size = Vector2(PREIS_KNOPF_B, UiStil.KNOPF_SEKUNDAER_H)
	knopf.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var platz_id: StringName = p.id
	knopf.pressed.connect(func() -> void: _kaufe_platz(platz_id, karte_neu, knopf))
	zeile.add_child(knopf)
	_platz_knoepfe[platz_id] = karte_neu
	return karte_neu


## Ein goldener Hinweis auf den Kauf, der gerade am meisten bringt.
##
## Der Spieler soll lernen, WAS sich lohnt -- nicht raten. Er steht auf genau
## einem Kauf je Menue: dem mit der hoechsten Mehreinnahme je Euro.
static func _lohnt_chip() -> PanelContainer:
	var chip := PanelContainer.new()
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.GOLD, float(UiStil.A2), 1.0, 2.0))
	chip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(UiStil.label(UiText.t("lohnt_sich"), UiStil.GR_HINWEIS - 2, UiStil.TINTE, UiStil.FETT))
	chip.visible = false
	return chip


## Begrenzt die Hoehe des Sheets auf SHEET_MAX (Anteil der Bildhoehe): Nur der
## Ausstattungsbereich scrollt, Kopf, Held-Zeile und Hauptknopf bleiben stehen.
func _passe_hoehe() -> void:
	if _scroll == null or not is_inside_tree():
		return
	var voll: float = get_viewport().get_visible_rect().size.y
	var rest: float = karte.get_combined_minimum_size().y - _scroll.custom_minimum_size.y
	var anteil: float = float(Sheet.konfig_wert("station_menue", "max_anteil", 0.45))
	var grenze: float = maxf(voll * anteil - unten_frei - rest, 120.0)
	var wunsch: float = _scroll_inhalt.get_combined_minimum_size().y
	var neu: float = minf(wunsch, grenze)
	if absf(neu - _scroll.custom_minimum_size.y) > 1.0:
		_scroll.custom_minimum_size.y = neu


func aktualisiere() -> void:
	if kern == null or station_id == &"":
		return
	_passe_hoehe.call_deferred()
	var station: StationModel = kern.kette.station(station_id)
	if station == null:
		return
	titel.text = WeltTexte.station_name(thema, station_id)
	_icon.texture = _station_icon()
	_beschreibung.text = WeltTexte.station_kurz(thema, station_id)
	_beschreibung.visible = not _beschreibung.text.is_empty()

	if station.max_stufe > 0:
		_stufe.text = UiText.t("stufe_von") % [station.stufe, station.max_stufe]
	else:
		_stufe.text = UiText.t("stufe") % station.stufe
	var moeglich: int = station.sterne_moeglich()
	var sterne_zustand: Array = [station.sterne(), moeglich]
	if _sterne_platz.get_meta("zustand", []) != sterne_zustand:
		var neuer_stern: bool = _sterne_platz.has_meta("zustand") \
			and (_sterne_platz.get_meta("zustand") as Array)[0] < station.sterne()
		_sterne_platz.set_meta("zustand", sterne_zustand)
		for kind in _sterne_platz.get_children():
			kind.queue_free()
		if moeglich > 0:
			var reihe: HBoxContainer = Sheet.sterne(station.sterne(), moeglich, 30.0)
			_sterne_platz.add_child(reihe)
			if neuer_stern:
				UiStil.aufploppen.call_deferred(reihe, 0.6)

	_aktualisiere_stern(station, moeglich)
	_aktualisiere_crew()
	_rechne_nutzen(station)
	_aktualisiere_ausbau(station)
	_aktualisiere_nutzen(station)
	_engpass.visible = kern.kette.bottleneck() == station_id and Ids.CHAIN.has(station_id)
	var bester: StringName = _bester_kauf(station)
	_lohnt_ausbau.visible = bester == &"stufe" and not _engpass.visible
	# Die grosse Nutzen-Zahl steht in der Pille; hier bleibt nur der Hinweis, wer bremst.
	_nutzen_euro.visible = _spring_knopf.visible
	_nutzen_leistung.visible = false
	_hinweis_zeile.visible = _spring_knopf.visible or _engpass.visible or _lohnt_ausbau.visible
	for p in station.ausstattung:
		_aktualisiere_zeile(station, p)
		var karte_p: PanelContainer = _platz_knoepfe.get(p.id) as PanelContainer
		if karte_p != null:
			(karte_p.find_child("Lohnt", true, false) as Control).visible = bester == p.id


## Die Crew-Karte der Station: Portrait (per Schluessel), Name, Rangtitel, Kartentext
## und ein Knopf fuer den naechsten Rang. Wird nur neu gebaut, wenn sich etwas aendert.
func _aktualisiere_crew() -> void:
	# Crew-Karten gibt es erst ab dem Rang aus erfolge.json (K2 4.1, "crew").
	if not kern.crew_hat(station_id) or not kern.ist_frei("crew"):
		_crew_platz.visible = false
		return
	var raenge: Array[Dictionary] = kern.crew_raenge(station_id)
	var rang: int = kern.crew_rang(station_id)
	var naechster: Dictionary = {}
	for r in raenge:
		if bool(r["naechster"]):
			naechster = r
	var kaufbar: bool = not naechster.is_empty() and bool(naechster["kaufbar"])
	var st: StationModel = kern.kette.station(station_id)
	var stufe: int = st.stufe if st != null else 0
	var eigene_bedingung: bool = not kern.crew.frei_bedingung(station_id).is_empty()
	var schmal: bool = false
	if rang == 0 and not kern.crew_frei(station_id):
		# Anfaenger nicht fluten: erst spaeter eine schmale Zeile, dann die Karte.
		if eigene_bedingung or stufe < kern.crew.karte_ab_stufe:
			_crew_platz.visible = false
			return
		schmal = true
	var sig: String = "%s|%d|%s|%s|%s" % [station_id, rang, kern.crew_frei(station_id), kaufbar, schmal]
	_crew_platz.visible = true
	if sig == _crew_sig:
		return
	_crew_sig = sig
	for kind in _crew_platz.get_children():
		kind.queue_free()
	var daten: Dictionary = thema.abschnitt("crew").get(String(station_id), {}) as Dictionary if thema != null else {}
	var name: String = String(daten.get("name", ""))
	var titel_liste: Array = daten.get("raenge", []) as Array
	var text_liste: Array = daten.get("texte", []) as Array
	var frei: bool = kern.crew_frei(station_id)
	if schmal:
		var zeile_s := Label.new()
		zeile_s.text = UiText.t("crew_ab_stufe") % kern.crew.frei_ab_stufe
		zeile_s.add_theme_font_size_override("font_size", UiStil.GR_HINWEIS + 2)
		zeile_s.add_theme_color_override("font_color", UiStil.TINTE_2)
		zeile_s.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_crew_platz.add_child(zeile_s)
		return
	var karte_c := Sheet.innenkarte(float(UiStil.A3))
	_crew_platz.add_child(karte_c)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	karte_c.add_child(zeile)
	var avatar: PanelContainer = UiStil.crew_avatar(String(daten.get("portrait", "")), name, 80.0)
	if rang == 0:
		avatar.modulate = Color(1, 1, 1, 0.55)
	zeile.add_child(avatar)
	var spalte := VBoxContainer.new()
	spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spalte.add_theme_constant_override("separation", 0)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(spalte)
	spalte.add_child(UiStil.label(name if not name.is_empty() else UiText.t("crew_titel"),
		UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT))
	var rang_text: String = UiText.t("crew_gesperrt")
	if rang > 0 and rang <= titel_liste.size():
		rang_text = String(titel_liste[rang - 1])
	elif frei and not titel_liste.is_empty():
		rang_text = String(daten.get("rolle", titel_liste[0]))
	spalte.add_child(UiStil.label("%s · %s" % [rang_text, UiText.t("crew_rang") % [rang, raenge.size()]],
		UiStil.GR_HINWEIS + 2, UiStil.TINTE_2, UiStil.FETT))
	var satz_index: int = clampi(maxi(rang - 1, 0), 0, maxi(text_liste.size() - 1, 0))
	if not text_liste.is_empty():
		var satz := UiStil.label(String(text_liste[satz_index]), UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		satz.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		satz.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(satz)
	var knopf: Button
	if naechster.is_empty():
		knopf = UiStil.kaufpille({"hoehe": UiStil.KNOPF_SEKUNDAER_H, "zustand": "fertig",
			"preis": UiText.t("crew_voll")})
	else:
		var kosten_text: String = "%s  %s" % [UiText.t("crew_anheuern"), UiStil.preis(float(naechster["kosten"]))]
		knopf = UiStil.kaufpille({"hoehe": UiStil.KNOPF_SEKUNDAER_H, "preis": kosten_text,
			"zustand": "kaufbar" if kaufbar else ("nicht" if frei else "gesperrt")})
		knopf.pressed.connect(func() -> void:
			if kern.kaufe_crew(station_id):
				Haptik.puls(14)
			else:
				abgelehnt.emit()
			_crew_sig = ""
			aktualisiere())
	knopf.custom_minimum_size = Vector2(0.0, UiStil.KNOPF_SEKUNDAER_H)
	knopf.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spalte.add_child(knopf)


## Stern-Fortschritt im Kopf: "Noch 3 bis x1,5", Zaehler, Balken.
func _aktualisiere_stern(station: StationModel, moeglich: int) -> void:
	var bis: int = station.stufen_bis_meilenstein()
	var alle: bool = station.ist_max() or (moeglich > 0 and station.sterne() >= moeglich)
	var intervall: int = maxi(station.meilenstein_intervall, 1)
	if alle:
		_stern_text.text = UiText.t("alle_sterne")
		_stern_zaehler.text = ""
		_stern_balken.value = 1.0
	else:
		_stern_text.text = UiText.t("noch_bis_faktor") % [bis, faktor_text(station.meilenstein_faktor)]
		_stern_zaehler.text = "%d/%d" % [station.stufe % intervall, intervall]
		_stern_balken.value = float(intervall - bis) / float(intervall)
	_stern_block.visible = true


## "1,5" statt "1.50": der Faktor eines Sterns, wie ihn ein Mensch schreibt.
static func faktor_text(faktor: float) -> String:
	var t: String = ("%.2f" % faktor)
	while t.contains(".") and (t.ends_with("0") or t.ends_with(".")):
		t = t.left(t.length() - 1)
	return t.replace(".", ",")


func _aktualisiere_ausbau(station: StationModel) -> void:
	for i in range(_mengen_knoepfe.size()):
		# Die gewaehlte Menge ist Tinte -- ein Schalter, kein zweiter Kaufknopf.
		UiStil.faerbe_knopf(_mengen_knoepfe[i], UiStil.TINTE if i == menge_index else UiStil.PAPIER)
	if station.ist_max():
		UiStil.kaufpille({"hoehe": UiStil.KNOPF_PRIMAER_H, "zustand": "fertig", "titel": UiText.t("fertig"),
			"symbol": UiStil.symbol("haken"), "preis": "", "euro": true}, _ausbau)
		return
	var vorschau: Array = kern.vorschau_mehrfach(station_id, MENGEN[menge_index])
	var anzahl: int = int(vorschau[0])
	var preis: float = float(vorschau[1])
	var zu_teuer: bool = anzahl == 0 or kern.kapital < preis
	var warten: String = _wartezeit_text(preis) if zu_teuer else ""
	_ausbau.set_meta("fehlt", maxf(preis - kern.kapital, 0.0))
	# Titel: AUSBAUEN (mit Menge); Nutzen: Wartezeit oder "+3,4 €/s" -- in der Einheit
	# des Tutorials. Prozent nur noch, wenn mehrere Stufen auf einmal gekauft werden.
	var titel_text: String = UiText.t("ausbauen").to_upper()
	if anzahl > 1:
		titel_text += " x%d" % anzahl
	var jetzt: float = kern.station_leistung(station_id)
	var danach: float = kern.station_leistung_danach(station_id)
	var prozent: int = int(roundf((danach / jetzt - 1.0) * 100.0)) if jetzt > 0.0 else 0
	var nutzen: String = ""
	if not warten.is_empty():
		nutzen = warten
	elif anzahl <= 1 and UiStil.zahl(_mehr_stufe) != "0":
		nutzen = UiText.t("einnahmen_plus") % UiStil.zahl(_mehr_stufe)
	elif prozent > 0:
		nutzen = UiText.t("plus_prozent") % prozent
	UiStil.kaufpille({"hoehe": UiStil.KNOPF_PRIMAER_H, "zustand": "nicht" if zu_teuer else "kaufbar",
		"symbol": UiStil.symbol("pfeil_hoch"), "titel": titel_text, "nutzen": nutzen,
		"preis": "%s €" % UiStil.preis(preis), "euro": true}, _ausbau)


## Mehreinnahme je moeglichem Kauf, einmal je Aktualisierung gerechnet.
func _rechne_nutzen(station: StationModel) -> void:
	var einkommen: float = kern.einkommen_pro_sekunde()
	_mehr_stufe = 0.0
	_mehr_platz.clear()
	if station.kann_ausbauen():
		_mehr_stufe = maxf(kern.einkommen_danach(station_id) - einkommen, 0.0)
	for p in station.ausstattung:
		if p.ist_max() or not p.freigegeben(station.stufe):
			continue
		_mehr_platz[p.id] = maxf(kern.einkommen_danach(station_id, p.id) - einkommen, 0.0)


## Die Held-Zeile: gross, was der Ausbau bringt -- oder warum nicht.
##
## "+0 EUR/s" las sich wie ein Fehler, "Bringt gerade nichts" wie eine Strafe.
## Jetzt sagt die Karte, wer bremst, und der Knopf darunter springt dorthin.
func _aktualisiere_nutzen(station: StationModel) -> void:
	var einheit: String = WeltTexte.einheit(thema, station_id)
	var jetzt: float = kern.station_leistung(station_id)
	_spring_knopf.visible = false
	if station.ist_max():
		_nutzen_euro.add_theme_font_size_override("font_size", UiStil.GR_TITEL)
		_nutzen_euro.text = "%s %s" % [_leistungstext(jetzt), "" if _leistung_in_euro() else einheit]
		_nutzen_euro.add_theme_color_override("font_color", UiStil.TINTE)
		_nutzen_leistung.visible = false
		return
	var danach: float = kern.station_leistung_danach(station_id)
	var engpass: StringName = kern.kette.bottleneck()
	var zahl_mehr: String = UiStil.zahl(_mehr_stufe)
	if zahl_mehr == "0" and engpass != &"" and engpass != station_id:
		# Nebeninfo: ruhig und klein, die Aktion ("Zu ...") daneben ist das Wichtige.
		_nutzen_euro.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
		_nutzen_euro.text = UiText.t("bremst_nicht_spring") % WeltTexte.station_name(thema, engpass)
		_nutzen_euro.add_theme_color_override("font_color", UiStil.TINTE_2)
		_spring_id = engpass
		_spring_knopf.text = UiText.t("zu_station") % WeltTexte.station_name(thema, engpass)
		_spring_knopf.visible = true
	elif _ist_kettenleistung() and _mehr_stufe > 0.0 and not einheit.is_empty():
		# K3 A2 (N1): Genau EINE Einheit gross, und zwar die des Tutorials und des
		# Kaufknopfs: "+0,4 €/s". Die Einheiten je Minute stehen klein darunter.
		_nutzen_euro.add_theme_font_size_override("font_size", UiStil.GR_NUTZEN)
		_nutzen_euro.text = UiText.t("einnahmen_plus") % zahl_mehr
		_nutzen_euro.add_theme_color_override("font_color", UiStil.PLUS_TEXT)
		_nutzen_leistung.visible = true
		_nutzen_leistung.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
		_nutzen_leistung.add_theme_color_override("font_color", UiStil.TINTE_2)
		_nutzen_leistung.text = "+%s %s · %s → %s" % [UiStil.zahl((danach - jetzt) * 60.0), einheit,
			_leistungstext(jetzt), _leistungstext(danach)]
		return
	else:
		_nutzen_euro.add_theme_font_size_override("font_size", UiStil.GR_TITEL)
		_nutzen_euro.text = UiText.t("einnahmen_plus") % zahl_mehr
		_nutzen_euro.add_theme_color_override("font_color", UiStil.PLUS_TEXT if _mehr_stufe > 0.0 else UiStil.TINTE_2)
	_nutzen_leistung.visible = not _leistung_in_euro()
	_nutzen_leistung.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
	_nutzen_leistung.add_theme_color_override("font_color", UiStil.TINTE_2)
	# vorher -> nachher, mit Einheit; das Delta in Prozent steht schon am Knopf.
	_nutzen_leistung.text = UiText.t("leistung_pfeil") % [_leistungstext(jetzt), _leistungstext(danach),
		"" if _leistung_in_euro() else einheit]


## Welcher Kauf bringt gerade am meisten je Euro? "stufe", eine Platz-ID oder leer.
func _bester_kauf(station: StationModel) -> StringName:
	var bester: StringName = &""
	var bestwert: float = 0.0
	if station.kann_ausbauen():
		var wert: float = _mehr_stufe / maxf(station.naechste_kosten(), 1.0)
		if wert > bestwert:
			bestwert = wert
			bester = &"stufe"
	for p in station.ausstattung:
		if p.ist_max() or not p.freigegeben(station.stufe):
			continue
		var wert: float = float(_mehr_platz.get(p.id, 0.0)) / maxf(p.naechste_kosten(), 1.0)
		if wert > bestwert * 1.0001:
			bestwert = wert
			bester = p.id
	return bester


## "in 1:23" bis ein Preis bezahlbar ist -- oder leer, wenn er es schon ist.
func _wartezeit_text(preis: float) -> String:
	var fehlt: float = preis - kern.kapital
	var einkommen: float = kern.einkommen_pro_sekunde()
	if fehlt <= 0.0 or einkommen <= 0.0:
		return ""
	var sekunden: float = fehlt / einkommen
	if sekunden >= 3600.0:
		return UiText.t("in_zeit") % WeltTexte.dauer(sekunden)
	var ganz: int = int(ceilf(sekunden))
	return UiText.t("in_zeit") % ("%d:%02d" % [ganz / 60, ganz % 60])


## Kettenglieder leisten Einheiten je Minute; Transport und Sonderstation einen Faktor bzw. Euro.
func _ist_kettenleistung() -> bool:
	return station_id != Ids.STATION_TRANSPORT and station_id != Ids.STATION_SPECIAL


func _leistung_in_euro() -> bool:
	return station_id == Ids.STATION_SPECIAL and kern.balance != null and kern.balance.grundeinnahme_aktiv


func _leistungstext(wert: float) -> String:
	# Eine Sonderstation mit eigener Grundeinnahme leistet Euro je Sekunde,
	# keinen Faktor (Welt 3, docs/nacht/wuensche_engine_an_ui.md 3).
	if _leistung_in_euro():
		return UiText.t("einnahmen_plus") % UiStil.zahl(wert)
	if station_id == Ids.STATION_TRANSPORT or station_id == Ids.STATION_SPECIAL:
		return "×" + ("%.2f" % wert).replace(".", ",")
	# Kettenglieder in Einheiten pro MINUTE: "0,3 pro Sekunde" liest sich
	# wie Stillstand, "18 pro Minute" wie Arbeit.
	return UiStil.zahl(wert * 60.0)


func _zeilen_stil(karte_p: PanelContainer, art: StringName) -> void:
	if karte_p.get_meta("stil", &"") == art:
		return
	karte_p.set_meta("stil", art)
	var farbe: Color = UiStil.GESPERRT if art == &"gesperrt" else UiStil.PAPIER
	var s: StickerBox = UiStil.karte(farbe, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A2))
	if art == &"gesperrt":
		s.flaeche.border_color = Color(UiStil.TINTE, 0.35)
		s.schatten = null
	karte_p.add_theme_stylebox_override("panel", s)


func _aktualisiere_zeile(station: StationModel, p: EquipmentSlot) -> void:
	var karte_p: PanelContainer = _platz_knoepfe.get(p.id) as PanelContainer
	if karte_p == null:
		return
	var bild: TextureRect = karte_p.find_child("Bild", true, false) as TextureRect
	var name: Label = karte_p.find_child("Name", true, false) as Label
	var stufe: Label = karte_p.find_child("Stufe", true, false) as Label
	var sterne_zeile: CenterContainer = karte_p.find_child("Sterne", true, false) as CenterContainer
	var knopf: Button = karte_p.find_child("Knopf", true, false) as Button
	var nutzen: Label = karte_p.find_child("Nutzen", true, false) as Label
	var sperre: ProgressBar = karte_p.find_child("Sperrbalken", true, false) as ProgressBar

	# Das Bild zeigt, was dort STEHT -- oder, solange noch nichts gekauft ist,
	# das erste Modell etwas blasser. Der Name ist der des Platzes ("Bildschirm"),
	# nicht der des Modells: Der Platz aendert sich nie, das Modell dreimal.
	bild.texture = _platz_icon(p.id, maxi(p.modellstufe(), 1))
	name.text = WeltTexte.platz_name(thema, station_id, p.id)
	var jetzt_name: String = WeltTexte.platz_stufe_name(thema, station_id, p.id, maxi(p.modellstufe(), 1))
	stufe.text = "%s · %s" % [UiText.t("stufe_von") % [p.stufe, p.max_stufe], jetzt_name]
	var sterne_zustand: Array = [p.modellstufe(), p.modell_schwellen.size()]
	if sterne_zeile.get_meta("zustand", []) != sterne_zustand:
		sterne_zeile.set_meta("zustand", sterne_zustand)
		for kind in sterne_zeile.get_children():
			kind.queue_free()
		sterne_zeile.add_child(Sheet.sterne(p.modellstufe(), p.modell_schwellen.size(), 20.0))

	sperre.visible = false
	nutzen.text = ""
	knopf.visible = true
	var kn_daten: Dictionary = {"hoehe": UiStil.KNOPF_SEKUNDAER_H}
	if p.ist_max():
		_zeilen_stil(karte_p, &"normal")
		kn_daten["zustand"] = "fertig"
		kn_daten["preis"] = UiText.t("fertig")
		UiStil.kaufpille(kn_daten, knopf)
		bild.modulate = Color.WHITE
		return
	if not p.freigegeben(station.stufe):
		# Gesperrt: Silhouette, Schloss, Mini-Balken -- nie ein Preis.
		_zeilen_stil(karte_p, &"gesperrt")
		kn_daten["zustand"] = "gesperrt"
		kn_daten["preis"] = UiText.t("ab_stufe") % p.ab_stufe
		UiStil.kaufpille(kn_daten, knopf)
		bild.modulate = Color(UiStil.TINTE, 0.45)
		sperre.visible = true
		sperre.value = clampf(float(station.stufe) / float(maxi(p.ab_stufe, 1)), 0.0, 1.0)
		nutzen.text = "%d/%d" % [station.stufe, p.ab_stufe]
		nutzen.add_theme_color_override("font_color", UiStil.TINTE_2)
		return
	_zeilen_stil(karte_p, &"normal")
	var preis: float = p.naechste_kosten()
	kn_daten["zustand"] = "kaufbar" if kern.kapital >= preis else "nicht"
	kn_daten["preis"] = UiStil.preis(preis)
	UiStil.kaufpille(kn_daten, knopf)
	bild.modulate = Color.WHITE if p.stufe > 0 else Color(1, 1, 1, 0.75)
	# Nutzen des naechsten Kaufs: Leistung in Prozent, sonst die Mehreinnahme.
	var leistung: float = kern.station_leistung(station_id)
	var danach: float = kern.station_leistung_danach(station_id, p.id)
	var prozent: int = int(roundf((danach / leistung - 1.0) * 100.0)) if leistung > 0.0 else 0
	nutzen.add_theme_color_override("font_color", UiStil.PLUS_TEXT)
	if prozent > 0:
		nutzen.text = UiText.t("plus_prozent") % prozent
	elif UiStil.zahl(float(_mehr_platz.get(p.id, 0.0))) != "0":
		nutzen.text = UiText.t("einnahmen_plus") % UiStil.zahl(float(_mehr_platz.get(p.id, 0.0)))


func _station_icon() -> Texture2D:
	var pfad: String = ICON_PFAD % [kern.welt_id(), String(station_id)]
	if ResourceLoader.exists(pfad):
		return load(pfad) as Texture2D
	return UiStil.symbol("werkzeug")


func _platz_icon(platz_id: StringName, modellstufe: int) -> Texture2D:
	var pfad: String = ICON_PFAD % [kern.welt_id(), "%s_%s_%d" % [station_id, platz_id, modellstufe]]
	if ResourceLoader.exists(pfad):
		return load(pfad) as Texture2D
	return UiStil.symbol("geschenk")


# --- Kaufen und feiern -------------------------------------------------------------

func _auf_springen() -> void:
	if _spring_id == &"":
		return
	var hud := get_parent() as Hud
	if hud != null:
		hud.zeige_station(_spring_id)
	else:
		zeige_station(_spring_id)


func _auf_ausbau() -> void:
	var station: StationModel = kern.kette.station(station_id)
	if station == null:
		return
	var vorher := _momentaufnahme(station)
	var gekauft: int = kern.upgrade_station_mehrfach(station_id, MENGEN[menge_index])
	if gekauft <= 0:
		abgelehnt.emit()
		Haptik.puls(8)
		aktualisiere()
		return
	_feiere(_ausbau, vorher, gekauft)
	pille_glanz(_ausbau)
	UiStil.aufploppen(_stufe, 1.25)
	aktualisiere()


func _kaufe_platz(platz_id: StringName, karte_p: Control, knopf: Button) -> void:
	var station: StationModel = kern.kette.station(station_id)
	if station == null:
		return
	var vorher := _momentaufnahme(station)
	if kern.kaufe_ausstattung(station_id, platz_id):
		UiStil.aufploppen(karte_p, 0.9)
		_feiere(knopf, vorher, 1)
	else:
		abgelehnt.emit()
		Haptik.puls(8)
	aktualisiere()


func _momentaufnahme(station: StationModel) -> Dictionary:
	return {
		"einkommen": kern.einkommen_pro_sekunde(),
		"leistung": kern.station_leistung(station_id),
		"sterne": station.sterne(),
	}


## Der Moment nach dem Kauf. Alles hier ist Darstellung -- gerechnet hat der Kern.
func _feiere(quelle: Control, vorher: Dictionary, gekauft: int) -> void:
	var station: StationModel = kern.kette.station(station_id)
	var hud := get_parent() as Hud
	var saft: Saft = hud.saft if hud != null else null
	var viele: bool = gekauft > 1
	var stern: bool = station != null and station.sterne() > int(vorher["sterne"])
	Haptik.puls(Haptik.DAUER_STERN if stern else (Haptik.DAUER_MENGE if viele else Haptik.DAUER_KAUF))
	if hud != null and hud.audio != null and stern:
		hud.audio.spiele(&"stern")
	if saft == null or not quelle.is_inside_tree():
		return
	var mitte: Vector2 = quelle.get_global_rect().get_center()
	var station_bild: Vector2 = _station_im_bild(hud)

	# Die Zahl: Mehreinnahme in Euro, sonst Leistung in Prozent.
	var mehr: float = kern.einkommen_pro_sekunde() - float(vorher["einkommen"])
	var text: String = ""
	if mehr > 0.0 and UiStil.zahl(mehr) != "0":
		text = UiText.t("einnahmen_plus") % UiStil.zahl(mehr)
	else:
		var jetzt: float = kern.station_leistung(station_id)
		var vor: float = float(vorher["leistung"])
		if vor > 0.0 and jetzt > vor:
			text = UiText.t("plus_prozent") % int(roundf((jetzt / vor - 1.0) * 100.0))
	if not text.is_empty():
		saft.betrag(mitte + Vector2(0.0, -70.0), text, UiStil.KAUFEN)

	saft.muenzen(mitte, MUENZEN_MENGE if viele else MUENZEN_EINZEL)
	saft.funken(mitte + Vector2(0.0, -10.0), UiStil.KAUFEN, 22 if viele else 12)
	if station_bild.x >= 0.0:
		saft.funken(station_bild, UiStil.GOLD if stern else UiStil.KAUFEN, 18 if (viele or stern) else 10)

	if stern:
		saft.blitz(UiStil.GOLD, 0.25, 0.15)
		var ziel: Vector2 = _sterne_platz.get_global_rect().get_center()
		if hud.marker != null:
			hud.marker.stern_moment(station_id, ziel)
		else:
			saft.flug("stern", _stern_balken.get_global_rect().get_center(), ziel)
		var anker: Vector2 = station_bild if station_bild.x >= 0.0 else mitte + Vector2(0.0, -220.0)
		saft.aufschlag(anker, UiText.t("meilenstein_faktor") % faktor_text(station.meilenstein_faktor))
		saft.konfetti(ziel, 28)


## Wo die Station gerade im Bild steht -- (-1, -1), wenn sie nicht zu sehen ist.
func _station_im_bild(hud: Hud) -> Vector2:
	if hud == null or hud.marker == null or hud.marker.kamera == null:
		return Vector2(-1.0, -1.0)
	var pos: Variant = hud.marker.station_positionen.get(station_id)
	if pos == null:
		return Vector2(-1.0, -1.0)
	var welt: Vector3 = (pos as Vector3) + Vector3(0.0, 1.0, 0.0)
	if hud.marker.kamera.is_position_behind(welt):
		return Vector2(-1.0, -1.0)
	return hud.marker.kamera.unproject_position(welt)
