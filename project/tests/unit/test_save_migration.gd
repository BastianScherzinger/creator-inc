## Prueft die Migrationskette gegen EINGEFRORENE Spielstaende.
##
## Das ist der Test, der ADR-006 von einer Absichtserklaerung zu einer Zusage
## macht: Ein Stand, den die App vor Monaten geschrieben hat, muss heute noch
## laden. Die Fixture in tests/fixtures/saves/ wurde damals geschrieben und
## wird nie wieder angefasst -- wer sie an ein neues Schema anpasst, hat den
## Test abgeschafft, ohne es zu merken.
extends GdUnitTestSuite

const FIXTURE_V1: String = "res://tests/fixtures/saves/save_v1.json"


func _lade_fixture(pfad: String) -> Dictionary:
	assert_bool(FileAccess.file_exists(pfad)) \
		.override_failure_message("Fixture fehlt: %s" % pfad).is_true()
	var geparst: Variant = JSON.parse_string(FileAccess.get_file_as_string(pfad))
	return geparst as Dictionary


func test_v1_stand_laedt_und_behaelt_seine_werte() -> void:
	var roh: Dictionary = _lade_fixture(FIXTURE_V1)
	var stand: SaveData = SaveData.from_dict(SaveData.migrieren(roh))

	assert_int(stand.schema_version).is_equal(SaveData.SCHEMA_VERSION)
	assert_float(stand.kapital).is_equal_approx(12480.5, 0.001)
	assert_float(stand.gesamt_verdient).is_equal_approx(48210.75, 0.001)
	assert_int(stand.letzter_zeitstempel).is_equal(1789000000)
	assert_array(stand.unlocks).contains(["unlock_transport"])


func test_v1_stufen_kommen_als_int_an() -> void:
	# JSON kennt keinen Unterschied zwischen 14 und 14.0. Ohne den Cast in
	# from_dict wanderte eine Stufe als float durch das ganze System und
	# faellt irgendwann an ganz anderer Stelle auf.
	var stand: SaveData = SaveData.from_dict(
		SaveData.migrieren(_lade_fixture(FIXTURE_V1)))
	var eintrag: Dictionary = stand.stationen["station_intake"] as Dictionary
	assert_int(eintrag["stufe"]).is_equal(14)
	assert_bool(typeof(eintrag["stufe"]) == TYPE_INT).is_true()
	assert_bool(bool(stand.stationen["station_special"]["freigeschaltet"])).is_false()


func test_v1_bekommt_die_neuen_einstellungen_mit_standardwert() -> void:
	# Wer seit Wochen ohne Ton spielt, hat das nie entschieden -- es gab die
	# Einstellung nicht. Stumm zu starten waere eine untergeschobene
	# Entscheidung.
	var stand: SaveData = SaveData.from_dict(
		SaveData.migrieren(_lade_fixture(FIXTURE_V1)))
	assert_bool(bool(stand.einstellungen.get("ton", false))).is_true()


func test_migration_laesst_die_fixture_unangetastet() -> void:
	# migrieren() darf die uebergebene Struktur nicht veraendern -- sonst
	# haengt das Ergebnis davon ab, wer vorher schon einmal migriert hat.
	var roh: Dictionary = _lade_fixture(FIXTURE_V1)
	SaveData.migrieren(roh)
	assert_int(int(roh["schema_version"])).is_equal(1)
	assert_bool(roh.has("einstellungen")).is_false()


func test_migration_ist_wiederholbar() -> void:
	var einmal: Dictionary = SaveData.migrieren(_lade_fixture(FIXTURE_V1))
	var zweimal: Dictionary = SaveData.migrieren(einmal.duplicate(true))
	assert_int(int(zweimal["schema_version"])).is_equal(SaveData.SCHEMA_VERSION)
	assert_bool(SaveData.pruefsumme(einmal) == SaveData.pruefsumme(zweimal)).is_true()


func test_stand_aus_der_zukunft_wird_abgelehnt_statt_geraten() -> void:
	# Eine heruntergestufte App darf nicht raten. Ein sauberer Abbruch ist
	# besser als ein Stand, der halb interpretiert wurde.
	var zukunft: Dictionary = _lade_fixture(FIXTURE_V1)
	zukunft["schema_version"] = SaveData.SCHEMA_VERSION + 5
	assert_bool(SaveData.migrieren(zukunft).is_empty()).is_true()


func test_runde_durch_speicherformat_veraendert_nichts() -> void:
	var stand: SaveData = SaveData.from_dict(
		SaveData.migrieren(_lade_fixture(FIXTURE_V1)))
	stand.einstellungen["ton"] = false

	var text: String = JSON.stringify(stand.to_dict(), "\t", true, true)
	var zurueck: SaveData = SaveData.from_dict(JSON.parse_string(text) as Dictionary)

	assert_float(zurueck.kapital).is_equal_approx(stand.kapital, 0.001)
	assert_int(zurueck.stationen["station_intake"]["stufe"]).is_equal(14)
	assert_bool(bool(zurueck.einstellungen["ton"])).is_false()
