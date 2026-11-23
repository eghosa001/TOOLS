# Five additional cryptocurrencies — protected futures strategy research
**Verified November 23, 2026 • All simulated, zero real trading**

Thirty Freqtrade historical simulations completed in GitHub Actions:
https://github.com/eghosa001/TOOLS/actions/runs/45225410445

Official Kraken Futures BTC, SOL, XRP, DOGE and ADA data (12h OHLCV,
actual hourly mark and funding, and official 4h open interest) passed the
data-completeness checks for the tested interval. All five contracts were
active linear USD margined futures with 1 contract-size unit; amount
precision varies, and fills/availability remain model assumptions.

The baseline is **the same 8-of-10 protected consensus** previously used
for ETH, with identical protections, 1x nominal exposure and a $150
starting account per coin. The second research class adds the same
causally lagged funding + open-interest crowding veto tested on ETH.
No optimization, extra leverage, real exchange keys or orders were used.
Neither strategy is authorized for production.

| Coin | Baseline net % | Funding/OI net % | W/L with OI | Baseline max DD | OI max DD | Research gate |
|---|---:|---:|---:|---:|---:|---|
| BTC | +4.6032% | +3.4048% | 8/11 | 2.0831% | 2.1073% | Fail |
| SOL | +7.0321% | **+7.8938%** | 7/10 | 2.9852% | 3.0038% | Pass, future validation required |
| XRP | -2.5271% | -2.4042% | 5/14 | 4.6488% | 4.5123% | Fail |
| DOGE | +4.7651% | +5.1542% | 7/8 | 2.2501% | 2.2247% | Fail: later window deteriorated |
| ADA | -0.9763% | -1.3882% | 5/14 | 4.7734% | 4.9736% | Fail |

All returns are **backtested**, inclusive of modeled Freqtrade fees
and exchange funding. Historical Freqtrade drawdown is not a guaranteed
intrabar, mark-to-market or future maximum drawdown.

### Crucial: profit from forced endpoint closures

The November 23 forced closing of an open position was **not** a
strategy-generated signal. It represented a large share of backtest
headline profit for most assets.

| Coin | OI-strategy total net USD | Of which forced terminal close USD | Net of other already-closed trades USD |
|---|---:|---:|---:|
| BTC | +5.107257 | +3.845149 | +1.262108 |
| SOL | +11.840733 | +7.136478 | +4.704255 |
| XRP | -3.606272 | +1.573294 | -5.179566 |
| DOGE | +7.731343 | +4.630415 | +3.100928 |
| ADA | -2.082238 | +3.864046 | -5.946284 |

The rightmost column is *trade-close attribution excluding terminal
forced exits*, **not the mark-to-market equity of an account with the
final position still open**. It must not be represented as an investable
performance total.

### Half-year sensitivity

The later July–November 2026 SOL funding/OI run produced the same
+$8.141770 as SOL's own baseline, despite improving the January–June
result from +$2.865002 to +$4.227192. The benefit arose entirely in
the earlier period. SOL's backtested drawdown actually rose slightly
from 2.9852% to 3.0038% (inside the preregistered numerical tolerance).

DOGE had +$7.731343 on the uninterrupted full window, but its later
restarted run **fell** to +$3.706123 from the original +$4.443655,
so the seemingly higher full-period return did not qualify as stable.

BTC's later restarted run lost -$0.726747 under **both** strategies.
XRP and ADA lost money for both variants over the full period.

The two half-year windows each **reset to $150** solely for scenario
comparison. The full Jan–Nov period uses one continuous account **per
coin**. There is NO multi-coin shared-wallet or simultaneous position
simulation, and percentages must never be added to claim overall portfolio
profit. Correlated crypto crashes can make a multi-asset account worse.

### Decision

Keep the existing main ETH paper observer and strategy unchanged.
Keep SOL funding/OI as a **separate candidate for future-only paper
evaluation**. DOGE is a weaker candidate that failed later-period
validation. Do not automatically deploy the BTC, XRP or ADA versions
that lost advantages or money. Test actual forward trade entry,
funding, funding publication delays, available minimum sizes, slippage,
cross-coin correlation and a shared 1%-risk budget before allowing more
than one coin to trade in the same portfolio.

The full trade-by-trade scenario reports and every check are at:
https://github.com/eghosa001/TOOLS/actions/runs/45225410445

No real-money exchange orders or paid LLM API signals were initiated
by this work.
