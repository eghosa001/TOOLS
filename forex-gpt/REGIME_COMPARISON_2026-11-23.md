# CFTC GBP/USD market-regime comparison — 23 November 2026

**Status:** completed independent, retrospective historical comparison. **Not a live trading result, not production-approved.**

[Successful GitHub Actions run](https://github.com/eghosa001/TOOLS/actions/runs/45139119298) · [Detailed result artifact](https://github.com/eghosa001/TOOLS/actions/runs/45139119298/artifacts/14801156586)

## Fixed experiment

The existing CFTC GBP futures leveraged-money net-positioning rule remains untouched. This experiment used official weekly CFTC TFF Futures Only reports for contract `096742`, entered the GBP/USD simulated position at **10:00 UTC on the Wednesday eight days after the Tuesday report**, required a weekly net-position change of magnitude at least 0.005, and settled five calendar days later. Each trade used a 1,000 GBP notional position and historical Dukascopy H1 bid/ask quotes.

Three predeclared paper-only filters were compared with the same eligible signals, same positions and same modeled costs:

1. **Volatility filter:** skip when the median high-low spread across the preceding 120 completed H1 candles exceeds 1.5 times that of the preceding 1,200 completed H1 candles.
2. **Trend agreement:** take a signal only when the preceding 120 completed H1 candles' GBP/USD momentum agrees with the CFTC direction.
3. **Combined:** require both conditions.

Modeled costs: historical bid/ask quotes; additional 0.2 pip round-trip slippage; $0.06 round-trip commission; illustrative $0.25 for five days' financing. The quotes are **not broker fills**, and the financing is not verified with a broker.

The research fetched 445 official historical CFTC reports and 62,925 aligned hourly bid/ask candles. It generated 313 complete matched trades. Exceptional non-Tuesday CFTC report dates and incomplete/missing data were not silently substituted.

## Results (US dollars)

| Period | Matched trades | Unfiltered CPU | Volatility filter | Trend agreement | Combined |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020–2023 | 181 | -132.15 | -225.43 | +105.57 | +64.41 |
| 2024–2025 | 93 | -64.07 | -99.43 | -29.69 | -29.69 |
| 2026 to cutoff | 39 | +163.54 | +151.48 | +86.75 | +74.69 |
| **Full sample** | **313** | **-32.68** | **-173.38** | **+162.63** | **+109.41** |

| Full-sample risk metric | Unfiltered CPU | Trend agreement |
| --- | ---: | ---: |
| Simulated P&L | -$32.68 | +$162.63 |
| Closed-trade equity drawdown | $289.92 | $115.04 |
| Gross losses | $1,483.97 | $533.25 |
| Worst closed trade | -$69.09 | -$30.12 |
| Trades taken | 313 | 132 |
| Skipped winners | 0 | 84 |
| Skipped losers | 0 | 97 |
| Profit factor | 0.978 | 1.305 |

**Finding:** simple trend agreement improved full-period historical net by $195.31 relative to this matched unfiltered baseline, but underperformed in 2026 by $76.79 and remained unprofitable in 2024–2025. A standalone extreme-volatility filter worsened results.

**Decision:** research promising but **do not turn it on in the existing strategy or put real money at risk on this evidence**. Accumulate genuinely prospective, frozen-hypothesis data; verify broker fees, swaps, fill quality, exposure/margin and intratrade equity drawdown before considering changes.

**Comparability:** the previous published 09:00 UTC historical experiment showed different historical P&L and sample selection. This study uses **10:00 UTC** and slightly different source/cost/data conditions. Its original CPU control and filter results are matched internally, but do not claim to exactly reproduce the original $187.84 reference backtest or prove a realistic account return on $150.

Code: [regime_backtest.py](./regime_backtest.py), [regime_fetch.cjs](./regime_fetch.cjs), [workflow](../.github/workflows/forex-regime-research.yml).

No broker orders, API inference, or changes to CPU/GPT trading rules were made.
