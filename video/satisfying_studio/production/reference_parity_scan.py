#!/usr/bin/env python3
"""Low-bandwidth CGI benchmark diagnostics. NEVER awards artistic ASMR approval."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

FRAME_WIDTH, FRAME_HEIGHT = 180, 320
RATE, WINDOW = 8000, 800

def shell(cmd, timeout=90):
    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stderr or b"FFmpeg failed")[-1200:].decode("utf-8", errors="replace"))
    return result.stdout

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def media(path):
    raw = shell(["ffprobe", "-v", "error", "-show_entries",
                 "format=duration:stream=codec_type,width,height,avg_frame_rate,sample_rate",
                 "-of", "json", str(path)])
    data = json.loads(raw)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("Video stream missing")
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {"duration_seconds": float(data["format"]["duration"]),
            "width": int(video["width"]), "height": int(video["height"]),
            "frame_rate": video.get("avg_frame_rate", ""),
            "audio_stream": bool(audio),
            "audio_sample_rate": audio.get("sample_rate") if audio else None}

def frame_metrics(path):
    raw = shell(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-an",
                 "-vf", f"fps=1,scale={FRAME_WIDTH}:{FRAME_HEIGHT},format=gray",
                 "-f", "rawvideo", "-pix_fmt", "gray", "-"], timeout=160)
    size = FRAME_WIDTH * FRAME_HEIGHT
    frames = [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]
    if not frames:
        raise ValueError("No frames decoded")
    lums, contrasts, edges = [], [], []
    for frame in frames:
        values = frame[::8]
        lums.append(statistics.fmean(values))
        contrasts.append(statistics.pstdev(values))
        strong = 0
        total = 0
        for y in range(4, FRAME_HEIGHT - 4, 4):
            row = y * FRAME_WIDTH
            for x in range(4, FRAME_WIDTH - 4, 4):
                p = row + x
                strong += (abs(frame[p] - frame[p + 4]) > 25 or
                           abs(frame[p] - frame[p + FRAME_WIDTH * 4]) > 25)
                total += 1
        edges.append(strong / max(1, total))
    return {"frames_sampled": len(frames),
            "luminance_mean": round(statistics.fmean(lums), 2),
            "luminance_contrast": round(statistics.fmean(contrasts), 2),
            "strong_local_gradient_fraction": round(statistics.fmean(edges), 4)}

def audio_metrics(path, available):
    if not available:
        return {"rms_dbfs_p10": None, "rms_dbfs_p50": None,
                "rms_dbfs_p90": None, "near_silent_fraction": 1.0}
    raw = shell(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-vn",
                 "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], timeout=160)
    data = array("h")
    data.frombytes(raw[:(len(raw) // 2) * 2])
    levels = []
    for i in range(0, len(data) - WINDOW + 1, WINDOW):
        segment = data[i:i + WINDOW]
        rms = math.sqrt(math.fsum((v / 32768) ** 2 for v in segment) / len(segment))
        levels.append(20 * math.log10(max(1e-9, rms)))
    if not levels:
        return {"rms_dbfs_p10": None, "rms_dbfs_p50": None,
                "rms_dbfs_p90": None, "near_silent_fraction": 1.0}
    ordered = sorted(levels)
    percentile = lambda q: round(ordered[int(q * (len(ordered) - 1))], 1)
    return {"rms_dbfs_p10": percentile(.1),
            "rms_dbfs_p50": percentile(.5),
            "rms_dbfs_p90": percentile(.9),
            "near_silent_fraction": round(sum(v <= -55 for v in levels) / len(levels), 3)}

def audit(path):
    if not path.is_file():
        raise FileNotFoundError(path)
    info = media(path)
    return {"sha256": sha256(path), **info, **frame_metrics(path),
            **audio_metrics(path, info["audio_stream"])}

def compare(candidate, reference):
    """Warnings are diagnostic, NOT genre-independent judgments of artistic quality."""
    warnings = []
    if not candidate["audio_stream"]:
        warnings.append("MISSING AUDIO: release blocker")
    if candidate["width"] < reference["width"] or candidate["height"] < reference["height"]:
        warnings.append("Reference has higher native resolution; inspect real macro detail")
    if candidate["luminance_mean"] < reference["luminance_mean"] * .6:
        warnings.append("Candidate considerably darker; check subject exposure, accounting for genre")
    if (candidate["strong_local_gradient_fraction"] <
            reference["strong_local_gradient_fraction"] * .55):
        warnings.append("Candidate has fewer local gradients; check microdetail, accounting for genre")
    warnings.append("NOT an artistic parity score; real full playback and headphone review required")
    return warnings

def produce(candidate, references):
    c = audit(candidate)
    comparisons = []
    for path in references:
        r = audit(path)
        comparisons.append({"reference": r, "warnings": compare(c, r)})
    return {"schema_version": 1, "candidate": c, "comparisons": comparisons,
            "candidate_release_approved": False,
            "limitations": "Cheap diagnostics only. Results do not verify source material, Foley timbre, simulation realism, copyright rights or full audiovisual parity. References must be authorized local files."}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--reference", type=Path, action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg/FFprobe required")
    report = produce(args.candidate, args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.output), "sources": len(report["comparisons"]) + 1,
                      "audio_present": report["candidate"]["audio_stream"],
                      "artistic_approval": False}, indent=2))
    return 0 if report["candidate"]["audio_stream"] else 2

if __name__ == "__main__":
    sys.exit(main())
