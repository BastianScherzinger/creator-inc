## Verwaltet die sichtbaren NPCs und die Warteschlange.
##
## Object Pooling ab dem ersten Tag (ADR-007): Alle Figuren werden einmal
## erzeugt und danach nur noch ein- und ausgeblendet. Waehrend des Spiels
## Nodes zu instanziieren erzeugt Speicherzuweisungen und damit Ruckler --
## sichtbar genau dann, wenn viel los ist.
##
## Die Warteschlange IST das Engpass-Signal aus GAME_DESIGN.md 2: Wenn die
## Annahme nicht hinterherkommt, wird die Schlange sichtbar laenger.
class_name NpcPool
extends Node3D

const NpcSkript := preload("res://game/npc/npc_view.gd")

## Obergrenze laut ARCHITECTURE.md 4. Mehr Figuren bringen keine zusaetzliche
## Information -- eine Schlange aus 24 Wartenden liest sich genauso wie eine
## aus 60, kostet aber ein Vielfaches.
const MAX_SICHTBAR: int = 24

## Die Schlange laeuft schraeg nach vorn statt gerade zur Seite -- sonst
## verlaesst sie bei mehr als sechs Wartenden das Bild. Ab SCHLANGE_UMBRUCH
## beginnt eine zweite Reihe daneben; so bleibt auch eine lange Schlange
## im Bild und trotzdem als Stau lesbar.
## Abstand an der Figurbreite ausgerichtet (0,42 Einheiten Schulterbreite).
## Enger gestellt ueberlappen die Silhouetten und die Schlange wird zum Klumpen
## -- sie soll aber als REIHE lesbar sein, sonst verliert sie ihre Aussage.
const SCHLANGE_ABSTAND: float = 0.88
const SCHLANGE_RICHTUNG := Vector3(-0.42, 0.0, 0.91)
const SCHLANGE_VERSATZ := Vector3(-0.91, 0.0, -0.42)
const SCHLANGE_UMBRUCH: int = 5

var _alle: Array[NpcView] = []
var _frei: Array[NpcView] = []
var _schlange: Array[NpcView] = []

var _eingang: Vector3 = Vector3.ZERO
var _ausgang: Vector3 = Vector3.ZERO
var _schalter: Vector3 = Vector3.ZERO

## Wie verhalten sich die Figuren in dieser Welt?
##
## "kunden"    -- sie kommen, stellen sich an und werden bedient (Welt 2 aufwaerts)
## "zuschauer" -- die meisten schauen kurz zu und gehen wieder (Welt 1)
##
## Der Unterschied ist keine Verhaltensvariante, sondern eine Aussage: In der
## ersten Welt hat man Reichweite und sonst nichts. Wer vorbeikommt, bleibt
## meistens nicht. Genau das soll man sehen, bevor es irgendwo steht.
var modus: String = "kunden"

## Anteil derer, die tatsaechlich bleiben. Aus den Weltdaten, nicht geraten.
var bleibt_anteil: float = 1.0
var verweildauer: float = 1.6

## Die Raummitte ist der Bezugspunkt der Zuschauer -- nicht die Station.
## Von der Station aus gerechnet landen sie zwangslaeufig wieder auf der Kette.
var _raummitte: Vector3 = Vector3.ZERO
var _zufall := RandomNumberGenerator.new()


func aufbauen(eingang: Vector3, ausgang: Vector3, schalter: Vector3,
		figuren: Dictionary = {}) -> void:
	_eingang = eingang
	_ausgang = ausgang
	_schalter = schalter
	_zufall.randomize()
	modus = String(figuren.get("modus", modus))
	bleibt_anteil = clampf(float(figuren.get("bleibt_anteil", bleibt_anteil)), 0.0, 1.0)
	verweildauer = float(figuren.get("verweildauer", verweildauer))
	for i in range(MAX_SICHTBAR):
		var npc: NpcView = NpcSkript.new()
		add_child(npc)
		_alle.append(npc)
		_frei.append(npc)


## Laesst eine Figur erscheinen, sofern der Pool noch etwas hergibt.
## Gibt false zurueck, wenn die Obergrenze erreicht ist -- das ist kein Fehler,
## sondern die gewollte Begrenzung.
func lass_erscheinen() -> bool:
	if _frei.is_empty():
		return false
	var npc: NpcView = _frei.pop_back()

	# Zuschauer, die nicht bleiben: Sie laufen zu einem Punkt neben dem
	# Geschehen, schauen kurz und gehen wieder. Sie kommen NICHT in die
	# Schlange -- sonst waere die Schlange kein Engpass-Signal mehr, sondern
	# nur noch eine Anwesenheitsliste.
	if modus == "zuschauer" and _zufall.randf() > bleibt_anteil:
		npc.aktiviere(_eingang, _zuschauerplatz(), _auf_abgang)
		npc.schau_vorbei(_zuschauerplatz(), verweildauer, _ausgang)
		return true

	var platz: Vector3 = _schlangenplatz(_schlange.size())
	npc.aktiviere(_eingang, platz, _auf_abgang)
	_schlange.append(npc)
	return true


## Fertigt die vorderste Figur ab. Alle anderen ruecken auf.
func fertige_vorderste_ab() -> bool:
	if _schlange.is_empty():
		return false
	var vorne: NpcView = _schlange.pop_front()
	vorne.fertige_ab(_ausgang)
	for i in range(_schlange.size()):
		_schlange[i].ruecke_auf(_schlangenplatz(i))
	return true


## Wie viele stehen tatsaechlich an?
##
## Zuschauer zaehlen hier NICHT mit. Sie stehen in keiner Schlange, und die
## Schlange ist das Engpass-Signal des Spiels -- wuerde blosse Anwesenheit
## mitzaehlen, waere sie eine Anwesenheitsliste statt einer Aussage.
func warten_anzahl() -> int:
	return _schlange.size()


func ist_voll() -> bool:
	return _frei.is_empty()


## Ein Platz mit Blick auf das Geschehen, aber nicht darauf.
##
## NEBEN der Kette, nicht davor und nicht rundherum.
##
## Zwei Anlaeufe waren falsch, und beide aus demselben Grund: Die Kette liegt
## auf der Weltdiagonalen (1,0,1), weil sie im Bild senkrecht verlaeuft und
## das Hochformat nur dort Platz hat. "Rundherum" setzte damit die Haelfte der
## Figuren AUF die Stationen, und "davor" verschob sie die Kette entlang --
## also wieder darauf. Ein Publikum, das die Buehne verdeckt, ist keins.
##
## Frei ist der Raum QUER zur Kette: die Richtung (1,0,-1), im Bild waagerecht.
## Dort stehen sie, links und rechts, leicht nach vorn versetzt.
##
## Gestreut statt auf einem Punkt: Zwoelf Figuren, die dieselbe Stelle
## anlaufen, sehen aus wie ein Fehler. Gestreut sehen sie aus wie Publikum.
func _zuschauerplatz() -> Vector3:
	var quer := Vector3(1.0, 0.0, -1.0).normalized()
	var vorn := Vector3(1.0, 0.0, 1.0).normalized()
	var seite: float = 2.2 + _zufall.randf() * 1.9
	if _zufall.randf() < 0.5:
		seite = -seite
	var tiefe: float = 0.4 + _zufall.randf() * 2.4
	return _raummitte + quer * seite + vorn * tiefe


func _schlangenplatz(index: int) -> Vector3:
	var reihe: int = index / SCHLANGE_UMBRUCH
	var platz_in_reihe: int = index % SCHLANGE_UMBRUCH
	return (_schalter
		# Abstand 2,2 statt 1,0: Bei 1,0 stand die Schlange MITTEN auf der
		# Station und verdeckte sie vollstaendig. Die Wartenden gehoeren
		# daneben -- sonst sieht man den Ausbau nicht, fuer den man bezahlt hat.
		+ SCHLANGE_RICHTUNG * (2.2 + float(platz_in_reihe) * SCHLANGE_ABSTAND)
		+ SCHLANGE_VERSATZ * (float(reihe) * 0.95))


func _auf_abgang(npc: NpcView) -> void:
	# Auch aus der Schlange nehmen: Ein Zuschauer steht nie darin, aber ein
	# Kunde, der ueber einen anderen Weg abgeht, wuerde die Schlange sonst
	# fuer immer belegen.
	_schlange.erase(npc)
	if not _frei.has(npc):
		_frei.append(npc)
