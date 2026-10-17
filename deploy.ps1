# deploy.ps1 -- Build -> Installation aufs Geraet -> Start -> gefiltertes Log
# Aufruf:  .\deploy.ps1            (mit Log-Anzeige)
#          .\deploy.ps1 -NoLog     (ohne Log, kehrt sofort zurueck)
#          .\deploy.ps1 -BuildOnly (nur bauen, kein Geraet noetig)

param(
    [switch]$NoLog,
    [switch]$BuildOnly
)

# WICHTIG: 'Continue', nicht 'Stop'. Godot schreibt seine Fortschrittsausgabe auf
# stderr; unter PowerShell 5.1 wuerde 'Stop' das als terminierenden Fehler werten,
# obwohl der Build mit Exit-Code 0 erfolgreich war.
$ErrorActionPreference = 'Continue'
$PKG      = "tech.wvmit.helloworld"
# Godot 4.7 registriert die Launcher-Activity als activity-alias.
# "com.godot.game.GodotApp" (die eigentliche Activity) laesst sich NICHT
# direkt starten -- am start bricht mit einer Exception ab.
# Ermitteln mit: adb shell cmd package resolve-activity --brief <paket>
$ACTIVITY = "com.godot.game.GodotAppLauncher"
$APK      = "build\game.apk"
$root     = $PSScriptRoot

$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
$gesamt = [System.Diagnostics.Stopwatch]::StartNew()

# WICHTIG: godot.exe ist eine GUI-Anwendung -- PowerShell wartet nicht auf sie und
# liefert weder Ausgabe noch Exit-Code. Fuer Skripte immer godot_console.exe nehmen.
$GODOT = (Get-Command godot_console -ErrorAction SilentlyContinue).Source
if (-not $GODOT) { $GODOT = (Get-Command godot -ErrorAction SilentlyContinue).Source }
if (-not $GODOT) { Write-Host "Godot nicht gefunden. .\tools\check_env.ps1 ausfuehren." -ForegroundColor Red; exit 1 }

# --- 1. Build ---------------------------------------------------------------
Write-Host "[1/4] Build ..." -ForegroundColor Cyan
$sw = [System.Diagnostics.Stopwatch]::StartNew()
New-Item -ItemType Directory -Force -Path "$root\build" | Out-Null
if (Test-Path "$root\$APK") { Remove-Item "$root\$APK" -Force }
& $GODOT --headless --path "$root\project" --export-debug "Android" "$root\$APK" | Out-Null
$code = $LASTEXITCODE
# Erfolg wird an der tatsaechlich erzeugten Datei gemessen, nicht nur am Exit-Code
if ($code -ne 0 -or -not (Test-Path "$root\$APK")) {
    Write-Host "      BUILD FEHLGESCHLAGEN (Exit $code)" -ForegroundColor Red
    exit 1
}
$sw.Stop()
$mb = (Get-Item "$root\$APK").Length/1MB
Write-Host ("      OK  {0:N1}s  {1:N1} MB" -f $sw.Elapsed.TotalSeconds, $mb) -ForegroundColor Green

if ($BuildOnly) { Write-Host "`nNur Build angefordert. Fertig.`n"; exit 0 }

# --- 2. Geraet pruefen ------------------------------------------------------
Write-Host "[2/4] Geraet ..." -ForegroundColor Cyan
$dev = & adb devices 2>&1 | Select-String -Pattern "\tdevice$"
if (-not $dev) {
    Write-Host "      KEIN GERAET" -ForegroundColor Red
    Write-Host @"

      Pruefen:
        - USB-Debugging aktiv? (Entwickleroptionen)
        - Kabellos:  adb connect <handy-ip>:5555
        - Auf dem Handy die Debugging-Anfrage bestaetigen

      Das APK liegt trotzdem bereit: $APK
"@ -ForegroundColor Yellow
    exit 1
}
Write-Host "      OK  $($dev.Line.Trim())" -ForegroundColor Green

# --- 3. Installieren --------------------------------------------------------
Write-Host "[3/4] Installation ..." -ForegroundColor Cyan
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$inst = & adb install -r "$root\$APK" 2>&1
if ($inst -match "Success") {
    $sw.Stop()
    Write-Host ("      OK  {0:N1}s" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green
} elseif ($inst -match "INSTALL_FAILED_USER_RESTRICTED") {
    # Xiaomi/MIUI/HyperOS blockiert ADB-Installationen mit einem EIGENEN Schalter,
    # unabhaengig vom normalen USB-Debugging. Ohne ihn ist kein automatischer
    # Deploy moeglich -- deshalb hier der Umweg ueber den Dateitransfer.
    Write-Host "      BLOCKIERT durch MIUI/HyperOS" -ForegroundColor Yellow
    Write-Host @"

      Auf dem Handy einschalten:
        Einstellungen -> Zusaetzliche Einstellungen -> Entwickleroptionen
          [x] Ueber USB installieren
          [x] USB-Debugging (Sicherheitseinstellungen)
        (Beides verlangt bei Xiaomi eine Anmeldung mit Mi-Konto.)

      Solange das nicht an ist, schiebe ich das APK nur aufs Handy --
      Installation dann dort von Hand antippen.
"@ -ForegroundColor Yellow
    & adb push "$root\$APK" /sdcard/Download/amt-fuer-alles.apk | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      APK liegt auf dem Handy: Download/amt-fuer-alles.apk" -ForegroundColor Cyan
        # Dateimanager oeffnen, damit die Installation nur noch ein Tippen ist
        & adb shell am start -a android.intent.action.VIEW -t "application/vnd.android.package-archive" -d "file:///sdcard/Download/amt-fuer-alles.apk" 2>&1 | Out-Null
    }
    exit 2
} else {
    Write-Host "      FEHLGESCHLAGEN:" -ForegroundColor Red
    $inst | Select-Object -Last 5
    exit 1
}

# --- 4. Starten -------------------------------------------------------------
Write-Host "[4/4] Start ..." -ForegroundColor Cyan
& adb shell am start -n "$PKG/$ACTIVITY" | Out-Null
$gesamt.Stop()
Write-Host ("      OK`n") -ForegroundColor Green
Write-Host ("ZYKLUSZEIT GESAMT: {0:N1}s   (Ziel: unter 120s)" -f $gesamt.Elapsed.TotalSeconds) -ForegroundColor $(if ($gesamt.Elapsed.TotalSeconds -lt 120) { "Green" } else { "Yellow" })

if ($NoLog) { exit 0 }

Write-Host "`n--- Log (Strg+C zum Beenden) ---`n" -ForegroundColor Cyan
& adb logcat -c
& adb logcat -s godot:V *:E
