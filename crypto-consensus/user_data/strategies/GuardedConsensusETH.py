"""Freqtrade V3 port of the FROZEN 8-of-10 ETH futures hypothesis.

IMPORTANT: This does not reproduce the previous custom simulator trade-for-trade.
Freqtrade's fill, intra-candle stop, min-stake and protection semantics differ.
Treat any Freqtrade results as independent, not interchangeable, validation.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import math
import json
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
from risk_guards import crash_mask, TRADE_RISK_FRACTION


class GuardedConsensusETH(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "12h"
    can_short = True
    startup_candle_count = STARTUP_CANDLES
    process_only_new_candles = True
    minimal_roi = {"0": 100.0}
    stoploss = -0.04  # price-distance emergency fallback, not guaranteed account cap
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
            {"method": "StoplossGuard", "lookback_period_candles": 14,
             "trade_limit": 1, "stop_duration_candles": 14,
             "only_per_pair": False},
            {"method": "MaxDrawdown", "lookback_period_candles": 14,
             "trade_limit": 2, "stop_duration_candles": 14,
             "max_allowed_drawdown": .04},
            {"method": "LowProfitPairs", "lookback_period_candles": 1,
             "trade_limit": 1, "stop_duration_candles": 14,
             "required_profit": 0.0, "only_per_pair": True},
        ]

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float,
                            rate: float, time_in_force: str, current_time: datetime,
                            entry_tag: str | None, side: str, **kwargs) -> bool:
        """Host watchdog can freeze all new paper entries; never places orders."""
        import os
        pause = os.environ.get("CRYPTO_PAPER_PAUSE_FILE")
        if not pause:
            return True
        try:
            return not Path(pause).exists()
        except OSError:
            return False

    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return 1.0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Avoid iloc[-1] here: this function runs over entire backtest history.
        out = build_indicators(dataframe)
        out['crash_block'] = crash_mask(out).to_numpy()
        return out

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        dataframe.loc[(dataframe["warm"]) &
                      (dataframe["buy_votes"] >= 8) &
                      (~dataframe["crash_block"]) &
                      (dataframe["volume"] > 0), "enter_long"] = 1
        dataframe.loc[(dataframe["warm"]) &
                      (dataframe["buy_votes"] <= 2) &
                      (~dataframe["crash_block"]) &
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
        risk_stake = wallet * TRADE_RISK_FRACTION * current_rate / (max(2.5 * atr, .04 * current_rate) + .002 * current_rate)
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



# Research candidates only; GuardedConsensusETH above is byte-for-byte
# unchanged. These strategies are never connected to real trading.
from quality_candidate_features import (btc_regime, derivatives_crowding,
                                         volatility_breakout, ml_direction)


class _QualityResearchBase(GuardedConsensusETH):
    def _candidate_gate(self, frame: DataFrame) -> tuple[pd.Series, pd.Series]:
        raise NotImplementedError

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        long_allowed, short_allowed = self._candidate_gate(dataframe)
        dataframe.loc[~long_allowed.fillna(False).astype(bool), "enter_long"] = 0
        dataframe.loc[~short_allowed.fillna(False).astype(bool), "enter_short"] = 0
        return dataframe


class ResearchBTCRegimeETH(_QualityResearchBase):
    """Conservatively lagged BTC Futures macro trend and shock veto."""
    def informative_pairs(self):
        return [("BTC/USD:USD", "12h", "futures")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_indicators(dataframe, metadata)
        if self.dp is None:
            raise ValueError("No BTC informative feed available")
        btc = self.dp.get_pair_dataframe("BTC/USD:USD", "12h",
                                         candle_type="futures")
        flags = btc_regime(frame, btc)
        frame["candidate_long"] = flags["btc_up"]
        frame["candidate_short"] = flags["btc_down"]
        frame["btc_shock"] = flags["btc_shock"]
        return frame

    def _candidate_gate(self, frame: DataFrame):
        return (frame["candidate_long"] & ~frame["btc_shock"],
                frame["candidate_short"] & ~frame["btc_shock"])


class ResearchFundingOpenInterestETH(_QualityResearchBase):
    """Real Kraken hourly funding + independently fetched 4h OI crowding veto.

    No fabricated OI or data-dependent fallback: unavailable history fails the
    experiment instead of being represented as zero/open interest unchanged.
    """
    def informative_pairs(self):
        return [("ETH/USD:USD", "1h", "funding_rate")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_indicators(dataframe, metadata)
        if self.dp is None:
            raise ValueError("No funding history dataprovider")
        funding = self.dp.get_pair_dataframe(
            pair=metadata["pair"], timeframe="1h", candle_type="funding_rate")
        oi_path = ROOT / "user_data" / "data" / "official-kraken-eth-oi.json"
        if not oi_path.exists():
            raise ValueError("Missing independently verified official OI research file")
        oi = json.loads(oi_path.read_text())
        flags = derivatives_crowding(frame, funding, oi)
        frame["candidate_long"] = flags["deriv_long"]
        frame["candidate_short"] = flags["deriv_short"]
        return frame

    def _candidate_gate(self, frame: DataFrame):
        return frame["candidate_long"], frame["candidate_short"]


class ResearchVolatilityBreakoutETH(_QualityResearchBase):
    """Require a genuine 3-day completed-price breakout at moderate ATR."""
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_indicators(dataframe, metadata)
        flags = volatility_breakout(frame)
        frame["candidate_long"] = flags["breakout_long"]
        frame["candidate_short"] = flags["breakout_short"]
        return frame

    def _candidate_gate(self, frame: DataFrame):
        return frame["candidate_long"], frame["candidate_short"]


class ResearchOnlineRidgeETH(_QualityResearchBase):
    """Rolling time-ordered, embargoed ridge with no future target leakage."""
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_indicators(dataframe, metadata)
        flags = ml_direction(frame)
        frame["candidate_long"] = flags["ml_long"]
        frame["candidate_short"] = flags["ml_short"]
        frame["candidate_ml_return"] = flags["ml_pred"]
        return frame

    def _candidate_gate(self, frame: DataFrame):
        return frame["candidate_long"], frame["candidate_short"]
