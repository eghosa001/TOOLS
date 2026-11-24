"""One-hour futures quality gates: completed BTC macro regime and genuine Kraken OI/funding.

Standalone past-only features. Nothing is automatically traded, and no existing
production class is modified. At hour t we use only features published strictly
before hour t+1; 4h OI deliberately delayed *an additional full 4 hours*.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quality_candidate_features import parse_official_oi

ONE_HOUR = pd.Timedelta(hours=1)
FOUR_HOURS = pd.Timedelta(hours=4)
TWELVE_HOURS = pd.Timedelta(hours=12)


def _timestamps(df: pd.DataFrame, label: str) -> pd.Series:
    if "date" not in df or len(df) < 100:
        raise ValueError(f"Insufficient dated {label} market data")
    t = pd.to_datetime(df["date"], utc=True)
    if t.isna().any() or not t.is_monotonic_increasing or t.duplicated().any():
        raise ValueError(f"{label}: invalid or repeated timestamps")
    return t.reset_index(drop=True)


def _base(eth: pd.DataFrame) -> pd.DataFrame:
    et = _timestamps(eth, "1h target futures")
    if et.diff().dropna().gt(ONE_HOUR).any():
        raise ValueError("1h research source has missing candles")
    return pd.DataFrame({"known_at": et + ONE_HOUR})


def btc_macro_gate(target: pd.DataFrame, btc_12h: pd.DataFrame) -> pd.DataFrame:
    """Two-day BTC momentum and causal EMA100, as-of actual published 12h closes."""
    key = _base(target)
    bt = _timestamps(btc_12h, "BTC 12h reference")
    if len(bt) < 240 or bt.diff().dropna().gt(TWELVE_HOURS).any():
        raise ValueError("No continuous BTC 12h history and EMA warmup")
    c = pd.to_numeric(btc_12h["close"], errors="raise").reset_index(drop=True)
    if c.isna().any() or c.le(0).any():
        raise ValueError("Invalid BTC market closes")
    trend = c.ewm(span=100, adjust=False).mean()
    long_ok = (c > trend) & (c.pct_change(4) >= .005)
    short_ok = (c < trend) & (c.pct_change(4) <= -.005)
    shock = c.pct_change().abs().ge(.08).rolling(4, min_periods=1).max().fillna(0).astype(bool)
    source = pd.DataFrame({
        "published_at": bt + TWELVE_HOURS,
        "btc_long": long_ok.to_numpy(dtype=bool),
        "btc_short": short_ok.to_numpy(dtype=bool),
        "btc_shock": shock.to_numpy(dtype=bool),
    })
    aligned = pd.merge_asof(
        key, source, left_on="known_at", right_on="published_at",
        direction="backward", allow_exact_matches=False,
    )
    good = (aligned["published_at"].notna() &
            ((aligned["known_at"] - aligned["published_at"]) <= pd.Timedelta(hours=24)))
    return pd.DataFrame({
        "allow_long": (good & aligned["btc_long"].fillna(False)
                       & ~aligned["btc_shock"].fillna(True)).to_numpy(dtype=bool),
        "allow_short": (good & aligned["btc_short"].fillna(False)
                        & ~aligned["btc_shock"].fillna(True)).to_numpy(dtype=bool),
    }, index=target.index)


def funding_oi_gate(target: pd.DataFrame, funding_hourly: pd.DataFrame,
                    official_oi_doc: dict) -> pd.DataFrame:
    """No forward-fills beyond strict freshness, and no invented OI observations.

    Funding from the hourly chart is assumed safely known TWO hours after
    its timestamp. OI at 4h open-time is assumed safely known EIGHT hours
    later. Require both actual feeds as of the just completed target candle.
    """
    key = _base(target)
    fts = _timestamps(funding_hourly, "actual hourly Kraken funding")
    if len(fts) < 400 or fts.diff().dropna().gt(pd.Timedelta(hours=3)).any():
        raise ValueError("Unverified or gapped hourly funding")
    if "funding_rate" not in funding_hourly:
        raise ValueError("No actual historical funding rate")
    funding = pd.to_numeric(funding_hourly["funding_rate"], errors="raise").reset_index(drop=True)
    if not np.isfinite(funding).all():
        raise ValueError("Missing actual historical funding values")
    avg = funding.rolling(12, min_periods=12).mean()
    reference = avg.rolling(240, min_periods=80)
    z = (avg - reference.mean()) / reference.std().replace(0,np.nan)
    funding_table = pd.DataFrame({
        "published_at": fts + pd.Timedelta(hours=2),
        "z": z.to_numpy(dtype=float),
    })
    oi = parse_official_oi(official_oi_doc)
    oi = oi[["known_at", "oi_growth_7d"]].copy()
    # Add four hours of publication tolerance beyond chart completion.
    oi["published_at"] = oi["known_at"] + FOUR_HOURS
    oi = oi[["published_at", "oi_growth_7d"]]
    fa = pd.merge_asof(key, funding_table, left_on="known_at",
                       right_on="published_at", direction="backward",
                       allow_exact_matches=False)
    oa = pd.merge_asof(key, oi, left_on="known_at",
                       right_on="published_at", direction="backward",
                       allow_exact_matches=False)
    complete = (
        fa["published_at"].notna() & fa["z"].notna() &
        oa["published_at"].notna() & oa["oi_growth_7d"].notna() &
        ((key["known_at"] - fa["published_at"]) <= pd.Timedelta(hours=4)) &
        ((key["known_at"] - oa["published_at"]) <= pd.Timedelta(hours=12))
    )
    crowded_long = (fa["z"] > 1.5) & (oa["oi_growth_7d"] > .05)
    crowded_short = (fa["z"] < -1.5) & (oa["oi_growth_7d"] > .05)
    return pd.DataFrame({
        "allow_long": (complete & ~crowded_long).to_numpy(dtype=bool),
        "allow_short": (complete & ~crowded_short).to_numpy(dtype=bool),
        "known_observations": complete.to_numpy(dtype=bool),
    }, index=target.index)


def combine_and(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    if len(a) != len(b) or not a.index.equals(b.index):
        raise ValueError("Misaligned one-hour evidence")
    return pd.DataFrame({
        "allow_long": a["allow_long"].astype(bool) & b["allow_long"].astype(bool),
        "allow_short": a["allow_short"].astype(bool) & b["allow_short"].astype(bool),
    }, index=a.index)
