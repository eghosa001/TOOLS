# Four quality ETH models: same-cost, same-risk comparison

All results are historical paper simulations. Original 10-vote protected ETH bot unchanged.
Kraken futures candles, mark, actual hourly funding, official 4h open interest,
one initial 150 USD modeled wallet and 1x nominal exposure.

First half and later half are each restarted scenario tests. FULL is a single
uninterrupted Jan-Nov account. Later half was previously inspected in earlier
projects and cannot be presented as truly untouched out-of-sample evidence.

| Research model | Jan-Jun net USD | Jul-Nov net USD | Jan-Nov return | Full net USD | Trades | W/L | DD | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Original 10 indicators | +4.830 | +11.044 | +11.042% | +16.563 | 15 | 7/8 | 2.266% | Reference |
| BTC market regime | +2.922 | +8.273 | +7.580% | +11.369 | 15 | 5/10 | 2.959% | Fail |
| Actual funding + OI | +6.047 | +11.044 | +11.854% | +17.780 | 14 | 7/7 | 1.476% | Pass - research only |
| Volatility breakout | -0.900 | +5.906 | +2.700% | +4.050 | 14 | 3/11 | 3.378% | Fail |
| Time-ordered rolling ML | +5.337 | +8.808 | +1.494% | +2.241 | 13 | 3/10 | 2.273% | Fail |

## What was tested

- BTC regime: conservative one-candle-delayed BTC futures EMA100 and momentum.
- Derivatives crowding: genuine Kraken 4-hour open interest, prior published
  hourly funding, and changes in how crowded directional positioning is.
- Breakout: a completed 12-hour ETH bar breaking the prior three-day
  trading range while measured volatility is neither too quiet nor extreme.
- Rolling machine learning: expanding chronological predictions from
  240 past bars of price and volume, ridge regularization, standardization
  using training data only, and one-candle label embargo.

Every candidate filters entries from the SAME original ten-indicator
consensus and retains the existing protective position sizing and exits.

## All simulated losing closes (full Jan-Nov account)

### Original 10 indicators (8 losing trades)
- 2026-01-05 00:00:00+00:00 to 2026-01-08 00:00:00+00:00 long: -0.351 USD [trailing_stop_loss]
- 2026-01-15 12:00:00+00:00 to 2026-01-19 12:00:00+00:00 long: -1.127 USD [trailing_stop_loss]
- 2026-02-27 12:00:00+00:00 to 2026-03-02 12:00:00+00:00 short: -0.847 USD [trailing_stop_loss]
- 2026-03-16 00:00:00+00:00 to 2026-03-19 00:00:00+00:00 long: -0.253 USD [trailing_stop_loss]
- 2026-03-28 00:00:00+00:00 to 2026-04-01 00:00:00+00:00 short: -1.163 USD [trailing_stop_loss]
- 2026-04-08 12:00:00+00:00 to 2026-04-29 12:00:00+00:00 long: -0.135 USD [trailing_stop_loss]
- 2026-05-07 00:00:00+00:00 to 2026-05-13 12:00:00+00:00 long: -1.092 USD [trailing_stop_loss]
- 2026-06-19 00:00:00+00:00 to 2026-07-02 12:00:00+00:00 short: -0.043 USD [trailing_stop_loss]

### BTC market regime (10 losing trades)
- 2026-01-06 00:00:00+00:00 to 2026-01-08 00:00:00+00:00 long: -0.868 USD [trailing_stop_loss]
- 2026-01-15 12:00:00+00:00 to 2026-01-19 12:00:00+00:00 long: -1.127 USD [trailing_stop_loss]
- 2026-03-01 00:00:00+00:00 to 2026-03-04 12:00:00+00:00 short: -1.258 USD [trailing_stop_loss]
- 2026-03-16 12:00:00+00:00 to 2026-03-19 00:00:00+00:00 long: -0.894 USD [trailing_stop_loss]
- 2026-03-28 00:00:00+00:00 to 2026-04-01 00:00:00+00:00 short: -1.163 USD [trailing_stop_loss]
- 2026-04-08 12:00:00+00:00 to 2026-04-29 12:00:00+00:00 long: -0.135 USD [trailing_stop_loss]
- 2026-05-07 00:00:00+00:00 to 2026-05-13 12:00:00+00:00 long: -1.092 USD [trailing_stop_loss]
- 2026-06-19 00:00:00+00:00 to 2026-07-02 12:00:00+00:00 short: -0.043 USD [trailing_stop_loss]
- 2026-07-21 00:00:00+00:00 to 2026-08-01 12:00:00+00:00 long: -0.742 USD [trailing_stop_loss]
- 2026-10-25 00:00:00+00:00 to 2026-11-04 12:00:00+00:00 short: -0.278 USD [trailing_stop_loss]

### Actual funding + OI (7 losing trades)
- 2026-01-05 00:00:00+00:00 to 2026-01-08 00:00:00+00:00 long: -0.351 USD [trailing_stop_loss]
- 2026-01-15 12:00:00+00:00 to 2026-01-19 12:00:00+00:00 long: -1.127 USD [trailing_stop_loss]
- 2026-02-27 12:00:00+00:00 to 2026-03-02 12:00:00+00:00 short: -0.847 USD [trailing_stop_loss]
- 2026-03-16 00:00:00+00:00 to 2026-03-19 00:00:00+00:00 long: -0.253 USD [trailing_stop_loss]
- 2026-04-08 00:00:00+00:00 to 2026-04-29 12:00:00+00:00 long: -0.081 USD [trailing_stop_loss]
- 2026-05-07 00:00:00+00:00 to 2026-05-13 12:00:00+00:00 long: -1.092 USD [trailing_stop_loss]
- 2026-06-19 00:00:00+00:00 to 2026-07-02 12:00:00+00:00 short: -0.043 USD [trailing_stop_loss]

### Volatility breakout (11 losing trades)
- 2026-01-05 12:00:00+00:00 to 2026-01-08 00:00:00+00:00 long: -0.633 USD [trailing_stop_loss]
- 2026-01-21 00:00:00+00:00 to 2026-01-28 00:00:00+00:00 short: -0.575 USD [trailing_stop_loss]
- 2026-02-24 12:00:00+00:00 to 2026-02-25 12:00:00+00:00 short: -1.471 USD [stop_loss]
- 2026-03-16 12:00:00+00:00 to 2026-03-19 00:00:00+00:00 long: -0.894 USD [trailing_stop_loss]
- 2026-04-08 00:00:00+00:00 to 2026-04-29 12:00:00+00:00 long: -0.081 USD [trailing_stop_loss]
- 2026-05-11 00:00:00+00:00 to 2026-05-13 12:00:00+00:00 long: -1.413 USD [trailing_stop_loss]
- 2026-06-19 00:00:00+00:00 to 2026-07-02 12:00:00+00:00 short: -0.038 USD [trailing_stop_loss]
- 2026-07-15 00:00:00+00:00 to 2026-08-01 12:00:00+00:00 long: -0.560 USD [trailing_stop_loss]
- 2026-09-19 00:00:00+00:00 to 2026-10-07 00:00:00+00:00 long: -0.270 USD [trailing_stop_loss]
- 2026-10-15 12:00:00+00:00 to 2026-10-21 12:00:00+00:00 short: -1.294 USD [trailing_stop_loss]
- 2026-10-30 00:00:00+00:00 to 2026-11-04 12:00:00+00:00 short: -1.207 USD [trailing_stop_loss]

### Time-ordered rolling ML (10 losing trades)
- 2026-01-14 12:00:00+00:00 to 2026-01-20 00:00:00+00:00 long: -1.046 USD [trailing_stop_loss]
- 2026-02-27 12:00:00+00:00 to 2026-03-02 12:00:00+00:00 short: -0.847 USD [trailing_stop_loss]
- 2026-03-16 00:00:00+00:00 to 2026-03-19 00:00:00+00:00 long: -0.253 USD [trailing_stop_loss]
- 2026-03-28 00:00:00+00:00 to 2026-04-01 00:00:00+00:00 short: -1.163 USD [trailing_stop_loss]
- 2026-04-12 00:00:00+00:00 to 2026-04-29 12:00:00+00:00 long: -0.460 USD [trailing_stop_loss]
- 2026-05-09 12:00:00+00:00 to 2026-05-13 12:00:00+00:00 long: -0.801 USD [trailing_stop_loss]
- 2026-06-23 12:00:00+00:00 to 2026-07-02 12:00:00+00:00 short: -0.504 USD [trailing_stop_loss]
- 2026-07-19 00:00:00+00:00 to 2026-08-01 12:00:00+00:00 long: -0.302 USD [trailing_stop_loss]
- 2026-08-24 12:00:00+00:00 to 2026-09-15 12:00:00+00:00 long: -1.042 USD [trailing_stop_loss]
- 2026-09-23 00:00:00+00:00 to 2026-10-07 00:00:00+00:00 long: -1.021 USD [trailing_stop_loss]

## Evidence threshold

Predeclared before viewing these candidate outcomes: >=5 full trades,
positive first-half and later-half profit, >=80% training profit retained,
>=90% full profit retained, later-half profit at least baseline, fewer
full-period losing trades, no worse full, training or later drawdown
(0.05 percentage-point numerical tolerance).

Research-screen passes: Actual funding + OI.

No historical model is approved for automatic production promotion.
Fees and funding already affect reported Freqtrade net profits.
Forced exits, candle granularity, multiple testing and feed provenance
limit any interpretation as future exchange profitability.
