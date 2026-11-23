#!/usr/bin/env node
/** Precommitted multi-year quote-dislocation FX experiment; paper only. */
'use strict';
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'), path=require('node:path'),crypto=require('node:crypto');
const W=[
[2021,12,'2021-03-22','2021-04-02'],[2021,21,'2021-05-24','2021-06-04'],
[2022,25,'2022-06-20','2022-07-01'],[2022,36,'2022-09-05','2022-09-16'],
[2023,11,'2023-03-13','2023-03-24'],[2023,20,'2023-05-15','2023-05-26'],
[2024,8,'2024-02-19','2024-03-01'],[2024,22,'2024-05-27','2024-06-07'],
[2025,28,'2025-07-07','2025-07-18'],[2025,41,'2025-10-06','2025-10-17'],
[2026,11,'2026-03-09','2026-03-20'],[2026,23,'2026-06-01','2026-06-12']
];
const PAIRS=['gbpusd','eurusd','eurgbp'];
const DIR=path.join(__dirname,'.tmp','parity_microstructure');
fs.mkdirSync(DIR,{recursive:true});
function weekdays(a,b) {
 const arr=[];
 for(let t=Date.parse(a+'T00:00:00Z');t<=Date.parse(b+'T00:00:00Z');t+=86400000){
  let d=new Date(t);if(d.getUTCDay()>0&&d.getUTCDay()<6)arr.push(d.toISOString().slice(0,10));
 }
 return arr;
}
const windows=W.map(([year,week,start,end])=>({year,week,start,end,dates:weekdays(start,end)}));
if(windows.some(w=>w.dates.length!==10))throw Error('Broken deterministic sample');
const output={source:'dukascopy-node@1.51.1',
  draw_seed:260923,method:'random.Random(260923) two separated ISO weeks per year, excluding previously inspected windows',
  years:{train:[2021,2022,2023],selection:[2024],heldout:[2025,2026]},
  session_utc:'07:00-09:00',windows,days:[],missing:[],
  volume_type:'Dukascopy quote-side volume, NOT trade flow',no_broker_orders:true};
(async()=>{
 for(const w of windows)for(const day of w.dates){
  const a=Date.parse(day+'T07:00:00Z'),b=a+7200000;
  const doc={date:day,provider:'dukascopy-node@1.51.1',instruments:{}};
  let error=null;
  for(const pair of PAIRS)try{
    const raw=await getHistoricalRates({instrument:pair,dates:{from:new Date(a),to:new Date(b)},
      timeframe:'tick',format:'array',volumes:true,volumeUnits:'millions',ignoreFlats:false,
      batchSize:2,pauseBetweenBatchesMs:125,retryCount:3,pauseBetweenRetriesMs:450,
      failAfterRetryCount:true});
    if(!Array.isArray(raw))throw Error('Not tick array');
    const q=raw.filter(r=>Array.isArray(r)&&r.length>=5&&Number.isSafeInteger(r[0])&&
       r[0]>=a&&r[0]<b&&r.slice(1,5).every(x=>Number.isFinite(x)&&x>=0)&&
       r[1]>=r[2]&&r[2]>0).map(r=>r.slice(0,5));
    q.sort((x,y)=>x[0]-y[0]);
    if(q.length<200)throw Error('Too few quotes: '+q.length);
    doc.instruments[pair]=q;
  }catch(e){error=pair+': '+String(e.message||e).slice(0,150);break}
  if(error){output.missing.push({day,error});console.error('PARITY_MISSING',day,error);continue}
  const raw=JSON.stringify(doc);
  fs.writeFileSync(path.join(DIR,day+'.json'),raw);
  const counts=Object.fromEntries(PAIRS.map(p=>[p,doc.instruments[p].length]));
  output.days.push({day,year:w.year,week:w.week,counts,sha256:crypto.createHash('sha256').update(raw).digest('hex')});
  console.log('PARITY_TICK_DAY',output.days.length,'/120',day,JSON.stringify(counts));
 }
 output.complete=output.days.length===120&&output.missing.length===0;
 fs.writeFileSync(path.join(DIR,'manifest.json'),JSON.stringify(output,null,2)+'\n');
 console.log('PARITY_TICK_FINAL',JSON.stringify({days:output.days.length,missing:output.missing.length,complete:output.complete}));
 if(!output.complete)process.exitCode=2;
})().catch(e=>{console.error('PARITY_FATAL',e.stack||String(e));process.exitCode=2});
