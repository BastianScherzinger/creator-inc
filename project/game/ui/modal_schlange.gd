## Zentrale Modal-Warteschlange (K3 A3, Befund M7; K5 / K4 P1.7): Es ist immer
## hoechstens EIN Fenster offen -- und damit hoechstens eine Ebene, die etwas
## vom Spieler will. Reihenfolge nach Art (REIHENFOLGE), innerhalb einer Art in
## der Reihenfolge der Anmeldung:
##
##   eroeffnung -> offline -> abschluss -> geschenk -> moment -> szene -> hinweis
##
## Erst die Belohnung fuer das, was man gerade getan hat (Moment), dann die
## Geschichte (Szene). Kapitel sind seit K6 1c kein Fenster mehr (Zeile an der
## Zielleiste). Ganz hinten die kleine
## Symbol-Erklaerung (P1.9): Sie ist "leicht" -- meldet sich irgendetwas anderes
## an, waehrend sie steht, macht sie Platz (Signal `angemeldet`).
##
## Benutzung (von ueberall, z. B. hud.gd):
##
##     ModalSchlange.global().anmelden(&"szene", func(fertig: Callable) -> void:
##         var s := SzeneView.zeige_szene(...)
##         s.beendet.connect(func(_i: int, _a: String) -> void: fertig.call()))
##
## `zeigen` darf
##   - genau ein Argument nehmen: dann bekommt es `fertig` (Callable) und ruft es
##     beim Schliessen auf;
##   - ohne Argument sein und einen Node zurueckgeben: Das Modal gilt als
##     geschlossen, sobald dieser Node den Baum verlaesst (z. B. queue_free der
##     Ebene). Gibt es null zurueck, wurde nichts gezeigt -> sofort das naechste.
##   `ModalSchlange.global().fertig()` schliesst das offene Modal von aussen.
##
## Anmeldungen aus demselben Bild werden gesammelt und erst am Bildende
## gestartet -- so gewinnt der Offline-Bericht auch dann, wenn die Szene eine
## Zeile frueher angemeldet wurde, und gleichzeitig faellige Momente lassen sich
## zu EINEM Sammelfenster buendeln. In Tests (keine Frames) `verzoegert = false`
## setzen oder `naechstes()` selbst aufrufen.
##
## K6 1c (§4.4) -- nie zwei Fenster direkt hintereinander:
##   - `moment` (Raumkauf) kommt erst, wenn der Spieler seit dem letzten Fenster
##     getippt hat (`melde_tipp`) -- der Raum-Moment nach dem Offline-Bericht wartet
##     also auf den ersten Tipp;
##   - alle anderen Arten (Szene, Geschenk ...) brauchen `abstand_s` Spielzeit seit
##     dem letzten Fenster (`ticke(delta)` zaehlt sie, solange keins offen ist);
##   - ausgenommen sind `OHNE_ABSTAND` (Eroeffnung, Offline-Bericht) und Anmeldungen
##     `vom_spieler` (der Spieler hat das Fenster selbst angetippt).
##   Der Abstand steht in data/ui/hinweise.json (`fenster_abstand_s`).
class_name ModalSchlange
extends RefCounted

## Ein Modal ist geschlossen worden (Art des Modals).
signal fertig_gemeldet(art: StringName)
## Ein Modal wird jetzt gezeigt (erst, wenn wirklich etwas zu sehen ist).
signal gezeigt(art: StringName)
## Etwas hat sich angemeldet (Art). Ein offenes leichtes Modal raeumt dann das Feld.
signal angemeldet(art: StringName)

const REIHENFOLGE: Array[StringName] = [&"eroeffnung", &"offline", &"abschluss", &"geschenk", &"moment",
	&"szene", &"hinweis"]
## Arten, die Platz machen, sobald sich etwas anderes anmeldet.
const LEICHT: Array[StringName] = [&"hinweis"]
## Arten, die ohne Abstand zum vorigen Fenster kommen duerfen (Sitzungsstart).
## Der Weltabschluss (K7) kommt sofort, sobald kein anderes Fenster offen ist.
const OHNE_ABSTAND: Array[StringName] = [&"eroeffnung", &"offline", &"abschluss"]
## Arten, die statt des Abstands nur einen Tipp des Spielers seit dem letzten Fenster brauchen.
const NACH_TIPP: Array[StringName] = [&"moment"]

## Am Bildende starten (Spiel) oder sofort (Tests).
var verzoegert: bool = true
## Spielzeit (s), die zwischen zwei Fenstern liegen muss. Das Spiel setzt den Wert aus
## data/ui/hinweise.json; 0 = Regel aus, auch die Tipp-Regel (Tests der reinen Reihenfolge).
var abstand_s: float = 0.0

## Spielzeit seit dem Ende des letzten Fensters (gross = es gab noch keins).
var _seit_fenster: float = INF
## Hat der Spieler seit dem letzten Fenster getippt?
var _tipp_seit_fenster: bool = true

var _wartend: Array[Dictionary] = []      ## {art, zeigen, nr}
var _offen: StringName = &""
var _offen_nr: int = -1
var _offen_knoten: Node = null             ## Knoten des offenen Modals, falls `zeigen` einen lieferte
var _offen_gezeigt: bool = false           ## War das offene Modal wirklich zu sehen (nicht sofort erledigt)?
var _zaehler: int = 0
var _gezeigt_zaehler: int = 0
var _geplant: bool = false

static var _global: ModalSchlange


## Die eine Schlange des laufenden Spiels.
static func global() -> ModalSchlange:
	if _global == null:
		_global = ModalSchlange.new()
	return _global


## Neue, leere Schlange (Weltwechsel, Neuaufbau). Offenes wird vergessen.
static func zuruecksetzen() -> ModalSchlange:
	_global = ModalSchlange.new()
	return _global


static func rang(art: StringName) -> int:
	var i: int = REIHENFOLGE.find(art)
	return i if i >= 0 else REIHENFOLGE.size()


## `vom_spieler`: Der Spieler hat das Fenster selbst ausgeloest (Tipp auf ein "!") -- kein Abstand.
func anmelden(art: StringName, zeigen: Callable, vom_spieler: bool = false) -> void:
	_zaehler += 1
	_wartend.append({"art": art, "zeigen": zeigen, "nr": _zaehler, "spieler": vom_spieler})
	angemeldet.emit(art)
	if _offen != &"":
		return
	if not verzoegert:
		naechstes()
		return
	if not _geplant:
		_geplant = true
		_plane.call_deferred()


func _plane() -> void:
	_geplant = false
	if _offen == &"":
		naechstes()


## Zeigt das wichtigste wartende Modal, falls keins offen ist.
## Gibt true zurueck, wenn eins gezeigt wird.
func naechstes() -> bool:
	if _offen != &"":
		return true
	while not _wartend.is_empty():
		var eintrag: Dictionary = _nimm_wichtigstes()
		if eintrag.is_empty():
			return false     # Es wartet etwas, aber noch nicht an der Reihe (Abstand/Tipp).
		var zeigen: Callable = eintrag["zeigen"] as Callable
		if not zeigen.is_valid():
			continue
		_offen = eintrag["art"] as StringName
		_offen_nr = int(eintrag["nr"])
		_offen_knoten = null
		_offen_gezeigt = false
		var art: StringName = _offen
		var nr: int = _offen_nr
		var schliessen: Callable = func() -> void: _fertig_fuer(nr)
		var ergebnis: Variant = null
		if zeigen.get_argument_count() >= 1:
			ergebnis = zeigen.call(schliessen)
		else:
			ergebnis = zeigen.call()
		if zeigen.get_argument_count() == 0 and _offen_nr == nr:
			if ergebnis is Node and is_instance_valid(ergebnis) and (ergebnis as Node).is_inside_tree():
				_offen_knoten = ergebnis as Node
				(ergebnis as Node).tree_exiting.connect(schliessen, CONNECT_ONE_SHOT)
			else:
				# Nichts gezeigt (z. B. kein Geschenk faellig, Moment schon gebuendelt):
				# sofort erledigt, sonst klemmt die Schlange. Zaehlt nicht als Fenster.
				_offen = &""
				_offen_nr = -1
				continue
		if _offen_nr == nr:
			_offen_gezeigt = true
			if not LEICHT.has(art):
				_gezeigt_zaehler += 1
			gezeigt.emit(art)
		return _offen != &"" or naechstes()
	return false


## Das offene Modal ist zu; das naechste kommt.
func fertig() -> void:
	if _offen != &"":
		_fertig_fuer(_offen_nr)


## Schliesst das offene Modal hart (Pruefschalter --fenster-log): Knoten weg, naechstes.
func schliesse_offenes() -> void:
	if _offen == &"":
		return
	if _offen_knoten != null and is_instance_valid(_offen_knoten):
		_offen_knoten.queue_free()
	fertig()


func _fertig_fuer(nr: int) -> void:
	if nr != _offen_nr or _offen == &"":
		return
	var art: StringName = _offen
	_offen = &""
	_offen_nr = -1
	_offen_knoten = null
	# Nur ein Fenster, das wirklich zu sehen war, startet den Abstand neu (eine verworfene,
	# sofort erledigte Szene nicht).
	if not LEICHT.has(art) and _offen_gezeigt:
		_seit_fenster = 0.0
		_tipp_seit_fenster = false
	_offen_gezeigt = false
	fertig_gemeldet.emit(art)
	if verzoegert and not _wartend.is_empty():
		if not _geplant:
			_geplant = true
			_plane.call_deferred()
	else:
		naechstes()


func ist_offen() -> bool:
	return _offen != &""


func offene_art() -> StringName:
	return _offen


## Ist ein Modal offen oder wartet eins? (Die Symbol-Erklaerung fragt das, bevor sie kommt.)
func ist_beschaeftigt() -> bool:
	return _offen != &"" or not _wartend.is_empty()


## Spielzeit vergeht (Hud, je Bild). Nur ohne offenes Fenster; wird ein wartendes
## dadurch faellig, kommt es jetzt.
func ticke(delta: float) -> void:
	if _offen != &"":
		return
	_seit_fenster += delta
	if not _wartend.is_empty() and _hat_bereites():
		naechstes()


## Der Spieler hat getippt (ohne offenes Fenster). Ein wartender Raum-Moment darf kommen.
func melde_tipp() -> void:
	if _offen != &"":
		return
	_tipp_seit_fenster = true
	if not _wartend.is_empty() and _hat_bereites():
		if verzoegert:
			if not _geplant:
				_geplant = true
				_plane.call_deferred()
		else:
			naechstes()


## Wartet etwas, das jetzt gezeigt werden darf? (Ortsblasen halten sich dann zurueck.)
func bereit_wartend() -> bool:
	return _offen == &"" and _hat_bereites()


## Sekunden Spielzeit seit dem letzten Fenster (INF = noch keins).
func seit_letztem_fenster() -> float:
	return _seit_fenster


## Darf dieser Eintrag jetzt kommen (Abstand, Tipp)?
func _darf(eintrag: Dictionary) -> bool:
	var art: StringName = eintrag["art"] as StringName
	if bool(eintrag.get("spieler", false)) or OHNE_ABSTAND.has(art) or LEICHT.has(art):
		return true
	if abstand_s <= 0.0:
		return true      # Regel aus (Tests der reinen Reihenfolge)
	if NACH_TIPP.has(art):
		return _tipp_seit_fenster
	return _seit_fenster >= abstand_s


func _hat_bereites() -> bool:
	for e in _wartend:
		if _darf(e):
			return true
	return false


## Wie viele Fenster bisher wirklich gezeigt wurden (Pruefung P1.7). Leichte zaehlen nicht.
func anzahl_gezeigt() -> int:
	return _gezeigt_zaehler


## Arten der wartenden Modale in der Reihenfolge, in der sie kommen werden.
func wartend() -> Array[StringName]:
	var kopie: Array[Dictionary] = _wartend.duplicate()
	kopie.sort_custom(_frueher)
	var arten: Array[StringName] = []
	for e in kopie:
		arten.append(e["art"] as StringName)
	return arten


## Wartende einer Art verwerfen (z. B. gestaute Szenen beim Vorspulen, N8).
func verwerfe(art: StringName) -> int:
	var vorher: int = _wartend.size()
	_wartend.assign(_wartend.filter(func(e: Dictionary) -> bool: return e["art"] != art))
	return vorher - _wartend.size()


## Das wichtigste wartende Modal, das jetzt kommen darf -- leer, wenn keins darf.
func _nimm_wichtigstes() -> Dictionary:
	var beste: int = -1
	for i in range(_wartend.size()):
		if not _darf(_wartend[i]):
			continue
		if beste < 0 or _frueher(_wartend[i], _wartend[beste]):
			beste = i
	if beste < 0:
		return {}
	var eintrag: Dictionary = _wartend[beste]
	_wartend.remove_at(beste)
	return eintrag


static func _frueher(a: Dictionary, b: Dictionary) -> bool:
	var ra: int = rang(a["art"] as StringName)
	var rb: int = rang(b["art"] as StringName)
	if ra != rb:
		return ra < rb
	return int(a["nr"]) < int(b["nr"])
