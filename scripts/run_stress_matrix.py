import sys,json,csv
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from clearinglab.replay import Replay
from clearinglab.candidate import CandidateClearingEngine
from clearinglab.scenarios import SCENARIOS
r=Replay(root/'data')
from collections import defaultdict
by_day=defaultdict(list)
for e in r.events:by_day[int(e['day'])].append(e)
checkpoints=[10,25,40,55,70,85,100,115,130,145,160,179]
rows=[]
for day in range(180):
    for e in by_day.get(day,[]):
        eid=e['event_id'];a=e['account_id'];op=e['operation']
        if op=='deposit':r.ledger.deposit(eid,day,a,e['amount'])
        elif op=='fill':r.ledger.apply_fill(eid,day,a,e['instrument_id'],e['quantity'],e['price'],e['fee'])
        elif op=='funding':r.ledger.funding(eid,day,a,e['instrument_id'],e['rate'],e['price'])
    if day not in checkpoints:continue
    risk=CandidateClearingEngine(r.market)
    for aid,acct in sorted(r.ledger.accounts.items()):
        report=risk.evaluate(acct,day)
        for name,pnl in report.scenario_losses.items():
            rows.append({'day':day,'account':aid,'scenario':name,'pnl':round(pnl,4),
                         'equity':round(report.equity,4),'initial_margin':round(report.initial_margin,4),
                         'breached':int(report.breached)})
out=root/'outputs'/'stress';out.mkdir(parents=True,exist_ok=True)
with (out/'scenario_account_losses.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
summary={'records':len(rows),'accounts':len(r.ledger.accounts),'scenarios':len(SCENARIOS),
         'checkpoints':checkpoints,'source':'starter reference risk until candidate implemented'}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
