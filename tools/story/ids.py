import re,json,sys,os
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,SP)
import story as S
src=open(os.path.join(SP,'lesung.py'),encoding='utf-8').read()
ns={'__file__':os.path.join(SP,'lesung.py')}
exec(src.split('def zeiten')[0],ns)
beschreibe=ns['beschreibe']
ROOT = os.path.dirname(os.path.dirname(SP))
p=os.path.join(ROOT,'docs','nacht','ids_welten.md')
txt=open(p,encoding='utf-8').read()
order=['zimmer','auftrag','webseiten','buero','produkt','kapital']
parts=re.split(r'(?m)^(?=## Welt )',txt)
out=[parts[0]]
for part in parts[1:]:
    m=re.match(r'## Welt (\d)',part)
    w=order[int(m.group(1))-1]
    theme=json.load(open(os.path.join(ROOT,'project','data','themes',w,'theme.json'),encoding='utf-8'))
    trig=dict(json.load(open(os.path.join(SP,'trig_%s.json'%w),encoding='utf-8'))['trig'])
    rows=['**Nachrichten** (22, in Zustell-Reihenfolge; Absender und Text: `docs/nacht/rp_story_lesung.md`)','','| ID | kommt, wenn … | Absender |','|---|---|---|']
    for mm in S.W[w]['nachrichten']:
        rows.append('| `%s` | %s | %s |'%(mm[0],beschreibe(trig[mm[0]],theme),S.W[w]['absender'][mm[1]]))
    new='\n'.join(rows)+'\n\n'
    a=part.index('**Nachrichten**')
    out.append(part[:a]+new)
res=''.join(out)
old='Nachrichten kommen der Reihe nach, sobald ihr Auslöser erfüllt ist.'
if old in res:
    res=res.replace(old,'Nachrichten kommen der Reihe nach (22 je Welt, `nachricht_01…22`), sobald ihr Auslöser erfüllt ist.\nStand 2026-10-14 (Paket C+D): Nachrichten-Tabellen neu; neue Auslösertypen `fortschritt` (Welt zu x %), `stufen_gesamt`, `ausstattung_gesamt`.')
res=res.replace('## Welt 1 · Die WG (nur zur Orientierung, unverändert)','## Welt 1 · Die WG')
open(p,'w',encoding='utf-8',newline='\n').write(res.rstrip('\n')+'\n')
print('ok')
