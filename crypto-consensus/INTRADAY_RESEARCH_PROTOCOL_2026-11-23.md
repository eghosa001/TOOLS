# Intraday ETH/SOL/BTC research protocol — 2026-11-23

## Research scope
Research only; no live orders, no paid OpenAI API calls and no changes to the 12-hour ETH production/paper rules.

On the same 114-day period (Aug 1–Nov 22, 2026), compare Ethereum, Solana and Bitcoin on Kraken Futures. Run the unchanged 12-hour protected strategy for a fair same-period reference, then 1-hour, 15-minute and 5-minute signals at both 8-of-10 and 9-of-10 indicator agreement.

Two protection modes: strict preserves 36-hour post-trade pause, seven-day loss pause and seven-day 4% modeled drawdown breaker; active *research only* shortens post-trade pause to 3 hours and a losing-trade pause to 24 hours but retains the 4% seven-day drawdown guard. The strict loss pause is measured in actual minutes and therefore cannot accidentally shrink to 70 minutes on a five-minute chart.

Every scenario begins with an independent paper wallet of $150, one maximum open position, 1x leverage, ATR stop and original position sizing and exit thresholds. Faster charts retain 12-hour, three-day and 48-hour price-crash lookback/block windows, converted correctly to each bar size.

Costs: 0.05% per side base modeled commission; all active configurations additionally tested at 0.15% per side (commission plus hypothetical friction/slippage). Exchange price/mark and funding histories are validated before a backtest is accepted. This cost stress is an assumption rather than a measurement of actual exchange spreads.

The audit captures gross opportunity frequency, actual closed trades per calendar day, net dollar and percent profit, modeled max account drawdown, wins, losses, maximum losing streak, average holding period, adverse close weeks, and net gains attributable to a forced end-of-test close. Closed-trade week P&L must not be reported as observed weekly account equity.

Results are separate, continuously modeled wallets per scenario, NOT a jointly deployed three-coin portfolio. The original hourly forward observer's separate 2%-daily/4%-weekly equity breakers are NOT reproduced by Freqtrade backtesting; no guarantee of exchange execution or strict real loss ceiling is implied. The sample was already partly studied, so none of these historical tests is new untouched out-of-sample evidence.

See the automatically generated intraday_research_report.md, intraday_research_report.json and the GitHub Action crypto-intraday-freqtrade-research.yml for measurements and exported trade evidence.

Selecting a winner must prioritize reliably positive after-friction net returns, controlled downside, organic exit quality and future-only forward paper evidence over raw trade count.