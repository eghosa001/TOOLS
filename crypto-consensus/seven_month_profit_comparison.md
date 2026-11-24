# Seven-month matched ETH futures profit audit: 1h versus 12h

**Historical simulated results; no real earnings or orders.**

Dates: **2026-05-01 00:00 UTC through 2026-11-22 23:59 UTC** (November 23 exclusive), seven named calendar months, November partial. Total **206 calendar days**.

Every strategy and cost scenario starts with its OWN **$150** paper account, 1x maximum leverage; both use actual Kraken historical perpetual futures data and modeled fees/funding. Historical research already viewed, not new forward test. 12h original has seven-day loss pause; improved 1h uses 24-hour loss pause, BTC completed macro gate and official Kraken futures funding/OI veto. Their differences are not solely due to candle duration.

## Total profit and average per calendar day

| Strategy | Fee / side | Seven-month return* | Profit USD* | Average USD/day* | Natural closed trades | Backtester max DD | Forced terminal profit USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 12h_original | 0.05% | +11.352% | +17.028 | +0.0827 | 7 | 0.100% | +5.138 |
| 12h_original | 0.15% | +11.134% | +16.701 | +0.0811 | 7 | 0.127% | +5.099 |
| 1h_unfiltered | 0.05% | -5.824% | -8.736 | -0.0424 | 82 | 8.390% | +0.000 |
| 1h_unfiltered | 0.15% | -5.736% | -8.603 | -0.0418 | 79 | 7.185% | +0.000 |
| 1h_btc_regime | 0.05% | +8.378% | +12.567 | +0.0610 | 56 | 3.504% | +0.000 |
| 1h_btc_regime | 0.15% | +5.695% | +8.542 | +0.0415 | 52 | 4.494% | +0.000 |
| 1h_btc_funding_oi | 0.05% | +8.825% | +13.238 | +0.0643 | 56 | 3.504% | +0.000 |
| 1h_btc_funding_oi | 0.15% | +6.105% | +9.158 | +0.0445 | 52 | 4.494% | +0.000 |

*Includes a modeled artificial closing of any position at the end of the test. Dividing by 206 days does NOT mean the bot earned that amount every day.

## Main comparison: improved 1h minus original 12h

| Fee / side | Difference in 7mo profit USD* | Difference in return percentage points* | Difference per calendar day USD* | Natural 1h/12h closed trades | Natural profitable 1h/12h months |
|---|---:|---:|---:|---:|---:|
| 0.05% | -3.790 | -2.526 | -0.0184 | 56/7 | 4/5 |
| 0.15% | -7.543 | -5.029 | -0.0366 | 52/7 | 4/5 |

## Month-by-month naturally closed-trade P&L (USD; NOT equity return)

Because a trade can remain open over several days or months, these rows record P&L **only when a trade closes naturally**. They ignore interim unrealized gains/losses, and completely exclude end-boundary forced closures. Thus the totals may differ from the headline backtest account return.

| Calendar month | 1h normal | 12h normal | 1h higher fee | 12h higher fee |
|---|---:|---:|---:|---:|
| 2026-05 | -0.093 | -0.149 | -0.811 | -0.191 |
| 2026-06 | +2.567 | +4.187 | +1.927 | +4.148 |
| 2026-07 | -2.263 | -0.043 | -3.069 | -0.074 |
| 2026-08 | +5.351 | +0.384 | +4.939 | +0.347 |
| 2026-09 | +2.179 | +5.607 | +1.746 | +5.552 |
| 2026-10 | -2.381 | +1.050 | -3.007 | +1.010 |
| 2026-11 | +7.879 | +0.854 | +7.432 | +0.810 |

## How frequently did closed trades actually make money?

| Strategy/cost | Days with profitable natural closes | Days with losing natural closes | Days with no natural close | Best profitable natural close-day USD | Worst natural close-day USD | Largest winning natural trade USD |
|---|---:|---:|---:|---:|---:|---:|
| 1h_btc_funding_oi normal | 19 | 36 | 151 | +8.062 | -1.065 | +8.062 |
| 1h_btc_funding_oi stress | 16 | 36 | 154 | +7.985 | -1.141 | +7.985 |
| 12h_original normal | 5 | 2 | 199 | +5.607 | -0.149 | +5.607 |
| 12h_original stress | 5 | 2 | 199 | +5.552 | -0.191 | +5.552 |

## Caveats that change the interpretation

The 12h strategy can go long intervals without closing a trade, and one artificial terminal gain can dominate its final reported profit. An hourly strategy can close more frequently but lose more often and incur more fees. The candidate was selected using historical 2026 data, so comparing it on those same months is NOT confirmation from unseen future observations.

No rigorous claim of statistically **significant** additional profit can be made without independent forward trading evidence. This file measures dollar magnitude and realized-close consistency, not guaranteed daily income.

See the full JSON for every day, every month, winning/loss streaks, forced exits and average closed-trade frequency. The existing hourly prospective paper account remains independent, with no historical profits credited.
