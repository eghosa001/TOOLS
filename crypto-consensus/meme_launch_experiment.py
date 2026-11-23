"""Research-only $150 per-scenario Kraken Futures screen.
Reuses existing crypto-consensus ten-vote engine and observed-equity risk gates.
Independent next-open fill simulator; NOT the Freqtrade execution engine.
No credentials, orders, leverage, optimization, or model inference.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import sys
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd
from core import build_indicators
from intraday_research_utils import time_consistent_crash_mask
from risk_guards import inspect_account, can_enter, TRADE_RISK_FRACTION

BASE = Path(__file__).resolve().parent
REPORT = BASE / "meme_launch_experiment.json"
START = int(pd.Timestamp("2026-10-15", tz="UTC").timestamp() * 1000)
WARMUP = int(pd.Timestamp("2026-10-01", tz="UTC").timestamp() * 1000)
END = int(pd.Timestamp("2026-11-23", tz="UTC").timestamp() * 1000)
HOUR = 3600_000
FIVE_MIN = 300_000
COINS = {"scalp": ("BTC", "ETH", "SOL"),
         "meme_momentum": ("DOGE", "PEPE", "WIF", "TRUMP", "FARTCOIN", "PENGU", "MUBARAK")}
# Predeclared Kraken Futures 2026 contract launch dates, from official contract specs.
# This is an EXCHANGE-LISTING proxy, not first on-chain token launch.
NEW_LISTING_DATES = {"MEZO":"2026-04-01", "OPN":"2026-03-06",
                     "PONS":"2026-09-25", "RAVE":"2026-03-17",
                     "UNITAS":"2026-04-01", "VSN":"2026-07-23"}
NEW_LISTING_POOL = tuple(NEW_LISTING_DATES)
MODEL_FEE = {"base": .0005, "stress": .0015} # cost per side incl modeled spread in stress
EXCHANGE = "Kraken Futures publicly reported trade candles; no keys"


def fetch_range(ex, symbol, timeframe, start, end, limit=500):
    step = ex.parse_timeframe(timeframe) * 1000
    cursor = start
    found = {}
    for _ in range(150):
        if cursor >= end:
            break
        rows = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=cursor, limit=limit)
        if not rows:
            raise ValueError("No source bars at requested time")
        advanced = False
        for x in rows:
            t = int(x[0])
            if t >= cursor and t < end:
                found[t] = list(x)
                advanced = True
        max_t = max(int(x[0]) for x in rows)
        if max_t < cursor:
            raise ValueError("Exchange price history cannot paginate to requested range")
        nxt = max_t + step
        if nxt <= cursor:
            raise ValueError("Historical price pagination did not advance")
        cursor = nxt
        if not advanced and cursor < end:
            raise ValueError("Missing market data for requested interval")
    if cursor < end:
        raise ValueError("Source data ended before test boundary")
    values = [found[x] for x in sorted(found)]
    if not values:
        raise ValueError("No validated exchange candles")
    df = pd.DataFrame(values, columns=["timestamp", "open", "high", "low", "close", "volume"])
    for field in ("open", "high", "low", "close", "volume"):
        if not np.isfinite(df[field]).all() or (df[field] < 0).any():
            raise ValueError("Invalid numeric Kraken candle " + field)
    if (df[["open","high","low","close"]] <= 0).any().any():
        raise ValueError("Zero price source bar")
    subset = df[(df.timestamp >= START) & (df.timestamp < END)]
    gaps = subset.timestamp.diff().dropna()
    if len(subset) < 7500 or (gaps > step).any():
        raise ValueError("Incomplete continuous historical testing period")
    return df.reset_index(drop=True)


def funding(ex, symbol):
    cursor = START - 2*HOUR
    events = {}
    for _ in range(15):
        if cursor >= END:
            break
        rates = ex.fetch_funding_rate_history(symbol, since=cursor, limit=500)
        if not rates:
            raise ValueError("Actual exchange funding series unavailable")
        for item in rates:
            t = int(item["timestamp"])
            v = item.get("fundingRate")
            if v is None or not math.isfinite(float(v)):
                raise ValueError("Missing real exchange funding")
            events[t] = float(v)
        maximum = max(int(x["timestamp"]) for x in rates)
        if maximum < cursor:
            raise ValueError("Funding pagination did not advance")
        cursor = maximum + 1
    ticks = sorted(t for t in events if START <= t < END)
    if len(ticks) < 28*24 or ticks[0] > START+3*HOUR or ticks[-1] < END-3*HOUR:
        raise ValueError("Insufficient exchange funding coverage")
    if any(b-a>3*HOUR for a,b in zip(ticks,ticks[1:])):
        raise ValueError("Gaps in actual funding observations")
    # exact timestamp application; historical funding may publish on the hour
    return {t: events[t] for t in ticks}


def signals(df, strategy):
    f = build_indicators(df)
    f["crash_block"] = time_consistent_crash_mask(f, "5m")
    prior_volume = f.volume.shift(1).rolling(72, min_periods=72).median()
    f["relvol"] = f.volume / prior_volume.replace(0,np.nan)
    f["one_hour_return"] = f.close / f.close.shift(12) - 1
    if strategy == "scalp":
        f["go_long"] = (f.buy_votes>=8) & (~f.crash_block) & (f.volume>0)
        f["go_short"] = (f.buy_votes<=2) & (~f.crash_block) & (f.volume>0)
    else:
        f["go_long"] = ((f.buy_votes>=8) & (f.one_hour_return>=.02) &
                        (f.relvol>=1.8) & (~f.crash_block) & (f.volume>0))
        f["go_short"] = False
    return f


def backtest(f, strategy, fee, funding_events):
    # funding events apply once per observed hourly event while a position is held;
    # last-price not mark-price settlement => estimated, not exchange fill economics
    cash, peak, pos = 150., 150., None
    s = {"equity_peak": 150., "cooldown_until_ms": 0}
    hist, trades = [], []
    fees_paid = funding_paid = 0.
    forced = 0
    initial_idx = int(f.index[f.timestamp >= START][0])
    for i in range(initial_idx, len(f)):
        bar = f.iloc[i]
        prior = f.iloc[i-1]
        t = int(bar.timestamp)
        if t>=END:
            break
        current = float(bar["open"])
        if pos is not None:
            # Prior close is observed before this opening price; no same-bar foresight.
            side = int(pos["side"])
            expired = t-pos["t"] >= (12*HOUR if strategy=="meme_momentum" else 72*HOUR)
            reverse = (prior.buy_votes <=4 if side==1 else prior.buy_votes>=6)
            if strategy=="meme_momentum" and (current/pos["entry"]-1)>=.06:
                reverse = True
            price = None
            reason = None
            if expired or reverse or s.get("permanent_risk_lock",False):
                price,reason = current, "closed_signal_or_time_or_lock"
            elif (side==1 and float(bar.low)<=pos["stop"]) or (side==-1 and float(bar.high)>=pos["stop"]):
                # Conservative price gap: adverse gap opens beyond stop.
                price = min(current, pos["stop"]) if side==1 else max(current,pos["stop"])
                reason="stop_touch"
            if price is not None:
                pnl = pos["stake"]*side*(price/pos["entry"]-1) - pos["stake"]*fee
                cost = pos["stake"]*fee
                cash += pnl
                fees_paid += cost
                trade = dict(side=side, entered=pos["t"], closed=t, net_usd=round(cash-pos["pre_cash"],6),
                             exit_reason=reason)
                trades.append(trade)
                s["cooldown_until_ms"] = t + (24*HOUR if cash < pos["pre_cash"] else 3*HOUR)
                pos = None
            else:
                # Only tighten the trailing stop AFTER this candle completes,
                # for application to the NEXT candle (conservative causality).
                if math.isfinite(float(prior.atr14)):
                    target = float(prior.close) - side*2.5*float(prior.atr14)
                    if side==1:
                        pos["stop"] = max(pos["stop"],min(target,prior.close*.999))
                    else:
                        pos["stop"] = min(pos["stop"],max(target,prior.close*1.001))
        if pos is not None and t in funding_events:
            payment = pos["side"]*pos["stake"]*funding_events[t]
            cash -= payment
            funding_paid += payment
        equity = cash
        if pos is not None:
            equity += pos["side"]*pos["stake"]*(current/pos["entry"]-1)
        inspect_account(s,t,max(equity,0.0001))
        # Crash refusal and original observed-equity safety thresholds apply.
        if pos is None and bool(prior.warm) and can_enter(s,t,bool(prior.crash_block)):
            side = 1 if bool(prior.go_long) else -1 if bool(prior.go_short) else 0
            if side != 0:
                atr = float(prior.atr14)
                distance = max(.04,2.5*atr/current)+.002
                stake = min(cash,cash*TRADE_RISK_FRACTION/distance)
                if stake>0 and math.isfinite(stake) and current>0:
                    pos = {"side":side,"entry":current,"stake":stake,
                           "stop":current*(1-.04*side),
                           "t":t,"pre_cash":cash}
                    cost=stake*fee
                    cash-=cost
                    fees_paid+=cost
        mtm = cash + (pos["side"]*pos["stake"]*(current/pos["entry"]-1) if pos else 0)
        hist.append(mtm)
    # No artificial profit from end-of-test force-close; return open mark-to-market separately.
    reported_cash = float(cash)
    open_pnl = 0 if pos is None else pos["side"]*pos["stake"]*(float(f.iloc[-1].close)/pos["entry"]-1)
    end_equity = reported_cash+open_pnl
    running_high=np.maximum.accumulate(np.r_[150.,np.array(hist)])
    dd=np.max(1-np.r_[150.,np.array(hist)]/running_high)
    return {
        "net_return_pct":round(100*(end_equity/150-1),4),
        "net_usd":round(end_equity-150,6),
        "realized_cash_usd":round(reported_cash,6),
        "open_mark_to_market_usd":round(open_pnl,6),
        "open_position_at_end":pos is not None,
        "closed_trades":len(trades),
        "wins":sum(x["net_usd"]>0 for x in trades),
        "losses":sum(x["net_usd"]<0 for x in trades),
        "fees_usd":round(fees_paid,6),
        "estimated_funding_usd":round(funding_paid,6),
        "max_sampled_equity_drawdown_pct":round(100*float(dd),4),
        "risk_lock":bool(s.get("permanent_risk_lock",False)),
    }


def launch_probe(ex, market):
    # Examines exchange-listed contracts only, not on-chain DEX launches or delisted failures.
    start=int(pd.Timestamp("2026-01-01",tz="UTC").timestamp()*1000)
    rows=ex.fetch_ohlcv(market,"1h",since=start,limit=150)
    if not rows:
        return {"status":"no_price_data"}
    first=rows[0][0]
    expected=int(pd.Timestamp(NEW_LISTING_DATES[market.split("/")[0]],tz="UTC").timestamp()*1000)
    if abs(first-expected)>72*HOUR:
        return {"status":"historical_first_bar_mismatch_official_listing_date",
                "expected_utc":NEW_LISTING_DATES[market.split("/")[0]],
                "first_bar_utc":dt.datetime.fromtimestamp(first/1000,dt.timezone.utc).isoformat()}
    if first >= END-3*24*HOUR:
        return {"status":"insufficient_followup"}
    if len(rows)<72:
        return {"status":"insufficient_launch_history"}
    if any(b[0]-a[0]>HOUR for a,b in zip(rows[:72],rows[1:72])):
        return {"status":"gapped_launch_prices"}
    # Fixed rule, not fitted: after first six 1h closed candles, buy at hour 7
    # only when first 6h rose >=3%. Compare stop/TP/24h time exit.
    early=rows[:31]
    if early[5][4]/early[0][1]-1<.03:
        return {"status":"no_entry_signal","first_utc":dt.datetime.fromtimestamp(first/1000,dt.timezone.utc).isoformat()}
    entry=float(early[6][1])
    stop=entry*.95
    take=entry*1.10
    exit_price=float(early[30][4])
    exit_reason="24h_time_exit"
    for r in early[6:31]:
        if r[3]<=stop:
            exit_price=min(float(r[1]),stop)
            exit_reason="5pct_stop"
            break
        if r[2]>=take:
            exit_price=take
            exit_reason="10pct_take_profit"
            break
    return {"status":"eligible_simulated","first_utc":dt.datetime.fromtimestamp(first/1000,dt.timezone.utc).isoformat(),
            "net_return_pct_fee_only":round(100*(exit_price/entry-1-2*.0015),4),
            "exit_reason":exit_reason,"warning":"No historical mark/funding/spread validation; not deployable"}


def main():
    ex=ccxt.krakenfutures({"enableRateLimit":True,"timeout":45000})
    report={"date_created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "exchange":EXCHANGE,"study_utc":["2026-10-15","2026-11-23"],
            "not_trading_permission":True,"independent_wallet_usd":150,
            "risk":"1x 1%-at-stop risk; existing 2% day/4% week/6% peak observed-equity gates",
            "method":"causal next-open simplified simulator; excludes exchange minimum contract rounding",
            "candidate_pool":COINS,"results":[],"launch_probe":{},
            "limitations":["Research reuses core voting and guards but is NOT the Freqtrade fill engine.",
                           "Funding approximated on price rather than actual settlement mark.",
                           "Kraken-listed survivor sample cannot represent rug pulls or delisted launches.",
                           "No liquidation orderbook fills or exact exchange minimum contract sizes."]}
    try:
        markets=ex.load_markets()
        for strategy,coins in COINS.items():
            for coin in coins:
                symbol=f"{coin}/USD:USD"
                if symbol not in markets or not markets[symbol].get("active",False):
                    report["results"].append({"strategy":strategy,"coin":coin,"status":"unavailable_exchange_market"})
                    continue
                try:
                    price=fetch_range(ex,symbol,"5m",WARMUP,END)
                    fees=funding(ex,symbol)
                    f=signals(price,strategy)
                    for typ,rate in MODEL_FEE.items():
                        row=backtest(f,strategy,rate,fees)
                        report["results"].append({"strategy":strategy,"coin":coin,"cost":typ,"status":"completed",
                                                  "candles":len(f),**row})
                except Exception as err:
                    report["results"].append({"strategy":strategy,"coin":coin,"status":"invalid_or_incomplete",
                                              "reason":str(err)[:240]})
        for coin in NEW_LISTING_POOL:
            symbol=f"{coin}/USD:USD"
            if symbol not in markets or not markets[symbol].get("active",False):
                report["launch_probe"][coin]={"status":"unavailable_exchange_market"}
                continue
            try:
                report["launch_probe"][coin]=launch_probe(ex,symbol)
            except Exception as err:
                report["launch_probe"][coin]={"status":"historical_probe_failed","reason":str(err)[:240]}
        REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print("EXPERIMENT_JSON="+json.dumps(report,sort_keys=True))
        if not any(x["status"]=="completed" for x in report["results"]):
            raise SystemExit("FAILED_CLOSED: No validated comparable result")
    finally:
        ex.close()

if __name__=="__main__":
    main()
