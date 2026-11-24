"""Acceptance gate verification script for the clearing engine."""
from pathlib import Path
import sys,json,copy
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from clearinglab.market import Market
from clearinglab.ledger import Ledger
from clearinglab.candidate import CandidateClearingEngine
from clearinglab.validation import validate_report,require_methods

market=Market(root/'data');candidate=CandidateClearingEngine(market)
ledger=Ledger(market.instruments);ledger.deposit('dep',0,'test',100000)
ledger.apply_fill('entry',0,'test','BTC-PERP',1,market.mark(0,'BTC-PERP')['mid'],10)
acct=ledger.accounts['test']
results={};errors=[]
try:
    rep=candidate.evaluate(acct,0)
    results['risk_report_valid']=not validate_report(rep)
    if not results['risk_report_valid']:errors.append('risk_report_invalid')
except Exception as exc:results['risk_report_valid']=False;errors.append('risk:'+repr(exc))
for label,fn,args in [
    ('pretrade',candidate.pretrade,(copy.deepcopy(acct),0,{'instrument_id':'BTC-PERP','quantity':1,'price':market.mark(0,'BTC-PERP')['mid'],'fee':1})),
    ('liquidation',candidate.liquidate,(copy.deepcopy(acct),0,{'max_slippage_bps':50})),
    ('reconciliation',candidate.reconcile,(ledger,0))]:
    try:
        value=fn(*args)
        results[label+'_implemented']=value is not None
        if value is None:errors.append(label+':empty result')
    except (NotImplementedError,Exception) as exc:
        results[label+'_implemented']=False
        errors.append(label+':'+str(exc))
results['ledger_balanced']=ledger.audit()['balanced']
results['starter_only_not_production_ready']=True
results['status']='INCOMPLETE' if errors else 'PROVISIONAL (independent hard gates still required)'
results['errors']=errors
out=root/'outputs'/'acceptance';out.mkdir(parents=True,exist_ok=True)
(out/'starter_gate.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
raise SystemExit(1 if errors else 0)
