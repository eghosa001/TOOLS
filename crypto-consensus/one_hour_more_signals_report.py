"""Audit 72 real-market 1h ETH multi-signal candidates with trade-frequency constraint.

Three separate historical windows × two fee scenarios × twelve entry models.
Every backtest starts with an independent $150 historical wallet. Report
does not combine early/late wallets into one portfolio and never imports
any simulated profit into the real-time paper observer.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime,timezone
import json
from pathlib import Path
from zipfile import ZipFile

MODELS=(
    "More1h8Both","More1h7Both","More1h6Both",
    "More1h7BTC","More1h6BTC","More1h7SoftBTC",
    "More1h7Flow","More1h6Flow","More1h7Hybrid",
    "More1h7Breakout","More1h7SoftHybrid","More1h6FlowBTC",
)
WINDOWS={
    "early":("2026-01-01","2026-08-01"),
    "later":("2026-08-01","2026-11-23"),
    "full":("2026-01-01","2026-11-23"),
}
FEES={"normal":.0005,"adverse":.0015}
ORIGINAL_ETH_1H_BOTH={
    "early":{"pct":2.8818,"trades":44},
    "later":{"pct":8.4978,"trades":44},
    "full":{"pct":11.6487,"trades":86},
}
BASE_CAPITAL=150.


def utc(value):
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Unaware exchange date in Freqtrade export")
    return dt.astimezone(timezone.utc)


def read_export(root:Path,model:str,window:str,fee:str):
    path=root/model/window/fee
    names=list(path.glob("*.zip"))
    if len(names)!=1:
        raise ValueError(f"Expected exactly one genuine Freqtrade ZIP at {path}, got {len(names)}")
    found=[]
    with ZipFile(names[0]) as archive:
        for name in archive.namelist():
            if not name.endswith(".json") or name.endswith(".meta.json"):
                continue
            candidate=json.loads(archive.read(name))
            if isinstance(candidate,dict) and model in candidate.get("strategy",{}):
                found.append(candidate["strategy"][model])
    if len(found)!=1:
        raise ValueError(f"Ambiguous or missing trade export for {model} {window} {fee}")
    return found[0]


def summarise(root:Path,model:str,window:str,fee:str):
    raw=read_export(root,model,window,fee)
    begin=utc(WINDOWS[window][0]+"T00:00:00Z")
    finish=utc(WINDOWS[window][1]+"T00:00:00Z")
    days=(finish-begin).days
    start=float(raw["starting_balance"])
    end=float(raw["final_balance"])
    trades=raw["trades"]
    pnl=sum(float(t["profit_abs"]) for t in trades)
    if start<=0 or end<=0 or abs(start-BASE_CAPITAL)>.001 or abs(start+pnl-end)>.03:
        raise ValueError("Unreconciled or insolvent Freqtrade account")
    if any(t["pair"]!="ETH/USD:USD" or float(t.get("leverage",1))>1.00001
           for t in trades):
        raise ValueError("Wrong futures instrument or non-1x leverage")
    natural=[]
    forced=[]
    for row in trades:
        opened=utc(row["open_date"])
        closed=utc(row["close_date"])
        if not begin<=opened<finish or not opened<=closed<=finish:
            raise ValueError("Historical trade outside predeclared interval")
        t={"opened":opened,"closed":closed,"net":float(row["profit_abs"])}
        (forced if row.get("exit_reason")=="force_exit" else natural).append(t)
    weeks=defaultdict(lambda:{"closes":0,"net_usd":0.})
    monthly=defaultdict(lambda:{"closes":0,"net_usd":0.,"wins":0,"losses":0})
    positive_days=set()
    negative_days=set()
    by_day=defaultdict(float)
    for t in natural:
        closed=t["closed"]
        wk=closed.strftime("%G-W%V")
        mon=closed.strftime("%Y-%m")
        day=closed.strftime("%Y-%m-%d")
        weeks[wk]["closes"]+=1
        weeks[wk]["net_usd"]+=t["net"]
        monthly[mon]["closes"]+=1
        monthly[mon]["net_usd"]+=t["net"]
        monthly[mon]["wins"]+=int(t["net"]>0)
        monthly[mon]["losses"]+=int(t["net"]<0)
        by_day[day]+=t["net"]
    natural_profit=sum(t["net"] for t in natural)
    forced_profit=sum(t["net"] for t in forced)
    if abs(natural_profit+forced_profit-pnl)>1e-7:
        raise ValueError("Terminal exit attribution not reconciled")
    winstreak=lossstreak=max_loss=0
    winners=[]
    for t in sorted(natural,key=lambda x:x["closed"]):
        if t["net"]<0:
            lossstreak+=1
            max_loss=max(max_loss,lossstreak)
        else:
            lossstreak=0
        if t["net"]>0:
            winners.append(t["net"])
    largest_winner=max(winners,default=0.)
    result={
        "model":model,"window":window,"fee_case":fee,
        "fee_per_side":FEES[fee],
        "start_usd":round(start,6),"end_usd":round(end,6),
        "net_usd":round(pnl,6),
        "return_pct":round(100*(end/start-1),4),
        "days":days,
        "average_account_net_usd_per_day_including_forced":round(pnl/days,6),
        "full_closed_trades":len(trades),
        "natural_closed_trades":len(natural),
        "natural_wins":sum(x["net"]>0 for x in natural),
        "natural_losses":sum(x["net"]<0 for x in natural),
        "natural_trades_per_week":round(len(natural)*7/days,3),
        "natural_closed_profit_usd":round(natural_profit,6),
        "terminal_forced_profit_usd":round(forced_profit,6),
        "terminal_forced_count":len(forced),
        "reported_account_max_drawdown_pct":round(100*float(raw["max_drawdown_account"]),4),
        "max_consecutive_natural_losses":max_loss,
        "largest_natural_winner_usd":round(largest_winner,6),
        "largest_win_share_of_positive_net_pct":round(largest_winner/natural_profit*100,3) if natural_profit>0 else None,
        "naturally_profitable_months":sum(z["net_usd"]>0 for z in monthly.values()),
        "natural_losing_months":sum(z["net_usd"]<0 for z in monthly.values()),
        "positive_closing_trade_days":sum(x>1e-9 for x in by_day.values()),
        "negative_closing_trade_days":sum(x< -1e-9 for x in by_day.values()),
        "no_natural_close_days":days-len(by_day),
        "monthly_natural_closes":{
            k:{**v,"net_usd":round(v["net_usd"],6)}
            for k,v in sorted(monthly.items())},
        "weekly_natural_closes":{
            k:{"closes":v["closes"],"net_usd":round(v["net_usd"],6)}
            for k,v in sorted(weeks.items())},
    }
    return result


def build(root:Path):
    values={
        model:{
            window:{
                fee:summarise(root,model,window,fee)
                for fee in FEES
            } for window in WINDOWS
        } for model in MODELS
    }
    reference=values["More1h8Both"]
    repro={}
    for window,prior in ORIGINAL_ETH_1H_BOTH.items():
        x=reference[window]["normal"]
        matched=abs(x["return_pct"]-prior["pct"])<=.02 and x["full_closed_trades"]==prior["trades"]
        repro[window]={
            "matched":matched,
            "previous_return_pct":prior["pct"],"reproduced_pct":x["return_pct"],
            "previous_trade_count":prior["trades"],"reproduced_trades":x["full_closed_trades"],
        }
        if not matched:
            raise ValueError(f"FROZEN_BASELINE_DRIFT: {window}: {repro[window]}")
    audited={}
    for model in MODELS:
        x=values[model]
        full=x["full"]["normal"]
        stressed=x["full"]["adverse"]
        early=x["early"]["normal"]
        early_stress=x["early"]["adverse"]
        later=x["later"]["normal"]
        later_stress=x["later"]["adverse"]
        ref=reference["full"]["normal"]
        ref_stress=reference["full"]["adverse"]
        # *Strict* predefined screen. Higher trade counts are explicitly
        # prioritized, but no method is promoted unless losses/costs also pass.
        pass_criteria={
            "more_natural_trades_than_control_by_25pct":
                full["natural_closed_trades"]>=int(ref["natural_closed_trades"]*1.25+0.999),
            "early_normal_net_positive":early["net_usd"]>0,
            "later_normal_net_positive":later["net_usd"]>0,
            "early_adverse_fee_net_positive":early_stress["net_usd"]>0,
            "later_adverse_fee_net_positive":later_stress["net_usd"]>0,
            "full_normal_net_at_least_2usd_better":
                full["net_usd"]>=ref["net_usd"]+2,
            "full_adverse_fee_net_at_least_2usd_better":
                stressed["net_usd"]>=ref_stress["net_usd"]+2,
            "full_adverse_fee_net_positive":stressed["net_usd"]>0,
            "full_reported_max_drawdown_le_6pct":
                full["reported_account_max_drawdown_pct"]<=6,
            "adverse_fee_max_drawdown_le_6pct":
                stressed["reported_account_max_drawdown_pct"]<=6,
            "max_loss_streak_le_8":full["max_consecutive_natural_losses"]<=8,
            "no_dependent_terminal_forced_profit":
                abs(full["terminal_forced_profit_usd"])<.10,
            "largest_winner_below_60pct_net":
                full["largest_win_share_of_positive_net_pct"] is not None and
                full["largest_win_share_of_positive_net_pct"]<60,
        }
        audited[model]={
            "pass":all(pass_criteria.values()),
            "checklist":pass_criteria,
            "extra_full_natural_trades":full["natural_closed_trades"]-ref["natural_closed_trades"],
            "extra_full_usd":round(full["net_usd"]-ref["net_usd"],6),
            "extra_stressed_usd":round(stressed["net_usd"]-ref_stress["net_usd"],6),
        }
    return {
        "study":"prospectively_declared_1h_6v7v8_consensus_with_flow_and_macro",
        "market":"ETH/USD:USD","no_orders":True,
        "each_scenario_starts_at_usd":BASE_CAPITAL,
        "real_exchange_data":True,"one_x_max":True,
        "date_windows":WINDOWS,"fees_per_side":FEES,
        "model_names":MODELS,"outcomes":values,
        "frozen_eth_8of10_combined_gate_reproduction":repro,
        "predeclared_extra_trades_and_profit_screen":audited,
        "passes":[m for m in MODELS if audited[m]["pass"]],
        "auto_promote":False,
        "unchanged_current_1h_forward_paper":True,
        "unchanged_existing_12h_paper":True,
        "warnings":[
            "All 2026 intervals are HISTORICAL and have been repeatedly researched; no subset is untouched independent future data.",
            "Agreement of multiple correlated indicators is not a validated accuracy percentage and not independent AI bots.",
            "More trades can worsen losing streaks, fees and loss size. Frequency itself is never proof of profit.",
            "Even an increase from 8/10 to 6/10 cannot imply a guaranteed one trade per day.",
            "Early and later samples restart $150 wallets; full wallet runs continuously. The samples cannot be added together as a real portfolio.",
            "Monthly and weekly closes ignore unrealized PnL and do not represent marked equity or daily cash income.",
            "Backtest terminal force_exit is not a natural strategy signal. Its contribution is separately identified.",
            "Higher fee assumes 0.15% per side as a proxy for adverse trading costs, NOT measured actual historical spread, slippage or orderbook depth.",
            "Historical drawdown may understate intrabar risk; exchange-held stops and the separate observed-equity 2/4/6 locks are not replicated here.",
            "A strong winning trade may dominate total net, and repeated variant testing increases overfitting risk.",
            "A model failing stress gates cannot be promoted to the forward paper bot merely to generate income.",
        ],
    }


def markdown(doc):
    outcomes=doc["outcomes"]
    checks=doc["predeclared_extra_trades_and_profit_screen"]
    lines=[
        "# One-hour ETH: more signals, more trades, real fee and drawdown comparison",
        "",
        "**72 historical Freqtrade simulations; no real orders.**",
        "Twelve preregistered entry hypotheses × three historical date windows "
        "(Jan–Jul, Aug–Nov, continuous Jan–Nov 2026) × two costs "
        "(0.05%/side and 0.15%/side). Each run has an independent $150 wallet.",
        "",
        "New completed-candle evidence: 24-hour rolling VWAP, volume "
        "participation versus prior 24-hour median, 20-hour Chaikin money flow, "
        "6-hour ATR-normalized momentum, prior-20h channel breakout, "
        "and (in some candidates) a less strict completed-BTC 12h EMA macro "
        "regime. REAL Kraken OI/funding crowding veto is retained where "
        "specified. These indicators are correlated, not standalone independent AI bots.",
        "",
        "The baseline More1h8Both is matched against earlier Q1h8Both24 Freqtrade "
        "results trade-for-trade; all existing paper trading remains separate.",
        "",
        "| Entry hypothesis | Jan–Jul net USD | Aug–Nov net USD | "
        "Jan–Nov return | Jan–Nov cost-stress return | Natural trades | "
        "Trades/week | Full max DD | Max loss streak | Largest winner / net | Pass? |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for model in MODELS:
        o=outcomes[model]
        early=o["early"]["normal"]
        later=o["later"]["normal"]
        full=o["full"]["normal"]
        stress=o["full"]["adverse"]
        share=full["largest_win_share_of_positive_net_pct"]
        lines.append(
            f"| {model} | {early['net_usd']:+.3f} | "
            f"{later['net_usd']:+.3f} | {full['return_pct']:+.3f}% | "
            f"{stress['return_pct']:+.3f}% | "
            f"{full['natural_closed_trades']} | {full['natural_trades_per_week']:.2f} | "
            f"{full['reported_account_max_drawdown_pct']:.2f}% | "
            f"{full['max_consecutive_natural_losses']} | "
            f"{f'{share:.1f}%' if share is not None else 'n/a'} | "
            f"{'Pass' if checks[model]['pass'] else 'Fail'} |"
        )
    lines+=["",
        "## Frozen incumbent reproduction",
        "",
    ]
    for name,entry in doc["frozen_eth_8of10_combined_gate_reproduction"].items():
        lines.append(
            f"- {name}: original {entry['previous_return_pct']:+.4f}%/"
            f"{entry['previous_trade_count']} vs research "
            f"{entry['reproduced_pct']:+.4f}%/"
            f"{entry['reproduced_trades']} trades — "
            f"{'MATCHED' if entry['matched'] else 'FAILED'}"
        )
    lines += [
        "",
        "## Predeclared promotion gate",
        "",
        "At least 25% more natural closed trades than 8/10 control; "
        "both historical segments profitable under **both** normal and "
        "higher fees; full normal AND stressed gains each at least "
        "$2 above the control; full DD <=6% under both fee models; "
        "no more than 8 consecutive losing closes; no artificial "
        "terminal close profit >10 cents; largest winner below 60% "
        "of positive natural net. Any failing check rejects the candidate.",
        "",
        "**Passes:** "+(", ".join(doc["passes"]) if doc["passes"] else "**None.**"),
        "",
        "The new 6/10 and 7/10 thresholds permit extra opportunities, "
        "but NO performance claim is accepted without actual additional "
        "net profit under independent fee-stress backtests.",
        "",
        "**No live trades, no automatic activation, no existing 12-hour "
        "strategy replacement, no modification to the ETH 1-hour prospective "
        "paper-ledger, and no guarantee of daily income.**",
        "",
    ]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--markdown",required=True)
    args=p.parse_args()
    doc=build(Path(args.root))
    Path(args.json).write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    Path(args.markdown).write_text(markdown(doc))
    for model in MODELS:
        v=doc["outcomes"][model]
        f=v["full"]["normal"]
        s=v["full"]["adverse"]
        print("MORE_1H_RESULT",model,
              "trades",f["natural_closed_trades"],
              "normal_pct",f["return_pct"],
              "stressed_pct",s["return_pct"],
              "early_usd",v["early"]["normal"]["net_usd"],
              "late_usd",v["later"]["normal"]["net_usd"],
              "cost_stress_early_usd",v["early"]["adverse"]["net_usd"],
              "cost_stress_late_usd",v["later"]["adverse"]["net_usd"],
              "maxdd",f["reported_account_max_drawdown_pct"],
              "max_loss_streak",f["max_consecutive_natural_losses"],
              "largest_win_share",f["largest_win_share_of_positive_net_pct"],
              "pass",doc["predeclared_extra_trades_and_profit_screen"][model]["pass"])
    print("ONEH_MORE_SIGNALS_PASSES",doc["passes"])


if __name__=="__main__":
    main()
