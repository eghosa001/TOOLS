#!/usr/bin/env python3
"""Acquire unedited movie scenes from DC's own clips, nothing from uploaded fan-edit references."""
from pathlib import Path
import urllib.request,subprocess,json,os
ROOT=Path("delivery/fast_joker");ROOT.mkdir(parents=True,exist_ok=True)
Y=ROOT/"yt-dlp"
with urllib.request.urlopen("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp",timeout=80) as r,Y.open("wb") as w:
 while True:
  b=r.read(1<<20)
  if not b:break
  w.write(b)
Y.chmod(0o755)
urls=[
 ("joker_interrogation","https://www.dailymotion.com/video/x70gjz"),
 ("joker_bank","https://www.dailymotion.com/video/x82ol7k"),
 ("joker_mob_pencil","https://www.dailymotion.com/video/x7k001"),
 ("joker_interrogation_alt","https://www.dailymotion.com/video/x6mjsx"),
 ("joker_entrance","https://www.dailymotion.com/video/xbpusia")]
good=[]
for name,url in urls:
 for flavor in [[]]:
  dest=ROOT/(name+".mp4")
  cmd=[str(Y),"--no-playlist","--no-warnings","--no-progress","--socket-timeout","15","--retries","1",
       "--format","best[ext=mp4][height<=1080]/best[height<=1080]",
       "-o",str(dest),*flavor,url]
  try:
   p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
   print("SOURCE_ATTEMPT",name,p.returncode,p.stderr[-330:],flush=True)
   if p.returncode==0 and dest.exists() and dest.stat().st_size>1000000:
    print("SOURCE_FOUND",name,dest.stat().st_size,flush=True)
    good.append({"name":name,"url":url,"size":dest.stat().st_size,"file":str(dest)})
    break
  except Exception as e:print("SOURCE_ERROR",name,str(e)[:200],flush=True)
if not good:raise RuntimeError("No usable film footage, must not recycle references")
(ROOT/"sources.json").write_text(json.dumps(good,indent=2))
print("ORIGINAL_JOKER_FOOTAGE_ACQUIRED",len(good),flush=True)
