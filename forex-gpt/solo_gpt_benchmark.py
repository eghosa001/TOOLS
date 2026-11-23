#!/usr/bin/env python3
"""Isolated, GPT-only, sealed-snapshot Forex research; absolutely no live orders.

Experiment: GBP/USD M1 at 08, 10, 12, 14 UTC on Nov 16-20, 2026.
The model sees ONLY market information available before each decision.
Every choice is saved, hashed and printed BEFORE any future outcomes are read.
The benchmark has no CFTC, KNN or LightGBM decisions. Historical paper only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

import forex_gpt

BASE = Path(__file__).resolve().parent
MARKET = BASE / ".tmp" / "gpt_solo_m1.json"
DECISIONS = BASE / ".tmp" / "gpt_solo_decisions.json"
RESULT = BASE / ".tmp" / "gpt_solo_result.json"
PIP = 0.0001
MINUTE = 60000
POSITION_GBP = 1000
COMMISSION_USD = 0.06
ADDITIONAL_SLIPPAGE_RT_PIPS = 0.2
MAX_ENTRY_SPREAD_PIPS = 1.5
DAILY_PAUSE_LOSS_USD = -3.0
DAYS = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-20"]
DECISION_HOURS_UTC = [8, 10, 12, 14]
HOLD_MINUTES = 15

MODEL_PROMPT = (
    "You are a standalone, risk-conscious GBP/USD short-horizon research trader. "
    "You are NOT receiving CFTC positioning, another strategy's direction, future "
    "candles, or news. The data describes only completed past one-minute candles. "
    "Choose BUY, SELL or SKIP for a hypothetical 1,000 GBP position opened about "
    "one minute after this observation and closed 15 minutes later. BUY enters "
    "at ask and exits bid; SELL enters at bid and exits ask. Estimate whether "
    "there is a directional edge AFTER the spread, an additional 0.2 pip "
    "round-trip slippage and $0.06 commission. Do not invent prices, outcomes, "
    "economic events or live market conditions. SKIP if the edge is weak. "
    "Choose independently using only the supplied snapshot. Return JSON only."
)
FORMAT = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": ["BUY", "SELL", "SKIP"]},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["decision", "confidence", "reason"],
    "additionalProperties": False,
}


def utc_millis(day, hour):
    return int(dt.datetime.fromisoformat(
        f"{day}T{hour:02d}:00:00+00:00").timestamp() * 1000)


def load_price_map(path=MARKET):
    raw = json.loads(Path(path).read_text())
    if raw.get("symbol") != "gbpusd" or raw.get("timeframe") != "m1":
        raise ValueError("Wrong bid/ask price source")
    sides = {}
    for name in ("bid", "ask"):
        rows = raw["sides"][name]
        sides[name] = {int(row[0]): row for row in rows}
    common = sorted(set(sides["bid"]) & set(sides["ask"]))
    if len(common) < 2000:
        raise ValueError("Too few matching bid/ask M1 records")
    for t in common:
        b, a = sides["bid"][t], sides["ask"][t]
        if b[1] > a[1] or any(
            not math.isfinite(float(v)) or float(v) <= 0
            for v in b[1:5] + a[1:5]
        ):
            raise ValueError(f"Invalid quotation at {t}")
    return sides


def past_snapshot(sides, decision_time):
    """Strictly reads minute bars whose *entire* candle ended by decision_time."""
    times = [decision_time - n * MINUTE for n in range(120, 0, -1)]
    for t in times:
        if t not in sides["bid"] or t not in sides["ask"]:
            raise ValueError(f"Missing completed M1 candle {t}")
    bid, ask = sides["bid"], sides["ask"]
    mid = [(bid[t][4] + ask[t][4]) / 2 for t in times]
    midhigh = [(bid[t][2] + ask[t][2]) / 2 for t in times]
    midlow = [(bid[t][3] + ask[t][3]) / 2 for t in times]
    delta = [(mid[j] - mid[j - 1]) / PIP for j in range(1, len(mid))]
    spread = (ask[times[-1]][4] - bid[times[-1]][4]) / PIP
    if spread < 0:
        raise ValueError("Inverted bid/ask spread")

    def change(minutes):
        return round((mid[-1] - mid[-1 - minutes]) / PIP, 3)

    def ema(n):
        k = 2 / (n + 1)
        x = mid[0]
        for val in mid[1:]:
            x += k * (val - x)
        return x

    stamp = dt.datetime.fromtimestamp(decision_time / 1000, dt.timezone.utc)
    return {
        "decision_utc": stamp.isoformat(),
        "instrument": "GBPUSD",
        "position_gbp_units": POSITION_GBP,
        "holding_minutes_after_entry": HOLD_MINUTES,
        "entry_delay_minutes": 1,
        "last_completed_M1_close_utc": (stamp).isoformat(),
        "last_completed_mid_price": round(mid[-1], 6),
        "last_completed_spread_pips": round(spread, 3),
        "momentum_pips": {str(n): change(n) for n in (5, 15, 30, 60)},
        "recent_30m_return_volatility_pips": round(statistics.pstdev(delta[-30:]), 3),
        "recent_60m_high_low_pips": round((max(midhigh[-60:]) - min(midlow[-60:])) / PIP, 3),
        "ema8_minus_ema32_pips": round((ema(8) - ema(32)) / PIP, 3),
        "recent_8_M1_change_pips": [round(v, 2) for v in delta[-8:]],
        "hour_utc": stamp.hour,
        "weekday_utc": stamp.strftime("%A"),
        "commission_usd_round_trip": COMMISSION_USD,
        "additional_slippage_pips_round_trip": ADDITIONAL_SLIPPAGE_RT_PIPS,
        "no_future_candles_or_CFTC_features": True,
    }


def build_cases(sides):
    cases = []
    for day in DAYS:
        for hour in DECISION_HOURS_UTC:
            t = utc_millis(day, hour)
            cases.append({
                "id": f"{day}T{hour:02d}:00Z",
                "decision_time_ms": t,
                "market_snapshot": past_snapshot(sides, t)
            })
    return cases


def ask_gpt(snapshot):
    response = forex_gpt.call_api("POST", "/responses", {
        "model": forex_gpt.MODEL,
        "instructions": MODEL_PROMPT,
        "input": [{"role": "user", "content": json.dumps(snapshot, sort_keys=True)}],
        "store": False,
        "max_output_tokens": 650,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "solo_fx_trade_decision",
                "strict": True,
                "schema": FORMAT,
            }
        },
    })
    if response.get("status") != "completed":
        raise RuntimeError("GPT response not completed")
    text_items = [
        part.get("text", "")
        for item in response.get("output", []) if item.get("type") == "message"
        for part in item.get("content", []) if part.get("type") == "output_text"
    ]
    if len(text_items) != 1:
        raise RuntimeError("Expected exactly one text answer")
    choice = json.loads(text_items[0])
    if (
        set(choice) != set(FORMAT["required"])
        or choice["decision"] not in ("BUY", "SELL", "SKIP")
        or isinstance(choice["confidence"], bool)
        or not isinstance(choice["confidence"], (int, float))
        or not math.isfinite(choice["confidence"])
        or not 0 <= choice["confidence"] <= 1
        or not isinstance(choice["reason"], str)
        or not 3 <= len(choice["reason"]) <= 500
    ):
        raise RuntimeError("Model output validation failed")
    return choice, response.get("usage", {})


def settle(cases, choices, sides):
    """Only invoked after all GPT choices have been sealed to disk."""
    by_day = {d: {"trades": 0, "skipped": 0, "spread_rejected": 0,
                  "daily_pause_rejected": 0, "net_usd": 0.0,
                  "wins": 0, "losses": 0} for d in DAYS}
    details = []
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for case, decision in zip(cases, choices):
        if case["id"] != decision["id"]:
            raise ValueError("Case/choice sequence mismatch")
        day = case["id"][:10]
        d = by_day[day]
        side = decision["decision"]
        entry_ms = case["decision_time_ms"] + MINUTE
        exit_ms = entry_ms + HOLD_MINUTES * MINUTE
        row = {"id": case["id"], "decision": side, "confidence": decision["confidence"]}
        if side == "SKIP":
            d["skipped"] += 1
            row["status"] = "GPT_SKIP"
        elif d["net_usd"] <= DAILY_PAUSE_LOSS_USD:
            d["daily_pause_rejected"] += 1
            row["status"] = "DAILY_RISK_PAUSE"
        else:
            ask_entry = sides["ask"][entry_ms][1]
            bid_entry = sides["bid"][entry_ms][1]
            spread = (ask_entry - bid_entry) / PIP
            if spread <= 0 or spread > MAX_ENTRY_SPREAD_PIPS:
                d["spread_rejected"] += 1
                row["status"] = "ENTRY_SPREAD_EXCEEDED"
                row["spread_pips"] = round(spread, 3)
            else:
                bid_exit = sides["bid"][exit_ms][1]
                ask_exit = sides["ask"][exit_ms][1]
                gross = ((bid_exit - ask_entry) if side == "BUY"
                         else (bid_entry - ask_exit)) * POSITION_GBP
                pnl = round(
                    gross - POSITION_GBP * PIP * ADDITIONAL_SLIPPAGE_RT_PIPS
                    - COMMISSION_USD,
                    5
                )
                d["trades"] += 1
                d["net_usd"] += pnl
                d["wins"] += int(pnl > 0)
                d["losses"] += int(pnl < 0)
                equity += pnl
                peak = max(peak, equity)
                max_dd = max(max_dd, peak - equity)
                row.update({
                    "status": "SIMULATED_CLOSED",
                    "net_usd": pnl,
                    "spread_pips": round(spread, 3),
                    "entry_utc": dt.datetime.fromtimestamp(entry_ms / 1000, dt.timezone.utc).isoformat(),
                    "exit_utc": dt.datetime.fromtimestamp(exit_ms / 1000, dt.timezone.utc).isoformat(),
                    "simulated_entry_px": ask_entry if side == "BUY" else bid_entry,
                    "simulated_exit_px": bid_exit if side == "BUY" else ask_exit,
                })
        details.append(row)
    for d in by_day.values():
        d["net_usd"] = round(d["net_usd"], 4)
    return {
        "model": forex_gpt.MODEL,
        "kind": "historical standalone GPT-only one-minute-price backtest",
        "days": by_day,
        "total_net_usd": round(sum(d["net_usd"] for d in by_day.values()), 4),
        "total_executed_trades": sum(d["trades"] for d in by_day.values()),
        "total_skipped_by_gpt": sum(d["skipped"] for d in by_day.values()),
        "profitable_days": sum(d["net_usd"] > 0 for d in by_day.values()),
        "losing_days": sum(d["net_usd"] < 0 for d in by_day.values()),
        "zero_profit_days": sum(d["net_usd"] == 0 for d in by_day.values()),
        "closed_trade_max_drawdown_usd": round(max_dd, 4),
        "daily_pause_loss_usd": DAILY_PAUSE_LOSS_USD,
        "max_entry_spread_pips": MAX_ENTRY_SPREAD_PIPS,
        "trade_holding_minutes": HOLD_MINUTES,
        "entry_delay_minutes": 1,
        "gpt_calls_requested": len(cases),
        "estimated_trading_fee_model": {
            "size_gbp_units": POSITION_GBP,
            "commission_usd": COMMISSION_USD,
            "additional_slippage_pips_rt": ADDITIONAL_SLIPPAGE_RT_PIPS,
            "spread": "Dukascopy actual historical bid/ask opens",
        },
        "notes": [
            "No CFTC or other direction predictor used in GPT prompts",
            "GPT predictions sealed before price outcomes were calculated",
            "No broker orders, broker slippage verification, or live fill observations",
            "Historical selections after observing test results are not forward proof",
            "No assurance of profit or reliable millisecond execution",
        ],
        "trades_and_skips": details
    }


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--validate-only", action="store_true")
    args = cli.parse_args()
    sides = load_price_map()
    cases = build_cases(sides)
    assert len(cases) == 20
    if args.validate_only:
        print("SOLO_GPT_VALIDATED", len(cases),
              "strict past-only snapshots and complete future test quotes")
        for case in cases:
            entry = case["decision_time_ms"] + MINUTE
            exit_ = entry + 15 * MINUTE
            for name in ("bid", "ask"):
                if entry not in sides[name] or exit_ not in sides[name]:
                    raise ValueError("Missing future settlement quote")
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("Missing GitHub OPENAI_API_KEY; no fake GPT decisions allowed")
    print("MODEL_CONNECTION", json.dumps(forex_gpt.run_check()), flush=True)
    decisions = []
    start = time.monotonic()
    for idx, case in enumerate(cases):
        choice, usage = ask_gpt(case["market_snapshot"])
        decisions.append({
            "id": case["id"],
            "decision": choice["decision"],
            "confidence": choice["confidence"],
            "reason": choice["reason"],
            "usage": usage,
            "model": forex_gpt.MODEL
        })
        print("GPT_PRECOMMIT", idx + 1, case["id"],
              choice["decision"], "confidence", choice["confidence"], flush=True)
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": forex_gpt.MODEL,
        "predictions": decisions,
        "outcomes_absent": True,
        "no_broker_orders": True,
    }
    blob = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    DECISIONS.write_text(blob)
    digest = hashlib.sha256(blob.encode()).hexdigest()
    print("PREDICTIONS_SEALED_SHA256", digest, flush=True)

    # This is the FIRST point where future bid/ask quotes are used.
    report = settle(cases, decisions, sides)
    report["prediction_file_sha256"] = digest
    report["model_elapsed_seconds"] = round(time.monotonic() - start, 2)
    RESULT.write_text(json.dumps(report, indent=2) + "\n")
    print("GPT_SOLO_DAILY_RESULTS", json.dumps(report["days"], sort_keys=True), flush=True)
    print("GPT_SOLO_SUMMARY", json.dumps({
        "net_usd": report["total_net_usd"],
        "profitable_days": report["profitable_days"],
        "losing_days": report["losing_days"],
        "trades": report["total_executed_trades"],
        "gpt_skips": report["total_skipped_by_gpt"],
        "closed_trade_max_drawdown_usd": report["closed_trade_max_drawdown_usd"],
        "predictions_hash": digest,
        "seconds": report["model_elapsed_seconds"],
    }, sort_keys=True), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("GPT_SOLO_BENCHMARK_FAILED:", type(err).__name__, str(err)[:300], file=sys.stderr)
        print("No broker orders were placed; do not infer profitability.", file=sys.stderr)
        sys.exit(2)
