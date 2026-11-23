"""Offline invariants: no real market requests, orders, or user credentials."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forward_paper import initial_state, order_size, close, PAIR_ID, TWELVE_H, simulate_observation


class PaperSafety(unittest.TestCase):
    def setUp(self):
        self.market={"id":PAIR_ID, "linear":True, "contractSize":1.0,
                     "precision":{"amount":0.001}}
    def test_never_overexposes_and_obeys_minimum(self):
        q=order_size(150,1700,140,self.market)
        self.assertGreaterEqual(q,0.0)
        self.assertLessEqual(q*1700,150)
        self.assertLessEqual(q*2.5*140,150*.02+1e-8)
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


if __name__=="__main__":
    unittest.main()
