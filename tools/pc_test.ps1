# pc_test.ps1 -- startet das Spiel im Handyformat mit der PC-Testumgebung (live) im Hintergrund.
# Aufruf:  .\tools\pc_test.ps1 [-Ordner shots\pc_live] [Spielschalter ...]   z. B.  .\tools\pc_test.ps1 --frisch --welt 6
# Befehle senden:  .\tools\pc_test.ps1 -Befehl "tipp 270 640"   (gibt die Logzeile zurueck; bei "bild x" den Pfad)
param([string]$Ordner = "", [string]$Befehl = "", [Parameter(ValueFromRemainingArguments = $true)][string[]]$Schalter)

$root = Split-Path $PSScriptRoot -Parent
if (-not $Ordner) { $Ordner = Join-Path $root "shots\pc_live" }
$Ordner = [IO.Path]::GetFullPath($Ordner)
$befehle = Join-Path $Ordner "befehle.txt"
$log = Join-Path $Ordner "log.txt"

if ($Befehl) {
    if (-not (Test-Path $befehle)) { Write-Host "FEHLER: kein Lauf in $Ordner"; exit 1 }
    [IO.File]::AppendAllText($befehle, "$Befehl`n")
    $nr = ([IO.File]::ReadAllLines($befehle)).Count
    for ($i = 0; $i -lt 600; $i++) {
        $z = Get-Content $log -ErrorAction SilentlyContinue | Where-Object { $_ -like "*] #$nr *" } | Select-Object -Last 1
        if ($z) { if ($Befehl -like "bild*") { ($z -split "-> ", 2)[1] } else { $z }; exit 0 }
        Start-Sleep -Milliseconds 100
    }
    Write-Host "FEHLER: keine Antwort"; exit 1
}

$GODOT = (Get-Command godot_console -ErrorAction SilentlyContinue).Source
if (-not $GODOT) { Write-Host "Godot nicht gefunden." -ForegroundColor Red; exit 1 }
New-Item -ItemType Directory -Force -Path $Ordner | Out-Null
Set-Content -Path $befehle -Value "" -NoNewline
Set-Content -Path $log -Value "" -NoNewline
$args2 = @("--path", "$root\project", "--resolution", "540x1200", "--position", "20,20", "--") + $Schalter + @("--pc-test-live", $Ordner)
$p = Start-Process -FilePath $GODOT -ArgumentList $args2 -PassThru -WindowStyle Minimized `
    -RedirectStandardOutput (Join-Path $Ordner "godot.txt") -RedirectStandardError (Join-Path $Ordner "godot_fehler.txt")
$p.Id | Set-Content (Join-Path $Ordner "pid.txt")
for ($i = 0; $i -lt 100; $i++) {
    if ((Get-Content $log -ErrorAction SilentlyContinue) -match "bereit") { Write-Host "bereit: $Ordner"; exit 0 }
    Start-Sleep -Milliseconds 300
}
Write-Host "FEHLER: Spiel meldet sich nicht" -ForegroundColor Red; exit 1
