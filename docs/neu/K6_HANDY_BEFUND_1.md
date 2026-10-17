# K6 Handy-Befund 1 (16.10.2026, Build f354b66, Redmi, Bilder shots/k6_handy/)

Gut:
- Menü bleibt beim Hoch-/Runterwischen offen (Scrollfehler behoben).
- Ziel-Geschenk: ein Tipp auf „Holen“ → Geld sofort, kein Fenster.
- Zielleiste überdeckt die Kopfleiste nicht mehr.
- Grüne Raum-Plakette „Der Flur 200“: Tipp kauft (wird laut Bastian auf „Tipp öffnet Raum-Menü“ umgestellt).
- Rand-Tab „200“ fährt auf Wunsch zum Flur (vom Spieler ausgelöst, ok).

Probleme:
1. Ohne Kamerafahrt liegt die gewählte Station UNTER dem Stationsmenü + Tutorialblase (h05, h07, h08, h09): man sieht nicht, was man ausbaut. → Beim Öffnen eines Stationsmenüs nur verschieben (kein Zoom), bis die Station über dem Panel sichtbar ist; oder Panel niedriger.
2. Tutorialblase + Panel + Zielleiste bedecken ~65 % des Bildes.
3. Debug-Knöpfe „Messdaten kopieren“/„+Geld“ sichtbar (nur Debug-Build; Release prüfen).
4. Logcat: „VIBRATE permission not found“ → Haptik wirkt nicht; Berechtigung im Export-Preset setzen.
5. Raumkauf-Fenster „Gekauft: Der Flur · Upload · Weiter“ braucht weiter einen Tipp (Bastian: kein OK-Drücken) → automatisch nach ~2 s schließen oder Tipp irgendwo.
6. Kaltstart zeigte ~20 s Schwarzbild (Splash) beim ersten Start nach Installation – beobachten.
