"""Matched comparison regression tests: all synthetic; no API, market access or orders."""
import unittest
import shadow_evaluation as e


def done(value):
    return {"status": "closed", "net_usd": float(value), "hypothetical": True}


def make_signal(idx, five, two, stopfive, stoptwo, action, two1000=None, five500=None,
                success=True, active_two=True):
    settled = {"5d_1000": done(five), "2d_500": done(two),
               "5d_1000_stop5": done(stopfive), "2d_500_stop3": done(stoptwo)}
    if two1000 is not None:
        settled["2d_1000"] = done(two1000)
    if five500 is not None:
        settled["5d_500_gpt_adaptive"] = done(five500)
    return {
        "id": str(idx), "paper_entry_utc": "2026-11-%02dT10:00:00+00:00" % idx,
        "CPU_5d_1000_active": True, "CPU_2d_500_active": active_two,
        "settlements": settled, "gpt_status": "SUCCESS_SHADOW" if success else "FAILED_SHADOW_NO_CPU_CHANGE",
        "gpt_advice": {"choice": action},
        "broker_orders": 0, "gpt_applies_to_cpu": False,
    }


class ShadowRiskAuditTests(unittest.TestCase):
    def setUp(self):
        self.state = {"signals": [
            make_signal(3, 5, 2, 5, 2, "KEEP_5D", 2, 4, active_two=False),
            make_signal(1, 10, 3, 8, 2.5, "SKIP", 6, 5),
            make_signal(2, -8, -4, -5, -3, "KEEP_2D", -4, -6),
        ]}

    def test_matched_cpu_gpt_winner_not_hidden(self):
        r = e.evaluate(self.state)
        v = r["five_day_gpt_veto"]
        self.assertEqual(v["matched_signals"], 3)
        self.assertEqual(v["cpu"]["net_usd"], 7)
        self.assertEqual(v["candidate"]["net_usd"], -3)
        self.assertEqual(v["gpt_skipped_winners"], 1)
        self.assertEqual(v["gpt_skipped_losers"], 0)
        self.assertEqual(v["gpt_missed_winning_usd"], 10)
        self.assertEqual(v["net_improvement_usd"], -10)
        self.assertFalse(r["gpt_can_override_cpu"])
        self.assertFalse(r["gpt_approved_for_live_orders"])

    def test_horizon_adaptation_respects_position_size(self):
        r = e.evaluate(self.state)
        v = r["five_day_gpt_horizon"]
        self.assertEqual(v["matched_signals"], 3)
        self.assertEqual(v["cpu"]["net_usd"], 7)
        self.assertEqual(v["candidate"]["net_usd"], 1)
        self.assertEqual(v["net_improvement_usd"], -6)

    def test_fixed_stop_is_compared_on_same_signal(self):
        r = e.evaluate(self.state)
        v = r["five_day_fixed_stop"]
        self.assertEqual(v["matched_signals"], 3)
        self.assertEqual(v["cpu"]["net_usd"], 7)
        self.assertEqual(v["candidate"]["net_usd"], 8)
        self.assertEqual(v["gpt_skipped_winners"], 0)

    def test_two_day_gate_is_respected(self):
        r = e.evaluate(self.state)
        self.assertEqual(r["two_day_gated_cpu_signals_matured"], 2)
        v = r["two_day_gpt_veto"]
        self.assertEqual(v["matched_signals"], 2)
        self.assertEqual(v["cpu"]["net_usd"], -1)
        self.assertEqual(v["candidate"]["net_usd"], -4)

    def test_no_missing_adaptive_outcome_masquerades_as_completed(self):
        self.state["signals"][2]["settlements"].pop("2d_1000")
        r = e.evaluate(self.state)
        self.assertEqual(r["five_day_gpt_veto"]["matched_signals"], 3)
        self.assertEqual(r["five_day_gpt_horizon"]["matched_signals"], 2)

    def test_failed_gpt_not_treated_as_keep(self):
        self.state["signals"][1]["gpt_status"] = "FAILED_SHADOW_NO_CPU_CHANGE"
        r = e.evaluate(self.state)
        self.assertEqual(r["five_day_gpt_veto"]["matched_signals"], 2)
        self.assertEqual(r["missing_or_failed_gpt_signal_records"], 1)

    def test_empty_forward_ledger_is_not_proof_of_profit(self):
        r = e.evaluate({"signals": []})
        self.assertEqual(r["five_day_gpt_veto"]["matched_signals"], 0)
        self.assertIsNone(r["five_day_gpt_veto"]["net_improvement_usd"])

    def test_zero_pnl_does_not_claim_improvement(self):
        c = e.comparison([(0.0, 0.0, False)], "CPU", "GPT")
        self.assertEqual(c["net_improvement_usd"], 0.0)
        self.assertIsNone(c["gross_loss_reduction_pct"])
        self.assertIsNone(c["closed_drawdown_reduction_pct"])


if __name__ == "__main__":
    unittest.main()
