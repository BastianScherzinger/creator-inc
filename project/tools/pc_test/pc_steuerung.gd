## PC-Testumgebung: Befehle aus einer Datei ausfuehren, als waere ein Finger am Handy.
##
## Nur in Debug-/Editor-Builds aktiv, nie im Release. Geladen von game/main.gd
## ueber `PcSteuerung.starte(self)`, wenn ein Schalter dran ist:
##   --pc-test <befehlsdatei>     Skript: Datei abarbeiten, dann beenden
##   --pc-test-live <ordner>      interaktiv: <ordner>/befehle.txt alle 200 ms nachlesen,
##                                nach jedem Befehl eine Zeile nach <ordner>/log.txt
## Befehle und Beispiele: docs/PC_TEST.md. Alle Eingaben laufen als echte
## InputEventScreenTouch/ScreenDrag durch Input.parse_input_event, also
## durch dieselbe Kette wie am Handy (Godot leitet Finger 0 zusaetzlich als Maus
## weiter, so greifen auch die Knoepfe).
class_name PcSteuerung
extends Node

const POLL_MS: int = 200
## Abstand zwischen zwei Tipps eines Doppeltipps.
const DOPPEL_PAUSE_MS: int = 90
const TIPP_DAUER_MS: int = 60

var _main: Node
var _ordner: String = ""
var _live: bool = false
var _skript_zeilen: PackedStringArray = PackedStringArray()
var _gelesen: int = 0
var _naechster_poll: int = 0
var _laeuft: bool = false
var _start_ms: int = 0
var _zoom_im_griff: float = -1.0
## Messung (Befehle `messen` / `bericht`): Fenster und gleichzeitige Textebenen je Bild.
var _misst: bool = false
var _wisch_delta: Vector2 = Vector2.ZERO
var _wisch_serie: int = 0
var _abhol_versuche: int = 0
var _abholen_ruhe_bis: int = 0
var _spur: bool = false   ## `spur an`: `spiele` nennt die ersten Tippziele (Fehlersuche)
var _mess_start_spielzeit: float = 0.0
var _kaeufe: int = 0
var _momente: int = 0
var _bus_verbunden: bool = false
var _mess_start_ms: int = 0
var _fenster_log: PackedStringArray = PackedStringArray()
var _max_blasen: int = 0
var _kombis: Dictionary = {}      ## "rand+ort" -> Anzahl Bilder
var _proben: int = 0
var _verbunden: bool = false
var _zug: int = 0


## Einstieg fuer main.gd. Tut nichts im Release und ohne Schalter.
static func starte(wurzel: Node) -> void:
	if not OS.is_debug_build():
		return
	var argumente: PackedStringArray = OS.get_cmdline_user_args()
	var live: int = argumente.find("--pc-test-live")
	var skript: int = argumente.find("--pc-test")
	if live < 0 and skript < 0:
		return
	var steuerung := PcSteuerung.new()
	steuerung.name = "PcSteuerung"
	if live >= 0 and live + 1 < argumente.size():
		steuerung._live = true
		steuerung._ordner = argumente[live + 1]
	elif skript >= 0 and skript + 1 < argumente.size():
		var datei: String = argumente[skript + 1]
		steuerung._ordner = datei.get_base_dir()
		steuerung._skript_zeilen = FileAccess.get_file_as_string(datei).split("\n")
	else:
		push_warning("PcSteuerung: Schalter ohne Pfad")
		return
	steuerung._main = wurzel
	wurzel.add_child(steuerung)


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_start_ms = Time.get_ticks_msec()
	DirAccess.make_dir_recursive_absolute(_ordner)
	var log_pfad: String = _ordner.path_join("log.txt")
	if not FileAccess.file_exists(log_pfad) or not _live:
		_schreibe(log_pfad, "", false)
	_schreibe(log_pfad, "[t=0.0] bereit (%s)" % ("live" if _live else "skript"), true)
	if not _live:
		_arbeite_skript()


func _process(_delta: float) -> void:
	if _misst:
		_probe_textebenen()
	if not _live or _laeuft:
		return
	var jetzt: int = Time.get_ticks_msec()
	if jetzt < _naechster_poll:
		return
	_naechster_poll = jetzt + POLL_MS
	_arbeite_neue_zeilen()


func _arbeite_skript() -> void:
	_laeuft = true
	for i in _skript_zeilen.size():
		await _bearbeite_zeile(i + 1, _skript_zeilen[i])
	_log(0, "skript fertig")
	get_tree().quit()


func _arbeite_neue_zeilen() -> void:
	var pfad: String = _ordner.path_join("befehle.txt")
	if not FileAccess.file_exists(pfad):
		return
	var text: String = FileAccess.get_file_as_string(pfad)
	# Nur vollstaendige Zeilen (mit Zeilenende) -- eine halb geschriebene wartet.
	var letzte: int = text.rfind("\n")
	if letzte < 0:
		return
	var zeilen: PackedStringArray = text.substr(0, letzte).split("\n")
	if zeilen.size() <= _gelesen:
		return
	_laeuft = true
	while _gelesen < zeilen.size():
		var nr: int = _gelesen + 1
		_gelesen += 1
		await _bearbeite_zeile(nr, zeilen[nr - 1])
	_laeuft = false


# --- Befehle ------------------------------------------------------------------

func _bearbeite_zeile(nr: int, roh: String) -> void:
	var zeile: String = roh.strip_edges()
	if zeile.is_empty() or zeile.begins_with("#"):
		return
	var teile: PackedStringArray = zeile.split(" ", false)
	var antwort: String = await _fuehre_aus(teile)
	_log(nr, "%s -> %s" % [zeile, antwort])


func _fuehre_aus(t: PackedStringArray) -> String:
	var befehl: String = t[0].to_lower()
	match befehl:
		"tipp":
			if t.size() < 3:
				return "FEHLER: tipp x y"
			var p: Vector2 = _punkt(t[1], t[2])
			var traf: String = _was(p)
			await _tippe(p)
			return "traf: " + traf
		"doppeltipp":
			if t.size() < 3:
				return "FEHLER: doppeltipp x y"
			var p: Vector2 = _punkt(t[1], t[2])
			var traf: String = _was(p)
			await _tippe(p)
			await _warte_ms(DOPPEL_PAUSE_MS)
			await _tippe(p)
			return "traf: " + traf
		"halten":
			if t.size() < 4:
				return "FEHLER: halten x y ms"
			var p: Vector2 = _punkt(t[1], t[2])
			var traf: String = _was(p)
			await _tippe(p, int(t[3]))
			return "traf: " + traf
		"wisch":
			if t.size() < 6:
				return "FEHLER: wisch x1 y1 x2 y2 ms"
			var von: Vector2 = _punkt(t[1], t[2])
			var nach: Vector2 = _punkt(t[3], t[4])
			var traf: String = _was(von)
			await _wische(von, nach, int(t[5]))
			return "von: " + traf
		"pinch":
			if t.size() < 5:
				return "FEHLER: pinch cx cy faktor ms"
			var mitte: Vector2 = _punkt(t[1], t[2])
			var zoom_vorher: float = _kamera_zoom()
			await _pinche(mitte, float(t[3]), int(t[4]))
			return "Kamera-Zoom %.2f -> %.2f (beim Loslassen) -> %.2f (kurz danach, Stufe %s)" % [
				zoom_vorher, _zoom_im_griff, _kamera_zoom(), _stufe()]
		"warte":
			await _warte_ms(int(float(t[1]) * 1000.0) if t.size() > 1 else 1000)
			return "ok"
		"zeitraffer":
			Engine.time_scale = clampf(float(t[1]) if t.size() > 1 else 1.0, 0.1, 50.0)
			return "time_scale=%.1f" % Engine.time_scale
		"bild":
			return await _bild(t[1] if t.size() > 1 else "bild")
		"was":
			if t.size() < 3:
				return "FEHLER: was x y"
			return _was(_punkt(t[1], t[2]))
		"zustand":
			return _zustand()
		"spur":
			_spur = t.size() < 2 or t[1] != "aus"
			return "spur=%s" % str(_spur)
		"empfehlung":
			var kern_e: GameCore = _main.get(&"kern") as GameCore
			var hud_e: Object = _main.get(&"_hud") as Object
			return "empfehlung=%s kauf_punkt=%s" % [str(kern_e.empfehlung()) if kern_e != null else "-",
				str(hud_e.call(&"kauf_punkt")) if hud_e != null else "-"]
		"messen":
			return _messen_start()
		"bericht":
			return _bericht()
		"spiele":
			return await _spiele(float(t[1]) if t.size() > 1 else 30.0)
		"textebenen":
			var hud_t: Object = _main.get(&"_hud") as Object
			var ort_t: Variant = hud_t.get(&"ortsblase") if hud_t != null else null
			var grund: String = String((ort_t as Object).call(&"grund")) if ort_t is Object and (ort_t as Object).has_method(&"grund") else ""
			return "%s | Ortsblase: %s" % [",".join(_textebenen()), grund]
		"bild_bei":
			# bild_bei <ebene> <name> [max_s]: spielen, bis die Textebene steht, dann Bild.
			if t.size() < 3:
				return "FEHLER: bild_bei ebene name [max_s]"
			return await _bild_bei(t[1], t[2], float(t[3]) if t.size() > 3 else 30.0)
		"geld":
			return _geld(float(t[1]) if t.size() > 1 else 0.0)
		"welt":
			return await _welt(int(t[1]) if t.size() > 1 else 0)
		"ende":
			_log(0, "ende")
			get_tree().quit()
			return "ende"
	return "FEHLER: unbekannter Befehl '%s'" % befehl


# --- Eingabe ------------------------------------------------------------------

func _fenster() -> Vector2:
	return Vector2(get_tree().root.size)


## "270" = Bildschirmpixel, "50%" = Prozent der Fensterbreite/-hoehe.
func _punkt(xs: String, ys: String) -> Vector2:
	var f: Vector2 = _fenster()
	return Vector2(_achse(xs, f.x), _achse(ys, f.y))


func _achse(wort: String, laenge: float) -> float:
	if wort.ends_with("%"):
		return float(wort.trim_suffix("%")) / 100.0 * laenge
	return float(wort)


func _warte_ms(ms: int) -> void:
	# Echte Zeit, unabhaengig von Engine.time_scale.
	await get_tree().create_timer(maxf(ms, 1) / 1000.0, true, false, true).timeout


func _beruehrung(index: int, pos: Vector2, gedrueckt: bool) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = pos
	e.pressed = gedrueckt
	Input.parse_input_event(e)


func _ziehen(index: int, pos: Vector2, relativ: Vector2) -> void:
	var e := InputEventScreenDrag.new()
	e.index = index
	e.position = pos
	e.relative = relativ
	Input.parse_input_event(e)


func _tippe(pos: Vector2, dauer_ms: int = TIPP_DAUER_MS) -> void:
	_beruehrung(0, pos, true)
	await _warte_ms(dauer_ms)
	_beruehrung(0, pos, false)
	await _warte_ms(30)


func _wische(von: Vector2, nach: Vector2, dauer_ms: int) -> void:
	_beruehrung(0, von, true)
	await _warte_ms(30)
	var start: int = Time.get_ticks_msec()
	var zuletzt: Vector2 = von
	var dauer: float = maxf(dauer_ms, 50)
	while true:
		await get_tree().process_frame
		var anteil: float = clampf(float(Time.get_ticks_msec() - start) / dauer, 0.0, 1.0)
		var pos: Vector2 = von.lerp(nach, anteil)
		_ziehen(0, pos, pos - zuletzt)
		zuletzt = pos
		if anteil >= 1.0:
			break
	await _warte_ms(30)
	_beruehrung(0, nach, false)
	await _warte_ms(30)


## Zwei Finger waagerecht um die Mitte; Faktor > 1 = auseinander (hineinzoomen).
func _pinche(mitte: Vector2, faktor: float, dauer_ms: int) -> void:
	var f: float = clampf(faktor, 0.1, 10.0)
	var weite: float = minf(_fenster().x * 0.9, 560.0)
	var abstand_start: float = 110.0 if f >= 1.0 else clampf(110.0 / f, 110.0, weite)
	var abstand_ende: float = clampf(abstand_start * f, 30.0, weite)
	var a0: Vector2 = mitte + Vector2(-abstand_start * 0.5, 0.0)
	var b0: Vector2 = mitte + Vector2(abstand_start * 0.5, 0.0)
	_beruehrung(0, a0, true)
	_beruehrung(1, b0, true)
	await _warte_ms(40)
	var start: int = Time.get_ticks_msec()
	var a_alt: Vector2 = a0
	var b_alt: Vector2 = b0
	var dauer: float = maxf(dauer_ms, 50)
	while true:
		await get_tree().process_frame
		var anteil: float = clampf(float(Time.get_ticks_msec() - start) / dauer, 0.0, 1.0)
		var abstand: float = lerpf(abstand_start, abstand_ende, anteil)
		var a: Vector2 = mitte + Vector2(-abstand * 0.5, 0.0)
		var b: Vector2 = mitte + Vector2(abstand * 0.5, 0.0)
		_ziehen(0, a, a - a_alt)
		_ziehen(1, b, b - b_alt)
		a_alt = a
		b_alt = b
		if anteil >= 1.0:
			break
	await _warte_ms(40)
	_zoom_im_griff = _kamera_zoom()
	_beruehrung(1, b_alt, false)
	_beruehrung(0, a_alt, false)
	# Pinch rastet nicht ein (K6 §4.1); kurz warten, falls die Kamera noch nachfedert.
	await _warte_ms(700)


# --- Abfragen -----------------------------------------------------------------

func _kamera() -> Camera3D:
	return _main.get(&"kamera") as Camera3D


func _stufe() -> String:
	var k: Camera3D = _kamera()
	return String(k.call(&"stufe")) if k != null and k.has_method(&"stufe") else "?"


func _kamera_zoom() -> float:
	var k: Camera3D = _kamera()
	if k != null and k.has_method(&"zoom"):
		return float(k.call(&"zoom"))
	return -1.0


## Fensterpixel -> Viewport-Koordinaten (Streckung canvas_items).
func _in_viewport(p: Vector2) -> Vector2:
	return get_tree().root.get_final_transform().affine_inverse() * p


## Was liegt unter dem Punkt: Controls (oberstes, das Eingaben annimmt) und 3D.
func _was(fenster_punkt: Vector2) -> String:
	var p: Vector2 = _in_viewport(fenster_punkt)
	var treffer: Array[Dictionary] = []
	var zaehler: Array[int] = [0]
	_sammle(get_tree().root, p, 0, zaehler, treffer)
	treffer.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if a["ebene"] != b["ebene"]:
			return int(a["ebene"]) > int(b["ebene"])
		return int(a["nr"]) > int(b["nr"]))
	var teile: PackedStringArray = PackedStringArray()
	var angenommen: bool = false
	for h in treffer:
		var c: Control = h["control"] as Control
		var nimmt: bool = c.mouse_filter != Control.MOUSE_FILTER_IGNORE
		if nimmt and not angenommen:
			teile.append(_beschreibe(c, true))
			angenommen = true
			break
		elif not nimmt and teile.size() < 2 and _kurz(c).contains("\""):
			teile.append("(ignoriert) " + _kurz(c))
	if not angenommen:
		teile.append("kein Control nimmt Eingaben an; Welt: " + _welt_treffer(p))
	return " | ".join(teile)


func _sammle(knoten: Node, p: Vector2, ebene: int, zaehler: Array[int], aus: Array[Dictionary]) -> void:
	var meine_ebene: int = ebene
	if knoten is CanvasLayer:
		meine_ebene = (knoten as CanvasLayer).layer
		if not (knoten as CanvasLayer).visible:
			return
	for kind in knoten.get_children():
		zaehler[0] += 1
		if kind is Control:
			var c: Control = kind as Control
			if c.is_visible_in_tree() and c.get_global_rect().has_point(p):
				aus.append({"control": c, "ebene": meine_ebene, "nr": zaehler[0]})
		_sammle(kind, p, meine_ebene, zaehler, aus)


func _sammle_texte(knoten: Node, aus: PackedStringArray) -> void:
	for kind in knoten.get_children():
		if kind is Label and not (kind as Label).text.is_empty() and aus.size() < 3:
			aus.append((kind as Label).text.replace("
", " "))
		_sammle_texte(kind, aus)


func _kurz(c: Control) -> String:
	var wert: Variant = c.get(&"text")
	var text: String = " \"%s\"" % (wert as String).replace("
", " ") if wert is String and not (wert as String).is_empty() else ""
	return "%s%s" % [c.get_class(), text]


func _beschreibe(c: Control, mit_filter: bool) -> String:
	var pfad: String = str(c.get_path()).trim_prefix("/root/")
	var text: String = ""
	var wert: Variant = c.get(&"text")
	if wert is String and not (wert as String).is_empty():
		text = " \"%s\"" % (wert as String).replace("\n", " ")
	if text.is_empty():
		var inhalt: PackedStringArray = PackedStringArray()
		_sammle_texte(c, inhalt)
		if not inhalt.is_empty():
			text = " enthaelt \"%s\"" % " / ".join(inhalt)
	var s: String = "%s%s [%s]" % [pfad, text, c.get_class()]
	if mit_filter:
		var filter: String = ["STOP", "PASS", "IGNORE"][c.mouse_filter]
		var knopf: String = ""
		if c is BaseButton and (c as BaseButton).disabled:
			knopf = ", deaktiviert"
		s += " (nimmt Eingaben an, filter=%s%s)" % [filter, knopf]
	return s


func _welt_treffer(p: Vector2) -> String:
	var k: Camera3D = _kamera()
	var karte: Variant = _main.get(&"_treffer")
	if k == null or karte == null or not (karte is Object) or not (karte as Object).has_method(&"finde"):
		return "keine Karte"
	var t: Dictionary = (karte as Object).call(&"finde", k.project_ray_origin(p), k.project_ray_normal(p)) as Dictionary
	var zone: Dictionary = t.get("zone", {}) as Dictionary
	var zonenname: String = str(zone.get("id", zone.get("name", ""))) if not zone.is_empty() else ""
	var s: String = "3D-Marker art=%s" % str(t.get("art", "?"))
	if str(t.get("station", "")) != "":
		s += " station=%s" % str(t["station"])
	if zonenname != "":
		s += " zone=%s" % zonenname
	return s


func _zustand() -> String:
	var kern: GameCore = _main.get(&"kern") as GameCore
	if kern == null:
		return "kein Kern"
	var gekauft: PackedStringArray = PackedStringArray()
	for id in kern.bereiche.ids():
		if kern.bereiche.ist_gekauft(id):
			gekauft.append(String(id))
	var schlange: ModalSchlange = ModalSchlange.global()
	var fenster: String = String(schlange.offene_art()) if schlange.ist_offen() else "keins"
	var wartend: PackedStringArray = PackedStringArray()
	for w in schlange.wartend():
		wartend.append(String(w))
	var panel: String = "keins"
	var hud: Object = _main.get(&"_hud") as Object
	if hud != null:
		var sheets: Variant = hud.get(&"_sheets")
		if sheets is Array:
			for sh in sheets as Array:
				if sh is Sheet and (sh as Sheet).ist_offen():
					panel = "%s (%s)" % [(sh as Sheet).get_class() if (sh as Sheet).get_script() == null else str((sh as Sheet).get_script().get_global_name()), (sh as Sheet).titel.text if (sh as Sheet).titel != null else ""]
					break
	var k: Camera3D = _kamera()
	var stufe: String = ""
	if k != null and k.has_method(&"stufe"):
		stufe = String(k.call(&"stufe"))
	return "Geld=%s Einkommen/s=%.2f Welt=%d (%s) Rang=%d Raeume=%d/%d [%s] Fenster=%s Wartend=[%s] Panel=%s Zoom=%.2f Stufe=%s time_scale=%.1f" % [
		_zahl(kern.kapital), kern.einkommen_pro_sekunde(), kern.welt_index + 1, kern.welt_id(),
		kern.rang(), kern.bereiche.anzahl_gekauft(), kern.bereiche.anzahl(), ",".join(gekauft),
		fenster, ",".join(wartend), panel, _kamera_zoom(), stufe, Engine.time_scale]


## GDScript kennt kein "%e" -- die Exponentenschreibweise wird selbst gebaut ("1.234e+15").
static func _zahl(wert: float) -> String:
	if absf(wert) < 1.0e6:
		return "%.1f" % wert
	var exponent: int = int(floorf(log(absf(wert)) / log(10.0)))
	var mantisse: float = wert / pow(10.0, exponent)
	if absf(mantisse) >= 9.9995:
		mantisse /= 10.0
		exponent += 1
	return "%.3fe+%d" % [mantisse, exponent]


# --- Eingriffe (nur Testmodus) ------------------------------------------------

func _geld(menge: float) -> String:
	var kern: GameCore = _main.get(&"kern") as GameCore
	if kern == null:
		return "kein Kern"
	kern.kapital += menge
	kern.bus.money_changed.emit(kern.kapital, 0.0)
	return "Geld=%s" % _zahl(kern.kapital)


## Nur vorwaerts (Kern kennt keinen Weg zurueck); fuer eine fruehere Welt mit `--welt N` starten.
func _welt(ziel: int) -> String:
	var kern: GameCore = _main.get(&"kern") as GameCore
	if kern == null:
		return "kein Kern"
	if ziel < 1 or ziel > kern.welten.anzahl():
		return "FEHLER: Welt 1..%d" % kern.welten.anzahl()
	if ziel - 1 < kern.welt_index:
		return "FEHLER: nur vorwaerts, Neustart mit --welt %d" % ziel
	while kern.welt_index < ziel - 1:
		if not kern.wechsle_welt():
			break
	_main.call(&"_baue_neu")
	await _warte_ms(500)
	return "Welt=%d (%s)" % [kern.welt_index + 1, kern.welt_id()]


func _bild(name: String) -> String:
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var bild: Image = get_viewport().get_texture().get_image()
	var sauber: String = name.validate_filename()
	var voll: String = ProjectSettings.globalize_path(_ordner) if _ordner.begins_with("res://") or _ordner.begins_with("user://") else _ordner
	var pfad: String = voll.path_join(sauber + ".png")
	bild.save_png(pfad)
	var klein: Image = bild.duplicate() as Image
	klein.resize(maxi(1, bild.get_width() / 2), maxi(1, bild.get_height() / 2), Image.INTERPOLATE_LANCZOS)
	klein.save_png(voll.path_join(sauber + "_50.png"))
	return pfad


# --- Protokoll ----------------------------------------------------------------

func _log(nr: int, text: String) -> void:
	var t: float = float(Time.get_ticks_msec() - _start_ms) / 1000.0
	var marke: String = "#%d " % nr if nr > 0 else ""
	_schreibe(_ordner.path_join("log.txt"), "[t=%.1f] %s%s" % [t, marke, text], true)


func _schreibe(pfad: String, zeile: String, anhaengen: bool) -> void:
	var datei: FileAccess = FileAccess.open(pfad, FileAccess.READ_WRITE if anhaengen and FileAccess.file_exists(pfad) else FileAccess.WRITE)
	if datei == null:
		return
	if anhaengen:
		datei.seek_end()
		datei.store_string(zeile + "\n")
	datei.close()


# --- Messung und Selbstspiel (K6 1c) --------------------------------------------

## Was gerade an Text ueber der Karte steht (ohne Zielleiste): "fenster:<art>", "rand"
## (Saft-Meldung), "erklaer" (Symbol-Blase), "ort" (Ortsblase), "tutorial" (Tutorialkarte).
func _textebenen() -> PackedStringArray:
	var aus: PackedStringArray = PackedStringArray()
	var schlange: ModalSchlange = ModalSchlange.global()
	if schlange.ist_offen() and not ModalSchlange.LEICHT.has(schlange.offene_art()):
		aus.append("fenster:" + String(schlange.offene_art()))
	var hud: Object = _main.get(&"_hud") as Object
	if hud == null:
		return aus
	var saft: Object = hud.get(&"saft") as Object
	if saft != null:
		var feld: Variant = saft.get(&"_aktuelles_feld")
		if feld is Control and is_instance_valid(feld) and (feld as Control).is_visible_in_tree():
			aus.append("rand")
	var symbol: Object = hud.get(&"symbol_hinweise") as Object
	if symbol != null and symbol.has_method(&"ist_offen") and bool(symbol.call(&"ist_offen")):
		aus.append("erklaer")
	var ort: Variant = hud.get(&"ortsblase")
	if ort is Object and ort != null and (ort as Object).has_method(&"ist_offen") and bool((ort as Object).call(&"ist_offen")):
		aus.append("ort")
	var tut: Variant = _main.get(&"_tutorial_view")
	if tut is Control and is_instance_valid(tut) and (tut as Control).is_visible_in_tree():
		aus.append("tutorial")
	return aus


func _messen_start() -> String:
	_misst = true
	_mess_start_ms = Time.get_ticks_msec()
	var kern1: GameCore = _main.get(&"kern") as GameCore
	_mess_start_spielzeit = kern1.spielzeit if kern1 != null else 0.0
	_fenster_log.clear()
	_max_blasen = 0
	_kombis.clear()
	_proben = 0
	_kaeufe = 0
	_momente = 0
	var kern0: GameCore = _main.get(&"kern") as GameCore
	if kern0 != null and not _bus_verbunden:
		_bus_verbunden = true
		kern0.bus.station_upgraded.connect(func(_i: StringName, _n: int) -> void:
			if _misst: _kaeufe += 1)
		kern0.bus.equipment_upgraded.connect(func(_i: StringName, _p: StringName, _n: int) -> void:
			if _misst: _kaeufe += 1)
		kern0.bus.area_bought.connect(func(_b: StringName) -> void:
			if _misst: _kaeufe += 1)
		kern0.bus.moment_appeared.connect(func(_i: StringName, _d: float) -> void:
			if _misst: _momente += 1)
	var schlange: ModalSchlange = ModalSchlange.global()
	if not _verbunden:
		_verbunden = true
		schlange.gezeigt.connect(func(art: StringName) -> void:
			if _misst and not ModalSchlange.LEICHT.has(art):
				var kern: GameCore = _main.get(&"kern") as GameCore
				_fenster_log.append("%s@%.0fs" % [String(art), kern.spielzeit if kern != null else 0.0]))
	return "Messung laeuft"


func _probe_textebenen() -> void:
	var ebenen: PackedStringArray = _textebenen()
	_proben += 1
	var blasen: int = 0
	for e in ebenen:
		if not e.begins_with("fenster:"):
			blasen += 1
	_max_blasen = maxi(_max_blasen, blasen)
	if ebenen.size() > 1:
		var schluessel: String = "+".join(ebenen)
		_kombis[schluessel] = int(_kombis.get(schluessel, 0)) + 1


func _bericht() -> String:
	var kombis: PackedStringArray = PackedStringArray()
	for k in _kombis.keys():
		kombis.append("%s:%d" % [k, int(_kombis[k])])
	var kern: GameCore = _main.get(&"kern") as GameCore
	var spielzeit: float = kern.spielzeit - _mess_start_spielzeit if kern != null else 0.0
	var minuten: float = maxf(spielzeit / 60.0, 0.01)
	return ("Fenster=%d [%s] MaxTextebenen=%d Mehrfach={%s} Bilder=%d Dauer=%.0fs Spielzeit=%.1fmin "
		+ "Kaeufe=%d (%.1f/min) Momente=%d (%.1f/min)") % [
		_fenster_log.size(), ", ".join(_fenster_log), _max_blasen, ", ".join(kombis), _proben,
		float(Time.get_ticks_msec() - _mess_start_ms) / 1000.0, spielzeit / 60.0,
		_kaeufe, float(_kaeufe) / minuten, _momente, float(_momente) / minuten]


## Spielt `sekunden` echte Sekunden lang wie ein ungeduldiger Spieler: Fenster weitertippen,
## im offenen Menue den Kaufknopf, sonst gruene Plakette, fertiges Ziel oder die Station des
## besten Kaufs. Jeder Tipp ist ein echter Touch (wie `tipp`).
func _spiele(sekunden: float) -> String:
	var ende: int = Time.get_ticks_msec() + int(sekunden * 1000.0)
	var tipps: int = 0
	var wische: int = 0
	var spur: Array[String] = []
	while Time.get_ticks_msec() < ende:
		var ziel: Vector2 = _naechster_spielzug()
		if ziel.x >= 0.0:
			if _spur and spur.size() < 8:
				spur.append("%s @%d,%d" % [_was(get_tree().root.get_final_transform() * ziel).right(110), int(ziel.x), int(ziel.y)])
			await _tippe(get_tree().root.get_final_transform() * ziel)
			tipps += 1
			_wisch_serie = 0
		elif _wisch_delta != Vector2.ZERO:
			# Fensterpixel wie beim Befehl `wisch`; die Verschiebung ist in Bildkoordinaten gerechnet.
			var von: Vector2 = _fenster() * Vector2(0.5, 0.533)
			var tf: Transform2D = get_tree().root.get_final_transform()
			_wisch_serie += 1
			if _wisch_serie > 2:
				# Wischen holt den Kauf nicht ins Bild (Rand der Karte): herauszoomen wie ein Spieler.
				_wisch_serie = 0
				await _pinche(von, 0.55, 600)
			else:
				await _wische(von, von + tf.basis_xform(_wisch_delta), 400)
			_wisch_delta = Vector2.ZERO
			wische += 1
		await _warte_ms(350)
	# Zum Schluss die Karte frei lassen (offene Menues zu), wie ein Spieler, der zuschaut.
	var hud: Object = _main.get(&"_hud") as Object
	if hud != null:
		hud.call(&"schliesse_alle")
	return "%d Tipps, %d Wische%s" % [tipps, wische, (" | " + " ; ".join(spur)) if _spur else ""]


## Ziel in Viewport-Koordinaten oder (-1,-1).
func _naechster_spielzug() -> Vector2:
	var hud: Object = _main.get(&"_hud") as Object
	if hud == null:
		return Vector2(-1.0, -1.0)
	var schlange: ModalSchlange = ModalSchlange.global()
	if schlange.ist_offen() and not ModalSchlange.LEICHT.has(schlange.offene_art()):
		var fz: Vector2 = _fenster_zug()
		# Eine Szene wartet, bis der Spieler das offene Menue schliesst (HUD._oeffne_szene) --
		# also schliessen wie ein Spieler; sonst stand der Autospieler eine Minute still.
		if fz.x < 0.0 and bool(hud.call(&"sheet_offen")):
			hud.call(&"schliesse_alle")
		return fz
	if bool(hud.call(&"sheet_offen")):
		_zug += 1
		var stm: Variant = hud.get(&"stationsmenue")
		if _zug % 2 == 0 and stm is Sheet and (stm as Sheet).ist_offen():
			var plaetze: Variant = (stm as Sheet).get(&"_platz_knoepfe")
			if plaetze is Dictionary:
				for karte in (plaetze as Dictionary).values():
					var knopf: Button = _erster_knopf(karte as Node)
					if knopf != null:
						return knopf.get_global_rect().get_center()
		# Auftragsbrett: den "Abholen"-Knopf druecken (der Knopf "Los geht's" bleibt unberuehrt).
		var brett: Variant = hud.get(&"auftragsbrett")
		if brett is Sheet and (brett as Sheet).ist_offen():
			var abholen: Button = _knopf_mit_text(brett as Node, UiText.t("brett_abholen")) if _abholen_frei() else null
			if abholen != null:
				_abhol_versuche += 1
				return abholen.get_global_rect().get_center()
		for name in [&"schnellkauf", &"bereichsmenue", &"stationsmenue"]:
			var sh: Variant = hud.get(name)
			if sh is Sheet and (sh as Sheet).ist_offen():
				for feld in [&"_knopf", &"_ausbau"]:
					var k: Variant = (sh as Sheet).get(feld)
					if k is Button and (k as Button).is_visible_in_tree() and not (k as Button).disabled:
						return (k as Button).get_global_rect().get_center()
		hud.call(&"schliesse_alle")
		return Vector2(-1.0, -1.0)
	# Tutorial: zeigt der Ring auf eine Station der Karte (Schritt "Kette", "Engpass"),
	# genau dort tippen -- sonst haengt der Autospieler an diesem Schritt fest.
	var tut_ziel: Vector2 = _tutorial_ring_punkt()
	if tut_ziel.x >= 0.0:
		return tut_ziel
	# Harte Obergrenze (Welt 2: Speicher): Ist der Umbau bezahlbar, zuerst ihn -- sonst kauft der
	# Autospieler Stufen, die nichts bringen, und die Messung zeigt eine stehende Welt.
	var umbau: Variant = hud.get(&"_umbau_knopf")
	if umbau is Button and (umbau as Button).is_visible_in_tree() and not (umbau as Button).disabled:
		return (umbau as Button).get_global_rect().get_center()
	var fertige: Vector2 = _fertige_auftragskarte(hud) if _abholen_frei() else Vector2(-1.0, -1.0)
	if fertige.x >= 0.0:
		return fertige
	# Waehrend der Abhol-Pause auch die Zielleiste nicht antippen: Sie oeffnet nur das Brett, das der
	# naechste Zug wieder schliesst -- in Welt 3 lief so eine ganze Minute ohne Kauf.
	if _abholen_frei() and bool(hud.call(&"ziel_abholbar")):
		var karte: Variant = hud.get(&"_zielkarte")
		if karte is Control:
			return (karte as Control).get_global_rect().get_center()
	var marker: Variant = hud.get(&"marker")
	if marker is Control:
		var schilder: Variant = (marker as Control).get(&"_schilder")
		if schilder is Dictionary:
			for id in (schilder as Dictionary).keys():
				var f: Variant = (schilder as Dictionary)[id]
				if f is Control and is_instance_valid(f) and (f as Control).is_visible_in_tree() 						and String((f as Control).get_meta("zustand", "")) == "kaufbar":
					return (f as Control).get_global_rect().get_center()
	if marker is Control:
		var tab: Variant = (marker as Control).get(&"_tab")
		if tab is Control and (tab as Control).is_visible_in_tree() and _zug % 3 == 0:
			_zug += 1
			return (tab as Control).get_global_rect().get_center()
	_zug += 1
	var p: Variant = hud.call(&"kauf_punkt")
	if p is Vector2:
		var pv: Vector2 = p as Vector2
		var sicht: Vector2 = get_viewport().get_visible_rect().size
		if pv.x >= 40.0 and pv.x <= sicht.x - 40.0 and pv.y >= 200.0 and pv.y <= sicht.y - 300.0:
			return pv
		# Der beste Kauf liegt ausserhalb des Bildes: Karte per Wisch dorthin ziehen
		# (sonst steht der Autospieler mit Geld in der Tasche still).
		var mitte: Vector2 = Vector2(sicht.x * 0.5, sicht.y * 0.42)
		_wisch_delta = (mitte - pv).limit_length(240.0)
	return Vector2(-1.0, -1.0)


## Bildschirmpunkt des Tutorial-Rings, wenn er auf einen Weltpunkt (Station) zeigt, sonst (-1,-1).
## Gleiche Rechnung wie TutorialView._draw (unproject_position, x im Bild gehalten).
func _tutorial_ring_punkt() -> Vector2:
	var tv: Variant = _main.get(&"_tutorial_view")
	if not (tv is Control) or not (tv as Control).is_visible_in_tree():
		return Vector2(-1.0, -1.0)
	if not bool((tv as Object).get(&"_hat_ziel_welt")):
		return Vector2(-1.0, -1.0)
	# K7: Ziel ausserhalb des Bildes -- der Randpfeil steht; antippen wie ein Spieler (Kamera schiebt hin).
	var pfeil: Vector2 = (tv as Object).call(&"rand_pfeil_punkt") as Vector2
	if pfeil.x >= 0.0:
		return pfeil
	var kam: Variant = (tv as Object).get(&"_kamera")
	var welt: Variant = (tv as Object).get(&"_ziel_welt")
	if not (kam is Camera3D) or not is_instance_valid(kam) or not (welt is Vector3):
		return Vector2(-1.0, -1.0)
	if (kam as Camera3D).is_position_behind(welt as Vector3):
		return Vector2(-1.0, -1.0)
	var p: Vector2 = (kam as Camera3D).unproject_position(welt as Vector3)
	var sicht: Vector2 = (tv as Control).get_viewport_rect().size
	# Ring knapp am Rand (halb im Bild): nicht antippen, der Autospieler spielt normal weiter.
	if p.x < 40.0 or p.x > sicht.x - 100.0 or p.y < 40.0 or p.y > sicht.y - 40.0:
		return Vector2(-1.0, -1.0)
	return p


## Mitte der Auftragskarte, die "Holen" zeigt (Meta `zustand[0]` = fertig), sonst (-1,-1).
## Die Mitte der ganzen Zielleiste traf frueher eine andere Karte oder die Kopfzeile.
func _fertige_auftragskarte(hud: Object) -> Vector2:
	var karten: Variant = hud.get(&"_auftrags_karten")
	if not (karten is Array):
		return Vector2(-1.0, -1.0)
	for teile in karten as Array:
		var k: Variant = (teile as Dictionary).get("karte") if teile is Dictionary else null
		if k is Control and is_instance_valid(k) and (k as Control).is_visible_in_tree():
			var zustand: Variant = (k as Control).get_meta("zustand", [])
			if zustand is Array and (zustand as Array).size() > 0 and bool((zustand as Array)[0]):
				return (k as Control).get_global_rect().get_center()
	return Vector2(-1.0, -1.0)


func _fenster_zug() -> Vector2:
	var offen: Control = _finde_fenster(get_tree().root)
	if offen == null:
		return Vector2(-1.0, -1.0)
	if offen is SzeneView:
		var zeile: Variant = offen.get(&"_antwort_zeile")
		if zeile is Control and (zeile as Control).get_child_count() > 0 and bool(offen.get(&"_wartet_auf_antwort")):
			return ((zeile as Control).get_child(0) as Control).get_global_rect().get_center()
		return offen.get_global_rect().get_center() + Vector2(0.0, offen.size.y * 0.3)
	var k: Variant = offen.get(&"_knopf")
	if k is Button and (k as Button).is_visible_in_tree():
		return (k as Button).get_global_rect().get_center()
	return offen.get_global_rect().get_center()


func _finde_fenster(knoten: Node) -> Control:
	for kind in knoten.get_children():
		if kind is VisualInstance3D:
			continue
		if (kind is SzeneView or kind is MomentView or kind is GeschenkView 				or (kind is Control and (kind as Control).has_signal(&"verdoppeln_gedrueckt"))) 				and (kind as Control).is_visible_in_tree():
			return kind as Control
		var tiefer: Control = _finde_fenster(kind)
		if tiefer != null:
			return tiefer
	return null


## Greift "Abholen" nicht mehr (Ziel bleibt "bereit", Befund 17.10.), gibt der Autospieler nach
## 6 Versuchen fuer 60 s Ruhe, statt die Zeit im Auftragsbrett zu verbringen.
func _abholen_frei() -> bool:
	var jetzt: int = Time.get_ticks_msec()
	if jetzt < _abholen_ruhe_bis:
		return false
	if _abhol_versuche >= 6:
		_abhol_versuche = 0
		_abholen_ruhe_bis = jetzt + 60000
		return false
	return true


func _knopf_mit_text(k: Node, text: String) -> Button:
	if k == null or not is_instance_valid(k):
		return null
	if k is Button and (k as Button).is_visible_in_tree() and not (k as Button).disabled and (k as Button).text == text:
		return k as Button
	for kind in k.get_children():
		var b: Button = _knopf_mit_text(kind, text)
		if b != null:
			return b
	return null


func _erster_knopf(k: Node) -> Button:
	if k == null or not is_instance_valid(k):
		return null
	if k is Button and (k as Button).is_visible_in_tree() and not (k as Button).disabled:
		return k as Button
	for kind in k.get_children():
		var b: Button = _erster_knopf(kind)
		if b != null:
			return b
	return null


func _bild_bei(ebene: String, name: String, max_s: float) -> String:
	var ende: int = Time.get_ticks_msec() + int(max_s * 1000.0)
	while Time.get_ticks_msec() < ende:
		if _textebenen().has(ebene):
			return "%s [%s]" % [await _bild(name), ",".join(_textebenen())]
		var ziel: Vector2 = _naechster_spielzug()
		if ziel.x >= 0.0:
			await _tippe(get_tree().root.get_final_transform() * ziel)
		for i in range(6):
			await _warte_ms(60)
			if _textebenen().has(ebene):
				return "%s [%s]" % [await _bild(name), ",".join(_textebenen())]
	return "nicht gesehen: " + ebene
