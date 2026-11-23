"""Read-only, matched CPU/GPT risk comparisons for the weekly GBP/USD paper engine.

No orders, no risk overrides and no changes to CPU entry rules. Comparisons
use the same dated signals, position sizes and only matured paper outcomes.
The original Wednesday 09:00 UTC 39-trade backtest is NOT compared to these
Wednesday 10:00 UTC prospective observations.
"""
from __future__ import annotations

CHOICES = frozenset(("SKIP", "KEEP_2D", "KEEP_5D"))


def closed(signal, key):
    record = signal.get("settlements", {}).get(key)
    if not isinstance(record, dict) or record.get("status") != "closed":
        return None
    pnl = record.get("net_usd")
    if isinstance(pnl, bool) or not isinstance(pnl, (int, float)):
        return None
    return float(pnl)


def metrics(vals):
    if not vals:
        return {"n": 0, "net_usd": None, "gross_losing_usd": None,
                "worst_loss_usd": None, "closed_drawdown_usd": None,
                "win_rate_pct": None, "profit_factor": None}
    net = 0.0
    peak = 0.0
    max_dd = 0.0
    for v in vals:
        net += v
        peak = max(peak, net)
        max_dd = max(max_dd, peak - net)
    gross_loss = -sum(v for v in vals if v < 0)
    gross_win = sum(v for v in vals if v > 0)
    return {
        "n": len(vals), "net_usd": round(net, 4),
        "gross_losing_usd": round(gross_loss, 4),
        "worst_loss_usd": round(min(0.0, min(vals)), 4),
        "closed_drawdown_usd": round(max_dd, 4),
        "win_rate_pct": round(100 * sum(v > 0 for v in vals) / len(vals), 2),
        "profit_factor": round(gross_win / gross_loss, 4) if gross_loss > 0 else None,
    }


def reduction_pct(before, after):
    if before is None or after is None or before <= 0:
        return None
    return round(100.0 * (before - after) / before, 2)


def comparison(rows, base_name, candidate_name):
    """rows: (baseline PnL, candidate PnL, is_gpt_skip)."""
    cpu = [a for a, _, _ in rows]
    candidate = [b for _, b, _ in rows]
    a = metrics(cpu)
    b = metrics(candidate)
    skipped = [(x, y) for x, y, flag in rows if flag]
    return {
        "baseline": base_name,
        "candidate_name": candidate_name,
        "matched_signals": len(rows),
        "cpu": a,
        "candidate": b,
        "net_improvement_usd": round(b["net_usd"] - a["net_usd"], 4) if rows else None,
        "gross_loss_reduction_pct": reduction_pct(a["gross_losing_usd"], b["gross_losing_usd"]),
        "worst_loss_reduction_pct": reduction_pct(-a["worst_loss_usd"], -b["worst_loss_usd"]) if rows else None,
        "closed_drawdown_reduction_pct": reduction_pct(a["closed_drawdown_usd"], b["closed_drawdown_usd"]),
        "gpt_skipped_winners": sum(x > 0 for x, _ in skipped),
        "gpt_skipped_losers": sum(x < 0 for x, _ in skipped),
        "gpt_missed_winning_usd": round(sum(x for x, _ in skipped if x > 0), 4),
        "gpt_avoided_losing_usd": round(-sum(x for x, _ in skipped if x < 0), 4),
    }


def evaluate(state):
    """Measure shadow advice, independent of CPU trading state or order logic.

    Veto-only keeps the CPU's original horizon whenever GPT says KEEP.
    Adaptive tests the GPT-requested horizon at the SAME unit size. A choice
    is scored only when its relevant actual-paper scenario has matured.
    """
    signals = sorted(state.get("signals", []),
                     key=lambda x: x.get("paper_entry_utc", ""))
    five_veto, five_adaptive = [], []
    two_veto, two_adaptive = [], []
    five_stop, two_stop = [], []
    count_five, count_two = 0, 0
    failures = 0
    for sig in signals:
        base5 = closed(sig, "5d_1000") if sig.get("CPU_5d_1000_active") else None
        base2 = closed(sig, "2d_500") if sig.get("CPU_2d_500_active") else None
        if base5 is not None:
            count_five += 1
            stop5 = closed(sig, "5d_1000_stop5")
            if stop5 is not None:
                five_stop.append((base5, stop5, False))
        if base2 is not None:
            count_two += 1
            stop2 = closed(sig, "2d_500_stop3")
            if stop2 is not None:
                two_stop.append((base2, stop2, False))
        advice = sig.get("gpt_advice", {})
        choice = advice.get("choice") if isinstance(advice, dict) else None
        if sig.get("gpt_status") != "SUCCESS_SHADOW" or choice not in CHOICES:
            if base5 is not None or base2 is not None:
                failures += 1
            continue
        if base5 is not None:
            is_skip = choice == "SKIP"
            five_veto.append((base5, 0.0 if is_skip else base5, is_skip))
            alternative = closed(sig, "2d_1000") if choice == "KEEP_2D" else base5
            if is_skip:
                alternative = 0.0
            if alternative is not None:
                five_adaptive.append((base5, alternative, is_skip))
        if base2 is not None:
            is_skip = choice == "SKIP"
            two_veto.append((base2, 0.0 if is_skip else base2, is_skip))
            alternative = closed(sig, "5d_500_gpt_adaptive") if choice == "KEEP_5D" else base2
            if is_skip:
                alternative = 0.0
            if alternative is not None:
                two_adaptive.append((base2, alternative, is_skip))
    return {
        "purpose": "CPU baseline vs GPT warnings and fixed stops, SHADOW ONLY",
        "entry_time_utc": "10:00",
        "excluded_reference": "39-trade 09:00 historical CPU baseline; not same sample",
        "five_day_cpu_signals_matured": count_five,
        "two_day_gated_cpu_signals_matured": count_two,
        "missing_or_failed_gpt_signal_records": failures,
        "five_day_gpt_veto": comparison(five_veto, "CPU_5d_1000", "GPT_veto_5d_1000"),
        "five_day_gpt_horizon": comparison(five_adaptive, "CPU_5d_1000", "GPT_2d_or_5d_same_1000_units"),
        "five_day_fixed_stop": comparison(five_stop, "CPU_5d_1000", "CPU_5d_1000_stop5"),
        "two_day_gpt_veto": comparison(two_veto, "CPU_2d_500_gated", "GPT_veto_2d_500"),
        "two_day_gpt_horizon": comparison(two_adaptive, "CPU_2d_500_gated", "GPT_2d_or_5d_same_500_units"),
        "two_day_fixed_stop": comparison(two_stop, "CPU_2d_500_gated", "CPU_2d_500_stop3"),
        "gpt_can_override_cpu": False,
        "gpt_approved_for_live_orders": False,
        "limitation": ("Prospective completed paper signals only. GPT and stop results "
                       "are observational comparisons with assumed costs, not broker fills. "
                       "No automatic trading promotion or causal proof of improvement."),
    }
