"""Forex GPT no-API, no-secret regression tests."""
import datetime as dt
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
import forex_gpt as fx

class Tests(unittest.TestCase):
    def case(self):
        t = dt.datetime(2026, 11, 25, 9, tzinfo=dt.timezone.utc)
        obj = {"utc_signal": t.isoformat(), "CFTC_asof_date": "2026-11-17",
               "base_side": "SELL", "CFTC_weekly_net_change": -.03}
        for f in fx.FEATURES:
            obj.setdefault(f, 2.5)
        return obj, t

    def test_valid(self):
        x, t = self.case()
        self.assertEqual(fx.validate_snapshot(x, t + dt.timedelta(minutes=15)), x)

    def test_stale_refused(self):
        x, t = self.case()
        with self.assertRaisesRegex(ValueError, "Expired"):
            fx.validate_snapshot(x, t + dt.timedelta(minutes=91))

    def test_wrong_report_refused(self):
        x, t = self.case()
        x["CFTC_asof_date"] = "2026-11-10"
        with self.assertRaisesRegex(ValueError, "eligible"):
            fx.validate_snapshot(x, t + dt.timedelta(minutes=15))

    def test_conflicting_direction_refused(self):
        x, t = self.case()
        x["base_side"] = "BUY"
        with self.assertRaisesRegex(ValueError, "contradictory"):
            fx.validate_snapshot(x, t + dt.timedelta(minutes=15))

    def test_missing_key_refused(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "not configured"):
                fx.call_api("GET", "/models/gpt-6-luna")

    def test_connection_check_uses_no_inference(self):
        with patch.object(fx, "call_api", return_value={"id": fx.MODEL}) as api:
            self.assertEqual(fx.run_check()["paid_predictions"], 0)
            self.assertEqual(api.call_args.args[0], "GET")

if __name__ == "__main__":
    unittest.main()
