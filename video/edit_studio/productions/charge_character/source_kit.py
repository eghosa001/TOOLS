#!/usr/bin/env python3
"""Fetch the original CC-BY-licensed Blender Studio Charge motion picture.
Never ingest the user's reference edits into the source directory.
"""
import json, urllib.request,hashlib,subprocess,os
from pathlib import Path
from PIL import Image, ImageDraw,ImageFont
ROOT=Path("delivery/charge_original");ROOT.mkdir(parents=True,exist_ok=True)
URL="https://video.blender.org/download/web-videos/04da454b-9893-4184-98f3-248d00625efe-1080.mp4"
F=ROOT/"Charge_2022_BlenderStudio_original_1080p.mp4"
def run(cmd):subprocess.run(cmd,check=True,timeout=280)
req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0 (creative-commons-film-editor)"})
with urllib.request.urlopen(req,timeout=140) as r,F.open("wb") as w:
    while True:
        b=r.read(2<<20)
        if not b:break
        w.write(b)
        if w.tell()//(20<<20)!=(w.tell()-len(b))//(20<<20):print("SOURCE_DOWNLOAD_BYTES",w.tell(),flush=True)
if F.stat().st_size<20_000_000:raise RuntimeError("Bad film download")
info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(F)]))
dur=float(info["format"]["duration"]);print("FILM_DURATION",dur,"BYTES",F.stat().st_size,flush=True)
assert dur>240
sha=hashlib.sha256(F.read_bytes()).hexdigest()
w=320;h=196;cols=6;count=60;rows=(count+cols-1)//cols
sheet=Image.new("RGB",(cols*w,rows*(h+25)),(18,20,23))
d=ImageDraw.Draw(sheet)
for idx in range(count):
    t=3.5+idx*(dur-10)/(count-1)
    out=ROOT/f"_frame{idx:02d}.jpg"
    run(["ffmpeg","-v","error","-y","-ss",str(round(t,2)),"-i",str(F),"-frames:v","1","-vf",f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2","-q:v","4",str(out)])
    with Image.open(out) as im:sheet.paste(im.convert("RGB"),((idx%cols)*w,(idx//cols)*(h+25)))
    d.text(((idx%cols)*w+9,(idx//cols)*(h+25)+h+5),f"{t:05.1f}s",fill="white")
    out.unlink()
sheet.save(ROOT/"CHARGE_60_FRAME_CONTACT_SHEET.jpg",quality=86)
license_notes={
  "asset":"Charge (2022) original short animated film","source":URL,
  "original_publisher":"Blender Studio / Blender Foundation",
  "license":"CC BY 4.0","license_url":"https://creativecommons.org/licenses/by/4.0/",
  "authoritative_project":"https://studio.blender.org/projects/charge/",
  "web_license_evidence":"https://commons.wikimedia.org/wiki/File:Charge_-_Blender_Open_Movie-full_movie.webm",
  "sha256":sha,"duration":dur,"size":F.stat().st_size,
  "reference_clips_used_as_source":False,
  "required_attribution":"Charge (CC) Blender Foundation | studio.blender.org. Adapted video edit under Creative Commons Attribution 4.0."
}
(ROOT/"SOURCE_PROVENANCE.json").write_text(json.dumps(license_notes,indent=2))
print("ORIGINAL_CHARGE_SOURCE_READY",sha,flush=True)
