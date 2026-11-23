# ETH Futures: four independent-information model trials (2026-11-23)

## Reproducible measurements

**Status: research only; original GuardedConsensusETH is not replaced.**
No exchange account, live API credentials, live orders, added leverage,
parameter search, AI hallucinated signals or retroactive ChatGPT forecasts.

15 completed official Freqtrade historical scenario backtests, all successful:
https://github.com/eghosa001/TOOLS/actions/runs/45219939171

| Model | Jan-Jun USD | Jul-Nov USD | Full Jan-Nov USD | Full return | Wins | Losses | Simulated maximum drawdown |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original protected 10/10 | +4.830249 | +11.044075 | +16.563049 | +11.0420% | 7 | 8 | 2.2663% |
| BTC price regime | +2.921540 | +8.272990 | +11.369423 | +7.5796% | 5 | 10 | 2.9590% |
| **Funding + actual Kraken open interest** | **+6.047436** | **+11.044075** | **+17.780237** | **+11.8535%** | **7** | **7** | **1.4760%** |
| Volatility breakout | -0.899767 | +5.905562 | +4.050192 | +2.7001% | 3 | 11 | 3.3778% |
| Causal rolling ridge machine learning | +5.336666 | +8.807597 | +2.241477 | +1.4943% | 3 | 10 | 2.2735% |

All numbers use a $150 simulated initial wallet in Kraken Futures ETH/USD,
one maximum open position, 1x leverage, original 1% modeled ATR-stop
risk sizing, original crash guard, original cooldown and equity protections
where applicable, 0.05% per-side simulated market fee and downloaded real
Kraken Futures hourly mark/funding and ETH/BTC 12-hour candles.

The Jan-Jun and Jul-Nov runs each reset to $150 to compare independent
scenarios. The **full Jan-Nov run is one continuous wallet without a reset**.

### What did the favorable funding/open-interest candidate change?

It stopped the unprofitable baseline short opened 2026-03-28 00:00 UTC,
closed 2026-04-01 00:00 UTC at a modeled -$1.163113.

It also shifted the April 8 losing entry to an earlier time, improving that
one trade from -$0.134726 to -$0.080651. Full net benefit +$1.217188
(+0.8115 percentage points of the initial $150), with 8 -> 7
losing closes and 2.2663% -> 1.4760% closed-account modeled DD.

**The improvement is entirely in January-June.** July-November profit is
identical to the original: +$11.044075. The original result, and this improved
one, both contain **+$5.138327 from an end-of-backtest forced close**,
not a normal exit signal. Profit excluding that forced terminal close is
smaller than the headline figure, and must not be described as an organic
realized strategy exit.

The funding/OI version passed the preregistered research *screen*, but
there is NOT enough evidence to promote it as a real-money bot:
- one avoided bad trade is a small sample;
- the previously studied July-November interval is NOT genuinely blind OOS;
- no measurable advantage in that later interval;
- simulated stop execution/drawdown can differ from actual futures;
- multiple model trials create chance-positive results.

### Actual positioning-data provenance

The research fetched **2,000 exchange-origin open-interest four-hour
OHLC records** (December 25, 2025 through November 23, 2026) from:
https://futures.kraken.com/api/charts/v1/analytics/PF_ETHUSD/open-interest?interval=14400

Source download SHA256:
4c72c0a7a3cd6bf0ac88c7a94988abee6648b2015e975976073cde03e90a0cf8

Only the official historical OI **close** for a four-hour block is used,
with availability delayed to the end of the block. Hourly funding events
are also delayed one hour. Inputs are merged backward in time to completed
ETH trading candles; signals are never assigned future observations. In
case of missing/stale history, the respective entry filter refuses
undocumented trades. Real BTC futures data (not ETH-inferred proxy) were
downloaded and coverage checked.

The rolling ML candidate was re-trained on prior feature/target pairs only,
with one-candle training-label embargo, rolling train-only normalization and
regularization. Unit tests verify outputs do not change if future candles
are added.

Pinned experiment Freqtrade image digest:
freqtradeorg/freqtrade@sha256:bd52747f04d0472ea326480e4800dbaf9dda0313b04e511fe518d04e108c817b

### Decision

**Keep GuardedConsensusETH unchanged.**
Keep ResearchFundingOpenInterestETH available as a separate research
candidate for a fresh forward paper test, rather than adding it to ten-vote
production now. The BTC, breakout and ML variations failed to demonstrate
a net advantage and should not become permanent ensemble votes.

Raw Freqtrade trade ZIPs, log files and report:
https://github.com/eghosa001/TOOLS/actions/runs/45219939171

This is a model-selection experiment, not financial advice or guaranteed
loss control.
