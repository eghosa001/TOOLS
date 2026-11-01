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
from urllib.parse import urlparse, parse_qs
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
    kind = data.get("production_kind", "pilot")
    require(kind in {"pilot", "long-form"}, "Unknown production_kind; use pilot or long-form")
    if kind == "long-form":
        require(type(duration) in (float, int) and 180 < duration <= 2400,
                "Long-form project must be >180 and <=2400 seconds with authored, reviewed shots")
    else:
        require(type(duration) in (float, int) and 3 <= duration <= 180,
                "Pilot must be 3-180 seconds, including 5-second ASMR previews")
    if data.get("format_id"):
        from studio_formats import get_format, StudioFormatError
        try:
            fmt = get_format(data["format_id"])
        except StudioFormatError as exc:
            raise GateError(str(exc)) from exc
        require(data.get("production_mode") == fmt["production_mode"],
                "Registered ASMR format production route must not change silently")
        require(data.get("delivery_intent") in {"preview", "short", "long"},
                "Registered ASMR delivery intent must be explicit")
        require(data.get("delivery_aspect_ratio", "9:16") == data.get("aspect_ratio", "9:16"),
                "ASMR delivery camera/aspect ratio declarations disagree")
    require(data.get("delivery_aspect_ratio", "9:16") in {"9:16", "16:9"},
            "delivery_aspect_ratio must be 9:16 or 16:9")
    shots = data.get("manually_directed_shots")
    require(isinstance(shots, list) and len(shots) > 0, "Manual shot plan is mandatory")
    previous = 0.0
    # Popular ASMR uses several editorial structures, not one mandatory material.
    # Keep the sensory *promise* coherent and preserve material-specific Foley.
    if duration > 30 and len(shots) > 1:
        editorial = data.get("editorial_format")
        allowed = {
            "single-material", "process-transformation", "comparison",
            "themed-compilation", "surreal-world"
        }
        require(editorial in allowed,
                "Long ASMR needs an explicit evidence-led editorial_format")
        thesis = data.get("editorial_thesis")
        require(isinstance(thesis, str) and len(thesis.strip()) >= 16,
                "Explain the episode's consistent sensory promise")
        for index, shot in enumerate(shots):
            require(isinstance(shot, dict), f"Shot {index+1} must be an object")
            require(isinstance(shot.get("material_family"), str) and
                    len(shot["material_family"].strip()) >= 3,
                    f"Shot {index+1}: declare real sonic material identity")
            if editorial == "single-material":
                require(shot["material_family"] == data.get("material_family"),
                        "Single-material episode unexpectedly changes its subject")
            else:
                require(isinstance(shot.get("editorial_link"), str) and
                        len(shot["editorial_link"].strip()) >= 8,
                        f"Shot {index+1}: explain how it belongs to the episode")
                if index:
                    require(isinstance(shot.get("transition_intent"), str) and
                            len(shot["transition_intent"].strip()) >= 8,
                            f"Shot {index+1}: intentional transition missing")
                if editorial == "comparison":
                    axis = data.get("comparison_axis")
                    require(isinstance(axis, str) and len(axis.strip()) >= 4 and
                            shot.get("comparison_axis") == axis,
                            "Comparison shots must share a clear test/action")
                elif editorial == "process-transformation":
                    require(isinstance(shot.get("process_stage"), str) and
                            len(shot["process_stage"].strip()) >= 4,
                            "Process shot requires an ordered transformation stage")
                elif editorial == "surreal-world":
                    require(isinstance(shot.get("world_id"), str) and
                            len(shot["world_id"].strip()) >= 4,
                            "Surreal scene needs an intentional fantasy-world identity")
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
    data.setdefault("av_scan_file", "render/post_render_av_scan.json")
    if data.get("format_id"):
        data.setdefault("preview_av_scan_file", "render/post_render_preview_scan.json")
    for key in ("preview_file", "final_file", "av_scan_file") + (("preview_av_scan_file",) if data.get("format_id") else ()):
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


def validate_benchmark_evidence(review: dict) -> None:
    """Accept either creator references OR actually reviewed independent examples."""
    original = review.get("benchmark_video_ids") or []
    researched = review.get("researched_benchmarks") or []
    require(isinstance(original, list) and isinstance(researched, list),
            "Benchmark evidence must be lists")
    require(bool(original or researched),
            "Compare against at least one genuine ASMR YouTube video")
    require(all(isinstance(v, str) and v in REFERENCE_IDS for v in original),
            "Unknown creator reference video ID")
    for i, item in enumerate(researched):
        require(isinstance(item, dict), f"Researched benchmark {i+1}: invalid record")
        url = item.get("video_url")
        require(isinstance(url, str), f"Researched benchmark {i+1}: video URL missing")
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        identifier = ""
        if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            if parsed.path == "/watch":
                identifier = (parse_qs(parsed.query).get("v") or [""])[0]
            elif parsed.path.startswith("/shorts/"):
                identifier = parsed.path.split("/")[2]
        elif host == "youtu.be":
            identifier = parsed.path.strip("/")
        require(parsed.scheme == "https" and len(identifier) == 11 and
                all(c.isascii() and (c.isalnum() or c in "_-") for c in identifier),
                f"Researched benchmark {i+1}: verified public YouTube URL required")
        require(isinstance(item.get("title"), str) and len(item["title"].strip()) >= 8,
                f"Researched benchmark {i+1}: title needed")
        require(isinstance(item.get("research_source_url"), str) and
                item["research_source_url"].startswith("https://"),
                f"Researched benchmark {i+1}: research source needed")
        # Metadata-only research never becomes a fabricated sound/scene review.
        require(item.get("actual_visual_review") is True and
                item.get("actual_audio_review") is True,
                f"Researched benchmark {i+1}: real viewing AND listening needed")
        require(isinstance(item.get("review_notes"), str) and
                len(item["review_notes"].strip()) >= 60,
                f"Researched benchmark {i+1}: detailed audio/visual notes needed")


def check_output_geometry(info: dict, ratio: str, *, preview: bool) -> None:
    """Validate explicitly selected final framing; engineering, not artistic approval.

    Backwards compatibility: legacy pilot manifests default to 9:16. A long-form
    editor can explicitly choose 16:9 without losing the existing Shorts gate.
    """
    require(ratio in {"9:16", "16:9"}, "Unknown delivery aspect ratio")
    if ratio == "9:16":
        min_width, min_height = (540, 960) if preview else (720, 1280)
        expected_ratio = 9 / 16
    else:
        min_width, min_height = (960, 540) if preview else (1280, 720)
        expected_ratio = 16 / 9
    label = "Preview" if preview else "Final"
    require(info["height"] > 0 and
            abs(info["width"] / info["height"] - expected_ratio) < 0.015,
            f"{label} aspect ratio must be {ratio}")
    require(info["width"] >= min_width and info["height"] >= min_height,
            f"{label} must be at least {min_width}x{min_height} ({ratio})")


def check_format_inputs(data: dict, root: Path) -> None:
    """No CGI format can bypass studio-created visuals and licensed Foley sourcing."""
    if not data.get("format_id"):
        return
    from studio_formats import inspect_assets
    issues = inspect_assets(data, root)
    require(not issues, "STOP: ASMR format source preflight failed: " + "; ".join(issues))


def verify_studio_physics(data: dict, root: Path) -> None:
    """Legacy single-bake projects and registered per-shot masters remain distinct."""
    if data.get("format_id"):
        from physics_verify import verify_shots
        verify_shots(data, root)
    else:
        verify_physics(data, root)


def check_preview(data: dict, root: Path) -> str:
    check_format_inputs(data, root)
    path = root / data["preview_file"]
    info = media_info(path)
    require(3 <= info["duration"] <= 12, "Preview must be a representative 3-12s sample")
    check_output_geometry(info, data.get("delivery_aspect_ratio", "9:16"), preview=True)
    digest = sha256(path)
    if data.get("format_id"):
        # The initial 3–12s CGI audition must meet the SAME signal basics as
        # the final master; preview score does not replace full final QA.
        p = (root / data["preview_av_scan_file"]).resolve()
        require(p.is_relative_to(root.resolve()) and p.is_file(),
                "STOP: CGI preview AV scan missing; run run-preview with real 48kHz Foley")
        try:
            scan = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise GateError("STOP: preview AV scan invalid") from exc
        require(scan.get("scan_complete") is True and
                scan.get("master_sha256") == digest and
                scan.get("format_id") == data["format_id"],
                "STOP: CGI preview scan stale, wrong format or incomplete")
        signal = scan.get("master_signal_qa")
        require(isinstance(signal, dict) and signal.get("signal_preflight_passed") is True and
                signal.get("blocking_signal_issues") == [] and
                scan.get("unresolved_technical_blockers") == [],
                "STOP: CGI preview signal, codec, loudness or picture scan failed")
    review = data.get("preview_review")
    if data.get("format_id"):
        require(review.get("reviewed_preview_scan_sha256") == sha256(p)
                if isinstance(review, dict) else False,
                "STOP: preview human review must bind to exact sound/picture scan SHA256")
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
    validate_benchmark_evidence(review)
    for key in ("benchmark_visual_comparison", "benchmark_audio_comparison"):
        note = review.get(key)
        require(isinstance(note, str) and len(note.strip()) >= 50,
                f"STOP: real {key} notes must explicitly compare preview to a reference")
    require(review.get("dynamics_match") is True,
            "STOP: preview sound intensity/dynamics must match visible action after actual audition")
    require(isinstance(review.get("dynamics_observations"), str) and
            len(review["dynamics_observations"].strip()) >= 40,
            "STOP: preview requires genuine observations of force, loudness, harshness and release")
    require(review.get("blocking_issues") == [], "STOP: all blocking issues must be resolved")
    return digest


def check_post_render_av_review(data: dict, root: Path, master_sha: str, review: dict) -> None:
    """Require technical AV scan AND complete, timecoded picture-and-sound review.

    The scanner cannot grant subjective approval or verify audio-to-picture parity.
    """
    scan_path = (root / data["av_scan_file"]).resolve()
    require(scan_path.is_relative_to(root.resolve()) and scan_path.is_file(),
            "STOP: mandatory post-render AV scan missing; re-run the final scan")
    try:
        scan = json.loads(scan_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise GateError("Invalid post-render AV scan report") from exc
    require(isinstance(scan, dict) and scan.get("schema_version") == 1
            and scan.get("scan_complete") is True,
            "STOP: incomplete post-render audiovisual scan")
    require(scan.get("master_sha256") == master_sha,
            "STOP: AV scan belongs to a different export; re-scan this exact master")
    duration = scan.get("duration_seconds")
    require(type(duration) in (int, float) and
            abs(duration - data["duration_seconds"]) < 1.1,
            "STOP: AV scan duration differs from master")
    continuity = scan.get("audio_continuity")
    if data.get("format_id"):
        require(scan.get("format_id") == data["format_id"],
                "STOP: original CGI format QA was not run for this exact final master")
        signal = scan.get("master_signal_qa")
        require(isinstance(signal, dict) and
                signal.get("format_id") == data["format_id"] and
                signal.get("signal_preflight_passed") is True and
                signal.get("blocking_signal_issues") == [],
                "STOP: required studio audio loudness, true-peak or picture preflight failed")
    require(scan.get("unresolved_technical_blockers") == [] and
            isinstance(continuity, dict) and continuity.get("passed") is True
            and continuity.get("gaps") == [],
            "STOP: post-render audio continuity failed; repair genuine Foley")
    require(review.get("reviewed_av_scan_sha256") == sha256(scan_path),
            "STOP: review must be bound to this exact AV scan report")
    require(review.get("full_video_watched") is True,
            "STOP: entire final picture must actually be watched")
    require(review.get("full_audio_listened") is True and
            review.get("headphone_review_completed") is True,
            "STOP: entire final soundtrack must actually be heard on headphones")
    require(isinstance(review.get("review_method"), str) and
            len(review["review_method"].strip()) >= 20,
            "STOP: describe genuine visual and audio playback method")
    require(isinstance(review.get("reviewer"), str) and
            len(review["reviewer"].strip()) >= 2,
            "STOP: identify the audiovisual reviewer")
    if scan.get("warnings"):
        require(isinstance(review.get("technical_warning_resolution_notes"), str)
                and len(review["technical_warning_resolution_notes"].strip()) >= 40,
                "STOP: investigate each black/freeze/audio diagnostic warning")
    reviews = review.get("shot_reviews")
    shots = data["manually_directed_shots"]
    require(isinstance(reviews, list) and len(reviews) == len(shots),
            "STOP: every final shot requires its own visual/audio/sync evidence")
    for idx, (shot, item) in enumerate(zip(shots, reviews), 1):
        require(isinstance(item, dict) and item.get("shot_index") == idx,
                f"STOP: shot {idx} audiovisual evidence missing/out of order")
        for boundary in ("start_seconds", "end_seconds"):
            value = item.get(boundary)
            require(type(value) in (int, float) and
                    abs(value - shot[boundary]) < 0.05,
                    f"STOP: shot {idx} review fails to cover the final timeline")
        for field in ("visual_observations", "audio_observations", "sync_observations"):
            note = item.get(field)
            require(isinstance(note, str) and len(note.strip()) >= 25,
                    f"STOP: shot {idx} needs genuine {field}")
        require(item.get("dynamics_match") is True,
                f"STOP: shot {idx} visible action and sound energy/harshness mismatch")
        require(isinstance(item.get("dynamics_observations"), str) and
                len(item["dynamics_observations"].strip()) >= 40,
                f"STOP: shot {idx} needs heard dynamics observations for movement and rest")
        contacts = item.get("contact_checks")
        require(isinstance(contacts, list) and bool(contacts),
                f"STOP: shot {idx} requires observed action-to-Foley contact checks")
        for j, cue in enumerate(contacts, 1):
            require(isinstance(cue, dict), f"STOP: shot {idx} contact {j} invalid")
            t = cue.get("time_seconds")
            require(type(t) in (int, float) and
                    shot["start_seconds"] <= t <= shot["end_seconds"],
                    f"STOP: shot {idx} contact {j} timestamp outside shot")
            require(isinstance(cue.get("cue_id"), str) and cue["cue_id"].strip()
                    and isinstance(cue.get("material_action_notes"), str)
                    and len(cue["material_action_notes"].strip()) >= 15,
                    f"STOP: shot {idx} contact {j} needs real Foley identity")
            allowed_intensity = {"delicate", "gentle", "moderate", "forceful", "impact"}
            require(cue.get("visual_intensity") in allowed_intensity and
                    cue.get("audio_intensity") in allowed_intensity,
                    f"STOP: shot {idx} contact {j} missing observed intensity classes")
            require(cue["visual_intensity"] == cue["audio_intensity"] and
                    cue.get("energy_match") is True and
                    cue.get("timbre_harshness_match") is True,
                    f"STOP: shot {idx} contact {j} sound intensity/harshness does not match visual force")
            require(isinstance(cue.get("dynamics_notes"), str) and
                    len(cue["dynamics_notes"].strip()) >= 35,
                    f"STOP: shot {idx} contact {j} needs true force, texture and tail audition notes")
            offset = cue.get("sync_error_frames")
            require(cue.get("material_action_match") is True and
                    type(offset) in (int, float) and abs(offset) <= 1,
                    f"STOP: shot {idx} contact {j} mismatched sound or sync error")

    # Mandatory second gate: the older per-shot review could be satisfied with
    # ONE generic contact even when other clearly visible actions were unmatched.
    # The exact-export parity ledger enumerates all SALIENT visible events and
    # verifies recording provenance, sound/environment/force and each onset.
    # Ambient-only shots also need explicit justification, not filler rain noise.
    from scene_audio_parity_gate import (
        SceneParityError, validate_scene_audio_parity,
    )
    try:
        validate_scene_audio_parity(data, root, master_sha, sha256(scan_path))
    except SceneParityError as exc:
        raise GateError(str(exc)) from exc


def check_final(data: dict, root: Path) -> str:
    check_preview(data, root)
    try:
        verify_studio_physics(data, root)
    except PhysicsEvidenceError as exc:
        raise GateError("STOP: real material physics evidence required: "+str(exc)) from exc
    path = root / data["final_file"]
    info = media_info(path)
    require(abs(info["duration"] - data["duration_seconds"]) < 1.1,
            "Final duration differs from the approved shot plan")
    # Native 9:16 Shorts and independently composed native 16:9 long-form
    # follow distinct minimums; neither numeric test certifies visual polish.
    check_output_geometry(info, data.get("delivery_aspect_ratio", "9:16"), preview=False)
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
    check_post_render_av_review(data, root, sha256(path), review)
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
            if args.stage == "run-preview":
                check_format_inputs(data, root)
            if args.stage == "run-final":
                check_preview(data, root)
                try:
                    verify_studio_physics(data, root)
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
                check_output_geometry(info, data.get("delivery_aspect_ratio", "9:16"), preview=True)
                if data.get("format_id"):
                    from production.post_render_av_review import scan_to_file
                    scan_file = root / data["preview_av_scan_file"]
                    scan = scan_to_file(output, scan_file, format_id=data["format_id"])
                    print(f"CGI PREVIEW QA UNAPPROVED: {scan_file}; SHA256 {sha256(scan_file)}")
                    require(not scan["unresolved_technical_blockers"],
                            "STOP: CGI preview audio/video signal must be repaired")
                print(f"PREVIEW COMPLETE, NOT APPROVED. Watch/listen: {output}; SHA256 {sha256(output)}")
                print("Record genuine reviewer feedback and preview scan hash before full render.")
            else:
                require(abs(info["duration"] - data["duration_seconds"]) < 1.1,
                        "Final duration mismatch")
                check_output_geometry(info, data.get("delivery_aspect_ratio", "9:16"), preview=False)
                # Automatic engineering diagnostics run after EVERY final render.
                # They cannot approve aesthetics or sound realism.
                from production.post_render_av_review import scan_to_file
                scan_path = root / data["av_scan_file"]
                scan = scan_to_file(output, scan_path, format_id=data.get("format_id"))
                print(f"FINAL EXPORTED, UNAPPROVED: {output}")
                print(f"POST-RENDER AV SCAN: {scan_path}; SHA256 {sha256(scan_path)}")
                print("Full watch + headphone listen + timed contact-by-contact review required.")
                print("Add final_review with shot_reviews bound to MP4 and scan SHA256.")
                require(not scan["unresolved_technical_blockers"],
                        "STOP: post-render AV scan found unwanted audio gaps; re-export")
    except (GateError, OSError, ValueError, KeyError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
