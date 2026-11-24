# Zero time cooldown versus current 1h ETH/SOL baseline

Historical simulated Kraken perpetual futures with 1x exposure and $150 separately restarted account per scenario, **no real orders**.

Test four combinations of 3h after-trade wait and 24h stop-loss pause. Existing technical votes, completed BTC regime, actual lagged OI/funding, ATR sizing/stops, one-position cap and **7-day 4% MaxDrawdown guard** are retained. This is an isolated change to timed restrictions only.

| Coin | Temporal restriction | Natural trades | Trades/week | Jan–Nov return | Higher-cost return | Early stress net USD | Later stress net USD | Max loss streak | Higher-fee DD | Forced end USD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ETH | Baseline | 86 | 1.85 | +11.649% | +6.780% | -0.948 | +10.399 | 6 | 4.465% | +0.000 |
| ETH | NoPostTradeWait | 88 | 1.89 | +12.486% | +7.894% | +0.437 | +10.617 | 6 | 4.289% | +0.000 |
| ETH | NoLossPause | 93 | 2.00 | +4.681% | -0.172% | -2.104 | +9.933 | 22 | 6.899% | +0.000 |
| ETH | NoTimeLocks | 94 | 2.02 | +4.474% | +7.930% | +2.543 | +9.420 | 22 | 4.866% | +0.000 |
| SOL | Baseline | 68 | 1.46 | +3.337% | +0.844% | -3.996 | +4.848 | 9 | 6.439% | +0.000 |
| SOL | NoPostTradeWait | 68 | 1.46 | +3.337% | +0.844% | -3.996 | +4.848 | 9 | 6.439% | +0.000 |
| SOL | NoLossPause | 80 | 1.72 | -2.201% | -5.199% | -7.792 | -0.580 | 7 | 11.464% | +0.000 |
| SOL | NoTimeLocks | 80 | 1.72 | -1.808% | -4.426% | -6.665 | -0.445 | 7 | 10.721% | +0.000 |

## Historical candidate screens
Increases naturally completed trades and net profit at both 0.05% and 0.15% per-side cost, both restarted historical segments positive under stress, higher-cost backtester drawdown <=6%, no worsening longest losing streak, no terminal force-exit profit dependency >$0.10.

- ETH NoPostTradeWait: +2 trades, +1.256 USD normal, +1.671 USD stressed

## Distinctions
Even with zero cooldown, 1h signals can be absent for most hours. No model can open a second concurrent position, and a seven-day maximum drawdown guard still limits losing periods. This experiment does NOT remove the actual forward paper observer's 2% daily, 4% weekly or 6% peak locks.

All data are retrospective; never interpret the per-day average as daily real profit. The existing 1h paper observer and 12h comparison bot remain unchanged unless separately validated.
