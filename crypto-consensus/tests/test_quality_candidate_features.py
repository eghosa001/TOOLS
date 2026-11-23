import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality_candidate_features import (btc_regime, volatility_breakout,
                                         ml_direction, parse_official_oi,
                                         derivatives_crowding)


def frame(n=520, start="2025-03-01"):
    date = pd.date_range(start, periods=n, freq="12h", tz="UTC")
    t = np.arange(n)
    close = 1900. * np.exp(.00035 * t + .028 * np.sin(t / 18.))
    return pd.DataFrame({"date": date,
                         "open": close * .997,
                         "high": close * 1.012,
                         "low": close * .985,
                         "close": close,
                         "volume": 110. + 40 * np.sin(t / 16.) ** 2})


class QualitySignals(unittest.TestCase):
    def test_rolling_ml_unchanged_when_future_candles_added(self):
        df = frame()
        initial = ml_direction(df.iloc[:420])
        extended = ml_direction(df)
        np.testing.assert_allclose(
            initial["ml_pred"].to_numpy(),
            extended["ml_pred"].iloc[:420].to_numpy(),
            equal_nan=True, rtol=1e-12, atol=1e-12)
        self.assertTrue(initial.iloc[:320]["ml_pred"].isna().all())

    def test_breakouts_are_causal(self):
        df = frame()
        original = volatility_breakout(df.iloc[:480])
        more = volatility_breakout(df)
        self.assertTrue(original.equals(more.iloc[:480]))
        self.assertFalse(original.iloc[0]["breakout_long"])

    def test_btc_uses_prior_completed_bar(self):
        eth, btc = frame(), frame(start="2025-03-01")
        first = btc_regime(eth.iloc[:470], btc.iloc[:470])
        more = btc_regime(eth, btc)
        self.assertTrue(first.equals(more.iloc[:470]))
        # Flip an index's current BTC candle: same-date ETH decision unchanged.
        changed = btc.copy()
        changed.loc[469, "close"] *= 0.2
        a = btc_regime(eth.iloc[:470], btc.iloc[:470])
        b = btc_regime(eth.iloc[:470], changed.iloc[:470])
        self.assertEqual(bool(a.iloc[-1]["btc_up"]), bool(b.iloc[-1]["btc_up"]))
        self.assertEqual(bool(a.iloc[-1]["btc_down"]), bool(b.iloc[-1]["btc_down"]))

    def test_oi_rejects_gaps_and_future(self):
        base = pd.Timestamp("2025-12-24", tz="UTC")
        stamps = [(base + pd.Timedelta(hours=4*i)).timestamp()
                  for i in range(700)]
        doc = {"errors":[], "result":{
            "timestamp":[int(t) for t in stamps],
            "data":[["11000", "11020", "10800", str(11000+i)] for i in range(700)]
        }}
        oi = parse_official_oi(doc)
        self.assertEqual(oi.loc[0, "known_at"], base + pd.Timedelta(hours=4))
        self.assertTrue(np.isnan(oi.loc[0, "oi_growth_7d"]))
        broken = {"errors": [], "result": {
            "timestamp": [int(t) for t in stamps[1:]],
            "data": doc["result"]["data"]}}
        with self.assertRaises(ValueError):
            parse_official_oi(broken)

    def test_derivatives_need_actual_published_funding_and_oi(self):
        start = pd.Timestamp("2025-12-20", tz="UTC")
        dates = pd.date_range(start, periods=1000, freq="1h")
        funding = pd.DataFrame({"date": dates,
                                "funding_rate": .00001 + .00001 * np.sin(np.arange(1000) / 14)})
        oi_dates = pd.date_range(start, periods=250, freq="4h")
        doc = {"errors":[], "result":{
            "timestamp":[int(t.timestamp()) for t in oi_dates],
            "data":[["11000", "11300", "10900", str(11000+i*2)] for i in range(250)]}}
        eth = frame(50, start="2026-01-01")
        result = derivatives_crowding(eth, funding, doc)
        self.assertEqual(len(result), 50)
        self.assertIn("deriv_funding_z", result)
        broken = funding.rename(columns={"funding_rate":"open"})
        with self.assertRaises(ValueError):
            derivatives_crowding(eth, broken, doc)


if __name__ == "__main__":
    unittest.main()
