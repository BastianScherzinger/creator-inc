## Die kleineren Menues: Ziele, Handy, Uebersicht, Fortschritt, Raum, Einstellungen.
##
## In einer Datei, weil jedes fuer sich nur eine Liste mit Knoepfen ist. Das
## Stationsmenue ist gross genug fuer eine eigene (stationsmenue.gd).
class_name Menues
extends RefCounted


## Der Pseudo-Raum fuer die Startzone, die keinen Bereich hat (das erste Zimmer).
const START_RAUM: StringName = &"start"


## Die Zonen eines Raums (Bereich oder Startzone) in der aktuellen Welt.
static func zonen_des_raums(kern: GameCore, bereich_id: StringName) -> Array[Dictionary]:
	var treffer: Array[Dictionary] = []
	if bereich_id == START_RAUM:
		var start: Dictionary = kern.welten.startzone(kern.welt_index)
		if not start.is_empty():
			treffer.append(start)
		return treffer
	for eintrag in kern.welten.zonen(kern.welt_index):
		var z: Dictionary = eintrag as Dictionary
		if StringName(String(z.get("bereich", ""))) == bereich_id:
			treffer.append(z)
	return treffer


## Die Stationen, die in einem Raum stehen (Reihenfolge der Kette).
static func stationen_des_raums(kern: GameCore, bereich_id: StringName) -> Array[StringName]:
	var ids: Array[StringName] = []
	for z in zonen_des_raums(kern, bereich_id):
		for id in kern.welten.stationen_in_zone(kern.welt_index, z):
			if not ids.has(id):
				ids.append(id)
	return ids


## Gibt es an dieser Station einen Kauf, den man sich jetzt leisten kann?
static func kauf_moeglich(kern: GameCore, s: StationModel) -> bool:
	if s == null or not s.freigeschaltet:
		return false
	if s.kann_ausbauen() and kern.kapital >= s.naechste_kosten():
		return true
	for p in s.ausstattung:
		if not p.ist_max() and p.freigegeben(s.stufe) and kern.kapital >= p.naechste_kosten():
			return true
	return false


## Die Kette eines Raums fuers Panel: das letzte erledigte Ziel, das aktuelle,
## das naechste -- hoechstens drei Glieder. Die Daten liefert der Kern
## (`kette_ziele`). Jedes Glied: {ziel (Definition), zustand: erledigt|jetzt|danach,
## fertig (einloesbar), fortschritt, belohnung}.
static func kette_anzeige(kern: GameCore, bereich_id: StringName) -> Array[Dictionary]:
	var kette_id: String = "start" if bereich_id == START_RAUM else String(bereich_id)
	var alle: Array[Dictionary] = kern.kette_ziele(kette_id)
	var ausgabe: Array[Dictionary] = []
	var aktuell: int = -1
	for i in range(alle.size()):
		if String(alle[i]["status"]) != "erledigt":
			aktuell = i
			break
	if aktuell < 0:
		# Alles geschafft: die letzten beiden als Beleg.
		for i in range(maxi(0, alle.size() - 2), alle.size()):
			ausgabe.append(_glied(kern, alle[i], "erledigt"))
		return ausgabe
	if aktuell > 0:
		ausgabe.append(_glied(kern, alle[aktuell - 1], "erledigt"))
	ausgabe.append(_glied(kern, alle[aktuell], "jetzt"))
	var rest: int = 3 - ausgabe.size()
	for i in range(aktuell + 1, mini(alle.size(), aktuell + 1 + rest)):
		ausgabe.append(_glied(kern, alle[i], "danach"))
	return ausgabe


static func _glied(kern: GameCore, eintrag: Dictionary, zustand: String) -> Dictionary:
	return {"ziel": kern.ziele.definition(String(eintrag["id"])), "zustand": zustand,
		"fertig": String(eintrag["status"]) == "bereit", "fortschritt": float(eintrag["fortschritt"]),
		"belohnung": float(eintrag["belohnung"])}


## Eine Zeile, die als Ganzes antippbar ist. Ein Tippen, das eigentlich ein
## Wischen in der Liste war, zaehlt nicht.
static func _tippbar(karte: Control, aktion: Callable) -> void:
	karte.mouse_filter = Control.MOUSE_FILTER_STOP
	var start := [Vector2.ZERO]
	karte.gui_input.connect(func(e: InputEvent) -> void:
		# Nur Mausereignisse: Godot spiegelt jeden Touch als Maus (und umgekehrt),
		# beide zu werten hiesse doppelt zu feuern (RELEASE_PLAN 2.E).
		if not (e is InputEventMouseButton):
			return
		var maus := e as InputEventMouseButton
		if maus.button_index != MOUSE_BUTTON_LEFT:
			return
		var pos: Vector2 = maus.position
		if maus.pressed:
			start[0] = pos
			return
		if UiStil.ist_tipp(e):
			if pos.distance_to(start[0]) < 24.0:
				UiStil.eindruecken(karte)
				aktion.call())


## --- Ziele -------------------------------------------------------------------
class Zielemenue extends Sheet:
	signal eingeloest(betrag: float, von: Vector2)
	## Ein offenes Ziel angetippt: hinspringen (Station oder Raum).
	signal ziel_gewaehlt(ziel_id: String)
	## Eine Raum-Kette angetippt: das Raum-Panel dazu.
	signal bereich_gewaehlt(id: StringName)

	const LISTE_MAX: float = 470.0

	var kern: GameCore
	var thema: ThemeData
	var _scroll: WischScroll
	var _liste: VBoxContainer
	var _zaehler_feld: PanelContainer
	var _zaehler: Label
	var _missionen: PanelContainer
	var _kapitel: PanelContainer

	func _init() -> void:
		super()
		_kapitel = PanelContainer.new()
		_kapitel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inhalt.add_child(_kapitel)
		_zaehler_feld = PanelContainer.new()
		_zaehler_feld.add_theme_stylebox_override("panel", UiStil.chip(UiStil.PAPIER, float(UiStil.A3), 2.0, 0.0))
		_zaehler_feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_zaehler = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
		_zaehler_feld.add_child(_zaehler)
		kopf.add_child(_zaehler_feld)
		kopf.move_child(_zaehler_feld, 1)
		_missionen = PanelContainer.new()
		inhalt.add_child(_missionen)
		_scroll = WischScroll.new()
		_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		inhalt.add_child(_scroll)
		_liste = VBoxContainer.new()
		_liste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_liste.add_theme_constant_override("separation", UiStil.A3)
		_scroll.add_child(_liste)

	## Die Missionen der Welt: Ziele mit eigenem Namen in der Themendatei
	## (Abschnitt "ziele"). Nur ihre IDs -- Kommentare zaehlen nicht.
	func _missions_ids() -> Array[String]:
		var ids: Array[String] = []
		if thema == null:
			return ids
		for schluessel in thema.abschnitt("ziele").keys():
			var s: String = String(schluessel)
			if not s.begins_with("_") and not kern.ziele.definition(s).is_empty():
				ids.append(s)
		return ids

	func _ist_mission(z: Dictionary) -> bool:
		return String(z.get("typ", "")) == "alle" or _missions_ids().has(String(z.get("id", "")))

	## Ein schmaler Streifen ganz oben: "Missionen 2/5" und alle Missionen der
	## Welt als Namen -- auch die, die noch nicht in der Liste stehen.
	func _baue_missionen() -> void:
		for kind in _missionen.get_children():
			kind.queue_free()
		var ids: Array[String] = _missions_ids()
		_missionen.visible = not ids.is_empty()
		if ids.is_empty():
			return
		var stil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3))
		stil.flaeche.border_color = UiStil.GOLD
		_missionen.add_theme_stylebox_override("panel", stil)
		var spalte := VBoxContainer.new()
		spalte.add_theme_constant_override("separation", UiStil.A2)
		_missionen.add_child(spalte)
		var geschafft: int = 0
		for ziel_id in ids:
			if kern.ziele.ist_eingeloest(ziel_id):
				geschafft += 1
		spalte.add_child(UiStil.label(UiText.t("missionen") % [geschafft, ids.size()], UiStil.GR_TEXT,
			UiStil.TINTE, UiStil.FETT))
		var fluss := HFlowContainer.new()
		fluss.add_theme_constant_override("h_separation", UiStil.A1 + 2)
		fluss.add_theme_constant_override("v_separation", UiStil.A1 + 2)
		spalte.add_child(fluss)
		for ziel_id in ids:
			var fertig: bool = kern.ziele.ist_eingeloest(ziel_id)
			var chip := PanelContainer.new()
			chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.GOLD if fertig else UiStil.PAPIER_2,
				float(UiStil.A2), 2.0, 0.0))
			var zeile := HBoxContainer.new()
			zeile.add_theme_constant_override("separation", UiStil.A1)
			chip.add_child(zeile)
			zeile.add_child(UiStil.symbolbild("haken" if fertig else "ziel", 22.0))
			zeile.add_child(UiStil.label(_kurzname(ziel_id), UiStil.GR_KLEIN - 2,
				UiStil.TINTE if fertig else UiStil.TINTE_2, UiStil.FETT))
			fluss.add_child(chip)

	## "Mission: Alle Aktien im Depot" -> "Alle Aktien im Depot".
	func _kurzname(ziel_id: String) -> String:
		var name: String = WeltTexte.ziel(thema, kern.ziele.definition(ziel_id))
		var teile: PackedStringArray = name.split(": ", false, 1)
		return teile[1] if teile.size() == 2 else name

	func aktualisiere() -> void:
		titel.text = UiText.t("ziele_titel")
		Menues.fuelle_kapitel_kopf(_kapitel, kern)
		_baue_missionen()
		_zaehler.text = "%d/%d" % [kern.ziele.anzahl_eingeloest(), kern.ziele.anzahl()]
		for kind in _liste.get_children():
			_liste.remove_child(kind)
			kind.queue_free()
		var sichtbar: Array[Dictionary] = kern.ziele.sichtbar()
		if sichtbar.is_empty():
			_liste.add_child(UiStil.label(UiText.t("ziele_leer"), UiStil.GR_MITTEL, UiStil.TINTE_2))
		else:
			_liste.add_child(_abschnitt(UiText.t("ziele_jetzt")))
			for z in sichtbar:
				_liste.add_child(_zeile(z))
		_baue_wege()
		# Hoehe nach Inhalt, aber das Panel deckt die Welt nie ganz zu (SHEET_MAX).
		_scroll.custom_minimum_size.y = clampf(_liste.get_combined_minimum_size().y, 120.0, LISTE_MAX)

	func _abschnitt(text: String) -> Label:
		return UiStil.label(text, UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT)

	## Die Wege: je Raum eine Kette aus Punkten (erledigt, jetzt, spaeter) --
	## man sieht, wie weit jeder Raum ist und was als Naechstes dort wartet.
	func _baue_wege() -> void:
		var zeilen: Array[Control] = []
		for kette_id in kern.ketten_ids():
			# "welt" sind die Missionen -- sie haben ihren eigenen Streifen oben.
			if kette_id == "welt":
				continue
			var raum: StringName = Menues.START_RAUM if kette_id == "start" else StringName(kette_id)
			zeilen.append(_weg_zeile(raum, kern.kette_ziele(kette_id)))
		if zeilen.is_empty():
			return
		_liste.add_child(_abschnitt(UiText.t("ziele_wege")))
		for zeile in zeilen:
			_liste.add_child(zeile)

	func _weg_zeile(raum: StringName, alle: Array[Dictionary]) -> Control:
		var karte_w := Sheet.innenkarte(float(UiStil.A3))
		var gekauft_jetzt: bool = raum == Menues.START_RAUM or kern.bereiche.ist_gekauft(raum)
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_w.add_child(zeile)
		var name: String = WeltTexte.bereich(thema, raum, "name")
		if name.is_empty():
			name = WeltTexte.kette(thema, "start" if raum == Menues.START_RAUM else String(raum))
		if name.is_empty() and thema != null:
			name = thema.welt_name
		var namen := UiStil.label(name, UiStil.GR_TEXT, UiStil.TINTE if gekauft_jetzt else UiStil.TINTE_2, UiStil.FETT)
		namen.custom_minimum_size = Vector2(150.0, 0.0)
		namen.clip_text = true
		namen.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		namen.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(namen)
		var punkte := HBoxContainer.new()
		punkte.add_theme_constant_override("separation", UiStil.A2)
		punkte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		punkte.alignment = BoxContainer.ALIGNMENT_CENTER
		punkte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(punkte)
		var geschafft: int = 0
		for z in alle:
			var status: String = String(z["status"])
			var farbe: Color = UiStil.PAPIER_2
			var art: String = "danach"
			if status == "erledigt":
				geschafft += 1
				farbe = UiStil.KAUFEN
				art = "erledigt"
			elif status == "bereit":
				farbe = UiStil.GOLD
				art = "jetzt"
			elif status == "laeuft":
				farbe = UiStil.akzent()
				art = "jetzt"
			punkte.add_child(_punkt(farbe, art))
		var zaehler := UiStil.label("%d/%d" % [geschafft, alle.size()], UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT)
		zaehler.custom_minimum_size = Vector2(64.0, 0.0)
		zaehler.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		zaehler.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(zaehler)
		Menues._tippbar(karte_w, func() -> void: bereich_gewaehlt.emit(raum))
		return karte_w

	## Ein Punkt der Kette: gefuellt = geschafft, Akzent = jetzt, leer = spaeter.
	func _punkt(farbe: Color, art: String) -> Control:
		var p := Panel.new()
		p.custom_minimum_size = Vector2(26.0, 26.0)
		p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		var stil := StyleBoxFlat.new()
		stil.bg_color = farbe
		stil.set_corner_radius_all(UiStil.RADIUS_CHIP)
		stil.border_color = UiStil.TINTE if art != "danach" else Color(UiStil.TINTE, 0.35)
		stil.set_border_width_all(UiStil.KONTUR_CHIP)
		p.add_theme_stylebox_override("panel", stil)
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		return p

	## Der "Warum"-Halbsatz zu einem Ziel (theme.json -> ziel_warum.<typ>); Missionen tragen ihren eigenen Namen.
	static func ziel_warum_text(t: ThemeData, z: Dictionary) -> String:
		if String(z.get("kette", "")) == "welt":
			return ""
		return WeltTexte.ziel_warum(t, String(z.get("typ", "")))

	func _zeile(z: Dictionary) -> PanelContainer:
		var fertig: bool = GoalSystem.erfuellt(z, kern.messwert)
		var karte_z := Sheet.innenkarte(float(UiStil.A3))
		var mission: bool = _ist_mission(z)
		if mission:
			# Missionen: Goldrand, damit sie in der Liste auffallen.
			var mstil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR + 1, float(UiStil.A3))
			mstil.flaeche.border_color = UiStil.GOLD
			karte_z.add_theme_stylebox_override("panel", mstil)
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_z.add_child(zeile)
		if not fertig:
			var sprung_id: String = String(z.get("id", ""))
			Menues._tippbar(karte_z, func() -> void: ziel_gewaehlt.emit(sprung_id))
		var bild := UiStil.symbolbild("geschenk" if fertig else "ziel", 52.0)
		bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile.add_child(bild)
		var spalte := VBoxContainer.new()
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.add_theme_constant_override("separation", UiStil.A2)
		spalte.alignment = BoxContainer.ALIGNMENT_CENTER
		zeile.add_child(spalte)
		if mission:
			var chip := PanelContainer.new()
			chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.akzent(), float(UiStil.A2), 0.0, 0.0))
			chip.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
			chip.add_child(UiStil.label(UiText.t("mission"), UiStil.GR_KLEIN - 3, UiStil.akzent_text(), UiStil.FETT))
			spalte.add_child(chip)
		var ziel_text: String = _kurzname(String(z.get("id", ""))) if mission else WeltTexte.ziel(thema, z)
		var text := UiStil.label(ziel_text, UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
		text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		spalte.add_child(text)
		# Warum sich das Ziel lohnt (K2 4.2): ein Halbsatz je Zieltyp aus dem Thema.
		var warum: String = ziel_warum_text(thema, z)
		if not warum.is_empty():
			var warum_label := UiStil.label(warum, UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
			warum_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			warum_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
			spalte.add_child(warum_label)
		var balken := UiStil.neuer_balken(16.0, UiStil.GOLD if fertig else UiStil.akzent())
		balken.value = GoalSystem.fortschritt(z, kern.messwert)
		spalte.add_child(balken)
		var betrag: float = maxf(kern.einkommen_pro_sekunde() * float(z.get("belohnung_sekunden", 0.0)),
			float(z.get("belohnung_minimum", 0.0)))
		var knopf := Button.new()
		knopf.custom_minimum_size = Vector2(160.0, UiStil.KNOPF_SEKUNDAER_H)
		knopf.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		knopf.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		if betrag > 0.0:
			knopf.icon = UiStil.symbol("muenze")
			knopf.add_theme_constant_override("icon_max_width", 28)
		knopf.text = UiStil.zahl(betrag) if betrag > 0.0 else UiText.t("abholen")
		knopf.disabled = not fertig
		# Einloesen ist kein Kauf: Gold, die Farbe der Belohnung.
		UiStil.faerbe_knopf(knopf, UiStil.GOLD if fertig else UiStil.PAPIER)
		var ziel_id: String = String(z.get("id", ""))
		knopf.pressed.connect(func() -> void:
			var von: Vector2 = knopf.get_global_rect().get_center()
			var bekommen: float = kern.loese_ziel_ein(StringName(ziel_id))
			if bekommen >= 0.0 and kern.ziele.ist_eingeloest(ziel_id):
				eingeloest.emit(bekommen, von)
			aktualisiere())
		zeile.add_child(knopf)
		return karte_z


## --- Handy -------------------------------------------------------------------
## Ein Messenger: runde Avatare mit Initiale, Sprechblasen mit dem Rand in der
## Farbe des Absenders, die neueste Nachricht unten. Folgen mehrere Nachrichten
## desselben Absenders, steht der Avatar nur an der ersten.
class Handymenue extends Sheet:
	var kern: GameCore
	var thema: ThemeData
	var _scroll: WischScroll
	var _liste: VBoxContainer
	var _anzahl_gezeigt: int = -1
	var _thema_gezeigt: ThemeData = null
	## Antworten des Spielers aus Szenen: Nachricht-ID -> Text (rechte Blase).
	var antworten: Dictionary = {}
	var _antworten_gezeigt: int = -1
	## K6 1c: Tipp auf eine Ortsblase -- beim naechsten Zeichnen zu dieser Nachricht scrollen.
	var ziel_nachricht: String = ""

	const AVATAR: float = 60.0
	var _kapitel: PanelContainer
	var _kapitel_gezeigt: int = -2

	func _init() -> void:
		super()
		_kapitel = PanelContainer.new()
		_kapitel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		inhalt.add_child(_kapitel)
		_scroll = WischScroll.new()
		_scroll.custom_minimum_size = Vector2(0.0, 500.0)
		_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		inhalt.add_child(_scroll)
		_liste = VBoxContainer.new()
		_liste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_liste.add_theme_constant_override("separation", UiStil.A2)
		_scroll.add_child(_liste)

	func aktualisiere() -> void:
		titel.text = UiText.t("handy_titel")
		if kern.kapitel_index() != _kapitel_gezeigt or thema != _thema_gezeigt:
			_kapitel_gezeigt = kern.kapitel_index()
			Menues.fuelle_kapitel_kopf(_kapitel, kern)
		var empfangen: Array[String] = kern.nachrichten.empfangen()
		if empfangen.size() == _anzahl_gezeigt and thema == _thema_gezeigt \
				and antworten.size() == _antworten_gezeigt:
			return
		_antworten_gezeigt = antworten.size()
		_anzahl_gezeigt = empfangen.size()
		_thema_gezeigt = thema
		for kind in _liste.get_children():
			kind.queue_free()
		if empfangen.is_empty():
			_liste.add_child(UiStil.label(UiText.t("handy_leer"), UiStil.GR_MITTEL, UiStil.TINTE_2))
			return
		var vorher: String = ""
		for nachricht_id in empfangen:
			var n: Dictionary = WeltTexte.nachricht(thema, nachricht_id)
			var von: String = String(n.get("von", ""))
			var zeile_n: Control = _zeile(von, String(n.get("text", "")), von != vorher)
			zeile_n.set_meta("nachricht", nachricht_id)
			_liste.add_child(zeile_n)
			vorher = von
			if antworten.has(nachricht_id):
				_liste.add_child(_antwort_zeile(String(antworten[nachricht_id])))
				vorher = ""
		if empfangen.size() <= 3:
			_liste.add_child(_leerzustand())
		await get_tree().process_frame
		_scroll.scroll_vertical = int(_scroll.get_v_scroll_bar().max_value)
		_zeige_ziel()

	## Zur Nachricht `ziel_nachricht` scrollen und sie kurz aufploppen lassen.
	func _zeige_ziel() -> void:
		if ziel_nachricht.is_empty():
			return
		for kind in _liste.get_children():
			if kind is Control and String((kind as Control).get_meta("nachricht", "")) == ziel_nachricht:
				var c: Control = kind as Control
				_scroll.scroll_vertical = int(maxf(c.position.y - float(UiStil.A4), 0.0))
				UiStil.aufploppen(c, 0.92)
				break
		ziel_nachricht = ""

	## Wenige Nachrichten: freundlicher Hinweis plus das naechste Ziel.
	func _leerzustand() -> Control:
		var karte_l := Sheet.innenkarte(float(UiStil.A3))
		karte_l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var spalte := VBoxContainer.new()
		spalte.add_theme_constant_override("separation", UiStil.A2)
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_l.add_child(spalte)
		spalte.add_child(UiStil.label(UiText.t("handy_mehr"), UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT))
		var offen: Array[Dictionary] = kern.ziele.sichtbar(1)
		if not offen.is_empty():
			var nachste: Label = UiStil.label(UiText.t("handy_naechstes") % WeltTexte.ziel(thema, offen[0]),
				UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
			nachste.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			spalte.add_child(nachste)
		return karte_l

	func neu_zeichnen() -> void:
		_antworten_gezeigt = -1
		if ist_offen():
			aktualisiere()

	## Die Antwort des Spielers: rechte Blase in der Akzentfarbe.
	func _antwort_zeile(text: String) -> Control:
		var zeile := HBoxContainer.new()
		zeile.alignment = BoxContainer.ALIGNMENT_END
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var blase := PanelContainer.new()
		var stil := UiStil.sticker(UiStil.akzent(), UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
			UiStil.SCHATTEN_Y - 1.0)
		stil.content_margin_left = float(UiStil.A4)
		stil.content_margin_right = float(UiStil.A4)
		stil.flaeche.corner_radius_top_right = 4
		blase.add_theme_stylebox_override("panel", stil)
		blase.mouse_filter = Control.MOUSE_FILTER_IGNORE
		blase.add_child(UiStil.label(text, UiStil.GR_TEXT + 1, UiStil.akzent_text(), UiStil.FETT))
		zeile.add_child(blase)
		return zeile

	func _zeile(von: String, text: String, mit_kopf: bool) -> Control:
		var farbe: Color = UiStil.absender_farbe(thema, von)
		var name: String = WeltTexte.absender(thema, von)
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if mit_kopf:
			zeile.add_child(UiStil.avatar(name, farbe, AVATAR))
		else:
			var luecke := Control.new()
			luecke.custom_minimum_size = Vector2(AVATAR, 0.0)
			luecke.mouse_filter = Control.MOUSE_FILTER_IGNORE
			zeile.add_child(luecke)
		var spalte := VBoxContainer.new()
		spalte.add_theme_constant_override("separation", UiStil.A1)
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(spalte)
		if mit_kopf:
			spalte.add_child(UiStil.label(name, UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT))
		var blase := PanelContainer.new()
		var stil := UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3),
			UiStil.SCHATTEN_Y - 1.0, farbe)
		stil.content_margin_left = float(UiStil.A4)
		stil.content_margin_right = float(UiStil.A4)
		# Die Ecke zum Absender hin ist spitz -- das macht die Blase zur Sprechblase.
		stil.flaeche.corner_radius_top_left = 4
		stil.schatten.corner_radius_top_left = 4
		blase.add_theme_stylebox_override("panel", stil)
		blase.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		blase.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var t := UiStil.label(text, UiStil.GR_TEXT + 1, UiStil.TINTE, UiStil.TEXT_GEWICHT)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		# Kurze Nachrichten bleiben schmal, lange brechen vor dem Rand um.
		var breite: float = t.get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1,
			UiStil.GR_TEXT + 1).x
		t.custom_minimum_size = Vector2(minf(breite + 4.0, 500.0), 0.0)
		blase.add_child(t)
		spalte.add_child(blase)
		return zeile


## --- Uebersicht (Ausbau) -----------------------------------------------------
class Ausbaumenue extends Sheet:
	signal station_gewaehlt(id: StringName)
	signal bereich_gewaehlt(id: StringName)
	signal abgelehnt

	var kern: GameCore
	var thema: ThemeData
	var _liste: VBoxContainer

	func _init() -> void:
		super()
		var scroll := WischScroll.new()
		scroll.custom_minimum_size = Vector2(0.0, 500.0)
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		inhalt.add_child(scroll)
		_liste = VBoxContainer.new()
		_liste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_liste.add_theme_constant_override("separation", UiStil.A3)
		scroll.add_child(_liste)

	func aktualisiere() -> void:
		# Derselbe Name wie der Knopf in der Menueleiste.
		titel.text = WeltTexte.menue(thema, "ausbau")
		for kind in _liste.get_children():
			kind.queue_free()
		for id in Ids.ALL_STATIONS:
			var s: StationModel = kern.kette.station(id)
			if s != null and s.freigeschaltet:
				_liste.add_child(_station_zeile(s))
		for bereich_id in kern.bereiche.ids():
			if not kern.bereiche.ist_gekauft(bereich_id):
				_liste.add_child(_bereich_zeile(bereich_id))

	func _station_zeile(s: StationModel) -> PanelContainer:
		var karte_s := Sheet.innenkarte(float(UiStil.A2))
		var id: StringName = s.id
		Menues._tippbar(karte_s, func() -> void: station_gewaehlt.emit(id))
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_s.add_child(zeile)
		var bild := TextureRect.new()
		var pfad: String = Stationsmenue.ICON_PFAD % [kern.welt_id(), String(id)]
		bild.texture = load(pfad) as Texture2D if ResourceLoader.exists(pfad) else UiStil.symbol("werkzeug")
		bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		bild.custom_minimum_size = Vector2(76.0, 76.0)
		bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(bild)
		var spalte := VBoxContainer.new()
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.alignment = BoxContainer.ALIGNMENT_CENTER
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(spalte)
		var name_zeile := HBoxContainer.new()
		name_zeile.add_theme_constant_override("separation", UiStil.A2)
		name_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(name_zeile)
		name_zeile.add_child(UiStil.label(WeltTexte.station_name(thema, id), UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT))
		if kern.kette.bottleneck() == id:
			name_zeile.add_child(UiStil.symbolbild("warnung", 30.0))
		var stufe_text: String = UiText.t("stufe_von") % [s.stufe, s.max_stufe] if s.max_stufe > 0 else UiText.t("stufe") % s.stufe
		var info := HBoxContainer.new()
		info.add_theme_constant_override("separation", UiStil.A2)
		info.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(info)
		info.add_child(UiStil.label(stufe_text, UiStil.GR_KLEIN, UiStil.TINTE_2, UiStil.FETT))
		if s.sterne_moeglich() > 0:
			info.add_child(Sheet.sterne(s.sterne(), s.sterne_moeglich(), 22.0))
		var knopf := Button.new()
		knopf.custom_minimum_size = Vector2(160.0, UiStil.TIPPZIEL)
		knopf.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		knopf.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		if s.ist_max():
			knopf.text = UiText.t("fertig")
			knopf.icon = UiStil.symbol("haken")
			knopf.add_theme_constant_override("icon_max_width", 28)
			knopf.disabled = true
		else:
			var preis: float = s.naechste_kosten()
			knopf.icon = UiStil.symbol("pfeil_hoch")
			knopf.add_theme_constant_override("icon_max_width", 24)
			knopf.text = UiStil.preis(preis)
			knopf.disabled = kern.kapital < preis
			UiStil.faerbe_knopf(knopf, UiStil.KAUFEN if not knopf.disabled else UiStil.PAPIER)
		knopf.pressed.connect(func() -> void:
			if not kern.upgrade_station(id):
				abgelehnt.emit()
			aktualisiere())
		zeile.add_child(knopf)
		return karte_s

	## Ein gesperrter Raum: ruhige Flaeche, Preis als Aufkleber rechts.
	func _bereich_zeile(bereich_id: StringName) -> PanelContainer:
		var karte_b := PanelContainer.new()
		karte_b.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER_2, UiStil.RADIUS_KARTE,
			UiStil.KONTUR, float(UiStil.A2), 0.0, Color(UiStil.TINTE, 0.5)))
		Menues._tippbar(karte_b, func() -> void: bereich_gewaehlt.emit(bereich_id))
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_b.add_child(zeile)
		var schloss := UiStil.symbolbild("schloss", 56.0)
		var eigen: Texture2D = UiStil.bereich_bild(thema, kern.welt_id(), bereich_id)
		if eigen != null:
			schloss.texture = eigen
		schloss.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile.add_child(schloss)
		var spalte := VBoxContainer.new()
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.alignment = BoxContainer.ALIGNMENT_CENTER
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(spalte)
		spalte.add_child(UiStil.label(WeltTexte.bereich(thema, bereich_id, "name"), UiStil.GR_MITTEL - 1,
			UiStil.TINTE, UiStil.FETT))
		var bonus := UiStil.label(WeltTexte.bonus(thema, kern, bereich_id), UiStil.GR_KLEIN, UiStil.TINTE_2,
			UiStil.TEXT_GEWICHT)
		bonus.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		spalte.add_child(bonus)
		# Limette heisst "kaufbar". Ein Preis, den man sich nicht leisten kann,
		# steht auf Papier.
		var bezahlbar: bool = kern.bereiche.verfuegbar(bereich_id) \
			and kern.kapital >= kern.bereiche.kosten(bereich_id)
		zeile.add_child(Menues.preis_sticker(kern.bereiche.kosten(bereich_id), bezahlbar))
		return karte_b


## Ein Preis als Aufkleber: Muenze und Zahl, Limette wenn bezahlbar.
## K5: Kopf "Kapitel 2 · Zu wenig Platz" mit der Aufgabe als Untertitel (Ziele, Handy).
## Fuellt `feld` neu; ohne Kapiteldaten unsichtbar.
static func fuelle_kapitel_kopf(feld: PanelContainer, kern: GameCore) -> void:
	for kind in feld.get_children():
		feld.remove_child(kind)
		kind.queue_free()
	var zeile: String = Hud.kapitel_zeile(kern)
	feld.visible = not zeile.is_empty()
	if zeile.is_empty():
		return
	var stil := UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3))
	stil.flaeche.border_color = UiStil.akzent()
	stil.flaeche.border_width_left = 10
	feld.add_theme_stylebox_override("panel", stil)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A1)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	feld.add_child(spalte)
	var oben := HBoxContainer.new()
	oben.add_theme_constant_override("separation", UiStil.A2)
	oben.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(oben)
	var titel_label := UiStil.label(zeile, UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT)
	titel_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	oben.add_child(titel_label)
	# Der Bogen der Welt als Punkte: erledigt/laufend gold, spaeter grau.
	var nummer: int = kern.kapitel_index() + 1
	for i in kern.kapitel.anzahl():
		var p := Panel.new()
		p.custom_minimum_size = Vector2(26.0 if i + 1 == nummer else 14.0, 14.0)
		p.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		p.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD if i + 1 <= nummer else UiStil.PAPIER_2,
			UiStil.RADIUS_CHIP, UiStil.KONTUR_CHIP, 0.0, 0.0))
		p.mouse_filter = Control.MOUSE_FILTER_IGNORE
		oben.add_child(p)
	var aufgabe: String = Hud.kapitel_aufgabe(kern)
	if not aufgabe.is_empty():
		var a := UiStil.label(aufgabe, UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		a.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		spalte.add_child(a)


static func preis_sticker(preis: float, bezahlbar: bool) -> PanelContainer:
	var chip := PanelContainer.new()
	chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.KAUFEN if bezahlbar else UiStil.PAPIER,
		float(UiStil.A3), float(UiStil.A1 + 2), 2.0))
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A1 + 2)
	zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_child(zeile)
	zeile.add_child(UiStil.symbolbild("muenze", 30.0))
	zeile.add_child(UiStil.label(UiStil.preis(preis), UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT))
	return chip


## --- Fortschritt -------------------------------------------------------------
class Fortschrittsmenue extends Sheet:
	var kern: GameCore
	var thema: ThemeData
	var _prozent: Label
	var _gesamt: ProgressBar
	var _teile: Array = []
	var _raeume: HFlowContainer

	func _init() -> void:
		super()
		var kopfzeile := HBoxContainer.new()
		kopfzeile.add_theme_constant_override("separation", UiStil.A4)
		inhalt.add_child(kopfzeile)
		_prozent = UiStil.label("", UiStil.GR_RIESIG, UiStil.TINTE, UiStil.FETT)
		_prozent.custom_minimum_size = Vector2(180.0, 0.0)
		kopfzeile.add_child(_prozent)
		_gesamt = UiStil.neuer_balken(32.0)
		_gesamt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_gesamt.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		kopfzeile.add_child(_gesamt)
		var tafel := Sheet.innenkarte(float(UiStil.A4))
		inhalt.add_child(tafel)
		var tafel_spalte := VBoxContainer.new()
		tafel_spalte.add_theme_constant_override("separation", UiStil.A3)
		tafel.add_child(tafel_spalte)
		for schluessel in ["teil_stufen", "teil_ausstattung", "teil_bereiche"]:
			var teil: Array = Sheet.balken_mit_text()
			(teil[1] as Label).add_theme_color_override("font_color", UiStil.TINTE)
			tafel_spalte.add_child(teil[0] as Control)
			_teile.append([schluessel, teil[1], teil[2]])
		_raeume = HFlowContainer.new()
		_raeume.add_theme_constant_override("h_separation", UiStil.A2)
		_raeume.add_theme_constant_override("v_separation", UiStil.A2)
		inhalt.add_child(_raeume)

	func aktualisiere() -> void:
		# K3 A2 (N2): derselbe Name wie in der Kopfleiste -- das Welt-Ziel, nicht der Weltname.
		var ziel_name: String = WeltTexte.welt_ziel(thema)
		titel.text = ziel_name if not ziel_name.is_empty() else UiText.t("fortschritt_titel")
		var anteil: float = kern.weltwechsel_fortschritt()
		_prozent.text = "%d %%" % int(floorf(anteil * 100.0))
		_gesamt.value = anteil
		var a: Dictionary = kern.abschluss_anteile()
		var werte: Array = [a["stufen"], a["ausstattung"], a["bereiche"]]
		for i in range(_teile.size()):
			var t: Array = _teile[i]
			(t[1] as Label).text = "%s  %d %%" % [UiText.t(String(t[0])), int(floorf(float(werte[i]) * 100.0))]
			(t[2] as ProgressBar).value = float(werte[i])
		for kind in _raeume.get_children():
			kind.queue_free()
		for bereich_id in kern.bereiche.ids():
			var gekauft: bool = kern.bereiche.ist_gekauft(bereich_id)
			var chip := PanelContainer.new()
			chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.PAPIER if gekauft else UiStil.PAPIER_2,
				float(UiStil.A3), float(UiStil.A1), 2.0 if gekauft else 0.0))
			var zeile := HBoxContainer.new()
			zeile.add_theme_constant_override("separation", UiStil.A1 + 2)
			chip.add_child(zeile)
			zeile.add_child(UiStil.symbolbild("haken" if gekauft else "schloss", 30.0))
			zeile.add_child(UiStil.label(WeltTexte.bereich(thema, bereich_id, "name"), UiStil.GR_KLEIN + 1,
				UiStil.TINTE if gekauft else UiStil.TINTE_2, UiStil.FETT))
			_raeume.add_child(chip)


## --- Ein Raum ----------------------------------------------------------------
##
## Ein Panel fuer JEDEN Raum (RELEASE_PLAN 4, DESIGN_OVERHAUL 4.3). Gekauft:
## je Station EINE Zeile (Stufe, Nutzen, Ausbau-Knopf) und die Ziel-Kette des
## Raums (✓ erledigt, ● jetzt, ○ danach). Genau ein Kauf ist Limette -- der, der
## sich am meisten lohnt. Ungekauft: zuerst das, was man bekommt, dann der
## grosse Kaufknopf, der Erklaersatz zuletzt.
##
## Variante "a": Stationen zuerst, Ziel-Kette darunter. Variante "b": Kette zuerst.
class Bereichsmenue extends Sheet:
	signal gekauft(id: StringName)
	signal abgelehnt
	## Zeile angetippt: das Stationsmenue dazu soll aufgehen.
	signal station_gewaehlt(id: StringName)
	## "Naechster Raum"-Zeile angetippt.
	signal bereich_gewaehlt(id: StringName)
	## Ein Kauf in einer Zeile: Position des Knopfes und Text (z. B. "+3,2 €/s").
	signal ausgegeben(von: Vector2, text: String)
	## Das aktuelle Kettenziel angetippt: hinspringen.
	signal ziel_gewaehlt(ziel_id: String)

	## Hoechste Hoehe der Liste: Das Panel soll die Welt nicht verdecken (SHEET_MAX).
	const LISTE_MAX: float = 400.0
	const KETTE_MAX: int = 3

	var kern: GameCore
	var thema: ThemeData
	var bereich_id: StringName = &""
	var _bild: TextureRect
	var _bonus_feld: PanelContainer
	var _bonus: Label
	var _held: PanelContainer
	var _held_bild: TextureRect
	var _held_titel: Label
	var _held_text: Label
	var _held_bonus: Label
	var _erklaerung: Label
	var _knopf: Button
	var _scroll: WischScroll
	var _liste: VBoxContainer
	var _naechster: PanelContainer
	var _naechster_text: Label
	var _naechster_id: StringName = &""
	var _bauzustand: String = ""
	var _karten: Dictionary = {}          ## station_id -> Dictionary mit Anzeigeteilen
	var _kette_balken: ProgressBar
	var _kette_ziel: Dictionary = {}
	## Belohnte Werbung "Rest geschenkt" (K3 C1). Hud setzt den Dienst.
	var werbung: AdService:
		set(w):
			werbung = w
			if w != null:
				w.belohnung_verdient.connect(_auf_werbung)
				w.nicht_verfuegbar.connect(func(_p: StringName, _g: String) -> void: _sofort_ziel = &"")
	var _sofort: Button
	var _sofort_hinweis: Label
	var _sofort_ziel: StringName = &""
	var _sofort_gezeigt: bool = false

	func _init() -> void:
		super()
		# Raumbild und Bonus wohnen im Titelstreifen: Name, was er bringt, Kreuz.
		_bild = UiStil.symbolbild("haus", 56.0)
		_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		kopf.add_child(_bild)
		kopf.move_child(_bild, 0)
		_bonus_feld = PanelContainer.new()
		_bonus_feld.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_bonus = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
		_bonus_feld.add_child(_bonus)
		kopf.add_child(_bonus_feld)
		kopf.move_child(_bonus_feld, kopf.get_child_count() - 2)

		# Ungekauft: die Held-Zeile -- was bekomme ich?
		_held = Sheet.innenkarte(float(UiStil.A3))
		inhalt.add_child(_held)
		var held_zeile := HBoxContainer.new()
		held_zeile.add_theme_constant_override("separation", UiStil.A4)
		_held.add_child(held_zeile)
		_held_bild = UiStil.symbolbild("haus", 96.0)
		_held_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		held_zeile.add_child(_held_bild)
		var held_spalte := VBoxContainer.new()
		held_spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		held_spalte.add_theme_constant_override("separation", UiStil.A1)
		held_spalte.alignment = BoxContainer.ALIGNMENT_CENTER
		held_zeile.add_child(held_spalte)
		_held_titel = UiStil.label("", UiStil.GR_GROSS, UiStil.TINTE, UiStil.FETT)
		_held_titel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		held_spalte.add_child(_held_titel)
		_held_bonus = UiStil.label("", UiStil.GR_TEXT, UiStil.PLUS_TEXT, UiStil.FETT)
		_held_bonus.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		held_spalte.add_child(_held_bonus)
		_held_text = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		_held_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		held_spalte.add_child(_held_text)

		_knopf = Sheet.kaufknopf()
		_knopf.icon = UiStil.symbol("muenze")
		_knopf.pressed.connect(func() -> void:
			var von: Vector2 = _knopf.get_global_rect().get_center()
			if kern.kaufe_bereich(bereich_id):
				gekauft.emit(bereich_id)
				ausgegeben.emit(von, "")
				schliessen()
			else:
				abgelehnt.emit()
				aktualisiere())
		inhalt.add_child(_knopf)

		_sofort_hinweis = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		_sofort_hinweis.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_sofort_hinweis.visible = false
		inhalt.add_child(_sofort_hinweis)
		_sofort = Sheet.kaufknopf(UiStil.GOLD)
		_sofort.visible = false
		_sofort.pressed.connect(func() -> void:
			if werbung == null or not werbung.ist_bereit(&"raum_sofort"):
				return
			_sofort_ziel = bereich_id
			_sofort.disabled = true
			_sofort.text = UiText.t("werbung_laeuft")
			werbung.zeige_belohnt(&"raum_sofort"))
		inhalt.add_child(_sofort)

		# Der Erklaersatz steht zuletzt -- nie vor der Zahl.
		_erklaerung = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		_erklaerung.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		inhalt.add_child(_erklaerung)

		# Gekauft: Stationszeilen und Ziel-Kette in einer Liste.
		_scroll = WischScroll.new()
		_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
		_scroll.custom_minimum_size = Vector2(0.0, LISTE_MAX)
		inhalt.add_child(_scroll)
		_liste = VBoxContainer.new()
		_liste.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_liste.add_theme_constant_override("separation", UiStil.A3)
		_scroll.add_child(_liste)

		_naechster = PanelContainer.new()
		_naechster.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE,
			UiStil.KONTUR, float(UiStil.A2), 0.0, Color(UiStil.TINTE, 0.5)))
		Menues._tippbar(_naechster, func() -> void:
			if _naechster_id != &"":
				bereich_gewaehlt.emit(_naechster_id))
		var nz := HBoxContainer.new()
		nz.add_theme_constant_override("separation", UiStil.A3)
		nz.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_naechster.add_child(nz)
		nz.add_child(UiStil.symbolbild("schloss", 36.0))
		_naechster_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
		_naechster_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_naechster_text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_naechster_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		nz.add_child(_naechster_text)
		nz.add_child(UiStil.symbolbild("play", 28.0))
		inhalt.add_child(_naechster)

	func zeige_bereich(id: StringName) -> void:
		bereich_id = id
		_bauzustand = ""
		oeffnen()

	func ist_start() -> bool:
		return bereich_id == Menues.START_RAUM

	func _name_des_raums() -> String:
		if ist_start():
			var n: String = WeltTexte.bereich(thema, bereich_id, "name")
			return n if not n.is_empty() else (thema.welt_name if thema != null else "")
		return WeltTexte.bereich(thema, bereich_id, "name")

	func aktualisiere() -> void:
		if bereich_id == &"" or kern == null:
			return
		var gekauft_jetzt: bool = ist_start() or kern.bereiche.ist_gekauft(bereich_id)
		titel.text = _name_des_raums()
		var eigen: Texture2D = UiStil.bereich_bild(thema, kern.welt_id(), bereich_id)
		_bild.texture = eigen if eigen != null else UiStil.symbol("haus")
		_bild.visible = not (ist_start() and eigen == null)
		var text: String = WeltTexte.bereich(thema, bereich_id, "text")
		_erklaerung.text = text
		# Der Erklaersatz steht nur noch dort, wo die Held-Zeile keinen eigenen hat.
		_erklaerung.visible = false
		_aktualisiere_bonus(gekauft_jetzt)
		if gekauft_jetzt:
			_aktualisiere_gekauft()
		else:
			_aktualisiere_ungekauft()

	## Der Bonus-Chip im Titelstreifen: "Alles x1,25" -- nur im gekauften Raum.
	func _aktualisiere_bonus(gekauft_jetzt: bool) -> void:
		var bonus_text: String = ""
		if gekauft_jetzt and not ist_start():
			# Was der Raum bringt: sein Bonus, sonst die Station, die er freigeschaltet hat.
			var bringt: String = WeltTexte.bonus(thema, kern, bereich_id).split(" · ")[0]
			bonus_text = (bringt + " ✓") if not bringt.is_empty() else ""
		_bonus.text = bonus_text
		_bonus_feld.visible = not bonus_text.is_empty()
		_bonus_feld.add_theme_stylebox_override("panel", UiStil.chip(UiStil.KAUFEN_TIEF.lerp(UiStil.KAUFEN, 0.5),
			float(UiStil.A3), float(UiStil.A1), 2.0))

	# --- Ungekauft: Was bekomme ich? ---------------------------------------------

	func _aktualisiere_ungekauft() -> void:
		if _bauzustand != "ungekauft":
			_bauzustand = "ungekauft"
			_leere_liste()
		_scroll.visible = false
		_naechster.visible = false
		_held.visible = true
		var eigen: Texture2D = UiStil.bereich_bild(thema, kern.welt_id(), bereich_id)
		_held_bild.texture = eigen if eigen != null else UiStil.symbol("haus")
		var unlock_id: StringName = kern.bereiche.schaltet_frei(bereich_id)
		var station_id: StringName = GameCore._station_zu_freischaltung(unlock_id)
		var danach: String = WeltTexte.bereich(thema, bereich_id, "danach")
		if danach.is_empty() and station_id != &"":
			danach = UiText.t("raum_danach") % WeltTexte.station_name(thema, station_id)
		_held_titel.text = danach if not danach.is_empty() else _name_des_raums()
		var bonus: String = WeltTexte.bonus(thema, kern, bereich_id).split(" · ")[0] if not kern.bereiche.bonus(bereich_id).is_empty() else ""
		_held_bonus.text = bonus
		_held_bonus.visible = not bonus.is_empty()
		var kurz: String = WeltTexte.station_kurz(thema, station_id) if station_id != &"" else ""
		# Ein Gedanke, ein Satz: die Stationszeile, sonst der Raumtext -- nie beide.
		if kurz.is_empty():
			kurz = WeltTexte.bereich(thema, bereich_id, "text")
		_held_text.text = kurz
		_held_text.visible = not kurz.is_empty()
		_knopf.visible = true
		if not kern.bereiche.verfuegbar(bereich_id):
			var wartet: String = WeltTexte.bereich(thema, bereich_id, "wartet")
			_knopf.text = wartet if not wartet.is_empty() else UiText.t("gesperrt")
			_knopf.disabled = true
			_knopf.icon = UiStil.symbol("schloss")
			UiStil.faerbe_knopf(_knopf, UiStil.GESPERRT)
		else:
			var preis: float = kern.bereiche.kosten(bereich_id)
			_knopf.text = UiText.t("raum_kaufen") % UiStil.preis(preis)
			_knopf.disabled = kern.kapital < preis
			if _knopf.disabled:
				_knopf.set_meta("fehlt", preis - kern.kapital)
			elif _knopf.has_meta("fehlt"):
				_knopf.remove_meta("fehlt")
			_knopf.icon = UiStil.symbol("muenze")
			UiStil.faerbe_knopf(_knopf, UiStil.KAUFEN if not _knopf.disabled else UiStil.PAPIER)
		_aktualisiere_sofort()

	## "Rest geschenkt": ab `ab_anteil` gespart bietet die Werbung den Fehlbetrag an. Der
	## Preis bleibt der Preis -- ohne Werbung wartet man einfach noch etwas.
	func _aktualisiere_sofort() -> void:
		var zeigen: bool = false
		var fehlt: float = 0.0
		if werbung != null and kern.bereiche.verfuegbar(bereich_id):
			var preis: float = kern.bereiche.kosten(bereich_id)
			fehlt = preis - kern.kapital
			var ab: float = float(werbung.wert(&"raum_sofort", "ab_anteil", 0.7))
			var warum: String = werbung.grund(&"raum_sofort")
			zeigen = fehlt > 0.0 and preis > 0.0 and kern.kapital / preis >= ab and (warum.is_empty() or warum == "laeuft")
		_sofort.visible = zeigen
		_sofort_hinweis.visible = zeigen
		if not zeigen:
			_sofort_gezeigt = false
			return
		_sofort_hinweis.text = UiText.t("werbung_raum_fehlt") % UiStil.preis(fehlt)
		var laeuft: bool = _sofort_ziel != &""
		_sofort.disabled = laeuft
		_sofort.text = UiText.t("werbung_laeuft") if laeuft else UiText.t("werbung_raum_sofort")
		if not _sofort_gezeigt:
			_sofort_gezeigt = true
			werbung.melde_angebot(&"raum_sofort")

	func _auf_werbung(art: StringName) -> void:
		if art != &"raum_sofort" or _sofort_ziel == &"":
			return
		var id: StringName = _sofort_ziel
		_sofort_ziel = &""
		if kern.bereiche.ist_gekauft(id):
			return
		var fehlt: float = kern.bereiche.kosten(id) - kern.kapital
		Hud.schreibe_gut(kern, fehlt)
		var von: Vector2 = _sofort.get_global_rect().get_center()
		if kern.kaufe_bereich(id):
			gekauft.emit(id)
			ausgegeben.emit(von, "")
			if bereich_id == id:
				schliessen()

	# --- Gekauft: Was steht hier, was kommt als Naechstes? ----------------------------

	func _aktualisiere_gekauft() -> void:
		_knopf.visible = false
		_sofort.visible = false
		_sofort_hinweis.visible = false
		_sofort_gezeigt = false
		_held.visible = false
		var ids: Array[StringName] = Menues.stationen_des_raums(kern, bereich_id)
		var offene: Array[StringName] = []
		for id in ids:
			var s: StationModel = kern.kette.station(id)
			if s != null and s.freigeschaltet:
				offene.append(id)
		var kette: Array[Dictionary] = Menues.kette_anzeige(kern, bereich_id)
		var kette_sig: String = ""
		for e in kette:
			kette_sig += "%s%s%s;" % [e["zustand"], (e["ziel"] as Dictionary).get("id", ""), e["fertig"]]
		var schluessel: String = "gekauft|%s|%d|%s|%s|%s" % [bereich_id, kern.welt_index,
			",".join(PackedStringArray(offene)), kette_sig, Experimente.variante("raum_panel")]
		if _bauzustand != schluessel:
			_bauzustand = schluessel
			_baue_liste(offene, kette)
		_scroll.visible = true
		_aktualisiere_zeilen(offene)
		_aktualisiere_kette(kette)
		_aktualisiere_naechsten()

	func _aktualisiere_naechsten() -> void:
		_naechster_id = &""
		for id in kern.bereiche.ids():
			if id != bereich_id and not kern.bereiche.ist_gekauft(id) and kern.bereiche.verfuegbar(id):
				_naechster_id = id
				break
		_naechster.visible = _naechster_id != &""
		if _naechster_id == &"":
			return
		_naechster_text.text = UiText.t("naechster_raum") % ("%s · %s €" % [
			WeltTexte.bereich(thema, _naechster_id, "name"), UiStil.preis(kern.bereiche.kosten(_naechster_id))])

	func _leere_liste() -> void:
		_karten.clear()
		_kette_balken = null
		for kind in _liste.get_children():
			_liste.remove_child(kind)
			kind.queue_free()

	func _baue_liste(ids: Array[StringName], kette: Array[Dictionary]) -> void:
		_leere_liste()
		var stationen := VBoxContainer.new()
		stationen.add_theme_constant_override("separation", UiStil.A3)
		stationen.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var teil_stationen: Control = stationen
		if ids.is_empty():
			stationen.add_child(UiStil.label(UiText.t("raum_leer"), UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.TEXT_GEWICHT))
		else:
			stationen.add_child(_abschnitt(UiText.t("hier_ausbauen")))
			for id in ids:
				stationen.add_child(_baue_zeile(id))
		var kette_box := VBoxContainer.new()
		kette_box.add_theme_constant_override("separation", UiStil.A2)
		kette_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if not kette.is_empty():
			var kette_name: String = WeltTexte.kette(thema, "start" if bereich_id == Menues.START_RAUM else String(bereich_id))
			kette_box.add_child(_abschnitt(kette_name if not kette_name.is_empty() else UiText.t("ziel_kette")))
			for e in kette:
				kette_box.add_child(_baue_kettenglied(e))
		if Experimente.variante("raum_panel") == "b" and not kette.is_empty():
			_liste.add_child(kette_box)
			_liste.add_child(teil_stationen)
		else:
			_liste.add_child(teil_stationen)
			if not kette.is_empty():
				_liste.add_child(kette_box)
		_scroll.scroll_vertical = 0
		var hoehe: float = _liste.get_combined_minimum_size().y
		_scroll.custom_minimum_size.y = clampf(hoehe, 120.0, LISTE_MAX)

	func _abschnitt(text: String) -> Label:
		var l := UiStil.label(text, UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		return l

	# --- Ziel-Kette: erledigt, jetzt, danach ---------------------------------------

	func _baue_kettenglied(e: Dictionary) -> Control:
		var z: Dictionary = e["ziel"] as Dictionary
		var zustand: String = String(e["zustand"])
		var jetzt: bool = zustand == "jetzt"
		var karte_k := PanelContainer.new()
		var fertig: bool = jetzt and bool(e["fertig"])
		var farbe: Color = UiStil.GOLD if fertig else (UiStil.PAPIER if jetzt else UiStil.PAPIER_2)
		var rand: Color = UiStil.TINTE if jetzt else Color(UiStil.TINTE, 0.35)
		karte_k.add_theme_stylebox_override("panel", UiStil.sticker(farbe, UiStil.RADIUS_KARTE - 4,
			UiStil.KONTUR if jetzt else UiStil.KONTUR_CHIP, float(UiStil.A2), 0.0, rand))
		karte_k.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_k.add_child(zeile)
		var sym: String = "haken" if zustand == "erledigt" else ("geschenk" if fertig else ("ziel" if jetzt else "schloss"))
		var bild := UiStil.symbolbild(sym, 36.0)
		bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		if zustand == "danach":
			bild.modulate = Color(1, 1, 1, 0.6)
		zeile.add_child(bild)
		var spalte := VBoxContainer.new()
		spalte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		spalte.add_theme_constant_override("separation", UiStil.A1)
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(spalte)
		var text := UiStil.label(WeltTexte.ziel(thema, z), UiStil.GR_TEXT if jetzt else UiStil.GR_HINWEIS + 2,
			UiStil.TINTE if zustand != "danach" else UiStil.TINTE_2, UiStil.FETT)
		text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		text.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(text)
		if jetzt:
			var balken := UiStil.neuer_balken(14.0, UiStil.TINTE if fertig else UiStil.akzent())
			balken.value = float(e["fortschritt"])
			spalte.add_child(balken)
			_kette_balken = balken
			_kette_ziel = z
		if zustand != "erledigt":
			var betrag: float = float(e["belohnung"])
			if betrag > 0.0:
				var chip := PanelContainer.new()
				chip.add_theme_stylebox_override("panel", UiStil.chip(UiStil.TINTE if fertig else (UiStil.GOLD if jetzt else UiStil.PAPIER),
					float(UiStil.A2), float(UiStil.A1), 2.0))
				chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
				var chip_zeile := HBoxContainer.new()
				chip_zeile.add_theme_constant_override("separation", UiStil.A1)
				chip_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
				chip.add_child(chip_zeile)
				chip_zeile.add_child(UiStil.symbolbild("geschenk", 24.0))
				chip_zeile.add_child(UiStil.label(UiStil.zahl(betrag), UiStil.GR_HINWEIS,
					UiStil.WEISS if fertig else UiStil.TINTE, UiStil.FETT))
				zeile.add_child(chip)
		if jetzt:
			var ziel_id: String = String(z.get("id", ""))
			Menues._tippbar(karte_k, func() -> void: ziel_gewaehlt.emit(ziel_id))
		return karte_k

	func _aktualisiere_kette(_kette: Array[Dictionary]) -> void:
		if _kette_balken != null and not _kette_ziel.is_empty():
			_kette_balken.value = GoalSystem.fortschritt(_kette_ziel, kern.messwert)

	# --- Stationszeilen -------------------------------------------------------------

	## Eine Station im Raum: Icon, Name, Stufe, Nutzen, ein Ausbau-Knopf. Darunter,
	## nur wenn eine Ausstattung sich jetzt lohnt, eine zweite Zeile mit ihrem Preis.
	func _baue_zeile(id: StringName) -> PanelContainer:
		var teile: Dictionary = {}
		var karte_s := Sheet.innenkarte(float(UiStil.A3))
		Menues._tippbar(karte_s, func() -> void: station_gewaehlt.emit(id))
		var spalte := VBoxContainer.new()
		spalte.add_theme_constant_override("separation", UiStil.A2)
		spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		karte_s.add_child(spalte)

		var kopf_zeile := HBoxContainer.new()
		kopf_zeile.add_theme_constant_override("separation", UiStil.A3)
		kopf_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(kopf_zeile)
		var icon := TextureRect.new()
		var pfad: String = Stationsmenue.ICON_PFAD % [kern.welt_id(), String(id)]
		icon.texture = load(pfad) as Texture2D if ResourceLoader.exists(pfad) else UiStil.symbol("werkzeug")
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.custom_minimum_size = Vector2(64.0, 64.0)
		icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		kopf_zeile.add_child(icon)
		var namen := VBoxContainer.new()
		namen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		namen.alignment = BoxContainer.ALIGNMENT_CENTER
		namen.add_theme_constant_override("separation", 0)
		namen.mouse_filter = Control.MOUSE_FILTER_IGNORE
		kopf_zeile.add_child(namen)
		var name_zeile := HBoxContainer.new()
		name_zeile.add_theme_constant_override("separation", UiStil.A2)
		name_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		namen.add_child(name_zeile)
		name_zeile.add_child(UiStil.label(WeltTexte.station_name(thema, id), UiStil.GR_TEXT + 2, UiStil.TINTE, UiStil.FETT))
		teile["engpass"] = UiStil.symbolbild("warnung", 26.0)
		name_zeile.add_child(teile["engpass"] as Control)
		var stufe_zeile := HBoxContainer.new()
		stufe_zeile.add_theme_constant_override("separation", UiStil.A2)
		stufe_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		namen.add_child(stufe_zeile)
		teile["stufe"] = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE_2, UiStil.FETT)
		stufe_zeile.add_child(teile["stufe"] as Control)
		teile["sterne_box"] = HBoxContainer.new()
		(teile["sterne_box"] as Control).mouse_filter = Control.MOUSE_FILTER_IGNORE
		stufe_zeile.add_child(teile["sterne_box"] as Control)
		teile["nutzen"] = UiStil.label("", UiStil.GR_TEXT, UiStil.PLUS_TEXT, UiStil.FETT)
		(teile["nutzen"] as Label).clip_text = true
		(teile["nutzen"] as Label).text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		(teile["nutzen"] as Label).mouse_filter = Control.MOUSE_FILTER_IGNORE
		namen.add_child(teile["nutzen"] as Control)
		var ausbau := Button.new()
		ausbau.custom_minimum_size = Vector2(190.0, UiStil.KNOPF_SEKUNDAER_H)
		ausbau.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		ausbau.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		ausbau.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		ausbau.add_theme_constant_override("icon_max_width", 26)
		ausbau.pressed.connect(func() -> void:
			var vorher: float = kern.einkommen_pro_sekunde()
			var von: Vector2 = ausbau.get_global_rect().get_center()
			if kern.upgrade_station(id):
				ausgegeben.emit(von, _gewinn_text(kern.einkommen_pro_sekunde() - vorher))
			else:
				abgelehnt.emit()
			aktualisiere())
		kopf_zeile.add_child(ausbau)
		teile["ausbau"] = ausbau

		# Zweite Zeile: die Ausstattung, die sich jetzt lohnt.
		var platz_zeile := HBoxContainer.new()
		platz_zeile.add_theme_constant_override("separation", UiStil.A3)
		platz_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		spalte.add_child(platz_zeile)
		teile["platz_zeile"] = platz_zeile
		var platz_bild := TextureRect.new()
		platz_bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		platz_bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		platz_bild.custom_minimum_size = Vector2(44.0, 44.0)
		platz_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		platz_bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
		platz_zeile.add_child(platz_bild)
		teile["platz_bild"] = platz_bild
		teile["platz_text"] = UiStil.label("", UiStil.GR_HINWEIS + 2, UiStil.TINTE, UiStil.FETT)
		(teile["platz_text"] as Label).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		(teile["platz_text"] as Label).clip_text = true
		(teile["platz_text"] as Label).text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		(teile["platz_text"] as Label).mouse_filter = Control.MOUSE_FILTER_IGNORE
		platz_zeile.add_child(teile["platz_text"] as Control)
		var platz_knopf := Button.new()
		platz_knopf.custom_minimum_size = Vector2(190.0, UiStil.KNOPF_SEKUNDAER_H - 12.0)
		platz_knopf.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT))
		platz_knopf.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
		platz_knopf.add_theme_constant_override("icon_max_width", 24)
		platz_knopf.pressed.connect(func() -> void:
			var platz_id: StringName = StringName(String(platz_knopf.get_meta("platz", "")))
			if platz_id == &"":
				return
			var vorher: float = kern.einkommen_pro_sekunde()
			var von: Vector2 = platz_knopf.get_global_rect().get_center()
			if kern.kaufe_ausstattung(id, platz_id):
				ausgegeben.emit(von, _gewinn_text(kern.einkommen_pro_sekunde() - vorher))
			else:
				abgelehnt.emit()
			aktualisiere())
		platz_zeile.add_child(platz_knopf)
		teile["platz_knopf"] = platz_knopf
		_karten[id] = teile
		return karte_s

	## Der eine Kauf im Raum, der sich am meisten lohnt (Mehreinnahme je Preis).
	## Nur er bekommt die Limette; alles andere bleibt Papier.
	func _bester_kauf(ids: Array[StringName]) -> String:
		var bester: String = ""
		var beste_rate: float = 0.0
		var jetzt: float = kern.einkommen_pro_sekunde()
		for id in ids:
			var s: StationModel = kern.kette.station(id)
			if s == null:
				continue
			if not s.ist_max() and kern.kapital >= s.naechste_kosten():
				var rate: float = (kern.einkommen_danach(id) - jetzt) / maxf(s.naechste_kosten(), 1.0)
				if rate > beste_rate and kern.einkommen_danach(id) - jetzt > maxf(jetzt * 0.001, 0.01):
					beste_rate = rate
					bester = String(id)
			for p in s.ausstattung:
				if p.ist_max() or not p.freigegeben(s.stufe) or kern.kapital < p.naechste_kosten():
					continue
				var mehr: float = kern.einkommen_danach(id, p.id) - jetzt
				if mehr > maxf(jetzt * 0.001, 0.01) and mehr / maxf(p.naechste_kosten(), 1.0) > beste_rate:
					beste_rate = mehr / maxf(p.naechste_kosten(), 1.0)
					bester = "%s:%s" % [id, p.id]
		return bester

	func _aktualisiere_zeilen(ids: Array[StringName]) -> void:
		var bester: String = _bester_kauf(ids)
		for id in ids:
			_aktualisiere_zeile(id, bester)

	func _aktualisiere_zeile(id: StringName, bester: String) -> void:
		var teile: Dictionary = _karten.get(id, {}) as Dictionary
		var s: StationModel = kern.kette.station(id)
		if teile.is_empty() or s == null:
			return
		var ist_engpass: bool = kern.kette.bottleneck() == id
		(teile["engpass"] as Control).visible = ist_engpass
		(teile["stufe"] as Label).text = UiText.t("stufe_von") % [s.stufe, s.max_stufe] if s.max_stufe > 0 \
			else UiText.t("stufe") % s.stufe
		var sterne_box: HBoxContainer = teile["sterne_box"] as HBoxContainer
		var sterne_zustand: Array = [s.sterne(), s.sterne_moeglich()]
		if sterne_box.get_meta("zustand", []) != sterne_zustand:
			sterne_box.set_meta("zustand", sterne_zustand)
			for kind in sterne_box.get_children():
				kind.queue_free()
			if s.sterne_moeglich() > 0:
				sterne_box.add_child(Sheet.sterne(s.sterne(), s.sterne_moeglich(), 20.0))
		var jetzt: float = kern.einkommen_pro_sekunde()
		var ausbau: Button = teile["ausbau"] as Button
		var nutzen: Label = teile["nutzen"] as Label
		if s.ist_max():
			ausbau.text = UiText.t("fertig")
			ausbau.icon = UiStil.symbol("haken")
			ausbau.disabled = true
			UiStil.faerbe_knopf(ausbau, UiStil.PAPIER)
			nutzen.text = ""
			nutzen.visible = false
		else:
			var preis: float = s.naechste_kosten()
			var bezahlbar: bool = kern.kapital >= preis
			var mehr: float = kern.einkommen_danach(id) - jetzt
			var wirkt: bool = mehr > maxf(jetzt * 0.001, 0.01)
			ausbau.text = UiStil.preis(preis)
			ausbau.icon = UiStil.symbol("pfeil_hoch")
			ausbau.disabled = not bezahlbar
			UiStil.faerbe_knopf(ausbau, UiStil.KAUFEN if bester == String(id) else UiStil.PAPIER)
			nutzen.visible = true
			if wirkt:
				nutzen.text = UiText.t("einnahmen_plus") % UiStil.zahl(mehr)
				nutzen.add_theme_font_size_override("font_size", UiStil.GR_MITTEL)
				nutzen.add_theme_color_override("font_color", UiStil.PLUS_TEXT)
			else:
				# Bringt der Kauf nichts, steht es leise da: nur wer der Engpass ist.
				var engpass: StringName = kern.kette.bottleneck()
				nutzen.text = UiText.t("engpass_ist") % WeltTexte.station_name(thema, engpass) \
					if engpass != &"" and engpass != id else UiText.t("bremst_nicht") % ""
				nutzen.add_theme_font_size_override("font_size", UiStil.GR_KLEIN)
				nutzen.add_theme_color_override("font_color", UiStil.TINTE_2)
		_aktualisiere_platzzeile(id, s, teile, bester, jetzt)

	## Die Ausstattungszeile zeigt den Platz, der sich jetzt am meisten lohnt --
	## oder gar nichts. Die ganze Auswahl liegt im Stationsmenue.
	func _aktualisiere_platzzeile(id: StringName, s: StationModel, teile: Dictionary, bester: String, jetzt: float) -> void:
		var zeile: Control = teile["platz_zeile"] as Control
		var beste_platz: EquipmentSlot = null
		var beste_mehr: float = 0.0
		for p in s.ausstattung:
			if p.ist_max() or not p.freigegeben(s.stufe):
				continue
			var mehr: float = kern.einkommen_danach(id, p.id) - jetzt
			if beste_platz == null or (kern.kapital >= p.naechste_kosten() and mehr > beste_mehr):
				beste_platz = p
				beste_mehr = mehr
		if beste_platz == null:
			zeile.visible = false
			return
		zeile.visible = true
		var p: EquipmentSlot = beste_platz
		var bild: TextureRect = teile["platz_bild"] as TextureRect
		var pfad: String = Stationsmenue.ICON_PFAD % [kern.welt_id(), "%s_%s_%d" % [id, p.id, maxi(p.modellstufe(), 1)]]
		bild.texture = load(pfad) as Texture2D if ResourceLoader.exists(pfad) else UiStil.symbol("geschenk")
		var text: String = "%s · %s" % [WeltTexte.platz_name(thema, id, p.id), UiText.t("stufe_von") % [p.stufe, p.max_stufe]]
		if beste_mehr > maxf(jetzt * 0.001, 0.01):
			text += "  " + UiText.t("einnahmen_plus") % UiStil.zahl(beste_mehr)
		(teile["platz_text"] as Label).text = text
		var knopf: Button = teile["platz_knopf"] as Button
		knopf.set_meta("platz", String(p.id))
		var kosten: float = p.naechste_kosten()
		knopf.text = UiStil.preis(kosten)
		knopf.icon = UiStil.symbol("muenze")
		knopf.disabled = kern.kapital < kosten
		UiStil.faerbe_knopf(knopf, UiStil.KAUFEN if bester == "%s:%s" % [id, p.id] else UiStil.PAPIER)

	func _gewinn_text(mehr: float) -> String:
		return UiText.t("einnahmen_plus") % UiStil.zahl(mehr) if mehr > 0.01 else ""


## --- Schnellkauf (K4 P1.1, K6 1c) -----------------------------------------------
## Tipp auf eine Raum-Plakette (jede Zoomstufe, jeder Zustand): das Menue des Raums.
## K6 1c: Unter dem grossen Vorschlag stehen ALLE uebrigen Verbesserungen des Raums
## (GameCore.kaeufe_im_raum, billigste zuerst), jede mit eigenem Kaufknopf -- man muss
## nicht erst suchen.
## Oben Raumname, dann die beste Verbesserung des Raums (GameCore.empfehlung_im_raum)
## mit Bild, Stufe und Nutzen "+X €/s", darunter der Kaufknopf mit Preis und klein
## "Raum ansehen →" (faehrt in den Raum wie bisher). Nach dem Kauf bleibt das Panel
## offen und zeigt den naechsten Vorschlag -- Kaufserie mit einem Finger.
## Gesperrter Raum: dieselbe Karte fuer den Raumkauf.
## Das Raum-Menue (Tipp auf die Raumplakette): ab W2e in game/ui/raum_panel.gd.
## Der Name bleibt, damit Hud und Tests unveraendert auf `Menues.Schnellkauf` zeigen.
class Schnellkauf extends RaumPanel:
	pass


## --- Einstellungen -----------------------------------------------------------
class Einstellungsmenue extends Sheet:
	signal ton_umgeschaltet(an: bool)
	signal laden_gedrueckt

	var ton_an: bool = true
	var _ton: Button
	var _ton_bild: TextureRect
	var _vib: Button
	var _vib_bild: TextureRect

	func _init() -> void:
		super()
		var karte_e := Sheet.innenkarte(float(UiStil.A3))
		inhalt.add_child(karte_e)
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A4)
		karte_e.add_child(zeile)
		_ton_bild = UiStil.symbolbild("ton_an", 64.0)
		_ton_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile.add_child(_ton_bild)
		var name := UiStil.label(UiText.t("ton"), UiStil.GR_GROSS, UiStil.TINTE, UiStil.FETT)
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		zeile.add_child(name)
		_ton = Button.new()
		_ton.custom_minimum_size = Vector2(160.0, UiStil.TIPPZIEL)
		_ton.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_MITTEL))
		_ton.add_theme_font_size_override("font_size", UiStil.GR_MITTEL)
		_ton.pressed.connect(func() -> void:
			ton_an = not ton_an
			ton_umgeschaltet.emit(ton_an)
			aktualisiere())
		zeile.add_child(_ton)
		# Vibration: eigener Schalter, abschaltbar (Haptik lebt in einer eigenen Datei).
		var karte_v := Sheet.innenkarte(float(UiStil.A3))
		inhalt.add_child(karte_v)
		var zeile_v := HBoxContainer.new()
		zeile_v.add_theme_constant_override("separation", UiStil.A4)
		karte_v.add_child(zeile_v)
		_vib_bild = UiStil.symbolbild("blitz", 64.0)
		_vib_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile_v.add_child(_vib_bild)
		var name_v := UiStil.label(UiText.t("vibration"), UiStil.GR_GROSS, UiStil.TINTE, UiStil.FETT)
		name_v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_v.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		zeile_v.add_child(name_v)
		_vib = Button.new()
		_vib.custom_minimum_size = Vector2(160.0, UiStil.TIPPZIEL)
		_vib.add_theme_font_override("font", UiStil.schrift(UiStil.FETT, UiStil.GR_MITTEL))
		_vib.add_theme_font_size_override("font_size", UiStil.GR_MITTEL)
		_vib.pressed.connect(func() -> void:
			Haptik.setze(not Haptik.an)
			aktualisiere())
		zeile_v.add_child(_vib)
		var laden := UiStil.nebenknopf(UiText.t("laden"), UiStil.TIPPZIEL + 8.0)
		laden.icon = UiStil.symbol("tasche")
		laden.add_theme_constant_override("icon_max_width", 44)
		laden.add_theme_font_size_override("font_size", UiStil.GR_MITTEL)
		laden.pressed.connect(func() -> void: laden_gedrueckt.emit())
		inhalt.add_child(laden)
		# Play-Vorgabe: Die Datenschutzerklaerung ist aus der App erreichbar.
		var url: String = datenschutz_url()
		if not url.is_empty():
			var recht := UiStil.nebenknopf(UiText.t("datenschutz"), UiStil.TIPPZIEL)
			recht.add_theme_font_size_override("font_size", UiStil.GR_TEXT)
			recht.pressed.connect(func() -> void: OS.shell_open(url))
			inhalt.add_child(recht)

	static func datenschutz_url() -> String:
		var f := FileAccess.open("res://data/services/rechtliches.json", FileAccess.READ)
		if f == null:
			return ""
		var d: Variant = JSON.parse_string(f.get_as_text())
		return String((d as Dictionary).get("datenschutz_url", "")) if d is Dictionary else ""

	func aktualisiere() -> void:
		titel.text = UiText.t("einstellungen_titel")
		_ton.text = UiText.t("an") if ton_an else UiText.t("aus")
		# An ist Akzent, Aus ist Papier -- ein Schalter, kein Kauf.
		UiStil.faerbe_knopf(_ton, UiStil.akzent() if ton_an else UiStil.PAPIER)
		_ton_bild.texture = UiStil.symbol("ton_an" if ton_an else "ton_aus")
		_vib.text = UiText.t("an") if Haptik.ist_an() else UiText.t("aus")
		UiStil.faerbe_knopf(_vib, UiStil.akzent() if Haptik.ist_an() else UiStil.PAPIER)


## --- Ein Nebenraum ---------------------------------------------------------------
##
## Zonen ohne Bereich und ohne Start (Bad, Pausenraum, Dachterrasse ...) hatten
## kein Panel: Der Tipp schloss nur das offene Menue, der Raum wirkte "nicht
## betretbar". Jetzt antwortet er mit Name und einem Satz.
class Nebenraummenue extends Sheet:
	var kern: GameCore
	var thema: ThemeData
	var zone_id: StringName = &""
	var _bild: TextureRect
	var _text: Label

	func _init() -> void:
		super()
		_bild = UiStil.symbolbild("haus", 56.0)
		_bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		kopf.add_child(_bild)
		kopf.move_child(_bild, 0)
		var karte_n := Sheet.innenkarte(float(UiStil.A4))
		inhalt.add_child(karte_n)
		_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		karte_n.add_child(_text)

	func zeige_zone(id: StringName) -> void:
		zone_id = id
		oeffnen()

	func aktualisiere() -> void:
		titel.text = WeltTexte.nebenraum(thema, zone_id, "name")
		_text.text = WeltTexte.nebenraum(thema, zone_id, "text")
