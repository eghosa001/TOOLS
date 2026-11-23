"""Compare four preregistered ETH futures models on identical historical fills.

Original strategy is untouched and no real orders may be placed.
Historical 'later' interval had previously been inspected and is NOT blind OOS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from zipfile import ZipFile

STRATEGIES=("GuardedConsensusETH","ResearchBTCRegimeETH",
            "ResearchFundingOpenInterestETH","ResearchVolatilityBreakoutETH",
            "ResearchOnlineRidgeETH")
WINDOWS=("train","holdout","full")
NAMES={"GuardedConsensusETH":"Original 10 indicators",
"ResearchBTCRegimeETH":"BTC market regime",
"ResearchFundingOpenInterestETH":"Actual funding + OI",
"ResearchVolatilityBreakoutETH":"Volatility breakout",
"ResearchOnlineRidgeETH":"Time-ordered rolling ML"}


def read_one(root, window, name):
    files=list((Path(root)/window/name).glob("*.zip"))
    if len(files)!=1:
        raise RuntimeError(f"Expected one export for {window}/{name}, found {len(files)}")
    with ZipFile(files[0]) as z:
        found=[]
        for fname in z.namelist():
            if fname.endswith(".json") and not fname.endswith(".meta.json"):
                obj=json.loads(z.read(fname))
                if isinstance(obj,dict) and name in obj.get("strategy",{}):
                    found.append(obj["strategy"][name])
    if len(found)!=1:
        raise RuntimeError("No unambiguous strategy export: "+name)
    data=found[0]
    trades=data["trades"]
    first=float(data["starting_balance"])
    final=float(data["final_balance"])
    net=sum(float(t["profit_abs"]) for t in trades)
    if abs(final-first-net)>.02:
        raise RuntimeError("Wallet/trade accounting mismatch: "+name+"/"+window)
    loss=[t for t in trades if float(t["profit_abs"])<0]
    win=[t for t in trades if float(t["profit_abs"])>0]
    force=[t for t in trades if t.get("exit_reason")=="force_exit"]
    return {
        "start_usd":first,
        "end_usd":round(final,6),
        "net_usd":round(net,6),
        "return_pct":round(100*(final/first-1),4),
        "max_drawdown_pct":round(100*float(data["max_drawdown_account"]),4),
        "trades":len(trades),"wins":len(win),"losses":len(loss),
        "forced_exits":len(force),
        "forced_exit_pnl_usd":round(sum(float(t["profit_abs"]) for t in force),6),
        "worst_trade_usd":round(min([float(t["profit_abs"]) for t in trades] or [0]),6),
        "losing_trades":[{
            "opened":t.get("open_date"),
            "closed":t.get("close_date"),
            "side":"short" if t.get("is_short") else "long",
            "net_usd":round(float(t["profit_abs"]),6),
            "exit":t.get("exit_reason"),
        } for t in loss],
    }


def research_screen(data,name):
    b=data["GuardedConsensusETH"]
    c=data[name]
    t,h,f=c["train"],c["holdout"],c["full"]
    bt,bh,bf=b["train"],b["holdout"],b["full"]
    conditions={
        "sufficient_trades":f["trades"]>=5,
        "positive_training":t["net_usd"]>0,
        "training_retains_80pct_profit":t["net_usd"]>=.8*max(0,bt["net_usd"]),
        "training_drawdown_not_worse":t["max_drawdown_pct"]<=bt["max_drawdown_pct"]+.05,
        "positive_later_interval":h["net_usd"]>0,
        "later_profit_not_worse":h["net_usd"]>=bh["net_usd"],
        "later_drawdown_not_worse":h["max_drawdown_pct"]<=bh["max_drawdown_pct"]+.05,
        "full_retains_90pct_profit":f["net_usd"]>=.9*max(0,bf["net_usd"]),
        "full_fewer_loss_trades":f["losses"]<bf["losses"],
        "full_drawdown_not_worse":f["max_drawdown_pct"]<=bf["max_drawdown_pct"]+.05,
    }
    return {"passes":all(conditions.values()),"conditions":conditions}


def make_report(root):
    data={name:{window:read_one(root,window,name) for window in WINDOWS}
          for name in STRATEGIES}
    checks={name:research_screen(data,name) for name in STRATEGIES[1:]}
    return {
        "mode":"historical_freqtrade_simulation_not_real_trading",
        "no_real_orders":True,
        "original_protected_strategy_changed":False,
        "data_sources":["Kraken Futures ETH USD 12h OHLCV",
                        "Kraken Futures BTC USD 12h OHLCV",
                        "Kraken futures actual hourly funding and mark",
                        "Kraken official 4h open interest analytics"],
        "capital_start_usd":150,
        "max_leverage":1,
        "per_side_simulated_fee":.0005,
        "intervals":{"train":"2026-01-01 to 2026-06-30",
                     "holdout":"2026-07-01 to 2026-11-22 (previously studied, not untouched)",
                     "full":"2026-01-01 to 2026-11-22 one continuous account"},
        "data":data,"research_checks":checks,
        "passes":[s for s,v in checks.items() if v["passes"]],
        "automatic_promotion":False,
        "warnings":[
            "All four experimental models are gates on top of the existing 10 indicators, not four independently managed trading bots.",
            "Later window was previously seen during earlier tests; not statistically untouched out-of-sample.",
            "Historical mark and funding are exchange-sourced but fills, stop gaps and slippage are simulated.",
            "The end-of-test force_exit closes a still-open position; do not treat that as a natural exit or reliable realized profit.",
            "Multiple trials and very few trade outcomes make historical superiority uncertain; forward validation required.",
        ],
    }


def markdown(r):
    lines=[
        "# Four quality ETH models: same-cost, same-risk comparison","",
        "All results are historical paper simulations. Original 10-vote protected ETH bot unchanged.",
        "Kraken futures candles, mark, actual hourly funding, official 4h open interest,",
        "one initial 150 USD modeled wallet and 1x nominal exposure.",
        "",
        "First half and later half are each restarted scenario tests. FULL is a single",
        "uninterrupted Jan-Nov account. Later half was previously inspected in earlier",
        "projects and cannot be presented as truly untouched out-of-sample evidence.",
        "",
        "| Research model | Jan-Jun net USD | Jul-Nov net USD | Jan-Nov return | Full net USD | Trades | W/L | DD | Pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name in STRATEGIES:
        t=r["data"][name]["train"]
        h=r["data"][name]["holdout"]
        f=r["data"][name]["full"]
        mark="Reference" if name==STRATEGIES[0] else (
            "Pass - research only" if r["research_checks"][name]["passes"] else "Fail")
        lines.append(
            f"| {NAMES[name]} | {t['net_usd']:+.3f} | {h['net_usd']:+.3f} | "
            f"{f['return_pct']:+.3f}% | {f['net_usd']:+.3f} | {f['trades']} | "
            f"{f['wins']}/{f['losses']} | {f['max_drawdown_pct']:.3f}% | {mark} |")
    lines += [
        "",
        "## What was tested",
        "",
        "- BTC regime: conservative one-candle-delayed BTC futures EMA100 and momentum.",
        "- Derivatives crowding: genuine Kraken 4-hour open interest, prior published",
        "  hourly funding, and changes in how crowded directional positioning is.",
        "- Breakout: a completed 12-hour ETH bar breaking the prior three-day",
        "  trading range while measured volatility is neither too quiet nor extreme.",
        "- Rolling machine learning: expanding chronological predictions from",
        "  240 past bars of price and volume, ridge regularization, standardization",
        "  using training data only, and one-candle label embargo.",
        "",
        "Every candidate filters entries from the SAME original ten-indicator",
        "consensus and retains the existing protective position sizing and exits.",
        "",
        "## All simulated losing closes (full Jan-Nov account)","",
    ]
    for name in STRATEGIES:
        x=r["data"][name]["full"]
        lines.append(f"### {NAMES[name]} ({x['losses']} losing trades)")
        for t in x["losing_trades"]:
            lines.append(f"- {t['opened']} to {t['closed']} "
                         f"{t['side']}: {t['net_usd']:+.3f} USD [{t['exit']}]")
        if not x["losing_trades"]:
            lines.append("- No losing close in this tested interval; not proof of future safety.")
        lines.append("")
    lines += [
        "## Evidence threshold","",
        "Predeclared before viewing these candidate outcomes: >=5 full trades,",
        "positive first-half and later-half profit, >=80% training profit retained,",
        ">=90% full profit retained, later-half profit at least baseline, fewer",
        "full-period losing trades, no worse full, training or later drawdown",
        "(0.05 percentage-point numerical tolerance).",
        "",
        "Research-screen passes: "+(", ".join(NAMES[x] for x in r["passes"])
                                   if r["passes"] else "None")+".",
        "",
        "No historical model is approved for automatic production promotion.",
        "Fees and funding already affect reported Freqtrade net profits.",
        "Forced exits, candle granularity, multiple testing and feed provenance",
        "limit any interpretation as future exchange profitability.",
    ]
    return "\n".join(lines)+"\n"


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--markdown",required=True)
    args=p.parse_args()
    report=make_report(Path(args.root))
    Path(args.json).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    Path(args.markdown).write_text(markdown(report))
    for name in STRATEGIES:
        f=report["data"][name]["full"]
        print("QUALITY_RESULT",name,"net",f["net_usd"],"pct",f["return_pct"],
              "trades",f["trades"],"wins",f["wins"],"losses",f["losses"],
              "drawdown_pct",f["max_drawdown_pct"],"forced",f["forced_exits"])
    print("RESEARCH_SCREEN_PASSES",report["passes"])


if __name__=="__main__":
    main()
