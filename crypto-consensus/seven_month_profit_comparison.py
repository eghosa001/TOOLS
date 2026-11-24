"""Seven calendar months: same-start $150 ETH futures 12h vs three 1h models.

Data: exported, reconciled actual Freqtrade historical simulations.
Calendar: May 1 2026 00:00 UTC to Nov 23 2026 00:00 UTC exclusive.
- Backtest account is new at start for EACH strategy and fee scenario.
- Monthly/daily summaries are naturally CLOSED trade PnL only (not equity).
- Never show a forced terminal close as natural daily earnings.
- Returns include exchange funding and modeled fee within Freqtrade PnL.
- No real trading, no promise of daily returns.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date,datetime,timedelta,timezone
import json
from pathlib import Path
from zipfile import ZipFile

START=datetime(2026,5,1,tzinfo=timezone.utc)
END=datetime(2026,11,23,tzinfo=timezone.utc)
DAYS=(END-START).days
MONTHS=("2026-05","2026-06","2026-07","2026-08","2026-09","2026-10","2026-11")
START_CAPITAL=150.
MODELS={
    "12h_original":"GuardedConsensusETH",
    "1h_unfiltered":"Q1h8Base24",
    "1h_btc_regime":"Q1h8BTC24",
    "1h_btc_funding_oi":"Q1h8Both24",
}
COSTS={"normal":.0005,"stress":.0015}


def parsedate(text:str)->datetime:
    out=datetime.fromisoformat(str(text).replace("Z","+00:00"))
    if out.tzinfo is None:
        raise ValueError("Trade timestamp is not UTC/offset aware")
    return out.astimezone(timezone.utc)


def read_export(root:Path,model_id:str,fee_id:str):
    where=root/model_id/fee_id
    archives=list(where.glob("*.zip"))
    if len(archives)!=1:
        raise ValueError(f"Expected exactly one backtest ZIP in {where}; found {len(archives)}")
    matches=[]
    with ZipFile(archives[0]) as archive:
        for name in archive.namelist():
            if not name.endswith(".json") or name.endswith(".meta.json"):
                continue
            contents=json.loads(archive.read(name))
            if isinstance(contents,dict) and MODELS[model_id] in contents.get("strategy",{}):
                matches.append(contents["strategy"][MODELS[model_id]])
    if len(matches)!=1:
        raise ValueError(f"No uniquely auditable Freqtrade trade export for {model_id} {fee_id}")
    return matches[0]


def metric(root:Path,model_id:str,fee_id:str)->dict:
    model=read_export(root,model_id,fee_id)
    trades=model["trades"]
    start=float(model["starting_balance"])
    end=float(model["final_balance"])
    net=sum(float(t["profit_abs"]) for t in trades)
    if start<=0 or end<=0 or abs(start-START_CAPITAL)>.001 or abs(start+net-end)>.025:
        raise ValueError(f"Unreconciled initial wallet / trade profits for {model_id} {fee_id}")
    if any(t.get("pair")!="ETH/USD:USD" for t in trades):
        raise ValueError("Mixed market or invented instrument")
    if any(float(t.get("leverage",1))>1.00001 for t in trades):
        raise ValueError("1x maximum leveraged account violated")
    natural=[]
    forced=[]
    for trade in trades:
        opened=parsedate(trade["open_date"])
        closed=parsedate(trade["close_date"])
        if opened<START or opened>=END or closed<opened or closed>END:
            raise ValueError(f"Trade leaked outside fixed seven-month window: {model_id}")
        row={"opened":opened,"closed":closed,"net":float(trade["profit_abs"]),
             "exit_reason":trade.get("exit_reason"),
             "side":"short" if trade.get("is_short",False) else "long",
             "open_price":trade.get("open_rate"),
             "close_price":trade.get("close_rate")}
        if trade.get("exit_reason")=="force_exit":
            forced.append(row)
        else:
            if not START<=closed<END:
                raise ValueError("Natural exit at artificial end boundary")
            natural.append(row)
    month_data={month:{"naturally_closed_trades":0,"natural_closed_net_usd":0.,
                       "wins":0,"losses":0,"positive_close_days":0,
                       "negative_close_days":0,"no_close_days":0}
                for month in MONTHS}
    daily=defaultdict(lambda:{"closed":0,"natural_net_usd":0.,"wins":0,"losses":0})
    for t in natural:
        key=t["closed"].date().isoformat()
        month=key[:7]
        if month not in month_data:
            raise ValueError("Out-of-window natural trade close")
        row=month_data[month]
        row["naturally_closed_trades"]+=1
        row["natural_closed_net_usd"]+=t["net"]
        row["wins"]+=int(t["net"]>0)
        row["losses"]+=int(t["net"]<0)
        day=daily[key]
        day["closed"]+=1
        day["natural_net_usd"]+=t["net"]
        day["wins"]+=int(t["net"]>0)
        day["losses"]+=int(t["net"]<0)
    per_day={}
    cursor=START.date()
    while cursor<END.date():
        key=cursor.isoformat()
        d=daily.get(key,{"closed":0,"natural_net_usd":0.,"wins":0,"losses":0})
        row={"natural_closed_trades":d["closed"],
             "natural_closed_net_usd":round(d["natural_net_usd"],6),
             "wins":d["wins"],"losses":d["losses"]}
        per_day[key]=row
        mon=month_data[key[:7]]
        mon["positive_close_days"]+=int(row["natural_closed_net_usd"]>1e-10)
        mon["negative_close_days"]+=int(row["natural_closed_net_usd"]< -1e-10)
        mon["no_close_days"]+=int(row["natural_closed_trades"]==0)
        cursor+=timedelta(days=1)
    month_data={m:{**r,"natural_closed_net_usd":round(r["natural_closed_net_usd"],6)}
                for m,r in month_data.items()}
    natural_sum=sum(t["net"] for t in natural)
    forced_sum=sum(t["net"] for t in forced)
    if abs(net-natural_sum-forced_sum)>1e-6:
        raise ValueError("Natural and artificial trade-close reconciliation failure")
    active_days=sum(x["natural_closed_trades"]>0 for x in per_day.values())
    positive_days=sum(x["natural_closed_net_usd"]>1e-10 for x in per_day.values())
    negative_days=sum(x["natural_closed_net_usd"]< -1e-10 for x in per_day.values())
    day_values=[x["natural_closed_net_usd"] for x in per_day.values()]
    winners=sorted((x["net"] for x in natural if x["net"]>0),reverse=True)
    largest_win=winners[0] if winners else 0.
    largest_loss=min((x["net"] for x in natural),default=0.)
    streak=longest=0
    for t in sorted(natural,key=lambda x:x["closed"]):
        streak=streak+1 if t["net"]<0 else 0
        longest=max(longest,streak)
    full={
        "model":MODELS[model_id],
        "timeframe":"12h" if model_id=="12h_original" else "1h",
        "fee_per_side":COSTS[fee_id],
        "starting_wallet_usd":start,
        "ending_wallet_usd":round(end,6),
        "net_with_forced_terminal_usd":round(net,6),
        "account_return_with_forced_terminal_pct":round(100*(end/start-1),4),
        "average_backtest_net_per_calendar_day_including_forced_usd":round(net/DAYS,6),
        "naturally_closed_trade_profit_usd":round(natural_sum,6),
        "natural_closed_profit_per_calendar_day_usd":round(natural_sum/DAYS,6),
        "forced_terminal_count":len(forced),
        "forced_terminal_profit_usd":round(forced_sum,6),
        "closed_trades_including_forced":len(trades),
        "naturally_closed_trades":len(natural),
        "natural_wins":sum(t["net"]>0 for t in natural),
        "natural_losses":sum(t["net"]<0 for t in natural),
        "naturally_closed_trades_per_week":round(len(natural)*7/DAYS,3),
        "days_with_natural_trade_close":active_days,
        "days_with_no_natural_trade_close":DAYS-active_days,
        "days_with_positive_closed_net":positive_days,
        "days_with_negative_closed_net":negative_days,
        "fraction_of_calendar_days_with_positive_closed_net_pct":round(100*positive_days/DAYS,3),
        "best_natural_closed_profit_day_usd":round(max(day_values),6),
        "worst_natural_closed_profit_day_usd":round(min(day_values),6),
        "largest_natural_winning_trade_usd":round(largest_win,6),
        "largest_natural_losing_trade_usd":round(largest_loss,6),
        "top_one_natural_win_share_of_natural_net_pct":(
            round(largest_win/natural_sum*100,2) if natural_sum>0 else None),
        "top_two_natural_wins_share_of_natural_net_pct":(
            round(sum(winners[:2])/natural_sum*100,2) if natural_sum>0 else None),
        "longest_natural_closing_loss_streak":longest,
        "reported_backtester_max_drawdown_pct":round(100*float(model["max_drawdown_account"]),4),
        "month_closes":month_data,
        "day_closes":per_day,
    }
    if abs(sum(x["natural_closed_net_usd"] for x in month_data.values())-natural_sum)>.00001:
        raise ValueError("Monthly natural realized profits do not reconcile")
    return full


def comparison(rows):
    pair={}
    for fee in COSTS:
        a=rows["1h_btc_funding_oi"][fee]
        b=rows["12h_original"][fee]
        pair[fee]={
            "one_hour_minus_twelve_hour_account_return_pct_points":round(
                a["account_return_with_forced_terminal_pct"]-
                b["account_return_with_forced_terminal_pct"],4),
            "one_hour_minus_twelve_hour_profit_usd_including_forced":round(
                a["net_with_forced_terminal_usd"]-
                b["net_with_forced_terminal_usd"],6),
            "one_hour_minus_twelve_hour_mean_profit_per_day_usd_including_forced":round(
                (a["net_with_forced_terminal_usd"]-
                 b["net_with_forced_terminal_usd"])/DAYS,6),
            "one_hour_minus_twelve_hour_natural_closed_profit_usd":round(
                a["naturally_closed_trade_profit_usd"]-
                b["naturally_closed_trade_profit_usd"],6),
            "one_hour_natural_positive_close_days":a["days_with_positive_closed_net"],
            "twelve_hour_natural_positive_close_days":b["days_with_positive_closed_net"],
            "one_hour_positive_natural_months":sum(
                x["natural_closed_net_usd"]>0 for x in a["month_closes"].values()),
            "twelve_hour_positive_natural_months":sum(
                x["natural_closed_net_usd"]>0 for x in b["month_closes"].values()),
            "one_hour_natural_trades":a["naturally_closed_trades"],
            "twelve_hour_natural_trades":b["naturally_closed_trades"],
            "one_hour_drawdown_minus_twelve_hour_points":round(
                a["reported_backtester_max_drawdown_pct"]-
                b["reported_backtester_max_drawdown_pct"],4),
        }
    return pair


def create(root):
    rows={name:{fee:metric(root,name,fee) for fee in COSTS} for name in MODELS}
    return {
        "simulation_only_no_real_orders":True,
        "project":"Crypto",
        "comparison_start_inclusive_utc":START.isoformat(),
        "comparison_end_exclusive_utc":END.isoformat(),
        "calendar_days":DAYS,
        "months_including_partial_november":MONTHS,
        "wallet_usd_per_strategy_per_fee_scenario":START_CAPITAL,
        "matched_same_dates":True,
        "strategy_packages_differ_in_indicators_filters_cooldowns_and_timeframe":True,
        "models":rows,
        "matched_1h_vs_12h_comparison":comparison(rows),
        "warnings":[
            "Every account is a historical simulation and NOT money earned by the user.",
            "Calendar-day total return divided by days is a mathematical AVERAGE, not daily income or expected future average.",
            "The final November period is partial (Nov 1-22); monthly natural closes are not monthly account equity.",
            "Monthly and daily closing trade PnL EXCLUDES artificial end-of-period forced exit and ignores unrealized positions crossing calendar boundaries.",
            "The reported end-wallet PnL DOES INCLUDE an artificial Freqtrade forced terminal close; the exit is NOT a strategy signal.",
            "The filtered one-hour model and original 12-hour model also differ in loss cooldown (24h vs original 7d) and entry gates, so this is a strategy package comparison, not an isolated timeframe experiment.",
            "The higher-fee 0.15% per side is adverse friction scenario; not empirical fill/slippage data.",
            "The seven-month window has already been seen historically and is NOT forward out-of-sample evidence.",
            "No hypothesis test with appropriate independence and forward sample is established; higher numeric return alone is not statistical proof.",
            "One $150 wallet per scenario; never add results into a real multi-strategy portfolio.",
            "Intrabar liquidation/gap risk not fully reflected by Freqtrade backtester drawdown.",
        ],
    }


def markdown(r):
    rows=r["models"]
    out=[
        "# Seven-month matched ETH futures profit audit: 1h versus 12h",
        "",
        "**Historical simulated results; no real earnings or orders.**",
        "",
        "Dates: **2026-05-01 00:00 UTC through 2026-11-22 23:59 UTC** "
        "(November 23 exclusive), seven named calendar months, November partial. "
        f"Total **{DAYS} calendar days**.",
        "",
        "Every strategy and cost scenario starts with its OWN **$150** paper "
        "account, 1x maximum leverage; both use actual Kraken historical "
        "perpetual futures data and modeled fees/funding. Historical research "
        "already viewed, not new forward test. 12h original has seven-day "
        "loss pause; improved 1h uses 24-hour loss pause, BTC completed "
        "macro gate and official Kraken futures funding/OI veto. Their "
        "differences are not solely due to candle duration.",
        "",
        "## Total profit and average per calendar day",
        "",
        "| Strategy | Fee / side | Seven-month return* | Profit USD* | "
        "Average USD/day* | Natural closed trades | Backtester max DD | "
        "Forced terminal profit USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in MODELS:
        for fee in COSTS:
            x=rows[name][fee]
            out.append(
                f"| {name} | {x['fee_per_side']*100:.2f}% | "
                f"{x['account_return_with_forced_terminal_pct']:+.3f}% | "
                f"{x['net_with_forced_terminal_usd']:+.3f} | "
                f"{x['average_backtest_net_per_calendar_day_including_forced_usd']:+.4f} | "
                f"{x['naturally_closed_trades']} | "
                f"{x['reported_backtester_max_drawdown_pct']:.3f}% | "
                f"{x['forced_terminal_profit_usd']:+.3f} |"
            )
    out+=["",
          "*Includes a modeled artificial closing of any position at the "
          "end of the test. Dividing by 206 days does NOT mean the bot "
          "earned that amount every day.",
          "",
          "## Main comparison: improved 1h minus original 12h",
          "",
          "| Fee / side | Difference in 7mo profit USD* | Difference in "
          "return percentage points* | Difference per calendar day USD* | "
          "Natural 1h/12h closed trades | Natural profitable 1h/12h months |",
          "|---|---:|---:|---:|---:|---:|"]
    for fee in COSTS:
        a=r["matched_1h_vs_12h_comparison"][fee]
        out.append(
            f"| {COSTS[fee]*100:.2f}% | "
            f"{a['one_hour_minus_twelve_hour_profit_usd_including_forced']:+.3f} | "
            f"{a['one_hour_minus_twelve_hour_account_return_pct_points']:+.3f} | "
            f"{a['one_hour_minus_twelve_hour_mean_profit_per_day_usd_including_forced']:+.4f} | "
            f"{a['one_hour_natural_trades']}/{a['twelve_hour_natural_trades']} | "
            f"{a['one_hour_positive_natural_months']}/{a['twelve_hour_positive_natural_months']} |")
    out+=["",
          "## Month-by-month naturally closed-trade P&L (USD; NOT equity return)",
          "",
          "Because a trade can remain open over several days or months, "
          "these rows record P&L **only when a trade closes naturally**. "
          "They ignore interim unrealized gains/losses, and completely "
          "exclude end-boundary forced closures. Thus the totals may differ "
          "from the headline backtest account return.",
          "",
          "| Calendar month | 1h normal | 12h normal | 1h higher fee | 12h higher fee |",
          "|---|---:|---:|---:|---:|"]
    for month in MONTHS:
        def monthval(name,fee):
            return rows[name][fee]["month_closes"][month]["natural_closed_net_usd"]
        out.append(
            f"| {month} | {monthval('1h_btc_funding_oi','normal'):+.3f} | "
            f"{monthval('12h_original','normal'):+.3f} | "
            f"{monthval('1h_btc_funding_oi','stress'):+.3f} | "
            f"{monthval('12h_original','stress'):+.3f} |"
        )
    out+=["",
          "## How frequently did closed trades actually make money?",
          "",
          "| Strategy/cost | Days with profitable natural closes | "
          "Days with losing natural closes | Days with no natural close | "
          "Best profitable natural close-day USD | Worst natural close-day USD | "
          "Largest winning natural trade USD |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for name in ("1h_btc_funding_oi","12h_original"):
        for fee in COSTS:
            x=rows[name][fee]
            out.append(f"| {name} {fee} | {x['days_with_positive_closed_net']} | "
                       f"{x['days_with_negative_closed_net']} | "
                       f"{x['days_with_no_natural_trade_close']} | "
                       f"{x['best_natural_closed_profit_day_usd']:+.3f} | "
                       f"{x['worst_natural_closed_profit_day_usd']:+.3f} | "
                       f"{x['largest_natural_winning_trade_usd']:+.3f} |")
    out+=["",
          "## Caveats that change the interpretation",
          "",
          "The 12h strategy can go long intervals without closing a trade, "
          "and one artificial terminal gain can dominate its final reported "
          "profit. An hourly strategy can close more frequently but lose "
          "more often and incur more fees. The candidate was selected using "
          "historical 2026 data, so comparing it on those same months is "
          "NOT confirmation from unseen future observations.",
          "",
          "No rigorous claim of statistically **significant** additional "
          "profit can be made without independent forward trading evidence. "
          "This file measures dollar magnitude and realized-close "
          "consistency, not guaranteed daily income.",
          "",
          "See the full JSON for every day, every month, winning/loss streaks, "
          "forced exits and average closed-trade frequency. The existing "
          "hourly prospective paper account remains independent, with no "
          "historical profits credited.",
          ""]
    return "\n".join(out)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--json",required=True)
    p.add_argument("--markdown",required=True)
    args=p.parse_args()
    doc=create(Path(args.root))
    Path(args.json).write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n")
    Path(args.markdown).write_text(markdown(doc))
    for name in MODELS:
        for fee in COSTS:
            r=doc["models"][name][fee]
            print("SEVEN_MONTH_RESULT",name,fee,"profit",r["net_with_forced_terminal_usd"],
                  "return_pct",r["account_return_with_forced_terminal_pct"],
                  "average_daily",r["average_backtest_net_per_calendar_day_including_forced_usd"],
                  "natural_closes",r["naturally_closed_trades"],
                  "profitable_close_days",r["days_with_positive_closed_net"],
                  "natural_positive_months",sum(x["natural_closed_net_usd"]>0 for x in r["month_closes"].values()),
                  "force_pnl",r["forced_terminal_profit_usd"],
                  "max_dd",r["reported_backtester_max_drawdown_pct"])
    print("MATCHED_SEVEN_MONTH_DIFFERENCE",json.dumps(doc["matched_1h_vs_12h_comparison"],sort_keys=True))


if __name__=="__main__":
    main()
