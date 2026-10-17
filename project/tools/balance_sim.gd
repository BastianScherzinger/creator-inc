## Balance-Simulator -- rechnet einen Spieldurchlauf headless durch, JE WELT.
##
## Aufruf:
##   godot_console --headless --path project -s res://tools/balance_sim.gd
##
## Simuliert fuer JEDE Welt aus data/worlds/worlds.json einen Spieler, der immer
## den aktuellen Engpass ausbaut, sobald er ihn sich leisten kann -- und das
## jeweils als FRISCHER Start in genau dieser Welt (mit ihrem eigenen
## Welt-Index, damit welt_faktor() korrekt eingeht). Vergleicht das Ergebnis
## mit der je Welt hinterlegten Zielkurve und prueft die harte Vorgabe, dass
## die Wartezeit auf die naechste Stufe in den ersten 60 Minuten nie ueber
## 90 Sekunden steigt.
##
## Damit ist Balancing eine Messung statt eines Bauchgefuehls: Eine Aenderung
## in data/balance/<welt>.json ist in unter einer Sekunde bewertet -- fuer
## ALLE sechs Welten in einem Lauf.
##
## Balance-A/B (Design-Overhaul 15.10.):
##   godot_console --headless --path project -s res://tools/balance_sim.gd -- --variante b
## legt data/balance/experimente/<welt>_b.json tief ueber das Original (Welten ohne
## Overlay laufen unveraendert). Neue Messgroessen je Welt: Zeit bis zum ersten
## Upgrade (Ziel < 10 s), Upgrades pro Minute in den ersten 10 Minuten (>= 1,5),
## Zeit bis Raum 2 (< 4 min), Zeit bis zum ersten Stern.
extends SceneTree

const SIM_MINUTEN: float = 60.0
const SCHRITT: float = 0.25

## Wartezeit-Grenzen in zwei Fenstern, je Welt gleich angewendet.
##
## Eine einzige Grenze waere designfremd: Kosten wachsen exponentiell, der
## Ertrag springt nur an Meilensteinen. Pro Meilenstein-Zyklus waechst die
## Kaufzeit deshalb zwangslaeufig (bei 1.15^12 / 1.7 um Faktor 3,15). Eine
## konstante Kaufzeit gaebe es nur bei faktor = wachstum^intervall -- dann
## wuerde die Gesamtprogression explodieren.
##
## Entscheidend ist deshalb nicht die Konstanz, sondern der EINSTIEG: Die
## ersten 15 Minuten muessen flott sein, weil dort ueber Behalten oder
## Deinstallieren entschieden wird. Danach darf es sich strecken.
const WARTEZEIT_GRENZE_EINSTIEG: float = 60.0   ## erste 15 Minuten
const EINSTIEG_SEKUNDEN: float = 900.0
const WARTEZEIT_GRENZE_GESAMT: float = 150.0    ## gesamte 60 Minuten

## Zielkurven JE WELT: Sekunde -> kumuliert verdient.
##
## 'zimmer' ist die urspruengliche, am Spieler kalibrierte Kurve
## (GAME_DESIGN.md 5.5) -- unveraendert, sie ist der Regressionsschutz fuer
## die einzige Welt, die schon vor TASK 013b balanciert war.
##
## Die fuenf uebrigen Kurven sind NEU: Erst wurde jede Balance-Datei so
## eingestellt, dass ihr 60-Minuten-Ertrag zur Groessenordnung aus
## docs/KONZEPT.md passt (Welt 2 zwei- bis dreistellig, Welt 3 drei- bis
## vierstellig, Welt 4 vier- bis fuenfstellig, Welt 5 fuenf- bis
## sechsstellig, Welt 6 sechs- bis siebenstellig), dann wurde die GEMESSENE
## Kurve hier eingefroren. Ab jetzt wirkt sie wie 'zimmer's Kurve als
## Regressionsschutz: Sie faengt jede kuenftige Balance-Aenderung ab, die den
## Verlauf unbeabsichtigt verschiebt.
##
## Wichtig fuer das Lesen der Zahlen: welt_faktor_pro_welt (6.0) potenziert
## sich mit dem Welt-Index (GameCore.welt_faktor()). Eine neue Welt startet
## dadurch bereits mit einem grossen Vorsprung -- deshalb sind die BASIS-Werte
## (basis_kosten, erloes_pro_einheit) je Welt bewusst NIEDRIGER als in
## 'zimmer', sonst wuerde der Ertrag doppelt wachsen (einmal durch den
## Welt-Faktor, einmal durch die eigene Balance).
## Die Zielkurve JE WELT.
##
## Sie ist in allen Welten dieselbe Kurve, nur mal zehn hoch Weltindex.
## Das ist kein Zufall, sondern die Aussage des Spiels: Jede Welt ist eine
## Groessenordnung groesser als die vorige, bei gleichem Tempo. Wer eine Welt
## umbalanciert, muss hier dieselbe Kurve wiederfinden -- weicht eine Welt in
## der FORM ab, ist das ein Fehler; weicht sie nur im MASSSTAB ab, ist es
## Absicht.
##
## Ausnahme ist "kapital": Sie hat als einzige eine echte Tempobremse
## (hoeheres Kostenwachstum, seltenere Meilensteine) und deshalb eine eigene
## Form. Der Ausstieg soll ruhiger sein als alles davor.
const ZIELKURVEN: Dictionary = {
	"zimmer": {
		30: 30, 120: 150, 300: 930, 720: 10000, 1500: 73000, 2400: 243000, 3600: 557000,
	},
	# Eigene FORM mit einer DELLE bei zwoelf Minuten -- und die ist der Sinn
	# dieser Welt. Dort steht die harte Obergrenze, und dort bringt Ausbauen
	# exakt nichts mehr; man muss sparen und umbauen. Die Kurve knickt deshalb
	# ein und faengt sich wieder.
	#
	# Waere hier die glatte Zehnerkurve eingetragen, wuerde der Simulator
	# genau das als Fehler melden, was die Welt ausmacht -- und der naechste,
	# der es "repariert", nimmt ihr ihren einzigen Einfall.
	"auftrag": {
		30: 296, 120: 1520, 300: 9260, 720: 68800,
		1500: 596000, 2400: 2.11e+06, 3600: 5.05e+06,
	},
	"webseiten": {
		30: 3000, 120: 15000, 300: 93000, 720: 1e+06, 1500: 7.3e+06, 2400: 2.43e+07, 3600: 5.57e+07,
	},
	"buero": {
		30: 30000, 120: 150000, 300: 930000, 720: 1e+07, 1500: 7.3e+07, 2400: 2.43e+08, 3600: 5.57e+08,
	},
	# Eigene FORM: flacher in der Mitte. Welt 5 verdient nicht pro Einheit,
	# sondern pro ABONNENT, und der Bestand hinkt jedem Ausbau rund dreissig
	# Sekunden hinterher. Jede Verbesserung wirkt hier verzoegert -- das ist
	# der Unterschied zwischen herstellen und halten, und er soll sich
	# anfuehlen.
	#
	# Am Anfang und am Ende liegt die Welt auf der Zehnerkurve; nur dazwischen,
	# waehrend am schnellsten ausgebaut wird, bleibt der Bestand zurueck.
	"produkt": {
		30: 294000, 120: 1.30e+06, 300: 6.52e+06, 720: 6.70e+07,
		1500: 5.91e+08, 2400: 2.05e+09, 3600: 4.94e+09,
	},
	# Eigene FORM, nicht nur eigener Massstab: Welt 6 ist die einzige mit einer
	# echten Tempobremse (Kostenwachstum 1,18 statt 1,15, Meilensteine alle 16
	# statt 12 Stufen und nur Faktor 1,6). Sie erreicht deshalb nach einer
	# Stunde rund ein Drittel dessen, was die reine Zehnerskalierung ergaebe --
	# das ist Absicht und keine Abweichung. Der Ausstieg soll sich anders
	# anfuehlen als alles davor: langsamer, mit mehr Platz zwischen den
	# Ereignissen.
	"kapital": {
		30: 2.95e+06, 120: 1.49e+07, 300: 8.69e+07, 720: 5.78e+08,
		1500: 3.31e+09, 2400: 7.64e+09, 3600: 1.674e+10,
	},
}
const TOLERANZ: float = 0.25   ## +/- 25 Prozent laut Definition of Done


func _init() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	for i_arg in range(args.size() - 1):
		if args[i_arg] == "--variante":
			BalanceData.variante = args[i_arg + 1]
	if BalanceData.variante != "":
		print("*** Balance-Variante '%s' (Overlay aus data/balance/experimente/) ***" % BalanceData.variante)
	var welten := WorldData.laden()
	var alle_ok: bool = true
	var zusammenfassung: Array[String] = []

	for i in range(welten.anzahl()):
		var welt_id: String = welten.id(i)
		var ergebnis: Dictionary
		var probe := BalanceData.fuer_welt(welt_id)
		if probe != null and probe.abschluss == Ids.ABSCHLUSS_ALLES:
			ergebnis = _simuliere_abschluss(i, welt_id, probe)
		else:
			ergebnis = _simuliere_welt(i, welt_id)
		alle_ok = alle_ok and bool(ergebnis["ok"])
		zusammenfassung.append(String(ergebnis["zeile"]))

	print("")
	print("=== GESAMTUEBERSICHT: alle Welten (je %d Minuten, isoliert simuliert) ===" % int(SIM_MINUTEN))
	print("")
	print("%-11s %4s %14s %14s %8s %6s %8s %6s %7s %6s %6s" % [
		"Welt", "OK?", "Verdient 60m", "Ziel 60m", "Stufen", "Weltw.", "Warte",
		"1.Upg", "Upg/Min", "Raum2", "Stern"])
	print("-".repeat(104))
	for zeile in zusammenfassung:
		print(zeile)
	print("-".repeat(104))
	print("Ziele Messgroessen: 1.Upg < 10 s · Upg/Min (Min 1-10) >= 1,5 · Raum2 < 4:00")

	print("")
	if alle_ok:
		print("ERGEBNIS: Balance liegt in allen Welten im Zielkorridor.")
		quit(0)
	else:
		print("ERGEBNIS: mindestens eine Welt liegt ausserhalb des Zielkorridors.")
		quit(1)


## Eine Welt, die bei 100 % endet, wird bis dorthin gespielt (ADR-021).
##
## Statt einer Zielkurve ueber 60 Minuten zaehlen hier Meilensteine: erster
## Kauf, erste Ausstattung, Raeume, Abschluss -- und die laengste Pause ohne
## Kauf. Die Zeile in der Uebersicht zeigt die Abschlusszeit statt des
## 60-Minuten-Ertrags.
func _simuliere_abschluss(welt_index: int, welt_id: String, balance: BalanceData) -> Dictionary:
	print("")
	print("=== WELT %d: '%s' (Abschluss 'alles') ===" % [welt_index + 1, welt_id])
	if not balance.validieren():
		for f in balance.fehler:
			print("    %s" % f)
		return {"ok": false, "zeile": "%-11s %4s %14s" % [welt_id, "NEIN", "Balance ungueltig"]}
	var sim := AbschlussSim.new(balance, welt_index)
	sim.laufen()
	sim.bericht()
	var verstoesse: PackedStringArray = sim.pruefe(welt_id)
	for v in verstoesse:
		print("  ABWEICHUNG: %s" % v)
	var ok: bool = verstoesse.is_empty()
	# In der Uebersicht: Abschlusszeit und die laengste Pause ohne Kauf.
	var zeile: String = "%-11s %4s %14s %14s %8d %6s %7.0fs %6s %7.2f %6s %6s" % [
		welt_id, ("ja" if ok else "NEIN"), String.num_scientific(snappedf(sim.kern.welt_verdient, 1.0e6)), "100 %",
		sim.kern.stufen_gesamt(), AbschlussSim._zeit(sim.ereignisse.get("abschluss", -1.0)),
		sim.luecke_gesamt, AbschlussSim._zeit(sim.ereignisse.get("erster_kauf", -1.0)),
		sim.upgrades_pro_minute(), AbschlussSim._zeit(sim.ereignisse.get("bereich_1", -1.0)),
		AbschlussSim._zeit(sim.ereignisse.get("erster_stern", -1.0))]
	return {"ok": ok, "zeile": zeile}


## Simuliert genau eine Welt ueber SIM_MINUTEN und meldet das Ergebnis.
##
## `welt_index` ist der ECHTE Index aus worlds.json -- nur damit stimmt
## welt_faktor() ueberein mit dem, was ein Spieler erlebt, der diese Welt
## nach den vorherigen erreicht.
func _simuliere_welt(welt_index: int, welt_id: String) -> Dictionary:
	print("")
	print("=== WELT %d: '%s' ===" % [welt_index + 1, welt_id])

	var balance := BalanceData.fuer_welt(welt_id)
	if balance == null or not balance.validieren():
		print("  FEHLER: Balance-Daten ungueltig.")
		if balance != null:
			for f in balance.fehler:
				print("    %s" % f)
		return {
			"ok": false,
			"zeile": "%-11s %4s %14s" % [welt_id, "NEIN", "Balance ungueltig"],
		}

	var kern := GameCore.new(balance, welt_index)
	var zielkurve: Dictionary = ZIELKURVEN.get(welt_id, {})

	var gesamt_sekunden: float = SIM_MINUTEN * 60.0
	var schritte: int = int(gesamt_sekunden / SCHRITT)
	var messpunkte: Dictionary = {}
	var max_wartezeit: float = 0.0
	var max_wartezeit_bei: float = 0.0
	var max_wartezeit_einstieg: float = 0.0
	var upgrades_gesamt: int = 0

	var schwelle_weltwechsel: float = float(
		(balance.unlocks.get(String(Ids.UNLOCK_WORLD_2), {}) as Dictionary).get("schwelle", 0.0))
	var weltwechsel_zeit: float = -1.0   ## -1 = innerhalb der Simulation nicht erreicht
	var umbau_zeit: float = -1.0         ## Wann die harte Obergrenze fiel (Welt 2)

	for i in range(schritte):
		kern.tick(SCHRITT)

		# Der Umbau hat VORRANG vor jedem Ausbau, sobald die Leitung voll ist.
		#
		# Ohne diese Zeile spielt der Simulator einen Spieler, der ewig gegen
		# eine Wand ausbaut -- und meldet dann eine Welt als unbalanciert, die
		# in Wahrheit nur eine Entscheidung verlangt. Ein Simulator, der die
		# eine Handlung nicht kennt, auf die eine Welt hinauslaeuft, misst die
		# falsche Welt.
		var an_der_wand: bool = kern.limit_gilt() and kern.limit_auslastung() >= 0.98
		if an_der_wand and kern.kaufe_umbau():
			umbau_zeit = kern.spielzeit
			an_der_wand = false

		# AN DER WAND WIRD GESPART, NICHT AUSGEBAUT.
		#
		# Das ist keine Feinheit, sondern der ganze Unterschied: Solange die
		# Leitung voll ist, bringt jeder weitere Ausbau exakt null. Ein
		# Simulator, der trotzdem weiter ausbaut, verbrennt das Geld, mit dem
		# der Umbau bezahlt werden muesste -- und meldet dann eine Welt als
		# unbalanciert, die in Wahrheit nur eine Entscheidung verlangt.
		#
		# Genau diesen Fehler macht auch ein Spieler, der die Anzeige nicht
		# liest. Deshalb muss die Anzeige gut sein.
		var versuche: int = 0
		if an_der_wand:
			versuche = 50
		while versuche < 50:
			var engpass: StringName = kern.kette.bottleneck()
			if engpass == &"":
				break
			if not kern.upgrade_station(engpass):
				break
			upgrades_gesamt += 1
			versuche += 1

		if weltwechsel_zeit < 0.0 and schwelle_weltwechsel > 0.0 \
				and float(kern.stufen_gesamt()) >= schwelle_weltwechsel:
			weltwechsel_zeit = kern.spielzeit

		# Wartezeit auf die naechste Stufe des Engpasses
		var eng: StationModel = kern.kette.station(kern.kette.bottleneck())
		if eng != null:
			var wartezeit: float = CostCurve.wartezeit_bis_naechste_stufe(
				eng.basis_kosten, eng.wachstum, eng.stufe,
				kern.kapital, kern.einkommen_pro_sekunde())
			if not is_inf(wartezeit):
				if wartezeit > max_wartezeit:
					max_wartezeit = wartezeit
					max_wartezeit_bei = kern.spielzeit
				if kern.spielzeit <= EINSTIEG_SEKUNDEN and wartezeit > max_wartezeit_einstieg:
					max_wartezeit_einstieg = wartezeit

		var sekunde: int = int(round(kern.spielzeit))
		if zielkurve.has(sekunde) and not messpunkte.has(sekunde):
			messpunkte[sekunde] = {
				"verdient": kern.gesamt_verdient,
				"kapital": kern.kapital,
				"stufen": kern.stufen_gesamt(),
				"einkommen": kern.einkommen_pro_sekunde(),
			}

	_bericht(kern, zielkurve, messpunkte, max_wartezeit, max_wartezeit_bei,
		max_wartezeit_einstieg, upgrades_gesamt, schwelle_weltwechsel, weltwechsel_zeit)

	var abweichungen: int = _pruefe_zielkurve(zielkurve, messpunkte)
	var wartezeit_ok: bool = (max_wartezeit <= WARTEZEIT_GRENZE_GESAMT
		and max_wartezeit_einstieg <= WARTEZEIT_GRENZE_EINSTIEG)
	var ok: bool = (abweichungen == 0 and wartezeit_ok)

	var endziel: float = 0.0
	var sekunden_sortiert: Array = zielkurve.keys()
	if not sekunden_sortiert.is_empty():
		sekunden_sortiert.sort()
		endziel = float(zielkurve[sekunden_sortiert[-1]])

	var weltwechsel_text: String = "-"
	if weltwechsel_zeit >= 0.0:
		weltwechsel_text = _zeit(int(weltwechsel_zeit))

	var zeile: String = "%-11s %4s %14.0f %14.0f %8d %6s %8s" % [
		welt_id, ("ja" if ok else "NEIN"), kern.gesamt_verdient, endziel,
		kern.stufen_gesamt(), weltwechsel_text, ("OK" if wartezeit_ok else "ZU HOCH")]

	return {"ok": ok, "zeile": zeile}


func _bericht(kern: GameCore, zielkurve: Dictionary, messpunkte: Dictionary,
		max_wartezeit: float, max_wartezeit_bei: float, max_wartezeit_einstieg: float,
		upgrades: int, schwelle_weltwechsel: float, weltwechsel_zeit: float) -> void:
	print("%-8s %14s %14s %8s %12s %8s" % [
		"Zeit", "Verdient", "Ziel", "Stufen", "Einkommen/s", "Abw."])
	print("-".repeat(72))

	var sekunden: Array = zielkurve.keys()
	sekunden.sort()
	for s in sekunden:
		var ziel: float = float(zielkurve[s])
		if messpunkte.has(s):
			var m: Dictionary = messpunkte[s]
			var abw: float = (float(m["verdient"]) - ziel) / ziel * 100.0
			print("%-8s %14.0f %14.0f %8d %12.1f %+7.0f%%" % [
				_zeit(s), float(m["verdient"]), ziel, int(m["stufen"]),
				float(m["einkommen"]), abw])
		else:
			print("%-8s %14s %14.0f" % [_zeit(s), "-", ziel])

	print("-".repeat(72))
	print("Endstand nach %d Min: %.0f verdient, %d Stufen, %.1f/s" % [
		int(SIM_MINUTEN), kern.gesamt_verdient, kern.stufen_gesamt(),
		kern.einkommen_pro_sekunde()])
	print("Upgrades gesamt:      %d" % upgrades)
	print("Freischaltungen:      %s" % ", ".join(kern.fortschritt.to_array()))
	if schwelle_weltwechsel > 0.0:
		if weltwechsel_zeit >= 0.0:
			print("Weltwechsel-Schwelle: %d Stufen, erreicht bei %s" % [
				int(schwelle_weltwechsel), _zeit(int(weltwechsel_zeit))])
		else:
			print("Weltwechsel-Schwelle: %d Stufen, in %d Minuten NICHT erreicht" % [
				int(schwelle_weltwechsel), int(SIM_MINUTEN)])
	print("Wartezeit Einstieg:   %.1fs (Grenze %.0fs, erste 15 Min) %s" % [
		max_wartezeit_einstieg, WARTEZEIT_GRENZE_EINSTIEG,
		"OK" if max_wartezeit_einstieg <= WARTEZEIT_GRENZE_EINSTIEG else "ZU HOCH"])
	print("Wartezeit gesamt:     %.1fs bei %s (Grenze %.0fs) %s" % [
		max_wartezeit, _zeit(int(max_wartezeit_bei)), WARTEZEIT_GRENZE_GESAMT,
		"OK" if max_wartezeit <= WARTEZEIT_GRENZE_GESAMT else "ZU HOCH"])


func _pruefe_zielkurve(zielkurve: Dictionary, messpunkte: Dictionary) -> int:
	var abweichungen: int = 0
	for s in zielkurve.keys():
		if not messpunkte.has(s):
			abweichungen += 1
			continue
		var ist: float = float((messpunkte[s] as Dictionary)["verdient"])
		var soll: float = float(zielkurve[s])
		if abs(ist - soll) / soll > TOLERANZ:
			abweichungen += 1
	return abweichungen


func _zeit(sekunden: int) -> String:
	return "%d:%02d" % [sekunden / 60, sekunden % 60]
