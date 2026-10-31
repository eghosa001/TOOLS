#!/usr/bin/env python3
"""Fetch exactly eight individually verified Mixkit Free License clips for local creative editing."""
import json,hashlib,subprocess,os,time,sys
from pathlib import Path
import requests
OUT=Path(os.environ.get("STOCK_OUT","/tmp/stock_sources"));OUT.mkdir(parents=True,exist_ok=True)
ITEMS={
 "jets":("thin-streams-of-water-falling-on-a-water-surface",51968),
 "ripple":("texture-of-the-water-surface-when-droplets-fall-on-it",3903),
 "fire":("intense-fire-burning-coal",3459),
 "coal":("fire-burning-coal-close-up",3440),
 "candle":("candle-lighting-in-the-dark",3458),
 "candles":("candles-lighting-detail-views",3453),
 "ink":("multicolor-ink-swirls-in-water",286),
 "inkmono":("black-ink-swirl-in-water",203),
}
S=requests.Session();S.headers.update({"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) SatisfyingTextureASMR/1.0"})
manifest={"source":"Mixkit Stock Video Free License","license":"https://mixkit.co/license/modal/videoFree/","assets":[],"failures":[]}
for name,(slug,id) in ITEMS.items():
 page=f"https://mixkit.co/free-stock-video/{slug}-{id}/"
 download=f"https://assets.mixkit.co/videos/download/mixkit-{slug}-{id}.mp4"
 preview=f"https://assets.mixkit.co/videos/preview/mixkit-{slug}-{id}-large.mp4"
 row={"name":name,"page":page,"license":"https://mixkit.co/license/modal/videoFree/"}
 try:
  response=S.get(page,timeout=25)
  if response.status_code!=200 or "Mixkit Stock Video Free License" not in response.text:
   raise RuntimeError("per-item free license not verifiable: "+str(response.status_code))
  for url in [download,preview]:
   try:
    print("GET",name,url,flush=True)
    r=S.get(url,stream=True,timeout=75)
    r.raise_for_status()
    path=OUT/(name+".mp4")
    size=0
    with open(path,"wb") as f:
     for chunk in r.iter_content(256*1024):
      if not chunk:continue
      size+=len(chunk)
      if size>35_000_000:raise RuntimeError("Asset exceeds 35MB transfer guard")
      f.write(chunk)
    with open(path,"rb") as f:f.seek(4);good=f.read(4)==b"ftyp"
    if size<250_000 or not good:raise RuntimeError("not an MP4 file: "+str(size))
    p=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height,codec_type","-of","json",str(path)],capture_output=True,text=True,timeout=30,check=True)
    info=json.loads(p.stdout);d=float(info["format"]["duration"]);v=next(s for s in info["streams"] if s["codec_type"]=="video")
    if d<6 or int(v["width"])<700:raise RuntimeError("unsuitable duration or width")
    row.update({"download_url":url,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"bytes":size,"duration":d,"width":v["width"],"height":v["height"]})
    manifest["assets"].append(row);print("VALID",name,size,d,flush=True);break
   except Exception as ex:
    print("RETRY",name,str(ex),flush=True)
    if path.exists():path.unlink()
  else:raise RuntimeError("all official URL variants failed")
 except Exception as ex:
  row["error"]=str(ex);manifest["failures"].append(row);print("FAIL",name,str(ex),flush=True)
 (OUT/"SOURCE_LICENSES.json").write_text(json.dumps(manifest,indent=2))
if len(manifest["assets"])<6 or len(set(a["name"] for a in manifest["assets"]))<6:
 raise SystemExit("Insufficient footage: "+str(manifest["failures"]))
for group in [("jets","ripple"),("fire","coal"),("candle","candles"),("ink","inkmono")]:
 if not any(a["name"] in group for a in manifest["assets"]):raise SystemExit("missing group "+str(group))
print("SUCCESS: licensed items",len(manifest["assets"]))
