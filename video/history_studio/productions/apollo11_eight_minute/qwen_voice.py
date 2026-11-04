#!/usr/bin/env python3
"""Original eight-chapter Facts Uncovered narration in approved Qwen3-TTS Ryan voice."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
MODEL="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
INSTRUCTION=("Tell this Apollo Eleven story naturally, like a thoughtful experienced "
             "American history documentary narrator who speaks briskly and conversationally "
             "near one hundred ninety-five words per minute. Warm but controlled; clear proper "
             "names, human timing, connected sentences, no theatrical overacting, no robotic "
             "word-by-word delivery, no artificial long pauses. Read all words clearly.")
ROOT=Path("video/history_studio/productions/apollo11_eight_minute")
STORY=json.loads((ROOT/"story.json").read_text())
def probe(path):
    return sf.info(str(path)).duration
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--chapter",type=int,required=True,choices=list(range(1,9)))
    args=ap.parse_args()
    chapter=STORY["chapters"][args.chapter-1]
    out=Path("delivery/apollo11_eight/qwen")/f"ch{args.chapter:02}"
    out.mkdir(parents=True,exist_ok=True)
    import torch
    torch.set_num_threads(max(1,min(4,os.cpu_count() or 2)))
    torch.set_num_interop_threads(2)
    from qwen_tts import Qwen3TTSModel
    print("QWEN_RYAN_LOADING",MODEL,chapter["title"],flush=True)
    tts=Qwen3TTSModel.from_pretrained(MODEL,device_map="cpu",dtype=torch.float32,attn_implementation="sdpa")
    measurements=[]
    cursor=0
    for i,beat in enumerate(chapter["beats"],1):
        text=beat["text"].strip()
        words=len(text.split())
        wavs,rate=tts.generate_custom_voice(text=text,speaker="Ryan",language="English",instruct=INSTRUCTION)
        wave=np.asarray(wavs[0],dtype=np.float32).flatten()
        if not np.isfinite(wave).all() or len(wave)<rate*3:
            raise RuntimeError(f"Qwen generated malformed beat {beat['id']}")
        native=out/f"{beat['id']}_native.wav"
        fast=out/f"{beat['id']}.wav"
        sf.write(native,wave,rate,subtype="PCM_16")
        raw_sec=probe(native)
        raw_wpm=words*60/raw_sec
        tempo=min(1.25,max(1.0,196/raw_wpm))
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-i",str(native),"-af",f"atempo={tempo:.5f},highpass=f=65,lowpass=f=11000,aresample=48000",
            "-ac","1","-ar","48000","-c:a","pcm_s16le",str(fast)],check=True,timeout=150)
        duration=probe(fast)
        if not 10<=duration<=32:raise RuntimeError(f"Unexpected beat runtime {beat['id']}: {duration:.2f}s, {words} words")
        measured=words*60/duration
        if not 135<=measured<=235:raise RuntimeError(f"Unnatural measured pace at {beat['id']}: {measured}")
        measurements.append({"id":beat["id"],"text":text,"chapter":chapter["title"],
            "source":beat["source"],"source_in_seconds":beat["source_in_seconds"],
            "start_seconds":round(cursor,4),"end_seconds":round(cursor+duration,4),
            "duration_seconds":round(duration,4),"words":words,"raw_wpm":round(raw_wpm,2),
            "final_wpm":round(measured,2),"tempo":round(tempo,4),"audio_sha256":sha(fast),
            "file":fast.name})
        cursor+=duration
        native.unlink(missing_ok=True)
        print("QWEN_RYAN_BEAT",beat["id"],words,round(duration,2),round(measured,1),flush=True)
    report={"model":MODEL,"speaker":"Ryan","chapter":args.chapter,
        "title":chapter["title"],"total_seconds":round(cursor,4),
        "total_words":sum(s["words"] for s in measurements),
        "effective_wpm":round(sum(s["words"] for s in measurements)*60/cursor,2),
        "audio_rights":"Qwen3 TTS model Apache 2.0; original scripted narration",
        "voice_reference":"https://drive.google.com/file/d/14vfA-GDPPZiwArJzDWKMsjZA3r0wXyxp/view?usp=drivesdk",
        "human_listen_approved":False,"beats":measurements}
    (out/f"ch{args.chapter:02}_timings.json").write_text(json.dumps(report,indent=2)+"\n")
    print("QWEN_CHAPTER_RENDERED",args.chapter,round(cursor,2),flush=True)
if __name__=="__main__":main()
