#!/usr/bin/env python3
"""Episode 1 Piper line WAV generation; original lines untouched.
Only two provisional LibriVox-based model candidates. Fails closed on model card rights.
This does not render video, change legacy story or launch Kaggle.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import urllib.request
import wave
from pathlib import Path

BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US"
SHORTLIST={"sprite":"kristin","elder_sprite":"john"}
ROOT=Path(__file__).resolve().parent

def fetch(url, target, cap):
    if not url.startswith(BASE+"/"):
        raise ValueError("Untrusted voice file source")
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(target.suffix+".partial")
    req=urllib.request.Request(url,headers={"User-Agent":"CartoonStudio-Episode1-Piper-license-check/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=100) as src, temp.open("wb") as out:
            total=0
            while True:
                part=src.read(1024*512)
                if not part:break
                total+=len(part)
                if total>cap:raise ValueError("Voice file exceeds allowlisted size")
                out.write(part)
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)

def model(cache,name):
    if name not in SHORTLIST.values():
        raise ValueError("Voice not in explicitly selected Episode 1 candidates")
    base=f"{BASE}/{name}/medium"
    model_name=f"en_US-{name}-medium"
    folder=cache/name
    card=folder/"MODEL_CARD"
    if not card.exists():fetch(base+"/MODEL_CARD",card,25_000)
    text=card.read_text(encoding="utf-8",errors="replace").lower()
    if "public domain" not in text or "librivox" not in text:
        raise ValueError("VOICE_LICENSE_NOT_CONFIRMED "+name+" — do not synthesize or publish")
    files=[folder/(model_name+".onnx"),folder/(model_name+".onnx.json")]
    for path in files:
        if not path.exists():
            fetch(base+"/"+path.name,path,110_000_000 if path.suffix==".onnx" else 30_000)
    if files[0].stat().st_size<5_000_000:
        raise ValueError("Suspect incomplete model "+name)
    config=json.loads(files[1].read_text(encoding="utf-8"))
    if config.get("language",{}).get("code")!="en_US" or config.get("num_speakers")!=1:
        raise ValueError("Wrong voice model configuration")
    return files[0],files[1],card

def main(story_path,out,cache,limit=0):
    from piper.voice import PiperVoice
    story=json.loads(Path(story_path).read_text(encoding="utf-8"))
    dialogue=story["dialogue"]
    if len(dialogue)!=15 or set(story["characters"])!=set(SHORTLIST):
        raise ValueError("Unexpected Episode 1 voices/length")
    out=Path(out).resolve()
    cache=Path(cache).resolve()
    out.mkdir(parents=True,exist_ok=True)
    (out/"licenses").mkdir(exist_ok=True)
    selected=dialogue[:limit] if limit else dialogue
    mapped={}
    licences={}
    for key in {line["speaker"] for line in selected}:
        name=SHORTLIST[key]
        expected="en_US-"+name+"-medium"
        if story["characters"][key]["voice"]!=expected:
            raise ValueError("Voice ID drift for "+key)
        f,config,card=model(cache,name)
        mapped[key]=PiperVoice.load(str(f),config_path=str(config))
        target=out/"licenses"/(expected+".MODEL_CARD")
        target.write_bytes(card.read_bytes())
        licences[key]={"model":expected,"model_sha256":hashlib.sha256(f.read_bytes()).hexdigest(),
                       "model_card_sha256":hashlib.sha256(card.read_bytes()).hexdigest(),
                       "rights":"public_domain_librivox_model_card_checked_not_voice_quality_approved"}
    timing=[]
    for line in selected:
        dest=out/f"line_{line['id']:03}.wav"
        with wave.open(str(dest),"wb") as wf:
            mapped[line["speaker"]].synthesize_wav(line["text"],wf)
        with wave.open(str(dest),"rb") as wf:
            actual=wf.getnframes()/wf.getframerate()
        allocated=line["end"]-line["start"]-0.12
        if not 0.1<=actual<=allocated:
            raise ValueError(f"AUDIO_TIMING_NOT_APPROVED line {line['id']} duration {actual:.3f}s allowed {allocated:.3f}s")
        timing.append({"id":line["id"],"speaker":line["speaker"],"duration":round(actual,3),
                       "start":line["start"],"end":line["end"],
                       "wav_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
        print("EP01_ACTUAL_VOICE_WAV",line["id"],line["speaker"],round(actual,2))
    (out/"voice-evidence.json").write_text(json.dumps({"voice_actors":licences,
         "actual_lines_generated":len(timing),"dialogue_timing":timing,
         "quality_approved_by_user":False,"video_rendered":False},indent=2)+"\n",encoding="utf-8")
    print("VOICE_GENERATION_DONE; quality_approval_and_preview_still_required",len(timing))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--story",type=Path,default=ROOT/"story.json")
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--cache",type=Path,default=Path("/tmp/cartoonstudio-ep01-piper"))
    ap.add_argument("--limit",type=int,default=0)
    args=ap.parse_args()
    main(args.story,args.out,args.cache,args.limit)
