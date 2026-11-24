"""Zero hourly cooldown experiments must never delete market or risk controls."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import json

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from intraday_research_utils import protection_settings
from one_hour_no_time_locks_report import COINS,SCENARIOS,DATES,FEES,export,summarize


class ClockRestrictionAuditTests(unittest.TestCase):
    def test_four_scenarios_and_fee_profiles_are_frozen(self):
        self.assertEqual(SCENARIOS,(
            "Baseline","NoPostTradeWait","NoLossPause","NoTimeLocks"))
        self.assertEqual(COINS,{"ETH":8,"SOL":9})
        self.assertEqual(set(FEES),{"normal","stress"})
        self.assertEqual(set(DATES),{"early","later","full"})

    def test_existing_baseline_contains_both_timed_waits_and_drawdown_guard(self):
        p=protection_settings("active")
        methods={x["method"]:x for x in p}
        self.assertEqual(methods["CooldownPeriod"]["stop_duration"],180)
        self.assertEqual(methods["StoplossGuard"]["stop_duration"],1440)
        self.assertEqual(methods["LowProfitPairs"]["stop_duration"],1440)
        self.assertEqual(methods["MaxDrawdown"]["max_allowed_drawdown"],.04)
        self.assertEqual(methods["MaxDrawdown"]["lookback_period"],10080)

    def test_isolated_strategy_does_not_modify_forward_live_or_paper_files(self):
        path=Path(__file__).resolve().parents[1].joinpath(
            "user_data/strategies/OneHourNoTimeLocksResearch.py")
        content=path.read_text()
        for forbidden in ("create_order(","create_market_order(","set_leverage(",
                          "one_hour_forward_state.json","forward_paper_state.json"):
            self.assertNotIn(forbidden,content)
        self.assertIn('"MaxDrawdown"',content)

    def test_forced_end_exit_disclosed_not_natural_gain(self):
        doc={
            "starting_balance":150,
            "final_balance":150.75,
            "max_drawdown_account":.012,
            "trades":[
                {
                    "pair":"ETH/USD:USD","leverage":1,
                    "open_date":"2026-01-06 00:00:00+00:00",
                    "close_date":"2026-01-06 01:00:00+00:00",
                    "profit_abs":-.25,"exit_reason":"stop_loss",
                },
                {
                    "pair":"ETH/USD:USD","leverage":1,
                    "open_date":"2026-07-30 00:00:00+00:00",
                    "close_date":"2026-08-01 00:00:00+00:00",
                    "profit_abs":1.,"exit_reason":"force_exit",
                },
            ]
        }
        result=summarize(doc,"ETH","NoTimeLocks","early","normal")
        self.assertEqual(result["natural_trades"],1)
        self.assertEqual(result["natural_trade_net_usd"],-.25)
        self.assertEqual(result["forced_end_exit_count"],1)
        self.assertEqual(result["forced_end_exit_profit_usd"],1.)
        self.assertEqual(result["total_closed_trades"],2)
        self.assertEqual(result["positive_natural_close_days"],0)
        self.assertEqual(result["backtester_reported_max_drawdown_pct"],1.2)

    def test_no_coin_mix_or_insolvent_account(self):
        doc={
            "starting_balance":150,
            "final_balance":-2,
            "max_drawdown_account":.02,
            "trades":[],
        }
        with self.assertRaises(ValueError):
            summarize(doc,"SOL","Baseline","full","stress")
        doc["final_balance"]=150
        doc["trades"]=[{
            "pair":"BTC/USD:USD","leverage":1,
            "open_date":"2026-01-10 00:00:00+00:00",
            "close_date":"2026-01-10 01:00:00+00:00",
            "profit_abs":0.,"exit_reason":"stop_loss",
        }]
        with self.assertRaisesRegex(ValueError,"Wrong coin"):
            summarize(doc,"SOL","Baseline","full","stress")


if __name__=="__main__":
    unittest.main()
