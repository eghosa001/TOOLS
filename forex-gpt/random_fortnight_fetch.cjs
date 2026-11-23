#!/usr/bin/env node
/** A preregistered deterministic draw: five separate 2-week Forex windows.
 * Seed 20261123 via Python Random produces ISO weeks 42/2022, 37/2023,
 * 16/2024, 17/2025 and 41/2026; periods were chosen before observing
 * strategy returns. No credentials, broker APIs or live trades.
 */
'use strict';
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const windows=[
 {start:'2022-10-17',end:'2022-10-28',iso_week:42},
 {start:'2023-09-11',end:'2023-09-22',iso_week:37},
 {start:'2024-04-15',end:'2024-04-26',iso_week:16},
 {start:'2025-04-21',end:'2025-05-02',iso_week:17},
 {start:'2026-10-05',end:'2026-10-16',iso_week:41}
];
const outdir='forex-gpt/.tmp/random_fortnights';
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
const manifest={random_seed:20261123,random_method:'python random.Random(seed).randint(6,42) one ISO week per year 2022-2026',source:'dukascopy-node@1.51.1',windows:windows.map(w=>({...w,days:daysBetween(w.start,w.end)})),
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
    if(rows.length<500)throw Error('Insufficient raw bid/ask quotes: '+rows.length);
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
   console.log('HISTORICAL_TICK_DAY',count,'/',50,day,'tick_counts',manifest.days.at(-1).counts);
  }
 }
 manifest.complete=manifest.missing.length===0&&manifest.days.length===50;
 fs.writeFileSync(path.join(outdir,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('HISTORICAL_RANDOM_WINDOWS',JSON.stringify({windows:manifest.windows.map(w=>[w.start,w.end]),
   loaded_days:manifest.days.length,missing_days:manifest.missing.length,complete:manifest.complete}));
 if(!manifest.complete)process.exitCode=2;
})().catch(e=>{console.error('FETCH_FATAL',e.stack||String(e));process.exitCode=2;});
