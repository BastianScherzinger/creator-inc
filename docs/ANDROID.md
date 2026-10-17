# ANDROID — Entwicklung, Deployment, Sichtbarkeit

**Stand:** 2026-09-10 · Status: **Gerät verbunden, Spiegelung läuft**

## Gerätestatus

| Punkt | Stand |
|---|---|
| ADB-Verbindung | ✅ `uomviz4hayswde4d` · Redmi Note 12 Pro 5G |
| Screenshots vom Gerät | ✅ funktioniert (`tools/screenshot.ps1`) |
| **scrcpy-Spiegelung** | ✅ läuft — Handybildschirm auf dem PC-Monitor |
| APK-Transfer | ✅ `adb push`, 32 MB/s |
| **Automatische Installation** | ❌ von MIUI blockiert, siehe unten |

### Zwei Xiaomi-Fallen, die Zeit gekostet haben

**1. Defekte Datenverbindung sieht aus wie ein Android-Problem, ist aber keines.**
Solange Windows das Gerät als *„Unbekanntes USB-Gerät (Fehler beim Anfordern einer Gerätebeschreibung)"* führt, ist die Ursache physisch — Kabel, Buchse oder Port. Kein Debugging-Schalter hilft. **Diagnose:** `Get-PnpDevice -PresentOnly | Where-Object InstanceId -match USB`. Erscheint dort ein **ADB Interface**, ist die Verbindung in Ordnung.

**2. `INSTALL_FAILED_USER_RESTRICTED` — MIUI/HyperOS blockiert ADB-Installationen mit einem eigenen Schalter**, unabhängig vom normalen USB-Debugging:

```
Einstellungen -> Zusaetzliche Einstellungen -> Entwickleroptionen
  [x] Ueber USB installieren
  [x] USB-Debugging (Sicherheitseinstellungen)
```

Beides verlangt bei Xiaomi eine Anmeldung mit Mi-Konto. Solange es aus ist, weicht `deploy.ps1` automatisch auf `adb push` aus und öffnet den Installationsdialog auf dem Gerät — dann ist die Installation ein Tippen statt automatisch.

**Für den schnellen Zyklus muss der Schalter an sein.** Manuelles Antippen bei jedem Build zerstört die Iterationsgeschwindigkeit, die der ganze Aufbau bezweckt.

---

## 0. Gemessene Werte (2026-09-10)

| Größe | Wert | Anmerkung |
|---|---|---|
| **targetSdk des APK** | **36** | Mit `apkanalyzer manifest target-sdk` am gebauten APK gemessen. Erfüllt die Play-Pflicht ohne Gradle-Build |
| **minSdk des APK** | **24** | Entspricht ADR-011 |
| Build-Dauer (warm) | **24 s** | `godot --headless --export-debug`, nur `arm64-v8a` |
| Build-Dauer (kalt) | 34 s | Erster Lauf nach Projektänderung |
| APK-Größe (Debug) | 26,9 MB | Leeres Projekt, ein ABI |
| Werkzeug-Speicher | 3,25 GB | Deutlich unter der Schätzung von 6–10 GB |

**Damit ist der Zyklus bereits weit unter dem 2-Minuten-Ziel** — Installation und Start auf dem Gerät kommen noch hinzu, liegen erfahrungsgemäß aber im Sekundenbereich.

### Drei Fallstricke, die Zeit gekostet haben

1. **`godot.exe` ist eine GUI-Anwendung.** PowerShell wartet nicht auf sie, liefert keine Ausgabe und keinen Exit-Code. In Skripten **immer `godot_console.exe`** verwenden.
2. **`$ErrorActionPreference = 'Stop'` plus `2>&1`** macht unter PowerShell 5.1 Godots Fortschrittsausgabe (die auf stderr geht) zu einem terminierenden Fehler, obwohl der Build erfolgreich war. `'Continue'` verwenden und den Erfolg an der erzeugten Datei prüfen.
3. **`min_sdk`/`target_sdk` im Export-Preset lassen sich nur mit aktiviertem Gradle-Build überschreiben.** Ohne Gradle-Build gelten die Werte der vorkompilierten Vorlage — die hier ohnehin korrekt sind. Felder daher leer lassen.

### Aktuelle Werkzeuglage (September 2026)

- **`sdkmanager` ist deprecated.** Google hat auf die neue **Android CLI** umgestellt: `android sdk install <paket>`. `sdkmanager.bat` delegiert nur noch weiter und gibt eine Warnung aus.
- **Die Android CLI 1.0.16261425 stürzt beim Beenden ab** (Exit `0xC0000409`), nachdem sie korrekt heruntergeladen und entpackt hat. Der Exit-Code ist unbrauchbar — **Erfolg an der Existenz der Dateien prüfen**, nicht am Rückgabewert.
- **Godot 4.7 bringt scrcpy-Unterstützung mit** (`export/android/scrcpy/screen_size` in den Editor-Einstellungen) und legt Debug-Keystore sowie JDK-Pfad selbst an.

---

## 0.1 Installierte Pfade

| Was | Pfad |
|---|---|
| Android SDK | `C:\Android\Sdk` (kurz und ohne Leerzeichen — Gradle dankt es) |
| JDK 17 | `C:\Users\basti\AppData\Local\Programs\Microsoft\jdk-17.0.10.7-hotspot` |
| Export-Templates | `%APPDATA%\Godot\export_templates\4.7.2.stable` |
| Debug-Keystore | `%APPDATA%\Godot\keystores\debug.keystore` (von Godot erzeugt) |

---

## 1. Die Kernanforderung

> „Ich möchte am PC-Bildschirm sehen, wie es auf dem Handy aussieht."

Dafür gibt es drei Ebenen, die sich ergänzen — keine ersetzt die andere:

| Ebene | Werkzeug | Wofür | Grenze |
|---|---|---|---|
| 1. **PC-Vorschau** | `toolsorschau.ps1` | Rendert das Spiel in 1080×2400 und legt einen Screenshot ab. Funktioniert **ohne Gerät** | Zeigt keine echte Performance, keine Touch-Ergonomie |
| 2. Live-Spiegelung | **scrcpy** | Das echte Spiel auf dem echten Gerät, groß auf dem Monitor, mit Maus bedienbar | Braucht ein angeschlossenes Gerät |
| 3. Screenshots | `adb exec-out screencap` | **Der Agent sieht seine eigene Oberfläche** und beurteilt sie | Standbild, keine Bewegung |

### `toolsorschau.ps1` — die Rückfallebene

```powershell
.	oolsorschau.ps1 -Sekunden 4
```

Startet das Spiel am PC in der Auflösung des Referenzgeräts, wartet, speichert
einen Screenshot nach `shotsorschau.png` und beendet sich selbst.

**Entstanden, als die ADB-Verbindung mitten in der Arbeit ausfiel.** Ohne Bild
lässt sich eine Oberfläche nicht beurteilen — und blind weiterzubauen wäre
schlimmer als eine Pause. Die Vorschau fand im ersten Lauf sofort drei Fehler
in der Kulissenplatzierung.

Sie **ersetzt das Gerät nicht**: Bildrate, Speicher und Touch-Ergonomie zeigt
nur das Handy. Für Layout, Lesbarkeit und Bildaufbau reicht sie vollständig.

**Ebene 3 ist die wichtigste für die Arbeitsweise dieses Projekts.** Ohne sie beurteilt ein Programmierer seine eigene Oberfläche blind. Mit ihr wird jede UI-Task mit einem tatsächlich angesehenen Bild abgeschlossen.

---

## 2. Werkzeuge

| Werkzeug | Version | Lizenz | Größe | Zweck |
|---|---|---|---|---|
| **Godot** | 4.7.2 | MIT | ~150 MB | Engine (keine Installation, portable ausführbare Datei) |
| **Godot Export Templates** | 4.7.2 | MIT | ~1,5 GB | Android-Export |
| **Android SDK** Platform-Tools + Build-Tools + Platform 36 | aktuell | Google-Lizenz | ~4–8 GB | ADB, Signieren, Bauen |
| **JDK 17** | 17.0.10 | — | vorhanden ✅ | **Nicht neu installieren** |
| **scrcpy** | aktuell | Apache-2.0 | ~50 MB | Live-Spiegelung |
| Android Studio | — | — | — | **Wird nicht installiert.** Rund 10 GB für eine IDE, die hier nichts beiträgt — Godot bringt seinen eigenen Build-Weg mit |
| Emulator | — | — | — | **Wird nicht installiert.** Auf einer 4-Kern-U-CPU ohne dedizierte GPU langsamer und unehrlicher als das echte Gerät |

**Geschätzter Gesamtbedarf: 6–10 GB** von 69 GB frei. Genaue Messung in TASK 001.

---

## 3. Gerät vorbereiten (einmalig, durch den Auftraggeber)

1. **Einstellungen → Über das Telefon → siebenmal auf „Build-Nummer" tippen** → Entwickleroptionen freigeschaltet
2. **Entwickleroptionen → USB-Debugging** aktivieren
3. **Entwickleroptionen → Drahtloses Debugging** aktivieren (nach der ersten USB-Kopplung)
4. Gerät per USB anschließen, auf dem Handy die Anfrage „USB-Debugging zulassen?" bestätigen

Danach ist das Kabel nur noch für die erstmalige Kopplung nötig.

```powershell
adb devices                      # Gerät sichtbar?
adb tcpip 5555                   # auf WLAN umstellen
adb connect <handy-ip>:5555      # kabellos verbinden
```

---

## 4. Der Arbeitszyklus

```
Code ändern
    │
    ▼
.\deploy.ps1
    ├── godot --headless --export-debug "Android" build/game.apk
    ├── adb install -r build/game.apk
    ├── adb shell am start -n <package>/com.godot.game.GodotApp
    └── adb logcat -s godot:V *:E        (gefiltert, nur Relevantes)
    │
    ▼
scrcpy läuft daneben → Spiel groß auf dem Monitor, mit Maus bedienbar
```

**Zielzeit für den gesamten Zyklus: unter 2 Minuten.** Wird sie in TASK 003 überschritten, ist zu optimieren (kleinere Export-Vorlagen, Ein-ABI-Build für Debug, Godots eigener One-Click-Deploy).

**Ein-ABI-Debug-Builds:** Debug-Exporte werden nur für `arm64-v8a` gebaut. Das halbiert die Build-Zeit und die Paketgröße; Release-Builds enthalten alle nötigen Architekturen.

---

## 5. Visuelle Rückkopplung für den Agenten

```powershell
# tools/screenshot.ps1
adb exec-out screencap -p > "shots/$(Get-Date -Format yyyyMMdd-HHmmss).png"
```

**Verbindliche Regel:** Jede Task, die etwas Sichtbares verändert, endet mit einem Screenshot, der tatsächlich angesehen und anhand dieser Punkte beurteilt wird:

- Sind Touch-Ziele mindestens 48 dp groß? (Faustregel: etwa eine Fingerkuppe breit)
- Ist der Text bei Armlänge lesbar?
- Ist der Kontrast auch bei hoher Helligkeit ausreichend?
- Kollidiert etwas mit Notch, Statusleiste oder Gestenbereich?
- Ist die visuelle Hierarchie eindeutig — findet das Auge zuerst das Wichtigste?
- Ist der aktuelle Engpass ohne Text erkennbar? (siehe `GAME_DESIGN.md` §2)

---

## 6. Diagnose

```powershell
adb logcat -s godot:V *:E            # Godot-Ausgabe + alle Fehler
adb logcat -b crash                  # Absturzprotokoll
adb shell dumpsys meminfo <package>  # Speicherverbrauch
adb shell dumpsys gfxinfo <package>  # Frame-Zeiten
adb shell top -m 5                   # CPU-Last live
```

---

## 7. Store-relevante Vorgaben (aus `PLAY_COMPLIANCE.md`)

| Punkt | Wert | Quelle |
|---|---|---|
| `targetSdk` | **36** (Android 16) — Pflicht seit 31.08.2026 | [Play-Anforderung](https://support.google.com/googleplay/android-developer/answer/11926878) |
| `minSdk` | 24 (vorläufig, in Phase 11 zu prüfen) | ADR-011 |
| Release-Format | **AAB** (App Bundle) | Play-Pflichtformat |
| Debug-Format | APK (nur für Gerätetests) | — |
| Signieren | Upload-Key lokal, Play App Signing | ADR-013 |
| Ausrichtung | Hochformat, gesperrt | Genre-Standard, halbiert den UI-Aufwand |

### Release-Signing: niemals im Repository

`project/export_presets.cfg` **ist versioniert** — sie enthält nur das Debug-Preset, und das Debug-Signing läuft über Godots Editor-Einstellungen, nicht über diese Datei.

**Release-Keystore, Passwort und Alias dürfen dort niemals eingetragen werden.** Godot liest sie stattdessen aus Umgebungsvariablen, die außerhalb des Repositories gesetzt werden:

```powershell
$env:GODOT_ANDROID_KEYSTORE_RELEASE_PATH  = "C:\keys\upload.keystore"
$env:GODOT_ANDROID_KEYSTORE_RELEASE_USER  = "upload"
$env:GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD = "<...>"
```

Die Variablennamen sind am 14.10.2026 mit Godot 4.7.2 verifiziert (Testexport mit dem Debug-Key lief durch). Nach dem Export `Remove-Item Env:GODOT_ANDROID_KEYSTORE_RELEASE_*`.

### Release-Preset „Android Release“ (seit 14.10.2026)

- Zweites Preset in `project/export_presets.cfg`: Gradle-Build, `export_format=1` (AAB), alle vier ABIs, `version/code=1`, `version/name="1.0.0"`, Berechtigung `vibrate`. Paketname **`tech.wvmit.helloworld`** (Florins Konto).
- Die Android-Build-Vorlage liegt in `project/android/build` (aus `android_source.zip`, plus `project/android/.build_version`). **`project/android/build/.gdignore` muss bleiben**, sonst importiert Godot die Vorlage und Gradle bricht mit „file name must end with .xml or .png“ ab. Der Ordner wird bis ~1,7 GB groß (Gradle-Zwischenstände) — nicht ins Git (Wunsch an die Leitung: `.gitignore`).
- Bauen: `.	oolselease_aab.ps1` (Testlauf mit Debug-Key) bzw. mit `-Keystore/-Alias` für Florins Upload-Key. Dauer ~10 Minuten (vier ABIs). Ergebnis `build/helloworld.aab` (~125 MB, mit nur `arm64-v8a`+`armeabi-v7a` deutlich kleiner).
- Prüfung: `aapt` liest keine AABs; targetSdk steht im Gradle-Manifest `project/android/build/build/intermediates/merged_manifests/standardRelease/.../AndroidManifest.xml` (36 / min 24 / Code 1 / Name 1.0.0 geprüft). Exakt am Paket: `bundletool build-apks` + `aapt2 dump badging` (bundletool liegt auf diesem PC nicht).

**Warnung Keystore:** Der Upload-Keystore liegt außerhalb des Repositories und braucht eine Sicherungskopie an einem zweiten Ort. Geht er verloren, lässt sich die App nicht mehr aktualisieren — ein Wiederherstellungsverfahren über Google existiert, ist aber langwierig.
