## Die ganze Bedienoberflaeche ueber der Karte (ADR-021, docs/WELT1_TIEFE.md 8).
##
## Kopfleiste oben, Menueleiste unten, Menues dazwischen, Schilder auf der
## Karte, Rueckmeldungen obendrauf. Sie stand bis hierher als 600 Zeilen in
## main.gd -- zusammen mit Weltaufbau, Spielstand und Tutorial. Jede neue
## Anzeige machte die groesste Datei des Projekts noch groesser.
##
## Die Hud schickt Kommandos an den Kern und hoert auf seinen Bus. Sie weiss
## nicht, wie die Welt gebaut ist -- Positionen bekommt sie von main.gd.
class_name Hud
extends Control

signal station_fokus(id: StringName)
signal laden_gewuenscht
signal speichern_gewuenscht
signal tutorial_ereignis(typ: StringName, wert: Variant)
## Die Kamera soll zu einem Raum fahren (Sprung aus der Ziele-Leiste).
signal bereich_fokus(id: StringName)
## Raum-Menue (Schnellkauf/Raum-Panel) offen: die Kamera schiebt den Raum nur so weit,
## dass er ueber dem Panel steht, ohne Zoom (K6 1c, Handy-Befund 1).
signal schnellkauf_fokus(id: StringName)

## Wie oft die Anzeigen neu gerechnet werden. Das Kapital aendert sich viermal
## pro Sekunde; die Kopfleiste zaehlt ohnehin weich hoch.
const TAKT: float = 0.2
## Oberkante der Zeile aus Zielkarte und Engpass: direkt unter der Kopfleiste.
const OBEN_ZEILE: float = Kopfleiste.OBEN + Kopfleiste.HOEHE + float(UiStil.A3)
## Ertragszahlen entfallen, wenn ihr Punkt so nah ueber einem offenen Menue liegt (Steighoehe).
const UNTER_MENUE_RAND: float = 60.0
## Kleinste Schrift der Auftragskarten (11 px in der 540er-Vorschau, K6 4.7).
const AUFTRAG_SCHRIFT_MIN: int = UiStil.GR_KLEIN - 3

var kern: GameCore
var thema: ThemeData
var audio: AudioDirector
var werbung: AdService

var kopfleiste: Kopfleiste
var menueleiste: Menueleiste
var marker: Kartenmarker
var saft: Saft
var stationsmenue: Stationsmenue
var zielemenue: Menues.Zielemenue
var handymenue: Menues.Handymenue
var ausbaumenue: Menues.Ausbaumenue
var fortschrittsmenue: Menues.Fortschrittsmenue
var bereichsmenue: Menues.Bereichsmenue
var einstellungsmenue: Menues.Einstellungsmenue
var nebenraummenue: Menues.Nebenraummenue
var schnellkauf: Menues.Schnellkauf

var _sheets: Array[Sheet] = []
var _stapel: VBoxContainer
var _zielkarte: VBoxContainer
var _aufgabe_karte: PanelContainer
var _aufgabe_text: Label
var _aufgabe_balken: ProgressBar
var _aufgabe_zaehler: Label
var _aufgabe_belohnung: Label
var _segmente: SegmentBalken
var _karten_pin: PanelContainer
## Die kleinen Aufgabenkarten unter der Kopfleiste: {karte, bild, text, balken, zaehler}.
var _auftrags_karten: Array[Dictionary] = []
var auftragsbrett: Auftragsbrett
var _szene: SzeneView
## Szenen, die im Tutorial faellig wurden: Sie laufen nach dessen Ende (K2 P1d), nicht stumm im Handy.
var _szenen_nach_tutorial: Array[String] = []
## Angemeldete, noch nicht gezeigte Szenen (P1.7: nur die neueste wird ein Fenster).
var _szenen_wartend: Array[String] = []
## Zwischenmarken des Welt-Ziels, die schon gemeldet (oder beim Laden schon erreicht) waren.
var _marken_gemeldet: Dictionary = {}
var _marken_gesehen: bool = false
var _szene_ebene: CanvasLayer
var _moment_ebene: CanvasLayer
var _moment: MomentView
var _momente_wartend: Array[Dictionary] = []
## P1.9: einmalige Erklaer-Blasen an Plaketten, Kiste und Stapel.
var symbol_hinweise: SymbolHinweise
## K6 1c: Nachrichten ohne Szene als Sprechblase ueber der Figur des Absenders.
var ortsblase: OrtsBlase
## K6 1c: das laufende Kapitel als Zeile in der Zielleiste (statt Kapitelkarte).
var _kapitel_zeile: KapitelZeile
var _engpass_pille: PanelContainer
var _engpass_text: Label
var _limit_feld: PanelContainer
var _limit_label: Label
var _limit_leiste: ProgressBar
var _umbau_knopf: Button
var _limit_voll: bool = false
var _limit_kurz: Label
var _limit_kompakt: bool = false
var _chip_zeile: HBoxContainer
var _aufgabe_chip: PanelContainer
var _aufgabe_chip_text: Label
var _aufgabe_offen: bool = false
var _limit_puls: float = 0.0
var _rest: float = 0.0
var _ertrag_rest: float = 0.0
var _ertrag_summe: float = 0.0
var _station_positionen: Dictionary = {}

## Laeuft das Tutorial? Dann schweigen Zielkarte, Engpass-Hinweis und
## Abzeichen: Der Anfang zeigte sonst sieben Dinge gleichzeitig, und der Hinweis
## des Tutorials war nur eines davon.
var tutorial_aktiv: bool = false:
	set(wert):
		tutorial_aktiv = wert
		if marker != null:
			marker.tutorial_aktiv = wert
		if menueleiste != null:
			aktualisiere_leiste()
		if not wert and not _szenen_nach_tutorial.is_empty():
			_spiele_szenen_nach_tutorial.call_deferred()

## Fragt das Tutorial, ob ein Element schon da sein darf (TutorialAblauf.zeigt). Main setzt es.
var tutorial_zeigt: Callable = Callable()
## Steht die Tutorialkarte gerade mit Text im Bild? (Main setzt es; eine Textquelle zur Zeit.)
var tutorial_karte_sichtbar: Callable = Callable()

## In Welten mit Clip-Fluss zeigt jeder Clip, der die Kette verlaesst, seinen
## Ertrag selbst (zeige_clip_ertrag). Dann entfaellt die Sammelanzeige.
var clips_zeigen_ertrag: bool = false


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	theme = UiStil.thema()


func _ready() -> void:
	# Der Debug-Knopf von main.gd haengt neben der Hud in derselben Ebene. Er
	# bekommt hier den Stil des Spiels -- vorher klebte er halbdurchsichtig und
	# ohne Rand links an der Kante und sah aus wie ein Darstellungsfehler.
	var ebene: Node = get_parent()
	if ebene != null:
		ebene.child_entered_tree.connect(_auf_nachbar)
		for kind in ebene.get_children():
			_auf_nachbar(kind)


func _auf_nachbar(knoten: Node) -> void:
	if knoten is Button and knoten.get_parent() == get_parent() and not knoten.has_meta("gestylt"):
		var knopf := knoten as Button
		knopf.set_meta("gestylt", true)
		knopf.theme = UiStil.thema()
		UiStil.faerbe_knopf(knopf, UiStil.PAPIER)
		knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_KLEIN))
		knopf.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
		knopf.modulate = Color(1.0, 1.0, 1.0, 0.5)
		# Unter Tutorialkarte und Menues -- er ist ein Werkzeug, kein Teil des Spiels.
		knopf.z_index = -1
		knopf.custom_minimum_size = Vector2(0.0, 64.0)
		knopf.set_deferred("offset_left", float(UiStil.A2))
		knopf.set_deferred("offset_right", float(UiStil.A2) + 96.0)


func aufbauen(k: GameCore, t: ThemeData, a: AudioDirector, w: AdService) -> void:
	kern = k
	thema = t
	audio = a
	werbung = w
	# Werbung (K3 C1): Tageszaehler auf die Platte (nicht in Vorschauen), Belohnungen
	# der Platzierungen, die dieser Bildschirm selbst auszahlt.
	if not OS.get_cmdline_user_args().has("--frisch"):
		werbung.verbinde_speicher("user://werbung_zaehler.json")
	werbung.belohnung_verdient.connect(_auf_werbung_belohnung)
	werbung.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void: _angebot_weg())
	_melde_werbe_stand()

	marker = Kartenmarker.new()
	add_child(marker)
	marker.station_getippt.connect(zeige_station)
	marker.bereich_getippt.connect(zeige_bereich)
	marker.bereich_schnellkauf.connect(zeige_schnellkauf)
	marker.moment_getippt.connect(_auf_moment)
	marker.auftrag_getippt.connect(_auf_auftrag)
	symbol_hinweise = SymbolHinweise.new()
	symbol_hinweise.marker = marker
	symbol_hinweise.darf = _darf_symbol_erklaeren
	symbol_hinweise.gesehen_geaendert.connect(func() -> void: speichern_gewuenscht.emit())
	# Direkt ueber der Karte, unter Kopfleiste, Menues und Fenstern.
	ortsblase = OrtsBlase.new()
	ortsblase.marker = marker
	ortsblase.darf = _darf_ortsblase
	ortsblase.getippt.connect(_auf_ortsblase)
	add_child(ortsblase)

	kopfleiste = Kopfleiste.new()
	add_child(kopfleiste)
	kopfleiste.fortschritt_gedrueckt.connect(func() -> void:
		# Das Fortschritt-Menue gibt es erst ab Rang 4 -- auch nicht ueber die Kopfleiste.
		if kern.ist_frei("menue_fortschritt"):
			_oeffne(fortschrittsmenue))
	kopfleiste.einstellungen_gedrueckt.connect(func() -> void: _oeffne(einstellungsmenue))
	kopfleiste.marke_getippt.connect(_auf_marke)

	# Ein Stapel unter der Kopfleiste: Speicher-Leiste, Ziel, Tagesaufgabe, Engpass.
	# Nichts darin ueberlappt je -- jedes Element schiebt das naechste nach unten.
	_stapel = VBoxContainer.new()
	_stapel.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_stapel.offset_left = float(UiStil.A4)
	_stapel.offset_right = -float(UiStil.A4)
	_stapel.offset_top = OBEN_ZEILE
	kopfleiste.hoehe_geaendert.connect(func() -> void:
		_stapel.offset_top = kopfleiste.unterkante_ist() + float(UiStil.A3)
		_setze_oben_frei())
	_stapel.add_theme_constant_override("separation", UiStil.A2)
	_stapel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stapel)
	_baue_limit_anzeige()
	_baue_zielkarte()
	_baue_aufgabe()
	_baue_chip_zeile()
	_baue_engpass_pille()

	menueleiste = Menueleiste.new()
	add_child(menueleiste)
	menueleiste.gewaehlt.connect(_auf_menue)

	stationsmenue = Stationsmenue.new()
	zielemenue = Menues.Zielemenue.new()
	auftragsbrett = Auftragsbrett.new()
	handymenue = Menues.Handymenue.new()
	ausbaumenue = Menues.Ausbaumenue.new()
	fortschrittsmenue = Menues.Fortschrittsmenue.new()
	bereichsmenue = Menues.Bereichsmenue.new()
	einstellungsmenue = Menues.Einstellungsmenue.new()
	nebenraummenue = Menues.Nebenraummenue.new()
	schnellkauf = Menues.Schnellkauf.new()
	for s in [stationsmenue, zielemenue, auftragsbrett, handymenue, ausbaumenue, fortschrittsmenue,
			bereichsmenue, einstellungsmenue, nebenraummenue, schnellkauf]:
		var sheet: Sheet = s
		sheet.unten_frei = Menueleiste.HOEHE - 18.0
		add_child(sheet)
		_sheets.append(sheet)
	stationsmenue.abgelehnt.connect(_abgelehnt)
	ausbaumenue.abgelehnt.connect(_abgelehnt)
	bereichsmenue.abgelehnt.connect(_abgelehnt)
	bereichsmenue.werbung = werbung
	bereichsmenue.station_gewaehlt.connect(zeige_station)
	bereichsmenue.bereich_gewaehlt.connect(zeige_bereich)
	bereichsmenue.ausgegeben.connect(_auf_raum_kauf)
	bereichsmenue.ziel_gewaehlt.connect(springe_zu_ziel)
	schnellkauf.abgelehnt.connect(_abgelehnt)
	schnellkauf.ausgegeben.connect(_auf_raum_kauf)
	schnellkauf.raum_ansehen.connect(func(id: StringName) -> void:
		zeige_bereich(id)
		bereich_fokus.emit(id))
	schnellkauf.raum_gewechselt.connect(func(id: StringName) -> void: schnellkauf_fokus.emit(id))
	auftragsbrett.ziel_gewaehlt.connect(_fahre_zum_auftrag)
	auftragsbrett.eingeloest.connect(func(betrag: float, von: Vector2) -> void:
		belohnung_zeigen(betrag, von, true)
		tutorial_ereignis.emit(&"ziele_eingeloest", kern.ziele.anzahl_eingeloest()))
	zielemenue.ziel_gewaehlt.connect(springe_zu_ziel)
	zielemenue.bereich_gewaehlt.connect(zeige_bereich)
	zielemenue.bereich_gewaehlt.connect(func(id: StringName) -> void: bereich_fokus.emit(id))
	ausbaumenue.station_gewaehlt.connect(zeige_station)
	ausbaumenue.bereich_gewaehlt.connect(zeige_bereich)
	zielemenue.eingeloest.connect(func(betrag: float, von: Vector2) -> void:
		belohnung_zeigen(betrag, von, true)
		tutorial_ereignis.emit(&"ziele_eingeloest", kern.ziele.anzahl_eingeloest()))
	einstellungsmenue.laden_gedrueckt.connect(func() -> void:
		schliesse_alle()
		laden_gewuenscht.emit())
	einstellungsmenue.ton_umgeschaltet.connect(func(an: bool) -> void:
		audio.setze_ton(an)
		if an:
			audio.spiele(&"tipp")
		speichern_gewuenscht.emit())
	handymenue.geschlossen.connect(func() -> void:
		kern.nachrichten.markiere_gelesen()
		_aktualisiere_abzeichen())

	saft = Saft.new()
	saft.kopfleiste = kopfleiste
	saft.menue_hoehe = offenes_menue_hoehe
	add_child(saft)
	saft.chat_getippt.connect(func() -> void: _oeffne(handymenue))
	# Randhinweise warten, solange eine Blase oder die Tutorialkarte spricht (eine Textquelle).
	saft.halt = func() -> bool: return ortsblase.ist_offen() or symbol_hinweise.ist_offen() or _tutorial_karte()
	# Ueber Saft, unter den Fenstern (die haben eigene CanvasLayer).
	add_child(symbol_hinweise)
	var schlange: ModalSchlange = ModalSchlange.global()
	schlange.abstand_s = Kartenmarker.hinweis("fenster_abstand_s")
	# Methoden statt Lambdas: Die Schlange ist global, die Verbindung faellt mit der Hud weg.
	schlange.gezeigt.connect(_auf_fenster)
	schlange.fertig_gemeldet.connect(_auf_fenster, CONNECT_DEFERRED)

	setze_thema(t)
	_verbinde_bus()
	aktualisiere()
	kopfleiste.zeige_sofort()
	aktualisiere_leiste()


## Nach einem Weltwechsel: neuer Kern-Zustand, neues Thema, neue Positionen.
func setze_thema(t: ThemeData) -> void:
	thema = t
	# Der Akzent der Welt gilt ab jetzt ueberall. Das Thema der NAECHSTEN Welt
	# braucht der Weltwechsel-Bildschirm -- er steht schon in deren Farbe.
	var naechstes: ThemeData = null
	if kern != null and kern.welten != null and not kern.welten.ist_letzte(kern.welt_index):
		naechstes = ThemeData.laden(kern.welten.id(kern.welt_index + 1))
	UiStil.setze_welt(t, naechstes)
	if marker != null:
		marker.thema = t
	for s in _sheets:
		if "thema" in s:
			s.set("thema", t)
		if "kern" in s:
			s.set("kern", kern)
	menueleiste.setze_text(&"ausbau", WeltTexte.menue(thema, "ausbau"))
	menueleiste.setze_text(&"ziele", WeltTexte.menue(thema, "ziele"))
	menueleiste.setze_text(&"handy", WeltTexte.menue(thema, "handy"))
	menueleiste.setze_text(&"fortschritt", UiText.t("fortschritt"))
	aktualisiere_leiste()
	antworten_aus_entscheidungen()


func setze_karte(kamera: Camera3D, stationen: Dictionary, bereiche: Dictionary) -> void:
	_station_positionen = stationen
	marker.aufbauen(kern, kamera, stationen, bereiche)
	ortsblase.startpunkt = bereiche.get(Kartenmarker.START_RAUM, Vector3.INF) as Vector3
	ortsblase.leeren()


func _verbinde_bus() -> void:
	kern.bus.money_changed.connect(_auf_geld)
	kern.bus.loss_tick.connect(func(betrag: float) -> void: _auf_verlust(-betrag))
	kern.bus.area_bought.connect(_auf_bereich_gekauft)
	kern.bus.equipment_upgraded.connect(_auf_ausstattung)
	kern.bus.station_upgraded.connect(_auf_stufe)
	kern.bus.message_received.connect(_auf_nachricht)
	kern.bus.goal_completed.connect(func(id: StringName) -> void:
		audio.spiele(&"hinweis")
		_aktualisiere_abzeichen()
		if tutorial_aktiv:
			tutorial_ereignis.emit(&"ziel_erfuellt", String(id)))
	kern.bus.moment_appeared.connect(func(_id: StringName, _d: float) -> void: audio.spiele(&"blase"))
	kern.bus.rank_up.connect(_auf_rang)
	kern.bus.star_reached.connect(_auf_stern)
	kern.bus.chapter_started.connect(_auf_kapitel)
	kern.bus.boost_changed.connect(func(_f: float, _r: float) -> void: _aktualisiere_schub())


## Der Bus des Kerns wechselt mit dem Kern nicht -- aber nach einem Neuanfang
## oder Weltwechsel wird die Hud neu an denselben Kern gebunden. Deshalb nichts
## doppelt verbinden: die Hud lebt so lange wie das Spiel.


func _process(delta: float) -> void:
	if kern == null:
		return
	if _limit_voll and _limit_feld.visible:
		_limit_puls += delta
		var hell: float = 1.0 + 0.18 * (0.5 + 0.5 * sin(_limit_puls * 5.0))
		_limit_leiste.modulate = Color(hell, hell, hell)
	elif _limit_leiste.modulate != Color.WHITE:
		_limit_leiste.modulate = Color.WHITE
	# Der Kartenmarker blendet bei offenem Sheet verdeckte Abzeichen aus.
	if sheet_offen():
		marker.sheet_oben = get_viewport_rect().size.y - offenes_menue_hoehe()
	else:
		marker.sheet_oben = -1.0
	_rest -= delta
	if _rest <= 0.0:
		_rest = TAKT
		aktualisiere()
	_ertrag_rest -= delta
	# K6 1c: Spielzeit zwischen zwei Fenstern zaehlen (ModalSchlange.abstand_s).
	ModalSchlange.global().ticke(delta)
	saft.anstossen()


## Jeder Tipp ohne offenes Fenster zaehlt als Spieleraktion (Raum-Moment nach Offline wartet darauf).
func _input(ereignis: InputEvent) -> void:
	if (ereignis is InputEventScreenTouch or ereignis is InputEventMouseButton) and ereignis.is_pressed():
		ModalSchlange.global().melde_tipp()


func aktualisiere() -> void:
	var anteil: float = kern.weltwechsel_fortschritt()
	var marken: Array[Dictionary] = kern.marken_liste()
	kopfleiste.setze(kern.kapital, kern.einkommen_pro_sekunde(), _welt_leiste_text(),
		anteil, true)
	kopfleiste.setze_marken(marken)
	kopfleiste.setze_marke_hinweis(_marke_hinweis_text(anteil, marken))
	_melde_marken(anteil, marken)
	_aktualisiere_abzeichen()
	_aktualisiere_schub()
	_aktualisiere_engpass()
	_aktualisiere_limit()
	_setze_oben_frei()
	_aktualisiere_zielkarte()
	_aktualisiere_aufgabe()
	_aktualisiere_rang_chip()
	aktualisiere_leiste()
	for s in _sheets:
		if s.ist_offen():
			s.aktualisiere()


## K6 §4.6 / 1c: Der Rang-Chip ist aus der Kopfleiste weg (zwei Zahlen oben). Der Rang steht
## im Fortschritt-Menue; ein Aufstieg meldet sich EINMAL kurz am Rand (_auf_rang).
func _aktualisiere_rang_chip() -> void:
	kopfleiste.zeige_rang(false)


## Welche Menuepunkte stehen in der Leiste? Gesperrte fehlen ganz (K2 4.1, nicht ausgegraut):
## Ausbau erst nach dem Tutorial, Ziele ab Rang 2, Boost ab 3, Fortschritt ab 4, das Handy
## erst, wenn die erste Nachricht da ist (K2 5.4). Die Namen der Merkmale stehen in erfolge.json.
func menue_ist_frei(schluessel: StringName) -> bool:
	return menue_frei(schluessel, kern, tutorial_aktiv)


## Die Regel selbst, ohne Oberflaeche (testbar).
static func menue_frei(schluessel: StringName, k: GameCore, im_tutorial: bool) -> bool:
	match schluessel:
		&"ausbau":
			return not im_tutorial
		&"ziele":
			return k.ist_frei("menue_ziele")
		&"schub":
			return k.ist_frei("schub")
		&"handy":
			return not im_tutorial and not k.nachrichten.empfangen().is_empty()
		&"fortschritt":
			return k.ist_frei("menue_fortschritt")
	return true


## Menueleiste und Menues an den Rang anpassen. Billig genug fuer jeden Takt.
func aktualisiere_leiste() -> void:
	if menueleiste == null or kern == null:
		return
	for punkt in Menueleiste.PUNKTE:
		menueleiste.setze_frei(punkt, menue_ist_frei(punkt))
	# Ohne Leiste liegt das Menue am Rand statt ueber einer leeren Flaeche.
	var unten: float = Menueleiste.HOEHE - 18.0 if menueleiste.visible else 0.0
	for sh in _sheets:
		sh.unten_frei = unten


## Rang gestiegen: GENAU EIN kurzer Hinweis am Rand (Saft.MELDUNG_DAUER, <= 2 s), kein
## Fenster, kein OK (K6 1c, Bastian 16.10.). Die Leiste zeichnet neu (Freischaltungen).
func _auf_rang(rang: int, name_id: StringName) -> void:
	var rang_name: String = UiText.t(String(name_id)) if UiText.hat(String(name_id)) else ""
	var daten: Dictionary = MomentView.rang_daten(rang, rang_name, kern.erfolge.freischaltung_bei(rang),
		kern.erfolge.bonus_je_rang * 100.0)
	audio.spiele(&"levelup")
	saft.meldung(String(daten.get("titel", "")) if not String(daten.get("titel", "")).is_empty()
		else U3Text.t("moment_levelup"), String(daten.get("untertitel", "")), "pfeil_hoch")
	aktualisiere()


## Text der Welt-Ziel-Leiste: das Welt-Ziel ("Der Gaming-PC"); ohne `welt_ziel` im Thema der Weltname.
func _welt_leiste_text() -> String:
	if thema == null:
		return UiText.t("welt") % (kern.welt_index + 1)
	return WeltTexte.welt_ziel(thema)


## Name der naechsten noch nicht erreichten Zwischenmarke ("Als Nächstes: Stativ steht").
func _marke_hinweis_text(anteil: float, marken: Array[Dictionary]) -> String:
	for m in marken:
		if anteil < float(m.get("wert", 0.0)):
			var name: String = WeltTexte.marke_name(thema, String(m.get("id", "")))
			if name.is_empty():
				return ""
			var format: String = thema.text("marken_hinweis")
			return format % name if format.contains("%s") else name
	return ""


## Eine Zwischenmarke wird erreicht: K6 §3.1 Nr. 12 -- stumm. Die Leiste fuellt sich, die
## Kopfleiste nennt die naechste Marke; kein Toast mehr (Spam-Liste §3.2).
func _melde_marken(anteil: float, marken: Array[Dictionary]) -> void:
	for m in marken:
		var marke_id: String = String(m.get("id", ""))
		if anteil >= float(m.get("wert", 0.0)):
			_marken_gemeldet[marke_id] = true
	_marken_gesehen = true


func _aktualisiere_abzeichen() -> void:
	if tutorial_aktiv:
		for punkt in Menueleiste.PUNKTE:
			menueleiste.setze_abzeichen(punkt, 0)
		return
	menueleiste.setze_abzeichen(&"ziele", kern.ziele.einloesbar(kern.messwert))
	# Bei offenem Handy ist alles gelesen -- auch was gerade hereinkommt.
	if handymenue.ist_offen():
		kern.nachrichten.markiere_gelesen()
	menueleiste.setze_abzeichen(&"handy", kern.nachrichten.ungelesen())
	var kaufbar: int = 0
	for id in Ids.ALL_STATIONS:
		var s: StationModel = kern.kette.station(id)
		if s == null or not s.freigeschaltet:
			continue
		if s.kann_ausbauen() and kern.kapital >= s.naechste_kosten():
			kaufbar += 1
		for p in s.ausstattung:
			if not p.ist_max() and p.freigegeben(s.stufe) and kern.kapital >= p.naechste_kosten():
				kaufbar += 1
	menueleiste.setze_abzeichen(&"ausbau", kaufbar)


# --- Menues --------------------------------------------------------------------

func _oeffne(sheet: Sheet) -> void:
	_schliesse_andere(sheet)
	audio.spiele(&"tipp")
	sheet.oeffnen()


## Nie zwei Menues zugleich: Die anderen verschwinden sofort, ohne Ausblenden.
func _schliesse_andere(behalten: Sheet) -> void:
	for s in _sheets:
		if s != behalten and (s.ist_offen() or s.visible):
			s.schliessen_sofort()


func schliesse_alle() -> bool:
	var war_offen: bool = false
	for s in _sheets:
		if s.ist_offen():
			s.schliessen()
			war_offen = true
	return war_offen


func zeige_station(id: StringName) -> void:
	var station: StationModel = kern.kette.station(id)
	if station == null:
		return
	if not station.freigeschaltet:
		# Eine gesperrte Station fuehrt zu dem Raum, der sie freischaltet.
		for bereich_id in kern.bereiche.ids():
			if GameCore._station_zu_freischaltung(kern.bereiche.schaltet_frei(bereich_id)) == id:
				zeige_bereich(bereich_id)
				return
		return
	_schliesse_andere(stationsmenue)
	audio.spiele(&"tipp")
	stationsmenue.zeige_station(id)
	station_fokus.emit(id)
	tutorial_ereignis.emit(&"station_gewaehlt", String(id))
	if id == kern.kette.bottleneck():
		tutorial_ereignis.emit(&"engpass_gewaehlt", String(id))


## Ein Raum ohne Kauf (Bad, Pausenraum ...): Name und ein Satz statt Schweigen.
func zeige_nebenraum(zone_id: StringName) -> void:
	_schliesse_andere(nebenraummenue)
	audio.spiele(&"tipp")
	nebenraummenue.zeige_zone(zone_id)


## Ueberblick: Tipp auf eine Raum-Plakette (oder den Raum) -> Schnellkauf (K4 P1.1).
func zeige_schnellkauf(id: StringName) -> void:
	_schliesse_andere(schnellkauf)
	audio.spiele(&"tipp")
	schnellkauf.zeige_bereich(id)
	schnellkauf_fokus.emit(id)


## K6 Welle 2: Es gibt nur noch EIN Raum-Menue -- das Raum-Panel. Die alte Raumliste
## (Bereichsmenue) bleibt nur als Objekt fuer Altaufrufe bestehen.
func zeige_bereich(id: StringName) -> void:
	zeige_schnellkauf(id)


## Ein Kauf in einer Zeile des Raum-Panels: Muenzen zur Kopfleiste, der Gewinn
## als Zahl, ein kurzes Brummen. Der Ton kommt vom Bus (platz/raum).
func _auf_raum_kauf(von: Vector2, text: String) -> void:
	saft.muenzen(von, 6)
	if not text.is_empty():
		saft.betrag(von, text, UiStil.KAUFEN)
	Haptik.puls(Haptik.DAUER_KAUF)


func _auf_menue(schluessel: StringName) -> void:
	match schluessel:
		&"ausbau":
			_oeffne(ausbaumenue)
		&"ziele":
			_oeffne(zielemenue)
			tutorial_ereignis.emit(&"ziele_geoeffnet", 1)
		&"handy":
			_oeffne(handymenue)
			# Beim OEFFNEN gelesen, nicht erst beim Schliessen -- sonst stand bei
			# offenem Handy weiter "6 ungelesen" auf dem Knopf.
			kern.nachrichten.markiere_gelesen()
			_aktualisiere_abzeichen()
		&"fortschritt":
			_oeffne(fortschrittsmenue)
		&"laden":
			schliesse_alle()
			audio.spiele(&"tipp")
			laden_gewuenscht.emit()
		&"schub":
			audio.spiele(&"tipp")
			if int(kern.bogen.get("schub", 0)) == 0:
				# Der erste Boost ist ein Geschenk (K2 3, Minute 6): ohne Werbung, kuerzer.
				kern.starte_schub(float(werbung.wert(&"schub", "geschenk_sekunden", -1.0)))
				if thema != null:
					var texte: Dictionary = thema.abschnitt("belohnung")
					saft.meldung(String(texte.get("schub_titel", "")), String(texte.get("schub_text", "")), "blitz")
				return
			# Dauer-Boost: auch waehrend er laeuft nachlegen, bis zur Hoechstdauer.
			if _schub_nachlegbar():
				werbung.zeige_belohnt(&"schub")


## Passt noch eine Boost-Runde unter die Hoechstdauer, und ist ein Angebot erlaubt?
func _schub_nachlegbar() -> bool:
	if tutorial_aktiv or not werbung.ist_bereit(&"schub"):
		return false
	return kern.schub_rest + kern.balance.schub_dauer <= kern.balance.schub_hoechstdauer + 0.01


func _raum_gekauft(bereich_id: StringName) -> bool:
	return not kern.bereiche.existiert(bereich_id) or kern.bereiche.ist_gekauft(bereich_id)


## Spielzeit und Raumstand an die Werbung: Der Startschutz (nicht in den ersten
## fuenf Minuten) entscheidet dort, nicht in der Oberflaeche.
func _melde_werbe_stand() -> void:
	if werbung != null and kern != null:
		werbung.setze_stand(kern.spielzeit, Callable(self, "_raum_gekauft"))


func _aktualisiere_schub() -> void:
	_melde_werbe_stand()
	var faktor: String = ("%.1f" % kern.balance.schub_faktor).rstrip("0").rstrip(".").replace(".", ",")
	var minuten: int = int(round(kern.balance.schub_dauer / 60.0))
	var nachlegbar: bool = _schub_nachlegbar()
	if nachlegbar and not _schub_angeboten:
		werbung.melde_angebot(&"schub")
	_schub_angeboten = nachlegbar
	# Mitte der Leiste: der Gegenwert steht IMMER im Knopf ("▶ ×2 · 30 Min"); laeuft er,
	# stehen Faktor und Restzeit da, und der Knopf atmet, solange Nachlegen moeglich ist.
	if kern.schub_laeuft():
		var laeuft_faktor: String = ("%.1f" % kern.schub_faktor).rstrip("0").rstrip(".").replace(".", ",")
		menueleiste.setze_text(&"schub", UiText.t("werbung_boost_laeuft") % [laeuft_faktor, _mm_ss(kern.schub_rest)])
		menueleiste.setze_schub_zustand(&"bereit" if nachlegbar else &"laeuft")
		return
	var rest: float = werbung.sperrzeit_rest(&"schub")
	if rest > 0.0 and werbung.grund(&"schub") == "abstand":
		menueleiste.setze_text(&"schub", UiText.t("boost_pause") % _mm_ss(rest))
		menueleiste.setze_schub_zustand(&"aus")
		return
	menueleiste.setze_text(&"schub", UiText.t("werbung_boost_bereit") % [faktor, str(minuten)])
	# Im Tutorial atmet nur das Tutorialziel: Der grosse Boost-Knopf in der Mitte
	# der Leiste konkurrierte mit dem Ring und der Hand.
	menueleiste.setze_schub_zustand(&"bereit" if nachlegbar else &"aus")


# --- Angebote nach einer Belohnung (K3 C1) ------------------------------------------

## Das schwebende Angebot ueber der Menueleiste: immer nur eines, immer mit Gegenwert,
## verschwindet von selbst. Ablehnen kostet nichts -- man tippt einfach nicht.
var _angebot: Button
var _angebot_art: StringName = &""
var _angebot_betrag: float = 0.0
var _angebot_laeuft: bool = false
var _schub_angeboten: bool = false


## Schreibt Geld gut, das nicht aus der Kette stammt (Werbe-Belohnung).
static func schreibe_gut(k: GameCore, betrag: float) -> void:
	if betrag <= 0.0:
		return
	k.kapital += betrag
	k.gesamt_verdient += betrag
	k.bus.money_changed.emit(k.kapital, betrag)


func _biete_ziel_doppelt(betrag: float) -> void:
	if betrag <= 0.0 or werbung == null:
		return
	var extra: float = betrag * (float(werbung.wert(&"ziel_doppelt", "faktor", 2.0)) - 1.0)
	_zeige_angebot(&"ziel_doppelt", UiText.t("werbung_ziel_doppelt") % UiStil.zahl(extra), extra)


func _zeige_angebot(art: StringName, text: String, betrag: float) -> void:
	if _angebot_laeuft:
		return
	_angebot_weg()
	if tutorial_aktiv or werbung == null or not werbung.ist_bereit(art) or betrag <= 0.0:
		return
	_angebot_art = art
	_angebot_betrag = betrag
	_angebot = Sheet.kaufknopf(UiStil.GOLD)
	_angebot.text = text
	_angebot.anchor_left = 0.5
	_angebot.anchor_right = 0.5
	_angebot.anchor_top = 1.0
	_angebot.anchor_bottom = 1.0
	_angebot.offset_left = -300.0
	_angebot.offset_right = 300.0
	# K7: ueber einem offenen Sheet (Auftragsbrett nach "Abholen"), nicht mitten auf seiner Liste.
	var unten: float = maxf(offenes_menue_hoehe(), Menueleiste.HOEHE)
	_angebot.offset_top = -(unten + 128.0)
	_angebot.offset_bottom = -(unten + 32.0)
	_angebot.pressed.connect(func() -> void:
		_angebot_laeuft = true
		_angebot.disabled = true
		_angebot.text = UiText.t("werbung_laeuft")
		werbung.zeige_belohnt(art))
	add_child(_angebot)
	UiStil.aufploppen(_angebot, 0.8)
	werbung.melde_angebot(art)
	var dauer: float = float(werbung.wert(art, "angebot_sekunden", 12.0))
	var knopf: Button = _angebot
	var uhr := knopf.create_tween()
	uhr.tween_interval(dauer)
	uhr.tween_callback(func() -> void:
		if not _angebot_laeuft and _angebot == knopf:
			_angebot_weg())


func _angebot_weg() -> void:
	_angebot_laeuft = false
	_angebot_art = &""
	if _angebot != null and is_instance_valid(_angebot):
		_angebot.queue_free()
	_angebot = null


## Zahlt die Platzierungen aus, die dieser Bildschirm selbst anbietet.
## (Boost und Rueckkehr-Verdopplung zahlt main.gd, den Raum das Raum-Panel,
## das Tagesgeschenk die Geschenk-Karte.)
func _auf_werbung_belohnung(art: StringName) -> void:
	if art != _angebot_art or _angebot_art == &"":
		return
	var betrag: float = _angebot_betrag
	_angebot_weg()
	schreibe_gut(kern, betrag)
	var text: String = UiText.t("werbung_danke_ziel") if art == &"ziel_doppelt" else UiText.t("werbung_danke_kiste")
	saft.meldung(UiText.t("werbung_danke_titel"), text + " +%s €" % UiStil.zahl(betrag), "muenze")
	saft.muenzen(get_viewport_rect().size * 0.5, 10)


static func _mm_ss(sekunden: float) -> String:
	var ganz: int = int(ceilf(maxf(sekunden, 0.0)))
	return "%d:%02d" % [ganz / 60, ganz % 60]


# --- Reaktionen ------------------------------------------------------------------

func _abgelehnt() -> void:
	audio.spiele(&"abgelehnt")


func _auf_geld(_neu: float, differenz: float) -> void:
	# Negative Differenzen sind Kaeufe -- Verluste kommen eigens ueber loss_tick.
	if differenz <= 0.0 or clips_zeigen_ertrag:
		return
	# Laufende Einnahmen als kleine Zahl ueber der letzten Station der Kette --
	# gesammelt und hoechstens einmal pro Sekunde, sonst ist es Rauschen.
	_ertrag_summe += differenz
	if _ertrag_rest > 0.0:
		return
	_ertrag_rest = 1.1
	var ort: StringName = Ids.STATION_PROCESSING
	var upload: StationModel = kern.kette.station(Ids.STATION_TRANSPORT)
	if upload != null and upload.freigeschaltet:
		ort = Ids.STATION_TRANSPORT
	if marker.kamera != null and _station_positionen.has(ort) and UiStil.zahl(_ertrag_summe) != "0":
		var welt: Vector3 = _station_positionen[ort] as Vector3 + Vector3(0.0, 2.0, 0.0)
		if not marker.kamera.is_position_behind(welt):
			var p: Vector2 = marker.kamera.unproject_position(welt)
			# K7: Liegt die Station unter einem offenen Menue, keine Zahl -- sie stand sonst
			# auf dessen Kopf und dem X (Auftragsbrett, Raum-Panel).
			if not _unter_menue(p):
				saft.betrag(p, "+" + UiStil.zahl(_ertrag_summe))
	_ertrag_summe = 0.0


## Verluste (Welt 6): keine Muenzen, sondern eine rote Zahl, die unter dem
## Kapital absinkt -- gesammelt, hoechstens einmal pro Sekunde.
var _verlust_summe: float = 0.0
var _verlust_rest: float = 0.0


func _auf_verlust(differenz: float) -> void:
	_verlust_summe += differenz
	var jetzt: float = Time.get_ticks_msec() / 1000.0
	if jetzt < _verlust_rest:
		return
	_verlust_rest = jetzt + 1.1
	var von: Vector2 = kopfleiste.einkommen_rechts()
	if UiStil.zahl(-_verlust_summe) != "0":
		saft.verlust(von, "-" + UiStil.zahl(-_verlust_summe))
	_verlust_summe = 0.0


func _auf_bereich_gekauft(bereich_id: StringName) -> void:
	audio.spiele(&"raum")
	var raum_name: String = WeltTexte.bereich(thema, bereich_id, "name")
	var bonus: String = WeltTexte.bonus(thema, kern, bereich_id)
	var bonus_teile: PackedStringArray = bonus.split(" · ")
	# Das Grosse nennt den ersten Teil; der Untertitel nur den Rest (nie doppelt).
	var rest: String = " · ".join(bonus_teile.slice(1))
	var daten: Dictionary = {"art": "raum", "betrag": 0.0, "name": raum_name, "titel": UiText.t("gekauft_titel") % raum_name,
		"text_gross": bonus_teile[0], "untertitel": rest}
	# Schaltet der Raum eine Station frei, ist DIE der Held: Bild, Name gross, Band "NEU".
	var frei_id: StringName = GameCore._station_zu_freischaltung(kern.bereiche.schaltet_frei(bereich_id))
	if frei_id != &"":
		daten["text_gross"] = WeltTexte.station_name(thema, frei_id)
		daten["untertitel"] = " · ".join(bonus_teile.slice(0, maxi(bonus_teile.size() - 1, 0)))
		daten["bild"] = Stationsmenue.ICON_PFAD % [kern.welt_id(), String(frei_id)]
		daten["band"] = UiText.t("neu")
	if not moment_zeigen(daten):
		saft.meldung(UiText.t("gekauft_titel") % raum_name, bonus, "haken")
	tutorial_ereignis.emit(&"bereich_gekauft", String(bereich_id))
	speichern_gewuenscht.emit()


func _auf_ausstattung(station_id: StringName, platz_id: StringName, stufe: int) -> void:
	var p: EquipmentSlot = kern.kette.station(station_id).platz(platz_id)
	audio.spiele(&"platz", stufe)
	tutorial_ereignis.emit(&"ausstattung_gekauft", stufe)
	if p != null and p.modell_schwellen.has(stufe):
		# Ein neues Modell ist der Moment, den man sieht -- am Objekt (Funken), kein Toast (§3.2).
		var an: Vector2 = _station_bildpunkt(station_id)
		if an.x >= 0.0:
			saft.funken(an, UiStil.GOLD, 18)
		audio.spiele(&"meilenstein")


## Eine Geschenk-Marke auf dem Weltbalken: Muenzen vom Balken zur Muenze.
func _auf_marke(marke_id: StringName) -> void:
	var betrag: float = kern.loese_marke_ein(marke_id)
	if betrag <= 0.0:
		return
	var von: Vector2 = kopfleiste.marke_mitte(marke_id)
	var wert: int = 0
	for m in kern.marken_liste():
		if StringName(String((m as Dictionary).get("id", ""))) == marke_id:
			wert = int(round(float((m as Dictionary).get("wert", 0.0)) * 100.0))
	if moment_zeigen({"art": "marke", "betrag": betrag, "zahl": wert}):
		aktualisiere()
		return
	audio.spiele(&"muenzen")
	Haptik.puls(Haptik.DAUER_MENGE)
	saft.muenzen(von, 10)
	saft.funken(von, UiStil.GOLD, 16)
	saft.betrag(von + Vector2(0.0, 60.0), "+" + UiStil.zahl(betrag))
	aktualisiere()


func _auf_stufe(_id: StringName, _stufe: int) -> void:
	# Meilenstein-Stufen melden sich als Stern am Objekt (_auf_stern), nicht als Toast (§3.2).
	tutorial_ereignis.emit(&"stufen_gesamt", kern.stufen_gesamt())


## Bildschirmpunkt einer Station (ueber dem Modell) oder (-1,-1), wenn sie nicht im Bild ist.
func _station_bildpunkt(id: StringName) -> Vector2:
	if marker == null or marker.kamera == null or not is_instance_valid(marker.kamera) \
			or not _station_positionen.has(id):
		return Vector2(-1.0, -1.0)
	var welt: Vector3 = _station_positionen[id] as Vector3 + Vector3(0.0, 1.2, 0.0)
	if marker.kamera.is_position_behind(welt):
		return Vector2(-1.0, -1.0)
	var p: Vector2 = marker.kamera.unproject_position(welt)
	return p if get_viewport_rect().has_point(p) else Vector2(-1.0, -1.0)


func _auf_nachricht(nachricht_id: StringName) -> void:
	_aktualisiere_abzeichen()
	var n: Dictionary = WeltTexte.nachricht(thema, String(nachricht_id))
	if n.is_empty():
		return
	if bool(n.get("szene", false)):
		if tutorial_aktiv:
			# Szenen warten bis zum Tutorialende (K2 P1d); das Handy zeigt sie sofort.
			if not _szenen_nach_tutorial.has(String(nachricht_id)):
				_szenen_nach_tutorial.append(String(nachricht_id))
			return
		_zeige_szene(String(nachricht_id))
		return
	# K6 1c: Nachrichten ohne `szene` sprechen als kurze Blase AM ORT (ueber der Figur des
	# Absenders), eine zur Zeit, nie unter einem Fenster oder Panel -- und stehen im Handy.
	if handymenue.ist_offen():
		handymenue.neu_zeichnen()
		return
	if OS.get_cmdline_user_args().has("--ohne-szene") or _start_args_haben("--ohne-szene"):
		return
	var von: String = String(n.get("von", ""))
	ortsblase.melde(String(nachricht_id), von, String(n.get("text", "")),
		WeltTexte.absender(thema, von), UiStil.absender_farbe(thema, von))


## Tipp auf eine Ortsblase: das Handy an genau dieser Nachricht.
func _auf_ortsblase(nachricht_id: String) -> void:
	handymenue.ziel_nachricht = nachricht_id
	_oeffne(handymenue)
	handymenue.neu_zeichnen()


## Darf jetzt eine Ortsblase stehen? Kein Panel, keine Tutorialkarte, keine Erklaerblase.
func _darf_ortsblase() -> bool:
	return not sheet_offen() and not _tutorial_karte() and not symbol_hinweise.ist_offen() 		and not saft.meldung_laeuft()


func _tutorial_karte() -> bool:
	return tutorial_karte_sichtbar.is_valid() and bool(tutorial_karte_sichtbar.call())


func _auf_moment(von: Vector2) -> void:
	var war_gross: bool = kern.momente.gross
	var war_kiste: bool = kern.momente.ist_kiste()
	var einkommen: float = kern.einkommen_pro_sekunde()
	var betrag: float = kern.tippe_moment()
	if betrag <= 0.0:
		return
	if war_kiste and werbung != null:
		# Kiste mit Werbung: statt der kleinen Lieferung lange Einkommen -- der Unterschied
		# steht im Knopf.
		var mit: float = maxf(einkommen * float(werbung.wert(&"kiste", "sekunden_mit", 0.0)),
			kern.momente.belohnung_minimum)
		_zeige_angebot(&"kiste", UiText.t("werbung_kiste") % UiStil.zahl(mit - betrag), mit - betrag)
	audio.spiele(&"muenzen")
	saft.muenzen(von, 7)
	saft.betrag(von, "+" + UiStil.zahl(betrag))
	# K6 1c: am Objekt -- Muenzen und Zahl, kein Toast mit Spruch dazu (§3.2).
	if war_gross:
		saft.muenzen(von, 18)
		saft.funken(von, UiStil.GOLD, 16)


func _auf_auftrag(von: Vector2) -> void:
	var erloes: float = kern.loese_auftrag_ein()
	if erloes <= 0.0:
		return
	audio.spiele(&"muenzen")
	saft.muenzen(von, 12)
	saft.betrag(von, "+" + UiStil.zahl(erloes))


# --- Die Aufgaben-Leiste ---------------------------------------------------------

## IBT-artig (K7): oben ein schmaler Segmentbalken des Weltziels mit dem Karten-Pin
## rechts (Standortkarte), darunter bis zu drei kleine Aufgabenkarten nebeneinander
## (Symbol, kurzer Text, Balken). Ein Tipp auf eine Karte oeffnet das Auftragsbrett.
## Der Weg zur naechsten Belohnung bleibt dauernd sichtbar (Gesetz 3 der Design-Analyse).
func _baue_zielkarte() -> void:
	_zielkarte = VBoxContainer.new()
	_zielkarte.add_theme_constant_override("separation", UiStil.A2)
	_zielkarte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stapel.add_child(_zielkarte)

	var kopf := HBoxContainer.new()
	kopf.add_theme_constant_override("separation", UiStil.A3)
	kopf.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_zielkarte.add_child(kopf)
	var links := VBoxContainer.new()
	links.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	links.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	links.add_theme_constant_override("separation", UiStil.A1)
	links.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kopf.add_child(links)
	# K6 1c: Kapitel als duenne Zeile ueber dem Segmentbalken (kein Fenster, kein Tipp).
	_kapitel_zeile = KapitelZeile.new()
	links.add_child(_kapitel_zeile)
	_segmente = SegmentBalken.new()
	_segmente.custom_minimum_size = Vector2(0.0, 22.0)
	links.add_child(_segmente)

	_karten_pin = PanelContainer.new()
	_karten_pin.custom_minimum_size = Vector2(UiStil.TIPPZIEL - 28.0, UiStil.TIPPZIEL - 28.0)
	_karten_pin.mouse_filter = Control.MOUSE_FILTER_STOP
	_karten_pin.tooltip_text = UiText.t("brett_karte")
	_karten_pin.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KNOPF,
		UiStil.KONTUR, float(UiStil.A2)))
	var pin_bild: TextureRect = UiStil.symbolbild("hochhaus", 34.0)
	pin_bild.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	pin_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_karten_pin.add_child(pin_bild)
	_karten_pin.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			UiStil.eindruecken(_karten_pin)
			oeffne_standortkarte())
	kopf.add_child(_karten_pin)

	var reihe := HBoxContainer.new()
	reihe.add_theme_constant_override("separation", UiStil.A2)
	reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_zielkarte.add_child(reihe)
	for i in range(Auftragsbrett.ANZAHL):
		reihe.add_child(_baue_auftragskarte(i))


func _baue_auftragskarte(index: int) -> PanelContainer:
	var karte := PanelContainer.new()
	karte.custom_minimum_size = Vector2(10.0, 96.0)
	karte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	karte.clip_contents = true
	karte.mouse_filter = Control.MOUSE_FILTER_STOP
	karte.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			_auf_auftragskarte(index))
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A1)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	karte.add_child(spalte)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.size_flags_vertical = Control.SIZE_EXPAND_FILL
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(zeile)
	var bild: TextureRect = UiStil.symbolbild("ziel", 32.0)
	bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(bild)
	var text: Label = UiStil.label("", UiStil.GR_KLEIN, UiStil.TINTE, UiStil.FETT)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.max_lines_visible = 3
	text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	text.custom_minimum_size = Vector2(10.0, 0.0)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(text)
	var balken: ProgressBar = UiStil.neuer_balken(18.0)
	balken.size_flags_vertical = Control.SIZE_SHRINK_END
	spalte.add_child(balken)
	var zaehler: Label = UiStil.label("", UiStil.GR_KLEIN - 2, UiStil.TINTE, UiStil.FETT)
	zaehler.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	zaehler.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	zaehler.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	balken.add_child(zaehler)
	_auftrags_karten.append({"karte": karte, "bild": bild, "text": text, "balken": balken, "zaehler": zaehler})
	return karte


## Die Tagesaufgabe: eine schmale zweite Leiste unter dem Hauptziel. Nur eine,
## nur ab dem Weltfortschritt, den die Daten nennen, nie im Tutorial.
func _baue_aufgabe() -> void:
	_aufgabe_karte = PanelContainer.new()
	_aufgabe_karte.custom_minimum_size = Vector2(0.0, 44.0)
	_aufgabe_karte.mouse_filter = Control.MOUSE_FILTER_STOP
	_aufgabe_karte.visible = false
	_aufgabe_karte.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			_auf_aufgabe())
	_stapel.add_child(_aufgabe_karte)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_aufgabe_karte.add_child(zeile)
	var chip := PanelContainer.new()
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.TINTE, float(UiStil.A2), 1.0, 0.0))
	chip.add_child(UiStil.label(UiText.t("aufgabe_leiste"), UiStil.GR_HINWEIS - 2, UiStil.WEISS, UiStil.FETT))
	zeile.add_child(chip)
	_aufgabe_text = UiStil.label("", UiStil.GR_HINWEIS + 2, UiStil.TINTE, UiStil.FETT)
	_aufgabe_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_aufgabe_text.clip_text = true
	_aufgabe_text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_aufgabe_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(_aufgabe_text)
	_aufgabe_balken = UiStil.neuer_balken(12.0)
	_aufgabe_balken.custom_minimum_size = Vector2(110.0, 12.0)
	_aufgabe_balken.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(_aufgabe_balken)
	_aufgabe_zaehler = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	_aufgabe_zaehler.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(_aufgabe_zaehler)
	_aufgabe_belohnung = UiStil.label("", UiStil.GR_HINWEIS, UiStil.GOLD_TEXT, UiStil.FETT)
	_aufgabe_belohnung.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(_aufgabe_belohnung)


func _aufgabe_eintrag() -> Dictionary:
	for e in kern.leiste():
		if String((e as Dictionary).get("art", "")) == "tagesaufgabe":
			return e as Dictionary
	return {}


func _aktualisiere_aufgabe() -> void:
	var e: Dictionary = _aufgabe_eintrag()
	if e.is_empty() or tutorial_aktiv or not kern.ist_frei("tagesaufgaben"):
		_aufgabe_karte.visible = false
		_aufgabe_chip.visible = false
		return
	# Eingeklappt (Standard): nur ein Chip in der Zeile mit dem Engpass. Eine fertige
	# Aufgabe klappt von selbst auf, damit man sie nicht uebersieht.
	var aufgeklappt: bool = _aufgabe_offen or bool(e.get("bereit", false))
	_aufgabe_karte.visible = aufgeklappt
	_aufgabe_chip.visible = not aufgeklappt
	_aufgabe_chip_text.text = "%s  %s/%s" % [UiText.t("aufgabe_leiste"),
		_ganz(float(e.get("ist", 0.0))), _ganz(float(e.get("soll", 1.0)))]
	var aufgabe_id: String = String(e.get("id", ""))
	_aufgabe_karte.set_meta("aufgabe", aufgabe_id)
	var schluessel: String = "aufgabe_" + aufgabe_id
	_aufgabe_text.text = UiText.t(schluessel) if UiText.hat(schluessel) else UiText.t("aufgabe_unbekannt")
	_aufgabe_balken.value = float(e.get("fortschritt", 0.0))
	var bereit: bool = bool(e.get("bereit", false))
	_aufgabe_zaehler.text = "%s/%s" % [_ganz(float(e.get("ist", 0.0))), _ganz(float(e.get("soll", 1.0)))]
	_aufgabe_belohnung.text = (UiText.t("ziel_holen") + " " if bereit else "") + "+" + UiStil.zahl(float(e.get("belohnung", 0.0)))
	var zustand: Array = [bereit, UiStil.akzent()]
	if _aufgabe_karte.get_meta("zustand", []) != zustand:
		_aufgabe_karte.set_meta("zustand", zustand)
		# Tagesaufgabe = Teil der Zielleiste: nur eine Flaeche, ohne Kontur und Schatten
		# (D1 C1: genau eine Kontur-Ebene unter der Kopfleiste).
		var stil := StyleBoxFlat.new()
		stil.bg_color = UiStil.GOLD if bereit else Color(UiStil.PAPIER_2, 0.92)
		stil.set_corner_radius_all(UiStil.RADIUS_KARTE - 8)
		stil.anti_aliasing = true
		stil.content_margin_left = float(UiStil.A3)
		stil.content_margin_right = float(UiStil.A3)
		stil.content_margin_top = float(UiStil.A1)
		stil.content_margin_bottom = float(UiStil.A1)
		_aufgabe_karte.add_theme_stylebox_override("panel", stil)
		UiStil.faerbe_balken(_aufgabe_balken, UiStil.TINTE if bereit else UiStil.akzent())


func _auf_aufgabe() -> void:
	var e: Dictionary = _aufgabe_eintrag()
	if e.is_empty():
		return
	if not bool(e.get("bereit", false)):
		_aufgabe_offen = false
		_aktualisiere_aufgabe()
		return
	var betrag: float = kern.loese_tagesaufgabe_ein(StringName(String(e.get("id", ""))))
	belohnung_zeigen(betrag, _aufgabe_karte.get_global_rect().get_center())
	UiStil.eindruecken(_aufgabe_karte)
	aktualisiere()


## Steht in der Zielleiste ein erreichtes Ziel, dessen Geschenk man jetzt holen kann?
func ziel_abholbar() -> bool:
	return _zielkarte != null and _zielkarte.visible and bool(_zielkarte.get_meta("fertig", false))


## Die Unterkante der Leiste -- darunter beginnt die freie Karte.
func ziel_unterkante() -> float:
	return _stapel_unterkante()


## Unterkante des Stapels (Speicher, Ziel, Tagesaufgabe, Engpass) in Bildschirmpixeln.
func _stapel_unterkante() -> float:
	if _stapel == null:
		return OBEN_ZEILE
	return _stapel.offset_top + _stapel.get_combined_minimum_size().y


func _tutorial_zeigt(was: String) -> bool:
	return tutorial_zeigt.is_valid() and bool(tutorial_zeigt.call(was))


## Text des aktuellen Hauptziels (fuer den Platzhalter {ziel} im Tutorial).
func aktuelles_ziel_text() -> String:
	var sichtbar: Array[Dictionary] = kern.ziele.sichtbar(1)
	return WeltTexte.ziel(thema, sichtbar[0]) if not sichtbar.is_empty() else ""


func _aktualisiere_zielkarte() -> void:
	var liste: Array[Dictionary] = Auftragsbrett.auftraege_von(kern, thema)
	if liste.is_empty() or (tutorial_aktiv and not _tutorial_zeigt("zielleiste")):
		_zielkarte.visible = false
		return
	_zielkarte.visible = true
	_kapitel_zeile.setze(kapitel_zeile(kern), false)
	_segmente.setze(kern.weltwechsel_fortschritt(), kern.marken_liste())
	var fertig_da: bool = false
	for i in range(_auftrags_karten.size()):
		var teile: Dictionary = _auftrags_karten[i]
		var karte: PanelContainer = teile["karte"] as PanelContainer
		karte.visible = i < liste.size()
		if i >= liste.size():
			continue
		var info: Dictionary = liste[i]
		var fertig: bool = String(info["status"]) == "bereit"
		fertig_da = fertig_da or fertig
		var ziel_id: String = String(info["id"])
		karte.set_meta("ziel", ziel_id)
		var z: Dictionary = kern.ziele.definition(ziel_id)
		var text_feld: Label = teile["text"] as Label
		var kurz: String = Auftragsbrett.kurztext(thema, z)
		var breite_alt: float = float(text_feld.get_meta("breite", -1.0))
		if text_feld.text != kurz or not is_equal_approx(breite_alt, text_feld.size.x):
			text_feld.text = kurz
			_passe_kartenschrift(text_feld)
		var balken: ProgressBar = teile["balken"] as ProgressBar
		balken.value = float(info["fortschritt"])
		(teile["zaehler"] as Label).text = UiText.t("ziel_holen") if fertig else Auftragsbrett.zaehler_text(info)
		(teile["bild"] as TextureRect).texture = UiStil.symbol("geschenk" if fertig else "ziel")
		var zustand: Array = [fertig, UiStil.akzent()]
		if karte.get_meta("zustand", []) != zustand:
			karte.set_meta("zustand", zustand)
			var stil := UiStil.karte(UiStil.GOLD if fertig else UiStil.PAPIER, UiStil.RADIUS_KARTE,
				UiStil.KONTUR, float(UiStil.A2))
			stil.content_margin_left = float(UiStil.A2 + 2)
			stil.content_margin_right = float(UiStil.A2 + 2)
			karte.add_theme_stylebox_override("panel", stil)
			var fuell: StyleBoxFlat = UiStil.balken(UiStil.WEISS if fertig else UiStil.akzent())
			balken.add_theme_stylebox_override("fill", fuell)
			if fertig:
				karte.pivot_offset = karte.size * 0.5
				UiStil.aufploppen(karte, 0.9)
	_zielkarte.set_meta("ziel", String(liste[0]["id"]))
	_zielkarte.set_meta("fertig", fertig_da)


## K7: Passt das laengste Wort nicht in die Karte ("Ausstattungsstufen"), wird die Schrift
## stufenweise kleiner (bis AUFTRAG_SCHRIFT_MIN) -- vorher brach das Wort mitten durch.
func _passe_kartenschrift(l: Label) -> void:
	var breite: float = l.size.x
	l.set_meta("breite", breite)
	var groesse: int = UiStil.GR_KLEIN
	if breite > 1.0:
		var laengstes: String = ""
		for wort in l.text.split(" ", false):
			if wort.length() > laengstes.length():
				laengstes = wort
		while groesse > AUFTRAG_SCHRIFT_MIN:
			var f: Font = UiStil.schrift(UiStil.FETT, groesse)
			if f.get_string_size(laengstes, HORIZONTAL_ALIGNMENT_LEFT, -1, groesse).x <= breite:
				break
			groesse -= 1
	l.add_theme_font_size_override("font_size", groesse)
	l.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, groesse))


## Zaehlerstand ohne Nachkomma: "3/10", nicht "3,0/10". Grosse Werte kurz ("1,2 Tsd").
static func _ganz(wert: float) -> String:
	return str(int(floorf(wert))) if wert < 10000.0 else UiStil.zahl(wert)


## Tipp auf eine Aufgabenkarte: das Auftragsbrett mit diesem Auftrag. Im Tutorial holt ein
## Tipp auf einen erfuellten Auftrag ihn direkt ab (die Hand zeigt auf die Leiste).
func _auf_auftragskarte(index: int) -> void:
	var karte: PanelContainer = _auftrags_karten[index]["karte"] as PanelContainer
	var ziel_id: String = String(karte.get_meta("ziel", ""))
	var z: Dictionary = kern.ziele.definition(ziel_id)
	if z.is_empty():
		return
	UiStil.eindruecken(karte)
	if tutorial_aktiv and GoalSystem.erfuellt(z, kern.messwert):
		_loese_ziel_ein(ziel_id, karte.get_global_rect().get_center())
		aktualisiere()
		return
	zeige_auftragsbrett(ziel_id)


## Das Auftragsbrett oeffnen (leer = der erste Auftrag).
func zeige_auftragsbrett(ziel_id: String = "") -> void:
	if ziel_id != "":
		auftragsbrett.gewaehlt = ziel_id
	_oeffne(auftragsbrett)
	tutorial_ereignis.emit(&"ziele_geoeffnet", 1)


## Der Knopf "Los geht's": zur Station oder zum Raum des Auftrags.
func _fahre_zum_auftrag(ziel_id: String) -> void:
	var ort: Dictionary = Auftragsbrett.ziel_ort(kern, ziel_id)
	var id := StringName(String(ort.get("id", "")))
	if String(ort.get("art", "")) == "bereich":
		zeige_bereich(id)
		bereich_fokus.emit(id)
	elif id != &"":
		zeige_station(id)


## Die Standortkarte der Firma (Pin rechts neben dem Weltziel-Balken).
func oeffne_standortkarte() -> StandortkarteView:
	schliesse_alle()
	audio.spiele(&"tipp")
	return StandortkarteView.oeffnen(self, kern, {})


func _loese_ziel_ein(ziel_id: String, von: Vector2) -> void:
	var betrag: float = kern.loese_ziel_ein(StringName(ziel_id))
	belohnung_zeigen(betrag, von, true)
	tutorial_ereignis.emit(&"ziele_eingeloest", kern.ziele.anzahl_eingeloest())


## Eingeloestes Ziel: ab 200 EUR ein Vollbild-Moment, darunter Muenzflug.
func belohnung_zeigen(betrag: float, von: Vector2, doppelt_anbieten: bool = false) -> void:
	if doppelt_anbieten:
		_biete_ziel_doppelt(betrag)
	if betrag > 0.0 and moment_zeigen(_ziel_moment_daten(betrag)):
		return
	audio.spiele(&"muenzen")
	Haptik.puls(Haptik.DAUER_KAUF)
	saft.muenzen(von, 10)
	if betrag > 0.0:
		saft.betrag(_betrag_anker(von), "+" + UiStil.zahl(betrag))


## Daten des Ziel-Moments. Das ALLERERSTE Ziel ist immer einer, auch unter der Schwelle (K2 3,
## Minute 1:40): Mo jubelt, die Zahl zaehlt hoch, der Text sagt, wohin das Geld fuehrt.
func _ziel_moment_daten(betrag: float) -> Dictionary:
	var daten: Dictionary = {"art": "ziel", "betrag": betrag}
	if tutorial_aktiv and kern.ziele.anzahl_eingeloest() <= 1 and thema != null:
		var texte: Dictionary = thema.abschnitt("tutorial").get("belohnung_moment", {}) as Dictionary
		if not texte.is_empty():
			daten["erzwingen"] = true
			daten["titel"] = String(texte.get("titel", ""))
			daten["untertitel"] = String(texte.get("untertitel", ""))
	return daten


## Wo die Zahl aufsteigt: Ist ein Sheet offen, ueber seinem oberen Rand in der
## Bildmitte -- nie ueber dem Schliessen-Knopf oder dem Titelstreifen.
func _betrag_anker(von: Vector2) -> Vector2:
	if not sheet_offen():
		return von
	var flaeche: Vector2 = get_viewport_rect().size
	return Vector2(flaeche.x * 0.5, flaeche.y - offenes_menue_hoehe() - 70.0)


## Ein Stern: Gold-Moment mit dem neuen Faktor (`star_reached` vom Kern).
func _auf_stern(station_id: StringName, sterne: int) -> void:
	var info: Dictionary = kern.stern_info(station_id)
	var faktor: String = ("%.2f" % float(info.get("faktor", 1.5))).rstrip("0").rstrip(".").replace(".", ",")
	# K6 §3.1 Nr. 3 / 1c: am Objekt -- der Faktor schlaegt ueber der Station auf, kein Toast.
	audio.spiele(&"stern")
	var an: Vector2 = _station_bildpunkt(station_id)
	if an.x >= 0.0 and not saft.pausiert and sterne > 0:
		saft.aufschlag(an, "×" + faktor)
		saft.funken(an, UiStil.GOLD, 14)


## Zeigt einen Belohnungs-Moment (Vollbild, U3). Laeuft schon einer, wartet der
## naechste. Gibt false zurueck, wenn die Art unter der Schwelle liegt -- dann
## gilt der kleine Weg (Muenzflug oder Banner).
func moment_zeigen(daten: Dictionary) -> bool:
	var art: String = String(daten.get("art", ""))
	# Bastian 16.10. (Handy): Nur der Raumkauf bleibt ein Vollbild-Moment. Stern, Rang,
	# Ziel und Marke werden ein kurzer Hinweis am Rand (Aufrufer: kleiner Weg). Welche
	# Arten Vollbild sind, steht in data/ui/hinweise.json (vollbild_momente).
	if not (Kartenmarker.hinweise().get("vollbild_momente", []) as Array).has(art):
		return false
	if not MomentView.ist_moment(art, float(daten.get("betrag", 0.0))) and not bool(daten.get("erzwingen", false)):
		return false
	if not daten.has("figur"):
		daten["figur"] = "mo"
	# Kein OK-Druecken (Bastian): schliesst nach raum_moment_auto_s, ein Tipp schliesst sofort.
	daten["auto_s"] = Kartenmarker.hinweis("raum_moment_auto_s")
	_momente_wartend.append(daten)
	_saft_pause()
	# K3 A2/A3: ein Modal zur Zeit. K6 1c: kein Sammelfenster mehr -- stauen sich
	# Raum-Momente (Vorspulen), kommt nur der NEUESTE (_zeige_moment).
	var schlange: ModalSchlange = ModalSchlange.global()
	schlange.anmelden(&"moment", func() -> Node: return _zeige_moment(daten))
	return true


## Nach dem Vorspulen (--tiefe): Raum-Momente und Ortsblasen der vorgespulten Kaeufe sind
## kein Spielerlebnis -- weg damit (Szenen verwirft main.gd ebenso).
func verwerfe_vorgespultes() -> void:
	_momente_wartend.clear()
	_szenen_nach_tutorial.clear()
	ModalSchlange.global().verwerfe(&"moment")
	ortsblase.leeren()
	_saft_pause()


## Nur fuer Pruefbilder: alle offenen und wartenden Momente wegraeumen.
func momente_verwerfen() -> void:
	_momente_wartend.clear()
	var schlange: ModalSchlange = ModalSchlange.global()
	schlange.verwerfe(&"moment")
	if _moment != null and is_instance_valid(_moment):
		_moment.queue_free()
	_moment = null
	if schlange.offene_art() == &"moment":
		schlange.fertig()
	# Pruefbilder (--moment aus) zeigen Menues und Karte, keine Erklaer- und Ortsblasen --
	# sie wuerden jede Vorschau mit --tiefe verdecken.
	if ortsblase != null:
		ortsblase.leeren()
	if symbol_hinweise != null:
		symbol_hinweise.set_process(false)
	_saft_pause()


func _auf_fenster(_art: StringName) -> void:
	_saft_pause()


func _saft_pause() -> void:
	# Banner und Zahlen ruhen, solange ein Moment oder eine Szene offen ist (oder wartet).
	# P1.7: auch jedes andere Fenster der Schlange (Kapitel, Offline, Eroeffnung) -- ausser
	# der kleinen Erklaer-Blase. Hinweise am Rand laufen nie unter einem Fenster durch.
	var schlange: ModalSchlange = ModalSchlange.global()
	var fenster: bool = schlange.ist_offen() and not ModalSchlange.LEICHT.has(schlange.offene_art())
	saft.pausiert = fenster or not _momente_wartend.is_empty() or (_moment != null and is_instance_valid(_moment) and _moment.is_inside_tree()) \
		or (_szene != null and is_instance_valid(_szene) and _szene.is_inside_tree())


## Die Schlange ruft das, wenn der Moment an der Reihe ist. Der zurueckgegebene
## Knoten gilt als offen, bis er den Baum verlaesst.
func _zeige_moment(daten: Dictionary) -> Node:
	if not _momente_wartend.has(daten):
		# Schon in einem Sammelfenster gezeigt.
		return null
	# K6 1c: Sammelfenster nur noch im Offline-Bericht. Stauen sich Raum-Momente, kommt der
	# neueste (er nennt den Raum, in dem man jetzt steht); die anderen sieht man in der Welt.
	daten = _momente_wartend.back()
	_momente_wartend.clear()
	if _moment_ebene == null:
		_moment_ebene = CanvasLayer.new()
		_moment_ebene.layer = 15
		add_child(_moment_ebene)
	_moment = MomentView.zeige_moment(_moment_ebene, daten, thema, saft, audio)
	_moment.tree_exited.connect(_saft_pause, CONNECT_DEFERRED)
	_saft_pause()
	return _moment


## Nach dem Tutorial: die Szenen, die waehrenddessen faellig wurden, nacheinander zeigen.
func _spiele_szenen_nach_tutorial() -> void:
	if tutorial_aktiv:
		return
	var liste: Array[String] = _szenen_nach_tutorial.duplicate()
	_szenen_nach_tutorial.clear()
	# K7: nur die NEUESTE (wie bei gestauten Szenen, P1.7). Einzeln angemeldet kam jede als eigenes
	# Fenster -- die Startszene ("Tipp auf die Pinnwand ...") erschien so erst nach dem ersten Raum,
	# veraltet, und direkt danach die Raumszene. Die aelteren stehen im Handy.
	if not liste.is_empty():
		_zeige_szene(liste.back())


## Eine Story-Szene (Nachricht mit szene:true): Figur-Popup statt Banner (U3).
## Waehrend eine Szene offen ist, warten weitere; kein Menue steht daneben.
func _zeige_szene(nachricht_id: String) -> void:
	# Pruefschalter --ohne-szene: Vorschauen mit vorgespulter Tiefe sehen sonst nur das Popup.
	if OS.get_cmdline_user_args().has("--ohne-szene") or _start_args_haben("--ohne-szene"):
		return
	# K3 A2/A3: ueber die Modal-Schlange -- nie zwei Modale gleichzeitig (M7).
	_szenen_wartend.append(nachricht_id)
	ModalSchlange.global().anmelden(&"szene", func(fertig: Callable) -> void:
		# P1.7 (K5): Stauen sich Szenen (nach Offline-Zeit, nach dem Tutorial, beim
		# Nachholen der Geschichte), kommt nur die NEUESTE als Fenster -- sie nennt das
		# aktuelle Ziel. Die aelteren stehen schon im Handy.
		var neueste: bool = not _szenen_wartend.is_empty() and _szenen_wartend.back() == nachricht_id
		_szenen_wartend.erase(nachricht_id)
		if not neueste:
			fertig.call()
			return
		_szenen_wartend.clear()
		_oeffne_szene(nachricht_id, fertig))


func _oeffne_szene(nachricht_id: String, fertig: Callable) -> void:
	# K6 Welle 2: Eine Szene reisst kein offenes Menue weg -- sie wartet, bis der
	# Spieler es selbst schliesst (sonst verschwindet das Raum-Panel mitten im Kauf).
	while sheet_offen() and is_inside_tree():
		await get_tree().create_timer(0.4).timeout
	if not is_inside_tree():
		fertig.call()
		return
	schliesse_alle()
	if _szene_ebene == null:
		_szene_ebene = CanvasLayer.new()
		_szene_ebene.layer = 30
		add_child(_szene_ebene)
	var n: Dictionary = WeltTexte.nachricht(thema, nachricht_id)
	_szene = SzeneView.zeige_szene(_szene_ebene, SzeneView.szene_aus_nachricht(n), thema, audio)
	_saft_pause()
	_szene.beendet.connect(func(index: int, antwort_text: String) -> void:
		if not antwort_text.is_empty():
			handymenue.antworten[nachricht_id] = antwort_text
			handymenue.neu_zeichnen()
		# K5: Die Antwort einer Kapitel-Entscheidung kommt in den Spielstand (nur Ton).
		var kapitel_id: String = kern.kapitel.kapitel_der_entscheidung(nachricht_id)
		if index >= 0 and not kapitel_id.is_empty():
			kern.merke_entscheidung(kapitel_id, index)
			speichern_gewuenscht.emit()
		_szene = null
		_saft_pause()
		fertig.call())


# --- Kapitel (K5) ----------------------------------------------------------------

## Ein neues Kapitel (K6 1c): kein Fenster -- die Kapitelzeile in der Zielleiste glaenzt kurz.
func _auf_kapitel(index: int) -> void:
	var e: Dictionary = kern.kapitel.eintrag(index)
	if e.is_empty():
		return
	if zielemenue.ist_offen():
		zielemenue.aktualisiere()
	handymenue.neu_zeichnen()
	if _kapitel_zeile != null:
		_kapitel_zeile.setze(kapitel_zeile(kern), true)


## "Kapitel 2 · Zu wenig Platz" fuer Ziele-Menue und Handy; leer ohne Kapiteldaten.
static func kapitel_zeile(k: GameCore) -> String:
	if k == null:
		return ""
	var i: int = k.kapitel_index()
	var e: Dictionary = k.kapitel.eintrag(i)
	if e.is_empty():
		return ""
	return UiText.t("kapitel_zeile") % [i + 1, String(e.get("titel", ""))]


## Die Aufgabe des laufenden Kapitels (ein Satz) oder leer.
static func kapitel_aufgabe(k: GameCore) -> String:
	if k == null:
		return ""
	return String(k.kapitel.eintrag(k.kapitel_index()).get("aufgabe", ""))


## Gespeicherte Entscheidungen wieder als Antworten ins Handy (nach dem Laden, nach
## dem Weltwechsel): Was man gesagt hat, steht dort auch nach einem Neustart.
func antworten_aus_entscheidungen() -> void:
	if kern == null or thema == null or handymenue == null:
		return
	for i in kern.kapitel.anzahl():
		var e: Dictionary = kern.kapitel.eintrag(i)
		var wahl: int = kern.entscheidung(String(e.get("id", "")))
		var nachricht_id: String = String(e.get("entscheidung", ""))
		if wahl < 0 or nachricht_id.is_empty():
			continue
		var antworten: Array = WeltTexte.nachricht(thema, nachricht_id).get("antworten", []) as Array
		if wahl >= antworten.size():
			continue
		var a: Variant = antworten[wahl]
		var text: String = String((a as Dictionary).get("text", "")) if a is Dictionary else String(a)
		if not text.is_empty():
			handymenue.antworten[nachricht_id] = text
	handymenue.neu_zeichnen()


## P1.9 / K6 1c: Erklaer-Blasen nur im Tutorial bzw. in den ersten Spielminuten
## (hinweise.json symbol_blase_bis_s), nur auf freier Karte -- kein Panel, keine Tutorialkarte
## mit Text, keine Ortsblase (eine Blase zur Zeit).
func _darf_symbol_erklaeren() -> bool:
	return symbol_erlaubt(tutorial_aktiv, kern.spielzeit if kern != null else INF,
		Kartenmarker.hinweis("symbol_blase_bis_s")) and _symbol_frei()


## Die Zeitregel allein (testbar): im Tutorial oder vor `bis_s` Spielzeit.
static func symbol_erlaubt(im_tutorial: bool, spielzeit: float, bis_s: float) -> bool:
	return im_tutorial or spielzeit < bis_s


func _symbol_frei() -> bool:
	if sheet_offen() or _tutorial_karte() or (ortsblase != null and ortsblase.ist_offen()):
		return false
	var argumente: PackedStringArray = OS.get_cmdline_user_args()
	# Pruefvorschauen mit Menue oder Moment: Die Blase wuerde das Bild verfaelschen.
	return not (argumente.has("--menue") or argumente.has("--ohne-symbolhinweis"))


## Ein offenes Ziel antippen heisst: hinfahren. Station oder Raum, um den es geht;
## Ziele ohne Ort (Gesamtstufen, Verdienst) oeffnen die Zielliste.
func springe_zu_ziel(ziel_id: String) -> void:
	var z: Dictionary = kern.ziele.definition(ziel_id)
	if not z.is_empty() and GoalSystem.erfuellt(z, kern.messwert):
		# Schon geschafft: Tippen holt die Belohnung, statt irgendwohin zu fuehren.
		_loese_ziel_ein(ziel_id, get_viewport().get_mouse_position())
		aktualisiere()
		return
	var station_id: StringName = StringName(String(z.get("station", "")))
	var bereich_id: StringName = StringName(String(z.get("bereich", "")))
	if station_id != &"" and kern.kette.station(station_id) != null:
		zeige_station(station_id)
		return
	if bereich_id != &"":
		zeige_bereich(bereich_id)
		bereich_fokus.emit(bereich_id)
		return
	if not kern.ist_frei("menue_ziele"):
		# Das Ziele-Menue gibt es noch nicht (Rang 1): zur Station, die gerade bremst.
		zeige_station(kern.kette.bottleneck())
		return
	if not zielemenue.ist_offen():
		_oeffne(zielemenue)
	tutorial_ereignis.emit(&"ziele_geoeffnet", 1)


## Ein Clip verlaesst die Kette: Sein Anteil am Einkommen steigt als Zahl auf.
##
## Das Genre zeigt staendig Geld ueber den Schaltern -- es ist die Rueckmeldung,
## dass die Kette ARBEITET. Vorher erschien einmal pro Sekunde eine Sammelzahl;
## jetzt gehoert jede Zahl zu einem Clip, den man gerade hat fliegen sehen.
func zeige_clip_ertrag(welt: Vector3, clips_pro_sekunde: float) -> void:
	if marker.kamera == null or not is_instance_valid(marker.kamera) or clips_pro_sekunde <= 0.0:
		return
	if marker.kamera.is_position_behind(welt):
		return
	var betrag: float = kern.einkommen_pro_sekunde() / clips_pro_sekunde
	if UiStil.zahl(betrag) == "0":
		return
	var p: Vector2 = marker.kamera.unproject_position(welt)
	if not _unter_menue(p):
		saft.betrag(p, "+" + UiStil.zahl(betrag))


## Liegt der Bildschirmpunkt unter (oder knapp ueber) einem offenen Menue? Laufende Ertragszahlen
## entfallen dort -- die Zahl steigt um ihre Hoehe auf und stand sonst auf Kopf und X des Menues.
func _unter_menue(p: Vector2) -> bool:
	return sheet_offen() and p.y > get_viewport_rect().size.y - offenes_menue_hoehe() - UNTER_MENUE_RAND


# --- Engpass und Limit ---------------------------------------------------------

## Eine Zeile am Stapelende: links der Aufgaben-Chip (eingeklappte Tagesaufgabe), rechts die Engpass-Pille.
func _baue_chip_zeile() -> void:
	_chip_zeile = HBoxContainer.new()
	_chip_zeile.add_theme_constant_override("separation", UiStil.A2)
	_chip_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stapel.add_child(_chip_zeile)
	_aufgabe_chip = PanelContainer.new()
	_aufgabe_chip.visible = false
	_aufgabe_chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_aufgabe_chip.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL)
	_aufgabe_chip.mouse_filter = Control.MOUSE_FILTER_STOP
	_aufgabe_chip.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER_2, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3)))
	_aufgabe_chip.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			_aufgabe_offen = true
			_aktualisiere_aufgabe())
	_aufgabe_chip_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_aufgabe_chip_text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_aufgabe_chip.add_child(_aufgabe_chip_text)
	_chip_zeile.add_child(_aufgabe_chip)
	var puffer := Control.new()
	puffer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	puffer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chip_zeile.add_child(puffer)


func _baue_engpass_pille() -> void:
	# Rot gehoert allein dem Engpass -- hier ist er.
	_engpass_pille = PanelContainer.new()
	var s := UiStil.karte(UiStil.WARNUNG, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A2))
	s.content_margin_left = float(UiStil.A2)
	s.content_margin_right = float(UiStil.A4)
	_engpass_pille.add_theme_stylebox_override("panel", s)
	_engpass_pille.size_flags_horizontal = Control.SIZE_SHRINK_END
	_engpass_pille.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL)
	_engpass_pille.mouse_filter = Control.MOUSE_FILTER_STOP
	_engpass_pille.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			zeige_station(kern.kette.bottleneck()))
	_chip_zeile.add_child(_engpass_pille)
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_engpass_pille.add_child(zeile)
	var bild := UiStil.symbolbild("warnung", 44.0)
	bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(bild)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", -4)
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	zeile.add_child(spalte)
	spalte.add_child(UiStil.label(UiText.t("bremst"), UiStil.GR_KLEIN - 2, UiStil.TINTE, UiStil.TEXT_GEWICHT))
	_engpass_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_engpass_text.custom_minimum_size = Vector2(0.0, 0.0)
	spalte.add_child(_engpass_text)


func _aktualisiere_engpass() -> void:
	# K3 A2 (M3): Den Engpass zeigt die Karte selbst (roter Blitz am Stationsschild).
	# Die rote Karte oben steht nur noch bei Ueberlastung -- die hat keinen Ort auf
	# der Karte. Sie steht nur, solange kein Menue offen ist.
	var offen: bool = false
	for s in _sheets:
		offen = offen or s.ist_offen()
	var text: String = ""
	if kern.ueberlastung() > 0.02 and thema != null:
		text = String(thema.abschnitt("personen").get("ueberlast_text", ""))
	_engpass_text.text = text
	_engpass_pille.visible = not offen and not text.is_empty() and not _limit_feld.visible and not tutorial_aktiv


## Wo die freie Karte beginnt: unter dem Stapel (Ziel, Speicher, Chips), plus Puffer.
## Frueher fest +76 fuer das Chat-Banner -- Schilder standen dann tief im Bild.
func _setze_oben_frei() -> void:
	if marker != null:
		marker.oben_frei = ziel_unterkante() + Kartenmarker.hinweis("oben_puffer_px")


func _baue_limit_anzeige() -> void:
	_limit_feld = PanelContainer.new()
	_limit_feld.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3)))
	_limit_feld.visible = false
	_stapel.add_child(_limit_feld)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStil.A2)
	_limit_feld.add_child(box)
	_limit_label = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_limit_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_limit_label)
	# Balken und Umbau-Knopf in EINER Zeile: Wer sieht, dass es voll ist,
	# hat die Loesung direkt daneben.
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	box.add_child(zeile)
	# Kurzform (nicht voll): Beschriftung links, duenner Balken rechts, alles in einer Zeile.
	_limit_kurz = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	_limit_kurz.visible = false
	zeile.add_child(_limit_kurz)
	_limit_leiste = UiStil.neuer_balken(22.0)
	_limit_leiste.max_value = 100.0
	_limit_leiste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_limit_leiste.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(_limit_leiste)
	_umbau_knopf = Sheet.kaufknopf()
	_umbau_knopf.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL)
	_umbau_knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
	_umbau_knopf.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
	_umbau_knopf.pressed.connect(func() -> void:
		if not kern.kaufe_umbau():
			_abgelehnt()
			return
		audio.spiele(&"freischaltung")
		var texte: Dictionary = thema.abschnitt("limit") if thema != null else {}
		saft.meldung(String(texte.get("erledigt_titel", "")), String(texte.get("erledigt_text", "")), "haken"))
	zeile.add_child(_umbau_knopf)


## Nicht voll: schlanke Kurzzeile (Text + duenner Balken). Voll: die grosse Karte mit Umbau-Knopf.
func _setze_limit_form(kompakt: bool, texte: Dictionary, anteil: float) -> void:
	if kompakt:
		_limit_kurz.text = String(texte.get("format", "%s  %d %%")) % [
			String(texte.get("titel", "")), int(round(clampf(anteil, 0.0, 1.0) * 100.0))]
	if kompakt == _limit_kompakt and _limit_feld.has_meta("form"):
		return
	_limit_feld.set_meta("form", true)
	_limit_kompakt = kompakt
	_limit_label.visible = false
	_limit_kurz.visible = true
	if kompakt:
		_limit_kurz.add_theme_color_override("font_color", UiStil.TINTE)
	_limit_leiste.custom_minimum_size.y = 10.0 if kompakt else 18.0
	_limit_feld.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A2) if kompakt else float(UiStil.A3)))


func _aktualisiere_limit() -> void:
	# Meldungen stehen direkt unter der Ziele-Leiste (nie ueber Stations-Schildern).
	saft.zusatz_oben = ziel_unterkante() + float(UiStil.A2) - Saft.MELDUNG_OBEN
	marker.oben_frei = ziel_unterkante() + 76.0
	if not kern.limit_gilt():
		_limit_feld.visible = false
		return
	var texte: Dictionary = thema.abschnitt("limit") if thema != null else {}
	var anteil: float = kern.limit_auslastung()
	_limit_feld.visible = true
	# Voll ist ein Engpass -- dann rot, pulsierend, und statt einer Zahl ueber
	# 100 % (die Auslastung laeuft weiter hoch) steht dort "voll".
	var voll: bool = anteil >= 0.98
	if voll:
		var voll_text: String = String(texte.get("voll", ""))
		if voll_text.is_empty():
			voll_text = UiText.t("voll")
		var hinweis: String = String(texte.get("voll_hinweis", ""))
		if hinweis.is_empty():
			hinweis = UiText.t("voll_hinweis")
		_limit_label.text = "%s  ·  %s  –  %s" % [String(texte.get("titel", "")), voll_text, hinweis]
	else:
		_limit_label.text = String(texte.get("format", "%s  %d %%")) % [
			String(texte.get("titel", "")), int(round(clampf(anteil, 0.0, 1.0) * 100.0))]
	_limit_label.add_theme_color_override("font_color", UiStil.WARNUNG_TEXT if voll else UiStil.TINTE)
	_limit_leiste.value = clampf(anteil * 100.0, 0.0, 100.0)
	_limit_voll = voll
	_setze_limit_form(not voll, texte, anteil)
	if voll:
		# Voll: dieselbe eine Zeile (Text, Balken, Umbau-Knopf) -- der Hinweis steht im Knopf.
		_limit_kurz.text = "%s  ·  %s" % [String(texte.get("titel", "")), String(texte.get("voll", UiText.t("voll")))]
		_limit_kurz.add_theme_color_override("font_color", UiStil.WARNUNG_TEXT)
	var zustand: Array = [voll, UiStil.akzent()]
	if _limit_leiste.get_meta("zustand", []) != zustand:
		_limit_leiste.set_meta("zustand", zustand)
		UiStil.faerbe_balken(_limit_leiste, UiStil.WARNUNG if voll else UiStil.akzent())
	# Ist es voll, steht der Umbau-Knopf immer da -- notfalls ausgegraut mit
	# Preis. Die Loesung soll sichtbar sein, bevor man sie bezahlen kann.
	var preis: float = kern.umbau_kosten()
	_umbau_knopf.visible = kern.kapital >= preis or voll
	_umbau_knopf.disabled = kern.kapital < preis
	if _umbau_knopf.visible:
		_umbau_knopf.text = String(texte.get("knopf", "%s")) % UiStil.preis(preis)


## Bildschirmpunkt des lohnendsten bezahlbaren Kaufs (fuer die Zeigehand), sonst (-1, -1).
func kauf_punkt() -> Vector2:
	var e: Dictionary = kern.empfehlung()
	if e.is_empty() or marker.kamera == null or not is_instance_valid(marker.kamera) or _menue_offen():
		return Vector2(-1.0, -1.0)
	var id: StringName = StringName(String(e.get("station", "")))
	if not _station_positionen.has(id):
		return Vector2(-1.0, -1.0)
	var welt: Vector3 = _station_positionen[id] as Vector3 + Vector3(0.0, 1.0, 0.0)
	if marker.kamera.is_position_behind(welt):
		return Vector2(-1.0, -1.0)
	return marker.kamera.unproject_position(welt)


func _menue_offen() -> bool:
	for sh in _sheets:
		if sh.ist_offen():
			return true
	return false


# --- Fuer das Tutorial ---------------------------------------------------------

## Worauf zeigt ein Tutorialschritt? Die Schritte kennen nur Namen.
func control_fuer(ziel: String) -> Control:
	if ziel.begins_with("bereich_") and bereichsmenue.ist_offen() and String(bereichsmenue.bereich_id) == ziel 			and bereichsmenue._knopf.visible:
		return bereichsmenue._knopf
	if ziel.begins_with("bereich_") and schnellkauf.ist_offen() and String(schnellkauf.bereich_id) == ziel 			and schnellkauf._knopf.visible:
		return schnellkauf._knopf
	match ziel:
		"knopf_upgrade":
			return stationsmenue._ausbau if stationsmenue.ist_offen() else null
		"ziel_balken":
			return kopfleiste
		"zielleiste":
			return _zielkarte if _zielkarte.visible else null
		"engpass_ausbau":
			# Der Ausbau-Knopf, wenn gerade die langsamste Station offen ist; sonst zeigt der Ring auf sie.
			if stationsmenue.ist_offen() and stationsmenue.station_id == kern.kette.bottleneck():
				return stationsmenue._ausbau
			return null
		"menue_ziele":
			return menueleiste.knopf(&"ziele")
		"menue_ausbau":
			return menueleiste.knopf(&"ausbau")
		"ausstattung":
			# Nur die erste Karte (die bezahlbare), nicht alle drei samt gesperrten:
			# genau EIN Ziel fuer Ring und Hand.
			if not stationsmenue.ist_offen():
				return null
			var karten: VBoxContainer = stationsmenue._karten
			if karten.get_child_count() > 0 and not karten.get_child(0).is_queued_for_deletion():
				return karten.get_child(0) as Control
			return karten
	return null


func sheet_offen() -> bool:
	for s in _sheets:
		if s.ist_offen():
			return true
	return false


func offenes_menue_hoehe() -> float:
	for s in _sheets:
		if s.ist_offen():
			return s.kartenhoehe() + s.unten_frei
	return Menueleiste.HOEHE if menueleiste == null or menueleiste.visible else 24.0


## Schmaler Segmentbalken des Weltziels (K7): Fuellung bis zum Anteil, ein Strich je
## Zwischenmarke, erreichte Marken in Gold.
class SegmentBalken extends Control:
	var anteil: float = 0.0
	var marken: Array = []

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func setze(neuer_anteil: float, neue_marken: Array) -> void:
		if is_equal_approx(neuer_anteil, anteil) and neue_marken.size() == marken.size():
			var gleich: bool = true
			for i in range(marken.size()):
				if bool((marken[i] as Dictionary).get("bereit", false)) != bool((neue_marken[i] as Dictionary).get("bereit", false)) 						or bool((marken[i] as Dictionary).get("eingeloest", false)) != bool((neue_marken[i] as Dictionary).get("eingeloest", false)):
					gleich = false
			if gleich:
				return
		anteil = neuer_anteil
		marken = neue_marken
		queue_redraw()

	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		var rund: float = minf(r.size.y * 0.5, float(UiStil.RADIUS_CHIP))
		var grund := UiStil.balken_grund()
		draw_style_box(grund, r)
		var innen: Rect2 = r.grow(-float(UiStil.KONTUR_CHIP))
		if anteil > 0.0 and innen.size.x > 0.0:
			var f := StyleBoxFlat.new()
			f.bg_color = UiStil.akzent()
			f.set_corner_radius_all(int(rund))
			f.anti_aliasing = true
			draw_style_box(f, Rect2(innen.position, Vector2(maxf(innen.size.x * clampf(anteil, 0.0, 1.0), innen.size.y), innen.size.y)))
		for m in marken:
			var d: Dictionary = m as Dictionary
			var x: float = innen.position.x + innen.size.x * clampf(float(d.get("wert", 0.0)), 0.0, 1.0)
			if x >= innen.end.x - 2.0:
				continue
			var farbe: Color = UiStil.GOLD if bool(d.get("eingeloest", false)) or bool(d.get("bereit", false)) else UiStil.TINTE
			draw_line(Vector2(x, innen.position.y), Vector2(x, innen.end.y), farbe, 3.0)


## Pruefschalter aus user://start_args.txt (Debug-Builds am Handy, siehe main.gd).
static func _start_args_haben(schalter: String) -> bool:
	if not OS.is_debug_build() or not FileAccess.file_exists("user://start_args.txt"):
		return false
	return FileAccess.get_file_as_string("user://start_args.txt").strip_edges().split(" ", false).has(schalter)
