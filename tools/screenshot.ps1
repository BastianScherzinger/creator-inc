# screenshot.ps1 -- holt einen Screenshot vom angeschlossenen Geraet
# Aufruf:  .\tools\screenshot.ps1              -> shots/<zeitstempel>.png
#          .\tools\screenshot.ps1 -Name hud    -> shots/hud.png
#
# VERBINDLICH: Jede Task, die etwas Sichtbares aendert, endet damit --
# und das Bild wird tatsaechlich angesehen (siehe docs/ANDROID.md 5).

param([string]$Name = "")

$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
$root = Split-Path $PSScriptRoot -Parent
$dir  = Join-Path $root "shots"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

$dev = & adb devices 2>&1 | Select-String -Pattern "\tdevice$"
if (-not $dev) { Write-Host "Kein Geraet verbunden." -ForegroundColor Red; exit 1 }

if ($Name) { $datei = Join-Path $dir "$Name.png" }
else { $datei = Join-Path $dir ("{0}.png" -f (Get-Date -Format "yyyyMMdd-HHmmss")) }

# exec-out liefert Binaerdaten -- ueber cmd umleiten, damit PowerShell sie nicht verfaelscht
cmd /c "adb exec-out screencap -p > `"$datei`""

if ((Test-Path $datei) -and ((Get-Item $datei).Length -gt 0)) {
    Write-Host ("OK  {0}  ({1:N0} KB)" -f $datei, ((Get-Item $datei).Length/1KB)) -ForegroundColor Green
    Write-Host "`nPruefen: Touch-Ziele >= 48dp | Lesbarkeit | Kontrast | Safe Area | Engpass ohne Text erkennbar?" -ForegroundColor Cyan
} else {
    Write-Host "Screenshot fehlgeschlagen." -ForegroundColor Red
    exit 1
}
