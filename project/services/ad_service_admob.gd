## AdMob hinter der Schnittstelle AdService -- VORBEREITET, NICHT AKTIV.
##
## Aktiv wird diese Klasse erst, wenn in data/services/ads.json
## "anbieter" auf "admob" steht UND das Godot-AdMob-Plugin (Poing Studios,
## v5.x, Godot 4.5+) im Projekt liegt. Solange "anbieter" = "stub" ist, wird sie
## nie erzeugt (main.gd waehlt). Doku: docs/release/ADMOB.md
##
## Ablauf (Reihenfolge ist Pflicht):
##   initialize() -> UMP-Einwilligung einholen/pruefen -> ERST DANACH
##   MobileAds initialisieren und die belohnte Anzeige laden.
## Ohne Einwilligung (im EWR) wird nie geladen.
##
## Ohne Plugin laeuft die Klasse fehlerfrei: Sie meldet "nicht_verfuegbar",
## das Spiel merkt nichts -- belohnte Werbung ist Angebot, nie Bedingung.
##
## WICHTIG ZUM PLUGIN-ZUGRIFF: Plugin-Klassen (MobileAds, ConsentInformation,
## RewardedAdLoader ...) werden hier NIE als Bezeichner geschrieben, sondern
## ueber die globale Klassenliste gesucht (_klasse). Ein fester Bezeichner
## wuerde ohne Plugin einen Parse-Fehler ausloesen und das ganze Skript (und
## damit den Debug-Build) zum Absturz bringen.
##
## Die Test-Anzeigen-IDs stammen aus der oeffentlichen Google-Dokumentation
## und liefern ausschliesslich Testanzeigen. Die echten IDs (Florins AdMob-
## Konto) gehoeren in ads.json unter "admob.echt", NIE in diese Datei.
class_name AdServiceAdmob
extends AdServiceStub

## Wie weit die Vorbereitung ist.
enum Phase { AUS, EINWILLIGUNG, LAEDT, BEREIT, KEIN_PLUGIN, ABGELEHNT }

## Einwilligung ist geklaert (egal ob ja oder nein). darf_werben = Anzeigen
## duerfen angefragt werden.
signal einwilligung_fertig(darf_werben: bool)

const TEST_APP_ID: String = "ca-app-pub-3940256099942544~3347511713"
const TEST_BELOHNT: String = "ca-app-pub-3940256099942544/5224354917"

## Klassen, die das Plugin mitbringen muss. Fehlt eine, gilt es als "kein Plugin".
const PFLICHT_KLASSEN: Array[String] = [
	"MobileAds", "ConsentInformation", "ConsentRequestParameters", "ConsentForm",
	"RewardedAdLoader", "AdRequest",
]

var phase: Phase = Phase.AUS
var darf_werben: bool = false

var _plugin_da: bool = false
var _einheit: String = TEST_BELOHNT
var _anzeige: Variant = null      ## geladene RewardedAd (Plugin-Objekt) oder null
var _zeige_platzierung: StringName = &""
var _verdient: bool = false


func _init() -> void:
	var cfg: Dictionary = laden().get("admob", {}) as Dictionary
	if bool(cfg.get("echte_ids_verwenden", false)):
		var echt: Dictionary = cfg.get("echt", {}) as Dictionary
		var id: String = String(echt.get("belohnt", ""))
		# Leere echte ID = Konfigurationsfehler: lieber Test-ID als gar nichts.
		_einheit = id if id != "" else String(cfg.get("test_belohnt", TEST_BELOHNT))
	else:
		_einheit = String(cfg.get("test_belohnt", TEST_BELOHNT))
	_plugin_da = _plugin_pruefen()
	if not _plugin_da:
		phase = Phase.KEIN_PLUGIN


## Welcher Anbieter steht in ads.json? Nur lesen. Fehlt der Schluessel: "stub".
static func gewaehlter_anbieter(pfad: String = PFAD) -> String:
	return String(laden(pfad).get("anbieter", "stub"))


## Liegt das Plugin im Projekt? Prueft die globale Klassenliste.
static func _plugin_pruefen() -> bool:
	for name in PFLICHT_KLASSEN:
		if _klasse(name) == null:
			return false
	return true


## Sucht eine Plugin-Klasse nach Namen; null, wenn nicht vorhanden.
static func _klasse(klassenname: String) -> Script:
	for eintrag in ProjectSettings.get_global_class_list():
		if String((eintrag as Dictionary).get("class", "")) == klassenname:
			var skript: Variant = load(String((eintrag as Dictionary).get("path", "")))
			return skript as Script
	return null


func plugin_vorhanden() -> bool:
	return _plugin_da


## Einstieg. Sicher mehrfach aufrufbar. Ohne Plugin: sofort Ende, kein Fehler.
func initialize() -> void:
	if not _plugin_da:
		push_warning("AdServiceAdmob: Plugin fehlt, Dienst meldet nicht_verfuegbar")
		phase = Phase.KEIN_PLUGIN
		einwilligung_fertig.emit(false)
		return
	if phase != Phase.AUS and phase != Phase.ABGELEHNT:
		return
	phase = Phase.EINWILLIGUNG
	_einwilligung_einholen()


## Alter Name aus der ersten Vorbereitung; gleiche Wirkung.
func starte() -> void:
	initialize()


## Fuer den Einstellungs-Knopf "Werbe-Einwilligung aendern" (UMP-Pflicht im EWR).
## Gibt true zurueck, wenn der Dialog angefordert wurde.
func einwilligung_aendern() -> bool:
	if not _plugin_da:
		return false
	var form: Script = _klasse("ConsentForm")
	if form == null or not form.has_method("show_privacy_options_form"):
		return false
	# TODO(Einbau): Listener-Klasse OnConsentFormDismissedListener, danach _nach_einwilligung().
	form.call("show_privacy_options_form", _listener_aus("OnConsentFormDismissedListener", {
		"on_consent_form_dismissed": Callable(self, "_nach_privacy_formular"),
	}))
	return true


# --- Einwilligung (UMP) ------------------------------------------------------

func _einwilligung_einholen() -> void:
	# TODO(Einbau, gegen die installierte Plugin-Version pruefen -- Namen aus der README v5.x):
	# 1. ConsentRequestParameters.new()  (tag_for_under_age_of_consent = true,
	#    solange Zielgruppe nicht >= 16 festgelegt ist; Debug-Geraete nur im Test)
	# 2. ConsentInformation.request_consent_info_update(params, OnConsentInfoUpdateListener)
	# 3. bei Erfolg: ConsentForm.load_and_show_consent_form_if_required(OnConsentFormDismissedListener)
	# 4. danach ConsentInformation.can_request_ads() entscheidet.
	var info: Script = _klasse("ConsentInformation")
	var param_klasse: Script = _klasse("ConsentRequestParameters")
	if info == null or param_klasse == null or not info.has_method("request_consent_info_update"):
		_einwilligung_ende(false, "UMP-Schnittstelle nicht gefunden")
		return
	var params: Variant = param_klasse.new()
	var listener: Variant = _listener_aus("OnConsentInfoUpdateListener", {
		"on_success": Callable(self, "_info_aktualisiert"),
		"on_failure": Callable(self, "_info_fehler"),
	})
	info.call("request_consent_info_update", params, listener)


func _info_aktualisiert() -> void:
	var form: Script = _klasse("ConsentForm")
	if form == null or not form.has_method("load_and_show_consent_form_if_required"):
		_nach_einwilligung()
		return
	form.call("load_and_show_consent_form_if_required", _listener_aus("OnConsentFormDismissedListener", {
		"on_consent_form_dismissed": Callable(self, "_nach_privacy_formular"),
	}))


func _info_fehler(_fehler: Variant = null) -> void:
	_einwilligung_ende(false, "UMP-Aktualisierung fehlgeschlagen")


func _nach_privacy_formular(_fehler: Variant = null) -> void:
	_nach_einwilligung()


func _nach_einwilligung() -> void:
	var info: Script = _klasse("ConsentInformation")
	var erlaubt: bool = false
	if info != null and info.has_method("can_request_ads"):
		erlaubt = bool(info.call("can_request_ads"))
	_einwilligung_ende(erlaubt, "" if erlaubt else "Einwilligung verweigert")


func _einwilligung_ende(erlaubt: bool, grund: String) -> void:
	darf_werben = erlaubt
	einwilligung_fertig.emit(erlaubt)
	if not erlaubt:
		phase = Phase.ABGELEHNT
		if grund != "":
			push_warning("AdServiceAdmob: %s" % grund)
		return
	# ERST JETZT das Werbe-SDK anfassen.
	var ads: Script = _klasse("MobileAds")
	if ads != null and ads.has_method("initialize"):
		ads.call("initialize")
	_laden()


# --- Laden und Zeigen --------------------------------------------------------

func _laden() -> void:
	if not darf_werben:
		return
	phase = Phase.LAEDT
	_anzeige = null
	var lader_klasse: Script = _klasse("RewardedAdLoader")
	var anfrage_klasse: Script = _klasse("AdRequest")
	if lader_klasse == null or anfrage_klasse == null:
		phase = Phase.KEIN_PLUGIN
		return
	# TODO(Einbau): RewardedAdLoadCallback mit on_ad_loaded(ad) / on_ad_failed_to_load(error).
	var lader: Variant = lader_klasse.new()
	var rueckruf: Variant = _listener_aus("RewardedAdLoadCallback", {
		"on_ad_loaded": Callable(self, "_geladen"),
		"on_ad_failed_to_load": Callable(self, "_laden_fehler"),
	})
	lader.call("load", _einheit, anfrage_klasse.new(), rueckruf)


func _geladen(anzeige: Variant) -> void:
	_anzeige = anzeige
	phase = Phase.BEREIT


func _laden_fehler(_fehler: Variant = null) -> void:
	_anzeige = null
	phase = Phase.AUS if darf_werben else Phase.ABGELEHNT
	# Kein Dauer-Nachladen: erst beim naechsten ist_bereit/zeige_belohnt neu versuchen.


func ist_bereit(platzierung: StringName) -> bool:
	if not _plugin_da or not darf_werben:
		return false
	return phase == Phase.BEREIT and _anzeige != null and super.ist_bereit(platzierung)


func zeige_belohnt(platzierung: StringName) -> void:
	if not _plugin_da:
		nicht_verfuegbar.emit(platzierung, "Werbe-Plugin nicht eingebunden")
		return
	if not darf_werben:
		nicht_verfuegbar.emit(platzierung, "keine Werbe-Einwilligung")
		return
	if not kennt(platzierung):
		nicht_verfuegbar.emit(platzierung, "unbekannte Platzierung")
		return
	if _anzeige == null or phase != Phase.BEREIT:
		if phase == Phase.AUS:
			_laden()
		nicht_verfuegbar.emit(platzierung, "Anzeige noch nicht geladen")
		return
	var warum: String = grund(platzierung)
	if not warum.is_empty():
		nicht_verfuegbar.emit(platzierung, warum)
		return
	_zeige_platzierung = platzierung
	_verdient = false
	# TODO(Einbau): FullScreenContentCallback (on_ad_dismissed_full_screen_content,
	# on_ad_failed_to_show_full_screen_content) an _anzeige.full_screen_content_callback
	# haengen, dann _anzeige.show(OnUserEarnedRewardListener -> _belohnt).
	var anzeige: Object = _anzeige as Object
	if anzeige == null or not anzeige.has_method("show"):
		nicht_verfuegbar.emit(platzierung, "Anzeige nicht zeigbar")
		return
	anzeige.call("show", _listener_aus("OnUserEarnedRewardListener", {
		"on_user_earned_reward": Callable(self, "_belohnt"),
	}))


func _belohnt(_belohnung: Variant = null) -> void:
	_verdient = true


## Anzeige wurde geschlossen: Belohnung nur, wenn sie vorher verdient wurde.
func _geschlossen() -> void:
	var p: StringName = _zeige_platzierung
	_zeige_platzierung = &""
	_anzeige = null
	if _verdient:
		_zaehle_gesehen(p)
		belohnung_verdient.emit(p)
	else:
		abgebrochen.emit(p)
	_verdient = false
	_laden()


func _zeigen_fehler(_fehler: Variant = null) -> void:
	var p: StringName = _zeige_platzierung
	_zeige_platzierung = &""
	_anzeige = null
	nicht_verfuegbar.emit(p, "Anzeige konnte nicht gezeigt werden")
	_laden()


## Erzeugt ein Plugin-Listener-Objekt und setzt dessen Callables.
## Gibt null zurueck, wenn die Klasse fehlt (dann schlaegt der Plugin-Aufruf
## sauber ueber die Fehlerpfade fehl, nicht ueber einen Absturz).
func _listener_aus(klassenname: String, felder: Dictionary) -> Variant:
	var klasse: Script = _klasse(klassenname)
	if klasse == null:
		return null
	var objekt: Variant = klasse.new()
	for schluessel in felder:
		(objekt as Object).set(String(schluessel), felder[schluessel])
	return objekt
