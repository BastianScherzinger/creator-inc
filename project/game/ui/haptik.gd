## Vibration als Rueckmeldung: ein Kauf soll sich in der Hand anfuehlen.
##
## Kurz und trocken (20 bis 60 ms) -- ein langes Brummen waere nach zehn Kaeufen
## laestig. Auf dem PC passiert nichts. Der Schalter steht in den Einstellungen
## und lebt in einer eigenen kleinen Datei, nicht im Spielstand: Eine Vorliebe
## des Geraets gehoert nicht in einen Stand, der spaeter einmal in die Cloud
## wandern koennte.
class_name Haptik
extends RefCounted

const PFAD: String = "user://haptik.cfg"
const DAUER_KAUF: int = 20
const DAUER_MENGE: int = 40
const DAUER_STERN: int = 60
const DAUER_FEIER: int = 90

static var an: bool = true
static var _geladen: bool = false


## Einmal pro Start lesen. Fehlt die Datei, bleibt es bei "an".
static func laden() -> void:
	_geladen = true
	var cfg := ConfigFile.new()
	if cfg.load(PFAD) == OK:
		an = bool(cfg.get_value("haptik", "an", true))


## Ist die Vibration an? Liest die Einstellung beim ersten Mal.
static func ist_an() -> bool:
	if not _geladen:
		laden()
	return an


static func setze(neu: bool) -> void:
	if not _geladen:
		laden()
	an = neu
	var cfg := ConfigFile.new()
	cfg.set_value("haptik", "an", an)
	cfg.save(PFAD)
	if an:
		puls(DAUER_KAUF)


static func puls(millisekunden: int) -> void:
	if not _geladen:
		laden()
	if not an:
		return
	Input.vibrate_handheld(millisekunden)
