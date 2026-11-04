#!/usr/bin/env python3
"""Check original NASA camera films and shot choices before assembly.

Does not generate or alter any images. Contact sheets are real video frames.
"""
from __future__ import annotations
import hashlib,json,subprocess,urllib.request,time
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path("video/history_studio/productions/apollo11_eight_minute")
STORY=json.loads((ROOT/"story.json").read_text())
ASSETS=Path("work/apollo11_eight/source")
OUT=Path("delivery/apollo11_eight/source_review")
ASSETS.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
def info(p):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)],timeout=90))
def fetch(src):
    path=ASSETS/src["filename"]
    if path.exists() and path.stat().st_size>1_000_000:
        return path
    for attempt in range(3):
        try:
            req=urllib.request.Request(src["url"],headers={"User-Agent":"FactsUncovered-NASA-Original-Film-Editor/1.0"})
            with urllib.request.urlopen(req,timeout=120) as stream,path.open("wb") as output:
                while True:
                    buf=stream.read(1024*1024)
                    if not buf:break
                    output.write(buf)
            if path.stat().st_size<1_000_000:raise ValueError("source too small")
            return path
        except Exception:
            path.unlink(missing_ok=True)
            if attempt==2:raise
            time.sleep(3+attempt*2)
    raise RuntimeError("No source file")
def frame(src,t,p):
    subprocess.run(["ffmpeg","-hide_banner","-v","error","-y","-ss",str(t),"-i",str(src),
                    "-frames:v","1","-vf","scale=320:180:force_original_aspect_ratio=decrease",
                    str(p)],check=True,timeout=100)
    with Image.open(p) as im:return im.convert("RGB").copy()
report={"sources":{},"missing_shots":[],"notes":"Actual NASA camera footage frames only, no synthetic images"}
for key,source in STORY["sources"].items():
    p=fetch(source)
    metadata=info(p); dur=float(metadata["format"]["duration"])
    video=next((s for s in metadata["streams"] if s.get("codec_type")=="video"),None)
    if not video:raise ValueError(f"No video track for {key}")
    shots=[b for c in STORY["chapters"] for b in c["beats"] if b["source"]==key]
    requested=[b["source_in_seconds"] for b in shots]
    invalid=[b["id"] for b in shots if b["source_in_seconds"]+16 > dur]
    report["missing_shots"]+=invalid
    sample=sorted(set([min(max(0,int(n)),int(dur)-2) for n in requested] +
        [int(dur*x/16) for x in range(1,16)]))
    sheet=Image.new("RGB",(5*320,((len(sample)+4)//5)*205),(18,20,24))
    for i,t in enumerate(sample):
        tmp=OUT/f"tmp_{key}_{i}.jpg"
        img=frame(p,t,tmp);tmp.unlink(missing_ok=True)
        x=i%5*320;y=i//5*205
        sheet.paste(img,(x,y))
        ImageDraw.Draw(sheet).text((x+8,y+183),f"{key} t={t}s",fill="white")
    sheet.save(OUT/f"{key}_source_contact_sheet.jpg",quality=86)
    report["sources"][key]={"duration":round(dur,2),"size":p.stat().st_size,
      "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
      "width":video.get("width"),"height":video.get("height"),
      "source_url":source["url"],"page_url":source["page"],
      "shot_count":len(requested),"source_inpoints":requested,"invalid_shots":invalid}
    print("NASA_SOURCE_CHECK",key,report["sources"][key],flush=True)
(OUT/"SOURCE_PREFLIGHT.json").write_text(json.dumps(report,indent=2)+"\n")
if report["missing_shots"]:raise SystemExit("SOURCE TIMECODES INVALID: "+str(report["missing_shots"]))
print("SOURCE_PREFLIGHT_PASS",len(STORY["sources"]),flush=True)
