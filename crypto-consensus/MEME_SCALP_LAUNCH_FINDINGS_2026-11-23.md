# Meme momentum, 5m scalping, and futures listing probe — 2026-11-23

This research is paper-only. It does not alter the existing ETH consensus paper observer or switch on real orders.

## Reproducibility

- [First successful Kraken Futures experiment](https://github.com/eghosa001/TOOLS/actions/runs/45273724078)
- [Second successful experiment, including 2026 official futures listing checks](https://github.com/eghosa001/TOOLS/actions/runs/45274587314)
- Source: meme_launch_experiment.py and crypto-meme-research.yml on branch research/crypto-meme-launch-20261123.

The date range was October 15 through November 22, 2026. Five-minute Kraken Futures history was sourced from public exchange feeds; October 1 onward supplied indicator warmup. Starting capital was $150 per coin per scenario, each an independent mock wallet. The experiment reuses the established 10-indicator consensus code, crash filter and account risk entry gates. The simulator uses the next candle open after signal confirmation, 1x maximum modeled exposure, 1% modeled stake-at-stop risk, a 4% price stop, ATR trailing, and cooldowns. Fees were 0.05% per side base, 0.15% per side stressed. Exchange funding rate data were included with a last-price rather than exact settlement-mark approximation. This is a simplified separate simulator, not official Freqtrade, and it does not verify actual spread, order-book depth, latency, contract-size rounding, or exchange stop orders.

## Five-minute scalping

| Asset | Closed trades base | Base net return | Stress net return |
|---|---:|---:|---:|
| BTC | 48 | -0.1094% | -3.3810% |
| ETH | 41 | -1.0519% | -3.4520% |
| SOL | 38 | -0.1917% | -1.9301% |

All three lost at both cost levels, consistent with the earlier negative 114-day official Freqtrade 5m evidence.

## Meme-coin momentum

The strategy used 8/10 bullish votes, at least 2% one-hour price momentum and 1.8x median volume. Long-only.

| Asset | Closed trades base | Base net return | Stress net return |
|---|---:|---:|---:|
| DOGE | 5 | +0.3948% | +0.1562% |
| PEPE | 10 | +0.3505% | +0.0773% |
| WIF | 6 | -0.8910% | -1.1743% |
| TRUMP | 8 | +1.0973% | +0.7134% |
| FARTCOIN | 8 | +2.0854% | +1.6981% |
| PENGU | 9 | -0.0035% | -0.4313% |
| MUBARAK | 7 | -2.1414% | -2.4681% |

FARTCOIN was best in this sample, returning approximately $3.13 base / $2.55 stressed on its independent $150 mock wallet. Eight trades are insufficient for robust claims. Arithmetic sum of independent wallets was about +$1.34 base and -$2.14 stressed on a total of seven separately allocated $150 wallets ($1,050 total); this is NOT a portfolio backtest.

## New futures listing proxy — inconclusive

Using official Kraken 2026 futures contract listings, a predefined early launch test checked MEZO, OPN, PONS, RAVE, UNITAS, and VSN. Candidate entry rule: after 6 hourly closes, if the initial move exceeded 3%, enter at the following open, exit at -5% stop, +10% take profit, or after 24 hours; estimated 0.15% side costs. The public source data could not support any such result:

- MEZO, RAVE, UNITAS, VSN: matching active contract not available in the CCXT Kraken Futures market set.
- OPN, PONS: public historical launch-hour candles returned empty.

Thus **zero eligible validated launch backtests**, not a zero return or strategy failure. No profit or win rate is asserted. Official Kraken contract listings are not equivalent to first on-chain token launches. Any on-chain study must account for failed and delisted launches, token contract and pool permissions, liquidity, real transaction costs, rug pulls, holder distribution and wallet execution costs to avoid survivorship bias.

## Recommendation

Do not turn on live trading from these samples. Reject five-minute scalping as presently specified; meme momentum is exploratory with negative aggregate stressed results. Launch strategy profitability remains unknown. Retain the existing ETH paper trading and controls unchanged. Next valid work is an independently sourced, point-in-time on-chain launch dataset and fresh forward-only paper test, rather than claiming these historical outliers will persist.
