## AdServiceAdmob ohne Plugin: sauberer Fallback, kein Absturz, nie Belohnung.
extends GdUnitTestSuite


func test_ohne_plugin_ist_nichts_bereit() -> void:
	var dienst: AdServiceAdmob = auto_free(AdServiceAdmob.new())
	assert_bool(dienst.plugin_vorhanden()).is_false()
	assert_bool(dienst.ist_bereit(&"schub")).is_false()
	assert_bool(dienst.ist_bereit(&"offline_verdoppeln")).is_false()
	assert_int(dienst.phase).is_equal(AdServiceAdmob.Phase.KEIN_PLUGIN)


func test_initialize_ohne_plugin_stuerzt_nicht_und_meldet_keine_werbung() -> void:
	var dienst: AdServiceAdmob = auto_free(AdServiceAdmob.new())
	var antworten: Array = []
	dienst.einwilligung_fertig.connect(func(darf: bool) -> void: antworten.append(darf))
	dienst.initialize()
	dienst.initialize()  # mehrfach aufrufbar
	assert_bool(dienst.darf_werben).is_false()
	assert_int(antworten.size()).is_equal(2)
	assert_bool(antworten[0]).is_false()


func test_zeige_belohnt_ohne_plugin_meldet_nicht_verfuegbar() -> void:
	var dienst: AdServiceAdmob = auto_free(AdServiceAdmob.new())
	var gründe: Array = []
	var belohnt: Array = []
	dienst.nicht_verfuegbar.connect(func(_p: StringName, grund: String) -> void: gründe.append(grund))
	dienst.belohnung_verdient.connect(func(p: StringName) -> void: belohnt.append(p))
	dienst.zeige_belohnt(&"schub")
	assert_int(gründe.size()).is_equal(1)
	assert_int(belohnt.size()).is_equal(0)


func test_einwilligung_aendern_ohne_plugin_ist_false() -> void:
	var dienst: AdServiceAdmob = auto_free(AdServiceAdmob.new())
	assert_bool(dienst.einwilligung_aendern()).is_false()


func test_anbieter_im_release_ist_stub() -> void:
	assert_str(AdServiceAdmob.gewaehlter_anbieter()).is_equal("stub")


func test_nur_google_test_ids() -> void:
	assert_str(AdServiceAdmob.TEST_APP_ID).starts_with("ca-app-pub-3940256099942544")
	assert_str(AdServiceAdmob.TEST_BELOHNT).starts_with("ca-app-pub-3940256099942544")
