# Automated GBP/USD Forex research: CFTC CPU strategy + GPT shadow

The full weekly research workflow runs on GitHub Actions, using the existing OpenAI API secret that was verified in TOOLS. It is independent of the older seconds-scalping LEAN algorithm. No broker accounts, order execution or auto-live trading are connected.

## Working links

- Automated pipeline, run history and paper artifacts: https://github.com/eghosa001/TOOLS/actions/workflows/forex-gpt-auto.yml
- Existing API secret settings: https://github.com/eghosa001/TOOLS/settings/secrets/actions
- Earlier manual no-cost key verification: https://github.com/eghosa001/TOOLS/actions/workflows/forex-gpt-paper.yml

## Data-to-decision steps

1. Download actual completed Dukascopy H1 bid and ask quotations for GBPUSD, EURUSD and USDJPY using the pinned dukascopy-node 1.51.1 library.
2. Retrieve the official US CFTC TFF Futures Only weekly data for CME GBP contract 096742 via publicreporting.cftc.gov/resource/gpe5-46if.json.
3. Enforce the existing conservative CFTC eligibility: report dated Tuesday cannot contribute to a decision until the following Wednesday at 09:00 UTC, eight calendar days later. Ignore weekly changes in (long minus short)/open interest below 0.005.
4. Calculate identical causal CPU side and momentum/volatility features to the existing multi-day positioning strategy. The 500 GBP/2-day scenario uses the positive eight-previously-closed-paper-trade gate initially seeded from archived 2026 CPU tests. The separate 1000 GBP/5-day control is retained.
5. Normally on Wednesday at 09:11 UTC, request a SINGLE billed OpenAI GPT-6-luna risk assessment for the eligible signal; absent/stale/weak signals never call the paid API. CPU and GPT use the same market snapshot. GPT only gets to mark SKIP, KEEP_2D or KEEP_5D with a risk explanation. CPU plans are NEVER changed by GPT.
6. The planned hypothetical entry is 10:00 UTC that Wednesday, one hour after the CPU signal. The entry quote is read later from real historical bid/ask H1 data. No guessed or invented entry fill.
7. On weekdays at 11:37 UTC, compare actual subsequent Dukascopy quotation outcomes for CPU 500 GBP/2-day and 1000 GBP/5-day, hypothetical $3 protective-stop 2-day/500 GBP, and GPT-veto/adaptive 2-day/5-day/500 GBP alternatives. Use 0.2 pip extra round-trip slippage, $0.06 round-trip commission, and illustrative funding $0.05/day per 1000 GBP; broker fees and overnight swap are not verified.
8. Record cumulative hypothetical net profit, losing dollars, worst completed trade and drawdown based on CLOSED trades, missed winning trades and losses avoided by GPT. These results are simulations, not actual broker fills or tick-level peak-to-trough account drawdown.
9. Repackage the rolling state in forex-paper-ledger and this run's analysis in forex-paper-report GitHub Actions artifacts. The next successful run restores the previous complete ledger and refuses silent resets.

## Schedule and manual controls

The recurring schedule is Wednesday 09:11 UTC (10:11 West Africa Time) for CFTC/CPU/GPT risk analysis, and Monday-Friday 11:37 UTC (12:37 WAT) for paper outcome tracking. GitHub scheduled runs may be delayed or skipped. Weekly GPT calls are rejected after 09:55 UTC to avoid implying the planned 10:00 entry could still be achieved. Public-repo schedules can also be disabled by GitHub following 60 days without repository activity.

To check safely, open the automated workflow and select Run workflow with task=status. This runs security/regression tests and reads the ledger with NO API inference or market download. Task=settle refreshes prices and settlements with NO GPT charge. Task=weekly only runs an eligible signal during the Wednesday window; one GPT inference may incur OpenAI API charges. The earlier manual workflow mode=check also tests authentication without a paid generation call.

## Security and limitations

- OPENAI_API_KEY is kept as a GitHub Actions SECRET, not in tracked files or workflow inputs. Never paste an unencrypted API key, encrypted FXKEY1 blob, or broker credentials into the public repository.
- TOOLS is PUBLIC and has many unrelated Actions workflows. Anyone able to change trusted workflows can potentially use repository secrets. Other users can inspect public source and possibly run artifacts. A private repo with narrowly scoped environments is preferable before using any real-money trading credentials or proprietary strategy data.
- This is a WEEKLY positioning strategy. It does not route signals to an actual broker or modify/enable the separate LEAN seconds-scalping algorithm. The pipeline does not maintain a continuously running trade executor.
- The original historical experiment does not prove ChatGPT improves downside control; it reduced total losing dollars while failing to reduce the worst individual loss or hourly drawdown. Keep GPT in SHADOW mode until prospectively observed after-cost losses and drawdowns establish a benefit.
- A valid bid/ask H1 candle is NOT proof that a stop would have executed at a modeled price; spreads, margin, swaps, news gaps and liquidity can make a real trade worse.
- The rolled-forward artifacts have finite retention (up to 90 days). Keep backups if long-term experiment continuity is important.

## Tests

Run: python3 -m unittest discover -s forex-gpt -p test_*.py -v

Tests are synthetic, offline, use no OpenAI API tokens and open no broker positions.
