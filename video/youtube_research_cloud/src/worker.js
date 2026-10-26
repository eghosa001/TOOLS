// Cloudflare Workers adapter for Facts Uncovered history-video research.
// No external packages, payment keys, Node server or database required.
const WIKI="https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/";
const YT="https://www.googleapis.com/youtube/v3/search";
const clip=(x,len=160)=>String(x??"").trim().slice(0,len);
const two=n=>String(n).padStart(2,"0");
const json=(obj,status=200)=>new Response(JSON.stringify(obj),{status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff"}});
const fail=(e,status=502)=>json({error:clip(e?.message||e,160)},status);
async function anniversaries(month,day){
  const m=+month,d=+day;
  if(!Number.isInteger(m)||m<1||m>12||!Number.isInteger(d)||d<1||d>31) throw Error("Invalid calendar date");
  const source=WIKI+two(m)+"/"+two(d);
  const r=await fetch(source,{headers:{"Accept":"application/json","User-Agent":"FactsUncoveredResearch/1.0 (https://github.com/eghosa001/TOOLS)"},signal:AbortSignal.timeout(8500)});
  if(!r.ok)throw Error("Wikimedia source unavailable: HTTP "+r.status);
  const data=await r.json();
  const events=(data.events||[]).slice(0,12).map(e=>({year:e.year,text:e.text,source:e.pages?.[0]?.content_urls?.desktop?.page||source}));
  return {type:"historical-anniversaries",date:two(m)+"-"+two(d),events,source,notice:"Historical anniversaries are editorial leads, not evidence of viral videos or YouTube search volumes. Verify against further reputable sources."};
}
function seo(topic){
 const t=clip(topic);if(!t)throw Error("Enter a historical topic");
 return {type:"seo",topic:t,titles:[t+": What the Evidence Shows","What Really Happened? The Story of "+t,"The History Behind "+t],shorts:["One thing people get wrong about "+t,"The forgotten detail in "+t,"What the original evidence says about "+t],description:"Explore the history of "+t+" through documented evidence and competing accounts. [Add verified source links and timestamps.]",notice:"Unscored editorial draft only. Review facts and title claims before publishing."};
}
async function youtube(topic,env,authenticated=false){
  const t=clip(topic);if(!t)throw Error("Enter a search topic");
  if(!env.YOUTUBE_API_KEY)return {type:"youtube",topic:t,configured:false,results:[],notice:"Free YouTube Data API key not configured yet. No paid vidIQ credits are used."};
  if(!env.RESEARCH_ACCESS_TOKEN||!authenticated)return {type:"youtube",topic:t,configured:true,results:[],notice:"YouTube API search is protected. Supply your private research access token; it is never stored in GitHub.",accessRequired:true};
  const q=new URL(YT);q.searchParams.set("part","snippet");q.searchParams.set("q",t);q.searchParams.set("type","video");q.searchParams.set("maxResults","10");q.searchParams.set("order","viewCount");q.searchParams.set("key",env.YOUTUBE_API_KEY);
  const r=await fetch(q,{signal:AbortSignal.timeout(8500)});if(!r.ok)throw Error("YouTube API unavailable: HTTP "+r.status);
  const d=await r.json();return {type:"youtube",topic:t,configured:true,results:(d.items||[]).map(v=>({title:v.snippet?.title,channel:v.snippet?.channelTitle,published:v.snippet?.publishedAt,url:"https://www.youtube.com/watch?v="+v.id?.videoId})),notice:"These are API search samples, not keyword search-volume measurements or verified viral outliers."};
}
const tools=[
 {name:"historical_anniversaries",description:"Real dated historical events; not YouTube trends.",inputSchema:{type:"object",properties:{month:{type:"integer"},day:{type:"integer"}}}},
 {name:"youtube_topic_search",description:"Look up YouTube videos using an authorized free YouTube Data API key, if configured.",inputSchema:{type:"object",properties:{topic:{type:"string"}},required:["topic"]}},
 {name:"youtube_seo_draft",description:"Draft history-video titles, description and Shorts angles without paid AI credits.",inputSchema:{type:"object",properties:{topic:{type:"string"}},required:["topic"]}}
];
async function mcp(request,env){
 if(request.method!=="POST")return json({error:"POST required"},405);
 if(env.RESEARCH_ACCESS_TOKEN&&request.headers.get("authorization")!=="Bearer "+env.RESEARCH_ACCESS_TOKEN)return json({error:"Unauthorized"},401);
 const content=await request.text();if(content.length>16000)return json({error:"Request too large"},413);
 let p;try{p=JSON.parse(content)}catch{return json({error:"Invalid JSON"},400)}
 const id=p.id??null;
 const result=x=>json({jsonrpc:"2.0",id,result:x});
 const error=(code,message)=>json({jsonrpc:"2.0",id,error:{code,message}});
 if(p.method==="initialize")return result({protocolVersion:"2025-03-26",capabilities:{tools:{}},serverInfo:{name:"free-history-research",version:"1.0.0"}});
 if(p.method==="notifications/initialized")return new Response(null,{status:202});
 if(p.method==="ping")return result({});
 if(p.method==="tools/list")return result({tools});
 if(p.method!=="tools/call")return error(-32601,"Unknown method");
 try{
  const args=p.params?.arguments||{},name=p.params?.name;
  const now=new Date();
  let d;
  if(name==="historical_anniversaries")d=await anniversaries(args.month||now.getUTCMonth()+1,args.day||now.getUTCDate());
  else if(name==="youtube_topic_search")d=await youtube(args.topic,env,true);
  else if(name==="youtube_seo_draft")d=seo(args.topic);
  else return error(-32602,"Unknown tool");
  return result({content:[{type:"text",text:JSON.stringify(d)}]});
 }catch(e){return result({content:[{type:"text",text:clip(e?.message||e)}],isError:true})}
}
export default {
 async fetch(request,env){
  const url=new URL(request.url);
  if(url.pathname==="/api/mcp")return mcp(request,env);
  if(url.pathname==="/health"||url.pathname==="/api/health")return json({ok:true,service:"facts-uncovered-research",youtubeApiConfigured:!!env.YOUTUBE_API_KEY});
  if(url.pathname==="/api/research"){
   if(request.method!=="GET")return json({error:"GET required"},405);
   const q=url.searchParams,t=q.get("type")||"history";
   try{
    if(t==="health")return json({ok:true,youtubeApiConfigured:!!env.YOUTUBE_API_KEY});
    if(t==="seo")return json(seo(q.get("topic")));
    if(t==="youtube"){const authed=!!env.RESEARCH_ACCESS_TOKEN && request.headers.get("authorization")==="Bearer "+env.RESEARCH_ACCESS_TOKEN;return json(await youtube(q.get("topic"),env,authed));}
    if(t==="history"){const now=new Date();return json(await anniversaries(q.get("month")||now.getUTCMonth()+1,q.get("day")||now.getUTCDate()))}
    return json({error:"Unknown research type"},400);
   }catch(e){return fail(e)}
  }
  return env.ASSETS.fetch(request);
 }
};
