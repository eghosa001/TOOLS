#!/usr/bin/env python3
"""Regime-switching GBP/USD Forex quote-only paper backtest, NOT broker execution.

Preselected 150 days in non-overlapping random windows from 2022..2026:
2022-23 = training, 2024 = validation/selection, 2025-26 = unseen test.
Static signal definitions and decisions are causal. Only training outcomes enter
the model fit and only 2024 results select which specialist to use by regime.
2025-26 prices and outcomes NEVER enter model selection.
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

ROOT=Path('forex-gpt/.tmp/regime_switch')
MANIFEST=ROOT/'manifest.json'
DST=ROOT/'regime_switch_results.json'
HORIZONS=(30,120,300)
EXPERTS=('trend_momentum','trend_breakout','range_reversion','extreme_reversion',
         'cross_market','tick_imbalance','trend_cross','ML_LightGBM','ML_Ridge')
REGIMES=('volatile','trending','ranging','mixed')
REGIME_FEATURES=('ret1','ret5','range5','spread','tick_rate','gbp_upticks','quoted_volume_imbalance',
 'EURUSD_ret1','EURGBP_ret1','EURGBP_ret5','z5','rsi_proxy','hour',
 'cross_pair_divergence','vol_pips_1m','price_to_10m_high','price_to_10m_low')
MODEL_SEED=260501
CONFIG={'starting_equity_usd':150.,'position_gbp':1000,
 'max_spread_pips':1.5,'max_recent_median_spread_pips':1.35,
 'additional_slippage_pips_roundtrip':0.2,'commission_usd_roundtrip':.06,
 'train_years':[2022,2023],'validation_years':[2024],'test_years':[2025,2026],
 'min_validation_trades_research':12,'min_validation_trades_strict':20,
 'min_positive_fortnights_strict':2,'strict_standard_error_multiples':1.0,
 'sample_utc':'07:15-08:45 1-minute decisions; 07:00-09:00 real quotes',
 'hold_seconds':[30,120,300],
 'max_trade_loss_usd_day':3.0,
 'event_calendar':'not available as reliable historical feed; NO historical news veto, no live approval'}

def stamp(ms):
 return dt.datetime.fromtimestamp(ms/1000,dt.timezone.utc).isoformat()
def historical_day(date,inventory):
 f=ROOT/(date+'.json')
 if not f.exists():
  raise FileNotFoundError('Missing quote file: '+date)
 raw=f.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=inventory[date]['sha256']:
  raise RuntimeError('Source checksum mismatch '+date)
 obj=json.loads(raw)
 if obj.get('date')!=date or obj.get('provider')!='dukascopy-node@1.51.1':
  raise ValueError('Unexpected source '+date)
 return {pair:fx.sorted_ticks(obj,pair,date) for pair in ('gbpusd','eurusd','eurgbp')}

def features_at(book,ts,now):
 lookback=fx.snapshot(book['gbpusd'],ts['gbpusd'],now,10*60000)
 window5=fx.snapshot(book['gbpusd'],ts['gbpusd'],now,300000)
 window1=fx.snapshot(book['gbpusd'],ts['gbpusd'],now,60000)
 if len(window5)<70 or len(window1)<10 or len(lookback)<100:return None
 price=(window5[-1][1]+window5[-1][2])/2
 mids=np.asarray([(q[1]+q[2])/2 for q in window5])
 m1=np.asarray([(q[1]+q[2])/2 for q in window1])
 r1=fx.older_mid(book['gbpusd'],ts['gbpusd'],now,60000)
 r5=fx.older_mid(book['gbpusd'],ts['gbpusd'],now,300000)
 if r1 is None or r5 is None:return None
 ret1=(price-r1)/fx.PIP
 ret5=(price-r5)/fx.PIP
 range5=(float(mids.max())-float(mids.min()))/fx.PIP
 # Exactly one regime priority, using completed observations only.
 if range5>=7.5 or abs(ret5)>=4.5:regime='volatile'
 elif abs(ret5)>=2.0 and range5>=3.0:regime='trending'
 elif abs(ret5)<=1.25 and range5<=4.75:regime='ranging'
 else:regime='mixed'
 signals,market=fx.decision_signals(book,ts,now)
 if market.get('reason')!='OK':return None
 e=bisect.bisect_left(ts['gbpusd'],now+500)
 entry=book['gbpusd'][e] if e<len(book['gbpusd']) else None
 if entry is None or entry[0]>now+4000:return None
 spread=(entry[1]-entry[2])/fx.PIP
 if not 0<spread<=1.5 or market['median_spread_5m_pips']>1.35:return None
 cross={}
 for pair,secs in [('eurusd',60),('eurgbp',60),('eurgbp',300)]:
  q=fx.snapshot(book[pair],ts[pair],now,300000)
  past=fx.older_mid(book[pair],ts[pair],now,secs*1000)
  if not q or past is None:return None
  cross[(pair,secs)]=((q[-1][1]+q[-1][2])/2-past)/fx.PIP
 in1=[(q[1]+q[2])/2 for q in window1]
 rate=len(window1)
 tickdiff=np.diff(m1)
 up=(int(np.count_nonzero(tickdiff>0))-int(np.count_nonzero(tickdiff<0)))/max(1,len(tickdiff))
 imbalance=[(q[4]-q[3])/(q[4]+q[3]) for q in window1 if q[4]+q[3]>0]
 quoted_imbalance=float(np.mean(imbalance)) if imbalance else 0.
 z=(price-float(mids.mean()))/(float(mids.std())+1e-12)
 pastprice=[(q[1]+q[2])/2 for q in lookback if q[0]<now-30000]
 if not pastprice:return None
 volatility_1m=float(np.std(tickdiff))/fx.PIP if len(tickdiff)>2 else 0.
 vals={
   'ret1':ret1,'ret5':ret5,'range5':range5,'spread':spread,'tick_rate':rate,
   'gbp_upticks':up,'quoted_volume_imbalance':quoted_imbalance,
   'EURUSD_ret1':cross[('eurusd',60)],'EURGBP_ret1':cross[('eurgbp',60)],
   'EURGBP_ret5':cross[('eurgbp',300)],'z5':z,
   'rsi_proxy':sum(q>0 for q in tickdiff)/max(1,len(tickdiff)),
   'hour':(now-fx.to_utc_ms(stamp(now)[:10]+'T00:00:00Z'))/3600000,
   'cross_pair_divergence':cross[('eurusd',60)]-cross[('eurgbp',60)],
   'vol_pips_1m':volatility_1m,
   'price_to_10m_high':(price-max(pastprice))/fx.PIP,
   'price_to_10m_low':(price-min(pastprice))/fx.PIP,
 }
 return {'regime':regime,'features':vals,'signals':signals,'now':now,'entry_idx':e,
         'entry_time':entry[0],'spread_pips':spread}

def expert_votes(s):
 def both(a,b):
  return a if a and a==b else 0
 gbp5=s['GBP_Momentum_5m'];gbp1=s['GBP_Momentum_1m']; br=s['GBP_Range_Breakout']
 cross1=s['EURUSD_Momentum_1m'];cross2=s['EURGBP_Inverse_1m'];cross5=s['EURGBP_Inverse_5m']
 mr=s['GBP_Price_Extreme_Fade'];tick=s['Tick_Uptick_Balance'];volume=s['TopQuote_Volume_Imbalance']
 return {'trend_momentum':both(gbp1,gbp5),
         'trend_breakout':both(br,gbp5),
         'range_reversion':mr if mr and (gbp1==0 or gbp1== -mr) else 0,
         'extreme_reversion':mr,
         'cross_market':both(cross1,cross2),
         'tick_imbalance':both(tick,volume),
         'trend_cross':both(gbp5,cross5)}

def build_rows(manifest):
 inventory={x['day']:x for x in manifest['days']}
 observed=[];missing=[]
 dates=sorted(d for w in manifest['windows'] for d in w['days'])
 for day in dates:
  try:
   book=historical_day(day,inventory)
   ts={name:[r[0] for r in ticks] for name,ticks in book.items()}
   good=0
   for now in range(fx.to_utc_ms(day+'T07:15:00Z'),fx.to_utc_ms(day+'T08:45:00Z')+1,60000):
    row=features_at(book,ts,now)
    if row is None:continue
    row['date']=day;row['year']=int(day[:4])
    row['window_id']=next(i for i,w in enumerate(manifest['windows']) if day in w['days'])
    row['expert']=expert_votes(row['signals'])
    row['votes_buy']=sum(x==1 for x in row['signals'].values())
    row['votes_sell']=sum(x==-1 for x in row['signals'].values())
    row['family_votes']=fx.diverse_family_votes(row['signals'])
    row['outcomes']={}
    for horizon in HORIZONS:
     if horizon==30:stop,target=2.,2.
     elif horizon==120:stop,target=4.,4.
     else:stop,target=6.,6.
     futures={}
     for side in [1,-1]:
      result=fx.exits(book['gbpusd'],ts['gbpusd'],row['entry_idx'],side,horizon,stop,target)
      futures['1' if side==1 else '-1']=(
       {'net_usd':float(result['pnl_usd']),
        'exit_time_ms':ts['gbpusd'][result['exit_tick_index']]}
       if result else None)
     row['outcomes'][str(horizon)]=futures
    observed.append(row);good+=1
   print('REGIME_DAY',day,'valid_decisions',good,'tick_counts',{k:len(v) for k,v in book.items()},flush=True)
  except (FileNotFoundError,RuntimeError,ValueError,KeyError) as e:
   missing.append({'date':day,'reason':str(e)})
   print('REGIME_MISSING',day,str(e),flush=True)
 return observed,missing

def predictions(rows,train_mask):
 # Fit both hypothetical directional returns for each horizon, including
 # transaction costs. Never use validation/test outcomes when fitting models.
 X=np.asarray([[r['features'][k] for k in REGIME_FEATURES] for r in rows],np.float32)
 train_idxs=np.flatnonzero(train_mask)
 if len(train_idxs)<2000:raise ValueError('Too little chronological training data')
 for horizon in HORIZONS:
  for side in ('1','-1'):
   yidx=np.asarray([i for i in train_idxs if rows[i]['outcomes'][str(horizon)][side] is not None],int)
   y=np.asarray([rows[i]['outcomes'][str(horizon)][side]['net_usd'] for i in yidx])
   estimators={
     'ML_LightGBM':LGBMRegressor(n_estimators=160,max_depth=4,num_leaves=12,
        learning_rate=.04,reg_lambda=12,min_child_samples=65,
        colsample_bytree=.85,random_state=MODEL_SEED,verbosity=-1,n_jobs=2),
     'ML_Ridge':make_pipeline(StandardScaler(),Ridge(alpha=180.))
   }
   for name,model in estimators.items():
    model.fit(X[yidx],y)
    estimates=model.predict(X)
    for i,r in enumerate(rows):
     r.setdefault('predictions',{}).setdefault(str(horizon),{}).setdefault(name,{})[side]=float(estimates[i])
   print('MODEL_TRAINED',horizon,side,'rows',len(yidx),
         'target_mean',round(float(y.mean()),5),flush=True)
 # Express predictions as paper signals only if expected win after costs
 # exceeds 5 cents; make independent side choice by larger predicted net PnL.
 for r in rows:
  for horizon in HORIZONS:
   for name in ('ML_LightGBM','ML_Ridge'):
    pred=r['predictions'][str(horizon)][name]
    buy=pred['1'];sell=pred['-1']
    winner=1 if buy>sell+.03 and buy>.05 else (
      -1 if sell>buy+.03 and sell>.05 else 0)
    r['expert'].setdefault(name,{})[str(horizon)]=winner

def expected_side(row,expert,horizon):
 val=row['expert'].get(expert,0)
 if isinstance(val,dict):return int(val.get(str(horizon),0))
 return int(val)

def consensus(row,threshold):
 buy=row['votes_buy'];sell=row['votes_sell']
 side=1 if buy>=threshold and buy>sell else (-1 if sell>=threshold and sell>buy else 0)
 if side and sum(v==side for v in row['family_votes'].values())<3:return 0
 return side

def simulate(rows,policy,collect_trades=True):
 # Each scenario resets the *same* illustrative $150 account every new date.
 # No sample selection using future outcomes and no overlapping positions.
 byday=collections.defaultdict(list)
 for r in rows:byday[r['date']].append(r)
 total=0.;trades=[];per_day={};pnl_by_window=collections.defaultdict(float)
 for day,events in sorted(byday.items()):
  equity=fx.START_EQUITY
  occupied_through=0
  day_net=0.
  count=0;wins=0;skips=collections.Counter()
  for r in sorted(events,key=lambda x:x['now']):
   if equity-fx.START_EQUITY<=fx.DAILY_STOP_USD:
    skips['DAILY_LOSS_PAUSE']+=1;continue
   answer=policy(r)
   if answer is None:
    skips['NO_APPROVED_REGIME_MODEL']+=1;continue
   expert,side,horizon=answer
   if not side:
    skips['MODEL_NO_SIGNAL']+=1;continue
   if r['entry_time']<=occupied_through:
    skips['OVERLAPPING_POSITION']+=1;continue
   outcome=r['outcomes'][str(horizon)][str(side)]
   if outcome is None:
    skips['NO_EXIT_QUOTE']+=1;continue
   amount=outcome['net_usd']
   occupied_through=outcome['exit_time_ms']
   equity+=amount;day_net+=amount;count+=1;wins+=int(amount>0)
   if collect_trades:trades.append({'date':day,'utc':stamp(r['now']),
    'model':expert,'regime':r['regime'],'side':'BUY' if side>0 else 'SELL',
    'hold_s':horizon,'net_usd':amount,'spread_pips':round(r['spread_pips'],4)})
  per_day[day]={'net_usd':round(day_net,5),'trades':count,'wins':wins,'skips':dict(skips)}
  total+=day_net
  pnl_by_window[events[0]['window_id']]+=day_net
 return {'net_usd':round(total,5),'trades':sum(v['trades'] for v in per_day.values()),
   'wins':sum(v['wins'] for v in per_day.values()),'days':len(per_day),
   'profitable_days':sum(v['net_usd']>0 for v in per_day.values()),
   'windows_profitable':sum(v>0 for v in pnl_by_window.values()),
   'net_by_window':{str(k):round(v,5) for k,v in sorted(pnl_by_window.items())},
   'daily':per_day,'trades_log':trades if collect_trades else []}

def subset_validation_metrics(rows,regime,expert,horizon,year=2024):
 selected=[r for r in rows if r['year']==year and r['regime']==regime]
 result=simulate(selected,lambda r:(expert,expected_side(r,expert,horizon),horizon),False)
 # Per-trade scores recomputed from aggregated daily ROI WITHOUT overlaps;
 # use full array under exactly same trading restrictions.
 pnl=[]
 for day,events in collections.groupby(sorted(selected,key=lambda r:(r['date'],r['now'])),lambda r:r['date']):
  occupied=0.;net=0.
  for r in events:
   if net<=fx.DAILY_STOP_USD:continue
   direction=expected_side(r,expert,horizon)
   if not direction or r['entry_time']<=occupied:continue
   outcome=r['outcomes'][str(horizon)][str(direction)]
   if outcome is None:continue
   net+=outcome['net_usd']
   occupied=outcome['exit_time_ms']
   pnl.append(float(outcome['net_usd']))
 n=len(pnl)
 if n!=result['trades']:
  raise RuntimeError('Validation trade score disagrees with execution simulator')
 average=statistics.mean(pnl) if pnl else 0
 sd=statistics.stdev(pnl) if n>=2 else 0
 lower=average-sd/math.sqrt(n) if n>=2 else -1.
 bywindow=result['net_by_window']
 return {k:result[k] for k in ['net_usd','trades','wins','days','profitable_days','windows_profitable','net_by_window']} | {
  'average_pnl_usd':round(average,5),
  'standard_error_lower_mean_usd':round(lower,5),'candidate_regime':regime,
  'candidate_expert':expert,'hold_seconds':horizon}

def main():
 manifest=json.loads(MANIFEST.read_text())
 if manifest['random_seed']!=260501 or len(manifest['windows'])!=15:
  raise RuntimeError('Not the predeclared 15-window random calendar')
 rows,missing=build_rows(manifest)
 if not rows:raise RuntimeError('No tick events')
 partitions={name:[r for r in rows if r['year'] in years] for name,years in
              [('train',(2022,2023)),('validation',(2024,)),('test',(2025,2026))]}
 print('REGIME_SAMPLES',json.dumps({k:len(v) for k,v in partitions.items()}),flush=True)
 training=np.asarray([r['year'] in (2022,2023) for r in rows],bool)
 predictions(rows,training)
 validation=partitions['validation']
 test=partitions['test']
 leaderboard={}
 selected_research={}
 selected_strict={}
 for regime in REGIMES:
  shortlist=[]
  for expert in EXPERTS:
   for horizon in HORIZONS:
    met=subset_validation_metrics(validation,regime,expert,horizon)
    shortlist.append(met)
  ordered=sorted(shortlist,key=lambda v:(v['net_usd'],v['trades']),reverse=True)
  leaderboard[regime]=ordered
  # Research switch: select one regime specialist based only on 2024
  # validation, with at least 12 transactions and net positive.
  qualified=[s for s in ordered if s['trades']>=12 and s['net_usd']>0]
  chosen=qualified[0] if qualified else None
  selected_research[regime]={
    'expert':chosen['candidate_expert'],'hold_seconds':chosen['hold_seconds'],
    'validation':chosen} if chosen else None
  # Strict switch: min 20 validation trades, SE-penalized mean >0,
  # and two distinct validation fortnights showing positive PnL.
  strict=[s for s in ordered if s['trades']>=20
        and s['standard_error_lower_mean_usd']>0 and s['windows_profitable']>=2]
  winner=strict[0] if strict else None
  selected_strict[regime]={
    'expert':winner['candidate_expert'],'hold_seconds':winner['hold_seconds'],
    'validation':winner} if winner else None
  print('REGIME_SELECTION',regime,json.dumps({
    'research':selected_research[regime],'strict':selected_strict[regime],
    'top_validation':ordered[:5]},sort_keys=True),flush=True)
 def switching(selected):
  def policy(r):
   choice=selected.get(r['regime'])
   if choice is None:return None
   ex=choice['expert'];horizon=choice['hold_seconds']
   return ex,expected_side(r,ex,horizon),horizon
  return policy
 reports={
  'regime_switch_research':simulate(test,switching(selected_research)),
  'regime_switch_strict':simulate(test,switching(selected_strict))}
 for horizon in HORIZONS:
  for threshold in (6,7,8):
   reports[f'fixed_consensus_{threshold}of10_{horizon}s']=simulate(test,lambda r,h=horizon,t=threshold:
     ('consensus_'+str(t),consensus(r,t),h))
 # Single-expert universal benchmarks use fixed specialists per expert and
 # horizon, not selected after inspecting unseen test outcomes.
 for expert in ('trend_momentum','range_reversion','cross_market','tick_imbalance',
                'ML_LightGBM','ML_Ridge'):
  reports['standalone_'+expert+'_120s']=simulate(test,lambda r,e=expert:
    (e,expected_side(r,e,120),120))
 for name,r in reports.items():
  print('REGIME_TEST_RESULT',name,json.dumps({k:r[k] for k in
    ['net_usd','trades','wins','days','profitable_days','windows_profitable',
     'net_by_window']},sort_keys=True),flush=True)
 report={
  'study':'Frozen context-dependent specialist models with strict chronological holdout',
  'design':'15 two-week periods randomized before seeing outcome; training 2022-23, select on 2024, evaluate once on 2025-26',
  'random_seed':260501,'source':manifest['source'],
  'full_tick_days':len({r['date'] for r in rows}),
  'missing_days':missing,'requested_days':150,
  'full_24h_market':False,'time_window_utc':'07:00-09:00',
  'initial_account_usd_per_day':150,'position_gbp':1000,
  'data_partition_decisions':{k:len(v) for k,v in partitions.items()},
  'data_partition_days':{k:len({r['date'] for r in v}) for k,v in partitions.items()},
  'regime_definitions':'volatile=5m range>=7.5p or |5m return|>=4.5p; trending=|5m return|>=2p and range>=3p; ranging=|5m return|<=1.25p and range<=4.75p; else mixed',
  'features':REGIME_FEATURES,
  'expert_names':EXPERTS,
  'model_specs':'LightGBM regressors and standardized Ridge each predict 30/120/300s cost-net BUY or SELL outcomes, models fitted on train 2022-23 ONLY',
  'rules':'7 specialists + 2 regressors; select at most one expert and horizon per regime from validation 2024 only; 2025-26 remains held out',
  'research_selection':selected_research,
  'strict_selection':selected_strict,
  'validation_all_candidates':leaderboard,
  'heldout_test_results':reports,
  'raw_market_days':manifest['days'],
  'no_live_orders':True,'historical_news_veto_applied':False,
  'limitations':['Historical economic-news calendar not available; cannot claim fully news-filtered strategy',
   'Simulation uses quote tick prices; broker execution, margin and slippage vary',
   'Numerous specialists and horizons screened on 2024; selection can overfit validation',
   'Adjacent training targets overlap, reducing effective independent sample size',
   'Consistent profit across all tested market conditions is not guaranteed',
   'Retrospective split with 2025-26 used ONCE; any follow-up tuning on these outcomes requires NEW holdout',
   'Per-day $150 notional balance reinitialization; account equity is not compounded',
   'Top-of-book quote volumes are not executed trade order flow']}
 DST.write_text(json.dumps(report,indent=2)+'\n')
 print('REGIME_RESULT_FILE',DST,'UNSEEN_TEST_EXAMINED_ONCE',True,'NO_LIVE_ORDERS',True)
if __name__=='__main__':main()
