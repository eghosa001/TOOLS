"""Compare 1h, 15m and 5m protected crypto strategies without hindsight fitting.

All 36 strategies are unoptimized predeclared scenarios. Exactly one $150
simulated account per (coin, timeframe, threshold, risk profile); no pooled
portfolio calculation, no real exchange orders. Stress fee effect is a
fixed-trade counterfactual, not an independently re-executed fill simulation.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
from statistics import median
from zipfile import ZipFile

COINS=("ETH","SOL","BTC")
TFS=("1h","15m","5m")
VOTES=(8,9)
PROFILES=("Strict","Active")
TIMERANGE_START=datetime(2026,9,1,tzinfo=timezone.utc)
TIMERANGE_END=datetime(2026,11,23,tzinfo=timezone.utc)
DURATION_DAYS=(TIMERANGE_END-TIMERANGE_START).total_seconds()/86400
STRESS_EXTRA_FEE_PER_SIDE=.001
START_CAPITAL=150.


def model_name(tf: str, votes: int, profile: str) -> str:
    return f"Fast{tf}{votes}{profile}"


def parse_zip(root, coin, tf, votes, profile):
    model=model_name(tf,votes,profile)
    folder=Path(root)/coin/tf/str(votes)/profile
    files=list(folder.glob("*.zip"))
    if len(files)!=1:
        raise ValueError(f"Expected exactly one source export {folder}, got {len(files)}")
    with ZipFile(files[0]) as z:
        selected=[]
        for entry in z.namelist():
            if entry.endswith(".json") and not entry.endswith(".meta.json"):
                data=json.loads(z.read(entry))
                if isinstance(data,dict) and model in data.get("strategy",{}):
                    selected.append(data["strategy"][model])
    if len(selected)!=1:
        raise ValueError("Invalid or duplicate model JSON for "+str(folder))
    return selected[0]


def date_of(value):
    return datetime.fromisoformat(value.replace("Z","+00:00"))


def summarize(raw, coin, tf, votes, profile):
    initial=float(raw["starting_balance"])
    final=float(raw["final_balance"])
    trades=raw["trades"]
    if abs(initial-START_CAPITAL)>.001:
        raise ValueError("Different account starting capital")
    if any(t.get("pair")!=f"{coin}/USD:USD" for t in trades):
        raise ValueError("Mixed-coin account contaminates result")
    if any(float(t.get("leverage",1.0))>1.00001 for t in trades):
        raise ValueError("Leveraged trade in 1x research")
    profit=sum(float(t["profit_abs"]) for t in trades)
    if abs(final-initial-profit)>.03:
        raise ValueError("Backtest wallet does not reconcile with closed trades")
    wins=sum(float(t["profit_abs"])>0 for t in trades)
    losses=sum(float(t["profit_abs"])<0 for t in trades)
    forced=[t for t in trades if t.get("exit_reason")=="force_exit"]
    opened=[date_of(t["open_date"]) for t in trades]
    closed=[date_of(t["close_date"]) for t in trades]
    if any(x>=TIMERANGE_END or x<TIMERANGE_START for x in opened):
        raise ValueError("Trade from outside the declared observation window")
    durations=[(end-start).total_seconds()/3600 for start,end in zip(opened,closed)]
    weekly=defaultdict(lambda:{"closes":0,"wins":0,"losses":0,"closed_net_usd":0.})
    for t,when in zip(trades,closed):
        key=when.strftime("%G-W%V")
        row=weekly[key]
        row["closes"]+=1
        row["closed_net_usd"]+=float(t["profit_abs"])
        row["wins"]+=int(float(t["profit_abs"])>0)
        row["losses"]+=int(float(t["profit_abs"])<0)
    weekly=dict(sorted((k,{**v,"closed_net_usd":round(v["closed_net_usd"],6)})
                       for k,v in weekly.items()))
    ordered=sorted(zip(closed,trades),key=lambda x:x[0])
    longest_loss=current_loss=0
    for _,t in ordered:
        if float(t["profit_abs"])<0:
            current_loss+=1
            longest_loss=max(longest_loss,current_loss)
        else:
            current_loss=0
    trade_days=len({x.date() for x in opened})
    boundaries=[TIMERANGE_START]+sorted(opened)+[TIMERANGE_END]
    longest_gap=max(((b-a).total_seconds()/86400 for a,b in zip(boundaries,boundaries[1:])),
                    default=DURATION_DAYS)
    # Different execution would have different positions. This is a COST
    # SENSITIVITY on the *same* fixed trade list, NOT a Freqtrade resimulation.
    # Freqtrade "amount" is base units, so amount*entry/exit price gives USD notional.
    extra_cost=0.
    stress_estimate_supported=True
    for t in trades:
        if not all(k in t for k in ("amount","open_rate","close_rate")):
            stress_estimate_supported=False
            break
        qty=float(t["amount"])
        entry=float(t["open_rate"])
        exit=float(t["close_rate"])
        if qty<=0 or entry<=0 or exit<=0:
            stress_estimate_supported=False
            break
        extra_cost+=STRESS_EXTRA_FEE_PER_SIDE*qty*(entry+exit)
    stressed_net=profit-extra_cost if stress_estimate_supported else None
    return {
        "coin":coin,
        "timeframe":tf,
        "votes_required":votes,
        "profile":profile.lower(),
        "initial_usd":round(initial,6),
        "end_usd":round(final,6),
        "net_usd":round(profit,6),
        "return_pct":round(100*(final/initial-1),4),
        "backtest_reported_max_drawdown_pct":round(float(raw["max_drawdown_account"])*100,4),
        "closed_trades":len(trades),
        "winning_trades":wins,
        "losing_trades":losses,
        "win_rate_pct":round(wins/len(trades)*100,2) if trades else None,
        "trades_per_week":round(len(trades)*7/DURATION_DAYS,3),
        "distinct_entry_days":trade_days,
        "longest_gap_between_entries_days":round(longest_gap,3),
        "max_consecutive_losing_closes":longest_loss,
        "median_trade_duration_hours":round(median(durations),3) if durations else None,
        "forced_end_exits":len(forced),
        "forced_end_net_usd":round(sum(float(t["profit_abs"]) for t in forced),6),
        "winning_closed_net_usd":round(sum(float(t["profit_abs"]) for t in trades
                                           if float(t["profit_abs"])>0),6),
        "losing_closed_net_usd":round(sum(float(t["profit_abs"]) for t in trades
                                          if float(t["profit_abs"])<0),6),
        "extra_cost_stress_per_side":STRESS_EXTRA_FEE_PER_SIDE,
        "stress_additional_notional_cost_usd":round(extra_cost,6) if stress_estimate_supported else None,
        "stress_net_usd_fixed_trades":round(stressed_net,6) if stressed_net is not None else None,
        "stress_return_pct_fixed_trades":round(100*stressed_net/initial,4) if stressed_net is not None else None,
        "closed_trade_weekly_attribution":weekly,
    }


def report(root, stress_root=None):
    data={}
    for coin in COINS:
        data[coin]={}
        for tf in TFS:
            data[coin][tf]={}
            for votes in VOTES:
                data[coin][tf][str(votes)]={}
                for profile in PROFILES:
                    raw=parse_zip(root,coin,tf,votes,profile)
                    data[coin][tf][str(votes)][profile]=summarize(raw,coin,tf,votes,profile)
    stress_data=None
    if stress_root is not None:
        stress_data={
            coin:{
                tf:{
                    str(votes):{
                        profile:summarize(
                            parse_zip(stress_root,coin,tf,votes,profile),
                            coin,tf,votes,profile
                        )
                        for profile in PROFILES
                    } for votes in VOTES
                } for tf in TFS
            } for coin in COINS
        }
    all_rows=[
        data[coin][tf][str(votes)][profile]
        for coin in COINS for tf in TFS for votes in VOTES for profile in PROFILES
    ]
    screened=[]
    for row in all_rows:
        # Predeclared research screen only, not trading or "best" certification.
        enough=row["closed_trades"]>=10
        nonforced=row["net_usd"]-row["forced_end_net_usd"]
        actual_stressed=(
            stress_data[row["coin"]][row["timeframe"]]
            [str(row["votes_required"])][row["profile"].capitalize()]
            if stress_data is not None else None
        )
        if (enough and row["net_usd"]>0 and nonforced>0
            and row["backtest_reported_max_drawdown_pct"]<=4.
            and row["stress_net_usd_fixed_trades"] is not None
            and row["stress_net_usd_fixed_trades"]>0
            and (actual_stressed is None or actual_stressed["net_usd"]>0)):
            screened.append({
                "coin":row["coin"],"timeframe":row["timeframe"],
                "votes":row["votes_required"],"profile":row["profile"],
                "net_usd":row["net_usd"],
                "stress_net_usd":row["stress_net_usd_fixed_trades"],
                "drawdown_pct":row["backtest_reported_max_drawdown_pct"],
                "trades_per_week":row["trades_per_week"],
                "stressed_backtest_net_usd":actual_stressed["net_usd"] if actual_stressed else None,
            })
    return {
        "mode":"retrospective_freqtrade_intraday_research_only",
        "no_real_trades":True,
        "initial_capital_usd_per_individual_run":START_CAPITAL,
        "same_1x_notional":True,
        "nominal_fee_per_side":.0005,
        "extra_cost_stress_per_side":STRESS_EXTRA_FEE_PER_SIDE,
        "period_start":TIMERANGE_START.isoformat(),
        "period_end_exclusive":TIMERANGE_END.isoformat(),
        "period_days":DURATION_DAYS,
        "markets":COINS,
        "tested_timeframes":TFS,
        "tested_consensus_thresholds":VOTES,
        "tested_protection_profiles":{
            "Strict":"original wall-clock 36h cooldown, 7-day loss guard",
            "Active":"one candle cooldown, 48h loss guard (less restrictive, separate experiment)"
        },
        "candidate_results":data,
        "independently_reexecuted_015pct_per_side_fee_results":stress_data,
        "reexecution_stress_fee_per_side":.0015 if stress_data is not None else None,
        "predeclared_research_screen":screened,
        "automatic_model_promotion":False,
        "existing_12h_bot_unchanged":True,
        "warnings":[
            "Nine of ten indicator agreement is not nine independent trading bots.",
            "Shorter candles may increase trade opportunities but can multiply fees, false signals, spread and slippage.",
            "All return estimates and drawdowns are historical backtest simulations; open-position mark-to-market drawdown is not guaranteed.",
            "An open trade automatically closed at the final backtest boundary is NOT a real strategy exit.",
            "Extra cost stress deducts hypothetical additional 0.1% of both entry and exit notionals from the same fixed trades and does NOT recompute executions, slippage or compounding.",
            "Protection strict and active profiles differ substantially; any active profile has relaxed cooldown protections.",
            "We have not confirmed live exchange minimum-order feasibility, liquidity, taker spread or real server latency for each trade.",
            "Trade counts are full-period counts, not guarantees of a daily trade.",
            "Fee-stressed rerun uses 0.15% per-side Freqtrade fee to approximate 0.05% assumed real fee plus 0.10% friction/slippage per side; execution, spread and market impact are NOT actually simulated.",
            "Each run uses a separate $150 scenario wallet; not a simultaneous three-coin portfolio.",
            "Weekly closure attribution is NOT weekly mark-to-market equity and does not reflect open unrealized loss.",
            "This interval is known historical data, not untouched out-of-sample; hold out genuinely future calendar weeks before any promotion.",
        ],
    }


def markdown(r):
    lines=[
        "# ETH, SOL, BTC intraday: 1h vs 15m vs 5m and 8/10 vs 9/10",
        "",
        "**36 historical futures simulations. No live orders.**",
        f"Test window: {r['period_start']} to {r['period_end_exclusive']} "
        f"(exclusive), {r['period_days']:.0f} calendar days.",
        "Each scenario starts with its OWN $150 account. A result is not a "
        "three-coin portfolio or forecast of income. One trade at a time, "
        "original Freqtrade ATR stops and position sizing, 1x maximum leverage. "
        "Kraken Futures actual prices/funding and modeled 0.05% per-side fee.",
        "",
        "Strict keeps wall-clock 36h cooldown and 7-day post-loss guard; "
        "Active experiments with 1 completed candle cooldown and 48h post-loss "
        "guard instead. Both keep original ATR stake/risk, 4% emergency "
        "stop and 7d MaxDrawdown 4% threshold; changing guard duration changes risk.",
        "Our 12h ETH reference has different full-year dates and MUST NOT be "
        "compared directly with the 83-day experiment as if the horizon matched.",
        "",
        "| Asset | TF | Votes | Risk mode | Trades | Trades/wk | Wins/Losses | "
        "Net return | Max DD | Extra-cost stress return | Rebacktested cost-stress return | Forced end profit USD |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for coin in COINS:
        for tf in TFS:
            for votes in VOTES:
                for profile in PROFILES:
                    row=r["candidate_results"][coin][tf][str(votes)][profile]
                    stress=row["stress_return_pct_fixed_trades"]
                    rerun=(r["independently_reexecuted_015pct_per_side_fee_results"]
                           [coin][tf][str(votes)][profile]
                           if r["independently_reexecuted_015pct_per_side_fee_results"] else None)
                    rerun_text=(f"{rerun['return_pct']:+.3f}%" if rerun is not None
                                else "Unavailable")
                    lines.append(
                        f"| {coin} | {tf} | {votes}/10 | {profile} | "
                        f"{row['closed_trades']} | {row['trades_per_week']:.2f} | "
                        f"{row['winning_trades']}/{row['losing_trades']} | "
                        f"{row['return_pct']:+.3f}% | "
                        f"{row['backtest_reported_max_drawdown_pct']:.3f}% | "
                        f"{f'{stress:+.3f}%' if stress is not None else 'Unavailable'} | "
                        f"{rerun_text} | "
                        f"{row['forced_end_net_usd']:+.3f} |"
                    )
    lines.extend([
        "",
        "## Fixed, predeclared research screen (not approval to trade)",
        "",
        "At least ten closed trades, positive total net, positive other trade-close "
        "profit excluding forced terminal exit, reported maximum DD <=4%, "
        "and remaining positive under an extra 0.1% assumed cost per SIDE "
        "as well as a separate 0.15%-per-side Freqtrade rebacktest.",
        "",
    ])
    if r["predeclared_research_screen"]:
        for row in r["predeclared_research_screen"]:
            lines.append(
                f"- {row['coin']} {row['timeframe']} {row['votes']}/10 "
                f"{row['profile']}: {row['trades_per_week']:.2f} closes/week; "
                f"{row['net_usd']:+.2f} USD, fixed-trade stressed {row['stress_net_usd']:+.2f} USD, "
                f"independent-fee-run {row['stressed_backtest_net_usd']} USD, "
                f"reported DD {row['drawdown_pct']:.2f}%"
            )
    else:
        lines.append("**None.**")
    lines.extend([
        "",
        "## Non-negotiable qualifications",
        "",
        "The weekly figures in machine-readable JSON group CLOSED-TRADE profit "
        "only. They do not measure unrealized loss or equity as positions cross "
        "week boundaries. Freqtrade terminal force-closes MUST NOT be treated "
        "as natural strategy profits. The extra-cost test is a fixed-trade "
        "approximation; the separately rerun 0.15% per-side fee scenario "
        "allows simulated trade changes but is still NOT an exchange fill or "
        "spread simulation.",
        "",
        "Candle availability is not execution opportunity: no trade is opened "
        "unless the relevant entry agrees, existing protection locks permit "
        "entry and exchange size constraints are satisfied. At 5m, high "
        "frequency can increase round-trip fees and slippage more rapidly "
        "than the average price move.",
        "",
        "The original 12-hour ETH paper strategy was NOT replaced, "
        "and no new market/timeframe was activated for real trading.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--stress-root",required=True)
    parser.add_argument("--json",required=True)
    parser.add_argument("--md",required=True)
    args=parser.parse_args()
    r=report(args.root,args.stress_root)
    Path(args.json).write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    Path(args.md).write_text(markdown(r))
    for coin in COINS:
        for tf in TFS:
            for votes in VOTES:
                for profile in PROFILES:
                    row=r["candidate_results"][coin][tf][str(votes)][profile]
                    print(
                        "INTRADAY_RESULT",coin,tf,votes,profile,
                        "trades",row["closed_trades"],
                        "trades_per_week",row["trades_per_week"],
                        "net_pct",row["return_pct"],
                        "maxdd_pct",row["backtest_reported_max_drawdown_pct"],
                        "stress_pct",row["stress_return_pct_fixed_trades"],
                        "actual_higher_fee_backtest_pct",
                        r["independently_reexecuted_015pct_per_side_fee_results"][coin][tf][str(votes)][profile]["return_pct"],
                        "forced_net",row["forced_end_net_usd"]
                    )
    print("RESEARCH_SCREEN",json.dumps(r["predeclared_research_screen"]))


if __name__=="__main__":
    main()
