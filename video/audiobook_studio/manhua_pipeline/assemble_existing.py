#!/usr/bin/env python3
"""Fast, CPU-only assembler for previously generated manhua panels and narration.

No GPU, AI model, image generation, TTS, story rewriting, or publication.
For multiple images, a timing JSON file is required; durations are not guessed.
Usage:
  python -m video.audiobook_studio.manhua_pipeline.assemble_existing \
    --audio narration_review.m4a --image scene-0000.png \
    --thumbnail THUMBNAIL_REVIEW.png --output review.mp4
  python -m video.audiobook_studio.manhua_pipeline.assemble_existing \
    --audio narration_review.m4a --timeline scene_timeline.json --output review.mp4
New full-color timing JSON: [{story_id, episode_id, page_id, panel_id,
  image, image_sha256, source_excerpt, source_sha256, seconds}, ...].
Pass --source-text /private/approved_spoken_script.txt. The old simple timing
format works only with explicit --art-policy legacy_dense for archived replays.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from video.audiobook_studio.episode_fastlane import atomic_json, probe_media, sha256, validate_review_video
from video.audiobook_studio.manhua_pipeline.music_bed import MOODS, music_filter, prepare_music


def _input(path: str, kind: str) -> Path:
    p = Path(path).expanduser().resolve(strict=True)
    if not p.is_file() or p.stat().st_size < 1024:
        raise ValueError("Missing or invalid " + kind + ": " + str(p))
    return p


def _audio_info(path: Path) -> tuple[float, str]:
    data = probe_media(path)
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if len(streams) != 1:
        raise ValueError("Expected exactly one narration audio stream")
    duration = float(data.get("format", {}).get("duration") or 0)
    if duration < 1 or duration > 4 * 3600:
        raise ValueError("Narration duration out of bounds")
    return duration, streams[0].get("codec_name", "")


def _scenes(args: argparse.Namespace, duration: float) -> list[tuple[Path, float]]:
    if args.timeline and args.image:
        raise ValueError("Use --timeline OR --image, not both")
    if args.timeline:
        source = Path(args.timeline).expanduser().resolve(strict=True)
        if not source.is_file():
            raise ValueError("Missing timing manifest")
        items = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(items, list) or not items:
            raise ValueError("Timeline must be a non-empty list")
        scenes = []
        for item in items:
            if not isinstance(item, dict) or "image" not in item or "seconds" not in item:
                raise ValueError("Timeline entries require image and seconds")
            name = Path(item["image"])
            if not name.is_absolute():
                name = source.parent / name
            panel = _input(str(name), "scene")
            declared_hash = item.get("image_sha256")
            if declared_hash is not None and declared_hash != sha256(panel):
                raise ValueError("Timeline image hash does not match actual panel")
            scenes.append((panel, float(item["seconds"])))
    elif args.image and len(args.image) == 1:
        scenes = [(_input(args.image[0], "scene"), duration)]
    else:
        raise ValueError("Use one --image or provide a precise --timeline for multiple images")
    if len(scenes) > 10000 or any(not 0.04 <= seconds <= 4 * 3600 for _, seconds in scenes):
        raise ValueError("Invalid scene count or duration")
    # New production defaults to verified COLOR panels from the actual source.
    # Older dense-art mode survives only for explicit legacy replay/tests.
    art_policy = getattr(args, "art_policy", "legacy_dense")
    if art_policy == "full_color_panels":
        if not getattr(args, "timeline", None):
            raise ValueError("COLOR_PANEL_SOURCE_REQUIRED: use a source-bound timeline, not one static image")
        from video.audiobook_studio.manhua_pipeline.color_panel_policy import (
            validate_color_panel_timeline,
        )
        validate_color_panel_timeline(
            items, timeline_path=source,
            source_text=Path(args.source_text) if getattr(args, "source_text", None) else None,
            narration_seconds=duration,
        )
    elif art_policy == "legacy_dense":
        if max(seconds for _, seconds in scenes) > 10.0 or (
                sum(seconds for _, seconds in scenes) / len(scenes) > 8.0):
            raise ValueError("ILLUSTRATION_CADENCE_FAILED: legacy dense stills every 5–8s")
        if len(scenes) != len({sha256(panel) for panel, _ in scenes}):
            raise ValueError("DUPLICATED_ILLUSTRATIONS_IN_TIMELINE")
    else:
        raise ValueError("Unknown audiobook illustration policy")
    if abs(sum(seconds for _, seconds in scenes) - duration) > 0.30:
        raise ValueError("Scene timeline differs from the actual narration duration")
    for panel, _ in scenes:
        media = probe_media(panel)
        if not any(s.get("codec_type") == "video" and s.get("width", 0) >= 512
                   and s.get("height", 0) >= 288 for s in media.get("streams", [])):
            raise ValueError("Low resolution or invalid scene image: " + panel.name)
    return scenes


def _verify_visual_evidence(args: argparse.Namespace,
                            scenes: list[tuple[Path, float]],
                            thumbnail: Path | None) -> dict:
    """Bind already-approved image hashes to source-to-image QA evidence.

    Preview assembly can run without the report, but cannot claim verified
    scene alignment. Strict production assembly fails closed on stale/bad QA.
    """
    source = getattr(args, "visual_qa_report", None)
    strict = (getattr(args, "require_visual_qa", False) or
              (getattr(args, "art_policy", "legacy_dense") == "full_color_panels"
               and not getattr(args, "draft_preview", False)))
    if not source:
        if strict:
            raise ValueError("Strict scene accuracy requires --visual-qa-report")
        return {"status": "NOT_REVIEWED", "source_to_image_verified": False,
                "human_visual_review_approved": False}
    path = Path(source).expanduser().resolve(strict=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("scenes", [])
    cover = data.get("thumbnail", {})
    gate = data.get("gate", {})
    if len(items) != len(scenes):
        raise ValueError("Visual QA report does not cover every scene")
    ledger = None
    if getattr(args, "timeline", None):
        ledger = json.loads(Path(args.timeline).expanduser().resolve(strict=True).read_text())
        if not isinstance(ledger, list) or len(ledger) != len(scenes):
            raise ValueError("Narration timeline does not cover every scene")
    if strict and ledger is None:
        raise ValueError("Strict visual QA requires a source-hashed narration timeline")
    for index, ((image, _), item) in enumerate(zip(scenes, items)):
        if ledger is not None:
            ref = ledger[index]
            if (not isinstance(ref, dict)
                or not re.fullmatch(r"[a-f0-9]{64}", str(ref.get("source_sha256", "")))
                or ref.get("source_sha256") != item.get("source_sha256")
                or ref.get("image_sha256") != sha256(image)):
                raise ValueError("Narration source or panel differs from reviewed timeline: " + str(index))
        if not item.get("source_sha256") or item.get("image_sha256") != sha256(image):
            raise ValueError("Scene source/image hash mismatch in QA: " + str(index))
    if thumbnail and cover.get("image_sha256") != sha256(thumbnail):
        raise ValueError("Thumbnail SHA does not match QA report")
    validated = (
        gate.get("automated_visual_triage_passed") is True and
        gate.get("needs_correction") is False and
        all(item.get("status") == "AUTOMATED_TRIAGE_PASS"
                and item.get("technical_ok") is True
                and item.get("image_model_verified") is True
                and item.get("requirements") for item in items) and
        (not thumbnail or (
            cover.get("status") == "AUTOMATED_TRIAGE_PASS"
            and cover.get("technical_ok") is True
            and cover.get("image_model_verified") is True
            and cover.get("requirements")))
    )
    # Hashes and model labels cannot establish that an image depicts an event.
    editor_gate = (
        gate.get("scene_by_scene_review_completed") is True and
        gate.get("editor_story_match_review_passed") is True and
        all(
            item.get("source_event_match_verified") is True and
            item.get("cast_costume_location_verified") is True and
            isinstance(item.get("specific_visual_evidence"), str) and
            len(item["specific_visual_evidence"].strip()) >= 24 and
            (not (ledger and ledger[index].get("reused_from_existing_episode"))
             or item.get("reuse_suits_this_event") is True)
            for index, item in enumerate(items)
        )
    )
    if strict and (not validated or not editor_gate):
        raise ValueError("STORY_IMAGE_MATCH_FAILED: actual story-event, cast, location and "
                         "reuse suitability review required for every scene before render")
    return {"status": "STORY_VISUAL_QA_PASS" if validated and editor_gate else "NEEDS_VISUAL_CORRECTION",
            "source_to_image_verified": validated and editor_gate,
            "automated_visual_triage_only": not editor_gate,
            "editor_story_match_review_approved": editor_gate,
            "human_visual_review_approved": False,
            "visual_qa_sha256": sha256(path)}


def _verify_narration_audible(video: Path, seconds: float) -> dict:
    """Decode the actual MP4 soundtrack. A stream header alone is not speech."""
    timeout = max(30, int(seconds * 0.25) + 30)
    check = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostdin", "-v", "info",
         "-i", str(video), "-map", "0:a:0", "-vn",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=timeout)
    if check.returncode:
        raise ValueError("Review video audio could not be decoded")
    stats = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", check.stderr)
    peaks = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", check.stderr)
    if not stats or not peaks:
        raise ValueError("Review video has no measurable narration audio")
    mean_db, peak_db = float(stats.group(1)), float(peaks.group(1))
    if mean_db < -55 or peak_db < -50:
        raise ValueError("Review narration is silent or too faint")
    return {"audible_audio_decoded": True, "mean_db": mean_db, "peak_db": peak_db}


def assemble(args: argparse.Namespace) -> dict:
    # Fail BEFORE narration decoding, picture preparation and expensive rendering.
    # New episodes MUST prebuild an original or rights-cleared soundtrack first.
    if (getattr(args, "art_policy", "legacy_dense") == "full_color_panels"
            and not getattr(args, "draft_preview", False)):
        from video.audiobook_studio.manhua_pipeline.music_bed import require_music_first_preflight
        music_first = require_music_first_preflight(
            Path(args.output), mood=getattr(args, "music_mood", "mystery"),
            level=getattr(args, "music_level", .10),
            music_file=getattr(args, "music_file", None))
    else:
        music_first = {"status": "DRAFT_OR_ARCHIVAL_NO_RELEASE_GATE"}
    audio = _input(args.audio, "narration")
    duration, audio_codec = _audio_info(audio)
    scenes = _scenes(args, duration)
    thumbnail = _input(args.thumbnail, "thumbnail") if args.thumbnail else None
    if thumbnail and getattr(args, "art_policy", "legacy_dense") == "full_color_panels":
        from video.audiobook_studio.manhua_pipeline.color_panel_policy import full_color_check
        full_color_check(thumbnail)
    visual_evidence = _verify_visual_evidence(args, scenes, thumbnail)
    output = Path(args.output).expanduser().resolve()
    if output.suffix.lower() != ".mp4" or output == audio or any(output == p for p, _ in scenes):
        raise ValueError("Output must be a distinct .mp4 path")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Normalize the private audio copy BEFORE rendering; never re-record or
    # retime the approved narration. Recheck its EBU R128 loudness.
    mastering = {"status": "DRAFT_OR_ARCHIVE_NOT_MASTERED"}
    if getattr(args, "art_policy", "legacy_dense") == "full_color_panels" and not getattr(args, "draft_preview", False):
        from video.audiobook_studio.manhua_pipeline.production_audio_gate import mastered_voice
        original_duration = duration
        audio, mastering = mastered_voice(audio, output.parent)
        duration, audio_codec = _audio_info(audio)
        if abs(duration - original_duration) > 0.30:
            raise ValueError("VOICE_MASTERING_DURATION_CHANGED: cannot alter narration timing")
    music, music_evidence = prepare_music(
        output, mood=getattr(args, "music_mood", "mystery"),
        music_file=getattr(args, "music_file", None),
        rights_file=getattr(args, "music_rights_file", None),
        level=getattr(args, "music_level", .10),
        legacy_no_music=getattr(args, "legacy_no_music", False),
        art_policy=getattr(args, "art_policy", "legacy_dense"),
    )
    if music_first.get("status") == "MUSIC_PREPARED_BEFORE_ASSEMBLY":
        if not music or sha256(music) != music_first["music_sha256"]:
            raise ValueError("MUSIC_FIRST_RENDER_SOURCE_MISMATCH")
    report_path = output.with_name(output.stem + ".assembly.json")
    inputs = {"audio_sha256": sha256(audio),
              "mastering_target": mastering.get("target_lufs"),
              "panels": [{"sha256": sha256(p), "duration_seconds": round(t, 5)}
                         for p, t in scenes],
              "thumbnail_sha256": sha256(thumbnail) if thumbnail else None,
              "music": music_evidence,
              "music_first_preflight": music_first,
              "codec": "h264", "width": 1920, "height": 1080,
              "fps": 24, "preset": args.preset, "motion": args.motion,
              "art_policy": getattr(args, "art_policy", "legacy_dense"),
              "visual_frame_timing_version": (
                  "scene_cfr24_v1" if getattr(args, "art_policy", "legacy_dense")
                  == "full_color_panels" else "legacy_concat"),
              "source_sha256": sha256(Path(args.source_text)) if (
                  getattr(args, "art_policy", "legacy_dense") == "full_color_panels"
                  and getattr(args, "source_text", None)) else None,
              "visual_qa": visual_evidence}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    if not args.force and report_path.is_file() and output.is_file():
        try:
            old = json.loads(report_path.read_text())
            if old.get("inputs_sha256") == key and old.get("video_sha256") == sha256(output):
                checked = validate_review_video(output, expected_audio_seconds=duration,
                                                min_duration_seconds=1.0)
                checked["audio_levels"] = _verify_narration_audible(output, duration)
                if thumbnail:
                    dest = output.with_name(output.stem + ".thumbnail" + thumbnail.suffix.lower())
                    if not dest.is_file() or sha256(dest) != sha256(thumbnail):
                        shutil.copy2(thumbnail, dest)
                old.update(status="DRAFT_CACHE_HIT_ONLY" if getattr(args, "draft_preview", False) else "CPU_ASSEMBLY_CACHE_HIT", cache_hit=True, video=output.name,
                           technical_review=checked)
                print("CPU_ASSEMBLY_CACHE_HIT", json.dumps(old), flush=True)
                return old
        except (ValueError, OSError, subprocess.SubprocessError, KeyError, json.JSONDecodeError):
            pass
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="manhua-assemble-", dir=output.parent) as scratch:
        root = Path(scratch)
        strict_color_timing = (
            getattr(args, "art_policy", "legacy_dense") == "full_color_panels")
        if strict_color_timing:
            from video.audiobook_studio.manhua_pipeline.timed_scene_track import (
                build_timed_scene_track,
            )
            scene_track = output.with_name(output.stem + ".scene_track.mp4")
            scene_track_report = build_timed_scene_track(
                scenes, scene_track, preset=args.preset, motion=args.motion)
        else:
            listing = root / "panels.ffconcat"
            lines = ["ffconcat version 1.0"]
            for image, seconds in scenes:
                if any(ch in str(image) for ch in ("'", "\n", "\r")):
                    raise ValueError("Unsafe panel path: " + str(image))
                lines.extend(["file '" + str(image) + "'", "duration " + f"{seconds:.6f}"])
            lines.append("file '" + str(scenes[-1][0]) + "'")
            listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
        vf = ("fps=24,scale=1920:1080:force_original_aspect_ratio=decrease,"
              "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p")
        if args.motion == "subtle":
            vf = ("scale=1920:1080:force_original_aspect_ratio=increase,"
                  "crop=1920:1080,fps=24,"
                  "zoompan=z='min(zoom+0.00008,1.06)':d=1:"
                  "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                  "s=1920x1080:fps=24,format=yuv420p")
        pending = root / "review.mp4"
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y"]
        if strict_color_timing:
            cmd.extend(["-i", str(scene_track), "-i", str(audio)])
        else:
            cmd.extend(["-safe", "0", "-f", "concat", "-i", str(listing),
                        "-i", str(audio)])
        if music:
            cmd.extend(["-stream_loop", "-1", "-i", str(music),
                        "-filter_complex", music_filter(duration, getattr(args, "music_level", .10)),
                        "-map", "0:v:0", "-map", "[aout]"])
        else:
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0"])
        if strict_color_timing:
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-vf", vf, "-c:v", "libx264", "-preset", args.preset,
                        "-crf", "21", "-r", "24"])
        cmd.extend(["-c:a", "aac" if music or audio_codec != "aac" else "copy"])
        if music or audio_codec != "aac":
            cmd.extend(["-b:a", "192k"])
        cmd.extend(["-t", f"{duration:.4f}", "-movflags", "+faststart", str(pending)])
        subprocess.run(cmd, check=True, timeout=max(120, int(duration * 6)))
        checked = validate_review_video(pending, expected_audio_seconds=duration,
                                        min_duration_seconds=1.0)
        checked["audio_levels"] = _verify_narration_audible(pending, duration)
        if strict_color_timing:
            from video.audiobook_studio.manhua_pipeline.timed_scene_track import (
                verify_rendered_scene_frames,
            )
            checked["source_to_video_scene_alignment"] = verify_rendered_scene_frames(
                pending, scenes)
        if getattr(args, "art_policy", "legacy_dense") == "full_color_panels" and not getattr(args, "draft_preview", False):
            from video.audiobook_studio.manhua_pipeline.production_audio_gate import measured_loudness, acceptable
            loudness = measured_loudness(pending)
            if not acceptable(loudness):
                raise ValueError(f"FINAL_AUDIO_MASTERING_FAILED: {loudness}; do not deliver")
            checked["final_loudness"] = loudness
        checked["music_bed"] = {
            "mixed_into_final_aac": bool(music),
            "sha256": music_evidence.get("sha256"),
            "speech_aware_ducking": bool(music),
            "full_listening_review_completed": False,
        }
        os.replace(pending, output)
    elapsed = round(time.monotonic() - started, 3)
    if thumbnail:
        dest = output.with_name(output.stem + ".thumbnail" + thumbnail.suffix.lower())
        if dest.resolve() != thumbnail:
            shutil.copy2(thumbnail, dest)
    result = {"status": "DRAFT_PREVIEW_ONLY" if getattr(args, "draft_preview", False) else "CPU_ASSEMBLY_PASS", "video": output.name,
              "audio_input": audio.name, "audio_mastering": mastering, "music": music_evidence,
              "music_first_preflight": music_first,
              "scene_count": len(scenes),
              "duration_seconds": checked["duration_seconds"],
              "assembly_seconds": elapsed, "cache_hit": False,
              "inputs_sha256": key, "video_sha256": sha256(output),
              "technical_review": checked,
              "gpu_used": False, "tts_run": False, "image_generation_run": False,
              "human_review_completed": False, "visual_quality": visual_evidence,
              "ready_for_youtube": False}
    atomic_json(report_path, result)
    print("CPU_ASSEMBLY_PASS", json.dumps(result), flush=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--image", action="append", help="A single existing image")
    ap.add_argument("--timeline", help="JSON ordered source-hashed colored panel shots")
    ap.add_argument("--source-text", help="Exact local approved spoken script; required for full-color panel mode")
    ap.add_argument("--art-policy", choices=["full_color_panels", "legacy_dense"],
                    default="full_color_panels",
                    help="Default: owner-mandated colored source-linked panels; legacy for old replay only")
    ap.add_argument("--thumbnail", help="Optional existing thumbnail, copied without regeneration")
    ap.add_argument("--visual-qa-report", help="Private source-linked pixel review JSON from image generation")
    ap.add_argument("--require-visual-qa", action="store_true",
                    help="Require visual QA even in archived replay/draft mode")
    ap.add_argument("--draft-preview", action="store_true",
                    help="Internal rough cut only; bypasses production story QA/mastering; cannot count as finished")
    ap.add_argument("--output", required=True)
    ap.add_argument("--motion", choices=["none", "subtle"], default="none")
    ap.add_argument("--preset", choices=["ultrafast", "superfast", "veryfast", "fast"],
                    default="ultrafast")
    ap.add_argument("--music-mood", choices=sorted(MOODS), default="mystery",
                    help="Original low-volume melodic music mood")
    ap.add_argument("--music-file", help="Alternative licensed music file")
    ap.add_argument("--music-rights-file",
                    help="Required licensing/provenance documentation with --music-file")
    ap.add_argument("--music-level", type=float, default=.10,
                    help="Music gain before speech ducking, between .02 and .20")
    ap.add_argument("--legacy-no-music", action="store_true",
                    help="Only for archived legacy replays; forbidden for new episodes")
    ap.add_argument("--force", action="store_true")
    assemble(ap.parse_args())


if __name__ == "__main__":
    main()
