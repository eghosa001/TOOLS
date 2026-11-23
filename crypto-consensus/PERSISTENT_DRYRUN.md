# Persistent ETH futures trading safety — deployment package

The checked-in package is **keyless DRY-RUN only**, not a real trading
account. It does not place orders or create actual exchange-side stops.

## Why exchange-side stops matter
Official Freqtrade/Kraken documentation confirms that Kraken Futures
supports mark-triggered stop-market orders in live trading. The
configuration in \`config.alwayson.dry.json\` selects those fields:
stoploss_on_exchange=true, stoploss=market, stoploss_price_type=mark,
stoploss_on_exchange_interval=60 and emergency_exit=market.

Dry-run simulates those orders and never obtains a real Kraken order ID.
The mock tests in \`stop_contract.py\` check what a live response would
need to prove: accepted order, reduce-only, opposite side, mark trigger,
same symbol, correct stop location and enough remaining quantity.
They DO NOT prove actual exchange acknowledgement. After any future
explicitly approved live entry, an authenticated read-only verification
of the exchange's returned stop and open position would be essential.

## Dedicated always-on host (not yet provisioned)
On a **separate owner-approved Docker host**, after verifying affordability
and availability:

    cd crypto-consensus
    docker compose -f docker-compose.paper.yml config
    docker compose -f docker-compose.paper.yml up -d
    docker compose -f docker-compose.paper.yml ps
    docker compose -f docker-compose.paper.yml logs --tail=80

The bot continuously observes the exchange's PUBLIC market data, uses
the \`GuardedConsensusETH\` 12h strategy at simulated 1x leverage,
one position max, and a $150 simulation wallet. Its SQLite database,
log and manual pause flag persist in a dedicated Docker volume
\`crypto_eth_paper_runtime\` across restarts. No network ports are published.
The separate Python sidecar monitors the Freqtrade heartbeat and
known stop/margin error messages. When a problem appears, it writes
\`PAUSE_ENTRIES\`, which rejects NEW simulated entries; the pause requires
a human operator to verify and clear. It does not cancel or fill
positions, and cannot substitute for real exchange-side stops.

To trigger a test PAUSE while running:

    docker compose -f docker-compose.paper.yml exec paper-watchdog \
      sh -c 'echo "operator test" > /freqtrade/runtime/PAUSE_ENTRIES'

To resume *after inspecting the logs, state, and safety conditions*:

    docker compose -f docker-compose.paper.yml exec paper-watchdog \
      rm /freqtrade/runtime/PAUSE_ENTRIES

No exchange credentials are used or read from environment. The startup
preflight rejects dry_run=false, non-$150 wallet, missing mark-stop-market
readiness fields and any nonblank exchange API keys.

## Hosting gate
A continuously running server cannot be created from a six-hour GitHub
Actions job or a periodically scheduled webhook. GitHub Actions are used
for validation and the existing periodic, less precise paper observer.
Railway's always-on Hobby plan entails recurring charges; Render Free
spins down. Existing user hosting for unrelated apps was intentionally
not altered. An owner-selected, affordable dedicated host with durable
storage is needed before this compose file can run 24/7.

## Current risk constraints
1% per position initial stop-distance budget; 1x notional; 2% daily,
4% weekly, 6% peak-drawdown **observed** circuit breakers in the
separate hourly paper observer; crash-entry filter and sticky
seven-day pauses. None guarantee real-money maximum losses, especially
in sudden price gaps, venue outages, and poor liquidity.
No funds are at risk in this package.

Sources: https://www.freqtrade.io/en/stable/stoploss/
https://www.freqtrade.io/en/latest/exchanges/
https://www.freqtrade.io/en/latest/docker_quickstart/
