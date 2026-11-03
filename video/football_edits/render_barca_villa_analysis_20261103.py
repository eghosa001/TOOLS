#!/usr/bin/env python3
"""Real-camera Barcelona–Aston Villa critical commentary short; REVIEW ONLY.

Inputs must be exact documented football source files and an actual recorded Qwen WAV.
Graphics are original plain typography. Source credit is visible on each clip,
with full link and underlying-footage caveat in description. Never auto-publish.
"""
from __future__ import annotations
import json,subprocess,hashlib,math,wave
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np

ROOT=Path("football_edit_source/barca_villa")
VOICE_ROOT=Path("football_edit_output/qwen_barca_villa_20261103")
OUT=Path("football_edit_output/barca_villa_transformative")
PART=OUT/"parts"
PART.mkdir(parents=True,exist_ok=True)
W,H,FPS=1080,1920,30
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"
SMALL="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def ff(args,timeout=250):
    print("FFMPEG",str(args)[:220],flush=True)
    subprocess.run(args,check=True,timeout=timeout)
def probe(path):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)]))
def text(d,x,y,value,size,color=(245,245,249),bold=True,maxw=970):
    font=FONT if bold else SMALL
    while size>18:
        ft=ImageFont.truetype(font,size)
        if d.textbbox((0,0),value,font=ft)[2] <= maxw:break
        size-=2
    d.text((x,y),value,font=ft,fill=color,stroke_width=1 if bold else 0,stroke_fill=(8,12,21))
def overlay_card(key,headline,sub,credit):
    im=Image.new("RGBA",(W,H),(0,0,0,0))
    d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((34,76,1046,170),radius=20,fill=(6,10,19,220))
    text(d,58,94,"BARCELONA  ×  ASTON VILLA",39,(244,211,122))
    d.rounded_rectangle((36,265,1044,402),radius=20,fill=(3,10,24,210))
    text(d,56,276,headline,57,maxw=974)
    text(d,58,355,sub,25,(217,225,244),bold=False)
    d.rounded_rectangle((24,1587,1056,1770),radius=22,fill=(8,12,24,228))
    text(d,50,1611,credit,27,(237,218,157),maxw=970)
    text(d,51,1660,"Original tactical analysis  |  Qwen Ryan narration",22,(227,234,247),bold=False)
    text(d,51,1698,"Sources & underlying rights in description",21,(200,209,222),bold=False)
    fn=PART/f"graphic_{key}.png"
    im.save(fn)
    return fn

def source(key):
    files=[p for p in ROOT.glob(key+".*") if p.suffix.lower() in {".mp4",".webm",".mkv",".ogv"}]
    if len(files)!=1:raise RuntimeError(f"{key}: expected ONE original actual recorded match video, got {files}")
    f=files[0]
    info=probe(f)
    v=next((s for s in info["streams"] if s["codec_type"]=="video"),None)
    if not v:raise RuntimeError(f"{key}: source not a video")
    dur=float(info["format"]["duration"])
    if dur<3.5:raise RuntimeError(f"{key}: source too short to explain tactics ({dur:.2f}s)")
    if int(v.get("width",0))<580 or int(v.get("height",0))<310:
        raise RuntimeError(f"{key}: source too low-quality for short form")
    print("VIDEO_ACTUAL_ORIGINAL",key,f,dur,v.get("width"),v.get("height"),flush=True)
    return f,dur,v

def still_intro(seconds):
    im=Image.new("RGB",(W,H),(9,17,29))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((43,130,1037,220),radius=20,fill=(23,39,57))
    text(d,69,148,"A RIVALRY RETURNS  /  EUROPE",39,(244,205,108))
    text(d,63,330,"1982 SUPER CUP",77)
    text(d,65,485,"BARCELONA  1–0  VILLA",57)
    text(d,65,570,"VILLA  3–0  BARCELONA",55)
    text(d,64,685,"Villa won 3–1 on aggregate",43,(243,207,123))
    d.rounded_rectangle((47,815,1034,1035),radius=20,fill=(28,45,64))
    text(d,72,858,"26 JANUARY 1983",48)
    text(d,72,938,"The last competitive meeting",30,(217,231,243),bold=False)
    text(d,52,1540,"H2H facts: UEFA Super Cup archive",29,(236,203,116))
    text(d,52,1600,"ARCHIVAL SCORE GRAPHIC  •  NOT MATCH VIDEO",24,(213,226,239))
    path=PART/"historical_scorecard.png";im.save(path)
    dest=PART/"clip_00_h2h.mp4"
    ff(["ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1","-framerate",str(FPS),
        "-i",str(path),"-t",f"{seconds:.3f}","-vf","format=yuv420p","-c:v","libx264",
        "-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-an",str(dest)])
    return dest

def moving_segment(key,file,seconds,headline,sub,credit,i):
    card=overlay_card(key,headline,sub,credit)
    dest=PART/f"clip_{i:02d}_{key}.mp4"
    vf=(
       "[0:v]setpts=PTS-STARTPTS,fps=30,split=2[back][front];"
       "[back]scale=540:960:force_original_aspect_ratio=increase,"
       "crop=540:960,boxblur=18:2,scale=1080:1920,eq=brightness=-0.21:saturation=0.72[bg];"
       "[front]scale=1000:562:force_original_aspect_ratio=decrease,"
       "pad=1000:562:(ow-iw)/2:(oh-ih)/2:color=black,"
       "eq=contrast=1.07:saturation=1.12[fg];"
       "[bg][fg]overlay=(W-w)/2:681[scene];"
       "[1:v]format=rgba[graphic];"
       "[scene][graphic]overlay=0:0:shortest=1,format=yuv420p[v]"
    )
    ff(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(file),"-loop","1",
        "-i",str(card),"-filter_complex",vf,"-map","[v]","-t",f"{seconds:.3f}",
        "-r",str(FPS),"-an","-c:v","libx264","-crf","22","-preset","veryfast",
        "-pix_fmt","yuv420p",str(dest)],timeout=390)
    return dest

def original_music(seconds,dest):
    # Soft royalty-free ORIGINAL percussion: not a pre-existing song.
    sr=48000
    n=round(seconds*sr)
    signal=np.zeros(n,dtype=np.float32)
    rng=np.random.default_rng(93)
    beat=60/117
    for i in range(int(seconds/beat)+1):
        at=round(i*beat*sr)
        if at>=n:break
        t=np.arange(min(round(.16*sr),n-at),dtype=np.float32)/sr
        signal[at:at+len(t)]+=.028*np.sin(2*np.pi*(48*t+23*t*np.exp(-25*t)))*np.exp(-t*23)
        if i%2:
            t2=np.arange(min(round(.08*sr),n-at),dtype=np.float32)/sr
            signal[at:at+len(t2)]+=.008*rng.standard_normal(t2.size)*np.exp(-t2*50)
    k=min(n,int(.35*sr))
    signal[:k]*=np.linspace(0,1,k)
    signal[-k:]*=np.linspace(1,0,k)
    with wave.open(str(dest),"wb") as f:
        f.setframerate(sr);f.setnchannels(1);f.setsampwidth(2)
        f.writeframes((np.clip(signal,-.8,.8)*32767).astype(np.int16).tobytes())

def main():
    voice=VOICE_ROOT/"Barcelona_AstonVilla_H2H_Qwen3_Ryan_20261103.wav"
    evidence=VOICE_ROOT/"qwen_voice_evidence.json"
    if not voice.is_file() or not evidence.is_file():
        raise RuntimeError("Missing original actual Qwen voice artifact; no fallback")
    q=json.loads(evidence.read_text())
    if q.get("model")!="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice" or q.get("speaker")!="Ryan" or not q.get("no_fallback"):
        raise RuntimeError("Qwen original voice evidence inconsistent")
    duration=float(probe(voice)["format"]["duration"])/1.10+1.1
    if not 30<=duration<=65:raise RuntimeError("Unexpected original voice length")
    b1,d1,_=source("barca_raphinha_oct31")
    b2,d2,_=source("barca_yamal_oct31")
    b3,d3,_=source("villa_bournemouth_2026")
    intro=4.5
    s1=min(d1-.35,10.5)
    s2=min(d2-.35,10.5)
    s3=duration-intro-s1-s2
    if s3>d3-.35:
        # Allocate more real Barcelona action if this is available, not repeat clips.
        deficit=s3-(d3-.35)
        extra1=min(deficit,max(0,d1-.35-s1));s1+=extra1;deficit-=extra1
        extra2=min(deficit,max(0,d2-.35-s2));s2+=extra2;deficit-=extra2
        s3=duration-intro-s1-s2
    if s1<4.0 or s2<4.0 or s3<10 or s3>d3-.3:
        raise RuntimeError(f"Insufficient unbroken relevant real footage {s1:.2f}, {s2:.2f}, {s3:.2f}; no loop or unrelated fallback")
    segments=[still_intro(intro)]
    segments.append(moving_segment("raphinha",b1,s1,"THE 15-PASS OPENING","Actual Barcelona 6–1 Alavés  /  31 OCT 2026",
                   "Footage: Barça v Alavés (via Reddit video)",1))
    segments.append(moving_segment("yamal",b2,s2,"YAMAL FINDS THE SPACE","Actual Barcelona 6–1 Alavés  /  31 OCT 2026",
                   "Footage: Barça v Alavés (via Reddit video)",2))
    segments.append(moving_segment("villa",b3,s3,"VILLA'S TRANSITION RISK","Actual Bournemouth v Aston Villa  /  08 FEB 2026",
                   "Footage: Bournemouth–Villa (Commons upload)",3))
    concat=PART/"concat.txt"
    concat.write_text("".join("file '"+str(p.resolve())+"'\n" for p in segments))
    silent=PART/"real_film_only.mp4"
    ff(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(concat),
        "-c","copy",str(silent)])
    music=PART/"original_beat.wav"
    original_music(duration,music)
    result=OUT/"Barcelona_Villa_H2H_2026_Original_Tactical_Analysis_Qwen_REVIEW.mp4"
    af="[0:a]atempo=1.10,volume=1.24[voice];[1:a]volume=0.23[beat];[voice][beat]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.94[mix]"
    ff(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(voice),"-i",str(music),"-i",str(silent),
        "-filter_complex",af,"-map","2:v:0","-map","[mix]","-t",f"{duration:.3f}",
        "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(result)])
    data=probe(result)
    video=next(s for s in data["streams"] if s["codec_type"]=="video")
    if (video["width"],video["height"]) != (W,H):raise RuntimeError("Incorrect final dimensions")
    if float(data["format"]["duration"])<37:raise RuntimeError("Source/cut is unexpectedly short")
    real_share=(s1+s2+s3)/duration
    if real_share<.80:raise RuntimeError(f"Insufficient filmed match-action percentage: {real_share}")
    for name,sec in [("opening",1.5),("barcelona",intro+s1/2),("villa",intro+s1+s2+s3/2)]:
        proof=OUT/f"proof_{name}.jpg"
        ff(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",f"{sec:.2f}","-i",str(result),
            "-frames:v","1",str(proof)])
    description=(
      "BARCELONA vs ASTON VILLA | History, recent form and transition analysis\n\n"
      "Original football tactical analysis and original Qwen3 Ryan narration.\n"
      "Historical facts: Aston Villa won the 1982 UEFA Super Cup tie 3–1 on aggregate after a 3–0 second-leg win in January 1983.\n"
      "Current form: Barcelona 6–1 Alavés (31 Oct 2026), Villa 1–1 Fulham (31 Oct 2026).\n"
      "Footage shown is explicitly labelled: Barcelona vs Alavés (Oct 2026) and Bournemouth vs Aston Villa (Feb 2026). "
      "No clips of the 1983 tie or Villa vs Fulham are depicted as such.\n\n"
      "FOOTAGE SOURCES / CREDITS:\n"
      "Barcelona–Alavés goal footage (broadcast mirror; original broadcaster/competition rights reserved):\n"
      "https://v.redd.it/qqr0qhtc1vyh1\nhttps://v.redd.it/aibhpkgffvyh1\n"
      "Bournemouth–Aston Villa 2026 match video: AFC Bournemouth original video, Commons upload (CC BY 4.0 marked; original broadcast rights not independently verified):\n"
      "https://commons.wikimedia.org/wiki/File:Rayan_scores_his_first_goal_for_AFC_Bournemouth_against_Aston_Villa_in_the_2025-26_Premier_League.webm\n"
      "Match/history references: https://www.uefa.com/uefasupercup/history/1982/\n"
      "https://www.fcbarcelona.com/en/football/first-team/news/4602177/fc-barcelona-6-1-alaves-thats-more-like-it\n"
      "https://www.avfc.co.uk/news/2026/october/31/report-aston-villa-1-1-fulham/\n\n"
      "Underlying recordings remain owned by their respective rights holders. "
      "Credits are not a licence. Excerpts used for criticism and analysis; "
      "copyright exception/permission and YouTube review are not guaranteed.\n"
    )
    (OUT/"youtube_description_and_footage_credits.md").write_text(description)
    manifest={"status":"ACTUAL_VIDEO_RENDER_COMPLETE_EDITORIAL_AND_COPYRIGHT_REVIEW_REQUIRED",
      "source_video":[{"name":"Barcelona Alaves 2026 Raphinha","url":"https://v.redd.it/qqr0qhtc1vyh1","seconds":round(s1,3),"copyright_exception_unverified":True},
                      {"name":"Barcelona Alaves 2026 Yamal","url":"https://v.redd.it/aibhpkgffvyh1","seconds":round(s2,3),"copyright_exception_unverified":True},
                      {"name":"Bournemouth Aston Villa 2026","url":"https://commons.wikimedia.org/wiki/File:Rayan_scores_his_first_goal_for_AFC_Bournemouth_against_Aston_Villa_in_the_2025-26_Premier_League.webm","seconds":round(s3,3),"copyright_exception_unverified":True}],
      "real_motion_share":round(real_share,4),"real_match_action_share":round(real_share,4),
      "original_graphic_seconds":intro,"duration_seconds":round(duration,2),
      "source_frames_are_real":True,"ai_generated_images_or_video":False,
      "narration":{"model":q["model"],"voice":"Ryan","duration":round(float(q["duration_sec"]),2),"playback_rate":1.1},
      "file":{"name":result.name,"size_bytes":result.stat().st_size,"sha256":hashlib.sha256(result.read_bytes()).hexdigest()},
      "youtube_uploaded":False,"human_audiovisual_review":"required","copyright_clearance":"not_guaranteed"}
    (OUT/"editorial_source_and_video_qa.json").write_text(json.dumps(manifest,indent=2))
    print("REAL_CAMERA_VIDEO_RENDER_COMPLETE",result,result.stat().st_size,"MOVING_SHARE",real_share,flush=True)
if __name__=="__main__":main()
