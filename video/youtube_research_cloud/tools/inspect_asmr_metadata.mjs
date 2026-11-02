// Strictly read-only, low-quota inspection. Public metadata only. No YouTube writes.
import {legacyYouTubeAccessToken,verifySurrealOwner,SURREAL_ASMR_ID} from '../src/auth.mjs';
const IDS=['FgUS9hMYEbk','YQByazV5lWU','fn_pI5rHo6c','s13AOyf4OOk','_w-wOh86vbA'];
try{
 const token=await legacyYouTubeAccessToken();
 await verifySurrealOwner(token);
 const url=new URL('https://www.googleapis.com/youtube/v3/videos');
 url.searchParams.set('part','snippet,status,statistics');
 url.searchParams.set('id',IDS.join(','));
 const r=await fetch(url,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error('YouTube videos.list failed HTTP '+r.status);
 const j=await r.json();
 const videos=j.items||[];
 if(videos.length!==IDS.length||videos.some(x=>x.snippet?.channelId!==SURREAL_ASMR_ID))
  throw Error('One or more target videos are missing or belong to a different channel.');
 console.log('OWNER_CHANNEL_VERIFIED',SURREAL_ASMR_ID);
 for(const v of videos){
  console.log('PUBLIC_VIDEO_METADATA '+JSON.stringify({
    id:v.id,title:v.snippet?.title,description:v.snippet?.description,
    tags:v.snippet?.tags||[],categoryId:v.snippet?.categoryId,
    defaultLanguage:v.snippet?.defaultLanguage||null,
    privacy:v.status?.privacyStatus,views:v.statistics?.viewCount
  }));
 }
 // A lightweight capability check only; no private analytics in public logs.
 const a=new URL('https://youtubeanalytics.googleapis.com/v2/reports');
 a.searchParams.set('ids','channel==MINE');
 a.searchParams.set('startDate','2026-10-30');
 a.searchParams.set('endDate','2026-11-01');
 a.searchParams.set('metrics','views');
 a.searchParams.set('dimensions','day');
 const x=await fetch(a,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(12000)});
 console.log('PRIVATE_ANALYTICS_READ_HTTP',x.status,'(values not logged)');
}catch(e){console.error('::error::'+String(e.message||e).slice(0,260));process.exitCode=1}
