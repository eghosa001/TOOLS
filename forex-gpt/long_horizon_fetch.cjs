#!/usr/bin/env node
/** Fixed-before-results random 10 two-week GBPUSD/EURUSD tick windows.
 * From a Python random.Random(260707) uniform 2 weeks/year, 5..43 ISO weeks,
 * excluding years' previously inspected study weeks within three weeks,
 * requiring >=8 weeks separation. 2022-23 train, 2024 validate,
 * 2025-26 untouched holdout. Never connect to a broker.
 */
'use strict';
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const W=[
 ['2022-03-14','2022-03-25',11],['2022-05-16','2022-05-27',20],
 ['2023-06-05','2023-06-16',23],['2023-10-09','2023-10-20',41],
 ['2024-08-12','2024-08-23',33],['2024-10-14','2024-10-25',42],
 ['2025-06-09','2025-06-20',24],['2025-09-01','2025-09-12',36],
 ['2026-02-16','2026-02-27',8], ['2026-05-04','2026-05-15',19]
];
const DIR=path.join(__dirname,'.tmp','long_horizon');
fs.mkdirSync(DIR,{recursive:true});
const PAIRS=['gbpusd','eurusd','eurgbp'];
function days(a,b){
 const list=[];
 for(let t=Date.parse(a+'T00:00:00Z'),end=Date.parse(b+'T00:00:00Z');t<=end;t+=86400000){
  const day=new Date(t);
  if(day.getUTCDay()>=1&&day.getUTCDay()<=5)list.push(day.toISOString().slice(0,10));
 }
 return list;
}
const manifest={source:'dukascopy-node@1.51.1',random_seed:260707,
 selection:'Two disjoint ISO weeks per year selected with Python random.Random(260707) from weeks 5..43, excluding earlier research windows by at least 3 weeks; retain pair >=8 weeks apart. Precommitted before quote download.',
 pairs:PAIRS,from_hour_utc:7,to_hour_utc:12,
 windows:W.map(([start,end,week])=>({start,end,week,days:days(start,end)})),
 days:[],missing:[],real_broker_orders:0};
(async()=>{
 for(const w of manifest.windows)for(const day of w.days){
  const q={date:day,provider:'dukascopy-node@1.51.1',symbols:PAIRS,
   start_utc:day+'T07:00:00Z',end_utc:day+'T12:00:00Z',instruments:{}};
  const begin=Date.parse(q.start_utc),end=Date.parse(q.end_utc);
  let err=null;
  for(const pair of PAIRS){
   try{
    const ticks=await getHistoricalRates({
     instrument:pair,dates:{from:new Date(begin),to:new Date(end)},
     timeframe:'tick',format:'array',volumes:true,volumeUnits:'millions',
     ignoreFlats:false,batchSize:5,pauseBetweenBatchesMs:100,
     retryCount:3,pauseBetweenRetriesMs:450,failAfterRetryCount:true
    });
    if(!Array.isArray(ticks))throw Error('Not a historical tick array');
    const clean=ticks.filter(r=>Array.isArray(r)&&r.length>=5&&
        Number.isSafeInteger(r[0])&&r[0]>=begin&&r[0]<end&&
        r.slice(1,5).every(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0)&&
        r[1]>=r[2]&&r[2]>0).map(r=>r.slice(0,5));
    clean.sort((a,b)=>a[0]-b[0]);
    if(clean.length<1000)throw Error('Too few valid ticks '+clean.length);
    q.instruments[pair]=clean;
   }catch(e){err=String(e.message||e).slice(0,250);break}
  }
  if(err){
   manifest.missing.push({day,error:err});
   console.error('LONG_HISTORICAL_MISSING',day,err);
  }else{
   const data=JSON.stringify(q),name=day+'.json';
   fs.writeFileSync(path.join(DIR,name),data);
   const record={day,checksum_sha256:crypto.createHash('sha256').update(data).digest('hex'),
      quotes:Object.fromEntries(PAIRS.map(p=>[p,q.instruments[p].length]))};
   manifest.days.push(record);
   console.log('LONG_HISTORICAL_DATE',day,'count',manifest.days.length,'quotes',JSON.stringify(record.quotes));
  }
 }
 manifest.complete=manifest.days.length===100&&manifest.missing.length===0;
 fs.writeFileSync(path.join(DIR,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log('LONG_HISTORICAL_DOWNLOAD',JSON.stringify({
  windows:manifest.windows.map(w=>[w.start,w.end]),downloaded:manifest.days.length,
  missing:manifest.missing.length,complete:manifest.complete
 }));
 if(!manifest.complete)process.exitCode=2;
})().catch(e=>{console.error('LONG_HISTORICAL_FATAL',e.stack||String(e));process.exitCode=2;});
