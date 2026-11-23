# ETH loss-week repair research — November 23, 2026

This research tests interventions against **one fixed, original** protected strategy,
`GuardedConsensusETH` in `eghosa001/TOOLS`. All tests were keyless historical
simulations on actual Kraken Futures ETH/USD data, using 12-hour completed candles,
mark/funding downloads, a $150 model wallet, 1x leverage and fees of 0.05% per side.

**Do not deploy any experimental variation automatically.** None met the
predeclared cross-period safety and profit-retention gates. Existing historical
returns must not be presented as real trading profits.

## Finding from exact 15 exported full-period trades

- Original Jan 1 – Nov 22 historical period: **+$16.563 (11.042%)** and
  **2.2663% max reported drawdown**, 7 winners and 8 losers.
- All eight losers were exited as `trailing_stop_loss`. Five were long positions
  and three were shorts. The largest net loss was **-$1.163113**, on a short
  opened March 28 and closed April 1 (trade return about -8.35% of stake;
  not -8.35% of the full $150 account).
- Losses were concentrated January – July, with a sequence of five consecutive
  failed trades after the profitable February 25 exit.
- **One positive +$5.138327 at Nov 23 was a forced backtest-end exit, not a
  genuine strategy-generated exit.** It must not be mistaken for a verified
  profit-taking signal.
- The exported Freqtrade `_wallet.feather` data reflect wallet balance,
  *not a continuously marked futures position equity curve*. At the last
  observed candle the recorded USD wallet was $161.42472148, while the final
  backtest closed an open position to reach $166.56304892. Do **not**
  calculate marked weekly profit or risk from this wallet data alone.

## Exact eight losing closes in the full-period baseline

| Position entry UTC | Side | Closed UTC | Net USD |
|---|---|---|---:|
| Jan 5 | Long | Jan 8 | -0.351137 |
| Jan 15 | Long | Jan 19 | -1.126624 |
| Feb 27 | Short | Mar 2 | -0.846898 |
| Mar 16 | Long | Mar 19 | -0.253493 |
| Mar 28 | Short | Apr 1 | -1.163113 |
| Apr 8 | Long | Apr 29 | -0.134726 |
| May 7 | Long | May 13 | -1.092185 |
| Jun 19 | Short | Jul 2 | -0.043254 |

## Five explicitly tested alternatives

| Model | Train Jan–Jun P&L | Held-out Jul–Nov P&L | Full P&L | Full losing trades | Full max drawdown |
|---|---:|---:|---:|---:|---:|
| Original protected | +$4.830 | +$11.044 | +$16.563 | 8 | 2.2663% |
| 2 completed 12h votes | +$4.117 | +$11.020 | +$13.963 | 7 | 2.2192% |
| EMA100 trend regime | +$3.371 | +$11.635 | +$15.695 | 9 | 3.0369% |
| Combined vote and trend | +$3.579 | +$11.541 | +$13.899 | 8 | 2.5687% |
| 2.5% nominal emergency stop | +$4.830 | +$11.044 | +$16.563 | 8 | 2.2663% |
| Early break-even trailing | +$5.098 | +$2.294 | +$7.649 | 15 | 2.3369% |

The **two-candle vote filter** eliminated one historical loser in the full
window and one loss in the separately restarted held-out window, but reduced
full-period profit by $2.6003. The combination of filters and narrower nominal
stop did not meet the evidence thresholds. Early break-even created many more
small trades and additional losses. A mechanically tighter stop loss cannot
guarantee smaller real market losses in a gap.

## Why no changes were promoted

A risk-control improvement must be defensible across training, later held-out
market conditions and one continuous full historical account. It must not
merely erase an observed losing trade with hindsight. All five candidates
were predeclared before the comparative run; none passed every gate.

**Do not re-use the same Jul–Nov data for repeated cherry-picked thresholds
and call it fresh out-of-sample validation.** Further experiments would be
exploratory, and would require new future-forward evidence or a genuinely
independent market.

## Audit links

- Completed independent 18-run comparison:
  https://github.com/eghosa001/TOOLS/actions/runs/45211172759
- Original continuous baseline:
  https://github.com/eghosa001/TOOLS/actions/runs/45207822271
- Freqtrade wallet data inspection:
  https://github.com/eghosa001/TOOLS/actions/runs/45212582287

Risk controls already on main: 1x maximum nominal exposure, 1% modeled
per-position stop-distance risk, one position at a time, 4% emergency
price stop, ETH crash-entry filter, seven-day break after losses, 2% daily,
4% weekly and 6% peak **observed** risk limits in the discrete forward
observer. These are not guaranteed real-money loss ceilings.

**Research conclusion:** The existing protected model's trailing-stop losses
were small in dollars and were outweighed by fewer larger winners, but the
sample is too small to establish robust future profitability. No experimental
signal alteration yet offers a demonstrated net advantage.
