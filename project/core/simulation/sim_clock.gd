## Fester Simulationstakt und Offline-Nachholrechnung.
##
## Die Wirtschaft rechnet in gleichmaessigen Schritten von 0,25 s -- unabhaengig
## von der Bildrate. Auf einem 30-fps- und einem 120-fps-Geraet kommt exakt
## dasselbe heraus. Das ist die Grundlage fuer reproduzierbare Tests und fuer
## einen Offline-Ertrag, den die Framerate nicht beeinflussen kann.
##
## NIEMALS `delta` direkt in eine Wirtschaftsrechnung geben (CLAUDE.md).
class_name SimClock
extends RefCounted

const TICK_DAUER: float = 0.25

## Gleitkomma-Toleranz beim Zaehlen der Ticks.
##
## Ohne sie entscheidet ein Rundungsfehler ueber einen ganzen Tick: Summiert man
## 120-mal 1/30 Sekunde, ergibt das 3.9999999999999996 statt 4.0, und
## int(3.9999999999999996 / 0.25) ist 15 statt 16. Der Spieler haette auf einem
## 30-fps-Geraet dauerhaft minimal weniger verdient als auf einem 120-fps-Geraet.
## Genau diesen Fall prueft test_takt_ist_unabhaengig_von_der_bildrate.
const TICK_EPSILON: float = 1e-9

## Offline-Parameter aus GAME_DESIGN.md 5.4.
var offline_rate: float = 0.5
var offline_obergrenze_sekunden: float = 4.0 * 3600.0

var _rest: float = 0.0
var _ticks_gesamt: int = 0


## Sammelt vergangene Zeit und gibt die Anzahl faelliger Ticks zurueck.
## Der Rest bleibt fuer den naechsten Aufruf erhalten -- so geht keine Zeit
## verloren und es entsteht keine, auch bei schwankender Bildrate.
func advance(delta: float) -> int:
	if delta <= 0.0:
		return 0
	_rest += delta
	var ticks: int = int((_rest + TICK_EPSILON) / TICK_DAUER)
	# Schutz gegen einen riesigen Sprung (App war im Hintergrund, Debugger-Pause):
	# mehr als 4 Sekunden am Stueck werden verworfen, dafuer gibt es die
	# Offline-Rechnung.
	if ticks > 16:
		ticks = 16
		_rest = 0.0
	else:
		_rest -= float(ticks) * TICK_DAUER
		# Das Epsilon kann den Rest minimal negativ machen -- abfangen,
		# damit sich kein Fehler in die Gegenrichtung aufbaut.
		if _rest < 0.0:
			_rest = 0.0
	_ticks_gesamt += ticks
	return ticks


func ticks_gesamt() -> int:
	return _ticks_gesamt


## Wie viele Sekunden werden von einer Abwesenheit tatsaechlich angerechnet?
## Gekappt auf die Obergrenze -- das ist keine Strafe, sondern der Grund
## zurueckzukommen (GAME_DESIGN.md 5.4).
func anrechenbare_offline_sekunden(abwesend_sekunden: float) -> float:
	if abwesend_sekunden <= 0.0:
		return 0.0
	return min(abwesend_sekunden, offline_obergrenze_sekunden)


## Ertrag fuer eine Abwesenheit.
## offline_ertrag = durchsatz * min(abwesend, obergrenze) * rate
func offline_ertrag(durchsatz_pro_sekunde: float, abwesend_sekunden: float) -> float:
	if durchsatz_pro_sekunde <= 0.0:
		return 0.0
	return durchsatz_pro_sekunde * anrechenbare_offline_sekunden(abwesend_sekunden) * offline_rate


## Berechnet die Abwesenheit aus zwei Zeitstempeln.
##
## Robust gegen zurueckgestellte Systemzeit: Eine negative Differenz ergibt 0
## statt eines negativen Ertrags. Vorstellen der Uhr laesst sich damit NICHT
## verhindern -- das waere nur mit einer Serverzeit moeglich und ist bei einem
## Offline-Einzelspieler den Aufwand nicht wert (ADR-006).
static func abwesenheit(letzter_zeitstempel: int, jetzt: int) -> float:
	if letzter_zeitstempel <= 0:
		return 0.0
	var differenz: int = jetzt - letzter_zeitstempel
	if differenz < 0:
		return 0.0
	return float(differenz)
