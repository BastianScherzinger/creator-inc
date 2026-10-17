## Rastert das App-Symbol aus der SVG-Quelle in die Groessen, die Play braucht.
##
## EINE Quelle, mehrere Groessen: art_source/icon/icon_quelle.svg ist das
## Original. Wer das Symbol aendert, aendert es dort und laesst dieses Skript
## laufen -- von Hand nachgezeichnete Groessen laufen sonst auseinander, und
## man merkt es erst im Store.
extends SceneTree

const ZIEL: String = "res://assets/icon/%s.png"

## Quelle -> Zielname -> Kantenlaenge.
##
## Drei Quellen, weil Android zwei verschiedene Dinge braucht: ein
## Vollbild-Symbol fuer alles Aeltere und ein ADAPTIVES aus zwei Ebenen, das
## das Betriebssystem selbst beschneidet und verschiebt.
const AUFTRAEGE: Array = [
	["icon_quelle",      "icon_512", 512],   # Store-Eintrag
	["icon_quelle",      "icon_192", 192],   # Launcher, Vollbild
	["icon_quelle",      "icon_128", 128],   # Godot-Projektsymbol
	["icon_vordergrund", "icon_adaptiv_vg", 432],
	["icon_hintergrund", "icon_adaptiv_hg", 432],
	# Die Feature-Grafik ist als einzige nicht quadratisch. Der Massstab
	# rechnet ueber die BREITE, deshalb steht hier 1024 und nicht 500.
	["feature", "feature_1024x500", 1024],
]


func _init() -> void:
	for auftrag in AUFTRAEGE:
		var quelle: String = "res://../art_source/icon/%s.svg" % String(auftrag[0])
		var name: String = String(auftrag[1])
		var kante: int = int(auftrag[2])

		var datei := FileAccess.open(quelle, FileAccess.READ)
		if datei == null:
			push_error("Symbolquelle nicht lesbar: %s" % quelle)
			quit(1)
			return
		var svg: String = datei.get_as_text()
		var bild := Image.new()
		# Die Quelle ist 432 breit -- der Massstab rechnet daraus die Zielkante.
		# Alle Quellen sind 432 breit -- ausser der Feature-Grafik, die 1024 ist.
		var quellbreite: float = 1024.0 if name.begins_with("feature") else 432.0
		var fehler: int = bild.load_svg_from_string(svg, float(kante) / quellbreite)
		if fehler != OK:
			push_error("SVG nicht lesbar (%d)" % fehler)
			quit(1)
			return
		var pfad: String = ZIEL % name
		bild.save_png(pfad)
		print("%-10s %4d x %4d" % [name, bild.get_width(), bild.get_height()])
	quit()
