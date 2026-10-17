#!/bin/bash
# store_handy.sh -- Store-Bilder vom Handy (Debug-Build, Paket tech.wvmit.helloworld).
# Aufruf: bash tools/store_handy.sh <name> <wartezeit_s> [schalter ...]
# Ergebnis: shots/store_handy/<name>.png (Originalbild 1080x2400) und
#           docs/release/store/handy_<name>.png (1080x2160, ohne Alpha: Play erlaubt hoechstens 2:1;
#           tools/store_format.py verkleinert statt abzuschneiden).
# Startet immer mit --frisch --store (kein Spielstand, keine Debug-Knoepfe).
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.." || exit 1
P=tech.wvmit.helloworld
name=$1; warte=$2; shift 2
mkdir -p shots/store_handy
adb shell am force-stop $P
adb shell "run-as $P sh -c 'echo --frisch --store $* > files/start_args.txt'"
adb shell monkey -p $P -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
sleep "$warte"
adb exec-out screencap -p > "shots/store_handy/$name.png"
adb shell run-as $P rm -f files/start_args.txt
python tools/store_format.py "shots/store_handy/$name.png" "docs/release/store/handy_$name.png"
