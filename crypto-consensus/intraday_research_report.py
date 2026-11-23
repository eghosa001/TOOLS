"""Reconcile short-candle Freqtrade histories without claiming future profits.

Research universe fixed BEFORE results:
BTC/SOL/ETH, 1h/15m/5m, 8/10 or 9/10, 7-day loss lock or
24h active lock, two fee/slippage-stress scenarios for the active mode,
and comparable 12h 8/10 protected reference.
All accounts separate, one uninterrupted Aug 1-Nov 22 2026 interval.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from zipfile import ZipFile

COINS=("ETH","SOL","BTC")
FAST=("1h","15m","5m")
CASES=[
    {"name":f"Fast{tf}{votes}{guard.title()}",
     "timeframe":tf,"votes":votes,"cooldown":guard,
     "fees":fees,"coin":coin}
    for coin in COINS for tf in FAST for votes in (8,9)
    for guard in ("strict","active")
    for fees in (("base","stress") if guard=="active" else ("base",))
]
REFERENCES=[{"name":"GuardedConsensusETH","timeframe":"12h",
             "votes":8,"cooldown":"strict","fees":"base","coin":coin}
            for coin in COINS]
ALL=REFERENCES+CASES
DAYS=114
START="2026-08-01T00:00:00+00:00"
END="2026-11-23T00:00:00+00:00"
FEE_PER_SIDE={"base":.0005,"stress":.0015}


def extract(root:Path,case:dict)->dict:
    coin,tf,model,fees=(case[k] for k in ("coin","timeframe","name","fees"))
    p=root/coin/tf/model/fees
    archives=list(p.glob("*.zip"))
    if len(archives)!=1:
        raise ValueError(f"Exactly one strategy ZIP expected in {p}: {len(archives)}")
    with ZipFile(archives[0]) as z:
        ss=[]
        for name in z.namelist():
            if name.endswith(".json") and not name.endswith(".meta.json"):
                obj=json.loads(z.read(name))
                if isinstance(obj,dict) and model in obj.get("strategy",{}):
                    ss.append(obj["strategy"][model])
        if len(ss)!=1:
            raise ValueError(f"Strategy export ambiguous in {archives[0]}")
    s=ss[0]
    trades=s["trades"]
    wallet=float(s["starting_balance"])
    final=float(s["final_balance"])
    net=sum(float(t["profit_abs"]) for t in trades)
    if abs(wallet-150)>.01 or abs(wallet+net-final)>.02:
        raise ValueError(f"Wallet/trade PnL does not reconcile {p}")
    weeks=defaultdict(lambda:{"net_closed_usd":0.,"closed":0,"losing":0})
    months=defaultdict(lambda:{"net_closed_usd":0.,"closed":0})
    losing_streak=0
    max_losing_streak=0
    last_close=None
    holding=[]
    forced=0
    forced_pnl=0.
    organic_trades=0
    organic_wins=0
    wins=0
    losses=0
    for t in sorted(trades,key=lambda x:x["close_date"]):
        if t.get("pair") != f"{coin}/USD:USD":
            raise ValueError(f"Mixed asset {p}")
        if float(t.get("leverage",1))>1.00001:
            raise ValueError(f"Excessive leverage {p}")
        close=datetime.fromisoformat(t["close_date"].replace("Z","+00:00"))
        opened=datetime.fromisoformat(t["open_date"].replace("Z","+00:00"))
        if opened > close or close.tzinfo is None or opened.tzinfo is None:
            raise ValueError(f"Invalid trade dates {p}")
        pnl=float(t["profit_abs"])
        forced_last=t.get("exit_reason")=="force_exit"
        forced+=int(forced_last)
        forced_pnl+=pnl if forced_last else 0
        organic_trades+=int(not forced_last)
        organic_wins+=int(pnl>0 and not forced_last)
        wins+=int(pnl>0)
        losses+=int(pnl<0)
        losing_streak=losing_streak+1 if pnl<0 else 0
        max_losing_streak=max(max_losing_streak,losing_streak)
        holding.append((close-opened).total_seconds()/3600)
        key=close.strftime("%G-W%V")
        weeks[key]["net_closed_usd"]+=pnl
        weeks[key]["closed"]+=1
        weeks[key]["losing"]+=int(pnl<0)
        mon=close.strftime("%Y-%m")
        months[mon]["net_closed_usd"]+=pnl
        months[mon]["closed"]+=1
    result={
        "coin":coin,"timeframe":tf,"votes":case["votes"],
        "cooldown":case["cooldown"],"fees":fees,
        "per_side_fee_model":FEE_PER_SIDE[fees],
        "model":model,
        "starting_balance_usd":round(wallet,6),
        "final_balance_usd":round(final,6),
        "net_usd":round(net,6),
        "return_pct":round(100*(final/wallet-1),4),
        "max_drawdown_pct":round(float(s["max_drawdown_account"])*100,4),
        "trades":len(trades),
        "trades_per_calendar_day":round(len(trades)/DAYS,4),
        "wins":wins,"losses":losses,
        "win_rate_pct":round(wins/len(trades)*100,2) if trades else None,
        "max_consecutive_losses":max_losing_streak,
        "forced_close_count":forced,
        "forced_close_net_usd":round(forced_pnl,6),
        "nonforced_closed_trade_net_usd":round(net-forced_pnl,6),
        "organic_closed_trades":organic_trades,
        "organic_win_count":organic_wins,
        "average_holding_hours":round(sum(holding)/len(holding),2) if holding else None,
        "max_trade_loss_usd":round(min([float(t["profit_abs"]) for t in trades] or [0]),6),
        "weeks_with_negative_closed_trade_pnl":sum(x["net_closed_usd"]<0 for x in weeks.values()),
        "by_close_week":{
            k:{"closed":v["closed"],"losing":v["losing"],
               "net_closed_usd":round(v["net_closed_usd"],6)}
            for k,v in sorted(weeks.items())},
        "by_close_month":{
            k:{"closed":v["closed"],"net_closed_usd":round(v["net_closed_usd"],6)}
            for k,v in sorted(months.items())},
    }
    return result


def build(root:Path)->dict:
    rows=[extract(root,case) for case in ALL]
    if len(rows)!=len(ALL):
        raise ValueError("Missing predeclared research variants")
    bykey={(x["coin"],x["timeframe"],x["votes"],x["cooldown"],x["fees"]):x
           for x in rows}
    stress_pairs=[]
    for row in rows:
        if row["timeframe"]=="12h" or row["cooldown"]!="active" or row["fees"]!="base":
            continue
        stressed=bykey[(row["coin"],row["timeframe"],row["votes"],"active","stress")]
        stress_pairs.append({
            "coin":row["coin"],"timeframe":row["timeframe"],"votes":row["votes"],
            "base_return_pct":row["return_pct"],
            "stress_return_pct":stressed["return_pct"],
            "stress_pnl_delta_usd":round(stressed["net_usd"]-row["net_usd"],6),
            "stress_trades":stressed["trades"],
            "profitable_after_stress":stressed["net_usd"]>0,
        })
    return {
        "mode":"historical_fee_aware_intraday_crypto_paper_backtests",
        "simulation_only_no_real_orders":True,
        "original_eth_strategy_modified":False,
        "openai_inference_calls":0,
        "sample_start_inclusive_utc":START,
        "sample_end_exclusive_utc":END,
        "calendar_days":DAYS,
        "coins":list(COINS),
        "timeframes":list(FAST),
        "agreements_tested":[8,9],
        "risk_modes":{
            "strict":"36h post-close cooldown and 7d after loss, 7d drawdown breaker",
            "active":"3h post-close cooldown and 24h after loss, unchanged 7d 4% drawdown breaker",
        },
        "per_side_fee_assumptions":FEE_PER_SIDE,
        "stress_fee_explanation":"Base 0.05% per side, stressed 0.15% per side as commission plus an extra 0.10% per side slippage/spread proxy. Not observed actual order-book slippage.",
        "independent_wallet_start_usd":150,
        "independent_wallet_per_coin_and_scenario":True,
        "reference_12h_same_calendar_window":True,
        "results":rows,
        "active_fee_stress_comparisons":stress_pairs,
        "not_a_multicoin_shared_wallet_test":True,
        "no_auto_promotion":True,
        "warnings":[
            "Faster candles make more potential decisions, not a guarantee of higher income.",
            "Base 0.05% and stressed 0.15% per-side fees are modeled: real spreads/latency/market impact not measured.",
            "Profits include artificially forced closing of remaining position at the backtest end.",
            "Calendar-week and month profits are closed-trade attribution, NOT mark-to-market period equity.",
            "These are isolated paper account experiments per coin, timeframe, consensus threshold, cooldown and fee.",
            "Freqtrade maximum drawdown can omit some intrabar unrealized losses or sharp gap fills.",
            "12h baseline risk protections defined in candles; short-timeframe implementations use equivalent minutes.",
            "Training period overlaps prior research; no fresh untouched future forward data exists.",
            "Daily/weekly 2%/4% hard account breaker from separate hourly forward ledger is not executable in these Freqtrade backtests.",
        ],
    }


def make_md(report:dict)->str:
    lines=[
        "# High-frequency crypto research — 1h, 15m and 5m",
        "",
        "Real historical Kraken futures candles and hourly mark/funding data; "
        "all returns are Freqtrade **simulations**, $150 initial independent "
        "wallets, maximum 1x notional, original ATR stop and position sizing.",
        "",
        "Dates: Aug 1–Nov 22, 2026 (114 calendar days). This report compares "
        "8-of-10 with 9-of-10 consensus, original strict seven-day loss lock "
        "with an exploratory 24-hour loss lock, and extra trading cost stress.",
        "",
        "The original 12h protected rule is rerun on the **same calendar window**; "
        "its prior whole-year +11% result is NOT used as a false comparison.",
        "",
        "## Every researched candidate — base 0.05% fee per side",
        "",
        "| Coin | TF | Votes | Loss cooldown | Trades | Trades/day | "
        "Net return | Max DD | W/L | Forced exit USD |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for x in report["results"]:
        if x["fees"]!="base":
            continue
        lines.append(
            f"| {x['coin']} | {x['timeframe']} | {x['votes']}/10 | "
            f"{x['cooldown']} | {x['trades']} | "
            f"{x['trades_per_calendar_day']:.3f} | "
            f"{x['return_pct']:+.3f}% | {x['max_drawdown_pct']:.3f}% | "
            f"{x['wins']}/{x['losses']} | {x['forced_close_net_usd']:+.3f} |")
    lines+=["","## Extra cost stress for every faster active-mode candidate",
            "",
            "0.05% per side original model; **0.15% per side** adverse model "
            "(fee plus hypothetical 0.10% slippage/spread per side). "
            "This is a **scenario**, not measured exchange slippage.",
            "",
            "| Coin | TF | Votes | Base return | Stressed return | "
            "Stressed PnL change USD | Stressed trades |",
            "|---|---|---:|---:|---:|---:|---:|"]
    for row in report["active_fee_stress_comparisons"]:
        lines.append(
            f"| {row['coin']} | {row['timeframe']} | {row['votes']} | "
            f"{row['base_return_pct']:+.3f}% | "
            f"{row['stress_return_pct']:+.3f}% | "
            f"{row['stress_pnl_delta_usd']:+.3f} | {row['stress_trades']} |")
    lines+=["","## Interpretation",
            "",
            "At the same measured interval, a fast model is interesting "
            "only if **net return, downside and trade quality** remain defensible "
            "after conservative costs. More trades alone do not imply income.",
            "A nine-vote threshold can reduce false signals but may also "
            "eliminate winning trades.",
            "Strict mode retains original 7-day loss protection in actual "
            "minutes rather than accidentally turning 14 candles into 70 "
            "minutes at 5m. Active mode shortens the single-loss pause to "
            "24 hours, while retaining the seven-day 4% modeled drawdown "
            "guard; that weaker loss cooldown must be evaluated separately.",
            "",
            "Each row represents one independent test of a $150 wallet, not "
            "a tradeable combined crypto portfolio. Backtest max drawdown "
            "does not guarantee real stop execution, and the forward model's "
            "daily/weekly account breakers are NOT implemented here.",
            "",
            "End-of-test forced exits are reported separately. A result "
            "showing no organic winning exit should not be considered proved "
            "profitable just because of an artificially closed final position.",
            "",
            "No strategy, ChatGPT shadow vote, loss limits or live trading "
            "permissions have been changed.",
            ""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--results-root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--markdown",required=True)
    opts=p.parse_args()
    result=build(Path(opts.results_root))
    Path(opts.json).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    Path(opts.markdown).write_text(make_md(result))
    for row in result["results"]:
        if row["fees"]!="base":
            continue
        print("FAST_RESULT",row["coin"],row["timeframe"],row["votes"],
              row["cooldown"],"net",row["return_pct"],
              "trades",row["trades"],"wins",row["wins"],
              "losses",row["losses"],"dd",row["max_drawdown_pct"],
              "forced_usd",row["forced_close_net_usd"])
    print("TOTAL_CASES",len(result["results"]))


if __name__=="__main__":
    main()
