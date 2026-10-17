#!/bin/bash
# u3_serie.sh -- wie serie.sh, aber startet die U3-Vorschauszene (Szene/Moment ohne main.gd-Schalter).
# Aufruf: bash tools/u3_serie.sh <name> [schalter ...]   z. B. --szene bsp_mo --variante b
cd "$(dirname "$0")/../project" || exit 1
name=$1
shift
mkdir -p ../shots/serie
timeout 120 godot_console --path . --resolution 540x1200 --position 20,20 res://game/ui/u3_vorschau.tscn -- --frisch --ohne-eroeffnung --bild "serie_$name" "$@" 2>&1 | grep -E "SCRIPT ERROR|Parse Error|ERROR" | head -8
mv "$APPDATA/Godot/app_userdata/Creator Inc/serie_$name.png" "../shots/serie/$name.png"
