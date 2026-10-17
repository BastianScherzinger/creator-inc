## Prueft das Leben der Figuren (docs/RELEASE_PLAN_2026-10-14.md 5): Wippen auf
## dem Koerper, Jubel an der eigenen Station, Wurzel der Figur bleibt unberuehrt.
extends GdUnitTestSuite


func _figur(x: float) -> Node3D:
	var figur := Node3D.new()
	figur.position = Vector3(x, 0.0, 0.0)
	var koerper := Node3D.new()
	koerper.name = "koerper"
	figur.add_child(koerper)
	for name in ["kopf", "arm_l", "arm_r"]:
		var teil := Node3D.new()
		teil.name = name
		koerper.add_child(teil)
	add_child(figur)
	return figur


func _leben(figuren: Array[Node3D], stationen: Dictionary, bus: EventBus) -> FigurLeben:
	var leben := FigurLeben.new()
	add_child(leben)
	leben.aufbauen(figuren, bus, stationen)
	return leben


func test_wippen_veraendert_nur_den_koerper() -> void:
	var figur: Node3D = auto_free(_figur(0.0))
	var bus := EventBus.new()
	var leben: FigurLeben = auto_free(_leben([figur], {}, bus))
	var koerper: Node3D = figur.find_child("koerper", true, false) as Node3D
	leben._process(0.1)
	leben._process(0.1)
	assert_float(koerper.scale.y).is_not_equal(1.0)
	assert_vector(figur.scale).is_equal(Vector3.ONE)
	assert_vector(figur.position).is_equal(Vector3.ZERO)


func test_kauf_an_der_station_laesst_die_figur_daneben_jubeln() -> void:
	var nah: Node3D = auto_free(_figur(1.0))
	var fern: Node3D = auto_free(_figur(20.0))
	var bus := EventBus.new()
	var leben: FigurLeben = auto_free(_leben([nah, fern], {&"station_a": Vector3(0, 0, 0)}, bus))
	bus.station_upgraded.emit(&"station_a", 5)
	for i in range(3):
		leben._process(0.1)
	var koerper_nah: Node3D = nah.find_child("koerper", true, false) as Node3D
	var koerper_fern: Node3D = fern.find_child("koerper", true, false) as Node3D
	assert_float(koerper_nah.position.y).is_greater(0.05)
	assert_float(koerper_fern.position.y).is_equal(0.0)
	assert_float((nah.find_child("arm_l", true, false) as Node3D).rotation.x).is_less(-1.0)


func test_jubel_endet_und_koerper_steht_wieder() -> void:
	var figur: Node3D = auto_free(_figur(0.0))
	var bus := EventBus.new()
	var leben: FigurLeben = auto_free(_leben([figur], {}, bus))
	leben.jubel_alle()
	for i in range(30):
		leben._process(0.1)
	assert_float((figur.find_child("koerper", true, false) as Node3D).position.y).is_equal(0.0)
