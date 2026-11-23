#!/usr/bin/env node
/**
 * Fetches up-to-date H1 Dukascopy bid/ask candles for the SAME markets and
 * data vendor as the existing Higgsfield historical experiment.
 *
 * Does not use credentials or submit trades. Never treats unfinished H1 as
 * a finished bar. Values are informational and NOT broker fills.
 */
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs');
const path=require('node:path');
const markets=['gbpusd','eurusd','usdjpy'];
const now=new Date();
const from=new Date(now.getTime()-18*86400000);
const asof=now.toISOString();
const prices={schema:1,provider:'dukascopy-node@1.51.1',fetched_utc:asof,
   from_utc:from.toISOString(),prices:{}};
async function go(){
 for(const pair of markets){
   const out={};
   for(const side of ['bid','ask']){
     const rows=await getHistoricalRates({
       instrument:pair,dates:{from,to:now},timeframe:'h1',
       priceType:side,format:'array',volumes:false,ignoreFlats:false,
       batchSize:4,pauseBetweenBatchesMs:250,
       retryCount:2,pauseBetweenRetriesMs:400,failAfterRetryCount:true
     });
     if(!Array.isArray(rows)||rows.length<200) throw new Error(pair+' '+side+' has insufficient H1 history');
     const filtered=rows.filter(z=>
       Array.isArray(z)&&z.length>=5&&Number.isSafeInteger(z[0])&&
       z[0]+3600000<=now.getTime() &&
       z.slice(1,5).every(x=>Number.isFinite(x)&&x>0));
     if(filtered.length<200)throw new Error(pair+' '+side+' insufficient complete H1 bars');
     out[side]=filtered.map(z=>z.slice(0,5));
   }
   const b=new Set(out.bid.map(z=>z[0])),a=new Set(out.ask.map(z=>z[0]));
   const intersection=new Set([...a].filter(z=>b.has(z)));
   if(intersection.size<200)throw new Error('Too few simultaneous bid/ask bars '+pair);
   out.bid=out.bid.filter(x=>intersection.has(x[0])).sort((x,y)=>x[0]-y[0]);
   out.ask=out.ask.filter(x=>intersection.has(x[0])).sort((x,y)=>x[0]-y[0]);
   const last=out.bid[out.bid.length-1][0];
   if(now.getTime()-last>72*3600000)throw new Error('Stale last H1 quote '+pair);
   prices.prices[pair]=out;
   console.log(pair,'closed_H1_bars',out.bid.length,'last_close_utc',
       new Date(last+3600000).toISOString());
 }
 const filename=process.argv[2]||'forex-gpt/.tmp/market_data.json';
 fs.mkdirSync(path.dirname(filename),{recursive:true});
 fs.writeFileSync(filename,JSON.stringify(prices));
 console.log('SAVED_COMPLETE_MARKET_DATA',filename);
}
go().catch(err=>{console.error('FAILED_MARKET_INGESTION',String(err.message||err).slice(0,220));process.exitCode=2;});
