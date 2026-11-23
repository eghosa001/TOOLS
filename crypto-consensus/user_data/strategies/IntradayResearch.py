"""Intraday (1h/15m/5m) 8/10 and 9/10 consensus research variants.

Each variant inherits the SAME original Freqtrade protective stake, stop,
exit and leverage methods, while translating entry shock and cooldown
intervals into equivalent elapsed minutes. Research ONLY, no real orders.
"""
from __future__ import annotations

from pandas import DataFrame

from GuardedConsensusETH import GuardedConsensusETH
from intraday_research_utils import (
    agreement_gate, protection_settings, startup_candles,
    time_consistent_crash_mask,
)


class _IntradayBase(GuardedConsensusETH):
    required_votes = 8
    cooldown_mode = "strict"

    @property
    def protections(self):
        return protection_settings(self.cooldown_mode)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        out = super().populate_indicators(dataframe, metadata)
        # super() computes the old 12h crash mask; REPLACE it with an
        # elapsed-time correct mask to avoid near-zero protection on 5m bars.
        out["crash_block"] = time_consistent_crash_mask(out, self.timeframe)
        return out

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The inherited 8/10 entry criteria, exits, stops and sizing remain.
        out = super().populate_entry_trend(dataframe, metadata)
        long_ok, short_ok = agreement_gate(out["buy_votes"], self.required_votes)
        out.loc[~long_ok, "enter_long"] = 0
        out.loc[~short_ok, "enter_short"] = 0
        return out


class Fast1h8Strict(_IntradayBase):
    timeframe = "1h"
    startup_candle_count = startup_candles("1h")
    required_votes = 8
    cooldown_mode = "strict"


class Fast1h9Strict(_IntradayBase):
    timeframe = "1h"
    startup_candle_count = startup_candles("1h")
    required_votes = 9
    cooldown_mode = "strict"


class Fast1h8Active(_IntradayBase):
    timeframe = "1h"
    startup_candle_count = startup_candles("1h")
    required_votes = 8
    cooldown_mode = "active"


class Fast1h9Active(_IntradayBase):
    timeframe = "1h"
    startup_candle_count = startup_candles("1h")
    required_votes = 9
    cooldown_mode = "active"


class Fast15m8Strict(_IntradayBase):
    timeframe = "15m"
    startup_candle_count = startup_candles("15m")
    required_votes = 8
    cooldown_mode = "strict"


class Fast15m9Strict(_IntradayBase):
    timeframe = "15m"
    startup_candle_count = startup_candles("15m")
    required_votes = 9
    cooldown_mode = "strict"


class Fast15m8Active(_IntradayBase):
    timeframe = "15m"
    startup_candle_count = startup_candles("15m")
    required_votes = 8
    cooldown_mode = "active"


class Fast15m9Active(_IntradayBase):
    timeframe = "15m"
    startup_candle_count = startup_candles("15m")
    required_votes = 9
    cooldown_mode = "active"


class Fast5m8Strict(_IntradayBase):
    timeframe = "5m"
    startup_candle_count = startup_candles("5m")
    required_votes = 8
    cooldown_mode = "strict"


class Fast5m9Strict(_IntradayBase):
    timeframe = "5m"
    startup_candle_count = startup_candles("5m")
    required_votes = 9
    cooldown_mode = "strict"


class Fast5m8Active(_IntradayBase):
    timeframe = "5m"
    startup_candle_count = startup_candles("5m")
    required_votes = 8
    cooldown_mode = "active"


class Fast5m9Active(_IntradayBase):
    timeframe = "5m"
    startup_candle_count = startup_candles("5m")
    required_votes = 9
    cooldown_mode = "active"


# Reference control: exactly the 12-hour incumbent strategy, no variations.
# The active research workflow runs GuardedConsensusETH for same calendar dates.
