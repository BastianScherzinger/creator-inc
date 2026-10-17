## Kaeufe ohne Kasse -- der Stub.
##
## Er liest denselben Katalog wie spaeter das echte Billing und kennt dieselben
## Ausgaenge. Heute ist der Katalog absichtlich LEER: Es gibt nichts zu kaufen,
## und das Spiel muss das aushalten, ohne dass irgendwo ein Loch klafft.
##
## Der leere Laden ist keine halbe Arbeit, sondern der Test: Wenn die
## Oberflaeche mit null Produkten sauber aussieht, sieht sie mit drei Produkten
## erst recht sauber aus. Umgekehrt gilt das nicht.
class_name StoreServiceStub
extends StoreService

const PFAD: String = "res://data/services/store.json"

## Im Test einstellbar: Was soll der naechste Kauf zurueckgeben?
var naechstes_ergebnis: Ergebnis = Ergebnis.GEKAUFT

var _produkte: Array = []
var _besessen: Dictionary = {}


func _init() -> void:
	var daten: Dictionary = laden()
	_produkte = daten.get("produkte", []) as Array


static func laden(pfad: String = PFAD) -> Dictionary:
	if not FileAccess.file_exists(pfad):
		push_error("Katalog fehlt: %s" % pfad)
		return {}
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	return geparst as Dictionary if geparst is Dictionary else {}


func katalog() -> Array:
	var liste: Array = []
	for eintrag in _produkte:
		var produkt: Dictionary = (eintrag as Dictionary).duplicate()
		produkt["besessen"] = ist_besessen(StringName(String(produkt.get("id", ""))))
		liste.append(produkt)
	return liste


func ist_besessen(produkt_id: StringName) -> bool:
	return bool(_besessen.get(String(produkt_id), false))


func kaufen(produkt_id: StringName) -> void:
	if _finde(produkt_id).is_empty():
		kauf_beendet.emit(produkt_id, Ergebnis.FEHLGESCHLAGEN)
		return
	if ist_besessen(produkt_id):
		kauf_beendet.emit(produkt_id, Ergebnis.BEREITS_BESESSEN)
		return
	if naechstes_ergebnis == Ergebnis.GEKAUFT:
		_besessen[String(produkt_id)] = true
	kauf_beendet.emit(produkt_id, naechstes_ergebnis)


func wiederherstellen() -> void:
	# Der Stub hat nichts zu holen -- aber der Weg existiert und meldet sich,
	# damit die Oberflaeche ihn schon heute anfassen kann.
	wiederherstellung_beendet.emit(_besessen.size())


func _finde(produkt_id: StringName) -> Dictionary:
	for eintrag in _produkte:
		if String((eintrag as Dictionary).get("id", "")) == String(produkt_id):
			return eintrag as Dictionary
	return {}
