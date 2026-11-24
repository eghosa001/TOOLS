# Forward-only Solana meme-coin research — no real trading

## Status

This is an isolated, keyless RESEARCH/PAPER workflow. It does not load a wallet, create or sign orders, call paid APIs, alter the existing protected ETH Freqtrade strategy, or modify its existing $150 forward paper ledger. Do not translate this simulator's prices into executable fills.

The first GitHub Action validation completed on Nov 24, 2026:
https://github.com/eghosa001/TOOLS/actions/runs/45379693942

## Historical: what was actually tested

Independent public MIT research data at:
https://github.com/ian05012/solana-memecoin-dataset/tree/7070d00e1e4492f8604d988549d91785cc5f43f7

Source: 44,460 feature snapshots (31,013 first-observed distinct tokens), 272,426 price candles covering a short June 2026 detection universe, **not all failed launches**. Source creators explicitly warn that tokens are only observed if they survive to detection.

The fixed, non-optimized snapshot screener selects only the first detection per token and NEVER uses forward return labels for entries. It requires pre-existing mint/freeze safety flags, adequate liquidity/volume, momentum, holder distribution and low reported rug risk. Test entry is first available 15m *open AFTER* capture and exit is at the close one hour later, if all four consecutive 15m intervals exist. Two hypothetical DEX friction scenarios: 0.35% and 1.5% per side.

**Actual key result: candle coverage is insufficient to infer profit.**
- Strict: 180 predefined signals, only 3 with viable full paths, 1.67% coverage. The three path-measured trades averaged -28.95% net per trade at 0.35% per-side assumed costs, but n=3 and survivorship/missingness prevent meaningful expected profit claims.
- Less restrictive: 829 predefined signals, only 19 with viable paths, 2.29% coverage. The 19 measurable paths averaged +61.70% net per trade at 0.35% costs; **this is selected-completer bias**, not a credible expected strategy return. The 810 missing-path outcomes are not assumed profitable or ignored in tradeability assessment.
- The high measured returns are NOT wallet backtest returns and must not be projected into income. Cannot compute a validated full-cohort PnL, sharpe, or drawdown from this archive.

Reproduce: use the pinned URL in the workflow to download only tokens.parquet and ohlcv.parquet, then run onchain_historical_screen.py. Do not train on labels and then evaluate on the same period.

## Forward source, universe, and data provenance

- GeckoTerminal Public API: https://api.geckoterminal.com/docs/index.html
- Endpoint: /api/v2/networks/solana/new_pools (two pages, currently up to 40 pool records per successful cycle, including failed/unsafe/illiquid ones **once discovered**).
- Scheduler: GitHub Actions **every 15 minutes** on the default branch, best effort. Github may delay or skip cron. No fake retroactive observations or fills; >45 minute gaps are recorded.
- The API has a public low request-rate cap (~10 calls per minute as of 2026). Uses modest sampling. **This is not the entire population of Solana token launches**; pools that never enter sampled pages will be missed. Successful, unsuccessful and disappearing **observed** pools are retained. Do not call their distribution a complete chain census.
- State file on the default branch: onchain_forward_state.json; report: onchain_forward_report.json. These are records, not exchange statements.
- After 24h, a rate-limited subset receives a follow-up multi-pool check. A missing API response is marked unresolved, not proof of a rug. Low follow-up liquidity (<$1k) is marked liquidity-lost. Do not relabel non-responders as survivors.
- GoPlus Solana security endpoint: https://docs.gopluslabs.io/reference/solanatokensecurityusingget
- GoPlus checks are point-in-time and fail closed when unknown: mintable/freezable/closable/balance-mutable permissions must explicitly be disabled, token transferable and initialized, no transfer hook, top 10 reported holders must control at most 50%. Missing or rate-limited response yields no entry. GoPlus is not an audit or protection guarantee.

## Prospective predeclared paper signals and execution

Eligible at first observation only: quote mint must be verified WSOL/USDC/USDT, pool age <=75 minutes, liquidity >=$50k, previous five-minute volume >=$12k, buys >=25, sells >=10 and buy/sell count ratio <=5. The token must pass the GoPlus gate. Select highest five-minute volume of up to three independently security-screened candidates. Entry is **NOT** made at first observation. One candidate is recorded as pending, and only a subsequent observation after >1 minute may enter at *that later observed quote* with adverse 1.5% entry friction. No missing quote is filled.

Per paper wallet:
- Starting cash $150; one open position maximum; risk stake at most $15 (10% of account or current balance, whichever less); no leverage, no averaging down; max one new position per 24h.
- Exit when observed price falls >=10%, rises >=25%, reaches two hours holding, liquidity falls below $5k, or sampled-equity peak lock activates. These are threshold triggers, **not hard loss caps or guaranteed exit prices**. Additional adverse 2%-5% exit impact is modeled; liquidity evacuation is modeled at an extra 75% impact.
- If an opened pool cannot be priced in two consecutive 15m observations, paper stake is conservatively written off as a 100% loss; it is never assumed to have escaped. Live fills could be even worse due to other obligations, and API outage is not equivalent to a contract rug.
- Original-style guard *targets*: stop new entries after an observed 2% day, 4% calendar-week, or 6% peak equity loss. These are sampled observations and cannot ensure a maximum loss.
- Market price and pool reserve are only indicative snapshots; there is no router simulation with signed swaps, token transfer tax, MEV, latency, actual priority fees, token-2022 runtime hooks, or true depth/execution.
- Net trade PnL includes modeled entry/exit costs and pessimistic liquidity impairment, never actual realized cash from any wallet.

## What can justify future promotion?

1. Prove the full observed-cohort coverage rate and retention of both failed and surviving observed pools over genuinely new future weeks, including timestamp gaps.
2. Obtain at least hundreds of eligible point-in-time signals with observed fillable exit paths, not 3–19 selective survivors.
3. Predeclare competing rules before collecting holdout samples; reject or disable models that fail stressed fee/slippage sensitivity and adverse-regime weeks.
4. Confirm that actual liquidity, contract-permission, exchange-route, and position sizing checks would permit transactions before any real-money request. None is authorized now.
5. The original ETH bot and its strategy remain separate. Do not blend ETH and Solana wallet results or double-count the same observed liquidity pool.

Do not claim any projected daily income from the incomplete June historical series or from an unseasoned forward paper account.
