## Das kleine Auftragsbrett (Welle 2b): ein Tipp auf eine Aufgabenkarte unter der
## Kopfleiste oeffnet es. Oben der gewaehlte Auftrag gross -- Absender mit Portrait,
## Aufgabe, Warum-Satz, Fortschritt, Belohnung -- darunter ein Knopf: "Los geht's!"
## fuehrt zur passenden Station oder zum Raum, "Abholen" zahlt einen erfuellten
## Auftrag aus (ohne Bestaetigungsfenster, nur Saft). Die uebrigen Auftraege stehen
## als schmale Zeilen darunter und lassen sich antippen.
##
## Texte: Abschnitt `auftragsbrett.<ziel_id>` der Themendatei (absender, satz).
class_name Auftragsbrett
extends Sheet

## Ein offener Auftrag: dorthin fahren (Station oder Raum).
signal ziel_gewaehlt(ziel_id: String)
## Ein erfuellter Auftrag wurde abgeholt.
signal eingeloest(betrag: float, von: Vector2)

## So viele Auftraege zeigt die Leiste und das Brett.
const ANZAHL: int = 3

var kern: GameCore
var thema: ThemeData
## Der gross gezeigte Auftrag (Ziel-ID); leer = der erste der Liste.
var gewaehlt: String = ""
var _signatur: String = ""

var _spalte: VBoxContainer


func _init() -> void:
	super()
	_spalte = VBoxContainer.new()
	_spalte.add_theme_constant_override("separation", UiStil.A3)
	inhalt.add_child(_spalte)


# --- Reine Logik (getestet) -------------------------------------------------------

## Die Texte des Themas fuer den Kern: <ziel_id> -> {absender, satz}.
static func texte_von(t: ThemeData) -> Dictionary:
	return t.abschnitt("auftragsbrett") if t != null else {}


## Anzeigename des Absenders ("mo" -> "Mo"); ohne Eintrag der Schluessel selbst.
static func absender_name(t: ThemeData, schluessel: String) -> String:
	if schluessel.is_empty():
		return ""
	if t != null:
		var namen: Dictionary = t.abschnitt("absender")
		if namen.has(schluessel):
			return String(namen[schluessel])
	return schluessel.capitalize()


## Kurzer Kartentext: "Mission: Alle Aktien im Depot" -> "Alle Aktien im Depot".
static func kurztext(t: ThemeData, z: Dictionary) -> String:
	var name: String = WeltTexte.ziel(t, z)
	var teile: PackedStringArray = name.split(": ", false, 1)
	return teile[1] if teile.size() == 2 else name


## Zaehlerstand "3/10"; kein Zaehler (leer) bei Zielen mit Soll <= 1.
static func zaehler_text(info: Dictionary) -> String:
	var soll: float = float(info.get("soll", 1.0))
	if soll <= 1.0:
		return ""
	return "%s/%s" % [_ganz(minf(float(info.get("ist", 0.0)), soll)), _ganz(soll)]


static func _ganz(wert: float) -> String:
	return str(int(floorf(wert))) if wert < 10000.0 else UiStil.zahl(wert)


## Die Auftraege fuer Leiste und Brett: erst die abholbaren, dann die offenen.
static func auftraege_von(k: GameCore, t: ThemeData) -> Array[Dictionary]:
	return k.auftragskarten(ANZAHL, texte_von(t))


## Wohin fuehrt "Los geht's!"? {art: station|bereich, id}. Ziele ohne Ort
## (Gesamtstufen, Verdienst) fuehren zur Station, die gerade bremst.
static func ziel_ort(k: GameCore, ziel_id: String) -> Dictionary:
	var ort: Dictionary = k.ziel_ort(ziel_id)
	var art: String = String(ort.get("art", ""))
	var id: String = String(ort.get("id", ""))
	if art == "station" and not id.is_empty() and k.kette.station(StringName(id)) != null:
		return {"art": "station", "id": id}
	if art == "bereich" and not id.is_empty():
		return {"art": "bereich", "id": id}
	return {"art": "station", "id": String(k.kette.bottleneck())}


# --- Aufbau -----------------------------------------------------------------------

func waehle(ziel_id: String) -> void:
	gewaehlt = ziel_id
	if ist_offen():
		aktualisiere()


func aktualisiere() -> void:
	if kern == null:
		return
	titel.text = UiText.t("brett_titel")
	var liste: Array[Dictionary] = auftraege_von(kern, thema)
	# Nur neu bauen, wenn sich etwas Sichtbares geaendert hat: Ein Knopf, der zwischen
	# Druecken und Loslassen ersetzt wird, verschluckt den Tipp ("Abholen" ging verloren).
	var signatur: String = gewaehlt
	for e in liste:
		signatur += "|%s:%s:%d" % [e.get("id", ""), e.get("status", ""), int(float(e.get("fortschritt", 0.0)) * 100.0)]
	if signatur == _signatur and _spalte.get_child_count() > 0:
		return
	_signatur = signatur
	for kind in _spalte.get_children():
		_spalte.remove_child(kind)
		kind.queue_free()
	if liste.is_empty():
		_spalte.add_child(UiStil.label(UiText.t("brett_leer"), UiStil.GR_MITTEL, UiStil.TINTE_2))
		return
	var aktiv: Dictionary = liste[0]
	for e in liste:
		if String(e["id"]) == gewaehlt:
			aktiv = e
	gewaehlt = String(aktiv["id"])
	_spalte.add_child(_grosse_karte(aktiv))
	_spalte.add_child(_knopf(aktiv))
	if liste.size() > 1:
		_spalte.add_child(UiStil.label(UiText.t("brett_weitere"), UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT))
		for e in liste:
			if String(e["id"]) != gewaehlt:
				_spalte.add_child(_zeile(e))


func _grosse_karte(info: Dictionary) -> Control:
	var fertig: bool = String(info["status"]) == "bereit"
	var karte_box := PanelContainer.new()
	karte_box.add_theme_stylebox_override("panel", UiStil.karte(UiStil.GOLD if fertig else UiStil.PAPIER,
		UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A4)))
	var spalte := VBoxContainer.new()
	spalte.add_theme_constant_override("separation", UiStil.A3)
	karte_box.add_child(spalte)

	var kopf_zeile := HBoxContainer.new()
	kopf_zeile.add_theme_constant_override("separation", UiStil.A3)
	spalte.add_child(kopf_zeile)
	var schluessel: String = String(info.get("absender", ""))
	var name: String = absender_name(thema, schluessel)
	if not name.is_empty():
		kopf_zeile.add_child(UiStil.avatar(name, UiStil.absender_farbe(thema, schluessel), 88.0))
	var texte := VBoxContainer.new()
	texte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	texte.add_theme_constant_override("separation", UiStil.A1)
	kopf_zeile.add_child(texte)
	if not name.is_empty():
		texte.add_child(UiStil.label(UiText.t("brett_von") % name, UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.FETT))
	var z: Dictionary = kern.ziele.definition(String(info["id"]))
	var aufgabe: Label = UiStil.label(kurztext(thema, z), UiStil.GR_MITTEL, UiStil.TINTE, UiStil.FETT)
	aufgabe.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	texte.add_child(aufgabe)
	var satz: String = String(info.get("satz", ""))
	if not satz.is_empty():
		var s: Label = UiStil.label(satz, UiStil.GR_TEXT, UiStil.TINTE_2, UiStil.TEXT_GEWICHT)
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		spalte.add_child(s)

	var balken_zeile := HBoxContainer.new()
	balken_zeile.add_theme_constant_override("separation", UiStil.A2)
	spalte.add_child(balken_zeile)
	var balken: ProgressBar = UiStil.neuer_balken(22.0, UiStil.TINTE if fertig else UiStil.akzent())
	balken.value = float(info["fortschritt"])
	balken.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	balken.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	balken_zeile.add_child(balken)
	var zaehler: String = zaehler_text(info)
	if not zaehler.is_empty():
		var l: Label = UiStil.label(zaehler, UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		balken_zeile.add_child(l)

	var belohnung: float = float(info.get("belohnung", 0.0))
	if belohnung > 0.0:
		var feld := PanelContainer.new()
		feld.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		feld.add_theme_stylebox_override("panel", UiStil.chip(UiStil.TINTE if fertig else UiStil.GOLD,
			float(UiStil.A3), float(UiStil.A1 + 2), 2.0))
		var zeile := HBoxContainer.new()
		zeile.add_theme_constant_override("separation", UiStil.A2)
		feld.add_child(zeile)
		zeile.add_child(UiStil.symbolbild("geschenk", 30.0))
		zeile.add_child(UiStil.label(UiText.t("brett_belohnung") + "  +" + UiStil.zahl(belohnung),
			UiStil.GR_TEXT, UiStil.WEISS if fertig else UiStil.TINTE, UiStil.FETT))
		spalte.add_child(feld)
	return karte_box


func _knopf(info: Dictionary) -> Button:
	var fertig: bool = String(info["status"]) == "bereit"
	var k: Button = UiStil.kaufknopf(UiStil.KAUFEN, UiStil.KNOPF_SEKUNDAER_H + 16.0)
	k.text = UiText.t("brett_abholen") if fertig else UiText.t("brett_los")
	var ziel_id: String = String(info["id"])
	k.pressed.connect(func() -> void:
		if fertig:
			_abholen(ziel_id, k.get_global_rect().get_center())
		else:
			schliessen_sofort()
			ziel_gewaehlt.emit(ziel_id))
	return k


func _abholen(ziel_id: String, von: Vector2) -> void:
	var betrag: float = kern.loese_ziel_ein(StringName(ziel_id))
	gewaehlt = ""
	eingeloest.emit(betrag, von)
	aktualisiere()


func _zeile(info: Dictionary) -> Control:
	var fertig: bool = String(info["status"]) == "bereit"
	var karte_box := PanelContainer.new()
	karte_box.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL - 8.0)
	karte_box.add_theme_stylebox_override("panel", UiStil.karte(UiStil.GOLD if fertig else UiStil.PAPIER_2,
		UiStil.RADIUS_KARTE, UiStil.KONTUR, float(UiStil.A3)))
	var zeile := HBoxContainer.new()
	zeile.add_theme_constant_override("separation", UiStil.A3)
	karte_box.add_child(zeile)
	zeile.add_child(UiStil.symbolbild("geschenk" if fertig else "ziel", 36.0))
	var z: Dictionary = kern.ziele.definition(String(info["id"]))
	var text: Label = UiStil.label(kurztext(thema, z), UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.clip_text = true
	text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	zeile.add_child(text)
	var balken: ProgressBar = UiStil.neuer_balken(14.0, UiStil.TINTE if fertig else UiStil.akzent())
	balken.value = float(info["fortschritt"])
	balken.custom_minimum_size = Vector2(110.0, 14.0)
	balken.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	zeile.add_child(balken)
	var ziel_id: String = String(info["id"])
	Menues._tippbar(karte_box, func() -> void: waehle(ziel_id))
	return karte_box
