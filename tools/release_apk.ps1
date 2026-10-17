# release_apk.ps1 -- baut die Download-APK build\creatorinc.apk (Preset "Android APK",
# Paket com.scherzinger.creatorinc, nur arm64-v8a + armeabi-v7a) fuer den freien Download (GitHub Releases).
# Signiert mit dem Godot-Debug-Keystore dieses PCs: .\tools\release_apk.ps1
#   Achtung: Updates muessen mit DEMSELBEN Schluessel signiert sein, sonst muss man neu installieren.
# Eigener Schluessel (nie im Repo): .\tools\release_apk.ps1 -Keystore C:\keys\creatorinc.keystore -Alias creatorinc
param(
    [string]$Keystore = "$env:APPDATA\Godot\keystores\debug.keystore",
    [string]$Alias = "androiddebugkey"
)
$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
$GODOT = (Get-Command godot_console -ErrorAction SilentlyContinue).Source
if (-not $GODOT) { Write-Host "godot_console nicht gefunden (.\tools\check_env.ps1)" -ForegroundColor Red; exit 1 }
if (-not (Test-Path "$root\project\android\build\.gdignore")) { Write-Host "Build-Vorlage fehlt (siehe docs/ANDROID.md)" -ForegroundColor Red; exit 1 }
if ($Keystore -like "*debug.keystore") { $pw = "android" }
else { $pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR((Read-Host "Keystore-Passwort" -AsSecureString))) }
$env:GODOT_ANDROID_KEYSTORE_RELEASE_PATH = $Keystore
$env:GODOT_ANDROID_KEYSTORE_RELEASE_USER = $Alias
$env:GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD = $pw
New-Item -ItemType Directory -Force -Path "$root\build" | Out-Null
Remove-Item "$root\build\creatorinc.apk" -Force -ErrorAction SilentlyContinue
# Godot startet fuer den Export Gradle. Der Gradle-Daemon erbt die Ausgabe-Leitung und lebt weiter --
# mit "| Out-Null" wartet PowerShell dann ewig. Darum: kein Daemon, Ausgabe in Dateien, Warten mit
# Zeitgrenze, danach Gradle stoppen und uebrige Daemons beenden.
$env:GRADLE_OPTS = "-Dorg.gradle.daemon=false"
$proc = Start-Process -FilePath $GODOT -PassThru -NoNewWindow `
    -ArgumentList @("--headless", "--path", "`"$root\project`"", "--export-release", "`"Android APK`"", "`"$root\build\creatorinc.apk`"") `
    -RedirectStandardOutput "$root\build\apk_export.log" -RedirectStandardError "$root\build\apk_export_err.log"
$grenzeSekunden = 900
if (-not $proc.WaitForExit($grenzeSekunden * 1000)) {
    Write-Host "Export laeuft laenger als $grenzeSekunden s -- wird abgebrochen" -ForegroundColor Red
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}
$gradlew = "$root\project\android\build\gradlew.bat"
if (Test-Path $gradlew) { & $gradlew --stop 2>$null | Out-Null }
Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*GradleDaemon*" -or $_.CommandLine -like "*gradle-launcher*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Remove-Item Env:GRADLE_OPTS -ErrorAction SilentlyContinue
Remove-Item Env:GODOT_ANDROID_KEYSTORE_RELEASE_PATH, Env:GODOT_ANDROID_KEYSTORE_RELEASE_USER, Env:GODOT_ANDROID_KEYSTORE_RELEASE_PASSWORD -ErrorAction SilentlyContinue
if (Test-Path "$root\build\creatorinc.apk") {
    Write-Host ("OK  build\creatorinc.apk  {0:N1} MB" -f ((Get-Item "$root\build\creatorinc.apk").Length/1MB)) -ForegroundColor Green
} else { Write-Host "APK FEHLT -- Export fehlgeschlagen" -ForegroundColor Red; exit 1 }
