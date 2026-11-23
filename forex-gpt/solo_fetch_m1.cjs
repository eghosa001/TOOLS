#!/usr/bin/env node
/**
 * Read bid/ask minute bars for the historical standalone-GPT control.
 * This is a one-off research data download, not a live broker connection.
 */
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs');
const path=require('node:path');
const from=new Date('2026-11-16T00:00:00Z');
const to=new Date('2026-11-21T00:00:00Z');
const data={
    provider:'dukascopy-node@1.51.1',
    symbol:'gbpusd',
    timeframe:'m1',
    from_utc:from.toISOString(),
    to_utc:to.toISOString(),
    sides:{}
};
(async()=>{
  for (const priceType of ['bid','ask']){
    const rs=await getHistoricalRates({
      instrument:'gbpusd',
      dates:{from,to},
      timeframe:'m1',
      priceType,
      format:'array',
      volumes:false,
      ignoreFlats:false,
      batchSize:6,
      pauseBetweenBatchesMs:150,
      retryCount:2,
      pauseBetweenRetriesMs:350,
      failAfterRetryCount:true
    });
    if (!Array.isArray(rs)||rs.length<5000) {
      throw new Error('Too few M1 price records for '+priceType);
    }
    const filtered=rs.filter(x=>Array.isArray(x)&&x.length>=5&&
      Number.isSafeInteger(x[0])&&x.slice(1,5).every(v=>Number.isFinite(v)&&v>0));
    if (filtered.length<5000) {
      throw new Error('Too few validated M1 prices for '+priceType);
    }
    data.sides[priceType]=filtered.map(x=>x.slice(0,5));
    console.log('M1_'+priceType.toUpperCase()+'_CANDLES',filtered.length);
  }
  const file=path.join(__dirname,'.tmp','gpt_solo_m1.json');
  fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify(data));
  console.log('SAVED_SOLO_GPT_HISTORICAL_QUOTES',file);
})().catch(e=>{console.error('SOLO_GPT_MARKET_DATA_FAILED',String(e));process.exitCode=2});
