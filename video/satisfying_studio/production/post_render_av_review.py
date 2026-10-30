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

try:
    from .audio_continuity_gate import check_audio
    from .reference_parity_scan import frame_metrics
    from .av_signal_quality import analyze_master
except ImportError:  # standalone CLI execution from production/
    from audio_continuity_gate import check_audio
    from reference_parity_scan import frame_metrics
    from av_signal_quality import analyze_master


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def analyze(master: Path, format_id: str | None = None) -> dict:
    master = master.resolve()
    if not master.is_file() or master.stat().st_size == 0:
        raise ValueError("Missing nonempty final MP4: " + str(master))
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("Both ffmpeg and ffprobe are required for post-render AV diagnostics")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height,avg_frame_rate,sample_rate,channels",
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
    # A single master hash binds video and audio to any genre-specific report.
    frames = frame_metrics(master)
    signal = analyze_master(master, format_id, frames,
                            timeout=max(90, min(1200, int(duration * 4)))) if format_id else None
    warnings = []
    if black:
        warnings.append("Possible dark/black intervals: inspect whether intentional")
    if freezes:
        warnings.append("Possible static/frozen intervals: inspect whether intentional")
    if not continuity.get("passed"):
        warnings.append("Blocking: soundtrack contains >=0.45s near-silent intervals")

    blockers = ["unwanted soundtrack silence"] if not continuity.get("passed") else []
    if signal:
        blockers.extend(signal["blocking_signal_issues"])
        warnings.extend(signal["editorial_investigation_flags"])
        # AAC and picture can appear technically valid with a missing tail.
        # Four-frame drift is a hard problem for exact-material close-up ASMR.
        sound_duration = continuity.get("duration_s")
        if not isinstance(sound_duration, (int, float)):
            blockers.append("Missing full decoded audio duration evidence")
        elif abs(float(sound_duration) - duration) > .10:
            blockers.append("Picture/audio duration mismatch exceeds 100 ms")
        if video.get("avg_frame_rate") != "24/1":
            blockers.append("Registered CGI master must use true constant 24 fps")
        if str(audio.get("sample_rate")) != "48000" or audio.get("channels") != 2:
            blockers.append("Registered CGI soundtrack must be 48 kHz stereo")
        if video.get("codec_name") != "h264" or audio.get("codec_name") != "aac":
            blockers.append("Registered CGI delivery must use H.264 video and AAC audio")

    return {
        "schema_version": 1,
        "format_id": format_id,
        "master_signal_qa": signal,
        "scan_complete": True,
        "master_sha256": sha256(master),
        "duration_seconds": duration,
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": video.get("avg_frame_rate"),
        "audio_sample_rate": audio.get("sample_rate"),
        "audio_channels": audio.get("channels"),
        "audio_continuity": continuity,
        # Objective sampled image information, not an artist score or reference
        # comparison. It helps flag underlit, flat, low-detail CGI for review.
        "cgi_frame_diagnostics": frames,
        "possible_black_intervals": black,
        "possible_freeze_intervals": freezes,
        "warnings": warnings,
        "unresolved_technical_blockers": blockers,
        "review_status": "UNAPPROVED — visual, audio and contact-sync editorial inspection outstanding",
        "limitations": (
            "Full decode and signal-level measurements only. This scan cannot hear "
            "Foley, watch tactile physics semantically, verify contact synchrony, "
            "judge attractiveness, or award any artistic score. Signal checks " 
            "cannot prove a human watched or heard the footage."
        ),
    }


def scan_to_file(master: Path, destination: Path, format_id: str | None = None) -> dict:
    result = analyze(master, format_id=format_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("master", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--format", dest="format_id", help="Registered 47-format CGI QA profile")
    args = parser.parse_args()
    result = scan_to_file(args.master, args.output_json, format_id=args.format_id)
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
