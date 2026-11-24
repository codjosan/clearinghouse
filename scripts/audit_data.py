import sys,csv,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from clearinglab.market import Market
root=Path(__file__).resolve().parents[1]
market=Market(root/'data');meta=json.loads((root/'data/manifest.json').read_text())
assert len(market.instruments)==meta['instruments']
assert len(market.marks)==meta['mark_rows']
assert len(market.index)==meta['index_rows']
assert len(market.dates)==meta['days']
assert not market.validate_marks()
assert len({inst.instrument_id for inst in market.instruments.values()})==len(market.instruments)
with (root/'data/events.csv').open() as f:
    rows=list(csv.DictReader(f))
assert len(rows)==meta['event_rows']
assert len({e['event_id'] for e in rows})==len(rows)
assert [int(e['day']) for e in rows]==sorted(int(e['day']) for e in rows)
print(json.dumps({'audit':'PASS',**meta},indent=2))
