"""More ETH 1h trade entries must be causal, directionally safe and count-aware."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from one_hour_flow_signals import flow_features,soft_btc_regime,entry_masks
from one_hour_more_signals_report import MODELS,WINDOWS


def market(n=900,start="2026-01-01",freq="1h"):
    date=pd.date_range(start,periods=n,freq=freq,tz="UTC")
    idx=np.arange(n)
    trend=1700*np.exp(.00003*idx+.015*np.sin(idx/13))
    return pd.DataFrame({
        "date":date,"open":trend*1.0001,"high":trend*1.0025,
        "low":trend*.9975,"close":trend,
        "volume":100+30*(1+np.sin(idx/6)),
        "atr14":np.full(n,12.),
        "buy_votes":np.full(n,7,dtype=int),
        "warm":np.arange(n)>400,
        "crash_block":False,
    })


class NewIndependentSignals(unittest.TestCase):
    def test_increasing_unfiltered_vote_opportunities(self):
        f=pd.DataFrame({"buy_votes":[4,5,6,7,8,9],
                        "flow_long_score":[1,1,3,4,1,1],
                        "flow_short_score":[3,1,1,1,1,1],
                        "flow_breakout_long":[False,False,True,False,False,False],
                        "flow_breakout_short":[False,False,False,False,False,False],
                        "flow_data_ready":[True]*6})
        a,_=entry_masks(f,"vote",8)
        b,_=entry_masks(f,"vote",7)
        c,_=entry_masks(f,"vote",6)
        self.assertEqual(int(a.sum()),2)
        self.assertEqual(int(b.sum()),3)
        self.assertEqual(int(c.sum()),4)
        x,_=entry_masks(f,"hybrid",7)
        self.assertEqual(int(x.sum()),4)
        x,_=entry_masks(f,"break_hybrid",7)
        self.assertEqual(int(x.sum()),4)

    def test_new_flow_signals_never_reference_future(self):
        frame=market()
        a=flow_features(frame.iloc[:700].copy())
        extra=market(1000)
        b=flow_features(extra)
        for col in (
            "flow_long_score","flow_short_score",
            "flow_breakout_long","flow_breakout_short","flow_data_ready",
        ):
            pd.testing.assert_series_equal(
                a[col],b[col].iloc[:700].reset_index(drop=True),
                check_names=True)
        self.assertEqual(len(a),700)

    def test_soft_btc_macro_unseen_data_does_not_change_old_votes(self):
        eth=market(n=650,start="2026-05-01")
        btc=market(n=850,start="2025-10-01",freq="12h")
        initial=soft_btc_regime(eth,btc)
        altered=btc.copy()
        altered.loc[altered["date"]>pd.Timestamp("2026-05-21T00:00:00Z"),"close"]*=.75
        new=soft_btc_regime(eth,altered)
        subset=eth["date"]<pd.Timestamp("2026-05-20T00:00:00Z")
        pd.testing.assert_frame_equal(initial[subset],new[subset])

    def test_soft_btc_blocks_stale_market(self):
        eth=market(n=600,start="2026-11-01")
        btc=market(n=600,start="2025-01-01",freq="12h")
        r=soft_btc_regime(eth,btc)
        self.assertFalse(r["allow_long"].any())
        self.assertFalse(r["allow_short"].any())

    def test_corrupt_data_rejected_and_only_registered_models(self):
        data=market()
        bad=data.copy()
        bad.loc[450,"volume"]=-1
        with self.assertRaises(ValueError):
            flow_features(bad)
        bad=data.copy()
        bad.loc[399,"close"]=np.nan
        with self.assertRaises(ValueError):
            flow_features(bad)
        for threshold in (5,9,10):
            with self.assertRaises(ValueError):
                entry_masks(pd.DataFrame({"buy_votes":[8]}),"vote",threshold)
        self.assertEqual(len(MODELS),12)
        self.assertEqual(set(WINDOWS),{"early","later","full"})


if __name__=="__main__":
    unittest.main()
