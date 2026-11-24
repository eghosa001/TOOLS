"""Isolated 1h ETH/SOL research: remove post-trade clock restrictions.

This compares the original 3-hour trade cooldown and 24-hour loss pause
against disabling one or both. It retains genuine market filters,
position sizing, Freqtrade ATR stop, emergency stop, <=1x leverage,
one position, and the independent seven-day 4% MaxDrawdown protection.
No existing forward paper or live configuration is modified.
"""
from __future__ import annotations

from OneHourQualityResearch import _QualityOneHour
from intraday_research_utils import protection_settings

_ALLOWED=("baseline","no_post_trade_wait","no_loss_pause","no_time_locks")

class _TimeLockResearch(_QualityOneHour):
    timeframe="1h"
    cooldown_mode="active"
    model_gate="both"
    required_votes=8
    time_locks="baseline"

    @property
    def protections(self):
        if self.time_locks not in _ALLOWED:
            raise ValueError("Unknown controlled clock-removal experiment")
        base=protection_settings("active")
        # Remove ONLY temporal restrictions, NEVER remove the account-level
        # 7-day MaxDrawdown guard, original stops or stake limits.
        if self.time_locks in ("no_post_trade_wait","no_time_locks"):
            base=[p for p in base if p["method"]!="CooldownPeriod"]
        if self.time_locks in ("no_loss_pause","no_time_locks"):
            base=[p for p in base
                  if p["method"] not in ("StoplossGuard","LowProfitPairs")]
        if [x["method"] for x in base].count("MaxDrawdown")!=1:
            raise AssertionError("Seven-day account drawdown safety must persist")
        return base


class ClockETHBaseline(_TimeLockResearch):
    required_votes=8
    time_locks="baseline"


class ClockETHNoPostTradeWait(_TimeLockResearch):
    required_votes=8
    time_locks="no_post_trade_wait"


class ClockETHNoLossPause(_TimeLockResearch):
    required_votes=8
    time_locks="no_loss_pause"


class ClockETHNoTimeLocks(_TimeLockResearch):
    required_votes=8
    time_locks="no_time_locks"


class ClockSOLBaseline(_TimeLockResearch):
    required_votes=9
    time_locks="baseline"


class ClockSOLNoPostTradeWait(_TimeLockResearch):
    required_votes=9
    time_locks="no_post_trade_wait"


class ClockSOLNoLossPause(_TimeLockResearch):
    required_votes=9
    time_locks="no_loss_pause"


class ClockSOLNoTimeLocks(_TimeLockResearch):
    required_votes=9
    time_locks="no_time_locks"
