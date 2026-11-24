"""Dataset integrity audit. Uses explicit checks (not `assert`, which `python -O` strips)."""
import sys,csv,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from clearinglab.market import Market

def read_rows(name):
    with (root/'data'/name).open(newline='') as f:return list(csv.DictReader(f))

market=Market(root/'data');meta=json.loads((root/'data/manifest.json').read_text())
instrument_rows=read_rows('instruments.csv')
rows=read_rows('events.csv')
failures=[]
def check(ok,message):
    if not ok:failures.append(message)

check(len(market.instruments)==meta['instruments'],'instrument count does not match manifest')
check(len(market.marks)==meta['mark_rows'],'mark row count does not match manifest (or duplicate day/instrument marks)')
check(len(market.index)==meta['index_rows'],'index row count does not match manifest (or duplicate day/underlying rows)')
check(len(market.dates)==meta['days'],'day count does not match manifest')
bad_marks=market.validate_marks()
check(not bad_marks,f'{len(bad_marks)} marks with invalid bid/mid/ask')
# Market keys instruments by id, so duplicates must be detected on the raw rows.
check(len({r['instrument_id'] for r in instrument_rows})==len(instrument_rows),'duplicate instrument ids')
check(len(rows)==meta['event_rows'],'event row count does not match manifest')
check(len({e['event_id'] for e in rows})==len(rows),'duplicate event ids')
check([int(e['day']) for e in rows]==sorted(int(e['day']) for e in rows),'events not in chronological order')
unknown=[e['event_id'] for e in rows if e['instrument_id'] and e['instrument_id'] not in market.instruments]
check(not unknown,f'{len(unknown)} events reference unknown instruments')
# Funding must settle against that day's index, never a different (e.g. future) day's price.
stale_funding=[e['event_id'] for e in rows if e['operation']=='funding' and e['instrument_id'] in market.instruments
               and abs(float(e['price'])-market.spot(int(e['day']),market.instruments[e['instrument_id']].underlying))>1e-6]
check(not stale_funding,f'{len(stale_funding)} funding events not priced at the same-day index (first: {stale_funding[:3]})')

if failures:
    print(json.dumps({'audit':'FAIL','failures':failures},indent=2))
    raise SystemExit(1)
print(json.dumps({'audit':'PASS',**meta},indent=2))
