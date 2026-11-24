# ETH 1-hour forward-only paper trading — BTC regime + real futures positioning

**Implemented November 24, 2026. This is a simulated research ledger, not a live trade executor.**

The hourly observer is \`crypto-consensus/one_hour_forward_paper.py\`.
The workflow \`.github/workflows/crypto-one-hour-forward-paper.yml\` runs at
**HH:29 UTC** for each hourly ETH futures candle, when GitHub schedules
permit. It uses Kraken public feeds only and never submits an order.

## Why this test exists

Historical ETH 1h 8/10 plus completed BTC regime and genuine Kraken
funding/open-interest veto returned +11.6487% on one $150 simulated
Jan–Nov 2026 wallet, or +6.7799% in the 0.15%-per-side fee stress case.
It also lost money under higher fees during the Jan–Jul separately
restarted test and depended on a small number of large winners. It
did **not** meet all research acceptance criteria. These values
are **not projected forward profit and are not copied into the
forward account**. [Historical findings](ONE_HOUR_QUALITY_FINDINGS_2026-11-24.md)

## What an actual paper observation contains

- At most one **prospective trade decision** for each fully completed
  Kraken ETH/USD perpetual 1h candle; no replaying old price signals.
- BTC macro gate from completed BTC/USD perpetual **12h** EMA100 and
  momentum, only applied strictly after candle completion.
- Actual Kraken ETH futures hourly funding history with a **two-hour
  publication margin**; actual Kraken PF_ETHUSD four-hour open-interest
  bars with an **eight-hour publication margin**. Missing, out-of-order,
  stale or truncated sources fail closed.
- A verified public ETH order book. The simulated fill uses actual
  bid/ask depth and VWAP, then deducts an **additional 0.10%
  adverse-fill assumption per side and 0.05% commission per side**.
  Actual exchange latency and future slippage are not known.
- Mark candles and past published funding for approximate charges; no
  credit for possible funding receipts. An extra holding-charge
  buffer accounts for as-yet-unpublished funding at simulated close.
- A $150 independent simulated wallet, 1x maximum notional,
  max one open position, <=1% theoretical entry-stop distance
  capital risk *including estimated round-trip charges*, 3h pause
  after normal exits and 24h after losing exits.

### Account risk events

The observer revalues open simulated positions at available order-book
quotes and uses the existing \`risk_guards.py\` mechanisms:

| Observed condition | Automatic paper action |
|---|---|
| Equity down >=2% against last UTC daily starting observation | Close simulated position if open; pause entries until next UTC day |
| Equity down >=4% against weekly starting observation | Close simulated position if open; pause entries for 7 days |
| Equity down >=6% from highest *observed* equity | Close simulated position if open; permanent manual-reset lock |
| Crash, 8% over 12h or 15% over 72h | Refuse new positions for the elapsed-time 48h shock lock |
| Missed forward observation >2.5h | Never invent historical fills; close an open simulated position using the **new** observed book and suspend all new entries >=24h |
| Low liquidity, wide/missing/stale order book, missing exchange data | Refuse operation or entry; fail closed |

**These risk numbers are NOT guaranteed maximum future losses.**
The workflow is a discrete hourly observer, not a running exchange-held
stop order. Real intrahour moves and gaps can exceed the checks,
and historically touched stop fills are estimated without an order book
captured at the original stop time. When GitHub skips or delays a
scheduled run, the observer explicitly detects missed hours and suspends
new entries rather than silently inventing fills.

The simulated loss conditions also retain the preceding observed equity
across UTC midnight and Monday boundaries, so a loss during the
boundary hour cannot be hidden by resetting its risk basis to a
lower amount.

## Persistent evidence and decision criteria

Unlike historical backtest export, the newly initialized forward paper
wallet always starts with **$150 cash, zero open positions and zero
simulated closed trades**. It appends genuine subsequent observation
timestamps and simulated fills to:

- \`crypto-consensus/one_hour_forward_state.json\`
- \`crypto-consensus/one_hour_forward_report.json\`
- \`crypto-consensus/one_hour_forward_report.md\`

The first successfully timed *main-branch* run creates those files;
test-branch runs are **smoke-only** and do not write paper performance.
An unsuccessful API/data check cannot silently create profitable
history. GitHub Actions also saves inspection artifacts for 30 days.

Before any live-capital discussion, review at least **30–50 genuine
subsequent simulated closed trades** across multiple conditions,
cost and drawdown behavior versus the 12-hour original, days/hours
missed and stops after each risk lock. Do not automatically promote
this candidate merely because the old backtest had a positive headline.

No exchange credentials, private-account APIs, leverage adjustments,
paid ChatGPT signals, or real orders are used. The pre-existing
12h paper-trading task and its separate state are untouched.
