## Erkennt EINEN Tipp aus einer Folge von Eingaben an einer Tippflaeche:
## Druecken + Loslassen innerhalb von `schwelle` Pixeln, egal ob als Maus oder als
## Touch (Finger 0). Godot spiegelt Touch als Maus und umgekehrt
## (emulate_mouse_from_touch / emulate_touch_from_mouse); beide Folgen teilen sich
## hier EINEN Zustand. Das erste Loslassen entscheidet, das gespiegelte zweite
## findet keinen Druck mehr und zaehlt nicht -- also genau ein Tipp je Finger.
##
## Warum nicht nur das Maus-Loslassen (UiStil.ist_tipp)? Verliert die Flaeche
## zwischen Druck und Loslassen den Maus-Fokus (z. B. weil sie kurz unsichtbar
## war), kommt das Maus-Loslassen nie an -- das Touch-Loslassen schon.
##
## Langdruck (K6 §4.3): Bleibt der Finger `langdruck_ms` (data/ui/sheet.json) ruhig
## liegen, meldet `pruefe_langdruck` genau einmal true -- der Besitzer fragt das je Bild
## ab. Das folgende Loslassen ist dann kein Tipp mehr.
##
## Positionen werden mit `nach_bild` (globale Transformation der Flaeche) in
## Bildpixel umgerechnet: Bewegt sich die Flaeche unter dem ruhenden Finger
## (sie folgt der Karte, pulsiert), ist das kein Wisch.
class_name TippErkenner
extends RefCounted

var schwelle: float = 0.0
var langdruck_ms: int = 0
var _gedrueckt: bool = false
var _verworfen: bool = false
var _lang_gemeldet: bool = false
var _start: Vector2 = Vector2.ZERO
var _start_ms: int = 0
var _start_bild: int = -1
var _jetzt_ms: int = -1


func _init(schwelle_px: float = -1.0, lang_ms: int = -1) -> void:
	schwelle = schwelle_px if schwelle_px >= 0.0 else Sheet.tipp_schwelle()
	langdruck_ms = lang_ms if lang_ms >= 0 else int(Sheet.konfig().get("langdruck_ms", 0))


## Wertet ein Ereignis aus. true genau bei dem Loslassen, das einen Tipp abschliesst.
## `jetzt_ms` < 0 = Uhr des Systems (Tests geben die Zeit vor).
func auswerten(e: InputEvent, nach_bild: Transform2D = Transform2D.IDENTITY, jetzt_ms: int = -1) -> bool:
	_jetzt_ms = jetzt_ms
	if e is InputEventScreenTouch:
		var t := e as InputEventScreenTouch
		if t.index != 0:
			# Ein zweiter Finger: Pinch, kein Tipp.
			if t.pressed:
				_verworfen = true
			return false
		if t.canceled:
			_gedrueckt = false
			return false
		return _druck(nach_bild * t.position) if t.pressed else _los(nach_bild * t.position)
	if e is InputEventMouseButton:
		var m := e as InputEventMouseButton
		if m.button_index != MOUSE_BUTTON_LEFT:
			return false
		return _druck(nach_bild * m.position) if m.pressed else _los(nach_bild * m.position)
	if e is InputEventScreenDrag:
		var d := e as InputEventScreenDrag
		if d.index == 0:
			_bewegt(nach_bild * d.position)
		return false
	if e is InputEventMouseMotion:
		_bewegt(nach_bild * (e as InputEventMouseMotion).position)
	return false


## Laeuft gerade ein Druck (fuer Tests und Anzeige)?
func gedrueckt() -> bool:
	return _gedrueckt


## Liegt der Finger seit `langdruck_ms` ruhig? Genau einmal je Druck true.
func pruefe_langdruck(jetzt_ms: int = -1) -> bool:
	if not _gedrueckt or _verworfen or _lang_gemeldet or langdruck_ms <= 0:
		return false
	var jetzt: int = jetzt_ms if jetzt_ms >= 0 else Time.get_ticks_msec()
	if jetzt - _start_ms < langdruck_ms:
		return false
	_lang_gemeldet = true
	return true


func _uhr() -> int:
	return _jetzt_ms if _jetzt_ms >= 0 else Time.get_ticks_msec()


func _druck(p: Vector2) -> bool:
	# Der gespiegelte Zwilling (Maus zu Touch oder umgekehrt) kommt im selben Bild am
	# selben Ort: dieselbe Beruehrung, die Uhr laeuft weiter. Jeder andere Druck setzt
	# neu an -- ein Druck, dessen Loslassen nie kam, verfaellt.
	if _gedrueckt and p.distance_to(_start) <= 1.0 and Engine.get_process_frames() == _start_bild:
		return false
	_gedrueckt = true
	_verworfen = false
	_lang_gemeldet = false
	_start = p
	_start_ms = _uhr()
	_start_bild = Engine.get_process_frames()
	return false


## Der Druck verfaellt (das Feld ist verschwunden): kein Tipp, kein Langdruck.
func abbrechen() -> void:
	_gedrueckt = false


func _bewegt(p: Vector2) -> void:
	if _gedrueckt and p.distance_to(_start) > schwelle:
		_verworfen = true


func _los(p: Vector2) -> bool:
	if not _gedrueckt:
		return false
	_gedrueckt = false
	return not _verworfen and not _lang_gemeldet and p.distance_to(_start) <= schwelle
