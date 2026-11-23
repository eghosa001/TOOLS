"""Freqtrade V3 port of the FROZEN 8-of-10 ETH futures hypothesis.

IMPORTANT: This does not reproduce the previous custom simulator trade-for-trade.
Freqtrade's fill, intra-candle stop, min-stake and protection semantics differ.
Treat any Freqtrade results as independent, not interchangeable, validation.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import math
import sys
from typing import Any

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, stoploss_from_absolute
from freqtrade.persistence import Trade

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core import build_indicators, STARTUP_CANDLES


class FrozenConsensusETH(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "12h"
    can_short = True
    startup_candle_count = STARTUP_CANDLES
    process_only_new_candles = True
    minimal_roi = {"0": 100.0}
    stoploss = -0.20  # Fail-safe only; custom ATR stop should be tighter.
    use_custom_stoploss = True
    use_exit_signal = True
    exit_profit_only = False
    trailing_stop = False
    position_adjustment_enable = False
    order_types = {"entry": "market", "exit": "market",
                   "stoploss": "market", "stoploss_on_exchange": False}

    @property
    def protections(self):
        # One lost trade starts a 14-candle (7-day) lock.
        # Freqtrade protection semantics are not identical to the custom simulator.
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 3},
            {"method": "LowProfitPairs", "lookback_period_candles": 1,
             "trade_limit": 1, "stop_duration_candles": 14,
             "required_profit": 0.0, "only_per_pair": True},
        ]

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return 1.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Avoid iloc[-1] here: this function runs over entire backtest history.
        return build_indicators(dataframe)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[(dataframe["warm"]) &
                      (dataframe["buy_votes"] >= 8) &
                      (dataframe["volume"] > 0), "enter_long"] = 1
        dataframe.loc[(dataframe["warm"]) &
                      (dataframe["buy_votes"] <= 2) &
                      (dataframe["volume"] > 0), "enter_short"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        dataframe.loc[dataframe["buy_votes"] <= 4, "exit_long"] = 1
        dataframe.loc[dataframe["buy_votes"] >= 6, "exit_short"] = 1
        return dataframe

    def _last_candle(self, pair: str):
        if not self.dp:
            return None
        frame, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if frame is None or frame.empty:
            return None
        return frame.iloc[-1]

    def custom_stake_amount(self, pair: str, current_time: datetime,
                            current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float,
                            leverage: float, entry_tag: str | None,
                            side: str, **kwargs) -> float:
        bar = self._last_candle(pair)
        if bar is None or current_rate <= 0:
            return 0.0
        atr = float(bar["atr14"])
        if not math.isfinite(atr) or atr <= 0:
            return 0.0
        wallet = float(self.wallets.get_total_stake_amount())
        risk_stake = wallet * .02 * current_rate / (2.5 * atr)
        stake = min(float(proposed_stake), float(max_stake), wallet, risk_stake)
        # Never enlarge a low-risk position to satisfy the exchange minimum.
        if min_stake is not None and stake < float(min_stake):
            return 0.0
        return max(0.0, stake)

    def custom_stoploss(self, pair: str, trade: Trade,
                        current_time: datetime, current_rate: float,
                        current_profit: float, after_fill: bool = False,
                        **kwargs) -> float | None:
        bar = self._last_candle(pair)
        if bar is None or current_rate <= 0:
            return None
        atr = float(bar["atr14"])
        if not math.isfinite(atr) or atr <= 0:
            return None
        distance = 2.5 * atr
        candle_close = float(bar["close"])
        # The stop is deliberately never loosened by Freqtrade.
        absolute = (candle_close + distance if trade.is_short
                    else candle_close - distance)
        initial = (trade.open_rate + distance if trade.is_short
                   else trade.open_rate - distance)
        absolute = min(initial, absolute) if trade.is_short else max(initial, absolute)
        # Avoid inverted stops caused by a large gap.
        if (trade.is_short and absolute <= current_rate) or (not trade.is_short and absolute >= current_rate):
            return 0.001
        return stoploss_from_absolute(absolute, current_rate,
                                      is_short=trade.is_short, leverage=trade.leverage)
