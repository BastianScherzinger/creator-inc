## Der Spielstand als reines Datenmodell -- ohne Dateizugriff.
##
## Trennung mit Absicht: Diese Klasse ist vollstaendig testbar, ohne dass
## irgendetwas auf die Platte geschrieben wird. Das Schreiben uebernimmt
## SaveManager.
##
## Versionierung ab Version 1 (ADR-006). Jede spaetere Schema-Aenderung
## bekommt eine eigene Migrationsfunktion und eine eingefrorene Fixture in
## tests/fixtures/saves/ -- nur so bleibt nachweisbar, dass alte Spielstaende
## auch nach Monaten noch laden.
class_name SaveData
extends RefCounted

## Aktuelle Schema-Version. Beim Erhoehen MUSS eine Migration ergaenzt werden.
const SCHEMA_VERSION: int = 5

var schema_version: int = SCHEMA_VERSION
var kapital: float = 0.0
var stationen: Dictionary = {}          ## String -> {stufe, freigeschaltet}
var unlocks: Array[String] = []
var letzter_zeitstempel: int = 0
var gesamt_verdient: float = 0.0
var spielzeit_sekunden: float = 0.0
var auftraege: Dictionary = {}

## Spielereinstellungen (Schema v2).
##
## Sie liegen im Spielstand und nicht in einer eigenen Datei, weil sie
## dieselbe Lebensdauer haben: Wer den Stand loescht, will auch wieder
## gefragt werden. Eine zweite Datei waere ein zweiter Ort, an dem etwas
## halb geschrieben sein kann.
##
## Der KERN liest sie nie -- er kennt keinen Ton. Gefuellt und ausgewertet
## werden sie in der Praesentation (ADR-004).
var einstellungen: Dictionary = {"ton": true}

## Stand des Tutorials (Schema v2).
##
## Er gehoert in den Spielstand und nicht in die Einstellungen: Ein Tutorial
## ist kein Wunsch des Spielers, sondern erreichter Fortschritt. Wer den Stand
## loescht, faengt auch die Einfuehrung neu an -- und das ist richtig so.
var tutorial: Dictionary = {"schritt": 0, "beendet": false}

## Laufender Belohnungsschub (Schema v2): Faktor und Restdauer in Sekunden.
var schub: Dictionary = {"faktor": 1.0, "rest": 0.0}

## In welcher Welt des Bogens steht der Spieler (Schema v2)?
var welt_index: int = 0

## Wie oft der ganze Bogen schon durchgespielt wurde (Schema v2).
var durchlaeufe: int = 0

## Abonnentenbestand (Schema v2, nur Welt 5).
var bestand: float = 0.0

## --- Schema v3: Welt in die Tiefe (ADR-021) ---

## In der aktuellen Welt verdient (fuer Ziele, die je Welt bei null anfangen).
var welt_verdient: float = 0.0

## Gekaufte Raeume (IDs).
var bereiche: Array[String] = []

## Eingeloeste Ziele (IDs).
var ziele: Array[String] = []

## Empfangene Nachrichten in Reihenfolge und wie viele davon gelesen sind.
var nachrichten: Dictionary = {"empfangen": [], "gelesen": 0}

## Tipp-Momente: nur der Zaehler. Eine gerade sichtbare Blase wird bewusst
## NICHT gespeichert -- sie gehoert zu dem Moment, in dem man hinsieht.
var momente: Dictionary = {"angetippt": 0}

## --- Schema v4: Belohnungen (Release-Plan 2026-10-14) ---

## Abgeholte Fortschrittsmarken der aktuellen Welt (IDs).
var marken: Array[String] = []

## Tagesgeschenk: zuletzt abgeholter Serientag (1..n) und Kalendertag (Tage seit 1970).
var tagesgeschenk: Dictionary = {"serientag": 0, "letzter_tag": 0}


## --- Schema v5: Crew, Tagesaufgaben, Erfolge, Level (Design-Overhaul 15.10.) ---

## Gekaufter Crew-Rang je Station (String -> int).
var crew: Dictionary = {}

## Tagesaufgaben: {tag, gewaehlt, stand, eingeloest}.
var tagesaufgaben: Dictionary = {}

## Zaehler ueber den ganzen Bogen (ziele, bereiche, welten, crew, aufgaben,
## momente). Leer = Stand aus der Zeit davor; der Kern leitet sie beim Laden ab.
var bogen: Dictionary = {}

## Erreichte Erfolge (IDs).
var erfolge: Array[String] = []

## Zufallswert dieser Installation (fuer die A/B-Zuteilung), 0 = noch nicht gewuerfelt.
var installations_wert: int = 0

## --- K5 (16.10.2026), optionale Felder in Schema v5 ---
## Beide fehlen in aelteren Staenden; from_dict setzt dann leere Werte. Keine
## Migration noetig: "leer" ist genau der richtige Stand fuer jemanden, der die
## Funktion nie gesehen hat.

## Antworten der Entscheidungs-Szenen: "<welt_id>/<kapitel_id>" -> 0|1 (nur Ton).
var entscheidungen: Dictionary = {}

## Einmal erklaerte Symbole (P1.9): IDs wie "kaufbar", "kiste". Fuellt die Darstellung.
var hinweise: Array[String] = []

## K6 (optional, Schema v5): die letzte Kameraansicht des Spielers -- {welt, zoom, x, z}.
## Leer = Erststart, dann gilt der Startblick der Welt. Der Kern rechnet damit nichts.
var kamera: Dictionary = {}


func to_dict() -> Dictionary:
	return {
		"schema_version": schema_version,
		"kapital": kapital,
		"stationen": stationen,
		"unlocks": unlocks,
		"letzter_zeitstempel": letzter_zeitstempel,
		"gesamt_verdient": gesamt_verdient,
		"spielzeit_sekunden": spielzeit_sekunden,
		"auftraege": auftraege,
		"einstellungen": einstellungen,
		"tutorial": tutorial,
		"schub": schub,
		"welt_index": welt_index,
		"durchlaeufe": durchlaeufe,
		"bestand": bestand,
		"welt_verdient": welt_verdient,
		"bereiche": bereiche,
		"ziele": ziele,
		"nachrichten": nachrichten,
		"momente": momente,
		"marken": marken,
		"tagesgeschenk": tagesgeschenk,
		"crew": crew,
		"tagesaufgaben": tagesaufgaben,
		"bogen": bogen,
		"erfolge": erfolge,
		"installations_wert": installations_wert,
		"entscheidungen": entscheidungen,
		"hinweise": hinweise,
		"kamera": kamera,
	}


static func from_dict(daten: Dictionary) -> SaveData:
	var s := SaveData.new()
	s.schema_version = int(daten.get("schema_version", 0))
	s.kapital = float(daten.get("kapital", 0.0))
	# Typen normalisieren: JSON liefert Zahlen immer als float zurueck, auch
	# wenn ein int gespeichert wurde. Ohne diesen Schritt wandert eine Stufe
	# als 7.0 durch das ganze System und taucht irgendwann als Fehler an einer
	# ganz anderen Stelle auf. Das Save-Modell garantiert die Typen.
	s.stationen = {}
	var roh_stationen: Dictionary = daten.get("stationen", {}) as Dictionary
	for schluessel in roh_stationen.keys():
		var eintrag: Dictionary = roh_stationen[schluessel] as Dictionary
		var plaetze: Dictionary = {}
		var roh_plaetze: Dictionary = eintrag.get("ausstattung", {}) as Dictionary
		for platz in roh_plaetze.keys():
			plaetze[String(platz)] = int(roh_plaetze[platz])
		s.stationen[String(schluessel)] = {
			"stufe": int(eintrag.get("stufe", 0)),
			"freigeschaltet": bool(eintrag.get("freigeschaltet", true)),
			"ausstattung": plaetze,
		}
	s.letzter_zeitstempel = int(daten.get("letzter_zeitstempel", 0))
	s.gesamt_verdient = float(daten.get("gesamt_verdient", 0.0))
	s.spielzeit_sekunden = float(daten.get("spielzeit_sekunden", 0.0))
	s.auftraege = daten.get("auftraege", {}) as Dictionary
	# Fehlende Einstellungen sind kein Fehler, sondern der Normalfall bei
	# einem Stand aus Schema v1. Der Standard ist "Ton an".
	var roh_einstellungen: Dictionary = daten.get("einstellungen", {}) as Dictionary
	s.einstellungen = {"ton": bool(roh_einstellungen.get("ton", true))}
	# Der Zoom-Hinweis (einmalig) ging hier bisher verloren und kam nach jedem Neustart wieder.
	if roh_einstellungen.has("zoom_hinweis"):
		s.einstellungen["zoom_hinweis"] = bool(roh_einstellungen["zoom_hinweis"])
	s.welt_index = int(daten.get("welt_index", 0))
	s.durchlaeufe = int(daten.get("durchlaeufe", 0))
	s.bestand = float(daten.get("bestand", 0.0))
	var roh_schub: Dictionary = daten.get("schub", {}) as Dictionary
	s.schub = {
		"faktor": float(roh_schub.get("faktor", 1.0)),
		"rest": float(roh_schub.get("rest", 0.0)),
	}
	var roh_tutorial: Dictionary = daten.get("tutorial", {}) as Dictionary
	s.tutorial = {
		"schritt": int(roh_tutorial.get("schritt", 0)),
		"beendet": bool(roh_tutorial.get("beendet", false)),
	}
	var roh_unlocks: Array = daten.get("unlocks", []) as Array
	s.unlocks.clear()
	for u in roh_unlocks:
		s.unlocks.append(String(u))
	s.welt_verdient = float(daten.get("welt_verdient", 0.0))
	s.bereiche.clear()
	for b in (daten.get("bereiche", []) as Array):
		s.bereiche.append(String(b))
	s.ziele.clear()
	for z in (daten.get("ziele", []) as Array):
		s.ziele.append(String(z))
	var roh_nachrichten: Dictionary = daten.get("nachrichten", {}) as Dictionary
	var empfangen: Array = []
	for n in (roh_nachrichten.get("empfangen", []) as Array):
		empfangen.append(String(n))
	s.nachrichten = {"empfangen": empfangen, "gelesen": int(roh_nachrichten.get("gelesen", 0))}
	var roh_momente: Dictionary = daten.get("momente", {}) as Dictionary
	s.momente = {"angetippt": int(roh_momente.get("angetippt", 0))}
	s.marken.clear()
	for m in (daten.get("marken", []) as Array):
		s.marken.append(String(m))
	var roh_geschenk: Dictionary = daten.get("tagesgeschenk", {}) as Dictionary
	s.tagesgeschenk = {
		"serientag": int(roh_geschenk.get("serientag", 0)),
		"letzter_tag": int(roh_geschenk.get("letzter_tag", 0)),
	}
	s.crew = {}
	var roh_crew: Dictionary = daten.get("crew", {}) as Dictionary
	for schluessel in roh_crew.keys():
		s.crew[String(schluessel)] = int(roh_crew[schluessel])
	var roh_aufgaben: Dictionary = daten.get("tagesaufgaben", {}) as Dictionary
	var gewaehlt: Array = []
	for g in (roh_aufgaben.get("gewaehlt", []) as Array):
		gewaehlt.append(String(g))
	var aufgaben_stand: Dictionary = {}
	var roh_aufgaben_stand: Dictionary = roh_aufgaben.get("stand", {}) as Dictionary
	for schluessel in roh_aufgaben_stand.keys():
		aufgaben_stand[String(schluessel)] = float(roh_aufgaben_stand[schluessel])
	var aufgaben_eingeloest: Array = []
	for e in (roh_aufgaben.get("eingeloest", []) as Array):
		aufgaben_eingeloest.append(String(e))
	s.tagesaufgaben = {
		"tag": int(roh_aufgaben.get("tag", 0)),
		"gewaehlt": gewaehlt,
		"stand": aufgaben_stand,
		"eingeloest": aufgaben_eingeloest,
	}
	s.bogen = {}
	var roh_bogen: Dictionary = daten.get("bogen", {}) as Dictionary
	for schluessel in roh_bogen.keys():
		s.bogen[String(schluessel)] = int(roh_bogen[schluessel])
	s.erfolge.clear()
	for e in (daten.get("erfolge", []) as Array):
		s.erfolge.append(String(e))
	s.installations_wert = int(daten.get("installations_wert", 0))
	s.entscheidungen = {}
	var roh_entscheidungen: Variant = daten.get("entscheidungen", {})
	if roh_entscheidungen is Dictionary:
		for schluessel in (roh_entscheidungen as Dictionary).keys():
			s.entscheidungen[String(schluessel)] = clampi(int((roh_entscheidungen as Dictionary)[schluessel]), 0, 1)
	s.hinweise.clear()
	var roh_hinweise: Variant = daten.get("hinweise", [])
	if roh_hinweise is Array:
		for h in (roh_hinweise as Array):
			s.hinweise.append(str(h))
	s.kamera = {}
	var roh_kamera: Variant = daten.get("kamera", {})
	if roh_kamera is Dictionary and (roh_kamera as Dictionary).has("zoom"):
		var k: Dictionary = roh_kamera as Dictionary
		s.kamera = {"welt": int(k.get("welt", -1)), "zoom": float(k["zoom"]),
			"x": float(k.get("x", 0.0)), "z": float(k.get("z", 0.0))}
	return s


## Pruefsumme ueber den Inhalt.
##
## Erkennt BESCHAEDIGUNG, nicht Manipulation -- wer die Datei bearbeitet, kann
## die Summe neu berechnen. Das ist bewusst so: Bei einem Offline-Einzelspieler
## ohne Ranglisten schadet Cheaten nur dem Spieler selbst, und echter Schutz
## waere unverhaeltnismaessiger Aufwand (ADR-006).
## WICHTIG -- die Normalisierung ist kein Zierrat:
## JSON kennt keinen Unterschied zwischen 7 und 7.0. Beim Speichern steht im
## Dictionary ein int, nach dem Laden ein float. Wuerde man die Summe direkt
## ueber das Dictionary bilden, waere sie vor und nach dem Roundtrip
## verschieden -- jeder gespeicherte Stand gaelte beim naechsten Start als
## beschaedigt. Deshalb wird immer ueber die durch JSON gegangene Fassung
## gerechnet.
static func pruefsumme(daten: Dictionary) -> String:
	var kopie: Dictionary = daten.duplicate(true)
	kopie.erase("_pruefsumme")
	var text: String = JSON.stringify(kopie, "", true, true)
	var normalisiert: Variant = JSON.parse_string(text)
	if normalisiert == null:
		return text.sha256_text()
	return JSON.stringify(normalisiert, "", true, true).sha256_text()


## Hebt einen Spielstand auf die aktuelle Schema-Version.
##
## Die Kette laeuft Schritt fuer Schritt (v1 -> v2 -> v3), damit jeder Sprung
## einzeln testbar bleibt. Gibt false zurueck, wenn der Stand aus einer
## NEUEREN Version stammt -- dann wurde die App heruntergestuft, und Raten
## waere schlimmer als ein sauberer Abbruch.
static func migrieren(daten: Dictionary) -> Dictionary:
	var version: int = int(daten.get("schema_version", 0))

	if version > SCHEMA_VERSION:
		push_error("Spielstand hat Version %d, App kennt nur %d" % [version, SCHEMA_VERSION])
		return {}

	# Version 0 = ein Stand aus der Zeit vor der Versionierung.
	if version == 0:
		daten = _migriere_v0_zu_v1(daten)
		version = 1

	if version == 1:
		daten = _migriere_v1_zu_v2(daten)
		version = 2

	if version == 2:
		daten = _migriere_v2_zu_v3(daten)
		version = 3

	if version == 3:
		daten = _migriere_v3_zu_v4(daten)
		version = 4

	if version == 4:
		daten = _migriere_v4_zu_v5(daten)
		version = 5

	# Kuenftige Migrationen hier anhaengen.

	daten["schema_version"] = version
	return daten


static func _migriere_v0_zu_v1(daten: Dictionary) -> Dictionary:
	var neu: Dictionary = daten.duplicate(true)
	# Felder, die es in v0 noch nicht gab, mit sinnvollen Werten belegen
	if not neu.has("gesamt_verdient"):
		neu["gesamt_verdient"] = neu.get("kapital", 0.0)
	if not neu.has("spielzeit_sekunden"):
		neu["spielzeit_sekunden"] = 0.0
	if not neu.has("unlocks"):
		neu["unlocks"] = []
	if not neu.has("auftraege"):
		neu["auftraege"] = {}
	neu["schema_version"] = 1
	return neu


## v1 -> v2: Spielereinstellungen und Tutorialstand kamen hinzu.
##
## Beide in EINEM Schritt, weil Version 2 nie ausgeliefert wurde -- es gibt
## keinen Spielstand da draussen, der das eine kennt und das andere nicht.
## Ein zweiter Migrationsschritt haette Geschichte erfunden, die es nicht gab.
##
## Der Sprung ist klein, die Uebung ist es nicht: Es ist die erste echte
## Migration des Projekts, und ihre eingefrorene Fixture in
## tests/fixtures/saves/save_v1.json ist der Nachweis, dass die Kette
## funktioniert. Ohne diesen Nachweis waere ADR-006 eine Absichtserklaerung.
##
## Der Standard ist bewusst "Ton an": Wer seit Wochen ohne Ton spielt, hat
## das nie entschieden -- es gab die Einstellung nicht. Stumm zu starten
## waere eine Entscheidung, die ihm hier untergeschoben wuerde.
static func _migriere_v1_zu_v2(daten: Dictionary) -> Dictionary:
	var neu: Dictionary = daten.duplicate(true)
	if not neu.has("einstellungen"):
		neu["einstellungen"] = {"ton": true}
	# Ein Stand aus v1 stammt von jemandem, der laengst spielt. Ihm jetzt das
	# Tutorial vorzusetzen waere eine Belehrung, keine Einfuehrung -- deshalb
	# gilt es als beendet.
	if not neu.has("tutorial"):
		neu["tutorial"] = {"schritt": 0, "beendet": true}
	if not neu.has("schub"):
		neu["schub"] = {"faktor": 1.0, "rest": 0.0}
	if not neu.has("welt_index"):
		neu["welt_index"] = 0
	if not neu.has("durchlaeufe"):
		neu["durchlaeufe"] = 0
	if not neu.has("bestand"):
		neu["bestand"] = 0.0
	neu["schema_version"] = 2
	return neu


## v2 -> v3: Ausstattung, Raeume, Ziele, Nachrichten, Tipp-Momente (ADR-021).
##
## Die Migration setzt nur LEERE Werte. Was ein alter Stand in der neuen Welt
## bedeutet (Upload schon frei -> Flur gilt als gekauft), entscheidet der Kern
## beim Laden -- nur er kennt die Balance-Daten. Eine Migration, die Spielregeln
## kennt, muesste bei jeder Balance-Aenderung mitgeaendert werden.
##
## Nachrichten gelten als GELESEN: Wer aus v2 kommt, soll nicht mit einem
## roten Abzeichen fuer eine Geschichte begruesst werden, die er nie verpasst hat.
static func _migriere_v2_zu_v3(daten: Dictionary) -> Dictionary:
	var neu: Dictionary = daten.duplicate(true)
	if not neu.has("welt_verdient"):
		neu["welt_verdient"] = 0.0
	if not neu.has("bereiche"):
		neu["bereiche"] = []
	if not neu.has("ziele"):
		neu["ziele"] = []
	if not neu.has("nachrichten"):
		neu["nachrichten"] = {"empfangen": [], "gelesen": 0}
	if not neu.has("momente"):
		neu["momente"] = {"angetippt": 0}
	neu["schema_version"] = 3
	return neu


## v3 -> v4: Fortschrittsmarken und Tagesgeschenk.
##
## Nur leere Werte. Ein alter Stand hat nie eine Marke abgeholt und nie ein
## Geschenk bekommen: Das erste Geschenk ist sofort faellig (Serientag 1), und
## Marken, die der Stand schon uebersprungen hat, sind abholbar -- sie wurden
## ihm ja nie angeboten.
static func _migriere_v3_zu_v4(daten: Dictionary) -> Dictionary:
	var neu: Dictionary = daten.duplicate(true)
	if not neu.has("marken"):
		neu["marken"] = []
	if not neu.has("tagesgeschenk"):
		neu["tagesgeschenk"] = {"serientag": 0, "letzter_tag": 0}
	neu["schema_version"] = 4
	return neu


## v4 -> v5: Crew, Tagesaufgaben, Erfolge, Bogen-Zaehler, Installationswert.
##
## Nur leere Werte. Die Zaehler ueber den Bogen (eingeloeste Ziele, gekaufte
## Raeume, fertige Welten) kann nur der Kern ableiten -- er kennt die Balance
## der frueheren Welten. Ein leeres `bogen` heisst deshalb "bitte beim Laden
## herleiten", nicht "null". Erfolge, die der Stand schon verdient hat, werden
## dort ebenfalls still nachgetragen und nicht als Moment gefeiert.
static func _migriere_v4_zu_v5(daten: Dictionary) -> Dictionary:
	var neu: Dictionary = daten.duplicate(true)
	if not neu.has("crew"):
		neu["crew"] = {}
	if not neu.has("tagesaufgaben"):
		neu["tagesaufgaben"] = {}
	if not neu.has("bogen"):
		neu["bogen"] = {}
	if not neu.has("erfolge"):
		neu["erfolge"] = []
	if not neu.has("installations_wert"):
		neu["installations_wert"] = 0
	neu["schema_version"] = 5
	return neu
