## Kapitel einer Welt (K5, docs/STORY.md "Business-Aufbau-Story").
##
## Reines Datenmodell ohne Texte-Wissen: Die Liste kommt als neutrale Daten
## herein (Eintraege mit id, titel, ab_bereich, aufgabe, entscheidung -- aus der
## Themendatei, gelesen von der Darstellung). Der Kern rechnet nur, WELCHES
## Kapitel gerade laeuft: das letzte, dessen `ab_bereich` gekauft ist; leer
## heisst "ab Spielbeginn".
##
## Die Antworten der Entscheidungs-Szenen merkt sich GameCore.entscheidungen.
## Sie aendern nie die Wirtschaft -- nur den Ton (Rueckblick im Handy).
class_name KapitelSystem
extends RefCounted

var _liste: Array[Dictionary] = []


func _init(liste: Array = []) -> void:
	for e in liste:
		if e is Dictionary and not String((e as Dictionary).get("id", "")).is_empty():
			_liste.append((e as Dictionary).duplicate())


func anzahl() -> int:
	return _liste.size()


func hat_kapitel() -> bool:
	return not _liste.is_empty()


## Eintrag i (0-basiert) oder leer.
func eintrag(index: int) -> Dictionary:
	if index < 0 or index >= _liste.size():
		return {}
	return _liste[index]


## Das laufende Kapitel (0-basiert); -1 ohne Kapiteldaten.
## `gekauft` sind die IDs der gekauften Raeume.
func index_fuer(gekauft: Array) -> int:
	var aktuell: int = -1
	for i in _liste.size():
		var ab: String = String(_liste[i].get("ab_bereich", ""))
		if ab.is_empty() or gekauft.has(ab) or gekauft.has(StringName(ab)):
			aktuell = i
	return aktuell


## Das Kapitel, dessen Entscheidung diese Nachricht traegt ("" = keine Entscheidung).
func kapitel_der_entscheidung(nachricht_id: String) -> String:
	for e in _liste:
		if String(e.get("entscheidung", "")) == nachricht_id and not nachricht_id.is_empty():
			return String(e.get("id", ""))
	return ""


## Ein Kapitelwechsel durch einen Kauf: neues Kapitel (0-basiert) oder -1.
## Nur vorwaerts -- ein Kapitel zaehlt nie zurueck.
static func wechsel(vorher: int, nachher: int) -> int:
	return nachher if nachher > vorher and nachher >= 0 else -1
