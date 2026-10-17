#!/bin/bash
# pc_test.sh -- startet das Spiel im Handyformat mit der PC-Testumgebung (live) im Hintergrund.
# Aufruf:  bash tools/pc_test.sh [Spielschalter ...]        z. B.  bash tools/pc_test.sh --frisch --welt 6 --tiefe 3
# Ordner:  PC_ORDNER=<ordner> (Standard shots/pc_live).  Befehle senden:  bash tools/pc_cmd.sh "tipp 270 640"
# Beenden: bash tools/pc_cmd.sh ende
export MSYS_NO_PATHCONV=1
wurzel="$(cd "$(dirname "$0")/.." && pwd -W 2>/dev/null || pwd)"
ordner="${PC_ORDNER:-$wurzel/shots/pc_live}"
mkdir -p "$ordner"
: > "$ordner/befehle.txt"
: > "$ordner/log.txt"
cd "$wurzel/project" || exit 1
nohup godot_console --path . --resolution 540x1200 --position 20,20 -- "$@" --pc-test-live "$ordner" > "$ordner/godot.txt" 2>&1 &
echo $! > "$ordner/pid.txt"
for i in $(seq 1 100); do
	grep -q "bereit" "$ordner/log.txt" 2>/dev/null && { echo "bereit: $ordner"; exit 0; }
	sleep 0.3
done
echo "FEHLER: Spiel meldet sich nicht (siehe $ordner/godot.txt)"; tail -5 "$ordner/godot.txt"; exit 1
