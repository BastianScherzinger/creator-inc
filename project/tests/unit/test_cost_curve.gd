## Prueft die Wirtschaftsformeln gegen die Referenzwerte aus
## docs/GAME_DESIGN.md 5.1 und 5.5. Diese Zahlen sind der Vertrag zwischen
## Design und Code -- wenn sie sich aendern, aendert sich das Spielgefuehl.
extends GdUnitTestSuite

const BASIS: float = 25.0
const WACHSTUM: float = 1.16


func test_kostenformel_referenzwerte() -> void:
	# Werte aus GAME_DESIGN.md 5.1
	assert_float(CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 1)).is_equal_approx(25.0, 0.5)
	assert_float(CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 5)).is_equal_approx(45.27, 0.05)
	assert_float(CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 10)).is_equal_approx(95.07, 0.05)
	assert_float(CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 20)).is_equal_approx(419.41, 0.05)
	assert_float(CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 30)).is_equal_approx(1850.21, 0.05)


func test_kosten_steigen_streng_monoton() -> void:
	var vorher: float = 0.0
	for stufe in range(1, 60):
		var jetzt: float = CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, stufe)
		assert_bool(jetzt > vorher).is_true()
		vorher = jetzt


func test_kosten_summe_entspricht_einzelsumme() -> void:
	var summe_einzeln: float = 0.0
	for stufe in range(6, 11):
		summe_einzeln += CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, stufe)
	assert_float(CostCurve.kosten_summe(BASIS, WACHSTUM, 5, 10)).is_equal_approx(summe_einzeln, 0.01)


func test_kosten_summe_ohne_fortschritt_ist_null() -> void:
	assert_float(CostCurve.kosten_summe(BASIS, WACHSTUM, 10, 10)).is_equal(0.0)
	assert_float(CostCurve.kosten_summe(BASIS, WACHSTUM, 10, 5)).is_equal(0.0)


func test_bezahlbare_stufen() -> void:
	# Genau der Preis fuer eine Stufe reicht fuer genau eine Stufe
	var preis_stufe_2: float = CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 2)
	assert_int(CostCurve.bezahlbare_stufen(BASIS, WACHSTUM, 1, preis_stufe_2)).is_equal(1)
	# Ein Cent zu wenig reicht fuer keine
	assert_int(CostCurve.bezahlbare_stufen(BASIS, WACHSTUM, 1, preis_stufe_2 - 0.01)).is_equal(0)
	# Ohne Geld geht nichts
	assert_int(CostCurve.bezahlbare_stufen(BASIS, WACHSTUM, 1, 0.0)).is_equal(0)


func test_ertrag_ist_linear() -> void:
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, 1)).is_equal(2.0)
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, 5)).is_equal(10.0)
	# Verdoppelte Stufe = verdoppelter Ertrag. Das unterscheidet den Ertrag
	# von den Kosten und erzeugt die wachsende Kaufzeit.
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, 20)).is_equal(
		CostCurve.ertrag_pro_sekunde(2.0, 10) * 2.0)


func test_ertrag_bei_stufe_null_ist_null() -> void:
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, 0)).is_equal(0.0)
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, -3)).is_equal(0.0)


func test_multiplikator_wirkt() -> void:
	assert_float(CostCurve.ertrag_pro_sekunde(2.0, 5, 1.5)).is_equal(15.0)


func test_wartezeit_null_wenn_kapital_reicht() -> void:
	var preis: float = CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 2)
	assert_float(CostCurve.wartezeit_bis_naechste_stufe(BASIS, WACHSTUM, 1, preis, 1.0)).is_equal(0.0)


func test_wartezeit_unendlich_ohne_einkommen() -> void:
	var wartezeit: float = CostCurve.wartezeit_bis_naechste_stufe(BASIS, WACHSTUM, 1, 0.0, 0.0)
	assert_bool(is_inf(wartezeit)).is_true()


func test_wartezeit_rechnet_korrekt() -> void:
	# Preis Stufe 2 = 29.0; bei 0 Kapital und 10/s dauert es 2.9s
	var preis: float = CostCurve.kosten_fuer_stufe(BASIS, WACHSTUM, 2)
	var erwartet: float = preis / 10.0
	assert_float(CostCurve.wartezeit_bis_naechste_stufe(BASIS, WACHSTUM, 1, 0.0, 10.0)) \
		.is_equal_approx(erwartet, 0.01)
