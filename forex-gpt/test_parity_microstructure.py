#!/usr/bin/env python3
"""Safety and microstructure invariants for parity quote replay."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import parity_microstructure_backtest as m

class ParityResearchTests(unittest.TestCase):
 def synthetic_quotes(self,t=100000):
  return {'eurusd':[t,1.1010,1.1009,.1,.1],
          'eurgbp':[t,.8501,.8500,.1,.1],
          'gbpusd':[t,1.2960,1.2959,.1,.1]}
 def test_implied_bid_ask_cross_rate(self):
  q=self.synthetic_quotes()
  p=m.triangle(q)
  self.assertAlmostEqual(p['buy_gap'],(q['eurusd'][2]/q['eurgbp'][1]-q['gbpusd'][1])/.0001)
  self.assertAlmostEqual(p['sell_gap'],(q['gbpusd'][2]-q['eurusd'][1]/q['eurgbp'][2])/.0001)
  self.assertLess(p['synthetic_spread'],10)
 def test_last_known_quote_only(self):
  x=[[10000,1.12,1.11,0,0],[12000,1.13,1.12,0,0]]
  self.assertEqual(m.at(x,[10000,12000],11000)[0],10000)
  self.assertIsNone(m.at(x,[10000,12000],9000))
  self.assertIsNone(m.at(x,[10000,12000],11900,1000))
 def test_cross_pair_stale_fail_closed(self):
  q=self.synthetic_quotes(10000)
  rows={p:[v] for p,v in q.items()}
  times={p:[10000] for p in q}
  self.assertIsNotNone(m.quotes_at(rows,times,11000))
  self.assertIsNone(m.quotes_at(rows,times,12001))
 def test_no_zero_cost_hypothetical(self):
  entry=100000
  rows={'gbpusd':[[entry,1.2501,1.2500,.1,.1],
      [entry+12000,1.2501,1.2500,.1,.1]]}
  r=m.exit_price(rows,0,1,10)
  self.assertAlmostEqual(r['pnl'],-.18,places=3)
 def test_no_automatic_trading_without_validation(self):
  dummy={'day':'2026-06-03','year':2026,'window':0,'t':100000,
    'entry':101000,'regime':'normal','f':{'residual':5,'gbp_age':0,'eurusd_age':0,'eurgbp_age':0},
    'future':{10:{1:{'pnl':2,'exit':110000,'reason':'TARGET'},-1:None}}}
  r=m.replay([dummy],lambda x:None)
  self.assertEqual(r['trades'],0)
  self.assertEqual(r['net_usd'],0.)
 def test_frozen_sample_counts_and_side_costs(self):
  self.assertEqual(m.HORIZONS,(10,30,120))
  self.assertGreater(m.COMMISSION,0.)
  self.assertGreater(m.SLIPPAGE_PIPS,0.)
  self.assertEqual(m.SIZE_GBP,1000)
if __name__=='__main__':unittest.main()
