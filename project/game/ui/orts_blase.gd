## Ortsblase (K6 1c, §4.4 "Blase in der Welt"): Eine Nachricht ohne `szene` spricht
## als kurze Sprechblase ueber der Figur ihres Absenders -- dort, wo es passiert,
## statt als Banner oder Fenster. Steht die Figur nicht im Bild (oder hat der
## Absender keine, z. B. die Plattform), spricht sie am Startraum.
##
## Regeln (Werte in data/ui/hinweise.json):
##   - `blase_dauer_s` sichtbar, dann weg; ein Tipp auf die Blase oeffnet das Handy
##     an genau dieser Nachricht (Signal `getippt`);
##   - nie zwei gleichzeitig, hoechstens `blasen_max` wartend (aeltere fallen weg),
##     ungelesen nach `blase_verfall_s` freier Karte verworfen -- im Handy stehen sie ohnehin;
##   - nie waehrend eines Fensters (ModalSchlange) oder Panels (`darf`);
##   - nie ueber einer Plakette, einem Pfeil oder Kaufknopf: Die Blase weicht nach oben
##     aus, sonst unter den Anker; geht beides nicht, wartet sie;
##   - Text hoechstens `blase_zeichen_max` Zeichen (sonst gekuerzt mit "...").
## Texte bleiben in data/themes (die Hud reicht sie durch).
class_name OrtsBlase
extends Control

## Der Spieler hat auf die Blase getippt.
signal getippt(nachricht_id: String)

const ZIPFEL: float = 20.0
const AVATAR: float = 44.0
## Meter ueber dem Fusspunkt der Figur (Kopf), wie das "!" der Aufgaben.
const KOPF_HOEHE: float = 2.3

var marker: Kartenmarker
## Darf jetzt eine Blase stehen? (Hud: kein Panel, keine Tutorialkarte, keine Erklaerblase.)
var darf: Callable = Callable()
## Absender-ID -> Node3D der Figur (oder null). Main setzt es.
var figur_suche: Callable = Callable()
## Weltpunkt, an dem Absender ohne sichtbare Figur sprechen (Startraum). Main setzt es.
var startpunkt: Vector3 = Vector3.INF

var _wartend: Array[Dictionary] = []    ## {id, von, text, name, farbe, alter}
var _blase: Control
var _aktuell: Dictionary = {}
var _rest: float = 0.0
var _figur: Node3D


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE


# --- Reine Regeln (ohne Baum getestet) -----------------------------------------------

## Text auf hoechstens `max_zeichen` kuerzen, am Wortende, mit "...".
static func kuerze(text: String, max_zeichen: int) -> String:
	var t: String = text.strip_edges()
	if max_zeichen <= 0 or t.length() <= max_zeichen:
		return t
	var schnitt: String = t.substr(0, max_zeichen - 1)
	var leer: int = schnitt.rfind(" ")
	if leer > max_zeichen / 2:
		schnitt = schnitt.substr(0, leer)
	return schnitt.strip_edges() + "…"


## Eine Nachricht einreihen: hoechstens `max_wartend`, die aeltesten fallen weg.
static func einreihen(wartend: Array[Dictionary], eintrag: Dictionary, max_wartend: int) -> void:
	wartend.append(eintrag)
	while wartend.size() > maxi(max_wartend, 1):
		wartend.pop_front()


## Alter fortschreiben und Verfallene entfernen.
static func altern(wartend: Array[Dictionary], delta: float, verfall_s: float) -> void:
	for e in wartend:
		e["alter"] = float(e.get("alter", 0.0)) + delta
	wartend.assign(wartend.filter(func(e: Dictionary) -> bool: return float(e["alter"]) < verfall_s))


## Platz fuer eine Blase der Groesse `groesse` ueber `anker`: Sie weicht Hindernissen nach
## oben aus. Gibt die linke obere Ecke zurueck oder Vector2.INF (kein Platz -> warten).
static func platz(anker: Vector2, groesse: Vector2, hindernisse: Array[Rect2], oben_frei: float,
		unten_frei: float, breite: float, rand: float, abstand: float) -> Vector2:
	var x: float = clampf(anker.x - groesse.x * 0.5, rand, maxf(rand, breite - groesse.x - rand))
	var y: float = minf(anker.y - groesse.y - abstand, unten_frei - groesse.y)
	for _versuch in range(12):
		if y < oben_frei:
			break
		var r := Rect2(Vector2(x, y), groesse).grow(4.0)
		var hoechste: float = INF
		for h in hindernisse:
			if r.intersects(h):
				hoechste = minf(hoechste, h.position.y)
		if hoechste == INF:
			return Vector2(x, y)
		y = hoechste - groesse.y - abstand
	# Oben kein Platz (Ueberblick voller Plaketten): unter dem Anker versuchen, ebenfalls
	# ohne etwas zu verdecken. Geht auch das nicht, wartet die Blase.
	y = anker.y + abstand
	for _versuch in range(12):
		if y + groesse.y > unten_frei:
			return Vector2.INF
		var r2 := Rect2(Vector2(x, y), groesse).grow(4.0)
		var tiefste: float = -INF
		for h in hindernisse:
			if r2.intersects(h):
				tiefste = maxf(tiefste, h.end.y)
		if tiefste == -INF:
			return Vector2(x, y)
		y = tiefste + abstand
	return Vector2.INF


# --- Ablauf ----------------------------------------------------------------------------

## Neue Nachricht (id, Absender-ID, Text, Anzeigename, Absenderfarbe).
func melde(nachricht_id: String, von: String, text: String, name: String, farbe: Color) -> void:
	if text.strip_edges().is_empty():
		return
	einreihen(_wartend, {"id": nachricht_id, "von": von, "name": name, "farbe": farbe, "alter": 0.0,
		"text": kuerze(text, int(Kartenmarker.hinweis("blase_zeichen_max")))},
		int(Kartenmarker.hinweis("blasen_max")))


func ist_offen() -> bool:
	return _blase != null and is_instance_valid(_blase)


func wartend() -> int:
	return _wartend.size()


## Alles weg (Pruefbilder, Vorspulen, Weltwechsel).
func leeren() -> void:
	_wartend.clear()
	schliesse()


func schliesse() -> void:
	if ist_offen():
		_blase.queue_free()
	_blase = null
	_aktuell = {}
	_figur = null


func _process(delta: float) -> void:
	# Verfall zaehlt nur, solange die Blase stehen DUERFTE (freie Karte): Nachrichten, die beim
	# Kauf im Menue kommen, sprechen nach dem Schliessen -- nicht erst gar nicht.
	var blockiert: bool = _blockiert()
	if not blockiert:
		altern(_wartend, delta, Kartenmarker.hinweis("blase_verfall_s"))
	if ist_offen():
		_rest -= delta
		if _rest <= 0.0 or blockiert:
			schliesse()
			return
		var ort: Vector2 = _position()
		if ort == Vector2.INF:
			schliesse()
			return
		_blase.position = ort
		_setze_zipfel()
		return
	if _wartend.is_empty() or blockiert:
		return
	_zeige(_wartend[0])


## Warum gerade keine Blase kommt (Pruefwerkzeug, docs/PC_TEST.md `textebenen`).
func grund() -> String:
	var schlange: ModalSchlange = ModalSchlange.global()
	if schlange.ist_offen():
		return "fenster"
	if schlange.bereit_wartend():
		return "fenster_wartet"
	if marker == null or marker.kamera == null or not is_instance_valid(marker.kamera):
		return "keine_kamera"
	if darf.is_valid() and not bool(darf.call()):
		return "darf_nicht"
	var gross: PackedStringArray = PackedStringArray()
	for kind in marker.get_children():
		var c: Control = kind as Control
		if c != null and c.mouse_filter != Control.MOUSE_FILTER_IGNORE and c.is_visible_in_tree():
			gross.append("%s%s" % [c.name, c.get_global_rect()])
	return "wartend=%d offen=%s hindernisse=%s oben_frei=%.0f" % [_wartend.size(), ist_offen(), ",".join(gross), marker.oben_frei]


func _blockiert() -> bool:
	var schlange: ModalSchlange = ModalSchlange.global()
	if schlange.ist_offen() or schlange.bereit_wartend():
		return true
	if marker == null or marker.kamera == null or not is_instance_valid(marker.kamera):
		return true
	return darf.is_valid() and not bool(darf.call())


func _zeige(eintrag: Dictionary) -> void:
	_aktuell = eintrag
	_figur = figur_suche.call(String(eintrag["von"])) as Node3D if figur_suche.is_valid() else null
	_blase = _baue(String(eintrag["name"]), String(eintrag["text"]), eintrag["farbe"] as Color)
	add_child(_blase)
	var ort: Vector2 = _position()
	if ort == Vector2.INF:
		# Kein Platz ohne Plakette zu verdecken: spaeter noch einmal (verfaellt sonst).
		_blase.queue_free()
		_blase = null
		_aktuell = {}
		return
	_wartend.erase(eintrag)
	print("ortsblase zeigt: %s" % String(eintrag["id"]))
	_blase.position = ort
	_setze_zipfel()
	_rest = Kartenmarker.hinweis("blase_dauer_s")
	UiStil.aufploppen.call_deferred(_blase.get_node("Karte") as Control, 0.7)


## Anker: Kopf der Figur, sonst Startraum; im Bild gehalten.
func _anker() -> Vector2:
	var kamera: Camera3D = marker.kamera
	var flaeche: Vector2 = get_viewport_rect().size
	var punkte: Array[Vector3] = []
	if _figur != null and is_instance_valid(_figur) and _figur.is_visible_in_tree():
		punkte.append(_figur.global_position + Vector3.UP * KOPF_HOEHE)
	if startpunkt != Vector3.INF:
		punkte.append(startpunkt + Vector3.UP * KOPF_HOEHE)
	for welt in punkte:
		if kamera.is_position_behind(welt):
			continue
		var p: Vector2 = kamera.unproject_position(welt)
		if Rect2(Vector2.ZERO, flaeche).has_point(p):
			return p
	return Vector2(flaeche.x * 0.5, flaeche.y * 0.5)


func _position() -> Vector2:
	var karte: Control = _blase.get_node("Karte") as Control
	var groesse: Vector2 = karte.get_combined_minimum_size()
	karte.size = groesse
	_blase.size = groesse
	var flaeche: Vector2 = get_viewport_rect().size
	var hindernisse: Array[Rect2] = []
	for kind in marker.get_children():
		var c: Control = kind as Control
		if c != null and c.mouse_filter != Control.MOUSE_FILTER_IGNORE and c.is_visible_in_tree():
			hindernisse.append(c.get_global_rect())
	var unten: float = flaeche.y - Menueleiste.HOEHE
	var ort: Vector2 = platz(_anker(), groesse, hindernisse, marker.oben_frei, unten, flaeche.x,
		float(UiStil.A4), Kartenmarker.hinweis("blase_abstand_px") + ZIPFEL * 0.5)
	if ort != Vector2.INF:
		_blase.set_meta("anker", _anker())
	return ort


func _setze_zipfel() -> void:
	var zipfel: Control = _blase.get_node_or_null("Zipfel") as Control
	if zipfel == null:
		return
	var anker: Vector2 = _blase.get_meta("anker", _blase.position) as Vector2
	var unter_dem_anker: bool = _blase.position.y > anker.y
	zipfel.position = Vector2(clampf(anker.x - _blase.position.x, 28.0, _blase.size.x - 28.0) - ZIPFEL * 0.5,
		-ZIPFEL * 0.4 if unter_dem_anker else _blase.size.y - ZIPFEL * 0.6)


func _baue(name: String, text: String, farbe: Color) -> Control:
	var blase := Control.new()
	blase.name = "Ortsblase"
	blase.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var zipfel := Panel.new()
	zipfel.name = "Zipfel"
	zipfel.size = Vector2(ZIPFEL, ZIPFEL)
	zipfel.pivot_offset = Vector2(ZIPFEL, ZIPFEL) * 0.5
	zipfel.rotation_degrees = 45.0
	zipfel.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, 3, UiStil.KONTUR, 0.0, 0.0))
	zipfel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	blase.add_child(zipfel)
	var karte := PanelContainer.new()
	karte.name = "Karte"
	karte.mouse_filter = Control.MOUSE_FILTER_STOP
	karte.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A2), UiStil.SCHATTEN_Y, farbe))
	var nachricht_id: String = String(_aktuell.get("id", ""))
	karte.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			karte.accept_event()
			schliesse()
			getippt.emit(nachricht_id))
	var reihe := HBoxContainer.new()
	reihe.add_theme_constant_override("separation", UiStil.A2)
	reihe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	karte.add_child(reihe)
	var bild: Control = UiStil.avatar(name, farbe, AVATAR)
	bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reihe.add_child(bild)
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", -2)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	reihe.add_child(spalte)
	var kopf := UiStil.label(name, UiStil.GR_KLEIN - 2, UiStil.TINTE_2, UiStil.FETT)
	kopf.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spalte.add_child(kopf)
	var l := UiStil.label(text, UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var max_breite: float = Kartenmarker.hinweis("blase_breite_px") - AVATAR - float(UiStil.A2 * 3)
	var breite: float = UiStil.schrift(UiStil.FETT, UiStil.GR_TEXT).get_string_size(text,
		HORIZONTAL_ALIGNMENT_LEFT, -1, UiStil.GR_TEXT).x
	l.custom_minimum_size = Vector2(minf(breite + 4.0, max_breite), 0.0)
	spalte.add_child(l)
	blase.add_child(karte)
	return blase
