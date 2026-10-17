## Das Design-System "Sticker-Pop" an EINER Stelle (docs/NACHT_PLAN.md 3, ADR-022).
##
## Karten und Knoepfe wie Aufkleber: dunkle Tintenkontur, harter versetzter
## Schatten ohne Weichzeichnung, cremiges Papier als Grund, eine kraeftige
## Grotesk-Schrift. Je Welt EINE Akzentfarbe -- die Farbe der Figur, aus dem
## Block "stil" der Themendatei. Limette ist die einzige Kauffarbe, Rot gehoert
## allein dem Engpass, Gold der Muenze und den Sternen.
##
## Ruhig bleibt das, weil es nur EINE Effektart gibt: die harte Kante. Kein
## Verlauf, kein Glanz, kein weicher Schatten.
##
## Hier stehen DARSTELLUNGSwerte, keine Balance und kein Text (Regel D3).
## Keine Ansicht traegt eigene Farbwerte -- alles kommt von hier.
class_name UiStil
extends RefCounted

# --- Farben ----------------------------------------------------------------------
const PAPIER := Color("fff7ea")        ## Kartenflaeche
const PAPIER_2 := Color("f3e9d8")      ## ruhige Flaeche, Leisten, deaktiviert
const TINTE := Color("1b1726")         ## Kontur, Text, harter Schatten
const TINTE_2 := Color("5a5368")       ## Nebentext (>= 4,5 : 1 auf Papier)
const TINTE_3 := Color("8c8499")       ## leere Sterne, Griff -- nie fuer Text
const KAUFEN := Color("b6f03c")        ## Kaufen. Schrift darauf immer Tinte.
const WARNUNG := Color("ff4d3d")       ## nur der Engpass
const GOLD := Color("ffc21a")          ## Muenze, Sterne, Belohnung
const WEISS := Color("ffffff")
## Text-Varianten fuer Plus und Gold auf Papier (Kontrast >= 4,5 : 1).
const PLUS_TEXT := Color("2f6f0a")
const GOLD_TEXT := Color("8a5a00")
const WARNUNG_TEXT := Color("b3221a")
## Rueckfall, solange keine Welt einen Akzent geliefert hat.
const AKZENT_STANDARD := Color("3d7bff")
## Schleier hinter Vollbild-Momenten: Tinte, nicht Schwarz.
const SCHLEIER := Color(0.106, 0.090, 0.149, 0.62)

# --- Masse -----------------------------------------------------------------------
const KONTUR: int = 3                  ## Knoepfe, Karten
const KONTUR_CHIP: int = 2             ## Chips, Balken
const SCHATTEN_Y: float = 4.0          ## harter Schatten 0/4
const EINDRUCK_Y: float = 3.0          ## gedrueckt: 3 px nach unten, Schatten 0/1
const RADIUS_KARTE: int = 18
const RADIUS_KNOPF: int = 14
const RADIUS_CHIP: int = 999
## Abstaende -- nur diese.
const A1: int = 4
const A2: int = 8
const A3: int = 12
const A4: int = 16
const A5: int = 24
const A6: int = 32
## Schriftgroessen (logische Pixel, Oberflaeche 720 breit).
const GR_KLEIN: int = 18
const GR_TEXT: int = 22
const GR_MITTEL: int = 26
const GR_GROSS: int = 32
const GR_TITEL: int = 40
const GR_ZAHL: int = 44
const GR_RIESIG: int = 64
const GR_POSTER: int = 92
## --- Overhaul 2026-10-15 (Tokens, docs/nacht/ov_tokens.md) ---
## Die Doku nennt GR_TITEL 32; im Code ist das GR_GROSS. GR_TITEL bleibt 40, damit
## bestehende Layouts nicht kippen. Neue Ansichten nehmen GR_NUTZEN (32).
const GR_HINWEIS: int = GR_KLEIN       ## 18: nur Chips, Untertitel, Badges
const GR_NUTZEN: int = GR_GROSS        ## 32: "+3,4 EUR/s" in PLUS_TEXT
const GR_HELD: int = GR_RIESIG         ## 64: Belohnungs-Moment
const KAUFEN_TIEF := Color("7fb81c")   ## Kante/Schatten des Hauptknopfs
const STERN_BALKEN := GOLD             ## nur Stern-Fortschritt
const GESPERRT := Color("d9d0c0")      ## gesperrte Karte, Text TINTE_3/TINTE_2
const KNOPF_PRIMAER_H: float = 104.0   ## genau einer je Sheet
const KNOPF_SEKUNDAER_H: float = 72.0  ## x1/x10/MAX, "Zur Station"
const SHEET_MAX: float = 0.56          ## Anteil der Bildhoehe
const BADGE_H: float = 40.0            ## Level-Abzeichen in der Welt
const SCHATTEN_Y_PRIMAER: float = 6.0
const SCHATTEN_Y_MARKER: float = 2.0     ## Marker und Schilder in der Welt: 0/2 (Karten/Chips 0/4, Hauptknopf 0/6)
const A7: int = 48                     ## Abstand zwischen Abschnitten (A6 = innerhalb)
const DAUER_ZAEHLEN: float = 0.8       ## Zahlen zaehlen hoch
const PULS_HZ: float = 1.2             ## Pfeil/Ring "kaufbar", Scale 1,0 -> 1,08
const PULS_SKALA: float = 1.08
const DAUER_SZENE_EIN: float = 0.25    ## Figuren-Popup, TRANS_BACK
## Schriftstaerken der Bricolage Grotesque.
## Genau zwei: Aufrufer mit alten Werten (900/1000 -> fett, 700 -> Text)
## landen automatisch auf einer der beiden.
const FETT: int = 800                  ## ExtraBold: Zahlen, Titel
const TEXT_GEWICHT: int = 600          ## SemiBold: Text
## Bewegung: 80 ms Eindruecken, 300 ms Kaufen-Ueberschwingen. Sonst nichts.
const DAUER_DRUECKEN: float = 0.08
const DAUER_KAUF: float = 0.30

## Mindesthoehe eines Tippziels in LOGISCHEN Pixeln. Die Oberflaeche ist logisch
## 720 breit, auf dem Referenzgeraet 1080 -- Faktor 1,5. 48 dp bei 440 dpi sind
## 132 Geraetepixel, also 88 logische.
const TIPPZIEL: float = 88.0

# --- Alte Namen ------------------------------------------------------------------
# Aufrufer ausserhalb von game/ui (main.gd) sprechen noch die Namen des alten
# Stils. Sie zeigen auf die neuen Token, damit dort nichts bricht.
const CREME := PAPIER
const CREME_TIEF := PAPIER_2
const RAND := TINTE
const TEXT := TINTE
const TEXT_SANFT := TINTE_2
const GRUEN := KAUFEN
const GRUEN_TIEF := PLUS_TEXT
const GELB := GOLD
const GELB_TIEF := GOLD_TEXT
const ROT := WARNUNG
const ROT_TIEF := WARNUNG_TEXT
const GRAU := PAPIER_2
const GRAU_TIEF := TINTE_2
const BALKEN_GRUND := PAPIER_2

const SCHRIFT_PFAD: String = "res://assets/fonts/BricolageGrotesque.ttf"
const RUECKFALL_PFAD: String = "res://assets/fonts/Nunito.ttf"
const SYMBOL_PFAD: String = "res://assets/ui/symbole/%s.svg"

static var _schriften: Dictionary = {}
static var _symbole: Dictionary = {}
static var _thema: Theme = null
static var _akzent: Color = AKZENT_STANDARD
static var _akzent_text: Color = TINTE
static var _akzent_tief: Color = TINTE
static var _welt_thema: ThemeData = null
static var _naechstes_thema: ThemeData = null


# --- Welt und Akzent -------------------------------------------------------------

## Die Hud meldet hier jede neue Welt. Der Akzent faerbt ab dann Balken,
## Titelstreifen und Chips; `naechstes` braucht der Weltwechsel-Bildschirm,
## der schon in der Farbe der KOMMENDEN Welt steht.
static func setze_welt(thema_daten: ThemeData, naechstes: ThemeData = null) -> void:
	_welt_thema = thema_daten
	_naechstes_thema = naechstes
	_akzent = akzent_von(thema_daten)
	_akzent_text = akzent_text_von(thema_daten)
	_akzent_tief = akzent_tief_von(thema_daten)
	if _thema != null:
		_thema.set_stylebox("fill", "ProgressBar", balken(_akzent))


static func akzent() -> Color:
	return _akzent


static func akzent_text() -> Color:
	return _akzent_text


## Dunkle Kante der Welt: Menueleiste, Sheet-Rand. `stil.akzent_tief` der Themendatei,
## sonst der Akzent, abgedunkelt.
static func akzent_tief() -> Color:
	return _akzent_tief


static func akzent_tief_von(thema_daten: ThemeData) -> Color:
	var grund: Color = akzent_von(thema_daten)
	if thema_daten == null:
		return TINTE
	return farbe(thema_daten.stil("akzent_tief"), grund.darkened(0.3))


## Sheet-Grund: PAPIER_2, zu 6 % in die Weltfarbe getoent -- die Welt faerbt das ganze Menue,
## nicht nur den Titelstreifen. Text bleibt Tinte (Kontrast bleibt weit ueber 4,5:1).
static func papier_welt() -> Color:
	return PAPIER_2.lerp(_akzent, 0.06)


static func welt_thema() -> ThemeData:
	return _welt_thema


static func naechstes_thema() -> ThemeData:
	return _naechstes_thema


static func akzent_von(thema_daten: ThemeData) -> Color:
	if thema_daten == null:
		return AKZENT_STANDARD
	return farbe(thema_daten.stil("akzent"), AKZENT_STANDARD)


static func akzent_text_von(thema_daten: ThemeData) -> Color:
	var grund: Color = akzent_von(thema_daten)
	if thema_daten == null:
		return text_auf(grund)
	return farbe(thema_daten.stil("akzent_text"), text_auf(grund))


## Farbe eines Absenders im Handy: `absender_farben` der Themendatei, sonst Akzent.
static func absender_farbe(thema_daten: ThemeData, schluessel: String) -> Color:
	if thema_daten == null:
		return _akzent
	var farben: Dictionary = thema_daten.abschnitt("absender_farben")
	return farbe(String(farben.get(schluessel, "")), akzent_von(thema_daten))


## Hex-Text aus den Daten in eine Farbe; leer oder kaputt -> Ersatz.
static func farbe(hex: String, ersatz: Color) -> Color:
	var sauber: String = hex.strip_edges()
	if sauber.is_empty() or not Color.html_is_valid(sauber):
		return ersatz
	return Color.html(sauber)


## Tinte oder Weiss -- was auf diesem Grund besser lesbar ist.
static func text_auf(grund: Color) -> Color:
	return TINTE if kontrast(grund, TINTE) >= kontrast(grund, WEISS) else WEISS


## Kontrastverhaeltnis nach WCAG.
static func kontrast(a: Color, b: Color) -> float:
	# get_luminance() erwartet LINEARE Werte; Farben aus Hex-Text sind sRGB.
	var la: float = a.srgb_to_linear().get_luminance()
	var lb: float = b.srgb_to_linear().get_luminance()
	return (maxf(la, lb) + 0.05) / (minf(la, lb) + 0.05)


# --- Schrift und Symbole ---------------------------------------------------------

## Bricolage Grotesque in einer Staerke, mit tabellarischen Ziffern.
##
## Variable Schrift mit drei Achsen. Der Schluessel muss das OpenType-TAG als
## Zahl sein -- mit dem String "wght" bleibt die Schrift stillschweigend in
## ihrer Grundinstanz (CLAUDE.md, Fallstricke). Die optische Groesse (opsz)
## folgt der Schriftgroesse in Stufen: kleine Texte bekommen die offenere
## Textvariante, grosse Titel die engere Plakatvariante.
static func schrift(gewicht: int = FETT, groesse: int = GR_MITTEL) -> Font:
	var staerke: int = FETT if gewicht >= FETT else TEXT_GEWICHT
	var optisch: int = _optische_groesse(groesse)
	var schluessel: String = "%d_%d" % [staerke, optisch]
	if _schriften.has(schluessel):
		return _schriften[schluessel] as Font
	var basis: FontFile = load(SCHRIFT_PFAD) as FontFile if ResourceLoader.exists(SCHRIFT_PFAD) else null
	var rueckfall: FontFile = load(RUECKFALL_PFAD) as FontFile if ResourceLoader.exists(RUECKFALL_PFAD) else null
	if basis == null:
		push_warning("Schrift fehlt: %s" % SCHRIFT_PFAD)
		basis = rueckfall
	if basis == null:
		return ThemeDB.fallback_font
	var ts: TextServer = TextServerManager.get_primary_interface()
	var variante := FontVariation.new()
	variante.base_font = basis
	variante.variation_opentype = {
		ts.name_to_tag("wght"): staerke,
		ts.name_to_tag("opsz"): optisch,
	}
	# Tabellarische Ziffern: Ein hochzaehlendes Kapital darf nicht zappeln.
	variante.opentype_features = {ts.name_to_tag("tnum"): 1}
	if rueckfall != null and basis != rueckfall:
		var ersatz := FontVariation.new()
		ersatz.base_font = rueckfall
		ersatz.variation_opentype = {ts.name_to_tag("wght"): staerke + 100}
		variante.fallbacks = [ersatz]
	_schriften[schluessel] = variante
	return variante


static func _optische_groesse(groesse: int) -> int:
	if groesse <= GR_KLEIN:
		return 14
	if groesse <= GR_MITTEL:
		return 20
	if groesse <= 36:
		return 28
	if groesse <= 56:
		return 40
	return 96


## Pfad eines Symbols: "haus" -> symbole/haus.svg; mit Schraegstrich ("zimmer/bereich_1")
## -> assets/ui/zimmer/bereich_1.svg (Bereichssymbole je Welt).
static func symbol_pfad(name: String) -> String:
	if name.contains("/"):
		return "res://assets/ui/%s.svg" % name
	return SYMBOL_PFAD % name


static func symbol(name: String) -> Texture2D:
	if _symbole.has(name):
		return _symbole[name] as Texture2D
	var pfad: String = symbol_pfad(name)
	var textur: Texture2D = load(pfad) as Texture2D if ResourceLoader.exists(pfad) else null
	if textur == null:
		push_warning("Symbol fehlt: %s" % pfad)
	_symbole[name] = textur
	return textur


## Das eigene Bild eines Bereichs, falls es eins gibt: zuerst ein Symbol aus
## der Themendatei (bereiche.<id>.symbol), dann ein PNG unter
## assets/ui/<welt>/<bereich_id>.png. Sonst null -- der Aufrufer nimmt sein
## allgemeines Symbol.
static func bereich_bild(thema_daten: ThemeData, welt_id: String, bereich_id: StringName) -> Texture2D:
	if thema_daten != null:
		var eintrag: Dictionary = thema_daten.abschnitt("bereiche").get(String(bereich_id), {}) as Dictionary
		var name: String = String(eintrag.get("symbol", ""))
		if not name.is_empty() and ResourceLoader.exists(symbol_pfad(name)):
			return symbol(name)
	# Sonst das Bereichssymbol der Welt: assets/ui/<welt>/bereich_<n>.svg, dann .png.
	var svg: String = "res://assets/ui/%s/%s.svg" % [welt_id, String(bereich_id)]
	if ResourceLoader.exists(svg):
		return symbol("%s/%s" % [welt_id, String(bereich_id)])
	var pfad: String = "res://assets/ui/%s/%s.png" % [welt_id, String(bereich_id)]
	if ResourceLoader.exists(pfad):
		return load(pfad) as Texture2D
	return null


static func symbolbild(name: String, kante: float) -> TextureRect:
	var r := TextureRect.new()
	r.texture = symbol(name)
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.custom_minimum_size = Vector2(kante, kante)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


# --- Das Theme -------------------------------------------------------------------

## Das Theme fuer die ganze Oberflaeche. Einmal an die Wurzel gehaengt, erben
## alle Controls Schrift, Farben und Knopfstil.
static func thema() -> Theme:
	if _thema != null:
		return _thema
	var t := Theme.new()
	t.default_font = schrift(FETT, GR_MITTEL)
	t.default_font_size = GR_MITTEL
	t.set_color("font_color", "Label", TINTE)
	# Ein Knopf ohne eigene Farbe ist ein NEBENknopf: Papier mit Kontur.
	var stile: Dictionary = knopf_stile(PAPIER)
	for zustand in stile.keys():
		t.set_stylebox(String(zustand), "Button", stile[zustand] as StyleBox)
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	for name in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color",
			"font_hover_pressed_color"]:
		t.set_color(name, "Button", TINTE)
	t.set_color("font_disabled_color", "Button", TINTE_2)
	t.set_constant("h_separation", "Button", A2)
	t.set_stylebox("panel", "PanelContainer", karte())
	t.set_stylebox("background", "ProgressBar", balken_grund())
	t.set_stylebox("fill", "ProgressBar", balken(_akzent))
	# Schmale Rollleiste in Tinte -- die Standardleiste war grau und breit.
	var leiste := StyleBoxFlat.new()
	leiste.bg_color = Color(TINTE, 0.55)
	leiste.set_corner_radius_all(RADIUS_CHIP)
	leiste.content_margin_left = 3.0
	leiste.content_margin_right = 3.0
	t.set_stylebox("grabber", "VScrollBar", leiste)
	t.set_stylebox("grabber_hover", "VScrollBar", leiste)
	t.set_stylebox("grabber_pressed", "VScrollBar", leiste)
	t.set_stylebox("scroll", "VScrollBar", StyleBoxEmpty.new())
	_thema = t
	return t


# --- Flaechen --------------------------------------------------------------------

## Die Grundform: Flaeche, Kontur, harter Schatten.
static func sticker(farbe_flaeche: Color, radius: int = RADIUS_KARTE, kontur: int = KONTUR,
		innen: float = A4, schatten: float = SCHATTEN_Y, kontur_farbe: Color = TINTE) -> StickerBox:
	var box := StickerBox.new()
	var f := StyleBoxFlat.new()
	f.bg_color = farbe_flaeche
	f.set_corner_radius_all(radius)
	f.border_color = kontur_farbe
	f.set_border_width_all(kontur)
	f.anti_aliasing = true
	f.corner_detail = 10
	box.flaeche = f
	if schatten > 0.0:
		var s := StyleBoxFlat.new()
		s.bg_color = TINTE
		s.set_corner_radius_all(radius)
		s.anti_aliasing = true
		s.corner_detail = 10
		box.schatten = s
	box.schatten_y = schatten
	box.eindruck_y = minf(EINDRUCK_Y, schatten)
	box.set_content_margin_all(innen)
	return box


## Eine Karte. Der Radius ist nach oben begrenzt: Karten sind 18 rund, egal was
## ein alter Aufrufer verlangt -- sonst hat jede Ansicht wieder ihre eigene Form.
static func karte(farbe_flaeche: Color = PAPIER, radius: int = RADIUS_KARTE, rand: int = KONTUR,
		innen: float = A4) -> StickerBox:
	var kontur: int = KONTUR if rand > 0 else 0
	return sticker(farbe_flaeche, mini(radius, RADIUS_KARTE), kontur, innen,
		SCHATTEN_Y if rand > 0 else 0.0)


## Ein Chip: pillenrund, duenne Kontur, kleiner Schatten.
static func chip(farbe_flaeche: Color, innen_x: float = A3, innen_y: float = A1,
		schatten: float = 2.0) -> StickerBox:
	var box := sticker(farbe_flaeche, RADIUS_CHIP, KONTUR_CHIP, 0.0, schatten)
	box.content_margin_left = innen_x
	box.content_margin_right = innen_x
	box.content_margin_top = innen_y
	box.content_margin_bottom = innen_y
	return box


## Die Zustaende eines Knopfs. Gedrueckt: Schatten weg, Flaeche 3 px tiefer --
## und die Schrift rutscht mit (Innenabstand oben +3, unten -3).
## `tief` ist ein Rest des alten Stils und wird nicht mehr gebraucht.
static func knopf_stile(farbe_flaeche: Color, _tief: Color = TINTE, radius: int = RADIUS_KNOPF) -> Dictionary:
	var normal := _knopf_box(farbe_flaeche, radius)
	var gedrueckt := _knopf_box(farbe_flaeche, radius)
	gedrueckt.druck = 1.0
	gedrueckt.content_margin_top += EINDRUCK_Y
	gedrueckt.content_margin_bottom -= EINDRUCK_Y
	var aus := sticker(PAPIER_2, radius, KONTUR, 0.0, 0.0, Color(TINTE, 0.35))
	aus.content_margin_left = normal.content_margin_left
	aus.content_margin_right = normal.content_margin_right
	aus.content_margin_top = normal.content_margin_top
	aus.content_margin_bottom = normal.content_margin_bottom
	return {"normal": normal, "hover": normal, "pressed": gedrueckt, "hover_pressed": gedrueckt,
		"disabled": aus}


static func _knopf_box(farbe_flaeche: Color, radius: int) -> StickerBox:
	var box := sticker(farbe_flaeche, radius, KONTUR, 0.0)
	box.content_margin_left = float(A4)
	box.content_margin_right = float(A4)
	box.content_margin_top = float(A2)
	box.content_margin_bottom = float(A2)
	return box


## Faerbt einen Knopf -- Schrift automatisch Tinte oder Weiss nach Kontrast.
static func faerbe_knopf(knopf: Button, farbe_flaeche: Color, _tief: Color = TINTE,
		radius: int = RADIUS_KNOPF) -> void:
	# Menues faerben ihre Knoepfe bei jeder Aktualisierung (fuenfmal pro
	# Sekunde). Nur bei einer echten Aenderung neue Boxen bauen.
	var primaer: bool = bool(knopf.get_meta("primaer", false))
	var kaufkontur: bool = bool(knopf.get_meta("kaufkontur", false))
	var merkmal: Array = [farbe_flaeche, radius, primaer, kaufkontur]
	if knopf.get_meta("stil_zustand", []) == merkmal:
		return
	knopf.set_meta("stil_zustand", merkmal)
	var stile: Dictionary = knopf_stile(farbe_flaeche, TINTE, radius)
	if kaufkontur:
		# Bezahlbarer Nebenkauf: Papier mit Limetten-Kontur (kein zweiter Hauptknopf).
		for z in ["normal", "hover", "pressed", "hover_pressed"]:
			var kb: StickerBox = stile[z] as StickerBox
			kb.flaeche.border_color = KAUFEN_TIEF
			kb.flaeche.set_border_width_all(KONTUR + 1)
	if primaer:
		# Der Hauptknopf hebt sich 2 px mehr als Karten (Ebene 0/6).
		for z in ["normal", "hover"]:
			var sb: StickerBox = stile[z] as StickerBox
			sb.schatten_y = SCHATTEN_Y_PRIMAER
	for zustand in stile.keys():
		knopf.add_theme_stylebox_override(String(zustand), stile[zustand] as StyleBox)
	var schrift_farbe: Color = text_auf(farbe_flaeche)
	for name in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color",
			"font_hover_pressed_color"]:
		knopf.add_theme_color_override(name, schrift_farbe)
	knopf.add_theme_color_override("font_disabled_color", TINTE_2)


## Nebenknopf bezahlbar: Limetten-Kontur. Vor faerbe_knopf aufrufen.
static func setze_kaufkontur(knopf: Button, an: bool) -> void:
	knopf.set_meta("kaufkontur", an)


## Raum-Plaketten (K4 P1.2): ein Zustand = eine Flaechenfarbe. Schrift darauf
## immer TINTE (auch auf WARNUNG >= 4,5 : 1).
const PLAKETTEN_FARBEN: Dictionary = {
	&"kaufbar": KAUFEN,
	&"fast": GOLD,
	&"gesperrt": GESPERRT,
	&"bremst": WARNUNG,
	&"ruhig": PAPIER_2,
}


static func plaketten_farbe(zustand: StringName) -> Color:
	return PLAKETTEN_FARBEN.get(zustand, PAPIER_2) as Color


## Fuellfarbe des Level-Abzeichens: Akzent der Welt; Schrift darauf text_auf().
static func badge_box() -> StickerBox:
	var b: StickerBox = sticker(_akzent, RADIUS_CHIP, KONTUR_CHIP, 0.0, 2.0)
	b.content_margin_left = float(A3)
	b.content_margin_right = float(A3)
	b.content_margin_top = float(A1)
	b.content_margin_bottom = float(A1)
	return b


## Der Hauptknopf eines Sheets: Limette, Tintenschrift, gross.
static func kaufknopf(farbe_flaeche: Color = KAUFEN, hoehe: float = KNOPF_PRIMAER_H) -> Button:
	var k := Button.new()
	k.custom_minimum_size = Vector2(0.0, maxf(hoehe, TIPPZIEL))
	k.add_theme_font_override("font", schrift(FETT, GR_GROSS))
	k.add_theme_font_size_override("font_size", GR_GROSS - 2)
	k.add_theme_constant_override("icon_max_width", 40)
	k.set_meta("primaer", true)
	faerbe_knopf(k, farbe_flaeche)
	k.pressed.connect(func() -> void: aufploppen(k, 0.92))
	return k


## Ein Nebenknopf: Papier mit Kontur.
static func nebenknopf(text: String = "", hoehe: float = TIPPZIEL) -> Button:
	var k := Button.new()
	k.text = text
	k.custom_minimum_size = Vector2(0.0, maxf(hoehe, TIPPZIEL))
	k.add_theme_font_override("font", schrift(FETT, GR_TEXT))
	k.add_theme_font_size_override("font_size", GR_TEXT)
	faerbe_knopf(k, PAPIER)
	return k


## Die Kaufpille (K6 4.3): EIN Muster fuer jeden Kauf. Links Symbol, Mitte Titel
## und Nutzen, rechts der Preis. Bezahlbar = Limette, sonst ruhig und grau.
##
## `daten`: zustand (kaufbar | nicht | gesperrt | fertig), symbol (Texture2D),
## titel, nutzen, preis (fertiger Text), hoehe (ab KNOPF_PRIMAER_H gross, darunter
## schlank als Zeilenknopf), euro (true: der Preistext traegt das Euro-Zeichen
## selbst; sonst haengt die Pille es an). Mit `pille` wird eine vorhandene Pille
## nur neu beschriftet -- sie baut sich nie zweimal. Der Preis steht in
## Meta "preis" (Label) bzw. im Text des schlanken Knopfs.
static func kaufpille(daten: Dictionary, pille: Button = null) -> Button:
	var hoehe: float = float(daten.get("hoehe", KNOPF_PRIMAER_H))
	var gross: bool = hoehe >= KNOPF_PRIMAER_H - 16.0
	var zustand: String = String(daten.get("zustand", "kaufbar"))
	var frei: bool = zustand == "kaufbar"
	var preis: String = String(daten.get("preis", ""))
	var symbol_tex: Texture2D = daten.get("symbol", null) as Texture2D
	if pille == null:
		pille = Button.new()
		pille.custom_minimum_size = Vector2(0.0, maxf(hoehe, TIPPZIEL * 0.6))
		pille.clip_contents = true
		pille.set_meta("primaer", gross)
		pille.pressed.connect(func() -> void: aufploppen(pille, 0.94))
	pille.disabled = not frei
	faerbe_knopf(pille, KAUFEN if frei else PAPIER_2)
	var tinte: Color = TINTE if frei else TINTE_2
	if not gross:
		# Schlank: ein gewoehnlicher Knopf mit Muenze und Preis.
		var sym: String = "muenze"
		if zustand == "gesperrt":
			sym = "schloss"
		elif zustand == "fertig":
			sym = "haken"
		pille.text = preis
		pille.icon = symbol_tex if symbol_tex != null else symbol(sym)
		pille.expand_icon = false
		pille.add_theme_font_override("font", schrift(FETT, GR_TEXT))
		pille.add_theme_font_size_override("font_size", GR_TEXT)
		pille.add_theme_constant_override("icon_max_width", 26)
		pille.add_theme_constant_override("h_separation", A2)
		pille.clip_text = true
		pille.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		return pille
	var teile: Dictionary = pille.get_meta("teile", {}) as Dictionary
	if teile.is_empty():
		var zeile := HBoxContainer.new()
		zeile.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		zeile.offset_left = float(A3) + 2.0
		zeile.offset_right = -float(A4)
		zeile.offset_top = float(A1)
		zeile.offset_bottom = -float(A1)
		zeile.add_theme_constant_override("separation", A3)
		zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
		pille.add_child(zeile)
		var bild := symbolbild("pfeil_hoch", 64.0)
		bild.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		zeile.add_child(bild)
		var mitte := VBoxContainer.new()
		mitte.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		mitte.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		mitte.add_theme_constant_override("separation", -4)
		mitte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(mitte)
		var titel_l := label("", GR_GROSS - 2, TINTE, FETT)
		titel_l.clip_text = true
		titel_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		mitte.add_child(titel_l)
		var nutzen_l := label("", GR_KLEIN + 2, TINTE, FETT)
		nutzen_l.clip_text = true
		nutzen_l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		mitte.add_child(nutzen_l)
		var preis_box := HBoxContainer.new()
		preis_box.add_theme_constant_override("separation", 0)
		preis_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		preis_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		zeile.add_child(preis_box)
		var preis_l := label("", GR_ZAHL, TINTE, FETT)
		preis_box.add_child(preis_l)
		var euro_l := label(" €", GR_ZAHL, TINTE, FETT)
		preis_box.add_child(euro_l)
		# Der Glanz nach dem Kauf: ein heller Streifen, der ueber die Pille huscht.
		var glanz := ColorRect.new()
		glanz.name = "Glanz"
		glanz.color = Color(1, 1, 1, 0.55)
		glanz.mouse_filter = Control.MOUSE_FILTER_IGNORE
		glanz.size = Vector2(56.0, hoehe)
		glanz.visible = false
		pille.add_child(glanz)
		teile = {"bild": bild, "titel": titel_l, "nutzen": nutzen_l, "preis": preis_l, "euro": euro_l}
		pille.set_meta("teile", teile)
	var bild_n: TextureRect = teile["bild"] as TextureRect
	bild_n.texture = symbol_tex
	bild_n.visible = symbol_tex != null
	bild_n.modulate = Color.WHITE if frei or zustand == "fertig" else Color(1, 1, 1, 0.6)
	var titel_n: Label = teile["titel"] as Label
	titel_n.text = String(daten.get("titel", ""))
	titel_n.add_theme_color_override("font_color", tinte)
	var nutzen_n: Label = teile["nutzen"] as Label
	nutzen_n.text = String(daten.get("nutzen", ""))
	nutzen_n.visible = not nutzen_n.text.is_empty()
	nutzen_n.add_theme_color_override("font_color", PLUS_TEXT if frei else TINTE_2)
	var preis_n: Label = teile["preis"] as Label
	var euro_n: Label = teile["euro"] as Label
	var klein: bool = zustand == "gesperrt" or zustand == "fertig"
	preis_n.text = preis
	preis_n.add_theme_font_size_override("font_size", GR_MITTEL if klein else GR_ZAHL)
	preis_n.add_theme_font_override("font", schrift(FETT, GR_MITTEL if klein else GR_ZAHL))
	preis_n.add_theme_color_override("font_color", tinte)
	euro_n.visible = not klein and not bool(daten.get("euro", false))
	euro_n.add_theme_color_override("font_color", tinte)
	return pille


# --- Balken ----------------------------------------------------------------------

## Fuellung eines Balkens: Farbe mit Tintenkontur.
static func balken(farbe_flaeche: Color) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = farbe_flaeche
	s.set_corner_radius_all(RADIUS_CHIP)
	s.border_color = TINTE
	s.set_border_width_all(KONTUR_CHIP)
	s.anti_aliasing = true
	return s


static func balken_grund() -> StyleBoxFlat:
	return balken(PAPIER_2)


static func faerbe_balken(leiste: ProgressBar, farbe_flaeche: Color) -> void:
	leiste.add_theme_stylebox_override("fill", balken(farbe_flaeche))


static func neuer_balken(hoehe: float = 18.0, farbe_flaeche: Color = Color(0, 0, 0, 0)) -> ProgressBar:
	var b := ProgressBar.new()
	b.show_percentage = false
	b.max_value = 1.0
	b.custom_minimum_size = Vector2(0.0, hoehe)
	b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if farbe_flaeche.a > 0.0:
		faerbe_balken(b, farbe_flaeche)
	return b


# --- Text ------------------------------------------------------------------------

static func label(text: String, groesse: int = GR_MITTEL, farbe_text: Color = TINTE,
		gewicht: int = FETT) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", groesse)
	l.add_theme_color_override("font_color", farbe_text)
	l.add_theme_font_override("font", schrift(gewicht, groesse))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


## Text direkt ueber der 3D-Szene (aufsteigende Betraege): dicke Tintenkontur
## und harter Schatten -- wie ein ausgeschnittener Aufkleber. Ohne Kontur
## verliert heller Text gegen einen hellen Holzboden.
static func label_kontur(text: String, groesse: int, farbe_text: Color = WEISS) -> Label:
	var l := label(text, groesse, farbe_text, FETT)
	l.add_theme_color_override("font_outline_color", TINTE)
	l.add_theme_constant_override("outline_size", maxi(groesse / 4, 6))
	l.add_theme_color_override("font_shadow_color", TINTE)
	l.add_theme_constant_override("shadow_offset_x", 0)
	l.add_theme_constant_override("shadow_offset_y", 4)
	l.add_theme_constant_override("shadow_outline_size", maxi(groesse / 4, 6))
	return l


## Ein runder Avatar -- das Portrait der Figur, wenn es eines gibt, sonst die
## Initiale auf der Absenderfarbe. `name` darf der Anzeigename ("Mo") oder der
## Schluessel ("mo") sein; welche Figur dahinter steht, sagt `absender_figur`
## in der Themendatei, das Bild liegt unter assets/ui/portraits/<figur>_<ausdruck>.png.
static func avatar(name: String, farbe_flaeche: Color, kante: float = 64.0, ausdruck: String = "neutral") -> PanelContainer:
	var feld := PanelContainer.new()
	var box := sticker(farbe_flaeche, RADIUS_CHIP, KONTUR_CHIP, 0.0, 2.0)
	feld.add_theme_stylebox_override("panel", box)
	feld.custom_minimum_size = Vector2(kante, kante)
	feld.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bild: Texture2D = portrait(name, ausdruck)
	if bild != null:
		# Rund beschnitten ueber die gezeichnete Flaeche des Aufklebers.
		feld.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
		var tr := TextureRect.new()
		tr.texture = bild
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		feld.add_child(tr)
		return feld
	# Ohne Portrait (z. B. "Dein Kanal"): das Handy-Symbol im Farbkreis, kein nacktes Schwarz-"D".
	feld.add_theme_stylebox_override("panel", sticker(_akzent, RADIUS_CHIP, KONTUR_CHIP, 0.0, 2.0))
	var sym: TextureRect = symbolbild("handy", kante * 0.52)
	sym.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	sym.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	feld.add_child(sym)
	return feld


## Runder Avatar einer Crew-Karte: Portrait per Schluessel, sonst Initiale des Namens.
static func crew_avatar(schluessel: String, name: String, kante: float = 80.0) -> PanelContainer:
	var bild: Texture2D = crew_portrait(schluessel)
	var feld := PanelContainer.new()
	feld.add_theme_stylebox_override("panel", sticker(PAPIER_2 if bild != null else akzent(), RADIUS_CHIP, KONTUR_CHIP, 0.0, 2.0))
	if bild == null:
		feld.custom_minimum_size = Vector2(kante, kante)
		feld.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
		feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var l := label(name.strip_edges().left(1).to_upper(), int(kante * 0.5), akzent_text(), FETT)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		feld.add_child(l)
		return feld
	feld.custom_minimum_size = Vector2(kante, kante)
	feld.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	feld.mouse_filter = Control.MOUSE_FILTER_IGNORE
	feld.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	var tr := TextureRect.new()
	tr.texture = bild
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	feld.add_child(tr)
	return feld


const PORTRAIT_PFAD: String = "res://assets/ui/portraits/%s_%s.png"
## Figurenname aus der Themendatei -> Dateiname der Portraets.
const PORTRAIT_FIGUREN: Dictionary = {
	"figur_cap": "mo", "figur_buckethat": "younes", "figur_brille": "roman",
	"figur_zopf": "selin",
}


## Das Portrait einer Figur (neutral / jubelnd / geschockt) oder null (dann
## zeigt der Avatar die Initiale).
static func portrait(name: String, ausdruck: String = "neutral") -> Texture2D:
	for basis in _portrait_namen(name):
		var pfad: String = PORTRAIT_PFAD % [basis, ausdruck]
		if ResourceLoader.exists(pfad):
			return load(pfad) as Texture2D
	return null


## Portrait direkt per Schluessel aus `crew.<station>.portrait` (mira, tobi, kind, onkel ...).
## `figur_*`-Namen laufen ueber PORTRAIT_FIGUREN; ohne Bild kommt null zurueck.
static func crew_portrait(schluessel: String, ausdruck: String = "neutral") -> Texture2D:
	var basis: String = String(PORTRAIT_FIGUREN.get(schluessel, schluessel))
	var pfad: String = PORTRAIT_PFAD % [basis, ausdruck]
	if ResourceLoader.exists(pfad):
		return load(pfad) as Texture2D
	return null


## Moegliche Dateinamen fuer diesen Absender: Schluessel selbst, dann die Figur.
static func _portrait_namen(name: String) -> Array[String]:
	var ergebnis: Array[String] = []
	var sauber: String = name.strip_edges()
	if sauber.is_empty() or _welt_thema == null:
		return ergebnis
	var namen: Dictionary = _welt_thema.abschnitt("absender")
	var figuren: Dictionary = _welt_thema.abschnitt("absender_figur")
	var schluessel: String = ""
	for k in namen.keys():
		if String(k) == sauber or String(namen[k]) == sauber:
			schluessel = String(k)
	if schluessel.is_empty() and figuren.has(sauber):
		schluessel = sauber
	if schluessel.is_empty():
		return ergebnis
	ergebnis.append(schluessel)
	var figur: String = String(figuren.get(schluessel, ""))
	if not figur.is_empty():
		ergebnis.append(String(PORTRAIT_FIGUREN.get(figur, figur)))
	return ergebnis


## Welche Figur steht hinter diesem Absender? Leer = unbekannt.
static func portrait_figur(name: String) -> String:
	var n: Array[String] = _portrait_namen(name)
	return "" if n.is_empty() else n[0]


# --- Eingabe und Bewegung --------------------------------------------------------

## Ist dieses Ereignis das Loslassen eines Tippens (linke Maustaste)?
##
## NUR das Mausereignis zaehlt. Godot erzeugt zu jedem Touch ein Mausereignis
## (emulate_mouse_from_touch) und zu jedem Mausklick einen Touch
## (emulate_touch_from_mouse); beide erreichen `gui_input`. Wer beides wertet,
## feuert jede Tippflaeche doppelt (RELEASE_PLAN 2.E).
##
## Achtung (K6): Verliert ein Feld zwischen Druck und Loslassen den Maus-Fokus
## (etwa weil es kurz unsichtbar war), kommt dieses Loslassen nie an. Felder, die
## sich bewegen oder ein- und ausgeblendet werden (Kartenmarker), nehmen deshalb
## `TippErkenner`: Druck + Loslassen innerhalb der Tippschwelle, Maus ODER Touch.
static func ist_tipp(e: InputEvent) -> bool:
	if e is InputEventMouseButton:
		var m := e as InputEventMouseButton
		return m.button_index == MOUSE_BUTTON_LEFT and not m.pressed
	return false


## Eindruecken (80 ms): Der Aufkleber senkt sich auf seinen Schatten, der Inhalt
## rutscht mit, dann federt alles zurueck.
##
## Knoepfe brauchen das nicht -- sie zeigen den Druck selbst ueber ihren
## Zustand "pressed". Alles andere (Karten, Schilder, Chips) bekommt es hier.
static func eindruecken(ziel: Control) -> void:
	if ziel == null or not ziel.is_inside_tree() or ziel is Button:
		return
	var box: StickerBox = null
	if ziel.has_theme_stylebox("panel"):
		box = ziel.get_theme_stylebox("panel") as StickerBox
	var kinder: Array[Control] = []
	var basis: Array[float] = []
	for kind in ziel.get_children():
		if kind is Control:
			kinder.append(kind as Control)
			basis.append((kind as Control).position.y)
	var schritt := func(f: float) -> void:
		if box != null:
			box.druck = f
		for i in range(kinder.size()):
			if is_instance_valid(kinder[i]):
				kinder[i].position.y = basis[i] + EINDRUCK_Y * f
	var t := ziel.create_tween()
	t.tween_method(schritt, 0.0, 1.0, DAUER_DRUECKEN)
	t.tween_method(schritt, 1.0, 0.0, DAUER_DRUECKEN * 1.5).set_ease(Tween.EASE_OUT)


## Aufploppen mit Ueberschwingen (300 ms) -- der Kauf-Moment.
static func aufploppen(ziel: Control, von: float = 0.85) -> void:
	if ziel == null or not ziel.is_inside_tree():
		return
	ziel.pivot_offset = ziel.size * 0.5
	ziel.scale = Vector2(von, von)
	var t := ziel.create_tween()
	t.tween_property(ziel, "scale", Vector2.ONE, DAUER_KAUF).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## Klebt ein Control schraeg -- fuer Aufkleber auf Plakaten.
##
## Container setzen Drehung und Skalierung ihrer Kinder bei jedem Sortieren
## auf null zurueck. Die Neigung wird deshalb NACH jedem Sortieren des
## Elternteils neu gesetzt, samt Drehpunkt in der Mitte.
static func drehe(ziel: Control, grad: float) -> void:
	var anwenden := func() -> void:
		ziel.pivot_offset = ziel.size * 0.5
		ziel.rotation_degrees = grad
	ziel.tree_entered.connect(func() -> void:
		var eltern: Container = ziel.get_parent() as Container
		if eltern != null and not eltern.sort_children.is_connected(anwenden):
			eltern.sort_children.connect(anwenden)
		anwenden.call())
	ziel.resized.connect(anwenden)


# --- Zahlen ----------------------------------------------------------------------

## Grosse Zahlen lesbar machen.
##
## Bis Welt 6 wachsen die Betraege ueber zehn Groessenordnungen. Deutsche
## Kurzformen mit einer Nachkommastelle und Komma: "5,6 Mio" ist auf einen
## Blick erfasst, "5573127" nicht. Unter tausend bleibt die Zahl ganz -- am
## Anfang zaehlt jeder einzelne Euro. Tausender bis 100.000 mit Punkt statt
## Kuerzel: "12.480" liest sich besser als "12,5 Tsd".
const STUFEN: Array = [
	[1e15, "Brd"],
	[1e12, "Bio"],
	[1e9, "Mrd"],
	[1e6, "Mio"],
]


## Betrag, nie aufgerundet: 199,6 -> "199". Steht ein Guthaben so da und der Preis
## (UiStil.preis, aufgerundet) ebenso, reicht das Guthaben wirklich -- sonst stuende
## "200 EUR" auf dem Schirm und der Kaufknopf bliebe grau (K3-Handyrunde 16.10.).
static func zahl(wert: float) -> String:
	return _betrag_text(wert, false)


## Preis, nie abgerundet: 199,2 -> "200". Zusammen mit `zahl` fuer das Guthaben gilt:
## Zeigt das Guthaben mindestens den Preis, ist der Kauf moeglich.
static func preis(wert: float) -> String:
	return _betrag_text(wert, true)


## Auf Vielfache von `schritt` runden, immer in eine Richtung. Die Toleranz faengt
## Gleitkommafehler ab (0,3 * 10 = 3,0000000000000004), ohne je einen Cent zu verschenken.
static func _runde_richtung(betrag: float, schritt: float, auf: bool) -> float:
	var q: float = betrag / schritt
	var toleranz: float = maxf(1.0, q) * 1.0e-9
	return (ceilf(q - toleranz) if auf else floorf(q + toleranz)) * schritt


static func _betrag_text(wert: float, auf: bool) -> String:
	var betrag: float = absf(wert)
	var vorzeichen: String = "-" if wert < 0.0 else ""
	for stufe in STUFEN:
		var grenze: float = float(stufe[0])
		if betrag >= grenze:
			var kurz: String = "%.1f" % _runde_richtung(betrag / grenze, 0.1, auf)
			if kurz.ends_with(".0"):
				kurz = kurz.substr(0, kurz.length() - 2)
			return (vorzeichen + kurz + " " + String(stufe[1])).replace(".", ",")
	if betrag >= 10.0:
		var ganz: int = int(_runde_richtung(betrag, 1.0, auf))
		var text: String = str(ganz)
		var mit_punkten: String = ""
		while text.length() > 3:
			mit_punkten = "." + text.substr(text.length() - 3) + mit_punkten
			text = text.substr(0, text.length() - 3)
		return vorzeichen + text + mit_punkten
	if betrag == 0.0:
		return "0"
	return (vorzeichen + "%.1f" % _runde_richtung(betrag, 0.1, auf)).replace(".", ",")
