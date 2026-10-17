## Entscheidet, OB und WIE ein Klang gespielt wird -- ohne Godot-Audio.
##
## Bewusst als RefCounted ohne Node und ohne AudioServer: Die interessanten
## Fehler eines Spielklangs sind Entscheidungsfehler, keine Abspielfehler.
## "Warum kommt der Ausbau-Klang dreimal?" und "warum ist der Hinweis so
## penetrant?" lassen sich hier headless in Millisekunden pruefen; ein Test,
## der echte Audiohardware braucht, laeuft auf keinem Bauserver.
##
## AudioDirector besitzt die Abspielseite und fragt hier nur nach.
class_name AudioRegeln
extends RefCounted

const PFAD: String = "res://data/audio/sounds.json"

var _ereignisse: Dictionary = {}
var _globale_sperre: float = 0.0

## Wann wurde welches Ereignis zuletzt ausgeloest?
var _zuletzt: Dictionary = {}          ## String -> float (Sekunden)
var _zuletzt_irgendetwas: float = -999.0

## Der Spieler kann den Ton abschalten. Dann faellt die Entscheidung immer
## negativ aus -- und zwar HIER, nicht erst beim Abspielen: Ein stumm
## geschalteter Player, der trotzdem belegt wird, ist eine Fehlerquelle.
var ton_an: bool = true


func _init(daten: Dictionary = {}) -> void:
	if daten.is_empty():
		daten = laden()
	_ereignisse = daten.get("ereignisse", {}) as Dictionary
	_globale_sperre = float(daten.get("globale_sperre", 0.0))


static func laden(pfad: String = PFAD) -> Dictionary:
	if not FileAccess.file_exists(pfad):
		push_error("Klangzuordnung fehlt: %s" % pfad)
		return {}
	var text: String = FileAccess.get_file_as_string(pfad)
	var geparst: Variant = JSON.parse_string(text)
	if geparst is Dictionary:
		return geparst as Dictionary
	push_error("Klangzuordnung nicht lesbar: %s" % pfad)
	return {}


## Kennt das Regelwerk dieses Ereignis?
func kennt(ereignis: StringName) -> bool:
	return _ereignisse.has(String(ereignis))


## Alle Klangdateien, die vorgeladen werden muessen.
func benoetigte_klaenge() -> Array[String]:
	var namen: Array[String] = []
	for schluessel in _ereignisse.keys():
		var name: String = String((_ereignisse[schluessel] as Dictionary).get("klang", ""))
		if name != "" and not namen.has(name):
			namen.append(name)
	return namen


## Die eigentliche Entscheidung.
##
## `jetzt` ist die Spielzeit in Sekunden -- sie wird HINEINGEGEBEN und nicht
## aus der Engine geholt, damit ein Test einen ganzen Abend Spielzeit in einer
## Schleife durchlaufen lassen kann.
##
## `kennzahl` ist ein ereignisabhaengiger Wert; beim Ausbau die neue Stufe.
##
## Rueckgabe ist ein leeres Dictionary, wenn NICHTS gespielt werden soll.
func entscheide(ereignis: StringName, jetzt: float, kennzahl: int = 0) -> Dictionary:
	if not ton_an:
		return {}
	var schluessel: String = String(ereignis)
	if not _ereignisse.has(schluessel):
		return {}

	# Globale Sperre: Wenn mehrere Ereignisse im selben Bild zusammenfallen --
	# Ausbau, Meilenstein und Freischaltung treffen regelmaessig zusammen --
	# darf nicht alles gleichzeitig losgehen. Das erste gewinnt.
	if jetzt - _zuletzt_irgendetwas < _globale_sperre:
		return {}

	var regel: Dictionary = _ereignisse[schluessel] as Dictionary
	var sperre: float = float(regel.get("sperre", 0.0))
	if jetzt - float(_zuletzt.get(schluessel, -999.0)) < sperre:
		return {}

	_zuletzt[schluessel] = jetzt
	_zuletzt_irgendetwas = jetzt

	return {
		"klang": String(regel.get("klang", "")),
		"lautstaerke_db": float(regel.get("lautstaerke_db", 0.0)),
		"tonhoehe": _tonhoehe(regel, kennzahl),
	}


## Die Tonhoehe steigt mit jeder Stufe und faellt am Meilenstein zurueck.
##
## Das ist kein Zierrat, sondern die hoerbare Fassung der Fortschrittskurve:
## Alle zwoelf Stufen greift ein Meilenstein-Multiplikator (CLAUDE.md), und
## genau dort setzt auch die Tonleiter neu an. Der Spieler hoert, wo er im
## Block steht, ohne hinzusehen -- und der Neuansatz nach dem Meilenstein
## fuehlt sich an wie Luftholen.
##
## Ohne Umbruch waere der Klang bei Stufe 80 ein unhoerbares Fiepen.
func _tonhoehe(regel: Dictionary, kennzahl: int) -> float:
	if regel.has("tonhoehe"):
		return float(regel["tonhoehe"])
	var schritt: float = float(regel.get("tonhoehe_schritt", 0.0))
	if schritt <= 0.0 or kennzahl <= 0:
		return 1.0
	var umbruch: int = int(regel.get("tonhoehe_umbruch", 12))
	var innerhalb: int = (kennzahl - 1) % maxi(umbruch, 1)
	var hoehe: float = 1.0 + schritt * float(innerhalb)
	return minf(hoehe, float(regel.get("tonhoehe_max", 2.0)))
