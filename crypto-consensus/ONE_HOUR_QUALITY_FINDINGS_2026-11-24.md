# One-hour ETH/SOL quality improvements — actual 72-run audit (November 24, 2026)

**All results are Freqtrade historical futures simulations, not observed profit,
income, live exchange orders or a guarantee of future performance.**

Verified successful GitHub Actions run, with all raw trades and provenance:
https://github.com/eghosa001/TOOLS/actions/runs/45353326794

## What was changed, without touching the working bot

The existing 12h protected ETH strategy, live keyless paper observer, loss
locks and paid ChatGPT shadow settings were **not altered**. Added isolated
1h research strategies for the historical 8/10 ETH and 9/10 SOL candidates:

- original 24h stop-loss pause/3h regular cooldown
- 12h **completed** BTC macro regime filter
- independently published 4h Kraken Futures open interest and hourly funding
  **crowding** veto, never estimated from ETH price
- both filters
- 48h loss pause with and without both filters

All use the original 1x leverage, ATR stop and stop-distance 1%-risk sizing.
The full test spans Jan 1–Nov 22 2026. Jan–Jul and Aug–Nov are also
separately *restarted* $150 scenario accounts; the full-period test is one
uninterrupted $150 account. Costs include Freqtrade modeled funding, 0.05%
per side normal commission and independently rerun 0.15% per-side
adverse-friction stress, NOT observed order-book slippage.

The research reproduced the earlier 114-day original one-hour baselines
**exactly** in the Aug–Nov scenario: SOL 9/10 active **+6.3220% from 40
trades**, ETH 8/10 active **−5.9331% from 42 trades**. Baseline
reconciliation passed before any improvement was accepted.

### Full-period ETH 1h results

| Entry gate, loss pause | Normal net return | Higher-fee return | Normal closed trades | Maximum normal reported DD | Maximum normal losing streak |
|---|---:|---:|---:|---:|---:|
| 8/10 original 24h pause | **−7.9037%** | −8.4425% | 119 | 12.2901% | 13 |
| BTC regime 24h | +9.6546% | +5.5942% | 85 | 3.5119% | 7 |
| Funding/OI 24h | −5.3760% | −7.9396% | 115 | 9.5176% | 12 |
| **BTC + funding/OI, 24h** | **+11.6487%** | **+6.7799%** | **86** | **3.5151%** | **6** |
| Original 48h pause | +2.6732% | +0.5018% | 101 | 7.6097% | 13 |
| Both filters 48h pause | +2.3778% | −1.0146% | 78 | 8.0599% | 10 |

For the leading ETH Both24 result, one continuously modeled $150
account finishes at ~$167.47 in the normal test and ~$160.17 under the
separate higher-cost test. The normal 86 closed trades were **33 wins
and 53 losses**, average ~1.85 closed trades per calendar week, and
there was **no terminal forced-close profit**.

Early Jan–July separately restarted normal PnL was **+$4.322747**,
but *higher-cost* PnL was **−$0.948298**. Later Aug–Nov separately
restarted PnL was **+$12.746656** normal and **+$10.399202** stressed.
The isolated early cost-stress loss means **the predeclared robustness
screen FAILED**, despite the substantial full-period gain.

Adverse-cost full ETH Both24 maximum reported account drawdown was
**~4.47%**, above the 4% figure in the historical drawdown
protection. Freqtrade protections are NOT hard guaranteed loss caps.

A single August trade gained **+$8.510 normal (+$7.985 stressed)**,
accounting for ~49% of normal full-period PnL and ~79% of stressed
PnL. The top two stressed winners together exceeded the stressed
total net profit: this is a warning about dependence on rare trends,
not proof of reliable frequent income.

The closed-trade calendar months of ETH Both24 normal were:
Jan −$0.317, Feb +$3.064, Mar +$3.058, Apr −$1.944,
May −$0.142, Jun +$2.611, Jul −$2.360, Aug +$5.697,
Sep +$2.278, Oct −$2.537, Nov +$8.066.
These are NOT monthly marked-equity returns or a live account.

### Full-period SOL 1h results

| Entry gate, loss pause | Normal return | Higher-fee return | Trades | Normal reported DD | Maximum consecutive losing trades |
|---|---:|---:|---:|---:|---:|
| 9/10 original 24h | +2.2398% | −0.0222% | 105 | 7.3605% | 8 |
| BTC 24h | −0.6998% | −3.0112% | 71 | 7.3377% | 9 |
| OI 24h | −1.2699% | −0.3978% | 105 | 8.2405% | 7 |
| Both 24h | +3.3374% | +0.8436% | 68 | 5.7380% | 9 |
| Original 48h | −9.6466% | −8.2852% | 92 | 12.6148% | 9 |
| Both 48h | +0.9838% | −2.9993% | 62 | 6.0458% | 7 |

The SOL Both24 24h result increased full profit versus the unfiltered
base but **lost money in the early Jan–July scenario**, worsened the
maximum losing streak from 8 to 9 and gave a smaller profit than the
original baseline in the previously observed Aug–Nov scenario.
**No SOL candidate passed the preregistered screen.**

## Data integrity and no-lookahead measures

- BTC macro gate evaluates genuine BTC 12h close, EMA100 and previous
  two-day momentum, published strictly after its bar closes.
- Kraken futures OI four-hour block is delayed eight hours from the
  open-time in source, deliberately including an extra 4h publication
  tolerance. Hourly funding is delayed 2h. Both must be fresh.
- Genuine, exchange-origin OI source is accompanied by SHA256 manifest.
  No hindsight “ChatGPT” signals or fabricated OI used.
- Historical 1h ETH/SOL and 12h BTC candles and actual Kraken funding/mark
  passed source coverage and continuity checks.
- Unit tests verify future BTC/OI changes do not rewrite earlier signals,
  reject gapped or missing feeds, and ensure the combined gate can only
  veto, not invent trades.
- All 72 Freqtrade ZIPs and timestamps are available in the action artifact.

## Decision

**Do not activate a real-money or live automated 1h bot.**
**Do not replace the existing protected 12-hour paper observer.**

ETH Both24 is the strongest *historical research candidate* after
actual BTC and open-interest evidence; it is better than the unchanged
1h baseline across the full model, but the early cost-stress loss and
large-trade dependence preclude declaring it a robust profit engine.
Keep the 1h ETH Both24 variant separate for genuinely future
paper-only evaluation and minimum-order/spread/stop-fill verification.

SOL 9/10 should retain its existing research status without being
promoted. Making the loss cooldown 48 hours did not solve losing
periods. No automatic model selection or trading permission is granted.

Main report: one_hour_quality_report.md and .json once published.
Full raw audit: https://github.com/eghosa001/TOOLS/actions/runs/45353326794
