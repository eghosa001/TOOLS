#!/usr/bin/env python3
"""Fail-closed safeguards for manually directed satisfying-video production.

This does NOT judge aesthetic quality or assemble video. It gates and time-limits
individual, pre-planned renders; a person must inspect and approve the footage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from physics_verify import verify as verify_physics, PhysicsEvidenceError

MAX_PREVIEW_SECONDS = 180
MAX_FINAL_SECONDS = 1200
MIN_REVIEW_SCORE = 9
# The user's video references set the artistic bar, but do not grant reuse rights.
REFERENCE_IDS = {"kKOJZbthcyo", "S47YZ2C7nv4", "7gV-0be8WqE", "XJ1SaNX4s8I"}
REQUIRED_QUALITY_SCORES = (
    "visual_score", "material_realism_score", "texture_detail_score",
    "lighting_color_score", "physical_coherence_score", "motion_score",
    "foley_quality_score", "audio_sync_score", "satisfaction_score"
)


class GateError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_plan(path: Path) -> tuple[dict, Path]:
    require(path.is_file(), f"Missing production manifest: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    root = path.resolve().parent
    require(isinstance(data, dict), "Manifest must be an object")
    require(bool(str(data.get("concept", "")).strip()), "Missing original concept")
    duration = data.get("duration_seconds")
    require(type(duration) in (float, int) and 3 <= duration <= 180, "Pilot must be 3-180 seconds, including 5-second ASMR previews")
    shots = data.get("manually_directed_shots")
    require(isinstance(shots, list) and len(shots) > 0, "Manual shot plan is mandatory")
    previous = 0.0
    # Multi-shot longform ASMR must keep one coherent tactile family.
    # The specialist episode builder separately validates per-contact Foley.
    if duration > 30:
        family = data.get("material_family")
        require(isinstance(family, str) and len(family.strip()) >= 4,
                "Long ASMR production must declare one material_family")
        require(all(isinstance(shot, dict) and shot.get("material_family") == family
                    for shot in shots),
                "BLOCKED: unrelated ASMR material families mixed in one episode")
    for i, shot in enumerate(shots):
        require(isinstance(shot, dict), f"Shot {i + 1} must be an object")
        start, end = shot.get("start_seconds"), shot.get("end_seconds")
        require(type(start) in (float, int) and type(end) in (float, int), f"Shot {i + 1}: invalid timing")
        require(abs(float(start) - previous) < 0.05 and end > start, f"Shot {i + 1}: gap, overlap or invalid order")
        previous = float(end)
        for key in ("visual_intent", "movement", "sound_cue", "source_and_rights"):
            require(isinstance(shot.get(key), str) and len(shot[key].strip()) >= 8,
                    f"Shot {i + 1}: missing {key}")
    require(abs(previous - duration) < 0.05, "Shot plan does not cover entire intended video")
    for key in ("preview_file", "final_file"):
        require(isinstance(data.get(key), str) and bool(data[key].strip()), f"Missing {key}")
        p = Path(data[key])
        require(not p.is_absolute() and ".." not in p.parts, f"{key} must be a relative path within the project")
    return data, root


def media_info(path: Path) -> dict:
    require(path.is_file() and path.stat().st_size > 0, f"Missing rendered media: {path}")
    require(shutil.which("ffprobe") is not None, "ffprobe required to check video/audio before proceeding")
    try:
        completed = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height",
             "-of", "json", str(path)], capture_output=True, text=True, timeout=15, check=True
        )
        result = json.loads(completed.stdout)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise GateError(f"Cannot validate media: {exc}") from exc
    streams = result.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    require(video is not None, "No video stream")
    require(any(s.get("codec_type") == "audio" for s in streams), "No audio stream; sync must be reviewable")
    duration = float(result.get("format", {}).get("duration", 0))
    require(duration > 0, "Media has no measurable duration")
    return {"duration": duration, "width": int(video.get("width", 0)),
            "height": int(video.get("height", 0))}


def check_preview(data: dict, root: Path) -> str:
    path = root / data["preview_file"]
    info = media_info(path)
    require(3 <= info["duration"] <= 12, "Preview must be a representative 3-12s sample")
    require(info["width"] >= 540 and info["height"] >= 960,
            "Preview must be at least 540x960 (vertical)")
    require(abs(info["width"] / info["height"] - 9 / 16) < 0.015,
            "Preview aspect ratio must be 9:16")
    digest = sha256(path)
    review = data.get("preview_review")
    require(isinstance(review, dict) and review.get("approved") is True,
            "STOP: sample has not been personally approved; no final rendering")
    require(review.get("reviewed_preview_sha256") == digest,
            "STOP: the preview changed after approval. Review the current preview again")
    require(isinstance(review.get("reviewer"), str) and len(review["reviewer"].strip()) >= 2,
            "Reviewer must be identified")
    require(isinstance(review.get("observations"), str) and len(review["observations"].strip()) >= 15,
            "Reviewer must describe what was actually watched and heard")
    # One good score cannot hide fake textures, implausible contact or mismatched Foley.
    for key in REQUIRED_QUALITY_SCORES:
        score = review.get(key)
        require(type(score) in (float, int) and MIN_REVIEW_SCORE <= score <= 10,
                f"STOP: {key} must be at least {MIN_REVIEW_SCORE}/10 after genuine inspection")
    references = review.get("benchmark_video_ids")
    require(isinstance(references, list) and len(references) > 0
            and all(isinstance(v, str) and v in REFERENCE_IDS for v in references),
            "STOP: compare preview to at least one user-supplied reference video ID")
    for key in ("benchmark_visual_comparison", "benchmark_audio_comparison"):
        note = review.get(key)
        require(isinstance(note, str) and len(note.strip()) >= 50,
                f"STOP: real {key} notes must explicitly compare preview to a reference")
    require(review.get("blocking_issues") == [], "STOP: all blocking issues must be resolved")
    return digest


def check_final(data: dict, root: Path) -> str:
    check_preview(data, root)
    try:
        verify_physics(data, root)
    except PhysicsEvidenceError as exc:
        raise GateError("STOP: real material physics evidence required: "+str(exc)) from exc
    path = root / data["final_file"]
    info = media_info(path)
    require(abs(info["duration"] - data["duration_seconds"]) < 1.1,
            "Final duration differs from the approved shot plan")
    # Creator-approved YouTube Shorts delivery profile: 720p portrait native.
    # Preserve all visual, Foley and manual-review gates independent of pixel count.
    require(info["width"] >= 720 and info["height"] >= 1280,
            "Final must be at least native 720x1280 (vertical HD)")
    require(abs(info["width"] / info["height"] - 9 / 16) < 0.015,
            "Final aspect ratio must be 9:16")
    review = data.get("final_review")
    require(isinstance(review, dict) and review.get("approved") is True,
            "Final export not approved: watch AND listen to the entire master")
    require(review.get("reviewed_final_sha256") == sha256(path),
            "Final export has changed since its full audiovisual review")
    require(isinstance(review.get("observations"), str) and len(review["observations"].strip()) >= 15,
            "Full-master review notes required")
    require(review.get("blocking_issues") == [], "Final export still has blocking issues")
    for key in REQUIRED_QUALITY_SCORES:
        score = review.get(key)
        require(type(score) in (float, int) and MIN_REVIEW_SCORE <= score <= 10,
                f"STOP: final {key} must be at least {MIN_REVIEW_SCORE}/10 after full viewing/listening")
    for key in ("benchmark_visual_comparison", "benchmark_audio_comparison"):
        note = review.get(key)
        require(isinstance(note, str) and len(note.strip()) >= 50,
                f"STOP: final {key} must compare the actual master to the benchmark")
    return sha256(path)


def run_limited(command: list[str], seconds: int, log_file: Path) -> None:
    require(bool(command), "No explicit renderer command provided")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        started = time.monotonic()
        last_update = -1
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed > seconds:
                    process.kill()
                    process.wait()
                    raise GateError(f"Render stopped after {seconds}s budget; read {log_file}")
                tick = int(elapsed // 10)
                if tick != last_update:
                    last_update = tick
                    print(f"Render in progress: {int(elapsed)}s/{seconds}s; log: {log_file}", flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            process.terminate()
            process.wait()
            raise GateError("Render interrupted by operator")
        require(process.returncode == 0,
                f"Render failed (exit {process.returncode}); inspect {log_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Short-preview-first, fail-closed video quality gates")
    parser.add_argument("stage", choices=["plan", "preview", "release", "run-preview", "run-final"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="For run-preview/run-final only: -- renderer executable and args")
    args = parser.parse_args()
    try:
        data, root = load_plan(args.manifest)
        if args.stage == "plan":
            print("PASS: original concept and all manually timed shots documented")
        elif args.stage == "preview":
            digest = check_preview(data, root)
            print(f"PASS: preview checked and personally signed off ({digest[:12]})")
        elif args.stage == "release":
            digest = check_final(data, root)
            print(f"PASS: final master fully reviewed ({digest[:12]}); ready for separate publishing decision")
        else:
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            if args.stage == "run-final":
                check_preview(data, root)
                try:
                    verify_physics(data, root)
                except PhysicsEvidenceError as exc:
                    raise GateError("STOP: no verified physical cache for final: "+str(exc)) from exc
                stage, seconds = "final", MAX_FINAL_SECONDS
            else:
                stage, seconds = "preview", MAX_PREVIEW_SECONDS
            run_limited(command, seconds, root / f"{stage}_render.log")
            output = root / data[f"{stage}_file"]
            info = media_info(output)
            if stage == "preview":
                require(3 <= info["duration"] <= 12, "Preview output must be 3-12 seconds")
                print(f"PREVIEW COMPLETE, NOT APPROVED. Watch/listen: {output}; SHA256 {sha256(output)}")
                print("Record genuine reviewer feedback in preview_review, then run 'preview' before full render.")
            else:
                require(abs(info["duration"] - data["duration_seconds"]) < 1.1,
                        "Final duration mismatch")
                print(f"FINAL EXPORTED, NOT APPROVED. Watch/listen to the entire file: {output}")
                print("Record final_review with this file's SHA256, then run 'release'.")
    except (GateError, OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
