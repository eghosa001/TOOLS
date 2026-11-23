#!/usr/bin/env python3
"""Historical GBPUSD ten-signal ensemble; November 16-20 2026, paper only."""
import datetime as dt
import json, math, statistics as st
from pathlib import Path
FILE=Path('forex-gpt/.tmp/gpt_solo_m1.json')
OUT=Path('forex-gpt/.tmp/consensus_10_results.json')
DAYS=['2026-11-16','2026-11-17','2026-11-18','2026-11-19','2026-11-20']
PIP=.0001
UNITS=1000
START=150.
SPREAD_MAX=1.5
SLIPPAGE_RT=.2
COMMISSION_RT=.06
STOP=8
TARGET=12
HOLD=15
PAUSE_DAY=-3.
def ema(seq,n):
    a=2/(n+1);v=seq[0]
    for x in seq[1:]:v+=a*(x-v)
    return v
def sign(x,d=0):return int(x>d)-int(x< -d)
def rsi(x,n=14):
    dif=[x[j]-x[j-1] for j in range(len(x)-n,len(x))]
    up=sum(max(d,0) for d in dif)/n
    down=sum(max(-d,0) for d in dif)/n
    return (100 if up else 50) if down==0 else 100-100/(1+up/down)
def models(close,high,low):
    x=close[-120:];h=high[-120:];l=low[-120:]
    m=[ema(x[:k],12)-ema(x[:k],26) for k in range(35,121)]
    m_sig=ema(m[-30:],9)
    s=st.pstdev(x[-20:])
    z=(x[-1]-st.mean(x[-20:]))/s if s else 0
    ran=max(h[-14:])-min(l[-14:])
    k=100*(x[-1]-min(l[-14:]))/ran if ran else 50
    return {
      'SMA_8_32':sign(st.mean(x[-8:])-st.mean(x[-32:]),PIP*.05),
      'EMA_12_36':sign(ema(x,12)-ema(x,36),PIP*.05),
      'ROC_5':sign(x[-1]-x[-6],PIP*.4),
      'ROC_20':sign(x[-1]-x[-21],PIP*.8),
      'RSI_14_50':sign(rsi(x)-50,3),
      'MACD_hist':sign(m[-1]-m_sig,PIP*.02),
      'Donchian_20_mid':sign(x[-1]-(max(h[-21:-1])+min(l[-21:-1]))/2,PIP*.2),
      'Stochastic_14':sign(k-50,5),
      'Bollinger_20_fade':-sign(z,1.2),
      'Pullback_5_fade':-sign(x[-1]-st.mean(x[-6:-1]),PIP*.9)}
def load():
    a=json.loads(FILE.read_text())
    if a.get('symbol')!='gbpusd' or a.get('timeframe')!='m1':raise ValueError('Wrong quote source')
    bid={int(q[0]):q for q in a['sides']['bid']}
    ask={int(q[0]):q for q in a['sides']['ask']}
    rows=[]
    for t in sorted(bid.keys()&ask.keys()):
        b=bid[t];a=ask[t]
        if not all(math.isfinite(v) and v>0 for v in b[1:5]+a[1:5]):raise ValueError('Bad quote')
        if any(b[j]>a[j] for j in (1,4)):raise ValueError('Inverted bid/ask')
        rows.append((t,b,a))
    if len(rows)<5000:raise ValueError('Too few aligned quotes')
    return rows
def settle(rows,entry_idx,side,last_idx):
    _,b,a=rows[entry_idx]
    entry=a[1] if side==1 else b[1]
    exit_idx=last_idx;out=None;reason='TIME_EXIT'
    for j in range(entry_idx,last_idx):
        _,b,a=rows[j]
        if side==1:
            stop=entry-STOP*PIP;target=entry+TARGET*PIP
            if b[1]<=stop or b[3]<=stop:
                out=min(b[1],stop);reason='STOP';exit_idx=j;break
            if b[2]>=target:
                out=target;reason='TARGET';exit_idx=j;break
        else:
            stop=entry+STOP*PIP;target=entry-TARGET*PIP
            if a[1]>=stop or a[2]>=stop:
                out=max(a[1],stop);reason='STOP';exit_idx=j;break
            if a[3]<=target:
                out=target;reason='TARGET';exit_idx=j;break
    if out is None:
        _,b,a=rows[last_idx];out=b[1] if side==1 else a[1]
    gross_pips=(out-entry)*side/PIP
    net=gross_pips*UNITS*PIP-SLIPPAGE_RT*UNITS*PIP-COMMISSION_RT
    return {'exit_idx':exit_idx,'net_usd':round(net,5),'gross_pips':round(gross_pips,4),'exit_reason':reason}
def main():
    rows=load()
    mid=[(b[4]+a[4])/2 for _,b,a in rows]
    hi=[(b[2]+a[2])/2 for _,b,a in rows]
    lo=[(b[3]+a[3])/2 for _,b,a in rows]
    contiguous=[]
    for i,r in enumerate(rows):
        contiguous.append(contiguous[-1]+1 if i and r[0]-rows[i-1][0]==60000 else 1)
    decisions=[]
    for i in range(120,len(rows)-HOLD-1):
        t=rows[i][0]
        when=dt.datetime.fromtimestamp((t+60000)/1000,dt.timezone.utc)
        day=when.date().isoformat()
        if day not in DAYS or not(7<=when.hour<17) or when.minute%5:continue
        if contiguous[i]<120:continue
        if rows[i+1][0]!=t+60000 or rows[i+HOLD+1][0]!=t+(HOLD+1)*60000:continue
        votes=models(mid[:i+1],hi[:i+1],lo[:i+1])
        buy=sum(v==1 for v in votes.values());sell=sum(v==-1 for v in votes.values())
        spread=(rows[i+1][2][1]-rows[i+1][1][1])/PIP
        if spread<0:raise ValueError('Negative spread')
        decisions.append({'idx':i,'day':day,'utc':when.isoformat(),'buy':buy,'sell':sell,'neutral':10-buy-sell,'spread':spread,'votes':votes})
    if len(decisions)<300:raise ValueError('Missing complete sessions')
    results={}
    for threshold in [6,7,8]:
        eq=START;peak=START;dd=0;blocked=-1;trades=[]
        days={d:{'trades':0,'wins':0,'losses':0,'net_usd':0.} for d in DAYS}
        for v in decisions:
            side=1 if v['buy']>=threshold and v['buy']>v['sell'] else (-1 if v['sell']>=threshold and v['sell']>v['buy'] else 0)
            if not side:continue
            i=v['idx']
            if i+1<=blocked or v['spread']>SPREAD_MAX or days[v['day']]['net_usd']<=PAUSE_DAY:continue
            result=settle(rows,i+1,side,i+HOLD+1)
            blocked=result['exit_idx'];p=result['net_usd']
            days[v['day']]['trades']+=1
            days[v['day']]['wins']+=int(p>0)
            days[v['day']]['losses']+=int(p<0)
            days[v['day']]['net_usd']+=p
            eq+=p;peak=max(peak,eq);dd=max(dd,peak-eq)
            trades.append({'utc':v['utc'],'side':'BUY' if side>0 else 'SELL',
              'votes_buy':v['buy'],'votes_sell':v['sell'],'votes_neutral':v['neutral'],
              'spread_pips':round(v['spread'],3),**result})
        for d in days.values():d['net_usd']=round(d['net_usd'],5)
        winners=[x['net_usd'] for x in trades if x['net_usd']>0]
        losers=[x['net_usd'] for x in trades if x['net_usd']<0]
        net=round(eq-START,5)
        results[str(threshold)]={'votes_required':threshold,'trades':len(trades),
          'winning_trades':len(winners),'losing_trades':len(losers),
          'win_rate_pct':round(100*len(winners)/len(trades),2) if trades else 0,
          'net_usd':net,'ending_balance_usd':round(eq,5),
          'net_pct':round(100*net/START,3),
          'profit_factor':round(sum(winners)/-sum(losers),3) if losers else None,
          'closed_trade_max_drawdown_usd':round(dd,5),
          'profitable_days':sum(x['net_usd']>0 for x in days.values()),
          'days':days,'trades_detail':trades}
    report={'kind':'historical paper-only backtest, no broker orders',
      'date_range_utc':'2026-11-16 to 2026-11-20',
      'symbol':'GBPUSD','data':'actual Dukascopy M1 bid/ask',
      'aligned_candles':len(rows),'evaluated_decisions':len(decisions),
      'signals':list(decisions[0]['votes']),
      'assumptions':{'starting_capital_usd':START,'gbp_units':UNITS,
          'max_spread_pips':SPREAD_MAX,'round_trip_extra_slippage_pips':SLIPPAGE_RT,
          'commission_usd_round_trip':COMMISSION_RT,
          'stop_loss_pips':STOP,'take_profit_pips':TARGET,
          'max_hold_minutes':HOLD,'daily_loss_pause_usd':PAUSE_DAY,
          'decisions':'every 5 minutes 07:00-17:00 UTC, completed M1 only',
          'execution':'next M1 bar open, bid/ask, one position at a time',
          'ambiguous_same_bar_stops':'conservatively stop first',
          'real_broker_orders':False,'profit_guaranteed':False},'results':results}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+'\n')
    print('CONSENSUS_DATA',json.dumps({'aligned_candles':len(rows),'decisions':len(decisions),'signals':report['signals']}))
    for k,v in results.items():
        print('CONSENSUS_'+k,json.dumps({x:y for x,y in v.items() if x!='trades_detail'},sort_keys=True))
    print('RESULT_FILE',str(OUT))
if __name__=='__main__':main()
