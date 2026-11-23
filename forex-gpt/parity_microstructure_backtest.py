#!/usr/bin/env python3
"""Causal FX triangular cross-rate research: NO brokerage connections or orders.
GBPUSD synthetic quote = EURUSD / EURGBP, as-of three separately updated
Dukascopy tick feeds. Train 2021-23, select 2024, test frozen 2025-26.
Historical news calendar unavailable; neither tri-arbitrage nor firm fills implied.
"""
from __future__ import annotations
import bisect,collections,datetime as dt,hashlib,json,math,statistics
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT=Path('forex-gpt/.tmp/parity_microstructure')
PIP=.0001;SIZE_GBP=1000;COMMISSION=.06;SLIPPAGE_PIPS=.2
AGE_MS=1200;DECISION_STEP_MS=10000
STOP_TARGET={10:(1.8,2.3),30:(2.5,3.),120:(4.5,5.5)}
HORIZONS=(10,30,120);REGIMES=('cross_lead_burst','large_parity_gap','normal')
MAX_SPREAD={'gbpusd':1.25,'eurusd':.9,'eurgbp':1.4}
EXPERTS=('parity_mid','synthetic_executable','cross_pair_lead','ML_Ridge','ML_LightGBM')
THRESHOLDS={'parity_mid':(.25,.5,1.),'synthetic_executable':(0.,.2,.5),
            'cross_pair_lead':(.25,.5,1.),'ML_Ridge':(.02,.05,.1),
            'ML_LightGBM':(.02,.05,.1)}
FEATURES=('residual','buy_gap','sell_gap','lead5','lead30','gbp5','gbp30',
          'synth5','synth30','gbp_spread','synthetic_spread',
          'gbp_age','eurusd_age','eurgbp_age','hour')

def time_ms(day,hms):
 return round(dt.datetime.fromisoformat(day+'T'+hms+'+00:00').timestamp()*1000)
def at(rows,timestamps,t,age=AGE_MS):
 i=bisect.bisect_right(timestamps,t)-1
 return rows[i] if i>=0 and t-rows[i][0]<=age else None
def quotes_at(book,times,t):
 q={p:at(book[p],times[p],t) for p in ('gbpusd','eurusd','eurgbp')}
 return q if all(v is not None for v in q.values()) else None
def triangle(q):
 eu,eg,g=q['eurusd'],q['eurgbp'],q['gbpusd']
 synth_bid=eu[2]/eg[1];synth_ask=eu[1]/eg[2]
 synth_mid=(synth_bid+synth_ask)/2;direct_mid=(g[1]+g[2])/2
 return {'synth_mid':synth_mid,'gbp_mid':direct_mid,
 'residual':(synth_mid-direct_mid)/PIP,
 'buy_gap':(synth_bid-g[1])/PIP,'sell_gap':(g[2]-synth_ask)/PIP,
 'gbp_spread':(g[1]-g[2])/PIP,
 'synthetic_spread':(synth_ask-synth_bid)/PIP}
def load_day(day,manifest):
 inventory={a['day']:a for a in manifest['days']}
 if day not in inventory:raise ValueError('Missing day '+day)
 blob=(ROOT/(day+'.json')).read_bytes()
 if hashlib.sha256(blob).hexdigest()!=inventory[day]['sha256']:
  raise ValueError('Historical quote hash mismatch '+day)
 x=json.loads(blob)
 if x.get('date')!=day or x.get('provider')!='dukascopy-node@1.51.1':
  raise ValueError('Source/day mismatch '+day)
 lo,hi=time_ms(day,'07:00:00'),time_ms(day,'09:00:00')
 for p in ('gbpusd','eurusd','eurgbp'):
  r=x['instruments'][p]
  if len(r)<200 or r[0][0]<lo or r[-1][0]>=hi:raise ValueError('Bad quote range '+p)
  prev=-1
  for q in r:
   if (len(q)!=5 or not isinstance(q[0],int) or q[0]<prev or
      q[0]<lo or q[0]>=hi or q[2]<=0 or q[1]<q[2] or
      not all(math.isfinite(v) and v>=0 for v in q[1:])):
    raise ValueError('Malformed quote '+day+' '+p)
   prev=q[0]
 return x['instruments']
def exit_price(book,entry_i,side,seconds):
 raw=book['gbpusd'];e=raw[entry_i];price=e[1] if side>0 else e[2]
 stop,target=STOP_TARGET[seconds];end=e[0]+seconds*1000
 j=entry_i+1;reason='TIME_EXIT'
 while j<len(raw) and raw[j][0]<end:
  mark=raw[j][2] if side>0 else raw[j][1]
  change=side*(mark-price)/PIP
  if change<=-stop:reason='STOP';break
  if change>=target:reason='TARGET';break
  j+=1
 if j>=len(raw):return None
 mark=raw[j][2] if side>0 else raw[j][1]
 return {'pnl':round(side*(mark-price)*SIZE_GBP-COMMISSION-SLIPPAGE_PIPS*PIP*SIZE_GBP,5),
         'exit':raw[j][0],'reason':reason}
def make_day(day,window_id,book):
 ts={p:[r[0] for r in arr] for p,arr in book.items()}
 rows=[]
 for t in range(time_ms(day,'07:15:00'),time_ms(day,'08:45:00')+1,DECISION_STEP_MS):
  q=quotes_at(book,ts,t)
  if q is None:continue
  if any(not(0<(r[1]-r[2])/PIP<=MAX_SPREAD[p]) for p,r in q.items()):continue
  older5=quotes_at(book,ts,t-5000);older30=quotes_at(book,ts,t-30000)
  if older5 is None or older30 is None:continue
  now,p5,p30=triangle(q),triangle(older5),triangle(older30)
  entry_i=bisect.bisect_left(ts['gbpusd'],t+500)
  if entry_i>=len(ts['gbpusd']) or ts['gbpusd'][entry_i]>t+4000:continue
  entry=book['gbpusd'][entry_i]
  if not(0<(entry[1]-entry[2])/PIP<=MAX_SPREAD['gbpusd']):continue
  lead5=(now['synth_mid']-p5['synth_mid']-now['gbp_mid']+p5['gbp_mid'])/PIP
  lead30=(now['synth_mid']-p30['synth_mid']-now['gbp_mid']+p30['gbp_mid'])/PIP
  if abs(lead5)>=.45:regime='cross_lead_burst'
  elif abs(now['residual'])>=.5:regime='large_parity_gap'
  else:regime='normal'
  f={'residual':now['residual'],'buy_gap':now['buy_gap'],'sell_gap':now['sell_gap'],
     'lead5':lead5,'lead30':lead30,
     'gbp5':(now['gbp_mid']-p5['gbp_mid'])/PIP,
     'gbp30':(now['gbp_mid']-p30['gbp_mid'])/PIP,
     'synth5':(now['synth_mid']-p5['synth_mid'])/PIP,
     'synth30':(now['synth_mid']-p30['synth_mid'])/PIP,
     'gbp_spread':now['gbp_spread'],'synthetic_spread':now['synthetic_spread'],
     'gbp_age':t-q['gbpusd'][0],'eurusd_age':t-q['eurusd'][0],
     'eurgbp_age':t-q['eurgbp'][0],'hour':(t-time_ms(day,'00:00:00'))/3600000}
  future={h:{side:exit_price(book,entry_i,side,h) for side in (1,-1)} for h in HORIZONS}
  rows.append({'day':day,'year':int(day[:4]),'window':window_id,'t':t,
    'entry':entry[0],'regime':regime,'f':f,'future':future,'prediction':{}})
 return rows
def train_predictions(rows):
 x=np.asarray([[r['f'][k] for k in FEATURES] for r in rows],dtype=np.float32)
 for h in HORIZONS:
  for side in (1,-1):
   ix=[i for i,r in enumerate(rows) if r['year'] in (2021,2022,2023)
       and r['future'][h][side] is not None]
   if len(ix)<1000:raise RuntimeError('Insufficient actual training quotes '+str((h,side,len(ix))))
   y=np.asarray([rows[i]['future'][h][side]['pnl'] for i in ix],np.float32)
   learners={'ML_Ridge':make_pipeline(StandardScaler(),Ridge(alpha=250.)),
     'ML_LightGBM':LGBMRegressor(n_estimators=120,max_depth=4,num_leaves=11,
       min_child_samples=100,learning_rate=.04,reg_lambda=18.,
       colsample_bytree=.85,random_state=260923,verbosity=-1,n_jobs=2)}
   for name,m in learners.items():
    m.fit(x[ix],y)
    predictions=m.predict(x)
    for i,r in enumerate(rows):
     r['prediction'].setdefault(h,{}).setdefault(name,{})[side]=float(predictions[i])
   print('TRIANGLE_MODEL_TRAINED',h,side,len(ix),'net_mean',round(float(y.mean()),5),flush=True)
def vote(r,expert,threshold,h):
 f=r['f']
 if expert=='parity_mid':
  x=f['residual'];return int(x>threshold)-int(x< -threshold)
 if expert=='synthetic_executable':
  a,b=f['buy_gap'],f['sell_gap']
  return 1 if a>threshold and a>b else -1 if b>threshold and b>a else 0
 if expert=='cross_pair_lead':
  x=f['lead5'];return int(x>threshold)-int(x< -threshold)
 p=r['prediction'][h][expert];a,b=p[1],p[-1]
 return 1 if a>=threshold and a>b+.03 else -1 if b>=threshold and b>a+.03 else 0
def replay(rows,route,with_trades=False):
 byday=collections.defaultdict(list)
 for r in rows:byday[r['day']].append(r)
 nets=collections.defaultdict(float);daily={};trades=[];byreg=collections.defaultdict(lambda:[0,0.])
 for day,qs in sorted(byday.items()):
  busy=-1;cash=150.;n=0;wins=0
  for r in sorted(qs,key=lambda z:z['t']):
   if cash<=147.:continue
   c=route(r)
   if c is None:continue
   expert,threshold,h=c
   side=vote(r,expert,threshold,h)
   if side==0 or r['entry']<=busy:continue
   out=r['future'][h][side]
   if out is None:continue
   cash+=out['pnl'];n+=1;wins+=int(out['pnl']>0)
   busy=out['exit'];byreg[r['regime']][0]+=1;byreg[r['regime']][1]+=out['pnl']
   if with_trades:
    trades.append({'date':day,'regime':r['regime'],'decision_utc':dt.datetime.fromtimestamp(
      r['t']/1000,dt.timezone.utc).isoformat(),'expert':expert,'threshold':threshold,
      'hold_seconds':h,'side':'BUY' if side>0 else 'SELL','net_usd':out['pnl'],
      'entry_delay_ms':r['entry']-r['t'],'quote_age_ms':{p:r['f'][p+'_age']
      for p in ('gbp','eurusd','eurgbp')},'exit_reason':out['reason']})
  daily[day]={'net_usd':round(cash-150.,5),'trades':n,'wins':wins}
  nets[qs[0]['window']]+=cash-150.
 return {'net_usd':round(sum(x['net_usd'] for x in daily.values()),5),
  'trades':sum(x['trades'] for x in daily.values()),'wins':sum(x['wins'] for x in daily.values()),
  'days':len(daily),'profitable_days':sum(x['net_usd']>0 for x in daily.values()),
  'profitable_fortnights':sum(v>0 for v in nets.values()),
  'net_per_fortnight':{str(k):round(v,5) for k,v in sorted(nets.items())},
  'net_by_regime':{k:{'trades':v[0],'net_usd':round(v[1],5)} for k,v in byreg.items()},
  'daily':daily,'trades_log':trades if with_trades else []}
def evaluate(val,regime,expert,threshold,h):
 qs=[r for r in val if r['regime']==regime]
 result=replay(qs,lambda r:(expert,threshold,h),True)
 pnl=[q['net_usd'] for q in result['trades_log']]
 n=len(pnl);avg=statistics.mean(pnl) if n else 0.
 sem=statistics.stdev(pnl)/math.sqrt(n) if n>1 else float('inf')
 return {'expert':expert,'threshold':threshold,'horizon_seconds':h,
    'trades':n,'wins':result['wins'],'net_usd':result['net_usd'],
    'avg_net_usd':round(avg,5),
    'lower_one_standard_error_usd':round(avg-sem,5) if math.isfinite(sem) else -999.,
    'positive_fortnights':result['profitable_fortnights'],
    'net_per_fortnight':result['net_per_fortnight']}
def summary(s):
 return {k:s[k] for k in ('net_usd','trades','wins','days','profitable_days',
  'profitable_fortnights','net_per_fortnight','net_by_regime')}
def main():
 mf=json.loads((ROOT/'manifest.json').read_text())
 if mf.get('draw_seed')!=260923 or len(mf['windows'])!=12 or len(mf['days'])!=120 or mf.get('missing'):
  raise RuntimeError('Historical raw data not complete for frozen 120 dates')
 rows=[]
 for wid,w in enumerate(mf['windows']):
  for day in w['dates']:
   book=load_day(day,mf);r=make_day(day,wid,book);rows.extend(r)
   print('TRIANGLE_DAY',day,'valid_asof_signals',len(r),flush=True)
 parts={'train':[r for r in rows if r['year'] in (2021,2022,2023)],
        'validation':[r for r in rows if r['year']==2024],
        'heldout':[r for r in rows if r['year'] in (2025,2026)]}
 print('TRIANGLE_PARTITIONS',json.dumps({k:{'signals':len(v),'dates':len(set(q['day'] for q in v))}
    for k,v in parts.items()}),flush=True)
 if min(len(parts['train']),len(parts['validation']),len(parts['heldout']))<200:
  raise RuntimeError('Sample too sparse; do not present as complete study')
 train_predictions(rows)
 val=parts['validation'];held=parts['heldout']
 select_exp={};select_strict={};all_validation={}
 for regime in REGIMES:
  pool=[evaluate(val,regime,expert,th,h) for expert in EXPERTS
      for th in THRESHOLDS[expert] for h in HORIZONS]
  pool.sort(key=lambda x:(x['net_usd'],x['trades']),reverse=True)
  exp=[c for c in pool if c['trades']>=15 and c['net_usd']>0]
  strict=[c for c in pool if c['trades']>=30 and c['positive_fortnights']==2
       and c['lower_one_standard_error_usd']>0]
  select_exp[regime]=exp[0] if exp else None
  select_strict[regime]=strict[0] if strict else None
  all_validation[regime]=pool
  print('TRIANGLE_SELECTION',regime,json.dumps({
     'exploratory':select_exp[regime],'strict':select_strict[regime],
     'top3':pool[:3]},sort_keys=True),flush=True)
 def routing(selection):
  def choose(r):
   a=selection.get(r['regime'])
   return (a['expert'],a['threshold'],a['horizon_seconds']) if a else None
  return choose
 final={'switch_exploratory':replay(held,routing(select_exp),True),
        'switch_strict':replay(held,routing(select_strict),True)}
 for h in HORIZONS:
  for expert,th in [('parity_mid',.5),('synthetic_executable',0.),
                     ('cross_pair_lead',.5),('ML_Ridge',.05)]:
   final[f'fixed_{expert}_{h}s']=replay(held,
     lambda r,e=expert,t=th,s=h:(e,t,s))
 for name,s in final.items():
  print('TRIANGLE_HELDOUT',name,json.dumps(summary(s),sort_keys=True),flush=True)
 report={'research':'causal synthetic EURUSD/EURGBP vs direct GBPUSD leading cross-rate quote strategy',
  'design':'120 previously unexamined 2h tick sessions; train 2021-23, selection 2024, heldout 2025-26',
  'provider':'dukascopy-node@1.51.1',
  'sample':{k:{'signals':len(v),'dates':len(set(r['day'] for r in v))} for k,v in parts.items()},
  'weeks':mf['windows'],'source_manifest':'manifest.json',
  'regimes':REGIMES,'experts':EXPERTS,'signal_features':FEATURES,'horizons_seconds':HORIZONS,
  'slippage_additional_pips_rt':SLIPPAGE_PIPS,'commission_usd_rt':COMMISSION,
  'start_usd_reset_each_day':150,'position_gbp_units':SIZE_GBP,
  'entry_latency_ms':[500,4000],'max_quote_age_ms':AGE_MS,'max_bid_ask_spreads_pips':MAX_SPREAD,
  'economic_news_asof_archive':False,'real_order_count':0,'live_eligible':False,
  'exploratory_requirement':'15 validation trades plus positive 2024 net',
  'strict_requirement':'30 trades plus both 2024 periods profitable and mean - one standard error positive',
  'selected_exploratory':select_exp,'selected_strict':select_strict,
  'all_validation':all_validation,'heldout':final,
  'limitations':['Dukascopy asynchronous quotes: theoretical triangular deviation NOT executable arbitrage',
   'No authoritative contemporaneous historical news calendar or broker spread/fill confirmations',
   'Multiple specialists screened within 2024; validation selection can overfit',
   'Only 07:00–09:00 UTC sessions; noncontinuous historical dates',
   'Quoted volume not traded order flow; broker last-look/rejection/slippage and margin not modeled',
   'No live broker orders; hypothetical resets to $150 every day',
   'No tuning on 2025-26 heldout data without new independent evaluation'] }
 dst=ROOT/'parity_results.json';dst.write_text(json.dumps(report,indent=2)+'\n')
 print('TRIANGLE_DONE',dst,'NO_REAL_ORDERS',True,flush=True)
if __name__=='__main__':main()
