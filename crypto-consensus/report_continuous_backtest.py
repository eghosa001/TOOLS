"""Audit one continuous (NEVER weekly-reset) Freqtrade futures backtest.

Per-week figures are CLOSED trade net profit attributed to close week, NOT
mark-to-market weekly equity returns. Continuous Freqtrade account drawdown
comes from the full backtest. Force-closed end-of-test positions are flagged.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from zipfile import ZipFile

UTC = timezone.utc
STRATEGY = "GuardedConsensusETH"


def date_time(x):
    t = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t.astimezone(UTC)


def amount(x):
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("NaN or infinite backtest financial value")
    return v


def read_export(folder: Path) -> dict:
    paths = list(folder.glob("backtest-result-*.zip"))
    if len(paths) != 1:
        raise ValueError(f"Expected exactly one Freqtrade export ZIP, got {len(paths)}")
    with ZipFile(paths[0]) as archive:
        matches = []
        for name in archive.namelist():
            if not name.endswith(".json") or name.endswith(".meta.json"):
                continue
            candidate = json.loads(archive.read(name))
            if isinstance(candidate, dict) and STRATEGY in candidate.get("strategy", {}):
                matches.append(candidate)
        if len(matches) != 1:
            raise ValueError("Freqtrade strategy result missing or ambiguous")
        return matches[0]


def analyse(backtest: dict, begin: str, end: str) -> dict:
    strategy = backtest["strategy"][STRATEGY]
    start = date_time(begin).replace(hour=0, minute=0, second=0, microsecond=0)
    finish = date_time(end).replace(hour=0, minute=0, second=0, microsecond=0)
    if finish <= start:
        raise ValueError("Empty historical test interval")
    starting_capital = amount(strategy["starting_balance"])
    final_capital = amount(strategy["final_balance"])
    if starting_capital <= 0:
        raise ValueError("Invalid initial balance")
    result_trades = []
    fees_total = 0.0
    has_complete_fee_data = True
    funding_total = 0.0
    has_complete_funding_data = True
    for item in strategy["trades"]:
        opening = date_time(item["open_date"])
        closing = date_time(item["close_date"])
        if not start <= opening <= closing <= finish:
            raise ValueError("Trade timestamp outside the requested continuous test")
        pnl = amount(item["profit_abs"])
        fees = None
        if all(k in item and item[k] is not None for k in
               ("amount", "open_rate", "close_rate", "fee_open", "fee_close")):
            fees = (amount(item["amount"]) * (
                amount(item["open_rate"]) * amount(item["fee_open"]) +
                amount(item["close_rate"]) * amount(item["fee_close"])))
            fees_total += fees
        else:
            has_complete_fee_data = False
        if item.get("funding_fees") is not None:
            funding_total += amount(item["funding_fees"])
        else:
            has_complete_funding_data = False
        result_trades.append({
            "opened": opening, "closed": closing, "net": pnl,
            "fees": fees, "funding": item.get("funding_fees"),
            "exit_reason": item.get("exit_reason", "unknown"),
        })

    total_net = sum(t["net"] for t in result_trades)
    if abs(total_net - (final_capital - starting_capital)) > .05:
        raise ValueError("Trade net sum does not reconcile to Freqtrade final account balance")
    rows = []
    day = start.date() - timedelta(days=start.weekday())
    while datetime.combine(day, datetime.min.time(), UTC) < finish:
        week_start = datetime.combine(day, datetime.min.time(), UTC)
        week_end = week_start + timedelta(days=7)
        # Freqtrade may force-close at the exact exclusive test-end boundary.
        # Attribute that closure to the final tested week, not to an untested future week.
        this_week = [t for t in result_trades if week_start <=
                     min(t["closed"], finish - timedelta(microseconds=1)) < week_end]
        open_at_end = sum(t["opened"] < week_end < t["closed"] for t in result_trades)
        rows.append({
            "week_start_utc": day.isoformat(),
            "week_end_exclusive_utc": week_end.date().isoformat(),
            "is_partial_interval": week_start < start or week_end > finish,
            "closed_trades": len(this_week),
            "winning_trades": sum(t["net"] > 0 for t in this_week),
            "losing_trades": sum(t["net"] < 0 for t in this_week),
            "closed_net_profit_usd": round(sum(t["net"] for t in this_week), 6),
            "open_positions_crossed_week_boundary": open_at_end,
            "force_closed_trades": sum(t["exit_reason"] == "force_exit"
                                       for t in this_week),
        })
        day += timedelta(days=7)
    if sum(r["closed_trades"] for r in rows) != len(result_trades):
        raise ValueError("Closed trades missing from week attribution")
    if abs(sum(r["closed_net_profit_usd"] for r in rows) - total_net) > .05:
        raise ValueError("Week P&L sum fails reconciliation")
    return {
        "mode": "single_continuous_historical_freqtrade_backtest",
        "real_exchange_orders": False,
        "weekly_reset": False,
        "starting_balance_usd": starting_capital,
        "final_balance_usd": final_capital,
        "net_profit_usd": round(total_net, 6),
        "net_return_pct": round(100 * total_net / starting_capital, 4),
        "total_closed_trades": len(result_trades),
        "wins": sum(t["net"] > 0 for t in result_trades),
        "losses": sum(t["net"] < 0 for t in result_trades),
        "end_of_test_forced_exits": sum(t["exit_reason"] == "force_exit"
                                        for t in result_trades),
        "full_period_max_drawdown_pct": (
            round(100 * amount(strategy["max_drawdown_account"]), 4)
            if strategy.get("max_drawdown_account") is not None else None),
        "approximate_trade_fees_usd": (
            round(fees_total, 6) if has_complete_fee_data else None),
        "backtest_reported_funding_total_raw_usd": (
            round(funding_total, 6) if has_complete_funding_data else None),
        "begin_inclusive_utc": start.isoformat(),
        "end_exclusive_utc": finish.isoformat(),
        "weeks": rows,
        "warnings": [
            "Weekly values are net profits on closed trades; NOT weekly equity returns.",
            "Open-position unrealized profit/loss can span weeks; it is NOT zero when no trades close.",
            "Only the full-period Freqtrade account drawdown is reported; week drawdowns are not invented.",
            "A forced close at the historical interval end is not an organic exit signal.",
            "Fees, funding and liquidation simulation depend on Freqtrade and historical data quality.",
            "Do not combine these historical returns with forward PAPER wallet returns.",
        ],
    }


def markdown(report):
    lines = [
        "# ETH — uninterrupted protected historical futures audit", "",
        "One Freqtrade wallet, one continuous run, no weekly reset; "
        "12-hour candles, historical Kraken Futures mark/funding data.", "",
        f'**Backtested net result:** {report["net_profit_usd"]:+.3f} USD '
        f'({report["net_return_pct"]:+.3f}%) on '
        f'{report["starting_balance_usd"]:.2f} USD.', "",
        f'**Closed trades:** {report["total_closed_trades"]} '
        f'({report["wins"]} wins, {report["losses"]} losses); '
        f'**forced test-end exits:** {report["end_of_test_forced_exits"]}.',
        f'**Full-period Freqtrade drawdown:** '
        f'{report["full_period_max_drawdown_pct"]}% (not weekly).', "",
        "| UTC week starting | Closed W/L | Realized net (USD) | "
        "Trades carried across week-end | Forced closes |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in report["weeks"]:
        lines.append(
            f'| {r["week_start_utc"]}{" (partial)" if r["is_partial_interval"] else ""}'
            f' | {r["winning_trades"]}/{r["losing_trades"]} '
            f'| {r["closed_net_profit_usd"]:+.3f} '
            f'| {r["open_positions_crossed_week_boundary"]} '
            f'| {r["force_closed_trades"]} |')
    lines.extend([
        "", "**Interpretation:** A zero-realized-profit week can still have "
        "material unrealized position losses. These columns are not "
        "full-equity weekly profitability claims.",
        "", "Fees and funding are already reflected in Freqtrade trade net "
        "profit. Do not subtract them again. Reported trade-fee estimates "
        f'(if complete): {report["approximate_trade_fees_usd"]}; '
        "recorded funding field total (if complete): "
        f'{report["backtest_reported_funding_total_raw_usd"]}.',
        "", "Weekly mark-to-market equity and intrahour risks are instead "
        "tracked, with coverage flags, by the separate forward PAPER ledger.",
        "", "No live trading, no verified exchange-side stop orders.", ""
    ])
    return "\n".join(lines)


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--results-dir", required=True)
    arg.add_argument("--begin", required=True)
    arg.add_argument("--end", required=True)
    arg.add_argument("--json", required=True)
    arg.add_argument("--markdown", required=True)
    opt = arg.parse_args()
    report = analyse(read_export(Path(opt.results_dir)), opt.begin, opt.end)
    Path(opt.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(opt.markdown).write_text(markdown(report))
    print(json.dumps({k: report[k] for k in
          ("net_profit_usd", "net_return_pct", "total_closed_trades",
           "wins", "losses", "full_period_max_drawdown_pct")}))


if __name__ == "__main__":
    main()
