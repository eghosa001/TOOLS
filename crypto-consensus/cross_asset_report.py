"""Cross-asset historical risk/return comparisons: NO live orders or portfolio claims."""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
from zipfile import ZipFile

COINS=("BTC","SOL","XRP","DOGE","ADA")
BASE="CrossAssetProtectedConsensus"
OI="CrossAssetFundingOIConsensus"
WINDOWS=("train","later","full")


def read_one(root,coin,window,model):
    folder=Path(root)/coin/window/model
    archives=list(folder.glob("*.zip"))
    if len(archives)!=1:
        raise RuntimeError(f"Expected one backtest ZIP {folder}, got {len(archives)}")
    with ZipFile(archives[0]) as z:
        matches=[]
        for name in z.namelist():
            if name.endswith(".json") and not name.endswith(".meta.json"):
                obj=json.loads(z.read(name))
                if isinstance(obj,dict) and model in obj.get("strategy",{}):
                    matches.append(obj["strategy"][model])
    if len(matches)!=1:
        raise RuntimeError(f"Missing backtest strategy export for {folder}")
    b=matches[0]
    trades=b["trades"]
    for t in trades:
        if t.get("pair") != coin+"/USD:USD":
            raise RuntimeError("Mixed markets in one-coin comparison")
        if float(t.get("leverage",1))>1.00001:
            raise RuntimeError("Unexpected leverage")
    start=float(b["starting_balance"])
    finish=float(b["final_balance"])
    net=sum(float(t["profit_abs"]) for t in trades)
    if start!=150 or abs(finish-start-net)>.02:
        raise RuntimeError("Balance reconciliation mismatch")
    weeks=defaultdict(lambda:{"closed_trades":0,"net_closed_trade_usd":0.,"losers":0})
    for t in trades:
        stamp=datetime.fromisoformat(t["close_date"].replace("Z","+00:00"))
        k=stamp.strftime("%G-W%V")
        weeks[k]["closed_trades"]+=1
        weeks[k]["net_closed_trade_usd"]+=float(t["profit_abs"])
        weeks[k]["losers"]+=int(float(t["profit_abs"])<0)
    forced=[t for t in trades if t.get("exit_reason")=="force_exit"]
    return {
        "net_usd":round(net,6),
        "return_pct":round(100*(finish/start-1),4),
        "starting_usd":start,
        "ending_usd":round(finish,6),
        "closed_trades":len(trades),
        "wins":sum(float(t["profit_abs"])>0 for t in trades),
        "losses":sum(float(t["profit_abs"])<0 for t in trades),
        "max_drawdown_pct":round(100*float(b["max_drawdown_account"]),4),
        "force_exit_count":len(forced),
        "force_exit_net_usd":round(sum(float(t["profit_abs"]) for t in forced),6),
        "weekly_closed_trade_attribution":{
            k:{**v,"net_closed_trade_usd":round(v["net_closed_trade_usd"],6)}
            for k,v in sorted(weeks.items())},
    }


def evaluate(data,coin):
    orig=data[coin][BASE]
    alt=data[coin][OI]
    a,b,c=(alt[w] for w in WINDOWS)
    x,y,z=(orig[w] for w in WINDOWS)
    rules={
        "at_least_five_full_trades":c["closed_trades"]>=5,
        "training_positive":a["net_usd"]>0,
        "later_positive":b["net_usd"]>0,
        "full_positive":c["net_usd"]>0,
        "full_profit_improves":c["net_usd"]>z["net_usd"],
        "full_loss_count_not_more":c["losses"]<=z["losses"],
        "full_drawdown_not_more":c["max_drawdown_pct"]<=z["max_drawdown_pct"]+.05,
        "later_profit_not_worse":b["net_usd"]>=y["net_usd"]-.1,
    }
    return {
        "rules":rules,
        "passes_research_screen":all(rules.values()),
        "profit_delta_usd":round(c["net_usd"]-z["net_usd"],6),
        "drawdown_delta_points":round(c["max_drawdown_pct"]-z["max_drawdown_pct"],4),
    }


def build(root,manifest):
    records=json.loads(Path(manifest).read_text())
    data={coin:{model:{window:read_one(root,coin,window,model)
                       for window in WINDOWS} for model in (BASE,OI)}
          for coin in COINS}
    screens={coin:evaluate(data,coin) for coin in COINS}
    return {
        "mode":"keyless_kraken_futures_historical_simulations_only",
        "no_real_orders":True,
        "simulation_capital_per_coin_per_scenario_usd":150,
        "same_fee_per_side":0.0005,
        "max_leverage":1,
        "market_data_manifest":records,
        "windows":{"train":"2026-01-01 to 2026-06-30",
                   "later":"2026-07-01 to 2026-11-22",
                   "full":"2026-01-01 to 2026-11-22 uninterrupted separate coin account"},
        "models":data,
        "research_screens":screens,
        "research_passes":[coin for coin,v in screens.items()
                           if v["passes_research_screen"]],
        "production_changed":False,
        "warnings":[
            "Every coin was tested in a separate $150 wallet. Never aggregate as a five-coin portfolio.",
            "A historical win does not imply future profitability or authorize live trading.",
            "Closed-trade weekly totals are NOT full weekly mark-to-market equity.",
            "Reported backtest drawdown can miss interim open-position adverse movements.",
            "One or more last trades may be force-closed at the test endpoint.",
            "Fees and actual exchange funding are included in Freqtrade net results; fills, gaps and slippage are simulated.",
            "Selecting among five coins and two variants on the same history can overfit: genuine new forward weeks required.",
        ],
    }


def markdown(r):
    out=[
        "# Five additional cryptocurrencies: protected strategy cross-market test",
        "",
        "All results are simulated using public Kraken futures historical data, "
        "real hourly funding/mark and real 4h open interest. Modelled $150 "
        "starting capital and 1x max notional PER COIN, not a pooled multi-coin portfolio.",
        "The original live-disabled ETH paper observer and strategy were not changed.",
        "",
        "| Coin | Original return | Funding/OI return | OI trades W/L | "
        "Original DD | Funding/OI DD | Decision |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for coin in COINS:
        a=r["models"][coin][BASE]["full"]
        b=r["models"][coin][OI]["full"]
        mark="Research candidate" if r["research_screens"][coin]["passes_research_screen"] else "Reject for now"
        out.append(f"| {coin} | {a['return_pct']:+.3f}% | {b['return_pct']:+.3f}% | "
                   f"{b['wins']}/{b['losses']} | {a['max_drawdown_pct']:.3f}% | "
                   f"{b['max_drawdown_pct']:.3f}% | {mark} |")
    out.extend([
        "",
        "## Independent time windows (profit USD, each restarted at $150)",
        "",
        "| Coin | Jan-Jun base | Jan-Jun funding/OI | Jul-Nov base | "
        "Jul-Nov funding/OI | Full base trades | Full funding/OI trades |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for coin in COINS:
        a,b=(r["models"][coin][m] for m in (BASE,OI))
        out.append(f"| {coin} | {a['train']['net_usd']:+.3f} | "
                   f"{b['train']['net_usd']:+.3f} | {a['later']['net_usd']:+.3f} | "
                   f"{b['later']['net_usd']:+.3f} | "
                   f"{a['full']['closed_trades']} | {b['full']['closed_trades']} |")
    out.extend([
        "",
        "## End-of-test forced trade close sensitivity",
        "",
        "| Coin | Base forced close USD (count) | Funding/OI forced close USD (count) |",
        "|---|---:|---:|",
    ])
    for coin in COINS:
        a,b=(r["models"][coin][m]["full"] for m in (BASE,OI))
        out.append(f"| {coin} | {a['force_exit_net_usd']:+.3f} "
                   f"({a['force_exit_count']}) | {b['force_exit_net_usd']:+.3f} "
                   f"({b['force_exit_count']}) |")
    out.extend([
        "",
        "## Interpreting these results",
        "",
        "A research-screen pass requires positive development/later/full returns, "
        "at least 5 full trades, higher full-period return than that coin's "
        "original baseline, no higher drawdown (0.05 percentage-point tolerance), "
        "no more losing trades and no material late-period regression (>10 cents). "
        "These criteria are not permission to deploy.",
        "",
        "A full-window result is a continuously modelled *single-coin* wallet; "
        "the first-half and later-half tests each start again at $150. "
        "Weekly close-based amounts in the JSON are NOT weekly equity returns. "
        "The historical last position may have been artificially force-closed. "
        "The same 10 indicators are correlated, so adding coins also introduces "
        "cross-coin crash correlation and exchange capacity risks.",
        "",
        "**Production:** None of these five currencies have been switched on "
        "for trading, and no real orders or exchange credentials were used.",
        "",
    ])
    return "\n".join(out)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--markdown",required=True)
    args=p.parse_args()
    result=build(Path(args.root),args.manifest)
    Path(args.json).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    Path(args.markdown).write_text(markdown(result))
    for coin in COINS:
        a=result["models"][coin][BASE]["full"]
        b=result["models"][coin][OI]["full"]
        print("CROSS_ASSET_RESULT",coin,"base_pct",a["return_pct"],
              "oi_pct",b["return_pct"],"base_trades",a["closed_trades"],
              "oi_trades",b["closed_trades"],"oi_losses",b["losses"],
              "oi_max_dd",b["max_drawdown_pct"],
              "screen",result["research_screens"][coin]["passes_research_screen"])
    print("RESEARCH_PASSES",result["research_passes"])


if __name__=="__main__":
    main()
