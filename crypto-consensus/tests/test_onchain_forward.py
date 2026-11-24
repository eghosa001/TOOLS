"""Deterministic onchain forward safeguards (no external calls)."""
import copy
import time
import unittest
from datetime import datetime,timezone
from onchain_forward import (blank,observation,security_ok,candidate,parse_pools,
                             summarize,mark_position,utc)

class OnchainTests(unittest.TestCase):
    def setUp(self):
        self.now=1795500000.0
        self.row={"pool":"3"*44,"mint":"4"*44,"quote":"So11111111111111111111111111111111111111112",
                  "created":self.now-1200,"price":1.,"liquidity":100000.,
                  "volume5":20000.,"buys5":60,"sells5":20,"at":self.now}
    def safe(self,mint):
        return True,"passed"

    def detail(self,pool,now):
        return {**self.row,"at":now,"created":self.now-1200}

    def test_security_fails_closed_and_positive_fields(self):
        self.assertFalse(security_ok({})[0])
        body={x:{"status":"0"} for x in ("mintable","freezable","closable","balance_mutable_authority")}
        body.update({"non_transferable":"0","default_account_state":"1",
                     "holders":[{"percent":.12},{"percent":.05}]})
        self.assertTrue(security_ok(body)[0])
        body["mintable"]={"status":"1"}
        self.assertFalse(security_ok(body)[0])
        body["mintable"]={"status":"0"}
        body["holders"]=[{"percent":.7}]
        self.assertFalse(security_ok(body)[0])

    def test_observe_all_including_bad_unqualified_and_missing(self):
        s=blank()
        bad={**self.row,"pool":"5"*44,"volume5":2.,"liquidity":3.,"price":None}
        observation(s,[self.row,bad],self.now,self.safe,self.detail)
        self.assertEqual(len(s["pools"]),2)
        self.assertIn(bad["pool"],s["pools"])
        self.assertEqual(s["pools"][bad["pool"]]["first_price"],None)
        self.assertEqual(s["paper"]["pending"]["pool"],self.row["pool"])
        self.assertIsNone(s["paper"]["position"])

    def test_entry_only_at_subsequent_observation_and_no_order(self):
        s=blank()
        observation(s,[self.row],self.now,self.safe,self.detail)
        self.assertIsNone(s["paper"]["position"])
        observation(s,[{**self.row,"at":self.now+1000,"price":1.05}],self.now+1000,self.safe,self.detail)
        self.assertIsNotNone(s["paper"]["position"])
        self.assertEqual(s["paper"]["wallet"],135.)
        self.assertAlmostEqual(s["paper"]["position"]["entry"],1.05*1.015)

    def test_rug_missing_observations_count_full_loss(self):
        s=blank()
        observation(s,[self.row],self.now,self.safe,self.detail)
        observation(s,[self.row],self.now+1000,self.safe,self.detail)
        observation(s,[],self.now+2000,self.safe,lambda *args:None)
        self.assertIsNotNone(s["paper"]["position"])
        observation(s,[],self.now+3000,self.safe,lambda *args:None)
        self.assertIsNone(s["paper"]["position"])
        self.assertEqual(s["paper"]["closed_trades"][0]["reason"],
                         "twice_unpriced_pessimistic_writeoff")
        self.assertLess(s["paper"]["wallet"],150.)

    def test_cannot_backfill_timestamp(self):
        s=blank()
        observation(s,[self.row],self.now,self.safe,self.detail)
        with self.assertRaises(RuntimeError):
            observation(s,[self.row],self.now-60,self.safe,self.detail)

    def test_security_unsafe_blocks_entry(self):
        s=blank()
        observation(s,[self.row],self.now,lambda mint:(False,"bad_contract"),self.detail)
        self.assertIsNone(s["paper"].get("pending"))
        self.assertEqual(s["pools"][self.row["pool"]]["security_status"],"bad_contract")

    def test_parse_no_fabricated_prices(self):
        base="4"*44
        pool="3"*44
        quote="So11111111111111111111111111111111111111112"
        payload={
            "data":[{
                "id":"solana_"+pool,
                "attributes":{
                    "address":pool,
                    "pool_created_at":"2026-11-24T09:00:00Z",
                    "reserve_in_usd":"80000",
                    "base_token_price_usd":"1.23",
                    "volume_usd":{"m5":"19000"},
                    "transactions":{"m5":{"buys":31,"sells":18}}
                },
                "relationships":{
                    "base_token":{"data":{"id":"solana_"+base}},
                    "quote_token":{"data":{"id":"solana_"+quote}}
                }
            }]
        }
        entries=parse_pools(payload,1795530000)
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]["liquidity"],80000.)
        self.assertEqual(entries[0]["mint"],base)
        self.assertEqual(entries[0]["quote"],quote)

if __name__=="__main__":
    unittest.main()
