"""Deterministic market replay. Designed to be extended with matched sides and expiry."""
import csv
from pathlib import Path
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

    def events_by_day(self):
        daily_events={}
        for e in self.events: daily_events.setdefault(int(e['day']),[]).append(e)
        return daily_events

    def apply_event(self,e):
        """Post one events.csv row to the ledger. Returns False for an already-seen event id."""
        op=e['operation'];eid=e['event_id'];day=int(e['day']);a=e['account_id']
        if op=='deposit': return self.ledger.deposit(eid,day,a,e['amount'])
        if op=='withdraw': return self.ledger.withdraw(eid,day,a,e['amount'])
        if op=='fill': return self.ledger.apply_fill(eid,day,a,e['instrument_id'],e['quantity'],e['price'],e['fee'])
        if op=='funding': return self.ledger.funding(eid,day,a,e['instrument_id'],e['rate'],e['price'])
        raise ValueError(f'unknown operation {op!r} in event {eid}')

    def run(self,until_day=None):
        daily_events=self.events_by_day()
        for day in range(max(self.market.dates)+1):
            if until_day is not None and day>until_day:break
            # Count only newly posted events, so re-running a window does not double count.
            count=sum(1 for e in daily_events.get(day,[]) if self.apply_event(e))
            if day%5==0 or day==max(self.market.dates):
                equity=sum(float(self.ledger.equity(a,day,self.market)) for a in self.ledger.accounts)
                # Only risk a deterministic subset for reasonable runtime.
                sampled=sorted(self.ledger.accounts)[:min(12,len(self.ledger.accounts))]
                breached=sum(self.margin.evaluate(self.ledger.accounts[a],day).breached for a in sampled)
                self.summary.append({'day':day,'events':count,'equity_total':round(equity,2),
                                     'sampled_breaches':breached,'accounts':len(self.ledger.accounts)})
        return {'ledger_audit':self.ledger.audit(),'ledger_fingerprint':self.ledger.fingerprint(),
                'events':len(self.ledger.events),'summary':self.summary}
