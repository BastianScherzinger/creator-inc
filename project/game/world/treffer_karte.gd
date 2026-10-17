## Was liegt unter dem Finger? Trefferpruefung mit Strahl gegen Boxen
## (RELEASE_PLAN 2.A/2.B).
##
## Die Karte wurde frueher mit der Bodenebene y = 0 geschnitten. Alles, was man
## SIEHT -- Waende (1,2 bis 2,4 m), Moebel -- liegt hoeher und wird in der
## Isometrie um (-h, -h) verschoben: Ein Tipp auf die Kuechenrueckwand fiel aus
## der Karte, ein Tipp auf die halbhohe Innenwand landete im Nachbarraum.
##
## Hier steht fuer jede Station, jede Zone und jedes Wandstueck eine Box. Der
## Strahl der Kamera trifft die Box, die er zuerst betritt -- also genau das,
## was vorn liegt und damit zu sehen ist. Das ist reine Geometrie ohne
## Physikserver: Es laeuft im Unit-Test ohne Bild, und es braucht keine
## Area3D-Knoten.
##
## Reihenfolge: Stationen (Layer 1) vor Zonen und Waenden (Layer 2), danach
## ein Rueckfall auf eine Ebene in Kompromisshoehe.
extends RefCounted

## Stationsbox: 2,2 x 1,6 x 2,2 m.
const STATION_BREITE: float = 2.2
const STATION_HOEHE: float = 1.6
## Zonenbox: das Zonenrechteck (Boden liegt auf x1-0,5 bis x2+0,5), 1,3 m hoch.
const ZONE_HOEHE: float = 1.3
## Wandstuecke: Dicke und Hoehe je Wandtyp (die Modelle in assets/room).
const WAND_DICKE: float = 0.3
const WAND_HOEHE: Dictionary = {"voll": 2.4, "halb": 1.2, "sockel": 0.4, "gelaender": 1.0}
## Rueckfallebene, wenn keine Box getroffen wird: zwischen Boden und Wandkrone.
const RUECKFALL_Y: float = 0.6
## Strahllaenge der Kamera (far = 200).
const REICHWEITE: float = 400.0

var _stationen: Array = []       ## [{id, box}]
var _flaechen: Array = []        ## [{zone, box}] Zonen und Wandstuecke
var _zonen: Array = []


## `stationen`: id -> Weltposition (Anzeigeposition), `zonen` und `waende` wie
## in worlds.json.
func bauen(stationen: Dictionary, zonen: Array, waende: Array) -> void:
	_stationen.clear()
	_flaechen.clear()
	_zonen = zonen
	for id in stationen.keys():
		var p: Vector3 = stationen[id] as Vector3
		var halb: float = STATION_BREITE * 0.5
		_stationen.append({"id": id,
			"box": AABB(Vector3(p.x - halb, 0.0, p.z - halb), Vector3(STATION_BREITE, STATION_HOEHE, STATION_BREITE))})
	for eintrag in zonen:
		var z: Dictionary = eintrag as Dictionary
		var x1: float = float(z.get("x1", 0)) - 0.5
		var z1: float = float(z.get("z1", 0)) - 0.5
		var breite: float = float(z.get("x2", 0)) + 0.5 - x1
		var tiefe: float = float(z.get("z2", 0)) + 0.5 - z1
		_flaechen.append({"zone": z, "box": AABB(Vector3(x1, 0.0, z1), Vector3(breite, ZONE_HOEHE, tiefe))})
	for eintrag in waende:
		_baue_wand(eintrag as Dictionary)


## Eine Wand in Stuecke zu je einem Meter. Jedes Stueck gehoert dem Raum, dessen
## Seite man sieht: bei Waenden entlang x die +z-Seite, bei Waenden entlang z die
## +x-Seite (die Kamera schaut aus +x/+z). Gibt es dort keinen Raum -- Aussenwand
## vorn oder rechts --, gilt die andere Seite.
func _baue_wand(w: Dictionary) -> void:
	var achse_x: bool = String(w.get("achse", "x")) == "x"
	var fest: float = float(w.get("fest", 0.0))
	var von: float = float(w.get("von", 0.0))
	var bis: float = float(w.get("bis", 0.0))
	var hoehe: float = float(WAND_HOEHE.get(String(w.get("typ", "halb")), 1.2))
	var feld: float = von
	while feld < bis - 0.001:
		var ende: float = minf(feld + 1.0, bis)
		var mitte: float = (feld + ende) * 0.5
		var vorn: Vector3 = Vector3(mitte, 0.0, fest + 0.6) if achse_x else Vector3(fest + 0.6, 0.0, mitte)
		var hinten: Vector3 = Vector3(mitte, 0.0, fest - 0.6) if achse_x else Vector3(fest - 0.6, 0.0, mitte)
		var zone: Dictionary = zone_an(vorn)
		if zone.is_empty():
			zone = zone_an(hinten)
		if not zone.is_empty():
			var box: AABB
			if achse_x:
				box = AABB(Vector3(feld, 0.0, fest - WAND_DICKE * 0.5), Vector3(ende - feld, hoehe, WAND_DICKE))
			else:
				box = AABB(Vector3(fest - WAND_DICKE * 0.5, 0.0, feld), Vector3(WAND_DICKE, hoehe, ende - feld))
			_flaechen.append({"zone": zone, "box": box})
		feld = ende


## Die Zone an einem Punkt: erst das Innere, dann ein Rand von 0,5 m.
func zone_an(punkt: Vector3) -> Dictionary:
	for rand in [0.0, 0.5]:
		for eintrag in _zonen:
			var z: Dictionary = eintrag as Dictionary
			if WorldData.zone_enthaelt(z, punkt, rand):
				return z
	return {}


## Was trifft der Strahl? {"art": "station" | "zone" | "boden" | "nichts",
## "station": StringName, "zone": Dictionary, "punkt": Vector3}.
func finde(ursprung: Vector3, richtung: Vector3) -> Dictionary:
	var rd: Vector3 = richtung.normalized()
	# Layer 1: Stationen -- die zuerst getroffene.
	var beste_t: float = INF
	var beste_id: StringName = &""
	for s in _stationen:
		var t: float = _eintritt(s["box"] as AABB, ursprung, rd)
		if t < beste_t:
			beste_t = t
			beste_id = s["id"] as StringName
	if beste_id != &"":
		return {"art": "station", "station": beste_id, "zone": {}, "punkt": ursprung + rd * beste_t}
	# Layer 2: Zonen und Waende -- was der Strahl zuerst betritt, liegt vorn.
	beste_t = INF
	var beste_zone: Dictionary = {}
	for f in _flaechen:
		var t: float = _eintritt(f["box"] as AABB, ursprung, rd)
		if t < beste_t:
			beste_t = t
			beste_zone = f["zone"] as Dictionary
	if not beste_zone.is_empty():
		return {"art": "zone", "station": &"", "zone": beste_zone, "punkt": ursprung + rd * beste_t}
	# Rueckfall: Ebene in Kompromisshoehe, Zone mit Rand.
	if absf(rd.y) > 0.0001:
		var t_boden: float = (RUECKFALL_Y - ursprung.y) / rd.y
		if t_boden > 0.0:
			var punkt: Vector3 = ursprung + rd * t_boden
			var zone: Dictionary = zone_an(punkt)
			if not zone.is_empty():
				return {"art": "boden", "station": &"", "zone": zone, "punkt": punkt}
			return {"art": "nichts", "station": &"", "zone": {}, "punkt": punkt}
	return {"art": "nichts", "station": &"", "zone": {}, "punkt": ursprung}


## Entfernung, bei der der Strahl die Box betritt, oder INF. Steht der Ursprung
## schon in der Box (Orthokamera weit weg: nie), gilt 0.
static func _eintritt(box: AABB, ursprung: Vector3, rd: Vector3) -> float:
	if box.has_point(ursprung):
		return 0.0
	var treffer: Variant = box.intersects_ray(ursprung, rd)
	if treffer == null:
		return INF
	return ursprung.distance_to(treffer as Vector3)
