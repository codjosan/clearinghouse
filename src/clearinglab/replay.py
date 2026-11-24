"""Deterministic market replay. Designed to be extended with matched sides and expiry."""
import csv
from pathlib import Path
from decimal import Decimal
from .ledger import Ledger
from .market import Market
from .reference_margin import ReferenceMargin

class Replay:
    def __init__(self,data_dir,engine_cls=ReferenceMargin):
        self.data_dir=Path(data_dir);self.market=Market(self.data_dir)
        self.ledger=Ledger(self.market.instruments)
        self.margin=engine_cls(self.market)
        with (self.data_dir/'events.csv').open(newline='') as f:
            self.events=list(csv.DictReader(f))
        self.summary=[]

    def run(self,until_day=None):
        daily_events={}
        for e in self.events: daily_events.setdefault(int(e['day']),[]).append(e)
        for day in range(max(self.market.dates)+1):
            if until_day is not None and day>until_day:break
            count=0
            for e in daily_events.get(day,[]):
                op=e['operation'];eid=e['event_id'];a=e['account_id']
                if op=='deposit': self.ledger.deposit(eid,day,a,e['amount'])
                elif op=='fill': self.ledger.apply_fill(eid,day,a,e['instrument_id'],e['quantity'],e['price'],e['fee'])
                elif op=='funding': self.ledger.funding(eid,day,a,e['instrument_id'],e['rate'],e['price'])
                else: raise ValueError(op)
                count+=1
            if day%5==0 or day==max(self.market.dates):
                equity=sum(float(self.ledger.equity(a,day,self.market)) for a in self.ledger.accounts)
                # Only risk a deterministic subset for reasonable runtime.
                sampled=sorted(self.ledger.accounts)[:min(12,len(self.ledger.accounts))]
                breached=sum(self.margin.evaluate(self.ledger.accounts[a],day).breached for a in sampled)
                self.summary.append({'day':day,'events':count,'equity_total':round(equity,2),
                                     'sampled_breaches':breached,'accounts':len(self.ledger.accounts)})
        return {'ledger_audit':self.ledger.audit(),'ledger_fingerprint':self.ledger.fingerprint(),
                'events':len(self.ledger.events),'summary':self.summary}
