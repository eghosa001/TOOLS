# Frozen Forex tick-level consensus: forward-paper research (23 November 2026)

**Status:** Implemented, smoke-tested, scheduled for five new trading days; strictly **no live orders**. Source revision frozen for all forward research: [66f1b337b13206fb7d3017b1b7f604214b0c48ef](https://github.com/eghosa001/TOOLS/commit/66f1b337b13206fb7d3017b1b7f604214b0c48ef).

## Research evidence already completed

- [Successful audited run including preserved raw snapshots](https://github.com/eghosa001/TOOLS/actions/runs/45146994905)
- [Artifact: underlying quotes, economic events, each signal and hypothetical trade](https://github.com/eghosa001/TOOLS/actions/runs/45146994905/artifacts/14804227230)
- 12 offline safety/causality tests passed; separate actual-data tick replay completed.
- 2026-11-23 **07:00–09:00 UTC**, 32,477 historical tick quotes: GBPUSD **11,629**, EURUSD **10,791**, EURGBP **10,057**.
- Quoted GBPUSD, EURUSD, EURGBP bid/ask and available top-of-book quote volumes supplied by Dukascopy through pinned dukascopy-node 1.51.1. This is **NOT executed order-flow** data. Source: https://www.dukascopy-node.app/downloading-tick-data
- Weekly USD/GBP economic-event feed verified with 10 medium/high/holiday GBP/USD relevant events; source: https://nfs.faireconomy.media/ff_calendar_thisweek.json. Feed is third party, may revise events, and was snapshotted **after** this test session; it does not prove as-of-market-session news availability. Missing/stale feed -> no trades.

## Historical smoke-test results, $150 reset per scenario

| Voting rule | Hold | Hypothetical trades | Hypothetical net P&L |
| --- | --- | --- | --- |
| 6-of-10 + diverse-factor veto | 30 seconds | 2 | -$0.53 |
| 7-of-10 + diverse-factor veto | 30 seconds | 1 | -$0.34 |
| 8-of-10 + diverse-factor veto | 30 seconds | 0 | $0.00 |
| 6-of-10 + diverse-factor veto | 120 seconds | 2 | -$0.24 |
| 7-of-10 + diverse-factor veto | 120 seconds | 1 | -$0.08 |
| 8-of-10 + diverse-factor veto | 120 seconds | 0 | $0.00 |

Net after actual historical bid/ask spread and **modeled** $0.06 roundtrip commission and 0.2 pip extra roundtrip slippage for illustrative **1,000 GBP** position. 30s model has 2 pip target and 2 pip stop; 120s model has 4 pip target and 4 pip stop. Quote observations (not verified broker executions) are used for entry, stop and settlement. The $150 balance is not evidence that this position is margin-feasible with a specific broker. Less trading is not a measured predictive edge.

## Signals and safeguards

Ten exploratory vote rules: GBP 1m momentum, GBP 5m momentum, GBP range breakout, tick uptick ratio, available quote-volume imbalance, EURUSD 1m direction, inverse EURGBP 1m, inverse EURGBP 5m, GBP short-range price reversion, and tick activity burst. A signal can be **BUY**, **SELL**, or **NEUTRAL**. None is independently validated for profitability.

To prevent duplicate correlated votes being interpreted as independent proof, voting only proceeds when at least **three of four factor families** agree: GBP price, GBP tick/quoted liquidity, EURUSD context, EURGBP context. The ten-rule vote threshold remains 6, 7 or 8.

The replay also enforces: <=1.5 pip latest bid/ask spread; <=1.35 pip recent five-minute median; <=2-second old snapshot; entry at least 500ms after signal and no later than 4s; at least 70 ticks in the previous 5m; no overlapping trades; and simulated -$3 daily pause.

News restrictions: relevant USD/GBP **High** event => block 45 minutes before to 30 minutes after, **Medium** => 20 minutes before/after, relevant **Holiday** => block the UTC day. Invalid/unavailable/wrong-week calendar => fail closed. Important: **the calendar is a risk veto, not a source of directional predictions.**

**Live quality gate:** zero approved replacement engines. The earlier four-week study found no period with three acceptable validation-profitable candidates, so the gate remains closed; simulated votes are for research only. The code includes **no broker connection or order placement**. No 10-slot forced promotion.

## Frozen future five-day research window

The GitHub workflow [forex-tick-forward-paper.yml](../.github/workflows/forex-tick-forward-paper.yml) checks out the exact immutable Git SHA above so subsequent unrelated changes to main cannot silently alter the tested algorithm.

GitHub Actions scheduled runs after **17:37 UTC** on:
- Tuesday **24 November 2026**
- Wednesday **25 November 2026**
- Thursday **26 November 2026**
- Friday **27 November 2026**
- Monday **30 November 2026**

Each evaluates **07:00–09:00 UTC** historical tick quotes for that newly completed day, using only earlier ticks at each decision timestamp. Saves calendar snapshot, raw tick quotes, all signals, vetoes, simulated trade exits and P&L in a GitHub artifact (30-day retention). These are *frozen-rule, next-day/day-end historical replays*: code is fixed **before** the future market days but decisions are reconstructed **after** the session. They are **not live paper broker orders**, and news feeds may have changed before job time. Calendar or quote failures fail the run / fail closed rather than fabricating transactions.

Cron jobs can be delayed or skipped by GitHub. They only execute for the five selected dates in 2026 and weekdays. No profits are promised from unobserved future dates.

## Decision and next criterion

There is no established positive edge; first smoke test stayed net-negative or zero. Do not trade real $150. After the five future dates, first inspect the whole predeclared report—net after costs, number of trades, directional calibration, daily stop behavior, event omissions, volatility spikes and closed-trade drawdown. If the candidate pool still fails quality requirements, remain in SKIP and gather further distinct sources, with broker-specific fill/latency/margin data before considering a demo broker experiment.
