#!/usr/bin/env python3
"""Longer-horizon FX research: EURUSD vs GBPUSD, regime model rotation, real ticks.
Precommitted 2022-23 train, 2024 validation-only model selection, 2025-26 final
holdout. No broker, orders, artificial economic-event data or future features.
"""
from __future__ import annotations
import bisect,collections,datetime as dt,hashlib,json,math,statistics
from pathlib import Path
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import tick_paper_replay as fx

DIR=Path('forex-gpt/.tmp/long_horizon')
HOLD=(600,900,1800)
PAIRS=('eurusd','gbpusd')
REGIMES=('volatile','trending','ranging','mixed')
EXPERTS=('momentum','breakout','reversal','cross_pair','tick_flow','ML_LightGBM','ML_Ridge')
COLS=('r1','r5','r15','range15','z15','spread','median_spread','tick_rate',
      'up_ratio','quote_imbalance','peer_r5','eurgbp_r5','vol5','hour','eurusd_flag')
COST={'units_base_currency':1000,'slippage_roundtrip_pips':0.2,'commission_roundtrip_usd':.06}
SPREAD_LIMIT={'eurusd':0.75,'gbpusd':1.05}
RECENT_SPREAD_LIMIT={'eurusd':0.7,'gbpusd':0.95}
STOPS={600:(8.,12.),900:(10.,15.),1800:(15.,22.)}
TRAIN_YEARS={2022,2023};VALIDATION_YEAR=2024;TEST_YEARS={2025,2026}
DECISION_STEP=5*60000
SIGNAL_START='08:00:00';SIGNAL_END='11:00:00'
SEED=260707

def when_ms(day,stamp):
 return fx.to_utc_ms(day+'T'+stamp+'Z')
def sid(v,t=0):
 return int(v>t)-int(v< -t)
def check_day(day,manifest):
 entry=next((x for x in manifest['days'] if x['day']==day),None)
 if entry is None:raise FileNotFoundError('No real historical data '+day)
 b=(DIR/(day+'.json')).read_bytes()
 if hashlib.sha256(b).hexdigest()!=entry['checksum_sha256']:
  raise ValueError('Dukascopy source hash differs '+day)
 obj=json.loads(b)
 if obj.get('provider')!='dukascopy-node@1.51.1' or obj.get('date')!=day:
  raise ValueError('Mismatched source and date '+day)
 book={}
 start,end=when_ms(day,'07:00:00'),when_ms(day,'12:00:00')
 for p in (*PAIRS,'eurgbp'):
  a=obj['instruments'][p]
  if len(a)<1000:raise ValueError('Too little real data '+day+' '+p)
  if any(len(x)!=5 or x[1]<x[2] or x[2]<=0 or x[0]<start or x[0]>=end for x in a):
   raise ValueError('Wrong bid-ask or timestamp '+day+' '+p)
  if any(a[i][0]>a[i+1][0] for i in range(len(a)-1)):
   raise ValueError('Tick history out of order '+day+' '+p)
  book[p]=a
 return book

def lastmid(book,clocks,pair,t,seconds):
 q=fx.older_mid(book[pair],clocks[pair],t,seconds*1000)
 return q

def features(book,clocks,day,pair,t):
 recent=fx.snapshot(book[pair],clocks[pair],t,5*60000)
 m15=fx.snapshot(book[pair],clocks[pair],t,15*60000)
 if len(recent)<90 or len(m15)<160:return None
 latest=recent[-1];mid=(latest[1]+latest[2])/2
 previous={}
 for seconds in (60,300,900):
  past=lastmid(book,clocks,pair,t,seconds)
  if past is None:return None
  previous[seconds]=(mid-past)/fx.PIP
 other='gbpusd' if pair=='eurusd' else 'eurusd'
 cross={}
 for q in (other,'eurgbp'):
  snap=fx.snapshot(book[q],clocks[q],t,5*60000)
  old=lastmid(book,clocks,q,t,300)
  if not snap or old is None:return None
  cross[q]=((snap[-1][1]+snap[-1][2])/2-old)/fx.PIP
 base=np.asarray([(x[1]+x[2])*0.5 for x in m15],dtype=np.float64)
 p5=np.asarray([(x[1]+x[2])*0.5 for x in recent],dtype=np.float64)
 range15=(float(base.max())-float(base.min()))/fx.PIP
 z15=(mid-float(base.mean()))/(float(base.std())+1e-10)
 r1,r5,r15=(previous[s] for s in (60,300,900))
 if range15>=13 or abs(r5)>=6:
  regime='volatile'
 elif abs(r15)>=4 and (r1*r15>0) and range15>=5:
  regime='trending'
 elif range15<=7 or abs(r15)<=1.5:
  regime='ranging'
 else:regime='mixed'
 entry_i=bisect.bisect_left(clocks[pair],t+500)
 if entry_i>=len(clocks[pair]):return None
 q=book[pair][entry_i]
 if q[0]>t+4000:return None
 spread=(q[1]-q[2])/fx.PIP
 recent_spread=statistics.median((x[1]-x[2])/fx.PIP for x in recent)
 if spread<=0 or spread>SPREAD_LIMIT[pair] or recent_spread>RECENT_SPREAD_LIMIT[pair]:
  return None
 micro=recent[-min(250,len(recent)):]
 diff=np.diff(np.asarray([(x[1]+x[2])*0.5 for x in micro]))
 up=(int(np.count_nonzero(diff>0))-int(np.count_nonzero(diff<0)))/max(len(diff),1)
 imb=[(x[4]-x[3])/(x[4]+x[3]) for x in micro if x[4]+x[3]>0]
 qimb=float(np.mean(imb)) if imb else 0.
 vol5=float(np.std(np.diff(p5)))/fx.PIP
 values={
  'r1':r1,'r5':r5,'r15':r15,'range15':range15,'z15':z15,
  'spread':spread,'median_spread':recent_spread,
  'tick_rate':len(recent),'up_ratio':up,'quote_imbalance':qimb,
  'peer_r5':cross[other],'eurgbp_r5':cross['eurgbp'],'vol5':vol5,
  'hour':(t-when_ms(day,'00:00:00'))/3600000,
  'eurusd_flag':int(pair=='eurusd')}
 return {'pair':pair,'date':day,'year':int(day[:4]),'utc_ms':t,
   'regime':regime,'x':values,'entry_idx':entry_i,'entry_time':q[0],
   'entry_spread_pips':spread}

def rule_votes(r):
 x=r['x']
 momentum=sid(x['r5'],1.35) if sid(x['r15'],2.6)==sid(x['r5'],1.35) else 0
 breakout=sid(x['r5'],2.8) if x['range15']>=8 and abs(x['r5'])>=2.8 else 0
 reversal=-sid(x['z15'],1.25) if abs(x['r15'])<4 else 0
 peer=sid(x['peer_r5'],1.5)
 cross=peer if peer and sid(x['r5'],0.8)==peer else 0
 tick=sid(x['up_ratio'],.11) if sid(x['quote_imbalance'],.08)==sid(x['up_ratio'],.11) else 0
 return {'momentum':momentum,'breakout':breakout,'reversal':reversal,
         'cross_pair':cross,'tick_flow':tick}

def collect_data(manifest):
 inventory=[d for w in manifest['windows'] for d in w['days']]
 output=[];unavailable=[]
 for day in inventory:
  try:
   book=check_day(day,manifest)
   ts={p:[v[0] for v in q] for p,q in book.items()}
   found=0
   for t in range(when_ms(day,SIGNAL_START),when_ms(day,SIGNAL_END)+1,DECISION_STEP):
    for pair in PAIRS:
     row=features(book,ts,day,pair,t)
     if row is None:continue
     row['window_index']=next(i for i,w in enumerate(manifest['windows']) if day in w['days'])
     row['votes']=rule_votes(row)
     future={}
     for duration in HOLD:
      stop,target=STOPS[duration]
      future[str(duration)]={}
      for direction in (1,-1):
       result=fx.exits(book[pair],ts[pair],row['entry_idx'],direction,duration,stop,target)
       if result is None:
        future[str(duration)][str(direction)]=None
       else:
        future[str(duration)][str(direction)]={
          'net_usd':float(result['pnl_usd']),
          'exit_ms':int(ts[pair][result['exit_tick_index']]),
          'exit_reason':result['exit_reason']}
     row['future']=future
     output.append(row);found+=1
   print('LONG_HISTORICAL_DAY',day,'eligible_decisions',found,
         'tick_counts',json.dumps({p:len(v) for p,v in book.items()}),flush=True)
  except (ValueError,RuntimeError,FileNotFoundError,KeyError,IndexError) as e:
   unavailable.append({'day':day,'error':str(e)})
   print('LONG_HISTORICAL_BAD_DAY',day,str(e),flush=True)
 if unavailable:raise RuntimeError('Incomplete market data; no scoring: '+str(unavailable))
 return output

def train_predictions(rows):
 years=[r['year'] for r in rows]
 for pair in PAIRS:
  indices=[i for i,r in enumerate(rows) if r['pair']==pair]
  x=np.asarray([[rows[i]['x'][k] for k in COLS] for i in indices],np.float32)
  for horizon in HOLD:
   for direction in (1,-1):
    train_index=[j for j,i in enumerate(indices) if years[i] in TRAIN_YEARS and
       rows[i]['future'][str(horizon)][str(direction)] is not None]
    if len(train_index)<300:raise RuntimeError('Insufficient 2022-23 ML training rows '+pair)
    y=np.asarray([rows[indices[j]]['future'][str(horizon)][str(direction)]['net_usd']
       for j in train_index])
    learners={
      'ML_LightGBM':LGBMRegressor(n_estimators=125,max_depth=4,
       num_leaves=12,min_child_samples=60,learning_rate=.035,
       reg_lambda=14.,colsample_bytree=.8,random_state=260707,verbosity=-1,n_jobs=2),
      'ML_Ridge':make_pipeline(StandardScaler(),Ridge(alpha=250.))
    }
    for name,model in learners.items():
     model.fit(x[train_index],y)
     pred=model.predict(x)
     for j,i in enumerate(indices):
      rows[i].setdefault('ml',{}).setdefault(str(horizon),{}).setdefault(name,{})[
       str(direction)]=float(pred[j])
    print('LONG_MODEL_TRAINED',pair,horizon,direction,'samples',len(train_index),
          'mean_cost_net_target',round(float(np.mean(y)),5),flush=True)

def expert_signal(r,expert,horizon):
 if expert in ('ML_LightGBM','ML_Ridge'):
  estimates=r['ml'][str(horizon)][expert]
  a,b=estimates['1'],estimates['-1']
  # 5-cent positive expected net profit hurdle and directional difference 3c.
  return 1 if a>0.05 and a>b+0.03 else -1 if b>0.05 and b>a+0.03 else 0
 return r['votes'][expert]

def simulate(rows,policy,details=False):
 # Single position across currency pairs, cap daily losses in account-level USD.
 # Each day starts at $150, unchanged for all scenarios. No overlapping positions.
 byday=collections.defaultdict(list)
 for r in rows:byday[r['date']].append(r)
 perday={};trades=[];bywindow=collections.defaultdict(float);bypair=collections.defaultdict(
  lambda:{'trades':0,'net_usd':0.,'wins':0})
 for day,entries in sorted(byday.items()):
  entries.sort(key=lambda r:(r['utc_ms'],r['pair']))
  balance=150.;busy=-1;n=0;wins=0;rejected=collections.Counter();trade_list=[]
  # Process one time-slot at a time; if two pairs qualify, use 2024
  # validation-only score, then lower entry spread, then EURUSD tie-break.
  for instant in sorted(set(r['utc_ms'] for r in entries)):
   if balance-150.<=-3.:
    rejected['DAILY_RISK_PAUSE']+=1;continue
   batch=[r for r in entries if r['utc_ms']==instant]
   actionable=[]
   for r in batch:
    pred=policy(r)
    if pred is None:continue
    name,horizon,score=pred
    side=expert_signal(r,name,horizon)
    if side==0:continue
    outcome=r['future'][str(horizon)][str(side)]
    if outcome is None:continue
    actionable.append((float(score),-r['entry_spread_pips'],
      int(r['pair']=='eurusd'),r,name,horizon,side,outcome))
   if not actionable:
    rejected['NO_VALIDATED_OPPORTUNITY']+=1;continue
   if busy>=instant:
    rejected['OVERLAP']+=1;continue
   actionable.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
   score,_,_,r,name,horizon,side,outcome=actionable[0]
   if r['entry_time']<=busy:continue
   net=float(outcome['net_usd'])
   busy=outcome['exit_ms']
   balance+=net;n+=1;wins+=int(net>0)
   bypair[r['pair']]['trades']+=1
   bypair[r['pair']]['wins']+=int(net>0)
   bypair[r['pair']]['net_usd']+=net
   if details:
    trade={'date':day,'pair':r['pair'],'regime':r['regime'],
      'decision_utc':fx.source_stamp() if False else dt.datetime.fromtimestamp(
       instant/1000,dt.timezone.utc).isoformat(),
      'expert':name,'side':side,'horizon_seconds':horizon,
      'selection_score_from_validation':round(score,5),
      'spread_entry_pips':round(r['entry_spread_pips'],3),
      'net_usd':net,'exit_reason':outcome['exit_reason']}
    trade_list.append(trade)
  profit=round(balance-150.,5)
  bywindow[entries[0]['window_index']]+=profit
  perday[day]={'net_usd':profit,'trades':n,'wins':wins,'skips':dict(rejected)}
  trades.extend(trade_list)
 net=round(sum(d['net_usd'] for d in perday.values()),5)
 return {'net_usd':net,'trades':sum(d['trades'] for d in perday.values()),
  'wins':sum(d['wins'] for d in perday.values()),'days':len(perday),
  'positive_days':sum(d['net_usd']>0 for d in perday.values()),
  'positive_windows':sum(x>0 for x in bywindow.values()),
  'net_by_window':{str(k):round(v,5) for k,v in sorted(bywindow.items())},
  'by_pair':{k:{**v,'net_usd':round(v['net_usd'],5)} for k,v in bypair.items()},
  'daily':perday,'trade_log':trades if details else []}

def evaluate_candidate(rows,pair,regime,expert,horizon):
 small=[r for r in rows if r['pair']==pair and r['regime']==regime]
 answer=lambda r:(expert,horizon,0.)
 sim=simulate(small,answer,True)
 pnl=[r['net_usd'] for r in sim['trade_log']]
 n=len(pnl)
 mu=statistics.mean(pnl) if n else 0.
 se=statistics.stdev(pnl)/math.sqrt(n) if n>=2 else float('inf')
 # Both 2024 validation fortnights must be profitable for strict selection.
 return {'expert':expert,'hold_s':horizon,'pair':pair,'regime':regime,
   'trades':n,'wins':sim['wins'],'net_usd':sim['net_usd'],
   'average_trade_net_usd':round(mu,5),
   'lower_one_se_usd':round(mu-se,5) if math.isfinite(se) else -999.,
   'positive_validation_windows':sim['positive_windows'],
   'validation_net_by_window':sim['net_by_window']}

def policy_factory(selected):
 def policy(r):
  opt=selected.get(r['pair'],{}).get(r['regime'])
  if not opt:return None
  return (opt['expert'],opt['hold_s'],opt['lower_one_se_usd'])
 return policy

def main():
 manifest=json.loads((DIR/'manifest.json').read_text())
 if manifest.get('random_seed')!=SEED or len(manifest['windows'])!=10:
  raise ValueError('Frozen random window manifest changed')
 if len(manifest['days'])!=100 or manifest.get('missing'):
  raise RuntimeError('Missing source dates; no misleading incomplete sample')
 records=collect_data(manifest)
 train=[r for r in records if r['year'] in TRAIN_YEARS]
 val=[r for r in records if r['year']==VALIDATION_YEAR]
 test=[r for r in records if r['year'] in TEST_YEARS]
 if len(train)<500 or len(val)<100 or len(test)<300:
  raise RuntimeError('Too few verified eligible decisions')
 print('LONG_DATA_SPLIT',json.dumps({
   'train':[len(train),len(set(r['date'] for r in train))],
   'validation':[len(val),len(set(r['date'] for r in val))],
   'holdout':[len(test),len(set(r['date'] for r in test))]}),flush=True)
 train_predictions(records)
 candidates={};lenient={};strict={}
 for pair in PAIRS:
  candidates[pair]={};lenient[pair]={};strict[pair]={}
  for regime in REGIMES:
   scored=[evaluate_candidate(val,pair,regime,ex,h) for ex in EXPERTS for h in HOLD]
   scored.sort(key=lambda s:(s['net_usd'],s['trades']),reverse=True)
   candidates[pair][regime]=scored
   good=[s for s in scored if s['trades']>=8 and s['net_usd']>0]
   robust=[s for s in scored if s['trades']>=15 and s['lower_one_se_usd']>0 and
      s['positive_validation_windows']==2]
   lenient[pair][regime]=good[0] if good else None
   strict[pair][regime]=robust[0] if robust else None
   print('LONG_REGIME_SELECTION',pair,regime,json.dumps({
      'lenient':lenient[pair][regime],'strict':strict[pair][regime],
      'top3_validation':scored[:3]},sort_keys=True),flush=True)
 results={
   'selected_exploratory':simulate(test,policy_factory(lenient),True),
   'selected_strict':simulate(test,policy_factory(strict),True)}
 for pair in PAIRS:
  for h in HOLD:
   for expert in ('momentum','reversal','ML_LightGBM'):
    key=f'baseline_{pair}_{expert}_{h}s'
    results[key]=simulate([r for r in test if r['pair']==pair],
      lambda r,ex=expert,hh=h:(ex,hh,0.),False)
 for key,r in results.items():
  print('LONG_HELDOUT',key,json.dumps({k:r[k] for k in
   ['net_usd','trades','wins','days','positive_days','positive_windows','net_by_window','by_pair']},
   sort_keys=True),flush=True)
 report={
  'date_created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
  'design':'100 precommitted historical weekdays, 2022-23 training, 2024 specialist validation, 2025-26 untouched holdout; decisions 5-min 08:00-11:00 UTC',
  'data_provider':manifest['source'],
  'windows':manifest['windows'],'source_hash_manifest':'manifest.json',
  'sample_counts':{'train':len(train),'validation':len(val),'test':len(test)},
  'date_counts':{'train':len(set(r['date'] for r in train)),
    'validation':len(set(r['date'] for r in val)),
    'test':len(set(r['date'] for r in test))},
  'pairs':list(PAIRS),'regimes':list(REGIMES),'hold_seconds':list(HOLD),
  'entry_max_spread_pips':SPREAD_LIMIT,
  'entry_recent_median_spread_pips':RECENT_SPREAD_LIMIT,
  'target_stop_pips':{str(k):{'stop_pips':a,'take_pips':b} for k,(a,b) in STOPS.items()},
  'transaction_costs':COST,'start_equity_usd_each_day':150.,
  'model_training':'LightGBM and scaled Ridge regressors trained to predict net hypothetical long and short exits on 2022-23 only',
  'validation_selection':{
    'lenient':'>=8 trades positive total in 2024 per pair and regime',
    'strict':'at least 15 trades and two profitable 2024 fortnights and lower confidence mean (>0)'},
  'selected_validation_lenient':lenient,
  'selected_validation_strict':strict,
  'all_validation_candidates':candidates,
  'heldout_results':results,
  'historical_news_blackout_applied':False,
  'no_live_broker_orders':True,
  'limitations':[
    'No verified as-of-event archived macro calendar: historical news filter not applied',
    'Dukascopy raw quote ticks do not guarantee executable broker fills or account margin',
    'No live trades and no positive edge should be inferred from abstention',
    'Short sample windows of selected hours, not full-day or uninterrupted five-year trading',
    'Model choices screened on a 20-day validation sample and may overfit despite separated holdout',
    'Quote volumes do not represent executed order flow',
    'Stop exit is first observed quote, added slippage only assumed and not measured',
    'Independent daily $150 account resets, no margin model or compounding',
    'Do not retune on these heldout outcomes and claim independent confirmation'
  ]}
 dst=DIR/'long_horizon_results.json'
 dst.write_text(json.dumps(report,indent=2)+'\n')
 print('LONG_RESEARCH_SAVED',dst,'NO_LIVE_ORDERS',True,'FINAL_HOLDOUT_ONLY_ONCE',True,flush=True)
if __name__=='__main__':main()
