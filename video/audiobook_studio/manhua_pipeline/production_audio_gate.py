#!/usr/bin/env python3
"""Fail-closed loudness preparation for new Mythveil episodes.

Only audio mastering (level/dynamics) is performed: no speech text, voice,
duration, or speed changes. Never overwrite the approved source narration.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

TARGET_LUFS = -16.0
MIN_LUFS, MAX_LUFS = -18.5, -13.5
MAX_TRUE_PEAK_DBFS = -1.0
MASTER_VERSION = "voice_loudnorm_16lu_1p5tp_v1"


def measured_loudness(audio: Path) -> dict:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "info",
         "-i", str(audio), "-map", "0:a:0", "-vn",
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, check=True, timeout=240,
    )
    # FFmpeg prints interim window statistics; the final Summary is authoritative.
    summary = result.stderr.rsplit("Summary:", 1)
    if len(summary) != 2:
        raise ValueError("LOUDNESS_MEASUREMENT_MISSING: no final EBU R128 summary")
    block = summary[-1]
    integrated = re.search(r"Integrated loudness:.*?I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", block, re.S)
    peak = re.search(r"True peak:.*?Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS", block, re.S)
    if not integrated or not peak:
        raise ValueError("LOUDNESS_MEASUREMENT_MISSING: integrated LUFS / true peak")
    return {"integrated_lufs": float(integrated.group(1)),
            "true_peak_dbfs": float(peak.group(1))}


def acceptable(stats: dict) -> bool:
    return (MIN_LUFS <= stats["integrated_lufs"] <= MAX_LUFS
            and stats["true_peak_dbfs"] <= MAX_TRUE_PEAK_DBFS)


def mastered_voice(source: Path, cache_dir: Path) -> tuple[Path, dict]:
    """Reuse correctly mastered speech, or normalize an immutable copy and check it."""
    source = Path(source).resolve(strict=True)
    initial = measured_loudness(source)
    if acceptable(initial):
        return source, {"status": "SOURCE_ALREADY_MASTERED", "source": initial,
                        "final": initial, "target_lufs": TARGET_LUFS}
    h = hashlib.sha256()
    with source.open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(block)
    cache_dir.mkdir(parents=True, exist_ok=True)
    name = f".{source.stem}.{h.hexdigest()[:16]}.{MASTER_VERSION}.flac"
    path = cache_dir / name
    if path.is_file() and path.stat().st_size > 30000:
        final = measured_loudness(path)
        if acceptable(final):
            return path, {"status": "CACHED_MASTERED_COPY", "source": initial,
                          "final": final, "target_lufs": TARGET_LUFS}
    temp = path.with_name(path.name + ".partial.flac")
    try:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
             "-i", str(source), "-map", "0:a:0", "-vn",
             "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             "-c:a", "flac", "-ar", "48000", str(temp)],
            check=True, timeout=240,
        )
        final = measured_loudness(temp)
        if not acceptable(final):
            raise ValueError(f"LOUDNESS_MASTERING_FAILED: {final}; expected "
                             f"{MIN_LUFS}..{MAX_LUFS} LUFS and TP <= {MAX_TRUE_PEAK_DBFS}")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return path, {"status": "MASTERED_COPY_VALIDATED", "source": initial,
                  "final": final, "target_lufs": TARGET_LUFS}
