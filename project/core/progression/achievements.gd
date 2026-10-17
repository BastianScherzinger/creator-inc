## Erfolge ueber den ganzen Bogen und der Firmen-Rang des Spielers (Design-Overhaul 15.10., K2 P2a).
##
## Erfolge sind Abzeichen; ihr `bonus` ist 0 -- der Dauerfaktor kommt aus dem Rang. Das System kennt nur Definitionen und die Menge der
## erreichten IDs; gemessen wird im Kern (welcher Wert zu welchem Typ gehoert).
class_name Achievements
extends RefCounted

const PFAD: String = "res://data/balance/erfolge.json"

## Firmen-Rang (K2 P2a): Punkte -> Rang ueber Schwellen aus erfolge.json.
## Rang 1 gilt ab 0 Punkten; `schwellen[n - 1]` ist die Punktzahl fuer Rang n.
var level_max: int = 30
var punkte_gewicht: Dictionary = {"ziel": 1, "bereich": 3, "mission": 5, "welt_fertig": 10}
var schwellen: Array[int] = [0]
var bonus_je_rang: float = 0.0
var bonus_ab_rang: int = 2
var _freischaltung: Dictionary = {}   ## Rang (int) -> Array[String] Merkmale
var _merkmal_rang: Dictionary = {}    ## Merkmal -> Rang, ab dem es frei ist
var _offline_sekunden: Dictionary = {}  ## Merkmal (offline_6h ...) -> Obergrenze des Offline-Ertrags in Sekunden

var _definitionen: Array = []
var _erreicht: Dictionary = {}   ## id -> true


func _init(daten: Dictionary = {}) -> void:
	var roh: Dictionary = daten if not daten.is_empty() else lade_roh()
	_definitionen = roh.get("erfolge", []) as Array
	_lade_rang(roh.get("rang", {}) as Dictionary)


func _lade_rang(rang: Dictionary) -> void:
	if rang.is_empty():
		return
	var gewicht: Dictionary = rang.get("punkte", {}) as Dictionary
	for schluessel in punkte_gewicht.keys():
		punkte_gewicht[schluessel] = int(gewicht.get(schluessel, punkte_gewicht[schluessel]))
	schwellen = []
	for wert in (rang.get("schwellen", [0]) as Array):
		schwellen.append(int(wert))
	if schwellen.is_empty():
		schwellen = [0]
	level_max = schwellen.size()
	bonus_je_rang = float(rang.get("bonus_je_rang", 0.0))
	bonus_ab_rang = maxi(int(rang.get("bonus_ab_rang", 2)), 1)
	var offline: Dictionary = rang.get("offline_sekunden", {}) as Dictionary
	for schluessel in offline.keys():
		_offline_sekunden[String(schluessel)] = float(offline[schluessel])
	var frei: Dictionary = rang.get("freischaltung", {}) as Dictionary
	for schluessel in frei.keys():
		var n: int = int(String(schluessel))
		var merkmale: Array = []
		for m in (frei[schluessel] as Array):
			merkmale.append(String(m))
			if not _merkmal_rang.has(String(m)):
				_merkmal_rang[String(m)] = n
		_freischaltung[n] = merkmale


static func lade_roh() -> Dictionary:
	if not FileAccess.file_exists(PFAD):
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(PFAD))
	return roh as Dictionary if roh is Dictionary else {}


func definitionen() -> Array:
	return _definitionen


func ist_erreicht(erfolg_id: String) -> bool:
	return _erreicht.has(erfolg_id)


func anzahl_erreicht() -> int:
	return _erreicht.size()


## Setzt einen Erfolg. Gibt true zurueck, wenn er NEU war.
func erreiche(erfolg_id: String) -> bool:
	if _erreicht.has(erfolg_id):
		return false
	_erreicht[erfolg_id] = true
	return true


## 1.0 + Summe der Boni aller erreichten Erfolge.
func faktor() -> float:
	var f: float = 1.0
	for d in _definitionen:
		var eintrag: Dictionary = d as Dictionary
		if _erreicht.has(String(eintrag.get("id", ""))):
			f += float(eintrag.get("bonus", 0.0))
	return f


## Punkte eines eingeloesten Ziels: Mission (kette "welt") 5, Raumziel
## (typ "bereich") 3, sonst 1. Werte aus den Daten.
func ziel_punkte(ziel: Dictionary) -> int:
	if String(ziel.get("kette", "")) == "welt":
		return int(punkte_gewicht["mission"])
	if String(ziel.get("typ", "")) == "bereich":
		return int(punkte_gewicht["bereich"])
	return int(punkte_gewicht["ziel"])


func welt_fertig_punkte() -> int:
	return int(punkte_gewicht["welt_fertig"])


## Rang (1 ... level_max) aus den gesammelten Punkten.
func rang(punkte: int) -> int:
	var r: int = 1
	for i in range(schwellen.size()):
		if punkte >= schwellen[i]:
			r = i + 1
	return clampi(r, 1, level_max)


## Punkte, ab denen der naechste Rang gilt; -1 beim hoechsten Rang.
func naechste_schwelle(rang_jetzt: int) -> int:
	if rang_jetzt >= level_max:
		return -1
	return schwellen[rang_jetzt]


func schwelle(rang_nr: int) -> int:
	return schwellen[clampi(rang_nr, 1, level_max) - 1]


## Merkmale, die genau mit diesem Rang frei werden.
func freischaltung_bei(rang_nr: int) -> Array:
	return (_freischaltung.get(rang_nr, []) as Array).duplicate()


## Ab welchem Rang ein Merkmal frei ist. Unbekannte Merkmale sind von Anfang an
## frei (1) -- nur was in erfolge.json steht, wird gesperrt.
func merkmal_rang(merkmal: String) -> int:
	return int(_merkmal_rang.get(merkmal, 1))


func ist_frei(merkmal: String, rang_jetzt: int) -> bool:
	return rang_jetzt >= merkmal_rang(merkmal)


## Obergrenze des Offline-Ertrags (Sekunden) bei diesem Rang: die groesste Grenze unter den
## freien Merkmalen `offline_*`, mindestens `basis` (K2 4.1: 4 -> 6 -> 8 -> 12 h).
func offline_obergrenze(rang_jetzt: int, basis: float) -> float:
	var grenze: float = basis
	for merkmal in _offline_sekunden.keys():
		if ist_frei(String(merkmal), rang_jetzt):
			grenze = maxf(grenze, float(_offline_sekunden[merkmal]))
	return grenze


## Dauerhafter Einkommensfaktor des Rangs: +bonus_je_rang je Rang ab bonus_ab_rang.
func rang_faktor(rang_jetzt: int) -> float:
	return 1.0 + bonus_je_rang * float(maxi(rang_jetzt - bonus_ab_rang + 1, 0))


func to_array() -> Array[String]:
	var liste: Array[String] = []
	for schluessel in _erreicht.keys():
		liste.append(String(schluessel))
	return liste


func apply_array(liste: Array) -> void:
	_erreicht.clear()
	for eintrag in liste:
		_erreicht[String(eintrag)] = true
