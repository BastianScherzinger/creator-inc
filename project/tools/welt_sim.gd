## Spielt einzelne Welten bis 100 % durch -- schneller als der ganze Balance-Lauf.
##
## Aufruf:
##   godot_console --headless --path project -s res://tools/welt_sim.gd -- webseiten produkt
##   godot_console --headless --path project -s res://tools/welt_sim.gd -- --variante b zimmer
##   ... -- --kaeufe zimmer     (jeder Kauf mit Preis und Einkommen danach)
##   ... -- --mit-rang auftrag   (startet mit den Rang-Punkten der Vorwelten)
##   ... -- --mit-boost zimmer   (K3 C1: ein Spieler, der den Dauer-Boost nutzt)
##   ... -- --mit-boost --boost-pause 3600 zimmer   (wartet nach Ablauf so lange)
##   ... -- --mit-boost --boost-faktor 1.25 --boost-dauer 900 zimmer   (Was-waere-wenn)
## Boost-Spieler: schaut die Boost-Werbung, sobald der Boost aus ist, die Regeln aus
## ads.json es erlauben (Startschutz, Mindestabstand, Tageslimit) und er `--boost-pause`
## Sekunden gewartet hat. Ohne Pause ist das der Hoechstfall: Boost dauernd an.
## Ohne Angabe: alle Welten mit Abschluss "alles". Ausgabe wie in balance_sim.gd,
## dazu die Zeitpunkte aller Ziele und Nachrichten (fuer die Texte), die Ziel-Ketten
## je Raum und die Crew-Freischaltung (Design-Overhaul 15.10.).
extends SceneTree


func _init() -> void:
	var welten := WorldData.laden()
	var gewuenscht: PackedStringArray = []
	var mit_rang: bool = false
	var kaeufe_zeigen: bool = false
	var mit_boost: bool = false
	var boost_pause: float = 0.0
	var boost_faktor: float = -1.0   ## Was-waere-wenn: ueberschreibt schub.faktor
	var boost_dauer: float = -1.0    ## Was-waere-wenn: ueberschreibt schub.dauer_sekunden
	var args: PackedStringArray = OS.get_cmdline_user_args()
	var i_arg: int = 0
	while i_arg < args.size():
		if args[i_arg] == "--variante" and i_arg + 1 < args.size():
			BalanceData.variante = args[i_arg + 1]
			i_arg += 2
			continue
		if args[i_arg] == "--kaeufe":
			kaeufe_zeigen = true   # jeder Kauf mit Zeit, Preis und Einkommen danach
			i_arg += 1
			continue
		if args[i_arg] == "--mit-boost":
			mit_boost = true
			i_arg += 1
			continue
		if args[i_arg] == "--boost-faktor" and i_arg + 1 < args.size():
			boost_faktor = float(args[i_arg + 1])
			i_arg += 2
			continue
		if args[i_arg] == "--boost-dauer" and i_arg + 1 < args.size():
			boost_dauer = float(args[i_arg + 1])
			i_arg += 2
			continue
		if args[i_arg] == "--boost-pause" and i_arg + 1 < args.size():
			boost_pause = float(args[i_arg + 1])
			i_arg += 2
			continue
		if args[i_arg] == "--mit-rang":
			mit_rang = true   # Rang-Punkte der Vorwelten mitbringen (Rang-Bonus wie im echten Lauf)
			i_arg += 1
			continue
		gewuenscht.append(args[i_arg])
		i_arg += 1
	var alle_ok: bool = true
	for i in range(welten.anzahl()):
		var welt_id: String = welten.id(i)
		if not gewuenscht.is_empty() and not gewuenscht.has(welt_id):
			continue
		var balance := BalanceData.fuer_welt(welt_id)
		if balance == null or balance.abschluss != Ids.ABSCHLUSS_ALLES:
			continue
		print("")
		print("=== WELT %d: '%s'%s ===" % [i + 1, welt_id,
			(" Variante " + BalanceData.variante) if BalanceData.variante != "" else ""])
		if not balance.validieren():
			for f in balance.fehler:
				print("  UNGUELTIG: %s" % f)
			alle_ok = false
			continue
		var sim := AbschlussSim.new(balance, i)
		var zeiten: Dictionary = {}
		var ketten_zeiten: Dictionary = {}
		var crew_frei_zeiten: Dictionary = {}
		var crew_kauf_zeiten: Dictionary = {}
		var kern: GameCore = sim.kern
		if mit_rang:
			var basis: int = 0
			for v in range(i):
				var vor := BalanceData.fuer_welt(welten.id(v))
				basis += kern.erfolge.welt_fertig_punkte()
				for zv in vor.ziele:
					basis += kern.erfolge.ziel_punkte(zv as Dictionary)
			kern.bogen["punkte"] = basis
			kern._level_zuletzt = kern.spieler_level()
			print("  Start mit %d Punkten, Rang %d" % [basis, kern.spieler_level()])
		kern.bus.goal_completed.connect(func(ziel_id: StringName) -> void:
			zeiten[String(ziel_id)] = kern.spielzeit)
		kern.bus.message_received.connect(func(nachricht_id: StringName) -> void:
			zeiten[String(nachricht_id)] = kern.spielzeit)
		var rang_ups: Array = []   ## [rang, zeit, punkte, fortschritt]
		var kurve: Array = []      ## [fortschritt, punkte, zeit] je eingeloestem Ziel
		kern.bus.rank_up.connect(func(rang_nr: int, _name_id: StringName) -> void:
			rang_ups.append([rang_nr, kern.spielzeit, kern.rang_punkte(), kern.weltwechsel_fortschritt()]))
		kern.bus.goal_claimed.connect(func(_ziel_id: StringName, _betrag: float) -> void:
			kurve.append([kern.weltwechsel_fortschritt(), kern.rang_punkte(), kern.spielzeit])
			for kette_id in kern.ketten_ids():
				if kern.kette_fertig(kette_id) and not ketten_zeiten.has(kette_id):
					ketten_zeiten[kette_id] = kern.spielzeit)
		kern.bus.station_upgraded.connect(func(station_id: StringName, _stufe: int) -> void:
			if kern.crew_frei(station_id) and not crew_frei_zeiten.has(String(station_id)):
				crew_frei_zeiten[String(station_id)] = kern.spielzeit)
		kern.bus.money_changed.connect(func(_stand: float, _diff: float) -> void:
			for id in Ids.ALL_STATIONS:
				if kern.crew_frei(id) and not crew_frei_zeiten.has(String(id)):
					crew_frei_zeiten[String(id)] = kern.spielzeit)
		kern.bus.crew_hired.connect(func(station_id: StringName, rang: int) -> void:
			crew_kauf_zeiten["%s %d" % [String(station_id).replace("station_", ""), rang]] = kern.spielzeit)
		if boost_faktor > 0.0:
			kern.balance.schub_faktor = boost_faktor
		if boost_dauer > 0.0:
			kern.balance.schub_dauer = boost_dauer
		if mit_boost:
			_boost_spieler(kern, boost_pause)
		sim.laufen()
		sim.bericht()
		var verlauf_text: PackedStringArray = []
		for minute in range(4, sim.verlauf.size(), 5):
			verlauf_text.append("%d:%d" % [minute + 1, int(sim.verlauf[minute])])
		print("  Einkommen/s alle 5 min: %s" % " ".join(verlauf_text))
		if kaeufe_zeigen:
			for k in sim.kauf_log:
				print("  KAUF %s %-7s %-16s %12.0f -> %.0f/s" % [AbschlussSim._zeit(k[0]), k[1], k[2], float(k[3]), float(k[4])])
		var gross: Array = sim.grossereignisse.duplicate()
		gross.sort()
		var gross_text: PackedStringArray = []
		for g in gross:
			gross_text.append(AbschlussSim._zeit(g))
		print("  Grossereignisse: %s" % " ".join(gross_text))
		var zeile: String = ""
		var namen: Array = zeiten.keys()
		namen.sort()
		for name in namen:
			zeile += "%s %s  " % [String(name).replace("nachricht_", "n").replace("ziel_", "z"),
				AbschlussSim._zeit(zeiten[name])]
		print("  Zeitpunkte: %s" % zeile)
		_ketten_ausgeben(kern, ketten_zeiten)
		_crew_ausgeben(kern, crew_frei_zeiten, crew_kauf_zeiten)
		_rang_ausgeben(kern, rang_ups, kurve)
		print("  Erfolge %d/%d · Spieler-Level %d" % [
			kern.erfolge.anzahl_erreicht(), kern.erfolge.definitionen().size(), kern.spieler_level()])
		for v in sim.pruefe(welt_id):
			print("  ABWEICHUNG: %s" % v)
			alle_ok = false
	quit(0 if alle_ok else 1)


## Haengt den Boost-Spieler an den Kern (K3 C1). Er handelt bei jeder Einnahme: Ist der Boost
## aus und die Werbung erlaubt, startet er einen Boost wie die Belohnung im Spiel.
func _boost_spieler(kern: GameCore, pause: float) -> void:
	var ads: Dictionary = AdServiceStub.laden()
	var ab: Dictionary = ads.get("erst_ab", {}) as Dictionary
	var abstand: float = float(ads.get("mindestabstand_sekunden", 0.0))
	var tag_max: int = int(ads.get("hoechstzahl_pro_tag", 0))
	var zustand: Dictionary = {"letzte": -1.0e9, "aus_seit": 0.0, "tag": -1, "heute": 0, "gesamt": 0}
	kern.bus.money_changed.connect(func(_stand: float, diff: float) -> void:
		if diff <= 0.0:
			return
		var t: float = kern.spielzeit
		if kern.schub_rest > 0.0:
			zustand["aus_seit"] = t
			return
		if t < float(ab.get("spielzeit_s", 0.0)):
			return
		var raum: StringName = StringName(String(ab.get("bereich", "")))
		if kern.bereiche.existiert(raum) and not kern.bereiche.ist_gekauft(raum):
			return
		if t - float(zustand["aus_seit"]) < pause or t - float(zustand["letzte"]) < abstand:
			return
		var tag: int = int(t / 86400.0)
		if tag != int(zustand["tag"]):
			zustand["tag"] = tag
			zustand["heute"] = 0
		if tag_max > 0 and int(zustand["heute"]) >= tag_max:
			return
		zustand["heute"] = int(zustand["heute"]) + 1
		zustand["gesamt"] = int(zustand["gesamt"]) + 1
		zustand["letzte"] = t
		kern.starte_schub())


## Rang-Ups mit Zeit und Weltfortschritt; dazu die Punkte, die bei 3/12/25/45/70 %
## Weltfortschritt erreicht sind (Eichung der Schwellen in erfolge.json).
func _rang_ausgeben(kern: GameCore, rang_ups: Array, kurve: Array) -> void:
	var teile: PackedStringArray = []
	for r in rang_ups:
		teile.append("R%d %s (%d P, %d %%)" % [int(r[0]), AbschlussSim._zeit(float(r[1])), int(r[2]), int(round(float(r[3]) * 100.0))])
	print("  Raenge: %s" % " · ".join(teile))
	var eich: PackedStringArray = []
	for anteil in [0.03, 0.12, 0.25, 0.45, 0.70]:
		var punkte: int = 0
		var zeit: float = 0.0
		for k in kurve:
			if float(k[0]) >= anteil:
				punkte = int(k[1])
				zeit = float(k[2])
				break
		eich.append("%d %% -> %d P (%s)" % [int(anteil * 100.0), punkte, AbschlussSim._zeit(zeit)])
	print("  Eichung: %s · Punkte am Ende %d · Rang %d" % [" · ".join(eich), kern.rang_punkte(), kern.spieler_level()])


func _ketten_ausgeben(kern: GameCore, ketten_zeiten: Dictionary) -> void:
	var teile: PackedStringArray = []
	for kette_id in kern.ketten_ids():
		var stand: Dictionary = kern.kette_stand(kette_id)
		teile.append("%s %d/%d%s" % [kette_id, int(stand["erledigt"]), int(stand["anzahl"]),
			(" fertig " + AbschlussSim._zeit(ketten_zeiten[kette_id])) if ketten_zeiten.has(kette_id) else ""])
	print("  Ketten: %s" % " · ".join(teile))


func _crew_ausgeben(kern: GameCore, frei_zeiten: Dictionary, kauf_zeiten: Dictionary) -> void:
	var teile: PackedStringArray = []
	for id in Ids.ALL_STATIONS:
		if not kern.crew_hat(id):
			continue
		teile.append("%s frei %s Rang %d/%d" % [String(id).replace("station_", ""),
			AbschlussSim._zeit(frei_zeiten.get(String(id), -1.0)), kern.crew_rang(id), kern.crew.max_rang(id)])
	print("  Crew: %s" % " · ".join(teile))
	var kaeufe: Array = kauf_zeiten.keys()
	kaeufe.sort_custom(func(a: Variant, b: Variant) -> bool: return float(kauf_zeiten[a]) < float(kauf_zeiten[b]))
	var text: PackedStringArray = []
	for k in kaeufe:
		text.append("%s %s" % [k, AbschlussSim._zeit(kauf_zeiten[k])])
	if not text.is_empty():
		print("  Crew gekauft: %s" % " · ".join(text))
