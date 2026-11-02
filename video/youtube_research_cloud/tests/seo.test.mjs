import test from 'node:test';
import assert from 'node:assert/strict';
import {parseCsv,analyzeStudioCsv,auditMetadata} from '../public/seo.mjs';
import {researchMarket} from '../src/market.mjs';
test('CSV: quotes, BOM, escaped quotes, CRLF',()=>assert.deepEqual(parseCsv('\uFEFFTitle,Views\r\n"History, ""facts""",1,000\r\n'),[['Title','Views'],['History, "facts"','1','000']]));
test('CSV: standard quoted numeric metrics and baseline flag',()=>{
 const csv='Video title,Content type,Impressions,Impressions click-through rate (%),Views,Average percentage viewed (%)\nA,Videos,"1,200",8,500,60\nB,Videos,500,10,300,55\nC,Videos,800,2,400,50\n';
 const x=analyzeStudioCsv(csv);assert.equal(x.videos,3);assert.equal(x.results[2].ctr,2);assert.ok(x.results[2].findings.some(z=>z.metric==='ctr'));assert.equal(x.formatWarning,null);
});
test('CSV: separate Shorts from long-form baselines',()=>{
 const x=analyzeStudioCsv('Video title,Content type,Views,Stayed to watch (%)\nOne,Shorts,300,40\nTwo,Shorts,100,20\nThree,Shorts,500,50\nLong,Videos,100,10');
 assert.equal(x.baseline.Shorts.stayed.median,40);assert.equal(x.baseline['Long-form'].stayed.median,null);assert.equal(x.results[1].findings[0].metric,'stayed');
});
test('CSV: no fake confidence on sample of one',()=>{
 const x=analyzeStudioCsv('Video title,Views,Impressions click-through rate (%)\nA,1,1');
 assert.equal(x.results[0].findings[0].kind,'observe');assert.ok(x.formatWarning);
});
test('CSV: reject unsupported formats',()=>assert.throws(()=>analyzeStudioCsv('Name,Count\nA,1'),/video-title column/));
test('metadata: catch required limits and placeholders',()=>{
 assert.equal(auditMetadata({title:'',description:'x'}).publishReady,false);
 assert.equal(auditMetadata({title:'Great Fire of London',description:'Records and eyewitness reports of the fire.'}).publishReady,true);
});
test('market: live counts and view-per-day, no invented keyword volume',async()=>{
 const requests=[]; const fetcher=async url=>{requests.push(url);return {ok:true,json:async()=>url.includes('/search?')?
 {items:[{id:{videoId:'abc'}}]}:
 {items:[{id:'abc',snippet:{title:'History of Earth',channelTitle:'Channel',publishedAt:'2026-10-31T00:00:00Z'},statistics:{viewCount:'240',likeCount:'5'},contentDetails:{duration:'PT1M'}}]}}};
 const r=await researchMarket('History',{apiKey:'private',now:new Date('2026-11-02T00:00:00Z'),fetcher});
 assert.equal(requests.length,2);assert.equal(r.results[0].viewsPerDay,120);assert.equal(r.results[0].views,240);assert.equal(r.quotaEstimate,101);assert.equal(r.results[0].keywordVolume,undefined);
});
test('market: no key does not attempt network',async()=>assert.equal((await researchMarket('Pyramids')).configured,false));
