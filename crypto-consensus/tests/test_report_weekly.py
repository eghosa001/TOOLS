"""Offline tests for completed weeks, missing data and no-reset weekly attribution."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from report_weekly import analyse, render

UTC = timezone.utc


def make_state():
    start = datetime(2026, 11, 9, tzinfo=UTC)  # Monday
    history = []
    for hour in range(14 * 24):
        moment = start + timedelta(hours=hour, minutes=17)
        value = (150 + .001 * hour) if hour < 168 else (
            150.167 - .012 * (hour - 168))
        history.append({
            "utc": moment.isoformat(),
            "equity_usd": round(value, 6),
            "position_open": hour > 100,
            "unrealized_usd": round(value - 150, 6),
            "fees_usd": round(hour * .0005, 6),
            "funding_usd": round(hour * .0001, 6),
        })
    return {
        "balance": 150, "equity_history": history,
        "last_observation": datetime(2026, 11, 23, 0, 17,
                                     tzinfo=UTC).isoformat(),
        "trades": [{
            "exited": datetime(2026, 11, 21, 0,
                               tzinfo=UTC).isoformat(),
            "net_usd": -.7,
        }],
    }


class WeeklyEvidence(unittest.TestCase):
    def test_two_complete_consecutive_weeks_without_wallet_reset(self):
        report = analyse(make_state())
        self.assertEqual(report["fully_covered_weeks"], 2)
        a, b = report["weeks"]
        self.assertEqual(a["status"], "verified_observation_coverage")
        self.assertEqual(b["status"], "verified_observation_coverage")
        self.assertEqual(a["closed_trades"], 0)
        self.assertEqual(b["losses"], 1)
        self.assertEqual(b["realized_trade_net_usd"], -.7)
        self.assertGreater(a["qualifying_weekly_return_pct"], 0)
        self.assertLess(b["qualifying_weekly_return_pct"], 0)
        self.assertEqual(report["weekly_starting_balance_reset"], False)
        self.assertIn("Not established", render({
            **report,
            "weeks": [{**b, "qualifying_weekly_return_pct": None}]
        }))

    def test_sparse_history_never_promotes_week_to_verified(self):
        state = make_state()
        state["equity_history"] = [
            x for i, x in enumerate(state["equity_history"])
            if i not in (100, 101, 102, 103)]
        report = analyse(state)
        self.assertEqual(report["fully_covered_weeks"], 1)
        self.assertEqual(report["weeks"][0]["status"], "incomplete_data")
        self.assertIsNone(report["weeks"][0]["qualifying_weekly_return_pct"])

    def test_missing_week_boundary_blocks_return(self):
        state = make_state()
        state["equity_history"] = state["equity_history"][8:]
        report = analyse(state)
        self.assertIsNone(report["weeks"][0]["qualifying_weekly_return_pct"])

    def test_duplicate_or_out_of_order_rejected(self):
        state = make_state()
        state["equity_history"].insert(4, state["equity_history"][3])
        with self.assertRaises(ValueError):
            analyse(state)

    def test_current_partial_week_is_not_complete(self):
        state = make_state()
        state["equity_history"] = state["equity_history"][:18]
        state["last_observation"] = state["equity_history"][-1]["utc"]
        report = analyse(state)
        self.assertEqual(report["weeks"][0]["status"], "in_progress")
        self.assertEqual(report["fully_covered_weeks"], 0)


if __name__ == "__main__":
    unittest.main()
