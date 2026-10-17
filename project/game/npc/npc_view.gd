## Ein NPC auf der Karte.
##
## WICHTIGSTE REGEL (ADR-007): NPCs erzeugen KEIN Geld. Der Kern rechnet
## deterministisch, die NPCs stellen das Ergebnis dar. Wuerde der Verdienst an
## Laufwegen haengen, waere korrekter Offline-Ertrag unmoeglich -- man kann
## acht Stunden Laufwege nicht nachsimulieren.
##
## Zustandsautomat statt Verhaltensbaum: Bei fuenf Zustaenden ist alles andere
## Ueberbau. Bewegung per Interpolation, ohne Physik und ohne Kollisionsabfragen.
class_name NpcView
extends Node3D

enum Zustand {
	FREI,        ## im Pool, unsichtbar
	ANKOMMEN,    ## laeuft zur Warteschlange
	WARTEN,      ## steht in der Schlange -- DAS ist das Engpass-Signal
	ABGEFERTIGT, ## wird gerade bedient
	GEHEN,       ## laeuft zum Ausgang
	VORBEI,      ## schaut kurz zu und geht wieder -- siehe schau_vorbei()
}

const TEMPO: float = 2.6
const ANKUNFTS_TOLERANZ: float = 0.12

## Gehzyklus ohne Skelett und ohne Animationsdaten.
##
## Die Figur wippt beim Laufen leicht auf und ab und neigt sich minimal in
## Laufrichtung. Das sind zwei Zeilen Mathematik statt eines Rigs mit
## Keyframes -- und der Unterschied zwischen "gleitet" und "geht" ist
## trotzdem sofort sichtbar.
##
## Bei 24 Figuren waere ein echter Skelett-Zyklus auf der Zielhardware
## spuerbar teurer und haette denselben Zweck erfuellt.
const WIPPEN_HOEHE: float = 0.055
const WIPPEN_TEMPO: float = 9.0
const NEIGUNG: float = 0.09

## Die Archetypen aus der Blender-Pipeline (art_source/scripts/build_npcs.py).
##
## Die Namen beschreiben die SILHOUETTE, nicht eine Rolle -- dieselbe gebeugte
## Figur ist in einer Welt ein alter Mensch mit Karton, in einer anderen ein
## Bote mit Paket. Waeren sie nach Rollen benannt, haetten die Dateinamen das
## Thema in den Code getragen (ADR-010).
##
## Auf 40 Pixel Hoehe ist der Umriss das Einzige, was ankommt
## (ART_DIRECTION R1) -- eine andere Jackenfarbe erkennt dort niemand mehr.
##
## Alle sieben zusammen wiegen 96 KB und entstanden in 6,4 Sekunden.
const ARCHETYPEN: Array[PackedScene] = [
	preload("res://assets/characters/npc_standard.glb"),
	preload("res://assets/characters/npc_gebeugt.glb"),
	preload("res://assets/characters/npc_schritt.glb"),
	preload("res://assets/characters/npc_kapuze.glb"),
	preload("res://assets/characters/npc_breit.glb"),
	preload("res://assets/characters/npc_rucksack.glb"),
	preload("res://assets/characters/npc_traeger.glb"),
]

## Wie oft der jeweilige Archetyp erscheint.
##
## Der Standard dominiert bewusst: Waeren alle gleich haeufig, wuerde die
## Besonderheit der Sonderfiguren verpuffen. Die Traeger-Silhouette fehlt hier --
## sie erscheint nicht zufaellig, sondern nur zum Grossauftrag (STORY.md 5).
const HAEUFIGKEIT: Array[int] = [0, 0, 0, 0, 1, 2, 3, 4, 5]

## Kleidungsfarben der Varianten. Entsaettigte Toene aus der Palette --
## die Figuren sollen die Karte beleben, aber nie mit dem Engpass-Rot
## konkurrieren (ART_DIRECTION R3: Saettigung ist fuer Bedeutung reserviert).
const KLEIDUNG_VARIANTEN: Array[Color] = [
	Color("454c5c"),   # Grund mittel
	Color("5a6274"),
	Color("6b6357"),
	Color("4a5568"),
	Color("6e6a78"),
	Color("57604f"),
]

const FARBE_UNGEDULDIG := Color("e0603d") ## Warnung
const GEDULD_SEKUNDEN: float = 12.0

var zustand: int = Zustand.FREI
var _verweilrest: float = 0.0
var _ausgang_merker: Vector3 = Vector3.ZERO
var _ziel: Vector3 = Vector3.ZERO
var _wartezeit: float = 0.0
var _modell: Node3D
var _flaechen: Array[MeshInstance3D] = []
var _material: StandardMaterial3D
var _grundfarbe: Color = Color.WHITE
var _schrittphase: float = 0.0
var _bei_abgang: Callable


func _ready() -> void:
	# Kleidungsfarbe der Variante -- pro Figur einmal gezogen
	_grundfarbe = KLEIDUNG_VARIANTEN[randi() % KLEIDUNG_VARIANTEN.size()]
	_material = StandardMaterial3D.new()
	_material.albedo_color = _grundfarbe
	_material.roughness = 1.0
	_material.metallic = 0.0

	# Archetyp nach Haeufigkeit ziehen
	var index: int = HAEUFIGKEIT[randi() % HAEUFIGKEIT.size()]
	_modell = ARCHETYPEN[index].instantiate()
	add_child(_modell)
	_sammle_flaechen(_modell)
	_setze_kleidungsfarbe(_grundfarbe)
	visible = false


## Holt den NPC aus dem Pool und schickt ihn los.
func aktiviere(start: Vector3, ziel: Vector3, bei_abgang: Callable) -> void:
	position = start
	_ziel = ziel
	_wartezeit = 0.0
	_bei_abgang = bei_abgang
	zustand = Zustand.ANKOMMEN
	_setze_kleidungsfarbe(_grundfarbe)
	visible = true


func gib_frei() -> void:
	zustand = Zustand.FREI
	visible = false


## Weist der Figur einen neuen Platz in der Schlange zu (jemand vor ihr ging).
func ruecke_auf(neues_ziel: Vector3) -> void:
	_ziel = neues_ziel
	if zustand == Zustand.WARTEN:
		zustand = Zustand.ANKOMMEN


## Wird bedient und verlaesst danach die Karte.
func fertige_ab(ausgang: Vector3) -> void:
	zustand = Zustand.GEHEN
	_ziel = ausgang


## Die Figur kommt herein, schaut kurz zu und geht wieder.
##
## Das ist der Normalfall in einer Welt, in der man Reichweite hat und sonst
## nichts: Die meisten, die vorbeikommen, bleiben nicht. Sie stellen sich in
## keine Schlange, sie hinterlassen nichts, und trotzdem sind sie da.
##
## Ohne sie waere ein Raum, in dem gerade niemand wartet, komplett leer -- und
## "niemand da" ist etwas anderes als "viele da, aber keiner bleibt". Der
## Unterschied ist die halbe Aussage der ersten Welt.
##
## WICHTIG (ADR-007): Auch diese Figuren erzeugen KEIN Geld. Der Kern rechnet,
## sie stellen dar.
func schau_vorbei(blickpunkt: Vector3, dauer: float, ausgang: Vector3) -> void:
	zustand = Zustand.VORBEI
	_ziel = blickpunkt
	_verweilrest = dauer
	_ausgang_merker = ausgang


func _process(delta: float) -> void:
	match zustand:
		Zustand.ANKOMMEN:
			if _bewege_dich(delta):
				zustand = Zustand.WARTEN
		Zustand.WARTEN:
			_wartezeit += delta
			# Ungeduld sichtbar machen: Wer lange steht, faerbt sich ein.
			# Das verstaerkt das Engpass-Signal, ohne ein Wort Text.
			if _wartezeit > GEDULD_SEKUNDEN:
				var anteil: float = clampf((_wartezeit - GEDULD_SEKUNDEN) / GEDULD_SEKUNDEN, 0.0, 1.0)
				_setze_kleidungsfarbe(_grundfarbe.lerp(FARBE_UNGEDULDIG, anteil))
		Zustand.VORBEI:
			# Erst hinlaufen, dann stehen bleiben, dann gehen. Das Stehen ist
			# der Teil, der zaehlt: Eine Figur, die ohne Pause durchlaeuft,
			# liest sich als Passant. Eine, die kurz stehen bleibt, liest
			# sich als jemand, der hingesehen hat.
			if _bewege_dich(delta):
				_verweilrest -= delta
				if _verweilrest <= 0.0:
					zustand = Zustand.GEHEN
					_ziel = _ausgang_merker
		Zustand.GEHEN:
			if _bewege_dich(delta):
				if _bei_abgang.is_valid():
					_bei_abgang.call(self)
				gib_frei()
		_:
			pass


## Bewegt die Figur Richtung Ziel. Gibt true zurueck, sobald sie da ist.
func _bewege_dich(delta: float) -> bool:
	var richtung: Vector3 = _ziel - position
	richtung.y = 0.0
	var distanz: float = richtung.length()
	if distanz <= ANKUNFTS_TOLERANZ:
		_beende_gehen()
		return true

	var schritt: Vector3 = richtung.normalized()
	position += schritt * minf(TEMPO * delta, distanz)

	# In Laufrichtung drehen -- eine Figur, die seitwaerts laeuft, wirkt kaputt
	if _modell != null:
		var ziel_drehung: float = atan2(schritt.x, schritt.z)
		_modell.rotation.y = lerp_angle(_modell.rotation.y, ziel_drehung, delta * 9.0)

		# Wippen und leichte Vorlage
		_schrittphase += delta * WIPPEN_TEMPO
		_modell.position.y = absf(sin(_schrittphase)) * WIPPEN_HOEHE
		_modell.rotation.x = NEIGUNG * 0.35
	return false


## Zurueck in die Ruhehaltung -- ohne das bliebe die Figur schief stehen.
func _beende_gehen() -> void:
	if _modell != null:
		_modell.position.y = 0.0
		_modell.rotation.x = 0.0
	_schrittphase = 0.0


## Sammelt alle Mesh-Flaechen des Modells ein.
## Godot laedt ein glTF als Baum aus Node3D und MeshInstance3D -- die Teile
## liegen also nicht flach nebeneinander, sondern verschachtelt.
func _sammle_flaechen(knoten: Node) -> void:
	if knoten is MeshInstance3D:
		_flaechen.append(knoten as MeshInstance3D)
	for kind in knoten.get_children():
		_sammle_flaechen(kind)


## Faerbt die Kleidungsteile ein und laesst Kopf und Tasche unberuehrt.
## Die Unterscheidung laeuft ueber die Teilenamen aus dem Blender-Skript --
## deshalb sind die Module dort einzeln benannt und nicht verschmolzen.
func _setze_kleidungsfarbe(farbe: Color) -> void:
	_material.albedo_color = farbe
	for flaeche in _flaechen:
		var name: String = flaeche.name.to_lower()
		if name.begins_with("kopf") or name.begins_with("tasche"):
			continue
		flaeche.material_override = _material
