# GBP/USD GPT paper adviser in TOOLS

This is a separate, manually-run and paper-only Forex component. It cannot access broker credentials, place trades, modify existing Android/video jobs or execute scheduled API calls.

## Connect the existing API key

Open https://github.com/eghosa001/TOOLS/settings/secrets/actions

Select New repository secret. Name it OPENAI_API_KEY. Paste the ORIGINAL secret API key beginning with sk-, not the encrypted FXKEY1 value you shared before. Never add a real API key to a committed repository file, GitHub workflow input, issue or chat.

TOOLS is a public repository with many workflows. Anyone able to modify authorized Actions code could potentially use its repository secrets. If this risk is unacceptable, store the credential in a dedicated private repository instead.

## First connection test (no paid GPT prediction)

Open https://github.com/eghosa001/TOOLS/actions/workflows/forex-gpt-paper.yml
Choose Run workflow, select main, leave mode = check, and run. The workflow first runs safe unit tests, then makes a GET request for the model gpt-6-luna. This verifies that the API key can authenticate and access the model, without generation charges.

The workflow does not run automatically. No paid prediction happens unless you deliberately select mode = paper.

## Paper-only forecasting

The optional paper mode requires a fresh, accurate, past-only JSON snapshot from official weekly CFTC institutional futures data and completed H1 Forex market quotes. The input must be less than 90 minutes old. Required fields: utc_signal with UTC offset, CFTC_asof_date, base_side, CFTC_lev_money_net_share, CFTC_weekly_net_change, GBPUSD_2d_momentum_bp, GBPUSD_5d_momentum_bp, GBPUSD_10d_momentum_bp, GBPUSD_5d_high_low_pips, EURUSD_5d_momentum_bp, USDJPY_5d_momentum_bp, GBPUSD_last_completed_H1_range_pips.

No fresh data pipeline is presently connected to GitHub. Never invent these fields or reuse old prices. The existing separate Higgsfield research workspace has historical quotes ending November 20, 2026 and would need fresh data ingestion before valid forward paper decisions.

GPT advice can be SKIP, KEEP_2D or KEEP_5D, with risk severity and brief reasoning. GPT cannot override the CPU signal. Historical 2026 experiments reduced overall gross losses but did not reduce worst loss or maximum drawdown, so the risk benefit remains unproven.

This workflow operates independently of the separate Higgsfield sandbox; installing the GitHub secret does NOT install it in Higgsfield.
