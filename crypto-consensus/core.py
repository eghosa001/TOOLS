"""Frozen 10-vote research signal model. OHLCV must be completed 12h futures candles.

This is an indicator-based ensemble, not ten independently trained bots.
All rolling calculations use observations no later than the input candle.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SIGNAL_NAMES = (
    "EMA20/50", "MACD", "Supertrend", "Donchian30", "Ichimoku",
    "DMI", "RSI50", "BollingerReversion", "Stochastic", "OBV",
)
STARTUP_CANDLES = 400


def build_indicators(candles: pd.DataFrame) -> pd.DataFrame:
    required = {"open", "high", "low", "close", "volume"}
    if not required.issubset(candles.columns):
        raise ValueError("OHLCV columns missing: " + str(required - set(candles.columns)))
    df = candles.copy().reset_index(drop=True)
    for column in required:
        df[column] = pd.to_numeric(df[column], errors="raise").astype("float64")
    if df[list(required)].isna().any().any():
        raise ValueError("Missing OHLCV: refuse to invent candles")
    c, h, l, v = (df[x] for x in ("close", "high", "low", "volume"))
    ema = lambda x, n: x.ewm(span=n, adjust=False).mean()
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False).mean()
    macd = ema(c, 12) - ema(c, 26)
    votes = [
        np.where(ema(c, 20) > ema(c, 50), 1, -1),
        np.where(macd > ema(macd, 9), 1, -1),
    ]

    # Frozen Supertrend voting implementation from the exploratory simulation.
    high, low, close = h.to_numpy(), l.to_numpy(), c.to_numpy()
    a10 = tr.ewm(alpha=.1, adjust=False).mean().to_numpy()
    upper = (high+low)/2+3*a10
    lower = (high+low)/2-3*a10
    final_upper, final_lower = upper.copy(), lower.copy()
    trend = np.ones(len(c), dtype=np.int8)
    for i in range(1, len(c)):
        if upper[i] >= final_upper[i-1] and close[i-1] <= final_upper[i-1]:
            final_upper[i] = final_upper[i-1]
        if lower[i] <= final_lower[i-1] and close[i-1] >= final_lower[i-1]:
            final_lower[i] = final_lower[i-1]
        if trend[i-1] < 0 and close[i] > final_upper[i-1]:
            trend[i] = 1
        elif trend[i-1] > 0 and close[i] < final_lower[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
    votes.append(trend)

    brk = np.where(c > h.rolling(30).max().shift(1), 1,
                   np.where(c < l.rolling(30).min().shift(1), -1, np.nan))
    votes.append(pd.Series(brk).ffill().fillna(-1).to_numpy())

    conversion = (h.rolling(9).max() + l.rolling(9).min()) / 2
    baseline = (h.rolling(26).max() + l.rolling(26).min()) / 2
    cloud_a = ((conversion+baseline)/2).shift(26)
    cloud_b = ((h.rolling(52).max()+l.rolling(52).min())/2).shift(26)
    top = pd.concat([cloud_a,cloud_b], axis=1).max(axis=1)
    bottom = pd.concat([cloud_a,cloud_b], axis=1).min(axis=1)
    ichi = np.where((c>top)&(conversion>baseline), 1,
                    np.where((c<bottom)&(conversion<baseline), -1, np.nan))
    votes.append(pd.Series(ichi).ffill().fillna(-1).to_numpy())

    up, down = h.diff(), -l.diff()
    plus = pd.Series(np.where((up>down)&(up>0), up, 0)).ewm(alpha=1/14, adjust=False).mean()
    minus = pd.Series(np.where((down>up)&(down>0), down, 0)).ewm(alpha=1/14, adjust=False).mean()
    votes.append(np.where(plus>minus, 1, -1))

    changes = c.diff()
    gain = changes.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-changes.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    rsi = (100-100/(1+gain/loss.replace(0,np.nan))).fillna(50)
    votes.append(np.where(rsi>=50, 1, -1))
    votes.append(np.where(c<c.rolling(20).mean(), 1, -1))

    stochastic_k = (100*(c-l.rolling(14).min()) /
                    (h.rolling(14).max()-l.rolling(14).min()).replace(0,np.nan)).rolling(3).mean()
    votes.append(np.where(stochastic_k>stochastic_k.rolling(3).mean(), 1, -1))
    obv = pd.Series(np.sign(c.diff().fillna(0))*v).cumsum()
    votes.append(np.where(ema(obv,10)>ema(obv,30), 1, -1))

    assert len(votes) == 10
    count = (np.stack(votes) == 1).sum(axis=0)
    df["atr14"] = atr.to_numpy()
    df["buy_votes"] = count.astype("int8")
    df["sell_votes"] = (10-count).astype("int8")
    df["warm"] = np.arange(len(df)) >= STARTUP_CANDLES
    return df


def decision(buy_votes: int, has_position: int = 0) -> int:
    """Return +1 long, -1 short, 0 flat, 2 exit existing side."""
    if has_position == 1:
        return 2 if buy_votes <= 4 else 0
    if has_position == -1:
        return 2 if buy_votes >= 6 else 0
    return 1 if buy_votes >= 8 else -1 if buy_votes <= 2 else 0
