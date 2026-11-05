#!/usr/bin/env python3
"""Transcribe actual Warner Bros The Dark Knight trailer to locate dialogue for music-led edit.
Speech-to-text is analysis only. Never creates voice, visuals or audio assets.
"""
from pathlib import Path
import urllib.request,json,time
from faster_whisper import WhisperModel
OUT=Path("delivery/joker_asr");OUT.mkdir(parents=True,exist_ok=True)
src=OUT/"warner_1080.mov"
url="https://pdl.warnerbros.com/wbmovies/thedarkknight/trailer2/TDK_TRL2_1080p.mov"
with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"}),timeout=80) as r,src.open("wb") as f:
 while True:
  b=r.read(2<<20)
  if not b:break
  f.write(b)
print("FILM_AUDIO_SOURCE",src.stat().st_size,flush=True)
model=WhisperModel("base.en",device="cpu",compute_type="int8",cpu_threads=4,num_workers=2)
segments,inf=model.transcribe(str(src),beam_size=2,language="en",word_timestamps=True,condition_on_previous_text=False)
out=[]
for seg in segments:
 record={"start":round(seg.start,3),"end":round(seg.end,3),"text":seg.text,
   "words":[{"start":round(w.start,3),"end":round(w.end,3),"word":w.word} for w in (seg.words or [])]}
 out.append(record)
 print("DIALOGUE",json.dumps(record)[:1500],flush=True)
(OUT/"ORIGINAL_DIALOGUE_TIMINGS.json").write_text(json.dumps(out,indent=2))
src.unlink()
print("TRANSCRIPTION_ANALYSIS_ONLY_COMPLETE",len(out),flush=True)
