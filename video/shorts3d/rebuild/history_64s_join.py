#!/usr/bin/env python3
"""Combine saved Kaggle Godot 64s footage with independently generated Qwen CPU narration."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess

from history_64s_audio_cpu import SOURCES, ROOT


def command(*args: object, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run([str(arg) for arg in args], check=True, timeout=timeout,
                          capture_output=True, text=True)


def metadata(path: Path) -> dict:
    return json.loads(command(
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate,channels,sample_rate",
        "-of", "json", path
    ).stdout)


def validate(video: Path, audio: Path) -> dict:
    v, a = metadata(video), metadata(audio)
    vids = [s for s in v["streams"] if s["codec_type"] == "video"]
    snds = [s for s in a["streams"] if s["codec_type"] == "audio"]
    assert len(vids) == 1 and len(snds) == 1
    assert (vids[0]["width"], vids[0]["height"]) == (720, 1280)
    assert vids[0]["r_frame_rate"] == "30/1"
    assert 63.8 <= float(v["format"]["duration"]) <= 64.2
    assert snds[0]["sample_rate"] == "48000" and snds[0]["channels"] == 2
    assert 63.8 <= float(a["format"]["duration"]) <= 64.2
    return {"source_video": v, "source_qwen_audio": a}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--topic", choices=list(SOURCES), required=True)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--audio", type=Path, required=True)
    p.add_argument("--outdir", type=Path, required=True)
    args = p.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    qa = validate(args.video, args.audio)
    output = args.outdir / (args.topic + "-64s-GODOT-QWEN-REVIEW.mp4")
    command("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", args.video, "-i", args.audio, "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
            "-ar", "48000", "-t", "64", "-movflags", "+faststart", output,
            timeout=350)
    out = metadata(output)
    assert len(out["streams"]) == 2, out
    assert 63.8 <= float(out["format"]["duration"]) <= 64.2, out
    frames = []
    spec = json.loads((ROOT / "storyboards" / SOURCES[args.topic]).read_text())
    for shot in spec["shots"]:
        seconds = (shot["start_seconds"] + shot["end_seconds"]) / 2
        thumbnail = args.outdir / (shot["id"] + "-midpoint.jpg")
        command("ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-ss", f"{seconds:.3f}", "-i", output, "-frames:v", "1",
                "-q:v", "5", thumbnail, timeout=40)
        assert thumbnail.stat().st_size > 1000
        frames.append({"shot": shot["id"], "image": thumbnail.name, "caption": shot["caption"]})
    silence = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(args.audio),
         "-af", "silencedetect=noise=-37dB:d=0.8", "-f", "null", "-"],
        capture_output=True, text=True, timeout=60,
    )
    qa["final_video"] = out
    qa["sampled_frames"] = frames
    qa["long_audio_silences"] = [
        l.strip() for l in silence.stderr.splitlines() if "silence_duration:" in l
    ]
    qa["audio_silence_gate"] = "PASS" if not qa["long_audio_silences"] else "REVIEW_REQUIRED"
    qa["technical_mux_ok"] = True
    qa["visual_reference_parity_approved"] = False
    qa["narration_scene_match_approved"] = False
    qa["publication_approved"] = False
    qa["status"] = "FULL_DURATION_QWEN_GODOT_REVIEW_VIDEO_NOT_RELEASE_APPROVED"
    qa["warning"] = (
        "Existing Godot reconstructions are reused. Technical mux success DOES NOT "
        "prove that the named historical actions and set details match the narrated claims."
    )
    (args.outdir / "review-qa.json").write_text(json.dumps(qa, indent=2) + "\n")
    print("FULL_LENGTH_QWEN_GODOT_REVIEW_CREATED", output, output.stat().st_size)


if __name__ == "__main__":
    main()
