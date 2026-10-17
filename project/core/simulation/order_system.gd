## Der Grossauftrag -- der Daily-Return-Anker (GAME_DESIGN.md 8).
##
## Alle paar Stunden steht ein Sonderfall bereit. Er WARTET, bis der Spieler
## kommt: kein Verfall, keine Strafe, kein Countdown. Ein Spiel, das bestraft,
## wenn man lebt, wird deinstalliert.
##
## Bis zu zwei koennen sich stapeln -- wer zwoelf Stunden weg war, findet
## zwei vor. Das ist ein Willkommensbonus, aber keine Farm: Mehr sammeln sich
## nie an, egal wie lange man wegbleibt.
class_name OrderSystem
extends RefCounted

const MAX_WARTEND: int = 2

var intervall_sekunden: float = 4.0 * 3600.0
var bonus_faktor: float = 2.0

var wartend: int = 0
var _seit_letztem: float = 0.0


## Laesst Zeit vergehen. Gibt zurueck, wie viele Auftraege NEU dazugekommen sind.
func tick(sekunden: float, bus: EventBus = null) -> int:
	if sekunden <= 0.0:
		return 0
	_seit_letztem += sekunden
	var neu: int = 0
	while _seit_letztem >= intervall_sekunden and wartend < MAX_WARTEND:
		_seit_letztem -= intervall_sekunden
		wartend += 1
		neu += 1
		if bus != null:
			bus.special_order_available.emit(&"order_standard", bonus_faktor)
	# Ist das Maximum erreicht, laeuft die Uhr nicht weiter voll --
	# sonst haette man nach einer Woche Abwesenheit einen Schwall.
	if wartend >= MAX_WARTEND:
		_seit_letztem = minf(_seit_letztem, intervall_sekunden)
	return neu


## Loest einen wartenden Auftrag ein. Gibt den Erloes zurueck (0 = keiner da).
##
## Der Bonus haengt am aktuellen Einkommen, nicht an einer festen Zahl --
## so bleibt der Grossauftrag ueber die gesamte Progression relevant und
## fuehlt sich auch nach Stunden noch nach etwas an.
func einloesen(einkommen_pro_sekunde: float, bus: EventBus = null) -> float:
	if wartend <= 0:
		return 0.0
	wartend -= 1
	# Gegenwert von rund einer Viertelstunde Arbeit, mal Bonus
	var erloes: float = einkommen_pro_sekunde * 900.0 * bonus_faktor
	if bus != null:
		bus.special_order_completed.emit(&"order_standard", erloes)
	return erloes


func to_dict() -> Dictionary:
	return {"wartend": wartend, "seit_letztem": _seit_letztem}


func apply_dict(daten: Dictionary) -> void:
	wartend = clampi(int(daten.get("wartend", 0)), 0, MAX_WARTEND)
	_seit_letztem = float(daten.get("seit_letztem", 0.0))
