# Forex CPU + GPT shadow: automatic paper tracker

## Actual workflow

[Open the automated workflow](https://github.com/eghosa001/TOOLS/actions/workflows/forex-gpt-auto.yml).

This is a **paper-only** Forex research system within TOOLS. It does **not** execute broker orders, connect to a brokerage account, or operate the original LEAN seconds-scalper.

* Wednesday **09:11 UTC**: fetch official CFTC Traders in Financial Futures futures-only GBP positions (CME contract 096742) and up-to-date Dukascopy completed H1 BID and ASK candles for GBPUSD, EURUSD and USDJPY. The CPU generates a signal only for an absolute 0.005+ change in leveraged-money net-position share. A Tuesday report is eligible the following Wednesday at 09:00 UTC, eight days after its as-of date. The model plans an illustrative **10:00 UTC** entry, two-day 500 GBP and five-day 1000 GBP scenarios, but **never places actual orders**. The connected OPENAI_API_KEY secret is used for one GPT risk-review call only for a new, current qualifying weekly signal. If no valid signal is present, no billable GPT prediction is made.
* Monday–Friday **11:37 UTC**: download newer Dukascopy prices, recover the saved paper-only ledger from the preceding successful workflow, and settle matured hypothetical two-day and five-day positions. Compare GBP 500 two-day CPU vs GPT skip/keep/adaptive scenarios and a *research-only* USD $3 protective stop. The rolling ledger stores losing trades, gross losses, maximum **closed-equity** drawdown, and skipped winning trades. A trade outcome is not counted until the relevant market quotations exist.

A separate **manual** status task is also available in the workflow menu. The old [manual key-connection test](https://github.com/eghosa001/TOOLS/actions/workflows/forex-gpt-paper.yml) succeeded on Nov 23, 2026; that confirmed authorization, but was not a paid prediction.

## Data, strategy and limits

This pipeline reproduces the same conservative CFTC CPU signal and exact past-only features as the original Higgsfield GBPUSD research; a Nov 18 2026 replay matched all nine feature values exactly against the archived research snapshot.

The CPU, GPT, and settlement components now run together inside **GitHub Actions**; they do not need to call the separate Higgsfield sandbox. The original Higgsfield LEAN seconds-scalping implementation is separate and remains not connected to live broker execution.

The after-cost research model includes real historical Dukascopy BID/ASK spreads and hypothetical USD $0.06 round-trip commissions, 0.2 pip added slippage, and USD $0.05/day/1000 GBP overnight financing. Actual broker fills, swaps, stop gaps and margin requirements are **unknown**. GitHub Actions result archives are retained for up to 90 days, and unusually long downtime can make data or the ledger unavailable. A public repo scheduled workflow can also be delayed or disabled after prolonged inactivity.

The 2026 GPT historical tests reduced **gross losing dollars** but did **not** reduce worst loss or peak-to-trough drawdown. GPT remains **shadow-only** and cannot change the CPU strategy. It should not be granted control unless sufficient independent, genuinely forward results justify it.

There is NO documented positive live track record. A successfully connected key does not make this system profitable.

## Security and ownership

OPENAI_API_KEY is supplied by your existing GitHub Actions repository secret. Never put its unencrypted value or the earlier FXKEY1 ciphertext into repository files, workflow inputs or logs. Your TOOLS repository is public and its source plus uploaded research artifacts may be public; move proprietary research to a private repository if necessary.

Sources: official [CFTC TFF data](https://publicreporting.cftc.gov/resource/gpe5-46if.json), [Dukascopy public data downloader](https://www.dukascopy-node.app/), [GitHub Actions schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Earliest prospective evaluation

As of Mon Nov 23, 2026, the next Wednesday run is Nov 25, 2026. It should produce a new **paper** risk opinion only if the CFTC positioning signal is eligible and source data are available at the scheduled time. The corresponding illustrative two-day outcome would mature Fri Nov 27, and five-day outcome Mon Nov 30, with a later weekday settlement action recording them. Do not interpret these as confirmed future profits or successful API calls before the actual runs.

Reviewed: 2026-11-23.
