"""Offline guards for five-coin experiment: no data API needed."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cross_asset_oi_fetch import CONTRACTS
from cross_asset_report import read_one,BASE


class CrossAssetSafety(unittest.TestCase):
    def test_contract_identifiers_are_individual_verified_perpetuals(self):
        self.assertEqual(len(CONTRACTS),5)
        self.assertEqual(CONTRACTS["BTC/USD:USD"],"PF_XBTUSD")
        self.assertEqual(CONTRACTS["SOL/USD:USD"],"PF_SOLUSD")
        self.assertEqual(CONTRACTS["XRP/USD:USD"],"PF_XRPUSD")
        self.assertEqual(len(set(CONTRACTS.values())),5)

    def test_trade_reconciliation_and_coin_isolation(self):
        with TemporaryDirectory() as d:
            folder=Path(d)/"BTC"/"full"/BASE
            folder.mkdir(parents=True)
            data={"strategy":{BASE:{
                "starting_balance":150.0,
                "final_balance":150.8,
                "max_drawdown_account":0.01,
                "trades":[{
                    "pair":"BTC/USD:USD",
                    "leverage":1.,
                    "profit_abs":0.8,
                    "close_date":"2026-06-04 00:00:00+00:00",
                    "exit_reason":"exit_signal",
                }]}}}
            with ZipFile(folder/"test.zip","w") as z:
                z.writestr("backtest-result.json",json.dumps(data))
            result=read_one(Path(d),"BTC","full",BASE)
            self.assertEqual(result["net_usd"],0.8)
            self.assertEqual(result["wins"],1)
            self.assertEqual(result["max_drawdown_pct"],1)
            with self.assertRaises(RuntimeError):
                read_one(Path(d),"SOL","full",BASE)
            data["strategy"][BASE]["trades"][0]["pair"]="ETH/USD:USD"
            with ZipFile(folder/"test.zip","w") as z:
                z.writestr("backtest-result.json",json.dumps(data))
            with self.assertRaises(RuntimeError):
                read_one(Path(d),"BTC","full",BASE)

    def test_no_account_leverage_or_cost_shortcuts(self):
        with TemporaryDirectory() as d:
            folder=Path(d)/"BTC"/"train"/BASE
            folder.mkdir(parents=True)
            doc={"strategy":{BASE:{
                "starting_balance":150.0,"final_balance":150.0,
                "max_drawdown_account":0.,
                "trades":[{"pair":"BTC/USD:USD","leverage":3.0,
                           "profit_abs":0.,"close_date":"2026-04-04 00:00:00+00:00"}]}}}
            with ZipFile(folder/"test.zip","w") as z:
                z.writestr("result.json",json.dumps(doc))
            with self.assertRaises(RuntimeError):
                read_one(Path(d),"BTC","train",BASE)


if __name__=="__main__":
    unittest.main()
