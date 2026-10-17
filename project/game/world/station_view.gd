## Die sichtbare Darstellung einer Station.
##
## Drei Ausbaustufen, die AUFEINANDER AUFBAUEN (ART_DIRECTION R4): Stufe 2
## zeigt alles von Stufe 1 plus das neue Teil. Der Spieler sieht dadurch
## nicht "etwas anderes", sondern "mehr als vorher" -- Fortschritt statt
## Austausch.
##
## Die Modelle kommen aus art_source/scripts/build_stations.py und heissen
## nach ihrer FUNKTION, nicht nach dem Gegenstand (ADR-010): Dieselbe ID ist
## in Welt 1 eine Wartebank und in Welt 2 ein Posteingang.
class_name StationView
extends Node3D

## Ab welcher Stufe die naechste Ausbaustufe sichtbar wird.
const STUFEN_SCHWELLEN: Array[int] = [1, 6, 12]

## Farben aus der Palette (ART_DIRECTION.md 3)
const FARBE_SOCKEL := Color("363c4b")
## Gedaempftes Warnrot: Der Sockel soll den Engpass melden, nicht das Bild
## beherrschen. Auf dem Geraet war a8452c immer noch ein leuchtender
## Klotz mitten im Raum -- der PC-Monitor hatte das verharmlost.
## uebernehmen. Die volle Signalfarbe bleibt der UI vorbehalten.
const FARBE_ENGPASS := Color("6e3326")
const FARBE_AUSWAHL := Color("f2a93b")   ## Aktion

var station_id: StringName
var _stufe: int = 0
var _ist_engpass: bool = false
## Ersatzwelt fuer noch nicht gebaute Stationsmodelle -- siehe _modellpfad.
const ERSATZWELT: String = "amt"

var _theme_ordner: String = "amt"

var _sockel: MeshInstance3D
var _sockel_material: StandardMaterial3D
var _modelle: Array[Node3D] = []      ## Index 0..2, jeweils eine Ausbaustufe


func aufbauen(id: StringName, position_welt: Vector3, theme_ordner: String = "amt") -> void:
	station_id = id
	position = position_welt
	_theme_ordner = theme_ordner

	# Sockel -- markiert den Standort und traegt die Engpass-Farbe.
	#
	# Die Engpass-Markierung sitzt bewusst NUR hier und nicht auf dem ganzen
	# Objekt: Sobald die Station echte Gegenstaende zeigt, wuerde eine
	# durchgehende Einfaerbung alle Details plattmachen. Ein farbiger Boden
	# ist genauso deutlich und laesst die Szene intakt.
	_sockel_material = StandardMaterial3D.new()
	_sockel_material.albedo_color = FARBE_SOCKEL
	_sockel_material.roughness = 1.0
	_sockel_material.metallic = 0.0

	_sockel = MeshInstance3D.new()
	var platte := BoxMesh.new()
	# Bewusst knapp bemessen: Ein grosser Sockel erschlaegt die Gegenstaende,
	# die darauf stehen -- im ersten Geraete-Screenshot war die rote Platte
	# das dominanteste Element der ganzen Szene.
	platte.size = Vector3(1.9, 0.07, 1.9)
	_sockel.mesh = platte
	_sockel.material_override = _sockel_material
	# Leicht ANGEHOBEN. Boden und Sockel lagen beide auf y = 0 und stritten
	# sich um dieselben Pixel -- im Vorschaubild als flackernde rote Linien
	# quer durch den Raum sichtbar (Z-Fighting).
	_sockel.position = Vector3(0.0, 0.055, 0.0)
	add_child(_sockel)

	# Die drei Ausbaustufen laden und alle ausblenden
	for i in range(STUFEN_SCHWELLEN.size()):
		var pfad: String = _modellpfad(String(station_id), i + 1)
		if pfad.is_empty():
			_modelle.append(null)
			continue
		var szene: PackedScene = load(pfad) as PackedScene
		var knoten: Node3D = szene.instantiate()
		knoten.visible = false
		add_child(knoten)
		_modelle.append(knoten)

	# Trefferflaeche fuer die Auswahl -- bewusst grosszuegiger als die
	# sichtbare Geometrie, damit ein Tippen auch daneben trifft.
	var koerper := StaticBody3D.new()
	var form := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2.6, 2.4, 2.6)
	form.shape = box
	form.position = Vector3(0.0, 1.2, 0.0)
	koerper.add_child(form)
	add_child(koerper)


## Findet das Modell einer Ausbaustufe -- notfalls aus der Ersatzwelt.
##
## BAUGERUEST, kein Dauerzustand: Solange eine Welt ihre eigenen Stationen
## noch nicht hat, laufen die Modelle der ersten fertig gebauten Welt. Das ist
## bewusst so gewaehlt, weil die Alternative schlechter ist: Ohne Ersatz stuende
## in einer neuen Welt nur der nackte Sockel, und jeder Screenshot waere
## unbrauchbar -- man koennte Raum, Kamera, Beleuchtung und Balance einer neuen
## Welt nicht beurteilen, bevor die letzte Requisite fertig ist.
##
## Die Warnung ist deshalb wichtig: Sie verhindert, dass ein Baugeruest
## unbemerkt zur Auslieferung wird.
func _modellpfad(station: String, stufe: int) -> String:
	var pfad: String = "res://assets/stations/%s/%s_%d.glb" % [_theme_ordner, station, stufe]
	if ResourceLoader.exists(pfad):
		return pfad
	var ersatz: String = "res://assets/stations/%s/%s_%d.glb" % [ERSATZWELT, station, stufe]
	if ResourceLoader.exists(ersatz):
		push_warning("Welt '%s' hat kein Modell fuer %s Stufe %d -- es laeuft '%s'"
			% [_theme_ordner, station, stufe, ERSATZWELT])
		return ersatz
	push_warning("Stationsmodell fehlt ganz: %s" % pfad)
	return ""


## Setzt die Ausbaustufe und blendet das passende Modell ein.
func setze_stufe(stufe: int) -> void:
	_stufe = stufe
	var aktiv: int = -1
	for i in range(STUFEN_SCHWELLEN.size()):
		if stufe >= STUFEN_SCHWELLEN[i]:
			aktiv = i
	for i in range(_modelle.size()):
		if _modelle[i] != null:
			_modelle[i].visible = (i == aktiv)


## Markiert diese Station als aktuellen Engpass.
## Das wichtigste visuelle Signal des Spiels (GAME_DESIGN.md 4).
func setze_engpass(ist_engpass: bool) -> void:
	_ist_engpass = ist_engpass
	_aktualisiere_sockel()


func _aktualisiere_sockel() -> void:
	_sockel_material.albedo_color = FARBE_ENGPASS if _ist_engpass else FARBE_SOCKEL


## Auftritt bei der Freischaltung: Die Station waechst kurz aus dem Boden.
##
## Kein Konfetti und kein Blitz -- das Spiel ist ein Amt, kein Jahrmarkt.
## Eine ruhige Bewegung reicht, um den Blick dorthin zu ziehen.
func erscheinen() -> void:
	scale = Vector3(0.6, 0.05, 0.6)
	modulate_kinder(0.0)
	var ablauf := create_tween()
	ablauf.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	ablauf.tween_property(self, "scale", Vector3.ONE, 0.55)
	ablauf.parallel().tween_method(modulate_kinder, 0.0, 1.0, 0.45)


## Setzt die Sichtbarkeit aller Modellteile weich -- Node3D kennt kein
## modulate, deshalb ueber die Materialtransparenz der Sockelplatte
## und das Ein-/Ausblenden der Modelle.
func modulate_kinder(wert: float) -> void:
	if _sockel_material != null:
		var farbe: Color = _sockel_material.albedo_color
		farbe.a = clampf(wert, 0.0, 1.0)
		_sockel_material.albedo_color = farbe


## Kurze Rueckmeldung beim Antippen -- unter 100 ms, sonst fuehlt es sich
## kaputt an (ART_DIRECTION.md 6).
func blitzen() -> void:
	_sockel_material.albedo_color = FARBE_AUSWAHL
	var zeitgeber := get_tree().create_timer(0.12)
	await zeitgeber.timeout
	if is_instance_valid(self):
		_aktualisiere_sockel()



# --- Namensschild der Mitarbeiter-Figur (K6 2a) --------------------------------

## Baut das Schild: ein Sticker-Pop-Feld (Name, darunter der Rangtitel), einmal in einen
## SubViewport gezeichnet und als Sprite zur Kamera gedreht. `werte` = lebendig.json crew.schild.
## Der Knoten liegt im Ursprung; der Aufrufer setzt ihn ueber den Kopf der Figur.
static func baue_namensschild(name_text: String, titel_text: String, akzent: Color, werte: Dictionary) -> Node3D:
	var wurzel := Node3D.new()
	wurzel.name = "Namensschild"
	var gr_name: int = int(werte.get("name_groesse", 60))
	var gr_titel: int = int(werte.get("titel_groesse", 34))
	var polster: int = int(werte.get("polster", 14))
	var kontur: int = int(werte.get("kontur", 5))
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStil.sticker(UiStil.PAPIER, 26, kontur, float(polster), 0.0))
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", -4)
	panel.add_child(spalte)
	var zeile_name: Label = UiStil.label(name_text, gr_name, UiStil.TINTE, UiStil.FETT)
	zeile_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	spalte.add_child(zeile_name)
	if not titel_text.is_empty():
		var zeile_titel: Label = UiStil.label(titel_text, gr_titel, akzent, UiStil.TEXT_GEWICHT)
		zeile_titel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		spalte.add_child(zeile_titel)
	# Groesse aus den Schriftmassen (Container melden ausserhalb des Baums keine Mindestgroesse).
	var f_name: Font = zeile_name.get_theme_font("font")
	var breite: float = f_name.get_string_size(name_text, HORIZONTAL_ALIGNMENT_LEFT, -1, gr_name).x
	var hoehe: float = f_name.get_height(gr_name) - 4.0
	if not titel_text.is_empty():
		var f_titel: Font = spalte.get_child(1).get_theme_font("font")
		breite = maxf(breite, f_titel.get_string_size(titel_text, HORIZONTAL_ALIGNMENT_LEFT, -1, gr_titel).x)
		hoehe += f_titel.get_height(gr_titel)
	var rand: float = float(polster + kontur) * 2.0
	var groesse := Vector2(ceilf(breite + rand + 4.0), ceilf(hoehe + rand))
	panel.custom_minimum_size = groesse
	panel.size = groesse
	var ansicht := SubViewport.new()
	ansicht.size = Vector2i(ceili(groesse.x), ceili(groesse.y))
	ansicht.transparent_bg = true
	ansicht.disable_3d = true
	ansicht.render_target_update_mode = SubViewport.UPDATE_ONCE
	ansicht.add_child(panel)
	wurzel.add_child(ansicht)
	var sprite := Sprite3D.new()
	sprite.texture = ansicht.get_texture()
	sprite.pixel_size = float(werte.get("pixel", 0.0042))
	sprite.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	sprite.offset = Vector2(0.0, groesse.y * 0.5)   # Unterkante am Aufhaengepunkt
	sprite.no_depth_test = true
	sprite.shaded = false
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	sprite.render_priority = 5
	wurzel.add_child(sprite)
	return wurzel
