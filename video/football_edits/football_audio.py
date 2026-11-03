#!/usr/bin/env python3
"""Universal football narration pacing and verification. Never generates a video.

Reads the single canonical audio tempo (1.35) from football_video_defaults.json.
Applies FFmpeg atempo to Qwen Ryan WAV/AAC files without changing pitch.
Run only for a NEW requested video. Do not mutate already approved old exports.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def audio_policy():
    policy=Path(__file__).with_name("football_video_defaults.json")
    data=json.loads(policy.read_text(encoding="utf-8"))
    a=data["audio"]
    if not (a["tempo"]==1.35 and a["pitch_preserving"] is True and
            a["speaker"]=="Ryan" and a["model"]=="Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"):
        raise RuntimeError("The canonical football-audio policy is inconsistent")
    return a

def process(input_path:Path,output_path:Path):
    a=audio_policy()
    if not input_path.is_file() or input_path.stat().st_size==0:
        raise FileNotFoundError("Actual generated source voice recording is missing")
    if input_path.resolve()==output_path.resolve():
        raise ValueError("Never overwrite raw Qwen audio; write a separate review file")
    if output_path.exists():
        raise FileExistsError("Do not overwrite an earlier approved voice recording")
    output_path.parent.mkdir(parents=True,exist_ok=True)
    # FFmpeg atempo is pitch preserving (different from naive sample-rate changes).
    args=["ffmpeg","-hide_banner","-loglevel","error","-n","-i",str(input_path),
          "-filter:a",f"atempo={a['tempo']:.2f},aresample=48000","-ac","1",
          "-c:a","pcm_s16le",str(output_path)]
    subprocess.run(args,check=True,timeout=300)
    if output_path.stat().st_size<12000:
        raise RuntimeError("Processed Qwen narration unexpectedly small")
    return {"input":str(input_path),"output":str(output_path),"speaker":a["speaker"],
            "tempo":a["tempo"],"pitch_preserving":True}

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--show-defaults",action="store_true")
    cli.add_argument("--input",type=Path)
    cli.add_argument("--output",type=Path)
    args=cli.parse_args()
    try:
        if args.show_defaults:
            print(json.dumps(audio_policy(),indent=2))
            return 0
        if args.input is None or args.output is None:
            cli.error("--input and --output required unless --show-defaults")
        print(json.dumps(process(args.input,args.output),indent=2))
        return 0
    except (OSError,RuntimeError,subprocess.CalledProcessError,ValueError) as exc:
        print("FOOTBALL_NARRATION_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
