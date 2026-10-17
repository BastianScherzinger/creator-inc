#!/bin/bash
# serie.sh -- rendert eine Vorschau mit Pruefschaltern nach shots/serie/<name>.png
# Aufruf:  bash tools/serie.sh <name> [schalter ...]
# Beispiel: bash tools/serie.sh 04_ziele --tiefe 2 --menue ziele
#
# Immer mit --frisch: Eine Vorschau darf nie den Stand der vorigen mitschleppen.
#
# --tiefe und --moment: Beim Vorspulen (--tiefe N) feuern Ziele und Stufen Belohnungs-Momente
# (Popup mitten im Bild) und verdecken die Vorschau. Darum haengt dieses Skript bei --tiefe
# automatisch `--moment aus` an, wenn kein eigener --moment-Schalter dabei ist.
# Einen Moment pruefen:  bash tools/serie.sh moment_ziel --tiefe 2 --moment ziel
# Schalter: --moment aus | ziel | marke | geschenk | raum | stern | offline | levelup
cd "$(dirname "$0")/../project" || exit 1
name=$1
shift
# --tiefe ohne eigenen --moment: Moment-Popups aus (sie verdecken sonst die Vorschau).
case " $* " in
	*" --tiefe "*) case " $* " in *" --moment "*) ;; *) set -- "$@" --moment aus ;; esac ;;
esac
mkdir -p ../shots/serie
timeout 120 godot_console --path . --resolution 540x1200 --position 20,20 -- --frisch --screenshot "${SHOT_WARTE:-3.5}" --bild "serie_$name" "$@" 2>&1 | grep -E "SCRIPT ERROR|Parse Error" | head -3
mv "$APPDATA/Godot/app_userdata/Creator Inc/serie_$name.png" "../shots/serie/$name.png"
