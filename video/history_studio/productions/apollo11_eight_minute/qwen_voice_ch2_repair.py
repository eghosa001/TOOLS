#!/usr/bin/env python3
"""Re-render only chapter 2 with controlled short-phrase Qwen 1.7B Ryan speech."""
import json,os,subprocess,hashlib
from pathlib import Path
import numpy as np,soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel
ROOT=Path("video/history_studio/productions/apollo11_eight_minute")
story=json.loads((ROOT/"story.json").read_text())
chapter=story["chapters"][1]
out=Path("delivery/apollo11_eight/qwen/ch02")
out.mkdir(parents=True,exist_ok=True)
torch.set_num_threads(4);torch.set_num_interop_threads(2)
m=Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
guide="Narrate briskly, at a natural pace of around two hundred words a minute. Calm documentary storytelling, fluent, clear English; no theatrical pauses."
allbeats=[];clock=0
for i,b in enumerate(chapter["beats"]):
    text=b["text"]
    # Split difficult long phrases to prevent unusually slow or wandering model output.
    sentences=[x.strip() for x in text.split(". ") if x.strip()]
    parts=[]
    for x in sentences:
        if x[-1] not in ".!?":x+="."
        parts.append(x)
    waves=[];rate=None
    for phrase in parts:
        speech,r=m.generate_custom_voice(text=phrase,speaker="Ryan",language="English",instruct=guide)
        w=np.asarray(speech[0],dtype=np.float32).ravel()
        if rate is None:rate=r
        if r!=rate or len(w)<rate*.3 or not np.isfinite(w).all():raise ValueError("Audio sample invalid")
        waves.append(w)
        waves.append(np.zeros(int(rate*.05),dtype=np.float32))
    raw=out/(b["id"]+"_raw.wav")
    sf.write(raw,np.concatenate(waves),rate,subtype="PCM_16")
    sec=sf.info(str(raw)).duration
    wc=len(text.split())
    base=wc*60/sec
    tempo=min(1.25,max(1,200/base))
    dst=out/(b["id"]+".wav")
    subprocess.run(["ffmpeg","-v","error","-nostdin","-y","-i",str(raw),"-af",f"atempo={tempo:.5f},aresample=48000","-ac","1","-ar","48000","-c:a","pcm_s16le",str(dst)],check=True)
    dur=sf.info(str(dst)).duration
    final=wc*60/dur
    if not 130<=final<=240:raise ValueError(f"Unnatural measured pace {b['id']} {final}")
    allbeats.append({"id":b["id"],"text":text,"chapter":chapter["title"],
     "source":b["source"],"source_in_seconds":b["source_in_seconds"],
     "start_seconds":round(clock,4),"end_seconds":round(clock+dur,4),
     "duration_seconds":round(dur,4),"words":wc,"raw_wpm":round(base,2),
     "final_wpm":round(final,2),"tempo":round(tempo,4),
     "audio_sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"file":dst.name})
    clock+=dur
    raw.unlink()
    print("QWEN_CH2_SENTENCE_STITCHED",b["id"],round(final,1),round(dur,1),flush=True)
meta={"model":"Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice","speaker":"Ryan","chapter":2,
"title":chapter["title"],"total_seconds":round(clock,4),
"total_words":sum(b["words"] for b in allbeats),"effective_wpm":round(sum(b["words"] for b in allbeats)*60/clock,2),
"audio_rights":"Qwen3 TTS Apache 2.0 original script","human_listen_approved":False,"beats":allbeats}
(out/"ch02_timings.json").write_text(json.dumps(meta,indent=2)+"\n")
print("QWEN_CH2_REPAIR_READY",meta["effective_wpm"],flush=True)
