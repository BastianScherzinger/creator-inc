## Spielt eine Welt mit Abschluss "alles" bis 100 % durch (ADR-021).
##
## Der alte Simulator baut immer den Engpass aus. In einer Welt mit Ausstattung
## und Raeumen ist das zu wenig: Dort konkurrieren eine Stufe, ein Bildschirm
## und ein ganzer Raum um dasselbe Geld. Dieser Spieler waehlt deshalb nach
## AMORTISATION -- wie lange dauert es, bis sich ein Kauf bezahlt gemacht hat,
## einschliesslich der Zeit, bis man ihn sich leisten kann:
##
##     t = max(Preis - Kapital, 0) / Einkommen  +  Preis / Mehreinkommen
##
## Das ist ungefaehr, wie ein aufmerksamer Spieler denkt ("das lohnt sich
## schneller"), ohne ein Optimum zu sein, das niemand spielt.
##
## Bringt ein Kauf kein Mehreinkommen (eine Station, die nicht der Engpass ist),
## wird er erst gekauft, wenn nichts anderes mehr hilft -- und dann der
## billigste zuerst. Zum Abschluss muss am Ende ohnehin alles gekauft sein.
##
## Ziele werden eingeloest, sobald sie erfuellt sind (das tut jeder Spieler).
## Tipp-Momente und Werbung rechnet der Simulator NICHT mit: Die Zielzeit gilt
## fuer jemanden, der beides ignoriert.
class_name AbschlussSim
extends RefCounted

const SCHRITT: float = 0.25
const HOECHSTDAUER: float = 6.0 * 3600.0
const EINSTIEG: float = 900.0

## Zielkorridore je Welt (Sekunden). Messwerte, keine Balance: Sie stehen hier
## wie die Zielkurven im Hauptsimulator.
const ZIELE: Dictionary = {
	"zimmer": {
		"erster_kauf_max": 15.0,
		"erste_ausstattung_max": 90.0,
		"bereich_1": [180.0, 300.0],
		"bereich_3": [1200.0, 1800.0],
		"abschluss": [4500.0, 6600.0],
		"luecke_einstieg_max": 90.0,
		# Fuenf Minuten Sparen auf einen RAUM sind Absicht: Der Raum ist der
		# groesste Kauf der Welt, und auf ihn hinzuarbeiten ist selbst ein Ziel.
		# Laenger wird es zaeh -- das hat der Spieler-Blick von aussen gezeigt.
		"luecke_max": 360.0,   # 310 vor dem Design-Overhaul; gedaempfte Ziel-Belohnungen strecken das Sparen auf Raum 4
		"raum_luecke_max": 900.0,
		"raum5_bis_ende_min": 480.0,
	},
	# Alle Welten, die keinen eigenen Eintrag haben (NACHT_PLAN N02): Abschluss
	# in 60 bis 100 Minuten, derselbe Einstieg wie in Welt 1.
	"_standard": {
		"erster_kauf_max": 15.0,
		"erste_ausstattung_max": 90.0,
		"bereich_1": [120.0, 420.0],
		"abschluss": [3600.0, 6000.0],
		"luecke_einstieg_max": 90.0,
		"luecke_max": 330.0,
		# K3 B1 (Tempo-Loch): kein Raumabstand ueber 15 min, kein Endspurt unter 8 min.
		# Nur ausgegeben, nicht geprueft: Einkommen Raum 4 -> Ende (Ziel x100) und die
		# Luecke zwischen Grossereignissen (Ziel 12 min) -- siehe docs/neu/K3_PACING.md.
		"raum_luecke_max": 900.0,
		"raum5_bis_ende_min": 480.0,
	},
}

var kern: GameCore
var kaeufe: int = 0
var ereignisse: Dictionary = {}       ## name -> Sekunde
var luecke_einstieg: float = 0.0
var luecke_gesamt: float = 0.0
var luecke_gesamt_bei: float = 0.0
var _letzter_kauf: float = 0.0

## Design-Overhaul 15.10.: Kaeufe in den ersten zehn Minuten (Upgrades pro Minute).
const MESSFENSTER: float = 600.0
var kaeufe_fenster: int = 0
var crew_kaeufe: int = 0

## K3 B1: Grossereignisse (Raum, Crew, Auftrag, Rang) und Einkommensverlauf.
var grossereignisse: Array[float] = []
var kauf_log: Array = []               ## [Zeit, Art, Ziel, Preis, Einkommen danach] (welt_sim --kaeufe)
var verlauf: Array[float] = []        ## Einkommen/s jede volle Minute
var _naechste_probe: float = 60.0


## Mit `vorhandener` spielt der Simulator einen laufenden Kern -- so treibt die
## Durchspielprobe im echten Spiel (main.gd, --durchspielen) die Oberflaeche mit.
func _init(balance: BalanceData, welt_index: int, vorhandener: GameCore = null) -> void:
	kern = vorhandener if vorhandener != null else GameCore.new(balance, welt_index)
	kern.bus.rank_up.connect(func(_rang: int, _name_id: StringName) -> void:
		grossereignisse.append(kern.spielzeit))
	kern.bus.crew_hired.connect(func(_station: StringName, _rang: int) -> void:
		grossereignisse.append(kern.spielzeit))
	kern.bus.goal_completed.connect(func(ziel_id: StringName) -> void:
		if String(kern.ziele.definition(String(ziel_id)).get("kette", "")) == "auftrag":
			grossereignisse.append(kern.spielzeit))


## Einkommen an den Meilensteinen, fuer den Bericht.
var einkommen_bei: Dictionary = {}

## Neu bewertet wird nur, wenn sich etwas geaendert hat: nach einem Kauf, sobald
## das gemerkte Ziel bezahlbar ist, oder spaetestens alle zwei Sekunden (der
## Wartezeit-Anteil der Amortisation verschiebt sich mit dem Kapital). Vorher
## bewertete der Simulator alle zwanzig Kandidaten viermal pro Sekunde -- 80
## Sekunden fuer eine Welt, und validate.ps1 wurde spuerbar zaeh.
var _gemerkter_preis: float = -1.0
var _bis_neubewertung: int = 0


func laufen() -> void:
	while kern.spielzeit < HOECHSTDAUER:
		kern.tick(SCHRITT)
		_loese_ziele_ein()
		_tippe_fuer_ziele()
		if kern.spielzeit >= _naechste_probe:
			verlauf.append(kern.einkommen_pro_sekunde())
			_naechste_probe += 60.0
		if not ereignisse.has("erster_stern") and kern.sterne_gesamt() > 0:
			ereignisse["erster_stern"] = kern.spielzeit
		_bis_neubewertung -= 1
		if _gemerkter_preis >= 0.0 and kern.kapital < _gemerkter_preis and _bis_neubewertung > 0:
			continue
		var gekauft_in_diesem_takt: int = 0
		while gekauft_in_diesem_takt < 500 and _kaufe_bestes():
			gekauft_in_diesem_takt += 1
		_bis_neubewertung = 8
		if gekauft_in_diesem_takt > 0:
			_merke_luecke()
		if kern.welt_abgeschlossen():
			ereignisse["abschluss"] = kern.spielzeit
			einkommen_bei["abschluss"] = kern.einkommen_pro_sekunde()
			break
	# Die letzten Ziele werden im selben Moment erfuellt, in dem die Welt fertig
	# ist -- ein Spieler loest sie danach noch ein.
	# Es sind immer nur drei Ziele sichtbar; die Ketten dahinter rutschen nach.
	for i in range(80):
		var vorher: int = kern.ziele.anzahl_eingeloest()
		_loese_ziele_ein()
		if kern.ziele.anzahl_eingeloest() == vorher:
			break


func _loese_ziele_ein() -> void:
	for ziel in kern.ziele.sichtbar():
		kern.loese_ziel_ein(StringName(String(ziel.get("id", ""))))


## Die Blasen rechnet der Simulator sonst nicht mit. Steht aber ein Ziel vom Typ
## "momente" offen und sichtbar, tippt er die laufende Blase an -- wie jeder Spieler,
## der dieses Ziel erreichen will. Sonst bliebe es fuer immer ein Platzhalter.
func _tippe_fuer_ziele() -> void:
	if not kern.momente.laeuft():
		return
	for ziel in kern.ziele.sichtbar():
		if String(ziel.get("typ", "")) == "momente" and not GoalSystem.erfuellt(ziel, kern.messwert):
			kern.tippe_moment()
			return


func _merke_luecke() -> void:
	var luecke: float = kern.spielzeit - _letzter_kauf
	if _letzter_kauf < EINSTIEG:
		luecke_einstieg = maxf(luecke_einstieg, luecke)
	if luecke > luecke_gesamt:
		luecke_gesamt = luecke
		luecke_gesamt_bei = kern.spielzeit
	_letzter_kauf = kern.spielzeit


## Waehlt den Kauf mit der kuerzesten Amortisation und kauft ihn, wenn das Geld
## reicht. Gibt true zurueck, wenn gekauft wurde.
##
## Zwei Einkommen: das JETZIGE bestimmt, wie lange man auf einen Kauf wartet; das
## Einkommen, auf das die Welt zulaeuft (einkommen_ziel), bestimmt, was ein Kauf
## bringt. Ausser im Bestand (Welt 5) sind beide gleich.
func _kaufe_bestes() -> bool:
	var einkommen: float = maxf(kern.einkommen_pro_sekunde(), 0.0001)
	var basis: float = maxf(kern.einkommen_ziel(), 0.0001)
	var bester: Dictionary = {}
	var beste_zeit: float = INF
	var billigster: Dictionary = {}
	for kandidat in _kandidaten():
		var preis: float = float(kandidat["preis"])
		var mehr: float = _mehreinkommen(kandidat, basis)
		# Ein Kauf, der ein sichtbares Ziel erfuellt, ist um die Belohnung
		# billiger -- genau so rechnet ein Spieler, der auf die Ziele schaut.
		preis = maxf(preis - _zielbelohnung(kandidat, einkommen), preis * 0.1)
		if mehr > basis * 1.0e-9:
			var zeit: float = maxf(preis - kern.kapital, 0.0) / einkommen + preis / mehr
			if zeit < beste_zeit:
				beste_zeit = zeit
				bester = kandidat
		# Crew ist nie Pflicht fuer den Abschluss -- nur wahlweise, wenn sie sich lohnt.
		if String(kandidat["art"]) == "crew":
			continue
		if billigster.is_empty() or preis < float(billigster["preis"]):
			billigster = kandidat
	var wahl: Dictionary = bester if not bester.is_empty() else billigster
	if wahl.is_empty():
		_gemerkter_preis = INF
		return false
	if kern.kapital < float(wahl["preis"]):
		# Auf den grossen Kauf warten -- aber nicht tatenlos. Was sich bezahlt
		# gemacht hat, BEVOR das Geld fuer den grossen Kauf da ist, kauft auch ein
		# Mensch zwischendurch. (Die neun Minuten Sparen auf das freie Zimmer hat
		# diese Regel NICHT verkuerzt -- dort gab es wirklich nichts Besseres. Die
		# Loesung war ein billigerer Raum, siehe zimmer.json.)
		var warten: float = (float(wahl["preis"]) - kern.kapital) / einkommen
		var zwischendurch: Dictionary = _bester_bezahlbarer(basis, warten)
		if not zwischendurch.is_empty():
			_gemerkter_preis = -1.0
			return _kaufe(zwischendurch)
		_gemerkter_preis = float(wahl["preis"])
		return false
	_gemerkter_preis = -1.0
	return _kaufe(wahl)


## Der bezahlbare Kauf mit der kuerzesten Amortisation, sofern er sich innerhalb
## von `frist` Sekunden bezahlt macht.
func _bester_bezahlbarer(einkommen: float, frist: float) -> Dictionary:
	var bester: Dictionary = {}
	var beste_zeit: float = frist
	for kandidat in _kandidaten():
		var preis: float = float(kandidat["preis"])
		if preis > kern.kapital:
			continue
		var mehr: float = _mehreinkommen(kandidat, einkommen)
		if mehr <= einkommen * 1.0e-9:
			continue
		var zeit: float = preis / mehr
		if zeit < beste_zeit:
			beste_zeit = zeit
			bester = kandidat
	return bester


func _kandidaten() -> Array[Dictionary]:
	var liste: Array[Dictionary] = []
	for id in Ids.ALL_STATIONS:
		var station: StationModel = kern.kette.station(id)
		if station == null or not station.freigeschaltet:
			continue
		if station.kann_ausbauen():
			liste.append({"art": "stufe", "station": id, "preis": station.naechste_kosten()})
		for p in station.ausstattung:
			if not p.ist_max() and p.freigegeben(station.stufe):
				liste.append({"art": "platz", "station": id, "platz": p.id, "preis": p.naechste_kosten()})
		# Crew kauft der Simulator nur nebenbei (bezahlbar), er spart nicht darauf.
		if kern.crew_frei(id) and not kern.crew.ist_max(id) and kern.crew.kosten_naechster(id) <= kern.kapital:
			liste.append({"art": "crew", "station": id, "preis": kern.crew.kosten_naechster(id)})
	for bereich_id in kern.bereiche.ids():
		if kern.bereiche.verfuegbar(bereich_id):
			liste.append({"art": "bereich", "bereich": bereich_id, "preis": kern.bereiche.kosten(bereich_id)})
	# Die Obergrenze (Welt 2) faellt nur durch den Umbau -- ein Kauf wie jeder andere.
	if kern.limit_gilt():
		liste.append({"art": "umbau", "preis": kern.umbau_kosten()})
	return liste


## Wie viel mehr pro Sekunde kaeme herein? Probeweise anwenden, messen, zuruecknehmen.
##
## EINE Ausnahme macht den Unterschied zwischen einem Spieler und einer
## Endlosschleife: Stehen zwei Kettenglieder GLEICHAUF am Engpass, bringt jedes
## einzeln exakt null -- das andere bremst sofort. Der erste Anlauf dieses
## Simulators hat deshalb nach vier Minuten aufgehoert zu kaufen und drei
## Stunden gespart. Ein Glied, das AM Engpass steht, zaehlt deshalb mit seiner
## eigenen Verbesserung, als waere es allein.
func _mehreinkommen(kandidat: Dictionary, einkommen: float) -> float:
	var art: String = String(kandidat["art"])
	if art == "bereich":
		return _mehreinkommen_bereich(kandidat["bereich"] as StringName, einkommen)
	if art == "umbau":
		kern.fortschritt.setze_frei(Ids.UNLOCK_UMBAU)
		var ohne_grenze: float = kern.einkommen_ziel()
		kern.fortschritt.freigeschaltet.erase(String(Ids.UNLOCK_UMBAU))
		return ohne_grenze - einkommen
	var station: StationModel = kern.kette.station(kandidat["station"] as StringName)
	var p: EquipmentSlot = null
	if art == "platz":
		p = station.platz(kandidat["platz"] as StringName)
	var vorher_station: float = station.durchsatz()
	var crew_verhaeltnis: float = 1.0
	if art == "crew":
		crew_verhaeltnis = kern.crew.faktor_bei(station.id, kern.crew.rang(station.id) + 1) \
			/ kern.crew.faktor(station.id)
		station.extern_faktor *= crew_verhaeltnis
		kern._aktualisiere_transport()
	else:
		_probe(station, p, 1)
	var danach: float = kern.einkommen_ziel()
	var nachher_station: float = station.durchsatz()
	if art == "crew":
		station.extern_faktor /= crew_verhaeltnis
		kern._aktualisiere_transport()
	else:
		_probe(station, p, -1)
	var gemessen: float = danach - einkommen
	var am_engpass: bool = vorher_station <= _engpass_durchsatz() * 1.001
	# An der harten Obergrenze hilft auch der Engpass nicht -- dort zaehlt nur,
	# was wirklich ankommt. Sonst baut der Simulator ewig gegen die Wand.
	if kern.limit_gilt() and kern.limit_auslastung() >= 0.999:
		am_engpass = false
	if Ids.CHAIN.has(station.id) and vorher_station > 0.0 and am_engpass:
		return maxf(gemessen, einkommen * (nachher_station / vorher_station - 1.0))
	return gemessen


## Welche Belohnung wuerde dieser Kauf freischalten? Probeweise anwenden und
## die sichtbaren, noch nicht erfuellten Ziele pruefen.
func _zielbelohnung(kandidat: Dictionary, einkommen: float) -> float:
	var offen: Array[Dictionary] = []
	for ziel in kern.ziele.sichtbar():
		if not GoalSystem.erfuellt(ziel, kern.messwert):
			offen.append(ziel)
	if offen.is_empty():
		return 0.0
	var art: String = String(kandidat["art"])
	var summe: float = 0.0
	if art == "crew":
		return 0.0
	if art == "umbau":
		for ziel in offen:
			if String(ziel.get("typ", "")) == "freigeschaltet" and String(ziel.get("unlock", "")) == String(Ids.UNLOCK_UMBAU):
				summe += _belohnung(ziel, einkommen)
		return summe
	if art == "bereich":
		for ziel in offen:
			var passt: bool = String(ziel.get("bereich", "")) == String(kandidat["bereich"])
			if String(ziel.get("typ", "")) == "bereich" and passt:
				summe += _belohnung(ziel, einkommen)
		return summe
	var station: StationModel = kern.kette.station(kandidat["station"] as StringName)
	var p: EquipmentSlot = station.platz(kandidat["platz"] as StringName) if art == "platz" else null
	_probe(station, p, 1)
	for ziel in offen:
		if GoalSystem.erfuellt(ziel, kern.messwert):
			summe += _belohnung(ziel, einkommen)
	_probe(station, p, -1)
	return summe


func _belohnung(ziel: Dictionary, einkommen: float) -> float:
	return maxf(einkommen * float(ziel.get("belohnung_sekunden", 0.0)) 		* kern.balance.ziel_belohnung_faktor, float(ziel.get("belohnung_minimum", 0.0)))


func _probe(station: StationModel, p: EquipmentSlot, richtung: int) -> void:
	if p != null:
		p.stufe += richtung
	else:
		station.stufe += richtung
	kern._aktualisiere_transport()


func _engpass_durchsatz() -> float:
	var minimum: float = INF
	for id in Ids.CHAIN:
		var s: StationModel = kern.kette.station(id)
		if s != null:
			minimum = minf(minimum, s.durchsatz())
	return minimum


func _mehreinkommen_bereich(bereich_id: StringName, einkommen: float) -> float:
	var bonus: Dictionary = kern.bereiche.bonus(bereich_id)
	var gewinn: float = 0.0
	if not bonus.is_empty():
		var faktor: float = float(bonus.get("faktor", 1.0))
		var ziel: String = String(bonus.get("ziel", AreaSystem.BONUS_ALLE))
		var betroffen: Array[StationModel] = []
		for id in Ids.ALL_STATIONS:
			if ziel == AreaSystem.BONUS_ALLE or ziel == String(id):
				betroffen.append(kern.kette.station(id))
		for s in betroffen:
			s.extern_faktor *= faktor
		kern._aktualisiere_transport()
		gewinn = kern.einkommen_ziel() - einkommen
		for s in betroffen:
			s.extern_faktor /= faktor
		kern._aktualisiere_transport()
	var unlock_id: StringName = kern.bereiche.schaltet_frei(bereich_id)
	var station_id: StringName = GameCore._station_zu_freischaltung(unlock_id)
	if station_id != &"":
		var station: StationModel = kern.kette.station(station_id)
		var war_frei: bool = station.freigeschaltet
		var war_stufe: int = station.stufe
		station.freigeschaltet = true
		station.stufe = maxi(station.stufe, 1)
		kern._aktualisiere_transport()
		# Eine Station, die eine ganze Reihe weiterer Kaeufe erst ermoeglicht,
		# ist mehr wert als ihre erste Stufe. Der Faktor 5 bildet das grob ab --
		# ohne ihn laesst der Simulator den Flur liegen, weil eine Stufe Upload
		# allein nur zwei Prozent bringt.
		gewinn += (kern.einkommen_ziel() - einkommen) * 5.0
		station.freigeschaltet = war_frei
		station.stufe = war_stufe
		kern._aktualisiere_transport()
	return gewinn


func _kaufe(kandidat: Dictionary) -> bool:
	var ok: bool = false
	match String(kandidat["art"]):
		"stufe":
			ok = kern.upgrade_station(kandidat["station"] as StringName)
			if ok and not ereignisse.has("erster_kauf"):
				ereignisse["erster_kauf"] = kern.spielzeit
		"platz":
			ok = kern.kaufe_ausstattung(kandidat["station"] as StringName, kandidat["platz"] as StringName)
			if ok and not ereignisse.has("erste_ausstattung"):
				ereignisse["erste_ausstattung"] = kern.spielzeit
		"bereich":
			var bereich_id: StringName = kandidat["bereich"] as StringName
			ok = kern.kaufe_bereich(bereich_id)
			if ok:
				ereignisse[String(bereich_id)] = kern.spielzeit
				grossereignisse.append(kern.spielzeit)
				einkommen_bei[String(bereich_id)] = kern.einkommen_pro_sekunde()
		"umbau":
			ok = kern.kaufe_umbau()
			if ok:
				ereignisse["umbau"] = kern.spielzeit
		"crew":
			ok = kern.kaufe_crew(kandidat["station"] as StringName)
			if ok:
				crew_kaeufe += 1
				if not ereignisse.has("erste_crew"):
					ereignisse["erste_crew"] = kern.spielzeit
	if ok:
		kauf_log.append([kern.spielzeit, String(kandidat["art"]),
			String(kandidat.get("platz", kandidat.get("station", kandidat.get("bereich", "")))).replace("station_", ""),
			float(kandidat["preis"]), kern.einkommen_pro_sekunde()])
		kaeufe += 1
		if kern.spielzeit <= MESSFENSTER:
			kaeufe_fenster += 1
		if not ereignisse.has("erster_kauf"):
			ereignisse["erster_kauf"] = kern.spielzeit
	return ok


## Prueft die Messwerte gegen die Zielkorridore. Gibt eine Liste von Verstoessen zurueck.
func pruefe(welt_id: String) -> PackedStringArray:
	var verstoesse: PackedStringArray = []
	var z: Dictionary = (ZIELE.get(welt_id, ZIELE["_standard"]) as Dictionary).duplicate()
	# Korridor je Welt aus den Daten (balance/<welt>.json -> ziel_minuten, Minuten).
	var zm: Array = kern.balance.ziel_minuten
	if zm.size() == 2:
		z["abschluss"] = [float(zm[0]) * 60.0, float(zm[1]) * 60.0]
	if not ereignisse.has("abschluss"):
		verstoesse.append("Welt in %d Stunden nicht abgeschlossen" % int(HOECHSTDAUER / 3600.0))
		return verstoesse
	for schluessel in z.keys():
		var soll: Variant = z[schluessel]
		match String(schluessel):
			"erster_kauf_max", "erste_ausstattung_max":
				var name: String = String(schluessel).trim_suffix("_max")
				if float(ereignisse.get(name, INF)) > float(soll):
					verstoesse.append("%s bei %s (Grenze %s)" % [name, _zeit(ereignisse.get(name, -1.0)), _zeit(soll)])
			"upgrades_min_10_min":
				if upgrades_pro_minute() < float(soll):
					verstoesse.append("Upgrades/Min in den ersten 10 Min %.2f (Minimum %.1f)" % [
						upgrades_pro_minute(), float(soll)])
			"luecke_einstieg_max":
				if luecke_einstieg > float(soll):
					verstoesse.append("Kaufluecke im Einstieg %.0fs (Grenze %.0fs)" % [luecke_einstieg, float(soll)])
			"raum_luecke_max":
				var lr: Array = raum_luecke()
				if float(lr[0]) > float(soll):
					verstoesse.append("Raumluecke %s bei %s (Grenze %s)" % [_zeit(lr[0]), _zeit(lr[1]), _zeit(soll)])
			"raum5_bis_ende_min":
				if raum5_bis_ende() < float(soll):
					verstoesse.append("letzter Raum bis Ende %s (Minimum %s)" % [_zeit(raum5_bis_ende()), _zeit(soll)])
			"raum4_sprung_max":
				if raum4_sprung() > float(soll):
					verstoesse.append("Einkommen Raum 4 bis Ende x%.0f (Grenze x%.0f)" % [raum4_sprung(), float(soll)])
			"gross_luecke_max":
				var lg: Array = gross_luecke()
				if float(lg[0]) > float(soll):
					verstoesse.append("Grossereignis-Luecke %s bei %s (Grenze %s)" % [_zeit(lg[0]), _zeit(lg[1]), _zeit(soll)])
			"luecke_max":
				if luecke_gesamt > float(soll):
					verstoesse.append("Kaufluecke %.0fs bei %s (Grenze %.0fs)" % [luecke_gesamt, _zeit(luecke_gesamt_bei), float(soll)])
			_:
				var bereich: Array = soll as Array
				var ist: float = float(ereignisse.get(String(schluessel), -1.0))
				if ist < float(bereich[0]) or ist > float(bereich[1]):
					verstoesse.append("%s bei %s (Ziel %s bis %s)" % [
						schluessel, _zeit(ist), _zeit(bereich[0]), _zeit(bereich[1])])
	if kern.nachrichten.empfangen().size() < kern.balance.nachrichten.size():
		verstoesse.append("nur %d von %d Nachrichten zugestellt" % [
			kern.nachrichten.empfangen().size(), kern.balance.nachrichten.size()])
	# Ziele vom Typ "momente" kann dieser Spieler nicht erfuellen -- er tippt nie
	# auf Blasen. Alle anderen muessen bis zum Abschluss erreichbar sein; ein
	# Ziel, das niemand erreichen kann, blockiert dauerhaft einen der drei Plaetze.
	var erreichbar: int = 0
	for eintrag in kern.balance.ziele:
		if String((eintrag as Dictionary).get("typ", "")) != "momente":
			erreichbar += 1
	var eingeloest_ohne_momente: int = 0
	for eintrag in kern.balance.ziele:
		var d: Dictionary = eintrag as Dictionary
		if String(d.get("typ", "")) != "momente" and kern.ziele.ist_eingeloest(String(d.get("id", ""))):
			eingeloest_ohne_momente += 1
	if eingeloest_ohne_momente < erreichbar:
		verstoesse.append("nur %d von %d erreichbaren Zielen eingeloest" % [
			eingeloest_ohne_momente, erreichbar])
	return verstoesse


## Groesste Luecke zwischen zwei Raumkaeufen: [Sekunden, Zeitpunkt des spaeteren Kaufs].
func raum_luecke() -> Array:
	var zeiten: Array[float] = []
	for name in ereignisse.keys():
		if String(name).begins_with("bereich_"):
			zeiten.append(float(ereignisse[name]))
	zeiten.sort()
	var groesste: float = 0.0
	var bei: float = 0.0
	for i in range(1, zeiten.size()):
		if zeiten[i] - zeiten[i - 1] > groesste:
			groesste = zeiten[i] - zeiten[i - 1]
			bei = zeiten[i]
	return [groesste, bei]


## Sekunden vom letzten Raumkauf bis zum Abschluss (Endspurt).
func raum5_bis_ende() -> float:
	var letzter: float = 0.0
	for name in ereignisse.keys():
		if String(name).begins_with("bereich_"):
			letzter = maxf(letzter, float(ereignisse[name]))
	return float(ereignisse.get("abschluss", 0.0)) - letzter


## Einkommen am Ende geteilt durch das Einkommen direkt nach Raum 4.
func raum4_sprung() -> float:
	var vor: float = float(einkommen_bei.get("bereich_4", 0.0))
	if vor <= 0.0:
		return 0.0
	return float(einkommen_bei.get("abschluss", 0.0)) / vor


## Groesste Luecke zwischen zwei Grossereignissen (Raum, Crew, Auftrag, Rang),
## vom Start bis zum Abschluss: [Sekunden, Zeitpunkt des spaeteren Ereignisses].
func gross_luecke() -> Array:
	var zeiten: Array[float] = [0.0]
	zeiten.append_array(grossereignisse)
	zeiten.append(float(ereignisse.get("abschluss", 0.0)))
	zeiten.sort()
	var groesste: float = 0.0
	var bei: float = 0.0
	for i in range(1, zeiten.size()):
		if zeiten[i] - zeiten[i - 1] > groesste:
			groesste = zeiten[i] - zeiten[i - 1]
			bei = zeiten[i]
	return [groesste, bei]


## Upgrades pro Minute in den ersten zehn Minuten (Kaeufe aller Art).
func upgrades_pro_minute() -> float:
	return float(kaeufe_fenster) / (MESSFENSTER / 60.0)


func bericht() -> void:
	var reihenfolge: Array = ereignisse.keys()
	reihenfolge.sort_custom(func(a: Variant, b: Variant) -> bool:
		return float(ereignisse[a]) < float(ereignisse[b]))
	for name in reihenfolge:
		var dazu: String = ""
		if einkommen_bei.has(name):
			dazu = "   (Einkommen danach %.0f/s)" % float(einkommen_bei[name])
		print("  %-20s %s%s" % [name, _zeit(ereignisse[name]), dazu])
	print("  Kaeufe gesamt:       %d (davon Crew %d)" % [kaeufe, crew_kaeufe])
	print("  Messgroessen:        erstes Upgrade %s · Upgrades/Min (Min 1-10) %.2f · Raum 2 %s · erster Stern %s" % [
		_zeit(ereignisse.get("erster_kauf", -1.0)), upgrades_pro_minute(),
		_zeit(ereignisse.get("bereich_1", -1.0)), _zeit(ereignisse.get("erster_stern", -1.0))])
	print("  Einkommen am Ende:   %.0f/s" % kern.einkommen_pro_sekunde())
	print("  Verdient in der Welt: %.0f" % kern.welt_verdient)
	print("  Kaufluecke Einstieg: %.0fs · gesamt %.0fs bei %s" % [
		luecke_einstieg, luecke_gesamt, _zeit(luecke_gesamt_bei)])
	var lr: Array = raum_luecke()
	var lg: Array = gross_luecke()
	print("  Pacing:              Raumluecke max %s (bei %s) · Raum 5 -> Ende %s · Einkommen Raum 4 -> Ende x%.0f · Grossereignis-Luecke max %s (bei %s)" % [
		_zeit(lr[0]), _zeit(lr[1]), _zeit(raum5_bis_ende()), raum4_sprung(), _zeit(lg[0]), _zeit(lg[1])])
	print("  Ziele %d/%d · Nachrichten %d/%d" % [
		kern.ziele.anzahl_eingeloest(), kern.ziele.anzahl(),
		kern.nachrichten.empfangen().size(), kern.balance.nachrichten.size()])


static func _zeit(sekunden: Variant) -> String:
	var s: int = int(float(sekunden))
	if s < 0:
		return "-"
	return "%d:%02d" % [s / 60, s % 60]
