import unittest,math
from pathlib import Path
from clearinglab.market import Market
from clearinglab.types import Account,Position,D
from clearinglab.reference_margin import ReferenceMargin
from clearinglab.validation import validate_report,require_methods
from clearinglab.candidate import CandidateClearingEngine
from clearinglab.scenarios import SCENARIOS

DATA=Path(__file__).resolve().parents[1]/'data'
class MarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=Market(DATA);cls.r=ReferenceMargin(cls.m)
    def test_instruments(self):self.assertGreaterEqual(len(self.m.instruments),100)
    def test_market_days(self):self.assertEqual(len(self.m.dates),180)
    def test_valid_quotes(self):self.assertEqual(self.m.validate_marks(),[])
    def test_spot_positive(self):
        for u in ('BTC','ETH','SOL','AVAX'):
            for day in (0,37,88,179):self.assertGreater(self.m.spot(day,u),0)
    def test_perp_quote_present(self):
        for day in (0,30,90,179):self.assertGreater(self.m.mark(day,'BTC-PERP')['mid'],0)
    def test_missing_quote_rejected(self):
        with self.assertRaises(KeyError):self.m.mark(180,'BTC-PERP')
    def test_scenarios_unique(self):self.assertEqual(len({s.name for s in SCENARIOS}),len(SCENARIOS))
    def test_has_severe_crash(self):self.assertTrue(any(s.spot.get('BTC',0)<=-.3 for s in SCENARIOS))
    def test_has_vol_crush(self):self.assertTrue(any(s.vol_shift<0 for s in SCENARIOS))
    def test_has_correlation_break(self):self.assertTrue(any(s.correlation_break for s in SCENARIOS))
    def test_has_liquidity_scenario(self):self.assertTrue(any(s.liquidity_haircut for s in SCENARIOS))
    def test_cash_only_zero_margin(self):
        a=Account('a',D('10000'))
        r=self.r.evaluate(a,10)
        self.assertEqual(r.initial_margin,0)
        self.assertEqual(r.maintenance_margin,0)
        self.assertEqual(r.equity,10000)
    def test_simple_long_perp_margin(self):
        a=Account('a',D('20000'),{'BTC-PERP':Position('BTC-PERP',D('1'),D(self.m.mark(10,'BTC-PERP')['mid']))})
        r=self.r.evaluate(a,10)
        self.assertGreater(r.initial_margin,0)
        self.assertGreater(r.gross_notional,0)
        self.assertFalse(validate_report(r))
    def test_short_option_margin_positive(self):
        iid=next(i for i,v in self.m.instruments.items() if v.kind=='CALL' and v.underlying=='BTC')
        a=Account('a',D('10000'),{iid:Position(iid,D('-12'),D(self.m.mark(20,iid)['mid']))})
        r=self.r.evaluate(a,20)
        self.assertGreater(r.initial_margin,0)
    def test_scenario_report_complete(self):
        a=Account('a',D('10000'),{'BTC-PERP':Position('BTC-PERP',D('-1'),D('40000'))})
        r=self.r.evaluate(a,5)
        self.assertEqual(set(r.scenario_losses),{s.name for s in SCENARIOS})
    def test_overleveraged_account_breached(self):
        a=Account('a',D('100'),{'BTC-PERP':Position('BTC-PERP',D('50'),D(self.m.mark(20,'BTC-PERP')['mid']))})
        self.assertTrue(self.r.evaluate(a,20).breached)
    def test_perp_unshocked_scenario_has_no_pnl(self):
        # vol_crush has no spot move and no liquidity haircut, so a perp-only book is flat.
        a=Account('a',D('20000'),{'BTC-PERP':Position('BTC-PERP',D('10'),D(self.m.mark(10,'BTC-PERP')['mid']))})
        self.assertEqual(self.r.evaluate(a,10).scenario_losses['vol_crush'],0)
    def test_perp_shock_scales_own_mark(self):
        inst=self.m.instruments['BTC-PERP'];crash=next(s for s in SCENARIOS if s.name=='crypto_crash_30')
        self.assertAlmostEqual(self.r._repriced(inst,10,crash),self.m.mark(10,'BTC-PERP')['mid']*0.70)
    def test_empty_account_not_breached(self):
        self.assertFalse(self.r.evaluate(Account('a',D('1')),0).breached)
    def test_candidate_interfaces_present(self):self.assertEqual(require_methods(CandidateClearingEngine),[])
    def test_candidate_pretrade_unfinished(self):
        with self.assertRaises(NotImplementedError):CandidateClearingEngine(self.m).pretrade(Account('a'),0,None)
    def test_candidate_liquidation_unfinished(self):
        with self.assertRaises(NotImplementedError):CandidateClearingEngine(self.m).liquidate(Account('a'),0,None)
    def test_candidate_reconciliation_unfinished(self):
        with self.assertRaises(NotImplementedError):CandidateClearingEngine(self.m).reconcile(None,0)
    def test_report_finite(self):
        for day in (0,20,60,100,179):
            a=Account('a',D('20000'),{'ETH-PERP':Position('ETH-PERP',D('2'),D('3000'))})
            self.assertFalse(validate_report(self.r.evaluate(a,day)))
    def test_initial_margin_at_least_maintenance(self):
        a=Account('a',D('20000'),{'ETH-PERP':Position('ETH-PERP',D('-2'),D('3000'))})
        for day in (0,30,100,179):
            r=self.r.evaluate(a,day)
            self.assertGreaterEqual(r.initial_margin,r.maintenance_margin)
