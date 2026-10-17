# vorschau.ps1 -- rendert das Spiel am PC im Handyformat und holt den Screenshot
#
# Ersetzt das Geraet NICHT (Performance und Touch zeigt nur das Handy),
# aber fuer Layout, Lesbarkeit und Bildaufbau reicht es -- und es funktioniert
# auch, wenn die ADB-Verbindung gerade ausfaellt.
#
# Aufruf:  .\tools\vorschau.ps1 [-Sekunden 5]

param([float]$Sekunden = 3.0, [switch]$Reich, [switch]$Laden, [switch]$Wechsel, [switch]$Durchlauf, [int]$Welt = 0)

$ErrorActionPreference = 'Continue'
$root = Split-Path $PSScriptRoot -Parent
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")

$GODOT = (Get-Command godot_console -ErrorAction SilentlyContinue).Source
if (-not $GODOT) { Write-Host "Godot nicht gefunden." -ForegroundColor Red; exit 1 }

New-Item -ItemType Directory -Force -Path "$root\shots" | Out-Null

# 540x1200 -- das SEITENVERHAELTNIS des Referenzgeraets (1080x2400, ADR-017)
# in halber Groesse.
#
# Vorher stand hier 1080x2400. Ein Fenster, das hoeher ist als der Bildschirm,
# kappt Windows aber auf die Bildschirmhoehe -- die Vorschau lief damit in
# einem deutlich breiteren Format als das Handy. Jede Position, die von oben
# gemessen wurde, sah am PC richtig aus und lag auf dem Geraet woanders. Das
# Bild ist jetzt kleiner, aber es zeigt dasselbe wie das Handy.
& $GODOT --path "$root\project" --resolution 540x1200 --position 20,20 `
    -- --screenshot $Sekunden $(if ($Reich) { "--reich" }) $(if ($Laden) { "--laden" }) `
       $(if ($Wechsel) { "--wechsel" }) $(if ($Durchlauf) { "--durchlauf" }) `
       $(if ($Welt -gt 0) { "--welt"; "$Welt" })

# Godot legt user:// unter %APPDATA%\Godot\app_userdata\<Projektname> ab
$quelle = Join-Path $env:APPDATA "Godot\app_userdata\Creator Inc\vorschau.png"
$ziel = Join-Path $root "shots\vorschau.png"
if (Test-Path $quelle) {
    Copy-Item $quelle $ziel -Force
    Write-Host ("OK  {0}  ({1:N0} KB)" -f $ziel, ((Get-Item $ziel).Length/1KB)) -ForegroundColor Green
} else {
    Write-Host "Kein Screenshot erzeugt. Erwartet unter:" -ForegroundColor Red
    Write-Host "  $quelle" -ForegroundColor Yellow
}
