"""Double-entry cash journal and deterministic replay, with a minimal position cost basis.

The candidate should extend this to complete novation, settlement, fees, and insurance.
"""
from copy import deepcopy
from decimal import Decimal
from .types import Account,Position,D
import hashlib,json

class Ledger:
    def __init__(self, instruments):
        self.instruments=instruments
        self.accounts={}
        self.events=[]
        self.seen=set()
        self.cash_book=[]
        self.system_accounts={'external':D('0'),'fee_pool':D('0'),'insurance':D('0')}

    def ensure(self, account_id):
        if account_id not in self.accounts: self.accounts[account_id]=Account(account_id)
        return self.accounts[account_id]

    def _check(self,event_id):
        if event_id in self.seen: return False
        self.seen.add(event_id)
        return True

    def _cash(self,event_id,day,account_id,amount,counterparty,reason):
        # Fixed settlement precision prevents long replay trails of sub-cent dust.
        amount=D(amount).quantize(D('0.00000001'))
        account=self.ensure(account_id)
        account.cash+=amount
        self.system_accounts[counterparty]=self.system_accounts.get(counterparty,D('0'))-amount
        self.cash_book.append({'event_id':event_id,'day':day,'account_id':account_id,
                               'amount':str(amount),'counterparty':counterparty,'reason':reason})

    def deposit(self,event_id,day,account_id,amount):
        if D(amount)<=0: raise ValueError('deposit must be positive')
        if not self._check(event_id): return False
        self._cash(event_id,day,account_id,amount,'external','deposit')
        self.events.append({'id':event_id,'op':'deposit','day':day,'account':account_id,'amount':str(D(amount))})
        return True

    def withdraw(self,event_id,day,account_id,amount):
        amount=D(amount)
        if amount<=0: raise ValueError('withdraw must be positive')
        if event_id in self.seen: return False
        if self.ensure(account_id).cash < amount: raise ValueError('insufficient free cash')
        self._check(event_id)
        self._cash(event_id,day,account_id,-amount,'external','withdraw')
        self.events.append({'id':event_id,'op':'withdraw','day':day,'account':account_id,'amount':str(amount)})
        return True

    def apply_fill(self,event_id,day,account_id,instrument_id,quantity,price,fee=0):
        if event_id in self.seen: return False
        quantity=D(quantity); price=D(price); fee=D(fee)
        if quantity==0 or price<=0 or fee<0: raise ValueError('invalid fill')
        if instrument_id not in self.instruments: raise KeyError(instrument_id)
        self._check(event_id)
        acct=self.ensure(account_id)
        pos=acct.positions.setdefault(instrument_id,Position(instrument_id))
        old=pos.quantity
        new=old+quantity
        multiplier=self.instruments[instrument_id].multiplier
        # Only realize on closing quantity; reversing resets the cost basis.
        close_qty=min(abs(old),abs(quantity)) if old*quantity<0 else D('0')
        realized=close_qty*(price-pos.average_entry)*(D('1') if old>0 else D('-1'))*multiplier
        if close_qty:
            self._cash(event_id,day,account_id,realized,'external','realized_pnl')
            pos.realized_pnl+=realized
        if new==0: pos.average_entry=D('0')
        elif old==0 or old*quantity>=0:
            pos.average_entry=(abs(old)*pos.average_entry+abs(quantity)*price)/abs(new)
        elif abs(quantity)>abs(old):
            pos.average_entry=price
        pos.quantity=new
        self._cash(event_id,day,account_id,-fee,'fee_pool','trade_fee')
        self.events.append({'id':event_id,'op':'fill','day':day,'account':account_id,
                            'instrument':instrument_id,'qty':str(quantity),'price':str(price),'fee':str(fee)})
        return True

    def funding(self,event_id,day,account_id,instrument_id,rate,index_price):
        if event_id in self.seen: return False
        if instrument_id not in self.instruments or self.instruments[instrument_id].kind!='PERP':
            raise ValueError('funding only on perpetual')
        acct=self.ensure(account_id)
        pos=acct.positions.get(instrument_id)
        quantity=pos.quantity if pos else D('0')
        payment=-quantity*D(index_price)*D(rate)*self.instruments[instrument_id].multiplier
        self._check(event_id)
        self._cash(event_id,day,account_id,payment,'external','funding')
        self.events.append({'id':event_id,'op':'funding','day':day,'account':account_id,
                            'instrument':instrument_id,'rate':str(D(rate)),'index':str(D(index_price))})
        return True

    def equity(self,account_id,day,market):
        account=self.ensure(account_id)
        value=account.cash
        for iid,p in account.positions.items():
            if p.quantity:
                value+=(D(market.mark(day,iid)['mid'])-p.average_entry)*p.quantity*self.instruments[iid].multiplier
        return value

    def audit(self):
        totals=sum((a.cash for a in self.accounts.values()),D('0'))
        totals+=sum(self.system_accounts.values(),D('0'))
        return {'balanced':totals==0,'sum_cash':str(totals.normalize()),
                'unique_events':len(self.seen)==len(self.events),
                'events':len(self.events),'cash_postings':len(self.cash_book)}

    def fingerprint(self):
        payload={'events':self.events,'balances':{k:str(v.cash) for k,v in sorted(self.accounts.items())}}
        return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

    def replay(self):
        other=Ledger(self.instruments)
        for e in self.events:
            op=e['op']; args=(e['id'],e['day'],e['account'])
            if op=='deposit': other.deposit(*args,e['amount'])
            elif op=='withdraw': other.withdraw(*args,e['amount'])
            elif op=='fill': other.apply_fill(*args,e['instrument'],e['qty'],e['price'],e['fee'])
            elif op=='funding': other.funding(*args,e['instrument'],e['rate'],e['index'])
            else: raise ValueError(op)
        return other
