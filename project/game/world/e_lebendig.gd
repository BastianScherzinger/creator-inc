## Lebendigkeit einer Welt: Himmel, Glow, Partikel, animierte Kulissen,
## pulsierende Leuchtflaechen. Alles datengetrieben (worlds.json + lebendig.json),
## ein Schluessel ohne Daten tut nichts.
##
## Performance (Mittelklasse-Handy, Compatibility-Renderer):
## - feste Obergrenzen aus lebendig.json (Animationen, Leuchtflaechen, Partikel-Systeme, Menge)
## - alle Listen werden beim Aufbau gebaut; _process legt nichts neu an
##   (nur Zahlen, Vector3-Werte und vorhandene Knoten)
## - Partikel: unshaded, 16x16-Textur, wenige Stueck, keine Schatten
## - ohne Daten: set_process(false), kein Knoten im Baum ausser dem leeren Wurzelknoten
## Nur Darstellung -- hier entsteht kein Geld (ADR-007), der Takt ist ein Bildtakt.
class_name Lebendig
extends Node3D

enum Typ { DREHEN, TREIBEN, FOERDERN, WACKELN, FAHREN }

## Zeichnet Verlauf, Sterne und Mond auf eine CanvasLayer hinter der Welt.
class HimmelZeichner extends Control:
	var oben: Color = Color.BLACK
	var unten: Color = Color.BLACK
	var sterne: PackedVector2Array = PackedVector2Array()
	var sterne_alpha: PackedFloat32Array = PackedFloat32Array()
	var stern_groesse: float = 1.5
	var stern_farbe: Color = Color.WHITE
	var mond: Dictionary = {}
	var mit_verlauf: bool = true
	var mit_deko: bool = true

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE

	func _notification(was: int) -> void:
		if was == NOTIFICATION_RESIZED:
			queue_redraw()

	func _draw() -> void:
		var r: Vector2 = size
		if mit_verlauf:
			var ecken := PackedVector2Array([Vector2(0, 0), Vector2(r.x, 0), Vector2(r.x, r.y), Vector2(0, r.y)])
			draw_polygon(ecken, PackedColorArray([oben, oben, unten, unten]))
		if not mit_deko:
			return
		for i in sterne.size():
			var c: Color = stern_farbe
			c.a = sterne_alpha[i]
			draw_circle(Vector2(sterne[i].x * r.x, sterne[i].y * r.y), stern_groesse, c)
		if not mond.is_empty():
			var m := Vector2(float(mond["x"]) * r.x, float(mond["y"]) * r.y)
			var g: float = float(mond["groesse"])
			var mc: Color = mond["farbe"] as Color
			var halo: Color = mc
			halo.a = float(mond["halo_alpha"])
			draw_circle(m, g * float(mond["halo"]), halo)
			draw_circle(m, g * (1.0 + (float(mond["halo"]) - 1.0) * 0.45), halo)
			draw_circle(m, g, mc)

var _regeln: Dictionary = {}
var _zeit: float = 0.0

# Animationen (parallele Listen, Index = Animation)
var _a_knoten: Array[Node3D] = []
var _a_typ: PackedInt32Array = PackedInt32Array()
var _a_achse: PackedVector3Array = PackedVector3Array()
var _a_tempo: PackedFloat32Array = PackedFloat32Array()
var _a_weite: PackedFloat32Array = PackedFloat32Array()
var _a_phase: PackedFloat32Array = PackedFloat32Array()
var _a_basis: PackedVector3Array = PackedVector3Array()
var _a_winkel: PackedFloat32Array = PackedFloat32Array()
var _a_mat: Array[StandardMaterial3D] = []         ## nur FOERDERN: das duplizierte Material
var _a_uv: PackedVector3Array = PackedVector3Array()
var _a_rot0: PackedVector3Array = PackedVector3Array()

# Fahrzeuge (Index = Fahrzeug)
var _f_knoten: Array[Node3D] = []
var _f_route: Array[PackedVector3Array] = []
var _f_warten: Array[PackedFloat32Array] = []
var _f_modus: PackedInt32Array = PackedInt32Array()   ## 0 Schleife, 1 hin und her, 2 einmal
var _f_tempo: PackedFloat32Array = PackedFloat32Array()
var _f_pause: PackedFloat32Array = PackedFloat32Array()
var _f_versatz: PackedFloat32Array = PackedFloat32Array()
var _f_basis_y: PackedFloat32Array = PackedFloat32Array()
var _f_seg: PackedInt32Array = PackedInt32Array()
var _f_dir: PackedInt32Array = PackedInt32Array()
var _f_weg: PackedFloat32Array = PackedFloat32Array()
var _f_rest_warten: PackedFloat32Array = PackedFloat32Array()
var _f_rest_pause: PackedFloat32Array = PackedFloat32Array()

# Leuchtflaechen (Index = Material)
var _p_mat: Array[StandardMaterial3D] = []
var _p_hz: PackedFloat32Array = PackedFloat32Array()
var _p_min: PackedFloat32Array = PackedFloat32Array()
var _p_max: PackedFloat32Array = PackedFloat32Array()
var _p_form: PackedInt32Array = PackedInt32Array()    ## 0 Sinus, 1 Blinken, 2 Flackern
var _p_phase: PackedFloat32Array = PackedFloat32Array()

# Partikel mit Wiederholung (Funken)
var _w_knoten: Array[GPUParticles3D] = []
var _w_intervall: PackedFloat32Array = PackedFloat32Array()
var _w_rest: PackedFloat32Array = PackedFloat32Array()

var _punkt_textur: Texture2D
var _fluegel_textur: Texture2D
var _himmel_ebene: CanvasLayer
var _aufgabe: AufgabenHinweis


## "!" ueber einer Figur = Mini-Aufgabe (K3 B3).
##
## Die Aufgaben sind gewoehnliche Ziele des Kerns mit den IDs `ziel_auftrag_1..n`
## (balance/<welt>.json, Kette "auftrag"); welche Figur fragt und was sie sagt,
## steht in theme.json -> `auftraege`. Es steht hoechstens EIN "!" -- ueber der
## Figur der ersten noch nicht eingeloesten Aufgabe, sobald deren Ziel in der
## Zielleiste steht --, und nur, wenn gerade kein Upgrade-Pfeil pulst (ein
## Hinweis zur Zeit, K3 PLAN 1), kein Menue, keine Szene, kein Tutorial offen ist.
##
## Tipp -> Szene ueber die Modal-Schlange. Offenes Ziel: `satz` (warum) plus
## `aufgabe_format` mit dem echten Zieltext (was), Antwort `knopf_start`.
## Erfuelltes Ziel: `dank`, Antwort `knopf_holen`. Beide Antworten tragen die
## Ziel-ID (`auftrag`); SzeneView ruft danach HUD.springe_zu_ziel (hinfuehren
## bzw. einloesen). Nur Darstellung: Hier entsteht kein Geld (ADR-007).
##
## Pruefschalter (nur Debug-Builds), fuer Vorschauen:
##   --aufgabe-probe <ziel_id>   dieses Ziel gilt als erste Aufgabe (ohne Pfeil-Sperre)
##   --aufgabe-tippen            die Szene oeffnet sich, sobald das "!" steht
class AufgabenHinweis extends Node:
	const PRAEFIX: String = "ziel_auftrag_"
	const ANZAHL: int = 3
	const TAKT_S: float = 0.25          ## so oft wird der Zustand neu geprueft
	const RUHE_S: float = 1.0           ## so lange darf kein Pfeil pulsen, bevor "!" kommt
	const KOPF_HOEHE: float = 2.3       ## Meter ueber dem Fusspunkt der Figur
	const WIPPEN_PX: float = 6.0
	const WIPPEN_HZ: float = 0.5
	const EBENE_SZENE: int = 30         ## wie die Story-Szenen des HUD
	const SUCHE_S: float = 1.0          ## so oft wird das HUD gesucht, solange es fehlt

	var _hud: Hud
	var _knopf: Control
	var _symbol: Label
	var _aufgabe_id: String = ""
	var _figur: Node3D
	var _rest: float = 0.0
	var _ruhe: float = 0.0
	var _zeit: float = 0.0
	var _szene_offen: bool = false
	var _probe: String = ""
	var _tippen: bool = false
	var _getippt: bool = false
	var _suche_rest: float = 0.0

	func _init() -> void:
		if not OS.is_debug_build():
			return
		var args: PackedStringArray = OS.get_cmdline_user_args()
		var i: int = args.find("--aufgabe-probe")
		if i >= 0 and i + 1 < args.size():
			_probe = args[i + 1]
		_tippen = args.has("--aufgabe-tippen")

	func _process(delta: float) -> void:
		_zeit += delta
		if _knopf != null and is_instance_valid(_knopf) and _knopf.visible:
			_setze_ort()
		_rest -= delta
		if _rest > 0.0:
			return
		_rest = TAKT_S
		_pruefe(TAKT_S)

	## Die Aufgabe, deren "!" gerade steht ("" = keins). Fuer Tests und Vorschauen.
	func sichtbare_aufgabe() -> String:
		return _aufgabe_id if _knopf != null and is_instance_valid(_knopf) and _knopf.visible else ""

	func _daten() -> Dictionary:
		if _hud == null or _hud.thema == null:
			return {}
		return _hud.thema.abschnitt("auftraege")

	## Ziel-ID zu einer Aufgabe; mit --aufgabe-probe steht ein vorhandenes Ziel fuer die erste.
	func _ziel_zu(aufgabe_id: String) -> String:
		if not _probe.is_empty() and aufgabe_id == PRAEFIX + "1":
			return _probe
		return aufgabe_id

	func _pruefe(dt: float) -> void:
		if _hud == null or not is_instance_valid(_hud):
			_suche_rest -= dt
			if _suche_rest > 0.0:
				return
			_suche_rest = SUCHE_S
			_hud = _finde_hud(get_tree().root) if is_inside_tree() else null
			if _hud == null:
				return
		var id: String = _aktuelle_aufgabe()
		var pulst: bool = _probe.is_empty() and _hud.marker != null and not _hud.marker.empfehlung().is_empty()
		_ruhe = 0.0 if pulst else _ruhe + dt
		var zeigen: bool = not id.is_empty() and not _szene_offen and not _blockiert() \
			and (_ruhe >= RUHE_S or not _probe.is_empty())
		if zeigen and (id != _aufgabe_id or _figur == null or not is_instance_valid(_figur) \
				or not _figur.is_visible_in_tree()):
			_figur = _finde_figur(id)
		_aufgabe_id = id
		zeigen = zeigen and _figur != null
		if not zeigen:
			if _knopf != null and is_instance_valid(_knopf):
				_knopf.visible = false
			return
		_zeige_knopf()
		if _tippen and not _getippt:
			_getippt = true
			_oeffne_szene()

	func _blockiert() -> bool:
		return _hud.tutorial_aktiv or _hud.sheet_offen() or ModalSchlange.global().ist_offen() \
			or _hud.marker == null or _hud.marker.kamera == null or not is_instance_valid(_hud.marker.kamera)

	## Die erste Aufgabe, die es gibt und die noch nicht eingeloest ist -- aber nur,
	## wenn ihr Ziel schon in der Zielleiste steht (sonst kommt sie spaeter).
	func _aktuelle_aufgabe() -> String:
		var kern: GameCore = _hud.kern
		if kern == null or kern.ziele == null or _daten().is_empty():
			return ""
		var sichtbar: Dictionary = {}
		for z in kern.ziele.sichtbar():
			sichtbar[String((z as Dictionary).get("id", ""))] = true
		for i in range(1, ANZAHL + 1):
			var aufgabe_id: String = PRAEFIX + str(i)
			var ziel_id: String = _ziel_zu(aufgabe_id)
			if kern.ziele.definition(ziel_id).is_empty() or kern.ziele.ist_eingeloest(ziel_id):
				continue
			if not (_daten().get(aufgabe_id, null) is Dictionary):
				return ""
			return aufgabe_id if sichtbar.has(ziel_id) or not _probe.is_empty() else ""
		return ""

	static func _finde_hud(k: Node) -> Hud:
		if k is Hud:
			return k as Hud
		for kind in k.get_children():
			if kind is Hud:
				return kind as Hud
			# Das HUD haengt an einer CanvasLayer; Modelle und Meshes muss niemand durchsuchen.
			if kind is VisualInstance3D or kind is Control:
				continue
			var h: Hud = _finde_hud(kind)
			if h != null:
				return h
		return null

	## Die Figur der Aufgabe auf der Karte (Modell aus absender_figur); fehlt sie
	## (noch nicht da, ausgezogen), fragt die erste andere Figur der Welt.
	func _finde_figur(aufgabe_id: String) -> Node3D:
		var welt: Node = get_parent().get_parent() if get_parent() != null else null
		if welt == null:
			return null
		var figuren: Dictionary = _hud.thema.abschnitt("absender_figur")
		var eigen: String = String((_daten().get(aufgabe_id, {}) as Dictionary).get("figur", ""))
		var reihe: Array[String] = []
		if figuren.has(eigen):
			reihe.append(String(figuren[eigen]))
		for schluessel in figuren.keys():
			if not reihe.has(String(figuren[schluessel])):
				reihe.append(String(figuren[schluessel]))
		for modell in reihe:
			var k: Node3D = _suche_modell(welt, "/" + modell + ".glb")
			if k != null:
				return k
		return null

	## Sucht ein sichtbares, aus `endung` instanziertes Modell. Steigt nicht in
	## fremde Szenen hinab (Raeume, Moebel), nur in Halter wie die Bewohner.
	static func _suche_modell(k: Node, endung: String) -> Node3D:
		for kind in k.get_children():
			if not (kind is Node3D):
				continue
			var pfad: String = (kind as Node).scene_file_path
			if pfad.ends_with(endung) and (kind as Node3D).is_visible_in_tree():
				return kind as Node3D
			if pfad.is_empty():
				var tiefer: Node3D = _suche_modell(kind, endung)
				if tiefer != null:
					return tiefer
		return null

	func _zeige_knopf() -> void:
		if _knopf == null or not is_instance_valid(_knopf):
			_baue_knopf()
		_symbol.text = String(_daten().get("symbol", "!"))
		if not _knopf.visible:
			_knopf.visible = true
			_setze_ort()
			UiStil.aufploppen(_knopf.get_child(0) as Control, 0.6)

	func _baue_knopf() -> void:
		var kante: float = maxf(Kartenmarker.hinweis("tippziel_min_px"), UiStil.TIPPZIEL)
		_knopf = Control.new()
		_knopf.name = "AufgabeKnopf"
		_knopf.custom_minimum_size = Vector2(kante, kante)
		_knopf.size = Vector2(kante, kante)
		_knopf.mouse_filter = Control.MOUSE_FILTER_STOP
		var plakette := PanelContainer.new()
		var innen: float = kante * 0.68
		plakette.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_CHIP,
			UiStil.KONTUR, 0.0, UiStil.SCHATTEN_Y))
		plakette.custom_minimum_size = Vector2(innen, innen)
		plakette.size = Vector2(innen, innen)
		plakette.position = Vector2((kante - innen) * 0.5, (kante - innen) * 0.5)
		plakette.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_symbol = UiStil.label("", UiStil.GR_TITEL, UiStil.TINTE, UiStil.FETT)
		_symbol.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_symbol.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		plakette.add_child(_symbol)
		_knopf.add_child(plakette)
		_knopf.gui_input.connect(func(e: InputEvent) -> void:
			if UiStil.ist_tipp(e):
				UiStil.eindruecken(plakette)
				_oeffne_szene())
		_knopf.visible = false
		# Unter dem Kartenmarker: liegt damit unter Kopfleiste, Menues und Szenen.
		var eltern: Control = _hud.marker if _hud.marker != null else _hud
		eltern.add_child(_knopf)

	func _setze_ort() -> void:
		if _figur == null or not is_instance_valid(_figur) or _hud == null or _hud.marker == null:
			return
		var kamera: Camera3D = _hud.marker.kamera
		if kamera == null or not is_instance_valid(kamera):
			return
		var kopf: Vector3 = _figur.global_position + Vector3.UP * KOPF_HOEHE
		if kamera.is_position_behind(kopf):
			_knopf.visible = false
			return
		var p: Vector2 = kamera.unproject_position(kopf)
		var wippen: float = sin(_zeit * TAU * WIPPEN_HZ) * WIPPEN_PX
		_knopf.position = p - Vector2(_knopf.size.x * 0.5, _knopf.size.y) + Vector2(0.0, wippen)

	func _oeffne_szene() -> void:
		if _szene_offen or _hud == null or _aufgabe_id.is_empty():
			return
		var szene: Dictionary = _szene_fuer(_aufgabe_id)
		if szene.is_empty():
			return
		_szene_offen = true
		if _knopf != null and is_instance_valid(_knopf):
			_knopf.visible = false
		var hud: Hud = _hud
		ModalSchlange.global().anmelden(&"szene", func(fertig: Callable) -> void:
			hud.schliesse_alle()
			var ebene := CanvasLayer.new()
			ebene.layer = EBENE_SZENE
			hud.add_child(ebene)
			var ansicht: SzeneView = SzeneView.zeige_szene(ebene, szene, hud.thema, hud.audio)
			ansicht.beendet.connect(func(_i: int, _t: String) -> void:
				_szene_offen = false
				_ruhe = 0.0
				fertig.call()), true)   # vom Spieler angetippt: kein Fensterabstand (K6 1c)

	## Die Szene zur Aufgabe: offen -> warum + was + "Mach ich"; erfuellt -> Dank + "Abholen".
	func _szene_fuer(aufgabe_id: String) -> Dictionary:
		var d: Dictionary = _daten()
		var eintrag: Dictionary = d.get(aufgabe_id, {}) as Dictionary
		var ziel_id: String = _ziel_zu(aufgabe_id)
		var z: Dictionary = _hud.kern.ziele.definition(ziel_id)
		if eintrag.is_empty() or z.is_empty():
			return {}
		var von: String = String(eintrag.get("figur", ""))
		if GoalSystem.erfuellt(z, _hud.kern.messwert):
			return {"von": von, "blasen": [{"von": von, "stimmung": "jubelnd", "text": String(eintrag.get("dank", ""))}],
				"antworten": [{"text": String(d.get("knopf_holen", "")), "reaktion": "", "auftrag": ziel_id}]}
		# Der Zieltext aus den Formaten (nicht der Missionsname): sagt genau, was zu tun ist.
		var ohne_namen: Dictionary = z.duplicate()
		ohne_namen.erase("id")
		var was: String = String(d.get("aufgabe_format", "%s"))
		was = was % WeltTexte.ziel(_hud.thema, ohne_namen) if was.contains("%s") else was
		return {"von": von, "blasen": [{"von": von, "stimmung": "neutral", "text": String(eintrag.get("satz", ""))},
			{"von": von, "stimmung": "neutral", "text": was}],
			"antworten": [{"text": String(d.get("knopf_start", "")), "reaktion": "", "auftrag": ziel_id}]}


## Modellpfad einer Figur: eigener Welt-Ordner, dann gemeinsam, dann die lose Datei (Kunden).
static func figur_pfad(welt_id: String, modell: String) -> String:
	for pfad in ["res://assets/characters/%s/%s.glb" % [welt_id, modell],
			"res://assets/characters/gemeinsam/%s.glb" % modell,
			"res://assets/characters/%s.glb" % modell]:
		if ResourceLoader.exists(pfad):
			return pfad
	return ""


## Mitarbeiter-Figuren (K6 2a): Sobald an einer Station ein Crew-Rang gekauft ist
## (`kern.crew`), steht dort eine Figur mit Namensschild, die arbeitet. Rang 2 und 3 sehen
## anders aus (Groesse, Kopfhoerer, Brosche, Ring). Beim Kauf erscheint sie mit Plopp und Staub.
## Nur Darstellung (ADR-007): hier entsteht kein Geld, der Kern bleibt unveraendert.
##
## Pruefschalter (nur Debug-Builds): `--crew-probe` zeigt die Raenge 1, 2, 3 reihum an allen
## Stationen, ohne den Kern anzufassen; `--crew-auftritt` dazu: schon die ersten erscheinen mit Plopp.
class CrewFiguren extends Node3D:
	const TAKT_S: float = 0.25
	const SUCHE_S: float = 1.0

	var _regeln: Dictionary = {}
	var _hud: Hud
	var _eintraege: Dictionary = {}     ## Station (String) -> Dictionary der Figur
	var _zeit: float = 0.0
	var _rest: float = 0.0
	var _suche_rest: float = 0.0
	var _bereit: bool = false           ## erst nach dem ersten Abgleich gibt es Auftritte
	var _probe: bool = false
	var _punkt_textur: Texture2D

	func _init(regeln: Dictionary = {}) -> void:
		_regeln = regeln
		name = "CrewFiguren"
		if OS.is_debug_build():
			var args: PackedStringArray = OS.get_cmdline_user_args()
			_probe = args.has("--crew-probe")
			_bereit = args.has("--crew-auftritt")   # Vorschau: auch die ersten Figuren erscheinen mit Plopp

	func _process(delta: float) -> void:
		var d: float = minf(delta, 0.1)
		_zeit += d
		_rest -= d
		if _rest <= 0.0:
			_rest = TAKT_S
			_suche_rest -= TAKT_S
			if _hud == null or not is_instance_valid(_hud):
				if _suche_rest <= 0.0:
					_suche_rest = SUCHE_S
					_hud = AufgabenHinweis._finde_hud(get_tree().root) if is_inside_tree() else null
			if _hud != null and _hud.kern != null and _hud.thema != null:
				gleiche_an(_hud.kern, _hud.thema)
		for k in _eintraege:
			_arbeite(_eintraege[k] as Dictionary)

	## Welche Stationen gerade eine Figur zeigen -- fuer Tests und Vorschauen.
	func stationen_mit_figur() -> Array[String]:
		var liste: Array[String] = []
		for k in _eintraege:
			liste.append(String(k))
		return liste

	func figur(station: String) -> Node3D:
		return (_eintraege.get(station, {}) as Dictionary).get("halter", null) as Node3D

	func rang_von(station: String) -> int:
		return int((_eintraege.get(station, {}) as Dictionary).get("rang", 0))

	func _crew_regeln() -> Dictionary:
		return _regeln.get("crew", {}) as Dictionary

	## Gleicht die Figuren mit dem Kern ab: fehlende bauen, geaenderte Raenge aktualisieren.
	func gleiche_an(kern: GameCore, thema: ThemeData) -> void:
		var i: int = kern.welt_index
		var positionen: Dictionary = kern.welten.stationen(i)
		var figuren: Dictionary = kern.welten.figuren_roh(i)
		var crew_daten: Dictionary = thema.abschnitt("crew")
		var nr: int = 0
		for id in Ids.ALL_STATIONS:
			var s: String = String(id)
			nr += 1
			if not positionen.has(id) or not (crew_daten.get(s, null) is Dictionary):
				continue
			var rang: int = kern.crew.rang(id) if kern.crew.hat(id) else 0
			if _probe:
				rang = maxi(rang, (nr - 1) % 3 + 1)
			if rang < 1:
				if _eintraege.has(s):
					((_eintraege[s] as Dictionary)["halter"] as Node3D).queue_free()
					_eintraege.erase(s)
				continue
			var eintrag: Dictionary = crew_daten[s] as Dictionary
			if not _eintraege.has(s):
				var e: Dictionary = _baue(kern, thema, s, id, eintrag, figuren, positionen, nr)
				if e.is_empty():
					continue
				_eintraege[s] = e
				_setze_rang(e, eintrag, rang, _bereit)
			elif int((_eintraege[s] as Dictionary)["rang"]) != rang:
				_setze_rang(_eintraege[s] as Dictionary, eintrag, rang, true)
		_bereit = true

	func _baue(kern: GameCore, thema: ThemeData, s: String, id: StringName, eintrag: Dictionary,
			figuren: Dictionary, positionen: Dictionary, nr: int) -> Dictionary:
		var modell: String = LebendigDaten.crew_modell(eintrag, thema.abschnitt("absender_figur"), _regeln, nr)
		var pfad: String = Lebendig.figur_pfad(kern.welt_id(), modell)
		if pfad.is_empty():
			return {}
		var platz: Dictionary = LebendigDaten.crew_platz(figuren, s, _regeln)
		var halter := Node3D.new()
		halter.name = "Crew_" + s
		halter.position = (positionen[id] as Vector3) + Vector3(float(platz["x"]), 0.0, float(platz["z"]))
		var koerper: Node3D = (load(pfad) as PackedScene).instantiate() as Node3D
		koerper.rotation_degrees.y = float(platz["blick"])
		halter.add_child(koerper)
		add_child(halter)
		var teile: Dictionary = {"koerper": koerper.find_child("koerper", true, false) as Node3D,
			"kopf": koerper.find_child("kopf", true, false) as Node3D,
			"arm_l": koerper.find_child("arm_l", true, false) as Node3D,
			"arm_r": koerper.find_child("arm_r", true, false) as Node3D,
			"bein_l": koerper.find_child("bein_l", true, false) as Node3D,
			"bein_r": koerper.find_child("bein_r", true, false) as Node3D}
		var basis: Dictionary = {}
		for k in teile:
			if teile[k] != null:
				basis[k] = (teile[k] as Node3D).rotation
		return {"halter": halter, "modell": koerper, "teile": teile, "basis": basis, "rang": 0,
			"basis_pos": halter.position, "skala": 1.0, "frei_ab": 0.0,
			"arbeit": LebendigDaten.crew_arbeit(s, _regeln), "phase": float(nr) * 1.9,
			"extras": [], "schild": null}

	## Rang setzen: Groesse, Zubehoer, Schild; bei `auftritt` mit Plopp und Staub.
	func _setze_rang(e: Dictionary, eintrag: Dictionary, rang: int, auftritt: bool) -> void:
		var look: Dictionary = LebendigDaten.crew_rang_look(rang, _regeln)
		if look.is_empty():
			return
		e["rang"] = rang
		var halter: Node3D = e["halter"] as Node3D
		e["skala"] = float(look["skala"])
		for alt in (e["extras"] as Array):
			if alt != null and is_instance_valid(alt):
				(alt as Node).queue_free()
		e["extras"] = _baue_zubehoer(e, look)
		if e["schild"] != null and is_instance_valid(e["schild"]):
			(e["schild"] as Node).queue_free()
		var schild_werte: Dictionary = _crew_regeln().get("schild", {}) as Dictionary
		var akzent: Color = UiStil.GOLD_TEXT if rang >= 3 else UiStil.TINTE_2
		var schild: Node3D = StationView.baue_namensschild(String(eintrag.get("name", "")),
			LebendigDaten.crew_titel(eintrag, rang), akzent, schild_werte)
		schild.position = Vector3(0.0, float(schild_werte.get("hoehe", 1.5)), 0.0)
		halter.add_child(schild)
		e["schild"] = schild
		if auftritt and is_inside_tree():
			_auftritt(e)
		else:
			halter.scale = Vector3.ONE * float(e["skala"])

	func _auftritt(e: Dictionary) -> void:
		var a: Dictionary = _crew_regeln().get("auftritt", {}) as Dictionary
		var halter: Node3D = e["halter"] as Node3D
		var dauer: float = float(a.get("dauer", 0.5))
		var hoehe: float = float(a.get("hoepfer", 0.2))
		e["frei_ab"] = _zeit + dauer
		halter.scale = Vector3.ONE * 0.05
		var t: Tween = halter.create_tween()
		t.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		t.tween_property(halter, "scale", Vector3.ONE * float(e["skala"]), dauer)
		var y0: float = (e["basis_pos"] as Vector3).y
		var h: Tween = halter.create_tween()
		h.tween_property(halter, "position:y", y0 + hoehe, dauer * 0.35).set_ease(Tween.EASE_OUT)
		h.tween_property(halter, "position:y", y0, dauer * 0.65).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
		_staub(halter.position, a)

	## Staubwolke am Boden: ein Schwung runder Partikel, einmal, danach weg.
	func _staub(ort: Vector3, a: Dictionary) -> void:
		var p := GPUParticles3D.new()
		p.amount = int(a.get("staub_menge", 12))
		p.lifetime = float(a.get("staub_dauer", 0.8))
		p.one_shot = true
		p.explosiveness = 1.0
		p.local_coords = false
		p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		p.visibility_aabb = AABB(Vector3(-3, -1, -3), Vector3(6, 4, 6))
		var groesse: float = float(a.get("staub_groesse", 0.2))
		var quad := QuadMesh.new()
		quad.size = Vector2(groesse, groesse)
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		m.vertex_color_use_as_albedo = true
		m.albedo_texture = _punkt()
		quad.material = m
		p.draw_pass_1 = quad
		var pm := ParticleProcessMaterial.new()
		pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		pm.emission_sphere_radius = 0.25
		pm.direction = Vector3(0, 0.6, 0)
		pm.spread = 80.0
		pm.initial_velocity_min = 0.6
		pm.initial_velocity_max = 1.4
		pm.gravity = Vector3(0, -1.2, 0)
		pm.damping_min = 1.5
		pm.damping_max = 2.5
		var farbe: Color = LebendigDaten.farbe(a.get("staub_farbe", null), Color.WHITE)
		var klar: Color = farbe
		klar.a = 0.0
		var verlauf := Gradient.new()
		verlauf.offsets = PackedFloat32Array([0.0, 0.15, 1.0])
		verlauf.colors = PackedColorArray([klar, farbe, klar])
		var vt := GradientTexture1D.new()
		vt.gradient = verlauf
		pm.color_ramp = vt
		pm.scale_min = 0.7
		pm.scale_max = 1.5
		p.process_material = pm
		p.position = ort + Vector3(0, 0.15, 0)
		add_child(p)
		p.emitting = true
		get_tree().create_timer(p.lifetime + 0.5).timeout.connect(p.queue_free)

	func _punkt() -> Texture2D:
		if _punkt_textur != null:
			return _punkt_textur
		var n: int = 16
		var bild := Image.create(n, n, false, Image.FORMAT_RGBA8)
		var mitte: float = (n - 1) * 0.5
		for y in n:
			for x in n:
				var dist: float = Vector2(x - mitte, y - mitte).length() / (n * 0.5)
				bild.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - pow(dist, 1.6), 0.0, 1.0)))
		_punkt_textur = ImageTexture.create_from_image(bild)
		return _punkt_textur

	static func _material(farbe: Color, leuchten: float = 0.0, alpha: float = 1.0) -> StandardMaterial3D:
		var m := StandardMaterial3D.new()
		m.albedo_color = Color(farbe.r, farbe.g, farbe.b, alpha)
		m.roughness = 0.55
		if leuchten > 0.0:
			m.emission_enabled = true
			m.emission = farbe
			m.emission_energy_multiplier = leuchten
		if alpha < 1.0:
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		return m

	static func _teil(eltern: Node3D, mesh: Mesh, mat: Material, ort: Vector3, drehung: Vector3 = Vector3.ZERO) -> MeshInstance3D:
		var m := MeshInstance3D.new()
		m.mesh = mesh
		m.material_override = mat
		m.position = ort
		m.rotation_degrees = drehung
		m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		eltern.add_child(m)
		return m

	## Kopfhoerer (Rang 2+), Brosche und Bodenring (Rang 3): einfache Formen aus Daten-Farben.
	## Gibt alle erzeugten Knoten zurueck, damit ein Rangwechsel sie wieder entfernen kann.
	func _baue_zubehoer(e: Dictionary, look: Dictionary) -> Array:
		var neu: Array = []
		var farben: Dictionary = _crew_regeln().get("farben", {}) as Dictionary
		var teile: Dictionary = e["teile"] as Dictionary
		var kopf: Node3D = teile.get("kopf", null) as Node3D
		if bool(look["kopfhoerer"]) and kopf != null:
			var band_farbe: Color = LebendigDaten.farbe(farben.get("kopfhoerer", null), Color.DIM_GRAY)
			var polster: Color = LebendigDaten.farbe(farben.get("polster", null), Color.GOLD)
			var band := TorusMesh.new()
			band.inner_radius = 0.335
			band.outer_radius = 0.385
			band.rings = 24
			band.ring_segments = 8
			neu.append(_teil(kopf, band, _material(band_farbe), Vector3(0.0, 0.3, 0.0), Vector3(90, 0, 0)))
			for seite in [-1.0, 1.0]:
				var cup := CylinderMesh.new()
				cup.top_radius = 0.12
				cup.bottom_radius = 0.12
				cup.height = 0.09
				neu.append(_teil(kopf, cup, _material(polster), Vector3(0.36 * float(seite), 0.3, 0.0), Vector3(0, 0, 90)))
		var koerper: Node3D = teile.get("koerper", null) as Node3D
		if bool(look["brosche"]) and koerper != null:
			var gold: Color = LebendigDaten.farbe(farben.get("brosche", null), Color.GOLD)
			var stern := CylinderMesh.new()
			stern.top_radius = 0.07
			stern.bottom_radius = 0.07
			stern.height = 0.03
			stern.radial_segments = 5
			stern.rings = 1
			for z in [-1.0, 1.0]:
				neu.append(_teil(koerper, stern, _material(gold, 0.6), Vector3(0.09, 0.2, 0.17 * float(z)), Vector3(90, 0, 0)))
		if bool(look["ring"]):
			var halter: Node3D = e["halter"] as Node3D
			var ring_farbe: Color = LebendigDaten.farbe(farben.get("ring", null), Color.GOLD)
			var scheibe := CylinderMesh.new()
			scheibe.top_radius = 0.62
			scheibe.bottom_radius = 0.62
			scheibe.height = 0.012
			scheibe.rings = 1
			neu.append(_teil(halter, scheibe, _material(ring_farbe, 0.0, float(farben.get("ring_alpha", 0.5))), Vector3(0.0, 0.03, 0.0)))
			var kante := TorusMesh.new()
			kante.inner_radius = 0.6
			kante.outer_radius = 0.66
			kante.rings = 32
			kante.ring_segments = 4
			neu.append(_teil(halter, kante, _material(ring_farbe.lightened(0.2), 0.8), Vector3(0.0, 0.035, 0.0)))
		return neu

	## Arbeit: tippen (Arme), nicken (Kopf), wippen (Koerper), hin_und_her (laeuft ein Stueck).
	func _arbeite(e: Dictionary) -> void:
		var t: Dictionary = _crew_regeln().get("tempo", {}) as Dictionary
		var teile: Dictionary = e["teile"] as Dictionary
		var basis: Dictionary = e["basis"] as Dictionary
		var zeit: float = _zeit + float(e["phase"])
		var arm_l: Node3D = teile.get("arm_l", null) as Node3D
		var arm_r: Node3D = teile.get("arm_r", null) as Node3D
		var kopf: Node3D = teile.get("kopf", null) as Node3D
		var koerper: Node3D = teile.get("koerper", null) as Node3D
		match String(e["arbeit"]):
			"tippen":
				var w: float = zeit * float(t.get("tippen_hz", 3.0)) * TAU
				if arm_l != null:
					arm_l.rotation.x = (basis["arm_l"] as Vector3).x - 0.5 + sin(w) * 0.28
				if arm_r != null:
					arm_r.rotation.x = (basis["arm_r"] as Vector3).x - 0.5 + sin(w + PI) * 0.28
				if kopf != null:
					kopf.rotation.x = (basis["kopf"] as Vector3).x + sin(zeit * 0.9) * 0.06
			"nicken":
				var n: float = sin(zeit * float(t.get("nicken_hz", 0.9)) * TAU)
				if kopf != null:
					kopf.rotation.x = (basis["kopf"] as Vector3).x + maxf(n, -0.3) * float(t.get("nicken_winkel", 0.2))
				if arm_r != null:
					arm_r.rotation.x = (basis["arm_r"] as Vector3).x - 0.35 + sin(zeit * 2.1) * 0.12
			"hin_und_her":
				_gehe(e, t, zeit)
			_:
				var s: float = sin(zeit * float(t.get("wippen_hz", 1.3)) * TAU)
				if koerper != null:
					koerper.rotation.z = (basis["koerper"] as Vector3).z + s * float(t.get("wippen_winkel", 0.06))
				if arm_l != null:
					arm_l.rotation.x = (basis["arm_l"] as Vector3).x + s * 0.12
				if arm_r != null:
					arm_r.rotation.x = (basis["arm_r"] as Vector3).x - s * 0.12

	func _gehe(e: Dictionary, t: Dictionary, zeit: float) -> void:
		var teile: Dictionary = e["teile"] as Dictionary
		var basis: Dictionary = e["basis"] as Dictionary
		var weite: float = float(t.get("gehen_weite", 0.5))
		var w: float = zeit * float(t.get("gehen_tempo", 0.5)) * PI
		var halter: Node3D = e["halter"] as Node3D
		var modell: Node3D = e["modell"] as Node3D
		# Laeuft ein Stueck entlang der X-Achse und dreht sich in Laufrichtung.
		if _zeit >= float(e["frei_ab"]):
			halter.position.x = (e["basis_pos"] as Vector3).x + sin(w) * weite
			modell.rotation.y = lerp_angle(modell.rotation.y, PI * 0.5 if cos(w) >= 0.0 else -PI * 0.5, 0.12)
		var schwung: float = sin(zeit * 7.0) * float(t.get("gehen_schwung", 0.5))
		for paar in [["bein_l", 1.0], ["bein_r", -1.0], ["arm_l", -0.8], ["arm_r", 0.8]]:
			var teil: Node3D = teile.get(paar[0], null) as Node3D
			if teil != null:
				teil.rotation.x = (basis[paar[0]] as Vector3).x + schwung * float(paar[1])


## Kunden-Figuren (K6 2a): Alle paar Sekunden kommt eine Figur vom Start zum Eingang der
## Kette, bleibt kurz und geht zurueck. Der Abstand haengt am Durchsatz der Kette (nur
## gelesen). Reine Darstellung: Die Figuren erzeugen kein Geld (ADR-007), und sie sind
## kein Teil der Warteschlange (NpcPool) -- nur Leben im Raum.
class KundenLauf extends Node3D:
	const TAKT_S: float = 0.25
	const SUCHE_S: float = 1.0

	var _regeln: Dictionary = {}
	var _hud: Hud
	var _weg: Dictionary = {}
	var _zeit: float = 0.0
	var _rest: float = 0.0
	var _suche_rest: float = 0.0
	var _naechster: float = 2.0
	var _zaehler: int = 0
	var _pool: Array[Dictionary] = []

	func _init(regeln: Dictionary = {}) -> void:
		_regeln = regeln
		name = "KundenLauf"
		if OS.is_debug_build() and OS.get_cmdline_user_args().has("--crew-probe"):
			_naechster = 0.2   # Vorschau: der erste Kunde kommt sofort

	func _process(delta: float) -> void:
		var d: float = minf(delta, 0.1)
		_zeit += d
		_rest -= d
		if _rest <= 0.0:
			_rest = TAKT_S
			_suche_rest -= TAKT_S
			if _hud == null or not is_instance_valid(_hud):
				if _suche_rest <= 0.0:
					_suche_rest = SUCHE_S
					_hud = AufgabenHinweis._finde_hud(get_tree().root) if is_inside_tree() else null
					if _hud != null and _hud.kern != null:
						_weg = LebendigDaten.kunden_weg(_hud.kern.welten.welt(_hud.kern.welt_index))
			if _hud != null and _hud.kern != null and not _weg.is_empty():
				_plane(TAKT_S)
		for k in _pool:
			_laufe(k, d)

	func ist_aktiv() -> bool:
		return not _weg.is_empty()

	func sichtbare() -> int:
		var n: int = 0
		for k in _pool:
			if int(k["zustand"]) != 0:
				n += 1
		return n

	## Die Wartezeit bis zum naechsten Kunden aus dem Durchsatz; ein Kunde kommt, wenn sie
	## abgelaufen ist und noch Platz im Pool ist.
	func _plane(dt: float) -> void:
		var kern: GameCore = _hud.kern
		var intervall: float = LebendigDaten.kunden_intervall(kern.kette.effektiver_durchsatz(), _regeln)
		if intervall <= 0.0:
			return
		_naechster -= dt
		if _naechster > 0.0:
			return
		_naechster = intervall * randf_range(0.8, 1.25)
		var k: Dictionary = _freier()
		if not k.is_empty():
			_starte(k)

	func _freier() -> Dictionary:
		var kd: Dictionary = _regeln.get("kunden", {}) as Dictionary
		var grenze: int = int(kd.get("max_gleichzeitig", 3))
		var modelle: Array = kd.get("modelle", []) as Array
		if modelle.is_empty():
			return {}
		for k in _pool:
			if int(k["zustand"]) == 0:
				return k
		if _pool.size() >= grenze:
			return {}
		var pfad: String = Lebendig.figur_pfad(_hud.kern.welt_id(), String(modelle[_zaehler % modelle.size()]))
		_zaehler += 1
		if pfad.is_empty():
			return {}
		var figur: Node3D = (load(pfad) as PackedScene).instantiate() as Node3D
		figur.visible = false
		figur.scale = Vector3.ONE * float(kd.get("skala", 1.0))
		add_child(figur)
		var k: Dictionary = {"figur": figur, "zustand": 0, "weg": 0.0, "rest": 0.0,
			"arm_l": figur.find_child("arm_l", true, false), "arm_r": figur.find_child("arm_r", true, false),
			"bein_l": figur.find_child("bein_l", true, false), "bein_r": figur.find_child("bein_r", true, false)}
		_pool.append(k)
		return k

	func _starte(k: Dictionary) -> void:
		var figur: Node3D = k["figur"] as Node3D
		figur.position = _weg["start"] as Vector3
		figur.visible = true
		k["zustand"] = 1
		k["seg"] = 0
		k["weg"] = 0.0

	## Zustand 1: hin, 2: wartet am Eingang, 3: zurueck, 0: weg. Der Weg ist die Punktfolge
	## start, via..., ziel; zurueck laeuft sie rueckwaerts.
	func _laufe(k: Dictionary, d: float) -> void:
		var z: int = int(k["zustand"])
		if z == 0:
			return
		var kd: Dictionary = _regeln.get("kunden", {}) as Dictionary
		var figur: Node3D = k["figur"] as Node3D
		if z == 2:
			k["rest"] = float(k["rest"]) - d
			_schwung(k, 0.0)
			if float(k["rest"]) <= 0.0:
				k["zustand"] = 3
				k["seg"] = 0
				k["weg"] = 0.0
			return
		var route: PackedVector3Array = _weg["route"] as PackedVector3Array
		var n: int = route.size()
		var seg: int = int(k["seg"])
		var von: Vector3 = route[seg] if z == 1 else route[n - 1 - seg]
		var nach: Vector3 = route[seg + 1] if z == 1 else route[n - 2 - seg]
		var laenge: float = maxf(0.01, von.distance_to(nach))
		k["weg"] = float(k["weg"]) + float(kd.get("tempo", 1.5)) * d
		var t: float = minf(1.0, float(k["weg"]) / laenge)
		figur.position = von.lerp(nach, t)
		var richtung: Vector3 = nach - von
		figur.rotation.y = lerp_angle(figur.rotation.y, atan2(richtung.x, richtung.z), minf(1.0, d * 8.0))
		_schwung(k, 1.0)
		if t < 1.0:
			return
		k["weg"] = 0.0
		k["seg"] = seg + 1
		if seg + 1 < n - 1:
			return
		if z == 1:
			k["zustand"] = 2
			k["rest"] = float(kd.get("warten", 1.5))
		else:
			k["zustand"] = 0
			figur.visible = false

	func _schwung(k: Dictionary, staerke: float) -> void:
		var kd: Dictionary = _regeln.get("kunden", {}) as Dictionary
		var s: float = sin(_zeit * float(kd.get("gehen_hz", 2.6)) * TAU) * float(kd.get("gehen_schwung", 0.5)) * staerke
		for paar in [["bein_l", 1.0], ["bein_r", -1.0], ["arm_l", -1.0], ["arm_r", 1.0]]:
			var teil: Node3D = k.get(paar[0], null) as Node3D
			if teil != null:
				teil.rotation.x = s * float(paar[1])


func _init() -> void:
	_regeln = LebendigDaten.laden_regeln()
	set_process(false)


## Der Aufgaben-Hinweis ("!" ueber einer Figur, K3 B3) haengt sich selbst ein:
## Er sucht das HUD im Baum und tut nichts, solange die Welt keine Aufgaben hat.
func _ready() -> void:
	if _aufgabe == null:
		_aufgabe = AufgabenHinweis.new()
		_aufgabe.name = "AufgabenHinweis"
		add_child(_aufgabe)
	# Mitarbeiter und Kunden (K6 2a): beide suchen sich das HUD selbst und tun nichts ohne Daten.
	add_child(CrewFiguren.new(_regeln))
	add_child(KundenLauf.new(_regeln))


## Nur Debug-Builds: user://e_lebendig_test.json legt Daten ueber eine Welt,
## ohne worlds.json anzufassen (Vorschauen und Tests). Form:
## {"<welt_id>": {"licht": {...}, "kulisse": {"<datei>": {"animation": ..., "emission_puls": ...}}}}
const TEST_PFAD: String = "user://e_lebendig_test.json"

func _test_daten(welt_id: String) -> Dictionary:
	if not OS.is_debug_build() or not FileAccess.file_exists(TEST_PFAD):
		return {}
	var roh: Variant = JSON.parse_string(FileAccess.get_file_as_string(TEST_PFAD))
	if roh is Dictionary and (roh as Dictionary).get(welt_id) is Dictionary:
		return (roh as Dictionary)[welt_id] as Dictionary
	return {}


func mit_test_licht(welt_id: String, licht: Dictionary) -> Dictionary:
	var z: Dictionary = _test_daten(welt_id).get("licht", {}) as Dictionary
	if z.is_empty():
		return licht
	var kopie: Dictionary = licht.duplicate(true)
	kopie.merge(z, true)
	return kopie


func mit_test_kulisse(welt_id: String, eintraege: Array) -> Array:
	var z: Dictionary = _test_daten(welt_id).get("kulisse", {}) as Dictionary
	if z.is_empty():
		return eintraege
	var kopie: Array = eintraege.duplicate(true)
	for e in kopie:
		if e is Dictionary and z.get(String((e as Dictionary).get("datei", "")), null) is Dictionary:
			(e as Dictionary).merge(z[String((e as Dictionary).get("datei", ""))] as Dictionary, true)
	return kopie


# --- Umgebung: Himmel und Glow ----------------------------------------------

## Setzt Himmel und Glow in die Umgebung. Aufruf aus _baue_licht, mit dem
## aufgeloesten Licht der Welt. Ohne die Schluessel bleibt `env` unveraendert.
func baue_umgebung(env: Environment, licht: Dictionary) -> void:
	var himmel: Dictionary = LebendigDaten.himmel(licht, _regeln)
	if not himmel.is_empty():
		_baue_himmel(env, himmel)
	var glow: Dictionary = LebendigDaten.glow(licht, _regeln)
	if not glow.is_empty():
		env.glow_enabled = true
		env.glow_intensity = float(glow["intensitaet"])
		env.glow_strength = float(glow["staerke"])
		env.glow_hdr_threshold = float(glow["schwelle"])
		env.glow_bloom = float(glow["bloom"])
		env.glow_hdr_luminance_cap = float(glow["hdr_deckel"])


func _baue_himmel(env: Environment, himmel: Dictionary) -> void:
	# Die Kamera ist orthogonal: ein Himmel aus Blickrichtungen (ProceduralSky)
	# waere dort eine einzige Farbe. Der Verlauf liegt deshalb als Bild hinter der Welt.
	env.background_mode = Environment.BG_CANVAS
	_himmel_ebene = CanvasLayer.new()
	_himmel_ebene.layer = int((_regeln.get("himmel", {}) as Dictionary).get("ebene", -10))
	var vorn: bool = bool(himmel.get("vorn", false))
	var z: HimmelZeichner = _neuer_zeichner(himmel, true, not vorn)
	_himmel_ebene.add_child(z)
	if vorn:
		# Sterne und Mond ueber der Karte (Ebene 0, unter der Oberflaeche), Verlauf dahinter.
		var vorne := CanvasLayer.new()
		vorne.layer = 0
		vorne.add_child(_neuer_zeichner(himmel, false, true))
		add_child(vorne)
	add_child(_himmel_ebene)


func _neuer_zeichner(himmel: Dictionary, verlauf: bool, deko: bool) -> HimmelZeichner:
	var z := HimmelZeichner.new()
	z.mit_verlauf = verlauf
	z.mit_deko = deko
	z.oben = himmel["oben"] as Color
	z.unten = himmel["unten"] as Color
	z.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var s: Dictionary = himmel["sterne"] as Dictionary
	if not s.is_empty():
		var rng := RandomNumberGenerator.new()
		rng.seed = int(s["seed"])
		for i in int(s["anzahl"]):
			z.sterne.append(Vector2(rng.randf(), rng.randf() * float(s["bis_hoehe"])))
			z.sterne_alpha.append(rng.randf_range(float(s["alpha_min"]), float(s["alpha_max"])))
		z.stern_groesse = float(s["groesse"])
		z.stern_farbe = s["farbe"] as Color
	z.mond = himmel["mond"] as Dictionary
	return z


# --- Kulisse ----------------------------------------------------------------

## `eintraege` = die rohen Kulissen-Eintraege aus worlds.json, `knoten` = die
## dazu gebauten Knoten (gleiche Reihenfolge, null wo nichts gebaut wurde).
func baue_kulisse(eintraege: Array, knoten: Array) -> void:
	var max_anim: int = LebendigDaten.grenze(_regeln, "max_animiert")
	var max_puls: int = LebendigDaten.grenze(_regeln, "max_puls")
	var max_mat: int = LebendigDaten.grenze(_regeln, "max_materialien_je_knoten")
	for i in mini(eintraege.size(), knoten.size()):
		if not (eintraege[i] is Dictionary) or not (knoten[i] is Node3D):
			continue
		var eintrag: Dictionary = eintraege[i] as Dictionary
		var k: Node3D = knoten[i] as Node3D
		var anim: Dictionary = LebendigDaten.animation(eintrag, _regeln)
		if not anim.is_empty() and _a_knoten.size() + _f_knoten.size() < max_anim:
			_baue_animation(k, anim, max_anim, max_mat, eintrag)
		var puls: Dictionary = LebendigDaten.emission_puls(eintrag, _regeln)
		if not puls.is_empty() and _p_mat.size() < max_puls:
			_baue_puls(k, puls, max_puls, max_mat, i)
	_aktualisiere_process()


func _baue_animation(k: Node3D, anim: Dictionary, max_anim: int, max_mat: int, eintrag: Dictionary) -> void:
	var typ: String = String(anim["typ"])
	if typ == "fahren":
		_baue_fahrzeug(k, anim)
		return
	var teil: String = String(anim["teil"])
	var ziele: Array[Node3D] = []
	if typ == "foerdern":
		_baue_foerderer(k, anim, max_mat)
		return
	if teil.is_empty():
		ziele.append(k)
	else:
		_sammle_knoten(k, teil.to_lower(), ziele)
	var nr: int = 0
	for ziel in ziele:
		if _a_knoten.size() + _f_knoten.size() >= max_anim:
			break
		var t: int = Typ.DREHEN
		match typ:
			"treiben": t = Typ.TREIBEN
			"wackeln": t = Typ.WACKELN
		_a_knoten.append(ziel)
		_a_typ.append(t)
		_a_achse.append(anim["achse"] as Vector3)
		_a_tempo.append(float(anim["tempo"]))
		_a_weite.append(float(anim["weite"]))
		_a_winkel.append(float(anim["winkel"]))
		# Versetzte Anfangsphase, damit Nachbarn nicht im Gleichschritt laufen.
		_a_phase.append(float(anim["phase"]) + float(nr) * 0.9 + float(eintrag.get("x", 0.0)) * 0.13)
		_a_basis.append(ziel.position)
		_a_rot0.append(ziel.rotation)
		_a_mat.append(null)
		_a_uv.append(Vector3.ZERO)
		nr += 1


func _baue_foerderer(k: Node3D, anim: Dictionary, max_mat: int) -> void:
	var meshes: Array[MeshInstance3D] = []
	_sammle_meshes(k, String(anim["teil"]).to_lower(), meshes)
	var max_anim: int = LebendigDaten.grenze(_regeln, "max_animiert")
	var n: int = 0
	for m in meshes:
		for s in m.get_surface_override_material_count():
			if n >= max_mat or _a_knoten.size() + _f_knoten.size() >= max_anim:
				return
			var mat: StandardMaterial3D = _eigenes_material(m, s)
			if mat == null:
				continue
			_a_knoten.append(m)
			_a_typ.append(Typ.FOERDERN)
			_a_achse.append(anim["achse"] as Vector3)
			_a_tempo.append(float(anim["tempo"]))
			_a_weite.append(1.0)
			_a_winkel.append(0.0)
			_a_phase.append(0.0)
			_a_basis.append(Vector3.ZERO)
			_a_rot0.append(Vector3.ZERO)
			_a_mat.append(mat)
			_a_uv.append(mat.uv1_offset)
			n += 1


func _baue_fahrzeug(k: Node3D, anim: Dictionary) -> void:
	var r: PackedVector3Array = anim["route"] as PackedVector3Array
	_f_knoten.append(k)
	_f_route.append(r)
	_f_warten.append(anim["warten"] as PackedFloat32Array)
	var modus: int = 0
	match String(anim["modus"]):
		"hin_und_her": modus = 1
		"einmal": modus = 2
	_f_modus.append(modus)
	_f_tempo.append(float(anim["tempo"]))
	_f_pause.append(float(anim["pause"]))
	_f_versatz.append(deg_to_rad(float(anim["blick_versatz"])))
	_f_basis_y.append(k.position.y)
	_f_seg.append(0)
	_f_dir.append(1)
	_f_weg.append(0.0)
	# Wartezeit am ersten Punkt gilt auch zum Start: das Fahrzeug steht erst da, bevor es losfaehrt.
	var w0: PackedFloat32Array = anim["warten"] as PackedFloat32Array
	_f_rest_warten.append(w0[0] if w0.size() > 0 else 0.0)
	_f_rest_pause.append(0.0)
	k.position = Vector3(r[0].x, k.position.y + r[0].y, r[0].z)


func _baue_puls(k: Node3D, puls: Dictionary, max_puls: int, max_mat: int, index: int) -> void:
	var meshes: Array[MeshInstance3D] = []
	_sammle_meshes(k, String(puls["teil"]).to_lower(), meshes)
	var form: int = 0
	match String(puls["form"]):
		"blinken": form = 1
		"flackern": form = 2
	var n: int = 0
	for m in meshes:
		for s in m.get_surface_override_material_count():
			if n >= max_mat or _p_mat.size() >= max_puls:
				return
			var mat: StandardMaterial3D = _eigenes_material(m, s)
			if mat == null:
				continue
			if bool(puls["mit_farbe"]):
				mat.emission_enabled = true
				mat.emission = puls["farbe"] as Color
			elif not mat.emission_enabled:
				# Mehrere Flaechen ohne eigenes Leuchten (ganze Umgebungen): nur die
				# leuchtenden pulsen, sonst glimmt die ganze Welt mit.
				if m.get_surface_override_material_count() > 1:
					continue
				# Einflaechige Modelle ohne Leuchten: dann leuchtet die Eigenfarbe.
				mat.emission_enabled = true
				mat.emission = mat.albedo_color
			_p_mat.append(mat)
			_p_hz.append(float(puls["hz"]))
			_p_min.append(float(puls["min"]))
			_p_max.append(float(puls["max"]))
			_p_form.append(form)
			_p_phase.append(float(puls["versatz"]) * float(_p_mat.size() + index))
			n += 1


## Ein eigenes StandardMaterial3D fuer genau diese Flaeche (das Modell teilt
## seine Materialien mit allen Instanzen). Andere Materialarten werden ignoriert.
func _eigenes_material(m: MeshInstance3D, flaeche: int) -> StandardMaterial3D:
	var vorhanden: Material = m.get_active_material(flaeche)
	if not (vorhanden is StandardMaterial3D):
		return null
	var mat: StandardMaterial3D = (vorhanden as StandardMaterial3D).duplicate() as StandardMaterial3D
	m.set_surface_override_material(flaeche, mat)
	return mat


func _sammle_meshes(knoten: Node, teil: String, ausgabe: Array[MeshInstance3D]) -> void:
	if knoten is MeshInstance3D and (teil.is_empty() or String(knoten.name).to_lower().begins_with(teil)):
		ausgabe.append(knoten as MeshInstance3D)
	for kind in knoten.get_children():
		_sammle_meshes(kind, teil, ausgabe)


func _sammle_knoten(knoten: Node, teil: String, ausgabe: Array[Node3D]) -> void:
	for kind in knoten.get_children():
		if kind is Node3D:
			# begins_with, nicht contains: "luefter" trifft sonst auch den Rahmen
			# "welt_luefter_rahmen" und dreht die ganze Wand mit.
			if String(kind.name).to_lower().begins_with(teil):
				ausgabe.append(kind as Node3D)
			else:
				_sammle_knoten(kind, teil, ausgabe)


# --- Partikel ---------------------------------------------------------------

## Baut die Partikel-Systeme der Welt. `quellen` = [licht.partikel, ...].
func baue_partikel(quellen: Array) -> void:
	var liste: Array[Dictionary] = LebendigDaten.partikel(quellen, _regeln)
	for e in liste:
		_baue_system(e)
	_aktualisiere_process()


func _baue_system(e: Dictionary) -> void:
	var t: Dictionary = e["werte"] as Dictionary
	var typ: String = String(e["typ"])
	var p := GPUParticles3D.new()
	p.amount = int(e["menge"])
	p.lifetime = maxf(0.2, LebendigDaten.zahl(t.get("lebensdauer", null), 2.0))
	p.local_coords = false
	p.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var weite: float = LebendigDaten.zahl((_regeln.get("partikel_fenster", {}) as Dictionary).get("sichtbar_ausdehnung", null), 30.0)
	p.visibility_aabb = AABB(Vector3(-weite, -weite, -weite), Vector3(weite, weite, weite) * 2.0)
	p.position = Vector3(float(e["x"]), float(e["y"]), float(e["z"]))

	var groesse: float = maxf(0.01, LebendigDaten.zahl(t.get("groesse", null), 0.1))
	var ende: float = maxf(groesse, LebendigDaten.zahl(t.get("groesse_ende", null), groesse))
	var quad := QuadMesh.new()
	quad.size = Vector2(ende, ende)
	quad.material = _partikel_material(typ, String(t.get("blenden", "mix")))
	p.draw_pass_1 = quad

	var pm := ParticleProcessMaterial.new()
	pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	var radius: float = float(e["radius"])
	pm.emission_box_extents = Vector3(radius, LebendigDaten.zahl(t.get("vol_y", null), 0.0), radius)
	var richtung: Vector3 = Vector3.UP
	var rr: Variant = t.get("richtung", null)
	if rr is Array and (rr as Array).size() >= 3:
		richtung = Vector3(LebendigDaten.zahl((rr as Array)[0], 0.0), LebendigDaten.zahl((rr as Array)[1], 1.0), LebendigDaten.zahl((rr as Array)[2], 0.0))
	pm.direction = richtung if richtung.length_squared() > 0.0001 else Vector3.UP
	pm.spread = clampf(LebendigDaten.zahl(t.get("streuung", null), 45.0), 0.0, 180.0)
	pm.initial_velocity_min = LebendigDaten.zahl(t.get("tempo_min", null), 0.1)
	pm.initial_velocity_max = maxf(pm.initial_velocity_min, LebendigDaten.zahl(t.get("tempo_max", null), 0.3))
	pm.gravity = Vector3(0.0, -LebendigDaten.zahl(t.get("schwerkraft", null), 0.0), 0.0)
	pm.scale_min = groesse / ende
	pm.scale_max = groesse / ende
	if ende > groesse:
		var kurve := Curve.new()
		kurve.add_point(Vector2(0.0, groesse / ende))
		kurve.add_point(Vector2(1.0, 1.0))
		var ct := CurveTexture.new()
		ct.curve = kurve
		pm.scale_curve = ct
		pm.scale_min = 1.0
		pm.scale_max = 1.0
	var farbe: Color = e["farbe"] as Color
	farbe.a = clampf(LebendigDaten.zahl(t.get("alpha", null), 1.0), 0.0, 1.0)
	var verlauf := Gradient.new()
	var klar: Color = farbe
	klar.a = 0.0
	verlauf.offsets = PackedFloat32Array([0.0, 0.18, 0.75, 1.0])
	verlauf.colors = PackedColorArray([klar, farbe, farbe, klar])
	var vt := GradientTexture1D.new()
	vt.gradient = verlauf
	pm.color_ramp = vt
	p.process_material = pm

	var intervall: float = float(e["intervall"])
	if intervall > 0.0:
		p.one_shot = true
		p.explosiveness = 1.0
		p.emitting = false
		_w_knoten.append(p)
		_w_intervall.append(intervall)
		_w_rest.append(intervall * 0.25)
	else:
		p.preprocess = p.lifetime
		p.emitting = true
	add_child(p)


func _partikel_material(typ: String, blenden: String) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if blenden == "add" else BaseMaterial3D.BLEND_MODE_MIX
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	m.vertex_color_use_as_albedo = true
	m.disable_receive_shadows = true
	m.albedo_texture = _fluegel_tex() if typ == "voegel" else _punkt_tex()
	return m


func _punkt_tex() -> Texture2D:
	if _punkt_textur != null:
		return _punkt_textur
	var d: Dictionary = _regeln.get("partikel_textur", {}) as Dictionary
	var n: int = clampi(int(LebendigDaten.zahl(d.get("groesse", null), 16.0)), 4, 32)
	var haerte: float = LebendigDaten.zahl(d.get("haerte", null), 1.5)
	var bild := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var mitte: float = (n - 1) * 0.5
	for y in n:
		for x in n:
			var dist: float = Vector2(x - mitte, y - mitte).length() / (n * 0.5)
			bild.set_pixel(x, y, Color(1, 1, 1, clampf(1.0 - pow(dist, haerte), 0.0, 1.0)))
	_punkt_textur = ImageTexture.create_from_image(bild)
	return _punkt_textur


## Ein flaches „V" als Vogelsilhouette.
func _fluegel_tex() -> Texture2D:
	if _fluegel_textur != null:
		return _fluegel_textur
	var n: int = 16
	var bild := Image.create(n, n, false, Image.FORMAT_RGBA8)
	bild.fill(Color(1, 1, 1, 0))
	for x in n:
		var hoehe: int = int(absf(x - (n - 1) * 0.5) * 0.7) + 3
		bild.set_pixel(x, clampi(hoehe, 0, n - 1), Color.WHITE)
		bild.set_pixel(x, clampi(hoehe + 1, 0, n - 1), Color.WHITE)
	_fluegel_textur = ImageTexture.create_from_image(bild)
	return _fluegel_textur


# --- Lauf -------------------------------------------------------------------

func _aktualisiere_process() -> void:
	set_process(not _a_knoten.is_empty() or not _f_knoten.is_empty()
		or not _p_mat.is_empty() or not _w_knoten.is_empty())


## Wie viele Dinge gerade bewegt werden -- fuer Tests und die Leistungspruefung.
func zaehler() -> Dictionary:
	return {"animiert": _a_knoten.size(), "fahrzeuge": _f_knoten.size(),
		"puls": _p_mat.size(), "partikel": _zaehle_partikel()}


func _zaehle_partikel() -> int:
	var n: int = 0
	for k in get_children():
		if k is GPUParticles3D:
			n += 1
	return n


func _process(delta: float) -> void:
	var d: float = minf(delta, 0.1)
	_zeit += d
	for i in _a_knoten.size():
		var k: Node3D = _a_knoten[i]
		_a_phase[i] += d * _a_tempo[i] / _a_weite[i] if _a_typ[i] == Typ.TREIBEN else d * _a_tempo[i]
		match _a_typ[i]:
			Typ.DREHEN:
				k.rotate_object_local(_a_achse[i], deg_to_rad(_a_tempo[i]) * d)
			Typ.TREIBEN:
				k.position = _a_basis[i] + _a_achse[i] * (sin(_a_phase[i]) * _a_weite[i])
			Typ.WACKELN:
				var w: float = deg_to_rad(sin(_a_phase[i] * TAU) * _a_winkel[i])
				k.rotation = _a_rot0[i] + _a_achse[i] * w
			Typ.FOERDERN:
				_a_uv[i] += _a_achse[i] * (_a_tempo[i] * d)
				_a_mat[i].uv1_offset = _a_uv[i]
	for i in _f_knoten.size():
		_fahre(i, d)
	for i in _p_mat.size():
		_p_mat[i].emission_energy_multiplier = _puls_wert(i)
	for i in _w_knoten.size():
		_w_rest[i] -= d
		if _w_rest[i] <= 0.0:
			_w_rest[i] = _w_intervall[i]
			_w_knoten[i].restart()


func _puls_wert(i: int) -> float:
	var s: float
	var x: float = _zeit * _p_hz[i] * TAU + _p_phase[i]
	match _p_form[i]:
		1:
			s = 1.0 if sin(x) > 0.0 else 0.0
		2:
			s = 0.5 + 0.25 * sin(x * 3.1) + 0.25 * sin(x * 7.3 + 1.7)
		_:
			s = 0.5 + 0.5 * sin(x)
	return lerpf(_p_min[i], _p_max[i], s)


func _fahre(i: int, d: float) -> void:
	var k: Node3D = _f_knoten[i]
	if _f_rest_pause[i] > 0.0:
		_f_rest_pause[i] -= d
		if _f_rest_pause[i] <= 0.0:
			_f_seg[i] = 0
			_f_dir[i] = 1
			_f_weg[i] = 0.0
			var p0: Vector3 = _f_route[i][0]
			k.position = Vector3(p0.x, _f_basis_y[i] + p0.y, p0.z)
			k.visible = true
		return
	if _f_rest_warten[i] > 0.0:
		_f_rest_warten[i] -= d
		return
	var route: PackedVector3Array = _f_route[i]
	var n: int = route.size()
	var seg: int = _f_seg[i]
	var ziel: int = seg + _f_dir[i]
	if _f_modus[i] == 0:
		ziel = (seg + 1) % n
	var a: Vector3 = route[seg]
	var b: Vector3 = route[ziel]
	var laenge: float = maxf(0.001, a.distance_to(b))
	_f_weg[i] += _f_tempo[i] * d
	var t: float = minf(1.0, _f_weg[i] / laenge)
	var q: Vector3 = a.lerp(b, t)
	k.position = Vector3(q.x, _f_basis_y[i] + q.y, q.z)
	var blick: float = atan2(b.x - a.x, b.z - a.z) + _f_versatz[i]
	k.rotation.y = lerp_angle(k.rotation.y, blick, minf(1.0, d * 6.0))
	if t < 1.0:
		return
	_f_weg[i] = 0.0
	_f_seg[i] = ziel
	_f_rest_warten[i] = _f_warten[i][ziel]
	match _f_modus[i]:
		1:
			if ziel == n - 1:
				_f_dir[i] = -1
			elif ziel == 0:
				_f_dir[i] = 1
		2:
			if ziel == n - 1:
				k.visible = false
				_f_rest_pause[i] = maxf(0.05, _f_pause[i])
		_:
			if ziel == 0 and _f_pause[i] > 0.0:
				_f_rest_warten[i] = maxf(_f_rest_warten[i], _f_pause[i])
