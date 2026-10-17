## Das Raum-Panel (W2e): Tipp auf die Raumplakette, Sheet im Stil von Idle Bank Tycoon.
##
## Von oben nach unten:
##   1. Kopf: Raumname gross, darunter Einnahmen je Sekunde und Fortschritt in %,
##      links/rechts ‹ › zum vorigen/naechsten gekauften Raum, rechts das Kreuz.
##   2. Zwei Reiter: Ausbau und Team.
##   3. Ausbau: EINE grosse Kaufpille fuer die gewaehlte (zuerst: beste) Verbesserung,
##      darunter ein Raster aller Verbesserungen mit Symbol, Stufe und gruenem Pfeil,
##      wenn bezahlbar. Ein Tipp auf eine Kachel waehlt sie fuer die Pille.
##      Team: je Station mit Crew eine Portraetkarte mit Rang und Kaufpille.
##
## Nach einem Kauf kommt kein Fenster: die Zahl im Kopf springt, ein Glanz huscht
## ueber die Pille, das Panel bleibt offen und aktualisiert sich. Geschlossen wird es
## nur per Kreuz oder per Wisch im Kopf (Sheet), nie beim Scrollen in der Liste.
##
## Alle Kaeufe gehen als Kommando an den Kern (kaufe_empfehlung, kaufe_crew,
## kaufe_bereich); das Panel rechnet nichts selbst, es fragt und zeigt.
class_name RaumPanel
extends Sheet

signal abgelehnt
## Ein Kauf: Position des Knopfes und Text (z. B. "+3,2 €/s").
signal ausgegeben(von: Vector2, text: String)
## "Raum ansehen" angetippt.
signal raum_ansehen(id: StringName)
## Mit ‹ › zu einem anderen Raum gewechselt (die Hud schiebt die Karte hin, falls verdeckt).
signal raum_gewechselt(id: StringName)

const REITER_AUSBAU: int = 0
const REITER_TEAM: int = 1

var kern: GameCore
var thema: ThemeData
var bereich_id: StringName = &""
## Die gerade gezeigte Verbesserung (Form von GameCore.empfehlung). Leer = Raumkauf
## oder nichts mehr offen. Die Pille kauft genau das, was zu sehen ist.
var vorschlag: Dictionary = {}
var reiter: int = REITER_AUSBAU

var _unter: Label
var _balken: ProgressBar
var _zurueck: Button
var _vor: Button
var _reiter_zeile: HBoxContainer
var _reiter_knoepfe: Array[Button] = []
var _team_punkt: Control
var _knopf: Button
var _knopf_preis: Label
var _fehlt: Label
var _scroll: WischScroll
## Mindesthoehe der Karte beim Blaettern mit ‹ › (0 = keine); zurueckgesetzt bei jedem Oeffnen.
var _hoehe_halten: float = 0.0
var _scroll_inhalt: VBoxContainer
var _info: Label
var _raster: GridContainer
var _team_raster: GridContainer
var _leer: Label
var _ansehen: Button

var _auswahl: String = ""
## K7: "noch nie gebaut". Eine leere Liste hat die Signatur "" -- mit "" als Ruecksetzwert blieben
## beim Wechsel in einen Raum ohne Kaeufe die Kacheln des VORIGEN Raums stehen.
const SIG_NEU: String = "-"
var _raster_sig: String = SIG_NEU
var _team_sig: String = SIG_NEU
var _einkommen: float = -1.0
var _prozent: int = 0
var _zahl_tween: Tween
var _nach_kauf: bool = false
## Die Verbesserungen dieses Durchlaufs (einmal je aktualisiere() gerechnet).
var _k_liste: Array[Dictionary] = []


func _init() -> void:
	super()
	_baue_kopf()
	inhalt.add_theme_constant_override("separation", UiStil.A3)
	_baue_reiter()
	_baue_pille()
	_baue_liste()


# --- Aufbau --------------------------------------------------------------------------

func _baue_kopf() -> void:
	var b: float = float(Sheet.konfig_wert("raum_panel", "pfeil_b", 56.0))
	_zurueck = _pfeil("‹", UiText.t("rp_voriger"), b)
	_zurueck.pressed.connect(func() -> void: _wechsle(-1))
	kopf.add_child(_zurueck)
	kopf.move_child(_zurueck, 0)

	var mitte := VBoxContainer.new()
	mitte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mitte.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	mitte.add_theme_constant_override("separation", 0)
	mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kopf.add_child(mitte)
	kopf.move_child(mitte, 1)
	titel.reparent(mitte)
	titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	titel.size_flags_horizontal = Control.SIZE_FILL
	_unter = UiStil.label("", UiStil.GR_TEXT, UiStil.akzent_text(), UiStil.FETT)
	_unter.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mitte.add_child(_unter)
	_balken = UiStil.neuer_balken(10.0, UiStil.KAUFEN)
	_balken.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var balken_rahmen := MarginContainer.new()
	balken_rahmen.add_theme_constant_override("margin_left", UiStil.A4)
	balken_rahmen.add_theme_constant_override("margin_right", UiStil.A4)
	balken_rahmen.add_theme_constant_override("margin_top", UiStil.A1)
	balken_rahmen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	balken_rahmen.add_child(_balken)
	mitte.add_child(balken_rahmen)

	_vor = _pfeil("›", UiText.t("rp_naechster"), b)
	_vor.pressed.connect(func() -> void: _wechsle(1))
	kopf.add_child(_vor)
	kopf.move_child(_vor, kopf.get_child_count() - 2)


func _pfeil(zeichen: String, hinweis: String, breite: float) -> Button:
	var k := Button.new()
	k.tooltip_text = hinweis
	k.focus_mode = Control.FOCUS_NONE
	k.custom_minimum_size = Vector2(breite, maxf(breite, UiStil.TIPPZIEL * 0.8))
	k.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	UiStil.faerbe_knopf(k, UiStil.PAPIER)
	# Der Winkel wird gezeichnet statt gesetzt: ein Schriftzeichen sitzt je nach
	# Schrift zu klein oder zu tief.
	var richtung: float = -1.0 if zeichen == "‹" else 1.0
	var winkel := Control.new()
	winkel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	winkel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	winkel.draw.connect(func() -> void:
		var m: Vector2 = winkel.size * 0.5 + Vector2(-richtung * 3.0, -1.0)
		var punkte := PackedVector2Array([m + Vector2(-richtung * 9.0, -16.0), m + Vector2(richtung * 9.0, 0.0),
			m + Vector2(-richtung * 9.0, 16.0)])
		winkel.draw_polyline(punkte, UiStil.TINTE, 6.0, true)
		for pkt in [punkte[0], punkte[2]]:
			winkel.draw_circle(pkt, 3.0, UiStil.TINTE)
		winkel.draw_circle(punkte[1], 3.0, UiStil.TINTE))
	k.add_child(winkel)
	return k


func _baue_reiter() -> void:
	_reiter_zeile = HBoxContainer.new()
	_reiter_zeile.add_theme_constant_override("separation", UiStil.A2)
	inhalt.add_child(_reiter_zeile)
	var h: float = float(Sheet.konfig_wert("raum_panel", "reiter_h", 56.0))
	for i in range(2):
		var k := Button.new()
		k.focus_mode = Control.FOCUS_NONE
		k.custom_minimum_size = Vector2(0.0, h)
		k.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		k.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		k.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		var index: int = i
		k.pressed.connect(func() -> void:
			# K7: Die Liste beginnt oben -- sonst stand der Team-Reiter mitten in der ersten Karte,
			# weil die Rollhoehe der Ausbau-Liste mitkam.
			if reiter != index:
				_scroll.scroll_vertical = 0
			reiter = index
			aktualisiere())
		_reiter_zeile.add_child(k)
		_reiter_knoepfe.append(k)
	# Gruener Punkt am Team-Reiter: dort wartet ein bezahlbarer Kauf.
	_team_punkt = PanelContainer.new()
	_team_punkt.add_theme_stylebox_override("panel", UiStil.chip(UiStil.KAUFEN, 0.0, 0.0, 0.0))
	_team_punkt.custom_minimum_size = Vector2(16.0, 16.0)
	_team_punkt.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_team_punkt.position = Vector2(-26.0, 8.0)
	_team_punkt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_team_punkt.visible = false
	_reiter_knoepfe[REITER_TEAM].add_child(_team_punkt)


func _baue_pille() -> void:
	_knopf = UiStil.kaufpille({"hoehe": float(Sheet.konfig_wert("raum_panel", "pille_h", 104.0)),
		"titel": "", "preis": "", "zustand": "nicht"})
	_knopf.pressed.connect(_auf_kauf)
	inhalt.add_child(_knopf)
	_knopf_preis = (_knopf.get_meta("teile") as Dictionary)["preis"] as Label
	_fehlt = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT)
	_fehlt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	inhalt.add_child(_fehlt)


func _baue_liste() -> void:
	_scroll = WischScroll.new()
	_scroll.custom_minimum_size = Vector2(0.0, 120.0)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	inhalt.add_child(_scroll)
	_scroll_inhalt = VBoxContainer.new()
	_scroll_inhalt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll_inhalt.add_theme_constant_override("separation", UiStil.A2)
	_scroll.add_child(_scroll_inhalt)
	# Der Raster-Rahmen entsteht erst mit den Spalten aus sheet.json.
	_info = UiStil.label("", UiStil.GR_TEXT, UiStil.PLUS_TEXT, UiStil.FETT)
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_scroll_inhalt.add_child(_info)
	_raster = _neues_raster(int(Sheet.konfig_wert("raum_panel", "spalten", 3)))
	_scroll_inhalt.add_child(_raster)
	_team_raster = _neues_raster(int(Sheet.konfig_wert("raum_panel", "team_spalten", 2)))
	_scroll_inhalt.add_child(_team_raster)
	_leer = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT)
	_leer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_leer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_scroll_inhalt.add_child(_leer)

	# Klein und ruhig: in den Raum fahren (wie bisher der Tipp auf die Plakette).
	_ansehen = Button.new()
	_ansehen.text = UiText.t("raum_ansehen")
	_ansehen.focus_mode = Control.FOCUS_NONE
	_ansehen.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL)
	_ansehen.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
	_ansehen.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
	for farbe_name in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		_ansehen.add_theme_color_override(farbe_name, UiStil.TINTE_2)
	for zustand in ["normal", "hover", "pressed", "focus"]:
		_ansehen.add_theme_stylebox_override(zustand, StyleBoxEmpty.new())
	_ansehen.set_meta("gestylt", true)
	_ansehen.pressed.connect(func() -> void: raum_ansehen.emit(bereich_id))
	_scroll_inhalt.add_child(_ansehen)
	# Eine geaenderte Inhaltshoehe (Zeilenumbruch, neue Kacheln) misst die Hoehe neu.
	_scroll_inhalt.minimum_size_changed.connect(_passe_hoehe)


func _neues_raster(spalten: int) -> GridContainer:
	var g := GridContainer.new()
	g.columns = maxi(spalten, 1)
	g.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	g.add_theme_constant_override("h_separation", UiStil.A2)
	g.add_theme_constant_override("v_separation", UiStil.A2)
	return g


# --- Oeffnen und Raumwechsel ---------------------------------------------------------

func zeige_bereich(id: StringName) -> void:
	if id != bereich_id and _scroll != null:
		_scroll.scroll_vertical = 0
	bereich_id = id
	vorschlag = {}
	_auswahl = ""
	_raster_sig = SIG_NEU
	_team_sig = SIG_NEU
	_einkommen = -1.0
	_nach_kauf = false
	_hoehe_halten = 0.0
	oeffnen()


func ist_start() -> bool:
	return bereich_id == GameCore.START_RAUM


func _gekauft_id(id: StringName) -> bool:
	return id == GameCore.START_RAUM or kern.bereiche.ist_gekauft(id)


func _gekauft() -> bool:
	return _gekauft_id(bereich_id)


## Alle Raeume der Welt in Reihenfolge: zuerst die Startzone, dann die Bereiche.
func _raeume() -> Array[StringName]:
	var liste: Array[StringName] = []
	if kern.welten != null and not kern.welten.startzone(kern.welt_index).is_empty():
		liste.append(GameCore.START_RAUM)
	for id in kern.bereiche.ids():
		liste.append(id)
	return liste


## Der naechste gekaufte Raum in Richtung `richtung` (1 oder -1), rundherum. Leer = keiner.
func nachbar_raum(richtung: int) -> StringName:
	var alle: Array[StringName] = _raeume()
	var n: int = alle.size()
	var i: int = alle.find(bereich_id)
	if n == 0 or i < 0:
		return &""
	for schritt in range(1, n):
		var kandidat: StringName = alle[posmod(i + schritt * richtung, n)]
		if kandidat != bereich_id and _gekauft_id(kandidat):
			return kandidat
	return &""


func _wechsle(richtung: int) -> void:
	var ziel: StringName = nachbar_raum(richtung)
	if ziel == &"":
		return
	Haptik.puls(10)
	# K7: Beim Blaettern bleibt das Panel mindestens so hoch wie eben -- sonst sprangen Pfeile
	# und X mit jeder Raumhoehe, und der naechste Tipp auf "›" traf die Karte (Panel zu).
	var halten: float = karte.get_combined_minimum_size().y
	zeige_bereich(ziel)
	_hoehe_halten = halten
	_passe_hoehe()
	raum_gewechselt.emit(ziel)


# --- Zahlen des Raums ----------------------------------------------------------------

## Einnahmen des Raums je Sekunde. Die Kette verdient gemeinsam; jede freigeschaltete
## Station traegt gleich viel, der Raum die Summe seiner Stationen.
static func raum_einkommen(kern_: GameCore, id: StringName) -> float:
	var aktiv: int = 0
	for sid in Ids.ALL_STATIONS:
		var s: StationModel = kern_.kette.station(sid)
		if s != null and s.freigeschaltet:
			aktiv += 1
	if aktiv == 0:
		return 0.0
	var hier: int = 0
	for sid in kern_._stationen_im_raum(id):
		var s2: StationModel = kern_.kette.station(sid)
		if s2 != null and s2.freigeschaltet:
			hier += 1
	return kern_.einkommen_pro_sekunde() * float(hier) / float(aktiv)


## Wie weit ein Raum ausgebaut ist (0..1): Stufen aller Stationen und Ausstattungen
## im Verhaeltnis zu ihren Hoechststufen. Ohne Hoechststufe zaehlt die Station nicht.
static func raum_fortschritt(kern_: GameCore, id: StringName) -> float:
	var ist: float = 0.0
	var soll: float = 0.0
	for sid in kern_._stationen_im_raum(id):
		var s: StationModel = kern_.kette.station(sid)
		if s == null or not s.freigeschaltet:
			continue
		if s.max_stufe > 0:
			ist += float(mini(s.stufe, s.max_stufe))
			soll += float(s.max_stufe)
		for p in s.ausstattung:
			ist += float(mini(p.stufe, p.max_stufe))
			soll += float(p.max_stufe)
	return clampf(ist / soll, 0.0, 1.0) if soll > 0.0 else 0.0


# --- Aktualisieren -------------------------------------------------------------------

func aktualisiere() -> void:
	if bereich_id == &"" or kern == null:
		return
	var name: String = WeltTexte.bereich(thema, bereich_id, "name")
	if name.is_empty() and ist_start():
		name = WeltTexte.kette(thema, "start")
	if name.is_empty() and thema != null:
		name = thema.welt_name
	titel.text = name
	var gekauft: bool = _gekauft()
	_zurueck.visible = nachbar_raum(-1) != &""
	_vor.visible = nachbar_raum(1) != &""
	_zeige_kopfzahlen(gekauft)
	var team_da: bool = gekauft and _team_stationen().size() > 0 and kern.ist_frei("crew")
	if not team_da:
		reiter = REITER_AUSBAU
	_reiter_zeile.visible = gekauft and team_da
	_scroll.visible = true
	_ansehen.visible = reiter == REITER_AUSBAU
	_zeige_reiter(team_da)
	if not gekauft:
		_zeige_raumkauf()
	elif reiter == REITER_TEAM:
		_zeige_team()
	else:
		_k_liste = _kaeufe()
		_zeige_verbesserung()
		_zeige_raster()
	_passe_hoehe()
	_passe_hoehe.call_deferred()


func _zeige_kopfzahlen(gekauft: bool) -> void:
	if not gekauft:
		_unter.text = UiText.t("gesperrt") if not kern.bereiche.verfuegbar(bereich_id) else UiText.t("rp_nicht_gekauft")
		_balken.value = 0.0
		_balken.visible = false
		return
	_balken.visible = true
	var anteil: float = raum_fortschritt(kern, bereich_id)
	_prozent = int(floorf(anteil * 100.0 + 0.0001))
	_balken.value = anteil
	var neu: float = raum_einkommen(kern, bereich_id)
	var alt: float = _einkommen
	_einkommen = neu
	var laeuft: bool = _zahl_tween != null and _zahl_tween.is_running()
	if _nach_kauf and alt >= 0.0 and neu > alt and is_inside_tree():
		_nach_kauf = false
		if _zahl_tween != null:
			_zahl_tween.kill()
		_zahl_tween = create_tween()
		_zahl_tween.tween_method(_schreibe_kopfzeile, alt, neu,
			float(Sheet.konfig_wert("raum_panel", "zahl_springt_s", 0.45))).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		UiStil.aufploppen(_unter, 1.14)
	elif not laeuft:
		_nach_kauf = false
		_schreibe_kopfzeile(neu)


func _schreibe_kopfzeile(wert: float) -> void:
	# Ein reiner Bonusraum hat keine Stationen: statt "0 €/s · 0 %" sein Bonus (QA 17.10.).
	if kern != null and bereich_id != &"" and kern._stationen_im_raum(bereich_id).is_empty():
		var faktor: float = float(kern.bereich_info(bereich_id).get("bonus_faktor", 1.0))
		if faktor > 1.0:
			_unter.text = UiText.t("rp_bonus") % String.num(faktor, 2).replace(".", ",")
			return
	_unter.text = "%s  ·  %s" % [UiText.t("rp_pro_sekunde") % UiStil.zahl(wert), UiText.t("rp_prozent") % _prozent]


func _zeige_reiter(team_da: bool) -> void:
	var team_stationen: Array[StringName] = _team_stationen()
	var angeheuert: int = 0
	var frei_kauf: bool = false
	for sid in team_stationen:
		if kern.crew_rang(sid) > 0:
			angeheuert += 1
		var naechster: Dictionary = _naechster_rang(sid)
		if not naechster.is_empty() and bool(naechster["kaufbar"]):
			frei_kauf = true
	_reiter_knoepfe[REITER_AUSBAU].text = UiText.t("rp_reiter_ausbau")
	_reiter_knoepfe[REITER_TEAM].text = "%s  %d/%d" % [UiText.t("rp_reiter_team"), angeheuert, team_stationen.size()]
	for i in range(2):
		UiStil.faerbe_knopf(_reiter_knoepfe[i], UiStil.TINTE if i == reiter else UiStil.PAPIER_2)
	_team_punkt.visible = team_da and frei_kauf and reiter != REITER_TEAM


# --- Gesperrter Raum: der Raumkauf ---------------------------------------------------

func _zeige_raumkauf() -> void:
	vorschlag = {}
	_raster.visible = false
	_team_raster.visible = false
	_leer.visible = false
	var eigen: Texture2D = UiStil.bereich_bild(thema, kern.welt_id(), bereich_id)
	var station_id: StringName = GameCore._station_zu_freischaltung(kern.bereiche.schaltet_frei(bereich_id))
	var danach: String = WeltTexte.bereich(thema, bereich_id, "danach")
	if danach.is_empty() and station_id != &"":
		danach = UiText.t("raum_danach") % WeltTexte.station_name(thema, station_id)
	var bonus: String = ""
	if not kern.bereiche.bonus(bereich_id).is_empty():
		bonus = WeltTexte.bonus(thema, kern, bereich_id).split(" · ")[0]
	_info.text = bonus
	_info.visible = not bonus.is_empty()
	var preis: float = kern.bereiche.kosten(bereich_id)
	var daten: Dictionary = {"hoehe": float(Sheet.konfig_wert("raum_panel", "pille_h", 104.0)),
		"symbol": eigen if eigen != null else UiStil.symbol("haus"),
		"titel": UiText.t("rp_kaufen"), "nutzen": danach, "preis": UiStil.preis(preis),
		"zustand": "kaufbar" if kern.kapital >= preis else "nicht"}
	if not kern.bereiche.verfuegbar(bereich_id):
		var wartet: String = WeltTexte.bereich(thema, bereich_id, "wartet")
		daten["zustand"] = "gesperrt"
		daten["preis"] = wartet if not wartet.is_empty() else UiText.t("gesperrt")
		daten["nutzen"] = UiStil.preis(preis) + " €"
		_fehlt.visible = false
	else:
		_setze_fehlt(preis)
	_knopf.visible = true
	UiStil.kaufpille(daten, _knopf)


# --- Gekaufter Raum: die gewaehlte Verbesserung --------------------------------------

func _kaeufe() -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for k in kern.kaeufe_im_raum(bereich_id):
		if String(k["art"]) != "crew":
			liste.append(k)
	return liste


static func _schluessel(k: Dictionary) -> String:
	return "%s|%s|%s" % [k["art"], k["station"], k["platz"]]


func _zeige_verbesserung() -> void:
	_scroll.visible = true
	_leer.visible = false
	_info.visible = false
	_team_raster.visible = false
	_raster.visible = true
	vorschlag = {}
	if not _auswahl.is_empty():
		for k in _k_liste:
			if _schluessel(k) == _auswahl:
				vorschlag = k
		if vorschlag.is_empty():
			_auswahl = ""
	if vorschlag.is_empty():
		vorschlag = kern.empfehlung_im_raum(bereich_id)
		if String(vorschlag.get("art", "")) == "crew":
			vorschlag = {}
			var rest: Array[Dictionary] = _k_liste.duplicate()
			if not rest.is_empty():
				rest.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
					return float(a["preis"]) < float(b["preis"]))
				vorschlag = rest[0]
	if vorschlag.is_empty():
		_knopf.visible = false
		_fehlt.visible = false
		_leer.text = UiText.t("rp_ausbau_leer")
		_leer.visible = true
		return
	_knopf.visible = true
	var b: Dictionary = _beschreibe(vorschlag)
	var mehr: float = float(vorschlag["mehr"])
	var nutzen: String = String(b["name"])
	if mehr > maxf(kern.einkommen_pro_sekunde() * 0.001, 0.01):
		nutzen += "  ·  " + UiText.t("einnahmen_plus") % UiStil.zahl(mehr)
	else:
		var engpass: StringName = kern.kette.bottleneck()
		var sid: StringName = StringName(String(vorschlag["station"]))
		if engpass != &"" and engpass != sid:
			nutzen += "  ·  " + UiText.t("engpass_ist") % WeltTexte.station_name(thema, engpass)
	var preis: float = float(vorschlag["preis"])
	UiStil.kaufpille({"hoehe": float(Sheet.konfig_wert("raum_panel", "pille_h", 104.0)),
		"symbol": b["bild"], "titel": UiText.t("rp_verbessern"), "nutzen": nutzen,
		"preis": UiStil.preis(preis), "zustand": "kaufbar" if kern.kapital >= preis else "nicht"}, _knopf)
	_setze_fehlt(preis)


## Bild, Name und Stufe eines Kaufs.
func _beschreibe(k: Dictionary) -> Dictionary:
	var sid: StringName = StringName(String(k["station"]))
	var s: StationModel = kern.kette.station(sid)
	match String(k["art"]):
		"platz":
			var pid: StringName = StringName(String(k["platz"]))
			var p: EquipmentSlot = s.platz(pid)
			return {"bild": _icon("%s_%s_%d" % [sid, pid, maxi(p.modellstufe(), 1)]),
				"name": WeltTexte.platz_name(thema, sid, pid), "stufe": p.stufe}
		"crew":
			return {"bild": UiStil.symbol("werkzeug"), "name": UiText.t("crew_anheuern"), "stufe": kern.crew_rang(sid)}
	return {"bild": _icon(String(sid)), "name": WeltTexte.station_name(thema, sid), "stufe": s.stufe}


func _icon(datei: String) -> Texture2D:
	var pfad: String = Stationsmenue.ICON_PFAD % [kern.welt_id(), datei]
	return load(pfad) as Texture2D if ResourceLoader.exists(pfad) else UiStil.symbol("werkzeug")


func _setze_fehlt(preis: float) -> void:
	var fehlt: float = preis - kern.kapital
	_fehlt.visible = fehlt > 0.0
	if _fehlt.visible:
		_fehlt.text = UiText.t("noch_euro") % UiStil.preis(fehlt)


# --- Das Raster ----------------------------------------------------------------------

func _zeige_raster() -> void:
	var kaeufe: Array[Dictionary] = _k_liste
	var teile: PackedStringArray = PackedStringArray()
	for k in kaeufe:
		var b: Dictionary = _beschreibe(k)
		teile.append("%s|%d|%s|%s" % [_schluessel(k), int(b["stufe"]), kern.kapital >= float(k["preis"]),
			_schluessel(k) == _schluessel(vorschlag) if not vorschlag.is_empty() else false])
	var sig: String = ";".join(teile)
	if sig == _raster_sig:
		return
	_raster_sig = sig
	for kind in _raster.get_children():
		_weg(kind)
	for k in kaeufe:
		_raster.add_child(_kachel(k))
	_raster.visible = not kaeufe.is_empty()


## Eine Kachel: Symbol, Stufe, Preis klein, rechts oben der Pfeil (gruen = bezahlbar).
func _kachel(k: Dictionary) -> Control:
	var b: Dictionary = _beschreibe(k)
	var preis: float = float(k["preis"])
	var frei: bool = kern.kapital >= preis
	var gewaehlt: bool = not vorschlag.is_empty() and _schluessel(k) == _schluessel(vorschlag)
	var kachel := Button.new()
	kachel.focus_mode = Control.FOCUS_NONE
	kachel.clip_contents = true
	kachel.custom_minimum_size = Vector2(0.0, float(Sheet.konfig_wert("raum_panel", "kachel_h", 112.0)))
	kachel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	UiStil.setze_kaufkontur(kachel, gewaehlt)
	UiStil.faerbe_knopf(kachel, UiStil.PAPIER if frei else UiStil.PAPIER_2)
	kachel.tooltip_text = String(b["name"])
	var zeile := HBoxContainer.new()
	zeile.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	zeile.offset_left = float(UiStil.A3)
	zeile.offset_right = -float(UiStil.A2)
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kachel.add_child(zeile)
	var bild := TextureRect.new()
	bild.texture = b["bild"] as Texture2D
	bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	bild.custom_minimum_size = Vector2(60.0, 60.0)
	bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bild.modulate = Color.WHITE if frei else Color(1, 1, 1, 0.8)
	zeile.add_child(bild)
	var spalte := VBoxContainer.new()
	spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	spalte.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	spalte.add_theme_constant_override("separation", -2)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(spalte)
	spalte.add_child(UiStil.label(UiText.t("rp_stufe_kurz") % int(b["stufe"]), UiStil.GR_TEXT,
		UiStil.TINTE, UiStil.FETT))
	var preis_l := UiStil.label(UiStil.preis(preis), UiStil.GR_KLEIN, UiStil.PLUS_TEXT if frei else UiStil.TINTE_2,
		UiStil.FETT)
	preis_l.clip_text = true
	spalte.add_child(preis_l)
	var pfeil := UiStil.symbolbild("kaufpfeil", 30.0)
	pfeil.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	pfeil.position = Vector2(-36.0, 6.0)
	pfeil.modulate = Color.WHITE if frei else Color(0.55, 0.55, 0.55, 0.45)
	kachel.add_child(pfeil)
	var key: String = _schluessel(k)
	kachel.pressed.connect(func() -> void:
		_auswahl = key
		_raster_sig = SIG_NEU
		Haptik.puls(10)
		aktualisiere())
	return kachel


# --- Team ----------------------------------------------------------------------------

func _team_stationen() -> Array[StringName]:
	var liste: Array[StringName] = []
	for sid in kern._stationen_im_raum(bereich_id):
		var s: StationModel = kern.kette.station(sid)
		if s != null and s.freigeschaltet and kern.crew_hat(sid):
			liste.append(sid)
	return liste


func _naechster_rang(sid: StringName) -> Dictionary:
	for r in kern.crew_raenge(sid):
		if bool(r["naechster"]):
			return r
	return {}


func _zeige_team() -> void:
	_scroll.visible = true
	_knopf.visible = false
	_fehlt.visible = false
	_info.visible = false
	_raster.visible = false
	_team_raster.visible = true
	_leer.visible = false
	vorschlag = {}
	var stationen: Array[StringName] = _team_stationen()
	var teile: PackedStringArray = PackedStringArray()
	for sid in stationen:
		var n: Dictionary = _naechster_rang(sid)
		teile.append("%s|%d|%s|%s" % [sid, kern.crew_rang(sid), kern.crew_frei(sid),
			bool(n["kaufbar"]) if not n.is_empty() else "max"])
	var sig: String = ";".join(teile)
	if sig == _team_sig:
		return
	_team_sig = sig
	for kind in _team_raster.get_children():
		_weg(kind)
	for sid in stationen:
		_team_raster.add_child(_team_karte(sid))
	_leer.text = UiText.t("rp_team_leer")
	_leer.visible = stationen.is_empty()


## Eine Portraetkarte: Figur, Name, Titel, Rang 0-3 als Sterne, darunter die Kaufpille.
func _team_karte(sid: StringName) -> Control:
	var daten: Dictionary = thema.abschnitt("crew").get(String(sid), {}) as Dictionary if thema != null else {}
	var station_name: String = WeltTexte.station_name(thema, sid)
	var name: String = String(daten.get("name", ""))
	var rang: int = kern.crew_rang(sid)
	var raenge: Array[Dictionary] = kern.crew_raenge(sid)
	var frei: bool = kern.crew_frei(sid)
	var titel_liste: Array = daten.get("raenge", []) as Array
	var titel_text: String = String(daten.get("titel_%d" % rang, ""))
	if titel_text.is_empty() and rang > 0 and rang <= titel_liste.size():
		titel_text = String(titel_liste[rang - 1])
	if titel_text.is_empty():
		titel_text = String(daten.get("rolle", "")) if frei else UiText.t("crew_gesperrt")
	if titel_text.is_empty():
		titel_text = station_name

	var karte_t := Sheet.innenkarte(float(UiStil.A3))
	karte_t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A2)
	karte_t.add_child(spalte)
	var oben := HBoxContainer.new()
	oben.add_theme_constant_override("separation", UiStil.A3)
	oben.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(oben)
	var avatar: PanelContainer = UiStil.crew_avatar(String(daten.get("portrait", "")),
		name if not name.is_empty() else station_name, 84.0)
	if rang == 0:
		avatar.modulate = Color(1, 1, 1, 0.55)
	oben.add_child(avatar)
	var text := VBoxContainer.new()
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	text.add_theme_constant_override("separation", 0)
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	oben.add_child(text)
	var name_l := UiStil.label(name if not name.is_empty() else station_name, UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	name_l.clip_text = true
	name_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	text.add_child(name_l)
	var titel_l := UiStil.label(titel_text, UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT)
	titel_l.clip_text = true
	titel_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	text.add_child(titel_l)
	text.add_child(Sheet.sterne(rang, maxi(raenge.size(), 3), 24.0))

	var n: Dictionary = _naechster_rang(sid)
	var zustand: String = "nicht"
	var pille_text: String = UiText.t("crew_voll")
	if n.is_empty():
		zustand = "fertig"
	elif not frei:
		zustand = "gesperrt"
		var bedingung: bool = not kern.crew.frei_bedingung(sid).is_empty()
		pille_text = UiText.t("crew_gesperrt") if bedingung else UiText.t("ab_stufe") % kern.crew.frei_ab_stufe
	else:
		zustand = "kaufbar" if bool(n["kaufbar"]) else "nicht"
		pille_text = "%s  %s" % [UiText.t("rp_anheuern") if rang == 0 else UiText.t("rp_befoerdern"),
			UiStil.preis(float(n["kosten"]))]
	var pille: Button = UiStil.kaufpille({"hoehe": UiStil.KNOPF_SEKUNDAER_H, "zustand": zustand,
		"preis": pille_text})
	pille.custom_minimum_size = Vector2(0.0, UiStil.KNOPF_SEKUNDAER_H)
	pille.pressed.connect(func() -> void: _kaufe_crew(sid, pille))
	spalte.add_child(pille)
	return karte_t


func _kaufe_crew(sid: StringName, pille: Button) -> void:
	var von: Vector2 = pille.get_global_rect().get_center()
	var vorher: float = kern.einkommen_pro_sekunde()
	if kern.kaufe_crew(sid):
		var mehr: float = kern.einkommen_pro_sekunde() - vorher
		_nach_kauf = true
		Haptik.puls(Haptik.DAUER_KAUF)
		ausgegeben.emit(von, UiText.t("einnahmen_plus") % UiStil.zahl(mehr) if mehr > 0.01 else "")
	else:
		abgelehnt.emit()
	_team_sig = SIG_NEU
	aktualisiere()


# --- Kaufen --------------------------------------------------------------------------

func _auf_kauf() -> void:
	var von: Vector2 = _knopf.get_global_rect().get_center()
	if not _gekauft():
		if kern.kaufe_bereich(bereich_id):
			ausgegeben.emit(von, "")
			# Der Raum-Moment (Kamera, Konfetti, Nachricht) uebernimmt.
			schliessen()
		else:
			abgelehnt.emit()
			aktualisiere()
		return
	if vorschlag.is_empty():
		return
	var vorher: float = kern.einkommen_pro_sekunde()
	if kern.kaufe_empfehlung(vorschlag):
		var mehr: float = kern.einkommen_pro_sekunde() - vorher
		_nach_kauf = true
		Haptik.puls(Haptik.DAUER_KAUF)
		pille_glanz(_knopf)
		ausgegeben.emit(von, UiText.t("einnahmen_plus") % UiStil.zahl(mehr) if mehr > 0.01 else "")
	else:
		abgelehnt.emit()
		Haptik.puls(8)
	# Offen bleiben und die naechste Verbesserung zeigen (Kaufserie).
	_raster_sig = SIG_NEU
	aktualisiere()


# --- Hoehe ---------------------------------------------------------------------------

## Das Panel deckt die Welt nie weiter zu als `max_anteil` der Bildhoehe (samt
## Menueleiste): nur die Liste scrollt, Kopf, Reiter und Pille bleiben stehen.
func _passe_hoehe() -> void:
	if _scroll == null or not is_inside_tree():
		return
	var rest: float = karte.get_combined_minimum_size().y - _scroll.custom_minimum_size.y
	var grenze: float = maxf(max_kartenhoehe(float(Sheet.konfig_wert("raum_panel", "max_anteil", 0.45))) - rest, 112.0)
	var wunsch: float = _scroll_inhalt.get_combined_minimum_size().y
	# _hoehe_halten gilt fuer die ganze Karte: Ohne Reiter/Pille (Raum ohne Kaeufe) waechst die Liste.
	var neu: float = minf(maxf(wunsch, _hoehe_halten - rest), grenze)
	if absf(neu - _scroll.custom_minimum_size.y) > 1.0:
		_scroll.custom_minimum_size.y = neu


## Alte Kacheln entsorgen: im Spiel verzoegert (ein Tipp kann gerade laufen), ausserhalb
## des Baums (Tests, keine Frames) sofort -- sonst bleiben sie als Waisen liegen.
func _weg(knoten: Node) -> void:
	if is_inside_tree():
		# Im Baum lassen, nur verstecken: so raeumt der Elternknoten sie mit ab, auch
		# wenn (wie in Tests) nie ein Frame laeuft. Versteckte Kinder ordnet kein Container ein.
		if knoten is CanvasItem:
			(knoten as CanvasItem).visible = false
		knoten.queue_free()
	else:
		knoten.get_parent().remove_child(knoten) if knoten.get_parent() != null else null
		knoten.free()
