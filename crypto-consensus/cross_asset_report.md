# Five additional cryptocurrencies: protected strategy cross-market test

All results are simulated using public Kraken futures historical data, real hourly funding/mark and real 4h open interest. Modelled $150 starting capital and 1x max notional PER COIN, not a pooled multi-coin portfolio.
The original live-disabled ETH paper observer and strategy were not changed.

| Coin | Original return | Funding/OI return | OI trades W/L | Original DD | Funding/OI DD | Decision |
|---|---:|---:|---:|---:|---:|---|
| BTC | +4.603% | +3.405% | 8/11 | 2.083% | 2.107% | Reject for now |
| SOL | +7.032% | +7.894% | 7/10 | 2.985% | 3.004% | Research candidate |
| XRP | -2.527% | -2.404% | 5/14 | 4.649% | 4.512% | Reject for now |
| DOGE | +4.765% | +5.154% | 7/8 | 2.250% | 2.225% | Reject for now |
| ADA | -0.976% | -1.388% | 5/14 | 4.773% | 4.974% | Reject for now |

## Independent time windows (profit USD, each restarted at $150)

| Coin | Jan-Jun base | Jan-Jun funding/OI | Jul-Nov base | Jul-Nov funding/OI | Full base trades | Full funding/OI trades |
|---|---:|---:|---:|---:|---:|---:|
| BTC | +7.600 | +5.802 | -0.727 | -0.727 | 19 | 19 |
| SOL | +2.865 | +4.227 | +8.142 | +8.142 | 18 | 17 |
| XRP | -2.019 | -1.915 | -2.157 | -2.076 | 19 | 19 |
| DOGE | +1.054 | +2.358 | +4.444 | +3.706 | 16 | 15 |
| ADA | +0.156 | -0.494 | -2.085 | -2.085 | 19 | 19 |

## End-of-test forced trade close sensitivity

| Coin | Base forced close USD (count) | Funding/OI forced close USD (count) |
|---|---:|---:|
| BTC | +3.845 (1) | +3.845 (1) |
| SOL | +7.136 (1) | +7.136 (1) |
| XRP | +1.573 (1) | +1.573 (1) |
| DOGE | +4.630 (1) | +4.630 (1) |
| ADA | +3.864 (1) | +3.864 (1) |

## Interpreting these results

A research-screen pass requires positive development/later/full returns, at least 5 full trades, higher full-period return than that coin's original baseline, no higher drawdown (0.05 percentage-point tolerance), no more losing trades and no material late-period regression (>10 cents). These criteria are not permission to deploy.

A full-window result is a continuously modelled *single-coin* wallet; the first-half and later-half tests each start again at $150. Weekly close-based amounts in the JSON are NOT weekly equity returns. The historical last position may have been artificially force-closed. The same 10 indicators are correlated, so adding coins also introduces cross-coin crash correlation and exchange capacity risks.

**Production:** None of these five currencies have been switched on for trading, and no real orders or exchange credentials were used.
