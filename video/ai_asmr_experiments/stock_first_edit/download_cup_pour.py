#!/usr/bin/env python3
"""Pexels editorial asset intake: two real cup pours. Uses public free-use originals, never stock-site redistributions."""
import hashlib,json,os,subprocess,requests
from pathlib import Path
D=Path(os.environ.get("OUT_DIR","/tmp/asmr-cup-pour"));D.mkdir(parents=True,exist_ok=True)
entries=[
 ("color_pour",32698841,"https://www.pexels.com/video/vibrant-drink-pouring-in-slow-motion-32698841/","khezez | خزاز"),
 ("clear_pour",8816380,"https://www.pexels.com/video/pouring-water-on-a-glass-cup-8816380/","TP Motion"),
]
rows=[]
for name,ident,page,creator in entries:
 url=f"https://www.pexels.com/download/video/{ident}/"
 output=D/(name+".mp4")
 try:
  with requests.get(url,headers={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36","Referer":page},timeout=90,stream=True,allow_redirects=True) as r:
   r.raise_for_status()
   sz=0
   with output.open("wb") as f:
    for data in r.iter_content(chunk_size=262144):
     if not data:continue
     sz+=len(data)
     if sz>85_000_000:raise ValueError("Max source size exceeded")
     f.write(data)
  j=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(output)],text=True)
  info=json.loads(j);duration=float(info["format"]["duration"]);v=next(s for s in info["streams"] if s["codec_type"]=="video")
  if duration<6 or v["width"]<720:raise ValueError("Source unsuitable")
  rows.append(dict(name=name,origin=page,creator=creator,source_url=url,license="https://www.pexels.com/license/",sha256=hashlib.sha256(output.read_bytes()).hexdigest(),bytes=sz,duration=duration,width=v["width"],height=v["height"],status="verified"))
  print("VALID",name,sz,duration,v["width"],v["height"],flush=True)
 except Exception as e:
  if output.exists():output.unlink()
  rows.append(dict(name=name,origin=page,creator=creator,error=str(e),status="failed"))
  print("FAIL",name,str(e),flush=True)
(D/"CUP_SOURCE_LEDGER.json").write_text(json.dumps(rows,indent=2))
if not any(x["status"]=="verified" for x in rows):raise RuntimeError("No real pour footage downloaded")
