#!/usr/bin/env python3
"""Tick-level *paper* replay, no broker API. Causal quote snapshots and fee-aware exits.

All candidate signals are exploratory; some are correlated. Trade eligibility is
hard-disabled until independently validated replacements are approved, and even
then this module NEVER sends orders. A 'shadow trade' is a simulated outcome.
"""
from __future__ import annotations
import bisect
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

PAIR='GBPUSD'
START_EQUITY=150.
POSITION_GBP=1000
PIP=0.0001
COMMISSION_USD=0.06
EXTRA_SLIPPAGE_PIPS_ROUND_TRIP=0.2
SPREAD_MAX_PIPS=1.5
TICK_FRESH_MS=2000
MAX_ENTRY_DELAY_MS=4000
MIN_QUOTES_5MIN=70
MAX_RECENT_MEDIAN_SPREAD_PIPS=1.35
DAILY_STOP_USD=-3.
REPLAY_HORIZONS_SECONDS={30:(2.,2.),120:(4.,4.)}
TRESHOLDS=(6,7,8)
SIGNAL_NAMES=[
    'GBP_Momentum_1m','GBP_Momentum_5m','GBP_Range_Breakout',
    'Tick_Uptick_Balance','TopQuote_Volume_Imbalance',
    'EURUSD_Momentum_1m','EURGBP_Inverse_1m','EURGBP_Inverse_5m',
    'GBP_Price_Extreme_Fade','Tick_Activity_Burst'
]
# Prior rolling tests found NO 3 reliably validated replacements.
# Never fill missing slots automatically. Even positive backtest records do
# not remove the approval requirement.
APPROVED_REPLACEMENTS=()
MIN_VALIDATED_REPLACEMENTS=3
MARKET_DATA_START_HOUR=7
MARKET_DATA_END_HOUR=9

def sign(x, threshold=0.):
    if not math.isfinite(x):
        return 0
    return int(x>threshold)-int(x< -threshold)

def to_utc_ms(timestamp):
    return round(dt.datetime.fromisoformat(timestamp.replace('Z','+00:00')).timestamp()*1000)

def source_stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sorted_ticks(raw, name, day):
    rows=raw['instruments'][name]
    if not isinstance(rows,list) or len(rows)<500:
        raise ValueError('insufficient real tick records '+name)
    day_start=to_utc_ms(day+'T07:00:00Z')
    day_end=to_utc_ms(day+'T09:00:00Z')
    prior=None
    for r in rows:
        if not isinstance(r,list) or len(r)!=5:
            raise ValueError('incorrect tick schema '+name)
        t,ask,bid,ask_vol,bid_vol=r
        if isinstance(t,bool) or not isinstance(t,int) or not day_start<=t<day_end:
            raise ValueError('tick timestamp outside research window '+name)
        if prior is not None and t<prior:
            raise ValueError('unsorted tick timestamps')
        if not(all(math.isfinite(float(x)) for x in r[1:]) and
               0<bid<=ask and 0<=ask_vol and 0<=bid_vol):
            raise ValueError('invalid or crossed tick quotes')
        prior=t
    return rows

def snapshot(rows, times, t, lookback_ms, max_age_ms=TICK_FRESH_MS):
    # Only observations <= decision timestamp; never access future.
    e=bisect.bisect_right(times,t)
    if e<1 or t-times[e-1]>max_age_ms:
        return []
    s=bisect.bisect_left(times,t-lookback_ms,0,e)
    return rows[s:e]

def older_mid(rows,times,t,delta_ms):
    e=bisect.bisect_right(times,t-delta_ms)
    if not e or (t-delta_ms)-times[e-1]>5000:
        return None
    r=rows[e-1]
    return (r[1]+r[2])/2

def source_valid(calendar,day):
    if calendar.get('status')!='verified':
        return False,'CALENDAR_UNVERIFIED'
    if not calendar.get('source','').startswith('https://nfs.faireconomy.media/'):
        return False,'CALENDAR_SOURCE_INVALID'
    try:
        fetch=dt.datetime.fromisoformat(calendar['fetched_utc'].replace('Z','+00:00'))
        test=dt.datetime.fromisoformat(day+'T12:00:00+00:00')
    except (ValueError,KeyError,TypeError):
        return False,'CALENDAR_BAD_DATE'
    # Week feed allowed for this UTC week only. Avoid replaying on expired source.
    if fetch.date().isocalendar()[:2]!=test.date().isocalendar()[:2]:
        return False,'CALENDAR_OUTSIDE_WEEK'
    events=calendar.get('events',[])
    if not isinstance(events,list) or not events:
        return False,'CALENDAR_EMPTY'
    for ev in events:
        try:
            if ev['country'] not in ('GBP','USD'): return False,'CALENDAR_INVALID_CURRENCY'
            if ev['impact'] not in ('High','Medium','Holiday'):return False,'CALENDAR_INVALID_IMPACT'
            if not isinstance(ev['title'],str):return False,'CALENDAR_INVALID_EVENT'
            to_utc_ms(ev['utc'])
        except (KeyError,ValueError,TypeError):
            return False,'CALENDAR_MALFORMED'
    return True,'OK'

def is_news_blackout(calendar,day,decision_ms):
    for ev in calendar['events']:
        t=to_utc_ms(ev['utc'])
        if ev['impact']=='Holiday' and dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).date().isoformat()==day:
            return 'HOLIDAY_'+ev['country']
        width={'High':(45,30),'Medium':(20,20)}.get(ev['impact'])
        if width and t-width[0]*60000<=decision_ms<=t+width[1]*60000:
            return 'NEWS_'+ev['country']+'_'+ev['impact']
    return ''

def decision_signals(book, times, now):
    gbp=book['gbpusd']; gt=times['gbpusd']
    recent=snapshot(gbp,gt,now,5*60000)
    old=snapshot(gbp,gt,now,10*60000)
    if len(recent)<MIN_QUOTES_5MIN or len(old)<100:
        return {k:0 for k in SIGNAL_NAMES}, {'reason':'TOO_FEW_QUOTES'}
    last=recent[-1]
    mid=(last[1]+last[2])/2
    pipmoves={}
    for name,secs in (('m1',60),('m5',300),('m10',600)):
        earlier=older_mid(gbp,gt,now,secs*1000)
        pipmoves[name]=(mid-earlier)/PIP if earlier else 0.
    # Exclude latest 30 seconds from range reference to avoid contemporaneous
    # breakout masking; timestamps are causal.
    history=[(r[1]+r[2])/2 for r in old if r[0]<now-30000]
    price_signals={}
    price_signals['GBP_Momentum_1m']=sign(pipmoves['m1'],0.55)
    price_signals['GBP_Momentum_5m']=sign(pipmoves['m5'],1.2)
    price_signals['GBP_Range_Breakout']=(
        sign(mid-max(history),.12*PIP) if mid>max(history) else
        sign(mid-min(history),.12*PIP) if mid<min(history) else 0)
    micro=recent[-min(350,len(recent)):]
    mids=[(r[1]+r[2])/2 for r in micro]
    changes=[int(mids[j]>mids[j-1])-int(mids[j]<mids[j-1]) for j in range(1,len(mids))]
    price_signals['Tick_Uptick_Balance']=sign(sum(changes)/max(1,len(changes)),.08)
    liquidity=[(r[4]-r[3])/(r[4]+r[3]) for r in micro if r[4]+r[3]>0]
    price_signals['TopQuote_Volume_Imbalance']=sign(statistics.mean(liquidity),.12) if len(liquidity)>40 else 0
    for name,token,reverse,threshold,secs in [
        ('EURUSD_Momentum_1m','eurusd',1,.32,60),
        ('EURGBP_Inverse_1m','eurgbp',-1,.25,60),
        ('EURGBP_Inverse_5m','eurgbp',-1,.65,300)]:
        q=snapshot(book[token],times[token],now,5*60000)
        prior=older_mid(book[token],times[token],now,secs*1000)
        if not q or prior is None:
            price_signals[name]=0
        else:
            m=(q[-1][1]+q[-1][2])/2
            price_signals[name]=reverse*sign((m-prior)/PIP,threshold)
    reference=[(r[1]+r[2])/2 for r in recent]
    sigma=statistics.pstdev(reference)
    z=(mid-statistics.mean(reference))/sigma if sigma>=1e-10 else 0.
    price_signals['GBP_Price_Extreme_Fade']=-sign(z,1.6)
    burst=snapshot(gbp,gt,now,30000)
    previous=[r for r in recent if now-150000<=r[0]<now-30000]
    intensity=(len(burst)/30)/(len(previous)/120) if previous else 0.
    m30=older_mid(gbp,gt,now,30000)
    price_signals['Tick_Activity_Burst']=(sign((mid-m30)/PIP,.55)
            if m30 is not None and intensity>1.55 else 0)
    return price_signals,{
       'reason':'OK','last_quote_age_ms':now-last[0],
       'quote_count_5m':len(recent),
       'pips_1m':round(pipmoves['m1'],3),'pips_5m':round(pipmoves['m5'],3),
       'last_spread_pips':round((last[1]-last[2])/PIP,3),
       'median_spread_5m_pips':round(statistics.median((r[1]-r[2])/PIP for r in recent),3),
       'top_quote_volume_is_NOT_traded_order_flow':True
    }

def exits(rows,times,entry_idx,side,horizon_sec,stop_pips,target_pips):
    entry=rows[entry_idx]
    initial=entry[1] if side>0 else entry[2]
    end_at=entry[0]+horizon_sec*1000
    idx=entry_idx+1
    why='TIME_EXIT'
    while idx<len(rows) and rows[idx][0]<end_at:
        r=rows[idx]
        mark=r[2] if side>0 else r[1]
        diff=side*(mark-initial)/PIP
        if diff<=-stop_pips:
            why='STOP';break
        if diff>=target_pips:
            why='TAKE_PROFIT';break
        idx+=1
    if idx>=len(rows):
        return None
    mark=rows[idx][2] if side>0 else rows[idx][1]
    pnl=side*(mark-initial)*POSITION_GBP-COMMISSION_USD-EXTRA_SLIPPAGE_PIPS_ROUND_TRIP*PIP*POSITION_GBP
    return {'pnl_usd':round(pnl,5),'exit_utc':dt.datetime.fromtimestamp(rows[idx][0]/1000,dt.timezone.utc).isoformat(),
           'exit_tick_index':idx,'exit_reason':why}

def replay(raw,calendar,day,horizon_sec,threshold,eligible=False):
    book={name:sorted_ticks(raw,name,day) for name in ('gbpusd','eurusd','eurgbp')}
    ticks={name:[r[0] for r in q] for name,q in book.items()}
    valid,calstatus=source_valid(calendar,day)
    decisions=[]
    rejected={}
    equity=START_EQUITY
    peak=START_EQUITY
    drawdown=0.
    blocked=-1
    stop_pips,target_pips=REPLAY_HORIZONS_SECONDS[horizon_sec]
    start=to_utc_ms(day+'T07:15:00Z')
    stop=to_utc_ms(day+'T08:45:00Z')
    for moment in range(start,stop+1,5*60000):
        if not valid:
            why=calstatus
        else:
            why=is_news_blackout(calendar,day,moment)
        votes,features=decision_signals(book,ticks,moment)
        ups=sum(v==1 for v in votes.values())
        downs=sum(v==-1 for v in votes.values())
        side=1 if ups>=threshold and ups>downs else (-1 if downs>=threshold and downs>ups else 0)
        entry_deadline=moment+MAX_ENTRY_DELAY_MS
        entry_idx=bisect.bisect_left(ticks['gbpusd'],moment+500)
        entry=(book['gbpusd'][entry_idx] if entry_idx<len(book['gbpusd']) else None)
        if not why and not side:why='NOT_ENOUGH_AGREEMENT'
        if not why and features['reason']!='OK':why=features['reason']
        if not why and entry and entry[0]>entry_deadline:why='STALE_ENTRY'
        if not why and not entry:why='NO_ENTRY_TICK'
        if not why and blocked>=moment:why='POSITION_OVERLAP'
        if not why and equity-START_EQUITY<=DAILY_STOP_USD:why='DAILY_LOSS_PAUSE'
        if not why:
            spread=(entry[1]-entry[2])/PIP
            if spread<=0 or spread>SPREAD_MAX_PIPS:why='HIGH_SPREAD_AT_ENTRY'
            if features['median_spread_5m_pips']>MAX_RECENT_MEDIAN_SPREAD_PIPS:
                why='HIGH_RECENT_SPREAD'
        d={'decision_utc':dt.datetime.fromtimestamp(moment/1000,dt.timezone.utc).isoformat(),
            'buy':ups,'sell':downs,'neutral':10-ups-downs,
            'signal':('BUY' if side==1 else 'SELL' if side==-1 else 'SKIP'),
            'signals':votes,'market_features':features,'news_calendar_verified':valid}
        if why:
            d['status']='SKIP';d['reason']=why
            rejected[why]=rejected.get(why,0)+1
        else:
            settlement=exits(book['gbpusd'],ticks['gbpusd'],entry_idx,side,horizon_sec,stop_pips,target_pips)
            if settlement is None:
                d['status']='SKIP';d['reason']='INSUFFICIENT_EXIT_TICKS'
                rejected[d['reason']]=rejected.get(d['reason'],0)+1
            else:
                d['status']='SHADOW_SIMULATED'
                d['net_usd']=settlement['pnl_usd']
                d['entry_utc']=dt.datetime.fromtimestamp(entry[0]/1000,dt.timezone.utc).isoformat()
                d['entry_spread_pips']=round((entry[1]-entry[2])/PIP,3)
                d['exit_utc']=settlement['exit_utc']
                d['exit_reason']=settlement['exit_reason']
                equity+=settlement['pnl_usd']
                peak=max(peak,equity)
                drawdown=max(drawdown,peak-equity)
                blocked=ticks['gbpusd'][settlement['exit_tick_index']]
        d['eligible_for_real_orders']=False
        # Must not let the ability to run shadow simulation imply approval.
        d['quality_gate']='PASS' if eligible else 'FAILED_NO_VALIDATED_REPLACEMENTS'
        decisions.append(d)
    traded=[d for d in decisions if d['status']=='SHADOW_SIMULATED']
    return {'threshold':threshold,'hold_seconds':horizon_sec,
      'calendar_verified':valid,'calendar_status':calstatus,
      'quality_gate':'PASS' if eligible else 'FAILED_NO_VALIDATED_REPLACEMENTS',
      'paper_only':True,'live_order_count':0,'signals_evaluated':len(decisions),
      'shadow_trades':len(traded),'shadow_winners':sum(d['net_usd']>0 for d in traded),
      'shadow_net_usd':round(equity-START_EQUITY,5),'shadow_final_balance_usd':round(equity,5),
      'shadow_closed_trade_max_drawdown_usd':round(drawdown,5),
      'rejections':rejected,'decisions':decisions}

def main():
    day=os.environ.get('TARGET_DAY','2026-11-23')
    folder=Path('forex-gpt/.tmp')
    raw=json.loads((folder/('tick_context_'+day+'.json')).read_text())
    calendar=json.loads((folder/('macro_calendar_'+day+'.json')).read_text())
    if raw.get('date')!=day or raw.get('provider')!='dukascopy-node@1.51.1':
        raise ValueError('Wrong tick source/day')
    if calendar.get('target_day_utc')!=day:
        raise ValueError('wrong calendar date')
    qualified=len(APPROVED_REPLACEMENTS)
    eligible=qualified>=MIN_VALIDATED_REPLACEMENTS
    reports={}
    for hold in REPLAY_HORIZONS_SECONDS:
        for threshold in TRESHOLDS:
            r=replay(raw,calendar,day,hold,threshold,eligible=eligible)
            reports[str(hold)+'s_'+str(threshold)+'of10']=r
            print('TICK_SHADOW',day,hold,'seconds',threshold,'votes',json.dumps({
                k:r[k] for k in r if k!='decisions'},sort_keys=True),flush=True)
    payload={
        'test_day':day,'status':'read-only actual Dukascopy bid/ask tick replay, not broker fills',
        'frozen_rule_names':SIGNAL_NAMES,
        'experimental':'Signals are causal but correlated; neither independent nor validated as profitable',
        'eligible_replacements':list(APPROVED_REPLACEMENTS),
        'min_approved_replacements':MIN_VALIDATED_REPLACEMENTS,
        'real_money_orders':0,'no_order_api_code':True,
        'starting_account_usd':START_EQUITY,'position_gbp_units':POSITION_GBP,
        'calendar_source':calendar['source'],'calendar_snapshot_time':calendar['fetched_utc'],
        'calendar_status':calendar.get('status'),
        'tick_counts':{k:len(v) for k,v in raw['instruments'].items()},
        'assumptions':{'commission_rt_usd':COMMISSION_USD,'extra_slippage_rt_pips':EXTRA_SLIPPAGE_PIPS_ROUND_TRIP,
          'spread':'actual Dukascopy bid/ask ticks','max_spread_pips':SPREAD_MAX_PIPS,
          'execution_delay_minimum_ms':500,'exit':'first observed tick after stop/target or time horizon'},
        'limitations':['Code fixed before future observations is not same as broker paper order confirmation',
           'Dukascopy top of book can differ from user broker and gives quote-side volumes, NOT executed order flow',
           'Calendar snapshot could have been revised relative to historical events; only use prospectively',
           'Single session, small sample; stop execution is idealized and quote feed may lack all executable prices',
           'Several signal families are correlated; vote share is not independent evidence of profitability',
           'All outcomes simulated and real order placement permanently disabled'],
        'results':reports}
    blob=json.dumps(payload,sort_keys=True,indent=2)+'\n'
    dst=folder/('tick_shadow_result_'+day+'.json')
    dst.write_text(blob)
    print('TICK_REPORT_SHA256',hashlib.sha256(blob.encode()).hexdigest())
    print('TICK_RESULT_FILE',dst,'LIVE_ORDER_COUNT',0,'QUALITY_PASS',eligible,flush=True)
if __name__=='__main__':
    main()
