"""Einmal-Werkzeug I2: schlankere Hud-Leiste (Speicher als Kurzzeile, Tagesaufgabe einklappbar)."""
p = "project/game/ui/hud.gd"
s = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")


def rep(a, b):
    global s
    assert s.count(a) == 1, (a, s.count(a))
    s = s.replace(a, b)


rep("var _limit_voll: bool = false\n",
    "var _limit_voll: bool = false\nvar _limit_kurz: Label\nvar _limit_kompakt: bool = false\n"
    "var _chip_zeile: HBoxContainer\nvar _aufgabe_chip: PanelContainer\nvar _aufgabe_chip_text: Label\n"
    "var _aufgabe_offen: bool = false\n")

rep("	_baue_aufgabe()\n	_baue_engpass_pille()\n",
    "	_baue_aufgabe()\n	_baue_chip_zeile()\n	_baue_engpass_pille()\n")
rep("	_stapel.add_child(_engpass_pille)\n", "	_chip_zeile.add_child(_engpass_pille)\n")

rep("""	box.add_child(zeile)
	_limit_leiste = UiStil.neuer_balken(22.0)""", """	box.add_child(zeile)
	# Kurzform (nicht voll): Beschriftung links, duenner Balken rechts, alles in einer Zeile.
	_limit_kurz = UiStil.label("", UiStil.GR_HINWEIS, UiStil.TINTE, UiStil.FETT)
	_limit_kurz.visible = false
	zeile.add_child(_limit_kurz)
	_limit_leiste = UiStil.neuer_balken(22.0)""")

rep("""	_limit_voll = voll
	var zustand: Array = [voll, UiStil.akzent()]""", """	_limit_voll = voll
	_setze_limit_form(not voll, texte, anteil)
	var zustand: Array = [voll, UiStil.akzent()]""")

rep("""func _aktualisiere_limit() -> void:""", """## Nicht voll: schlanke Kurzzeile (Text + duenner Balken). Voll: die grosse Karte mit Umbau-Knopf.
func _setze_limit_form(kompakt: bool, texte: Dictionary, anteil: float) -> void:
	if kompakt:
		_limit_kurz.text = String(texte.get("format", "%s  %d %%")) % [
			String(texte.get("titel", "")), int(round(clampf(anteil, 0.0, 1.0) * 100.0))]
	if kompakt == _limit_kompakt and _limit_feld.has_meta("form"):
		return
	_limit_feld.set_meta("form", true)
	_limit_kompakt = kompakt
	_limit_label.visible = not kompakt
	_limit_kurz.visible = kompakt
	_limit_leiste.custom_minimum_size.y = 10.0 if kompakt else 22.0
	_limit_feld.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A2) if kompakt else float(UiStil.A3)))


func _aktualisiere_limit() -> void:""")

rep("""	if e.is_empty() or tutorial_aktiv:
		_aufgabe_karte.visible = false
		return
	_aufgabe_karte.visible = true
""", """	if e.is_empty() or tutorial_aktiv:
		_aufgabe_karte.visible = false
		_aufgabe_chip.visible = false
		return
	# Eingeklappt (Standard): nur ein Chip in der Zeile mit dem Engpass. Eine fertige
	# Aufgabe klappt von selbst auf, damit man sie nicht uebersieht.
	var aufgeklappt: bool = _aufgabe_offen or bool(e.get("bereit", false))
	_aufgabe_karte.visible = aufgeklappt
	_aufgabe_chip.visible = not aufgeklappt
	_aufgabe_chip_text.text = "%s  %s/%s" % [UiText.t("aufgabe_leiste"),
		_ganz(float(e.get("ist", 0.0))), _ganz(float(e.get("soll", 1.0)))]
""")

# Aufgabenkarte: Tipp auf eine NICHT fertige Karte klappt sie wieder ein.
rep("""	var e: Dictionary = _aufgabe_eintrag()
	if e.is_empty() or not bool(e.get("bereit", false)):
		return
""", """	var e: Dictionary = _aufgabe_eintrag()
	if e.is_empty():
		return
	if not bool(e.get("bereit", false)):
		_aufgabe_offen = false
		_aktualisiere_aufgabe()
		return
""")

rep("""func _baue_engpass_pille() -> void:""", """## Eine Zeile am Stapelende: links der Aufgaben-Chip (eingeklappte Tagesaufgabe), rechts die Engpass-Pille.
func _baue_chip_zeile() -> void:
	_chip_zeile = HBoxContainer.new()
	_chip_zeile.add_theme_constant_override("separation", UiStil.A2)
	_chip_zeile.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stapel.add_child(_chip_zeile)
	_aufgabe_chip = PanelContainer.new()
	_aufgabe_chip.visible = false
	_aufgabe_chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_aufgabe_chip.custom_minimum_size = Vector2(0.0, UiStil.TIPPZIEL)
	_aufgabe_chip.mouse_filter = Control.MOUSE_FILTER_STOP
	_aufgabe_chip.add_theme_stylebox_override("panel", UiStil.karte(UiStil.PAPIER_2, UiStil.RADIUS_KARTE,
		UiStil.KONTUR, float(UiStil.A3)))
	_aufgabe_chip.gui_input.connect(func(e: InputEvent) -> void:
		if UiStil.ist_tipp(e):
			_aufgabe_offen = true
			_aktualisiere_aufgabe())
	_aufgabe_chip_text = UiStil.label("", UiStil.GR_TEXT, UiStil.TINTE, UiStil.FETT)
	_aufgabe_chip_text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_aufgabe_chip.add_child(_aufgabe_chip_text)
	_chip_zeile.add_child(_aufgabe_chip)
	var puffer := Control.new()
	puffer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	puffer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chip_zeile.add_child(puffer)


func _baue_engpass_pille() -> void:""")

if crlf:
    s = s.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
