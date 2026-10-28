#!/usr/bin/env python3
"""Record only the two specifically authored Titanic Short narrations.
No footage selection, picture editing, publication, or guessed word SRT timing.
"""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"SHORTS_FINAL_SCRIPTS_AND_VISUAL_DIRECTION.json"
OUT=ROOT/"recorded_shorts"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--voices",type=Path,required=True)
    args=ap.parse_args()
    if not args.model.is_file() or not args.voices.is_file():raise FileNotFoundError("Kokoro model not found")
    from kokoro_onnx import Kokoro
    engine=Kokoro(str(args.model),str(args.voices))
    source=json.loads(SOURCE.read_text(encoding="utf8"))
    assert len(source["deliverables"])==2
    OUT.mkdir(parents=True,exist_ok=True)
    records=[]
    for item in source["deliverables"]:
        assert item["narration"].strip().endswith("Subscribe to Facts Uncovered for more history.") or item["narration"].strip().endswith("Subscribe to Facts Uncovered for more historical discoveries.")
        raw,sr=engine.create(item["narration"],voice="am_michael",speed=0.94,lang="en-us")
        wave=np.asarray(raw,dtype=np.float32).reshape(-1)
        if sr not in (24000,48000) or not np.isfinite(wave).all() or wave.size < sr*10:
            raise RuntimeError("Corrupt narration or unsupported sample rate for "+item["id"])
        path=OUT/(item["id"]+".wav")
        sf.write(path,wave,sr,subtype="PCM_24")
        duration=len(wave)/sr
        record={"file":path.name,"id":item["id"],"duration_seconds":round(duration,3),
          "narration_sha256":hashlib.sha256(item["narration"].encode()).hexdigest(),
          "rate":sr,"samples":len(wave),"voice":"am_michael","speed":0.94,
          "video_assembly":"NOT PERFORMED","full_listening_review":"PENDING",
          "duration_in_45_60_sec_target":45<=duration<=60,
          "captions_srt":"NOT PRODUCED — REQUIRE ACTUAL ALIGNMENT"}
        records.append(record)
        print("SHORT_VOICE_RECORDED",path.name,round(duration,2),flush=True)
    (OUT/"VOICE_ONLY_LEDGER.json").write_text(json.dumps({"source":SOURCE.name,
      "narrations":records,"publication_approved":False,
      "content_warning":"Voice audio only; scene-by-scene directed visual edit is not assembled or reviewed."},indent=2))
    print("TWO_NARRATION_FILES_DONE_NOT_A_VIDEO",flush=True)
if __name__=="__main__":main()
