"""No real orders: stop-ack contract mocks, dry-run config and watchdog."""
import json,tempfile,sys,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from preflight_dryrun import validate
from stop_contract import check_ack,response
from watchdog import check

class Safety(unittest.TestCase):
    def setUp(self):
        self.pos={"symbol":"ETH/USD:USD","qty":.02,"entry":1700.,"side":"buy"}
        self.stop={"symbol":"ETH/USD:USD","remaining_qty":.02,"stop_price":1632.,
                   "side":"sell","trigger":"mark","order_id":"mock-ack",
                   "status":"open","type":"stop-market","reduce_only":True}
    def test_stop_ack_rejects_missing_partial_wrong_side_non_reduceonly(self):
        self.assertTrue(check_ack(self.pos,self.stop))
        for k,bad in (("order_id",None),("remaining_qty",.01),("trigger","last"),
                      ("reduce_only",False),("status","rejected"),("type","limit"),
                      ("side","buy"),("stop_price",1750.)):
            x=dict(self.stop,**{k:bad})
            self.assertFalse(check_ack(self.pos,x),k)
            self.assertEqual(response(self.pos,x),"EMERGENCY_EXIT_AND_HALT")
    def test_api_outage_fails_closed(self):
        self.assertEqual(response(self.pos,self.stop,False),"HALT_UNVERIFIED_OPEN_POSITION")
        self.assertEqual(response(self.pos,None),"EMERGENCY_EXIT_AND_HALT")
    def test_dryrun_preflight_rejects_all_real_trading(self):
        cfg=json.loads((Path(__file__).resolve().parents[1]/"config.alwayson.dry.json").read_text())
        self.assertTrue(validate(cfg))
        for changes in ({"dry_run":False},{"dry_run_wallet":1000},
                        {"force_entry_enable":True},{"api_server":{"enabled":True}},
                        {"exchange":dict(cfg["exchange"],key="SECRET")}):
            with self.assertRaises(RuntimeError):validate(dict(cfg,**changes))
        for v in ({"stoploss_on_exchange":False},{"stoploss_price_type":"last"},
                  {"emergency_exit":"limit"}):
            with self.assertRaises(RuntimeError):
                validate(dict(cfg,order_types=dict(cfg["order_types"],**v)))
    def test_stale_heartbeat_creates_sticky_manual_pause(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/"freqtrade.log").write_text("healthy heartbeat")
            now=time.time()
            self.assertFalse(check(p,now=now,age_limit=100)["paused"])
            self.assertTrue(check(p,now=now+150,age_limit=100)["paused"])
            self.assertTrue(check(p,now=now,age_limit=100)["paused"])
    def test_emergency_stop_log_creates_manual_pause(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/"freqtrade.log").write_text("emergency_exit initiated")
            self.assertTrue(check(p,age_limit=100)["paused"])
            self.assertIn("DO NOT AUTOMATICALLY CLEAR",(p/"PAUSE_ENTRIES").read_text())

if __name__=="__main__":unittest.main()
