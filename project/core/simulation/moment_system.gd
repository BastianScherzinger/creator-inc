## Tipp-Momente: etwas Grosses in der Welt, das man antippen kann (ADR-021, K3 B2).
##
## Unvorhersehbares haelt die Aufmerksamkeit. Deshalb kommen die Momente zu
## zufaelligen Zeiten -- aber OHNE Einsatz und OHNE Strafe: Wer nicht tippt,
## verliert nichts, der Moment verschwindet leise. Kein Zaehler sagt "verpasst".
## Das ist die Grenze zwischen variabler Belohnung und Gluecksspielmechanik,
## und sie verlaeuft genau hier.
##
## Drei Arten, abwechselnd, damit es nach dem zehnten Mal keine Routine wird:
##   - ART_KISTE: eine Lieferung steht an der Tuer -- Tipp = Geld (Moment-Belohnung).
##   - ART_STAPEL: am Engpass stapelt sich die Arbeit -- Tipp raeumt ab und gibt
##     einen kurzen Schub. KEIN Geld: Die Teile im Stapel sind Darstellung, ihr
##     Ertrag ist laengst gezaehlt. Zweimal zahlen waere doppeltes Geld.
##   - ART_BLASE: die seltene grosse Blase ueber einer Station.
##
## Offline gibt es keine Momente: Sie belohnen Anwesenheit, nicht Abwesenheit.
## Der Kern ruft `tick` deshalb nur im laufenden Spiel auf.
class_name MomentSystem
extends RefCounted

const ART_BLASE: StringName = &"blase"
const ART_KISTE: StringName = &"kiste"
const ART_STAPEL: StringName = &"stapel"
## K6 2c: Die Kasse am Ende der Kette ist kein Zufallsmoment, sondern ein
## wachsender Stapel; hier nur der Name fuer Bericht und Darstellung.
const ART_KASSE: StringName = &"kasse"
## Kandidat "Kiste": keine Station, sondern ein fester Ort der Karte. Steht er in
## den Kandidaten, darf eine Lieferung kommen.
const KISTE: StringName = &"kiste"

var aktiv_erlaubt: bool = false
var abstand_min: float = 40.0
var abstand_max: float = 90.0
var dauer: float = 20.0
## K4: In den ersten Spielsekunden kommen Momente dichter (der Einstieg hatte nur 0,4-0,6
## Belohnungen je Minute, Ziel >= 2). 0 = keine Frueh-Phase.
var frueh_bis_s: float = 0.0
var frueh_abstand_min: float = 0.0
var frueh_abstand_max: float = 0.0
var belohnung_sekunden: float = 30.0
var belohnung_minimum: float = 5.0
## Einkommen in Sekunden fuer die Lieferung (Grundstufe). Fehlt der Schluessel,
## gilt belohnung_sekunden.
var kiste_sekunden: float = 30.0
## Wie lange der Schub nach einem abgeraeumten Stapel laeuft. Fehlt der
## Schluessel, gilt die Dauer eines Moments.
var stapel_schub_sekunden: float = 20.0

## Die Kasse (K6 2c): Geld liegt als Stapel am Ende der Kette. `kasse_fuell` waechst
## mit der Spielzeit (nur live, nie offline), ab `kasse_ab_s` ist sie antippbar,
## bei `kasse_max_s` ist sie voll. Der Tipp zahlt `kasse_anteil` des Einkommens je
## gesammelter Sekunde -- ueber die Zeit gerechnet also hoechstens dieser Anteil
## des Einkommens (kleiner Bonus, nie Pflicht, nie Verlust: der Kern bucht das
## Einkommen weiter selbst).
var kasse_ab_s: float = 20.0
var kasse_max_s: float = 90.0
var kasse_anteil: float = 0.018
var kasse_fuell: float = 0.0
var kasse_gesamt: int = 0

## Manchmal ist ein Moment GROSS: ein Clip, der durch die Decke geht.
##
## Ein seltener grosser Moment haelt die Aufmerksamkeit -- ohne Einsatz: Wer
## tippt, bekommt mehr, wer nicht tippt, verliert nichts.
var gross_chance: float = 0.0
var gross_sekunden: float = 0.0

## Ist der laufende Moment ein grosser?
var gross: bool = false
## Welche Art laeuft gerade (leer, wenn keiner)?
var art: StringName = &""
## Die Art des zuletzt angetippten Moments -- die Darstellung waehlt danach ihren Text.
var letzte_art: StringName = &""

## Die Station, um die es geht -- leer, wenn kein Moment laeuft. Bei der Kiste
## die Station, fuer die geliefert wird; beim Stapel der Engpass.
var station: StringName = &""
var rest: float = 0.0
var angetippt_gesamt: int = 0
var stapel_gesamt: int = 0

## Wo sich gerade Arbeit stapeln darf (der Engpass) -- leer = kein Stapel-Moment.
## Der Kern setzt es zusammen mit den Kandidaten.
var stapel_ziel: StringName = &""

var _bis_naechster: float = 0.0
var _laufzeit: float = 0.0
var _arten_zaehler: int = 0
var _erzwungen: StringName = &""
var _zufall := RandomNumberGenerator.new()


func _init(params: Dictionary = {}, startwert: int = 20260911) -> void:
	aktiv_erlaubt = bool(params.get("aktiv", false))
	abstand_min = float(params.get("abstand_min", abstand_min))
	abstand_max = maxf(float(params.get("abstand_max", abstand_max)), abstand_min)
	dauer = float(params.get("dauer", dauer))
	frueh_bis_s = maxf(float(params.get("frueh_bis_s", 0.0)), 0.0)
	frueh_abstand_min = float(params.get("frueh_abstand_min", abstand_min))
	frueh_abstand_max = maxf(float(params.get("frueh_abstand_max", abstand_max)), frueh_abstand_min)
	belohnung_sekunden = float(params.get("belohnung_sekunden", belohnung_sekunden))
	belohnung_minimum = float(params.get("belohnung_minimum", belohnung_minimum))
	kiste_sekunden = float(params.get("kiste_sekunden", belohnung_sekunden))
	stapel_schub_sekunden = float(params.get("stapel_schub_sekunden", dauer))
	kasse_ab_s = maxf(float(params.get("kasse_ab_s", kasse_ab_s)), 0.0)
	kasse_max_s = maxf(float(params.get("kasse_max_s", kasse_max_s)), kasse_ab_s)
	kasse_anteil = clampf(float(params.get("kasse_anteil", kasse_anteil)), 0.0, 0.02)
	gross_chance = clampf(float(params.get("gross_chance", 0.0)), 0.0, 1.0)
	gross_sekunden = float(params.get("gross_sekunden", 0.0))
	_zufall.seed = startwert
	_bis_naechster = naechster_abstand()


## Wartezeit bis zum naechsten Moment: in der Frueh-Phase kuerzer.
func naechster_abstand() -> float:
	if _laufzeit < frueh_bis_s:
		return _zufall.randf_range(frueh_abstand_min, frueh_abstand_max)
	return _zufall.randf_range(abstand_min, abstand_max)


func laeuft() -> bool:
	return station != &""


func ist_kiste() -> bool:
	return laeuft() and art == ART_KISTE


func ist_stapel() -> bool:
	return laeuft() and art == ART_STAPEL


## Prueft-Schalter der Vorschau: Der naechste Moment kommt sofort und hat diese Art.
func erzwinge(gewuenscht: StringName) -> void:
	_erzwungen = gewuenscht
	if not laeuft():
		_bis_naechster = 0.0


## Laesst Zeit vergehen. `kandidaten` sind die Stationen, ueber denen ein Moment
## erscheinen darf (freigeschaltet, arbeitend), plus KISTE, wenn eine Lieferung
## kommen darf.
func tick(sekunden: float, kandidaten: Array[StringName], bus: EventBus = null) -> void:
	if not aktiv_erlaubt or sekunden <= 0.0:
		return
	_laufzeit += sekunden
	# Die Kasse fuellt sich, solange irgendwo etwas arbeitet (Kandidaten da).
	if not kandidaten.is_empty():
		kasse_fuell = minf(kasse_fuell + sekunden, kasse_max_s)
	if laeuft():
		rest -= sekunden
		if rest <= 0.0:
			var war: StringName = station
			_beende()
			if bus != null:
				bus.moment_ended.emit(war, false, 0.0)
		return
	_bis_naechster -= sekunden
	var stationen: Array[StringName] = []
	for k in kandidaten:
		if k != KISTE:
			stationen.append(k)
	if _bis_naechster > 0.0 or stationen.is_empty():
		return
	station = stationen[_zufall.randi_range(0, stationen.size() - 1)]
	gross = gross_chance > 0.0 and _zufall.randf() < gross_chance
	art = _waehle_art(kandidaten.has(KISTE), stationen)
	if art == ART_STAPEL:
		station = stapel_ziel
	if art != ART_BLASE:
		gross = false
	_erzwungen = &""
	rest = dauer
	if bus != null:
		bus.moment_appeared.emit(station, rest)


## Kiste und Stapel wechseln sich ab (Kiste zuerst); der grosse Moment bleibt
## eine Blase ueber der Station. Ohne Kiste und Stapel: wie frueher die Blase.
func _waehle_art(kiste_erlaubt: bool, stationen: Array[StringName]) -> StringName:
	var stapel_erlaubt: bool = stapel_ziel != &"" and stationen.has(stapel_ziel)
	if _erzwungen == ART_KISTE and kiste_erlaubt:
		return ART_KISTE
	if _erzwungen == ART_STAPEL and stapel_erlaubt:
		return ART_STAPEL
	if gross:
		return ART_BLASE
	var arten: Array[StringName] = []
	if kiste_erlaubt:
		arten.append(ART_KISTE)
	if stapel_erlaubt:
		arten.append(ART_STAPEL)
	if arten.is_empty():
		return ART_BLASE
	var gewaehlt: StringName = arten[_arten_zaehler % arten.size()]
	_arten_zaehler += 1
	return gewaehlt


## Tippt eine laufende Kiste oder Blase an. Gibt die Belohnung zurueck
## (0 = nichts zum Antippen). Ein Stapel zahlt hier nie -- er geht ueber
## stapel_antippen.
##
## `sekunden` > 0 ersetzt die Grundbelohnung: die zweite Stufe (z. B. mit
## Werbung) dockt hier an, ohne dass sich die Regel aendert.
func antippen(einkommen_pro_sekunde: float, bus: EventBus = null, sekunden: float = -1.0) -> float:
	if not laeuft() or art == ART_STAPEL:
		return 0.0
	var war: StringName = station
	var betrag: float = belohnung(einkommen_pro_sekunde, sekunden)
	letzte_art = art
	_beende()
	angetippt_gesamt += 1
	if bus != null:
		bus.moment_ended.emit(war, true, betrag)
	return betrag


## Was ein Tipp auf den laufenden Moment bringen wuerde (ohne ihn zu verbrauchen).
func belohnung(einkommen_pro_sekunde: float, sekunden: float = -1.0) -> float:
	var s: float = sekunden
	if s <= 0.0:
		if gross:
			s = gross_sekunden
		elif art == ART_KISTE:
			s = kiste_sekunden
		else:
			s = belohnung_sekunden
	return maxf(einkommen_pro_sekunde * s, belohnung_minimum)


## Raeumt den Stapel an `station_id` ab. Gibt die Schubdauer in Sekunden zurueck
## (0 = dort liegt gerade kein Stapel zum Antippen).
func stapel_antippen(station_id: StringName, bus: EventBus = null) -> float:
	if not ist_stapel() or station_id != station:
		return 0.0
	letzte_art = art
	_beende()
	angetippt_gesamt += 1
	stapel_gesamt += 1
	if bus != null:
		bus.moment_ended.emit(station_id, true, 0.0)
	return stapel_schub_sekunden


## Ist die Kasse voll genug zum Antippen?
func kasse_bereit() -> bool:
	return aktiv_erlaubt and kasse_fuell >= kasse_ab_s and kasse_ab_s > 0.0


## Was ein Tipp jetzt brachte (ohne ihn zu verbrauchen).
func kasse_betrag(einkommen_pro_sekunde: float) -> float:
	return maxf(einkommen_pro_sekunde, 0.0) * kasse_fuell * kasse_anteil


## Leert die Kasse und gibt den Bonus zurueck (0 = noch nicht antippbar). Der
## Aufrufer bucht ihn; hier wird nur gerechnet.
func kasse_antippen(einkommen_pro_sekunde: float, _bus: EventBus = null) -> float:
	if not kasse_bereit():
		return 0.0
	var betrag: float = kasse_betrag(einkommen_pro_sekunde)
	kasse_fuell = 0.0
	kasse_gesamt += 1
	return betrag


func _beende() -> void:
	station = &""
	art = &""
	rest = 0.0
	gross = false
	_bis_naechster = naechster_abstand()


func to_dict() -> Dictionary:
	return {"angetippt": angetippt_gesamt}


func apply_dict(daten: Dictionary) -> void:
	angetippt_gesamt = maxi(int(daten.get("angetippt", 0)), 0)
