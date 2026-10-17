## Die beiden Formeln, auf denen die gesamte Progression steht.
##
## Kosten wachsen exponentiell, Ertrag linear (docs/GAME_DESIGN.md 5.1/5.2).
## Dieser Abstand ist Absicht: Die Kaufzeit pro Stufe steigt langsam an, und
## genau daraus entsteht die Spannung des Genres -- und der Ort, an dem eine
## Rewarded Ad spaeter als Erleichterung wirkt statt als Erpressung.
##
## Alle Zahlenwerte kommen aus data/balance/*.json, niemals aus dem Code.
class_name CostCurve
extends RefCounted


## Kosten fuer den Sprung auf Stufe `stufe` (1-basiert).
## kosten(n) = basis * wachstum^(n-1)
static func kosten_fuer_stufe(basis: float, wachstum: float, stufe: int) -> float:
	assert(stufe >= 1, "Stufen sind 1-basiert")
	assert(basis > 0.0, "Basiskosten muessen positiv sein")
	assert(wachstum >= 1.0, "Wachstum unter 1.0 wuerde Kosten sinken lassen")
	return basis * pow(wachstum, stufe - 1)


## Gesamtkosten, um von `von_stufe` auf `bis_stufe` zu kommen.
## Wird fuer "Alles kaufen"-Schaltflaechen und den Balance-Simulator gebraucht.
static func kosten_summe(basis: float, wachstum: float, von_stufe: int, bis_stufe: int) -> float:
	if bis_stufe <= von_stufe:
		return 0.0
	var summe: float = 0.0
	for n in range(von_stufe + 1, bis_stufe + 1):
		summe += kosten_fuer_stufe(basis, wachstum, n)
	return summe


## Wie viele Stufen sind mit `kapital` ab `aktuelle_stufe` bezahlbar?
static func bezahlbare_stufen(basis: float, wachstum: float, aktuelle_stufe: int, kapital: float) -> int:
	var anzahl: int = 0
	var rest: float = kapital
	var stufe: int = aktuelle_stufe + 1
	# Obergrenze verhindert eine Endlosschleife bei absurden Kapitalwerten
	while anzahl < 10000:
		var preis: float = kosten_fuer_stufe(basis, wachstum, stufe)
		if preis > rest:
			break
		rest -= preis
		anzahl += 1
		stufe += 1
	return anzahl


## Ertrag pro Sekunde auf einer Stufe.
## ertrag(n) = basis * n * multiplikator
static func ertrag_pro_sekunde(basis: float, stufe: int, multiplikator: float = 1.0) -> float:
	if stufe <= 0:
		return 0.0
	return basis * float(stufe) * multiplikator


## Sekunden, bis `kapital` fuer die naechste Stufe zusammengespart ist.
## Zielwert laut Design: in den ersten 60 Minuten nie ueber 90 Sekunden.
## Gibt INF zurueck, wenn kein Einkommen flieszt.
static func wartezeit_bis_naechste_stufe(
	basis: float, wachstum: float, aktuelle_stufe: int,
	kapital: float, einkommen_pro_sekunde: float
) -> float:
	var preis: float = kosten_fuer_stufe(basis, wachstum, aktuelle_stufe + 1)
	var fehlend: float = preis - kapital
	if fehlend <= 0.0:
		return 0.0
	if einkommen_pro_sekunde <= 0.0:
		return INF
	return fehlend / einkommen_pro_sekunde
