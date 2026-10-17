## Der Daten-Parser des Lebendigkeits-Systems (reines GDScript, ohne Nodes).
##
## Liest die Schluessel aus worlds.json (licht.himmel, licht.glow, licht.partikel,
## kulisse[].animation, kulisse[].emission_puls) und macht daraus saubere,
## begrenzte Dictionaries. Regel: Was fehlt, ist leer. Was nicht lesbar ist,
## wird still verworfen -- nie ein Fehler, nie ein Absturz. Beide
## Schreibweisen (D1-Schema und Varianten) werden verstanden.
##
## Standardwerte und Obergrenzen stehen in data/worlds/lebendig.json.
class_name LebendigDaten
extends RefCounted

const REGELN_PFAD: String = "res://data/worlds/lebendig.json"

## Wenn die Regeldatei fehlt: nur die harten Grenzen, damit nichts ausufert.
const NOTFALL: Dictionary = {
	"grenzen": {"max_animiert": 8, "max_puls": 8, "max_materialien_je_knoten": 4,
		"max_partikel_systeme": 2, "max_partikel_menge": 8, "max_route_punkte": 8, "max_sterne": 20},
}

const TYP_ALIAS: Dictionary = {
	"drehen": "drehen", "rotieren": "drehen", "rotation": "drehen", "spin": "drehen",
	"treiben": "treiben", "driften": "treiben", "drift": "treiben", "schweben": "treiben",
	"foerdern": "foerdern", "fördern": "foerdern", "scrollen": "foerdern", "band": "foerdern", "lauf": "foerdern",
	"wackeln": "wackeln", "wippen": "wackeln", "schwanken": "wackeln",
	"fahren": "fahren", "fahrt": "fahren", "route": "fahren",
}

const PARTIKEL_ALIAS: Dictionary = {
	"staub": "staub", "dampf": "dampf", "rauch": "dampf", "funken": "funken",
	"motten": "motten", "motte": "motten", "voegel": "voegel", "vögel": "voegel", "vogel": "voegel",
}


## Regeln laden und ueber den Notfall legen. `pfad` ist fuer Tests ueberschreibbar.
static func laden_regeln(pfad: String = REGELN_PFAD) -> Dictionary:
	var ergebnis: Dictionary = NOTFALL.duplicate(true)
	if not FileAccess.file_exists(pfad):
		return ergebnis
	var text: String = FileAccess.get_file_as_string(pfad)
	var roh: Variant = JSON.parse_string(text)
	if roh is Dictionary:
		for schluessel in (roh as Dictionary):
			if String(schluessel).begins_with("_"):
				continue
			var wert: Variant = (roh as Dictionary)[schluessel]
			if wert is Dictionary and ergebnis.get(schluessel) is Dictionary:
				(ergebnis[schluessel] as Dictionary).merge(wert as Dictionary, true)
			else:
				ergebnis[schluessel] = wert
	return ergebnis


static func grenze(regeln: Dictionary, name: String) -> int:
	return int((regeln.get("grenzen", {}) as Dictionary).get(name, 0))


# --- Hilfen -----------------------------------------------------------------

## Zahl lesen; alles andere (Text, null, NaN, Unendlich) ergibt den Ersatzwert.
static func zahl(wert: Variant, ersatz: float) -> float:
	if wert is float or wert is int:
		var f: float = float(wert)
		if is_nan(f) or is_inf(f):
			return ersatz
		return f
	return ersatz


## Farbe lesen: Hex-Text mit oder ohne '#'. Sonst `ersatz`.
static func farbe(wert: Variant, ersatz: Color) -> Color:
	if wert is String or wert is StringName:
		var s: String = String(wert).strip_edges()
		if not s.is_empty() and Color.html_is_valid(s):
			return Color(s)
	return ersatz


static func hat_farbe(wert: Variant) -> bool:
	return (wert is String or wert is StringName) and Color.html_is_valid(String(wert).strip_edges())


## Achse lesen: "x"/"y"/"z", [x,y,z] oder {x,y,z}. Ergebnis normiert, sonst `ersatz`.
static func achse(wert: Variant, ersatz: Vector3) -> Vector3:
	var v: Vector3 = Vector3.ZERO
	if wert is String or wert is StringName:
		match String(wert).strip_edges().to_lower():
			"x": v = Vector3.RIGHT
			"y": v = Vector3.UP
			"z": v = Vector3.BACK
			"-x": v = Vector3.LEFT
			"-y": v = Vector3.DOWN
			"-z": v = Vector3.FORWARD
	elif wert is Array and (wert as Array).size() >= 3:
		var a: Array = wert as Array
		v = Vector3(zahl(a[0], 0.0), zahl(a[1], 0.0), zahl(a[2], 0.0))
	elif wert is Dictionary:
		var d: Dictionary = wert as Dictionary
		v = Vector3(zahl(d.get("x", 0.0), 0.0), zahl(d.get("y", 0.0), 0.0), zahl(d.get("z", 0.0), 0.0))
	if v.length_squared() < 0.0001:
		return ersatz
	return v.normalized()


# --- licht.himmel -----------------------------------------------------------

## Himmelsverlauf. Leer = kein Himmel. Verstanden: {oben, unten} (D1) sowie
## {zenit, horizont}, {top, bottom} oder ein Array [oben, unten].
## Optional: sterne (Zahl, true oder {anzahl, groesse, farbe, seed}) und
## mond (true oder {x, y, groesse, farbe}); Positionen als Anteil der Bildschirmflaeche.
static func himmel(licht: Dictionary, regeln: Dictionary) -> Dictionary:
	var roh: Variant = licht.get("himmel", null)
	var oben_roh: Variant = null
	var unten_roh: Variant = null
	var d: Dictionary = {}
	if roh is Dictionary:
		d = roh as Dictionary
		oben_roh = d.get("oben", d.get("zenit", d.get("top", null)))
		unten_roh = d.get("unten", d.get("horizont", d.get("bottom", null)))
	elif roh is Array and (roh as Array).size() >= 2:
		oben_roh = (roh as Array)[0]
		unten_roh = (roh as Array)[1]
	else:
		return {}
	if not hat_farbe(oben_roh) and not hat_farbe(unten_roh):
		return {}
	var hintergrund: Color = farbe(licht.get("hintergrund", null), Color.BLACK)
	var oben: Color = farbe(oben_roh, farbe(unten_roh, hintergrund))
	var unten: Color = farbe(unten_roh, oben)
	var r: Dictionary = regeln.get("himmel", {}) as Dictionary
	var ergebnis: Dictionary = {"oben": oben, "unten": unten, "sterne": {}, "mond": {},
		"vorn": d.get("vorn", false) is bool and bool(d.get("vorn", false))}

	var sterne_roh: Variant = d.get("sterne", null)
	var max_sterne: int = grenze(regeln, "max_sterne")
	var anzahl: int = 0
	var sd: Dictionary = {}
	if sterne_roh is Dictionary:
		sd = sterne_roh as Dictionary
		anzahl = int(zahl(sd.get("anzahl", sd.get("menge", 24)), 24.0))
	elif sterne_roh is float or sterne_roh is int:
		anzahl = int(zahl(sterne_roh, 0.0))
	elif sterne_roh is bool and sterne_roh:
		anzahl = 24
	anzahl = clampi(anzahl, 0, max_sterne)
	if anzahl > 0:
		ergebnis["sterne"] = {
			"anzahl": anzahl,
			"groesse": maxf(0.5, zahl(sd.get("groesse", null), zahl(r.get("sterne_groesse", null), 1.5))),
			"farbe": farbe(sd.get("farbe", null), farbe(r.get("sterne_farbe", null), Color.WHITE)),
			"seed": int(zahl(sd.get("seed", null), zahl(r.get("sterne_seed", null), 1.0))),
			"alpha_min": clampf(zahl(r.get("sterne_alpha_min", null), 0.4), 0.0, 1.0),
			"alpha_max": clampf(zahl(r.get("sterne_alpha_max", null), 0.9), 0.0, 1.0),
			"bis_hoehe": clampf(zahl(r.get("sterne_bis_hoehe", null), 0.7), 0.05, 1.0),
		}

	var mond_roh: Variant = d.get("mond", null)
	var md: Dictionary = {}
	var mond_an: bool = false
	if mond_roh is Dictionary:
		md = mond_roh as Dictionary
		mond_an = true
	elif mond_roh is bool and mond_roh:
		mond_an = true
	if mond_an:
		ergebnis["mond"] = {
			"x": clampf(zahl(md.get("x", null), zahl(r.get("mond_x", null), 0.8)), 0.0, 1.0),
			"y": clampf(zahl(md.get("y", null), zahl(r.get("mond_y", null), 0.1)), 0.0, 1.0),
			"groesse": clampf(zahl(md.get("groesse", null), zahl(r.get("mond_groesse", null), 24.0)), 4.0, 120.0),
			"farbe": farbe(md.get("farbe", null), farbe(r.get("mond_farbe", null), Color.WHITE)),
			"halo": zahl(r.get("mond_halo", null), 2.0),
			"halo_alpha": clampf(zahl(r.get("mond_halo_alpha", null), 0.1), 0.0, 1.0),
		}
	return ergebnis


# --- licht.glow -------------------------------------------------------------

## Glow. Leer = aus. `true` = Standardwerte aus lebendig.json, eine Zahl = Intensitaet,
## ein Dictionary = {intensitaet, staerke, schwelle, bloom} (auch englisch).
static func glow(licht: Dictionary, regeln: Dictionary) -> Dictionary:
	var roh: Variant = licht.get("glow", null)
	var r: Dictionary = regeln.get("glow", {}) as Dictionary
	var d: Dictionary = {}
	if roh is Dictionary:
		d = roh as Dictionary
	elif roh is bool and roh:
		d = {}
	elif roh is float or roh is int:
		if zahl(roh, 0.0) <= 0.0:
			return {}
		d = {"intensitaet": roh}
	else:
		return {}
	if d.has("an") and d["an"] is bool and not d["an"]:
		return {}
	var deckel: float = zahl(r.get("hdr_deckel", null), 4.0)
	return {
		"intensitaet": clampf(zahl(d.get("intensitaet", d.get("intensity", null)), zahl(r.get("intensitaet", null), 0.6)), 0.0, 2.0),
		"staerke": clampf(zahl(d.get("staerke", d.get("strength", null)), zahl(r.get("staerke", null), 0.9)), 0.0, 2.0),
		"schwelle": clampf(zahl(d.get("schwelle", d.get("hdr_threshold", null)), zahl(r.get("schwelle", null), 0.9)), 0.0, deckel),
		"bloom": clampf(zahl(d.get("bloom", null), zahl(r.get("bloom", null), 0.0)), 0.0, 1.0),
		"hdr_deckel": deckel,
	}


# --- licht.partikel ---------------------------------------------------------

## Partikel-Systeme. Quellen: licht.partikel (D1) und optional ein Array auf
## Weltebene. Unbekannte Typen und kaputte Eintraege fallen weg; die Menge ist
## gedeckelt, die Anzahl der Systeme auch.
static func partikel(quellen: Array, regeln: Dictionary) -> Array[Dictionary]:
	var ergebnis: Array[Dictionary] = []
	var typen: Dictionary = regeln.get("partikel_typen", {}) as Dictionary
	var max_systeme: int = grenze(regeln, "max_partikel_systeme")
	var max_menge: int = grenze(regeln, "max_partikel_menge")
	for quelle in quellen:
		if not (quelle is Array):
			continue
		for roh in (quelle as Array):
			if ergebnis.size() >= max_systeme:
				return ergebnis
			if not (roh is Dictionary):
				continue
			var e: Dictionary = roh as Dictionary
			var typ_roh: Variant = e.get("typ", e.get("art", null))
			if not (typ_roh is String or typ_roh is StringName):
				continue
			var typ: String = String(PARTIKEL_ALIAS.get(String(typ_roh).strip_edges().to_lower(), ""))
			if typ.is_empty() or not typen.has(typ):
				continue
			var t: Dictionary = typen[typ] as Dictionary
			var menge: int = clampi(int(zahl(e.get("menge", e.get("anzahl", null)), 8.0)), 1, maxi(1, max_menge))
			# Einzelne Werte des Typs lassen sich je System ueberschreiben (Groesse, Alpha, Tempo ...).
			t = t.duplicate()
			for ueber in ["groesse", "groesse_ende", "alpha", "lebensdauer", "tempo_min", "tempo_max",
					"streuung", "schwerkraft", "vol_y"]:
				var wert: Variant = e.get(ueber, null)
				if (wert is float or wert is int) and not is_nan(float(wert)) and not is_inf(float(wert)):
					t[ueber] = float(wert)
			var rr: Variant = e.get("richtung", null)
			if rr is Array and (rr as Array).size() >= 3:
				t["richtung"] = rr
			ergebnis.append({
				"typ": typ,
				"x": zahl(e.get("x", null), 0.0),
				"y": zahl(e.get("y", e.get("hoehe", null)), zahl(t.get("hoehe", null), 0.0)),
				"z": zahl(e.get("z", null), 0.0),
				"menge": menge,
				"radius": maxf(0.0, zahl(e.get("radius", null), zahl(t.get("radius", null), 1.0))),
				"intervall": maxf(0.0, zahl(e.get("intervall", null), zahl(t.get("intervall", null), 0.0))),
				"farbe": farbe(e.get("farbe", null), farbe(t.get("farbe", null), Color.WHITE)),
				"werte": t,
			})
	return ergebnis


# --- kulisse[].animation / emission_puls -------------------------------------

## Animation eines Kulissen-Eintrags. Leer = keine. `animation` darf ein Dictionary,
## ein Text (nur der Typ) oder ein Array (erstes brauchbares Element) sein.
static func animation(eintrag: Dictionary, regeln: Dictionary) -> Dictionary:
	var roh: Variant = eintrag.get("animation", null)
	if roh is Array:
		var gefunden: Variant = null
		for e in (roh as Array):
			if e is Dictionary or e is String:
				gefunden = e
				break
		roh = gefunden
	var d: Dictionary = {}
	if roh is Dictionary:
		d = roh as Dictionary
	elif roh is String or roh is StringName:
		d = {"typ": roh}
	else:
		return {}
	var typ_roh: Variant = d.get("typ", d.get("art", null))
	if not (typ_roh is String or typ_roh is StringName):
		return {}
	var typ: String = String(TYP_ALIAS.get(String(typ_roh).strip_edges().to_lower(), ""))
	if typ.is_empty():
		return {}
	var r: Dictionary = (regeln.get("animation", {}) as Dictionary).get(typ, {}) as Dictionary
	var ergebnis: Dictionary = {
		"typ": typ,
		"tempo": zahl(d.get("tempo", d.get("geschwindigkeit", null)), zahl(r.get("tempo", null), 1.0)),
		"achse": achse(d.get("achse", null), achse(r.get("achse", null), Vector3.UP)),
		"teil": String(d.get("teil", "")) if (d.get("teil", "") is String) else "",
		"weite": maxf(0.01, zahl(d.get("weite", d.get("strecke", null)), zahl(r.get("weite", null), 1.0))),
		"winkel": zahl(d.get("winkel", null), zahl(r.get("winkel", null), 4.0)),
		"phase": zahl(d.get("phase", null), 0.0),
	}
	if typ == "fahren":
		var punkte: PackedVector3Array = route(d.get("route", null), grenze(regeln, "max_route_punkte"))
		if punkte.size() < 2:
			return {}
		var modus: String = "schleife"
		var m: Variant = d.get("modus", r.get("modus", "schleife"))
		if m is String:
			modus = String(m).to_lower()
		if not (modus in ["schleife", "hin_und_her", "einmal"]):
			modus = "schleife"
		ergebnis["route"] = punkte
		ergebnis["warten"] = route_warten(d.get("route", null), punkte.size())
		ergebnis["modus"] = modus
		ergebnis["pause"] = maxf(0.0, zahl(d.get("pause", d.get("intervall", null)), zahl(r.get("pause", null), 0.0)))
		ergebnis["blick_versatz"] = zahl(d.get("blick_versatz", null), zahl(r.get("blick_versatz", null), 0.0))
		ergebnis["tempo"] = maxf(0.05, absf(ergebnis["tempo"] as float))
	return ergebnis


## Routenpunkte lesen: [{x, z}], [[x, z]] oder [{x, y, z}]. Ungueltige Punkte fallen weg.
static func route(roh: Variant, maximum: int) -> PackedVector3Array:
	var punkte := PackedVector3Array()
	if not (roh is Array):
		return punkte
	for p in (roh as Array):
		if punkte.size() >= maximum:
			break
		if p is Dictionary:
			var d: Dictionary = p as Dictionary
			if (d.get("x", null) is float or d.get("x", null) is int) and (d.get("z", null) is float or d.get("z", null) is int):
				punkte.append(Vector3(zahl(d["x"], 0.0), zahl(d.get("y", null), 0.0), zahl(d["z"], 0.0)))
		elif p is Array and (p as Array).size() >= 2:
			var a: Array = p as Array
			if (a[0] is float or a[0] is int) and (a[1] is float or a[1] is int):
				punkte.append(Vector3(zahl(a[0], 0.0), 0.0, zahl(a[1], 0.0)))
	return punkte


## Wartezeit je Punkt (Schluessel `warten`, wie bei den Bewohner-Routen).
static func route_warten(roh: Variant, anzahl: int) -> PackedFloat32Array:
	var w := PackedFloat32Array()
	w.resize(anzahl)
	if not (roh is Array):
		return w
	var i: int = 0
	for p in (roh as Array):
		if i >= anzahl:
			break
		if p is Dictionary and ((p as Dictionary).get("x", null) is float or (p as Dictionary).get("x", null) is int):
			w[i] = maxf(0.0, zahl((p as Dictionary).get("warten", null), 0.0))
			i += 1
		elif p is Array and (p as Array).size() >= 2:
			i += 1
	return w


## Emission-Puls eines Kulissen-Eintrags. Leer = keiner. `true` nimmt die
## Standardwerte, eine Zahl ist die Frequenz in Hz, ein Dictionary
## {hz, min, max, form, versatz, teil, farbe}.
static func emission_puls(eintrag: Dictionary, regeln: Dictionary) -> Dictionary:
	var roh: Variant = eintrag.get("emission_puls", null)
	var r: Dictionary = regeln.get("emission_puls", {}) as Dictionary
	var d: Dictionary = {}
	if roh is Dictionary:
		d = roh as Dictionary
	elif roh is bool and roh:
		d = {}
	elif roh is float or roh is int:
		d = {"hz": roh}
	else:
		return {}
	var hz: float = zahl(d.get("hz", d.get("frequenz", null)), zahl(r.get("hz", null), 0.5))
	if hz <= 0.0:
		return {}
	var kleinster: float = maxf(0.0, zahl(d.get("min", null), zahl(r.get("min", null), 0.4)))
	var groesster: float = maxf(kleinster, zahl(d.get("max", null), zahl(r.get("max", null), 1.6)))
	var form: String = "sinus"
	var f: Variant = d.get("form", r.get("form", "sinus"))
	if f is String:
		form = String(f).to_lower()
	if not (form in ["sinus", "blinken", "flackern"]):
		form = "sinus"
	return {
		"hz": hz,
		"min": kleinster,
		"max": groesster,
		"form": form,
		"versatz": zahl(d.get("versatz", null), zahl(r.get("versatz", null), 0.0)),
		"teil": String(d.get("teil", "")) if (d.get("teil", "") is String) else "",
		"farbe": farbe(d.get("farbe", null), Color(0, 0, 0, 0)),
		"mit_farbe": hat_farbe(d.get("farbe", null)),
	}


# --- Mitarbeiter-Figuren (crew) und Kunden ------------------------------------

## Darstellung eines Rangs (1..n): {skala, kopfhoerer, brosche, ring}. Leer = Rang ausserhalb.
static func crew_rang_look(rang: int, regeln: Dictionary) -> Dictionary:
	var liste: Variant = (regeln.get("crew", {}) as Dictionary).get("raenge", [])
	if not (liste is Array) or rang < 1 or rang > (liste as Array).size():
		return {}
	var e: Variant = (liste as Array)[rang - 1]
	if not (e is Dictionary):
		return {}
	var d: Dictionary = e as Dictionary
	return {
		"skala": clampf(zahl(d.get("skala", null), 1.0), 0.5, 2.0),
		"kopfhoerer": d.get("kopfhoerer", false) is bool and bool(d.get("kopfhoerer", false)),
		"brosche": d.get("brosche", false) is bool and bool(d.get("brosche", false)),
		"ring": d.get("ring", false) is bool and bool(d.get("ring", false)),
	}


## Platz der Figur an einer Station: {x, z, blick} (Grad), relativ zur Stationsposition.
## Quelle: worlds.json figuren.plaetze[<station>], sonst crew.platz_standard.
static func crew_platz(figuren: Dictionary, station: String, regeln: Dictionary) -> Dictionary:
	var std: Dictionary = (regeln.get("crew", {}) as Dictionary).get("platz_standard", {}) as Dictionary
	var eigen: Dictionary = (figuren.get("plaetze", {}) as Dictionary).get(station, {}) as Dictionary
	return {
		"x": zahl(eigen.get("x", null), zahl(std.get("x", null), 0.0)),
		"z": zahl(eigen.get("z", null), zahl(std.get("z", null), 0.0)),
		"blick": zahl(eigen.get("blick", null), zahl(std.get("blick", null), 180.0)),
	}


## Modellname (ohne .glb) fuer die Figur einer Station. Reihenfolge: theme crew.<station>.figur,
## portrait, das schon ein Modellname ist, portrait ueber absender_figur, sonst ein Ersatz
## (reihum, damit zwei Ersatzfiguren nicht gleich aussehen).
static func crew_modell(eintrag: Dictionary, absender_figur: Dictionary, regeln: Dictionary, nr: int) -> String:
	var direkt: String = String(eintrag.get("figur", ""))
	if not direkt.is_empty():
		return direkt
	var portrait: String = String(eintrag.get("portrait", ""))
	if portrait.begins_with("figur_"):
		return portrait
	if absender_figur.has(portrait):
		return String(absender_figur[portrait])
	var ersatz: Array = (regeln.get("crew", {}) as Dictionary).get("ersatz_modelle", []) as Array
	return String(ersatz[nr % ersatz.size()]) if not ersatz.is_empty() else ""


## Rangtitel (I..III) aus theme crew.<station>.raenge, "" wenn es ihn nicht gibt.
static func crew_titel(eintrag: Dictionary, rang: int) -> String:
	var liste: Variant = eintrag.get("raenge", [])
	if liste is Array and rang >= 1 and rang <= (liste as Array).size():
		return String((liste as Array)[rang - 1])
	return ""


static func crew_arbeit(station: String, regeln: Dictionary) -> String:
	return String(((regeln.get("crew", {}) as Dictionary).get("arbeit", {}) as Dictionary).get(station, "wippen"))


## Abstand zwischen zwei Kunden in Sekunden; sinkt (logarithmisch) mit dem Durchsatz.
## 0 Durchsatz oder fehlende Daten -> -1 (keine Kunden).
static func kunden_intervall(durchsatz: float, regeln: Dictionary) -> float:
	var k: Dictionary = regeln.get("kunden", {}) as Dictionary
	if k.is_empty() or durchsatz <= 0.0 or is_nan(durchsatz) or is_inf(durchsatz):
		return -1.0
	var klein: float = maxf(0.001, zahl(k.get("durchsatz_klein", null), 1.0))
	var voll: float = maxf(klein * 2.0, zahl(k.get("durchsatz_voll", null), 1.0e6))
	var t: float = clampf((log(maxf(durchsatz, klein)) - log(klein)) / (log(voll) - log(klein)), 0.0, 1.0)
	return lerpf(zahl(k.get("intervall_langsam", null), 9.0), zahl(k.get("intervall_schnell", null), 2.6), t)


## Weg der Kunden einer Welt (worlds.json figuren.kunden {start, via[], ziel}): {start, ziel, route}.
## `route` = start, alle via-Punkte, ziel. Leer = keine Kunden. Ein Welt-Schluessel `eingang`
## {x, z} ueberschreibt das Ziel.
static func kunden_weg(welt: Dictionary) -> Dictionary:
	var f: Dictionary = (welt.get("figuren", {}) as Dictionary).get("kunden", {}) as Dictionary
	var start: Variant = f.get("start", null)
	var ziel: Variant = f.get("ziel", null)
	var tor: Variant = welt.get("eingang", null)
	if tor is Dictionary and (tor as Dictionary).has("x") and (tor as Dictionary).has("z"):
		ziel = tor
	if not (start is Dictionary) or not (ziel is Dictionary):
		return {}
	var punkt := func(d: Dictionary) -> Vector3:
		return Vector3(zahl(d.get("x", null), 0.0), 0.0, zahl(d.get("z", null), 0.0))
	var route := PackedVector3Array()
	route.append(punkt.call(start as Dictionary))
	var via: Variant = f.get("via", [])
	if via is Array:
		for v in (via as Array):
			if v is Dictionary:
				route.append(punkt.call(v as Dictionary))
	route.append(punkt.call(ziel as Dictionary))
	return {"start": route[0], "ziel": route[route.size() - 1], "route": route}
