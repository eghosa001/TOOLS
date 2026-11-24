# One-hour futures profit-quality experiment: ETH and SOL

**72 matched Freqtrade historical simulations, with no exchange keys or real orders.** Each candidate uses the same one-hour 8/10 ETH or 9/10 SOL ten-indicator consensus, 1x, $150 account, ATR sizing/stop, and Freqtrade protections.

Six candidate configurations per coin: original 24h loss pause, completed BTC regime veto, actual Kraken 4h open interest + hourly funding crowding veto, both vetoes, 48h loss pause without vetoes, or both vetoes with 48h pause. The normal 3h post-close cooldown and original 7-day modeled drawdown guard remain unchanged. All one-hour additions are research only.

Three windows: Jan–Jul, Aug–Nov, and one uninterrupted Jan–Nov; each window is restarted independently at $150. The later period was already examined and is **NOT untouched future data**.

Cost: actual Freqtrade funding, 0.05%/side normal or an independently rerun 0.15%/side stress scenario. These are hypotheses about friction, not measured live bid/ask spread.

| Coin | Model | Early net USD | Later net USD | Full return | Full stress return | Full trades W/L | Full max DD | Max loss streak | Research screen |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| SOL | Base24 | -5.325 | +9.483 | +2.240% | -0.022% | 34/71 | 7.361% | 8 | Fail |
| SOL | BTC24 | -7.427 | +6.181 | -0.700% | -3.011% | 23/48 | 7.338% | 9 | Fail |
| SOL | OI24 | -9.896 | +8.953 | -1.270% | -0.398% | 37/68 | 8.241% | 7 | Fail |
| SOL | Both24 | -1.314 | +5.767 | +3.337% | +0.844% | 24/44 | 5.738% | 9 | Fail |
| SOL | Base48 | -15.031 | +0.813 | -9.647% | -8.285% | 25/67 | 12.615% | 9 | Fail |
| SOL | Both48 | -1.026 | +2.366 | +0.984% | -2.999% | 22/40 | 6.046% | 7 | Fail |
| ETH | Base24 | -3.276 | -8.900 | -7.904% | -8.443% | 29/90 | 12.290% | 13 | Fail |
| ETH | BTC24 | +2.486 | +12.076 | +9.655% | +5.594% | 32/53 | 3.512% | 7 | Fail |
| ETH | OI24 | -3.762 | -4.569 | -5.376% | -7.940% | 30/85 | 9.518% | 12 | Fail |
| ETH | Both24 | +4.323 | +12.747 | +11.649% | +6.780% | 33/53 | 3.515% | 6 | Fail |
| ETH | Base48 | -6.939 | +11.675 | +2.673% | +0.502% | 30/71 | 7.610% | 13 | Fail |
| ETH | Both48 | -1.187 | +4.837 | +2.378% | -1.015% | 29/49 | 8.060% | 10 | Fail |

## Same-period baseline reproduction

- SOL: previous +6.3220%/40 trades, now +6.3220%/40 trades; matched=True
- ETH: previous -5.9331%/42 trades, now -5.9331%/42 trades; matched=True

## Decision criteria

Historical screen set before results: at least 12 full-period trades, early/later and their cost-stress net positive, full cost-stress positive, full gain >=$0.50 above that coin's Base24, later gain not lower by more than $0.10, no increased full drawdown or loss streak, and no large terminal forced exit. Passing **never authorizes real trading**.

Research-screen passes: **None**

Futures open-interest close is usable only after its 4h bar plus an extra 4h publication lag; funding is delayed 2h; BTC completed 12h trend is only used strictly after candle completion. Each filter fails closed on missing or stale data.

Weekly closed-trade P&L in the JSON is NOT a weekly marked-equity curve. Simulated protections do not replicate guaranteed 2% daily, 4% weekly and 6% peak live-account locks. Do not claim expected real earnings.

**No production ETH strategy, existing paper bot, real orders or ChatGPT paid signal settings were changed.**
