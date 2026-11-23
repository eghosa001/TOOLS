"""Time-consistent intraday research safety helpers.

12h strategy has 12h+3d shock windows and seven-day loss lock. At shorter
bars these must be converted to elapsed time, NOT simply 1/6 candles.
Research-only. Never routes exchange orders or adjusts actual paper account.
"""
from __future__ import annotations

import math
import pandas as pd

SUPPORTED_MINUTES = {"12h": 720, "1h": 60, "15m": 15, "5m": 5}
THREE_DAYS_MIN = 3 * 24 * 60
TWELVE_H_MIN = 12 * 60
TWO_DAYS_MIN = 2 * 24 * 60
WEEK_MIN = 7 * 24 * 60


def startup_candles(timeframe: str) -> int:
    minutes = SUPPORTED_MINUTES[timeframe]
    # Keep 3-day shock history and 2-day block window in view.
    return max(400, (THREE_DAYS_MIN + TWO_DAYS_MIN) // minutes + 5)


def time_consistent_crash_mask(frame: pd.DataFrame, timeframe: str) -> pd.Series:
    """12h price shock >8%, three day >15%; block entries for 48h."""
    minutes = SUPPORTED_MINUTES[timeframe]
    c = pd.to_numeric(frame["close"], errors="raise")
    if c.isna().any() or c.le(0).any():
        raise ValueError("Invalid 12h-equivalent price shock input")
    shock = (
        (c / c.shift(TWELVE_H_MIN // minutes) - 1).abs().ge(.08)
        | (c / c.shift(THREE_DAYS_MIN // minutes) - 1).abs().ge(.15)
    )
    blocked = shock.rolling(TWO_DAYS_MIN // minutes, min_periods=1).max()
    return blocked.fillna(0).astype(bool)


def protection_settings(mode: str) -> list[dict]:
    """Never accidentally shorten a 7-day cooldown by switching timeframes.

    strict: 7-day stoploss guard, 36h after any close.
    active: exploratory 24h after loss, 3h cooldown, with unchanged
            7-day 4% backtester drawdown guard.
    """
    if mode not in ("strict", "active"):
        raise ValueError("Unknown research-only cooldown")
    initial_cooldown = 36 * 60 if mode == "strict" else 3 * 60
    loss_cooldown = WEEK_MIN if mode == "strict" else 24 * 60
    return [
        {"method": "CooldownPeriod", "stop_duration": initial_cooldown},
        {"method": "StoplossGuard", "lookback_period": WEEK_MIN,
         "trade_limit": 1, "stop_duration": loss_cooldown,
         "only_per_pair": False},
        {"method": "MaxDrawdown", "lookback_period": WEEK_MIN,
         "trade_limit": 2, "stop_duration": WEEK_MIN,
         "max_allowed_drawdown": .04},
        {"method": "LowProfitPairs", "lookback_period": TWELVE_H_MIN,
         "trade_limit": 1, "stop_duration": loss_cooldown,
         "required_profit": 0.0, "only_per_pair": True},
    ]


def agreement_gate(votes: pd.Series, required: int) -> tuple[pd.Series, pd.Series]:
    if required not in (8, 9):
        raise ValueError("Only preregistered 8/10 or 9/10 gates")
    votes = pd.to_numeric(votes, errors="raise")
    if votes.isna().any() or not votes.between(0, 10).all():
        raise ValueError("Unexpected consensus tally")
    return votes.ge(required), votes.le(10 - required)
