import unittest
from clearinglab.types import RiskReport
from clearinglab.validation import validate_report
class ValidationTests(unittest.TestCase):
    def make(self,**kwargs):
        values=dict(equity=100,initial_margin=40,maintenance_margin=30,excess_equity=60,
                    breached=False,greeks={},worst_loss=25,scenario_losses={},gross_notional=400)
        values.update(kwargs)
        return RiskReport(**values)
    def test_valid(self):self.assertEqual(validate_report(self.make()),[])
    def test_negative_margin(self):self.assertIn('negative margin',validate_report(self.make(initial_margin=-1)))
    def test_inverted_margin(self):self.assertIn('maintenance > initial',validate_report(self.make(maintenance_margin=50)))
    def test_bad_excess(self):self.assertIn('excess mismatch',validate_report(self.make(excess_equity=42)))
    def test_nan_equity(self):self.assertIn('equity: nonfinite',validate_report(self.make(equity=float('nan'))))
    def test_inf_margin(self):self.assertIn('initial_margin: nonfinite',validate_report(self.make(initial_margin=float('inf'))))
