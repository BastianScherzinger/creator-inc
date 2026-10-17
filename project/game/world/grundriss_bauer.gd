## Baut eine Karte aus Zonen und Waenden -- die WG aus Welt 1 (ADR-021).
##
## RoomBuilder kann genau ein Rechteck mit zwei Waenden. Eine Wohnung hat acht
## Raeume, drei Bodenbelaege, hohe Aussenwaende, halbhohe Innenwaende, einen
## Sockel vorn und ein Balkongelaender. Alles davon steht in worlds.json; hier
## steht nur, wie man es zusammensetzt.
##
## Boeden sind je ZONE eine eigene Platte: So kann ein gesperrter Raum
## abgedunkelt werden, ohne den Flur daneben mitzufaerben. Waende laufen je
## Wandtyp ueber ein MultiMesh fuer die ganze Karte -- sie werden nie eingefaerbt.
## Die Raummodule (worlds.json "module") liefern nur noch Farben und Hoehen.
class_name GrundrissBauer
extends Node3D

const RAUM_PFAD: String = "res://assets/room/%s/%s.glb"
const WELT_PFAD: String = "res://assets/world/%s/%s.glb"

## Die Welt, deren Module einspringen, wenn einer neuen Welt ein Modul fehlt.
## Laut (push_warning) -- ein Baugeruest, das niemand bemerkt, wird ausgeliefert.
const ERSATZWELT: String = "zimmer"

## Die Tabelle von Welt 1 (worlds.json ohne "module").
## Boden-Schluessel aus worlds.json -> Module (Schachbrett aus a und b).
const BOEDEN: Dictionary = {
	"holz": ["wg_boden_holz_a", "wg_boden_holz_b"],
	"flur": ["wg_boden_flur_a", "wg_boden_flur_b"],
	"fliese": ["wg_boden_fliese_a", "wg_boden_fliese_b"],
	"bad": ["wg_boden_bad_a", "wg_boden_bad_b"],
	"deck": ["wg_boden_deck", "wg_boden_deck"],
}

## Wandtyp -> [Wand, Tuer, Fenster, Pfosten]. Leerer Eintrag = gibt es nicht.
const WAENDE: Dictionary = {
	"voll": ["wg_wand_voll", "wg_wand_halb_tuer", "wg_wand_voll_fenster", "wg_pfosten_voll"],
	"halb": ["wg_wand_halb", "wg_wand_halb_tuer", "wg_wand_halb", "wg_pfosten_halb"],
	"sockel": ["wg_wand_sockel", "wg_wand_sockel_tuer", "wg_wand_sockel", "wg_pfosten_sockel"],
	"gelaender": ["wg_gelaender", "wg_gelaender", "wg_gelaender", ""],
}

## Die Standardtabelle aus dem Asset-Vertrag (worlds.json: "module": "standard").
## Boeden heissen dort boden_<typ>_a / boden_<typ>_b, fuer jeden Typ der Zonen.
const STANDARD_WAENDE: Dictionary = {
	"voll": ["wand_voll", "wand_halb_tuer", "wand_voll_fenster", "pfosten_voll"],
	"halb": ["wand_halb", "wand_halb_tuer", "wand_halb", "pfosten_halb"],
	"sockel": ["wand_sockel", "wand_sockel_tuer", "wand_sockel", "pfosten_sockel"],
	"gelaender": ["gelaender", "gelaender", "gelaender", ""],
}

var _welt: String = ""
var _szenen: Dictionary = {}                ## Modulname -> PackedScene (oder null)
var _zonen_knoten: Dictionary = {}          ## zone_id -> Node3D
var _zonen_daten: Dictionary = {}           ## zone_id -> Dictionary
var _sperren: Dictionary = {}               ## bereich_id -> Node3D (Silhouetten)
var _schleier: StandardMaterial3D
var _gesperrt: Dictionary = {}              ## zone_id -> bool
var _variante: Dictionary = {}              ## zone_id -> String
var _boeden: Dictionary = {}                ## Bodentyp -> [a, b] (eigene Angaben)
var _waende: Dictionary = {}                ## Wandtyp -> [wand, tuer, fenster, pfosten]
var _standard: bool = false                 ## Standardtabelle statt Welt-1-Tabelle

# --- Buehne (K3 A1, A/B-Urteil 16.10.: b) ---------------------------------------
# Wenige grosse Formen statt Kleinteile: EINE Bodenplatte je Zone, Waende als
# durchgehende dicke Bloecke ohne Pfosten, gesperrte Raeume dunkel mit der
# Silhouette der kommenden Station.

const BUEHNE_DATEI: String = "_buehne"    ## Einrichtung mit hoechstens 5 Deko-Bloecken
const PLATTE_DICKE: float = 0.06          ## so dick wie die Bodenmodule (y -0,06 .. 0)
const PLATTE_FASE: float = 0.03           ## 3-cm-Fase am Rand jeder Bodenplatte
const BODEN_SAETTIGUNG: float = 0.78      ## Faktor auf die Saettigung der Bodenplatte
const BODEN_HELL: float = 1.04            ## Faktor auf die Helligkeit der Bodenplatte
const WAND_DICKE: float = 0.35
const KAPPE_HOEHE: float = 0.07           ## Deckfarbe oben auf der Wand
const KAPPE_UEBERSTAND: float = 0.02      ## die Kappe steht je Seite 2 cm ueber
const KAPPE_RUHE: float = 0.3             ## Kappenfarbe 30 % Richtung Wandfarbe
const TUER_HOEHE: float = 2.05            ## Sturz ueber Tueren in hohen Waenden
const GELAENDER_HOEHE: float = 0.55       ## Brüstung statt Staebe
const GELAENDER_DICKE: float = 0.14
const FENSTER_BREITE: float = 0.62
const FENSTER_UNTEN: float = 0.95
const FENSTER_OBEN: float = 1.9
## Gesperrter Boden: Helligkeit (sRGB) relativ zum gekauften Raum, leicht kuehl.
const GESPERRT_HELL: float = 0.5
const GESPERRT_TOENUNG := Color(0.80, 0.86, 1.0)
## Schleier fuer Einrichtung in gesperrten Raeumen (Buehne): wirkt auf ~50 %.
const FARBE_SCHLEIER_B := Color(0.06, 0.07, 0.12, 0.72)
## Silhouette der kommenden Station: dunkel, ohne Licht, etwas groesser als das
## Modell, damit sie die (abgedunkelte) Station ganz umschliesst.
const FARBE_SILHOUETTE := Color(0.12, 0.13, 0.20, 1.0)
const SILHOUETTE_SKALA: float = 1.04
const STATION_PFAD: String = "res://assets/stations/%s/%s.glb"

var _kern: GameCore = null
var _boden_mat: Dictionary = {}              ## zone_id -> StandardMaterial3D (Buehne)
var _boden_farbe: Dictionary = {}            ## zone_id -> Color (ungesperrt)


## `module` kommt aus worlds.json (WorldData.module): leer = Welt-1-Tabelle,
## "standard" = Asset-Vertrag, Dictionary = eigene Dateinamen je Typ.
func bauen(welt_id: String, zonen: Array, waende: Array, module: Variant = "") -> void:
	_welt = welt_id
	waehle_module(module)
	_schleier = StandardMaterial3D.new()
	_schleier.albedo_color = FARBE_SCHLEIER_B
	_schleier.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_schleier.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_schleier.render_priority = 1
	for eintrag in zonen:
		var z: Dictionary = eintrag as Dictionary
		var zone_id: String = String(z.get("id", ""))
		var knoten := Node3D.new()
		knoten.name = "Zone_" + zone_id
		add_child(knoten)
		_zonen_knoten[zone_id] = knoten
		_zonen_daten[zone_id] = z
		_baue_bodenplatte(knoten, z)
	_baue_wandbloecke(waende)


# --- Boeden --------------------------------------------------------------------

func waehle_module(module: Variant) -> void:
	_standard = false
	_boeden = BOEDEN.duplicate()
	_waende = WAENDE.duplicate()
	if module is Dictionary:
		_standard = true
		_boeden = ((module as Dictionary).get("boeden", {}) as Dictionary).duplicate()
		_waende = STANDARD_WAENDE.duplicate()
		_waende.merge((module as Dictionary).get("waende", {}) as Dictionary, true)
	elif String(module) == "standard":
		_standard = true
		_boeden = {}
		_waende = STANDARD_WAENDE.duplicate()
	elif not String(module).is_empty():
		push_warning("Grundriss: unbekannte Modultabelle '%s' -- es gilt die von Welt 1" % String(module))


## Die beiden Bodenmodule eines Typs (Schachbrett).
func boden_module(typ: String) -> Array:
	if _boeden.has(typ):
		return _boeden[typ] as Array
	if _standard:
		return ["boden_%s_a" % typ, "boden_%s_b" % typ]
	return BOEDEN["holz"] as Array


## [Wand, Tuer, Fenster, Pfosten] eines Wandtyps.
func wand_satz(typ: String) -> Array:
	if _waende.has(typ):
		return _waende[typ] as Array
	push_warning("Grundriss: unbekannter Wandtyp '%s' -- es gilt 'halb'" % typ)
	return _waende.get("halb", WAENDE["halb"]) as Array


# --- Buehne: Bodenplatten und Wandbloecke ------------------------------------------

## Eine Platte je Zone: ein Mesh, eine Farbe (Mittel der Bodenmodule), 3-cm-Fase.
func _baue_bodenplatte(ziel: Node3D, z: Dictionary) -> void:
	var zone_id: String = String(z.get("id", ""))
	var module: Array = boden_module(String(z.get("boden", "holz")))
	var farbe: Color = _flaechen_farbe(String(module[0])).lerp(_flaechen_farbe(String(module[1])), 0.5)
	# Eine grosse einfarbige Flaeche wirkt kraeftiger als dieselbe Farbe in
	# Dielen mit Fugen -- leicht zuruecknehmen, damit die Stationen fuehren.
	farbe = Color.from_hsv(farbe.h, farbe.s * BODEN_SAETTIGUNG, minf(1.0, farbe.v * BODEN_HELL))
	var x1: float = float(z.get("x1", 0)) - 0.5
	var x2: float = float(z.get("x2", 0)) + 0.5
	var z1: float = float(z.get("z1", 0)) - 0.5
	var z2: float = float(z.get("z2", 0)) + 0.5
	var boden := Node3D.new()
	boden.name = "Boden"
	ziel.add_child(boden)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = farbe
	mat.roughness = 0.92
	_boden_mat[zone_id] = mat
	_boden_farbe[zone_id] = farbe
	var platte := MeshInstance3D.new()
	platte.name = "Platte"
	platte.mesh = platten_mesh(x2 - x1, z2 - z1, PLATTE_DICKE, PLATTE_FASE)
	platte.material_override = mat
	platte.position = Vector3((x1 + x2) * 0.5, 0.0, (z1 + z2) * 0.5)
	boden.add_child(platte)


## Quader mit abgeschraegter Oberkante; Oberseite bei y = 0, Mitte im Ursprung.
static func platten_mesh(breite: float, tiefe: float, dicke: float, fase: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ax: float = breite * 0.5
	var az: float = tiefe * 0.5
	var ix: float = ax - fase
	var iz: float = az - fase
	var oben: float = 0.0
	var kante: float = -fase
	var unten: float = -dicke
	# Oberseite
	_viereck(st, Vector3(-ix, oben, -iz), Vector3(ix, oben, -iz), Vector3(ix, oben, iz), Vector3(-ix, oben, iz), Vector3.UP)
	# Fase (vier schraege Streifen)
	var n_fase: float = 0.7071
	_viereck(st, Vector3(-ix, oben, iz), Vector3(ix, oben, iz), Vector3(ax, kante, az), Vector3(-ax, kante, az), Vector3(0.0, n_fase, n_fase))
	_viereck(st, Vector3(ix, oben, -iz), Vector3(-ix, oben, -iz), Vector3(-ax, kante, -az), Vector3(ax, kante, -az), Vector3(0.0, n_fase, -n_fase))
	_viereck(st, Vector3(ix, oben, iz), Vector3(ix, oben, -iz), Vector3(ax, kante, -az), Vector3(ax, kante, az), Vector3(n_fase, n_fase, 0.0))
	_viereck(st, Vector3(-ix, oben, -iz), Vector3(-ix, oben, iz), Vector3(-ax, kante, az), Vector3(-ax, kante, -az), Vector3(-n_fase, n_fase, 0.0))
	# Seiten
	_viereck(st, Vector3(-ax, kante, az), Vector3(ax, kante, az), Vector3(ax, unten, az), Vector3(-ax, unten, az), Vector3.BACK)
	_viereck(st, Vector3(ax, kante, -az), Vector3(-ax, kante, -az), Vector3(-ax, unten, -az), Vector3(ax, unten, -az), Vector3.FORWARD)
	_viereck(st, Vector3(ax, kante, az), Vector3(ax, kante, -az), Vector3(ax, unten, -az), Vector3(ax, unten, az), Vector3.RIGHT)
	_viereck(st, Vector3(-ax, kante, -az), Vector3(-ax, kante, az), Vector3(-ax, unten, az), Vector3(-ax, unten, -az), Vector3.LEFT)
	return st.commit()


## Zwei Dreiecke mit Vorderseite zur Normalen (Godot: Vorderseite im Uhrzeigersinn).
static func _viereck(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, normale: Vector3) -> void:
	var n: Vector3 = normale.normalized()
	var punkte: Array[Vector3] = [a, b, c, a, c, d]
	if (b - a).cross(c - a).dot(n) > 0.0:
		punkte = [a, c, b, a, d, c]
	for p in punkte:
		st.set_normal(n)
		st.add_vertex(p)


## Flaechengewichtete Farbe der sichtbaren Oberseite eines Bodenmoduls (ohne Fugen).
func _flaechen_farbe(modul: String) -> Color:
	var mesh: Mesh = _mesh(modul)
	var fallback := Color("d8c3a0")
	if mesh == null:
		return fallback
	var oben: float = mesh.get_aabb().end.y
	var summe := Vector3.ZERO
	var gewicht: float = 0.0
	for i in range(mesh.get_surface_count()):
		var mat: StandardMaterial3D = mesh.surface_get_material(i) as StandardMaterial3D
		if mat == null or mat.resource_name.contains("fuge"):
			continue
		var arrays: Array = mesh.surface_get_arrays(i)
		var ecken: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array
		var index: PackedInt32Array = PackedInt32Array()
		if arrays[Mesh.ARRAY_INDEX] != null:
			index = arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
		if index.is_empty():
			for k in range(ecken.size()):
				index.append(k)
		var flaeche: float = 0.0
		for t in range(0, index.size() - 2, 3):
			var p0: Vector3 = ecken[index[t]]
			var p1: Vector3 = ecken[index[t + 1]]
			var p2: Vector3 = ecken[index[t + 2]]
			var kreuz: Vector3 = (p1 - p0).cross(p2 - p0)
			if absf(kreuz.normalized().y) < 0.8 or (p0.y + p1.y + p2.y) / 3.0 < oben - 0.02:
				continue
			flaeche += kreuz.length() * 0.5
		var c: Color = mat.albedo_color
		summe += Vector3(c.r, c.g, c.b) * flaeche
		gewicht += flaeche
	if gewicht <= 0.0:
		return fallback
	summe /= gewicht
	return Color(summe.x, summe.y, summe.z)


## Farben eines Moduls in Surface-Reihenfolge (0 = Wandkoerper, 1 = Kappe).
func _modul_farben(modul: String) -> Array[Color]:
	var out: Array[Color] = []
	var mesh: Mesh = _mesh(modul)
	if mesh == null:
		return out
	for i in range(mesh.get_surface_count()):
		var mat: StandardMaterial3D = mesh.surface_get_material(i) as StandardMaterial3D
		if mat != null:
			out.append(mat.albedo_color)
	return out


func _modul_hoehe(modul: String, standard: float) -> float:
	var mesh: Mesh = _mesh(modul)
	return mesh.get_aabb().end.y if mesh != null else standard


## Farbe der ersten Surface eines Moduls, deren Material `teil` im Namen traegt.
func _modul_farbe_mit(modul: String, teil: String) -> Variant:
	var mesh: Mesh = _mesh(modul)
	if mesh == null:
		return null
	for i in range(mesh.get_surface_count()):
		var mat: StandardMaterial3D = mesh.surface_get_material(i) as StandardMaterial3D
		if mat != null and mat.resource_name.contains(teil):
			return mat.albedo_color
	return null


## Waende als durchgehende Bloecke: je Abschnitt zwischen zwei Tueren EIN Quader,
## 0,35 m dick, Kappe in der Deckfarbe des Moduls. Keine Pfosten. Ueber Tueren in
## hohen Waenden liegt ein Sturz; Fenster sind eine Glasscheibe in der Wand.
## Alle Bloecke eines Wandtyps laufen ueber ein MultiMesh (wenige Draw Calls).
func _baue_wandbloecke(waende: Array) -> void:
	var koerper: Dictionary = {}     ## typ -> Array[Transform3D]
	var kappen: Dictionary = {}      ## typ -> Array[Transform3D]
	var scheiben: Array = []         ## Transform3D
	var glas: Variant = null
	for eintrag in waende:
		var w: Dictionary = eintrag as Dictionary
		var typ: String = String(w.get("typ", "halb"))
		var satz: Array = wand_satz(typ)
		var gelaender: bool = typ == "gelaender"
		var hoehe: float = GELAENDER_HOEHE if gelaender else _modul_hoehe(String(satz[0]), 1.2)
		var dicke: float = GELAENDER_DICKE if gelaender else WAND_DICKE
		var achse_x: bool = String(w.get("achse", "x")) == "x"
		var fest: float = float(w.get("fest", 0.0))
		var von: float = float(w.get("von", 0.0))
		var bis: float = float(w.get("bis", 0.0))
		var tueren: Array = w.get("tueren", []) as Array
		var fenster: Array = w.get("fenster", []) as Array
		if not koerper.has(typ):
			koerper[typ] = []
			kappen[typ] = []
		# Abschnitte zwischen den Tueren; an den Enden der Wand um die halbe Dicke
		# verlaengert, damit Ecken geschlossen sind.
		var luecken: Array = []
		for t in tueren:
			luecken.append(float(t))
		luecken.sort()
		var anfang: float = von - dicke * 0.5
		var abschnitte: Array = []
		for t in luecken:
			abschnitte.append([anfang, float(t) - 0.5])
			anfang = float(t) + 0.5
		abschnitte.append([anfang, bis + dicke * 0.5])
		for ab in abschnitte:
			var a: float = float(ab[0])
			var b: float = float(ab[1])
			if b - a < 0.05:
				continue
			_block(koerper[typ] as Array, kappen[typ] as Array, achse_x, fest, a, b, 0.0, hoehe, dicke)
		# Sturz ueber Tueren, wenn die Wand hoeher ist als die Tuer.
		if hoehe > TUER_HOEHE + 0.1:
			for t in luecken:
				_block(koerper[typ] as Array, kappen[typ] as Array, achse_x, fest,
					float(t) - 0.5, float(t) + 0.5, TUER_HOEHE, hoehe, dicke)
		if not fenster.is_empty() and hoehe > FENSTER_OBEN + 0.1:
			if glas == null:
				glas = _modul_farbe_mit(String(satz[2]), "glas")
			for f in fenster:
				var mitte: float = float(f)
				var laenge: float = FENSTER_BREITE
				var basis := Basis().scaled(Vector3(laenge, FENSTER_OBEN - FENSTER_UNTEN, dicke + 0.03)) if achse_x \
					else Basis().scaled(Vector3(dicke + 0.03, FENSTER_OBEN - FENSTER_UNTEN, laenge))
				var y: float = (FENSTER_UNTEN + FENSTER_OBEN) * 0.5
				var pos := Vector3(mitte, y, fest) if achse_x else Vector3(fest, y, mitte)
				scheiben.append(Transform3D(basis, pos))

	var knoten := Node3D.new()
	knoten.name = "Waende"
	add_child(knoten)
	var wuerfel := BoxMesh.new()
	wuerfel.size = Vector3.ONE
	for typ in koerper.keys():
		var farben: Array[Color] = _modul_farben(String(wand_satz(String(typ))[0]))
		var farbe_koerper: Color = farben[0] if farben.size() > 0 else Color("efe3cf")
		var farbe_kappe: Color = farben[1] if farben.size() > 1 else farbe_koerper.darkened(0.25)
		# Die Kappe zeichnet die Raumkante nach, soll aber nicht schreien.
		farbe_kappe = farbe_kappe.lerp(farbe_koerper, KAPPE_RUHE)
		if String(typ) == "gelaender":
			farbe_kappe = farbe_koerper.darkened(0.2)
		var block := _multimesh(wuerfel, koerper[typ] as Array)
		block.name = "Block_" + String(typ)
		block.material_override = _wandstoff(farbe_koerper)
		knoten.add_child(block)
		var kappe := _multimesh(wuerfel, kappen[typ] as Array)
		kappe.name = "Kappe_" + String(typ)
		kappe.material_override = _wandstoff(farbe_kappe)
		knoten.add_child(kappe)
	if not scheiben.is_empty() and glas != null:
		var scheibe := _multimesh(wuerfel, scheiben)
		scheibe.name = "Fenster"
		scheibe.material_override = _wandstoff(glas as Color)
		scheibe.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		knoten.add_child(scheibe)


## Ein Wandblock von `a` bis `b` entlang der Achse, Hoehe `unten` bis `oben`.
static func _block(koerper: Array, kappen: Array, achse_x: bool, fest: float, a: float, b: float,
		unten: float, oben: float, dicke: float) -> void:
	var laenge: float = b - a
	var mitte: float = (a + b) * 0.5
	var k_hoehe: float = minf(KAPPE_HOEHE, (oben - unten) * 0.4)
	var h: float = oben - unten - k_hoehe
	var groesse := Vector3(laenge, h, dicke) if achse_x else Vector3(dicke, h, laenge)
	var y: float = unten + h * 0.5
	var pos := Vector3(mitte, y, fest) if achse_x else Vector3(fest, y, mitte)
	koerper.append(Transform3D(Basis().scaled(groesse), pos))
	var ue: float = KAPPE_UEBERSTAND * 2.0
	var k_groesse := Vector3(laenge + ue, k_hoehe, dicke + ue) if achse_x else Vector3(dicke + ue, k_hoehe, laenge + ue)
	var k_pos := Vector3(mitte, oben - k_hoehe * 0.5, fest) if achse_x else Vector3(fest, oben - k_hoehe * 0.5, mitte)
	kappen.append(Transform3D(Basis().scaled(k_groesse), k_pos))


static func _wandstoff(farbe: Color) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = farbe
	m.roughness = 0.9
	return m


static func _enthaelt(liste: Array, feld: float) -> bool:
	for eintrag in liste:
		if absf(float(eintrag) - feld) < 0.01:
			return true
	return false


# --- Einrichtung und Sperren ----------------------------------------------------

## Setzt Einrichtung und Sperr-Zustand aller Zonen nach dem Stand des Kerns.
##
## Wird beim Aufbau und nach jedem Raumkauf aufgerufen. Eine Zone kann dabei
## eine Geschichte in Bildern erzaehlen ("varianten" in worlds.json): je eine
## Dateiendung fuer gesperrt, verfuegbar (kaufbar) und gekauft.
func aktualisiere(kern: GameCore, mit_auftritt: bool = false) -> void:
	_kern = kern
	for zone_id in _zonen_daten.keys():
		var z: Dictionary = _zonen_daten[zone_id]
		var bereich_id := StringName(String(z.get("bereich", "")))
		var gesperrt: bool = bereich_id != &"" and not kern.bereiche.ist_gekauft(bereich_id)
		var zustand: String = "gekauft"
		if gesperrt:
			zustand = "verfuegbar" if kern.bereiche.verfuegbar(bereich_id) else "gesperrt"
		var variante: String = einrichtung_fuer(z, zustand)
		if String(_variante.get(zone_id, "")) != variante:
			_setze_einrichtung(String(zone_id), variante, mit_auftritt)
		var war_gesperrt: bool = bool(_gesperrt.get(zone_id, false))
		if gesperrt != war_gesperrt or not _gesperrt.has(zone_id):
			_setze_gesperrt(String(zone_id), bereich_id, gesperrt, mit_auftritt and war_gesperrt)
		_gesperrt[zone_id] = gesperrt


## Welche Einrichtungsdatei eine Zone im gegebenen Zustand zeigt.
## Fehlt die Endung fuer "verfuegbar", gilt die fuer "gesperrt".
static func einrichtung_fuer(z: Dictionary, zustand: String) -> String:
	var datei: String = String(z.get("einrichtung", ""))
	var varianten: Dictionary = z.get("varianten", {}) as Dictionary
	if datei.is_empty() or varianten.is_empty():
		return datei
	var endung: String = String(varianten.get(zustand, ""))
	if endung.is_empty() and zustand == "verfuegbar":
		endung = String(varianten.get("gesperrt", ""))
	return datei + endung


func _setze_einrichtung(zone_id: String, datei: String, mit_auftritt: bool) -> void:
	var knoten: Node3D = _zonen_knoten[zone_id]
	var alt: Node = knoten.get_node_or_null("Einrichtung")
	if alt != null:
		alt.name = "Einrichtung_alt"
		alt.queue_free()
	_variante[zone_id] = datei
	if datei.is_empty():
		return
	# Buehne: dieselbe Einrichtung mit hoechstens 5 Deko-Bloecken
	# (build_einrichtung_buehne.py). Fehlt sie, springt die volle ein -- laut.
	var pfade: Array = [WELT_PFAD % [_welt, datei + BUEHNE_DATEI], WELT_PFAD % [_welt, datei]]
	var szene: PackedScene = _lade(pfade)
	if szene == null:
		return
	var einrichtung: Node3D = szene.instantiate()
	einrichtung.name = "Einrichtung"
	var z: Dictionary = _zonen_daten[zone_id]
	einrichtung.position = Vector3(
		(float(z.get("x1", 0)) + float(z.get("x2", 0))) * 0.5, 0.0,
		(float(z.get("z1", 0)) + float(z.get("z2", 0))) * 0.5)
	knoten.add_child(einrichtung)
	if bool(_gesperrt.get(zone_id, false)):
		_schleier_auf(einrichtung, true)
	if mit_auftritt:
		einrichtung.scale = Vector3(1.0, 0.01, 1.0)
		var t := create_tween()
		t.tween_property(einrichtung, "scale", Vector3.ONE, 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _setze_gesperrt(zone_id: String, bereich_id: StringName, gesperrt: bool, auftritt: bool) -> void:
	var knoten: Node3D = _zonen_knoten[zone_id]
	_schleier_auf(knoten, gesperrt)
	_toene_boden(zone_id, gesperrt)
	if gesperrt:
		if not _sperren.has(bereich_id):
			_sperren[bereich_id] = _baue_sperre(zone_id)
		return
	var sperre: Node3D = _sperren.get(bereich_id) as Node3D
	_sperren.erase(bereich_id)
	if sperre == null:
		return
	if not auftritt:
		sperre.queue_free()
		return
	# Der Moment des Kaufs: Die Silhouetten verschwinden, Staub steigt auf.
	var t := create_tween()
	t.tween_property(sperre, "scale", Vector3(1.2, 0.01, 1.2), 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	t.tween_callback(sperre.queue_free)
	_staub(sperre.global_position)
	_konfetti(sperre.global_position)


## Die Sperre eines gesperrten Raums: Silhouetten der kommenden Stationen.
func _baue_sperre(zone_id: String) -> Node3D:
	var z: Dictionary = _zonen_daten[zone_id]
	var mitte := Vector3(
		(float(z.get("x1", 0)) + float(z.get("x2", 0))) * 0.5, 0.0,
		(float(z.get("z1", 0)) + float(z.get("z2", 0))) * 0.5)
	var sperre := Node3D.new()
	sperre.name = "Sperre_" + zone_id
	sperre.position = mitte
	add_child(sperre)
	_baue_silhouetten(sperre, zone_id)
	return sperre


## Buehne: Der Boden eines gesperrten Raums wird selbst dunkel (kein Schleier
## darueber) -- so ist er messbar dunkler als der gekaufte Nachbar.
func _toene_boden(zone_id: String, gesperrt: bool) -> void:
	var mat: StandardMaterial3D = _boden_mat.get(zone_id) as StandardMaterial3D
	if mat == null:
		return
	var farbe: Color = _boden_farbe[zone_id] as Color
	if gesperrt:
		farbe = Color(farbe.r * GESPERRT_HELL * GESPERRT_TOENUNG.r,
			farbe.g * GESPERRT_HELL * GESPERRT_TOENUNG.g,
			farbe.b * GESPERRT_HELL * GESPERRT_TOENUNG.b)
	mat.albedo_color = farbe
	var platte: Node = _zonen_knoten[zone_id].get_node_or_null("Boden/Platte")
	if platte is GeometryInstance3D:
		(platte as GeometryInstance3D).material_overlay = null


## Silhouetten der Stationen, die dieser Raum freischaltet: dasselbe Modell,
## dunkel und ohne Licht. Sie umschliesst die abgedunkelte Station knapp, damit
## man die Form sieht, aber keine Details ("das kommt hier").
func _baue_silhouetten(sperre: Node3D, zone_id: String) -> void:
	if _kern == null:
		return
	var z: Dictionary = _zonen_daten[zone_id]
	var x1: float = float(z.get("x1", 0)) - 0.5
	var x2: float = float(z.get("x2", 0)) + 0.5
	var z1: float = float(z.get("z1", 0)) - 0.5
	var z2: float = float(z.get("z2", 0)) + 0.5
	var positionen: Dictionary = _kern.welten.stationen(_kern.welt_index)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = FARBE_SILHOUETTE
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for id in positionen.keys():
		var p: Vector3 = positionen[id] as Vector3
		if p.x < x1 or p.x > x2 or p.z < z1 or p.z > z2:
			continue
		var station: StationModel = _kern.kette.station(StringName(id))
		if station == null or station.freigeschaltet:
			continue
		var silhouette := Node3D.new()
		silhouette.name = "Silhouette_" + String(id)
		silhouette.position = p - sperre.position
		silhouette.scale = Vector3.ONE * SILHOUETTE_SKALA
		sperre.add_child(silhouette)
		var dateien: Array = ["%s_basis" % String(id)]
		for platz in station.ausstattung:
			dateien.append("%s_%s_0" % [String(id), String(platz.id)])
		for datei in dateien:
			var pfad: String = STATION_PFAD % [_welt, String(datei)]
			if not ResourceLoader.exists(pfad):
				continue
			var teil: Node3D = (load(pfad) as PackedScene).instantiate() as Node3D
			silhouette.add_child(teil)
			_ueberziehe(teil, mat)


static func _ueberziehe(wurzel: Node, mat: Material) -> void:
	if wurzel is GeometryInstance3D:
		(wurzel as GeometryInstance3D).material_override = mat
		(wurzel as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for kind in wurzel.get_children():
		_ueberziehe(kind, mat)


## Legt den Schleier auf alle Meshes unter `wurzel` -- oder nimmt ihn weg.
func _schleier_auf(wurzel: Node, an: bool) -> void:
	if wurzel is GeometryInstance3D:
		(wurzel as GeometryInstance3D).material_overlay = _schleier if an else null
	for kind in wurzel.get_children():
		if String(kind.name).begins_with("Sperre"):
			continue
		_schleier_auf(kind, an)


func _staub(ort: Vector3) -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 40
	p.lifetime = 1.1
	p.explosiveness = 0.9
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(2.0, 0.2, 2.0)
	p.direction = Vector3.UP
	p.spread = 50.0
	p.initial_velocity_min = 1.5
	p.initial_velocity_max = 3.5
	p.gravity = Vector3(0.0, -2.0, 0.0)
	p.scale_amount_min = 0.15
	p.scale_amount_max = 0.35
	var mesh := SphereMesh.new()
	mesh.radius = 0.5
	mesh.height = 1.0
	mesh.radial_segments = 6
	mesh.rings = 3
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("f6e7cf")
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh.material = mat
	p.mesh = mesh
	p.position = ort + Vector3(0.0, 0.5, 0.0)
	add_child(p)
	p.emitting = true
	get_tree().create_timer(2.0).timeout.connect(p.queue_free)


# --- Laden ---------------------------------------------------------------------

## Laedt die erste vorhandene Datei aus `pfade`. Fehlt die erste (die eigene
## Welt), wird das gemeldet -- auch wenn eine spaetere einspringt.
func _lade(pfade: Array) -> PackedScene:
	var schluessel: String = "|".join(pfade)
	if _szenen.has(schluessel):
		return _szenen[schluessel] as PackedScene
	var szene: PackedScene = null
	for i in range(pfade.size()):
		var pfad: String = String(pfade[i])
		if ResourceLoader.exists(pfad):
			szene = load(pfad) as PackedScene
			if i > 0:
				push_warning("Grundriss: %s fehlt -- Ersatz: %s" % [String(pfade[0]), pfad])
			break
	if szene == null:
		# Laut, nicht still (CLAUDE.md "Baugerueste muessen laut sein").
		push_warning("Grundriss: Modul fehlt: %s" % String(pfade[0]))
	_szenen[schluessel] = szene
	return szene


## Konfetti ueber dem Raum, der gerade aufgegangen ist: 60 Teilchen in Akzent
## und Gold, 1,2 s (RELEASE_PLAN 3).
func _konfetti(ort: Vector3) -> void:
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.amount = 60
	p.lifetime = 1.2
	p.explosiveness = 0.95
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	p.emission_box_extents = Vector3(1.2, 0.1, 1.2)
	p.direction = Vector3.UP
	p.spread = 55.0
	p.initial_velocity_min = 4.0
	p.initial_velocity_max = 7.5
	p.gravity = Vector3(0.0, -9.0, 0.0)
	p.angular_velocity_min = -540.0
	p.angular_velocity_max = 540.0
	p.scale_amount_min = 0.7
	p.scale_amount_max = 1.3
	var farben := Gradient.new()
	var akzent: Color = UiStil.akzent()
	farben.offsets = PackedFloat32Array([0.0, 0.25, 0.5, 0.75, 1.0])
	farben.colors = PackedColorArray([akzent, UiStil.GOLD, Color.WHITE, UiStil.KAUFEN, UiStil.GOLD])
	p.color_initial_ramp = farben
	var mesh := QuadMesh.new()
	mesh.size = Vector2(0.14, 0.2)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mesh.material = mat
	p.mesh = mesh
	p.position = ort + Vector3(0.0, 0.8, 0.0)
	add_child(p)
	p.emitting = true
	get_tree().create_timer(2.0).timeout.connect(p.queue_free)


## Ein Raummodul der Welt. Fehlt es in einer Welt mit Standardtabelle, springt
## das passende Modul von Welt 1 ein (laut).
func _mesh(name: String) -> Mesh:
	var pfade: Array = [RAUM_PFAD % [_welt, name]]
	if _standard:
		pfade.append(RAUM_PFAD % [ERSATZWELT, ersatz_name(name)])
	var szene: PackedScene = _lade(pfade)
	if szene == null:
		return null
	var wurzel: Node = szene.instantiate()
	var gefunden: Mesh = _suche_mesh(wurzel)
	wurzel.free()
	return gefunden


## Das Welt-1-Modul, das fuer ein fehlendes Standardmodul einspringt.
static func ersatz_name(name: String) -> String:
	if name.begins_with("boden_"):
		return "wg_boden_holz_b" if name.ends_with("_b") else "wg_boden_holz_a"
	return "wg_" + name


static func _suche_mesh(knoten: Node) -> Mesh:
	if knoten is MeshInstance3D:
		return (knoten as MeshInstance3D).mesh
	for kind in knoten.get_children():
		var treffer: Mesh = _suche_mesh(kind)
		if treffer != null:
			return treffer
	return null


static func _multimesh(mesh: Mesh, transformationen: Array) -> MultiMeshInstance3D:
	var multi := MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	multi.mesh = mesh
	multi.instance_count = transformationen.size()
	for i in range(transformationen.size()):
		multi.set_instance_transform(i, transformationen[i] as Transform3D)
	var knoten := MultiMeshInstance3D.new()
	knoten.multimesh = multi
	return knoten
