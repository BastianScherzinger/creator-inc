# -*- coding: utf-8 -*-
"""Quelle aller Story-Texte (Paket D). Daraus entstehen theme.json, balance.json und die Lesung.

Nachrichten-Eintrag: (id, von, text, antwort, slot)
  slot: "fix"   -> Ausloeser steht in FIX[welt][id] (oder bleibt aus dem alten Stand)
        "F"     -> Fortschrittsschwelle, wird aus der Probe berechnet
        "b1".."b5" -> Raum gekauft
        "ende"  -> Abschluss
"""

W = {}

# ---------------------------------------------------------------- WELT 1
W["zimmer"] = dict(
    absender={"plattform": "Dein Kanal", "mo": "Mo", "mira": "Mira", "tobi": "Tobi",
              "younes": "Younes", "du": "Du"},
    farben={"plattform": "#1B1726", "mo": "#3D7BFF", "mira": "#FF6FA8", "tobi": "#F59E0B",
            "younes": "#FF4FA3", "du": "#3D7BFF"},
    eroeffnung_chat=[
        ("mo", "Bruder."),
        ("mo", "Dein erster Clip hat drei Aufrufe."),
        ("mo", "Zwei davon warst du."),
        ("mo", "Der dritte war ich. Ich war sehr stolz."),
        ("du", "Und jetzt?"),
        ("mo", "Jetzt kaufen wir einen Gaming-PC. Das Handy auf dem Bücherstapel macht's nicht mehr lange."),
    ],
    eroeffnung_text="Dein erster Clip hat drei Aufrufe. Zwei davon warst du. Mo sagt, der dritte war er.\n\nZiel: der erste Gaming-PC.",
    nachrichten=[
        ("nachricht_01", "mo", "Abonnent Nummer 1. Das bin ich. Ein Danke reicht.", "Danke.", "fix"),
        ("nachricht_02", "mira", "Dein Zimmer sieht aus wie ein Studio. Und meine Lampe ist weg. Zufall?", None, "fix"),
        ("nachricht_03", "mo", "Bruder, du rüstest auf! Ich steh vor der Kamera, du schneidest. Deal?", "Deal.", "fix"),
        ("nachricht_04", "plattform", "100 Aufrufe. 61 davon sind Mo.", None, "fix"),
        ("nachricht_05", "mira", "Der Router steht im Flur. Das WLAN im Bad ist jetzt besser als in meinem Zimmer. Danke?", None, "b1"),
        ("nachricht_16", "mo", "Ich hab ausgerechnet, was ein richtiger Gaming-PC kostet. Setz dich lieber hin.", None, "F"),
        ("nachricht_06", "tobi", "Ich koch heute für drei. Mo ist der dritte. Er weiß es schon.", None, "b2"),
        ("nachricht_17", "mo", "Die Leute wollen uns zocken sehen. Ich hab dem PC schon einen Platz freigehalten: neben dem Nudeltopf.", None, "F"),
        ("nachricht_07", "mira", "Dein Schreibtisch summt. Ich hab Kopfhörer auf und hör's trotzdem. Ist das normal?", None, "F"),
        ("nachricht_18", "plattform", "1.000 Aufrufe. 400 davon Mo. Er hat sich ein zweites Konto gemacht.", None, "F"),
        ("nachricht_09", "mo", "Sofa, Fernseher, Chat. Ab heute streamen wir abends. Ich bring die Chips, du das Gesicht.", None, "b3"),
        ("nachricht_08", "tobi", "Neues Schild in der Küche: „Nach 22 Uhr nur leise Nudeln.“ Mo hat es als Herausforderung gelesen.", None, "F"),
        ("nachricht_19", "mira", "Die Nachbarin fragt, ob du der aus dem Stream bist. Ich hab „nie gesehen“ gesagt. Reflex.", None, "F"),
        ("nachricht_10", "plattform", "Euer Stream hatte 1.000 Zuschauer gleichzeitig. Mo hat allen gewunken.", None, "F"),
        ("nachricht_20", "mo", "Bruder, 1.000 Leute! Ich hab Autogramme geübt, auf Tobis Kühlschrank. Er weiß es noch nicht.", None, "F"),
        ("nachricht_11", "tobi", "Ich zieh zum Ersten aus. Willst du mein Zimmer? Der Topf bleibt.", "Ja.", "b4"),
        ("nachricht_12", "mira", "Du filmst auf dem Balkon? Die Nachbarn winken seit Dienstag.", None, "F"),
        ("nachricht_14", "mo", "Mein Cousin Younes hat eine Kamera, die teurer ist als mein Auto. Ich hab kein Auto. Aber trotzdem.", None, "b5"),
        ("nachricht_13", "plattform", "126.000 Aufrufe. Mo sagt 127.000. Er zählt sich dreimal.", None, "F"),
        ("nachricht_21", "mira", "Ein Paket für dich. Es ist groß. Es piept. Soll ich Angst haben?", None, "F"),
        ("nachricht_22", "mo", "Er bootet, Bruder. Ich hör die Lüfter. Klingt wie ein Hubschrauber.", None, "F"),
        ("nachricht_15", "younes", "Mo sagt, du schneidest. Ich hab eine Garage und ein Rolltor, das klemmt. Bring Kaffee.", "Morgen.", "ende"),
    ],
    abschluss=dict(
        titel="Der Gaming-PC steht",
        text="Die WG ist fertig. Auf deinem Schreibtisch leuchtet der Gaming-PC. Mo hat geweint. Er sagt, es war der Lüfter.\n\nEine Nachricht von Younes.",
        antwort="Morgen."),
    weltwechsel=dict(titel="Das Studio",
                     text="Eine Garage im Hinterhof, ein Rolltor, das klemmt. Younes wartet schon. Er hat die Lampen dreimal verstellt.",
                     figur="mit Younes"),
    offline_von="mo",
    offline_saetze=[
        "Bruder, du warst weg. Ich hab deine Clips für dich geguckt. Alle. Zweimal.",
        "Es lief die ganze Zeit. Ich glaub, ich hab geholfen. Ich hab Chips gebracht.",
        "Ich hab den Kanal bewacht, während du weg warst. Gegessen hab ich auch.",
    ],
    danach={
        "bereich_1": "Der Upload zieht ein. Das WLAN im Bad wird noch besser.",
        "bereich_2": "Alle Stationen werden schneller. Tobi kocht, Mo isst, der Rest läuft.",
        "bereich_3": "Der Stream zieht ein. Mo bringt die Chips.",
        "bereich_4": "Die Aufnahme wird besser. Dein Gesicht bekommt Farbe.",
        "bereich_5": "Alles wird schneller. Und Tobis Topf bleibt.",
    },
)

# ---------------------------------------------------------------- WELT 2
W["auftrag"] = dict(
    absender={"plattform": "Dein Kanal", "younes": "Younes", "mo": "Mo", "marke": "Eine Marke",
              "roman": "Roman", "du": "Du"},
    farben={"plattform": "#1B1726", "younes": "#FF4FA3", "mo": "#3D7BFF", "marke": "#5A5368",
            "roman": "#FF7A1A", "du": "#FF4FA3"},
    nachrichten=[
        ("nachricht_01", "younes", "Kein Kaffee. Ich hab's notiert. Miete zahlen wir hier übrigens in Videos.", None, "fix"),
        ("nachricht_02", "mo", "Ich hab dem Rolltor einen Namen gegeben. Es heißt Problem.", None, "fix"),
        ("nachricht_03", "younes", "Das Licht ist falsch. Take 3.", None, "fix"),
        ("nachricht_04", "mo", "Die Festplatten sind voll. Ich hab nur ein Video gelöscht. Das falsche. Younes redet nicht mehr mit mir.", None, "fix"),
        ("nachricht_05", "younes", "Im Hof steht ein Container. Da passt ein Server rein. Mein Onkel weiß es noch nicht.", None, "b1"),
        ("nachricht_16", "plattform", "1.000 Abonnenten. Mo hat jeden einzeln begrüßt.", None, "F"),
        ("nachricht_06", "younes", "Das Archiv läuft. Ab jetzt löscht hier niemand mehr etwas. Auch nicht Mo.", None, "fix"),
        ("nachricht_07", "mo", "Im Requisitenlager steht ein Thron. Ich hab mich nur kurz draufgesetzt. Younes filmt es trotzdem.", None, "b2"),
        ("nachricht_17", "younes", "Take 14 war gut. Take 15 war besser. Wir nehmen 16.", None, "F"),
        ("nachricht_18", "plattform", "10.000 Abonnenten. Younes sagt, das ist erst der Anfang.", None, "F"),
        ("nachricht_09", "mo", "Ich war eben auf dem Mond. Es war die Garage mit grünem Tuch. War schön.", None, "b3"),
        ("nachricht_08", "younes", "Ich will dich anstellen. Also eigentlich willst du mich anstellen. Ich bin teuer.", None, "F"),
        ("nachricht_19", "marke", "Wir würden gern mit euch arbeiten. Das Budget ist da. Die Frist ist heute.", None, "F"),
        ("nachricht_10", "plattform", "Ein Video hat eine Million Aufrufe. Younes sieht sich den Schnitt trotzdem noch mal an.", None, "F"),
        ("nachricht_20", "mo", "Eine Million, Bruder. Younes hat gesagt: „Naja.“ Ich hab Gänsehaut und er sagt Naja.", None, "F"),
        ("nachricht_11", "younes", "Auf dem Dach ist das Licht um sieben perfekt. Sei um sechs da.", None, "b4"),
        ("nachricht_12", "mo", "Wenn der Kinoraum fertig ist, will ich einen Stammplatz. Mit Schild. Das Schild hab ich schon.", None, "F"),
        ("nachricht_14", "younes", "Ein Designer hat geschrieben. Er hat elf Fehler in unserem Intro gefunden. Ich mag ihn.", None, "b5"),
        ("nachricht_13", "plattform", "Vier Marken im Postfach. Younes hat noch auf keine geantwortet. Er liest noch.", None, "F"),
        ("nachricht_21", "mo", "Auf dem Teamfoto hat Younes gelächelt. Nicht lange. Ein halbes Frame. Ich hab's gesehen.", None, "F"),
        ("nachricht_22", "younes", "Fertig. Das erste Video, bei dem ich nichts mehr ändern will. Gut so.", None, "F"),
        ("nachricht_15", "roman", "Euer Logo ist falsch gesetzt. Ich hab's neu gemacht. Und 380 Shirts bestellt.", "Warum 380?", "ende"),
    ],
    abschluss=dict(
        titel="Gut so",
        text="Das Studio ist fertig. Younes hat zum ersten Mal „gut so“ gesagt. Er hat es sofort bereut.\n\nEine Nachricht von Roman.",
        antwort="Warum 380?"),
    weltwechsel=dict(titel="Der Merch-Laden",
                     text="Ein Eckladen mit Schaufenster. Roman hat schon ausgerechnet, wie viele Shirts in den Keller passen.",
                     figur="mit Roman"),
    offline_von="younes",
    offline_saetze=[
        "Ich hab die Takes gezählt, während du weg warst. Achtunddreißig. Du hast nichts verpasst.",
        "Die Videos sind fertig geworden. Ich hab alle gesehen. Eins davon war gut.",
        "Das Rolltor hat geklemmt. Mo sagt, es hat Charakter. Ich sage nichts.",
    ],
    danach={
        "bereich_1": "Der Render-Server zieht ein. Laut, warm, zuverlässig.",
        "bereich_2": "Alle Stationen werden schneller. Und ein Thron, auf dem keiner sitzt.",
        "bereich_3": "Die Sponsoren ziehen ein. Und Mo auf dem Mond.",
        "bereich_4": "Der Dreh wird besser. Um sieben ist das Licht perfekt.",
        "bereich_5": "Alles wird schneller. Und Mos Stammplatz mit Schild.",
    },
)

# ---------------------------------------------------------------- WELT 3
W["webseiten"] = dict(
    absender={"plattform": "Dein Shop", "roman": "Roman", "mo": "Mo", "younes": "Younes",
              "kundin": "Eine Kundin", "du": "Du"},
    farben={"plattform": "#1B1726", "roman": "#FF7A1A", "mo": "#3D7BFF", "younes": "#FF4FA3",
            "kundin": "#5A5368", "du": "#FF7A1A"},
    nachrichten=[
        ("nachricht_01", "roman", "380 Shirts. Weil 400 zu rund war. Und ja, das Logo sitzt jetzt richtig.", None, "fix"),
        ("nachricht_02", "mo", "Ich hab das erste Shirt gekauft. Mit Rabatt. Ich bin schließlich im Video.", None, "fix"),
        ("nachricht_03", "roman", "Der Druck ist schief. Nicht viel. Ich sehe es trotzdem. Und die Pakete stapeln sich auf meinem Stuhl.", None, "fix"),
        ("nachricht_04", "plattform", "10 Bestellungen. 6 davon sind Mo.", None, "fix"),
        ("nachricht_05", "roman", "Der Laden ist offen. Mein Stuhl ist wieder ein Stuhl.", None, "b1"),
        ("nachricht_16", "plattform", "100 Bestellungen. 38 gehen an dieselbe Adresse. Mo hat Freunde.", None, "F"),
        ("nachricht_06", "roman", "Der Keller ist frei. 380 Shirts passen rein. 381 nicht. Ich hab's probiert.", None, "b2"),
        ("nachricht_17", "kundin", "Zweites Mal bestellt. Das Paket riecht nach Druckfarbe. Gut so.", None, "F"),
        ("nachricht_07", "roman", "Ich hab die Bestellungen nachgezählt. Drei fehlen. Ich hab sie gefunden. Sie waren in Mos Rucksack.", None, "F"),
        ("nachricht_18", "plattform", "1.000 Bestellungen. 0 Retouren. Roman hat nachgefragt, ob das ein Fehler ist.", None, "F"),
        ("nachricht_09", "roman", "Der Showroom ist frei. Eine Bühne, drei Puppen, eine Schlange bis zur Ecke.", None, "b3"),
        ("nachricht_08", "younes", "Ich film den ersten Drop. Stell die Leute nicht in die Sonne. Take 1. Ich meine das ernst.", None, "F"),
        ("nachricht_19", "mo", "Die Puppen heißen jetzt Gerd, Gerd und Gerd. Ich bitte um Respekt.", None, "F"),
        ("nachricht_10", "roman", "Der Drop war in 4 Minuten weg. Ich hab die Sekunden mitgezählt: 243.", None, "F"),
        ("nachricht_20", "kundin", "Drittes Mal bestellt. Mein Hund liegt auf dem Paket. Er riecht nach Druckfarbe. Gut so.", None, "F"),
        ("nachricht_11", "roman", "Fotostudio. Unsere Produktfotos sehen aus wie von einem Handy auf einem Bücherstapel.", None, "b4"),
        ("nachricht_14", "mo", "Handy auf einem Bücherstapel? Erinnert mich an was. Die Siebdruckmaschine heißt übrigens Siebi.", None, "b5"),
        ("nachricht_12", "roman", "Siebdruck im Hinterzimmer. Ab jetzt drucken wir zu zweit. Ich habe den Namen Siebi nicht genehmigt.", None, "F"),
        ("nachricht_13", "mo", "Roman hat einen Zollstock bestellt. Einen großen. Das ist kein gutes Zeichen.", None, "F"),
        ("nachricht_21", "roman", "Der Laden ist zu klein. Ich hab gemessen. Er war es schon vor dem Showroom.", None, "F"),
        ("nachricht_22", "plattform", "100.000 Bestellungen. Mo hat nicht alle selbst gemacht.", None, "F"),
        ("nachricht_15", "roman", "Drei Marken wollen, dass wir für sie verschicken. Die Halle ist zu groß. Ich hab sie trotzdem gemietet.", "Wie groß?", "ende"),
    ],
    abschluss=dict(
        titel="Ausverkauft",
        text="Der Laden ist fertig. Vor der Tür steht jemand mit deinem Hoodie. Roman hat die Minuten gezählt.\n\nEine Nachricht von Roman.",
        antwort="Wie groß?"),
    weltwechsel=dict(titel="Das Lager",
                     text="Eine Halle am Stadtrand. Vier Shops, ein Förderband und Roman mit Klemmbrett.",
                     figur="mit Roman"),
    offline_von="roman",
    offline_saetze=[
        "Während du weg warst, sind Pakete rausgegangen. Ich habe mitgezählt. Es stimmt.",
        "Die Schlange war bis zur Ecke. Ich habe sie nicht gezählt. Es war schwer.",
        "Der Druck war nur ein bisschen schief. Ich habe es trotzdem gesehen.",
    ],
    danach={
        "bereich_1": "Der Versand zieht ein. Roman bekommt seinen Stuhl zurück.",
        "bereich_2": "Alle Stationen werden schneller. 380 Shirts passen rein. 381 nicht.",
        "bereich_3": "Der Drop zieht ein. Eine Bühne, drei Puppen.",
        "bereich_4": "Der Druck wird besser. Die Fotos auch.",
        "bereich_5": "Alles wird schneller. Siebdruck zu zweit.",
    },
)

# ---------------------------------------------------------------- WELT 4
W["buero"] = dict(
    absender={"plattform": "Dein Shop", "roman": "Roman", "mo": "Mo", "younes": "Younes",
              "grosshaendler": "Ein Großhändler", "unbekannt": "Unbekannte Nummer",
              "jana": "Jana", "du": "Du"},
    farben={"plattform": "#1B1726", "roman": "#FF7A1A", "mo": "#3D7BFF", "younes": "#FF4FA3",
            "grosshaendler": "#5A5368", "unbekannt": "#5A5368", "jana": "#12B5A5", "du": "#12B5A5"},
    nachrichten=[
        ("nachricht_01", "roman", "Vier Shops, ein Lager, eine Tabelle mit sieben Reitern. Ich schlafe schlecht.", None, "fix"),
        ("nachricht_02", "mo", "Darf ich mit dem Hubwagen fahren? Nur einmal! Er heißt Hubert.", None, "fix"),
        ("nachricht_05", "roman", "Das Förderband ist da. Ab jetzt laufen die Pakete, nicht wir.", None, "b1"),
        ("nachricht_03", "mo", "Roman hat eine Packerin eingestellt. Jana. Sie hat ihm in zwanzig Sekunden seinen eigenen Tisch erklärt.", None, "fix"),
        ("nachricht_04", "jana", "Tisch war zu niedrig. Hab ich geändert. Geht jetzt schneller.", None, "fix"),
        ("nachricht_16", "mo", "Ich hab das Förderband Frank genannt. Frank läuft. Frank ist ein guter Junge.", None, "F"),
        ("nachricht_06", "roman", "Wareneingang. Vier Paletten, eine Unterschrift und kein Reiter in der Tabelle, der das vorhergesehen hat.", None, "b2"),
        ("nachricht_17", "jana", "Pausenzeiten waren falsch. Hab ich geändert. Roman weiß es noch nicht.", None, "F"),
        ("nachricht_07", "younes", "Ich hab das Lager gefilmt. Ein Förderband ist erstaunlich beruhigend.", None, "F"),
        ("nachricht_18", "roman", "Jana hat meine Pausenzeiten geändert, ohne zu fragen. Sie hatte recht. Die Tabelle hat jetzt drei Reiter. Mir ist schwindelig.", None, "F"),
        ("nachricht_09", "grosshaendler", "Wir hätten gern alles. In zwölf Städten.", None, "b3"),
        ("nachricht_08", "roman", "Das Händler-Büro steht. Ich hab zwölf Stühle gekauft, für zwölf Städte.", None, "F"),
        ("nachricht_19", "mo", "Roman hat zwölf Stühle gekauft. Ich hab auf allen gesessen. Der dritte ist der beste.", None, "F"),
        ("nachricht_10", "jana", "Nachtschicht umgebaut. Läuft.", None, "F"),
        ("nachricht_20", "mo", "Jana hat mir verboten, den Hubwagen zu benutzen. Hubert ist arbeitslos.", None, "F"),
        ("nachricht_11", "roman", "Hochregal. Bis zur Decke. Ich hab die Decke nachgemessen. Sie ist höher, als ich dachte.", None, "b4"),
        ("nachricht_12", "jana", "Regal sicher. Hab geprüft. Mo war dabei. Er hat überlebt.", None, "F"),
        ("nachricht_14", "roman", "Die Laderampe ist unsere. Zwei Transporter, zwei Fahrer, null Ausreden.", None, "b5"),
        ("nachricht_13", "mo", "Eine Frau im Blaumann hat die Rampe vermessen. Sie hat „zu wenig Strom“ gesagt und ist gegangen. Ich nenn sie Strom-Frau.", None, "F"),
        ("nachricht_21", "younes", "Ich hab Janas Nachtschicht geschnitten. Zum zweiten Mal in meinem Leben muss ich nichts ändern. Sag es niemandem.", None, "F"),
        ("nachricht_22", "roman", "Das Lager läuft ohne uns. Das war der Plan. Es fühlt sich trotzdem komisch an.", None, "F"),
        ("nachricht_15", "unbekannt", "Ich heiße Selin. Ich habe eine Halle, viel Strom und eine Idee. Mo hat mir deine Nummer gegeben. Er hätte nicht sollen.", "Mo ...", "ende"),
    ],
    abschluss=dict(
        titel="Läuft ohne uns",
        text="Das Lager ist fertig. Die Pakete gehen auch nachts raus. Jana hat „Ja“ gesagt. Das war alles.\n\nEine Nachricht von einer unbekannten Nummer.",
        antwort="Mo ..."),
    weltwechsel=dict(titel="Die Farm",
                     text="Eine alte Fabrikhalle, Backstein, Sheddach. Selin steht im Stromkasten und sagt nicht Hallo.",
                     figur="mit Selin"),
    offline_von="roman",
    offline_saetze=[
        "Die Nachtschicht hat gepackt. Jana sagt, es war ruhig. Ich hab es trotzdem nachgezählt.",
        "Frank läuft. Frank wird nicht müde. Ich schon.",
        "Ich habe nichts kontrolliert, während du weg warst. Es ging gut. Ich habe dreimal nachgesehen.",
    ],
    danach={
        "bereich_1": "Das Förderband zieht ein. Frank läuft.",
        "bereich_2": "Alle Stationen werden schneller. Vier Paletten, eine Unterschrift.",
        "bereich_3": "Der Großhandel zieht ein. Zwölf Stühle für zwölf Städte.",
        "bereich_4": "Das Regal wächst bis zur Decke.",
        "bereich_5": "Alles wird schneller. Zwei Transporter, null Ausreden.",
    },
)

# ---------------------------------------------------------------- WELT 5
W["produkt"] = dict(
    absender={"plattform": "Dein Kanal", "selin": "Selin", "roman": "Roman", "mo": "Mo",
              "younes": "Younes", "du": "Du"},
    farben={"plattform": "#1B1726", "selin": "#8B5CF6", "roman": "#FF7A1A", "mo": "#3D7BFF",
            "younes": "#FF4FA3", "du": "#8B5CF6"},
    nachrichten=[
        ("nachricht_01", "selin", "Die Halle hat Starkstrom. Das ist der einzige Grund, warum ich sie genommen habe.", None, "fix"),
        ("nachricht_02", "mo", "Das summt hier wie ein Raumschiff, Bruder. Darf ich hier wohnen?", None, "fix"),
        ("nachricht_03", "selin", "Keine Namen von Coins in diesem Chat. Wir reden über Rechenleistung.", None, "fix"),
        ("nachricht_04", "roman", "Ich hab die Stromrechnung gesehen. Ich brauche einen Moment. Zwei.", None, "fix"),
        ("nachricht_05", "selin", "Nein. Auch nicht probeweise. Die Sicherung fliegt schon, wenn Mo Wasser kocht.", None, "b1"),
        ("nachricht_16", "plattform", "Eure Farm-Doku läuft: 10.000 Aufrufe. Younes hat nur das Licht kritisiert.", None, "F"),
        ("nachricht_06", "mo", "Eigener Trafo! Jetzt fliegt die Sicherung nicht mehr, wenn ich Wasser koche. Ich hab's dreimal getestet.", None, "b2"),
        ("nachricht_17", "roman", "Selin sagt, die Halle wird warm. Wärme ist verlorene Rechenleistung. Die Kühlung kostet. Ich brauche noch einen Moment.", None, "F"),
        ("nachricht_07", "selin", "Zwei Rigs sind aus. Nicht laut. Sie haben einfach aufgehört. So machen das die guten.", None, "F"),
        ("nachricht_18", "mo", "Ich hab dem großen Lüfter einen Namen gegeben. Er heißt Wolfgang. Selin hat es überlesen.", None, "F"),
        ("nachricht_09", "selin", "Der Kontrollraum ist frei. Ab jetzt sehen wir, was die Halle wirklich leistet. Nicht, was Mo glaubt.", None, "b3"),
        ("nachricht_08", "mo", "Roman starrt seit Stunden auf eine rote Zelle. Ich hab ihm einen Tee gebracht. Er hat ihn nachgerechnet.", None, "F"),
        ("nachricht_19", "plattform", "Deine Farm-Doku hat zwei Millionen Aufrufe. Younes hat nur das Licht kritisiert.", None, "F"),
        ("nachricht_10", "selin", "Es ist ein Spiel mit Zahlen. Wer es für sicher hält, hat es nicht verstanden.", None, "F"),
        ("nachricht_20", "younes", "Ich hab die Halle gefilmt. Viel Backstein, viel Licht von oben. Selin hat gefragt, ob das Licht Strom verbraucht.", None, "F"),
        ("nachricht_11", "selin", "Solardach. Die Sonne schickt keine Rechnung.", None, "b4"),
        ("nachricht_12", "roman", "Ich hab nachgerechnet. Die Solaranlage war die beste Entscheidung des Jahres. Ich sag das einmal.", None, "F"),
        ("nachricht_14", "selin", "Zweite Halle. Ich hab sie schon verkabelt. Du darfst jetzt unterschreiben.", None, "b5"),
        ("nachricht_13", "mo", "Selin hat gelächelt. Ich glaub. Es war ein Zucken, aber ein gutes.", None, "F"),
        ("nachricht_21", "selin", "Zweite Halle läuft. Die Rigs brauchen uns kaum noch.", None, "F"),
        ("nachricht_22", "roman", "Ich hab die Zahlen gesehen. Dreimal. Ich glaube sie trotzdem nicht.", None, "F"),
        ("nachricht_15", "selin", "Wir haben mehr, als wir brauchen. Jetzt wird's gefährlich.", "Wie gefährlich?", "ende"),
    ],
    abschluss=dict(
        titel="Sie summt",
        text="Die Farm ist fertig. Sie summt. Niemand muss mehr danebenstehen.\n\nEine Nachricht von Selin.",
        antwort="Wie gefährlich?"),
    weltwechsel=dict(titel="Das Portfolio",
                     text="Ganz oben über der Stadt. Glaswände, ein leerer Tresor, eine Liste von Selin.",
                     figur="mit Selin und allen"),
    offline_von="selin",
    offline_saetze=[
        "Du warst weg. Die Halle nicht. Das ist der Unterschied zwischen einer Idee und einer Maschine.",
        "Die Rigs liefen. Zwei sind ausgefallen. Nicht laut.",
        "Mo war hier. Er hat Wolfgang gestreichelt. Wolfgang hat nicht reagiert.",
    ],
    danach={
        "bereich_1": "Die Kühlung zieht ein. Es war schon zu warm.",
        "bereich_2": "Alle Stationen werden schneller. Und die Sicherung bleibt drin.",
        "bereich_3": "Das Staking zieht ein. Ab jetzt sieht man, was die Halle leistet.",
        "bereich_4": "Der Strom wird besser. Die Sonne schickt keine Rechnung.",
        "bereich_5": "Alles wird schneller. Selin hat schon verkabelt.",
    },
)

# ---------------------------------------------------------------- WELT 6
W["kapital"] = dict(
    absender={"plattform": "Dein Kanal", "selin": "Selin", "roman": "Roman", "mo": "Mo",
              "younes": "Younes", "du": "Du"},
    farben={"plattform": "#1B1726", "selin": "#8B5CF6", "roman": "#FF7A1A", "mo": "#3D7BFF",
            "younes": "#FF4FA3", "du": "#F2B200"},
    nachrichten=[
        ("nachricht_01", "selin", "Gefährlich heißt: Es geht auch runter. Die Liste: Aktien, Anleihen, Immobilien, Dinge, die glänzen.", None, "fix"),
        ("nachricht_02", "mo", "Ich hab gefragt, was Anleihen sind. Selin hat „Zeit“ gesagt. Mehr nicht.", None, "fix"),
        ("nachricht_03", "roman", "Eine Mappe voller Anleihen, schon abgeheftet. Jana hat „Ja“ geschrieben. Ich weiß nicht, was das heißt.", None, "fix"),
        ("nachricht_04", "selin", "Ein roter Tag. In diesem Spiel gibt es die. Die Kurve hat sich bisher immer wieder gefangen.", None, "fix"),
        ("nachricht_05", "younes", "Ich film die Galerie. Endlich Licht, das jemand anderes bezahlt hat.", None, "b1"),
        ("nachricht_16", "roman", "Die Galerie hat vierzehn Bilder. Ich hab sie nach Größe sortiert, Younes nach Licht. Wir reden nicht mehr.", None, "F"),
        ("nachricht_06", "mo", "Bruder, wir haben einen Tresor. Einen echten. Mit Tür!", None, "b2"),
        ("nachricht_17", "selin", "Mit mehr Streuung schwankt unsere Zahl weniger. Schneller wird sie davon nicht.", None, "F"),
        ("nachricht_07", "plattform", "Heute kein roter Tag. Roman hat trotzdem nachgesehen. Dreimal.", None, "F"),
        ("nachricht_18", "younes", "Ich will die Galerie in Ruhe filmen. Mo steht im Bild. Er steht immer im Bild.", None, "F"),
        ("nachricht_09", "selin", "Der Boardroom ist unser. Im Spiel kommen die Dividenden jetzt von allein.", None, "b3"),
        ("nachricht_08", "roman", "Ich hab eine Liste mit Häusern. Sie ist länger als die Liste der Shops.", None, "F"),
        ("nachricht_19", "mo", "Ich hab eine Uhr anprobiert. Ich hab sie sofort zurückgelegt. Sie war schwerer als mein erster Laptop.", None, "F"),
        ("nachricht_10", "younes", "Ich hab einmal „gut so“ gesagt. Es hängt jetzt in eurer Galerie. In Neon. Mo hat's gemacht.", None, "F"),
        ("nachricht_20", "mo", "Roman hat Fähnchen bestellt. Ich weiß nicht wofür. Er sagt: Überraschung. Roman. Überraschung.", None, "F"),
        ("nachricht_11", "roman", "Das Stadtmodell zeigt alle Häuser, die uns gehören. Ich hab Fähnchen gekauft.", None, "b4"),
        ("nachricht_12", "selin", "Streuung heißt: nicht alles auf ein Haus. Das gilt auch für Fähnchen, Roman.", None, "F"),
        ("nachricht_14", "roman", "Kunstsalon. Der Oldtimer ist da. Ich hab den Kilometerstand fotografiert: 41.208. Zur Sicherheit.", None, "b5"),
        ("nachricht_13", "younes", "Ich hab den Oldtimer gefilmt. Mo nennt ihn Bernd. Ich hasse, dass es passt.", None, "F"),
        ("nachricht_21", "mo", "Dachterrasse morgen. Alle kommen. Bring nichts mit, wir haben alles.", None, "F"),
        ("nachricht_22", "selin", "Ich hab nie gesagt, dass ich euch mag. Ich sag es einmal. Danach reden wir wieder über Kurven.", None, "F"),
        ("nachricht_15", "plattform", "Neue Anfrage von jemandem, der gerade anfängt. Sein erster Clip hat drei Aufrufe.", "Ich schreib ihm.", "ende"),
    ],
    abschluss=dict(
        titel="Alle sind da",
        text="Das Portfolio ist komplett. Auf der Dachterrasse sitzen Mo, Younes, Roman und Selin. Jana ist auch gekommen. Sie hat „Ja“ gesagt.\n\nEine Nachricht von deinem Kanal.",
        antwort="Ich schreib ihm."),
    weltwechsel=None,
    offline_von="selin",
    offline_saetze=[
        "Während du weg warst, hat sich die Zahl bewegt. Rauf und runter. Im Schnitt: rauf.",
        "Nichts zu tun. Das ist der Punkt.",
        "Ich habe die Kurve beobachtet. Mo hat sie beschimpft. Sie hat nicht reagiert.",
    ],
    danach={
        "bereich_1": "Die Streuung zieht ein. Die roten Tage werden leiser.",
        "bereich_2": "Alle Stationen werden schneller. Ein echter Tresor, mit Tür.",
        "bereich_3": "Die Dividenden ziehen ein. Sie kommen von allein, im Spiel.",
        "bereich_4": "Die Analyse wird besser. Roman hat Fähnchen.",
        "bereich_5": "Alles wird schneller. Und ein roter Oldtimer namens Bernd.",
    },
)


if __name__ == "__main__":
    import sys
    if "--erzwingen" not in sys.argv:
        sys.exit("""ABBRUCH: Die theme.json und balance/*.json wurden nach dem Generieren von Hand poliert (Nacht 15.10.2026).
Dieses Skript wuerde sie ueberschreiben. Nur mit --erzwingen fortfahren (vorher sichern!).""")
