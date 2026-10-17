# Story-Generator (Pakete C+D)

`story.py` ist die Quelle aller Story-Texte (Nachrichten, Eroeffnungs-Chat, Offline-Saetze,
Raumtexte). Daraus entstehen `project/data/themes/<welt>/theme.json`, die Nachrichten in
`project/data/balance/<welt>.json` und die Lesung `docs/nacht/rp_story_lesung.md`.

Alle Pfade sind relativ zu diesem Ordner (`tools/story/` -> Repo-Wurzel).

- `story.py` -- Texte je Welt (`W`). Hier aendern, nicht in den JSON-Dateien.
- `build.py <probe.txt>` -- schreibt theme/balance. Braucht die Ausgabe der Probe
  (`project/tools/` Tiefenlauf je Welt, Zeiten der Raumkaeufe) fuer die Fortschrittsschwellen.
  Handgesetzte Schwellen in `fover.json`. Optional: `backup/bal_<welt>.json` = Stand vor dem ersten Lauf
  (alte Ausloeser); fehlt es, gelten die aktuellen.
- `lesung.py` -- schreibt die Lesung (liest `trig_<welt>.json`, die `build.py` erzeugt, und `sim_<welt>.txt`).
- `ids.py` -- schreibt `docs/nacht/ids_welten.md`.

Start (Repo-Wurzel): `python tools/story/build.py <probe.txt>`, danach `.\validate.ps1`
(Sperrwoerter D3, Balance, Tests). Die Zwischendateien `trig_*.json`/`sim_*.txt` sind Ausgaben und nicht eingecheckt.
