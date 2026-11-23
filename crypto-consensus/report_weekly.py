"""Weekly, unreset ETH forward-paper evidence from observed account equity.

No orders, no exchange credentials, no invented missing observations.
A calendar-week return is published only if hourly history covers BOTH
boundaries without long gaps. Incomplete weeks display observations but
never a certified weekly return. All timestamps are UTC.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

UTC = timezone.utc
MAX_INTERVAL_HOURS = 2.5
BOUNDARY_TOLERANCE_HOURS = 1.5


def timestamp(value: str) -> datetime:
    t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError("Naive timestamp in paper ledger")
    return t.astimezone(UTC)


def numeric(value) -> float:
    f = float(value)
    if not math.isfinite(f):
        raise ValueError("Nonfinite accounting value")
    return f


def week_start(t: datetime) -> datetime:
    midnight = t.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight - timedelta(days=t.weekday())


def analyse(state: dict) -> dict:
    points = []
    for item in state.get("equity_history", []):
        t = timestamp(item["utc"])
        equity = numeric(item["equity_usd"])
        if equity <= 0:
            raise ValueError("Nonpositive account equity")
        points.append((t, equity, item))
    if any(points[i][0] <= points[i - 1][0] for i in range(1, len(points))):
        raise ValueError("Paper observations must be unique and strictly chronological")
    by_week = defaultdict(list)
    for p in points:
        by_week[week_start(p[0])].append(p)

    closed = defaultdict(list)
    for trade in state.get("trades", []):
        if "exited" not in trade:
            raise ValueError("Missing trade exit time")
        numeric(trade["net_usd"])
        closed[week_start(timestamp(trade["exited"]))].append(trade)

    as_of = timestamp(state["last_observation"]) if state.get("last_observation") else (
        points[-1][0] if points else None
    )
    if points and as_of < points[-1][0]:
        raise ValueError("Account observation timestamp precedes equity history")
    weeks = []
    for begin in sorted(by_week):
        samples = by_week[begin]
        finish = begin + timedelta(days=7)
        gaps = [(b[0] - a[0]).total_seconds() / 3600.0 for a, b in zip(samples, samples[1:])]
        maximum_gap = max(gaps, default=0.0)
        reached_week_end = as_of is not None and as_of >= finish
        boundary_coverage = (
            (samples[0][0] - begin).total_seconds() <= BOUNDARY_TOLERANCE_HOURS * 3600
            and (finish - samples[-1][0]).total_seconds() <= BOUNDARY_TOLERANCE_HOURS * 3600
        )
        continuous = (reached_week_end and boundary_coverage
                      and maximum_gap <= MAX_INTERVAL_HOURS)
        values = [v for _, v, _ in samples]
        high = values[0]
        drawdown = 0.0
        for value in values:
            high = max(high, value)
            drawdown = max(drawdown, (high - value) / high * 100)
        weekly_trades = closed.get(begin, [])
        winning = sum(numeric(t["net_usd"]) > 0 for t in weekly_trades)
        losing = sum(numeric(t["net_usd"]) < 0 for t in weekly_trades)

        def cum_change(key):
            if key not in samples[0][2] or key not in samples[-1][2]:
                return None
            return round(numeric(samples[-1][2][key]) -
                         numeric(samples[0][2][key]), 6)

        week = {
            "week_start_utc": begin.date().isoformat(),
            "week_end_exclusive_utc": finish.date().isoformat(),
            "status": "verified_observation_coverage" if continuous else (
                "in_progress" if not reached_week_end else "incomplete_data"),
            "samples": len(samples),
            "first_observation": samples[0][0].isoformat(),
            "last_observation": samples[-1][0].isoformat(),
            "largest_observation_gap_hours": round(maximum_gap, 3),
            "first_observed_equity_usd": round(values[0], 6),
            "last_observed_equity_usd": round(values[-1], 6),
            "observed_equity_change_usd": round(values[-1] - values[0], 6),
            "observed_equity_change_pct": round((values[-1] / values[0] - 1) * 100, 4),
            "qualifying_weekly_return_pct": (
                round((values[-1] / values[0] - 1) * 100, 4) if continuous else None),
            "observed_max_drawdown_pct": round(drawdown, 4),
            "closed_trades": len(weekly_trades),
            "wins": winning,
            "losses": losing,
            "realized_trade_net_usd": round(
                sum(numeric(t["net_usd"]) for t in weekly_trades), 6),
            "estimated_fee_change_usd": cum_change("fees_usd"),
            "estimated_funding_change_usd": cum_change("funding_usd"),
            "last_observed_unrealized_usd": (
                numeric(samples[-1][2]["unrealized_usd"])
                if "unrealized_usd" in samples[-1][2] else None),
            "positions_carried_across_boundary": "unknown",
        }
        weeks.append(week)

    qualifying = [w for w in weeks if w["qualifying_weekly_return_pct"] is not None]
    return {
        "mode": "forward_hourly_observation_paper_only",
        "account_restarts_between_weeks": False,
        "weekly_starting_balance_reset": False,
        "capital_currency": "USD",
        "as_of_utc": as_of.isoformat() if as_of else None,
        "all_time_observation_count": len(points),
        "observed_calendar_weeks": len(weeks),
        "fully_covered_weeks": len(qualifying),
        "weeks": weeks,
        "warnings": [
            "This is a simulated paper ledger, not exchange fills or audited live P&L.",
            "Returns are measured between first/last hourly observations, not exact boundary prices.",
            "Weeks missing observations or either boundary have no qualifying return.",
            "Hourly monitoring can miss intrahour stops, price gaps and actual funding settlement.",
            "Realized trade P&L includes model fees and funding; open-position P&L is sampled.",
        ],
    }


def render(report: dict) -> str:
    lines = [
        "# ETH crypto consensus — uninterrupted weekly PAPER accounting", "",
        "**No real orders. No weekly wallet resets.** "
        "A week only qualifies when both boundaries and hourly observation coverage pass.", "",
        "| UTC week starting | Coverage | Sampled equity change | Return if complete | "
        "Closed W/L | Realized net | Sampled drawdown | Fees* | Funding* |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for w in report["weeks"]:
        ret = w["qualifying_weekly_return_pct"]
        fees = w["estimated_fee_change_usd"]
        fund = w["estimated_funding_change_usd"]
        lines.append(
            "| {} | {} ({} obs) | {:+.3f} USD | {} | {}/{} | {:+.3f} USD | "
            "{:.3f}% | {} | {} |".format(
                w["week_start_utc"], w["status"], w["samples"],
                w["observed_equity_change_usd"],
                f"{ret:+.3f}%" if ret is not None else "Not established",
                w["wins"], w["losses"], w["realized_trade_net_usd"],
                w["observed_max_drawdown_pct"],
                f"{fees:+.4f} USD" if fees is not None else "Unavailable",
                f"{fund:+.4f} USD" if fund is not None else "Unavailable"
            )
        )
    if not report["weeks"]:
        lines.append("| No observations yet | No evidence | — | — | — | — | — | — | — |")
    lines.extend([
        "",
        f'**Complete, sufficiently observed weeks:** {report["fully_covered_weeks"]}.',
        f'**Latest snapshot (UTC):** {report["as_of_utc"] or "none"}.',
        "",
        "A sampled change in an incomplete week is **not** a full-week return. "
        "The drawdown column is based only on sampled hourly account equity. "
        "Realized net is attributed to the week a modeled trade closes, while "
        "unrealized equity stays in the hourly equity snapshots.",
        "",
        "*Fee and funding columns are changes in cumulative model accounting "
        "between the first and last snapshot of each week. "
        "They are **already included** in modeled net equity; do not subtract twice.",
        "",
        "This report contains no real trades, exchange stop acknowledgments, "
        "or proof of future profitability.",
        ""
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    report = analyse(json.loads(Path(args.state).read_text()))
    Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(args.markdown).write_text(render(report))
    print(json.dumps({"weeks": report["observed_calendar_weeks"],
                      "qualified": report["fully_covered_weeks"],
                      "as_of": report["as_of_utc"]}))


if __name__ == "__main__":
    main()
