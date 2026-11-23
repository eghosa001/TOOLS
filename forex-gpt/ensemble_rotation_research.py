#!/usr/bin/env python3
"""Screen new GBPUSD strategies on *prior* validation weeks and replay 4 later weeks.
Historical paper research only; zero broker orders. 10 votes: 4 retained + 6 selected.
Selection is made before each week's test, no future prices in features/selection.
Earlier 2026-11-16..20 was ALREADY viewed; no claim of pristine unseen performance.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import ensemble_ml_backtest as engine

SEED=23
DST=Path('forex-gpt/.tmp/ensemble_rotation_results.json')
FOLDS=[
 ('2026-08-21','2026-08-24','2026-09-04','2026-09-07','2026-09-11'),
 ('2026-09-18','2026-09-21','2026-10-02','2026-10-05','2026-10-09'),
 ('2026-10-16','2026-10-19','2026-10-30','2026-11-02','2026-11-06'),
 ('2026-10-30','2026-11-02','2026-11-13','2026-11-16','2026-11-20'),
]
FEATURES=['ret_1','ret_3','ret_5','ret_10','ret_15','ret_30','ret_60',
          'ema9_30','ema30_90','px_ema30','z20','channel20_pct',
          'channel20_width','vol15','vol60','vol_ratio','atr15','rsi14',
          'body','body5','up10','spread','hour_sin','hour_cos','weekday']
INCUMBENTS=['RBF_SVM','Donchian_Breakout','Bollinger_Reversion','Momentum_Regime']
QUALITY_MIN_TRADES=10
QUALITY_MIN_WINNERS=3
# All test configurations are registered before any fold outcome is evaluated.
THRESHOLDS=[6,7,8]
def sign(v,epsilon=0):
    return np.where(v>epsilon,1,np.where(v< -epsilon,-1,0)).astype(np.int8)
def directional(buy,sell):
    return np.where(buy&~sell,1,np.where(sell&~buy,-1,0)).astype(np.int8)
def candidates(raw):
    x={n:raw['features'][:,i].astype(float) for i,n in enumerate(FEATURES)}
    t=pd.to_datetime(raw['ts'][raw['idx']],unit='ms',utc=True)
    hour=t.hour.to_numpy()
    quiet=x['vol_ratio']<1.07
    trend_pos=(x['ema9_30']>.35)&(x['ema30_90']>.4)
    trend_neg=(x['ema9_30']<-.35)&(x['ema30_90']<-.4)
    c={}
    c['ATR_Channel_Break']=directional((x['channel20_pct']>1.02)&(x['atr15']>.8)&(x['vol_ratio']>1.08),
                                       (x['channel20_pct']<-.02)&(x['atr15']>.8)&(x['vol_ratio']>1.08))
    c['RSI_Trend_Confirm']=directional(trend_pos&(x['rsi14']>57)&(x['ret_15']>1.2),
                                       trend_neg&(x['rsi14']<43)&(x['ret_15']< -1.2))
    c['Trend_Pullback']=directional(trend_pos&(x['px_ema30']>-.3)&(x['px_ema30']<1.0)&(x['ret_3']<-.45),
                                    trend_neg&(x['px_ema30']<.3)&(x['px_ema30']> -1.0)&(x['ret_3']>.45))
    c['RSI_Extreme_Fade']=directional((x['rsi14']<28)&(x['z20']< -1.2)&quiet,
                                      (x['rsi14']>72)&(x['z20']>1.2)&quiet)
    c['ZScore_Deep_Fade']=directional((x['z20']< -2.0)&quiet,
                                      (x['z20']>2.0)&quiet)
    c['London_Impulse']=directional((hour>=7)&(hour<11)&(x['ret_10']>2.2)&(x['ema9_30']>.45),
                                     (hour>=7)&(hour<11)&(x['ret_10']< -2.2)&(x['ema9_30']<-.45))
    c['RSI_Continuation']=directional((x['rsi14']>54)&(x['rsi14']<74)&(x['ret_5']>1.1)&(x['ema9_30']>.4),
                                        (x['rsi14']<46)&(x['rsi14']>26)&(x['ret_5']< -1.1)&(x['ema9_30']<-.4))
    c['Channel_Extreme_Fade']=directional((x['channel20_pct']<.05)&(x['z20']< -1.6)&quiet,
                                          (x['channel20_pct']>.95)&(x['z20']>1.6)&quiet)
    c['EMA_60m_Trend']=directional(trend_pos&(x['ret_60']>3)&(x['ret_15']>1),
                                  trend_neg&(x['ret_60']< -3)&(x['ret_15']< -1))
    c['Streak_Exhaustion']=directional((x['up10']<.25)&(x['ret_5']< -2)&quiet,
                                      (x['up10']>.75)&(x['ret_5']>2)&quiet)
    c['Compression_Break']=directional((x['channel20_width']<8)&(x['vol_ratio']>1.3)&(x['ret_5']>1.25),
                                       (x['channel20_width']<8)&(x['vol_ratio']>1.3)&(x['ret_5']< -1.25))
    c['Volatility_Expansion']=directional((x['vol_ratio']>1.35)&(x['ret_15']>2.4)&(x['ema9_30']>.4),
                                          (x['vol_ratio']>1.35)&(x['ret_15']< -2.4)&(x['ema9_30']<-.4))
    c['Session_Range_Fade']=directional((hour>=12)&(hour<16)&(x['z20']< -1.6)&quiet,
                                       (hour>=12)&(hour<16)&(x['z20']>1.6)&quiet)
    c['Momentum_30_60']=directional((x['ret_30']>3)&(x['ret_60']>4)&(x['ret_5']>1),
                                     (x['ret_30']< -3)&(x['ret_60']< -4)&(x['ret_5']< -1))
    c['Micro_Momentum']=directional((x['ret_1']>.75)&(x['ret_3']>1.5)&(x['vol_ratio']>1.2),
                                    (x['ret_1']<-.75)&(x['ret_3']< -1.5)&(x['vol_ratio']>1.2))
    c['Price_Mean_Fade']=directional((x['px_ema30']< -2.2)&(x['rsi14']<35)&quiet,
                                     (x['px_ema30']>2.2)&(x['rsi14']>65)&quiet)
    return c
def days_between(start,end):
    return list(pd.bdate_range(start,end).strftime('%Y-%m-%d'))
def get_report(raw,name,signals,days,phase):
    prev=engine.DAYS
    try:
        engine.DAYS=days
        splitraw={**raw,'splits':{**raw['splits'],'test':raw['splits'][phase]}}
        # Voting matrix is provided for per-trade trace. P&L independent of this matrix.
        zeros=np.zeros((len(signals),10),dtype=np.int8)
        return engine.simulate(zeros,signals,splitraw)
    finally:
        engine.DAYS=prev
def dedup_select(candidates_,raw,stats,valid):
    ranked=sorted(candidates_,key=lambda k:(
        stats[k]['net_usd'],stats[k]['profit_factor'] or 0,stats[k]['trades']),reverse=True)
    chosen=[]
    for k in ranked:
        if stats[k]['trades']<QUALITY_MIN_TRADES: continue
        vec=candidates_[k][valid]
        similar=False
        for selected in chosen:
            b=candidates_[selected][valid]
            both=(vec!=0)&(b!=0)
            if both.sum()>=20 and np.mean(vec[both]==b[both])>.90:
                similar=True;break
        if not similar: chosen.append(k)
        if len(chosen)==6:break
    # Some sparse rules can make <10 trades in validation. Fill in predetermined rank
    # but do NOT treat these as validation-profitable.
    if len(chosen)<6:
        chosen.extend(k for k in ranked if k not in chosen and len(chosen)<6)
    assert len(chosen)==6
    return chosen
def sim_votes(raw,choices,daily,gate,phase='test'):
    fold_days=days_between(engine.TEST_BEGIN,engine.DAYS[-1])
    if not gate:
        return {'net_usd':0.0,'end_balance_usd':150.0,
                'trades':0,'win_rate_pct':0.,'profitable_days':0,
                'closed_trade_max_drawdown_usd':0.,'daily':{d:{'net_usd':0.,'trades':0} for d in fold_days},
                'quality_gate_skipped':True,'transactions':[]}
    return engine.simulate(choices,daily,raw)
def main():
    engine.DATA=Path('forex-gpt/.tmp/ensemble_walkforward_m1.json')
    b,a=engine.load_market()
    details=[]
    summaries={str(n):{'net_usd':0.,'trades':0,'wins':0,'losses':0,
                       'test_days':0,'profitable_days':0,'weeks_profitable':0,
                       'quality_gated_net_usd':0.,'quality_gated_trades':0} for n in THRESHOLDS}
    for f,params in enumerate(FOLDS,1):
        train_end,val_start,val_end,test_start,test_end=params
        engine.TRAIN_END=train_end
        engine.VALID_BEGIN=val_start
        engine.VALID_END=val_end
        engine.TEST_BEGIN=test_start
        engine.DAYS=days_between(test_start,test_end)
        raw=engine.build_features(b,a)
        X=raw['features'];y=raw['labels'];train=raw['splits']['train'];valid=raw['splits']['validation']
        model=engine.make_models()['RBF_SVM']
        model.fit(X[train],y[train])
        pred=model.predict(X).astype(int)
        rbf=np.where(pred==2,1,np.where(pred==0,-1,0)).astype(np.int8)
        retained={
          'RBF_SVM':rbf,
          'Donchian_Breakout':raw['rules'][:,1].astype(np.int8),
          'Bollinger_Reversion':raw['rules'][:,2].astype(np.int8),
          'Momentum_Regime':raw['rules'][:,3].astype(np.int8)}
        new=candidates(raw)
        validation_days=days_between(val_start,val_end)
        validation={}
        for name,signal in new.items():
            result=get_report(raw,name,signal,validation_days,'validation')
            validation[name]={k:result[k] for k in ['net_usd','trades','win_rate_pct','profit_factor']}
        chosen=dedup_select(new,raw,validation,valid)
        selected_stats={k:validation[k] for k in chosen}
        positive=sum(validation[k]['net_usd']>0 and validation[k]['trades']>=QUALITY_MIN_TRADES for k in chosen)
        quality_ok=positive>=QUALITY_MIN_WINNERS
        names=INCUMBENTS+chosen
        matrix=np.column_stack([retained[k] if k in retained else new[k] for k in names])
        buys=(matrix==1).sum(axis=1)
        sells=(matrix==-1).sum(axis=1)
        fold_results={}
        fold_results_gated={}
        for threshold in THRESHOLDS:
            side=np.where((buys>=threshold)&(buys>sells),1,
                          np.where((sells>=threshold)&(sells>buys),-1,0)).astype(np.int8)
            r=engine.simulate(matrix,side,raw)
            net=r['net_usd']
            s=summaries[str(threshold)]
            s['net_usd']+=net;s['trades']+=r['trades'];s['wins']+=r['wins']
            s['losses']+=r['losses'];s['test_days']+=5;s['profitable_days']+=r['profitable_days']
            s['weeks_profitable']+=int(net>0)
            if quality_ok:
                s['quality_gated_net_usd']+=net;s['quality_gated_trades']+=r['trades']
            fold_results[str(threshold)]=r
            print('ROTATION_FOLD_'+str(f)+'_THRESHOLD_'+str(threshold),
                  json.dumps({k:r[k] for k in r if k!='transactions'},sort_keys=True),flush=True)
        details.append({
          'fold':f,'train_ends':train_end,'validation':val_start+'..'+val_end,
          'test':test_start+'..'+test_end,'sample_sizes':{
              k:int(v.sum()) for k,v in raw['splits'].items()},
          'retained_models':INCUMBENTS,
          'selected_replacements':chosen,
          'prior_validation_selected':selected_stats,
          'prior_validation_all':validation,
          'positive_replacements_on_validation':positive,
          'quality_gate_min_profitable_replacements':QUALITY_MIN_WINNERS,
          'quality_gate_passed':quality_ok,
          'test_results':fold_results})
        print('ROTATION_SELECTION_'+str(f),json.dumps({
          'test_week':test_start,'selected':chosen,
          'quality_gate':quality_ok,'positive_validated':positive,
          'prior_validation':selected_stats},sort_keys=True),flush=True)
    for n,s in summaries.items():
        s['net_usd']=round(s['net_usd'],5)
        s['quality_gated_net_usd']=round(s['quality_gated_net_usd'],5)
        s['wins_rate_pct']=round(100*s['wins']/s['trades'],2) if s['trades'] else 0.
        # The paper account is independently RESET to $150 at start of each week.
        s['aggregate_4x150_initial_usd']=600
        s['aggregate_final_usd']=round(600+s['net_usd'],5)
        print('ROTATION_AGGREGATE_'+str(n),json.dumps(s,sort_keys=True),flush=True)
    report={'kind':'read-only chronological iterative candidate screening research',
            'data_source':'Dukascopy GBPUSD M1 historical bid/ask',
            'candles':len(b),'date_start_utc':'2026-06-01','final_date_utc':'2026-11-20',
            'method':'4 incumbents from earlier exploratory test; screen 16 replacements on prior two weeks of validation each fold; retain six distinct enough candidates; evaluate on following five days',
            'scope':'research comparison, selection uses only prior historical outcomes',
            'important':'The November 16-20 week was seen in previous study, so not a truly untouched research sample',
            'no_live_trades':True,'not_tick_level':True,
            'transaction_assumptions':{'start_usd_per_week':150,'units_gbp':1000,
                 'slippage_round_trip_pips':.2,'commission_usd_round_trip':.06,
                 'spread':'historical bid/ask at entry/exit','stop_pips':8,'target_pips':12,
                 'daily_pause_loss_usd':-3},
            'selection_predeclared':{'minimum_validation_trades':QUALITY_MIN_TRADES,
                   'quality_gate_min_profitable_candidates':QUALITY_MIN_WINNERS,
                   'similar_vote_screen':'exclude candidates agreeing >90% on >=20 joint active votes',
                   'force_fill_to_10':'if too few qualify by trade count, rank remaining candidates; does not imply validation-profitability'},
            'folds':details,'aggregates':summaries,
            'limitations':['Do not choose threshold based on evaluated week; 6,7,8 compared for research',
             'Aggregate results treat each fold as independent initial $150 account',
             'One minute candle stops are approximate; stops may slip and broker can reject orders',
             'Repeated backtesting and candidate screening raise data-snooping risk',
             'A live forward demo on previously unavailable prices is necessary before live risk']}
    DST.parent.mkdir(parents=True,exist_ok=True)
    DST.write_text(json.dumps(report,default=lambda o:o.item() if isinstance(o,np.generic) else str(o),indent=2)+'\n')
    print('ROTATION_RESULT_FILE',DST,flush=True)
if __name__=='__main__':main()
