"""Audit 1-hour ETH/SOL trade-clock restrictions using actual Freqtrade exports.

3 windows × 2 markets × 4 clock restrictions × 2 independently re-executed
fee assumptions = 48 historical simulations; no orders or runtime changes.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
import json
from zipfile import ZipFile

CAPITAL=150.
DATES={
    "early":("2026-01-01","2026-08-01"),
    "later":("2026-08-01","2026-11-23"),
    "full":("2026-01-01","2026-11-23"),
}
COINS={"ETH":8,"SOL":9}
SCENARIOS=("Baseline","NoPostTradeWait","NoLossPause","NoTimeLocks")
FEES={"normal":.0005,"stress":.0015}
PREVIOUS={
    "ETH":{"early":(2.8818,58),"later":(8.4978,29),"full":(11.6487,86)},
    "SOL":{"early":(-.8760,40),"later":(3.8448,29),"full":(3.3374,68)},
}


def parse_time(text):
    x=datetime.fromisoformat(str(text).replace("Z","+00:00"))
    if x.tzinfo is None:
        raise ValueError("Offset-aware UTC timestamps required")
    return x.astimezone(timezone.utc)


def export(root,coin,scenario,window,fee):
    model=f"Clock{coin}{scenario}"
    folder=Path(root)/coin/scenario/window/fee
    archives=list(folder.glob("*.zip"))
    if len(archives)!=1:
        raise ValueError(f"Expected exactly one real Freqtrade export {folder}, got {len(archives)}")
    selected=[]
    with ZipFile(archives[0]) as z:
        for name in z.namelist():
            if name.endswith(".json") and not name.endswith(".meta.json"):
                contents=json.loads(z.read(name))
                if isinstance(contents,dict) and model in contents.get("strategy",{}):
                    selected.append(contents["strategy"][model])
    if len(selected)!=1:
        raise ValueError(f"Missing or duplicated {model} source export")
    return selected[0]


def summarize(source,coin,scenario,window,fee):
    start=parse_time(DATES[window][0]+"T00:00:00Z")
    end=parse_time(DATES[window][1]+"T00:00:00Z")
    days=(end-start).days
    balance=float(source["starting_balance"])
    final=float(source["final_balance"])
    trades=source["trades"]
    profit=sum(float(t["profit_abs"]) for t in trades)
    if balance<=0 or final<=0 or abs(balance-CAPITAL)>.001 or abs(final-balance-profit)>.03:
        raise ValueError("Invalid starting account or unreconciled cash performance")
    natural=[]
    forced=[]
    weekly=defaultdict(lambda:{"trades":0,"pnl_usd":0.})
    daily=defaultdict(float)
    consecutive=max_consecutive=0
    for t in sorted(trades,key=lambda t:t["close_date"]):
        if t.get("pair")!=coin+"/USD:USD" or float(t.get("leverage",1.))>1.00001:
            raise ValueError("Wrong coin or unacceptable leverage in experiment")
        a=parse_time(t["open_date"]);b=parse_time(t["close_date"])
        if not start<=a<end or not a<=b<=end:
            raise ValueError("Out-of-period trade or invalid interval")
        amount=float(t["profit_abs"])
        entry={"open":a,"close":b,"net":amount}
        if t.get("exit_reason")=="force_exit":
            forced.append(entry)
        else:
            if b>=end:raise ValueError("Artificial end treated as natural close")
            natural.append(entry)
            daily[b.date().isoformat()]+=amount
            week=weekly[b.strftime("%G-W%V")]
            week["trades"]+=1
            week["pnl_usd"]+=amount
        if amount<0:
            consecutive+=1
            max_consecutive=max(max_consecutive,consecutive)
        else:
            consecutive=0
    natural_net=sum(x["net"] for x in natural)
    forced_net=sum(x["net"] for x in forced)
    if abs(natural_net+forced_net-profit)>1e-8:
        raise ValueError("Forced terminal attribution mismatch")
    return {
        "coin":coin,"scenario":scenario,"period":window,"fee_mode":fee,
        "days":days,"starting_usd":balance,"ending_usd":round(final,6),
        "profit_usd_including_forced":round(profit,6),
        "return_pct_including_forced":round((final/balance-1)*100,4),
        "mean_profit_per_day_usd_including_forced":round(profit/days,6),
        "total_closed_trades":len(trades),
        "natural_trades":len(natural),
        "natural_trades_per_week":round(len(natural)*7/days,4),
        "natural_trade_net_usd":round(natural_net,6),
        "natural_winners":sum(t["net"]>0 for t in natural),
        "natural_losers":sum(t["net"]<0 for t in natural),
        "positive_natural_close_days":sum(x>0 for x in daily.values()),
        "negative_natural_close_days":sum(x<0 for x in daily.values()),
        "days_without_a_natural_close":days-len(daily),
        "weeks_with_natural_closes":len(weekly),
        "weeks_with_positive_natural_net":sum(x["pnl_usd"]>0 for x in weekly.values()),
        "max_consecutive_losses":max_consecutive,
        "forced_end_exit_count":len(forced),
        "forced_end_exit_profit_usd":round(forced_net,6),
        "backtester_reported_max_drawdown_pct":round(float(source["max_drawdown_account"])*100,4),
        "daily_natural_closed_pnl_usd":{k:round(v,6) for k,v in sorted(daily.items())},
        "weekly_natural_closed_pnl":{k:{"trades":v["trades"],"net_usd":round(v["pnl_usd"],6)}
                                     for k,v in sorted(weekly.items())},
    }


def build(root):
    results={
        coin:{
            sc:{
                period:{
                    fee:summarize(export(root,coin,sc,period,fee),
                                  coin,sc,period,fee)
                    for fee in FEES
                } for period in DATES
            } for sc in SCENARIOS
        } for coin in COINS
    }
    # A historical "improvement" is invalid unless original model
    # outputs can be reproduced on identical data and fees.
    match={}
    for coin in COINS:
        match[coin]={}
        for window in DATES:
            expected_return,expected_trades=PREVIOUS[coin][window]
            base=results[coin]["Baseline"][window]["normal"]
            matched=(abs(base["return_pct_including_forced"]-expected_return)<=.02
                     and base["total_closed_trades"]==expected_trades)
            match[coin][window]={
                "matched":matched,"old_pct":expected_return,
                "retested_pct":base["return_pct_including_forced"],
                "old_trades":expected_trades,"retested_trades":base["total_closed_trades"],
            }
            if not matched:
                raise ValueError(f"Existing original model drifted: {coin} {window} {match[coin][window]}")
    decisions={}
    for coin in COINS:
        incumbent=results[coin]["Baseline"]
        decisions[coin]={}
        for sc in SCENARIOS:
            p=results[coin][sc]
            full=p["full"]["normal"]
            stressed=p["full"]["stress"]
            control=incumbent["full"]["normal"]
            control_stress=incumbent["full"]["stress"]
            gains={
                "extra_natural_trades":full["natural_trades"]-control["natural_trades"],
                "extra_normal_profit_usd":round(full["profit_usd_including_forced"]-
                                                control["profit_usd_including_forced"],6),
                "extra_stress_profit_usd":round(stressed["profit_usd_including_forced"]-
                                                control_stress["profit_usd_including_forced"],6),
            }
            rules={
                "natural_trade_count_above_original":gains["extra_natural_trades"]>0,
                "net_profit_higher_at_normal_fees":gains["extra_normal_profit_usd"]>0,
                "net_profit_higher_under_fee_stress":gains["extra_stress_profit_usd"]>0,
                "both_historical_periods_stressed_positive":
                    p["early"]["stress"]["profit_usd_including_forced"]>0 and
                    p["later"]["stress"]["profit_usd_including_forced"]>0,
                "reported_stress_drawdown_below_six_pct":
                    stressed["backtester_reported_max_drawdown_pct"]<=6,
                "losing_streak_not_longer_than_original":
                    full["max_consecutive_losses"]<=control["max_consecutive_losses"],
                "no_meaningful_terminal_force_exit_profit":
                    abs(full["forced_end_exit_profit_usd"])<.1,
            }
            decisions[coin][sc]={
                **gains,"rules":rules,
                "historical_screen_passed":sc!="Baseline" and all(rules.values()),
            }
    return {
        "type":"time_lock_ablation_research_historical_futures_not_earnings",
        "no_live_trades":True,
        "unchanged_forward_paper_bot":True,
        "unchanged_original_12h_bot":True,
        "risk_controls_retained":[
            "8/10 ETH or 9/10 SOL technical agreement",
            "genuine lagged BTC regime and published funding/OI veto",
            "one open position and one-times leverage",
            "existing ATR sizing, stop and 4% emergency stop",
            "7-day Freqtrade 4% max-drawdown protection",
        ],
        "time_restrictions_under_test":{
            "Baseline":"3h after any completed trade + 24h after stop/loss",
            "NoPostTradeWait":"0h after any completed trade + 24h after stop/loss",
            "NoLossPause":"3h after any completed trade + 0h after stop/loss",
            "NoTimeLocks":"0h after any completed trade + 0h after stop/loss",
        },
        "starting_cash_per_independent_run_usd":CAPITAL,
        "time_windows":DATES,"fees":FEES,
        "results":results,"baseline_reproduction":match,
        "candidate_assessment":decisions,
        "eligible_historical_candidates":[{
            "coin":coin,"scenario":scenario,
            **{k:v for k,v in decisions[coin][scenario].items() if k.startswith("extra_")}
        } for coin in COINS for scenario in SCENARIOS
          if decisions[coin][scenario]["historical_screen_passed"]],
        "warnings":[
            "No cooldown is not a license to exceed daily weekly or peak equity loss controls in the existing forward observer.",
            "Deleting Freqtrade stoploss/low-profit guard weakens defense against clusters of losses; even a profitable backtest need not survive future volatility.",
            "Only selected clock-based pauses are removed. MAXDRAWDOWN guard, stops, one position, 1x sizing and signal filters remain.",
            "One-hour candles, single ETH/SOL account and actual market gating still limit the number of trade opportunities: zero pauses do NOT guarantee multiple trades daily.",
            "Higher costs assumed 0.15% fee per side, not actual orderbook spread/slippage.",
            "Forced terminal exit is a fictitious exit in backtests and its profit is separated.",
            "Weeks/days attribute only closed natural trades, not marked-to-market equity.",
            "2026 backtest data is already repeatedly examined; prospective hourly paper testing remains required.",
        ],
    }


def markdown(doc):
    lines=[
        "# Zero time cooldown versus current 1h ETH/SOL baseline",
        "",
        "Historical simulated Kraken perpetual futures with 1x exposure and "
        "$150 separately restarted account per scenario, **no real orders**.",
        "",
        "Test four combinations of 3h after-trade wait and 24h stop-loss pause. "
        "Existing technical votes, completed BTC regime, actual lagged OI/funding, "
        "ATR sizing/stops, one-position cap and **7-day 4% MaxDrawdown guard** "
        "are retained. This is an isolated change to timed restrictions only.",
        "",
        "| Coin | Temporal restriction | Natural trades | Trades/week | "
        "Jan–Nov return | Higher-cost return | Early stress net USD | "
        "Later stress net USD | Max loss streak | Higher-fee DD | Forced end USD |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for coin in COINS:
        for scenario in SCENARIOS:
            rec=doc["results"][coin][scenario]
            full=rec["full"]["normal"]
            stress=rec["full"]["stress"]
            early=rec["early"]["stress"]
            later=rec["later"]["stress"]
            lines.append(
                f"| {coin} | {scenario} | {full['natural_trades']} | "
                f"{full['natural_trades_per_week']:.2f} | "
                f"{full['return_pct_including_forced']:+.3f}% | "
                f"{stress['return_pct_including_forced']:+.3f}% | "
                f"{early['profit_usd_including_forced']:+.3f} | "
                f"{later['profit_usd_including_forced']:+.3f} | "
                f"{full['max_consecutive_losses']} | "
                f"{stress['backtester_reported_max_drawdown_pct']:.3f}% | "
                f"{full['forced_end_exit_profit_usd']:+.3f} |")
    lines+=["","## Historical candidate screens",
            "Increases naturally completed trades and net profit at both 0.05% "
            "and 0.15% per-side cost, both restarted historical segments "
            "positive under stress, higher-cost backtester drawdown <=6%, "
            "no worsening longest losing streak, no terminal force-exit "
            "profit dependency >$0.10.", ""]
    if doc["eligible_historical_candidates"]:
        for a in doc["eligible_historical_candidates"]:
            lines.append(f"- {a['coin']} {a['scenario']}: "
                         f"{a['extra_natural_trades']:+} trades, "
                         f"{a['extra_normal_profit_usd']:+.3f} USD normal, "
                         f"{a['extra_stress_profit_usd']:+.3f} USD stressed")
    else:
        lines.append("**None.** No clock-removal change passed all tests.")
    lines+=["","## Distinctions",
            "Even with zero cooldown, 1h signals can be absent for most hours. "
            "No model can open a second concurrent position, and a "
            "seven-day maximum drawdown guard still limits losing periods. "
            "This experiment does NOT remove the actual forward paper "
            "observer's 2% daily, 4% weekly or 6% peak locks.",
            "",
            "All data are retrospective; never interpret the per-day average "
            "as daily real profit. The existing 1h paper observer and 12h "
            "comparison bot remain unchanged unless separately validated.",
            ""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--md",required=True)
    a=p.parse_args()
    doc=build(Path(a.root))
    Path(a.json).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
    Path(a.md).write_text(markdown(doc))
    for coin in COINS:
        for sc in SCENARIOS:
            full=doc["results"][coin][sc]["full"]["normal"]
            stress=doc["results"][coin][sc]["full"]["stress"]
            print("CLOCK_RESULT",coin,sc,"trades",full["natural_trades"],
                  "normal_pct",full["return_pct_including_forced"],
                  "stress_pct",stress["return_pct_including_forced"],
                  "normal_usd",full["profit_usd_including_forced"],
                  "stress_usd",stress["profit_usd_including_forced"],
                  "max_dd_stress",stress["backtester_reported_max_drawdown_pct"],
                  "streak",full["max_consecutive_losses"],
                  "screen",doc["candidate_assessment"][coin][sc]["historical_screen_passed"])
    print("CLOCK_ABLATION_PASSES",doc["eligible_historical_candidates"])


if __name__=="__main__":
    main()
