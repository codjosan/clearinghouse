import unittest
from decimal import Decimal as D
from clearinglab.ledger import Ledger
from clearinglab.types import Instrument

I={'BTC-PERP':Instrument('BTC-PERP','BTC','PERP'),'BTC-CALL':Instrument('BTC-CALL','BTC','CALL',D('100'),200)}

class LedgerTests(unittest.TestCase):
    def setUp(self):self.l=Ledger(I);self.l.deposit('d1',0,'a',1000)
    def test_cash_journal_balanced(self):self.assertTrue(self.l.audit()['balanced'])
    def test_deposit_idempotence(self):
        self.assertFalse(self.l.deposit('d1',0,'a',1000))
        self.assertEqual(self.l.accounts['a'].cash,1000)
    def test_withdrawal(self):
        self.l.withdraw('w1',0,'a',250)
        self.assertEqual(self.l.accounts['a'].cash,750)
    def test_insufficient_withdrawal(self):
        with self.assertRaises(ValueError):self.l.withdraw('w1',0,'a',2000)
    def test_negative_deposit(self):
        with self.assertRaises(ValueError):self.l.deposit('d2',0,'a',-1)
    def test_negative_withdraw(self):
        with self.assertRaises(ValueError):self.l.withdraw('w1',0,'a',-1)
    def test_open_position(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100,1)
        p=self.l.accounts['a'].positions['BTC-PERP']
        self.assertEqual(p.quantity,2);self.assertEqual(p.average_entry,100)
    def test_add_position_weighted_average(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100)
        self.l.apply_fill('f2',0,'a','BTC-PERP',2,120)
        self.assertEqual(self.l.accounts['a'].positions['BTC-PERP'].average_entry,110)
    def test_close_long_realized_profit(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100)
        self.l.apply_fill('f2',1,'a','BTC-PERP',-2,110)
        self.assertEqual(self.l.accounts['a'].cash,1020)
    def test_close_short_realized_profit(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',-2,100)
        self.l.apply_fill('f2',1,'a','BTC-PERP',2,90)
        self.assertEqual(self.l.accounts['a'].cash,1020)
    def test_partial_close_keeps_cost_basis(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',3,100)
        self.l.apply_fill('f2',1,'a','BTC-PERP',-1,110)
        p=self.l.accounts['a'].positions['BTC-PERP']
        self.assertEqual(p.quantity,2);self.assertEqual(p.average_entry,100)
    def test_reversal_resets_basis(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100)
        self.l.apply_fill('f2',1,'a','BTC-PERP',-4,120)
        p=self.l.accounts['a'].positions['BTC-PERP']
        self.assertEqual(p.quantity,-2);self.assertEqual(p.average_entry,120)
        self.assertEqual(p.realized_pnl,40)
    def test_negative_fee_rejected(self):
        with self.assertRaises(ValueError):self.l.apply_fill('f1',0,'a','BTC-PERP',1,100,-1)
    def test_zero_quantity_rejected(self):
        with self.assertRaises(ValueError):self.l.apply_fill('f1',0,'a','BTC-PERP',0,100)
    def test_negative_price_rejected(self):
        with self.assertRaises(ValueError):self.l.apply_fill('f1',0,'a','BTC-PERP',1,-100)
    def test_unknown_instrument(self):
        with self.assertRaises(KeyError):self.l.apply_fill('f1',0,'a','BAD',1,100)
    def test_funding_long_pays_positive_rate(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100)
        self.l.funding('fnd',1,'a','BTC-PERP',.01,100)
        self.assertEqual(self.l.accounts['a'].cash,998)
    def test_funding_short_receives_positive_rate(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',-2,100)
        self.l.funding('fnd',1,'a','BTC-PERP',.01,100)
        self.assertEqual(self.l.accounts['a'].cash,1002)
    def test_funding_option_forbidden(self):
        with self.assertRaises(ValueError):self.l.funding('fnd',1,'a','BTC-CALL',.01,100)
    def test_idempotent_fills(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100)
        self.assertFalse(self.l.apply_fill('f1',0,'a','BTC-PERP',2,100))
        self.assertEqual(self.l.accounts['a'].positions['BTC-PERP'].quantity,2)
    def test_journal_replay_equivalence(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',2,100,1)
        self.l.apply_fill('f2',1,'a','BTC-PERP',-1,110,2)
        self.l.funding('fnd',1,'a','BTC-PERP',.01,100)
        self.l.withdraw('w1',1,'a',50)
        other=self.l.replay()
        self.assertEqual(other.fingerprint(),self.l.fingerprint())
        self.assertTrue(other.audit()['balanced'])
    def test_unknown_replay_event_not_allowed(self):
        self.l.events.append({'op':'unknown','id':'bad'})
        with self.assertRaises(Exception):self.l.replay()
    def test_realized_pnl_matches_posted_cash(self):
        # Sub-quantum products must not leave position PnL and the cash journal out of step.
        self.l.apply_fill('f1',0,'a','BTC-PERP','0.333','100.123457')
        self.l.apply_fill('f2',1,'a','BTC-PERP','-0.333','101.987653')
        posted=sum(D(c['amount']) for c in self.l.cash_book if c['reason']=='realized_pnl')
        self.assertEqual(self.l.accounts['a'].positions['BTC-PERP'].realized_pnl,posted)
    def test_atomic_balance_for_all_postings(self):
        self.l.apply_fill('f1',0,'a','BTC-PERP',1,100,4)
        self.l.withdraw('w1',0,'a',250)
        self.assertEqual(self.l.audit()['sum_cash'],'0')
