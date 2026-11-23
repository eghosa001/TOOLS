import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from report_paper import summarise,markdown
class PaperReportSafety(unittest.TestCase):
    def test_no_trade_and_equity_return(self):
        a=summarise({"balance":150.,"equity_usd":150.,"trades":[],
                     "equity_history":[{"equity_usd":150.}]})
        self.assertEqual(a["simulated_return_pct"],0.)
        self.assertEqual(a["closed_trades"],0)
        self.assertFalse(a["exchange_stop_order_verified"])
        self.assertIn("not real fills",markdown(a))
    def test_drawdown_causal(self):
        a=summarise({"balance":145.,"equity_usd":145.,"trades":[],
                     "equity_history":[{"equity_usd":150.},{"equity_usd":140.},
                                       {"equity_usd":145.}]})
        self.assertAlmostEqual(a["max_observed_drawdown_pct"],6.6667,places=3)
        self.assertAlmostEqual(a["simulated_return_pct"],-3.3333,places=3)
if __name__=="__main__":unittest.main()
