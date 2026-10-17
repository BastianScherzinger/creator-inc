## Ein Ausstattungsplatz an einer Station (ADR-021).
##
## Stufen sind das eine, Ausstattung das andere: Eine Stufe macht eine Station
## "besser", ein Ausstattungsteil macht sie SICHTBAR anders. Der neue Bildschirm
## auf dem Schreibtisch ist ein Gegenstand, den man gekauft hat und der dort
## steht -- das merkt man sich, eine Prozentzahl nicht.
##
## Der Platz kennt nur Zahlen und eine neutrale ID (`ausstattung_1`). Was dort
## steht, sagt das Thema (Regel D3).
class_name EquipmentSlot
extends RefCounted

var id: StringName
var stufe: int = 0
var max_stufe: int = 10

## Ab welcher STATIONSstufe der Platz kaufbar ist. Vorher zeigt die Oberflaeche
## ein Schloss -- ein Ziel, das man schon sieht, bevor man es erreichen kann.
var ab_stufe: int = 1

var basis_kosten: float = 50.0
var wachstum: float = 1.8

## Wie viel jede Stufe zur Leistung der Station beitraegt.
var bonus_je_stufe: float = 0.1

## Zusaetzlicher Faktor je erreichtem MODELL (Stern).
##
## Ein neues Modell ist der Moment, den man sieht -- der zweite Monitor steht
## da. Waere er rechnerisch nur eine Stufe wie jede andere (+5 %), stuende auf
## dem Bildschirm ein Ereignis und in der Kasse keins. Der Sprung muss sich in
## beiden zeigen.
var stern_faktor: float = 1.0

## Bei welchen Stufen ein neues MODELL erscheint (die drei Sterne des Platzes).
##
## Nicht jede Stufe ein neues Modell: Zehn Modelle je Platz waeren fuenfzehn
## mal zehn Dateien und nicht unterscheidbar. Drei deutlich verschiedene
## Stufen sind lesbar -- dazwischen waechst nur die Zahl.
var modell_schwellen: Array[int] = [1, 4, 8]


func _init(platz_id: StringName, params: Dictionary = {}) -> void:
	id = platz_id
	max_stufe = int(params.get("max_stufe", max_stufe))
	ab_stufe = int(params.get("ab_stufe", ab_stufe))
	basis_kosten = float(params.get("basis_kosten", basis_kosten))
	wachstum = float(params.get("wachstum", wachstum))
	bonus_je_stufe = float(params.get("bonus_je_stufe", bonus_je_stufe))
	stern_faktor = float(params.get("stern_faktor", stern_faktor))
	var schwellen: Array = params.get("modell_schwellen", []) as Array
	if not schwellen.is_empty():
		modell_schwellen.clear()
		for s in schwellen:
			modell_schwellen.append(int(s))


## Der Faktor, mit dem dieser Platz die Leistung der Station multipliziert.
func faktor() -> float:
	return _faktor_fuer(stufe)


## Der Faktor nach dem naechsten Kauf -- fuer "jetzt -> danach" im Menue.
func faktor_danach() -> float:
	return _faktor_fuer(mini(stufe + 1, max_stufe))


func _faktor_fuer(s: int) -> float:
	var modelle: int = 0
	for schwelle in modell_schwellen:
		if s >= schwelle:
			modelle += 1
	return (1.0 + bonus_je_stufe * float(s)) * pow(stern_faktor, float(modelle))


func ist_max() -> bool:
	return stufe >= max_stufe


func freigegeben(station_stufe: int) -> bool:
	return station_stufe >= ab_stufe


## Preis der naechsten Stufe. Stufe 0 -> 1 kostet genau die Basis.
func naechste_kosten() -> float:
	return basis_kosten * pow(wachstum, float(stufe))


## Welches der Modelle gerade zu sehen ist: 0 = Anfangszustand, 1..3 = Sterne.
func modellstufe() -> int:
	var ergebnis: int = 0
	for i in range(modell_schwellen.size()):
		if stufe >= modell_schwellen[i]:
			ergebnis = i + 1
	return ergebnis


## Die Stufe, ab der das naechste Modell erscheint, oder -1, wenn keines mehr kommt.
func naechste_modell_schwelle() -> int:
	for schwelle in modell_schwellen:
		if stufe < schwelle:
			return schwelle
	return -1
