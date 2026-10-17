## Prueft das Save-System -- den Teil des Spiels, bei dem ein Fehler
## Spielerdaten vernichtet.
##
## Getestet wird nicht nur der Normalfall, sondern vor allem:
## abgeschnittene Dateien, verfaelschte Pruefsummen, fehlende Dateien,
## Spielstaende aus aelteren und aus neueren Versionen.
extends GdUnitTestSuite

const TEST_PFAD: String = "user://test_save.json"

var _manager: SaveManager


func before_test() -> void:
	_manager = SaveManager.new()
	_aufraeumen()


func after_test() -> void:
	_aufraeumen()


func _aufraeumen() -> void:
	for p in [TEST_PFAD, SaveManager.PFAD_BACKUP, SaveManager.PFAD_TEMP]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(p))


func _beispielstand() -> SaveData:
	var s := SaveData.new()
	s.kapital = 1234.56
	s.gesamt_verdient = 9999.0
	s.spielzeit_sekunden = 777.5
	s.letzter_zeitstempel = 1700000000
	s.stationen = {
		String(Ids.STATION_INTAKE): {"stufe": 7, "freigeschaltet": true},
		String(Ids.STATION_BUFFER): {"stufe": 3, "freigeschaltet": true},
	}
	s.unlocks = [String(Ids.UNLOCK_TRANSPORT)]
	return s


func test_rundlauf_ist_verlustfrei() -> void:
	var original := _beispielstand()
	assert_bool(_manager.speichern(original, TEST_PFAD)).is_true()

	var ergebnis: Array = _manager.laden(TEST_PFAD)
	assert_int(ergebnis[0]).is_equal(SaveManager.Ergebnis.OK)

	var geladen: SaveData = ergebnis[1]
	assert_float(geladen.kapital).is_equal_approx(1234.56, 0.001)
	assert_float(geladen.gesamt_verdient).is_equal_approx(9999.0, 0.001)
	assert_float(geladen.spielzeit_sekunden).is_equal_approx(777.5, 0.001)
	assert_int(geladen.letzter_zeitstempel).is_equal(1700000000)
	assert_int(geladen.schema_version).is_equal(SaveData.SCHEMA_VERSION)
	assert_int((geladen.stationen[String(Ids.STATION_INTAKE)] as Dictionary)["stufe"]).is_equal(7)
	assert_bool(geladen.unlocks.has(String(Ids.UNLOCK_TRANSPORT))).is_true()


func test_ohne_datei_kommt_kein_stand() -> void:
	var ergebnis: Array = _manager.laden(TEST_PFAD)
	assert_int(ergebnis[0]).is_equal(SaveManager.Ergebnis.KEIN_STAND)
	assert_object(ergebnis[1]).is_null()


func test_abgeschnittene_datei_faellt_auf_backup_zurueck() -> void:
	# Erster Stand -> wird beim zweiten Speichern zum Backup
	var alt := _beispielstand()
	alt.kapital = 500.0
	_manager.speichern(alt, TEST_PFAD)

	var neu := _beispielstand()
	neu.kapital = 4000.0
	_manager.speichern(neu, TEST_PFAD)

	# Hauptdatei mitten im Schreiben abgeschnitten simulieren
	var f := FileAccess.open(TEST_PFAD, FileAccess.WRITE)
	f.store_string('{"schema_version": 1, "kapital": 40')
	f.close()

	var ergebnis: Array = _manager.laden(TEST_PFAD)
	assert_int(ergebnis[0]).is_equal(SaveManager.Ergebnis.AUS_BACKUP)
	var geladen: SaveData = ergebnis[1]
	# Das Backup enthaelt den vorherigen Stand
	assert_float(geladen.kapital).is_equal_approx(500.0, 0.001)


func test_verfaelschter_inhalt_wird_erkannt() -> void:
	_manager.speichern(_beispielstand(), TEST_PFAD)

	# Kapital von Hand hochsetzen, Pruefsumme unveraendert lassen
	var text: String = FileAccess.get_file_as_string(TEST_PFAD)
	var daten: Dictionary = JSON.parse_string(text)
	daten["kapital"] = 999999999.0
	var f := FileAccess.open(TEST_PFAD, FileAccess.WRITE)
	f.store_string(JSON.stringify(daten, "\t", true, true))
	f.close()

	# Ohne Backup ist der Stand damit unbrauchbar -- besser als still
	# einen verfaelschten Stand zu laden
	var ergebnis: Array = _manager.laden(TEST_PFAD)
	assert_int(ergebnis[0]).is_not_equal(SaveManager.Ergebnis.OK)


func test_leere_datei_ist_kein_gueltiger_stand() -> void:
	var f := FileAccess.open(TEST_PFAD, FileAccess.WRITE)
	f.store_string("")
	f.close()
	var ergebnis: Array = _manager.laden(TEST_PFAD)
	assert_int(ergebnis[0]).is_not_equal(SaveManager.Ergebnis.OK)


func test_zuruecksetzen_loescht_alles() -> void:
	_manager.speichern(_beispielstand(), SaveManager.PFAD)
	_manager.zuruecksetzen()
	assert_bool(FileAccess.file_exists(SaveManager.PFAD)).is_false()
	assert_bool(FileAccess.file_exists(SaveManager.PFAD_BACKUP)).is_false()


# --- Migration ---------------------------------------------------------------

func test_alter_stand_ohne_version_wird_migriert() -> void:
	# So sah ein Stand aus, bevor es die Versionierung gab
	var alt := {"kapital": 250.0, "stationen": {}}
	var migriert: Dictionary = SaveData.migrieren(alt)
	assert_int(int(migriert["schema_version"])).is_equal(SaveData.SCHEMA_VERSION)
	# Fehlende Felder wurden sinnvoll ergaenzt, nicht auf null gesetzt
	assert_float(float(migriert["gesamt_verdient"])).is_equal_approx(250.0, 0.001)
	assert_float(float(migriert["spielzeit_sekunden"])).is_equal(0.0)
	assert_bool(migriert.has("unlocks")).is_true()
	# Und das Kapital ist unangetastet
	assert_float(float(migriert["kapital"])).is_equal_approx(250.0, 0.001)


func test_aktueller_stand_bleibt_unveraendert() -> void:
	var aktuell := _beispielstand().to_dict()
	var migriert: Dictionary = SaveData.migrieren(aktuell)
	assert_int(int(migriert["schema_version"])).is_equal(SaveData.SCHEMA_VERSION)
	assert_float(float(migriert["kapital"])).is_equal_approx(1234.56, 0.001)


func test_stand_aus_neuerer_version_wird_abgelehnt() -> void:
	# App wurde heruntergestuft -- raten waere schlimmer als abbrechen
	var zukunft := {"schema_version": 99, "kapital": 1.0}
	assert_dict(SaveData.migrieren(zukunft)).is_empty()


func test_pruefsumme_ignoriert_sich_selbst() -> void:
	# Sonst waere die Summe nie stabil
	var daten := {"a": 1, "b": 2}
	var summe: String = SaveData.pruefsumme(daten)
	daten["_pruefsumme"] = summe
	assert_str(SaveData.pruefsumme(daten)).is_equal(summe)


func test_pruefsumme_aendert_sich_bei_inhaltsaenderung() -> void:
	var a: String = SaveData.pruefsumme({"kapital": 100.0})
	var b: String = SaveData.pruefsumme({"kapital": 100.01})
	assert_str(a).is_not_equal(b)
