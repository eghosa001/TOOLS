"""Fast-consensus time units, independent causal votes, and no duplicate classes."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from intraday_research_report import model_name, summarize
from quality_candidate_features import ml_features
from risk_guards import CRASH_12H, CRASH_3D

# Research strategy file imports Freqtrade; those tests execute in the official
# Freqtrade Docker image, not in lightweight host Python.
class IntradayLightweight(unittest.TestCase):
    def test_all_twelve_model_identifiers(self):
        identifiers=set()
        for tf in ("1h","15m","5m"):
            for vote in (8,9):
                for mode in ("Strict","Active"):
                    identifiers.add(model_name(tf,vote,mode))
        self.assertEqual(len(identifiers),12)

    def test_trade_count_and_extra_cost_stress(self):
        rows=[
            {
                "pair":"ETH/USD:USD","leverage":1.0,
                "profit_abs":.5,"amount":.01,"open_rate":2000,
                "close_rate":2020,
                "open_date":"2026-09-20 12:00:00+00:00",
                "close_date":"2026-09-21 00:00:00+00:00",
                "exit_reason":"trailing_stop_loss",
            },
            {
                "pair":"ETH/USD:USD","leverage":1.0,
                "profit_abs":-.3,"amount":.02,"open_rate":2020,
                "close_rate":2035,
                "open_date":"2026-10-20 12:00:00+00:00",
                "close_date":"2026-10-21 00:00:00+00:00",
                "exit_reason":"trailing_stop_loss",
            }
        ]
        r=summarize({"starting_balance":150.,"final_balance":150.2,
                     "max_drawdown_account":.02,"trades":rows},
                     "ETH","5m",9,"Strict")
        self.assertEqual(r["closed_trades"],2)
        self.assertEqual(r["winning_trades"],1)
        self.assertEqual(r["losing_trades"],1)
        self.assertEqual(r["max_consecutive_losing_closes"],1)
        self.assertLess(r["stress_net_usd_fixed_trades"],r["net_usd"])
        self.assertEqual(len(r["closed_trade_weekly_attribution"]),2)

    def test_wrong_coin_and_real_leverage_rejected(self):
        trade={"pair":"SOL/USD:USD","leverage":1.0,
               "profit_abs":0.,"open_date":"2026-09-20 00:00:00+00:00",
               "close_date":"2026-09-20 00:05:00+00:00"}
        data={"starting_balance":150,"final_balance":150,"trades":[trade],
              "max_drawdown_account":0}
        with self.assertRaisesRegex(ValueError,"Mixed-coin"):
            summarize(data,"ETH","5m",8,"Strict")
        trade["pair"]="ETH/USD:USD"
        trade["leverage"]=3.
        with self.assertRaisesRegex(ValueError,"Leveraged"):
            summarize(data,"ETH","5m",8,"Strict")


if __name__=="__main__":
    unittest.main()
