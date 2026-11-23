"""No remote data or Freqtrade required: checks pure signal and safety invariants."""
import sys
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import build_indicators, decision, SIGNAL_NAMES, STARTUP_CANDLES


class CoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(20261123)
        n = 850
        prices = 2500 * np.exp(np.cumsum(rng.normal(0,.009,n)))
        cls.data = pd.DataFrame({
            "open": prices * (1 + rng.normal(0,.001,n)),
            "high": prices * 1.02,
            "low": prices * .98,
            "close": prices,
            "volume": rng.lognormal(11,1,n),
        })

    def test_ten_votes_and_vote_ranges(self):
        self.assertEqual(len(SIGNAL_NAMES), 10)
        out = build_indicators(self.data)
        self.assertTrue(((out.buy_votes >= 0)&(out.buy_votes<=10)).all())
        self.assertTrue((out.buy_votes+out.sell_votes == 10).all())
        self.assertTrue(out.atr14.ge(0).all())
        self.assertFalse(out.warm.iloc[STARTUP_CANDLES-1])
        self.assertTrue(out.warm.iloc[STARTUP_CANDLES])

    def test_no_future_candles_change_prior_signal(self):
        whole = build_indicators(self.data)
        for end in [420, 500, 650, 800]:
            past = build_indicators(self.data.iloc[:end])
            self.assertEqual(int(past.buy_votes.iloc[-1]),int(whole.buy_votes.iloc[end-1]))
            self.assertAlmostEqual(float(past.atr14.iloc[-1]),
                                   float(whole.atr14.iloc[end-1]),places=9)

    def test_decisions(self):
        self.assertEqual(decision(8), 1)
        self.assertEqual(decision(2), -1)
        self.assertEqual(decision(7), 0)
        self.assertEqual(decision(4,1), 2)
        self.assertEqual(decision(6,-1), 2)
        self.assertEqual(decision(5,1), 0)

    def test_no_missing_ohlcv(self):
        data=self.data.copy()
        data.loc[4,"close"]=float("nan")
        with self.assertRaises(ValueError):
            build_indicators(data)


if __name__=="__main__":
    unittest.main()
