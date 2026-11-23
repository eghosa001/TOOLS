# ETH crash protection — paper-only experiment

**No real trading is enabled.** Freqtrade and the hourly CCXT observer in
this repository are not a brokerage. They do not place exchange stop orders.
The observable-loss thresholds below are **circuit-breaker targets**, not a
guaranteed maximum possible loss. Fast price gaps, downtime, slippage, missing
candle history, funding spikes, liquidation and market outages can exceed
the planned loss amounts. Forward hourly snapshots are too sparse to
guarantee intrahour risk control.

## Fixed, conservative risk schedule for $150 paper capital

- 1x (unlevered notional), no averaging down, no second position.
- Risk **at most 1%** of simulated account equity *at modeled initial
  stop distance* (ATR2.5 or 4% trade price, whichever is farther,
  plus a 0.2% modeled fill-cost budget). Starting account target $1.50.
  The position is skipped if rounded size is below the exchange minimum.
- Emergency position stop of **4% price movement** in protected Freqtrade
  strategy; ATR 2.5 trailing continues to tighten stops. Neither guarantees
  a fill at that price.
- Block new entries after a close-to-close ETH price shock of **8% in
  12 hours** or **15% in three days** (either direction), for at least
  48h in the 12h-strategy evaluation.
- In keyless forward observer: after 2% observed daily account loss, no
  new entries until next UTC day; after 4% weekly loss, seven-day pause;
  after 6% drawdown from observed equity peak, flatten the *simulated*
  position and latch a **manual-reset-only** lock. The observer's existing
  seven-day pause after any losing trade also remains.
- A severe shock also flattens an open simulated position at the next
  observation quote. This **cannot** protect against movements between
  hourly observations.

### Accurate backtest comparison
`GuardedConsensusETH.py` is a separate version of the existing Freqtrade
model, retaining all ten voting engines. It uses Freqtrade `StoplossGuard`,
`MaxDrawdown` and the 1% stake cap for reproducible historical testing.
**The daily/weekly/peak account-equity gates are not part of Freqtrade
backtesting**: those are in the keyless `forward_paper.py` observer only.
Freqtrade `MaxDrawdown` looks at completed trades, not continuously marked
open risk. Do not present Freqtrade results as fully testing those gates.

Use `.github/workflows/crypto-eth-crash-protection.yml` for the actual
Kraken Futures price crash-week, baseline/protected Freqtrade and causality
tests. Its short crash-week runs reset to $150 at each boundary and
force-close positions there; they are stress snapshots, not a continuous
week-by-week capital curve.

To have a **real exchange-side stop** rather than a paper simulation,
an owner must explicitly approve connecting a broker, verify stop types,
mark versus last prices, minimum-size handling, liquidation buffer, reduce
only, reject/fallback alerts, and an always-on execution host. Freqtrade
supports stoploss-on-exchange where a venue supports it, but no such live
activation has been authorized here.

References:
- https://www.freqtrade.io/en/stable/stoploss/
- https://www.freqtrade.io/en/latest/plugins/
