## Die eine Effektart von "Sticker-Pop": Flaeche mit Tintenkontur und einem
## HARTEN, versetzten Schatten ohne Unschaerfe (docs/NACHT_PLAN.md 3).
##
## StyleBoxFlat zeichnet Schatten nur mit Weichzeichnung (shadow_size > 0).
## Ein Aufkleber hat aber eine scharfe Kante -- deshalb zeichnet diese Box zwei
## flache Boxen uebereinander: den Schatten versetzt, darueber die Flaeche.
##
## `druck` (0..1) ist der Eindrueck-Zustand: Die Flaeche rutscht nach unten auf
## ihren Schatten, der Schatten verschwindet. Knoepfe nutzen dafuer eine eigene
## Box im Zustand "pressed", Karten setzen den Wert kurz per Tween.
class_name StickerBox
extends StyleBox

var flaeche: StyleBoxFlat
var schatten: StyleBoxFlat
## Versatz des Schattens im Ruhezustand.
var schatten_y: float = 4.0
## Wie weit die Flaeche beim vollen Druck nach unten rutscht.
var eindruck_y: float = 3.0

var druck: float = 0.0:
	set(wert):
		druck = clampf(wert, 0.0, 1.0)
		emit_changed()


func _draw(ziel: RID, rechteck: Rect2) -> void:
	if flaeche == null:
		return
	var rutschen: float = eindruck_y * druck
	var r := Rect2(rechteck.position + Vector2(0.0, rutschen), rechteck.size)
	# Der Schatten bleibt, wo er ist -- die Flaeche senkt sich auf ihn.
	var rest: float = schatten_y - rutschen
	if schatten != null and rest > 0.0:
		schatten.draw(ziel, Rect2(rechteck.position + Vector2(0.0, schatten_y), rechteck.size))
	flaeche.draw(ziel, r)


func _get_draw_rect(rechteck: Rect2) -> Rect2:
	return Rect2(rechteck.position, rechteck.size + Vector2(0.0, schatten_y))
