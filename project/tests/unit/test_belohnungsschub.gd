## Prueft den Belohnungsschub im Kern.
##
## Ein zeitlich begrenzter Multiplikator ist die Stelle, an der Idle-Games
## regelmaessig auslaufen: Er wird an einer Stelle angewendet und an einer
## anderen vergessen, oder er laesst sich durch App-Wechsel vervielfachen.
## Beides steht hier.
extends GdUnitTestSuite

const TAKT: float = SimClock.TICK_DAUER


func _kern() -> GameCore:
	var kern := GameCore.new()
	# Etwas Kette, sonst ist der Durchsatz null und jeder Faktor wirkungslos.
	for id in Ids.CHAIN:
		var station: StationModel = kern.kette.station(id)
		if station != null:
			station.stufe = 8
	return kern


func _laufe(kern: GameCore, sekunden: float) -> void:
	var schritte: int = int(sekunden / TAKT)
	for i in range(schritte):
		kern.tick(TAKT)


func test_ohne_schub_ist_der_faktor_eins() -> void:
	var kern: GameCore = _kern()
	assert_bool(kern.schub_laeuft()).is_false()
	assert_float(kern.durchsatz()).is_equal_approx(kern.kette.effektiver_durchsatz(), 0.0001)


func test_schub_vervielfacht_den_durchsatz() -> void:
	var kern: GameCore = _kern()
	var vorher: float = kern.durchsatz()
	kern.starte_schub()
	assert_float(kern.durchsatz()).is_equal_approx(vorher * kern.balance.schub_faktor, 0.0001)


func test_angezeigtes_einkommen_und_tatsaechlicher_ertrag_stimmen_ueberein() -> void:
	# Der teure Fehler: Der Schub wirkt im Tick, aber die Kopfzeile zeigt
	# weiter den alten Wert -- oder umgekehrt. Der Spieler sieht dann eine
	# Zahl, die nicht passiert.
	var kern: GameCore = _kern()
	kern.starte_schub()
	var angezeigt: float = kern.einkommen_pro_sekunde()
	var vorher: float = kern.gesamt_verdient
	_laufe(kern, 10.0)
	var tatsaechlich: float = (kern.gesamt_verdient - vorher) / 10.0
	assert_float(tatsaechlich).is_equal_approx(angezeigt, angezeigt * 0.02)


func test_schub_laeuft_nach_seiner_dauer_aus() -> void:
	var kern: GameCore = _kern()
	kern.starte_schub()
	_laufe(kern, kern.balance.schub_dauer + 1.0)
	assert_bool(kern.schub_laeuft()).is_false()
	assert_float(kern.schub_faktor).is_equal_approx(1.0, 0.0001)
	assert_float(kern.durchsatz()).is_equal_approx(kern.kette.effektiver_durchsatz(), 0.0001)


func test_zweite_belohnung_verlaengert_statt_zu_ersetzen() -> void:
	# Wer zwei Belohnungen kurz hintereinander einloest, hat sie sich zweimal
	# verdient. Ersetzen waere eine stille Enteignung.
	var kern: GameCore = _kern()
	kern.starte_schub()
	_laufe(kern, 30.0)
	var rest_vorher: float = kern.schub_rest
	kern.starte_schub()
	assert_float(kern.schub_rest).is_greater(rest_vorher)


func test_schub_laesst_sich_nicht_unbegrenzt_stapeln() -> void:
	# Ohne Deckel koennte man sich einen ganzen Tag Schub anhaeufen, und die
	# Kurve, die der Balance-Simulator prueft, waere Makulatur.
	var kern: GameCore = _kern()
	for i in range(200):
		kern.starte_schub()
	assert_float(kern.schub_rest).is_less_equal(kern.balance.schub_hoechstdauer)


func test_offline_ertrag_bekommt_den_schub_nicht() -> void:
	# DIE Ausnutzung: Schub starten, App schliessen, Stunden spaeter das
	# Vielfache abholen. Der Offline-Ertrag rechnet deshalb mit dem
	# Grunddurchsatz.
	var ohne: GameCore = _kern()
	var mit: GameCore = _kern()
	mit.starte_schub()

	var ertrag_ohne: float = ohne.wende_offline_an(3600.0)
	var ertrag_mit: float = mit.wende_offline_an(3600.0)
	assert_float(ertrag_mit).is_equal_approx(ertrag_ohne, maxf(ertrag_ohne * 0.001, 0.001))


func test_schub_wird_offline_auch_nicht_verbraucht() -> void:
	# Die Kehrseite: Wenn er offline nicht wirkt, darf er auch nicht
	# ablaufen. Sonst waeren vier Minuten Schub nach einem Blick aufs
	# Handy weg.
	var kern: GameCore = _kern()
	kern.starte_schub()
	var rest_vorher: float = kern.schub_rest
	kern.wende_offline_an(7200.0)
	assert_float(kern.schub_rest).is_equal_approx(rest_vorher, 0.0001)


func test_schub_ueberlebt_speichern_und_laden() -> void:
	var kern: GameCore = _kern()
	kern.starte_schub()
	_laufe(kern, 20.0)
	var stand: SaveData = kern.to_save()

	var neu: GameCore = _kern()
	neu.from_save(stand)
	assert_float(neu.schub_rest).is_equal_approx(kern.schub_rest, 0.001)
	assert_bool(neu.schub_laeuft()).is_true()


func test_abgelaufener_schub_kommt_nicht_als_faktor_zurueck() -> void:
	# Ein Stand mit rest = 0, aber faktor = 2 waere ein dauerhafter
	# Multiplikator. So etwas entsteht durch halb geschriebene Staende.
	var kern: GameCore = _kern()
	var stand := SaveData.new()
	stand.schub = {"faktor": 2.0, "rest": 0.0}
	kern.from_save(stand)
	assert_float(kern.schub_faktor).is_equal_approx(1.0, 0.0001)


# --- K3 C1: Dauer-Boost ------------------------------------------------------------

func test_dauer_boost_dreissig_minuten_stapelbar_bis_zwei_stunden() -> void:
	var kern: GameCore = _kern()
	assert_float(kern.balance.schub_dauer).is_equal(1800.0)
	assert_float(kern.balance.schub_hoechstdauer).is_equal(7200.0)
	kern.starte_schub()
	assert_float(kern.schub_rest).is_equal_approx(1800.0, 0.001)
	kern.starte_schub()
	assert_float(kern.schub_rest).is_equal_approx(3600.0, 0.001)
	for i in range(20):
		kern.starte_schub()
	assert_float(kern.schub_rest).is_equal_approx(7200.0, 0.001)


func test_kuerzere_geschenk_dauer_wird_respektiert() -> void:
	var kern: GameCore = _kern()
	kern.starte_schub(600.0)
	assert_float(kern.schub_rest).is_equal_approx(600.0, 0.001)
