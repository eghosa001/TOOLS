"""One-hour quality gates must fail closed and never use later observations."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from one_hour_quality_features import btc_macro_gate,funding_oi_gate,combine_and


def target(start="2026-04-01",n=1000):
    ts=pd.date_range(start,periods=n,freq="1h",tz="UTC")
    values=1500*np.exp(.0004*np.arange(n))
    return pd.DataFrame({"date":ts,"close":values})


def btc(start="2025-08-01",n=650):
    ts=pd.date_range(start,periods=n,freq="12h",tz="UTC")
    values=50000*np.exp(.0004*np.arange(n)+.02*np.sin(np.arange(n)/9))
    return pd.DataFrame({"date":ts,"close":values})


def derivatives():
    ts=pd.date_range("2026-01-01",periods=3500,freq="1h",tz="UTC")
    f=pd.DataFrame({"date":ts,
                    "funding_rate":(.00001+np.sin(np.arange(len(ts))/20)*.00001)})
    ot=pd.date_range("2025-12-25T12:00:00Z",periods=1000,freq="4h")
    doc={"errors":[],"result":{
        "timestamp":[int(x.timestamp()) for x in ot],
        "data":[["1","2","1",str(500000+10*i)] for i in range(len(ot))],
        "more":False,
    }}
    return f,doc


class OneHourGateTests(unittest.TestCase):
    def test_btc_past_predictions_immune_to_future_changes(self):
        a=target("2026-04-01",650)
        b=btc()
        original=btc_macro_gate(a,b)
        changed=b.copy()
        changed.loc[changed["date"] >= pd.Timestamp("2026-05-20",tz="UTC"),"close"]*=.1
        altered=btc_macro_gate(a,changed)
        selection=a["date"]<pd.Timestamp("2026-05-19",tz="UTC")
        self.assertTrue(original[selection].equals(altered[selection]))
        self.assertEqual(len(original),len(a))

    def test_btc_feed_stale_or_missing_rejects_signal(self):
        a=target("2026-10-01",500)
        out=btc_macro_gate(a,btc())
        self.assertFalse(out["allow_long"].any())
        self.assertFalse(out["allow_short"].any())

    def test_oi_and_funding_need_real_historical_data(self):
        data=target("2026-04-01",650)
        f,oi=derivatives()
        result=funding_oi_gate(data,f,oi)
        self.assertEqual(len(result),len(data))
        bad=f.copy().rename(columns={"funding_rate":"fake_funding"})
        with self.assertRaises(ValueError):
            funding_oi_gate(data,bad,oi)
        oi2={"errors":[],"result":{
            "timestamp":oi["result"]["timestamp"][1:],
            "data":oi["result"]["data"]}}
        with self.assertRaises(ValueError):
            funding_oi_gate(data,f,oi2)

    def test_future_oi_amendment_cannot_change_past_signals(self):
        data=target("2026-02-01",400)
        f,oi=derivatives()
        initial=funding_oi_gate(data,f,oi)
        later=json_clone(oi)
        # Published no earlier than April; February decisions are immutable.
        for i,s in enumerate(later["result"]["timestamp"]):
            if s>=pd.Timestamp("2026-04-01",tz="UTC").timestamp():
                later["result"]["data"][i][3]=str(999999+i*10)
        changed=funding_oi_gate(data,f,later)
        self.assertTrue(initial.equals(changed))

    def test_combination_veto_never_adds_entries(self):
        a=pd.DataFrame({"allow_long":[True,False,True],
                        "allow_short":[False,True,True]})
        b=pd.DataFrame({"allow_long":[False,True,True],
                        "allow_short":[True,False,True]})
        out=combine_and(a,b)
        self.assertEqual(out["allow_long"].tolist(),[False,False,True])
        self.assertEqual(out["allow_short"].tolist(),[False,False,True])


def json_clone(obj):
    import json
    return json.loads(json.dumps(obj))


if __name__=="__main__":
    unittest.main()
