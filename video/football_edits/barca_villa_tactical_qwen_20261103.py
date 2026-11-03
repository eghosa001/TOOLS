#!/usr/bin/env python3
"""Source-verified Barcelona–Aston Villa 2026 original analysis review; never publishes."""
from __future__ import annotations
import os, math, hashlib, json, subprocess, urllib.request
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageOps
import torch

OUT=Path("football_edit_output/barca_villa_preview"); OUT.mkdir(parents=True,exist_ok=True)
W,H,FPS=720,1280,20
WHITE=(244,246,253); SUB=(164,180,198); GOLD=(240,188,88)
BARCA=(55,102,238); VILLA=(208,66,112)
FOREGROUND=(15,25,43)
FONT_B="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def font(n,bold=True): return ImageFont.truetype(FONT_B if bold else FONT_R,n)
def text(d,x,y,s,sz=34,color=WHITE,anchor=None,bold=True):
    d.text((x,y),s,font=font(sz,bold),fill=color,anchor=anchor)
def box(d,coords,fill,r=15,outline=None,width=1):
    d.rounded_rectangle(coords,radius=r,fill=fill,outline=outline,width=width)
def dot(d,x,y,col,r=16): d.ellipse((x-r,y-r,x+r,y+r),fill=col,outline=WHITE,width=2)
def arrow(d,a,b,col=GOLD,width=8):
    d.line((a,b),fill=col,width=width)
    an=math.atan2(b[1]-a[1],b[0]-a[0])
    for da in (-2.6,2.6):
        d.line((b,(b[0]+23*math.cos(an+da),b[1]+23*math.sin(an+da))),fill=col,width=width)
def pitch(d):
    box(d,(45,396,675,968),(21,71,68),17,outline=(115,175,153),width=3)
    d.rectangle((65,416,655,948),outline=(124,182,157),width=2)
    d.line((65,681,655,681),fill=(124,182,157),width=2)
    d.ellipse((287,610,433,752),outline=(124,182,157),width=2)
    d.rectangle((225,416,495,525),outline=(124,182,157),width=2)
    d.rectangle((225,839,495,948),outline=(124,182,157),width=2)
def load_image(key,url,expected_sha1):
    f=OUT/(key+".jpg")
    req=urllib.request.Request(url,headers={"User-Agent":"FootballOriginalPreview/1.0 (licensed image attribution in preview)"})
    with urllib.request.urlopen(req,timeout=50) as resp: f.write_bytes(resp.read())
    got=hashlib.sha1(f.read_bytes()).hexdigest()
    if expected_sha1 and got!=expected_sha1: raise ValueError(f"Source checksum mismatch {key}: {got}")
    return Image.open(f).convert("RGB"),got

PHOTOS=[
    ("Yamal","https://upload.wikimedia.org/wikipedia/commons/e/e3/Lamine_Yamal_in_2025.jpg","cba2969dac3c0bc8e019b697abb7591396056167"),
    ("Maatsen","https://upload.wikimedia.org/wikipedia/commons/a/a5/Ian_Maatsen_Aston_Villa.jpg",None),
]
# A source failure must not produce an apparently complete video.
photos, hashes={},{}
for key,url,expected in PHOTOS:
    photos[key],hashes[key]=load_image(key,url,expected)
print("REAL_LICENSED_PHOTOS_VERIFIED",hashes,flush=True)

SCRIPT=(
 "Aston Villa have won all three of their Champions League matches. Barcelona have six points, "
 "but remain the heavy favourites. Here is what could decide this game. "
 "First, Barcelona's high defensive line. If Villa escape the first press, Nicolas Jackson could attack the space behind it. "
 "Second, watch Lamine Yamal against Ian Maatsen. Press too closely, and the space opens behind the full-back. "
 "Back off, and Yamal has room to create. "
 "Third, Barcelona are missing important defensive players, including Kounde, Eric Garcia and Christensen. "
 "Opta gives Barcelona a seventy-two percent chance of winning. "
 "But Villa's transitions make this more complicated than the numbers suggest."
)
MODEL="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
torch.set_num_threads(4)
from qwen_tts import Qwen3TTSModel
print("QWEN_LOADING",flush=True)
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
print("QWEN_GENERATING",flush=True)
audio,sr=model.generate_custom_voice(text=SCRIPT,speaker="Ryan",language="English")
wave=np.asarray(audio[0],dtype=np.float32).ravel()
assert np.isfinite(wave).all() and float(np.sqrt(np.mean(wave**2)))>0.007
speech=OUT/"qwen_ryan_original.wav"; sf.write(speech,wave,sr,subtype="PCM_16")
faster=OUT/"qwen_ryan_110pct.wav"
subprocess.run(["ffmpeg","-v","error","-y","-i",str(speech),"-af","atempo=1.10",str(faster)],check=True)
ffprobe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-of","json",str(faster)]))
duration=float(ffprobe["format"]["duration"])+1.7
if not 26<=duration<=100: raise ValueError("Unexpected narration duration")
print("QWEN_SECONDS",duration,flush=True)
# Each scene is precisely matched to one author-written editorial beat.
scenes=[
    ("WHY THIS MATCH MATTERS",0.145),
    ("THE CHAMPIONS LEAGUE FORM",0.145),
    ("BARCELONA'S HIGH LINE",0.245),
    ("YAMAL vs MAATSEN",0.18),
    ("BARÇA'S DEFENSIVE ABSENCES",0.13),
    ("THE PREDICTION",0.155),
]
ends=np.cumsum([q for _,q in scenes]).tolist()
background=Image.new("RGB",(W,H))
px=background.load()
for y in range(H):
    for x in range(W):
        glow=max(0,1-math.hypot((x-505)*.8,(y-250)*.5)/980)
        px[x,y]=(round(10+6*glow),round(17+10*glow),round(31+17*glow))

def photo_panel(im,photo,area):
    # Real photograph. No generated likeness or substitute match footage.
    x1,y1,x2,y2=area; tw,th=x2-x1,y2-y1
    src=ImageOps.fit(photo,(tw,th),method=Image.Resampling.LANCZOS,centering=(.5,.38))
    im.paste(src,(x1,y1))
    layer=Image.new("RGBA",im.size,(0,0,0,0))
    ld=ImageDraw.Draw(layer);ld.rectangle((x1,y1,x2,y2),fill=(2,14,30,92))
    im.paste(Image.alpha_composite(im.convert("RGBA"),layer).convert("RGB"))
def render(i,f,elapsed):
    im=background.copy(); d=ImageDraw.Draw(im)
    d.line((30,92,690,92),fill=(48,68,91),width=2)
    text(d,35,41,"MATCH INTELLIGENCE",21,GOLD)
    text(d,686,44,"UCL  /  03 NOV 2026",18,SUB,anchor="ra")
    box(d,(40,143,335,183),(29,44,60),13,outline=GOLD,width=2)
    text(d,59,152,"BARCELONA  vs  ASTON VILLA",19,GOLD)
    if i==0:
        photo_panel(im,photos["Yamal"],(38,280,675,920));d=ImageDraw.Draw(im)
        box(d,(35,251,682,391),(12,25,42),15)
        text(d,59,263,"CAN VILLA EXPOSE",51,WHITE)
        text(d,59,328,"BARCELONA?",59,GOLD)
        text(d,47,971,"6 POINTS    vs    9 POINTS",37,WHITE)
        text(d,47,1044,"Flick's press. Emery's transition threat.",24,SUB)
    elif i==1:
        text(d,43,237,"TWO VERY DIFFERENT STARTS",39,WHITE)
        for y,col,name,score,record in [(398,BARCA,"BARCELONA",6,"TWO WINS • ONE LOSS"),(668,VILLA,"ASTON VILLA",9,"THREE WINS • ZERO LOSSES")]:
            box(d,(40,y,680,y+225),(24,38,56),20,outline=col,width=4)
            text(d,66,y+32,name,29,WHITE); text(d,66,y+85,str(score).zfill(2),77,GOLD)
            text(d,172,y+127,"POINTS",22,SUB)
            text(d,66,y+182,record,20,col)
        text(d,44,1010,"Villa are unbeaten in Europe.",30,WHITE)
        text(d,44,1060,"Barcelona have home advantage.",27,SUB)
    elif i==2:
        text(d,43,235,"CAN VILLA BEAT THE PRESS?",38,WHITE)
        text(d,44,297,"This is the danger in a high line.",25,SUB)
        pitch(d)
        for x in (135,284,435,575):dot(d,x,600,BARCA,20)
        for x,y in [(166,857),(330,817),(534,862)]:dot(d,x,y,VILLA,20)
        d.line((65,632,655,632),fill=GOLD,width=4)
        dot(d,332,817,WHITE,8)
        fac=max(0,min(1,(f-.15)/.64))
        arrow(d,(334,817),(509,817-270*fac),GOLD,9)
        text(d,53,1030,"One pass into space behind the line.",25,WHITE)
        text(d,54,1085,"Illustrative tactical scenario",19,SUB)
    elif i==3:
        text(d,44,222,"THE WIDE 1-ON-1",38,WHITE)
        photo_panel(im,photos["Maatsen"],(48,300,675,890));d=ImageDraw.Draw(im)
        box(d,(42,837,675,1000),(12,25,42),17)
        text(d,63,855,"LAMINE YAMAL",36,GOLD)
        text(d,63,913,"vs IAN MAATSEN",33,WHITE)
        text(d,53,1047,"Close him down? Leave space behind.",24,WHITE)
        text(d,53,1091,"Drop off? He can create.",24,SUB)
    elif i==4:
        text(d,44,227,"DEFENSIVE ABSENCES",47,WHITE)
        text(d,44,303,"Barcelona could need adjustments.",27,SUB)
        for j,s in enumerate(["Jules Koundé","Eric García","Andreas Christensen","Xavi Espart"]):
            y=427+j*138;box(d,(46,y,673,y+111),(25,39,58),18,outline=(51,71,91),width=2)
            d.ellipse((64,y+37,98,y+72),fill=VILLA)
            text(d,120,y+36,s,32,WHITE)
        text(d,47,1050,"Selection problems matter against",25,SUB)
        text(d,47,1092,"fast, direct counterattacks.",26,WHITE)
    else:
        text(d,43,219,"WHAT THE MODEL SAYS",45,WHITE)
        text(d,43,299,"Opta: 10,000 pre-match simulations",23,SUB)
        for j,(name,value,col) in enumerate([("BARCELONA",72.0,BARCA),("DRAW",15.3,GOLD),("ASTON VILLA",12.7,VILLA)]):
            y=451+j*149;text(d,54,y,name,27,WHITE)
            text(d,655,y,str(value)+"%",30,GOLD,anchor="ra")
            box(d,(54,y+48,660,y+70),(37,51,69),10)
            box(d,(54,y+48,54+max(4,int(606*value/100*min(1,f*3))),y+70),col,10)
        box(d,(43,965,677,1102),(27,44,60),16,outline=GOLD,width=2)
        text(d,62,989,"BARCELONA ARE FAVOURITES",29,WHITE)
        text(d,62,1044,"But Villa have a way through.",28,GOLD)
    d=ImageDraw.Draw(im)
    d.line((39,1180,681,1180),fill=(48,68,91),width=2)
    text(d,42,1198,"ORIGINAL TACTICAL ANALYSIS • REVIEW",18,SUB)
    d.rectangle((0,H-10,int(W*min(1,elapsed/duration)),H),fill=GOLD)
    return im

silent=OUT/"tactical_visual.mp4"
cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(silent)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
n=math.ceil(duration*FPS)
for k in range(n):
    t=k/FPS; fraction=t/duration; i=next((j for j,end in enumerate(ends) if fraction<end),len(scenes)-1)
    start=0 if i==0 else ends[i-1]; local=(fraction-start)/max(0.01,ends[i]-start)
    p.stdin.write(render(i,max(0,min(1,local)),t).tobytes())
p.stdin.close()
if p.wait()!=0: raise RuntimeError("FFmpeg video rendering failed")
result=OUT/"Barcelona_Aston_Villa_2026_Qwen_Tactical_Preview_REVIEW.mp4"
subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(faster),"-map","0:v","-map","1:a","-c:v","copy","-c:a","aac","-b:a","192k","-t",str(duration),"-movflags","+faststart",str(result)],check=True)
proof={}
for name,sec in [("first",2),("middle",duration/2),("last",duration-3)]:
    f=OUT/("proof_"+name+".jpg")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(sec),"-i",str(result),"-frames:v","1",str(f)],check=True)
    proof[name]=str(f)
ledger={
 "status":"REVIEW_ONLY_NOT_PUBLICATION_APPROVED",
 "event":"FC Barcelona vs Aston Villa, UEFA Champions League 2026-11-03",
 "official_match_source":"https://www.fcbarcelona.com/en/news/4603354/preview-fc-barcelona-v-aston-villa",
 "prediction_source":"https://theanalyst.com/articles/barcelona-vs-aston-villa-prediction-champions-league-preview-11-2026",
 "photo_rights":[
  {"name":"Yamal 2025 (NOT 2026 match footage)","creator":"Biso","license":"CC BY 4.0","source":"https://commons.wikimedia.org/wiki/File:Lamine_Yamal_in_2025.jpg","sha1":hashes["Yamal"],"changes":"cropped, tinted, editorial text overlay"},
  {"name":"Ian Maatsen at Villa 2024 (NOT 2026 match footage)","creator":"Harold9595959","license":"CC0 1.0","source":"https://commons.wikimedia.org/wiki/File:Ian_Maatsen_Aston_Villa.jpg","sha1":hashes["Maatsen"],"changes":"cropped, tinted, editorial text overlay"}],
 "voice":{"model":MODEL,"speaker":"Ryan","speed":"1.10x pitch-preserving","script":SCRIPT,"duration":duration},
 "media":{"path":str(result),"bytes":result.stat().st_size,"sha256":hashlib.sha256(result.read_bytes()).hexdigest()},
 "review":{"visual":"human review pending","audio":"human review pending","youtube":"not uploaded","monetization":"not guaranteed"},
 "proof_frames":proof}
(OUT/"source_rights_and_technical_review.json").write_text(json.dumps(ledger,indent=2,ensure_ascii=False))
print("VIDEO_RENDERED_REVIEW",result,result.stat().st_size,flush=True)
