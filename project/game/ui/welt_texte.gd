## Setzt Texte fuer die Menues aus Thema, Bedienwoertern und Kerndaten zusammen.
##
## Ziele und Boni werden ERZEUGT, nicht ausgeschrieben: "Schnitt auf Stufe 10"
## kommt aus dem Namen der Station im Thema und der 10 aus der Balance. Stuende
## der Satz fertig im Thema, muesste bei jeder Balance-Aenderung jemand daran
## denken, den Text mitzuaendern -- und irgendwann stuende dort "Stufe 10",
## waehrend das Ziel bei 12 liegt.
class_name WeltTexte
extends RefCounted


static func station_name(thema: ThemeData, id: StringName) -> String:
	return thema.station_name(id) if thema != null else String(id)


static func station_kurz(thema: ThemeData, id: StringName) -> String:
	if thema == null:
		return ""
	var st: Dictionary = thema.abschnitt("stationen").get(String(id), {}) as Dictionary
	return String(st.get("kurz", st.get("beschreibung", "")))


static func einheit(thema: ThemeData, id: StringName) -> String:
	if thema == null:
		return ""
	var st: Dictionary = thema.abschnitt("stationen").get(String(id), {}) as Dictionary
	return String(st.get("einheit", ""))


static func platz_name(thema: ThemeData, station_id: StringName, platz_id: StringName) -> String:
	return String(_platz(thema, station_id, platz_id).get("name", String(platz_id)))


## Name der Modellstufe (0 = Anfangszustand, 1..3 = Sterne).
static func platz_stufe_name(thema: ThemeData, station_id: StringName, platz_id: StringName,
		modellstufe: int) -> String:
	var stufen: Array = _platz(thema, station_id, platz_id).get("stufen", []) as Array
	if stufen.is_empty():
		return platz_name(thema, station_id, platz_id)
	return String(stufen[clampi(modellstufe, 0, stufen.size() - 1)])


static func _platz(thema: ThemeData, station_id: StringName, platz_id: StringName) -> Dictionary:
	if thema == null:
		return {}
	var station: Dictionary = thema.abschnitt("ausstattung").get(String(station_id), {}) as Dictionary
	return station.get(String(platz_id), {}) as Dictionary


## Nebenraeume (Zonen ohne Bereich und ohne Start): Name und Satz aus theme.json -> "nebenraeume".
static func nebenraum(thema: ThemeData, zone_id: StringName, feld: String) -> String:
	if thema == null:
		return ""
	var z: Dictionary = thema.abschnitt("nebenraeume").get(String(zone_id), {}) as Dictionary
	return String(z.get(feld, ""))


static func bereich(thema: ThemeData, bereich_id: StringName, feld: String) -> String:
	if thema == null:
		return ""
	var b: Dictionary = thema.abschnitt("bereiche").get(String(bereich_id), {}) as Dictionary
	return String(b.get(feld, ""))


## "Alles ×1,25" oder "Aufnahme ×1,5" -- aus den Balance-Daten des Bereichs.
static func bonus(thema: ThemeData, kern: GameCore, bereich_id: StringName) -> String:
	var teile: PackedStringArray = []
	var b: Dictionary = kern.bereiche.bonus(bereich_id)
	if not b.is_empty():
		var faktor: String = ("%.2f" % float(b.get("faktor", 1.0))).rstrip("0").rstrip(".").replace(".", ",")
		var ziel: String = String(b.get("ziel", AreaSystem.BONUS_ALLE))
		if ziel == AreaSystem.BONUS_ALLE:
			teile.append(UiText.t("bonus_alle") % faktor)
		else:
			teile.append(UiText.t("bonus_station") % [station_name(thema, StringName(ziel)), faktor])
	var unlock_id: StringName = kern.bereiche.schaltet_frei(bereich_id)
	var station_id: StringName = GameCore._station_zu_freischaltung(unlock_id)
	if station_id != &"":
		teile.append(UiText.t("schaltet_frei") % station_name(thema, station_id))
	return " · ".join(teile)


## Anzeigename einer Ziel-Kette ("start", "bereich_1" ...) aus `ketten` der Themendatei; leer, wenn keiner da ist.
static func kette(thema: ThemeData, kette_id: String) -> String:
	if thema == null:
		return ""
	return String(thema.abschnitt("ketten").get(kette_id, ""))


static func ziel(thema: ThemeData, z: Dictionary) -> String:
	# Eigene Namen (Missionen) gehen vor: "ziele" -> <ziel_id> in der Themendatei.
	if thema != null:
		var eigen: Variant = thema.abschnitt("ziele").get(String(z.get("id", "")), null)
		if eigen is String and not String(eigen).is_empty():
			return String(eigen)
		if eigen is Dictionary and not String((eigen as Dictionary).get("name", "")).is_empty():
			return String((eigen as Dictionary).get("name", ""))
	var formate: Dictionary = thema.abschnitt("ziel_formate") if thema != null else {}
	var typ: String = String(z.get("typ", ""))
	var format: String = String(formate.get(typ, typ))
	var wert: int = int(z.get("wert", 0))
	match typ:
		"station_stufe":
			return format % [station_name(thema, StringName(String(z.get("station", "")))), wert]
		"ausstattung_stufe":
			var sid := StringName(String(z.get("station", "")))
			return format % [station_name(thema, sid),
				platz_name(thema, sid, StringName(String(z.get("platz", "")))), wert]
		"bereich":
			return format % bereich(thema, StringName(String(z.get("bereich", ""))), "name")
		"verdient":
			return format % UiStil.zahl(float(z.get("wert", 0.0)))
		"abschluss":
			return format
	if format.contains("%d"):
		return format % wert
	return format


static func absender(thema: ThemeData, schluessel: String) -> String:
	if thema == null:
		return schluessel
	return String(thema.abschnitt("absender").get(schluessel, schluessel))


static func nachricht(thema: ThemeData, nachricht_id: String) -> Dictionary:
	if thema == null:
		return {}
	return thema.abschnitt("nachrichten").get(nachricht_id, {}) as Dictionary


## Das Welt-Ziel ("Der Gaming-PC") fuer die Kopfleiste; ohne Eintrag der Untertitel der Welt.
static func welt_ziel(thema: ThemeData) -> String:
	if thema == null:
		return ""
	var z: String = thema.text("welt_ziel")
	return z if not z.is_empty() else thema.welt_untertitel


## Name einer Zwischenmarke auf dem Welt-Ziel-Balken (Schluessel = Marken-ID, z. B.
## "fortschritt_25"); leer, wenn das Thema keine benennt.
static func marke_name(thema: ThemeData, marke_id: String) -> String:
	if thema == null:
		return ""
	return String(thema.abschnitt("marken_namen").get(marke_id, ""))


## Halbsatz "warum" zu einem Zieltyp (theme.json -> ziel_warum); leer, wenn keiner da ist.
static func ziel_warum(thema: ThemeData, typ: String) -> String:
	if thema == null:
		return ""
	return String(thema.abschnitt("ziel_warum").get(typ, ""))


static func menue(thema: ThemeData, schluessel: String) -> String:
	if thema == null:
		return schluessel
	return String(thema.abschnitt("menue").get(schluessel, schluessel))


static func dauer(sekunden: float) -> String:
	var stunden: int = int(sekunden / 3600.0)
	var minuten: int = int(fmod(sekunden, 3600.0) / 60.0)
	if stunden > 0:
		return UiText.t("std_min") % [stunden, minuten]
	return UiText.t("min") % maxi(minuten, 1)
