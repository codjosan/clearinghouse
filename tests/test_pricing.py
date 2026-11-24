import unittest,math
from clearinglab.pricing import bs_price,bs_greeks,implied_vol

class PricingTests(unittest.TestCase):
    def test_put_call_parity(self):
        for s in (50,100,150):
            for k in (75,100,125):
                for vol in (.1,.5,1.0):
                    c=bs_price(s,k,.5,vol,True)
                    p=bs_price(s,k,.5,vol,False)
                    self.assertAlmostEqual(c-p,s-k,places=8)
    def test_intrinsic_at_expiry(self):
        for k in (90,100,110):
            self.assertEqual(bs_price(100,k,0,.5,True),max(100-k,0))
            self.assertEqual(bs_price(100,k,0,.5,False),max(k-100,0))
    def test_implied_vol_round_trip(self):
        for vol in (.15,.4,.9):
            for kind in (True,False):
                px=bs_price(100,103,.4,vol,kind)
                self.assertAlmostEqual(implied_vol(px,100,103,.4,kind),vol,places=5)
    def test_monotonicity_spot(self):
        self.assertLess(bs_price(90,100,.5,.5,True),bs_price(110,100,.5,.5,True))
        self.assertGreater(bs_price(90,100,.5,.5,False),bs_price(110,100,.5,.5,False))
    def test_monotonicity_vol(self):
        for kind in (True,False):
            self.assertLess(bs_price(100,100,.5,.2,kind),bs_price(100,100,.5,.8,kind))
    def test_positive_vega_gamma(self):
        for s in (50,100,150):
            for kind in (True,False):
                g=bs_greeks(s,100,.5,.5,kind)
                self.assertGreater(g['gamma'],0)
                self.assertGreater(g['vega'],0)
    def test_delta_ranges(self):
        for s in (50,100,150):
            c=bs_greeks(s,100,.5,.5,True)['delta']
            p=bs_greeks(s,100,.5,.5,False)['delta']
            self.assertTrue(0<c<1)
            self.assertTrue(-1<p<0)
            self.assertAlmostEqual(c-p,1)
    def test_invalid_inputs(self):
        for args in [(0,100,.5,.4),(100,-1,.5,.4),(100,100,-1,.4),(100,100,.5,-1)]:
            with self.assertRaises(ValueError):bs_price(*args)
    def test_iv_rejects_impossible(self):
        with self.assertRaises(ValueError):implied_vol(-5,100,100,.5)
    def test_zero_vol_limit(self):
        self.assertAlmostEqual(bs_price(100,90,.5,0,True),10)
    def test_option_prices_bounded(self):
        for s in (50,100,200):
            for k in (50,100,200):
                for kind in (True,False):
                    x=bs_price(s,k,1,.5,kind)
                    self.assertGreaterEqual(x,0)
                    self.assertLessEqual(x,s if kind else k)
    def test_greeks_finite(self):
        for vol in (.01,.1,1,2):
            for tau in (.001,.1,2):
                g=bs_greeks(100,110,tau,vol)
                self.assertTrue(all(math.isfinite(v) for v in g.values()))
