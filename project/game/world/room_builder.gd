## Setzt aus den Raummodulen einen ganzen Grundriss zusammen.
##
## Bisher schwebte ein Podest im Nichts. Ein Idle-Tycoon braucht einen ORT:
## Fliesenboden, Waende, Tuer, Ecken. Erst dadurch wirkt die Karte wie ein Amt.
##
## Die Fliesen laufen ueber MultiMeshInstance3D. Bei rund 170 Fliesen waeren
## einzelne Nodes 170 Draw Calls allein fuer den Boden -- das Budget liegt bei
## 150 fuer die GESAMTE Szene (ARCHITECTURE.md 4). Als MultiMesh sind es drei.
class_name RoomBuilder
extends Node3D

## Raumgroesse in Fliesen. Der Grundriss ist bewusst rechteckig und
## ueberschaubar -- eine kompakte Karte, kein Gebaeudekomplex (GAME_DESIGN).
## Gemessen am Geraet, nicht am PC: Bei 45 Grad Kameradrehung haengen BEIDE
## Bildschirmausdehnungen an der SUMME aus Breite und Tiefe -- ein breiterer
## oder ein tieferer Raum kostet gleich viel Bildbreite. Im Hochformat ist
## Bildbreite das knappe Gut, deshalb ist der Raum kompakt statt weitlaeufig.
## 15x13 lief links und rechts aus dem Bild, ohne dass mehr zu sehen war.
## Vorbelegung. Die tatsaechliche Groesse kommt je Welt aus worlds.json --
## das Zimmer in Welt 1 ist eng, das Buero in Welt 4 hat zwei Raeume.
const BREITE_STANDARD: int = 13
const TIEFE_STANDARD: int = 11

var BREITE: int = BREITE_STANDARD      ## entlang X
var TIEFE: int = TIEFE_STANDARD        ## entlang Z

## Die STRUKTURMODULE sind ein Vertrag: Jede Welt muss sie liefern, sonst
## fehlen Boden oder Waende. Alles Weitere (Heizkoerper, Automat, Uhr) ist
## Ausstattung und kommt aus worlds.json -- sie unterscheidet die Welten.
## Ersatzwelt fuer noch nicht gebaute Raummodule -- siehe _lade_modul.
const ERSATZWELT: String = "zimmer"

const STRUKTUR: Array[String] = [
	"raum_fliese_a", "raum_fliese_b", "raum_fliese_weg",
	"raum_wand", "raum_wand_ecke", "raum_wand_tuer", "raum_wand_fenster",
]

var _theme_ordner: String = "amt"
var _module: Dictionary = {}
var _ausstattung: Array = []
var _laufwege: Array = []
var _tuer_x: int = 3
var _fenster_x: Array = [-4, -2, 5]
var _fenster_z: Array = [-3, 1, 4]


func bauen(theme_ordner: String = "amt", breite: int = -1, tiefe: int = -1,
		grundriss: Dictionary = {}) -> void:
	_theme_ordner = theme_ordner
	_ausstattung = grundriss.get("ausstattung", []) as Array
	_laufwege = grundriss.get("laufwege", []) as Array
	if grundriss.has("tuer_x"):
		_tuer_x = int(grundriss["tuer_x"])
	if grundriss.has("fenster_x"):
		_fenster_x = grundriss["fenster_x"] as Array
	if grundriss.has("fenster_z"):
		_fenster_z = grundriss["fenster_z"] as Array
	# Ungerade Kantenlaengen: Der Grundriss ist um (0,0) zentriert, damit die
	# Kette auf der Diagonalen mittig liegt. Eine gerade Zahl haette keine
	# Mittelfliese und der Raum saesse einen halben Meter schief.
	if breite > 0:
		BREITE = breite if breite % 2 == 1 else breite + 1
	if tiefe > 0:
		TIEFE = tiefe if tiefe % 2 == 1 else tiefe + 1
	_lade_module()
	_baue_boden()
	_baue_waende()
	_baue_ausstattung()


func _lade_module() -> void:
	var zu_laden: Array = STRUKTUR.duplicate()
	for eintrag in _ausstattung:
		var name: String = String((eintrag as Dictionary).get("datei", ""))
		if name != "" and not zu_laden.has(name):
			zu_laden.append(name)
	for name in zu_laden:
		var szene: PackedScene = _lade_modul(name)
		if szene != null:
			_module[name] = szene


## Laedt ein Raummodul -- notfalls aus der Ersatzwelt.
##
## BAUGERUEST, kein Dauerzustand. Dieselbe Ueberlegung wie bei Stationsmodellen
## und Themendaten: Ohne Ersatz haette eine neue Welt gar keinen Boden, und
## jeder Blick darauf waere wertlos -- man koennte weder Kamera noch
## Beleuchtung noch Stationsanordnung beurteilen, bevor das letzte Wandsegment
## modelliert ist. Bei sechs Welten waere das eine Sperre gegen die eigene
## Arbeit.
##
## Die Warnung ist der Teil, der zaehlt: Ein Baugeruest, das man nicht bemerkt,
## wird ausgeliefert.
func _lade_modul(name: String) -> PackedScene:
	var pfad: String = "res://assets/room/%s/%s.glb" % [_theme_ordner, name]
	if ResourceLoader.exists(pfad):
		return load(pfad) as PackedScene
	var ersatz: String = "res://assets/room/%s/%s.glb" % [ERSATZWELT, name]
	if _theme_ordner != ERSATZWELT and ResourceLoader.exists(ersatz):
		push_warning("Welt '%s' hat kein Raummodul '%s' -- es laeuft '%s'"
			% [_theme_ordner, name, ERSATZWELT])
		return load(ersatz) as PackedScene
	push_warning("Raummodul fehlt ganz: %s" % pfad)
	return null


## Holt das Mesh eines Bodenmoduls.
##
## Godot verschachtelt glTF-Inhalte in Node3D-Baeume, das Mesh liegt also
## nicht direkt an der Wurzel.
##
## VERTRAG: Ein Bodenmodul muss GENAU EIN Mesh enthalten.
##
## Der Boden laeuft ueber MultiMeshInstance3D, und ein MultiMesh vervielfaeltigt
## genau ein Mesh. Bestand eine Kachel aus mehreren Teilen, wurde stillschweigend
## nur das erste verlegt -- in Welt 1 lag daraufhin pro Rasterfeld eine einzelne
## Diele statt vier, sichtbar als helle Streifen mit Loechern dazwischen. Beide
## Seiten waren fuer sich richtig, nur zusammen nicht. Deshalb wird der Vertrag
## hier geprueft und nicht vorausgesetzt: Das Bauskript verschmilzt die Teile
## (siehe `verbinden` in build_room_*.py), und wer das vergisst, bekommt eine
## Warnung statt eines Raetsels.
func _erstes_mesh(szene: PackedScene) -> Mesh:
	if szene == null:
		return null
	var wurzel: Node = szene.instantiate()
	var anzahl: int = _zaehle_meshes(wurzel)
	if anzahl > 1:
		push_warning(("Bodenmodul enthaelt %d Meshes, verlegt wird nur eines. " +
			"Im Bauskript verbinden() verwenden.") % anzahl)
	var gefunden: Mesh = _suche_mesh(wurzel)
	wurzel.queue_free()
	return gefunden


func _zaehle_meshes(knoten: Node) -> int:
	var summe: int = 1 if knoten is MeshInstance3D else 0
	for kind in knoten.get_children():
		summe += _zaehle_meshes(kind)
	return summe


func _suche_mesh(knoten: Node) -> Mesh:
	if knoten is MeshInstance3D:
		return (knoten as MeshInstance3D).mesh
	for kind in knoten.get_children():
		var treffer: Mesh = _suche_mesh(kind)
		if treffer != null:
			return treffer
	return null


func _baue_boden() -> void:
	var muster := {"raum_fliese_a": [], "raum_fliese_b": [], "raum_fliese_weg": []}

	var halb_x: int = BREITE / 2
	var halb_z: int = TIEFE / 2
	for ix in range(-halb_x, halb_x + 1):
		for iz in range(-halb_z, halb_z + 1):
			var pos := Vector3(float(ix), 0.0, float(iz))
			muster[_fliese_fuer(ix, iz)].append(pos)

	for name in muster.keys():
		var positionen: Array = muster[name]
		if positionen.is_empty() or not _module.has(name):
			continue
		var mesh: Mesh = _erstes_mesh(_module[name])
		if mesh == null:
			continue

		var multi := MultiMesh.new()
		multi.transform_format = MultiMesh.TRANSFORM_3D
		multi.mesh = mesh
		multi.instance_count = positionen.size()
		for i in range(positionen.size()):
			multi.set_instance_transform(i, Transform3D(Basis(), positionen[i]))

		var knoten := MultiMeshInstance3D.new()
		knoten.multimesh = multi
		add_child(knoten)


## Welche Fliese liegt an dieser Stelle?
##
## Grundmuster ist ein Schachbrett -- ohne Muster wirkt ein Boden wie eine
## leere Flaeche. Darueber liegen die LAUFWEGE: heller getretene Stellen dort,
## wo jeden Tag jemand geht. Sie erzaehlen, dass der Raum in Betrieb ist, und
## fuehren zugleich das Auge zur Kette.
##
## Die Wege kommen aus worlds.json und stehen nicht mehr hier.
##
## Vorher war der Verlauf fest verdrahtet -- und zwar auf den Grundriss der
## ersten gebauten Welt. In einem kleineren Raum ergaben dieselben Formeln
## ein breites Kreuz quer durch alles, weil die Grenzen ausserhalb des Raums
## lagen und damit nie griffen. Ein Weg gehoert zum Raum, nicht zum Bauer.
func _fliese_fuer(ix: int, iz: int) -> String:
	if _auf_laufweg(float(ix), float(iz)):
		return "raum_fliese_weg"
	return "raum_fliese_a" if (ix + iz) % 2 == 0 else "raum_fliese_b"


## Liegt dieses Feld nahe genug an einer der Wegstrecken?
##
## Jede Strecke ist eine Linie von (x1,z1) nach (x2,z2). Ein Feld gehoert zum
## Weg, wenn sein Mittelpunkt hoechstens `breite` davon entfernt liegt. Damit
## ist ein Weg eine Linie mit Dicke und kein Rechteck -- er darf schraeg
## verlaufen, und die Kette liegt auf der Diagonalen.
func _auf_laufweg(x: float, z: float) -> bool:
	for eintrag in _laufwege:
		var w: Dictionary = eintrag as Dictionary
		var a := Vector2(float(w.get("x1", 0.0)), float(w.get("z1", 0.0)))
		var b := Vector2(float(w.get("x2", 0.0)), float(w.get("z2", 0.0)))
		var breite: float = float(w.get("breite", 0.7))
		if Geometry2D.get_closest_point_to_segment(Vector2(x, z), a, b).distance_to(Vector2(x, z)) <= breite:
			return true
	return false


## Waende nur auf den beiden ABGEWANDTEN Seiten.
##
## Bei isometrischer Aufsicht wuerden die vorderen Waende dem Betrachter die
## Sicht nehmen. Der offene Raum nach vorn ist keine Nachlaessigkeit, sondern
## die uebliche Loesung des Genres.
func _baue_waende() -> void:
	var halb_x: int = BREITE / 2
	var halb_z: int = TIEFE / 2

	# Rueckwand entlang X (bei -Z)
	for ix in range(-halb_x, halb_x + 1):
		var name: String = "raum_wand"
		if ix == 3:
			name = "raum_wand_tuer"        # Eingang
		elif ix in [-4, -2, 5]:
			name = "raum_wand_fenster"
		_setze_modul(name, Vector3(float(ix), 0.0, float(-halb_z) - 0.5), 0.0)

	# Seitenwand entlang Z (bei -X)
	for iz in range(-halb_z, halb_z + 1):
		var name: String = "raum_wand"
		if iz in [-3, 1, 4]:
			name = "raum_wand_fenster"
		_setze_modul(name, Vector3(float(-halb_x) - 0.5, 0.0, float(iz)), 90.0)

	# Ecke schliesst die Naht zwischen beiden Waenden
	_setze_modul("raum_wand_ecke",
		Vector3(float(-halb_x) - 0.5, 0.0, float(-halb_z) - 0.5), 0.0)


## Die Ausstattung unterscheidet die Welten voneinander.
##
## Sie stand bis hierher als feste Liste im Code -- Automat, Uhr und
## Muelleimer eines Amtes. Im 14-Quadratmeter-Zimmer von Welt 1 haette ein
## Getraenkeautomat an der Wand gestanden. Was in einem Raum steht, ist eine
## Aussage ueber diesen Raum und gehoert deshalb zu seinen Daten.
##
## `y` ist optional und nur fuer Dinge noetig, die an der Wand haengen.
func _baue_ausstattung() -> void:
	for eintrag in _ausstattung:
		var d: Dictionary = eintrag as Dictionary
		_setze_modul(
			String(d.get("datei", "")),
			Vector3(float(d.get("x", 0.0)), float(d.get("y", 0.0)), float(d.get("z", 0.0))),
			float(d.get("drehung", 0.0)))


func _setze_modul(name: String, position: Vector3, drehung_y: float) -> void:
	if not _module.has(name):
		return
	var knoten: Node3D = (_module[name] as PackedScene).instantiate()
	knoten.position = position
	knoten.rotation_degrees = Vector3(0.0, drehung_y, 0.0)
	add_child(knoten)
