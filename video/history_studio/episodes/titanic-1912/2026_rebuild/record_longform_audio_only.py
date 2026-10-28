#!/usr/bin/env python3
"""Record the complete 15-chapter Titanic script as 151 individually timed
Kokoro paragraphs. This job records ONLY sound; it makes no video, selects
no images and cannot publish. Shot-internal cut times await listening review.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parent
EPISODE=ROOT.parent
PARTS=("01_05","06_10","11_15")
OUT=ROOT/"recorded_longform"

def run(cmd):
    subprocess.run([str(s) for s in cmd],check=True)

def get_sections():
    chs=[c for p in PARTS for c in json.loads((EPISODE/"v2"/f"script_{p}.json").read_text(encoding="utf8"))]
    assert len(chs)==15
    sections=[]
    for n,c in enumerate(chs,1):
        for p,words in enumerate(c["narration"].split("\n\n"),1):
            assert words.strip()
            sections.append({"chapter":n,"title":c["title"],"paragraph":p,"narration":words,
                             "source_refs":c["source_refs"]})
    assert len(sections)==151,len(sections)
    assert "subscribe" in sections[-1]["narration"].lower()
    return sections

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--voices",type=Path,required=True)
    args=ap.parse_args()
    from kokoro_onnx import Kokoro
    speech=Kokoro(str(args.model),str(args.voices))
    records=get_sections()
    OUT.mkdir(parents=True,exist_ok=True)
    now=0.
    files=[]
    for idx,record in enumerate(records):
        name=f"T{record['chapter']:02d}_P{record['paragraph']:02d}"
        wav=OUT/(name+".wav")
        audio,rate=speech.create(record["narration"],voice="am_michael",speed=0.94,lang="en-us")
        audio=np.asarray(audio,dtype=np.float32).reshape(-1)
        if rate!=24000 or not np.isfinite(audio).all() or len(audio)<=rate*3:
            raise RuntimeError(f"Invalid narration {name}: {rate}, {len(audio)} samples")
        sf.write(wav,audio,rate,subtype="PCM_24")
        spoken=len(audio)/rate
        pause=0.8 if idx==len(records)-1 or records[idx+1]["chapter"]!=record["chapter"] else 0.25
        record.update({"audio_file":wav.name,"start_seconds":round(now,3),
                       "spoken_seconds":round(spoken,3),
                       "pause_after_seconds":pause,
                       "end_seconds":round(now+spoken+pause,3),
                       "source_text_sha256":hashlib.sha256(record["narration"].encode()).hexdigest(),
                       "picture_cuts_in_paragraph":"UNSET: manual audio listening required",
                       "editorial_status":"AUDIO ONLY / NOT APPROVED"})
        now+=spoken+pause
        files.append(wav)
        print("VOICE_PARAGRAPH",idx+1,"/",len(records),name,round(spoken,2),flush=True)
    for wav in files:
        run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",wav,"-c:a","flac",wav.with_suffix(".flac")])
    listening=OUT/"Titanic_Complete_Narration_Listening_Copy.m4a"
    joined=OUT/"joined_sound_only.wav"
    with sf.SoundFile(joined,"w",samplerate=24000,channels=1,subtype="PCM_16") as dst:
        for r in records:
            a,s=sf.read(OUT/r["audio_file"],dtype="float32")
            assert s==24000
            dst.write(a)
            dst.write(np.zeros(round(r["pause_after_seconds"]*24000),dtype=np.float32))
    run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",joined,
        "-af","loudnorm=I=-16:TP=-1.5:LRA=9",
        "-ar","48000","-ac","2","-c:a","aac","-b:a","192k",listening])
    joined.unlink(missing_ok=True)
    manifest={"episode":"Titanic: The Final Night, the Warnings and What the Wreck Reveals",
      "narrator":"Kokoro am_michael, speed 0.94, English",
      "chapter_count":15,"paragraph_count":len(records),
      "duration_seconds":round(now,3),
      "subtitles":"WORD TIMINGS UNVERIFIED — DO NOT USE EQUAL WORD DIVISION",
      "publication_approved":False,
      "visual_timeline":"MUST BE MANUALLY APPROVED IN AUDIO TIME; NO AUTOMATIC SELECTION",
      "records":records}
    (OUT/"NARRATION_TIME_LEDGER.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf8")
    print("AUDIO_ONLY_FINAL_LENGTH_MINUTES",round(now/60,2),flush=True)
    print("LONGFORM_NARRATION_RECORDED_NOT_A_FINISHED_FILM",flush=True)
if __name__=="__main__":
    main()
