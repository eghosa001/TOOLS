"""Reproducible, inspectable report from REAL forward paper observations.

Never combines backtest returns with forward simulated balances. Missing
observations cannot be replaced with synthetic profitability.
"""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path

def summarise(state):
    hist=state.get("equity_history",[])
    equity=float(state.get("equity_usd",state["balance"]))
    start=150.0
    peak=start
    maximum=0.0
    for r in hist:
        value=float(r["equity_usd"])
        peak=max(peak,value)
        maximum=max(maximum,(peak-value)/peak)
    entries=len(state.get("trades",[]))
    realized=sum(float(t.get("net_usd",0)) for t in state.get("trades",[]))
    last=state.get("last_observation","unknown")
    try:
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()
    except (ValueError,TypeError):
        age=None
    return {"mode":"keyless_discrete_paper_observer_not_real_trading",
            "starting_usd":start,"equity_usd":equity,
            "simulated_return_pct":round((equity/start-1)*100,4),
            "realized_trade_profit_usd":round(realized,6),
            "closed_trades":entries,
            "observations":int(state.get("observations",0)),
            "history_points":len(hist),
            "max_observed_drawdown_pct":round(maximum*100,4),
            "funding_estimate_usd":round(float(state.get("funding_usd",0)),6),
            "fees_estimate_usd":round(float(state.get("fees_usd",0)),6),
            "cash_balance_usd":round(float(state["balance"]),6),
            "open_unrealized_usd":round(equity-float(state["balance"]),6),
            "blocked_entries":int(state.get("blocked_entries",0)),
            "crash_blocked_entries":int(state.get("crash_blocked_entries",0)),
            "daily_paused":bool(state.get("daily_pause_until_ms",0)>state.get("last_checked_ms",0)),
            "weekly_paused":bool(state.get("weekly_pause_until_ms",0)>state.get("last_checked_ms",0)),
            "permanent_risk_lock":bool(state.get("permanent_risk_lock",False)),
            "risk_events":state.get("risk_events",[])[-12:],
            "open_position":state.get("position"),
            "last_observation_utc":last,
            "feed_age_seconds":round(age) if age is not None else None,
            "feed_stale":age is None or age>7200,
            "exchange_stop_order_verified":False}

def markdown(a):
    def money(x):return "$"+format(float(x),".2f")
    return ("# Ethereum consensus — actual forward PAPER observations\n\n"
        "This report contains simulated forward observations, **not real fills** and "
        "not the historical backtest. It must not be used as proof of future returns.\n\n"
        "| Metric | Observed value |\n|---|---:|\n"
        "| Starting simulated capital | "+money(a["starting_usd"])+" |\n"
        "| Last simulated account equity | "+money(a["equity_usd"])+" |\n"
        "| Forward paper return | "+format(a["simulated_return_pct"],"+.3f")+"% |\n"
        "| Closed simulated trades | "+str(a["closed_trades"])+" |\n"
        "| Forward observations | "+str(a["observations"])+" |\n"
        "| Measured equity-history drawdown | "+format(a["max_observed_drawdown_pct"],".3f")+"% |\n"
        "| Funding estimate (included in simulated equity) | "+money(a["funding_estimate_usd"])+" |\n"
        "| Trading fees (already deducted from equity) | "+money(a["fees_estimate_usd"])+" |\n"
        "| Open-position unrealized P&L | "+money(a["open_unrealized_usd"])+" |\n"
        "| Daily/weekly loss pause | "+str(a["daily_paused"])+"/"+str(a["weekly_paused"])+" |\n"
        "| Permanent manual-reset risk lock | "+str(a["permanent_risk_lock"])+" |\n"
        "| Historical observations stored | "+str(a["history_points"])+" |\n"
        "| Market feed stale | "+str(a["feed_stale"])+" |\n\n"
        "**Most recent observation:** "+str(a["last_observation_utc"])+" UTC\n\n"
        "**Exchange-held stops verified:** No. This is a keyless observer; "
        "even the standalone Freqtrade dry-run would simulate stops. "
        "Missing snapshots, slippage, mark prices and gaps limit the accuracy "
        "of this model.\n")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",required=True)
    p.add_argument("--markdown",required=True)
    p.add_argument("--json",required=True)
    opts=p.parse_args()
    s=json.loads(Path(opts.state).read_text())
    result=summarise(s)
    Path(opts.markdown).write_text(markdown(result))
    Path(opts.json).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
