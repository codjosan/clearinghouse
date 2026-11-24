import csv, json
from pathlib import Path
from .types import Instrument,D

class Market:
    def __init__(self,data_dir):
        data_dir=Path(data_dir)
        self.instruments={}
        with (data_dir/'instruments.csv').open(newline='') as f:
            for r in csv.DictReader(f):
                self.instruments[r['instrument_id']]=Instrument(
                    r['instrument_id'],r['underlying'],r['kind'],D(r['strike']),
                    int(r['expiry_day']),D(r['multiplier']),D(r['tick_size']))
        self.marks={}
        with (data_dir/'marks.csv').open(newline='') as f:
            for r in csv.DictReader(f):
                self.marks[(int(r['day']),r['instrument_id'])]={
                    'mid':float(r['mid']),'bid':float(r['bid']),'ask':float(r['ask']),
                    'iv':float(r['iv']),'stale':bool(int(r['stale'])),'source':r['source']}
        self.index={}
        with (data_dir/'index.csv').open(newline='') as f:
            for r in csv.DictReader(f): self.index[(int(r['day']),r['underlying'])]=float(r['index_price'])
        self.dates=sorted({day for day,_ in self.index})
    def mark(self,day,instrument_id):
        try: return self.marks[(int(day),instrument_id)]
        except KeyError: raise KeyError(f'No mark: day={day} instrument={instrument_id}')
    def spot(self,day,underlying): return self.index[(int(day),underlying)]
    def validate_marks(self):
        errors=[]
        for key,row in self.marks.items():
            if row['bid']<0 or row['ask']<row['bid'] or not row['bid']<=row['mid']<=row['ask']:
                errors.append(key)
        return errors
