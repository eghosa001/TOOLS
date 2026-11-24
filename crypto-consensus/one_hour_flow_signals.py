"""Independent causal 1h directional confirmation for crypto consensus research.

These signals are not extra mandatory votes in the existing ensemble.
They support optional additional entries and use only completed price/volume.
Indicators intentionally originate from different aspects: rolling VWAP,
money flow, ATR-normalized momentum and volume participation.
No model uses future candles, unseen quotes or historical market impact.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pandas import DataFrame

from one_hour_quality_features import _base, _timestamps, TWELVE_HOURS


def flow_features(frame:DataFrame)->DataFrame:
    out=frame.copy()
    if len(out)<400:
        raise ValueError("1h flow research needs 400+ genuine candles")
    columns=("open","high","low","close","volume","atr14")
    if any(c not in out for c in columns):
        raise ValueError("Missing 1h flow source")
    for name in columns:
        out[name]=pd.to_numeric(out[name],errors="raise")
    if out[list(columns)].isna().any().any():
        raise ValueError("Missing actual price/volume in 1h research")
    h,l,c,v,a=(out[k].astype(float) for k in ("high","low","close","volume","atr14"))
    if (c<=0).any() or (h<l).any() or (v<0).any() or (a<=0).any():
        raise ValueError("Invalid OHLCV/ATR research observations")
    ts=(h+l+c)/3
    v_total=v.rolling(24,min_periods=24).sum().replace(0,np.nan)
    vwap=(ts*v).rolling(24,min_periods=24).sum()/v_total
    money_factor=(2*c-h-l)/(h-l).replace(0,np.nan)
    mf=(money_factor.fillna(0)*v).rolling(20,min_periods=20).sum()/v.rolling(
        20,min_periods=20).sum().replace(0,np.nan)
    momentum=(c-c.shift(6))/a
    activity=v/v.shift(1).rolling(24,min_periods=24).median().replace(0,np.nan)
    long_score=(
        (c>vwap).astype(int)+(mf>.04).astype(int)+
        (momentum>.65).astype(int)+(activity>1.10).astype(int)
    )
    short_score=(
        (c<vwap).astype(int)+(mf<-.04).astype(int)+
        (momentum<-.65).astype(int)+(activity>1.10).astype(int)
    )
    # Only previous complete candles define breakout channel.
    past_high=h.shift(1).rolling(20,min_periods=20).max()
    past_low=l.shift(1).rolling(20,min_periods=20).min()
    break_long=(c>past_high)&(activity>1.25)&(mf>.04)&(momentum>.65)
    break_short=(c<past_low)&(activity>1.25)&(mf<-.04)&(momentum<-.65)
    good=(v_total.notna()&vwap.notna()&mf.notna()&
          momentum.notna()&activity.notna()&(a/c<.06))
    out["flow_long_score"]=long_score.where(good,0).astype("int8")
    out["flow_short_score"]=short_score.where(good,0).astype("int8")
    out["flow_breakout_long"]=(good&break_long).to_numpy(dtype=bool)
    out["flow_breakout_short"]=(good&break_short).to_numpy(dtype=bool)
    out["flow_data_ready"]=good.to_numpy(dtype=bool)
    return out


def soft_btc_regime(target:DataFrame,btc_12h:DataFrame)->DataFrame:
    """Less restrictive BTC macro trend: EMA100 direction, no momentum floor.

    12h source publication strictly AFTER candle closes, no forward
    publication/guessing. 48h strong shock veto and 24h freshness limit.
    """
    key=_base(target)
    bt=_timestamps(btc_12h,"genuine 12h BTC future")
    if len(bt)<240 or bt.diff().dropna().gt(TWELVE_HOURS).any():
        raise ValueError("Gapped/inadequate BTC macro history")
    c=pd.to_numeric(btc_12h["close"],errors="raise").reset_index(drop=True)
    if c.isna().any() or c.le(0).any():
        raise ValueError("Invalid BTC macro price")
    trend=c.ewm(span=100,adjust=False).mean()
    shock=(c.pct_change().abs().ge(.08).rolling(4,min_periods=1)
           .max().fillna(0).astype(bool))
    source=pd.DataFrame({
        "published_at":bt+TWELVE_HOURS,
        "long":(c>trend).to_numpy(dtype=bool),
        "short":(c<trend).to_numpy(dtype=bool),
        "shock":shock.to_numpy(dtype=bool),
    })
    m=pd.merge_asof(key,source,left_on="known_at",
                    right_on="published_at",direction="backward",
                    allow_exact_matches=False)
    fresh=(m["published_at"].notna()&
           (key["known_at"]-m["published_at"]<=pd.Timedelta(hours=24)))
    return pd.DataFrame({
        "allow_long":(fresh&m["long"].fillna(False)&
                      ~m["shock"].fillna(True)).to_numpy(dtype=bool),
        "allow_short":(fresh&m["short"].fillna(False)&
                       ~m["shock"].fillna(True)).to_numpy(dtype=bool),
    },index=target.index)


def entry_masks(frame:DataFrame,model:str,threshold:int):
    """OR-of-validated-entry-paths; new signals are not fictional bot votes."""
    if threshold not in (6,7,8):
        raise ValueError("Research thresholds limited to prespecified 6/7/8")
    if model not in ("vote","flow","hybrid","break_hybrid"):
        raise ValueError("Unregistered entry hypothesis")
    b=pd.to_numeric(frame["buy_votes"],errors="raise")
    if b.isna().any() or not b.between(0,10).all():
        raise ValueError("Unknown consensus votes")
    direct_l=b.ge(threshold)
    direct_s=b.le(10-threshold)
    if model=="vote":
        return direct_l,direct_s
    if not {"flow_long_score","flow_short_score",
            "flow_breakout_long","flow_breakout_short","flow_data_ready"}.issubset(frame):
        raise ValueError("Independent flow features missing")
    ready=frame["flow_data_ready"].fillna(False).astype(bool)
    flow_l=ready&frame["flow_long_score"].ge(3)
    flow_s=ready&frame["flow_short_score"].ge(3)
    if model=="flow":
        return direct_l&flow_l,direct_s&flow_s
    if model=="hybrid":
        return (direct_l | (b.ge(threshold-1)&flow_l)),(
            direct_s | (b.le(11-threshold)&flow_s))
    return (direct_l | (b.ge(threshold-2)&ready&
                        frame["flow_breakout_long"].fillna(False).astype(bool))),(
            direct_s | (b.le(12-threshold)&ready&
                        frame["flow_breakout_short"].fillna(False).astype(bool)))
