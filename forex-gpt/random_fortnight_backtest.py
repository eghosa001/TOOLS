#!/usr/bin/env python3
"""Five preregistered random 2-week Forex samples: tick-level quote-only research.
Read-only historical tick replay with the EXACT existing causal signal and exit
functions; no calendar fabrication and no real broker orders.

Unlike the prospectively frozen workflow, this exploratory exercise deliberately
omits the historic macro-event veto: archived as-of-event calendars for years
2022–2026 are not present. Its result cannot approve live trading.
"""
from __future__ import annotations
import bisect
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import tick_paper_replay as fx

ROOT=Path('forex-gpt/.tmp/random_fortnights')
MANIFEST=ROOT/'manifest.json'
OUTPUT=ROOT/'random_fortnight_results.json'
HORIZONS=(30,120)
VOTES=(6,7,8)
EXPECTED_WINDOWS=(
 ('2022-10-17','2022-10-28'),
 ('2023-09-11','2023-09-22'),
 ('2024-04-15','2024-04-26'),
 ('2025-04-21','2025-05-02'),
 ('2026-10-05','2026-10-16')
)

def iso(ms):
    return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).isoformat()

def load_day(date,manifest):
    f=ROOT/(date+'.json')
    if not f.is_file():
        raise FileNotFoundError('No real market file '+date)
    bytes_=f.read_bytes()
    recs={x['day']:x for x in manifest['days']}
    if date not in recs:raise RuntimeError('Missing quote inventory '+date)
    digest=hashlib.sha256(bytes_).hexdigest()
    if digest!=recs[date]['sha256']:raise ValueError('Quote checksum mismatch '+date)
    doc=json.loads(bytes_)
    if doc.get('date')!=date or doc.get('provider')!='dukascopy-node@1.51.1':
        raise ValueError('Wrong quote data '+date)
    return doc

def decisions_for_day(raw,day):
    book={name:fx.sorted_ticks(raw,name,day) for name in ('gbpusd','eurusd','eurgbp')}
    clocks={k:[r[0] for r in v] for k,v in book.items()}
    decisions=[]
    for now in range(fx.to_utc_ms(day+'T07:15:00Z'),
                     fx.to_utc_ms(day+'T08:45:00Z')+1,5*60000):
        votes,features=fx.decision_signals(book,clocks,now)
        if set(votes)!=set(fx.SIGNAL_NAMES):
            raise ValueError('Unexpected vote set')
        family=fx.diverse_family_votes(votes)
        buys=sum(v==1 for v in votes.values())
        sells=sum(v==-1 for v in votes.values())
        entry_i=bisect.bisect_left(clocks['gbpusd'],now+500)
        entry=book['gbpusd'][entry_i] if entry_i<len(book['gbpusd']) else None
        decisions.append({'now':now,'votes':votes,'family':family,
          'buy':buys,'sell':sells,'features':features,'entry_idx':entry_i,
          'entry':entry})
    if len(decisions)!=19:raise RuntimeError('Incomplete research decision grid')
    return book,clocks,decisions

def per_day(book,clocks,decisions,threshold,hold):
    assert threshold in VOTES and hold in HORIZONS
    capital=fx.START_EQUITY
    peak=capital
    max_dd=0.
    blocked_through=-1
    skip=collections.Counter()
    trades=[]
    stop,target=fx.REPLAY_HORIZONS_SECONDS[hold]
    for d in decisions:
        now=d['now']
        side=1 if d['buy']>=threshold and d['buy']>d['sell'] else (
            -1 if d['sell']>=threshold and d['sell']>d['buy'] else 0)
        support=sum(v==side for v in d['family'].values()) if side else 0
        entry=d['entry']
        reason=None
        if not side:reason='NOT_ENOUGH_AGREEMENT'
        elif support<fx.MIN_DIVERSE_FAMILIES:reason='CORRELATED_GROUP_VETO'
        elif d['features'].get('reason')!='OK':reason=d['features'].get('reason','BAD_FEATURES')
        elif entry is None:reason='MISSING_ENTRY'
        elif entry[0]>now+fx.MAX_ENTRY_DELAY_MS:reason='ENTRY_TOO_STALE'
        elif blocked_through>=now:reason='OVERLAP'
        elif capital-fx.START_EQUITY<=fx.DAILY_STOP_USD:reason='DAILY_STOP'
        else:
            spread=(entry[1]-entry[2])/fx.PIP
            if not(0<spread<=fx.SPREAD_MAX_PIPS):reason='ENTRY_SPREAD_VETO'
            elif d['features']['median_spread_5m_pips']>fx.MAX_RECENT_MEDIAN_SPREAD_PIPS:
                reason='RECENT_SPREAD_VETO'
        if reason:
            skip[reason]+=1
            continue
        settlement=fx.exits(book['gbpusd'],clocks['gbpusd'],d['entry_idx'],side,
                            hold,stop,target)
        if settlement is None:
            skip['MISSING_EXIT']+=1
            continue
        pnl=float(settlement['pnl_usd'])
        capital+=pnl
        peak=max(peak,capital)
        max_dd=max(max_dd,peak-capital)
        blocked_through=book['gbpusd'][settlement['exit_tick_index']][0]
        trades.append({'utc':iso(now),'side':'BUY' if side>0 else 'SELL',
             'agreement':d['buy'] if side>0 else d['sell'],
             'family_agreement':support,'pnl_usd':pnl,
             'entry_spread_pips':round(float(spread),4),
             'entry_utc':iso(entry[0]),
             'exit_utc':settlement['exit_utc'],
             'exit_reason':settlement['exit_reason']})
    return {'net_usd':round(capital-fx.START_EQUITY,5),
        'trades':len(trades),'wins':sum(t['pnl_usd']>0 for t in trades),
        'losses':sum(t['pnl_usd']<0 for t in trades),
        'closed_trade_max_drawdown_usd':round(max_dd,5),
        'rejected':dict(skip),'trade_details':trades}

def main():
    manifest=json.loads(MANIFEST.read_text())
    if manifest.get('random_seed')!=20261123 or manifest.get('historical_news_calendar_available') is not False:
        raise ValueError('Wrong test manifest')
    if [(w['start'],w['end']) for w in manifest['windows']]!=list(EXPECTED_WINDOWS):
        raise ValueError('Different or cherry-picked windows')
    if len(manifest['windows'])!=5:raise ValueError('Unexpected period count')
    results=[]
    all_missing=[]
    for number,w in enumerate(manifest['windows'],1):
        days=w['days']
        if len(days)!=10:raise ValueError('A window must have ten weekdays')
        stats={(h,t):{'trades':0,'wins':0,'losses':0,'net_usd':0.,
                       'worst_max_drawdown_day':0.,'days_profitable':0}
              for h in HORIZONS for t in VOTES}
        dayrows=[]
        for day in days:
            try:
                raw=load_day(day,manifest)
                book,clocks,decisions=decisions_for_day(raw,day)
            except (FileNotFoundError,ValueError,RuntimeError,KeyError) as e:
                all_missing.append({'day':day,'reason':str(e)})
                dayrows.append({'day':day,'status':'MISSING_DATA','reason':str(e)})
                continue
            data={}
            for h in HORIZONS:
                for t in VOTES:
                    result=per_day(book,clocks,decisions,t,h)
                    data[f'{h}s_{t}of10']=result
                    s=stats[(h,t)]
                    s['trades']+=result['trades']
                    s['wins']+=result['wins']
                    s['losses']+=result['losses']
                    s['net_usd']+=result['net_usd']
                    s['worst_max_drawdown_day']=max(s['worst_max_drawdown_day'],
                                                     result['closed_trade_max_drawdown_usd'])
                    s['days_profitable']+=int(result['net_usd']>0)
            dayrows.append({'day':day,'status':'COMPLETE',
                      'tick_counts':{k:len(v) for k,v in book.items()},
                      'decisions':19,'results':data})
            print('HISTORIC_DAY',day,json.dumps({
                k:{'trades':v['trades'],'net_usd':v['net_usd']} for k,v in data.items()}),flush=True)
        for s in stats.values():
            s['net_usd']=round(s['net_usd'],5)
            s['hypothetical_final_balance_usd']=round(150+s['net_usd'],5)
        sums={f'{h}s_{t}of10':stats[(h,t)] for h in HORIZONS for t in VOTES}
        result={'period':number,'start':w['start'],'end':w['end'],'source_days_complete':
                 sum(d['status']=='COMPLETE' for d in dayrows),'source_days_expected':10,
                'status':'COMPLETE' if all(d['status']=='COMPLETE' for d in dayrows) else 'INCOMPLETE',
                'summaries':sums,'daily':dayrows}
        results.append(result)
        print('HISTORICAL_FORTNIGHT_'+str(number),json.dumps({'start':w['start'],
            'end':w['end'],'days':result['source_days_complete'],'status':result['status'],
            'summary':sums},sort_keys=True),flush=True)
    totals={}
    for h in HORIZONS:
        for t in VOTES:
            key=f'{h}s_{t}of10'
            vals=[r['summaries'][key] for r in results if r['status']=='COMPLETE']
            totals[key]={
              'complete_fortnights':len(vals),'trades':sum(v['trades'] for v in vals),
              'wins':sum(v['wins'] for v in vals),'losses':sum(v['losses'] for v in vals),
              'net_usd':round(sum(v['net_usd'] for v in vals),5),
              'profitable_fortnights':sum(v['net_usd']>0 for v in vals),
              'flat_fortnights':sum(v['net_usd']==0 for v in vals),
              'losing_fortnights':sum(v['net_usd']<0 for v in vals),
              'consistent_profit_across_all_complete_fortnights':(
                 len(vals)==len(EXPECTED_WINDOWS) and all(v['net_usd']>0 and v['trades']>=10 for v in vals))
              }
            print('FORTNIGHT_AGGREGATE_'+key,json.dumps(totals[key],sort_keys=True),flush=True)
    report={
       'experiment':'Preregistered deterministic random 2-week samples per year 2022-2026',
       'periods_selected_before_observing_outcomes':True,
       'random_seed':20261123,
       'source':'actual historical Dukascopy bid/ask/quote-volume tick history',
       'data_session':'07:00 to 09:00 UTC; 19 signals every five minutes from 07:15 through 08:45',
       'historical_macro_calendar':'UNAVAILABLE; news-event blocking deliberately not applied in quote-only research; live gate remains closed',
       'strategy':'Unmodified frozen tick_paper_replay.py signals, 3/4 family diversity veto, original spread/delay/quote-count protections, original tick exit and fee calculations',
       'starting_capital_usd_per_period':150,
       'notional_gbp_units':1000,'transaction_cost':{
          'actual_historical_bid_ask':True,'modelled_commission_usd_rt':fx.COMMISSION_USD,
          'additional_slippage_pips_rt':fx.EXTRA_SLIPPAGE_PIPS_ROUND_TRIP},
       'real_broker_orders':0,'approved_for_live_trading':False,
       'periods':results,'aggregate':totals,
       'missing_dates':all_missing,
       'source_manifest_complete':manifest.get('complete',False),
       'limitations':[
        'Quote-side depth/volume is not executable order flow',
        'No verified historical as-of-time economic event calendar; omitting news veto makes replay incomparable to fully protected strategy',
        'No spread-adjusted broker-specific stop-fill confirmation, price impact or margin checks',
        'Selection was randomized without viewing these historical outcomes, but the signal algorithms were iteratively developed using other 2026 data',
        'Each two-week window starts a separate illustrative $150 account; total across windows is not a continuous account',
        'Consistent profitability cannot be proven from these retrospective historical tests alone'
       ]
    }
    OUTPUT.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT_FILE',OUTPUT,'ALL_DATA_COMPLETE',not all_missing,flush=True)
    if all_missing:
        raise RuntimeError(f'Incomplete market dates: {len(all_missing)}. Do not call the study a complete 50-day test.')

if __name__=='__main__':
    main()
