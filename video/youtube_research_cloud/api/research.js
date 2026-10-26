const WIKI = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/";
const YT = "https://www.googleapis.com/youtube/v3/search";
function clean(s){return String(s||"").trim().slice(0,160)}
function dd(n){return String(n).padStart(2,"0")}
async function history(month,day){
 const m=+month,d=+day;
 if(!(m>=1&&m<=12&&d>=1&&d<=31))throw Error("Invalid date");
 const source=WIKI+dd(m)+"/"+dd(d);
 const r=await fetch(source,{headers:{"User-Agent":"FreeHistoryResearch/1.0 (github.com/eghosa001/TOOLS)","Accept":"application/json"},signal:AbortSignal.timeout(9000)});
 if(!r.ok)throw Error("Wikipedia returned "+r.status);
 const data=await r.json();
 const events=(data.events||[]).slice(0,12).map(e=>({year:e.year,text:e.text,source:e.pages?.[0]?.content_urls?.desktop?.page||source}));
 return {type:"historical-anniversaries",date:dd(m)+"-"+dd(d),events,source,notice:"These events are research leads, not evidence of YouTube search volume or trending popularity."};
}
async function youtube(topic){
 const t=clean(topic);if(!t)throw Error("Enter a topic");
 const key=process.env.YOUTUBE_API_KEY;
 if(!key)return {type:"youtube",topic:t,configured:false,results:[],notice:"YouTube Data API key is not configured. Search is unavailable until a free Google API key is added to the host."};
 const q=new URL(YT);q.searchParams.set("part","snippet");q.searchParams.set("q",t);q.searchParams.set("type","video");q.searchParams.set("maxResults","10");q.searchParams.set("order","viewCount");q.searchParams.set("key",key);
 const r=await fetch(q,{signal:AbortSignal.timeout(9000)});if(!r.ok)throw Error("YouTube API returned "+r.status);
 const data=await r.json();return {type:"youtube",topic:t,configured:true,results:(data.items||[]).map(v=>({title:v.snippet?.title,channel:v.snippet?.channelTitle,published:v.snippet?.publishedAt,url:"https://www.youtube.com/watch?v="+v.id?.videoId})),notice:"Results are real search samples, not verified trends, outliers or numeric keyword volumes."};
}
function seo(topic){const t=clean(topic);if(!t)throw Error("Enter a topic");return {type:"seo",topic:t,titles:[t+": What the Evidence Shows","What Really Happened? The Story of "+t,"The History Behind "+t],shorts:["One thing people get wrong about "+t,"The forgotten detail in "+t,"What the original evidence says about "+t],description:"Explore the history of "+t+" through documented evidence and competing accounts. [Add verified source links and timestamps.]",notice:"Unscored editorial drafts; fact-check before uploading."}}
module.exports=async(req,res)=>{
 res.setHeader("Cache-Control","no-store");
 if(req.method!=="GET")return res.status(405).json({error:"GET required"});
 try{
 const type=clean(req.query.type||"history");
 if(type==="health")return res.status(200).json({ok:true,youtubeApiConfigured:!!process.env.YOUTUBE_API_KEY});
 if(type==="seo")return res.status(200).json(seo(req.query.topic));
 if(type==="youtube")return res.status(200).json(await youtube(req.query.topic));
 if(type==="history"){const now=new Date();return res.status(200).json(await history(req.query.month||now.getUTCMonth()+1,req.query.day||now.getUTCDate()));}
 return res.status(400).json({error:"Unsupported action"});
 }catch(e){return res.status(502).json({error:String(e.message||e).slice(0,160)})}
};
module.exports.history=history;module.exports.youtube=youtube;module.exports.seo=seo;
