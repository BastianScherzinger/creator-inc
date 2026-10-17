## Spielt Klaenge ab. Die Entscheidung, ob gespielt wird, faellt in AudioRegeln.
##
## Diese Trennung ist dieselbe wie zwischen core/ und game/, eine Ebene tiefer:
## Hier liegt alles, was Hardware und Engine braucht, dort alles, was man
## pruefen will.
##
## Der Director haengt am EventBus des Kerns und uebersetzt Ereignisse in
## Klaenge. Der Kern weiss davon nichts -- er wuerde auch stumm laufen.
class_name AudioDirector
extends Node

## Eigener Bus, damit sich alles Hoerbare mit einem Griff stummschalten laesst
## und spaeter Musik danebenpasst, ohne dass hier etwas umgebaut wird.
const BUS_EFFEKTE: String = "Effekte"

## Wie viele Klaenge duerfen gleichzeitig laufen?
##
## Acht ist reichlich fuer ein Spiel, in dem ein einzelner Tipp der Normalfall
## ist. Der Grund fuer eine feste Zahl ist ein anderer: Ohne Obergrenze legt
## ein Fehler in der Ereignisverdrahtung hunderte Player an, und die App
## stirbt an einer Stelle, die mit Klang nichts zu tun hat.
const STIMMEN: int = 8

const KLANG_ORDNER: String = "res://assets/audio/%s.wav"

var regeln: AudioRegeln

var _stimmen: Array[AudioStreamPlayer] = []
var _naechste: int = 0
var _klaenge: Dictionary = {}          ## String -> AudioStream
var _zeit: float = 0.0


func _ready() -> void:
	regeln = AudioRegeln.new()
	_richte_bus_ein()
	_lade_klaenge()

	for i in range(STIMMEN):
		var spieler := AudioStreamPlayer.new()
		spieler.bus = BUS_EFFEKTE
		add_child(spieler)
		_stimmen.append(spieler)


func _process(delta: float) -> void:
	# Eigene Uhr statt Time.get_ticks_msec(): Die Sperren sollen sich auf
	# SPIELZEIT beziehen. Bei angehaltener App laeuft hier nichts weiter, und
	# ein Klang, der vor dem Pausieren gesperrt war, ist nach der Rueckkehr
	# nicht ploetzlich wieder frei.
	_zeit += delta


## Der einzige Weg nach draussen. `kennzahl` ist ereignisabhaengig --
## beim Ausbau die neue Stufe.
func spiele(ereignis: StringName, kennzahl: int = 0) -> void:
	var wahl: Dictionary = regeln.entscheide(ereignis, _zeit, kennzahl)
	if wahl.is_empty():
		return
	var stream: AudioStream = _klaenge.get(String(wahl["klang"])) as AudioStream
	if stream == null:
		return

	var spieler: AudioStreamPlayer = _stimmen[_naechste]
	_naechste = (_naechste + 1) % _stimmen.size()
	spieler.stream = stream
	spieler.volume_db = float(wahl["lautstaerke_db"])
	spieler.pitch_scale = float(wahl["tonhoehe"])
	spieler.play()


## Ton an oder aus. Wirkt sofort und schaltet zusaetzlich den Bus stumm,
## damit auch bereits laufende Klaenge verstummen.
func setze_ton(an: bool) -> void:
	regeln.ton_an = an
	var index: int = AudioServer.get_bus_index(BUS_EFFEKTE)
	if index >= 0:
		AudioServer.set_bus_mute(index, not an)


func ton_an() -> bool:
	return regeln != null and regeln.ton_an


## Haengt den Director an den Kern.
##
## Die Zuordnung steht hier und nicht in main.gd, weil sie vollstaendig ist:
## Wer wissen will, was das Spiel wann von sich gibt, liest diese Funktion.
func verbinde(bus: EventBus) -> void:
	bus.station_upgraded.connect(func(_id: StringName, stufe: int) -> void:
		spiele(&"ausbau", stufe))
	bus.milestone_reached.connect(func(_id: StringName) -> void:
		spiele(&"meilenstein"))
	bus.unlocked.connect(func(_id: StringName) -> void:
		spiele(&"freischaltung"))
	bus.special_order_available.connect(func(_id: StringName, _bonus: float) -> void:
		spiele(&"auftrag_bereit"))
	bus.special_order_completed.connect(func(_id: StringName, _erloes: float) -> void:
		spiele(&"auftrag_fertig"))
	bus.bottleneck_changed.connect(func(_id: StringName) -> void:
		spiele(&"hinweis"))

	# BEWUSST NICHT VERBUNDEN: money_changed und throughput_tick.
	# Beide feuern viermal pro Sekunde, dauerhaft, ohne dass der Spieler etwas
	# getan haette. Ein Klang darauf waere nach zwei Minuten der Grund, warum
	# jemand den Ton abschaltet -- und danach hoert er auch die Klaenge nicht
	# mehr, die etwas bedeuten.


func _richte_bus_ein() -> void:
	if AudioServer.get_bus_index(BUS_EFFEKTE) >= 0:
		return
	var index: int = AudioServer.bus_count
	AudioServer.add_bus(index)
	AudioServer.set_bus_name(index, BUS_EFFEKTE)
	AudioServer.set_bus_send(index, "Master")


func _lade_klaenge() -> void:
	for name in regeln.benoetigte_klaenge():
		var pfad: String = KLANG_ORDNER % name
		if not ResourceLoader.exists(pfad):
			push_warning("Klang fehlt: %s" % pfad)
			continue
		_klaenge[name] = load(pfad) as AudioStream
