#!/bin/bash
# Paket 2d: bash tools/w2d_bild.sh <name> <modus> [rang]  -> shots/serie/<name>.png
cd "$(dirname "$0")/../project" || exit 1
mkdir -p ../shots/serie
timeout 90 godot_console --path . --resolution 540x1200 --position 20,20 -s res://tools/w2d_vorschau.gd -- "$2" "user://$1.png" "${3:-5}" 2>&1 | grep -E "SCRIPT ERROR|Parse Error|ERROR" | head -5
mv "$APPDATA/Godot/app_userdata/Creator Inc/$1.png" "../shots/serie/$1.png"
