#!/usr/bin/env node
/** Historical GBP/USD M1 bid and ask for four chronological walk-forward folds.
 * Uses only public Dukascopy data and never submits orders.
 */
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path');
const ranges=[
  ['2026-06-01','2026-07-01'],
  ['2026-07-01','2026-08-01'],
  ['2026-08-01','2026-09-01'],
  ['2026-09-01','2026-10-01'],
  ['2026-10-01','2026-11-01'],
  ['2026-11-01','2026-11-21']
];
const bySide={bid:[],ask:[]};
(async()=>{
 for(const [start,end] of ranges)for(const side of ['bid','ask']){
  const rows=await getHistoricalRates({
   instrument:'gbpusd',
   dates:{from:new Date(start+'T00:00:00Z'),to:new Date(end+'T00:00:00Z')},
   timeframe:'m1',priceType:side,format:'array',volumes:false,
   ignoreFlats:false,batchSize:6,pauseBetweenBatchesMs:150,
   retryCount:3,pauseBetweenRetriesMs:600,failAfterRetryCount:true
  });
  if(!Array.isArray(rows)||rows.length<15000)throw Error('Bad history '+start+' '+side+' '+(rows?.length||0));
  bySide[side].push(...rows.filter(q=>Array.isArray(q)&&q.length>=5&&Number.isSafeInteger(q[0])&&q.slice(1,5).every(v=>Number.isFinite(v)&&v>0)).map(q=>q.slice(0,5)));
  console.log('HISTORY_CHUNK',start,end,side,rows.length);
 }
 const maps={};
 for(const side of ['bid','ask'])maps[side]=new Map(bySide[side].map(q=>[q[0],q]));
 const ts=[...maps.bid.keys()].filter(t=>maps.ask.has(t)).sort((a,b)=>a-b);
 if(ts.length<155000)throw Error('Insufficient aligned historical candles: '+ts.length);
 const sides={};
 for(const side of ['bid','ask'])sides[side]=ts.map(t=>maps[side].get(t));
 const dst=path.join(__dirname,'.tmp','ensemble_walkforward_m1.json');
 fs.mkdirSync(path.dirname(dst),{recursive:true});
 fs.writeFileSync(dst,JSON.stringify({
  provider:'dukascopy-node@1.51.1',symbol:'gbpusd',timeframe:'m1',
  from_utc:ranges[0][0],to_utc:ranges.at(-1)[1],sides
 }));
 console.log('WALKFORWARD_CANDLES',ts.length,'FILE',dst);
})().catch(e=>{console.error('HISTORY_FAILED',e.stack||String(e));process.exitCode=2});
