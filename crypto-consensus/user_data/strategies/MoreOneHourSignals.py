"""One-hour more-opportunities experiments, NO real exchange orders.

The historical frozen 8/10 class and forward paper-ledger are NOT modified.
Any added "flow" route combines completed VWAP, CMF, volume participation
and ATR-normalized momentum. This is NOT 14 independent AI bots: the
signals may be statistically correlated and must be evaluated for overfit.
"""
from __future__ import annotations

from pandas import DataFrame

from OneHourQualityResearch import _QualityOneHour
from one_hour_flow_signals import flow_features,soft_btc_regime,entry_masks


class _OneHourMoreSignals(_QualityOneHour):
    timeframe="1h"
    required_votes=8
    consensus_threshold=8
    model_gate="both"
    trigger="vote"
    soft_btc=False
    after_loss_hours=24

    def informative_pairs(self):
        items=list(super().informative_pairs())
        if self.soft_btc and ("BTC/USD:USD","12h","futures") not in items:
            items.append(("BTC/USD:USD","12h","futures"))
        return items

    def populate_indicators(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        frame=super().populate_indicators(dataframe,metadata)
        if self.soft_btc:
            if self.model_gate!="oi" or self.dp is None:
                raise ValueError("Soft BTC model requires actual OI and actual BTC 12h")
            btc=self.dp.get_pair_dataframe(
                "BTC/USD:USD","12h",candle_type="futures")
            aligned=soft_btc_regime(frame,btc)
            frame["one_hour_long_ok"]=(
                frame["one_hour_long_ok"].fillna(False).astype(bool)&aligned["allow_long"])
            frame["one_hour_short_ok"]=(
                frame["one_hour_short_ok"].fillna(False).astype(bool)&aligned["allow_short"])
        return flow_features(frame)

    def populate_entry_trend(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        # Do NOT call super(): that imposes inherited 8/10 before an
        # alternative 6/10 or 7/10 entry could ever qualify.
        frame=dataframe.copy()
        frame["enter_long"]=0
        frame["enter_short"]=0
        long_ok,short_ok=entry_masks(frame,self.trigger,self.consensus_threshold)
        safe=(frame["warm"].fillna(False).astype(bool)&
              ~frame["crash_block"].fillna(True).astype(bool)&
              frame["volume"].gt(0)&frame["atr14"].gt(0))
        frame.loc[safe&long_ok&
                  frame["one_hour_long_ok"].fillna(False).astype(bool),
                  "enter_long"]=1
        frame.loc[safe&short_ok&
                  frame["one_hour_short_ok"].fillna(False).astype(bool),
                  "enter_short"]=1
        if (frame["enter_long"].astype(bool)&
                frame["enter_short"].astype(bool)).any():
            raise ValueError("Conflicting hourly long/short research entries")
        return frame


class More1h8Both(_OneHourMoreSignals):
    consensus_threshold=8

class More1h7Both(_OneHourMoreSignals):
    consensus_threshold=7

class More1h6Both(_OneHourMoreSignals):
    consensus_threshold=6

class More1h7BTC(_OneHourMoreSignals):
    consensus_threshold=7
    model_gate="btc"

class More1h6BTC(_OneHourMoreSignals):
    consensus_threshold=6
    model_gate="btc"

class More1h7SoftBTC(_OneHourMoreSignals):
    consensus_threshold=7
    model_gate="oi"
    soft_btc=True

class More1h7Flow(_OneHourMoreSignals):
    consensus_threshold=7
    trigger="flow"

class More1h6Flow(_OneHourMoreSignals):
    consensus_threshold=6
    trigger="flow"

class More1h7Hybrid(_OneHourMoreSignals):
    consensus_threshold=7
    trigger="hybrid"

class More1h7Breakout(_OneHourMoreSignals):
    consensus_threshold=7
    trigger="break_hybrid"

class More1h7SoftHybrid(_OneHourMoreSignals):
    consensus_threshold=7
    trigger="hybrid"
    model_gate="oi"
    soft_btc=True

class More1h6FlowBTC(_OneHourMoreSignals):
    consensus_threshold=6
    trigger="flow"
    model_gate="btc"
