#!/usr/bin/env node
/** Regime-switching Forex: preselected independent 2-week random windows.
 * Three disjoint windows per year (2022..2026), excluding five prior test windows.
 * The draw is committed BEFORE outcome inspection. Actual historical Dukascopy
 * tick bid/ask in 07:00–09:00 UTC, three currencies, never broker orders.
 */
'use strict';
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const windows=[
 {start:'2022-01-31',end:'2022-02-11',iso_week:5},
 {start:'2022-04-11',end:'2022-04-22',iso_week:15},
 {start:'2022-08-01',end:'2022-08-12',iso_week:31},
 {start:'2023-04-17',end:'2023-04-28',iso_week:16},
 {start:'2023-07-03',end:'2023-07-14',iso_week:27},
 {start:'2023-08-07',end:'2023-08-18',iso_week:32},
 {start:'2024-03-18',end:'2024-03-29',iso_week:12},
 {start:'2024-07-08',end:'2024-07-19',iso_week:28},
 {start:'2024-09-16',end:'2024-09-27',iso_week:38},
 {start:'2025-02-03',end:'2025-02-14',iso_week:6},
 {start:'2025-03-17',end:'2025-03-28',iso_week:12},
 {start:'2025-05-12',end:'2025-05-23',iso_week:20},
 {start:'2026-04-06',end:'2026-04-17',iso_week:15},
 {start:'2026-07-06',end:'2026-07-17',iso_week:28},
 {start:'2026-09-14',end:'2026-09-25',iso_week:38}
];
const outdir='forex-gpt/.tmp/regime_switch';
const instruments=['gbpusd','eurusd','eurgbp'];
fs.mkdirSync(outdir,{recursive:true});
function daysBetween(start,end) {
 const dates=[];
 for(let t=Date.parse(start+'T00:00:00Z');t<=Date.parse(end+'T00:00:00Z');t+=86400000){
  const d=new Date(t);
  if(d.getUTCDay()>=1&&d.getUTCDay()<=5)dates.push(d.toISOString().slice(0,10));
 }
 return dates;
}
const manifest={random_seed:260501,random_method:'python random.Random(seed) uniform 3 separated ISO weeks 5-44 per year 2022-2026; exclude prior test windows by >=3 weeks',source:'dukascopy-node@1.51.1',windows:windows.map(w=>({...w,days:daysBetween(w.start,w.end)})),
 historical_news_calendar_available:false,news_blackout_applied:false,
 no_market_orders:true,days:[],missing:[]};
(async()=>{
 let count=0;
 for(const w of manifest.windows)for(const day of w.days){
  const start=Date.parse(day+'T07:00:00Z'),stop=start+7200000;
  const document={date:day,provider:'dukascopy-node@1.51.1',
    kind:'historical tick bid ask only',instruments:{}};
  let missing=null;
  for(const instrument of instruments){
   try{
    const rs=await getHistoricalRates({instrument,
     dates:{from:new Date(start),to:new Date(stop)},
     timeframe:'tick',format:'array',volumes:true,volumeUnits:'millions',
     ignoreFlats:false,batchSize:3,pauseBetweenBatchesMs:125,
     retryCount:3,pauseBetweenRetriesMs:400,failAfterRetryCount:true});
    if(!Array.isArray(rs))throw Error('No array returned');
    const rows=rs.filter(q=>Array.isArray(q)&&q.length>=5&&Number.isSafeInteger(q[0])&&
      q[0]>=start&&q[0]<stop&&q.slice(1,5).every(v=>Number.isFinite(v)&&v>=0)&&
      q[1]>0&&q[2]>0&&q[1]>=q[2]).map(q=>q.slice(0,5));
    rows.sort((a,b)=>a[0]-b[0]);
    if(rows.length<200)throw Error('Insufficient raw bid/ask quotes: '+rows.length);
    document.instruments[instrument]=rows;
   }catch(e){missing=instrument+': '+String(e.message||e).slice(0,250);break}
  }
  if(missing){
   manifest.missing.push({day,error:missing});
   console.error('DAY_MISSING',day,missing);
  }else{
   const bytes=JSON.stringify(document);
   fs.writeFileSync(path.join(outdir,day+'.json'),bytes);
   manifest.days.push({day,counts:Object.fromEntries(instruments.map(k=>[k,document.instruments[k].length])),
     sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
   count++;
   console.log('HISTORICAL_TICK_DAY',count,'/',150,day,'tick_counts',manifest.days.at(-1).counts);
  }
 }
 manifest.complete=manifest.missing.length===0&&manifest.days.length===150;
 fs.writeFileSync(path.join(outdir,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('HISTORICAL_RANDOM_WINDOWS',JSON.stringify({windows:manifest.windows.map(w=>[w.start,w.end]),
   loaded_days:manifest.days.length,missing_days:manifest.missing.length,complete:manifest.complete}));
 if(!manifest.complete)console.error('PARTIAL_DATA_EXPLICIT: Missing days are tracked, never fabricated; do not treat missing periods as complete');
})().catch(e=>{console.error('FETCH_FATAL',e.stack||String(e));process.exitCode=2;});
