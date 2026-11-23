# ETH — uninterrupted protected historical futures audit

One Freqtrade wallet, one continuous run, no weekly reset; 12-hour candles, historical Kraken Futures mark/funding data.

**Backtested net result:** +16.563 USD (+11.042%) on 150.00 USD.

**Closed trades:** 15 (7 wins, 8 losses); **forced test-end exits:** 1.
**Full-period Freqtrade drawdown:** 2.2663% (not weekly).

| UTC week starting | Closed W/L | Realized net (USD) | Trades carried across week-end | Forced closes |
|---|---:|---:|---:|---:|
| 2025-12-29 (partial) | 0/0 | +0.000 | 0 | 0 |
| 2026-01-05 | 0/1 | -0.351 | 0 | 0 |
| 2026-01-12 | 0/0 | +0.000 | 1 | 0 |
| 2026-01-19 | 0/1 | -1.127 | 0 | 0 |
| 2026-01-26 | 0/0 | +0.000 | 1 | 0 |
| 2026-02-02 | 0/0 | +0.000 | 1 | 0 |
| 2026-02-09 | 0/0 | +0.000 | 1 | 0 |
| 2026-02-16 | 0/0 | +0.000 | 1 | 0 |
| 2026-02-23 | 1/0 | +5.492 | 1 | 0 |
| 2026-03-02 | 0/1 | -0.847 | 0 | 0 |
| 2026-03-09 | 0/0 | +0.000 | 0 | 0 |
| 2026-03-16 | 0/1 | -0.253 | 0 | 0 |
| 2026-03-23 | 0/0 | +0.000 | 1 | 0 |
| 2026-03-30 | 0/1 | -1.163 | 0 | 0 |
| 2026-04-06 | 0/0 | +0.000 | 1 | 0 |
| 2026-04-13 | 0/0 | +0.000 | 1 | 0 |
| 2026-04-20 | 0/0 | +0.000 | 1 | 0 |
| 2026-04-27 | 0/1 | -0.135 | 0 | 0 |
| 2026-05-04 | 0/0 | +0.000 | 1 | 0 |
| 2026-05-11 | 0/1 | -1.092 | 0 | 0 |
| 2026-05-18 | 0/0 | +0.000 | 1 | 0 |
| 2026-05-25 | 0/0 | +0.000 | 1 | 0 |
| 2026-06-01 | 0/0 | +0.000 | 1 | 0 |
| 2026-06-08 | 0/0 | +0.000 | 0 | 0 |
| 2026-06-15 | 1/0 | +3.050 | 1 | 0 |
| 2026-06-22 | 0/0 | +0.000 | 1 | 0 |
| 2026-06-29 | 0/1 | -0.043 | 0 | 0 |
| 2026-07-06 | 0/0 | +0.000 | 1 | 0 |
| 2026-07-13 | 0/0 | +0.000 | 1 | 0 |
| 2026-07-20 | 0/0 | +0.000 | 1 | 0 |
| 2026-07-27 | 1/0 | +0.384 | 0 | 0 |
| 2026-08-03 | 0/0 | +0.000 | 1 | 0 |
| 2026-08-10 | 0/0 | +0.000 | 1 | 0 |
| 2026-08-17 | 0/0 | +0.000 | 1 | 0 |
| 2026-08-24 | 0/0 | +0.000 | 1 | 0 |
| 2026-08-31 | 0/0 | +0.000 | 1 | 0 |
| 2026-09-07 | 0/0 | +0.000 | 1 | 0 |
| 2026-09-14 | 1/0 | +5.607 | 1 | 0 |
| 2026-09-21 | 0/0 | +0.000 | 1 | 0 |
| 2026-09-28 | 0/0 | +0.000 | 1 | 0 |
| 2026-10-05 | 1/0 | +1.050 | 1 | 0 |
| 2026-10-12 | 0/0 | +0.000 | 1 | 0 |
| 2026-10-19 | 0/0 | +0.000 | 1 | 0 |
| 2026-10-26 | 0/0 | +0.000 | 1 | 0 |
| 2026-11-02 | 1/0 | +0.854 | 1 | 0 |
| 2026-11-09 | 0/0 | +0.000 | 1 | 0 |
| 2026-11-16 | 1/0 | +5.138 | 0 | 1 |

**Interpretation:** A zero-realized-profit week can still have material unrealized position losses. These columns are not full-equity weekly profitability claims.

Fees and funding are already reflected in Freqtrade trade net profit. Do not subtract them again. Reported trade-fee estimates (if complete): 0.284011; recorded funding field total (if complete): -0.27154.

Weekly mark-to-market equity and intrahour risks are instead tracked, with coverage flags, by the separate forward PAPER ledger.

No live trading, no verified exchange-side stop orders.
