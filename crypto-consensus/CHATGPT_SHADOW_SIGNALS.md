# ETH consensus — ChatGPT/OpenAI 11th shadow signal

The repository's original ten technical-indicator votes remain unchanged.
**The optional OpenAI vote is NOT included in its >=8-of-10 entry threshold.**
It cannot create or cancel exchange orders or increase stake size.

## How it works

- Every 00:35 and 12:35 UTC, a separate GitHub Action observes completed
  12-hour ETH/USD Kraken Futures candles, a 10-vote consensus tally, ATR,
  and a crash-entry status. Input is restricted to timestamped PUBLIC prices.
- It asks a configured OpenAI model to return only:
  \`{"signal":"BUY|SELL|HOLD","confidence":0..1,"rationale":"..."}\`.
  A structured schema and independent validation reject malformed responses.
  The model is instructed to forecast the *next 12-hour direction* and HOLD
  when uncertain. No external tools or trading authority are provided.
- Only predictions actually made soon after the candle close are saved.
  Each signal includes input hash, issuance time, observed entry quote,
  model identity and usage. It is evaluated only when the next
  **completed** 12-hour candle actually arrives. No historical ChatGPT votes
  are invented or backfilled.
- We score AI and baseline directions on equal price opportunities with a
  0.2% round-trip simulated trading-cost assumption. This measures hypothetical
  **directional value**, NOT strategy P&L, actual execution, or risk-managed
  equity. The original forward paper account is separate.
- The full AI ledger is saved in \`ai_shadow_state.json\` and reports as
  \`ai_shadow_report.json\` and \`ai_shadow_report.md\` on main.
  A missing API key is recorded as \`unavailable_no_paid_api_opt_in\`, not a
  fictitious HOLD. Once a candle is recorded, the job never retroactively
  replaces that entry with an artificial AI prediction.

## Cost: no surprise API charges

**Default:** ZERO OpenAI calls, no API bill. The scheduled job continues
collecting which completed candles were eligible and what the original ten
voters said. A ChatGPT Plus subscription is NOT an API key.

The user must intentionally complete BOTH of these steps before any
model inference begins:

1. Add an OpenAI project key as a GitHub Actions encrypted repository
   secret named \`OPENAI_API_KEY\`. Do not add the key to code or chat.
2. Set repository Actions variable \`ENABLE_PAID_OPENAI_SIGNALS\` to
   the literal string \`true\`. All other values disable AI requests.

Optional variable: \`OPENAI_SIGNAL_MODEL\` (default: \`gpt-5-nano\`).
Use a project budget, usage caps, and alerts in OpenAI Platform before
enabling. The automatic cadence is at most two scheduled calls per day,
subject to retries and manually dispatched runs; **the code itself never
retries a model request**. There are no paid calls during GitHub PR
safety tests, even with a real secret on the GitHub account.

A user with no paid API entitlement can still use the rest of the
crypto consensus system and the independent data collection for free.

## Minimum evidence threshold before considering use

- Gather at least 60 *forward-made* completed 12-hour predictions with
  resolved next-candle price outcomes, spanning multiple market regimes,
  including losing weeks. Prefer 100+ resolved predictions.
- Compare AI and baseline on EXACTLY matched signal opportunities and
  cost assumptions. Test whether AI adds information on the occasions
  it contradicts the original ten-vote consensus; correlate outcomes,
  not just apparent win rate.
- Examine HOLD coverage, prediction latency, confidence calibration,
  funding, slippage and persistent wallet equity with risk controls.
- Hold out subsequent genuinely future weeks. Do not use the same July–
  November 2026 history for further tuning and call it untouched test data.
- Only after independent forward improvements should there be a separate
  human-reviewed proposal to modify the entry/exit thresholds or weights.
  This module deliberately contains **no such deployment path**.

### Reproducibility and safety

Entry benchmark is the observed public quote after signal issuance; exit
benchmark is the next 12h close, not an exchange fill. Stop-loss fills and
capital allocation are *not* modeled here. Sudden gaps, low liquidity and
funding differences remain risks. Not financial advice and no promise of
profits. OpenAI models can confidently make incorrect market forecasts.

Relevant source documentation:
- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/pricing
