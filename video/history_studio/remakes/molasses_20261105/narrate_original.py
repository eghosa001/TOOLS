#!/usr/bin/env python3
"""Produce deliberately scripted 24-scene male narration, never automated visual selection."""
import hashlib,json,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
root=Path("delivery/molasses_voice")
root.mkdir(parents=True,exist_ok=True)
data=json.loads(Path("video/history_studio/remasters_2026/episode_research_and_scripts.json").read_text())
scenes=data["episodes"]["molasses"]["scenes"]
assert len(scenes)==24
engine=Kokoro("model/kokoro-v1.0.onnx","model/voices-v1.0.bin")
texts=[]
wavs=[]
info=[]
rate=None
for i,scene in enumerate(scenes,1):
    line=scene["narration"].strip()
    if i==24:
        line+=" If you value history told through evidence, subscribe to Facts Uncovered: Stories and Evidence."
    # Clear spoken forms, no synthetic or misleading claims.
    line=line.replace("Copp's Hill","Copps Hill").replace("U.S.S.","U S S")
    signal, sr=engine.create(line,voice="am_michael",speed=1.08,lang="en-us")
    sig=np.asarray(signal,dtype=np.float32).reshape(-1)
    if rate is None:rate=sr
    assert rate==sr and len(sig)>2*sr and np.isfinite(sig).all()
    tail=0.24 if i!=24 else 0.45
    sig=np.concatenate([sig,np.zeros(int(sr*tail),dtype=np.float32)])
    begin=sum(len(w) for w in wavs)/sr
    wavs.append(sig)
    info.append({"scene":scene["id"],"title":scene["heading"],"narration":line,
                 "begin_raw":round(begin,4),"end_raw":round(begin+len(sig)/sr,4),
                 "seconds_raw":round(len(sig)/sr,3)})
    print("RECORDED_MALE_MICH",scene["id"],round(len(sig)/sr,2),flush=True)
raw=np.concatenate(wavs)
rawsec=len(raw)/rate
if not (390<rawsec<560):
  raise RuntimeError("Narration unexpected duration "+str(rawsec))
raw_file=root/"narration_raw.wav"
sf.write(raw_file,np.clip(raw*0.92,-0.98,0.98),rate,subtype="PCM_16")
target=456.0
speed=rawsec/target
if not (.83<=speed<=1.23):
  raise RuntimeError("Time stretch exceeds natural delivery limit "+str(speed))
final=root/"Molasses_Michael_7m36s_48k.wav"
subprocess.run(["ffmpeg","-v","error","-nostdin","-y","-i",str(raw_file),"-af",
                "atempo="+str(speed)+",loudnorm=I=-16:TP=-1.5:LRA=10",
                "-ac","2","-ar","48000","-c:a","pcm_s16le",str(final)],check=True)
actual=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries",
         "format=duration","-of","json",str(final)]))["format"]["duration"]
assert abs(float(actual)-456)<1.1
for x in info:
    x["start"]=round(x.pop("begin_raw")/speed,3)
    x["end"]=round(x.pop("end_raw")/speed,3)
    x["seconds"]=round(x.pop("seconds_raw")/speed,3)
(root/"scene_timings.json").write_text(json.dumps(info,indent=2)+"\n")
def stamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"
out=[];n=1
for scene in info:
  words=scene["narration"].split()
  groups=[]
  for j in range(0,len(words),7):groups.append(words[j:j+7])
  sec=scene["seconds"]
  total=sum(len(g) for g in groups)
  cur=scene["start"]
  for k,g in enumerate(groups):
    nxt=scene["end"] if k==len(groups)-1 else cur+sec*len(g)/total
    cut=(len(g)+1)//2
    out.append(f"{n}\n{stamp(cur)} --> {stamp(nxt)}\n{' '.join(g[:cut])}\n{' '.join(g[cut:])}")
    cur=nxt;n+=1
(root/"subtitles.srt").write_text("\n\n".join(out)+"\n")
(root/"VOICE_QC.json").write_text(json.dumps({
  "voice":"Kokoro am_michael MALE", "model":"Kokoro 82M Apache 2.0",
  "source":"existing 24 original Molasses research scenes, preserved content, appended factual outro",
  "duration":float(actual),"original_duration":rawsec,"atempo":speed,
  "sha256":hashlib.sha256(final.read_bytes()).hexdigest(),
  "status":"REVIEW_REQUIRED_HUMAN_LISTENING_NOT_DONE",
},indent=2)+"\n")
print("MALE_DOCUMENTARY_NARRATION_DONE",json.dumps({"duration":float(actual),"atempo":speed}),flush=True)
