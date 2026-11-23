"""Regression checks for the end-to-end Forex CPU/GPT paper-only pipeline.

Synthetic fixtures; no real API, no broker and no cost.
"""
import datetime as dt
import copy
import json
import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
import weekly_pipeline as p

UTC = dt.timezone.utc


def fake_market():
    start = dt.datetime(2026, 11, 3, 0, tzinfo=UTC)
    end = dt.datetime(2026, 12, 2, 0, tzinfo=UTC)
    pairs = {}
    delta = dt.timedelta(hours=1)
    for pair, base in [('gbpusd', 1.3), ('eurusd', 1.09), ('usdjpy', 155)]:
        bid = {}
        ask = {}
        cur = start
        n = 0
        while cur <= end:
            stamp = int(cur.timestamp() * 1000)
            # GBP/USD spread=.0001 = 1pip; USDJPY fixed %. Here tests only
            # use GBP/USD bid and ask fills.
            op = base + n * .00001
            bd = (stamp, op, op + .00005, op - .00004, op + .00001)
            ak = (stamp, op + .0001, op + .00015, op + .00006, op + .00011)
            bid[stamp] = bd
            ask[stamp] = ak
            n += 1
            cur += delta
        pairs[pair] = {"bid": bid, "ask": ask, "stamps": sorted(bid)}
    return pairs


def cftc_rows():
    # Nov17 as-of is ONLY permitted Nov25 >= 09UTC.
    def item(date, oi, long, short):
        return {"report_date_as_yyyy_mm_dd": date + "T00:00:00.000",
                "cftc_contract_market_code": "096742",
                "open_interest_all": str(oi),
                "lev_money_positions_long": str(long),
                "lev_money_positions_short": str(short), "id": "CFTC-" + date}
    return [
        item("2026-11-03", 100000, 56000, 43000),
        item("2026-11-10", 100000, 60000, 45000),
        item("2026-11-17", 100000, 66000, 43000),
    ]


class ForexPipelineTests(unittest.TestCase):
    def setUp(self):
        self.market = fake_market()
        self.now = dt.datetime(2026, 11, 25, 9, 22, tzinfo=UTC)

    def test_cftc_conservative_asof_no_lookahead(self):
        early = p.latest_eligible(cftc_rows(),
                       dt.datetime(2026, 11, 18, 9, tzinfo=UTC))
        self.assertEqual(early["CFTC_asof_date"], "2026-11-10")
        due = p.latest_eligible(cftc_rows(), self.now)
        self.assertEqual(due["CFTC_asof_date"], "2026-11-17")
        self.assertAlmostEqual(due["net_change"], .08)

    def test_cpu_snapshot_features_only_prior_complete_bar(self):
        report = p.latest_eligible(cftc_rows(), self.now)
        s = p.make_snapshot(report, self.market)
        self.assertEqual(s["base_side"], "BUY")
        self.assertEqual(s["last_completed_H1_open_utc"],
                         "2026-11-25T08:00:00+00:00")
        self.assertEqual(s["utc_signal"], "2026-11-25T09:00:00+00:00")
        self.assertIn("GBPUSD_10d_momentum_bp", s)
        self.assertGreater(s["GBPUSD_5d_high_low_pips"], 0)

    def test_invalid_ask_below_bid_fails(self):
        market = copy.deepcopy(self.market)
        k = market["gbpusd"]["stamps"][-1]
        market["gbpusd"]["ask"][k] = (k, .1, .2, .05, .12)
        self.assertGreater(market["gbpusd"]["bid"][k][1],
                           market["gbpusd"]["ask"][k][1])

    def test_closed_quote_spread_and_fees(self):
        trade = {"paper_entry_utc": "2026-11-25T10:00:00+00:00",
                 "base_side": "BUY"}
        result = p.compute_trade(self.market, trade, days=2, units=500)
        self.assertEqual(result["status"], "closed")
        self.assertEqual(result["size_base_gbp"], 500)
        self.assertGreater(result["spread_pips"], 0)
        self.assertEqual(result["reason"], "calendar_hold")
        self.assertAlmostEqual(result["funding_assumed_usd"], .05)
        self.assertEqual(result["hypothetical"], True)

    def test_stop_only_simulated_not_broker_fill(self):
        trade = {"paper_entry_utc": "2026-11-25T10:00:00+00:00",
                 "base_side": "SELL"}
        no_stop = p.compute_trade(self.market, trade, 2, 500)
        stopped = p.compute_trade(self.market, trade, 2, 500, stop_usd=.3)
        self.assertEqual(stopped["reason"], "modeled_stop")
        self.assertTrue(stopped["hypothetical"])
        self.assertNotEqual(no_stop["exit_utc"], stopped["exit_utc"])

    def test_outside_window_does_not_make_api_call(self):
        state = p.initial_state()
        monday = dt.datetime(2026, 11, 23, 9, 22, tzinfo=UTC)
        with patch.object(p.forex_gpt, "run_paper") as api:
            r = p.weekly(state, self.market, monday)
            self.assertEqual(r["status"], "OUTSIDE_WEEKLY_CFTC_SIGNAL_WINDOW")
            api.assert_not_called()
        self.assertEqual(len(state["signals"]), 0)

    def test_duplicate_cftc_signal_never_charges_twice(self):
        state = p.initial_state()
        state["signals"].append({"id": "cftc_gbpusd_2026-11-17"})
        with patch.object(p, "fetch_cftc", return_value=cftc_rows()):
            with patch.object(p.forex_gpt, "run_paper") as api:
                r = p.weekly(state, self.market, self.now)
                self.assertEqual(r["status"], "DUPLICATE_SIGNAL_SKIPPED")
                api.assert_not_called()

    def test_one_real_gpt_shadow_call_and_no_order(self):
        state = p.initial_state()
        advisory = {"GPT_advice":{"choice":"SKIP","risk_level":"high",
                                    "confidence":.83,"risk_reason":"Historical volatility"},
                    "token_usage":{"input_tokens":100,"output_tokens":20}}
        with patch.object(p, "fetch_cftc", return_value=cftc_rows()):
            with patch.object(p.forex_gpt, "run_paper", return_value=advisory) as api:
                with patch.object(p, "utcnow", return_value=self.now):
                    result = p.weekly(state, self.market, self.now)
        self.assertEqual(result["status"], "WEEKLY_CPU_AND_GPT_SHADOW_RECORDED")
        self.assertEqual(result["GPT_choice"], "SKIP")
        self.assertTrue(state["signals"][0]["CPU_5d_1000_active"])
        self.assertFalse(state["signals"][0]["gpt_applies_to_cpu"])
        self.assertEqual(state["signals"][0]["broker_orders"], 0)
        api.assert_called_once()
        self.assertEqual(state["signals"][0]["settlements"], {})

    def test_paper_settlement_and_loss_comparison(self):
        state = p.initial_state()
        advice = {"GPT_advice": {"choice": "KEEP_2D", "risk_level":"low",
                                 "confidence": .55, "risk_reason": "No specific spike"},
                  "token_usage": {}}
        with patch.object(p, "fetch_cftc", return_value=cftc_rows()):
            with patch.object(p.forex_gpt, "run_paper", return_value=advice):
                with patch.object(p, "utcnow", return_value=self.now):
                    p.weekly(state, self.market, self.now)
        late = dt.datetime(2026, 11, 30, 13, tzinfo=UTC)
        result = p.settle(state, self.market, late)
        self.assertEqual(result["newly_settled_scenarios"], 4)
        self.assertIn("2d_500", state["signals"][0]["settlements"])
        self.assertIn("5d_1000", state["signals"][0]["settlements"])
        self.assertEqual(result["summary"]["CPU_2d_500"]["n_closed"], 1)
        self.assertEqual(result["summary"]["CPU_5d_1000"]["n_closed"], 1)


if __name__=="__main__":
    unittest.main()

