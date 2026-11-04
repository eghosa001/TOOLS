#!/usr/bin/env python3
"""Require a real 9:16 display aspect ratio before uploading a history Short.

Encoded dimensions alone are insufficient: 1080x1920 with SAR 64:27
displays as 4:3 and can be classified as a regular YouTube video.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess


def assess(width: int, height: int, sar: str, duration: float, audio: bool) -> dict:
    errors: list[str] = []
    try:
        sample_aspect = Fraction(str(sar or "1:1").replace(":", "/"))
        if sample_aspect <= 0:
            raise ValueError("Nonpositive SAR")
    except (ValueError, ZeroDivisionError):
        errors.append("Missing or invalid sample aspect ratio (SAR)")
        sample_aspect = Fraction(1, 1)
    if width <= 0 or height <= 0:
        errors.append("Invalid video frame dimensions")
        width, height = max(width, 1), max(height, 1)
    displayed_ratio = float(Fraction(width, height) * sample_aspect)
    if sample_aspect != 1:
        errors.append(f"Non-square pixels: SAR {sar} changes display aspect ratio")
    if abs(displayed_ratio - 9 / 16) > 0.01:
        errors.append(f"Display aspect is {displayed_ratio:.4f}, not 9:16")
    if width < 720 or height < 1280:
        errors.append("History Shorts must be at least 720x1280")
    if not 0 < duration <= 180:
        errors.append("A YouTube Short must run for 0 to 180 seconds")
    if not audio:
        errors.append("History Short is missing its narration/audio stream")
    return {
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
        "width": width, "height": height,
        "sample_aspect_ratio": sar,
        "display_aspect_ratio": displayed_ratio,
        "duration_seconds": duration,
        "audio_stream_present": audio,
    }


def verify(video: Path) -> dict:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,width,height,sample_aspect_ratio:format=duration",
            "-of", "json", str(video)
        ], check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        picture = next(s for s in data["streams"] if s["codec_type"] == "video")
        audio = any(s["codec_type"] == "audio" for s in data["streams"])
        return assess(int(picture["width"]), int(picture["height"]),
                      picture.get("sample_aspect_ratio") or "N/A",
                      float(data["format"]["duration"]), audio)
    except (OSError, subprocess.CalledProcessError, KeyError, ValueError,
            StopIteration, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"Unable to probe Short: {exc}"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    args = parser.parse_args()
    outcome = verify(args.video)
    print(json.dumps(outcome, indent=2))
    return 0 if outcome["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
