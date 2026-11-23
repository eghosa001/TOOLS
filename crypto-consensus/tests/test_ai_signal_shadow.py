"""Offline invariants: no network, no secret, no order, no hindsight scores."""
from datetime import datetime, timezone
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai_signal_shadow import (
    BAR_MS, make_snapshot, run, score_history, build_report,
    validate_response, is_opted_in, SCHEMA,
)


def samples(n=410):
    start = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    out = []
    for i in range(n):
        price = 1800.0 + i * 1.2 + 10 * math.sin(i / 8)
        out.append([start + i * BAR_MS, price - 3, price + 5,
                    price - 8, price, 100.0 + i / 100])
    return out


class AIResearch(unittest.TestCase):
    def setUp(self):
        self.candles = samples()
        self.now = int(self.candles[-1][0]) + BAR_MS + 20 * 60_000
        self.state = {"version": 1, "signals": []}

    def test_closed_bar_timestamps_and_completed_only(self):
        snap = make_snapshot(self.candles, self.now)
        self.assertEqual(snap["candle_end_ms"], self.candles[-1][0] + BAR_MS)
        self.assertEqual(len(snap["model_input"]["closed_candles"]), 48)
        self.assertTrue(0 <= snap["baseline_votes"] <= 10)
        prior = make_snapshot(self.candles[:-1], self.now - BAR_MS)
        self.assertEqual(prior["candle_end_ms"], snap["candle_end_ms"] - BAR_MS)

    def test_missing_api_does_not_claim_chatgpt_vote(self):
        def illegal_provider(*args):
            raise AssertionError("No paid model call authorized")
        result = run(self.state, self.candles, self.now, 1798,
                     provider=illegal_provider, paid_enabled=True,
                     account_opt_in="false", api_key="dummy")
        self.assertEqual(result["signals"][0]["ai_signal"], None)
        self.assertIn("unavailable", result["signals"][0]["status"])
        self.assertEqual(build_report(result)["actual_ai_calls"], 0)
        self.assertFalse(is_opted_in(True, "true", ""))
        self.assertFalse(is_opted_in(False, "true", "key"))
        self.assertTrue(is_opted_in(True, "true", "key"))

    def test_one_valid_signal_and_idempotent_no_extra_charge(self):
        calls = []
        def fake(snapshot, api_key, model):
            calls.append(snapshot["input_sha256"])
            return {"signal": "BUY", "confidence": .67, "rationale": "Market trend"}
        state = run(self.state, self.candles, self.now, 1798,
                    provider=fake, paid_enabled=True,
                    account_opt_in="true", api_key="dummy")
        state = run(state, self.candles, self.now, 1800,
                    provider=fake, paid_enabled=True,
                    account_opt_in="true", api_key="dummy")
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(state["signals"]), 1)
        self.assertEqual(state["signals"][0]["reference_price"], 1798)

    def test_no_future_outcome_before_next_candle_closes(self):
        state = run(self.state, self.candles, self.now, 1800,
                    provider=lambda *_: {"signal": "SELL", "confidence": .6,
                                         "rationale": "Reversal"},
                    paid_enabled=True, account_opt_in="true", api_key="dummy")
        score_history(state, self.candles, self.now)
        self.assertIsNone(state["signals"][0]["result"])
        next_bar = samples(411)[-1]
        next_now = int(next_bar[0]) + BAR_MS + 20 * 60_000
        new_state = run(state, self.candles + [next_bar], next_now, 1810)
        self.assertIsNotNone(new_state["signals"][0]["result"])
        self.assertEqual(len(new_state["signals"]), 2)
        self.assertIsNone(new_state["signals"][1]["result"])
        self.assertEqual(new_state["signals"][1]["ai_signal"], None)
        self.assertNotIn("realized_account_profit", new_state["signals"][0]["result"])

    def test_stale_or_missing_candles_fail_closed(self):
        with self.assertRaises(ValueError):
            make_snapshot(self.candles, self.now + 3 * 3_600_000)
        gap = self.candles[:42] + self.candles[43:]
        with self.assertRaises(ValueError):
            make_snapshot(gap, self.now)
        with self.assertRaises(ValueError):
            make_snapshot(self.candles[:-1], self.now)

    def test_strict_prediction_safety(self):
        with self.assertRaises(ValueError):
            validate_response({"signal": "BUY", "confidence": 1.5,
                               "rationale": "Impossible certainty"})
        with self.assertRaises(ValueError):
            validate_response({"signal": "BUY", "confidence": True,
                               "rationale": "Boolean is not confidence"})
        with self.assertRaises(ValueError):
            validate_response({"signal": "BUY", "confidence": .5,
                               "rationale": "fine", "execute_order": True})
        self.assertTrue(SCHEMA["additionalProperties"] is False)

    def test_invalid_response_does_not_mutate_original_ledger(self):
        with self.assertRaises(ValueError):
            run(self.state, self.candles, self.now, 1800,
                provider=lambda *_: {"signal": "moon", "confidence": 1,
                                     "rationale": "bad"},
                paid_enabled=True, account_opt_in="true", api_key="dummy")
        self.assertEqual(self.state["signals"], [])


if __name__ == "__main__":
    unittest.main()
