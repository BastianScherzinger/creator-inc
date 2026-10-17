"""Erzeugt die Klaenge des Spiels als WAV -- synthetisch, ohne Fremdmaterial.

Aufruf:
    python art_source/scripts/build_sounds.py

WARUM SYNTHESE STATT SAMPLE-BIBLIOTHEK:

1. Lizenzen. Ein Google-Play-Eintrag braucht eine saubere Herkunft fuer jedes
   Byte. "Irgendwo heruntergeladen, klang gut" ist genau die Sorte Altlast,
   die spaeter niemand mehr aufloesen kann. Diese Datei IST die Lizenz --
   der Klang entsteht aus Rechenvorschriften, die hier stehen.
2. Groesse. Sieben Klaenge zusammen unter 60 KB. Ein Paket gekaufter Samples
   waere ein Vielfaches davon, fuer Toene von einer Zehntelsekunde.
3. Aenderbarkeit. Ein Klang ist hier drei Zahlen, kein Audioeditor.

NUR STANDARDBIBLIOTHEK -- kein numpy, kein Fremdpaket. Das haelt die
Einrichtung auf einem neuen Rechner bei "Python installieren".

KEINE THEMENBEGRIFFE in den Dateinamen (Regel D3 / ADR-010): Die Klaenge
heissen nach ihrer ROLLE im System, nicht nach dem, was sie im Amt darstellen.
"sfx_ausbau", nicht "stempel".
"""

import math
import os
import struct
import wave

RATE = 22050          # Hz -- fuer kurze Interface-Klaenge voellig ausreichend
                      # und halb so gross wie 44,1 kHz.
AUSGABE = "project/assets/audio"

# Halbtonverhaeltnis. Alle Tonhoehen leiten sich davon ab, damit die Klaenge
# untereinander stimmen und nicht zufaellig gegeneinander schweben.
def ton(halbtoene: float, grund: float = 440.0) -> float:
    return grund * (2.0 ** (halbtoene / 12.0))


def huellkurve(i: int, laenge: int, anstieg: float, abfall: float) -> float:
    """Attack/Decay in Sekunden. Der Anstieg ist entscheidend: Ein Ton, der
    bei voller Lautstaerke beginnt, knackt -- das hoert man als Fehler, ohne
    sagen zu koennen, was fehlt."""
    t = i / RATE
    dauer = laenge / RATE
    if t < anstieg:
        return t / max(anstieg, 1e-6)
    rest = t - anstieg
    return math.exp(-rest / max(abfall, 1e-6))


def sinus(frequenz: float, dauer: float, anstieg: float = 0.004,
          abfall: float = 0.08, lautstaerke: float = 0.5,
          gleiten: float = 0.0, oberton: float = 0.0) -> list:
    """Ein Sinuston mit Huellkurve.

    `gleiten` ist der Faktor, um den sich die Frequenz ueber die Dauer
    verschiebt (1,06 = ein Halbton aufwaerts). Diese kleine Bewegung macht aus
    einem Piepen einen Klang -- statische Sinustoene wirken billig.
    `oberton` mischt die Oktave dazu und gibt dem Ton Koerper.
    """
    n = int(dauer * RATE)
    proben = []
    phase = 0.0
    for i in range(n):
        anteil = i / max(n - 1, 1)
        f = frequenz * (1.0 + (gleiten - 1.0) * anteil) if gleiten else frequenz
        phase += 2.0 * math.pi * f / RATE
        wert = math.sin(phase)
        if oberton > 0.0:
            wert += oberton * math.sin(2.0 * phase)
        proben.append(wert * lautstaerke * huellkurve(i, n, anstieg, abfall))
    return proben


def rauschen(dauer: float, abfall: float = 0.01,
             lautstaerke: float = 0.3, tiefpass: float = 0.35) -> list:
    """Gefiltertes Rauschen -- der Anschlag, den ein reiner Sinus nicht hat.

    Der Zufall ist ein eigener linearer Kongruenzgenerator statt `random`:
    Der Klang soll bei jedem Lauf BITGENAU derselbe sein, sonst aendert sich
    bei jedem Neubau die Datei und das Repository sammelt Rauschen im
    wortwoertlichen Sinn.
    """
    n = int(dauer * RATE)
    proben = []
    zustand = 12345
    letzter = 0.0
    for i in range(n):
        zustand = (1103515245 * zustand + 12345) % 2147483648
        roh = (zustand / 1073741824.0) - 1.0
        # Einpoliger Tiefpass: nimmt dem Rauschen die Schaerfe
        letzter += (roh - letzter) * tiefpass
        proben.append(letzter * lautstaerke * huellkurve(i, n, 0.0005, abfall))
    return proben


def mischen(*spuren) -> list:
    """Spuren additiv uebereinanderlegen, laengste bestimmt die Dauer."""
    laenge = max((len(s) for s in spuren), default=0)
    summe = [0.0] * laenge
    for spur in spuren:
        for i, wert in enumerate(spur):
            summe[i] += wert
    return summe


def nacheinander(*paare) -> list:
    """(versatz_in_sekunden, spur) -- fuer Motive aus mehreren Toenen."""
    laenge = 0
    for versatz, spur in paare:
        laenge = max(laenge, int(versatz * RATE) + len(spur))
    summe = [0.0] * laenge
    for versatz, spur in paare:
        start = int(versatz * RATE)
        for i, wert in enumerate(spur):
            summe[start + i] += wert
    return summe


def schreiben(name: str, proben: list) -> int:
    """Weich begrenzen und als 16-Bit-Mono-WAV ablegen.

    Die Begrenzung ist ein Tangens Hyperbolicus, kein hartes Abschneiden:
    Hartes Abschneiden erzeugt Oberwellen, die auf einem Handylautsprecher
    als Kratzen hoerbar werden.
    """
    os.makedirs(AUSGABE, exist_ok=True)
    pfad = os.path.join(AUSGABE, name + ".wav")

    # Kurze Rampe am Ende: Ein WAV, das mitten in der Schwingung endet,
    # knackt beim Abspielen -- derselbe Fehler wie ein fehlender Anstieg.
    ausblende = min(int(0.005 * RATE), len(proben))
    for i in range(ausblende):
        proben[len(proben) - ausblende + i] *= 1.0 - (i / max(ausblende - 1, 1))

    daten = bytearray()
    for wert in proben:
        begrenzt = math.tanh(wert)
        daten += struct.pack("<h", int(max(-1.0, min(1.0, begrenzt)) * 32000))

    with wave.open(pfad, "wb") as datei:
        datei.setnchannels(1)
        datei.setsampwidth(2)
        datei.setframerate(RATE)
        datei.writeframes(bytes(daten))
    return os.path.getsize(pfad)


# --- Die Klaenge -------------------------------------------------------------
# Alle liegen auf derselben Tonleiter (Grundton A). Das ist der Unterschied
# zwischen einem Spiel, das klingt, und einem, das piept: Wenn Ausbau,
# Meilenstein und Freischaltung zufaellige Frequenzen haetten, waere jede
# Ueberlagerung ein Missklang -- und in einem Idle-Game ueberlagert sich
# staendig etwas.

def sfx_tipp() -> list:
    """Antippen. Der meistgehoerte Klang des Spiels -- deshalb der leiseste
    und kuerzeste. Ein Klick, den man nach der zwanzigsten Wiederholung noch
    ertraegt, darf beim ersten Mal nicht beeindrucken wollen."""
    return mischen(
        sinus(ton(12), 0.05, anstieg=0.001, abfall=0.018, lautstaerke=0.22),
        rauschen(0.02, abfall=0.004, lautstaerke=0.10),
    )


def sfx_ausbau() -> list:
    """Ausbau gelungen. Aufwaerts gleitend -- die Bewegung nach oben ist die
    ganze Botschaft: Es ging voran."""
    return mischen(
        sinus(ton(0), 0.22, anstieg=0.003, abfall=0.075,
              lautstaerke=0.34, gleiten=1.19, oberton=0.30),
        sinus(ton(7), 0.20, anstieg=0.006, abfall=0.060,
              lautstaerke=0.20, gleiten=1.19),
        rauschen(0.03, abfall=0.006, lautstaerke=0.12),
    )


def sfx_meilenstein() -> list:
    """Meilenstein. Ein Dreiklang aufwaerts -- laenger und voller als der
    Ausbau, weil er selten kommt und etwas bedeuten soll."""
    return nacheinander(
        (0.00, sinus(ton(0), 0.26, abfall=0.10, lautstaerke=0.30, oberton=0.25)),
        (0.09, sinus(ton(4), 0.26, abfall=0.10, lautstaerke=0.30, oberton=0.25)),
        (0.18, sinus(ton(7), 0.40, abfall=0.16, lautstaerke=0.34, oberton=0.30)),
    )


def sfx_freischaltung() -> list:
    """Freischaltung. Vier Toene bis zur Oktave -- das groesste Ereignis im
    Klangbild, weil es das seltenste ist."""
    return nacheinander(
        (0.00, sinus(ton(0), 0.24, abfall=0.09, lautstaerke=0.26, oberton=0.22)),
        (0.10, sinus(ton(4), 0.24, abfall=0.09, lautstaerke=0.26, oberton=0.22)),
        (0.20, sinus(ton(7), 0.24, abfall=0.09, lautstaerke=0.28, oberton=0.25)),
        (0.30, sinus(ton(12), 0.55, abfall=0.22, lautstaerke=0.34, oberton=0.32)),
    )


def sfx_auftrag() -> list:
    """Ein Auftrag steht bereit. Zwei helle Toene im Quintabstand -- fordernd
    genug, um den Blick zu holen, kurz genug, um nicht zu draengen."""
    return nacheinander(
        (0.00, sinus(ton(12), 0.16, abfall=0.055, lautstaerke=0.26)),
        (0.07, sinus(ton(19), 0.24, abfall=0.085, lautstaerke=0.26)),
    )


def sfx_abgelehnt() -> list:
    """Nicht genug Geld. Tief, dumpf, kurz -- eine Absage, kein Fehleralarm.
    Der Spieler hat nichts falsch gemacht, er ist nur noch nicht so weit."""
    return mischen(
        sinus(ton(-24), 0.20, anstieg=0.002, abfall=0.055,
              lautstaerke=0.30, gleiten=0.90),
        sinus(ton(-19), 0.14, anstieg=0.002, abfall=0.035, lautstaerke=0.14),
    )


def sfx_hinweis() -> list:
    """Der Engpass hat gewechselt. Ein leiser Wink, mehr nicht: Dieses
    Ereignis tritt oft ein, und was oft eintritt, darf nicht laut sein."""
    return sinus(ton(9), 0.13, anstieg=0.008, abfall=0.040, lautstaerke=0.16)


def sfx_muenzen() -> list:
    """Geld kommt an: ein Ziel eingeloest, eine Blase angetippt. Sechs kurze,
    helle Toene dicht hintereinander -- Muenzen, die auf einen Stapel fallen.
    Er darf nach Belohnung klingen, weil er nur nach einer Handlung kommt."""
    toene = [12, 16, 19, 24, 19, 24]
    return nacheinander(*[
        (0.045 * i, mischen(
            sinus(ton(t), 0.12, anstieg=0.001, abfall=0.035, lautstaerke=0.20, oberton=0.35),
            rauschen(0.012, abfall=0.003, lautstaerke=0.05)))
        for i, t in enumerate(toene)])


def sfx_platz() -> list:
    """Ausstattung steht an ihrem Platz: ein weicher Aufsetzer und ein kleines
    Aufploppen. Anders als der Ausbau, damit man ohne hinzusehen weiss, dass
    etwas Neues im Raum steht und nicht nur eine Zahl gestiegen ist."""
    return nacheinander(
        (0.00, mischen(
            sinus(ton(-12), 0.10, anstieg=0.001, abfall=0.030, lautstaerke=0.32, gleiten=0.85),
            rauschen(0.03, abfall=0.010, lautstaerke=0.10, tiefpass=0.15))),
        (0.06, sinus(ton(7), 0.16, anstieg=0.003, abfall=0.050, lautstaerke=0.24, gleiten=1.12, oberton=0.25)),
    )


def sfx_raum() -> list:
    """Ein Raum wird bezogen. Ein Luftzug (Band und Kartons fliegen weg), dann
    ein Akkord, der stehen bleibt. Das groesste Ereignis in Welt 1 neben dem
    Abschluss -- und es kommt fuenfmal."""
    luft = rauschen(0.45, abfall=0.20, lautstaerke=0.22, tiefpass=0.08)
    return nacheinander(
        (0.00, luft),
        (0.18, sinus(ton(0), 0.70, abfall=0.30, lautstaerke=0.22, oberton=0.25)),
        (0.18, sinus(ton(4), 0.70, abfall=0.30, lautstaerke=0.18)),
        (0.18, sinus(ton(7), 0.70, abfall=0.30, lautstaerke=0.18)),
        (0.30, sinus(ton(12), 0.60, abfall=0.26, lautstaerke=0.20, oberton=0.2)),
    )


def sfx_blase() -> list:
    """Eine Tipp-Blase erscheint. Ein kurzes Aufperlen -- leise, weil es eine
    Einladung ist und keine Aufforderung."""
    return sinus(ton(14), 0.10, anstieg=0.004, abfall=0.030, lautstaerke=0.14, gleiten=1.25)


def sfx_kauf() -> list:
    """Kauf im Menue: ein weiches, warmes Doppel -- kuerzer und runder als der
    Ausbau, weil er haeufig kommt. Reserve fuer sounds.json (Paket B)."""
    return nacheinander(
        (0.00, mischen(sinus(ton(5), 0.09, anstieg=0.002, abfall=0.030, lautstaerke=0.26, oberton=0.30),
                       rauschen(0.012, abfall=0.003, lautstaerke=0.07))),
        (0.05, sinus(ton(12), 0.16, anstieg=0.003, abfall=0.055, lautstaerke=0.24, gleiten=1.05, oberton=0.25)),
    )


def sfx_levelup() -> list:
    """Stufenaufstieg: kleine Tonleiter aufwaerts, hell und freundlich. Zwischen
    Ausbau und Meilenstein -- mehr als eine Zahl, weniger als ein Fest."""
    return nacheinander(*[
        (0.06 * i, sinus(ton(t), 0.20 if i < 4 else 0.38, abfall=0.07 if i < 4 else 0.15,
                         lautstaerke=0.24 + 0.02 * i, oberton=0.28))
        for i, t in enumerate([0, 2, 4, 7, 12])])


def sfx_stern() -> list:
    """Stern verdient: heller Glanz, zwei hohe Toene mit Oberton, lang ausklingend."""
    return nacheinander(
        (0.00, sinus(ton(19), 0.30, anstieg=0.002, abfall=0.10, lautstaerke=0.22, oberton=0.45)),
        (0.07, sinus(ton(24), 0.45, anstieg=0.002, abfall=0.16, lautstaerke=0.24, oberton=0.40)),
        (0.07, rauschen(0.04, abfall=0.010, lautstaerke=0.05, tiefpass=0.8)),
    )


def sfx_fanfare() -> list:
    """Kurzer Sieg-Jingle (unter 1,5 s): Quarte-Quinte-Oktave mit Akkord am Ende."""
    akkord = [mischen(sinus(ton(t), 0.55, abfall=0.22, lautstaerke=0.16, oberton=0.3)) for t in (7, 11, 14)]
    return nacheinander(
        (0.00, sinus(ton(0), 0.14, abfall=0.06, lautstaerke=0.30, oberton=0.35)),
        (0.12, sinus(ton(0), 0.14, abfall=0.06, lautstaerke=0.30, oberton=0.35)),
        (0.24, sinus(ton(4), 0.16, abfall=0.07, lautstaerke=0.32, oberton=0.35)),
        (0.38, sinus(ton(7), 0.55, abfall=0.25, lautstaerke=0.34, oberton=0.35)),
        (0.38, akkord[1]),
        (0.38, akkord[2]),
        (0.38, sinus(ton(-12), 0.50, abfall=0.22, lautstaerke=0.20)),
    )


def sfx_konfetti() -> list:
    """Plopp mit Rascheln: tiefer Knall, danach hell gefiltertes Rauschen."""
    return nacheinander(
        (0.00, sinus(ton(-5), 0.09, anstieg=0.001, abfall=0.025, lautstaerke=0.30, gleiten=0.7)),
        (0.02, rauschen(0.30, abfall=0.09, lautstaerke=0.16, tiefpass=0.75)),
    )


def sfx_geschenk() -> list:
    """Schachtel oeffnen (Knack + Luft), dann Glitzer aus fallenden hohen Toenen."""
    glitzer = [(0.14 + 0.05 * i, sinus(ton(t), 0.14, anstieg=0.001, abfall=0.05, lautstaerke=0.14, oberton=0.4))
               for i, t in enumerate([28, 24, 26, 21, 24, 19])]
    return nacheinander(
        (0.00, mischen(rauschen(0.05, abfall=0.012, lautstaerke=0.16, tiefpass=0.3),
                       sinus(ton(-7), 0.08, abfall=0.025, lautstaerke=0.22, gleiten=1.15))),
        (0.05, rauschen(0.12, abfall=0.05, lautstaerke=0.07, tiefpass=0.1)),
        *glitzer,
    )


def sfx_zaehlen() -> list:
    """Leises Tick fuer hochzaehlende Zahlen. Sehr kurz; die Tonhoehe steigt
    ueber sounds.json (tonhoehe_schritt)."""
    return mischen(
        sinus(ton(17), 0.03, anstieg=0.0005, abfall=0.009, lautstaerke=0.20),
        rauschen(0.01, abfall=0.002, lautstaerke=0.05, tiefpass=0.6),
    )


KLAENGE = {
    "sfx_muenzen": sfx_muenzen,
    "sfx_platz": sfx_platz,
    "sfx_raum": sfx_raum,
    "sfx_blase": sfx_blase,
    "sfx_tipp": sfx_tipp,
    "sfx_ausbau": sfx_ausbau,
    "sfx_meilenstein": sfx_meilenstein,
    "sfx_freischaltung": sfx_freischaltung,
    "sfx_auftrag": sfx_auftrag,
    "sfx_abgelehnt": sfx_abgelehnt,
    "sfx_hinweis": sfx_hinweis,
    "sfx_kauf": sfx_kauf,
    "sfx_levelup": sfx_levelup,
    "sfx_stern": sfx_stern,
    "sfx_fanfare": sfx_fanfare,
    "sfx_konfetti": sfx_konfetti,
    "sfx_geschenk": sfx_geschenk,
    "sfx_zaehlen": sfx_zaehlen,
}


def main() -> None:
    print("")
    print("=== KLAENGE ===")
    gesamt = 0
    for name, bauen in KLAENGE.items():
        proben = bauen()
        groesse = schreiben(name, proben)
        gesamt += groesse
        print("  %-20s %6.0f ms  %5.1f KB"
              % (name, 1000.0 * len(proben) / RATE, groesse / 1024.0))
    print("")
    print("  %d Klaenge, zusammen %.1f KB" % (len(KLAENGE), gesamt / 1024.0))


if __name__ == "__main__":
    main()
