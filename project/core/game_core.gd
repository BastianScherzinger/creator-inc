## Der Simulationskern. Bindet Wirtschaft, Kette, Takt und Fortschritt zusammen.
##
## Das ist die EINZIGE Klasse, die die Praesentation ansprechen muss. Sie ist
## vollstaendig headless lauffaehig: kein Node, keine Szene, kein Rendering.
## Ein kompletter Spieldurchlauf ueber 60 simulierte Minuten laeuft in
## Sekundenbruchteilen -- das macht Balancing zu einer Messung statt zu einer
## Vermutung (ADR-004).
class_name GameCore
extends RefCounted

var bus: EventBus
var welten: WorldData
var balance: BalanceData
var kette: ProductionChain
var uhr: SimClock
var fortschritt: Progression
var auftraege: OrderSystem

## Welt in die Tiefe (ADR-021). In Welten ohne diese Daten sind die Systeme
## leer und tun nichts -- sie existieren trotzdem, damit niemand auf null
## pruefen muss.
var bereiche: AreaSystem
var ziele: GoalSystem
var nachrichten: StoryFeed
var momente: MomentSystem

## Fortschrittsmarken der aktuellen Welt (25/50/75 %): drei Ziele vom Typ
## `fortschritt`, immer alle sichtbar und einzeln abholbar. Werte in geschenk.json.
var marken: GoalSystem

## Tagesgeschenk. Gehoert zum ganzen Bogen, nicht zu einer Welt: Es wird beim
## Weltwechsel NICHT zurueckgesetzt.
var geschenk: Tagesgeschenk

## Was in DIESER Welt verdient wurde. gesamt_verdient laeuft ueber den ganzen
## Bogen; ein Ziel "verdiene 10.000" soll aber in Welt 1 bei null anfangen und
## nicht in Welt 3 schon erfuellt sein, bevor man dort angekommen ist.
var welt_verdient: float = 0.0

var kapital: float = 0.0
var gesamt_verdient: float = 0.0
var spielzeit: float = 0.0

## Laufender Belohnungsschub: Multiplikator und Restdauer in Sekunden.
##
## Er sitzt im KERN und nicht in der Oberflaeche, obwohl ihn eine Werbung
## ausloest: Er wird im festen Takt verbraucht, gehoert in den Spielstand,
## und die ANGEZEIGTE Einnahme pro Sekunde muss dieselbe sein wie die
## tatsaechlich verbuchte. Zwei Wahrheiten ueber den Durchsatz sind die
## sichere Art, ein Idle-Game falsch abrechnen zu lassen.
var schub_faktor: float = 1.0
var schub_rest: float = 0.0

## In welcher Welt des Bogens steht der Spieler? 0 ist die erste.
##
## Der Index und nicht die ID: Die Reihenfolge steht in worlds.json, und der
## Kern soll sie nicht doppelt kennen. Wer die ID braucht, fragt `welten`.
var welt_index: int = 0

## Wie oft wurde der ganze Bogen schon durchgespielt?
##
## Ein Idle-Game ohne Neuanfang endet in einer Sackgasse: Die letzte Welt ist
## irgendwann ausgebaut, und dann passiert nichts mehr. Der Neuanfang macht
## aus dem Ende einen Anfang -- und der dauerhafte Faktor sorgt dafuer, dass
## es sich nicht wie Zuruecksetzen anfuehlt, sondern wie Vorsprung.
var durchlaeufe: int = 0

## Abonnenten (Welt 5). Waechst mit der Arbeit, schrumpft ohne Betreuung.
var bestand: float = 0.0

## --- Design-Overhaul 15.10. (U4) ---
## Crew-Karten je Station (pro Welt neu), Tagesaufgaben und Erfolge (ueber den
## ganzen Bogen), Zaehler ueber den Bogen und der Zufallswert der Installation.
var crew: CrewSystem
var tagesaufgaben_system: DailyTasks
var erfolge: Achievements

## Zaehler ueber alle Welten: ziele, bereiche, welten, crew, aufgaben, momente.
var bogen: Dictionary = {"ziele": 0, "bereiche": 0, "welten": 0, "crew": 0, "aufgaben": 0, "momente": 0, "punkte": 0, "schub": 0}

## Wuerfelt der Kern beim ersten Speichern (A/B-Zuteilung, nie gesendet).
var installations_wert: int = 0

## Kapitel der laufenden Welt (K5). Die Liste setzt die Darstellung aus der
## Themendatei (setze_kapitel) -- der Kern kennt keine Texte.
var kapitel: KapitelSystem = KapitelSystem.new()
## Antworten der Entscheidungs-Szenen: "<welt_id>/<kapitel_id>" -> 0|1.
## Nur Ton und Rueckblick, nie Wirtschaft.
var entscheidungen: Dictionary = {}

## Tests und Simulatoren koennen den Kalendertag festlegen (-1 = die echte Uhr).
var tag_override: int = -1

var _welt_gezaehlt: bool = false
var _level_zuletzt: int = 1
var _stumm: bool = false
var _nachkontrolle: float = 0.0

## Eigener Zufall statt des globalen: Mit festem Startwert laeuft der
## Balance-Simulator reproduzierbar, und zwei Laeufe sind vergleichbar.
var _zufall := RandomNumberGenerator.new()


func _init(balance_daten: BalanceData = null, start_welt: int = 0) -> void:
	bus = EventBus.new()
	geschenk = Tagesgeschenk.new()
	welten = WorldData.laden()
	welt_index = clampi(start_welt, 0, maxi(welten.anzahl() - 1, 0))
	balance = balance_daten if balance_daten != null else BalanceData.fuer_welt(welt_id())
	assert(balance != null, "Balance-Daten konnten nicht geladen werden")
	# Fester Startwert: Der Balance-Simulator soll reproduzierbar laufen.
	# Ein zufaelliger Startwert machte zwei Messungen unvergleichbar -- und
	# eine Balance, die man nicht zweimal gleich messen kann, ist keine.
	_zufall.seed = 20260911

	uhr = SimClock.new()
	erfolge = Achievements.new()
	_baue_weltsysteme()
	# NACH der Kette: Das Gleichgewicht haengt am Durchsatz, und den gibt es
	# erst, wenn die Kette steht. Beim ersten Anlauf stand die Zeile davor --
	# sie rechnete mit einem Durchsatz von null und tat damit gar nichts.
	_setze_bestand_ins_gleichgewicht()


## Alles, was eine Welt NEU anfaengt, an EINER Stelle.
##
## Vorher stand dieselbe Zeilenfolge dreimal (Start, Weltwechsel, Neuanfang),
## und jede neue Mechanik haette an drei Stellen ergaenzt werden muessen. Beim
## vierten System ist es genau die Stelle, die man vergisst.
func _baue_weltsysteme() -> void:
	kette = ProductionChain.new(balance.erzeuge_stationen())
	uhr.offline_rate = balance.offline_rate
	uhr.offline_obergrenze_sekunden = balance.offline_obergrenze
	fortschritt = Progression.new(balance.unlocks)
	auftraege = OrderSystem.new()
	bereiche = AreaSystem.new(balance.bereiche)
	ziele = GoalSystem.new(balance.ziele)
	nachrichten = StoryFeed.new(balance.nachrichten)
	momente = MomentSystem.new(balance.momente, 20260911 + welt_index)
	marken = GoalSystem.new(_marken_definitionen())
	crew = CrewSystem.new(balance.crew, balance.stationen, balance.crew_kosten_faktor)
	var aufgaben_alt: Dictionary = tagesaufgaben_system.to_dict() if tagesaufgaben_system != null else {}
	tagesaufgaben_system = DailyTasks.new(balance.tagesaufgaben_pool)
	if not aufgaben_alt.is_empty():
		tagesaufgaben_system.apply_dict(aufgaben_alt)
	_welt_gezaehlt = false
	kapital = balance.start_kapital
	welt_verdient = 0.0
	_aktualisiere_faktoren()


## Ein Simulationsschritt. `delta` ist echte Zeit; die Umrechnung in Ticks
## macht die Uhr, damit das Ergebnis nicht an der Bildrate haengt.
func tick(delta: float) -> void:
	var ticks: int = uhr.advance(delta)
	if ticks <= 0:
		return
	var dauer: float = float(ticks) * SimClock.TICK_DAUER
	spielzeit += dauer

	_verbrauche_schub(dauer)

	var menge: float = durchsatz() * dauer
	_aktualisiere_bestand(menge, dauer)
	if menge > 0.0:
		var erloes: float = _erloes_fuer(menge, dauer)
		if erloes > 0.0:
			_verdiene(erloes)
		elif erloes < 0.0:
			_verliere(-erloes)
		bus.throughput_tick.emit(menge, erloes)
	var grund: float = grundeinnahme() * dauer
	if grund > 0.0:
		_verdiene(grund)

	kette.check_bottleneck_changed(bus)
	_aktiviere(fortschritt.pruefe(kapital, stufen_gesamt(), bus))
	_aktualisiere_transport()
	momente.tick(dauer, _momente_kandidaten(), bus)
	_pruefe_ziele_und_geschichte()
	_nachkontrolle -= dauer
	if _nachkontrolle <= 0.0:
		_nachkontrolle = 10.0
		_pruefe_aufgaben_und_erfolge()
	if balance.limit_aktiv:
		bus.limit_changed.emit(limit_auslastung(), limit_gilt())

	# Grossauftraege laufen nur, wenn die fuenfte Station freigeschaltet ist
	var sonder: StationModel = kette.station(Ids.STATION_SPECIAL)
	if sonder != null and sonder.freigeschaltet:
		auftraege.tick(dauer, bus)


## Der Transportfaktor ist der Lohn fuer die vierte Station.
##
## Er multipliziert den Durchsatz der GESAMTEN Kette -- das ist der Moment,
## in dem Automatisierung sich zum ersten Mal wie Befreiung anfuehlt
## (GAME_DESIGN.md 6). Gedeckelt, damit er die Kette nicht ersetzt: Wer nur
## den Kumpel ausbaut und den Engpass ignoriert, kommt nicht weiter.
func _aktualisiere_transport() -> void:
	var transport: StationModel = kette.station(Ids.STATION_TRANSPORT)
	if transport == null or not transport.freigeschaltet:
		kette.transport_faktor = 1.0
		return
	# Die Ausstattung des Uploads wirkt auf den ZUWACHS, nicht auf die 1,0 davor:
	# Ein besserer Router beschleunigt, was der Upload beitraegt -- nicht die
	# Kette, die es ohne ihn auch gaebe.
	var zuwachs: float = float(transport.stufe) * balance.transport_faktor_pro_stufe 		* transport.ausstattung_faktor() * transport.extern_faktor
	kette.transport_faktor = minf(1.0 + zuwachs, balance.transport_faktor_maximum)


## Eine Freischaltung, die zu einer Station gehoert, schaltet sie im KERN frei.
##
## Das stand bisher in der Darstellung (main.gd) -- mit der Folge, dass der
## Balance-Simulator Upload und Kommentar nie freigeschaltet bekam und zwei
## Stationen dort nie mitrechneten. Was die Wirtschaft veraendert, gehoert in
## den Kern.
func _aktiviere(neu: Array[StringName]) -> void:
	for unlock_id in neu:
		var station_id: StringName = _station_zu_freischaltung(unlock_id)
		if station_id == &"":
			continue
		var station: StationModel = kette.station(station_id)
		if station != null and not station.freigeschaltet:
			station.freigeschaltet = true
			station.stufe = maxi(station.stufe, 1)
			bus.station_upgraded.emit(station_id, station.stufe)
	if not neu.is_empty():
		_aktualisiere_transport()
		kette.check_bottleneck_changed(bus)


static func _station_zu_freischaltung(unlock_id: StringName) -> StringName:
	match unlock_id:
		Ids.UNLOCK_TRANSPORT:
			return Ids.STATION_TRANSPORT
		Ids.UNLOCK_SPECIAL:
			return Ids.STATION_SPECIAL
	return &""


## Baut eine Station aus, wenn das Kapital reicht.
## Gibt true zurueck, wenn der Ausbau stattgefunden hat.
func upgrade_station(id: StringName) -> bool:
	return upgrade_station_mehrfach(id, 1) > 0


## Baut bis zu `anzahl` Stufen auf einmal aus (-1 = so viele, wie das Geld reicht).
##
## Fuer die Knoepfe x10 und MAX. Ein Ereignis am Ende statt zehn einzelne: Die
## Oberflaeche soll einmal reagieren, nicht zehnmal hintereinander blitzen.
## Gibt die Zahl der tatsaechlich gekauften Stufen zurueck.
func upgrade_station_mehrfach(id: StringName, anzahl: int) -> int:
	var station: StationModel = kette.station(id)
	if station == null or not station.freigeschaltet:
		return 0
	var gekauft: int = 0
	var bezahlt: float = 0.0
	var sterne_vorher: int = station.sterne()
	while (anzahl < 0 or gekauft < anzahl) and station.kann_ausbauen():
		var preis: float = station.naechste_kosten()
		if kapital < preis:
			break
		kapital -= preis
		bezahlt += preis
		station.upgrade()
		gekauft += 1
	if gekauft == 0:
		return 0
	bus.money_changed.emit(kapital, -bezahlt)
	bus.station_upgraded.emit(id, station.stufe)
	if station.sterne() > sterne_vorher:
		bus.star_reached.emit(id, station.sterne())
	_zaehle_tag("stufen_kauf", float(gekauft))
	_nach_kauf()
	return gekauft


## Was ein Mehrfachkauf kosten WUERDE: [anzahl, preis].
##
## anzahl -1 (MAX) zaehlt, was das Geld hergibt. Reicht es fuer keine einzige
## Stufe, kommt [0, Preis der naechsten Stufe] zurueck -- der Knopf soll zeigen,
## was fehlt, nicht "0 €".
func vorschau_mehrfach(id: StringName, anzahl: int) -> Array:
	var station: StationModel = kette.station(id)
	if station == null or not station.kann_ausbauen():
		return [0, 0.0]
	var stufe: int = station.stufe
	var summe: float = 0.0
	var menge: int = 0
	var rest: float = kapital
	while (anzahl < 0 or menge < anzahl) and (station.max_stufe <= 0 or stufe < station.max_stufe):
		var preis: float = CostCurve.kosten_fuer_stufe(station.basis_kosten, station.wachstum, stufe + 1)
		if anzahl < 0 and rest < preis:
			break
		rest -= preis
		summe += preis
		stufe += 1
		menge += 1
		if menge > 10000:
			break
	if menge == 0:
		return [0, station.naechste_kosten()]
	return [menge, summe]


## Kauft die naechste Stufe eines Ausstattungsplatzes.
func kaufe_ausstattung(station_id: StringName, platz_id: StringName) -> bool:
	var station: StationModel = kette.station(station_id)
	if station == null or not station.freigeschaltet:
		return false
	var p: EquipmentSlot = station.platz(platz_id)
	if p == null or p.ist_max() or not p.freigegeben(station.stufe):
		return false
	var preis: float = p.naechste_kosten()
	if kapital < preis:
		return false
	kapital -= preis
	p.stufe += 1
	bus.money_changed.emit(kapital, -preis)
	bus.equipment_upgraded.emit(station_id, platz_id, p.stufe)
	_zaehle_tag("stufen_kauf", 1.0)
	_nach_kauf()
	return true


## Kauft einen Raum der Karte.
func kaufe_bereich(bereich_id: StringName) -> bool:
	if not bereiche.verfuegbar(bereich_id):
		return false
	var preis: float = bereiche.kosten(bereich_id)
	if kapital < preis:
		return false
	kapital -= preis
	var kapitel_vorher: int = kapitel_index()
	bereiche.kaufe(bereich_id)
	bus.money_changed.emit(kapital, -preis)
	var unlock_id: StringName = bereiche.schaltet_frei(bereich_id)
	if unlock_id != &"" and not fortschritt.ist_frei(unlock_id):
		fortschritt.setze_frei(unlock_id)
		bus.unlocked.emit(unlock_id)
		var neu: Array[StringName] = [unlock_id]
		_aktiviere(neu)
	bus.area_bought.emit(bereich_id)
	var neues_kapitel: int = KapitelSystem.wechsel(kapitel_vorher, kapitel_index())
	if neues_kapitel >= 0:
		bus.chapter_started.emit(neues_kapitel)
	bogen["bereiche"] = int(bogen.get("bereiche", 0)) + 1
	_zaehle_tag("raum_gekauft", 1.0)
	_nach_kauf()
	return true


## Loest ein erfuelltes Ziel ein. Gibt die Belohnung zurueck (0 = nichts).
##
## Die Belohnung haengt am Einkommen: "zwei Minuten Arbeit" bleibt ueber die
## ganze Welt gleich viel wert, waehrend ein fester Betrag am Anfang ein
## Vermoegen und am Ende ein Trinkgeld waere. Das Minimum sorgt dafuer, dass
## das allererste Ziel nicht "3 €" auszahlt.
func loese_ziel_ein(ziel_id: StringName) -> float:
	var ziel: Dictionary = ziele.einloesen(String(ziel_id), messwert)
	if ziel.is_empty():
		return 0.0
	var betrag: float = ziel_belohnung(ziel)
	if betrag > 0.0:
		_verdiene(betrag)
	bus.goal_claimed.emit(ziel_id, betrag)
	bogen["ziele"] = int(bogen.get("ziele", 0)) + 1
	bogen["punkte"] = int(bogen.get("punkte", 0)) + erfolge.ziel_punkte(ziel)
	_zaehle_tag("ziel_eingeloest", 1.0)
	_pruefe_level()
	_pruefe_ziele_und_geschichte()
	_pruefe_aufgaben_und_erfolge()
	return betrag


## Was eine Station gerade leistet, in ihrer eigenen Groesse: Kettenglieder in
## Einheiten pro Sekunde, der Upload als Faktor auf die Kette, die Sonderstation
## als Faktor auf den Erloes. Das Menue zeigt "jetzt -> danach" und muss dafuer
## nicht wissen, welche Station was bedeutet.
func station_leistung(id: StringName) -> float:
	match id:
		Ids.STATION_TRANSPORT:
			return kette.transport_faktor
		Ids.STATION_SPECIAL:
			if balance.grundeinnahme_aktiv:
				return grundeinnahme()
			return erloes_faktor()
	var s: StationModel = kette.station(id)
	return s.durchsatz() if s != null else 0.0


## Dieselbe Groesse nach dem naechsten Kauf -- einer Stufe oder, mit `platz_id`,
## einer Ausstattungsstufe. Probeweise angewendet und sofort zurueckgenommen.
func station_leistung_danach(id: StringName, platz_id: StringName = &"") -> float:
	var s: StationModel = kette.station(id)
	if s == null:
		return 0.0
	var p: EquipmentSlot = s.platz(platz_id) if platz_id != &"" else null
	if p != null:
		p.stufe += 1
	else:
		s.stufe += 1
	_aktualisiere_transport()
	var danach: float = station_leistung(id)
	if p != null:
		p.stufe -= 1
	else:
		s.stufe -= 1
	_aktualisiere_transport()
	return danach


## Wie viel mehr pro Sekunde herein kaeme, wenn diese Stufe oder diese
## Ausstattungsstufe gekauft wuerde.
##
## Das Menue zeigte vorher nur die Leistung der Station ("60 -> 120 Ideen/Min").
## Ist die Station nicht der Engpass, verdoppelt sich dabei die Leistung und das
## Einkommen steigt um nichts -- die Anzeige versprach etwas, das der Kauf nicht
## hielt. Die ehrliche Zahl ist die Mehreinnahme.
##
## Im Bestand (Welt 5) wirkt ein Kauf erst mit Verzoegerung auf das Einkommen --
## gemessen am Einkommen JETZT braechte jeder Kauf null. Dort zaehlt deshalb der
## Unterschied im Gleichgewicht, auf das der Bestand zulaeuft.
func einkommen_danach(id: StringName, platz_id: StringName = &"") -> float:
	var s: StationModel = kette.station(id)
	if s == null:
		return einkommen_pro_sekunde()
	var vorher: float = einkommen_ziel()
	var p: EquipmentSlot = s.platz(platz_id) if platz_id != &"" else null
	if p != null:
		p.stufe += 1
	else:
		s.stufe += 1
	_aktualisiere_transport()
	var danach: float = einkommen_ziel()
	if p != null:
		p.stufe -= 1
	else:
		s.stufe -= 1
	_aktualisiere_transport()
	return einkommen_pro_sekunde() + (danach - vorher)


## Tippt die laufende Blase an.
func tippe_moment() -> float:
	var betrag: float = momente.antippen(einkommen_pro_sekunde(), bus)
	if betrag > 0.0:
		_verdiene(betrag)
		bogen["momente"] = int(bogen.get("momente", 0)) + 1
		_zaehle_tag("moment_getippt", 1.0)
		_pruefe_ziele_und_geschichte()
	return betrag


func _nach_kauf() -> void:
	_aktualisiere_faktoren()
	_aktualisiere_transport()
	kette.check_bottleneck_changed(bus)
	_aktiviere(fortschritt.pruefe(kapital, stufen_gesamt(), bus))
	_pruefe_ziele_und_geschichte()
	_pruefe_erfolge()


## Gibt jeder Station den Faktor aus den gekauften Raeumen.
func _aktualisiere_faktoren() -> void:
	if kette == null or bereiche == null:
		return
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station != null:
			station.extern_faktor = bereiche.faktor_fuer(id) * crew.faktor(id)


## Ueber welchen Stationen darf eine Blase erscheinen? Nur ueber solchen, die
## arbeiten -- eine Blase ueber einem abgesperrten Raum waere ein Versprechen,
## das man nicht einloesen kann.
##
## Arbeitet mindestens eine, darf auch eine Lieferung kommen (KISTE), und am
## Engpass darf sich Arbeit stapeln (stapel_ziel) -- dort, wo sie wirklich wartet.
func _momente_kandidaten() -> Array[StringName]:
	var liste: Array[StringName] = []
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station != null and station.freigeschaltet and station.stufe > 0:
			liste.append(id)
	var engpass: StringName = kette.bottleneck()
	momente.stapel_ziel = engpass if liste.has(engpass) else &""
	if not liste.is_empty():
		liste.append(MomentSystem.KISTE)
	return liste


## Raeumt den Stapel am Engpass ab (K3 B2). Gibt die Schubdauer in Sekunden
## zurueck, 0 = dort lag kein Stapel zum Antippen.
##
## Kein Geld: Die gestapelten Teile sind Darstellung, ihr Ertrag ist schon
## gezaehlt. Der Lohn ist der Schub -- er laeuft ueber starte_schub und schlaeft
## deshalb wie jeder Schub, waehrend die App schlaeft (wende_offline_an): Der
## Offline-Ertrag bleibt unberuehrt.
func tippe_stapel(station_id: StringName) -> float:
	var sekunden: float = momente.stapel_antippen(station_id, bus)
	if sekunden <= 0.0:
		return 0.0
	starte_schub(sekunden)
	bogen["momente"] = int(bogen.get("momente", 0)) + 1
	_zaehle_tag("moment_getippt", 1.0)
	_pruefe_ziele_und_geschichte()
	return sekunden


## K6 Welle 2: Geld auf der Kasse antippen -- kleiner Bonus, nie Pflicht.
func tippe_kasse() -> float:
	var betrag: float = momente.kasse_antippen(einkommen_pro_sekunde(), bus)
	if betrag > 0.0:
		_verdiene(betrag)
		bogen["momente"] = int(bogen.get("momente", 0)) + 1
	return betrag


func _pruefe_ziele_und_geschichte() -> void:
	var gerade_fertig: bool = _pruefe_abschluss()
	ziele.pruefe(messwert, bus)
	for marke_id in marken.pruefe(messwert, null):
		bus.progress_mark_ready.emit(StringName(marke_id))
	nachrichten.pruefe(bedingung_erfuellt, bus)
	# Das Signal kommt ERST, wenn auch die letzte Nachricht zugestellt ist: Der
	# Abschluss zeigt sie. Im ersten Anlauf stand dort die vorletzte, weil der
	# Abschluss gemeldet wurde, bevor die Geschichte nachgezogen hatte.
	if gerade_fertig:
		_zaehle_welt_fertig()
		bus.world_completed.emit()
		bus.unlocked.emit(Ids.UNLOCK_WORLD_2)


# --- Fortschrittsmarken und Tagesgeschenk (Release-Plan 2026-10-14) ----------

## Die drei Marken als Ziel-Definitionen aus geschenk.json.
func _marken_definitionen() -> Array:
	var roh: Dictionary = Tagesgeschenk.lade_roh().get("fortschrittsmarken", {}) as Dictionary
	var liste: Array = []
	for schwelle in (roh.get("schwellen", []) as Array):
		var prozent: int = int(round(float(schwelle) * 100.0))
		liste.append({
			"id": "fortschritt_%d" % prozent,
			"typ": "fortschritt",
			"wert": float(schwelle),
			"belohnung_sekunden": float(roh.get("belohnung_sekunden", 0.0)),
			"belohnung_minimum": float(roh.get("belohnung_minimum", 0.0)),
		})
	return liste


## Alle Marken fuer die Kopfleiste: {id, wert, bereit, eingeloest, belohnung}.
func marken_liste() -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for d in marken.definitionen():
		var marke: Dictionary = d as Dictionary
		var marke_id: String = String(marke.get("id", ""))
		var eingeloest: bool = marken.ist_eingeloest(marke_id)
		liste.append({
			"id": marke_id,
			"wert": float(marke.get("wert", 0.0)),
			"eingeloest": eingeloest,
			"bereit": not eingeloest and GoalSystem.erfuellt(marke, messwert),
			"belohnung": marken_belohnung(marke_id),
		})
	return liste


## Was die Marke JETZT auszahlen wuerde.
func marken_belohnung(marke_id: String) -> float:
	var marke: Dictionary = marken.definition(marke_id)
	if marke.is_empty():
		return 0.0
	return maxf(einkommen_pro_sekunde() * float(marke.get("belohnung_sekunden", 0.0)),
		float(marke.get("belohnung_minimum", 0.0)))


## Holt eine erreichte Marke ab. Gibt den Betrag zurueck, 0 wenn nichts da war.
func loese_marke_ein(marke_id: StringName) -> float:
	var betrag: float = marken_belohnung(String(marke_id))
	if marken.einloesen(String(marke_id), messwert).is_empty():
		return 0.0
	if betrag > 0.0:
		_verdiene(betrag)
	bus.progress_mark_claimed.emit(marke_id, betrag)
	return betrag


## Ist am Kalendertag `tag` (Tage seit 1970, lokal; Standard: heute) ein Geschenk da?
func geschenk_verfuegbar(tag: int = -1) -> bool:
	return geschenk.verfuegbar(tag if tag >= 0 else Tagesgeschenk.heute())


## Welcher Serientag (1..n) wuerde abgeholt -- fuer die Karte "Geschenk Tag 3/7".
func geschenk_serientag(tag: int = -1) -> int:
	return geschenk.naechster_serientag(tag if tag >= 0 else Tagesgeschenk.heute())


## Wie viele Tage die Serie hat (die "7" in "Tag 3/7").
func geschenk_serientage() -> int:
	return geschenk.tage_in_serie()


## Betrag des Geschenks an diesem Tag: Einkommen x Dauer x Serienfaktor.
func geschenk_betrag(tag: int = -1) -> float:
	var faktor: float = geschenk.faktor_fuer(geschenk_serientag(tag))
	return maxf(einkommen_pro_sekunde() * geschenk.sekunden * faktor, geschenk.minimum * faktor)


## Holt das Tagesgeschenk ab. Gibt den Betrag zurueck, 0 wenn heute schon geholt.
func loese_geschenk_ein(tag: int = -1) -> float:
	var heute_tag: int = tag if tag >= 0 else Tagesgeschenk.heute()
	if not geschenk.verfuegbar(heute_tag):
		return 0.0
	var betrag: float = geschenk_betrag(heute_tag)
	var serientag: int = geschenk.abholen(heute_tag)
	_verdiene(betrag)
	bus.daily_gift_claimed.emit(serientag, betrag)
	return betrag


## Die Angaben fuer die Geschenk-Karte; leer, wenn heute nichts abzuholen ist.
## `tag`/`serie_max`/`betrag`/`faktor` und `tage` (Faktor je Serientag 1..n).
func geschenk_bereit(tag: int = -1) -> Dictionary:
	if not geschenk_verfuegbar(tag):
		return {}
	var serientag: int = geschenk_serientag(tag)
	return {
		"tag": serientag,
		"serie_max": geschenk_serientage(),
		"betrag": geschenk_betrag(tag),
		"faktor": geschenk.faktor_fuer(serientag),
		"tage": geschenk.serie_faktoren.duplicate(),
	}


## Kurzform von loese_geschenk_ein fuer die Oberflaeche.
func geschenk_abholen(tag: int = -1) -> float:
	return loese_geschenk_ein(tag)


# --- Messen: eine Stelle fuer Ziele UND Nachrichten --------------------------

## Der aktuelle Wert zu einer Bedingung aus den Daten.
func messwert(bedingung: Dictionary) -> float:
	var typ: String = String(bedingung.get("typ", ""))
	match typ:
		"start":
			return 1.0
		"station_stufe":
			var s: StationModel = kette.station(StringName(String(bedingung.get("station", ""))))
			return float(s.stufe) if s != null else 0.0
		"stufen_gesamt":
			return float(stufen_gesamt())
		"ausstattung_stufe":
			var st: StationModel = kette.station(StringName(String(bedingung.get("station", ""))))
			if st == null:
				return 0.0
			var p: EquipmentSlot = st.platz(StringName(String(bedingung.get("platz", ""))))
			return float(p.stufe) if p != null else 0.0
		"ausstattung_gesamt":
			return float(ausstattung_stufen_gesamt())
		"bereich":
			return 1.0 if bereiche.ist_gekauft(StringName(String(bedingung.get("bereich", "")))) else 0.0
		"verdient":
			return welt_verdient
		"momente":
			return float(momente.angetippt_gesamt)
		"sterne":
			return float(sterne_gesamt())
		"ziel":
			return 1.0 if ziele.ist_eingeloest(String(bedingung.get("ziel", ""))) else 0.0
		"abschluss":
			return 1.0 if welt_abgeschlossen() else 0.0
		"fortschritt":
			return weltwechsel_fortschritt()
		"ausstattung_station":
			var sa: StationModel = kette.station(StringName(String(bedingung.get("station", ""))))
			if sa == null:
				return 0.0
			var summe: int = 0
			for pl in sa.ausstattung:
				summe += pl.stufe
			return float(summe)
		"freigeschaltet":
			return 1.0 if fortschritt.ist_frei(StringName(String(bedingung.get("unlock", "")))) else 0.0
		"kette":
			return 1.0 if kette_fertig(String(bedingung.get("kette", ""))) else 0.0
		"alle":
			# Eine Mission aus mehreren Teilen. Der Wert ist der erfuellte ANTEIL --
			# so zeigt der Balken, wie weit man ist; erfuellt ist sie erst bei 1.
			var teile: Array = bedingung.get("bedingungen", []) as Array
			if teile.is_empty():
				return 0.0
			var erfuellt: int = 0
			for teil in teile:
				if bedingung_erfuellt(teil as Dictionary):
					erfuellt += 1
			return float(erfuellt) / float(teile.size())
	return 0.0


func bedingung_erfuellt(bedingung: Dictionary) -> bool:
	return messwert(bedingung) >= float(bedingung.get("wert", 1.0))


func ausstattung_stufen_gesamt() -> int:
	var summe: int = 0
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station == null:
			continue
		for p in station.ausstattung:
			summe += p.stufe
	return summe


func sterne_gesamt() -> int:
	var summe: int = 0
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station != null:
			summe += station.sterne()
	return summe


# --- Weltabschluss (ADR-021) ---------------------------------------------------

func welt_hat_abschluss() -> bool:
	return balance.abschluss == Ids.ABSCHLUSS_ALLES


## Drei Anteile von 0 bis 1: Stationsstufen, Ausstattungsstufen, Raeume.
##
## Drei getrennte Balken statt einer Summe aller Kaeufe: 230 Stationsstufen
## wuerden fuenf Raeume sonst unsichtbar machen, obwohl jeder Raum ein
## groesserer Schritt ist als jede einzelne Stufe.
func abschluss_anteile() -> Dictionary:
	var stufen_ist: int = 0
	var stufen_soll: int = 0
	var plaetze_ist: int = 0
	var plaetze_soll: int = 0
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station == null:
			continue
		if station.max_stufe > 0:
			stufen_soll += station.max_stufe
			stufen_ist += mini(station.stufe, station.max_stufe)
		for p in station.ausstattung:
			plaetze_soll += p.max_stufe
			plaetze_ist += p.stufe
	return {
		"stufen": float(stufen_ist) / float(stufen_soll) if stufen_soll > 0 else 1.0,
		"ausstattung": float(plaetze_ist) / float(plaetze_soll) if plaetze_soll > 0 else 1.0,
		"bereiche": bereiche.anteil(),
	}


func welt_abgeschlossen() -> bool:
	if not welt_hat_abschluss():
		return fortschritt.ist_frei(Ids.UNLOCK_WORLD_2)
	var a: Dictionary = abschluss_anteile()
	return float(a["stufen"]) >= 1.0 and float(a["ausstattung"]) >= 1.0 \
		and float(a["bereiche"]) >= 1.0


## Bei 100 % gibt der Kern den Weltwechsel frei -- ueber DIESELBE Freischaltung
## wie die alten Welten. Damit bleiben Weltwechsel-Angebot, Abspann und
## Spielstand unveraendert, egal wie eine Welt endet.
func _pruefe_abschluss() -> bool:
	if not welt_hat_abschluss() or fortschritt.ist_frei(Ids.UNLOCK_WORLD_2):
		return false
	if not welt_abgeschlossen():
		return false
	fortschritt.setze_frei(Ids.UNLOCK_WORLD_2)
	return true


## Verrechnet die Abwesenheit seit dem letzten Spielstand.
## Wird als Geschenk praesentiert, nie als entgangener Gewinn
## (GAME_DESIGN.md 5.4).
## Der Schub SCHLAEFT, waehrend die App schlaeft.
##
## Er wird hier weder angewendet noch verbraucht, und das ist die einzige
## haltbare von drei Moeglichkeiten:
##   - Anwenden UND verbrauchen waere unfair -- vier Minuten Schub waeren
##     nach dem ersten Blick aufs Handy weg.
##   - Anwenden ohne zu verbrauchen waere ein Selbstbedienungsladen: Schub
##     starten, App schliessen, vier Stunden spaeter das Vierfache abholen.
##     Genau so bricht die Kurve, die der Balance-Simulator prueft.
##   - Also: Er wartet. Wer zurueckkommt, findet seinen Schub vor.
func wende_offline_an(abwesend_sekunden: float) -> float:
	# Die Obergrenze waechst mit dem Rang (offline_6h/8h/12h in erfolge.json).
	uhr.offline_obergrenze_sekunden = erfolge.offline_obergrenze(spieler_level(), balance.offline_obergrenze)
	var grundertrag: float = kette.effektiver_durchsatz() * welt_faktor() 		* balance.erloes_pro_einheit * erloes_faktor() + _grundeinnahme_ohne_schub()
	var erloes: float = uhr.offline_ertrag(grundertrag, abwesend_sekunden)
	if erloes > 0.0:
		_verdiene(erloes)
		bus.offline_progress_applied.emit(
			uhr.anrechenbare_offline_sekunden(abwesend_sekunden), erloes)
	return erloes


## Loest einen wartenden Grossauftrag ein.
func loese_auftrag_ein() -> float:
	var erloes: float = auftraege.einloesen(einkommen_pro_sekunde(), bus)
	if erloes > 0.0:
		_verdiene(erloes)
	return erloes


## Fortschritt in Richtung Weltwechsel, 0.0 bis 1.0.
##
## Das Fernziel muss jederzeit ablesbar sein -- ein Idle-Game ohne sichtbares
## Ziel ist nur eine Zahl, die groesser wird (GAME_DESIGN.md 2).
func weltwechsel_fortschritt() -> float:
	if welt_hat_abschluss():
		var a: Dictionary = abschluss_anteile()
		return (float(a["stufen"]) + float(a["ausstattung"]) + float(a["bereiche"])) / 3.0
	var bedingung: Dictionary = balance.unlocks.get(String(Ids.UNLOCK_WORLD_2), {}) as Dictionary
	var schwelle: float = float(bedingung.get("schwelle", 0.0))
	if schwelle <= 0.0:
		return 0.0
	return clampf(float(stufen_gesamt()) / schwelle, 0.0, 1.0)


## Die ID der Welt, in der gerade gespielt wird -- Schluessel fuer Themendaten,
## Balance und Assets.
func welt_id() -> String:
	return welten.id(welt_index)


## Wechselt in die naechste Welt.
##
## Was BLEIBT: gesamt_verdient und die Spielzeit. Sie erzaehlen den ganzen
## Bogen und duerfen nie zurueckgesetzt werden -- sie sind das Einzige, was
## belegt, dass die erste Welt stattgefunden hat.
##
## Was NEU ANFAENGT: Kette, Kapital, Freischaltungen. Eine neue Welt ist ein
## neuer Anfang, sonst waere sie nur eine Fortsetzung mit anderer Tapete.
##
## Was MITGENOMMEN wird: ein dauerhafter Faktor je abgeschlossener Welt. Ohne
## ihn faengt der Spieler sechsmal bei null an und merkt beim dritten Mal, dass
## Fortschritt nichts bedeutet.
func wechsle_welt() -> bool:
	if welten.ist_letzte(welt_index):
		return false
	_zaehle_welt_fertig()
	welt_index += 1
	balance = BalanceData.fuer_welt(welt_id())
	_baue_weltsysteme()
	schub_faktor = 1.0
	schub_rest = 0.0
	bestand = 0.0
	_setze_bestand_ins_gleichgewicht()
	bus.world_changed.emit(welt_index, welt_id())
	return true


## Der dauerhafte Faktor aus abgeschlossenen Welten.
##
## Multiplikativ und aus den Daten, nicht aus dem Code: Wie stark eine Welt
## nachwirkt, ist eine Balance-Frage und keine Programmierfrage.
func welt_faktor() -> float:
	return pow(balance.welt_faktor_pro_welt, float(welt_index)) * erfahrungsfaktor() * erfolge_faktor()


## Der dauerhafte Faktor aus abgeschlossenen Durchlaeufen.
##
## Er ist bewusst kraeftig (Faktor 4 je Durchlauf): Wer den ganzen Bogen ein
## zweites Mal beginnt, soll die erste Welt in Minuten hinter sich lassen und
## nicht noch einmal zwanzig. Was beim ersten Mal die Geschichte war, ist beim
## zweiten Mal der Vorspann.
func erfahrungsfaktor() -> float:
	return pow(4.0, float(durchlaeufe))


## Ist der Bogen zu Ende gespielt?
##
## Nicht "letzte Welt betreten", sondern "letzte Welt DURCH": Sonst waere der
## Abspann der Anfang von Welt 6 statt ihres Endes.
func bogen_beendet() -> bool:
	if not welten.ist_letzte(welt_index):
		return false
	return fortschritt.ist_frei(Ids.UNLOCK_WORLD_2)


## Faengt von vorn an -- mit allem, was man mitnimmt.
##
## Was BLEIBT: gesamt_verdient, Spielzeit und die Zahl der Durchlaeufe. Sie
## sind der einzige Beleg dafuer, dass der erste Bogen stattgefunden hat.
## Alles andere faengt neu an, und das ist der Sinn: Das Zimmer aus Akt 1 sieht
## beim zweiten Mal anders aus, weil man weiss, was daraus wird.
func neuanfang() -> void:
	_zaehle_welt_fertig()
	durchlaeufe += 1
	welt_index = 0
	balance = BalanceData.fuer_welt(welt_id())
	_baue_weltsysteme()
	schub_faktor = 1.0
	schub_rest = 0.0
	bus.world_changed.emit(welt_index, welt_id())


## Startet den Bestand im GLEICHGEWICHT statt bei null.
##
## Man kommt nicht mit null Kunden im Loft an -- man bringt die mit, die man
## sich in Welt 4 erarbeitet hat. Erzaehlerisch ist das richtig, und
## rechnerisch ist es der Unterschied zwischen einer Mechanik und einer Huerde:
## Bei null Abonnenten ist das Einkommen null, die erste Ausbaustufe damit
## unerreichbar, und die gemessene Wartezeit unendlich.
##
## Das Gleichgewicht ergibt sich aus den Daten selbst (Zuwachs mal Durchsatz
## geteilt durch Abwanderung) und nicht aus einer Zahl, die jemand geschaetzt
## hat. Damit stimmt es auch noch, wenn jemand an der Balance dreht.
func _setze_bestand_ins_gleichgewicht() -> void:
	if not balance.bestand_aktiv or balance.bestand_abwanderung <= 0.0:
		return
	bestand = durchsatz() * balance.bestand_zuwachs / balance.bestand_abwanderung


## --- Bestand (Welt 5) ---------------------------------------------------
##
## Der Durchsatz erzeugt keine Einnahme mehr, sondern ABONNENTEN. Sie zahlen,
## solange sie bleiben, und sie gehen von allein wieder.
##
## Das ist der erste Ertrag im Spiel, der schrumpft, wenn man nichts tut --
## bis hierher konnte Fortschritt nur stehenbleiben, nie zurueckgehen. Genau
## deshalb steht er in Welt 5 und nicht frueher: Wer etwas halten muss, hat
## vorher etwas aufgebaut.
func _aktualisiere_bestand(menge: float, dauer: float) -> void:
	if not balance.bestand_aktiv:
		return
	bestand += menge * balance.bestand_zuwachs
	# Abwanderung wirkt auf den BESTAND, nicht auf einen festen Betrag:
	# Wer viele hat, verliert viele. Sonst waere ein grosser Bestand
	# automatisch sicherer als ein kleiner, und das waere gelogen.
	var verlust: float = bestand * balance.bestand_abwanderung * dauer
	bestand = maxf(bestand - verlust, 0.0)
	bus.bestand_changed.emit(bestand, verlust / maxf(dauer, 0.0001))


## --- Schwankung (Welt 6) ------------------------------------------------
##
## Der Ertrag eines Ticks liegt um den Mittelwert herum statt genau darauf.
## Die Streuung (die Transport-Station) senkt den AUSSCHLAG, nicht den
## Mittelwert -- das ist der ganze Unterschied zwischen Streuung und Gewinn,
## und das Spiel soll ihn lehren, ohne ihn zu erklaeren.
##
## Ein Rest bleibt immer. Eine Streuung, die den Ausschlag auf null bringt,
## waere eine Behauptung ueber die Wirklichkeit, die nicht stimmt.
func _erloes_fuer(menge: float, dauer: float) -> float:
	if balance.bestand_aktiv:
		# Die Sonderstation hebt auch hier den Erloes -- ohne diesen Faktor waeren
		# ihre dreissig Stufen in Welt 5 Kaeufe ohne jede Wirkung.
		return bestand * balance.bestand_erloes * erloes_faktor() * dauer
	var grund: float = menge * balance.erloes_pro_einheit * erloes_faktor()
	if not balance.risiko_aktiv:
		return grund
	return grund * _schwankungsfaktor()


func _schwankungsfaktor() -> float:
	var streuung: StationModel = kette.station(Ids.STATION_TRANSPORT)
	var stufen: int = streuung.stufe if streuung != null and streuung.freigeschaltet else 0
	var daempfung: float = 1.0 - float(stufen) * balance.risiko_streuung_pro_stufe
	var ausschlag: float = balance.risiko_schwankung * maxf(daempfung, 0.0)
	ausschlag = maxf(ausschlag, balance.risiko_rest_schwankung)
	# Symmetrisch um 1.0: Der MITTELWERT bleibt unveraendert, egal wie stark
	# gestreut wird. Waere er es nicht, waere Streuung heimlich ein Gewinn --
	# und der Spieler wuerde etwas Falsches ueber Risiko lernen.
	return 1.0 + _zufall.randf_range(-ausschlag, ausschlag)


func stufen_gesamt() -> int:
	var summe: int = 0
	for id in Ids.ALL_STATIONS:
		var s: StationModel = kette.station(id)
		if s != null:
			summe += s.stufe
	return summe


## Was pro Sekunde hereinkommt -- im MITTEL.
##
## "Im Mittel" ist ab Welt 6 woertlich zu nehmen: Dort schwankt der Ertrag.
## Die Anzeige zeigt trotzdem den Mittelwert und nicht den letzten Tick, sonst
## springt die Zahl in der Kopfzeile wild und sagt nichts mehr aus.
func einkommen_pro_sekunde() -> float:
	if balance.bestand_aktiv:
		return bestand * balance.bestand_erloes * erloes_faktor() + grundeinnahme()
	return durchsatz() * balance.erloes_pro_einheit * erloes_faktor() + grundeinnahme()


## Das Einkommen, auf das die Welt gerade zulaeuft.
##
## Ueberall ausser im Bestand ist das das Einkommen jetzt. Im Bestand hinkt das
## Einkommen jedem Ausbau hinterher; wer bewerten will, ob ein Kauf sich lohnt
## (Menue, Simulator), braucht das Gleichgewicht, nicht den Augenblick.
func einkommen_ziel() -> float:
	if not balance.bestand_aktiv or balance.bestand_abwanderung <= 0.0:
		return einkommen_pro_sekunde()
	var gleichgewicht: float = durchsatz() * balance.bestand_zuwachs / balance.bestand_abwanderung
	return gleichgewicht * balance.bestand_erloes * erloes_faktor() + grundeinnahme()


## Die laufende Grundeinnahme der Sonderstation je Sekunde (Welt 3), sonst 0.
##
## Unabhaengig von der Kette: Sie laeuft, auch wenn der Engpass steht. Der Schub
## wirkt mit, damit die angezeigte Verdopplung auch fuer sie gilt.
func grundeinnahme() -> float:
	return _grundeinnahme_ohne_schub() * schub_faktor


func _grundeinnahme_ohne_schub() -> float:
	if not balance.grundeinnahme_aktiv:
		return 0.0
	var sonder: StationModel = kette.station(Ids.STATION_SPECIAL)
	if sonder == null or not sonder.freigeschaltet:
		return 0.0
	var stufenwachstum: float = pow(balance.grundeinnahme_wachstum, float(maxi(sonder.stufe - 1, 0)))
	return sonder.durchsatz() * stufenwachstum * welt_faktor() * balance.erloes_pro_einheit


## Der Faktor der Sonderstation auf den Erloes je Einheit (1.0 = keiner).
func erloes_faktor() -> float:
	if balance.sonder_faktor_pro_stufe <= 0.0:
		return 1.0
	var sonder: StationModel = kette.station(Ids.STATION_SPECIAL)
	if sonder == null or not sonder.freigeschaltet:
		return 1.0
	return 1.0 + float(sonder.stufe) * balance.sonder_faktor_pro_stufe 		* sonder.ausstattung_faktor() * sonder.extern_faktor


## Der Durchsatz einschliesslich eines laufenden Schubs.
##
## Tick und Anzeige gehen hierdurch -- die Offline-Rechnung BEWUSST nicht,
## siehe wende_offline_an().
func durchsatz() -> float:
	return minf(roher_durchsatz(), obergrenze())


## Der Durchsatz OHNE die harte Obergrenze.
##
## Getrennt, weil die Oberflaeche beides braucht: Sie zeigt an, wie viel die
## Kette koennte, und wie viel davon durchkommt. Ohne diesen Unterschied waere
## das Limit unsichtbar -- der Spieler saehe nur, dass Ausbauen nichts bringt,
## und wuesste nicht warum.
func roher_durchsatz() -> float:
	return kette.effektiver_durchsatz() * schub_faktor * welt_faktor() * personen_faktor()


## --- Menschen (Welt 4) --------------------------------------------------
##
## Die Verarbeitungsstation steht in dieser Welt fuer ANGESTELLTE. Kommt mehr
## Arbeit herein, als sie schaffen, wird WENIGER fertig -- nicht gleich viel.
##
## Das ist der einzige Ort im Spiel, an dem mehr Druck weniger Leistung
## bedeutet, und die einzige Stelle, an der es schadet, eine ANDERE Station
## auszubauen. Wer Akquise und Planung hochzieht, ohne das Team mitwachsen zu
## lassen, verliert Durchsatz und wundert sich.
##
## Ein Rest bleibt immer: Ueberlastete Menschen arbeiten langsamer, nicht gar
## nicht. Das ist kein Balancing-Detail, sondern die Aussage.
func personen_faktor() -> float:
	if not balance.personen_aktiv:
		return 1.0
	var verarbeitung: StationModel = kette.station(Ids.STATION_PROCESSING)
	if verarbeitung == null or verarbeitung.durchsatz() <= 0.0:
		return 1.0
	var annahme: StationModel = kette.station(Ids.STATION_INTAKE)
	var puffer: StationModel = kette.station(Ids.STATION_BUFFER)
	if annahme == null or puffer == null:
		return 1.0
	var zulauf: float = minf(annahme.durchsatz(), puffer.durchsatz())
	var last: float = zulauf / verarbeitung.durchsatz()
	if last <= balance.personen_schwelle:
		return 1.0
	var ueberlast: float = last - balance.personen_schwelle
	return maxf(1.0 - balance.personen_daempfung * ueberlast, balance.personen_minimum)


## Wie stark ist das Team ueberlastet? 0.0 heisst: alles im Rahmen.
## Fuer die Anzeige -- ohne sie merkt der Spieler nur, dass es langsamer wird.
func ueberlastung() -> float:
	return 1.0 - personen_faktor()


## Die Obergrenze, oder unendlich, wenn keine gilt.
##
## Sie waechst mit dem Weltfaktor mit. Sonst waere sie in Welt 2 eine Wand und
## in Welt 5 ein Staubkorn -- eine Grenze, die man vergessen kann, ist keine.
func obergrenze() -> float:
	if not limit_gilt():
		return INF
	return balance.limit_obergrenze * welt_faktor()


## Gilt die Obergrenze gerade?
##
## Sie gilt, solange die Welt eine hat UND der Umbau nicht gekauft wurde.
func limit_gilt() -> bool:
	return balance.limit_aktiv and not fortschritt.ist_frei(Ids.UNLOCK_UMBAU)


## Wie voll ist die Leitung? 1.0 heisst: am Anschlag.
func limit_auslastung() -> float:
	if not limit_gilt():
		return 0.0
	var grenze: float = obergrenze()
	if grenze <= 0.0:
		return 1.0
	return roher_durchsatz() / grenze


## Kauft den Umbau, der die Obergrenze aufhebt.
##
## Es ist ein KAUF und keine Freischaltung ueber eine Schwelle, und das ist der
## Kern der Mechanik: An dieser Stelle muss man etwas WEGNEHMEN, statt weiter
## etwas hinzuzufuegen. Diese Entscheidung kann einem kein Zaehler abnehmen.
##
## (Der Browser raus, das HTML direkt gelesen. Zwei Tage Arbeit, um etwas
## wegzunehmen -- docs/STORY.md, Akt 2.)
func kaufe_umbau() -> bool:
	if not limit_gilt():
		return false
	var preis: float = umbau_kosten()
	if kapital < preis:
		return false
	kapital -= preis
	fortschritt.setze_frei(Ids.UNLOCK_UMBAU)
	bus.money_changed.emit(kapital, -preis)
	bus.unlocked.emit(Ids.UNLOCK_UMBAU)
	bus.limit_changed.emit(0.0, false)
	return true


func umbau_kosten() -> float:
	return balance.limit_umbau_kosten * welt_faktor()


## Startet oder verlaengert den Schub.
##
## Verlaengern statt ersetzen: Wer zwei Belohnungen kurz hintereinander
## einloest, hat sie sich zweimal verdient. Gedeckelt bleibt die Kurve
## trotzdem berechenbar (BalanceData.schub_hoechstdauer).
func starte_schub(dauer_sekunden: float = -1.0) -> void:
	var dauer: float = balance.schub_dauer if dauer_sekunden < 0.0 else dauer_sekunden
	schub_faktor = balance.schub_faktor
	schub_rest = minf(schub_rest + dauer, balance.schub_hoechstdauer)
	bogen["schub"] = int(bogen.get("schub", 0)) + 1
	bus.boost_changed.emit(schub_faktor, schub_rest)


func schub_laeuft() -> bool:
	return schub_rest > 0.0


func _verbrauche_schub(dauer: float) -> void:
	if schub_rest <= 0.0:
		return
	schub_rest = maxf(schub_rest - dauer, 0.0)
	if schub_rest <= 0.0:
		schub_faktor = 1.0
	bus.boost_changed.emit(schub_faktor, schub_rest)


func _verdiene(betrag: float) -> void:
	kapital += betrag
	gesamt_verdient += betrag
	welt_verdient += betrag
	bus.money_changed.emit(kapital, betrag)


## Ein Tick mit Verlust (Welt 6). Nie unter null: Ein Spiel, das Schulden macht,
## haelt den Spieler fest -- und genau das darf keine Mechanik. Gebucht wird
## netto, damit der Mittelwert ehrlich bleibt.
func _verliere(betrag: float) -> void:
	var abzug: float = minf(betrag, maxf(kapital, 0.0))
	if abzug <= 0.0:
		return
	kapital -= abzug
	gesamt_verdient -= abzug
	welt_verdient -= abzug
	bus.money_changed.emit(kapital, -abzug)
	bus.loss_tick.emit(abzug)


# --- Spielstand --------------------------------------------------------------

# --- Kapitel und Entscheidungen (K5) ----------------------------------------------

## Kapiteldaten der laufenden Welt als neutrale Liste (aus der Themendatei).
func setze_kapitel(liste: Array) -> void:
	kapitel = KapitelSystem.new(liste)


## Das laufende Kapitel (0-basiert), -1 ohne Kapiteldaten.
func kapitel_index() -> int:
	return kapitel.index_fuer(bereiche.to_array())


func _entscheidung_schluessel(kapitel_id: String) -> String:
	return "%s/%s" % [welt_id(), kapitel_id]


## Merkt die Antwort (0 oder 1) einer Entscheidung. Aendert nichts an der Wirtschaft.
func merke_entscheidung(kapitel_id: String, antwort: int) -> void:
	if kapitel_id.is_empty() or antwort < 0:
		return
	entscheidungen[_entscheidung_schluessel(kapitel_id)] = clampi(antwort, 0, 1)


## Die gemerkte Antwort dieser Welt, -1 = noch nicht entschieden.
func entscheidung(kapitel_id: String) -> int:
	return int(entscheidungen.get(_entscheidung_schluessel(kapitel_id), -1))


func to_save() -> SaveData:
	var s := SaveData.new()
	s.kapital = kapital
	s.gesamt_verdient = gesamt_verdient
	s.spielzeit_sekunden = spielzeit
	s.letzter_zeitstempel = int(Time.get_unix_time_from_system())
	s.unlocks = fortschritt.to_array()
	s.auftraege = auftraege.to_dict()
	s.schub = {"faktor": schub_faktor, "rest": schub_rest}
	s.welt_index = welt_index
	s.durchlaeufe = durchlaeufe
	s.bestand = bestand
	s.welt_verdient = welt_verdient
	s.bereiche = bereiche.to_array()
	s.ziele = ziele.to_array()
	s.nachrichten = nachrichten.to_dict()
	s.momente = momente.to_dict()
	s.marken = marken.to_array()
	s.tagesgeschenk = geschenk.to_dict()
	s.crew = crew.to_dict()
	s.tagesaufgaben = tagesaufgaben_system.to_dict()
	s.bogen = bogen.duplicate()
	s.erfolge = erfolge.to_array()
	s.entscheidungen = entscheidungen.duplicate()
	if installations_wert == 0:
		var wuerfel := RandomNumberGenerator.new()
		wuerfel.randomize()
		installations_wert = wuerfel.randi_range(1, 2000000000)
	s.installations_wert = installations_wert
	Experimente.installations_wert = installations_wert
	s.stationen = {}
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kette.station(id)
		if station != null:
			s.stationen[String(id)] = station.to_dict()
	return s


func from_save(stand: SaveData) -> void:
	# Die Welt ZUERST: Kette, Balance und Freischaltungen haengen daran. Wer
	# erst die Stufen setzt und dann die Welt wechselt, hat die Stufen an die
	# falsche Kette geschrieben.
	durchlaeufe = maxi(stand.durchlaeufe, 0)
	bestand = maxf(stand.bestand, 0.0)
	var gewuenscht: int = clampi(stand.welt_index, 0, maxi(welten.anzahl() - 1, 0))
	if gewuenscht != welt_index:
		welt_index = gewuenscht
		balance = BalanceData.fuer_welt(welt_id())
		_baue_weltsysteme()
	kapital = stand.kapital
	welt_verdient = maxf(stand.welt_verdient, 0.0)
	gesamt_verdient = stand.gesamt_verdient
	spielzeit = stand.spielzeit_sekunden
	fortschritt.apply_array(stand.unlocks)
	auftraege.apply_dict(stand.auftraege)
	schub_faktor = float(stand.schub.get("faktor", 1.0))
	schub_rest = float(stand.schub.get("rest", 0.0))
	if schub_rest <= 0.0:
		schub_faktor = 1.0
	for schluessel in stand.stationen.keys():
		var station: StationModel = kette.station(StringName(schluessel))
		if station != null:
			station.apply_dict(stand.stationen[schluessel] as Dictionary)
	bereiche.apply_array(stand.bereiche)
	ziele.apply_array(stand.ziele)
	nachrichten.apply_dict(stand.nachrichten)
	momente.apply_dict(stand.momente)
	marken.apply_array(stand.marken)
	geschenk.apply_dict(stand.tagesgeschenk)
	crew.apply_dict(stand.crew)
	tagesaufgaben_system.apply_dict(stand.tagesaufgaben)
	erfolge.apply_array(stand.erfolge)
	entscheidungen = stand.entscheidungen.duplicate()
	installations_wert = stand.installations_wert
	Experimente.installations_wert = installations_wert
	_gleiche_alten_stand_an()
	_uebernimm_bogen(stand)
	_aktualisiere_faktoren()
	_aktualisiere_transport()
	_stumm = true
	_pruefe_erfolge()
	_stumm = false
	_level_zuletzt = spieler_level()


## Ein Spielstand von VOR der Tiefe (ADR-021) passt nicht ohne Weiteres.
##
## Zwei Faelle, beide zugunsten des Spielers geloest:
##  - Upload oder Kommentar sind schon freigeschaltet, der Raum dazu ist aber
##    nicht gekauft. Dann gilt der Raum als gekauft -- den Upload wieder
##    wegzunehmen, weil es jetzt Raeume gibt, waere eine Strafe fuer nichts.
##  - Der Weltwechsel ist ueber die alte Stufen-Schwelle freigeschaltet, die
##    Welt aber nicht zu 100 % fertig. Dann gilt er als NICHT freigeschaltet:
##    Eine Welt, die bei "alles" endet, soll nicht bei 40 % enden.
func _gleiche_alten_stand_an() -> void:
	for bereich_id in bereiche.ids():
		var unlock_id: StringName = bereiche.schaltet_frei(bereich_id)
		if unlock_id != &"" and fortschritt.ist_frei(unlock_id):
			bereiche.setze_gekauft(bereich_id)
	if welt_hat_abschluss() and fortschritt.ist_frei(Ids.UNLOCK_WORLD_2) \
			and not welt_abgeschlossen():
		fortschritt.freigeschaltet.erase(String(Ids.UNLOCK_WORLD_2))


# --- Design-Overhaul 15.10. (U4): Ketten, Sterne, Empfehlung, Crew, Tagesaufgaben,
# --- Erfolge, Level. Die Formate stehen in docs/nacht/ov_schema.md. ------------

## Der Kalendertag fuer Tagesaufgaben (Tage seit 1970, lokal).
func _heute() -> int:
	return tag_override if tag_override >= 0 else Tagesgeschenk.heute()


## Was ein Ziel JETZT auszahlen wuerde: Einkommen x Sekunden, mindestens das Minimum.
func ziel_belohnung(ziel: Dictionary) -> float:
	return maxf(einkommen_pro_sekunde() * float(ziel.get("belohnung_sekunden", 0.0)) 		* balance.ziel_belohnung_faktor, float(ziel.get("belohnung_minimum", 0.0)))


# --- Ziel-Ketten ---------------------------------------------------------------

func _ziele_der_kette(kette_id: String) -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for eintrag in ziele.definitionen():
		var d: Dictionary = eintrag as Dictionary
		if String(d.get("kette", "welt")) == kette_id:
			liste.append(d)
	return liste


## Die Ketten dieser Welt in Reihenfolge: "start", die Raeume, "welt" -- nur die mit Zielen.
func ketten_ids() -> Array[String]:
	var kandidaten: Array[String] = ["start"]
	for bereich_id in bereiche.ids():
		kandidaten.append(String(bereich_id))
	kandidaten.append("auftrag")   # K3 B1: Mini-Aufgaben zwischen Raum 3 und 4
	kandidaten.append("welt")
	var liste: Array[String] = []
	for kette_id in kandidaten:
		if not _ziele_der_kette(kette_id).is_empty():
			liste.append(kette_id)
	return liste


## Sind alle Ziele der Kette eingeloest? Eine leere Kette gilt nie als fertig.
func kette_fertig(kette_id: String) -> bool:
	var liste: Array[Dictionary] = _ziele_der_kette(kette_id)
	if liste.is_empty():
		return false
	for d in liste:
		if not ziele.ist_eingeloest(String(d.get("id", ""))):
			return false
	return true


func _ziel_eintrag(d: Dictionary, status: String) -> Dictionary:
	var soll: float = float(d.get("wert", 1.0))
	var ist: float = messwert(d)
	return {
		"id": String(d.get("id", "")),
		"kette": String(d.get("kette", "welt")),
		"status": status,
		"fortschritt": clampf(ist / soll, 0.0, 1.0) if soll > 0.0 else 1.0,
		"ist": ist,
		"soll": soll,
		"belohnung": ziel_belohnung(d),
		"ort": ziel_ort(String(d.get("id", ""))),
	}


## Die Ziele einer Kette mit Status: "erledigt" · "bereit" (einloesbar) · "laeuft" · "offen".
func kette_ziele(kette_id: String) -> Array[Dictionary]:
	var sichtbar_ids: Dictionary = {}
	for z in ziele.sichtbar():
		sichtbar_ids[String((z as Dictionary).get("id", ""))] = true
	var liste: Array[Dictionary] = []
	var laeuft_vergeben: bool = false
	for d in _ziele_der_kette(kette_id):
		var ziel_id: String = String(d.get("id", ""))
		var status: String = "offen"
		if ziele.ist_eingeloest(ziel_id):
			status = "erledigt"
		elif sichtbar_ids.has(ziel_id) and bedingung_erfuellt(d):
			status = "bereit"
		elif not laeuft_vergeben:
			status = "laeuft"
			laeuft_vergeben = true
		liste.append(_ziel_eintrag(d, status))
	return liste


func kette_stand(kette_id: String) -> Dictionary:
	var gesamt: int = 0
	var erledigt: int = 0
	var naechstes: String = ""
	for d in _ziele_der_kette(kette_id):
		gesamt += 1
		if ziele.ist_eingeloest(String(d.get("id", ""))):
			erledigt += 1
		elif naechstes.is_empty():
			naechstes = String(d.get("id", ""))
	return {"anzahl": gesamt, "erledigt": erledigt, "fertig": gesamt > 0 and erledigt == gesamt,
		"naechstes": naechstes}


## EIN Ziel fuer die Leiste: ein einloesbares, sonst das naechste im Pfad. {} wenn alles erledigt.
func haupt_ziel() -> Dictionary:
	var offen: Array[Dictionary] = ziele.sichtbar()
	for d in offen:
		if bedingung_erfuellt(d):
			return _ziel_eintrag(d, "bereit")
	if offen.is_empty():
		return {}
	return _ziel_eintrag(offen[0], "laeuft")


## Wohin springt die Oberflaeche beim Tippen auf ein Ziel? {art: station|bereich|menue, id}.
func ziel_ort(ziel_id: String) -> Dictionary:
	var d: Dictionary = ziele.definition(ziel_id)
	if d.is_empty():
		return {"art": "menue", "id": "ziele"}
	if d.has("ort"):
		return d["ort"] as Dictionary
	match String(d.get("typ", "")):
		"station_stufe", "ausstattung_stufe", "ausstattung_station":
			return {"art": "station", "id": String(d.get("station", ""))}
		"bereich":
			return {"art": "bereich", "id": String(d.get("bereich", ""))}
		"kette":
			return {"art": "bereich", "id": String(d.get("kette", ""))}
	return {"art": "menue", "id": "ziele"}


# --- Sterne, Empfehlung, Kaufbarkeit -----------------------------------------------

## Der Weg zum naechsten Stern: {sterne, moeglich, stufen_bis, ist, soll, faktor, fortschritt}.
func stern_info(station_id: StringName) -> Dictionary:
	var s: StationModel = kette.station(station_id)
	if s == null or s.meilenstein_intervall <= 0:
		return {"sterne": 0, "moeglich": 0, "stufen_bis": 0, "ist": 0, "soll": 0, "faktor": 1.0,
			"fortschritt": 1.0}
	var bis: int = s.stufen_bis_meilenstein()
	var sterne: int = s.sterne()
	var ist: int = s.stufe - sterne * s.meilenstein_intervall
	return {
		"sterne": sterne,
		"moeglich": s.sterne_moeglich(),
		"stufen_bis": bis,
		"ist": s.stufe,
		"soll": s.stufe + bis,
		"faktor": s.meilenstein_faktor,
		"fortschritt": clampf(float(ist) / float(s.meilenstein_intervall), 0.0, 1.0) if bis > 0 else 1.0,
	}


## Bringt die naechste Stufe wirklich mehr Einkommen UND reicht das Geld? (Welt-Pfeil)
## Nicht pro Frame aufrufen: Die UI merkt sich das Ergebnis bei `money_changed`.
func kauf_lohnt(station_id: StringName) -> bool:
	var s: StationModel = kette.station(station_id)
	if s == null or not s.freigeschaltet or not s.kann_ausbauen():
		return false
	if kapital < s.naechste_kosten():
		return false
	return einkommen_danach(station_id) > einkommen_pro_sekunde() * (1.0 + 1.0e-9)


## Der EINE "Lohnt sich"-Kauf: bezahlbar, bringt Mehreinkommen, kuerzeste Amortisation.
## {art: stufe|platz|crew, station, platz, preis, mehr} oder {}.
func empfehlung() -> Dictionary:
	var beste: Dictionary = {}
	var jetzt: float = einkommen_pro_sekunde()
	for id in Ids.ALL_STATIONS:
		var s: StationModel = kette.station(id)
		if s == null or not s.freigeschaltet:
			continue
		if s.kann_ausbauen() and kapital >= s.naechste_kosten():
			_bewerte_kauf(beste, {"art": "stufe", "station": id, "platz": &"",
				"preis": s.naechste_kosten(), "mehr": einkommen_danach(id) - jetzt})
		for p in s.ausstattung:
			if not p.ist_max() and p.freigegeben(s.stufe) and kapital >= p.naechste_kosten():
				_bewerte_kauf(beste, {"art": "platz", "station": id, "platz": p.id,
					"preis": p.naechste_kosten(), "mehr": einkommen_danach(id, p.id) - jetzt})
		if crew_frei(id) and not crew.ist_max(id) and kapital >= crew.kosten_naechster(id):
			_bewerte_kauf(beste, {"art": "crew", "station": id, "platz": &"",
				"preis": crew.kosten_naechster(id), "mehr": einkommen_nach_crew(id) - jetzt})
	return beste


## K6 1c: Alle Verbesserungen eines gekauften Raums (Stufe, Ausstattung, Crew je Station),
## billigste zuerst -- fuer die Liste im Raum-Menue. Form wie empfehlung().
func kaeufe_im_raum(bereich_id: StringName) -> Array[Dictionary]:
	var kandidaten: Array[Dictionary] = _kaeufe_im_raum_ungeordnet(bereich_id)
	kandidaten.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["preis"]) < float(b["preis"]))
	return kandidaten


## Dieselben Kaeufe in Stationsreihenfolge (empfehlung_im_raum bewertet in dieser Reihenfolge).
func _kaeufe_im_raum_ungeordnet(bereich_id: StringName) -> Array[Dictionary]:
	var jetzt: float = einkommen_pro_sekunde()
	var kandidaten: Array[Dictionary] = []
	for id in _stationen_im_raum(bereich_id):
		var s: StationModel = kette.station(id)
		if s == null or not s.freigeschaltet:
			continue
		if s.kann_ausbauen():
			kandidaten.append({"art": "stufe", "station": id, "platz": &"",
				"preis": s.naechste_kosten(), "mehr": einkommen_danach(id) - jetzt})
		for p in s.ausstattung:
			if not p.ist_max() and p.freigegeben(s.stufe):
				kandidaten.append({"art": "platz", "station": id, "platz": p.id,
					"preis": p.naechste_kosten(), "mehr": einkommen_danach(id, p.id) - jetzt})
		if crew_frei(id) and not crew.ist_max(id):
			kandidaten.append({"art": "crew", "station": id, "platz": &"",
				"preis": crew.kosten_naechster(id), "mehr": einkommen_nach_crew(id) - jetzt})
	return kandidaten


## Die beste Verbesserung EINES Raums (Bereich oder Startzone) fuer den Schnellkauf im
## Ueberblick (K4 P1.1). Gleiche Form wie empfehlung(), aber auch fuer Kaeufe, die noch
## zu teuer sind -- man sieht, worauf man spart. Reihenfolge: bezahlbar und lohnend
## (kuerzeste Amortisation) > lohnend, aber zu teuer > Ausbau des Engpasses > billigster
## offener Kauf. {} = im Raum ist nichts mehr offen.
func empfehlung_im_raum(bereich_id: StringName) -> Dictionary:
	var kandidaten: Array[Dictionary] = _kaeufe_im_raum_ungeordnet(bereich_id)
	if kandidaten.is_empty():
		return {}
	var bezahlbar: Dictionary = {}
	var lohnend: Dictionary = {}
	for k in kandidaten:
		if kapital >= float(k["preis"]):
			_bewerte_kauf(bezahlbar, k)
		_bewerte_kauf(lohnend, k)
	if not bezahlbar.is_empty():
		return bezahlbar
	if not lohnend.is_empty():
		return lohnend
	var engpass: StringName = kette.bottleneck()
	var billigster: Dictionary = {}
	for k in kandidaten:
		if String(k["art"]) == "stufe" and StringName(k["station"]) == engpass:
			return k
		if billigster.is_empty() or float(k["preis"]) < float(billigster["preis"]):
			billigster = k
	return billigster


## Kauft einen Vorschlag aus empfehlung()/empfehlung_im_raum(). false = zu teuer oder weg.
func kaufe_empfehlung(kauf: Dictionary) -> bool:
	var sid: StringName = StringName(String(kauf.get("station", "")))
	match String(kauf.get("art", "")):
		"stufe":
			return upgrade_station(sid)
		"platz":
			return kaufe_ausstattung(sid, StringName(String(kauf.get("platz", ""))))
		"crew":
			return kaufe_crew(sid)
	return false


## Ersetzt `beste` (in-place) durch `kandidat`, wenn er sich schneller bezahlt macht.
func _bewerte_kauf(beste: Dictionary, kandidat: Dictionary) -> void:
	var mehr: float = float(kandidat["mehr"])
	if mehr <= 0.0 or mehr <= einkommen_pro_sekunde() * 1.0e-9:
		return
	if beste.is_empty() or _kaufzeit(kandidat) < _kaufzeit(beste):
		beste.clear()
		beste.merge(kandidat)


func _kaufzeit(kauf: Dictionary) -> float:
	return float(kauf["preis"]) / maxf(float(kauf["mehr"]), 1.0e-12)


## Der Pseudo-Raum der Startzone (sie hat keinen Bereich, aber eine Kette "start").
const START_RAUM: StringName = &"start"


## Angaben zu einem Raum fuer das Raum-Panel und die Raum-Plakette auf der Karte.
##
## K3 A2: `kaeufe_bezahlbar` (Stationen im Raum mit mindestens einem bezahlbaren
## Kauf), `naechster_preis` (gesperrt: Raumpreis; gekauft: billigster offener Kauf
## im Raum, 0 = nichts mehr offen) und `anteil_gespart` (Kapital / naechster_preis,
## 0..1). `start` liefert die Startzone (immer gekauft).
func bereich_info(bereich_id: StringName) -> Dictionary:
	if bereich_id == START_RAUM:
		var start: Dictionary = {"kosten": 0.0, "gekauft": true, "verfuegbar": true, "bezahlbar": true,
			"voraussetzung": "", "bonus_faktor": 1.0, "bonus_ziel": "", "schaltet_station": ""}
		start.merge(_raum_kaeufe(START_RAUM, true, 0.0))
		return start
	if not bereiche.existiert(bereich_id):
		return {}
	var bonus: Dictionary = bereiche.bonus(bereich_id)
	var info: Dictionary = {
		"kosten": bereiche.kosten(bereich_id),
		"gekauft": bereiche.ist_gekauft(bereich_id),
		"verfuegbar": bereiche.verfuegbar(bereich_id),
		"bezahlbar": kapital >= bereiche.kosten(bereich_id),
		"voraussetzung": String(bereiche.voraussetzung(bereich_id)),
		"bonus_faktor": float(bonus.get("faktor", 1.0)),
		"bonus_ziel": String(bonus.get("ziel", "")),
		"schaltet_station": String(_station_zu_freischaltung(bereiche.schaltet_frei(bereich_id))),
	}
	info.merge(_raum_kaeufe(bereich_id, bool(info["gekauft"]), float(info["kosten"])))
	return info


## K7: Der naechste Raum, auf den gerade gespart wird -- liegt sein Preis innerhalb des
## Sparfensters (Sekunden Einkommen) und ist ein Teil davon schon da. Bleibt auch, wenn er
## bezahlbar ist: dann leuchtet nur ER, bis er gekauft ist. Leer = kein Sparziel.
## Solange es eins gibt, zeigt die Karte keine gruenen Ausbauten: sonst kauft man jede
## kleine Stufe sofort und erreicht den Raum nie (QA 17.10.: Raum 3 erst nach 27 min).
func sparziel() -> StringName:
	var fenster: float = balance.spar_fenster
	# Erst ab dem zweiten Raum: Bis zum ersten Raumkauf fuehrt das Tutorial ueber Ausbauten.
	if fenster <= 0.0 or bereiche == null or bereiche.anzahl_gekauft() < 1:
		return &""
	var ziel: StringName = &""
	var preis: float = INF
	for id in bereiche.ids():
		if bereiche.ist_gekauft(id) or not bereiche.verfuegbar(id):
			continue
		if bereiche.kosten(id) < preis:
			preis = bereiche.kosten(id)
			ziel = id
	var zu_wenig: bool = kapital < preis * balance.spar_ab_anteil
	if ziel == &"" or zu_wenig or preis > einkommen_pro_sekunde() * fenster:
		return &""
	return ziel


## Kaufzaehler und Sparstand eines Raums (Teil von bereich_info).
func _raum_kaeufe(bereich_id: StringName, gekauft: bool, raum_preis: float) -> Dictionary:
	var anzahl: int = 0
	var billigster: float = INF
	var sparen: bool = sparziel() != &""
	if gekauft:
		for id in _stationen_im_raum(bereich_id):
			var s: StationModel = kette.station(id)
			if s == null or not s.freigeschaltet:
				continue
			var bezahlbar: bool = false
			if s.kann_ausbauen():
				billigster = minf(billigster, s.naechste_kosten())
				bezahlbar = kapital >= s.naechste_kosten()
			for p in s.ausstattung:
				if p.ist_max() or not p.freigegeben(s.stufe):
					continue
				billigster = minf(billigster, p.naechste_kosten())
				bezahlbar = bezahlbar or kapital >= p.naechste_kosten()
			if bezahlbar and not sparen:
				anzahl += 1
	else:
		billigster = raum_preis
	var preis: float = billigster if billigster < INF else 0.0
	return {
		"kaeufe_bezahlbar": anzahl,
		"naechster_preis": preis,
		"anteil_gespart": clampf(kapital / preis, 0.0, 1.0) if preis > 0.0 else 1.0,
	}


## Stationen, die in einem Raum (Bereich oder Startzone) der aktuellen Welt stehen.
func _stationen_im_raum(bereich_id: StringName) -> Array[StringName]:
	var ids: Array[StringName] = []
	if welten == null:
		return ids
	var zonen_liste: Array[Dictionary] = []
	if bereich_id == START_RAUM:
		var start: Dictionary = welten.startzone(welt_index)
		if not start.is_empty():
			zonen_liste.append(start)
	else:
		for eintrag in welten.zonen(welt_index):
			var z: Dictionary = eintrag as Dictionary
			if StringName(String(z.get("bereich", ""))) == bereich_id:
				zonen_liste.append(z)
	for z in zonen_liste:
		for id in welten.stationen_in_zone(welt_index, z):
			if not ids.has(id):
				ids.append(id)
	return ids


# --- Crew --------------------------------------------------------------------------

func crew_hat(station_id: StringName) -> bool:
	return crew.hat(station_id)


func crew_rang(station_id: StringName) -> int:
	return crew.rang(station_id)


func crew_faktor(station_id: StringName) -> float:
	return crew.faktor(station_id)


## Der Faktor aus gekauften Raeumen allein (extern_faktor enthaelt Raum UND Crew).
func raum_faktor(station_id: StringName) -> float:
	return bereiche.faktor_fuer(station_id)


## Ist die Karte dieser Station freigeschaltet (Bedingung aus den Daten, sonst Stationsstufe)?
func crew_frei(station_id: StringName) -> bool:
	if not crew.hat(station_id):
		return false
	var s: StationModel = kette.station(station_id)
	if s == null or not s.freigeschaltet:
		return false
	var bedingung: Dictionary = crew.frei_bedingung(station_id)
	if bedingung.is_empty():
		return s.stufe >= crew.frei_ab_stufe
	return bedingung_erfuellt(bedingung)


## Alle Raenge: [{rang, kosten, faktor, gekauft, frei, naechster, kaufbar}].
func crew_raenge(station_id: StringName) -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	var aktuell: int = crew.rang(station_id)
	var frei: bool = crew_frei(station_id)
	var index: int = 0
	for r in crew.raenge(station_id):
		var d: Dictionary = r as Dictionary
		liste.append({
			"rang": index + 1,
			"kosten": float(d.get("kosten", 0.0)),
			"faktor": float(d.get("faktor", 1.0)),
			"gekauft": index < aktuell,
			"frei": frei,
			"naechster": index == aktuell,
			"kaufbar": frei and index == aktuell and kapital >= float(d.get("kosten", 0.0)),
		})
		index += 1
	return liste


func kaufe_crew(station_id: StringName) -> bool:
	if not crew_frei(station_id) or crew.ist_max(station_id):
		return false
	var preis: float = crew.kosten_naechster(station_id)
	if kapital < preis:
		return false
	kapital -= preis
	crew.erhoehe(station_id)
	bus.money_changed.emit(kapital, -preis)
	bus.crew_hired.emit(station_id, crew.rang(station_id))
	bogen["crew"] = int(bogen.get("crew", 0)) + 1
	_zaehle_tag("crew_gekauft", 1.0)
	_nach_kauf()
	return true


## Einkommen (Ziel), wenn der naechste Crew-Rang gekauft waere. Probeweise und zurueck.
func einkommen_nach_crew(station_id: StringName) -> float:
	var s: StationModel = kette.station(station_id)
	if s == null or crew.ist_max(station_id):
		return einkommen_pro_sekunde()
	var verhaeltnis: float = crew.faktor_bei(station_id, crew.rang(station_id) + 1) \
		/ crew.faktor(station_id)
	var vorher: float = einkommen_ziel()
	s.extern_faktor *= verhaeltnis
	_aktualisiere_transport()
	var danach: float = einkommen_ziel()
	s.extern_faktor /= verhaeltnis
	_aktualisiere_transport()
	return einkommen_pro_sekunde() + (danach - vorher)


# --- Tagesaufgaben -------------------------------------------------------------------

func tagesaufgaben_aktiv() -> bool:
	return weltwechsel_fortschritt() >= tagesaufgaben_system.ab_fortschritt


func _synchronisiere_tag() -> void:
	tagesaufgaben_system.aktualisiere(_heute(), tagesaufgaben_aktiv())


func _zaehle_tag(zaehler: String, menge: float) -> void:
	_synchronisiere_tag()
	for aufgabe_id in tagesaufgaben_system.zaehle(zaehler, menge):
		bus.daily_task_completed.emit(StringName(aufgabe_id))


## Die Aufgaben von heute: {id, ist, soll, fortschritt, erfuellt, eingeloest, belohnung}.
func tagesaufgaben() -> Array[Dictionary]:
	_synchronisiere_tag()
	var liste: Array[Dictionary] = []
	for aufgabe_id in tagesaufgaben_system.gewaehlt():
		var d: Dictionary = tagesaufgaben_system.definition(aufgabe_id)
		var soll: float = tagesaufgaben_system.soll(aufgabe_id)
		var ist: float = tagesaufgaben_system.ist(aufgabe_id)
		liste.append({
			"id": aufgabe_id,
			"zaehler": String(d.get("zaehler", "")),
			"ist": minf(ist, soll),
			"soll": soll,
			"fortschritt": clampf(ist / soll, 0.0, 1.0) if soll > 0.0 else 1.0,
			"erfuellt": ist >= soll,
			"eingeloest": tagesaufgaben_system.ist_eingeloest(aufgabe_id),
			"belohnung": ziel_belohnung(d),
		})
	return liste


func loese_tagesaufgabe_ein(aufgabe_id: StringName) -> float:
	_synchronisiere_tag()
	var d: Dictionary = tagesaufgaben_system.einloesen(String(aufgabe_id))
	if d.is_empty():
		return 0.0
	var betrag: float = ziel_belohnung(d)
	if betrag > 0.0:
		_verdiene(betrag)
	bogen["aufgaben"] = int(bogen.get("aufgaben", 0)) + 1
	bus.daily_task_claimed.emit(aufgabe_id, betrag)
	_pruefe_erfolge()
	return betrag


## Die Eintraege der Ziele-Leiste (hoechstens zwei): Hauptziel, dann eine Tagesaufgabe.
func leiste() -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	var z: Dictionary = haupt_ziel()
	if not z.is_empty():
		liste.append({"art": "ziel", "id": z["id"], "fortschritt": z["fortschritt"],
			"ist": z["ist"], "soll": z["soll"], "belohnung": z["belohnung"],
			"bereit": String(z["status"]) == "bereit", "ort": z["ort"]})
	var wahl: Dictionary = {}
	for a in tagesaufgaben():
		if bool(a["eingeloest"]):
			continue
		if wahl.is_empty() or (bool(a["erfuellt"]) and not bool(wahl["erfuellt"])):
			wahl = a
	if not wahl.is_empty():
		liste.append({"art": "tagesaufgabe", "id": wahl["id"], "fortschritt": wahl["fortschritt"],
			"ist": wahl["ist"], "soll": wahl["soll"], "belohnung": wahl["belohnung"],
			"bereit": bool(wahl["erfuellt"]), "ort": {"art": "menue", "id": "ziele"}})
	return liste


func _pruefe_aufgaben_und_erfolge() -> void:
	_synchronisiere_tag()
	_pruefe_erfolge()


# --- Erfolge und Level -----------------------------------------------------------------

func erfolg_messwert(bedingung: Dictionary) -> float:
	match String(bedingung.get("typ", "")):
		"sterne_station":
			var hoechste: int = 0
			for id in Ids.ALL_STATIONS:
				var s: StationModel = kette.station(id)
				if s != null:
					hoechste = maxi(hoechste, s.sterne())
			return float(hoechste)
		"sterne_gesamt":
			return float(sterne_gesamt())
		"ziele_gesamt":
			return float(int(bogen.get("ziele", 0)))
		"bereiche_gesamt":
			return float(int(bogen.get("bereiche", 0)))
		"welten_fertig":
			return float(int(bogen.get("welten", 0)))
		"serie_tage":
			return float(geschenk.serientag)
		"crew_gekauft":
			return float(int(bogen.get("crew", 0)))
		"tagesaufgaben":
			return float(int(bogen.get("aufgaben", 0)))
		"momente":
			return float(int(bogen.get("momente", 0)))
		"stufen_gesamt":
			return float(stufen_gesamt())
		"durchlaeufe":
			return float(durchlaeufe)
	return 0.0


func _pruefe_erfolge() -> void:
	for eintrag in erfolge.definitionen():
		var d: Dictionary = eintrag as Dictionary
		var erfolg_id: String = String(d.get("id", ""))
		if erfolge.ist_erreicht(erfolg_id):
			continue
		var bedingung: Dictionary = d.get("bedingung", {}) as Dictionary
		if erfolg_messwert(bedingung) < float(bedingung.get("wert", 1.0)):
			continue
		erfolge.erreiche(erfolg_id)
		if not _stumm:
			bus.achievement_unlocked.emit(StringName(erfolg_id), float(d.get("bonus", 0.0)))


## Alle Erfolge: {id, erreicht, ist, soll, fortschritt, bonus}.
func erfolge_liste() -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for eintrag in erfolge.definitionen():
		var d: Dictionary = eintrag as Dictionary
		var bedingung: Dictionary = d.get("bedingung", {}) as Dictionary
		var soll: float = float(bedingung.get("wert", 1.0))
		var erreicht: bool = erfolge.ist_erreicht(String(d.get("id", "")))
		var ist: float = soll if erreicht else minf(erfolg_messwert(bedingung), soll)
		liste.append({
			"id": String(d.get("id", "")),
			"erreicht": erreicht,
			"ist": ist,
			"soll": soll,
			"fortschritt": clampf(ist / soll, 0.0, 1.0) if soll > 0.0 else 1.0,
			"bonus": float(d.get("bonus", 0.0)),
		})
	return liste


## Dauerfaktor aus Erfolgen (Bonus je Erfolg, heute 0) und Rang (+x % je Rang).
func erfolge_faktor() -> float:
	return erfolge.faktor() * erfolge.rang_faktor(spieler_level())


## Firmen-Punkte des ganzen Bogens: Ziel 1, Raumziel 3, Mission 5, Welt fertig 10.
func rang_punkte() -> int:
	return int(bogen.get("punkte", 0))


## Der Firmen-Rang (1 ... 30). Der alte Name `spieler_level` bleibt als Zugang.
func spieler_level() -> int:
	return erfolge.rang(rang_punkte())


func rang() -> int:
	return spieler_level()


## Rang und alles, was die Anzeige braucht. `level` ist der Rang (alter Schluessel).
func spieler_level_info() -> Dictionary:
	var r: int = spieler_level()
	return {
		"level": r, "rang": r, "max": erfolge.level_max,
		"ziele": int(bogen.get("ziele", 0)),
		"punkte": rang_punkte(),
		"name_id": rang_name_id(r),
		"freischaltung": erfolge.freischaltung_bei(r),
		"schwelle": erfolge.schwelle(r),
		"naechste_schwelle": erfolge.naechste_schwelle(r),
	}


## i18n-Schluessel des Rangnamens, z. B. "rang_name_4".
func rang_name_id(rang_nr: int) -> String:
	return "rang_name_%d" % rang_nr


## Ist ein Menue oder eine Mechanik durch den Rang frei? Unbekannte Merkmale
## sind frei. Gebaut wird das Gating in game/ (spaeteres Paket).
func ist_frei(merkmal: String) -> bool:
	return erfolge.ist_frei(merkmal, spieler_level())


func _pruefe_level() -> void:
	var jetzt: int = spieler_level()
	while _level_zuletzt < jetzt:
		_level_zuletzt += 1
		if not _stumm:
			bus.rank_up.emit(_level_zuletzt, StringName(rang_name_id(_level_zuletzt)))
			bus.player_level_up.emit(_level_zuletzt)


func _zaehle_welt_fertig() -> void:
	if _welt_gezaehlt:
		return
	_welt_gezaehlt = true
	bogen["welten"] = int(bogen.get("welten", 0)) + 1
	bogen["punkte"] = int(bogen.get("punkte", 0)) + erfolge.welt_fertig_punkte()
	_pruefe_level()
	_pruefe_erfolge()


## Beim Laden: Zaehler uebernehmen oder, bei einem Stand von VOR Schema 5, aus
## Welt und Zielen herleiten (fruehere Welten gelten als abgeschlossen).
func _uebernimm_bogen(stand: SaveData) -> void:
	var standard: Dictionary = {"ziele": 0, "bereiche": 0, "welten": 0, "crew": 0, "aufgaben": 0, "momente": 0, "punkte": 0, "schub": 0}
	if not stand.bogen.is_empty():
		for schluessel in standard.keys():
			standard[schluessel] = int(stand.bogen.get(schluessel, 0))
		bogen = standard
		_welt_gezaehlt = welt_abgeschlossen()
		# Stand von VOR dem Rang (K2 P2a): das Level war 1 + Ziele, jetzt zaehlen
		# Punkte. Ohne gespeicherte Punkte werden sie aus den Daten hergeleitet.
		if not stand.bogen.has("punkte"):
			bogen["punkte"] = _punkte_herleiten(stand, _welt_gezaehlt)
		return
	var ziele_summe: int = stand.ziele.size()
	var bereiche_summe: int = bereiche.anzahl_gekauft()
	var ziele_voll: int = 0
	var bereiche_voll: int = 0
	for i in range(welten.anzahl()):
		var daten: BalanceData = BalanceData.fuer_welt(welten.id(i))
		var z: int = daten.ziele.size() if daten != null else 0
		var b: int = daten.bereiche.size() if daten != null else 0
		ziele_voll += z
		bereiche_voll += b
		if i < welt_index:
			ziele_summe += z
			bereiche_summe += b
	standard["ziele"] = ziele_summe + durchlaeufe * ziele_voll
	standard["bereiche"] = bereiche_summe + durchlaeufe * bereiche_voll
	standard["welten"] = welt_index + durchlaeufe * welten.anzahl()
	standard["momente"] = int(stand.momente.get("angetippt", 0))
	bogen = standard
	_welt_gezaehlt = false
	bogen["punkte"] = _punkte_herleiten(stand, false)


## Rang-Punkte eines Altstands: frueher abgeschlossene Welten (und Durchlaeufe)
## zaehlen voll samt "Welt fertig", die aktuelle Welt nach den eingeloesten Zielen.
func _punkte_herleiten(stand: SaveData, aktuelle_welt_fertig: bool) -> int:
	var summe: int = 0
	var alle_welten: int = 0
	for i in range(welten.anzahl()):
		var daten: BalanceData = BalanceData.fuer_welt(welten.id(i))
		if daten == null:
			continue
		var welt_summe: int = 0
		for z in daten.ziele:
			var d: Dictionary = z as Dictionary
			if i < welt_index:
				welt_summe += erfolge.ziel_punkte(d)
			elif i == welt_index and stand.ziele.has(String(d.get("id", ""))):
				welt_summe += erfolge.ziel_punkte(d)
		if i < welt_index:
			welt_summe += erfolge.welt_fertig_punkte()
		elif i == welt_index and aktuelle_welt_fertig:
			welt_summe += erfolge.welt_fertig_punkte()
		summe += welt_summe
		var voll: int = erfolge.welt_fertig_punkte()
		for z in daten.ziele:
			voll += erfolge.ziel_punkte(z as Dictionary)
		alle_welten += voll
	return summe + durchlaeufe * alle_welten


# --- Auftragsbrett (Welle 2b) ----------------------------------------------------

## Ein Ziel als Auftragskarte: der Eintrag aus `_ziel_eintrag` plus `absender` und `satz`.
## `texte` ist der Abschnitt "auftragsbrett" des Themas (<ziel_id> -> {absender, satz});
## der Kern kennt keine Themen, die Oberflaeche reicht ihn herein. {} bei unbekannter ID.
func ziel_info(ziel_id: String, texte: Dictionary = {}) -> Dictionary:
	var d: Dictionary = ziele.definition(ziel_id)
	if d.is_empty():
		return {}
	var status: String = "offen"
	if ziele.ist_eingeloest(ziel_id):
		status = "erledigt"
	elif bedingung_erfuellt(d):
		status = "bereit"
	var eintrag: Dictionary = _ziel_eintrag(d, status)
	var eigen: Variant = texte.get(ziel_id, {})
	var t: Dictionary = eigen as Dictionary if eigen is Dictionary else {}
	eintrag["absender"] = String(t.get("absender", ""))
	eintrag["satz"] = String(t.get("satz", ""))
	return eintrag


## Bis zu `anzahl` Auftraege fuer die Leiste: erst die einloesbaren, dann die offenen
## in der Reihenfolge der Ziel-Liste.
func auftragskarten(anzahl: int, texte: Dictionary = {}) -> Array[Dictionary]:
	var bereit: Array[Dictionary] = []
	var rest: Array[Dictionary] = []
	for d in ziele.sichtbar():
		var info: Dictionary = ziel_info(String((d as Dictionary).get("id", "")), texte)
		if info.is_empty():
			continue
		if String(info["status"]) == "bereit":
			bereit.append(info)
		else:
			rest.append(info)
	bereit.append_array(rest)
	var ausgabe: Array[Dictionary] = []
	for e in bereit:
		if ausgabe.size() >= anzahl:
			break
		ausgabe.append(e)
	return ausgabe
