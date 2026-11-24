# One-hour ETH: more signals, more trades, real fee and drawdown comparison

**72 historical Freqtrade simulations; no real orders.**
Twelve preregistered entry hypotheses × three historical date windows (Jan–Jul, Aug–Nov, continuous Jan–Nov 2026) × two costs (0.05%/side and 0.15%/side). Each run has an independent $150 wallet.

New completed-candle evidence: 24-hour rolling VWAP, volume participation versus prior 24-hour median, 20-hour Chaikin money flow, 6-hour ATR-normalized momentum, prior-20h channel breakout, and (in some candidates) a less strict completed-BTC 12h EMA macro regime. REAL Kraken OI/funding crowding veto is retained where specified. These indicators are correlated, not standalone independent AI bots.

The baseline More1h8Both is matched against earlier Q1h8Both24 Freqtrade results trade-for-trade; all existing paper trading remains separate.

| Entry hypothesis | Jan–Jul net USD | Aug–Nov net USD | Jan–Nov return | Jan–Nov cost-stress return | Natural trades | Trades/week | Full max DD | Max loss streak | Largest winner / net | Pass? |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| More1h8Both | +4.323 | +12.747 | +11.649% | +6.780% | 86 | 1.85 | 3.52% | 6 | 48.7% | Fail |
| More1h7Both | +6.660 | +6.947 | +9.301% | +2.285% | 95 | 2.04 | 3.50% | 9 | 61.3% | Fail |
| More1h6Both | +5.373 | +4.749 | +6.733% | -2.093% | 99 | 2.13 | 4.31% | 9 | 84.7% | Fail |
| More1h7BTC | +4.874 | +9.196 | +9.650% | +1.123% | 94 | 2.02 | 3.48% | 9 | 59.1% | Fail |
| More1h6BTC | +3.501 | +4.797 | +5.262% | -1.757% | 100 | 2.15 | 4.49% | 9 | 102.6% | Fail |
| More1h7SoftBTC | +4.153 | +5.128 | +5.997% | +0.370% | 111 | 2.38 | 3.41% | 10 | 90.1% | Fail |
| More1h7Flow | +3.741 | +13.112 | +11.014% | +1.192% | 79 | 1.70 | 4.53% | 7 | 48.4% | Fail |
| More1h6Flow | +1.605 | +12.190 | +8.869% | +0.050% | 82 | 1.76 | 5.05% | 7 | 60.1% | Fail |
| More1h7Hybrid | +5.348 | +6.606 | +8.230% | +0.701% | 94 | 2.02 | 4.28% | 9 | 69.3% | Fail |
| More1h7Breakout | +6.660 | +6.302 | +8.831% | +1.778% | 96 | 2.06 | 3.50% | 9 | 64.6% | Fail |
| More1h7SoftHybrid | +2.256 | +8.620 | +7.169% | +0.106% | 109 | 2.34 | 4.32% | 10 | 75.3% | Fail |
| More1h6FlowBTC | -0.017 | +11.764 | +7.491% | -0.722% | 82 | 1.76 | 6.05% | 10 | 71.2% | Fail |

## Frozen incumbent reproduction

- early: original +2.8818%/58 vs research +2.8818%/58 trades — MATCHED
- later: original +8.4978%/29 vs research +8.4978%/29 trades — MATCHED
- full: original +11.6487%/86 vs research +11.6487%/86 trades — MATCHED

## Predeclared promotion gate

At least 25% more natural closed trades than 8/10 control; both historical segments profitable under **both** normal and higher fees; full normal AND stressed gains each at least $2 above the control; full DD <=6% under both fee models; no more than 8 consecutive losing closes; no artificial terminal close profit >10 cents; largest winner below 60% of positive natural net. Any failing check rejects the candidate.

**Passes:** **None.**

The new 6/10 and 7/10 thresholds permit extra opportunities, but NO performance claim is accepted without actual additional net profit under independent fee-stress backtests.

**No live trades, no automatic activation, no existing 12-hour strategy replacement, no modification to the ETH 1-hour prospective paper-ledger, and no guarantee of daily income.**
