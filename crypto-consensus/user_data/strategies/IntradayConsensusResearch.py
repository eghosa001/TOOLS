"""Intraday research ONLY: 1h, 15m, 5m; 8/10 and 9/10 votes.

Each historical class inherits existing stake sizing, one-position limit,
stoploss and 1x nominal leverage. The two protection profiles are explicitly
different studies. No real orders, no change to current 12h production class.
"""
from __future__ import annotations

import math

import pandas as pd
from pandas import DataFrame

from GuardedConsensusETH import GuardedConsensusETH


HOURS = {"1h": 1, "15m": 1/4, "5m": 1/12}
STRICT_COOLDOWN_HOURS = 36
STRICT_LOSS_PAUSE_HOURS = 168
ACTIVE_COOLDOWN_HOURS = None  # one completed candle; not zero wait
ACTIVE_LOSS_PAUSE_HOURS = 48
CRASH_SHOCK_12H = .08
CRASH_SHOCK_72H = .15
CRASH_BLOCK_HOURS = 48


def bars(hours: float, timeframe: str) -> int:
    if timeframe not in HOURS:
        raise ValueError("Unrecognized intraday research timeframe")
    return max(1, math.ceil(hours / HOURS[timeframe]))


def fast_crash_mask(candles: DataFrame, timeframe: str) -> pd.Series:
    """Keep original 8%/12h, 15%/72h and 48h crisis-entry suspension."""
    close = pd.to_numeric(candles["close"], errors="raise").astype(float)
    if not (close > 0).all():
        raise ValueError("Market feed contains invalid prices")
    shock = (
        close.pct_change(bars(12, timeframe)).abs().ge(CRASH_SHOCK_12H)
        | close.pct_change(bars(72, timeframe)).abs().ge(CRASH_SHOCK_72H)
    )
    return shock.rolling(bars(CRASH_BLOCK_HOURS, timeframe), min_periods=1).max().fillna(0).astype(bool)


class _IntradayResearch(GuardedConsensusETH):
    """Override the candle clock, not the original risk/stake model."""
    vote_threshold = 8
    protection_mode = "strict"

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        result = super().populate_indicators(dataframe, metadata)
        # Original crash-mask is explicitly 12h-specific; preserve its REAL
        # wall-clock definition when using faster candles.
        result["crash_block"] = fast_crash_mask(result, self.timeframe).to_numpy()
        return result

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_entry_trend(dataframe, metadata)
        n = int(self.vote_threshold)
        if n not in (8, 9):
            raise ValueError("Only predeclared 8/10 vs 9/10 are eligible")
        # super() did the original 8-of-10. The 9-of-10 candidate is
        # strictly a subset; never loosens the existing entry rule.
        if n == 9:
            frame.loc[frame["buy_votes"] < 9, "enter_long"] = 0
            frame.loc[frame["buy_votes"] > 1, "enter_short"] = 0
        return frame

    @property
    def protections(self):
        tf = self.timeframe
        if tf not in HOURS:
            raise ValueError("Unknown timeframe")
        lookback = bars(7 * 24, tf)
        if self.protection_mode == "strict":
            pause = bars(STRICT_LOSS_PAUSE_HOURS, tf)
            cooldown = bars(STRICT_COOLDOWN_HOURS, tf)
            low_profit_lookback = bars(12, tf)
        elif self.protection_mode == "active":
            # Research comparison only, weaker than strict profile.
            pause = bars(ACTIVE_LOSS_PAUSE_HOURS, tf)
            cooldown = 1
            low_profit_lookback = bars(12, tf)
        else:
            raise ValueError("Invalid protection profile")
        return [
            {"method": "CooldownPeriod",
             "stop_duration_candles": cooldown},
            {"method": "StoplossGuard",
             "lookback_period_candles": lookback,
             "trade_limit": 1,
             "stop_duration_candles": pause,
             "only_per_pair": False},
            {"method": "MaxDrawdown",
             "lookback_period_candles": lookback,
             "trade_limit": 2,
             "stop_duration_candles": pause,
             "max_allowed_drawdown": .04},
            {"method": "LowProfitPairs",
             "lookback_period_candles": low_profit_lookback,
             "trade_limit": 1,
             "stop_duration_candles": pause,
             "required_profit": 0.0,
             "only_per_pair": True},
        ]


class Fast1h8Strict(_IntradayResearch):
    timeframe = "1h"
    vote_threshold = 8
    protection_mode = "strict"


class Fast1h9Strict(_IntradayResearch):
    timeframe = "1h"
    vote_threshold = 9
    protection_mode = "strict"


class Fast15m8Strict(_IntradayResearch):
    timeframe = "15m"
    vote_threshold = 8
    protection_mode = "strict"


class Fast15m9Strict(_IntradayResearch):
    timeframe = "15m"
    vote_threshold = 9
    protection_mode = "strict"


class Fast5m8Strict(_IntradayResearch):
    timeframe = "5m"
    startup_candle_count = 865  # 72h/5m + one completed prior bar for crash guard
    vote_threshold = 8
    protection_mode = "strict"


class Fast5m9Strict(_IntradayResearch):
    timeframe = "5m"
    startup_candle_count = 865
    vote_threshold = 9
    protection_mode = "strict"


class Fast1h8Active(Fast1h8Strict):
    protection_mode = "active"


class Fast1h9Active(Fast1h9Strict):
    protection_mode = "active"


class Fast15m8Active(Fast15m8Strict):
    protection_mode = "active"


class Fast15m9Active(Fast15m9Strict):
    protection_mode = "active"


class Fast5m8Active(Fast5m8Strict):
    protection_mode = "active"


class Fast5m9Active(Fast5m9Strict):
    protection_mode = "active"
