# ART DIRECTION

**Stand:** 2026-09-10 · Status: Rahmen gesetzt, Feinausarbeitung in TASK 018

---

## 1. Stil

**Stylized Low-Poly 3D**, dargestellt über eine orthographische Kamera in fester Isometrie-Neigung (ADR-003).

Die Leitidee: **charmant heruntergekommen**. Das Amt startet vergilbt, fleckig und improvisiert — Resopal-Tresen, flackernde Neonröhre, durchgesessene Stühle, ein trauriger Gummibaum — und wird sichtbar hell, sauber und geordnet. Der Stil muss beide Enden dieser Skala tragen, ohne zu wechseln.

**Visueller Anker:** westdeutsche Amtsstube der Achtzigerjahre, die nie renoviert wurde. Beige, Braun, Resopal, Linoleum, Leuchtstoffröhre. Diese Farbwelt ist sofort wiedererkennbar und hebt sich klar von der bunten Bonbon-Optik ab, die das Genre dominiert — ein echter Vorteil im Store-Screenshot.

**Was der Stil nicht ist:** kein Hochglanz-Realismus, keine generische Mobile-Bonbon-Optik mit Farbverläufen und Glanzlichtern auf jeder Fläche, keine „AI-Art"-Anmutung mit beliebigem Detailrauschen.

---

## 2. Die vier Regeln, die den Stil zusammenhalten

### R1 — Silhouette vor Detail
Jedes Objekt muss als schwarze Fläche auf weißem Grund erkennbar bleiben. Auf einem 6"-Display bei Sonnenlicht ist die Silhouette das Einzige, was zuverlässig ankommt.
**Prüfung:** Screenshot in reines Schwarzweiß umwandeln — ist alles noch identifizierbar?

### R2 — Drei Materialtöne pro Objekt
Jedes Objekt verwendet höchstens drei Farbflächen. Keine Texturen mit Details, keine Verläufe. Das hält Draw Calls niedrig, macht Farbvarianten trivial und erzwingt klare Formen.

### R3 — Farbe trägt Bedeutung, nicht Dekoration
Sättigung ist reserviert für Dinge, die der Spieler antippen oder verstehen soll. Die Umgebung bleibt entsättigt. Deshalb sticht ein wartender Kunde sofort heraus, ohne dass ein Pfeil nötig wäre.

### R4 — Fortschritt ist sichtbar, nicht numerisch
Jede Ausbaustufe verändert **Form oder Zustand**, nicht nur eine Zahl: Der Riss verschwindet, das Regal füllt sich, das Neonlicht flackert nicht mehr. Drei klar unterscheidbare Stufen pro Station sind Pflicht.

---

## 3. Farbpalette (Startwerte, in TASK 018 zu verfeinern)

| Rolle | Hex | Verwendung |
|---|---|---|
| Grund dunkel | `#2A2F3A` | Straße, Schatten, Rahmen |
| Grund mittel | `#454C5C` | Wände, Basisflächen |
| Grund hell | `#8E97A8` | Böden, helle Flächen |
| Amtsbeige | `#C9B79A` | Resopal, Aktendeckel, Pappordner — die Signaturfarbe |
| **Aktion** | `#F2A93B` | Antippbares, Upgrade-Schaltflächen |
| **Erfolg** | `#5BBF7A` | Geld, positive Rückmeldung |
| **Warnung** | `#E0603D` | Engpass, ungeduldiger Kunde |
| Akzent kühl | `#4A9DD6` | UI-Hervorhebung, Auswahlrahmen |
| Papier | `#F5F1E8` | UI-Flächen, Text auf dunklem Grund |

**Kontrastregel:** Text auf Fläche mindestens 4.5:1. Jede UI-Farbkombination wird beim Festlegen gemessen, nicht geschätzt.

---

## 4. Typografie

Zwei Familien, beide mit klarer freier Lizenz (Auswahl in TASK 018, Lizenz wird in `ASSET_LICENSES.md` dokumentiert):

| Rolle | Anforderung |
|---|---|
| Zahlen und HUD | Tabellarische Ziffern (Beträge dürfen beim Zählen nicht springen), hohe x-Höhe, gut lesbar ab 14 sp |
| Überschriften | Etwas Charakter, aber keine Deko-Schrift; muss deutsche Umlaute und Eszett vollständig enthalten |

**Mindestgrößen:** Fließtext 14 sp, sekundär 12 sp, niemals darunter. Beträge nie kleiner als 16 sp — sie sind das, worauf der Blick zuerst fällt.

---

## 5. UI-Raster

- Grundmaß **8 dp**, alle Abstände sind Vielfache davon
- Touch-Ziele mindestens **48 × 48 dp**, zwischen zwei Zielen mindestens 8 dp Abstand
- Sichere Zone: Bedienelemente im unteren Drittel (Daumenreichweite), Informationen oben
- Ecken einheitlich 12 dp gerundet
- Genau **eine** Schattenstufe für schwebende Elemente — keine gestapelten Tiefenebenen

---

## 6. Animationsprinzipien

| Element | Dauer | Kurve |
|---|---|---|
| Antipp-Rückmeldung | 80 ms | Sofort ein, weich aus |
| Zahlen-Popup („+25") | 600 ms | Aufsteigend, ausblendend |
| Upgrade-Bestätigung | 350 ms | Leichtes Überschwingen — das ist der befriedigende Moment |
| Menüwechsel | 200 ms | Weich ein und aus |
| NPC-Gehzyklus | — | Bewusst leicht überzeichnet, mit spürbarem Gewicht |

**Grundsatz:** Jede Spieleraktion braucht eine Rückmeldung innerhalb von 100 ms. Ohne sie fühlt sich das Spiel kaputt an, selbst wenn es korrekt rechnet.

---

## 7. Asset-Pipeline

```
Blender (.blend)  ──►  glTF (.glb)  ──►  project/assets/  ──►  Szene
   art_source/            Export           Godot-Import        Platzierung
```

**Regeln:**
- `.blend`-Dateien liegen in `art_source/` **außerhalb** des Godot-Projekts — sonst würde Godot sie importieren und Paketgröße wie Importzeit aufblähen
- Einheitliches Rastermaß: 1 Godot-Einheit = 1 Meter, Objekte rasten auf 0,5 Einheiten
- Ein Basis-Rig für alle humanoiden Figuren, Animationen werden geteilt
- Varianten entstehen über Material-Slots und austauschbare Kleidungs-Meshes, nicht über neue Modelle
- Blender-Python-Skripte in `art_source/scripts/` erzeugen und exportieren Varianten reproduzierbar

**Budget je Objekt:**

| Typ | Dreiecke | Materialien |
|---|---|---|
| NPC | < 900 | 2–3 |
| Möbel / Requisite | < 400 | 1–2 |
| Stationsmodul | < 2.000 | 2–3 |
| Gebäudehülle | < 3.500 | 3 |

---

## 7.1 Was die erste Figurenserie gezeigt hat

**Silhouette schlägt Farbe — deutlicher als erwartet.** Bei 40 Pixel Figurhöhe
ist der Umriss das Einzige, was ankommt. Der gebeugte Rentner mit Hut, die
Eilige im Schritt, der Erstantragsteller mit Kapuze und ohne Unterlagen sind
auf einen Blick unterscheidbar. Verschiedene Jackenfarben allein wären es nicht.

**Genau ein Merkmal je Archetyp.** Zwei Merkmale verwaschen die Silhouette,
statt sie zu schärfen. Der Rentner hat die Beugung *und* den Hut *und* den
Karton — das funktioniert nur, weil alle drei dieselbe Aussage machen.

**Erzählende Details sind billiger als Detailverfeinerung.** Die Aktentasche
ist ein einziger Quader und macht aus einer Silhouette jemanden mit einem
Anliegen. Ein glatteres Mesh hätte dieselbe Arbeit gekostet und nichts erzählt.

**Weglassen ist auch ein Merkmal.** Der Erstantragsteller trägt als Einziger
nichts bei sich — er weiß ja nicht einmal, was er bräuchte. Das liest sich
sofort und kostet null Geometrie.

**Gemessen:** 7 Archetypen, 6,4 Sekunden Erzeugung, 96 KB zusammen,
72–108 Dreiecke je Figur bei einem Budget von 900.

---

## 8. Platzhalter-Phase

Bis Phase 5 wird ausschließlich mit **einfarbiger Grundgeometrie** gearbeitet — Quader, Zylinder, Kapseln in den Paletten-Farben.

**Das ist kein Provisorium, sondern Methode:** Wenn das Spiel mit Kisten Spaß macht, macht es mit Grafik mehr Spaß. Macht es mit Kisten keinen Spaß, rettet die Grafik es nicht — und man hat es herausgefunden, bevor Wochen an Assets verloren waren.

---

## 9. Die Karte: ein Raum, kein Podest

Bis hierher schwebte eine Platte im Nichts. Ein Idle-Tycoon braucht aber einen
**Ort**, in dem man sich befindet. Welt 1 ist deshalb ein Raum aus zehn
Modulen: Fliesen in drei Tönen, Wandsegmente, Ecke, Tür, Fensterband, Automat,
Uhr, Mülleimer.

**Modulbaukasten statt fertigem Raum.** `RoomBuilder` setzt den Grundriss zur
Laufzeit aus Einzelteilen zusammen. Welt 2 ist damit eine andere Anordnung
derselben Teile statt neuer Modellierung — dieselbe Rechnung, die schon bei den
Stationen aufgegangen ist.

**Wände nur auf den beiden abgewandten Seiten.** Bei isometrischer Aufsicht
würden die vorderen Wände dem Betrachter die Sicht nehmen. Der offene Raum nach
vorn ist keine Nachlässigkeit, sondern die übliche Lösung des Genres.

**Laufwege statt gleichmäßigem Boden.** Heller getretene Fliesen auf den Achsen,
die täglich benutzt werden. Sie erzählen, dass dieser Raum seit Jahren in
Betrieb ist, und führen zugleich das Auge zur Kette.

**Drei Fliesen über MultiMesh, nicht 143 Nodes.** Einzelne Nodes wären allein
für den Boden mehr Draw Calls gewesen als das Budget für die gesamte Szene
hergibt. Als `MultiMeshInstance3D` sind es drei.

### Zwei Fallen, die Zeit gekostet haben

**Farbraum.** glTF speichert `baseColorFactor` **linear**, Godot zeigt
`albedo_color` in **sRGB**. Ein Wert von 0,10 im Blender-Skript erscheint im
Spiel als 0,35 Helligkeit. Drei Runden „der Boden wird einfach nicht dunkler"
hatten genau diese Ursache. Wer die gewünschte Bildschirmhelligkeit *s* kennt,
rechnet `linear = s^2,2`.

**Raumgröße im Hochformat.** Bei 45 Grad Kameradrehung hängen **beide**
Bildschirmausdehnungen an der *Summe* aus Breite und Tiefe — ein breiterer und
ein tieferer Raum kosten gleich viel Bildbreite. Ein gedrehtes Rechteck hat
immer eine quadratische Hüllfläche, unabhängig vom Seitenverhältnis. Im
Hochformat ist Bildbreite das knappe Gut, deshalb ist der Raum kompakt
(13 × 11) statt weitläufig. Dass die äußersten Ecken angeschnitten bleiben, ist
Absicht: Die Karte reicht über den Rand hinaus und lässt sich schwenken.

**Gemessen auf dem Redmi Note 12 Pro 5G:** 60,5 FPS im Median, p95 identisch —
mit vollem Raum, fünf Stationen, Warteschlange und Kulisse kein einziger
verlorener Frame. 10 Raummodule, ~420 Dreiecke zusammen.

---

## 10. Klang

Sieben Klänge, zusammen 101 KB, **synthetisch erzeugt** in
`art_source/scripts/build_sounds.py` — reine Standardbibliothek, kein
Fremdmaterial.

**Warum Synthese statt Sample-Bibliothek:** Ein Play-Store-Eintrag braucht eine
saubere Herkunft für jedes Byte. „Irgendwo heruntergeladen, klang gut" ist
genau die Altlast, die später niemand mehr auflöst. Das Skript *ist* die
Lizenz. Nebenbei: Ein Klang ist dort drei Zahlen, kein Audioeditor.

**Alles auf einer Tonleiter.** Ausbau, Meilenstein und Freischaltung liegen auf
demselben Grundton. In einem Idle-Game überlagert sich ständig etwas — mit
zufälligen Frequenzen wäre jede Überlagerung ein Missklang.

**Die Tonhöhe erzählt die Fortschrittskurve.** Der Ausbau-Klang steigt mit
jeder Stufe und setzt alle zwölf Stufen zurück — genau dort, wo der
Meilenstein-Multiplikator greift. Der Spieler hört, wo er im Block steht, ohne
hinzusehen, und der Neuansatz fühlt sich an wie Luftholen. Ohne den Umbruch
wäre Stufe 80 ein unhörbares Fiepen.

**Was bewusst KEINEN Klang hat:** `money_changed` und `throughput_tick`. Beide
feuern viermal pro Sekunde, dauerhaft, ohne Zutun des Spielers. Ein Klang
darauf wäre nach zwei Minuten der Grund, warum jemand den Ton abschaltet — und
danach hört er auch die Klänge nicht mehr, die etwas bedeuten.

**Der leiseste Klang ist der häufigste.** `sfx_tipp` ist 50 ms lang und der
leiseste von allen. Was man nach der zwanzigsten Wiederholung noch erträgt,
darf beim ersten Mal nicht beeindrucken wollen.

Die Zuordnung Ereignis → Klang steht in `data/audio/sounds.json`, nicht im
Code. `AudioRegeln` entscheidet (headless testbar, 10 Tests), `AudioDirector`
spielt ab.
