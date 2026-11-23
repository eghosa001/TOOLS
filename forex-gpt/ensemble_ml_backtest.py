#!/usr/bin/env python3
"""Prospective-design 10-engine GBPUSD study. Prior-only training, 5-day blind test.
6 supervised ML families (actual fitted models) + 4 distinct rule families.
No broker access, no live orders, no inference from 2026-11-16..20 outcomes.
Run after ensemble_ml_fetch.cjs, from repository root.
"""
import json, math, os, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import balanced_accuracy_score
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

DATA=Path('forex-gpt/.tmp/consensus_ml_m1.json')
OUT=Path('forex-gpt/.tmp/ensemble_ml_results.json')
DAYS=['2026-11-16','2026-11-17','2026-11-18','2026-11-19','2026-11-20']
TRAIN_END='2026-10-30'
VALID_BEGIN='2026-11-02'
VALID_END='2026-11-13'
TEST_BEGIN='2026-11-16'
PIP=0.0001
START_USD=150.0
UNITS=1000
SLIP_PIPS=0.2
FEE_USD=0.06
MAX_SPREAD=1.5
STOP_PIPS=8.0
TAKE_PIPS=12.0
HOLD_MINS=15
DAILY_LOSS_PAUSE=-3.0
ML_NAMES=['LightGBM','XGBoost','CatBoost','ExtraTrees','LogisticRegression','RBF_SVM']
RULE_NAMES=['MultiTF_Trend','Donchian_Breakout','Bollinger_Reversion','Momentum_Regime']
SEED=23

def safe_json_dumps(value, **kwargs):
    def convert(v):
        if isinstance(v, np.generic): return v.item()
        raise TypeError(f'Non-JSON value: {type(v).__name__}')
    return json.dumps(value, default=convert, **kwargs)

def signal(x, eps=0.):
    return np.where(x>eps,1,np.where(x< -eps,-1,0)).astype(np.int8)

def load_market():
    raw=json.loads(DATA.read_text())
    if raw.get('symbol')!='gbpusd' or raw.get('timeframe')!='m1':
        raise ValueError('unexpected source')
    b=np.asarray(raw['sides']['bid'],dtype=np.float64)
    a=np.asarray(raw['sides']['ask'],dtype=np.float64)
    if len(b)<65000 or len(a)<65000:raise ValueError('Insufficient history')
    if len(b)!=len(a) or np.any(b[:,0]!=a[:,0]):
        raise ValueError('Unaligned bid and ask')
    if not np.all(np.isfinite(b)) or not np.all(np.isfinite(a)):
        raise ValueError('Non-finite data')
    if np.any(b[:,1]>a[:,1]) or np.any(b[:,4]>a[:,4]):
        raise ValueError('Crossed quotes')
    return b,a

def build_features(b,a):
    ts=b[:,0].astype(np.int64)
    dt=pd.to_datetime(ts,unit='ms',utc=True)
    cb=pd.Series((b[:,4]+a[:,4])/2)
    hb=pd.Series((b[:,2]+a[:,2])/2)
    lb=pd.Series((b[:,3]+a[:,3])/2)
    op=pd.Series((b[:,1]+a[:,1])/2)
    ret=cb.diff()/PIP
    spread=(a[:,1]-b[:,1])/PIP
    ema9=cb.ewm(span=9,adjust=False).mean()
    ema30=cb.ewm(span=30,adjust=False).mean()
    ema90=cb.ewm(span=90,adjust=False).mean()
    std20=cb.rolling(20).std()
    hi20=hb.shift(1).rolling(20).max()
    lo20=lb.shift(1).rolling(20).min()
    vol15=ret.rolling(15).std()
    vol60=ret.rolling(60).std()
    rsi_up=ret.clip(lower=0).rolling(14).mean()
    rsi_dn=(-ret.clip(upper=0)).rolling(14).mean()
    rsi=100-100/(1+rsi_up/(rsi_dn+1e-9))
    tr=pd.concat([(hb-lb),(hb-cb.shift(1)).abs(),(lb-cb.shift(1)).abs()],axis=1).max(axis=1)
    atr15=tr.rolling(15).mean()/PIP
    body=(cb-op)/PIP
    x=pd.DataFrame(index=np.arange(len(ts)))
    for n in [1,3,5,10,15,30,60]:
        x['ret_'+str(n)]=(cb-cb.shift(n))/PIP
    x['ema9_30']=(ema9-ema30)/PIP
    x['ema30_90']=(ema30-ema90)/PIP
    x['px_ema30']=(cb-ema30)/PIP
    x['z20']=(cb-cb.rolling(20).mean())/(std20+1e-8)
    x['channel20_pct']=(cb-lo20)/(hi20-lo20+1e-8)
    x['channel20_width']=(hi20-lo20)/PIP
    x['vol15']=vol15
    x['vol60']=vol60
    x['vol_ratio']=vol15/(vol60+1e-6)
    x['atr15']=atr15
    x['rsi14']=rsi
    x['body']=body
    x['body5']=body.rolling(5).mean()
    x['up10']=ret.gt(0).rolling(10).mean()
    x['spread']=spread
    x['hour_sin']=np.sin(2*np.pi*(dt.hour.to_numpy()+dt.minute.to_numpy()/60)/24)
    x['hour_cos']=np.cos(2*np.pi*(dt.hour.to_numpy()+dt.minute.to_numpy()/60)/24)
    x['weekday']=dt.weekday.to_numpy()
    x=x.replace([np.inf,-np.inf],np.nan)
    # Strictly causal rule engines: all use only completed bars at index i.
    rules=pd.DataFrame(index=x.index)
    trend1=signal(x['ema9_30'].to_numpy(),.35)
    trend2=signal(x['ema30_90'].to_numpy(),.45)
    rules['MultiTF_Trend']=np.where(trend1==trend2,trend1,0)
    rules['Donchian_Breakout']=np.where(cb.to_numpy()>hi20.to_numpy()+.15*PIP,1,
                                  np.where(cb.to_numpy()<lo20.to_numpy()-.15*PIP,-1,0))
    # Fade extremes only in genuinely quiet regimes.
    quiet=(x['vol_ratio'].to_numpy()<1.05)
    zz=x['z20'].to_numpy()
    rules['Bollinger_Reversion']=np.where(quiet& (zz>1.35),-1,
                                      np.where(quiet&(zz< -1.35),1,0))
    # Short-horizon momentum specialist when recent 15m volatility supports movement.
    rv=x['ret_5'].to_numpy()
    highvol=(x['vol_ratio'].to_numpy()>1.10)&(x['atr15'].to_numpy()>0.6)
    rules['Momentum_Regime']=np.where(highvol,signal(rv,1.1),0)
    # Times are M1 candle STARTS. Signal after completed bar i,
    # enter at next candle i+1 open (idealized immediate boundary order).
    n=len(ts)
    backward=np.ones(n,dtype=np.int32)
    for i in range(1,n):
        if ts[i]-ts[i-1]==60000:backward[i]=backward[i-1]+1
    entry_i=np.arange(n)+1
    exit_i=entry_i+HOLD_MINS
    legal=exit_i<n
    good=np.where(legal)[0]
    legal[good]&=ts[exit_i[good]]-ts[good]==(HOLD_MINS+1)*60000
    legal&=backward>=121
    hour=dt.hour.to_numpy()
    minute=dt.minute.to_numpy()
    # Each entry at hh:00, hh:05, etc; no weekends; London/NY overlap window.
    legal&=(hour>=7)&(hour<17)&(minute%5==4)&(dt.weekday.to_numpy()<5)
    legal&=x.notna().all(axis=1).to_numpy()
    idx=np.flatnonzero(legal)
    if len(idx)<2000:raise RuntimeError('Too few valid historical decisions: '+str(len(idx)))
    e=entry_i[idx];f=exit_i[idx]
    gross_long=(b[f,1]-a[e,1])*UNITS
    gross_short=(b[e,1]-a[f,1])*UNITS
    fee=FEE_USD+SLIP_PIPS*PIP*UNITS
    net_long=gross_long-fee
    net_short=gross_short-fee
    # Labels account for bid/ask + cost. 0 SELL, 1 NO-EDGE, 2 BUY.
    labels=np.where((net_long>0)&(net_long>net_short),2,
                    np.where((net_short>0)&(net_short>net_long),0,1)).astype(int)
    times=dt[idx]
    dates=times.date.astype(str)
    splits={
      'train':(dates<=TRAIN_END),
      'validation':((dates>=VALID_BEGIN)&(dates<=VALID_END)),
      'test':((dates>=TEST_BEGIN)&(dates<=DAYS[-1]))
    }
    for name,m in splits.items():
        print('SPLIT',name,int(m.sum()),'date_start',str(dates[m][0]),'date_end',str(dates[m][-1]),flush=True)
        if m.sum() < (1000 if name=='train' else 200):
            raise RuntimeError('Insufficient split '+name)
    return {'b':b,'a':a,'ts':ts,'features':x.iloc[idx].to_numpy(dtype=np.float32),
            'rules':rules.iloc[idx].fillna(0).astype(np.int8).to_numpy(),
            'idx':idx,'dates':dates,'splits':splits,'labels':labels,'spread':spread}

def make_models():
    return {
      'LightGBM':LGBMClassifier(n_estimators=180,num_leaves=15,max_depth=6,
         learning_rate=.035,colsample_bytree=.8,subsample=.85,reg_lambda=6,
         min_child_samples=45,random_state=SEED,verbosity=-1,n_jobs=2),
      'XGBoost':XGBClassifier(n_estimators=180,max_depth=3,learning_rate=.045,
         subsample=.8,colsample_bytree=.85,reg_lambda=12,min_child_weight=15,
         objective='multi:softprob',num_class=3,eval_metric='mlogloss',
         random_state=SEED,n_jobs=2,tree_method='hist'),
      'CatBoost':CatBoostClassifier(iterations=230,depth=4,learning_rate=.045,
         l2_leaf_reg=9,loss_function='MultiClass',verbose=False,
         random_seed=SEED,thread_count=2),
      'ExtraTrees':ExtraTreesClassifier(n_estimators=250,min_samples_leaf=35,
         max_features=.8,max_depth=9,random_state=SEED,n_jobs=2),
      'LogisticRegression':make_pipeline(StandardScaler(),
         LogisticRegression(C=.4,max_iter=400,random_state=SEED)),
      'RBF_SVM':make_pipeline(StandardScaler(),
         SVC(C=.6,gamma='scale',kernel='rbf',cache_size=512,decision_function_shape='ovr'))
    }

def train_and_vote(raw):
    X=raw['features'];Y=raw['labels']
    tr=raw['splits']['train']
    va=raw['splits']['validation']
    te=raw['splits']['test']
    votes={}
    metrics={}
    models=make_models()
    for name in ML_NAMES:
        mod=models[name]
        mod.fit(X[tr],Y[tr])
        # Class 1 = no edge. No performance-based refitting against the test.
        pred=mod.predict(X).astype(int)
        if len(pred)!=len(X):raise RuntimeError('Prediction length error '+name)
        votes[name]=np.where(pred==2,1,np.where(pred==0,-1,0)).astype(np.int8)
        metrics[name]={
          'validation_balanced_accuracy':round(float(balanced_accuracy_score(Y[va],pred[va])),4),
          'test_balanced_accuracy_diagnostic':round(float(balanced_accuracy_score(Y[te],pred[te])),4),
          'validation_voting_pct':round(float(np.mean(votes[name][va]!=0)*100),2),
          'test_voting_pct':round(float(np.mean(votes[name][te]!=0)*100),2)}
        print('MODEL',name,safe_json_dumps(metrics[name]),flush=True)
    for j,name in enumerate(RULE_NAMES):
        votes[name]=raw['rules'][:,j]
    stacked=np.column_stack([votes[k] for k in ML_NAMES+RULE_NAMES])
    if stacked.shape!=(len(X),10):raise RuntimeError('Incorrect vote matrix')
    return votes,stacked,metrics

def simulate(rows,selected,raw):
    # selected: signals on all sampled decision rows. Only test rows are replayed.
    b=raw['b'];a=raw['a'];ts=raw['ts'];idx=raw['idx']
    dates=raw['dates'];spread=raw['spread']
    daily={d:{'trades':0,'wins':0,'losses':0,'net_usd':0.} for d in DAYS}
    transactions=[]
    equity=START_USD;peak=START_USD;drawdown=0.;blocked_through=-1
    rejected={'no_consensus':0,'overlap':0,'spread':0,'daily_pause':0}
    for j in np.flatnonzero(raw['splits']['test']):
        side=int(selected[j])
        if side==0:
            rejected['no_consensus']+=1;continue
        i=int(idx[j]);entry=i+1;end=entry+HOLD_MINS
        day=str(dates[j])
        if entry<=blocked_through:
            rejected['overlap']+=1;continue
        if daily[day]['net_usd']<=DAILY_LOSS_PAUSE:
            rejected['daily_pause']+=1;continue
        entry_spread=(a[entry,1]-b[entry,1])/PIP
        if not(0<entry_spread<=MAX_SPREAD):
            rejected['spread']+=1;continue
        fill=a[entry,1] if side==1 else b[entry,1]
        close=0.;reason='TIME_EXIT';end_idx=end
        # Stop first if both stop and target lie within same minute.
        for k in range(entry,end):
            if side==1:
                stop=fill-STOP_PIPS*PIP;target=fill+TAKE_PIPS*PIP
                if b[k,1]<=stop or b[k,3]<=stop:
                    close=min(b[k,1],stop);reason='STOP';end_idx=k;break
                if b[k,2]>=target:
                    close=target;reason='TARGET';end_idx=k;break
            else:
                stop=fill+STOP_PIPS*PIP;target=fill-TAKE_PIPS*PIP
                if a[k,1]>=stop or a[k,2]>=stop:
                    close=max(a[k,1],stop);reason='STOP';end_idx=k;break
                if a[k,3]<=target:
                    close=target;reason='TARGET';end_idx=k;break
        if not close:
            close=b[end,1] if side==1 else a[end,1]
        p=float(round(side*(close-fill)*UNITS -FEE_USD -SLIP_PIPS*PIP*UNITS,5))
        equity+=p;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
        daily[day]['trades']+=1
        daily[day]['net_usd']+=p
        daily[day]['wins']+=int(p>0)
        daily[day]['losses']+=int(p<0)
        blocked_through=end_idx
        transactions.append({
          'decision_utc':pd.to_datetime(int(ts[i])+60000,unit='ms',utc=True).isoformat(),
          'side':'BUY' if side==1 else 'SELL','entry_utc':pd.to_datetime(int(ts[entry]),unit='ms',utc=True).isoformat(),
          'exit_utc':pd.to_datetime(int(ts[end_idx]),unit='ms',utc=True).isoformat(),
          'entry_spread_pips':round(float(entry_spread),3),'net_usd':p,
          'exit_reason':reason,'votes_buy':int(np.sum(rows[j]==1)),
          'votes_sell':int(np.sum(rows[j]==-1))})
    for d in daily.values():d['net_usd']=round(d['net_usd'],5)
    won=[t['net_usd'] for t in transactions if t['net_usd']>0]
    lost=[t['net_usd'] for t in transactions if t['net_usd']<0]
    return {'net_usd':round(equity-START_USD,5),
      'end_balance_usd':round(equity,5),'return_pct':round((equity/START_USD-1)*100,3),
      'trades':len(transactions),'wins':len(won),'losses':len(lost),
      'win_rate_pct':round(100*len(won)/len(transactions),2) if transactions else 0.,
      'profit_factor':round(sum(won)/-sum(lost),3) if lost else None,
      'closed_trade_max_drawdown_usd':round(drawdown,5),
      'profitable_days':sum(t['net_usd']>0 for t in daily.values()),
      'daily':daily,'rejected':rejected,'transactions':transactions}

def main():
    np.random.seed(SEED)
    b,a=load_market()
    raw=build_features(b,a)
    votes,V,metrics=train_and_vote(raw)
    vb=(V==1).sum(axis=1)
    vs=(V==-1).sum(axis=1)
    results={}
    for votes_needed in [6,7,8]:
        sides=np.where((vb>=votes_needed)&(vb>vs),1,
                np.where((vs>=votes_needed)&(vs>vb),-1,0))
        results[str(votes_needed)]=simulate(V,sides,raw)
        r=results[str(votes_needed)]
        print('ENSEMBLE_THRESHOLD_'+str(votes_needed),safe_json_dumps({
           k:r[k] for k in r if k!='transactions'},sort_keys=True),flush=True)
    standalone={}
    for name in ML_NAMES+RULE_NAMES:
        r=simulate(V,votes[name],raw)
        standalone[name]={k:r[k] for k in ['trades','net_usd','end_balance_usd','win_rate_pct']}
    print('STANDALONE_TEST',safe_json_dumps(standalone),flush=True)
    report={
      'status':'five-day chronological held-out historical paper only',
      'pair':'GBPUSD','source':'Dukascopy bid/ask M1',
      'quote_count':len(b),'starting_capital_usd':START_USD,
      'model_families':ML_NAMES,'structural_rules':RULE_NAMES,
      'train_until_utc':TRAIN_END,'validation_utc':f'{VALID_BEGIN} through {VALID_END}',
      'sealed_test_utc':f'{TEST_BEGIN} through {DAYS[-1]}',
      'split_counts':{k:int(v.sum()) for k,v in raw['splits'].items()},
      'execution':{'size_gbp':UNITS,'entry':'next minute open after completed signal bar',
      'hold_minutes':HOLD_MINS,'stop_pips':STOP_PIPS,'target_pips':TAKE_PIPS,
      'max_entry_spread_pips':MAX_SPREAD,'additional_slippage_rt_pips':SLIP_PIPS,
      'commission_usd_round_trip':FEE_USD,'daily_stop_usd':DAILY_LOSS_PAUSE,
      'no_overlap':True,'no_broker_orders':True,
      'stops':'M1 high/low estimated, stop-first on ambiguity',
      'session':'M1 every five minutes, entries approximately 07:00-17:00 UTC'},
      'metrics':metrics,'results':results,'standalone':standalone,
      'limitations':['Models are trained fresh on 2026 prior data; no pre-trained third-party bot claimed',
      'Models can still be correlated and overfit; holdout has only five days',
      'M1 bar simulation is not tick-accurate; stop execution is hypothetical',
      'Actual spread used at entry/exit, other slippage and commission modeled',
      'No verified broker fills, financing, margin calls, swap or fast execution',
      'No guarantee of profitability or future performance']}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(safe_json_dumps(report,indent=2)+'\n')
    print('ARTIFACT',str(OUT),flush=True)

if __name__=='__main__':
    main()
