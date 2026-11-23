"""Strictly historical cross-asset research: original 8-of-10 vs funding/OI veto.

No real orders, no increase in risk, and no alteration to the production
ETH-specific strategy class. One independent pair/account per backtest.
"""
from __future__ import annotations

import json
from pathlib import Path

from pandas import DataFrame

from GuardedConsensusETH import GuardedConsensusETH
from quality_candidate_features import derivatives_crowding

ROOT = Path(__file__).resolve().parents[2]

# Kraken Futures official perpetual contract IDs verified with public CCXT
# market metadata on 2026-11-23; fail closed for anything else.
CONTRACTS = {
    "BTC/USD:USD": "PF_XBTUSD",
    "SOL/USD:USD": "PF_SOLUSD",
    "XRP/USD:USD": "PF_XRPUSD",
    "DOGE/USD:USD": "PF_DOGEUSD",
    "ADA/USD:USD": "PF_ADAUSD",
}


class CrossAssetProtectedConsensus(GuardedConsensusETH):
    """Unmodified 10-indicator rules, same 1x / ATR sizing / stop protections."""

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata.get("pair")
        if pair not in CONTRACTS:
            raise ValueError("This research only supports the five verified contracts")
        return super().populate_indicators(dataframe, metadata)


class CrossAssetFundingOIConsensus(CrossAssetProtectedConsensus):
    """Funding and independently sourced 4h open interest: veto only, never adds risk."""

    def informative_pairs(self):
        if len(self.config["exchange"]["pair_whitelist"]) != 1:
            raise ValueError("Research requires one separate pair-specific paper wallet")
        pair = self.config["exchange"]["pair_whitelist"][0]
        if pair not in CONTRACTS:
            raise ValueError(f"No official OI contract mapping for {pair}")
        return [(pair, "1h", "funding_rate")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_indicators(dataframe, metadata)
        pair = metadata["pair"]
        contract = CONTRACTS[pair]
        oi_path = ROOT / "user_data" / "data" / "cross-asset-oi" / (contract + ".json")
        if not oi_path.exists():
            raise RuntimeError(f"Official Kraken open-interest file missing: {contract}")
        document = json.loads(oi_path.read_text())
        if document.get("research_contract") != contract:
            raise RuntimeError("Cross-asset market/OI mismatch: refuse backtest")
        if not self.dp:
            raise RuntimeError("Funding market data unavailable")
        funding = self.dp.get_pair_dataframe(
            pair=pair, timeframe="1h", candle_type="funding_rate")
        gates = derivatives_crowding(frame, funding, document)
        frame["cross_deriv_long_allowed"] = gates["deriv_long"]
        frame["cross_deriv_short_allowed"] = gates["deriv_short"]
        return frame

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        frame = super().populate_entry_trend(dataframe, metadata)
        frame.loc[~frame["cross_deriv_long_allowed"].fillna(False).astype(bool),
                  "enter_long"] = 0
        frame.loc[~frame["cross_deriv_short_allowed"].fillna(False).astype(bool),
                  "enter_short"] = 0
        return frame
