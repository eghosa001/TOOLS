#!/usr/bin/env python3
"""Qwen 1.7B approved-voice narration and original freely reusable assets for broadcast-style AEK preview.
This action generates a review asset pack, not a posted finished video.
"""
import hashlib,io,json,os,subprocess
from pathlib import Path
from urllib.parse import quote
import requests,numpy as np,soundfile as sf,torch
from PIL import Image

OUT=Path("football_edit_output/aek_real_20261104_premium")
PHOTO=OUT/"assets";VOICE=OUT/"voice";PHOTO.mkdir(parents=True,exist_ok=True);VOICE.mkdir(parents=True,exist_ok=True)
SOURCES={
"mbappe_video":("Kylian_Mbappe_at_Real_Madrid's_UEFA_Champions_League_game_versus_Juventus_Turin_on_22_October_2025_(video).webm","mbappe_source.webm","SdHb, CC BY-SA 4.0, 22 Oct 2025"),
"mbappe":("Kylian_Mbappe_at_Real_Madrid's_game_versus_Juventus_Turin_on_22_October_2025.jpeg","mbappe.jpg","SdHb, CC BY-SA 4.0, 22 Oct 2025"),
"moukoudi":("Harold_Moukoudi_-_Lens_B_-_Le_Havre_B_(13-08-2016).jpg","moukoudi.jpg","Supporterhéninois, CC0, 13 Aug 2016"),
"jovic":("FC_RB_Salzburg_versus_Real_Madrid_(Testspiel,_7._August_2019)_17.jpg","jovic.jpg","Werner100359, CC BY-SA 4.0, 7 Aug 2019"),
"rudiger":("Antonio_Rudiger_Ecuador_v_Germany_25_June_2026-055_(cropped).jpg","rudiger.jpg","Bryan Berlin/WikiPortraits, CC BY-SA 4.0, 25 Jun 2026"),
"aek":("ConferenceRayoVallecanoyAEKAtenas9-4-26.jpg","aek.jpg","Goo064s, CC BY 4.0, 9 Apr 2026")
}
def grab(filename,local):
    md=hashlib.md5(filename.encode()).hexdigest()
    url="https://upload.wikimedia.org/wikipedia/commons/"+md[0]+"/"+md[:2]+"/"+quote(filename,safe="(),-._'!")
    urls=[url] if local.endswith(".webm") else ["https://wsrv.nl/?url="+quote(url.removeprefix("https://"),safe="")+"&w=1200&output=jpg","https://wsrv.nl/?url="+quote(url.removeprefix("https://"),safe="")+"&w=1400&output=jpg",url]
    last=None
    for u in urls:
        try:
            r=requests.get(u,timeout=70,headers={"User-Agent":"FootballEditorialProduction/1.0 (photo attribution)"})
            r.raise_for_status()
            if len(r.content)<8000:raise RuntimeError("short response")
            if local.endswith(".jpg"):Image.open(io.BytesIO(r.content)).verify()
            else:
                if r.content[:4]!=bytes([0x1a,0x45,0xdf,0xa3]):raise RuntimeError("not WEBM")
            (PHOTO/local).write_bytes(r.content)
            print("DOWNLOADED",local,len(r.content),flush=True);return True
        except Exception as e:
            last=e;print("TRY_FAILED",local,str(e)[:180],flush=True)
    if local=="mbappe_source.webm":
        print("OPTIONAL_VIDEO_NOT_AVAILABLE; do not manufacture footage",flush=True);return False
    # Rights-preserving backup: actual CC photos already embedded in our previous
    # same-fixture production, not a synthetic or substituted player's face.
    # GitHub's release hosts the exact film reviewed in the prior chat turn.
    source_video=PHOTO/"prior_review_source.mp4"
    try:
        if not source_video.exists():
            release="https://github.com/eghosa001/TOOLS/releases/download/aek-real-20261104-editor-preview/AEK_Real_Madrid_20261104_Tactical_Preview.mp4"
            old=requests.get(release,timeout=75)
            old.raise_for_status()
            if len(old.content)<3000000:raise RuntimeError("prior review not a video")
            source_video.write_bytes(old.content)
        cuts={
          "mbappe.jpg":(23,42,325,523,969),
          "moukoudi.jpg":(23,568,325,1057,969),
          "jovic.jpg":(33,42,325,523,969),
          "rudiger.jpg":(33,568,325,1057,969),
          "aek.jpg":(13,0,240,1080,1150)
        }
        sec,x1,y1,x2,y2=cuts[local]
        f=PHOTO/("backup_"+local)
        command=["ffmpeg","-v","error","-y","-ss",str(sec),"-i",str(source_video),"-frames:v","1",str(f)]
        import subprocess
        subprocess.run(command,check=True)
        shot=Image.open(f).convert("RGB").crop((x1,y1,x2,y2))
        if shot.size[0]<100:raise RuntimeError("previous photograph crop invalid")
        shot.save(PHOTO/local,quality=92)
        print("BACKUP_GENUINE_PHOTO_FROM_PREVIOUS_EDIT",local,flush=True)
        return True
    except Exception as backup_error:
        raise RuntimeError("Genuine photo unavailable "+local+" original:"+str(last)+" backup:"+str(backup_error))

retrieved={}
for key,(name,local,credit) in SOURCES.items():
    retrieved[key]=grab(name,local)
VOICE_SCRIPT=[
    ("hook","Real Madrid have never won away to AEK Athens. Tonight, they get another chance."),
    ("record","Two visits. No wins. They lost one nil in nineteen eighty-five, then drew three all in two thousand and two."),
    ("duel_mbappe","Watch Kylian Mbappé against Harold Moukoudi. A run behind the defensive line forces Moukoudi to turn. That opens space inside."),
    ("duel_jovic","And Luka Yovich against Antonio Rüdiger. The former Madrid striker attacks the near post, while Rüdiger must protect the cutback. Two decisions in one moment."),
    ("close","Madrid won three nil in their last league game. The Greek side lost two nil. My prediction? Real Madrid by two goals to one. What's yours?")
]
print("LOADING_USER_APPROVED_QWEN17",flush=True)
torch.set_num_threads(4);torch.set_num_interop_threads(2)
from qwen_tts import Qwen3TTSModel
MODEL="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
model=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
details=[]
INSTRUCT=("You are an articulate, relaxed professional football analyst recording for a television football preview. "
"Speak naturally, fluently and warmly at around 165 complete English words per minute before any slight tempo finishing. "
"Use connected speech, varied intonation and short, natural pauses rather than robotic announcement cadence. "
"Pronounce Real Madrid like Ray-al Ma-dreed; pronounce the Greek club AEK as a compact AH-ek, not three letter names. "
"Pronounce Yovich like YO-vitch and Rüdiger naturally in German; Moukoudi is a fluent single name, not syllable-by-syllable. "
"Keep the player and team names smooth, do not over-emphasize any syllables.")
for i,(key,words) in enumerate(VOICE_SCRIPT):
    print("VOICE_START",key,flush=True)
    result,sr=model.generate_custom_voice(text=words,speaker="Ryan",language="English",instruct=INSTRUCT)
    a=np.asarray(result[0],dtype=np.float32).flatten()
    if len(a)<sr*1.4 or not np.isfinite(a).all() or np.sqrt(np.mean(a*a))<.004:raise RuntimeError("invalid Qwen "+key)
    original=VOICE/f"{i:02d}_{key}_original.wav";sf.write(original,a,sr,subtype="PCM_16")
    target=VOICE/f"{i:02d}_{key}_approved_pace.wav"
    native_wpm=len(words.split())/(len(a)/sr)*60
    # Reproduce approved natural ~185 WPM where possible, never exceed 1.25x stretch.
    atempo=min(1.25,max(1.0,185/max(native_wpm,1)))
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(original),"-af",f"atempo={atempo:.4f},aresample=48000","-ar","48000","-ac","1",str(target)],check=True)
    b,sr2=sf.read(target);dur=len(b)/sr2
    rate=len(words.split())/dur*60
    # Human listening required; a slight under-target passage is not a hard technical failure.
    if rate<155:print("PACING_LISTEN_REVIEW_REQUIRED",key,round(rate,1),"wpm; natural phrase first",flush=True)
    if not (110<rate<260):raise RuntimeError(f"Qwen voice clearly unusable {key}:{rate:.1f} wpm")
    details.append({"key":key,"words":words,"audio":str(target),"seconds":round(dur,3),"native_wpm":round(native_wpm,1),"tempo":round(atempo,4),"wpm":round(rate,1)})
    print("VOICE_OK",key,"sec",round(dur,2),"wpm",round(rate,1),flush=True)
(OUT/"audio_manifest.json").write_text(json.dumps({"model":MODEL,"speaker":"Ryan","tempo":"per-beat capped at 1.25","source_reference":"https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view","scenes":details,"original_media":retrieved},indent=2,ensure_ascii=False))
(OUT/"LICENSES.txt").write_text("\n".join(k+": "+c+" "+'https://commons.wikimedia.org/wiki/File:'+quote(n) for k,(n,f,c) in SOURCES.items())+"\nOriginal crop, graphic overlays, editorial animation. Abide by per-source attribution and ShareAlike where applicable.\n")
print("VOICE_ASSETS_COMPLETE",flush=True)
