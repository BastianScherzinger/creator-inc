## Orthographische Isometrie-Kamera mit Touch-Steuerung (ADR-021, WELT1_TIEFE 9).
##
## - Ein Finger zieht die Karte, und der Punkt unter dem Finger BLEIBT unter dem
##   Finger -- gerechnet ueber Strahlen auf den Boden, nicht ueber eine
##   geschaetzte Umrechnung
## - Zwei Finger zoomen um den Punkt zwischen den Fingern
## - Nach dem Loslassen gleitet die Karte aus
## - Grenzen und Zoombereich kommen je Welt aus den Daten, mit weichem Rand
## - Eine Fokusfahrt bringt eine Station ueber das geoeffnete Menue
## - Tippen und Ziehen werden ueber Schwellwerte unterschieden
## - K3 A3: zwei Stufen `raum` / `ueberblick` (worlds.json -> karte.zoom_stufen).
## - K6 (Bastian 16.10.): Der Spieler bestimmt den Zoom. Pinch, Mausrad und Trackpad
##   zoomen frei zwischen zoom_min und zoom_max und bleiben, wo sie losgelassen
##   werden -- kein Einrasten. Nur der Doppeltipp (bewusste Geste) faehrt auf die
##   andere Stufe. Welche Stufe gilt, folgt aus dem AKTUELLEN Zoom und einer
##   Schwelle (`schwelle`, dieselbe wie die Plaketten: hinweise.json
##   lod_grenze_zoom), nicht aus dem letzten Einrasten.
extends Camera3D

## Ein Tipp: der Strahl der Kamera (Ursprung, Richtung) und der Bodenpunkt (y = 0).
## main.gd prueft den Strahl gegen Stations- und Raumboxen (TrefferKarte); der
## Bodenpunkt ist nur der Rueckfall -- er liegt bei allem, was hoeher als der
## Boden ist, daneben (RELEASE_PLAN 2.A).
signal welt_getippt(ursprung: Vector3, richtung: Vector3, bodenpunkt: Vector3)
## Zweiter Tipp kurz nach dem ersten an fast derselben Stelle.
## Kommt STATT `welt_getippt` -- der zweite Tipp loest nie einen Kauf oder ein Menue aus.
signal doppelt_getippt(ursprung: Vector3, richtung: Vector3, bodenpunkt: Vector3)
## Die Kamera faehrt auf eine Stufe (Doppeltipp, springe_stufe).
signal stufe_gewechselt(stufe: StringName)
## Eine Zwei-Finger-Geste (oder Trackpad) hat den Zoom veraendert.
signal gezoomt

const TAP_MAX_DISTANZ: float = 18.0     ## Pixel
const REIBUNG: float = 5.0
const ABSTAND: float = 40.0
const DOPPEL_ZEIT_MS: int = 350           ## zweiter Tipp innerhalb dieser Zeit
const DOPPEL_ABSTAND: float = 60.0        ## ... und hoechstens so weit weg (Pixel)
const RAST_DAUER: float = 0.3

## Isometrie (Blick entlang (-1,-1,-1)): Bodenstrecke (x + z) erscheint mit
## 1/sqrt6 senkrecht im Bild, eine senkrechte Kante mit sqrt(2/3).
const V_FAKTOR: float = 0.40824829
const W_FAKTOR: float = 0.81649658

const RAUM: StringName = &"raum"
const UEBERBLICK: StringName = &"ueberblick"

var zoom_min: float = 8.0
var zoom_max: float = 44.0

## Stufen fuer den Doppeltipp: Name -> Zoom. Leer = keine Stufen.
var stufen: Dictionary = {}
## Ab diesem Zoom (groesser = weiter weg) gilt der Ueberblick. Eine Quelle mit den
## Plaketten (Kartenmarker.ist_ueberblick): hinweise.json lod_grenze_zoom.
var schwelle: float = Kartenmarker.hinweis("lod_grenze_zoom")
## Blickpunkt der Ueberblicks-Stufe (Mitte der ganzen Karte im freien Streifen). Gesetzt
## von main.gd aus den Zonen; unendlich = keiner, dann bleibt der Punkt unter dem Finger.
var ueberblick_blick: Vector3 = Vector3.INF

## Rechteck in Weltkoordinaten (x, z), in dem der Blickpunkt bleiben darf.
var grenzen: Rect2 = Rect2(-6.0, -6.0, 12.0, 12.0)

var _ziel: Vector3 = Vector3(0.6, 0.0, 0.6)
var _schwung: Vector3 = Vector3.ZERO
var _zoom: float = 30.0

var _beruehrungen: Dictionary = {}      ## index -> Vector2
var _druck_start: Vector2 = Vector2.ZERO
var _gezogen: bool = false
var _pinch_abstand: float = 0.0
var _letzte_bewegung: float = 0.0
var _fahrt: Tween
var _ruck: Vector3 = Vector3.ZERO        ## kurzer Versatz des Blicks (Raumkauf)
var _ruck_tween: Tween
var _letzter_tipp_ms: int = -100000
var _letzter_tipp_ort: Vector2 = Vector2(-9999.0, -9999.0)
var _hat_gepincht: bool = false
var _zoom_beim_tipp: float = -1.0          ## Zoom VOR dem ersten Tipp eines Doppeltipps
## Ein Doppeltipp wurde gemeldet und seine Fahrt (betrete/springe_stufe) steht noch aus.
## Nur dann darf `betrete` den Zoom aendern (K6). Jede neue Beruehrung loescht ihn.
var _doppeltipp_offen: bool = false
## Ansicht vor der Raumfahrt (Blickpunkt + Zoom): Dorthin faehrt "Zurueck".
## Leer, solange man in der Uebersicht steht oder selbst weitergewischt hat.
var _rueckkehr: Dictionary = {}


func _ready() -> void:
	projection = PROJECTION_ORTHOGONAL
	size = _zoom
	far = 200.0
	_aktualisiere_position()


func setze_welt_zoom(wert: float) -> void:
	_zoom = clampf(wert, zoom_min, zoom_max)
	size = _zoom
	_aktualisiere_position()


func setze_grenzen(rechteck: Rect2, min_zoom: float, max_zoom: float) -> void:
	grenzen = rechteck
	zoom_min = min_zoom
	zoom_max = max_zoom
	_zoom = clampf(_zoom, zoom_min, zoom_max)
	size = _zoom
	_begrenze_ziel(true)
	_aktualisiere_position()


func setze_blickpunkt(punkt: Vector3) -> void:
	_ziel = Vector3(punkt.x, 0.0, punkt.z)
	_schwung = Vector3.ZERO
	_begrenze_ziel(true)
	_aktualisiere_position()


func blickpunkt() -> Vector3:
	return _ziel


func zoom() -> float:
	return _zoom


## Raststufen setzen (aus worlds.json -> karte.zoom_stufen). Werte ausserhalb
## des Zoombereichs werden in ihn geklemmt.
func setze_stufen(raum: float, ueberblick: float) -> void:
	stufen = {RAUM: clampf(raum, zoom_min, zoom_max), UEBERBLICK: clampf(ueberblick, zoom_min, zoom_max)}


## Die Stufe, die dem Zoom `wert` am naechsten liegt -- im Verhaeltnis gemessen
## (12 -> 18 ist so weit wie 18 -> 27). Ohne Stufen: &"".
static func naechste_stufe(wert: float, stufen_werte: Dictionary) -> StringName:
	var beste: StringName = &""
	var bester_abstand: float = INF
	for name in stufen_werte:
		var z: float = float(stufen_werte[name])
		var abstand: float = absf(log(maxf(wert, 0.01) / maxf(z, 0.01)))
		if abstand < bester_abstand:
			bester_abstand = abstand
			beste = StringName(name)
	return beste


## Stufe zu einem Zoom: ueber der Schwelle Ueberblick, sonst Raum. Rein, testbar.
static func stufe_fuer(wert: float, schwelle_zoom: float) -> StringName:
	return UEBERBLICK if wert > schwelle_zoom else RAUM


## Auf welcher Stufe die Kamera gerade steht -- aus dem aktuellen Zoom.
func stufe() -> StringName:
	return stufe_fuer(_zoom, schwelle)


## Die jeweils andere Stufe (Doppeltipp).
func andere_stufe() -> StringName:
	return UEBERBLICK if stufe() == RAUM else RAUM


## Ziel eines Doppeltipps: die andere Stufe als die, auf der man VOR dem ersten
## Tipp stand -- der erste Tipp kann schon eine Raumfahrt gestartet haben.
func doppeltipp_ziel() -> StringName:
	var vorher: float = _zoom_beim_tipp if _zoom_beim_tipp > 0.0 else _zoom
	return UEBERBLICK if stufe_fuer(vorher, schwelle) == RAUM else RAUM


## Weich auf eine Stufe zoomen. `um` = Bildschirmpunkt, der stehen bleibt
## (Vector2.INF = Bildmitte, der Blickpunkt bleibt).
func springe_stufe(name: StringName, um: Vector2 = Vector2.INF, dauer: float = RAST_DAUER) -> void:
	if not stufen.has(name):
		return
	_rueckkehr.clear()
	_doppeltipp_offen = false
	var ziel_zoom: float = float(stufen[name])
	var ende: Vector3 = _ziel
	if name == UEBERBLICK and ueberblick_blick.is_finite():
		# Der Ueberblick zeigt die ganze Karte, nicht den Ausschnitt um die Tippstelle.
		ende = _begrenzt(Vector3(ueberblick_blick.x, 0.0, ueberblick_blick.z))
	elif um.is_finite():
		# Mit dem Ziel-Zoom rechnen: Welcher Bodenpunkt liegt dann unter `um`?
		var vorher: Variant = _boden(um)
		var alt_size: float = size
		size = ziel_zoom
		var nachher: Variant = _boden(um)
		size = alt_size
		if vorher != null and nachher != null:
			var d: Vector3 = (vorher as Vector3) - (nachher as Vector3)
			d.y = 0.0
			ende = _begrenzt(_ziel + d)
	_fahre_nach(ende, ziel_zoom, dauer)
	stufe_gewechselt.emit(name)


func _process(delta: float) -> void:
	if not _beruehrungen.is_empty():
		return
	var bewegt: bool = false
	if _schwung.length() > 0.01:
		_ziel += _schwung * delta
		_schwung = _schwung.lerp(Vector3.ZERO, clampf(delta * REIBUNG, 0.0, 1.0))
		bewegt = true
	# Weicher Rand: Wer ueber die Grenze hinaus zieht, wird sanft zurueckgeholt
	# statt hart gestoppt. Eine harte Wand fuehlt sich an wie ein Fehler.
	var begrenzt: Vector3 = _begrenzt(_ziel)
	if not begrenzt.is_equal_approx(_ziel):
		_ziel = _ziel.lerp(begrenzt, clampf(delta * 8.0, 0.0, 1.0))
		_schwung *= 0.5
		bewegt = true
	if bewegt:
		_aktualisiere_position()


## Jede neue Beruehrung -- auch auf einem Knopf oder Panel -- beendet das Recht des
## letzten Doppeltipps auf eine Zoomfahrt (_doppeltipp_offen).
func _input(ereignis: InputEvent) -> void:
	if (ereignis is InputEventScreenTouch or ereignis is InputEventMouseButton) and ereignis.is_pressed():
		_doppeltipp_offen = false


func _unhandled_input(ereignis: InputEvent) -> void:
	if ereignis is InputEventScreenTouch:
		_behandle_beruehrung(ereignis as InputEventScreenTouch)
	elif ereignis is InputEventScreenDrag:
		_behandle_ziehen(ereignis as InputEventScreenDrag)
	elif ereignis is InputEventMouseButton:
		var maus := ereignis as InputEventMouseButton
		if maus.pressed and (maus.button_index == MOUSE_BUTTON_WHEEL_UP or maus.button_index == MOUSE_BUTTON_WHEEL_DOWN):
			_stoppe_fahrt()
			_rueckkehr.clear()
		if maus.pressed and maus.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoome_um(maus.position, _zoom * 0.9)
			gezoomt.emit()
		elif maus.pressed and maus.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoome_um(maus.position, _zoom / 0.9)
			gezoomt.emit()
	elif ereignis is InputEventMagnifyGesture:
		# Trackpad (Laptop, Chromebook): factor > 1 = auseinander = naeher heran.
		var geste := ereignis as InputEventMagnifyGesture
		if geste.factor > 0.0:
			_stoppe_fahrt()
			_rueckkehr.clear()
			_zoome_um(geste.position, _zoom / geste.factor)
			gezoomt.emit()


func _behandle_beruehrung(ereignis: InputEventScreenTouch) -> void:
	if ereignis.pressed:
		_beruehrungen[ereignis.index] = ereignis.position
		_doppeltipp_offen = false
		_stoppe_fahrt()
		if _beruehrungen.size() == 1:
			_druck_start = ereignis.position
			_gezogen = false
			_schwung = Vector3.ZERO
		elif _beruehrungen.size() == 2:
			_pinch_abstand = _pinch_werte()[0]
			_gezogen = true
			_hat_gepincht = true
	else:
		if _beruehrungen.size() == 1 and not _gezogen:
			if ereignis.position.distance_to(_druck_start) <= TAP_MAX_DISTANZ:
				_tipp(ereignis.position)
		_beruehrungen.erase(ereignis.index)
		if _beruehrungen.size() == 1:
			# Vom Pinch zurueck zu einem Finger: neu ansetzen, sonst springt die
			# Karte um den Abstand der beiden Finger.
			_druck_start = _beruehrungen.values()[0] as Vector2
			_pinch_abstand = 0.0
		if _beruehrungen.is_empty() and _hat_gepincht:
			# Pinch zu Ende (letzter Finger weg): Der Zoom bleibt, wo er ist (K6).
			_hat_gepincht = false
			_pinch_abstand = 0.0
			gezoomt.emit()


## Ein Tipp. Ein zweiter Tipp kurz danach an derselben Stelle wird
## zum Doppeltipp -- und dann NICHT mehr als normaler Tipp gemeldet.
func _tipp(position_bild: Vector2) -> void:
	var punkt: Variant = _boden(position_bild)
	if punkt == null:
		return
	var ursprung: Vector3 = project_ray_origin(position_bild)
	var richtung: Vector3 = project_ray_normal(position_bild)
	var jetzt: int = Time.get_ticks_msec()
	if ist_doppeltipp(_letzter_tipp_ms, _letzter_tipp_ort, jetzt, position_bild):
		_letzter_tipp_ms = -100000
		_doppeltipp_offen = true
		doppelt_getippt.emit(ursprung, richtung, punkt as Vector3)
		return
	_letzter_tipp_ms = jetzt
	_letzter_tipp_ort = position_bild
	_zoom_beim_tipp = _zoom
	welt_getippt.emit(ursprung, richtung, punkt as Vector3)


## Reine Entscheidung, testbar ohne Uhr.
static func ist_doppeltipp(vorher_ms: int, vorher_ort: Vector2, jetzt_ms: int, ort: Vector2) -> bool:
	return jetzt_ms - vorher_ms <= DOPPEL_ZEIT_MS and ort.distance_to(vorher_ort) <= DOPPEL_ABSTAND


func _behandle_ziehen(ereignis: InputEventScreenDrag) -> void:
	var vorher: Vector2 = _beruehrungen.get(ereignis.index, ereignis.position - ereignis.relative) as Vector2
	_beruehrungen[ereignis.index] = ereignis.position

	if _beruehrungen.size() >= 2:
		_pinch()
		return

	if ereignis.position.distance_to(_druck_start) > TAP_MAX_DISTANZ:
		_gezogen = true
	if not _gezogen:
		return
	# Wer selbst wischt, nimmt die Kamera in die Hand: kein Zurueckfahren mehr.
	_rueckkehr.clear()

	# Exakt: Welcher Bodenpunkt lag unter dem Finger, welcher liegt jetzt dort?
	# Die Differenz ist die Bewegung. Die vorige Fassung rechnete mit EINEM
	# Massstab fuer beide Achsen -- in der Isometrie ist ein Pixel senkrecht
	# aber 1,73-mal so viel Boden wie waagerecht, und die Karte lief dem Finger
	# beim Hoch- und Runterwischen davon.
	var a: Variant = _boden(vorher)
	var b: Variant = _boden(ereignis.position)
	if a == null or b == null:
		return
	var bewegung: Vector3 = (a as Vector3) - (b as Vector3)
	bewegung.y = 0.0
	_ziel += bewegung
	_ziel = _gummi(_ziel)
	var dt: float = maxf(get_process_delta_time(), 0.001)
	_schwung = bewegung / dt
	_aktualisiere_position()


func _pinch() -> void:
	_rueckkehr.clear()
	var werte: Array = _pinch_werte()
	var abstand: float = werte[0]
	var mitte: Vector2 = werte[1]
	if _pinch_abstand <= 0.0:
		_pinch_abstand = abstand
		return
	var neu: float = _zoom * (_pinch_abstand / maxf(abstand, 1.0))
	_pinch_abstand = abstand
	_zoome_um(mitte, neu)


func _pinch_werte() -> Array:
	var punkte: Array = _beruehrungen.values()
	if punkte.size() < 2:
		return [0.0, Vector2.ZERO]
	var p0: Vector2 = punkte[0]
	var p1: Vector2 = punkte[1]
	return [p0.distance_to(p1), (p0 + p1) * 0.5]


## Zoomt so, dass der Bodenpunkt unter `bildschirm` an seiner Stelle bleibt.
func _zoome_um(bildschirm: Vector2, neuer_zoom: float) -> void:
	var vorher: Variant = _boden(bildschirm)
	_zoom = clampf(neuer_zoom, zoom_min, zoom_max)
	size = _zoom
	_aktualisiere_position()
	var nachher: Variant = _boden(bildschirm)
	if vorher != null and nachher != null:
		var d: Vector3 = (vorher as Vector3) - (nachher as Vector3)
		d.y = 0.0
		_ziel = _gummi(_ziel + d)
		_aktualisiere_position()


## Faehrt so, dass `welt` auf der Bildschirmhoehe `bildschirm_y` in der Mitte steht.
## `bildschirm_x` >= 0: statt der Mitte auf diese Spalte (K6 1c: nur so weit schieben wie noetig).
func fokussiere(welt: Vector3, bildschirm_y: float, dauer: float = 0.35, bildschirm_x: float = -1.0) -> void:
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var jetzt: Vector2 = unproject_position(welt)
	var ziel_punkt := Vector2(flaeche.x * 0.5 if bildschirm_x < 0.0 else bildschirm_x, bildschirm_y)
	var a: Variant = _boden(jetzt)
	var b: Variant = _boden(ziel_punkt)
	if a == null or b == null:
		return
	var d: Vector3 = (a as Vector3) - (b as Vector3)
	d.y = 0.0
	var ende: Vector3 = _begrenzt(_ziel + d)
	_stoppe_fahrt()
	_schwung = Vector3.ZERO
	_fahrt = create_tween()
	_fahrt.tween_method(func(p: Vector3) -> void:
		_ziel = p
		_aktualisiere_position(), _ziel, ende, dauer).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)


## Raum betreten: weiche Fahrt auf `welt` (Bildschirmhoehe `bildschirm_y`), jede
## Beruehrung unterbricht sie (_stoppe_fahrt).
##
## K6 (Bastian 16.10.: "Das soll man selbst einstellen"): Den Zoom aendert `betrete`
## nur nach einem Doppeltipp (bewusste Geste) oder mit `mit_zoom`. Sonst bleibt der
## Zoom -- und steht `welt` schon im Bild, bleibt auch der Ausschnitt: Ein Tipp auf
## einen sichtbaren Raum bewegt die Kamera nicht. Es gibt keine Rueckfahrt mehr.
func betrete(welt: Vector3, bildschirm_y: float, ziel_zoom: float, dauer: float = 0.5,
		mit_zoom: bool = false) -> void:
	var flaeche: Vector2 = get_viewport().get_visible_rect().size
	var darf_zoomen: bool = mit_zoom or _doppeltipp_offen
	_doppeltipp_offen = false
	if not darf_zoomen:
		if im_bild(welt, flaeche):
			return
		ziel_zoom = _zoom
	var neuer_zoom: float = clampf(ziel_zoom, zoom_min, zoom_max)
	# Mit dem ZIEL-Zoom rechnen: Wie weit liegt `welt` dann von der Bildmarke?
	var alt_size: float = size
	size = neuer_zoom
	var a: Variant = _boden(unproject_position(welt))
	var b: Variant = _boden(Vector2(flaeche.x * 0.5, bildschirm_y))
	size = alt_size
	if a == null or b == null:
		return
	var d: Vector3 = (a as Vector3) - (b as Vector3)
	d.y = 0.0
	_fahre_nach(_begrenzt(_ziel + d), neuer_zoom, dauer)


## Zoom, bei dem ein Raum ueber dem Panel (`frei` Pixel Hoehe) ins Bild passt.
## `zoom` in worlds.json (zonen[].zoom) hat Vorrang. Isometrie: Der Raum misst auf
## dem Bild (b + t) / sqrt2 in die Breite und (b + t) * 0.41 in die Hoehe
## (Weltmasse), dazu ein kleiner Rand fuer Waende und Schilder.
static func raum_zoom(zone: Dictionary, flaeche: Vector2, frei: float) -> float:
	if zone.has("zoom"):
		return float(zone["zoom"])
	var summe: float = (float(zone["x2"]) - float(zone["x1"])) + (float(zone["z2"]) - float(zone["z1"]))
	var rand: float = 1.05
	var breite_n: float = summe / sqrt(2.0) * rand / (flaeche.x / flaeche.y)
	var hoehe_n: float = summe * 0.41 * rand / (maxf(frei, 1.0) / flaeche.y)
	return maxf(breite_n, hoehe_n)


## Ansicht, in der alle `zonen` (Dictionaries mit x1/z1/x2/z2) zugleich im Bild
## stehen: {"zoom": float, "blick": Vector3}. Gerechnet wird im Bildraum der
## Isometrie: rechts u = (x - z) / sqrt2, unten v = (x + z) * 0.408 (Weltmasse).
## `oben`/`unten` sind die verdeckten Pixelstreifen (Kopfleiste, Menueleiste);
## die Mitte der Zonen landet in der Mitte des freien Streifens. Waende ragen
## nach oben aus dem Boden -- dafuer `wand` Weltmeter Zuschlag oben.
static func ansicht_fuer(zonen: Array, flaeche: Vector2, oben: float, unten: float,
		rand: float = 1.08, wand: float = 2.0) -> Dictionary:
	if zonen.is_empty() or flaeche.x <= 0.0 or flaeche.y <= 0.0:
		return {}
	var u_min: float = INF
	var u_max: float = -INF
	var v_min: float = INF
	var v_max: float = -INF
	for eintrag in zonen:
		var z: Dictionary = eintrag as Dictionary
		for x in [float(z.get("x1", 0.0)), float(z.get("x2", 0.0))]:
			for zz in [float(z.get("z1", 0.0)), float(z.get("z2", 0.0))]:
				var u: float = (x - zz) / sqrt(2.0)
				var v: float = (x + zz) * V_FAKTOR
				u_min = minf(u_min, u)
				u_max = maxf(u_max, u)
				v_min = minf(v_min, v)
				v_max = maxf(v_max, v)
	v_min -= wand * W_FAKTOR
	var frei: float = maxf(flaeche.y - oben - unten, 1.0)
	var zoom_breite: float = (u_max - u_min) * rand / (flaeche.x / flaeche.y)
	var zoom_hoehe: float = (v_max - v_min) * rand / (frei / flaeche.y)
	var zoom_neu: float = maxf(zoom_breite, zoom_hoehe)
	# Die Mitte der Zonen soll in der Mitte des freien Streifens stehen, also um
	# `versatz` Pixel unter der Bildmitte -- die Bildmitte liegt entsprechend hoeher.
	var versatz_px: float = (oben + (flaeche.y - unten)) * 0.5 - flaeche.y * 0.5
	var u_mitte: float = (u_min + u_max) * 0.5
	var v_mitte: float = (v_min + v_max) * 0.5 - versatz_px / flaeche.y * zoom_neu
	return {"zoom": zoom_neu, "blick": blick_aus_bild(u_mitte, v_mitte)}


## Ansicht, in der alle `punkte` (Weltpunkte, z. B. die Stationen eines Raums) samt `rand_m`
## Meter Rand zugleich im freien Streifen stehen -- die Mitte der PUNKTE liegt in der Mitte
## des Streifens, nicht die Mitte des Raums (K3-Fix 2). Ohne Punkte: leeres Dictionary.
## Zusatz `mitte`: Weltpunkt der Mitte, zum Anfahren mit `betrete`.
static func punkte_ansicht(punkte: Array, rand_m: float, flaeche: Vector2, oben: float, unten: float,
		wand: float = 1.0) -> Dictionary:
	var zonen: Array = []
	var x_min: float = INF
	var x_max: float = -INF
	var z_min: float = INF
	var z_max: float = -INF
	for p in punkte:
		var v: Vector3 = p as Vector3
		zonen.append({"x1": v.x - rand_m, "x2": v.x + rand_m, "z1": v.z - rand_m, "z2": v.z + rand_m})
		x_min = minf(x_min, v.x)
		x_max = maxf(x_max, v.x)
		z_min = minf(z_min, v.z)
		z_max = maxf(z_max, v.z)
	if zonen.is_empty():
		return {}
	var ergebnis: Dictionary = ansicht_fuer(zonen, flaeche, oben, unten, 1.0, wand)
	ergebnis["mitte"] = Vector3((x_min + x_max) * 0.5, 0.0, (z_min + z_max) * 0.5)
	return ergebnis


## Bodenpunkt, der im Bildraum (u, v) liegt (Umkehrung von `ansicht_fuer`).
static func blick_aus_bild(u: float, v: float) -> Vector3:
	var differenz: float = u * sqrt(2.0)       # x - z
	var summe: float = v / V_FAKTOR            # x + z
	return Vector3((summe + differenz) * 0.5, 0.0, (summe - differenz) * 0.5)


## Steht der Weltpunkt im Bild (`flaeche` in Bildpixeln)?
func im_bild(welt: Vector3, flaeche: Vector2) -> bool:
	if is_position_behind(welt):
		return false
	return Rect2(Vector2.ZERO, flaeche).has_point(unproject_position(welt))


## Zurueck in die Ansicht vor dem Raum. Seit K6 merkt sich `betrete` keine Ansicht
## mehr -- die Kamera faehrt nach dem Schliessen eines Menues nirgends hin.
func kehre_zurueck(dauer: float = 0.45) -> bool:
	if _rueckkehr.is_empty():
		return false
	var blick: Vector3 = _rueckkehr["blick"] as Vector3
	var z: float = float(_rueckkehr["zoom"])
	_rueckkehr.clear()
	_fahre_nach(blick, z, dauer)
	return true


## Blickpunkt und Zoom setzen -- weich (`dauer` > 0) oder sofort (Start).
func zeige_ansicht(blick: Vector3, ziel_zoom: float, dauer: float = 0.0) -> void:
	_rueckkehr.clear()
	var z: float = clampf(ziel_zoom, zoom_min, zoom_max)
	if dauer <= 0.0:
		_stoppe_fahrt()
		_zoom = z
		size = _zoom
		setze_blickpunkt(blick)
		return
	_fahre_nach(_begrenzt(Vector3(blick.x, 0.0, blick.z)), z, dauer)


func hat_rueckkehr() -> bool:
	return not _rueckkehr.is_empty()


func _fahre_nach(ende: Vector3, ende_zoom: float, dauer: float) -> void:
	_stoppe_fahrt()
	_schwung = Vector3.ZERO
	var start: Vector3 = _ziel
	var start_zoom: float = _zoom
	_fahrt = create_tween()
	_fahrt.tween_method(func(f: float) -> void:
		_ziel = start.lerp(ende, f)
		_zoom = lerpf(start_zoom, ende_zoom, f)
		size = _zoom
		_aktualisiere_position(), 0.0, 1.0, dauer).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


## Kamera-Ruck beim Raumkauf -- seit K6 aus: Die Kamera bewegt nur der Spieler.
## Bleibt als Aufrufpunkt, bis main.gd ihn nicht mehr ruft; `staerke` <= 0 = nichts.
func ruck(staerke: float = 0.0, dauer: float = 0.2) -> void:
	if staerke <= 0.0:
		return
	if _ruck_tween != null and _ruck_tween.is_valid():
		_ruck_tween.kill()
	_ruck = Vector3(staerke, 0.0, staerke)
	_aktualisiere_position()
	_ruck_tween = create_tween()
	_ruck_tween.tween_method(func(f: float) -> void:
		_ruck = Vector3(staerke, 0.0, staerke) * f
		_aktualisiere_position(), 1.0, 0.0, dauer).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func _stoppe_fahrt() -> void:
	if _fahrt != null and _fahrt.is_valid():
		_fahrt.kill()


## Bodenpunkt (y = 0) unter einer Bildschirmposition, oder null.
func _boden(bildschirm: Vector2) -> Variant:
	var ursprung: Vector3 = project_ray_origin(bildschirm)
	var richtung: Vector3 = project_ray_normal(bildschirm)
	if absf(richtung.y) < 0.0001:
		return null
	var t: float = -ursprung.y / richtung.y
	return ursprung + richtung * t


func _begrenzt(p: Vector3) -> Vector3:
	return Vector3(
		clampf(p.x, grenzen.position.x, grenzen.end.x), 0.0,
		clampf(p.z, grenzen.position.y, grenzen.end.y))


## Beim Ziehen darf man ein Stueck ueber die Grenze -- mit wachsendem Widerstand.
func _gummi(p: Vector3) -> Vector3:
	var b: Vector3 = _begrenzt(p)
	var ueber: Vector3 = p - b
	return b + ueber * 0.35


func _begrenze_ziel(hart: bool = false) -> void:
	_ziel = _begrenzt(_ziel) if hart else _gummi(_ziel)


func _aktualisiere_position() -> void:
	# Position und Blickrichtung aus EINER Rechnung -- look_at() macht die
	# Ausrichtung zur Folge der Position statt zu einer zweiten Wahrheit.
	var richtung: Vector3 = Vector3(1.0, 1.0, 1.0).normalized()
	global_position = _ziel + _ruck + richtung * ABSTAND
	look_at(_ziel + _ruck, Vector3.UP)
