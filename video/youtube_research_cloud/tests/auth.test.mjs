import test from 'node:test';
import assert from 'node:assert/strict';
import {legacyYouTubeAccessToken,verifySurrealOwner,SURREAL_ASMR_ID} from '../src/auth.mjs';
import {auditPublicChannel} from '../src/channel.mjs';
test('legacy OAuth token uses existing secret names and does not send them in a URL',async()=>{
 const env={YOUTUBE_OAUTH_CLIENT_JSON:JSON.stringify({installed:{client_id:'id',client_secret:'secret'}}),YOUTUBE_REFRESH_TOKEN:'refresh'};
 const calls=[];
 const token=await legacyYouTubeAccessToken({env,fetcher:async(url,options)=>{
  calls.push({url,options});
  return {ok:true,json:async()=>({access_token:'ephemeral'})};
 }});
 assert.equal(token,'ephemeral');
 assert.equal(calls.length,1);
 assert.equal(calls[0].url,'https://oauth2.googleapis.com/token');
 assert.equal(calls[0].options.body.get('refresh_token'),'refresh');
});
test('owner API accepts only the observed Surreal ASMR channel ID',async()=>{
 const f=async()=>({ok:true,json:async()=>({items:[{id:SURREAL_ASMR_ID,snippet:{title:'Surreal ASMR',customUrl:'@surrealasmr-r3x'}}]})});
 const c=await verifySurrealOwner('token',{fetcher:f});
 assert.equal(c.title,'Surreal ASMR');
 await assert.rejects(()=>verifySurrealOwner('token',{fetcher:async()=>({ok:true,json:async()=>({items:[{id:'UCOther',snippet:{title:'Facts Uncovered'}}]})})}),/different YouTube channel/);
});
test('channel public report works with OAuth and never leaks access token in URL',async()=>{
 const calls=[];
 const fetcher=async(url,options)=>{
  calls.push({url,headers:options.headers});
  let data;
  if(url.includes('/channels?'))data={items:[{id:SURREAL_ASMR_ID,snippet:{title:'Surreal ASMR'},statistics:{videoCount:'1'},contentDetails:{relatedPlaylists:{uploads:'UUexample'}}}]};
  else if(url.includes('/playlistItems?'))data={items:[{contentDetails:{videoId:'v123'}}]};
  else data={items:[{id:'v123',snippet:{title:'Rain ASMR',description:'Rain ambience'},statistics:{viewCount:'321'},contentDetails:{duration:'PT1M'}}]};
  return {ok:true,json:async()=>data};
 };
 const report=await auditPublicChannel('surrealasmr-r3x',{accessToken:'secret-access',fetcher});
 assert.equal(report.results[0].views,321);
 assert.equal(report.quotaCalls,3);
 assert.ok(calls.every(x=>x.headers.Authorization==='Bearer secret-access'));
 assert.ok(calls.every(x=>!x.url.includes('secret-access')&&!x.url.includes('key=')));
});
