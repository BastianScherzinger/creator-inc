## Zentrale ID-Konstanten.
##
## WICHTIG (ADR-010 / Guardrail D3): Diese IDs sind bewusst thematisch neutral.
## Sie benennen die FUNKTION in der Kette, nicht ihre Erscheinung im Spiel.
## Alle Anzeigenamen stehen ausschliesslich in data/themes/<name>/ und data/i18n/.
##
## Damit kostet ein Themenwechsel eine Datenaenderung statt eines Rewrites --
## was sich beim ersten Themenwechsel des Projekts bereits bewaehrt hat (ADR-015).
## validate.ps1 erzwingt diese Trennung mit einer Sperrwortliste.
class_name Ids
extends RefCounted

# --- Stationen der Kette -----------------------------------------------------
# Reihenfolge = Materialfluss: INTAKE -> BUFFER -> PROCESSING
const STATION_INTAKE := &"station_intake"          ## Annahme, erzeugt Auftraege
const STATION_BUFFER := &"station_buffer"          ## Puffer zwischen Annahme und Bearbeitung
const STATION_PROCESSING := &"station_processing"  ## Abarbeitung, erzeugt Erloes

# Spaeter freigeschaltet
const STATION_TRANSPORT := &"station_transport"    ## Automatisierung des Flusses
const STATION_SPECIAL := &"station_special"        ## Grossauftraege

## Die Kernkette in Flussrichtung. Der Engpass ist immer eines dieser Glieder.
const CHAIN: Array[StringName] = [
	STATION_INTAKE,
	STATION_BUFFER,
	STATION_PROCESSING,
]

## Alle Stationen inklusive der spaeter freigeschalteten.
const ALL_STATIONS: Array[StringName] = [
	STATION_INTAKE,
	STATION_BUFFER,
	STATION_PROCESSING,
	STATION_TRANSPORT,
	STATION_SPECIAL,
]

# --- Freischaltungen ---------------------------------------------------------
const UNLOCK_TRANSPORT := &"unlock_transport"
const UNLOCK_SPECIAL := &"unlock_special"
const UNLOCK_WORLD_2 := &"unlock_world_2"

## Der Umbau, der eine harte Obergrenze aufhebt (Welt 2).
##
## Bewusst KEINE Freischaltung ueber eine Schwelle, sondern ein Kauf: Die
## Aussage der Mechanik ist, dass man an dieser Stelle etwas WEGNEHMEN muss,
## statt weiter etwas hinzuzufuegen. Das kann einem kein Zaehler abnehmen.
const UNLOCK_UMBAU := &"unlock_umbau"


## Wie eine Welt endet (ADR-021).
##
## "schwelle": wie bisher ueber unlock_world_2 (Stufen gesamt).
## "alles":    alle Stationen auf Maximum, alle Ausstattung, alle Raeume.
const ABSCHLUSS_SCHWELLE := &"schwelle"
const ABSCHLUSS_ALLES := &"alles"


## Prueft, ob eine ID zu einer bekannten Station gehoert.
static func is_station(id: StringName) -> bool:
	return id in ALL_STATIONS
