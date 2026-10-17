## Clips fliegen sichtbar von Station zu Station (ADR-021, WELT1_TIEFE 3.5).
##
## Die Kette war bisher eine Zahl und ein roter Ring. Jetzt sieht man, WAS durch
## sie laeuft: kleine Karten mit Play-Zeichen, die von der Idee zur Aufnahme,
## zum Schnitt und zum Upload fliegen. Vor der Station, die bremst, bleiben sie
## liegen und stapeln sich -- das ist der Engpass, ohne ein Wort.
##
## Nur Darstellung: Die Raten kommen aus dem Kern, gedeckelt auf ein lesbares
## Mass. Die Karten erzeugen kein Geld (ADR-007).
class_name ClipFluss
extends Node3D

## Ein Clip hat die Kette verlassen -- fuer die Ertragszahl darueber.
signal clip_raus(welt_position: Vector3, clips_pro_sekunde: float)

const MAX_RATE: float = 2.2       ## sichtbare Clips pro Sekunde, hoechstens
const MIN_RATE: float = 0.35
const FLUGZEIT: float = 0.9
const HOEHE: float = 1.25
const STAPEL_MAX: int = 8

## Die Clip-Spur, die gerade auf der Karte liegt. Der Kartenmarker findet darueber
## den Stapel, den man antippen kann -- ohne dass main.gd ihn durchreichen muss.
static var aktuell: ClipFluss = null

var kern: GameCore
var _orte: Array[Vector3] = []          ## Station je Glied, in Flussrichtung
var _ids: Array[StringName] = []
var _stapel: Array[int] = []            ## wartende Clips VOR jedem Glied
var _stapel_knoten: Array[Node3D] = []
var _arbeit: Array[float] = []          ## Fortschritt je Glied
var _ankunft_rest: float = 0.0
## Die Clips sind Play-Zeichen, die sich zur Kamera drehen. Der erste Versuch
## waren flache rote Kaertchen -- aus der Isometrie lagen sie wie Konfetti auf
## dem Boden, und niemand haette gewusst, dass es Clips sind.
var _textur: Texture2D
var _pool: Array[Node3D] = []

## Hat die Welt ein eigenes Teil, das fliegt (assets/world/<welt>/fluss_teil.glb)?
## Dann fliegt das Modell statt des Kaertchens: im Laden ein Shirt, in der Farm
## ein Block. Fehlt es, bleibt das Kaertchen -- still, weil es ein Standard ist
## und kein Loch.
const TEIL_PFAD: String = "res://assets/world/%s/fluss_teil.glb"
var _teil: PackedScene
var _teil_zeit: float = 0.0
## Wo die Anfragen eintreffen (worlds.json -> karte.eingang).
var _eingang: Vector3 = Vector3.ZERO


func aufbauen(k: GameCore, positionen: Dictionary, reihenfolge: Array[StringName], welt_id: String = "") -> void:
	kern = k
	aktuell = self
	# Die Lieferkiste wohnt hier, weil die Clip-Spur der Teil der Welt ist, der
	# mit dem Kern verbunden ist und mit jeder Welt neu entsteht.
	var kiste := Lieferkiste.new()
	add_child(kiste)
	kiste.aufbauen(kern)
	# K6 2c: Die Kasse am Ende der Kette und der Eingang, an dem Anfragen ankommen.
	var ende: Vector3 = positionen.get(reihenfolge[reihenfolge.size() - 1], Vector3.ZERO) as Vector3
	var kasse := Kassenstapel.new()
	add_child(kasse)
	kasse.aufbauen(kern, Kassenstapel.ort(kern.welten, kern.welt_index, ende))
	_eingang = Lieferkiste.eingang_ort(kern.welten, kern.welt_index, positionen.get(reihenfolge[0], Vector3.ZERO) as Vector3)
	if OS.is_debug_build() and OS.get_cmdline_user_args().has("--stapel"):
		kern.momente.erzwinge(MomentSystem.ART_STAPEL)
	if not welt_id.is_empty() and ResourceLoader.exists(TEIL_PFAD % welt_id):
		_teil = load(TEIL_PFAD % welt_id) as PackedScene
	for id in reihenfolge:
		if positionen.has(id):
			_ids.append(id)
			_orte.append(positionen[id] as Vector3)
			_stapel.append(0)
			_arbeit.append(0.0)
			var knoten := Node3D.new()
			knoten.position = (positionen[id] as Vector3) + Vector3(-0.55, 0.0, 0.75)
			add_child(knoten)
			_stapel_knoten.append(knoten)
	# Weisse Kaertchen mit kleinem Play-Zeichen: Rot gehoert dem Engpass allein.
	# Rote Scheiben lagen vorher wie verstreuter Muell auf dem Boden.
	_textur = UiStil.symbol("clip")


func _process(delta: float) -> void:
	if kern == null or _ids.is_empty():
		return
	if _teil != null:
		# Modelle drehen sich langsam -- ein stehendes Teil liest sich wie Deko.
		_teil_zeit += delta
		for m in _pool:
			if m.visible:
				m.rotation.y = _teil_zeit * 2.5
	# Neue Ideen kommen im Tempo der ersten Station.
	_ankunft_rest += _rate(0) * delta
	while _ankunft_rest >= 1.0:
		_ankunft_rest -= 1.0
		if _stapel[0] < STAPEL_MAX:
			_stapel[0] += 1
			_fliege_anfrage()
	# Jedes Glied arbeitet seinen Stapel im eigenen Tempo ab und schickt den
	# Clip zum naechsten. Wer langsamer ist als sein Vorgaenger, sammelt an.
	for i in range(_ids.size()):
		if _stapel[i] <= 0:
			_arbeit[i] = 0.0
			continue
		_arbeit[i] += _rate(i) * delta
		if _arbeit[i] >= 1.0:
			_arbeit[i] -= 1.0
			_stapel[i] -= 1
			if i + 1 < _ids.size() and _aktiv(i + 1):
				_fliege(_orte[i], _orte[i + 1], i + 1)
			else:
				_fliege_hoch(_orte[i])
	_fuelle_tippstapel()
	_zeige_stapel()


func _exit_tree() -> void:
	if aktuell == self:
		aktuell = null


# --- Der Stapel zum Antippen (K3 B2) ---------------------------------------------

## Ab so vielen Teilen ist ein Stapel antippbar: sobald mehr warten, als sichtbar
## uebereinander liegen -- dann steht der Zaehler darueber.
func stapel_antippbar_ab() -> int:
	return STAPEL_SICHTBAR + 1


## Waehrend eines Stapel-Moments liegt am Engpass mindestens ein antippbarer
## Stapel. Nur Darstellung: Der Engpass staut ohnehin, hier wird er sichtbar.
func _fuelle_tippstapel() -> void:
	if not kern.momente.ist_stapel():
		return
	var i: int = _ids.find(kern.momente.station)
	if i >= 0:
		_stapel[i] = maxi(_stapel[i], stapel_antippbar_ab())


func stapel_anzahl(station_id: StringName) -> int:
	var i: int = _ids.find(station_id)
	return _stapel[i] if i >= 0 else 0


## Weltposition ueber dem Stapel vor `station_id` (Vector3.INF = keiner).
func stapel_ort(station_id: StringName) -> Vector3:
	var i: int = _ids.find(station_id)
	if i < 0:
		return Vector3.INF
	return _stapel_knoten[i].global_position + Vector3(0.0, 0.35 + float(STAPEL_SICHTBAR) * STAPEL_SCHRITT * 0.5, 0.0)


## Der Stapel ist abgeraeumt: Alle Teile fliegen auf einmal hoch und sind raus.
## Es kommt kein Ertrag dazu -- der war schon gezaehlt.
func raeume_ab(station_id: StringName) -> void:
	var i: int = _ids.find(station_id)
	if i < 0:
		return
	var n: int = mini(_stapel[i], STAPEL_MAX)
	_stapel[i] = 0
	var von: Vector3 = _stapel_knoten[i].position
	for k in range(n):
		var karte := _hole()
		karte.position = von + Vector3(0.0, 0.35 + float(mini(k, STAPEL_SICHTBAR)) * STAPEL_SCHRITT, 0.0)
		var winkel: float = TAU * float(k) / float(maxi(n, 1))
		var ziel: Vector3 = karte.position + Vector3(cos(winkel) * 0.9, 2.4, sin(winkel) * 0.9)
		var t := create_tween().set_parallel(true)
		t.tween_property(karte, "position", ziel, 0.55).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT).set_delay(float(k) * 0.03)
		t.tween_property(karte, "scale", Vector3(0.2, 0.2, 0.2), 0.55).set_ease(Tween.EASE_IN).set_delay(float(k) * 0.03)
		t.chain().tween_callback(func() -> void: _gib_zurueck(karte))
	_zeige_stapel()


func _aktiv(i: int) -> bool:
	var s: StationModel = kern.kette.station(_ids[i])
	return s != null and s.freigeschaltet


func _rate(i: int) -> float:
	var s: StationModel = kern.kette.station(_ids[i])
	if s == null or not s.freigeschaltet:
		return 0.0
	var roh: float = s.durchsatz()
	if Ids.CHAIN.has(_ids[i]):
		# Die Kette wird auf ein lesbares Tempo ABGEBILDET, nicht abgeschnitten:
		# Alle Glieder teilen denselben Faktor, damit das Verhaeltnis -- und damit
		# der Stau -- stimmt.
		var hoechste: float = 0.0
		for id in Ids.CHAIN:
			var c: StationModel = kern.kette.station(id)
			if c != null:
				hoechste = maxf(hoechste, c.durchsatz())
		if hoechste <= 0.0:
			return 0.0
		return clampf(roh / hoechste * MAX_RATE, MIN_RATE, MAX_RATE)
	# Der Upload arbeitet so schnell, wie die Kette liefert.
	return MAX_RATE


func _fliege(von: Vector3, nach: Vector3, ziel_index: int) -> void:
	var karte := _hole()
	var start: Vector3 = von + Vector3(0.0, HOEHE, 0.0)
	var ende: Vector3 = nach + Vector3(0.0, HOEHE, 0.0)
	karte.position = start
	karte.scale = Vector3.ONE
	var t := create_tween()
	t.tween_method(func(f: float) -> void:
		var p: Vector3 = start.lerp(ende, f)
		p.y += sin(f * PI) * 0.9
		karte.position = p, 0.0, 1.0, FLUGZEIT).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	t.tween_callback(func() -> void:
		_gib_zurueck(karte)
		if ziel_index < _stapel.size():
			_stapel[ziel_index] = mini(_stapel[ziel_index] + 1, STAPEL_MAX))


## Eine Anfrage-Karte (Briefumschlag mit Siegel) wandert vom Eingang in die erste
## Station. Gekoppelt an den Durchsatz: Sie startet genau dann, wenn ein neues
## Teil in die Kette kommt. Nur Darstellung -- kein Geld.
func _fliege_anfrage() -> void:
	var brief := Node3D.new()
	var body := MeshInstance3D.new()
	var b := BoxMesh.new()
	b.size = Vector3(0.62, 0.05, 0.42)
	body.mesh = b
	var m1 := StandardMaterial3D.new()
	m1.albedo_color = Color("f6ecd2")
	m1.roughness = 0.7
	body.material_override = m1
	brief.add_child(body)
	var klappe := MeshInstance3D.new()
	var kb := BoxMesh.new()
	kb.size = Vector3(0.62, 0.056, 0.05)
	klappe.mesh = kb
	var m2 := StandardMaterial3D.new()
	m2.albedo_color = Color("d9c79c")
	klappe.material_override = m2
	klappe.position = Vector3(0.0, 0.0, -0.06)
	brief.add_child(klappe)
	var siegel := MeshInstance3D.new()
	var c := CylinderMesh.new()
	c.top_radius = 0.075
	c.bottom_radius = 0.075
	c.height = 0.07
	siegel.mesh = c
	var m3 := StandardMaterial3D.new()
	m3.albedo_color = Color("d2453a")
	m3.metallic = 0.3
	m3.roughness = 0.35
	siegel.material_override = m3
	siegel.position = Vector3(0.0, 0.03, 0.0)
	brief.add_child(siegel)
	add_child(brief)
	brief.scale = Vector3.ONE * 1.6
	var start: Vector3 = _eingang + Vector3(0.0, 0.5, 0.0)
	var ende: Vector3 = _orte[0] + Vector3(-0.2, HOEHE, 0.2)
	brief.position = start
	var t := create_tween()
	t.tween_method(func(f: float) -> void:
		var p: Vector3 = start.lerp(ende, f)
		p.y += sin(f * PI) * 1.1
		brief.position = p
		brief.rotation.y = f * 0.8
		brief.scale = Vector3.ONE * lerpf(1.6, 0.5, f * f), 0.0, 1.0, FLUGZEIT * 1.3).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	t.tween_callback(brief.queue_free)


## Am Ende der Kette steigt der Clip auf und verschwindet -- er ist raus.
func _fliege_hoch(von: Vector3) -> void:
	var karte := _hole()
	karte.position = von + Vector3(0.0, HOEHE, 0.0)
	var t := create_tween().set_parallel(true)
	t.tween_property(karte, "position:y", karte.position.y + 2.2, 0.8).set_ease(Tween.EASE_OUT)
	t.tween_property(karte, "scale", Vector3(0.2, 0.2, 0.2), 0.8).set_ease(Tween.EASE_IN)
	t.chain().tween_callback(func() -> void: _gib_zurueck(karte))
	clip_raus.emit(von + Vector3(0.0, HOEHE + 1.0, 0.0), _rate(_ids.size() - 1))


## Wartende Clips als kleiner Stapel neben der Station: hoechstens drei
## Karten, sauber uebereinander; wartet mehr, steht ein Zaehler "x7" darueber.
## Sieben rote Karten uebereinander sahen wie Unordnung aus.
const STAPEL_SICHTBAR: int = 3
const STAPEL_SCHRITT: float = 0.26


func _zeige_stapel() -> void:
	for i in range(_stapel_knoten.size()):
		var knoten: Node3D = _stapel_knoten[i]
		# Vor der ersten Station liegt nichts -- ausser waehrend eines Stapel-Moments dort.
		var soll: int = _stapel[i] if i > 0 or (kern.momente.ist_stapel() and kern.momente.station == _ids[i]) else 0
		var karten: int = mini(soll, STAPEL_SICHTBAR)
		var zaehler: Label3D = knoten.get_node_or_null("Zaehler") as Label3D
		var vorhanden: int = knoten.get_child_count() - (1 if zaehler != null else 0)
		while vorhanden < karten:
			var m := _neues_zeichen(0.0011)
			m.position = Vector3(0.0, 0.35 + float(vorhanden) * STAPEL_SCHRITT, 0.0)
			knoten.add_child(m)
			vorhanden += 1
		while vorhanden > karten:
			var letztes: Node = null
			for k in knoten.get_children():
				if k != zaehler:
					letztes = k
			knoten.remove_child(letztes)
			letztes.queue_free()
			vorhanden -= 1
		if soll > STAPEL_SICHTBAR:
			if zaehler == null:
				zaehler = Label3D.new()
				zaehler.name = "Zaehler"
				zaehler.billboard = BaseMaterial3D.BILLBOARD_ENABLED
				zaehler.fixed_size = true
				zaehler.no_depth_test = true
				zaehler.pixel_size = 0.0016
				zaehler.font = UiStil.schrift(UiStil.FETT, 48)
				zaehler.font_size = 48
				zaehler.modulate = UiStil.PAPIER
				zaehler.outline_modulate = UiStil.TINTE
				zaehler.outline_size = 14
				zaehler.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				knoten.add_child(zaehler)
			zaehler.position = Vector3(0.0, 0.35 + float(STAPEL_SICHTBAR) * STAPEL_SCHRITT + 0.12, 0.0)
			var text: String = "×%d" % soll
			if zaehler.text != text:
				zaehler.text = text
		elif zaehler != null:
			knoten.remove_child(zaehler)
			zaehler.queue_free()


## Ein fliegendes oder wartendes Teil: das Modell der Welt oder das Kaertchen.
## `groesse` ist die Pixelgroesse des Kaertchens; das Modell wird im selben
## Verhaeltnis skaliert (0,0013 = volle Groesse).
func _neues_zeichen(groesse: float) -> Node3D:
	if _teil != null:
		var teil: Node3D = _teil.instantiate() as Node3D
		teil.set_meta("grundgroesse", groesse / 0.0013)
		teil.scale = Vector3.ONE * (groesse / 0.0013)
		return teil
	return _kaertchen(groesse)


func _kaertchen(groesse: float) -> Sprite3D:
	var m := Sprite3D.new()
	m.texture = _textur
	m.pixel_size = groesse
	m.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	m.shaded = false
	m.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return m


func _hole() -> Node3D:
	var m: Node3D
	if _pool.is_empty():
		m = _neues_zeichen(0.0013)
		add_child(m)
	else:
		m = _pool.pop_back()
	m.visible = true
	return m


func _gib_zurueck(m: Node3D) -> void:
	if not is_instance_valid(m):
		return
	m.visible = false
	_pool.append(m)
