"""Risk guards for a keyless paper simulator. Observed losses can exceed thresholds in a gap."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import pandas as pd

TRADE_RISK_FRACTION = .01
DAY_LOSS_FRACTION = .02
WEEK_LOSS_FRACTION = .04
PEAK_DRAWDOWN_FRACTION = .06
CRASH_12H = .08
CRASH_3D = .15
CRASH_BLOCK_CANDLES = 4
DAY_MS = 86400000
WEEK_MS = 7 * DAY_MS

def crash_mask(df):
    c = pd.to_numeric(df["close"], errors="raise")
    shock = (c / c.shift(1) - 1).abs().ge(CRASH_12H) | (c / c.shift(6) - 1).abs().ge(CRASH_3D)
    return shock.rolling(CRASH_BLOCK_CANDLES, min_periods=1).max().fillna(0).astype(bool)

def _date(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).date()

def _week(ms):
    d = _date(ms)
    return (d - timedelta(days=d.weekday())).isoformat()

def ensure_risk_state(s, now, equity):
    if equity <= 0:
        raise RuntimeError("Invalid or insolvent account")
    s.setdefault("equity_peak", max(150., equity))
    s.setdefault("risk_day", _date(now).isoformat())
    s.setdefault("risk_day_start", equity)
    s.setdefault("risk_week", _week(now))
    s.setdefault("risk_week_start", equity)
    s.setdefault("daily_pause_until_ms", 0)
    s.setdefault("weekly_pause_until_ms", 0)
    s.setdefault("permanent_risk_lock", False)
    s.setdefault("risk_events", [])

def inspect_account(s, now, equity):
    ensure_risk_state(s, now, equity)
    if s["risk_day"] != _date(now).isoformat():
        s["risk_day"] = _date(now).isoformat()
        s["risk_day_start"] = equity
    if s["risk_week"] != _week(now):
        s["risk_week"] = _week(now)
        s["risk_week_start"] = equity
    s["equity_peak"] = max(float(s["equity_peak"]), equity)
    daily = equity / s["risk_day_start"] - 1
    weekly = equity / s["risk_week_start"] - 1
    peak = equity / s["equity_peak"] - 1
    events = []
    if peak <= -PEAK_DRAWDOWN_FRACTION and not s["permanent_risk_lock"]:
        s["permanent_risk_lock"] = True
        events.append("peak_drawdown_6pct_manual_unlock")
    if weekly <= -WEEK_LOSS_FRACTION and now >= s["weekly_pause_until_ms"]:
        s["weekly_pause_until_ms"] = now + WEEK_MS
        events.append("weekly_loss_4pct_pause_7d")
    if daily <= -DAY_LOSS_FRACTION and now >= s["daily_pause_until_ms"]:
        tomorrow = datetime.combine(_date(now) + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        s["daily_pause_until_ms"] = int(tomorrow.timestamp() * 1000)
        events.append("daily_loss_2pct_pause")
    if events:
        s["risk_events"].append({"at": datetime.fromtimestamp(now / 1000, timezone.utc).isoformat(),
                                 "equity": round(equity, 6), "reasons": events})
    return events

def can_enter(s, now, crash=False):
    return (not crash and not s.get("permanent_risk_lock", False)
            and now >= s.get("daily_pause_until_ms", 0)
            and now >= s.get("weekly_pause_until_ms", 0)
            and now >= s.get("cooldown_until_ms", 0))
