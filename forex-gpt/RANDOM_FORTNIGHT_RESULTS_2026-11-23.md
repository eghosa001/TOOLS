# Random historical Forex consistency test — 23 November 2026

**Status:** Historical simulation complete; **none of the tested voting configurations demonstrated consistent profitability**. No live orders, accounts or credentials used.

## Fully auditable run

- [Successful 50-day GitHub Actions execution](https://github.com/eghosa001/TOOLS/actions/runs/45149599022)
- [Full source manifest with quote hashes, per-day decisions, rejected signals and every simulated trade](https://github.com/eghosa001/TOOLS/actions/runs/45149599022/artifacts/14806142274)
- Source files: [preregistered history downloader](./random_fortnight_fetch.cjs), [50-day replay](./random_fortnight_backtest.py), [unchanged tick-voting and execution rules](./tick_paper_replay.py)
- **All 50 historical trading days available; missing quote days: 0.** Four currency-pair evidence groups gate signals (10 rule votes), actual Dukascopy top-of-book quotes and quote volumes for GBPUSD/EURUSD/EURGBP.

## Preregistered random draw

Python `random.Random(20261123)`, one ISO week chosen uniformly in range 6–42 per year for 2022–2026, each the start of a two-week (10-weekday) experiment. Dates were fixed in the committed fetcher before historical returns were retrieved.

| Year | Week | Two-week trading period |
| --- | --- | --- |
| 2022 | 42 | Oct 17–28 |
| 2023 | 37 | Sep 11–22 |
| 2024 | 16 | Apr 15–26 |
| 2025 | 17 | Apr 21–May 2 |
| 2026 | 41 | Oct 5–16 |

**Sampling caveat:** Source covers *one 07:00–09:00 UTC session for each of 50 trading days*, 19 decisions each day (07:15–08:45 UTC in five-minute increments). It is **not** a continuous 24-hour / five-year market simulation.

## Fully costed exploratory quote-only outcomes

All returns are USD net profit/loss **after** the historical bid/ask spread plus modeled round-trip slippage of 0.2 pip and round-trip commission of $0.06. Each fortnight starts separately with illustrative $150 initial capital and a 1,000 GBP position; results across disjoint years are added as cumulative **independent test profit**, not a continuous-account equity curve. Holds are 30 or 120 seconds with 2/2 or 4/4 pip stop/take pairs; no overlapping trades, additional three-of-four factor-group veto, actual quote spreads and stale-quote filters, and $3 per-day stop-pause remain active. Quote execution is hypothetical, not verified broker fills.

### 120-second trades: daily-replay aggregate per historical fortnight

| Period | 6/10 (trades, P&L) | 7/10 (trades, P&L) | 8/10 (trades, P&L) |
| --- | --- | --- | --- |
| Oct 17–28, 2022 | 9 / −$1.39 | 6 / −$0.52 | 1 / +$0.34 |
| Sep 11–22, 2023 | 6 / −$0.86 | 3 / −$0.04 | 0 / $0.00 |
| Apr 15–26, 2024 | 6 / −$0.50 | 0 / $0.00 | 0 / $0.00 |
| Apr 21–May 2, 2025 | 9 / −$1.06 | 1 / −$0.49 | 0 / $0.00 |
| Oct 5–16, 2026 | 8 / +$0.49 | 2 / +$0.13 | 1 / +$0.34 |
| **Totals** | **38 / −$3.32** | **12 / −$0.92** | **2 / +$0.68** |

### 30-second trades: five-window totals

| Threshold | Trades | Wins | Losses | Net $ | Positive 2-week periods |
| --- | ---: | ---: | ---: | ---: | ---: |
| 6/10 | 38 | 10 | 28 | −$5.15 | 1 |
| 7/10 | 12 | 2 | 10 | −$1.96 | 0 |
| 8/10 | 2 | 1 | 1 | −$0.18 | 1 |

### 120-second five-window totals

| Threshold | Trades | Wins | Losses | Net $ | Positive 2-week periods |
| --- | ---: | ---: | ---: | ---: | ---: |
| 6/10 | 38 | 14 | 24 | −$3.32 | 1 |
| 7/10 | 12 | 4 | 8 | −$0.92 | 1 |
| 8/10 | 2 | 2 | 0 | +$0.68 | 2 |

### Interpretation

- A +$0.68 net return on 8/10, 120-second holding **is not evidence of reliability**: there were only two trades in 50 days and three entire fortnights had no trades.
- The 6/10 and 7/10 approaches were net negative across these randomly selected samples. The more active 6/10 120s configuration lost in four out of five randomly drawn windows.
- 10 votes are not 10 independent models: they share signal sources and currency relationships, so the three-of-four factor-group requirement stays enabled.
- No sampled configuration passed a meaningful consistency test; do not select the best sampled combination and rebrand these samples as unseen tests.

## Important distinction: historical economic calendar unavailable

The frozen live-research pipeline **rejects** signals if the economic calendar is absent/stale. A trusted as-of-time GBP/USD economic calendar for the randomly selected historical years was not provided, so this historical test **explicitly did not apply economic-news blackouts**. It does not assert that a calendar existed or invent historical announcements.

Therefore the results are a **quote-only diagnostic**, not a full reproduction of the protected strategy. The actual safe quality gate remains **no real-money orders** until independent new evidence supports an engine. We did **not** loosen or change the future-date scheduled paper test workflow to run this study.

## Next scientifically sound step

Freeze this result and resist optimizing thresholds on these same five samples. Obtain trustworthy historical macro-event data and broker-specific executable tick spread/latency data. Improve genuinely independent signal families or cross-validation design, then evaluate on fresh independent dates or future paper sessions. The current evidence does **not** justify risking the $150 account.
