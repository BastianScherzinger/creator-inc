## Laedt und prueft die Balance-Werte aus data/balance/*.json.
##
## Der Validator ist wichtiger als der Loader: Ein Tippfehler in einer JSON --
## eine fehlende Station, ein Wachstum von 0.9, ein negativer Preis -- wuerde
## sich sonst als merkwuerdiges Spielverhalten aeussern statt als Fehlermeldung.
## Hier bricht er sofort und benennt das Feld.
class_name BalanceData
extends RefCounted

## Eine Balancedatei JE WELT. Der Dateiname ist die Welt-ID.
##
## Vorher lag genau eine Datei unter einem festen Pfad. Bei sechs Welten waere
## das entweder eine Datei mit sechs Abschnitten geworden (unuebersichtlich und
## bei jeder Aenderung ein Konflikt) oder ein Pfad im Code je Welt. Beides ist
## schlechter als ein Muster.
const PFAD_MUSTER: String = "res://data/balance/%s.json"

## Die erste Welt des Bogens. Wer ohne Angabe laedt, bekommt sie -- Tests und
## der Balance-Simulator sollen nicht wissen muessen, wo der Bogen anfaengt.
const STANDARD_WELT: String = "zimmer"

## Balance-Overlay fuer A/B-Vergleiche (U4, Design-Overhaul 15.10.).
##
## Ist `variante` gesetzt (z. B. "b"), liegt `data/balance/experimente/<welt>_b.json`
## tief ueber dem Original. Leer = Original. Nur fuer Messungen und geschlossene
## Tests; es wird nichts erhoben (siehe Experimente).
const PFAD_EXPERIMENT: String = "res://data/balance/experimente/%s_%s.json"
static var variante: String = ""

## Beibehalten fuer Aufrufer, die weiterhin nur eine Welt kennen.
const PFAD: String = "res://data/balance/zimmer.json"

var start_kapital: float = 0.0
var erloes_pro_einheit: float = 1.0
var offline_rate: float = 0.5
var offline_obergrenze: float = 14400.0
## K7: Ist der naechste Raum in so vielen Sekunden Einkommen erreichbar, zeigt die Karte
## keine gruenen Ausbauten mehr (Sparen auf den Raum). 0 = aus.
var spar_fenster: float = 0.0
## ... und erst ab diesem Anteil des Raumpreises auf dem Konto (vorher lohnt jeder Ausbau).
var spar_ab_anteil: float = 0.4
var offline_obergrenze_ausgebaut: float = 43200.0
var transport_faktor_pro_stufe: float = 0.05
var transport_faktor_maximum: float = 3.0

## Die Sonderstation hebt den Erloes je Einheit (ADR-021).
##
## Bisher schaltete sie nur Grossauftraege frei, und ihre Stufen taten nichts.
## In einer Welt, die man durch ALLES Kaufen abschliesst, waeren das dreissig
## Kaeufe ohne Wirkung -- Pflichtarbeit statt Entscheidung. 0 = wie bisher.
var sonder_faktor_pro_stufe: float = 0.0

## Die Sonderstation bringt eine eigene, laufende Grundeinnahme (Welt 3).
##
## Statt den Erloes je Einheit zu heben, liefert sie selbst: ihr Durchsatz
## (basis_durchsatz, Stufe, Sterne, Ausstattung, Raeume) mal Weltfaktor mal
## erloes_pro_einheit je Sekunde -- unabhaengig davon, was die Kette schafft.
## Betreuung ist der erste Erloes, der weiterlaeuft, wenn man nichts tut.
var grundeinnahme_aktiv: bool = false

## Wachstum der Grundeinnahme je Stufe (multiplikativ, 1.0 = linear wie eine
## Kettenstation). Die Kosten der Station wachsen exponentiell; eine Einnahme,
## die nur linear waechst, waere nach zehn Stufen bedeutungslos.
var grundeinnahme_wachstum: float = 1.0

## Belohnungsschub: Multiplikator und Dauer. Die Hoechstdauer deckelt das
## Stapeln -- ohne sie koennte man sich einen Tag Schub anhaeufen, und die
## Kurve, die der Balance-Simulator prueft, waere Makulatur.
var schub_faktor: float = 2.0
var schub_dauer: float = 240.0
var schub_hoechstdauer: float = 1800.0

## Dauerhafter Faktor je abgeschlossener Welt (multiplikativ).
var welt_faktor_pro_welt: float = 6.0

## Die harte Obergrenze (Welt 2).
##
## Sie deckelt den Durchsatz und verschwindet NICHT durch Ausbau -- das ist
## der einzige Moment im Spiel, in dem Ausbauen nicht hilft. Nur ein Umbau
## hebt sie, und der kostet Geld statt Stufen.
var limit_aktiv: bool = false
var limit_obergrenze: float = 0.0
var limit_umbau_kosten: float = 0.0

## Bestand statt Durchsatz (Welt 5).
##
## Erloes kommt pro ABONNENT, nicht pro durchgesetzter Einheit. Der Bestand
## waechst mit der Arbeit und schrumpft ohne Betreuung. Zum ersten Mal muss
## man etwas HALTEN statt herstellen.
var bestand_aktiv: bool = false
var bestand_zuwachs: float = 0.0        ## Abos je Einheit Durchsatz
var bestand_abwanderung: float = 0.0    ## Anteil je Sekunde
var bestand_erloes: float = 0.0         ## Erloes je Abo und Sekunde

## Menschen statt Maschinen (Welt 4).
##
## Die Verarbeitungsstation steht in dieser Welt fuer ANGESTELLTE. Wer sie
## ueberlaestet, bekommt WENIGER heraus, nicht gleich viel. Das ist der
## einzige Ort im Spiel, an dem mehr Druck weniger Leistung bedeutet.
var personen_aktiv: bool = false
var personen_schwelle: float = 1.0      ## ab welcher Auslastung es kippt
var personen_daempfung: float = 0.0     ## wie stark Ueberlast bremst
var personen_minimum: float = 0.4       ## was auch bei voller Ueberlast bleibt

## Schwankung (Welt 6).
##
## Erstmals kann ein Tick unter dem Mittel liegen. Streuung senkt den
## AUSSCHLAG, nicht den Mittelwert -- das ist der ganze Unterschied zwischen
## Streuung und Gewinn.
var risiko_aktiv: bool = false
var risiko_schwankung: float = 0.0          ## Ausschlag ohne Streuung
var risiko_streuung_pro_stufe: float = 0.0  ## wie stark eine Stufe daempft
var risiko_rest_schwankung: float = 0.0     ## was auch bei voller Streuung bleibt

var stationen: Dictionary = {}   ## String -> Dictionary
var unlocks: Dictionary = {}     ## String -> Dictionary

## --- Welt in die Tiefe (ADR-021) ---
##
## Alle vier Abschnitte sind OPTIONAL. Eine Welt ohne sie laeuft wie vorher:
## endlose Stufen, Weltwechsel ueber unlock_world_2. So kann Welt 1 in die
## Tiefe gehen, ohne dass Welt 2 bis 6 im selben Zug umgebaut werden muessen.
var abschluss: StringName = Ids.ABSCHLUSS_SCHWELLE
var bereiche: Dictionary = {}    ## String -> {kosten, schaltet_frei, bonus, nach}
var ziele: Array = []            ## Array[Dictionary]
var nachrichten: Array = []      ## Array[Dictionary]
var momente: Dictionary = {}     ## {aktiv, abstand_min, abstand_max, dauer, ...}

## Crew-Karten je Station (optional, siehe docs/nacht/ov_schema.md) und der
## Tagesaufgaben-Pool dieser Welt (ergaenzt/ueberschreibt den globalen Pool).
var crew: Dictionary = {}
## Ein Regler fuer ALLE Crew-Preise dieser Welt (Balance-Knopf, 1.0 = wie in den Daten).
var crew_kosten_faktor: float = 1.0
## Regler fuer ALLE Ziel-Belohnungen dieser Welt (1.0 = wie in den Daten). Belohnungen
## treiben die Abschlusszeit; hier wird sie nachgestellt, ohne die Ziele anzufassen.
var ziel_belohnung_faktor: float = 1.0
## Zielkorridor der Abschlusszeit im Simulator in Minuten [min, max] (K2 4.3, P6).
## Leer = Standardkorridor aus AbschlussSim. Daten statt Code: je Welt in balance/<welt>.json.
var ziel_minuten: Array = []
var tagesaufgaben_pool: Array = []

## Bedingungstypen, die Ziele und Nachrichten verwenden duerfen. Ein Tippfehler
## im Typ waere sonst ein Ziel, das nie erfuellt wird -- und niemand merkt es.
const BEDINGUNGSTYPEN: Array[String] = [
	"start", "station_stufe", "stufen_gesamt", "ausstattung_stufe",
	"ausstattung_gesamt", "bereich", "verdient", "momente", "sterne",
	"ziel", "abschluss",
	# Seit N02 (alle Welten in Tiefe):
	"ausstattung_station",   ## Summe der Ausstattungsstufen EINER Station
	"freigeschaltet",        ## eine Freischaltung liegt vor (z. B. der Umbau)
	"alle",                  ## alle Unterbedingungen erfuellt -- fuer Missionen
	"fortschritt",           ## Weltfortschritt 0..1 (Messwert = weltwechsel_fortschritt)
	"kette",                 ## alle Ziele einer Ziel-Kette eingeloest (Messwert 0/1)
]

## Zaehler, die Tagesaufgaben kennen duerfen.
const TAGES_ZAEHLER: Array[String] = [
	"stufen_kauf", "ziel_eingeloest", "moment_getippt", "raum_gekauft", "crew_gekauft",
]

var fehler: PackedStringArray = []


## Laedt aus einer Datei. Gibt null zurueck, wenn die Datei fehlt oder
## kaputt ist -- der Aufrufer muss das behandeln.
static func laden(pfad: String = PFAD) -> BalanceData:
	if not FileAccess.file_exists(pfad):
		push_error("Balance-Datei nicht gefunden: %s" % pfad)
		return null
	var text: String = FileAccess.get_file_as_string(pfad)
	return aus_text(text)


## Laedt die Balance EINER WELT ueber ihre ID.
##
## Faellt auf die Standardwelt zurueck statt null zu liefern: Eine Welt ohne
## eigene Zahlen ist im Aufbau normal (Welt 4 hat Assets, bevor sie Balance
## hat). Ein Absturz an dieser Stelle wuerde die Arbeit an allen anderen
## Welten blockieren -- eine Warnung reicht.
static func fuer_welt(welt_id: String) -> BalanceData:
	var pfad: String = PFAD_MUSTER % welt_id
	if FileAccess.file_exists(pfad):
		if variante != "":
			var overlay: BalanceData = _mit_overlay(pfad, welt_id)
			if overlay != null:
				return overlay
		return laden(pfad)
	push_warning("Keine Balance fuer Welt '%s' -- es gilt '%s'" % [welt_id, STANDARD_WELT])
	return laden(PFAD_MUSTER % STANDARD_WELT)


## Original plus Experiment-Overlay (tief gemischt). null, wenn es keins gibt.
static func _mit_overlay(pfad: String, welt_id: String) -> BalanceData:
	var overlay_pfad: String = PFAD_EXPERIMENT % [welt_id, variante]
	if not FileAccess.file_exists(overlay_pfad):
		return null
	var basis: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	var zusatz: Variant = JSON.parse_string(FileAccess.get_file_as_string(overlay_pfad))
	if not (basis is Dictionary) or not (zusatz is Dictionary):
		push_error("Balance-Overlay ungueltig: %s" % overlay_pfad)
		return null
	var daten := BalanceData.new()
	daten._uebernehmen(_tief_mischen(basis as Dictionary, zusatz as Dictionary))
	return daten


## Dictionaries werden Schluessel fuer Schluessel verschmolzen, alles andere
## (Zahlen, Texte, Listen) ersetzt das Original. Schluessel mit `_` am Anfang
## sind Kommentare und werden ignoriert.
static func _tief_mischen(basis: Dictionary, zusatz: Dictionary) -> Dictionary:
	var ergebnis: Dictionary = basis.duplicate(true)
	for schluessel in zusatz.keys():
		if String(schluessel).begins_with("_"):
			continue
		var neu: Variant = zusatz[schluessel]
		if neu is Dictionary and ergebnis.get(schluessel) is Dictionary:
			ergebnis[schluessel] = _tief_mischen(ergebnis[schluessel] as Dictionary, neu as Dictionary)
		else:
			ergebnis[schluessel] = neu
	return ergebnis


## Baut die Daten aus einem JSON-Text. Getrennt von `laden`, damit Tests
## ohne Dateizugriff auskommen.
static func aus_text(json_text: String) -> BalanceData:
	var roh: Variant = JSON.parse_string(json_text)
	if roh == null or not (roh is Dictionary):
		push_error("Balance-JSON ist ungueltig")
		return null
	var daten := BalanceData.new()
	daten._uebernehmen(roh as Dictionary)
	return daten


func _uebernehmen(roh: Dictionary) -> void:
	start_kapital = float(roh.get("start_kapital", start_kapital))
	erloes_pro_einheit = float(roh.get("erloes_pro_einheit", erloes_pro_einheit))

	var off: Dictionary = roh.get("offline", {}) as Dictionary
	offline_rate = float(off.get("rate", offline_rate))
	offline_obergrenze = float(off.get("obergrenze_sekunden", offline_obergrenze))
	offline_obergrenze_ausgebaut = float(
		off.get("obergrenze_ausgebaut_sekunden", offline_obergrenze_ausgebaut))

	var sp: Dictionary = roh.get("sparen", {}) as Dictionary
	spar_fenster = float(sp.get("fenster_sekunden", spar_fenster))
	spar_ab_anteil = float(sp.get("ab_anteil", spar_ab_anteil))

	var tr: Dictionary = roh.get("transport", {}) as Dictionary
	transport_faktor_pro_stufe = float(tr.get("faktor_pro_stufe", transport_faktor_pro_stufe))
	transport_faktor_maximum = float(tr.get("faktor_maximum", transport_faktor_maximum))

	welt_faktor_pro_welt = float(roh.get("welt_faktor_pro_welt", welt_faktor_pro_welt))

	var sonder: Dictionary = roh.get("sonder", {}) as Dictionary
	sonder_faktor_pro_stufe = float(sonder.get("faktor_pro_stufe", 0.0))
	grundeinnahme_aktiv = bool(sonder.get("grundeinnahme_aktiv", false))
	grundeinnahme_wachstum = maxf(float(sonder.get("grundeinnahme_wachstum", 1.0)), 1.0)

	var best: Dictionary = roh.get("bestand", {}) as Dictionary
	bestand_aktiv = bool(best.get("aktiv", false))
	bestand_zuwachs = float(best.get("zuwachs_je_einheit", 0.0))
	bestand_abwanderung = float(best.get("abwanderung_je_sekunde", 0.0))
	bestand_erloes = float(best.get("erloes_je_abo", 0.0))

	var pers: Dictionary = roh.get("personen", {}) as Dictionary
	personen_aktiv = bool(pers.get("aktiv", false))
	personen_schwelle = float(pers.get("schwelle", 1.0))
	personen_daempfung = float(pers.get("daempfung", 0.0))
	personen_minimum = float(pers.get("minimum", 0.4))

	var ris: Dictionary = roh.get("risiko", {}) as Dictionary
	risiko_aktiv = bool(ris.get("aktiv", false))
	risiko_schwankung = float(ris.get("schwankung", 0.0))
	risiko_streuung_pro_stufe = float(ris.get("streuung_pro_stufe", 0.0))
	risiko_rest_schwankung = float(ris.get("rest_schwankung", 0.0))

	var lim: Dictionary = roh.get("limit", {}) as Dictionary
	limit_aktiv = bool(lim.get("aktiv", false))
	limit_obergrenze = float(lim.get("obergrenze", 0.0))
	limit_umbau_kosten = float(lim.get("umbau_kosten", 0.0))

	var sch: Dictionary = roh.get("schub", {}) as Dictionary
	schub_faktor = float(sch.get("faktor", schub_faktor))
	schub_dauer = float(sch.get("dauer_sekunden", schub_dauer))
	schub_hoechstdauer = float(sch.get("hoechstdauer_sekunden", schub_hoechstdauer))

	stationen = roh.get("stationen", {}) as Dictionary
	unlocks = roh.get("unlocks", {}) as Dictionary

	abschluss = StringName(String(roh.get("abschluss", String(Ids.ABSCHLUSS_SCHWELLE))))
	bereiche = roh.get("bereiche", {}) as Dictionary
	ziele = roh.get("ziele", []) as Array
	nachrichten = roh.get("nachrichten", []) as Array
	momente = roh.get("momente", {}) as Dictionary
	crew = roh.get("crew", {}) as Dictionary
	crew_kosten_faktor = float(roh.get("crew_kosten_faktor", 1.0))
	ziel_belohnung_faktor = float(roh.get("ziel_belohnung_faktor", 1.0))
	ziel_minuten = roh.get("ziel_minuten", []) as Array
	tagesaufgaben_pool = roh.get("tagesaufgaben_pool", []) as Array


## Prueft die Daten auf Vollstaendigkeit und Plausibilitaet.
## Gibt true zurueck, wenn alles in Ordnung ist; `fehler` enthaelt sonst
## Klartextmeldungen mit dem betroffenen Feld.
func validieren() -> bool:
	fehler.clear()
	if not ziel_minuten.is_empty() and (ziel_minuten.size() != 2 or float(ziel_minuten[0]) <= 0.0 or float(ziel_minuten[0]) >= float(ziel_minuten[1])):
		fehler.append("ziel_minuten: erwartet [min, max] mit 0 < min < max")

	# Jede Station der Kette muss existieren -- fehlt eine, ist der Durchsatz
	# still null und niemand weiss warum.
	for id in Ids.ALL_STATIONS:
		var schluessel := String(id)
		if not stationen.has(schluessel):
			fehler.append("Station fehlt: %s" % schluessel)
			continue
		_pruefe_station(schluessel, stationen[schluessel] as Dictionary)

	# Unbekannte Stationen deuten auf einen Tippfehler hin
	for schluessel in stationen.keys():
		if not Ids.is_station(StringName(schluessel)):
			fehler.append("Unbekannte Station: %s" % schluessel)

	if offline_rate < 0.0 or offline_rate > 1.0:
		fehler.append("offline.rate muss zwischen 0 und 1 liegen (ist %s)" % offline_rate)
	if offline_obergrenze <= 0.0:
		fehler.append("offline.obergrenze_sekunden muss positiv sein")
	if offline_obergrenze_ausgebaut < offline_obergrenze:
		fehler.append("offline.obergrenze_ausgebaut_sekunden darf nicht kleiner sein als die Grundgrenze")
	if erloes_pro_einheit <= 0.0:
		fehler.append("erloes_pro_einheit muss positiv sein")

	for schluessel in unlocks.keys():
		var u: Dictionary = unlocks[schluessel] as Dictionary
		if not u.has("typ") or not u.has("schwelle"):
			fehler.append("Unlock '%s' braucht 'typ' und 'schwelle'" % schluessel)
		elif float(u.get("schwelle", 0.0)) <= 0.0:
			fehler.append("Unlock '%s': schwelle muss positiv sein" % schluessel)

	_pruefe_tiefe()
	return fehler.is_empty()


## Prueft die optionalen Abschnitte aus ADR-021.
func _pruefe_tiefe() -> void:
	if abschluss != Ids.ABSCHLUSS_SCHWELLE and abschluss != Ids.ABSCHLUSS_ALLES:
		fehler.append("abschluss muss '%s' oder '%s' sein" % [Ids.ABSCHLUSS_SCHWELLE, Ids.ABSCHLUSS_ALLES])

	if abschluss == Ids.ABSCHLUSS_ALLES:
		# Eine Welt, die bei "alles" endet, braucht fuer ALLES ein Ende --
		# sonst ist "alles" nie erreicht und die Welt eine Sackgasse.
		for id in Ids.ALL_STATIONS:
			var st: Dictionary = stationen.get(String(id), {}) as Dictionary
			if int(st.get("max_stufe", 0)) <= 0:
				fehler.append("%s: abschluss 'alles' braucht max_stufe" % id)

	for id in Ids.ALL_STATIONS:
		var st: Dictionary = stationen.get(String(id), {}) as Dictionary
		var plaetze: Dictionary = st.get("ausstattung", {}) as Dictionary
		for platz in plaetze.keys():
			var p: Dictionary = plaetze[platz] as Dictionary
			if float(p.get("basis_kosten", 0.0)) <= 0.0:
				fehler.append("%s/%s: basis_kosten muss positiv sein" % [id, platz])
			if float(p.get("wachstum", 0.0)) < 1.0:
				fehler.append("%s/%s: wachstum muss mindestens 1.0 sein" % [id, platz])
			if int(p.get("max_stufe", 0)) <= 0:
				fehler.append("%s/%s: max_stufe muss positiv sein" % [id, platz])
			var max_station: int = int(st.get("max_stufe", 0))
			if max_station > 0 and int(p.get("ab_stufe", 1)) > max_station:
				fehler.append("%s/%s: ab_stufe liegt ueber der hoechsten Stationsstufe" % [id, platz])

	for bereich in bereiche.keys():
		var b: Dictionary = bereiche[bereich] as Dictionary
		if float(b.get("kosten", 0.0)) <= 0.0:
			fehler.append("Bereich %s: kosten muss positiv sein" % bereich)
		var vorher: String = String(b.get("nach", ""))
		if not vorher.is_empty() and not bereiche.has(vorher):
			fehler.append("Bereich %s: Voraussetzung '%s' gibt es nicht" % [bereich, vorher])

	_pruefe_liste(ziele, "Ziel", "")
	_pruefe_liste(nachrichten, "Nachricht", "ausloeser")
	_pruefe_ketten()
	_pruefe_crew()
	_pruefe_tagesaufgaben_pool()


## Jedes Ziel gehoert zu "start", "welt" oder einem vorhandenen Raum.
func _pruefe_ketten() -> void:
	for eintrag in ziele:
		var d: Dictionary = eintrag as Dictionary
		var kette: String = String(d.get("kette", "welt"))
		if kette == "start" or kette == "welt" or kette == "auftrag":
			continue   # "auftrag": Mini-Aufgaben zwischen Raum 3 und 4 (K3 B1/B3)
		if not bereiche.has(kette):
			fehler.append("Ziel %s: kette '%s' ist weder start, welt noch ein Bereich" % [d.get("id", "?"), kette])


func _pruefe_crew() -> void:
	for schluessel in crew.keys():
		if not Ids.is_station(StringName(schluessel)):
			fehler.append("crew: unbekannte Station '%s'" % schluessel)
			continue
		var eintrag: Dictionary = crew[schluessel] as Dictionary
		var raenge: Array = eintrag.get("raenge", []) as Array
		if raenge.is_empty():
			fehler.append("crew/%s: 'raenge' fehlt" % schluessel)
		var letzter: float = 1.0
		for rang in raenge:
			var r: Dictionary = rang as Dictionary
			if float(r.get("kosten", 0.0)) <= 0.0:
				fehler.append("crew/%s: kosten muss positiv sein" % schluessel)
			var faktor: float = float(r.get("faktor", 0.0))
			if faktor <= letzter:
				fehler.append("crew/%s: faktor muss von Rang zu Rang steigen und ueber 1 liegen" % schluessel)
			letzter = faktor
		if eintrag.has("frei"):
			_pruefe_bedingung(eintrag["frei"] as Dictionary, "crew/%s frei" % schluessel)


func _pruefe_tagesaufgaben_pool() -> void:
	for eintrag in tagesaufgaben_pool:
		var d: Dictionary = eintrag as Dictionary
		if String(d.get("id", "")).is_empty():
			fehler.append("tagesaufgaben_pool: Eintrag ohne id")
		if not TAGES_ZAEHLER.has(String(d.get("zaehler", ""))):
			fehler.append("tagesaufgaben_pool %s: unbekannter zaehler" % d.get("id", "?"))
		if float(d.get("wert", 0.0)) <= 0.0:
			fehler.append("tagesaufgaben_pool %s: wert muss positiv sein" % d.get("id", "?"))


func _pruefe_liste(liste: Array, art: String, unterfeld: String) -> void:
	var gesehen: Dictionary = {}
	for eintrag in liste:
		var d: Dictionary = eintrag as Dictionary
		var eintrag_id: String = String(d.get("id", ""))
		if eintrag_id.is_empty():
			fehler.append("%s ohne id" % art)
			continue
		if gesehen.has(eintrag_id):
			fehler.append("%s %s ist doppelt" % [art, eintrag_id])
		gesehen[eintrag_id] = true
		var bedingung: Dictionary = d if unterfeld.is_empty() else d.get(unterfeld, {}) as Dictionary
		_pruefe_bedingung(bedingung, "%s %s" % [art, eintrag_id])


## Prueft den Typ einer Bedingung -- bei "alle" auch jede Unterbedingung.
func _pruefe_bedingung(bedingung: Dictionary, wo: String) -> void:
	var typ: String = String(bedingung.get("typ", ""))
	if not BEDINGUNGSTYPEN.has(typ):
		fehler.append("%s: unbekannter Typ '%s'" % [wo, typ])
		return
	if typ == "alle":
		var teile: Array = bedingung.get("bedingungen", []) as Array
		if teile.is_empty():
			fehler.append("%s: 'alle' braucht eine Liste 'bedingungen'" % wo)
		for teil in teile:
			_pruefe_bedingung(teil as Dictionary, wo)


func _pruefe_station(schluessel: String, s: Dictionary) -> void:
	var pflicht := ["basis_kosten", "wachstum", "basis_durchsatz"]
	for feld in pflicht:
		if not s.has(feld):
			fehler.append("%s: Feld '%s' fehlt" % [schluessel, feld])

	var kosten: float = float(s.get("basis_kosten", 0.0))
	if kosten <= 0.0:
		fehler.append("%s: basis_kosten muss positiv sein (ist %s)" % [schluessel, kosten])

	# Ein Wachstum unter 1.0 liesse die Kosten sinken -- die Progression
	# wuerde sich selbst aufloesen.
	var wachstum: float = float(s.get("wachstum", 0.0))
	if wachstum < 1.0:
		fehler.append("%s: wachstum muss mindestens 1.0 sein (ist %s)" % [schluessel, wachstum])
	elif wachstum > 1.5:
		fehler.append("%s: wachstum %s ist unspielbar hoch (Korridor 1.07-1.20)" % [schluessel, wachstum])

	if float(s.get("basis_durchsatz", 0.0)) < 0.0:
		fehler.append("%s: basis_durchsatz darf nicht negativ sein" % schluessel)

	if int(s.get("start_stufe", 0)) < 0:
		fehler.append("%s: start_stufe darf nicht negativ sein" % schluessel)


## Baut die Stationsmodelle aus den geprueften Daten.
func erzeuge_stationen() -> Array[StationModel]:
	var liste: Array[StationModel] = []
	for id in Ids.ALL_STATIONS:
		var schluessel := String(id)
		var params: Dictionary = (stationen.get(schluessel, {}) as Dictionary).duplicate()
		params["stufe"] = int(params.get("start_stufe", 0))
		liste.append(StationModel.new(id, params))
	return liste
