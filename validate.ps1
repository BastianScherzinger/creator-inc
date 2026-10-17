# validate.ps1 -- DAS Tor vor jedem Commit.
# Aufruf:  .\validate.ps1              (alles)
#          .\validate.ps1 -SkipBuild   (ohne Android-Build, schneller)
#
# Exit 0 = gruen, Exit 1 = rot. Kein Commit bei rot.

param([switch]$SkipBuild)

# 'Continue', nicht 'Stop': Godot schreibt Fortschritt auf stderr (siehe docs/ANDROID.md)
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")

# godot.exe ist eine GUI-App -- fuer Skripte immer die Konsolenvariante
$GODOT = (Get-Command godot_console -ErrorAction SilentlyContinue).Source
if (-not $GODOT) { $GODOT = (Get-Command godot -ErrorAction SilentlyContinue).Source }
if (-not $GODOT) { Write-Host "Godot nicht gefunden. .\tools\check_env.ps1 ausfuehren." -ForegroundColor Red; exit 1 }

$fehler = 0
$gesamt = [System.Diagnostics.Stopwatch]::StartNew()

function Schritt([string]$nr, [string]$name) {
    Write-Host "`n[$nr] $name" -ForegroundColor Cyan
}
function Ok([string]$text)    { Write-Host "      OK    $text" -ForegroundColor Green }
function Fail([string]$text)  { Write-Host "      FEHLER $text" -ForegroundColor Red; $script:fehler++ }

# ─── 1. Schichtentrennung (ARCHITECTURE.md 1) ────────────────────────────────
# core/ ist der headless testbare Wirtschaftskern. Sobald er etwas aus game/
# kennt oder Godot-Nodes benutzt, ist er nicht mehr ohne Szene testbar --
# und die zentrale Architekturentscheidung (ADR-004) ist gebrochen.
Schritt "1/7" "Schichtentrennung: core/ darf nichts aus game/ kennen"
$coreDir = Join-Path $root "project\core"
$verstoesse = @()
if (Test-Path $coreDir) {
    $muster = @('res://game/', 'res://services/', 'extends Node', 'get_tree\(', 'get_node\(', '\$"')
    foreach ($datei in Get-ChildItem $coreDir -Recurse -Filter *.gd) {
        $inhalt = Get-Content $datei.FullName -Raw
        foreach ($m in $muster) {
            if ($inhalt -match $m) {
                $verstoesse += "$($datei.FullName.Replace($root,'.')) : $m"
            }
        }
    }
}
if ($verstoesse.Count -gt 0) {
    Fail "$($verstoesse.Count) Verstoss(e):"
    $verstoesse | ForEach-Object { Write-Host "             $_" -ForegroundColor Red }
} else { Ok "keine Verstoesse" }

# ─── 2. Theme-Trennung (ADR-010 / Guardrail D3) ──────────────────────────────
# Kein thematischer Begriff ausserhalb von data/themes/. Diese Pruefung ist der
# Grund, warum der Themenwechsel Cannabis -> Amt eine Datenaenderung war und
# kein Rewrite. Sie bleibt in Kraft, auch wenn das aktuelle Thema harmlos ist.
Schritt "2/7" "Theme-Trennung: keine Themenbegriffe im Code"
$sperrwoerter = @(
    'cannabis','marijuana','weed','joint','thc','dealer',
    'buerger','bürger','formular','stempel','sachbearbeiter',
    'behoerde','behörde','amtsstube','amtsbote','wartemarke','gebuehr','gebühr'
)
$treffer = @()
foreach ($ordner in @("project\core","project\game","project\services")) {
    $pfad = Join-Path $root $ordner
    if (-not (Test-Path $pfad)) { continue }
    foreach ($datei in Get-ChildItem $pfad -Recurse -Include *.gd,*.tscn) {
        $inhalt = (Get-Content $datei.FullName -Raw).ToLower()
        foreach ($w in $sperrwoerter) {
            if ($inhalt -match "\b$w") {
                $treffer += "$($datei.FullName.Replace($root,'.')) : '$w'"
            }
        }
    }
}
if ($treffer.Count -gt 0) {
    Fail "$($treffer.Count) Themenbegriff(e) im Code -- gehoeren nach data/themes/ bzw. data/i18n/:"
    $treffer | ForEach-Object { Write-Host "             $_" -ForegroundColor Red }
} else { Ok "keine Themenbegriffe im Code" }

# ─── 3. Projektimport ────────────────────────────────────────────────────────
Schritt "3/7" "Projektimport (findet kaputte Referenzen)"
& $GODOT --headless --path "$root\project" --import 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Import fehlgeschlagen (Exit $LASTEXITCODE)" } else { Ok "Import sauber" }

# ─── 4. Tests ────────────────────────────────────────────────────────────────
# --ignoreHeadlessMode ist noetig: gdUnit4 blockiert Headless sonst wegen
# fehlender InputEvents. Unsere Core-Tests brauchen keine Eingaben.
Schritt "4/7" "Unit- und Integrationstests"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$ausgabe = & $GODOT --headless --path "$root\project" -s "res://addons/gdUnit4/bin/GdUnitCmdTool.gd" --ignoreHeadlessMode -a "res://tests" 2>&1
$testCode = $LASTEXITCODE
$sw.Stop()
$zeile = ($ausgabe | Select-String -Pattern "Overall Summary" | Select-Object -First 1)
if ($zeile) {
    $sauber = ($zeile.Line -replace "\x1b\[[0-9;]*m", "" -replace "\s+", " ").Trim()
    Write-Host "      $sauber" -ForegroundColor Gray
}
if ($testCode -ne 0) {
    Fail "Tests rot (Exit $testCode)"
    $ausgabe | Select-String -Pattern "FAILED|failure|Expecting" | Select-Object -First 12 |
        ForEach-Object { Write-Host "             $(($_.Line -replace '\x1b\[[0-9;]*m',''))" -ForegroundColor Red }
} else { Ok ("{0:N1}s" -f $sw.Elapsed.TotalSeconds) }

# ─── 5. Balance ──────────────────────────────────────────────────────────────
# Rechnet 60 simulierte Spielminuten durch und vergleicht mit der Zielkurve.
# Faengt Balance-Aenderungen ab, die den Verlauf unbeabsichtigt verschieben --
# ein Fehler, der sich sonst erst nach Stunden Spielzeit zeigen wuerde.
Schritt "5/7" "Balance-Simulation (60 Spielminuten)"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$simAusgabe = & $GODOT --headless --path "$root\project" -s "res://tools/balance_sim.gd" 2>&1
$simCode = $LASTEXITCODE
$sw.Stop()
$ergebniszeile = ($simAusgabe | Select-String -Pattern "ERGEBNIS:" | Select-Object -First 1)
if ($ergebniszeile) { Write-Host "      $(($ergebniszeile.Line).Trim())" -ForegroundColor Gray }
if ($simCode -ne 0) {
    Fail "Balance ausserhalb des Zielkorridors"
    $simAusgabe | Select-String -Pattern "^\d|Wartezeit" | Select-Object -First 12 |
        ForEach-Object { Write-Host "             $($_.Line)" -ForegroundColor Red }
} else {
    Ok ("{0:N1}s" -f $sw.Elapsed.TotalSeconds)
}

# ─── 6. Android-Build ────────────────────────────────────────────────────────
if ($SkipBuild) {
    Write-Host "`n[6/7] Android-Build   uebersprungen (-SkipBuild)" -ForegroundColor DarkGray
} else {
    Schritt "6/7" "Android-Debug-Build"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $apk = Join-Path $root "build\game.apk"
    New-Item -ItemType Directory -Force -Path (Join-Path $root "build") | Out-Null
    if (Test-Path $apk) { Remove-Item $apk -Force }
    & $GODOT --headless --path "$root\project" --export-debug "Android" $apk | Out-Null
    $sw.Stop()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $apk)) {
        Fail "Build fehlgeschlagen (Exit $LASTEXITCODE)"
    } else {
        Ok ("{0:N1}s  {1:N1} MB" -f $sw.Elapsed.TotalSeconds, ((Get-Item $apk).Length/1MB))
    }
}

# --- 7. Weltvollstaendigkeit -------------------------------------------------
# Eine Welt gilt erst als fertig, wenn sie OHNE Ersatzwelt startet.
#
# Fehlt einer Welt ein Raummodul, ein Stationsmodell oder die Themendatei,
# springt zur Laufzeit eine Ersatzwelt ein und schreibt eine Warnung. Das ist
# Absicht -- ohne Ersatz liesse sich eine Welt erst betreten, wenn ihr letztes
# Wandsegment modelliert ist. Aber eine Warnung im Log liest irgendwann
# niemand mehr, und ein Baugeruest, das niemand bemerkt, wird ausgeliefert.
#
# Diese Stufe zaehlt deshalb nach, was fehlt, und stellt es bei JEDEM Lauf als
# Liste hin. Sie ist absichtlich ein statischer Dateicheck und startet das
# Spiel nicht sechsmal -- das waere langsam und wuerde dasselbe messen.
#
# Schraegstriche in den Pfaden, keine Backslashes: PowerShell kommt damit
# zurecht, und die Datei ueberlebt so jeden Generator, der Backslashes als
# Escape-Zeichen liest.
Schritt "7/7" "Weltvollstaendigkeit: keine Welt haengt an einer Ersatzwelt"
$weltDatei = Join-Path $root "project/data/worlds/worlds.json"
if (-not (Test-Path $weltDatei)) {
    Fail "worlds.json fehlt"
} else {
    $welten = (Get-Content $weltDatei -Raw | ConvertFrom-Json).welten
    $struktur = @("raum_fliese_a","raum_fliese_b","raum_fliese_weg","raum_wand",
                  "raum_wand_ecke","raum_wand_tuer","raum_wand_fenster")
    $stationen = @("station_intake","station_buffer","station_processing",
                   "station_transport","station_special")
    $unfertig = @()
    foreach ($w in $welten) {
        $id = $w.id
        $luecken = @()
        if (-not (Test-Path "$root/project/data/themes/$id/theme.json")) { $luecken += "Texte" }
        if (-not (Test-Path "$root/project/data/balance/$id.json"))      { $luecken += "Balance" }
        foreach ($m in $struktur) {
            if (-not (Test-Path "$root/project/assets/room/$id/$m.glb")) { $luecken += "Raum/$m" }
        }
        foreach ($st in $stationen) {
            foreach ($stufe in 1..3) {
                if (-not (Test-Path "$root/project/assets/stations/$id/${st}_$stufe.glb")) {
                    $luecken += "Station/${st}_$stufe"
                }
            }
        }
        foreach ($k in $w.kulisse) {
            if (-not (Test-Path "$root/project/assets/world/$id/$($k.datei).glb")) { $luecken += "Kulisse/$($k.datei)" }
        }
        foreach ($a in $w.ausstattung) {
            if (-not (Test-Path "$root/project/assets/room/$id/$($a.datei).glb")) { $luecken += "Ausstattung/$($a.datei)" }
        }
        if ($luecken.Count -gt 0) {
            $unfertig += $id
            $kurz = (($luecken | Select-Object -Unique) | Select-Object -First 4) -join ", "
            $rest = ""
            if ($luecken.Count -gt 4) { $rest = " (+$($luecken.Count - 4) weitere)" }
            Write-Host "      OFFEN  $id -- $kurz$rest" -ForegroundColor Yellow
        }
    }
    if ($unfertig.Count -eq 0) {
        Ok "alle $($welten.Count) Welten vollstaendig"
    } else {
        # KEIN Fehler, solange Welten im Bau sind -- sonst waere waehrend der
        # ganzen Bauphase kein einziger Commit moeglich. Die Liste ist der
        # Zweck: Sie steht bei jedem Lauf da und laesst sich nicht uebersehen.
        Write-Host "      $($unfertig.Count) von $($welten.Count) Welten noch im Bau" -ForegroundColor Yellow
    }
}

# ─── Ergebnis ────────────────────────────────────────────────────────────────
$gesamt.Stop()
Write-Host ""
Write-Host ("-" * 60)
if ($fehler -gt 0) {
    Write-Host ("ROT -- $fehler Problem(e).  Kein Commit.   ({0:N1}s)" -f $gesamt.Elapsed.TotalSeconds) -ForegroundColor Red
    exit 1
}
Write-Host ("GRUEN -- alles sauber.  Commit frei.   ({0:N1}s)" -f $gesamt.Elapsed.TotalSeconds) -ForegroundColor Green
exit 0
