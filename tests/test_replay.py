import unittest, tempfile
from pathlib import Path
from clearinglab.replay import Replay
from clearinglab.ledger import Ledger
DATA=Path(__file__).resolve().parents[1]/'data'
class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=Replay(DATA)
        cls.summary=cls.r.run(until_day=10)
    def test_account_count(self):self.assertEqual(len(self.r.ledger.accounts),120)
    def test_event_count(self):self.assertGreater(self.summary['events'],300)
    def test_cash_balance(self):self.assertTrue(self.summary['ledger_audit']['balanced'])
    def test_unique_events(self):self.assertTrue(self.summary['ledger_audit']['unique_events'])
    def test_replay_determinism(self):
        x=Replay(DATA).run(until_day=10)
        self.assertEqual(x['ledger_fingerprint'],self.summary['ledger_fingerprint'])
    def test_replay_journal_equivalence(self):
        other=self.r.ledger.replay()
        self.assertEqual(other.fingerprint(),self.r.ledger.fingerprint())
    def test_daily_summary_structure(self):
        self.assertTrue(self.summary['summary'])
        self.assertIn('equity_total',self.summary['summary'][0])
    def test_cash_posting_count(self):self.assertGreater(self.summary['ledger_audit']['cash_postings'],120)
    def test_no_duplicate_account_ids(self):
        self.assertEqual(len(set(self.r.ledger.accounts)),120)
    def test_fee_pool_nonnegative(self):
        self.assertGreaterEqual(self.r.ledger.system_accounts['fee_pool'],0)
