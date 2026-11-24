# Fair seven-month comparison — ETH 1h vs 12h (May–November 2026)

**Validated historical simulation, not money earned or a prospective income forecast.**

Dates: **May 1–November 22 inclusive, 2026 (206 calendar days)**. Seven named
calendar months, November partial. Both independent Freqtrade strategy
wallets start with the same **$150** and operate at a maximum 1x leverage.

Full 8-case audit workflow:
https://github.com/eghosa001/TOOLS/actions/runs/45359217641

## Observed historical account results

| | Improved ETH 1h BTC + OI | Frozen original ETH 12h |
|---|---:|---:|
| Net account profit at 0.05% fee/side | **+$13.237822** | **+$17.027612** |
| Net simulated wallet return | **+8.8252%** | **+11.3517%** |
| Mean *net backtest profit* / calendar day | **+$0.064261** | **+$0.082658** |
| Full net profit at 0.15% adverse fee/side | **+$9.157803** | **+$16.701049** |
| Mean higher-fee profit per calendar day | **+$0.044455** | **+$0.081073** |
| Naturally closed trades (normal costs) | **56** | **7** |
| Days with positive naturally closed profit | **19 / 206** | **5 / 206** |
| Days with negative naturally closed profit | **36 / 206** | **2 / 206** |
| Days with no naturally closed trade | **151 / 206** | **199 / 206** |
| Positive months based on natural close PnL | **4 / 7** | **5 / 7** |
| Artificial forced terminal close PnL | **$0** | **+$5.138327** |
| Naturally closed-trade PnL excluding forced exit | **+$13.237822** | **+$11.889284** |
| Higher-fee natural close PnL excluding forced | **+$9.157803** | **+$11.602306** |
| Reported normal historical maximum account drawdown | **3.5043%** | **0.0997%** |
| Reported higher-fee historical maximum drawdown | **4.4937%** | **0.1270%** |

The original 12h model's apparently tiny backtester account drawdown
can miss large intratrade and intrabar adverse movements, particularly
on positions held across many calendar days. It is NOT proof of a
guaranteed 0.1% drawdown or less risk than the 1h model.

The reported 12h final wallet includes a **+$5.14** forced position
close at the backtest boundary. That is NOT a natural exit or a profit
that can be counted on. Subtracting this from the headline profit
produces closed-trade attribution only; it does NOT describe the
economic marked value of leaving the last position open.

## Actual seven-month consistency using natural closes

| Month 2026 | One hour, net USD | Twelve hours, net USD |
|---|---:|---:|
| May | −$0.093 | −$0.149 |
| June | +$2.567 | +$4.187 |
| July | −$2.263 | −$0.043 |
| August | +$5.351 | +$0.384 |
| September | +$2.179 | +$5.607 |
| October | −$2.381 | +$1.050 |
| November 1–22 | +$7.879 | +$0.854 |

These are **profits of naturally completed trades attributed to their
closing dates**. They are not monthly equity returns; positions can
cross month ends with unrealized profits/losses. Forced exit is omitted.

The one-hour strategy earned profits in only **4 of 7 calendar months**,
and only **19 days out of 206** had positive net closed-trade PnL.
It had **36 losing natural close days** and **151 days with no natural
close at all**. Thus $0.064/day is a net average divided by 206; the
strategy did NOT produce income of that amount every day.

## Concentration and fees

The 1h version's **largest naturally winning trade** made **+$8.062301**,
equal to ~61% of its entire +$13.237822 normal-fee net.
Under higher costs, its largest winner contributed **+$7.985456**,
roughly **87%** of the total net +$9.157803.
This makes its profitability dependent on finding rare larger trends.

In contrast, the 12h model makes very few decisions, but its late
artificial forced close contributed ~30% of the headline full net,
which also warrants skepticism.

The one-hour **unfiltered** 8/10 model actually LOST **−$8.735947**
(−5.824%) during these 206 days; the BTC regime gate improved it to
+$12.567270, and the combination of BTC + published ETH OI/funding
improved it further to +$13.237822. Thus any advantage in the
hourly candidate is mainly associated with the carefully tested
additional filters and cooldown, NOT merely with shorter candles.

At normal fees, the one-hour model has +$1.348538 more naturally
closed-trade profit than the 12h model after excluding the 12h
artificial closing contribution. Under higher 0.15% fees, it has
**−$2.444503 less** natural close profit. The reported end-account
return including the artificial closing favors 12h by $3.789790
normally and $7.543246 under higher costs.

## Decision

**No evidence of significantly higher or consistent daily income**
from faster trading. Historical scenario comparisons cannot establish
statistical significance or guaranteed future returns, especially
when one-hour model features were developed on 2026 price history.

Keep BOTH candidates as **independent, keyless paper research**:
- Maintain the existing 12h forward observer as comparison baseline.
- Continue the already-active ETH 1h BTC+OI forward-only observer and
  measure genuinely future trades after 24 November 2026.
- Record unrealized equity, gaps, funding, fees, actual signal
  availability and daily/weekly loss locks.
- Do not add live capital, relax leverage, or claim daily income
  before enough new genuine forward results exist.

Reports:
- [Structured 206-day audit](seven_month_profit_comparison.json)
- [Full monthly/daily comparison](seven_month_profit_comparison.md)
- [1h forward paper ledger](one_hour_forward_report.md)
