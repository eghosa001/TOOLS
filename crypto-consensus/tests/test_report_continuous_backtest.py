"""No network tests: verify one-wallet backtest accounting and losing weeks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report_continuous_backtest import analyse, markdown


def fixture():
    return {
        "strategy": {
            "GuardedConsensusETH": {
                "starting_balance": 150.0,
                "final_balance": 151.0,
                "max_drawdown_account": .02,
                "trades": [
                    {"open_date": "2026-11-02 12:00:00",
                     "close_date": "2026-11-10 12:00:00",
                     "profit_abs": -1.5, "amount": .02,
                     "open_rate": 2000., "close_rate": 2100.,
                     "fee_open": .0005, "fee_close": .0005,
                     "funding_fees": -.05, "exit_reason": "stop_loss"},
                    {"open_date": "2026-11-12 12:00:00",
                     "close_date": "2026-11-21 12:00:00",
                     "profit_abs": 2.5, "amount": .02,
                     "open_rate": 2000., "close_rate": 1800.,
                     "fee_open": .0005, "fee_close": .0005,
                     "funding_fees": .03, "exit_reason": "force_exit"}
                ]
            }
        }
    }


class ContinuousBacktest(unittest.TestCase):
    def test_reconcile_all_weeks_and_carry_open_trade(self):
        result = analyse(fixture(), "2026-11-02", "2026-11-23")
        self.assertEqual(result["net_profit_usd"], 1.0)
        self.assertEqual(result["net_return_pct"], .6667)
        self.assertEqual(result["total_closed_trades"], 2)
        self.assertEqual(result["wins"], 1)
        self.assertEqual(result["losses"], 1)
        self.assertEqual(result["full_period_max_drawdown_pct"], 2.0)
        self.assertEqual(result["end_of_test_forced_exits"], 1)
        self.assertEqual(len(result["weeks"]), 3)
        self.assertEqual(result["weeks"][1]["closed_net_profit_usd"], -1.5)
        self.assertEqual(result["weeks"][2]["closed_net_profit_usd"], 2.5)
        self.assertEqual(result["weeks"][0]["open_positions_crossed_week_boundary"], 1)
        self.assertIn("unrealized", markdown(result))

    def test_reject_bad_report_reconciliation(self):
        broken = fixture()
        broken["strategy"]["GuardedConsensusETH"]["final_balance"] = 161
        with self.assertRaisesRegex(ValueError, "reconcile"):
            analyse(broken, "2026-11-02", "2026-11-23")

    def test_does_not_report_weekly_drawdowns_as_known(self):
        result = analyse(fixture(), "2026-11-02", "2026-11-23")
        self.assertNotIn("weekly_max_drawdown_pct", result["weeks"][0])

    def test_rejects_misaligned_dates(self):
        broken = fixture()
        broken["strategy"]["GuardedConsensusETH"]["trades"][0]["close_date"] = "2027-01-01"
        with self.assertRaises(ValueError):
            analyse(broken, "2026-11-02", "2026-11-23")


if __name__ == "__main__":
    unittest.main()
