"""Pre-registered, PAPER-ONLY loss-control experiment review.

No fitting, price retrieval, exchange order routing or invented weekly equity.
Read exact Freqtrade trade exports. Full window, train and holdout results use
SEPARATE wallets only to compare scenarios; the production account is never
reset and original GuardedConsensusETH remains unchanged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from zipfile import ZipFile

BASELINE = "GuardedConsensusETH"
CANDIDATES = [
    "ResearchVotesConfirmedETH",
    "ResearchTrendRegimeETH",
    "ResearchConfirmedTrendETH",
    "ResearchTightStopETH",
    "ResearchEarlyBreakevenETH",
]
WINDOWS = ("train", "holdout", "full")


def read_one(root: Path, window: str, strategy: str) -> dict:
    folder = root / window / strategy
    files = list(folder.glob("*.zip"))
    if len(files) != 1:
        raise ValueError(f"Wrong number of result ZIPs: {folder}: {len(files)}")
    with ZipFile(files[0]) as archive:
        data = []
        for name in archive.namelist():
            if name.endswith(".json") and not name.endswith(".meta.json"):
                obj = json.loads(archive.read(name))
                if isinstance(obj, dict) and strategy in obj.get("strategy", {}):
                    data.append(obj["strategy"][strategy])
        if len(data) != 1:
            raise ValueError(f"Result missing/ambiguous in {files[0]}")
    s = data[0]
    trades = s["trades"]
    balance = float(s["starting_balance"])
    close_balance = float(s["final_balance"])
    net = round(sum(float(t["profit_abs"]) for t in trades), 6)
    if abs((close_balance - balance) - net) > .05:
        raise ValueError(f"{strategy}/{window} balance reconciliation failed")
    losses = []
    for t in trades:
        if float(t["profit_abs"]) < 0:
            losses.append({
                "opened_utc": t.get("open_date"),
                "closed_utc": t.get("close_date"),
                "side": "short" if t.get("is_short", False) else "long",
                "net_usd": round(float(t["profit_abs"]), 6),
                "exit": t.get("exit_reason"),
                "entry_rate": t.get("open_rate"),
                "exit_rate": t.get("close_rate"),
                "entry_tag": t.get("enter_tag"),
            })
    forced = [t for t in trades if t.get("exit_reason") == "force_exit"]
    max_dd = s.get("max_drawdown_account")
    if max_dd is None:
        raise ValueError(f"{strategy}/{window} missing actual account drawdown")
    return {
        "strategy": strategy,
        "window": window,
        "starting_usd": balance,
        "ending_usd": round(close_balance, 6),
        "net_usd": net,
        "return_pct": round((close_balance / balance - 1) * 100, 4),
        "max_drawdown_pct": round(float(max_dd) * 100, 4),
        "closed_trades": len(trades),
        "wins": sum(float(t["profit_abs"]) > 0 for t in trades),
        "losses": len(losses),
        "losing_trades": losses,
        "net_forced_exit_usd": round(sum(float(t["profit_abs"]) for t in forced), 6),
        "forced_exits": len(forced),
        "loss_usd_total": round(sum(float(t["profit_abs"]) for t in trades
                                     if float(t["profit_abs"]) < 0), 6),
        "win_usd_total": round(sum(float(t["profit_abs"]) for t in trades
                                    if float(t["profit_abs"]) > 0), 6),
        "exit_reasons": {
            r: sum(t.get("exit_reason") == r for t in trades)
            for r in sorted(set(t.get("exit_reason", "unknown") for t in trades))
        },
    }


def qualifies(rows: dict, candidate: str):
    baseline = rows[BASELINE]
    option = rows[candidate]
    train_base, train = baseline["train"], option["train"]
    hold_base, hold = baseline["holdout"], option["holdout"]
    full_base, full = baseline["full"], option["full"]

    # Strict predeclared rules; modest buffer covers marginal numerical errors.
    conditions = {
        "training_profit_positive": train["net_usd"] > 0,
        "training_profit_retained_80pct": train["net_usd"] >= .80 * max(0, train_base["net_usd"]),
        "training_fewer_losses": train["losses"] < train_base["losses"],
        "training_drawdown_not_higher": train["max_drawdown_pct"] <= train_base["max_drawdown_pct"] + .05,
        "holdout_profit_positive": hold["net_usd"] > 0,
        "holdout_profit_retained_80pct": hold["net_usd"] >= .80 * max(0, hold_base["net_usd"]),
        "holdout_loss_count_not_higher": hold["losses"] <= hold_base["losses"],
        "holdout_drawdown_not_higher": hold["max_drawdown_pct"] <= hold_base["max_drawdown_pct"] + .05,
        "full_profit_retained_90pct": full["net_usd"] >= .90 * max(0, full_base["net_usd"]),
        "full_fewer_losses": full["losses"] < full_base["losses"],
        "full_drawdown_not_higher": full["max_drawdown_pct"] <= full_base["max_drawdown_pct"] + .05,
    }
    return {
        "conditions": conditions, "accepted": all(conditions.values())
    }


def report(results):
    rows = {strat: {w: read_one(results, w, strat) for w in WINDOWS}
            for strat in [BASELINE, *CANDIDATES]}
    verdicts = {s: qualifies(rows, s) for s in CANDIDATES}
    passing = [s for s in CANDIDATES if verdicts[s]["accepted"]]
    # Important: do not announce a winner if there is no cross-period pass.
    # Cross-validation after inspecting many candidates is still weak evidence.
    winner = max(passing, key=lambda x: (rows[x]["full"]["net_usd"],
                                          -rows[x]["full"]["max_drawdown_pct"])) if passing else None
    return {
        "mode": "offline_historical_research_only",
        "original_strategy_preserved": True,
        "no_real_orders": True,
        "fee_per_side": .0005,
        "training_timerange": "20260101-20260701",
        "held_out_timerange": "20260701-20261123",
        "full_timerange": "20260101-20261123",
        "selection_rules": "Predeclared before trade outcomes; positive and retained profit, fewer losses, drawdown no worse",
        "baseline_and_candidates": rows,
        "promotion_tests": verdicts,
        "passing_candidates": passing,
        "suggested_research_candidate": winner,
        "warning": (
            "Even when a candidate passes, its observed past advantage is not "
            "proof of future profit. Holdout is repeatedly examined across five "
            "predeclared alternatives. Backtesting uses 12h OHLC and estimates "
            "fills; smaller timeframes and forward paper results required."
        ),
    }


def markdown(r: dict) -> str:
    lines = [
        "# Protected ETH loss-week reduction — controlled historical comparisons",
        "",
        "**No live trading. Original GuardedConsensusETH stays unchanged.**",
        "These results are modelled in Freqtrade on actual Kraken Futures "
        "historical prices, mark and funding. 12-hour bars cannot prove real "
        "intrabar stop execution.",
        "",
        "Train: Jan 1–Jun 30, 2026; held-out: Jul 1–Nov 22, 2026. "
        "Full: Jan 1–Nov 22, 2026. These are independent testing windows, "
        "not a continuous forward account.",
        "",
        "| Candidate | Train profit | Train losses | Holdout profit | Holdout losses | "
        "Full profit | Full drawdown | Full losses | Cross-period pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    rows = r["baseline_and_candidates"]
    for name in [BASELINE, *CANDIDATES]:
        a, b, c = (rows[name][w] for w in WINDOWS)
        mark = "Baseline" if name == BASELINE else (
            "PASS" if r["promotion_tests"][name]["accepted"] else "Reject")
        lines.append("| {} | {:+.2f} USD | {} | {:+.2f} USD | {} | "
                     "{:+.2f} USD | {:.2f}% | {} | {} |".format(
                         name, a["net_usd"], a["losses"], b["net_usd"],
                         b["losses"], c["net_usd"], c["max_drawdown_pct"],
                         c["losses"], mark))
    lines.extend(["", "## Original baseline losing trades (one uninterrupted account)", ""])
    for t in rows[BASELINE]["full"]["losing_trades"]:
        lines.append("- {} {} → {}: {:+.3f} USD, {}, exit {}".format(
            t["side"], t["opened_utc"], t["closed_utc"],
            t["net_usd"], t["entry_rate"], t["exit"]))
    lines.extend(["",
                  "**Predeclared gate:** Training must reduce losing trades and "
                  "retain at least 80% of training net profit without more "
                  "drawdown; held-out profit must stay positive, retain at least "
                  "80% of baseline, and not increase loss count or drawdown; "
                  "full-window profit must retain at least 90%, reduce loss count "
                  "and not increase drawdown. This is a strict research filter, "
                  "not a guarantee.",
                  "",
                  "**Candidate meeting all gates:** " +
                  (r["suggested_research_candidate"] or "None"),
                  "",
                  "Fees and funding are already inside net profit. A forced close "
                  "at a backtest endpoint is not a natural exit. Results exclude "
                  "true exchange slippage and exchange-held stops. "
                  "A clean forward paper run and finer-candle execution audits "
                  "remain necessary before deployment.", ""])
    return "\n".join(lines)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--results-root", required=True)
    a.add_argument("--output-json", required=True)
    a.add_argument("--output-md", required=True)
    opts = a.parse_args()
    result = report(Path(opts.results_root))
    Path(opts.output_json).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    Path(opts.output_md).write_text(markdown(result))
    print(json.dumps({
        "summary": {
            k: {
                w: {field: result["baseline_and_candidates"][k][w][field] for field in (
                    "net_usd", "return_pct", "max_drawdown_pct", "wins", "losses",
                    "forced_exits"
                )}
                for w in WINDOWS
            }
            for k in [BASELINE, *CANDIDATES]
        },
        "promotion_tests": result["promotion_tests"],
        "suggested": result["suggested_research_candidate"]
    }, indent=2))


if __name__ == "__main__":
    main()
