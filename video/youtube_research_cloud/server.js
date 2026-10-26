"use strict";
const http=require("node:http"),fs=require("node:fs"),path=require("node:path");
const research=require("./api/research"),mcp=require("./api/mcp");
const html=fs.readFileSync(path.join(__dirname,"index.html"));
const port=Number(process.env.PORT||3000);
const server=http.createServer(async(req,res)=>{
 const url=new URL(req.url,"http://127.0.0.1");
 req.query=Object.fromEntries(url.searchParams);
 res.status=function(code){res.statusCode=code;return {json(obj){res.setHeader("Content-Type","application/json; charset=utf-8");res.end(JSON.stringify(obj))},end(){res.end()}}};
 if(url.pathname==="/" && req.method==="GET"){res.setHeader("Content-Type","text/html; charset=utf-8");res.end(html);return}
 if(url.pathname==="/health" && req.method==="GET"){res.setHeader("Content-Type","application/json");res.end(JSON.stringify({ok:true,service:"facts-uncovered-research",youtubeApiConfigured:!!process.env.YOUTUBE_API_KEY}));return}
 if(url.pathname==="/api/research"){await research(req,res);return}
 if(url.pathname==="/api/mcp"){
  let total=0,body="";
  if(req.method==="POST"){
   for await(const chunk of req){total+=chunk.length;if(total>16000){res.statusCode=413;res.end("Request too large");return}body+=chunk.toString()}
   try{req.body=JSON.parse(body)}catch{res.statusCode=400;res.end("Invalid JSON");return}
  }
  await mcp(req,res);return
 }
 res.statusCode=404;res.end("Not found");
});
server.listen(port,"0.0.0.0",()=>console.log("Facts Uncovered research listening on "+port));
