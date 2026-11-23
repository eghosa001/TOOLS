#!/usr/bin/env node
/**
 * Read-only full tick bid/ask/quoted-volume research:
 * GBPUSD + EURUSD + EURGBP (multi-pair context)
 * Download exactly the day's UTC 07:00-09:00 interval, in two hourly slices.
 * Also snapshot the CURRENT WEEK public macro calendar; missing = fail closed.
 * No broker access, orders, keys, or account interactions.
 */
'use strict';
const {getHistoricalRates}=require('dukascopy-node');
const fs=require('node:fs'),path=require('node:path'),https=require('node:https');
const target=process.env.TARGET_DAY||'2026-11-23';
if(!/^2026-11-(2[3-9]|30)$/.test(target))throw Error('TARGET_DAY must be Nov 23-30, 2026');
const outdir=path.join(__dirname,'.tmp');
fs.mkdirSync(outdir,{recursive:true});
const instruments=['gbpusd','eurusd','eurgbp'];
const output={provider:'dukascopy-node@1.51.1', kind:'actual raw historical ticks',
 date:target, start_utc:target+'T07:00:00.000Z',end_utc:target+'T09:00:00.000Z',
 instruments:{},no_live_orders:true};
function getJSON(url){
 return new Promise((resolve,reject)=>{
  const req=https.get(url,{headers:{'User-Agent':'ForexPaperResearch/1.0','Accept':'application/json'},timeout:16000},res=>{
   if(res.statusCode!==200){res.resume();return reject(Error('calendar HTTP '+res.statusCode))}
   let s='';
   res.setEncoding('utf8');
   res.on('data',chunk=>{s+=chunk;if(s.length>2000000)req.destroy(Error('calendar too large'));});
   res.on('end',()=>{try{resolve(JSON.parse(s))}catch(e){reject(e)}});
  });
  req.on('timeout',()=>req.destroy(Error('calendar timeout')));
  req.on('error',reject);
 });
}
(async()=>{
  const day=Date.parse(target+'T07:00:00Z');
  for(const instrument of instruments){
   const combined=[];
   for(const hour of [7,8]){
    const from=new Date(Date.parse(target+'T'+String(hour).padStart(2,'0')+':00:00Z'));
    const to=new Date(from.getTime()+60*60*1000);
    const rows=await getHistoricalRates({
     instrument,dates:{from,to},timeframe:'tick',format:'array',
     volumes:true,volumeUnits:'millions',ignoreFlats:false,
     batchSize:2,pauseBetweenBatchesMs:250,retryCount:3,
     pauseBetweenRetriesMs:600,failAfterRetryCount:true
    });
    if(!Array.isArray(rows)||rows.length<150)throw Error('Insufficient tick quotes '+instrument+' '+hour+': '+(rows?.length||0));
    for(const t of rows){
     if(!Array.isArray(t)||t.length<5||!Number.isSafeInteger(t[0])||
       !t.slice(1,5).every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=0)||
       t[1]<=0||t[2]<=0||t[1]<t[2])throw Error('Malformed tick '+instrument);
     if(t[0]>=day&&t[0]<day+7200000)combined.push(t.slice(0,5));
    }
    console.log('RAW_TICK_HOUR',target,instrument,hour,rows.length);
   }
   combined.sort((a,b)=>a[0]-b[0]);
   if(combined.length<500||combined[0][0]<day||combined.at(-1)[0]>=day+7200000)throw Error('Bad tick range '+instrument);
   output.instruments[instrument]=combined;
   console.log('VALID_TICKS',instrument,combined.length,'first',combined[0][0],'last',combined.at(-1)[0]);
  }
  const file=path.join(outdir,'tick_context_'+target+'.json');
  fs.writeFileSync(file,JSON.stringify(output));
  console.log('TICK_HISTORY_SAVED',file);
  const cal={source:'https://nfs.faireconomy.media/ff_calendar_thisweek.json',
      fetched_utc:new Date().toISOString(),status:'unavailable',
      target_day_utc:target,events:[]};
  try{
   const raw=await getJSON(cal.source);
   if(!Array.isArray(raw)||raw.length<20)throw Error('Empty or insufficient calendar');
   for(const ev of raw){
    if(!ev||!['USD','GBP'].includes(ev.country))continue;
    if(!['High','Medium','Holiday'].includes(ev.impact))continue;
    if(typeof ev.date!=='string'||!/[+-]\d\d:\d\d$/.test(ev.date))throw Error('Missing event timezone');
    const time=Date.parse(ev.date);
    if(!Number.isFinite(time))throw Error('Invalid event timestamp');
    cal.events.push({utc:new Date(time).toISOString(),country:ev.country,impact:ev.impact,title:String(ev.title||'').slice(0,180)});
   }
   if(!cal.events.length)throw Error('No USD/GBP high/medium/holiday events returned');
   // Live calendar is one-week only. Do not substitute it as if historical.
   if(!cal.events.some(e=>Math.abs(Date.parse(e.utc)-Date.parse(target+'T12:00:00Z'))<7*86400000))
      throw Error('Feed appears stale, different week');
   cal.status='verified';
  }catch(e){
   cal.error=String(e.message||e).slice(0,250);
   console.error('ECONOMIC_CALENDAR_UNVERIFIED_FAIL_CLOSED',cal.error);
  }
  const calFile=path.join(outdir,'macro_calendar_'+target+'.json');
  fs.writeFileSync(calFile,JSON.stringify(cal,null,2)+'\n');
  console.log('CALENDAR_STATUS',cal.status,'events',cal.events.length,calFile);
})().catch(e=>{console.error('TICK_RESEARCH_FETCH_FAILED',e.stack||String(e));process.exitCode=2;});
