import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from risk_guards import crash_mask, ensure_risk_state, inspect_account, can_enter, WEEK_MS

class CrashGuards(unittest.TestCase):
    def test_crash_mask_is_causal_and_cools_down(self):
        series = [100.]*10 + [80.,79.,81.,80.] + [80.]*10
        df = pd.DataFrame({"close": series})
        output = crash_mask(df)
        self.assertTrue(output.iloc[10])
        self.assertTrue(output.iloc[12])
        self.assertFalse(output.iloc[-1])
        for n in range(12,len(df)):
            self.assertEqual(bool(output.iloc[n-1]),bool(crash_mask(df.iloc[:n]).iloc[-1]))

    def test_daily_cutoff_pauses(self):
        now = int(pd.Timestamp("2026-11-23T12:00:00Z").timestamp()*1000)
        s = {"cooldown_until_ms":0}
        ensure_risk_state(s,now,150.)
        reasons = inspect_account(s,now+3600000,146.9)
        self.assertTrue(any("daily" in r for r in reasons))
        self.assertFalse(can_enter(s,now+3600000))

    def test_weekly_and_peak_drawdown_locks(self):
        now = int(pd.Timestamp("2026-11-23T12:00:00Z").timestamp()*1000)
        s = {"cooldown_until_ms":0}
        ensure_risk_state(s,now,150.)
        reasons = inspect_account(s,now+3600000,143.9)
        self.assertTrue(any("weekly" in r for r in reasons))
        self.assertGreaterEqual(s["weekly_pause_until_ms"],now+WEEK_MS)
        reasons = inspect_account(s,now+7200000,140.7)
        self.assertTrue(any("peak" in r for r in reasons))
        self.assertTrue(s["permanent_risk_lock"])
        self.assertFalse(can_enter(s,now+100*WEEK_MS))

    def test_crash_blocks_entries(self):
        s = {"cooldown_until_ms":0}
        ensure_risk_state(s,10000,150.)
        self.assertFalse(can_enter(s,10000,crash=True))
        self.assertTrue(can_enter(s,10000,crash=False))

if __name__=="__main__":
    unittest.main()
