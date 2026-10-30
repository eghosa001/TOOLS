#!/usr/bin/env python3
"""After-export AV diagnostics for Satisfying Studio.

Runs on the EXACT exported master, before anyone may claim it is ready.
Engineering checks are NOT a claim that footage was watched, that sound was
heard, or that ASMR is satisfying. Human or genuinely audio/video-capable
editorial review is separately required by quality_gate.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from audio_continuity_gate import check_audio


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze(master: Path) -> dict:
    master = master.resolve()
    if not master.is_file() or master.stat().st_size == 0:
        raise ValueError("Missing nonempty final MP4: " + str(master))
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("Both ffmpeg and ffprobe are required for post-render AV diagnostics")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height,avg_frame_rate,sample_rate,channels",
         "-of", "json", str(master)],
        text=True, capture_output=True, check=True, timeout=30,
    )
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if video is None or audio is None:
        raise ValueError("Final master must have decodable video AND audio streams")
    duration = float(metadata.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise ValueError("Cannot determine finished-master duration")

    # Decode the entire video (at reduced analysis resolution). This detects
    # suspicious dark/frozen stretches; it does NOT evaluate material realism.
    filters = "scale=160:-2,blackdetect=d=0.5:pix_th=0.06,freezedetect=n=-60dB:d=1.5"
    diagnostic = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-v", "info", "-i", str(master),
         "-map", "0:v:0", "-an", "-vf", filters, "-f", "null", "-"],
        text=True, capture_output=True, timeout=max(90, min(1200, int(duration * 3))),
    )
    if diagnostic.returncode:
        raise RuntimeError("Full-picture decode/scan failed: " + diagnostic.stderr[-1200:])

    def spans(pattern):
        return [{"start_s": float(a), "end_s": float(b)}
                for a, b in re.findall(pattern, diagnostic.stderr)]

    black = spans(r"black_start:([0-9.]+) black_end:([0-9.]+)")
    freezes = spans(r"freeze_start: ([0-9.]+)\s+freeze_end: ([0-9.]+)")
    # A freeze can extend to EOF without freeze_end.
    open_freezes = re.findall(r"freeze_start: ([0-9.]+)", diagnostic.stderr)
    if len(open_freezes) > len(freezes):
        freezes.append({"start_s": float(open_freezes[-1]), "end_s": duration})

    continuity = check_audio(master)  # full-length decoded actual soundtrack
    warnings = []
    if black:
        warnings.append("Possible dark/black intervals: inspect whether intentional")
    if freezes:
        warnings.append("Possible static/frozen intervals: inspect whether intentional")
    if not continuity.get("passed"):
        warnings.append("Blocking: soundtrack contains >=0.45s near-silent intervals")

    return {
        "schema_version": 1,
        "scan_complete": True,
        "master_sha256": sha256(master),
        "duration_seconds": duration,
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("avg_frame_rate"),
        "audio_sample_rate": audio.get("sample_rate"),
        "audio_channels": audio.get("channels"),
        "audio_continuity": continuity,
        "possible_black_intervals": black,
        "possible_freeze_intervals": freezes,
        "warnings": warnings,
        "unresolved_technical_blockers": (
            ["unwanted soundtrack silence"] if not continuity.get("passed") else []
        ),
        "review_status": "UNAPPROVED — visual, audio and contact-sync editorial inspection outstanding",
        "limitations": (
            "Full decode and signal-level measurements only. This scan cannot hear "
            "Foley, watch tactile physics semantically, verify contact synchrony, "
            "judge attractiveness, or award any artistic score."
        ),
    }


def scan_to_file(master: Path, destination: Path) -> dict:
    result = analyze(master)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("master", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()
    result = scan_to_file(args.master, args.output_json)
    print(json.dumps({
        "master_sha256": result["master_sha256"],
        "scan_complete": True,
        "technical_blockers": result["unresolved_technical_blockers"],
        "warnings": result["warnings"],
        "report": str(args.output_json),
        "review_status": result["review_status"],
    }, indent=2))
    if result["unresolved_technical_blockers"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
