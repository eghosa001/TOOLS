"""Public-data-only Kraken ETH perpetual forward PAPER observer.

No API credentials, no trading endpoints, no order placements, no real fills.
Scheduled observations are discrete; they are NOT an always-on Freqtrade dry-run.
Simulated stops use hourly OHLC (conservative if timing is ambiguous);
funding is estimated using observed hourly mark candle prices.
"""
from __future__ import annotations

from datetime import datetime, timezone
import argparse
import json
import math
from pathlib import Path

import ccxt
import numpy as np
import pandas as pd
from core import build_indicators, decision, STARTUP_CANDLES
from risk_guards import crash_mask, inspect_account, can_enter, TRADE_RISK_FRACTION

PAIR = "ETH/USD:USD"
PAIR_ID = "PF_ETHUSD"
TWELVE_H = 12 * 3600_000
HOUR = 3600_000
FEE = 0.0005
SLIPPAGE = 0.0005
STOP_ATR_MULT = 2.5
RISK = TRADE_RISK_FRACTION
MIN_CONTRACTS = 0.001  # PF_ETHUSD official Kraken spec; refuse if market differs
STATE_VERSION = 1


def now_iso(ts):
    return datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat()


def initial_state():
    return {"version": STATE_VERSION, "balance": 150.0, "position": None,
            "trades": [], "last_checked_ms": None, "last_signal_ms": None,
            "cooldown_until_ms": 0, "funding_usd": 0.0,
            "blocked_entries": 0, "observations": 0, "crash_blocked_entries": 0}


def order_size(wallet, price, atr, market, exchange=None):
    if wallet <= 0 or price <= 0 or atr <= 0 or not np.isfinite(atr):
        return 0.0
    if market.get("id") != PAIR_ID or not market.get("linear", False):
        raise RuntimeError("Wrong futures contract. Paper trade rejected.")
    contract_size = float(market.get("contractSize") or 0)
    if contract_size != 1.0:
        raise RuntimeError("Contract size changed: manual safety review required")
    precision = market.get("precision", {}).get("amount")
    if precision is None or float(precision) != 0.001:
        raise RuntimeError("Unexpected contract step size: refuse modeled fills")
    step = 0.001
    cap_notional = min(wallet, wallet * RISK * price / (max(STOP_ATR_MULT * atr, .04 * price) + .002 * price))
    raw = max(0.0, cap_notional / price / contract_size)
    qty = math.floor((raw + 1e-12) / step) * step
    if qty + 1e-12 < MIN_CONTRACTS:
        return 0.0
    if qty * price * contract_size > wallet + 1e-8:
        raise AssertionError("Paper order exceeds unleveraged balance")
    return round(qty, 8)


def check_candles(rows, timeframe_ms, now_ms, minimum=0):
    complete = [r for r in rows if int(r[0]) + timeframe_ms <= now_ms - 10_000]
    if len(complete) < minimum:
        raise RuntimeError("Insufficient fully closed public market candles")
    times = [int(r[0]) for r in complete]
    if times != sorted(set(times)):
        raise RuntimeError("Invalid OHLCV timestamps")
    if any(b - a != timeframe_ms for a,b in zip(times, times[1:])):
        raise RuntimeError("Missing public OHLCV intervals")
    return complete


def close(state, price, when, reason):
    p = state.get("position")
    if p is None:
        raise AssertionError("No position to close")
    fill = float(price) * (1 - SLIPPAGE * p["side"])
    state["balance"] += p["side"] * p["qty"] * (fill - p["entry"])
    state["balance"] -= p["qty"] * fill * FEE
    pnl = state["balance"] - p["starting_balance"]
    trade = {"entered": p["entered"], "exited": now_iso(when), "side": p["side"],
             "entry": p["entry"], "exit": round(fill, 6), "qty": p["qty"],
             "net_usd": round(pnl, 6), "reason": reason,
             "funding_included": True}
    state["trades"].append(trade)
    state["cooldown_until_ms"] = when + (14 if pnl <= 0 else 3) * TWELVE_H
    state["position"] = None


def simulate_observation(state, now_ms, candles12, candles1, mark1, funding, ticker, market):
    """Apply future-arriving information once; all feeds are public."""
    previous = state.get("last_checked_ms")
    if previous is not None:
        if now_ms <= previous:
            raise RuntimeError("Clock did not advance")
        if now_ms - previous > 36 * HOUR:
            raise RuntimeError("Gap >36h: stop paper ledger for manual reconciliation")

    closed12 = check_candles(candles12, TWELVE_H, now_ms, STARTUP_CANDLES + 5)
    if now_ms - (int(closed12[-1][0]) + TWELVE_H) > TWELVE_H + 2 * HOUR:
        raise RuntimeError("12h public feed stale")
    candles1 = check_candles(candles1, HOUR, now_ms)
    mark1 = check_candles(mark1, HOUR, now_ms)
    if not np.isfinite(ticker) or ticker <= 0:
        raise RuntimeError("Bad ticker price")
    df = pd.DataFrame([{
        "open": float(x[1]), "high": float(x[2]), "low": float(x[3]),
        "close": float(x[4]), "volume": float(x[5]),
    } for x in closed12])
    current = build_indicators(df).iloc[-1]
    crash_now = bool(crash_mask(df).iloc[-1])
    last_signal_ms = int(closed12[-1][0])

    if previous is not None and state.get("position") is not None:
        position = state["position"]
        # Use only complete hourly OHLCV observed after the previous snapshot.
        segment = [b for b in candles1 if int(b[0]) + HOUR > previous]
        if segment and int(segment[0][0]) > previous + HOUR:
            raise RuntimeError("Missing hourly stop-observation candles")
        stop_event = None
        for bar in segment:
            bar_start = int(bar[0])
            if bar_start + HOUR <= int(position["entered_ms"]):
                continue
            hit = (float(bar[3]) <= position["stop"] if position["side"] == 1
                   else float(bar[2]) >= position["stop"])
            if hit:
                fill = (min(float(bar[1]),position["stop"]) if position["side"] == 1
                        else max(float(bar[1]),position["stop"]))
                stop_event = (bar_start + HOUR, fill)
                break
        # Funding uses published Kraken relative funding rates and completed
        # mark-candle closes as an APPROXIMATION, never claimed as settlement.
        mark_prices = {int(b[0]) + HOUR: float(b[4]) for b in mark1}
        events = sorted(funding, key=lambda e: int(e["timestamp"]))
        if len(events) >= 200:
            raise RuntimeError("Funding pagination limit reached")
        funded_through = stop_event[0] if stop_event else now_ms
        for event in events:
            ts = int(event["timestamp"])
            if not (max(previous,position["entered_ms"]) < ts <= funded_through):
                continue
            rate = float(event.get("fundingRate",float("nan")))
            if not np.isfinite(rate):
                raise RuntimeError("Missing published relative funding rate")
            available = [t for t in mark_prices if t <= ts]
            if not available or ts - max(available) > 2 * HOUR:
                raise RuntimeError("Missing mark price near funding event")
            mark = mark_prices[max(available)]
            payment = position["side"] * position["qty"] * mark * rate
            state["balance"] -= payment
            state["funding_usd"] += payment
        if stop_event:
            close(state,stop_event[1],stop_event[0],"hourly_stop_touch")
        elif state.get("position") is not None:
            p = state["position"]
            if (p["side"] == 1 and ticker <= p["stop"]) or (
                    p["side"] == -1 and ticker >= p["stop"]):
                close(state,ticker,now_ms,"observed_quote_stop")

    # Revalue account on every observation, not just on closed trades.
    pos = state.get("position")
    observed_equity = float(state["balance"] + (pos["side"]*pos["qty"]*(ticker-pos["entry"]) if pos else 0.0))
    account_reasons = inspect_account(state, now_ms, observed_equity)
    if state.get("position") is not None and (account_reasons or state.get("permanent_risk_lock", False)):
        close(state, ticker, now_ms, "observed_account_risk_breaker")

    # One new 12h close, acted on at the actual observation quote, not backfilled.
    if state.get("last_signal_ms") != last_signal_ms:
        vote = int(current["buy_votes"])
        p = state.get("position")
        if p is not None and crash_now:
            close(state, ticker, now_ms, "observed_volatility_shock")
            p = None
        if p is not None:
            if decision(vote, p["side"]) == 2:
                close(state,ticker,now_ms,"opposing_vote")
            else:
                new_stop = float(current["close"]) - p["side"] * STOP_ATR_MULT * float(current["atr14"])
                p["stop"] = max(p["stop"],new_stop) if p["side"] == 1 else min(p["stop"],new_stop)
        if state.get("position") is None and can_enter(state, now_ms, crash=crash_now):
            side = decision(vote)
            if side:
                qty = order_size(state["balance"], ticker,float(current["atr14"]),market)
                if qty > 0:
                    entry = ticker * (1 + SLIPPAGE * side)
                    wallet = state["balance"]
                    state["balance"] -= qty * entry * FEE
                    state["position"] = {
                        "side": side, "qty": qty, "entry": entry,
                        "stop": entry - side * STOP_ATR_MULT * float(current["atr14"]),
                        "starting_balance": wallet, "entered": now_iso(now_ms),
                        "entered_ms": now_ms,
                    }
                else:
                    state["blocked_entries"] += 1
        if state.get("position") is None and crash_now and decision(vote):
            state["crash_blocked_entries"] = state.get("crash_blocked_entries", 0) + 1
        state["last_signal_ms"] = last_signal_ms
    state["last_checked_ms"] = now_ms
    state["observations"] += 1
    state["latest_votes"] = int(current["buy_votes"])
    state["crash_entry_blocked"] = crash_now
    state["last_quote"] = ticker
    state["last_observation"] = now_iso(now_ms)
    p = state.get("position")
    state["equity_usd"] = round(state["balance"] + (
        p["side"] * p["qty"] * (ticker - p["entry"]) if p else 0.0), 6)
    state.setdefault("equity_history", [])
    state["equity_history"].append({"utc": now_iso(now_ms),
                                  "equity_usd": state["equity_usd"],
                                  "votes": state["latest_votes"],
                                  "position_open": state.get("position") is not None})
    state["equity_history"] = state["equity_history"][-3000:]
    if state["equity_usd"] <= 0:
        raise RuntimeError("Paper account insolvent")
    return state


def fetch_and_apply(state):
    exchange = ccxt.krakenfutures({"enableRateLimit": True})
    try:
        exchange.load_markets()
        market = exchange.market(PAIR)
        if market["id"] != PAIR_ID or not market.get("active", True):
            raise RuntimeError("Wrong or inactive Kraken contract")
        now_ms = exchange.milliseconds()
        start = state.get("last_checked_ms")
        if start is not None and now_ms - start > 36 * HOUR:
            raise RuntimeError("Stale state (>36h): no invented fills")
        o12 = exchange.fetch_ohlcv(PAIR, "12h", limit=550)
        quote = float(exchange.fetch_ticker(PAIR)["last"])
        if start is not None and state["position"]:
            o1 = exchange.fetch_ohlcv(PAIR,"1h", since=start-HOUR,limit=80)
            marks = exchange.fetch_ohlcv(PAIR,"1h", since=start-2*HOUR,
                                         limit=80,params={"price":"mark"})
            rates = exchange.fetch_funding_rate_history(PAIR,since=start,
                                                       limit=200)
        else:
            o1,marks,rates = [],[],[]
        return simulate_observation(state,now_ms,o12,o1,marks,rates,quote,market)
    finally:
        exchange.close()


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--state", default="crypto-consensus/forward_paper_state.json")
    arg.add_argument("--smoke",action="store_true",
                     help="Read and verify live public feed, but never modify state")
    opts = arg.parse_args()
    path = Path(opts.state)
    state = json.loads(path.read_text()) if path.exists() else initial_state()
    if state.get("version") != STATE_VERSION:
        raise RuntimeError("Unknown state format")
    after = fetch_and_apply(state)
    print(json.dumps({"mode":"PUBLIC-DATA ONLY: NO ORDER ROUTING",
                       "timestamp":after["last_observation"],
                       "votes":after["latest_votes"],
                       "simulated_equity_usd":after["equity_usd"],
                       "paper_position":after["position"],
                       "simulated_trades":len(after["trades"]),
                       "funding_estimate_usd":round(after["funding_usd"],6),
                       "risk_daily_paused":after.get("daily_pause_until_ms",0)>after["last_checked_ms"],
                       "risk_weekly_paused":after.get("weekly_pause_until_ms",0)>after["last_checked_ms"],
                       "risk_permanently_locked":after.get("permanent_risk_lock",False),
                       "crash_entry_blocked":after.get("crash_entry_blocked",False)},indent=2))
    if not opts.smoke:
        tmp=path.with_suffix(".tmp")
        tmp.parent.mkdir(parents=True,exist_ok=True)
        tmp.write_text(json.dumps(after,sort_keys=True,indent=2)+"\n")
        tmp.replace(path)


if __name__ == "__main__":
    main()
