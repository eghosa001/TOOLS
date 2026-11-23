#!/usr/bin/env node
/** Read-only GBP/USD H1 bid/ask history for pre-registered CFTC regime comparison.
 * Never uses broker keys, OpenAI keys, or places orders. */
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs');
const path=require('node:path');
const boundaries=['2019-09-01','2020-01-01','2021-01-01','2022-01-01','2023-01-01','2024-01-01','2025-01-01','2026-01-01','2026-11-23'];
const bySide={bid:[],ask:[]};
(async()=>{
  for(let i=0;i<boundaries.length-1;i++){
    const from=new Date(boundaries[i]+'T00:00:00Z');
    const to=new Date(boundaries[i+1]+'T00:00:00Z');
    for(const side of ['bid','ask']){
      const rows=await getHistoricalRates({
        instrument:'gbpusd',dates:{from,to},timeframe:'h1',
        priceType:side,format:'array',volumes:false,ignoreFlats:false,
        batchSize:8,pauseBetweenBatchesMs:100,
        retryCount:3,pauseBetweenRetriesMs:500,failAfterRetryCount:true
      });
      if(!Array.isArray(rows)||rows.length<200){
        throw new Error('Missing quote history '+boundaries[i]+' '+side+' '+(rows?.length||0));
      }
      bySide[side].push(...rows.filter(r=>Array.isArray(r)&&Number.isSafeInteger(r[0])&&
        r.length>=5&&r.slice(1,5).every(v=>Number.isFinite(v)&&v>0)).map(r=>r.slice(0,5)));
      console.log('REGIME_CHUNK',boundaries[i],side,rows.length);
    }
  }
  const sides={};
  for(const side of ['bid','ask']){
    const x=new Map(bySide[side].map(r=>[r[0],r]));
    sides[side]=[...x.values()].sort((a,b)=>a[0]-b[0]);
  }
  const b=new Set(sides.bid.map(x=>x[0])),a=new Set(sides.ask.map(x=>x[0]));
  const common=new Set([...b].filter(t=>a.has(t)));
  for(const side of ['bid','ask'])sides[side]=sides[side].filter(r=>common.has(r[0]));
  if(common.size<34000)throw new Error('Too few aligned historical hourly quotes: '+common.size);
  const file='forex-gpt/.tmp/regime_h1_quotes.json';
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify({provider:'dukascopy-node@1.51.1',symbol:'gbpusd',
    timeframe:'h1',cutoff_utc:'2026-11-23T00:00:00Z',sides}));
  console.log('REGIME_ALIGNED_H1',common.size,'FILE',file);
})().catch(e=>{console.error('REGIME_QUOTES_FAILED',String(e.message||e));process.exitCode=2;});
