import test from 'node:test';
import assert from 'node:assert/strict';
import {auditPublicChannel,normalizeHandle,metadataIssues} from '../src/channel.mjs';
test('ASMR audit: resolve exact handle, uploads and public video counters without search calls',async()=>{
 const resources=[];
 const fetcher=async url=>{
   const u=new URL(url);resources.push({path:u.pathname,params:u.searchParams});
   const body=u.pathname.endsWith('/channels') ? {items:[{id:'UCexample',snippet:{title:'Surreal ASMR'},statistics:{subscriberCount:'3',videoCount:'5',viewCount:'2400'},contentDetails:{relatedPlaylists:{uploads:'UUexample'}}}]}:
     u.pathname.endsWith('/playlistItems') ? {items:[{contentDetails:{videoId:'v123'}},{contentDetails:{videoId:'v456'}}]}:
     {items:[{id:'v123',snippet:{title:'Rain ASMR',description:'Sound of rain',publishedAt:'2026-11-01T06:00:00Z'},statistics:{viewCount:'150',likeCount:'10'},contentDetails:{duration:'PT2M45S'}},
       {id:'v456',snippet:{title:'Water',description:''},statistics:{},contentDetails:{duration:'PT10M'}}]};
   return {ok:true,json:async()=>body};
 };
 const d=await auditPublicChannel('@surrealasmr-r3x',{apiKey:'test',fetcher});
 assert.equal(d.channel.id,'UCexample'); assert.equal(d.results.length,2);
 assert.equal(d.results[0].views,150);assert.equal(d.results[1].views,null);
 assert.deepEqual(d.results[1].issues,['Missing description']);
 assert.equal(d.quotaCalls,3);
 assert.deepEqual(resources.map(x=>x.path),['/youtube/v3/channels','/youtube/v3/playlistItems','/youtube/v3/videos']);
 assert.equal(resources[0].params.get('forHandle'),'surrealasmr-r3x');
 assert.equal(resources[2].params.get('id'),'v123,v456');
});
test('ASMR audit: missing secret makes zero network requests',async()=>{
 const d=await auditPublicChannel('surrealasmr-r3x',{fetcher:()=>{throw Error('unexpected network')}});
 assert.equal(d.configured,false);assert.deepEqual(d.results,[]);
});
test('ASMR audit: wrong channel is not replaced silently',async()=>{
 const d=await auditPublicChannel('surrealasmr-r3x',{apiKey:'test',fetcher:async()=>({ok:true,json:async()=>({items:[]})})});
 assert.equal(d.found,false);assert.equal(d.quotaCalls,1);
});
test('ASMR audit: invalid handles rejected and issues limited to verified metadata',()=>{
 assert.throws(()=>normalizeHandle('../../foo'));assert.throws(()=>normalizeHandle(''));
 assert.deepEqual(metadataIssues({title:'Test',description:'A [add sources]'}),['Unresolved editorial placeholder']);
});
