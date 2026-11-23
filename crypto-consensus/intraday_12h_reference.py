"""Same-date 12-hour guarded baseline for 2026 intraday timeframe experiment.

One independent $150 baseline account per coin. This is NOT a portfolio and
must not be equated to the 2026 year-to-date 12h report with different dates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

from intraday_research_report import summarize

COINS=("ETH","SOL","BTC")
FEES=("baseline","stress")
MODEL="GuardedConsensusETH"


def open_result(root,coin,fee_mode):
    parent=Path(root)/fee_mode/coin
    archives=list(parent.glob("*.zip"))
    if len(archives)!=1:
        raise ValueError(f"Expected exactly one baseline ZIP {parent}")
    with ZipFile(archives[0]) as z:
        matches=[]
        for path in z.namelist():
            if path.endswith(".json") and not path.endswith(".meta.json"):
                obj=json.loads(z.read(path))
                if isinstance(obj,dict) and MODEL in obj.get("strategy",{}):
                    matches.append(obj["strategy"][MODEL])
    if len(matches)!=1:
        raise ValueError("Unverifiable original protected strategy export")
    return summarize(matches[0],coin,"12h",8,"Strict")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--md",required=True)
    a=p.parse_args()
    data={coin:{fee:open_result(a.root,coin,fee) for fee in FEES}
          for coin in COINS}
    report={
        "mode":"same_interval_12h_historical_scenario_benchmark",
        "no_orders":True,
        "same_dates_as_intraday":"2026-09-01 to 2026-11-22 inclusive",
        "starting_usd_per_coin":150,
        "original_guarded_strategy":True,
        "normal_fee_per_side":.0005,
        "stress_fee_per_side":.0015,
        "coin_runs":data,
        "warnings":[
            "Each coin/timeframe uses a new paper wallet, not an aggregated portfolio.",
            "This uses exactly the 83-day intraday test interval, not 2026 year-to-date.",
            "Backtest equity drawdown omits some intrabar adverse outcomes.",
            "An end-of-test forced exit is not a natural strategy exit.",
            "Higher fee is a stress proxy, not measured market spread and slippage.",
        ],
    }
    Path(a.json).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    lines=[
        "# Fair 12-hour comparison on the same 83-day market interval",
        "",
        "No real exchange orders. 8/10 frozen original protected strategy. "
        "One independent $150 wallet for ETH, SOL and BTC each. "
        "September 1 to November 22, 2026, same 83 days as the "
        "1h/15m/5m research. Normal fee .05% per side, stress .15%.",
        "",
        "| Coin | Normal return | Higher-cost return | Trades | "
        "Trades/week | Wins/Losses | Reported max DD | Artificial final exit USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for coin in COINS:
        norm=data[coin]["baseline"]
        stress=data[coin]["stress"]
        lines.append(
            f"| {coin} | {norm['return_pct']:+.3f}% | "
            f"{stress['return_pct']:+.3f}% | {norm['closed_trades']} | "
            f"{norm['trades_per_week']:.2f} | "
            f"{norm['winning_trades']}/{norm['losing_trades']} | "
            f"{norm['backtest_reported_max_drawdown_pct']:.3f}% | "
            f"{norm['forced_end_net_usd']:+.3f} |")
        print("SAME_DATE_12H_REFERENCE",coin,
              "net_pct",norm["return_pct"],
              "stress_pct",stress["return_pct"],
              "trades",norm["closed_trades"],
              "trades_per_week",norm["trades_per_week"],
              "forced_close",norm["forced_end_net_usd"])
    lines += [
        "",
        "The 12h wallet begins with $150 on September 1 instead of carrying "
        "previous-period positions. For fair scenario comparison, the "
        "fast timeframe models also start with separate $150 accounts. "
        "The forced terminal close is shown explicitly.",
        "",
        "Crypto signals can be checked every five minutes without becoming "
        "profitable or executable every five minutes. Fees, minimum size "
        "and protection cooldowns still limit actionable trades.",
        "",
    ]
    Path(a.md).write_text("\n".join(lines)+"\n")


if __name__=="__main__":
    main()
