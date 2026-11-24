import unittest
from pathlib import Path
from clearinglab.replay import Replay

DATA=Path(__file__).resolve().parents[1]/'data'

class FullReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=Replay(DATA).run()

    def test_full_replay_has_all_events(self):
        self.assertEqual(self.first['events'],4763)

    def test_full_replay_balanced(self):
        self.assertTrue(self.first['ledger_audit']['balanced'])
        self.assertEqual(self.first['ledger_audit']['sum_cash'],'0')

    def test_full_replay_unique_ids(self):
        self.assertTrue(self.first['ledger_audit']['unique_events'])

    def test_full_replay_reproducible(self):
        other=Replay(DATA).run()
        self.assertEqual(other['ledger_fingerprint'],self.first['ledger_fingerprint'])

    def test_reference_reporting_has_last_day(self):
        self.assertEqual(self.first['summary'][-1]['day'],179)
