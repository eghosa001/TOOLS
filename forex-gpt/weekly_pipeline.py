#!/usr/bin/env python3
"""Weekly CFTC GBP/USD CPU + GPT SHADOW and after-cost settlement.

- CFTC source: public TFF Futures Only, CME GBP futures code 096742.
- Price source: Dukascopy completed H1 bid and ask from fetch_market.cjs.
- CPU strategy: sign of week-on-week leveraged-money net/OI delta, abs >= .005.
  Report Tuesday+8 calendar days, eligible following Wednesday 09:00 UTC.
  Projected entry following Wednesday 10:00 UTC, hold 2 or 5 calendar days.
- GPT: OpenAI API invoked via forex_gpt.py only inside Wednesday window,
  and NEVER changes CPU recommendation or issues an actual order.
- Follow-up days: measures realized hypothetical PnL from historical
  price quotations and tracks losses, skipped trades, and stop scenario.
- NO broker accounts, live or demo broker orders, execution credentials.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import urllib.parse
import urllib.request

import forex_gpt
import shadow_evaluation

UTC = dt.timezone.utc
BASE = Path(__file__).resolve().parent
DATA = BASE / ".tmp" / "market_data.json"
LEDGER = BASE / ".state" / "ledger.json"
RESULT = BASE / ".tmp" / "latest_run.json"
BOOTSTRAP = BASE / "initial_closed_trades.json"
CFTC_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
PIP = .0001
SLIP_PIPS_RT = .2
COMMISSION_RT_USD = .06
FINANCING_DAY_1000_GBP = .05   # hypothetical, not a broker swap quote
SIDE = {"BUY": 1, "SELL": -1}


def utcnow() -> dt.datetime:
    return dt.datetime.now(UTC)


def parse_dt(value):
    if not isinstance(value, str):
        raise ValueError("Missing datetime")
    z = dt.datetime.fromisoformat(value.replace("Z", "+00:00").replace(" ", "T"))
    if z.tzinfo is None or z.utcoffset() != dt.timedelta(0):
        raise ValueError("Timestamp requires UTC timezone")
    return z.astimezone(UTC)


def clean_ratio(row):
    oi = float(row["open_interest_all"])
    long = float(row["lev_money_positions_long"])
    short = float(row["lev_money_positions_short"])
    if not math.isfinite(oi + long + short) or oi <= 1000 or min(long, short) < 0:
        raise ValueError("Invalid CFTC leveraged-money and OI counts")
    return (long - short) / oi


def fetch_cftc():
    params = urllib.parse.urlencode({
        "$where": "cftc_contract_market_code = '096742'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 10,
    })
    req = urllib.request.Request(CFTC_URL + "?" + params,
            headers={"Accept": "application/json", "User-Agent": "ForexPaperResearch/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.loads(response.read(180000))
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("CFTC TFF source returned insufficient weekly report rows")
    for row in data:
        if str(row.get("cftc_contract_market_code")) != "096742":
            raise ValueError("CFTC mismatched contract code")
    return sorted(data, key=lambda x: x["report_date_as_yyyy_mm_dd"])


def latest_eligible(rows, now):
    eligible = []
    for row in rows:
        asof = dt.date.fromisoformat(row["report_date_as_yyyy_mm_dd"][:10])
        if asof.weekday() != 1 or asof > now.date():
            continue
        allowed = dt.datetime.combine(asof + dt.timedelta(days=8), dt.time(9), UTC)
        if allowed <= now:
            eligible.append((asof, allowed, row))
    if len(eligible) < 2:
        raise ValueError("Need two eligible official CFTC reports")
    (previous_date, _, prev), (current_date, eligible_utc, latest) = eligible[-2:]
    gap = (current_date - previous_date).days
    if gap < 7 or gap > 14:
        raise ValueError("Missing CFTC previous report; week-on-week signal unknown")
    return {
        "CFTC_asof_date": current_date.isoformat(),
        "CFTC_previous_asof_date": previous_date.isoformat(),
        "eligible_utc": eligible_utc,
        "net_share": clean_ratio(latest),
        "net_change": clean_ratio(latest) - clean_ratio(prev),
        "report_id": str(latest.get("id", "")),
        "previous_report_id": str(prev.get("id", "")),
    }


def load_prices(path=DATA):
    raw = json.loads(Path(path).read_text())
    if raw.get("schema") != 1 or "dukascopy-node" not in raw.get("provider", ""):
        raise ValueError("Unknown historical price source")
    market = {}
    for pair in ("gbpusd", "eurusd", "usdjpy"):
        info = raw["prices"][pair]
        bid = {int(r[0]): tuple(r) for r in info["bid"]}
        ask = {int(r[0]): tuple(r) for r in info["ask"]}
        shared = sorted(set(bid).intersection(ask))
        if len(shared) < 200:
            raise ValueError("Too little aligned bid/ask history")
        for t in shared:
            if (not 0 < bid[t][1] <= ask[t][1] or
                    bid[t][2] < bid[t][3] or ask[t][2] < ask[t][3]):
                raise ValueError("Invalid historical ask/bid H1 candle")
        market[pair] = {"bid": bid, "ask": ask, "stamps": shared}
    return market


def bar(market, pair, side, when):
    timestamp = int(when.timestamp() * 1000)
    try:
        return market[pair][side][timestamp]
    except KeyError:
        raise ValueError(f"Missing exact completed {pair} {side} H1 quote for {when.isoformat()}") from None


def midclose(market, pair, when):
    return (bar(market, pair, "ask", when)[4] +
            bar(market, pair, "bid", when)[4]) / 2.


def momentum(market, pair, obs, hours):
    close = midclose(market, pair, obs)
    previous = midclose(market, pair, obs - dt.timedelta(hours=hours))
    return round(10000. * (close / previous - 1.), 2)


def five_day_range(market, obs):
    ends_at = int(obs.timestamp() * 1000)
    stamps = [t for t in market["gbpusd"]["stamps"]
              if ends_at - 120 * 3600000 <= t < ends_at]
    if len(stamps) != 120:
        raise ValueError("Missing hourly candles for 5d high-low range")
    high = max((market["gbpusd"]["bid"][t][2] +
                market["gbpusd"]["ask"][t][2]) / 2. for t in stamps)
    low = min((market["gbpusd"]["bid"][t][3] +
               market["gbpusd"]["ask"][t][3]) / 2. for t in stamps)
    return round((high - low) / PIP, 2)


def make_snapshot(report, market):
    signal = report["eligible_utc"]
    obs = signal - dt.timedelta(hours=1)
    b = bar(market, "gbpusd", "bid", obs)
    a = bar(market, "gbpusd", "ask", obs)
    delta = report["net_change"]
    if abs(delta) < .005:
        raise ValueError("CPU signal below .005 weekly delta threshold")
    snap = {
        "id": "cftc_gbpusd_" + report["CFTC_asof_date"],
        "utc_signal": signal.isoformat(),
        "CFTC_asof_date": report["CFTC_asof_date"],
        "CFTC_previous_asof_date": report["CFTC_previous_asof_date"],
        "CFTC_report_id": report["report_id"],
        "CFTC_contract_code": "096742",
        "CFTC_source": CFTC_URL,
        "base_side": "BUY" if delta > 0 else "SELL",
        "CFTC_lev_money_net_share": round(report["net_share"], 6),
        "CFTC_weekly_net_change": round(delta, 6),
        "GBPUSD_2d_momentum_bp": momentum(market, "gbpusd", obs, 48),
        "GBPUSD_5d_momentum_bp": momentum(market, "gbpusd", obs, 120),
        "GBPUSD_10d_momentum_bp": momentum(market, "gbpusd", obs, 240),
        "GBPUSD_5d_high_low_pips": five_day_range(market, obs),
        "EURUSD_5d_momentum_bp": momentum(market, "eurusd", obs, 120),
        "USDJPY_5d_momentum_bp": momentum(market, "usdjpy", obs, 120),
        "GBPUSD_last_completed_H1_range_pips": round(
            (a[2] + b[2] - a[3] - b[3]) / (2 * PIP), 2),
        "last_completed_H1_open_utc": obs.isoformat(),
        "not_a_live_trade": True,
    }
    # Consumer's conservative time checks remain active.
    forex_gpt.validate_snapshot(snap, signal + dt.timedelta(minutes=5))
    return snap


def initial_state():
    seed = json.loads(BOOTSTRAP.read_text())
    if seed.get("source") != "sealed 2026 historical after-cost CPU matched-trade experiment":
        raise ValueError("Unknown CPU historical-seed provenance")
    if len(seed.get("last_eight_2d_500GBP", [])) != 8:
        raise ValueError("Need exactly eight previously closed paper baseline PnL values")
    return {"schema": 1, "created_utc": utcnow().isoformat(), "updated_utc": utcnow().isoformat(),
            "bootstrapped_historical": seed, "signals": [], "runs": 0}


def state_load():
    if not LEDGER.exists():
        return initial_state()
    data = json.loads(LEDGER.read_text())
    if data.get("schema") != 1 or not isinstance(data.get("signals"), list):
        raise ValueError("Refusing malformed historical paper ledger")
    ids = [r["id"] for r in data["signals"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate paper signal IDs in ledger")
    return data


def write_run(state, result, write_state=True):
    state["runs"] += 1
    state["updated_utc"] = utcnow().isoformat()
    result.update({"generated_utc": utcnow().isoformat(),
                   "cpu_changed_by_gpt": False, "broker_orders_submitted": 0,
                   "live_trading_enabled": False, "paper_broker_orders": 0})
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    if write_state:
        LEDGER.write_text(json.dumps(state, indent=2) + "\n")
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print("FOREX_PAPER_STATUS", result.get("status"), "GPT",
          result.get("GPT_status", "NOT_CALLED"),
          "signals_in_ledger", len(state["signals"]),
          "orders=0")
    return result


def recent_closed_two_day(state, asof):
    seed = state["bootstrapped_historical"]
    vals = [(parse_dt(x["entry_utc"]), float(x["net_2d_500_funded_usd"]))
            for x in seed["last_eight_2d_500GBP"]]
    for row in state["signals"]:
        pnl = row.get("settlements", {}).get("2d_500")
        if pnl and pnl.get("status") == "closed":
            trade_entry = parse_dt(row["paper_entry_utc"])
            if trade_entry + dt.timedelta(days=2) <= asof:
                vals.append((trade_entry, float(pnl["net_usd"])))
    vals = [(d, x) for d, x in vals if d + dt.timedelta(days=2) <= asof]
    vals.sort(key=lambda z: z[0])
    return [round(x, 6) for d, x in vals[-8:]]


def accept_spread(market, at):
    buy = bar(market, "gbpusd", "ask", at)[1]
    sell = bar(market, "gbpusd", "bid", at)[1]
    spread = (buy - sell) / PIP
    if not 0 < spread <= 2.:
        raise ValueError("At intended 10UTC entry, spread outside approved <2pip window")
    return round(spread, 5)


def compute_trade(market, signal, days, units, stop_usd=None):
    entry = parse_dt(signal["paper_entry_utc"])
    exit_at = entry + dt.timedelta(days=days)
    direct = SIDE[signal["base_side"]]
    spread = accept_spread(market, entry)
    entry_px = float(bar(market, "gbpusd",
                     "ask" if direct > 0 else "bid", entry)[1])
    exit_px = float(bar(market, "gbpusd",
                    "bid" if direct > 0 else "ask", exit_at)[1])
    exit_reason = "calendar_hold"
    actual_exit = exit_at
    worst_adverse_quote = 0.
    hours = int((exit_at-entry).total_seconds() / 3600)
    if stop_usd is not None:
        stop_quote = stop_usd / units
        stop_level = entry_px - direct * stop_quote
    for h in range(hours + 1):
        moment = entry + dt.timedelta(hours=h)
        if moment > exit_at:
            break
        adverse = float(bar(market, "gbpusd",
                       "bid" if direct > 0 else "ask", moment)[3 if direct > 0 else 2])
        worst_adverse_quote = min(worst_adverse_quote, direct * (adverse - entry_px) * units)
        if stop_usd is not None and h < hours:
            touched = adverse <= stop_level if direct > 0 else adverse >= stop_level
            if touched:
                worst_open = float(bar(market, "gbpusd",
                          "bid" if direct > 0 else "ask", moment)[1])
                exit_px = min(stop_level, worst_open) if direct > 0 else max(stop_level, worst_open)
                actual_exit = moment
                exit_reason = "modeled_stop"
                break
    financing_usd = FINANCING_DAY_1000_GBP * units / 1000 * (
        (actual_exit-entry).total_seconds() / 86400)
    net = direct * (exit_px-entry_px) * units \
            - PIP * SLIP_PIPS_RT * units - COMMISSION_RT_USD - financing_usd
    return {
        "status": "closed", "net_usd": round(net, 6),
        "worst_adverse_quote_usd": round(worst_adverse_quote, 6),
        "spread_pips": spread, "reason": exit_reason,
        "exit_utc": actual_exit.isoformat(),
        "funding_assumed_usd": round(financing_usd, 5),
        "fixed_commission_rt_usd": COMMISSION_RT_USD,
        "extra_slippage_pips_rt": SLIP_PIPS_RT,
        "size_base_gbp": units, "intended_hold_calendar_days": days,
        "hypothetical": True,
    }


def weekly(state, market, now):
    if now.weekday() != 2 or not (9 <= now.hour < 10):
        return {"status": "OUTSIDE_WEEKLY_CFTC_SIGNAL_WINDOW",
                "reason": "Weekly model eligible on Wednesday 09:00-09:55 UTC only"}
    rows = fetch_cftc()
    report = latest_eligible(rows, now)
    if (now-report["eligible_utc"]) > dt.timedelta(minutes=55):
        return {"status": "STALE_CFTC_WEEKLY_WINDOW",
                "report_asof": report["CFTC_asof_date"]}
    if abs(report["net_change"]) < .005:
        return {"status": "CPU_NO_POSITIONING_SIGNAL",
                "CFTC_asof_date": report["CFTC_asof_date"],
                "weekly_net_change": round(report["net_change"], 6)}
    entryid = "cftc_gbpusd_" + report["CFTC_asof_date"]
    if any(r["id"] == entryid for r in state["signals"]):
        return {"status": "DUPLICATE_SIGNAL_SKIPPED", "signal_id": entryid}
    snap = make_snapshot(report, market)
    # Ensure actual data source's newest completed obs is < signal and
    # all values are backed by bid/ask, never placeholders.
    precheck = forex_gpt.validate_snapshot(snap, now)
    history = recent_closed_two_day(state, now)
    gate = (len(history) >= 4 and sum(history) > 0.)
    # Explain both CPU plans and only PAST closed trades to the GPT risk reviewer.
    # This is advice context, not an input to either CPU entry rule.
    snap["CPU_risk_context"] = {
        "five_day_1000_gbp_baseline_active": True,
        "two_day_500_gbp_baseline_gate_active": bool(gate),
        "last_eight_or_fewer_closed_two_day_500_gbp_usd": history,
        "recent_closed_two_day_500_gbp_net_usd": round(sum(history), 6),
        "planned_entry_utc": (report["eligible_utc"] + dt.timedelta(hours=1)).isoformat(),
        "modeled_commission_roundtrip_usd": COMMISSION_RT_USD,
        "modeled_extra_slippage_roundtrip_pips": SLIP_PIPS_RT,
        "modeled_financing_usd_day_per_1000_gbp": FINANCING_DAY_1000_GBP,
        "actual_broker_fills_available": False,
    }
    sample_sha = hashlib.sha256(json.dumps(snap, sort_keys=True).encode()).hexdigest()
    # Only the weekly GHA step has access to the OpenAI API secret.
    try:
        os.environ["SNAPSHOT_JSON"] = json.dumps(snap)
        if not 0 <= (utcnow() - report["eligible_utc"]).total_seconds() <= 55 * 60:
            raise RuntimeError("API risk-advice time budget expired")
        advisory = forex_gpt.run_paper()
        gpt_status = "SUCCESS_SHADOW"
        advice = advisory["GPT_advice"]
    except Exception as e:
        gpt_status = "FAILED_SHADOW_NO_CPU_CHANGE"
        advice = {"choice": "UNAVAILABLE", "risk_level": "unknown",
                  "confidence": 0.0, "risk_reason": type(e).__name__ + ": " + str(e)[:90]}
    finally:
        os.environ.pop("SNAPSHOT_JSON", None)
    # DO NOT fabricate entry quotes at Wednesday 10:00: they do not exist yet.
    entry = report["eligible_utc"] + dt.timedelta(hours=1)
    record = {
        "id": entryid, "base_side": snap["base_side"],
        "CFTC_asof_date": report["CFTC_asof_date"],
        "CFTC_report_id": report["report_id"],
        "CFTC_delta": snap["CFTC_weekly_net_change"],
        "snapshot_sha256": sample_sha,
        "snapshot": snap,
        "paper_entry_utc": entry.isoformat(),
        "cpu_2d_500_gate": {"recent_8_closed_sum_usd": round(sum(history), 5),
                             "trades_count": len(history), "approved": gate},
        "CPU_2d_500_active": bool(gate),
        "CPU_5d_1000_active": True,
        "gpt_status": gpt_status, "gpt_advice": advice,
        "gpt_applies_to_cpu": False,
        "settlements": {},
        "broker_orders": 0,
        "is_actual_broker_trade": False,
    }
    state["signals"].append(record)
    return {"status": "WEEKLY_CPU_AND_GPT_SHADOW_RECORDED",
            "signal_id": entryid,
            "side": snap["base_side"],
            "CPU_2d_500_gate": gate,
            "CPU_5d_1000_paper": True,
            "entry_planned_utc": entry.isoformat(),
            "snapshot_sha256": sample_sha,
            "GPT_status": gpt_status, "GPT_choice": advice["choice"],
            "GPT_risk": advice["risk_level"],
            "GPT_cost": advisory.get("token_usage", {}) if gpt_status=="SUCCESS_SHADOW" else {},
            "note": "Future entry quote unavailable. CPU and GPT stay simulated / no actual order."}


def settle(state, market, now):
    updated = 0
    awaiting = []
    for s in state["signals"]:
        entry = parse_dt(s["paper_entry_utc"])
        for name, days, units in (
            ("2d_500", 2, 500), ("5d_1000", 5, 1000),
            ("2d_1000", 2, 1000),
            ("5d_500_gpt_adaptive", 5, 500),
            ("2d_500_stop3", 2, 500),
            ("5d_1000_stop5", 5, 1000)):
            if name in s["settlements"]:
                continue
            due = entry + dt.timedelta(days=days)
            if now < due + dt.timedelta(hours=1):
                awaiting.append(name)
                continue
            try:
                result = compute_trade(market, s, days, units,
                    stop_usd=3. if name == "2d_500_stop3" else
                             5. if name == "5d_1000_stop5" else None)
            except ValueError as e:
                # Missing quotes/source outage isn't evidence of a loss.
                awaiting.append(name + ": " + str(e)[:100])
                continue
            s["settlements"][name] = result
            updated += 1
    return {"status": "SETTLEMENT_UPDATED" if updated else "NO_DUE_SETTLEMENTS",
            "newly_settled_scenarios": updated,
            "still_missing_or_not_due": len(awaiting),
            "summary": analyze(state)}


def curve_stats(values):
    vals = [float(x) for x in values]
    equity = peak = 1000.0
    dd = 0.0
    for x in vals:
        equity += x
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    neg = [x for x in vals if x < 0]
    return {
        "n_closed": len(vals),
        "gross_losses_usd": round(-sum(neg), 4),
        "net_usd": round(sum(vals), 4),
        "worst_trade_usd": round(min(vals, default=0.), 4),
        "max_closed_equity_drawdown_usd": round(dd, 4),
        "losing_trades": len(neg),
    }


def analyze(state):
    done2 = []
    done5 = []
    veto = []
    stop = []
    for s in sorted(state["signals"], key=lambda r: r["paper_entry_utc"]):
        a = s["settlements"].get("2d_500")
        b = s["settlements"].get("5d_1000")
        c = s["settlements"].get("2d_500_stop3")
        if a and a.get("status")=="closed":
            if s.get("CPU_2d_500_active"):
                done2.append(a["net_usd"])
                if c and c.get("status")=="closed":
                    stop.append(c["net_usd"])
                gpt_action=s.get("gpt_advice",{}).get("choice")
                if gpt_action in ("SKIP", "KEEP_2D","KEEP_5D"):
                    veto.append(0. if gpt_action=="SKIP" else a["net_usd"])
        if b and b.get("status")=="closed":
            done5.append(b["net_usd"])
    matched_cpu = []
    matched_gpt_adaptive = []
    vetoed_winners = 0
    vetoed_losers = 0
    vetoed_gain_usd = 0.
    vetoed_loss_usd = 0.
    for s in sorted(state["signals"], key=lambda r: r["paper_entry_utc"]):
        if not s.get("CPU_2d_500_active"):
            continue
        settled = s["settlements"]
        base = settled.get("2d_500")
        advice = s.get("gpt_advice",{}).get("choice")
        if not base or base.get("status")!="closed":
            continue
        pnl = float(base["net_usd"])
        if advice == "SKIP":
            vetoed_winners += (pnl > 0)
            vetoed_losers += (pnl < 0)
            vetoed_gain_usd += max(pnl, 0.)
            vetoed_loss_usd += max(-pnl, 0.)
            matched_cpu.append(pnl)
            matched_gpt_adaptive.append(0.)
        elif advice == "KEEP_2D":
            matched_cpu.append(pnl)
            matched_gpt_adaptive.append(pnl)
        elif advice == "KEEP_5D":
            alt = settled.get("5d_500_gpt_adaptive")
            if alt and alt.get("status")=="closed":
                matched_cpu.append(pnl)
                matched_gpt_adaptive.append(float(alt["net_usd"]))
    return {
        "CPU_2d_500": curve_stats(done2),
        "CPU_5d_1000": curve_stats(done5),
        "GPT_veto_2d_500_shadow": curve_stats(veto),
        "CPU_2d_500_3usd_stop_shadow": curve_stats(stop),
        "CPU_2d_500_matched_matured": curve_stats(matched_cpu),
        "GPT_adaptive_2or5d_500_matched_matured": curve_stats(matched_gpt_adaptive),
        "GPT_skipped_winning_trades": vetoed_winners,
        "GPT_skipped_losing_trades": vetoed_losers,
        "GPT_skipped_positive_gains_usd": round(vetoed_gain_usd, 4),
        "GPT_avoided_gross_losses_usd": round(vetoed_loss_usd, 4),
        "GPT_has_order_override_authority": False,
        "GPT_CPU_combined_risk_audit": shadow_evaluation.evaluate(state),
        "note": "Dukascopy quotes + assumed fees, spreads and financing, not broker fills. Drawdown at trade closes only; not MTM. Adaptive metrics use only matched mature trades."
    }


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--task", choices=("status", "weekly", "settle", "selftest"), required=True)
    cli.add_argument("--market", default=str(DATA))
    opts = cli.parse_args()
    if opts.task == "selftest":
        print("SELFTEST_IMPORT_OK")
        return 0
    state = state_load()
    now = utcnow()
    if opts.task == "status":
        out = {"status": "CPU_GPT_PIPELINE_CONFIGURED",
               "ledger_signals": len(state["signals"]),
               "summary": analyze(state),
               "key_resolved_only_for_weekly_step": True}
    else:
        market = load_prices(opts.market)
        out = weekly(state, market, now) if opts.task == "weekly" else settle(state, market, now)
    write_run(state, out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, RuntimeError) as e:
        print("FOREX PAPER PIPELINE FAILED CLOSED: "+type(e).__name__+": "+str(e)[:260],
              file=sys.stderr)
        print("No actual orders; missing data is NOT interpreted as a losing trade.",
              file=sys.stderr)
        raise SystemExit(2)

