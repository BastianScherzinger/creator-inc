## Werkzeug zum Einstellen einer Welt mit Abschluss "alles": spielt Varianten
## der Balance durch und druckt die Meilensteine nebeneinander.
##
## Aufruf: godot_console --headless --path project -s res://tools/abschluss_tuning.gd
## Die Varianten stehen unten -- dieses Werkzeug ist ein Messgeraet, keine Balance.
extends SceneTree

const VARIANTEN: Array = [
	{"name": "basis"},
	{"name": "i2.25", "item_wachstum": 2.25},
	{"name": "i2.2", "item_wachstum": 2.2},
	{"name": "i2.25 b0.6", "item_wachstum": 2.25, "bereich_kosten": 0.6},
	{"name": "i2.3 b0.5", "item_wachstum": 2.3, "bereich_kosten": 0.5},
]


func _init() -> void:
	var text: String = FileAccess.get_file_as_string("res://data/balance/zimmer.json")
	for v in VARIANTEN:
		var roh: Dictionary = JSON.parse_string(text) as Dictionary
		_wende_an(roh, v as Dictionary)
		var balance := BalanceData.aus_text(JSON.stringify(roh))
		var sim := AbschlussSim.new(balance, 0)
		sim.laufen()
		var e: Dictionary = sim.ereignisse
		print("%-22s ausst %s  b1 %s  b2 %s  b3 %s  b4 %s  b5 %s  FERTIG %s  Luecke E %.0f G %.0f  Ende %.0f/s" % [
			v["name"], AbschlussSim._zeit(e.get("erste_ausstattung", -1)),
			AbschlussSim._zeit(e.get("bereich_1", -1)), AbschlussSim._zeit(e.get("bereich_2", -1)),
			AbschlussSim._zeit(e.get("bereich_3", -1)), AbschlussSim._zeit(e.get("bereich_4", -1)),
			AbschlussSim._zeit(e.get("bereich_5", -1)), AbschlussSim._zeit(e.get("abschluss", -1)),
			sim.luecke_einstieg, sim.luecke_gesamt, sim.kern.einkommen_pro_sekunde()])
	quit(0)


func _wende_an(roh: Dictionary, v: Dictionary) -> void:
	for st in (roh["stationen"] as Dictionary).values():
		var d: Dictionary = st as Dictionary
		if v.has("station_wachstum"):
			d["wachstum"] = float(v["station_wachstum"])
		if v.has("meilenstein_faktor"):
			d["meilenstein_faktor"] = float(v["meilenstein_faktor"])
		for p in (d.get("ausstattung", {}) as Dictionary).values():
			var pd: Dictionary = p as Dictionary
			if v.has("item_wachstum"):
				pd["wachstum"] = float(v["item_wachstum"])
			if v.has("item_kosten"):
				pd["basis_kosten"] = float(pd["basis_kosten"]) * float(v["item_kosten"])
			if v.has("stern_faktor"):
				pd["stern_faktor"] = float(v["stern_faktor"])
			if v.has("bonus_je_stufe"):
				pd["bonus_je_stufe"] = float(v["bonus_je_stufe"])
	if v.has("bereich_kosten"):
		for b in (roh["bereiche"] as Dictionary).values():
			(b as Dictionary)["kosten"] = float((b as Dictionary)["kosten"]) * float(v["bereich_kosten"])
