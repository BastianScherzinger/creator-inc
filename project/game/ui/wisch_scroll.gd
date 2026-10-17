## Scroll-Rahmen, der sich auf dem Handy mit dem Finger wischen laesst.
##
## Ursache des Fehlers "Menues lassen sich nicht scrollen": Ein Control mit
## mouse_filter STOP (Knopf, Karte, Zeile mit gui_input) behaelt jede Beruehrung
## fuer sich und reicht den Wisch NICHT an den ScrollContainer weiter. Auf dem PC
## faellt das nicht auf (Mausrad), auf dem Handy liegt fast die ganze Flaeche aus
## Knoepfen und Karten. Darum stellt dieser Rahmen alle Nachfahren von STOP auf
## PASS: Sie bekommen den Tipp weiterhin (Knopf druecken geht), der Wisch laeuft
## aber nach oben zum Rahmen.
##
## Auch spaeter eingehaengte Kinder (Menues bauen ihre Zeilen bei jedem Oeffnen
## neu) werden erfasst: ueber das Signal des Baums und nach jedem Sortieren.
class_name WischScroll
extends ScrollContainer


func _init() -> void:
	horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	mouse_filter = Control.MOUSE_FILTER_PASS
	follow_focus = true
	# Ein Finger zittert: erst nach ein paar Pixeln gilt es als Wisch (und damit
	# nicht mehr als Tipp). Die Schwelle steht in data/ui/sheet.json.
	scroll_deadzone = int(Sheet.tipp_schwelle())
	sort_children.connect(durchlaessig_machen)
	gui_input.connect(_auf_eingabe)


func _enter_tree() -> void:
	var baum: SceneTree = get_tree()
	if baum != null and not baum.node_added.is_connected(_knoten_neu):
		baum.node_added.connect(_knoten_neu)


func _exit_tree() -> void:
	var baum: SceneTree = get_tree()
	if baum != null and baum.node_added.is_connected(_knoten_neu):
		baum.node_added.disconnect(_knoten_neu)


## Beruehrung und Wisch im Scrollbereich gehoeren dem Menue: Sie laufen weder an
## die Karte dahinter noch (am Rand der Liste) an einen Wisch-zum-Schliessen.
func _auf_eingabe(ereignis: InputEvent) -> void:
	if ereignis is InputEventScreenTouch or ereignis is InputEventScreenDrag:
		accept_event()


func _knoten_neu(knoten: Node) -> void:
	if knoten is Control and is_ancestor_of(knoten):
		_pass_setzen(knoten as Control)


## Stellt jedes STOP unterhalb dieses Rahmens auf PASS (nicht den Rahmen selbst).
func durchlaessig_machen() -> void:
	for kind in get_children():
		_rekursiv(kind)


func _rekursiv(knoten: Node) -> void:
	if knoten is Control:
		_pass_setzen(knoten as Control)
	for kind in knoten.get_children():
		_rekursiv(kind)


static func _pass_setzen(c: Control) -> void:
	if c.mouse_filter == Control.MOUSE_FILTER_STOP:
		c.mouse_filter = Control.MOUSE_FILTER_PASS
