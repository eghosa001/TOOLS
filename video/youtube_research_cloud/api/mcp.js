const research=require("./research");
const tools=[
{name:"historical_anniversaries",description:"Find real dated historical events from Wikimedia. These are not YouTube trends.",inputSchema:{type:"object",properties:{month:{type:"integer"},day:{type:"integer"}}}},
{name:"youtube_topic_search",description:"Search YouTube videos. Requires optional free YouTube API key configured in cloud environment.",inputSchema:{type:"object",properties:{topic:{type:"string"}},required:["topic"]}},
{name:"youtube_seo_draft",description:"Create draft titles, description and three Shorts ideas with no paid AI credits.",inputSchema:{type:"object",properties:{topic:{type:"string"}},required:["topic"]}}
];
module.exports=async(req,res)=>{
 if(req.method!=="POST")return res.status(405).json({error:"POST only"});
 const secret=process.env.RESEARCH_ACCESS_TOKEN;
 if(secret&&req.headers.authorization!=="Bearer "+secret)return res.status(401).json({error:"Unauthorized"});
 const p=req.body||{},id=p.id??null;
 const answer=result=>res.status(200).json({jsonrpc:"2.0",id,result});
 const error=(code,message)=>res.status(200).json({jsonrpc:"2.0",id,error:{code,message}});
 if(p.method==="initialize")return answer({protocolVersion:"2025-03-26",capabilities:{tools:{}},serverInfo:{name:"free-history-research",version:"1.0"}});
 if(p.method==="notifications/initialized")return res.status(202).end();
 if(p.method==="ping")return answer({});
 if(p.method==="tools/list")return answer({tools});
 if(p.method!=="tools/call")return error(-32601,"Unknown method");
 try{
 const name=p.params?.name,args=p.params?.arguments||{};let result;
 if(name==="youtube_seo_draft")result=research.seo(args.topic);
 else if(name==="youtube_topic_search")result=await research.youtube(args.topic);
 else if(name==="historical_anniversaries"){const now=new Date();result=await research.history(args.month||now.getUTCMonth()+1,args.day||now.getUTCDate());}
 else return error(-32602,"Unknown tool");
 return answer({content:[{type:"text",text:JSON.stringify(result)}]});
 }catch(e){return answer({content:[{type:"text",text:String(e.message||e)}],isError:true})}
};
