# ASSET PIPELINE

**Stand:** 2026-09-10 · Blender 5.2.1 LTS · **erste Figur produziert und im Spiel**

---

## 1. Die Kennzahl, auf die es ankommt

Risiko R-02 lautet: *Die Asset-Produktion wird zum Flaschenhals.* Der einzige
belastbare Test dagegen ist eine Messung — nicht eine Absichtserklärung.

| Schritt | Gemessen |
|---|---|
| Blender-Skript ausführen bis fertiges `.glb` | **19,7 s** |
| Deploy inklusive Build aufs Gerät | ~35 s |
| **Gesamt: Änderung am Modell → auf dem Handy sichtbar** | **unter 1 Minute** |
| Dateigröße | 11 KB |
| Dreiecke | ~84 (Budget: 900) |
| APK-Zuwachs durch das Modell | **0,0 MB** (unter Messgrenze) |

**Eine neue Variante kostet Sekunden, kein Modellieren.** Damit ist die
Grundannahme aus ADR-003 und ADR-019 belegt statt behauptet.

---

## 2. Warum prozedural statt von Hand

Das Ziel sind 20+ NPC-Typen. Von Hand modelliert wäre das die Stelle, an der
ein Ein-Personen-Projekt stirbt. Ein Skript erzeugt die Basisfigur
reproduzierbar; Varianten entstehen danach **allein über Materialfarben**,
ohne dass Geometrie angefasst wird.

```
art_source/scripts/build_npc.py   →   project/assets/characters/npc_basis.glb
        (Blender, headless)                   (glTF, 11 KB)
```

Aufruf:
```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2lender.exe" `
    --background --python art_source\scriptsuild_npc.py `
    -- --out projectssets\characters
pc_basis.glb
```

---

## 3. Aufbau der Figur (ADR-019: getrennte Module)

```
rumpf · kopf · arm_links · arm_rechts · bein_links · bein_rechts · tasche
```

**Kein verschmolzenes Mesh.** Jedes Teil ist einzeln benannt und austauschbar.
Das zahlt sich zweifach aus:

1. **Varianten:** `npc_view.gd` färbt gezielt die Kleidungsteile und lässt Kopf
   und Tasche unberührt — möglich nur, weil die Teile getrennt und benannt sind.
2. **Detailstufen:** Eine spätere, feinere Version ersetzt ein einzelnes Modul,
   ohne die Figur neu zu bauen.

**Drei Material-Slots**, nicht mehr (ART_DIRECTION R2): `kleidung` · `haut` ·
`akzent`. Die Farben stehen nicht im Mesh, sondern im Slot.

---

## 4. Regeln

- **Rastermaß:** 1 Blender-Einheit = 1 Meter = 1 Godot-Einheit. Objekte rasten auf 0,5.
- **Export:** glTF Binary (`.glb`), `export_yup=True` — Godot erwartet Y nach oben.
- **Kein Glanz:** `roughness = 1.0`, `metallic = 0.0`. Reine Farbflächen.
- **`.blend`-Quelldateien** gehören nach `art_source/`, **außerhalb** von `project/`.
  Sonst importiert Godot sie und bläht Importzeit und Paket auf.
- **Budget je Objekt:** NPC < 900 Dreiecke · Requisite < 400 · Stationsmodul < 2.000

---

## 5. Was der erste Durchlauf gezeigt hat

**Die Figur macht mehr aus als erwartet.** Der Wechsel von Platzhalter-Kapseln
zu Figuren mit Kopf, Kleidung und Aktentasche verändert die Szene stärker als
jede andere Einzeländerung bisher. Aus abstrakten Punkten werden Leute, die
etwas zu erledigen haben.

**Ein Detail trägt das meiste:** die Aktentasche im Akzentton. Sie ist ein
einziger Quader und macht aus einer Silhouette jemanden mit einem Anliegen.
Solche erzählenden Kleinigkeiten sind billiger als jede Detailverfeinerung.

**Nachjustiert werden musste** nur der Schlangenabstand — die Figuren brauchen
mehr Platz als die vorherigen Kapseln.

---

## 6. Stationsmodule

Neun Dateien: drei Stationen × drei Ausbaustufen, erzeugt in **9,9 Sekunden**.

| Modul | Teile | Dreiecke | Größe |
|---|---|---|---|
| `station_intake_1..3` | 6 / 18 / 21 | 72 / 216 / 260 | bis 33 KB |
| `station_buffer_1..3` | 3 / 8 / 20 | 36 / 96 / 240 | bis 31 KB |
| `station_processing_1..3` | 3 / 5 / 14 | 36 / 60 / 200 | bis 26 KB |

**Die Stufen bauen aufeinander auf.** Stufe 2 zeigt alles von Stufe 1 plus das
neue Teil. Der Spieler sieht dadurch nicht „etwas anderes", sondern „mehr als
vorher" — Fortschritt statt Austausch (ART_DIRECTION R4).

Der Ausbau erzählt die Geschichte mit:
`Klemmbrett auf den Knien → Klapptisch → eingerichteter Platz mit Lampe,
Ablagekorb und Thermoskanne`. Die Lampe macht den Platz *bewohnt* — sie ist
drei Quader und leistet mehr als jede Detailverfeinerung.

---

## 7. Gehzyklus ohne Skelett

Die Figuren wippen beim Laufen leicht auf und ab, neigen sich minimal nach vorn
und drehen sich in Laufrichtung. **Zwei Zeilen Mathematik statt eines Rigs mit
Keyframes** — der Unterschied zwischen „gleitet" und „geht" ist trotzdem sofort
sichtbar.

Bei 24 gleichzeitigen Figuren wäre ein echter Skelett-Zyklus auf der
Zielhardware spürbar teurer gewesen und hätte denselben Zweck erfüllt.

---

## 8. Gemessene Leistung auf dem Zielgerät

Redmi Note 12 Pro 5G, 14 sichtbare Figuren, alle drei Stationen bebildert:

| Größe | Gemessen | Budget | |
|---|---|---|---|
| Frame-Zeit, 50. Perzentil | **11 ms** (≈90 fps) | 16,7 ms | ✅ |
| Frame-Zeit, 90. Perzentil | **16 ms** (≈62 fps) | 16,7 ms | ✅ |
| Frame-Zeit, 95. Perzentil | 20 ms (≈50 fps) | — | knapp |
| Janky Frames | 4 % | — | ✅ |
| RAM (PSS) | **232 MB** | 350 MB | ✅ |
| APK | 27,1 MB | 60 MB | ✅ |

`[Kurze Messung über 25 Frames — vor Phase 9 mit einer längeren Sitzung wiederholen.]`

---

## 9. Nächste Schritte

1. Weltrequisiten: Tresen, Neonröhre, der vertrocknete Gummibaum aus `STORY.md`
2. Assets für Welt 2 (Die Bude) — derselbe Satz IDs, andere Gegenstände
3. Zahlen-Popups und Partikel beim Ausbau
