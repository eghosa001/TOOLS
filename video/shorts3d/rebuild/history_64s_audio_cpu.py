#!/usr/bin/env python3
"""Recover 64-second history narration with Qwen3-TTS on free GitHub CPU.

The two Kaggle GPU jobs successfully saved silent Godot AVIs, then failed inside
Qwen/Torch CUDA sampling. This job creates REAL Qwen speech on CPU without
re-rendering or paying for another GPU session. No fallback/synthetic silence.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

# This must precede importing PyTorch to rule out the failed Kaggle CUDA path.
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rebuild.validate_storyboards import verify

SOURCES = {
    "london": "great-fire-london-64s.json",
    "constantinople": "constantinople-64s.json",
}
MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"


def voice_spec(storyboard: dict) -> dict:
    assert storyboard["seconds"] == 64
    shots = storyboard["shots"]
    assert len(shots) == 12
    return {
        "seconds": 64,
        "audio": {
            "model": MODEL,
            "speaker": "Ryan",
            "language": "English",
            "instruct": "Clear, brisk, natural English historical documentary narration.",
        },
        "shots": [
            {
                "id": shot["id"],
                "start": shot["start_seconds"],
                "end": shot["end_seconds"],
                "spoken": shot["spoken"],
            }
            for shot in shots
        ],
    }


def probe_audio(path: pathlib.Path) -> dict:
    info = json.loads(subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,channels,sample_rate",
            "-of", "json", str(path),
        ],
        text=True,
    ))
    streams = [stream for stream in info["streams"] if stream["codec_type"] == "audio"]
    assert len(streams) == 1, info
    audio = streams[0]
    assert audio["sample_rate"] == "48000", info
    assert audio["channels"] == 2, info
    assert abs(float(info["format"]["duration"]) - 64) <= .15, info
    return info


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", choices=list(SOURCES), required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    source = ROOT / "storyboards" / SOURCES[args.topic]
    verify(source)
    spec = voice_spec(json.loads(source.read_text(encoding="utf-8")))
    args.out.mkdir(parents=True, exist_ok=True)
    if args.validate_only:
        print("STORYBOARD_AND_QWEN_CPU_SPEC_OK", args.topic, len(spec["shots"]))
        return

    # qwen_audio.generate chooses float32 whenever CUDA is unavailable.
    # This eliminates the float16 / CUDA decoding failure seen in both Kaggle
    # notebooks; it does not pretend that a CPU output exists until it does.
    import torch
    assert not torch.cuda.is_available(), "CPU narration isolation failed"
    from qwen_audio import generate, mix_authored_timeline
    print("QWEN_REAL_MODEL_CPU", MODEL, "torch", torch.__version__, flush=True)
    clips = args.out / "individual_qwen_shots"
    cache = args.out / "qwen_cache"
    generate(spec, clips, cache)
    wav = args.out / (args.topic + "-qwen-64s-stereo.wav")
    timing = mix_authored_timeline(spec, clips, wav)
    evidence = probe_audio(wav)
    report = {
        "status": "QWEN_64S_CPU_AUDIO_GENERATED_NOT_ARTISTICALLY_APPROVED",
        "topic": args.topic,
        "qwen_model": MODEL,
        "speaker": "Ryan",
        "device": "cpu",
        "all_shots": len(spec["shots"]),
        "shot_timing": timing,
        "audio_probe": evidence,
        "audio_listening_approved": False,
        "visual_narrative_approved": False,
    }
    (args.out / "qwen-64s-audio-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print("VERIFIED_REAL_QWEN_64S_STEREO", wav, wav.stat().st_size, flush=True)


if __name__ == "__main__":
    main()
