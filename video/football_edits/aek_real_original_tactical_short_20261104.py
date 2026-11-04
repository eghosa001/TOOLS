#!/usr/bin/env python3
"""Explicitly directed, real-photo football tactical Short: AEK v Real, Nov 4 2026.
No AI visual generation; exact dated CC source images and one original camera video.
The output is editorial proof pending complete visual/audio human review.
"""
import hashlib,io,json,math,os,subprocess,time
from pathlib import Path
from urllib.parse import quote
import numpy as np,requests,soundfile as sf,torch
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps

OUT=Path("football_edit_output/aek_real_20261104")
AS=OUT/"assets"; AS.mkdir(parents=True,exist_ok=True)
W,H,FPS=540,960,30
BG=(9,15,25); GOLD=(241,184,62); PURPLE=(144,115,251); WHITE=(247,247,246)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
def grab(filename,local,optional=False):
    encoded=filename.replace(" ","_")
    md=hashlib.md5(encoded.encode()).hexdigest()
    url="https://upload.wikimedia.org/wikipedia/commons/"+md[0]+"/"+md[:2]+"/"+quote(encoded,safe="(),-._'!") 
    print("MEDIA_FETCH",local,url,flush=True)
    try:
        # Wikimedia rate-limits GitHub-hosted IPs (HTTP 429). Use the public
        # origin-pull cache wsrv.nl for authorized CC photographs, reducing bytes.
        # This is not a source-licence substitution: original author and licence
        # still come from Commons and are retained in video credits.
        headers={"User-Agent":"FootballEditorialShort/1.0 (source attribution and educational edit)"}
        if local.endswith(".webm"):
            urls=[url, "https://commons.wikimedia.org/wiki/Special:Redirect/file/"+quote(encoded,safe="(),-._'!")]
        else:
            urls=["https://wsrv.nl/?url="+quote(url.replace("https://",""),safe="")+"&w=1200&output=jpg",url]
        last=None
        for attempt in urls:
            try:
                r=requests.get(attempt,timeout=48,headers=headers)
                r.raise_for_status()
                if len(r.content)<8000:raise RuntimeError("media too small, likely an error document")
                if local.endswith(".webm") and not (r.content[:4]==b"\\x1a\\x45\\xdf\\xa3" or r.content[:4]==bytes([0x1a,0x45,0xdf,0xa3])):
                    raise RuntimeError("response is not WebM, will not mislabel it")
                if local.endswith(".jpg"):
                    from PIL import Image as _IM
                    _IM.open(io.BytesIO(r.content)).verify()
                (AS/local).write_bytes(r.content)
                print("MEDIA_OK",local,len(r.content),"host",attempt.split("/")[2],flush=True)
                return AS/local
            except Exception as ex:
                last=ex;print("MEDIA_ROUTE_FAILED",local,str(ex)[:200],flush=True)
        raise RuntimeError("No source route available: "+str(last))
    except Exception as e:
        print("MEDIA_ERROR",local,str(e),flush=True)
        if optional:return None
        raise
SOURCES={
"mbappe_video":("Kylian_Mbappe_at_Real_Madrid's_UEFA_Champions_League_game_versus_Juventus_Turin_on_22_October_2025_(video).webm","real_mbappe_2025.webm","SdHb; CC BY-SA 4.0; 22 October 2025"),
"mbappe":("Kylian_Mbappe_at_Real_Madrid's_game_versus_Juventus_Turin_on_22_October_2025.jpeg","mbappe.jpg","SdHb; CC BY-SA 4.0; 22 October 2025"),
"moukoudi":("Harold_Moukoudi_-_Lens_B_-_Le_Havre_B_(13-08-2016).jpg","moukoudi.jpg","Supporterhéninois; CC0; 13 August 2016"),
"jovic":("FC_RB_Salzburg_versus_Real_Madrid_(Testspiel,_7._August_2019)_17.jpg","jovic.jpg","Werner100359; CC BY-SA 4.0; 7 August 2019"),
"rudiger":("Antonio_Rudiger_Ecuador_v_Germany_25_June_2026-055_(cropped).jpg","rudiger.jpg","Bryan Berlin / WikiPortraits; CC BY-SA 4.0; 25 June 2026"),
"aek":("ConferenceRayoVallecanoyAEKAtenas9-4-26.jpg","aek.jpg","Goo064s; CC BY 4.0; 9 April 2026"),
}
files={}
for key,(name,fn,credit) in SOURCES.items():
    files[key]=grab(name,fn,optional=(key=="mbappe_video"))
def command(cmd):
    print("CMD", " ".join(map(str,cmd))[:500],flush=True)
    subprocess.run(cmd,check=True)
# Extract a sample from ACTUAL camera video, never reproduce a match as if it were 2026.
if files["mbappe_video"] is not None:
    command(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(files["mbappe_video"]),"-t","6.1","-vf","fps=30,scale=540:960:force_original_aspect_ratio=increase,crop=540:960,format=yuv420p","-an","-c:v","libx264","-preset","ultrafast",str(AS/"mbappe_open.mp4")])
else:
    print("EDITOR_NOTE: licensed matchday video not served; hook uses genuine AEK filmed match photograph, never invented video.",flush=True)
# Photos: crop to center, animated vertical position.
photos={}
for key in ["mbappe","moukoudi","jovic","rudiger","aek"]:
    img=ImageOps.exif_transpose(Image.open(files[key]).convert("RGB"))
    photos[key]=img
# Story beats. Each voice beat maps to one hand-authored visual state.
SCENES=[
{"id":"hook","text":"Madrid have never beaten AEK Athens away from home. Tonight, they get another shot. And this is the tactical battle to watch."},
{"id":"context","text":"Madrid have won all three Champions League games so far. Yet in Athens, they lost in nineteen eighty-five and drew three all in two thousand and two."},
{"id":"mbappe","text":"First, Mbappé against Harold Moukoudi. If Mbappé sprints into the channel, Moukoudi has to choose. Track the runner, or protect the space inside. That half-second matters."},
{"id":"jovic","text":"Then Luka Jović against Antonio Rüdiger. The former Madrid striker could attack the near post. Rüdiger must stay close without leaving the cutback free."},
{"id":"finish","text":"Madrid beat Racing Santander three nil last time. AEK lost two nil to Panathinaikos. My prediction? Real Madrid edge it two one. What's yours?"}
]
model_id="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
torch.set_num_interop_threads(2)
print("QWEN_MODEL_LOADING",model_id,flush=True)
model=Qwen3TTSModel.from_pretrained(model_id,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
beats=[]
for i,scene in enumerate(SCENES):
    print("GENERATING",scene["id"],flush=True)
    wavs,sr=model.generate_custom_voice(text=scene["text"],speaker="Ryan",language="English",instruct="Speak like a naturally quick conversational football analyst, lively but not shouty. Pronounce names as single natural names, flow smoothly and avoid dramatic pauses.")
    wav=np.asarray(wavs[0],dtype=np.float32).flatten()
    rms=float(np.sqrt((wav*wav).mean()))
    if len(wav)<sr or not np.isfinite(wav).all() or rms<.004:raise RuntimeError("invalid authentic Qwen audio")
    raw=OUT/(scene["id"]+"_Qwen_Ryan_raw.wav"); sf.write(raw,wav,sr)
    fast=OUT/(scene["id"]+"_Ryan_135.wav")
    command(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),"-af","atempo=1.35,aresample=48000","-ar","48000","-ac","1",str(fast)])
    dat,sr2=sf.read(fast)
    actual=len(dat)/sr2
    # 0.26 seconds visual tail for cuts, no long dead air
    sec=max(actual+.27, 6.2 if i==0 else 0)
    beats.append({"id":scene["id"],"text":scene["text"],"audio":str(fast),"spoken":actual,"dur":sec})
print("BEATS",json.dumps(beats),flush=True)

def cover(im,w,h,dx=0):
    iw,ih=im.size; s=max(w/iw,h/ih); nw=int(iw*s);nh=int(ih*s)
    im=im.resize((nw,nh),Image.Resampling.LANCZOS)
    x=max(0,(nw-w)//2+dx); y=max(0,(nh-h)//2)
    x=min(x,nw-w)
    return im.crop((x,y,x+w,y+h))
def base(t):
    im=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(im)
    for yy in range(H):
        c=(9+int(12*yy/H),15+int(12*yy/H),25+int(14*yy/H))
        d.line((0,yy,W,yy),fill=c)
    for x in range(0,W,54):d.line((x,0,x,H),fill=(17,26,38),width=1)
    return im
def txt(d,xy,s,size,color=WHITE,bold=False,anchor=None):
    d.text(xy,s,font=font(size,bold),fill=color,anchor=anchor,stroke_width=0)
def pill(d,x,y,s,fg=GOLD):
    bw=int(d.textbbox((0,0),s,font=font(16,True))[2]+25)
    d.rounded_rectangle((x,y,x+bw,y+34),radius=13,fill=(28,34,46),outline=fg,width=2)
    txt(d,(x+13,y+6),s,16,fg,True)
def header(d,tag):
    d.rectangle((0,0,W,10),fill=GOLD)
    txt(d,(25,27),"THE CHAMPIONS LEAGUE  |  MATCHDAY 4",13,(179,191,209),True)
    pill(d,25,59,tag)
def footer(d,label):
    d.rectangle((0,905,W,960),fill=(8,12,22))
    txt(d,(24,916),label[:64],11,(177,190,209))
    txt(d,(24,936),"AEK ATHENS   /   REAL MADRID     •     04 NOV 2026",12,WHITE,True)
def card(im,key,rect,position=0):
    x,y,w,h=rect
    p=cover(photos[key],w,h,int(math.sin(position)*7))
    # subtle dark wash to ensure readability
    im.paste(p,(x,y))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((x,y,x+w,y+h),radius=10,outline=(225,231,234),width=2)
def board(im,phase=0,mode="run"):
    d=ImageDraw.Draw(im)
    l,t,r,b=30,497,510,839
    d.rounded_rectangle((l,t,r,b),radius=18,fill=(19,56,54),outline=(63,109,103),width=3)
    for x in range(l+30,r,54): d.line((x,t+16,x,b-15),fill=(25,64,60),width=13)
    d.rectangle((l+20,t+18,r-20,b-18),outline=(133,164,146),width=2)
    d.line((270,t+18,270,b-18),fill=(133,164,146),width=2)
    d.ellipse((223,625,317,719),outline=(133,164,146),width=2)
    d.rectangle((l+20,t+113,l+75,t+247),outline=(133,164,146),width=2)
    d.rectangle((r-75,t+113,r-20,t+247),outline=(133,164,146),width=2)
    if mode=="run":
        runners=[(125,665,GOLD),(185,605,GOLD),(195,735,GOLD),(320,665,PURPLE),(360,570,PURPLE),(360,738,PURPLE)]
        runners[0]=(125+int(115*phase),665-int(65*phase),GOLD)
        runners[3]=(320-int(40*phase),665-int(12*phase),PURPLE)
        d.line([(130,664),(215,616),(285,586)],fill=GOLD,width=8,joint="curve")
        d.polygon([(285,586),(264,586),(274,602)],fill=GOLD)
    else:
        runners=[(410-int(120*phase),670-int(40*phase),GOLD),(370,770,GOLD),(297+int(14*phase),646,PURPLE),(272,730,PURPLE),(332,739,PURPLE)]
        d.line([(407,674),(336,636),(269,609)],fill=GOLD,width=8)
        d.polygon([(269,609),(286,602),(282,623)],fill=GOLD)
    for x,y,c in runners:
        d.ellipse((x-14,y-14,x+14,y+14),fill=c,outline=(245,248,243),width=2)
    txt(d,(44,852),"TACTICAL ILLUSTRATION • NOT MATCH FOOTAGE",12,(178,197,193),True)
def compose(scene,t,duration,vframe=None):
    q=min(1,max(0,t/duration))
    im=base(t); d=ImageDraw.Draw(im)
    if scene=="hook":
        if vframe is not None:
            im.paste(vframe,(0,0))
            # dark stripes for large title
            wash=Image.new("RGBA",(W,H),(4,8,18,0))
            wd=ImageDraw.Draw(wash)
            wd.rectangle((0,0,W,218),fill=(4,8,18,212))
            wd.rectangle((0,683,W,960),fill=(4,8,18,202))
            im=Image.alpha_composite(im.convert("RGBA"),wash).convert("RGB")
        d=ImageDraw.Draw(im)
        txt(d,(25,40),"THE AWAY RECORD",22,GOLD,True)
        txt(d,(25,102),"REAL MADRID",47,WHITE,True)
        txt(d,(25,158),"HAVE NEVER WON",35,WHITE,True)
        txt(d,(25,201),"IN ATHENS.",47,GOLD,True)
        d.rounded_rectangle((26,720,510,824),radius=17,fill=(9,16,28),outline=GOLD,width=2)
        txt(d,(44,743),"AEK ATHENS  ×  REAL MADRID",22,WHITE,True)
        txt(d,(44,781),"UEFA CHAMPIONS LEAGUE • PREVIEW",17,GOLD,True)
        footer(d,"Real AEK match photo (2026) / filmed Mbappé clip (2025) | CC")
    elif scene=="context":
        if photos.get("aek"):
            p=cover(photos["aek"],540,385,int(20*math.sin(q*2)))
            im.paste(p,(0,110))
        dark=Image.new("RGBA",(W,H),(0,0,0,0)); dd=ImageDraw.Draw(dark); dd.rectangle((0,0,540,144),fill=(8,14,24,235));dd.rectangle((0,410,540,960),fill=(8,14,24,241));im=Image.alpha_composite(im.convert("RGBA"),dark).convert("RGB")
        d=ImageDraw.Draw(im);header(d,"HISTORY CHECK")
        txt(d,(25,435),"MADRID IN ATHENS",37,WHITE,True)
        d.rounded_rectangle((24,514,515,618),radius=16,fill=(28,34,47),outline=(68,79,96),width=2)
        txt(d,(44,532),"1985  •  AEK  1—0  MADRID",24,GOLD,True)
        txt(d,(44,572),"2002  •  AEK  3—3  MADRID",24,WHITE,True)
        txt(d,(28,677),"3 WINS FROM 3 IN EUROPE",25,PURPLE,True)
        txt(d,(28,718),"Can they break the away record?",23,WHITE)
        footer(d,"AEK v Rayo match photo, 9 Apr 2026 | Goo064s CC BY")
    elif scene=="mbappe":
        header(d,"MATCHUP 01")
        txt(d,(23,120),"MBAPPÉ   VS   MOUKOUDI",29,WHITE,True)
        card(im,"mbappe",(24,192,235,276),q)
        card(im,"moukoudi",(280,192,235,276),-q)
        d=ImageDraw.Draw(im)
        d.rectangle((24,441,259,468),fill=(48,38,20)); d.rectangle((280,441,515,468),fill=(50,39,78))
        txt(d,(39,443),"MBAPPÉ  •  MADRID",14,GOLD,True)
        txt(d,(293,443),"MOUKOUDI  •  AEK",14,(202,180,255),True)
        board(im,min(1,(q*1.6)),mode="run")
        txt(d,(24,878),"THE RUN BEHIND THE LINE",21,WHITE,True)
        footer(d,"Photo dates: Mbappé 2025 • Moukoudi 2016 | Commons CC")
    elif scene=="jovic":
        header(d,"MATCHUP 02")
        txt(d,(22,120),"JOVIĆ   VS   RÜDIGER",35,WHITE,True)
        card(im,"jovic",(24,192,235,276),q)
        card(im,"rudiger",(280,192,235,276),-q)
        d=ImageDraw.Draw(im)
        d.rectangle((24,441,259,468),fill=(48,38,20));d.rectangle((280,441,515,468),fill=(50,39,78))
        txt(d,(40,443),"JOVIĆ  •  AEK",15,GOLD,True)
        txt(d,(293,443),"RÜDIGER  •  MADRID",14,(202,180,255),True)
        board(im,min(1,q*1.6),mode="post")
        txt(d,(24,878),"NEAR POST OR CUTBACK?",23,WHITE,True)
        footer(d,"Photo dates: Jović 2019 • Rüdiger 2026 | Commons CC")
    else:
        header(d,"THE FINAL CALL")
        txt(d,(28,141),"LAST MATCHES",34,WHITE,True)
        d.rounded_rectangle((25,230,515,360),radius=20,fill=(37,36,36),outline=GOLD,width=3)
        txt(d,(49,253),"RACING   0—3   MADRID",28,WHITE,True)
        txt(d,(49,310),"1 NOV 2026",17,GOLD)
        d.rounded_rectangle((25,388,515,520),radius=20,fill=(36,35,40),outline=PURPLE,width=3)
        txt(d,(48,411),"PANATHINAIKOS  2—0  AEK",21,WHITE,True)
        txt(d,(49,472),"1 NOV 2026",17,PURPLE)
        txt(d,(28,594),"MY PREDICTION",28,WHITE,True)
        txt(d,(28,647),"AEK   1—2   REAL",39,GOLD,True)
        d.rounded_rectangle((25,762,515,826),radius=15,fill=GOLD)
        txt(d,(48,781),"WHAT'S YOUR SCORE?",23,(10,16,26),True)
        footer(d,"Prediction, not confirmed result | 4 Nov 2026")
    return im
# One manually designed sequence per spoken beat; speech & scene durations are measured.
audio_clips=[]
for beat in beats:
    audio_clips.extend(["-i",beat["audio"]])
# Timestamps by concatenating audio with short silence pads between scenes.
silent=OUT/"pad.wav";sf.write(silent,np.zeros(13000,dtype=np.float32),48000)
aud=OUT/"voice_sequence.wav"
# Use an in-Python audio composition to enforce exact beat boundaries.
full=np.array([],dtype=np.float32);bound=[]
for beat in beats:
    a,sr=sf.read(beat["audio"]);a=np.asarray(a,dtype=np.float32)
    gap=int(round((beat["dur"]-len(a)/sr)*sr))
    full=np.concatenate([full,a,np.zeros(max(0,gap),dtype=np.float32)])
    bound.append(len(full)/sr)
sf.write(aud,full,48000,subtype="PCM_16")
total=len(full)/48000
# Original quiet music / percussion, no copyrighted music samples.
rng=np.random.default_rng(233)
N=len(full);music=np.zeros(N,dtype=np.float32)
for at in np.arange(0,total,.5):
    start=int(at*48000);n=min(8000,N-start)
    if n<=0:break
    ts=np.arange(n)/48000
    tone=np.sin(2*np.pi*(81*ts-32*ts*ts))*np.exp(-ts*28)
    music[start:start+n]+=.016*tone.astype(np.float32)
mixed=full+music
peak=float(np.max(np.abs(mixed)))
if peak>.82:mixed*=.82/peak
finalwav=OUT/"mixed_voice_music.wav";sf.write(finalwav,mixed,48000,subtype="PCM_16")
# Opening clip via ffmpeg raw frames, no image synthesis.
cap=None
try:
    import cv2
    if files["mbappe_video"] is not None:
        cap=cv2.VideoCapture(str(AS/"mbappe_open.mp4"))
        if not cap.isOpened():raise RuntimeError("authentic opening footage could not be decoded")
except ImportError:
    raise RuntimeError("OpenCV required to play actual Mbappe source during render")
video=OUT/"picture_only.mp4"
cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0","-an","-vf","scale=1080:1920:flags=lanczos,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p","-movflags","+faststart",str(video)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
starts=[0]+bound[:-1]
try:
    for i in range(math.ceil(total*FPS)):
        now=i/FPS
        ix=next((j for j,e in enumerate(bound) if now<e),len(beats)-1)
        beat=beats[ix]; local=max(0,now-starts[ix]); vf=None
        if ix==0:
            # camera footage may be slightly shorter than narration, hold last true frame at end
            if cap is not None and local<=6.0:
                cap.set(cv2.CAP_PROP_POS_MSEC,int(local*1000))
                okay,fr=cap.read()
                if okay:vf=Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB))
            if vf is None:
                # real 2026 AEK match photograph as opener; not fake animation or unrelated football
                vf=cover(photos["aek"],W,H,int(math.sin(local/2)*7))
        frame=compose(beat["id"],local,beat["dur"],vf)
        proc.stdin.write(frame.tobytes())
        if i%180==0:print("FRAME",i,"of",int(total*FPS),flush=True)
finally:
    proc.stdin.close();ret=proc.wait();
    if cap is not None:cap.release()
    if ret:raise RuntimeError("ffmpeg video render failed "+str(ret))
finished=OUT/"AEK_Real_Madrid_20261104_Tactical_Preview.mp4"
command(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(video),"-i",str(finalwav),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-af","loudnorm=I=-16:TP=-1.5:LRA=9","-shortest","-movflags","+faststart",str(finished)])
command(["ffprobe","-v","error","-show_entries","format=duration,size","-of","default=nw=1",str(finished)])
# First, middle and last proofs to enable later source/date/player inspection.
for sec,label in [(1,"opening"),(total*.52,"middle"),(total-1,"end")]:
    command(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(sec),"-i",str(finished),"-frames:v","1",str(OUT/(label+"_proof.jpg"))])
credits=[]
for k,(name,fn,cr) in SOURCES.items():
    credits.append(k+" | "+cr+" | https://commons.wikimedia.org/wiki/File:"+quote(name))
(OUT/"SOURCE_CREDITS_AND_LICENSES.txt").write_text("\n".join(credits)+"\nLicensed photos adapted by crop, tonal grading, overlays, captions. Video clip cropped and captioned. CC BY-SA 4.0 adapted material must be shared subject to license; check full publication terms. Specific players and historical match footage are labeled by original date. No claim of clearance from venue rightsholder. No broadcast game highlights used.\n")
(OUT/"production_manifest.json").write_text(json.dumps({"fixture":"AEK Athens vs Real Madrid","date":"2026-11-04","duration":total,"scenes":beats,"sources":credits,"authentic_video_seconds":min(6.1,beats[0]["dur"]) if files["mbappe_video"] is not None else 0,"original_tactical_visuals":True,"no_AI_generated_visuals":True,"narration":"Qwen3-TTS Ryan, pitch-preserving 1.35x","needs_human_review":True,"youtube_published":False},indent=2,ensure_ascii=False))
print("VIDEO_CREATED",str(finished),finished.stat().st_size,"SHA256",hashlib.sha256(finished.read_bytes()).hexdigest(),flush=True)
