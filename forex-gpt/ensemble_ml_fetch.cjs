#!/usr/bin/env node
/** Read-only historical GBP/USD M1 bid/ask, Sep 7 through Nov 20 2026. */
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path');
const ranges=[['2026-09-07','2026-10-01'],['2026-10-01','2026-11-01'],['2026-11-01','2026-11-21']];
const sides={bid:[],ask:[]};
(async()=>{
for(const [s,e] of ranges)for(const side of ['bid','ask']){
 const rows=await getHistoricalRates({
   instrument:'gbpusd',dates:{from:new Date(s+'T00:00:00Z'),to:new Date(e+'T00:00:00Z')},
   timeframe:'m1',priceType:side,format:'array',volumes:false,ignoreFlats:false,
   batchSize:6,pauseBetweenBatchesMs:150,retryCount:3,
   pauseBetweenRetriesMs:600,failAfterRetryCount:true
 });
 if(!Array.isArray(rows)||rows.length<10000)throw Error('Incomplete history '+s+' '+e+' '+side+' '+rows?.length);
 sides[side].push(...rows.filter(r=>Array.isArray(r)&&Number.isSafeInteger(r[0])&&r.length>=5&&r.slice(1,5).every(v=>Number.isFinite(v)&&v>0)).map(r=>r.slice(0,5)));
 console.log('MONTH',s,e,side,rows.length);
}
for(const side of ['bid','ask']){
 const bytime=new Map(sides[side].map(x=>[x[0],x]));
 sides[side]=[...bytime.values()].sort((a,b)=>a[0]-b[0]);
}
// Intersection efficiently: never synthesize or forward-fill a quote.
const aTimes=new Set(sides.ask.map(x=>x[0]));
const shared=new Set(sides.bid.filter(x=>aTimes.has(x[0])).map(x=>x[0]));
for(const s of ['bid','ask'])sides[s]=sides[s].filter(x=>shared.has(x[0]));
if(shared.size<65000)throw Error('Not enough aligned M1 candles: '+shared.size);
const file=path.join(__dirname,'.tmp','consensus_ml_m1.json');
fs.mkdirSync(path.dirname(file),{recursive:true});
fs.writeFileSync(file,JSON.stringify({provider:'dukascopy-node@1.51.1',symbol:'gbpusd',timeframe:'m1',from_utc:ranges[0][0],to_utc:ranges.at(-1)[1],sides}));
console.log('ENSEMBLE_ALIGNED_CANDLES',shared.size,'OUTPUT',file);
})().catch(e=>{console.error('ENSEMBLE_HISTORY_ERROR',e.stack||String(e));process.exitCode=2});
