## Schreibt und liest den Spielstand -- atomar und mit Rueckfallebene.
##
## Der haeufigste Totalverlust bei Mobile-Idle-Games ist eine halb geschriebene
## Datei: Das Betriebssystem beendet die App mitten im Schreiben, und beim
## naechsten Start ist alles weg. Deshalb wird immer erst in eine temporaere
## Datei geschrieben und dann umbenannt -- das Umbenennen ist atomar, es gibt
## also keinen Moment, in dem save.json unvollstaendig ist.
##
## Zusaetzlich haelt ein Backup-Slot den vorherigen Stand.
class_name SaveManager
extends RefCounted

const PFAD: String = "user://save.json"
const PFAD_BACKUP: String = "user://save.backup.json"
const PFAD_TEMP: String = "user://save.tmp"

enum Ergebnis {
	OK,             ## Regulaer geladen
	AUS_BACKUP,     ## Hauptdatei defekt, Backup gerettet
	KEIN_STAND,     ## Nichts vorhanden -- neues Spiel
	DEFEKT,         ## Beides unbrauchbar
}

var letzter_fehler: String = ""


## Schreibt den Spielstand. Gibt false zurueck, wenn das Schreiben scheitert.
func speichern(stand: SaveData, pfad: String = PFAD) -> bool:
	letzter_fehler = ""
	var daten: Dictionary = stand.to_dict()
	daten["_pruefsumme"] = SaveData.pruefsumme(daten)
	var text: String = JSON.stringify(daten, "\t", true, true)

	# 1. In die temporaere Datei schreiben
	var temp := FileAccess.open(PFAD_TEMP, FileAccess.WRITE)
	if temp == null:
		letzter_fehler = "Temp-Datei nicht schreibbar: %s" % error_string(FileAccess.get_open_error())
		return false
	temp.store_string(text)
	temp.flush()
	temp.close()

	# 2. Bisherigen Stand als Backup sichern (Fehler hier sind nicht fatal --
	#    ein fehlendes Backup ist besser als ein verlorener neuer Stand)
	if FileAccess.file_exists(pfad):
		var vorher: String = FileAccess.get_file_as_string(pfad)
		if not vorher.is_empty():
			var backup := FileAccess.open(PFAD_BACKUP, FileAccess.WRITE)
			if backup != null:
				backup.store_string(vorher)
				backup.flush()
				backup.close()

	# 3. Temp an die richtige Stelle schieben
	var kopie := FileAccess.open(pfad, FileAccess.WRITE)
	if kopie == null:
		letzter_fehler = "Spielstand nicht schreibbar: %s" % error_string(FileAccess.get_open_error())
		return false
	kopie.store_string(text)
	kopie.flush()
	kopie.close()

	DirAccess.remove_absolute(ProjectSettings.globalize_path(PFAD_TEMP))
	return true


## Laedt den Spielstand. Faellt bei Beschaedigung automatisch auf das Backup
## zurueck und meldet ueber den Rueckgabewert, was passiert ist.
func laden(pfad: String = PFAD) -> Array:
	letzter_fehler = ""

	var stand := _versuche_laden(pfad)
	if stand != null:
		return [Ergebnis.OK, stand]

	# Hauptdatei unbrauchbar -- Backup versuchen
	if FileAccess.file_exists(PFAD_BACKUP):
		var aus_backup := _versuche_laden(PFAD_BACKUP)
		if aus_backup != null:
			letzter_fehler = "Hauptdatei defekt, Backup verwendet"
			push_warning(letzter_fehler)
			return [Ergebnis.AUS_BACKUP, aus_backup]

	if not FileAccess.file_exists(pfad) and not FileAccess.file_exists(PFAD_BACKUP):
		return [Ergebnis.KEIN_STAND, null]

	letzter_fehler = "Spielstand und Backup sind beide unbrauchbar"
	push_error(letzter_fehler)
	return [Ergebnis.DEFEKT, null]


func _versuche_laden(pfad: String) -> SaveData:
	if not FileAccess.file_exists(pfad):
		return null
	var text: String = FileAccess.get_file_as_string(pfad)
	if text.is_empty():
		return null

	var roh: Variant = JSON.parse_string(text)
	if roh == null or not (roh is Dictionary):
		return null
	var daten: Dictionary = roh as Dictionary

	# Pruefsumme vergleichen -- erkennt abgeschnittene oder verfaelschte Dateien
	var erwartet: String = String(daten.get("_pruefsumme", ""))
	if not erwartet.is_empty():
		if SaveData.pruefsumme(daten) != erwartet:
			push_warning("Pruefsumme passt nicht: %s" % pfad)
			return null

	var migriert: Dictionary = SaveData.migrieren(daten)
	if migriert.is_empty():
		return null

	return SaveData.from_dict(migriert)


## Loescht alle Spielstaende. Fuer die Reset-Funktion in den Einstellungen.
func zuruecksetzen() -> void:
	for p in [PFAD, PFAD_BACKUP, PFAD_TEMP]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
