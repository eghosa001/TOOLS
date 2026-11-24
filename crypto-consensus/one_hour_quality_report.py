"""1h SOL/ETH futures research, 72 comparable simulations and cohort diagnostics.

Three independent $150 wallet windows per model (first 212 days, later 114
days, and uninterrupted 326 days); never aggregate separate wallets. Each
run includes actual exchange funding, 0.05% fees or 0.15% stress fees.
No backtest can establish forward performance; no order routing.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict

COINS={"SOL":9,"ETH":8}
GATES=("Base24","BTC24","OI24","Both24","Base48","Both48")
FEES=("normal","stress")
PERIODS=("early","later","full")
FEE_VALUES={"normal":.0005,"stress":.0015}
DATE_RANGES={
    "early":("2026-01-01","2026-08-01"),
    "later":("2026-08-01","2026-11-23"),
    "full":("2026-01-01","2026-11-23"),
}
REPRO_ANCHORS={"SOL":{"net":6.3220,"trades":40},
               "ETH":{"net":-5.9331,"trades":42}}


def as_date(x):
    return datetime.fromisoformat(str(x).replace("Z","+00:00"))


def load_result(root:Path,coin:str,gate:str,period:str,fee:str)->dict:
    strategy=f"Q1h{COINS[coin]}{gate}"
    directory=root/coin/gate/period/fee
    zips=list(directory.glob("*.zip"))
    if len(zips)!=1:
        raise ValueError(f"Expected exactly one Freqtrade ZIP {directory}, found {len(zips)}")
    with ZipFile(zips[0]) as z:
        found=[]
        for name in z.namelist():
            if name.endswith(".json") and not name.endswith(".meta.json"):
                doc=json.loads(z.read(name))
                if isinstance(doc,dict) and strategy in doc.get("strategy",{}):
                    found.append(doc["strategy"][strategy])
    if len(found)!=1:
        raise ValueError("Ambiguous Freqtrade strategy trade result: "+str(directory))
    doc=found[0]
    t=doc["trades"]
    first=float(doc["starting_balance"])
    last=float(doc["final_balance"])
    net=sum(float(trade["profit_abs"]) for trade in t)
    if abs(first-150)>.001 or abs(first+net-last)>.03:
        raise ValueError("Trade-by-trade PnL does not match $150 account")
    start=as_date(DATE_RANGES[period][0]+"T00:00:00+00:00")
    end=as_date(DATE_RANGES[period][1]+"T00:00:00+00:00")
    weeks=defaultdict(lambda:{"profit_usd":0.,"closed":0,"losers":0})
    wins=losses=forced=0
    forced_net=0.
    consecutive=max_consecutive=0
    for trade in sorted(t,key=lambda x:x["close_date"]):
        if trade.get("pair")!=coin+"/USD:USD":
            raise ValueError("Mixed coin research account")
        if float(trade.get("leverage",1))>1.00001:
            raise ValueError("Leverage above 1x")
        opened=as_date(trade["open_date"])
        closed=as_date(trade["close_date"])
        if opened<start or opened>=end or closed<opened:
            raise ValueError("Trade opens outside research sample")
        p=float(trade["profit_abs"])
        wins+=int(p>0)
        losses+=int(p<0)
        consecutive=consecutive+1 if p<0 else 0
        max_consecutive=max(max_consecutive,consecutive)
        isforced=trade.get("exit_reason")=="force_exit"
        forced+=int(isforced)
        forced_net+=p if isforced else 0
        week=closed.strftime("%G-W%V")
        weeks[week]["closed"]+=1
        weeks[week]["profit_usd"]+=p
        weeks[week]["losers"]+=int(p<0)
    result={
        "model":strategy,
        "coin":coin,
        "gate":gate,
        "period":period,
        "fee_case":fee,
        "wallet_start_usd":first,
        "wallet_end_usd":round(last,6),
        "net_usd":round(net,6),
        "return_pct":round(100*(last/first-1),4),
        "closed_trades":len(t),
        "wins":wins,
        "losses":losses,
        "max_consecutive_losses":max_consecutive,
        "max_drawdown_pct":round(100*float(doc["max_drawdown_account"]),4),
        "forced_terminal_count":forced,
        "forced_terminal_net_usd":round(forced_net,6),
        "nonforced_closed_net_usd":round(net-forced_net,6),
        "closed_trade_weeks":{
            k:{**x,"profit_usd":round(x["profit_usd"],6)}
            for k,x in sorted(weeks.items())
        },
        "losing_close_weeks":sum(x["profit_usd"]<0 for x in weeks.values()),
    }
    return result


def make(root:Path,manifest:Path)->dict:
    sources=json.loads(manifest.read_text())
    if set(sources)!={"ETH/USD:USD","SOL/USD:USD"}:
        raise ValueError("Provenance for both approved futures markets required")
    rows={coin:{
        gate:{
            period:{fee:load_result(root,coin,gate,period,fee)
                    for fee in FEES} for period in PERIODS
        } for gate in GATES
    } for coin in COINS}

    # Sanity check new "baseline" is genuinely comparable with the previously
    # released 114-day research: threshold, 24h loss lock and 3h cooldown.
    anchor_checks={}
    for coin in COINS:
        previous=REPRO_ANCHORS[coin]
        now=rows[coin]["Base24"]["later"]["normal"]
        comparable=(abs(now["return_pct"]-previous["net"])<.15 and
                    now["closed_trades"]==previous["trades"])
        anchor_checks[coin]={
            "consistent_with_previous_114d_baseline":comparable,
            "previous_return_pct":previous["net"],
            "new_return_pct":now["return_pct"],
            "previous_closed_trades":previous["trades"],
            "new_closed_trades":now["closed_trades"],
        }
        if not comparable:
            raise ValueError(f"Baseline drift for {coin}; compare cause before claiming improved gains")
    checks={}
    for coin in COINS:
        baseline=rows[coin]["Base24"]
        checks[coin]={}
        for gate in GATES:
            a=rows[coin][gate]
            full=a["full"]["normal"]
            fullstress=a["full"]["stress"]
            early=a["early"]["normal"]
            later=a["later"]["normal"]
            estress=a["early"]["stress"]
            lstress=a["later"]["stress"]
            ref=baseline["full"]["normal"]
            rlate=baseline["later"]["normal"]
            conditions={
                "at_least_12_full_trades":full["closed_trades"]>=12,
                "positive_early_and_late":early["net_usd"]>0 and later["net_usd"]>0,
                "positive_both_fee_stresses":estress["net_usd"]>0 and lstress["net_usd"]>0,
                "positive_full_cost_stress":fullstress["net_usd"]>0,
                "full_profit_better_than_same_coin_base":full["net_usd"]>ref["net_usd"]+.5,
                "later_profit_not_worse_than_base":later["net_usd"]>=rlate["net_usd"]-.10,
                "full_drawdown_not_increased":full["max_drawdown_pct"]<=ref["max_drawdown_pct"]+.05,
                "full_loss_streak_not_increased":full["max_consecutive_losses"]<=ref["max_consecutive_losses"],
                "no_large_terminal_pnl":abs(full["forced_terminal_net_usd"])<=.10,
            }
            checks[coin][gate]={
                "passes_historical_screen":all(conditions.values()),
                "conditions":conditions,
                "full_incremental_usd":round(full["net_usd"]-ref["net_usd"],6),
                "later_incremental_usd":round(later["net_usd"]-rlate["net_usd"],6),
            }
    return {
        "mode":"historical_kraken_one_hour_quality_paper_audit",
        "zero_real_orders":True,
        "no_strategy_auto_promotion":True,
        "wallet_start_usd_per_independent_scenario":150,
        "max_leverage":1,
        "normal_fee_per_side":FEE_VALUES["normal"],
        "stress_fee_per_side":FEE_VALUES["stress"],
        "dates":DATE_RANGES,
        "asset_votes":COINS,
        "gates":GATES,
        "oi_source_provenance":sources,
        "baseline_114d_reproduced":anchor_checks,
        "rows":rows,
        "historical_screens":checks,
        "historical_passes":[{
            "coin":coin,"gate":gate
        } for coin in COINS for gate in GATES
          if checks[coin][gate]["passes_historical_screen"]],
        "limitations":[
            "Both early and later calendar windows are retrospectively studied; neither constitutes genuinely unseen forward trades.",
            "Each period / fee / coin / strategy restarts from $150; full is continuous over Jan-Nov, NOT the sum of early and later.",
            "Fundamental/derivatives feeds are from Kraken public history; fills, spread and stop gaps are not actual executed orders.",
            "Stressed fees are 0.15% per side as hypothetical adverse friction; not exchange-observed slippage.",
            "All entry filters evaluate fully completed bars and deliberately lag data publication.",
            "OI/funding gate requires both actual feed observations, never infers missing data from zero.",
            "A forced closing of an open position on the period boundary is hypothetical and NOT organic realized profit.",
            "MaxDrawdown guard is a backtesting protection, NOT a hard daily-2% weekly-4% or peak-6% live account equity lock.",
            "At least one coin will sometimes lose, and profitable weekly income cannot be guaranteed.",
            "Forward-only shadow evidence must precede any real-money deployment.",
        ],
    }


def markdown(r):
    out=[
        "# One-hour futures profit-quality experiment: ETH and SOL",
        "",
        "**72 matched Freqtrade historical simulations, with no exchange keys or real orders.** "
        "Each candidate uses the same one-hour 8/10 ETH or 9/10 SOL ten-indicator "
        "consensus, 1x, $150 account, ATR sizing/stop, and Freqtrade protections.",
        "",
        "Six candidate configurations per coin: original 24h loss pause, completed "
        "BTC regime veto, actual Kraken 4h open interest + hourly funding crowding veto, "
        "both vetoes, 48h loss pause without vetoes, or both vetoes with 48h pause. "
        "The normal 3h post-close cooldown and original 7-day modeled drawdown "
        "guard remain unchanged. All one-hour additions are research only.",
        "",
        "Three windows: Jan–Jul, Aug–Nov, and one uninterrupted Jan–Nov; each "
        "window is restarted independently at $150. The later period was already "
        "examined and is **NOT untouched future data**.",
        "",
        "Cost: actual Freqtrade funding, 0.05%/side normal or an independently "
        "rerun 0.15%/side stress scenario. These are hypotheses about friction, "
        "not measured live bid/ask spread.",
        "",
        "| Coin | Model | Early net USD | Later net USD | Full return | "
        "Full stress return | Full trades W/L | Full max DD | Max loss streak | Research screen |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for coin in COINS:
        for gate in GATES:
            a=r["rows"][coin][gate]
            early=a["early"]["normal"]
            later=a["later"]["normal"]
            full=a["full"]["normal"]
            stress=a["full"]["stress"]
            checks=r["historical_screens"][coin][gate]
            decision="Pass (research only)" if checks["passes_historical_screen"] else "Fail"
            out.append(
                f"| {coin} | {gate} | {early['net_usd']:+.3f} | "
                f"{later['net_usd']:+.3f} | {full['return_pct']:+.3f}% | "
                f"{stress['return_pct']:+.3f}% | {full['wins']}/{full['losses']} | "
                f"{full['max_drawdown_pct']:.3f}% | "
                f"{full['max_consecutive_losses']} | {decision} |")
    out += [
        "",
        "## Same-period baseline reproduction",
        "",
    ]
    for coin,verify in r["baseline_114d_reproduced"].items():
        out.append(f"- {coin}: previous {verify['previous_return_pct']:+.4f}%/"
                   f"{verify['previous_closed_trades']} trades, now "
                   f"{verify['new_return_pct']:+.4f}%/"
                   f"{verify['new_closed_trades']} trades; "
                   f"matched={verify['consistent_with_previous_114d_baseline']}")
    out += [
        "",
        "## Decision criteria",
        "",
        "Historical screen set before results: at least 12 full-period trades, "
        "early/later and their cost-stress net positive, full cost-stress positive, "
        "full gain >=$0.50 above that coin's Base24, later gain not lower by more than "
        "$0.10, no increased full drawdown or loss streak, and no large terminal "
        "forced exit. Passing **never authorizes real trading**.",
        "",
        "Research-screen passes: "+(
            ", ".join(f"{x['coin']} {x['gate']}" for x in r["historical_passes"])
            if r["historical_passes"] else "**None**"
        ),
        "",
        "Futures open-interest close is usable only after its 4h bar plus an extra "
        "4h publication lag; funding is delayed 2h; BTC completed 12h "
        "trend is only used strictly after candle completion. Each filter fails "
        "closed on missing or stale data.",
        "",
        "Weekly closed-trade P&L in the JSON is NOT a weekly marked-equity curve. "
        "Simulated protections do not replicate guaranteed 2% daily, 4% weekly "
        "and 6% peak live-account locks. Do not claim expected real earnings.",
        "",
        "**No production ETH strategy, existing paper bot, real orders or "
        "ChatGPT paid signal settings were changed.**",
    ]
    return "\n".join(out)+"\n"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--json",required=True)
    ap.add_argument("--markdown",required=True)
    a=ap.parse_args()
    report=make(Path(a.root),Path(a.manifest))
    Path(a.json).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    Path(a.markdown).write_text(markdown(report))
    for coin in COINS:
        for gate in GATES:
            d=report["rows"][coin][gate]
            full=d["full"]["normal"]
            stress=d["full"]["stress"]
            print("ONEH_QUALITY_RESULT",coin,gate,
                  "early",d["early"]["normal"]["net_usd"],
                  "later",d["later"]["normal"]["net_usd"],
                  "full_return",full["return_pct"],
                  "stress_return",stress["return_pct"],
                  "trades",full["closed_trades"],
                  "streak",full["max_consecutive_losses"],
                  "dd",full["max_drawdown_pct"],
                  "forced",full["forced_terminal_net_usd"],
                  "passes",report["historical_screens"][coin][gate]["passes_historical_screen"])
    print("ONEH_SCREEN_PASSES",report["historical_passes"])


if __name__=="__main__":
    main()
