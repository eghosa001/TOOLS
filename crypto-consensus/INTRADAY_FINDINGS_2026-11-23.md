# ETH / SOL / BTC intraday consensus research — 23 November 2026

**Results: actual Freqtrade backtests on Kraken Futures market data; NOT live exchange profits.**
No real exchange orders, no keys, no paid AI inference. The existing 12-hour
ETH research and its continuing paper observer are unchanged.

## Exact experiment

- ETH, SOL and BTC perpetual futures; one $150 starting simulated account
  **per market and configuration**, not a combined account.
- 1-hour, 15-minute and 5-minute completed-price candles.
- Entry agreement **8/10 versus 9/10** of the same ten *correlated*
  technical indicators (not independent bots).
- Strict mode: original calendar-equivalent 36h trade cooldown and 7-day
  post-loss lock; Active mode: 1 full candle cooldown and 48h post-loss
  lock, with substantially more opportunities but weaker protection.
- Both modes: 1x position leverage, maximum one open trade, original ATR
  position sizing for 1% modeled stop-distance capital risk, original
  4% emergency stop, and 4% historical 7-day MaxDrawdown protection.
- Original 8% move in 12h / 15% move in 72h crisis-entry filters retained
  in real calendar hours on shorter candles, with 48h entry block; 5m
  warmup corrected to 865 completed candles so the full 72h observation
  is available **before the first five-minute trade**.
- Normal model fee: 0.05% on each side; *independently rebacktested* higher
  friction fee: 0.15% each side (additional 0.10%/side proxy for
  spread/slippage, NOT an actual exchange execution simulation).
- The **same 83 calendar days**: September 1 through November 22, 2026.
  Each test has a continuous paper wallet through its entire 83-day
  window, not weekly resets. Weekly closes are not marked equity.
- Total: 3 markets × 3 timeframes × 2 vote thresholds × 2 cooldown
  modes × 2 cost scenarios = **72 Freqtrade runs**.
- Independent same-date 12-hour benchmark: 3 markets × 2 cost scenarios
  = **6 further Freqtrade runs**.

### Main finding

**One candidate passed the prespecified research screen:**
ETH / 1h / 8-of-10 / Active.

| Metric | Normal cost model | Rebacktested higher friction |
|---|---:|---:|
| End-equity return over 83 days | **+5.0941%** | **+2.0506%** |
| Profit on $150 paper starting capital | **+$7.641223** | **+$3.075860** |
| Completed trades, normal case | **31** | Separate 0.15% fee execution |
| Winning / losing normal-case closes | **12 / 19** | Distinct re-executed trades |
| Normal case backtester reported max drawdown | **1.3612%** | Separate simulation |
| Average completed trades/week | **2.614** | Separate simulation |
| Forced end-of-test exit P&L | **$0** | No terminal artificial profit |

The improvement is meaningful *only as a historical research signal*:
- It requires a shorter, riskier post-loss lock (48 hours instead of seven
  days); the strict same-timestamp 1h 8/10 version **lost 1.5548%**.
- Among 12 calendar weeks with ETH 1h Active trade closes, six had positive
  closed-trade P&L and six negative. This is not a marked weekly wallet
  equity curve.
- The winning average exceeded the losing average, but the strategy
  actually lost **19 out of 31 trades**.
- It was the best of many historical variants chosen after examination,
  which can substantially overstate the odds of repeating its performance.
- It delivers roughly three opportunities a week, **not several profitable
  entries every day**; no earnings promise follows from this simulation.

### Other intraday candidates (Active protection)

| Market | Timeframe | Votes | Closed trades | Normal return | Higher-cost return |
|---|---|---:|---:|---:|---:|
| ETH | 1h | 8/10 | 31 | **+5.0941%** | **+2.0506%** |
| ETH | 1h | 9/10 | 25 | +0.8162% | -0.3606% |
| ETH | 15m | 8/10 | 45 | -2.6362% | -5.0799% |
| ETH | 15m | 9/10 | 41 | -1.6225% | -3.8713% |
| ETH | 5m | 8/10 | 56 | -0.4534% | -2.3129% |
| ETH | 5m | 9/10 | 55 | +0.2057% | -2.9788% |
| SOL | 1h | 8/10 | 35 | +1.4763% | +0.6396% |
| SOL | 1h | 9/10 | 28 | -2.1769% | -3.3920% |
| SOL | 15m | 8/10 | 42 | -1.0061% | -2.8875% |
| SOL | 15m | 9/10 | 43 | -2.8456% | -4.7118% |
| SOL | 5m | 8/10 | 51 | -0.7078% | -3.6129% |
| SOL | 5m | 9/10 | 46 | -1.4085% | -4.0907% |
| BTC | 1h | 8/10 | 34 | +0.8141% | -2.0301% |
| BTC | 1h | 9/10 | 27 | +0.6263% | -0.6158% |
| BTC | 15m | 8/10 | 46 | -1.1491% | -2.1172% |
| BTC | 15m | 9/10 | 43 | -1.0545% | -1.2732% |
| BTC | 5m | 8/10 | 53 | -0.9347% | -2.4997% |
| BTC | 5m | 9/10 | 52 | -0.8827% | -2.3501% |

The 18 additional Strict-mode simulations are in the full JSON/MD report
alongside counts, worst gaps between entries, run-specific weekly closures,
max losing streaks and maximum simulated drawdowns.

**The 15-minute experiments were unprofitable for all three markets, and the
5-minute strategies lost money in the independently rerun higher-cost test
regardless of 8/10 or 9/10 agreement.** More candles and extra trades did
not reliably create more net profit.

### Fair comparison with same-date original 12h trading

| Market | 12h original return | Same-date 12h trades | Artificial final trade close USD |
|---|---:|---:|---:|
| ETH | +2.5511% | 4 | +$4.624495 |
| SOL | +4.8149% | 3 | +$7.136478 |
| BTC | +1.3869% | 5 | +$3.845149 |

Original 12h results for the same 83 days rely heavily on **forced,
end-of-simulation position closures** rather than natural strategy exits.
These are not genuine profit-taking signals. The leading ETH 1h result
had no such terminal artificial close. For ETH the 12h model's +2.4472%
higher-friction result is numerically above the 1h candidate's +2.0506%,
but this comparison is dominated by the 12h **artificial final exit**.

Do not present a single period's net as reliable monthly income.
The older, 326-day original ETH +11.042% result is **not a direct
same-period control** and is deliberately excluded from this table.

### Decision / research status

- Keep the existing 12-hour ETH paper bot intact and real trading disabled.
- Preserve ETH 1h 8/10 Active as **an experimental shadow candidate**;
  collect genuinely subsequent, forward-made trades through changing
  price regimes before modifying any real positions or risk rules.
- Do **not** promote the 15m or 5m strategies simply to increase
  trade frequency. Re-test them only if a defensible new independent
  signal hypothesis is developed, with additional price-execution data.
- Do not automatically add BTC or SOL to live trading from this evidence.
  SOL 1h 8/10 Active has a slight positive result but fails the stricter
  fixed-trade cost-sensitivity screen.
- Never infer that the 2%/4%/6% keyless forward-paper observer locks
  are implemented as exchange-held guaranteed intraday stops inside
  these Freqtrade historical studies. Actual intrabar gaps and fills may
  lose more than reported limits.
- Do not treat these 78 retrospective model checks as a fresh,
  independent out-of-sample experiment; future data is still required.

### Audit evidence

- Corrected 72-case fast strategy workflow:
  https://github.com/eghosa001/TOOLS/actions/runs/45232030147
- Independent six-case same-date 12h original benchmark:
  https://github.com/eghosa001/TOOLS/actions/runs/45232955173
- Generated intraday research output: intraday_research_report.md/json
- Generated matched 12h output: intraday_12h_reference.md/json

All calculations are reproducible from the actual Freqtrade trade export
ZIPs and timestamped Kraken public futures price/mark/funding data
contained in the workflow artifacts.
