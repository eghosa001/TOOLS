# GBP/USD consensus engine rotation — research report, 23 November 2026

## Verification
- [Completed GitHub Actions run](https://github.com/eghosa001/TOOLS/actions/runs/45144690002)
- [Full JSON with validation candidates and every paper trade](https://github.com/eghosa001/TOOLS/actions/runs/45144690002/artifacts)
- Research implementations: [rotation study](./ensemble_rotation_research.py), [historical downloader](./ensemble_walkforward_fetch.cjs), [reused supervised model/execution engine](./ensemble_ml_backtest.py).
- Status: **research-only, not production-approved; no real-money execution**.

## Experiment (all choices historical)

Continue the user's $150 GBP/USD consensus trading program. From the previously inspected 16–20 November run, retain the four least-loss-making strategies: RBF SVM, Donchian breakout, Bollinger mean-reversion and volatility-conditioned momentum. Explore 16 further candidates. For each test week, train RBF on the prior historical slice, screen the 16 replacements over the immediately preceding 10 trading days (using net trading profit after costs), select 6 for the 10-engine ballot, and compare 6/10, 7/10, 8/10 voting thresholds. An alternative predeclared **quality gate** refuses ALL trades unless at least three selected replacements were profitable in validation and had at least 10 validation trades each.

Source: **210,236 actual, aligned Dukascopy GBP/USD M1 bid/ask historical candles**, June 1–November 20, 2026.

Fixed simulation: 1,000 GBP position, $150 initial account **independently reset for each of four test weeks**, candidate votes every five minutes in session, up to 15-minute holding, 8 pip protective stop, 12 pip target, bid/ask fills at modeled next-minute market open, maximum entry spread 1.5 pips, extra 0.2 pip roundtrip slippage and $0.06 roundtrip commission, $3 daily loss-pause based on closed trades. Conservative stop-first handling of intrabar stop/target ambiguity. Broker margin, intrabar realized slippage, financing, and stop execution are NOT verified.

## Four *exploratory* five-day test windows, 6-of-10 votes

| Test period | Trades | Net USD | Profit? |
| --- | ---: | ---: | --- |
| 7–11 Sep 2026 | 2 | +0.61 | Yes |
| 5–9 Oct 2026 | 2 | -1.19 | No |
| 2–6 Nov 2026 | 3 | +1.28 | Yes |
| 16–20 Nov 2026 | 2 | -1.12 | No |
| **Four independent $150 research accounts combined** | **9** | **-0.42** | **No** |

| Votes required | Trades across four windows | Wins | Net USD |
| --- | ---: | ---: | ---: |
| 6/10 | 9 | 3 | -0.42 |
| 7/10 | 1 | 0 | -0.83 |
| 8/10 | 1 | 0 | -0.83 |

### Screening results and safeguard

| Evaluation week | Positive screened replacements (meeting min-trade criteria) | Quality gate eligible? |
| --- | ---: | --- |
| Sep 7–11 | 0 | No |
| Oct 5–9 | 1 | No |
| Nov 2–6 | 0 | No |
| Nov 16–20 | 1 | No |

Under the stronger quality gate **all trades are skipped**; simulated net profit is **$0.00**, not a profitable edge. The gate protects the initial $150 by declining to trade while there is inadequate evidence for the replacements. This is important: selecting the 6 *least bad* candidate algorithms does not make them truly good.

Isolated candidate validation outcomes worth **further independent investigation only**, not immediate activation:
- *Session_Range_Fade*: +$0.54 across 61 validation trades, September 21–October 2; no demonstrated repeatability.
- *Compression_Break*: +$1.47 across 12 validation trades, November 2–13; extremely small evidence and the four week study has not established repeatability.
- On the other validation periods, the candidate algorithms failed the profit screen. Don't call any of these proven winners.

## Research honesty

1. The four retained incumbents were originally chosen *after* examining the November 16–20 outcomes. Those earlier November data informed system selection, so the September/October retrospective folds are **NOT a fully pristine untouched proof of profitability**. This is exploratory development, not forward evidence.
2. Past two-week screens and four separate five-day evaluation windows are too small to establish a Forex trading edge. Multiple testing can manufacture attractive-looking candidates.
3. Several strategies reuse the same historical price features and have correlated signals; the absolute voting count is not an independent probability estimate.
4. One-minute bid/ask bars are unsuitable for validating **seconds-long** scalping or true tick-level fill/latency.
5. The user’s $150 setup, margin and leverage for a 1,000 GBP position still require broker verification.
6. Both original ten-indicator and advanced ten-engine 16–20 November results were negative. This newest lineup has not become profitable under costs.

## Research decision and forward criterion

- **Do not activate any lineups for live trading.**
- The validated-only quality gate is the safe default: **SKIP** while fewer than 3 positive candidates meet their minimum sample requirement.
- Keep this report, evidence and exact code. Continue investigation using genuinely new source information (tick bid/ask, economic-event timing, optional independent order-flow data) rather than repeatedly optimizing this same dataset.
- Freeze next version before an actually future five-day paper-forward run; benchmark after transaction costs, drawdown, trade count, calibration, spread/stops and realistic microstructure before accepting any candidate.
