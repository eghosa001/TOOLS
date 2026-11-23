# Kraken ETH, SOL, BTC intraday consensus research — verified 2026-11-23

**Results: 57 successful Freqtrade historical backtests; no exchange orders, no changes to the current 12-hour ETH paper strategy.**

Primary verified GitHub Actions run: https://github.com/eghosa001/TOOLS/actions/runs/45230288024

## Comparison design

- Exactly the same dates: August 1 through November 22, 2026 (114 calendar days). A 12-hour 8/10 reference was re-run on those dates. Older full-year numbers are NOT directly comparable.
- Markets: Kraken Futures ETH/USD, SOL/USD, BTC/USD, one independent $150 simulated wallet per scenario, maximum 1x exposure and one position at a time.
- Faster candles: 1-hour, 15-minute, 5-minute; 8-of-10 and 9-of-10 entry voting. All use the inherited ten indicators, original ATR-size/stop/exit rules and elapsed-time correct 12-hour/3-day crash detection with 48-hour entry block.
- Strict mode retains the 36-hour post-close pause and seven-day loss lock; active exploratory mode uses 3 hours after any close and 24 hours after a loss; both have the seven-day 4% Freqtrade closed-trade drawdown protection.
- Fees: 0.05% simulated per-side base; the active variants were re-executed at 0.15% per side, an extra hypothetical 0.10% per-side trading friction proxy. The extra friction is NOT verified live slippage.

## Same-period base return and trade-count highlights

| Scenario | Closes | Wins | Losses | Return | Max reported DD |
|---|---:|---:|---:|---:|---:|
| ETH 12h 8/10 strict reference | 4 | 4 | 0 | +8.0905% | 0.0000% |
| SOL 12h 8/10 strict reference | 6 | 4 | 2 | +6.6519% | 0.7769% |
| BTC 12h 8/10 strict reference | 6 | 2 | 4 | +0.7746% | 1.7888% |
| **SOL 1h 9/10 active** | **40** | **13** | **27** | **+6.3220%** | **2.5443%** |
| SOL 1h 8/10 strict | 19 | 7 | 12 | +3.8472% | 1.3895% |
| SOL 1h 8/10 active | 46 | 17 | 29 | +3.3197% | 1.9241% |
| SOL 15m 8/10 strict | 22 | 9 | 13 | +1.1685% | 0.8613% |
| ETH 1h 9/10 active | 35 | 9 | 26 | +1.7603% | 4.6521% |
| ETH 1h 8/10 active | 42 | 6 | 36 | -5.9331% | 6.7161% |
| ETH 5m 8/10 active | 125 | 36 | 89 | -2.2801% | 2.2801% |
| SOL 5m 8/10 active | 105 | 25 | 80 | -3.3391% | 3.6395% |
| BTC 5m 8/10 active | 126 | 28 | 98 | -0.9838% | 1.5344% |

**All 5-minute model combinations on the 114-day study lost money at base fees**, despite several generating roughly one closed trade per day. The two 9/10 ETH 5m modes also ended negative at base fees (-0.0616% strict and -1.2414% active). More signals did not imply more profit.

## Adverse cost re-execution for active candidates

| Candidate | 0.05% per-side return | 0.15% per-side return | Decision |
|---|---:|---:|---|
| **SOL 1h 9/10, 24h loss lock** | **+6.3220%** | **+5.0094%** | Research candidate; NOT approved for trading |
| SOL 1h 8/10, 24h loss lock | +3.3197% | -3.1199% | Reject, cost fragile |
| ETH 1h 9/10, 24h loss lock | +1.7603% | +0.6925% | Reject, drawdown exceeds 4% modeled limit |
| ETH 1h 8/10, 24h loss lock | -5.9331% | -3.9073% | Reject |
| BTC 1h 8/10, 24h loss lock | +0.8211% | -1.8122% | Reject, cost fragile |

All 12h reference results had an artificially force-closed last position: ETH +$4.624495 of +$12.135727 net; SOL +$7.136478 of +$9.977857 net; BTC +$3.845149 of +$1.161932 net. These trades were not normal exit signals. **SOL 1h 9/10 active had zero end-of-sample force-close profit.**

**SOL 1h 9/10 active downside:** 13 winners versus 27 losers, a maximum 7 consecutive losing closes, +$9.483068 base PnL on $150 and +$7.514101 under stressed fees, with maximum backtested drawdown 2.5443% base/2.9854% stress. It averaged 40 / 114 = 0.351 closes per day, about one close every 2.85 calendar days, not every hour. Closed-trade attribution showed an October loss of -$1.352954 before later recovery; October stressed loss -$2.136315.

## Second, DIFFERENT protection experiment on overlapping dates

A separate repository workflow also completed **72 rebacktest scenarios over September 1–November 22, 2026**: https://github.com/eghosa001/TOOLS/actions/runs/45230006803 . It used a DIFFERENT active mode: 48 hours after a loss, and a one-completed-candle cooldown after a close, instead of our 24 hours/3 hours. It found ETH 1h 8/10 active +5.0941% at normal fees (+2.0506% when rebacktested with higher fees), while SOL 1h 9/10 active lost -2.1769% under normal fees. These are **not** equivalent configurations, not an independent future holdout and not proof either signal is stable. They demonstrate that performance can change sharply with the chosen cooldown and testing dates.

## Risk and research decision

- **Do not activate any 5m strategy for actual trading.** Higher candle count increased losing closes, and friction wiped out apparent small edges.
- Solana 1h 9/10 active is worth a separate forward-only paper observer because it remained profitable under adverse fee assumptions in the primary 114-day simulation. It is not safe to assume that it will behave similarly in fresh months, especially after the alternate experiment's contradictory SOL result.
- Retain the 12h original system unchanged. The short-term research is not a live portfolio simulation.
- Original separate forward paper account checks 2%-daily, 4%-weekly and 6%-peak observed equity loss locks. This Freqtrade research implements *different* historical protections and **cannot be claimed to enforce those original stateful observed-equity limits**. Max account drawdown exceeded the configured historical guard in some short-candle cases, proving they are not hard caps.
- Real order-book spread, fill latency, liquidation, gap execution, position minimums and funding settlement can differ from the backtester. A high hit rate is not necessary for positive net returns, but several consecutive losses are a material risk.

## Evidence links

- Main 57-run audit: https://github.com/eghosa001/TOOLS/actions/runs/45230288024
- Supplemental differently parameterized 72-run audit: https://github.com/eghosa001/TOOLS/actions/runs/45230006803
- Full detailed JSON/Markdown published as intraday_research_report.json and intraday_research_report.md on a successful main-branch workflow, with trade ZIPs archived as GitHub Actions artifacts.

**Status: historical research complete, candidate identified, no permission to trade or auto-promote.**