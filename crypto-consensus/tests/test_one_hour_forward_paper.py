"""Offline guard tests: no exchange network, no credentials, no real orders."""
from __future__ import annotations

import copy
from datetime import datetime,timezone
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from one_hour_forward_paper import (
    initial_state,validate_market,book_quality,volume_weighted_book,
    size_for_risk,entry_fill_price,mark_exit_price,close_position,
    apply_observation,HOUR,COMMISSION,ADVERSE_SLIPPAGE,
)
from risk_guards import ensure_risk_state,can_enter


MARKET={"id":"PF_ETHUSD","active":True,"linear":True,
        "contractSize":1.0,"precision":{"amount":.001}}
WHEN=int(datetime(2026,11,24,10,29,tzinfo=timezone.utc).timestamp()*1000)


def book(now_ms=WHEN,spread=.1):
    return {"timestamp":now_ms,
            "bids":[[1700.,100],[1699.9,100]],
            "asks":[[1700.+spread,100],[1700.+spread+.1,100]]}


def snap(now_ms=WHEN):
    # 410 completed hourly mark bars; signal generator mocked but the
    # stop observation, freshness, risk and fill logic is REAL code.
    start=now_ms-29*60000-410*HOUR
    marks=[[start+i*HOUR,1700,1720,1680,1700,0] for i in range(410)]
    return {"now_ms":now_ms,"market":MARKET,"book":book(now_ms),
            "hourly":[],"btc12":[],"oi_doc":{},"funding":[],
            "mark_hourly":marks}


def signal(now_ms=WHEN,direction=1,crash=False,btc=True,oi=True):
    bar_start=now_ms-29*60000-HOUR
    return {
        "bar_start_ms":bar_start,
        "bar_end_ms":bar_start+HOUR,
        "votes":9 if direction==1 else 1 if direction==-1 else 5,
        "direction":direction,"atr":35.0,
        "btc_allow":btc,"oi_allow":oi,"crash":crash,
        "bar_close":1700.,
        "hourly_candles":[],
        "btc_flags":{"allow_long":btc,"allow_short":btc},
        "oi_flags":{"allow_long":oi,"allow_short":oi},
    }


class OneHourForwardTests(unittest.TestCase):
    def test_no_leverage_no_upsizing_and_decent_cost_allowance(self):
        q=size_for_risk(150,1700,35,MARKET,book())
        self.assertGreaterEqual(q,0)
        self.assertLessEqual(q*1700,150)
        worst=max(2.5*35,.04*1700)+1700*(2*(COMMISSION+ADVERSE_SLIPPAGE)+.1/1700)
        self.assertLessEqual(q*worst,1.5+1e-8)
        self.assertEqual(size_for_risk(.1,1700,35,MARKET,book()),0.)
        with self.assertRaises(ValueError):
            validate_market({**MARKET,"id":"WRONG"})

    def test_actual_orderbook_vwap_and_spread_rejection(self):
        b=book()
        self.assertAlmostEqual(volume_weighted_book(b,1,1),1700.1)
        self.assertAlmostEqual(volume_weighted_book(b,-1,1),1700.0)
        self.assertGreater(entry_fill_price(b,1,1),1700.1)
        self.assertLess(mark_exit_price(b,1,1),1700.)
        with self.assertRaises(ValueError):
            volume_weighted_book(b,1,250)
        with self.assertRaises(ValueError):
            book_quality(book(spread=9),WHEN)
        with self.assertRaises(ValueError):
            book_quality(book(now_ms=WHEN-300001),WHEN)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_forward_entry_only_on_actual_next_observation(self,mock):
        mock.return_value=signal()
        state=initial_state()
        first=apply_observation(state,snap())
        self.assertEqual(first["observations"],1)
        self.assertIsNotNone(first["position"])
        self.assertEqual(first["position"]["entered_ms"],WHEN)
        self.assertTrue(first["position"]["qty"]*1700<=150)
        self.assertEqual(first["latest_candidate_signal"]["direction"],"long")
        with self.assertRaises(ValueError):
            apply_observation(first,snap())
        self.assertEqual(len(first["trades"]),0)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_btc_and_oi_veto_individually_reject(self,m):
        for kw,key in (({"btc":False},"btc"),({"oi":False},"funding_oi"),
                       ({"crash":True},"crash")):
            m.return_value=signal(**kw)
            result=apply_observation(initial_state(),snap())
            self.assertIsNone(result["position"])
            self.assertEqual(result["signal_rejections"][key],1)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_observed_daily_weekly_peak_and_gap_locks(self,m):
        m.return_value=signal()
        for amount,expected in ((146.9,"daily"),(143.9,"weekly"),(140.5,"peak")):
            state=initial_state()
            ensure_risk_state(state,WHEN-HOUR,150.)
            state["balance"]=amount
            result=apply_observation(state,snap())
            self.assertIsNone(result["position"])
            self.assertTrue(result["risk_events"])
            self.assertFalse(can_enter(result,WHEN))
            self.assertTrue(result["signal_rejections"]["risk"]>=1)
            if expected=="peak":self.assertTrue(result["permanent_risk_lock"])
        # Missing more than 2.5h must not make a historical entry.
        state=initial_state()
        state["last_checked_ms"]=WHEN-3*HOUR
        missed=apply_observation(state,snap())
        self.assertEqual(missed["missed_checks"],1)
        self.assertIsNone(missed["position"])
        self.assertGreaterEqual(missed["cooldown_until_ms"],WHEN+24*HOUR)

    def test_loss_pause_and_terminal_charges(self):
        state=initial_state()
        state["position"]={
            "side":1,"qty":.02,"entry":1700,"entered_ms":WHEN-4*HOUR,
            "entered_utc":"2026-11-24T06:29:00Z","stop":1600,
            "opening_wallet":150.,
            "entry_fee":.017,"funding_cost":0.,
        }
        state["balance"]=149.983
        close_position(state,1580,WHEN,"offline_stop_test",modelled_stop=True)
        self.assertIsNone(state["position"])
        self.assertEqual(len(state["trades"]),1)
        self.assertLess(state["trades"][0]["net_usd"],0)
        self.assertGreaterEqual(state["cooldown_until_ms"],WHEN+24*HOUR)
        self.assertGreater(state["total_funding_buffer_usd"],0)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_frozen_state_without_completion_cannot_open_trade(self,m):
        m.return_value=signal()
        state=initial_state()
        bad=snap()
        bad["mark_hourly"]=bad["mark_hourly"][:-30]
        with self.assertRaises(ValueError):
            apply_observation(state,bad)
        self.assertIsNone(state["position"])
        self.assertEqual(state["observations"],0)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_utc_midnight_daily_loss_cannot_reset(self,mock):
        start=int(datetime(2026,11,24,23,29,tzinfo=timezone.utc).timestamp()*1000)
        now=start+HOUR
        mock.return_value=signal(now)
        state=initial_state()
        ensure_risk_state(state,start,150.)
        state["last_checked_ms"]=start
        state["equity_usd"]=150.
        state["balance"]=146.8
        new=apply_observation(state,snap(now))
        self.assertTrue(new["daily_pause_until_ms"]>now)
        self.assertFalse(can_enter(new,now))
        self.assertEqual(new["risk_day_start"],150.)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_utc_monday_week_boundary_preserves_previous_equity(self,mock):
        start=int(datetime(2026,11,22,23,29,tzinfo=timezone.utc).timestamp()*1000)
        now=start+HOUR
        mock.return_value=signal(now)
        state=initial_state()
        ensure_risk_state(state,start,150.)
        state["last_checked_ms"]=start
        state["equity_usd"]=150.
        state["balance"]=143.8
        new=apply_observation(state,snap(now))
        self.assertTrue(new["weekly_pause_until_ms"]>now)
        self.assertEqual(new["risk_week_start"],150.)

    @patch("one_hour_forward_paper.candidate_signal")
    def test_missed_hour_preserves_longer_24h_suspension_after_forced_close(self,mock):
        mock.return_value=signal()
        state=initial_state()
        state["last_checked_ms"]=WHEN-3*HOUR
        state["equity_usd"]=150.
        ensure_risk_state(state,WHEN-3*HOUR,150.)
        state["balance"]=149.99
        state["position"]={
            "side":1,"qty":.02,"entry":1700,"entered_ms":WHEN-6*HOUR,
            "entered_utc":"2026-11-24T04:29:00Z",
            "stop":1600.,"opening_wallet":150.,"entry_fee":.01,
            "funding_cost":0.,
        }
        stopped=apply_observation(state,snap())
        self.assertEqual(stopped["missed_checks"],1)
        self.assertIsNone(stopped["position"])
        self.assertGreaterEqual(stopped["cooldown_until_ms"],WHEN+24*HOUR)

    def test_module_has_no_authenticated_order_routing(self):
        text=Path(__file__).resolve().parents[1].joinpath("one_hour_forward_paper.py").read_text()
        for forbidden in (".create_order(", ".create_market_order(", ".set_leverage(",
                          "apiKey", "apiSecret", "fetch_balance("):
            self.assertNotIn(forbidden,text)


if __name__=="__main__":
    unittest.main()
