#!/usr/bin/env python3
"""Fast, CPU-only assembler for previously generated manhua panels and narration.

No GPU, AI model, image generation, TTS, story rewriting, or publication.
For multiple images, a timing JSON file is required; durations are not guessed.
Usage:
  python -m video.audiobook_studio.manhua_pipeline.assemble_existing \
    --audio narration_review.m4a --image scene-0000.png \
    --thumbnail THUMBNAIL_REVIEW.png --output review.mp4
  python -m video.audiobook_studio.manhua_pipeline.assemble_existing \
    --audio narration_review.m4a --timeline scene_timeline.json --output review.mp4
Timing JSON: [{"image": "/path/panel1.png", "seconds": 4.2}, ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from video.audiobook_studio.episode_fastlane import atomic_json, probe_media, sha256, validate_review_video


def _input(path: str, kind: str) -> Path:
    p = Path(path).expanduser().resolve(strict=True)
    if not p.is_file() or p.stat().st_size < 1024:
        raise ValueError("Missing or invalid " + kind + ": " + str(p))
    return p


def _audio_info(path: Path) -> tuple[float, str]:
    data = probe_media(path)
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if len(streams) != 1:
        raise ValueError("Expected exactly one narration audio stream")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration < 1 or duration > 4 * 3600:
        raise ValueError("Narration duration out of bounds")
    return duration, streams[0].get("codec_name", "")


def _scenes(args: argparse.Namespace, duration: float) -> list[tuple[Path, float]]:
    if args.timeline and args.image:
        raise ValueError("Use --timeline OR --image, not both")
    if args.timeline:
        source = _input(args.timeline, "timing manifest")
        items = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(items, list) or not items:
            raise ValueError("Timeline must be a non-empty list")
        scenes = []
        for item in items:
            if not isinstance(item, dict) or "image" not in item or "seconds" not in item:
                raise ValueError("Timeline entries require image and seconds")
            name = Path(item["image"])
            if not name.is_absolute():
                name = source.parent / name
            scenes.append((_input(str(name), "scene"), float(item["seconds"])))
    elif args.image and len(args.image) == 1:
        scenes = [(_input(args.image[0], "scene"), duration)]
    else:
        raise ValueError("Use one --image or provide a precise --timeline for multiple images")
    if len(scenes) > 10000 or any(not 0.04 <= seconds <= 4 * 3600 for _, seconds in scenes):
        raise ValueError("Invalid scene count or duration")
    if abs(sum(seconds for _, seconds in scenes) - duration) > 0.30:
        raise ValueError("Scene timeline differs from the actual narration duration")
    for panel, _ in scenes:
        media = probe_media(panel)
        if not any(s.get("codec_type") == "video" and s.get("width", 0) >= 512
                   and s.get("height", 0) >= 288 for s in media.get("streams", [])):
            raise ValueError("Low resolution or invalid scene image: " + panel.name)
    return scenes


def assemble(args: argparse.Namespace) -> dict:
    audio = _input(args.audio, "narration")
    duration, audio_codec = _audio_info(audio)
    scenes = _scenes(args, duration)
    thumbnail = _input(args.thumbnail, "thumbnail") if args.thumbnail else None
    output = Path(args.output).expanduser().resolve()
    if output.suffix.lower() != ".mp4" or output == audio or any(output == p for p, _ in scenes):
        raise ValueError("Output must be a distinct .mp4 path")
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path = output.with_name(output.stem + ".assembly.json")
    inputs = {"audio_sha256": sha256(audio),
              "panels": [{"sha256": sha256(p), "duration_seconds": round(t, 5)}
                         for p, t in scenes],
              "thumbnail_sha256": sha256(thumbnail) if thumbnail else None,
              "codec": "h264", "width": 1920, "height": 1080,
              "fps": 24, "preset": args.preset, "motion": args.motion}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    if not args.force and report_path.is_file() and output.is_file():
        try:
            old = json.loads(report_path.read_text())
            if old.get("inputs_sha256") == key and old.get("video_sha256") == sha256(output):
                checked = validate_review_video(output, expected_audio_seconds=duration,
                                                min_duration_seconds=1.0)
                old.update(status="CPU_ASSEMBLY_CACHE_HIT", cache_hit=True, video=output.name,
                           technical_review=checked)
                print("CPU_ASSEMBLY_CACHE_HIT", json.dumps(old), flush=True)
                return old
        except (ValueError, OSError, subprocess.SubprocessError, KeyError, json.JSONDecodeError):
            pass
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="manhua-assemble-", dir=output.parent) as scratch:
        root = Path(scratch)
        listing = root / "panels.ffconcat"
        lines = ["ffconcat version 1.0"]
        for image, seconds in scenes:
            # ffconcat single quote path escape is cumbersome; reject unsafe source paths.
            if any(ch in str(image) for ch in ("'", "\n", "\r")):
                raise ValueError("Unsafe panel path: " + str(image))
            lines.extend(["file '" + str(image) + "'", "duration " + f"{seconds:.6f}"])
        lines.append("file '" + str(scenes[-1][0]) + "'")
        listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
        vf = ("fps=24,scale=1920:1080:force_original_aspect_ratio=decrease,"
              "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p")
        if args.motion == "subtle":
            vf = ("scale=1920:1080:force_original_aspect_ratio=increase,"
                  "crop=1920:1080,fps=24,"
                  "zoompan=z='min(zoom+0.00008,1.06)':d=1:"
                  "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                  "s=1920x1080:fps=24,format=yuv420p")
        pending = root / "review.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
               "-safe", "0", "-f", "concat", "-i", str(listing),
               "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
               "-vf", vf, "-c:v", "libx264", "-preset", args.preset,
               "-crf", "21", "-r", "24",
               "-c:a", "copy" if audio_codec == "aac" else "aac"]
        if audio_codec != "aac":
            cmd.extend(["-b:a", "160k"])
        cmd.extend(["-t", f"{duration:.4f}", "-movflags", "+faststart", str(pending)])
        subprocess.run(cmd, check=True, timeout=max(120, int(duration * 6)))
        checked = validate_review_video(pending, expected_audio_seconds=duration,
                                        min_duration_seconds=1.0)
        os.replace(pending, output)
    elapsed = round(time.monotonic() - started, 3)
    if thumbnail:
        dest = output.with_name(output.stem + ".thumbnail" + thumbnail.suffix.lower())
        if dest.resolve() != thumbnail:
            shutil.copy2(thumbnail, dest)
    result = {"status": "CPU_ASSEMBLY_PASS", "video": output.name,
              "audio_input": audio.name, "scene_count": len(scenes),
              "duration_seconds": checked["duration_seconds"],
              "assembly_seconds": elapsed, "cache_hit": False,
              "inputs_sha256": key, "video_sha256": sha256(output),
              "technical_review": checked,
              "gpu_used": False, "tts_run": False, "image_generation_run": False,
              "human_review_completed": False, "ready_for_youtube": False}
    atomic_json(report_path, result)
    print("CPU_ASSEMBLY_PASS", json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--image", action="append", help="A single existing image")
    ap.add_argument("--timeline", help="JSON list of image + seconds for multiple scenes")
    ap.add_argument("--thumbnail", help="Optional existing thumbnail, copied without regeneration")
    ap.add_argument("--output", required=True)
    ap.add_argument("--motion", choices=["none", "subtle"], default="none")
    ap.add_argument("--preset", choices=["ultrafast", "superfast", "veryfast", "fast"],
                    default="ultrafast")
    ap.add_argument("--force", action="store_true")
    assemble(ap.parse_args())


if __name__ == "__main__":
    main()
