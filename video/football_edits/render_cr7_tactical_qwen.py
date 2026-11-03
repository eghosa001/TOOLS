#!/usr/bin/env python3
"""Manually selected Cristiano Ronaldo movement analysis Short with actual Qwen voice.

Only authentic Real Madrid CC BY 3.0 archival film. No artificial football video,
no keyword-picked clips. All source timecodes chosen by review of contact sheets.
Export is an editorial REVIEW candidate pending full watched/listened sign-off.
"""
from __future__ import annotations
import hashlib,json,math,os,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

SRC=Path("football_edit_source/ronaldo_48_goals_2014_15.ogv")
VOICE=Path("football_edit_output/qwen/Qwen3_TTS_Ryan_Ronaldo_Original_Analysis.wav")
VOICE_EVIDENCE=Path("football_edit_output/qwen/qwen_voice_evidence.json")
OUT=Path("football_edit_output/cr7_tactical_qwen")
OUT.mkdir(parents=True,exist_ok=True)
SEG_DIR=OUT/"segments"
SEG_DIR.mkdir(exist_ok=True)
TITLE="THE GOAL STARTS BEFORE THE SHOT"
SHORT_NAME="CR7_Before_The_Shot_Real_Footage_Qwen3_1080x1920.mp4"
COMMONS="https://commons.wikimedia.org/wiki/File:All_48_goals_of_Cristiano_Ronaldo,_in_35_league_matches_for_Real_Madrid_(2014-15).ogv"
EXPECTED_SHA1="6a75c744421acb76b827441fd9967d778cc19a4a"
# Timestamps are verified to show consecutive attacking footage, finish, and
# aftermath in the real source's contact sheets. Not claimed as all 48 goals.
SHOTS=[
 {"start":28.25,"end":33.70,"speed":1.0,"heading":"01   /   THE OPENING",
  "title":"FIND THE SPACE","sub":"The chance begins long before the strike.",
  "editorial_reason":"Real Madrid advance into an opening, finish the goal, and the original broadcast shows Ronaldo's reaction."},
 {"start":46.15,"end":51.75,"speed":1.0,"heading":"02   /   THE TIMING",
  "title":"A STEP AHEAD","sub":"Watch what happens before the finish.",
  "editorial_reason":"A fresh attack builds to a finish with celebration; the segment retains the entire decisive move."},
 {"start":131.45,"end":138.95,"speed":1.0,"heading":"03   /   THE FINISH",
  "title":"THE MOMENT ARRIVES","sub":"The opening lasts only a moment.",
  "editorial_reason":"Source archive shows approach, penalty-area action, goal and Ronaldo's resulting reaction."},
 {"start":46.15,"end":51.35,"speed":0.80,"heading":"REPLAY   /   LOOK AGAIN",
  "title":"BEFORE THE SHOT","sub":"Movement creates the chance. The finish completes it.",
  "editorial_reason":"Purposeful replay of the earlier attack at 80 percent speed to re-examine the run rather than add arbitrary footage."}
]
FONTPATH=Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")
FONTSMALL=Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
if not FONTPATH.exists():raise RuntimeError("Install font DejaVu")

def run(cmd,timeout=420):
    print("EXEC", " ".join(map(str,cmd))[:350],flush=True)
    subprocess.run([str(x) for x in cmd],check=True,timeout=timeout)

def probe(path):
    return json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(path)]))

def font(sz,bold=True):
    return ImageFont.truetype(str(FONTPATH if bold else FONTSMALL),sz)

def textfit(d,s,x,y,max_w,size,col):
    while size>=20:
        f=font(size)
        if d.textbbox((0,0),s,font=f)[2]<=max_w:break
        size-=2
    d.text((x,y),s,font=font(size),fill=col)

def overlay_card(shot,i):
    im=Image.new("RGBA",(1080,1920),(0,0,0,0))
    d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((45,70,1035,120),radius=8,fill=(6,12,20,175))
    d.text((66,83),"CR7   /   THE ART OF THE FINISH",fill=(242,220,165,245),font=font(24))
    d.line((50,145,1030,145),fill=(225,190,89,220),width=3)
    textfit(d,shot["title"],53,277,988,79,(255,255,255,255))
    d.text((57,408),shot["heading"],fill=(243,194,80,245),font=font(37))
    d.text((58,493),"THE PLAY BEFORE THE PAYOFF",fill=(218,228,244,215),font=font(26,False))
    d.rounded_rectangle((27,626,1053,1244),radius=14,outline=(236,198,90,242),width=5)
    d.rounded_rectangle((46,1370,1034,1525),radius=20,fill=(6,12,24,220),outline=(225,190,89,130),width=2)
    textfit(d,shot["sub"],69,1418,945,35,(250,250,252,255))
    # Progress indicators are new editorial graphics, not manufactured football visuals.
    for k in range(4):
        x0=60+k*246
        d.rounded_rectangle((x0,1600,x0+222,1613),radius=6,
                            fill=(246,200,79,255) if k<=i else (233,236,243,70))
    d.text((57,1723),"2014 / 15    •    LICENSED REAL MATCH FOOTAGE",fill=(244,218,145,230),font=font(22))
    d.text((57,1771),"ORIGINAL NARRATIVE + QWEN3-TTS ENGLISH RYAN",fill=(245,247,250,170),font=font(20,False))
    im.save(SEG_DIR/f"card_{i:02}.png",optimize=True)
    return SEG_DIR/f"card_{i:02}.png"

def beats(seconds,path):
    """Short original quiet syncopated percussion and bass, no outside music."""
    sr=48000
    n=int((seconds+.2)*sr)
    sound=np.zeros(n,dtype=np.float32)
    rng=np.random.default_rng(26015)
    bpm=123
    beat=60.0/bpm
    for i in range(int(seconds/beat)+1):
        start=int(i*beat*sr)
        if start>=n:break
        t=np.arange(min(int(.30*sr),n-start),dtype=np.float32)/sr
        kick=(.12*np.sin(2*np.pi*(55*t+38*t*np.exp(-15*t)))*np.exp(-t*19))
        sound[start:start+len(t)]+=kick
        if i%4 in (1,3):
            q=np.arange(min(int(.13*sr),n-start),dtype=np.float32)/sr
            sound[start:start+len(q)]+=.032*rng.standard_normal(q.size)*np.exp(-q*30)
    for i in range(int(seconds/(beat/2))+1):
        start=int(i*beat/2*sr)
        if start>=n:break
        t=np.arange(min(int(.05*sr),n-start),dtype=np.float32)/sr
        sound[start:start+len(t)]+=.015*rng.standard_normal(t.size)*np.exp(-90*t)
    for i in range(int(seconds/(beat*4))+1):
        start=int(i*beat*4*sr)
        if start>=n:break
        t=np.arange(min(int(beat*4*sr),n-start),dtype=np.float32)/sr
        hz=[65.4,55.,49.,61.7][i%4]
        sound[start:start+len(t)]+=.035*np.sin(2*np.pi*hz*t)*np.minimum(1,t*2)*np.exp(-.8*t)
    count=int(.26*sr)
    sound[:count]*=np.linspace(0,1,count,dtype=np.float32)
    sound[-count:]*=np.linspace(1,0,count,dtype=np.float32)
    with wave.open(str(path),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((np.clip(sound,-.9,.9)*32767).astype(np.int16).tobytes())

def main():
    if not SRC.is_file() or not VOICE.is_file() or not VOICE_EVIDENCE.is_file():
        raise RuntimeError("Original licensed footage and genuine Qwen WAV/evidence required; no substitutions.")
    source_sha1=hashlib.sha1(SRC.read_bytes()).hexdigest()
    if source_sha1!=EXPECTED_SHA1:raise RuntimeError("Original match video hash mismatch")
    info=json.loads(VOICE_EVIDENCE.read_text())
    if info.get("voice_model")!="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice" or info.get("speaker")!="Ryan" or not info.get("no_fallback"):
        raise RuntimeError("No real Qwen voice evidence; refuse synthetic substitute")
    if info["text"].count("Ronaldo")!=1:raise RuntimeError("Unexpected original narration text")
    voice_duration=float(probe(VOICE)["format"]["duration"])
    duration=sum((shot["end"]-shot["start"])/shot["speed"] for shot in SHOTS)
    if voice_duration>duration-.15:
        raise RuntimeError(f"Qwen narration {voice_duration:.2f}s does not fit {duration:.2f}s edit; rewrite or extend, do NOT truncate")
    if len(SHOTS)!=4:raise RuntimeError("Unexpected storyboard")
    all_segments=[]
    for i,shot in enumerate(SHOTS):
        card=overlay_card(shot,i)
        a,b,s=shot["start"],shot["end"],shot["speed"]
        clip_seconds=b-a
        segment=SEG_DIR/f"segment_{i:02}.mp4"
        vf=(
            f"[0:v]setpts=(PTS-STARTPTS)/{s},fps=30,split=2[back][front];"
            "[back]scale=560:1000:force_original_aspect_ratio=increase:flags=bicubic,"
            "crop=560:1000,boxblur=20:1,scale=1080:1920,eq=brightness=-0.20:saturation=0.60[bg];"
            "[front]scale=1024:576:flags=lanczos,eq=contrast=1.05:saturation=1.09,"
            "unsharp=3:3:0.25:3:3:0[fg];"
            "[bg][fg]overlay=28:647,format=yuv420p[scene];"
            "[1:v]format=rgba[graphic];"
            "[scene][graphic]overlay=0:0:shortest=1,format=yuv420p[v];"
            f"[0:a]atempo={s},aresample=48000,volume=0.65[a]"
        )
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-ss",str(a),"-t",str(clip_seconds),"-i",SRC,
             "-loop","1","-i",card,
             "-filter_complex",vf,"-map","[v]","-map","[a]",
             "-t",f"{clip_seconds/s:.3f}",
             "-c:v","libx264","-preset","veryfast","-crf","22","-r","30",
             "-c:a","aac","-b:a","128k","-ar","48000",
             "-pix_fmt","yuv420p",segment],timeout=600)
        all_segments.append(segment)
        print("GOAL_SEQUENCE",i+1,f"{a}-{b}",f"speed={s}",flush=True)
    manifest=SEG_DIR/"concat.txt"
    manifest.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in all_segments))
    base=SEG_DIR/"original_broadcast_with_cuts.mp4"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-f","concat","-safe","0","-i",manifest,"-c","copy",base])
    actual=float(probe(base)["format"]["duration"])
    music=SEG_DIR/"original_cinematic_beat.wav"
    beats(actual,music)
    dest=OUT/SHORT_NAME
    af=("[0:a]volume=0.16[ambience];"
        "[1:a]aresample=48000,atempo=1.10,volume=1.25,apad=whole_dur=40[voice];"
        "[2:a]aresample=48000,volume=0.40[beat];"
        "[ambience][voice][beat]amix=inputs=3:duration=first:normalize=0,"
        "alimiter=limit=0.94[a]")
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-i",base,"-i",VOICE,"-i",music,
         "-filter_complex",af,"-map","0:v:0","-map","[a]",
         "-c:v","copy","-c:a","aac","-b:a","192k",
         "-movflags","+faststart","-t",f"{actual:.2f}",
         "-metadata","comment=Real Madrid CC BY 3.0 match footage, original analysis, Qwen3 TTS",
         dest],timeout=240)
    finished=probe(dest)
    video=next(s for s in finished["streams"] if s["codec_type"]=="video")
    audio=next(s for s in finished["streams"] if s["codec_type"]=="audio")
    if (video["width"],video["height"])!=(1080,1920):raise RuntimeError("Incorrect output dimension")
    if not (24<=float(finished["format"]["duration"])<=29):raise RuntimeError("Invalid final edit runtime")
    rights=(
        "# CR7: The Goal Begins Before The Shot — ORIGINAL EDIT / REVIEW ONLY\n\n"
        "Source footage: Real Madrid, 'All 48 goals of Cristiano Ronaldo in 35 league matches for Real Madrid (2014–15)'.\n"
        f"Wikimedia Commons source: {COMMONS}\n"
        "Footage licence: CC BY 3.0 https://creativecommons.org/licenses/by/3.0/\n"
        "Changes: editorially selected complete attack sequences, a purposeful slow-motion replay, "
        "original analysis and structure, motion graphics, regrading/reframing, altered background sound and original beat.\n"
        "Voice: real Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice English Ryan, newly authored original script; speech-generated audio only.\n"
        "Source metadata and rights page say commercial adaptation is permitted WITH attribution; "
        "YouTube reused-content review and Content ID are separate.\n\n"
        "This is NOT a compilation of all 48 goals. Four segments, three distinct goals and one replay. "
        "Awaiting full human audiovisual editorial sign-off before any platform upload or monetization claim.\n"
    )
    (OUT/"rights_and_editorial_credits.md").write_text(rights)
    qa={
        "status":"TECHNICAL_RENDER_COMPLETE_EDITORIAL_REVIEW_PENDING",
        "source_sha1":source_sha1,"source_url":COMMONS,"source_licence":"CC BY 3.0; Real Madrid",
        "voice_model":info["voice_model"],"voice_speaker":"Ryan",
        "voice_duration_sec":voice_duration,"voice_playback_speed":1.10,"pitch_preserved":True,"source_shots":SHOTS,
        "duration":finished["format"]["duration"],"resolution":"1080x1920",
        "audio_codec":audio["codec_name"],
        "original_narration_text":info["text"],
        "footage_is_real":True,"ai_generated_football_footage":False,
        "goal_scene_editorial_approved":False,
        "youtube_published":False,"youtube_monetization_guaranteed":False
    }
    (OUT/"technical_and_editorial_qa.json").write_text(json.dumps(qa,indent=2))
    # First / middle / ending proofs for review; no claims of quality approval.
    for label,sec in [("opening",2.5),("middle",13),("closing",23)]:
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
             "-ss",str(sec),"-i",dest,"-frames:v","1",OUT/f"proof_{label}.jpg"])
    print("REAL_QWEN_FOOTBALL_EDIT_RENDERED",dest,dest.stat().st_size,flush=True)

if __name__=="__main__":main()
