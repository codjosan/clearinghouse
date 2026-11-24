"""Naive margin reference: candidate must deliver defensible portfolio-risk upgrades."""
from collections import defaultdict
from math import isfinite
from .pricing import bs_price,bs_greeks
from .scenarios import SCENARIOS
from .types import RiskReport,D,RiskLimits

class ReferenceMargin:
    def __init__(self,market,limits=None): self.market=market;self.limits=limits or RiskLimits()
    def _repriced(self,inst,day,shock):
        original=self.market.mark(day,inst.instrument_id)
        s=self.market.spot(day,inst.underlying)*(1+shock.spot.get(inst.underlying,0.))
        if inst.kind in ('CALL','PUT'):
            tau=max(0,(inst.expiry_day-day)/365)
            return bs_price(s,float(inst.strike),tau,max(0.01,original['iv']+shock.vol_shift),inst.kind=='CALL')
        return s

    def evaluate(self,account,day):
        greeks=defaultdict(float)
        base=0.0;gross=0.0
        positions=[]
        for iid,p in account.positions.items():
            if not p.quantity: continue
            inst=self.market.instruments[iid]
            mark=self.market.mark(day,iid)
            qty=float(p.quantity*inst.multiplier)
            mid=mark['mid']
            base+=(mid-float(p.average_entry))*qty
            underlying=self.market.spot(day,inst.underlying)
            if inst.kind in ('CALL','PUT'):
                g=bs_greeks(underlying,float(inst.strike),max(0,(inst.expiry_day-day)/365),mark['iv'],inst.kind=='CALL')
            else:g={'delta':1.,'gamma':0.,'vega':0.,'theta':0.}
            for k,v in g.items(): greeks[k]+=v*qty
            gross+=abs(qty)*underlying if inst.kind in ('PERP','FUT') else abs(qty)*max(mid,underlying*0.10)
            positions.append((inst,qty,mid))
        pnl_by_scenario={}
        for shock in SCENARIOS:
            pnl=0.0
            for inst,qty,mid in positions:
                new=self._repriced(inst,day,shock)
                pnl+=qty*(new-mid)
                pnl-=abs(qty)*(new if inst.kind in ('CALL','PUT') else self.market.spot(day,inst.underlying))*shock.liquidity_haircut*0.003
            pnl_by_scenario[shock.name]=pnl
        worst_loss=max(0,-min(pnl_by_scenario.values(),default=0))
        floor=gross*self.limits.minimum_margin_rate
        concentration=self.limits.concentration_surcharge*max(0,gross-500000)
        initial=max(worst_loss+concentration,floor)
        maintenance=initial*self.limits.maintenance_fraction
        equity=float(account.cash)+base
        return RiskReport(equity=equity,initial_margin=initial,maintenance_margin=maintenance,
                          excess_equity=equity-initial,breached=equity<maintenance,
                          greeks=dict(greeks),worst_loss=worst_loss,scenario_losses=pnl_by_scenario,
                          gross_notional=gross,diagnostics={'reference_only':True})
