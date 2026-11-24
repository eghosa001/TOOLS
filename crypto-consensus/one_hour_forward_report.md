# Forward ETH 1-hour paper candidate: BTC + genuine funding/open interest

**Genuinely prospective, keyless and no real orders.** The current 12h paper bot remains separate and unchanged. This report NEVER combines historical backtest profits into forward profitability.

| Metric | Latest observed value |
|---|---:|
| Simulated opening cash | \$150.00 |
| Observed simulated equity | \$150.000 |
| Observed forward paper return | +0.0000% |
| Closed forward paper trades | 0 |
| Winners / losers | 0 / 0 |
| Prospective hourly observations | 2 |
| Observed sampled drawdown | 0.000% |
| Daily/weekly/peak risk locks | False / False / False |
| Missed observation gaps | 1 |
| Commission charged | \$0.0000 |
| Estimated paid funding + safety buffer | \$0.0000 |

**Most recent UTC observation:** 2026-11-24T20:16:19.844000+00:00

**Execution model:** Current Kraken public order book depth and bid/ask VWAP for attempted quote fills, plus a further 0.10% adverse slippage assumption PER SIDE and 0.05% fees PER SIDE. Candle-level historical stop touches use pessimistic price/open plus the same extra slippage because historic order books cannot be reconstructed. Funding-rate payments are estimated from published events and mark prices; expected receipts are not credited; unsettled holding periods are charged a buffer at close.

**Risk:** 1x exposure, maximum 1% theoretical entry-stop risk, 2% daily / 4% weekly / 6% peak observed account lock, loss pause 24h, 3h normal cooldown, 12h/72h crash veto and no retroactive fills after missed runs. These limits are OBSERVATION-TIME checks only, not continuously enforced exchange stops. Real gaps may exceed thresholds.

No existing positions from the historical backtest were loaded into the forward paper wallet. Each signal uses completed 1-hour ETH candles, an already-completed BTC 12h candle and official funding/OI delayed conservatively.
