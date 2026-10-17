## Prüfschalter für Szenen und Momente (Paket U3), damit `tools/serie.sh` sie ohne
## Finger zeigen kann. main.gd ruft das einmal nach dem Aufbau auf:
##
##   U3Pruefung.anwenden(self, kern, thema, _hud, _audio, _pruefschalter())
##
## Schalter:
##   --variante a|b                A/B-Darstellung der Szene
##   --szene <nachricht_id|bsp_...> [--blase N|-1]  Szene aus der Themendatei oder data/tutorial/u3_beispiele.json
##   --moment <ziel|marke|geschenk|raum|stern|offline|levelup>  Belohnungs-Moment
class_name U3Pruefung
extends RefCounted

const BEISPIELE: String = "res://data/tutorial/u3_beispiele.json"
static var _angewandt: bool = false


static func anwenden(wurzel: Node, kern: GameCore, thema: ThemeData, hud: Hud,
		audio: AudioDirector, schalter: PackedStringArray) -> void:
	if _angewandt:
		return
	_angewandt = true
	var v: int = schalter.find("--variante")
	if v >= 0 and v + 1 < schalter.size():
		SzeneView.standard_variante = schalter[v + 1]
	var s: int = schalter.find("--szene")
	if s >= 0 and s + 1 < schalter.size():
		var blase: int = -2
		var b: int = schalter.find("--blase")
		if b >= 0 and b + 1 < schalter.size():
			blase = int(schalter[b + 1])
		_szene(wurzel, thema, audio, schalter[s + 1], blase)
	var m: int = schalter.find("--moment")
	if m >= 0 and m + 1 < schalter.size():
		_moment(wurzel, kern, thema, hud, audio, schalter[m + 1])


static func _szene(wurzel: Node, thema: ThemeData, audio: AudioDirector, id: String, blase: int = -2) -> void:
	var szene: Dictionary = {}
	if id.begins_with("bsp_"):
		var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(BEISPIELE))
		if geparst is Dictionary:
			szene = (geparst as Dictionary).get(id, {}) as Dictionary
	elif id == "eroeffnung" and thema != null:
		szene = SzeneView.szene_aus_eroeffnung(thema.abschnitt("eroeffnung"))
	elif thema != null:
		szene = SzeneView.szene_aus_nachricht(WeltTexte.nachricht(thema, id))
	if szene.is_empty():
		push_warning("Szene nicht gefunden: %s" % id)
		return
	var ebene := CanvasLayer.new()
	ebene.layer = 30
	wurzel.add_child(ebene)
	var ansicht: SzeneView = SzeneView.zeige_szene(ebene, szene, thema, audio)
	if blase > -2:
		ansicht.springe_zu(blase)


static func _moment(wurzel: Node, kern: GameCore, thema: ThemeData, hud: Hud,
		audio: AudioDirector, art: String) -> void:
	if art == "aus" and hud != null:
		# Vorgespulte Staende (--tiefe) loesen Momente aus; fuer reine Menue-Bilder weg damit.
		hud.get_tree().create_timer(0.8).timeout.connect(hud.momente_verwerfen)
		return
	if art == "raum" and hud != null:
		# Der echte Weg des Raumkaufs (Station als Bild, Band "NEU"), ohne zu kaufen.
		hud._auf_bereich_gekauft(&"bereich_1")
		return
	var ebene := CanvasLayer.new()
	ebene.layer = 31
	wurzel.add_child(ebene)
	var daten: Dictionary = {"art": art, "figur": "mo", "betrag": maxf(kern.einkommen_pro_sekunde() * 120.0, 2400.0),
		"untertitel": "2 Minuten Einkommen on top."}
	match art:
		"marke":
			daten["zahl"] = 25
		"levelup":
			# Wie im Spiel (K2 4.4): Rang 4 mit Name und der einen Zeile "Neu: ...".
			daten = MomentView.rang_daten(4, UiText.t("rang_name_4"), kern.erfolge.freischaltung_bei(4),
				kern.erfolge.bonus_je_rang * 100.0)
		"stern":
			daten["betrag"] = 0.0
			daten["text_gross"] = "×1,5"
			daten["untertitel"] = "Nächster Stern in 10 Stufen."
	MomentView.zeige_moment(ebene, daten, thema, hud.saft if hud != null else null, audio)
