"""Forward-only ETH 1h + BTC regime + REAL funding/OI paper observer.

NO real orders, NO exchange credentials, NO backfill trading, NO paid LLM use.
One discretionary observation per completed 1h candle; Github schedule can
delay/miss hours, so positions/risk checks are *not continuously observed*.
This observer is NOT the original 12h Freqtrade strategy or a live broker stop.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone,timedelta
import hashlib
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen

import ccxt
import numpy as np
import pandas as pd

from core import build_indicators,STARTUP_CANDLES
from intraday_research_utils import time_consistent_crash_mask
from one_hour_quality_features import btc_macro_gate,funding_oi_gate
from quality_candidate_features import parse_official_oi
from risk_guards import inspect_account,can_enter,TRADE_RISK_FRACTION

PAIR="ETH/USD:USD"
CONTRACT_ID="PF_ETHUSD"
HOUR=3600000
DAY=24*HOUR
START_BALANCE=150.0
STATE_VERSION=1
COMMISSION=.0005
ADVERSE_SLIPPAGE=.001   # hypothetical *additional* adverse fill, each side
MAX_REL_SPREAD=.002
MAX_BOOK_AGE_MS=180000
CLOSE_AGE_MIN_MS=5*60000
CLOSE_AGE_MAX_MS=55*60000
MAX_OBSERVATION_GAP_MS=150*60000
MIN_POSITION_CONTRACTS=.001
CONTRACT_STEP=.001
POSITION_RISK=.01
HOLDING_FUNDING_BUFFER_RATE=.00005  # conservative charge per uncovered hour
RUN_RESEARCH_ONLY=True


def utc(ms:int)->str:
    return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()


def ms_from(ts:str)->int:
    return int(datetime.fromisoformat(ts.replace("Z","+00:00")).timestamp()*1000)


def initial_state():
    return {
        "version":STATE_VERSION,
        "mode":"forward_only_keyless_one_hour_eth_both_filters",
        "balance":START_BALANCE,
        "equity_usd":START_BALANCE,
        "position":None,
        "trades":[],
        "last_checked_ms":None,
        "last_signal_ms":None,
        "last_funding_paid_ts":None,
        "cooldown_until_ms":0,
        "observations":0,
        "missed_checks":0,
        "feed_failures":0,
        "signal_rejections":{"consensus":0,"btc":0,"funding_oi":0,"crash":0,
                             "risk":0,"book":0,"size":0,"stale":0},
        "total_fees_usd":0.0,
        "total_funding_cost_usd":0.0,
        "total_funding_buffer_usd":0.0,
        "events":[],
        "equity_history":[],
        "starting_usd":START_BALANCE,
        "real_orders_enabled":False,
    }


def validate_market(market):
    if market.get("id")!=CONTRACT_ID or market.get("active") is False:
        raise ValueError("Unexpected or inactive perpetual futures market")
    if market.get("linear") is not True or float(market.get("contractSize") or 0)!=1:
        raise ValueError("Unexpected futures contract sizing")
    if float(market.get("precision",{}).get("amount") or 0)!=CONTRACT_STEP:
        raise ValueError("Unexpected ETH perpetual amount step; never round up")


def published(rows, period_ms:int, observed_ms:int, minimum:int=0):
    closed=[x for x in rows if int(x[0])+period_ms<=observed_ms]
    if len(closed)<minimum:
        raise ValueError("Too few genuinely completed exchange candles")
    t=[int(x[0]) for x in closed]
    if t!=sorted(set(t)) or any(b-a!=period_ms for a,b in zip(t,t[1:])):
        raise ValueError("Missing or repeated historical market candles")
    for row in closed:
        if len(row)<6 or not all(np.isfinite(float(x)) for x in row[1:6]):
            raise ValueError("Invalid exchange market price history")
    return closed


def series(rows):
    return pd.DataFrame([{
        "date":pd.Timestamp(int(r[0]),unit="ms",tz="UTC"),
        "open":float(r[1]),"high":float(r[2]),"low":float(r[3]),
        "close":float(r[4]),"volume":float(r[5]),
    } for r in rows])


def book_quality(book:dict,now_ms:int):
    stamp=book.get("timestamp")
    if stamp is None or abs(int(stamp)-now_ms)>MAX_BOOK_AGE_MS:
        raise ValueError("Bid/ask order book is stale or timestamp missing")
    bids=book.get("bids",[])
    asks=book.get("asks",[])
    if not bids or not asks:
        raise ValueError("No executable bid/ask research quotes")
    bid=float(bids[0][0])
    ask=float(asks[0][0])
    if not 0<bid<ask or (ask-bid)/((ask+bid)/2)>MAX_REL_SPREAD:
        raise ValueError("Invalid or too-wide public spread")
    return bid,ask


def volume_weighted_book(book,side:int,qty:float):
    """side=1 means buy from asks, -1 means sell into bids. Do not invent depth."""
    if side not in (-1,1) or qty<=0:
        raise ValueError("Invalid simulated book fill direction")
    levels=book["asks"] if side==1 else book["bids"]
    left=qty
    cost=0.
    for raw_price,raw_size,*_ in levels:
        price=float(raw_price)
        amount=float(raw_size)
        if not np.isfinite(price) or not np.isfinite(amount) or price<=0 or amount<0:
            raise ValueError("Invalid displayed order-book depth")
        take=min(left,amount)
        cost+=take*price
        left-=take
        if left<=1e-9:break
    if left>1e-9:
        raise ValueError("Insufficient visible public order-book depth")
    return cost/qty


def mark_exit_price(book,side:int,qty:float):
    # Exit a long by selling, exit a short by buying. Extra adverse fill
    # assumption is independent of the displayed bid/ask depth.
    quote=volume_weighted_book(book,-side,qty)
    return quote*(1-side*ADVERSE_SLIPPAGE)


def entry_fill_price(book,side:int,qty:float):
    quote=volume_weighted_book(book,side,qty)
    return quote*(1+side*ADVERSE_SLIPPAGE)


def size_for_risk(balance:float,mid:float,atr:float,market:dict,book:dict)->float:
    validate_market(market)
    if balance<=0 or mid<=0 or atr<=0 or not math.isfinite(atr):
        return 0.
    b,a=book_quality(book,int(book["timestamp"]))
    # Model at most 1x notional. Costs, gap risk and adverse fills lower size.
    worst_stop_distance=max(2.5*atr,.04*mid)
    round_trip_cost=mid*(2*(COMMISSION+ADVERSE_SLIPPAGE)+(a-b)/mid)
    capital_risk=balance*POSITION_RISK
    max_notional=min(balance*.98,capital_risk*mid/(worst_stop_distance+round_trip_cost))
    qty=math.floor(max_notional/mid/CONTRACT_STEP+1e-10)*CONTRACT_STEP
    if qty<MIN_POSITION_CONTRACTS:
        return 0.
    if qty*mid>balance+1e-9:
        raise AssertionError("Paper leverage guard refused")
    # Book quantity check at simulated buy/sell side happens before entry.
    return round(qty,8)


def close_position(state:dict,price:float,at_ms:int,reason:str,
                   book:dict|None=None,modelled_stop:bool=False):
    pos=state["position"]
    if pos is None:
        raise RuntimeError("No paper position to close")
    if book is not None and not modelled_stop:
        fill=mark_exit_price(book,pos["side"],pos["qty"])
    else:
        # Historic candle OHLC has no archived bid/ask book: use worse open
        # or stop and explicit adverse slippage instead, not perfect fills.
        fill=float(price)*(1-pos["side"]*ADVERSE_SLIPPAGE)
    qty=pos["qty"]
    state["balance"]+=pos["side"]*qty*(fill-pos["entry"])
    fee=abs(fill*qty)*COMMISSION
    state["balance"]-=fee
    state["total_fees_usd"]+=fee
    # Charges for funding events not yet known (publication is delayed 2h).
    # This intentionally NEVER credits positive funding.
    unsettled=min(2.,max(0.,(at_ms-max(pos["entered_ms"],
                                          state.get("last_funding_paid_ts") or pos["entered_ms"]))/HOUR))
    buffer=unsettled*qty*fill*HOLDING_FUNDING_BUFFER_RATE
    state["balance"]-=buffer
    state["total_funding_buffer_usd"]+=buffer
    pnl=state["balance"]-pos["opening_wallet"]
    state["trades"].append({
        "entry_utc":pos["entered_utc"],"exit_utc":utc(at_ms),
        "direction":"long" if pos["side"]==1 else "short",
        "side":pos["side"],"qty":qty,"open_price":pos["entry"],
        "exit_price":round(fill,6),
        "net_usd":round(pnl,6),"reason":reason,
        "fees_usd":round(pos["entry_fee"]+fee,6),
        "funding_charge_usd":round(pos.get("funding_cost",0.),6),
        "funding_buffer_usd":round(buffer,6),
        "historic_stop_modelled_without_order_book":bool(modelled_stop),
    })
    state["position"]=None
    # Following any loss 24h pause, otherwise 3h after each completed trade;
    # account-level day/week/peak observed locks take precedence.
    state["cooldown_until_ms"]=max(state.get("cooldown_until_ms",0),
                                       at_ms+(24*HOUR if pnl<0 else 3*HOUR))
    state["events"].append({"time":utc(at_ms),"type":"closed","reason":reason,
                            "net_usd":round(pnl,6)})


def account_equity(state,book):
    pos=state.get("position")
    if not pos:return state["balance"]
    quote=volume_weighted_book(book,-pos["side"],pos["qty"])
    return state["balance"]+pos["side"]*pos["qty"]*(quote-pos["entry"])


def apply_funding(state,records:list,mark_rows:list,now_ms:int):
    """Only pay published event costs for an OPEN paper position; never credit.

    Last two hours at close use a separate conservative holding-cost buffer.
    Historical mark closes approximate settlement; this is not a bill.
    """
    mature=[x for x in records if int(x["timestamp"])+2*HOUR<=now_ms]
    if not mature:return
    watermark=state.get("last_funding_paid_ts")
    if watermark is None:
        # Do not apply past funding to a position opened after observation.
        watermark=state.get("position",{}).get("entered_ms",now_ms) if state.get("position") else now_ms
    mature=[x for x in mature if int(x["timestamp"])>watermark]
    mark={int(row[0])+HOUR:float(row[4]) for row in mark_rows}
    for item in mature:
        ts=int(item["timestamp"])
        position=state.get("position")
        if position is not None and ts>position["entered_ms"]:
            eligible=[t for t in mark if t<=ts]
            if not eligible or ts-max(eligible)>2*HOUR:
                raise ValueError("Historical mark close absent for funding")
            rate=float(item["fundingRate"])
            if not np.isfinite(rate):
                raise ValueError("Invalid actual published funding")
            notional=position["qty"]*mark[max(eligible)]
            # Positive funding payment costs; negative funding receipt ignored
            # deliberately to avoid profit inflation in forward paper.
            charge=max(0.,position["side"]*notional*rate)
            state["balance"]-=charge
            state["total_funding_cost_usd"]+=charge
            position["funding_cost"]=position.get("funding_cost",0.)+charge
        state["last_funding_paid_ts"]=ts


def candidate_signal(now_ms,ohlcv_hourly,ohlcv_btc,funding,oi_doc):
    one=published(ohlcv_hourly,HOUR,now_ms,STARTUP_CANDLES+5)
    twelve=published(ohlcv_btc,12*HOUR,now_ms,240)
    one_end=int(one[-1][0])+HOUR
    age=now_ms-one_end
    if not CLOSE_AGE_MIN_MS<=age<=CLOSE_AGE_MAX_MS:
        raise ValueError("Latest completed 1h candle too recent or too stale")
    target=series(one)
    btc=series(twelve)
    fr=pd.DataFrame([{"date":pd.Timestamp(int(x["timestamp"]),unit="ms",tz="UTC"),
                      "funding_rate":float(x["fundingRate"])}
                     for x in funding])
    if len(fr)<400:
        raise ValueError("Not enough actual hourly funding observations")
    if fr["date"].duplicated().any():
        raise ValueError("Funding history contains duplicates")
    oi=parse_official_oi(oi_doc)
    if int(oi["known_at"].iloc[-1].timestamp()*1000)<now_ms-24*HOUR:
        raise ValueError("Actual Kraken OI source too stale")
    btc_gate=btc_macro_gate(target,btc)
    oi_gate=funding_oi_gate(target,fr,oi_doc)
    ind=build_indicators(target)
    votes=int(ind["buy_votes"].iloc[-1])
    atr=float(ind["atr14"].iloc[-1])
    crash=bool(time_consistent_crash_mask(target,"1h").iloc[-1])
    direction=1 if votes>=8 else -1 if votes<=2 else 0
    return {
        "bar_start_ms":int(one[-1][0]),
        "bar_end_ms":one_end,
        "votes":votes,"atr":atr,"direction":direction,
        "btc_allow":bool(btc_gate["allow_long" if direction==1 else "allow_short"].iloc[-1])
                    if direction else False,
        "oi_allow":bool(oi_gate["allow_long" if direction==1 else "allow_short"].iloc[-1])
                    if direction else False,
        "btc_flags":{k:bool(btc_gate[k].iloc[-1]) for k in ("allow_long","allow_short")},
        "oi_flags":{k:bool(oi_gate[k].iloc[-1]) for k in ("allow_long","allow_short")},
        "crash":crash,
        "bar_close":float(ind["close"].iloc[-1]),
        "hourly_candles":one,
    }



def preserve_utc_risk_window_start(state:dict,now_ms:int):
    """Do not erase overnight/weekly losses by resetting at new UTC date.

    Use the last ACTUALLY OBSERVED equity before the boundary rather than
    the already-depressed equity at the first post-boundary observation.
    This is still discrete monitoring, not guaranteed intrahour execution.
    """
    if state.get("last_checked_ms") is None:
        return
    prior=float(state.get("equity_usd",state["balance"]))
    if not math.isfinite(prior) or prior<=0:
        raise ValueError("Invalid previous observed equity at UTC boundary")
    now_date=datetime.fromtimestamp(now_ms/1000,timezone.utc).date()
    new_day=now_date.isoformat()
    new_week=(now_date-timedelta(days=now_date.weekday())).isoformat()
    if state.get("risk_day") is not None and state["risk_day"]!=new_day:
        state["risk_day"]=new_day
        state["risk_day_start"]=prior
    if state.get("risk_week") is not None and state["risk_week"]!=new_week:
        state["risk_week"]=new_week
        state["risk_week_start"]=prior


def apply_observation(state:dict,snapshot:dict):
    """Mutate a deepcopy of one state ONLY after fully validated public feeds."""
    if state.get("version")!=STATE_VERSION or state.get("real_orders_enabled") is not False:
        raise ValueError("Unexpected state format or trading permission")
    now_ms=int(snapshot["now_ms"])
    previous=state.get("last_checked_ms")
    if previous is not None and now_ms<=previous:
        raise ValueError("Duplicate or reversed observation clock")
    validate_market(snapshot["market"])
    book=snapshot["book"]
    book_quality(book,now_ms)
    signal=candidate_signal(now_ms,snapshot["hourly"],snapshot["btc12"],
                            snapshot["funding"],snapshot["oi_doc"])
    mature_marks=published(snapshot["mark_hourly"],HOUR,now_ms,400)
    if now_ms-(int(mature_marks[-1][0])+HOUR)>2*HOUR:
        raise ValueError("Mark-price feed stale")
    # Make no decisions based on unrecorded hours. If schedule missed >2.5h,
    # close any OPEN paper position at the *observed current book* and
    # block new entry for 24h rather than pretend retroactive stops/fills.
    gap=previous is not None and now_ms-previous>MAX_OBSERVATION_GAP_MS
    if gap:
        state["missed_checks"]+=1
        state["cooldown_until_ms"]=max(state.get("cooldown_until_ms",0),now_ms+DAY)
        state["events"].append({"time":utc(now_ms),"type":"missed_hourly_observation",
                                "elapsed_hours":round((now_ms-previous)/HOUR,3)})
        if state.get("position") is not None:
            close_position(state,0,now_ms,"missed_observation_conservative_exit",book=book)
    # Apply only funding costs from published events; no exchange settlement
    # is represented. The elapsed hour before publication is padded at exit.
    if not gap:
        apply_funding(state,snapshot["funding"],mature_marks,now_ms)
    else:
        mature=[e for e in snapshot["funding"] if int(e["timestamp"])+2*HOUR<=now_ms]
        if mature:state["last_funding_paid_ts"]=int(mature[-1]["timestamp"])
    if previous is not None and state.get("position") is not None:
        p=state["position"]
        bars=[x for x in signal["hourly_candles"] if int(x[0])+HOUR>previous
              and int(x[0])+HOUR>p["entered_ms"]]
        for bar in bars:
            if state.get("position") is None:break
            low,high=float(bar[3]),float(bar[2])
            ishit=low<=p["stop"] if p["side"]==1 else high>=p["stop"]
            if ishit:
                chosen=min(float(bar[1]),p["stop"]) if p["side"]==1 else max(float(bar[1]),p["stop"])
                close_position(state,chosen,int(bar[0])+HOUR,"completed_hourly_stop_touch",
                               modelled_stop=True)
                break
    equity=account_equity(state,book)
    preserve_utc_risk_window_start(state,now_ms)
    reasons=inspect_account(state,now_ms,equity)
    if reasons or state.get("permanent_risk_lock"):
        if state.get("position") is not None:
            close_position(state,0,now_ms,"observed_equity_risk_breaker",book=book)
            equity=account_equity(state,book)
    if state.get("last_signal_ms")!=signal["bar_start_ms"]:
        direction=signal["direction"]
        p=state.get("position")
        if p is not None:
            # Frozen exit logic: 4-or-fewer bullish votes exit a long;
            # 6-or-more bullish votes exit a short.
            exit_vote=(p["side"]==1 and signal["votes"]<=4) or (
                p["side"]==-1 and signal["votes"]>=6)
            if exit_vote or signal["crash"]:
                close_position(state,0,now_ms,"opposing_vote_or_crash",book=book)
            else:
                trail=signal["bar_close"]-p["side"]*2.5*signal["atr"]
                p["stop"]=max(p["stop"],trail) if p["side"]==1 else min(p["stop"],trail)
        if direction!=0 and state.get("position") is None:
            if signal["crash"]:
                state["signal_rejections"]["crash"]+=1
            elif not signal["btc_allow"]:
                state["signal_rejections"]["btc"]+=1
            elif not signal["oi_allow"]:
                state["signal_rejections"]["funding_oi"]+=1
            elif not can_enter(state,now_ms):
                state["signal_rejections"]["risk"]+=1
            else:
                mid=sum(book_quality(book,now_ms))/2
                qty=size_for_risk(state["balance"],mid,signal["atr"],
                                  snapshot["market"],book)
                if qty<MIN_POSITION_CONTRACTS:
                    state["signal_rejections"]["size"]+=1
                else:
                    try:
                        fill=entry_fill_price(book,direction,qty)
                    except ValueError:
                        state["signal_rejections"]["book"]+=1
                    else:
                        start_balance=state["balance"]
                        fee=qty*fill*COMMISSION
                        state["balance"]-=fee
                        state["total_fees_usd"]+=fee
                        state["position"]={
                            "side":direction,"qty":qty,"entry":fill,
                            "entered_ms":now_ms,"entered_utc":utc(now_ms),
                            "opening_wallet":start_balance,
                            "entry_fee":fee,"funding_cost":0.,
                            # conservative max 4% price emergency distance
                            "stop":fill-direction*min(2.5*signal["atr"],.04*fill),
                        }
                        state["events"].append({"time":utc(now_ms),"type":"opened",
                            "side":"long" if direction==1 else "short",
                            "qty":qty,"fill_usd":round(fill,6)})
        elif direction==0:
            state["signal_rejections"]["consensus"]+=1
        state["last_signal_ms"]=signal["bar_start_ms"]
    state["last_checked_ms"]=now_ms
    state["observations"]+=1
    state["last_observation_utc"]=utc(now_ms)
    state["latest_votes"]=signal["votes"]
    state["latest_candidate_signal"]={
        "candle_utc":utc(signal["bar_start_ms"]),
        "buy_votes":signal["votes"],
        "direction":"long" if signal["direction"]==1 else "short" if signal["direction"]==-1 else "hold",
        "btc_regime":signal["btc_flags"],
        "funding_oi":signal["oi_flags"],
        "crash_blocked":signal["crash"],
        "paper_only":True,
    }
    state["equity_usd"]=round(account_equity(state,book),6)
    state["last_book_spread_pct"]=round(
        (book["asks"][0][0]-book["bids"][0][0])/
        ((book["asks"][0][0]+book["bids"][0][0])/2)*100,6)
    state["equity_history"].append({
        "time_utc":utc(now_ms),"equity_usd":state["equity_usd"],
        "balance_usd":round(state["balance"],6),
        "position_open":bool(state.get("position")),
        "buy_votes":signal["votes"],
        "risk_locked":bool(state.get("permanent_risk_lock",False)),
    })
    state["equity_history"]=state["equity_history"][-1500:]
    state["events"]=state["events"][-400:]
    if state["equity_usd"]<=0:
        raise RuntimeError("Simulated account insolvent")
    return state


def fetch_snapshot():
    # All methods below are PUBLIC read calls. No API keys, order endpoints
    # or implicit authenticated exchange setup are used.
    exchange=ccxt.krakenfutures({"enableRateLimit":True})
    try:
        exchange.load_markets()
        market=exchange.market(PAIR)
        validate_market(market)
        hourly=exchange.fetch_ohlcv(PAIR,"1h",limit=600)
        btc12=exchange.fetch_ohlcv("BTC/USD:USD","12h",limit=600)
        mark=exchange.fetch_ohlcv(PAIR,"1h",limit=600,params={"price":"mark"})
        since=exchange.milliseconds()-35*DAY
        funding=exchange.fetch_funding_rate_history(PAIR,since=since,limit=1000)
        # Retain only genuine past published funding records; reject bad gaps.
        if len(funding)<400 or len(funding)>=1000:
            raise ValueError("Insufficient or truncated actual published funding history")
        if any(int(b["timestamp"])<=int(a["timestamp"])
               for a,b in zip(funding,funding[1:])):
            raise ValueError("Repeated or unordered real funding records")
        book=exchange.fetch_order_book(PAIR,limit=20)
        now=exchange.milliseconds()
        url=("https://futures.kraken.com/api/charts/v1/analytics/"
             "PF_ETHUSD/open-interest?interval=14400")
        with urlopen(Request(url,headers={"User-Agent":"crypto-consensus-forward-paper/1.0"}),
                     timeout=30) as response:
            oi_doc=json.load(response)
        if oi_doc.get("errors") or oi_doc.get("result",{}).get("more"):
            raise ValueError("Invalid/truncated genuine Kraken open interest")
        return {"market":market,"hourly":hourly,"btc12":btc12,
                "mark_hourly":mark,"funding":funding,"book":book,
                "now_ms":now,"oi_doc":oi_doc}
    finally:
        exchange.close()


def report(state:dict):
    series=state["equity_history"]
    peak=START_BALANCE
    maxdd=0.
    for row in series:
        peak=max(peak,row["equity_usd"])
        maxdd=max(maxdd,(peak-row["equity_usd"])/peak)
    last=state.get("last_observation_utc")
    return {
        "mode":"forward_only_keyless_one_hour_eth_combined_filters",
        "no_real_orders":True,
        "original_12h_paper_observer_unchanged":True,
        "starting_balance_usd":START_BALANCE,
        "equity_usd":round(state["equity_usd"],6),
        "simulated_return_pct":round(100*(state["equity_usd"]/START_BALANCE-1),5),
        "cash_balance_usd":round(state["balance"],6),
        "closed_paper_trades":len(state["trades"]),
        "wins":sum(t["net_usd"]>0 for t in state["trades"]),
        "losses":sum(t["net_usd"]<0 for t in state["trades"]),
        "realized_close_pnl_usd":round(sum(t["net_usd"] for t in state["trades"]),6),
        "observations":state["observations"],
        "missed_hours_or_gaps":state["missed_checks"],
        "measured_hourly_drawdown_pct":round(100*maxdd,5),
        "daily_lock":state.get("daily_pause_until_ms",0)>state.get("last_checked_ms",0),
        "weekly_lock":state.get("weekly_pause_until_ms",0)>state.get("last_checked_ms",0),
        "peak_manual_lock":bool(state.get("permanent_risk_lock",False)),
        "entry_rejections":state["signal_rejections"],
        "risk_events":state.get("risk_events",[])[-20:],
        "last_observation_utc":last,
        "last_signal":state.get("latest_candidate_signal"),
        "open_paper_position":state["position"],
        "total_execution_fees_usd":round(state["total_fees_usd"],6),
        "total_funding_charged_usd":round(state["total_funding_cost_usd"],6),
        "total_unsettled_funding_buffer_usd":round(state["total_funding_buffer_usd"],6),
        "assumed_extra_adverse_fill_per_side":ADVERSE_SLIPPAGE,
        "actual_best_bid_ask_used_for_quote_fills":True,
        "exchange_stop_order_verified":False,
        "risk_limits_are_hourly_observation_not_guaranteed":True,
    }


def markdown(r:dict):
    return "\n".join([
        "# Forward ETH 1-hour paper candidate: BTC + genuine funding/open interest",
        "",
        "**Genuinely prospective, keyless and no real orders.** The current "
        "12h paper bot remains separate and unchanged. This report NEVER "
        "combines historical backtest profits into forward profitability.",
        "",
        "| Metric | Latest observed value |",
        "|---|---:|",
        f"| Simulated opening cash | \${r['starting_balance_usd']:.2f} |",
        f"| Observed simulated equity | \${r['equity_usd']:.3f} |",
        f"| Observed forward paper return | {r['simulated_return_pct']:+.4f}% |",
        f"| Closed forward paper trades | {r['closed_paper_trades']} |",
        f"| Winners / losers | {r['wins']} / {r['losses']} |",
        f"| Prospective hourly observations | {r['observations']} |",
        f"| Observed sampled drawdown | {r['measured_hourly_drawdown_pct']:.3f}% |",
        f"| Daily/weekly/peak risk locks | {r['daily_lock']} / {r['weekly_lock']} / {r['peak_manual_lock']} |",
        f"| Missed observation gaps | {r['missed_hours_or_gaps']} |",
        f"| Commission charged | \${r['total_execution_fees_usd']:.4f} |",
        f"| Estimated paid funding + safety buffer | \${r['total_funding_charged_usd']+r['total_unsettled_funding_buffer_usd']:.4f} |",
        "",
        f"**Most recent UTC observation:** {r['last_observation_utc']}",
        "",
        "**Execution model:** Current Kraken public order book depth and "
        "bid/ask VWAP for attempted quote fills, plus a further 0.10% "
        "adverse slippage assumption PER SIDE and 0.05% fees PER SIDE. "
        "Candle-level historical stop touches use pessimistic price/open "
        "plus the same extra slippage because historic order books cannot "
        "be reconstructed. Funding-rate payments are estimated from published "
        "events and mark prices; expected receipts are not credited; unsettled "
        "holding periods are charged a buffer at close.",
        "",
        "**Risk:** 1x exposure, maximum 1% theoretical entry-stop risk, "
        "2% daily / 4% weekly / 6% peak observed account lock, loss pause "
        "24h, 3h normal cooldown, 12h/72h crash veto and no retroactive "
        "fills after missed runs. These limits are OBSERVATION-TIME "
        "checks only, not continuously enforced exchange stops. "
        "Real gaps may exceed thresholds.",
        "",
        "No existing positions from the historical backtest were loaded "
        "into the forward paper wallet. Each signal uses completed "
        "1-hour ETH candles, an already-completed BTC 12h candle and "
        "official funding/OI delayed conservatively.",
    ])+"\n"


def cli():
    p=argparse.ArgumentParser()
    p.add_argument("--state",default="crypto-consensus/one_hour_forward_state.json")
    p.add_argument("--report-json",default="crypto-consensus/one_hour_forward_report.json")
    p.add_argument("--report-md",default="crypto-consensus/one_hour_forward_report.md")
    p.add_argument("--smoke",action="store_true",
                   help="Validate public data and candidate signal but never save anything")
    args=p.parse_args()
    path=Path(args.state)
    state=json.loads(path.read_text()) if path.exists() else initial_state()
    data=fetch_snapshot()
    import copy
    result=apply_observation(copy.deepcopy(state),data)
    if args.smoke:
        print(json.dumps({"smoke_only":True,"signal":result["latest_candidate_signal"],
                          "paper_position":result["position"],
                          "unchanged_state":True},indent=2))
        return
    a=report(result)
    writes=[(path,json.dumps(result,sort_keys=True,indent=2)+"\n"),
            (Path(args.report_json),json.dumps(a,sort_keys=True,indent=2)+"\n"),
            (Path(args.report_md),markdown(a))]
    for target,body in writes:
        target.parent.mkdir(parents=True,exist_ok=True)
        tmp=target.with_suffix(target.suffix+".tmp")
        tmp.write_text(body)
        tmp.replace(target)
    print("FORWARD_1H_OBSERVATION",json.dumps({
        "utc":a["last_observation_utc"],"return_pct":a["simulated_return_pct"],
        "trades":a["closed_paper_trades"],"equity":a["equity_usd"],
        "signal":a["last_signal"],"risk_locked":a["peak_manual_lock"],
        "paper_only":True,
    },sort_keys=True))


if __name__=="__main__":
    cli()
