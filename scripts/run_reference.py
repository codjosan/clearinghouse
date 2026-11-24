import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from clearinglab.replay import Replay
result=Replay(root/'data').run()
out=root/'outputs/reference';out.mkdir(parents=True,exist_ok=True)
(out/'replay_summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'audit':result['ledger_audit'],'fingerprint':result['ledger_fingerprint'],
                  'events':result['events'],'sampled_days':len(result['summary'])},indent=2))
