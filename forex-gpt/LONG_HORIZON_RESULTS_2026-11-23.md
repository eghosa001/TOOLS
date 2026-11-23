# FX Regime Rotation: EUR/USD vs GBP/USD, 10/15/30 minute holds

Completed 23 November 2026. **Read-only historical research: NO LIVE ORDERS.**

## Verified sources

- [Successful historical GitHub Actions run](https://github.com/eghosa001/TOOLS/actions/runs/45155369026)
- [Evidence artifact: date inventory and cryptographic hashes, 2024 selection results, 2025–26 trade-level audit and baseline](https://github.com/eghosa001/TOOLS/actions/runs/45155369026/artifacts/14808446792)
- [Frozen market fetcher](./long_horizon_fetch.cjs)
- [Regime switching, independently trained supervised ML and held-out replay](./long_horizon_backtest.py)

All **100** predeclared days of Dukascopy historical tick bid/ask for EURUSD, GBPUSD and EURGBP were downloaded successfully. Day quotes were validated and cryptographically inventoried. The date windows were precommitted using a deterministic random seed, with exclusions from previously inspected intervals:

| Stage | Dates | Calendar days tested | Eligible paper decision rows |
| --- | --- | ---: | ---: |
| Train | March 14–25 and May 16–27, 2022; June 5–16 and Oct 9–20, 2023 | 40 trading days | 1,064 |
| Validation and specialist selection | Aug 12–23 and Oct 14–25, 2024 | 20 trading days | 223 |
| Held-out evaluation | June 9–20 and Sep 1–12, 2025; Feb 16–27 and May 4–15, 2026 | 40 trading days | 756 |

Sampling covers EURUSD and GBPUSD decision opportunities 08:00–11:00 UTC at 5-minute intervals, with 07:00–12:00 UTC tick context. **Not full 24-hour Forex days.** EURGBP acts as cross-market context, not an additional traded pair.

## Models and execution model

- Detect 4 market regimes: volatile, trending, ranging and mixed using only prior price/quote information.
- Candidate specialists: momentum, breakout, reversal, cross-pair, tick flow, LightGBM expected **net P&L** regression, standardized Ridge expected **net P&L** regression.
- Models fitted only on 2022–23. Candidate expert and hold duration (10m, 15m, 30m) selected separately for each pair and market regime **using 2024 validation outcomes alone**.
- Research selector requires >=8 validation trades and positive net return; stringent selector requires >=15 validation trades, positive lower-one-standard-error mean net return and gains in both 2024 fortnights. If no model passes, abstain.
- Stricter entry spreads: historical EURUSD <=0.75 pip, GBPUSD <=1.05 pips, and five-minute median EURUSD <=0.70, GBPUSD <=0.95 pips. Valid quote freshness <=2 s and entries >=0.5 s and <=4 s after decision.
- Simulated 1,000 base currency units (EUR or GBP). $150 initial account for *each independent day* (not continuous compounding). Stop/target: 10m 8/12 pips; 15m 10/15 pips; 30m 15/22 pips. Actual historical bid/ask quotes for exits, extra assumed 0.2-pip roundtrip slippage and $0.06 roundtrip commission. Nonoverlapping positions across pairs and -$3 daily pause.
- No historical as-of-economic-news feed available: **news blackout NOT applied**; actual broker executable fills, margin, slippage and commissions remain unverified.

## 2024 validation: three exploratory model choices

| Pair and market condition | Selected specialist | Hold | Validation trades | Validation net USD |
| --- | --- | --- | ---: | ---: |
| EURUSD ranging | Ridge net-return regression | 30 min | 14 | +$2.28 |
| GBPUSD ranging | Reversal | 30 min | 9 | +$4.15 |
| GBPUSD mixed | LightGBM net-return regression | 30 min | 15 | +$0.75 |

Other regimes had no candidate with >=8 trades and positive net result. None met the **strict** rule, which requires at least 15 trades, positive one-SE-adjusted mean and positive returns across **both** validation fortnights. Even these selected results may reflect selection bias across many candidates; they are NOT verified live winners.

## 2025–26 independent historical test

**Exploratory market regime router** (choices determined solely by 2024):
- **67 trades, 27 profitable**, net after modeled costs **−$6.21** over 40 trading days.
- By instrument: EURUSD **13 trades, −$2.13**; GBPUSD **54 trades, −$4.08**.
- 15 profitable days of 40; one profitable two-week period out of four.
- Two-week cumulative USD net by heldout window: 2025 Jun 9–20 **−$1.87**; 2025 Sep 1–12 **−$5.61**; 2026 Feb 16–27 **−$0.05**; 2026 May 4–15 **+$1.32**.
- This indicates the 2024-validated-looking positive regimes **did not generalize** to the unseen four fortnights.

**Strict market regime router**:
- **0 trades, $0.00 P&L**, because no 2024 candidates passed the stricter sample-size/reliability gate. This is defensive abstention, not evidence of profitability.

### Fixed per-pair models on the same held-out data (USD after modeled costs)

| Signal | 10 min | 15 min | 30 min |
| --- | ---: | ---: | ---: |
| EURUSD momentum | −$16.90 (118 trades) | −$18.49 (103) | −$16.13 (87) |
| EURUSD reversal | −$10.62 (55) | −$12.63 (51) | −$14.39 (48) |
| EURUSD LightGBM net-return model | −$5.29 (70) | −$3.55 (65) | −$12.83 (84) |
| GBPUSD momentum | −$15.53 (136) | −$21.60 (122) | −$15.82 (98) |
| GBPUSD reversal | −$9.41 (44) | −$8.46 (42) | −$7.90 (36) |
| GBPUSD LightGBM net-return model | −$1.85 (68) | −$11.88 (103) | −$2.65 (86) |

No demonstrated net-profit advantage from simply extending holding periods or switching to EURUSD. Good retrospective validation P&L does not prove market-regime selection will succeed on later market data.

## Research integrity

- Trade-label outcomes and quote futures were computed for each hypothetical 10/15/30-minute buy and sell but **never added to model features**; fitting uses train-year records only.
- 2024 validation only determines switching candidates; 2025–26 unseen backtest evaluated after selection. Those 2025–26 data are **now examined**; any tuning inspired by their P&L requires new independent dates.
- The multiple-expert/multiple-horizon search itself creates overfitting risk, even with a 2024-only selector.
- Historical Dukascopy quote and stated cost modeling cannot promise the user's broker fill quality or margin feasibility for a $150 account.
- Missing archival news calendars mean this is not the complete prospectively scheduled risk-filtered system.
- **No evidence of consistent profitability; no activation of live trading.**

## Next research direction

The strict rule correctly rejected weak evidence. More candidate models without independent predictive information are unlikely to solve it. Investigate a distinct feature that might have a plausible edge (published tick order-flow **trades**, cross-venue prices, regime-specific macro event analysis with as-of-time calendar, or genuinely measured broker microstructure). Alternatively, test a much larger 10–30m sample *before* considering thresholds and validate on dates never inspected. Keep no-live-order guard and read-only forward paper workflow unchanged.
