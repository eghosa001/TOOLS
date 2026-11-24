"""Research-only 1h ETH/SOL: 8/10 and 9/10, risk gates and causal external data.

No Freqtrade live or dry-run service is started by this file. Only historical
backtesting classes; original 12h and existing forward observer remain intact.
"""
from __future__ import annotations

import json
from pathlib import Path

from pandas import DataFrame

from IntradayResearch import _IntradayBase
from intraday_research_utils import startup_candles, protection_settings
from one_hour_quality_features import btc_macro_gate, funding_oi_gate, combine_and

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_IDS = {"ETH/USD:USD": "PF_ETHUSD", "SOL/USD:USD": "PF_SOLUSD"}


class _QualityOneHour(_IntradayBase):
    timeframe = "1h"
    startup_candle_count = startup_candles("1h")
    required_votes = 8
    cooldown_mode = "active"
    model_gate = "base"
    after_loss_hours = 24

    def _pair(self) -> str:
        pairs = self.config["exchange"]["pair_whitelist"]
        if len(pairs) != 1 or pairs[0] not in CONTRACT_IDS:
            raise ValueError("Only one verified ETH or SOL futures research wallet")
        return pairs[0]

    @property
    def protections(self):
        if self.after_loss_hours not in (24,48):
            raise ValueError("Unapproved cooldown length")
        settings = protection_settings("active")
        for guard in settings:
            if guard["method"] in ("StoplossGuard", "LowProfitPairs"):
                guard["stop_duration"] = self.after_loss_hours * 60
        # Keep seven-day MaxDrawdown lookback and pause; no removal of original ATR stop.
        return settings

    def informative_pairs(self):
        pair = self._pair()
        out = []
        if self.model_gate in ("btc","both"):
            out.append(("BTC/USD:USD","12h","futures"))
        if self.model_gate in ("oi","both"):
            out.append((pair,"1h","funding_rate"))
        return out

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = self._pair()
        if metadata.get("pair") != pair:
            raise ValueError("No mixed-market evidence allowed")
        frame = super().populate_indicators(dataframe,metadata)
        if self.model_gate == "base":
            return frame
        if self.model_gate not in ("btc","oi","both") or self.dp is None:
            raise ValueError("Unknown one-hour candidate or missing actual feed")
        outcomes = {}
        if self.model_gate in ("btc","both"):
            btc = self.dp.get_pair_dataframe("BTC/USD:USD", "12h",
                                             candle_type="futures")
            outcomes["btc"] = btc_macro_gate(frame,btc)
        if self.model_gate in ("oi","both"):
            contract = CONTRACT_IDS[pair]
            path=ROOT/"user_data"/"data"/"quality-one-hour-oi"/(contract+".json")
            if not path.exists():
                raise ValueError(f"Official historical {contract} OI file unavailable")
            source=json.loads(path.read_text())
            if source.get("research_contract") != contract:
                raise ValueError("Official open-interest market mismatch")
            funding=self.dp.get_pair_dataframe(
                pair=pair,timeframe="1h",candle_type="funding_rate")
            outcomes["oi"]=funding_oi_gate(frame,funding,source)
        if self.model_gate=="both":
            gate=combine_and(outcomes["btc"],outcomes["oi"])
        else:
            gate=outcomes[self.model_gate]
        frame["one_hour_long_ok"]=gate["allow_long"]
        frame["one_hour_short_ok"]=gate["allow_short"]
        return frame

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame=super().populate_entry_trend(dataframe,metadata)
        if self.model_gate!="base":
            frame.loc[~frame["one_hour_long_ok"].fillna(False).astype(bool),"enter_long"]=0
            frame.loc[~frame["one_hour_short_ok"].fillna(False).astype(bool),"enter_short"]=0
        return frame


class Q1h8Base24(_QualityOneHour):
    required_votes=8
    model_gate="base"

class Q1h8BTC24(_QualityOneHour):
    required_votes=8
    model_gate="btc"

class Q1h8OI24(_QualityOneHour):
    required_votes=8
    model_gate="oi"

class Q1h8Both24(_QualityOneHour):
    required_votes=8
    model_gate="both"

class Q1h8Base48(_QualityOneHour):
    required_votes=8
    model_gate="base"
    after_loss_hours=48

class Q1h8Both48(_QualityOneHour):
    required_votes=8
    model_gate="both"
    after_loss_hours=48


class Q1h9Base24(_QualityOneHour):
    required_votes=9
    model_gate="base"

class Q1h9BTC24(_QualityOneHour):
    required_votes=9
    model_gate="btc"

class Q1h9OI24(_QualityOneHour):
    required_votes=9
    model_gate="oi"

class Q1h9Both24(_QualityOneHour):
    required_votes=9
    model_gate="both"

class Q1h9Base48(_QualityOneHour):
    required_votes=9
    model_gate="base"
    after_loss_hours=48

class Q1h9Both48(_QualityOneHour):
    required_votes=9
    model_gate="both"
    after_loss_hours=48
