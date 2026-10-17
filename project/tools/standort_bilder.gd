## Rendert je Welt ein Ueberblicksbild fuer die Standortkarte
## (assets/ui/standorte/<welt>.png, transparent beschnitten).
##
## Aufruf fuer alle Welten (startet sich selbst je Welt neu, damit jede Welt
## einen frischen Kern bekommt):
##   godot_console --path project -s res://tools/standort_bilder.gd -- --alle
## Eine Welt (Position 1..6):
##   godot_console --path project --resolution 900x900 -s res://tools/standort_bilder.gd -- --welt 3 --frisch --tiefe 6 --ohne-eroeffnung --moment aus --ohne-szene
##
## Das Spiel selbst bleibt unangetastet: Das Skript haengt main.tscn ein,
## wartet, blendet alle Oberflaechen-Ebenen aus, macht den Hintergrund
## durchsichtig, rahmt die ganze Welt mit der Kamera und schneidet das Bild
## auf den sichtbaren Inhalt zu. Werte: data/ui/standortkarte.json ("render").
extends SceneTree

const DATEN: String = "res://data/ui/standortkarte.json"
const SZENE: String = "res://game/main.tscn"
const ZIEL_ORDNER: String = "res://assets/ui/standorte"

var _render: Dictionary = {}
var _bild_pfad: String = ""
var _bilder: int = 0
var _main: Node = null
var _gerahmt: bool = false


func _initialize() -> void:
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATEN))
	var daten: Dictionary = roh as Dictionary if roh is Dictionary else {}
	_render = daten.get("render", {}) as Dictionary
	_bild_pfad = String(daten.get("bild_pfad", ""))
	var argumente: PackedStringArray = OS.get_cmdline_user_args()
	if argumente.has("--alle"):
		_alle()
		quit(0)
		return
	_main = (load(SZENE) as PackedScene).instantiate()
	root.add_child(_main)


## Startet je Welt einen eigenen Prozess (frischer Kern, frische Szene).
func _alle() -> void:
	var welten: WorldData = WorldData.laden()
	var kante: int = int(_render.get("aufloesung", 900))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(ZIEL_ORDNER))
	for i in range(welten.anzahl()):
		var args: PackedStringArray = ["--path", ProjectSettings.globalize_path("res://"),
			"--resolution", "%dx%d" % [kante, kante], "-s", "res://tools/standort_bilder.gd", "--",
			"--welt", str(i + 1)]
		for s in _render.get("schalter", []) as Array:
			args.append(String(s))
		var ausgabe: Array = []
		var code: int = OS.execute(OS.get_executable_path(), args, ausgabe, true)
		var zeilen: PackedStringArray = String("\n".join(ausgabe)).split("\n")
		for z in zeilen:
			if z.begins_with("STANDORT") or z.contains("SCRIPT ERROR"):
				print(z)
		print("Welt %d (%s): Exit %d" % [i + 1, welten.id(i), code])


func _process(_delta: float) -> bool:
	if _main == null:
		return false
	_bilder += 1
	var warten: int = int(_render.get("warte_bilder", 150))
	if _bilder == warten - 10 and not _gerahmt:
		_rahme()
	if _bilder >= warten:
		_speichere()
		return true
	return false


## Oberflaeche aus, Hintergrund durchsichtig, Kamera auf die ganze Welt.
func _rahme() -> void:
	_gerahmt = true
	root.transparent_bg = true
	for knoten in _alle_knoten(_main):
		if knoten is CanvasLayer:
			(knoten as CanvasLayer).visible = false
		elif knoten is WorldEnvironment:
			var env: Environment = (knoten as WorldEnvironment).environment
			env.background_mode = Environment.BG_CLEAR_COLOR
			env.glow_enabled = false
			env.fog_enabled = false
		elif knoten is GPUParticles3D or knoten is CPUParticles3D:
			(knoten as Node3D).visible = false
	var kamera: Camera3D = root.get_viewport().get_camera_3d()
	if kamera == null:
		return
	kamera.set_process(false)
	kamera.set_physics_process(false)
	var box: AABB = _welt_box(_main)
	if box.size == Vector3.ZERO:
		return
	# Alle acht Ecken in Kamerarichtung projizieren und die Kamera so setzen,
	# dass das Rechteck um die Ecken das Bild genau fuellt.
	var basis: Basis = kamera.global_transform.basis
	var rechts: Vector3 = basis.x
	var oben: Vector3 = basis.y
	var mitte: Vector3 = box.get_center()
	var halb_x: float = 0.0
	var halb_y: float = 0.0
	for i in range(8):
		var ecke: Vector3 = box.get_endpoint(i) - mitte
		halb_x = maxf(halb_x, absf(ecke.dot(rechts)))
		halb_y = maxf(halb_y, absf(ecke.dot(oben)))
	var rand: float = float(_render.get("rand_faktor", 1.04))
	kamera.projection = Camera3D.PROJECTION_ORTHOGONAL
	kamera.keep_aspect = Camera3D.KEEP_HEIGHT
	var groesse: Vector2 = Vector2(root.get_viewport().get_visible_rect().size)
	var seitenverhaeltnis: float = groesse.x / maxf(1.0, groesse.y)
	kamera.size = maxf(halb_y * 2.0, halb_x * 2.0 / seitenverhaeltnis) * rand
	var abstand: float = box.size.length() * 2.0
	kamera.global_position = mitte + basis.z * abstand
	kamera.far = abstand * 3.0
	kamera.near = 0.05


func _welt_box(wurzel: Node) -> AABB:
	var box: AABB = AABB()
	var erste: bool = true
	for knoten in _alle_knoten(wurzel):
		if not (knoten is MeshInstance3D or knoten is MultiMeshInstance3D):
			continue
		var g: GeometryInstance3D = knoten as GeometryInstance3D
		if not g.is_visible_in_tree():
			continue
		var lokal: AABB = (g as VisualInstance3D).get_aabb()
		if lokal.size.length() > 500.0:
			continue
		var welt: AABB = g.global_transform * lokal
		if erste:
			box = welt
			erste = false
		else:
			box = box.merge(welt)
	return box


func _alle_knoten(wurzel: Node) -> Array[Node]:
	var liste: Array[Node] = [wurzel]
	var i: int = 0
	while i < liste.size():
		for kind in liste[i].get_children():
			liste.append(kind)
		i += 1
	return liste


func _speichere() -> void:
	var kern_knoten: Variant = _main.get("kern")
	var welt_id: String = ""
	if kern_knoten is GameCore:
		welt_id = (kern_knoten as GameCore).welt_id()
	if welt_id.is_empty():
		push_error("Welt unbekannt")
		quit(1)
		return
	var bild: Image = root.get_texture().get_image()
	bild.convert(Image.FORMAT_RGBA8)
	var schwelle: float = float(_render.get("alpha_schwelle", 0.04))
	var w: int = bild.get_width()
	var h: int = bild.get_height()
	var x0: int = w
	var y0: int = h
	var x1: int = -1
	var y1: int = -1
	for y in range(h):
		for x in range(w):
			if bild.get_pixel(x, y).a > schwelle:
				x0 = mini(x0, x)
				y0 = mini(y0, y)
				x1 = maxi(x1, x)
				y1 = maxi(y1, y)
	if x1 < 0:
		push_error("Bild leer: %s" % welt_id)
		quit(1)
		return
	var zuschnitt: Image = bild.get_region(Rect2i(x0, y0, x1 - x0 + 1, y1 - y0 + 1))
	var ziel_breite: int = int(_render.get("ziel_breite", 640))
	if zuschnitt.get_width() > ziel_breite:
		var faktor: float = float(ziel_breite) / float(zuschnitt.get_width())
		zuschnitt.resize(ziel_breite, maxi(1, int(zuschnitt.get_height() * faktor)), Image.INTERPOLATE_LANCZOS)
	var pfad: String = _bild_pfad % welt_id
	zuschnitt.save_png(ProjectSettings.globalize_path(pfad))
	print("STANDORT %s -> %s (%d x %d)" % [welt_id, pfad, zuschnitt.get_width(), zuschnitt.get_height()])
	quit(0)
