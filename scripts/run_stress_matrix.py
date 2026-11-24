import sys,json,csv
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from clearinglab.replay import Replay
from clearinglab.candidate import CandidateClearingEngine
from clearinglab.scenarios import SCENARIOS
r=Replay(root/'data',CandidateClearingEngine)
by_day=r.events_by_day()
last_day=max(r.market.dates)
checkpoints=[10,25,40,55,70,85,100,115,130,145,160,last_day]
rows=[]
for day in range(last_day+1):
    # Shared dispatch: unknown operations raise instead of being silently dropped.
    for e in by_day.get(day,[]):r.apply_event(e)
    if day not in checkpoints:continue
    for aid,acct in sorted(r.ledger.accounts.items()):
        report=r.margin.evaluate(acct,day)
        for name,pnl in report.scenario_losses.items():
            rows.append({'day':day,'account':aid,'scenario':name,'pnl':round(pnl,4),
                         'equity':round(report.equity,4),'initial_margin':round(report.initial_margin,4),
                         'breached':int(report.breached)})
if not rows:raise SystemExit('no stress rows produced: no accounts at any checkpoint')
out=root/'outputs'/'stress';out.mkdir(parents=True,exist_ok=True)
with (out/'scenario_account_losses.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
summary={'records':len(rows),'accounts':len(r.ledger.accounts),'scenarios':len(SCENARIOS),
         'checkpoints':checkpoints,'source':'starter reference risk until candidate implemented'}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
