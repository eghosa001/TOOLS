#!/usr/bin/env python3
"""Facts Uncovered real-media-only offline preview editor.

Consumes editor-selected, rights-verified actual footage/photographs and
already-produced, commercially cleared narration. It never generates imagery,
never silently falls back to stock/stills, and NEVER uploads video.
All output remains PREVIEW / HUMAN REVIEW REQUIRED.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def imported(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOURCE = imported("facts_source", ROOT / "source_first_policy.py")
MOTION = imported("facts_motion", ROOT / "video_motion_gate.py")


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, timeout=2400)


def probe_seconds(path: Path) -> float:
    item = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-of", "json", str(path)
    ], timeout=60))
    return float(item["format"]["duration"])


def resolve_media(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("Missing local media path")
    base = root.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        raise ValueError(f"Media file is missing or outside approved input directory: {relative}")
    return target


def review_plan(source: dict, motion: dict, media: Path) -> dict:
    """Fail closed before touching the renderer; no synthetic substitutions."""
    a = SOURCE.validate(source, phase="release", root=media)
    b = MOTION.validate(motion)
    problems = [f"Source: {item}" for item in a["errors"]]
    problems += [f"Motion: {item}" for item in b["errors"]]
    shots = source.get("shots", [])
    parts = motion.get("shots", [])
    if len(shots) != len(parts):
        problems.append("Source and motion timelines have different number of shots")
    for i, (left, right) in enumerate(zip(shots, parts), 1):
        try:
            if left["id"] != right["id"]:
                problems.append(f"Shot {i}: different source and motion IDs")
            if abs(float(left["start_seconds"]) - float(right["start_seconds"])) > .05 or abs(
                float(left["end_seconds"]) - float(right["end_seconds"])) > .05:
                problems.append(f"Shot {i}: timing mismatch")
            real_video = left["visual_kind"] == "REAL_FOOTAGE"
            if real_video != (right["visual_kind"] in MOTION.MOTION_KINDS):
                problems.append(f"Shot {i}: source and motion classifications disagree")
            expected_capture = "CAMERA_FILM" if real_video else (
                "CAMERA_PHOTO" if left["asset"]["origin_type"] == "CAMERA_PHOTO" else "SCAN_OF_PHYSICAL_ORIGINAL")
            if real_video and left["asset"]["origin_type"] != "CAMERA_FILM":
                problems.append(f"Shot {i}: moving source must be original camera film")
            if right["capture_type"] not in (
                {"CAMERA_FILM", "FILMED_REENACTMENT", "FILMED_REAL_WORLD"} if real_video
                else {expected_capture}
            ):
                problems.append(f"Shot {i}: camera/scan origin mismatch")
            if left["asset"]["source_page_url"] != right["source_page_url"]:
                problems.append(f"Shot {i}: provenance URL mismatch")
        except (KeyError, TypeError, ValueError):
            problems.append(f"Shot {i}: missing required evidence or timeline data")
    audio = source.get("audio")
    try:
        if not isinstance(audio, dict) or audio.get("commercial_rights_verified") is not True:
            raise ValueError("Audio rights not independently verified")
        if not isinstance(audio.get("source_description"), str) or not audio["source_description"].strip():
            raise ValueError("Audio origin not identified")
        sound = resolve_media(media, audio["local_path"])
        if digest(sound).lower() != audio["sha256"].lower():
            raise ValueError("Narration hash mismatch")
        if sound.suffix.lower() not in {".wav", ".m4a", ".mp3", ".flac"}:
            raise ValueError("Unsupported narration format")
        if abs(probe_seconds(sound) - float(motion["duration_seconds"])) > 1.0:
            raise ValueError("Narration runtime differs from approved footage timeline by >1 second")
    except (ValueError, TypeError, KeyError, subprocess.CalledProcessError, FileNotFoundError) as exc:
        problems.append(f"Audio: {exc}")
    if problems:
        raise ValueError("Real-media-only preview BLOCKED:\n- " + "\n- ".join(problems))
    return {"real_film_share": b["motion_share"], "total_seconds": b["total_seconds"],
            "shot_count": len(shots)}


def build(source: dict, motion: dict, media: Path, output: Path, format_name: str) -> dict:
    info = review_plan(source, motion, media)
    output.mkdir(parents=True, exist_ok=True)
    parts = output / "_segments"
    parts.mkdir(exist_ok=True)
    if format_name == "short":
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080
    filenames = []
    for i, shot in enumerate(source["shots"], 1):
        original = resolve_media(media, shot["asset"]["local_path"])
        motion_shot = motion["shots"][i-1]
        start = float(shot["start_seconds"])
        duration = round(float(shot["end_seconds"]) - start, 5)
        if duration <= 0:
            raise ValueError(f"Invalid shot length: {shot['id']}")
        result = parts / f"{i:04d}.mp4"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
        is_film = motion_shot["visual_kind"] in MOTION.MOTION_KINDS
        if is_film:
            if original.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".ogv"}:
                raise ValueError(f"Unexpected source-film format: {original}")
            source_start = float(shot.get("source_in_seconds", 0))
            if source_start < 0 or probe_seconds(original) + .02 < source_start + duration:
                raise ValueError(f"Original source film too short: {shot['id']}")
            command += ["-ss", str(source_start), "-i", str(original), "-t", str(duration)]
        else:
            if original.suffix.lower() not in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}:
                raise ValueError(f"Unsupported real-photo format: {original}")
            command += ["-loop", "1", "-framerate", "24", "-i", str(original), "-t", str(duration)]
        vf = (f"fps=24,scale={width}:{height}:force_original_aspect_ratio=decrease,"
              f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,format=yuv420p")
        command += ["-vf", vf, "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-r", "24", str(result)]
        run(command)
        filenames.append(result)
    concat = output / "_concat.txt"
    concat.write_text("\n".join(
        "file '" + str(p.resolve()).replace("'", "'\\''") + "'" for p in filenames
    ) + "\n", encoding="utf-8")
    audio_file = resolve_media(media, source["audio"]["local_path"])
    target = output / "Facts_Uncovered_REAL_MEDIA_PREVIEW.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(audio_file), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-af", "apad", "-t", str(info["total_seconds"]), "-movflags", "+faststart", str(target)])
    actual_seconds = probe_seconds(target)
    if abs(actual_seconds - info["total_seconds"]) > .3:
        raise RuntimeError(f"Output length mismatch: {actual_seconds:.2f}s != {info['total_seconds']:.2f}s")
    source["master_sha256"] = motion["master_sha256"] = digest(target)
    source["final_editorial_review"] = {
        "approved_for_facts_uncovered": False,
        "reviewer": "",
        "reviewed_mp4_sha256": "",
        "visual_and_audio_review_notes": "Preview generated; human picture/sound rights review outstanding"
    }
    (output / "REAL_ONLY_SOURCE_MANIFEST.json").write_text(json.dumps(source, indent=2)+"\n")
    (output / "REAL_ONLY_MOTION_MANIFEST.json").write_text(json.dumps(motion, indent=2)+"\n")
    outcome = {
        "status": "PREVIEW_NOT_APPROVED_FOR_PUBLICATION",
        "master_sha256": source["master_sha256"],
        **info,
        "visual_media_policy": "Genuine film/photo/scans only; all commercial source rights must be individually reviewed",
        "upload_allowed": False,
    }
    (output / "PREVIEW_QC.json").write_text(json.dumps(outcome, indent=2)+"\n")
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=["short", "long"], default="long")
    args = parser.parse_args()
    source = json.loads((args.media / "REAL_ONLY_SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    motion = json.loads((args.media / "REAL_ONLY_MOTION_MANIFEST.json").read_text(encoding="utf-8"))
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("FFmpeg and FFprobe must be installed")
    print(json.dumps(build(source, motion, args.media, args.output, args.format), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
