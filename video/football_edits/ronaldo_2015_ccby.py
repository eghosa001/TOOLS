#!/usr/bin/env python3
"""CR7 2014/15: real-footage edit, original soundtrack, CC BY 3.0 attribution."""
from __future__ import annotations
import hashlib, json, os, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(os.environ.get("FOOTBALL_OUTPUT_DIR","football_edit_output"))
SRC=Path(os.environ.get("FOOTBALL_SOURCE_FILE","football_edit_source/ronaldo_48_goals_2014_15.ogv"))
ROOT.mkdir(parents=True,exist_ok=True)
FPS=30
FRAMES=78
CUT_DURATION=FRAMES/FPS
CUTS=[
 (12.0,"48 GOALS","THE SEASON WAS DIFFERENT","01"),
 (44.0,"35 GAMES","A CAMPAIGN FOR THE AGES","02"),
 (78.0,"ONE SEASON","REAL MADRID  /  2014–15","03"),
 (112.0,"THE FINISHING","EVERY OPENING WAS DANGEROUS","04"),
 (146.0,"THE MOVEMENT","ALWAYS ONE STEP AHEAD","05"),
 (183.0,"THE HUNGER","NEVER SATISFIED","06"),
 (219.0,"NUMBER 7","CRISTIANO RONALDO","07"),
 (253.0,"CR7  /  PRIME","WHAT WAS HIS BEST GOAL?","08")
]
FONTS=["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FONT=next((p for p in FONTS if Path(p).exists()),None)
if not FONT: raise RuntimeError("Required DejaVu font missing")

def run(args,timeout=300):
 print("RUN", " ".join(str(x) for x in args)[:300],flush=True)
 subprocess.run([str(x) for x in args],check=True,timeout=timeout)

def font(size): return ImageFont.truetype(FONT,size)

def centered(draw,y,message,color,size):
 f=font(size); b=draw.textbbox((0,0),message,font=f)
 draw.text(((1080-(b[2]-b[0]))//2,y),message,fill=color,font=f)

def make_card(title,subtitle,num):
 w,h=1080,1920
 yy,xx=np.ogrid[:h,:w]
 glow_a=np.exp(-((xx-790)**2+(yy-280)**2)/(2*480**2))
 glow_b=np.exp(-((xx-100)**2+(yy-1630)**2)/(2*480**2))
 ar=np.empty((h,w,3),dtype=np.uint8)
 for i,v in enumerate((10,12,22)):
  ar[:,:,i]=np.clip(v+glow_a*([25,19,4][i])+glow_b*([2,13,25][i]),0,255).astype(np.uint8)
 image=Image.fromarray(ar).convert("RGBA")
 d=ImageDraw.Draw(image,"RGBA")
 for y in range(80,h,110): d.line((60,y,1020,y),fill=(255,255,255,12),width=1)
 d.rounded_rectangle((50,642,1030,1280),radius=20,fill=(230,181,55,255))
 d.rectangle((53,650,1027,1272),fill=(0,0,0,255))
 d.text((62,83),"FOOTBALL  /  ARCHIVE EDIT",fill=(224,196,119,255),font=font(26))
 d.text((940,83),num,fill=(255,255,255,190),font=font(29))
 d.line((65,134,1018,134),fill=(255,255,255,72),width=2)
 centered(d,225,title,(255,247,215,255),116 if len(title)<13 else 87)
 centered(d,463,"RONALDO   •   REAL MADRID",(245,245,250,230),36)
 d.rounded_rectangle((55,1380,1025,1520),radius=18,fill=(255,255,255,17),outline=(255,255,255,55),width=2)
 centered(d,1416,subtitle,(255,255,255,255),39 if len(subtitle)<32 else 33)
 centered(d,1643,"2014 / 15    —    48 LEAGUE GOALS",(222,189,93,245),30)
 centered(d,1783,"REAL MATCH FOOTAGE  •  ORIGINAL EDIT",(255,255,255,155),23)
 return image

def build_original_beat(seconds,path):
 sr=48000;n=int(round(seconds*sr))
 a=np.zeros(n,dtype=np.float64)
 rng=np.random.default_rng(708)
 beat=60/140
 for b in range(int(seconds/beat)+2):
  start=int(b*beat*sr)
  if start>=n:continue
  t=np.arange(min(int(.4*sr),n-start))/sr
  kick=.48*np.sin(2*np.pi*(54*t+36*np.exp(-t*22)*t))*np.exp(-t*24)
  a[start:start+len(t)]+=kick
  if b%4 in (1,3):
   z=np.arange(min(int(.18*sr),n-start))/sr
   sn=.15*rng.normal(0,1,len(z))*np.exp(-z*24)+.06*np.sin(2*np.pi*185*z)*np.exp(-z*15)
   a[start:start+len(z)]+=sn
 for h in range(int(seconds/(beat/2))+2):
  start=int(h*beat/2*sr)
  if start>=n:continue
  t=np.arange(min(int(.065*sr),n-start))/sr
  a[start:start+len(t)]+=(.049 if h%2 else .065)*rng.normal(0,1,len(t))*np.exp(-t*80)
 scale=[55.0,65.406,73.416,49.0]
 for b in range(int(seconds/beat)+1):
  start=int(b*beat*sr)
  if start>=n:continue
  t=np.arange(min(int(.36*sr),n-start))/sr
  f=scale[(b//4)%4]
  a[start:start+len(t)]+=(.17*np.sin(2*np.pi*f*t)+.055*np.sin(2*np.pi*2*f*t))*np.exp(-t*6)
 for i in range(len(CUTS)):
  start=int(i*CUT_DURATION*sr)
  if start>=n:continue
  t=np.arange(min(int(.2*sr),n-start))/sr
  a[start:start+len(t)]+=.16*rng.normal(0,1,len(t))*np.exp(-t*18)
 fade=int(.2*sr)
 a[:fade]*=np.linspace(.05,1,fade)
 a[-fade:]*=np.linspace(1,0,fade)
 pcm=np.int16(np.clip(np.tanh(a*1.45)*.85,-1,1)*32767)
 with wave.open(str(path),"wb") as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())

def probe(path):
 return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)]))

def main():
 if not SRC.is_file():raise RuntimeError("Missing licensed source footage: "+str(SRC))
 digest=hashlib.sha1()
 with SRC.open("rb") as f:
  while b:=f.read(1024*1024):digest.update(b)
 sha1=digest.hexdigest()
 if sha1!="6a75c744421acb76b827441fd9967d778cc19a4a":
  raise RuntimeError("Unexpected source; licence evidence does not match: "+sha1)
 length=float(probe(SRC)["format"]["duration"])
 if length<267:raise RuntimeError("Truncated source duration")
 work=ROOT/"segments";work.mkdir(exist_ok=True)
 segments=[]
 for i,(start,title,subtitle,num) in enumerate(CUTS):
  if start+CUT_DURATION>length:raise RuntimeError("Shot beyond source")
  card=work/f"card_{i:02}.png";make_card(title,subtitle,num).save(card,optimize=True)
  shot=work/f"shot_{i:02}.mp4"
  flt=("[0:v]fps=30,scale=974:548:flags=lanczos,"
       "eq=contrast=1.1:saturation=1.13,unsharp=3:3:0.35:3:3:0,"
       "format=yuv420p[match];"
       "[1:v]format=yuv420p[card];"
       "[card][match]overlay=x=53:y=686:shortest=1,format=yuv420p[v]")
  run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
       "-ss",start,"-i",SRC,"-loop","1","-i",card,
       "-filter_complex",flt,"-map","[v]","-frames:v",FRAMES,
       "-an","-c:v","libx264","-preset","veryfast","-crf","20",
       "-pix_fmt","yuv420p",shot],timeout=320)
  segments.append(shot);print(f"SHOT {i+1}/8 DONE",flush=True)
 manifest=work/"concat.txt"
 manifest.write_text("".join("file '%s'\n"%p.resolve().as_posix() for p in segments))
 silent=work/"silent.mp4"
 run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
      "-f","concat","-safe","0","-i",manifest,"-c","copy",silent])
 seconds=len(CUTS)*CUT_DURATION
 wav=work/"original_beat.wav";build_original_beat(seconds,wav)
 final=ROOT/"CR7_48_Goals_One_Season_Football_Edit_1080x1920.mp4"
 run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
      "-i",silent,"-i",wav,"-map","0:v:0","-map","1:a:0",
      "-c:v","copy","-c:a","aac","-b:a","192k","-ar","48000",
      "-t",seconds,"-movflags","+faststart",
      "-metadata","artist=Original edit; footage Real Madrid",
      final])
 result=probe(final)
 vid=next(s for s in result["streams"] if s["codec_type"]=="video")
 if (vid["width"],vid["height"])!=(1080,1920):raise RuntimeError("Dimensions invalid")
 if not any(s["codec_type"]=="audio" for s in result["streams"]):raise RuntimeError("Audio missing")
 if not 20<float(result["format"]["duration"])<22:raise RuntimeError("Duration invalid")
 source_url="https://commons.wikimedia.org/wiki/File:All_48_goals_of_Cristiano_Ronaldo,_in_35_league_matches_for_Real_Madrid_(2014-15).ogv"
 (ROOT/"rights_and_description.md").write_text(
  "# CR7 — 48 Goals. 35 Games. One Season.\n\n"
  "**Suggested title:** Cristiano Ronaldo’s 48-Goal Season Was Unreal 🤯 #ronaldo #football #shorts\n\n"
  "**Description:** 48 league goals in 35 La Liga games. Cristiano Ronaldo’s 2014/15 Real Madrid season deserves a rewatch. This edited short selects, re-times, re-grades, reframes and captions moments from Real Madrid's archive, with a newly programmed percussion soundtrack. What was his best goal?\n\n"
  "**Video copyright attribution:** Real Madrid, 'All 48 goals of Cristiano Ronaldo, in 35 league matches for Real Madrid (2014-15)', Wikimedia Commons, CC BY 3.0.\n"
  f"Source: {source_url}\nLicense: https://creativecommons.org/licenses/by/3.0/\n"
  "Adaptations: selected excerpts, sound replaced, colour, typesetting, composition and editorial sequencing. No endorsement implied.\n\n"
  "Footage reuse rights and YouTube reused-content monetization requirements are separate. Monetization is NOT guaranteed; Content ID disputes may still arise even for licensed material.\n")
 (ROOT/"technical_and_rights_qa.json").write_text(json.dumps({
  "status":"rendered_technical_checks_passed_pending_editorial_review",
  "source_sha1_verified":sha1,"source_url":source_url,
  "license":"CC BY 3.0; Real Madrid; attribution required",
  "duration":result["format"]["duration"],
  "resolution":"1080x1920","fps":30,"cuts":len(CUTS),
  "sound":"Original programmed beat, no unlicensed music",
  "not_published":True,"youtube_monetization_guaranteed":False},indent=2))
 run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
      "-ss","9","-i",final,"-frames:v","1",ROOT/"proof_frame.jpg"])
 print("RENDERED",final,final.stat().st_size,flush=True)

if __name__=="__main__":main()
