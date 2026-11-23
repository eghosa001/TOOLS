"""Offline unit checks for time-matched intraday research safety."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from intraday_research_utils import (
    agreement_gate, protection_settings, startup_candles,
    time_consistent_crash_mask
)
from risk_guards import crash_mask


class IntradayResearchSafety(unittest.TestCase):
    def test_equivalent_crash_mask_for_12h_baseline(self):
        c=np.full(415, 100.,dtype=float)
        c[400]=90.
        frame=pd.DataFrame({"close":c})
        self.assertTrue(
            time_consistent_crash_mask(frame, "12h").equals(crash_mask(frame))
        )
        self.assertTrue(time_consistent_crash_mask(frame, "12h").iloc[400])
        self.assertTrue(time_consistent_crash_mask(frame, "12h").iloc[403])
        # The 3-day comparison detects the same drop for six bars;
        # 48h cooldown extends another four bars (last blocked at 408).
        self.assertFalse(time_consistent_crash_mask(frame, "12h").iloc[409])

    def test_crash_12h_is_not_one_five_minute_change(self):
        c=np.full(2000,100.,dtype=float)
        # A one-bar 1% move will not be seen as 8% 12h crash.
        c[145:]=99.0
        masks=time_consistent_crash_mask(pd.DataFrame({"close":c}),"5m")
        self.assertFalse(masks.iloc[200])
        c[600:]=90.0
        masks=time_consistent_crash_mask(pd.DataFrame({"close":c}),"5m")
        self.assertTrue(masks.iloc[600])
        self.assertTrue(masks.iloc[900])
        self.assertFalse(masks.iloc[1500])

    def test_5m_startup_covers_three_day_shock_plus_two_day_block(self):
        self.assertGreaterEqual(startup_candles("5m"),1440)
        self.assertGreaterEqual(startup_candles("15m"),480)
        self.assertEqual(startup_candles("1h"),400)

    def test_9_of_10_is_stricter_than_8(self):
        votes=pd.Series([0,1,2,3,7,8,9,10])
        long8,short8=agreement_gate(votes,8)
        long9,short9=agreement_gate(votes,9)
        self.assertTrue(long9.le(long8).all())
        self.assertTrue(short9.le(short8).all())
        self.assertEqual(int(long8.sum()),3)
        self.assertEqual(int(long9.sum()),2)
        self.assertEqual(int(short8.sum()),3)
        self.assertEqual(int(short9.sum()),2)
        with self.assertRaises(ValueError):
            agreement_gate(votes,7)

    def test_cooldowns_are_elapsed_minutes_not_candle_counts(self):
        strict=protection_settings("strict")
        active=protection_settings("active")
        self.assertEqual(strict[1]["stop_duration"],10080)
        self.assertEqual(active[1]["stop_duration"],1440)
        self.assertEqual(strict[2]["max_allowed_drawdown"],.04)
        self.assertEqual(active[2]["max_allowed_drawdown"],.04)
        self.assertEqual(strict[2]["lookback_period"],10080)
        self.assertTrue(all("stop_duration_candles" not in x for x in strict))


if __name__=="__main__":
    unittest.main()
