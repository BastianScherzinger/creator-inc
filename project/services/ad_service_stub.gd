## Werbung ohne Werbung -- der Stub fuer Entwicklung und Tests.
##
## Er tut so, als liefe eine belohnte Werbung: Er braucht Zeit, er kann
## fehlschlagen, und er kennt Sperrzeiten und ein Tageslimit. Alle drei
## Eigenschaften sind der Grund, warum es ihn gibt. Ein Stub, der sofort
## "Belohnung!" ruft, ist bequem und wertlos -- er testet den einen Fall,
## der spaeter nie das Problem ist.
##
## Werte aus data/services/ads.json, keine Zahl im Code.
class_name AdServiceStub
extends AdService

const PFAD: String = "res://data/services/ads.json"

## Simulierte Dauer und Fehlerquote sind ueber diese Felder auch im Test
## setzbar -- dort will man nicht sechs Sekunden warten.
var dauer_sekunden: float = 6.0
var fehlerquote: float = 0.0

## Zeitquelle (Sekunden). Leer = echte Uhr. Tests setzen eine eigene, damit
## Mindestabstand und Sperrzeiten ohne Warten pruefbar sind.
var uhr: Callable = Callable()
## Kalendertag (JJJJ-MM-TT). Leer = Systemdatum. Tests setzen ihn.
var datum: Callable = Callable()

var _platzierungen: Dictionary = {}       ## String -> Dictionary
var _global: Dictionary = {}              ## Mindestabstand, Tageslimit, Startschutz
var _zuletzt_gesehen: Dictionary = {}     ## String -> float (Uhr)
var _sitzung_gesehen: Dictionary = {}     ## String -> int (seit App-Start)
var _letzte_irgendeine: float = -999999.0
var _tag: String = ""
var _tag_gesamt: int = 0                  ## Werbungen heute, alle Platzierungen
var _tag_je: Dictionary = {}              ## String -> int, heute
var _laeuft: StringName = &""
var _stand_bekannt: bool = false
var _spielzeit: float = 0.0
var _raum_gekauft: Callable = Callable()
var _speicherpfad: String = ""

var _zufall := RandomNumberGenerator.new()


## Konfiguration im KONSTRUKTOR, nicht in _ready().
##
## _ready() laeuft erst, wenn der Knoten in den Baum kommt -- und das kann
## spaeter sein, als der Aufrufer denkt. Ein Test, der direkt nach add_child()
## die Dauer auf 50 ms setzt, bekam sie danach wieder auf sechs Sekunden
## gesetzt und lief in einen Zeitfehler, dessen Ursache nirgends stand.
## Was ein Objekt zum Arbeiten braucht, gehoert in seine Erzeugung.
func _init() -> void:
	_zufall.randomize()
	var daten: Dictionary = laden()
	dauer_sekunden = float(daten.get("stub_dauer_sekunden", dauer_sekunden))
	fehlerquote = float(daten.get("stub_fehlerquote", fehlerquote))
	_platzierungen = daten.get("platzierungen", {}) as Dictionary
	_global = {
		"mindestabstand_sekunden": float(daten.get("mindestabstand_sekunden", 0.0)),
		"hoechstzahl_pro_tag": int(daten.get("hoechstzahl_pro_tag", 0)),
		"erst_ab": daten.get("erst_ab", {}) as Dictionary,
	}


## Die Oberflaeche findet den Dienst ueber die Gruppe "werbung" (Geschenk- und
## Rueckkehr-Karte werden ohne Hud-Bezug gebaut).
func _enter_tree() -> void:
	add_to_group(&"werbung")


## Der Faktor einer Platzierung ohne Dienst-Objekt (Beschriftung vor dem Zeigen).
static func faktor(platzierung: StringName, datei: String = PFAD) -> float:
	var regeln: Dictionary = laden(datei).get("platzierungen", {}) as Dictionary
	var regel: Dictionary = regeln.get(String(platzierung), {}) as Dictionary
	return float(regel.get("faktor", 1.0))


static func laden(pfad: String = PFAD) -> Dictionary:
	if not FileAccess.file_exists(pfad):
		push_error("Werbe-Konfiguration fehlt: %s" % pfad)
		return {}
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	return geparst as Dictionary if geparst is Dictionary else {}


## Zeitquelle und Wartezeit gehen NICHT ueber get_tree().
##
## get_tree() ist null, solange der Knoten nicht im Szenenbaum haengt -- und
## wann das passiert, entscheidet der Aufrufer, nicht dieser Dienst. Genau
## daran ist der erste Anlauf gescheitert: Der Aufruf lief ins Leere, es kam
## nie ein Signal, und der Fehler stand als Zeitueberschreitung im Test statt
## als Ursache. Ein Dienst, der eine Antwort verspricht, muss sie unter allen
## Umstaenden geben koennen.
func _jetzt() -> float:
	if uhr.is_valid():
		return float(uhr.call())
	return float(Time.get_ticks_msec()) / 1000.0


func _heute() -> String:
	if datum.is_valid():
		return String(datum.call())
	return Time.get_date_string_from_system()


## Neuer Kalendertag: Tageszaehler auf null.
func _tag_pruefen() -> void:
	var heute: String = _heute()
	if heute != _tag:
		_tag = heute
		_tag_gesamt = 0
		_tag_je = {}


## Dauer 0 heisst: SOFORT antworten, ohne einen Frame abzuwarten.
##
## Das ist kein Schoenheitsfehler, sondern der Testmodus. Im gdUnit-Lauf
## werden keine SceneTree-Frames verarbeitet -- ein Timer laeuft dort nie ab,
## und eine abgekoppelte Coroutine wacht nie wieder auf. Mit Dauer 0 pruefen
## die Tests, worauf es ankommt (Sperrzeiten, Limits, Fehlerwege), und die
## echte Wartezeit bleibt dem Spiel vorbehalten.
func _warte(sekunden: float) -> void:
	if sekunden <= 0.0:
		return
	var baum := Engine.get_main_loop() as SceneTree
	if baum == null:
		return
	await baum.create_timer(sekunden).timeout


func kennt(platzierung: StringName) -> bool:
	return _platzierungen.has(String(platzierung))


func ist_bereit(platzierung: StringName) -> bool:
	return grund(platzierung).is_empty()


## Die Reihenfolge ist Absicht: erst "gibt es das ueberhaupt", dann Startschutz,
## dann die harten Limits, zuletzt die Ruhezeiten. Leer = bereit.
func grund(platzierung: StringName) -> String:
	if not kennt(platzierung):
		return "unbekannt"
	if _laeuft != &"":
		return "laeuft"
	if not _start_frei():
		return "start"
	_tag_pruefen()
	var regel: Dictionary = _platzierungen.get(String(platzierung), {}) as Dictionary
	var tag_max: int = int(_global.get("hoechstzahl_pro_tag", 0))
	if tag_max > 0 and _tag_gesamt >= tag_max:
		return "tag"
	var je_tag: int = int(regel.get("hoechstzahl_pro_tag", 0))
	if je_tag > 0 and int(_tag_je.get(String(platzierung), 0)) >= je_tag:
		return "tag"
	var je_sitzung: int = int(regel.get("hoechstzahl_pro_sitzung", 0))
	if je_sitzung > 0 and int(_sitzung_gesehen.get(String(platzierung), 0)) >= je_sitzung:
		return "sitzung"
	if sperrzeit_rest(platzierung) > 0.0:
		return "abstand"
	return ""


## Startschutz (K3 C1): vor `erst_ab.spielzeit_s` und vor dem Kauf des genannten
## Raums ist nirgends ein Angebot. Ohne gemeldeten Spielstand (reiner Dienst im
## Test) gilt kein Schutz -- die Oberflaeche meldet ihn mit setze_stand().
func _start_frei() -> bool:
	if not _stand_bekannt:
		return true
	var ab: Dictionary = _global.get("erst_ab", {}) as Dictionary
	if _spielzeit < float(ab.get("spielzeit_s", 0.0)):
		return false
	var raum: String = String(ab.get("bereich", ""))
	if not raum.is_empty() and _raum_gekauft.is_valid():
		return bool(_raum_gekauft.call(StringName(raum)))
	return true


func setze_stand(spielzeit: float, raum_gekauft: Callable) -> void:
	_stand_bekannt = true
	_spielzeit = spielzeit
	_raum_gekauft = raum_gekauft


func wert(platzierung: StringName, schluessel: String, standard: Variant = null) -> Variant:
	var regel: Dictionary = _platzierungen.get(String(platzierung), {}) as Dictionary
	return regel.get(schluessel, standard)


## Wartezeit bis zur naechsten Werbung: die Sperrzeit der Platzierung ODER der
## globale Mindestabstand zur letzten Werbung -- was laenger dauert.
func sperrzeit_rest(platzierung: StringName) -> float:
	var regel: Dictionary = _platzierungen.get(String(platzierung), {}) as Dictionary
	var jetzt: float = _jetzt()
	var sperre: float = float(regel.get("sperrzeit_sekunden", 0.0))
	var zuletzt: float = float(_zuletzt_gesehen.get(String(platzierung), -999999.0))
	var eigene: float = maxf(0.0, sperre - (jetzt - zuletzt))
	var abstand: float = float(_global.get("mindestabstand_sekunden", 0.0))
	var global_rest: float = maxf(0.0, abstand - (jetzt - _letzte_irgendeine))
	return maxf(eigene, global_rest)


## Wie viele Werbungen heute noch moeglich sind (fuer Anzeige und Tests).
func rest_heute() -> int:
	_tag_pruefen()
	var tag_max: int = int(_global.get("hoechstzahl_pro_tag", 0))
	return maxi(0, tag_max - _tag_gesamt) if tag_max > 0 else 999


# --- Tageszaehler: Speichern und Laden ---------------------------------------------

func zaehler_als_dict() -> Dictionary:
	_tag_pruefen()
	return {"tag": _tag, "gesamt": _tag_gesamt, "je": _tag_je.duplicate()}


func zaehler_laden(daten: Dictionary) -> void:
	_tag = String(daten.get("tag", ""))
	_tag_gesamt = int(daten.get("gesamt", 0))
	_tag_je = {}
	var je: Dictionary = daten.get("je", {}) as Dictionary
	for k in je:
		_tag_je[String(k)] = int(je[k])
	_tag_pruefen()


func verbinde_speicher(pfad: String) -> void:
	_speicherpfad = pfad
	if pfad.is_empty() or not FileAccess.file_exists(pfad):
		return
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	if geparst is Dictionary:
		zaehler_laden(geparst as Dictionary)


func _speichern() -> void:
	if _speicherpfad.is_empty():
		return
	var datei := FileAccess.open(_speicherpfad, FileAccess.WRITE)
	if datei != null:
		datei.store_string(JSON.stringify(zaehler_als_dict()))


func zeige_belohnt(platzierung: StringName) -> void:
	if not kennt(platzierung):
		nicht_verfuegbar.emit(platzierung, "unbekannte Platzierung")
		return
	var warum: String = grund(platzierung)
	if not warum.is_empty():
		var text: Dictionary = {
			"laeuft": "es laeuft bereits eine", "start": "Startschutz",
			"tag": "Tageslimit erreicht", "sitzung": "Sitzungslimit erreicht",
			"abstand": "Sperrzeit",
		}
		nicht_verfuegbar.emit(platzierung, String(text.get(warum, warum)))
		return

	_laeuft = platzierung
	# Die Wartezeit ist der Punkt. Sie zwingt die Oberflaeche dazu, einen
	# Zwischenzustand zu haben -- und den braucht sie spaeter mit echtem SDK
	# genauso.
	await _warte(dauer_sekunden)
	_laeuft = &""

	if _zufall.randf() < fehlerquote:
		nicht_verfuegbar.emit(platzierung, "Ladefehler")
		return

	_zaehle_gesehen(platzierung)
	belohnung_verdient.emit(platzierung)


## Zaehlt eine vollstaendig gesehene Werbung fuer Sperrzeit, Sitzungs- und
## Tageslimit. Auch der AdMob-Dienst nutzt das, damit die Limits ueberall gleich gelten.
func _zaehle_gesehen(platzierung: StringName) -> void:
	var jetzt: float = _jetzt()
	_zuletzt_gesehen[String(platzierung)] = jetzt
	_letzte_irgendeine = jetzt
	_sitzung_gesehen[String(platzierung)] = int(_sitzung_gesehen.get(String(platzierung), 0)) + 1
	_tag_pruefen()
	_tag_gesamt += 1
	_tag_je[String(platzierung)] = int(_tag_je.get(String(platzierung), 0)) + 1
	_speichern()


## Bricht eine laufende Vorfuehrung ab -- im echten Leben der Moment, in dem
## der Spieler die Werbung wegdrueckt.
func breche_ab() -> void:
	if _laeuft == &"":
		return
	var was: StringName = _laeuft
	_laeuft = &""
	abgebrochen.emit(was)
