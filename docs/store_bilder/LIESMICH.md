# Store-Bilder

Sieben Aufnahmen im Format des Zielgeräts (1080 × 2400), erzeugt mit
`tools/vorschau.ps1`. Sie liegen bewusst **hier** und nicht unter `shots/` —
jener Ordner ist in `.gitignore` und für Diagnose-Screenshots gedacht, die
kommen und gehen. Diese sieben sind Auslieferungsmaterial.

**Reihenfolge für den Store-Eintrag** (siehe `docs/STORE_EINTRAG.md`):

| # | Datei | Was man sieht |
|---|---|---|
| 1 | `welt_1.png` | Das Zimmer: Matratze, Laminat, Heizkörper |
| 2 | `welt_2.png` | Derselbe Raum, ein Schreibtisch statt Klapptisch |
| 3 | `welt_3.png` | Parkett, Schreibtisch am Fenster, zwei Monitore |
| 4 | `welt_4.png` | Zwei Bereiche, Innenwand, mehrere Arbeitsplätze |
| 5 | `welt_5.png` | Loft, Sichtbeton, Serverschränke |
| 6 | `welt_6.png` | Ein Sessel, ein Bildschirm, ein Kamin |
| 7 | `abspann.png` | „Der Zähler läuft weiter" |

Bild 1 und 2 sehen absichtlich ähnlich aus. Das ist die Aussage von Akt 2:
derselbe Ort, später.

**Format: 1080 × 2160.** Play lehnt Telefon-Screenshots ab, deren lange
Seite mehr als doppelt so lang ist wie die kurze. Die Aufnahmen vom
Referenzgerät (1080 × 2400) sind 2,22 : 1 und damit ungültig; sie werden
skaliert und seitlich mit der Grundfarbe aufgefüllt, nicht beschnitten —
Kopfzeile und Ausbau-Knopf gehören ins Bild.

**Die Bilder stammen vom Handy, nicht aus der PC-Vorschau.** Die erste Fassung
kam aus der Vorschau, deren Fenster damals ein anderes Seitenverhältnis hatte
als das Gerät, und zeigte außerdem den Debug-Knopf „+1000".

**Neu erzeugen** (Handy per USB, Debug-Build installiert):

```bash
PKG=tech.wvmit.helloworld
aufnahme() {  # Name, Prüfschalter, Wartezeit
  adb shell am force-stop $PKG
  adb shell "run-as $PKG sh -c 'rm -f files/save.json files/save.backup.json; echo $2 > files/start_args.txt'"
  adb shell am start -n $PKG/com.godot.game.GodotAppLauncher >/dev/null
  sleep $3; adb exec-out screencap -p > "shots/store_roh_$1.png"
}
aufnahme eroeffnung "--nichts" 10
aufnahme welt_1 "--welt 1 --reich --store" 14
aufnahme welt_2 "--welt 2 --store" 20
for W in 3 4 5; do aufnahme welt_$W "--welt $W --reich --store" 14; done
aufnahme welt_6 "--welt 6 --store" 14
aufnahme abspann "--welt 6 --wechsel --store" 14
adb shell "run-as $PKG rm -f files/start_args.txt"
python art_source/icon/store_bilder.py
```

`--store` blendet Debug-Knopf und Tutorialkarte aus. Welt 2 und 6 ohne
`--reich`: In Welt 2 stünde der Speicher sonst bei 208 % mit großem
Umbau-Knopf über dem Raum, in Welt 6 erschiene sofort der Abspann.

**Das Handy dabei nicht anfassen.** Eine Aufnahme zeigte eine gestartete
Belohnungswerbung — das Protokoll bewies, dass es eine Berührung am Gerät war,
nicht das Spiel.
