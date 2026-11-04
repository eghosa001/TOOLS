#!/usr/bin/env python3
"""Inspect exact 2026 AEK and Real Madrid public CBS highlight streams for original analysis.
No DRM/access bypass. No assumption that access grants reuse rights.
"""
import json,os,re,subprocess,sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
root=Path("football_edit_output/aek_madrid_2026_cbs_candidates");root.mkdir(parents=True,exist_ok=True)
pages={
  "city_aek":"https://www.cbssports.com/watch/champions-league/video/manchester-city-vs-aek-athens-game-highlights",
  "madrid_leipzig":"https://www.cbssports.com/watch/champions-league/video/real-madrid-vs-rb-leipzig-game-highlights-2",
}
summary={}
for name,url in pages.items():
  obj={"page":url,"status":"SOURCE_NOT_VERIFIED_OR_BLOCKED"}
  try:
    r=requests.get(url,timeout=32,headers={"User-Agent":"Mozilla/5.0 (compatible; editorial-football-source-review/1.0)"})
    obj["html_status"]=r.status_code;r.raise_for_status()
    soup=BeautifulSoup(r.text,"html.parser")
    candidates=[]
    for node in soup.find_all("script",attrs={"type":"application/ld+json"}):
      try: q=json.loads(node.string or node.get_text())
      except Exception:continue
      items=q if isinstance(q,list) else [q]
      for v in items:
        if v.get("@type")=="VideoObject" and "highlights" in str(v.get("name","")).lower():
          candidates.append({"title":v.get("name"),"url":v.get("contentUrl"),"duration":v.get("duration")})
    obj["candidates"]=[{"title":x["title"],"duration":x["duration"]} for x in candidates[:5]]
    match=next((c for c in candidates if (
      ("Manchester City" in c["title"] and "AEK" in c["title"]) if name=="city_aek"
      else ("Real Madrid" in c["title"] and "Leipzig" in c["title"]))),None)
    if not match:raise RuntimeError("Exact intended game missing from source metadata")
    source_url=match["url"]
    if not source_url or not source_url.startswith("https://sports.play.cbsi.video/"):raise RuntimeError("No valid public HLS URL")
    obj["source_title"]=match["title"];obj["original_duration"]=match["duration"]
    f=root/(name+"_review.mp4")
    cmd=["ffmpeg","-hide_banner","-loglevel","warning","-nostdin","-y","-i",source_url,
      "-t","110","-vf","scale=-2:480,fps=25","-an","-c:v","libx264","-preset","veryfast","-crf","27",str(f)]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150)
    obj["ffmpeg_status"]=p.returncode;obj["ffmpeg_last_error"]=p.stderr.decode("utf-8",errors="replace")[-1000:]
    if p.returncode or not f.exists() or f.stat().st_size<600000:raise RuntimeError("Actual source not accessible or valid")
    obj["status"]="Genuine match candidate downloaded; visual review and copyright analysis mandatory"
    obj["bytes"]=f.stat().st_size
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(f),
      "-vf","fps=1/10,scale=480:-2","-frames:v","10",str(root/(name+"_%02d.jpg"))],check=True,timeout=50)
  except Exception as e:
    obj["error"]=str(e);print("SOURCE_FAILURE",name,str(e),flush=True)
  summary[name]=obj
  print("SOURCE_RESULT",name,json.dumps(obj)[:1400],flush=True)
(root/"SOURCE_ACCESS_REPORT.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
