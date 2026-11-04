#!/usr/bin/env python3
"""Original Apollo 11 edit. References are for craft analysis ONLY and NEVER source frames."""
from __future__ import annotations
import hashlib,json,urllib.request,subprocess,time,os,math
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path("delivery/original_apollo"); HERE.mkdir(parents=True,exist_ok=True)
RAW=Path("work/original_apollo");RAW.mkdir(parents=True,exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SOURCES={
 "crew":{"url":"https://catalog.archives.gov/medialz/mopix/255/PV/255-pv-74-r2.mp4","page":"https://www.archives.gov/research/motion-pictures/apollo-av","creator":"National Archives / NASA, 1969, reel 255-PV-74"},
 "launch":{"url":"https://catalog.archives.gov/medialz/mopix/255/PV/255-pv-75-r2.mp4","page":"https://www.archives.gov/research/motion-pictures/apollo-av","creator":"National Archives / NASA, 1969, reel 255-PV-75"},
 "step":{"url":"https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010453/Apollo_11_EVA_1_AppleTv.webmhd.webm","page":"https://svs.gsfc.nasa.gov/10453/","creator":"NASA Apollo 11 original lunar television, restored archive"},
 "flag":{"url":"https://svs.gsfc.nasa.gov/vis/a010000/a010400/a010458/Apollo_11_EVA_6_AppleTv.webmhd.webm","page":"https://svs.gsfc.nasa.gov/10458/","creator":"NASA Apollo 11 original lunar television, restored archive"}
}
def run(cmd,timeout=600): subprocess.run(cmd,check=True,timeout=timeout)
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def fetch(urls,dst,minimum=10000,optional=False):
 if isinstance(urls,str): urls=[urls]
 for u in urls:
  for attempt in range(2):
   try:
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 archive research editor"})
    with urllib.request.urlopen(req,timeout=100) as resp,open(dst,"wb") as f:
     while True:
      b=resp.read(1<<20)
      if not b:break
      f.write(b)
    if dst.stat().st_size<minimum:raise RuntimeError("not a media file")
    print("SOURCE_OK",dst,round(dst.stat().st_size/1e6,2),"MB",u,flush=True)
    return u
   except Exception as exc:
    print("SOURCE_RETRY",str(exc)[:125],flush=True)
    dst.unlink(missing_ok=True)
    time.sleep(2)
 if optional:return None
 raise RuntimeError("Original external source download failed "+str(urls))
def info(path):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,width,height","-of","json",str(path)]))
for key,val in SOURCES.items():
 dst=RAW/(key+".mp4")
 fetch(val["url"],dst,600000)
 val["file"]=str(dst);val["sha256"]=sha(dst)
 val["duration"]=float(info(dst)["format"]["duration"])
 print("SOURCE_PROBE",key,val["duration"],flush=True)
# A real, independently licensable music track. No soundtrack extracted from the supplied references.
MUSIC=RAW/"mixkit_epical_drums_01_676.mp3"
music_url=fetch([
 "https://assets.mixkit.co/active_storage/music/676/676.mp3",
 "https://assets.mixkit.co/active_storage/music/676/676-preview.mp3",
 "https://cdn.mixkit.co/music/preview/mixkit-epical-drums-01-676.mp3"
],MUSIC,160000,optional=True)
SFX_URLS={
 "impact":"https://assets.mixkit.co/active_storage/sfx/2908/2908-preview.mp3",
 "riser":"https://assets.mixkit.co/active_storage/sfx/632/632-preview.mp3"
}
sfx={}
for key,url in SFX_URLS.items():
 path=RAW/(key+".mp3")
 actual=fetch(url,path,7000,optional=True)
 if actual:sfx[key]={"file":str(path),"url":actual,"sha256":sha(path)}
NASA_AUDIO=RAW/"apollo_landing_radio.wav"
radio_url=fetch(["https://www.nasa.gov/wav/62283main_landing.wav",
 "https://nssdc.gsfc.nasa.gov/planetary/sound/apollo11.wav"],NASA_AUDIO,10000,optional=True)
# In/out chosen from ORIGINAL archival source logs, never from a finished edit.
# First story: departure and peril; at an authored impact cue ~6.2s, cut to rocket launch.
SHOTS=[
 ("crew",10.0,12.2,.95,"The crew prepares to leave Earth"),
 ("crew",33.0,34.55,1.05,"A close human decision before launch"),
 ("crew",57.0,59.15,.90,"Last prelaunch glimpse, building tension"),
 ("launch",108.0,110.4,1.00,"Launch-reveal starts on the large impact"),
 ("launch",120.0,121.25,1.20,"Cut to new launch perspective on rhythm"),
 ("launch",125.0,126.5,1.20,"Rocket acceleration"),
 ("launch",138.0,140.1,.86,"Hold on meaningful launch motion"),
 ("launch",145.0,146.4,1.25,"Final punch of the launch sequence"),
 ("step",155.0,157.6,.92,"First steps after the journey"),
 ("step",160.0,162.0,1.06,"Continue the astronaut movement"),
 ("flag",145.0,147.6,1.00,"Lunar flag reveals mission consequence"),
 ("flag",153.0,155.35,1.00,"Complete the lasting historical payoff")]
SEG=HERE/"segments";SEG.mkdir(exist_ok=True)
timeline=[];clock=0
for idx,(source,begin,end,speed,reason) in enumerate(SHOTS):
 file=Path(SOURCES[source]["file"])
 if SOURCES[source]["duration"]<end+0.1:raise RuntimeError(f"Out point past source: {source}/{end}")
 segment=SEG/f"{idx:02d}.mp4"
 # 1:1 matches the supplied square-format references without excessive zoom.
 # A continuous subdued editorial color finish and strictly original film.
 vf=f"fps=30,scale=1080:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1080,setsar=1,setpts=(PTS-STARTPTS)/{speed:.4f},eq=contrast=1.09:saturation=0.94:brightness=-0.006,unsharp=5:5:0.32:5:5:0,format=yuv420p"
 run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
      "-ss",str(begin),"-i",str(file),"-t",str(end-begin),"-an",
      "-vf",vf,"-r","30","-c:v","libx264","-preset","veryfast",
      "-crf","19","-pix_fmt","yuv420p",str(segment)],timeout=400)
 dur=float(info(segment)["format"]["duration"])
 timeline.append({"shot":idx+1,"source":source,"source_in":begin,"source_out":end,"speed":speed,
   "start":round(clock,3),"end":round(clock+dur,3),"reason":reason})
 clock+=dur
 print("CUT",idx+1,source,round(clock,3),flush=True)
f=HERE/"concat.txt"
f.write_text("".join(f"file '{p.resolve()}'\n" for p in sorted(SEG.glob("*.mp4"))))
joined=HERE/"picture.mp4"
run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","concat","-safe","0","-i",str(f),
     "-an","-c:v","copy",str(joined)],timeout=120)
# Text is sparse and earns its position in the story, with safe margins for mobile.
# The sole pale impact flash is 2 frames at the original sequence switch.
def text_filter(text,start,end,y=820,size=42,color="white"):
 t=text.replace("\\","\\\\").replace(":","\\:").replace("'","\\'")
 return (f"drawtext=fontfile={FONT}:text='{t}':fontsize={size}:fontcolor={color}:"
         f"borderw=3:bordercolor=black@0.70:x=(w-text_w)/2:y={y}:"
         f"enable='between(t,{start:.3f},{end:.3f})'")
drops=[timeline[2]["end"],timeline[7]["end"],timeline[9]["end"]]
vfilters=[
 "eq=contrast=1.03:saturation=0.99",
 text_filter("THE WORLD HELD ITS BREATH",.30,2.5,820,34),
 text_filter("THREE MEN. ONE MOON.",3.15,5.9,840,37),
 text_filter("APOLLO 11",drops[0]+.12,drops[0]+2.0,820,67),
 text_filter("JULY 20  /  1969",drops[1]+.1,drops[1]+2.6,830,38),
 text_filter("ONE SMALL STEP",drops[2]+.08,drops[2]+1.6,840,43),
 text_filter("HISTORY CHANGED HERE",clock-2.25,clock-.18,845,35),
 f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.24:t=fill:enable='between(t,{drops[0]:.3f},{drops[0]+.067:.3f})'",
 "format=yuv420p"]
final=HERE/"APOLLO11_ORIGINAL_CINEMATIC_REVIEW.mp4"
# Explicit original licensed mix plus intentional NASA radio cue if available.
inputs=["-i",str(joined)];mix=[];aud=[]
if music_url:
 inputs+=["-stream_loop","-1","-i",str(MUSIC)]
 aud.append(("[1:a]volume=0.40,highpass=f=36,afade=t=in:st=0:d=.65,"
             f"afade=t=out:st={max(clock-1.6,0):.3f}:d=1.5[mus]"))
 mix.append("[mus]")
if "impact" in sfx:
 index=len(mix)+1  # this is not input count; actual input count is tracked below
# Assemble audio inputs without guessing indexes.
source_idx=1+(1 if music_url else 0)
for name,position,gain in [("riser",max(drops[0]-1.6,0),0.26),("impact",drops[0],0.70),("impact",drops[1],0.23)]:
 if name not in sfx:continue
 inputs+=["-i",sfx[name]["file"]]
 tag=f"sfx{len(aud)}"; pos=int(position*1000)
 aud.append(f"[{source_idx}:a]atrim=0:2.1,asetpts=PTS-STARTPTS,volume={gain},adelay={pos}|{pos}[{tag}]")
 mix.append(f"[{tag}]");source_idx+=1
if radio_url:
 inputs+=["-i",str(NASA_AUDIO)]
 tag="radio"
 aud.append(f"[{source_idx}:a]atrim=0:4.8,asetpts=PTS-STARTPTS,highpass=f=200,lowpass=f=5000,volume=1.4,adelay={int((drops[1]+.3)*1000)}|{int((drops[1]+.3)*1000)}[{tag}]")
 mix.append(f"[{tag}]")
# A music-only candidate is not acceptable: a real soundtrack must be available.
if not music_url: raise RuntimeError("Music not downloaded: cannot claim reference-quality sound")
chain=";".join(aud)+";"+("".join(mix)+f"amix=inputs={len(mix)}:duration=longest:normalize=0,alimiter=limit=0.89,atrim=0:"+str(clock)+"[mix]" if len(mix)>1 else mix[0]+"anull[mix]")
run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",*inputs,
     "-filter_complex",f"[0:v]{','.join(vfilters)}[v];{chain}",
     "-map","[v]","-map","[mix]","-r","30","-t",f"{clock:.3f}",
     "-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p",
     "-c:a","aac","-b:a","224k","-movflags","+faststart",str(final)],timeout=800)
# Evidence-driven contact sheets from actual frames, not synthetic frames.
def sheet(path,count=12):
 w,h=360,360
 img=Image.new("RGB",(4*w,3*(h+32)),(18,18,22))
 draw=ImageDraw.Draw(img)
 dur=float(info(final)["format"]["duration"])
 for i,t in enumerate([(j+.5)*dur/count for j in range(count)]):
  frame=HERE/f"_frame_{i}.png"
  run(["ffmpeg","-v","error","-y","-ss",str(t),"-i",str(final),"-frames:v","1",
       "-vf",f"scale={w}:{h}",str(frame)],timeout=30)
  with Image.open(frame) as frameimg:img.paste(frameimg.convert("RGB"),((i%4)*w,(i//4)*(h+32)))
  draw.text(((i%4)*w+10,(i//4)*(h+32)+h+6),f"{t:.1f} seconds",fill=(255,255,255))
  frame.unlink()
 img.save(path,quality=88)
sheet(HERE/"scene_contact.jpg")
# Independent source thumbnails at real source selection points.
img=Image.new("RGB",(4*360,3*228),(18,18,22));dr=ImageDraw.Draw(img)
for i,(src,start,end,sp,reason) in enumerate(SHOTS):
 frame=HERE/f"_s_{i}.png"
 run(["ffmpeg","-v","error","-y","-ss",str(start+.45),"-i",SOURCES[src]["file"],
     "-frames:v","1","-vf","scale=360:204:force_original_aspect_ratio=decrease,pad=360:204:(ow-iw)/2:(oh-ih)/2",str(frame)],timeout=35)
 with Image.open(frame) as im:img.paste(im.convert("RGB"),((i%4)*360,(i//4)*228))
 dr.text(((i%4)*360+8,(i//4)*228+207),f"{i+1:02d} {src} {start}s",fill=(245,245,245))
 frame.unlink()
img.save(HERE/"source_contact.jpg",quality=88)
qc={"title":"Apollo 11: The World Held Its Breath","release_status":"PRIVATE_REVIEW_NOT_AUTOMATICALLY_APPROVED",
"source_files_are_original_camera_or_live_broadcast":True,
"references_used_only_for_craft":True,"synthetic_visuals":False,
"frame_size":[1080,1080],"fps":30,"duration":round(clock,3),"output_sha256":sha(final),
"music":{"track":"Epical Drums 01","artist":"Grigoriy Nuzhny","landing_page":"https://mixkit.co/free-stock-music/percussion-trailer/","license":"https://mixkit.co/license/modal/musicFree/","url":music_url,"sha256":sha(MUSIC)},
"radio_url":radio_url,"sfx":sfx,"music_drop_markers_sec":drops,
"sources":SOURCES,"shots":timeline,"claim":"Editorial review cut only; human audio/visual final approval pending"}
(HERE/"PROVENANCE_AND_QC.json").write_text(json.dumps(qc,indent=2))
(HERE/"CREDITS.txt").write_text(
 "APOLLO 11 — THE WORLD HELD ITS BREATH\nUnpublished reference-style original edit\n"
 "Moving images: NASA / US National Archives original 1969 motion pictures (not reference-channel footage)\n"
 +"\n".join(k+": "+v["page"]+" — "+v["creator"] for k,v in SOURCES.items())
 +"\nMusic: Mixkit Epical Drums 01 by Grigoriy Nuzhny — https://mixkit.co/license/modal/musicFree/\n"
 +"Effects: Mixkit free sound effect license https://mixkit.co/license/modal/sfxFree/\n"
 +"Unmodified historical narration not generated; no AI pictures or voices.\n"
 +"Do not redistribute source music separately. Human QC before publishing.\n")
print("COMPLETE_NEW_ORIGINAL_EDIT",str(final),final.stat().st_size,sha(final),round(clock,2),flush=True)
