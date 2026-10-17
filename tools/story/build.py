# -*- coding: utf-8 -*-
import json, re, sys, os, copy
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import importlib, story
importlib.reload(story)
W = story.W
ROOT = os.path.join(os.path.dirname(os.path.dirname(SP)), 'project')
ORDER = ['zimmer', 'auftrag', 'webseiten', 'buero', 'produkt', 'kapital']

def zeit(s):
    m, sec = s.strip().split(':')
    return int(m) * 60 + int(sec)

def parse_probe(path):
    txt = re.sub(r'\x1b\[[0-9;]*m', '', open(path, encoding='utf-8', errors='replace').read())
    res, cur = {}, None
    for line in txt.splitlines():
        if line.startswith('=== '):
            cur = line[4:].strip(); res[cur] = dict(f={}, area={}, areaf={}, v={}, end=None)
        elif cur and line.startswith('abschluss '):
            res[cur]['end'] = zeit(line.split()[1])
        elif cur and '|' in line:
            for part in line.split('|'):
                part = part.strip()
                if not part: continue
                k, v = part.rsplit(' ', 1)
                if k.startswith('AREAF_'):
                    res[cur]['areaf'][k[6:]] = float(v)
                elif k.startswith('AREA_'):
                    res[cur]['area'][k[5:]] = zeit(v)
                elif re.fullmatch(r'v\d\d_\d\d', k):
                    e, mant = k[1:].split('_')
                    res[cur]['v'][int(mant) * 10 ** (int(e) - 1)] = zeit(v)
                elif re.fullmatch(r'f\d\d', k):
                    res[cur]['f'][int(k[1:])] = zeit(v)
    return res

def load(p):
    return json.load(open(p, encoding='utf-8'))

def dump(p, d):
    open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(d, ensure_ascii=False, indent='\t') + '\n')

# Handgesetzte Ausloeser (ueberschreiben alte), nach Welt
OVERRIDE = {}
# Handgesetzte Fortschrittsschwellen (Prozent) fuer F-Slots: {welt: {id: prozent}}
FOVER = {}
try:
    FOVER = json.load(open(os.path.join(SP, 'fover.json')))
except Exception:
    pass

def build(probe_path):
    probe = parse_probe(probe_path)
    report = {}
    for w in ORDER:
        spec = W[w]
        bal_p = os.path.join(ROOT, 'data', 'balance', w + '.json')
        bal = load(bal_p)
        bak = os.path.join(SP, 'backup', 'bal_%s.json' % w)  # optional: Sicherung vor dem ersten Lauf
        alt = {n['id']: n['ausloeser'] for n in load(bak if os.path.exists(bak) else bal_p)['nachrichten']}
        P = probe[w]
        msgs = spec['nachrichten']
        # Anker-Zeiten
        anchors = {}
        for i, m in enumerate(msgs):
            if m[4] in ('b1', 'b2', 'b3', 'b4', 'b5'):
                anchors[i] = P['area']['bereich_' + m[4][1]]
            elif m[4] == 'ende':
                anchors[i] = P['end']
        trig = {}
        warn = []
        # fixe + Raum + Ende
        for i, m in enumerate(msgs):
            mid, slot = m[0], m[4]
            if slot == 'fix':
                t = OVERRIDE.get(w, {}).get(mid) or alt[mid]
                if mid == 'nachricht_02':
                    t = {"typ": "ausstattung_gesamt", "wert": 1}
                if mid == 'nachricht_03' and w != 'buero':
                    t = {"typ": "stufen_gesamt", "wert": 8}
                trig[i] = t
            elif slot.startswith('b'):
                trig[i] = {"typ": "bereich", "bereich": "bereich_" + slot[1]}
            elif slot == 'ende':
                trig[i] = {"typ": "abschluss"}
        # Fueller je Segment
        idx_anchor = sorted(anchors)
        fidx = [i for i, m in enumerate(msgs) if m[4] == 'F']
        prev_th = 0
        for i in fidx:
            pass
        # Segmente: zwischen Ankern
        seg_start = None
        for a, b in zip([None] + idx_anchor, idx_anchor + [None]):
            lo = (a + 1) if a is not None else 0
            hi = b if b is not None else len(msgs)
            fs = [i for i in range(lo, hi) if msgs[i][4] == 'F']
            if not fs:
                continue
            tA = anchors[a] if a is not None else 0
            tB = anchors[b] if b is not None else P['end']
            k = len(fs)
            prev_t = tA
            for j, i in enumerate(fs):
                mid = msgs[i][0]
                target = tA + (tB - tA) * (j + 1) / (k + 1)
                if mid in FOVER.get(w, {}):
                    kind, val = FOVER[w][mid]
                else:
                    cands = []
                    for th, t in P['f'].items():
                        if max(tA, prev_t) + 20 < t < tB - 20 and th > prev_th:
                            cands.append((abs(t - target), 0, 'f', th, t))
                    for val_, t in P['v'].items():
                        if max(tA, prev_t) + 20 < t < tB - 20:
                            cands.append((abs(t - target) + 8, 1, 'v', val_, t))
                    if cands:
                        _, _, kind, val, tt = min(cands)
                    else:
                        kind, val = 'f', prev_th + 1
                        warn.append(f'{mid}: keine Schwelle im Fenster ({tA}-{tB}s)')
                if kind == 'f':
                    prev_th = max(prev_th, val)
                    prev_t = P['f'].get(val, prev_t)
                    trig[i] = {"typ": "fortschritt", "wert": round(val / 100, 2)}
                else:
                    prev_t = P['v'].get(val, prev_t)
                    trig[i] = {"typ": "verdient", "wert": val}
        report[w] = warn
        # balance schreiben
        bal['nachrichten'] = [{"id": m[0], "ausloeser": trig[i]} for i, m in enumerate(msgs)]
        dump(bal_p, bal)
        # theme
        th_p = os.path.join(ROOT, 'data', 'themes', w, 'theme.json')
        t = load(th_p)
        t['nachrichten'] = {}
        for m in msgs:
            e = {"von": m[1], "text": m[2]}
            if m[3]:
                e["antwort"] = m[3]
            t['nachrichten'][m[0]] = e
        t['absender'] = spec['absender']
        t['absender_farben'] = spec['farben']
        fig = {"mo": "figur_cap", "younes": "figur_buckethat", "roman": "figur_brille",
               "selin": "figur_zopf", "jana": "figur_packer", "du": "figur_kapuze"}
        t['absender_figur'] = {k: v for k, v in fig.items() if k in spec['absender']}
        ab = t['abschluss']
        ab['titel'] = spec['abschluss']['titel']
        ab['text'] = spec['abschluss']['text']
        ab['antwort'] = spec['abschluss']['antwort']
        if spec.get('weltwechsel'):
            t['weltwechsel'].update(spec['weltwechsel'])
        if w == 'zimmer':
            e = t['eroeffnung']
            e['text'] = spec['eroeffnung_text']
            e['chat'] = [{"von": a, "text": b} for a, b in spec['eroeffnung_chat']]
        ob = t['offline_bericht']
        ob['von'] = spec['offline_von']
        ob['saetze'] = spec['offline_saetze']
        for bid, dtxt in spec['danach'].items():
            t['bereiche'][bid]['danach'] = dtxt
        dump(th_p, t)
        # Auslöser für Lesung
        json.dump({"trig": [(m[0], trig[i]) for i, m in enumerate(msgs)]},
                  open(os.path.join(SP, f'trig_{w}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for w, wr in report.items():
        for x in wr:
            print('WARN', w, x)
    print('gebaut')

if __name__ == '__main__':
    if '--erzwingen' not in sys.argv:
        sys.exit("""ABBRUCH: Die theme.json und balance/*.json wurden nach dem Generieren von Hand poliert (Nacht 15.10.2026).
Dieses Skript wuerde sie ueberschreiben. Nur mit --erzwingen fortfahren (vorher sichern!).""")
    build([a for a in sys.argv[1:] if a != '--erzwingen'][0])
