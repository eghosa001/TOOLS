"""Causal experimental ETH filters. No order routing or training labels from the future.

These features are candidate research gates over the fixed 8-of-10 baseline.
Do not promote them to active orders without independent validation.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BAR_HOURS = 12
EXTERNAL_OI_HOURS = 4


def _dates(df: pd.DataFrame, label: str) -> pd.Series:
    if "date" not in df or df.empty:
        raise ValueError(f"Missing {label} date series")
    t = pd.to_datetime(df["date"], utc=True)
    if t.isna().any() or t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError(f"Invalid {label} timestamp order")
    return t


def btc_regime(eth: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    """BTC completed-bar confirmation, conservatively delayed by one BTC bar."""
    e = _dates(eth, "ETH")
    b = _dates(btc, "BTC")
    if len(b) < 180:
        raise ValueError("Missing BTC Futures research warmup")
    c = pd.to_numeric(btc["close"], errors="raise")
    if c.isna().any() or c.le(0).any():
        raise ValueError("Invalid BTC price")
    ema = c.ewm(span=100, adjust=False).mean()
    up = ((c > ema) & (c.pct_change(4) > .005)).shift(1).fillna(False)
    dn = ((c < ema) & (c.pct_change(4) < -.005)).shift(1).fillna(False)
    shock = (c.pct_change().abs() >= .08).rolling(4).max().fillna(0)
    info = pd.DataFrame({"key": b, "btc_known_at": b, "btc_up": up.astype(bool),
                         "btc_down": dn.astype(bool),
                         "btc_shock": shock.shift(1).fillna(0).astype(bool)})
    merged = pd.merge_asof(pd.DataFrame({"key": e}), info, on="key", direction="backward")
    stale = (e - merged["btc_known_at"]).dt.total_seconds().gt(14 * 3600)
    # merge_asof uses same key; independently align published informative time.
    # Last BTC candle used by features is always one earlier (shift(1)).
    merged["btc_up"] = merged["btc_up"].fillna(False) & ~stale
    merged["btc_down"] = merged["btc_down"].fillna(False) & ~stale
    merged["btc_shock"] = merged["btc_shock"].fillna(True)
    return merged[["btc_up", "btc_down", "btc_shock"]].set_axis(eth.index)


def parse_official_oi(doc: dict) -> pd.DataFrame:
    """Kraken chart analytics 4h OHLC OI; never use close before period ends."""
    if doc.get("errors") or not isinstance(doc.get("result"), dict):
        raise ValueError("Invalid official Kraken OI payload")
    r = doc["result"]
    stamps = r.get("timestamp", [])
    bars = r.get("data", [])
    if len(stamps) != len(bars) or len(stamps) < 100:
        raise ValueError("Insufficient real 4h OI history")
    t = pd.to_datetime(stamps, unit="s", utc=True)
    if t.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("Unordered official OI observations")
    if (t.to_series().diff().dropna() != pd.Timedelta(hours=4)).any():
        raise ValueError("Gapped official 4h open interest")
    vals = np.array([float(row[3]) for row in bars], dtype=float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise ValueError("Invalid official 4h open-interest values")
    # 7d change uses 42 preceding four-hour periods and is causal.
    table = pd.DataFrame({"known_at": t + pd.Timedelta(hours=4),
                          "oi_known_at": t + pd.Timedelta(hours=4),
                          "oi_growth_7d": pd.Series(vals).pct_change(42).to_numpy()})
    return table


def derivatives_crowding(eth: pd.DataFrame, funding: pd.DataFrame,
                         oi_document: dict) -> pd.DataFrame:
    """Block crowded futures entries only when both verified feeds agree."""
    ed = _dates(eth, "ETH")
    fd = _dates(funding, "Kraken funding")
    if len(fd) < 400 or "funding_rate" not in funding:
        raise ValueError("Missing actual hourly funding-rate history")
    raw = pd.to_numeric(funding["funding_rate"], errors="raise").astype(float)
    if not np.isfinite(raw).all():
        raise ValueError("Invalid funding observations")
    trend = raw.rolling(12, min_periods=12).mean()
    prior_mean = trend.rolling(240, min_periods=80).mean()
    prior_std = trend.rolling(240, min_periods=80).std()
    zscore = (trend - prior_mean) / prior_std.replace(0, np.nan)
    # Published completed hourly funding event; allow a full hour for disclosure.
    ft = pd.DataFrame({"known_at": fd + pd.Timedelta(hours=1),
                       "funding_known_at": fd + pd.Timedelta(hours=1),
                       "funding_z": zscore.to_numpy()})
    oi = parse_official_oi(oi_document)
    key = pd.DataFrame({"known_at": ed + pd.Timedelta(hours=12)})
    f = pd.merge_asof(key, ft, on="known_at", direction="backward",
                      allow_exact_matches=False)
    o = pd.merge_asof(key, oi, on="known_at", direction="backward",
                      allow_exact_matches=False)
    # Do not infer any future data; use most recent fully published values.
    growth = o["oi_growth_7d"]
    z = f["funding_z"]
    # The conservative veto requires BOTH extreme relative funding AND
    # actual increasing open interest (riskier crowded directional leverage).
    # A missing observation refuses the entry, never fills a fake zero.
    complete = (z.notna() & growth.notna() &
                ((key["known_at"] - f["funding_known_at"]).dt.total_seconds() <= 24 * 3600) &
                ((key["known_at"] - o["oi_known_at"]).dt.total_seconds() <= 12 * 3600))
    allow_long = complete & ~((z > 1.5) & (growth > .05))
    allow_short = complete & ~((z < -1.5) & (growth > .05))
    return pd.DataFrame({"deriv_long": allow_long.to_numpy(dtype=bool),
                         "deriv_short": allow_short.to_numpy(dtype=bool),
                         "deriv_oi_growth_7d": growth.to_numpy(dtype=float),
                         "deriv_funding_z": z.to_numpy(dtype=float)}, index=eth.index)


def volatility_breakout(eth: pd.DataFrame) -> pd.DataFrame:
    """Volatility expansion from the PRIOR 3-day range (six 12h bars)."""
    h, l, c = (pd.to_numeric(eth[x], errors="raise") for x in
               ("high", "low", "close"))
    tr = pd.concat([h-l, (h-c.shift(1)).abs(),
                    (l-c.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    vol = atr / c
    high = h.shift(1).rolling(6, min_periods=6).max()
    low = l.shift(1).rolling(6, min_periods=6).min()
    acceptable = vol.between(.008, .065, inclusive="both")
    return pd.DataFrame({"breakout_long": ((c > high) & acceptable).fillna(False),
                         "breakout_short": ((c < low) & acceptable).fillna(False)},
                        index=eth.index)


def ml_features(eth: pd.DataFrame) -> pd.DataFrame:
    """Price/volume regime features computed only with each bar and its past."""
    c, h, l, v = (pd.to_numeric(eth[x], errors="raise") for x in
                  ("close", "high", "low", "volume"))
    returns = c.pct_change()
    volume_scale = v / (v.rolling(40).mean() + 1e-12) - 1
    features = pd.DataFrame({
        "return1": returns,
        "return3": c.pct_change(3),
        "return6": c.pct_change(6),
        "return14": c.pct_change(14),
        "range": (h - l) / c,
        "volatility": returns.rolling(14).std(),
        "relative_volume": volume_scale,
        "candle_body": (c - pd.to_numeric(eth["open"], errors="raise")) / c,
    })
    return features.replace([np.inf, -np.inf], np.nan)


def online_ridge_forecast(eth: pd.DataFrame, window: int = 240,
                          retrain_every: int = 12) -> pd.Series:
    """Rolling time-series ridge; each prediction excludes future labels.

    At index i, train j<=i-2 on target return close[j+1]/close[j]-1.
    Refit only every 12 candles and keep model+scaler fixed between fits.
    There is no shuffling, no global normalization, and no future target.
    """
    if window < 80 or retrain_every < 1:
        raise ValueError("Invalid time-ordered model settings")
    feat = ml_features(eth).to_numpy(dtype=float)
    close = pd.to_numeric(eth["close"], errors="raise").to_numpy(dtype=float)
    if len(close) < 300 or not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError("Insufficient valid historical ML candles")
    target = np.empty(len(close))
    target[:] = np.nan
    target[:-1] = close[1:] / close[:-1] - 1
    output = np.full(len(close), np.nan)
    mean = scale = weights = None
    for i in range(max(window + 40, 320), len(close)):
        if weights is None or i % retrain_every == 0:
            # Excludes i-1 label even though it would be available at candle i;
            # use a one-candle additional embargo for auditability.
            stop = i - 1
            start = max(40, stop - window)
            train_x = feat[start:stop]
            train_y = target[start:stop]
            valid = np.isfinite(train_x).all(axis=1) & np.isfinite(train_y)
            if valid.sum() < int(window * .8):
                continue
            x, y = train_x[valid], train_y[valid]
            mean = x.mean(axis=0)
            scale = x.std(axis=0)
            scale = np.where(scale < 1e-9, 1.0, scale)
            z = (x - mean) / scale
            design = np.column_stack([np.ones(len(z)), z])
            ridge = np.diag([0.0] + [25.0] * z.shape[1])
            weights = np.linalg.solve(design.T @ design + ridge,
                                      design.T @ y)
        if weights is not None and np.isfinite(feat[i]).all():
            row = np.r_[1., (feat[i] - mean) / scale]
            output[i] = float(row @ weights)
    return pd.Series(output, index=eth.index, name="ml_next_return")


def ml_direction(eth: pd.DataFrame) -> pd.DataFrame:
    pred = online_ridge_forecast(eth)
    # Small price changes are swamped by costs. This is a fixed preregistered
    # magnitude threshold, not a fitted classification boundary.
    return pd.DataFrame({
        "ml_long": (pred > .001).fillna(False),
        "ml_short": (pred < -.001).fillna(False),
        "ml_pred": pred,
    }, index=eth.index)
