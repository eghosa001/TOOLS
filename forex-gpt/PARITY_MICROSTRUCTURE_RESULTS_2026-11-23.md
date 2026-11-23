# Forex microstructure study: cross-rate price discovery, 23 November 2026

## Outcome

**No validated, consistently profitable trading signal.** Independent 2025–26 held-out backtest found zero qualified regime-selective models. Raw triangular price-discrepancy and cross-pair lead signals were nonprofitable on executed shadow trades after estimated costs.

## Verified evidence

- [Successful 120-day authentic Dukascopy tick-data and historical replay](https://github.com/eghosa001/TOOLS/actions/runs/45159054376).
- [Complete stored sample-date inventory, hashes, all 2024 selection candidates, final shadow trades, net returns, and rejection/selection statistics](https://github.com/eghosa001/TOOLS/actions/runs/45159054376/artifacts/14809538974).
- Code: [causal downloader](./parity_microstructure_fetch.cjs), [regime-specific parity signal + trained net-return predictors](./parity_microstructure_backtest.py), [six additional quote-causality/cost regression tests](./test_parity_microstructure.py), [12 existing tick research tests](./test_tick_paper_replay.py).
- GitHub runner finished all steps successfully and **all 18 automated unit tests passed**.

## Research design fixed before test

12 disjoint, new two-week windows (10 weekdays each) distributed across 2021–2026 = 120 historical trading days. Historical tick downloads succeeded for all **120/120** days, missing raw market days **zero**.

Only a 07:00–09:00 UTC session is downloaded for GBPUSD, EURUSD, EURGBP. Decisions are sampled every **10 seconds** from 07:15–08:45 UTC, not every tick. All three currency quotes at the decision time and at the 5-second and 30-second lookbacks must be <1.2 seconds old. Any crossed, stale, or high-spread quotes, or delayed GBP/USD entry, are rejected.

**Sample partition with *eligible as-of signal opportunities***:

| Chronological stage | Trading days with downloaded data | Days with any eligible signal | Eligible decision rows |
| --- | ---: | ---: | ---: |
| Training 2021–2023 | 60 | 59 | 4,705 |
| Specialist validation 2024 | 20 | 19 | 295 |
| Held-out evaluation 2025–2026 | 40 | 40 | 1,317 |

Only a small fraction of theoretical opportunities survive high-quality simultaneous quote freshness checks; importantly, raw quote availability is not equivalent to a trade opportunity.

The independent predictor uses the **bid/ask correct synthetic GBPUSD** from EURUSD / EURGBP:

- synthetic bid = EURUSD_bid / EURGBP_ask.
- synthetic ask = EURUSD_ask / EURGBP_bid.
- gap buy GBPUSD = synthetic bid - direct GBPUSD ask.
- gap sell GBPUSD = direct GBPUSD bid - synthetic ask.

Predictions are based on historical, causally aligned quote snapshots. Three regimes are defined by an observed cross-pair 5s lead burst, large synthetic price gap, or otherwise normal pricing. Five specialists compete: raw parity midpoint deviation, executable-quote synthetic gap, quote cross-pair leading divergence, and two trained models estimating **net returns after all simulated trading costs**, Ridge and LightGBM.

The two ML models are fitted exclusively using 2021–23 outcomes. 2024 selects the best expert, threshold and 10/30/120s horizon by regime. The exploratory selection requires at least 15 trades and a positive validation net; strict selection requires 30 trades, both 2024 fortnights profitable and mean net P&L minus one standard error >0. Neither selection rule looked at 2025–26 outcomes.

**2024 selection: none passed, in any of the three regimes.** A positive +$0.15 result on two signals did not reach the minimum 15 trades and was correctly rejected. The relevant 2024 research set had only 295 fully fresh triple-quote decision opportunities, so broader statistical conclusions are unwarranted.

## Final held-out GBP/USD results, 2025–26, 40 independent trading days

| Frozen policy | Hypothetical trades | Winners | Net USD |
| --- | ---: | ---: | ---: |
| Regime-selective exploratory | 0 | 0 | $0.00 |
| Regime-selective strict | 0 | 0 | $0.00 |
| Parity midpoint gap 0.5 pip, 10s | 3 | 1 | **−$0.29** |
| Parity midpoint gap 0.5 pip, 30s | 2 | 1 | **−$0.14** |
| Parity midpoint gap 0.5 pip, 120s | 2 | 0 | **−$1.10** |
| Executable synthetic-triangle quote gap >0 pip, 10s/30s/120s | 0 | 0 | $0.00 |
| 5-second cross-pair lead >0.5 pip, 10s | 13 | 1 | **−$1.87** |
| 5-second cross-pair lead >0.5 pip, 30s | 13 | 3 | **−$1.80** |
| 5-second cross-pair lead >0.5 pip, 120s | 12 | 3 | **−$1.41** |
| Fixed Ridge expected net profit >$0.05, 10s/30s/120s | 0 | 0 | $0.00 |

Each model was fitted/selected with 2025–26 excluded. Small theoretical quote gaps do not justify live cross-venue arbitrage claims. **Zero trades ≠ profitable strategy.** All reported results are net of actual Dukascopy bid/ask quote prices plus $0.06 hypothetical roundtrip commission and 0.2 pip extra roundtrip slippage, on a hypothetical 1,000 GBP position, with illustrative $150 balance reset **per day**, no overlaps and a $3 daily net stop-pause.

**Training labels:** average hypothetical net buy/sell returns were about −$0.17 per 10, 30, 120 seconds; both directions generally began from negative expected value after trading costs.

## Critical execution limitations

1. The pairs update asynchronously, even at the same broker feed; there is no assured three-leg simultaneous firm executable market.
2. The arbitrary 1.2-second max quote age and 0.5–4-second GBPUSD order delay do not reproduce any named broker's execution.
3. Dukascopy quotes are top-of-book; last-look reject decisions, liquidity, market impact, broker-specific live spreads and available margin for the illustrative $150 account are **not verified**.
4. Actual executed order flow and transaction timestamps from independent venue liquidity are absent; quote-side volume should not be misrepresented as true trade flow.
5. Contemporaneous historical economic announcement archives are not verified; the historical event blackout is **not applied**. The existing future-dated safety research workflow is separate and unchanged.
6. The validation sample after strict quote freshness is small (295 decisions over 20 days); many candidate thresholds/horizons are screened, so apparent validation positives are at high risk of false discovery.
7. No live broker orders were programmed, sent, or approved.

## Research consequence

This new hypothesis had a plausible market-microstructure basis, but the observed results **failed** to establish a tradable edge. Further variations of the same indicator on the inspected 2025–26 data cannot count as independent proof. Do not reactivate trading on this basis.

**Better next evidence:** actual interdealer or exchange-traded FX futures transaction-level executed prints/order-book changes with broker-specific marketability, slippage, rejections and a real as-of macro-event calendar; or prospective multi-venue quote data with arrival timestamps and paper broker fills. Only after that should a new, truly untouched chronological holdout be used to evaluate whether predictive skill survives costs.
