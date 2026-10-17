## Der Einstiegspunkt: bindet den Simulationskern an die Darstellung.
##
## Die Richtung ist streng (ADR-004):
##   Eingabe -> Kommando an den Kern
##   Kern -> Ereignis -> Darstellung reagiert
## Diese Datei baut die Welt, haelt den Spielstand und das Tutorial. Die
## Bedienoberflaeche lebt seit ADR-021 in game/ui/hud.gd -- sie stand vorher
## hier und machte diese Datei zur groessten des Projekts.
extends Node3D

const StationViewSkript := preload("res://game/world/station_view.gd")
const NpcPoolSkript := preload("res://game/npc/npc_pool.gd")
const RoomBuilderSkript := preload("res://game/world/room_builder.gd")
const KameraSkript := preload("res://game/world/world_camera.gd")
const TrefferKarteSkript := preload("res://game/world/treffer_karte.gd")

## Sichtbare Ankuenfte pro Sekunde -- gedeckelt (Welten mit Warteschlange).
const ANKUNFT_MIN: float = 0.35
const ANKUNFT_MAX: float = 2.5

## Automatisches Speichern alle 30 Sekunden.
const SPEICHER_INTERVALL: float = 30.0

## Dauer der Blende je Richtung beim Weltwechsel.
const BLENDE_DAUER: float = 0.9

## Ueberblick (K3 A3): verdeckter Streifen oben (Kopf- und Zielleiste, logische
## px wie in _betrete_zone) und Pause zwischen Raumkauf und Zoom-Hinweis (der Raum-Moment kommt zuerst).
const START_OBEN: float = 170.0
const ZOOM_HINWEIS_WARTEN: float = 1.2

## Weltpositionen der Stationen -- gefuellt aus worlds.json beim Aufbau.
##
## ACHTUNG ISOMETRIE: Die Kamera ist um 45 Grad gedreht. "Oben im Bild" ist die
## Weltrichtung (-1, 0, -1), "rechts im Bild" ist (1, 0, -1).
var STATION_POSITIONEN: Dictionary = {}

## Wo Schild, Ring, Treffer und Kamerafokus einer Station sitzen: der Ursprung
## plus der optionale Versatz "schild" aus worlds.json -- fuer Modelle, deren
## sichtbare Mitte nicht auf dem Ursprung liegt.
var ANZEIGE_POSITIONEN: Dictionary = {}

var kern: GameCore
var thema: ThemeData
var kamera: Camera3D
var _ansichten: Dictionary = {}      ## StringName -> StationView | AusstattungsStation
var _grundriss: GrundrissBauer
var _bereich_positionen: Dictionary = {}
var _speicher: SaveManager
var _speicher_rest: float = 0.0
var _npcs: NpcPool
var _ankunft_rest: float = 0.0
var _abfertigung_rest: float = 0.0
var _audio: AudioDirector
var _tutorial: TutorialAblauf
var _tutorial_view: TutorialView
var _tutorial_id_zuletzt: String = ""
## Ziel, fuer das die Kamera schon einmal an den Rand geholt wurde (nicht jede Viertelsekunde).
var _rand_fokus_ziel: String = ""
var _welt_wurzel: Node3D
var _leben: Lebendig   ## Himmel, Glow, Partikel, animierte Kulissen (game/world/e_lebendig.gd)
var _wechsel_view: WeltwechselView
var _wechsel_angeboten: bool = false
var _blende_rect: ColorRect
var _debug_knopf: Button
var _messdaten_knopf: Button
## Lokale Messung (K3 C3): nur user://messung.json, kein Netz.
var _messung: MessungService
var _werbung: AdService
var _laden: StoreService
var _shop: ShopView
var _hud: Hud
var _offline_erloes: float = 0.0
var _figuren: Array[Node3D] = []
var _treffer: RefCounted                 ## TrefferKarte: Boxen fuer Stationen, Raeume, Waende
var _figur_leben: Node3D                 ## FigurLeben (game/npc/figur_leben.gd)
var _upgrade_rest: float = 0.0
## Der Zoom-Hinweis nach dem ersten Raumkauf kommt genau einmal (Einstellungen).
var _zoom_hinweis_gezeigt: bool = false
## K6 §4.1.6: die letzte Kameraansicht aus dem Spielstand ({welt, zoom, x, z}), leer = keine.
var _gespeicherte_kamera: Dictionary = {}
## `--tiefe` kauft Raeume vor -- das ist kein erster Raumkauf des Spielers.
var _vorspulen: bool = false


func _ready() -> void:
	# Android-Zurueck-Taste darf die App nicht wortlos beenden.
	get_tree().set_auto_accept_quit(false)
	# A/B-Schalter (`--variante`, `--ab boost=b,...`) VOR dem Aufbau: Darsteller
	# fragen sie schon beim Bauen ab.
	Experimente.lade_argumente(_pruefschalter())
	ModalSchlange.zuruecksetzen()
	_verbinde_schlange()
	kern = GameCore.new(null, _start_welt_aus_argumenten())
	_starte_messung()
	thema = ThemeData.laden(kern.welt_id())
	_speicher = SaveManager.new()
	_audio = AudioDirector.new()
	add_child(_audio)
	_tutorial = TutorialAblauf.new()
	# Der Stub steht hinter derselben Schnittstelle wie spaeter das SDK.
	_werbung = AdServiceStub.new()
	add_child(_werbung)
	_werbung.belohnung_verdient.connect(_auf_belohnung)
	_werbung.nicht_verfuegbar.connect(_auf_werbung_nicht_verfuegbar)
	_laden = StoreServiceStub.new()
	add_child(_laden)
	_lade_spielstand_vor_dem_aufbau()
	_setze_kapitel()
	_baue_welt()
	_baue_hud()
	_verbinde_kern()
	_audio.verbinde(kern.bus)
	_nach_dem_laden()
	# Absolute Messwerte nachreichen: Ein Stand mitten im Tutorial hat Schritte schon erfuellt.
	_tutorial.melde(&"stufen_gesamt", kern.stufen_gesamt())
	_tutorial.melde(&"ziele_eingeloest", kern.ziele.anzahl_eingeloest())
	_aktualisiere_tutorial()
	# Jetzt erst steht fest, ob die Einfuehrung laeuft und welche Raeume gekauft sind.
	_zeige_start_ansicht(0.0)
	_zeige_eroeffnung_falls_neu()
	_pruefe_screenshot_modus()
	PcSteuerung.starte(self)   # PC-Testumgebung (--pc-test / --pc-test-live), nur Debug, docs/PC_TEST.md


## P1.7: Solange ein Fenster offen ist, schweigt die Tutorialhand -- es fordert
## immer nur EINE Ebene etwas. `--fenster-log` zaehlt die Fenster und schliesst
## jedes nach kurzer Zeit selbst (Pruefung: wie viele Fenster bis zur freien Karte?).
func _verbinde_schlange() -> void:
	var schlange: ModalSchlange = ModalSchlange.global()
	schlange.gezeigt.connect(func(_art: StringName) -> void:
		if _tutorial_view != null:
			_tutorial_view.visible = false)
	schlange.fertig_gemeldet.connect(func(_art: StringName) -> void:
		_nach_fenster.call_deferred())
	if not _pruefschalter().has("--fenster-log"):
		return
	# `--fenster-log moment,kapitel`: nur diese Arten selbst schliessen (Vorschau des naechsten).
	var nur: String = _wert_nach(_pruefschalter(), "--fenster-log", "")
	var arten: PackedStringArray = [] if nur.begins_with("--") else nur.split(",", false)
	schlange.gezeigt.connect(func(art: StringName) -> void:
		print("FENSTER %d: %s @%.1fs" % [schlange.anzahl_gezeigt(), art, Time.get_ticks_msec() / 1000.0])
		if arten.is_empty() or arten.has(String(art)):
			get_tree().create_timer(0.6).timeout.connect(func() -> void:
				if schlange.offene_art() == art:
					schlange.schliesse_offenes()))


func _nach_fenster() -> void:
	if not ModalSchlange.global().ist_offen():
		_aktualisiere_tutorial()


var _hud_rest: float = 0.0

func _process(delta: float) -> void:
	if _probe != null:
		_probe_schritt()
	# P1.7: Ein Fenster ist oben -- die Tutorialkarte samt Hand wartet darunter nicht sichtbar.
	if _tutorial_view != null and _tutorial_view.visible and ModalSchlange.global().ist_offen():
		_tutorial_view.visible = false
	kern.tick(delta)
	if _messung != null:
		_messung.tick(delta)
	_bewege_npcs(delta)
	_bewege_figuren(delta)
	_hud_rest -= delta
	if _hud_rest <= 0.0:
		_hud_rest = 0.25
		_aktualisiere_tutorial_ziel()
		_aktualisiere_upgrade_ringe()
	_speicher_rest += delta
	if _speicher_rest >= SPEICHER_INTERVALL:
		_speicher_rest = 0.0
		_speichere()


## Koppelt die Warteschlangen-Figuren an die gerechnete Wirtschaft (Welten 2-6).
##
## Ankunft = was die ANNAHME schafft, Abfertigung = was die ganze Kette schafft.
## Bremst ein spaeteres Glied, waechst die Schlange sichtbar. Die Figuren
## erzeugen dabei KEIN Geld (ADR-007).
func _bewege_npcs(delta: float) -> void:
	if _npcs == null:
		return
	var annahme: StationModel = kern.kette.station(Ids.STATION_INTAKE)
	var ankunft_rate: float = clampf(
		annahme.durchsatz() if annahme != null else 0.0, ANKUNFT_MIN, ANKUNFT_MAX)
	var abfertigung_rate: float = clampf(kern.kette.effektiver_durchsatz(), 0.0, ANKUNFT_MAX)
	_ankunft_rest += ankunft_rate * delta
	while _ankunft_rest >= 1.0:
		_ankunft_rest -= 1.0
		if not _npcs.lass_erscheinen():
			_ankunft_rest = 0.0
			break
	_abfertigung_rest += abfertigung_rate * delta
	while _abfertigung_rest >= 1.0:
		_abfertigung_rest -= 1.0
		if not _npcs.fertige_vorderste_ab():
			_abfertigung_rest = 0.0
			break


# --- Aufbau ------------------------------------------------------------------

## Baut den sichtbaren Teil EINER Welt unter `_welt_wurzel` auf -- beim
## Weltwechsel wird genau dieser Knoten freigegeben und neu gebaut.
func _baue_welt() -> void:
	var i: int = kern.welt_index
	STATION_POSITIONEN = kern.welten.stationen(i)
	ANZEIGE_POSITIONEN = kern.welten.stationen_anzeige(i)
	_ansichten.clear()
	_figuren.clear()
	_bewohner.clear()
	_darsteller.clear()
	_grundriss = null
	_npcs = null
	_welt_wurzel = Node3D.new()
	add_child(_welt_wurzel)

	_baue_licht(kern.welten.licht(i))

	if kern.welten.hat_zonen(i):
		_grundriss = GrundrissBauer.new()
		_welt_wurzel.add_child(_grundriss)
		_grundriss.bauen(kern.welt_id(), kern.welten.zonen(i), kern.welten.waende(i),
			kern.welten.module(i))
		_grundriss.aktualisiere(kern)
		_bereich_positionen = kern.welten.bereich_positionen(i)
	else:
		var raum := RoomBuilderSkript.new()
		_welt_wurzel.add_child(raum)
		raum.bauen(kern.welt_id(), kern.welten.raum_breite(i), kern.welten.raum_tiefe(i),
			kern.welten.grundriss(i))
		_bereich_positionen = {}

	_treffer = TrefferKarteSkript.new()
	_treffer.bauen(ANZEIGE_POSITIONEN, kern.welten.zonen(i), kern.welten.waende(i))
	# Die Startzone hat keinen Bereich -- sie bekommt trotzdem ihr Panel.
	var start_zone: Dictionary = kern.welten.startzone(i)
	if not start_zone.is_empty():
		_bereich_positionen[Menues.START_RAUM] = Vector3(
			(float(start_zone.get("x1", 0)) + float(start_zone.get("x2", 0))) * 0.5, 0.0,
			(float(start_zone.get("z1", 0)) + float(start_zone.get("z2", 0))) * 0.5)

	_baue_kulisse()

	var figuren: Dictionary = kern.welten.figuren(i)
	if String(figuren.get("modus", "kunden")) != "wg":
		_npcs = NpcPoolSkript.new()
		_welt_wurzel.add_child(_npcs)
		var halb_x: float = float(kern.welten.raum_breite(i)) * 0.5 - 1.0
		var halb_z: float = float(kern.welten.raum_tiefe(i)) * 0.5 - 1.0
		_npcs.aufbauen(Vector3(-halb_x, 0.0, -1.0), Vector3(-1.0, 0.0, -halb_z),
			STATION_POSITIONEN[Ids.STATION_INTAKE], figuren)
	else:
		_baue_wg_figuren()

	var mit_ausstattung: bool = kern.welten.stationsmodell(i) == "ausstattung"
	for id in Ids.ALL_STATIONS:
		if not STATION_POSITIONEN.has(id):
			continue
		var station: StationModel = kern.kette.station(id)
		if mit_ausstattung:
			var ansicht := AusstattungsStation.new()
			_welt_wurzel.add_child(ansicht)
			var plaetze: Array[StringName] = []
			if station != null:
				for p in station.ausstattung:
					plaetze.append(p.id)
			ansicht.aufbauen(id, STATION_POSITIONEN[id], kern.welt_id(), plaetze)
			ansicht.setze_ring_versatz((ANZEIGE_POSITIONEN[id] as Vector3) - (STATION_POSITIONEN[id] as Vector3))
			_ansichten[id] = ansicht
		else:
			var alt: StationView = StationViewSkript.new()
			_welt_wurzel.add_child(alt)
			alt.aufbauen(id, STATION_POSITIONEN[id], kern.welt_id())
			alt.visible = station != null and station.freigeschaltet
			_ansichten[id] = alt
	_gleiche_stationen_an()
	_baue_figur_leben()

	kamera = KameraSkript.new()
	_welt_wurzel.add_child(kamera)
	kamera.current = true
	kamera.welt_getippt.connect(_auf_welt_getippt)
	kamera.doppelt_getippt.connect(_auf_doppeltipp)
	var karte: Dictionary = kern.welten.karte(i)
	kamera.setze_grenzen(karte["grenzen"] as Rect2, float(karte["zoom_min"]), float(karte["zoom_max"]))
	kamera.setze_welt_zoom(kern.welten.zoom_start(i))
	kamera.setze_blickpunkt(karte["start"] as Vector3)
	# Zoom-Stufen (K3 A3): Der Pinch rastet, der Doppeltipp wechselt die Stufe.
	var stufen: Dictionary = (kern.welten.welt(i).get("karte", {}) as Dictionary).get("zoom_stufen", {}) as Dictionary
	if not stufen.is_empty():
		kamera.setze_stufen(float(stufen.get("raum", karte["zoom_min"])), float(stufen.get("ueberblick", karte["zoom_max"])))
	var ganz: Dictionary = _ansicht_fuer(_zonen_im_blick(true))
	if not ganz.is_empty():
		kamera.ueberblick_blick = ganz["blick"] as Vector3
	_zeige_start_ansicht(0.0)

	_markiere_engpass(kern.kette.bottleneck())


## Licht und Hintergrund je Welt -- die Werte stehen in worlds.json ("licht",
## aufgeloest von WorldData.licht). Die WG ist warm und hell (ADR-021); jede
## Welt hat ihre eigene Stimmung. Bewusst OHNE Filmic-Tonemapping: Bei warmem
## Umgebungslicht wurde die Karte damit fast weiss (CLAUDE.md).
func _baue_licht(werte: Dictionary) -> void:
	var umgebung := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.background_color = Color(String(werte.get("hintergrund", "e9d8bf")))
	env.ambient_light_color = Color(String(werte.get("umgebung", "ffe8cc")))
	env.ambient_light_energy = float(werte.get("umgebung_energie", 0.38))
	# Lebendigkeit: Himmel/Glow nur, wenn die Welt sie in "licht" benennt.
	_leben = Lebendig.new()
	_welt_wurzel.add_child(_leben)
	werte = _leben.mit_test_licht(kern.welt_id(), werte)
	_leben.baue_umgebung(env, werte)
	_leben.baue_partikel([werte.get("partikel", []), kern.welten.welt(kern.welt_index).get("partikel", [])])
	umgebung.environment = env
	_welt_wurzel.add_child(umgebung)

	var licht := DirectionalLight3D.new()
	var richtung: Dictionary = werte.get("sonne_richtung", {}) as Dictionary
	licht.rotation_degrees = Vector3(float(richtung.get("x", -55.0)), float(richtung.get("y", -30.0)), 0.0)
	licht.light_energy = float(werte.get("sonne_energie", 0.85))
	licht.light_color = Color(String(werte.get("sonne", "ffe9c9")))
	if bool(werte.get("schatten", true)):
		# Weiche Schatten geben der Karte Tiefe -- ohne sie stehen Moebel wie
		# aufgeklebt auf dem Boden. Gemessen wird am Geraet (TASK 080).
		licht.shadow_enabled = true
		licht.shadow_blur = 1.5
		licht.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
		licht.directional_shadow_max_distance = 60.0
	_welt_wurzel.add_child(licht)


## Die Kulisse macht aus einer Flaeche einen Ort. Reine Deko, Positionen aus
## worlds.json.
func _baue_kulisse() -> void:
	var gebaut: Array = []
	for eintrag in kern.welten.kulisse(kern.welt_index):
		var name: String = eintrag[0] as String
		var pfad: String = _asset_pfad("world", name)
		if pfad.is_empty():
			gebaut.append(null)
			continue
		var knoten: Node3D = (load(pfad) as PackedScene).instantiate()
		knoten.position = eintrag[1] as Vector3
		knoten.rotation_degrees = Vector3(0.0, eintrag[2] as float, 0.0)
		# Optional: "skala" im rohen Eintrag (gleicher Index) verkleinert/vergroessert ein Requisit.
		var roh_liste: Array = kern.welten.welt(kern.welt_index).get("kulisse", []) as Array
		var idx: int = gebaut.size()
		if idx < roh_liste.size() and roh_liste[idx] is Dictionary:
			var sk: float = float((roh_liste[idx] as Dictionary).get("skala", 1.0))
			if sk > 0.05 and not is_equal_approx(sk, 1.0):
				knoten.scale = Vector3.ONE * sk
		_welt_wurzel.add_child(knoten)
		gebaut.append(knoten)
	# Animation und Emission-Puls stehen im rohen Eintrag (WorldData.kulisse reicht sie nicht durch).
	if _leben != null:
		_leben.baue_kulisse(_leben.mit_test_kulisse(kern.welt_id(),
			kern.welten.welt(kern.welt_index).get("kulisse", []) as Array), gebaut)


## Leben auf der Karte (ADR-021, fuer jede Welt mit Figurenmodus "wg"): die
## Spielfigur an ihrer Station (von hinten, Kapuze, kein Gesicht), Figuren auf
## ihren Wegen, Darsteller an den Stationen und die Teile, die von Station zu
## Station fliegen.
func _baue_wg_figuren() -> void:
	var daten: Dictionary = kern.welten.figuren_roh(kern.welt_index)

	var spieler: Dictionary = daten.get("spielfigur", {}) as Dictionary
	var sid := StringName(String(spieler.get("station", "")))
	var spieler_pfad: String = _asset_pfad("characters", "figur_kapuze_sitzend") if STATION_POSITIONEN.has(sid) else ""
	if not spieler_pfad.is_empty():
		var figur: Node3D = (load(spieler_pfad) as PackedScene).instantiate()
		figur.position = STATION_POSITIONEN[sid] as Vector3 + Vector3(float(spieler.get("x", 0.0)), 0.0, float(spieler.get("z", 0.0)))
		figur.rotation_degrees.y = float(spieler.get("blick", 180.0))
		_welt_wurzel.add_child(figur)
		_figuren.append(figur)

	# Mehrere Darsteller je Welt; das alte einzelne Objekt gilt weiter.
	for eintrag in kern.welten.darsteller(kern.welt_index):
		var d: Dictionary = eintrag as Dictionary
		var did := StringName(String(d.get("station", "")))
		if not STATION_POSITIONEN.has(did):
			push_warning("Darsteller '%s': Station '%s' steht nicht auf der Karte" % [String(d.get("figur", "")), did])
			continue
		var dpfad: String = _asset_pfad("characters", String(d.get("figur", "")))
		if dpfad.is_empty():
			continue
		var figur: Node3D = (load(dpfad) as PackedScene).instantiate()
		figur.position = STATION_POSITIONEN[did] as Vector3 + Vector3(float(d.get("x", 0.0)), 0.0, float(d.get("z", 0.0)))
		figur.rotation_degrees.y = float(d.get("blick", 0.0))
		figur.set_meta("ab", d.get("ab", {}))
		_welt_wurzel.add_child(figur)
		_darsteller.append(figur)

	_bewohner.clear()
	var versatz: int = 0
	for eintrag in (daten.get("bewohner", []) as Array):
		var b: Dictionary = eintrag as Dictionary
		var figur := Bewohner.new()
		var bpfad: String = _asset_pfad("characters", String(b.get("figur", "")))
		if not bpfad.is_empty() and figur.aufbauen(bpfad, b.get("route", []) as Array, versatz):
			figur.set_meta("solange_nicht_verfuegbar", String(b.get("solange_nicht_verfuegbar", "")))
			figur.set_meta("ab", b.get("ab", {}))
			figur.set_meta("bis", b.get("bis", {}))
			_welt_wurzel.add_child(figur)
			_bewohner.append(figur)
		else:
			figur.free()
		versatz += 5

	var fluss := ClipFluss.new()
	_welt_wurzel.add_child(fluss)
	var reihenfolge: Array[StringName] = [Ids.STATION_INTAKE, Ids.STATION_BUFFER,
		Ids.STATION_PROCESSING, Ids.STATION_TRANSPORT]
	fluss.aufbauen(kern, STATION_POSITIONEN, reihenfolge, kern.welt_id())
	fluss.clip_raus.connect(func(welt: Vector3, rate: float) -> void:
		if _hud != null:
			_hud.zeige_clip_ertrag(welt, rate))
	_aktualisiere_bewohner()


var _darsteller: Array[Node3D] = []
var _bewohner: Array[Bewohner] = []


## Haengt das Leben der Figuren ein (Wippen, Kopfdrehen, Jubel). Es liegt in
## game/npc/figur_leben.gd (Paket B); per load(), damit main.gd auch ohne die
## Datei laeuft.
func _baue_figur_leben() -> void:
	_figur_leben = null
	var pfad: String = "res://game/npc/figur_leben.gd"
	if not ResourceLoader.exists(pfad):
		return
	var alle: Array[Node3D] = []
	alle.append_array(_figuren)
	alle.append_array(_darsteller)
	for b in _bewohner:
		alle.append(b)
	_figur_leben = (load(pfad) as GDScript).new() as Node3D
	_welt_wurzel.add_child(_figur_leben)
	_figur_leben.call("aufbauen", alle, kern.bus, STATION_POSITIONEN)


## Der Pfad eines Modells: erst die eigene Welt, dann der gemeinsame Ordner.
## Leer, wenn es beides nicht gibt -- dann laut (Baugerueste muessen laut sein).
func _asset_pfad(art: String, name: String) -> String:
	if name.is_empty():
		return ""
	var eigen: String = "res://assets/%s/%s/%s.glb" % [art, kern.welt_id(), name]
	if ResourceLoader.exists(eigen):
		return eigen
	var gemeinsam: String = "res://assets/%s/gemeinsam/%s.glb" % [art, name]
	if ResourceLoader.exists(gemeinsam):
		return gemeinsam
	push_warning("Modell fehlt: %s (auch nicht in %s/gemeinsam)" % [eigen, art])
	return ""


## Ist eine Figuren-Bedingung aus worlds.json erfuellt? Leer = immer.
##
## Kurzformen: {"bereich": id} (gekauft), {"station", "platz", "stufe"}
## (Ausstattungsstufe), {"station", "stufe"} (Stationsstufe). Mit "typ" gilt
## die volle Bedingung wie bei Zielen.
func _figur_bedingung(b: Dictionary) -> bool:
	if b.is_empty():
		return true
	if b.has("typ"):
		return kern.bedingung_erfuellt(b)
	if b.has("bereich"):
		return kern.bereiche.ist_gekauft(StringName(String(b["bereich"])))
	if b.has("platz"):
		return kern.bedingung_erfuellt({"typ": "ausstattung_stufe", "station": b.get("station", ""),
			"platz": b["platz"], "wert": int(b.get("stufe", 1))})
	if b.has("station"):
		return kern.bedingung_erfuellt({"typ": "station_stufe", "station": b["station"],
			"wert": int(b.get("stufe", 1))})
	return true


## Wer ist gerade da? Figuren gehen ("bis") und kommen ("ab") mit dem Fortschritt:
## Tobi zieht aus, sobald sein Zimmer kaufbar wird; der Kumpel kommt, sobald es
## eine Kamera gibt, vor der er stehen kann.
func _aktualisiere_bewohner() -> void:
	for figur in _bewohner:
		var bereich := StringName(String(figur.get_meta("solange_nicht_verfuegbar", "")))
		var da: bool = bereich == &"" or not (kern.bereiche.verfuegbar(bereich) or kern.bereiche.ist_gekauft(bereich))
		var bis: Dictionary = figur.get_meta("bis", {}) as Dictionary
		if not bis.is_empty() and _figur_bedingung(bis):
			da = false
		figur.visible = da and _figur_bedingung(figur.get_meta("ab", {}) as Dictionary)
	for figur in _darsteller:
		if not is_instance_valid(figur):
			continue
		var war: bool = figur.visible
		figur.visible = _figur_bedingung(figur.get_meta("ab", {}) as Dictionary)
		if figur.visible and not war:
			figur.scale = Vector3(0.2, 0.2, 0.2)
			create_tween().tween_property(figur, "scale", Vector3.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


var _figur_zeit: float = 0.0

func _bewege_figuren(delta: float) -> void:
	if _figuren.is_empty():
		return
	_figur_zeit += delta
	for figur in _figuren:
		var koerper: Node3D = figur.find_child("koerper", true, false) as Node3D
		if koerper == null:
			continue
		# Tippen: leichtes Wippen und abwechselnde Arme.
		koerper.rotation.x = sin(_figur_zeit * 2.2) * 0.03
		var arm_l: Node3D = koerper.find_child("arm_l", false, false) as Node3D
		var arm_r: Node3D = koerper.find_child("arm_r", false, false) as Node3D
		if arm_l != null:
			arm_l.rotation.x = sin(_figur_zeit * 9.0) * 0.07
		if arm_r != null:
			arm_r.rotation.x = sin(_figur_zeit * 9.0 + PI) * 0.07


func _baue_hud() -> void:
	var ebene := CanvasLayer.new()
	ebene.layer = 1
	add_child(ebene)

	# A/B-Vergleich der Oberflaeche: `--variante a|b`, `--ab schirm=a|b,...` --
	# gelesen in _ready (Experimente.lade_argumente).
	_hud = Hud.new()
	_hud.tutorial_zeigt = func(was: String) -> bool: return _tutorial != null and _tutorial.zeigt(was)
	# K6 1c: eine Textquelle zur Zeit -- Blasen warten, solange die Tutorialkarte spricht.
	_hud.tutorial_karte_sichtbar = func() -> bool:
		return _tutorial_view != null and _tutorial_view.is_visible_in_tree() and _tutorial_view.kartenhoehe() > 0.0
	ebene.add_child(_hud)
	_hud.aufbauen(kern, thema, _audio, _werbung)
	_hud.setze_karte(kamera, ANZEIGE_POSITIONEN, _bereich_positionen)
	_hud.marker.thema = thema
	_hud.ortsblase.figur_suche = _figur_fuer_absender
	# K6 1c (Handy-Befund 1): Oeffnet der Spieler ein Stations- oder Raummenue, schiebt die
	# Kamera nur so weit, dass das Gemeinte ueber dem Panel steht -- ohne Zoom, ohne Rueckfahrt.
	_hud.station_fokus.connect(func(id: StringName) -> void:
		if ANZEIGE_POSITIONEN.has(id):
			_halte_ueber_panel(ANZEIGE_POSITIONEN[id] as Vector3))
	_hud.schnellkauf_fokus.connect(func(id: StringName) -> void:
		if _bereich_positionen.has(id):
			_halte_ueber_panel(_bereich_positionen[id] as Vector3))
	_hud.clips_zeigen_ertrag = kern.welten.figuren_roh(kern.welt_index).get("modus", "") == "wg"
	ZeigeHand.leerlauf(ebene, _hud.kauf_punkt)
	# K6 §4.1 (Bastian 16.10.: "Das soll man selbst einstellen"): Station, Raum,
	# Plakette, Ausbauliste und Schnellkauf fahren und zoomen NICHT (bereich_fokus bleibt
	# unverbunden); station_fokus/schnellkauf_fokus schieben nur, wenn das Panel verdeckt (oben).
	# Einzige Fahrt im Normalspiel ausser dem Doppeltipp: der Rand-Tab -- der Spieler
	# tippt ihn, um zu einem Raum ausserhalb des Bildes zu kommen (§4.1.7), ohne Zoom.
	_hud.marker.bereich_richtung.connect(_fokussiere_bereich_ohne_panel)
	# "Raum ansehen" im Schnellkauf ist dieselbe ausdrueckliche Bitte: hinschieben, ohne Zoom.
	_hud.schnellkauf.raum_ansehen.connect(_fokussiere_bereich_ohne_panel)
	_hud.laden_gewuenscht.connect(func() -> void:
		_tutorial_view.verbergen()
		_shop.oeffnen())
	_hud.speichern_gewuenscht.connect(_speichere)
	_hud.tutorial_ereignis.connect(_tutorial_melde)
	_hud.stationsmenue.geschlossen.connect(_aktualisiere_tutorial)
	# K6 §4.1: Nach dem Schliessen eines Menues faehrt die Kamera NICHT zurueck --
	# Zoom und Ausschnitt bestimmt der Spieler.

	# Zuletzt eingehaengt und damit ueber allem: Ein Hinweis, der hinter dem
	# liegt, worauf er zeigt, ist keiner.
	_tutorial_view = TutorialView.new()
	_tutorial_view.ueberspringen_gedrueckt.connect(_auf_tutorial_uebersprungen)
	_tutorial_view.rand_pfeil_gedrueckt.connect(_auf_tutorial_rand_pfeil)
	_tutorial_view.meide = func() -> Array[Rect2]: return _hud.marker.sichtbare_rechtecke()
	ebene.add_child(_tutorial_view)

	# Der Laden bekommt eine EIGENE CanvasLayer ueber der Hud.
	var laden_ebene := CanvasLayer.new()
	laden_ebene.layer = 10
	add_child(laden_ebene)
	_shop = ShopView.new()
	_shop.verbinde(_laden)
	_shop.geschlossen.connect(_aktualisiere_tutorial)
	laden_ebene.add_child(_shop)

	# Debug-Werkzeug: nur in Debug-Builds (ARCHITECTURE.md 5).
	if OS.is_debug_build():
		_debug_knopf = Button.new()
		_debug_knopf.text = "+Geld"
		# Rechts am Rand, auf halber Hoehe: Dort liegt weder ein Menue noch die
		# Tutorialkarte noch ein Schild. Der Knopf ist schon viermal umgezogen.
		_debug_knopf.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
		_debug_knopf.offset_left = 8.0
		_debug_knopf.offset_right = 94.0
		_debug_knopf.offset_top = -Menueleiste.HOEHE - 76.0
		_debug_knopf.offset_bottom = -Menueleiste.HOEHE - 16.0
		_debug_knopf.add_theme_font_size_override("font_size", 20)
		_debug_knopf.pressed.connect(func() -> void:
			# Zehn Minuten Einkommen, mindestens 1000 -- ein fester Betrag waere
			# in Welt 1 zu viel und ab der Mitte zu wenig.
			var betrag: float = maxf(kern.einkommen_pro_sekunde() * 600.0, 1000.0)
			kern.kapital += betrag
			kern.bus.money_changed.emit(kern.kapital, betrag))
		ebene.add_child(_debug_knopf)
		# Messdaten (K3 C3) in die Zwischenablage -- zum Einfuegen in eine Datei.
		_messdaten_knopf = Button.new()
		_messdaten_knopf.text = UiText.t("messdaten_kopieren")
		_messdaten_knopf.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
		_messdaten_knopf.offset_left = 8.0
		_messdaten_knopf.offset_right = 250.0
		_messdaten_knopf.offset_top = -Menueleiste.HOEHE - 148.0
		_messdaten_knopf.offset_bottom = -Menueleiste.HOEHE - 88.0
		_messdaten_knopf.add_theme_font_size_override("font_size", 20)
		_messdaten_knopf.pressed.connect(func() -> void:
			if _messung != null:
				DisplayServer.clipboard_set(_messung.als_json()))
		ebene.add_child(_messdaten_knopf)


func _verbinde_kern() -> void:
	kern.bus.bottleneck_changed.connect(_markiere_engpass)
	kern.bus.station_upgraded.connect(_auf_station_ausgebaut)
	kern.bus.equipment_upgraded.connect(_auf_ausstattung_gekauft)
	kern.bus.unlocked.connect(_auf_freischaltung)
	kern.bus.area_bought.connect(_auf_bereich_gekauft)
	kern.bus.world_completed.connect(_auf_welt_abgeschlossen)
	_verbinde_messung()


# --- Lokale Messung (K3 C3) ------------------------------------------------------

func _starte_messung() -> void:
	_messung = MessungService.new()
	var ab: Dictionary = {}
	for schirm in Experimente.schirme():
		ab[schirm] = Experimente.variante(schirm)
	_messung.starte(kern.welt_id(), ab, " ".join(_pruefschalter()))


## Nur Signale, die es schon gibt: Kern-Bus, Werbedienst, Marker der Hud.
func _verbinde_messung() -> void:
	kern.bus.station_upgraded.connect(func(id: StringName, _stufe: int) -> void:
		_messe(&"kauf", String(id)))
	kern.bus.equipment_upgraded.connect(func(id: StringName, platz: StringName, _stufe: int) -> void:
		_messe(&"kauf", "%s/%s" % [String(id), String(platz)]))
	kern.bus.area_bought.connect(func(bereich: StringName) -> void:
		_messe(&"raum", {"id": String(bereich), "n": kern.bereiche.anzahl_gekauft()}))
	kern.bus.moment_ended.connect(func(_id: StringName, angetippt: bool, _lohn: float) -> void:
		_messe(&"moment", "getippt" if angetippt else "verpasst"))
	_werbung.belohnung_verdient.connect(func(platz: StringName) -> void:
		_messe(&"angebot_genommen", String(platz)))
	_werbung.abgebrochen.connect(func(platz: StringName) -> void:
		_messe(&"angebot_abgelehnt", String(platz)))
	_werbung.angebot_gezeigt.connect(func(platz: StringName) -> void:
		_messe(&"angebot_gezeigt", String(platz)))
	if _hud != null and _hud.marker != null:
		_hud.marker.station_getippt.connect(func(id: StringName) -> void:
			_messe_tipp(&"tipp_station", "marker:%s" % String(id)))
		_hud.marker.bereich_getippt.connect(func(id: StringName) -> void:
			_messe_tipp(&"tipp_plakette", "marker:%s" % String(id)))


func _messe(art: StringName, daten: Variant = null) -> void:
	if _messung != null and not _vorspulen:
		_messung.ereignis(art, kern.welt_id(), daten)


func _messe_tipp(art: StringName, daten: Variant = null) -> void:
	if _messung != null and not _vorspulen:
		_messung.tipp(art, kern.welt_id(), daten)


func _messung_ende() -> void:
	if _messung != null:
		_messung.sitzung_ende(kern.welt_id())


func _notification(was: int) -> void:
	match was:
		NOTIFICATION_WM_GO_BACK_REQUEST:
			# Zurueck schliesst zuerst ein offenes Menue -- erst dann die App.
			if _hud != null and _hud.schliesse_alle():
				return
			_messung_ende()
			_speichere()
			get_tree().quit()
		NOTIFICATION_WM_CLOSE_REQUEST:
			_messung_ende()
			_speichere()
			get_tree().quit()
		NOTIFICATION_APPLICATION_PAUSED:
			_messung_ende()
			_speichere()


# --- Reaktionen --------------------------------------------------------------

## Antippen der Karte: Der Strahl der Kamera wird gegen Boxen gerechnet (RELEASE_PLAN
## 2). Station getroffen -> ihr Menue. Raum getroffen -> das Panel dieses Raums,
## gekauft oder nicht; im Ueberblick stattdessen der Schnellkauf (K4 P1.1).
## Nebenraum ohne Kauf: nur im Ueberblick sein Satz, im Raum-Zoom nichts (K6).
## Nichts getroffen -> ein offenes Menue schliesst. Die Kamera bewegt sich bei
## keinem Tipp (K6 §4.1) -- nur Finger, Doppeltipp und Rand-Tab bewegen sie.
##
## Eine Zeile `tipp: <ziel>` je Tipp im Log (adb logcat -s godot): Zwei Zeilen
## je Fingertipp waeren der Doppeltipp-Fehler (RELEASE_PLAN 9.1).
func _auf_welt_getippt(ursprung: Vector3, richtung: Vector3, boden: Vector3) -> void:
	var treffer: Dictionary = {"art": "nichts", "station": &"", "zone": {}, "punkt": boden}
	if _treffer != null:
		treffer = _treffer.finde(ursprung, richtung)
	var art: String = String(treffer["art"])
	if art == "station":
		var id: StringName = treffer["station"] as StringName
		print("tipp: station %s" % id)
		_messe_tipp(&"tipp_station", "welt:%s" % String(id))
		var ansicht: Node = _ansichten.get(id)
		if ansicht != null and ansicht.has_method("blitzen"):
			ansicht.call("blitzen")
		_hud.zeige_station(id)
		return
	if art == "zone" or art == "boden":
		var zone: Dictionary = treffer["zone"] as Dictionary
		var raum: StringName = _raum_der_zone(zone)
		if raum != &"":
			print("tipp: raum %s (%s)" % [raum, String(zone.get("id", ""))])
			_messe_tipp(&"tipp_plakette", "boden:%s" % String(raum))
			if _hud.marker.ist_ueberblick():
				_hud.zeige_schnellkauf(raum)
				return
			_hud.zeige_bereich(raum)
			return
		var zone_id := StringName(String(zone.get("id", "")))
		if not WeltTexte.nebenraum(thema, zone_id, "name").is_empty() and _hud.marker.ist_ueberblick():
			# Nebenraum (Bad, Pausenraum ...): im Ueberblick Name und ein Satz. Im Raum-Zoom
			# oeffnet der Boden kein leeres Panel ("hier gibt es nichts zu kaufen", K6).
			print("tipp: nebenraum %s" % zone_id)
			_messe_tipp(&"tipp_plakette", "boden:%s" % String(zone_id))
			_hud.zeige_nebenraum(zone_id)
			return
		print("tipp: zone %s (ohne Panel)" % zone_id)
		_messe_tipp(&"tipp_leer", "zone")
	else:
		print("tipp: nichts")
		_messe_tipp(&"tipp_leer", "nichts")
	_hud.schliesse_alle()


## Welches Raum-Panel gehoert zu dieser Zone? Ein Bereich -> seine Id, die
## Startzone -> das Start-Panel, jede andere Zone (Bad, Nachbarzimmer) -> keins.
func _raum_der_zone(zone: Dictionary) -> StringName:
	if zone.is_empty():
		return &""
	var bereich := StringName(String(zone.get("bereich", "")))
	if bereich != &"":
		return bereich
	var start: Dictionary = kern.welten.startzone(kern.welt_index)
	if not start.is_empty() and String(start.get("id", "")) == String(zone.get("id", "")):
		return Menues.START_RAUM
	return &""


## Randschild: nur hinfahren, nichts oeffnen. Fahrt auf den Raum ohne Menue-Hoehe und
## ohne Zoom -- ausgeloest vom Spieler (K6 §4.1.7).
func _fokussiere_bereich_ohne_panel(id: StringName) -> void:
	if _bereich_positionen.has(id):
		_fokussiere_punkt(_bereich_positionen[id] as Vector3)


## Nur noch fuer Pruefschalter (`--menue bereich_x`, Vorschaubilder): Fahrt auf den Raum.
## Im Spiel faehrt kein Menue die Kamera (K6 §4.1).
func _fokussiere_bereich(id: StringName) -> void:
	var zonen: Array[Dictionary] = Menues.zonen_des_raums(kern, id)
	if not zonen.is_empty():
		_betrete_zone(zonen[0], Vector3.INF)
	elif _bereich_positionen.has(id):
		_fokussiere_punkt(_bereich_positionen[id] as Vector3)


## Raum betreten (K2 6.2): Die Kamera faehrt weich auf den Raum und zoomt hinein,
## ueber dem Panel. `tipp` ist der angetippte Bodenpunkt (Vector3.INF = keiner):
## Fuer lange Raeume (Flur) bleibt die Kamera dort, statt in die Mitte zu springen.
func _betrete_zone(zone: Dictionary, tipp: Vector3, mit_zoom: bool = false) -> void:
	if kamera == null or zone.is_empty():
		return
	var mitte := Vector3(
		(float(zone.get("x1", 0)) + float(zone.get("x2", 0))) * 0.5, 0.0,
		(float(zone.get("z1", 0)) + float(zone.get("z2", 0))) * 0.5)
	await get_tree().process_frame
	await get_tree().process_frame
	if kamera == null or not is_instance_valid(kamera):
		return
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var unten: float = _hud.offenes_menue_hoehe()
	# Steht die Tutorialkarte ueber dem Menue, gehoert ihr Platz dazu (wie _fokussiere_punkt).
	if _tutorial_view != null and _tutorial_view.visible:
		unten += _tutorial_view.kartenhoehe() + 16.0
	var oben: float = maxf(170.0, _hud.ziel_unterkante() + 8.0)
	var frei: float = maxf(flaeche.y - unten - oben, 120.0)
	var ziel_zoom: float = KameraSkript.raum_zoom(zone, flaeche, frei)
	var punkt: Vector3 = mitte
	# K3-Fix 2: Mitte der STATIONEN statt Mitte des Raums oder Tippstelle; der Zoom
	# richtet sich nach dem Kasten um die Stationen, damit alle ueber dem Panel stehen.
	var stationen: Dictionary = kern.welten.stationen(kern.welt_index)
	var punkte: Array = []
	for id in kern.welten.stationen_in_zone(kern.welt_index, zone):
		punkte.append(stationen[id] as Vector3)
	var rand_m: float = _karten_wert("raum_rand_m", 2.0)
	var nah: Dictionary = KameraSkript.punkte_ansicht(punkte, rand_m, flaeche, oben, unten)
	if not nah.is_empty():
		punkt = nah["mitte"] as Vector3
		var kleinster: float = _karten_wert("raum_zoom_min", 12.0)
		ziel_zoom = minf(ziel_zoom, maxf(float(nah["zoom"]), kleinster))
	elif ziel_zoom >= kamera.zoom() - 0.01 and tipp.is_finite():
		# Der Raum passt auch hineingezoomt nicht ins Bild: dort bleiben, wo getippt wurde.
		punkt = Vector3(clampf(tipp.x, float(zone["x1"]), float(zone["x2"])), 0.0,
			clampf(tipp.z, float(zone["z1"]), float(zone["z2"])))
	var ziel_y: float = oben + frei * 0.5
	if nah.is_empty():
		kamera.betrete(punkt + Vector3(0.0, 0.8, 0.0), ziel_y, minf(ziel_zoom, kamera.zoom()), 0.5, mit_zoom)
	else:
		kamera.betrete(punkt + Vector3(0.0, 0.8, 0.0), ziel_y, ziel_zoom, 0.5, mit_zoom)


## Ein Wert aus karte.zoom_stufen der aktuellen Welt (worlds.json).
func _karten_wert(schluessel: String, ersatz: float) -> float:
	var stufen: Dictionary = (kern.welten.welt(kern.welt_index).get("karte", {}) as Dictionary).get("zoom_stufen", {}) as Dictionary
	return float(stufen.get(schluessel, ersatz))


## Die Figur eines Absenders auf der Karte (theme.json absender_figur), sonst null.
func _figur_fuer_absender(von: String) -> Node3D:
	if thema == null or _welt_wurzel == null or not is_instance_valid(_welt_wurzel):
		return null
	var figuren: Dictionary = thema.abschnitt("absender_figur")
	if not figuren.has(von):
		return null
	return Lebendig.AufgabenHinweis._suche_modell(_welt_wurzel, "/" + String(figuren[von]) + ".glb")


## K6 1c: Liegt `punkt` unter dem offenen Panel (oder der Tutorialkarte darueber) bzw. unter
## der Zielleiste, schiebt die Kamera ihn gerade so weit, dass er frei steht. Kein Zoom,
## keine Fahrt, wenn er schon sichtbar ist; beim Schliessen faehrt nichts zurueck.
func _halte_ueber_panel(punkt: Vector3) -> void:
	if kamera == null:
		return
	await get_tree().process_frame
	await get_tree().process_frame
	if kamera == null or not is_instance_valid(kamera) or not _hud.sheet_offen():
		return
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var unten: float = _hud.offenes_menue_hoehe()
	if _tutorial_view != null and _tutorial_view.visible:
		unten += _tutorial_view.kartenhoehe() + 16.0
	var oben: float = _hud.ziel_unterkante() + 8.0
	var welt: Vector3 = punkt + Vector3(0.0, 0.8, 0.0)
	var rand: float = Kartenmarker.hinweis("tippziel_min_px")
	var grenze_unten: float = flaeche.y - unten - rand
	var grenze_oben: float = oben + rand
	var ziel_y: float = (grenze_oben + grenze_unten) * 0.5 if grenze_unten <= grenze_oben else 0.0
	var p: Vector2 = Vector2(flaeche.x * 0.5, flaeche.y) if kamera.is_position_behind(welt) else kamera.unproject_position(welt)
	if grenze_unten > grenze_oben:
		if p.y >= grenze_oben and p.y <= grenze_unten and p.x >= rand and p.x <= flaeche.x - rand:
			return
		ziel_y = clampf(p.y, grenze_oben, grenze_unten)
	kamera.fokussiere(welt, ziel_y, 0.35, clampf(p.x, rand, flaeche.x - rand))


## Faehrt die Kamera so, dass der Punkt ueber dem geoeffneten Menue steht.
func _fokussiere_punkt(punkt: Vector3) -> void:
	if kamera == null:
		return
	await get_tree().process_frame
	await get_tree().process_frame
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var unten: float = _hud.offenes_menue_hoehe()
	# Steht die Tutorialkarte ueber dem Menue, muss die Station auch ueber IHR
	# stehen -- im ersten Geraetetest lag die Karte genau auf dem Schreibtisch.
	if _tutorial_view != null and _tutorial_view.visible:
		unten += _tutorial_view.kartenhoehe() + 16.0
	var oben: float = 170.0
	var mitte_y: float = oben + (flaeche.y - unten - oben) * 0.5
	if kamera == null or not is_instance_valid(kamera):
		return
	kamera.fokussiere(punkt + Vector3(0.0, 0.8, 0.0), mitte_y)


# --- Zoom-Stufen und Ueberblick (K3 A3) ---------------------------------------

## Die Zonen, die der Start zeigen soll: Startraum, alle gekauften Raeume und
## der naechste kaufbare. `alle` = jede Zone der Karte ("Ganze Karte").
func _zonen_im_blick(alle: bool = false) -> Array:
	var i: int = kern.welt_index
	if alle:
		return kern.welten.zonen(i)
	var zonen: Array = []
	var start: Dictionary = kern.welten.startzone(i)
	if not start.is_empty():
		zonen.append(start)
	var naechster_fehlt: bool = true
	for id in kern.bereiche.ids():
		var gekauft: bool = kern.bereiche.ist_gekauft(id)
		if not gekauft and not naechster_fehlt:
			continue
		if not gekauft:
			naechster_fehlt = false
		zonen.append_array(Menues.zonen_des_raums(kern, id))
	return zonen


## Ansicht fuer `zonen` im freien Streifen zwischen Kopf- und Menueleiste.
func _ansicht_fuer(zonen: Array) -> Dictionary:
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	return KameraSkript.ansicht_fuer(zonen, flaeche, START_OBEN, Menueleiste.HOEHE)


## Start: alle gekauften Raeume plus der naechste im Bild (Befund M6).
## Ohne Zonen (Welt ohne Grundriss) bleibt der Startblick aus worlds.json.
func _zeige_start_ansicht(dauer: float) -> void:
	if kamera == null:
		return
	# K6 §4.1.6: Startzoom je Sitzung = letzter Zoom des Spielers (gleiche Welt).
	if not _gespeicherte_kamera.is_empty() and int(_gespeicherte_kamera.get("welt", -1)) == kern.welt_index:
		kamera.zeige_ansicht(Vector3(float(_gespeicherte_kamera["x"]), 0.0, float(_gespeicherte_kamera["z"])),
			float(_gespeicherte_kamera["zoom"]), 0.0)
		return
	# Waehrend der Einfuehrung zeigt Mo auf einzelne Stationen: Dann beginnt die
	# Kamera auf der Raum-Stufe ueber dem Startraum, sonst sind die Schilder
	# (unterhalb der LOD-Grenze) gar nicht zu sehen. Der Ueberblick kommt mit
	# dem ersten Raumkauf (_zeige_zoom_hinweis).
	var im_tutorial: bool = _tutorial != null and not _tutorial.beendet
	var start: Dictionary = kern.welten.startzone(kern.welt_index)
	var zonen: Array = [start] if im_tutorial and not start.is_empty() else _zonen_im_blick()
	var ansicht: Dictionary = _ansicht_fuer(zonen)
	if ansicht.is_empty():
		return
	var z: float = float(ansicht["zoom"])
	if kamera.stufen.has(KameraSkript.RAUM):
		var raum: float = float(kamera.stufen[KameraSkript.RAUM])
		z = raum if im_tutorial else maxf(z, raum)
	kamera.zeige_ansicht(ansicht["blick"] as Vector3, z, dauer)


## Doppeltipp: auf Boden ohne Station wechselt die Stufe.
## Eine Station loest nichts aus -- der erste Tipp hat ihr Menue schon geoeffnet,
## und ein Doppeltipp darf nie etwas kaufen.
func _auf_doppeltipp(ursprung: Vector3, richtung: Vector3, boden: Vector3) -> void:
	var art: String = "nichts"
	if _treffer != null:
		art = String(_treffer.finde(ursprung, richtung)["art"])
	if art == "station" or kamera == null:
		print("tipp: doppelt auf station (nichts)")
		return
	var ziel: StringName = kamera.doppeltipp_ziel()
	print("tipp: doppelt -> %s" % ziel)
	_hud.schliesse_alle()
	if ziel == KameraSkript.RAUM:
		# Auf die Mitte der Stationen des getippten Raums, nicht auf die Tippstelle.
		var zone: Dictionary = kern.welten.zone_an(kern.welt_index, boden)
		if not zone.is_empty() and not kern.welten.stationen_in_zone(kern.welt_index, zone).is_empty():
			# Der Doppeltipp ist die bewusste Geste: Hier darf die Kamera zoomen (K6).
			_betrete_zone(zone, boden, true)
			return
	kamera.springe_stufe(ziel, kamera.unproject_position(boden))


## Nach dem ersten Raumkauf: einmal hinaus in den Ueberblick, und die Figur der
## Welt sagt, wie man zoomt (Befund M6). Gemerkt in den Einstellungen.
func _zeige_zoom_hinweis() -> void:
	_zoom_hinweis_gezeigt = true
	await get_tree().create_timer(ZOOM_HINWEIS_WARTEN).timeout
	if kamera == null or not is_instance_valid(kamera):
		return
	# Bastian 16.10.: keine automatische Kamerafahrt mehr -- er zoomt selbst. Es bleibt der Satz.
	var eintrag: Dictionary = (thema.abschnitt("tutorial") if thema != null else {}).get("zoom", {}) as Dictionary
	var text: String = String(eintrag.get("text_b", eintrag.get("text", "")))
	var von: String = String(eintrag.get("von", ""))
	if not text.is_empty() and _hud != null:
		print("hinweis: zoom")
		_hud.saft.chat(WeltTexte.absender(thema, von), text, UiStil.absender_farbe(thema, von))
	_speichere()


func _auf_station_ausgebaut(id: StringName, stufe: int) -> void:
	var ansicht: Node = _ansichten.get(id)
	if ansicht == null:
		return
	ansicht.call("setze_stufe", stufe)
	if ansicht.has_method("huepfen"):
		ansicht.call("huepfen")
	var station: StationModel = kern.kette.station(id)
	if ansicht is StationView and station != null:
		(ansicht as StationView).visible = station.freigeschaltet
	elif ansicht is AusstattungsStation and station != null:
		# Ein neuer Stern faerbt die Bodenplatte (U1-Wunsch 1).
		(ansicht as AusstattungsStation).setze_sterne(station.sterne(), station.sterne_moeglich())


func _auf_ausstattung_gekauft(station_id: StringName, platz_id: StringName, _stufe: int) -> void:
	var ansicht: AusstattungsStation = _ansichten.get(station_id) as AusstattungsStation
	var station: StationModel = kern.kette.station(station_id)
	if ansicht == null or station == null:
		return
	var p: EquipmentSlot = station.platz(platz_id)
	if p != null:
		ansicht.setze_ausstattung(platz_id, p.modellstufe(), true)
	_aktualisiere_bewohner()


## Eine Freischaltung ist der zweitwichtigste Moment nach dem Weltwechsel.
func _auf_freischaltung(unlock_id: StringName) -> void:
	if unlock_id == Ids.UNLOCK_WORLD_2:
		# Bei Welten mit Abschluss kommt vorher die Feier (_auf_welt_abgeschlossen).
		if not kern.welt_hat_abschluss():
			_biete_weltwechsel_an()
		return
	var station_id: StringName = GameCore._station_zu_freischaltung(unlock_id)
	if station_id == &"":
		return
	var ansicht: Node = _ansichten.get(station_id)
	if ansicht == null:
		return
	if ansicht is StationView:
		(ansicht as StationView).visible = true
	ansicht.call("erscheinen")
	_hud.saft.meldung(WeltTexte.station_name(thema, station_id),
		thema.station_beschreibung(station_id) if thema != null else "", "stern")


func _auf_bereich_gekauft(bereich_id: StringName) -> void:
	if _grundriss != null:
		_grundriss.aktualisiere(kern, true)
	_gleiche_stationen_an()
	_aktualisiere_bewohner()
	# Der Moment, in dem ein Raum aufgeht: die Figuren freuen sich. Kein Ruck im Bild
	# mehr -- er verschob den Blickpunkt (K6: die Kamera bewegt nur der Spieler).
	if _figur_leben != null and _bereich_positionen.has(bereich_id):
		_figur_leben.call("jubel_an", _bereich_positionen[bereich_id], 6.0)
	if not _vorspulen and _probe == null and not _zoom_hinweis_gezeigt \
			and kern.bereiche.anzahl_gekauft() == 1:
		_zeige_zoom_hinweis()


## Welt zu 100 % fertig: der Abschluss mit den Zahlen des Weges und der
## Nachricht, die alles aendert -- DANN der Weltwechsel-Bildschirm.
var _abschluss_view: AbschlussView
## Schliesst den Abschluss in der Modal-Schlange, sobald der Weltwechsel angenommen ist.
var _abschluss_fertig: Callable = Callable()


func _auf_welt_abgeschlossen() -> void:
	_audio.spiele(&"freischaltung")
	if _figur_leben != null:
		_figur_leben.call("jubel_alle")
	_hud.schliesse_alle()
	_hud.saft.muenzen(get_viewport().get_visible_rect().size * 0.5, 24)
	var texte: Dictionary = thema.abschnitt("abschluss") if thema != null else {}
	var namen: Dictionary = texte.get("zahlen", {}) as Dictionary
	var zahlen: Array = [
		[String(namen.get("spielzeit", "")), WeltTexte.dauer(kern.spielzeit)],
		[String(namen.get("verdient", "")), UiStil.zahl(kern.welt_verdient) + " €"],
		[String(namen.get("raeume", "")), "%d/%d" % [kern.bereiche.anzahl_gekauft(), kern.bereiche.anzahl()]],
		[String(namen.get("ausstattung", "")), "%d" % kern.ausstattung_stufen_gesamt()],
	]
	# Die letzte Nachricht der Welt steht im Abschluss, nicht nur im Handy.
	var letzte: Array[String] = kern.nachrichten.empfangen()
	var von: String = ""
	var nachricht: String = String(texte.get("text", ""))
	if not letzte.is_empty():
		var n: Dictionary = WeltTexte.nachricht(thema, letzte[letzte.size() - 1])
		von = WeltTexte.absender(thema, String(n.get("von", "")))
		nachricht = String(n.get("text", nachricht))
	kern.nachrichten.markiere_gelesen()
	var zeigen: Callable = func(fertig: Callable) -> void:
		var ebene := CanvasLayer.new()
		ebene.layer = 18
		add_child(ebene)
		_abschluss_view = AbschlussView.new()
		ebene.add_child(_abschluss_view)
		_abschluss_view.zeige(String(texte.get("titel", "")), zahlen, von, nachricht,
			String(texte.get("antwort", "")), UiText.t("weiter"))
		_abschluss_view.angenommen.connect(func() -> void:
			_abschluss_view = null
			ebene.queue_free()
			_biete_weltwechsel_an()
			# Das Fenster bleibt fuer die Schlange offen, bis der Weltwechsel angenommen ist --
			# sonst legte sich eine wartende Szene ueber den Wechsel-Bildschirm.
			if _wechsel_angeboten:
				_abschluss_fertig = fertig
			else:
				fertig.call())
	# K7: Ueber die Modal-Schlange -- vorher stand eine Szene, die gleichzeitig faellig war,
	# ueber dem Abschluss (zwei Fenster, zwei Textquellen). Die Durchspielprobe zeigt direkt.
	if _probe != null:
		zeigen.call(func() -> void: pass)
	else:
		ModalSchlange.global().anmelden(&"abschluss", zeigen)


## Bringt jede Station auf den Stand des Kerns: Ausstattung, Sperre, Sichtbarkeit.
func _gleiche_stationen_an() -> void:
	for id in _ansichten.keys():
		var station: StationModel = kern.kette.station(id)
		var ansicht: Node = _ansichten[id]
		if station == null:
			continue
		if ansicht is AusstattungsStation:
			var a := ansicht as AusstattungsStation
			for p in station.ausstattung:
				a.setze_ausstattung(p.id, p.modellstufe())
			a.setze_gesperrt(not station.freigeschaltet)
			a.setze_sterne(station.sterne(), station.sterne_moeglich())
		elif ansicht is StationView:
			(ansicht as StationView).setze_stufe(station.stufe)
			(ansicht as StationView).visible = station.freigeschaltet


## Limetten-Ring an jeder Station, an der ein Kauf bezahlbar ist -- ruhig. Nur die
## Station des EINEN empfohlenen Kaufs pulsiert (K4 P1.3, Kartenmarker.puls_station).
func _aktualisiere_upgrade_ringe() -> void:
	var tutorial_laeuft: bool = _tutorial != null and not _tutorial.beendet
	var puls: StringName = _hud.marker.puls_station() if _hud != null else &""
	for id in _ansichten.keys():
		var ansicht: Node = _ansichten[id]
		if not ansicht.has_method("setze_upgrade"):
			continue
		var station: StationModel = kern.kette.station(id)
		ansicht.call("setze_upgrade", not tutorial_laeuft and Menues.kauf_moeglich(kern, station), id == puls)


func _markiere_engpass(engpass_id: StringName) -> void:
	for id in _ansichten.keys():
		_ansichten[id].call("setze_engpass", id == engpass_id)
	_tutorial_melde(&"engpass_gesehen")


# --- Belohnte Werbung ------------------------------------------------------------

func _auf_belohnung(platzierung: StringName) -> void:
	match platzierung:
		&"schub":
			kern.starte_schub()
			_hud.saft.meldung(_belohnung_text("schub_titel"), _belohnung_text("schub_text"), "blitz")
		&"offline_verdoppeln":
			if _offline_erloes > 0.0:
				Hud.schreibe_gut(kern, _offline_erloes * (AdServiceStub.faktor(&"offline_verdoppeln") - 1.0))
				_offline_erloes = 0.0
	_audio.spiele(&"meilenstein")


## Nichts da ist KEIN Fehler -- der Hinweis darf sich nicht wie eine Panne anfuehlen.
func _auf_werbung_nicht_verfuegbar(_platzierung: StringName, _grund: String) -> void:
	_hud.saft.meldung(_belohnung_text("nichts_da_titel"), _belohnung_text("nichts_da_text"), "uhr")


func _belohnung_text(schluessel: String) -> String:
	if thema == null:
		return ""
	return String(thema.abschnitt("belohnung").get(schluessel, ""))


# --- Tutorial ----------------------------------------------------------------

## Meldet ein Ereignis an den Ablauf und zeichnet neu, falls es weitergegangen ist.
func _tutorial_melde(typ: StringName, wert: Variant = null) -> void:
	if _tutorial == null or _tutorial.beendet:
		return
	if _tutorial.melde(typ, wert):
		_aktualisiere_tutorial()
		_speichere()


func _auf_tutorial_uebersprungen() -> void:
	_tutorial.ueberspringen()
	_audio.spiele(&"tipp")
	_aktualisiere_tutorial()
	# Frueher fuhr die Kamera hier in die Startansicht -- Bastian zoomt selbst (16.10.).
	_speichere()


## K7: Der Spieler tippt den Randpfeil (Tutorialziel ausserhalb des Bildes) -- die Kamera
## schiebt einmal sanft dorthin, ohne Zoom. Ausgeloest vom Spieler, nur im Tutorial (K6 4.1).
func _auf_tutorial_rand_pfeil() -> void:
	if _tutorial_view == null or kamera == null:
		return
	var welt: Variant = _tutorial_view.ziel_welt()
	if welt == null:
		return
	_audio.spiele(&"tipp")
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var unten: float = _hud.offenes_menue_hoehe() + _tutorial_view.kartenhoehe() + 16.0
	var oben: float = _hud.ziel_unterkante() + 8.0
	var mitte_y: float = oben + maxf(flaeche.y - unten - oben, 0.0) * 0.5
	kamera.fokussiere((welt as Vector3) + Vector3(0.0, 0.8, 0.0), mitte_y, 0.6)


## Traegt Text und Ziel des laufenden Schritts ein. Die Texte kommen aus dem
## THEMA (Regel D3) -- hier stehen nur Schluessel.
func _aktualisiere_tutorial() -> void:
	if _tutorial_view == null:
		return
	_hud.tutorial_aktiv = _tutorial != null and not _tutorial.beendet
	if _tutorial == null or _tutorial.beendet or thema == null:
		_tutorial_view.verbergen()
		return
	var id: String = _tutorial.aktuelle_id()
	if id.is_empty():
		_tutorial_view.verbergen()
		return
	var texte: Dictionary = thema.abschnitt("tutorial")
	var eintrag: Dictionary = texte.get(id, {}) as Dictionary
	_tutorial_view.zeige(String(eintrag.get("titel", "")), _tutorial_text(id, String(eintrag.get("text", ""))),
		String(texte.get("ueberspringen", "Weiter")))
	# Nach dem ersten Ausbau schliesst das Menue von selbst: Die Kette soll frei im Bild stehen.
	if id != _tutorial_id_zuletzt and id == "kette":
		_hud.schliesse_alle()
	_tutorial_id_zuletzt = id
	_aktualisiere_tutorial_ziel()


## Setzt die Platzhalter eines Tutorialtexts ein: {plus} = Mehreinnahmen der naechsten Stufe der
## gemeinten Station, {ziel} = Text des ersten Ziels. Jede Karte sagt so, WAS der Ausbau bewirkt.
func _tutorial_text(id: String, roh: String) -> String:
	if not roh.contains("{"):
		return roh
	var text: String = roh
	if text.contains("{plus}"):
		var station: StringName = Ids.STATION_INTAKE if id == "ausbauen" else kern.kette.bottleneck()
		var mehr: float = kern.einkommen_danach(station) - kern.einkommen_pro_sekunde()
		var plus: String = UiText.t("tutorial_mehr_geld")
		if mehr > 0.0 and UiStil.zahl(mehr) != "0":
			plus = UiText.t("einnahmen_plus") % UiStil.zahl(mehr)
		text = text.replace("{plus}", plus)
	if text.contains("{ziel}"):
		text = text.replace("{ziel}", _hud.aktuelles_ziel_text())
	return text


func _aktualisiere_tutorial_ziel() -> void:
	if _tutorial_view == null or not _tutorial_view.visible or _tutorial == null or _tutorial.beendet:
		return
	_tutorial_view.setze_unten(_hud.offenes_menue_hoehe())
	_tutorial_view.setze_oben(_hud.ziel_unterkante())
	_tutorial_view.setze_kompakt(_hud.sheet_offen())
	var ziel: String = _tutorial.aktuelles_ziel()
	var eintrag: Dictionary = thema.abschnitt("tutorial").get(_tutorial.aktuelle_id(), {}) as Dictionary
	_tutorial_view.setze_text(_tutorial_text(_tutorial.aktuelle_id(), String(eintrag.get("text", ""))))
	# Die Kette: Pfeile durch die ersten drei Stationen, die langsamste rot.
	var kette_punkte: Array[Vector3] = []
	if ziel == "kette":
		for kette_id in [Ids.STATION_INTAKE, Ids.STATION_BUFFER, Ids.STATION_PROCESSING]:
			if ANZEIGE_POSITIONEN.has(kette_id):
				kette_punkte.append(ANZEIGE_POSITIONEN[kette_id] as Vector3)
	_tutorial_view.setze_kette(kette_punkte, ziel == "kette", kamera)
	var control: Control = _hud.control_fuer(ziel)
	_tutorial_view.setze_ohne_hand(ziel == "zielleiste" and not _hud.ziel_abholbar())
	_tutorial_view.setze_zusatz("")
	_tutorial_view.setze_karte_aus(false)
	# Fehlt das Geld, ist der Knopf ausgegraut: kein Ring auf einem toten Knopf,
	# stattdessen sagt die Karte, wie viel noch fehlt.
	if control is Button and (control as Button).disabled and control.has_meta("fehlt"):
		var fehlt: float = float(control.get_meta("fehlt"))
		if fehlt > 0.0:
			_tutorial_view.setze_zusatz(UiText.t("tutorial_noch") % UiStil.preis(fehlt))
			_tutorial_view.ohne_ziel()
			return
	if control != null:
		_tutorial_view.zeige_auf_control(control)
		# Zeigt die Hand auf den Hauptknopf eines offenen Panels, das denselben Gegenstand
		# schon erklaert, entfaellt die Tutorialkarte: ein Gedanke, ein Ort.
		_tutorial_view.setze_karte_aus(ziel.begins_with("bereich_") and (_hud.bereichsmenue.ist_offen() or _hud.schnellkauf.ist_offen()))
		return
	_tutorial_view.setze_karte_aus(false)
	var station_id := StringName(ziel)
	if ziel == "engpass" or ziel == "kette" or ziel == "engpass_ausbau":
		station_id = kern.kette.bottleneck()
	elif ziel == "ausstattung":
		# Noch kein Menue offen: der Ring steht an der Station mit der ersten Ausstattung.
		station_id = Ids.STATION_BUFFER
	var welt_punkt: Variant = null
	if ANZEIGE_POSITIONEN.has(station_id):
		welt_punkt = ANZEIGE_POSITIONEN[station_id]
	elif _bereich_positionen.has(StringName(ziel)):
		welt_punkt = _bereich_positionen[StringName(ziel)]
	if welt_punkt != null:
		_tutorial_view.zeige_auf_welt(welt_punkt as Vector3, kamera)
		# Keine automatische Kamerafahrt zum Tutorialziel mehr (Bastian 16.10.).
	else:
		_tutorial_view.ohne_ziel()


# --- Eroeffnung und Weltwechsel ----------------------------------------------------

## Der allererste Bildschirm -- und zwar nur der allererste. Kein Titelmenue:
## Titel, ein Satz, ein Knopf, dann der Raum.
func _zeige_eroeffnung_falls_neu() -> void:
	if kern.welt_index > 0 or kern.durchlaeufe > 0:
		return
	var schalter: PackedStringArray = _pruefschalter()
	# Das zweite return stand frueher IN der Schleife -- die Eroeffnung erschien nie.
	for ueberspringt in ["--reich", "--store", "--ohne-eroeffnung", "--tiefe", "--menue", "--durchspielen"]:
		if schalter.has(ueberspringt):
			return
	if kern.gesamt_verdient > 0.0 or kern.stufen_gesamt() > Ids.CHAIN.size():
		return
	if thema == null:
		return
	var texte: Dictionary = thema.abschnitt("eroeffnung")
	if String(texte.get("titel", "")).is_empty():
		return
	# P1.7: Auch die Eroeffnung ist ein Fenster der Schlange -- sie kommt zuerst, und
	# nichts anderes (Moment, Szene, Erklaer-Blase) legt sich daneben.
	ModalSchlange.global().anmelden(&"eroeffnung", func() -> Node: return _baue_eroeffnung(texte))


func _baue_eroeffnung(texte: Dictionary) -> Node:
	var ebene := CanvasLayer.new()
	ebene.layer = 30
	add_child(ebene)
	# Mit Chat-Zeilen in den Daten: Mo spricht als Figur-Popup (Szene), sonst die Karte.
	if not (texte.get("chat", []) as Array).is_empty():
		_eroeffnung_keyart(ebene)
		var szene: SzeneView = SzeneView.zeige_szene(ebene, SzeneView.szene_aus_eroeffnung(texte), thema, _audio)
		szene.beendet.connect(func(_index: int, _antwort: String) -> void: ebene.queue_free())
		if szene._grund != null:
			szene._grund.color.a = 0.0   # das Key-Art soll nicht grau werden
		_eroeffnung_titel(ebene, String(texte.get("titel", "")))
		return ebene
	var karte := WeltwechselView.new()
	ebene.add_child(karte)
	karte.angenommen.connect(func() -> void: ebene.queue_free())
	karte.zeige(String(texte.get("titel", "")), String(texte.get("text", "")),
		String(texte.get("knopf", "Anfangen")))
	return ebene


## Key-Art hinter der Eroeffnung (D1 C10): Vollflaeche, an den Seiten beschnitten.
func _eroeffnung_keyart(ebene: CanvasLayer) -> void:
	var pfad: String = "res://assets/ui/keyart_start.png"
	if not ResourceLoader.exists(pfad):
		return
	var bild := TextureRect.new()
	bild.texture = load(pfad) as Texture2D
	bild.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bild.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bild.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bild.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ebene.add_child(bild)


## Das Logo-Sticker im leeren oberen Drittel des Key-Arts: HELLO / WORLD gross, weiss mit
## dicker Tinte-Kontur, auf Limette und Gold, leicht schraeg, mit kurzem Pop-in.
func _eroeffnung_titel(ebene: CanvasLayer, titel: String) -> void:
	if titel.is_empty():
		return
	var woerter: PackedStringArray = titel.split(" ", false)
	var logo := Control.new()
	logo.set_anchors_preset(Control.PRESET_CENTER_TOP)
	logo.offset_left = -290.0
	logo.offset_right = 290.0
	logo.offset_top = 120.0
	logo.offset_bottom = 120.0 + 340.0
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	logo.pivot_offset = Vector2(290.0, 170.0)
	logo.rotation_degrees = -4.0
	# Hinten: eine goldene Platte, leicht gegen die Limette verdreht.
	var gold := Panel.new()
	gold.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	gold.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.GOLD, UiStil.RADIUS_KARTE + 30,
		UiStil.KONTUR + 1, 0.0, UiStil.SCHATTEN_Y_PRIMAER))
	gold.pivot_offset = Vector2(290.0, 170.0)
	gold.rotation_degrees = 5.0
	gold.mouse_filter = Control.MOUSE_FILTER_IGNORE
	logo.add_child(gold)
	var limette := Panel.new()
	limette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	limette.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.KAUFEN, UiStil.RADIUS_KARTE + 30,
		UiStil.KONTUR + 1, 0.0, UiStil.SCHATTEN_Y_PRIMAER))
	limette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	logo.add_child(limette)
	var spalte := VBoxContainer.new()
	spalte.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	spalte.alignment = BoxContainer.ALIGNMENT_CENTER
	spalte.add_theme_constant_override("separation", -UiStil.A3)
	spalte.mouse_filter = Control.MOUSE_FILTER_IGNORE
	logo.add_child(spalte)
	for wort in woerter:
		var l := UiStil.label_kontur(wort.to_upper(), UiStil.GR_HELD + 44)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		spalte.add_child(l)
	ebene.add_child(logo)
	# Pop-in: 0,6 -> 1,05 -> 1 in 0,4 s.
	logo.scale = Vector2(0.6, 0.6)
	var t := logo.create_tween()
	t.tween_property(logo, "scale", Vector2(1.05, 1.05), 0.24).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	t.tween_property(logo, "scale", Vector2.ONE, 0.16).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)


## Der Weltwechsel wird ANGEBOTEN, nicht ausgeloest.
func _biete_weltwechsel_an() -> void:
	if _wechsel_angeboten:
		return
	var abspann: bool = kern.bogen_beendet()
	if not abspann and kern.welten.ist_letzte(kern.welt_index):
		return
	_wechsel_angeboten = true
	_hud.schliesse_alle()
	var texte: Dictionary = {}
	if thema != null:
		texte = thema.abschnitt("abspann") if abspann else thema.abschnitt("weltwechsel")
	var wechsel_ebene := CanvasLayer.new()
	wechsel_ebene.layer = 20
	add_child(wechsel_ebene)
	_wechsel_view = WeltwechselView.new()
	_wechsel_view.angenommen.connect(_wechsle_welt)
	wechsel_ebene.add_child(_wechsel_view)
	var text: String = String(texte.get("text", ""))
	# Der Pflichthinweis haengt am Abspann und nur dort (Welt 6, keine Anlageberatung).
	var hinweis: String = String(texte.get("hinweis", ""))
	if abspann and not hinweis.is_empty():
		text += "\n\n" + hinweis
	_wechsel_view.zeige(String(texte.get("titel", "Weiter")), text, String(texte.get("knopf", "Weiter")))


## Wechselt tatsaechlich: erst der Kern, dann das Thema, dann das Bild -- hinter
## einer Blende, damit der wichtigste Moment nicht aussieht wie ein Schnittfehler.
func _wechsle_welt() -> void:
	if kern.bogen_beendet():
		kern.neuanfang()
	elif not kern.wechsle_welt():
		return
	_wechsel_angeboten = false
	if _abschluss_fertig.is_valid():
		var fertig: Callable = _abschluss_fertig
		_abschluss_fertig = Callable()
		# Szenen der alten Welt, die hinter dem Abschluss warteten, gehoeren nicht in die neue
		# (sie stehen im Handy).
		ModalSchlange.global().verwerfe(&"szene")
		fertig.call()
	if _wechsel_view != null:
		var ebene: Node = _wechsel_view.get_parent()
		_wechsel_view = null
		if ebene != null:
			ebene.queue_free()
	await _blende(true)
	_baue_neu()
	_audio.spiele(&"freischaltung")
	_speichere()
	await _blende(false)


func _baue_neu() -> void:
	thema = ThemeData.laden(kern.welt_id())
	_setze_kapitel()
	if _welt_wurzel != null:
		_welt_wurzel.free()
		_welt_wurzel = null
	_baue_welt()
	_hud.setze_thema(thema)
	_hud.setze_karte(kamera, ANZEIGE_POSITIONEN, _bereich_positionen)
	_hud.marker.thema = thema
	_hud.ortsblase.figur_suche = _figur_fuer_absender
	# K6 1c (Handy-Befund 1): Oeffnet der Spieler ein Stations- oder Raummenue, schiebt die
	# Kamera nur so weit, dass das Gemeinte ueber dem Panel steht -- ohne Zoom, ohne Rueckfahrt.
	_hud.station_fokus.connect(func(id: StringName) -> void:
		if ANZEIGE_POSITIONEN.has(id):
			_halte_ueber_panel(ANZEIGE_POSITIONEN[id] as Vector3))
	_hud.schnellkauf_fokus.connect(func(id: StringName) -> void:
		if _bereich_positionen.has(id):
			_halte_ueber_panel(_bereich_positionen[id] as Vector3))
	_hud.clips_zeigen_ertrag = kern.welten.figuren_roh(kern.welt_index).get("modus", "") == "wg"
	_hud.aktualisiere()
	_aktualisiere_tutorial()


## Die Kapitel der Welt (theme.json -> kapitel) gehen als neutrale Liste in den Kern.
func _setze_kapitel() -> void:
	var liste: Array = []
	if thema != null:
		var roh: Variant = thema.wert("kapitel")
		if roh is Array:
			liste = roh as Array
	kern.setze_kapitel(liste)


func _blende(nach_schwarz: bool) -> void:
	if _blende_rect == null:
		var ebene := CanvasLayer.new()
		ebene.layer = 40
		add_child(ebene)
		_blende_rect = ColorRect.new()
		_blende_rect.color = Color(UiStil.TINTE, 0.0)
		_blende_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		_blende_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ebene.add_child(_blende_rect)
	_blende_rect.visible = true
	var ablauf := create_tween()
	ablauf.tween_property(_blende_rect, "color:a", 1.0 if nach_schwarz else 0.0, BLENDE_DAUER)
	await ablauf.finished
	_blende_rect.visible = nach_schwarz


# --- Pruefschalter -------------------------------------------------------------

## Wechselt der Reihe nach durch alle Welten und meldet, was dabei passiert.
func _durchlauf_alle_welten() -> void:
	print("=== DURCHLAUF durch alle Welten ===")
	var schritte: int = 0
	while not kern.welten.ist_letzte(kern.welt_index) and schritte < 20:
		var vorher: String = kern.welt_id()
		if not kern.wechsle_welt():
			print("  ABBRUCH bei '%s'" % vorher)
			break
		schritte += 1
		_baue_neu()
		print("  %-10s -> %-10s  Stationen %d" % [vorher, kern.welt_id(), _ansichten.size()])
	print("=== %d Wechsel ohne Absturz, Endwelt '%s' ===" % [schritte, kern.welt_id()])


## Die Pruefschalter: Kommandozeile am PC, Datei auf dem Handy (nur Debug-Builds).
func _pruefschalter() -> PackedStringArray:
	var argumente: PackedStringArray = OS.get_cmdline_user_args()
	if OS.is_debug_build() and FileAccess.file_exists("user://start_args.txt"):
		var text: String = FileAccess.get_file_as_string("user://start_args.txt")
		for teil in text.strip_edges().split(" ", false):
			argumente.append(teil)
	return argumente


func _start_welt_aus_argumenten() -> int:
	var argumente: PackedStringArray = _pruefschalter()
	var index: int = argumente.find("--welt")
	if index >= 0 and index + 1 < argumente.size():
		return maxi(0, int(argumente[index + 1]) - 1)
	return 0


func _wert_nach(argumente: PackedStringArray, schalter: String, standard: String) -> String:
	var index: int = argumente.find(schalter)
	if index >= 0 and index + 1 < argumente.size():
		return argumente[index + 1]
	return standard


func _pruefe_screenshot_modus() -> void:
	var argumente: PackedStringArray = _pruefschalter()

	# Spaeter Spielstand: Kapital und ausgebaute Stationen.
	if argumente.has("--reich"):
		kern.kapital = maxf(kern.einkommen_pro_sekunde() * 3000.0, 250000.0)
		for id in Ids.CHAIN:
			var station: StationModel = kern.kette.station(id)
			if station != null:
				station.stufe = mini(14, station.max_stufe) if station.max_stufe > 0 else 14
		kern.bus.money_changed.emit(kern.kapital, 0.0)
		_markiere_engpass(kern.kette.bottleneck())

	# Ein Bereich schon gekauft, Ausstattung verteilt: `--tiefe N` kauft die
	# ersten N Raeume und je Platz N Stufen. Zum Ansehen spaeter Zustaende.
	if argumente.has("--tiefe"):
		var n: int = int(_wert_nach(argumente, "--tiefe", "2"))
		_vorspulen = true
		kern.kapital = 1.0e12
		var ids: Array[StringName] = kern.bereiche.ids()
		for i in range(mini(n, ids.size())):
			kern.kaufe_bereich(ids[i])
		for id in Ids.ALL_STATIONS:
			kern.upgrade_station_mehrfach(id, n * 8)
			var s: StationModel = kern.kette.station(id)
			if s == null:
				continue
			for p in s.ausstattung:
				for k in range(n * 2):
					kern.kaufe_ausstattung(id, p.id)
		kern.kapital = 12480.0
		kern.bus.money_changed.emit(kern.kapital, 0.0)
		_vorspulen = false
		# Gestaute Szenen des Vorspulens verwerfen (N8): Sie lagen sonst ueber
		# Menues und Vorschauen. Der Startblick zeigt die vorgespulten Raeume.
		ModalSchlange.global().verwerfe(&"szene")
		if _hud != null:
			_hud.verwerfe_vorgespultes()

	# --kapital 8.8e14: Kontostand fuer Vorschauen mit langen Zahlen (Kopfleiste, Ziele).
	if argumente.has("--kapital"):
		kern.kapital = float(_wert_nach(argumente, "--kapital", "0"))
		kern.bus.money_changed.emit(kern.kapital, 0.0)

	# `--tiefe` setzt `--store` mit (N8): Ein vorgespulter Stand mit Tutorial-Hand
	# bei Lv 41 ist kein Zustand, den ein Spieler je sieht.
	if argumente.has("--store") or (argumente.has("--tiefe") and not argumente.has("--mit-tutorial")):
		if _debug_knopf != null:
			_debug_knopf.visible = false
		if _messdaten_knopf != null:
			_messdaten_knopf.visible = false
		_tutorial.ueberspringen()
		_aktualisiere_tutorial()
		_zeige_start_ansicht(0.0)

	if argumente.has("--durchlauf"):
		_durchlauf_alle_welten()

	if argumente.has("--abschluss"):
		_auf_welt_abgeschlossen()

	if argumente.has("--wechsel"):
		if kern.welten.ist_letzte(kern.welt_index):
			kern.fortschritt.setze_frei(Ids.UNLOCK_WORLD_2)
		_biete_weltwechsel_an()

	if argumente.has("--laden") and _shop != null:
		_tutorial_view.verbergen()
		_shop.oeffnen()

	# --tutorial-schritt N: das Tutorial an Schritt N aufnehmen (zusammen mit --mit-tutorial).
	if argumente.has("--tutorial-schritt") and _tutorial != null:
		_tutorial.beendet = false
		_tutorial.schritt = int(_wert_nach(argumente, "--tutorial-schritt", "0"))
		_aktualisiere_tutorial()

	# Menues ohne Finger oeffnen: `--menue station_processing`, `--menue ziele`, ...
	if argumente.has("--menue"):
		var was: String = _wert_nach(argumente, "--menue", "")
		if not argumente.has("--mit-tutorial"):
			_tutorial.ueberspringen()
			_aktualisiere_tutorial()
		get_tree().create_timer(0.6).timeout.connect(func() -> void:
			if Ids.is_station(StringName(was)):
				_hud.zeige_station(StringName(was))
			elif was.begins_with("bereich_"):
				_hud.zeige_bereich(StringName(was))
				_fokussiere_bereich(StringName(was))
			elif was == String(Menues.START_RAUM) or was == String(kern.welten.startzone(kern.welt_index).get("id", "-")):
				# Das Panel der Startzone (`--menue start` oder mit ihrer Zonen-Id).
				_hud.zeige_bereich(Menues.START_RAUM)
				_fokussiere_bereich(Menues.START_RAUM)
			elif not WeltTexte.nebenraum(thema, StringName(was), "name").is_empty():
				# Ein Nebenraum per Zonen-Id: `--menue bad`.
				_hud.zeige_nebenraum(StringName(was))
				for eintrag in kern.welten.zonen(kern.welt_index):
					if String((eintrag as Dictionary).get("id", "")) == was:
						_betrete_zone(eintrag as Dictionary, Vector3.INF)
			elif was == "fortschritt":
				_hud._oeffne(_hud.fortschrittsmenue)
			elif was == "einstellungen":
				_hud._oeffne(_hud.einstellungsmenue)
			else:
				_hud._auf_menue(StringName(was)))

	# --standortkarte / --brett: die Standortkarte bzw. das Auftragsbrett nach dem Start oeffnen.
	if argumente.has("--standortkarte"):
		get_tree().create_timer(0.6).timeout.connect(func() -> void: _hud.oeffne_standortkarte())
	if argumente.has("--brett"):
		get_tree().create_timer(0.6).timeout.connect(func() -> void: _hud.zeige_auftragsbrett())

	if argumente.has("--durchspielen"):
		_tutorial.ueberspringen()
		_aktualisiere_tutorial()
		_probe = AbschlussSim.new(null, kern.welt_index, kern)
		_probe_start = Time.get_ticks_msec()
		_probe_welt = kern.welt_index
		_probe_welt_beginn = kern.spielzeit
		# --alle-welten: nicht nach dem ersten Wechsel aufhoeren, sondern den
		# ganzen Bogen bis zum Abspann spielen.
		_probe_alle = argumente.has("--alle-welten")
		print("=== DURCHSPIELPROBE: Welt '%s' im Zeitraffer%s ===" % [kern.welt_id(),
			" (alle Welten bis zum Abspann)" if _probe_alle else ""])

	if argumente.has("--zoom"):
		kamera.setze_welt_zoom(float(_wert_nach(argumente, "--zoom", "20")))
	# --ueberblick: sofort auf die Ueberblicks-Stufe (wie nach dem Doppeltipp).
	if argumente.has("--ueberblick"):
		kamera.springe_stufe(KameraSkript.UEBERBLICK, Vector2.INF, 0.0)
	# --schnellkauf <bereich_id|start>: der Schnellkauf eines Raums wie nach dem Tipp
	# auf seine Plakette im Ueberblick (K4 P1.1).
	if argumente.has("--schnellkauf"):
		var raum_id := StringName(_wert_nach(argumente, "--schnellkauf", "start"))
		get_tree().create_timer(0.8).timeout.connect(func() -> void: _hud.zeige_schnellkauf(raum_id))

	# --offline <sekunden>: so tun, als waere der Spieler so lange weg gewesen
	# (Standard 5400 s) und die Rueckkehr-Karte zeigen. Ohne Zahl: 90 Minuten.
	if argumente.has("--offline"):
		var abwesend: float = maxf(61.0, float(_wert_nach(argumente, "--offline", "5400")))
		var erloes: float = kern.wende_offline_an(abwesend)
		if erloes > 0.0:
			_offline_erloes = erloes
			_zeige_offline_bericht(abwesend, erloes)

	# --zoom-hinweis: der einmalige Ueberblick mit Zoom-Satz wie nach dem ersten Raumkauf.
	if argumente.has("--zoom-hinweis"):
		_zeige_zoom_hinweis()

	# Szenen und Momente per Pruefschalter (--szene, --moment, --variante).
	U3Pruefung.anwenden(self, kern, thema, _hud, _audio, argumente)

	if not argumente.has("--screenshot"):
		return
	var wartezeit: float = maxf(0.5, float(_wert_nach(argumente, "--screenshot", "3")))
	# --bild <name>: eigener Dateiname -- mehrere Vorschauen gleichzeitig
	# ueberschreiben sich sonst gegenseitig.
	_screenshot_nach(wartezeit, _wert_nach(argumente, "--bild", "vorschau"))


## Die Durchspielprobe: eine Welt im Zeitraffer bis 100 %, dann der Weltwechsel.
## Mit --alle-welten weiter durch den ganzen Bogen bis zum Abspann.
##
## Der Balance-Simulator prueft den KERN. Diese Probe prueft alles, was daran
## haengt: Ausstattungsmodelle, die erscheinen, Raeume, die sich oeffnen,
## Figuren, die kommen und gehen, Meldungen, die sich stapeln, der Abschluss,
## der Weltwechsel-Bildschirm und der Aufbau der naechsten Welt. Ein Fehler in
## dieser Kette zeigt sich sonst erst nach achtzig Minuten Spielzeit -- und nur
## einmal.
var _probe: AbschlussSim = null
var _probe_start: int = 0
var _probe_letzte_meldung: int = -1
var _probe_alle: bool = false
var _probe_welt: int = 0
var _probe_welt_beginn: float = 0.0


func _probe_schritt() -> void:
	if kern.welt_index != _probe_welt:
		print("=== DURCHSPIELPROBE: in Welt '%s' angekommen nach %.0f s Spielzeit, %.1f s echt ===" % [
			kern.welt_id(), kern.spielzeit, float(Time.get_ticks_msec() - _probe_start) / 1000.0])
		_probe_welt = kern.welt_index
		_probe_welt_beginn = kern.spielzeit
		_probe_letzte_meldung = -1
		if not _probe_alle:
			_probe_beenden("Welt %d steht, %d Stationen" % [kern.welt_index + 1, _ansichten.size()])
			return
	# Vier Sekunden Spielzeit je Bild -- mehr laesst die Uhr nicht zu.
	for i in range(16):
		kern.tick(SimClock.TICK_DAUER)
	_probe._loese_ziele_ein()
	if kern.momente.laeuft():
		kern.tippe_moment()
	var kaeufe: int = 0
	while kaeufe < 40 and _probe._kaufe_bestes():
		kaeufe += 1
	var in_welt: float = kern.spielzeit - _probe_welt_beginn
	var minute: int = int(in_welt / 600.0)
	if minute != _probe_letzte_meldung:
		_probe_letzte_meldung = minute
		print("  %-10s %3d min  %3d %%  Raeume %d/%d  Einkommen %s/s" % [kern.welt_id(), int(in_welt / 60.0),
			int(kern.weltwechsel_fortschritt() * 100.0), kern.bereiche.anzahl_gekauft(),
			kern.bereiche.anzahl(), UiStil.zahl(kern.einkommen_pro_sekunde())])
	if _abschluss_view != null and is_instance_valid(_abschluss_view):
		_abschluss_view.angenommen.emit()
	if _wechsel_view != null and is_instance_valid(_wechsel_view):
		if kern.bogen_beendet():
			_probe_beenden("Bogen durch, Abspann steht -- %d min Spielzeit gesamt" % int(kern.spielzeit / 60.0))
			return
		print("=== DURCHSPIELPROBE: Welt '%s' fertig nach %d min -- Weltwechsel wird angenommen ===" % [
			kern.welt_id(), int(in_welt / 60.0)])
		_wechsel_view.angenommen.emit()


func _probe_beenden(meldung: String) -> void:
	_probe = null
	get_tree().create_timer(3.0).timeout.connect(func() -> void:
		print("=== DURCHSPIELPROBE: %s ===" % meldung)
		_messung_ende()
		get_tree().quit())


func _screenshot_nach(sekunden: float, name: String = "vorschau") -> void:
	await get_tree().create_timer(sekunden).timeout
	await RenderingServer.frame_post_draw
	var bild: Image = get_viewport().get_texture().get_image()
	var pfad: String = "user://%s.png" % name.validate_filename()
	bild.save_png(pfad)
	print("SCREENSHOT: %s" % ProjectSettings.globalize_path(pfad))
	get_tree().quit()


# --- Spielstand --------------------------------------------------------------

var _geladener_stand: SaveData = null
var _lade_status: int = SaveManager.Ergebnis.KEIN_STAND


## Der Stand wird VOR dem Aufbau geladen: Welche Welt gebaut wird, welche Raeume
## gesperrt sind und welche Ausstattung dasteht, haengt daran. Vorher wurde erst
## die Welt gebaut und danach geladen -- die Karte haette einen Augenblick lang
## den Anfangszustand gezeigt und dann umgebaut.
func _lade_spielstand_vor_dem_aufbau() -> void:
	# Pruefschalter --frisch: so tun, als gaebe es keinen Stand. Sonst traegt
	# jede Vorschau den Stand der vorigen mit -- ein Bild mit "1,0 Bio" und
	# Willkommen-Dialog, obwohl ein Anfang angesehen werden sollte.
	if _pruefschalter().has("--frisch"):
		return
	var ergebnis: Array = _speicher.laden()
	_lade_status = ergebnis[0]
	match _lade_status:
		SaveManager.Ergebnis.KEIN_STAND:
			return
		SaveManager.Ergebnis.DEFEKT:
			push_error("Spielstand unbrauchbar -- es wird neu begonnen")
			return
	_geladener_stand = ergebnis[1]
	if _geladener_stand == null:
		return
	# Beim Pruefschalter --welt gilt die gewuenschte Welt, nicht die gespeicherte.
	if _pruefschalter().has("--welt"):
		_geladener_stand.welt_index = kern.welt_index
	kern.from_save(_geladener_stand)
	thema = ThemeData.laden(kern.welt_id())


func _nach_dem_laden() -> void:
	var stand: SaveData = _geladener_stand
	if stand == null:
		return
	_audio.setze_ton(bool(stand.einstellungen.get("ton", true)))
	_hud.einstellungsmenue.ton_an = _audio.ton_an()
	_zoom_hinweis_gezeigt = bool(stand.einstellungen.get("zoom_hinweis", false))
	_gespeicherte_kamera = stand.kamera.duplicate()
	_hud.symbol_hinweise.gesehen_setzen(stand.hinweise)
	_hud.antworten_aus_entscheidungen()
	_tutorial.apply_dict(stand.tutorial)
	if kern.fortschritt.ist_frei(Ids.UNLOCK_WORLD_2):
		_biete_weltwechsel_an()
	if _lade_status == SaveManager.Ergebnis.AUS_BACKUP:
		push_warning("Hauptdatei war defekt, Sicherung geladen")
	var abwesend: float = SimClock.abwesenheit(
		stand.letzter_zeitstempel, int(Time.get_unix_time_from_system()))
	if abwesend > 60.0:
		var erloes: float = kern.wende_offline_an(abwesend)
		if erloes > 0.0:
			_offline_erloes = erloes
			_zeige_offline_bericht(abwesend, erloes)
	_hud.aktualisiere()
	_hud.kopfleiste.zeige_sofort()
	# K6 Welle 2: Das Tagesgeschenk ist kein Fenster mehr, sondern ein Symbol am Rand.
	GeschenkView.biete_am_rand(self, kern, _hud.saft, _audio)


func _speichere() -> void:
	if kern == null or _speicher == null or _pruefschalter().has("--frisch"):
		return
	var stand: SaveData = kern.to_save()
	stand.einstellungen["ton"] = _audio.ton_an()
	stand.einstellungen["zoom_hinweis"] = _zoom_hinweis_gezeigt
	if kamera != null and is_instance_valid(kamera):
		var blick: Vector3 = kamera.blickpunkt()
		stand.kamera = {"welt": kern.welt_index, "zoom": kamera.zoom(), "x": blick.x, "z": blick.z}
	stand.tutorial = _tutorial.to_dict()
	stand.hinweise = _hud.symbol_hinweise.gesehen()
	if not _speicher.speichern(stand):
		push_error("Speichern fehlgeschlagen: %s" % _speicher.letzter_fehler)


## Der Offline-Ertrag als GESCHENK, nie als entgangener Gewinn (GAME_DESIGN 5.4).
## Die Karte selbst ist OfflineView (game/ui/offline_view.gd, Paket B): Betrag zaehlt
## hoch, die Figur der Welt spricht einen Satz. Hier wird sie nur eingehaengt.
func _zeige_offline_bericht(sekunden: float, erloes: float) -> void:
	# Ueber die Modal-Schlange: Der Bericht kommt vor Geschenk, Szene und Moment,
	# und nie zwei Fenster uebereinander (Befund M7, k3_36).
	ModalSchlange.global().anmelden(&"offline", func() -> Node:
		return _baue_offline_bericht(sekunden, erloes))


func _baue_offline_bericht(sekunden: float, erloes: float) -> Node:
	var ebene := CanvasLayer.new()
	ebene.layer = 15
	add_child(ebene)
	var ansicht: Control = (load("res://game/ui/offline_view.gd") as GDScript).new() as Control
	ebene.add_child(ansicht)
	var verdoppeln_moeglich: bool = _werbung != null and _werbung.ist_bereit(&"offline_verdoppeln")
	ansicht.call("zeige", sekunden, erloes, thema, verdoppeln_moeglich, kern.uhr.offline_obergrenze_sekunden)
	ansicht.connect("verdoppeln_gedrueckt", func() -> void:
		_werbung.zeige_belohnt(&"offline_verdoppeln"))
	ansicht.connect("weiter", func(position_knopf: Vector2) -> void:
		_hud.saft.muenzen(position_knopf, 14)
		ebene.queue_free())
	return ebene
