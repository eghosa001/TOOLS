#!/usr/bin/env python3
"""Render two extended Kokoro Michael male-voice review narrations.
Open model/voice source is retained for editorial validation; no posting.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

SCRIPTS={
    "roman_scroll_extended": (
        "Imagine a book that survived a volcanic eruption, but could not be opened without "
        "destroying it. In the year seventy-nine, Mount Vesuvius buried the Roman town of "
        "Herculaneum. Inside a seaside villa, hundreds of papyrus scrolls were baked into "
        "brittle, charcoal-black rolls. For generations, their words were almost impossible "
        "to recover. Then researchers found a way to look inside without touching the layers. "
        "Powerful X-ray scans mapped the hidden papyrus. Computer models helped separate its "
        "tightly curled surfaces, and specialists examined the ancient Greek writing. "
        "In June twenty twenty-six, researchers announced a breakthrough. "
        "The surviving portion of scroll sixteen sixty-seven had been virtually opened from "
        "end to end. Nearly one and a half metres of text, arranged in twenty columns, "
        "became accessible for study. Scholars could finally follow an ancient argument "
        "across entire passages, rather than struggling with isolated letters. "
        "One sealed scroll has given up its secrets. Hundreds more are still waiting. "
        "Subscribe to Facts Uncovered for more lost history."
    ),
    "sealed_library_extended": (
        "Beneath a Roman town destroyed by Mount Vesuvius lies a library that may still "
        "hold hundreds of unread books. In the year seventy-nine, volcanic ash and heat "
        "buried Herculaneum. They also carbonized papyrus scrolls inside a vast seaside "
        "house, now called the Villa of the Papyri. The rolls survived, but became so "
        "fragile that unrolling them could tear the writing apart. "
        "About six hundred remain unopened. For years, scholars could only guess "
        "what those sealed books contained. Now a different approach is working. "
        "Researchers scan the rolls with powerful X-rays and use computers to follow their "
        "hidden layers. Experts then decipher the ancient Greek letters. "
        "In twenty twenty-six, one scroll yielded nearly twenty columns of text from its "
        "surviving length. Another revealed more than seventy columns. "
        "Newly recovered works include ancient Greek philosophy that scholars had never seen "
        "in such complete form. But this is not the end of the story. "
        "Every unopened roll could contain ideas that have waited nearly two thousand years "
        "for a reader. Subscribe to Facts Uncovered for more discoveries."
    ),
}
SOURCE_URLS=[
 "https://research.uky.edu/news/day-herculaneum-scrolls-began-speaking-again",
 "https://engr.uky.edu/herculaneum",
 "https://scrollprize.org/firstscroll",
]
def run(*cmd):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode:
  raise RuntimeError("FFmpeg failure: "+p.stderr[-1400:])
def main(out):
 from kokoro_onnx import Kokoro
 m=Path("model/kokoro-v1.0.onnx");v=Path("model/voices-v1.0.bin")
 assert m.is_file() and v.is_file(), "Required verified Kokoro resources not installed"
 engine=Kokoro(str(m),str(v));out.mkdir(parents=True,exist_ok=True)
 summary=[]
 for key,script in SCRIPTS.items():
  wave,rate=engine.create(script,voice="am_michael",speed=1.15,lang="en-us")
  wave=np.asarray(wave,dtype=np.float32).reshape(-1)
  assert np.isfinite(wave).all() and len(wave)>rate*30
  words=len(script.split())
  native=len(wave)/rate
  # Natural 174–185 WPM with no clipped speech or heavy post stretch.
  target=max(54.0,min(67.0,words*60.0/179.0))
  factor=native/target
  if not 0.8<=factor<=1.25:
   raise RuntimeError(f"{key}: unsafe tempo {factor:.3f}; revise text rather than distort")
  raw=out/f"{key}_raw.wav"
  sf.write(raw,wave,rate,subtype="PCM_16")
  dest=out/f"Facts_Uncovered_{key}_MALE_Michael_Narration.wav"
  run("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(raw),
      "-af",f"atempo={factor:.6f},loudnorm=I=-17:TP=-1.5:LRA=8,apad=pad_dur=0.85",
      "-t",f"{target+0.8:.3f}","-ar","48000","-ac","2","-c:a","pcm_s16le",str(dest))
  info={
   "title":key,"audio_file":dest.name,"model":"kokoro-onnx v1.0",
   "voice_gender":"male","speaker_id":"am_michael",
   "narration_text":script,"word_count":words,
   "native_duration_sec":round(native,3),
   "post_tempo_factor":round(factor,4),
   "audio_duration_sec":round(target+0.8,3),
   "speaking_rate_wpm":round(words*60.0/target,1),
   "voice_fingerprint":hashlib.sha256(dest.read_bytes()).hexdigest(),
   "research_sources":SOURCE_URLS,
   "pronunciation_terms_pending_listen":["Herculaneum","Vesuvius","papyrus","Villa of the Papyri"],
   "user_approval":"PREVIEW_NOT_APPROVED",
   "footage_rights":"UK Research permission pending; not approved for monetized public release",
   "upload_to_youtube":False,
  }
  (out/f"{key}_AUDIO_QC.json").write_text(json.dumps(info,indent=2)+"\n")
  (out/f"{key}_SCRIPT.txt").write_text(script+"\n")
  summary.append(info)
  print("RENDERED_MALE_EXTENDED_REVIEW",key,words,round(target,2),dest.stat().st_size,flush=True)
 (out/"EXTENDED_NARRATION_MANIFEST.json").write_text(json.dumps(summary,indent=2)+"\n")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--out",type=Path,default=Path("delivery/herculaneum_extended_male"))
 main(p.parse_args().out)
