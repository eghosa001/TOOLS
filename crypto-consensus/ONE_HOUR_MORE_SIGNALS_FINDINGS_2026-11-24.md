# ETH 1-hour frequency and profit research — November 24, 2026

**Decision: Do not loosen the working 8-of-10 ETH entry gate. More trades were
possible, but none of the twelve variants improved net profitability and
risk sufficiently to warrant promotion.**

Verified successfully completed Freqtrade workflow with 72 real-data simulations:
https://github.com/eghosa001/TOOLS/actions/runs/45362554203

## What was tested

The frozen forward-only ETH 1h paper observer and original protected ETH
12h paper strategy were not changed. This experiment added **research-only**
models with:

- 8/10 (exact previously verified control), 7/10 and 6/10 votes from the
  same original ten technical signals.
- Additional separate **24h volume-weighted price (VWAP)**, **20h Chaikin
  money-flow pressure (CMF)**, **6h ATR-normalized directional momentum**,
  **volume compared to the preceding 24h median**, and **20h
  previous-candle breakout**.
- A strictly completed BTC 12h EMA-based macro regime, with both the
  original strict trend/momentum veto and a less restrictive trend-only
  counterfactual.
- Official, independently published 4h Kraken Futures ETH open interest
  and hourly funding where applicable; stale or missing feeds fail
  closed. BTC and OI/funding signals have explicit past-only publication
  lags.
- The same Freqtrade one-position, <=1x leverage, ATR-based risk
  sizing/stop, 24-hour stoploss pause, 3-hour ordinary cooldown, and
  historical 7-day MaxDrawdown protection. No existing live protections
  were relaxed.

**12 entry families × three separate historical windows (January–July,
August–November, continuous January–November 2026) × two Freqtrade cost
scenarios (0.05%/side and adverse 0.15%/side) = 72 actual backtests**.

Each scenario starts a **separate historical $150 wallet**. The 326-day
continuous run is not the sum of the two restarted shorter wallets.
All results are historical, not forward returns or real earnings.
The candidate list and every screening threshold were fixed in code
before the simulation generated results.

## All 12 continuous-account results

| New one-hour candidate | Naturally closed trades | Normal return | Higher-cost return | Reported normal maximum drawdown | Longest losing streak |
|---|---:|---:|---:|---:|---:|
| **8/10 + strict BTC and OI (control)** | **86** | **+11.6487%** | **+6.7799%** | **3.5151%** | **6** |
| 7/10 + strict BTC and OI | 95 | +9.3006% | +2.2847% | 3.5008% | 9 |
| 6/10 + strict BTC and OI | 99 | +6.7330% | −2.0926% | 4.3138% | 9 |
| 7/10 + strict BTC only | 94 | +9.6497% | +1.1234% | 3.4762% | 9 |
| 6/10 + strict BTC only | 100 | +5.2620% | −1.7572% | 4.4883% | 9 |
| 7/10 + softer BTC and OI | **111** | +5.9967% | +0.3701% | 3.4121% | 10 |
| 7/10 + all four flow confirmations | 79 | +11.0141% | +1.1925% | 4.5317% | 7 |
| 6/10 + all four flow confirmations | 82 | +8.8689% | +0.0503% | 5.0465% | 7 |
| 7/10 OR flow-assisted 6/10 | 94 | +8.2302% | +0.7009% | 4.2777% | 9 |
| 7/10 OR volume breakout-assisted 5/10 | 96 | +8.8310% | +1.7785% | 3.5008% | 9 |
| 7/10 OR flow-assisted 6/10 + soft BTC | 109 | +7.1686% | +0.1058% | 4.3172% | 10 |
| 6/10 + flow confirmation + strict BTC only | 82 | +7.4909% | −0.7222% | 6.0459% | 10 |

**No candidate passed the predefined frequency-and-profit acceptance screen.**

The trade-count target required at least 25% more naturally completed
positions than the 86-trade incumbent, or >=108 trades. Two candidates
reached this threshold (111 and 109), but both had substantially lower
profits and worse losing streaks. Their independently re-executed
higher-fee returns were only **+0.3701%** and **+0.1058%** on $150
over 326 days.

The higher-frequency 111-trade soft-BTC candidate was profitable at
standard historical fees but **lost $2.179794** in the independently
restarted August–November higher-cost window. The 109-trade candidate
lost **$0.650015** in January–July at higher fees. The
strategy-selection screen requires both segments profitable under both
fee models; neither qualifies.

The 6/10 plain strategy gave 99 trades but its stressed full result
was **−2.0926%**. Filtering with flow reduced that count back to 82
and did not improve the net return versus the incumbent.

## Reproduction check

Before accepting new comparisons, the unchanged 8/10 reference was
reproduced **exactly** in the same historical configuration:
- January–July: +2.8818%, 58 trades
- August–November: +8.4978%, 29 trades
- Continuous January–November: +11.6487%, 86 trades
This matched the previously saved Q1h8Both24 Freqtrade reports.
The early and late restarted-wallett counts do **not** add to the
continuous-wallet count.

All newly added directional features are causal in synthetic
future-amendment regression tests and real futures market-data checks.
The trading research runs without any exchange secret or live API key.

## What the tests establish

The original indicator group is substantially correlated. Counting
more indicators, reducing the threshold, or adding more mandatory
technical confirmations cannot by itself create a reliable profit edge.
The extra 1h entries in these configurations were generally less
profitable after execution costs. In particular:

1. More frequent entry did not create reliable daily income.
2. Loosening 8/10 to 6/10 decreased returns and worsened fee sensitivity.
3. Adding flow gates by mandatory AND reduced opportunities, and
   optional OR pathways added opportunities with weaker profitability.
4. Softer macro restrictions increased trades but worsened streak risk.
5. The leading 8/10 historical result still missed prior stringent
   stress and future-forward tests. This is **not certification** of
   a profitable real strategy.

**The logical next research hypothesis is a truly distinct strategy
family, such as separately risk-budgeted sideways-market mean
reversion or an event/order-flow strategy with independently available
high-quality data, evaluated on newly arriving, prospectively captured
quotes and sufficiently long subsequent trades.** Repeating more
indicator variations on the same 2026 candles risks selecting noise.

## Account economics and next action

A historical **+11.6487% on $150 is +$17.473** over nearly eleven
months before the adverse-fee scenario cuts it to **+$10.170**.
Even a historically successful 20% total return on a $150 account
would yield only $30: more trade frequency does not solve the
starting-capital limitation. Seeking large daily income by increasing
leverage or stake risk can cause loss of the account and is not
approved by this study.

Keep the 8/10 combined model only as the current **forward-only
paper candidate**. Do not activate any of these experiments for real
orders, change the existing ETH 12h bot, or backfill historical
profits into the new prospective ledger.

Raw artifacts and all 72 Freqtrade ZIPs:
https://github.com/eghosa001/TOOLS/actions/runs/45362554203
