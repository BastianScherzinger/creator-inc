## Selbsttest des Testframeworks (TASK 004).
## Beweist, dass gdUnit4 headless laeuft und Fehlschlaege korrekt meldet.
## Dieser Test bleibt dauerhaft bestehen: Faellt er aus, ist die Testkette kaputt,
## nicht der Spielcode.
extends GdUnitTestSuite


func test_framework_laeuft() -> void:
	assert_int(2 + 2).is_equal(4)


func test_gleitkomma_vergleich() -> void:
	# Die Wirtschaft rechnet mit float -- exakte Gleichheit waere hier eine Falle.
	assert_float(0.1 + 0.2).is_equal_approx(0.3, 0.0001)


func test_kostenformel_erwartungswerte() -> void:
	# Referenzwerte aus docs/GAME_DESIGN.md 5.1: kosten(n) = 25 * 1.16^(n-1)
	# Noch keine Implementierung -- hier wird nur die Formel selbst festgenagelt,
	# damit TASK 006 gegen eine bereits geprueffte Erwartung baut.
	var basis: float = 25.0
	var wachstum: float = 1.16
	assert_float(basis * pow(wachstum, 0)).is_equal_approx(25.0, 0.5)
	assert_float(basis * pow(wachstum, 4)).is_equal_approx(45.4, 0.5)
	assert_float(basis * pow(wachstum, 9)).is_equal_approx(95.4, 0.5)
