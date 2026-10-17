# -*- coding: utf-8 -*-
import json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import story
W = story.W
ROOT = os.path.dirname(os.path.dirname(SP))
ORDER = ['zimmer', 'auftrag', 'webseiten', 'buero', 'produkt', 'kapital']
TITEL = {'zimmer': 'Die WG (mit Mo)', 'auftrag': 'Das Studio (mit Younes)', 'webseiten': 'Der Merch-Laden (mit Roman)',
         'buero': 'Das Lager (mit Roman und Jana)', 'produkt': 'Die Farm (mit Selin)', 'kapital': 'Das Portfolio (mit allen)'}

def zahl(v):
    v = float(v)
    for g, s in ((1e12, ' Bio'), (1e9, ' Mrd'), (1e6, ' Mio'), (1e3, ' Tsd')):
        if v >= g:
            x = v / g
            return (('%g' % x).replace('.', ',')) + s
    return '%g' % v

def beschreibe(a, theme):
    t = a.get('typ')
    st = theme['stationen']
    def sname(s): return st.get(s, {}).get('name', s)
    if t == 'start': return 'sofort beim Start'
    if t == 'bereich': return 'Raum „%s“ gekauft' % theme['bereiche'][a['bereich']]['name']
    if t == 'fortschritt': return 'Welt zu %d %% fertig' % round(a['wert'] * 100)
    if t == 'verdient': return '%s € in dieser Welt verdient' % zahl(a['wert'])
    if t == 'abschluss': return 'Welt zu 100 % fertig (Abschluss)'
    if t == 'freigeschaltet': return 'Umbau gekauft'
    if t == 'station_stufe': return '%s auf Stufe %d' % (sname(a['station']), a['wert'])
    if t == 'ausstattung_stufe':
        pl = theme['ausstattung'].get(a['station'], {}).get(a['platz'], {})
        pn = pl.get('name', a['platz']) if isinstance(pl, dict) else a['platz']
        return '%s: %s gekauft' % (sname(a['station']), pn)
    if t == 'stufen_gesamt': return '%d Stufen insgesamt' % a['wert']
    if t == 'ausstattung_gesamt': return '%d Ausstattungsstufen insgesamt' % a['wert']
    if t == 'sterne': return '%d Sterne' % a['wert']
    return json.dumps(a, ensure_ascii=False)

def zeiten(path):
    if not os.path.exists(path): return {}
    txt = re.sub(r'\x1b\[[0-9;]*m', '', open(path, encoding='utf-8', errors='replace').read())
    out = {}
    for m in re.finditer(r'\bn(\d\d) (\d+:\d\d)', txt):
        out['nachricht_' + m.group(1)] = m.group(2)
    return out

def main():
    L = []
    L.append('# Story-Lesung — HELLO WORLD (Paket D, 2026-10-14)\n')
    L.append('Alle 132 Nachrichten zum Durchlesen, in der Reihenfolge, in der sie im Spiel eintreffen. '
             '„Zeit“ ist der Zeitpunkt im Balance-Simulator (optimal spielender Spieler, Minuten:Sekunden). '
             'Echte Spieler brauchen etwas länger. Texte stehen in `data/themes/<welt>/theme.json`, Auslöser in `data/balance/<welt>.json`.\n')
    L.append('**Regeln:** höchstens zwei kurze Sätze · Chat-Ton · jede Nachricht endet mit einem Haken (Frage, Behauptung, Zahl) · '
             'Running Gags je Figur mindestens zweimal pro Welt · letzte Nachricht jeder Welt = Cliffhanger der nächsten Figur · '
             'keine Belehrung, keine echten Namen, keine Handlungsanweisungen zu Geld.\n')
    L.append('**Figuren:** Mo (Bruder, isst überall mit, benennt Dinge) · Younes (Takes, sagt genau einmal „gut so“) · '
             'Roman (zählt alles, Tabelle mit Reitern, lernt abzugeben) · Selin (nüchtern bis zum vorletzten Satz) · '
             'Jana (Welt 4, antwortet in einem Satz) · Mira (trocken, „Danke?“) · Tobi (kocht, zieht aus) · Dein Kanal (nur Zahlen).\n')
    for w in ORDER:
        spec = W[w]
        theme = json.load(open(os.path.join(ROOT, 'project', 'data', 'themes', w, 'theme.json'), encoding='utf-8'))
        trig = dict((k, v) for k, v in json.load(open(os.path.join(SP, f'trig_{w}.json'), encoding='utf-8'))['trig'])
        zt = zeiten(os.path.join(SP, f'sim_{w}.txt'))
        L.append(f'\n---\n\n## Welt {ORDER.index(w) + 1} — {TITEL[w]}\n')
        if w == 'zimmer':
            L.append('### Eröffnung (Chat in den ersten 60 Sekunden, Tipp = nächste Blase)\n')
            for a, b in spec['eroeffnung_chat']:
                L.append(f'- **{spec["absender"][a]}:** {b}')
            L.append('- Knopf: **Anfangen**\n')
        L.append('### Nachrichten\n')
        L.append('| # | ID | kommt bei | Zeit | Von | Text | Antwort |')
        L.append('|---|---|---|---|---|---|---|')
        for i, m in enumerate(spec['nachrichten'], 1):
            mid, von, text, ant, slot = m
            L.append('| %d | `%s` | %s | %s | %s | %s | %s |' % (
                i, mid, beschreibe(trig[mid], theme), zt.get(mid, ''), spec['absender'][von], text.replace('|', '/'), ant or ''))
        L.append('\n### Abschluss-Bildschirm\n')
        L.append(f'**{spec["abschluss"]["titel"]}** — ' + spec['abschluss']['text'].replace('\n\n', ' ') + f' · Antwort: „{spec["abschluss"]["antwort"]}“\n')
        if spec.get('weltwechsel'):
            ww = spec['weltwechsel']
            L.append(f'### Weltwechsel\n\n**{ww["titel"]}** — {ww["text"]} · Figur: {ww["figur"]}\n')
        L.append(f'### Offline-Sätze ({spec["absender"][spec["offline_von"]]})\n')
        for s in spec['offline_saetze']:
            L.append(f'- {s}')
        L.append('\n### Raumtexte „Danach hier“\n')
        for bid, d in spec['danach'].items():
            L.append(f'- **{theme["bereiche"][bid]["name"]}:** {d}')
    open(os.path.join(ROOT, 'docs', 'nacht', 'rp_story_lesung.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    print('Lesung geschrieben')

main()
