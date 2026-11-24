"""Reproducible, non-optimized historical Solana memecoin screening.
Source: MIT data, github.com/ian05012/solana-memecoin-dataset
IMPORTANT: dataset excludes coins before discovery and is NOT an unbiased launch universe.
No live orders, broker, credentials, or lookahead entry signals.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
DATA=HERE / "research_data"
SOURCE_SHA="7070d00e1e4492f8604d988549d91785cc5f43f7"
COSTS={"base":0.0035,"stress":0.015}  # hypothetical PER-SIDE DEX fee + slippage
STAKE=15.0 # 10% of each independent $150 modeled wallet; no repeated compounding
MIN_COVERED=20

def datetime_utc(series):
    """Convert second/ms/us epoch or ISO dates without mixing epoch scales."""
    if pd.api.types.is_numeric_dtype(series):
        nums=pd.to_numeric(series,errors="coerce")
        med=nums.dropna().abs().median()
        unit="ns" if med>1e17 else "us" if med>1e14 else "ms" if med>1e11 else "s"
        return pd.to_datetime(nums,unit=unit,utc=True,errors="coerce")
    return pd.to_datetime(series,utc=True,errors="coerce",format="mixed")

def truth(x):
    return str(x).strip().lower() in ("true","1","1.0","yes")

def eligible(row,mode):
    try:
        liq=float(row["liquidity_usd"])
        vol=float(row["volume_h24"])
        top=float(row["top10_holder_pct"])
        momentum=float(row["price_change_1h"])
        risk=float(row["rug_probability"])
    except (ValueError,TypeError,KeyError):
        return False
    if not all(np.isfinite(x) for x in (liq,vol,top,momentum,risk)):
        return False
    # normalized fraction vs percentage per data check; reject impossible units
    if top>1: top/=100
    if risk>1: risk/=100
    base=truth(row.get("mint_disabled")) and truth(row.get("freeze_disabled"))
    if mode=="strict":
        return base and liq>=50000 and vol>=100000 and top<=.35 and momentum>=.02 and risk<=.2
    if mode=="liquid":
        return base and liq>=30000 and vol>=50000 and top<=.5 and momentum>=.01 and risk<=.4
    raise ValueError("Unexpected strategy")

def research(tokens,ohlcv):
    needed={"token_address","captured_at","liquidity_usd","volume_h24","top10_holder_pct",
            "price_change_1h","rug_probability","mint_disabled","freeze_disabled"}
    if not needed.issubset(tokens.columns):
        raise ValueError("Missing historical snapshot features: "+str(needed-set(tokens.columns)))
    if not {"token_address","ts","open","close"}.issubset(ohlcv.columns):
        raise ValueError("Incomplete historical OHLCV columns")
    a=tokens.copy()
    a["captured_at"]=datetime_utc(a["captured_at"])
    a=a[a["captured_at"].notna()].sort_values(["captured_at","token_address"])
    first=a.drop_duplicates("token_address",keep="first")
    # no oracle return label, max-return labels or other post-capture column used.
    f=ohlcv[["token_address","ts","open","close"]].copy()
    f["ts"]=datetime_utc(f["ts"])
    f["open"]=pd.to_numeric(f["open"],errors="coerce")
    f["close"]=pd.to_numeric(f["close"],errors="coerce")
    f=f[f.ts.notna() & (f.open>0) & (f.close>0)].sort_values(["token_address","ts"])
    grouped={key:g.reset_index(drop=True) for key,g in f.groupby("token_address",sort=False)}
    out={"source_git_sha":SOURCE_SHA,"readme_survivorship_caveat":True,
         "snapshot_rows":len(tokens),"unique_first_detected_tokens":len(first),
         "ohlcv_rows":len(ohlcv),"signals_are_snapshot_time_only":True,
         "modes":{}}
    for mode in ("strict","liquid"):
        selected=first[first.apply(lambda row:eligible(row,mode),axis=1)]
        trade_returns=[]
        reasons={"missing_token_candles":0,"no_next_open":0,"no_contiguous_hour":0}
        for row in selected.itertuples(index=False):
            coin=row.token_address
            candles=grouped.get(coin)
            if candles is None or len(candles)<5:
                reasons["missing_token_candles"]+=1
                continue
            capture=row.captured_at
            # Exclude bars that began before capture; next bar open must be
            # no more than 30 mins after detection, no backfilled fills.
            entries=candles[(candles.ts>capture)&(candles.ts<=capture+pd.Timedelta(minutes=30))]
            if entries.empty:
                reasons["no_next_open"]+=1
                continue
            entry_idx=entries.index[0]
            if entry_idx+4>=len(candles):
                reasons["no_contiguous_hour"]+=1
                continue
            path=candles.iloc[entry_idx:entry_idx+5]
            if not all((path.ts.diff().dropna()==pd.Timedelta(minutes=15))):
                reasons["no_contiguous_hour"]+=1
                continue
            price_in=float(path.open.iloc[0])
            price_out=float(path.close.iloc[-1])
            if not (np.isfinite(price_in) and np.isfinite(price_out) and price_in>0 and price_out>0):
                reasons["no_contiguous_hour"]+=1
                continue
            trade_returns.append(price_out/price_in-1)
        arr=np.asarray(trade_returns,dtype=float)
        costs={}
        for name,rate in COSTS.items():
            net=(1-rate)*(1+arr)*(1-rate)-1
            costs[name]={
                "measured_trades":int(len(net)),
                "mean_trade_return_pct":round(float(net.mean()*100),4) if len(net) else None,
                "median_trade_return_pct":round(float(np.median(net)*100),4) if len(net) else None,
                "win_rate_pct":round(float((net>0).mean()*100),4) if len(net) else None,
                "independent_stakes_sum_net_usd":round(float(np.sum(STAKE*net)),4) if len(net) else None,
                "profitability_claim_allowed":False,
            }
        out["modes"][mode]={
            "predeclared_entry_count":len(selected),
            "price_path_coverage_count":len(arr),
            "price_path_coverage_pct":round(len(arr)/len(selected)*100,2) if len(selected) else 0,
            "missing_reasons":reasons,
            "costs":costs,
            "missing_paths_not_assumed_to_be_profitable":True,
            "bias":"Selected already-observed tokens; misses pre-detection rug pulls and tokens with missing price data; incomplete paths prevent tradable profit inference.",
        }
    return out

def main():
    tokens=pd.read_parquet(DATA/"tokens.parquet")
    candles=pd.read_parquet(DATA/"ohlcv.parquet")
    report=research(tokens,candles)
    p=HERE/"onchain_historical_screen.json"
    p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,sort_keys=True))
    assert report["unique_first_detected_tokens"]>1000, "SOURCE TOO SMALL"
    assert report["ohlcv_rows"]>10000, "MISSING_PRICE_CANDLES"

if __name__=="__main__":
    main()
