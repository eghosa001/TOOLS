// YouTube Data API competitor evidence. Search costs 100 quota units per request;
// videos.list costs 1. Public counts are measured, never keyword-volume estimates.
const ENDPOINT = 'https://www.googleapis.com/youtube/v3/';
export async function researchMarket(topic, {apiKey, days=180, limit=20, now=new Date(), fetcher=fetch}={}) {
  topic = String(topic ?? '').trim().slice(0,150);
  if (!topic) throw new Error('Enter a YouTube search phrase');
  days = Number(days); limit=Number(limit);
  if (!Number.isInteger(days) || days < 1 || days > 3650) throw new Error('days must be between 1 and 3650');
  if (!Number.isInteger(limit) || limit < 1 || limit > 25) throw new Error('limit must be between 1 and 25');
  if (!apiKey) return {type:'market',topic,configured:false,results:[],notice:'No YOUTUBE_API_KEY configured. Connect a free YouTube Data API key to enable real public-video metrics.'};
  async function api(resource, params) {
    const u = new URL(ENDPOINT+resource);
    for (const [k,v] of Object.entries({...params,key:apiKey})) u.searchParams.set(k,String(v));
    const response = await fetcher(u.toString(), {signal:AbortSignal.timeout(10000)});
    if (!response.ok) throw new Error('YouTube Data API '+resource+' returned '+response.status);
    return await response.json();
  }
  const cutoff = new Date(now.getTime()-days*86400000).toISOString();
  const s = await api('search',{part:'snippet',q:topic,type:'video',order:'relevance',maxResults:limit,publishedAfter:cutoff});
  const ids = [...new Set((s.items??[]).map(v=>v?.id?.videoId).filter(Boolean))];
  if (!ids.length) return {type:'market',topic,configured:true,results:[],sampleSize:0,notice:'No matching public videos returned in this date window. No conclusions about demand.'};
  const d = await api('videos',{part:'snippet,statistics,contentDetails',id:ids.join(',')});
  const byId = new Map((d.items??[]).map(v=>[v.id,v]));
  const results = ids.map(id=>{
    const v=byId.get(id);if(!v)return null;
    const when=Date.parse(v.snippet?.publishedAt??'');
    const ageHours=Number.isFinite(when)?Math.max(1,(now.getTime()-when)/3600000):null;
    const views=Number(v.statistics?.viewCount);
    const safeViews=Number.isFinite(views)?views:null;
    return {videoId:id,title:v.snippet?.title??'',channel:v.snippet?.channelTitle??'',publishedAt:v.snippet?.publishedAt??null,
      url:'https://www.youtube.com/watch?v='+id,views:safeViews,likes:v.statistics?.likeCount==null?null:Number(v.statistics.likeCount),
      viewsPerDay:safeViews!==null && ageHours!==null?Math.round(safeViews/(ageHours/24)):null,
      duration:v.contentDetails?.duration??null};
  }).filter(Boolean);
  results.sort((a,b)=>(b.viewsPerDay??-1)-(a.viewsPerDay??-1));
  return {type:'market',topic,configured:true,source:'YouTube Data API v3 search.list + videos.list',sampleSize:results.length,
    windowDays:days,asOf:now.toISOString(),quotaEstimate:101,results,
    notice:'Views/day is views divided by elapsed days since publication, not current views/hour or verified trend growth. Results are a non-random YouTube Search sample; no keyword volume, difficulty score, or guaranteed ranking is inferred.'};
}