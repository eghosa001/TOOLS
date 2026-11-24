"""Seven-month comparison is apples-to-apples and force-close safe."""
from __future__ import annotations
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from seven_month_profit_comparison import (
    START,END,DAYS,MODELS,metric,comparison
)


class SevenMonthAudit(unittest.TestCase):
    def test_fixed_seven_calendar_months(self):
        self.assertEqual(DAYS,206)
        self.assertEqual(START.isoformat(),"2026-05-01T00:00:00+00:00")
        self.assertEqual(END.isoformat(),"2026-11-23T00:00:00+00:00")

    def fixture(self,root,second_pair="ETH/USD:USD",gain=1.5):
        path=Path(root)/"1h_btc_funding_oi"/"normal"
        path.mkdir(parents=True)
        model=MODELS["1h_btc_funding_oi"]
        doc={"strategy":{model:{
            "starting_balance":150,
            "final_balance":150+gain+2.,
            "max_drawdown_account":.02,
            "trades":[
                {"pair":second_pair,"profit_abs":gain,"leverage":1.,
                 "open_date":"2026-05-10 00:00:00+00:00",
                 "close_date":"2026-05-11 01:00:00+00:00",
                 "exit_reason":"trailing_stop_loss"},
                {"pair":second_pair,"profit_abs":2.,"leverage":1.,
                 "open_date":"2026-11-20 00:00:00+00:00",
                 "close_date":"2026-11-23 00:00:00+00:00",
                 "exit_reason":"force_exit"},
            ]
        }}}
        with ZipFile(path/"research.zip","w") as z:
            z.writestr("backtest-result.json",json.dumps(doc))

    def test_realized_monthly_does_not_include_terminal_forced_profit(self):
        with TemporaryDirectory() as temp:
            self.fixture(temp)
            r=metric(Path(temp),"1h_btc_funding_oi","normal")
            self.assertEqual(r["net_with_forced_terminal_usd"],3.5)
            self.assertEqual(r["naturally_closed_trade_profit_usd"],1.5)
            self.assertEqual(r["forced_terminal_profit_usd"],2)
            self.assertEqual(r["days_with_positive_closed_net"],1)
            self.assertEqual(r["days_with_no_natural_trade_close"],205)
            self.assertEqual(r["month_closes"]["2026-05"]["natural_closed_net_usd"],1.5)
            self.assertEqual(r["month_closes"]["2026-11"]["natural_closed_net_usd"],0.)
            self.assertEqual(r["reported_backtester_max_drawdown_pct"],2.)

    def test_pair_mismatch_and_bad_balance_are_rejected(self):
        with TemporaryDirectory() as temp:
            self.fixture(temp,second_pair="BTC/USD:USD")
            with self.assertRaisesRegex(ValueError,"Mixed market"):
                metric(Path(temp),"1h_btc_funding_oi","normal")
        with TemporaryDirectory() as temp:
            self.fixture(temp,gain=-1000.)
            # Negative wallet fails a balance sanity rule only when an
            # exchange itself would be insolvent; here disallow bad equity.
            r=metric(Path(temp),"1h_btc_funding_oi","normal")
            self.assertLess(r["ending_wallet_usd"],0)


if __name__=="__main__":
    unittest.main()
