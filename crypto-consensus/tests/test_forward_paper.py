"""Offline invariants: no real market requests, orders, or user credentials."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forward_paper import initial_state, order_size, close, PAIR_ID, TWELVE_H, simulate_observation
from risk_guards import ensure_risk_state, inspect_account


class PaperSafety(unittest.TestCase):
    def setUp(self):
        self.market={"id":PAIR_ID, "linear":True, "contractSize":1.0,
                     "precision":{"amount":0.001}}
    def test_never_overexposes_and_obeys_minimum(self):
        q=order_size(150,1700,140,self.market)
        self.assertGreaterEqual(q,0.0)
        self.assertLessEqual(q*1700,150)
        self.assertLessEqual(q*(max(2.5*140,.04*1700)+.002*1700),150*.01+1e-8)
        self.assertEqual(order_size(0.5,1700,140,self.market),0)
    def test_wrong_contract_fails_closed(self):
        wrong=dict(self.market,id="WRONG")
        with self.assertRaises(RuntimeError):
            order_size(150,1700,140,wrong)
    def test_loss_requires_seven_day_pause(self):
        state=initial_state()
        state["balance"]=150-0.0001*2000
        state["position"]={"side":1,"qty":.1,"entry":2000.0,
            "stop":1800., "starting_balance":150.,
            "entered":"2026-11-23T00:00:00Z"}
        timestamp=1795478400000
        close(state,1800,timestamp,"test")
        self.assertIsNone(state["position"])
        self.assertEqual(state["cooldown_until_ms"],timestamp+14*TWELVE_H)
        self.assertLess(state["trades"][-1]["net_usd"],0)



    def test_crash_gap_triggers_manual_lock_even_when_loss_exceeds_threshold(self):
        # These are observation-time controls, not a guarantee that a gap cannot exceed 6%.
        state=initial_state()
        start=1795428000000
        ensure_risk_state(state,start,150.0)
        state["balance"]=149.9
        state["position"]={"side":1,"qty":0.03,"entry":2000.0,"stop":1920.0,
                            "starting_balance":150.0,"entered":"2026-11-23T10:00:00Z"}
        crash_price=1000.0
        equity=state["balance"]+state["position"]["qty"]*(crash_price-2000)
        reasons=inspect_account(state,start+3600000,equity)
        self.assertTrue(any("peak_drawdown" in r for r in reasons))
        self.assertTrue(state["permanent_risk_lock"])
        self.assertLess(equity,141)  # Already worse than 6% before detection.

if __name__=="__main__":
    unittest.main()
