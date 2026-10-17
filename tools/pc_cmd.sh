#!/bin/bash
# pc_cmd.sh -- haengt einen Befehl an befehle.txt und gibt die Antwortzeile aus log.txt zurueck.
# Aufruf:  bash tools/pc_cmd.sh "tipp 270 640"      (bei "bild x" nur der Bildpfad)
# Ordner:  PC_ORDNER=<ordner> (Standard shots/pc_live).  Zeitgrenze: PC_WARTE=<Sekunden> (Standard 60)
export MSYS_NO_PATHCONV=1
wurzel="$(cd "$(dirname "$0")/.." && pwd)"
ordner="${PC_ORDNER:-$wurzel/shots/pc_live}"
[ -f "$ordner/befehle.txt" ] || { echo "FEHLER: kein Lauf in $ordner (erst tools/pc_test.sh)"; exit 1; }
befehl="$*"
printf '%s\n' "$befehl" >> "$ordner/befehle.txt"
nr=$(wc -l < "$ordner/befehle.txt" | tr -d ' ')
grenze=$(( ${PC_WARTE:-60} * 10 ))
for i in $(seq 1 "$grenze"); do
	zeile=$(grep -F "] #$nr " "$ordner/log.txt" 2>/dev/null | tail -1)
	if [ -n "$zeile" ]; then
		case "$befehl" in
			bild*) echo "${zeile#*-> }" ;;
			*) echo "$zeile" ;;
		esac
		exit 0
	fi
	sleep 0.1
done
echo "FEHLER: keine Antwort auf '$befehl' (Spiel beendet?)"; exit 1
