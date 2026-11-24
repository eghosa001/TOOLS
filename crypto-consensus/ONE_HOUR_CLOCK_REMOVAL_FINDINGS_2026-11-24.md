# ETH and SOL 1-hour trade-clock removal audit — 24 November 2026

**Result: removing only the normal 3-hour after-trade cooldown modestly improved historical ETH. Removing the 24-hour loss protection caused much worse losing streaks and did not improve robust profits.**

Verified 48 genuine Freqtrade simulations:
https://github.com/eghosa001/TOOLS/actions/runs/45422100103

All figures below are **historical simulated returns** on separate independent
$150 starting wallets, January 1–November 22, 2026, not actual earnings or
forward paper profits. Normal fees: 0.05% per side. Higher-cost independent
rerun: 0.15% per side (a rough friction proxy, not measured slippage).

## ETH, 1h, original 8/10 plus completed BTC + actual Kraken funding/OI

| Timed pause | Natural trade closes | Normal return | Normal profit on $150 | Higher-cost return | Higher-cost net on $150 | Longest historical losing streak | Higher-cost reported maximum DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3h after any trade + 24h after loss (existing) | 86 | +11.6487% | +$17.473052 | +6.7799% | +$10.169812 | 6 | 4.4652% |
| **No 3h after-trade wait; retain 24h after loss** | **88** | **+12.4861%** | **+$18.729136** | **+7.8940%** | **+$11.840967** | **6** | **4.2894%** |
| Retain 3h wait; remove 24h loss pause | 93 | +4.6808% | +$7.021213 | −0.1724% | −$0.258675 | 22 | 6.8985% |
| Remove BOTH timed pauses | 94 | +4.4740% | +$6.710969 | +7.9297% | +$11.894542 | 22 | 4.8660% |

The separately rerun high-fee ETH no-time-lock result happens to exceed
its normal-fee result. Freqtrade fee variation changes individual
positions and risk locks: this is **NOT** evidence that higher trading
fees are profitable. The normal-fee combined-removal case underperforms
the retained-pause case by ~$10.76 and runs through a **22-loss streak**.
That is a material risk deterioration.

Removing ONLY the normal 3h cooldown adds **two natural trade closes
across 326 calendar days**: about **0.043 more completed trades per
week**, not enough to approach a daily high-frequency target.
Historical ETH profit increases by **+$1.256084** normally and
**+$1.671155** in the higher-fee rerun. The original six-loss maximum
streak does not increase.

## SOL, 1h, original 9/10 plus BTC + genuine funding/OI

| Timed pause | Natural trade closes | Normal return | Normal profit on $150 | Higher-cost return | Higher-cost profit on $150 | Longest historical losing streak | Higher-cost reported max DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Both original pauses | 68 | +3.3374% | +$5.006143 | +0.8436% | +$1.265359 | 9 | 6.4392% |
| Remove 3h wait only | 68 | +3.3374% | +$5.006143 | +0.8436% | +$1.265359 | 9 | 6.4392% |
| Remove 24h loss pause only | 80 | −2.2013% | −$3.301894 | −5.1989% | −$7.798317 | 7 | 11.4636% |
| Remove BOTH timed pauses | 80 | −1.8077% | −$2.711616 | −4.4264% | −$6.639554 | 7 | 10.7210% |

Removing the normal three-hour wait had **no effect** on SOL trading
frequency. Removing the after-loss pause allowed **12 more trades** but
produced a losing account under BOTH fee models.

## What protections remained

To isolate timed cooldown changes, **all candidates retained**:

- Existing ETH 8/10 or SOL 9/10 agreement;
- Completed 12-hour BTC market regime and genuinely observed Kraken ETH/SOL
  funding + open-interest crowding veto;
- 1x maximum leverage, one position at a time, original ATR-based sizing
  and stop, original emergency market stop;
- 8%/12h and 15%/72h crash entry block;
- Freqtrade seven-day 4% MaxDrawdown guard.

A backtester MaxDrawdown *rule* is not a guaranteed 4% maximum loss:
actual reported results exceeded it (e.g., 6.90% on ETH and 11.46%
on SOL in higher-fee no-loss-pause simulations). The separate
prospective one-hour paper observer's 2% daily, 4% weekly, 6% peak
**observed-equity** limits were **not removed**.

The test measured three date periods—Jan–July, Aug–Nov, and continuous
Jan–Nov—at normal and higher costs for each coin and cooldown mode.
The code fails if the frozen old baseline cannot reproduce the exact
original returns/trade counts.

## Decision

**Research-screen pass: ETH no normal three-hour wait, with 24-hour
after-loss pause retained.** It adds 2 historical trades and ~$1.26
normal historical net with no longer normal-fee losing streak.
This is **not a proven high-frequency strategy**; historical period
was already studied extensively and may not repeat.

**Do not remove the 24-hour loss protection** on either coin under these
conditions; it causes 22 consecutive ETH losing trades and SOL
net losses. Removing both waits is NOT a credible way to achieve a lot
of profit-generating trades each day.

All experiments are research-only. The actual running one-hour paper
observer, the 12-hour comparison bot, their stored ledgers, and all real
exchange trade permissions remain unchanged. To reach a daily
multi-trade goal, test genuinely different short-horizon edge
hypotheses with realistic order-book/fee costs and shared risk limits,
not unlimited re-entry after each loss.

Full machine-readable backtest attribution and daily/weekly closes
are published by the matched workflow to:

- \`crypto-consensus/one_hour_no_time_locks_report.json\`
- \`crypto-consensus/one_hour_no_time_locks_report.md\`

Raw Freqtrade export artifact:
https://github.com/eghosa001/TOOLS/actions/runs/45422100103
