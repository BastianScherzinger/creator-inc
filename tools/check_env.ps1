# check_env.ps1 -- prueft alle Werkzeuge der Entwicklungsumgebung
# Aufruf:  .\tools\check_env.ps1
# Exit 0 = alles vorhanden, Exit 1 = etwas fehlt

$ErrorActionPreference = 'Continue'
$fehler = 0

$SDK  = "C:\Android\Sdk"
$JAVA = "$env:LOCALAPPDATA\Programs\Microsoft\jdk-17.0.10.7-hotspot"
$TPL  = "$env:APPDATA\Godot\export_templates\4.7.2.stable"

function Pruefe([string]$name, [scriptblock]$test, [string]$hinweis) {
    Write-Host ("{0,-22}" -f $name) -NoNewline
    try {
        $wert = & $test
        if ($wert) { Write-Host "OK   $wert" -ForegroundColor Green; return }
    } catch { }
    Write-Host "FEHLT  $hinweis" -ForegroundColor Red
    $script:fehler++
}

Write-Host "`n=== Entwicklungsumgebung ===" -ForegroundColor Cyan

Pruefe "Godot" {
    (& godot --version 2>&1 | Select-Object -First 1)
} "winget install GodotEngine.GodotEngine"

Pruefe "Export-Templates" {
    if (Test-Path "$TPL\android_debug.apk") { "4.7.2.stable (Android)" }
} "Templates nach $TPL entpacken"

Pruefe "JDK 17" {
    if (Test-Path "$JAVA\bin\java.exe") {
        (& "$JAVA\bin\java.exe" -version 2>&1 | Select-Object -First 1)
    }
} "JDK 17 nicht gefunden"

Pruefe "ADB" {
    (& adb version 2>&1 | Select-Object -First 1)
} "winget install Google.PlatformTools"

Pruefe "scrcpy" {
    (& scrcpy --version 2>&1 | Select-Object -First 1)
} "winget install Genymobile.scrcpy"

Pruefe "Android Platform 36" {
    if (Test-Path "$SDK\platforms\android-36\android.jar") { "android-36" }
} "android sdk install 'platforms;android-36'"

Pruefe "Android Build-Tools" {
    if (Test-Path "$SDK\build-tools") {
        (Get-ChildItem "$SDK\build-tools" | Select-Object -Last 1).Name
    }
} "android sdk install 'build-tools;36.1.0'"

Pruefe "Android CLI" {
    if (Test-Path "$SDK\cmdline-tools\latest\bin\android.exe") { "cmdline-tools 23.0" }
} "cmdline-tools fehlen"

Write-Host "`n=== Geraet ===" -ForegroundColor Cyan
$geraete = (& adb devices 2>&1 | Select-String -Pattern "\tdevice$")
if ($geraete) {
    Write-Host "Android-Geraet         OK   verbunden" -ForegroundColor Green
} else {
    Write-Host "Android-Geraet         --   keins verbunden (fuer TASK 003 noetig)" -ForegroundColor Yellow
}

Write-Host "`n=== Speicher ===" -ForegroundColor Cyan
$frei = (Get-PSDrive C).Free/1GB
Write-Host ("Frei auf C:            {0:N2} GB" -f $frei) -ForegroundColor $(if ($frei -lt 15) { "Red" } else { "Green" })

if ($fehler -gt 0) {
    Write-Host "`n$fehler Werkzeug(e) fehlen.`n" -ForegroundColor Red
    exit 1
}
Write-Host "`nAlle Werkzeuge vorhanden.`n" -ForegroundColor Green
exit 0
