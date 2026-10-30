#!/usr/bin/env python3
"""Offline audio/video signal QA shared by ALL 47 original-CGI ASMR formats.

Checks decoded *master* audio (integrated loudness/true peak and stream metadata)
and existing sampled CGI frame diagnostics. Does not pretend to hear Foley,
inspect realistic fractures, or approve contact synchrony or artistic quality.
All thresholds are conservative studio engineering heuristics, NOT YouTube
standards. Runtime relies only on installed ffmpeg/ffprobe and the studio
format catalogue; no model/API/Internet/extra downloads required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_formats import get_format, catalogue

# A professional macro video is not a uniform lighting or audio profile.
# Below are checks that the director needs to actively observe by group.
DIRECTOR_REQUIREMENTS = {
    "fracture": ("shard volumes, blade contacts, material cut planes and debris",
                 "physical snap attack, genuine fracture timbre and proportional decay"),
    "deformation": ("actual mesh volume, collisions, fine tactile skin and rebound",
                    "matching squeeze/relax audio envelope; no misplaced crunchy impact"),
    "particle-fluid": ("actual particle/mesh fluid or granular surface, turbulence and lighting",
                       "real fluid/grain movement and source-specific close recorded sound"),
    "mechanical": ("rigid contact without intersections, track fit and visible press points",
                   "material-specific clicks with correct speed, scale and intensity"),
    "transformation": ("geometry genuinely changes and transformation is causally visible",
                       "progressive cleaning/processing acoustics and natural pauses"),
    "capture": ("fully original synthetic 3D craft/tools/hands, not filmed video",
                "licensed real tool/contact Foley that matches rendered material"),
    "sound-first": ("camera supports the gesture without hiding the tapping/brushing surface",
                    "real close-mic recorded exact trigger, no manufactured noise fill"),
    "ambient": ("credible original 3D environment, genuine volumetric/weather motion",
                "appropriate continuous licensed source ambience without short identical loops"),
    "performance": ("credible original CGI face/body/jaw gesture, no real filmed person",
                    "consented/licensed voice or body source with actual gesture lip/hand sync"),
    "editorial": ("distinctive genuinely rendered CGI takes; no repeated stock/filler",
                  "correct independent Foley source for every take and natural transitions"),
}

# FFmpeg EBU R128 integrated loudness and true peak. Lower number = softer.
# Intentionally not treated as a material-realism or artistic-quality rating.
# Hard failures are for objectively potentially unsafe signal extremes only.
MAX_TRUE_PEAK_DBTP = -1.0
MAX_INTEGRATED_LUFS = -8.0
MIN_INTEGRATED_LUFS = -50.0
SOFT_TRUE_PEAK_DBTP = -2.0
SOFT_LOUD_LUFS = -13.0
SOFT_QUIET_LUFS = -32.0
BASELINE_LUMA_MIN = 22.0
BASELINE_LUMA_MAX = 235.0


def formats_covered() -> dict:
    items = catalogue()["formats"]
    missing = sorted(set(x["group"] for x in items) - set(DIRECTOR_REQUIREMENTS))
    if len(items) != 47 or missing:
        raise ValueError(f"Expected 47 mapped genres; unhandled families: {missing}")
    return {item["id"]: {
        "group": item["group"],
        "material": item["material"],
        "action": item["action"],
        "foley": item["foley"],
        "solver": item["required_evidence_solver"],
        "visual_director_check": DIRECTOR_REQUIREMENTS[item["group"]][0],
        "audio_director_check": DIRECTOR_REQUIREMENTS[item["group"]][1],
        "cgi_only": True,
        "needs_genuine_recorded_sound": True,
        "needs_actual_headphone_and_picture_review": True,
        "user_media_required": False,
    } for item in items}


def _number(string: str):
    try:
        number = float(string)
    except (ValueError, TypeError):
        return None
    return round(number, 2) if math.isfinite(number) else None


def parse_ebur128_summary(stderr: str) -> dict:
    """Parse only LAST EBU R128 Summary, not incidental momentary frames.

    Sample FFmpeg output has multiple I:/Peak: fields outside the summary.
    Parsing the summary's labelled subsections avoids false loudness values.
    """
    if "Summary:" not in stderr:
        raise ValueError("No EBU R128 summary: audio decode or filter unavailable")
    summary = stderr.rsplit("Summary:", 1)[-1]
    integrated = re.search(
        r"Integrated loudness:\s*I:\s*(-?(?:\d+(?:\.\d+)?|inf))\s+LUFS", summary, re.I)
    true_peak = re.search(
        r"True peak:\s*Peak:\s*(-?(?:\d+(?:\.\d+)?|inf))\s+dBFS", summary, re.I)
    if not integrated or not true_peak:
        raise ValueError("Missing integrated loudness or true peak in FFmpeg EBU R128 report")
    return {
        "integrated_loudness_lufs": _number(integrated.group(1)),
        "true_peak_dbtp": _number(true_peak.group(1)),
        "method": "ffmpeg ebur128=peak=true; entire actual encoded soundtrack",
        "is_an_auditory_review": False,
    }


def analyze_sound(master: Path, *, timeout=None) -> dict:
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-v", "info", "-i", str(master),
           "-map", "0:a:0", "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=timeout or 1200)
    if result.returncode:
        raise RuntimeError("Full-master EBU R128 audio analysis failed: " +
                           result.stderr[-1200:])
    return parse_ebur128_summary(result.stderr)


def assess(format_id: str, video: dict, audio: dict) -> dict:
    profiles = formats_covered()
    if format_id not in profiles:
        raise ValueError(f"Unregistered ASMR format {format_id!r}")
    profile = profiles[format_id]
    blockers = []
    warnings = []
    tp = audio.get("true_peak_dbtp")
    loudness = audio.get("integrated_loudness_lufs")
    if tp is None or loudness is None:
        blockers.append("No measurable audible audio energy / true-peak evidence")
    else:
        if tp > MAX_TRUE_PEAK_DBTP:
            blockers.append("True-peak exceeds -1 dBTP engineering safety ceiling")
        elif tp > SOFT_TRUE_PEAK_DBTP:
            warnings.append("True-peak above -2 dBTP preferred mastering margin")
        if loudness > MAX_INTEGRATED_LUFS:
            blockers.append("Soundtrack excessively loud: above -8 LUFS")
        elif loudness > SOFT_LOUD_LUFS:
            warnings.append("Soundtrack is loud for many gentle ASMR scenes; audition force/intensity")
        if loudness < MIN_INTEGRATED_LUFS:
            blockers.append("Soundtrack effectively inaudible: below -50 LUFS")
        elif loudness < SOFT_QUIET_LUFS:
            warnings.append("Very quiet ASMR recording; check phone-speaker audibility")
    frames = video.get("frames_sampled")
    if not isinstance(frames, int) or frames <= 0:
        blockers.append("No decoded picture frame diagnostic available")
    else:
        lum = video.get("luminance_mean")
        edges = video.get("strong_local_gradient_fraction")
        if isinstance(lum, (int, float)) and (lum < BASELINE_LUMA_MIN or lum > BASELINE_LUMA_MAX):
            warnings.append("Potentially underexposed/washed out image; check material and artistic intent")
        if isinstance(edges, (int, float)) and edges < 0.012:
            warnings.append("Very low local gradient content: may indicate flat CGI or intended defocus")
        if frames < 3:
            warnings.append("Few frames sampled; contact and camera movement need fuller review")
    return {
        "format_id": format_id,
        "studio_profile": profile,
        "blocking_signal_issues": blockers,
        "editorial_investigation_flags": warnings,
        "signal_preflight_passed": not blockers,
        "creative_approval": False,
        "physical_timbre_verified": False,
        "audio_action_sync_verified": False,
        "visual_reference_parity_verified": False,
        "quality_standard": ">=9/10 each of nine actual full audiovisual review criteria",
        "meaning": "Signal diagnostics only. This report never releases or approves a CGI ASMR video.",
    }


def analyze_master(master: Path, format_id: str, video: dict, *, timeout=None) -> dict:
    return assess(format_id, video, analyze_sound(master, timeout=timeout))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("master", type=Path, nargs="?")
    p.add_argument("--format", dest="format_id")
    p.add_argument("--frame-diagnostics", type=Path,
                   help="JSON output of post_render_av_review.cgi_frame_diagnostics")
    p.add_argument("--list-profiles", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    if args.list_profiles:
        print(json.dumps(formats_covered(), indent=2))
        return 0
    if not args.master or not args.format_id or not args.frame_diagnostics:
        p.error("master, --format and --frame-diagnostics required unless --list-profiles")
    try:
        report = analyze_master(args.master, args.format_id,
                                json.loads(args.frame_diagnostics.read_text()))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0 if report["signal_preflight_passed"] else 2
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
