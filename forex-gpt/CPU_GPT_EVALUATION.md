# Combined CPU + GPT Forex risk evaluation

## What was preserved

- The CPU signal is unchanged: CFTC TFF Futures Only GBP contract `096742`, weekly leveraged-money net-position fraction change of at least `0.005` in either direction.
- The live scheduled paper-research entry stays Wednesday **10:00 UTC**. The historical **09:00 UTC** strategy is a different backtest and is **not** silently substituted.
- CPU paper strategies stay: **1,000 GBP / five calendar days** and **500 GBP / two calendar days** with a positive sum of up to eight previously closed baseline CPU trades (at least four).
- GPT cannot change CPU direction, entry, holding time, order state or the performance gate.
- No broker integration or live orders were introduced.

## Historical reference benchmarks — not new forward test outcomes

These were reported in the prior research and must be reproduced from the original price dataset before making comparisons:

| Benchmark | Entry UTC | Sample | Net simulated P&L |
|---|---|---|---:|
| Original CPU five-day 1,000 GBP (no financing) | 09:00 | 39 trades in 2026 through Nov 20 | +$187.84 |
| Same 09:00 baseline with illustrative financing | 09:00 | 39 trades | +$178.09 |
| Matched CPU five-day 1,000 GBP | 10:00 | 38 trades in 2026 | +$177.53 |
| Matched GPT veto five-day 1,000 GBP | 10:00 | 38 trade opportunities | +$128.56 |
| Matched CPU two-day 500 GBP (ungated 2026) | 10:00 | 38 trade opportunities | +$65.105 |
| Matched GPT veto two-day 500 GBP | 10:00 | 38 trade opportunities | +$55.165 |
| CPU gated two-day 500 GBP historical | Original historical configuration | 142 trades, 2020–2026 | +$101.76 |

The five-day, 09:00 CPU backtest lost $192.45 during 2020–2025 (271 historical trades). The positive 2026 results do not prove consistent future profitability. The archived GPT historical vetoes were not an independent real-time forward experiment.

## What was added

`shadow_evaluation.py` combines the same CPU and GPT experiment for each *matured* scheduled paper signal:

- **Five-day CPU 1,000 GBP vs GPT veto at 1,000 GBP.** `SKIP` means hypothetical cash, while `KEEP_2D` and `KEEP_5D` both preserve five-day CPU exposure in the veto-only comparator.
- **Five-day CPU vs GPT duration selection at the same 1,000 GBP.** `KEEP_2D` uses the new 1,000 GBP / two-day paper scenario. Do not compare 500 GBP to 1,000 GBP returns.
- **Five-day CPU vs a hypothetical $5 protective stop.** This is a separate fixed-risk scenario, not the actual CPU strategy.
- **Gated two-day CPU 500 GBP vs GPT veto.** Uses only signals for which the original eight-trade gate approved the baseline trade.
- **Gated two-day CPU vs GPT duration choice at the same 500 GBP.**
- **Gated two-day CPU vs hypothetical $3 protective stop.**

Each comparison counts only matched matured signals, and reports net P&L difference, gross losing dollars, worst loss, closed-equity drawdown, skipped winners, skipped losers and profit-factor metrics. Failed GPT calls and incomplete alternative outcomes are never counted as successful predictions.

The GPT request now includes the *already closed* eight-trade CPU performance history, gate status and estimated transaction costs. It never includes the upcoming trade outcome.

The rolling GitHub Actions paper ledger and its report contain `summary.GPT_CPU_combined_risk_audit`. The audit always declares `gpt_can_override_cpu=false` and `gpt_approved_for_live_orders=false`.

## Verification

Run `python3 -m unittest discover -s forex-gpt -p 'test_*.py' -v`.

The additional checks validate identical position sizes, skip-winner accounting, matching only matured outcomes, the two-day CPU gate and fail-closed behavior for missing GPT advice. All checks are offline and incur no OpenAI API costs.

## What this does NOT establish

- Passing tests establishes calculation and data-flow correctness, **not** trading profitability.
- Neither historical simulation nor the current paper ledger demonstrates how a broker would have filled a stop or paid/charged swaps.
- GitHub Actions does **not** provide millisecond trade execution. No broker latency is measured by this change.
- GPT is not permitted to influence execution without prospective evidence, risk limits, independent broker fills and explicit permission.

**Recommendation:** Keep the profitable-period CPU baseline intact. Accumulate new forward results for the GPT risk warning and both stop scenarios, then compare only matched trades with verified broker costs. Do not promote GPT based on the original 2026 retrospective dataset.
