# High-frequency crypto research — 1h, 15m and 5m

Real historical Kraken futures candles and hourly mark/funding data; all returns are Freqtrade **simulations**, $150 initial independent wallets, maximum 1x notional, original ATR stop and position sizing.

Dates: Aug 1–Nov 22, 2026 (114 calendar days). This report compares 8-of-10 with 9-of-10 consensus, original strict seven-day loss lock with an exploratory 24-hour loss lock, and extra trading cost stress.

The original 12h protected rule is rerun on the **same calendar window**; its prior whole-year +11% result is NOT used as a false comparison.

## Every researched candidate — base 0.05% fee per side

| Coin | TF | Votes | Loss cooldown | Trades | Trades/day | Net return | Max DD | W/L | Forced exit USD |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| ETH | 12h | 8/10 | strict | 4 | 0.035 | +8.091% | 0.000% | 4/0 | +4.624 |
| SOL | 12h | 8/10 | strict | 6 | 0.053 | +6.652% | 0.777% | 4/2 | +7.136 |
| BTC | 12h | 8/10 | strict | 6 | 0.053 | +0.775% | 1.789% | 2/4 | +3.845 |
| ETH | 1h | 8/10 | strict | 17 | 0.149 | -2.015% | 2.400% | 4/13 | +0.000 |
| ETH | 1h | 8/10 | active | 42 | 0.368 | -5.933% | 6.716% | 6/36 | +0.000 |
| ETH | 1h | 9/10 | strict | 16 | 0.140 | -1.761% | 2.240% | 5/11 | +0.000 |
| ETH | 1h | 9/10 | active | 35 | 0.307 | +1.760% | 4.652% | 9/26 | +0.000 |
| ETH | 15m | 8/10 | strict | 16 | 0.140 | -2.344% | 2.344% | 1/15 | +0.000 |
| ETH | 15m | 8/10 | active | 88 | 0.772 | -0.066% | 2.991% | 22/66 | +0.000 |
| ETH | 15m | 9/10 | strict | 17 | 0.149 | -1.194% | 1.354% | 3/14 | +0.000 |
| ETH | 15m | 9/10 | active | 69 | 0.605 | -1.075% | 5.462% | 13/56 | +0.000 |
| ETH | 5m | 8/10 | strict | 17 | 0.149 | -0.511% | 0.514% | 2/15 | +0.000 |
| ETH | 5m | 8/10 | active | 125 | 1.097 | -2.280% | 2.280% | 36/89 | +0.000 |
| ETH | 5m | 9/10 | strict | 20 | 0.175 | -0.062% | 0.378% | 6/14 | +0.000 |
| ETH | 5m | 9/10 | active | 113 | 0.991 | -1.241% | 1.793% | 28/85 | +0.000 |
| SOL | 1h | 8/10 | strict | 19 | 0.167 | +3.847% | 1.389% | 7/12 | +0.000 |
| SOL | 1h | 8/10 | active | 46 | 0.404 | +3.320% | 1.924% | 17/29 | +0.000 |
| SOL | 1h | 9/10 | strict | 18 | 0.158 | -1.719% | 2.662% | 6/12 | +0.000 |
| SOL | 1h | 9/10 | active | 40 | 0.351 | +6.322% | 2.544% | 13/27 | +0.000 |
| SOL | 15m | 8/10 | strict | 22 | 0.193 | +1.169% | 0.861% | 9/13 | +0.000 |
| SOL | 15m | 8/10 | active | 76 | 0.667 | +0.043% | 4.109% | 24/52 | +0.000 |
| SOL | 15m | 9/10 | strict | 20 | 0.175 | +0.369% | 0.826% | 6/14 | +0.000 |
| SOL | 15m | 9/10 | active | 79 | 0.693 | -0.989% | 3.786% | 24/55 | +0.000 |
| SOL | 5m | 8/10 | strict | 18 | 0.158 | -0.635% | 0.899% | 3/15 | +0.000 |
| SOL | 5m | 8/10 | active | 105 | 0.921 | -3.339% | 3.639% | 25/80 | +0.000 |
| SOL | 5m | 9/10 | strict | 19 | 0.167 | -0.735% | 1.038% | 4/15 | +0.000 |
| SOL | 5m | 9/10 | active | 100 | 0.877 | -0.485% | 3.137% | 25/75 | +0.000 |
| BTC | 1h | 8/10 | strict | 17 | 0.149 | -1.395% | 1.395% | 3/14 | +0.000 |
| BTC | 1h | 8/10 | active | 58 | 0.509 | +0.821% | 2.813% | 18/40 | +0.000 |
| BTC | 1h | 9/10 | strict | 16 | 0.140 | -1.265% | 1.476% | 4/12 | +0.000 |
| BTC | 1h | 9/10 | active | 44 | 0.386 | -0.325% | 2.740% | 11/33 | +0.000 |
| BTC | 15m | 8/10 | strict | 19 | 0.167 | -0.493% | 0.771% | 4/15 | +0.000 |
| BTC | 15m | 8/10 | active | 101 | 0.886 | -2.025% | 4.524% | 25/76 | +0.000 |
| BTC | 15m | 9/10 | strict | 19 | 0.167 | -0.993% | 1.035% | 5/14 | +0.000 |
| BTC | 15m | 9/10 | active | 94 | 0.825 | -3.746% | 4.769% | 22/72 | +0.000 |
| BTC | 5m | 8/10 | strict | 23 | 0.202 | -0.061% | 0.540% | 8/15 | +0.000 |
| BTC | 5m | 8/10 | active | 126 | 1.105 | -0.984% | 1.534% | 28/98 | +0.000 |
| BTC | 5m | 9/10 | strict | 16 | 0.140 | -1.123% | 1.123% | 0/16 | +0.000 |
| BTC | 5m | 9/10 | active | 120 | 1.053 | -4.428% | 4.428% | 26/94 | +0.000 |

## Extra cost stress for every faster active-mode candidate

0.05% per side original model; **0.15% per side** adverse model (fee plus hypothetical 0.10% slippage/spread per side). This is a **scenario**, not measured exchange slippage.

| Coin | TF | Votes | Base return | Stressed return | Stressed PnL change USD | Stressed trades |
|---|---|---:|---:|---:|---:|---:|
| ETH | 1h | 8 | -5.933% | -3.907% | +3.039 | 39 |
| ETH | 1h | 9 | +1.760% | +0.693% | -1.602 | 32 |
| ETH | 15m | 8 | -0.066% | -1.821% | -2.633 | 82 |
| ETH | 15m | 9 | -1.075% | -2.865% | -2.685 | 56 |
| ETH | 5m | 8 | -2.280% | -6.286% | -6.009 | 98 |
| ETH | 5m | 9 | -1.241% | -5.853% | -6.918 | 107 |
| SOL | 1h | 8 | +3.320% | -3.120% | -9.659 | 37 |
| SOL | 1h | 9 | +6.322% | +5.009% | -1.969 | 39 |
| SOL | 15m | 8 | +0.043% | -4.437% | -6.721 | 73 |
| SOL | 15m | 9 | -0.989% | -6.356% | -8.050 | 65 |
| SOL | 5m | 8 | -3.339% | -3.221% | +0.177 | 85 |
| SOL | 5m | 9 | -0.485% | -3.248% | -4.145 | 83 |
| BTC | 1h | 8 | +0.821% | -1.812% | -3.950 | 56 |
| BTC | 1h | 9 | -0.325% | -3.070% | -4.117 | 39 |
| BTC | 15m | 8 | -2.025% | -4.169% | -3.217 | 84 |
| BTC | 15m | 9 | -3.746% | -5.476% | -2.595 | 73 |
| BTC | 5m | 8 | -0.984% | -3.957% | -4.460 | 111 |
| BTC | 5m | 9 | -4.428% | -8.021% | -5.389 | 104 |

## Interpretation

At the same measured interval, a fast model is interesting only if **net return, downside and trade quality** remain defensible after conservative costs. More trades alone do not imply income.
A nine-vote threshold can reduce false signals but may also eliminate winning trades.
Strict mode retains original 7-day loss protection in actual minutes rather than accidentally turning 14 candles into 70 minutes at 5m. Active mode shortens the single-loss pause to 24 hours, while retaining the seven-day 4% modeled drawdown guard; that weaker loss cooldown must be evaluated separately.

Each row represents one independent test of a $150 wallet, not a tradeable combined crypto portfolio. Backtest max drawdown does not guarantee real stop execution, and the forward model's daily/weekly account breakers are NOT implemented here.

End-of-test forced exits are reported separately. A result showing no organic winning exit should not be considered proved profitable just because of an artificially closed final position.

No strategy, ChatGPT shadow vote, loss limits or live trading permissions have been changed.
