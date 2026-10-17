## A/B-Varianten der Kernbildschirme -- ohne jede Datenerhebung.
##
## Heute (vor dem Release) rendert die Vorschau je Bildschirm beide Varianten
## nebeneinander (`--variante a|b`, tools/ab_montage.py). Nach dem Release kann
## ein geschlossener Test Variante A oder B bekommen; ausgewertet wird per
## Rueckmeldung der Tester. Die App sendet nichts; gemessen wird nur lokal (services/messung_service.gd, K3 C3).
##
## Reihenfolge der Entscheidung:
##   1. `override_schirm` je Bildschirm (`--ab boost=b,raum_panel=a`, K3 A3),
##   2. `override` global (`--variante a|b`, Rueckfall fuer alle Schirme),
##   3. `aktiv` in data/experimente.json (Standard bzw. feststehender Gewinner),
##   4. deterministisch aus dem Zufallswert der Installation.
##
## Die Schalter kommen von der PC-Kommandozeile oder aus `user://start_args.txt`
## (nur Debug-Builds). `variante()` liest sie beim ersten Aufruf selbst, damit
## jeder Darsteller sie ohne main.gd abfragen kann; main.gd setzt sie zusaetzlich
## ausdruecklich (`lade_argumente`).
class_name Experimente
extends RefCounted

const PFAD: String = "res://data/experimente.json"

## Von der Oberflaeche aus `--variante` gesetzt. Leer = nicht erzwungen.
static var override: String = ""

## Je Bildschirm erzwungen (`--ab schirm=variante,...`): schirm -> "a" | "b".
static var override_schirm: Dictionary = {}

## Wert der Installation (SaveData.installations_wert); vom Kern gesetzt.
static var installations_wert: int = 0

static var _argumente_gelesen: bool = false
static var _daten: Dictionary = {}
static var _daten_geladen: bool = false


static func _lade() -> Dictionary:
	if _daten_geladen:
		return _daten
	_daten_geladen = true
	_daten = {}
	if FileAccess.file_exists(PFAD):
		var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(PFAD))
		if roh is Dictionary:
			_daten = roh as Dictionary
	return _daten


## `karte=a,pfeil=b` -> {"karte": "a", "pfeil": "b"}. Kaputte Teile werden
## still uebergangen; Gross-/Kleinschreibung egal.
static func parse_ab(text: String) -> Dictionary:
	var ergebnis: Dictionary = {}
	for teil in text.split(",", false):
		var paar: PackedStringArray = teil.strip_edges().split("=", false)
		if paar.size() != 2:
			continue
		var schirm: String = paar[0].strip_edges().to_lower()
		var wert: String = paar[1].strip_edges().to_lower()
		if schirm != "" and wert != "":
			ergebnis[schirm] = wert
	return ergebnis


## Setzt `override` und `override_schirm` aus den Pruefschaltern.
## Mehrere `--ab` werden zusammengefuehrt (spaetere gewinnen).
static func lade_argumente(argumente: PackedStringArray) -> void:
	_argumente_gelesen = true
	override = ""
	override_schirm = {}
	for i in range(argumente.size() - 1):
		if argumente[i] == "--variante":
			override = argumente[i + 1].strip_edges().to_lower()
		elif argumente[i] == "--ab":
			override_schirm.merge(parse_ab(argumente[i + 1]), true)


## Die Pruefschalter wie main.gd sie sieht: Kommandozeile plus (nur Debug)
## `user://start_args.txt`.
static func pruefschalter() -> PackedStringArray:
	var argumente: PackedStringArray = OS.get_cmdline_user_args()
	if OS.is_debug_build() and FileAccess.file_exists("user://start_args.txt"):
		var text: String = FileAccess.get_file_as_string("user://start_args.txt")
		for teil in text.strip_edges().split(" ", false):
			argumente.append(teil)
	return argumente


## Alle Bildschirme mit Varianten (fuer die lokale Messung).
static func schirme() -> Array[String]:
	var liste: Array[String] = []
	for schluessel in (_lade().get("varianten", {}) as Dictionary).keys():
		liste.append(String(schluessel))
	return liste


## Alle Varianten eines Bildschirms, z. B. ["a", "b"]. Leer, wenn unbekannt.
static func varianten(schirm: String) -> Array[String]:
	var liste: Array[String] = []
	var roh: Array = (_lade().get("varianten", {}) as Dictionary).get(schirm, []) as Array
	for eintrag in roh:
		liste.append(String(eintrag))
	return liste


## Die Variante, die dieser Bildschirm JETZT zeigt. Ohne Eintrag "a".
static func variante(schirm: String) -> String:
	if not _argumente_gelesen:
		lade_argumente(pruefschalter())
	var erzwungen: String = String(override_schirm.get(schirm, override))
	return waehle(schirm, installations_wert, erzwungen)


## Reine Funktion, damit testbar: Erzwingung, Gewinner oder Hash des Wertes.
static func waehle(schirm: String, wert: int, erzwungen: String = "", mit_aktiv: bool = true) -> String:
	var alle: Array[String] = varianten(schirm)
	if alle.is_empty():
		return "a"
	if erzwungen != "" and alle.has(erzwungen):
		return erzwungen
	var aktiv: String = String((_lade().get("aktiv", {}) as Dictionary).get(schirm, "")) if mit_aktiv else ""
	if aktiv != "" and alle.has(aktiv):
		return aktiv
	# Je Bildschirm ein anderer Schluessel, damit nicht jeder Tester ueberall
	# dieselbe Seite bekommt.
	var schluessel: int = absi(("%s:%d" % [schirm, wert]).hash())
	return alle[schluessel % alle.size()]
