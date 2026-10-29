#!/usr/bin/env python3
"""Editor-authored five-second FOLEY cue mix. Recorded CC0 sounds only.
NOT automatically selected by content or keyword; real audiovisual approval required.
"""
import os, pathlib, json, hashlib, tempfile, subprocess, math, zipfile
import numpy as np
from scipy.signal import butter,sosfilt
import soundfile as sf

ROOT=pathlib.Path(os.environ.get("ASMR_ASSETS","/kaggle/input/satisfying-studio-cc0-asmr-v1"))
DEST=pathlib.Path(os.environ.get("ASMR_OUT","/kaggle/working/prismatic_asmr"))
DEST.mkdir(parents=True,exist_ok=True)
FPS=24
RATE=48000
DURATION=5
# Deliberate movement-defined times, not randomly generated sonic montage.
# Frame contacts must be adjusted only against ACTUAL final rendered frames.
CUES=[
 ("rubberduck_wood_metal.zip","metal_sheet_03.ogg",9,-22,.9,.15,"controlled metallic tool movement"),
 ("rubberduck_water_slime.zip","slime_03.ogg",22,-14,1,-.16,"first pressure on wet gel"),
 ("rubberduck_water_slime.zip","slime_07.ogg",40,-15,1.1,.06,"increasing gel compression"),
 ("rubberduck_water_slime.zip","slime_13.ogg",56,-13,1.18,-.08,"wet gel flattening"),
 ("rubberduck_water_slime.zip","slime_10.ogg",66,-17,1,.10,"lateral jelly bulge"),
 ("kenney_rpg.zip","OGG/knifeSlice.ogg",82,-23,.8,.2,"metal gliding over wet surface"),
 ("rubberduck_water_slime.zip","bubble_02.ogg",88,-21,1,0,"tiny microbubble"),
 ("rubberduck_breaking_falling.zip","bfh1_glass_hit_01.ogg",104,-24,1.3,-.1,"fine crystal contact, not major shatter"),
 ("rubberduck_water_slime.zip","slime_02.ogg",109,-23,.8,0,"release and settle"),
]

def find_recorded(pack,name):
    # Kaggle may auto-extract ZIP inputs; keep source pack and clip name explicit.
    p=ROOT/pack
    if p.is_file():
        with zipfile.ZipFile(p) as z:return z.read(name)
    for c in ROOT.rglob(pathlib.Path(name).name):
        if c.is_file():return c.read_bytes()
    raise FileNotFoundError("Required CC0 recording missing: %s / %s"%(pack,name))

def decode(buf):
    with tempfile.NamedTemporaryFile(suffix=".ogg") as f:
        f.write(buf);f.flush()
        proc=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",f.name,"-f",
                             "f32le","-ar","48000","-ac","1","-"],
                             capture_output=True,check=True,timeout=30)
        return np.frombuffer(proc.stdout,dtype="<f4").astype(np.float64)

def main():
    mixed=np.zeros((RATE*DURATION,2),dtype=np.float64)
    log=[]
    for archive,clip,frame,gain_db,speed,pan,event in CUES:
        buf=find_recorded(archive,clip)
        data=decode(buf)
        cutoff=10500 if ("metal" in clip or "glass" in clip) else 8300
        data=sosfilt(butter(2,cutoff,fs=RATE,output="sos"),data)
        if speed!=1:
            position=np.arange(0,len(data)-1,speed)
            data=np.interp(position,np.arange(len(data)),data)
        start=int(frame/FPS*RATE)
        data=data[:max(0,len(mixed)-start)]
        if not len(data):continue
        fade=min(int(RATE*.006),len(data)//3)
        if fade:
            data[:fade]*=np.linspace(0,1,fade)
            data[-fade:]*=np.linspace(1,0,fade)
        g=10**(gain_db/20)
        left=math.cos((pan+1)*math.pi/4)*1.4142
        right=math.sin((pan+1)*math.pi/4)*1.4142
        mixed[start:start+len(data),0]+=g*left*data
        mixed[start:start+len(data),1]+=g*right*data
        log.append(dict(pack=archive,filename=clip,frame=frame,event=event,
                        gain_db=gain_db,speed=speed,pan=pan,source_sha256=hashlib.sha256(buf).hexdigest(),
                        license="CC0",review_status="editor chosen; final rendered scene sync unverified"))
    peak=np.max(np.abs(mixed))
    if peak>0:mixed*=10**(-4/20)/peak
    mixed[-int(RATE*.15):]*=np.linspace(1,0,int(RATE*.15))[:,None]
    path=DEST/"original_CC0_foley_5sec.wav"
    sf.write(path,mixed.astype(np.float32),RATE,subtype="PCM_24")
    (DEST/"editor_audio_cue_sheet.json").write_text(json.dumps({
        "fps":FPS,"duration_seconds":DURATION,"cues":log,
        "reminder":"A real visual comparison and full listening are required; no claimed quality score."
        },indent=2)+"\n")
    print("FOLEY_RENDERED_NOT_APPROVED",path,path.stat().st_size)
if __name__=="__main__":main()
