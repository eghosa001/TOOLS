# Crypto consensus — frozen research / paper only

Isolated from the Forex experiment and all existing workflows. **No live orders and no exchange credentials.**

## Frozen hypothesis
ETH/USDT:USDT Binance USDT perpetual, 12h completed candles, ten indicator votes
(EMA20/50, MACD, Supertrend, Donchian30, Ichimoku, DMI, RSI50,
Bollinger reversion, Stochastic, OBV). Enter long at >=8 bullish votes,
short at <=2; exit long at <=4, exit short at >=6. One position, 1x
notional exposure, 2% *initial stop-distance risk budget*, 2.5x ATR14
trailing stop, seven-day pause after a losing close.

The original exploratory simulation is **not independently verified**.
In particular, the Freqtrade port is not the same execution engine:
protection timing, trailing-stop order, funding, fills, data warmup,
precision and exchange minimum notional can change trades. The earlier
+62.22% result must **not** be imported as a Freqtrade result.

## Tests
The workflow named **Crypto consensus - independent Freqtrade audit**
runs fast Python indicator/causality tests, then a separate Freqtrade
historical audit using an official Freqtrade image and downloaded *actual*
futures market, mark and funding candles. If data downloading, funding,
lookahead-analysis or recursive-analysis fails, the audit stays FAILED.
No synthetic funding or silently defaulted fee data is allowed.

This is a new strategy implementation: Freqtrade itself contains open-source
infrastructure but the ten signal rules are adaptations of public-domain
indicator ideas, not ten separately validated open-source trading bots.

To reproduce inside a local Docker environment (no key is needed for backtests):

    docker run --rm -v "$PWD/crypto-consensus:/freqtrade/crypto-consensus" \
      -v "$PWD/crypto-consensus/user_data:/freqtrade/user_data" \
      -e PYTHONPATH=/freqtrade/crypto-consensus freqtradeorg/freqtrade:stable \
      download-data -c /freqtrade/user_data/config.dry.json \
      --pairs "ETH/USDT:USDT" --timeframes 12h --trading-mode futures \
      --timerange 20250101-20261101

Then run backtesting, lookahead-analysis and recursive-analysis as defined in
`.github/workflows/crypto-consensus-freqtrade-audit.yml`.

**Forward execution:** genuine Freqtrade dry-run requires an always-on process
with persistent SQLite state, exchange connectivity and actual exchange
minimum-size validation. A scheduled GitHub Actions backtest is not a
continuous dry-run. Never switch dry_run to false. No live trading is
authorized. See the audit workflow results before starting a forward test.

Research controls: do not tune against the held-out 2025-2026 block;
collect forward paper trades, include fees/funding/slippage, inspect
two-week windows and stopping behavior, and reject any lookahead or
recursive-signal discrepancy.


## Cross-venue independent audit
Kraken Futures ETH/USD:USD historical audit uses 2025-12-01 through
2026-10-31 (both inclusive) because Kraken public funding records start
2025-11-19. The workflow explicitly requires both hourly funding and
hourly mark prices to cover the full testing period without gaps.

The Freqtrade result of +7.95% on $150 (17 trades, 8.43% max drawdown)
is one exploratory cross-venue sample and is NOT an expected live return.
The earlier +8.49% broad-range result was invalid as a full-funded
comparison because funding coverage started late.

## Public Kraken forward-only paper ledger
`forward_paper.py` is a separate periodic, modeled paper account.
It uses PUBLIC CCXT Kraken Futures market candles, completed 12-hour
consensus signals, hourly stop-touch observations, approximate mark-price
funding, a $150 mock wallet, and strict 1x/2% risk sizing.
`--smoke` verifies real public feeds without writing state.

The scheduled GitHub Action only runs on the repository DEFAULT branch.
Branch builds smoke-test instead. State lives in
`crypto-consensus/forward_paper_state.json` and is committed to main
when a scheduled observation succeeds. Missed observations, unavailable
feeds or funding gaps fail closed and require reconciliation.

The scheduled observer is NOT the always-on Freqtrade dry-run. It can
miss intrahour fills and funding marks are approximations; real paper
execution quality requires an always-on runner. It never sends orders,
cannot be switched to live trading by configuration, and holds no keys.
