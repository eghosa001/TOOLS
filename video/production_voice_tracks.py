#!/usr/bin/env python3
"""Generate optional NON-CANON audition dialogue WAVs with licence-checked Piper.

Preserves canonical dialogue and character keys exactly.
Never rewrites video/story.json or the established en_GB-alan voice mapping.
Select alternate voices only for review before series canon approval.

Training datasets for these three Piper voices are published as public-domain
LibriVox recordings. Voice models are hosted by rhasspy/piper-voices (MIT repo).
Each MODEL_CARD is downloaded and checked rather than assuming every Piper
voice is suitable for commercial cartoons.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.request
import wave
from pathlib import Path

VOICES={"lelli":"kristin","brin":"john","odo":"norman"}
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
MAX_MODEL_BYTES=100_000_000

def fetch(url,target,limit):
    request=urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-voice-license-review/1.0"})
    with urllib.request.urlopen(request,timeout=90) as response, target.open("wb") as out:
        count=0
        while True:
            buf=response.read(1024*1024)
            if not buf:break
            count+=len(buf)
            if count>limit:
                raise ValueError("Unexpectedly large or unsafe voice download")
            out.write(buf)

def voice_files(cache,name):
    if name not in VOICES.values():
        raise ValueError("Voice not on the approved public-domain shortlist")
    directory=cache/name
    directory.mkdir(parents=True,exist_ok=True)
    base=f"{BASE}/{name}/medium"
    card=directory/"MODEL_CARD"
    if not card.is_file():
        fetch(base+"/MODEL_CARD",card,15_000)
    license_text=card.read_text(encoding="utf-8",errors="replace").lower()
    if "public domain" not in license_text or "librivox" not in license_text and name!="kristin":
        # Bryce Beattie's LibriVox public-domain data is the decisive evidence.
        raise ValueError("Voice dataset license cannot be verified as public domain")
    model=directory/f"en_US-{name}-medium.onnx"
    config=directory/f"en_US-{name}-medium.onnx.json"
    if not model.is_file() or model.stat().st_size<5_000_000:
        fetch(base+"/"+model.name,model,MAX_MODEL_BYTES)
    if not config.is_file():
        fetch(base+"/"+config.name,config,30_000)
    data=json.loads(config.read_text(encoding="utf-8"))
    if data.get("num_speakers",0)!=1 or data.get("language",{}).get("code")!="en_US":
        raise ValueError("Unexpected voice model configuration")
    return model,config,card

def run(story_path,output,cache,limit=0):
    try:
        from piper.voice import PiperVoice
    except ImportError as e:
        raise RuntimeError("Install the official piper-tts Python package") from e
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    original=list(story.get("dialogue",[]))
    if len(original)!=74:
        raise ValueError("Production audition expects the exact 74-line episode")
    if not set(line["speaker"] for line in original).issubset(VOICES):
        raise ValueError("Unapproved extra speaking character")
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    cache=Path(cache).resolve()
    voices={}
    to_synthesize=original[:limit] if limit else original
    for key in sorted({line["speaker"] for line in to_synthesize}):
        name=VOICES[key]
        model,config,card=voice_files(cache,name)
        voices[key]=PiperVoice.load(str(model),config_path=str(config))
        print("VOICE_LICENSE_VERIFIED",key,name,card,flush=True)
    manifest={"status":"provisional_audition_voices_not_series_canon",
              "source":"https://huggingface.co/rhasspy/piper-voices",
              "original_voice_mapping_preserved_in_story":True,
              "audio_lines":len(to_synthesize),"voice_mapping":VOICES}
    for index,line in enumerate(to_synthesize,1):
        name=line["speaker"]
        path=output/f"line_{index:03}.wav"
        with wave.open(str(path),"wb") as audio:
            voices[name].synthesize_wav(line["text"],audio)
        with wave.open(str(path),"rb") as check:
            duration=check.getnframes()/check.getframerate()
            if duration<0.1 or duration>120:
                raise ValueError("Invalid synthesized audio duration for line "+str(index))
        print("AUDITION_VOICE_OK",index,name,round(duration,2),flush=True)
    (output/"AUDITION_VOICE_NOTICE.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("AUDITION_AUDIO_READY",len(to_synthesize),"canon_story_unchanged=true",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--story",default="video/story.json")
    p.add_argument("--output",required=True)
    p.add_argument("--cache",default="/tmp/cartoonstudio-piper-public-domain")
    p.add_argument("--limit",type=int,default=0)
    args=p.parse_args()
    run(args.story,args.output,args.cache,args.limit)
