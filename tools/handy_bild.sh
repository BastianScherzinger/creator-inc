#!/bin/bash
# handy_bild.sh <name> -- Bildschirm des Handys nach shots/k7/<name>.png und halbe Groesse <name>_k.png
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.." || exit 1
mkdir -p shots/k7
adb exec-out screencap -p > "shots/k7/$1.png"
python -c "
from PIL import Image
im = Image.open('shots/k7/$1.png')
im.resize((im.width // 2, im.height // 2)).save('shots/k7/$1_k.png')
"
