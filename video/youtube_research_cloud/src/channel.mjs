// Public YouTube channel inspection using the existing server-side API key.
// No OAuth access, write operations, private analytics, keyword-volume guesses or search.list.
const API = 'https://www.googleapis.com/youtube/v3/';
export const DEFAULT_ASMR_HANDLE = 'surrealasmr-r3x';
export const REQUIRED_CHANNEL_NAME = 'Surreal ASMR';
export function normalizeHandle(value) {
  const handle = String(value ?? '').trim().replace(/^@/, '');
  if (!/^[a-zA-Z0-9._-]{3,40}$/.test(handle)) throw new Error('Invalid YouTube handle');
  return handle;
}
const safeCount = v => v == null || v === '' || !/^\d+$/.test(String(v)) ? null : Number(v);
export function metadataIssues(snippet={}) {
  const issues=[];
  const title=String(snippet.title ?? '').trim();
  const desc=String(snippet.description ?? '').trim();
  if (!title) issues.push('Missing title');
  if (title.length > 100) issues.push('Title exceeds 100 characters');
  if (!desc) issues.push('Missing description');
  if (desc.length > 5000) issues.push('Description exceeds 5000 characters');
  if (/\[(add|insert|placeholder|timestamp|source)\b/i.test(desc)) issues.push('Unresolved editorial placeholder');
  return issues;
}
export async function auditPublicChannel(handle=DEFAULT_ASMR_HANDLE,
  {apiKey,limit=25,fetcher=fetch}={}) {
  handle=normalizeHandle(handle);
  if (!apiKey) return {type:'youtube-channel-public-audit',handle,configured:false,results:[],
    notice:'YOUTUBE_API_KEY is not configured in this execution environment. No API calls attempted.'};
  if (!Number.isInteger(limit)||limit<1||limit>50) throw new Error('limit must be 1-50');
  let used=0;
  async function get(resource,params){
    const u=new URL(API+resource);
    for(const [k,v] of Object.entries({...params,key:apiKey}))u.searchParams.set(k,String(v));
    const r=await fetcher(u.toString(),{signal:AbortSignal.timeout(10000)});
    used++;
    if(!r.ok)throw new Error('YouTube '+resource+' request failed (HTTP '+r.status+')');
    return r.json();
  }
  const ch=(await get('channels',{part:'snippet,statistics,contentDetails',forHandle:handle})).items?.[0];
  if(!ch) return {type:'youtube-channel-public-audit',handle,configured:true,found:false,results:[],
    quotaCalls:used,notice:'No public channel returned for this handle; no other channel will be substituted.'};
  const uploads=ch.contentDetails?.relatedPlaylists?.uploads;
  const ids=uploads?(await get('playlistItems',{part:'contentDetails',playlistId:uploads,maxResults:limit}))
    .items?.map(x=>x.contentDetails?.videoId).filter(Boolean)||[]:[];
  const data=ids.length?(await get('videos',{part:'snippet,statistics,contentDetails',id:[...new Set(ids)].join(',')})).items||[]:[];
  const map=new Map(data.map(v=>[v.id,v]));
  const results=ids.map(id=>{
    const v=map.get(id);if(!v)return null;
    const s=v.snippet||{};
    return {
      videoId:id,url:'https://www.youtube.com/watch?v='+id,
      title:s.title||'',description:s.description||'',
      publishedAt:s.publishedAt||null,
      durationISO:v.contentDetails?.duration||null,
      views:safeCount(v.statistics?.viewCount),likes:safeCount(v.statistics?.likeCount),
      comments:safeCount(v.statistics?.commentCount),
      issues:metadataIssues(s)
    };
  }).filter(Boolean);
  return {
    type:'youtube-channel-public-audit',configured:true,found:true,handle,
    channel:{id:ch.id,title:ch.snippet?.title||'',description:ch.snippet?.description||'',
      videoCount:safeCount(ch.statistics?.videoCount),subscriberCount:safeCount(ch.statistics?.subscriberCount),
      viewCount:safeCount(ch.statistics?.viewCount)},
    checkedAt:new Date().toISOString(),quotaCalls:used,results,
    limits:['Public lifetime counts only; no private CTR, engaged views, search terms or retention.',
      'Duration does not establish Shorts classification, aspect ratio or revenue eligibility.',
      'Metadata warnings are mechanical; no video or channel was modified.',
      'Do not change recently published videos without a verified baseline and exact owner approval.']
  };
}
