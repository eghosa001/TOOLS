#!/usr/bin/env python3
"""Fast deterministic offline tests of tick economic-news and causal gates."""
import datetime as dt
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import tick_paper_replay as fx

def ms(t):
    return fx.to_utc_ms(t)

class TickSafetyTests(unittest.TestCase):
    def setUp(self):
        self.day='2026-11-23'
        self.cal={
            'status':'verified','source':'https://nfs.faireconomy.media/ff_calendar_thisweek.json',
            'fetched_utc':'2026-11-23T10:00:00+00:00',
            'events':[{'utc':'2026-11-23T08:15:00Z','country':'GBP','impact':'High','title':'test'}]}
    def test_high_news_filter_five_minute_before(self):
        self.assertTrue(fx.is_news_blackout(self.cal,self.day,ms('2026-11-23T08:10:00Z')).startswith('NEWS_GBP_High'))
    def test_news_after_past_window(self):
        self.assertEqual('',fx.is_news_blackout(self.cal,self.day,ms('2026-11-23T08:50:00Z')))
    def test_stale_calendar_fails_closed(self):
        self.cal['fetched_utc']='2026-11-09T09:00:00+00:00'
        self.assertEqual(fx.source_valid(self.cal,self.day)[0],False)
    def test_empty_calendar_fails_closed(self):
        self.cal['events']=[]
        self.assertFalse(fx.source_valid(self.cal,self.day)[0])
    def test_holiday_blocks_whole_day(self):
        self.cal['events']=[{'utc':'2026-11-23T09:00:00Z','country':'USD','impact':'Holiday','title':'test'}]
        self.assertEqual(fx.is_news_blackout(self.cal,self.day,ms('2026-11-23T07:00:00Z')),'HOLIDAY_USD')
    def test_quote_snapshot_uses_only_past(self):
        base=ms('2026-11-23T07:50:00Z')
        past=[[base-1200,1.2602,1.2600,1.,1.],[base-500,1.2604,1.2602,1.,1.]]
        future=[base+600,1.2900,1.2800,1.,1.]
        self.assertEqual(fx.snapshot(past+[future],[r[0] for r in past+[future]],base,60000),past)
    def test_no_trade_without_validated_engines(self):
        self.assertEqual(fx.APPROVED_REPLACEMENTS,())
        self.assertGreater(fx.MIN_VALIDATED_REPLACEMENTS,len(fx.APPROVED_REPLACEMENTS))
    def test_invalid_quotes_rejected(self):
        day='2026-11-23'
        t=ms('2026-11-23T07:01:00Z')
        raw={'instruments':{'gbpusd':[[t,1.20,1.30,1.,1.]]*501}}
        with self.assertRaises(ValueError):
            fx.sorted_ticks(raw,'gbpusd',day)
    def test_costs_are_nonzero(self):
        self.assertGreater(fx.COMMISSION_USD,0)
        self.assertGreater(fx.EXTRA_SLIPPAGE_PIPS_ROUND_TRIP,0)
    def test_correlated_votes_do_not_count_as_independent_families(self):
        votes={name:0 for name in fx.SIGNAL_NAMES}
        for name in fx.SIGNAL_GROUPS['gbp_price']+fx.SIGNAL_GROUPS['gbp_tick_quoted_liquidity']:
            votes[name]=1
        self.assertEqual(sum(v==1 for v in votes.values()),7)
        self.assertEqual(sum(v==1 for v in fx.diverse_family_votes(votes).values()),2)
        self.assertLess(sum(v==1 for v in fx.diverse_family_votes(votes).values()),
                        fx.MIN_DIVERSE_FAMILIES)
    def test_three_families_can_agree(self):
        votes={name:0 for name in fx.SIGNAL_NAMES}
        votes['GBP_Momentum_1m']=1
        votes['Tick_Uptick_Balance']=1
        votes['EURUSD_Momentum_1m']=1
        self.assertEqual(sum(v==1 for v in fx.diverse_family_votes(votes).values()),3)
    def test_ten_signals_unique(self):
        self.assertEqual(len(fx.SIGNAL_NAMES),10)
        self.assertEqual(len(set(fx.SIGNAL_NAMES)),10)

if __name__=='__main__':unittest.main()
