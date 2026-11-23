#!/usr/bin/env python3
"""Predeclared, retrospective CFTC GBP/USD regime filter experiment.

Control: same weekly CFTC net-position-change direction / >=0.005 threshold,
10:00 UTC entry, 1,000 GBP units, five calendar days; H1 Dukascopy bid/ask.
Variants do NOT change direction, size, timing, or exit. No broker or GPT.
All filters are computed using past completed H1 candles before each entry.
"""
from __future__ import annotations
import bisect
import datetime as dt
import json
import math
import statistics
import urllib.parse
import urllib.request
from pathlib import Path

BASE=Path(__file__).resolve().parent
QUOTES=BASE/'.tmp'/'regime_h1_quotes.json'
RESULT=BASE/'.tmp'/'regime_results.json'
UTC=dt.timezone.utc
CUTOFF=dt.datetime(2026,11,23,tzinfo=UTC)
PIP=.0001
UNITS=1000
SLIPPAGE_PIPS=.2
COMMISSION_USD=.06
FUNDING_USD_5D=.25
CFTC_URL='https://publicreporting.cftc.gov/resource/gpe5-46if.json'
VOL_RATIO_LIMIT=1.5
SIGNAL_THRESHOLD=.005
PREV_HOURS=1200
NEAR_HOURS=120

def fetch_cftc():
    params=urllib.parse.urlencode({
      '$where':"cftc_contract_market_code = '096742'",
      '$order':'report_date_as_yyyy_mm_dd DESC',
      '$limit':450
    })
    req=urllib.request.Request(CFTC_URL+'?'+params,headers={
      'Accept':'application/json','User-Agent':'ReadOnlyCFTCRegimeResearch/1.0'
    })
    with urllib.request.urlopen(req,timeout=45) as response:
      rows=json.loads(response.read(2000000))
    if not isinstance(rows,list) or len(rows)<300:
      raise ValueError('Insufficient authentic CFTC historical positioning reports')
    unique={}
    for r in rows:
      d=dt.date.fromisoformat(str(r['report_date_as_yyyy_mm_dd'])[:10])
      if str(r.get('cftc_contract_market_code'))!='096742':
        raise ValueError('Unexpected CFTC contract code')
      # Official exceptional calendar dates must not be invented as Tuesdays.
      # Exclude them consistently from this fixed Wednesday-entry experiment.
      if d.weekday()!=1:
        continue
      if d in unique:
        raise ValueError('Duplicate CFTC report date; reject ambiguous rows')
      oi=float(r['open_interest_all'])
      long=float(r['lev_money_positions_long'])
      short=float(r['lev_money_positions_short'])
      if not all(map(math.isfinite,(oi,long,short))) or oi<=1000 or min(long,short)<0:
        raise ValueError('Invalid CFTC positioning')
      unique[d]=(long-short)/oi
    return sorted(unique.items())

def quotes_load():
    raw=json.loads(QUOTES.read_text())
    if (raw.get('symbol'),raw.get('timeframe'),raw.get('cutoff_utc'))!=(
         'gbpusd','h1','2026-11-23T00:00:00Z'):
      raise ValueError('Incorrect or stale historical quote source')
    bid={int(r[0]):r for r in raw['sides']['bid']}
    ask={int(r[0]):r for r in raw['sides']['ask']}
    stamps=sorted(set(bid)&set(ask))
    if len(stamps)<34000:
      raise ValueError('Missing multi-year aligned bid/ask H1 data')
    for t in stamps:
      b,a=bid[t],ask[t]
      if t+3600000>int(CUTOFF.timestamp()*1000):
        raise ValueError('Future or incomplete quote')
      if not (0<b[1]<=a[1] and b[2]>=max(b[1],b[4],b[3])
         and a[2]>=max(a[1],a[4],a[3])
         and b[3]<=min(b[1],b[4]) and a[3]<=min(a[1],a[4])):
        raise ValueError('Invalid quote candle '+str(t))
    return bid,ask,stamps

def create_trades(reports,bid,ask,stamps):
    out=[]
    counts={'below_position_change_threshold':0,'not_matured':0,
      'incomplete_price_or_warmup':0,'spread_too_high':0,
      'no_prior_week':0}
    mids={t:(bid[t][4]+ask[t][4])/2 for t in stamps}
    ranges={t:((bid[t][2]+ask[t][2])-(bid[t][3]+ask[t][3]))/2/PIP for t in stamps}
    by_index={t:i for i,t in enumerate(stamps)}
    for k in range(1,len(reports)):
      current,net=reports[k]
      prev,previous=reports[k-1]
      if not 7<=(current-prev).days<=14:
        counts['no_prior_week']+=1
        continue
      change=net-previous
      if abs(change)<SIGNAL_THRESHOLD:
        counts['below_position_change_threshold']+=1
        continue
      entry=dt.datetime.combine(current+dt.timedelta(days=8),dt.time(10),UTC)
      exit_=entry+dt.timedelta(days=5)
      if entry.year<2020:continue
      if exit_>CUTOFF:
        counts['not_matured']+=1
        continue
      em=int(entry.timestamp()*1000)
      xm=int(exit_.timestamp()*1000)
      i=bisect.bisect_left(stamps,em)
      if em not in by_index or xm not in by_index or i<PREV_HOURS+NEAR_HOURS+1:
        counts['incomplete_price_or_warmup']+=1
        continue
      spread=(ask[em][1]-bid[em][1])/PIP
      if not 0<spread<=2.0:
        counts['spread_too_high']+=1
        continue
      old=stamps[i-PREV_HOURS-NEAR_HOURS:i-NEAR_HOURS]
      recent=stamps[i-NEAR_HOURS:i]
      if len(old)!=PREV_HOURS or len(recent)!=NEAR_HOURS:
        counts['incomplete_price_or_warmup']+=1
        continue
      # All historical bars above closed BEFORE 10:00 UTC entry.
      vol_ratio=statistics.median(ranges[t] for t in recent)/max(
        .000000001,statistics.median(ranges[t] for t in old))
      movement=mids[recent[-1]]-mids[stamps[i-NEAR_HOURS-1]]
      direction=1 if change>0 else -1
      aligned=(direction*movement)>0
      enter=ask[em][1] if direction>0 else bid[em][1]
      leave=bid[xm][1] if direction>0 else ask[xm][1]
      pnl=direction*(leave-enter)*UNITS-PIP*SLIPPAGE_PIPS*UNITS-COMMISSION_USD-FUNDING_USD_5D
      out.append({'date':entry.date().isoformat(),'direction':'BUY' if direction>0 else 'SELL',
                  'net_usd':round(pnl,5),'volatility_ratio':round(vol_ratio,6),
                  'trend_aligned':bool(aligned),'cftc_change':round(change,7),
                  'entry_spread_pips':round(spread,4)})
    return sorted(out,key=lambda t:t['date']),counts

def calc(rows,condition):
    control=[r['net_usd'] for r in rows]
    accepted=[r['net_usd'] if condition(r) else 0 for r in rows]
    taken=[r['net_usd'] for r in rows if condition(r)]
    blocked=[r['net_usd'] for r in rows if not condition(r)]
    def drawdown(x):
      peak=equity=dd=0.
      for n in x:
        equity+=n
        peak=max(peak,equity)
        dd=max(dd,peak-equity)
      return round(dd,4)
    gross_win=sum(max(0,x) for x in taken)
    gross_loss=-sum(min(0,x) for x in taken)
    return {'opportunities':len(rows),'taken':len(taken),'skipped':len(blocked),
            'net_usd':round(sum(accepted),4),
            'gross_losses_usd':round(gross_loss,4),
            'worst_trade_usd':round(min([0]+taken),4),
            'closed_equity_drawdown_usd':drawdown(accepted),
            'win_rate_taken_pct':round(100*sum(x>0 for x in taken)/len(taken),2) if taken else None,
            'profit_factor':round(gross_win/gross_loss,3) if gross_loss else None,
            'skipped_winners':sum(x>0 for x in blocked),
            'skipped_losers':sum(x<0 for x in blocked),
            'skipped_winning_usd':round(sum(x for x in blocked if x>0),4),
            'avoided_losing_usd':round(-sum(x for x in blocked if x<0),4),
            'net_delta_vs_control_usd':round(sum(accepted)-sum(control),4)}
def evaluate(rows):
    fn={
      'CONTROL_all_eligible':lambda r:True,
      'AVOID_volatility_spike':lambda r:r['volatility_ratio']<=VOL_RATIO_LIMIT,
      'REQUIRE_5day_trend_alignment':lambda r:r['trend_aligned'],
      'COMBINE_both_filters':lambda r:r['volatility_ratio']<=VOL_RATIO_LIMIT and r['trend_aligned']
    }
    return {name:calc(rows,f) for name,f in fn.items()}
def main():
    reports=fetch_cftc()
    bid,ask,stamps=quotes_load()
    trades,exclusions=create_trades(reports,bid,ask,stamps)
    if len(trades)<180:
      raise ValueError('Insufficient complete matched trades; no profitability conclusion')
    years={
     '2020-2023_development':lambda y:2020<=y<=2023,
     '2024-2025_later_period':lambda y:2024<=y<=2025,
     '2026_latest_retro':lambda y:y==2026,
     '2020-2026_all':lambda y:2020<=y<=2026
    }
    by_period={period:evaluate([r for r in trades if pred(int(r['date'][:4]))])
               for period,pred in years.items()}
    result={
      'study':'READ ONLY fixed-hypothesis comparison to original CFTC 5-day GBPUSD CPU strategy',
      'price_source':'Dukascopy bid/ask H1; NOT actual broker fills',
      'cftc_source':CFTC_URL,
      'cutoff_utc':CUTOFF.isoformat(),
      'method':'CFTC report Tue+8 calendar days, Wed 10UTC, abs(change)>=.005; 1000 GBP 5-calendar-day hold',
      'signal_maturity':'past-only CFTC; 120 completed H1 bars + prior 1200 completed H1 bars for volatility',
      'pre_registered_candidate_rules':{
        'volatility':f'avoid when median range of last 120 H1 bars > {VOL_RATIO_LIMIT}x median previous 1200 H1 bars',
        'trend':'take when prior 120 H1-bar GBP/USD momentum agrees with CFTC signal',
        'combined':'both filters required'
      },
      'cost_assumptions':{'spread':'historical Dukascopy bid/ask',
         'commission_roundtrip_usd':COMMISSION_USD,
         'added_slippage_roundtrip_pips':SLIPPAGE_PIPS,
         'illustrative_funding_5d_usd':FUNDING_USD_5D},
      'safety':'zero broker orders, no GPT inference; no alteration to existing strategy',
      'limitations':['retrospective tests including previously seen 2026 outcomes',
         'execution costs and swap rates not verified with broker',
         'closed-trade drawdown only; not intra-trade equity drawdown',
         'fixed regime rules are hypotheses, not independently validated prospective alpha'],
      'total_weekly_reports':len(reports),'total_matched_trades':len(trades),
      'excluded':exclusions,'results':by_period,'individual_trades':trades
    }
    RESULT.parent.mkdir(parents=True,exist_ok=True)
    RESULT.write_text(json.dumps(result,indent=2)+'\n')
    print('REGIME_SAMPLE',len(reports),'official_CFTC_reports',
          len(stamps),'aligned_H1_candles',len(trades),'matched_trades',flush=True)
    print('REGIME_EXCLUSIONS',json.dumps(exclusions),flush=True)
    print('REGIME_RESULTS',json.dumps(by_period,sort_keys=True),flush=True)
    print('REGIME_REPORT',str(RESULT),flush=True)
if __name__=='__main__':
  main()
