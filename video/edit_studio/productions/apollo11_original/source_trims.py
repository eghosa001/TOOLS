#!/usr/bin/env python3
"""Download independent NASA/NARA primary footage; deliver tiny accurate source trims and licensed music (NO REFERENCE CLIPS)."""
import urllib.request,subprocess,hashlib,json,time
from pathlib import Path
from PIL import Image,ImageDraw
R=Path("delivery/apollo_raw_trims");R.mkdir(parents=True,exist_ok=True)
C=Path("work/apollo_raw_source");C.mkdir(parents=True,exist_ok=True)
src={
"crew":("https://catalog.archives.gov/medialz/mopix/255/PV/255-pv-74-r2.mp4","https://www.archives.gov/research/motion-pictures/apollo-av"),
"launch":("https://catalog.archives.gov/medialz/mopix/255/PV/255-pv-75-r2.mp4","https://www.archives.gov/research/motion-pictures/apollo-av"),
"step":("https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010453/Apollo_11_EVA_1_AppleTv.webmhd.webm","https://svs.gsfc.nasa.gov/10453/"),
"flag":("https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010458/Apollo_11_EVA_6_AppleTv.webmhd.webm","https://svs.gsfc.nasa.gov/10458/")
}
def run(c):subprocess.run(c,check=True,timeout=240)
def get(url,path):
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0; Archival research"})
 with urllib.request.urlopen(req,timeout=160) as s,open(path,"wb") as f:
  while True:
   b=s.read(1<<20)
   if not b:break
   f.write(b)
 assert path.stat().st_size>50000
 return path
def h(p):
 z=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):z.update(b)
 return z.hexdigest()
files={}
for k,(u,page) in src.items():
 p=C/(k+".source")
 get(u,p);files[k]=str(p);print("FETCHED",k,p.stat().st_size,flush=True)
shots=[
 ("crew",10,12.2,.95),("crew",33,34.55,1.05),("crew",57,59.15,.90),
 ("launch",108,110.4,1),("launch",120,121.25,1.20),
 ("launch",125,126.5,1.20),("launch",138,140.1,.86),("launch",145,146.4,1.25),
 ("step",155,157.6,.92),("step",160,162,1.06),
 ("flag",145,147.6,1),("flag",153,155.35,1)]
records=[]
for i,(source,a,b,speed) in enumerate(shots):
 p=R/f"source_{i:02d}_{source}.mp4"
 # Accurate frame seeking, no source soundtrack, and no pre-existing edit elements.
 run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-ss",str(a),"-i",files[source],"-t",str(b-a),"-an",
 "-c:v","libx264","-preset","ultrafast","-crf","17","-pix_fmt","yuv420p",str(p)])
 records.append({"shot":i+1,"path":p.name,"source":source,"start":a,"end":b,"speed":speed,"sha256":h(p),"source_page":src[source][1]})
 print("TRIM_OK",i+1,p.stat().st_size,flush=True)
songs=[
 ("licensed_music.mp3","https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Descent.mp3"),
 ("impact.mp3","https://assets.mixkit.co/active_storage/sfx/2908/2908-preview.mp3"),
 ("riser.mp3","https://assets.mixkit.co/active_storage/sfx/632/632-preview.mp3"),
 ("radio.wav","https://www.nasa.gov/wav/62283main_landing.wav")]
for name,url in songs:
 try:
  p=get(url,R/name); print("AUDIO_OK",name,p.stat().st_size,flush=True)
 except Exception as exc:print("AUDIO_NOT_AVAILABLE",name,str(exc),flush=True)
metadata={"footage_origin":"NASA/NARA ORIGINAL FILM","reference_footage_used":False,
"source_pages":{k:v[1] for k,v in src.items()},"shots":records,
"music":"The Descent by Kevin MacLeod, CC BY 4.0 https://creativecommons.org/licenses/by/4.0/"}
(R/"sources.json").write_text(json.dumps(metadata,indent=2))
m=Image.new("RGB",(3*320,4*205),(25,25,25));dr=ImageDraw.Draw(m)
for i,rec in enumerate(records):
 f=R/f"_f{i:02d}.png"
 run(["ffmpeg","-v","error","-y","-ss","0.45","-i",str(R/rec["path"]),"-frames:v","1",
 "-vf","scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2",str(f)])
 with Image.open(f) as p:m.paste(p.convert("RGB"),((i%3)*320,(i//3)*205))
 dr.text(((i%3)*320+9,(i//3)*205+184),f"{i+1:02d} {rec['source']} {rec['start']}s",fill="white")
 f.unlink()
m.save(R/"independent_original_footage_contact.jpg",quality=85)
print("ORIGINAL_ONLY_ASSET_PACK_READY",flush=True)
