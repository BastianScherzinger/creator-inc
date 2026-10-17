## Der Ablauf der Einfuehrung -- als reine Zustandsmaschine, ohne Oberflaeche.
##
## Dieselbe Trennung wie bei AudioRegeln: Was man pruefen will, ist nicht die
## Darstellung, sondern die Frage "haengt der Spieler hier fest?". Ein Tutorial
## mit einer unerfuellbaren Bedingung ist der teuerste Fehler eines Spiels --
## niemand meldet ihn, die Leute deinstallieren einfach.
##
## Diese Klasse enthaelt KEINEN Text (Regel D3 / ADR-010). Sie kennt
## Schritt-IDs; die Saetze holt die Oberflaeche aus dem Thema.
class_name TutorialAblauf
extends RefCounted

const PFAD: String = "res://data/tutorial/tutorial.json"

var _schritte: Array = []

## Index des laufenden Schritts.
var schritt: int = 0
## Beendet heisst: durchlaufen ODER uebersprungen. Der Unterschied ist fuer
## das Spiel keiner -- in beiden Faellen soll nichts mehr erscheinen.
var beendet: bool = false

## Was ist bisher passiert? Beides wird UNABHAENGIG vom laufenden Schritt
## fortgeschrieben:
##   _zaehler -- wie oft ein Ereignis eintrat (etwa Engpasswechsel)
##   _letzte  -- der zuletzt gemeldete Wert (etwa die Gesamtstufen)
##
## Der Grund steht in _pruefe_fortschritt: Ein Schritt, dessen Bedingung schon
## erfuellt war, BEVOR er begann, muss sofort durch sein.
var _zaehler: Dictionary = {}
var _letzte: Dictionary = {}
## Zaehlerstand bei Beginn des laufenden Schritts. Bedingungen mit "neu": true zaehlen nur,
## was SEITDEM passiert ist -- sonst zaehlte ein Antippen aus einem frueheren Schritt mit.
var _basis: Dictionary = {}


func _init(daten: Dictionary = {}) -> void:
	if daten.is_empty():
		daten = laden()
	_schritte = daten.get("schritte", []) as Array


static func laden(pfad: String = PFAD) -> Dictionary:
	if not FileAccess.file_exists(pfad):
		push_error("Tutorial-Ablauf fehlt: %s" % pfad)
		return {}
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	if geparst is Dictionary:
		return geparst as Dictionary
	push_error("Tutorial-Ablauf nicht lesbar: %s" % pfad)
	return {}


func anzahl_schritte() -> int:
	return _schritte.size()


## Der laufende Schritt, oder ein leeres Dictionary, wenn nichts zu zeigen ist.
func aktueller() -> Dictionary:
	if beendet or schritt < 0 or schritt >= _schritte.size():
		return {}
	return _schritte[schritt] as Dictionary


## ID des laufenden Schritts -- der Schluessel, unter dem die Oberflaeche
## den Text im Thema findet.
func aktuelle_id() -> String:
	var s: Dictionary = aktueller()
	return String(s.get("id", ""))


## Welches Element soll hervorgehoben werden?
func aktuelles_ziel() -> String:
	var s: Dictionary = aktueller()
	return String(s.get("ziel", ""))


## Meldet ein Ereignis. Gibt true zurueck, wenn dadurch weitergeschaltet wurde.
##
## Die Meldungen kommen aus der Oberflaeche und dem Kern und werden IMMER
## geschickt, auch wenn das Tutorial laengst beendet ist -- der Aufrufer soll
## sich nicht merken muessen, ob er noch melden muss. Das Filtern passiert hier.
func melde(typ: StringName, wert: Variant = null) -> bool:
	if beendet:
		return false
	var schluessel: String = String(typ)
	_zaehler[schluessel] = int(_zaehler.get(schluessel, 0)) + 1
	if wert != null:
		_letzte[schluessel] = wert
	return _pruefe_fortschritt()


## Schaltet weiter, solange die Bedingung des laufenden Schritts erfuellt ist.
##
## Die Schleife ist keine Vorsicht, sondern noetig: Wenn ein Schritt endet,
## kann der naechste laengst erfuellt sein. Der Engpass wechselt oft genau
## einen Wimpernschlag zu frueh -- naemlich beim ersten Ausbau, waehrend noch
## der Ausbau-Schritt laeuft. Wuerde erst der NAECHSTE Wechsel zaehlen, haengt
## der Spieler vor einem Hinweis, dessen Bedingung er bereits erfuellt hat.
## Das ist der haeufigste Weg, auf dem ein Tutorial tot laeuft.
func _pruefe_fortschritt() -> bool:
	var bewegt: bool = false
	var schutz: int = 0
	while not beendet and schutz < 64:
		schutz += 1
		var s: Dictionary = aktueller()
		if s.is_empty():
			break
		if not _erfuellt(s.get("abschluss", {}) as Dictionary):
			break
		weiter()
		bewegt = true
	return bewegt


func _erfuellt(bedingung: Dictionary) -> bool:
	var typ: String = String(bedingung.get("typ", ""))
	var erwartet: Variant = bedingung.get("wert", null)
	match typ:
		"station_gewaehlt":
			return String(_letzte.get(typ, "")) == String(erwartet)
		"stufen_gesamt", "ziele_eingeloest":
			# Absolute Messwerte: ueberleben einen Neustart mitten im Schritt.
			return float(_letzte.get(typ, -1.0)) >= float(erwartet)
		_:
			# Zaehlende Bedingung: Wie oft ist das Ereignis insgesamt (oder, mit "neu",
			# seit Beginn des Schritts) eingetreten?
			var anzahl: float = float(_zaehler.get(typ, 0))
			if bool(bedingung.get("neu", false)):
				anzahl -= float(_basis.get(typ, 0))
			return anzahl >= float(erwartet)


## Soll die Oberflaeche dieses Element schon zeigen? Ein Schritt schaltet es mit "zeigt"
## frei; es bleibt bis zum Ende des Tutorials da (und danach immer). So bleibt der Anfang
## leer-ruhig (K2 3): nur Kopfleiste, dann kommt je Schritt genau ein Ding dazu.
func zeigt(was: String) -> bool:
	if beendet:
		return true
	for i in range(mini(schritt + 1, _schritte.size())):
		if String((_schritte[i] as Dictionary).get("zeigt", "")) == was:
			return true
	return false


func weiter() -> void:
	_basis = _zaehler.duplicate()
	schritt += 1
	if schritt >= _schritte.size():
		beendet = true


## Der Spieler bricht ab. Das muss jederzeit moeglich sein: Ein Tutorial, das
## man nicht wegklicken kann, ist eine Geiselnahme -- und ein Spieler, der es
## schon kennt, ist genau der, den man behalten will.
func ueberspringen() -> void:
	beendet = true


func to_dict() -> Dictionary:
	return {"schritt": schritt, "beendet": beendet}


func apply_dict(daten: Dictionary) -> void:
	schritt = int(daten.get("schritt", 0))
	beendet = bool(daten.get("beendet", false))
	# Ein gespeicherter Schritt jenseits der Liste kann entstehen, wenn eine
	# spaetere Fassung Schritte ENTFERNT. Dann ist das Tutorial durch, nicht
	# kaputt.
	if schritt >= _schritte.size():
		beendet = true
