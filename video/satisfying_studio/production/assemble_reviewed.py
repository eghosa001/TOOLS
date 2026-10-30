#!/usr/bin/env python3
"""Assemble genuinely editor-selected AV takes for any registered ASMR format.

This NEVER creates source clips, chooses stock media, selects a creative
timeline, or fabricates Foley. It joins only fully timecoded, reviewed,
SHA-bound, ORIGINAL/cleared takes with their already contact-matched audio.
Every export is rescanned and remains UNAPPROVED until quality_gate release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_formats import safe_file, sha256, inspect_assets, StudioFormatError
from quality_gate import load_plan, GateError, require_composition
from production.post_render_av_review import scan_to_file


class AssemblyBlocked(ValueError):
    pass


def demand(condition, message):
    if not condition:
        raise AssemblyBlocked(message)


def inspect_take(take: Path, frames: int, aspect: str) -> None:
    """Check actual encoded media; do not silently crop/resample framing."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames",
         "-show_entries", "stream=codec_type,codec_name,width,height,avg_frame_rate,"
         "sample_rate,channels,nb_read_frames:format=duration",
         "-of", "json", str(take)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    info = json.loads(proc.stdout)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    demand(video is not None and audio is not None,
           "Shot has no complete picture and original or accurately edited soundtrack: " + str(take))
    demand(video.get("codec_name") == "h264" and video.get("avg_frame_rate") == "24/1",
           "All takes need actual H.264 24 fps source; separately conform takes under editor oversight")
    demand(int(video.get("nb_read_frames") or 0) == frames,
           "Shot frame count differs from approved editorial timing: " + str(take))
    demand(audio.get("sample_rate") == "48000" and audio.get("channels") == 2,
           "All takes need 48kHz stereo matching Foley or recorded in-shot sound")
    width, height = (1280, 720) if aspect == "16:9" else (720, 1280)
    demand(int(video.get("width") or 0) == width and
           int(video.get("height") or 0) == height,
           f"No auto crop: shot must already be composition-approved {width}x{height}")
    duration = float(info.get("format", {}).get("duration") or 0)
    demand(abs(duration - frames / 24) <= .075,
           "Shot encode duration diverges from approved frame count")


def validate(manifest: Path, probe=True) -> tuple[dict, Path, list[Path]]:
    plan, root = load_plan(manifest)
    demand(bool(plan.get("format_id")),
           "Only registered ASMR formats accepted; legacy assembly remains separate")
    issues = inspect_assets(plan, root)
    demand(not issues, "Source/Foley preflight failed: " + "; ".join(issues))
    demand(plan.get("manual_timeline_approved") is True,
           "No automated creative video assembly. Editor must explicitly approve exact shot order")
    duration = plan["duration_seconds"]
    fps = plan.get("fps", 24)
    demand(fps == 24, "This studio joins 24fps editorial takes only")
    aspect = plan.get("aspect_ratio", "9:16")
    shots = plan["manually_directed_shots"]
    demand(len(shots) >= 1, "No original shots")
    selected = []
    seen_hashes = set()
    last_frame = 0
    for i, shot in enumerate(shots, 1):
        start = round(shot["start_seconds"] * fps)
        end = round(shot["end_seconds"] * fps)
        demand(start == last_frame and end > start,
               f"Shot {i} gaps/overlap or invalid frame boundary")
        last_frame = end
        try:
            take = safe_file(root, shot.get("edited_take"))
        except StudioFormatError as exc:
            raise AssemblyBlocked(f"Shot {i}: " + str(exc)) from exc
        demand(take.is_file() and take.stat().st_size > 0,
               f"Shot {i}: missing already edited picture+real Foley take")
        digest = sha256(take)
        demand(digest == shot.get("edited_take_sha256"),
               f"Shot {i}: reviewed take hash mismatch")
        demand(digest not in seen_hashes,
               f"Shot {i}: exact duplicate take used as artificial filler")
        seen_hashes.add(digest)
        demand(shot.get("take_visual_audio_reviewed") is True and
               isinstance(shot.get("take_review_notes"), str) and
               len(shot["take_review_notes"].strip()) >= 60,
               f"Shot {i}: watch/listen to actual source before authoring the edit")
        demand(shot.get("source_license") in {"CC0", "CC BY 4.0", "original", "Pexels License"} and
               isinstance(shot.get("source_url"), str) and
               len(shot["source_url"]) >= 12,
               f"Shot {i}: cleared source rights and URL required")
        if i > 1:
            demand(isinstance(shot.get("transition_intent"), str)
                   and len(shot["transition_intent"].strip()) >= 8,
                   f"Shot {i}: editor must describe why adjacent shots belong together")
        if probe:
            inspect_take(take, end - start, aspect)
        selected.append(take)
    demand(last_frame == round(fps * duration),
           "Editor-approved takes do not fill final timeline")
    return plan, root, selected


def assemble(manifest: Path, check_only: bool = False) -> dict:
    plan, root, takes = validate(manifest)
    output = safe_file(root, plan["final_file"])
    report = safe_file(root, plan["av_scan_file"])
    demand(output not in takes and report != output,
           "Final destination cannot overwrite reviewed source footage")
    if check_only:
        return {
            "status": "source_takes_validated_not_rendered",
            "shot_count": len(takes),
            "duration_seconds": plan["duration_seconds"],
            "final_export": str(output),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    # GitHub cannot substitute a pre-approved scene, edit rhythm or Foley.
    # FFmpeg joins only the specific takes explicitly approved in manifest.
    with tempfile.TemporaryDirectory(prefix="asmr_manual_") as tmp:
        concat = Path(tmp) / "approved_takes.txt"
        def escape(path):
            return str(path).replace("'", "'\\''")
        concat.write_text("".join("file '" + escape(p) + "'\n" for p in takes),
                          encoding="utf-8")
        cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-map", "0:v:0", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "24",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
            "-frames:v", str(round(plan["duration_seconds"] * 24)),
            "-movflags", "+faststart",
            str(output),
        ]
        subprocess.run(cmd, check=True, timeout=max(1200, min(7200, int(plan["duration_seconds"] * 8))))
    inspect_take(output, round(plan["duration_seconds"] * 24),
                 plan.get("aspect_ratio", "9:16"))
    scan = scan_to_file(output, report)
    demand(not scan["unresolved_technical_blockers"],
           "Final file has unwanted near-silence: fix material-specific Foley, then re-export")
    return {
        "status": "RENDERED_UNAPPROVED",
        "master": str(output),
        "master_sha256": sha256(output),
        "scan_file": str(report),
        "scan_sha256": sha256(report),
        "shot_count": len(takes),
        "next_step": "Actual full-picture/headphone audio review then quality_gate.py release",
        "automatic_creative_approval": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--check-only", action="store_true",
                        help="Validate selected takes and provenance without re-encoding")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(assemble(args.manifest, check_only=args.check_only), indent=2))
        return 0
    except (AssemblyBlocked, GateError, StudioFormatError, OSError,
            subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as exc:
        print("BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
