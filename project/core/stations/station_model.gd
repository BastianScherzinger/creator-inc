## Eine einzelne Station der Kette.
##
## Kennt ihre Stufe, ihre Kosten- und Ertragsparameter und ihren Durchsatz.
## Sie weiss nichts ueber Darstellung, Meshes oder Szenen -- und nichts
## darueber, welche der anderen Stationen gerade der Engpass ist. Das ist
## Aufgabe der ProductionChain.
class_name StationModel
extends RefCounted

var id: StringName
var stufe: int = 0

## Balance-Parameter, kommen aus data/balance/*.json (ADR-005).
var basis_kosten: float = 25.0
var wachstum: float = 1.16
var basis_durchsatz: float = 1.0
var multiplikator: float = 1.0

## Meilenstein-Multiplikatoren -- ohne sie stirbt das Spiel.
##
## Die Kosten wachsen exponentiell, ein rein linearer Ertrag kommt dagegen
## nicht an: Bei Stufe 100 kostet eine weitere Stufe sonst sieben Tage
## Wartezeit. Alle `meilenstein_intervall` Stufen verdoppelt sich deshalb der
## Ertrag (Genre-Standard). Damit waechst auch der Ertrag exponentiell, nur
## langsamer als die Kosten -- die Progression bleibt spuerbar, ohne je
## hoffnungslos zu werden.
##
## Der Balance-Simulator hat diesen Fehler aufgedeckt (TASK 012).
var meilenstein_intervall: int = 15
var meilenstein_faktor: float = 2.0

## Erst freigeschaltete Stationen zaehlen im Durchsatz mit.
var freigeschaltet: bool = true

## Hoechste Stufe, 0 heisst: keine Grenze (ADR-021).
##
## Eine Welt, die man ABSCHLIESSEN kann, braucht ein Ende je Station. Ohne
## Grenze gaebe es kein "alles gekauft" -- und damit keinen Moment, in dem die
## naechste Welt verdient ist statt nur erreicht. Welten ohne diesen Wert
## laufen wie bisher endlos.
var max_stufe: int = 0

## Die Ausstattungsplaetze in fester Reihenfolge (ausstattung_1 .. _3).
var ausstattung: Array[EquipmentSlot] = []

## Faktor von aussen, z. B. aus gekauften Raeumen. Der Kern setzt ihn; die
## Station weiss nicht, woher er kommt -- sie weiss auch nichts von Raeumen.
var extern_faktor: float = 1.0


func _init(station_id: StringName, params: Dictionary = {}) -> void:
	id = station_id
	basis_kosten = float(params.get("basis_kosten", basis_kosten))
	wachstum = float(params.get("wachstum", wachstum))
	basis_durchsatz = float(params.get("basis_durchsatz", basis_durchsatz))
	multiplikator = float(params.get("multiplikator", multiplikator))
	meilenstein_intervall = int(params.get("meilenstein_intervall", meilenstein_intervall))
	meilenstein_faktor = float(params.get("meilenstein_faktor", meilenstein_faktor))
	stufe = int(params.get("stufe", stufe))
	freigeschaltet = bool(params.get("freigeschaltet", freigeschaltet))
	max_stufe = int(params.get("max_stufe", max_stufe))
	var plaetze: Dictionary = params.get("ausstattung", {}) as Dictionary
	for schluessel in plaetze.keys():
		ausstattung.append(EquipmentSlot.new(StringName(String(schluessel)),
			plaetze[schluessel] as Dictionary))


## Durchsatz pro Sekunde auf der aktuellen Stufe.
## Eine Station auf Stufe 0 leistet nichts -- das ist der Grund, warum das
## Spiel mit einem sofort sichtbaren Engpass startet.
func durchsatz() -> float:
	if not freigeschaltet:
		return 0.0
	return CostCurve.ertrag_pro_sekunde(
		basis_durchsatz, stufe,
		multiplikator * meilenstein_bonus() * ausstattung_faktor() * extern_faktor)


## Das Produkt aller Ausstattungsplaetze.
func ausstattung_faktor() -> float:
	var f: float = 1.0
	for platz in ausstattung:
		f *= platz.faktor()
	return f


func platz(platz_id: StringName) -> EquipmentSlot:
	for p in ausstattung:
		if p.id == platz_id:
			return p
	return null


## Kann die Station noch eine Stufe hoeher? Ohne Grenze immer.
func kann_ausbauen() -> bool:
	return max_stufe <= 0 or stufe < max_stufe


func ist_max() -> bool:
	return max_stufe > 0 and stufe >= max_stufe


## Erreichte Sterne -- ein Stern je Meilenstein.
func sterne() -> int:
	return meilensteine_erreicht()


## Wie viele Sterne diese Station ueberhaupt haben kann (0 = unbegrenzt).
func sterne_moeglich() -> int:
	if max_stufe <= 0 or meilenstein_intervall <= 0:
		return 0
	return max_stufe / meilenstein_intervall


## Wie oft hat sich der Ertrag durch Meilensteine verdoppelt?
func meilensteine_erreicht() -> int:
	if meilenstein_intervall <= 0:
		return 0
	return stufe / meilenstein_intervall


## Der Faktor aus allen bisher erreichten Meilensteinen.
func meilenstein_bonus() -> float:
	return pow(meilenstein_faktor, float(meilensteine_erreicht()))


## Wie viele Stufen fehlen bis zum naechsten Meilenstein?
## Die UI zeigt das an -- ein sichtbares Nahziel haelt den Spieler bei der Sache.
func stufen_bis_meilenstein() -> int:
	if meilenstein_intervall <= 0 or ist_max():
		return 0
	var bis: int = meilenstein_intervall - (stufe % meilenstein_intervall)
	# Hinter dem letzten Stern kommt keiner mehr -- "noch 7 bis zum Stern"
	# waere dann eine Behauptung ueber einen Stern, den es nicht gibt.
	if max_stufe > 0 and stufe + bis > max_stufe:
		return 0
	return bis


## Preis fuer die naechste Stufe.
func naechste_kosten() -> float:
	return CostCurve.kosten_fuer_stufe(basis_kosten, wachstum, stufe + 1)


## Hebt die Stufe um eins an. Gibt den bezahlten Preis zurueck.
## Die Pruefung, ob das Kapital reicht, liegt bewusst NICHT hier, sondern
## im aufrufenden System -- eine Station kennt kein Konto.
func upgrade() -> float:
	var preis: float = naechste_kosten()
	stufe += 1
	return preis


## Zustand fuer den Spielstand.
func to_dict() -> Dictionary:
	var plaetze: Dictionary = {}
	for p in ausstattung:
		plaetze[String(p.id)] = p.stufe
	return {
		"id": String(id),
		"stufe": stufe,
		"freigeschaltet": freigeschaltet,
		"ausstattung": plaetze,
	}


## Stellt den Zustand aus dem Spielstand wieder her.
## Balance-Parameter werden NICHT aus dem Save gelesen, sondern immer frisch
## aus den Balance-Daten -- sonst wuerde ein alter Spielstand ein neues
## Balancing dauerhaft blockieren.
func apply_dict(daten: Dictionary) -> void:
	stufe = int(daten.get("stufe", 0))
	# Ein Stand aus der Zeit vor der Grenze kann hoeher liegen, als die Grenze
	# heute erlaubt. Kappen statt ablehnen: Der Spieler hat nichts falsch
	# gemacht, die Regel ist neu.
	if max_stufe > 0:
		stufe = mini(stufe, max_stufe)
	freigeschaltet = bool(daten.get("freigeschaltet", true))
	var plaetze: Dictionary = daten.get("ausstattung", {}) as Dictionary
	for p in ausstattung:
		p.stufe = clampi(int(plaetze.get(String(p.id), 0)), 0, p.max_stufe)
