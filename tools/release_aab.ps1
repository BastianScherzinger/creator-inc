# release_aab.ps1 -- baut das Play-Bundle build\creatorinc.aab (Preset "Android Release")
# Testlauf mit dem Debug-Key:      .\tools\release_aab.ps1
# Echter Upload-Key (nie im Repo): .\tools\release_aab.ps1 -Keystore C:\keys\upload.keystore -Alias upload
#   -> das Passwort wird abgefragt und nur fuer diesen Lauf in der Umgebung gehalten.
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
Remove-Item "$root\build\creatorinc.aab" -Force -ErrorAction SilentlyContinue
# Godot startet fuer den Export Gradle. Der Gradle-Daemon erbt die Ausgabe-Leitung und lebt weiter --
# mit "| Out-Null" wartet PowerShell dann ewig. Darum: kein Daemon, Ausgabe in Dateien, Warten mit
# Zeitgrenze, danach Gradle stoppen und uebrige Daemons beenden.
$env:GRADLE_OPTS = "-Dorg.gradle.daemon=false"
$proc = Start-Process -FilePath $GODOT -PassThru -NoNewWindow `
    -ArgumentList @("--headless", "--path", "`"$root\project`"", "--export-release", "`"Android Release`"", "`"$root\build\creatorinc.aab`"") `
    -RedirectStandardOutput "$root\build\aab_export.log" -RedirectStandardError "$root\build\aab_export_err.log"
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
if (Test-Path "$root\build\creatorinc.aab") {
    Write-Host ("OK  build\creatorinc.aab  {0:N1} MB" -f ((Get-Item "$root\build\creatorinc.aab").Length/1MB)) -ForegroundColor Green
} else { Write-Host "BUNDLE FEHLT -- Export fehlgeschlagen" -ForegroundColor Red; exit 1 }
