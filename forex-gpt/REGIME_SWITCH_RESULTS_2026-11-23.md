# Forex regime-specific profit prediction — actual multi-year experiment

Verified on 23 November 2026 using GitHub Actions, original user repository eghosa001/TOOLS. **Research simulation only. No broker orders.**

## Evidence
- [Successful complete GitHub Actions run](https://github.com/eghosa001/TOOLS/actions/runs/45153532834)
- [Full result artifact — 2024 validation candidate list, selected regimes, 2025–26 individual trades, all controls](https://github.com/eghosa001/TOOLS/actions/runs/45153532834/artifacts/14807926068)
- [Preregistered 150-day history fetcher](./regime_switch_fetch.cjs)
- [Trained profit prediction, market regime switching and held-out paper simulator](./regime_switch_backtest.py)
- [Fixed prior as-of-tick signals and cost model](./tick_paper_replay.py)

## Precommitted study
Draw three non-overlapping 2-week weekday blocks per year 2022–2026 using deterministic seed 260501, excluding the five earlier random test windows. 15 fortnights = **150 trading days** of actual Dukascopy historical GBPUSD/EURUSD/EURGBP top-of-book tick bid/ask and quoted volumes. **All 150 quote days loaded** with zero missing source dates (some illiquid dates had no eligible decisions). **Not full-market hours:** two hours 07:00–09:00 UTC per day, one trading decision opportunity per minute from 07:15–08:45, contingent on causal quotes and low spread.

Chronology:
- 2022–2023 train: **2,594 eligible decision rows**.
- 2024 validation & *model selection*: **705 eligible decision rows**.
- 2025–2026 completely held out from training and selection: **2,017 eligible decision rows over 60 trading days**.

Four mutually exclusive regimes based ONLY on historical 5-minute absolute returns and 5-minute quote range: volatile, trending, ranging, mixed.

Seven fixed price, mean-reversion, cross-market and tick/quote-volume specialists plus two trained ML families: LightGBM regressors and standardized Ridge regressors. The regression targets are realized hypothetical *net P&L after costs* for BUY and SELL for 30-, 120-, and 300-second horizons, not just next price direction. Models are fitted **only on 2022–23 training rows**. The 2024 period selects at most ONE (expert,horizon) per regime. No filling required.

Two predeclared selectors:
- Exploratory: require >=12 nonoverlapping validation trades and strictly positive validation P&L.
- Strong: require >=20 trades, at least 2 of 3 positive validation fortnights, and mean net P&L minus one standard error >0.
Both can select **no model** if no convincing evidence. 2025–26 was examined only after training and selection rules were fixed.

Historical quote-cost model: 1,000 GBP notional, illustration $150 capital, observed bid/ask spread at entry/exit; add $0.06 roundtrip commission + 0.2 pips additional modeled roundtrip slippage; entry next observed tick >=500 ms after decision, <4 s; one simulated position at a time; daily -$3 stop. Stops/targets: 2/2 pips for 30s, 4/4 pips for 120s, 6/6 pips for 300s. Per-test-day capital is reset to $150; aggregate P&L is the sum of independent daily tests, **not** a continuously compounded account.

## Validation selections

| Regime | Exploratory winner | Strong winner |
| --- | --- | --- |
| Volatile | None | None |
| Trending | None | None |
| Ranging | None | None |
| Mixed | None | None |

The 2024 validation period did **not** show positive net returns at sufficient trade counts for **any** specialist in any regime. Both selective policies therefore stayed in SKIP on held-out days.

## Strict held-out evaluation, 2025–26

| Evaluated policy | Trades | Total simulated net USD | Days with positive P&L |
| --- | ---: | ---: | ---: |
| Regime switching, exploratory selector | 0 | **$0.00** | 0 |
| Regime switching, strict selector | 0 | **$0.00** | 0 |
| 6-of-10, 30 seconds | 220 | **−$28.89** | 1 |
| 7-of-10, 30 seconds | 64 | **−$8.86** | 3 |
| 8-of-10, 30 seconds | 18 | **−$2.59** | 2 |
| 6-of-10, 120 seconds | 199 | **−$23.99** | 8 |
| 7-of-10, 120 seconds | 60 | **−$6.04** | 12 |
| 8-of-10, 120 seconds | 18 | **−$0.69** | 5 |
| 6-of-10, 300 seconds | 175 | **−$17.02** | 14 |
| 7-of-10, 300 seconds | 56 | **−$4.90** | 11 |
| 8-of-10, 300 seconds | 17 | **+$1.00** | 6 |

**Note:** 8-of-10 300s positive P&L is only 17 trades and 2 of 6 positive fortnights. Not a statistically established positive expected value, and selected for illustration AFTER seeing this table, so do not present as a prospective winner.

Single specialist universal 120-second tests also lost, e.g., trend momentum −$95.58/631 trades, range reversion −$78.53/454, cross market −$50.49/353 and tick quoted-volume imbalance −$7.79/54. Standalone LightGBM and Ridge took no trades because they did not predict sufficiently positive net P&L.

Average per hypothetical trade in **train** for both indiscriminate BUY and SELL targets was strongly negative after costs, about −$0.16 (30/120/300s). This highlights the spread + trading costs, and why direction forecasting alone is inadequate.

## What is established and what is NOT

Established:
1. Implemented regime-selective architecture and trained ML models estimating net expected trading profit.
2. All 150 historical quote dates retrieved; actual ticks and measured bid-ask spreads used.
3. Chronological training/validation/held-out separation maintained.
4. Gated regime switching consistently refused unvalidated configurations; it **did not demonstrate a positive trading edge**.
5. More frequent fixed voting lost money; 8/10 300s showed a negligible positive net outcome on too few trades for reliability.

NOT established:
- No demonstration of statistically robust or consistently profitable scalping.
- No actual broker fills, latency/impact measurements, broker spreads, leverage feasibility or account margin calculation.
- **No verified archived as-of-event economic-calendar feed:** event blackout was NOT applied in historical research; forward paper strategy retains its own fail-closed news filter.
- Top-of-book quoted volumes do NOT represent actual executed order flow, and votes/model experts share some underlying price features.
- 150 days means disjoint 2-hour sessions, not continuous 150 entire trading days or years.

## Concrete next research priority

Do not retroactively lower validation thresholds based on 2025–26 outcomes and claim a pristine test. Keep current conservative SKIP. To get more positive instances for model training, explore lower-spread executable markets, longer holding periods (10–30min), longer session coverage, robust macro-event archival data and broker-specific execution model, and compare against additional *new* dates. A real risk-free broker demo forward test is required before live trading.
