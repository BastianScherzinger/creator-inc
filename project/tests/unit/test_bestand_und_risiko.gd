## Prueft die beiden letzten Sondermechaniken.
##
## Bestand (Welt 5): Erloes kommt pro ABONNENT statt pro Einheit. Der Bestand
## waechst mit der Arbeit und schrumpft ohne Betreuung -- der erste Ertrag im
## Spiel, der zurueckgehen kann.
##
## Schwankung (Welt 6): Der Ertrag liegt um den Mittelwert herum statt genau
## darauf. Streuung senkt den AUSSCHLAG, nicht den Mittelwert. Genau dieser
## Unterschied ist der Grund, warum es die Mechanik gibt -- und genau den
## pruefen die Tests.
extends GdUnitTestSuite

const TAKT: float = SimClock.TICK_DAUER


func _welt(id: String, index: int, stufen: int = 8) -> GameCore:
	var kern := GameCore.new(BalanceData.fuer_welt(id), index)
	for sid in Ids.CHAIN:
		var s: StationModel = kern.kette.station(sid)
		if s != null:
			s.stufe = stufen
	return kern


func _laufe(kern: GameCore, sekunden: float) -> void:
	for i in range(int(sekunden / TAKT)):
		kern.tick(TAKT)


# --- Bestand ----------------------------------------------------------------

func test_nur_welt_5_rechnet_mit_bestand() -> void:
	assert_bool(BalanceData.fuer_welt("produkt").bestand_aktiv).is_true()
	for andere in ["zimmer", "auftrag", "webseiten", "buero", "kapital"]:
		assert_bool(BalanceData.fuer_welt(andere).bestand_aktiv) \
			.override_failure_message("Welt '%s' sollte keinen Bestand haben" % andere).is_false()


func test_bestand_startet_im_gleichgewicht_statt_bei_null() -> void:
	# Man kommt nicht mit null Kunden im Loft an. Bei null waere das Einkommen
	# null, die erste Ausbaustufe unerreichbar und die Welt unspielbar.
	var kern: GameCore = _welt("produkt", 4)
	assert_float(kern.bestand).is_greater(0.0)
	assert_float(kern.einkommen_pro_sekunde()).is_greater(0.0)


func test_bestand_waechst_mit_der_arbeit() -> void:
	var kern: GameCore = _welt("produkt", 4)
	var vorher: float = kern.bestand
	for sid in Ids.CHAIN:
		var s: StationModel = kern.kette.station(sid)
		if s != null:
			s.stufe = 30
	_laufe(kern, 60.0)
	assert_float(kern.bestand).is_greater(vorher * 1.5)


func test_bestand_schrumpft_ohne_nachschub() -> void:
	# DAS ist die Aussage: Zum ersten Mal geht Fortschritt zurueck, wenn man
	# nichts tut. Bis hierher konnte er nur stehenbleiben.
	var kern: GameCore = _welt("produkt", 4)
	for sid in Ids.CHAIN:
		var s: StationModel = kern.kette.station(sid)
		if s != null:
			s.stufe = 0            # nichts kommt mehr nach
	var vorher: float = kern.bestand
	_laufe(kern, 120.0)
	assert_float(kern.bestand).is_less(vorher * 0.5)


func test_abwanderung_trifft_grosse_bestaende_staerker() -> void:
	# Sie wirkt anteilig, nicht als fester Betrag. Sonst waere ein grosser
	# Bestand automatisch sicherer als ein kleiner, und das waere gelogen.
	var klein: GameCore = _welt("produkt", 4)
	var gross: GameCore = _welt("produkt", 4)
	klein.bestand = 100.0
	gross.bestand = 10000.0
	for sid in Ids.CHAIN:
		for k in [klein, gross]:
			var s: StationModel = k.kette.station(sid)
			if s != null:
				s.stufe = 0
	var klein_vorher: float = klein.bestand
	var gross_vorher: float = gross.bestand
	_laufe(klein, 30.0)
	_laufe(gross, 30.0)
	assert_float(gross_vorher - gross.bestand).is_greater(klein_vorher - klein.bestand)


func test_bestand_ueberlebt_speichern_und_laden() -> void:
	var kern: GameCore = _welt("produkt", 4)
	_laufe(kern, 20.0)
	var neu: GameCore = _welt("produkt", 4)
	neu.from_save(kern.to_save())
	assert_float(neu.bestand).is_equal_approx(kern.bestand, 0.01)


# --- Schwankung -------------------------------------------------------------

func test_nur_welt_6_schwankt() -> void:
	assert_bool(BalanceData.fuer_welt("kapital").risiko_aktiv).is_true()
	for andere in ["zimmer", "auftrag", "webseiten", "buero", "produkt"]:
		assert_bool(BalanceData.fuer_welt(andere).risiko_aktiv) \
			.override_failure_message("Welt '%s' sollte nicht schwanken" % andere).is_false()


func test_der_ertrag_schwankt_ueberhaupt() -> void:
	var kern: GameCore = _welt("kapital", 5)
	var werte: Array[float] = []
	var letzter: float = kern.gesamt_verdient
	for i in range(40):
		kern.tick(TAKT)
		werte.append(kern.gesamt_verdient - letzter)
		letzter = kern.gesamt_verdient
	var kleinster: float = werte.min()
	var groesster: float = werte.max()
	assert_float(groesster).is_greater(kleinster * 1.1)


func test_streuung_senkt_den_ausschlag() -> void:
	# Der Kern der Mechanik. Ohne diesen Test koennte Streuung alles Moegliche
	# tun und niemand wuerde es merken.
	var ohne: GameCore = _welt("kapital", 5)
	var mit: GameCore = _welt("kapital", 5)
	var t_ohne: StationModel = ohne.kette.station(Ids.STATION_TRANSPORT)
	var t_mit: StationModel = mit.kette.station(Ids.STATION_TRANSPORT)
	t_ohne.freigeschaltet = true
	t_ohne.stufe = 1
	t_mit.freigeschaltet = true
	t_mit.stufe = 40

	var s_mit: float = _spannweite(mit)
	var s_ohne: float = _spannweite(ohne)
	assert_float(s_mit).override_failure_message(
		"Ausschlag mit Streuung %.4f, ohne %.4f -- er muss kleiner werden"
		% [s_mit, s_ohne]).is_less(s_ohne)


func test_streuung_senkt_NICHT_den_mittelwert() -> void:
	# Waere es anders, waere Streuung heimlich ein Gewinn -- und der Spieler
	# wuerde etwas Falsches ueber Risiko lernen.
	var ohne: GameCore = _welt("kapital", 5)
	var mit: GameCore = _welt("kapital", 5)
	var t_mit: StationModel = mit.kette.station(Ids.STATION_TRANSPORT)
	t_mit.freigeschaltet = true
	t_mit.stufe = 40

	_laufe(ohne, 400.0)
	_laufe(mit, 400.0)
	# Der Transport-Faktor selbst erhoeht den Durchsatz, deshalb wird nicht
	# absolut verglichen, sondern gegen den jeweils eigenen Mittelwert.
	var abweichung: float = absf(mit.gesamt_verdient / mit.einkommen_pro_sekunde()
		- ohne.gesamt_verdient / ohne.einkommen_pro_sekunde())
	assert_float(abweichung).is_less(40.0)


func test_ein_rest_ausschlag_bleibt_immer() -> void:
	# Eine Streuung, die den Ausschlag auf null braechte, waere eine
	# Behauptung ueber die Wirklichkeit, die nicht stimmt.
	var kern: GameCore = _welt("kapital", 5)
	var t: StationModel = kern.kette.station(Ids.STATION_TRANSPORT)
	t.freigeschaltet = true
	t.stufe = 500
	assert_float(_spannweite(kern)).is_greater(0.0)


## Wie stark schwankt der Ertrag JE EINHEIT, bezogen auf seinen Hoechstwert?
##
## JE EINHEIT, nicht je Tick -- und das ist der Unterschied zwischen einer
## Messung und einem Zufallsergebnis. Ein Tick umfasst je nach Rundung eine
## oder zwei Takteinheiten; der Ertrag verdoppelt sich dann mit. Diese
## Schwankung hat mit Risiko nichts zu tun, war aber groesser als der Effekt,
## den der Test messen soll. Zwei Anlaeufe sind daran gescheitert: erst ueber
## gesamt_verdient (dort kommen zusaetzlich die sprunghaften Grossauftraege
## dazu), dann ueber den Tick-Ertrag.
##
## Der Quotient Erloes durch Menge ist von beidem frei.
func _spannweite(kern: GameCore) -> float:
	var werte: Array[float] = []
	kern.bus.throughput_tick.connect(func(menge: float, erloes: float) -> void:
		if menge > 0.0:
			werte.append(erloes / menge))
	for i in range(300):
		kern.tick(TAKT)
	if werte.size() < 10:
		return 0.0
	var kleinster: float = werte.min()
	var groesster: float = werte.max()
	return (groesster - kleinster) / maxf(groesster, 0.0001)
